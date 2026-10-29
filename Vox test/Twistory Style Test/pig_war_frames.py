"""Style test for long-form Twistory videos: three 1920x1080 frames of "The Pig War" (1859),
drawn in the flat cartoon look of the reference channel (thick ink outlines, flat colours,
big white eyes with small pupils, stubble, stick legs, painted skies and bushes, flat maps).
    python3 pig_war_frames.py <fonts dir> <out dir>
"""
import math, os, random, sys
import skia

FONTS, OUT = sys.argv[1], sys.argv[2]
W, H = 1920, 1080
INK = '#17120f'


def col(h, a=255):
    h = h.lstrip('#')
    return skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def smooth(pts, closed=True, k=1.0):
    """Catmull-Rom through the points, as cubic Beziers."""
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


def fillp(cv, path, color, lw=5.0, alpha=255):
    cv.drawPath(path, skia.Paint(Color=col(color, alpha), AntiAlias=True))
    if lw: stroke(cv, path, lw)


def stroke(cv, path, lw=5.0, color=INK, alpha=255):
    cv.drawPath(path, skia.Paint(Color=col(color, alpha), AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=lw,
                                 StrokeJoin=skia.Paint.kRound_Join, StrokeCap=skia.Paint.kRound_Cap))


def line(cv, pts, lw=5.0, color=INK, alpha=255):
    stroke(cv, smooth(pts, False) if len(pts) > 2 else poly(pts, False), lw, color, alpha)


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


def T(pts, cx, cy, s, flip=1):
    return [(cx + x * s * flip, cy + y * s) for x, y in pts]


def text(cv, s, x, y, size, fill='#ffffff', outline=INK, ow=None, font='LilitaOne.ttf', align='center'):
    tf = skia.Typeface.MakeFromFile(os.path.join(FONTS, font)); f = skia.Font(tf, size)
    w = f.measureText(s)
    x0 = x - w / 2 if align == 'center' else x
    blob = skia.TextBlob.MakeFromString(s, f)
    ow = ow or size * 0.16
    cv.drawTextBlob(blob, x0 + size * 0.05, y + size * 0.08, skia.Paint(Color=col('#000000', 110), AntiAlias=True,
                    MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, size * 0.05)))
    cv.drawTextBlob(blob, x0, y, skia.Paint(Color=col(outline), AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=ow, StrokeJoin=skia.Paint.kRound_Join))
    cv.drawTextBlob(blob, x0, y, skia.Paint(Color=col(fill), AntiAlias=True))


# ------------------------------------------------------------------ painted backgrounds
def sky(cv, top='#2f97e6', bottom='#a9dcf8', seed=1, y1=H):
    rnd = random.Random(seed)
    cv.drawRect(skia.Rect.MakeWH(W, y1), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 0), (0, y1)], [col(top), col(bottom)])))
    # clouds: a few soft masses built from wide, curved dry-brush strokes
    centres = [(rnd.uniform(0, W), rnd.uniform(y1 * 0.1, y1 * 0.75), rnd.uniform(160, 360)) for _ in range(5)]
    for cx, cy, R in centres:
        for _ in range(int(R * 1.3)):
            a = rnd.uniform(0, math.tau); d = R * math.sqrt(rnd.random())
            x, y = cx + math.cos(a) * d * 1.6, cy + math.sin(a) * d * 0.45
            L, ang = rnd.uniform(30, 120), rnd.uniform(-0.32, -0.12)
            k = 1 - d / R
            p = skia.Paint(Color=col('#ffffff', int(40 + 150 * k * rnd.random())), AntiAlias=True, StrokeWidth=rnd.uniform(6, 26),
                           Style=skia.Paint.kStroke_Style, StrokeCap=skia.Paint.kRound_Cap)
            path = skia.Path(); path.moveTo(x, y)
            path.quadTo(x + L * 0.5 * math.cos(ang), y + L * 0.5 * math.sin(ang) - rnd.uniform(2, 10), x + L * math.cos(ang), y + L * math.sin(ang))
            cv.drawPath(path, p)
    for _ in range(2500):  # speckle, like a textured brush
        x, y = rnd.uniform(0, W), rnd.uniform(0, y1)
        cv.drawCircle(x, y, rnd.uniform(0.8, 2.6), skia.Paint(Color=col('#ffffff', int(rnd.uniform(30, 120))), AntiAlias=True))


def bush(cv, cx, cy, s, seed, base='#3cae45', dark='#26843a', light='#a5e46b'):
    rnd = random.Random(seed)
    balls = [(cx + rnd.uniform(-1, 1) * s * 1.2, cy + rnd.uniform(-0.5, 0.4) * s, s * rnd.uniform(0.45, 0.75)) for _ in range(9)]
    balls += [(cx + (i - 3) * s * 0.42, cy + s * 0.55, s * 0.6) for i in range(7)]
    shape = union([oval(x, y, r, r) for x, y, r in balls])
    cv.drawPath(shape, skia.Paint(Color=col(base), AntiAlias=True))
    cv.save(); cv.clipPath(shape, doAntiAlias=True)
    for x, y, r in balls:  # shade the underside of every ball, light its top
        cv.drawCircle(x + r * 0.15, y + r * 0.55, r * 0.75, skia.Paint(Color=col(dark, 150), AntiAlias=True))
    for x, y, r in balls:
        cv.drawCircle(x - r * 0.2, y - r * 0.25, r * 0.55, skia.Paint(Color=col(base), AntiAlias=True))
        for _ in range(14):
            a = rnd.uniform(math.pi * 1.05, math.pi * 1.9); rr = r * rnd.uniform(0.35, 0.8)
            px, py = x - r * 0.2 + math.cos(a) * rr, y - r * 0.25 + math.sin(a) * rr
            cv.drawLine(px, py, px + rnd.uniform(4, 16), py - rnd.uniform(2, 10),
                        skia.Paint(Color=col(light, 200), StrokeWidth=rnd.uniform(2, 5), AntiAlias=True, StrokeCap=skia.Paint.kRound_Cap))
    for _ in range(int(s * 6)):
        cv.drawCircle(rnd.uniform(cx - s * 2, cx + s * 2), rnd.uniform(cy - s, cy + s), rnd.uniform(1, 2.5), skia.Paint(Color=col('#ffffff', 70), AntiAlias=True))
    cv.restore()
    stroke(cv, shape, 5)


# ------------------------------------------------------------------ people
SKIN = '#f3c4a2'


def head(cv, cx, cy, s, look=(0, 0), mood='shock', hair='#a85a28', stubble=True, flip=1, hat=None, mustache=None, skin=SKIN):
    """Unit head about 1.0 tall, 0.84 wide, turned a little toward +x (flip=-1 mirrors)."""
    out = [(-0.06, -0.53), (0.22, -0.5), (0.39, -0.33), (0.43, -0.06), (0.4, 0.2), (0.3, 0.39), (0.12, 0.5), (-0.08, 0.5),
           (-0.27, 0.41), (-0.38, 0.22), (-0.43, -0.05), (-0.39, -0.33), (-0.25, -0.49)]
    hp = smooth(T(out, cx, cy, s, flip))
    # ear on the far-from-camera side
    ex = -0.41
    ear = smooth(T([(ex + 0.02, -0.12), (ex - 0.1, -0.15), (ex - 0.13, 0.0), (ex - 0.08, 0.12), (ex + 0.02, 0.1)], cx, cy, s, flip))
    fillp(cv, ear, skin, s * 0.011)
    fillp(cv, hp, skin, s * 0.012)
    cv.save(); cv.clipPath(hp, doAntiAlias=True)
    if stubble:  # stubble: a soft brown jaw band with grain
        rnd = random.Random(int(cx + cy))
        jaw = smooth(T([(-0.42, 0.08), (-0.2, 0.18), (0.0, 0.14), (0.2, 0.18), (0.44, 0.06), (0.44, 0.6), (-0.44, 0.6)], cx, cy, s, flip))
        cv.drawPath(jaw, skia.Paint(Color=col('#b06a3a', 60), AntiAlias=True, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, s * 0.012)))
        for _ in range(int(s * 0.9)):
            x, y = cx + rnd.uniform(-0.42, 0.42) * s, cy + rnd.uniform(0.12, 0.5) * s
            if jaw.contains(x, y): cv.drawCircle(x, y, s * 0.0028, skia.Paint(Color=col('#7a3f1c', 110), AntiAlias=True))
    # a little cheek shading on the far side
    cv.drawPath(smooth(T([(-0.44, -0.2), (-0.3, 0.0), (-0.32, 0.3), (-0.5, 0.3)], cx, cy, s, flip)), skia.Paint(Color=col('#d98f6e', 70), AntiAlias=True))
    cv.restore()
    # eyes: big, round, overlapping a little, pupils small
    big = {'shock': 1.18, 'angry': 0.82, 'smug': 0.86}.get(mood, 1.0)
    for ex, ey, r in [(-0.13, -0.06, 0.14), (0.17, -0.07, 0.155)]:
        r *= big
        ry = r * (0.62 if mood == 'angry' else 1.0)
        X, Y = cx + ex * s * flip, cy + ey * s
        e = oval(X, Y, r * s, ry * s)
        fillp(cv, e, '#ffffff', s * 0.011)
        cv.drawCircle(X + look[0] * r * s * 0.45 * flip, Y + look[1] * ry * s * 0.45, s * 0.026, skia.Paint(Color=col(INK), AntiAlias=True))
        if mood == 'angry':  # heavy upper lid
            line(cv, [(X - r * s, Y - ry * s * 0.2), (X, Y - ry * s * 0.75), (X + r * s, Y - ry * s * 0.35)], s * 0.016)
    # eyebrows
    if mood == 'shock':
        line(cv, T([(-0.25, -0.27), (-0.15, -0.33), (-0.04, -0.3)], cx, cy, s, flip), s * 0.022)
        line(cv, T([(0.05, -0.31), (0.17, -0.36), (0.3, -0.31)], cx, cy, s, flip), s * 0.022)
    elif mood == 'angry':
        line(cv, T([(-0.27, -0.2), (-0.15, -0.16), (-0.03, -0.1)], cx, cy, s, flip), s * 0.03)
        line(cv, T([(0.04, -0.1), (0.17, -0.17), (0.32, -0.22)], cx, cy, s, flip), s * 0.03)
    else:
        line(cv, T([(-0.25, -0.24), (-0.13, -0.27), (-0.03, -0.25)], cx, cy, s, flip), s * 0.02)
        line(cv, T([(0.06, -0.26), (0.18, -0.29), (0.3, -0.26)], cx, cy, s, flip), s * 0.02)
    # nose: a soft bulb pointing the way he faces
    nose = smooth(T([(0.03, 0.02), (0.14, 0.09), (0.2, 0.17), (0.16, 0.23), (0.07, 0.23), (0.02, 0.19)], cx, cy, s, flip))
    fillp(cv, nose, skin, s * 0.011)
    line(cv, T([(0.1, 0.2), (0.12, 0.17)], cx, cy, s, flip), s * 0.009)
    # mustache
    if mustache:
        m = smooth(T([(-0.12, 0.27), (0.02, 0.24), (0.1, 0.25), (0.24, 0.27), (0.3, 0.33), (0.2, 0.32), (0.06, 0.3), (-0.06, 0.31), (-0.18, 0.34)], cx, cy, s, flip))
        fillp(cv, m, mustache, s * 0.01)
    # mouth
    if mood == 'shock':
        mo = oval(cx + 0.05 * s * flip, cy + 0.36 * s, 0.05 * s, 0.035 * s)
        fillp(cv, mo, '#5a1f1a', s * 0.011)
    elif mood == 'angry':
        line(cv, T([(-0.08, 0.38), (0.04, 0.35), (0.16, 0.38)], cx, cy, s, flip), s * 0.016)
    else:
        line(cv, T([(-0.06, 0.34), (0.06, 0.38), (0.18, 0.33)], cx, cy, s, flip), s * 0.016)
    # hair
    if hair:
        hr = smooth(T([(-0.42, -0.12), (-0.46, -0.36), (-0.32, -0.55), (-0.08, -0.64), (0.06, -0.72), (0.12, -0.6), (0.3, -0.57),
                       (0.44, -0.42), (0.42, -0.24), (0.3, -0.36), (0.12, -0.42), (-0.1, -0.38), (-0.28, -0.3), (-0.36, -0.1)], cx, cy, s, flip))
        fillp(cv, hr, hair, s * 0.012)
        for a, b in [((-0.3, -0.48), (-0.18, -0.36)), ((-0.05, -0.56), (0.02, -0.44)), ((0.2, -0.5), (0.26, -0.4))]:
            line(cv, T([a, b], cx, cy, s, flip), s * 0.008, '#5a2a10')
    if mood == 'shock':  # sweat drop
        d = smooth(T([(0.3, -0.36), (0.36, -0.26), (0.33, -0.2), (0.27, -0.21), (0.26, -0.27)], cx, cy, s, flip))
        fillp(cv, d, '#9fdcff', s * 0.008)
    if hat: hat(cv, cx, cy, s, flip)


def straw_hat(cv, cx, cy, s, flip):
    brim = smooth(T([(-0.72, -0.4), (-0.3, -0.5), (0.3, -0.52), (0.74, -0.44), (0.4, -0.34), (-0.4, -0.32)], cx, cy, s, flip))
    crown = smooth(T([(-0.36, -0.42), (-0.33, -0.7), (-0.1, -0.8), (0.2, -0.79), (0.36, -0.68), (0.38, -0.44)], cx, cy, s, flip))
    fillp(cv, brim, '#e7c063', s * 0.012)
    fillp(cv, crown, '#efcc72', s * 0.012)
    band = smooth(T([(-0.35, -0.5), (0.37, -0.52), (0.37, -0.45), (-0.36, -0.43)], cx, cy, s, flip))
    fillp(cv, band, '#b0342a', s * 0.009)
    for i in range(6):
        x = -0.28 + i * 0.11
        line(cv, T([(x, -0.75 + abs(x) * 0.1), (x + 0.03, -0.55)], cx, cy, s, flip), s * 0.005, '#b48a3a')


def shako(cv, cx, cy, s, flip):
    body = poly(T([(-0.3, -0.42), (-0.26, -0.92), (0.3, -0.95), (0.34, -0.44)], cx, cy, s, flip))
    fillp(cv, body, '#1e1b22', s * 0.012)
    fillp(cv, smooth(T([(-0.42, -0.4), (0.0, -0.46), (0.46, -0.42), (0.1, -0.34)], cx, cy, s, flip)), '#1e1b22', s * 0.012)
    fillp(cv, oval(cx + 0.02 * s * flip, cy - 0.7 * s, 0.09 * s, 0.1 * s), '#e6b43c', s * 0.009)
    fillp(cv, oval(cx + 0.02 * s * flip, cy - 0.99 * s, 0.05 * s, 0.05 * s), '#f2f2f2', s * 0.008)


def kepi(cv, cx, cy, s, flip):
    cap = smooth(T([(-0.38, -0.42), (-0.32, -0.72), (0.0, -0.8), (0.32, -0.74), (0.38, -0.46)], cx, cy, s, flip))
    fillp(cv, cap, '#24407e', s * 0.012)
    visor = smooth(T([(0.02, -0.44), (0.32, -0.46), (0.56, -0.38), (0.3, -0.36)], cx, cy, s, flip))
    fillp(cv, visor, '#141218', s * 0.011)
    fillp(cv, oval(cx + 0.06 * s * flip, cy - 0.58 * s, 0.06 * s, 0.045 * s), '#e6b43c', s * 0.007)


def soldier(cv, cx, foot_y, s, coat, trim, hatf, flip, mood='angry', hair='#3a2412', mustache=None, gun=True):
    """Full body: big head, small coat, stick legs (s = head height in px)."""
    hy = foot_y - s * 2.15
    # legs and feet
    for dx in (-0.12, 0.14):
        line(cv, [(cx + dx * s, foot_y - s * 0.9), (cx + dx * s * 1.1, foot_y - s * 0.02)], s * 0.035)
        fillp(cv, oval(cx + dx * s * 1.1 + 0.07 * s * flip, foot_y, 0.1 * s, 0.045 * s), '#1a1614', s * 0.02)
    body = smooth([(cx - 0.3 * s, hy + 0.48 * s), (cx + 0.3 * s, hy + 0.48 * s), (cx + 0.36 * s, foot_y - 0.85 * s), (cx - 0.34 * s, foot_y - 0.85 * s)], True, 0.4)
    fillp(cv, body, coat, s * 0.03)
    cv.save(); cv.clipPath(body, doAntiAlias=True)
    line(cv, [(cx - 0.3 * s, hy + 0.5 * s), (cx + 0.36 * s, foot_y - 0.95 * s)], s * 0.07, trim)
    line(cv, [(cx + 0.3 * s, hy + 0.5 * s), (cx - 0.34 * s, foot_y - 0.95 * s)], s * 0.07, trim)
    cv.drawRect(skia.Rect.MakeLTRB(cx - s, foot_y - 1.08 * s, cx + s, foot_y - 0.98 * s), skia.Paint(Color=col('#1a1614')))
    for i in range(4): cv.drawCircle(cx, hy + (0.62 + i * 0.13) * s, s * 0.025, skia.Paint(Color=col('#e6b43c'), AntiAlias=True))
    cv.restore()
    stroke(cv, body, s * 0.03)
    # rifle held across the body with both hands
    g0, g1 = (cx - 0.38 * s * flip, hy + 1.42 * s), (cx + 0.5 * s * flip, hy - 0.25 * s)
    at = lambda k: (g0[0] + (g1[0] - g0[0]) * k, g0[1] + (g1[1] - g0[1]) * k)
    if gun:
        line(cv, [g0, at(0.62)], s * 0.075, '#7a4a22'); line(cv, [at(0.55), g1], s * 0.035, '#3c3c44')
        stroke(cv, poly([g0, at(0.62)], False), s * 0.012)
    for sh, k, mid in [((cx - 0.28 * s * flip, hy + 0.62 * s), 0.3, (cx - 0.42 * s * flip, hy + 0.95 * s)),
                       ((cx + 0.28 * s * flip, hy + 0.62 * s), 0.6, (cx + 0.38 * s * flip, hy + 0.9 * s))]:
        hand = at(k)
        line(cv, [sh, mid, hand], s * 0.035)
        fillp(cv, oval(*hand, 0.065 * s, 0.065 * s), SKIN, s * 0.02)
    head(cv, cx, hy, s, look=(1, 0.1), mood=mood, hair=None, stubble=True, flip=flip, hat=hatf, mustache=mustache)


# ------------------------------------------------------------------ the pig
def pig(cv, cx, cy, s, flip=1, chewing=True):
    body = smooth(T([(-0.55, -0.05), (-0.4, -0.35), (0.0, -0.42), (0.38, -0.32), (0.55, -0.1), (0.52, 0.18), (0.25, 0.3), (-0.3, 0.3), (-0.55, 0.16)], cx, cy, s, flip))
    for dx in (-0.36, -0.18, 0.2, 0.36):
        leg = poly(T([(dx - 0.06, 0.2), (dx + 0.06, 0.2), (dx + 0.06, 0.46), (dx - 0.06, 0.46)], cx, cy, s, flip))
        fillp(cv, leg, '#2c2733', s * 0.02)
    tail = T([(-0.55, -0.05), (-0.66, -0.12), (-0.62, -0.22), (-0.7, -0.24)], cx, cy, s, flip)
    line(cv, tail, s * 0.025)
    fillp(cv, body, '#2c2733', s * 0.022)
    cv.save(); cv.clipPath(body, doAntiAlias=True)
    cv.drawPath(oval(cx + 0.05 * s * flip, cy - 0.3 * s, 0.45 * s, 0.12 * s), skia.Paint(Color=col('#5a5466', 160), AntiAlias=True))
    cv.drawPath(oval(cx - 0.3 * s * flip, cy + 0.08 * s, 0.18 * s, 0.14 * s), skia.Paint(Color=col('#f2f2ee', 230), AntiAlias=True))  # a white Berkshire patch
    cv.restore()
    stroke(cv, body, s * 0.022)
    # head
    hd = smooth(T([(0.32, -0.34), (0.6, -0.44), (0.84, -0.26), (0.88, 0.02), (0.66, 0.18), (0.38, 0.12)], cx, cy, s, flip))
    for ex in (0.48, 0.66):
        ear = poly(T([(ex - 0.06, -0.3), (ex + 0.02, -0.5), (ex + 0.08, -0.28)], cx, cy, s, flip))
        fillp(cv, ear, '#2c2733', s * 0.018)
    fillp(cv, hd, '#2c2733', s * 0.022)
    snout = oval(cx + 0.9 * s * flip, cy - 0.04 * s, 0.11 * s, 0.095 * s)
    fillp(cv, snout, '#f29bab', s * 0.018)
    for d in (-0.035, 0.035):
        cv.drawCircle(cx + (0.9 + d) * s * flip, cy - 0.04 * s, s * 0.018, skia.Paint(Color=col('#7a2a3a'), AntiAlias=True))
    for ex, r in [(0.6, 0.085), (0.75, 0.09)]:
        fillp(cv, oval(cx + ex * s * flip, cy - 0.2 * s, r * s, r * s), '#ffffff', s * 0.014)
        cv.drawCircle(cx + (ex + 0.025) * s * flip, cy - 0.18 * s, s * 0.02, skia.Paint(Color=col(INK), AntiAlias=True))
    if chewing:  # a potato in the mouth
        fillp(cv, oval(cx + 0.86 * s * flip, cy + 0.12 * s, 0.11 * s, 0.07 * s), '#c9944e', s * 0.016)
        for d in (-0.04, 0.03): cv.drawCircle(cx + (0.86 + d) * s * flip, cy + 0.11 * s, s * 0.008, skia.Paint(Color=col('#7a5228'), AntiAlias=True))


def potato_row(cv, y, x0, x1, seed):
    rnd = random.Random(seed)
    fillp(cv, smooth([(x0, y), ((x0 + x1) / 2, y - 18), (x1, y), (x1 - 20, y + 26), (x0 + 20, y + 26)]), '#7a4e2c', 4)
    for i in range(int((x1 - x0) / 70)):
        x = x0 + 40 + i * 70 + rnd.uniform(-10, 10)
        for a in (-0.7, 0, 0.7):
            leaf = oval(x + math.sin(a) * 22, y - 30 - math.cos(a) * 14, 14, 9)
            fillp(cv, leaf, '#4fbf4a', 3)


# ------------------------------------------------------------------ frames
def frame_farmer():
    surf = skia.Surface(W, H); cv = surf.getCanvas()
    sky(cv, seed=3)
    # field, fence and the potato patch behind him
    fillp(cv, smooth([(-50, 760), (500, 720), (1100, 740), (1980, 700), (1980, 1150), (-50, 1150)]), '#79c94f', 0)
    for x in range(1120, 1960, 150):
        fillp(cv, poly([(x, 560), (x + 22, 560), (x + 22, 790), (x, 790)]), '#a8743f', 4)
    for y in (610, 690):
        fillp(cv, poly([(1100, y), (1960, y - 8), (1960, y + 14), (1100, y + 22)]), '#b98247', 4)
    for i, y in enumerate((820, 900, 990)):
        potato_row(cv, y, 1080 + i * 30, 1900, 10 + i)
    pig(cv, 1470, 905, 300, flip=-1)
    bush(cv, 160, 850, 170, 4); bush(cv, 520, 960, 150, 5)
    # him: big head close-up, plaid shirt
    sh = smooth([(470, 1100), (520, 880), (700, 820), (900, 830), (1030, 900), (1060, 1100)], True, 0.6)
    cv.save(); cv.clipPath(sh, doAntiAlias=True)
    cv.drawPath(sh, skia.Paint(Color=col('#d2483c')))
    for i in range(-10, 30):
        cv.drawRect(skia.Rect.MakeXYWH(440 + i * 40, 800, 12, 400), skia.Paint(Color=col('#f4e7d0', 150)))
        cv.drawRect(skia.Rect.MakeXYWH(440, 800 + i * 40, 700, 12), skia.Paint(Color=col('#f4e7d0', 150)))
    cv.restore(); stroke(cv, sh, 6)
    fillp(cv, poly([(700, 822), (770, 900), (840, 826)]), '#f6efe2', 5)
    head(cv, 770, 520, 560, look=(1, 0.15), mood='shock', hair='#a85a28', hat=straw_hat)
    text(cv, 'JUNE 15, 1859', 1500, 170, 96)
    return surf.makeImageSnapshot()


def frame_map():
    surf = skia.Surface(W, H); cv = surf.getCanvas()
    cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=col('#3d86dc')))
    rnd = random.Random(7)
    for _ in range(120):  # little wave marks
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        line(cv, [(x, y), (x + 14, y - 6), (x + 28, y)], 3, '#7fb6f0')
    land = '#8fd16a'
    bc = smooth([(760, -40), (1960, -40), (1960, 470), (1500, 520), (1210, 500), (1110, 430), (1020, 300), (900, 180), (790, 90)])
    usa = smooth([(1110, 520), (1500, 540), (1960, 500), (1960, 1120), (1250, 1120), (1180, 960), (1230, 820), (1140, 680)])
    van = smooth([(30, 170), (250, 110), (520, 240), (760, 420), (900, 560), (960, 690), (880, 770), (700, 700), (500, 560), (300, 420), (120, 320), (10, 260)])
    oly = smooth([(-40, 880), (380, 820), (760, 880), (1000, 940), (1080, 1120), (-40, 1120)])
    sj = smooth([(985, 640), (1050, 620), (1090, 668), (1072, 742), (1020, 770), (975, 730)])
    for p in (bc, usa, van, oly): fillp(cv, p, land, 6)
    fillp(cv, sj, '#ffb43c', 6)
    # the border everyone argued about: dashed through the water on both sides of the island
    dash = skia.Paint(Color=col('#d62a2a'), AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=7,
                      PathEffect=skia.DashPathEffect.Make([26, 18], 0))
    p = skia.Path(); p.moveTo(1110, 505); p.cubicTo(1000, 560, 930, 620, 940, 700); p.cubicTo(950, 780, 900, 830, 860, 900); cv.drawPath(p, dash)
    p = skia.Path(); p.moveTo(1110, 505); p.cubicTo(1130, 580, 1120, 640, 1120, 700); p.cubicTo(1120, 780, 1100, 840, 1080, 900); cv.drawPath(p, dash)
    # tiny soldiers marching in from both sides
    def tiny(x, y, coat):
        line(cv, [(x - 4, y + 18), (x - 5, y + 34)], 3); line(cv, [(x + 4, y + 18), (x + 5, y + 34)], 3)
        fillp(cv, poly([(x - 9, y), (x + 9, y), (x + 8, y + 20), (x - 8, y + 20)]), coat, 3)
        fillp(cv, oval(x, y - 10, 11, 11), SKIN, 3)
        line(cv, [(x + 10, y + 16), (x + 16, y - 16)], 3, '#7a4a22')
    for i in range(6): tiny(820 + i * 34 - (i % 2) * 8, 470 + i * 26, '#d62a2a')
    for i in range(6): tiny(1240 + i * 36, 650 + i * 22 - (i % 2) * 10, '#24407e')
    pig(cv, 1030, 690, 60, flip=-1, chewing=False)
    text(cv, '!', 1080, 650, 70, '#ffe14a')
    text(cv, 'BRITISH', 1500, 250, 92)
    text(cv, 'AMERICAN', 1610, 800, 92)
    text(cv, 'SAN JUAN ISLAND', 1030, 860, 54, '#ffe14a')
    text(cv, '1859', 230, 1010, 120)
    return surf.makeImageSnapshot()


def frame_standoff():
    surf = skia.Surface(W, H); cv = surf.getCanvas()
    sky(cv, seed=9, y1=760)
    # sea with a British warship, then the meadow
    cv.drawRect(skia.Rect.MakeLTRB(0, 600, W, 760), skia.Paint(Color=col('#3a8ed8')))
    hull = smooth([(820, 640), (1060, 640), (1030, 668), (850, 668)], True, 0.3); fillp(cv, hull, '#3a2a22', 4)
    for x in (880, 945, 1005):
        line(cv, [(x, 640), (x, 540)], 4)
        fillp(cv, poly([(x - 24, 555), (x + 22, 558), (x + 19, 605), (x - 21, 602)]), '#f4efe4', 3)
    fillp(cv, smooth([(-50, 690), (600, 650), (1300, 680), (1980, 640), (1980, 1150), (-50, 1150)]), '#7fcd52', 6)
    rnd = random.Random(2)
    for _ in range(260):
        x, y = rnd.uniform(0, W), rnd.uniform(700, H)
        line(cv, [(x, y), (x + rnd.uniform(-6, 6), y - rnd.uniform(10, 26))], 3, '#4fa93c')
    bush(cv, 90, 760, 140, 11); bush(cv, 1840, 780, 150, 12)
    soldier(cv, 560, 960, 250, '#cf2330', '#f4f1ea', shako, 1, mood='angry', mustache='#6a3a1a')
    soldier(cv, 1360, 960, 250, '#28447f', '#a8b8d8', kepi, -1, mood='angry', mustache='#2a1a10')
    pig(cv, 960, 905, 210, flip=1)
    text(cv, 'THE PIG WAR', W / 2, 160, 130)
    return surf.makeImageSnapshot()


os.makedirs(OUT, exist_ok=True)
for name, fn in [('pigwar_01_farmer', frame_farmer), ('pigwar_02_map', frame_map), ('pigwar_03_standoff', frame_standoff)]:
    fn().save(os.path.join(OUT, name + '.png'), skia.kPNG)
    print('wrote', name)
