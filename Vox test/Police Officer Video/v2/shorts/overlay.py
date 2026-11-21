"""shorts.overlay: draws one Short's overlay events (shorts.edit) on every vertical frame, plus the per-frame picture
effects (flashes, shakes, glitches, the REWIND loop).

    O = Overlay(E)     O(cv, t, i, vshot)       skia pass in 1080 x 1920 design units (captions, HUD, slams, UI, CTA)
    P = Post(E)        P.shake(t) -> (dx, dy)   P.apply(img, t, i, vs)   P.final(img, t, i, vs)
"""
import math
import numpy as np
import cv2
import vfx
from engine.core import clamp, ease_out_cubic, noise1, Pen, text, rrect, oval
from engine import hud as H


TAG_MIN = 62          # px at 1080 width: tags, bubbles and form rows stay readable on a phone
TAG_MIN_DUR = 1.0     # s


def normalise_events(events):
    """Readability floor for the small inserts (critic: 42-46 px tags flashed for 0.9 s are unreadable on a phone)."""
    for e in events:
        if e['type'] in ('tag', 'bubble'):
            e['size'] = max(TAG_MIN, e.get('size', 40))
            e['dur'] = max(TAG_MIN_DUR, e.get('dur', 1.0))
    return events


class Overlay:
    def __init__(self, E):
        self.E = E
        self.ev = E.events
        self.huds = E.huds
        self.chunks = E.chunks
        self.words = E.words
        clips = E.T['clips']
        self.clip_who = [c['who'] for c in clips]
        self.clip_fx = [c.get('fx') for c in clips]
        first, last = {}, {}
        for k, c in enumerate(self.chunks):
            first.setdefault(c['clip'], k); last[c['clip']] = k
        self.first, self.last = first, last
        self.nocap = [(e['t'], e['t'] + e.get('dur', 1.0)) for e in self.ev if e['type'] in ('nocap', 'endcard')]
        # a slam that shows the caption's own words hides that caption chunk (no doubled text)
        from timing import _norm, SMALL
        self._norm, self._small = _norm, SMALL
        self.slam_words = [(e['t'] - 0.02, e['t'] + e.get('dur', 1.0), set(_norm(w) for w in e['text'].split()) - SMALL - {''})
                           for e in self.ev if e['type'] == 'slam' and e.get('text')]

    # ---------------------------------------------------------------- HUD
    def hud_state(self, t):
        st, tv, tc = {}, -1e9, -1e9
        for (tt, s) in self.huds:
            if tt <= t:
                if s.get('pop', True):
                    if 'value' in s or 'score' in s: tv = tt
                    if 'clock' in s and s.get('clock') != st.get('clock') or s.get('clock_pop'): tc = tt
                st.update(s)
            else: break
        return st, t - tv, t - tc

    def draw_hud(self, cv, t, vs):
        st, u, uc = self.hud_state(t)
        if not st or st.get('hide'): return
        if st.get('clock'):
            vfx.clock(cv, st['clock'], uc)
        if st.get('value') is not None:
            vfx.hud_pill(cv, u, st.get('title', ''), st['value'], st.get('accent', vfx.RED), meter=st.get('meter'),
                         flash=clamp(1 - u / 0.15) * 0.6 if st.get('flash') else 0.0)
        if st.get('score'):
            vfx.scoreboard(cv, u, st['score'][0], st['score'][1])
        if st.get('wave'):                                    # S2: live mini waveform under the playback counter
            amp = st.get('wave_amp', 1.0)
            H.waveform(cv, vfx.VW / 2 - 200, vfx.VY_HUD + 112, 400, 52 * amp, t, st.get('wave_c', '#ff5a5f'), 7, 1.0, amp > 0.05,
                       230, 5.0, 3.0)

    # ---------------------------------------------------------------- captions
    def draw_caption(self, cv, t):
        for (a, b) in self.nocap:
            if a <= t < b: return
        for k, c in enumerate(self.chunks):
            if c['t'] <= t < c['t1']:
                cw = set(self._norm(w) for w in c['text'].split()) - self._small
                if any(a <= t < b and (cw & ws) for a, b, ws in self.slam_words): return
                who = self.clip_who[c['clip']]
                ws = c['text'].split()
                q = (who != 'N' and self.first.get(c['clip']) == k, who != 'N' and self.last.get(c['clip']) == k)
                key, colr = c.get('key'), c.get('colour')
                if who in ('Y', 'M') and self.clip_fx[c['clip']] and key is None:
                    key, colr = len(ws) - 1, (vfx.AMBER if who == 'Y' else vfx.PINK)
                vfx.caption(cv, ws, key, colr, t - c['t'], (t - c['kt']) if c.get('kt') is not None and key == c.get('key') else -1, q)
                return

    # ---------------------------------------------------------------- events
    def __call__(self, cv, t, i, vs):
        E = self.E
        kinds = getattr(vs.src, 'long_kind', None)
        if kinds == 'door' and not vs.fx.get('no_doorbell'):
            vfx.doorbell(cv, t, '12:%02d:%02d AM' % (36 + int(t // 60), (7 + int(t)) % 60))
        late = []
        for e in self.ev:
            u = t - e['t']
            typ = e['type']
            dur = e.get('dur', 1.0)
            if typ == 'subscribe':
                if -0.5 <= u <= 1.8: late.append(e)
                continue
            if u < 0 or u > dur: continue
            if typ in ('slam', 'stamp', 'tag', 'bubble', 'label', 'loop', 'ghost'): late.append(e); continue
            if typ == 'panel_dim':
                Pen(cv).fill(rrect(-10, -10, vfx.VW + 20, vfx.VH + 20, 0), '#000000', 255 * e.get('k', 0.45) * clamp(u / 0.12))
            elif typ == 'wave':
                rows = []
                for r in e['rows']:
                    r = dict(r)
                    if 'p' in r:
                        a, b = r.pop('p'); r['progress'] = clamp((t - a) / max(1e-3, b - a)); r['live'] = a <= t <= b
                    rows.append(r)
                ph = None
                if e.get('play'):
                    a, b = e['play']; ph = clamp((t - a) / max(1e-3, b - a))
                vfx.wave_panel(cv, u, rows, e.get('title', 'SHOULDER RADIO'), e.get('y', 0.27 * vfx.VH), e.get('h'), ph)
                if e.get('line') is not None and t >= e['line']:
                    x = 50 + 18 * 1.18 + (900 - 36 * 1.18) * e.get('line_x', 0.5)
                    hh = e.get('h') or 150 + 150 * len(e['rows'])
                    y0 = e.get('y', 0.27 * vfx.VH)
                    k = ease_out_cubic(clamp((t - e['line']) / 0.12))
                    Pen(cv).seg((x, y0 + 40), (x, y0 + 40 + (hh - 50) * k), 7, vfx.RED, 255)
            elif typ == 'phone':
                st, ts = e['states'][0][1], e['states'][0][0]
                for (tt, s_) in e['states']:
                    if t >= tt: st, ts = s_, tt
                k = (1.0 + 0.04 * u)
                cv.save(); cv.translate(vfx.SAFE_CX, e.get('y', 0.40 * vfx.VH)); cv.scale(k, k)
                cv.translate(-vfx.SAFE_CX, -e.get('y', 0.40 * vfx.VH))
                H.phone(cv, st, t - ts, name=e.get('name', 'MUM'), x=vfx.SAFE_CX + 6 * noise1(t * 0.9, 3), y=e.get('y', 0.40 * vfx.VH),
                        scale=e.get('scale', 1.4), timer=(t - ts) if st == 'connected' else None)
                cv.restore()
            elif typ == 'notebook':
                vfx.notebook(cv, u, e['rows'], ticks=[x - e['t'] for x in e['ticks']], y=e.get('y', 0.38 * vfx.VH))
            elif typ == 'complaint':
                hl = {r: t - tt for r, tt in e.get('hl', {}).items()}
                rv = None
                if e.get('reveal'):
                    a, b = e['reveal']; rv = clamp((t - a) / max(1e-3, b - a))
                vfx.complaint(cv, u, e['rows'], hl.items(), blur_row=e.get('blur_row'), reveal=rv, y=e.get('y', 0.34 * vfx.VH))
            elif typ == 'rule':
                vfx.rule_card(cv, e['n'], e['text'], u)
            elif typ == 'bodycam':
                off = e.get('off')
                vfx.bodycam(cv, u, rec=not (off is not None and t >= off))
            elif typ == 'endcard':
                vfx.endcard(cv, u, e['question'], e.get('sub', 'FULL VIDEO ON THE CHANNEL'), [h - e['t'] for h in e.get('hits', [])],
                            y=e.get('y', 0.44 * vfx.VH), dur=dur, title=e.get('title'))
            elif typ == 'callout':
                vfx.callout(cv, u, e['x'], e['y'], e.get('r', 90), e.get('label'), e.get('c', vfx.RED), dur, e.get('lx'), e.get('ly'),
                            e.get('size', 64), e.get('to'))
            elif typ == 'comments':
                vfx.comments(cv, u, e['prompt'], e['word'], dur=dur, y=e.get('y', 0.30 * vfx.VH))
            elif typ == 'split_labels':
                hh = vfx.VH / 2
                vfx.outlined(cv, e.get('top', 'HIM'), 60, hh - 40, 80, e.get('ct', vfx.RED), 0.12, 'left', 0.4)
                vfx.outlined(cv, e.get('bot', 'YOU'), 60, vfx.VH - 0.21 * vfx.VH, 80, e.get('cb', vfx.AMBER), 0.12, 'left', 0.4)
        for e in late:
            u = t - e['t']; typ = e['type']; dur = e.get('dur', 1.0)
            if typ == 'slam':
                vfx.slam(cv, u, e['text'], e.get('c', vfx.RED), e.get('y', 0.40 * vfx.VH), e.get('size', 150), dur, e.get('rot', -3.0),
                         sub=e.get('sub'))
            elif typ == 'stamp':
                vfx.stamp(cv, u, e['text'], e.get('c', vfx.RED), e.get('x', vfx.SAFE_CX), e.get('y', 0.33 * vfx.VH), e.get('size', 96),
                          e.get('rot', -9.0), dur)
            elif typ == 'tag':
                vfx.tag(cv, u, e['text'], e.get('x', vfx.SAFE_CX), e.get('y', 0.30 * vfx.VH), e.get('style', 'red'), e.get('pin'),
                        max(TAG_MIN, e.get('size', 40)), hold=dur - 0.12)
            elif typ == 'bubble':
                H.speech_bubble(cv, e['lines'], e.get('x', vfx.SAFE_CX), e.get('y', 0.30 * vfx.VH), u, size=max(TAG_MIN, e.get('size', 44)),
                                fade=0.15)
            elif typ == 'label':
                a = 255 * clamp(u / 0.06) * clamp((dur - u) / 0.1)
                sz = e.get('size', 70)
                sz = min(sz, sz * 0.88 * vfx.VW / max(1.0, vfx.twidth(e['text'], sz)))     # never wider than the frame
                vfx.outlined(cv, e['text'], e.get('x', vfx.SAFE_CX), e.get('y', 0.3 * vfx.VH), sz, e.get('c', vfx.WHITE),
                             0.12, e.get('align', 'center'), 0.4, a)
            elif typ == 'ghost':
                a = 150 * clamp(u / 0.1) * clamp((dur - u) / 0.15)
                s_ = e['text'][:max(1, int(len(e['text']) * clamp(u / max(0.2, dur * 0.7))))]
                text(cv, s_, vfx.SAFE_CX, e.get('y', 0.55 * vfx.VH), 700, 64, '#ffffff', a, 0.04, 'center', 0.6)
            elif typ == 'loop':
                vfx.loop_icon(cv, u, y=e.get('y', 0.30 * vfx.VH))
            elif typ == 'subscribe':
                vfx.subscribe(cv, u, y=e.get('y', 0.50 * vfx.VH), x=e.get('x', vfx.SAFE_CX), hand=e.get('hand', 'cursor'),
                              from_=e.get('from_'), lead=e.get('lead', 0.5))
        self.draw_hud(cv, t, vs)
        self.draw_caption(cv, t)
        for e in self.ev:
            if e['type'] == 'rewind' and 0 <= t - e['t'] <= e.get('dur', 0.14):
                vfx.rewind_label(cv, t - e['t'])


class Post:
    def __init__(self, E):
        self.E = E
        self.ev = E.events
        self.flashes = [e for e in self.ev if e['type'] == 'flash']
        self.shakes = [e for e in self.ev if e['type'] in ('shake', 'slam') and e.get('shake', e['type'] == 'shake')]
        self.glitches = [e for e in self.ev if e['type'] == 'glitch']
        self.rewinds = [e for e in self.ev if e['type'] == 'rewind']

    def shake(self, t):
        dx = dy = 0.0
        for e in self.shakes:
            u = t - e['t']; d = e.get('sdur', 0.22)
            if 0 <= u <= d:
                a = e.get('amp', 14.0) * (1 - u / d)
                dx += a * noise1(u * 45, 11); dy += a * noise1(u * 45, 12)
        return dx, dy

    def apply(self, img, t, i, vs):
        for e in self.rewinds:                         # the REWIND glitch runs under the overlay: its label stays sharp
            u = t - e['t']; d = e.get('dur', 0.14)
            if 0 <= u <= d:
                img = vfx.rewind_fx(img, 0.6 + 0.4 * math.sin(math.pi * u / d), seed=i * 7 + 1)
        for e in self.glitches:
            u = t - e['t']
            if 0 <= u <= e.get('dur', 0.15):
                img = vfx.rewind_fx(img, e.get('k', 0.8) * (1 - u / e.get('dur', 0.15) * 0.5), seed=i)
        for e in self.flashes:
            u = t - e['t']; d = e.get('dur', 0.07)
            if 0 <= u <= d:
                img = vfx.flash(img, e.get('c', '#ff1a1a'), e.get('k', 0.55) * (1 - u / d))
        return img

    def final(self, img, t, i, vs):
        return img
