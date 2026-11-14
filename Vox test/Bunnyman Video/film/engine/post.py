"""engine.post: grades and the film look (all uint8 OpenCV ops at work resolution, cached masks and textures).

Grade(name='night_blue', **overrides)   presets: GRADES = night_blue, porch_warm, interior_dim, red_alert, phone_dark, ir_night,
                                        doorbell_night (rich night colour: sodium key on navy), face_close, neutral
  params: exposure (stops), contrast (S-curve, 1 = flat), pivot, gamma (>1 brightens mids), shoulder (0..1 highlight roll-off),
          sat, wb (r, g, b gains = highlight tint), floor ('#hex' lifted, tinted blacks), mono (0..1) + tint ('#hex'),
          bloom (1.0 = reference halo on lamps; 0 = off), bloom_thr (0..255 on the pre-grade image; only small features
          above it bloom: draw light cores #fff8ee..#ffffff, keep eye whites / teeth <= #f0f0f0), vignette (mask value at r = 0.8 of the half diagonal; 1 = none),
          grain (std in levels; the references have none, keep <= 1.5: it mostly dithers dark gradients), soft (px sigma at 2560)
  g.with_(**kw) -> modified copy;  g.lerp(other, k) -> blend (e.g. climax creeping into red_alert)

Per-frame effects: pass post={...} to scene.render_frame:
  exposure (stops), sat (x), fade (0..1 to black), white (0..1 white flash), dim (0..1), red (0..1 blend to red_alert),
  mix (Grade, k), flash (police_flash(t) result), static (0..1 TV static, 2-6 frame scare flashes), glitch (0..1 RGB tear),
  blur (design px, whole-frame blur for rule-card backgrounds), vignette / bloom (override the grade's value)
  vhs (dict): a 1970s tape played on a CRT, applied at output resolution before the static / glitch / grain:
      dict(t=seconds (required: drives the wobble and the rolling tracking band), k=1 (overall), wobble=1 (per-line
      horizontal jitter + slow skew), track=0.35 (the rolling tracking-noise band; 1 = a bad tape), noise=1 (tape snow,
      dropouts), chroma=1 (colour bleed / shift), curve=1 (CRT glass curvature + rounded tube corners; 0 = flat),
      scan=1 (scanlines), glow=1 (phosphor glow), glass=1 (sheen on the glass), bezel=0..1 (the TV's bezel round the tube:
      the push-in from the living room lands on it), head=1 (head-switching noise at the bottom))

police_flash(t, strength=1.0, speed=1.0, mode='sweep'|'strobe', side=0.0) -> Flash: rotating red/blue light sweeps.
  Flash.light(xf) -> (r, b) 0..1 intensities at horizontal frame fraction xf (for sets that light walls in-scene).
"""
import math
import numpy as np
import cv2
from . import core
from .core import CFG, rgb, clamp, lerp

_GRADE_KEYS = ('exposure', 'contrast', 'pivot', 'gamma', 'shoulder', 'sat', 'wb', 'floor', 'mono', 'tint', 'bloom', 'bloom_thr',
               'bloom_r', 'vignette', 'grain', 'soft')
BASE = dict(exposure=0.0, contrast=1.0, pivot=0.25, gamma=1.0, shoulder=0.35, sat=1.0, wb=(1.0, 1.0, 1.0), floor='#000000',
            mono=0.0, tint='#ffffff', bloom=0.0, bloom_thr=236, bloom_r=12.0, vignette=1.0, grain=0.8, soft=0.0)

# Presets sit on the reference palettes (VISUAL_SPEC a): navy nights, warm sodium porch, desaturated mids, lifted dark floors.
GRADES = {
    'neutral': dict(),
    'night_blue': dict(contrast=1.12, pivot=0.2, gamma=0.94, sat=0.86, wb=(0.9, 0.96, 1.12), floor='#05070f', bloom=1.0,
                       bloom_thr=236, vignette=0.34, grain=0.9),
    'porch_warm': dict(contrast=1.1, pivot=0.22, gamma=0.96, sat=0.88, wb=(1.05, 1.0, 0.9), floor='#070609', bloom=1.0,
                       bloom_thr=236, vignette=0.34, grain=0.9),
    'interior_dim': dict(contrast=0.9, pivot=0.25, gamma=1.0, sat=0.82, wb=(0.94, 0.98, 1.08), floor='#0d0c13', bloom=0.0,
                         vignette=0.45, grain=0.8),
    'red_alert': dict(contrast=1.05, gamma=0.9, sat=1.2, mono=0.72, tint='#e8606a', wb=(1.08, 0.9, 0.92), floor='#0c0407',
                      bloom=0.8, bloom_thr=230, vignette=0.33, grain=0.9),
    'phone_dark': dict(contrast=1.08, gamma=0.9, sat=0.9, wb=(0.95, 0.97, 1.08), floor='#07060a', bloom=0.9, bloom_thr=230,
                       vignette=0.36, grain=0.8),
    'ir_night': dict(exposure=-0.25, contrast=1.18, pivot=0.3, gamma=1.0, sat=0.0, mono=1.0, tint='#dfe8e4', floor='#0b0d0d',
                     bloom=0.35, bloom_thr=240, vignette=0.5, grain=0.0, shoulder=0.6),
    # v2.1: the doorbell is the most-used view, so it carries full colour now (owner: 'ultra-level colours'): warm sodium
    # porch key against a deep navy floor, police red/blue at full strength. Lit-pixel S mean ~95-112 (fire ref 104-141).
    'doorbell_night': dict(contrast=1.1, pivot=0.25, gamma=0.98, sat=1.3, wb=(0.97, 1.0, 1.05), floor='#070b18', bloom=0.9,
                           bloom_thr=232, vignette=0.38, grain=0.0, shoulder=0.5),
    'face_close': dict(contrast=1.05, gamma=1.0, sat=0.9, wb=(1.0, 0.98, 1.02), floor='#0a0910', bloom=0.4, bloom_thr=240,
                       vignette=0.45, grain=0.8),
}


def _lerp_val(a, b, k):
    if isinstance(a, str): return core.mix(a, b, k)
    if isinstance(a, (tuple, list)): return tuple(lerp(x, y, k) for x, y in zip(a, b))
    return lerp(a, b, k)


class Grade:
    def __init__(self, name='night_blue', **kw):
        self.name = name
        self.p = dict(BASE); self.p.update(GRADES.get(name, {})); self.p.update(kw)

    def with_(self, **kw):
        g = Grade(self.name); g.p = dict(self.p); g.p.update(kw); return g

    def lerp(self, other, k):
        other = get_grade(other); k = clamp(k)
        g = Grade(self.name); g.p = {key: _lerp_val(self.p[key], other.p[key], k) for key in _GRADE_KEYS}
        return g

    def __getitem__(self, k): return self.p[k]

    def __repr__(self): return 'Grade(%r)' % self.name

    # ---- per-frame tables
    def lut(self, exposure=0.0, fade=0.0):
        p = self.p
        v = np.arange(256, dtype=np.float64) / 255.0
        lin = v ** 2.2 * 2.0 ** (p['exposure'] + exposure)
        sh = p['shoulder']
        if sh > 0:                                     # soft highlight roll-off instead of hard clipping
            knee = 1.0 - sh * 0.6
            over = np.maximum(lin - knee, 0)
            lin = np.where(lin > knee, knee + (1 - knee) * (1 - np.exp(-over / max(1e-6, 1 - knee))), lin)
        v = np.clip(lin, 0, 1) ** (1 / 2.2)
        c, pv = p['contrast'], p['pivot']
        if abs(c - 1) > 1e-3:
            lo = v < pv
            v = np.where(lo, pv * (np.maximum(v, 0) / pv) ** c, 1 - (1 - pv) * ((1 - v) / (1 - pv)) ** c)
        v = np.clip(v, 0, 1) ** (1.0 / p['gamma'])
        v = v * (1 - fade)
        return np.clip(v * 255 + 0.5, 0, 255).astype(np.uint8)

    def matrix(self, sat=1.0, white=0.0):
        """3x4 cv2.transform matrix in BGR order: mono tint, saturation, white balance, lifted floor, white flash."""
        p = self.p
        lw = np.array([0.2126, 0.7152, 0.0722])
        tint = np.array(rgb(p['tint'])) / 255.0
        mono = p['mono']
        M = (1 - mono) * np.eye(3) + mono * np.outer(tint / max(1e-6, (tint * lw).sum()) * 1.0, lw)
        s = p['sat'] * sat
        S = s * np.eye(3) + (1 - s) * np.outer(np.ones(3), lw)
        M = np.diag(p['wb']) @ S @ M
        fl = np.array(rgb(p['floor']), np.float64)
        M = M * (1 - fl / 255.0)[:, None]
        off = fl
        M = M * (1 - white); off = off * (1 - white) + 255 * white
        P = np.eye(3)[::-1]
        Mb = P @ M @ P; ob = off[::-1]
        return np.hstack([Mb, ob[:, None]]).astype(np.float32)


def get_grade(g):
    if g is None: return Grade('neutral')
    if isinstance(g, Grade): return g
    return Grade(g)


# ------------------------------------------------------------------ cached masks / textures
_c = {}
core.on_size_change(_c.clear)


def vignette_mask(v80, w, h, extra=None, extra_key=None):
    """u8 3ch mask (unity 200): exp(-k r^2.2), r = distance / half-diagonal, value v80 at r = 0.8; times an optional lens mask."""
    key = ('vig', round(v80, 3), w, h, extra_key)
    if key not in _c:
        if v80 >= 0.999: m = np.ones((h, w), np.float32)
        else:
            k = -math.log(max(1e-3, v80)) / 0.8 ** 2.2
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
            r = np.sqrt((xx + 0.5 - w / 2) ** 2 + (yy + 0.5 - h / 2) ** 2) / math.hypot(w / 2, h / 2)
            m = np.exp(-k * r ** 2.2)
        mm = np.clip(m * 200, 0, 255).astype(np.uint8)
        mm = cv2.merge([mm, mm, mm])
        if extra is not None: mm = cv2.multiply(mm, extra, scale=1 / 200.0)
        if len(_c) > 40: [_c.pop(k_) for k_ in [k_ for k_ in _c if k_[0] == 'vig'][:10]]
        _c[key] = mm
    return _c[key]


def _grain_tex(w, h):
    key = ('grain', w, h)
    if key not in _c:
        rng = np.random.default_rng(11)
        n = cv2.GaussianBlur(rng.normal(0, 1, (h + 64, w + 64)).astype(np.float32), (0, 0), 0.65)
        n = n / n.std() * 16.0
        g = np.clip(128 + n, 0, 255).astype(np.uint8)
        _c[key] = cv2.merge([g, g, g])
    return _c[key]


def _static_tex(w, h):
    key = ('static', w, h)
    if key not in _c:
        rng = np.random.default_rng(5)
        sw, sh = w // 2 + 32, h // 2 + 32
        n = rng.normal(0, 1, (sh, sw)).astype(np.float32) * 55
        rows = rng.normal(0, 1, (sh, 1)).astype(np.float32) * 22          # horizontal streaks
        g = np.clip(118 + n + rows, 0, 255).astype(np.uint8)
        g = cv2.resize(g, (sw * 2, sh * 2), interpolation=cv2.INTER_NEAREST)
        _c[key] = cv2.merge([g, g, g])
    return _c[key]


# ------------------------------------------------------------------ police lights
class Flash:
    """Red/blue rotating beacon light. field(w, h) -> float32 BGR intensity image (small)."""

    def __init__(self, t, strength=1.0, speed=1.0, mode='sweep', side=0.0, width=0.35):
        self.t, self.strength, self.speed, self.mode, self.side, self.width = t, strength, speed, mode, side, width

    def light(self, xf, yf=0.5):
        """(red, blue) intensity 0..~1 at frame fraction (xf, yf)."""
        t = self.t * self.speed
        if self.mode == 'strobe':
            ph = (t * 2.0) % 1.0
            def burst(p0): return 1.0 if (p0 <= ph < p0 + 0.07 or p0 + 0.12 <= ph < p0 + 0.19) else 0.0
            r, b = burst(0.0), burst(0.5)
            return r * self.strength, b * self.strength
        out = []
        for ph0, s0 in ((0.0, -1.0), (math.pi, 1.0)):
            phi = 2 * math.pi * 0.85 * t + ph0
            face = max(0.0, math.cos(phi)) ** 0.7
            xc = 0.5 + self.side * s0 * 0.15 + 0.75 * math.sin(phi)
            lobe = np.exp(-((np.asarray(xf) - xc) / self.width) ** 2)
            amb = 0.18 * (0.5 + 0.5 * math.cos(phi))
            out.append((face * lobe + amb) * self.strength * (0.85 + 0.3 * (1 - np.asarray(yf))))
        return out[0], out[1]

    def field(self, w=64, h=36):
        xs = (np.arange(w) + 0.5) / w; ys = (np.arange(h) + 0.5) / h
        X, Y = np.meshgrid(xs, ys)
        r, b = self.light(X, Y)
        r = np.broadcast_to(r, X.shape); b = np.broadcast_to(b, X.shape)
        red = np.array([0.18, 0.12, 1.0]); blue = np.array([1.0, 0.35, 0.10])       # BGR light colours
        return (r[..., None] * red + b[..., None] * blue).astype(np.float32)


class Spill(Flash):
    """A blinking coloured light washing in from one side of the frame (the delivery van's hazards in the climax):
    strength 0..1 (already multiplied by the blink), side -1 = from the left / +1 = from the right, colour BGR 0..1."""

    def __init__(self, strength=1.0, side=1.0, color=(0.10, 0.16, 1.0), reach=0.75):
        self.strength, self.side, self.color, self.reach = strength, side, np.array(color, np.float32), reach

    def field(self, w=64, h=36):
        xs = (np.arange(w) + 0.5) / w; ys = (np.arange(h) + 0.5) / h
        X, Y = np.meshgrid(xs, ys)
        u = X if self.side > 0 else 1 - X
        k = np.clip(1 - (1 - u) / self.reach, 0, 1) ** 1.6 * (0.75 + 0.25 * (1 - Y)) + 0.03
        return (k[..., None] * self.color * self.strength).astype(np.float32)


def police_flash(t, strength=1.0, speed=1.0, mode='sweep', side=0.0, width=0.35):
    return Flash(t, strength, speed, mode, side, width)


# ------------------------------------------------------------------ the pipeline pieces
def bloom_src(img, thr, tophat=90.0):
    """Bright pass at 1/4 res (float32, 0..1 = how far above the threshold) from the pre-grade picture. Only small bright
    features (lamp cores, bulbs, screens' hot spots) bloom: a morphological top-hat of `tophat` design px removes large
    bright areas, so pale faces, eye whites and teeth in close-ups never glow."""
    h, w = img.shape[:2]
    small = cv2.resize(img, (max(8, w // 4), max(8, h // 4)), interpolation=cv2.INTER_AREA).astype(np.float32)
    b = cv2.max(small - float(thr), 0.0) * (1.0 / max(1.0, 255.0 - thr))
    if tophat:
        k = int(max(3, tophat * small.shape[1] / 1920.0)) | 1
        b = cv2.morphologyEx(b, cv2.MORPH_TOPHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    return b


def bloom_glow(bright, strength, radius_design):
    """Soft glow (u8, bright-pass resolution): a narrow and a wide Gaussian. strength 1.0 = the reference halo
    (VISUAL_SPEC a: ~0.2 of peak at 2-6 px, ~0.04 at 30 px @1280 for a porch lamp)."""
    s = bright.shape[1] / 1920.0                               # small px per design px
    s1 = max(0.8, radius_design * 0.7 * s)
    k2 = int(max(3, radius_design * 5.0 * s * 2.5)) | 1        # stack blur ~ Gaussian sigma k / 2.5
    g = cv2.GaussianBlur(bright, (0, 0), s1) * 0.75 + cv2.stackBlur(bright, (k2, k2)) * 2.2
    return np.clip(g * (strength * 255.0), 0, 255).astype(np.uint8)


def bloom_add(img, bright, strength, radius_design):
    h, w = img.shape[:2]
    g = cv2.resize(bloom_glow(bright, strength, radius_design), (w, h), interpolation=cv2.INTER_LINEAR)
    return cv2.add(img, g)


def apply_grade(img, grade, fx, bright=None, lens_mask=None, lens_key=None, skip_vignette=False, lens_add=None):
    """img BGR u8 (work res). Returns graded BGR with bloom and vignette."""
    g = grade
    if fx.get('red'): g = g.lerp('red_alert', fx['red'])
    if fx.get('mix'): g = g.lerp(fx['mix'][0], fx['mix'][1])
    p = g.p
    fade = clamp(fx.get('fade', 0.0) + fx.get('dim', 0.0) * (1 - fx.get('fade', 0.0)))
    out = cv2.LUT(img, g.lut(fx.get('exposure', 0.0), fade))
    out = cv2.transform(out, g.matrix(fx.get('sat', 1.0), clamp(fx.get('white', 0.0))))
    bl = fx.get('bloom', p['bloom'])
    fl = fx.get('flash')
    v = fx.get('vignette', p['vignette'])
    if skip_vignette: v = 1.0
    h, w = out.shape[:2]
    add = None                                                # smooth additive light (bloom + flash haze) at 1/4 res
    if bl and bright is not None:
        add = bloom_glow(bright, bl * (1 - fade), p['bloom_r'])
    if fl is not None:
        sw, sh = max(16, w // 16), max(9, h // 16)
        fld = fl.field(sw, sh)
        aw, ah = (add.shape[1], add.shape[0]) if add is not None else (max(16, w // 4), max(9, h // 4))
        haze = cv2.resize(np.clip(fld * 26, 0, 255).astype(np.uint8), (aw, ah), interpolation=cv2.INTER_LINEAR)
        add = haze if add is None else cv2.add(add, haze)
    if add is not None:
        out = cv2.add(out, cv2.resize(add, (w, h), interpolation=cv2.INTER_LINEAR))
    if fl is not None:
        # police light gain and vignette combined at 1/16 res (both smooth): one full-res multiply (unity 128)
        gain = (1 + fld * 1.6) * _vig_small(v, sw, sh)[..., None]
        gain = cv2.resize(np.clip(gain * 128, 0, 255).astype(np.uint8), (w, h), interpolation=cv2.INTER_LINEAR)
        out = cv2.multiply(out, gain, scale=1 / 128.0)
        if lens_mask is not None: out = cv2.multiply(out, lens_mask, scale=1 / 200.0)
    elif v < 0.999 or lens_mask is not None:
        m = vignette_mask(v, w, h, lens_mask, lens_key)
        out = cv2.multiply(out, m, scale=1 / 200.0)
    if lens_add is not None: out = cv2.add(out, lens_add)
    return out


def _vig_small(v80, w, h):
    key = ('vigs', round(v80, 3), w, h)
    if key not in _c:
        if v80 >= 0.999: m = np.ones((h, w), np.float32)
        else:
            k = -math.log(max(1e-3, v80)) / 0.8 ** 2.2
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
            r = np.sqrt((xx + 0.5 - w / 2) ** 2 + (yy + 0.5 - h / 2) ** 2) / math.hypot(w / 2, h / 2)
            m = np.exp(-k * r ** 2.2).astype(np.float32)
        _c[key] = m
    return _c[key]


def _vhs_static(w, h, vw, vh, curve, scan, glass, bezel, tube=True):
    """Cached per size: CRT curvature maps (output px -> VHS-res source px), the tube mask (scanlines, edge falloff,
    rounded corners; u8, 200 = unity), the glass sheen (additive u8) and the bezel image outside the tube. tube=False: a
    camcorder tape seen full frame (scanlines only, no tube edge / corners)."""
    key = ('vhs', w, h, vw, vh, round(curve, 3), round(scan, 3), round(glass, 3), round(bezel, 3), bool(tube))
    if key in _c: return _c[key]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (xx + 0.5) / w * 2 - 1; ny = (yy + 0.5) / h * 2 - 1
    cx, cy = 5.2 / max(1e-3, curve), 4.2 / max(1e-3, curve)
    if curve > 1e-3:
        sx = nx + nx * (ny / cy) ** 2 * 1.0; sy = ny + ny * (nx / cx) ** 2 * 1.0
        sx = sx * (0.985 if bezel <= 0 else 1.0); sy = sy * (0.985 if bezel <= 0 else 1.0)
    else:
        sx, sy = nx, ny
    mx = ((sx + 1) * 0.5 * vw - 0.5).astype(np.float32); my = ((sy + 1) * 0.5 * vh - 0.5).astype(np.float32)
    m1, m2 = cv2.convertMaps(mx, my, cv2.CV_16SC2)
    # tube: rounded-rectangle edge in source space, soft 0.6 % falloff; corner radius ~7 %
    ax, ay = np.abs(sx), np.abs(sy)
    rr = 0.075
    qx, qy = np.maximum(ax - (1 - rr), 0), np.maximum(ay - (1 - rr * 16 / 9), 0)
    dist = np.sqrt(qx ** 2 + (qy * 9 / 16) ** 2) - rr + np.minimum(np.maximum(ax - 1, ay - 1), 0) * 0      # <0 inside
    inside = np.clip(-dist / 0.012, 0, 1) * (ax < 1.02) * (ay < 1.02)
    edge = np.exp(-((np.maximum(ax, 0) ** 6) * 0.9 + (np.maximum(ay, 0) ** 6) * 0.9))                       # darker rim
    if not tube:
        inside = np.ones_like(inside); edge = np.ones_like(edge)
    lines = vh * 0.62                                                                                         # ~270 lines
    sl = 1.0 - 0.32 * scan * (0.5 + 0.5 * np.cos((sy + 1) * 0.5 * lines * 2 * np.pi)) ** 1.6
    m = np.clip(inside * edge * sl * 200, 0, 255).astype(np.uint8)
    mask = cv2.merge([m, m, m])
    add = None
    if glass > 0:                                                                     # a soft diagonal sheen + top glint
        g = np.clip(1 - np.abs((nx * 0.55 + ny * 0.85) + 0.55) / 0.22, 0, 1) ** 2 * 18 * glass
        g += np.exp(-(((nx + 0.45) / 0.35) ** 2 + ((ny + 0.78) / 0.12) ** 2)) * 26 * glass
        g = g * inside
        gu = np.clip(g, 0, 255).astype(np.uint8)
        add = cv2.merge([gu, gu, gu])
    bz = None
    if bezel > 0:                                                                     # warm dark plastic round the tube
        out_ = 1 - inside
        lum = (0.16 + 0.05 * (-ny) + 0.04 * np.exp(-((dist - 0.03) / 0.02) ** 2)) * out_
        b = np.clip(lum * 255 * bezel, 0, 255)
        bz = cv2.merge([np.clip(b * 0.78, 0, 255).astype(np.uint8), np.clip(b * 0.86, 0, 255).astype(np.uint8), b.astype(np.uint8)])
    _c[key] = (m1, m2, mask, add, bz)
    return _c[key]


def vhs(img, p, frame_i):
    """The 1974 tape on a CRT (see the module docstring, fx['vhs']). img BGR u8 at output size -> BGR u8."""
    if not isinstance(p, dict): p = dict(k=float(p))
    h, w = img.shape[:2]
    t = float(p.get('t', frame_i / 60.0)); k = float(p.get('k', 1.0))
    vw = max(320, int(round(w * 0.38 / 2)) * 2); vh = max(180, int(round(vw * h / w / 2)) * 2)
    small = cv2.resize(img, (vw, vh), interpolation=cv2.INTER_AREA)
    rng = np.random.default_rng(frame_i * 7919 + 13)
    # chroma bleed + shift (YCrCb, chroma smeared along the line, nudged right)
    ch = float(p.get('chroma', 1.0)) * k
    if ch > 0:
        ycc = cv2.cvtColor(small, cv2.COLOR_BGR2YCrCb)
        yl, cr, cb = cv2.split(ycc)
        kx = max(3, int(vw * 0.012 * ch) | 1)
        cr = cv2.blur(cr, (kx, 1)); cb = cv2.blur(cb, (kx, 1))
        shf = int(round(vw * 0.003 * ch))
        if shf: cr = np.roll(cr, shf, axis=1); cb = np.roll(cb, shf, axis=1)
        yl = cv2.GaussianBlur(yl, (0, 0), sigmaX=0.6 + 0.3 * k, sigmaY=0.01)
        small = cv2.cvtColor(cv2.merge([yl, cr, cb]), cv2.COLOR_YCrCb2BGR)
    # per-line horizontal displacement: slow skew wave, line jitter, the rolling tracking band, head switching
    rows = np.arange(vh, dtype=np.float32)
    wob = float(p.get('wobble', 1.0)) * k
    off = wob * (0.9 * np.sin(rows / vh * 2 * np.pi * 1.3 + t * 1.7) + 0.5 * np.sin(rows / vh * 2 * np.pi * 0.37 - t * 0.9))
    off += wob * 0.45 * rng.standard_normal(vh).astype(np.float32)
    tr = float(p.get('track', 0.35)) * k
    band = np.zeros(vh, np.float32)
    if tr > 0:
        yb = ((t * 0.075 + 0.3) % 1.35 - 0.15) * vh
        bh = vh * (0.035 + 0.03 * tr)
        band = np.exp(-((rows - yb) / bh) ** 2).astype(np.float32)
        off += band * tr * vw * 0.012 * (1.0 + rng.standard_normal(vh).astype(np.float32))
    hd = float(p.get('head', 1.0)) * k
    if hd > 0:
        nb = max(2, int(vh * 0.022))
        off[-nb:] += hd * vw * 0.02 * (1 + 0.5 * rng.standard_normal(nb).astype(np.float32)) * np.linspace(0.3, 1.0, nb)
    mx = np.tile(np.arange(vw, dtype=np.float32), (vh, 1)) - off[:, None]
    my = np.repeat(rows[:, None], vw, axis=1)
    small = cv2.remap(small, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    # tape snow, dropouts, the noisy band
    nz = float(p.get('noise', 1.0)) * k
    if nz > 0:
        g = (rng.standard_normal((vh // 2, vw // 2)).astype(np.float32) * 9 * nz)
        g = cv2.resize(g, (vw, vh), interpolation=cv2.INTER_LINEAR)
        g += (band[:, None] * tr * 70 * (rng.random((vh, vw), dtype=np.float32) - 0.35))
        small = np.clip(small.astype(np.float32) + g[..., None], 0, 255).astype(np.uint8)
        for _ in range(int(rng.poisson(2.5 * nz))):                         # dropouts: short white streaks
            yy_ = int(rng.integers(0, vh)); xx_ = int(rng.integers(0, vw)); ln = int(rng.integers(vw // 40, vw // 8))
            small[yy_, xx_:xx_ + ln] = np.maximum(small[yy_, xx_:xx_ + ln], 210)
    gl = float(p.get('glow', 1.0)) * k
    if gl > 0:
        bl = cv2.GaussianBlur(small, (0, 0), vw * 0.012)
        small = cv2.addWeighted(small, 1.0, bl, 0.22 * gl, 0)
    curve = float(p.get('curve', 1.0)); scan = float(p.get('scan', 1.0)) * k
    glass = float(p.get('glass', 1.0)); bezel = float(p.get('bezel', 0.0))
    m1, m2, mask, add, bz = _vhs_static(w, h, vw, vh, curve, scan, glass, round(bezel * 4) / 4, bool(p.get('tube', True)))
    out = cv2.remap(small, m1, m2, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    out = cv2.multiply(out, mask, scale=1 / 200.0)
    if add is not None: out = cv2.add(out, add)
    if bz is not None: out = cv2.add(out, bz)
    return out


def finish(img, grade, fx, frame_i):
    """Output-resolution finishing: VHS / CRT (fx['vhs']), blur (rule-card backgrounds), softness, static, glitch, grain."""
    p = grade.p
    h, w = img.shape[:2]
    if fx.get('vhs'):
        img = vhs(img, fx['vhs'], frame_i)
    if fx.get('blur'):
        s = fx['blur'] * w / 1920.0
        f = 4 if s > 6 else 2
        sm = cv2.resize(img, (w // f, h // f), interpolation=cv2.INTER_AREA)
        sm = cv2.GaussianBlur(sm, (0, 0), s / f)
        img = cv2.resize(sm, (w, h), interpolation=cv2.INTER_LINEAR)
    soft = fx.get('soft', p['soft'])
    if soft: img = cv2.GaussianBlur(img, (0, 0), soft * w / 2560.0)
    st = fx.get('static', 0.0)
    if st:
        tex = _static_tex(w, h)
        rng = np.random.default_rng(frame_i * 31 + 7)
        ox, oy = int(rng.integers(0, 32)) * 2, int(rng.integers(0, 32)) * 2
        img = cv2.addWeighted(img, 1 - clamp(st), tex[oy:oy + h, ox:ox + w], clamp(st), 0)
    gl = fx.get('glitch', 0.0)
    if gl:
        rng = np.random.default_rng(frame_i * 17 + 3)
        b, g_, r = cv2.split(img)
        sh = int(gl * w * 0.012) + 1
        r = np.roll(r, sh, axis=1); b = np.roll(b, -sh, axis=1)
        img = cv2.merge([b, g_, r])
        for _ in range(int(3 + gl * 6)):
            y0 = int(rng.integers(0, h - 8)); hh = int(rng.integers(4, max(6, h // 14)))
            img[y0:y0 + hh] = np.roll(img[y0:y0 + hh], int(rng.integers(-w // 12, w // 12) * gl), axis=1)
    gr = fx.get('grain', p['grain'])
    if gr:
        tex = _grain_tex(w, h)
        o = (frame_i * 37) % 64; o2 = (frame_i * 23 + 11) % 64
        k = gr / 16.0
        img = cv2.addWeighted(img, 1.0, tex[o:o + h, o2:o2 + w], k, -128.0 * k)
    return img
