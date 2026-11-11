"""ui_v2_letter: the film's own drawing materials for on-screen text (DIRECTION_V2 5.3-5.5).

Everything is drawn in the 1920x1080 design space on a skia canvas (the HUD canvas, or a set layer's pen).

Palette        LIP (lipstick #c63449), LIP_DK, LIP_HI, LIP_GLOW, CHALK, GREASE, MARKER, the world chip colours (CHIP).
Sprites        sprite(key, box, draw, dens=1.0) -> cached image of draw(canvas) over the design box (render density);
               blit(cv, spr, alpha=255). Use them for anything with a blurred glow (blurs cost ~ms per call at 2560).
Hand lettering a single-stroke capital alphabet (A-Z, 0-9, ' . , - ! ? : / · * and space) drawn with a hand wobble:
               Script(text, x, y, size, seed, slant, rot, track, align) -> laid-out strokes in design px.
                 .length            total pen length (design px)
                 .partial(u)        strokes cut at fraction u (0..1) of the pen length (pen lifts between strokes)
                 .tip(u)            (x, y, angle) of the pen at u
                 .box               (x0, y0, x1, y1)
               write(pen, script, material, u=1.0, a=255, tip=True, glow=0.0, seed=0) draws it written up to u, with the
               writing tool at the head while 0 < u < 1. Materials: 'lipstick' (waxy: dark edge, core, sheen, crumbs;
               the bullet and its gold tube), 'marker' (kid marker on tape), 'chalk' (grainy white, the diagrams),
               'grease' (off-white grease pencil), 'pencil'.
Strokes        wax(pen, pts, w, a, glow, seed) one lipstick stroke; chalk_line(pen, pts, w, a, seed, dash=None);
               marker_line(...); squiggle / dotted / arrow helpers.
Type           type_text(cv, s, x, y, size, ...) Montserrat with letter spacing in em; fit_size(s, weight, size, maxw).
"""
import math
import numpy as np
import skia
from engine.core import (CFG, DW, DH, Pen, col, mix, rgb, text, text_width, rrect, rect, oval, poly, smooth, union, minus,
                         clamp, lerp, ease, ease_out_cubic, hash01, noise1, surface_for, image_from)

# ------------------------------------------------------------------ palette
LIP, LIP_DK, LIP_HI, LIP_GLOW = '#c63449', '#7e1a28', '#ec7d8a', '#ff4060'
LIP_CORE = '#d23a50'
RED = '#e3262e'
CHALK = '#f2efe6'
GREASE = '#eee7d8'
MARKER = '#17151d'
INK_RED = '#c0392b'
GOLD = '#f2c46d'
NAVY = '#16204a'
CHIP = {                       # world chips: (fill, edge, dot, text)
    'ours': ('#18204c', '#4b5aa8', '#7f9dff', '#e9ecff'),
    'theirs': ('#6a4410', '#e2a54a', '#ffb43c', '#fff2d6'),
    'loop': ('#3a1830', '#d06a8a', '#ff6a8a', '#ffe6ee'),
    'teaser': ('#b0141c', '#ff4a52', '#ffffff', '#ffffff'),
    'memory': ('#7a2e1e', '#a8432c', '#a8432c', '#a8432c'),
    'stairs': ('#2a1838', '#c63449', '#ff4060', '#f6e6f0'),
    'climax': ('#3a0612', '#ff2d55', '#ff2d55', '#ffe0e6'),
    'ending': ('#18204c', '#4b5aa8', '#ffd58a', '#e9ecff'),
}
_BLURS = {}


def blur_mf(r):
    r = round(float(r), 2)
    if r not in _BLURS:
        if len(_BLURS) > 200: _BLURS.clear()
        _BLURS[r] = skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, max(0.1, r))
    return _BLURS[r]


def paint(c, a=255, stroke=None, cap='round', blur=0.0, blend=None):
    p = skia.Paint(Color=col(c, a), AntiAlias=True)
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke); p.setStrokeJoin(skia.Paint.kRound_Join)
        p.setStrokeCap({'round': skia.Paint.kRound_Cap, 'butt': skia.Paint.kButt_Cap, 'square': skia.Paint.kSquare_Cap}[cap])
    if blur: p.setMaskFilter(blur_mf(blur))
    if blend: p.setBlendMode(blend)
    return p


# ------------------------------------------------------------------ sprites (cached raster pieces at render density)
_SPR = {}
_LINS = skia.SamplingOptions(skia.FilterMode.kLinear)


def sprite(key, box, draw, dens=1.0):
    """Draw once at the render density into an image over the design box (x0, y0, x1, y1); reused every frame."""
    kk = (key, CFG.rw, round(dens, 3))
    e = _SPR.get(kk)
    if e is None:
        if len(_SPR) > 260:
            for k_ in list(_SPR)[:80]: del _SPR[k_]
        k = CFG.rw / DW * dens
        x0, y0, x1, y1 = box
        w, h = max(1, int(math.ceil((x1 - x0) * k))), max(1, int(math.ceil((y1 - y0) * k)))
        arr = np.zeros((h, w, 4), np.uint8); sf = surface_for(arr); c = sf.getCanvas()
        c.scale(w / (x1 - x0), h / (y1 - y0)); c.translate(-x0, -y0); draw(c)
        del c, sf
        e = (image_from(arr), box, arr, w, h); _SPR[kk] = e
    return e


def sprite_post(key, box, draw, dens=1.0, post=None):
    """sprite() with post(arr, k) applied to the BGRA premultiplied pixels before the image is made (k = render px per
    design px): blur a reflection, grade a plate."""
    kk = (key, CFG.rw, round(dens, 3), 'post')
    e = _SPR.get(kk)
    if e is None:
        k = CFG.rw / DW * dens
        x0, y0, x1, y1 = box
        w, h = max(1, int(math.ceil((x1 - x0) * k))), max(1, int(math.ceil((y1 - y0) * k)))
        arr = np.zeros((h, w, 4), np.uint8); sf = surface_for(arr); c = sf.getCanvas()
        c.scale(w / (x1 - x0), h / (y1 - y0)); c.translate(-x0, -y0); draw(c)
        del c, sf
        if post is not None:
            r = post(arr, k)
            if r is not None: arr = np.ascontiguousarray(r)
        e = (image_from(arr), box, arr, w, h); _SPR[kk] = e
    return e


def blit(cv, e, alpha=255.0, blend=None):
    img, (x0, y0, x1, y1), _, w, h = e
    p = skia.Paint(); p.setAlphaf(clamp(alpha / 255.0))
    if blend is not None: p.setBlendMode(blend)
    cv.drawImageRect(img, skia.Rect.MakeWH(w, h), skia.Rect.MakeLTRB(x0, y0, x1, y1), _LINS, p, skia.Canvas.kFast_SrcRectConstraint)


def clear_sprites():
    _SPR.clear()


# ------------------------------------------------------------------ type helpers
def type_text(cv, s, x, y, size, c='#ffffff', a=255, weight=800, sp=0.0, align='center', shadow=0.0, glow=None):
    return text(cv, s, x, y, weight, size, c, a, sp, align, shadow, glow)


def fit_size(s, weight, size, maxw, sp=0.0):
    w = text_width(s, weight, size, sp)
    return size if w <= maxw else size * maxw / w


def text_path(s, x, y, weight, size, sp=0.0, align='left'):
    """Glyph outlines as one skia.Path (baseline at y) for clipping, outlining and fills with gradients."""
    from engine.core import _font
    f = _font(weight, size)
    glyphs = f.textToGlyphs(s); widths = f.getWidths(glyphs)
    total = sum(widths) + sp * size * (len(glyphs) - 1)
    x0 = x - total / 2 if align == 'center' else (x - total if align == 'right' else x)
    out = skia.Path(); cx = x0
    for g, w in zip(glyphs, widths):
        gp = f.getPath(g)
        if gp is not None:
            gp.offset(cx, y); out.addPath(gp)
        cx += w + sp * size
    return out, total


# ------------------------------------------------------------------ hand-lettering stroke font
def _arc(cx, cy, rx, ry, a0, a1, n=None):
    n = n or max(5, int(abs(a1 - a0) / 11) + 1)
    return [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a))) for a in np.linspace(a0, a1, n)]


def _dot(x, y, r=0.045):
    return _arc(x, y, r, r, 0, 360, 9)


G = {
    'A': (0.62, [[(0, 1), (0.31, 0), (0.62, 1)], [(0.13, 0.64), (0.49, 0.64)]]),
    'B': (0.56, [[(0, 1), (0, 0)], [(0, 0), (0.25, 0)] + _arc(0.25, 0.24, 0.25, 0.24, -90, 90) + [(0, 0.48)],
                 [(0, 0.48), (0.27, 0.48)] + _arc(0.27, 0.74, 0.28, 0.26, -90, 90) + [(0, 1)]]),
    'C': (0.6, [_arc(0.32, 0.5, 0.31, 0.5, -42, -318)]),
    'D': (0.6, [[(0, 0), (0, 1)], [(0, 0), (0.2, 0)] + _arc(0.2, 0.5, 0.39, 0.5, -90, 90) + [(0, 1)]]),
    'E': (0.52, [[(0.5, 0), (0, 0), (0, 1), (0.52, 1)], [(0, 0.5), (0.4, 0.5)]]),
    'F': (0.5, [[(0.5, 0), (0, 0), (0, 1)], [(0, 0.5), (0.4, 0.5)]]),
    'G': (0.64, [_arc(0.33, 0.5, 0.32, 0.5, -40, -358), [(0.64, 0.55), (0.36, 0.55)]]),
    'H': (0.6, [[(0, 0), (0, 1)], [(0.6, 0), (0.6, 1)], [(0, 0.5), (0.6, 0.5)]]),
    'I': (0.14, [[(0.07, 0), (0.07, 1)]]),
    'J': (0.5, [[(0.48, 0), (0.48, 0.7)] + _arc(0.25, 0.7, 0.23, 0.3, 0, 180)]),
    'K': (0.56, [[(0, 0), (0, 1)], [(0.54, 0), (0, 0.62)], [(0.18, 0.46), (0.58, 1)]]),
    'L': (0.48, [[(0, 0), (0, 1), (0.48, 1)]]),
    'M': (0.74, [[(0, 1), (0, 0), (0.37, 0.66), (0.74, 0), (0.74, 1)]]),
    'N': (0.62, [[(0, 1), (0, 0), (0.62, 1), (0.62, 0)]]),
    'O': (0.7, [_arc(0.35, 0.5, 0.35, 0.5, -95, 265)]),
    'P': (0.54, [[(0, 1), (0, 0), (0.26, 0)] + _arc(0.26, 0.26, 0.27, 0.26, -90, 90) + [(0, 0.52)]]),
    'Q': (0.72, [_arc(0.35, 0.5, 0.35, 0.5, -95, 265), [(0.44, 0.72), (0.74, 1.05)]]),
    'R': (0.56, [[(0, 1), (0, 0), (0.26, 0)] + _arc(0.26, 0.25, 0.27, 0.25, -90, 90) + [(0, 0.5)], [(0.22, 0.5), (0.58, 1)]]),
    'S': (0.56, [_arc(0.29, 0.25, 0.26, 0.25, -15, -270) + _arc(0.29, 0.75, 0.28, 0.25, -90, 160)[1:]]),
    'T': (0.58, [[(0, 0), (0.58, 0)], [(0.29, 0), (0.29, 1)]]),
    'U': (0.6, [[(0, 0), (0, 0.66)] + _arc(0.3, 0.66, 0.3, 0.34, 180, 0) + [(0.6, 0)]]),
    'V': (0.62, [[(0, 0), (0.31, 1), (0.62, 0)]]),
    'W': (0.86, [[(0, 0), (0.2, 1), (0.43, 0.3), (0.66, 1), (0.86, 0)]]),
    'X': (0.58, [[(0, 0), (0.58, 1)], [(0.58, 0), (0, 1)]]),
    'Y': (0.6, [[(0, 0), (0.3, 0.52)], [(0.6, 0), (0.3, 0.52), (0.3, 1)]]),
    'Z': (0.56, [[(0, 0), (0.56, 0), (0, 1), (0.58, 1)]]),
    '0': (0.56, [_arc(0.28, 0.5, 0.28, 0.5, -95, 265)]),
    '1': (0.34, [[(0.0, 0.22), (0.24, 0), (0.24, 1)]]),
    '2': (0.56, [_arc(0.27, 0.27, 0.26, 0.27, -165, 15) + [(0, 1), (0.56, 1)]]),
    '3': (0.54, [_arc(0.25, 0.25, 0.25, 0.25, -160, 90) + _arc(0.25, 0.74, 0.28, 0.26, -90, 160)[1:]]),
    '4': (0.6, [[(0.44, 1), (0.44, 0), (0, 0.68), (0.62, 0.68)]]),
    '5': (0.56, [[(0.52, 0), (0.08, 0), (0.05, 0.45)] + _arc(0.28, 0.68, 0.28, 0.32, -140, 150)]),
    '6': (0.56, [_arc(0.36, 0.6, 0.34, 0.6, -80, -185) + _arc(0.28, 0.72, 0.27, 0.28, 180, 535)]),
    '7': (0.56, [[(0, 0), (0.56, 0), (0.18, 1)]]),
    '8': (0.54, [_arc(0.27, 0.25, 0.22, 0.24, 90, -270), _arc(0.27, 0.74, 0.27, 0.26, -90, 270)]),
    '9': (0.56, [_arc(0.28, 0.3, 0.27, 0.3, 0, 360) + [(0.55, 0.3), (0.5, 1)]]),
    "'": (0.12, [[(0.06, 0), (0.04, 0.24)]]),
    '·': (0.24, [_dot(0.12, 0.52, 0.05)]),
    '.': (0.18, [_dot(0.08, 0.96)]),
    ',': (0.16, [[(0.08, 0.9), (0.03, 1.12)]]),
    '-': (0.4, [[(0.03, 0.55), (0.37, 0.55)]]),
    '!': (0.16, [[(0.08, 0), (0.08, 0.68)], _dot(0.08, 0.96)]),
    '?': (0.5, [_arc(0.25, 0.25, 0.24, 0.25, -170, 70) + [(0.25, 0.62), (0.25, 0.72)], _dot(0.25, 0.96)]),
    ':': (0.16, [_dot(0.08, 0.36), _dot(0.08, 0.96)]),
    '/': (0.44, [[(0.42, 0), (0.0, 1)]]),
    ' ': (0.34, []),
}


def _star(cx, cy, r, ri=0.42):
    pts = []
    for i in range(11):
        a = -90 + i * 36
        rr = r if i % 2 == 0 else r * ri
        pts.append((cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a))))
    return pts


G['*'] = (0.8, [_star(0.4, 0.5, 0.42)])


def _densify(stroke, step):
    out = [stroke[0]]
    for (x0, y0), (x1, y1) in zip(stroke[:-1], stroke[1:]):
        d = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(d / step))
        for i in range(1, n + 1):
            out.append((x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n))
    return out


class Script:
    """A string laid out in the stroke font. size = cap height in design px; track = extra spacing in em; slant = shear
    (0.12 = italic hand); rot = degrees about (x, y); wob = hand wobble in em; align left / center / right."""

    def __init__(self, s, x, y, size, seed=0, slant=0.08, rot=0.0, track=0.18, align='left', wob=0.028, step=None):
        self.s, self.size = s.upper(), float(size)
        em = self.size
        widths = [G.get(ch, G[' '])[0] for ch in self.s]
        total = (sum(widths) + track * max(0, len(widths) - 1)) * em
        x0 = x - total / 2 if align == 'center' else (x - total if align == 'right' else x)
        ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        step = step or max(2.0, em * 0.05)
        strokes = []
        cx = 0.0
        for i, ch in enumerate(self.s):
            w, ss = G.get(ch, G[' '])
            gs = seed * 101 + i * 7
            dy = (hash01(gs, 3) - 0.5) * 0.05                       # baseline wander
            gr = (hash01(gs, 4) - 0.5) * 4.0                         # per-letter tilt (deg)
            gsz = 1.0 + (hash01(gs, 5) - 0.5) * 0.08
            gca, gsa = math.cos(math.radians(gr)), math.sin(math.radians(gr))
            for j, st in enumerate(ss):
                pts = _densify(st, step / em)
                q = []
                for k, (px, py) in enumerate(pts):
                    jx = wob * noise1(k * 0.35 + j * 3.1, gs + 11, 1)
                    jy = wob * noise1(k * 0.35 + j * 2.3, gs + 13, 1)
                    lx, ly = (px - w / 2) * gsz, (py - 0.5) * gsz
                    lx, ly = lx * gca - ly * gsa, lx * gsa + ly * gca
                    lx += w / 2 + jx; ly += 0.5 + jy + dy
                    X = (cx + lx + slant * (1 - ly)) * em
                    Y = (ly - 1.0) * em
                    q.append((x0 + X * ca - Y * sa, y + X * sa + Y * ca))
                strokes.append(q)
            cx += w + track
        self.strokes = [s_ for s_ in strokes if len(s_) >= 2]
        self.lens = [sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(st[:-1], st[1:])) for st in self.strokes]
        self.lift = em * 0.35                                         # pen-lift travel counted between strokes
        self.length = sum(self.lens) + self.lift * max(0, len(self.strokes) - 1)
        xs = [p[0] for st in self.strokes for p in st] or [x]; ys = [p[1] for st in self.strokes for p in st] or [y]
        self.box = (min(xs), min(ys), max(xs), max(ys))
        self.width = total

    def partial(self, u):
        if u >= 1.0: return [list(st) for st in self.strokes]
        L = clamp(u) * self.length
        out = []
        for st, ln in zip(self.strokes, self.lens):
            if L <= 0: break
            if L >= ln:
                out.append(list(st)); L -= ln + self.lift; continue
            acc, q = 0.0, [st[0]]
            for a, b in zip(st[:-1], st[1:]):
                d = math.hypot(b[0] - a[0], b[1] - a[1])
                if acc + d >= L:
                    k = (L - acc) / max(1e-6, d); q.append((a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)); break
                q.append(b); acc += d
            out.append(q); L = 0
        return out

    def tip(self, u):
        parts = self.partial(u)
        if not parts: return (self.strokes[0][0][0], self.strokes[0][0][1], 0.0) if self.strokes else (0, 0, 0)
        q = parts[-1]
        if len(q) >= 2:
            a, b = q[-2], q[-1]; ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        else:
            ang = 0.0
        return (q[-1][0], q[-1][1], ang)


# ------------------------------------------------------------------ materials
def _pl(pts):
    return poly(pts, False)


def offset_pts(pts, d):
    """The polyline shifted by d along its left normal (per point, averaged over the neighbouring segments)."""
    n = len(pts); out = []
    for i in range(n):
        a_ = pts[max(0, i - 1)]; b_ = pts[min(n - 1, i + 1)]
        dx, dy = b_[0] - a_[0], b_[1] - a_[1]; L = math.hypot(dx, dy) or 1.0
        out.append((pts[i][0] - dy / L * d, pts[i][1] + dx / L * d))
    return out


_DASH = {}


def _dash(on, off, phase=0.0):
    k = (round(on, 1), round(off, 1), round(phase, 1))
    if k not in _DASH: _DASH[k] = skia.DashPathEffect.Make([max(0.5, on), max(0.5, off)], phase)
    return _DASH[k]


def wax(pen, pts, w, a=1.0, glow=0.0, seed=0, crumbs=True, core=None):
    """One waxy lipstick stroke as it lies on glass: a thin translucent dark rim, a flat body with drag streaks along the
    stroke (wax skips and builds up), a broken sheen line, crumbs."""
    if len(pts) < 2 or a <= 0: return
    cv = pen.cv
    p = _pl(pts)
    if glow > 0:
        cv.drawPath(p, paint(LIP_GLOW, 70 * glow * a, w * 3.2, blur=w * 1.4))
    cv.drawPath(p, paint(LIP_DK, 165 * a, w * 1.12))
    body = core or mix(LIP_CORE, '#ff5a6e', 0.35 * glow)
    cv.drawPath(p, paint(body, 250 * a, w))
    for j, (off, c_, al, ww) in enumerate(((-0.30, mix(body, LIP_DK, 0.45), 120, 0.13), (-0.04, mix(body, '#ff8a98', 0.35), 95, 0.10),
                                            (0.22, mix(body, LIP_DK, 0.35), 110, 0.16), (0.36, mix(body, LIP_DK, 0.6), 90, 0.07))):
        sp = paint(c_, al * a, w * ww, cap='butt')
        sp.setPathEffect(_dash(w * (1.6 + 2.2 * hash01(j, seed + 31)), w * (0.35 + 0.7 * hash01(j, seed + 32)), w * hash01(j, seed + 33) * 3))
        cv.drawPath(_pl(offset_pts(pts, off * w)), sp)
    hp = paint(mix(LIP_HI, '#ffd0d6', 0.25 * glow), 165 * a, w * 0.16)
    hp.setPathEffect(_dash(w * 2.6, w * 1.1, w * hash01(seed, 34) * 4))
    cv.drawPath(_pl(offset_pts(pts, -0.24 * w)), hp)
    if crumbs:
        pc = skia.Path(); pd = skia.Path()
        n = len(pts)
        for i in range(0, n, 2):
            x, y = pts[i]
            if hash01(i, seed + 6) < 0.45: continue
            ox, oy = (hash01(i, seed + 3) - 0.5) * w * 1.7, (hash01(i, seed + 4) - 0.5) * w * 1.6
            r = w * (0.05 + 0.09 * hash01(i, seed + 5))
            (pc if hash01(i, seed + 7) < 0.6 else pd).addOval(skia.Rect.MakeLTRB(x + ox - r, y + oy - r, x + ox + r, y + oy + r))
        cv.drawPath(pc, paint(LIP_DK, 220 * a)); cv.drawPath(pd, paint(LIP, 220 * a))


def marker_line(pen, pts, w, a=1.0, c=MARKER):
    if len(pts) < 2 or a <= 0: return
    p = _pl(pts)
    pen.cv.drawPath(p, paint(c, 45 * a, w * 1.35))
    pen.cv.drawPath(p, paint(c, 235 * a, w))


_CHALK_FX = {}


def _chalk_pe(seg, dev, seed):
    k = (round(seg, 1), round(dev, 1), seed)
    if k not in _CHALK_FX:
        _CHALK_FX[k] = skia.DiscretePathEffect.Make(seg, dev, seed)
    return _CHALK_FX[k]


def chalk_line(pen, pts, w, a=1.0, seed=0, c=CHALK, dash=None, closed=False):
    """Grainy chalk: three jagged passes (discrete path effect) of falling width plus a soft core."""
    if len(pts) < 2 or a <= 0: return
    p = poly(pts, closed)
    cv = pen.cv
    if dash:                                                  # dashed chalk: jagged dashes
        ok = _dash(dash[0], dash[1])
        for k, (wk, ak) in enumerate(((w, 0.55), (w * 0.62, 0.8))):
            pp = paint(c, 255 * a * ak, wk, cap='round'); pp.setPathEffect(skia.PathEffect.MakeCompose(ok, _chalk_pe(w * 0.9, w * 0.18, seed + k)))
            cv.drawPath(p, pp)
        return
    for k, (wk, ak, dev) in enumerate(((w * 1.1, 0.30, 0.34), (w * 0.8, 0.55, 0.22), (w * 0.45, 0.85, 0.12))):
        pp = paint(c, 255 * a * ak, wk, cap='round')
        pp.setPathEffect(_chalk_pe(max(2.0, w * 0.8), w * dev, seed * 7 + k))
        cv.drawPath(p, pp)


def grease_line(pen, pts, w, a=1.0, c=GREASE, seed=0):
    if len(pts) < 2 or a <= 0: return
    p = _pl(pts)
    pen.cv.drawPath(p, paint('#000000', 90 * a, w * 1.6, blur=w * 0.6))
    pp = paint(c, 235 * a, w); pp.setPathEffect(_chalk_pe(max(2.0, w * 1.2), w * 0.10, seed))
    pen.cv.drawPath(p, pp)
    pen.cv.drawPath(_pl([(x - w * 0.08, y - w * 0.16) for x, y in pts]), paint('#ffffff', 90 * a, w * 0.3))


def _lipstick_tool(pen, x, y, ang, size, a=255):
    """The lipstick at the head of a stroke: an angled red bullet with a sheen, the gold tube behind it up and right."""
    cv = pen.cv
    cv.save(); cv.translate(x, y); cv.rotate(-38.0)
    s = size
    bullet = smooth([(-0.10 * s, 0.02 * s), (0.10 * s, -0.02 * s), (0.13 * s, -0.36 * s), (-0.13 * s, -0.36 * s), (-0.13 * s, -0.12 * s)], True, 0.5)
    tube = rrect(-0.15 * s, -0.95 * s, 0.30 * s, 0.6 * s, 0.03 * s)
    collar = rrect(-0.17 * s, -0.42 * s, 0.34 * s, 0.09 * s, 0.02 * s)
    cv.drawPath(tube, paint('#000000', 90 * a / 255, None, blur=0.08 * s))
    Pen(cv).linear(tube, -0.15 * s, 0, 0.15 * s, 0, [(0, '#8a6a2a'), (0.35, '#f6dc8a'), (0.6, '#c9a24a'), (1, '#6a4e1c')], a / 255)
    cv.drawPath(tube, paint('#3a2a10', a, max(1.0, 0.02 * s)))
    Pen(cv).linear(collar, -0.17 * s, 0, 0.17 * s, 0, [(0, '#5a4418'), (0.4, '#e6c870'), (1, '#4a3812')], a / 255)
    cv.drawPath(bullet, paint(LIP, a)); cv.drawPath(bullet, paint(LIP_DK, a, max(1.0, 0.02 * s)))
    cv.drawPath(_pl([(-0.06 * s, -0.32 * s), (-0.05 * s, -0.08 * s)]), paint('#ff9aa8', 0.7 * a, 0.03 * s))
    cv.restore()


def _chalk_tool(pen, x, y, size, a=255):
    cv = pen.cv
    cv.save(); cv.translate(x, y); cv.rotate(-30.0)
    s = size
    stick = rrect(-0.06 * s, -0.5 * s, 0.12 * s, 0.5 * s, 0.03 * s)
    cv.drawPath(stick, paint('#000000', 70 * a / 255, None, blur=0.05 * s))
    cv.drawPath(stick, paint('#f4f1e8', a)); cv.drawPath(stick, paint('#b9b4a6', a, max(1.0, 0.012 * s)))
    cv.restore()


def _pencil_tool(pen, x, y, size, a=255, c='#e8e2d2'):
    cv = pen.cv
    cv.save(); cv.translate(x, y); cv.rotate(-35.0)
    s = size
    body = rrect(-0.06 * s, -0.8 * s, 0.12 * s, 0.62 * s, 0.02 * s)
    cone = poly([(-0.06 * s, -0.18 * s), (0.06 * s, -0.18 * s), (0, 0)])
    cv.drawPath(body, paint('#000000', 70 * a / 255, None, blur=0.05 * s))
    cv.drawPath(body, paint('#d9c27a', a)); cv.drawPath(cone, paint('#e9d7b4', a)); cv.drawPath(poly([(-0.02 * s, -0.06 * s), (0.02 * s, -0.06 * s), (0, 0)]), paint(c, a))
    cv.drawPath(body, paint('#5a4a20', a, max(1.0, 0.012 * s)))
    cv.restore()


def write(pen, sc, material='lipstick', u=1.0, a=255, tip=True, glow=0.0, seed=0, w=None, c=None):
    """Draw Script sc written up to u (0..1) in a material; the writing tool rides the head while 0 < u < 1."""
    if u <= 0 or a <= 0: return
    parts = sc.partial(u)
    s = sc.size
    k = a / 255.0
    if material == 'lipstick':
        ww = w or s * 0.165
        for j, q in enumerate(parts): wax(pen, q, ww, k, glow, seed + j * 13)
    elif material == 'marker':
        ww = w or s * 0.12
        for q in parts: marker_line(pen, q, ww, k, c or MARKER)
    elif material == 'chalk':
        ww = w or s * 0.10
        for j, q in enumerate(parts): chalk_line(pen, q, ww, k, seed + j, c or CHALK)
    elif material == 'grease':
        ww = w or s * 0.12
        for j, q in enumerate(parts): grease_line(pen, q, ww, k, c or GREASE, seed + j)
    else:
        ww = w or s * 0.08
        for q in parts:
            pen.cv.drawPath(_pl(q), paint(c or '#ffffff', a, ww))
    if tip and 0.0 < u < 1.0:
        x, y, ang = sc.tip(u)
        if material == 'lipstick': _lipstick_tool(pen, x, y, ang, s * 1.25, a)
        elif material == 'chalk': _chalk_tool(pen, x, y, s * 1.1, a)
        elif material in ('grease', 'pencil'): _pencil_tool(pen, x, y, s * 1.3, a)


# ------------------------------------------------------------------ small vector helpers
def dotted(pen, pts, r, gap, c=CHALK, a=255, u=1.0):
    """Dots of radius r every `gap` design px along the polyline, up to fraction u of its length."""
    L = sum(math.hypot(b[0] - a_[0], b[1] - a_[1]) for a_, b in zip(pts[:-1], pts[1:]))
    n = int(L * clamp(u) / gap)
    p = skia.Path(); acc = 0.0; j = 0; target = 0.0
    for a_, b in zip(pts[:-1], pts[1:]):
        d = math.hypot(b[0] - a_[0], b[1] - a_[1])
        while j <= n and target <= acc + d:
            k = (target - acc) / max(1e-6, d)
            x, y = a_[0] + (b[0] - a_[0]) * k, a_[1] + (b[1] - a_[1]) * k
            p.addOval(skia.Rect.MakeLTRB(x - r, y - r, x + r, y + r))
            j += 1; target = j * gap
        acc += d
    pen.cv.drawPath(p, paint(c, a))


def arrow_head(pen, x, y, ang, size, c=CHALK, a=255, material='chalk', w=None):
    a1, a2 = math.radians(ang + 150), math.radians(ang - 150)
    p1 = (x + size * math.cos(a1), y + size * math.sin(a1)); p2 = (x + size * math.cos(a2), y + size * math.sin(a2))
    if material == 'chalk':
        chalk_line(pen, [p1, (x, y), p2], w or size * 0.28, a / 255.0, 5, c)
    else:
        pen.cv.drawPath(poly([p1, (x, y), p2], False), paint(c, a, w or size * 0.25))


def squiggle_ring(cx, cy, r, amp, n_teeth=28, phase=0.0, seed=0, jag=True):
    """A jagged (rattle) ring: radius modulated by a zigzag plus noise."""
    pts = []
    N = n_teeth * 2
    for i in range(N + 1):
        a = 2 * math.pi * i / N + phase
        z = (1 if i % 2 else -1) if jag else math.sin(i * 0.5)
        rr = r + amp * (0.6 * z + 0.4 * noise1(i * 0.7, seed, 1))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def ring_pts(cx, cy, r, n=72, a0=0.0, a1=360.0, sy=1.0):
    return [(cx + r * math.cos(math.radians(a)), cy + r * sy * math.sin(math.radians(a))) for a in np.linspace(a0, a1, n)]


def soft_shadow(cv, path, a=150, blur=14.0, dx=0.0, dy=6.0):
    q = skia.Path(path); q.offset(dx, dy)
    cv.drawPath(q, paint('#000000', a, None, blur=blur))
