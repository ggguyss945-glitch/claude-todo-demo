"""engine.hud: screen overlays styled after the references (all drawn on a skia canvas in DESIGN coordinates, after the grade).

Every function takes `cv` (the canvas passed to render_frame's hud callback) and, where animated, `t` = seconds since the
element appeared (t < 0 draws nothing). Text marked *like this* is drawn in the threat red.
Timing constants (VISUAL_SPEC f): RULE_POP 0.07 s, RULE_TYPE ~3 s, RULE_HOLD 1.5 s, ALERT_HOLD 1.2 s, TAG_FADE 1.0 s.

caption(cv, text, alpha=255)                       v1 caption: small white uppercase, letter-spaced, low, soft shadow
header(cv, right, corner='12:36 AM', alpha=255)    v1 "HOUSE RULES / RULE n OF 7" header
rule_card(cv, n, text, t, total=7, icon=None, type_dur=None, scrim=0.35)
    "RULE" + numeral popping in (<= 4 frames), red rule line, text typed on with *red* keywords, progress dashes.
    Pair it with post={'blur': 6, 'dim': 0.35} for the reference's dimmed, blurred background.
rule_times(text, type_dur=None) -> {'pop', 'line', 'type0', 'type1', 'end'} seconds after the card starts (for SFX: ui_pop, typing)
tag(cv, text, x, y, style='red', t=None, ...)       styles: 'alert' (NEVER OPEN UP box, 58 % W, hard cut), 'red' (red label,
    pops), 'white' (white label, pops), 'pill' (outlined pill, fades 1 s), 'dark' (navy label). Returns (x0, y0, x1, y1).
speech_bubble(cv, lines, x, y, t=None, tail=(-60, 50), size=28)   dark box, white dashed border, tail, fades in 1 s
waveform(cv, x, y, w, h, t, color='#5b7fe0', seed=0, progress=1.0, live=True)
waveform_panel(cv, x, y, w, h, title, rows, t, playhead=None)   rows: [{'label', 'color', 'seed', 'progress', 'live'}]
dispatch_panel(cv, x, y, title, lines, t, w=520)    small navy info panel, lines typed on
phone(cv, state, t, name='MUM', x=960, y=560, scale=1.0, timer=None, hand=True, skin='#c0aa9e')
    state: 'calling' | 'busy' | 'incoming' | 'connected' | 'voicemail' | 'emergency' (911). Phone ~600 design px tall.
doorbell_hud(cv, t, name='FRONT DOOR', clock=(0, 36, 7), date='OCT 14', motion=None, signal=3, battery=0.78, ir=False, talk=False)
    LIVE pill, camera name, ticking timestamp, motion box (x, y, w, h) with corner brackets, signal, battery, IR badge.
bodycam_hud(cv, t, unit='UNIT 24-07', badge='4471', clock=(0, 36, 7), date='2026-10-14', rec=True)
typed(s, t, dur) -> visible prefix;  rich_text(cv, s, x, y, ...) -> width (with *red* markup and typing)
"""
import math
import numpy as np
import skia
from .core import (DW, DH, LINE, Pen, col, mix, text, text_width, wrap, typeface, rrect, rect, oval, poly, smooth, union, minus,
                   clamp, ease, ease_out_back, ease_out_cubic, prog, noise1, hash01)

RED = '#e3262e'
RED_BOX = '#c0161c'
RULE_POP, RULE_TYPE, RULE_HOLD, ALERT_HOLD, TAG_FADE = 0.07, 3.0, 1.5, 1.2, 1.0


# ------------------------------------------------------------------ text helpers
def typed(s, t, dur):
    if t <= 0: return ''
    n = len(s); k = int(math.floor(n * clamp(t / max(1e-6, dur))))
    return s[:k]


def _segments(s):
    out, red = [], False
    for i, part in enumerate(s.split('*')):
        if part: out.append((part, red))
        red = not red
    return out


def rich_text(cv, s, x, y, weight=800, size=30, c='#ffffff', key=RED, a=255, spacing=0.04, align='center', shadow=0.6,
              reveal=None, glow=None):
    """Text with *red* keywords. reveal = number of visible characters (markup excluded, may be fractional: the next
    character fades in). Returns the full width."""
    segs = _segments(s)
    plain = ''.join(p for p, _ in segs)
    total = text_width(plain, weight, size, spacing)
    x0 = x - total / 2 if align == 'center' else (x - total if align == 'right' else x)
    rv = len(plain) if reveal is None else max(0.0, reveal)
    full = int(math.floor(rv)); frac = rv - full
    cx = x0; used = 0
    for part, red in segs:
        if used > full: break
        colr = key if red else c; n = len(part)
        k = min(n, full - used)
        if k > 0: text(cv, part[:k], cx, y, weight, size, colr, a, spacing, 'left', shadow, glow)
        if k < n and frac > 0:
            xx = cx + (text_width(part[:k], weight, size, spacing) + spacing * size if k else 0.0)
            text(cv, part[k], xx, y, weight, size, colr, a * frac, spacing, 'left', shadow, glow)
        cx += text_width(part, weight, size, spacing) + spacing * size
        used += n
    return total


def wrap_rich(s, weight, size, maxw, spacing=0.0):
    """Wrap text with *red* markup; returns lines that each carry their own balanced markup. Punctuation glued to a red
    word (e.g. '*answer*.') stays attached."""
    words, red, open_end = [], False, False     # each word = list of (text, red) segments
    for part in s.split('*'):
        if part:
            toks = part.split(' ')
            for k, tok in enumerate(toks):
                if tok == '': continue
                if k == 0 and words and open_end and not part[0].isspace():
                    words[-1].append((tok, red))
                else:
                    words.append([(tok, red)])
            open_end = not part[-1].isspace()
        red = not red
    lines, cur, curw = [], [], 0.0
    sp = text_width(' ', weight, size, spacing) + spacing * size
    for w in words:
        ww = text_width(''.join(t for t, _ in w), weight, size, spacing)
        if cur and curw + sp + ww > maxw:
            lines.append(cur); cur, curw = [], 0.0
        curw = curw + sp + ww if cur else ww
        cur.append(w)
    if cur: lines.append(cur)
    return [' '.join(''.join('*%s*' % t if r else t for t, r in w) for w in l) for l in lines]


# ------------------------------------------------------------------ v1 caption + header
_CAP_BLUR = {}


def caption(cv, s, alpha=255):
    """v1 caption plus a soft dark halo under each line (blurred, no visible box) so the white text stays readable over
    pale skin, hands, props and lit walls (VISUAL_SPEC f: soft dark drop shadow, no box)."""
    s = s.upper()
    lines = wrap(s, 600, 31, 1300, 0.035)
    y0 = 975 - (len(lines) - 1) * 42
    if 'mf' not in _CAP_BLUR: _CAP_BLUR['mf'] = skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 16.0)
    for i, l in enumerate(lines):
        w = text_width(l, 600, 31, 0.035)
        yb = y0 + i * 42
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(DW / 2 - w / 2 - 26, yb - 34, w + 52, 46), 22, 22),
                     skia.Paint(Color=skia.Color4f(0, 0, 0, 0.42 * alpha / 255).toColor(), AntiAlias=True, MaskFilter=_CAP_BLUR['mf']))
    for i, l in enumerate(lines): text(cv, l, DW / 2, y0 + i * 42, 600, 31, '#ffffff', alpha, 0.035, 'center', 1.0)


def header(cv, right, corner='12:36 AM', alpha=255):
    left = 'HOUSE RULES'
    w = text(cv, left, 44, 42, 600, 13, '#8c8c98', 120 * alpha / 255, 0.24, 'left')
    text(cv, '/   ' + right, 44 + w + 16, 42, 600, 13, '#c4c4ce', 150 * alpha / 255, 0.24, 'left')
    text(cv, corner, DW - 44, 42, 600, 13, '#8c8c98', 100 * alpha / 255, 0.24, 'right')


# ------------------------------------------------------------------ rule card
def rule_times(text_, type_dur=None):
    n = len(text_.replace('*', ''))
    td = type_dur if type_dur is not None else clamp(n * 0.045, 1.6, RULE_TYPE)
    return {'pop': 0.0, 'line': 0.05, 'type0': 0.35, 'type1': 0.35 + td, 'end': 0.35 + td + RULE_HOLD}


def rule_card(cv, n, text_, t, total=7, icon=None, type_dur=None, scrim=0.35, alpha=255, y=0.0):
    if t < 0: return
    pen = Pen(cv)
    tm = rule_times(text_, type_dur)
    if scrim:
        pen.radial(None, DW / 2, DH / 2 + y, 900, [(0, '#000000', 255 * scrim), (1, '#000000', 255 * scrim * 0.45)], sy=0.75)
    y0 = y
    # "RULE" label (0.30 H), numeral centred at 0.42 H with a 9 % H cap height, red line 0.52 H, text from 0.6 H, dashes 0.8 H
    text(cv, 'RULE', DW / 2, 330 + y0, 700, 17, '#b8b8c2', alpha * 0.85 * clamp(t / 0.05), 0.5, 'center', 0.4)
    u = clamp(t / RULE_POP)
    s = 1.18 - 0.18 * ease_out_cubic(u)
    cv.save(); cv.translate(DW / 2, 452 + y0); cv.scale(s, s)
    text(cv, '%02d' % n, 0, 48, 800, 138, '#ffffff', alpha * u, 0.0, 'center', 0.7)
    cv.restore()
    lu = ease_out_cubic(prog(t, tm['line'], tm['line'] + 0.28))
    if lu > 0:
        hw = 150 * lu
        pen.fill(rrect(DW / 2 - hw, 556 + y0, hw * 2, 4, 2), RED, alpha)
    lines = wrap_rich(text_.upper(), 800, 31, 760, 0.045)
    total_chars = sum(len(l.replace('*', '')) for l in lines)
    shown = total_chars * clamp((t - tm['type0']) / max(1e-6, tm['type1'] - tm['type0']))
    used = 0
    for i, l in enumerate(lines):
        n_l = len(l.replace('*', ''))
        rv = clamp(shown - used, 0, n_l)
        if rv > 0: rich_text(cv, l, DW / 2, 648 + y0 + i * 44, 800, 31, '#ffffff', RED, alpha, 0.045, 'center', 0.6, reveal=rv)
        used += n_l
    da = alpha * clamp((t - 0.1) / 0.15)
    if da > 0:
        dw_, gap = 34, 12; x0 = DW / 2 - (total * dw_ + (total - 1) * gap) / 2
        yd = max(862, 648 + (len(lines) - 1) * 44 + 70) + y0
        for k in range(total):
            c, a = ('#ffffff', 90) if k + 1 > n else (('#ffffff', 210) if k + 1 < n else (RED, 255))
            pen.fill(rrect(x0 + k * (dw_ + gap), yd, dw_, 4, 2), c, a * da / 255)
    if icon is not None:
        ia = alpha * 0.45 * clamp(t / 0.3)
        pen.line(rrect(150, 250 + y, 190, 190, 22), 3, '#ffffff', ia * 0.6)
        icon(pen, 245, 345 + y, 120, ia)


# ------------------------------------------------------------------ tags
def _anim(style, anim):
    if anim: return anim
    return {'alert': 'cut', 'red': 'pop', 'white': 'pop', 'pill': 'fade', 'dark': 'fade'}.get(style, 'pop')


def tag(cv, s, x, y, style='red', t=None, alpha=255, size=None, w=None, anim=None, fade=TAG_FADE):
    """Label at centre (x, y). Returns its box. t = seconds since it appeared (None = fully shown)."""
    pen = Pen(cv)
    a = alpha; sc = 1.0
    an = _anim(style, anim)
    if t is not None:
        if t < 0: return None
        if an == 'pop':
            a *= clamp(t / 0.06); sc = 0.72 + 0.28 * ease_out_back(clamp(t / 0.2), 2.2)
        elif an == 'fade':
            a *= ease(t / fade)
    plain = s.replace('*', '')
    if style == 'alert':
        size = size or 92
        bw = w or DW * 0.58
        bh = size * 1.55
        cv.save(); cv.translate(x, y); cv.scale(sc, sc)
        box = rrect(-bw / 2, -bh / 2, bw, bh, 8)
        pen.fill(box, '#0a090b', a * 0.86)
        pen.line(box, 9, RED_BOX, a * 0.35, blur=10)
        pen.line(box, 3.5, '#d4252c', a)
        rich_text(cv, s, 0, size * 0.36, 800, size, '#e5323a', '#ff5a5f', a, 0.04, 'center', 0.0, glow=('#ff1f2a', 120, 14))
        cv.restore()
        return (x - bw / 2, y - bh / 2, x + bw / 2, y + bh / 2)
    size = size or (30 if style == 'pill' else 26)
    sp = 0.1
    tw = text_width(plain, 800, size, sp)
    padx, h = size * 0.95, size * 1.75
    bw = w or tw + padx * 2
    cv.save(); cv.translate(x, y); cv.scale(sc, sc)
    if style == 'pill':
        box = rrect(-bw / 2, -h / 2, bw, h, h / 2)
        pen.fill(box, '#0c0d12', a * 0.7)
        pen.line(box, 3.2, '#b9bcc8', a * 0.9)
        rich_text(cv, s, 0, size * 0.36, 800, size, '#d9dbe3', RED, a, sp, 'center', 0.0)
    elif style == 'white':
        box = rrect(-bw / 2, -h / 2, bw, h, 6)
        pen.shadow(box, 0, 6, 12, '#000000', a * 0.5)
        pen.fill(box, '#f4f4f2', a)
        rich_text(cv, s, 0, size * 0.36, 800, size, '#16171c', RED_BOX, a, sp, 'center', 0.0)
    elif style == 'dark':
        box = rrect(-bw / 2, -h / 2, bw, h, 6)
        pen.fill(box, '#0b1222', a * 0.9); pen.line(box, 2, '#3a4a6c', a)
        rich_text(cv, s, 0, size * 0.36, 800, size, '#e8ecf6', RED, a, sp, 'center', 0.0)
    else:  # red
        box = rrect(-bw / 2, -h / 2, bw, h, 6)
        pen.shadow(box, 0, 6, 12, '#000000', a * 0.5)
        pen.fill(box, RED_BOX, a)
        rich_text(cv, s.replace('*', ''), 0, size * 0.36, 800, size, '#ffffff', '#ffffff', a, sp, 'center', 0.0)
    cv.restore()
    return (x - bw / 2, y - h / 2, x + bw / 2, y + h / 2)


def speech_bubble(cv, lines, x, y, t=None, tail=(-60, 50), size=28, alpha=255, fade=TAG_FADE, w=None):
    """Dashed speech tag centred at (x, y); tail points from the lower-left corner by `tail` (dx, dy). lines: str or list."""
    if isinstance(lines, str): lines = [lines]
    a = alpha
    if t is not None:
        if t < 0: return None
        a *= ease(t / fade)
    pen = Pen(cv)
    sp = 0.07
    tw = max(text_width(l.replace('*', '').upper(), 800, size, sp) for l in lines)
    lh = size * 1.45
    bw = w or tw + size * 2.2; bh = lh * len(lines) + size * 1.1
    x0, y0 = x - bw / 2, y - bh / 2
    box = rrect(x0, y0, bw, bh, 10)
    tx, ty = x0 + bw * 0.12, y0 + bh
    tl = poly([(tx - 18, ty - 1), (tx + 22, ty - 1), (tx + tail[0], ty + tail[1])])
    shape = union(box, tl)
    pen.fill(shape, '#0b0b10', a * 0.86)
    pen.dashed(shape, 3.2, '#f2f2f2', a, 15, 9)
    for i, l in enumerate(lines):
        yy = y0 + size * 0.55 + lh * (i + 0.5) + size * 0.36
        rich_text(cv, l.upper(), x, yy, 800, size, '#f2f2f2', RED, a, sp, 'center', 0.0)
    return (x0, y0, x0 + bw, y0 + bh)


# ------------------------------------------------------------------ waveforms and panels
def _env(n, seed, t, live):
    """Speech-like amplitude envelope for n bars (vectorised)."""
    i = np.arange(n, dtype=np.float64)
    ph = t * 3.2 if live else 0.0
    a = 0.55 + 0.45 * noise1(i * 0.09 + seed * 13.1 + ph, seed + 41)
    b = 0.5 + 0.5 * noise1(i * 0.31 + seed * 3.7 + ph * 2.1, seed + 42)
    gate = np.clip((noise1(i * 0.035 + seed * 7.3 + ph * 0.4, seed + 43) + 0.35) * 2.0, 0, 1)
    return np.clip(a * b * gate * 1.25 + 0.04 * hash01(np.arange(n), seed), 0, 1)


def waveform(cv, x, y, w, h, t, color='#5b7fe0', seed=0, progress=1.0, live=True, alpha=255, bar=3.2, gap=2.2, dim='#4a5068'):
    """Mirrored bar waveform centred vertically on y, from x to x + w. Bars past `progress` are dim."""
    pen = Pen(cv)
    n = max(1, int(w / (bar + gap)))
    amps = _env(n, seed, t, live) * h / 2
    p = skia.Path(); pd = skia.Path()
    for i in range(n):
        amp = float(amps[i]); bx = x + i * (bar + gap)
        (p if i / n <= progress else pd).addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(bx, y - amp - 1, bar, amp * 2 + 2), bar / 2, bar / 2))
    pen.fill(pd, dim, alpha * 0.7)
    pen.fill(p, color, alpha)


def _panel(pen, x, y, w, h, a, title=None, dot=False, t=0.0):
    box = rrect(x, y, w, h, 8)
    pen.fill(box, '#0a1120', a * 0.92)
    pen.line(box, 2, '#2c3a58', a)
    if title:
        text(pen.cv, title, x + 18, y + 26, 700, 13, '#8fa0c6', a, 0.18, 'left')
        if dot:
            pen.fill(oval(x + w - 20, y + 21, 4.5), RED, a * (0.55 + 0.45 * (math.sin(t * 6.0) > 0)))


def waveform_panel(cv, x, y, w, h, title='TRUCK SPEAKER', rows=None, t=0.0, playhead=None, alpha=255, appear=None):
    """Navy panel with labelled waveform rows (reference 'waveform_panels'). appear: seconds since shown (fade 0.25 s).
    Row keys: label, color ('blue' | 'red' | '#hex' | 'split' = blue then red from row['split'] (0..1)), seed, progress,
    live, marker=(f0, f1, 'PAUSE TOO LONG'): a red band over that stretch with its label, flashing while the playhead
    (panel playhead, 0..1) is inside it. Labels scale with the panel width (designed at 760)."""
    a = alpha * (1.0 if appear is None else ease(appear / 0.25))
    if a <= 0: return
    pen = Pen(cv)
    rows = rows or [{'label': 'PLAY 1', 'color': '#5b7fe0', 'seed': 1}]
    ks = clamp(w / 760.0, 1.0, 1.6)
    _panel(pen, x, y, w, h, a, None)
    if title:
        text(cv, title, x + 18 * ks, y + 26 * ks, 700, 13 * ks, '#8fa0c6', a, 0.18, 'left')
        pen.fill(oval(x + w - 22 * ks, y + 21 * ks, 4.5 * ks), RED, a * (0.55 + 0.45 * (math.sin(t * 6.0) > 0)))
    top = 46 * ks
    rh = (h - top - 4) / len(rows)
    for k, r in enumerate(rows):
        ry = y + top + rh * k
        x0, ww = x + 18 * ks, w - 36 * ks
        text(cv, r.get('label', ''), x0, ry + 14 * ks, 700, 11 * ks, '#7f8aa6', a, 0.16, 'left')
        cy, hh = ry + rh * 0.58, rh * 0.62
        mk = r.get('marker')
        if mk:
            f0, f1, lab = mk
            live = playhead is not None and f0 <= playhead <= f1 + 0.04
            ma = (0.55 + 0.45 * (math.sin(t * 14.0) > 0)) if live else 0.35
            band = rect(x0 + ww * f0, cy - hh * 0.62, ww * (f1 - f0), hh * 1.24)
            pen.fill(band, RED, a * 0.32 * ma)
            pen.line(band, 2.0, RED, a * 0.9 * ma)
            if lab: text(cv, lab, x0 + ww * (f0 + f1) / 2, cy - hh * 0.62 - 8 * ks, 800, 12 * ks, '#ff5a60', a * (0.6 + 0.4 * ma), 0.14, 'center')
        col_ = r.get('color', 'blue')
        if col_ == 'split':
            fs = clamp(r.get('split', 0.5))
            for (cx0, cx1, cc) in ((x0 - 2, x0 + ww * fs, '#5b7fe0'), (x0 + ww * fs, x0 + ww + 4, '#e0444c')):
                cv.save(); cv.clipRect(skia.Rect.MakeLTRB(cx0, cy - hh, cx1, cy + hh))
                waveform(cv, x0, cy, ww, hh, t, cc, r.get('seed', k), r.get('progress', 1.0), r.get('live', True), a, bar=3.2 * ks, gap=2.2 * ks)
                cv.restore()
        else:
            c = {'blue': '#5b7fe0', 'red': '#e0444c'}.get(col_, col_)
            waveform(cv, x0, cy, ww, hh, t, c, r.get('seed', k), r.get('progress', 1.0), r.get('live', True), a, bar=3.2 * ks, gap=2.2 * ks)
    if playhead is not None:
        px = x + 18 * ks + (w - 36 * ks) * clamp(playhead)
        pen.seg((px, y + top - 2), (px, y + h - 8), 2.2 * ks, '#f2f2f2', a * 0.9)
        pen.fill(oval(px, y + top - 4, 5 * ks), '#f2f2f2', a * 0.9)


def dispatch_panel(cv, x, y, title, lines, t, w=520, alpha=255, cps=34.0):
    """Small navy info panel (911 dispatch). Lines are typed at `cps` characters per second."""
    if t < 0: return
    a = alpha * ease(t / 0.2)
    pen = Pen(cv)
    h = 52 + 38 * len(lines)
    _panel(pen, x, y, w, h, a, title, dot=True, t=t)
    pen.seg((x + 14, y + 40), (x + w - 14, y + 40), 1.2, '#2c3a58', a)
    shown = max(0.0, (t - 0.2) * cps)
    for i, l in enumerate(lines):
        n = len(l.replace('*', ''))
        if shown > 0:
            rich_text(cv, l.upper(), x + 18, y + 72 + 38 * i, 800, 17, '#e9edf7', RED, a, 0.06, 'left', 0.0, reveal=min(n, shown))
        shown -= n


# ------------------------------------------------------------------ phone UI
def _handset(pen, cx, cy, s, c='#ffffff', a=255, rot=135):
    cv = pen.cv; cv.save(); cv.translate(cx, cy); cv.rotate(rot); cv.scale(s / 40.0, s / 40.0)
    p = smooth([(-16, -6), (-12, -12), (12, -12), (16, -6), (12, -2), (7, -6), (-7, -6), (-12, -2)], True, 0.6)
    pen.fill(p, c, a); cv.restore()


def _button(pen, cx, cy, r, c, a, icon='end', t=0.0):
    pen.shadow(oval(cx, cy, r), 0, 4, 8, '#000000', a * 0.4)
    pen.fill(oval(cx, cy, r), c, a)
    if icon == 'end': _handset(pen, cx, cy + 2, r * 1.15, '#ffffff', a, 180)
    elif icon == 'accept': _handset(pen, cx, cy, r * 1.15, '#ffffff', a, 0)
    elif icon == 'pause':
        pen.fill(rrect(cx - r * 0.3, cy - r * 0.36, r * 0.2, r * 0.72, 3), '#16171c', a)
        pen.fill(rrect(cx + r * 0.1, cy - r * 0.36, r * 0.2, r * 0.72, 3), '#16171c', a)
    elif icon == 'dot':
        pen.fill(oval(cx, cy, r * 0.22), '#ffffff', a * 0.8)


def _hand(pen, w, h, skin, a, front):
    """Simple flat hand holding the phone from below (drawn in phone-local coords, phone spans -w/2..w/2, -h/2..h/2)."""
    sh = mix(skin, '#6b5148', 0.35)
    if not front:
        palm = smooth([(-w * 0.62, h * 0.18), (-w * 0.5, h * 0.62), (-w * 0.1, h * 0.86), (w * 0.38, h * 0.78), (w * 0.6, h * 0.42),
                       (w * 0.66, h * 0.14), (w * 0.5, h * 0.05), (w * 0.2, h * 0.3), (-w * 0.3, h * 0.25)], True, 0.8)
        wrist = poly([(-w * 0.32, h * 0.7), (w * 0.3, h * 0.72), (w * 0.42, h * 1.2), (-w * 0.4, h * 1.2)])
        body = union(palm, wrist)
        pen.fill(body, skin, a); pen.shade(body, moved_path(body, w * 0.12, 0), sh, a * 0.5); pen.line(body, 7, LINE, a)
        return
    # fingers wrapping over the right edge and the thumb over the left edge
    for k in range(3):
        fy = h * (0.05 + k * 0.12)
        f = rrect(w * 0.42, fy, w * 0.2, h * 0.095, h * 0.045)
        pen.fill(f, skin, a); pen.line(f, 6, LINE, a)
    th = smooth([(-w * 0.62, h * 0.32), (-w * 0.44, h * 0.12), (-w * 0.36, h * 0.16), (-w * 0.42, h * 0.38)], True, 0.8)
    pen.fill(th, skin, a); pen.line(th, 6, LINE, a)


def moved_path(p, dx, dy):
    q = skia.Path(p); q.offset(dx, dy); return q


def phone(cv, state, t, name='MUM', x=960, y=560, scale=1.0, timer=None, hand=True, skin='#c0aa9e', alpha=255, number=None,
          progress=None, label=None):
    """Phone held up to the camera. t = seconds since this state began (drives pulses, dots, vibration, timers)."""
    pen = Pen(cv); a = alpha
    W, H = 300.0, 600.0
    vib = 0.0
    if state == 'incoming':
        on = (t % 1.4) < 0.8
        vib = math.sin(t * 2 * math.pi * 26) * 3.0 * on
    cv.save(); cv.translate(x + vib, y); cv.scale(scale, scale)
    if hand: _hand(pen, W, H, skin, a, False)
    body = rrect(-W / 2, -H / 2, W, H, 46)
    pen.radial(None, 0, 24, W * 0.95, [(0, '#000000', 170 * a / 255), (0.6, '#000000', 90 * a / 255), (1, '#000000', 0)],
               sy=H * 0.62 / (W * 0.95), clip=False)
    pen.fill(body, '#15161b', a)
    pen.line(body, 6, LINE, a)
    scr = rrect(-W / 2 + 12, -H / 2 + 12, W - 24, H - 24, 36)
    top, bot = {'busy': ('#2a0f14', '#0d0a0e'), 'emergency': ('#0f1830', '#090c16'), 'voicemail': ('#14161f', '#0b0c12'),
                'incoming': ('#162036', '#0a0e19')}.get(state, ('#121a2e', '#0a0d16'))
    pen.linear(scr, 0, -H / 2, 0, H / 2, [top, bot], a / 255)
    pen.fill(rrect(-38, -H / 2 + 24, 76, 20, 10), '#050506', a)                       # camera pill
    cvx = cv
    def T(s, yy, size, c='#ffffff', w=800, sp=0.02, aa=1.0): text(cvx, s, 0, yy, w, size, c, a * aa, sp, 'center', 0.0)
    clock = timer if timer is not None else t
    mmss = '%02d:%02d' % (int(clock) // 60, int(clock) % 60)
    if state in ('calling', 'busy', 'incoming', 'connected'):
        T({'calling': 'CALLING', 'busy': 'CALL FAILED', 'incoming': 'INCOMING CALL', 'connected': 'CONNECTED'}[state], -H / 2 + 92, 13,
          '#9aa3b8', 700, 0.22)
        T(name, -H / 2 + 146, 40)
        if number: T(number, -H / 2 + 178, 15, '#9aa3b8', 600, 0.06)
        av = (0, -40)
        if state in ('calling', 'incoming'):
            for k in range(3):
                ph = (t * 0.8 + k / 3.0) % 1.0
                pen.line(oval(av[0], av[1], 62 + ph * 70), 2.2, '#8fb0ff' if state == 'calling' else '#7fe0a0', a * (1 - ph) * 0.6)
        pen.fill(oval(av[0], av[1], 62), '#2a3350', a)
        T(name[:1].upper(), av[1] + 18, 52, '#d6dcf0', 800)
        if state == 'calling':
            dots = '.' * (1 + int(t * 2.5) % 3)
            T('calling' + dots, 92, 19, '#c5cbe0', 600, 0.02)
        elif state == 'busy':
            on = (t % 0.5) < 0.25
            T('USER BUSY', 92, 20, RED, 800, 0.12, 0.45 + 0.55 * on)
            for k in range(3):
                pen.fill(rrect(-30 + k * 22, 116, 14, 6, 3), RED, a * (0.3 + 0.7 * on))
        elif state == 'connected':
            T(mmss, 92, 22, '#c5cbe0', 600, 0.06)
            waveform(cv, -100, 140, 200, 46, t, '#6f95ff', 5, 1.0, True, a, 3.0, 2.4)
        if state == 'incoming':
            wig = math.sin(t * 9) * 4 * (t % 1.4 < 0.8)
            _button(pen, -72, H / 2 - 92, 34, '#e0343b', a, 'end')
            _button(pen, 72, H / 2 - 92 + wig, 34, '#2fbf5b', a, 'accept')
        else:
            _button(pen, 0, H / 2 - 92, 36, '#e0343b', a, 'end')
    elif state == 'emergency':
        T('EMERGENCY CALL', -H / 2 + 104, 15, '#b8c0d6', 700, 0.12)
        T('911', -H / 2 + 196, 84, '#ffffff', 800, 0.0)
        T(mmss, -H / 2 + 236, 19, '#c5cbe0', 600, 0.08)
        waveform(cv, -105, 30, 210, 62, t, '#6f95ff', 9, 1.0, True, a, 3.2, 2.6)
        for k in range(3): pen.fill(oval(-56 + k * 56, 132, 20), '#2a3350', a)
        _button(pen, 0, H / 2 - 96, 36, '#e0343b', a, 'end')
    elif state == 'voicemail':
        T('VOICEMAIL', -H / 2 + 100, 13, '#9aa3b8', 700, 0.24)
        T(name, -H / 2 + 148, 34)
        dur = 9.0
        pos = clamp(t / dur) if progress is None else progress
        T('0:%02d' % int(pos * dur), -H / 2 + 184, 20, RED, 800, 0.04)
        waveform(cv, -112, -6, 224, 96, 0.0, '#e0444c', 13, pos, False, a, 3.0, 2.2, dim='#5a5e6e')
        pen.seg((-112, 90), (112, 90), 4, '#3a3e4c', a)
        pen.seg((-112, 90), (-112 + 224 * pos, 90), 4, '#f2f2f2', a)
        pen.fill(oval(-112 + 224 * pos, 90, 8), '#ffffff', a)
        _button(pen, 0, H / 2 - 100, 36, '#f2f2f2', a, 'pause')
    if label: T(label, H / 2 - 30, 12, '#7f8aa6', 700, 0.2)
    pen.radial(scr, -W * 0.3, -H * 0.45, H * 0.9, [(0, '#ffffff', 16), (1, '#ffffff', 0)], a / 255)   # glass sheen
    if hand: _hand(pen, W, H, skin, a, True)
    cv.restore()


# ------------------------------------------------------------------ doorbell + bodycam HUDs
def _clock_str(clock, t, ampm=True):
    h, m, s = clock
    tot = int(h * 3600 + m * 60 + s + t)
    h, m, s = (tot // 3600) % 24, (tot // 60) % 60, tot % 60
    if not ampm: return '%02d:%02d:%02d' % (h, m, s)
    return '%d:%02d:%02d %s' % ((h % 12) or 12, m, s, 'AM' if h < 12 else 'PM')


def _signal(pen, x, y, bars, a):
    for k in range(4):
        hh = 7 + k * 5
        pen.fill(rrect(x + k * 8, y - hh, 5, hh, 1.5), '#ffffff', a * (0.95 if k < bars else 0.3))


def _battery(pen, x, y, lvl, a):
    pen.line(rrect(x, y - 14, 34, 16, 4), 2.2, '#ffffff', a)
    pen.fill(rrect(x + 35.5, y - 9.5, 3, 7, 1.5), '#ffffff', a)
    c = '#ffffff' if lvl > 0.2 else RED
    pen.fill(rrect(x + 3, y - 11, 28 * clamp(lvl), 10, 2), c, a)


def doorbell_hud(cv, t, name='FRONT DOOR', clock=(0, 36, 7), date='OCT 14', motion=None, signal=3, battery=0.78, ir=False,
                 talk=False, alpha=255, live=True):
    """Generic doorbell-camera app overlay (no brand). motion: (x, y, w, h) design box of the moving subject, or None."""
    pen = Pen(cv); a = alpha
    pen.linear(rect(0, 0, DW, 150), 0, 0, 0, 150, [(0, '#000000', 120), (1, '#000000', 0)], a / 255)
    pen.linear(rect(0, DH - 120, DW, 120), 0, DH - 120, 0, DH, [(0, '#000000', 0), (1, '#000000', 110)], a / 255)
    # LIVE pill + camera name
    if live:
        pill = rrect(46, 38, 96, 36, 18)
        pen.fill(pill, '#d3262d', a * 0.95)
        pulse = 0.55 + 0.45 * math.cos(t * 2 * math.pi)
        pen.fill(oval(66, 56, 6.5), '#ffffff', a * pulse)
        text(cv, 'LIVE', 80, 63, 800, 19, '#ffffff', a, 0.1, 'left')
    text(cv, name.upper(), 160 if live else 46, 63, 700, 21, '#ffffff', a * 0.95, 0.14, 'left', 0.8)
    # timestamp
    text(cv, date.upper() + '   ' + _clock_str(clock, t), DW - 46, 63, 700, 21, '#ffffff', a * 0.95, 0.1, 'right', 0.8)
    # bottom status
    _signal(pen, 48, DH - 44, signal, a * 0.9)
    text(cv, 'HD', 92, DH - 45, 800, 15, '#ffffff', a * 0.85, 0.08, 'left')
    if ir:
        b = rrect(136, DH - 64, 132, 26, 5); pen.line(b, 2, '#ffffff', a * 0.8)
        text(cv, 'NIGHT VISION', 202, DH - 45, 700, 13, '#ffffff', a * 0.9, 0.12, 'center')
    _battery(pen, DW - 100, DH - 40, battery, a * 0.9)
    text(cv, '%d%%' % int(battery * 100), DW - 112, DH - 44, 700, 16, '#ffffff', a * 0.9, 0.04, 'right')
    if talk:
        pen.fill(oval(DW / 2, DH - 70, 30), '#ffffff', a * 0.18); pen.line(oval(DW / 2, DH - 70, 30), 2, '#ffffff', a * 0.7)
        pen.fill(rrect(DW / 2 - 6, DH - 86, 12, 22, 6), '#ffffff', a)
        waveform(cv, DW / 2 + 44, DH - 70, 120, 26, t, '#ffffff', 3, 1.0, True, a * 0.9, 3, 3)
    if motion:
        mx, my, mw, mh = motion
        blink = 0.6 + 0.4 * (math.sin(t * 2 * math.pi * 1.5) > 0)
        L = min(mw, mh) * 0.18; c = '#ffd23a'
        for (cx, cy, sx, sy) in ((mx, my, 1, 1), (mx + mw, my, -1, 1), (mx, my + mh, 1, -1), (mx + mw, my + mh, -1, -1)):
            pen.line(poly([(cx + sx * L, cy), (cx, cy), (cx, cy + sy * L)], False), 4, c, a * 0.95, 'butt')
        b = rrect(mx, my - 40, 118, 28, 5); pen.fill(b, c, a * 0.9 * blink)
        text(cv, 'MOTION', mx + 59, my - 20, 800, 15, '#16171c', a * blink, 0.14, 'center')


def bodycam_hud(cv, t, unit='UNIT 24-07', badge='4471', clock=(0, 36, 7), date='2026-10-14', rec=True, alpha=255):
    """Generic body-worn camera burn-in (no brand): REC, timestamp, unit and badge."""
    pen = Pen(cv); a = alpha
    def T(s, x, y, size=24, al='left', aa=1.0):
        text(cv, s, x, y, 700, size, '#ffffff', a * aa, 0.06, al, 0.0, glow=('#000000', 230, 3))
    T('%s  %s  -0500' % (date, _clock_str(clock, t, False)), DW - 52, 70, 24, 'right')
    T('BODY CAM 2   %s   #%s' % (unit, badge), DW - 52, 104, 20, 'right', 0.9)
    if rec:
        on = (t % 1.0) < 0.6
        pen.fill(oval(66, 62, 10), RED, a * on)
        T('REC', 86, 70, 24)
    for (x0, y0, sx, sy) in ((40, 30, 1, 1), (DW - 40, 30, -1, 1), (40, DH - 30, 1, -1), (DW - 40, DH - 30, -1, -1)):
        pen.line(poly([(x0 + sx * 60, y0), (x0, y0), (x0, y0 + sy * 60)], False), 3, '#ffffff', a * 0.55, 'butt')
