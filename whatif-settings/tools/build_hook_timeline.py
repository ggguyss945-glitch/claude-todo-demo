#!/usr/bin/env python3
"""Build the 60-second hook timeline from the hook board.

    python3 -I tools/build_hook_timeline.py [--board episodes/hook/board.json] [--out episodes/hook/timeline.json]
                                            [--md episodes/hook/SHOTS.md] [--no-measure] [--quiet]

Reads episodes/hook/board.json (lines, shots, music, drops, beds; anchor syntax in its _doc) and audio/voice_lines.json
(the 24 voice takes), places the voice lines with the designed gaps, resolves every shot boundary, the music edit and
the ambience beds to global seconds, builds the word-timed captions with the engine's captionsFromLine()
(engine/anim/captions.js, run through node), measures the loudness of every music/bed slice with audio/lib.py
(skipped with --no-measure or when the licensed media is not on disk: gain_db is then null) and writes
episodes/hook/timeline.json (the engine v3 timeline, plus T.music / T.drops / T.beds / T.sync for the mixer) and
episodes/hook/SHOTS.md (the animators' table). Deterministic: same inputs -> same files.
"""
import argparse, json, math, os, re, statistics, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
ENGINE = os.path.join(PROJECT, 'engine')
AUDIO = os.path.join(PROJECT, 'audio')
NODE_PATH = os.environ.get('NODE_PATH', '/opt/node-tools/node_modules')
MODULES = {'hook_a': 'shots/hook_a.js', 'hook_b': 'shots/hook_b.js', 'hook_c': 'shots/hook_c.js', 'hook_d': 'shots/hook_d.js'}
r3 = lambda x: round(float(x), 3) + 0.0      # + 0.0: no "-0.0"
norm = lambda s: re.sub(r"[^a-z0-9']", '', str(s).lower())


class Board:
    def __init__(self, B, V):
        self.B, self.fps = B, B.get('fps', 60)
        self.V = {e['id']: e for e in V}
        self.lines = B['lines']
        self.line_ix = {L['id']: i for i, L in enumerate(self.lines)}
        self.shots = B['shots']
        self.shot_ix = {S['id']: i for i, S in enumerate(self.shots)}
        self.music = {m['id']: m for m in B.get('music', [])}
        self._start, self._shot, self._hit, self._mus = {}, {}, {}, {}
        self._stack = []

    # ---------- voice ----------
    def words(self, lid):
        return self.V[lid]['words']

    def line_start(self, lid):
        """global start of the line's file (word times are relative to it)"""
        if lid in self._start:
            return self._start[lid]
        if lid in self._stack:
            raise ValueError('circular anchor at line ' + lid)
        self._stack.append(lid)
        i = self.line_ix[lid]
        L, W = self.lines[i], self.words(lid)
        if 'onset' in L:
            onset = self.G(L['onset'])
        else:
            prev = self.lines[i - 1]['id']
            onset = self.last_end(prev) + L.get('gap', 0.4)
        self._start[lid] = onset - W[0]['t']
        self._stack.pop()
        return self._start[lid]

    def first_on(self, lid):
        return self.line_start(lid) + self.words(lid)[0]['t']

    def last_end(self, lid):
        w = self.words(lid)[-1]
        return self.line_start(lid) + w['t'] + w['d']

    def word(self, ref):
        """'LINE:Word' | 'LINE:Word#2' (2nd match) | 'LINE:#3' (index, negative from the end) -> (line id, word dict)"""
        lid, key = ref.split(':', 1)
        W = self.words(lid)
        if key.startswith('#'):
            return lid, W[int(key[1:])]
        n = 1
        if '#' in key:
            key, n = key.split('#')
            n = int(n)
        m = [w for w in W if norm(w['w']) == norm(key)]
        if len(m) < n:
            raise KeyError(f'word {ref!r} not found in {[w["w"] for w in W]}')
        return lid, m[n - 1]

    # ---------- anchors ----------
    def G(self, a):
        if a is None:
            return None
        off = a.get('off', 0.0)
        if 't' in a:
            v = a['t']
        elif 'word' in a:
            lid, w = self.word(a['word'])
            v = self.line_start(lid) + w['t']
        elif 'wordEnd' in a:
            lid, w = self.word(a['wordEnd'])
            v = self.line_start(lid) + w['t'] + w['d']
        elif 'line' in a:
            v = self.first_on(a['line'])
        elif 'lineEnd' in a:
            v = self.last_end(a['lineEnd'])
        elif 'shot' in a:
            v = self.shot_start(a['shot'])
        elif 'shotEnd' in a:
            v = self.shot_end(a['shotEnd'])
        elif 'hit' in a:
            v = self.hit(a['hit'])
        elif 'end' in a:
            v = self.end()
        elif 'music' in a:
            v = self.mus(a['music'])['at']
        else:
            raise ValueError('bad anchor ' + json.dumps(a))
        return v + off

    def hit(self, k):
        if k not in self._hit:
            self._hit[k] = self.G(self.B['hits'][k])
        return self._hit[k]

    def shot_start(self, sid):
        if sid not in self._shot:     # shot edges land on frames; everything anchored to a shot follows the snapped edge
            self._shot[sid] = round(self.G(self.shots[self.shot_ix[sid]]['start']) * self.fps) / self.fps
        return self._shot[sid]

    def shot_end(self, sid):
        i = self.shot_ix[sid]
        return self.shot_start(self.shots[i + 1]['id']) if i + 1 < len(self.shots) else self.end()

    def end(self):
        return round(self.G(self.B['timeline_end']) * self.fps) / self.fps

    # ---------- music edit ----------
    def mus(self, mid):
        """resolve a music entry: at (global start), src0/src1, fades (crossfades overlap the neighbour)"""
        if mid in self._mus:
            return self._mus[mid]
        m = self.music[mid]
        xin = m.get('xfade_in', 0.0)
        if 'sync' in m:
            s_src, anc = m['sync']
            at = self.G(anc) - (s_src - m['src0'])
        elif 'at' in m and 'join_after' in m['at']:
            prev = self.mus(m['at']['join_after'])
            at = prev['at'] + prev['len'] - xin
        else:
            at = self.G(m['at'])
        u = m.get('until')
        fade_out = m.get('fade_out', 0.0)
        if u and 'join' in u:
            nxt = self.mus(u['join'])
            end = nxt['at'] + nxt['xfade_in']
            fade_out = nxt['xfade_in']
        elif u:
            end = self.G(u)
        else:
            end = at + (m['src1'] - m['src0'])
        length = end - at
        fx = m.get('fx') or {}
        if fx.get('rate') == 'fit':
            rate = (m['src1'] - m['src0']) / length
            src1 = m['src1']
        else:
            rate = fx.get('rate', 1.0)
            src1 = m['src0'] + length * rate
            if 'src1' in m and src1 > m['src1'] + 1e-6:
                raise ValueError(f'music {mid}: needs src up to {src1:.3f} but src1 is {m["src1"]}')
        out = {'id': mid, 'track': m['track'], 'src': [r3(m['src0']), r3(src1)], 'at': at, 'len': length, 'end': end,
               'fade_in': m.get('fade_in', xin), 'fade_out': fade_out, 'xfade_in': xin, 'rate': rate, 'fx': fx,
               'target_lufs': m.get('target_lufs'), 'measure': m.get('measure'), 'note': m.get('note', '')}
        self._mus[mid] = out
        return out


# ---------- captions (engine captionsFromLine via node) ----------
NODE_CAPS = r"""
import fs from 'fs';
const { captionsFromLine } = await import(process.argv[1] + '/anim/captions.js');
const jobs = JSON.parse(fs.readFileSync(0, 'utf8'));
const out = jobs.map((j) => captionsFromLine(j.line, j.markup, j.o));
process.stdout.write(JSON.stringify(out));
"""


def run_caption_jobs(jobs):
    env = dict(os.environ, NODE_PATH=NODE_PATH)
    p = subprocess.run(['node', '--input-type=module', '-e', NODE_CAPS, ENGINE], input=json.dumps(jobs), capture_output=True, text=True, env=env)
    if p.returncode:
        raise RuntimeError('node captions failed: ' + p.stderr[-2000:])
    return json.loads(p.stdout)


def plain(markup):
    return re.sub(r'\{([^|}]+)(\|[^}]+)?\}', r'\1', markup)


def build_captions(bd, placed, cuts=()):
    """1-3 word chunks; ' / ' in the board text fixes chunk boundaries (each group timed by captionsFromLine on its words)"""
    fps, lead = bd.fps, bd.B.get('caption_lead_frames', 3)
    tail = bd.B.get('caption_tail', 0.25)
    jobs, meta = [], []
    for L in bd.lines:
        lid, text, mode = L['id'], L['captions'], L.get('mode')
        start, W = placed[lid]['start'], bd.words(lid)
        words = [{'w': w['w'], 't0': r3(w['t']), 't1': r3(w['t'] + w['d'])} for w in W]
        groups = [g.strip() for g in text.split(' / ')]
        if len(groups) == 1 and len(words) > 3 and '{' not in text:
            jobs.append({'line': {'start': start, 'dur': placed[lid]['dur'], 'words': words}, 'markup': text, 'o': {'lead': lead, 'maxWords': 3, 'tail': tail}})
            meta.append((lid, mode, None, L))
            continue
        # walk the groups over the words by token count (numbers like '412' cover the rest of the spoken number)
        wi = 0
        for gi, gtxt in enumerate(groups):
            toks = [t for t in re.findall(r"\{[^}]+\}|\S+", gtxt)]
            ntok = sum(len(plain(t).split()) for t in toks)
            if gi == len(groups) - 1:
                n = len(words) - wi
            elif re.search(r'\d', plain(gtxt)):
                # a digit chunk stands for the spoken number: it covers words up to the next group's first word
                nxt = norm(plain(groups[gi + 1]).split()[0])
                k = wi
                while k < len(words) and norm(words[k]['w']) != nxt:
                    k += 1
                n = max(1, k - wi)
            else:
                n = ntok
            sub = words[wi:wi + n]
            if not sub:
                raise ValueError(f'caption group {gtxt!r} of {lid} has no words left')
            jobs.append({'line': {'start': start, 'dur': sub[-1]['t1'] + 0.05, 'words': sub},
                         'markup': ' '.join(w['w'] for w in sub), 'o': {'lead': lead, 'maxWords': 99, 'tail': tail}})
            meta.append((lid, mode, gtxt, L))
            wi += n
        if wi != len(words):
            raise ValueError(f'captions of {lid}: groups cover {wi} of {len(words)} words')
    res = run_caption_jobs(jobs)
    caps = []
    for (lid, mode, gtxt, L), r in zip(meta, res):
        if gtxt is not None:
            assert len(r) == 1, (lid, gtxt, r)
            r[0]['markup'] = gtxt
        for c in r:
            c['line'] = lid
            c['wEnd'] = None
            if mode:
                c['mode'] = mode
            caps.append(c)
    # word ends for tails; chunk -> words of its line
    for c in caps:
        W, st = bd.words(c['line']), placed[c['line']]['start']
        c['_first'] = c['t0'] + lead / fps
    # timing: each chunk holds until the next one; a line's last chunk until its last word + tail (or the next caption)
    # (a line's last chunk also ends at the first cut after its last word, but not before last word end + 2 frames,
    #  so a finished line does not ride into the next scene)
    caps.sort(key=lambda c: c['t0'])
    for i, c in enumerate(caps):
        nxt = caps[i + 1]['t0'] if i + 1 < len(caps) else None
        same = i + 1 < len(caps) and caps[i + 1]['line'] == c['line']
        last = placed[c['line']]['last_end']
        t1 = nxt if same else last + tail
        if not same:
            cut = next((x for x in cuts if x > last), None)
            if cut is not None:
                t1 = max(last + 2 / fps, min(t1, cut))
        if nxt is not None:
            t1 = min(t1, nxt)
        c['t1'] = t1
    # modes: quotes per line side, typewriter speed matched to the speech, scream quotes
    by_line = {}
    for c in caps:
        by_line.setdefault(c['line'], []).append(c)
    for lid, cs in by_line.items():
        L = bd.lines[bd.line_ix[lid]]
        for k, c in enumerate(cs):
            if c.get('mode') == 'quote':
                c['quote'] = 'both' if len(cs) == 1 else 'open' if k == 0 else 'close' if k == len(cs) - 1 else 'none'
            if L.get('quotes') and c.get('mode') == 'scream':
                if k == 0:
                    c['markup'] = '“' + c['markup']
                if k == len(cs) - 1:
                    c['markup'] = c['markup'] + '”'
            if c.get('mode') == 'type':
                n = len(plain(c['markup']))
                nxt_first = cs[k + 1]['_first'] if k + 1 < len(cs) else placed[lid]['last_end']
                span = max(0.12, (nxt_first - c['t0']) * 0.9)
                c['cps'] = round(max(24.0, n / span), 1)
    out = []
    for c in caps:
        e = {'t0': r3(c['t0']), 't1': r3(c['t1']), 'markup': c['markup']}
        for k in ('mode', 'quote', 'cps'):
            if k in c:
                e[k] = c[k]
        e['line'] = c['line']
        out.append(e)
    return out


# ---------- loudness ----------
def measure(music, beds, enabled=True):
    if not enabled:
        return 'skipped (--no-measure)'
    try:
        sys.path.insert(0, AUDIO)
        import numpy as np
        import lib
    except Exception as e:  # noqa: BLE001
        return f'skipped ({e})'
    try:
        for m in music:
            x = lib.load_music(m['track'], *(m.get('measure') or m['src']))      # measure: the part the level is set on
            if m['fx'].get('reverse'):
                x = x[::-1].copy()
            L = lib.loudness(x)
            v = L['i'] if (L.get('i') is not None and math.isfinite(L['i']) and L['i'] > -70) else L.get('ungated')
            m['measured_lufs'] = round(float(v), 1)
            m['gain_db'] = round(m['target_lufs'] - m['measured_lufs'], 1) if m.get('target_lufs') is not None else 0.0
        for b in beds:
            x = lib.load_sfx(b['sfx'], b['variant'])
            n = int(min(len(x), b['dur'] * lib.SR))
            L = lib.loudness(x[:max(n, int(0.5 * lib.SR))])
            v = L['i'] if (L.get('i') is not None and math.isfinite(L['i']) and L['i'] > -70) else L.get('ungated')
            b['clip_s'] = round(len(x) / lib.SR, 2)
            b['measured_lufs'] = round(float(v), 1)
            b['gain_db'] = round(b['target_lufs'] - b['measured_lufs'], 1)
            if b['dur'] > b['clip_s'] + 1e-3:
                b['loop'] = True
        return 'measured with audio/lib.py (integrated LUFS of the exact slice; gain_db = target_lufs - measured)'
    except Exception as e:  # noqa: BLE001
        for m in music:
            m.setdefault('gain_db', None)
        for b in beds:
            b.setdefault('gain_db', None)
        return f'skipped ({e})'


# ---------- build ----------
def build(board_path, quiet=False, do_measure=True):
    B = json.load(open(board_path))
    V = json.load(open(os.path.join(AUDIO, 'voice_lines.json')))
    bd = Board(B, V)
    fps = bd.fps
    placed = {}
    for L in bd.lines:
        lid = L['id']
        e = bd.V[lid]
        st = bd.line_start(lid)
        placed[lid] = {'start': st, 'dur': e['dur'], 'first_on': bd.first_on(lid), 'last_end': bd.last_end(lid)}
    dur = bd.end()
    # shots
    shots = []
    for i, S in enumerate(bd.shots):
        a = bd.shot_start(S['id'])
        b = bd.shot_end(S['id'])
        e = {'name': S['name'], 'start': r3(a), 'end': r3(b), 'capY': S.get('capY', 'mid')}
        if S.get('tin'):
            e['tin'] = S['tin']
        e['p'] = {'id': S['id'], 'set': S.get('set'), 'module': S['module'], 'brief': S.get('picture', '')}
        shots.append(e)
    # frame-snap shot edges (cuts land on frames)
    for e in shots:
        e['start'] = r3(round(e['start'] * fps) / fps)
        e['end'] = r3(round(e['end'] * fps) / fps)
    dur = r3(round(dur * fps) / fps)
    shots[-1]['end'] = dur
    # voice
    vlines = []
    for L in bd.lines:
        e = bd.V[L['id']]
        vlines.append({'id': e['id'], 'role': e['role'], 'tag': e['tag'], 'text': e['text'], 'start': r3(placed[L['id']]['start']), 'dur': e['dur'],
                       'file': e['file'], 'words': e['words'], 'visemes': e['visemes']})
    # music
    music = [bd.mus(mid) for mid in bd.music]
    for m in music:
        m['at'], m['len'], m['end'] = r3(m['at']), r3(m['len']), r3(m['end'])
    beds = []
    for b in B.get('beds', []):
        at, end = bd.G(b['at']), bd.G(b['until'])
        beds.append({'id': b['id'], 'sfx': b['sfx'], 'variant': b['variant'], 'at': r3(at), 'dur': r3(end - at), 'end': r3(end), 'target_lufs': b['target_lufs'],
                     'fade_in': b.get('fade_in', 0.0), 'fade_out': b.get('fade_out', 0.0), 'note': b.get('note', '')})
    mstat = measure(music, beds, do_measure)
    drops = []
    for d in B.get('drops', []):
        t0, t1 = bd.G(d['t0']), bd.G(d['t1'])
        drops.append({'id': d['id'], 't0': r3(t0), 't1': r3(t1), 'dur': r3(t1 - t0), 'slam': d['slam'], 'note': d.get('note', '')})
    sync = {k: r3(bd.hit(k)) for k in B.get('hits', {})}
    caps = build_captions(bd, placed, sorted(x['start'] for x in shots[1:]))
    music_out = []
    for m in music:
        e = {'id': m['id'], 'track': m['track'], 'src': m['src'], 'at': m['at'], 'dur': m['len'], 'end': m['end'], 'gain_db': m.get('gain_db'),
             'fade_in': m['fade_in'], 'fade_out': m['fade_out'], 'target_lufs': m['target_lufs'], 'measured_lufs': m.get('measured_lufs')}
        if m['fx']:
            fx = dict(m['fx'])
            if fx.get('rate') == 'fit':
                fx['rate'] = round(m['rate'], 4)
            e['fx'] = fx
        e['note'] = m['note']
        music_out.append(e)
    T = {
        '_doc': 'Built by tools/build_hook_timeline.py from episodes/hook/board.json (do not edit by hand: edit the board and rebuild). '
                'Engine contract: engine/anim/README.md. Mixer: T.music / T.drops / T.beds below (global seconds).',
        'fps': fps, 'dur': dur, 'bg': '#000',
        'modules': [MODULES[k] for k in ('hook_a', 'hook_b', 'hook_c', 'hook_d')],
        'shots': shots,
        'voice': {'lines': vlines},
        'captions': caps,
        'sync': sync,
        'music_doc': ('T.music: each entry plays lib.load_music(track, src[0], src[1]) (fx: reverse = play the slice backwards, rate = '
                      'resample speed so src span/rate = dur, lowpass_hz) starting at global `at` for `dur` s, scaled by gain_db (dB; '
                      'gain_db = target_lufs - measured_lufs of that exact slice, so every bed sits where the plan wants it relative '
                      'to voice files at -20 LUFS), with linear fade_in/fade_out inside the entry. Entries that join overlap by the '
                      'incoming fade_in (crossfade). Speech ducking (about 4 dB, attack 30 ms, release 250 ms, bible 4.4) and the '
                      'final loudness normalisation are applied on top by the mixer. T.drops = deliberate music drops (t0..t1 silent '
                      'on the music bus) and what slams back. T.beds: lib.load_sfx(sfx, variant) (already -18 LUFS) from `at` for '
                      '`dur` s, gain_db = target_lufs - measured, fades as given. ' + mstat),
        'music': music_out,
        'drops': drops,
        'beds': beds,
    }
    return T, bd, placed


# ---------- stats + SHOTS.md ----------
def stats(T, bd, placed):
    sh = T['shots']
    durs = [s['end'] - s['start'] for s in sh]
    cuts = len(sh) - 1
    gaps = []
    ids = [L['id'] for L in bd.lines]
    for a, b in zip(ids[:-1], ids[1:]):
        gaps.append((a, b, placed[b]['first_on'] - placed[a]['last_end']))
    words = sum(len(bd.words(i)) for i in ids)
    speech = sum(placed[i]['last_end'] - placed[i]['first_on'] for i in ids)
    drop_s = sum(d['dur'] for d in T['drops'])
    trans = {}
    for s in sh[1:]:
        k = (s.get('tin') or {}).get('type', 'cut')
        trans[k] = trans.get(k, 0) + 1
    return {
        'dur': T['dur'], 'shots': len(sh), 'cuts': cuts, 'cuts_per_min': round(cuts / (T['dur'] / 60), 1),
        'median_shot': round(statistics.median(durs), 3), 'mean_shot': round(sum(durs) / len(durs), 3),
        'min_shot': round(min(durs), 3), 'max_shot': round(max(durs), 3), 'transitions': trans,
        'gaps': gaps, 'gap_median': round(statistics.median(g for _, _, g in gaps), 3), 'gap_max': round(max(g for _, _, g in gaps), 3),
        'words': words, 'wpm_overall': round(words / (T['dur'] / 60), 1), 'wpm_speech': round(words / (speech / 60), 1),
        'music_presence': round(1 - drop_s / T['dur'], 3), 'drop_s': round(drop_s, 3), 'captions': len(T['captions']),
    }


def fmt(t):
    return f'{t:6.2f}'


def shots_md(T, bd, placed, st):
    fps = T['fps']
    out = ['# Hook shots (built)', '',
           'Generated by `python3 -I tools/build_hook_timeline.py` from `episodes/hook/board.json`; do not edit by hand. '
           'Timeline: `episodes/hook/timeline.json`. Times are global seconds (60 fps; shot edges are frame-snapped); '
           '"local" times are seconds from the shot start (what `ctx.t`, `ctx.line(id).at(word)` give inside the shot). '
           'Plan and acting notes: `docs/HOOK_BOARD.md`. Engine contract: `engine/anim/README.md`.', '',
           f"**Total {T['dur']:.3f} s · {st['shots']} shots · median shot {st['median_shot']:.2f} s (mean {st['mean_shot']:.2f}, "
           f"min {st['min_shot']:.2f}, max {st['max_shot']:.2f}) · {st['cuts']} cuts = {st['cuts_per_min']} cuts/min · "
           f"transitions {', '.join(f'{k} {v}' for k, v in sorted(st['transitions'].items()))} · voice gaps median {st['gap_median']:.2f} s, "
           f"max {st['gap_max']:.2f} s · {st['words']} words, {st['wpm_overall']} wpm overall / {st['wpm_speech']} wpm in speech · "
           f"music present {st['music_presence']*100:.1f}% ({len(T['drops'])} designed drops, {st['drop_s']:.2f} s) · {st['captions']} caption chunks.**", '',
           '| # | shot | module | start | end | dur | voice in the shot (local word onsets) | tin | capY | music under it |',
           '|---|---|---|---|---|---|---|---|---|---|']
    mus = T['music']
    for k, s in enumerate(T['shots']):
        a, b = s['start'], s['end']
        vs = []
        for L in T['voice']['lines']:
            for w in L['words']:
                g0 = L['start'] + w['t']
                if a - 1e-6 <= g0 < b - 1e-6:
                    vs.append((L['id'], w['w'], g0 - a))
        vtxt = []
        for lid in dict.fromkeys(v[0] for v in vs):
            ws = ' '.join(f"{w} {t:.2f}" for l2, w, t in vs if l2 == lid)
            vtxt.append(f"{lid[-4:] if lid.startswith('S00') else lid}: {ws}")
        under = []
        for m in mus:
            if m['at'] < b and m['end'] > a:
                under.append(f"{m['id']}")
        for d in T['drops']:
            if d['t0'] < b and d['t1'] > a:
                under.append(f"DROP {d['id']} {d['t0']:.2f}-{d['t1']:.2f}")
        tin = s.get('tin', {}).get('type', 'cut') if k else 'start'
        if s.get('tin', {}).get('dur'):
            tin += f" {s['tin']['dur']:.2f}"
        out.append(f"| {s['p']['id']} | `{s['name']}` | {s['p']['module']} | {a:.3f} | {b:.3f} | {b - a:.2f} | {'<br>'.join(vtxt) or '-'} | {tin} | {s['capY']} | {', '.join(under) or '-'} |")
    out += ['', '## Sync points (global s)', '', '| key | t | meaning |', '|---|---|---|']
    for k2, v in T['sync'].items():
        out.append(f"| {k2} | {v:.3f} | {bd.B['hits'][k2].get('note', '')} |")
    out += ['', '## Music edit (T.music)', '', '| id | track | src | at | end | gain dB | fades in/out | note |', '|---|---|---|---|---|---|---|---|']
    for m in mus:
        fx = f" fx {json.dumps(m['fx'])}" if m.get('fx') else ''
        out.append(f"| {m['id']} | {m['track']} | {m['src'][0]:.3f}-{m['src'][1]:.3f}{fx} | {m['at']:.3f} | {m['end']:.3f} | {m['gain_db']} | {m['fade_in']}/{m['fade_out']} | {m['note']} |")
    out += ['', '## Deliberate music drops (T.drops)', '', '| id | t0 | t1 | dur | slams back with | note |', '|---|---|---|---|---|---|']
    for d in T['drops']:
        out.append(f"| {d['id']} | {d['t0']:.3f} | {d['t1']:.3f} | {d['dur']:.2f} | {d['slam']} | {d['note']} |")
    out += ['', '## Ambience beds (T.beds)', '', '| id | sfx[variant] | at | end | gain dB | note |', '|---|---|---|---|---|---|']
    for b in T['beds']:
        out.append(f"| {b['id']} | {b['sfx']}[{b['variant']}] | {b['at']:.3f} | {b['end']:.3f} | {b.get('gain_db')} | {b['note']} |")
    out += ['', '## Voice lines (global)', '', '| line | role | start (file) | first word | last word end | gap before | text |', '|---|---|---|---|---|---|---|']
    gaps = {b: g for _, b, g in st['gaps']}
    for L in bd.lines:
        lid = L['id']
        out.append(f"| {lid} | {bd.V[lid]['role']} | {placed[lid]['start']:.3f} | {placed[lid]['first_on']:.3f} | {placed[lid]['last_end']:.3f} | "
                   f"{gaps.get(lid, placed[lid]['first_on']):.2f} | {bd.V[lid]['text']} |")
    out += ['', '## Shot briefs (from docs/HOOK_BOARD.md) and key local times', '']
    for s, S in zip(T['shots'], bd.shots):
        a = s['start']
        out.append(f"### {S['id']} `{s['name']}` ({S['module']}.js) {a:.3f}-{s['end']:.3f} ({s['end'] - a:.2f} s), set `{S.get('set')}`, capY {s['capY']}"
                   + (f", tin {json.dumps(S['tin'])}" if S.get('tin') else ''))
        for k in ('picture', 'camera', 'faces', 'ui', 'sfx'):
            if S.get(k):
                out.append(f"- {k}: {S[k]}")
        keys = []
        for k2, v in T['sync'].items():
            if a - 0.3 <= v <= s['end'] + 0.3:
                keys.append(f"{k2} {v - a:+.3f}")
        for m in T['music']:      # a cue that starts fresh (not a crossfade join), and every drop edge
            fresh = not any(abs(o['end'] - m['at'] - m['fade_in']) < 0.02 for o in T['music'] if o is not m)
            if fresh and a - 0.3 <= m['at'] <= s['end']:
                keys.append(f"music in: {m['track']} ({m['id']}) {m['at'] - a:+.3f}")
        for d in T['drops']:
            if a - 0.3 <= d['t0'] <= s['end']:
                keys.append(f"music DROP starts {d['t0'] - a:+.3f}")
            if a - 0.3 <= d['t1'] <= s['end'] + 0.3:
                keys.append(f"drop ends {d['t1'] - a:+.3f}")
        if keys:
            out.append('- local sync: ' + ', '.join(keys))
        out.append('')
    out += ['## Voice gaps', '', ' · '.join(f"{a[-4:]}->{b[-4:]} {g:.2f}" for a, b, g in st['gaps']), '']
    return '\n'.join(out) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--board', default=os.path.join(PROJECT, 'episodes', 'hook', 'board.json'))
    ap.add_argument('--out', default=os.path.join(PROJECT, 'episodes', 'hook', 'timeline.json'))
    ap.add_argument('--md', default=os.path.join(PROJECT, 'episodes', 'hook', 'SHOTS.md'))
    ap.add_argument('--no-measure', action='store_true')
    ap.add_argument('--quiet', action='store_true')
    a = ap.parse_args()
    T, bd, placed = build(a.board, a.quiet, not a.no_measure)
    st = stats(T, bd, placed)
    T['stats'] = {k: v for k, v in st.items() if k != 'gaps'}
    with open(a.out, 'w') as f:
        f.write(dumps(T))
    with open(a.md, 'w') as f:
        f.write(shots_md(T, bd, placed, st))
    if not a.quiet:
        print(json.dumps(T['stats']))
        print('gaps:', ' '.join(f"{b[-4:]}:{g:.2f}" for _, b, g in st['gaps']))
        for s in T['shots']:
            print(f"{s['p']['id']:4s} {s['name']:18s} {s['start']:7.3f} {s['end']:7.3f} {s['end'] - s['start']:5.2f} {s.get('tin', {}).get('type', '')}")
        print('wrote', a.out, 'and', a.md)


def dumps(T):
    """compact but diffable JSON: one shot / caption / music entry per line; voice words on one line"""
    def j(x):
        return json.dumps(x, ensure_ascii=False, separators=(', ', ': '))
    out = ['{']
    keys = list(T.keys())
    for i, k in enumerate(keys):
        v = T[k]
        comma = ',' if i < len(keys) - 1 else ''
        if k in ('shots', 'captions', 'music', 'drops', 'beds'):
            out.append(f'  {j(k)}: [')
            out += [f'    {j(e)}' + (',' if n < len(v) - 1 else '') for n, e in enumerate(v)]
            out.append('  ]' + comma)
        elif k == 'voice':
            out.append('  "voice": {"lines": [')
            out += [f'    {j(e)}' + (',' if n < len(v["lines"]) - 1 else '') for n, e in enumerate(v['lines'])]
            out.append('  ]}' + comma)
        else:
            out.append(f'  {j(k)}: {j(v)}{comma}')
    out.append('}')
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    main()
