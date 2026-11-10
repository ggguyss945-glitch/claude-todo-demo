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

# Mirror film presets (PLAN.md section 1; exposure added on camp_night / mirror_world / dawn_normal to hit the plan's measured luma targets). Per-frame parts (dawn_break red leak + flicker) come from sets SetPiece.fx(t).
_MF = dict(
    camp_night=dict(exposure=0.95, contrast=1.12, pivot=0.2, gamma=0.94, sat=0.9, wb=(0.88, 0.98, 1.10), floor='#06101a', bloom=1.0,
                    vignette=0.35, grain=0.0),
    cabin_flash=dict(contrast=1.1, gamma=0.95, sat=0.85, wb=(0.94, 0.99, 1.08), floor='#070d14', bloom=0.9, vignette=0.32,
                     grain=0.0),
    mirror_world=dict(exposure=0.75, contrast=1.15, gamma=0.88, sat=0.9, floor='#04060c', bloom=1.4, bloom_r=20.0, vignette=0.3, grain=0.0),
    dawn_normal=dict(exposure=0.25, contrast=0.95, pivot=0.3, gamma=1.05, sat=0.7, wb=(1.03, 1.0, 0.96), floor='#3d3d40', bloom=0.3,
                     vignette=0.67, grain=0.0),
    climax_red=dict(contrast=1.08, gamma=0.9, sat=1.25, wb=(1.08, 0.92, 0.94), floor='#0c0408', bloom=1.0, bloom_thr=228,
                    vignette=0.32, grain=0.0),
    memory=dict(contrast=0.85, gamma=1.08, sat=0.6, wb=(1.06, 1.0, 0.9), floor='#2c2824', bloom=1.5, bloom_thr=220,
                vignette=0.45, soft=1.0, grain=0.0),
)
_MF['camp_night_run'] = dict(_MF['camp_night'], exposure=1.05, bloom=1.2)
_MF['cabin_doorway'] = dict(_MF['cabin_flash'], wb=(1.0, 0.99, 1.0), bloom=1.1)
_MF['cabin_after'] = dict(_MF['cabin_flash'], exposure=-0.1, sat=0.8)
_MF['mirror_old_cabin'] = dict(_MF['cabin_flash'], exposure=0.2, vignette=0.4)
_MF['dawn_queen'] = dict(_MF['dawn_normal'], sat=0.55, wb=(0.97, 1.0, 1.04), vignette=0.55)
_MF['dawn_break'] = dict(_MF['dawn_queen'])
_MF['memory_night'] = dict(_MF['memory'], exposure=-0.6, wb=(1.08, 0.98, 0.86))
_MF['memory_morning'] = dict(_MF['memory'], exposure=0.25, sat=0.45, wb=(0.98, 1.0, 1.04))
GRADES.update(_MF)

# v2 presets (DIRECTION_V2 4.8). The sets are drawn at their target brightness, so these grades do NOT lift exposure (the
# cast keeps its own values: no dimming of characters under the night grade). Per-tenth light arc and the dawn_break
# flicker / red leak come from sets SetPiece.fx(t) (sets_v2.arc_fx).
_V2 = dict(
    night_v2=dict(exposure=0.0, contrast=1.32, pivot=0.24, gamma=1.0, shoulder=0.4, sat=1.15, wb=(0.92, 0.95, 1.12),
                  floor='#151632', bloom=1.2, bloom_thr=228, bloom_r=14.0, vignette=0.45, grain=0.0),
    stairs_v2=dict(exposure=0.0, contrast=1.3, pivot=0.24, gamma=1.0, shoulder=0.4, sat=1.25, wb=(1.04, 0.92, 1.1),
                   floor='#140a1e', bloom=1.4, bloom_thr=222, bloom_r=16.0, vignette=0.42, grain=0.0),
    dawn_v2=dict(exposure=0.0, contrast=1.26, pivot=0.52, gamma=1.0, shoulder=0.45, sat=1.2, wb=(1.06, 1.0, 0.9), floor='#5a4030',
                 bloom=0.8, bloom_thr=232, bloom_r=14.0, vignette=0.6, grain=0.0),
    climax_v2=dict(exposure=0.12, contrast=1.3, pivot=0.2, gamma=1.0, shoulder=0.4, sat=1.2, wb=(1.04, 0.9, 1.04),
                   floor='#1a0610', bloom=1.4, bloom_thr=222, bloom_r=16.0, vignette=0.42, grain=0.0),
    ending_v2=dict(exposure=0.0, contrast=1.3, pivot=0.24, gamma=1.0, shoulder=0.4, sat=1.1, wb=(0.95, 0.96, 1.08),
                   floor='#141530', bloom=1.1, bloom_thr=228, bloom_r=14.0, vignette=0.45, grain=0.0),
    memory_sepia=dict(exposure=0.0, contrast=1.12, pivot=0.5, gamma=1.0, shoulder=0.5, sat=0.6, mono=0.25, tint='#d8b088',
                      wb=(1.04, 0.98, 0.88), floor='#2e2218', bloom=0.6, bloom_thr=236, bloom_r=18.0, vignette=0.6,
                      grain=2.5, soft=0.8),
)
_V2['dawn_queen_v2'] = dict(_V2['dawn_v2'], sat=1.0, wb=(1.0, 0.99, 0.95), vignette=0.5)
_V2['dawn_break_v2'] = dict(_V2['dawn_queen_v2'], contrast=1.1, sat=0.95)
GRADES.update(_V2)


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


def finish(img, grade, fx, frame_i):
    """Output-resolution finishing: blur (rule-card backgrounds), softness, static, glitch, grain."""
    p = grade.p
    h, w = img.shape[:2]
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
