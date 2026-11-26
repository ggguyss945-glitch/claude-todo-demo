"""sets_obsession.py: the sets of "If a Girl Is OBSESSED With Being Your Only Friend... DON'T WRITE YOUR NAME" (Night Policy).

Run inside sets.py's namespace at import, after sets_buttons.py (it reuses the set engine: BView cameras on a plan in
metres with pitch, per-face light maps, Room / Piece / build_view, BuBox rooms, Door, bu_stairs, the streetlight, the
post VHS look). Every new name starts with om_ / OM_ / _om.  import sets as ST;  sp = ST.om_front('down', track='step').
OM_API lists every builder's views, OM_INSERTS every insert. SETS.md has the short guide.

ADAM'S HOUSE (one plan, metres: x east, y north, Y up; the street to the south). A semi with a two-storey WING projecting
  to the front on the west (x -3.4 .. 0, front y -2.4): the living room below, ADAM'S ROOM above (floor OM_UP 2.7), whose
  window is in the wing's EAST wall (x 0, y -1.85 .. -0.75) and looks DOWN onto the path and the GREEN front door.
  The main block (x 0 .. 4.6, front wall y 0): the front door (x 0.35 .. 1.25) with its letterbox (Y 1.0), the hall
  (x 0 .. 1.9; the stairs on its east side rise north from y 0.9 to the landing at y 4.15; the passage x 0 .. 1.0 runs
  straight to the kitchen), the kitchen across the back (y 4.6 .. 8.2: the table, Mom's chair at its north end with the
  dark window behind it, the back door and the bucket). Upstairs: the corridor over the passage to Adam's door (x 0,
  y 0.1 .. 0.9), the landing at the top of the stairs under the bare bulb. Outside: the doorstep (Y 0) with the mat,
  one stone step, the path (OM_G) to the gate, the pavement, the streetlight by the gate (OM_LAMP), the road.
DANNY'S HOUSE: the same estate house type, BLUE door, number 9; Danny's mom's window is upstairs in the main block.
THE SCHOOL (own plan): the corridor (lockers on the east wall, Mrs. Rahman's open door on the west), the lunch hall at
  its north end, her office behind her door; the PLAYGROUND (own plan): the school's back wall (the caretaker's
  floodlight over the door), the swings, the bright repainted hopscotch running south to the faded red KEEPING SQUARE
  by the back fence, the gate.
THE TAPE: the same playground one summer five years before, seen by Mom's camcorder (om_tape, om_tape_content,
  om_tape_stamp; post['vhs'] carries the look, warp 0..1 for the rule 4 return, rewind for the rule 7 replay).
Staging data as every film: sp.anchors[name] -> Spot (.x .y design px, .depth, .ppm, .X .Yp .Y plan, .turn, .seat_y).
LOOK RULES: red is ONLY the Keeping Square's faded red (OM_RED, = characters' KEEPING_RED), her ribbons and the one
sunset. Door shots look DOWN from an upstairs window with ONLY ME the biggest shape. Night: blue-black, warm window
light; light the subject (streetlight, porch light, phone glow, window light), not the whole frame.
"""
import math
import numpy as np
import skia

# ====================================================================================================== plan + palette
OM_UP, OM_CEIL = 2.7, 2.4
OM_G = -0.32                              # the front garden and the path
OM_STEP = -0.16                           # the stone step's top (the doorstep is at 0)
OM_PAVE, OM_ROAD = -0.3, -0.45
OM_WING = (-3.4, 0.0, -2.4, 4.6)
OM_MAIN = (0.0, 4.6, 0.0, 8.2)
OM_ROOM = (-3.4, 0.0, -2.4, 1.0)          # Adam's room (upstairs in the wing)
OM_SWIN = (-1.85, -0.75, 0.85, 2.05)      # his window on x 0 (y0, y1, sill, top above OM_UP)
OM_ADOOR = (0.1, 0.9, 2.0)                # his door on x 0 (y0, y1, h), to the corridor
OM_HALL = (0.0, 1.9, 0.0, 4.6)
OM_FDOOR = (0.35, 1.25, 2.05)             # the front door on y 0 (x0 hinge, x1 latch, h)
OM_SLOT = (0.8, 1.0)                      # the letterbox (x, Y) on the door
OM_ST = (1.0, 1.9, 0.9, 13, 0.25)         # stairs: x0, x1, first riser y, risers, run
OM_RISE = OM_UP / OM_ST[3]
OM_ST_TOP = OM_ST[2] + OM_ST[3] * OM_ST[4]  # 4.15: the landing
OM_KIT = (0.0, 4.6, 4.6, 8.2)
OM_KDOOR = (0.1, 0.95)                    # the passage into the kitchen on y 4.6
OM_KWIN = (1.75, 2.95, 0.95, 2.05)        # the dark window behind Mom's chair (back wall y 8.2)
OM_BDOOR = (5.0, 5.85)                    # the back door on x 4.6 (y0, y1)
OM_TABLE = Box(2.35, 6.45, 0.9, 1.5, 0.0, 0.76, 0)
OM_MOMCHAIR = (2.35, 7.55)                # Mom's chair (faces south, the hall)
OM_BULB = (0.95, OM_UP + 2.1, 4.65)       # the bare landing bulb
OM_LAMP = (2.05, -6.25)                   # the streetlight by the gate (arm over the pavement)
OM_GATE = (0.45, 1.45)                    # the gate gap in the garden wall (y -6.0)
OM_PATH = (0.5, 1.4)                      # the path (x0, x1) from the step to the gate
OM_PLIGHT = (1.62, 2.05, -0.06)           # the porch light (x, Y, y) on the wall right of the door
# the chalk tracker (bible table): where ONLY ME is each night (x, y, Y, letter height m, empty line under)
OM_TRACK = {'street': (1.15, -7.05, OM_PAVE, 0.5, False), 'half': (0.95, -3.4, OM_G, 0.36, False),
            'foot': (0.95, -1.42, OM_G, 0.26, False), 'step': (0.95, -0.82, OM_STEP, 0.2, True),
            'door': (0.85, -0.2, 0.0, 0.17, False), 'mat': (0.8, -0.23, 0.02, 0.12, False)}
OM_RED = '#b0584f'                        # KEEPING_RED: the square, her ribbons, the one sunset. Nothing else is red.
OM_CHALK = '#f2f0e9'
OM_SODIUM = '#ffb468'
OM_WARM = '#ffcf94'
OM_PURPLE = '#5e3a96'                     # Danny's mom's ink
OM_BLUE_PEN = '#2346b4'                   # Danny's chewed blue pen
OM_DOORS = {'adam': '#2e6a48', 'danny': '#2c5c9e'}
OM_PAL = dict(render='#cfc6b4', brick='#a89880', brick_ink='#6e6252', trim='#ecebe4', roof='#3a3c44', wing='#c8bea8',
              hall_paper='#d9cfb8', hall_ink='#b8aa8c', room_paper='#9fb2c4', room_ink='#7d92a8', kit_paper='#dfe2cc', tile='#d8d4c6')

_GR.setdefault('om_night', dict(exposure=0.16, contrast=1.08, pivot=0.24, gamma=1.06, sat=0.98, wb=(0.94, 1.0, 1.1), floor='#060912',
                                bloom=0.9, bloom_thr=222, vignette=0.42, grain=0.6, shoulder=0.45))
_GR.setdefault('om_ext', dict(exposure=0.12, contrast=1.1, pivot=0.24, gamma=1.05, sat=1.0, wb=(0.93, 1.0, 1.1), floor='#050812',
                              bloom=1.0, bloom_thr=220, vignette=0.46, grain=0.6, shoulder=0.45))
_GR.setdefault('om_warm', dict(exposure=0.05, contrast=1.04, pivot=0.25, gamma=1.04, sat=1.04, wb=(1.05, 1.0, 0.93), floor='#0e0a08',
                               bloom=0.85, bloom_thr=226, vignette=0.4, grain=0.45, shoulder=0.5))
_GR.setdefault('om_day', dict(exposure=0.04, contrast=1.04, pivot=0.26, gamma=1.02, sat=1.06, wb=(1.02, 1.0, 0.97), floor='#12100e',
                              bloom=0.75, bloom_thr=232, vignette=0.34, grain=0.35, shoulder=0.55))
_GR.setdefault('om_school', dict(exposure=0.05, contrast=1.02, pivot=0.26, gamma=1.03, sat=0.94, wb=(0.98, 1.01, 1.02), floor='#101214',
                                 bloom=0.7, bloom_thr=234, vignette=0.36, grain=0.4, shoulder=0.55))
_GR.setdefault('om_sunset', dict(exposure=0.06, contrast=1.08, pivot=0.25, gamma=1.0, sat=1.08, wb=(1.08, 0.97, 0.9), floor='#140808',
                                 bloom=1.0, bloom_thr=218, vignette=0.48, grain=0.5, shoulder=0.5))
_GR.setdefault('om_flash', dict(exposure=0.1, contrast=0.98, pivot=0.27, gamma=1.05, sat=1.12, wb=(1.08, 1.0, 0.86), floor='#1a120a',
                                bloom=0.9, bloom_thr=222, vignette=0.42, grain=0.6, soft=0.4, shoulder=0.55))
_GR.setdefault('om_dawn', dict(exposure=0.08, contrast=1.0, pivot=0.26, gamma=1.04, sat=0.82, wb=(0.95, 1.0, 1.06), floor='#0c0f14',
                               bloom=0.7, bloom_thr=230, vignette=0.42, grain=0.5, shoulder=0.55))
_GR.setdefault('om_tape', dict(exposure=0.1, contrast=0.92, pivot=0.3, gamma=1.06, sat=0.8, wb=(1.08, 1.0, 0.84), floor='#22160e',
                               bloom=0.9, bloom_thr=220, vignette=0.55, grain=0.0, soft=0.5, shoulder=0.55))
_GR.setdefault('om_ins', dict(contrast=1.04, pivot=0.25, gamma=1.04, sat=1.02, wb=(1.0, 1.0, 1.0), floor='#0a0a0c',
                              bloom=0.5, bloom_thr=236, vignette=0.42, grain=0.4, shoulder=0.5))
_GR.setdefault('om_ins_night', dict(contrast=1.06, pivot=0.25, gamma=1.04, sat=0.98, wb=(0.96, 1.0, 1.06), floor='#05070e',
                                    bloom=0.7, bloom_thr=230, vignette=0.5, grain=0.55, shoulder=0.5))
_GR.setdefault('om_screen', dict(contrast=1.0, pivot=0.25, gamma=1.0, sat=1.0, wb=(1.0, 1.0, 1.0), floor='#000000',
                                 bloom=0.35, bloom_thr=240, vignette=0.9, grain=0.2, shoulder=0.7))

OM_CAMS = []


def _ocam(name, S, h, eye, x, y, yaw, env=None, note='', room='', pitch=0.0):
    _cam(name, S, h, eye, x, y, yaw, env or _env(), note, room, pitch)
    if name not in OM_CAMS: OM_CAMS.append(name)


def _otod(o): return o.get('tod', 'night') or 'night'


def _olv(o, k, d=0.0): return _static(o.get(k, d), d)


def _oo(kw, extra=None):
    o = dict(tod='night', no_veil=True)
    if extra: o.update(extra)
    o.update(kw)
    return o


def _xpanes(x, y0, y1, Y0, Y1):
    return [[(x, Y0, y0), (x, Y0, y1), (x, Y1, y1), (x, Y1, y0)]]


# ====================================================================================================== CHALK (everyone's primitive)
# Adam's handwriting (Evie writes in it: she only has what he has): the same strokes as characters_evie._LETTERS (round
# letters, curly M's), traced in order in a unit box (x 0..1 right, y 0..1 down). Space = a gap; '\n' = a new line.
OM_LETTERS = {
    'O': [[(0.62, 0.06), (0.24, 0.12), (0.05, 0.5), (0.24, 0.92), (0.6, 0.95), (0.92, 0.6), (0.84, 0.16), (0.55, 0.04), (0.36, 0.13)]],
    'N': [[(0.02, 0.9), (0.1, 0.98), (0.1, 0.5), (0.12, 0.04), (0.5, 0.52), (0.86, 0.95), (0.88, 0.5), (0.9, 0.03)]],
    'L': [[(0.2, 0.02), (0.16, 0.5), (0.14, 0.94), (0.5, 0.95), (0.86, 0.88)]],
    'Y': [[(0.06, 0.04), (0.3, 0.32), (0.5, 0.5)], [(0.94, 0.04), (0.7, 0.3), (0.5, 0.5), (0.4, 0.76), (0.3, 0.98)]],
    'M': [[(-0.02, 0.86), (0.08, 0.98), (0.1, 0.6), (0.12, 0.2), (0.2, 0.05), (0.31, 0.1), (0.41, 0.46), (0.5, 0.62),
           (0.57, 0.4), (0.66, 0.08), (0.78, 0.05), (0.88, 0.28), (0.9, 0.82), (0.98, 0.98), (1.08, 0.86)]],
    'E': [[(0.88, 0.07), (0.22, 0.06), (0.15, 0.5), (0.13, 0.94), (0.88, 0.94)], [(0.15, 0.5), (0.7, 0.5)]],
    'A': [[(0.05, 0.98), (0.5, 0.02), (0.95, 0.98)], [(0.24, 0.62), (0.76, 0.62)]],
    'D': [[(0.14, 0.02), (0.13, 0.98)], [(0.14, 0.03), (0.62, 0.07), (0.92, 0.46), (0.66, 0.92), (0.13, 0.97)]],
}
_OM_GLYPH_W = {'M': 1.1, 'O': 0.95, 'N': 0.92, 'L': 0.8, 'Y': 0.9, 'E': 0.82, 'A': 0.95, 'D': 0.9}


def _om_cr(pts, n=14):
    """Catmull-Rom through pts -> (N, 2) array."""
    P = np.asarray(pts, float)
    if len(P) < 3: return np.vstack([P[0] + (P[-1] - P[0]) * k for k in np.linspace(0, 1, n)])
    Q = np.vstack([P[0], P, P[-1]])
    out = []
    for i in range(1, len(Q) - 2):
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        for s in np.linspace(0, 1, n, endpoint=False):
            s2, s3 = s * s, s * s * s
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s2 + (-p0 + 3 * p1 - 3 * p2 + p3) * s3))
    out.append(P[-1])
    return np.array(out)


def om_chalk_layout(text, gap=0.2, lead=1.45, align='center', seed=0):
    """text -> [(char, [stroke (N, 2) in letter-height units: x right, y down])], the block's (w, h). Each letter has a
    slight hand-made wobble (size, slant, baseline) seeded per letter, the same on every frame."""
    lines = text.upper().split('\n')
    widths = []
    for ln in lines:
        w = 0.0
        for ch in ln: w += (0.55 if ch == ' ' else _OM_GLYPH_W.get(ch, 0.9)) + gap
        widths.append(max(0.0, w - gap))
    W = max(widths) if widths else 0.0
    out = []
    rng = np.random.default_rng(seed + 11)
    for li, ln in enumerate(lines):
        x = (W - widths[li]) / 2 if align == 'center' else 0.0
        y0 = li * lead
        for ch in ln:
            if ch == ' ': x += 0.55 + gap; continue
            gw = _OM_GLYPH_W.get(ch, 0.9)
            if ch in OM_LETTERS:
                sc = 1.0 + rng.uniform(-0.06, 0.08); sl = rng.uniform(-0.07, 0.05); dy = rng.uniform(-0.05, 0.05)
                sts = []
                for st in OM_LETTERS[ch]:
                    p = _om_cr(st, 10)
                    xx = x + (p[:, 0] * gw) * sc + (1.0 - p[:, 1]) * sl
                    yy = y0 + dy + (p[:, 1] - 1.0) * sc + 1.0
                    sts.append(np.column_stack([xx, yy]))
                out.append((ch, sts))
            x += gw + gap
    return out, (W, (len(lines) - 1) * lead + 1.0)


def _om_chalk_paint(c_, a, w, dash=None, blur=0.0):
    p = skia.Paint(Color=col(c_, int(clamp(a, 0, 255))), AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=max(0.6, w),
                   StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)
    if dash: p.setPathEffect(skia.DashPathEffect.Make(list(dash), 0.0))
    if blur > 0: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def _om_chalk_draw(cv, strokes, ws, u=1.0, rub=0.0, wet=0.0, alpha=1.0, colr=OM_CHALK):
    """strokes: screen polylines (N, 2); ws: their widths (px). u = how much is written (stroke by stroke, 0..1);
    rub 0..1 = rubbed out with a palm (faded, smeared sideways, still legible at 0.8); wet 0..1 = washed with a bucket
    (1 = only a faint ghost on the wet ground)."""
    if alpha <= 0.004 or not strokes: return
    lens = [float(np.sum(np.hypot(*np.diff(s, axis=0).T))) if len(s) > 1 else 0.0 for s in strokes]
    tot = sum(lens) or 1.0
    done = clamp(u) * tot
    a = alpha * (1.0 - 0.62 * clamp(rub)) * (1.0 - 0.93 * clamp(wet))
    for s, ln, w in zip(strokes, lens, ws):
        if done <= 1e-6: break
        if done < ln:                                                     # the stroke being drawn now
            cum = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(s, axis=0).T))])
            k = int(np.searchsorted(cum, done))
            f = (done - cum[k - 1]) / max(1e-6, cum[k] - cum[k - 1])
            s = np.vstack([s[:k], s[k - 1] + (s[k] - s[k - 1]) * f])
        done -= ln
        path = poly([tuple(q) for q in s], False)
        if rub > 0.01:                                                    # the palm's smear: a wide soft dust band
            for dx in (-0.6, 0.6):
                pm = poly([(q[0] + dx * w * 2.2 * rub, q[1] + 0.4 * w * rub) for q in s], False)
                cv.drawPath(pm, _om_chalk_paint(colr, 60 * alpha * rub, w * (1.6 + 2.2 * rub), blur=w * 1.2))
        cv.drawPath(path, _om_chalk_paint(colr, 60 * a, w * 1.9, blur=w * 0.35))
        d = max(w * 0.9, 1.0)
        cv.drawPath(path, _om_chalk_paint(colr, 215 * a, w, dash=(d * 3.1, d * 0.55, d * 1.7, d * 0.4)))
        cv.drawPath(path, _om_chalk_paint(colr, 150 * a, w * 0.45, dash=(d * 2.3, d * 0.9)))


def om_chalk_flat(pen, text, x, y, h, u=1.0, rub=0.0, wet=0.0, angle=0.0, squash=1.0, width=0.11, alpha=1.0, colr=OM_CHALK, seed=0, gap=0.2):
    """Chalk words flat on the screen (inserts, the card, the tape): (x, y) = the block's centre, h = letter height px,
    angle (deg), squash (ground foreshortening, 1 = facing us). See _om_chalk_draw for u / rub / wet."""
    lay, (W, H) = om_chalk_layout(text, gap, seed=seed)
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    sts = []
    for _, ss in lay:
        for s in ss:
            X = (s[:, 0] - W / 2) * h; Y = (s[:, 1] - H / 2) * h * squash
            sts.append(np.column_stack([x + X * ca - Y * sa, y + X * sa + Y * ca]))
    _om_chalk_draw(pen.cv, sts, [width * h] * len(sts), u, rub, wet, alpha, colr)


def om_chalk_ground(pen, v, text, x, y, Y, h, u=1.0, rub=0.0, wet=0.0, reader=None, width=0.1, alpha=1.0, lit_k=True, seed=0, gap=0.2):
    """Chalk words on a level surface of a plan (pavement, path, step, doormat, hall floor, the square): centre (x, y) at
    height Y, letter height h (m). The words read upright for reader = plan point (x, y) of whoever they are written for
    (default: this camera: Adam at his window, Danny at his). lit_k: chalk takes the light there (never below 0.55, so
    ONLY ME always reads). u / rub / wet: _om_chalk_draw."""
    rx_, ry_ = reader if reader is not None else (v.hx, v.hy)
    ux, uy = x - rx_, y - ry_
    n = math.hypot(ux, uy) or 1.0
    ux, uy = ux / n, uy / n                                                 # 'up' on the page = away from the reader
    r = (uy, -ux)
    lay, (W, H) = om_chalk_layout(text, gap, seed=seed)
    sts, ws = [], []
    for _, ss in lay:
        for s in ss:
            a_ = (s[:, 0] - W / 2) * h; b_ = (s[:, 1] - H / 2) * h
            X = x + r[0] * a_ - ux * b_; Yy = y + r[1] * a_ - uy * b_
            if min(v.d(X[i], Yy[i]) for i in (0, len(X) - 1)) < v.near + 0.05: continue
            sts.append(np.array([v.p(X[i], Y, Yy[i]) for i in range(len(X))]))
            m = len(X) // 2
            ws.append(width * h * v.s(X[m], Yy[m]))
    c_ = OM_CHALK
    if lit_k:
        m3 = light_at((x, Y + 0.01, y), (0.0, 1.0, 0.0))
        k = clamp(0.3 * (m3[0] + m3[1] + m3[2]), 0.55, 1.0)
        c_ = mix('#7c8aa8', OM_CHALK, k)
    _om_chalk_draw(pen.cv, sts, ws, u, rub, wet, alpha, c_)


def om_chalk_events(text, t0, dur, kind='chalk_scrape'):
    """Sound events for chalk written over [t0, t0 + dur]: one per stroke, at its start, with its length (s)."""
    lay, _ = om_chalk_layout(text)
    lens = [float(np.sum(np.hypot(*np.diff(s, axis=0).T))) for _, ss in lay for s in ss]
    tot = sum(lens) or 1.0
    ev, t = [], t0
    for ln in lens:
        d = dur * ln / tot
        ev.append(dict(t=round(t, 3), kind=kind, dur=round(d, 3)))
        t += d
    return ev


def om_line_ground(pen, v, x, y, Y, w, reader=None, alpha=1.0, width=0.016):
    """One empty chalk line on the ground (the line under ONLY ME on the step, 'waiting for a name')."""
    rx_, ry_ = reader if reader is not None else (v.hx, v.hy)
    ux, uy = x - rx_, y - ry_; n = math.hypot(ux, uy) or 1.0; ux, uy = ux / n, uy / n
    r = (uy, -ux)
    pts = [(x + r[0] * w * (k - 0.5) + ux * 0.006 * math.sin(k * 9.0), y + r[1] * w * (k - 0.5) + uy * 0.006 * math.sin(k * 9.0)) for k in np.linspace(0, 1, 9)]
    s = np.array([v.p(px, Y, py) for (px, py) in pts])
    _om_chalk_draw(pen.cv, [s], [width * v.s(x, y)], 1.0, 0.0, 0.0, alpha)


def _om_cast(name):
    """A free function of the cast (characters.py) when it is loaded (the chalk girl, the sneaker print), else None."""
    import sys
    CH = sys.modules.get('characters')
    if CH is None:
        try:
            import characters as CH
        except Exception:
            return None
    return getattr(CH, name, None)


# ====================================================================================================== small props
def om_bucket(pen, v, x, Y, y, s_=1.0, wet=True):
    """The scrubbing bucket: grey-blue plastic, a wire handle, a wet rag over the rim."""
    if v.d(x, y) < v.near + 0.1: return
    r0, r1, h = 0.15 * s_, 0.12 * s_, 0.3 * s_
    top = ellipse3(v, x, y, r0, r0, Y + h); bot = ellipse3(v, x, y, r1, r1, Y)
    b1, b2 = top.getBounds(), bot.getBounds()
    body = poly([(b1.left(), (b1.top() + b1.bottom()) / 2), (b1.right(), (b1.top() + b1.bottom()) / 2),
                 (b2.right(), (b2.top() + b2.bottom()) / 2), (b2.left(), (b2.top() + b2.bottom()) / 2)])
    body = union(body, bot)
    pen.fill(body, lit('#6f8496', (x, Y + h / 2, y), None)); pen.line(body, 1.0)
    pen.fill(top, lit('#2c3a46', (x, Y + h, y), (0, 1, 0))); pen.line(top, 1.0)
    if wet:
        pen.fill(ellipse3(v, x, y, r0 * 0.82, r0 * 0.82, Y + h * 0.8), lit('#5a6e7e', (x, Y + h, y), (0, 1, 0)), 220)
    a_, b_ = v.p(x - r0, Y + h, y), v.p(x + r0, Y + h, y)
    hp = v.p(x, Y + h + 0.16 * s_, y)
    pen.line(smooth([a_, hp, b_], False, 0.8), max(1.0, 0.008 * v.s(x, y)), '#2a2e34')
    rag = poly([v.p(x + r0 * 0.3, Y + h + 0.01, y - r0 * 0.2), v.p(x + r0 * 1.05, Y + h, y - r0 * 0.4), v.p(x + r0 * 1.1, Y + h * 0.55, y - r0 * 0.5),
                v.p(x + r0 * 0.6, Y + h * 0.7, y - r0 * 0.6)])
    pen.fill(rag, lit('#c8c2b0', (x, Y + h, y), None)); pen.line(rag, 0.8)


def om_doormat(pen, v, x0, x1, y0, y1, Y=0.0):
    """The coir doormat (brown bristle, a woven border)."""
    F = floor_face(x0, x1, y0, y1, Y + 0.012)
    def art(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'fabric', 0.9, 'overlay', 0.5); p_.texture(rect(0, 0, W, H), 'grunge', 0.5, 'overlay', 1.5)
        p_.line(rect(4, 4, W - 8, H - 8), 3.0, '#5a4026', 200)
    draw_face(pen, v, F, art, '#8a6a42', ao=False, line=True, lw=0.8)


def om_print(pen, v, x, y, Y, toward=(0.0, 1.0), alpha=1.0, side=1):
    """One white chalk sneaker print on a level surface, its toe pointing along plan direction `toward` (the cast's
    draw_sneaker_print when it is loaded)."""
    if v.d(x, y) < v.near + 0.1: return
    px, py = v.p(x, Y, y)
    tip = v.p(x + toward[0] * 0.14, Y, y + toward[1] * 0.14)
    ang = math.degrees(math.atan2(tip[0] - px, -(tip[1] - py)))
    sq = clamp(abs(v.cam_h - Y) / max(0.3, math.hypot(v.d(x, y), v.cam_h - Y)), 0.2, 1.0)
    fn = _om_cast('draw_sneaker_print')
    ppc = v.s(x, y) / 100.0
    if fn is not None:
        fn(pen, px, py, ppc, ang, alpha, sq, side); return
    cv = pen.cv; cv.save(); cv.translate(px, py); cv.scale(1.0, sq); cv.rotate(ang); cv.scale(ppc, ppc)
    sole = smooth([(-3.2, 10.5), (3.0, 10.0), (3.8, 2.0), (4.2, -6.0), (2.4, -10.8), (-1.8, -11.0), (-4.0, -6.0), (-3.4, 2.0)], True, 0.8)
    cv.drawPath(sole, _om_chalk_paint(OM_CHALK, 170 * alpha, 0.6)); cv.restore()


def _om_chair_parts(x, y, fa, Y0=0.0, c='#c9b48e', seat=0.45, back=0.9, w=0.42, d=0.42):
    """A plain wooden kitchen / school chair as Parts (fa: the way the sitter faces, Box convention)."""
    B = Box(x, y, w, d, Y0, Y0 + seat, fa)
    P = [Part(sub(B, -w / 2, w / 2, -d / 2, d / 2, Y0 + seat - 0.04, Y0 + seat), {'all': c, 'top': _lighten(c, 0.08)})]
    for (u, n) in ((-w / 2 + 0.03, -d / 2 + 0.03), (w / 2 - 0.03, -d / 2 + 0.03), (-w / 2 + 0.03, d / 2 - 0.03), (w / 2 - 0.03, d / 2 - 0.03)):
        P.append(Part(sub(B, u - 0.02, u + 0.02, n - 0.02, n + 0.02, Y0, Y0 + seat - 0.04), {'all': _darken(c, 0.15)}))
    P.append(Part(sub(B, -w / 2, w / 2, -d / 2, -d / 2 + 0.035, Y0 + seat, Y0 + back), {'all': c}, tag='back'))
    return P, B


def _om_seat_piece(name, x, y, fa, Y0=0.0, c='#c9b48e', seat=0.45, back=0.9):
    parts, B = _om_chair_parts(x, y, fa, Y0, c, seat, back)
    return Piece(name, (x, Y0 + 0.4, y), lambda pen, v, ps=parts: draw_parts(pen, v, ps), occupant=[(x, y)], front=parts, block=B.footprint())


def _om_photo(p_, x, y, w, h, kind='boys'):
    """A small framed photo on a wall (cm frame): 'boys' (Adam and Danny at seven on the swings, the tape's summer)."""
    p_.fill(rect(x - w / 2 - 2, y - h / 2 - 2, w + 4, h + 4), '#e8e2d4'); p_.line(rect(x - w / 2 - 2, y - h / 2 - 2, w + 4, h + 4), 0.6)
    p_.fill(rect(x - w / 2, y - h / 2, w, h), '#9cc4e4'); p_.fill(rect(x - w / 2, y + h * 0.1, w, h * 0.4), '#7aa860')
    p_.line(poly([(x - w * 0.35, y - h * 0.3), (x - w * 0.35, y + h * 0.2)], False), 0.6, '#5a5a5a')
    p_.line(poly([(x + w * 0.35, y - h * 0.3), (x + w * 0.35, y + h * 0.2)], False), 0.6, '#5a5a5a')
    for (dx, c) in ((-0.17, '#3a6ac8'), (0.17, '#e8c040')):
        p_.fill(oval(x + dx * w, y - h * 0.02, w * 0.07), '#c89a7a'); p_.fill(rect(x + dx * w - w * 0.06, y + h * 0.04, w * 0.12, h * 0.18), c)


# ====================================================================================================== ADAM'S ROOM
def _om_room_cfg(o):
    U = OM_UP
    def lights(o):
        tod = _otod(o)
        amb = '#8a8478' if tod == 'day' else mix('#161c30', '#6a7aa8', 0.3)
        pan = _xpanes(0.0, OM_SWIN[0], OM_SWIN[1], U + OM_SWIN[2], U + OM_SWIN[3])
        if tod == 'day': win = Lamp(kind='win', c='#fff0d8', k=1.3, soft=10.0, panes=pan, d=_norm3((-1.0, -0.5, 0.2)))
        else: win = Lamp(kind='win', c=OM_SODIUM, k=1.0 * _olv(o, 'street', 1.0), soft=12.0, panes=pan, d=_norm3((-1.0, -0.55, 0.45)))
        var = [('lamp', [Lamp(-2.75, U + 1.05, -2.0, 3.0, OM_WARM, 1.3, (1.0, 0.6, 0.3), fall=1.4)], _kfn(o.get('lamp', 0.0), 901)),
               ('ceil', [Lamp(-1.7, U + 2.3, -0.7, 6.0, '#fff0d8', 1.15, (1.0, 0.5, 0.2), fall=1.3)], _kfn(o.get('ceil', 0.0), 902)),
               ('phone', [Lamp(*o.get('phone_at', (-2.85, U + 0.8, 0.25)), R=1.8, c='#cfe0ff', k=1.6, w=(0.8, 1.0, 0.8), fall=1.5)], _kfn(o.get('phone', 0.0), 903)),
               ('torch', [Lamp(*o.get('torch_at', (-1.4, U + 1.2, -0.6)), R=4.5, c='#fff4dc', k=1.8, fall=1.4)], _kfn(o.get('torch', 0.0), 904)),
               ('strip', [Lamp(-0.12, U + 0.06, 0.5, 1.5, OM_WARM, 1.6, (1.0, 1.0, 0.2), only=('floor',), sxy=(0.35, 2.2), fall=1.6)], _kfn(o.get('strip', 0.0), 905))]
        return amb, [win], var
    def back(p_, W, H):                                                    # y 1.0, from x -3.4: the pinboard, the photo
        p_.fill(rect(150, H - 175, 90, 60), '#b89468'); p_.line(rect(150, H - 175, 90, 60), 0.8)
        _om_photo(p_, 175, H - 148, 26, 20, 'boys')
        for (k, c) in enumerate(('#e8e0c0', '#a8c8e8', '#e8c8a0')): p_.fill(rect(207 + k * 9, H - 168 + (k % 2) * 14, 8, 11), c)
        _light_switch(p_, 300, H - 118, True)
    def front(p_, W, H):                                                   # y -2.4, from x 0: a football poster
        p_.fill(rect(70, H - 190, 46, 62), '#2a4a7a'); p_.fill(oval(93, H - 162, 12), '#f2f2f2'); p_.line(rect(70, H - 190, 46, 62), 0.6)
    wins = {'east': [(0.0, OM_SWIN[0], 0.0, OM_SWIN[1], OM_SWIN[2], OM_SWIN[3], (2, 1))]}
    holes = {'east': [(0.0, OM_ADOOR[0], 0.0, OM_ADOOR[1], 0.0, OM_ADOOR[2])]}
    runs = _rect_runs(OM_ROOM, holes, wins, {'back': back, 'front': front})
    rug = _bu_rug_art(OM_ROOM[0], OM_ROOM[3], -1.7, -0.6, 0.75, 0.55, ('#3a5a8a', '#d8c890', '#4a7a6a', '#efe8d8'))
    def pieces(o):
        P = []
        bed = Box(-2.95, 0.02, 0.92, 1.95, U, U + 0.5, 0)                   # head at the back wall (north), along the west wall
        parts = bu_bed_parts(bed, U, o.get('bed', 'made'), '#5a4a3a', ('#2e4a72', '#d8cfb4', '#5a7a92', '#b8ae96'), '#2e4a72')
        P.append(Piece('bed', (-2.95, U + 0.4, 0.02), lambda pen, v: draw_parts(pen, v, parts), block=bed.footprint()))
        dk = Box(-2.4, -2.1, 1.1, 0.55, U, U + 0.74, 180)
        lk = _olv(o, 'lamp', 0.0); dr = _olv(o, 'drawer', 0.0)
        def desk(pen, v):
            draw_parts(pen, v, _bt_tparts(dk, '#c8b090', apron=0.05))
            dw = sub(dk, -0.3, 0.3, 0.275, 0.285 + 0.42 * dr, U + 0.58, U + 0.7)      # the drawer, pulled toward the room
            draw_box(pen, v, dw, {'all': '#b89a78', 'front': dict(fill='#b89a78', art=lambda p_, W, H: p_.fill(oval(W / 2, H / 2, 2.2), '#5a4a3a'))}, lw=0.8,
                     skip=() if dr > 0.02 else ('top', 'left', 'right'))
            dr_table_lamp(pen, v, -2.8, -2.2, U + 0.74, lk, '#e8e0c8', '#4a6a9a', 0.38)
        P.append(Piece('desk', (dk.cx, U + 0.4, dk.cy), desk, block=dk.footprint()))
        P.append(_om_seat_piece('desk_chair', -2.4, -1.6, 0, U, '#4a6a9a', 0.44, 0.86))
        sh = Box(-0.5, -2.2, 0.8, 0.3, U, U + 1.1, 180)
        def shelf(pen, v):
            draw_box(pen, v, sh, {'all': '#d8d0c0'}, lw=0.8)
            for k, c in enumerate(('#3a5a8a', '#c8a040', '#5a8a5a', '#8a5a7a', '#d8d8d0')):
                draw_box(pen, v, sub(sh, -0.36 + k * 0.12, -0.27 + k * 0.12, -0.1, 0.12, U + 0.6, U + 0.88 - (k % 2) * 0.05), {'all': c}, lw=0.6)
        P.append(Piece('shelf', (sh.cx, U + 0.5, sh.cy), shelf, block=sh.footprint()))
        if not callable(o.get('door')):
            D = Door((0.0, OM_ADOOR[1]), OM_ADOOR[1] - OM_ADOOR[0], OM_ADOOR[2], (0.0, -1.0), -1, U, art_a=door_art('six', 'right', bolt=False),
                     art_b=door_art('six', 'left', bolt=False), col='#ece8dc')
            P.append(_door_piece('door', D, _olv(o, 'door', 0.0), U + 1.0))
        return P
    def glows(v, o):
        ks = _kfn(o.get('strip', 0.0), 905)
        sh = o.get('shadow')
        def g(pen, t):                                                     # the 2 a.m. strip of hall light under the door
            k = ks(t)
            if k <= 0.01 or v.d(-0.05, 0.5) < 0.3: return
            a_, b_ = v.p(-0.01, U + 0.012, OM_ADOOR[0] + 0.03), v.p(-0.01, U + 0.012, OM_ADOOR[1] - 0.03)
            pen.seg(a_, b_, max(1.5, 0.012 * v.s(0.0, 0.5)), '#ffe6b8', 240 * k)
            pen.glow((a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2, 0.35 * v.s(0.0, 0.5), OM_WARM, 90 * k)
            if sh is not None:                                             # Mom's two feet out there: gaps in the strip
                s_ = sh(t) if callable(sh) else sh
                for dy in (-0.07, 0.07):
                    yy = OM_ADOOR[0] + 0.1 + 0.6 * s_ + dy
                    pen.seg(v.p(-0.01, U + 0.013, yy - 0.04), v.p(-0.01, U + 0.013, yy + 0.04), max(2.0, 0.016 * v.s(0.0, 0.5)), '#0a0a10', 230 * k)
        return [('strip_glow', (-0.05, U, 0.5), g)]
    def spots(v, o):
        S = {}
        S['bed'] = _mk_spot(v, 'bed', -2.95, 0.1, U + 0.5, 'lie', 'Adam in bed (head at the north wall, pillow end)')
        S['pillow'] = _mk_spot(v, 'pillow', -2.95, 0.78, U + 0.62, 'point', 'his head on the pillow')
        S['bed_edge'] = _mk_spot(v, 'bed_edge', -2.45, -0.2, U, 'seat', 'sitting on the edge of the bed (facing the window, +x)', face=(1, 0), seat_Y=0.5)
        S['window'] = _mk_spot(v, 'window', -0.42, -1.3, U, 'stand', 'at his window, looking down at the path (facing +x)', face=(1, 0))
        S['window_glass'] = _mk_spot(v, 'window_glass', -0.04, -1.3, U + 1.45, 'point', 'the glass (the white chalk fingerprint on the INSIDE: rule 3)')
        S['desk'] = _mk_spot(v, 'desk', -2.4, -1.6, U, 'seat', 'at the desk (facing -y, the drawer)', face=(0, -1), seat_Y=0.44)
        S['drawer'] = _mk_spot(v, 'drawer', -2.4, -1.75, U + 0.66, 'point', 'the desk drawer (the bracelet; later chalk dust)')
        S['door_in'] = _mk_spot(v, 'door_in', -0.45, 0.5, U, 'stand', 'one step inside his door (facing -x)', face=(-1, 0))
        S['door_gap'] = _mk_spot(v, 'door_gap', 0.0, 0.5, U, 'point', 'the gap under the door (the 2 a.m. light strip)')
        S['room_mid'] = _mk_spot(v, 'room_mid', -1.6, -0.7, U, 'stand', 'the middle of the room (the torch swing)')
        S['phone_bed'] = _mk_spot(v, 'phone_bed', -2.75, 0.3, U + 0.56, 'surface', 'his phone on the quilt')
        return S
    return dict(name='room', R=OM_ROOM, Y0=U, H=OM_CEIL, floor=dict(base='#9a7a58', kind='boards', ink='#5a4028', seed=81, art=rug), runs=runs,
                walls=dict(paper=OM_PAL['room_paper'], ink=OM_PAL['room_ink'], kind='stripe', wains=0.0, seed=83, scale=1.0, pa=60),
                ceil=dict(c='#e8ecf0'), lights=lights, pieces=pieces, spots=spots, glows=glows)


def _om_dark_corr(o):
    """The upstairs corridor seen through Adam's open door (dim; the landing bulb far off)."""
    U = OM_UP
    return BuBox(dict(name='corridor', R=(0.0, 1.0, 0.0, OM_ST_TOP), Y0=U, H=OM_CEIL, floor=dict(base='#6a5038', kind='boards', ink='#3a2a1a', seed=5),
                      walls=dict(paper=OM_PAL['hall_paper']), ceil=dict(c='#d8d4cc'),
                      lights=lambda o: (mix('#141a2c', '#5a6a90', 0.25), [], [('landing', [Lamp(*OM_BULB, R=5.0, c=OM_WARM, k=1.2, fall=1.4)], _kfn(o.get('landing', 0.0), 921)),
                                                                                ('hall', [Lamp(0.5, U + 1.8, 0.8, 3.0, OM_WARM, 1.0, fall=1.5)], _kfn(o.get('strip', 0.0), 905))])), far=True)


# ====================================================================================================== HALL, STAIRS, LANDING
def _om_house_light(o, night='#151a2c'):
    tod = _otod(o)
    if tod == 'day': return '#8a8478'
    if tod == 'dawn': return '#5a6278'
    return mix(night, '#5a6a92', 0.3)


def _om_front_door(o):
    """The front door leaf (hinge x 0.35, opening inward): outside GREEN (or Danny's blue), inside cream, the brass
    letterbox at Y 1.0 (its inner flap: flap 0..1)."""
    c = OM_DOORS[o.get('house', 'adam')]
    fl = _olv(o, 'flap', 0.0)
    return Door((OM_FDOOR[0], 0.0), OM_FDOOR[1] - OM_FDOOR[0], OM_FDOOR[2], (1.0, 0.0), 1, 0.0,
                art_a=door_art('four', 'right', slot=True, flap=0.0, bolt=False, col=c),
                art_b=door_art('four', 'left', slot=True, flap=fl, bolt=True, col='#ece6d6'), col='#ece6d6')


def _om_hall_cfg(o):
    U = OM_UP; T = OM_UP + OM_CEIL
    x0s, x1s, ys, n, run = OM_ST
    def lights(o):
        amb = _om_house_light(o)
        steady = []
        var = [('hall', [Lamp(0.5, OM_CEIL - 0.1, 1.7, 4.2, OM_WARM, 1.35, (1.0, 0.6, 0.3), fall=1.35)], _kfn(o.get('hall', 0.0), 931)),
               ('landing', [Lamp(*OM_BULB, R=5.5, c=OM_WARM, k=1.5, w=(1.0, 0.9, 0.5), fall=1.35)], _kfn(o.get('landing', 0.0), 932)),
               ('kitchen', [Lamp(0.55, 1.2, 4.75, 3.6, '#ffe2b0', 1.2, (0.6, 1.0, 0.3), fall=1.5)], _kfn(o.get('kitchen', 0.0), 933)),
               ('porch', [Lamp(0.8, 2.2, 0.15, 1.6, '#ffd8a0', 0.8, fall=1.6)], _kfn(o.get('porch', 0.0), 934)),
               ('street', [Lamp(0.8, 2.25, 0.2, 2.0, '#9ab0e0', 0.6, fall=1.6)], _kfn(o.get('street', 1.0), 935)),
               _phone_lamp(o, 936), _flash_lamp(o, 937)]
        return amb, steady, var
    def west(p_, W, H):                                                    # x 0, from y 0: coats on hooks, a mirror
        for k in range(3): p_.fill(oval(30 + k * 18, H - 172, 1.8), '#8a7a5a')
        p_.fill(smooth([(26, H - 170), (40, H - 170), (46, H - 92), (20, H - 94)], True, 0.6), '#4a5a7a')
        p_.fill(smooth([(62, H - 170), (74, H - 170), (80, H - 110), (56, H - 112)], True, 0.6), '#7a8a5a')
        p_.fill(rrect(300, H - 175, 40, 56, 3), '#c8c0a8'); p_.fill(rrect(304, H - 171, 32, 48, 2), '#8a9ab0')
        _light_switch(p_, 95, H - 118, True)
    def east(p_, W, H):                                                    # x 1.9 up the stairwell, from y 4.6: family photos rising
        for k in range(4):
            px = (4.6 - (1.4 + k * 0.7)) * 100; py = H - 160 - (k * 0.7 / run) * OM_RISE * 100 - 60
            p_.fill(rect(px - 15, py - 12, 30, 24), '#e8e2d4'); p_.fill(rect(px - 12, py - 9, 24, 18), ('#8aa8c8', '#c8a888', '#9ab88a', '#b8a8c8')[k])
    runs = [_run((1.9, 0.0), (x0s, 0.0), Y1=T),
            _run((x0s, 0.0), (0.0, 0.0), holes=[(OM_FDOOR[1], 0.0, OM_FDOOR[0], 0.0, 0.0, OM_FDOOR[2])], Y1=OM_CEIL),
            _run((0.0, 0.0), (0.0, 4.6), holes=[(0.0, 1.6, 0.0, 2.45, 0.0, 2.02)], Y1=OM_CEIL, art=west),
            _run((0.0, 4.6), (1.9, 4.6), holes=[(OM_KDOOR[0], 4.6, OM_KDOOR[1], 4.6, 0.0, 2.05)], Y1=OM_CEIL),
            _run((1.9, 4.6), (1.9, 0.0), Y1=T, art=east),
            # upstairs: the corridor's front wall (a small window above the front door), its west wall (Adam's door), the landing
            _run((x0s, 0.0), (0.0, 0.0), Y0=U, Y1=T, wins=[(0.75, 0.0, 0.25, 0.0, 0.9, 1.75, (1, 1))]),
            _run((0.0, 0.0), (0.0, 5.0), Y0=U, Y1=T, holes=[(0.0, OM_ADOOR[0], 0.0, OM_ADOOR[1], 0.0, OM_ADOOR[2])]),
            _run((0.0, 5.0), (1.9, 5.0), Y0=U, Y1=T, holes=[(0.3, 5.0, 1.1, 5.0, 0.0, 2.0)]),
            _run((1.9, 5.0), (1.9, 4.6), Y0=U, Y1=T),
            _run((x0s, 0.0), (x0s, OM_ST_TOP), Y0=OM_CEIL, Y1=U, paper='#ece8de', wains=0.0)]        # the corridor slab's edge
    def shell_pre(pen, v, o):
        ceil_rect(pen, v, x0s, 1.9, 0.0, OM_ST_TOP, T, c='#e4e0d6')
        if v.cam_h > U:
            ceil_rect(pen, v, 0.0, 1.9, OM_ST_TOP, 5.0, T, c='#e4e0d6'); ceil_rect(pen, v, 0.0, x0s, 0.0, OM_ST_TOP, T, c='#e4e0d6')
    def shell_x(pen, v, o):
        if v.cam_h > U:                                                    # the upstairs floors, seen from the landing / the stairs
            floor_rect(pen, v, 0.0, x0s, 0.0, OM_ST_TOP, U, '#7a5a3a', 'boards', '#3a2818', seed=7)
            floor_rect(pen, v, 0.0, 1.9, OM_ST_TOP, 5.0, U, '#7a5a3a', 'boards', '#3a2818', seed=8)
        if v.cam_h < OM_CEIL and v.d(0.5, 1.7) > 0.3:
            e = ellipse3(v, 0.5, 1.7, 0.14, 0.14, OM_CEIL - 0.03); pen.fill(e, lit('#efe8d8', (0.5, OM_CEIL - 0.1, 1.7), (0, -1, 0))); pen.line(e, 1.0)
    def hall_art(p_, W, H):                                                # a long runner down the passage
        u0, w0 = floor_uv(0.0, 4.6, 0.18, 4.45); u1, w1 = floor_uv(0.0, 4.6, 0.86, 0.95)
        rr = rect(u0, w0, u1 - u0, w1 - w0); p_.fill(rr, '#4a5a6a'); p_.texture(rr, 'fabric', 0.6, 'overlay', 1.0)
        p_.line(rect(u0 + 3, w0 + 3, u1 - u0 - 6, w1 - w0 - 6), 1.6, '#c8b890', 150)
    def pieces(o):
        P = []
        fa = o.get('fdoor', 0.0); fa = 0.0 if callable(fa) else fa
        D = _om_front_door(o)
        P.append(Piece('front_door', (0.8, 1.0, 0.03 + 0.4 * math.sin(math.radians(fa))), lambda pen, v, D=D, a=fa: D.draw(pen, v, a)))
        P.append(Piece('stairs', (x0s + 0.45, 1.0, (ys + OM_ST_TOP) / 2),
                       lambda pen, v: bu_stairs(pen, v, x0s, x1s, ys, n, run, OM_RISE, 0.0, '#7a5434', '#ece6d8', '#3e5468'),
                       block=_r4p((x0s, x1s, ys - 0.04, OM_ST_TOP))))
        def banister(pen, v):
            Yb = U + 0.92
            for k in range(14):
                yy = 0.35 + k * 0.28
                if v.d(x0s, yy) > 0.25: pen.seg(v.p(x0s + 0.02, U, yy), v.p(x0s + 0.02, Yb, yy), max(1.0, 0.03 * v.s(x0s, yy)), lit('#ece6d8', (x0s, U + 0.5, yy), (1, 0, 0)))
            a_, b_ = v.p(x0s + 0.02, Yb, 0.3), v.p(x0s + 0.02, Yb, OM_ST_TOP)
            if v.d(x0s, 0.3) > 0.25 and v.d(x0s, OM_ST_TOP) > 0.25:
                pen.seg(a_, b_, max(2.0, 0.06 * v.s(x0s, 2.0)) + 2, LINE); pen.seg(a_, b_, max(1.5, 0.06 * v.s(x0s, 2.0)), lit('#7a5434', (x0s, Yb, 2.0), (0, 1, 0)))
            # the handrail down the stairs (on the east wall)
            ks = [k for k in np.linspace(0, 1, 24) if v.d3(1.86, 1.1 + (U - 0.2) * k, ys + (OM_ST_TOP - ys) * k) > 0.6]
            if len(ks) > 1:
                pts = [v.p(1.86, 1.1 + (U - 0.2) * k, ys + (OM_ST_TOP - ys) * k) for k in ks]
                pen.line(poly(pts, False), max(1.5, 0.05 * v.s(1.86, ys + (OM_ST_TOP - ys) * ks[0])), lit('#7a5434', (1.86, 2.0, 2.5), (-1, 0, 0)))
        P.append(Piece('banister', (x0s, U + 0.5, 2.0), banister, vis=lambda v: v.cam_h > OM_CEIL or v.hx > x0s))
        if o.get('stub'):
            sx, sy = (1.45, ys - 0.12) if o['stub'] is True else o['stub']
            P.append(Piece('stub', (sx, 0.02, sy), lambda pen, v: _om_stub3(pen, v, sx, 0.01, sy)))
        return P
    def glows(v, o):
        kl = _kfn(o.get('landing', 0.0), 932); kh = _kfn(o.get('hall', 0.0), 931)
        def g(pen, t):
            k = kl(t)
            x, Y, y = OM_BULB
            if v.d(x, y) > 0.25:
                s = v.s(x, y); top = v.p(x, OM_UP + OM_CEIL, y); bp = v.p(x, Y, y)
                pen.seg(top, bp, max(1.0, 0.008 * s), '#1a1a1a')
                g_ = oval(bp[0], bp[1] + 0.05 * s, 0.035 * s, 0.045 * s)
                if k > 0.01:
                    pen.glow(bp[0], bp[1] + 0.05 * s, 1.1 * s, '#ffcf8a', 80 * k); pen.glow(bp[0], bp[1] + 0.05 * s, 0.22 * s, '#fff2d8', 220 * k)
                pen.fill(g_, mix('#a8a090', '#fffaf0', k)); pen.line(g_, 0.8)
            k2 = kh(t)
            if k2 > 0.01 and v.cam_h < OM_CEIL and v.d(0.5, 1.7) > 0.3:
                pen.fill(ellipse3(v, 0.5, 1.7, 0.12, 0.12, OM_CEIL - 0.035), '#fff6e4', 230 * k2)
        return [('bulb', (OM_BULB[0], OM_BULB[1], OM_BULB[2]), g)]
    def spots(v, o):
        S = {}
        S['door_in'] = _mk_spot(v, 'door_in', 0.8, 0.45, 0.0, 'stand', 'just inside the front door (facing it, -y)', face=(0, -1))
        S['mom_door'] = _mk_spot(v, 'mom_door', 0.45, 0.85, 0.0, 'stand', 'Mom beside Adam at the open door (facing out, -y)', face=(0, -1))
        S['adam_door'] = _mk_spot(v, 'adam_door', 1.05, 0.8, 0.0, 'stand', 'Adam at the open door (facing out, -y)', face=(0, -1))
        S['letterbox'] = _mk_spot(v, 'letterbox', OM_SLOT[0], 0.05, OM_SLOT[1], 'point', 'the letterbox slot, inside face (the fingers come in here)')
        S['door_base'] = _mk_spot(v, 'door_base', OM_SLOT[0], 0.06, 0.0, 'point', 'the floor under the letterbox')
        S['only_floor'] = _mk_spot(v, 'only_floor', 0.75, 0.55, 0.0, 'surface', 'the hall floor between the door and the stairs: O-N-L-Y')
        S['bottom_stair'] = _mk_spot(v, 'bottom_stair', 1.45, ys - 0.1, 0.0, 'surface', 'the floor at the bottom stair (the stub rolls here)')
        for k_ in (1, 3, 6, 9, 12):
            S['step%d' % k_] = _mk_spot(v, 'step%d' % k_, 1.45, ys + (k_ - 0.5) * run, k_ * OM_RISE, 'stand', 'on stair %d (facing down, -y)' % k_, face=(0, -1))
        S['halfway'] = S['step6']
        S['landing'] = _mk_spot(v, 'landing', 1.4, 4.5, U, 'stand', 'the landing at the top of the stairs (facing down, -y)', face=(0, -1))
        S['lina_landing'] = _mk_spot(v, 'lina_landing', 0.75, 4.6, U, 'stand', 'Lina under the bare bulb (facing the stairs, -y)', face=(0, -1))
        S['card_landing'] = _mk_spot(v, 'card_landing', 0.6, 4.4, U + 0.01, 'surface', 'the card thrown on the landing floor')
        S['passage'] = _mk_spot(v, 'passage', 0.5, 2.6, 0.0, 'stand', 'the passage to the kitchen (facing north)', face=(0, 1))
        S['kitchen_door'] = _mk_spot(v, 'kitchen_door', 0.52, 4.5, 0.0, 'stand', 'at the kitchen doorway (facing north)', face=(0, 1))
        return S
    floors = [(0.0, 1.9, 0.0, 4.6)]
    return dict(name='hall', R=OM_HALL, Y0=0.0, H=OM_CEIL, floors=floors, floor=dict(base='#8a6440', kind='boards', ink='#4a3018', seed=91, art=hall_art),
                runs=runs, walls=dict(paper=OM_PAL['hall_paper'], ink=OM_PAL['hall_ink'], kind='stripe', wains=0.9, wcol='#ece6d8', seed=93, pa=50),
                ceil=dict(c='#e4e0d6', rects=[(0.0, x0s, 0.0, OM_ST_TOP), (0.0, 1.9, OM_ST_TOP, 4.6)]), lights=lights, pieces=pieces, spots=spots, glows=glows,
                shell_x=shell_x, shell_pre=shell_pre)


def _om_stub3(pen, v, x, Y, y, ang=20.0):
    """The worn chalk stub lying on the floor / the bottom stair."""
    if v.d(x, y) < v.near + 0.1: return
    a_, b_ = v.p(x - 0.03 * math.cos(math.radians(ang)), Y + 0.006, y - 0.03 * math.sin(math.radians(ang))), v.p(x + 0.03 * math.cos(math.radians(ang)), Y + 0.006, y + 0.03 * math.sin(math.radians(ang)))
    w = max(2.0, 0.012 * v.s(x, y))
    pen.seg(a_, b_, w + 1.5, '#5a5a60'); pen.seg(a_, b_, w, OM_CHALK)
    pen.glow((a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2, 0.05 * v.s(x, y), '#ffffff', 50)


# ====================================================================================================== KITCHEN
def _om_kit_cfg(o):
    def lights(o):
        amb = _om_house_light(o, '#141a2a')
        var = [('kitchen', [Lamp(2.35, OM_CEIL - 0.25, 6.45, 4.8, '#ffe8c4', 1.4, (1.0, 0.65, 0.35), fall=1.3)], _kfn(o.get('kitchen', 0.0), 941)),
               ('hall', [Lamp(0.55, 1.6, 4.2, 2.6, OM_WARM, 0.9, fall=1.5)], _kfn(o.get('hall', 0.0), 931)),
               _phone_lamp(o, 942)]
        return amb, [], var
    def back(p_, W, H):                                                    # y 8.2 from x 0: a calendar, the cupboards' tiles
        p_.fill(rect(80, H - 180, 34, 44), '#f2efe6'); p_.fill(rect(80, H - 180, 34, 10), '#5a7a9a'); p_.line(rect(80, H - 180, 34, 44), 0.6)
        for i in range(12): p_.fill(rect(320 + (i % 6) * 22, H - 150 + (i // 6) * 22, 20, 20), '#e8ece4')
    def west(p_, W, H):                                                    # x 0 from y 4.6: Lina's crayon drawings on the wall
        for k, c in enumerate(('#e8c040', '#5aa0d8', '#7ac070')):
            p_.fill(rect(120 + k * 46, H - 168 + (k % 2) * 10, 36, 28), '#fbf8f0'); p_.line(rect(120 + k * 46, H - 168 + (k % 2) * 10, 36, 28), 0.5)
            p_.line(smooth([(126 + k * 46, H - 150), (138 + k * 46, H - 160), (150 + k * 46, H - 148)], False), 1.2, c)
    runs = [_run((4.6, 4.6), (0.0, 4.6), holes=[(OM_KDOOR[1], 4.6, OM_KDOOR[0], 4.6, 0.0, 2.05)]),
            _run((0.0, 4.6), (0.0, 8.2), art=west),
            _run((0.0, 8.2), (4.6, 8.2), wins=[(OM_KWIN[0], 8.2, OM_KWIN[1], 8.2, OM_KWIN[2], OM_KWIN[3], (2, 2))], art=back),
            _run((4.6, 8.2), (4.6, 4.6), holes=[(4.6, OM_BDOOR[1], 4.6, OM_BDOOR[0], 0.0, 2.02)])]
    def pieces(o):
        P = []
        tb = OM_TABLE
        def table(pen, v):
            draw_parts(pen, v, table_parts(tb, '#b89068', apron=0.06, cloth=None))
            if o.get('dinner'):
                for (px, py) in ((2.35, 5.85), (2.35, 7.05), (1.98, 6.45)):
                    pen.fill(ellipse3(v, px, py, 0.13, 0.13, 0.765), lit('#f4f2ec', (px, 0.77, py), (0, 1, 0))); pen.line(ellipse3(v, px, py, 0.13, 0.13, 0.765), 0.8)
                    pen.fill(ellipse3(v, px, py, 0.07, 0.07, 0.77), lit('#c8a050', (px, 0.78, py), (0, 1, 0)))
        P.append(Piece('table', (tb.cx, 0.5, tb.cy), table, block=tb.footprint()))
        P.append(_om_seat_piece('mom_chair', OM_MOMCHAIR[0], OM_MOMCHAIR[1], 0))
        P.append(_om_seat_piece('adam_chair', 2.35, 5.35, 180))
        P.append(_om_seat_piece('lina_chair', 1.5, 6.45, 90))
        cn = Box(3.85, 7.9, 1.5, 0.6, 0.0, 0.92, 0)
        def counter(pen, v):
            draw_box(pen, v, cn, {'all': '#e8e4d8', 'top': '#9a948a', 'front': dict(fill='#e8e4d8', art=lambda p_, W, H: [p_.line(rect(6 + k * W / 3, 10, W / 3 - 12, H - 16), 0.8, '#000000', 70) for k in range(3)])}, lw=0.9)
            draw_box(pen, v, sub(cn, -0.55, -0.05, -0.1, 0.22, 0.92, 0.94), {'all': '#c8ccd0'}, lw=0.6)          # the sink
            ke = Box(4.3, 7.9, 0.18, 0.16, 0.92, 1.12, 0); draw_box(pen, v, ke, {'all': '#e8e2cc'}, lw=0.7)    # a cream kettle
            ub = Box(3.85, 8.02, 1.5, 0.35, 1.45, 2.2, 0)
            draw_box(pen, v, ub, {'all': '#e8e4d8', 'front': dict(fill='#e8e4d8', art=lambda p_, W, H: [p_.line(rect(6 + k * W / 3, 6, W / 3 - 12, H - 12), 0.8, '#000000', 70) for k in range(3)])}, lw=0.9)
        P.append(Piece('counter', (3.85, 0.6, 7.9), counter, block=cn.footprint()))
        fr = Box(0.38, 7.85, 0.7, 0.64, 0.0, 1.8, 90)
        P.append(Piece('fridge', (0.38, 0.9, 7.85), lambda pen, v: draw_box(pen, v, fr, {'all': '#eef0ec', 'front': dict(fill='#eef0ec', art=lambda p_, W, H: (p_.line(poly([(4, H * 0.38), (W - 4, H * 0.38)], False), 1.0, '#000000', 90), p_.fill(rect(W - 12, H * 0.2, 4, 26), '#a8aaa8')))}, lw=0.9), block=fr.footprint()))
        if o.get('bucket', True): P.append(Piece('bucket', (4.3, 0.15, 6.1), lambda pen, v: om_bucket(pen, v, 4.3, 0.0, 6.1)))
        BD = Door((4.6, OM_BDOOR[1]), OM_BDOOR[1] - OM_BDOOR[0], 2.02, (0.0, -1.0), 1, 0.0, art_a=door_art('glass', 'left', bolt=True), art_b=door_art('glass', 'right', bolt=True), col='#e8e0d0')
        P.append(Piece('back_door', (4.58, 1.0, 5.4), lambda pen, v, D=BD: D.draw(pen, v, 0.0)))
        return P
    def shell_x(pen, v, o):
        if v.cam_h < OM_CEIL and v.d(2.35, 6.45) > 0.3:
            e = ellipse3(v, 2.35, 6.45, 0.22, 0.22, OM_CEIL - 0.03); pen.fill(e, lit('#efe8d8', (2.35, OM_CEIL - 0.1, 6.45), (0, -1, 0))); pen.line(e, 1.0)
    def glows(v, o):
        kk = _kfn(o.get('kitchen', 0.0), 941)
        def g(pen, t):
            k = kk(t)
            if k > 0.01 and v.cam_h < OM_CEIL and v.d(2.35, 6.45) > 0.3:
                pen.fill(ellipse3(v, 2.35, 6.45, 0.19, 0.19, OM_CEIL - 0.035), '#fff8ea', 235 * k)
        return [('kitchen_glow', (2.35, OM_CEIL, 6.45), g)]
    def spots(v, o):
        S = {}
        S['mom_chair'] = _mk_spot(v, 'mom_chair', OM_MOMCHAIR[0], OM_MOMCHAIR[1], 0.0, 'seat', "Mom's chair (facing the hall, -y; the dark window behind her)", face=(0, -1), seat_Y=0.45)
        S['adam_chair'] = _mk_spot(v, 'adam_chair', 2.35, 5.35, 0.0, 'seat', "Adam's chair (facing Mom, +y)", face=(0, 1), seat_Y=0.45)
        S['lina_chair'] = _mk_spot(v, 'lina_chair', 1.5, 6.45, 0.0, 'seat', "Lina's chair (facing +x)", face=(1, 0), seat_Y=0.45)
        S['window_out'] = _mk_spot(v, 'window_out', 2.35, 8.6, -0.3, 'stand', 'Evie outside the dark window (her lips moving), on the garden', face=(0, -1))
        S['doorway'] = _mk_spot(v, 'doorway', 0.52, 4.75, 0.0, 'stand', 'just inside the kitchen from the hall (facing +y)', face=(0, 1))
        S['by_chair'] = _mk_spot(v, 'by_chair', 1.9, 7.1, 0.0, 'surface', "the tiles in front of Mom's chair (where M... E... stops)")
        S['stand_mom'] = _mk_spot(v, 'stand_mom', 1.95, 7.5, 0.0, 'stand', 'Mom standing up from her chair (facing the doorway)', face=(-0.4, -1))
        S['bucket'] = _mk_spot(v, 'bucket', 4.3, 6.1, 0.0, 'surface', 'the bucket by the back door')
        S['table_top'] = _mk_spot(v, 'table_top', 2.35, 6.9, 0.76, 'surface', 'the table top (her fork; the phone)')
        return S
    return dict(name='kitchen', R=OM_KIT, Y0=0.0, H=OM_CEIL, floor=dict(base=OM_PAL['tile'], kind='checker', ink='#a8a49a', seed=95, scale=1.0),
                runs=runs, walls=dict(paper=OM_PAL['kit_paper'], ink='#c8ccb4', kind=None, wains=0.0, seed=97), ceil=dict(c='#eceae0'),
                lights=lights, pieces=pieces, spots=spots, glows=glows, shell_x=shell_x)


# ====================================================================================================== SKY, TREES
def _om_hy(v):
    """Screen y of the horizon (pitched cameras look down: the horizon rises)."""
    return v.h - v.S * math.tan(math.radians(getattr(v, 'pitch', 0.0) or 0.0))


def om_sky(pen, v, tod='night'):
    """The sky for camera v: night (blue-black, stars, a thin moon), dawn (cold, clean), day, sunset (THE one red glow:
    the square's faded red low in the west), summer (the tape's warm afternoon)."""
    hy = _om_hy(v)
    st = {'night': [(0, '#02040c'), (0.6, '#0a1430'), (1, '#22385e')], 'dawn': [(0, '#4e5c7c'), (0.65, '#9aa8bc'), (1, '#e2dcc8')],
          'day': [(0, '#4a86cc'), (0.7, '#8cb8e0'), (1, '#d8e6ee')], 'summer': [(0, '#5a9ad8'), (0.7, '#a8d0ec'), (1, '#f4ead0')],
          'warm': [(0, '#6aa0d4'), (0.7, '#c8d8d8'), (1, '#f6dca8')],
          'sunset': [(0, '#2e2440'), (0.42, '#6e3e52'), (0.7, OM_RED), (0.88, '#d8784e'), (1, '#f2b070')]}.get(tod, None)
    if st is None: st = [(0, '#02040c'), (1, '#22385e')]
    pen.linear(rect(-900, -900, 3800, 3200), 0, hy - 1.05 * v.S, 0, hy + 12, st)
    rng = np.random.default_rng(31)
    if tod == 'night':
        for i in range(170):
            az, el = math.radians(rng.uniform(-180, 180)), math.radians(rng.uniform(4, 70))
            P = (v.hx + 400 * math.sin(az) * math.cos(el), v.cam_h + 400 * math.sin(el), v.hy + 400 * math.cos(az) * math.cos(el))
            if v.d3(*P) < 1.0: continue
            x, y = v.p(*P)
            if -20 < x < 1940 and y < hy - 6: pen.fill(oval(x, y, rng.uniform(0.6, 1.7)), '#ffffff', int(rng.uniform(80, 230)))
    elif tod in ('day', 'summer', 'warm', 'sunset'):
        for i in range(6):
            az = math.radians(rng.uniform(-180, 180)); el = math.radians(rng.uniform(6, 22))
            P = (v.hx + 300 * math.sin(az) * math.cos(el), v.cam_h + 300 * math.sin(el), v.hy + 300 * math.cos(az) * math.cos(el))
            if v.d3(*P) < 1.0: continue
            x, y = v.p(*P)
            cc = ('#f6e8e0', '#fff4ee') if tod != 'sunset' else ('#e88a6a', '#f6c08a')
            _cloud(pen, x, y, rng.uniform(0.5, 0.9) * v.S, 0.05 * v.S, int(rng.integers(0, 999)), cc[0], cc[1], 150)


def om_lamp_glow(pen, v, hx, hy, G, k=1.0, h=6.2, c=OM_SODIUM, pool=3.2):
    """A streetlight's head glow at plan (hx, hy) (the head over the pavement) and its pool on the ground (true
    perspective: right for pitched cameras too)."""
    if k <= 0.01: return
    if v.d3(hx, G + h, hy) > v.near + 0.2:
        x, y = v.p(hx, G + h + 0.1, hy); s = v.s(hx, hy)
        pen.glow(x, y, 1.3 * s, c, 105 * k); pen.glow(x, y, 0.3 * s, '#fff6e0', 220 * k)
    if v.d(hx, hy) > v.near + 0.5:
        for (r, a) in ((pool, 26), (pool * 0.62, 30), (pool * 0.32, 34)):
            pen.fill(ellipse3(v, hx, hy, r, r, G + 0.01), c, a * k, blur=max(2.0, 0.18 * r * v.s(hx, hy)))


def _om_tree(pen, v, x, y, G, h, tod='night', seed=0):
    """A rounded garden / street tree standing on G (crown of leafy masses)."""
    if v.d(x, y) < 1.0: return
    bx, by = v.p(x, G, y); s = v.s(x, y)
    tp = v.p(x, G + 0.55 * h, y)
    night = tod == 'night'
    tr = poly([(bx - 0.14 * s, by), (bx + 0.14 * s, by), (tp[0] + 0.09 * s, tp[1]), (tp[0] - 0.09 * s, tp[1])])
    pen.fill(tr, '#14100e' if night else '#4a3a2e'); pen.line(tr, 1.0)
    rng = np.random.default_rng(300 + seed)
    c0, c1 = {'night': ('#0c1610', '#16241a'), 'sunset': ('#3a2a22', '#5a3a2a'), 'dawn': ('#2a3a30', '#3a4a3e')}.get(tod, ('#3a6a2e', '#5a8a3e'))
    for i in range(7):
        P = (x + rng.uniform(-0.32, 0.32) * h, G + (0.62 + rng.uniform(0.0, 0.34)) * h, y)
        cx, cy = v.p(*P)
        _bush(pen, cx, cy, rng.uniform(0.42, 0.65) * h * s, rng.uniform(0.32, 0.46) * h * s, seed * 10 + i, c0, c1)


# ====================================================================================================== THE HOUSES (outside)
# One estate semi-detached half in OUR plan coordinates (x -3.4 .. 4.6; front y 0; the wing to y -2.4); other houses are
# copies through _om_xf (mirror / across the road). Walls: (A, B, outward normal); features in plan coordinates.
_OM_WALLS = [((0.0, 0.0), (4.6, 0.0), (0, -1)), ((-3.4, -2.4), (0.0, -2.4), (0, -1)), ((0.0, -2.4), (0.0, 0.0), (1, 0)),
             ((-3.4, 4.6), (-3.4, -2.4), (-1, 0)), ((4.6, 0.0), (4.6, 8.2), (1, 0))]
_OM_EAVE, _OM_RIDGE = 5.3, 7.3
# windows: name -> (wall index, (x, y) a, (x, y) b, sill Y, top Y)
_OM_WINS = {'front': (0, (2.3, 0.0), (4.0, 0.0), 0.9, 2.1), 'up': (0, (2.3, 0.0), (3.9, 0.0), OM_UP + 0.85, OM_UP + 2.05),
            'stairwin': (0, (0.25, 0.0), (0.75, 0.0), OM_UP + 0.9, OM_UP + 1.75), 'living': (1, (-2.9, -2.4), (-0.5, -2.4), 0.8, 2.1),
            'adam': (2, (0.0, OM_SWIN[0]), (0.0, OM_SWIN[1]), OM_UP + OM_SWIN[2], OM_UP + OM_SWIN[3]),
            'side': (2, (0.0, -1.7), (0.0, -0.9), 0.9, 2.0)}


def _om_xf(kind):
    """Plan transform for a copy of the house: 'ours' | 'next' (the attached mirror half east) | 'west' (the next semi
    west) | 'across' / 'across2' (facing north over the road)."""
    return {'ours': lambda x, y: (x, y), 'next': lambda x, y: (9.2 - x, y), 'west': lambda x, y: (-9.4 - x, y),
            'west2': lambda x, y: (x - 16.4, y), 'across': lambda x, y: (x - 1.0, -22.0 - y), 'across2': lambda x, y: (6.4 - x, -22.0 - y),
            'across3': lambda x, y: (x - 17.4, -22.0 - y), 'across4': lambda x, y: (22.8 - x, -22.0 - y)}[kind]


def _om_seg(xf, a, b, n):
    """Transform a wall and order it so its outside is on the right of A -> B."""
    A, B = xf(*a), xf(*b)
    q0, q1 = xf(0.0, 0.0), xf(n[0], n[1])
    N = (q1[0] - q0[0], q1[1] - q0[1])
    fx, fy = B[0] - A[0], B[1] - A[1]
    if fy * N[0] - fx * N[1] < 0: A, B = B, A
    return A, B


def _om_house_draw(pen, v, o, kind='ours', who='adam', seed=0):
    """One half of an estate semi from outside: buff brick below, cream render above, white uPVC windows, the front door
    (GREEN for Adam, BLUE for Danny, cream / grey for the neighbours) with its letterbox, the porch light, the wing."""
    xf = _om_xf(kind)
    night = _otod(o) in ('night',)
    doorc = OM_DOORS.get(who, ('#d8d2c2', '#5a6470', '#8a7a62', '#e2dccc')[seed % 4])
    render = (OM_PAL['render'], '#c9cbc0', '#d4c8b0', '#bfc4c8')[seed % 4] if who not in ('adam', 'danny') else (OM_PAL['render'] if who == 'adam' else '#c4ccc8')
    brick = (OM_PAL['brick'], '#9c9484', '#a89c86', '#958d80')[seed % 4]
    for wi, (a, b, n) in enumerate(_OM_WALLS):
        if wi == 4: continue
        A, B = _om_seg(xf, a, b, n)
        F = wall_face(A, B, OM_G, _OM_EAVE)
        if not v.visible(F.O, F.n): continue
        L = math.hypot(B[0] - A[0], B[1] - A[1]); fx, fy = (B[0] - A[0]) / L, (B[1] - A[1]) / L
        def U(P, A=A, fx=fx, fy=fy): return ((P[0] - A[0]) * fx + (P[1] - A[1]) * fy) * 100.0
        def art(p_, W, H, wi=wi, U=U):
            yb = (_OM_EAVE - 2.75) * 100
            p_.fill(rect(0, 0, W, yb), render); p_.texture(rect(0, 0, W, yb), 'grunge', 0.35, 'overlay', 1.6)
            p_.cv.save(); p_.cv.clipRect(skia.Rect(0, yb, W, H)); p_.fill(rect(0, yb, W, H - yb), brick)
            pat(p_, W, H, 'brick', OM_PAL['brick_ink'], 110, seed=seed); p_.cv.restore()
            p_.fill(rect(0, yb - 5, W, 7), '#e8e4da')
            for nm, (wj, wa, wb, sl, tp) in _OM_WINS.items():
                if wj != wi: continue
                ua, ub = sorted((U(xf(*wa)), U(xf(*wb))))
                _wl_window_art(p_, ua, ub, (_OM_EAVE - tp) * 100, (_OM_EAVE - sl) * 100, night, False, False, 2 if ub - ua > 90 else 1)
            if wi == 0:                                                       # the front door, its fanlight, the number, the porch light
                ua, ub = sorted((U(xf(OM_FDOOR[0], 0.0)), U(xf(OM_FDOOR[1], 0.0))))
                yt = (_OM_EAVE - OM_FDOOR[2]) * 100; ybt = (_OM_EAVE - 0.0) * 100
                p_.fill(rect(ua - 10, yt - 34, ub - ua + 20, ybt - yt + 34), '#ece8de'); p_.line(rect(ua - 10, yt - 34, ub - ua + 20, ybt - yt + 34), 0.8)
                p_.fill(rect(ua, yt - 26, ub - ua, 20), '#10141e' if night else '#5a6a7a')
                p_.cv.save(); p_.cv.translate(ua, yt)
                door_art('four', 'right' if U(xf(OM_FDOOR[1], 0.0)) > U(xf(OM_FDOOR[0], 0.0)) else 'left', slot=True, bolt=False, col=doorc)(p_, ub - ua, ybt - yt)
                p_.cv.restore()
                num = {'adam': '14', 'danny': '9'}.get(who, str(16 + seed * 2))
                btext(p_, num, (ua + ub) / 2, yt - 10, 'serif_b', 13, '#2a2a2a', 230, 'center')
                ul = U(xf(OM_PLIGHT[0], 0.0))
                p_.fill(rrect(ul - 7, (_OM_EAVE - OM_PLIGHT[1]) * 100 - 12, 14, 22, 3), '#2a2c30'); p_.fill(rrect(ul - 5, (_OM_EAVE - OM_PLIGHT[1]) * 100 - 9, 10, 15, 2), '#d8d0b8')
        draw_face(pen, v, F, art, render, ao=False, lw=1.2)
    ys = [xf(0.0, 0.0)[1], xf(0.0, 8.2)[1]]
    mx0, mx1 = sorted((xf(0.0, 0.0)[0], xf(4.6, 0.0)[0]))
    _wl_gable_roof(pen, v, mx0, mx1, min(ys), max(ys), _OM_EAVE, _OM_RIDGE, OM_PAL['roof'], gables=(False, False), side_col=render, oh=0.25)
    wx0, wx1 = sorted((xf(-3.4, 0.0)[0], xf(0.0, 0.0)[0])); wy0, wy1 = sorted((xf(0.0, -2.4)[1], xf(0.0, 4.6)[1]))
    _om_roof_y(pen, v, wx0, wx1, wy0, wy1, _OM_EAVE, _OM_RIDGE, OM_PAL['roof'], front=xf(0.0, -2.4)[1], render=render)
    # the ground in front of it: the lawn, the path, the step, the doorstep, the low garden wall, the gate
    def B3(x0, x1, y0, y1, Y0, Y1):
        (ax, ay), (bx, by) = xf(x0, y0), xf(x1, y1)
        return Box((ax + bx) / 2, (ay + by) / 2, abs(bx - ax), abs(by - ay), Y0, Y1, 0)
    for (x0, x1) in ((-3.4, OM_GATE[0] - 0.08), (OM_GATE[1] + 0.08, 4.6)):
        draw_box(pen, v, B3(x0, x1, -6.11, -5.89, OM_G, OM_G + 0.5), {'all': '#8e877a', 'top': '#a8a294'}, lw=0.9)
    for xg in (OM_GATE[0] - 0.2, OM_GATE[1] + 0.2):
        draw_box(pen, v, B3(xg - 0.14, xg + 0.14, -6.14, -5.86, OM_G, OM_G + 0.68), {'all': '#8a8274', 'top': '#a8a294'}, lw=0.9)
    draw_box(pen, v, B3(0.15, 1.75, -1.1, -0.45, OM_G, OM_STEP), {'all': '#8c8c86', 'top': '#a2a29a'}, lw=0.9)
    draw_box(pen, v, B3(0.3, 1.6, -0.45, 0.0, OM_G, 0.0), {'all': '#8c8c86', 'top': '#9c9a92'}, lw=0.9)


def _om_roof_y(pen, v, x0, x1, y0, y1, Ye, Yr, col, front=None, render='#cfc6b4', oh=0.25):
    """The wing's gable roof (ridge along y, the gable end facing the street at y = front)."""
    xm = (x0 + x1) / 2
    for (q, n) in (([(x0 - oh, Ye, y0), (x0 - oh, Ye, y1), (xm, Yr, y1), (xm, Yr, y0)], (-0.8, 0.6, 0)),
                   ([(x1 + oh, Ye, y1), (x1 + oh, Ye, y0), (xm, Yr, y0), (xm, Yr, y1)], (0.8, 0.6, 0))):
        cen = tuple(sum(p_[k] for p_ in q) / 4 for k in range(3))
        if not v.visible(cen, _norm3(n)): continue
        path = v.poly3(q)
        if path.isEmpty(): continue
        pen.fill(path, lit(col, cen, _norm3(n))); pen.line(path, 1.2)
    if front is not None:
        yf = front
        tri = [(x0, Ye, yf), (x1, Ye, yf), (xm, Yr - 0.1, yf)]
        n = (0, 0, -1) if yf < (y0 + y1) / 2 else (0, 0, 1)
        if v.visible(tri[2], n):
            path = v.poly3(tri)
            if not path.isEmpty(): pen.fill(path, lit(_darken(render, 0.04), tri[2], n)); pen.line(path, 1.0)


def _om_ground_draw(pen, v, o):
    """Lawns, the paths, both pavements, the kerbs, the road (residential: no lines), wet patches at dawn."""
    tod = _otod(o); night = tod == 'night'; wet = o.get('wet', tod == 'dawn')
    grass = {'night': '#121e18', 'dawn': '#3e4e40'}.get(tod, '#5a7440')
    F = floor_face(-60.0, 60.0, -30.0, 12.0, OM_G)
    draw_face(pen, v, F, lambda p_, W, H: (p_.texture(rect(0, 0, W, H), 'grunge', 0.6, 'overlay', 5.0), p_.texture(rect(0, 0, W, H), 'fabric', 0.4, 'overlay', 0.8)),
              grass, ao=False, line=False)
    road = '#1e2026' if night else ('#3c3e44' if wet else '#55575c')
    _wl_strip(pen, v, -60.0, 60.0, -14.0, -8.0, OM_ROAD, road, 'asphalt')
    slab = '#4c4e54' if night else ('#6e7078' if wet else '#a8a69e')
    joints = lambda p_, W, H: ([p_.fill(rect(k * 90, 0, 1.4, H), '#000000', 80) for k in range(int(W / 90))], [p_.fill(rect(0, k * 90, W, 1.4), '#000000', 70) for k in range(int(H / 90) + 1)])
    _wl_strip(pen, v, -60.0, 60.0, -8.0, -6.0, OM_PAVE, slab, 'asphalt', joints)
    _wl_strip(pen, v, -60.0, 60.0, -16.0, -14.0, OM_PAVE, slab, 'asphalt', joints)
    for (yk, a, b) in ((-8.0, (60.0, -8.0), (-60.0, -8.0)), (-14.0, (-60.0, -14.0), (60.0, -14.0))):
        draw_face(pen, v, wall_face(a, b, OM_ROAD, OM_PAVE), lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'grunge', 0.5, 'overlay', 1.0),
                  '#4a4c52' if night else '#8a8a86', ao=False, line=False)
    for kind in ('ours', 'next', 'west', 'west2', 'across', 'across2', 'across3', 'across4'):
        xf = _om_xf(kind)
        (ax, ay), (bx, by) = xf(OM_PATH[0], -6.0), xf(OM_PATH[1], -1.1)
        pc = '#5a5c62' if night else ('#7c7e84' if wet else '#b8b4aa')
        _wl_strip(pen, v, min(ax, bx), max(ax, bx), min(ay, by), max(ay, by), OM_G + 0.006, pc, 'asphalt',
                  lambda p_, W, H: [p_.fill(rect(0, k * 60, W, 1.6), '#000000', 90) for k in range(int(H / 60) + 1)])
    if wet:                                                                   # the wet clean path: a darker sheen, a few puddle glints
        (ax, ay), (bx, by) = (OM_PATH[0], -6.0), (OM_PATH[1], -0.45)
        _wl_strip(pen, v, ax, bx, ay, by, OM_G + 0.008, '#30343c', 'asphalt')
        for (px, py, r) in ((0.8, -2.2, 0.2), (1.15, -4.1, 0.16), (0.7, -5.2, 0.22)):
            if v.d(px, py) > 0.5: pen.fill(ellipse3(v, px, py, r, r * 0.6, OM_G + 0.01), '#9aa8c0', 70)


class OmFront(Room):
    """The front of Adam's (or Danny's) house at night as a room: the shell is the whole street (cached)."""
    name = 'front'
    poly = [(-60.0, -30.0), (60.0, -30.0), (60.0, 12.0), (-60.0, 12.0)]

    def __init__(self, o): self.o = o

    def lights(self, o):
        tod = _otod(o)
        if tod == 'day': amb, st = '#9a948a', [Lamp(kind='dir', c='#fff0d0', k=1.0, d=_norm3((-0.5, -0.7, 0.5)))]
        elif tod == 'dawn': amb, st = '#6a7288', [Lamp(kind='dir', c='#c8d0e8', k=0.6, d=_norm3((-0.6, -0.5, 0.6)))]
        else: amb, st = '#2a3254', [Lamp(kind='dir', c='#8a9ee0', k=0.45, d=_norm3((0.3, -0.8, 0.6)))]
        st = list(st)
        if tod == 'night' or o.get('street_on'):
            st.append(Lamp(OM_LAMP[0], OM_PAVE + 6.0, OM_LAMP[1] - 1.6, 12.0, OM_SODIUM, 2.0, (1.0, 0.6, 0.2), fall=1.3))
        var = [('porch', [Lamp(OM_PLIGHT[0], OM_PLIGHT[1], OM_PLIGHT[2] - 0.35, 5.0, '#ffd090', 1.9, fall=1.35)], _kfn(o.get('porch', 0.0), 951)),
               ('mom', [Lamp(3.1, OM_UP + 1.3, -0.6, 3.2, OM_WARM, 0.8, fall=1.5)], _kfn((o.get('win') or {}).get('up', 0.0), 952)),
               ('flash', [Lamp(*o.get('flash_at', (0.95, 1.2, -2.0)), R=6.0, c='#fff4dc', k=1.6, fall=1.4)], _kfn(o.get('flash', 0.0), 953))]
        return amb, st, var

    def shell(self, pen, v, o):
        tod = _otod(o)
        om_sky(pen, v, tod)
        _om_ground_draw(pen, v, o)
        who = o.get('house', 'adam')
        houses = [('across3', 'n', 5), ('across4', 'n', 6), ('across', 'n', 1), ('across2', 'n', 2), ('west2', 'n', 7), ('west', 'n', 3), ('next', 'n', 0), ('ours', who, 0)]
        houses.sort(key=lambda h: -v.d(*_om_xf(h[0])(0.6, 3.0)))
        for i, (kind, w, sd) in enumerate(houses):
            if kind == 'ours': continue
            if kind in ('across', 'across3'): _om_tree(pen, v, _om_xf(kind)(-2.6, -5.0)[0], _om_xf(kind)(-2.6, -5.0)[1], OM_G, 6.5, tod, sd)
        for (kind, w, sd) in houses:
            _om_house_draw(pen, v, o, kind, w if kind == 'ours' else 'n', sd)
        dr_streetlight(pen, v, OM_LAMP[0], OM_LAMP[1], 1.0 if (tod == 'night' or o.get('street_on')) else 0.0, OM_SODIUM, 1.0, 6.2, True, OM_PAVE)
        dr_streetlight(pen, v, -14.0, -14.3, 1.0 if tod == 'night' else 0.0, OM_SODIUM, -1.0, 6.2, True, OM_PAVE)
        if o.get('mat', True) and v.d(0.8, -0.22) > 0.3: om_doormat(pen, v, 0.42, 1.18, -0.4, -0.06, 0.0)
        if o.get('bucket') and v.d(1.45, -0.2) > 0.3: om_bucket(pen, v, 1.42, 0.0, -0.18, 0.95)

    def pieces(self, o): return []

    def spots(self, v, o):
        S = {}
        for nm, (x, y, Y, h, ln) in OM_TRACK.items():
            S['on_' + nm] = _mk_spot(v, 'on_' + nm, x, y + 0.05, Y, 'stand', 'standing ON ONLY ME (%s), face up to the window' % nm, face=(0, 1) if nm != 'street' else (-0.3, 1))
        S['gate'] = _mk_spot(v, 'gate', 0.95, -6.0, OM_G, 'stand', 'in the gateway (facing the house)', face=(0, 1))
        S['pave'] = _mk_spot(v, 'pave', 1.2, -7.05, OM_PAVE, 'stand', 'on the pavement under the streetlight', face=(0, 1))
        S['doorstep'] = _mk_spot(v, 'doorstep', 0.8, -0.24, 0.0, 'stand', 'on the doormat facing the door (+y; R7: Evie, cropped by the frame)', face=(0, 1))
        S['step'] = _mk_spot(v, 'step', 0.95, -0.72, OM_STEP, 'stand', 'on the stone step', face=(0, 1))
        S['door'] = _mk_spot(v, 'door', OM_SLOT[0], -0.02, OM_SLOT[1], 'point', 'the letterbox from outside')
        S['window_adam'] = _mk_spot(v, 'window_adam', 0.02, -1.3, OM_UP + 1.45, 'point', "Adam's window (she smiles up at it; the neck stretches toward it)")
        S['window_up'] = _mk_spot(v, 'window_up', 3.1, -0.02, OM_UP + 1.45, 'point', "the upstairs front window (Danny's mom's silhouette at Danny's)")
        S['print'] = _mk_spot(v, 'print', 0.95, -0.7, OM_STEP, 'surface', 'the white sneaker print on the wet step (pointing in)')
        S['bucket'] = _mk_spot(v, 'bucket', 1.42, -0.18, 0.0, 'surface', 'the bucket by the door')
        return S


def _om_track_spec(o):
    tr = o.get('track')
    if tr is None: return None
    if isinstance(tr, str): x, y, Y, h, ln = OM_TRACK[tr]
    else: x, y, Y, h = tr[:4]; ln = tr[4] if len(tr) > 4 else False
    return x, y, Y, h, o.get('track_line', ln)


def _om_front_live(v, o, sp_amb, steady, var):
    """The live layers: lit windows (Danny's mom's silhouette, phone to her ear), the porch and street glows, the chalk
    tracker ONLY ME (track_u = how much is written, number or f(t); track_wet; track_rub), the empty line, the print."""
    L = []
    kp = _kfn(o.get('porch', 0.0), 951)
    wins = {nm: _kfn(lv, 960 + i) for i, (nm, lv) in enumerate((o.get('win') or {}).items())}
    tod = _otod(o)

    def glow(pen, t):
        if tod == 'night' or o.get('street_on'):
            om_lamp_glow(pen, v, OM_LAMP[0], OM_LAMP[1] - 1.6, OM_PAVE, 1.0)
            om_lamp_glow(pen, v, -14.0, -14.3 + 1.6, OM_PAVE, 0.8)
        k = kp(t)
        if k > 0.01 and v.d(OM_PLIGHT[0], OM_PLIGHT[2]) > 0.3:
            x, y = v.p(*OM_PLIGHT); s = v.s(OM_PLIGHT[0], OM_PLIGHT[2])
            pen.glow(x, y, 1.3 * s, '#ffc070', 105 * k); pen.glow(x, y, 0.09 * s, '#fff4d8', 245 * k)
        for nm, kf in wins.items():
            k = kf(t)
            if k <= 0.01 or nm not in _OM_WINS: continue
            wi, wa, wb, sl, tp = _OM_WINS[nm]
            n = _OM_WALLS[wi][2]
            off = (n[0] * 0.015, n[1] * 0.015)
            q = [(wa[0] + off[0], tp, wa[1] + off[1]), (wb[0] + off[0], tp, wb[1] + off[1]), (wb[0] + off[0], sl, wb[1] + off[1]), (wa[0] + off[0], sl, wa[1] + off[1])]
            if not v.visible(q[0], (n[0], 0, n[1])) or min(v.d3(*p_) for p_ in q) < v.near + 0.1: continue
            path = poly([v.p(*p_) for p_ in q])
            pen.fill(path, '#ffcf8a', 205 * k)
            cx = sum(v.p(*p_)[0] for p_ in q) / 4; cy = sum(v.p(*p_)[1] for p_ in q) / 4
            pen.glow(cx, cy, 0.9 * v.s(q[0][0], q[0][2]), OM_WARM, 60 * k)
            if nm == 'up' and o.get('mom'):                                   # Danny's mom: a dark silhouette, phone to her ear
                xm, ym = (wa[0] + wb[0]) / 2 + 0.15 * n[1], (wa[1] + wb[1]) / 2
                s = v.s(xm, ym); hx, hy = v.p(xm, sl + 0.62, ym + off[1])
                pen.cv.save(); pen.cv.clipPath(path, doAntiAlias=True)
                body = smooth([(hx - 0.3 * s, hy + 0.9 * s), (hx - 0.24 * s, hy + 0.2 * s), (hx - 0.1 * s, hy + 0.06 * s), (hx + 0.1 * s, hy + 0.06 * s),
                               (hx + 0.24 * s, hy + 0.2 * s), (hx + 0.3 * s, hy + 0.9 * s)], True, 0.5)
                pen.fill(body, '#1a1418', 235 * k); pen.fill(oval(hx, hy - 0.06 * s, 0.1 * s, 0.12 * s), '#1a1418', 235 * k)
                pen.fill(smooth([(hx - 0.1 * s, hy - 0.14 * s), (hx + 0.12 * s, hy - 0.16 * s), (hx + 0.14 * s, hy + 0.02 * s), (hx - 0.12 * s, hy + 0.04 * s)], True, 0.7), '#1a1418', 235 * k)
                arm = smooth([(hx + 0.2 * s, hy + 0.22 * s), (hx + 0.2 * s, hy + 0.05 * s), (hx + 0.12 * s, hy - 0.04 * s)], False)
                pen.line(arm, 0.07 * s, '#1a1418', 235 * k)
                pen.fill(rrect(hx + 0.08 * s, hy - 0.12 * s, 0.035 * s, 0.07 * s, 0.01 * s), '#9ab8e8', 230 * k)
                pen.cv.restore()
    gl = Layer(0.5, glow, 'ext_glow', blur=None); gl.order = ORDER_SHELL - 0.5
    L.append(gl)
    spec = _om_track_spec(o)
    reader = o.get('reader')
    if spec is not None:
        x, y, Y, h, ln = spec
        tu, tw, trb = o.get('track_u', 1.0), o.get('track_wet', 0.0), o.get('track_rub', 0.0)
        text = o.get('text', 'ONLY ME')
        def chalk(pen, v_, t):
            u_ = tu(t) if callable(tu) else tu; w_ = tw(t) if callable(tw) else tw; r_ = trb(t) if callable(trb) else trb
            om_chalk_ground(pen, v_, text, x, y, Y + 0.004, h, u_, r_, w_, reader=reader, width=0.11)
            if ln:
                rx_, ry_ = reader if reader is not None else (v_.hx, v_.hy)
                ux, uy = x - rx_, y - ry_; nn = math.hypot(ux, uy) or 1.0
                om_line_ground(pen, v_, x - ux / nn * 1.05 * h, y - uy / nn * 1.05 * h, Y + 0.004, 4.2 * h, reader=reader, alpha=1.0 - 0.9 * w_)
        L.append(live_layer('chalk', v, (x, Y, y), chalk, sp_amb, steady, var, order=v.d(x, y) + 0.6))
    if o.get('print'):
        pr = o['print'] if isinstance(o['print'], tuple) else (0.95, -0.7)
        L.append(live_layer('print', v, (pr[0], OM_STEP, pr[1]), lambda pen, v_, t: om_print(pen, v_, pr[0], pr[1], OM_STEP + 0.004, (0.0, 1.0), 0.9),
                            sp_amb, steady, var, order=v.d(pr[0], pr[1]) + 0.5))
    return L


def _om_window_frame(view):
    """Screen-space foreground for the POV down from an upstairs window: the frame's edges and the sill, soft."""
    def draw(pen, t):
        if view == 'down':
            pen.fill(rect(-400, -300, 470, 1700), '#16141a'); pen.fill(rect(-400, 1010, 2720, 400), '#1e1c22')
            pen.fill(rect(-400, 990, 2720, 26), '#2c2a30')
        elif view == 'street':
            pen.fill(rect(1850, -300, 470, 1700), '#16141a'); pen.fill(rect(-400, 1030, 2720, 400), '#1e1c22')
        else:
            pen.fill(rect(-400, -300, 400, 1700), '#16141a'); pen.fill(rect(1890, -300, 430, 1700), '#16141a')
            pen.fill(rect(-400, 1040, 2720, 400), '#1e1c22')
    return Layer(0.3, draw, 'window_frame', blur=10)


# ====================================================================================================== builders: Adam's house
def _om_outside_front(o):
    """What Adam's window and the hall see outside: the same street (its own lights; no veil: night stays night)."""
    def f(pen, v):
        R = OmFront(o)
        amb, steady, var = R.lights(o)
        with lighting(amb, steady, 1.0): R.shell(pen, v, o)
        if _otod(o) == 'night': om_lamp_glow(pen, v, OM_LAMP[0], OM_LAMP[1] - 1.6, OM_PAVE, 1.0)
    return f


def _om_outside_back(o):
    """The back garden through the kitchen window at night: a fence, a shed, a tree, the sky (Evie stands out there)."""
    def f(pen, v):
        tod = _otod(o)
        om_sky(pen, v, 'night' if tod == 'night' else tod)
        with lighting('#2a3254' if tod == 'night' else '#8a8a8a', [Lamp(kind='dir', c='#8a9ee0', k=0.4, d=_norm3((0.3, -0.8, -0.6)))]):
            draw_face(pen, v, floor_face(-10.0, 15.0, 8.2, 22.0, -0.3), lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'grunge', 0.6, 'overlay', 4.0), '#121c16', ao=False, line=False)
            draw_face(pen, v, wall_face((15.0, 17.0), (-10.0, 17.0), -0.3, 1.5), lambda p_, W, H: [p_.fill(rect(k * 15, 0, 1.5, H), '#000000', 90) for k in range(int(W / 15))],
                      '#3a3228', ao=False, line=False)
            draw_box(pen, v, Box(5.2, 15.2, 2.0, 1.6, -0.3, 1.9, 180), {'all': '#2a2a28', 'top': '#1e1e1c'}, lw=1.0)
        _om_tree(pen, v, -1.5, 15.5, -0.3, 6.0, 'night' if tod == 'night' else tod, 4)
    return f


def om_room(view='wide', **kw):
    """Adam's room (upstairs in the wing). view: wide | window | door | bed | desk. tod 'night' | 'day'. Levels (number or
    f(t)): lamp (desk lamp), ceil, phone (+phone_at: the phone lighting the bed), torch (+torch_at: his torch swing),
    strip (the 2 a.m. light under the door; shadow = 0..1 or f(t): Mom's feet passing), street (the streetlight through
    the window, default 1), landing (the corridor through the open door). door (deg, default 0 = shut) or f(t);
    drawer 0..1 (pulled out); bed 'made' | 'turned'. The window shows the street (om_front's world): pass track=...,
    porch=... to see ONLY ME / the porch light through it."""
    o = _oo(kw)
    v = cam('om_room_' + view)
    main = BuBox(_om_room_cfg(o))
    far = [_om_dark_corr(o)]
    dyn = []
    amb, steady, var = main.lights(o)
    if callable(o.get('door')):
        D = Door((0.0, OM_ADOOR[1]), OM_ADOOR[1] - OM_ADOOR[0], OM_ADOOR[2], (0.0, -1.0), -1, OM_UP, art_a=door_art('six', 'right', bolt=False),
                 art_b=door_art('six', 'left', bolt=False), col='#ece8dc')
        df = o['door']
        dyn.append(live_layer('door', v, (-0.3, OM_UP + 1.0, 0.5), lambda pen, v_, t: D.draw(pen, v_, df(t)), amb, steady, var))
    grade = 'om_day' if _otod(o) == 'day' else ('om_warm' if any(_olv(o, k_) > 0.3 for k_ in ('lamp', 'ceil')) else 'om_night')
    sp = build_view('om_room_' + view, v, main, o, far=far, outside=_om_outside_front(o), grade=grade, dyn=dyn)
    sp.info['note'] = "Adam's room: bed / pillow / bed_edge, window (looking down), window_glass, desk / drawer, door_in / door_gap, phone_bed."
    sp.info['out_order'] = ORDER_OUT - 1
    return sp


def om_hall(view='landing', **kw):
    """The hall, the stairs and the landing. view: landing (down the stairs from the top to the front door: the
    thumbnail angle) | halfway (Adam halfway down) | up (from the stairs up to the landing: Lina under the bare bulb) |
    door (facing the front door from the passage: the R7 doormat past Mom's and Adam's backs) | kitchen (from the
    front door down the passage to the kitchen: M... E...) | floor (low on the hall floor at the door: O-N-L-Y).
    Levels: hall (pendant), landing (the bare bulb: 'Behind me, the landing light clicked on' = dict(on=t)), kitchen
    (spill from the kitchen: R7 'already on'), porch, street (through the fanlight), phone, flash. fdoor (deg, 0 shut ..
    90 open, or f(t)); flap 0..1 (the letterbox's inner flap lifted) or f(t); stub True | (x, y) (the chalk stub on the
    floor; default at the bottom stair); chalk = [dict(text, x, y, h, u, rub, wet)] static or live chalk on the floor
    (u may be f(t)); house 'adam'. Floor quads for the cast's chalk_word / LetterboxFingers: om_floor_quad(sp, ...)."""
    o = _oo(kw, dict(house='adam'))
    v = cam('om_hall_' + view)
    main = BuBox(_om_hall_cfg(o))
    far = [BuBox(_om_kit_cfg(dict(o, _far=True)), far=True), _dark_far('living', _r4p((-3.4, 0.0, -2.4, 4.6)), 0.0, OM_CEIL),
           BuBox(_om_room_cfg(dict(o, _far=True, strip=0.0)), far=True), _dark_far('lina_room', _r4p((0.0, 2.6, 5.0, 8.2)), OM_UP, OM_CEIL)]
    dyn = []
    amb, steady, var = main.lights(o)
    if callable(o.get('fdoor')) or callable(o.get('flap')):
        fd, ff = o.get('fdoor', 0.0), o.get('flap', 0.0)
        def dfn(pen, v_, t):
            D = _om_front_door(dict(o, flap=ff(t) if callable(ff) else ff))
            D.draw(pen, v_, fd(t) if callable(fd) else fd)
        dyn.append(live_layer('front_door_live', v, (0.8, 1.0, 0.05), dfn, amb, steady, var))
    for i, c_ in enumerate(o.get('chalk') or []):
        dyn.append(live_layer('chalk%d' % i, v, (c_['x'], 0.0, c_['y']), (lambda c_: lambda pen, v_, t: om_chalk_ground(
            pen, v_, c_.get('text', 'ONLY'), c_['x'], c_['y'], c_.get('Y', 0.004), c_.get('h', 0.26), _val_t(c_.get('u', 1.0), t), _val_t(c_.get('rub', 0.0), t),
            _val_t(c_.get('wet', 0.0), t), reader=c_.get('reader', (0.8, 3.0)), lit_k=True))(c_), amb, steady, var, order=v.d(c_['x'], c_['y']) + 0.3))
    grade = 'om_warm' if any(_olv(o, k_) > 0.3 for k_ in ('hall', 'landing', 'kitchen')) else 'om_night'
    outside = _om_outside_front(dict(o, track=o.get('track')))
    sp = build_view('om_hall_' + view, v, main, o, far=far, outside=outside, grade=grade, dyn=dyn)
    sp.info['note'] = 'Hall: door_in / mom_door / adam_door, letterbox / door_base, only_floor, bottom_stair, step1..12 (halfway), landing, lina_landing, passage, kitchen_door.'
    sp.info['out_order'] = ORDER_OUT - 1
    sp.info['floor_only'] = (0.05, 1.0, 0.08, 0.86, 0.0)                  # the hall floor rect for O-N-L-Y (x0, x1, y0, y1, Y)
    sp.info['floor_me'] = (0.12, 0.9, 0.9, 4.55, 0.0)                     # the passage strip for M... E... (toward the kitchen)
    return sp


def om_floor_quad(sp, x0, x1, y0, y1, Y=0.0):
    """Screen corners [near-left, near-right, far-right, far-left] of a floor rectangle for this set's camera (for the
    cast's chalk_word / LetterboxFingers floor_quad), plus its size in cm."""
    v = sp.view
    pts = sorted([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], key=lambda q: v.d(*q))
    near, far = sorted(pts[:2], key=lambda q: v.u(*q)), sorted(pts[2:], key=lambda q: v.u(*q))
    quad = [v.p(near[0][0], Y, near[0][1]), v.p(near[1][0], Y, near[1][1]), v.p(far[1][0], Y, far[1][1]), v.p(far[0][0], Y, far[0][1])]
    w = math.hypot(near[1][0] - near[0][0], near[1][1] - near[0][1]) * 100; d = math.hypot(far[0][0] - near[0][0], far[0][1] - near[0][1]) * 100
    return quad, (w, d)


def om_kitchen(view='dinner', **kw):
    """The kitchen. view: dinner (from Adam's seat: Mom at the far end, the dark window behind her, Lina at the left) |
    wide (from the hall doorway: the table, Mom's chair, the window, the back door and the bucket) | tiles (low along the
    floor from the doorway to Mom's chair: the letters stop there) | mom (side-on at the table: her fork down; Save,
    Block, Report). Levels: kitchen (the light: R7 'already on'), hall, phone. dinner (plates), bucket (default True)."""
    o = _oo(kw)
    v = cam('om_kit_' + view)
    main = BuBox(_om_kit_cfg(o))
    far = [BuBox(_om_hall_cfg(dict(o, _far=True)), far=True)]
    grade = 'om_warm' if _olv(o, 'kitchen', 0.0) > 0.3 else 'om_night'
    dyn = []
    amb, steady, var = main.lights(o)
    for i, c_ in enumerate(o.get('chalk') or []):
        dyn.append(live_layer('chalk%d' % i, v, (c_['x'], 0.0, c_['y']), (lambda c_: lambda pen, v_, t: om_chalk_ground(
            pen, v_, c_.get('text', 'ME'), c_['x'], c_['y'], 0.004, c_.get('h', 0.24), _val_t(c_.get('u', 1.0), t), 0.0, _val_t(c_.get('wet', 0.0), t),
            reader=c_.get('reader', (0.5, 4.0))))(c_), amb, steady, var, order=v.d(c_['x'], c_['y']) + 0.3))
    sp = build_view('om_kit_' + view, v, main, o, far=far, outside=_om_outside_back(o), grade=grade, dyn=dyn)
    sp.info['note'] = 'Kitchen: mom_chair (seat), adam_chair, lina_chair, window_out (Evie outside the dark window), doorway, by_chair, stand_mom, bucket, table_top.'
    sp.info['out_order'] = ORDER_OUT - 1
    return sp


def om_front(view='down', house='adam', **kw):
    """The front of the house at night, framed from the upstairs window looking DOWN (house 'adam': the GREEN door,
    from Adam's window; 'danny': the BLUE door from Danny's window, Danny's mom's silhouette at the next window: mom=True,
    win={'up': 1}). view: down (the door, the step, the path: ONLY ME the biggest shape) | street (down the path to the
    gate and the streetlight) | wide (the whole front garden) | facade (lower pitch: the door and the upstairs window
    together) | step (close on the step from outside, at dawn: the print, the bucket).
    track: None | 'street' | 'half' | 'foot' | 'step' | 'door' | 'mat' | (x, y, Y, h[, line]) (the bible's table) with
    track_u (written 0..1 or f(t)), track_wet (the dawn wash 0..1), track_rub, track_line (the empty line), text;
    tod 'night' | 'dawn' (the wet clean path: wet=True) | 'day'; porch (the porch light: dict(on=t) = 'clicked on'); win
    {adam, up, front, stairwin, living, side}: lit windows; mom (Danny's); print (the white sneaker print on the step,
    pointing in); bucket (by the door); frame (the window frame foreground, default True in the window views)."""
    o = _oo(kw, dict(house=house))
    if _otod(o) == 'dawn': o.setdefault('wet', True)
    v = cam('om_front_' + view)
    main = OmFront(o)
    amb, steady, var = main.lights(o)
    dyn = _om_front_live(v, o, amb, steady, var)
    grade = {'dawn': 'om_dawn', 'day': 'om_day'}.get(_otod(o), 'om_ext')
    sp = build_view('om_front_' + view, v, main, o, outside=None, grade=grade, dyn=dyn, dof=0.5)
    if o.get('frame', view in ('down', 'street', 'wide')): sp = sp.add(_om_window_frame(view))
    sp.info['note'] = 'Outside: figures order = their depth. Anchors on_<track> (standing on ONLY ME), pave, gate, step, doorstep, window_adam, window_up, print, bucket.'
    sp.info['track'] = _om_track_spec(o)
    return sp


# cameras: Adam's house
_ocam('om_room_wide', 760, 540, OM_UP + 1.5, -3.0, 0.75, 128, _env(), "his room from the bed's head: the door left, the window centre, the desk right", 'room')
_ocam('om_room_window', 900, 520, OM_UP + 1.55, -1.45, -1.25, 92, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.1)), 'behind Adam at his window, looking out and down', 'room', pitch=14.0)
_ocam('om_room_door', 900, 560, OM_UP + 0.95, -2.75, 0.15, 90, _env(), 'from the bed to the door: the gap under it (the 2 a.m. strip)', 'room', pitch=8.0)
_ocam('om_room_bed', 820, 520, OM_UP + 1.75, -1.5, -0.9, -55, _env(), 'over the bed (his phone lighting up in the dark)', 'room', pitch=34.0)
_ocam('om_room_desk', 1000, 520, OM_UP + 1.35, -2.3, -0.95, 182, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.1)), 'the desk and its drawer', 'room', pitch=28.0)
_ocam('om_hall_landing', 780, 560, OM_UP + 1.4, 1.42, 4.7, 186, _env(x=(900, 1020), y=(480, 600), zoom=(1.0, 1.1)), 'from the landing down the stairs to the front door', 'hall', pitch=34.0)
_ocam('om_hall_halfway', 860, 540, 6 * OM_RISE + 1.45, 1.4, 2.35, 196, _env(x=(900, 1020), y=(480, 600), zoom=(1.0, 1.1)), 'halfway down the stairs: the hall floor and the letterbox', 'hall', pitch=30.0)
_ocam('om_hall_up', 820, 560, 4 * OM_RISE + 1.3, 1.45, 1.6, 0, _env(), 'from the stairs up to the landing (Lina under the bare bulb)', 'hall', pitch=-24.0)
_ocam('om_hall_door', 920, 540, 1.35, 0.6, 3.3, 180, _env(), 'from the passage to the front door (the R7 doormat past their backs)', 'hall')
_ocam('om_hall_kitchen', 820, 540, 1.45, 0.62, 0.35, 2, _env(), 'from the front door down the passage to the kitchen', 'hall', pitch=10.0)
_ocam('om_hall_floor', 1000, 520, 1.0, 1.25, 1.6, 200, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.1)), 'low over the hall floor at the door (O-N-L-Y, the stub)', 'hall', pitch=34.0)
_ocam('om_kit_dinner', 860, 520, 1.15, 2.35, 4.9, 0, _env(), "from Adam's seat: Mom, the dark window behind her, Lina left", 'kitchen')
_ocam('om_kit_wide', 760, 540, 1.55, 0.5, 4.75, 46, _env(), 'from the hall doorway: table, Mom, window, back door, bucket', 'kitchen')
_ocam('om_kit_tiles', 900, 520, 0.75, 0.7, 4.75, 28, _env(), "low along the tiles to Mom's chair", 'kitchen', pitch=18.0)
_ocam('om_kit_mom', 1000, 520, 1.3, 0.9, 6.9, 78, _env(), 'side-on on Mom at the table', 'kitchen')
_ocam('om_front_down', 900, 540, OM_UP + 1.45, -0.2, -1.55, 64, _env(x=(900, 1020), y=(480, 600), zoom=(1.0, 1.1)), "down from Adam's window: the door, the step, the path", 'front', pitch=63.0)
_ocam('om_front_street', 820, 540, OM_UP + 1.45, -0.32, -1.25, 152, _env(x=(900, 1020), y=(480, 600), zoom=(1.0, 1.1)), "down from Adam's window: the path to the gate and the streetlight", 'front', pitch=30.0)
_ocam('om_front_wide', 640, 540, OM_UP + 1.45, -0.2, -1.55, 108, _env(x=(920, 1000), y=(500, 580), zoom=(1.0, 1.06)), "from Adam's window: the whole front garden", 'front', pitch=50.0)
_ocam('om_front_facade', 700, 540, OM_UP + 1.45, -0.32, -1.6, 58, _env(), 'from the window: the door below and the upstairs window together', 'front', pitch=22.0)
_ocam('om_front_step', 1050, 520, OM_G + 1.55, 0.95, -2.7, 0, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.1)), 'close on the step from the path, looking down (dawn)', 'front', pitch=34.0)


# ====================================================================================================== THE PLAYGROUND (own plan)
# The school's back wall y 0 (the playground south of it, y < 0; the back door x 1.4 .. 2.6 with the caretaker's
# floodlight over it); the swings (A-frame along x at y -14, x -8.2 .. -5.0); the hopscotch from y -21.4 running south
# to the KEEPING SQUARE (x -0.45 .. 0.45, y -25.85 .. -25.0); the back fence (green railings) at y -27 with the gate
# x 3.0 .. 5.0.
OM_SQ = (-0.45, 0.45, -25.85, -25.0)
OM_PGATE = (3.0, 5.0, -27.0)
OM_SWINGS = {'l': (-7.25, -14.0), 'r': (-5.95, -14.0)}       # the pivots' plan points (top bar Y 2.25)
OM_SWING_TOP, OM_SWING_SEAT = 2.25, 0.45
OM_FLOOD = (2.0, 4.4, -0.18)
_OM_HOP = [[(-0.3, 0.3)], [(-0.3, 0.3)], [(-0.3, 0.3)], [(-0.6, 0.0), (0.0, 0.6)], [(-0.3, 0.3)], [(-0.6, 0.0), (0.0, 0.6)]]
_OM_HOPC = ('#f2c43a', '#4a9ad8', '#62b85a', '#f2f2ea', '#4a9ad8', '#f2c43a', '#62b85a', '#f2f2ea', '#4a9ad8')


def _om_play_light(o):
    tod = _otod(o)
    if tod == 'sunset':
        return '#5a4450', [Lamp(kind='dir', c=mix(OM_RED, '#ffa070', 0.45), k=1.25, d=_norm3((0.85, -0.3, -0.2)))]
    if tod in ('warm', 'summer'):
        return '#8a7a6a', [Lamp(kind='dir', c='#ffe0a8', k=1.15, d=_norm3((0.4, -0.75, -0.4)))]
    if tod == 'night':
        return '#262c48', [Lamp(kind='dir', c='#8a9ee0', k=0.4, d=_norm3((0.3, -0.8, -0.6)))]
    return '#8e8c88', [Lamp(kind='dir', c='#fff4e0', k=1.05, d=_norm3((-0.4, -0.8, -0.3)))]


def _om_hop_draw(pen, v, o):
    """The hopscotch: bright new paint (numbers, white outlines) and the top square in faded red (worn edges, old chalk
    ghosts) unless it is painted over (square 'painted', paint 0..1)."""
    y = -21.4
    n = 1
    for row in _OM_HOP:
        for (x0, x1) in row:
            F = floor_face(x0, x1, y - 0.6, y, 0.004)
            c = _OM_HOPC[n % len(_OM_HOPC)]
            def art(p_, W, H, n=n, c=c):
                p_.fill(rect(0, 0, W, H), c); p_.texture(rect(0, 0, W, H), 'grunge', 0.25, 'overlay', 0.8)
                p_.line(rect(2, 2, W - 4, H - 4), 4.0, '#ffffff', 230)
                btext(p_, str(n), W / 2, H * 0.68, 'sans_b', 26, '#ffffff', 235, 'center')
            draw_face(pen, v, F, art, c, ao=False, line=False)
            n += 1
        y -= 0.6
    pk = clamp(o.get('paint', 1.0)) if o.get('square') == 'painted' else 0.0
    F = floor_face(OM_SQ[0], OM_SQ[1], OM_SQ[2], OM_SQ[3], 0.004)
    def sq(p_, W, H):
        p_.fill(rect(0, 0, W, H), OM_RED); p_.texture(rect(0, 0, W, H), 'grunge', 0.85, 'overlay', 1.4); p_.texture(rect(0, 0, W, H), 'grunge', 0.5, 'multiply', 0.7, 30)
        p_.line(rect(3, 3, W - 6, H - 6), 3.0, '#f0e8e0', 110)
        for k in range(5): p_.line(poly([(10 + k * 17, 12 + (k % 3) * 20), (40 + k * 11, 30 + (k % 2) * 30)], False), 1.2, '#f2f0e9', 30)   # old chalk ghosts
        if pk > 0:
            p_.fill(rect(0, H * (1 - pk), W, H * pk), '#f2c43a'); p_.line(rect(2, 2, W - 4, H - 4), 4.0, '#ffffff', 230 * pk)
            if pk > 0.99: btext(p_, '10', W / 2, H * 0.62, 'sans_b', 30, '#ffffff', 235, 'center')
    draw_face(pen, v, F, sq, OM_RED, ao=False, line=False)


def _om_fence(pen, v, o):
    """The back fence: green steel railings on posts (the gate in it, closed)."""
    yf = OM_PGATE[2]
    c = '#2e5a3a'
    for x in np.arange(-16.0, 16.01, 0.14):
        if OM_PGATE[0] - 0.02 < x < OM_PGATE[1] + 0.02: continue
        if v.d(x, yf) < 0.6: continue
        a_, b_ = v.p(x, 0.0, yf), v.p(x, 1.75, yf)
        pen.seg(a_, b_, max(0.8, 0.022 * v.s(x, yf)), lit(c, (x, 1.0, yf), (0, 0, 1)))
    for Yr in (0.12, 1.62):
        for (x0, x1) in ((-16.0, OM_PGATE[0]), (OM_PGATE[1], 16.0)):
            q = [(x_, Yr, yf) for x_ in np.linspace(x0, x1, 12) if v.d(x_, yf) > 0.6]
            if len(q) > 1: pen.line(poly([v.p(*p_) for p_ in q], False), max(1.0, 0.04 * v.s((x0 + x1) / 2, yf)), lit(c, (x0, Yr, yf), (0, 0, 1)))
    gx0, gx1 = OM_PGATE[0], OM_PGATE[1]
    if v.d((gx0 + gx1) / 2, yf) > 0.6:                                     # the gate: two leaves, a latch
        for (x0, x1) in ((gx0, (gx0 + gx1) / 2 - 0.02), ((gx0 + gx1) / 2 + 0.02, gx1)):
            for x in np.linspace(x0 + 0.05, x1 - 0.05, 8):
                pen.seg(v.p(x, 0.06, yf), v.p(x, 1.8, yf), max(0.9, 0.025 * v.s(x, yf)), lit('#2a4e34', (x, 1.0, yf), (0, 0, 1)))
            fr = [v.p(x0, 0.06, yf), v.p(x1, 0.06, yf), v.p(x1, 1.85, yf), v.p(x0, 1.85, yf)]
            pen.line(poly(fr), max(1.2, 0.05 * v.s(x0, yf)), lit('#24452e', (x0, 1.0, yf), (0, 0, 1)))
        for xp in (gx0 - 0.06, gx1 + 0.06):
            pen.seg(v.p(xp, 0.0, yf), v.p(xp, 2.0, yf), max(1.4, 0.09 * v.s(xp, yf)), lit('#24452e', (xp, 1.0, yf), (0, 0, 1)))


def _om_school_back(pen, v, o):
    """The school's back wall (two storeys of cream render over buff brick, tall windows), the back door, the
    caretaker's floodlight on its bracket over it."""
    F = wall_face((-20.0, 0.0), (20.0, 0.0), 0.0, 6.6)
    if v.visible(F.O, F.n):
        def art(p_, W, H):
            p_.fill(rect(0, 0, W, H), '#d8cfba'); p_.texture(rect(0, 0, W, H), 'grunge', 0.4, 'overlay', 2.0)
            p_.cv.save(); p_.cv.clipRect(skia.Rect(0, H - 110, W, H)); pat(p_, W, H, 'brick', '#7a6e5a', 90, seed=3); p_.cv.restore()
            for k in range(13):
                ux = 150 + k * 300
                if abs(ux / 100 - 20 - 2.0) < 1.6: continue
                for (yt, yb) in ((H - 300, H - 140), (H - 600, H - 420)):
                    _wl_window_art(p_, ux, ux + 180, yt, yb, _otod(o) == 'night', False, False, 3)
            dx = (1.4 + 20.0) * 100
            p_.fill(rect(dx - 8, H - 222, 136, 222), '#e8e4da'); p_.fill(rect(dx, H - 214, 120, 214), '#3a5a7a')
            p_.fill(rect(dx + 10, H - 200, 44, 90), '#1a2430'); p_.fill(rect(dx + 66, H - 200, 44, 90), '#1a2430')
            p_.fill(rect(dx + 98, H - 110, 14, 4), '#c8ccd0')
        draw_face(pen, v, F, art, '#d8cfba', ao=False, lw=1.2)
    x, Y, y = OM_FLOOD
    if v.d(x, y) > 0.5:
        s = v.s(x, y); a_ = v.p(x, Y + 0.25, y + 0.1); b_ = v.p(x, Y, y - 0.12)
        pen.seg(a_, b_, max(1.2, 0.04 * s), '#2a2c30')
        hd = poly([v.p(x - 0.22, Y + 0.12, y - 0.2), v.p(x + 0.22, Y + 0.12, y - 0.2), v.p(x + 0.22, Y - 0.12, y - 0.28), v.p(x - 0.22, Y - 0.12, y - 0.28)])
        pen.fill(hd, '#3a3c42'); pen.line(hd, 1.0)


def _om_swing_frame(pen, v):
    """The A-frame: two legs a side, the top bar (painted blue, worn)."""
    xl, xr = OM_SWINGS['l'][0] - 0.95, OM_SWINGS['r'][0] + 0.95
    y = OM_SWINGS['l'][1]
    c = '#3a6aa8'
    for xe in (xl, xr):
        for dy in (-0.75, 0.75):
            if v.d(xe, y + dy) > 0.4: pen.seg(v.p(xe, 0.0, y + dy), v.p(xe, OM_SWING_TOP, y), max(1.4, 0.055 * v.s(xe, y)), lit(c, (xe, 1.0, y + dy), (0, 0.3, -1)))
    if v.d(xl, y) > 0.4 and v.d(xr, y) > 0.4:
        pen.seg(v.p(xl - 0.1, OM_SWING_TOP, y), v.p(xr + 0.1, OM_SWING_TOP, y), max(1.6, 0.07 * v.s((xl + xr) / 2, y)) + 2, LINE)
        pen.seg(v.p(xl - 0.1, OM_SWING_TOP, y), v.p(xr + 0.1, OM_SWING_TOP, y), max(1.4, 0.07 * v.s((xl + xr) / 2, y)), lit(c, (0, 2.2, y), (0, 0.5, -1)))


def om_swing_seat(v, which='l', angle=0.0):
    """Plan point (x, Y, y) of swing `which` seat at swing angle (deg; + = toward -y, the camera side of the wide
    view) and its screen point / px per metre for camera v: ((x, Y, y), (sx, sy), ppm)."""
    px, py = OM_SWINGS[which]
    L = OM_SWING_TOP - OM_SWING_SEAT
    a = math.radians(angle)
    P = (px, OM_SWING_TOP - L * math.cos(a), py - L * math.sin(a))
    return P, v.p(*P), v.s(P[0], P[2])


def om_swing(pen, v, which='l', angle=0.0, seat='#2a2a2e'):
    """One swing (two chains from the top bar, a black rubber seat) at angle deg. Draw it under the child sitting on it
    (its seat point: om_swing_seat)."""
    px, py = OM_SWINGS[which]
    P, (sx, sy), s = om_swing_seat(v, which, angle)
    if v.d3(*P) < v.near + 0.2: return
    for dx in (-0.2, 0.2):
        a_ = v.p(px + dx, OM_SWING_TOP, py); b_ = v.p(px + dx, P[1] + 0.03, P[2])
        pen.line(poly([a_, b_], False), max(0.8, 0.012 * s), '#8a8e94')
        pen.line(poly([a_, b_], False), max(0.4, 0.006 * s), '#c8ccd0', 160)
    q = poly([v.p(px - 0.24, P[1] + 0.03, P[2] - 0.07), v.p(px + 0.24, P[1] + 0.03, P[2] - 0.07), v.p(px + 0.24, P[1] - 0.02, P[2] + 0.07), v.p(px - 0.24, P[1] - 0.02, P[2] + 0.07)])
    pen.fill(q, lit(seat, P, (0, 1, 0))); pen.line(q, 1.0)


class OmPlay(Room):
    """The playground as a room (the shell is everything that never moves; cached)."""
    name = 'playground'
    poly = [(-16.0, -27.0), (16.0, -27.0), (16.0, 0.0), (-16.0, 0.0)]

    def __init__(self, o): self.o = o

    def lights(self, o):
        amb, st = _om_play_light(o)
        var = [('flood', [Lamp(OM_FLOOD[0], OM_FLOOD[1], OM_FLOOD[2] - 0.5, 34.0, '#eef2ff', 2.1, (1.0, 0.8, 0.2), fall=1.2)], _kfn(o.get('flood', 0.0), 971))]
        return amb, st, var

    def shell(self, pen, v, o):
        tod = _otod(o)
        om_sky(pen, v, tod)
        F = floor_face(-80.0, 80.0, -90.0, -27.0, 0.0)                    # the field beyond the fence
        g = {'sunset': '#5a4a3a', 'night': '#121c16', 'summer': '#6a9a48', 'warm': '#7a9a50'}.get(tod, '#6a8a48')
        draw_face(pen, v, F, lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'grunge', 0.6, 'overlay', 5.0), g, ao=False, line=False)
        for i, (x, y, h) in enumerate([(-12.0, -33.0, 7.5), (-4.0, -35.0, 8.5), (6.5, -32.0, 7.0), (13.0, -36.0, 8.0), (-15.0, -40.0, 9.0), (1.0, -42.0, 8.0)]):
            _om_tree(pen, v, x, y, 0.0, h, 'sunset' if tod == 'sunset' else ('night' if tod == 'night' else 'day'), i + 20)
        tar = {'sunset': '#5a4c50', 'night': '#202228', 'summer': '#7a7a80', 'warm': '#8a8480'}.get(tod, '#6c6e74')
        T = floor_face(-16.0, 16.0, -27.0, 0.0, 0.0)
        def tart(p_, W, H):
            p_.texture(rect(0, 0, W, H), 'asphalt', 0.7, 'overlay', 1.6); p_.texture(rect(0, 0, W, H), 'grunge', 0.4, 'overlay', 4.0)
            for (u0, w0, u1, w1) in ((1100, 400, 1500, 900), (2300, 900, 2700, 1500)):       # old painted court lines
                p_.line(rect(u0, w0, u1 - u0, w1 - w0), 5.0, '#e8e4d8', 120)
        draw_face(pen, v, T, tart, tar, ao=False, line=False)
        _om_hop_draw(pen, v, o)
        _om_school_back(pen, v, o)
        _om_fence(pen, v, o)
        _om_swing_frame(pen, v)
        b = Box(8.5, -10.0, 1.6, 0.42, 0.0, 0.45, 90)
        draw_box(pen, v, b, {'all': '#6a5a48', 'top': '#8a7458'}, lw=0.9)

    def pieces(self, o):
        P = []
        sw = o.get('swings', (0.0, 0.0))
        if sw:
            for which, ang in zip(('l', 'r'), sw):
                P.append(Piece('swing_' + which, (OM_SWINGS[which][0], 1.0, OM_SWINGS[which][1] - 0.05), (lambda w_, a_: lambda pen, v: om_swing(pen, v, w_, a_))(which, ang)))
        return P

    def spots(self, v, o):
        S = {}
        for w in ('l', 'r'):
            S['swing_' + w] = _mk_spot(v, 'swing_' + w, OM_SWINGS[w][0], OM_SWINGS[w][1], 0.0, 'seat', 'on swing %s (facing -y)' % w, face=(0, -1), seat_Y=OM_SWING_SEAT)
            S['swing_%s_pivot' % w] = _mk_spot(v, 'swing_%s_pivot' % w, OM_SWINGS[w][0], OM_SWINGS[w][1], OM_SWING_TOP, 'point', 'its pivot on the top bar (chains %.2f m)' % (OM_SWING_TOP - OM_SWING_SEAT))
        S['square'] = _mk_spot(v, 'square', 0.0, (OM_SQ[2] + OM_SQ[3]) / 2, 0.0, 'surface', 'the centre of the Keeping Square (the chalk girl, the names)')
        S['square_front'] = _mk_spot(v, 'square_front', 0.0, OM_SQ[3] + 0.5, 0.0, 'stand', 'at the top of the hopscotch facing the square (-y)', face=(0, -1))
        S['square_stand'] = _mk_spot(v, 'square_stand', 0.0, (OM_SQ[2] + OM_SQ[3]) / 2, 0.0, 'stand', 'standing IN the square (Evie stands up here; facing +y, the school)', face=(0, 1))
        S['hop_start'] = _mk_spot(v, 'hop_start', 0.0, -20.9, 0.0, 'stand', 'at the start of the hopscotch (facing -y)', face=(0, -1))
        S['gate'] = _mk_spot(v, 'gate', (OM_PGATE[0] + OM_PGATE[1]) / 2, OM_PGATE[2] + 0.35, 0.0, 'stand', 'in front of the gate (arms spread across it; facing +y)', face=(0, 1))
        S['gate_adam'] = _mk_spot(v, 'gate_adam', 3.3, -23.8, 0.0, 'stand', 'Adam facing the gate (-y)', face=(0.1, -1))
        S['caretaker'] = _mk_spot(v, 'caretaker', 2.0, -0.45, 0.0, 'stand', 'the caretaker in the back doorway under his floodlight (facing -y, squinting)', face=(0, -1))
        S['flood'] = _mk_spot(v, 'flood', OM_FLOOD[0], OM_FLOOD[2], OM_FLOOD[1], 'point', 'the floodlight')
        S['bench'] = _mk_spot(v, 'bench', 8.5, -10.0, 0.0, 'seat', 'on the bench (facing -x)', face=(-1, 0), seat_Y=0.45)
        S['yard'] = _mk_spot(v, 'yard', -2.0, -12.0, 0.0, 'stand', 'the middle of the playground')
        S['roller'] = _mk_spot(v, 'roller', 0.0, OM_SQ[3] + 0.4, 0.0, 'stand', 'the caretaker painting over the square (from behind: facing -y)', face=(0, -1))
        return S


def _om_play_live(v, o, amb, steady, var):
    L = []
    kf = _kfn(o.get('flood', 0.0), 971)
    def glow(pen, t):
        k = kf(t)
        if k > 0.01 and v.d(OM_FLOOD[0], OM_FLOOD[2]) > 0.5:
            x, y = v.p(OM_FLOOD[0], OM_FLOOD[1] - 0.12, OM_FLOOD[2] - 0.3); s = v.s(OM_FLOOD[0], OM_FLOOD[2])
            pen.glow(x, y, 1.6 * s, '#e8f0ff', 120 * k); pen.glow(x, y, 0.2 * s, '#ffffff', 250 * k)
        if k > 0.01 and v.d(2.5, -14.0) > 1.0:
            pen.fill(ellipse3(v, 2.6, -13.0, 9.0, 13.0, 0.01), '#e8eeff', 34 * k, blur=max(4.0, 1.5 * v.s(2.6, -13.0)))
    gl = Layer(0.5, glow, 'play_glow', blur=None); gl.order = ORDER_SHELL - 0.5
    L.append(gl)
    sq = o.get('square', 'plain')
    rd = (0.0, -21.0)
    cx, cy = 0.0, (OM_SQ[2] + OM_SQ[3]) / 2
    if sq in ('danny', 'adam'):
        u_ = o.get('chalk_u', 1.0); rb = o.get('rub', 0.85 if sq == 'adam' else 0.0); au = o.get('adam_u', 1.0)
        def chalk(pen, v_, t):
            u = _val_t(u_, t)
            om_chalk_ground(pen, v_, 'DANNY', cx, cy + 0.17, 0.006, 0.15, u if sq == 'danny' else 1.0, _val_t(rb, t), 0.0, reader=rd, width=0.12, seed=3)
            if sq == 'adam': om_chalk_ground(pen, v_, 'ADAM', cx + 0.02, cy + 0.15, 0.007, 0.16, _val_t(au, t), 0.0, 0.0, reader=rd, width=0.12, seed=5)
            om_chalk_ground(pen, v_, 'ONLY ME', cx, cy - 0.2, 0.006, 0.12, u if sq == 'danny' else 1.0, 0.0, 0.0, reader=rd, width=0.12, seed=1)
        L.append(live_layer('square_chalk', v, (cx, 0.0, cy), chalk, amb, steady, var, order=v.d(cx, cy) + 0.6))
    elif sq == 'girl':
        def girl(pen, v_, t):
            fn = _om_cast('draw_chalk_girl')
            if fn is None or v_.d(cx, cy) < 0.6: return
            x, y = v_.p(cx, 0.006, cy + 0.36); hh = abs(v_.p(cx, 0.006, cy - 0.36)[1] - y)
            sq_ = clamp(abs(v_.cam_h) / max(0.3, math.hypot(v_.d(cx, cy), v_.cam_h)), 0.15, 1.0)
            fn(pen, x, y, max(hh, 0.6 * v_.s(cx, cy) * sq_) / max(sq_, 0.15), alpha=0.95, smile=1.0, t=t, flat_k=sq_)
        L.append(live_layer('chalk_girl', v, (cx, 0.0, cy), girl, amb, steady, var, order=v.d(cx, cy) + 0.6))
    if o.get('prints'):
        pk = o['prints']
        def prints(pen, v_, t):
            k = _val_t(pk, t)
            n = 18
            for i in range(int(round(n * clamp(k)))):
                f = i / (n - 1.0)
                x = 1.8 + (0.12 - 1.8) * f + (0.12 if i % 2 else -0.12); y = -2.0 + (OM_SQ[3] + 0.15 + 2.0) * f
                om_print(pen, v_, x, y, 0.005, (-0.07, -1.0), 0.85, 1 if i % 2 else -1)
        L.append(live_layer('prints', v, (0.8, 0.0, -14.0), prints, amb, steady, var, order=ORDER_SHELL - 0.4))
    return L


def om_playground(view='wide', tod='day', square='plain', **kw):
    """The playground behind the school. view: wide (from the school wall: the hopscotch running to the faded red
    square by the back fence, the swings right, the gate left) | square (high over the Keeping Square) | hop (low along
    the hopscotch toward the square: 'Her white prints led to the square') | gate (Evie's arms spread across the gate) |
    flood (from the gate back to the school wall: the caretaker under his floodlight) | swings.
    tod 'day' | 'sunset' (THE one red glow: 'Washed in red') | 'warm' (the flashback) | 'summer' (the tape) | 'night'.
    square 'plain' | 'girl' (the chalk girl, drawn by the cast's draw_chalk_girl) | 'danny' (DANNY / ONLY ME; chalk_u
    0..1 or f(t) writes it) | 'adam' (DANNY rubbed out (rub), ADAM written over it (adam_u), ONLY ME under) |
    'painted' (paint 0..1 or number: the caretaker's fresh paint over it). flood (the floodlight level: 'Clank.
    Floodlight.' = dict(on=t)); prints 0..1 or f(t) (the white sneaker prints from the back door to the square);
    swings (angle_l, angle_r) static or False (the film draws them: om_swing / om_swing_seat)."""
    o = _oo(kw, dict(tod=tod, square=square))
    v = cam('om_play_' + view)
    main = OmPlay(o)
    amb, steady, var = main.lights(o)
    dyn = _om_play_live(v, o, amb, steady, var)
    if square == 'painted' and callable(o.get('paint')):
        pf = o['paint']
        dyn.append(live_layer('paint', v, (0.0, 0.0, -25.4), lambda pen, v_, t: _om_hop_draw(pen, v_, dict(o, paint=pf(t))), amb, steady, var, order=ORDER_SHELL - 0.45))
    grade = {'sunset': 'om_sunset', 'warm': 'om_flash', 'summer': 'om_flash', 'night': 'om_ext'}.get(tod, 'om_day')
    sp = build_view('om_play_' + view, v, main, o, outside=None, grade=grade, dyn=dyn, dof=0.5)
    sp.info['note'] = 'Playground: swing_l / swing_r (seats; _pivot), square / square_front / square_stand, hop_start, gate / gate_adam, caretaker, flood, bench, yard, roller.'
    sp.info['swings'] = {w: dict(pivot=(OM_SWINGS[w][0], OM_SWING_TOP, OM_SWINGS[w][1]), length=OM_SWING_TOP - OM_SWING_SEAT) for w in OM_SWINGS}
    return sp


_ocam('om_play_wide', 820, 520, 1.65, -1.2, -7.5, 182, _env(f=(1.0, 2.6)), 'from the school wall: hopscotch to the red square, swings right, gate left', 'playground', pitch=5.0)
_ocam('om_play_square', 1000, 540, 2.3, 0.0, -23.55, 180, _env(x=(900, 1020), y=(480, 600), zoom=(1.0, 1.1)), 'high over the Keeping Square', 'playground', pitch=52.0)
_ocam('om_play_hop', 900, 520, 1.05, 0.25, -19.2, 182, _env(), 'low along the hopscotch toward the square', 'playground', pitch=12.0)
_ocam('om_play_gate', 900, 520, 1.5, 2.6, -21.2, 166, _env(), 'the gate in the back fence (Evie across it)', 'playground', pitch=2.0)
_ocam('om_play_flood', 760, 540, 1.5, 3.8, -24.2, 2, _env(), 'from the gate back to the school wall: the floodlight, the caretaker', 'playground', pitch=-4.0)
_ocam('om_play_swings', 900, 520, 1.45, -3.4, -10.3, 222, _env(), 'the swings (Evie sings on them at break)', 'playground', pitch=4.0)
_ocam('om_play_tape', 1100, 560, 1.62, -4.0, -9.6, 214, _env(), "Mom's camcorder on the swings, one summer (slightly high)", 'playground', pitch=10.0)


# ====================================================================================================== THE TAPE
def om_tape_content(figures=None, warp=0.0, rewind=None, o=None):
    """Mom's camcorder tape as a content function f(pen, W, H, t) (W x H = 16:9): the playground one summer (cached
    plate through the camcorder camera 'om_play_tape'), the handheld drift (slightly high, a slow wander and small
    corrections), figures(pen, t) drawn in the same 1920 x 1080 tape space (little Adam and Danny on the swings: anchors
    from om_tape().anchors, swings by om_swing). warp 0..1 (number or f(t)): the rule 4 return (the drift slows, the
    colour sickens and darkens, a crease band chews the picture). rewind = f(t) -> speed (0 = playing, 1 = full rewind:
    the picture tears into fast backward bands, the drift jerks backward)."""
    v = cam('om_play_tape')
    oo = dict(tod='summer', square='plain', swings=False)
    if o: oo.update(o)
    def plate(p_):
        R = OmPlay(oo); amb, st, var = R.lights(oo)
        with lighting(amb, st, 1.0): R.shell(p_, v, oo)
    key = ('omtape', _okey({k_: v_ for k_, v_ in oo.items() if not callable(v_)}))
    def content(pen, W, H, t):
        wk = clamp(_val_t(warp, t)); rw = clamp(_val_t(rewind, t)) if rewind is not None else 0.0
        cv = pen.cv; cv.save(); cv.scale(W / 1920.0, H / 1080.0)
        sl = 1.0 - 0.7 * wk
        tt = t * sl - 2.5 * rw * t
        dx = 14 * math.sin(0.53 * tt) + 6 * math.sin(1.7 * tt + 0.4) + 3 * math.sin(4.1 * tt); dy = 9 * math.sin(0.71 * tt + 1.0) + 4 * math.sin(2.3 * tt)
        cv.save(); cv.translate(960 + dx, 540 + dy); cv.rotate(0.5 * math.sin(0.37 * tt)); cv.scale(1.07, 1.07); cv.translate(-960, -540)
        if rw > 0.02:                                                      # the rewind: fast backward bands
            nb = 9
            for i in range(nb):
                y0 = i * 1080 / nb - 40; ofs = rw * 220 * math.sin(t * 23.0 + i * 1.7) + rw * 90 * ((i * 37 + int(t * 30)) % 7 - 3)
                cv.save(); cv.clipRect(skia.Rect(-400, y0, 2320, y0 + 1080 / nb + 2)); cv.translate(ofs, 0)
                _sprite(pen, key, plate, (-300, -300, 2220, 1380))
                if figures: figures(pen, t)
                cv.restore()
        else:
            _sprite(pen, key, plate, (-300, -300, 2220, 1380))
            if figures: figures(pen, t)
        cv.restore()
        if wk > 0.01:                                                      # warp: the sick tint, the chewed crease
            pen.fill(rect(-400, -300, 2720, 1700), '#2a1a3a', 70 * wk)
            yb = (t * 140 * (0.3 + wk)) % 1300 - 110
            pen.fill(rect(-400, yb, 2720, 40 + 70 * wk), '#e8e0f0', 40 * wk, blur=6)
            pen.fill(rect(-400, yb + 10, 2720, 8), '#ffffff', 110 * wk)
        if rw > 0.02:
            for i in range(6):
                yy = ((t * 900 + i * 197) % 1200) - 60
                pen.fill(rect(-400, yy, 2720, 6 + 10 * rw), '#f0f0f0', 150 * rw)
        cv.restore()
    return content


def om_tape_fx(warp=0.0, rewind=None):
    """sp.fx for the tape: the camcorder look through engine post['vhs'] (no CRT tube: full frame, warm and soft),
    heavier tracking / wobble / chroma / snow with warp, a torn rolling picture with rewind."""
    def fx(t):
        wk = clamp(_val_t(warp, t)); rw = clamp(_val_t(rewind, t)) if rewind is not None else 0.0
        d = dict(t=t, k=1.0, curve=0.0, glass=0.0, scan=0.35, tube=False, bezel=0.0, glow=0.8, head=1.0 + 1.5 * rw,
                 track=0.32 + 0.9 * wk + 1.2 * rw, wobble=1.0 + 2.5 * wk + 3.0 * rw, noise=0.9 + 1.3 * wk + 1.5 * rw, chroma=1.1 + 1.2 * wk)
        out = {'vhs': d}
        if wk > 0.3 or rw > 0.3: out['glitch'] = 0.25 * max(wk, rw)
        return out
    return fx


def om_tape_stamp(cv, t, date='JUL. 14 1996', counter0=12 * 60 + 47, mode='play', alpha=255, warp=0.0):
    """The camcorder's on-screen stamp (draw it in the HUD, over the VHS look): PLAY > (blinking for the first seconds;
    mode 'rew' shows << REW and the counter running backward; 'pause' || PAUSE), the tape counter top right
    (H:MM:SS from counter0 s), the date bottom left. warp jitters it."""
    pen = Pen(cv)
    j = (3 * math.sin(t * 37.0) if warp > 0.2 else 0.0)
    sec = counter0 + (t if mode == 'play' else (-6.0 * t if mode == 'rew' else 0.0))
    sec = max(0, int(sec))
    ctr = '%d:%02d:%02d' % (sec // 3600, (sec // 60) % 60, sec % 60)
    lab = {'play': 'PLAY ▶', 'rew': '◀◀ REW', 'pause': '❙❙ PAUSE'}[mode]
    show = mode != 'play' or t < 3.0 and int(t * 2) % 2 == 0 or t >= 3.0 and False
    for (s_, x, y, al, on) in ((lab, 120, 128, 'left', mode != 'play' or (t < 3.2 and int(t * 2.2) % 2 == 0)), (ctr, 1800, 128, 'right', True),
                               (date, 120, 985, 'left', True)):
        if not on: continue
        btext(pen, s_, x + 3 + j, y + 3, 'vhs', 62, '#000000', alpha * 0.55, al)
        btext(pen, s_, x + j, y, 'vhs', 62, '#f4f4f0', alpha, al)


def om_tape(figures=None, warp=0.0, rewind=None, **o):
    """Mom's camcorder tape FULL FRAME (Adam and Danny at seven on the swings, one summer): a flat set with
    om_tape_content as its one layer, sp.fx = om_tape_fx (the VHS look), grade 'om_tape'. Draw om_tape_stamp(cv, t)
    in the HUD. Anchors (tape space, 1920 x 1080): swing_l / swing_r (seats), swing_l_pivot / swing_r_pivot,
    square, yard; sp.info['view'] = the camcorder camera (om_swing(pen, v, 'l', angle) draws a swing in figures())."""
    v = cam('om_play_tape')
    content = om_tape_content(figures, warp, rewind, o)
    lay = Layer(1.0, lambda pen, t: content(pen, 1920, 1080, t), 'tape', blur=0)
    oo = dict(tod='summer', square='plain', swings=False); oo.update(o)
    anchors = OmPlay(oo).spots(v, oo)
    sp = BSet('om_tape', [lay], anchors, {}, lens=None, grade='om_tape', focus=1.0, dof=0.0, cover=(-300, -300, 2220, 1380),
              fx=om_tape_fx(warp, rewind), info={'note': "Mom's camcorder tape (full frame)", 'view': v, 'cam_env': dict(x=(940, 980), y=(520, 560), zoom=(1.0, 1.04), f=(1.0, 1.0))}, view=v)
    return sp
