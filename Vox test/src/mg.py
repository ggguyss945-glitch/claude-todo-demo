"""Tiny procedural motion-graphics engine built on skia-python.

Everything is drawn from code: shapes, type, textures and camera moves.
Design space is 1080x1920 (portrait); frames are rendered at a higher
output resolution by scaling the canvas.
"""
import functools
import json
import math
import os

import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONT_DIR = os.path.join(ROOT, "assets", "fonts")

W, H = 1080, 1920


# ----------------------------------------------------------------- maths ---
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def prog(t, a, b):
    """Normalised progress of t through [a, b]."""
    if b == a:
        return 1.0 if t >= b else 0.0
    return clamp((t - a) / (b - a))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out_cubic(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_cubic(x):
    x = clamp(x)
    return x ** 3


def ease_in_out_cubic(x):
    x = clamp(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out_quint(x):
    x = clamp(x)
    return 1 - (1 - x) ** 5


def ease_in_out_quint(x):
    x = clamp(x)
    return 16 * x ** 5 if x < 0.5 else 1 - (-2 * x + 2) ** 5 / 2


def ease_out_expo(x):
    x = clamp(x)
    return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)


def ease_in_out_expo(x):
    x = clamp(x)
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    return 2 ** (20 * x - 10) / 2 if x < 0.5 else (2 - 2 ** (-20 * x + 10)) / 2


def ease_out_back(x, s=1.70158):
    x = clamp(x)
    c3 = s + 1
    return 1 + c3 * (x - 1) ** 3 + s * (x - 1) ** 2


def ease_out_elastic(x):
    x = clamp(x)
    if x in (0.0, 1.0):
        return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi) / 3) + 1


def spring(x, damping=6.0, freq=2.2):
    """Damped spring settling from 0 to 1."""
    if x <= 0:
        return 0.0
    return 1 - math.exp(-damping * x) * math.cos(2 * math.pi * freq * x)


def env(t, a, b, fade_in=0.25, fade_out=0.25):
    """1 inside [a, b] with eased ramps at both ends."""
    return ease_out_cubic(prog(t, a, a + fade_in)) * (1 - ease_in_cubic(prog(t, b - fade_out, b)))


def hash01(*args):
    """Deterministic pseudo-random number in [0, 1)."""
    h = 0
    for a in args:
        h = (h * 1000003) ^ int(a * 9973 + 17)
        h &= 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 0x5BD1E995) & 0xFFFFFFFF
    h ^= h >> 15
    return (h & 0xFFFFFF) / float(0x1000000)


def noise1(x, seed=0):
    """Smooth 1D value noise in [-1, 1]."""
    i = math.floor(x)
    f = x - i
    a = hash01(i, seed) * 2 - 1
    b = hash01(i + 1, seed) * 2 - 1
    return lerp(a, b, smooth(f))


# ---------------------------------------------------------------- colour ---
def hexc(h, a=1.0):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return skia.ColorSetARGB(int(clamp(a) * 255), r, g, b)


def mix(h1, h2, t, a=1.0):
    h1, h2 = h1.lstrip("#"), h2.lstrip("#")
    c = [int(lerp(int(h1[i:i + 2], 16), int(h2[i:i + 2], 16), clamp(t))) for i in (0, 2, 4)]
    return skia.ColorSetARGB(int(clamp(a) * 255), *c)


def rgb_hex(r, g, b):
    return "#%02x%02x%02x" % (int(r), int(g), int(b))


def paint(color="#000000", a=1.0, stroke=None, cap="round", join="round", aa=True, blend=None,
          shader=None, blur=0.0, effect=None):
    p = skia.Paint(AntiAlias=aa)
    p.setColor(hexc(color, a) if isinstance(color, str) else color)
    if isinstance(color, int) and a < 1:
        p.setAlphaf(p.getAlphaf() * a)
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap({"round": skia.Paint.kRound_Cap, "butt": skia.Paint.kButt_Cap,
                        "square": skia.Paint.kSquare_Cap}[cap])
        p.setStrokeJoin({"round": skia.Paint.kRound_Join, "miter": skia.Paint.kMiter_Join,
                         "bevel": skia.Paint.kBevel_Join}[join])
    if blend is not None:
        p.setBlendMode(blend)
    if shader is not None:
        p.setShader(shader)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if effect is not None:
        p.setPathEffect(effect)
    return p


def linear(x0, y0, x1, y1, colors, pos=None):
    cols = [hexc(c) if isinstance(c, str) else c for c in colors]
    return skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)], cols, pos)


def radial(cx, cy, r, colors, pos=None):
    cols = [hexc(c) if isinstance(c, str) else c for c in colors]
    return skia.GradientShader.MakeRadial(skia.Point(cx, cy), r, cols, pos)


# ------------------------------------------------------------------ type ---
def _tag(s):
    return int.from_bytes(s.encode(), "big")


@functools.lru_cache(maxsize=None)
def typeface(name, wght=None, wdth=None, opsz=None):
    tf = skia.Typeface.MakeFromFile(os.path.join(FONT_DIR, name))
    if tf is None:
        raise FileNotFoundError(name)
    axes = [(k, v) for k, v in (("wght", wght), ("wdth", wdth), ("opsz", opsz)) if v is not None]
    if axes:
        C = skia.FontArguments.VariationPosition.Coordinate
        coords = skia.FontArguments.VariationPosition.Coordinates([C(_tag(k), float(v)) for k, v in axes])
        args = skia.FontArguments()
        args.setVariationDesignPosition(skia.FontArguments.VariationPosition(coords))
        tf = tf.makeClone(args)
    return tf


@functools.lru_cache(maxsize=4096)
def font(name, size, wght=None, wdth=None, opsz=None):
    f = skia.Font(typeface(name, wght, wdth, opsz), size)
    f.setSubpixel(True)
    f.setHinting(skia.FontHinting.kNone)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setLinearMetrics(True)
    return f


def text_width(s, f, tracking=0.0):
    if not s:
        return 0.0
    if tracking == 0:
        return f.measureText(s)
    g = f.textToGlyphs(s)
    return sum(f.getWidths(g)) + tracking * (len(g) - 1)


def text_blob(s, f, tracking=0.0):
    if tracking == 0:
        return skia.TextBlob.MakeFromString(s, f), f.measureText(s)
    g = f.textToGlyphs(s)
    ws = f.getWidths(g)
    xs, x = [], 0.0
    for w_ in ws:
        xs.append(x)
        x += w_ + tracking
    return skia.TextBlob.MakeFromPosTextH(s, xs, 0, f), x - tracking


def draw_text(c, s, x, y, f, p, align="left", tracking=0.0):
    """Draw text with baseline at y. Returns the text width."""
    if not s:
        return 0.0
    blob, w_ = text_blob(s, f, tracking)
    if align == "center":
        x -= w_ / 2
    elif align == "right":
        x -= w_
    c.drawTextBlob(blob, x, y, p)
    return w_


def cap_height(f):
    m = f.getMetrics()
    return -m.fCapHeight if m.fCapHeight < 0 else m.fCapHeight


# --------------------------------------------------------------- shapes ---
def rect(x, y, w, h):
    return skia.Rect.MakeXYWH(x, y, w, h)


def rrect(c, x, y, w, h, r, p):
    c.drawRRect(skia.RRect.MakeRectXY(rect(x, y, w, h), r, r), p)


def poly(pts, close=True):
    path = skia.Path()
    path.moveTo(*pts[0])
    for pt in pts[1:]:
        path.lineTo(*pt)
    if close:
        path.close()
    return path


def trim(path, a, b):
    """Return a copy of `path` trimmed to [a, b] of its length."""
    a, b = clamp(a), clamp(b)
    if b <= a:
        return skia.Path()
    if a <= 0 and b >= 1:
        return path
    out = skia.Path()
    meas = skia.PathMeasure(path, False)
    total = []
    while True:
        total.append(meas.getLength())
        if not meas.nextContour():
            break
    L = sum(total)
    meas = skia.PathMeasure(path, False)
    s0, s1 = a * L, b * L
    acc = 0.0
    for seg_len in total:
        lo, hi = max(s0 - acc, 0), min(s1 - acc, seg_len)
        if hi > lo:
            meas.getSegment(lo, hi, out, True)
        acc += seg_len
        meas.nextContour()
    return out


def star(cx, cy, r1, r2, n=5, rot=-math.pi / 2):
    pts = []
    for i in range(n * 2):
        r = r1 if i % 2 == 0 else r2
        a = rot + i * math.pi / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return poly(pts)


# ------------------------------------------------------------- textures ---
def _fbm(h, w, octaves, seed, base=4):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh, gw = base * 2 ** o + 1, int(base * 2 ** o * w / h) + 2
        g = rng.standard_normal((gh, gw)).astype(np.float32)
        img = skia.Image.fromarray(np.dstack([np.clip(g * 40 + 128, 0, 255)] * 3 +
                                             [np.full_like(g, 255)]).astype(np.uint8))
        img = img.resize(w, h, skia.SamplingOptions(skia.FilterMode.kLinear))
        arr = img.toarray()[..., 0].astype(np.float32) / 255 - 0.5
        out += arr * amp
        tot += amp
        amp *= 0.55
    return out / tot


def paper_texture(w, h, seed=1, strength=1.0, tint=(243, 237, 226)):
    """Cream paper: soft blotches + fibres + fine tooth. Returns skia.Image."""
    rng = np.random.default_rng(seed)
    blot = _fbm(h, w, 5, seed, base=3)
    tooth = rng.standard_normal((h, w)).astype(np.float32)
    # directional fibres
    fib = rng.standard_normal((h // 2, w // 8)).astype(np.float32)
    fimg = skia.Image.fromarray(np.dstack([np.clip(fib * 50 + 128, 0, 255)] * 3 +
                                          [np.full_like(fib, 255)]).astype(np.uint8))
    fimg = fimg.resize(w, h, skia.SamplingOptions(skia.FilterMode.kLinear))
    fib = fimg.toarray()[..., 0].astype(np.float32) / 255 - 0.5
    v = 1 + strength * (blot * 0.10 + fib * 0.025 + tooth * 0.018)
    rgb = np.stack([np.clip(tint[i] * v, 0, 255) for i in range(3)], -1)
    a = np.full((h, w, 1), 255, np.float32)
    return skia.Image.fromarray(np.concatenate([rgb, a], -1).astype(np.uint8))


def grain_frames(w, h, n=6, seed=7, amount=10.0):
    """Monochrome film-grain layers centred on mid grey (for overlay blending)."""
    rng = np.random.default_rng(seed)
    frames = []
    for _ in range(n):
        g = rng.standard_normal((h // 2, w // 2)).astype(np.float32) * amount + 128
        g = np.clip(g, 0, 255).astype(np.uint8)
        img = skia.Image.fromarray(np.dstack([g, g, g, np.full_like(g, 255)]))
        frames.append(img.resize(w, h, skia.SamplingOptions(skia.FilterMode.kLinear)))
    return frames


def vignette(c, w, h, strength=0.35, color="#000000"):
    p = paint()
    p.setShader(radial(w / 2, h / 2, math.hypot(w, h) * 0.62,
                       [hexc(color, 0), hexc(color, 0), hexc(color, strength)], [0, 0.55, 1]))
    c.drawRect(rect(0, 0, w, h), p)


# ----------------------------------------------------------- transcript ---
def load_words():
    with open(os.path.join(ROOT, "transcript", "words.json")) as fh:
        return json.load(fh)


def word_time(words, text, after=0.0):
    """Start time of the first word matching `text` at or after `after`."""
    text = text.lower().strip(".,")
    for w_ in words:
        if w_["s"] >= after - 1e-6 and w_["w"].lower().strip(".,!?") == text:
            return w_["s"]
    raise KeyError(f"{text} after {after}")
