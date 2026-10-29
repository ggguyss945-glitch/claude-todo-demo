"""A 2D cartoon renderer for Twistory long-form videos (skia).

Style rules (from measuring the reference frames):
- heavy dark ink outlines (about 8-10 px at 1080p on a close-up head), round joins, tapered inner lines
- flat fills with hard-edged cel shadows: the far side of the face, under hat brims, under the chin
- wide human heads with jaw and cheek bulge, huge round white eyes with tiny pupils that touch each other,
  a nose that grows out of the face (bridge line + tip + nostril wing), ears with an inner curve,
  thin wrinkle/fold lines, thick tapered eyebrows that make a V when angry
- small bodies, arms and legs as single thick ink lines, small round hands
Coordinates for a head are normalised: origin at the head centre, head height = 1, y down,
drawn facing screen-right; flip=-1 mirrors it.
"""
import math, os, random
import skia

INK = '#1d1512'


def col(h, a=255):
    h = h.lstrip('#')
    return skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def shade(h, k=0.78, warm=0.0):
    """Shadow tone: darker, a touch more saturated and warmer."""
    h = h.lstrip('#'); r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b = r * k + warm * 20, g * k * 0.97, b * k * 0.93
    return '#%02x%02x%02x' % tuple(max(0, min(255, int(v))) for v in (r, g, b))


# ------------------------------------------------------------------ paths
def smooth(pts, closed=True, k=1.0):
    p = skia.Path(); n = len(pts)
    p.moveTo(*pts[0])
    for i in range(n if closed else n - 1):
        p0 = pts[(i - 1) % n] if closed else pts[max(i - 1, 0)]
        p1, p2 = pts[i], pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if closed else pts[min(i + 2, n - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6 * k, p1[1] + (p2[1] - p0[1]) / 6 * k)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6 * k, p2[1] - (p3[1] - p1[1]) / 6 * k)
        p.cubicTo(*c1, *c2, *p2)
    if closed: p.close()
    return p


def sample(pts, closed=False, n=12):
    """Points along the Catmull-Rom curve (for brush strokes)."""
    out = []; m = len(pts)
    segs = m if closed else m - 1
    for i in range(segs):
        p0 = pts[(i - 1) % m] if closed else pts[max(i - 1, 0)]
        p1, p2 = pts[i], pts[(i + 1) % m]
        p3 = pts[(i + 2) % m] if closed else pts[min(i + 2, m - 1)]
        for j in range(n):
            t = j / n; t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
    if not closed: out.append(pts[-1])
    return out


def poly(pts, closed=True):
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    if closed: p.close()
    return p


def oval(cx, cy, rx, ry):
    p = skia.Path(); p.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry)); return p


def union(paths):
    out = paths[0]
    for q in paths[1:]: out = skia.Op(out, q, skia.PathOp.kUnion_PathOp)
    return out


def inter(a, b): return skia.Op(a, b, skia.PathOp.kIntersect_PathOp)


def minus(a, b): return skia.Op(a, b, skia.PathOp.kDifference_PathOp)


class Pen:
    """Draws into a canvas with the style's ink rules."""
    def __init__(self, cv, lw=8.0):
        self.cv, self.lw = cv, lw

    def fill(self, path, color, alpha=255):
        self.cv.drawPath(path, skia.Paint(Color=col(color, alpha), AntiAlias=True))

    def ink(self, path, w=None, color=INK, alpha=255):
        self.cv.drawPath(path, skia.Paint(Color=col(color, alpha), AntiAlias=True, Style=skia.Paint.kStroke_Style,
                                          StrokeWidth=w or self.lw, StrokeJoin=skia.Paint.kRound_Join, StrokeCap=skia.Paint.kRound_Cap))

    def shape(self, path, color, w=None):
        self.fill(path, color); self.ink(path, w)

    def brush(self, pts, w=None, taper=(0.15, 0.15), color=INK, closed=False, alpha=255, wobble=0.0, seed=0):
        """A tapered stroke as a filled outline: full width in the middle, thin at the ends."""
        w = w or self.lw
        P = sample(pts, closed, 10)
        rnd = random.Random(seed)
        n = len(P); L, R = [], []
        for i, (x, y) in enumerate(P):
            a, b = P[max(i - 1, 0)], P[min(i + 1, n - 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]; d = math.hypot(dx, dy) or 1
            nx, ny = -dy / d, dx / d
            t = i / (n - 1)
            k = 1.0
            if taper[0] and t < taper[0]: k = 0.25 + 0.75 * (t / taper[0])
            if taper[1] and t > 1 - taper[1]: k = min(k, 0.25 + 0.75 * ((1 - t) / taper[1]))
            k *= 1 + wobble * (rnd.random() - 0.5)
            h = w * k / 2
            L.append((x + nx * h, y + ny * h)); R.append((x - nx * h, y - ny * h))
        self.fill(poly(L + R[::-1]), color, alpha)

    def cel(self, clip, shadow_path, color, alpha=255):
        """Hard-edged shadow, kept inside the shape it falls on."""
        self.cv.save(); self.cv.clipPath(clip, doAntiAlias=True)
        self.fill(shadow_path, color, alpha)
        self.cv.restore()


def T(pts, cx, cy, s, flip=1):
    return [(cx + x * s * flip, cy + y * s) for x, y in pts]


# ------------------------------------------------------------------ text
def caption(cv, s, x, y, size, font_path, fill='#ffffff', outline=INK, align='center'):
    tf = skia.Typeface.MakeFromFile(font_path); f = skia.Font(tf, size)
    w = f.measureText(s); x0 = x - w / 2 if align == 'center' else x
    blob = skia.TextBlob.MakeFromString(s, f)
    cv.drawTextBlob(blob, x0, y, skia.Paint(Color=col(outline), AntiAlias=True, Style=skia.Paint.kStroke_Style,
                                            StrokeWidth=size * 0.17, StrokeJoin=skia.Paint.kRound_Join))
    cv.drawTextBlob(blob, x0, y, skia.Paint(Color=col(fill), AntiAlias=True))


# ------------------------------------------------------------------ heads
SKINS = {'light': '#f5c6a0', 'tan': '#e2a77b', 'brown': '#9a5f3d', 'dark': '#6b3f28'}
HEAD = [(0.0, -0.5), (0.22, -0.48), (0.37, -0.4), (0.44, -0.26), (0.46, -0.1), (0.475, 0.04), (0.455, 0.16), (0.41, 0.27),
        (0.33, 0.37), (0.2, 0.46), (0.04, 0.505), (-0.12, 0.49), (-0.27, 0.42), (-0.38, 0.3), (-0.45, 0.14), (-0.48, -0.04),
        (-0.47, -0.22), (-0.4, -0.38), (-0.24, -0.47)]
EAR = [(-0.43, -0.12), (-0.52, -0.17), (-0.59, -0.09), (-0.59, 0.04), (-0.53, 0.14), (-0.43, 0.15)]
EAR_IN = [(-0.47, -0.07), (-0.535, -0.07), (-0.545, 0.03), (-0.5, 0.09)]


class Face:
    """mood: neutral, angry, scared, worried, shout, smug. eyes: 'round' (men) or 'almond' (women)."""
    def __init__(self, skin='light', mood='neutral', look=(0.0, 0.0), eyes='round', moustache=None, beard=None, hair=None,
                 hair_style='side', folds=1, old=False, hat=None, female=False, iris='#5a3a22', width=1.0):
        self.__dict__.update(locals()); del self.__dict__['self']
        self.skin = SKINS.get(skin, skin)


def draw_head(pen, cx, cy, s, f, flip=1):
    """s = head height in px. Returns the head path (for clipping hats or shadows)."""
    lw = pen.lw
    P = lambda pts: T([(x * f.width, y) for x, y in pts], cx, cy, s, flip)
    sk, sh = f.skin, shade(f.skin, 0.8)
    if f.hat and getattr(f.hat, 'back', None): f.hat.back(pen, cx, cy, s, flip, f)
    if f.hair and f.hair_style in ('long', 'bob'):
        back = smooth(P([(-0.5, -0.2), (-0.56, 0.2), (-0.5, 0.52), (-0.2, 0.58), (0.3, 0.55), (0.5, 0.3), (0.5, -0.2), (0.2, -0.56), (-0.3, -0.56)]))
        pen.shape(back, f.hair)
    # ear and neck behind the head
    neck = smooth(P([(-0.2, 0.3), (0.18, 0.38), (0.2, 0.9), (-0.22, 0.9)]), True, 0.3)
    pen.shape(neck, sk)
    pen.cel(neck, poly(P([(-0.4, 0.3), (0.4, 0.3), (0.4, 0.62), (-0.4, 0.55)])), sh)
    ear = smooth(P(EAR)); pen.shape(ear, sk)
    pen.cel(ear, smooth(P([(-0.48, -0.05), (-0.55, -0.04), (-0.55, 0.06), (-0.5, 0.1)])), sh)
    pen.brush(P(EAR_IN), lw * 0.55, (0.3, 0.3))
    head = smooth(P(HEAD))
    pen.fill(head, sk)
    # cel shadow: the far side of the face, and a band under a hat brim
    pen.cel(head, smooth(P([(-0.7, -0.7), (-0.2, -0.7), (-0.27, -0.3), (-0.23, 0.0), (-0.28, 0.3), (-0.12, 0.6), (-0.7, 0.6)])), sh)
    if f.hat: pen.cel(head, smooth(P([(-0.7, -0.7), (0.7, -0.7), (0.7, -0.26), (0.2, -0.22), (-0.3, -0.24), (-0.7, -0.26)])), sh)
    if f.hair and f.hair_style == 'side' and f.hat:  # sideburn/back hair peeking under a hat
        pen.fill(inter(head, smooth(P([(-0.52, -0.42), (-0.28, -0.44), (-0.3, -0.2), (-0.36, 0.02), (-0.5, 0.0)]))), f.hair)
    pen.ink(head)
    # wrinkles for old faces
    if f.old:
        for pts in ([(-0.2, -0.36), (0.0, -0.39), (0.22, -0.36)], [(-0.12, -0.31), (0.08, -0.33)]):
            pen.brush(P(pts), lw * 0.45)
    # eyes
    sizes = [(-0.13, -0.05, 0.14), (0.17, -0.055, 0.155)]
    lid = {'angry': 0.42, 'smug': 0.5, 'neutral': 0.0, 'scared': 0.0, 'worried': 0.18, 'shout': 0.3}.get(f.mood, 0.0)
    big = 1.12 if f.mood == 'scared' else 1.0
    for i, (ex, ey, r) in enumerate(sizes):
        r *= big
        if f.eyes == 'almond': r *= 0.82
        X, Y = P([(ex, ey)])[0]; R = r * s * f.width
        ry = R * (0.72 if f.eyes == 'almond' else 1.0)
        eye = oval(X, Y, R, ry)
        cut = None
        if lid:  # brow/lid cuts the top of the eye; the cut slopes down toward the nose when angry
            inner = 1 if (ex > 0) == (flip > 0) else -1
            k = lid * 2 * R
            slope = 0.35 * R if f.mood in ('angry', 'shout') else (-0.25 * R if f.mood == 'worried' else 0)
            a, b = (X - R * 1.2, Y - R + k - slope * inner), (X + R * 1.2, Y - R + k + slope * inner)
            cut = poly([(a[0], a[1]), (b[0], b[1]), (b[0], Y + R * 2), (a[0], Y + R * 2)])
            eye = inter(eye, cut)
        pen.fill(eye, '#ffffff')
        px, py = X + f.look[0] * R * 0.45 * flip, Y + f.look[1] * ry * 0.45
        if f.eyes == 'almond':
            pen.cv.save(); pen.cv.clipPath(eye, doAntiAlias=True)
            pen.fill(oval(px, py, R * 0.42, R * 0.42), f.iris); pen.fill(oval(px, py, R * 0.2, R * 0.2), INK)
            pen.fill(oval(px - R * 0.12, py - R * 0.14, R * 0.08, R * 0.08), '#ffffff')
            pen.cv.restore()
        else:
            pen.fill(oval(px, py, s * 0.024, s * 0.024), INK)
        pen.ink(eye, lw * 0.95)
        if f.eyes == 'almond':  # heavy upper lid and a lash flick at the outer corner
            out = 1 if ex > 0 else -1
            pen.brush([(X - R * out, Y + ry * 0.1), (X - R * 0.3 * out, Y - ry * 1.0), (X + R * 0.6 * out, Y - ry * 0.9), (X + R * 1.15 * out, Y - ry * 0.55)], lw * 1.6, (0.3, 0.05))
    # eyebrows
    B = {'neutral': ([(-0.27, -0.25), (-0.14, -0.28), (-0.03, -0.25)], [(0.04, -0.26), (0.18, -0.3), (0.32, -0.27)]),
         'angry': ([(-0.29, -0.26), (-0.15, -0.21), (-0.02, -0.13)], [(0.03, -0.13), (0.17, -0.22), (0.33, -0.29)]),
         'shout': ([(-0.29, -0.24), (-0.15, -0.19), (-0.02, -0.12)], [(0.03, -0.12), (0.17, -0.2), (0.33, -0.27)]),
         'scared': ([(-0.27, -0.27), (-0.15, -0.33), (-0.04, -0.33)], [(0.05, -0.34), (0.18, -0.35), (0.31, -0.29)]),
         'worried': ([(-0.27, -0.2), (-0.15, -0.24), (-0.03, -0.29)], [(0.04, -0.3), (0.17, -0.25), (0.31, -0.21)]),
         'smug': ([(-0.27, -0.2), (-0.14, -0.22), (-0.03, -0.2)], [(0.04, -0.23), (0.18, -0.3), (0.32, -0.28)])}[f.mood]
    bw = lw * (1.9 if not f.female else 1.3)
    for b in B: pen.brush(P(b), bw, (0.05, 0.45))
    if f.mood in ('angry', 'shout'):  # frown creases between the brows
        pen.brush(P([(-0.03, -0.19), (0.0, -0.25), (-0.01, -0.31)]), lw * 0.5, (0.3, 0.3))
        pen.brush(P([(0.03, -0.2), (0.07, -0.27)]), lw * 0.45, (0.3, 0.3))
    # nose: bridge on the near side, round tip, nostril wing
    nose = smooth(P([(0.03, 0.0), (0.12, 0.06), (0.2, 0.13), (0.225, 0.19), (0.18, 0.23), (0.1, 0.225), (0.045, 0.2), (0.035, 0.15), (0.06, 0.12), (0.02, 0.06)]))
    pen.fill(nose, sk)
    pen.cel(nose, smooth(P([(0.0, 0.1), (0.1, 0.17), (0.2, 0.21), (0.14, 0.3), (0.0, 0.3)])), sh)
    pen.brush(P([(0.07, 0.02), (0.15, 0.08), (0.205, 0.135), (0.225, 0.19), (0.19, 0.23), (0.11, 0.228)]), lw, (0.25, 0.1))
    pen.brush(P([(0.11, 0.228), (0.05, 0.205), (0.04, 0.155), (0.075, 0.125)]), lw * 0.9, (0.05, 0.35))
    # folds
    if f.folds:
        pen.brush(P([(0.03, 0.19), (-0.03, 0.27), (-0.03, 0.34)]), lw * 0.55, (0.2, 0.5))
        pen.brush(P([(0.235, 0.24), (0.29, 0.3), (0.29, 0.36)]), lw * 0.5, (0.2, 0.5))
    if f.old:
        pen.brush(P([(-0.24, 0.07), (-0.14, 0.1), (-0.05, 0.08)]), lw * 0.45, (0.3, 0.3))
        pen.brush(P([(0.07, 0.08), (0.18, 0.11), (0.3, 0.08)]), lw * 0.45, (0.3, 0.3))
    # mouth
    if f.mood == 'shout':
        m = smooth(P([(0.0, 0.33), (0.12, 0.31), (0.26, 0.33), (0.22, 0.43), (0.1, 0.45), (0.02, 0.41)]))
        pen.fill(m, '#3a1612')
        pen.cv.save(); pen.cv.clipPath(m, doAntiAlias=True)
        pen.fill(poly(P([(-0.1, 0.2), (0.4, 0.2), (0.4, 0.355), (-0.1, 0.36)])), '#ffffff')
        pen.fill(oval(*P([(0.13, 0.46)])[0], 0.08 * s, 0.04 * s), '#c0504a')
        pen.cv.restore(); pen.ink(m)
    else:
        M = {'neutral': [(0.04, 0.37), (0.13, 0.375), (0.22, 0.365)], 'angry': [(0.03, 0.385), (0.13, 0.36), (0.23, 0.385)],
             'scared': [(0.05, 0.38), (0.13, 0.36), (0.21, 0.385)], 'worried': [(0.04, 0.385), (0.13, 0.37), (0.22, 0.39)],
             'smug': [(0.03, 0.37), (0.15, 0.38), (0.25, 0.34)]}[f.mood]
        if f.female:
            lips = smooth(P([(M[0][0], M[0][1]), (0.13, M[1][1] - 0.025), (M[2][0], M[2][1]), (0.13, M[1][1] + 0.035)]))
            pen.fill(lips, shade(sk, 0.86))
        pen.brush(P(M), lw * 0.85, (0.3, 0.3))
        if f.mood == 'angry':
            pen.brush(P([(0.07, 0.44), (0.14, 0.445)]), lw * 0.45, (0.3, 0.3))
    if f.moustache:
        R_ = [(0.13, 0.235), (0.22, 0.228), (0.31, 0.248), (0.39, 0.238), (0.445, 0.19), (0.475, 0.205), (0.455, 0.27), (0.38, 0.315), (0.26, 0.325), (0.13, 0.305)]
        L_ = [(0.13 - (x - 0.13) * 0.78, y) for x, y in R_]
        mo = smooth(P(R_ + L_[::-1][1:-1]))
        pen.shape(mo, f.moustache, lw * 0.9)
        pen.cel(mo, poly(P([(-0.3, 0.29), (0.6, 0.29), (0.6, 0.5), (-0.3, 0.5)])), shade(f.moustache, 0.82))
        pen.ink(mo, lw * 0.9)
        for a, b in [((0.02, 0.27), (0.08, 0.3)), ((0.25, 0.27), (0.31, 0.3))]: pen.brush(P([a, b]), lw * 0.35)
    if f.beard:
        # bristly lower edge from ear to ear around the chin, smooth upper edge along the cheeks and under the nose
        rnd = random.Random(int(cx))
        low = []
        for i in range(31):
            t = i / 30; a = math.pi * (1.0 - t)          # left ear -> chin -> right ear
            r = 1.0 + (0.07 if i % 2 else 0.0) + rnd.uniform(-0.015, 0.015)
            low.append((math.cos(a) * 0.47 * r + 0.01, 0.06 + math.sin(a) * 0.5 * r))
        top = [(0.45, 0.1), (0.38, 0.2), (0.3, 0.29), (0.21, 0.285), (0.13, 0.262), (0.05, 0.28), (-0.05, 0.25), (-0.2, 0.19), (-0.36, 0.13), (-0.47, 0.09)]
        bd = poly(P(low + top))
        bd = skia.Op(bd, union([smooth(P([(-0.46, 0.0), (0.46, 0.0), (0.46, 0.7), (-0.46, 0.7)]))]), skia.PathOp.kIntersect_PathOp)
        hole = smooth(P([(0.03, 0.34), (0.13, 0.325), (0.24, 0.34), (0.13, 0.39)]))
        if f.mood == 'shout': hole = smooth(P([(0.0, 0.33), (0.12, 0.31), (0.26, 0.33), (0.22, 0.43), (0.1, 0.45), (0.02, 0.41)]))
        bd = minus(bd, hole)
        pen.fill(bd, f.beard)
        pen.cel(bd, smooth(P([(-0.7, 0.0), (-0.2, 0.1), (-0.15, 0.7), (-0.7, 0.7)])), shade(f.beard, 0.75))
        rs = random.Random(5)
        pen.cv.save(); pen.cv.clipPath(bd, doAntiAlias=True)
        for _ in range(70):  # hair texture
            x, y = rs.uniform(-0.45, 0.45), rs.uniform(0.1, 0.55)
            pen.brush(P([(x, y), (x + 0.01, y + 0.04)]), lw * 0.35, (0.4, 0.4), shade(f.beard, 0.6))
        pen.cv.restore()
        pen.ink(bd, lw * 0.9)
        if f.mood == 'shout': pen.ink(hole)
    if f.hair and f.hair_style in ('top', 'long', 'bob'):
        top = smooth(P([(-0.48, -0.08), (-0.5, -0.36), (-0.32, -0.55), (0.0, -0.6), (0.3, -0.55), (0.47, -0.38), (0.47, -0.2),
                        (0.36, -0.33), (0.12, -0.38), (-0.1, -0.34), (-0.3, -0.26), (-0.4, -0.08)]))
        pen.shape(top, f.hair)
        pen.cel(top, smooth(P([(-0.1, -0.7), (0.6, -0.7), (0.6, -0.3), (0.2, -0.42)])), '#ffffff', 50)
        pen.brush(P([(-0.2, -0.5), (0.1, -0.52), (0.3, -0.46)]), lw * 0.5, (0.3, 0.3), shade(f.hair, 0.6))
        pen.ink(top)
    if f.hat: f.hat.front(pen, cx, cy, s, flip, f)
    return head


# ------------------------------------------------------------------ hats (normalised to the head, drawn facing right)
class Hat:
    def __init__(self, color, kind, trim='#e3b33c', band=None):
        self.color, self.kind, self.trim, self.band = color, kind, trim, band
    back = None

    def front(self, pen, cx, cy, s, flip, f):
        P = lambda pts: T(pts, cx, cy, s, flip)
        c, sh, lw = self.color, shade(self.color, 0.74), pen.lw
        if self.kind == 'kepi':
            crown = smooth(P([(-0.47, -0.27), (-0.47, -0.55), (-0.36, -0.68), (0.02, -0.82), (0.33, -0.78), (0.45, -0.6), (0.47, -0.27)]), True, 0.7)
            pen.fill(crown, c); pen.cel(crown, smooth(P([(-0.7, -0.9), (-0.2, -0.9), (-0.16, -0.5), (-0.24, -0.2), (-0.7, -0.2)])), sh)
            band = poly(P([(-0.48, -0.37), (0.48, -0.37), (0.48, -0.26), (-0.48, -0.26)]))
            pen.fill(inter(band, crown), shade(c, 0.6)); pen.ink(crown)
            pen.brush(P([(-0.47, -0.37), (0.0, -0.375), (0.47, -0.37)]), lw * 0.6, (0.1, 0.1))
            visor = smooth(P([(0.05, -0.3), (0.3, -0.31), (0.6, -0.24), (0.66, -0.17), (0.4, -0.19), (0.1, -0.23)]), True, 0.6)
            pen.shape(visor, '#24201f'); pen.cel(visor, poly(P([(0.2, -0.3), (0.62, -0.25), (0.6, -0.27), (0.2, -0.32)])), '#5a5452')
            badge = oval(*P([(0.16, -0.5)])[0], 0.07 * s, 0.05 * s); pen.shape(badge, self.trim, lw * 0.6)
        elif self.kind == 'shako':
            body = smooth(P([(-0.4, -0.27), (-0.34, -0.95), (0.3, -1.0), (0.42, -0.27)]), True, 0.25)
            pen.fill(body, c); pen.cel(body, poly(P([(-0.7, -1.2), (-0.12, -1.2), (-0.1, -0.2), (-0.7, -0.2)])), sh); pen.ink(body)
            top = smooth(P([(-0.34, -0.95), (-0.02, -1.03), (0.3, -1.0), (-0.02, -0.92)])); pen.shape(top, shade(c, 0.6), lw * 0.8)
            pen.shape(oval(*P([(0.0, -1.06)])[0], 0.08 * s, 0.07 * s), '#f2efe8', lw * 0.7)
            plate = smooth(P([(0.0, -0.78), (0.14, -0.66), (0.1, -0.48), (-0.06, -0.47), (-0.12, -0.64)])); pen.shape(plate, self.trim, lw * 0.6)
            peak = smooth(P([(0.0, -0.3), (0.42, -0.31), (0.6, -0.22), (0.3, -0.19), (0.02, -0.24)]), True, 0.6); pen.shape(peak, '#1d1a1a')
            pen.brush(P([(-0.42, -0.25), (-0.38, 0.05), (-0.1, 0.42), (0.18, 0.47)]), lw * 0.9, (0.0, 0.0), '#2a2520')  # chin strap
        elif self.kind == 'tophat':
            body = smooth(P([(-0.32, -0.35), (-0.35, -1.12), (0.33, -1.15), (0.31, -0.35)]), True, 0.2)
            pen.fill(body, c); pen.cel(body, poly(P([(-0.7, -1.3), (-0.1, -1.3), (-0.08, -0.2), (-0.7, -0.2)])), sh)
            pen.fill(inter(body, poly(P([(-0.5, -0.52), (0.5, -0.52), (0.5, -0.38), (-0.5, -0.38)]))), self.band or '#3a2e2a'); pen.ink(body)
            pen.cel(body, poly(P([(0.08, -1.1), (0.15, -1.1), (0.15, -0.55), (0.08, -0.55)])), '#ffffff', 60)
            brim = smooth(P([(-0.56, -0.36), (-0.3, -0.42), (0.3, -0.43), (0.58, -0.38), (0.5, -0.27), (0.0, -0.25), (-0.5, -0.28)]), True, 0.6)
            pen.shape(brim, c); pen.cel(brim, poly(P([(-0.7, -0.33), (0.7, -0.34), (0.7, -0.2), (-0.7, -0.2)])), sh); pen.ink(brim)
        elif self.kind == 'straw':
            crown = smooth(P([(-0.4, -0.36), (-0.38, -0.7), (-0.14, -0.84), (0.16, -0.84), (0.38, -0.72), (0.42, -0.36)]), True, 0.7)
            brim = smooth(P([(-0.8, -0.34), (-0.5, -0.44), (0.0, -0.46), (0.5, -0.45), (0.82, -0.36), (0.6, -0.26), (0.0, -0.22), (-0.6, -0.25)]), True, 0.7)
            pen.fill(crown, c); pen.cel(crown, smooth(P([(-0.7, -1.0), (-0.12, -1.0), (-0.1, -0.3), (-0.7, -0.3)])), sh); pen.ink(crown)
            pen.brush(P([(-0.05, -0.83), (0.0, -0.74), (0.06, -0.83)]), lw * 0.5, (0.3, 0.3))
            band = inter(crown, poly(P([(-0.5, -0.5), (0.5, -0.5), (0.5, -0.38), (-0.5, -0.38)])))
            pen.fill(band, self.band or '#7a3a26'); pen.ink(band, lw * 0.7)
            pen.fill(brim, c); pen.cel(brim, smooth(P([(-0.9, -0.3), (0.9, -0.3), (0.9, -0.1), (-0.9, -0.1)])), sh); pen.ink(brim)
            for i in range(9):
                x = -0.62 + i * 0.155
                pen.brush(P([(x, -0.37), (x * 1.08, -0.29)]), lw * 0.32, (0.3, 0.3), shade(c, 0.6))


# ------------------------------------------------------------------ bodies
def figure(pen, cx, foot_y, s, face, coat, flip=1, pants='#2c2a33', arms=None, legs=True, details=None, collar=None, ammo=False):
    """Full figure: head s px tall, total height about 2.8 heads. arms: dict side -> list of points (head units, relative to the
    shoulder line) or None for hanging arms. Returns hand positions."""
    lw = pen.lw
    hy = foot_y - s * 2.3                     # head centre
    sy = hy + s * 0.62                        # shoulder line
    P = lambda pts: T(pts, cx, sy, s, flip)
    hip = foot_y - s * 0.9
    if legs:
        for dx in (-0.14, 0.14):
            x = cx + dx * s * flip
            pen.brush([(x, hip - s * 0.1), (x + dx * s * 0.15, foot_y - s * 0.04)], lw * 1.05, (0.0, 0.0))
            pen.shape(oval(x + dx * s * 0.15 + 0.05 * s * flip, foot_y - s * 0.02, 0.11 * s, 0.05 * s), '#1e1a19', lw * 0.8)
    torso = smooth(P([(-0.3, 0.0), (0.0, -0.04), (0.3, 0.0), (0.36, 0.5), (0.36, (hip - sy) / s + 0.04), (-0.36, (hip - sy) / s + 0.04), (-0.36, 0.5)]), True, 0.5)
    pen.fill(torso, coat)
    pen.cel(torso, smooth(P([(-0.6, -0.2), (-0.12, -0.2), (-0.16, 0.5), (-0.1, 1.6), (-0.6, 1.6)])), shade(coat, 0.75))
    if details: details(pen, P, s, flip, torso)
    pen.ink(torso)
    if collar: pen.shape(smooth(P([(-0.16, -0.02), (0.0, 0.14), (0.17, -0.02), (0.0, 0.03)])), collar, lw * 0.8)
    hands = {}
    for side, sx in (('far', -0.3), ('near', 0.3)):
        path = (arms or {}).get(side) or [(sx, 0.08), (sx * 1.35, 0.5), (sx * 1.2, 0.9)]
        pts = P(path)
        pen.brush(pts, lw * 1.05, (0.0, 0.0))
        hands[side] = pts[-1]
    draw_head(pen, cx, hy, s, face, flip)
    return hands


def hand(pen, x, y, s, skin):
    pen.shape(oval(x, y, 0.075 * s, 0.07 * s), SKINS.get(skin, skin), pen.lw * 0.8)


def rifle(pen, a, b, s):
    """Wooden stock from a to most of the way, dark steel barrel to b."""
    k = 0.62
    m = (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)
    pen.brush([a, m], s * 0.075, (0.0, 0.0), INK); pen.brush([a, m], s * 0.075 - pen.lw * 1.2, (0.0, 0.0), '#8a4a22')
    pen.brush([m, b], s * 0.032, (0.0, 0.0), INK); pen.brush([m, b], max(2, s * 0.032 - pen.lw), (0.0, 0.0), '#55555e')


# ------------------------------------------------------------------ the pig (a black Berkshire)
def pig(pen, cx, cy, s, flip=1, mood='neutral', chewing=True):
    lw = pen.lw
    P = lambda pts: T(pts, cx, cy, s, flip)
    base, sh = '#34303a', '#221f27'
    for dx in (-0.36, -0.2, 0.2, 0.34):
        pen.shape(smooth(P([(dx - 0.07, 0.15), (dx + 0.07, 0.15), (dx + 0.07, 0.47), (dx - 0.07, 0.47)]), True, 0.3), base)
        pen.shape(poly(P([(dx - 0.07, 0.42), (dx + 0.07, 0.42), (dx + 0.07, 0.48), (dx - 0.07, 0.48)])), '#f0b4bd', lw * 0.6)
    pen.brush(P([(-0.55, -0.06), (-0.67, -0.14), (-0.62, -0.24), (-0.71, -0.27)]), lw * 0.9, (0.0, 0.3))
    body = smooth(P([(-0.56, -0.05), (-0.42, -0.33), (0.0, -0.4), (0.4, -0.3), (0.55, -0.08), (0.5, 0.2), (0.2, 0.3), (-0.3, 0.3), (-0.56, 0.15)]))
    pen.fill(body, base)
    pen.cel(body, smooth(P([(-0.7, 0.08), (0.7, 0.1), (0.7, 0.5), (-0.7, 0.5)])), sh)
    pen.cel(body, smooth(P([(-0.35, -0.08), (-0.2, -0.04), (-0.18, 0.2), (-0.4, 0.22)])), '#f3efe9')  # white patch
    pen.cel(body, smooth(P([(-0.2, -0.36), (0.3, -0.33), (0.2, -0.27), (-0.15, -0.29)])), '#6a6475')  # rim light
    pen.ink(body)
    hd = smooth(P([(0.3, -0.34), (0.6, -0.44), (0.84, -0.27), (0.9, 0.02), (0.68, 0.18), (0.38, 0.12)]))
    for ex in (0.48, 0.68):
        pen.shape(smooth(P([(ex - 0.08, -0.32), (ex + 0.01, -0.56), (ex + 0.1, -0.3)]), True, 0.3), base)
    pen.fill(hd, base); pen.cel(hd, smooth(P([(0.2, 0.0), (1.0, 0.04), (1.0, 0.3), (0.2, 0.3)])), sh); pen.ink(hd)
    sn = oval(*P([(0.92, -0.03)])[0], 0.115 * s, 0.1 * s); pen.shape(sn, '#f2a3b0')
    for d in (-0.04, 0.035): pen.fill(oval(*P([(0.92 + d, -0.03)])[0], 0.018 * s, 0.03 * s), '#7a2a3c')
    for ex, r in [(0.6, 0.085), (0.76, 0.095)]:
        e = oval(*P([(ex, -0.2)])[0], r * s, r * s); pen.shape(e, '#ffffff', lw * 0.85)
        pen.fill(oval(*P([(ex + 0.03, -0.18)])[0], 0.02 * s, 0.02 * s), INK)
    if chewing:
        pot = oval(*P([(0.88, 0.12)])[0], 0.12 * s, 0.075 * s); pen.shape(pot, '#c99350', lw * 0.8)
        pen.cel(pot, oval(*P([(0.86, 0.17)])[0], 0.12 * s, 0.05 * s), '#a87438')


# ------------------------------------------------------------------ painted backgrounds
def sky(pen, W, y1, top='#3e9ae6', bottom='#bfe3fb', seed=1, clouds=4):
    cv = pen.cv; rnd = random.Random(seed)
    cv.drawRect(skia.Rect.MakeWH(W, y1), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 0), (0, y1)], [col(top), col(bottom)])))
    for _ in range(clouds):  # cartoon cumulus: lumpy white with a soft blue-grey underside
        cx, cy, w = rnd.uniform(0, W), rnd.uniform(y1 * 0.12, y1 * 0.6), rnd.uniform(160, 340)
        balls = [(cx + (i - 2.5) * w * 0.17, cy - math.sin(i / 5 * math.pi) * w * 0.12, w * rnd.uniform(0.12, 0.2)) for i in range(6)]
        balls += [(cx + (i - 2) * w * 0.2, cy + w * 0.06, w * 0.13) for i in range(5)]
        c = union([oval(x, y, r, r * 0.85) for x, y, r in balls])
        c = inter(c, poly([(cx - w, cy - w), (cx + w, cy - w), (cx + w, cy + w * 0.14), (cx - w, cy + w * 0.14)]))
        pen.fill(c, '#ffffff')
        pen.cel(c, poly([(cx - w, cy + w * 0.02), (cx + w, cy + w * 0.02), (cx + w, cy + w), (cx - w, cy + w)]), '#d6e6f3')


def bush(pen, cx, cy, s, seed, base='#46b23c', dark='#2a8a32', light='#9ee05a'):
    rnd = random.Random(seed)
    balls = [(cx + rnd.uniform(-1, 1) * s * 1.1, cy + rnd.uniform(-0.45, 0.3) * s, s * rnd.uniform(0.38, 0.6)) for _ in range(10)]
    balls += [(cx + (i - 3) * s * 0.38, cy + s * 0.5, s * 0.5) for i in range(7)]
    shape = union([oval(x, y, r, r * 0.92) for x, y, r in balls])
    pen.fill(shape, base)
    cv = pen.cv; cv.save(); cv.clipPath(shape, doAntiAlias=True)
    for x, y, r in sorted(balls, key=lambda b: b[1]):  # leaf clumps: dark underside, lit top, scribble highlights
        pen.fill(oval(x + r * 0.1, y + r * 0.35, r * 0.95, r * 0.75), dark)
        pen.fill(oval(x - r * 0.1, y - r * 0.12, r * 0.8, r * 0.7), base)
        for _ in range(9):
            a = rnd.uniform(math.pi * 1.1, math.pi * 1.9); rr = r * rnd.uniform(0.3, 0.7)
            px, py = x - r * 0.1 + math.cos(a) * rr, y - r * 0.12 + math.sin(a) * rr
            pen.brush([(px, py), (px + rnd.uniform(6, 14), py - rnd.uniform(4, 9)), (px + rnd.uniform(12, 22), py)], pen.lw * 0.5, (0.3, 0.3), light)
        pen.brush([(x - r * 0.75, y + r * 0.2), (x - r * 0.2, y + r * 0.62), (x + r * 0.6, y + r * 0.45)], pen.lw * 0.55, (0.3, 0.3), shade(dark, 0.7))
    cv.restore()
    pen.ink(shape)


def water(pen, W, y0, y1, seed=3, color='#25c4d8'):
    rnd = random.Random(seed)
    pen.fill(poly([(0, y0), (W, y0), (W, y1), (0, y1)]), color)
    for i in range(int((y1 - y0) / 34)):
        y = y0 + 22 + i * 34
        x = rnd.uniform(-200, 0)
        while x < W:
            L = rnd.uniform(160, 420)
            pts = [(x + L * t, y + math.sin(t * math.pi * 2 + i) * 5) for t in (0, 0.25, 0.5, 0.75, 1)]
            pen.brush(pts, pen.lw * 0.55, (0.3, 0.3), '#ffffff', alpha=230)
            x += L + rnd.uniform(60, 200)
