"""sets.py: every set, view, lighting variant and animated prop state of "If An Eighth Step Appears On Your Mirror...".

Full API and the per-view notes are in SETS.md. In short:

    import sets
    sp = sets.build_shot(shot)                    # a plan/shots.json entry -> SetPiece
    sp = sets.build('cabin_now', 'wide', 'flash', shot=shot)          # same, explicit (shot gives props, sfx, cam, t0/t1)
    sp.anchors['tess_mirror']                     # Anchor(x, y, depth, height): feet / bust point as drawn at `depth`
    at = sets.resolve_at(sp, spec)                # shots.json chars[i] -> the `at` list for characters.CharRig
    img = render_frame(sp.add(char_layers...), cam.at(t), t, i, **sp.render_kw(), post=sp.fx(t), hud=...)
    sp.info['beam'].override = f(t) -> (sx, sy, ax, ay, k)   # optional: drive Tess's beam from her rig pose
    sp.info['press'] = f(t) -> [(x, y, k), ...]   # optional: fingertips under the towel (S115/S116) from the hands rig

A SetPiece is a list of engine Layers (static parts cached, animated parts small live layers) plus anchors, the shot's
grade, focus / dof and fx(t) (per-frame post effects such as the dawn_break flicker and red edge leak).
Everything is drawn in the 1920x1080 design space with the camera home at (960, 540, zoom 1).
"""
import math, re
import numpy as np
import skia
from engine.core import (DW, DH, LINE, Pen, col, mix, rgb, poly, smooth, rect, rrect, oval, union, minus, moved,
                         clamp, lerp, prog, ease, ease_in_out, ease_out_cubic, ease_in_cubic, ease_out_back, noise1, hash01,
                         text, text_width, surface_for, image_from)
from engine.scene import Layer

__all__ = ['SetPiece', 'Anchor', 'St', 'Beam', 'build', 'build_shot', 'resolve_at', 'SETS', 'VIEWS', 'clock_ours',
           'clock_theirs', 'STEP_XY', 'EIGHTH', 'TILT']

FRAME = (-420, -280, 2340, 1360)        # depth >= 1 layers: frame + camera moves (zoom 0.95..2.2, shake)
NEAR = (-900, -560, 2820, 1640)         # foreground layers (depth < 1) move further under pans
TILT = -13.0                            # the tilted mirror (degrees, same sense as a camera roll)
STEP_XY = [(1280 - 110 * k, 300 + 80 * k) for k in range(7)]     # lipstick tread centres, top (k=0) to bottom (k=6)
EIGHTH = (510.0, 860.0, 130.0)          # the 8th line: left end x, y, length (depth 1.04, behind the glass)
RED, RED_HI, RED_DK, GLOW = '#c63449', '#d84a5a', '#8a1e2c', '#ff4060'
CORE, FALL = '#fff2d6', '#f3d9a6'       # flashlight core / falloff
MOON = '#9fb6ff'


# ====================================================================== containers
class Anchor:
    """Where a character goes: x, y (feet for body modes, centre for bust / hands) in design px at `depth`, height = design
    px of the figure there (bust: scale, 1 = a 600 px head)."""
    __slots__ = ('x', 'y', 'depth', 'height', 'note')

    def __init__(self, x, y, depth=1.0, height=600.0, note=''):
        self.x, self.y, self.depth, self.height, self.note = float(x), float(y), float(depth), float(height), note

    def __iter__(self): return iter((self.x, self.y, self.height, self.depth))

    def at(self): return [self.x, self.y, self.height, self.depth]

    def __repr__(self): return 'Anchor(%.0f, %.0f, d=%.2f, h=%.2f%s)' % (self.x, self.y, self.depth, self.height,
                                                                         ', ' + self.note if self.note else '')


class SetPiece(list):
    def __init__(self, name, layers, anchors=None, grade=None, focus=1.0, dof=0.0, lens=None, fx=None, info=None):
        super().__init__([l for l in layers if l is not None])
        self.name, self.anchors, self.grade, self.focus, self.dof, self.lens = name, anchors or {}, grade, focus, dof, lens
        self._fx, self.info = fx, info or {}

    def add(self, *layers):
        return SetPiece(self.name, list(self) + [l for l in layers if l is not None], self.anchors, self.grade, self.focus,
                        self.dof, self.lens, self._fx, self.info)

    def without(self, *names):
        return SetPiece(self.name, [l for l in self if l.name not in names], self.anchors, self.grade, self.focus, self.dof,
                        self.lens, self._fx, self.info)

    def layer(self, name):
        for l in self:
            if l.name == name: return l
        raise KeyError(name)

    def fx(self, t): return dict(self._fx(t)) if self._fx else {}

    def render_kw(self): return dict(lens=self.lens, grade=self.grade, focus=self.focus, dof=self.dof)


def resolve_at(sp, spec):
    """chars[i]['at'] (anchor name or list) -> list for characters.CharRig (`[x, y, h, depth]` for body modes)."""
    a = spec.get('at')
    if isinstance(a, str):
        if a not in sp.anchors: raise KeyError('set %s has no anchor %r (has %s)' % (sp.name, a, sorted(sp.anchors)))
        an = sp.anchors[a]
        if spec.get('mode') in ('bust', 'hands', 'feet', 'lying'): return [an.x, an.y, an.height]
        return an.at()
    return a


# ====================================================================== prop state over a shot
DEFAULT = dict(steps_drawn=7, steps_smeared=0, eighth='none', mirror='not_found', towel='wrapped', flashlight='off',
               candy='none', bell='crate', tape='on', shoe='one_on_lace_loose', phone='tess_pocket', doorway='none',
               jacket='you', sweatshirt='fits', clock='running', sprinkler='off', drop='none', lantern='on', queen='absent')
_ALIAS = {'held in your left hand': 'held', 'in your hands': 'in_hands', 'unwrapped, upright against the back wall': 'held_upright',
          'falling drips': 'falling', 'on the eighth step': 'eighth_step', 'head turned to you': 'turned_to_you',
          'in the doorway (other side)': 'doorway', 'beside Noah (glimpse)': 'bunk', 'sitting beside Noah': 'bunk',
          'on the step below yours': 'step_below', 'lifting her foot toward an erased step': 'step_below',
          'on the step, hand through the railing behind her': 'eighth_step', 'held out by Noah': 'held_out',
          'with Tess on the porch': 'tess_running', 'lace dropped': 'left behind'}
_NUM = re.compile(r'(?<![\d:])(\d+\.\d+)')


def _times(s): return [float(x) for x in _NUM.findall(str(s))]


class St:
    """Prop states of one shot as functions of film time t (from shots.json props + changes_in_shot + the shot's sfx).
    v(key, t) -> state; since(key, t) -> seconds since it took that state (1e3 if from before the shot);
    ev(name) -> list of event times parsed from the plan strings; sfx(name) -> cue times of that SFX in the shot."""

    def __init__(self, shot=None, props=None, t0=None):
        shot = shot or {}
        p = dict(DEFAULT); p.update(props if props is not None else shot.get('props', {}))
        self.t0 = float(shot.get('t0', 0.0) if t0 is None else t0)
        self.t1 = float(shot.get('t1', self.t0 + 3.0))
        self.raw = {k: v for k, v in p.items() if k != 'changes_in_shot'}
        self.events = {}
        self._sfx = {}
        for c in shot.get('sfx', []):
            self._sfx.setdefault(c['name'], []).append(c)
        base, ch = {}, []
        for k, v in self.raw.items():
            if isinstance(v, (int, float)): base[k] = v; continue
            s = str(v); ts = _times(s)
            val = _ALIAS.get(s, s)
            if ' -> ' in s and not ts and k != 'steps_smeared':
                a, b = s.split(' -> ', 1); val = a.strip()
            if k == 'steps_smeared' and ' -> ' in s:
                val = int(s.split(' -> ')[0])
            elif k == 'steps_drawn' and isinstance(val, str):
                if s.startswith('5 -> 7'):
                    val = 5; self.events['step_draw'] = [(5, ts[0]), (6, ts[1])]
                else:
                    val = 7; self.events['erase'] = (ts[0], ts[1]); self.events['glow'] = True
            elif k == 'eighth' and ts:
                val = 'none'; ch.append((ts[0], {'eighth': 'present'})); self.events['eighth_draw'] = ts[0]
            elif k == 'mirror':
                if s.startswith('tilted'): val = 'tilted'
                elif s.startswith('fog'): val = 'tilted'; self.events['fog'] = ts[0]
                elif s.startswith('dark at'): val = 'mirror_again'; ch.append((ts[0], {'mirror': 'dark'}))
            elif k == 'towel' and ts:
                if s.startswith('snatched'): val = 'held'; self.events['towel_throw'] = (ts[0], ts[1]); ch.append((ts[1], {'towel': 'over_mirror'}))
                elif s.startswith('drops'): val = 'over_mirror'; self.events['towel_drop'] = ts[0]; ch.append((ts[0], {'towel': 'floor'}))
            elif k == 'flashlight' and ts: val = 'off'; ch.append((ts[0], {'flashlight': 'tess_on'}))
            elif k == 'bell' and ts:
                if 'broken' in s: val = 'crate_seen'; self.events['crate_break'] = ts[0]; ch.append((ts[0], {'bell': 'crate_broken'}))
                elif 'struck' in s: val = 'fake_ringing'; self.events['strike'] = ts[0]; ch.append((ts[0], {'bell': 'rattle'}))
            elif k == 'drop' and ts:
                if s.startswith('rises'): val = 'none'; self.events['drop_rise'] = (ts[0], ts[1]); ch.append((ts[1], {'drop': 'hanging'}))
                elif 'falls' in s: val = 'hanging'; self.events['drop_fall'] = ts[0]; ch.append((ts[0], {'drop': 'falling'}))
            elif k == 'phone':
                if ts: val = 'tess_pocket'; ch.append((ts[0], {'phone': 'sill_face_up'}))
                elif s.startswith('screen_steps'): val = 'screen_steps'
            elif k == 'sprinkler' and ts: val = 'off'; self.events['sprinkler'] = ts
            elif k == 'clock' and ts: val = 'running'; self.events['clock_back'] = ts[0]
            elif k == 'jacket' and ts: val = 'you'; ch.append((ts[0], {'jacket': 'noah'}))
            elif k in ('footprints', 'clock_dawn', 'fake_bell', 'watch', 'mattress', 'fingertip'):
                self.events[k] = ts or True
            base[k] = val
        for (tc, d) in p.get('changes_in_shot', []): ch.append((float(tc), d))
        ch.sort(key=lambda c: c[0])
        self.base, self.changes = base, ch

    def v(self, key, t):
        val = self.base.get(key, DEFAULT.get(key))
        for (tc, d) in self.changes:
            if tc > t: break
            if key in d: val = d[key]
        return val

    def since(self, key, t):
        last = None
        for (tc, d) in self.changes:
            if tc > t: break
            if key in d: last = tc
        return 1e3 if last is None else t - last

    def change_t(self, key, value=None):
        for (tc, d) in self.changes:
            if key in d and (value is None or d[key] == value): return tc
        return None

    def ev(self, name, default=None): return self.events.get(name, default)

    def sfx(self, name): return sorted(c['t'] for c in self._sfx.get(name, []))

    def sfx_cues(self, name): return sorted(self._sfx.get(name, []), key=lambda c: c['t'])


# ====================================================================== the two clocks (wall clocks + header)
def clock_ours(t):
    """Seconds after midnight (may be negative = before 00:00) on our side: 23:57:00 at 19.40 s, real time; runs backward
    278.97-281.81 s, then forward again (PLAN header spec)."""
    base = -180.0 + (t - 19.40)
    if t < 278.97: return base
    b0 = -180.0 + (278.97 - 19.40)
    if t < 281.81: return b0 - (t - 278.97)
    return b0 - (281.81 - 278.97) + (t - 281.81)


def clock_theirs(t):
    """Seconds after 06:00 on the other side: 06:59:40 + ((t - 297.59) mod 19.48); frozen at 07:00:00 from 535.36."""
    if t >= 535.36: return 3600.0
    return 3580.0 + ((t - 297.59) % 19.48)


# ---------------------------------------------------------------------- gradient key normalisation (speed)
# core caches one 256 px gradient image per distinct stop list; a stop alpha that changes every frame (pulses, motes, beams)
# would rebuild that image per call. _R / _L move the overall level into the paint alpha and quantise the rest.
def _qc(c):
    r_, g_, b_ = rgb(c)
    return '#%02x%02x%02x' % (min(255, int(round(r_ / 6.0)) * 6), min(255, int(round(g_ / 6.0)) * 6), min(255, int(round(b_ / 6.0)) * 6))


def _norm(stops, a):
    if not stops or isinstance(stops[0], str): return [_qc(c) for c in stops], a
    m = max(float(st_[2]) if len(st_) > 2 else 255.0 for st_ in stops)
    if m <= 0.5: return None, 0.0
    out = [(round(float(st_[0]), 3), _qc(st_[1]), round((float(st_[2]) if len(st_) > 2 else 255.0) / m * 32) / 32 * 255) for st_ in stops]
    return out, a * m / 255.0


def _R(pen, path, cx, cy, r, stops, a=1.0, sy=1.0, blend='normal', clip=True):
    st_, a = _norm(stops, a)
    if st_ is None or a <= 0.002 or r <= 0: return
    pen.radial(path, cx, cy, r, st_, a=min(1.0, a), sy=sy, blend=blend, clip=clip)


def _L(pen, path, x0, y0, x1, y1, stops, a=1.0):
    st_, a = _norm(stops, a)
    if st_ is None or a <= 0.002: return
    pen.linear(path, x0, y0, x1, y1, st_, a=min(1.0, a))


# ====================================================================== small helpers
def _h(i, seed=0):
    return float(hash01(abs(int(i)) * 2 + (1 if i < 0 else 0), abs(int(seed)) * 2 + (1 if seed < 0 else 0)))


def _lt(c, k): return mix(c, '#ffffff', k)


def _dk(c, k): return mix(c, '#000000', k)


def _cl(depth, draw, name, key, bounds=FRAME, **kw):
    return Layer(depth, draw, name, cache='mf:' + key, bounds=bounds, **kw)


def _live(depth, draw, name, **kw):
    return Layer(depth, draw, name, **kw)


def _clip(pen, path):
    pen.cv.save(); pen.cv.clipPath(path, skia.ClipOp.kIntersect, True)


def _unclip(pen): pen.cv.restore()


def _blob(cx, cy, rx, ry, n=10, seed=0, jag=0.2):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 1 + jag * (_h(i, seed) - 0.5) * 2
        pts.append((cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r))
    return smooth(pts, True, 0.9)


def _tx(pen, s, x, y, weight=600, size=30, c='#ffffff', a=255, spacing=0.0, align='center'):
    """core.text with letter spacing in design px (core takes em)."""
    return text(pen.cv, s, x, y, weight, size, c, a, spacing / max(1.0, size), align)


def _ttext(pen, s, x, y, size, c, a=255, weight=800, spacing=0.0, align='center', rot=0.0, worn=0.0, seed=0):
    """Painted text (optionally rotated, and worn: grunge chips knocked out of the letters only)."""
    cv = pen.cv
    cv.save(); cv.translate(x, y)
    if rot: cv.rotate(rot)
    if worn: cv.saveLayer(None, None)
    sp_em = spacing / max(1.0, size)
    text(cv, s, 0, 0, weight, size, c, a, sp_em, align)
    if worn:
        w = text_width(s, weight, size, sp_em) * 1.05
        x0 = -(w / 2 if align == 'center' else (w if align == 'right' else 0))
        p = skia.Paint(AntiAlias=True); p.setBlendMode(skia.BlendMode.kDstOut)
        for i in range(int(18 * worn * w / 300) + 2):
            px = x0 + _h(i, seed) * w; py = -size * 0.8 + _h(i, seed + 1) * size * 0.95
            cv.drawPath(_blob(px, py, size * (0.03 + 0.11 * _h(i, seed + 2)), size * (0.02 + 0.07 * _h(i, seed + 3)), 7, seed + i, 0.45), p)
        cv.restore()
    cv.restore()


# ====================================================================== light: beam, hot spot, flare
_SPR = {}


def _beam_sprite(r0, r1, soft, W):
    """Cone + haze in one premultiplied BGRA image (W x W/2): apex at the left edge; r0 / r1 = the cone's half-width at the
    apex / far end relative to the image half-height (the haze fills the rest). Sized close to its on-screen size so it
    can be drawn with nearest sampling (a rotated linear-filtered upscale costs ~40 ms per beam at 2560)."""
    key = (round(r0, 2), round(r1, 2), round(soft, 2), W)
    if key in _SPR: return _SPR[key]
    H = W // 2
    u = (np.arange(W, dtype=np.float32) + 0.5) / W
    v = (np.arange(H, dtype=np.float32) + 0.5) / H * 2 - 1
    U, V = np.meshgrid(u, v)
    along = np.clip(U / 0.02, 0, 1) * (1 - U) ** 0.85 * (0.6 + 0.4 * np.exp(-U * 4))
    hw = r0 + (r1 - r0) * U
    d = np.abs(V) / np.maximum(hw, 1e-3)
    cone = np.clip(1.0 - d, 0, 1) ** (0.6 + soft) * np.exp(-1.8 * d * d)
    hz_w = np.maximum(r0 * 2, (r1 * 1.7) * U + 1e-3)
    dh = np.abs(V) / np.maximum(np.minimum(hz_w, 1.0), 1e-3)
    haze = np.clip(1.0 - dh, 0, 1) ** 1.2 * np.exp(-1.8 * dh * dh)
    a = np.clip((cone * 0.88 + haze * 0.36) * along, 0, 1)
    arr = np.zeros((H, W, 4), np.uint8)
    rr, gg, bb = rgb(CORE)
    arr[..., 3] = (a * 255).astype(np.uint8)
    arr[..., 2] = (a * rr).astype(np.uint8); arr[..., 1] = (a * gg).astype(np.uint8); arr[..., 0] = (a * bb).astype(np.uint8)
    img = skia.Image.fromarray(np.ascontiguousarray(arr), skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType)
    if len(_SPR) > 48: _SPR.clear()
    _SPR[key] = (img, arr)
    return _SPR[key]


_SLIN = skia.SamplingOptions(skia.FilterMode.kLinear)
_SNEAR = skia.SamplingOptions(skia.FilterMode.kNearest)


def draw_beam(pen, sx, sy, ax, ay, k=1.0, w0=26.0, spread=0.32, length=None, a=0.35, blend='plus', soft=0.4):
    """Flashlight cone from (sx, sy) toward (ax, ay): core #fff2d6 at alpha a falling to 0 over its length, with a wider
    faint haze around it (one image draw)."""
    if k <= 0.01: return
    dx, dy = ax - sx, ay - sy
    L = length or math.hypot(dx, dy) * 1.25
    ang = math.degrees(math.atan2(dy, dx))
    w1 = w0 + 2 * L * spread
    wh = max(w1 * 1.7, w0 * 2)                       # image half-height covers the haze
    cv = pen.cv
    cb = cv.getLocalClipBounds(); mw = cb.width() * 0.3
    if not (cb.left() - mw < sx < cb.right() + mw and cb.top() - mw < sy < cb.bottom() + mw):
        # source far off-frame (close-ups): only a broad wash of the beam is visible -> axis-aligned soft radial (fast)
        mx, my = lerp(sx, ax, 0.62), lerp(sy, ay, 0.62)
        rr = max(w1 * 0.55, 0.5 * math.hypot(ax - mx, ay - my) + w1 * 0.3)
        _R(pen, None, mx, my, rr, [(0, CORE, 70), (0.5, CORE, 30), (1, CORE, 0)], a=a * k / 0.35, sy=0.75, clip=False)
        return
    m = cv.getTotalMatrix(); px_per = math.hypot(m.getScaleX(), m.getSkewY())
    W = 256
    while W < L * px_per and W < 2048: W *= 2
    img, _ = _beam_sprite(w0 / 2 / (wh / 2) * 1.0, w1 / 2 / (wh / 2), soft, W)
    cv.save(); cv.translate(sx, sy); cv.rotate(ang)
    p = skia.Paint(AntiAlias=False); p.setAlphaf(clamp(a * k / 0.35 * 0.62))
    p.setBlendMode(skia.BlendMode.kPlus if blend == 'plus' else skia.BlendMode.kSrcOver)
    cv.drawImageRect(img, skia.Rect.MakeWH(W, W // 2), skia.Rect.MakeLTRB(0, -wh / 2, L, wh / 2), _SNEAR if W >= L * px_per * 0.7 else _SLIN, p,
                     skia.Canvas.kFast_SrcRectConstraint)
    cv.restore()


def hot_spot(pen, x, y, r, k=1.0, sy=0.8, c=FALL, core=CORE):
    """Pool of flashlight light on a surface: warm falloff, a hot core (draw with the beam)."""
    if k <= 0.01: return
    _R(pen, None, x, y, r * 2.0, [(0, c, 46 * k), (0.5, c, 20 * k), (1, c, 0)], sy=sy, clip=False)
    _R(pen, None, x, y, r, [(0, core, 105 * k), (0.55, c, 80 * k), (0.8, c, 52 * k), (1, c, 0)], sy=sy, clip=False)
    _R(pen, None, x, y, r * 0.3, [(0, '#ffffff', 60 * k), (1, core, 0)], sy=sy, clip=False)


def lens_flare(pen, x, y, k=1.0, c=CORE, cx=960, cy=540):
    """Flashlight pointing near the lens: hot core, horizontal streak, ghosts mirrored through the frame centre."""
    if k <= 0.01: return
    _R(pen, None, x, y, 260 * k, [(0, '#ffffff', 200 * k), (0.12, c, 150 * k), (0.4, c, 40 * k), (1, c, 0)], clip=False)
    _R(pen, None, x, y, 900, [(0, c, 60 * k), (1, c, 0)], sy=0.018, clip=False)
    for i, (f, r, cc) in enumerate(((0.5, 40, '#9fd0ff'), (0.9, 22, '#ffd0a0'), (1.35, 70, '#a0ffd0'), (1.7, 30, '#ffb0c0'))):
        gx, gy = x + (cx - x) * f * 2 * 0.5, y + (cy - y) * f * 2 * 0.5
        _R(pen, None, gx, gy, r * 1.6, [(0, cc, 0), (0.7, cc, 38 * k), (1, cc, 0)], clip=False)


class Beam:
    """Tess's flashlight in a set: fn(t) -> (sx, sy, ax, ay, k). `override` (set by the assembler from the rig pose) wins.
    beam_k(x, y, t) gives how much of the beam lights a point (dust motes use it)."""

    def __init__(self, fn, w0=26.0, spread=0.32, a=0.35, spot=170.0, spot_sy=0.8, flare=0.0):
        self.fn, self.override = fn, None
        self.w0, self.spread, self.a, self.spot, self.spot_sy, self.flare = w0, spread, a, spot, spot_sy, flare
        self._c = (None, None)

    def at(self, t):
        if self._c[0] == t: return self._c[1]
        f = self.override or self.fn
        r = f(t) if f else None
        if r is None: r = (0, 0, 1, 0, 0.0)
        self._c = (t, r)
        return r

    def k_at(self, x, y, t):
        sx, sy, ax, ay, k = self.at(t)
        if k <= 0.01: return 0.0
        dx, dy = ax - sx, ay - sy; L = math.hypot(dx, dy) * 1.25 or 1.0
        ux, uy = dx / L * 1.25 / 1.25, dy / L
        dl = math.hypot(dx, dy) or 1.0; ux, uy = dx / dl, dy / dl
        px, py = x - sx, y - sy
        u = px * ux + py * uy
        if u <= 0 or u > L: return 0.0
        d = abs(px * uy - py * ux)
        hw = self.w0 / 2 + u * self.spread
        return k * math.exp(-2.2 * (d / hw) ** 2) * (1 - u / L) ** 0.7

    def layer(self, depth=1.0, name='beam', spot=True):
        def draw(pen, t):
            sx, sy, ax, ay, k = self.at(t)
            if k <= 0.01: return
            draw_beam(pen, sx, sy, ax, ay, k, self.w0, self.spread, None, self.a)
            if spot and self.spot: hot_spot(pen, ax, ay, self.spot, k * 0.9, self.spot_sy)
            if self.flare: lens_flare(pen, sx, sy, self.flare * k)
        return _live(depth, draw, name, blur=0)


def aim_fn(src, aims, k=1.0, wobble=10.0, seed=0, t_on=None, t_off=None, sweep=None):
    """Beam path helper: src (x, y) or f(t); aims = [(t, x, y), ...] eased between (or a single (x, y)); hand wobble px.
    sweep = (amp_x, hz) adds a side-to-side search."""
    def fn(t):
        if (t_on is not None and t < t_on) or (t_off is not None and t >= t_off): return None
        s = src(t) if callable(src) else src
        if isinstance(aims[0], (int, float)): ax, ay = aims
        else:
            ax, ay = aims[0][1], aims[0][2]
            for i in range(len(aims) - 1):
                (ta, xa, ya), (tb, xb, yb) = aims[i], aims[i + 1]
                if t >= ta:
                    u = ease_in_out(prog(t, ta, tb)); ax, ay = lerp(xa, xb, u), lerp(ya, yb, u)
        ax += wobble * noise1(t * 0.9, seed) + 0.4 * wobble * noise1(t * 3.1, seed + 3)
        ay += wobble * 0.7 * noise1(t * 0.8, seed + 1) + 0.3 * wobble * noise1(t * 2.7, seed + 4)
        if sweep: ax += sweep[0] * math.sin(t * sweep[1] * 2 * math.pi)
        kk = k(t) if callable(k) else k
        return (s[0], s[1], ax, ay, kk)
    return fn


# ====================================================================== particles
def motes(pen, t, box, n=90, seed=0, beam=None, c=CORE, amb=0.06, size=(1.4, 3.4), speed=(8.0, 20.0), fall=0.0,
          bokeh=0.08, alpha=230, rise=0.0):
    """Dust drifting 8-20 px/s inside a box (wraps, never stops); brightness from the beam (Beam.k_at) plus ambient."""
    x0, y0, x1, y1 = box; W, H = x1 - x0, y1 - y0
    for i in range(n):
        h1, h2, h3, h4, h5 = (_h(i, seed + j) for j in range(5))
        sp = speed[0] + (speed[1] - speed[0]) * h3
        ang = 2 * math.pi * h4
        vx, vy = sp * math.cos(ang) * 0.8, sp * math.sin(ang) * 0.5 + fall - rise
        x = x0 + (h1 * W + vx * t + 22 * noise1(t * 0.23 + i * 0.37, seed)) % W
        y = y0 + (h2 * H + vy * t + 16 * noise1(t * 0.19 + i * 0.71, seed + 1)) % H
        k = amb + (beam.k_at(x, y, t) * 1.3 if beam is not None else 0.0)
        if k < 0.02: continue
        tw = 0.7 + 0.3 * math.sin(t * (1.3 + 2.5 * h5) + i)
        a = min(255.0, alpha * k * tw)
        if h5 < bokeh:
            r = 9 + 10 * h1
            _R(pen, None, x, y, r, [(0, c, a * 0.35), (0.7, c, a * 0.28), (1, c, 0)], clip=False)
        else:
            r = size[0] + (size[1] - size[0]) * h2
            _R(pen, None, x, y, r * 1.8, [(0, c, a), (0.45, c, a * 0.7), (1, c, 0)], clip=False)


def fireflies(pen, t, box, n=8, seed=0, c='#e4f59a'):
    x0, y0, x1, y1 = box
    for i in range(n):
        h1, h2, h3 = _h(i, seed), _h(i, seed + 1), _h(i, seed + 2)
        x = x0 + ((h1 * (x1 - x0) + (14 + 20 * h3) * t * (1 if h2 > 0.5 else -1)) % (x1 - x0))
        y = y0 + h2 * (y1 - y0) + 40 * noise1(t * 0.35 + i, seed + 3)
        b = max(0.0, math.sin(t * (0.9 + 0.8 * h3) * 2 + i * 2.1)) ** 3
        if b < 0.03: continue
        _R(pen, None, x, y, 26, [(0, '#ffffff', 220 * b), (0.12, c, 200 * b), (0.4, c, 60 * b), (1, c, 0)], clip=False)


def mist(pen, t, y, x0, x1, h, n=7, seed=0, a=24, c='#a9bfd6', speed=14.0):
    """Drifting mist band at height y (bands of soft ellipses moving at `speed` px/s, wrapping)."""
    W = x1 - x0
    for i in range(n):
        w = (0.25 + 0.35 * _h(i, seed)) * W
        x = x0 + ((_h(i, seed + 1) * W + speed * (0.7 + 0.6 * _h(i, seed + 2)) * t) % (W + w)) - w / 2
        yy = y + (_h(i, seed + 3) - 0.5) * h * 0.6 + 6 * noise1(t * 0.2 + i, seed)
        _R(pen, None, x, yy, w / 2, [(0, c, a), (0.6, c, a * 0.5), (1, c, 0)], sy=h / w, clip=False)


def moths(pen, t, x, y, r=60.0, n=5, seed=0, c='#d9cbb0'):
    for i in range(n):
        ph = t * (2.2 + 1.3 * _h(i, seed)) + i * 1.7
        mx = x + r * (math.sin(ph) * 0.9 + 0.3 * noise1(t * 2 + i, seed))
        my = y + r * 0.6 * math.sin(ph * 1.7 + i) + 0.25 * r * noise1(t * 2.3 + i, seed + 1)
        fl = abs(math.sin(t * 38 + i * 3))
        pen.fill(oval(mx - 3.5, my, 4.2, 2.0 + 2.6 * fl), c, 230)
        pen.fill(oval(mx + 3.5, my, 4.2, 2.0 + 2.6 * fl), c, 230)
        pen.fill(oval(mx, my, 1.6, 3.2), '#5a5040', 255)


def stars(pen, box, n, seed, ymax, c='#dfe8ff'):
    x0, y0, x1, y1 = box
    for i in range(n):
        x = x0 + _h(i, seed) * (x1 - x0); y = y0 + _h(i, seed + 1) ** 1.6 * (ymax - y0)
        r = 0.8 + 1.8 * _h(i, seed + 2) ** 3
        a = 90 + 150 * _h(i, seed + 3)
        pen.fill(oval(x, y, r), c, a)
        if r > 2.0: _R(pen, None, x, y, r * 5, [(0, c, 60), (1, c, 0)], clip=False)


def twinkle(pen, t, box, n, seed, ymax, c='#ffffff'):
    x0, y0, x1, y1 = box
    for i in range(n):
        x = x0 + _h(i, seed) * (x1 - x0); y = y0 + _h(i, seed + 1) ** 1.6 * (ymax - y0)
        b = max(0.0, math.sin(t * (1.5 + 2 * _h(i, seed + 2)) + i)) ** 6
        if b > 0.05:
            _R(pen, None, x, y, 9, [(0, c, 200 * b), (1, c, 0)], clip=False)
            pen.seg((x - 8 * b, y), (x + 8 * b, y), 1.0, c, int(150 * b)); pen.seg((x, y - 8 * b), (x, y + 8 * b), 1.0, c, int(150 * b))


def moon(pen, x, y, r, c='#e9eefc'):
    _R(pen, None, x, y, r * 9, [(0, MOON, 70), (0.25, MOON, 26), (1, MOON, 0)], clip=False)
    _R(pen, None, x, y, r * 2.2, [(0, '#ffffff', 90), (1, MOON, 0)], clip=False)
    d = oval(x, y, r)
    _R(pen, d, x - r * 0.3, y - r * 0.3, r * 1.3, [(0, '#ffffff'), (0.7, c), (1, '#b9c4e6')])
    for (dx, dy, rr) in ((-0.3, -0.1, 0.22), (0.25, 0.3, 0.16), (0.1, -0.35, 0.1), (-0.05, 0.45, 0.12)):
        pen.fill(oval(x + dx * r, y + dy * r, rr * r), '#aab6d8', 120)


def drops_fall(pen, t, x, y0, y1, period=1.1, seed=0, c='#dfe8f0', r=5.0, phase=0.0, n=1):
    """Water drops forming at (x, y0) and falling to y1 every `period` s (deterministic: the time loop repeats exactly)."""
    for j in range(n):
        u = ((t + phase + j * period / max(1, n)) / period) % 1.0
        if u < 0.55:
            g = u / 0.55; rr = r * (0.4 + 0.6 * g)
            pen.fill(_drop_path(x, y0 + rr * 0.6 * g, rr, 1.0 + 0.4 * g), c, 220)
        else:
            g = (u - 0.55) / 0.45
            yy = y0 + (y1 - y0) * g * g
            if g < 0.97:
                pen.fill(_drop_path(x, yy, r, 1.6), c, 230)
                pen.fill(oval(x - r * 0.3, yy - r * 0.3, r * 0.25), '#ffffff', 200)
            else:
                pen.fill(oval(x, y1, r * 3, r * 0.6), c, 120)


def _drop_path(x, y, r, stretch=1.3):
    return smooth([(x, y - r * stretch * 1.6), (x + r * 0.75, y - r * 0.2), (x + r, y + r * 0.4), (x, y + r),
                   (x - r, y + r * 0.4), (x - r * 0.75, y - r * 0.2)], True, 0.8)


# ====================================================================== materials
def boards(pen, box, c, horizontal=False, bw=70.0, seed=0, grain=0.5, seam='#05080c', seam_a=200, var=0.1, knots=0.3,
           nails=True, hi=None, lw=2.0, gap_shadow=True):
    """Plank wall / floor fill over box (x0, y0, x1, y1): tone-varied boards, wood grain, dark seams, a lit edge, knots,
    nail heads. hi = highlight colour for the lit board edge."""
    x0, y0, x1, y1 = box
    hi = hi or _lt(c, 0.12)
    n = int(math.ceil(((y1 - y0) if horizontal else (x1 - x0)) / bw))
    path_all = rect(x0, y0, x1 - x0, y1 - y0)
    _clip(pen, path_all)
    for i in range(n):
        tone = mix(c, '#000000' if _h(i, seed) < 0.5 else '#ffffff', var * _h(i, seed + 1))
        if horizontal: r = rect(x0, y0 + i * bw, x1 - x0, bw)
        else: r = rect(x0 + i * bw, y0, bw, y1 - y0)
        if horizontal: _L(pen, r, 0, y0 + i * bw, 0, y0 + (i + 1) * bw, [_lt(tone, 0.05), tone, _dk(tone, 0.12)])
        else: _L(pen, r, x0 + i * bw, 0, x0 + (i + 1) * bw, 0, [_lt(tone, 0.04), tone, _dk(tone, 0.1)])
    pen.texture(path_all, 'wood', grain, 'overlay', 1.4 if horizontal else 1.4, 0 if horizontal else 90)
    for i in range(n + 1):
        if horizontal:
            yy = y0 + i * bw
            if gap_shadow: pen.fill(rect(x0, yy, x1 - x0, 5), '#000000', 70)
            pen.seg((x0, yy), (x1, yy), lw, seam, seam_a); pen.seg((x0, yy + 2.5), (x1, yy + 2.5), 1.2, hi, 60)
            if i < n and _h(i, seed + 9) < 0.7:          # butt joints
                bx = x0 + _h(i, seed + 10) * (x1 - x0)
                pen.seg((bx, yy), (bx, yy + bw), lw * 0.8, seam, seam_a * 0.8)
        else:
            xx = x0 + i * bw
            if gap_shadow: pen.fill(rect(xx, y0, 5, y1 - y0), '#000000', 60)
            pen.seg((xx, y0), (xx, y1), lw, seam, seam_a); pen.seg((xx + 2.5, y0), (xx + 2.5, y1), 1.2, hi, 55)
    for i in range(int(n * knots * 3)):
        kx = x0 + _h(i, seed + 20) * (x1 - x0); ky = y0 + _h(i, seed + 21) * (y1 - y0)
        rr = bw * (0.06 + 0.07 * _h(i, seed + 22))
        pen.fill(oval(kx, ky, rr * (2.2 if horizontal else 1.0), rr * (1.0 if horizontal else 2.2)), _dk(c, 0.35), 180)
        pen.line(oval(kx, ky, rr * (3.2 if horizontal else 1.6), rr * (1.6 if horizontal else 3.2)), 1.2, _dk(c, 0.3), 110)
    if nails:
        for i in range(n):
            for j, f in enumerate((0.12, 0.88) if not horizontal else (0.06, 0.5, 0.94)):
                if horizontal: nx, ny = x0 + f * (x1 - x0) + (_h(i * 3 + j, seed + 30) - 0.5) * 40, y0 + (i + 0.5) * bw
                else: nx, ny = x0 + (i + 0.5) * bw, y0 + f * (y1 - y0)
                pen.fill(oval(nx, ny, 2.4), '#0a0c10', 200); pen.fill(oval(nx - 0.6, ny - 0.6, 1.0), _lt(c, 0.3), 120)
    _unclip(pen)


def floor_persp(pen, xl_n, xr_n, y_n, xl_f, xr_f, y_f, n, c0, c1, seed=0, grain=0.45, seam='#05080c', joints=True):
    """Perspective floorboards: near edge y_n from xl_n..xr_n, far edge y_f from xl_f..xr_f, n boards converging."""
    path = poly([(xl_f, y_f), (xr_f, y_f), (xr_n, y_n), (xl_n, y_n)])
    _L(pen, path, 0, y_f, 0, y_n, [c0, c1])
    for i in range(n):
        u0, u1 = i / n, (i + 1) / n
        q = poly([(lerp(xl_f, xr_f, u0), y_f), (lerp(xl_f, xr_f, u1), y_f), (lerp(xl_n, xr_n, u1), y_n), (lerp(xl_n, xr_n, u0), y_n)])
        tone = _h(i, seed)
        pen.fill(q, '#000000' if tone < 0.5 else '#ffffff', int(18 * abs(tone - 0.5) * 2))
    pen.texture(path, 'wood', grain, 'overlay', 1.6, 90)
    for i in range(n + 1):
        u = i / n
        pen.seg((lerp(xl_f, xr_f, u), y_f), (lerp(xl_n, xr_n, u), y_n), 1.0 + 2.0 * abs(u - 0.5) * 0 + 1.6, seam, 200)
        if joints and i < n:
            for j in range(2):
                v = _h(i * 2 + j, seed + 5)
                yy = y_f + (y_n - y_f) * v ** 1.6
                xa = lerp(lerp(xl_f, xr_f, u), lerp(xl_n, xr_n, u), v ** 1.6)
                xb = lerp(lerp(xl_f, xr_f, u + 1 / n), lerp(xl_n, xr_n, u + 1 / n), v ** 1.6)
                pen.seg((xa, yy), (xb, yy), 1.4, seam, 170)
    return path


def dust_film(pen, path, a=40, c='#8a96a2', seed=0, scale=1.0):
    pen.texture(path, 'grunge', a / 255.0, 'screen', scale)
    pen.texture(path, 'plaster', a / 400.0, 'overlay', scale * 0.6)


def mesh(pen, box, step=22.0, c='#8a96a4', a=70, w=1.2, torn=None):
    """Chain-link / window-screen diamond mesh over box; torn = (cx, cy, r): a hole."""
    x0, y0, x1, y1 = box
    r = rect(x0, y0, x1 - x0, y1 - y0)
    if torn: r = minus(r, _blob(torn[0], torn[1], torn[2], torn[2] * 0.8, 11, 5, 0.45))
    _clip(pen, r)
    H = y1 - y0
    xx = x0 - H
    while xx < x1 + H:
        pen.seg((xx, y0), (xx + H, y1), w, c, a); pen.seg((xx + H, y0), (xx, y1), w, c, a)
        xx += step
    _unclip(pen)


def shaft(pen, pts, c=MOON, a=60, soft=3):
    """Light shaft polygon (window to floor) with soft edges: nested polygons fading out."""
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    for i in range(soft, 0, -1):
        k = 1 + 0.05 * i
        q = poly([(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in pts])
        pen.fill(q, c, int(a / (soft + 1)))
    _L(pen, poly(pts), pts[0][0], pts[0][1], pts[2][0], pts[2][1], [(0, c, a / 255.0 * 255 * 0.9), (1, c, 0)])


def grass(pen, x0, x1, y, h, n, seed, c, hi=None):
    for i in range(n):
        x = x0 + _h(i, seed) * (x1 - x0); hh = h * (0.4 + 0.6 * _h(i, seed + 1)); lean = (_h(i, seed + 2) - 0.5) * hh * 0.7
        pen.fill(poly([(x - 3, y), (x + lean, y - hh), (x + 3, y)]), c)
        if hi and _h(i, seed + 3) < 0.4: pen.seg((x + 1, y - 2), (x + lean * 0.9, y - hh * 0.9), 1.2, hi, 90)


def pine(pen, x, y, h, seed=0, c='#08111a', rim=None, rim_a=0, sway=0.0, tiers=8, w=0.42, trunk=True):
    """Layered pine silhouette with drooping jagged tiers; sway bends the top (px at the tip); rim = moonlit right edges."""
    pts_l, pts_r = [], []
    top = (x + sway, y - h)
    for j in range(tiers):
        f = j / tiers
        yy = y - h * (0.12 + 0.88 * f)
        ww = h * w * (1 - f) ** 0.95 * (0.85 + 0.3 * _h(j, seed))
        bend = sway * ((0.12 + 0.88 * f) ** 2)
        yb = yy + h * 0.06 * (1 - f * 0.5)
        pts_l += [(x + bend - ww * 0.35, yy - h * 0.035), (x + bend - ww, yb + h * 0.02 * _h(j, seed + 1))]
        pts_r += [(x + bend + ww * 0.35, yy - h * 0.035), (x + bend + ww, yb + h * 0.02 * _h(j, seed + 2))]
    path = poly([(x - h * 0.03, y)] + pts_l + [top] + pts_r[::-1] + [(x + h * 0.03, y)])
    if trunk: pen.fill(rect(x - h * 0.018, y - h * 0.12, h * 0.036, h * 0.12), _dk(c, 0.2))
    pen.fill(path, c)
    if rim and rim_a:
        for j in range(tiers):
            a, b = pts_r[j * 2], pts_r[j * 2 + 1]
            pen.seg(a, b, max(1.2, h * 0.006), rim, rim_a)
        pen.seg(pts_r[-2], top, max(1.2, h * 0.006), rim, rim_a)
    return path


def treeline(pen, x0, x1, y, h, n, seed, c, rim=None, rim_a=0, jitter=0.45):
    for i in range(n):
        xx = x0 + (i + _h(i, seed) * 0.8) * (x1 - x0) / n
        hh = h * (1 - jitter + jitter * _h(i, seed + 1))
        pine(pen, xx, y + 10 * _h(i, seed + 2), hh, seed + i, c, rim, rim_a, 0.0, 7, 0.36)


def lantern(pen, x, y, s=1.0, k=1.0, glass='#ffd9a0', body='#3a4a3a', glow=True):
    """Battery camping lantern standing at (x, y = base)."""
    if glow and k > 0:
        _R(pen, None, x, y - 60 * s, 520 * s, [(0, glass, 90 * k), (0.3, glass, 34 * k), (1, glass, 0)], clip=False)
    base = rrect(x - 34 * s, y - 26 * s, 68 * s, 26 * s, 6 * s)
    pen.shape(base, body, 3 * s)
    g = rrect(x - 26 * s, y - 96 * s, 52 * s, 72 * s, 8 * s)
    _R(pen, g, x, y - 60 * s, 60 * s, [(0, '#ffffff'), (0.5, glass), (1, _dk(glass, 0.2))] if k > 0.3 else [_dk(glass, 0.5), _dk(glass, 0.6)])
    for dx in (-14, 0, 14): pen.seg((x + dx * s, y - 96 * s), (x + dx * s, y - 26 * s), 2.2 * s, _dk(body, 0.2), 180)
    pen.line(g, 3 * s)
    top = rrect(x - 30 * s, y - 112 * s, 60 * s, 18 * s, 6 * s)
    pen.shape(top, body, 3 * s)
    pen.line(smooth([(x - 22 * s, y - 112 * s), (x, y - 140 * s), (x + 22 * s, y - 112 * s)], False), 4 * s, '#2a2a2a')


# ====================================================================== props
def wall_clock(pen, cx, cy, r, sec, jitter=0.0, face='#d9d4c6', rim='#3a3f46', hand='#1a1a1a', red='#a32a2a', lw=None):
    """Round school wall clock; sec = seconds after midnight (12-hour face). jitter = second-hand recoil (deg)."""
    lw = lw or max(2.0, r * 0.05)
    pen.shadow(oval(cx, cy, r * 1.08), 6 * r / 44, 8 * r / 44, r * 0.18, '#000000', 120)
    pen.shape(oval(cx, cy, r * 1.08), rim, lw)
    _R(pen, oval(cx, cy, r * 0.94), cx - r * 0.3, cy - r * 0.35, r * 1.4, [_lt(face, 0.1), face, _dk(face, 0.25)])
    for k in range(60):
        a = k * math.pi / 30
        r0 = 0.78 if k % 5 == 0 else 0.86
        pen.seg((cx + math.cos(a) * r * r0, cy + math.sin(a) * r * r0), (cx + math.cos(a) * r * 0.9, cy + math.sin(a) * r * 0.9),
                lw * (0.8 if k % 5 == 0 else 0.3), '#2a2a2a', 230)
    if r > 60:
        for k in range(1, 13):
            a = k * math.pi / 6 - math.pi / 2
            _tx(pen, str(k), cx + math.cos(a) * r * 0.64, cy + math.sin(a) * r * 0.64 + r * 0.06, 700, r * 0.15, '#2a2a2a')
    s = sec % 43200
    h_a = 2 * math.pi * (s / 43200.0) - math.pi / 2
    m_a = 2 * math.pi * ((s % 3600) / 3600.0) - math.pi / 2
    s_a = 2 * math.pi * (math.floor(s % 60) / 60.0) - math.pi / 2 + math.radians(jitter)
    pen.seg((cx - math.cos(h_a) * r * 0.1, cy - math.sin(h_a) * r * 0.1), (cx + math.cos(h_a) * r * 0.5, cy + math.sin(h_a) * r * 0.5), lw * 1.6, hand)
    pen.seg((cx - math.cos(m_a) * r * 0.12, cy - math.sin(m_a) * r * 0.12), (cx + math.cos(m_a) * r * 0.76, cy + math.sin(m_a) * r * 0.76), lw * 1.1, hand)
    pen.seg((cx - math.cos(s_a) * r * 0.2, cy - math.sin(s_a) * r * 0.2), (cx + math.cos(s_a) * r * 0.84, cy + math.sin(s_a) * r * 0.84), lw * 0.45, red)
    pen.fill(oval(cx, cy, lw * 1.2), hand); pen.fill(oval(cx, cy, lw * 0.5), red)
    gl = minus(oval(cx, cy, r * 0.92), oval(cx + r * 0.25, cy + r * 0.28, r * 0.95))
    pen.fill(gl, '#ffffff', 34)


def _clock_sec(t, st, side='ours'):
    """Wall-clock seconds and second-hand recoil for the shot (backward jerk on our side, the 6:59:40 loop on theirs)."""
    if side == 'theirs':
        s = 6 * 3600 + clock_theirs(t)
        return s, 0.0
    s = clock_ours(t) % 86400
    tb = st.ev('clock_back') if st is not None else None
    if tb is None and st is not None: tb = st.change_t('clock', 'backward')
    if tb is not None and t >= tb:
        n = math.floor((t - tb) / 0.2)
        s = clock_ours(tb) - 2 - n
        u = (t - tb) % 0.2
        return s, -6.0 * math.exp(-u * 30) * math.cos(u * 60)
    u = (t % 1.0)
    return s, 3.0 * math.exp(-u * 25) * math.cos(u * 50)


def mirror_frame(pen, x0, y0, x1, y1, fw, s=1.0, lit=0.0, c='#d8d4c8', wood='#8f8a7e', seed=3, night=True):
    """White-painted wooden frame chipped to grey wood around the pane box (x0..x1, y0..y1), frame width fw."""
    outer = rect(x0 - fw, y0 - fw, x1 - x0 + 2 * fw, y1 - y0 + 2 * fw)
    inner = rect(x0, y0, x1 - x0, y1 - y0)
    fr = minus(outer, inner)
    base = mix(_dk(c, 0.62), c, lit) if night else c
    pen.shadow(outer, 10 * s, 14 * s, 20 * s, '#000000', 140)
    _L(pen, fr, x0 - fw, 0, x1 + fw, 0, [_lt(base, 0.08), base, _dk(base, 0.25)])
    pen.texture(fr, 'wood', 0.3, 'overlay', 0.7 * s, 90)
    woodc = mix(_dk(wood, 0.55), wood, lit) if night else wood
    _clip(pen, fr)
    for i in range(int(26 * s ** 0.3) + 10):
        side = i % 4
        u = _h(i, seed)
        if side == 0: px, py = x0 - fw * _h(i, seed + 1), y0 + u * (y1 - y0)
        elif side == 1: px, py = x1 + fw * _h(i, seed + 1), y0 + u * (y1 - y0)
        elif side == 2: px, py = x0 + u * (x1 - x0), y0 - fw * _h(i, seed + 1)
        else: px, py = x0 + u * (x1 - x0), y1 + fw * _h(i, seed + 1)
        rr = fw * (0.12 + 0.3 * _h(i, seed + 2))
        chip = _blob(px, py, rr * (1.8 if side < 2 else 1.0), rr * (1.0 if side < 2 else 1.8), 8, seed + i, 0.45)
        pen.fill(chip, woodc); pen.line(chip, max(1.0, 1.2 * s), _dk(woodc, 0.4), 160)
    _unclip(pen)
    pen.seg((x0 - fw * 0.55, y0 - fw * 0.55), (x1 + fw * 0.55, y0 - fw * 0.55), max(1.0, 1.5 * s), _lt(base, 0.25), 120)
    pen.line(inner, max(1.5, 3 * s), '#000000', 200)
    pen.line(outer, max(2.0, 4 * s), LINE)
    return outer, inner


def glass(pen, path, box, base='#0c1520', refl='#1c2a38', seed=0, s=1.0, dust=0.1, silver=True):
    """Old mirror glass: dark reflective gradient, desilvering spots at the edges, a dust film and finger smudges."""
    x0, y0, x1, y1 = box
    _L(pen, path, x0, y0, x1, y1, [_lt(refl, 0.08), refl, base, _dk(base, 0.3)])
    _clip(pen, path)
    if silver:
        for i in range(int(22 + 30 * s ** 0.2)):
            e = i % 4; u = _h(i, seed)
            px = x0 + (u * (x1 - x0) if e > 1 else (8 + 50 * _h(i, seed + 1)) * s * (1 if e == 0 else -1) + (x0 if e == 0 else x1))
            py = y0 + (u * (y1 - y0) if e <= 1 else (8 + 40 * _h(i, seed + 1)) * s * (1 if e == 2 else -1) + (0 if e == 2 else y1 - y0))
            if e > 1: px = x0 + u * (x1 - x0)
            rr = (4 + 22 * _h(i, seed + 2) ** 2) * s
            pen.fill(_blob(px, py, rr, rr * 0.8, 9, seed + i, 0.5), '#9aa0a6', 60 + int(70 * _h(i, seed + 3)))
            pen.fill(_blob(px, py, rr * 0.45, rr * 0.4, 7, seed + i + 1, 0.5), '#2a2e33', 120)
    dust_film(pen, path, int(255 * dust), seed=seed, scale=s)
    for i in range(5):
        px = x0 + (0.2 + 0.6 * _h(i, seed + 40)) * (x1 - x0); py = y0 + (0.2 + 0.6 * _h(i, seed + 41)) * (y1 - y0)
        _R(pen, None, px, py, 46 * s, [(0, '#c8d2dc', 22), (0.6, '#c8d2dc', 10), (1, '#c8d2dc', 0)], sy=0.75, clip=False)
    _unclip(pen)


def _stroke_pts(a, b, n=10, wob=2.0, seed=0):
    return [(lerp(a[0], b[0], i / (n - 1)) + wob * (_h(i, seed) - 0.5), lerp(a[1], b[1], i / (n - 1)) + wob * (_h(i, seed + 1) - 0.5))
            for i in range(n)]


def _wax(pen, pts, w, a=1.0, glow=0.0, seed=0, crumbs=True):
    """One waxy lipstick stroke along pts: crumbly dark edge, core, sheen highlight, crumbs."""
    if len(pts) < 2: return
    p = poly(pts, False)
    if glow > 0:
        pen.line(p, w * 4.5, GLOW, int(40 * glow * a)); pen.line(p, w * 2.2, GLOW, int(70 * glow * a))
    pen.line(p, w * 1.18, RED_DK, int(235 * a))
    pen.line(p, w, mix('#b0283a', '#ff5a6e', 0.35 * glow), int(250 * a))
    hp = poly([(x - w * 0.12, y - w * 0.22) for x, y in pts], False)
    pen.line(hp, w * 0.28, mix(RED_HI, '#ffd0d6', 0.3 * glow), int(200 * a))
    for i in range(len(pts) - 1):
        x, y = pts[i]
        if _h(i, seed + 7) < 0.5:
            pen.seg((x, y + w * 0.1), (pts[i + 1][0], pts[i + 1][1] + w * 0.15), w * 0.14, '#6e1622', int(120 * a))
    if crumbs:
        for i in range(len(pts) * 2):
            j = i % len(pts); x, y = pts[j]
            ox, oy = (_h(i, seed + 3) - 0.5) * w * 1.6, (_h(i, seed + 4) - 0.5) * w * 1.5
            pen.fill(oval(x + ox, y + oy, w * (0.06 + 0.1 * _h(i, seed + 5))), RED_DK if _h(i, seed + 6) < 0.6 else RED, int(220 * a))


def _streaks(pen, x, y, L, fade, seed, w=120):
    """Lipstick dragged down the glass by cloth: a pink haze plus irregular tapering drags (no hard edges)."""
    _R(pen, None, x, y + L * 0.35, max(80, L * 0.45), [(0, '#d0566a', 60 * fade), (1, '#d0566a', 0)], sy=1.4 * max(0.3, min(1.6, L / 260)), clip=False)
    for j in range(7):
        cx_ = x - w * 0.45 + w * 0.9 * _h(j, seed) + 8 * (_h(j, seed + 9) - 0.5)
        ln = L * (0.35 + 0.65 * _h(j, seed + 1))
        wd = 4 + 11 * _h(j, seed + 2)
        n = 5
        for i in range(n):
            ya, yb = y + ln * i / n, y + ln * (i + 1) / n
            xa = cx_ + 6 * math.sin(i * 1.3 + j); xb = cx_ + 6 * math.sin((i + 1) * 1.3 + j)
            pen.seg((xa, ya), (xb, yb), wd * (1 - 0.6 * i / n), RED, int(fade * (150 - 26 * i) * (0.5 + 0.5 * _h(j, seed + 3))))
        if _h(j, seed + 4) < 0.4:
            pen.fill(_drop_path(cx_, y + ln + 6, wd * 0.45, 1.3), RED_DK, int(150 * fade))


def lipstick_steps(pen, t, drawn=7, partial=None, smear=None, glow=0.0, wipe=None, erase=None, sc=1.0, ox=0.0, oy=0.0,
                   fade=1.0, seed=11, erased=False, last=0.0):
    """The seven lipstick treads (top k=0 .. bottom k=6) in mirror_cu coordinates (scaled by sc about (ox, oy)).
    drawn = how many from the bottom are complete (the hook draws the top two on); partial = (k, u) a stroke being drawn;
    smear[k] = 0..1 down-right drag; glow = red glow (climax); wipe = y line: everything above it is streaked downward;
    erase = fraction of red left (1 = all), fade = overall alpha."""
    smear = smear or [0.0] * 7
    cv = pen.cv
    cv.save(); cv.translate(ox, oy); cv.scale(sc, sc); cv.translate(-ox, -oy)
    first = 7 - drawn
    if erased:              # wiped clean: faint pink smudges where the treads were; maybe one last streak
        for k in range(7):
            x, y = STEP_XY[k]
            _R(pen, None, x, y + 20, 110, [(0, '#c8606e', 36 * fade), (1, '#c8606e', 0)], sy=0.45, clip=False)
            if k == 6 and last > 0.01:
                _streaks(pen, x, y - 10, 260 * (0.4 + 0.6 * last), last, seed + 77, 70)
        cv.restore()
        return
    for k in range(7):
        u = 1.0
        if k < first:
            if partial and partial[0] == k: u = partial[1]
            else: continue
        x, y = STEP_XY[k]
        tread = _stroke_pts((x + 60, y + 1), (x - 60, y - 1), 9, 2.4, seed + k * 5)
        riser = _stroke_pts((x - 60, y), (x - 50, y + 80), 7, 2.0, seed + k * 5 + 2) if k < 6 else []
        pts = tread + riser[1:]
        m = max(1, int(round(len(pts) * u)))
        pts = pts[:m]
        sm = smear[k]
        a = fade * (1 - 0.62 * sm)
        if wipe is not None and y < wipe:
            dy = wipe - y
            _streaks(pen, x, y, dy, fade, seed + k * 9)
            continue
        _wax(pen, pts, 19, a, glow, seed + k)
        if sm > 0.02:
            ddx, ddy = 40 * sm * 0.9, 40 * sm * 0.45
            for j in range(1, 5):
                f = j / 4
                q = [(px + ddx * f, py + ddy * f) for px, py in pts]
                pen.line(poly(q, False), 14 * (1 - 0.15 * f), RED, int(fade * 150 * sm * (1 - f * 0.7)))
            fx, fy = x + 20 + ddx, y + ddy
            pen.fill(oval(fx, fy, 22 * sm, 9 * sm), '#e8a0a8', int(70 * fade * sm))
    cv.restore()


def eighth_line(pen, t, t_draw=None, dur=0.6, k=1.0, glow=1.0, rot=0.0, sc=1.0, ox=0.0, oy=0.0):
    """The 8th step: a clean straight 6 px line #c63449 with a faint glow; draws itself left to right in `dur`."""
    x, y, L = EIGHTH
    u = 1.0 if t_draw is None else ease_in_out(prog(t, t_draw, t_draw + dur))
    if u <= 0 or k <= 0: return
    cv = pen.cv
    cv.save(); cv.translate(ox, oy); cv.scale(sc, sc); cv.translate(-ox, -oy)
    if rot: cv.rotate(rot, x + L / 2, y)
    x1 = x + L * u
    _R(pen, None, x + L * u / 2, y, L * 0.75, [(0, GLOW, 70 * glow * k), (0.5, GLOW, 22 * glow * k), (1, GLOW, 0)], sy=0.22, clip=False)
    pen.seg((x, y), (x1, y), 10, GLOW, int(60 * k * glow))
    pen.seg((x, y), (x1, y), 6, RED, int(255 * k))
    pen.seg((x, y - 1.6), (x1, y - 1.6), 1.6, '#ff9aa8', int(170 * k))
    if 0 < u < 1: _R(pen, None, x1, y, 22, [(0, '#ffd0d8', 230), (1, GLOW, 0)], clip=False)
    cv.restore()


def towel_cloth(pen, path, box, s=1.0, wet=0.0, seed=0, lit=1.0, stripes=True, base='#e0a060', alt='#efe6d6'):
    """Faded orange-and-white striped terry towel filling `path` (stripes run across box width), terry texture, folds."""
    x0, y0, x1, y1 = box
    o = mix(_dk(base, 0.55), base, lit); w_ = mix(_dk(alt, 0.6), alt, lit)
    if wet: o, w_ = _dk(o, 0.25 * wet), _dk(w_, 0.3 * wet)
    pen.fill(path, w_)
    _clip(pen, path)
    if stripes:
        sw = 46 * s; y = y0; i = 0
        while y < y1:
            if i % 2 == 0: pen.fill(rect(x0 - 10, y, x1 - x0 + 20, sw * (0.55 if i % 4 == 0 else 1.0)), o)
            y += sw * (0.55 if i % 4 == 0 else 1.0); i += 1
    pen.texture(path, 'fabric', 0.55, 'overlay', 0.9 * s)
    pen.texture(path, 'grunge', 0.25, 'multiply', 1.4 * s)
    for i in range(5):
        fx = x0 + (0.15 + 0.7 * _h(i, seed)) * (x1 - x0)
        _L(pen, rect(fx - 30 * s, y0, 60 * s, y1 - y0), fx - 30 * s, 0, fx + 30 * s, 0,
                   [(0, '#000000', 0), (0.5, '#000000', 60), (1, '#000000', 0)])
        pen.seg((fx + 12 * s, y0), (fx + 16 * s, y1), 3 * s, '#ffffff', 40)
    _unclip(pen)
    pen.line(path, max(2.0, 3.5 * s), LINE)


def phone_prop(pen, cx, cy, w, h, rot=0.0, screen='dark', t=0.0, lit=0.6, red=0.0, dust=0.4, steps=0.0, seed=2):
    """Tess's phone lying face up: dark glass, a beam glint, dust; screen='steps' draws 7 tiny lipstick steps (0..1)."""
    cv = pen.cv
    cv.save(); cv.translate(cx, cy); cv.rotate(rot)
    body = rrect(-w / 2, -h / 2, w, h, w * 0.12)
    pen.shadow(body, w * 0.03, w * 0.05, w * 0.06, '#000000', 160)
    pen.fill(body, '#22262c'); pen.line(body, max(2, w * 0.012), '#5a6068')
    scr = rrect(-w / 2 + w * 0.045, -h / 2 + w * 0.045, w * 0.91, h - w * 0.09, w * 0.09)
    _L(pen, scr, -w / 2, -h / 2, w / 2, h / 2, ['#0e1218', '#05070a', '#0b0f14'])
    _clip(pen, scr)
    _L(pen, poly([(-w, -h * 0.2), (w, -h * 0.55), (w, -h * 0.45), (-w, -h * 0.08)]), 0, -h * 0.5, 0, 0,
               [(0, '#ffffff', 0), (0.5, '#c8d6e6', 46 * lit), (1, '#ffffff', 0)])
    if red > 0: _R(pen, None, w * 0.15, h * 0.1, w * 0.9, [(0, GLOW, 90 * red), (1, GLOW, 0)], clip=False)
    if dust:
        for i in range(int(60 * dust)):
            px, py = (-0.45 + 0.9 * _h(i, seed)) * w, (-0.45 + 0.9 * _h(i, seed + 1)) * h
            pen.fill(oval(px, py, w * 0.004 * (1 + 2 * _h(i, seed + 2))), '#aab4be', int(60 + 80 * _h(i, seed + 3)))
    if steps > 0:
        sc = w * 0.0009
        for k in range(7):
            u = clamp(steps * 7 - (6 - k))
            if u <= 0: continue
            x, y = (STEP_XY[k][0] - 950) * sc * 0.6, (STEP_XY[k][1] - 560) * sc * 0.6
            pts = _stroke_pts((x + 60 * sc * 0.6, y), (x - 60 * sc * 0.6, y), 6, 0.5, k)
            if k < 6: pts += _stroke_pts((x - 60 * sc * 0.6, y), (x - 50 * sc * 0.6, y + 80 * sc * 0.6), 4, 0.4, k + 9)[1:]
            pts = pts[:max(2, int(len(pts) * u))]
            _wax(pen, pts, 14 * sc * 0.6 * 1.6, 1.0, 0.5, k, crumbs=False)
    _unclip(pen)
    pen.fill(rrect(-w * 0.12, -h / 2 + w * 0.06, w * 0.24, w * 0.05, w * 0.025), '#000000', 200)
    cv.restore()


def bunk(pen, x0, x1, y_floor, s=1.0, c='#3a4250', mat='#46505c', tick='#2c3440', top=True, made=False, blanket='#5a6a4a',
         lit=0.0, y_mat=None, y_top=None, dip=None, posts_c=None, pillow='#c9c4b8'):
    """Camp bunk bed seen frontally: wooden posts, bottom mattress band (striped ticking, or made with a blanket), top bunk
    with rail. y_mat = (top, bottom) of the bottom mattress; y_top = (rail_y0, rail_y1). dip = (x, depth px) mattress dip."""
    ym0, ym1 = y_mat or (y_floor - 190 * s, y_floor - 100 * s)
    yr0, yr1 = y_top or (ym0 - 270 * s, ym0 - 220 * s)
    pc = posts_c or c
    pw = 26 * s
    # back shadow on the wall
    pen.fill(rect(x0 + 20 * s, yr0 - 60 * s, x1 - x0, y_floor - yr0 + 40 * s), '#000000', 60)
    # frame under the bottom mattress
    pen.shape(rect(x0, ym1, x1 - x0, 24 * s), _dk(c, 0.15), 3 * s)
    pen.fill(rect(x0 + pw, ym1 + 24 * s, x1 - x0 - 2 * pw, y_floor - ym1 - 24 * s), '#000000', 120)
    for i in range(1, 6):
        xx = lerp(x0, x1, i / 6); pen.seg((xx, ym1 + 24 * s), (xx, y_floor - 6 * s), 3 * s, _dk(c, 0.5), 160)
    # bottom mattress
    def mattress(ya, yb, has_dip=None, mc=mat):
        if has_dip:
            dx, dd = has_dip
            pts = [(x0 + pw * 0.5, ya)]
            for i in range(25):
                xx = lerp(x0 + pw * 0.5, x1 - pw * 0.5, i / 24)
                pts.append((xx, ya + dd * math.exp(-((xx - dx) / (90 * s)) ** 2)))
            pts += [(x1 - pw * 0.5, ya), (x1 - pw * 0.5, yb), (x0 + pw * 0.5, yb)]
            m = smooth(pts, True, 0.3)
        else:
            m = rrect(x0 + pw * 0.5, ya, x1 - x0 - pw, yb - ya, 14 * s)
        if made:
            pen.fill(m, blanket)
            pen.texture(m, 'fabric', 0.5, 'overlay', 0.8 * s)
            pen.fill(rrect(x0 + pw, ya - 8 * s, 150 * s, 40 * s, 14 * s), pillow); pen.line(rrect(x0 + pw, ya - 8 * s, 150 * s, 40 * s, 14 * s), 2.5 * s)
            pen.fill(rect(x0 + pw * 0.5, ya + (yb - ya) * 0.15, x1 - x0 - pw, 10 * s), _lt(blanket, 0.25), 200)
        else:
            pen.fill(m, mc)
            _clip(pen, m)
            xx = x0; i = 0
            while xx < x1:
                pen.fill(rect(xx, ya - 30 * s, 9 * s, yb - ya + 60 * s), tick, 200 if i % 3 else 255)
                xx += 26 * s; i += 1
            pen.texture(m, 'fabric', 0.4, 'overlay', 0.8 * s)
            _L(pen, m, 0, ya, 0, yb, [(0, '#ffffff', 30), (0.4, '#000000', 0), (1, '#000000', 90)])
            for i in range(3):
                sx_ = lerp(x0, x1, 0.2 + 0.3 * i + 0.1 * _h(i, 4))
                pen.fill(_blob(sx_, lerp(ya, yb, 0.5), 50 * s, 20 * s, 9, i, 0.35), '#6a5a3a', 50)
            _unclip(pen)
        pen.line(m, 3.2 * s)
    mattress(ym0, ym1, dip)
    if top:
        tm0 = yr0 - 50 * s
        pen.shape(rect(x0, yr1, x1 - x0, 22 * s), _dk(c, 0.1), 3 * s)
        mattress(tm0, yr0 + 8 * s)
        rail = rect(x0 + pw, yr0, x1 - x0 - 2 * pw, yr1 - yr0)
        pen.fill(rail, c); pen.texture(rail, 'wood', 0.35, 'overlay', 0.9 * s); pen.line(rail, 3 * s)
        pen.seg((x0 + pw, yr0 + 4 * s), (x1 - pw, yr0 + 4 * s), 2 * s, _lt(c, 0.3 + 0.3 * lit), 140)
    ytop = (yr0 - 120 * s) if top else (ym0 - 90 * s)
    for xx in (x0, x1 - pw):
        post = rect(xx, ytop, pw, y_floor - ytop)
        _L(pen, post, xx, 0, xx + pw, 0, [_lt(pc, 0.15 + 0.3 * lit), pc, _dk(pc, 0.3)])
        pen.texture(post, 'wood', 0.35, 'overlay', 0.8 * s, 90)
        pen.line(post, 3.2 * s)
        pen.fill(rrect(xx - 3 * s, ytop - 10 * s, pw + 6 * s, 14 * s, 5 * s), _dk(pc, 0.1)); pen.line(rrect(xx - 3 * s, ytop - 10 * s, pw + 6 * s, 14 * s, 5 * s), 2.5 * s)
    if top:   # ladder at the right end
        lx = x1 - pw - 70 * s
        for xx in (lx, lx + 46 * s): pen.shape(rect(xx, yr1, 10 * s, ym0 - yr1), _dk(c, 0.1), 2.4 * s)
        for i in range(3):
            yy = lerp(yr1 + 30 * s, ym0 - 20 * s, i / 2)
            pen.shape(rect(lx, yy, 56 * s, 9 * s), c, 2.4 * s)
    return dict(mat=(ym0, ym1), rail=(yr0, yr1), top=ytop)


def swimsuits(pen, x0, x1, y, t=0.0, s=1.0, sway=1.0, seed=4, drip=True):
    """A row of damp swimsuits and a towel hanging over the top-bunk rail, swaying a little and dripping."""
    cols = ['#3d6fa8', '#c8524a', '#2f8a7a', '#d8a63a', '#7a4a9a', '#e07a5a']
    n = 5 if s >= 0.9 else 6; w = (x1 - x0) / n
    for i in range(n):
        cx = x0 + (i + 0.5) * w + (_h(i, seed) - 0.5) * w * 0.2
        c = cols[(i + seed) % len(cols)]
        sw = sway * 3 * s * noise1(t * 0.6 + i, seed)
        ww, hh = w * (0.55 + 0.2 * _h(i, seed + 1)), (90 + 60 * _h(i, seed + 2)) * s
        if i % 2 == 0:   # trunks
            p = smooth([(cx - ww / 2, y), (cx + ww / 2, y), (cx + ww / 2 + sw, y + hh * 0.7), (cx + 4 * s + sw, y + hh * 0.75),
                        (cx + sw, y + hh * 0.45), (cx - 4 * s + sw, y + hh * 0.75), (cx - ww / 2 + sw, y + hh * 0.7)], True, 0.4)
        else:            # one-piece folded over
            p = smooth([(cx - ww / 2, y), (cx + ww / 2, y), (cx + ww * 0.32 + sw, y + hh), (cx + sw, y + hh * 1.08),
                        (cx - ww * 0.32 + sw, y + hh)], True, 0.5)
        pen.fill(p, c); pen.texture(p, 'fabric', 0.35, 'overlay', 0.6 * s)
        pen.fill(p, '#000000', 40)
        _L(pen, p, 0, y, 0, y + hh, [(0, '#000000', 0), (1, '#000000', 70)])
        pen.line(p, 2.6 * s)
        if drip:
            drops_fall(pen, t, cx + sw * 0.5, y + hh * 0.95, y + hh + 260 * s, 1.3 + 0.4 * _h(i, seed + 3), seed + i, '#e8eef4', 3.2 * s,
                       phase=_h(i, seed + 4) * 2)


def footprint(pen, x, y, s=1.0, kind='bare', ang=0.0, k=1.0, left=True, c='#6f7d88', sheen='#f4f8fa'):
    """Wet footprint (darkened damp wood + sheen): kind 'bare' (five toes) or 'shoe' (sneaker tread)."""
    if k <= 0.01: return
    cv = pen.cv
    cv.save(); cv.translate(x, y); cv.rotate(ang); cv.scale(s * (1 if left else -1), s)
    a = int(150 * k)
    if kind == 'bare':
        sole = smooth([(0, -40), (10, -34), (14, -10), (11, 14), (13, 30), (6, 40), (-6, 40), (-11, 26), (-9, 4), (-13, -20), (-8, -38)], True, 0.8)
        pen.fill(sole, c, a)
        for j, (tx, ty, tr) in enumerate(((-7, -50, 6.5), (2, -53, 5), (9, -50, 4.4), (14, -45, 3.8), (17, -38, 3.2))):
            pen.fill(oval(tx, ty, tr, tr * 1.15), c, a)
        pen.fill(oval(-2, -22, 5, 9), sheen, int(70 * k))
    else:
        sole = smooth([(0, -46), (12, -40), (15, -14), (12, 20), (12, 40), (0, 48), (-12, 40), (-12, 16), (-14, -16), (-11, -40)], True, 0.8)
        pen.fill(sole, c, a)
        for j in range(7):
            yy = -38 + j * 12
            pen.seg((-10, yy), (10, yy + 3), 2.2, _dk(c, 0.35), int(120 * k))
        pen.fill(oval(-3, -20, 4, 10), sheen, int(60 * k))
    cv.restore()


def candy(pen, x, y, s=1.0, rot=0.0, red='#d8323e', wrapper=True):
    """Red cinnamon candy in a clear twist wrapper."""
    cv = pen.cv
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(s, s)
    if wrapper:
        for sg in (-1, 1):
            tw = poly([(sg * 18, -10), (sg * 46, -20), (sg * 52, -4), (sg * 46, 16), (sg * 18, 10)])
            pen.fill(tw, '#e8eef4', 110); pen.line(tw, 1.6, '#ffffff', 170)
            for j in range(3): pen.seg((sg * (24 + j * 8), -12 + j), (sg * (26 + j * 8), 12 - j), 1.0, '#ffffff', 150)
    b = oval(0, 0, 22, 17)
    _R(pen, b, -7, -6, 30, ['#ff8a8a', red, '#7a0e18'])
    pen.line(b, 2.2)
    pen.fill(oval(-8, -7, 6, 3.5), '#ffffff', 200)
    if wrapper: pen.fill(oval(0, 0, 25, 20), '#ffffff', 36)
    cv.restore()


def gingham(pen, path, box, c='#d8b54a', s=1.0, a=1.0, lit=1.0):
    """Yellow gingham curtain fabric (checked) with fold shading."""
    x0, y0, x1, y1 = box
    pen.fill(path, mix('#f3ead2', '#ffffff', 0.2))
    _clip(pen, path)
    step = 26 * s
    xx = x0
    while xx < x1:
        pen.fill(rect(xx, y0, step / 2, y1 - y0), c, int(120 * a)); xx += step
    yy = y0
    while yy < y1:
        pen.fill(rect(x0, yy, x1 - x0, step / 2), c, int(120 * a)); yy += step
    pen.texture(path, 'fabric', 0.35, 'overlay', 0.6 * s)
    n = 7
    for i in range(n):
        fx = lerp(x0, x1, (i + 0.5) / n)
        _L(pen, rect(fx - step, y0, step * 2, y1 - y0), fx - step, 0, fx + step, 0,
                   [(0, '#6a5a3a', 0), (0.5, '#6a5a3a', 70), (1, '#6a5a3a', 0)])
    _unclip(pen)
    pen.line(path, 2.8 * s, LINE)


def bell(pen, cx, cy, s=1.0, swing=0.0, light=0.7, crack=True, lit_from=(-1, -1), rope=True, bracket=True, red=0.0,
         vib=0.0, t=0.0, c='#b8893a'):
    """Brass breakfast bell (~30 cm, about 260 px tall at s=1), mouth at the bottom, centred at (cx, cy); swing in deg
    about the yoke; crack = the hairline crack in the rim; vib = ring vibration (rim shimmer)."""
    cv = pen.cv
    cv.save(); cv.translate(cx, cy - 120 * s); cv.rotate(swing); cv.translate(-cx, -(cy - 120 * s))
    if vib: cv.translate(vib * 3 * s * math.sin(t * 90), 0)
    if bracket:
        pen.shape(rrect(cx - 60 * s, cy - 150 * s, 120 * s, 22 * s, 6 * s), '#3a3430', 3 * s)
        pen.shape(rect(cx - 9 * s, cy - 175 * s, 18 * s, 40 * s), '#4a423a', 3 * s)
    body = smooth([(cx - 26 * s, cy - 128 * s), (cx + 26 * s, cy - 128 * s), (cx + 50 * s, cy - 90 * s), (cx + 62 * s, cy - 10 * s),
                   (cx + 96 * s, cy + 92 * s), (cx + 104 * s, cy + 112 * s), (cx - 104 * s, cy + 112 * s), (cx - 96 * s, cy + 92 * s),
                   (cx - 62 * s, cy - 10 * s), (cx - 50 * s, cy - 90 * s)], True, 0.55)
    dark, mid, hi = _dk(c, 0.62), mix(_dk(c, 0.4), c, light), mix(c, '#fff0c0', 0.5 * light)
    _L(pen, body, cx - 104 * s, 0, cx + 104 * s, 0, [dark, mid, hi, mid, dark, _dk(dark, 0.4)])
    pen.texture(body, 'grunge', 0.35, 'multiply', 0.8 * s)
    _R(pen, body, cx - 30 * s, cy + 10 * s, 70 * s, [(0, '#ffffff', 90 * light), (1, '#ffffff', 0)], sy=1.8)
    if red: _L(pen, body, cx + 104 * s, 0, cx, 0, [(0, '#ff3a50', 150 * red), (1, '#ff3a50', 0)])
    pen.line(body, 3.6 * s)
    lip = smooth([(cx - 104 * s, cy + 112 * s), (cx + 104 * s, cy + 112 * s), (cx + 100 * s, cy + 126 * s), (cx - 100 * s, cy + 126 * s)], True, 0.5)
    pen.fill(lip, _dk(c, 0.5)); pen.line(lip, 3 * s)
    for yy in (cy - 70 * s, cy + 70 * s):
        hw = 45 * s if yy < cy else 88 * s
        pen.seg((cx - hw, yy), (cx + hw, yy), 2.2 * s, _dk(c, 0.55), 160)
        pen.seg((cx - hw, yy + 3 * s), (cx + hw, yy + 3 * s), 1.2 * s, hi, 110)
    if crack:
        pts = [(cx + 38 * s, cy + 126 * s), (cx + 42 * s, cy + 108 * s), (cx + 36 * s, cy + 92 * s), (cx + 44 * s, cy + 74 * s), (cx + 40 * s, cy + 60 * s)]
        pen.line(poly(pts, False), 3.2 * s, '#120c06', 230); pen.line(poly([(x + 1.5 * s, y) for x, y in pts], False), 1.0 * s, hi, 120)
    if vib:
        pen.line(lip, 7 * s, '#fff2c8', int(120 * vib)); pen.line(body, 2 * s, '#fff2c8', int(90 * vib))
    if rope:
        sw = 18 * s * math.sin(t * 2.2) * (1 if swing == 0 else 0.3)
        pen.line(smooth([(cx, cy + 40 * s), (cx + 4 * s, cy + 160 * s), (cx + sw, cy + 300 * s)], False), 9 * s, '#8a7a5a')
        pen.line(smooth([(cx, cy + 40 * s), (cx + 4 * s, cy + 160 * s), (cx + sw, cy + 300 * s)], False), 3 * s, '#c9b890', 120)
        pen.fill(oval(cx + sw, cy + 300 * s, 12 * s, 16 * s), '#7a6a4a'); pen.line(oval(cx + sw, cy + 300 * s, 12 * s, 16 * s), 2.5 * s)
    cv.restore()
    return body


def crate(pen, x0, y0, x1, y1, s=1.0, lit=0.5, c='#8a7550', broken=0.0, stencil=True, tag=True, seed=3, lid=1.0, night=True):
    """Slatted pine crate stencilled SAVE FOR THE MUSEUM with a museum tag on string; broken = 0..1 front slats smashed in."""
    base = mix(_dk(c, 0.6), c, lit) if night else c
    pen.shadow(rect(x0, y0, x1 - x0, y1 - y0), 12 * s, 16 * s, 18 * s, '#000000', 150)
    pen.fill(rect(x0, y0, x1 - x0, y1 - y0), _dk(base, 0.7))
    n = 5; sh = (y1 - y0) / n
    for i in range(n):
        if broken > 0 and i in (2, 3) and _h(i, seed) < 0.99:
            continue
        r = rect(x0, y0 + i * sh + 4 * s, x1 - x0, sh - 9 * s)
        tone = mix(base, '#ffffff' if _h(i, seed) > 0.5 else '#000000', 0.06)
        _L(pen, r, 0, y0 + i * sh, 0, y0 + (i + 1) * sh, [_lt(tone, 0.08), tone, _dk(tone, 0.15)])
        pen.texture(r, 'wood', 0.5, 'overlay', 0.9 * s)
        pen.line(r, 3 * s)
    if broken > 0:
        for j in range(6):   # splintered stubs
            yy = y0 + 2 * sh + (j % 2) * sh + 4 * s
            xx = lerp(x0, x1, _h(j, seed + 5))
            ln = (40 + 80 * _h(j, seed + 6)) * s
            sp = poly([(x0 if j < 3 else x1, yy), (xx, yy + 6 * s), (x0 if j < 3 else x1, yy + sh - 9 * s)])
            pen.shape(sp, mix(base, '#d8c8a0', 0.3), 2.2 * s)
    for xx in (x0, x1 - 30 * s):
        cr = rect(xx, y0 - 6 * s, 30 * s, y1 - y0 + 12 * s)
        pen.fill(cr, _dk(base, 0.1)); pen.texture(cr, 'wood', 0.5, 'overlay', 0.9 * s, 90); pen.line(cr, 3 * s)
        for yy in (y0 + 10 * s, y1 - 14 * s): pen.fill(oval(xx + 15 * s, yy, 3 * s), '#1a1a1a')
    if stencil and broken < 0.5:
        fs = (y1 - y0) * 0.12
        _ttext(pen, 'SAVE FOR THE', (x0 + x1) / 2, y0 + sh * 1.55, fs * 0.9, '#121418', 250, 900, fs * 0.08, worn=0.35, seed=seed)
        _ttext(pen, 'MUSEUM', (x0 + x1) / 2, y0 + sh * 1.55 + fs * 1.15, fs * 1.25, '#121418', 250, 900, fs * 0.14, worn=0.4, seed=seed + 1)
    if tag:
        tx, ty = x1 - 70 * s, y0 + 20 * s
        pen.line(smooth([(tx - 40 * s, y0 - 4 * s), (tx - 20 * s, ty + 20 * s), (tx, ty + 34 * s)], False), 2.2 * s, '#d8d0c0')
        tg = poly([(tx - 6 * s, ty + 30 * s), (tx + 56 * s, ty + 24 * s), (tx + 66 * s, ty + 54 * s), (tx + 64 * s, ty + 100 * s), (tx, ty + 104 * s)])
        pen.shape(tg, mix('#6a6458', '#e8dcc0', lit if night else 1.0), 2.2 * s)
        pen.fill(oval(tx + 8 * s, ty + 42 * s, 5 * s), '#2a2a2a')
        if s > 0.9:
            for j, ln in enumerate(('CEDAR LAKE', 'HISTORICAL', 'SOC.')):
                _tx(pen, ln, tx + 34 * s, ty + 62 * s + j * 13 * s, 700, 10 * s, '#3a3428', 220)
    if lid < 1.0:
        pass
    return rect(x0, y0, x1 - x0, y1 - y0)


def sprinkler(pen, x, y, t, spits=(), on=None, die=None, s=1.0, c='#dfe8ea'):
    """Oscillating lawn sprinkler: comes on (hiss), each spit fires the SAME arc animation (identical replays), dies."""
    pen.shape(rrect(x - 50 * s, y - 10 * s, 100 * s, 16 * s, 6 * s), '#5a6a5a', 2.4 * s)
    pen.shape(rect(x - 6 * s, y - 34 * s, 12 * s, 26 * s), '#7a8a7a', 2.0 * s)
    pen.line(smooth([(x + 50 * s, y), (x + 140 * s, y + 18 * s), (x + 320 * s, y + 8 * s)], False), 7 * s, '#3e6a42')
    for ts in spits:
        u = (t - ts) / 0.55
        if 0 <= u <= 1:
            for j in range(14):
                ang = math.radians(-90 + (j - 6.5) * 9)
                v0 = 420 * s
                tt = u * 0.55
                px = x + math.cos(ang) * v0 * tt
                py = y - 30 * s + math.sin(ang) * v0 * tt + 0.5 * 1500 * s * tt * tt
                a = int(200 * (1 - u))
                pen.fill(oval(px, py, 4 * s, 6 * s), c, a)
                pen.fill(oval(px - math.cos(ang) * 14 * s * tt, py - math.sin(ang) * 14 * s * tt, 3 * s, 4 * s), c, a // 2)
    if on is not None and die is not None and on <= t < die + 0.6:
        k = 1 - prog(t, die, die + 0.6)
        for j in range(5):
            u = ((t - on) * 3 + j / 5) % 1.0
            pen.fill(oval(x + (j - 2) * 6 * s, y - 34 * s - u * 26 * s, 2.5 * s), c, int(150 * k * (1 - u)))


def chain_gate(pen, x0, x1, y0, y1, s=1.0, c='#5a6672', mesh_c='#7c8a98', mesh_a=110, lit=0.0):
    """Chain-link double gate with a pipe frame and a centre seam."""
    for (a, b) in ((x0, (x0 + x1) / 2 - 6 * s), ((x0 + x1) / 2 + 6 * s, x1)):
        fr = rect(a, y0, b - a, y1 - y0)
        mesh(pen, (a, y0, b, y1), 24 * s, mesh_c, mesh_a, 1.6 * s)
        pen.line(fr, 9 * s, _dk(c, 0.1)); pen.line(fr, 3 * s, _lt(c, 0.25 + 0.4 * lit), 160)
        pen.seg((a, (y0 + y1) / 2), (b, (y0 + y1) / 2), 7 * s, _dk(c, 0.1))
        pen.line(fr, 11 * s, LINE, 120)


def padlock(pen, x, y, s=1.0, lit=0.5, swing=0.0, open_=0.0, c='#8a8f96'):
    """Laminated steel padlock hanging at (x, y = top of the shackle)."""
    cv = pen.cv
    cv.save(); cv.translate(x, y); cv.rotate(swing)
    sh = smooth([(-22 * s, 40 * s - open_ * 30 * s), (-22 * s, 0), (0, -22 * s), (22 * s, 0), (22 * s, 40 * s)], False, 0.9)
    pen.line(sh, 15 * s, LINE); pen.line(sh, 10 * s, mix('#4a5058', '#c8ccd2', lit)); pen.line(sh, 3 * s, '#ffffff', int(100 * lit))
    b = rrect(-36 * s, 36 * s, 72 * s, 70 * s, 8 * s)
    _L(pen, b, -36 * s, 0, 36 * s, 0, [_dk(c, 0.5), mix(_dk(c, 0.3), c, lit), _lt(c, 0.3 * lit), _dk(c, 0.4)])
    for j in range(6): pen.seg((-36 * s, 44 * s + j * 10 * s), (36 * s, 44 * s + j * 10 * s), 1.2 * s, '#2a2e33', 160)
    pen.texture(b, 'grunge', 0.4, 'multiply', 0.5 * s)
    pen.fill(rrect(-8 * s, 64 * s, 16 * s, 26 * s, 6 * s), '#1a1c20')
    pen.line(b, 3.2 * s)
    cv.restore()


def chain(pen, pts, s=1.0, lit=0.5, c='#6a7078'):
    """Chain links along a polyline."""
    tot = 0.0; segs = []
    for i in range(len(pts) - 1):
        L = math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]); segs.append(L); tot += L
    n = int(tot / (22 * s))
    for j in range(n):
        d = j * 22 * s; i = 0
        while i < len(segs) - 1 and d > segs[i]: d -= segs[i]; i += 1
        u = d / max(1e-3, segs[i]); (ax, ay), (bx, by) = pts[i], pts[i + 1]
        px, py = lerp(ax, bx, u), lerp(ay, by, u)
        ang = math.degrees(math.atan2(by - ay, bx - ax))
        pen.cv.save(); pen.cv.translate(px, py); pen.cv.rotate(ang)
        lk = rrect(-14 * s, -(7 if j % 2 else 3) * s, 28 * s, (14 if j % 2 else 6) * s, 7 * s)
        pen.line(lk, 7 * s, LINE); pen.line(lk, 4.5 * s, mix(_dk(c, 0.5), c, lit)); pen.line(lk, 1.5 * s, '#ffffff', int(90 * lit))
        pen.cv.restore()


def sign_board(pen, x0, y0, x1, y1, s=1.0, c='#2a3a34', lit=0.4, worn=True, seed=0):
    r = rect(x0, y0, x1 - x0, y1 - y0)
    pen.shadow(r, 6 * s, 10 * s, 14 * s, '#000000', 140)
    boards(pen, (x0, y0, x1, y1), mix(_dk(c, 0.5), c, lit), True, (y1 - y0) / 3, seed, 0.5, nails=True, lw=2 * s)
    pen.line(r, 4 * s, LINE)
    return r


def cabin_ext(pen, x, y, w, h, s=1.0, num=None, c='#22303c', roof='#121a22', trim='#3a4a58', rim=MOON, rim_a=60, door=True,
              window=True, lit_win=0.0, porch=True, hasp=False, tape=False, seed=0, day=False):
    """Rustic camp cabin front (x = centre, y = ground): horizontal siding, gable roof with shingles, screened windows,
    door with number plaque, porch step. rim = moonlight on the roof edge."""
    x0, x1 = x - w / 2, x + w / 2
    wall_top = y - h
    pen.fill(rect(x0 + 18 * s, y - 6 * s, w, 16 * s), '#000000', 90)
    boards(pen, (x0, wall_top, x1, y), c, True, 26 * s, seed, 0.45, nails=False, lw=1.6 * s, var=0.08)
    pen.line(rect(x0, wall_top, w, h), 3 * s)
    ov = 30 * s; rh = h * 0.62
    rp = poly([(x0 - ov, wall_top + 8 * s), (x, wall_top - rh), (x1 + ov, wall_top + 8 * s)])
    gable = poly([(x0, wall_top), (x, wall_top - rh + 14 * s), (x1, wall_top)])
    pen.fill(gable, _dk(c, 0.12)); pen.texture(gable, 'wood', 0.4, 'overlay', 0.8 * s, 90)
    pen.line(gable, 2.5 * s)
    band = minus(rp, poly([(x0 - ov + 26 * s, wall_top + 8 * s), (x, wall_top - rh + 26 * s), (x1 + ov - 26 * s, wall_top + 8 * s)]))
    pen.fill(band, roof); pen.texture(band, 'grunge', 0.45, 'overlay', 0.9 * s)
    pen.line(band, 3 * s)
    pen.seg((x0 - ov, wall_top + 8 * s), (x, wall_top - rh), 3 * s, rim, rim_a)
    if window:
        for wx in (x0 + w * 0.2, x1 - w * 0.2 - w * 0.18):
            wr = rect(wx, wall_top + h * 0.22, w * 0.18, h * 0.32)
            if lit_win: _R(pen, wr, wx + w * 0.09, wall_top + h * 0.38, w * 0.2, ['#ffe0a0', '#b8864f'])
            else: _L(pen, wr, 0, wall_top + h * 0.22, 0, wall_top + h * 0.54, ['#1a2633', '#0a0f16'] if not day else ['#dfe6ea', '#9aa8b2'])
            mesh(pen, (wx, wall_top + h * 0.22, wx + w * 0.18, wall_top + h * 0.54), 8 * s, '#8a9aa8', 60, 0.8 * s)
            pen.line(wr, 6 * s, trim); pen.line(wr, 2 * s)
            pen.fill(rect(wx - 6 * s, wall_top + h * 0.54, w * 0.18 + 12 * s, 7 * s), trim)
    if door:
        dw, dh = w * 0.22, h * 0.72
        dr = rect(x - dw / 2, y - dh, dw, dh)
        pen.fill(dr, _dk(c, 0.3)); pen.texture(dr, 'wood', 0.4, 'overlay', 0.7 * s, 90)
        pen.line(dr, 5 * s, trim); pen.line(dr, 2 * s)
        pen.fill(oval(x + dw * 0.32, y - dh * 0.48, 4 * s), '#8a8a80')
        if num:
            pr = rrect(x - 22 * s, y - dh - 40 * s, 44 * s, 32 * s, 4 * s)
            pen.shape(pr, '#c8c0a8' if day else '#6a6658', 2 * s)
            _tx(pen, str(num), x, y - dh - 15 * s, 800, 24 * s, '#1a1a1a')
        if hasp:
            pen.fill(rect(x + dw * 0.3, y - dh * 0.56, 22 * s, 9 * s), '#5a6068'); padlock(pen, x + dw * 0.4, y - dh * 0.55, s * 0.35, 0.5)
    if porch:
        pen.shape(rect(x - w * 0.18, y - 12 * s, w * 0.36, 14 * s), _dk(c, 0.2), 2.4 * s)
    if tape:
        pen.line(smooth([(x0 - 10 * s, y - h * 0.45), (x - w * 0.3, y - h * 0.36), (x0 + w * 0.1, y - h * 0.32)], False), 7 * s, '#b8a04a', 150)
        pen.line(smooth([(x0 - 10 * s, y - h * 0.45), (x - w * 0.3, y - h * 0.36), (x0 + w * 0.1, y - h * 0.32)], False), 2 * s, '#3a3420', 120)


# ====================================================================== shared set builders
VIEWS = {}


def view(set_name, *names):
    def deco(fn):
        for n in names: VIEWS[(set_name, n)] = fn
        return fn
    return deco


def _flash_k(st, var, ramp=0.06):
    """Beam strength f(t): Tess's flashlight on (tess_on / tess_running) in *_flash / run / flash variants."""
    if var in ('moon', 'tv', 'after', 'phone_glow', 'dawn', 'dawn_queen', 'dawn_break', 'old_cabin', 'dark', 'void'): return lambda t: 0.0
    def k(t):
        v = st.v('flashlight', t)
        if v not in ('tess_on', 'tess_running'): return 0.0
        return clamp(st.since('flashlight', t) / ramp) if st.since('flashlight', t) < 1e3 else 1.0
    return k


def _night_sky(key, horizon=620, moon_xy=(1600, 160, 38), seed=1, top='#0b1822', mid='#152634', low='#2a4458'):
    def sky(pen, t):
        x0, y0, x1, y1 = FRAME
        _L(pen, rect(x0 - 600, y0 - 400, x1 - x0 + 1200, horizon + 600 - y0), 0, y0, 0, horizon,
                   [(0, top, 255), (0.6, mid, 255), (1, low, 255)])
        stars(pen, (x0 - 600, y0 - 400, x1 + 600, horizon), 260, seed, horizon - 140)
        for (cx, cy, w, h) in ((380, 120, 900, 40), (1250, 70, 1000, 34), (2100, 200, 800, 30)):
            _R(pen, None, cx, cy, w / 2, [(0, '#2a3e58', 110), (0.6, '#1c2c40', 60), (1, '#1c2c40', 0)], sy=h * 2 / w, clip=False)
            _R(pen, None, cx + w * 0.1, cy - h * 0.3, w / 3, [(0, '#5a6e90', 50), (1, '#5a6e90', 0)], sy=h / w, clip=False)
        if moon_xy: moon(pen, *moon_xy)
    tw = _live(40, lambda pen, t: twinkle(pen, t, (FRAME[0] - 600, FRAME[1] - 400, FRAME[2] + 600, horizon), 26, seed + 5, horizon - 160), 'twinkle', blur=0)
    return [_cl(40, sky, 'sky', key + ':sky', (FRAME[0] - 700, FRAME[1] - 450, FRAME[2] + 700, horizon + 700)), tw]


def _trees_far(key, y=600, depth=14.0, seed=7, h=260, c='#10202e', n=26, rim_a=50, x0=-1400, x1=3300):
    def draw(pen, t):
        pen.fill(rect(x0, y - 20, x1 - x0, 900), _dk(c, 0.2))
        treeline(pen, x0, x1, y, h * 0.75, n + 8, seed + 3, _lt(c, 0.06), MOON, rim_a // 2)
        treeline(pen, x0, x1, y + 14, h, n, seed, c, MOON, rim_a)
    return _cl(depth, draw, 'trees_far', key + ':far', (x0, y - h * 1.3 - 40, x1, y + 900))


def _mist_layer(depth, y, x0=-900, x1=2900, h=80, a=26, n=7, seed=3, c='#9ab0c8', speed=14.0, name='mist'):
    return _live(depth, lambda pen, t: mist(pen, t, y, x0, x1, h, n, seed, a, c, speed), name, blur=0)


def _sway_pines(depth, specs, c='#060d14', rim=MOON, rim_a=70, name='pines', amp=8.0):
    """Live swaying pines: specs = [(x, y, h, seed)]."""
    def draw(pen, t):
        for (x, y, h, sd) in specs:
            sw = amp * (h / 600) * (noise1(t * 0.35 + sd, sd) + 0.35 * noise1(t * 1.1 + sd, sd + 1))
            pine(pen, x, y, h, sd, c, rim, rim_a, sw, 9, 0.4)
    return _live(depth, draw, name, blur=0)


def _gravel(pen, path, box, c='#2a3440', seed=0, n=260, s=1.0):
    x0, y0, x1, y1 = box
    _L(pen, path, 0, y0, 0, y1, [_dk(c, 0.2), c, _lt(c, 0.05)])
    pen.texture(path, 'asphalt', 0.5, 'overlay', 0.8 * s)
    _clip(pen, path)
    for i in range(n):
        v = _h(i, seed + 1) ** 1.4
        px = x0 + _h(i, seed) * (x1 - x0); py = y0 + v * (y1 - y0)
        r = (1.2 + 3.5 * v) * s * (0.5 + _h(i, seed + 2))
        pen.fill(oval(px, py, r * 1.3, r), _lt(c, 0.25) if _h(i, seed + 3) > 0.5 else _dk(c, 0.4), 200)
    _unclip(pen)


def _beam_layers(st, var, src, aims, depth=1.0, wobble=10.0, seed=0, spot=170, spread=0.3, sweep=None, dust_box=None, n_dust=90,
                 moth=None, flare=0.0, w0=26.0, a=0.35, spot_sy=0.8):
    """Tess's beam + its dust (and moths near the hot spot) as live layers; returns (layers, Beam)."""
    kf = _flash_k(st, var)
    b = Beam(aim_fn(src, aims, kf, wobble, seed, sweep=sweep), w0=w0, spread=spread, spot=spot, a=a, spot_sy=spot_sy, flare=flare)
    L = [b.layer(depth, 'beam')]
    if dust_box:
        L.append(_live(depth * 0.96, lambda pen, t: motes(pen, t, dust_box, n_dust, seed + 9, b), 'dust', blur=0))
    if moth:
        def mo(pen, t):
            sx, sy, ax, ay, k = b.at(t)
            if k > 0.2: moths(pen, t, lerp(sx, ax, 0.75), lerp(sy, ay, 0.75) - 30, 70, moth, seed)
        L.append(_live(depth * 0.95, mo, 'moths', blur=0))
    return L, b


def _sp(name, layers, anchors=None, grade=None, focus=1.0, dof=0.0, fx=None, info=None, beam=None):
    info = dict(info or {})
    if beam is not None: info['beam'] = beam
    return SetPiece(name, layers, anchors, grade, focus, dof, None, fx, info)


# ====================================================================== camp_gate
def _gate_world(key, st, var, t_on=None):
    """Static gate wide: arch sign, chain-link gate, fence, notice board + MISSING poster, demolition notice, road."""
    def gate(pen, t):
        # fence both sides
        for (a, b) in ((-700, 600), (1320, 2620)):
            mesh(pen, (a, 520, b, 900), 24, '#5a6a7a', 80, 1.4)
            for xx in range(int(a), int(b) + 1, 260):
                pen.shape(rect(xx - 7, 500, 14, 410), '#2a3440', 3)
                pen.seg((xx + 5, 500), (xx + 5, 905), 2, MOON, 60)
            pen.seg((a, 520), (b, 520), 8, '#2a3440'); pen.seg((a, 516), (b, 516), 2, MOON, 70)
            for xx in range(int(a), int(b), 18):     # barbed wire
                pen.seg((xx, 500 + 4 * math.sin(xx * 0.05)), (xx + 18, 500 + 4 * math.sin((xx + 18) * 0.05)), 1.6, '#4a5866', 200)
        chain_gate(pen, 640, 1280, 480, 900, 1.0, '#4a5866', '#6e7e8e', 120)
        # log posts and the arch
        for xx in (585, 1335):
            p = rect(xx - 34, 200, 68, 720)
            _L(pen, p, xx - 34, 0, xx + 34, 0, ['#0e161e', '#26323c', '#3a4a58', '#1a242e'])
            pen.texture(p, 'wood', 0.55, 'overlay', 1.0, 90)
            for yy in range(240, 900, 70): pen.seg((xx - 30, yy), (xx + 26, yy + 8), 1.5, '#0a0e12', 160)
            pen.line(p, 4)
            pen.seg((xx + 26, 210), (xx + 26, 910), 3, MOON, 80)
            pen.fill(oval(xx, 200, 34, 12), '#3a4652'); pen.line(oval(xx, 200, 34, 12), 3)
        beam_ = rect(520, 196, 900, 46)
        _L(pen, beam_, 0, 196, 0, 242, ['#3a4a58', '#26323e', '#141c24']); pen.texture(beam_, 'wood', 0.5, 'overlay', 1.0); pen.line(beam_, 4)
        for xx in (700, 1220):
            pen.line(poly([(xx, 242), (xx + 8, 262)], False), 4, '#6a7480')
        sgn = rrect(560, 262, 800, 100, 10)
        pen.shadow(sgn, 6, 10, 14, '#000000', 150)
        boards(pen, (560, 262, 1360, 362), '#3a3226', True, 33.4, 5, 0.6, lw=2)
        pen.line(sgn, 4)
        _ttext(pen, 'CAMP CEDAR LAKE', 960, 330, 58, '#c9c0a8', 235, 900, 6, worn=0.85, seed=3)
        _ttext(pen, 'EST. 1962', 960, 354, 18, '#a8a088', 200, 800, 4, worn=0.5, seed=4)
        for i in range(9):     # peeling paint flakes
            px, py = 600 + _h(i, 9) * 720, 275 + _h(i, 10) * 80
            pen.fill(_blob(px, py, 16 + 20 * _h(i, 11), 6 + 6 * _h(i, 12), 8, i, 0.5), '#1e1a14', 200)
        # notice board with the MISSING poster
        nb = (210, 420, 450, 650)
        pen.shape(rect(232, 640, 16, 280), '#1c2630', 3); pen.shape(rect(412, 640, 16, 280), '#1c2630', 3)
        sign_board(pen, *nb, 1.0, '#2a3430', 0.5, seed=2)
        pen.shape(poly([(190, 425), (330, 380), (470, 425)]), '#141c24', 3)
        pen.shape(rect(262, 455, 140, 180), '#c9c6bc', 2.5)
        pen.fill(rect(262, 455, 140, 180), '#000000', 70)
        _tx(pen, 'MISSING', 332, 482, 900, 24, '#7a2020', 230)
        pen.shape(rect(292, 492, 80, 92), '#5a6a5a', 2)
        pen.fill(oval(332, 528, 22, 26), '#b8a090'); pen.fill(rect(304, 552, 56, 32), '#3a6a3a')
        for j in range(3): pen.seg((276, 598 + j * 10), (388, 598 + j * 10), 2, '#5a5a5a', 160)
        pen.fill(rect(420, 470, 24, 60), '#d8d0b8', 90); pen.fill(rect(226, 520, 30, 50), '#d8d0b8', 70)
        # demolition notice zip-tied to the fence
        dn = rect(1440, 600, 130, 92)
        pen.shape(dn, '#c9a636', 2.5)
        pen.fill(rect(1440, 600, 130, 22), '#1a1a1a')
        _tx(pen, 'NOTICE', 1505, 617, 900, 15, '#c9a636')
        for j in range(4): pen.seg((1452, 636 + j * 13), (1558 - 20 * (j % 2), 636 + j * 13), 3, '#3a3420', 200)
        for (zx, zy) in ((1444, 604), (1566, 604)): pen.seg((zx - 6, zy - 8), (zx + 6, zy + 8), 3, '#f0f0f0', 220)
        pen.fill(dn, '#000000', 60)
    def ground(pen, t):
        _L(pen, rect(-900, 880, 3800, 700), 0, 880, 0, 1400, ['#152634', '#233b4c'])
        road = poly([(700, 895), (1240, 895), (1900, 1500), (40, 1500)])
        _gravel(pen, road, (40, 895, 1900, 1500), '#2e4050', 3, 320)
        for sg in (-1, 1):
            pen.line(smooth([(960 + sg * 160, 900), (960 + sg * 300, 1100), (960 + sg * 460, 1420)], False), 26, '#121c24', 140)
        pen.fill(oval(1240, 1060, 150, 22), '#2c4256', 200); pen.fill(oval(1210, 1056, 60, 6), MOON, 90)
        grass(pen, -800, 700, 905, 40, 220, 3, '#0e1c28', '#4a6480')
        grass(pen, 1240, 2800, 905, 40, 220, 4, '#0e1c28', '#4a6480')
    def fg(pen, t):
        for (x, y, n, sd) in ((-160, 1180, 60, 1), (2080, 1180, 60, 2)):
            grass(pen, x - 300, x + 300, y, 260, n, sd, '#03070b', '#26384a')
    return [_cl(1.0, gate, 'gate', key + ':gate'), _cl(0.92, ground, 'ground', key + ':ground', (-900, 860, 2820, 1600)),
            _cl(0.6, fg, 'fg', key + ':fg', NEAR)]


@view('camp_gate', 'wide')
def _v_gate_wide(var, st, shot):
    key = 'gate'
    L = _night_sky(key, 600) + [_trees_far(key, 600, 14, 7, 300)]
    def camp(pen, t):
        # the lake sliver between trunks, the mess hall roof and a cabin behind the gate
        _L(pen, rect(-900, 592, 1500, 28), 0, 592, 0, 620, ['#1c3448', '#0c1824'])
        pen.shape(poly([(380, 620), (420, 560), (860, 560), (900, 620)]), '#0d1822', 2)
        pen.shape(rect(1100, 560, 200, 70), '#101c26', 2); pen.shape(poly([(1080, 562), (1200, 500), (1320, 562)]), '#0b141c', 2)
        pen.seg((1200, 500), (1080, 562), 2, MOON, 60)
    glints = _live(9, lambda pen, t: [pen.fill(oval(-500 + ((_h(i, 3) * 1300 + 9 * t * (0.5 + _h(i, 4))) % 1300), 600 + 14 * _h(i, 5),
                                                     5 + 8 * _h(i, 6), 1.2), '#c8d8ff', int(200 * max(0, math.sin(t * 3 + i)) ** 3))
                                          for i in range(18)], 'lake_glints', blur=0)
    L += [_cl(9, camp, 'camp', key + ':camp', (-900, 480, 2900, 700)), glints,
          _sway_pines(4.0, [(-120, 700, 720, 11), (180, 690, 560, 12), (1620, 700, 640, 13), (1980, 705, 780, 14)], '#0b1822', MOON, 60),
          _mist_layer(3.0, 640, a=30), _mist_layer(1.6, 880, h=70, a=22, seed=8, speed=10)]
    L += _gate_world(key, st, var)
    L.append(_live(1.3, lambda pen, t: fireflies(pen, t, (-200, 620, 2100, 960), 9, 4), 'fireflies', blur=0))
    L.append(_live(1.0, lambda pen, t: padlock(pen, 960, 700, 0.9, 0.5 + 0.4 * b.k_at(960, 720, t), 2.5 * math.sin(t * 1.7)), 'padlock', blur=0))
    L.append(_live(1.0, lambda pen, t: chain(pen, [(930, 650), (960, 705), (995, 650), (1000, 760), (950, 770)], 0.8, 0.5), 'chain', blur=0))
    bl, b = _beam_layers(st, var, (950, 640), [(st.t0, 960, 720), (st.t0 + 1.6, 1000, 700), (st.t0 + 4, 900, 730)], 1.0, 14, 3,
                         spot=150, dust_box=(500, 300, 1500, 1000), n_dust=80, moth=5)
    L += bl
    an = dict(tess_gate=Anchor(880, 960, 1.0, 600), you_gate=Anchor(1100, 960, 1.0, 620), padlock=Anchor(960, 720, 1.0, 1))
    return _sp('camp_gate/wide', L, an, beam=b)


@view('camp_gate', 'lock_cu')
def _v_gate_lock(var, st, shot):
    L = _night_sky('gatelock', 700, None)
    L.append(_trees_far('gatelock', 760, 6, 9, 600))
    def mesh_bg(pen, t):
        mesh(pen, (-600, -400, 2500, 1500), 90, '#4a5a6a', 120, 5)
    def bars(pen, t):
        for xx in (820, 1100):
            p = rect(xx - 30, -400, 60, 1900)
            _L(pen, p, xx - 30, 0, xx + 30, 0, ['#1a222a', '#4a5866', '#7a8896', '#2a3440']); pen.line(p, 6)
        _L(pen, rect(-500, 380, 2900, 50), 0, 380, 0, 430, ['#3a4652', '#1a222a']); pen.line(rect(-500, 380, 2900, 50), 6)
    L += [_cl(1.6, mesh_bg, 'mesh', 'gatelock:mesh'), _cl(1.15, bars, 'bars', 'gatelock:bars')]
    bl, b = _beam_layers(st, var, (1700, 1300), [(st.t0, 980, 600), (st.t1, 940, 620)], 1.0, 18, 5, spot=360, dust_box=(200, 0, 1800, 1100), n_dust=90, moth=6)
    L.append(_live(1.0, lambda pen, t: chain(pen, [(760, 300), (900, 420), (1050, 410), (1160, 300), (1120, 520), (960, 560)], 3.0,
                                              0.35 + 0.6 * b.k_at(960, 500, t)), 'chain', blur=0))
    L.append(_live(1.0, lambda pen, t: padlock(pen, 960, 520, 3.1, 0.35 + 0.65 * b.k_at(960, 650, t), 3 * math.sin(t * 2.1)), 'padlock', blur=0))
    L += bl
    return _sp('camp_gate/lock_cu', L, dict(padlock=Anchor(960, 560, 1.0, 1)), beam=b)


@view('camp_gate', 'keys_cu')
def _v_gate_keys(var, st, shot):
    L = _night_sky('gatekeys', 760, (1500, 220, 40))
    L.append(_trees_far('gatekeys', 800, 8, 9, 500))
    L.append(_cl(2.4, lambda pen, t: chain_gate(pen, 300, 1700, 300, 1400, 2.2, '#3a4652', '#5a6a7a', 110), 'gate_bg', 'gatekeys:gate'))
    bl, b = _beam_layers(st, var, (-200, 1200), [(st.t0, 1000, 500), (st.t1, 1080, 520)], 1.0, 24, 7, spot=300, dust_box=(300, 0, 1700, 1080), n_dust=60, moth=4)
    L += bl
    return _sp('camp_gate/keys_cu', L, dict(keys=Anchor(960, 500, 1.0, 1)), focus=1.0, dof=6.75, beam=b)


def _noah_photo(pen, x, y, w, h, faded=0.0, seed=1, polaroid=False):
    """Noah's school photo (gap-tooth grin, green sweatshirt) drawn with the cast's own bust."""
    r = rect(x, y, w, h)
    _L(pen, r, x, y, x, y + h, ['#7a8c9c', '#5a6a7a'] if not polaroid else ['#9ab0c0', '#d8c8a0'])
    _clip(pen, r)
    try:
        import characters as C
        C.draw_bust(pen, 'noah13', x + w / 2, y + h * 0.5, w / 600 * 0.95, C.Pose('grin_kid'))
    except Exception:
        pen.fill(oval(x + w / 2, y + h * 0.42, w * 0.28, h * 0.27), '#d8b8a0'); pen.fill(rect(x + w * 0.15, y + h * 0.72, w * 0.7, h * 0.3), '#3a7a3a')
    pen.fill(r, '#f0e0c0', int(60 + 90 * faded))
    pen.texture(r, 'paper', 0.4, 'overlay', 0.8)
    _unclip(pen)
    pen.line(r, 3)


@view('camp_gate', 'poster')
def _v_gate_poster(var, st, shot):
    def board(pen, t):
        boards(pen, (-500, -350, 2420, 1450), '#232e2c', False, 150, 6, 0.6, lw=4)
        pen.fill(rect(-500, -350, 2920, 1800), '#000000', 70)
        for (x, y, w, h, a) in ((140, 60, 300, 380, 120), (1520, 600, 280, 360, 90), (1560, 90, 220, 260, 110)):
            pr = rect(x, y, w, h); pen.fill(pr, '#a8a496', a); pen.texture(pr, 'paper', 0.5, 'overlay')
    def poster(pen, t):
        px, py, pw, ph = 600, 60, 720, 960
        pr = poly([(px, py), (px + pw, py + 6), (px + pw - 4, py + ph), (px + 80, py + ph - 4), (px, py + ph - 70)])
        pen.shadow(pr, 10, 16, 22, '#000000', 170)
        pen.fill(pr, '#cfcabd'); pen.texture(pr, 'paper', 0.6, 'overlay', 1.2)
        _clip(pen, pr)
        for i in range(6):   # rain stains
            sx = px + _h(i, 4) * pw
            _L(pen, rect(sx - 20, py, 40 + 30 * _h(i, 5), ph), sx, 0, sx + 40, 0, [(0, '#7a7466', 0), (0.5, '#7a7466', 60), (1, '#7a7466', 0)])
            pen.fill(_blob(sx, py + ph * (0.2 + 0.7 * _h(i, 6)), 40, 26, 9, i, 0.4), '#8a8270', 40)
        _unclip(pen)
        _tx(pen, 'MISSING', 960, 190, 900, 120, '#8a1c1c', 240, 6)
        _noah_photo(pen, 780, 215, 360, 430)
        _tx(pen, 'NOAH, 13', 960, 712, 900, 46, '#1a1a1a', 235, 3)
        _tx(pen, 'LAST SEEN: CAMP CEDAR LAKE, CABIN 7', 960, 752, 700, 26, '#1a1a1a', 220, 1)
        _tx(pen, 'LAST SEEN WEARING A GREEN SWEATSHIRT', 960, 792, 700, 24, '#1a1a1a', 210, 1)
        _tx(pen, 'IF YOU HAVE ANY INFORMATION CALL', 960, 850, 600, 20, '#2a2a2a', 190, 1)
        for j in range(3): pen.seg((760, 890 + j * 26), (1160, 890 + j * 26), 5, '#3a3a3a', 120)
        pen.fill(poly([(px, py + ph - 70), (px + 80, py + ph - 4), (px + 30, py + ph - 10)]), '#8a8676')   # torn corner curl
        for (tx, ty) in ((px + 18, py + 18), (px + pw - 20, py + 22)):
            pen.fill(oval(tx, ty, 9), '#c03030'); pen.fill(oval(tx - 3, ty - 3, 3), '#ffffff', 180)
    L = [_cl(1.25, board, 'board', 'poster:board'), _cl(1.0, poster, 'poster', 'poster:poster')]
    bl, b = _beam_layers(st, var, (-400, 900), [(st.t0, 400, 500), (st.t0 + 2.5, 1300, 420), (st.t1 + 2, 1500, 600)], 1.0, 10, 8,
                         spot=420, dust_box=(-200, -100, 2100, 1150), n_dust=70, a=0.2)
    L += bl
    return _sp('camp_gate/poster', L, {}, beam=b)


@view('camp_gate', 'notice')
def _v_gate_notice(var, st, shot):
    def bg(pen, t):
        mesh(pen, (-500, -350, 2420, 1450), 70, '#3a4a5a', 140, 4)
    def sign(pen, t):
        r = rect(560, 200, 800, 620)
        pen.shadow(r, 12, 18, 20, '#000000', 170)
        _L(pen, r, 0, 200, 0, 820, ['#d8b84a', '#b8962e']); pen.texture(r, 'grunge', 0.45, 'multiply', 1.0)
        pen.fill(rect(560, 200, 800, 120), '#141414')
        _tx(pen, 'NOTICE OF DEMOLITION', 960, 280, 900, 52, '#d8b84a', 255, 2)
        _tx(pen, 'CABINS 5 - 7', 960, 440, 900, 92, '#141414', 245, 4)
        _tx(pen, 'SATURDAY 7:00 AM', 960, 560, 800, 58, '#141414', 240, 2)
        _tx(pen, 'KEEP OUT  -  AUTHORIZED PERSONNEL ONLY', 960, 660, 700, 26, '#141414', 220, 1)
        for j in range(3): pen.seg((640, 712 + j * 28), (1280 - 120 * (j % 2), 712 + j * 28), 6, '#3a3420', 150)
        pen.fill(r, '#ffffff', 26); pen.line(r, 5)
        for (zx, zy) in ((580, 220), (1340, 220), (580, 800), (1340, 800)):
            pen.line(poly([(zx - 26, zy - 22), (zx + 26, zy + 22)], False), 8, '#e8e8e8'); pen.fill(rect(zx + 16, zy + 12, 18, 12), '#e8e8e8')
    L = _night_sky('notice', 900, None) + [_cl(1.5, bg, 'mesh', 'notice:mesh'), _cl(1.0, sign, 'sign', 'notice:sign')]
    bl, b = _beam_layers(st, var, (2300, 1200), [(st.t0, 900, 470), (st.t1, 1040, 450)], 1.0, 14, 9, spot=460, dust_box=(0, 0, 1920, 1080), n_dust=60, a=0.22)
    return _sp('camp_gate/notice', L + bl, {}, beam=b)


# ====================================================================== camp_path
@view('camp_path', 'aerial')
def _v_path_aerial(var, st, shot):
    def ground(pen, t):
        pen.fill(rect(-700, -500, 3300, 2100), '#0b1822')
        for i in range(900):     # pine crowns from above
            x = -700 + _h(i, 1) * 3300; y = -500 + _h(i, 2) * 2100
            if 300 < x < 1800 and 300 < y < 1000 and _h(i, 3) < 0.85: continue
            r = 18 + 26 * _h(i, 4)
            pen.fill(_blob(x, y, r, r, 9, i, 0.45), mix('#0a1822', '#14283a', _h(i, 5)))
            pen.fill(_blob(x + r * 0.25, y - r * 0.25, r * 0.5, r * 0.5, 7, i + 1, 0.4), '#2a4258', 90)
        clearing = _blob(1100, 680, 900, 380, 16, 3, 0.18)
        pen.fill(clearing, '#14222c'); pen.texture(clearing, 'grunge', 0.5, 'overlay', 1.4)
        for (a, b) in (((600, 680), (1500, 470)), ((900, 640), (1200, 680)), ((1200, 680), (1650, 950)), ((600, 680), (300, 760))):
            pen.line(poly([a, b], False), 22, '#27333c'); pen.line(poly([a, b], False), 8, '#34424c')
        lake = _blob(-60, -40, 640, 380, 14, 8, 0.2)
        _L(pen, lake, 0, -400, 0, 340, ['#0c1a2a', '#1c3248']); pen.line(lake, 4, '#030608')
        for (x, y, w, h, rot, n) in ((600, 640, 150, 100, -6, '5'), (900, 600, 150, 100, 4, '6'), (1200, 640, 150, 100, -3, '7'), (1500, 420, 330, 150, 2, '')):
            pen.cv.save(); pen.cv.translate(x, y); pen.cv.rotate(rot)
            pen.fill(rect(-w / 2 + 14, -h / 2 + 18, w, h), '#000000', 120)
            rp = rect(-w / 2, -h / 2, w, h)
            pen.fill(rect(-w / 2, -h / 2, w, h / 2), '#2a3a48'); pen.fill(rect(-w / 2, 0, w, h / 2), '#18232e')
            pen.texture(rp, 'grunge', 0.4, 'overlay'); pen.seg((-w / 2, 0), (w / 2, 0), 3, MOON, 120); pen.line(rp, 3)
            pen.cv.restore()
        # excavator
        ex, ey = 1350, 720
        pen.fill(rect(ex - 60, ey - 30, 120, 70), '#000000', 120)
        pen.shape(rect(ex - 70, ey - 40, 110, 70), '#a88a2a', 3); pen.shape(rect(ex - 90, ey - 46, 150, 14), '#2a2a2a', 2)
        pen.line(poly([(ex + 30, ey - 10), (ex + 120, ey - 70), (ex + 170, ey - 10)], False), 14, '#8a7020'); pen.shape(rect(ex + 150, ey - 20, 40, 30), '#4a4a4a', 2)
        # the gate and the car
        pen.shape(rect(1610, 930, 90, 10), '#4a5866', 2)
        pen.shape(rrect(1730, 980, 120, 56, 14), '#2a2e36', 3); pen.fill(rect(1752, 990, 70, 34), '#0e1218')
    lk = _live(1.0, lambda pen, t: [pen.fill(oval(160 + 30 * noise1(t * 0.5 + i, 3) + i * 7, 60 + i * 9 + 4 * math.sin(t * 2 + i), 26 - i, 2.5),
                                             '#dfe8ff', int(200 * (0.5 + 0.5 * math.sin(t * 4 + i * 1.3)))) for i in range(10)], 'moon_glint', blur=0)
    def car(pen, t):
        k = 1.0 if t < 22.6 else max(0.0, 1 - (t - 22.6) / 0.12)
        if k <= 0: return
        for dy in (-12, 12):
            _R(pen, None, 1700, 1008 + dy, 260, [(0, '#fff4d8', 130 * k), (0.4, '#fff0c8', 50 * k), (1, '#fff0c8', 0)], sy=0.35, clip=False)
            pen.fill(oval(1728, 1008 + dy, 6), '#ffffff', int(255 * k))
    fog = _live(0.8, lambda pen, t: mist(pen, t, 540, -800, 2800, 400, 8, 5, 22, '#8aa0bc', 18), 'fog', blur=0)
    return _sp('camp_path/aerial', [_cl(1.0, ground, 'ground', 'aerial:ground', (-700, -500, 2620, 1600)), lk,
                                    _live(1.0, car, 'headlights', blur=0), fog], {})


@view('camp_path', 'cabins_row')
def _v_path_cabins(var, st, shot):
    L = _night_sky('row', 640) + [_trees_far('row', 640, 12, 21, 280)]
    def far(pen, t):
        cabin_ext(pen, 300, 700, 360, 190, 0.7, '5', '#1f3040', '#0b1218', '#25323e', MOON, 50, seed=1)
        cabin_ext(pen, 740, 720, 420, 210, 0.8, '6', '#223444', '#0b1218', '#28343f', MOON, 60, seed=2)
    def near(pen, t):
        _L(pen, rect(-900, 900, 3800, 700), 0, 900, 0, 1400, ['#152634', '#22384a'])
        cabin_ext(pen, 1300, 940, 760, 400, 1.35, '7', '#2a3c4c', '#111c26', '#3a4a58', MOON, 90, hasp=True, tape=True, seed=3)
        grass(pen, -800, 2800, 945, 34, 260, 7, '#0e1c28', '#4a6480')
    def bucket(pen, t):
        b = poly([(-300, 1180), (-120, 760), (240, 700), (420, 860), (380, 1180)])
        pen.fill(b, '#05090d'); pen.line(b, 4)
        for i in range(5): pen.fill(poly([(-80 + i * 80, 1180), (-50 + i * 80, 1260), (-20 + i * 80, 1180)]), '#05090d')
        pen.seg((-120, 760), (240, 700), 4, MOON, 110); pen.seg((240, 700), (420, 860), 3, MOON, 70)
        pen.line(poly([(260, 700), (600, -300)], False), 60, '#05090d'); pen.seg((290, 700), (630, -300), 3, MOON, 80)
    L += [_cl(2.2, far, 'far_cabins', 'row:far'), _mist_layer(2.0, 760, a=26),
          _sway_pines(3.4, [(-60, 760, 700, 31), (2100, 760, 760, 32), (980, 700, 560, 33)], '#0b1822', MOON, 55),
          _cl(1.0, near, 'cabin7', 'row:near'), _cl(0.6, bucket, 'bucket', 'row:bucket', NEAR),
          _live(1.2, lambda pen, t: fireflies(pen, t, (-200, 650, 2100, 980), 7, 9), 'fireflies', blur=0),
          _live(0.9, lambda pen, t: mist(pen, t, 950, -900, 2800, 90, 6, 4, 22, '#9ab0c8', 12), 'ground_mist', blur=0)]
    return _sp('camp_path/cabins_row', L, dict(cabin7_door=Anchor(1300, 940, 1.0, 560)))


@view('camp_path', 'path_track')
def _v_path_track(var, st, shot):
    L = _night_sky('track', 600) + [_trees_far('track', 600, 14, 41, 300)]
    def mid(pen, t):
        for (x, n) in ((300, '5'), (1500, '6')): cabin_ext(pen, x, 690, 380, 190, 0.7, n, '#1f3040', '#0b1218', '#25323e', MOON, 50, seed=int(n))
        pen.shape(poly([(780, 700), (820, 620), (1180, 620), (1220, 700)]), '#0f1a22', 2)
    def path(pen, t):
        _L(pen, rect(-900, 860, 3800, 700), 0, 860, 0, 1400, ['#101c26', '#1c2a34'])
        p = poly([(-900, 905), (2900, 905), (2900, 1010), (-900, 1010)])
        _gravel(pen, p, (-900, 905, 2900, 1010), '#2e4050', 5, 500)
        grass(pen, -900, 2900, 905, 36, 320, 8, '#0e1c28', '#4a6480')
    def fence(pen, t):
        for xx in range(-1000, 3000, 340):
            post = rect(xx, 760, 46, 520)
            _L(pen, post, xx, 0, xx + 46, 0, ['#0a1016', '#1e2a34', '#2a3844']); pen.line(post, 4)
            pen.seg((xx + 40, 770), (xx + 40, 1280), 3, MOON, 70)
        for yy in (820, 960):
            r = rect(-1000, yy, 4000, 30)
            _L(pen, r, 0, yy, 0, yy + 30, ['#2a3642', '#121a22']); pen.texture(r, 'wood', 0.5, 'overlay'); pen.line(r, 3)
    L += [_cl(4.0, mid, 'mid', 'track:mid'), _mist_layer(2.5, 720, a=24),
          _sway_pines(5.0, [(100, 700, 600, 51), (900, 690, 520, 52), (1800, 700, 640, 53)], '#0b1822', MOON, 50),
          _cl(1.0, path, 'path', 'track:path', (-1400, 600, 3300, 1500))]
    bl, b = _beam_layers(st, var, (lambda t: (880 + 30 * math.sin(t * 2.4), 640)), [(st.t0, 1500, 930), (st.t1, 1560, 940)], 1.0, 22, 11,
                         spot=200, spot_sy=0.3, dust_box=(600, 500, 1900, 1000), n_dust=60, moth=4)
    L += bl + [_cl(0.6, fence, 'fence', 'track:fence', (-1800, 700, 3800, 1400)),
               _live(1.3, lambda pen, t: fireflies(pen, t, (-200, 640, 2100, 940), 8, 12), 'fireflies', blur=0)]
    an = dict(tess_path=Anchor(800, 960, 1.0, 600), you_path=Anchor(1080, 960, 1.0, 620))
    return _sp('camp_path/path_track', L, an, beam=b)


def _lodge(pen, s=1.0, c='#2a3a48', lit=0.0, day=False, sign=True):
    """Mess hall lodge front at home framing: low long building, porch roof on posts, screen door (960, 520), sign (960, 300),
    windows, stacked chairs, porch boards and steps."""
    roof = poly([(-500, 330), (2420, 330), (2300, 160), (-380, 160)])
    pen.fill(roof, '#0c141b' if not day else '#5a5a58'); pen.texture(roof, 'grunge', 0.5, 'overlay', 1.2); pen.line(roof, 4)
    pen.seg((-380, 160), (2300, 160), 3, MOON if not day else '#ffffff', 90)
    boards(pen, (-500, 330, 2420, 800), c, True, 30, 8, 0.5, nails=False, lw=1.6, var=0.06)
    pen.fill(rect(-500, 330, 2920, 60), '#000000', 120)
    for wx in (180, 520, 1320, 1660):
        wr = rect(wx, 420, 220, 170)
        _L(pen, wr, 0, 420, 0, 590, ['#121c26', '#060a0e'] if not day else ['#c8d4d8', '#8a9aa2'])
        mesh(pen, (wx, 420, wx + 220, 590), 10, '#8a9aa8', 40, 0.8)
        pen.seg((wx + 110, 420), (wx + 110, 590), 6, '#3a4652'); pen.line(wr, 9, '#3a4652'); pen.line(wr, 3)
    dr = rect(880, 380, 160, 300)
    pen.fill(dr, '#05080c'); mesh(pen, (880, 380, 1040, 680), 9, '#7a8a98', 70, 0.9)
    pen.line(dr, 12, '#3e4a56'); pen.seg((880, 530), (1040, 530), 10, '#3e4a56'); pen.line(dr, 3)
    pen.fill(oval(1022, 540, 6), '#9a9a90')
    if sign:
        sr = rrect(740, 252, 440, 78, 8)
        boards(pen, (740, 252, 1180, 330), '#3a3024', True, 26, 3, 0.6, lw=2)
        pen.line(sr, 4)
        _ttext(pen, 'MESS HALL', 960, 308, 50, '#d8ccb0', 230, 900, 4, worn=0.7, seed=12)
    for xx in (-200, 300, 700, 1220, 1620, 2120):
        post = rect(xx, 330, 36, 470)
        _L(pen, post, xx, 0, xx + 36, 0, ['#0c141a', '#26323c', '#3a4854']); pen.texture(post, 'wood', 0.5, 'overlay', 0.8, 90); pen.line(post, 3.5)
        pen.seg((xx + 32, 336), (xx + 32, 796), 2.5, MOON if not day else '#ffffff', 80)
    for k in range(4):   # stacked chairs left
        cx, cy = 420 + k * 6, 560 - k * 34
        pen.line(poly([(cx - 50, cy + 200), (cx - 40, cy), (cx + 40, cy), (cx + 50, cy + 200)], False), 6, '#3a4048')
        pen.shape(rect(cx - 52, cy + 80, 104, 14), '#4a525a', 2)
    floor = poly([(-500, 800), (2420, 800), (2600, 920), (-680, 920)])
    _L(pen, floor, 0, 800, 0, 920, ['#22303a', '#2c3a44'] if not day else ['#a89e8a', '#c8bca0'])
    pen.texture(floor, 'wood', 0.5, 'overlay', 1.2)
    for i in range(30):
        x0_ = -500 + i * 100
        pen.seg((x0_, 800), (x0_ + (x0_ - 960) * 0.06, 920), 2, '#0a0e12', 170)
    pen.line(floor, 3)
    for j in range(3):     # steps down to the path
        yy = 920 + j * 52
        st_ = rect(700 - j * 30, yy, 520 + j * 60, 52)
        _L(pen, st_, 0, yy, 0, yy + 52, ['#2e3c46', '#16202a'] if not day else ['#c8bca0', '#8a806c']); pen.texture(st_, 'wood', 0.5, 'overlay'); pen.line(st_, 3)


@view('mess_porch', 'wide')
def _v_porch_wide(var, st, shot):
    L = _night_sky('porch', 300, (300, 90, 30))
    L.append(_trees_far('porch', 330, 10, 61, 260))
    L.append(_cl(1.05, lambda pen, t: _lodge(pen), 'lodge', 'porch:lodge', (-900, 100, 2820, 1300)))
    def crate_l(pen, t): crate(pen, 1080, 700, 1290, 830, 0.55, 0.5)
    L.append(_cl(0.98, crate_l, 'crate', 'porch:crate'))
    def chimes(pen, t):
        x, y = 1400, 360
        pen.seg((x - 40, y), (x + 40, y), 4, '#5a6068')
        for i in range(5):
            sw = 6 * noise1(t * 0.9 + i * 0.6, 3) + 3 * math.sin(t * 2.3 + i)
            xx = x - 34 + i * 17
            ln = 60 + 22 * (i % 3)
            pen.seg((xx, y), (xx + sw, y + ln), 1.2, '#8a9098', 200)
            pen.shape(rrect(xx + sw - 4, y + ln, 8, 46 + 10 * (i % 2), 3), '#7a8490', 1.5)
            pen.seg((xx + sw - 2, y + ln + 4), (xx + sw - 2, y + ln + 40), 1.4, MOON, 120)
    L.append(_live(1.05, chimes, 'chimes', blur=0))
    bl, b = _beam_layers(st, var, (lambda t: (780, 700)), [(st.t0, 1180, 780), (st.t0 + 1.0, 960, 560), (st.t1, 1180, 800)], 1.0, 16, 13,
                         spot=180, dust_box=(500, 300, 1500, 1000), n_dust=70, moth=5)
    L += bl + [_mist_layer(0.9, 1010, h=60, a=20, seed=3), _live(1.3, lambda pen, t: fireflies(pen, t, (-200, 700, 2100, 1050), 7, 14), 'fireflies', blur=0)]
    an = dict(tess_steps=Anchor(800, 1060, 0.95, 600), you_steps=Anchor(1080, 1075, 0.95, 620), porch_mid=Anchor(960, 830, 1.05, 520),
              porch_left=Anchor(600, 830, 1.05, 520), crate=Anchor(1185, 820, 1.0, 1))
    return _sp('mess_porch/wide', L, an, beam=b)


def _porch_bg_blur(key, day=False):
    """Blurred lodge front for porch close-ups (depth 3: dof blurs it)."""
    return _cl(3.0, lambda pen, t: _lodge(pen, day=day), 'lodge_bg', key + (':day' if day else ''), (-900, 100, 2820, 1300))


@view('mess_porch', 'porch_low')
def _v_porch_low(var, st, shot):
    def boards_low(pen, t):
        _L(pen, rect(-900, -600, 3800, 1100), 0, -500, 0, 480, ['#0a1218', '#1a2832'])
        boards(pen, (-900, -200, 2820, 470), '#1e2a34', True, 40, 9, 0.5, nails=False)
        floor_persp(pen, -1600, 3500, 1500, 300, 1620, 470, 22, '#1a2630', '#3a4a56', 4)
    def crate_fg(pen, t):
        crate(pen, 1180, 360, 2500, 1260, 2.6, 0.55)
    L = [_cl(1.2, boards_low, 'porch', 'plow:porch', (-1400, -600, 3300, 1600)), _cl(0.7, crate_fg, 'crate', 'plow:crate', NEAR)]
    bl, b = _beam_layers(st, var, (lambda t: (300, 300)), [(st.t0, 900, 700), (st.t1, 1100, 760)], 1.0, 22, 17, spot=240, spot_sy=0.35,
                         dust_box=(0, 0, 1920, 1080), n_dust=70)
    return _sp('mess_porch/porch_low', L + bl, dict(tess_low=Anchor(800, 900, 1.0, 900)), beam=b)


@view('mess_porch', 'crate_cu')
def _v_porch_crate(var, st, shot):
    L = [_porch_bg_blur('pcrate:bg'), _cl(1.0, lambda pen, t: crate(pen, 200, 160, 1720, 980, 3.0, 0.55), 'crate', 'pcrate:crate')]
    bl, b = _beam_layers(st, var, (2400, -200), [(st.t0, 800, 520), (st.t1, 1000, 560)], 1.0, 14, 19, spot=520, dust_box=(0, 0, 1920, 1080), n_dust=80, a=0.2)
    return _sp('mess_porch/crate_cu', L + bl, {}, dof=6.75, beam=b)


def _bell_interior(pen, t, lit=0.6, day=False):
    pen.fill(rect(-800, -500, 3500, 2100), '#06090c' if not day else '#3a3428')
    _R(pen, None, 980, 640, 700, [(0, '#2a2418' if not day else '#8a7a58', 255), (1, '#06090c' if not day else '#3a3428', 255)], clip=False)
    pen.fill(rect(-800, 820, 3500, 900), '#14100a' if not day else '#5a4c36')
    pen.texture(rect(-800, 820, 3500, 900), 'wood', 0.5, 'overlay', 1.4)
    for i in range(9):    # straw / packing
        x = 300 + i * 160; pen.line(smooth([(x, 830), (x + 40, 800), (x + 90, 840)], False), 3, '#8a7a4a', 120)


@view('mess_porch', 'bell_slats')
def _v_porch_slats(var, st, shot):
    bl_, b = _beam_layers(st, var, (lambda t: (2300, -300)), [(st.t0, 600, 640), (st.t0 + 1.6, 990, 610), (st.t1, 1000, 600)], 1.0, 10, 23,
                          spot=260, dust_box=(200, 100, 1800, 1000), n_dust=60, a=0.3)
    def bell_l(pen, t): bell(pen, 980, 600, 1.15, 0.0, 0.25 + 0.75 * b.k_at(980, 600, t), True, t=t)
    def slats(pen, t):
        for i in range(-3, 9):
            x0 = -700 + i * 420
            r = rect(x0, -600, 250, 2300)
            _L(pen, r, x0, 0, x0 + 250, 0, ['#0e0b07', '#3a3022', '#5a4a34', '#1a140c']); pen.texture(r, 'wood', 0.6, 'overlay', 1.2, 90); pen.line(r, 6)
    L = [_cl(1.3, lambda pen, t: _bell_interior(pen, t), 'interior', 'slats:in', (-800, -500, 2720, 1600)), _live(1.0, bell_l, 'bell', blur=0)]
    L += bl_ + [_cl(0.7, slats, 'slats', 'slats:slats', (-1600, -700, 3600, 1800))]
    return _sp('mess_porch/bell_slats', L, dict(bell=Anchor(980, 600, 1.0, 1)), beam=b)


def _bell_ecu_layers(key, st, var, t_strike=None, day=False, shot=None):
    """The cracked rim filling the frame; strike flash + vibration after t_strike."""
    def bg(pen, t): _bell_interior(pen, t, day=day)
    def bl(pen, t):
        vib = 0.0; red = 0.0
        if t_strike is not None and t >= t_strike: vib = math.exp(-(t - t_strike) * 2.2)
        if var == 'bell_hit': red = clamp((t - 534.4) / 0.6) * 0.8
        bell(pen, 752, 58, 5.2, 0.0, 0.95 if day else 0.75, True, rope=False, bracket=False, red=red, vib=vib, t=t)
    def flare(pen, t):
        if t_strike is None or t < t_strike - 0.02: return
        u = t - t_strike
        k = math.exp(-u * 7)
        _R(pen, None, 1000, 600, 700, [(0, '#ffffff', 255 * k), (0.15, '#fff2d6', 200 * k), (1, '#fff2d6', 0)], clip=False)
        _R(pen, None, 1000, 600, 1600, [(0, '#fff2d6', 120 * k), (1, '#fff2d6', 0)], sy=0.04, clip=False)
        for j in range(10):
            ang = 2 * math.pi * _h(j, 3); d = 900 * u * (0.5 + _h(j, 4))
            pen.fill(oval(1000 + math.cos(ang) * d, 600 + math.sin(ang) * d + 400 * u * u, 4), '#ffe8b0', int(255 * max(0, 1 - u * 2)))
    L = [_cl(2.0, bg, 'interior', key + ':in' + (':d' if day else ''), (-800, -500, 2720, 1600)), _live(1.0, bl, 'bell', blur=0),
         _live(0.95, flare, 'strike_flare', blur=0)]
    return L


@view('mess_porch', 'bell_ecu')
def _v_porch_bell_ecu(var, st, shot):
    ts = st.ev('strike') or (st.change_t('bell', 'rattle'))
    L = _bell_ecu_layers('becu', st, var, ts)
    bl, b = _beam_layers(st, var, (2200, -400), [(st.t0, 960, 560), (st.t1, 1060, 600)], 1.0, 8, 29, spot=520, dust_box=(0, 0, 1920, 1080), n_dust=50, a=0.25)
    return _sp('mess_porch/bell_ecu', L + bl, {}, beam=b)


@view('mess_porch', 'porch_run')
def _v_porch_run(var, st, shot):
    L = _night_sky('prun', 300, (300, 90, 30)) + [_trees_far('prun', 330, 10, 61, 260)]
    L.append(_cl(1.3, lambda pen, t: _lodge(pen), 'lodge', 'prun:lodge', (-900, 100, 2820, 1300)))
    tb = st.ev('crate_break') or st.change_t('bell', 'crate_broken')
    ts = st.ev('strike') or st.change_t('bell', 'rattle')
    def crate_live(pen, t):
        br = st.v('bell', t) in ('crate_broken', 'fake_ringing', 'rattle')
        crate(pen, 860, 720, 1240, 900, 1.0, 0.6, broken=1.0 if br else 0.0)
        if br:
            vib = math.exp(-(t - ts) * 2.5) if (ts is not None and t >= ts) else 0.0
            rolled = 1.0 if tb is None else ease_out_cubic(prog(t, tb + 0.2, tb + 1.0))
            bell(pen, 1300 + 120 * rolled, 860, 0.62, -90 * (1 - rolled) + 8 * math.sin(t * 40) * vib, 0.7, True, rope=False,
                 bracket=False, vib=vib, t=t, red=0.6 if var == 'bell_hit' else 0.0)
        if tb is not None and t >= tb:
            u = t - tb
            for j in range(14):
                ang = -math.pi * (0.1 + 0.8 * _h(j, 5)); v = 500 + 600 * _h(j, 6)
                px = 1050 + math.cos(ang) * v * u; py = 800 + math.sin(ang) * v * u + 1400 * u * u
                if py < 1150:
                    pen.cv.save(); pen.cv.translate(px, py); pen.cv.rotate(u * 700 * (_h(j, 7) - 0.5))
                    pen.shape(rect(-14, -3, 28 + 20 * _h(j, 8), 6), '#a89060', 1.5); pen.cv.restore()
    L.append(_live(1.0, crate_live, 'crate', blur=0))
    kf = _flash_k(st, var)
    b = Beam(aim_fn(lambda t: (760 + 40 * math.sin(t * 5), 700), [(st.t0, 1050, 800)], kf, 120 if var == 'run' else 30, 31,
                    sweep=(260, 0.9) if var == 'run' else None), spot=160)
    L += [b.layer(1.0), _live(0.96, lambda pen, t: motes(pen, t, (300, 300, 1700, 1100), 70, 41, b), 'dust', blur=0)]
    def red_rim(pen, t):
        if var != 'bell_hit' or t < 534.4: return
        k = clamp((t - 534.4) / 0.8)
        _R(pen, None, 1350, 860, 600, [(0, GLOW, 70 * k), (1, GLOW, 0)], sy=0.6, clip=False)
    L.append(_live(0.99, red_rim, 'red_rim', blur=0))
    an = dict(tess_crate=Anchor(820, 960, 1.0, 640), crate=Anchor(1050, 810, 1.0, 1))
    return _sp('mess_porch/porch_run', L, an, beam=b)


@view('mess_porch', 'boot_ecu')
def _v_porch_boot(var, st, shot):
    tb = (st.sfx('wood_break') or st.sfx('crate_break') or [st.t0 + 0.3])[0]
    def boards_bg(pen, t):
        floor_persp(pen, -1800, 3700, 1500, -400, 2300, 200, 26, '#121c24', '#34424e', 6)
        _L(pen, rect(-900, -700, 3800, 900), 0, -700, 0, 200, ['#04070a', '#0e161c'])
    def slats(pen, t):
        u = max(0.0, t - tb)
        for i in range(4):
            y0 = 380 + i * 150
            if i in (1, 2) and t >= tb:
                for sgn in (-1, 1):
                    pen.cv.save(); pen.cv.translate(960 + sgn * 120, y0 + 60); pen.cv.rotate(sgn * min(35, u * 260))
                    pen.shape(rect(-sgn * 0 - (500 if sgn < 0 else 0), -55, 500, 110), '#6a5838', 4); pen.cv.restore()
                continue
            r = rect(-300, y0, 2500, 120)
            _L(pen, r, 0, y0, 0, y0 + 120, ['#7a6844', '#5a4a30', '#3a2e1c']); pen.texture(r, 'wood', 0.5, 'overlay', 1.4); pen.line(r, 5)
        for j in range(18):
            if t < tb: break
            ang = -math.pi * (0.05 + 0.9 * _h(j, 2)); v = 900 + 900 * _h(j, 3)
            px = 960 + math.cos(ang) * v * u; py = 600 + math.sin(ang) * v * u + 2600 * u * u
            pen.cv.save(); pen.cv.translate(px, py); pen.cv.rotate(u * 900 * (_h(j, 4) - 0.5))
            pen.shape(rect(-20, -4, 40 + 30 * _h(j, 5), 8), '#c8b080', 2); pen.cv.restore()
    L = [_cl(2.0, boards_bg, 'boards', 'boot:bg', (-1400, -700, 3300, 1600)), _live(1.0, slats, 'slats', blur=0)]
    kf = _flash_k(st, var)
    b = Beam(aim_fn((300, -200), [(st.t0, 900, 600)], kf, 90, 37, sweep=(200, 1.3)), spot=300)
    return _sp('mess_porch/boot_ecu', L + [b.layer(1.0)], dict(boot=Anchor(960, 640, 1.0, 900)), beam=b)


# ====================================================================== caretaker
@view('caretaker', 'wide')
def _v_caretaker(var, st, shot):
    L = _night_sky('care', 560, (420, 140, 30)) + [_trees_far('care', 560, 12, 71, 280)]
    def house(pen, t):
        _L(pen, rect(-900, 760, 3800, 800), 0, 760, 0, 1300, ['#142432', '#22384a'])
        x0, x1, yb = 880, 1520, 760
        boards(pen, (x0, 380, x1, yb), '#2a3440', True, 22, 4, 0.4, nails=False, lw=1.4, var=0.05)
        pen.line(rect(x0, 380, x1 - x0, yb - 380), 3)
        rf = poly([(x0 - 50, 390), (1200, 210), (x1 + 50, 390)])
        pen.fill(rf, '#10171e'); pen.texture(rf, 'grunge', 0.5, 'overlay'); pen.line(rf, 3); pen.seg((x0 - 50, 390), (1200, 210), 3, MOON, 80)
        pen.shape(rect(1310, 250, 36, 90), '#1a222a', 2.5)
        dr = rect(960, 540, 110, 220); pen.fill(dr, '#141c24'); pen.line(dr, 6, '#3a4652'); pen.line(dr, 2.5)
        pen.shape(rect(930, 740, 170, 20), '#1e2830', 2.5)
        wr = rect(1180, 460, 160, 120); pen.fill(wr, '#000000')
        # pickup truck
        tx, ty = 1650, 790
        body = poly([(tx, ty), (tx, ty - 80), (tx + 120, ty - 80), (tx + 160, ty - 150), (tx + 300, ty - 150), (tx + 330, ty - 80),
                     (tx + 460, ty - 80), (tx + 460, ty)])
        pen.fill(body, '#1a2430'); pen.texture(body, 'grunge', 0.4, 'overlay'); pen.line(body, 3)
        pen.fill(poly([(tx + 175, ty - 140), (tx + 290, ty - 140), (tx + 312, ty - 86), (tx + 160, ty - 86)]), '#0a1018')
        for wx in (tx + 90, tx + 370): pen.shape(oval(wx, ty, 46), '#06090c', 3); pen.fill(oval(wx, ty, 18), '#2a3036')
        pen.seg((tx + 160, ty - 150), (tx + 300, ty - 150), 2.5, MOON, 110)
        grass(pen, -900, 2900, 765, 30, 300, 9, '#0e1c28', '#4a6480')
    def window(pen, t):
        k = 0.6 + 0.4 * (0.5 + 0.5 * noise1(t * 9, 3)) * (0.7 + 0.3 * math.sin(t * 23))
        blue = 0.5 + 0.5 * noise1(t * 4, 5)
        wr = rect(1180, 460, 160, 120)
        _L(pen, wr, 0, 460, 0, 580, [mix('#ffcf8a', '#a8c8ff', blue * 0.7), mix('#c8864a', '#4a6ab8', blue * 0.6)], a=k)
        sway = 0.0
        if 70.32 - 0.1 <= t <= 71.6: sway = math.sin((t - 70.32) * 6) * math.exp(-(t - 70.32) * 2.5) * 22
        cur = smooth([(1180, 460), (1250, 460), (1246 + sway, 520), (1252 + sway * 1.3, 580), (1180, 580)], True, 0.5)
        pen.fill(cur, '#c8a070'); pen.fill(cur, '#000000', 60); pen.line(cur, 2)
        pen.line(wr, 8, '#3a4652'); pen.line(wr, 2.5); pen.seg((1260, 460), (1260, 580), 5, '#3a4652')
        _R(pen, None, 1260, 520, 380, [(0, mix('#ffcf8a', '#8ab0ff', blue * 0.6), 60 * k), (1, '#8ab0ff', 0)], sy=0.7, clip=False)
        _R(pen, None, 1260, 790, 260, [(0, mix('#ffcf8a', '#8ab0ff', blue * 0.6), 40 * k), (1, '#8ab0ff', 0)], sy=0.25, clip=False)
    def fg(pen, t):
        for (x, y, r, sd) in ((-100, 1200, 420, 1), (300, 1250, 300, 2), (2050, 1200, 460, 3)):
            pen.fill(_blob(x, y, r, r * 0.7, 14, sd, 0.3), '#020507')
            pen.fill(_blob(x + r * 0.2, y - r * 0.5, r * 0.5, r * 0.25, 10, sd + 4, 0.35), '#16243a', 120)
    L += [_cl(1.6, house, 'house', 'care:house', (-900, 150, 2820, 1400)), _live(1.6, window, 'window', blur=0),
          _mist_layer(1.4, 760, h=70, a=22), _cl(0.6, fg, 'fg', 'care:fg', NEAR),
          _live(1.2, lambda pen, t: fireflies(pen, t, (-200, 560, 2100, 900), 6, 21), 'fireflies', blur=0)]
    an = dict(tess_pass=Anchor(700, 1150, 0.6, 900), you_pass=Anchor(1000, 1160, 0.6, 930))
    return _sp('caretaker/wide', L, an)


# ====================================================================== build
DEFAULT_GRADE = {'moon': 'camp_night', 'moon_flash': 'camp_night', 'run': 'camp_night_run', 'bell_hit': 'climax_red', 'tv': 'camp_night',
                 'flash': 'cabin_flash', 'flash_low': 'cabin_flash', 'doorway_glow': 'cabin_doorway', 'red': 'climax_red',
                 'after': 'cabin_after', 'phone_glow': 'cabin_after', 'wipe': 'cabin_flash', 'old_cabin': 'mirror_old_cabin',
                 'queen': 'mirror_world', 'dark': 'mirror_world', 'void': 'mirror_world', 'void_noah': 'mirror_world',
                 'dawn': 'dawn_normal', 'dawn_queen': 'dawn_queen', 'dawn_break': 'dawn_break', 'memory_day': 'memory',
                 'memory_night': 'memory_night', 'memory_morning': 'memory_morning', 'phone': 'phone_dark', 'black': 'neutral'}


def _var_fx(var, shot):
    """Per-frame post for variants: dawn_break = red leak at the edges + exposure flicker (plus the shot's fx_post keys)."""
    fxp = (shot or {}).get('fx_post') or []
    def fx(t):
        d = {}
        if var == 'dawn_break':
            d['red'] = 0.15
            d['exposure'] = -0.12 * max(0.0, noise1(t * 7.0, 5)) - (0.25 if _h(int(t * 12), 9) < 0.08 else 0.0)
        for e in fxp:
            if e.get('t', -1) <= t < e.get('t', -1) + e.get('dur', 0.1):
                for k, v in e.items():
                    if k not in ('t', 'dur', 'note'): d[k] = d.get(k, 0.0) + v if isinstance(v, (int, float)) else v
        return d
    return fx


def build(set_name, view_name, var=None, shot=None, props=None, t0=None):
    """-> SetPiece for (set, view, variant). shot: the shots.json dict (props, changes, sfx, t0/t1, cam, grade, dof)."""
    shot = dict(shot or {})
    shot.setdefault('set', set_name); shot.setdefault('view', view_name)
    st = St(shot, props, t0)
    fn = VIEWS.get((set_name, view_name))
    if fn is None: raise KeyError('no set view %s/%s' % (set_name, view_name))
    sp = fn(var, st, shot)
    sp.grade = shot.get('grade') or sp.grade or DEFAULT_GRADE.get(var, 'neutral')
    dd = shot.get('dof')
    if isinstance(dd, dict): sp.focus, sp.dof = dd.get('focus', 1.0), dd.get('dof', 6.75)
    elif dd is not None: sp.dof = float(dd)
    modes = [c.get('mode') for c in shot.get('chars', [])]
    bg_views = ('floor_end', 'doorway', 'wide', 'two_shot', 'noah_ms', 'doorway_back', 'queen_bunk', 'cabin_door', 'porch_run')
    if modes and not sp.info.get('insert') and (all(m == 'bust' for m in modes) or
                                                (all(m in ('bust', 'hands') for m in modes) and view_name in bg_views)):
        push_back(sp, 2.6)
        if shot.get('dof') is None: sp.dof = 6.75
    fit_bounds(sp, shot)
    vfx = _var_fx(var, shot); own = sp._fx
    sp._fx = (lambda t: dict(vfx(t), **(own(t) if own else {})))
    sp.info.setdefault('st', st); sp.info['var'] = var
    return sp


def fit_bounds(sp, shot, margin=60.0):
    """Shrink every cached layer's bake rect to what this shot's camera can see of it (keys, shake, hits, roll), and key
    the cache by that rect. Without this, full-size bounds baked at push-in densities blow the engine's cache budget
    (700 MB) and layers re-bake every frame."""
    cam = (shot or {}).get('cam') or {}
    ks = cam.get('keys') or []
    if not ks: return sp
    samples = []
    for a, b in zip(ks, ks[1:] + ks[-1:]):
        for u in (0.0, 0.5):
            samples.append((lerp(a[1], b[1], u), lerp(a[2], b[2], u), max(0.3, a[3] * (b[3] / a[3]) ** u), abs(lerp(a[4] if len(a) > 4 else 0, b[4] if len(b) > 4 else 0, u))))
    sh = float(cam.get('shake') or 0.0) * 3.0 + max([h[1] for h in (cam.get('hit') or [])] + [0.0]) * 1.5
    for l in sp:
        if not l.cache or callable(l.depth): continue
        d, ref = float(l.depth), float(l.ref_depth)
        xs, ys = [], []
        for (cx, cy, z, roll) in samples:
            dc = max(0.05, d - (1.0 - 1.0 / z))
            hw, hh = 960.0 * dc / ref, 540.0 * dc / ref
            if roll:
                rr = math.radians(roll); hw, hh = hw * math.cos(rr) + hh * math.sin(rr), hh * math.cos(rr) + hw * math.sin(rr)
            px, py = 960.0 + (cx - 960.0) / ref, 540.0 + (cy - 540.0) / ref
            m = (margin + sh) / ref
            xs += [px - hw * 1.04 - m, px + hw * 1.04 + m]; ys += [py - hh * 1.04 - m, py + hh * 1.04 + m]
        b0 = l.bounds
        nb = (max(b0[0], math.floor(min(xs) / 32) * 32), max(b0[1], math.floor(min(ys) / 32) * 32),
              min(b0[2], math.ceil(max(xs) / 32) * 32), min(b0[3], math.ceil(max(ys) / 32) * 32))
        if nb[2] <= nb[0] or nb[3] <= nb[1]: continue
        l.bounds = nb
        if isinstance(l.cache, str): l.cache = '%s@%d,%d,%d,%d' % ((l.cache,) + tuple(int(v) for v in nb))
    return sp


def push_back(sp, k=2.6, dim=0.25):
    """Turn a set into the background of a face / hands close-up: every layer at depth >= 0.85 moves k times further
    (same picture at the home camera, less parallax, real depth-of-field blur) and static layers darken by `dim`."""
    for l in sp:
        if callable(l.depth): continue
        if l.depth < 0.85: continue
        l.depth = l.depth * k; l.ref_depth = l.ref_depth * k
        if l.blur == 0: l.blur = None
        if l.cache and not l.dim: l.dim = dim
    return sp


def build_shot(shot):
    """SetPiece for a plan/shots.json entry (rule cards build their live background set `bg`)."""
    if shot['set'] == 'rule_mirror' and shot.get('bg'):
        bg = shot['bg']
        s2 = dict(shot); s2['set'], s2['view'], s2['var'] = bg['set'], bg['view'], bg['var']
        sp = build(bg['set'], bg['view'], bg['var'], s2)
        own = sp._fx; extra = bg.get('post', {})
        sp._fx = (lambda t: dict(own(t), **extra))
        return sp
    return build(shot['set'], shot['view'], shot['var'], shot)


@view('black', 'black')
def _v_black(var, st, shot):
    return _sp('black', [_live(1.0, lambda pen, t: pen.fill(rect(-2000, -2000, 6000, 5000), '#000000'), 'black', blur=0)], {})


@view('camp_path', 'path')
def _v_path_path(var, st, shot):
    L = _night_sky('ppath', 520, (1500, 120, 30)) + [_trees_far('ppath', 520, 12, 81, 240)]
    def lodge_far(pen, t):
        pen.cv.save(); pen.cv.translate(960, 600); pen.cv.scale(0.42, 0.42); pen.cv.translate(-960, -600)
        _lodge(pen); crate(pen, 1080, 700, 1290, 830, 0.55, 0.4)
        pen.cv.restore()
    def ground(pen, t):
        _L(pen, rect(-900, 640, 3800, 900), 0, 640, 0, 1300, ['#142432', '#22384a'])
        p = poly([(860, 680), (1060, 680), (1500, 1400), (420, 1400)])
        _gravel(pen, p, (420, 680, 1500, 1400), '#2e4050', 6, 300)
        grass(pen, -900, 2900, 690, 28, 300, 10, '#0e1c28', '#4a6480')
        pen.fill(oval(1100, 980, 120, 18), '#2c4256', 200); pen.fill(oval(1080, 976, 46, 5), MOON, 100)
    def door(pen, t):
        for (a, b) in ((-900, 260), (1660, 2820)):
            r = rect(a, -600, b - a, 2300)
            boards(pen, (a, -600, b, 1700), '#141e28', False, 60, 3 if a < 0 else 4, 0.5)
            pen.fill(r, '#000000', 120)
        for xx in (230, 1630):
            jamb = rect(xx, -600, 60, 2300)
            _L(pen, jamb, xx, 0, xx + 60, 0, ['#1a242e', '#34424e', '#1a242e']); pen.texture(jamb, 'wood', 0.5, 'overlay', 1.0, 90); pen.line(jamb, 5)
        pen.fill(rect(-900, 1180, 3800, 600), '#0a1016'); pen.texture(rect(-900, 1180, 3800, 600), 'wood', 0.5, 'overlay', 1.2)
        pen.seg((-900, 1180), (2820, 1180), 4, MOON, 90)
    L += [_cl(3.2, lodge_far, 'lodge', 'ppath:lodge', (-400, 200, 2320, 1000)), _mist_layer(2.0, 700, a=24),
          _sway_pines(4.5, [(300, 640, 520, 91), (1650, 650, 600, 92)], '#0b1822', MOON, 50),
          _cl(1.0, ground, 'ground', 'ppath:ground', (-900, 600, 2820, 1500)),
          _live(1.4, lambda pen, t: fireflies(pen, t, (200, 560, 1700, 900), 7, 31), 'fireflies', blur=0),
          _cl(0.6, door, 'doorframe', 'ppath:door', NEAR)]
    return _sp('camp_path/path', L, {})


# ====================================================================== the mirror system
# Mirror-local coordinates = mirror_cu framing: pane x 300..1620, y -1092..2252 (centre (960, 580)), frame 88 px wide.
PANE = (300.0, -1092.0, 1620.0, 2252.0)
FW = 88.0
MPIV = (960.0, 580.0)


def mirror_xf(pen, M, tilt=0.0):
    """Push the mirror-local -> design transform M = (cx, cy, s) (+ tilt deg about the pane centre). Pair with cv.restore()."""
    cx, cy, s = M
    pen.cv.save(); pen.cv.translate(cx, cy); pen.cv.scale(s, s)
    if tilt: pen.cv.rotate(tilt)
    pen.cv.translate(-MPIV[0], -MPIV[1])


def _pane_path(grow=0.0):
    x0, y0, x1, y1 = PANE
    return rect(x0 - grow, y0 - grow, x1 - x0 + 2 * grow, y1 - y0 + 2 * grow)


def _steps_state(st, var, t):
    """-> kwargs for lipstick_steps at t from the shot state (draw-on, smears in time with the finger, wipe, erase, glow)."""
    kw = dict(drawn=7, partial=None, smear=[0.0] * 7, glow=0.0, wipe=None, fade=1.0, erased=False, last=0.0)
    sd = st.ev('step_draw')
    if sd:
        done = 5
        for (k, tk) in sd:
            if t >= tk + 0.3: done = 7 - k
            elif t >= tk: kw['partial'] = (k, (t - tk) / 0.3)
        kw['drawn'] = max(5, min(7, done if done >= 5 else 5))
        if kw['partial'] is None and t < sd[0][1]: kw['drawn'] = 5
    n0 = st.v('steps_smeared', st.t0 - 1e-3)
    n0 = int(n0) if isinstance(n0, (int, float)) else 0
    tc = None; n1 = n0
    for (tc_, d) in st.changes:
        if 'steps_smeared' in d: tc, n1 = tc_, int(d['steps_smeared'])
    sm = [1.0 if k < n0 else 0.0 for k in range(7)]
    if tc is not None and n1 > n0:
        cues = st.sfx('lipstick_smear')
        ta = cues[0] - 0.05 if cues else max(st.t0, tc - 0.35 * (n1 - n0))
        for j, k in enumerate(range(n0, n1)):
            tk = ta + (tc - ta) * (j / max(1, n1 - n0))
            if n1 - n0 == 1: tk = (cues[0] if cues else tc - 0.2)
            sm[k] = ease_out_cubic(prog(t, tk, tk + 0.22))
    kw['smear'] = sm
    if st.ev('glow') or var == 'red':
        kw['glow'] = 0.7 + 0.3 * math.sin(t * 2.4)
    er = st.ev('erase')
    wipes = st.sfx('glass_wipe')
    if var == 'wipe' and wipes:
        kw['wipe'] = lerp(120, 1000, ease_out_cubic(prog(t, wipes[0] - 0.03, wipes[0] + 1.0)))
    elif er:
        kw['wipe'] = lerp(120, 1100, prog(t, er[0], er[1]))
        kw['fade'] = 1.0 - 0.6 * prog(t, er[0], er[1] + 0.6)
    elif (var == 'red' and st.v('mirror', t) == 'mirror_again' and st.t0 > 620.0 - 1e-3) or (var == 'dark' and st.t0 > 620.0):
        kw['erased'] = True; kw['fade'] = 1.0          # after the wipe: faint smudges, and the last streak thinning (S284)
        kw['last'] = (1.0 - prog(t, st.t0 + 0.2, st.t1)) if st.t0 < 621.0 else 0.0
    return kw


def _reflection(pen, t, var, st, beam=None):
    """What the glass shows behind the 8th step (mirror-local coords, drawn larger than the pane)."""
    x0, y0, x1, y1 = PANE
    big = rect(x0 - 500, y0 - 400, x1 - x0 + 1000, y1 - y0 + 800)
    if var in ('queen', 'void', 'red', 'dark') or (var == 'flash' and st.v('mirror', t) == 'tilted'):
        base = ['#05070c', '#080c14', '#0b0d14']
        _L(pen, big, 0, y0, 0, y1, base)
        # the stairwell falling away inside the glass: faint treads converging under the 8th step
        for j in range(12):
            u = j / 12.0
            yy = 900 + 260 * u ** 0.8
            w = 420 * (1 - u) + 40
            pen.seg((575 - w, yy), (575 + w * 0.6, yy), 3 * (1 - u) + 0.8, '#3a1a24', int(150 * (1 - u)))
        red = 1.0 if var != 'dark' else 1.0
        if var == 'red': red = 1.6 + 0.4 * math.sin(t * 2.4)
        _R(pen, None, 575, 900, 520, [(0, GLOW, 70 * red), (0.4, '#5a0e1e', 60 * red), (1, '#000000', 0)], sy=0.6, clip=False)
        return
    if var == 'old_cabin':
        _old_cabin_refl(pen, t, st)
        return
    # ours at night: the dark cabin behind the viewer, Tess's lamp reflected
    _L(pen, big, 0, y0, 0, y1, ['#142232', '#1c2e3e', '#24384a', '#121c26'])
    for (bx, bw_) in ((360, 360), (1180, 420)):
        pen.fill(rect(bx, 60, bw_, 900), '#070c12', 200)
        pen.fill(rect(bx, 540, bw_, 70), '#22303c', 160)
        pen.fill(rect(bx, 250, bw_, 40), '#1a2632', 150)
    wr = rect(820, 140, 300, 240)
    _L(pen, wr, 0, 140, 0, 380, ['#3a5068', '#1c2c3c']); pen.seg((970, 140), (970, 380), 12, '#0a1018'); pen.line(wr, 14, '#0a1018')
    _R(pen, None, 970, 260, 420, [(0, MOON, 40), (1, MOON, 0)], clip=False)


def _old_cabin_refl(pen, t, st, floor_view=False, part='all'):
    """The cabin as it was (theirs palette, 6:59 AM, morning) seen in the glass: made bunks, swimsuits dripping on the
    top-bunk rail, the door swinging in, wet footprints appearing to Noah's bunk (times from the shot's wet_footstep cues)."""
    x0, y0, x1, y1 = PANE
    if part in ('all', 'static'):
        _L(pen, rect(x0 - 500, y0 - 400, x1 - x0 + 1000, y1 - y0 + 800), 0, 100, 0, 1200, ['#bcbcb8', '#d2d0ca', '#a4a6a4'])
        boards(pen, (-200, -600, 2200, 860), '#c6c4bc', False, 74, 31, 0.35, seam='#8f9394', seam_a=140, nails=False, hi='#f2f0ea')
        floor_persp(pen, -900, 2900, 1700, -200, 2200, 860, 22, '#969896', '#b8b6b0', 7, seam='#6f7b84')
        _L(pen, rect(860, 300, 230, 560), 0, 300, 0, 860, ['#fbf6e6', '#e8e2cc'])
        pen.line(rect(860, 300, 230, 560), 8, '#7f8b94')
        bunk(pen, 160, 760, 900, 1.0, '#9a9a94', '#7f8b94', '#6a7680', True, True, '#7f8b94', lit=0.5, y_mat=(690, 780), y_top=(400, 440), posts_c='#a8a8a2')
        bunk(pen, 1180, 1900, 900, 1.0, '#9a9a94', '#7f8b94', '#6a7680', True, True, '#5a7a8a', lit=0.5, y_mat=(690, 780), y_top=(400, 440), posts_c='#a8a8a2')
    if part == 'static': return
    # door at the back (swings in during S074)
    sw = 0.0
    for c in st.sfx_cues('door_creak'):
        sw = ease_out_cubic(prog(t, c['t'], c['t'] + 1.6))
    if st.v('mirror', t) == 'tilted' and not st.sfx('door_creak') and st.t0 >= 163.5: sw = 1.0
    dr = rect(860, 300, 230, 560)
    if sw <= 0.05: _L(pen, dr, 0, 300, 0, 860, ['#8a8e90', '#7a7e80'])
    if sw > 0.05:
        _R(pen, None, 975, 900, 500, [(0, '#fff6dc', 140 * sw), (1, '#fff6dc', 0)], sy=0.3, clip=False)
        shaft(pen, [(860, 860), (1090, 860), (1300, 1500), (700, 1500)], '#fff6dc', int(90 * sw))
    dw = 230 * (1 - 0.82 * sw)
    door = poly([(860, 300), (860 + dw, 300 - 30 * sw), (860 + dw, 860 + 30 * sw), (860, 860)])
    pen.fill(door, '#9aa0a0'); _L(pen, door, 860, 0, 1090, 0, [(0, '#ffffff', 40), (1, '#000000', 40)]); pen.line(door, 3.5, '#4a4e50')
    dipk = 0.0
    fp = st.sfx_cues('wet_footstep')
    if fp and t >= fp[-1]['t']: dipk = ease_out_cubic(prog(t, fp[-1]['t'], fp[-1]['t'] + 0.8))
    if st.t0 >= 172.2: dipk = max(dipk, ease_in_out(prog(t, st.t0 + 0.3, st.t0 + 1.2)))
    if dipk > 0.01:      # the mattress dips by itself: a shadow pressing into the blanket
        _R(pen, None, 1500, 700, 150, [(0, '#3a4650', 120 * dipk), (1, '#3a4650', 0)], sy=0.3, clip=False)
        pen.line(smooth([(1380, 690), (1500, 690 + 24 * dipk), (1620, 690)], False), 4, '#4a5660', int(200 * dipk))
    swimsuits(pen, 1230, 1840, 440, t, 1.0, 1.0, 4, True)
    # wet footprints: door -> Noah's bunk
    prints = _footprint_track(st)
    for (tp, x, y, kind, ang, left) in prints:
        if t >= tp:
            k = ease_out_cubic(prog(t, tp, tp + 0.18))
            footprint(pen, x, y, 0.9 + 0.5 * (y - 860) / 800, kind, ang, k, left, '#6f7d88')
            if t - tp < 0.5: _R(pen, None, x, y, 60, [(0, '#ffffff', 90 * (1 - (t - tp) / 0.5)), (1, '#ffffff', 0)], sy=0.4, clip=False)


def _footprint_track(st):
    """Two trails from the door to Noah's bunk: bare (left trail) and shoe/bare alternating (right). Times = the shot's
    wet_footstep cues (params.bare), else every 0.42 s from the plan's 'appearing every 0.42 s from T'."""
    cues = st.sfx_cues('wet_footstep')
    fp = st.ev('footprints')
    if not cues and fp and isinstance(fp, list):
        cues = [dict(t=fp[0] + 0.42 * i, params=dict(bare=(i % 2 == 0))) for i in range(8)]
    out = []
    path = [(980, 880), (1060, 940), (1140, 1000), (1220, 1050), (1300, 1090), (1380, 1120), (1450, 1130), (1510, 1120)]
    nb = ns = 0
    for c in cues:
        bare = (c.get('params') or {}).get('bare', True)
        if bare: i, off, kind = nb, -34, 'bare'; nb += 1
        else: i, off, kind = ns, 34, ('shoe' if ns % 2 == 0 else 'bare'); ns += 1
        i = min(i, len(path) - 1)
        x, y = path[i]
        out.append((c['t'], x + off * (1 if i % 2 else 0.7), y + off * 0.4, kind, 62.0, i % 2 == 0))
    return out


def mirror_layers(key, st, var, shot, M=(960.0, 580.0, 1.0), tilt=0.0, wall=None, beam=None, refl_depth=2.2, cache_steps=None,
                  counter_roll=None):
    """Layers of the mirror at transform M: reflection (depth refl_depth), the wall with a pane hole (1.15), the 8th line
    (1.04, level or counter-rotated), glass surface + lipstick (1.0), frame. wall(pen, t) draws the wall around it."""
    L = []
    cx, cy, s = M
    def refl(pen, t):
        cv = pen.cv; cv.save()
        cv.translate(cx, cy); cv.scale(s, s); cv.translate(-MPIV[0], -MPIV[1])
        _reflection(pen, t, var, st, beam)
        cv.restore()
    rb = (cx - 1500 * s - 300, cy - 2200 * s - 300, cx + 1500 * s + 300, cy + 2200 * s + 300)
    if var == 'old_cabin':
        def refl_part(part):
            def d(pen, t):
                cv = pen.cv; cv.save(); cv.translate(cx, cy); cv.scale(s, s); cv.translate(-MPIV[0], -MPIV[1])
                _old_cabin_refl(pen, t, st, part=part); cv.restore()
            return d
        L.append(_cl(refl_depth, refl_part('static'), 'reflection', '%s:oldrefl' % key, rb))
        L.append(_live(refl_depth, refl_part('dynamic'), 'reflection_live', blur=0))
    elif var == 'red': L.append(_live(refl_depth, refl, 'reflection', blur=0))
    else: L.append(_cl(refl_depth, refl, 'reflection', '%s:refl:%s:%s' % (key, var, st.v('mirror', st.t0) == 'tilted'),
                       (cx - 1500 * s - 300, cy - 2200 * s - 300, cx + 1500 * s + 300, cy + 2200 * s + 300)))
    if wall is not None:
        def wall_hole(pen, t):
            cv = pen.cv
            cv.saveLayer(None, None)
            wall(pen, t)
            mirror_xf(pen, M, tilt)
            pclear = skia.Paint(AntiAlias=True); pclear.setBlendMode(skia.BlendMode.kClear)
            cv.drawPath(_pane_path(FW * 0.5), pclear)
            cv.restore(); cv.restore()
        L.append(_cl(1.15, wall_hole, 'wall', '%s:wall:%.1f' % (key, tilt), NEAR))
    # the eighth step (other side of the glass)
    tdraw = st.ev('eighth_draw')
    def eighth(pen, t):
        ev = st.v('eighth', t)
        if ev != 'present' and not (tdraw is not None and t >= tdraw): return
        k = 1.0
        if var == 'dark': k = 1 - prog(t, 628.18, 628.48)
        rot = -counter_roll(t) if counter_roll else 0.0
        cv = pen.cv; cv.save(); cv.translate(cx, cy); cv.scale(s, s); cv.translate(-MPIV[0], -MPIV[1])
        eighth_line(pen, t, tdraw, 0.6, k, 1.3 if var in ('queen', 'red') else 1.0, rot)
        cv.restore()
    L.append(_live(1.04, eighth, 'eighth', blur=0))
    # glass surface: sheen, desilvering, dust, smudges (cached), fog breath (live)
    def surface(pen, t):
        mirror_xf(pen, M, tilt)
        pp = _pane_path()
        x0, y0, x1, y1 = PANE
        _L(pen, pp, x0, y0, x1, y1, [(0, '#9fb6d8', 26), (0.45, '#ffffff', 10), (0.55, '#ffffff', 22), (1, '#9fb6d8', 8)])
        _clip(pen, pp)
        for i in range(70):
            e = i % 4; u = _h(i, 3)
            if e == 0: px, py = x0 + 30 * _h(i, 4) ** 2, y0 + u * (y1 - y0)
            elif e == 1: px, py = x1 - 30 * _h(i, 4) ** 2, y0 + u * (y1 - y0)
            else: px, py = x0 + u * (x1 - x0), (y0 if e == 2 else y1) + (1 if e == 2 else -1) * 40 * _h(i, 4)
            rr = 6 + 34 * _h(i, 5) ** 2
            pen.fill(_blob(px, py, rr, rr * 0.8, 9, i, 0.5), '#9aa0a6', 40 + int(70 * _h(i, 6)))
            pen.fill(_blob(px, py, rr * 0.45, rr * 0.4, 7, i + 1, 0.5), '#1a1e22', 110)
        pen.texture(pp, 'grunge', 0.16, 'screen', 1.6)
        for i in range(6):
            px = 450 + _h(i, 40) * 1000; py = 200 + _h(i, 41) * 800
            _R(pen, None, px, py, 70, [(0, '#c8d2dc', 26), (0.6, '#c8d2dc', 10), (1, '#c8d2dc', 0)], sy=0.6, clip=False)
            for j in range(5): pen.line(oval(px + 6 * j, py + 3 * j, 22 + 7 * j, 30 + 7 * j), 1.2, '#c8d2dc', 22)
        _unclip(pen)
        pen.cv.restore()
        if var != 'none':
            mirror_xf(pen, M, tilt)
            mirror_frame(pen, x0, y0, x1, y1, FW, 4.0, 0.55 if var in ('flash', 'wipe') else 0.3)
            pen.cv.restore()
    L.append(_cl(1.0, surface, 'glass', '%s:glass:%.1f:%s' % (key, tilt, var in ('flash', 'wipe')), NEAR))
    tfog = st.ev('fog')
    if tfog:
        def fog(pen, t):
            k = ease_out_cubic(prog(t, tfog, tfog + 0.4)) * (1 - prog(t, tfog + 0.8, tfog + 2.5))
            if k <= 0: return
            mirror_xf(pen, M, tilt)
            _R(pen, None, 700, 760, 260, [(0, '#dfe6ee', 120 * k), (0.6, '#dfe6ee', 60 * k), (1, '#dfe6ee', 0)], sy=0.8, clip=False)
            pen.cv.restore()
        L.append(_live(0.99, fog, 'fog_breath', blur=0))
    # lipstick on the glass
    animated = bool(st.ev('step_draw') or st.ev('erase') or var in ('wipe', 'red') or
                    any('steps_smeared' in d for (_, d) in st.changes))
    def steps(pen, t):
        if var == 'dark' and t >= 628.18 + 0.3: return
        kw = _steps_state(st, var, t)
        if var == 'dark': kw['fade'] = 1 - prog(t, 628.18, 628.48)
        mirror_xf(pen, M, tilt)
        lipstick_steps(pen, t, **kw)
        pen.cv.restore()
    if shot.get('view') in ('queen_face', 'queen_mouth'): pass
    elif animated: L.append(_live(0.995, steps, 'steps', blur=0))
    else: L.append(_cl(0.995, steps, 'steps', '%s:steps:%.1f:%s:%s' % (key, tilt, var, st.v('steps_smeared', st.t0)), NEAR))
    if var == 'dark':
        def drain(pen, t):
            k = prog(t, 628.18, 628.48)
            if k <= 0: return
            mirror_xf(pen, M, tilt); pen.fill(_pane_path(), '#000000', int(250 * ease_in_cubic(k))); pen.cv.restore()
        L.append(_live(0.99, drain, 'drain', blur=0))
    return L


# ====================================================================== Cabin 7 (our side)
CAB_MIRROR = (1190.0, 665.0, 0.111)       # mirror transform in cabin_now/wide
OTS_MIRROR = (960.0, 520.0, 300.0 / 1320.0)


def _cabin7_back(pen, t, lit=0.5, door_hole=None):
    """Back wall (x 60..1860, y 200..860), window hole x 780..1100 y 300..560 (outside drawn by another layer), cubbies with
    the NOAH label, clock nail, ceiling rafters, side walls, floorboards with a smooth unbroken dust film."""
    wall = '#25394a'
    _L(pen, rect(-900, -700, 3800, 2600), 0, -700, 0, 1600, ['#05090d', '#0e1820'])
    # ceiling
    ceil = poly([(-900, -700), (2820, -700), (1860, 200), (60, 200)])
    _L(pen, ceil, 0, -700, 0, 200, ['#070c11', '#141f28']); pen.texture(ceil, 'wood', 0.35, 'overlay', 1.2)
    for i in range(9):
        u = i / 8
        pen.line(poly([(lerp(-900, 2820, u), -700), (lerp(60, 1860, u), 200)], False), 26, '#0a1016')
        pen.seg((lerp(-900, 2820, u) + 10, -700), (lerp(60, 1860, u) + 4, 200), 3, '#2a3a48', 120)
    # side walls
    for (pts, a) in (([(-900, -700), (60, 200), (60, 860), (-900, 1600)], 0), ([(1860, 200), (2820, -700), (2820, 1600), (1860, 860)], 1)):
        p = poly(pts)
        _L(pen, p, pts[0][0], 0, pts[1][0], 0, ['#0c141b', '#18242f'] if a == 0 else ['#18242f', '#0c141b'])
        pen.texture(p, 'wood', 0.4, 'overlay', 1.2, 90)
        for j in range(14):
            u = j / 13
            xa = lerp(pts[0][0], pts[1][0], u); ya0 = lerp(pts[0][1], pts[1][1], u); ya1 = lerp(pts[3][1], pts[2][1], u)
            pen.seg((xa, ya0), (xa, ya1), 2, '#05080b', 170)
    boards(pen, (60, 200, 1860, 860), wall, False, 64, 5, 0.5, var=0.12)
    _L(pen, rect(60, 200, 1800, 660), 0, 200, 0, 860, [(0, '#000000', 90), (0.4, '#000000', 0), (1, '#000000', 60)])
    _L(pen, rect(60, 200, 1800, 660), 60, 0, 1860, 0, [(0, '#000000', 110), (0.2, '#000000', 0), (0.8, '#000000', 0), (1, '#000000', 110)])
    pen.fill(rect(60, 840, 1800, 22), '#121a22'); pen.seg((60, 840), (1860, 840), 2, '#3a4a58', 120)
    # window hole + trim + sill
    hole = rect(780, 300, 320, 260)
    cv = pen.cv; pc = skia.Paint(AntiAlias=True); pc.setBlendMode(skia.BlendMode.kClear); cv.drawPath(hole, pc)
    pen.line(rect(770, 290, 340, 280), 22, '#2c3a46'); pen.line(rect(758, 278, 364, 304), 4)
    pen.seg((940, 300), (940, 560), 10, '#2c3a46'); pen.seg((780, 430), (1100, 430), 10, '#2c3a46')
    sill = rect(748, 556, 384, 26)
    _L(pen, sill, 0, 556, 0, 582, ['#4a5a68', '#26323e']); pen.texture(sill, 'wood', 0.5, 'overlay'); pen.line(sill, 3)
    dust_film(pen, rect(748, 556, 384, 8), 60)
    # cubbies
    for r_ in range(3):
        for c_ in range(2):
            cb = rect(600 + c_ * 82, 380 + r_ * 92, 78, 88)
            pen.fill(cb, '#0b1117'); pen.line(cb, 6, '#2c3844'); pen.line(cb, 2)
            pen.fill(rect(600 + c_ * 82 + 4, 380 + r_ * 92 + 60, 70, 24), '#000000', 90)
            lab = rect(612 + c_ * 82, 384 + r_ * 92 + 64, 54, 14)
            pen.fill(lab, '#8a8470', 200)
            nm = ['NOAH', 'M.K.', 'DEV', 'SAM', 'J', 'ELI'][r_ * 2 + c_]
            _tx(pen, nm, 639 + c_ * 82, 384 + r_ * 92 + 76, 700, 11, '#1a1a2a', 220)
    pen.fill(rect(604, 416, 70, 50), '#3a5a3a', 70)   # a folded green thing in Noah's cubby
    # floor with an even, unbroken dust film
    fl = floor_persp(pen, -900, 2820, 1600, 60, 1860, 860, 26, '#1f2f3c', '#35495c', 9)
    pen.texture(fl, 'grunge', 0.22, 'screen', 1.8)
    _L(pen, fl, 0, 860, 0, 1600, [(0, '#8a98a6', 26), (1, '#8a98a6', 10)])


def _cabin7_bunks(pen, t, lit=0.4, mirror_under=True):
    bunk(pen, -80, 520, 880, 1.0, '#2e3a46', '#3e4c5a', '#28323e', True, False, lit=lit, y_mat=(690, 780), y_top=(420, 470))
    bunk(pen, 1260, 2000, 880, 1.0, '#2e3a46', '#3e4c5a', '#28323e', True, False, lit=lit, y_mat=(690, 780), y_top=(420, 470))
    if mirror_under:     # the towel bundle in the dark under Noah's bunk
        tb = smooth([(1380, 860), (1400, 830), (1700, 826), (1730, 858)], True, 0.6)
        towel_cloth(pen, tb, (1380, 826, 1730, 860), 0.5, 0, 3, 0.25)


def _window_out(pen, t, day=False):
    """Night outside Cabin 7's window: sky, moon glow, pines (static)."""
    _L(pen, rect(700, 220, 480, 420), 0, 220, 0, 560, ['#1a3048', '#2a4560', '#203648'])
    stars(pen, (700, 220, 1180, 420), 30, 5, 400)
    _R(pen, None, 1060, 300, 300, [(0, MOON, 90), (1, MOON, 0)], clip=False)
    treeline(pen, 640, 1240, 560, 200, 6, 13, '#0b1822', MOON, 60)


def _moon_shafts(pen, t):
    shaft(pen, [(780, 300), (1100, 300), (1500, 1300), (700, 1300)], MOON, 46, 4)
    _R(pen, None, 1040, 1060, 360, [(0, MOON, 40), (1, MOON, 0)], sy=0.3, clip=False)


def _cabin_light_layers(key, var, st, t_grow=None):
    """Variant light over cabin_now: doorway_glow (warm pale light + rays + haze from the doorway/mirror spot), red (lipstick
    red, slow pulse), phone_glow (faint red from the sill phone), after (flashlight on the floor raking the dust)."""
    L = []
    dx, dy = CAB_MIRROR[0], CAB_MIRROR[1]
    if var == 'doorway_glow':
        def glow(pen, t):
            _R(pen, None, dx, dy, 900, [(0, '#fff3dc', 150), (0.25, '#f3e3c4', 70), (1, '#f3e3c4', 0)], sy=0.75, clip=False)
            shaft(pen, [(dx - 70, dy + 190), (dx + 70, dy + 190), (dx + 520, 1400), (dx - 560, 1400)], '#fff0d0', 70, 5)
            for j in range(7):
                a0 = -0.9 + j * 0.3
                _L(pen, poly([(dx, dy), (dx + 1600 * math.cos(a0 + 1.57) - 30, dy + 1600 * math.sin(a0 + 1.57)),
                                 (dx + 1600 * math.cos(a0 + 1.57) + 30, dy + 1600 * math.sin(a0 + 1.57))]), dx, dy, dx, dy + 900,
                           [(0, '#fff6e4', 40), (1, '#fff6e4', 0)])
        grow = (lambda t: ease_in_out(prog(t, t_grow, t_grow + 2.2))) if t_grow else 1.0
        L.append(_cl(1.12, glow, 'doorway_light', key + ':dglow', NEAR, alpha=grow))
    if var == 'red':
        def redg(pen, t):
            _R(pen, None, dx, dy, 1100, [(0, GLOW, 120), (0.3, RED, 60), (1, RED, 0)], sy=0.7, clip=False)
            shaft(pen, [(dx - 70, dy + 190), (dx + 70, dy + 190), (dx + 520, 1400), (dx - 560, 1400)], RED, 60, 4)
        L.append(_cl(1.12, redg, 'red_light', key + ':red', NEAR, alpha=lambda t: 0.75 + 0.25 * math.sin(t * 2.0)))
    return L


@view('cabin_now', 'wide')
def _v_cab_wide(var, st, shot):
    key = 'cab7'
    L = [_cl(6.0, lambda pen, t: _window_out(pen, t), 'outside', key + ':out', (600, 150, 1300, 700)),
         _cl(1.18, lambda pen, t: _cabin7_back(pen, t), 'room', key + ':room', NEAR)]
    L.append(_cl(1.12, _moon_shafts, 'moon', key + ':moon', NEAR))
    mstate = st.v('mirror', st.t0)
    under = mstate in ('not_found', 'wrapped_under_bunk', 'hook_glass')
    L.append(_cl(1.0, lambda pen, t: _cabin7_bunks(pen, t, 0.4, under), 'bunks', key + ':bunks:%s' % under, NEAR))
    # the clock
    L.append(_live(1.18, lambda pen, t: wall_clock(pen, 560, 300, 44, *_clock_sec(t, st)), 'clock', blur=0))
    # phone on the sill
    def phone(pen, t):
        if st.v('phone', t) in ('sill_face_up', 'screen_steps'):
            phone_prop(pen, 1060, 552, 46, 18, 0.0, lit=0.6, red=0.6 if var == 'phone_glow' else 0.0, dust=0.0)
    L.append(_live(1.17, phone, 'phone', blur=0))
    # the mirror / doorway at the mirror spot
    def doorway(pen, t):
        ds = st.v('doorway', t)
        m = st.v('mirror', t)
        if ds == 'open' or m == 'gone':
            x0, y0, x1, y1 = dx_ = (1118, 470, 1262, 860)
            hole = poly([(x0, y0), (x1, y0 + 4), (x1 - 3, y1), (x0 + 2, y1)])
            _L(pen, hole, 0, y0, 0, y1, ['#f6f2e8', '#e2ded2'] if var != 'red' else ['#ff8a96', '#c63449'])
            _R(pen, hole, 1190, 700, 160, [(0, '#ffffff', 200), (1, '#ffffff', 0)])
            for i in range(10):
                yy = lerp(y0, y1, i / 9)
                pen.seg((x0 - 4 - 8 * _h(i, 3), yy), (x0 + 4, yy + 20), 3, '#6a5a44', 200)
                pen.seg((x1 + 4 + 8 * _h(i, 4), yy), (x1 - 4, yy + 20), 3, '#6a5a44', 200)
            pen.line(hole, 3, '#3a2e22')
    L.append(_live(1.16, doorway, 'doorway', blur=0))
    if mstate in ('held_upright', 'tilted', 'towel_over', 'mirror_again', 'dark'):
        tl = TILT if mstate == 'tilted' else 0.0
        L += [l for l in mirror_layers(key + 'm', st, 'flash' if var in ('flash', 'flash_low') else var, shot, CAB_MIRROR, tl)
              if l.name != 'wall']
    L += _cabin_light_layers(key, var, st, t_grow=st.t0 if (var == 'doorway_glow' and st.since('mirror', st.t0) < 3.5) else None)
    # Tess's beam
    tm = Anchor(1440, 960, 1.0, 600)
    aims = {'flash': [(st.t0, 1190, 680)], 'flash_low': [(st.t0, 900, 1060), (st.t1, 1100, 1000)],
            'doorway_glow': [(st.t0, 1190, 660)], 'red': [(st.t0, 1250, 700), (st.t1, 1000, 760)]}.get(var, [(st.t0, 1190, 680)])
    bl, b = _beam_layers(st, var, (1400, 700), aims, 1.0, 9, 41, spot=110, dust_box=(500, 250, 1700, 1250), n_dust=110)
    L += bl
    if var in ('after', 'phone_glow'):
        b2 = Beam(lambda t: (330, 975, 1500, 1010, 1.0), w0=20, spread=0.16, spot=260, spot_sy=0.25, a=0.3)
        L += [b2.layer(0.95, 'floor_beam'), _live(0.94, lambda pen, t: motes(pen, t, (200, 700, 1900, 1200), 90, 43, b2), 'dust_floor', blur=0)]
        L.append(_live(0.95, lambda pen, t: _flashlight_on_floor(pen, 300, 980, 1.0), 'flashlight', blur=0))
    if var == 'doorway_glow':
        gb = Beam(lambda t: (1190, 640, 1190, 1250, 1.0), w0=140, spread=0.45, spot=0, a=0.0)
        L.append(_live(0.97, lambda pen, t: motes(pen, t, (700, 400, 1700, 1300), 90, 47, gb, c='#fff6e4'), 'dust_glow', blur=0))
    if var == 'red':
        rb = Beam(lambda t: (1190, 640, 1190, 1250, 1.0), w0=140, spread=0.45, spot=0, a=0.0)
        L.append(_live(0.97, lambda pen, t: motes(pen, t, (700, 300, 1700, 1300), 100, 49, rb, c='#ff9aa8', fall=14), 'dust_red', blur=0))
    an = dict(tess_mirror=Anchor(1440, 960, 1.0, 600), you_mirror=Anchor(1090, 950, 1.0, 590), noah_stand=Anchor(1560, 950, 1.0, 640),
              doorway_mid=Anchor(1190, 862, 1.16, 400), mirror=Anchor(1190, 665, 1.0, 1))
    return _sp('cabin_now/wide', L, an, beam=b)


def _flashlight_on_floor(pen, x, y, s=1.0):
    body = rrect(x - 90 * s, y - 16 * s, 150 * s, 32 * s, 12 * s)
    pen.shadow(body, 6 * s, 10 * s, 10 * s, '#000000', 160)
    _L(pen, body, 0, y - 16 * s, 0, y + 16 * s, ['#5a626a', '#2a3036', '#14181c']); pen.line(body, 3 * s)
    hd = rrect(x + 50 * s, y - 24 * s, 46 * s, 48 * s, 8 * s)
    _L(pen, hd, 0, y - 24 * s, 0, y + 24 * s, ['#6a727a', '#3a4046']); pen.line(hd, 3 * s)
    pen.fill(oval(x + 96 * s, y, 8 * s, 22 * s), '#fff8ee'); _R(pen, None, x + 100 * s, y, 70 * s, [(0, '#ffffff', 220), (1, CORE, 0)], clip=False)


# ====================================================================== mirror (close-ups of the glass)
def _cam_roll_fn(shot):
    """Camera roll (deg) over the shot from cam.keys (linear), for counter-rotating the 8th line under a rolled camera."""
    ks = (shot or {}).get('cam', {}).get('keys') or []
    if not ks or all(abs(k[4] if len(k) > 4 else 0) < 1e-3 for k in ks): return None
    def f(t):
        if t <= ks[0][0]: return ks[0][4]
        for a, b in zip(ks, ks[1:]):
            if t <= b[0]: return lerp(a[4], b[4], prog(t, a[0], b[0]))
        return ks[-1][4]
    return f


def _mirror_wall(pen, t):
    """The back wall around the leaning mirror, in mirror_cu framing (boards ~3.7x the wide scale)."""
    boards(pen, (-1400, -1000, 3300, 1300), '#24384a', False, 230, 15, 0.6, lw=5)
    pen.fill(rect(-1400, -1000, 4700, 2300), '#000000', 70)
    _R(pen, None, 960, 580, 1500, [(0, '#2a3e4e', 90), (1, '#2a3e4e', 0)], clip=False)
    pen.fill(rect(-1400, 1180, 4700, 900), '#141e28')


@view('mirror', 'mirror_cu', 'queen_step_tilt', 'queen_face', 'queen_mouth')
def _v_mirror_cu(var, st, shot):
    key = 'mcu'
    m0 = st.v('mirror', st.t0)
    vname = shot.get('view', 'mirror_cu')
    tilted = (m0 == 'tilted')
    roll = _cam_roll_fn(shot)
    tilt = TILT if (tilted and roll is None) else 0.0
    counter = roll if (tilted and roll is not None) else None
    if vname in ('queen_face', 'queen_mouth'): tilt = 0.0
    sv = var
    if var == 'flash' and tilted and vname == 'queen_step_tilt': sv = 'flash'
    kf = _flash_k(st, var if var not in ('queen', 'red') else 'flash')
    hook = m0 == 'hook_glass'
    aims = [(st.t0, 1180 + (40 * (st.t1 - st.t0) if hook else 0), 420), (st.t1, 1180 - 40 * (st.t1 - st.t0) * 0, 430)]
    if hook: aims = [(st.t0, 1060, 430), (st.t1, 1060 + 40 * (st.t1 - st.t0), 450)]
    b = Beam(aim_fn((2500, 1500), aims, (lambda t: 1.0) if hook else kf, 10, 51), w0=40, spread=0.28, spot=300, spot_sy=0.9, a=0.22)
    if var in ('dark', 'old_cabin') or (var == 'queen' and vname in ('queen_face', 'queen_mouth')): b.fn = None
    L = mirror_layers(key, st, sv, shot, (960, 580, 1.0), tilt, _mirror_wall, b, counter_roll=counter)
    # beam glare on the glass (the brightest thing in the shot) + dust in front of the glass
    def glare(pen, t):
        sx, sy, ax, ay, k = b.at(t)
        if k <= 0.01: return
        _R(pen, None, ax, ay, 300, [(0, '#ffffff', 120 * k), (0.15, CORE, 90 * k), (0.5, FALL, 30 * k), (1, FALL, 0)], sy=0.85, clip=False)
        _R(pen, None, ax, ay, 700, [(0, CORE, 50 * k), (1, CORE, 0)], sy=0.06, clip=False)
    L.append(_live(0.99, glare, 'glare', blur=0))
    L.append(_live(0.9, lambda pen, t: motes(pen, t, (-200, -100, 2100, 1200), 110, 53, b, amb=0.05 if var != 'dark' else 0.0), 'dust', blur=0))
    if var == 'red':
        L.append(_live(0.98, lambda pen, t: _R(pen, None, 575, 860, 1100, [(0, GLOW, 50 + 20 * math.sin(t * 2.4)), (1, GLOW, 0)], sy=0.7, clip=False),
                       'red_glow', blur=0))
    if var == 'wipe' or (st.ev('erase') and vname == 'mirror_cu') or (var == 'red' and vname == 'mirror_cu' and st.t0 >= 619.9):
        L.append(_live(0.97, lambda pen, t: _towel_wipe(pen, t, st, var), 'towel', blur=0))
    an = dict(eighth=Anchor(575, 860, 1.04, 230), queen_step=Anchor(575, 860, 1.04, 230), top_step=Anchor(*STEP_XY[0], 1.0, 1),
              bottom_step=Anchor(*STEP_XY[6], 1.0, 1), queen_face=Anchor(960, 560, 1.04, 1.4))
    info = dict(tilt=tilt, counter_roll=counter, mirror_xf=(960, 580, 1.0), steps=STEP_XY, eighth=EIGHTH)
    return _sp('mirror/' + vname, L, an, beam=b, info=info)


def _towel_wipe(pen, t, st, var):
    """The striped towel bunched in your hands, dragging down the glass along the wipe line (hook S003, S283, S284)."""
    kw = _steps_state(st, var, t)
    y = kw['wipe']
    if y is None:
        if st.t0 >= 619.9: y = 700 + 220 * math.sin((t - st.t0) * 1.4)
        else: return
    x = 960 + 160 * math.sin(t * 3.1)
    if var == 'red' and st.t0 >= 619.9: x = 700 + 300 * prog(t, st.t0, st.t1)
    pts = []
    for i in range(18):
        a = 2 * math.pi * i / 18
        r = 1 + 0.16 * math.sin(a * 3 + 1) + 0.1 * (_h(i, 7) - 0.5) + 0.05 * math.sin(t * 6 + i)
        pts.append((x + math.cos(a) * 470 * r, y + math.sin(a) * 200 * r))
    path = smooth(pts, True, 0.85)
    pen.shadow(path, 20, 30, 40, '#000000', 150)
    towel_cloth(pen, path, (x - 520, y - 240, x + 520, y + 240), 1.7, 0.0, 7, 0.8)
    for j in range(6):     # folds and bunches
        fx = x - 330 + j * 130 + 30 * _h(j, 3)
        pen.line(smooth([(fx, y - 160), (fx + 40, y - 40), (fx - 10, y + 70), (fx + 30, y + 160)], False), 9, '#000000', 60)
        pen.line(smooth([(fx + 16, y - 150), (fx + 54, y - 40), (fx + 6, y + 60)], False), 4, '#ffffff', 50)
    for i in range(0, 18, 2):    # terry fringe
        px, py = pts[i]
        pen.seg((px, py), (px + 10 * math.cos(i), py + 16), 3, '#efe6d6', 160)
    pen.line(path, 7, LINE)


def _old_cabin_frame_layers(key, st, shot, M=(960, 580, 1.0), tilt=TILT):
    """Dark frame + our cabin wall around the pale reflection (old_cabin_refl)."""
    return mirror_layers(key, st, 'old_cabin', shot, M, tilt, _mirror_wall, None, refl_depth=2.0)


@view('mirror', 'old_cabin_refl')
def _v_old_refl(var, st, shot):
    # the reflection seen through the tilted dark frame at a wider framing (pane spans ~70 % of the frame)
    M = (960, 560, 0.42)
    L = _old_cabin_frame_layers('ocr', st, shot, M, TILT)
    L.append(_live(0.9, lambda pen, t: motes(pen, t, (-200, -100, 2100, 1200), 70, 57, None, amb=0.12, c='#dfe6ee'), 'dust', blur=0))
    an = dict(noah_bunk_refl=Anchor(960 + (1540 - 960) * 0.42, 560 + (900 - 580) * 0.42, 2.0, 1))
    return _sp('mirror/old_cabin_refl', L, an, info=dict(mirror_xf=M, tilt=TILT))


@view('mirror', 'old_cabin_floor')
def _v_old_floor(var, st, shot):
    """Low on the reflected floorboards: prints appearing toward the bunk (in the pale world, glass sheen over it)."""
    def floor_part(part):
        def d(pen, t):
            pen.cv.save(); pen.cv.translate(960, 540); pen.cv.scale(1.9, 1.9); pen.cv.translate(-1160, -1000)
            _old_cabin_refl(pen, t, st, True, part)
            pen.cv.restore()
        return d
    def sheen(pen, t):
        _L(pen, rect(-600, -400, 3100, 1900), -600, -400, 2500, 1500, [(0, '#ffffff', 0), (0.45, '#ffffff', 26), (0.5, '#ffffff', 8), (1, '#ffffff', 0)])
        pen.texture(rect(-600, -400, 3100, 1900), 'grunge', 0.1, 'screen', 2.0)
        _R(pen, None, 960, 540, 1500, [(0, '#000000', 0), (0.6, '#000000', 0), (1, '#05070c', 220)], sy=0.6, clip=False)
    L = [_cl(1.6, floor_part('static'), 'old_floor', 'ocf:static', NEAR), _live(1.6, floor_part('dynamic'), 'old_floor_live', blur=0),
         _cl(1.0, sheen, 'glass_sheen', 'ocf:sheen', NEAR)]
    return _sp('mirror/old_cabin_floor', L, {})


# ---------------------------------------------------------------------- cabin_now: closer views and inserts
def _zoom(fn, cx, cy, m, tx=960.0, ty=540.0):
    """Draw fn magnified m about design point (cx, cy) -> (tx, ty) (closer framings of the same room stay consistent)."""
    def d(pen, t):
        pen.cv.save(); pen.cv.translate(tx, ty); pen.cv.scale(m, m); pen.cv.translate(-cx, -cy); fn(pen, t); pen.cv.restore()
    return d


def _cabin7_all(pen, t, under=False, mirror='none', doorway=None):
    """The whole static room in one draw (outside, back wall, moon shafts, bunks): backgrounds for inserts."""
    _window_out(pen, t); _cabin7_back(pen, t); _moon_shafts(pen, t); _cabin7_bunks(pen, t, 0.4, under)
    if doorway == 'glass':
        _L(pen, rect(1118, 470, 144, 390), 0, 470, 0, 860, ['#0e141c', '#05080c']); pen.line(rect(1118, 470, 144, 390), 4, '#2a2e33')
    elif doorway in ('open', 'glow'):
        _L(pen, rect(1118, 470, 144, 390), 0, 470, 0, 860, ['#f6f2e8', '#d8d4c8'])
    elif mirror in ('held_upright', 'tilted'):
        pen.fill(rect(1110, 470, 160, 400), '#d8d4c8', 120); pen.fill(rect(1124, 484, 132, 372), '#121c26')


def _light_over(var, key, cx=960, cy=540, depth=2.9):
    """Variant light washes for close views (kept cheap: cached radials with animated alpha)."""
    if var == 'doorway_glow':
        return [_cl(depth, lambda pen, t: _R(pen, None, cx + 300, cy - 100, 1300, [(0, '#fff3dc', 110), (0.5, '#f3e3c4', 40), (1, '#f3e3c4', 0)], clip=False),
                    'glow', key + ':glow', NEAR)]
    if var == 'red':
        return [_cl(depth, lambda pen, t: _R(pen, None, cx + 200, cy - 100, 1400, [(0, GLOW, 120), (0.5, RED, 50), (1, RED, 0)], clip=False),
                    'red_light', key + ':red', NEAR, alpha=lambda t: 0.75 + 0.25 * math.sin(t * 2.0))]
    if var == 'phone_glow':
        return [_cl(depth, lambda pen, t: _R(pen, None, cx, cy + 100, 900, [(0, GLOW, 40), (1, GLOW, 0)], clip=False), 'phone_red', key + ':pred', NEAR,
                    alpha=lambda t: 0.6 + 0.4 * math.sin(t * 1.3))]
    return []


def _insert_bg(key, var, st, cx, cy, m=2.4, doorway=None, depth=3.0):
    """Blurred cabin behind a close-up (depth 3 -> sigma 4.5 with focus 1, dof 6.75), lit for the variant."""
    dw = doorway or st.v('doorway', st.t0)
    fn = _zoom(lambda pen, t: _cabin7_all(pen, t, False, st.v('mirror', st.t0), dw), cx, cy, m)
    L = [_cl(depth, fn, 'room_bg', '%s:bg:%s' % (key, dw), NEAR)]
    L += _light_over(var, key)
    if var in ('flash', 'flash_low', 'doorway_glow'):
        L.append(_live(2.5, lambda pen, t: hot_spot(pen, 960 + 260 * noise1(t * 0.4, 3), 500 + 120 * noise1(t * 0.3, 4), 520, 0.6 * _flash_k(st, var)(t)), 'beam_spill', blur=0))
    if var in ('after', 'phone_glow'):
        L.append(_cl(2.5, lambda pen, t: _R(pen, None, 960, 900, 1300, [(0, CORE, 60), (1, CORE, 0)], sy=0.25, clip=False), 'floor_beam', key + ':fb', NEAR))
    return L


def _motes_layer(depth, box, n, seed, beam=None, c=CORE, amb=0.1, **kw):
    return _live(depth, lambda pen, t: motes(pen, t, box, n, seed, beam, c, amb, **kw), 'dust', blur=0)


@view('cabin_now', 'cabin_door')
def _v_cab_door(var, st, shot):
    ts = (st.sfx('door_creak') or [st.t0 - 10])[0]
    def wall(pen, t):
        pen.fill(rect(-900, -600, 3800, 2300), '#0a1016')
        boards(pen, (-900, 100, 2820, 900), '#22364a', False, 80, 21, 0.5)
        floor_persp(pen, -1500, 3400, 1600, -300, 2200, 900, 26, '#1a2834', '#34485a', 13)
        _L(pen, poly([(-900, -600), (2820, -600), (2200, 100), (-300, 100)]), 0, -600, 0, 100, ['#05090d', '#121c26'])
        bunk(pen, -700, 420, 980, 1.15, '#2e3a46', '#3e4c5a', '#28323e', True, False, y_mat=(760, 860), y_top=(450, 500))
        bunk(pen, 1520, 2700, 980, 1.15, '#2e3a46', '#3e4c5a', '#28323e', True, False, y_mat=(760, 860), y_top=(450, 500))
        pc = skia.Paint(AntiAlias=True); pc.setBlendMode(skia.BlendMode.kClear); pen.cv.drawPath(rect(800, 220, 320, 690), pc)
    def outside(pen, t):
        _L(pen, rect(780, 200, 360, 720), 0, 200, 0, 900, ['#1a3048', '#2a4560', '#1c2c3a'])
        treeline(pen, 700, 1220, 700, 260, 4, 17, '#0b1822', MOON, 80)
        pen.fill(rect(780, 700, 360, 220), '#22384a'); grass(pen, 780, 1140, 702, 20, 30, 3, '#0e1c28', '#4a6480')
    def door(pen, t):
        u = ease_in_out(prog(t, ts, ts + 1.5)) if t >= ts else 0.0
        if st.t0 > 400: u = 0.92
        u = u + 0.02 * math.sin(t * 1.3) * (1 if u > 0.5 else 0)
        w = 320 * (1 - u) + 30 * u
        ext = 80 * u
        d = poly([(800, 220), (800 - ext + 0 + w * 0 + (w if u < 0.5 else 0) * 0, 220), (800, 220)])
        dp = poly([(800, 220), (800 + w - ext, 220 - 40 * u), (800 + w - ext, 910 + 60 * u), (800, 910)]) if u < 0.98 else None
        if dp is not None:
            _L(pen, dp, 800, 0, 800 + w, 0, ['#26323c', '#3a4854'])
            pen.texture(dp, 'wood', 0.5, 'overlay', 0.9, 90); pen.line(dp, 4)
            pen.fill(oval(800 + w * 0.85 - ext, 560, 6 + 4 * u), '#8a8a80')
        pen.line(rect(790, 210, 340, 710), 18, '#2c3a46'); pen.line(rect(780, 200, 360, 730), 4)
        if u > 0.05:
            _L(pen, poly([(800 + w, 910), (1120, 910), (1500, 1500), (700, 1500)]), 0, 910, 0, 1500, [(0, MOON, 70 * u), (1, MOON, 0)])
    L = [_cl(6.0, outside, 'outside', 'cdoor:out', (600, 100, 1300, 1000)), _cl(1.2, wall, 'room', 'cdoor:room', NEAR),
         _live(1.18, door, 'door', blur=0)]
    kf = _flash_k(st, var)
    b = Beam(aim_fn((960, 640), [(ts, 1000, 1000), (ts + 0.8, 300, 900), (ts + 2.2, 1700, 880), (ts + 4.0, 600, 860)], kf, 14, 61),
             w0=30, spread=0.3, spot=200, spot_sy=0.5)
    if st.t0 > 400: b.fn = None
    L += [b.layer(1.0), _motes_layer(0.95, (100, 200, 1800, 1200), 110, 63, b)]
    return _sp('cabin_now/cabin_door', L, dict(tess_door=Anchor(960, 930, 1.18, 600)), beam=b)


@view('cabin_now', 'under_bunk')
def _v_cab_under(var, st, shot):
    def floor(pen, t):
        pen.fill(rect(-900, -600, 3800, 2300), '#06090d')
        floor_persp(pen, -1900, 3800, 1500, 200, 1700, 560, 30, '#1a2a38', '#3e566c', 17)
        _L(pen, rect(-900, 560, 3800, 1000), 0, 560, 0, 1500, [(0, '#000000', 120), (0.5, '#000000', 20), (1, '#000000', 0)])
        for (x, y, r) in ((300, 640, 60), (1500, 620, 50), (1750, 900, 80)):
            pen.fill(_blob(x, y, r, r * 0.4, 12, int(x), 0.5), '#5a6470', 140)
        pen.line(smooth([(1650, 560), (1780, 470), (1900, 560)], False), 1.2, '#9aa6b2', 90)
    def bundle(pen, t):
        top = poly([(640, 700), (1320, 700), (1440, 830), (540, 830)])
        pen.shadow(top, 10, 20, 24, '#000000', 180)
        towel_cloth(pen, top, (540, 700, 1440, 830), 0.9, 0, 9, 0.55)
        side = poly([(540, 830), (1440, 830), (1440, 852), (540, 852)])
        towel_cloth(pen, side, (540, 830, 1440, 852), 0.5, 0, 10, 0.35)
        dust_film(pen, top, 70)
        pen.line(smooth([(700, 720), (900, 760), (1200, 740), (1380, 800)], False), 4, '#000000', 80)
    def slats(pen, t):
        pen.fill(rect(-1400, -700, 4800, 760), '#0a0f14')
        for i in range(-6, 16):
            x0 = -1400 + i * 260
            r = rect(x0, -700, 200, 840)
            _L(pen, r, x0, 0, x0 + 200, 0, ['#1a2430', '#34424e', '#1a2430']); pen.texture(r, 'wood', 0.5, 'overlay', 1.0, 90); pen.line(r, 4)
        pen.fill(rect(-1400, 120, 4800, 40), '#05080b')
        for x in (-200, 2100):
            pen.shape(rect(x, -700, 120, 2400), '#1a2430', 4)
    kf = _flash_k(st, var)
    b = Beam(aim_fn((-300, 900), [(st.t0, 900, 780), (st.t1, 1000, 760)], kf, 10, 67), w0=40, spread=0.22, spot=330, spot_sy=0.35)
    L = [_cl(1.3, floor, 'floor', 'under:floor', NEAR), _cl(1.0, bundle, 'mirror_bundle', 'under:bundle', NEAR), b.layer(1.0),
         _motes_layer(0.9, (0, 300, 1920, 1080), 90, 69, b, fall=4), _cl(0.7, slats, 'slats', 'under:slats', NEAR)]
    return _sp('cabin_now/under_bunk', L, dict(bundle=Anchor(980, 760, 1.0, 1)), beam=b)


@view('cabin_now', 'towel_label')
def _v_cab_label(var, st, shot):
    def towel(pen, t):
        r = rect(-600, -400, 3100, 1900)
        towel_cloth(pen, r, (-600, -400, 2500, 1500), 3.2, 0, 11, 0.6)
        for j in range(4):
            pen.line(smooth([(-600, 200 + j * 280), (400, 260 + j * 280), (1300, 180 + j * 280), (2500, 240 + j * 280)], False), 30, '#000000', 50)
        tag = poly([(820, 470), (1160, 450), (1172, 640), (830, 662)])
        pen.shadow(tag, 6, 10, 14, '#000000', 140)
        pen.fill(tag, '#d8d4c6'); pen.texture(tag, 'fabric', 0.5, 'overlay', 0.6); pen.line(tag, 4)
        for j in range(3): pen.seg((840, 490 + j * 8), (1150, 472 + j * 8), 1.5, '#a8a49a', 200)
        _ttext(pen, 'NOAH', 1000, 600, 110, '#1e2a4a', 220, 800, 4, rot=-3.5, worn=0.25, seed=5)
        pen.fill(tag, '#000000', 50)
    kf = _flash_k(st, var)
    b = Beam(aim_fn((2600, -300), [(st.t0, 1000, 560), (st.t1, 960, 580)], kf, 12, 71), spot=480, spot_sy=0.8, a=0.15)
    L = [_cl(1.0, towel, 'towel', 'label:towel', NEAR), b.layer(0.98), _motes_layer(0.9, (0, 0, 1920, 1080), 60, 73, b)]
    return _sp('cabin_now/towel_label', L, {}, beam=b)


def _ots_wall(pen, t):
    """Cabin back wall around the leaning mirror at the over-the-shoulder scale (2.05x the wide)."""
    _zoom(lambda p, tt: (_window_out(p, tt), _cabin7_back(p, tt), _moon_shafts(p, tt), _cabin7_bunks(p, tt, 0.4, False)), 1190, 665, 2.05, 960, 520)(pen, t)


@view('cabin_now', 'mirror_ots')
def _v_cab_ots(var, st, shot):
    kf = _flash_k(st, var)
    b = Beam(aim_fn((1700, 820), [(st.t0, 990, 470), (st.t1, 960, 500)], kf, 10, 77), w0=34, spread=0.26, spot=140, spot_sy=0.9, a=0.3)
    L = mirror_layers('ots', st, 'flash', shot, OTS_MIRROR, TILT if st.v('mirror', st.t0) == 'tilted' else 0.0, _ots_wall, b)
    def towel(pen, t):
        tw = st.v('towel', t)
        if tw == 'wrapped':
            mirror_xf(pen, OTS_MIRROR)
            p = smooth([(180, -1200), (1740, -1180), (1780, 2340), (200, 2360)], True, 0.2)
            towel_cloth(pen, p, (180, -1200, 1780, 2360), 4.0, 0, 13, 0.6)
            pen.cv.restore()
        elif tw == 'over_mirror':
            mirror_xf(pen, OTS_MIRROR)
            sag = 120 * (1 - ease_out_cubic(prog(t, st.t0, st.t0 + 0.4)))
            p = smooth([(160, -1220 + sag), (960, -1300 + sag), (1760, -1220 + sag), (1820, 2380), (960, 2440), (120, 2380)], True, 0.5)
            towel_cloth(pen, p, (120, -1300, 1820, 2440), 4.0, 0, 13, 0.6)
            pen.cv.restore()
    L += [_live(0.99, towel, 'towel', blur=0), b.layer(0.98), _motes_layer(0.92, (300, 0, 1700, 1100), 100, 79, b)]
    an = dict(you_mirror=Anchor(560, 1240, 0.7, 980), tess_mirror=Anchor(1500, 1040, 0.95, 640), mirror=Anchor(960, 520, 1.0, 1))
    return _sp('cabin_now/mirror_ots', L, an, beam=b, info=dict(mirror_xf=OTS_MIRROR))


@view('cabin_now', 'two_shot')
def _v_cab_two(var, st, shot):
    L = _insert_bg('two', var, st, 820, 600, 1.7, depth=2.6)
    kf = _flash_k(st, var)
    b = Beam(aim_fn((1240, 640), [(st.t0, 1900, 700)], kf, 8, 81), w0=30, spread=0.25, spot=0, a=0.25)
    def mirror_edge(pen, t):     # the mirror in profile at the right edge, glowing with the beam's reflection
        x = 1840
        pen.fill(poly([(x, 120), (x + 60, 100), (x + 90, 1200), (x + 20, 1220)]), '#c8c4b8'); pen.line(poly([(x, 120), (x + 60, 100), (x + 90, 1200), (x + 20, 1220)]), 5)
        _R(pen, None, x - 40, 560, 600, [(0, CORE, 70 * kf(t)), (1, CORE, 0)], sy=0.9, clip=False)
    L += [_live(1.05, mirror_edge, 'mirror_edge', blur=0), b.layer(1.0), _motes_layer(0.95, (200, 100, 1900, 1100), 90, 83, b, amb=0.12)]
    an = dict(you_mirror=Anchor(640, 1100, 1.0, 860), tess_mirror=Anchor(1340, 1110, 1.0, 840))
    return _sp('cabin_now/two_shot', L, an, beam=b, dof=4.0)


@view('cabin_now', 'sill')
def _v_cab_sill(var, st, shot):
    def win(pen, t):
        _L(pen, rect(-600, -500, 3200, 1100), 0, -500, 0, 580, ['#122236', '#2a4560', '#22384c'])
        stars(pen, (-600, -500, 2600, 300), 60, 9, 300)
        _R(pen, None, 1500, 0, 600, [(0, MOON, 110), (1, MOON, 0)], clip=False)
        treeline(pen, -600, 2600, 580, 380, 10, 23, '#0b1822', MOON, 70)
    def sill(pen, t):
        pen.line(rect(-200, -300, 2320, 880), 60, '#2c3a46'); pen.seg((960, -300), (960, 560), 40, '#2c3a46')
        mesh(pen, (-200, -300, 2120, 580), 26, '#8a9aa8', 55, 1.2, torn=(1450, 200, 260))
        pen.line(_blob(1450, 200, 262, 210, 11, 5, 0.45), 2.5, '#8a9aa8', 120)
        top = poly([(-500, 580), (2420, 580), (2620, 700), (-700, 700)])
        _L(pen, top, 0, 580, 0, 700, ['#3e4e5c', '#56687a']); pen.texture(top, 'wood', 0.6, 'overlay', 1.6)
        dust_film(pen, top, 90)
        front = rect(-700, 700, 3320, 90)
        _L(pen, front, 0, 700, 0, 790, ['#2a3846', '#141c24']); pen.line(front, 4)
        boards(pen, (-700, 790, 2620, 1500), '#1c2c3a', False, 150, 25, 0.5)
        for i in range(40):
            x = -400 + _h(i, 3) * 2800; pen.fill(oval(x, 590 + 100 * _h(i, 4), 2 + 4 * _h(i, 5), 1.5 + 2 * _h(i, 6)), '#9aa6b2', 120)
    def phone(pen, t):
        if st.v('phone', t) in ('sill_face_up', 'screen_steps'):
            dt = st.since('phone', t)
            drop = 0.0 if dt > 0.25 else (1 - dt / 0.25) * 30
            red = 0.35 + 0.25 * math.sin(t * 1.7) if var in ('flash', 'after') else 0.6
            pen.cv.save(); pen.cv.translate(960, 630 - drop); pen.cv.scale(1.0, 0.42)
            phone_prop(pen, 0, 0, 300, 600, 8, lit=0.8, red=red, dust=0.5)
            pen.cv.restore()
            _R(pen, None, 1010, 610, 40, [(0, '#ff6070', 200), (1, GLOW, 0)], clip=False)
    kf = _flash_k(st, var)
    b = Beam(aim_fn((-300, 200), [(st.t0, 900, 640), (st.t1, 1000, 640)], kf, 10, 87), spot=420, spot_sy=0.35, a=0.2)
    L = [_cl(5.0, win, 'outside', 'sill:out', (-800, -700, 2800, 700)), _cl(1.0, sill, 'sill', 'sill:sill', NEAR),
         _cl(0.99, _moon_sill, 'moon', 'sill:moon', NEAR), _live(0.98, phone, 'phone', blur=0), b.layer(0.97),
         _motes_layer(0.9, (0, 0, 1920, 1080), 80, 89, b, amb=0.14, c='#dfe8ff')]
    return _sp('cabin_now/sill', L, dict(phone=Anchor(960, 630, 1.0, 1)), beam=b)


def _moon_sill(pen, t):
    shaft(pen, [(200, -300), (900, -300), (1500, 700), (500, 700)], MOON, 40, 3)


@view('cabin_now', 'fingertip', 'hands', 'sleeve', 'cuffs')
def _v_cab_insert(var, st, shot):
    vname = shot.get('view')
    around = {'fingertip': (1190, 640), 'hands': (1150, 760), 'sleeve': (1190, 700), 'cuffs': (1190, 760)}[vname]
    L = _insert_bg('ins_' + vname, var, st, around[0], around[1], 2.6)
    b = None
    if var in ('flash', 'doorway_glow'):
        kf = _flash_k(st, var)
        b = Beam(aim_fn((2400, -200), [(st.t0, 980, 560), (st.t1, 940, 600)], kf, 12, 91), spot=380, a=0.18)
        L.append(b.layer(1.6))
    c = {'red': '#ff9aa8', 'doorway_glow': '#fff6e4'}.get(var, CORE)
    L.append(_live(0.92, lambda pen, t: motes(pen, t, (-100, -100, 2000, 1200), 70, 93, b, c, 0.16), 'dust', blur=0))
    return _sp('cabin_now/' + vname, L, dict(hands=Anchor(960, 600, 1.0, 420), noah_floor=Anchor(820, 1240, 1.0, 900, 'seated, over the shoulder')),
               dof=6.75, beam=b, info=dict(insert=True))


@view('cabin_now', 'palm')
def _v_cab_palm(var, st, shot):
    L = _insert_bg('palm', var, st, 700, 1000, 2.2)
    def palm(pen, t):
        tr = 0.6 * noise1(t * 6, 3)
        info = None
        try:
            import characters as C
            info = C.draw_hands(pen, 'you', 960 + tr, 700, 560, C.Pose(ir_shape='open', il_shape='open'), t=t)
        except Exception:
            info = None
        if info and info.get('wrist') and info.get('tip'):
            w_ = info['wrist']; tp = info['tip']
            w_ = w_.get('r', list(w_.values())[0]) if isinstance(w_, dict) else w_
            tp = tp.get('r', list(tp.values())[0]) if isinstance(tp, dict) else tp
            px, py = lerp(w_[0], tp[0], 0.32), lerp(w_[1], tp[1], 0.32)
            ang = math.degrees(math.atan2(tp[1] - w_[1], tp[0] - w_[0])) + 90
        else:
            px, py, ang = 960, 760, 0.0
            hand = smooth([(700, 1300), (660, 700), (760, 420), (1160, 420), (1260, 700), (1220, 1300)], True, 0.7)
            _R(pen, hand, 900, 640, 600, ['#d8bcaa', '#c0a28e', '#9e8072']); pen.line(hand, 8)
        # the twist wrapper's imprint, pressed red into the palm
        pen.cv.save(); pen.cv.translate(px, py); pen.cv.rotate(ang - 18)
        _R(pen, None, 0, 0, 150, [(0, '#c8505a', 110), (0.6, '#c8505a', 60), (1, '#c8505a', 0)], sy=0.75, clip=False)
        pen.line(oval(0, 0, 70, 52), 5, '#a8323e', 170)
        for sg in (-1, 1):
            for j in range(4):
                pen.seg((sg * (78 + j * 24), -18 + j * 4), (sg * (84 + j * 24), 18 - j * 4), 3.5, '#b8424e', 150 - j * 25)
        pen.fill(oval(-18, -14, 24, 10), '#ffffff', 40)
        pen.cv.restore()
    L += [_live(1.0, palm, 'palm', blur=0), _live(0.9, lambda pen, t: motes(pen, t, (-100, -100, 2000, 1200), 50, 97, None, CORE, 0.15), 'dust', blur=0)]
    return _sp('cabin_now/palm', L, {}, dof=6.75, info=dict(insert=True))


@view('cabin_now', 'towel_fly')
def _v_cab_towel_fly(var, st, shot):
    L = _insert_bg('tfly', var, st, 1190, 665, 2.0)
    t0, t1 = st.t0, st.t1
    def towel(pen, t):
        u = prog(t, t0, t1)
        s = 0.6 + 2.6 * ease_in_cubic(u)
        x = lerp(1700, 900, u); y = lerp(300, 540, u)
        pts = []
        for i in range(16):
            a = 2 * math.pi * i / 16
            r = 1 + 0.25 * math.sin(a * 3 + t * 9) + 0.12 * math.sin(a * 5 - t * 13)
            pts.append((x + math.cos(a) * 520 * s * r, y + math.sin(a) * 330 * s * r))
        p = smooth(pts, True, 0.8)
        towel_cloth(pen, p, (x - 700 * s, y - 450 * s, x + 700 * s, y + 450 * s), 1.4 * s, 0, 15, 0.7)
        for j in range(5):
            pen.line(smooth([(x - 500 * s, y + (j - 2) * 120 * s), (x, y + (j - 2) * 110 * s + 40 * math.sin(t * 8 + j)), (x + 500 * s, y + (j - 2) * 120 * s)], False),
                     18 * s, '#000000', 50)
    L.append(_live(0.9, towel, 'towel', blur=0))
    return _sp('cabin_now/towel_fly', L, {}, dof=6.75, info=dict(insert=True))


@view('cabin_now', 'towel_over')
def _v_cab_towel_over(var, st, shot):
    M = (960, 540, 0.33)
    td = st.ev('towel_drop') or ((st.sfx('towel_drop') or [None])[0])
    def wall(pen, t):
        _zoom(lambda p, tt: (_window_out(p, tt), _cabin7_back(p, tt), _cabin7_bunks(p, tt, 0.4, False)), 1190, 665, 2.97)(pen, t)
    def behind(pen, t):     # after the drop: no mirror, a dark doorway shape with the first faint glow
        if td is None or t < td: return
        k = prog(t, td, td + 1.0)
        mirror_xf(pen, M)
        _L(pen, _pane_path(FW), 0, PANE[1], 0, PANE[3], ['#05070a', '#0a0e12'])
        _R(pen, None, 960, 600, 1400, [(0, '#f6f0e0', 60 * k), (1, '#f6f0e0', 0)], sy=1.6, clip=False)
        pen.cv.restore()
    def towel(pen, t, part='all'):
        drop = 0.0
        if td is not None and t >= td: drop = 2200 * (t - td) ** 2 * 1.8
        if part == 'body' and drop > 0: return
        if part == 'bumps' and drop > 0: part = 'all'
        mirror_xf(pen, M)
        pen.cv.translate(0, drop / M[2])
        x0, y0, x1, y1 = PANE[0] - FW - 520, PANE[1] - FW - 140, PANE[2] + FW + 520, PANE[3] + FW + 260
        pts = [(x0 + 40, y0 + 120), (960, y0), (x1 - 40, y0 + 120), (x1 + 30, y1), (960, y1 + 60), (x0 - 30, y1)]
        p = smooth(pts, True, 0.45)
        if part in ('all', 'body'):
            pen.shadow(p, 30, 40, 60, '#000000', 160)
            towel_cloth(pen, p, (x0 - 40, y0, x1 + 40, y1 + 60), 3.2, 0, 17, 0.55)
            for j in range(6):
                fx = x0 + 160 + j * (x1 - x0 - 320) / 5
                pen.line(smooth([(fx, y0 + 140), (fx + 30, (y0 + y1) / 2), (fx - 20, y1)], False), 26, '#000000', 50)
        if part == 'body':
            pen.cv.restore(); return
        tips = []
        pf = info.get('press')
        if callable(pf): tips = [(x, y, k) for (x, y, k) in pf(t)]
        else:
            hx, hy, hs = 960.0, 520.0, 380.0
            for c in shot.get('chars', []):
                if c.get('who') == 'queen' and isinstance(c.get('at'), list): hx, hy, hs = c['at'][:3]
            for c in st.sfx_cues('cloth_press'):
                k = ease_out_cubic(prog(t, c['t'] - 0.15, c['t'] + 0.35))
                if k > 0:
                    for j in range(5):
                        tips.append((hx + (j - 2) * hs * 0.14, hy - hs * 0.45 + abs(j - 2) * hs * 0.06 + (hs * 0.1 if j == 0 else 0), k))
        tips = [((x - M[0]) / M[2] + MPIV[0], (y - M[1]) / M[2] + MPIV[1], k) for (x, y, k) in tips]
        for (tx_, ty_, k) in tips:   # fingertips straining the terry toward the lens
            g = 70 * k / M[2]
            _R(pen, None, tx_, ty_, g * 1.6, [(0, '#ffffff', 70 * k), (0.5, '#ffffff', 30 * k), (1, '#000000', 0)], clip=False)
            _R(pen, None, tx_ + g * 0.4, ty_ + g * 0.6, g * 1.6, [(0, '#000000', 90 * k), (1, '#000000', 0)], clip=False)
            for i in range(4):
                pen.line(smooth([(tx_ - g * 1.6, ty_ - g * (1.2 - i * 0.8)), (tx_, ty_ - g * 0.3 * (i - 1.5)), (tx_ + g * 1.6, ty_ - g * (1.2 - i * 0.8))], False),
                         4 / M[2], '#000000', int(60 * k))
        pen.cv.restore()
    kf = _flash_k(st, var)
    b = Beam(aim_fn((2300, 900), [(st.t0, 960, 520), (st.t1, 1000, 560)], kf, 12, 101), spot=420, a=0.2)
    info = dict(mirror_xf=M, press=None)
    L = [_cl(1.15, wall, 'wall', 'tover:wall', NEAR), _live(1.08, behind, 'behind', blur=0),
         _cl(0.985, lambda pen, t: towel(pen, -1.0, 'body'), 'towel', 'tover:towel', NEAR,
             alpha=(lambda t: 1.0 if (td is None or t < td) else 0.0)),
         _live(0.984, lambda pen, t: towel(pen, t, 'bumps'), 'towel_live', blur=0), b.layer(0.98)]
    if td is not None:
        def burst(pen, t):
            if t < td + 0.45: return
            u = t - td - 0.45
            for j in range(40):
                ang = math.pi * (1.05 + 0.9 * _h(j, 3)); v = 200 + 400 * _h(j, 4)
                x = 960 + math.cos(ang) * v * u * 1.5 + (_h(j, 5) - 0.5) * 800
                y = 1120 + math.sin(ang) * v * u - 30 * u
                _R(pen, None, x, y, 30 + 60 * u, [(0, '#aab4be', 90 * max(0, 1 - u)), (1, '#aab4be', 0)], clip=False)
        L.append(_live(0.95, burst, 'dust_burst', blur=0))
    L.append(_motes_layer(0.9, (0, 0, 1920, 1080), 80, 103, b))
    return _sp('cabin_now/towel_over', L, dict(press=Anchor(960, 520, 1.0, 380)), beam=b, info=info)


@view('cabin_now', 'clock')
def _v_cab_clock(var, st, shot):
    def wall(pen, t): _zoom(lambda p, tt: _cabin7_back(p, tt), 560, 300, 8.2)(pen, t)
    L = [_cl(1.2, wall, 'wall', 'clock:wall', NEAR),
         _live(1.0, lambda pen, t: wall_clock(pen, 960, 540, 360, *_clock_sec(t, st)), 'clock', blur=0)]
    kf = _flash_k(st, var)
    b = Beam(aim_fn((-400, 1400), [(st.t0, 900, 520), (st.t1, 1000, 540)], kf, 8, 107), spot=520, a=0.15)
    L += [b.layer(0.97)] + _light_over(var, 'clock')
    if var == 'after':
        L.append(_cl(0.99, lambda pen, t: shaft(pen, [(-400, -300), (300, -300), (1600, 1400), (600, 1400)], MOON, 46, 3), 'moon', 'clock:moon', NEAR))
    L.append(_motes_layer(0.9, (0, 0, 1920, 1080), 60, 109, b, amb=0.12))
    return _sp('cabin_now/clock', L, {}, beam=b)


@view('cabin_now', 'dust_floor')
def _v_cab_dust_floor(var, st, shot):
    def floor(pen, t):
        pen.fill(rect(-900, -700, 3800, 2400), '#05080c')
        _L(pen, rect(-900, -700, 3800, 1000), 0, -700, 0, 300, ['#05080c', '#16222e'])
        fl = floor_persp(pen, -2600, 4500, 1500, 500, 1420, 300, 30, '#1a2834', '#3a4e60', 19)
        pen.texture(fl, 'grunge', 0.35, 'screen', 2.4)
        _L(pen, fl, 0, 300, 0, 1500, [(0, '#9aa8b6', 40), (1, '#9aa8b6', 18)])
        for x in (620, 1300): pen.shape(rect(x, 140, 26, 170), '#1a2430', 3)
        pen.fill(rect(560, 100, 820, 60), '#141c24'); pen.line(rect(560, 100, 820, 60), 3)
    kf = _flash_k(st, 'flash')
    b = Beam(aim_fn((-500, 900), [(st.t0, 900, 700), (st.t1, 1100, 650)], kf, 10, 111), w0=50, spread=0.18, spot=600, spot_sy=0.22, a=0.3)
    L = [_cl(1.0, floor, 'floor', 'dfloor:floor', NEAR), b.layer(0.99), _motes_layer(0.9, (0, 200, 1920, 1080), 120, 113, b, size=(1.2, 3.0))]
    return _sp('cabin_now/dust_floor', L, {}, beam=b)


def _bunk_under(pen, t, dy=0.0):
    pen.fill(rect(-900, -700, 3800, 2400), '#05080c')
    pen.cv.save(); pen.cv.translate(0, dy)
    under = poly([(-900, -700), (2820, -700), (2820, 300), (-900, 380)])
    _L(pen, under, 0, -700, 0, 380, ['#0e141a', '#2a3644'])
    for i in range(-4, 18):
        x = -900 + i * 220
        sl = poly([(x, -700), (x + 150, -700), (x + 150, 330 - i * 4), (x, 334 - i * 4)])
        _L(pen, sl, x, 0, x + 150, 0, ['#2a3644', '#3e4c5a', '#222c38']); pen.texture(sl, 'wood', 0.5, 'overlay', 1.0, 90); pen.line(sl, 4)
    rail = poly([(-900, 360), (2820, 290), (2820, 380), (-900, 470)])
    _L(pen, rail, 0, 300, 0, 470, ['#3a4854', '#1a242e']); pen.texture(rail, 'wood', 0.5, 'overlay', 1.2); pen.line(rail, 5)
    pen.shape(rect(1500, -700, 140, 2200), '#1e2a34', 5)
    pen.cv.restore()
    boards(pen, (-900, 470, 2820, 1100), '#1c2c3a', False, 180, 115, 0.5)
    fl = floor_persp(pen, -2000, 3900, 1600, -400, 2300, 1000, 22, '#16222c', '#2e4050', 117)


@view('cabin_now', 'bunk_hit', 'bunk_low')
def _v_cab_bunk(var, st, shot):
    th = (st.sfx('wood_thud') or [None])[0]
    if th is None and shot.get('view') == 'bunk_low': th = st.t0 - 0.85
    def bunk_l(pen, t):
        dy = 0.0
        if th is not None and t >= th:
            u = t - th; dy = -26 * math.exp(-u * 5) * math.cos(u * 26)
        _bunk_under(pen, t, dy)
    def dust(pen, t):
        if th is None: return
        u = t - th
        if u < 0: return
        for j in range(90):
            x = -200 + _h(j, 3) * 2300
            y = 340 + (60 + 200 * _h(j, 4)) * u + 40 * u * u + 30 * noise1(t * 0.5 + j, 5)
            a = 180 * max(0.0, 1 - u / 4.0) * (0.4 + 0.6 * _h(j, 6))
            if y < 1200: _R(pen, None, x + 20 * noise1(t + j, 7), y, 3 + 5 * _h(j, 8), [(0, '#ffb0b8' if var == 'red' else '#cfd8e0', a), (1, '#ffb0b8', 0)], clip=False)
        if u < 0.4:
            k = 1 - u / 0.4
            _R(pen, None, 960, 380, 900, [(0, '#c8b0b0', 120 * k), (1, '#c8b0b0', 0)], sy=0.35, clip=False)
    L = [_live(1.0, bunk_l, 'bunk', blur=0)] + _light_over(var, 'bunkh', 960, 300, 0.97) + [_live(0.95, dust, 'dust_burst', blur=0),
         _motes_layer(0.9, (0, 0, 1920, 1080), 60, 119, None, '#ff9aa8' if var == 'red' else CORE, 0.12, fall=20)]
    return _sp('cabin_now/' + shot.get('view', 'bunk_hit'), L, {})


@view('cabin_now', 'floor_low')
def _v_cab_floor_low(var, st, shot):
    tf = (st.sfx('body_fall') or [st.t0 + 0.4])[0]
    def floor(pen, t):
        pen.fill(rect(-900, -700, 3800, 2400), '#06090d')
        boards(pen, (-900, -300, 2820, 640), '#1e2e3c', False, 110, 121, 0.5)
        floor_persp(pen, -2400, 4300, 1600, -500, 2400, 640, 26, '#1a2834', '#3a4e60', 123)
    def burst(pen, t):
        u = t - tf
        if u < 0: return
        for j in range(60):
            ang = math.pi * (1.0 + _h(j, 3)); v = 300 + 600 * _h(j, 4)
            x = 960 + math.cos(ang) * v * u + 40 * noise1(t + j, 3); y = 1000 + math.sin(ang) * v * u * 0.5 + 60 * u * u
            _R(pen, None, x, y, 20 + 60 * u, [(0, '#d0a8b0', 100 * max(0, 1 - u / 1.4)), (1, '#d0a8b0', 0)], clip=False)
    L = [_cl(1.2, floor, 'floor', 'flow:floor', NEAR)] + _light_over(var, 'flow', 960, 500, 0.97) + [_live(0.95, burst, 'dust_burst', blur=0),
         _motes_layer(0.9, (0, 0, 1920, 1080), 60, 127, None, '#ff9aa8', 0.12)]
    return _sp('cabin_now/floor_low', L, dict(you_floor=Anchor(960, 1000, 1.0, 640)))


# ====================================================================== the other cabin at dawn (theirs: 06:59, too normal)
PT = dict(wall='#cdccc7', wall2='#bebeba', seam='#8f9394', floor0='#a6a7a5', floor1='#c8c6c0', wood='#a19f98', post='#b0aea6',
          mat='#8a96a0', tick='#76828c', blanket='#7a8e9a', pillow='#ecebe6', sky0='#e2e8e8', sky1='#d2dada', lawn='#a9b49c',
          lawn2='#909c86', pine='#8a9690', pine2='#a2aca6', curtain='#c9a84a', trim='#e7e5e0', shadow='#7f8b94', lantern='#ffd9a0')
PM = dict(PT, wall='#d8c8aa', wall2='#c8b696', seam='#9a8466', floor0='#bfa888', floor1='#e0ccaa', wood='#b89a74', post='#c8aa84',
          mat='#a8988a', tick='#8a7a6c', blanket='#a8786a', pillow='#f6ecd8', sky0='#e4d8be', sky1='#d6caa8', lawn='#b8c08a',
          lawn2='#9aa874', pine='#8a9a7a', pine2='#a8b494', curtain='#d8b04a', trim='#dccfb2', shadow='#8a7a6a')


def _dawn_outside(pen, t, P=PT, x0=380, y0=230, x1=860, y1=590, far=True):
    """Morning outside the dawn cabin window: pale sky, lawn, misty pines, the mess hall far away."""
    _L(pen, rect(x0, y0, x1 - x0, y1 - y0), 0, y0, 0, y1, [P['sky0'], P['sky1'], _lt(P['lawn'], 0.2)])
    _R(pen, None, (x0 + x1) / 2 + 80, y0 + 60, 360, [(0, '#ffffff', 80), (1, '#ffffff', 0)], clip=False)
    treeline(pen, x0 - 100, x1 + 100, y0 + (y1 - y0) * 0.62, (y1 - y0) * 0.5, 7, 41, P['pine2'])
    pen.fill(rect(x0, y0 + (y1 - y0) * 0.62, x1 - x0, (y1 - y0) * 0.4), P['lawn'])
    _R(pen, None, (x0 + x1) / 2, y0 + (y1 - y0) * 0.6, (x1 - x0) * 0.7, [(0, '#ffffff', 90), (1, '#ffffff', 0)], sy=0.25, clip=False)


def _dawn_room(pen, t, P=PT, curtains=True, lantern_k=1.0, towel=True, shoe=True, swim=True, clock=False, made=True):
    """The other cabin from the doorway (static parts): back wall, window back-left (x 420-820, y 260-560) with gingham
    curtains, sill + lantern (700, 556), Noah's bunk x 900-1700 (mattress y 690-780, top rail y 400), floor, towel on the
    floor (620, 900), the other shoe (1000, 940). Clean, still, evenly lit."""
    pen.fill(rect(-900, -700, 3800, 2400), _dk(P['wall'], 0.15))
    ceil = poly([(-900, -700), (2820, -700), (2000, 150), (-200, 150)])
    _L(pen, ceil, 0, -700, 0, 150, [_dk(P['wall'], 0.3), _dk(P['wall'], 0.12)])
    for i in range(9):
        u = i / 8; pen.line(poly([(lerp(-900, 2820, u), -700), (lerp(-200, 2000, u), 150)], False), 22, _dk(P['wall'], 0.35))
    boards(pen, (-200, 150, 2000, 860), P['wall'], False, 66, 131, 0.3, seam=P['seam'], seam_a=150, var=0.05, nails=False, hi=P['trim'])
    for (pts, a) in (([(-900, -700), (-200, 150), (-200, 860), (-900, 1600)], 0), ([(2000, 150), (2820, -700), (2820, 1600), (2000, 860)], 1)):
        p = poly(pts)
        _L(pen, p, pts[0][0], 0, pts[1][0], 0, [_dk(P['wall2'], 0.12), P['wall2']] if a == 0 else [P['wall2'], _dk(P['wall2'], 0.15)])
        pen.texture(p, 'wood', 0.25, 'overlay', 1.2, 90)
    pen.fill(rect(-200, 840, 2200, 22), _dk(P['wall'], 0.25))
    fl = floor_persp(pen, -1500, 3400, 1600, -200, 2000, 860, 26, P['floor0'], P['floor1'], 133, seam=P['shadow'])
    _R(pen, None, 620, 1000, 700, [(0, '#ffffff', 60), (1, '#ffffff', 0)], sy=0.35, clip=False)
    # window
    hole = rect(420, 260, 400, 300)
    _dawn_outside(pen, t, P, 420, 260, 820, 560)
    pen.line(rect(410, 250, 420, 320), 22, P['trim']); pen.line(rect(398, 238, 444, 344), 4)
    pen.seg((620, 260), (620, 560), 10, P['trim']); pen.seg((420, 410), (820, 410), 10, P['trim'])
    sill = rect(388, 556, 464, 26)
    _L(pen, sill, 0, 556, 0, 582, [P['trim'], _dk(P['trim'], 0.15)]); pen.line(sill, 3)
    if curtains:
        for (cx0, cx1) in ((340, 470), (770, 900)):
            cp = smooth([(cx0, 232), (cx1, 232), (cx1 - 6, 600), (cx0 + 8, 610)], True, 0.25)
            gingham(pen, cp, (cx0, 232, cx1, 610), P['curtain'], 0.9)
        val = rect(330, 214, 580, 50)
        gingham(pen, val, (330, 214, 910, 264), P['curtain'], 0.9)
        pen.seg((320, 214), (920, 214), 6, _dk(P['trim'], 0.4))
    # Noah's bunk (made), the left bunk edge
    bunk(pen, -520, 120, 900, 1.0, P['wood'], P['mat'], P['tick'], True, made, P['blanket'], 0.6, (690, 780), (400, 440), posts_c=P['post'], pillow=P['pillow'])
    bunk(pen, 900, 1700, 900, 1.0, P['wood'], P['mat'], P['tick'], True, made, P['blanket'], 0.6, (690, 780), (400, 440), posts_c=P['post'], pillow=P['pillow'])
    if swim: swimsuits(pen, 980, 1620, 440, 0.0, 0.72, 0.0, 6, False)
    if towel:
        tw = smooth([(470, 930), (520, 870), (640, 862), (760, 880), (790, 930), (700, 950), (560, 952)], True, 0.7)
        pen.shadow(tw, 6, 8, 10, '#000000', 60)
        towel_cloth(pen, tw, (470, 862, 790, 952), 0.6, 0.6, 21, 1.0)
        pen.fill(oval(640, 940, 160, 16), _dk(P['floor0'], 0.25), 110)
    if shoe: sneaker(pen, 1000, 940, 0.8)
    if clock:
        wall_clock(pen, 1550, 230, 46, 6 * 3600 + 59 * 60 + 40, 0.0, '#f2efe6', '#8a8e92')


def sneaker(pen, x, y, s=1.0, rot=0.0, c='#efefec', lace='#f8f8f8', loose=True):
    """Noah's white sneaker on its side (the one he left by the bed), lace loose."""
    pen.cv.save(); pen.cv.translate(x, y); pen.cv.rotate(rot); pen.cv.scale(s, s)
    sole = smooth([(-120, 10), (130, 10), (140, -4), (120, -18), (-110, -18), (-130, -6)], True, 0.6)
    up = smooth([(-110, -16), (-100, -70), (-40, -86), (20, -70), (70, -52), (120, -30), (124, -16)], True, 0.7)
    pen.shadow(sole, 6, 10, 12, '#000000', 90)
    pen.fill(up, c); _L(pen, up, 0, -86, 0, -16, [(0, '#ffffff', 80), (1, '#000000', 40)]); pen.line(up, 4)
    pen.fill(sole, '#d8d4c8'); pen.line(sole, 4)
    pen.fill(smooth([(-60, -76), (10, -64), (6, -40), (-50, -46)], True, 0.5), '#2a2e36')
    for j in range(4): pen.seg((-40 + j * 16, -70 + j * 4), (-20 + j * 16, -58 + j * 4), 4, lace)
    if loose:
        pen.line(smooth([(-10, -60), (40, -30), (20, 0), (70, 14)], False), 4, lace); pen.line(smooth([(-20, -62), (-70, -20), (-40, 12)], False), 4, lace)
    pen.cv.restore()


def _queen_cool(key, cx, cy, r=400, k=1.0):
    """dawn_queen: the light cools and drains near her (400 px radial)."""
    return _cl(0.99, lambda pen, t: _R(pen, None, cx, cy, r * 1.6, [(0, '#5a6878', 120 * k), (0.5, '#7a8898', 60 * k), (1, '#7a8898', 0)], clip=False),
               'queen_cool', key, NEAR)


def _drop_draw(pen, t, st, x=620, y_hang=700, y_towel=900, y_frame=580):
    """The towel drop: drips falling from the window frame onto the towel (deterministic loop), or rising off the towel and
    hanging at (620, 700), glinting and turning, then falling again."""
    v = st.v('drop', t)
    rise = st.ev('drop_rise')
    if rise and t < rise[1]:
        if t < rise[0]: v = 'none'
        else:
            u = ease_out_cubic(prog(t, rise[0], rise[1]))
            yy = lerp(y_towel - 20, y_hang, u)
            pen.fill(_drop_path(x, yy, 9, 1.2 + 0.5 * (1 - u)), '#e8f0f4', 230); pen.fill(oval(x - 3, yy - 3, 2.5), '#ffffff', 240)
            return
    if v == 'hanging':
        wob = 2 * math.sin(t * 3.1)
        _R(pen, None, x, y_hang, 60, [(0, '#ffffff', 80), (1, '#ffffff', 0)], clip=False)
        d = _drop_path(x, y_hang + wob, 10, 1.15)
        pen.fill(d, '#dfe8ee', 235); _R(pen, d, x - 3, y_hang - 4 + wob, 12, [(0, '#ffffff'), (1, '#9aaab4')])
        pen.fill(oval(x - 3.5, y_hang - 5 + wob, 2.6), '#ffffff', 255); pen.line(d, 1.6, '#6a7a86', 200)
        return
    tf = st.ev('drop_fall')
    if v == 'falling' or (tf and t >= tf):
        t_ = t if not (tf and t >= tf) else (t - tf + 0.6 * 1.1)
        drops_fall(pen, t_, x, y_frame, y_towel - 14, 1.1, 0, '#e2eaee', 6.0)


@view('cabin_dawn', 'wide', 'queen_bunk', 'noah_ms')
def _v_dawn_wide(var, st, shot):
    vname = shot.get('view', 'wide')
    key = 'dawn'
    L = [_cl(1.15, lambda pen, t: _dawn_room(pen, t, PT, shoe=False, towel=True), 'room', key + ':room', NEAR)]
    def lantern_l(pen, t):
        k = 1.0
        if var == 'dawn_break': k = 0.55 + 0.45 * (1 if _h(int(t * 15), 3) > 0.25 else 0.2)
        lantern(pen, 700, 556, 0.62, k, PT['lantern'], '#6a7a6a')
    L.append(_live(1.14, lantern_l, 'lantern', blur=0))
    L.append(_cl(1.12, lambda pen, t: shaft(pen, [(430, 270), (810, 270), (1180, 1250), (380, 1250)], '#ffffff', 54, 4), 'window_shaft', key + ':shaft', NEAR))
    L.append(_live(1.11, lambda pen, t: motes(pen, t, (380, 260, 1200, 1200), 40, 141,
                                              Beam(lambda tt: (620, 270, 780, 1250, 1.0), w0=380, spread=0.12, spot=0), '#ffffff', 0.0,
                                              speed=(2.0, 5.0)), 'shaft_dust', blur=0))
    L.append(_live(1.13, lambda pen, t: wall_clock(pen, 1550, 230, 46, *_clock_sec(t, st, 'theirs'), face='#f2efe6', rim='#8a8e92'), 'clock', blur=0))
    L.append(_live(1.1, lambda pen, t: _drop_draw(pen, t, st), 'drop', blur=0))
    # the dip beside Noah and the other shoe
    dip_t = st.sfx('mattress_creak') or ([st.t0 + 0.4] if (st.ev('mattress') or vname == 'queen_bunk') else [])
    def dip(pen, t):
        if not dip_t and st.v('queen', t) != 'bunk': return
        k = ease_out_cubic(prog(t, dip_t[0], dip_t[0] + 1.2)) if dip_t else 1.0
        pen.fill(oval(1420, 712, 150, 14 * k), '#000000', int(70 * k))
        _L(pen, rect(1280, 690, 280, 40), 0, 690, 0, 730, [(0, '#3a4650', 90 * k), (1, '#3a4650', 0)])
    L.append(_live(1.0, dip, 'dip', blur=0))
    L.append(_live(1.0, lambda pen, t: sneaker(pen, 1000, 940, 0.8), 'shoe', blur=0))
    if var == 'dawn_queen': L.append(_queen_cool(key + ':qc', 1440, 760))
    an = dict(noah_bunk=Anchor(1180, 930, 1.0, 560, 'seated'), queen_bunk=Anchor(1440, 930, 1.0, 600, 'seated'),
              you_bunk=Anchor(760, 1010, 1.0, 640), you_stand=Anchor(760, 1010, 1.0, 640), dip=Anchor(1420, 720, 1.0, 1),
              towel=Anchor(620, 900, 1.0, 1), shoe=Anchor(1000, 940, 1.0, 1))
    return _sp('cabin_dawn/' + vname, L, an)


def _dawn_bg(key, var, st, cx, cy, m, depth=3.0, P=PT, queen_at=None):
    """Blurred dawn cabin behind a close-up (zoom of the wide about (cx, cy))."""
    L = [_cl(depth, _zoom(lambda pen, t: (_dawn_room(pen, t, P, shoe=True), lantern(pen, 700, 556, 0.62, 1.0, P['lantern'], '#6a7a6a',
                                                                                          True)), cx, cy, m), 'room_bg', key + ':bg', NEAR)]
    L.append(_cl(depth * 0.95, _zoom(lambda pen, t: shaft(pen, [(430, 270), (810, 270), (1180, 1250), (380, 1250)], '#ffffff', 54, 4), cx, cy, m),
                 'shaft', key + ':sh', NEAR))
    if var == 'dawn_queen': L.append(_queen_cool(key + ':qc', *(queen_at or (960, 560)), 520, 1.0))
    if var == 'dawn_break':
        L.append(_live(depth * 0.9, lambda pen, t: _R(pen, None, 700 + (700 - cx) * (m - 1), 540, 900,
                                                               [(0, '#ffd9a0', 60 * (1 if _h(int(t * 15), 3) > 0.25 else 0.1)), (1, '#ffd9a0', 0)], clip=False),
                       'lantern_stutter'))
    L.append(_live(0.92, lambda pen, t: motes(pen, t, (-100, -100, 2000, 1200), 30, 143, None, '#ffffff', 0.12, speed=(2, 6)), 'dust', blur=0))
    return L


@view('cabin_dawn', 'noah_cu', 'candy', 'hands_jerk', 'you_face', 'queen_bust', 'queen_face', 'queen_mouth', 'knot_cu')
def _v_dawn_cu(var, st, shot):
    vname = shot.get('view')
    around = {'noah_cu': (1180, 560, 2.6), 'candy': (1100, 700, 2.8), 'hands_jerk': (900, 760, 2.8), 'you_face': (700, 450, 2.4),
              'queen_bust': (1440, 560, 2.6), 'queen_face': (1440, 520, 3.0), 'queen_mouth': (1440, 540, 3.4), 'knot_cu': (1000, 900, 3.0)}[vname]
    L = _dawn_bg('dcu_' + vname, var, st, *around, queen_at=(960, 560) if vname.startswith('queen') else (1500, 600))
    if vname == 'knot_cu':   # sharp floor + bunk edge close under the hands
        def edge(pen, t):
            floor_persp(pen, -1800, 3700, 1500, -300, 2200, 640, 22, PT['floor0'], PT['floor1'], 147, seam=PT['shadow'])
            r = rect(-600, 300, 3100, 140); pen.fill(r, PT['blanket']); pen.texture(r, 'fabric', 0.5, 'overlay', 1.4); pen.line(r, 5)
            pen.fill(rect(-600, 440, 3100, 50), _dk(PT['wood'], 0.1)); pen.line(rect(-600, 440, 3100, 50), 5)
            _R(pen, None, 600, 700, 1100, [(0, '#ffffff', 80), (1, '#ffffff', 0)], sy=0.5, clip=False)
        L = [_cl(1.3, edge, 'floor', 'knot:edge', NEAR)] + L[-1:]
    return _sp('cabin_dawn/' + vname, L, {}, dof=6.75, info=dict(insert=True))


@view('cabin_dawn', 'towel')
def _v_dawn_towel(var, st, shot):
    def floor(pen, t):
        boards(pen, (-700, -500, 2620, 420), PT['wall'], False, 150, 151, 0.3, seam=PT['seam'], seam_a=140, nails=False, hi=PT['trim'])
        floor_persp(pen, -2200, 4100, 1600, -500, 2400, 420, 22, PT['floor0'], PT['floor1'], 153, seam=PT['shadow'])
        _L(pen, rect(-700, -500, 3300, 120), 0, -500, 0, -380, [PT['trim'], _dk(PT['trim'], 0.2)])
        per = [(260 + i * 180, 600 - 30 * math.sin(i)) for i in range(9)] + [(1700, 760), (1740, 900)] + \
              [(1700 - i * 180, 980 + 25 * math.sin(i * 1.7)) for i in range(9)] + [(240, 820)]
        tw = smooth([(x + 26 * (_h(i, 29) - 0.5), y + 30 * (_h(i, 31) - 0.5)) for i, (x, y) in enumerate(per)], True, 0.6)
        pen.shadow(tw, 14, 20, 26, '#000000', 70)
        towel_cloth(pen, tw, (230, 560, 1720, 1000), 2.4, 0.7, 23, 1.0)
        for (fx, w_) in ((560, 90), (980, 140), (1380, 100)):     # soft fold shadows and highlights
            _L(pen, rect(fx - w_, 560, 2 * w_, 450), fx - w_, 0, fx + w_, 0, [(0, '#000000', 0), (0.55, '#000000', 70), (0.75, '#ffffff', 40), (1, '#ffffff', 0)])
        corner = poly([(1660, 760), (1720, 900), (1560, 860)]); pen.fill(corner, '#e0a060'); pen.line(corner, 4)
        pen.fill(oval(980, 1000, 760, 40), '#5a6670', 50)
        pen.fill(oval(960, 990, 700, 50), _dk(PT['floor0'], 0.3), 100)
        _R(pen, None, 960, 760, 1200, [(0, '#ffffff', 70), (1, '#ffffff', 0)], sy=0.5, clip=False)
    def drop(pen, t):
        _drop_draw(pen, t, st, 960, 330, 720, -420)
    L = [_cl(1.2, floor, 'towel', 'dtowel:floor', NEAR), _live(1.0, drop, 'drop', blur=0),
         _live(0.95, lambda pen, t: motes(pen, t, (0, -100, 1920, 1100), 25, 157, None, '#ffffff', 0.12, speed=(1.5, 4)), 'dust', blur=0)]
    return _sp('cabin_dawn/towel', L, dict(drop=Anchor(960, 330, 1.0, 1)))


@view('cabin_dawn', 'shoe', 'mattress_dip')
def _v_dawn_shoe(var, st, shot):
    vname = shot.get('view')
    def floor(pen, t):
        pen.fill(rect(-900, -700, 3800, 2400), PT['wall'])
        r = rect(-900, -200, 3800, 420); pen.fill(r, PT['blanket']); pen.texture(r, 'fabric', 0.6, 'overlay', 1.8)
        for j in range(5): pen.line(smooth([(-900, 0 + j * 60), (960, 40 + j * 60), (2820, -10 + j * 60)], False), 10, '#000000', 40)
        pen.fill(rect(-900, 220, 3800, 80), _dk(PT['wood'], 0.1)); pen.line(rect(-900, 220, 3800, 80), 6)
        floor_persp(pen, -2400, 4300, 1600, -800, 2700, 300, 22, PT['floor0'], PT['floor1'], 161, seam=PT['shadow'])
        _R(pen, None, 700, 700, 1300, [(0, '#ffffff', 70), (1, '#ffffff', 0)], sy=0.5, clip=False)
    L = []
    if vname == 'shoe':
        L = [_cl(1.2, floor, 'floor', 'dshoe:floor', NEAR), _live(1.0, lambda pen, t: sneaker(pen, 1060, 780, 2.6, -4), 'shoe', blur=0)]
        if var == 'dawn_queen': L.append(_queen_cool('dshoe:qc', 1500, 300, 600))
    else:
        dip_t = (st.sfx('mattress_creak') or [st.t0 + 0.3])[0]
        def mat(pen, t):
            k = ease_out_cubic(prog(t, dip_t, dip_t + 1.4))
            pen.fill(rect(-900, -700, 3800, 2400), PT['wall'])
            pts = [(-900, 300)] + [(x, 300 + 110 * k * math.exp(-((x - 1100) / 420.0) ** 2)) for x in range(-900, 2900, 100)] + [(2820, 1400), (-900, 1400)]
            m = smooth(pts, True, 0.3)
            pen.fill(m, PT['blanket']); pen.texture(m, 'fabric', 0.6, 'overlay', 1.8)
            for j in range(8):
                y0 = 380 + j * 110
                pen.line(smooth([(-900, y0), (600, y0 + 30 * k), (1100, y0 + 90 * k * math.exp(-j * 0.2)), (1600, y0 + 30 * k), (2820, y0)], False), 8, '#000000', int(30 + 50 * k))
            _R(pen, None, 1100, 360 + 60 * k, 600, [(0, '#000000', 90 * k), (1, '#000000', 0)], sy=0.4, clip=False)
            sat = ease_in_out(prog(t, dip_t + 0.4, dip_t + 2.0))
            if sat > 0:      # black satin spreading over the blanket
                sp_ = smooth([(1100 - 700 * sat, 380), (1100, 300 + 60 * k), (1100 + 600 * sat, 400), (1100 + 500 * sat, 560 + 200 * sat), (1100, 600 + 260 * sat),
                              (1100 - 620 * sat, 540 + 180 * sat)], True, 0.7)
                pen.fill(sp_, '#0b0d14'); _L(pen, sp_, 1100 - 700 * sat, 0, 1100 + 600 * sat, 0, [(0, '#3a3e4a', 0), (0.45, '#5a5e6e', 120), (0.55, '#c63449', 60), (1, '#3a3e4a', 0)])
            sneaker(pen, 400, 260, 1.6, 6)
        L = [_live(1.0, mat, 'mattress', blur=0), _queen_cool('ddip:qc', 1100, 400, 600, 1.0 if var == 'dawn_queen' else 0.4)]
    L.append(_live(0.95, lambda pen, t: motes(pen, t, (0, 0, 1920, 1080), 20, 163, None, '#ffffff', 0.12, speed=(1.5, 4)), 'dust', blur=0))
    return _sp('cabin_dawn/' + vname, L, {})


@view('cabin_dawn', 'clock')
def _v_dawn_clock(var, st, shot):
    def wall(pen, t):
        boards(pen, (-700, -500, 2620, 1600), PT['wall'], False, 300, 171, 0.3, seam=PT['seam'], seam_a=150, nails=False, hi=PT['trim'], lw=5)
        _R(pen, None, 600, 200, 1600, [(0, '#ffffff', 90), (1, '#ffffff', 0)], clip=False)
    snap = st.ev('clock_dawn')
    def clk(pen, t):
        s, j = _clock_sec(t, st, 'theirs')
        if isinstance(snap, list) and snap:
            ts = snap[-1]
            s = 6 * 3600 + (3590 + (t - (ts - 9.0 + 0.0)) if t < ts else 3580 + (t - ts))
            if t >= ts: j = -8 * math.exp(-(t - ts) * 18) * math.cos((t - ts) * 50)
        wall_clock(pen, 960, 540, 380, s, j, '#f2efe6', '#8a8e92')
    L = [_cl(1.2, wall, 'wall', 'dclock:wall', NEAR), _live(1.0, clk, 'clock', blur=0),
         _live(0.95, lambda pen, t: motes(pen, t, (0, 0, 1920, 1080), 20, 173, None, '#ffffff', 0.12, speed=(1.5, 4)), 'dust', blur=0)]
    return _sp('cabin_dawn/clock', L, {})


@view('cabin_dawn', 'window')
def _v_dawn_window(var, st, shot):
    def win(pen, t):
        _zoom(lambda p, tt: _dawn_room(p, tt, PT, shoe=False, towel=False), 620, 410, 2.3)(pen, t)
    L = [_cl(1.0, win, 'window', 'dwin:win', NEAR),
         _live(0.99, lambda pen, t: lantern(pen, 960 + (700 - 620) * 2.3, 540 + (556 - 410) * 2.3, 1.45, 1.0, PT['lantern'], '#6a7a6a'), 'lantern', blur=0),
         _cl(0.98, _zoom(lambda pen, t: shaft(pen, [(430, 270), (810, 270), (1180, 1250), (380, 1250)], '#ffffff', 60, 4), 620, 410, 2.3), 'shaft', 'dwin:sh', NEAR),
         _live(0.96, lambda pen, t: motes(pen, t, (200, 0, 1700, 1100), 30, 175,
                                          Beam(lambda tt: (960, 0, 1400, 1100, 1.0), w0=800, spread=0.1, spot=0), '#ffffff', 0.0, speed=(1.5, 3.5)), 'shaft_dust', blur=0)]
    return _sp('cabin_dawn/window', L, {})


@view('cabin_dawn', 'window_out')
def _v_dawn_window_out(var, st, shot):
    cues = st.sfx_cues('sprinkler_spit')
    on = next((c['t'] for c in cues if not (c.get('params') or {}).get('loop_id') and (c.get('params') or {}).get('kind') != 'die'), None)
    spits = [c['t'] for c in cues if (c.get('params') or {}).get('loop_id')]
    die = next((c['t'] for c in cues if (c.get('params') or {}).get('kind') == 'die'), None)
    if spits and on is None: on = spits[0] - 0.4
    if spits and die is None: die = spits[-1] + 0.72
    fake = st.change_t('bell', 'fake_ringing') or (st.ev('fake_bell')[0] if isinstance(st.ev('fake_bell'), list) else None)
    def outside(pen, t):
        _L(pen, rect(-900, -700, 3800, 1400), 0, -700, 0, 640, [PT['sky0'], '#e2e8e8', PT['sky1']])
        _R(pen, None, 700, 100, 1300, [(0, '#ffffff', 90), (1, '#ffffff', 0)], clip=False)
        treeline(pen, -900, 2900, 640, 300, 22, 181, PT['pine2'])
        mist(pen, 0, 600, -900, 2900, 140, 8, 3, 60, '#f4f6f6', 0)
        pen.fill(rect(-900, 640, 3800, 900), PT['lawn'])
        _L(pen, rect(-900, 640, 3800, 900), 0, 640, 0, 1400, [(0, '#ffffff', 60), (1, PT['lawn2'], 255)])
        p = poly([(1180, 700), (1300, 700), (1700, 1400), (900, 1400)])
        pen.fill(p, '#c4bca8'); pen.texture(p, 'asphalt', 0.3, 'overlay')
        # the mess hall far away with its bell on the porch
        pen.cv.save(); pen.cv.translate(1450, 600); pen.cv.scale(0.16, 0.16); pen.cv.translate(-960, -600)
        _lodge(pen, day=True, sign=True)
        pen.cv.restore()
        grass(pen, -900, 2900, 1080, 40, 200, 183, PT['lawn2'], '#ffffff')
    def bell_far(pen, t):
        sw = 0.0
        if fake is not None and t >= fake - 0.2:
            u = t - fake; sw = 28 * math.sin(u * 5.2) * min(1.0, (u + 0.2) * 3)
        pen.cv.save(); pen.cv.translate(1450 + (1420 - 960) * 0.16, 600 + (420 - 600) * 0.16)
        bell(pen, 0, 0, 0.11, sw, 0.9, False, rope=False, bracket=True, t=t)
        pen.cv.restore()
    def spr(pen, t):
        sprinkler(pen, 900, 760, t, spits, on, die, 0.9)
    def frame(pen, t):
        pen.fill(minus(rect(-900, -700, 3800, 2400), rect(160, 80, 1600, 920)), PT['trim'])
        pen.line(rect(160, 80, 1600, 920), 10, _dk(PT['trim'], 0.3)); pen.line(rect(140, 60, 1640, 960), 4)
        pen.seg((960, 80), (960, 1000), 26, PT['trim']); pen.line(rect(947, 80, 26, 920), 3)
        for (cx0, cx1) in ((-200, 260), (1660, 2120)):
            cp = smooth([(cx0, 40), (cx1, 40), (cx1 - 10, 1160), (cx0 + 10, 1170)], True, 0.25)
            gingham(pen, cp, (cx0, 40, cx1, 1170), PT['curtain'], 2.0)
    L = [_cl(4.0, outside, 'outside', 'wout:out', (-900, -700, 2820, 1500)), _live(3.6, bell_far, 'fake_bell', blur=0),
         _live(3.0, spr, 'sprinkler', blur=0), _cl(1.0, frame, 'window_frame', 'wout:frame', NEAR)]
    return _sp('cabin_dawn/window_out', L, dict(sprinkler=Anchor(900, 760, 3.0, 1), bell_far=Anchor(1420, 600, 3.6, 1)))


@view('cabin_dawn', 'doorway_back')
def _v_dawn_doorway_back(var, st, shot):
    """Looking back at the doorway (x 840-1080, y 220-900) from the dawn side: a dark navy rectangle with Tess in it,
    her beam into the dawn cabin, perfectly steady (no hand wobble: she is frozen), dust drifting in it."""
    def wall(pen, t):
        boards(pen, (-900, -500, 2820, 900), PT['wall'], False, 74, 191, 0.3, seam=PT['seam'], seam_a=150, nails=False, hi=PT['trim'])
        floor_persp(pen, -2000, 3900, 1600, -900, 2820, 900, 26, PT['floor0'], PT['floor1'], 193, seam=PT['shadow'])
        _R(pen, None, 300, 300, 1400, [(0, '#ffffff', 80), (1, '#ffffff', 0)], clip=False)
        pc = skia.Paint(AntiAlias=True); pc.setBlendMode(skia.BlendMode.kClear)
        hole = poly([(840, 220), (1080, 226), (1076, 900), (844, 900)])
        pen.cv.drawPath(hole, pc)
        for i in range(12):
            yy = lerp(220, 900, i / 11)
            pen.seg((840 - 10 * _h(i, 3), yy), (846, yy + 30), 4, '#6a5a44'); pen.seg((1080 + 10 * _h(i, 4), yy), (1074, yy + 30), 4, '#6a5a44')
        pen.line(hole, 4, '#3a2e22')
        bunk(pen, 1500, 2500, 980, 1.1, PT['wood'], PT['mat'], PT['tick'], True, True, PT['blanket'], 0.6, (740, 840), (430, 470), posts_c=PT['post'])
    def dark(pen, t):
        _L(pen, rect(700, 150, 520, 800), 0, 150, 0, 950, ['#0a1622', '#14263a', '#0c1824'])
        _zoom(lambda p, tt: _cabin7_back(p, tt), 1190, 665, 1.2, 960, 560)(pen, t)
        pen.fill(rect(-900, -700, 3800, 2400), '#05090e', 120)
    frozen = st.v('drop', st.t0) == 'hanging' or 'perfectly steady' in shot.get('frame', '') or 'frozen' in shot.get('frame', '')
    kf = _flash_k(st, 'flash') if var != 'dawn_break' else (lambda t: 1.0)
    b = Beam(aim_fn((930, 600), [(st.t0, 640, 1060)], kf, 0.0 if frozen else 6.0, 197), w0=26, spread=0.22, spot=220, spot_sy=0.35, a=0.3)
    L = [_cl(2.5, dark, 'our_side', 'dback:dark', (600, 100, 1320, 1000)), _cl(1.0, wall, 'wall', 'dback:wall', NEAR), b.layer(0.98),
         _live(0.95, lambda pen, t: motes(pen, t, (300, 450, 1100, 1150), 90, 199, b, '#fff2d6', 0.03), 'dust', blur=0)]
    if var == 'dawn_break': L.append(_live(0.97, lambda pen, t: _R(pen, None, 960, 560, 700, [(0, GLOW, 50), (1, GLOW, 0)], sy=1.2, clip=False), 'red_leak'))
    an = dict(tess_in_doorway=Anchor(960, 900, 1.05, 640), doorway=Anchor(960, 560, 1.0, 1))
    return _sp('cabin_dawn/doorway_back', L, an, beam=b)


# ---------------------------------------------------------------------- cabin_now: the doorway, the ending, the phone
def _doorway_glimpse(pen, t, red=0.0):
    """The pale dawn cabin seen through the doorway (drawn big; the doorway hole frames it)."""
    _zoom(lambda p, tt: (_dawn_room(p, tt, PT, shoe=False), lantern(p, 700, 556, 0.62, 1.0, PT['lantern'], '#6a7a6a')), 980, 560, 0.9, 960, 600)(pen, t)
    _R(pen, None, 960, 560, 700, [(0, '#ffffff', 120), (1, '#ffffff', 0)], clip=False)


@view('cabin_now', 'doorway')
def _v_cab_doorway(var, st, shot):
    m = 1.5
    def back(pen, t):
        _zoom(lambda p, tt: (_window_out(p, tt), _cabin7_back(p, tt), _moon_shafts(p, tt), _cabin7_bunks(p, tt, 0.4, False)), 1190, 665, m, 960, 600)(pen, t)
        pc = skia.Paint(AntiAlias=True); pc.setBlendMode(skia.BlendMode.kClear)
        hole = poly([(860, 306), (1062, 312), (1058, 894), (864, 892)])
        pen.cv.drawPath(hole, pc)
        for i in range(16):      # the raw splintered edge
            yy = lerp(306, 892, i / 15)
            for (sx, d) in ((860, -1), (1061, 1)):
                ln = 10 + 22 * _h(i + sx, 3)
                pen.fill(poly([(sx, yy), (sx + d * ln, yy + 10 + 14 * _h(i, 4)), (sx, yy + 26)]), '#7a6248')
                pen.seg((sx, yy), (sx + d * ln, yy + 10), 2, '#2a2018')
        pen.line(hole, 5, '#2a2018')
        tw = smooth([(820, 940), (900, 880), (1060, 870), (1180, 900), (1200, 950), (1080, 975), (900, 972)], True, 0.7)
        pen.shadow(tw, 8, 12, 14, '#000000', 140)
        towel_cloth(pen, tw, (820, 870, 1200, 975), 0.7, 0, 25, 0.6)
    def spill(pen, t):
        k = 0.92 + 0.08 * noise1(t * 0.7, 3)
        _R(pen, None, 960, 600, 1000, [(0, '#fff6e4', 110 * k), (0.3, '#f3e3c4', 50 * k), (1, '#f3e3c4', 0)], sy=0.8, clip=False)
        shaft(pen, [(864, 892), (1058, 894), (1700, 1500), (200, 1500)], '#fff2dc', int(80 * k), 5)
        for j in range(9):
            a0 = math.radians(-60 + j * 15 + 3 * math.sin(t * 0.4 + j))
            ex, ey = 960 + 1900 * math.sin(a0), 600 + 1900 * math.cos(a0) * 0.7
            _L(pen, poly([(960 - 30, 600), (960 + 30, 600), (ex + 60, ey), (ex - 60, ey)]), 960, 600, ex, ey,
                       [(0, '#fff6e4', 34 * k), (1, '#fff6e4', 0)])
    L = [_cl(2.6, _doorway_glimpse, 'other_cabin', 'cdw:glimpse', (500, 100, 1420, 1100)),
         _cl(1.15, back, 'wall', 'cdw:wall', NEAR), _cl(1.12, spill, 'spill', 'cdw:spill', NEAR)]
    if var == 'red':
        L.append(_cl(1.1, lambda pen, t: (_R(pen, None, 960, 600, 1400, [(0, '#000000', 0), (0.25, GLOW, 70), (0.7, RED, 60), (1, RED, 0)], sy=0.8, clip=False),
                                         pen.fill(rect(-900, -700, 3800, 2400), '#3a0610', 70)), 'red_light', 'cdw:red', NEAR,
                     alpha=lambda t: 0.75 + 0.25 * math.sin(t * 2.0)))
    gb = Beam(lambda t: (960, 560, 960, 1300, 1.0), w0=200, spread=0.5, spot=0)
    L.append(_live(0.97, lambda pen, t: motes(pen, t, (400, 250, 1500, 1250), 110, 211, gb, '#fff6e4', 0.05), 'haze_dust', blur=0))
    L.append(_live(1.05, lambda pen, t: mist(pen, t, 640, 780, 1500, 260, 5, 7, 30, '#fff6e4', 22), 'haze', blur=0))
    kf = _flash_k(st, 'flash')
    b = Beam(aim_fn((300, 700), [(st.t0, 900, 700), (st.t1, 980, 680)], kf, 10, 213), spot=150, a=0.25)
    L.append(b.layer(1.0))
    an = dict(tess_doorway=Anchor(700, 1000, 1.0, 640), you_doorway=Anchor(1000, 960, 1.05, 620), doorway=Anchor(960, 600, 1.15, 1),
              queen_doorway=Anchor(1080, 900, 1.6, 600))
    return _sp('cabin_now/doorway', L, an, beam=b)


@view('cabin_now', 'floor_end')
def _v_cab_floor_end(var, st, shot):
    m, zc = 1.5, (1100, 800)
    def room(pen, t):
        _zoom(lambda p, tt: (_window_out(p, tt), _cabin7_back(p, tt), _moon_shafts(p, tt), _cabin7_bunks(p, tt, 0.4, False)), zc[0], zc[1], m)(pen, t)
        gx0, gy0 = 960 + (1118 - zc[0]) * m, 540 + (470 - zc[1]) * m
        g = rect(gx0, gy0, 144 * m, 390 * m)
        _L(pen, g, 0, gy0, 0, gy0 + 390 * m, ['#121a24', '#06090d']); pen.texture(g, 'grunge', 0.2, 'screen', 1.2)
        _L(pen, g, gx0, gy0, gx0 + 144 * m, gy0 + 390 * m, [(0, '#ffffff', 0), (0.5, '#9fb6d8', 30), (1, '#ffffff', 0)])
        pen.line(g, 6, '#2a2e33')
        for i in range(12):
            yy = gy0 + i * 390 * m / 11
            pen.seg((gx0 - 8, yy), (gx0 + 2, yy + 22), 2.5, '#5a4836'); pen.seg((gx0 + 144 * m + 8, yy), (gx0 + 144 * m - 2, yy + 22), 2.5, '#5a4836')
        tw = smooth([(1280, 1010), (1340, 960), (1520, 950), (1640, 990), (1600, 1040), (1380, 1050)], True, 0.7)
        towel_cloth(pen, tw, (1280, 950, 1640, 1050), 0.8, 0, 27, 0.4)
    b2 = Beam(lambda t: (400, 975, 1800, 1030, 1.0), w0=22, spread=0.15, spot=320, spot_sy=0.22, a=0.32)
    L = [_cl(1.15, room, 'room', 'fend:room', NEAR), b2.layer(0.97, 'floor_beam'),
         _live(0.96, lambda pen, t: _flashlight_on_floor(pen, 300, 980, 1.0), 'flashlight', blur=0),
         _live(0.94, lambda pen, t: motes(pen, t, (200, 600, 1900, 1150), 100, 221, b2, CORE, 0.04), 'dust', blur=0)]
    if var == 'phone_glow':
        px, py = 960 + (1060 - zc[0]) * m, 540 + (556 - zc[1]) * m
        L.append(_live(1.12, lambda pen, t: _R(pen, None, px, py, 220, [(0, GLOW, 90 + 40 * math.sin(t * 1.3)), (1, GLOW, 0)], clip=False), 'phone_red'))
    an = dict(noah_floor=Anchor(1060, 960, 1.0, 520, 'seated'), you_floor=Anchor(700, 975, 1.0, 560, 'seated'),
              tess_floor_end=Anchor(1500, 1000, 1.0, 640))
    return _sp('cabin_now/floor_end', L, an, beam=b2)


PHONE = (960.0, 560.0, 330.0, 680.0)      # phone_screen: centre, width, height (portrait)


@view('cabin_now', 'phone_screen')
def _v_cab_phone(var, st, shot):
    cx, cy, w, h = PHONE
    L = _insert_bg('phone', var, st, 700, 1000, 2.0)
    tw = (st.sfx('glass_wipe') or [None])[0]
    tsteps = st.change_t('phone', 'screen_steps') or (st.t0 - 10 if st.v('phone', st.t0) == 'screen_steps' else None)
    scr = rrect(cx - w / 2 + w * 0.045, cy - h / 2 + w * 0.045, w * 0.91, h - w * 0.09, w * 0.09)
    def phone(pen, t):
        dust = 1.0
        if tw is not None: dust = 1.0 - ease_in_out(prog(t, tw - 0.1, tw + 0.5))
        if st.t0 > 682: dust = 0.0
        red = 0.25 + (0.35 * (0.5 + 0.5 * math.sin(t * 1.3)) if var == 'phone_glow' else 0.0)
        phone_prop(pen, cx, cy, w, h, 0.0, lit=0.9, red=red, dust=0.0)
        if dust > 0.01:
            _clip(pen, scr)
            pen.texture(scr, 'grunge', 0.35 * dust, 'screen', 0.8)
            for i in range(90):
                px, py = cx + (_h(i, 3) - 0.5) * w * 0.9, cy + (_h(i, 4) - 0.5) * h * 0.92
                pen.fill(oval(px, py, 1.2 + 2.5 * _h(i, 5)), '#aab4be', int(160 * dust))
            if tw is not None and t >= tw:      # the sleeve's wipe stroke
                u = prog(t, tw - 0.1, tw + 0.5)
                pen.fill(rect(cx - w, cy - h / 2, w * 2 * u, h), '#05070a', int(60 * u))
            _unclip(pen)
        if tsteps is not None and t >= tsteps:
            u = ease_out_cubic(prog(t, tsteps, tsteps + 0.6))
            _clip(pen, scr)
            sc = 0.2
            for k in range(6):
                x, y = cx + (STEP_XY[k][0] - 950) * sc, cy - 40 + (STEP_XY[k][1] - 540) * sc
                pts = _stroke_pts((x + 12, y), (x - 12, y), 6, 0.6, k) + _stroke_pts((x - 12, y), (x - 10, y + 16), 4, 0.4, k + 9)[1:]
                _wax(pen, pts, 4.0, u, 0.6, k, crumbs=False)
            _unclip(pen)
    def bottom_step(pen, t):     # the 7th tiny step is on the other side of the screen: clean, no smear
        if tsteps is None or t < tsteps: return
        u = ease_out_cubic(prog(t, tsteps + 0.2, tsteps + 0.8))
        x, y = cx + (STEP_XY[6][0] - 950) * 0.2, cy - 40 + (STEP_XY[6][1] - 540) * 0.2
        _R(pen, None, x, y, 40, [(0, GLOW, 80 * u), (1, GLOW, 0)], sy=0.3, clip=False)
        pen.seg((x - 13, y), (x - 13 + 26 * u, y), 2.6, RED, int(255 * u))
    L += [_live(1.0, phone, 'phone', blur=0), _live(1.04, bottom_step, 'bottom_step', blur=0),
          _live(0.95, lambda pen, t: _R(pen, None, cx - 60, cy - 160, 260, [(0, '#c8d6e6', 30), (1, '#c8d6e6', 0)], sy=0.5, clip=False), 'glint')]
    an = dict(screen=Anchor(cx, cy, 1.04, 1), bottom_step=Anchor(cx + (STEP_XY[6][0] - 950) * 0.2, cy - 40 + (STEP_XY[6][1] - 540) * 0.2, 1.04, 1))
    return _sp('cabin_now/phone_screen', L, an, dof=6.75, info=dict(screen=scr, insert=True))


def clip_layer(layer, path):
    """Wrap a layer's draw in a clip path (e.g. the queen inside the phone screen: sp.info['screen'])."""
    f = layer.draw
    def d(pen, t):
        pen.cv.save(); pen.cv.clipPath(path, skia.ClipOp.kIntersect, True); f(pen, t); pen.cv.restore()
    layer.draw = d
    return layer


# ====================================================================== mirror_world (inside the glass)
VOID, VOID2 = '#080c14', '#0b0d14'


def _stairs_geom(n=30, vy=380, y_near=1500, y_end=780):
    """Tread front edges from the foreground (y_near) to the landing (y_end), converging on (960, vy)."""
    out = []
    for i in range(n):
        u = i / (n - 1)
        y = y_end + (y_near - y_end) * (1 - u) ** 1.9
        f = (y - vy) / (y_near - vy)
        out.append((y, 1500 * f + 60))
    return out


def _stairs_draw(pen, t, ylo, yhi, red=1.0, noah_patch=False):
    tr = _stairs_geom(y_end=780 if noah_patch else 420)
    for i in range(len(tr) - 1):
        (y0, w0), (y1, w1) = tr[i], tr[i + 1]
        if not (ylo <= y0 < yhi): continue
        rise = (y0 - y1) * 0.42
        top = poly([(960 - w0, y0 - rise), (960 + w0, y0 - rise), (960 + w1, y1), (960 - w1, y1)])
        _L(pen, top, 0, y1, 0, y0, ['#242c3c', '#3a4256'])
        pen.texture(top, 'grunge', 0.25, 'overlay', 1.0)
        face = rect(960 - w0, y0 - rise, 2 * w0, rise)
        _L(pen, face, 0, y0 - rise, 0, y0, ['#141a26', '#0c1018'])
        k = red * clamp(0.15 + 0.85 * (y0 - 420) / 900)
        pen.seg((960 - w0, y0 - rise), (960 + w0, y0 - rise), max(1.5, 5 * w0 / 1500), GLOW, int(60 * k))
        pen.seg((960 - w0, y0 - rise), (960 + w0, y0 - rise), max(1.0, 2.4 * w0 / 1500), RED, int(230 * k))
        _R(pen, None, 960, y0 - rise, w0, [(0, GLOW, 26 * k), (1, GLOW, 0)], sy=0.05, clip=False)
    # the railing on the left
    if ylo < 600:
        pts = [(960 - w * 1.02, y - (y - 380) * 0.55 - 260 * (w / 1500)) for (y, w) in _stairs_geom(y_end=780 if noah_patch else 420)]
        pen.line(poly(pts, False), 14, '#141822'); pen.line(poly(pts, False), 3, '#4a4e5a', 150)
        for (y, w), (px, py) in zip(tr, pts):
            pen.seg((960 - w * 1.02, y - (y - 380) * 0.3), (px, py), max(2, 10 * w / 1500), '#10131c')
    if noah_patch:
        _R(pen, None, 960, 770, 360, [(0, '#e7e5e0', 170), (0.4, '#ccccc9', 70), (1, '#ccccc9', 0)], sy=0.45, clip=False)
        _R(pen, None, 960, 500, 420, [(0, '#dfe8ea', 40), (1, '#dfe8ea', 0)], sy=1.3, clip=False)


def _scratches(pen, t, box, n=120, seed=0, a=70):
    """The queen's world: pale scratch lines on the treads, re-jittering every 3 frames (shimmer)."""
    q = int(t * 60) // 3
    x0, y0, x1, y1 = box
    for i in range(n):
        x = x0 + _h(i, seed) * (x1 - x0); y = y0 + _h(i, seed + 1) ** 0.7 * (y1 - y0)
        ln = 10 + 50 * _h(i, seed + 2) * (y - 380) / 900
        j = (_h(i + q * 131, seed + 3) - 0.5) * 3
        pen.seg((x + j, y), (x + ln + j, y + (_h(i, seed + 4) - 0.5) * 6), 1.1, '#cdd4d5', int(a * (0.3 + 0.7 * _h(i + q * 7, seed + 5))))


@view('mirror_world', 'stairs')
def _v_mw_stairs(var, st, shot):
    noah = var == 'void_noah'
    L = [_cl(30, lambda pen, t: _L(pen, rect(-2000, -1500, 6000, 4000), 0, -200, 0, 1200, ['#04060c', '#0b111c', '#101624', '#0a0e16']), 'void', 'mw:void',
             (-2000, -1500, 4000, 2600))]
    L += [_cl(6.0, lambda pen, t: _stairs_draw(pen, t, 0, 760, 0.8, noah), 'stairs_far', 'mw:far:%s' % noah, (-600, -200, 2520, 1200)),
          _cl(2.0, lambda pen, t: _stairs_draw(pen, t, 760, 1000, 1.0, noah), 'stairs_mid', 'mw:mid:%s' % noah, (-1200, 200, 3120, 1400)),
          _cl(0.8, lambda pen, t: _stairs_draw(pen, t, 1000, 1700, 1.0, noah), 'stairs_near', 'mw:near:%s' % noah, (-2600, 400, 4520, 2000)),
          _cl(5.0, lambda pen, t: _R(pen, None, 960, 420, 560, [(0, '#000000', 255), (0.3, '#000000', 190), (1, '#000000', 0)], sy=0.5, clip=False),
              'depth_dark', 'mw:dd:%s' % noah, (-600, -400, 2520, 1300), alpha=0.0 if noah else 1.0)]
    L.append(_live(1.6, lambda pen, t: _scratches(pen, t, (100, 780, 1820, 1300), 170, 231, 110), 'scratches', blur=0))
    L.append(_cl(12, lambda pen, t: _R(pen, None, 960, 200, 1300, [(0, '#3a4458', 70), (1, '#3a4458', 0)], sy=0.7, clip=False), 'cold_light', 'mw:cold', (-1200, -800, 3100, 1400)))
    L.append(_live(2.5, lambda pen, t: motes(pen, t, (300, 200, 1600, 1100), 50, 233, None, '#cdd4d5', 0.12, fall=10, speed=(3, 8)), 'falling_dust', blur=0))
    breath = (lambda t: 0.8 + 0.2 * math.sin(t * 1.4))
    L.append(_live(7.5, lambda pen, t: _R(pen, None, 960, 760, 260, [(0, '#e7e5e0' if noah else '#8a2030', (60 if noah else 30) * breath(t)), (1, '#000000', 0)],
                                                  sy=0.6, clip=False), 'far_glow', blur=0))
    an = dict(queen_back=Anchor(1240, 1100, 0.72, 1000), noah_far=Anchor(960, 760, 8.0, 150), landing=Anchor(960, 780, 6.0, 1))
    return _sp('mirror_world/stairs', L, an)


@view('mirror_world', 'railing')
def _v_mw_railing(var, st, shot):
    def bal(pen, t):
        pen.line(poly([(-800, 150), (2700, 330)], False), 40, '#141822'); pen.line(poly([(-800, 140), (2700, 320)], False), 4, '#5a5e6a', 160)
        for i in range(-6, 22):
            x = -700 + i * 120
            yt = 150 + (x + 800) * 180 / 3500
            b = rect(x - 16, yt, 32, 1400)
            _L(pen, b, x - 16, 0, x + 16, 0, ['#10141c', '#3a3e4c', '#141820']); pen.line(b, 3, '#05060a')
            pen.seg((x + 10, yt + 10), (x + 10, yt + 1300), 1.5, '#cdd4d5', 50)
        pen.line(poly([(-800, 980), (2700, 1100)], False), 30, '#10131c')
    L = [_cl(30, lambda pen, t: _L(pen, rect(-2000, -1500, 6000, 4000), 0, -200, 0, 1300, ['#060810', '#101622', '#1e0a12']), 'void', 'mwr:void', (-2000, -1500, 4000, 2600)),
         _live(8, lambda pen, t: _R(pen, None, 960, 1300, 1400, [(0, GLOW, 50 + 15 * math.sin(t * 1.2)), (1, GLOW, 0)], sy=0.5, clip=False), 'under_glow'),
         _cl(1.0, bal, 'railing', 'mwr:bal', NEAR),
         _live(1.2, lambda pen, t: _scratches(pen, t, (-200, 200, 2100, 1100), 60, 241, 40), 'scratches', blur=0),
         _live(0.9, lambda pen, t: motes(pen, t, (0, 0, 1920, 1080), 40, 243, None, '#cdd4d5', 0.1, fall=8, speed=(3, 8)), 'dust', blur=0)]
    return _sp('mirror_world/railing', L, dict(hand=Anchor(980, 600, 1.0, 260), queen_side=Anchor(1500, 1000, 0.8, 820)))


@view('mirror_world', 'feet')
def _v_mw_feet(var, st, shot):
    red = 1.8 if var == 'red' else 1.0
    def treads(pen, t):
        _L(pen, rect(-900, -700, 3800, 2400), 0, -700, 0, 1600, ['#020306', VOID, '#05070c'])
        for (yt, ye, rb) in ((300, 560, 700), (700, 860, 1100), (1100, 1180, 1500)):
            top = poly([(-900, yt), (2820, yt), (2820, ye), (-900, ye)])
            _L(pen, top, 0, yt, 0, ye, ['#141a26', '#262c3a']); pen.texture(top, 'grunge', 0.2, 'overlay', 1.2)
            pen.fill(rect(-900, ye, 3800, rb - ye), '#05070c')
            pen.seg((-900, ye), (2820, ye), 14, GLOW, int(50 * red)); pen.seg((-900, ye), (2820, ye), 5, RED, int(min(255, 220 * red)))
            _R(pen, None, 960, ye, 1500, [(0, GLOW, 40 * red), (1, GLOW, 0)], sy=0.08, clip=False)
    L = [_cl(1.1, treads, 'treads', 'mwf:treads:%s' % var, NEAR), _live(1.05, lambda pen, t: _scratches(pen, t, (-300, 300, 2200, 1100), 120, 251, 60), 'scratches', blur=0),
         _live(0.9, lambda pen, t: motes(pen, t, (0, 0, 1920, 1080), 40, 253, None, '#cdd4d5', 0.1, fall=6, speed=(3, 8)), 'dust', blur=0)]
    if var == 'red':
        L.append(_live(1.0, lambda pen, t: _R(pen, None, 1040, 860, 900, [(0, GLOW, 40 + 20 * math.sin(t * 3)), (1, GLOW, 0)], sy=0.4, clip=False), 'red_pulse'))
    return _sp('mirror_world/feet', L, dict(your_step=Anchor(880, 560, 1.0, 600), her_step=Anchor(1040, 860, 1.0, 700)))


@view('mirror_world', 'dress')
def _v_mw_dress(var, st, shot):
    L = [_cl(30, lambda pen, t: _L(pen, rect(-2000, -1500, 6000, 4000), 0, -200, 0, 1300, ['#060810', '#101622', '#1e0a12']), 'void', 'mwd:void', (-2000, -1500, 4000, 2600)),
         _cl(3.0, lambda pen, t: _stairs_draw(pen, t, 860, 1600, 0.7), 'stairs', 'mwd:stairs', (-1200, 300, 3120, 2000)),
         _live(2.5, lambda pen, t: _R(pen, None, 960, 1200, 1100, [(0, GLOW, 46 + 14 * math.sin(t * 1.6)), (1, GLOW, 0)], sy=0.5, clip=False), 'under_glow'),
         _live(0.9, lambda pen, t: motes(pen, t, (0, 0, 1920, 1080), 40, 261, None, '#cdd4d5', 0.1, fall=6, speed=(3, 8)), 'dust', blur=0)]
    return _sp('mirror_world/dress', L, {})


@view('mirror_world', 'eye')
def _v_mw_eye(var, st, shot):
    t0, t1 = st.t0, st.t1
    def eye(pen, t):
        pen.fill(rect(-900, -700, 3800, 2400), '#030407')
        u = prog(t, t0, t1)
        flare = math.exp(-((t - t0 - 0.12) / 0.1) ** 2) * 1.0 + 0.35
        r = 150 * (1.15 - 0.3 * u)
        q = int(t * 60) // 3
        _R(pen, None, 960, 540, r * 6, [(0, GLOW, 90 * flare), (0.3, RED, 40 * flare), (1, RED, 0)], clip=False)
        lid = smooth([(960 - r * 3.2, 540), (960, 540 - r * 1.25), (960 + r * 3.2, 540), (960, 540 + r * 1.1)], True, 0.8)
        pen.fill(lid, '#1a1c22')
        pen.fill(oval(960, 540, r * 2.1, r * 1.05), '#cdd4d5', 60)
        iris = oval(960, 540, r)
        _R(pen, iris, 960, 540, r, ['#ff5a6a', RED, '#5a0a16'])
        for i in range(18):
            a = 2 * math.pi * i / 18
            pen.seg((960 + math.cos(a) * r * 0.25, 540 + math.sin(a) * r * 0.25), (960 + math.cos(a) * r * 0.95, 540 + math.sin(a) * r * 0.95), 2, '#2a0408', 160)
        pen.fill(oval(960, 540, r * 0.07), '#000000')
        pen.fill(oval(960 - r * 0.35, 540 - r * 0.35, r * 0.12), '#ffffff', 220)
        for i in range(26):     # scratch-line eyelid and lashes
            j = (_h(i + q * 13, 5) - 0.5) * 6
            a = math.pi * (0.1 + 0.8 * i / 25)
            px, py = 960 - math.cos(a) * r * 3.0, 540 - math.sin(a) * r * 1.2
            pen.seg((px + j, py), (px + j * 2 - math.cos(a) * 30, py - 50 - 30 * _h(i, 6)), 1.3, '#cdd4d5', 120)
        pen.line(lid, 1.4, '#cdd4d5', 110)
    return _sp('mirror_world/eye', [_live(1.0, eye, 'eye', blur=0)], {})


# ====================================================================== memories (14 years ago: bleached, halation, still moving)
MD = dict(sky0='#ddd2ba', sky1='#c6d2d2', pine='#7e8c6c', pine2='#a2ac8c', lawn='#b6bc84', lawn2='#9aa46c', wood='#c2a27a', wood2='#9a7a58',
          water='#86a8ac', water2='#628890', path='#cbbb98', hi='#efdcb8')
MN = dict(bg='#1a1c2a', bg2='#24263a', lamp='#e8b878', wood='#4a3e3a', wood2='#2e2830')


def _day_sky(pen, y_h=560, P=MD, sun=(1500, 120)):
    _L(pen, rect(-900, -700, 3800, y_h + 700), 0, -700, 0, y_h, [P['sky1'], P['sky0'], _lt(P['sky0'], 0.3)])
    _R(pen, None, sun[0], sun[1], 900, [(0, '#fff8ea', 120), (0.3, P['hi'], 50), (1, P['hi'], 0)], clip=False)


def _mem_layers(L, fog=False, seed=0, c='#fff4dc'):
    """Halation motes / morning mist that keep memories moving."""
    L.append(_live(0.9, lambda pen, t: motes(pen, t, (-100, -100, 2000, 1200), 40, 300 + seed, None, c, 0.18, speed=(4, 10)), 'mem_motes', blur=0))
    if fog: L.append(_live(1.5, lambda pen, t: mist(pen, t, 640, -900, 2900, 420, 9, seed + 3, 32, '#dfe8ea', 16), 'mem_mist', blur=0))
    return L


def _mem_lodge(pen, t):
    _day_sky(pen, 330); treeline(pen, -900, 2900, 330, 260, 24, 311, MD['pine2']); _lodge(pen, c='#9a8a70', day=True)
    pen.fill(rect(-900, -700, 3800, 2400), '#fff4dc', 20)


@view('memory', 'dock')
def _v_mem_dock(var, st, shot):
    def scene(pen, t):
        _day_sky(pen, 520); treeline(pen, -900, 2900, 520, 200, 26, 321, MD['pine'])
        _L(pen, rect(-900, 520, 3800, 1100), 0, 520, 0, 1300, [MD['water'], MD['water2']])
        dock = poly([(760, 560), (1060, 560), (1700, 1500), (200, 1500)])
        _L(pen, dock, 0, 560, 0, 1500, [MD['wood'], _lt(MD['wood'], 0.15)]); pen.texture(dock, 'wood', 0.4, 'overlay', 1.2, 90)
        for i in range(1, 12):
            u = (i / 12) ** 1.7; y = lerp(560, 1500, u); pen.seg((lerp(760, 200, u), y), (lerp(1060, 1700, u), y), 2 + 4 * u, MD['wood2'], 180)
        pen.line(dock, 4)
        for (x, y, h) in ((740, 600, 80), (1080, 600, 80), (420, 1100, 260), (1500, 1100, 260)): pen.shape(rect(x - 10, y - h * 0.3, 20, h), MD['wood2'], 3)
    def glitter(pen, t):
        for i in range(70):
            x = -400 + ((_h(i, 3) * 2800 + 12 * t * (0.5 + _h(i, 4))) % 2800); y = 540 + _h(i, 5) ** 0.7 * 600
            b = max(0.0, math.sin(t * (2 + 3 * _h(i, 6)) + i)) ** 4
            if b > 0.05: pen.fill(oval(x, y, 6 + 12 * _h(i, 7), 1.6 + 1.5 * _h(i, 8)), '#ffffff', int(230 * b))
    L = _mem_layers([_cl(1.2, scene, 'dock', 'mdock', NEAR), _live(1.3, glitter, 'glitter', blur=0)], seed=1)
    return _sp('memory/dock', L, dict(noah_dock=Anchor(1100, 960, 1.0, 600), kid_dock=Anchor(780, 980, 1.0, 470)))


@view('memory', 'pocket')
def _v_mem_pocket(var, st, shot):
    def f(pen, t):
        r = rect(-700, -500, 3300, 2100); pen.fill(r, '#3e7a46'); pen.texture(r, 'fabric', 0.7, 'overlay', 1.6); pen.texture(r, 'grunge', 0.2, 'overlay', 2)
        pk = smooth([(200, 1300), (360, 380), (960, 300), (1560, 380), (1720, 1300)], False, 0.8)
        pen.line(pk, 70, '#2a5a32'); pen.line(pk, 14, '#5a9a62', 180)
        pen.fill(smooth([(380, 420), (960, 330), (1540, 420), (1400, 560), (960, 520), (520, 560)], True, 0.7), '#173a1e')
        pen.dashed(smooth([(330, 1300), (450, 430), (960, 350), (1470, 430), (1590, 1300)], False, 0.8), 5, '#8ac08e', 180, 16, 10)
        _tx(pen, 'CEDAR LAKE', 960, 900, 900, 120, '#e6e0c8', 200, 10)
        _R(pen, None, 700, 300, 1400, [(0, '#fff4dc', 110), (1, '#fff4dc', 0)], clip=False)
    return _sp('memory/pocket', _mem_layers([_cl(1.0, f, 'sweatshirt', 'mpocket', NEAR)], seed=2), dict(pocket=Anchor(960, 450, 1.0, 1)))


@view('memory', 'porch_steps', 'bell_ring_porch')
def _v_mem_porch(var, st, shot):
    vname = shot.get('view')
    L = [_cl(1.1, _mem_lodge, 'lodge', 'mporch', NEAR)]
    if vname == 'bell_ring_porch':
        def b_(pen, t):
            sw = 22 * math.sin((t - st.t0) * 4.4)
            pen.shape(rect(1300, 380, 18, 160), '#6a5a48', 3)
            bell(pen, 1309, 640, 0.55, sw, 1.0, True, rope=True, bracket=True, t=t)
        L.append(_live(1.05, b_, 'bell', blur=0))
    else:
        tb = (st.sfx('bell_drop') or st.sfx('metal_clang') or [None])[0]
        def b2(pen, t):
            if tb is None or t >= tb: bell(pen, 1180, 860, 0.5, -70 if tb is not None else 0, 1.0, True, rope=False, bracket=False, t=t,
                                          vib=math.exp(-(t - tb) * 3) if tb is not None and t >= tb else 0.0)
        L.append(_live(1.0, b2, 'bell', blur=0))
    L = _mem_layers(L, seed=3)
    an = dict(adult_legs=Anchor(1120, 860, 1.0, 1100), noah_steps=Anchor(760, 1080, 0.95, 600), kid_steps=Anchor(1080, 1090, 0.95, 470),
              counselor=Anchor(1180, 860, 1.05, 620))
    return _sp('memory/' + vname, L, an)


@view('memory', 'sprinkler_lawn')
def _v_mem_sprinkler(var, st, shot):
    def scene(pen, t):
        _day_sky(pen, 560); treeline(pen, -900, 2900, 560, 240, 24, 331, MD['pine2'])
        for (x, n) in ((300, '5'), (900, '6'), (1550, '7')): cabin_ext(pen, x, 640, 420, 200, 0.75, n, '#b8a080', '#7a6a58', '#e8dcc0', '#ffffff', 60, seed=int(n), day=True)
        _L(pen, rect(-900, 640, 3800, 900), 0, 640, 0, 1400, [MD['lawn'], MD['lawn2']])
        grass(pen, -900, 2900, 1100, 40, 260, 333, MD['lawn2'], '#ffffff')
    def spray(pen, t):
        x, y = 960, 900
        ang0 = math.radians(-90 + 55 * math.sin(t * 1.6))
        for j in range(60):
            u = ((t * 1.3 + j / 60) % 1.0)
            a = ang0 + (_h(j, 3) - 0.5) * 0.25
            px = x + math.cos(a) * 900 * u; py = y + math.sin(a) * 900 * u + 1100 * u * u
            pen.fill(oval(px, py, 5, 8), '#ffffff', int(200 * (1 - u)))
        sprinkler(pen, x, y, t, (), None, None, 1.0)
    L = _mem_layers([_cl(1.3, scene, 'lawn', 'mspr', NEAR), _live(1.0, spray, 'spray', blur=0)], seed=4)
    return _sp('memory/sprinkler_lawn', L, dict(noah_run=Anchor(1200, 1040, 1.0, 600)))


@view('memory', 'cabin_morning')
def _v_mem_cabin(var, st, shot):
    P = PM if var == 'memory_day' else dict(PM, wall='#d2d8d8', wall2='#c4cacc', floor0='#b4babc', floor1='#ccd2d2', sky0='#e4ecec', sky1='#d8e0e0')
    L = [_cl(1.15, lambda pen, t: _dawn_room(pen, t, P, towel=False, shoe=False, swim=True, made=False), 'room', 'mcab:%s' % var, NEAR),
         _cl(1.12, lambda pen, t: shaft(pen, [(430, 270), (810, 270), (1180, 1250), (380, 1250)], '#fff4dc', 50, 4), 'shaft', 'mcab:sh', NEAR)]
    L = _mem_layers(L, fog=(var == 'memory_morning'), seed=5)
    an = dict(kid_bunk=Anchor(1300, 680, 1.0, 460), kid_sit_dip=Anchor(1420, 930, 1.0, 470, 'seated'), noah_bunk=Anchor(1000, 1010, 1.0, 600))
    return _sp('memory/cabin_morning', L, an)


def _mem_night_room(pen, t):
    pen.fill(rect(-900, -700, 3800, 2400), MN['bg'])
    boards(pen, (-900, -300, 2820, 900), MN['bg2'], False, 120, 341, 0.4)
    floor_persp(pen, -2000, 3900, 1600, -900, 2820, 900, 24, '#2a2630', '#3a3440', 343)
    _R(pen, None, 1500, 500, 1300, [(0, MN['lamp'], 110), (0.4, MN['lamp'], 40), (1, MN['lamp'], 0)], clip=False)


@view('memory', 'bunk_night', 'kids_game')
def _v_mem_bunk_night(var, st, shot):
    vname = shot.get('view')
    def scene(pen, t):
        _mem_night_room(pen, t)
        if vname == 'bunk_night':
            bunk(pen, -100, 2000, 1080, 1.4, '#4a3e3a', '#6a5a52', '#4a3e3a', True, True, '#5a4a62', 0.5, (700, 820), (300, 360), pillow='#d8c8b0')
        else:
            for (x0, c) in ((200, '#6a3a5a'), (1100, '#3a5a7a')):
                sb = smooth([(x0, 900), (x0 + 120, 720), (x0 + 700, 700), (x0 + 760, 880), (x0 + 700, 1040), (x0 + 80, 1060)], True, 0.7)
                pen.fill(sb, c); pen.texture(sb, 'fabric', 0.5, 'overlay', 1.2); pen.line(sb, 4)
                pen.line(smooth([(x0 + 140, 760), (x0 + 680, 740)], False), 5, '#d8c8a0', 180)
    def lamp(pen, t):
        k = 0.92 + 0.08 * noise1(t * 6, 3)
        lantern(pen, 1500, 980 if vname == 'kids_game' else 640, 1.0, k, MN['lamp'], '#3a4a3a')
    L = _mem_layers([_cl(1.1, scene, 'room', 'mbn:' + vname, NEAR), _live(1.05, lamp, 'lantern', blur=0)], seed=6, c=MN['lamp'])
    an = dict(bunk_sleep=Anchor(900, 690, 1.0, 900), kids=Anchor(960, 1000, 1.0, 470))
    return _sp('memory/' + vname, L, an)


@view('memory', 'watch_cu')
def _v_mem_watch(var, st, shot):
    tw = st.ev('watch')
    tchg = tw[0] if isinstance(tw, list) and tw else st.t0 + 1.5
    def watch(pen, t):
        strap = rrect(-400, 380, 2700, 320, 60); pen.fill(strap, '#2a2a30'); pen.texture(strap, 'grunge', 0.3, 'overlay')
        for i in range(14): pen.seg((-300 + i * 200, 400), (-300 + i * 200, 680), 3, '#18181c')
        case = rrect(620, 250, 680, 580, 90)
        pen.shadow(case, 10, 20, 30, '#000000', 160)
        _L(pen, case, 620, 250, 1300, 830, ['#5a5e66', '#2a2c32', '#121316']); pen.line(case, 7)
        for (bx, by) in ((600, 400), (600, 680), (1320, 400), (1320, 680)): pen.shape(rect(bx - 20, by - 30, 40, 60), '#3a3c44', 4)
        lcd = rrect(720, 360, 480, 360, 26)
        _L(pen, lcd, 0, 360, 0, 720, ['#b8c4a0', '#9aa884']); pen.line(lcd, 5)
        hhmm = '6:45' if t < tchg else '4:45'
        blink = (t >= tchg and int((t - tchg) * 4) % 2 == 0 and t < tchg + 1.2)
        _tx(pen, 'ALM', 960, 450, 800, 60, '#2a3020', 230, 8)
        if not blink: _tx(pen, hhmm, 960, 640, 800, 170, '#1e2418', 240, 4)
        pen.fill(rrect(700, 340, 520, 30, 14), '#ffffff', 50)
        _tx(pen, 'MODE', 960, 300, 700, 26, '#c8c8c8', 160, 3)
        _R(pen, None, 960, 540, 900, [(0, MN['lamp'], 70), (1, MN['lamp'], 0)], clip=False)
    return _sp('memory/watch_cu', _mem_layers([_cl(1.3, _mem_night_room, 'room', 'mwatch:room', NEAR), _live(1.0, watch, 'watch', blur=0)], seed=7, c=MN['lamp']),
               dict(buttons=Anchor(1320, 400, 1.0, 1)))


@view('memory', 'lipstick_game', 'card_queen')
def _v_mem_lipstick(var, st, shot):
    vname = shot.get('view')
    def glass_l(pen, t):
        pen.fill(rect(-900, -700, 3800, 2400), '#0e1018')
        mirror_frame(pen, 300, -400, 1620, 1500, 88, 4.0, 0.9, night=False)
        _L(pen, rect(300, -400, 1320, 1900), 0, -400, 0, 1500, ['#2a2c3a', '#1a1c28', '#2a2630'])
        _R(pen, None, 960, 1250, 1100, [(0, MN['lamp'], 140), (0.5, MN['lamp'], 50), (1, MN['lamp'], 0)], clip=False)
    def steps_l(pen, t):
        u = prog(t, st.t0 + 0.1, st.t1)
        n = 3 + int(u * 4.999)
        part = (6 - (n - 1) + 0, (u * 4.999) % 1.0) if n < 7 else None
        lipstick_steps(pen, t, drawn=max(1, n - 1) if part else 7, partial=(7 - n, (u * 4.999) % 1.0) if part else None, glow=0.0)
    L = [_cl(1.1, glass_l, 'mirror', 'mlip', NEAR)]
    if vname == 'lipstick_game': L.append(_live(1.0, steps_l, 'steps', blur=0))
    else:
        L.append(_cl(1.05, lambda pen, t: lipstick_steps(pen, t, 7), 'steps', 'mlip:steps', NEAR))
        def card(pen, t):
            pen.cv.save(); pen.cv.translate(960, 760); pen.cv.rotate(-7 + 0.6 * math.sin(t * 0.8))
            c = rrect(-250, -360, 500, 720, 30)
            pen.shadow(c, 14, 20, 30, '#000000', 180)
            pen.fill(c, '#ece4cc'); pen.texture(c, 'paper', 0.6, 'overlay', 1.0); pen.texture(c, 'grunge', 0.3, 'multiply', 0.8)
            pen.line(rrect(-224, -334, 448, 668, 20), 3, '#8a2a2a', 160)
            for sg in (-1, 1):
                pen.cv.save(); pen.cv.scale(sg, sg)
                _tx(pen, 'Q', -196, -270, 800, 64, '#1a1a1a', 240)
                sp_ = smooth([(-196, -236), (-176, -206), (-186, -196), (-196, -204), (-206, -196), (-216, -206)], True, 0.8)
                pen.fill(sp_, '#1a1a1a')
                pen.cv.restore()
            face = rrect(-150, -230, 300, 460, 16); pen.fill(face, '#d8ccb0'); pen.line(face, 3)
            pen.fill(smooth([(-90, -40), (0, -190), (90, -40), (60, 40), (-60, 40)], True, 0.7), '#141418')   # black hair
            pen.fill(oval(0, -60, 50, 64), '#e8dcc8'); pen.fill(oval(-18, -70, 7, 4), '#1a1a1a'); pen.fill(oval(18, -70, 7, 4), '#1a1a1a')
            pen.fill(smooth([(-16, -28), (0, -22), (16, -28), (0, -16)], True, 0.6), RED)
            pen.fill(smooth([(-120, 30), (120, 30), (150, 230), (-150, 230)], True, 0.4), '#1a1a1e')
            pen.seg((-140, 200), (140, 200), 6, RED, 200)
            pen.cv.restore()
        L.append(_live(1.0, card, 'card', blur=0))
    L = _mem_layers(L, seed=8, c=MN['lamp'])
    return _sp('memory/' + vname, L, dict(kid_hands=Anchor(1180, 400, 1.0, 300)))


@view('memory', 'grin_ecu', 'polaroid')
def _v_mem_grin(var, st, shot):
    vname = shot.get('view')
    if vname == 'grin_ecu':
        def bg(pen, t):
            _day_sky(pen, 520); treeline(pen, -900, 2900, 520, 260, 26, 351, MD['pine']); _L(pen, rect(-900, 520, 3800, 1100), 0, 520, 0, 1300, [MD['water'], MD['water2']])
        return _sp('memory/grin_ecu', _mem_layers([_cl(3.0, bg, 'bg', 'mgrin', NEAR)], seed=9), {}, dof=6.75, info=dict(insert=True))
    def pol(pen, t):
        boards(pen, (-900, -700, 2820, 1800), '#8a7258', True, 140, 353, 0.6)
        _R(pen, None, 900, 400, 1400, [(0, '#fff4dc', 120), (1, '#fff4dc', 0)], clip=False)
        pen.cv.save(); pen.cv.translate(960, 540); pen.cv.rotate(-4)
        fr = rect(-380, -420, 760, 860)
        pen.shadow(fr, 14, 22, 30, '#000000', 160); pen.fill(fr, '#d6cfc2'); pen.texture(fr, 'paper', 0.5, 'overlay'); pen.line(fr, 4)
        ph = rect(-330, -370, 660, 640)
        _L(pen, ph, 0, -370, 0, 270, ['#b8cad0', '#d8d0b0'])
        _clip(pen, ph)
        car = smooth([(-340, 150), (-320, 40), (-180, 0), (-80, -70), (150, -70), (260, 10), (340, 40), (340, 150)], True, 0.4)
        pen.fill(car, '#6a3a3a'); pen.line(car, 4); pen.fill(rect(-60, -50, 180, 50), '#a8c0c8'); pen.line(rect(-60, -50, 180, 50), 3)
        for wx in (-200, 220): pen.shape(oval(wx, 150, 50), '#222226', 4)
        pen.fill(rect(-340, 200, 680, 80), '#8a8470')
        try:
            import characters as C
            C.draw_bust(pen, 'noah13', -40, 100, 0.62, C.Pose('grin_kid'))
        except Exception: pass
        hx, hy = 150, -150
        hand = smooth([(hx - 40, hy + 120), (hx - 46, hy), (hx - 30, hy - 110), (hx + 30, hy - 120), (hx + 50, hy - 20), (hx + 46, hy + 120)], True, 0.7)
        pen.fill(hand, '#e0b8a0'); pen.line(hand, 4)
        for j, fx in enumerate((-28, -6, 16)):
            pen.fill(rrect(hx + fx - 10, hy - 140, 22, 70, 9), '#5a8ad0'); pen.line(rrect(hx + fx - 10, hy - 140, 22, 70, 9), 3)
        pen.fill(ph, '#ffe8c0', 60); pen.texture(ph, 'grunge', 0.25, 'multiply', 0.8)
        _unclip(pen)
        pen.line(ph, 3)
        _tx(pen, 'NOAH - 13', 0, 360, 700, 34, '#3a3a6a', 200, 2)
        pen.cv.restore()
    return _sp('memory/polaroid', _mem_layers([_cl(1.0, pol, 'polaroid', 'mpol', NEAR)], seed=10), {})


def _mess_inside(pen, t, P=MD):
    pen.fill(rect(-900, -700, 3800, 2400), '#d4c6a8')
    boards(pen, (-900, -200, 2820, 760), '#bca484', False, 110, 361, 0.4)
    for wx in (100, 700, 1300): _L(pen, rect(wx, 0, 420, 420), 0, 0, 0, 420, ['#ece6d6', '#d8d0c0']); pen.line(rect(wx, 0, 420, 420), 14, '#a08868')
    floor_persp(pen, -2000, 3900, 1600, -900, 2820, 760, 24, '#b8a080', '#d8c0a0', 363)
    for (y, w) in ((820, 1400), (980, 1900)):
        pen.shape(rect(960 - w / 2, y, w, 40), '#a88a64', 4); pen.shape(rect(960 - w / 2, y + 40, w, 16), '#8a6a4a', 3)
    _R(pen, None, 900, 200, 1600, [(0, '#fff8ea', 80), (1, '#fff8ea', 0)], clip=False)


@view('memory', 'bench', 'breakfast_table')
def _v_mem_bench(var, st, shot):
    vname = shot.get('view')
    L = [_cl(1.2, _mess_inside, 'mess_hall', 'mbench', NEAR)]
    if vname == 'breakfast_table':
        def table(pen, t):
            tb = poly([(-900, 860), (2820, 860), (2820, 1600), (-900, 1600)])
            _L(pen, tb, 0, 860, 0, 1600, ['#b08a60', '#8a6a48']); pen.texture(tb, 'wood', 0.5, 'overlay', 1.4); pen.line(tb, 5)
            pen.fill(oval(960, 980, 330, 90), '#dcd8ce'); pen.line(oval(960, 980, 330, 90), 5); pen.line(oval(960, 975, 260, 66), 3, '#c8c0b0')
            for j in range(4):
                pen.fill(oval(960, 960 - j * 22, 220 - j * 8, 52), '#d8a050'); pen.line(oval(960, 960 - j * 22, 220 - j * 8, 52), 3, '#8a5a20')
            pen.fill(_blob(960, 880, 60, 24, 9, 3, 0.3), '#f6e6a0'); pen.fill(smooth([(900, 870), (1040, 880), (1080, 960), (1000, 920)], True, 0.7), '#8a4a18', 200)
        L.append(_cl(0.9, table, 'table', 'mbreak', NEAR))
    L = _mem_layers(L, seed=11)
    return _sp('memory/' + vname, L, dict(noah_bench=Anchor(960, 1000, 1.0, 560, 'seated')))


@view('memory', 'night_window')
def _v_mem_night_window(var, st, shot):
    def win(pen, t):
        pen.fill(rect(-900, -700, 3800, 2400), MN['bg2'])
        boards(pen, (-900, -700, 2820, 1800), MN['bg2'], False, 140, 371, 0.4)
        _L(pen, rect(500, 120, 920, 640), 0, 120, 0, 760, ['#0a0c18', '#16182a']); stars(pen, (500, 120, 1420, 500), 40, 9, 460)
        treeline(pen, 400, 1500, 760, 260, 6, 373, '#0a0c14')
        pen.line(rect(490, 110, 940, 660), 30, '#5a4a40'); pen.seg((960, 120), (960, 760), 16, '#5a4a40')
        pen.fill(rect(440, 760, 1040, 40), '#6a5a4a'); pen.line(rect(440, 760, 1040, 40), 4)
    def lamp(pen, t):
        lantern(pen, 1180, 760, 1.2, 0.95 + 0.05 * noise1(t * 8, 3), MN['lamp'], '#3a4a3a')
        moths(pen, t, 1180, 600, 140, 12, 7, '#e8dcc0')
    L = _mem_layers([_cl(1.1, win, 'window', 'mnw', NEAR), _live(1.0, lamp, 'lantern_moths', blur=0)], seed=12, c=MN['lamp'])
    return _sp('memory/night_window', L, dict(noah_window=Anchor(760, 1080, 1.0, 640)))


@view('memory', 'search_pines', 'kitchen_staff')
def _v_mem_search(var, st, shot):
    vname = shot.get('view')
    def scene(pen, t):
        _L(pen, rect(-900, -700, 3800, 2400), 0, -700, 0, 1300, ['#d4dcdc', '#c8d2d4', '#b4c0c0'])
        for (d, a, c) in ((0, 520, '#a4b4b4'), (1, 600, '#8c9e9e'), (2, 700, '#788a88')):
            treeline(pen, -900, 2900, a + 160, 420 + 80 * d, 18, 381 + d, c)
            mist(pen, 0, a + 140, -900, 2900, 240, 9, 5 + d, 46, '#dfe8ea', 0)
        pen.fill(rect(-900, 860, 3800, 900), '#b8c4b0')
        if vname == 'kitchen_staff':
            pen.cv.save(); pen.cv.translate(200, 400); pen.cv.scale(0.7, 0.7); pen.cv.translate(-960, -600); _lodge(pen, c='#a89a80', day=True, sign=False); pen.cv.restore()
            pen.fill(rect(-900, -700, 3800, 2400), '#dfe8ea', 50)
    L = [_cl(2.0, scene, 'pines', 'msearch:' + vname, (-900, -700, 2820, 1600)), _live(1.6, lambda pen, t: mist(pen, t, 760, -900, 2900, 300, 9, 3, 40, '#dfe8ea', 20), 'mist', blur=0)]
    if vname == 'search_pines':
        def frame(pen, t):
            pen.fill(minus(rect(-900, -700, 3800, 2400), rect(180, 60, 1560, 960)), PM['trim'])
            pen.line(rect(180, 60, 1560, 960), 12, '#a8a090'); pen.seg((960, 60), (960, 1020), 24, PM['trim']); pen.seg((180, 540), (1740, 540), 18, PM['trim'])
            mesh(pen, (180, 60, 1740, 1020), 18, '#ffffff', 40, 1.2)
        L.append(_cl(0.8, frame, 'window', 'msearch:frame', NEAR))
    L = _mem_layers(L, seed=13)
    an = dict(search_line=Anchor(960, 900, 2.0, 380), director=Anchor(1350, 940, 1.6, 460), kitchen_line=Anchor(900, 940, 1.6, 440))
    return _sp('memory/' + vname, L, an)


@view('memory', 'kitchen')
def _v_mem_kitchen(var, st, shot):
    def k(pen, t):
        pen.fill(rect(-900, -700, 3800, 2400), '#d0d2ce')
        for i in range(30):
            for j in range(10): pen.fill(rect(-900 + i * 130, -200 + j * 90, 126, 86), '#dcdcd6' if (i + j) % 2 else '#d0d2ce')
        pen.shape(rect(-900, 640, 3800, 60), '#b8bcbc', 4)
        pen.shape(rect(-900, 700, 3800, 900), '#8a9090', 4)
        gr = rect(200, 560, 760, 80); _L(pen, gr, 0, 560, 0, 640, ['#4a4c50', '#2a2c30']); pen.line(gr, 5)
        bowl = smooth([(1100, 640), (1120, 540), (1400, 540), (1420, 640)], True, 0.5); pen.fill(bowl, '#d8d4c8'); pen.line(bowl, 5)
        pen.fill(oval(1260, 548, 150, 20), '#f0dca0')
        perc = smooth([(1560, 640), (1540, 380), (1600, 300), (1700, 300), (1760, 380), (1740, 640)], True, 0.6)
        _L(pen, perc, 1540, 0, 1760, 0, ['#8a9096', '#e0e4e8', '#6a7076']); pen.line(perc, 5); pen.shape(oval(1650, 290, 30, 14), '#3a3a3a', 3)
        pen.shape(rect(600, 120, 20, 80), '#5a5a5a', 3)
        bell(pen, 610, 330, 0.5, 0.0, 1.0, True, rope=True, bracket=False, t=0.0)
        _R(pen, None, 700, 100, 1500, [(0, '#fff8ea', 70), (1, '#fff8ea', 0)], clip=False)
    L = _mem_layers([_cl(1.0, k, 'kitchen', 'mkit', NEAR)], fog=True, seed=14)
    return _sp('memory/kitchen', L, {})


@view('memory', 'buses')
def _v_mem_buses(var, st, shot):
    def scene(pen, t):
        _day_sky(pen, 600, sun=(960, 60)); treeline(pen, -900, 2900, 600, 300, 24, 391, MD['pine2'])
        pen.fill(rect(-900, 600, 3800, 900), MD['path'])
        for (x, s) in ((-200, 0.9), (700, 1.0)):
            bx, by = x, 860
            body = rrect(bx, by - 380 * s, 1100 * s, 380 * s, 30 * s)
            pen.shadow(body, 16, 20, 20, '#000000', 90)
            _L(pen, body, 0, by - 380 * s, 0, by, ['#f2c03a', '#d89a1a']); pen.line(body, 5)
            for i in range(7):
                w = rect(bx + 60 * s + i * 140 * s, by - 330 * s, 110 * s, 110 * s)
                _L(pen, w, 0, by - 330 * s, 0, by - 220 * s, ['#e8f0f0', '#a8b8bc']); pen.line(w, 4)
            pen.fill(rect(bx, by - 200 * s, 1100 * s, 20 * s), '#1a1a1a')
            _tx(pen, 'SCHOOL BUS', bx + 550 * s, by - 160 * s, 900, 40 * s, '#1a1a1a', 220, 4)
            for wx in (bx + 200 * s, bx + 880 * s): pen.shape(oval(wx, by, 70 * s), '#1a1a1e', 5)
        chain_gate(pen, -900, -300, 560, 900, 1.0, '#7a8088', '#9aa0a8', 120)
    L = _mem_layers([_cl(1.0, scene, 'buses', 'mbus', NEAR)], seed=15)
    return _sp('memory/buses', L, dict(bus_window=Anchor(1225, 600, 1.0, 0.32)))


@view('memory', 'gate_close')
def _v_mem_gate_close(var, st, shot):
    t0 = st.t0
    def bg(pen, t):
        _day_sky(pen, 600); treeline(pen, -900, 2900, 600, 320, 24, 401, MD['pine2']); pen.fill(rect(-900, 600, 3800, 900), MD['path'])
        for xx in (585, 1335):
            p = rect(xx - 34, 200, 68, 720); _L(pen, p, xx - 34, 0, xx + 34, 0, ['#7a6a58', '#a8947a', '#6a5a48']); pen.line(p, 4)
        sgn = rrect(560, 262, 800, 100, 10); pen.fill(sgn, '#8a7050'); pen.line(sgn, 4)
        _tx(pen, 'CAMP CEDAR LAKE', 960, 330, 900, 58, '#f6ecd0', 240, 6)
    def gate(pen, t):
        u = ease_in_out(prog(t, t0 + 0.1, t0 + 1.4))
        for side in (-1, 1):
            hinge = 640 if side < 0 else 1280
            w = 320 * (0.25 + 0.75 * u)
            x0 = hinge if side < 0 else hinge - w
            chain_gate(pen, x0, x0 + w, 480, 900, 1.0, '#6a7078', '#8a9098', 150)
        if u >= 1:
            k = prog(t, t0 + 1.5, t0 + 2.2)
            chain(pen, [(930, 650), (960, 705), (995, 650), (1000, 760 * k + 650 * (1 - k)), (950, 770)], 0.8, 0.9, '#9aa0a8')
            padlock(pen, 960, 700, 0.9, 0.9, 0.0, 1.0 - ease_out_back(prog(t, t0 + 2.2, t0 + 2.4)))
    L = _mem_layers([_cl(1.2, bg, 'gate_bg', 'mgate', NEAR), _live(1.0, gate, 'gate', blur=0)], seed=16)
    return _sp('memory/gate_close', L, {})


@view('memory', 'storage_shed')
def _v_mem_shed(var, st, shot):
    t0, t1 = st.t0, st.t1
    def shed(pen, t):
        pen.fill(rect(-900, -700, 3800, 2400), '#5a4a3a')
        boards(pen, (-900, -700, 2820, 900), '#6a5844', False, 120, 411, 0.6)
        shaft(pen, [(1400, -700), (1700, -700), (1300, 1400), (700, 1400)], '#fff0c8', 70, 4)
        floor_persp(pen, -2000, 3900, 1600, -900, 2820, 900, 22, '#4a3c2e', '#6a5844', 413)
    def box(pen, t):
        u = prog(t, t0 + 0.1, t1 - 0.4)
        crate(pen, 600, 620, 1320, 1000, 1.5, 1.0, night=False, tag=True)
        if u < 0.6: bell(pen, 960, lerp(200, 700, ease_in_out(u / 0.6)), 0.8, 3 * math.sin(t * 3), 1.0, True, rope=False, bracket=False, t=t)
        lid = ease_in_out(prog(u, 0.65, 1.0))
        if lid > 0:
            pen.cv.save(); pen.cv.translate(600, 620); pen.cv.rotate(-80 * (1 - lid))
            lr = rect(0, -40, 720, 40); pen.fill(lr, '#a88a5a'); pen.texture(lr, 'wood', 0.5, 'overlay'); pen.line(lr, 4); pen.cv.restore()
    L = _mem_layers([_cl(1.2, shed, 'shed', 'mshed', NEAR), _live(1.0, box, 'crate', blur=0)], seed=17)
    return _sp('memory/storage_shed', L, {})


@view('memory', 'path_run')
def _v_mem_path_run(var, st, shot):
    tsp = (st.sfx('water_splash') or st.sfx('puddle_splash') or [st.t0 + 1.0])[0]
    def scene(pen, t):
        _day_sky(pen, 520); treeline(pen, -900, 2900, 520, 240, 24, 421, MD['pine2'])
        pen.cv.save(); pen.cv.translate(1300, 560); pen.cv.scale(0.45, 0.45); pen.cv.translate(-960, -600); _lodge(pen, c='#a89a80', day=True); pen.cv.restore()
        pen.fill(rect(-900, 640, 3800, 900), MD['lawn'])
        p = poly([(-900, 900), (2820, 820), (2820, 1100), (-900, 1180)]); pen.fill(p, MD['path']); pen.texture(p, 'asphalt', 0.3, 'overlay')
        pen.fill(oval(960, 1010, 260, 40), '#9ab4bc'); pen.fill(oval(920, 1000, 120, 10), '#ffffff', 150)
    def splash(pen, t):
        u = t - tsp
        if u < 0 or u > 0.9: return
        for j in range(30):
            a = math.pi * (1.05 + 0.9 * _h(j, 3)); v = 500 + 500 * _h(j, 4)
            pen.fill(oval(960 + math.cos(a) * v * u, 1000 + math.sin(a) * v * u + 1800 * u * u, 6, 9), '#e8f4f8', int(220 * (1 - u / 0.9)))
    L = _mem_layers([_cl(1.2, scene, 'path', 'mrun', NEAR), _live(1.0, splash, 'splash', blur=0)], seed=18)
    return _sp('memory/path_run', L, dict(run_a=Anchor(800, 1060, 1.0, 600), run_b=Anchor(1150, 1050, 1.0, 470)))


@view('memory', 'bell_ecu')
def _v_mem_bell_ecu(var, st, shot):
    return _sp('memory/bell_ecu', _mem_layers(_bell_ecu_layers('mbecu', st, var, None, True), seed=19), {})


# ====================================================================== phone screens (the phone itself is HUD): live backgrounds
@view('ui', 'text', 'voicemail', 'call')
def _v_ui(var, st, shot):
    t = st.t0
    if t < 89:      # at the gate
        L = [_cl(3.0, _zoom(lambda pen, tt: (_night_sky('x', 600)[0].draw(pen, tt), _gate_world('uig', st, 'moon_flash')[0].draw(pen, tt)), 960, 640, 1.3),
                 'gate_bg', 'ui:gate', NEAR, dim=0.3)]
        kf = (lambda tt: 1.0)
        b = Beam(aim_fn((1500, 900), [(st.t0, 700, 600), (st.t1, 1300, 640)], kf, 30, 431), spot=300, a=0.25)
        L.append(b.layer(2.5))
    else:
        L = _insert_bg('ui', 'after' if t > 600 else 'flash', st, 1100, 760, 1.6)
        for l in L: l.dim = 0.3
    L.append(_live(0.9, lambda pen, tt: motes(pen, tt, (-100, -100, 2000, 1200), 50, 433, None, CORE, 0.12), 'dust', blur=0))
    return _sp('ui/' + shot.get('view', 'text'), L, {}, dof=6.75, info=dict(insert=True))
