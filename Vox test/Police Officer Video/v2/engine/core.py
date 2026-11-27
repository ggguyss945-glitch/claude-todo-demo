"""engine.core: drawing primitives, easing, noise and textures.

Everything is drawn in a 1920x1080 DESIGN space with skia; the engine scales to the render size.

Render size
    set_render_size(w, h)      configure output size (default 2560x1440); tests use 960x540
    CFG.rw, CFG.rh, CFG.k      current render size and scale (render px per design px)
    DW, DH                     1920, 1080 design space

Colours
    col(hex, a=255) -> skia colour     mix(hex_a, hex_b, k) -> hex     rgb(hex) -> (r, g, b) ints
    LINE = '#1d1f26' (measured outline colour), SKIN = pale palette list

Geometry (skia.Path): smooth(pts, closed, k), poly(pts, closed), rect, rrect, oval, ring, inter/union/minus, moved(path, dx, dy),
    scaled(path, sx, sy, cx, cy)

Easing (u in 0..1 unless noted): ease (smoothstep), lerp, prog(t, a, b), clamp, ease_in_out, ease_in_cubic, ease_out_cubic,
    ease_out_quad, ease_out_back(u, s), ease_push (reference push-in profile: linear with slight ease-out, no ease-in),
    spring(t, freq, damp) (0->1 with overshoot, t in seconds), EASES[name], ease_fn(name_or_fn)

Noise: noise1(t, seed=0, octaves=2) smooth value noise in [-1, 1] (scalar or numpy array); hash01(i, seed) deterministic random.

Textures: tex(name) cached tileable 512x512 grey texture (numpy float 0..1). Names: grunge, fabric, plaster, wood, asphalt,
    paper, skin, noise.  Pen.texture(path, name, alpha, blend, scale, angle) paints one onto a shape.

Pen(canvas, lw=4.0): fill, line, seg, shape, shade, glow, grad, wash (v1 API) plus
    texture, shadow (soft drop shadow), rim (rim light crescent), linear / radial (multi-stop gradients),
    cone (light cone), dashed (dashed outline), ellipse_glow.
Text: text(cv, s, x, y, weight, size, c, a, spacing, align, shadow) -> width;  text_width(...);  wrap(s, weight, size, maxw, spacing)
    typeface(weight) with MontserratLC 600/700/800/900 (Latin + Cyrillic).
"""
import math, os
import numpy as np
import cv2
import skia

DW, DH = 1920, 1080
LINE = '#1d1f26'
SKIN = ['#c0aa9e', '#b89e90', '#ac9585', '#b6947e']
SKIN_SHADE = '#8c746a'
FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'fonts')


class _Cfg:
    rw, rh = 2560, 1440

    @property
    def k(self):
        return self.rw / DW

    @property
    def size(self):
        return self.rw, self.rh


CFG = _Cfg()
_size_listeners = []


def set_render_size(w, h):
    """Set the output size (any 16:9 size; 2560x1440 for the film, 960x540 for tests). Clears size-dependent caches."""
    CFG.rw, CFG.rh = int(w), int(h)
    for f in _size_listeners: f()


def on_size_change(f):
    _size_listeners.append(f); return f


# ------------------------------------------------------------------ colours
_tf = {}


def rgb(h):
    if isinstance(h, (tuple, list)): return tuple(int(v) for v in h[:3])
    h = h.lstrip('#'); return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def col(h, a=255):
    r, g, b = rgb(h); return skia.Color(r, g, b, int(max(0, min(255, a))))


def mix(a, b, k):
    a, b = rgb(a), rgb(b); k = max(0.0, min(1.0, k))
    return '#%02x%02x%02x' % tuple(int(round(a[i] * (1 - k) + b[i] * k)) for i in range(3))


def typeface(weight):
    if weight not in _tf:
        name = f'MontserratLC-{weight}.ttf'
        if not os.path.exists(os.path.join(FONTS, name)): name = f'Montserrat-{weight}.ttf'
        _tf[weight] = skia.Typeface.MakeFromFile(os.path.join(FONTS, name))
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


def ring(cx, cy, r0, r1):
    return minus(oval(cx, cy, r1), oval(cx, cy, r0))


def inter(a, b): return skia.Op(a, b, skia.PathOp.kIntersect_PathOp)
def union(a, b): return skia.Op(a, b, skia.PathOp.kUnion_PathOp)
def minus(a, b): return skia.Op(a, b, skia.PathOp.kDifference_PathOp)


def moved(path, dx, dy):
    q = skia.Path(path); q.offset(dx, dy); return q


def scaled(path, sx, sy=None, cx=0.0, cy=0.0):
    sy = sx if sy is None else sy
    m = skia.Matrix(); m.setScale(sx, sy, cx, cy); q = skia.Path(path); q.transform(m); return q


# ------------------------------------------------------------------ easing
def clamp(x, a=0.0, b=1.0): return a if x < a else (b if x > b else x)
def lerp(a, b, k): return a + (b - a) * k
def prog(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def linear(x): return clamp(x)


def ease_in_out(x):
    x = clamp(x); return 4 * x * x * x if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_in_cubic(x): x = clamp(x); return x * x * x
def ease_out_cubic(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_out_quad(x): x = clamp(x); return 1 - (1 - x) ** 2
def ease_in_quad(x): x = clamp(x); return x * x


def ease_out_back(x, s=1.70158):
    x = clamp(x); x1 = x - 1; return 1 + (s + 1) * x1 ** 3 + s * x1 ** 2


def ease_push(x):
    """Reference push-in profile (VISUAL_SPEC b): already moving on frame 1, near-linear, slight ease-out."""
    x = clamp(x); return 1 - (1 - x) ** 1.15


def spring(t, freq=2.2, damp=0.38):
    """Damped spring step response, 0 at t<=0 settling to 1 (overshoots). t in seconds."""
    if t <= 0: return 0.0
    w = 2 * math.pi * freq; z = clamp(damp, 0.01, 0.99); wd = w * math.sqrt(1 - z * z)
    return 1 - math.exp(-z * w * t) * (math.cos(wd * t) + z / math.sqrt(1 - z * z) * math.sin(wd * t))


EASES = {'lin': linear, 'linear': linear, 'in_out': ease_in_out, 'smooth': ease, 'out': ease_out_cubic, 'out_cubic': ease_out_cubic,
         'in': ease_in_cubic, 'in_cubic': ease_in_cubic, 'out_quad': ease_out_quad, 'in_quad': ease_in_quad, 'back': ease_out_back,
         'push': ease_push, 'hold': lambda x: 0.0, 'step': lambda x: float(x >= 1.0)}


def ease_fn(e):
    return e if callable(e) else EASES[e or 'in_out']


# ------------------------------------------------------------------ noise
_ntab = {}


def _table(seed):
    if seed not in _ntab: _ntab[seed] = np.random.default_rng(1000 + int(seed)).uniform(-1, 1, 4096)
    return _ntab[seed]


def noise1(t, seed=0, octaves=2):
    """Smooth 1D value noise, range about [-1, 1], ~1 feature per unit of t. Works on floats and numpy arrays."""
    tab = _table(seed); out = 0.0; amp = 1.0; norm = 0.0; f = 1.0
    arr = np.asarray(t, dtype=np.float64)
    for o in range(octaves):
        x = arr * f + o * 37.13
        i = np.floor(x); u = x - i; i = i.astype(np.int64)
        u = u * u * u * (u * (u * 6 - 15) + 10)
        a = tab[i % 4096]; b = tab[(i + 1) % 4096]
        out = out + amp * (a + (b - a) * u); norm += amp; amp *= 0.5; f *= 2.0
    out = out / norm * 1.25
    return float(out) if np.ndim(out) == 0 else out


def hash01(i, seed=0):
    """Deterministic pseudo-random in [0, 1) for an integer (or array)."""
    x = (np.asarray(i, dtype=np.uint64) * np.uint64(2654435761) + np.uint64(seed * 97 + 13)) % np.uint64(4294967296)
    x = (x ^ (x >> np.uint64(13))) * np.uint64(1274126177) % np.uint64(4294967296)
    v = (x % np.uint64(1000003)).astype(np.float64) / 1000003.0
    return float(v) if np.ndim(v) == 0 else v


# ------------------------------------------------------------------ textures (tileable, procedural, cached)
_texc = {}


def _spec_noise(n, beta, seed, aniso=1.0):
    rng = np.random.default_rng(seed)
    F = np.fft.rfft2(rng.standard_normal((n, n)))
    fy = np.fft.fftfreq(n)[:, None]; fx = np.fft.rfftfreq(n)[None, :] * aniso
    f = np.sqrt(fx * fx + fy * fy); f[0, 0] = 1.0
    F = F * f ** (-beta / 2.0); F[0, 0] = 0
    a = np.fft.irfft2(F, s=(n, n)); return (a - a.mean()) / (a.std() + 1e-9)


def _norm01(a, lo=None, hi=None):
    lo = np.percentile(a, 1) if lo is None else lo; hi = np.percentile(a, 99) if hi is None else hi
    return np.clip((a - lo) / (hi - lo + 1e-9), 0, 1)


def tex(name, n=512):
    """Cached tileable grey texture (float32 HxW in 0..1, mean ~0.5 = neutral for overlay blends)."""
    key = (name, n)
    if key in _texc: return _texc[key]
    s = abs(hash(name)) % 997
    if name == 'grunge':
        lo = _spec_noise(n, 2.4, s); hi = _spec_noise(n, 1.3, s + 1)
        blot = np.clip((lo - 0.6) * 1.2, 0, 1)
        g = 0.5 + 0.12 * hi - 0.35 * blot + 0.06 * lo
    elif name == 'fabric':
        y, x = np.mgrid[0:n, 0:n] / n * 2 * np.pi * 64
        weave = np.sin(x) * np.sin(y)
        g = 0.5 + 0.10 * weave + 0.07 * _spec_noise(n, 1.0, s) + 0.06 * _spec_noise(n, 2.2, s + 2)
    elif name == 'plaster':
        g = 0.5 + 0.09 * _spec_noise(n, 1.7, s) + 0.05 * _spec_noise(n, 0.6, s + 3)
    elif name == 'wood':
        streak = _spec_noise(n, 2.0, s, aniso=12.0)
        y = np.mgrid[0:n, 0:n][0] / n
        rings = np.sin((y * 18 + streak * 0.35) * 2 * np.pi)
        g = 0.5 + 0.12 * rings * 0.6 + 0.12 * streak + 0.04 * _spec_noise(n, 0.8, s + 4)
    elif name == 'asphalt':
        sp = _spec_noise(n, 0.2, s); pebble = np.clip(sp - 1.6, 0, 2)
        g = 0.5 + 0.06 * sp + 0.25 * pebble - 0.08 * np.clip(-sp - 1.8, 0, 2) + 0.08 * _spec_noise(n, 2.2, s + 5)
    elif name == 'paper':
        g = 0.5 + 0.05 * _spec_noise(n, 1.0, s) + 0.05 * _spec_noise(n, 1.0, s + 6, aniso=6.0) + 0.04 * _spec_noise(n, 2.0, s + 7)
    elif name == 'skin':
        rng = np.random.default_rng(s); dots = np.zeros((n, n), np.float32)
        pts = rng.integers(0, n, (int(n * n / 90), 2))
        dots[pts[:, 0], pts[:, 1]] = 1.0
        dots = cv2.GaussianBlur(np.tile(dots, (3, 3)), (0, 0), 0.9)[n:2 * n, n:2 * n]
        dots = dots / (dots.max() + 1e-9)
        g = 0.5 - 0.22 * dots + 0.05 * _spec_noise(n, 2.4, s + 8) + 0.025 * _spec_noise(n, 1.0, s + 9)
    else:  # 'noise'
        g = 0.5 + 0.15 * _spec_noise(n, 1.0, s)
    g = np.clip(g, 0, 1).astype(np.float32)
    _texc[key] = g
    return g


def _tex_image(name, blend):
    key = ('img', name, blend)
    if key not in _texc:
        g = tex(name)
        if blend == 'multiply': g = 1.0 - np.clip((0.5 - g) * 2.0, 0, 1)       # only darker-than-mid areas darken
        elif blend == 'screen': g = np.clip((g - 0.5) * 2.0, 0, 1)
        v = (g * 255).astype(np.uint8)
        arr = np.dstack([v, v, v, np.full_like(v, 255)])
        _texc[key] = skia.Image.fromarray(np.ascontiguousarray(arr), skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType)
    return _texc[key]


_BLEND = {'multiply': skia.BlendMode.kMultiply, 'overlay': skia.BlendMode.kOverlay, 'softlight': skia.BlendMode.kSoftLight,
          'screen': skia.BlendMode.kScreen, 'normal': skia.BlendMode.kSrcOver, 'add': skia.BlendMode.kPlus,
          'color': skia.BlendMode.kColor, 'darken': skia.BlendMode.kDarken, 'lighten': skia.BlendMode.kLighten}
_LIN = skia.SamplingOptions(skia.FilterMode.kLinear)


def _stops(stops):
    """[c, c, ...] or [(pos, c), (pos, c, alpha), ...] -> (colors, positions)."""
    cs, ps = [], []
    for i, s in enumerate(stops):
        if isinstance(s, str):
            cs.append(col(s)); ps.append(i / max(1, len(stops) - 1))
        else:
            ps.append(float(s[0])); cs.append(col(s[1], s[2] if len(s) > 2 else 255))
    return cs, ps


def _stops_key(stops):
    out = []
    for i, s in enumerate(stops):
        if isinstance(s, str): out.append((round(i / max(1, len(stops) - 1), 4), s.lower(), 255.0))
        else: out.append((round(float(s[0]), 4), s[1].lower(), round(float(s[2]) if len(s) > 2 else 255.0, 1)))
    return tuple(out)


_gimg = {}


def _ramp(key, t):
    """Premultiplied BGRA uint8 colours of a stop list at positions t (array)."""
    ps = np.array([k[0] for k in key]); cs = np.array([rgb(k[1]) for k in key], np.float64); al = np.array([k[2] for k in key])
    o = np.argsort(ps, kind='stable'); ps, cs, al = ps[o], cs[o], al[o]
    a = np.interp(t, ps, al) / 255.0
    ch = [np.interp(t, ps, cs[:, c]) * a for c in (2, 1, 0)]                  # B, G, R premultiplied
    return np.clip(np.stack(ch + [a * 255.0], -1) + 0.5, 0, 255).astype(np.uint8)


def _grad_image(key, kind, n=256):
    k2 = (key, kind, n)
    im = _gimg.get(k2)
    if im is None:
        if kind == 'v':
            arr = np.repeat(_ramp(key, (np.arange(n) + 0.5) / n)[:, None, :], 4, axis=1)     # n x 4 (1-px images fail)
        elif kind == 'h':
            arr = np.repeat(_ramp(key, (np.arange(n) + 0.5) / n)[None, :, :], 4, axis=0)     # 4 x n
        else:
            yy, xx = np.mgrid[0:n, 0:n]
            r = np.sqrt((xx + 0.5 - n / 2) ** 2 + (yy + 0.5 - n / 2) ** 2) / (n / 2)
            arr = _ramp(key, np.clip(r, 0, 1))
        arr = np.ascontiguousarray(arr)
        img = skia.Image.fromarray(arr, skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType)
        if img is None: raise RuntimeError('gradient image creation failed %r' % (arr.shape,))
        im = (img, arr)
        if len(_gimg) > 600: _gimg.clear()
        _gimg[k2] = im
    return im[0]


def _axis_aligned(cv):
    m = cv.getTotalMatrix(); return m.rectStaysRect()


class Pen:
    """Drawing helper on a skia canvas in design coordinates. lw: default outline width (design px)."""

    def __init__(self, cv, lw=4.0): self.cv, self.lw = cv, lw

    # ---- v1 API
    def fill(self, path, c, a=255, blur=0):
        p = skia.Paint(Color=col(c, a), AntiAlias=True)
        if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
        self.cv.drawPath(path, p)

    def line(self, path, w=None, c=LINE, a=255, cap='round', blur=0):
        p = skia.Paint(Color=col(c, a), AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w or self.lw,
                       StrokeJoin=skia.Paint.kRound_Join,
                       StrokeCap={'round': skia.Paint.kRound_Cap, 'butt': skia.Paint.kButt_Cap, 'square': skia.Paint.kSquare_Cap}[cap])
        if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
        self.cv.drawPath(path, p)

    def seg(self, a, b, w=None, c=LINE, alpha=255): self.line(poly([a, b], False), w, c, alpha)

    def shape(self, path, c, w=None, lc=LINE):
        self.fill(path, c); self.line(path, w, lc)

    def shade(self, clip, path, c, a=255, blur=0):
        self.cv.save(); self.cv.clipPath(clip, doAntiAlias=True); self.fill(path, c, a, blur); self.cv.restore()

    def glow(self, x, y, r, c, a=150):
        self.radial(None, x, y, r, [(0, c, a), (1, c, 0)], clip=False)

    def grad(self, x0, y0, x1, y1, c0, c1, vertical=True, path=None):
        if vertical: self.linear(path if path is not None else rect(x0, y0, x1 - x0, y1 - y0), x0, y0, x0, y1, [c0, c1])
        else: self.linear(path if path is not None else rect(x0, y0, x1 - x0, y1 - y0), x0, y0, x1, y0, [c0, c1])

    def wash(self, c, a, blend='normal'):
        p = skia.Paint(Color=col(c, a)); p.setBlendMode(_BLEND[blend])
        self.cv.drawRect(skia.Rect.MakeLTRB(-DW * 3, -DH * 3, DW * 4, DH * 4), p)

    # ---- new
    def linear(self, path, x0, y0, x1, y1, stops, a=1.0):
        """Multi-stop linear gradient fill (clamped beyond the end points). path None = everything visible.
        stops: ['#hex', ...] or [(pos, '#hex', alpha), ...]. Vertical/horizontal gradients use a fast stretched-image path."""
        cv = self.cv
        vert, horz = abs(x1 - x0) < 1e-6, abs(y1 - y0) < 1e-6
        if (vert or horz) and _axis_aligned(cv) and not (vert and horz):
            key = _stops_key(stops)
            if (vert and y1 < y0) or (horz and x1 < x0):
                key = tuple(sorted(((round(1 - p_, 4), c_, a_) for p_, c_, a_ in key), key=lambda k: k[0]))
                x0, x1, y0, y1 = min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1)
            cv.save()
            if path is not None:
                cv.clipPath(path, skia.ClipOp.kIntersect, True); bb = path.getBounds()
            else:
                bb = cv.getLocalClipBounds()
            bx0, by0, bx1, by1 = bb.left() - 1, bb.top() - 1, bb.right() + 1, bb.bottom() + 1
            paint = skia.Paint(AntiAlias=False); paint.setAlphaf(clamp(a))
            first, last = key[0], key[-1]
            k0 = sorted(key, key=lambda k: k[0])
            c_first, c_last = k0[0], k0[-1]
            if vert:
                img = _grad_image(key, 'v')
                if by0 < y0: self._solid(skia.Rect.MakeLTRB(bx0, by0, bx1, y0), c_first, a)
                if by1 > y1: self._solid(skia.Rect.MakeLTRB(bx0, y1, bx1, by1), c_last, a)
                cv.drawImageRect(img, skia.Rect.MakeLTRB(0, 0, 4, 256), skia.Rect.MakeLTRB(bx0, y0, bx1, y1), _LIN, paint,
                                 skia.Canvas.kFast_SrcRectConstraint)
            else:
                img = _grad_image(key, 'h')
                if bx0 < x0: self._solid(skia.Rect.MakeLTRB(bx0, by0, x0, by1), c_first, a)
                if bx1 > x1: self._solid(skia.Rect.MakeLTRB(x1, by0, bx1, by1), c_last, a)
                cv.drawImageRect(img, skia.Rect.MakeLTRB(0, 0, 256, 4), skia.Rect.MakeLTRB(x0, by0, x1, by1), _LIN, paint,
                                 skia.Canvas.kFast_SrcRectConstraint)
            cv.restore()
            return
        cs, ps = _stops(stops)
        p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(x0, y0), (x1, y1)], cs, ps), Alphaf=a)
        if path is None: cv.drawPaint(p)
        else: cv.drawPath(path, p)

    def _solid(self, r, k, a):
        if k[2] * a <= 0.5: return
        self.cv.drawRect(r, skia.Paint(Color=col(k[1], k[2] * clamp(a)), AntiAlias=False))

    def radial(self, path, cx, cy, r, stops, a=1.0, sy=1.0, blend='normal', clip=True):
        """Multi-stop radial gradient (sy squashes it into an ellipse). path None = everything visible (or just the
        gradient's square when clip=False). Normal blending on an unrotated canvas uses a fast stretched image."""
        cv = self.cv
        if blend == 'normal' and _axis_aligned(cv):
            key = _stops_key(stops)
            img = _grad_image(key, 'r')
            dst = skia.Rect.MakeLTRB(cx - r, cy - r * sy, cx + r, cy + r * sy)
            paint = skia.Paint(AntiAlias=False); paint.setAlphaf(clamp(a))
            last = sorted(key, key=lambda k: k[0])[-1]
            cv.save()
            if path is not None: cv.clipPath(path, skia.ClipOp.kIntersect, True)
            cv.drawImageRect(img, skia.Rect.MakeLTRB(0, 0, 256, 256), dst, _LIN, paint, skia.Canvas.kFast_SrcRectConstraint)
            if last[2] * a > 0.5 and (path is not None or clip):
                cv.clipRect(dst, skia.ClipOp.kDifference, False)
                bb = path.getBounds() if path is not None else cv.getLocalClipBounds()
                self._solid(bb, last, a)
            cv.restore()
            return
        cs, ps = _stops(stops)
        m = skia.Matrix(); m.setScale(1.0, sy, cx, cy)
        p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((cx, cy), r, cs, ps, skia.TileMode.kClamp, 0, m), Alphaf=a)
        p.setBlendMode(_BLEND[blend])
        if path is None: cv.drawPaint(p)
        else: cv.drawPath(path, p)

    def ellipse_glow(self, cx, cy, rx, ry, c, a=140, blend='normal'):
        self.radial(None, cx, cy, rx, [(0, c, a), (0.45, c, a * 0.45), (1, c, 0)], sy=ry / rx, blend=blend, clip=False)

    def texture(self, path, name, alpha=0.25, blend='overlay', scale=1.0, angle=0.0, dx=0.0, dy=0.0):
        """Paint a cached procedural texture (core.tex names) over a shape. blend: overlay | softlight | multiply | screen."""
        img = _tex_image(name, blend)
        m = skia.Matrix(); m.setScale(scale, scale); m.postRotate(angle); m.postTranslate(dx, dy)
        p = skia.Paint(AntiAlias=True, Shader=img.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat, _LIN, m), Alphaf=float(alpha))
        p.setBlendMode(_BLEND[blend])
        self.cv.drawPath(path, p)

    def shadow(self, path, dx=0.0, dy=8.0, blur=14.0, c='#000000', a=110):
        """Soft drop shadow of a shape (draw before the shape)."""
        self.cv.save(); self.cv.translate(dx, dy); self.fill(path, c, a, blur); self.cv.restore()

    def rim(self, path, lx=-1.0, ly=-0.6, w=6.0, c='#ffffff', a=90, blur=2.0):
        """Rim light: a crescent along the edge of `path` facing the light direction (lx, ly)."""
        n = math.hypot(lx, ly) or 1.0
        crescent = minus(path, moved(path, -lx / n * w, -ly / n * w))
        self.shade(path, crescent, c, a, blur)

    def cone(self, x, y, w0, w1, h, c='#ffd9a0', a=70, soft=30.0):
        """Soft light cone from (x, y) going down: top width w0, bottom width w1, height h, fading out (cached image)."""
        key = ('cone', int(w0), int(w1), int(h), c, int(a), int(soft))
        im = _gimg.get(key)
        pad = soft * 2.5 + 2
        W, H = w1 + 2 * pad, h + 2 * pad
        if im is None:
            d = 0.5
            arr = np.zeros((int(math.ceil(H * d)), int(math.ceil(W * d)), 4), np.uint8)
            s_ = surface_for(arr); c_ = s_.getCanvas(); c_.scale(d, d)
            ox = W / 2
            p = poly([(ox - w0 / 2, pad), (ox + w0 / 2, pad), (ox + w1 / 2, pad + h), (ox - w1 / 2, pad + h)])
            paint = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, pad), (0, pad + h)], [col(c, a), col(c, a * 0.4), col(c, 0)],
                                                                                        [0, 0.5, 1]))
            if soft: paint.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, soft * d))
            c_.drawPath(p, paint); del c_, s_
            im = (skia.Image.fromarray(arr, skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType), arr)
            _gimg[key] = im
        img = im[0]
        self.cv.drawImageRect(img, skia.Rect.MakeWH(img.width(), img.height()), skia.Rect.MakeXYWH(x - W / 2, y - pad, W, H), _LIN,
                              skia.Paint(), skia.Canvas.kFast_SrcRectConstraint)

    def dashed(self, path, w=3.0, c='#ffffff', a=255, on=14.0, off=9.0, phase=0.0):
        p = skia.Paint(Color=col(c, a), AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                       PathEffect=skia.DashPathEffect.Make([on, off], phase), StrokeCap=skia.Paint.kButt_Cap)
        self.cv.drawPath(path, p)


# ------------------------------------------------------------------ text
_FONTS = {}


def _font(weight, size):
    """Unhinted, subpixel-positioned font with linear metrics: glyph advances scale exactly with size, so letter-spaced
    small text (the header) keeps even spacing at every render size (hinted advances rounded narrow glyphs up)."""
    k = (weight, round(float(size), 3))
    f = _FONTS.get(k)
    if f is None:
        f = skia.Font(typeface(weight), size)
        f.setSubpixel(True); f.setHinting(skia.FontHinting.kNone); f.setLinearMetrics(True); f.setBaselineSnap(False)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        if len(_FONTS) > 400: _FONTS.clear()
        _FONTS[k] = f
    return f


def text_width(s, weight=600, size=30, spacing=0.0):
    f = _font(weight, size); g = f.textToGlyphs(s)
    return sum(f.getWidths(g)) + spacing * size * max(0, len(g) - 1)


def text(cv, s, x, y, weight=600, size=30, c='#ffffff', a=255, spacing=0.0, align='center', shadow=0.0, glow=None):
    """Draw text with its baseline at y. align: left | center | right. shadow: 0..1 soft drop shadow. glow: (hex, alpha, blur)."""
    if not s: return 0.0
    f = _font(weight, size)
    glyphs = f.textToGlyphs(s); widths = f.getWidths(glyphs)
    total = sum(widths) + spacing * size * (len(glyphs) - 1)
    x0 = x - total / 2 if align == 'center' else (x - total if align == 'right' else x)
    pos, cx = [], x0
    for w in widths: pos.append(skia.Point(cx, y)); cx += w + spacing * size
    blob = skia.TextBlob.MakeFromPosText(s, pos, f)
    if shadow:
        cv.drawTextBlob(blob, 0, size * 0.05, skia.Paint(Color=col('#000000', 200 * shadow * a / 255), AntiAlias=True,
                                                         MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, size * 0.14)))
    if glow:
        gc, ga, gb = glow
        cv.drawTextBlob(blob, 0, 0, skia.Paint(Color=col(gc, ga * a / 255), AntiAlias=True,
                                               MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, gb)))
    cv.drawTextBlob(blob, 0, 0, skia.Paint(Color=col(c, a), AntiAlias=True))
    return total


def wrap(s, weight, size, maxw, spacing=0.0):
    f = _font(weight, size); words = s.split(); lines, cur = [], ''
    for w in words:
        tryl = (cur + ' ' + w).strip()
        if f.measureText(tryl.replace('*', '')) + spacing * size * len(tryl) > maxw and cur: lines.append(cur); cur = w
        else: cur = tryl
    if cur: lines.append(cur)
    return lines


def surface_for(arr):
    """Wrap an HxWx4 uint8 numpy array (BGRA, premultiplied) as a skia surface (no copy)."""
    return skia.Surface(arr, skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType)


def image_from(arr, copy=False):
    """skia.Image over an HxWx4 uint8 BGRA premultiplied array (no copy by default: keep `arr` alive)."""
    return skia.Image.fromarray(arr, skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType, None, copy)
