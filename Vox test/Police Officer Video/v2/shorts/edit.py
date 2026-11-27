"""shorts.edit: turns shorts_spec.json + one Short's staging (shorts/s1.py, s2.py, s3.py) into a timed edit.

    E = Edit(spec_short, voice)          # spec beats in order; voice = timing.Voice
    mod.voice(E)                         # the Short's voice decisions (replacements of NEW lines, inserted lines, tension)
    E.retime()                           # cut + place the clips -> E.T (timing dict), beat times
    mod.stage(E)                         # shots + overlay events + sound cues, all in short time
    E.finish()                           # default shots, keyword punches, filler punches (a visual event every <= 0.8 s)

Staging helpers (times in seconds of the Short; `at` may be a float offset from the beat start, 'w:word' = that word's
start minus LEAD, or ('f', 0.6) = a fraction of the beat):
    E.t(n, at)  E.w(n, word, k=0)  E.beat(n)  E.long(n, t, j=0)  (long-video time of short time t in beat n's clip j)
    E.sync(n, j=0)                    LongSrc that plays the long video in sync with beat n's clip j
    E.custom(kind, n, p, at=0, talk=None)   CustomSrc anchored to beat n's clip (mouths follow the long video's line)
    E.shot(n, at, src, **vshot kw)    add a VShot          E.ev(type, n, at, **kw)   add an overlay event
    E.hud(n, at, **state)             HUD state change    E.sfx(n, at, name, gain_db=0, **params)   add a sound cue
"""
import json, math, os, re
from timing import retime, chunk_words, LEAD, _norm
from stage import VShot, LongSrc, CustomSrc, SplitSrc, BlackSrc
import vfx

KEY_COL = {'cop': vfx.BLUE, 'police': vfx.BLUE, 'officer': vfx.BLUE, 'radio': vfx.BLUE, 'reception': vfx.BLUE, 'camera': vfx.BLUE,
           'mother': vfx.PINK, 'mum': vfx.PINK, 'her': vfx.PINK, 'she': vfx.PINK, 'father': vfx.PINK,
           'you': vfx.AMBER, 'your': vfx.AMBER, 'yours': vfx.AMBER, 'yourself': vfx.AMBER, 'voice': vfx.AMBER, 'i': vfx.AMBER,
           'live': vfx.AMBER, 'own': vfx.AMBER, 'green': vfx.GREEN, 'blue': vfx.BLUE, 'right': vfx.GREEN}


def key_colour(word):
    return KEY_COL.get(_norm(word), vfx.RED)


class Edit:
    def __init__(self, sp, V):
        self.sp, self.V = sp, V
        self.id = sp['id']
        self.beats = []                      # [dict(n, clips (Clip list), gap, inner, dur, kw, spec)]
        for b in sp['beats']:
            v = b['voice']
            clips = []
            if v and v['src'] == 'line':
                clips = [V.clip(v['i'])]
            self.beats.append(dict(n=b['n'], clips=clips, gap=None, inner=0.3, kw=list(b.get('caption_keywords') or []), spec=b,
                                   dur=None))
        self.tension_after = None
        self.tension = 1.1
        self.shots, self.events, self.cues, self.music = [], [], [], []
        self.huds = []                       # [(t, dict(state))]
        self.flags = {}

    # ---------------------------------------------------------------- voice decisions
    def B(self, n):
        for b in self.beats:
            if b['n'] == n: return b
        raise KeyError(n)

    def voice(self, n, segs, inner=0.3, gap=None, kw=None):
        b = self.B(n)
        b['clips'] = [self._clip(d) for d in segs]
        b['inner'] = inner
        if gap is not None: b['gap'] = gap
        if kw is not None: b['kw'] = kw

    def nl(self, ident):
        """A newly recorded line (only with --with-new-lines and when $S/pov2/shorts_vo/<ID>.wav exists)."""
        return dict(new=self.new_lines[ident], text=self.new_texts[ident], ident=ident)

    def has_nl(self, ident): return ident in getattr(self, 'new_lines', {})

    def _clip(self, d):
        d = dict(d)
        if 'new' in d: return self.V.new_clip(d['new'], d['text'], ident=d.get('ident'))
        m = d.pop('match', None)
        if m:
            lw = [w for w, _ in self.V.line_words(d.get('alias', d['i']))]
            target = [_norm(x) for x in m.split()]
            nw = [_norm(x) for x in lw]
            for k in range(len(nw) - len(target) + 1):
                if nw[k:k + len(target)] == target:
                    d['words'] = (k, k + len(target) - 1); break
            else:
                raise ValueError('no match %r in line %d' % (m, d['i']))
        return self.V.clip(**d)

    def insert(self, after, n, segs, kw=None, inner=0.3, gap=None):
        k = [j for j, b in enumerate(self.beats) if b['n'] == after][0]
        self.beats.insert(k + 1, dict(n=n, clips=[self._clip(d) for d in segs], gap=gap, inner=inner, kw=kw or [], spec=None, dur=None))

    def move(self, n, after):
        """Move beat n to just after beat `after`."""
        b = self.B(n); self.beats.remove(b)
        k = [j for j, x in enumerate(self.beats) if x['n'] == after][0]
        self.beats.insert(k + 1, b)

    def drop(self, n):
        self.beats = [b for b in self.beats if b['n'] != n]

    def gap(self, n, g): self.B(n)['gap'] = g

    def tail(self, n, dur):
        b = self.B(n); b['clips'] = []; b['dur'] = dur

    # ---------------------------------------------------------------- timing
    def retime(self):
        # clip spans now run from -40 dBFS onset to -40 dBFS decay (timing.Voice.clip), about 90 ms longer than the old
        # -32 dB thresholds: the planned gaps shrink by 60 ms so the audible pauses (and the pace) stay as planned
        adj = lambda g: (g - 0.06) if (g is not None and g < 0.4) else g
        bl = [dict(n=b['n'], clips=b['clips'], gap=adj(b['gap']), inner=adj(b['inner']), dur=b['dur'] or 0.5) for b in self.beats]
        self.T = retime(self.V, bl, tension_after=self.tension_after, tension=self.tension, default_gap=0.22)
        self.dur = self.T['duration']
        self.bt = {e['n']: e for e in self.T['beats']}
        for b in self.beats:
            e = self.bt[b['n']]; b.update(t0=e['t0'], t1=e['t1'], on=e['voice_on'], off=e['voice_off'], tclips=e['clips'])
        self.words = self.T['words']
        self.chunks = []
        for ci in sorted(set(w['clip'] for w in self.words)):
            ws = [w for w in self.words if w['clip'] == ci]
            base = self.words.index(ws[0])
            for c in chunk_words(ws):
                c['i0'] += base; c['i1'] += base
                self.chunks.append(c)
        self.chunks.sort(key=lambda c: c['t'])
        for k, c in enumerate(self.chunks):          # never overlap the next chunk
            if k + 1 < len(self.chunks): c['t1'] = min(c['t1'], self.chunks[k + 1]['t'])
        self._min_chunks()
        self._keywords()
        return self.T

    def _min_chunks(self, mind=0.25):
        """No caption chunk shorter than 0.25 s: a one-word chunk joins the next one-word chunk of the same clip (still
        1-2 words, <= 14 characters); otherwise it holds 0.25 s and the next chunk starts that much later (<= 0.1 s late,
        the next chunk keeps >= 0.2 s)."""
        ch = self.chunks; out = []; k = 0
        while k < len(ch):
            c = ch[k]
            n = ch[k + 1] if k + 1 < len(ch) else None
            if (c['t1'] - c['t'] < mind and n is not None and n['clip'] == c['clip'] and c['i1'] == c['i0'] and n['i1'] == n['i0']
                    and len(c['text']) + 1 + len(n['text']) <= 14 and not c['text'].endswith(('.', '?', '!'))):
                ch[k + 1] = dict(c, text=c['text'] + ' ' + n['text'], i1=n['i1'], t1=n['t1'], end=n['end'])
                k += 1; continue
            out.append(c); k += 1
        for k, c in enumerate(out):
            if c['t1'] - c['t'] < mind and k + 1 < len(out):
                n = out[k + 1]
                shift = min(mind - (c['t1'] - c['t']), 0.1, max(0.0, n['t1'] - n['t'] - 0.2))
                c['t1'] += shift; n['t'] = max(n['t'], c['t1'])
            elif c['t1'] - c['t'] < mind and k + 1 == len(out):
                c['t1'] = c['t'] + mind
        self.chunks = out

    def _keywords(self):
        """One coloured keyword per sentence: the beat's caption_keywords (first match per sentence), else none."""
        for c in self.chunks: c['key'] = None; c['colour'] = None
        for b in self.beats:
            kws = [k.upper() for k in (b.get('kw') or [])]
            if not kws: continue
            idx = [k for k, w in enumerate(self.words) if w['beat'] == b['n']]
            if not idx: continue
            # sentences inside the beat
            sent, cur = [], []
            for k in idx:
                if cur and self.words[k]['clip'] != self.words[cur[-1]]['clip']: sent.append(cur); cur = []
                cur.append(k)
                if self.words[k]['w'].endswith(('.', '?', '!')): sent.append(cur); cur = []
            if cur: sent.append(cur)
            for s_ in sent:
                done = False
                for kw in kws:
                    parts = kw.split()
                    for k in s_:
                        seq = [_norm(self.words[k + j]['w']) if k + j < len(self.words) else '' for j in range(len(parts))]
                        if seq == [_norm(p) for p in parts]:
                            last = k + len(parts) - 1
                            for c in self.chunks:
                                if c['i0'] <= last <= c['i1']:
                                    c['key'] = last - c['i0']; c['colour'] = b.get('kc', {}).get(kw) or key_colour(parts[-1])
                                    c['kt'] = self.words[last]['t']
                                    self.words[last]['key'] = True
                            done = True; break
                    if done: break

    # ---------------------------------------------------------------- staging helpers
    def beat(self, n): return self.B(n)

    def w(self, n, word, k=0):
        word = _norm(word); m = 0
        for x in self.words:
            if x['beat'] == n and _norm(x['w']).startswith(word):
                if m == k: return x['t']
                m += 1
        raise KeyError('word %r not in beat %s' % (word, n))

    def wf(self, n, *cands, frac=0.5):
        """Start of the first of these words found in beat n, else a fraction of the beat (robust to voice swaps)."""
        for c in cands:
            try: return self.w(n, c)
            except KeyError: pass
        return self.t(n, ('f', frac))

    def t(self, n, at=0.0):
        b = self.B(n)
        if isinstance(at, str):
            if at.startswith('w:'):
                parts = at[2:].split('#'); k = int(parts[1]) if len(parts) > 1 else 0
                return self.w(n, parts[0], k) - LEAD
            if at == 'end': return b['t1']
            if at == 'on': return b['on']
            if at == 'off': return b['off']
            raise ValueError(at)
        if isinstance(at, tuple):
            if at[0] == 'f': return b['t0'] + at[1] * (b['t1'] - b['t0'])
            if at[0] == 'w': return self.w(n, at[1], at[2] if len(at) > 2 else 0) + (at[3] if len(at) > 3 else 0.0)
            if at[0] == 'off': return b['off'] + at[1]
            if at[0] == 'on': return b['on'] + at[1]
        return b['t0'] + at

    def clip(self, n, j=0): return self.B(n)['tclips'][j]

    def long(self, n, t, j=0):
        c = self.clip(n, j); return c['a'] + (t - c['dst_a']) * 1.0

    def sync(self, n, j=0, dt=0.0):
        c = self.clip(n, j)
        return LongSrc(anchor=(c['dst_a'], c['a'] + dt))

    def custom(self, kind, n=None, p=None, talk=None, T=None, j=0, dt=0.0):
        if T is not None: return CustomSrc(kind, T0=T, p=p, talk=talk)
        c = self.clip(n, j)
        return CustomSrc(kind, p=p, talk=talk, anchor=(c['dst_a'], c['a'] + dt))

    def film(self, T, **k): return LongSrc(T, **k)

    def shot(self, bn, at, src, **kw):
        t = self.t(bn, at) if bn is not None else at
        vs = VShot(t, src, **kw); vs.beat = bn
        self.shots.append(vs)
        return vs

    def ev(self, typ, bn, at, **kw):
        t = self.t(bn, at) if bn is not None else at
        e = dict(type=typ, t=t, **kw); self.events.append(e); return e

    def hud(self, bn, at, **st):
        t = self.t(bn, at) if bn is not None else at
        self.huds.append((t, st))

    def sfx(self, bn, at, name, gain_db=0.0, pan=0.0, space=None, kind='transient', **params):
        t = self.t(bn, at) if bn is not None else at
        e = dict(t=round(t, 3), name=name, gain_db=gain_db, pan=pan, kind=kind)
        if space: e['space'] = space
        if params: e['params'] = params
        self.cues.append(e); return e

    def mus(self, bn, at, typ, level=0.7, length=None):
        t = self.t(bn, at) if bn is not None else at
        e = dict(t=round(t, 3), type=typ, level=level)
        if length: e['len'] = length
        self.music.append(e); return e

    # ---------------------------------------------------------------- finishing passes
    def finish(self):
        shots = sorted(self.shots, key=lambda s: s.t0)
        have = set(s.beat for s in shots)
        for b in self.beats:                          # any beat without a shot plays the long video in sync with its voice
            if b['n'] not in have and b['tclips']:
                shots.append(self._mk(VShot(b['t0'], self.sync(b['n'])), b['n']))
        shots.sort(key=lambda s: s.t0)
        if not shots or shots[0].t0 > 0: raise ValueError('no shot at 0')
        for j, s in enumerate(shots): s.t1 = shots[j + 1].t0 if j + 1 < len(shots) else self.dur
        self.shots = shots
        from overlay import normalise_events
        normalise_events(self.events)
        self._reframe_cuts()
        # keyword punches (110-140 %) on the shot that holds the keyword
        for c in self.chunks:
            if c.get('key') is None: continue
            s = self.shot_at(c['kt'])
            if c['kt'] - s.t0 < 0.15 or s.fx.get('no_punch'): continue
            lev = self._level(s, c['kt'])
            s.punches.append((c['kt'], 1.0 if lev >= 1.28 else min(1.4, lev + 0.24)))
        # filler punches: no gap between visual events > 0.95 s
        for s in self.shots:
            if s.fx.get('no_fill'): continue
            for _ in range(8):
                evs = sorted([s.t0] + [p[0] for p in s.punches] + [c[0] for c in getattr(s, 'cuts', [])]
                             + [e['t'] for e in self.events if s.t0 < e['t'] < s.t1 and e['type'] in VISUAL] + [s.t1])
                gaps = [(evs[k + 1] - evs[k], evs[k]) for k in range(len(evs) - 1)]
                g, at = max(gaps)
                if g <= 0.95: break
                tp = at + g / 2
                lev = self._level(s, tp)
                s.punches.append((tp, 1.0 if lev >= 1.2 else lev + 0.16))
            s.punches.sort()
        self.events.sort(key=lambda e: e['t'])
        self.huds.sort(key=lambda h: h[0])

    def _reframe_cuts(self, every=1.0):
        """Long shots get hard re-frame cuts (a jump cut to a tighter / wider framing, shifted sideways) about every 1.0 s,
        on word starts where possible, never within 0.2 s of a slam / flash / shot boundary: the references cut every
        0.7-1.2 s."""
        words = [w['t'] for w in self.words]
        busy = [e['t'] for e in self.events if e['type'] in ('slam', 'flash', 'stamp', 'subscribe', 'endcard', 'rewind', 'glitch')]
        for s in self.shots:
            s.cuts = []
            if s.fx.get('no_fill') or s.fx.get('no_cuts') or s.fx.get('rewind'): continue
            d = s.t1 - s.t0
            if d < 1.45: continue
            n = max(2, int(round(d / every)))
            side = 1 if (int(s.t0 * 10) % 2) else -1
            for j in range(1, n):
                tc = s.t0 + d * j / n
                near = [w for w in words if abs(w - tc) <= 0.2 and s.t0 + 0.5 < w < s.t1 - 0.45]
                if near: tc = min(near, key=lambda w: abs(w - tc))
                if tc < s.t0 + 0.5 or tc > s.t1 - 0.45 or any(abs(tc - b) < 0.2 for b in busy): continue
                if s.cuts and tc - s.cuts[-1][0] < 0.6: continue
                tight = (len(s.cuts) % 2 == 0)
                s.cuts.append((round(tc, 3), 1.16 if tight else 1.0, (38 * side) if tight else 0.0, 12 if tight else 0.0))
                side = -side

    @staticmethod
    def _mk(vs, n):
        vs.beat = n; return vs

    def _level(self, s, t):
        lev = 1.0
        for (tt, l) in sorted(s.punches):
            if tt <= t: lev = l
        return lev

    def shot_at(self, t):
        cur = self.shots[0]
        for s in self.shots:
            if s.t0 <= t: cur = s
        return cur


VISUAL = {'slam', 'tag', 'stamp', 'flash', 'subscribe', 'endcard', 'comments', 'glitch', 'panel', 'notebook', 'complaint', 'rule',
          'wave', 'phone', 'loop', 'bubble', 'ghost'}
