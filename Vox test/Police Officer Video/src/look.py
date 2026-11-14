"""Drawing helpers and the film look for the police-officer video.
Everything is drawn in a 1920x1080 design space and rendered at 2560x1440 (canvas scale 4/3).
Look (from the reference videos): flat shapes, thin dark outlines, one shade tone, desaturated warm/navy palette,
glows from lamps and windows, coloured light washes, heavy vignette, film grain, slight softness, fisheye POVs.
"""
import math, os, random
import numpy as np
import cv2
import skia

DW, DH = 1920, 1080                 # design space
RW, RH = 2560, 1440                 # render size
K = RW / DW
LINE = '#1b1411'
FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fonts')
_tf = {}


def col(h, a=255):
    h = h.lstrip('#'); return skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(max(0, min(255, a))))


def mix(a, b, k):
    a, b = a.lstrip('#'), b.lstrip('#')
    return '#%02x%02x%02x' % tuple(int(int(a[i:i + 2], 16) * (1 - k) + int(b[i:i + 2], 16) * k) for i in (0, 2, 4))


def typeface(weight):
    if weight not in _tf: _tf[weight] = skia.Typeface.MakeFromFile(os.path.join(FONTS, f'MontserratLC-{weight}.ttf'))
    return _tf[weight]


# ------------------------------------------------------------------ geometry
def smooth(pts, closed=True, k=1.0):
    p = skia.Path(); n = len(pts); p.moveTo(*pts[0])
    for i in range(n if closed else n - 1):
        p0 = pts[(i - 1) % n] if closed else pts[max(i - 1, 0)]
        p1, p2 = pts[i], pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if closed else pts[min(i + 2, n - 1)]
        p.cubicTo(p1[0] + (p2[0] - p0[0]) / 6 * k, p1[1] + (p2[1] - p0[1]) / 6 * k,
                  p2[0] - (p3[0] - p1[0]) / 6 * k, p2[1] - (p3[1] - p1[1]) / 6 * k, *p2)
    if closed: p.close()
    return p


def poly(pts, closed=True):
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    if closed: p.close()
    return p


def rect(x, y, w, h):
    p = skia.Path(); p.addRect(skia.Rect.MakeXYWH(x, y, w, h)); return p


def rrect(x, y, w, h, r):
    p = skia.Path(); p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)); return p


def oval(cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    p = skia.Path(); p.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry)); return p


def inter(a, b): return skia.Op(a, b, skia.PathOp.kIntersect_PathOp)
def union(a, b): return skia.Op(a, b, skia.PathOp.kUnion_PathOp)
def minus(a, b): return skia.Op(a, b, skia.PathOp.kDifference_PathOp)


def ease(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def lerp(a, b, k): return a + (b - a) * k
def prog(t, a, b): return max(0.0, min(1.0, (t - a) / (b - a))) if b > a else float(t >= a)


class Pen:
    def __init__(self, cv, lw=3.0): self.cv, self.lw = cv, lw

    def fill(self, path, c, a=255, blur=0):
        p = skia.Paint(Color=col(c, a), AntiAlias=True)
        if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
        self.cv.drawPath(path, p)

    def line(self, path, w=None, c=LINE, a=255):
        self.cv.drawPath(path, skia.Paint(Color=col(c, a), AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w or self.lw,
                                          StrokeJoin=skia.Paint.kRound_Join, StrokeCap=skia.Paint.kRound_Cap))

    def seg(self, a, b, w=None, c=LINE, alpha=255): self.line(poly([a, b], False), w, c, alpha)

    def shape(self, path, c, w=None, lc=LINE):
        self.fill(path, c); self.line(path, w, lc)

    def shade(self, clip, path, c, a=255):
        self.cv.save(); self.cv.clipPath(clip, doAntiAlias=True); self.fill(path, c, a); self.cv.restore()

    def glow(self, x, y, r, c, a=150):
        self.cv.drawCircle(x, y, r, skia.Paint(Shader=skia.GradientShader.MakeRadial((x, y), r, [col(c, a), col(c, 0)])))

    def grad(self, x0, y0, x1, y1, c0, c1, vertical=True, path=None):
        pts = [(x0, y0), (x0, y1)] if vertical else [(x0, y0), (x1, y0)]
        p = skia.Paint(Shader=skia.GradientShader.MakeLinear(pts, [col(c0), col(c1)]))
        if path is None: self.cv.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), p)
        else: self.cv.drawPath(path, p)

    def wash(self, c, a):
        self.cv.drawRect(skia.Rect.MakeWH(DW * 3, DH * 3).makeOffset(-DW, -DH), skia.Paint(Color=col(c, a)))


def text(cv, s, x, y, weight=600, size=30, c='#ffffff', a=255, spacing=0.0, align='center', shadow=0.0):
    f = skia.Font(typeface(weight), size)
    glyphs = f.textToGlyphs(s); widths = f.getWidths(glyphs)
    total = sum(widths) + spacing * size * (len(glyphs) - 1)
    x0 = x - total / 2 if align == 'center' else (x - total if align == 'right' else x)
    pos, cx = [], x0
    for w in widths: pos.append(skia.Point(cx, y)); cx += w + spacing * size
    blob = skia.TextBlob.MakeFromPosText(s, pos, f)
    if shadow:
        cv.drawTextBlob(blob, 0, size * 0.05, skia.Paint(Color=col('#000000', 200 * shadow), AntiAlias=True,
                                                         MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, size * 0.14)))
    cv.drawTextBlob(blob, 0, 0, skia.Paint(Color=col(c, a), AntiAlias=True))
    return total


def wrap(s, weight, size, maxw, spacing=0.0):
    f = skia.Font(typeface(weight), size); words = s.split(); lines, cur = [], ''
    for w in words:
        tryl = (cur + ' ' + w).strip()
        if f.measureText(tryl) + spacing * size * len(tryl) > maxw and cur: lines.append(cur); cur = w
        else: cur = tryl
    if cur: lines.append(cur)
    return lines


def caption(cv, s, alpha=255):
    """The reference's caption: small white uppercase, letter-spaced, low in the frame, soft shadow; wraps to two lines."""
    s = s.upper()
    lines = wrap(s, 600, 31, 1300, 0.035)
    y0 = 975 - (len(lines) - 1) * 42
    for i, l in enumerate(lines): text(cv, l, DW / 2, y0 + i * 42, 600, 31, '#ffffff', alpha, 0.035, 'center', 1.0)


def header(cv, right, corner='12:36 AM', alpha=255):
    left = 'HOUSE RULES'
    w = text(cv, left, 44, 42, 600, 13, '#8c8c98', 120 * alpha / 255, 0.24, 'left')
    text(cv, '/   ' + right, 44 + w + 16, 42, 600, 13, '#c4c4ce', 150 * alpha / 255, 0.24, 'left')
    text(cv, corner, DW - 44, 42, 600, 13, '#8c8c98', 100 * alpha / 255, 0.24, 'right')


# ------------------------------------------------------------------ post (numpy / OpenCV at render size)
_cache = {}


def _vignette(strength, power=1.6):
    key = ('vig', round(strength, 2))
    if key not in _cache:
        yy, xx = np.mgrid[0:RH, 0:RW].astype(np.float32)
        d = np.sqrt(((xx - RW / 2) / (RW / 2)) ** 2 + ((yy - RH / 2) / (RH / 2)) ** 2)
        m = (1 - strength * np.clip(d - 0.3, 0, 1) ** power).astype(np.float32)
        _cache[key] = cv2.merge([m, m, m])
    return _cache[key]


def _grain(i, amount):
    key = ('grain', i % 6, round(amount, 1))
    if key not in _cache:
        rng = np.random.default_rng(i % 6)
        g = cv2.resize(rng.normal(0, 1, (RH // 2, RW // 2)).astype(np.float32), (RW, RH), interpolation=cv2.INTER_LINEAR) * amount
        _cache[key] = cv2.merge([g, g, g])
    return _cache[key]


def _maps(kind):
    if kind not in _cache:
        yy, xx = np.mgrid[0:RH, 0:RW].astype(np.float32)
        nx, ny = (xx - RW / 2) / (RW / 2), (yy - RH / 2) / (RW / 2)
        r2 = nx * nx + ny * ny
        k, zoom = {'peephole': (0.55, 1.05), 'doorbell': (0.42, 1.12), 'lens': (0.08, 1.02)}[kind]
        f = (1 + k * r2) / zoom
        mx, my = nx * f * (RW / 2) + RW / 2, ny * f * (RW / 2) + RH / 2
        mask = None
        if kind == 'peephole':
            r = np.sqrt((xx - RW / 2) ** 2 + (yy - RH / 2) ** 2) / (RH * 0.43)
            inside = np.clip((1 - r) * 80, 0, 1)
            shade = np.clip(1 - np.clip(r - 0.6, 0, 1) * 1.8, 0, 1) ** 1.5
            ring = np.exp(-((r - 1.0) / 0.011) ** 2)
            m = (inside * shade).astype(np.float32)
            ringc = np.dstack([ring * 40 * 0.9, ring * 26 * 0.9, ring * 16 * 0.9]).astype(np.float32)
            mask = (cv2.merge([m, m, m]), ringc)
        _cache[kind] = (cv2.convertMaps(mx.astype(np.float32), my.astype(np.float32), cv2.CV_16SC2), mask)
    return _cache[kind]


def post(rgb, frame_i, lens=None, vignette=0.7, grain=6.0, soft=0.7, tint=None, lift=0.0, gain=1.0):
    """rgb: uint8 HxWx3 at render size. All the heavy lifting in OpenCV (SIMD, multithreaded). Returns uint8."""
    a = rgb
    if lens:
        (m1, m2), mask = _maps(lens)
        a = cv2.remap(a, m1, m2, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    if soft: a = cv2.GaussianBlur(a, (0, 0), soft)
    f = a.astype(np.float32)
    if tint is not None or gain != 1.0:
        tt = np.array(tint if tint is not None else (1, 1, 1), np.float32) * gain
        f = cv2.multiply(f, cv2.merge([np.full(f.shape[:2], float(v), np.float32) for v in tt])) if tint is not None else f * gain
    if lens == 'peephole':
        m, ringc = _maps('peephole')[1]
        f = cv2.add(cv2.multiply(f, m), ringc)
    f = cv2.multiply(f, _vignette(vignette))
    if lift: f = cv2.add(f, np.full_like(f, lift))
    f = cv2.add(f, _grain(frame_i, grain))
    return cv2.convertScaleAbs(f)
