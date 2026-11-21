"""Flat night-horror look for "rules" videos (If X knocks... NEVER OPEN): skia drawing + numpy post.
Look, from the reference videos: flat vector shapes with thin dark outlines and one soft shade tone, dark navy nights,
warm window glows, coloured light washes, fisheye peephole and doorbell views, a heavy vignette, film grain, slight softness,
small uppercase captions low in the frame, a tiny "HOUSE RULES / RULE 1 OF 7" header.
"""
import math, os, random
import numpy as np
import skia
from scipy import ndimage

W, H = 1920, 1080
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
LINE = '#1a1210'


def col(h, a=255):
    h = h.lstrip('#'); return skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def font(weight, size):
    return skia.Font(skia.Typeface.MakeFromFile(os.path.join(FONT_DIR, f'Montserrat-{weight}.ttf')), size)


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


def rrect(x, y, w, h, r):
    p = skia.Path(); p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)); return p


def oval(cx, cy, rx, ry):
    p = skia.Path(); p.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry)); return p


def inter(a, b): return skia.Op(a, b, skia.PathOp.kIntersect_PathOp)


class Pen:
    def __init__(self, cv): self.cv = cv

    def fill(self, path, c, a=255, blur=0):
        p = skia.Paint(Color=col(c, a), AntiAlias=True)
        if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
        self.cv.drawPath(path, p)

    def line(self, path, w, c=LINE, a=255):
        self.cv.drawPath(path, skia.Paint(Color=col(c, a), AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                                          StrokeJoin=skia.Paint.kRound_Join, StrokeCap=skia.Paint.kRound_Cap))

    def shape(self, path, c, w=4, lc=LINE):
        self.fill(path, c); self.line(path, w, lc)

    def shade(self, clip, path, c, a=255):
        self.cv.save(); self.cv.clipPath(clip, doAntiAlias=True); self.fill(path, c, a); self.cv.restore()

    def glow(self, x, y, r, c, a=160):
        self.cv.drawCircle(x, y, r, skia.Paint(Shader=skia.GradientShader.MakeRadial((x, y), r, [col(c, a), col(c, 0)])))

    def grad_rect(self, x0, y0, x1, y1, c0, c1, vertical=True):
        pts = [(x0, y0), (x0, y1)] if vertical else [(x0, y0), (x1, y0)]
        self.cv.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), skia.Paint(Shader=skia.GradientShader.MakeLinear(pts, [col(c0), col(c1)])))


def text(cv, s, x, y, weight, size, c='#ffffff', a=255, spacing=0.0, align='center', shadow=True):
    f = font(weight, size)
    glyphs = f.textToGlyphs(s); widths = f.getWidths(glyphs)
    total = sum(widths) + spacing * size * (len(s) - 1)
    x0 = x - total / 2 if align == 'center' else (x - total if align == 'right' else x)
    pos, cx = [], x0
    for w in widths: pos.append(skia.Point(cx, y)); cx += w + spacing * size
    blob = skia.TextBlob.MakeFromPosText(s, pos, f) if hasattr(skia.TextBlob, 'MakeFromPosText') else skia.TextBlob.MakeFromString(s, f)
    if shadow:
        cv.drawTextBlob(blob, 0, size * 0.06, skia.Paint(Color=col('#000000', 170), AntiAlias=True, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, size * 0.12)))
    cv.drawTextBlob(blob, 0, 0, skia.Paint(Color=col(c, a), AntiAlias=True))
    return total


def caption(cv, s, y=962):
    text(cv, s.upper(), W / 2, y, 600, 31, spacing=0.035)


def header(cv, left='HOUSE RULES', right='RULE 1 OF 7', corner='NIGHT 03:00'):
    text(cv, left, 42, 40, 600, 14, '#9a9aa6', 120, 0.22, 'left', False)
    text(cv, '/  ' + right, 42 + font(600, 14).measureText(left) + left.__len__() * 14 * 0.22 + 14, 40, 600, 14, '#c8c8d2', 150, 0.22, 'left', False)
    text(cv, corner, W - 42, 40, 600, 14, '#9a9aa6', 90, 0.22, 'right', False)


# ------------------------------------------------------------------ post
def to_np(img):
    return np.array(img.toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3], dtype=np.float32)


def finish(img_np, vignette=0.75, grain=7.0, soft=0.6, seed=1):
    a = img_np.copy()
    if soft: a = ndimage.gaussian_filter(a, (soft, soft, 0))
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    d = np.sqrt(((xx - a.shape[1] / 2) / (a.shape[1] / 2)) ** 2 + ((yy - a.shape[0] / 2) / (a.shape[0] / 2)) ** 2)
    a *= (1 - vignette * np.clip(d - 0.35, 0, 1) ** 1.6)[..., None]
    rng = np.random.default_rng(seed)
    a += rng.normal(0, grain, a.shape[:2])[..., None]
    return np.clip(a, 0, 255).astype(np.uint8)


def fisheye(a, k=0.38, zoom=1.0):
    """Barrel distortion: each output pixel samples the source further out the further it is from the centre."""
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx, ny = (xx - w / 2) / (w / 2), (yy - h / 2) / (w / 2)
    r2 = nx * nx + ny * ny
    f = (1 + k * r2) / zoom
    sx, sy = nx * f * (w / 2) + w / 2, ny * f * (w / 2) + h / 2
    out = np.stack([ndimage.map_coordinates(a[..., c], [sy, sx], order=1, mode='constant', cval=0) for c in range(3)], -1)
    return out


def peephole(a, r_frac=0.43, ring='#2a1a10'):
    """Circular peephole: fisheye inside a dark ring, black outside."""
    h, w = a.shape[:2]
    b = fisheye(a, 0.55, 1.05)
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt((xx - w / 2) ** 2 + (yy - h / 2) ** 2) / (h * r_frac)
    inside = np.clip((1 - r) * 60, 0, 1)
    shade = np.clip(1 - np.clip(r - 0.62, 0, 1) * 1.9, 0, 1) ** 1.4
    out = b * (inside * shade)[..., None]
    ringm = np.exp(-((r - 1.0) / 0.012) ** 2)
    rc = np.array([int(ring[i:i + 2], 16) for i in (1, 3, 5)], np.float32)
    out = out * (1 - ringm[..., None]) + rc * ringm[..., None] * 0.9
    return out


def from_np(a):
    a = np.ascontiguousarray(np.dstack([a.astype(np.uint8), np.full(a.shape[:2], 255, np.uint8)]))
    return skia.Image.fromarray(a, colorType=skia.kRGBA_8888_ColorType)
