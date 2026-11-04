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


def _beam_sprite(ratio, soft):
    """Cone image (premultiplied BGRA, 512 x 256): apex at the left edge, full width w1 at the right; alpha falls off
    along the length and softly across the edges. ratio = w0 / w1."""
    key = (round(ratio, 2), round(soft, 2))
    if key in _SPR: return _SPR[key]
    W, H = 512, 256
    u = (np.arange(W, dtype=np.float32) + 0.5) / W
    v = (np.arange(H, dtype=np.float32) + 0.5) / H * 2 - 1
    U, V = np.meshgrid(u, v)
    hw = ratio + (1 - ratio) * U
    d = np.abs(V) / np.maximum(hw, 1e-3)
    across = np.clip(1.0 - d, 0, 1) ** (0.6 + soft) * np.exp(-1.8 * d * d)
    along = np.clip(U / 0.02, 0, 1) * (1 - U) ** 0.85 * (0.6 + 0.4 * np.exp(-U * 4))
    a = np.clip(across * along * 1.6, 0, 1)
    arr = np.zeros((H, W, 4), np.uint8)
    r, g, b = rgb(CORE)
    arr[..., 3] = (a * 255).astype(np.uint8)
    arr[..., 2] = (a * r).astype(np.uint8); arr[..., 1] = (a * g).astype(np.uint8); arr[..., 0] = (a * b).astype(np.uint8)
    img = skia.Image.fromarray(np.ascontiguousarray(arr), skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType)
    _SPR[key] = (img, arr)
    return _SPR[key]


_SLIN = skia.SamplingOptions(skia.FilterMode.kLinear)


def draw_beam(pen, sx, sy, ax, ay, k=1.0, w0=26.0, spread=0.32, length=None, a=0.35, blend='plus', soft=0.4):
    """Flashlight cone from (sx, sy) toward (ax, ay): core #fff2d6 at alpha a falling to 0 over its length."""
    if k <= 0.01: return
    dx, dy = ax - sx, ay - sy
    L = length or math.hypot(dx, dy) * 1.25
    ang = math.degrees(math.atan2(dy, dx))
    w1 = w0 + 2 * L * spread
    img, _ = _beam_sprite(w0 / w1, soft)
    cv = pen.cv
    cv.save(); cv.translate(sx, sy); cv.rotate(ang)
    p = skia.Paint(AntiAlias=False); p.setAlphaf(clamp(a * k / 0.35 * 0.55))
    p.setBlendMode(skia.BlendMode.kPlus if blend == 'plus' else skia.BlendMode.kSrcOver)
    cv.drawImageRect(img, skia.Rect.MakeWH(512, 256), skia.Rect.MakeLTRB(0, -w1 / 2, L, w1 / 2), _SLIN, p,
                     skia.Canvas.kFast_SrcRectConstraint)
    w2 = w0 * 2 + 2 * L * spread * 1.7                      # atmospheric haze around the cone
    p.setAlphaf(clamp(a * k / 0.35 * 0.22))
    cv.drawImageRect(img, skia.Rect.MakeWH(512, 256), skia.Rect.MakeLTRB(-L * 0.04, -w2 / 2, L * 1.1, w2 / 2), _SLIN, p,
                     skia.Canvas.kFast_SrcRectConstraint)
    cv.restore()


def hot_spot(pen, x, y, r, k=1.0, sy=0.8, c=FALL, core=CORE):
    """Pool of flashlight light on a surface: warm falloff, a hot core (draw with the beam)."""
    if k <= 0.01: return
    pen.radial(None, x, y, r * 2.0, [(0, c, 46 * k), (0.5, c, 20 * k), (1, c, 0)], sy=sy, clip=False)
    pen.radial(None, x, y, r, [(0, core, 105 * k), (0.55, c, 80 * k), (0.8, c, 52 * k), (1, c, 0)], sy=sy, clip=False)
    pen.radial(None, x, y, r * 0.3, [(0, '#ffffff', 60 * k), (1, core, 0)], sy=sy, clip=False)


def lens_flare(pen, x, y, k=1.0, c=CORE, cx=960, cy=540):
    """Flashlight pointing near the lens: hot core, horizontal streak, ghosts mirrored through the frame centre."""
    if k <= 0.01: return
    pen.radial(None, x, y, 260 * k, [(0, '#ffffff', 200 * k), (0.12, c, 150 * k), (0.4, c, 40 * k), (1, c, 0)], clip=False)
    pen.radial(None, x, y, 900, [(0, c, 60 * k), (1, c, 0)], sy=0.018, clip=False)
    for i, (f, r, cc) in enumerate(((0.5, 40, '#9fd0ff'), (0.9, 22, '#ffd0a0'), (1.35, 70, '#a0ffd0'), (1.7, 30, '#ffb0c0'))):
        gx, gy = x + (cx - x) * f * 2 * 0.5, y + (cy - y) * f * 2 * 0.5
        pen.radial(None, gx, gy, r * 1.6, [(0, cc, 0), (0.7, cc, 38 * k), (1, cc, 0)], clip=False)


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
            pen.radial(None, x, y, r, [(0, c, a * 0.35), (0.7, c, a * 0.28), (1, c, 0)], clip=False)
        else:
            r = size[0] + (size[1] - size[0]) * h2
            pen.radial(None, x, y, r * 1.8, [(0, c, a), (0.45, c, a * 0.7), (1, c, 0)], clip=False)


def fireflies(pen, t, box, n=8, seed=0, c='#e4f59a'):
    x0, y0, x1, y1 = box
    for i in range(n):
        h1, h2, h3 = _h(i, seed), _h(i, seed + 1), _h(i, seed + 2)
        x = x0 + ((h1 * (x1 - x0) + (14 + 20 * h3) * t * (1 if h2 > 0.5 else -1)) % (x1 - x0))
        y = y0 + h2 * (y1 - y0) + 40 * noise1(t * 0.35 + i, seed + 3)
        b = max(0.0, math.sin(t * (0.9 + 0.8 * h3) * 2 + i * 2.1)) ** 3
        if b < 0.03: continue
        pen.radial(None, x, y, 26, [(0, '#ffffff', 220 * b), (0.12, c, 200 * b), (0.4, c, 60 * b), (1, c, 0)], clip=False)


def mist(pen, t, y, x0, x1, h, n=7, seed=0, a=24, c='#a9bfd6', speed=14.0):
    """Drifting mist band at height y (bands of soft ellipses moving at `speed` px/s, wrapping)."""
    W = x1 - x0
    for i in range(n):
        w = (0.25 + 0.35 * _h(i, seed)) * W
        x = x0 + ((_h(i, seed + 1) * W + speed * (0.7 + 0.6 * _h(i, seed + 2)) * t) % (W + w)) - w / 2
        yy = y + (_h(i, seed + 3) - 0.5) * h * 0.6 + 6 * noise1(t * 0.2 + i, seed)
        pen.radial(None, x, yy, w / 2, [(0, c, a), (0.6, c, a * 0.5), (1, c, 0)], sy=h / w, clip=False)


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
        if r > 2.0: pen.radial(None, x, y, r * 5, [(0, c, 60), (1, c, 0)], clip=False)


def twinkle(pen, t, box, n, seed, ymax, c='#ffffff'):
    x0, y0, x1, y1 = box
    for i in range(n):
        x = x0 + _h(i, seed) * (x1 - x0); y = y0 + _h(i, seed + 1) ** 1.6 * (ymax - y0)
        b = max(0.0, math.sin(t * (1.5 + 2 * _h(i, seed + 2)) + i)) ** 6
        if b > 0.05:
            pen.radial(None, x, y, 9, [(0, c, 200 * b), (1, c, 0)], clip=False)
            pen.seg((x - 8 * b, y), (x + 8 * b, y), 1.0, c, int(150 * b)); pen.seg((x, y - 8 * b), (x, y + 8 * b), 1.0, c, int(150 * b))


def moon(pen, x, y, r, c='#e9eefc'):
    pen.radial(None, x, y, r * 9, [(0, MOON, 70), (0.25, MOON, 26), (1, MOON, 0)], clip=False)
    pen.radial(None, x, y, r * 2.2, [(0, '#ffffff', 90), (1, MOON, 0)], clip=False)
    d = oval(x, y, r)
    pen.radial(d, x - r * 0.3, y - r * 0.3, r * 1.3, [(0, '#ffffff'), (0.7, c), (1, '#b9c4e6')])
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
        if horizontal: pen.linear(r, 0, y0 + i * bw, 0, y0 + (i + 1) * bw, [_lt(tone, 0.05), tone, _dk(tone, 0.12)])
        else: pen.linear(r, x0 + i * bw, 0, x0 + (i + 1) * bw, 0, [_lt(tone, 0.04), tone, _dk(tone, 0.1)])
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
    pen.linear(path, 0, y_f, 0, y_n, [c0, c1])
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
    pen.linear(poly(pts), pts[0][0], pts[0][1], pts[2][0], pts[2][1], [(0, c, a / 255.0 * 255 * 0.9), (1, c, 0)])


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
        pen.radial(None, x, y - 60 * s, 520 * s, [(0, glass, 90 * k), (0.3, glass, 34 * k), (1, glass, 0)], clip=False)
    base = rrect(x - 34 * s, y - 26 * s, 68 * s, 26 * s, 6 * s)
    pen.shape(base, body, 3 * s)
    g = rrect(x - 26 * s, y - 96 * s, 52 * s, 72 * s, 8 * s)
    pen.radial(g, x, y - 60 * s, 60 * s, [(0, '#ffffff'), (0.5, glass), (1, _dk(glass, 0.2))] if k > 0.3 else [_dk(glass, 0.5), _dk(glass, 0.6)])
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
    pen.radial(oval(cx, cy, r * 0.94), cx - r * 0.3, cy - r * 0.35, r * 1.4, [_lt(face, 0.1), face, _dk(face, 0.25)])
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
    pen.linear(fr, x0 - fw, 0, x1 + fw, 0, [_lt(base, 0.08), base, _dk(base, 0.25)])
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
    pen.linear(path, x0, y0, x1, y1, [_lt(refl, 0.08), refl, base, _dk(base, 0.3)])
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
        pen.radial(None, px, py, 46 * s, [(0, '#c8d2dc', 22), (0.6, '#c8d2dc', 10), (1, '#c8d2dc', 0)], sy=0.75, clip=False)
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


def lipstick_steps(pen, t, drawn=7, partial=None, smear=None, glow=0.0, wipe=None, erase=None, sc=1.0, ox=0.0, oy=0.0,
                   fade=1.0, seed=11):
    """The seven lipstick treads (top k=0 .. bottom k=6) in mirror_cu coordinates (scaled by sc about (ox, oy)).
    drawn = how many from the bottom are complete (the hook draws the top two on); partial = (k, u) a stroke being drawn;
    smear[k] = 0..1 down-right drag; glow = red glow (climax); wipe = y line: everything above it is streaked downward;
    erase = fraction of red left (1 = all), fade = overall alpha."""
    smear = smear or [0.0] * 7
    cv = pen.cv
    cv.save(); cv.translate(ox, oy); cv.scale(sc, sc); cv.translate(-ox, -oy)
    first = 7 - drawn
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
            for j in range(5):                           # dragged-down smears, tapering, with drips
                cx_ = x - 50 + j * 25 + 6 * (_h(j + k * 9, seed) - 0.5)
                L = dy * (0.45 + 0.55 * _h(j + k * 9, seed + 1))
                w0, w1 = 15 + 6 * _h(j, seed + 2), 4 + 3 * _h(j, seed + 3)
                pts_l = [(cx_ - w0 / 2 + 5 * math.sin(i * 1.7 + j), y + L * i / 6) for i in range(7)]
                pts_r = [(cx_ + w0 / 2 - (w0 - w1) / 2 * (i / 6) + 4 * math.sin(i * 2.1 + j), y + L * i / 6) for i in range(7)]
                band = poly(pts_l + pts_r[::-1])
                pen.linear(band, 0, y, 0, y + L, [(0, RED, 210 * fade), (0.55, RED, 120 * fade), (1, RED, 10 * fade)])
                pen.fill(oval(cx_ + 1, y + L, w1 * 0.7, w1), RED_DK, int(150 * fade))
            pen.fill(oval(x, y, 72, 12), RED, int(110 * fade))
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
    pen.radial(None, x + L * u / 2, y, L * 0.75, [(0, GLOW, 70 * glow * k), (0.5, GLOW, 22 * glow * k), (1, GLOW, 0)], sy=0.22, clip=False)
    pen.seg((x, y), (x1, y), 10, GLOW, int(60 * k * glow))
    pen.seg((x, y), (x1, y), 6, RED, int(255 * k))
    pen.seg((x, y - 1.6), (x1, y - 1.6), 1.6, '#ff9aa8', int(170 * k))
    if 0 < u < 1: pen.radial(None, x1, y, 22, [(0, '#ffd0d8', 230), (1, GLOW, 0)], clip=False)
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
        pen.linear(rect(fx - 30 * s, y0, 60 * s, y1 - y0), fx - 30 * s, 0, fx + 30 * s, 0,
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
    pen.linear(scr, -w / 2, -h / 2, w / 2, h / 2, ['#0e1218', '#05070a', '#0b0f14'])
    _clip(pen, scr)
    pen.linear(poly([(-w, -h * 0.2), (w, -h * 0.55), (w, -h * 0.45), (-w, -h * 0.08)]), 0, -h * 0.5, 0, 0,
               [(0, '#ffffff', 0), (0.5, '#c8d6e6', 46 * lit), (1, '#ffffff', 0)])
    if red > 0: pen.radial(None, w * 0.15, h * 0.1, w * 0.9, [(0, GLOW, 90 * red), (1, GLOW, 0)], clip=False)
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
            pen.linear(m, 0, ya, 0, yb, [(0, '#ffffff', 30), (0.4, '#000000', 0), (1, '#000000', 90)])
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
        pen.linear(post, xx, 0, xx + pw, 0, [_lt(pc, 0.15 + 0.3 * lit), pc, _dk(pc, 0.3)])
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
    n = 5; w = (x1 - x0) / n
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
        pen.linear(p, 0, y, 0, y + hh, [(0, '#000000', 0), (1, '#000000', 70)])
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
    pen.radial(b, -7, -6, 30, ['#ff8a8a', red, '#7a0e18'])
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
        pen.linear(rect(fx - step, y0, step * 2, y1 - y0), fx - step, 0, fx + step, 0,
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
    pen.linear(body, cx - 104 * s, 0, cx + 104 * s, 0, [dark, mid, hi, mid, dark, _dk(dark, 0.4)])
    pen.texture(body, 'grunge', 0.35, 'multiply', 0.8 * s)
    pen.radial(body, cx - 30 * s, cy + 10 * s, 70 * s, [(0, '#ffffff', 90 * light), (1, '#ffffff', 0)], sy=1.8)
    if red: pen.linear(body, cx + 104 * s, 0, cx, 0, [(0, '#ff3a50', 150 * red), (1, '#ff3a50', 0)])
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
        pen.linear(r, 0, y0 + i * sh, 0, y0 + (i + 1) * sh, [_lt(tone, 0.08), tone, _dk(tone, 0.15)])
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
        _ttext(pen, 'SAVE FOR THE', (x0 + x1) / 2, y0 + sh * 1.55, fs * 0.9, '#20242a', 225, 900, fs * 0.08, worn=0.6, seed=seed)
        _ttext(pen, 'MUSEUM', (x0 + x1) / 2, y0 + sh * 1.55 + fs * 1.15, fs * 1.25, '#20242a', 225, 900, fs * 0.14, worn=0.7, seed=seed + 1)
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
    pen.linear(b, -36 * s, 0, 36 * s, 0, [_dk(c, 0.5), mix(_dk(c, 0.3), c, lit), _lt(c, 0.3 * lit), _dk(c, 0.4)])
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
    boards(pen, (x0, wall_top - rh, x1, wall_top), _dk(c, 0.1), False, 24 * s, seed + 1, 0.4, nails=False, lw=1.4 * s) if False else None
    pen.fill(gable, _dk(c, 0.12)); pen.texture(gable, 'wood', 0.4, 'overlay', 0.8 * s, 90)
    pen.line(gable, 2.5 * s)
    band = minus(rp, poly([(x0 - ov + 26 * s, wall_top + 8 * s), (x, wall_top - rh + 26 * s), (x1 + ov - 26 * s, wall_top + 8 * s)]))
    pen.fill(band, roof); pen.texture(band, 'grunge', 0.45, 'overlay', 0.9 * s)
    pen.line(band, 3 * s)
    pen.seg((x0 - ov, wall_top + 8 * s), (x, wall_top - rh), 3 * s, rim, rim_a)
    if window:
        for wx in (x0 + w * 0.2, x1 - w * 0.2 - w * 0.18):
            wr = rect(wx, wall_top + h * 0.22, w * 0.18, h * 0.32)
            if lit_win: pen.radial(wr, wx + w * 0.09, wall_top + h * 0.38, w * 0.2, ['#ffe0a0', '#b8864f'])
            else: pen.linear(wr, 0, wall_top + h * 0.22, 0, wall_top + h * 0.54, ['#1a2633', '#0a0f16'] if not day else ['#dfe6ea', '#9aa8b2'])
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
        pen.linear(rect(x0 - 600, y0 - 400, x1 - x0 + 1200, horizon + 600 - y0), 0, y0, 0, horizon,
                   [(0, top, 255), (0.6, mid, 255), (1, low, 255)])
        stars(pen, (x0 - 600, y0 - 400, x1 + 600, horizon), 260, seed, horizon - 140)
        for (cx, cy, w, h) in ((380, 120, 900, 40), (1250, 70, 1000, 34), (2100, 200, 800, 30)):
            pen.radial(None, cx, cy, w / 2, [(0, '#2a3e58', 110), (0.6, '#1c2c40', 60), (1, '#1c2c40', 0)], sy=h * 2 / w, clip=False)
            pen.radial(None, cx + w * 0.1, cy - h * 0.3, w / 3, [(0, '#5a6e90', 50), (1, '#5a6e90', 0)], sy=h / w, clip=False)
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
    pen.linear(path, 0, y0, 0, y1, [_dk(c, 0.2), c, _lt(c, 0.05)])
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
            pen.linear(p, xx - 34, 0, xx + 34, 0, ['#0e161e', '#26323c', '#3a4a58', '#1a242e'])
            pen.texture(p, 'wood', 0.55, 'overlay', 1.0, 90)
            for yy in range(240, 900, 70): pen.seg((xx - 30, yy), (xx + 26, yy + 8), 1.5, '#0a0e12', 160)
            pen.line(p, 4)
            pen.seg((xx + 26, 210), (xx + 26, 910), 3, MOON, 80)
            pen.fill(oval(xx, 200, 34, 12), '#3a4652'); pen.line(oval(xx, 200, 34, 12), 3)
        beam_ = rect(520, 196, 900, 46)
        pen.linear(beam_, 0, 196, 0, 242, ['#3a4a58', '#26323e', '#141c24']); pen.texture(beam_, 'wood', 0.5, 'overlay', 1.0); pen.line(beam_, 4)
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
        pen.linear(rect(-900, 880, 3800, 700), 0, 880, 0, 1400, ['#152634', '#233b4c'])
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
        pen.linear(rect(-900, 592, 1500, 28), 0, 592, 0, 620, ['#1c3448', '#0c1824'])
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
            pen.linear(p, xx - 30, 0, xx + 30, 0, ['#1a222a', '#4a5866', '#7a8896', '#2a3440']); pen.line(p, 6)
        pen.linear(rect(-500, 380, 2900, 50), 0, 380, 0, 430, ['#3a4652', '#1a222a']); pen.line(rect(-500, 380, 2900, 50), 6)
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
    pen.linear(r, x, y, x, y + h, ['#7a8c9c', '#5a6a7a'] if not polaroid else ['#9ab0c0', '#d8c8a0'])
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
            pen.linear(rect(sx - 20, py, 40 + 30 * _h(i, 5), ph), sx, 0, sx + 40, 0, [(0, '#7a7466', 0), (0.5, '#7a7466', 60), (1, '#7a7466', 0)])
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
        pen.linear(r, 0, 200, 0, 820, ['#d8b84a', '#b8962e']); pen.texture(r, 'grunge', 0.45, 'multiply', 1.0)
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
        pen.linear(lake, 0, -400, 0, 340, ['#0c1a2a', '#1c3248']); pen.line(lake, 4, '#030608')
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
            pen.radial(None, 1700, 1008 + dy, 260, [(0, '#fff4d8', 130 * k), (0.4, '#fff0c8', 50 * k), (1, '#fff0c8', 0)], sy=0.35, clip=False)
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
        pen.linear(rect(-900, 900, 3800, 700), 0, 900, 0, 1400, ['#152634', '#22384a'])
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
        pen.linear(rect(-900, 860, 3800, 700), 0, 860, 0, 1400, ['#101c26', '#1c2a34'])
        p = poly([(-900, 905), (2900, 905), (2900, 1010), (-900, 1010)])
        _gravel(pen, p, (-900, 905, 2900, 1010), '#2e4050', 5, 500)
        grass(pen, -900, 2900, 905, 36, 320, 8, '#0e1c28', '#4a6480')
    def fence(pen, t):
        for xx in range(-1000, 3000, 340):
            post = rect(xx, 760, 46, 520)
            pen.linear(post, xx, 0, xx + 46, 0, ['#0a1016', '#1e2a34', '#2a3844']); pen.line(post, 4)
            pen.seg((xx + 40, 770), (xx + 40, 1280), 3, MOON, 70)
        for yy in (820, 960):
            r = rect(-1000, yy, 4000, 30)
            pen.linear(r, 0, yy, 0, yy + 30, ['#2a3642', '#121a22']); pen.texture(r, 'wood', 0.5, 'overlay'); pen.line(r, 3)
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
        pen.linear(wr, 0, 420, 0, 590, ['#121c26', '#060a0e'] if not day else ['#c8d4d8', '#8a9aa2'])
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
        pen.linear(post, xx, 0, xx + 36, 0, ['#0c141a', '#26323c', '#3a4854']); pen.texture(post, 'wood', 0.5, 'overlay', 0.8, 90); pen.line(post, 3.5)
        pen.seg((xx + 32, 336), (xx + 32, 796), 2.5, MOON if not day else '#ffffff', 80)
    for k in range(4):   # stacked chairs left
        cx, cy = 420 + k * 6, 560 - k * 34
        pen.line(poly([(cx - 50, cy + 200), (cx - 40, cy), (cx + 40, cy), (cx + 50, cy + 200)], False), 6, '#3a4048')
        pen.shape(rect(cx - 52, cy + 80, 104, 14), '#4a525a', 2)
    floor = poly([(-500, 800), (2420, 800), (2600, 920), (-680, 920)])
    pen.linear(floor, 0, 800, 0, 920, ['#22303a', '#2c3a44'] if not day else ['#a89e8a', '#c8bca0'])
    pen.texture(floor, 'wood', 0.5, 'overlay', 1.2)
    for i in range(30):
        x0_ = -500 + i * 100
        pen.seg((x0_, 800), (x0_ + (x0_ - 960) * 0.06, 920), 2, '#0a0e12', 170)
    pen.line(floor, 3)
    for j in range(3):     # steps down to the path
        yy = 920 + j * 52
        st_ = rect(700 - j * 30, yy, 520 + j * 60, 52)
        pen.linear(st_, 0, yy, 0, yy + 52, ['#2e3c46', '#16202a'] if not day else ['#c8bca0', '#8a806c']); pen.texture(st_, 'wood', 0.5, 'overlay'); pen.line(st_, 3)


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
        pen.linear(rect(-900, -600, 3800, 1100), 0, -500, 0, 480, ['#0a1218', '#1a2832'])
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
    pen.radial(None, 980, 640, 700, [(0, '#2a2418' if not day else '#8a7a58', 255), (1, '#06090c' if not day else '#3a3428', 255)], clip=False)
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
            pen.linear(r, x0, 0, x0 + 250, 0, ['#0e0b07', '#3a3022', '#5a4a34', '#1a140c']); pen.texture(r, 'wood', 0.6, 'overlay', 1.2, 90); pen.line(r, 6)
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
        pen.radial(None, 1000, 600, 700, [(0, '#ffffff', 255 * k), (0.15, '#fff2d6', 200 * k), (1, '#fff2d6', 0)], clip=False)
        pen.radial(None, 1000, 600, 1600, [(0, '#fff2d6', 120 * k), (1, '#fff2d6', 0)], sy=0.04, clip=False)
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
        pen.radial(None, 1350, 860, 600, [(0, GLOW, 70 * k), (1, GLOW, 0)], sy=0.6, clip=False)
    L.append(_live(0.99, red_rim, 'red_rim', blur=0))
    an = dict(tess_crate=Anchor(820, 960, 1.0, 640), crate=Anchor(1050, 810, 1.0, 1))
    return _sp('mess_porch/porch_run', L, an, beam=b)


@view('mess_porch', 'boot_ecu')
def _v_porch_boot(var, st, shot):
    tb = (st.sfx('wood_break') or st.sfx('crate_break') or [st.t0 + 0.3])[0]
    def boards_bg(pen, t):
        floor_persp(pen, -1800, 3700, 1500, -400, 2300, 200, 26, '#121c24', '#34424e', 6)
        pen.linear(rect(-900, -700, 3800, 900), 0, -700, 0, 200, ['#04070a', '#0e161c'])
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
            pen.linear(r, 0, y0, 0, y0 + 120, ['#7a6844', '#5a4a30', '#3a2e1c']); pen.texture(r, 'wood', 0.5, 'overlay', 1.4); pen.line(r, 5)
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
        pen.linear(rect(-900, 760, 3800, 800), 0, 760, 0, 1300, ['#142432', '#22384a'])
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
        pen.linear(wr, 0, 460, 0, 580, [mix('#ffcf8a', '#a8c8ff', blue * 0.7), mix('#c8864a', '#4a6ab8', blue * 0.6)], a=k)
        sway = 0.0
        if 70.32 - 0.1 <= t <= 71.6: sway = math.sin((t - 70.32) * 6) * math.exp(-(t - 70.32) * 2.5) * 22
        cur = smooth([(1180, 460), (1250, 460), (1246 + sway, 520), (1252 + sway * 1.3, 580), (1180, 580)], True, 0.5)
        pen.fill(cur, '#c8a070'); pen.fill(cur, '#000000', 60); pen.line(cur, 2)
        pen.line(wr, 8, '#3a4652'); pen.line(wr, 2.5); pen.seg((1260, 460), (1260, 580), 5, '#3a4652')
        pen.radial(None, 1260, 520, 380, [(0, mix('#ffcf8a', '#8ab0ff', blue * 0.6), 60 * k), (1, '#8ab0ff', 0)], sy=0.7, clip=False)
        pen.radial(None, 1260, 790, 260, [(0, mix('#ffcf8a', '#8ab0ff', blue * 0.6), 40 * k), (1, '#8ab0ff', 0)], sy=0.25, clip=False)
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
    if shot.get('dof') is not None: sp.dof = shot['dof']
    vfx = _var_fx(var, shot); own = sp._fx
    sp._fx = (lambda t: dict(vfx(t), **(own(t) if own else {})))
    sp.info.setdefault('st', st); sp.info['var'] = var
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
        pen.linear(rect(-900, 640, 3800, 900), 0, 640, 0, 1300, ['#142432', '#22384a'])
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
            pen.linear(jamb, xx, 0, xx + 60, 0, ['#1a242e', '#34424e', '#1a242e']); pen.texture(jamb, 'wood', 0.5, 'overlay', 1.0, 90); pen.line(jamb, 5)
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
    kw = dict(drawn=7, partial=None, smear=[0.0] * 7, glow=0.0, wipe=None, fade=1.0)
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
        kw['fade'] = 1.0 - 0.7 * prog(t, er[0], er[1] + 0.6)
    elif var == 'red' and st.v('mirror', t) == 'mirror_again' and st.t0 > 620.0 - 1e-3:
        kw['wipe'] = 1100; kw['fade'] = 0.25          # after the wipe: only the last streaks are left
    return kw


def _reflection(pen, t, var, st, beam=None):
    """What the glass shows behind the 8th step (mirror-local coords, drawn larger than the pane)."""
    x0, y0, x1, y1 = PANE
    big = rect(x0 - 500, y0 - 400, x1 - x0 + 1000, y1 - y0 + 800)
    if var in ('queen', 'void', 'red', 'dark') or (var == 'flash' and st.v('mirror', t) == 'tilted'):
        base = ['#05070c', '#080c14', '#0b0d14']
        pen.linear(big, 0, y0, 0, y1, base)
        # the stairwell falling away inside the glass: faint treads converging under the 8th step
        for j in range(12):
            u = j / 12.0
            yy = 900 + 260 * u ** 0.8
            w = 420 * (1 - u) + 40
            pen.seg((575 - w, yy), (575 + w * 0.6, yy), 3 * (1 - u) + 0.8, '#3a1a24', int(150 * (1 - u)))
        red = 1.0 if var != 'dark' else 1.0
        if var == 'red': red = 1.6 + 0.4 * math.sin(t * 2.4)
        pen.radial(None, 575, 900, 520, [(0, GLOW, 70 * red), (0.4, '#5a0e1e', 60 * red), (1, '#000000', 0)], sy=0.6, clip=False)
        return
    if var == 'old_cabin':
        _old_cabin_refl(pen, t, st)
        return
    # ours at night: the dark cabin behind the viewer, Tess's lamp reflected
    pen.linear(big, 0, y0, 0, y1, ['#142232', '#1c2e3e', '#24384a', '#121c26'])
    for (bx, bw_) in ((360, 360), (1180, 420)):
        pen.fill(rect(bx, 60, bw_, 900), '#070c12', 200)
        pen.fill(rect(bx, 540, bw_, 70), '#22303c', 160)
        pen.fill(rect(bx, 250, bw_, 40), '#1a2632', 150)
    wr = rect(820, 140, 300, 240)
    pen.linear(wr, 0, 140, 0, 380, ['#3a5068', '#1c2c3c']); pen.seg((970, 140), (970, 380), 12, '#0a1018'); pen.line(wr, 14, '#0a1018')
    pen.radial(None, 970, 260, 420, [(0, MOON, 40), (1, MOON, 0)], clip=False)


def _old_cabin_refl(pen, t, st, floor_view=False):
    """The cabin as it was (theirs palette, 6:59 AM, morning) seen in the glass: made bunks, swimsuits dripping on the
    top-bunk rail, the door swinging in, wet footprints appearing to Noah's bunk (times from the shot's wet_footstep cues)."""
    x0, y0, x1, y1 = PANE
    pen.linear(rect(x0 - 500, y0 - 400, x1 - x0 + 1000, y1 - y0 + 800), 0, 100, 0, 1200, ['#c8c8c4', '#e2e0da', '#b4b6b4'])
    boards(pen, (-200, -600, 2200, 860), '#c6c4bc', False, 74, 31, 0.35, seam='#8f9394', seam_a=140, nails=False, hi='#f2f0ea')
    floor_persp(pen, -900, 2900, 1700, -200, 2200, 860, 22, '#a6a8a6', '#c8c6c0', 7, seam='#7f8b94')
    # door at the back (swings in during S074)
    sw = 0.0
    for c in st.sfx_cues('door_creak'):
        sw = ease_out_cubic(prog(t, c['t'], c['t'] + 1.6))
    if st.v('mirror', t) == 'tilted' and not st.sfx('door_creak') and st.t0 >= 163.5: sw = 1.0
    dr = rect(860, 300, 230, 560)
    pen.linear(dr, 0, 300, 0, 860, ['#fbf6e6', '#e8e2cc'] if sw > 0.05 else ['#8a8e90', '#7a7e80'])
    if sw > 0.05:
        pen.radial(None, 975, 900, 500, [(0, '#fff6dc', 140 * sw), (1, '#fff6dc', 0)], sy=0.3, clip=False)
        shaft(pen, [(860, 860), (1090, 860), (1300, 1500), (700, 1500)], '#fff6dc', int(90 * sw))
    dw = 230 * (1 - 0.82 * sw)
    door = poly([(860, 300), (860 + dw, 300 - 30 * sw), (860 + dw, 860 + 30 * sw), (860, 860)])
    pen.fill(door, '#9aa0a0'); pen.texture(door, 'wood', 0.3, 'overlay', 0.8, 90); pen.line(door, 3.5, '#4a4e50')
    pen.line(dr, 8, '#7f8b94')
    # bunks made, Noah's on the right
    bunk(pen, 160, 760, 900, 1.0, '#9a9a94', '#7f8b94', '#6a7680', True, True, '#7f8b94', lit=0.5, y_mat=(690, 780), y_top=(400, 440), posts_c='#a8a8a2')
    dipk = 0.0
    fp = st.sfx_cues('wet_footstep')
    if fp and t >= fp[-1]['t']: dipk = ease_out_cubic(prog(t, fp[-1]['t'], fp[-1]['t'] + 0.8))
    if st.t0 >= 172.2: dipk = max(dipk, ease_in_out(prog(t, st.t0 + 0.3, st.t0 + 1.2)))
    bunk(pen, 1180, 1900, 900, 1.0, '#9a9a94', '#7f8b94', '#6a7680', True, True, '#5a7a8a', lit=0.5, y_mat=(690, 780), y_top=(400, 440),
         posts_c='#a8a8a2', dip=(1500, 26 * dipk))
    swimsuits(pen, 1230, 1840, 440, t, 1.0, 1.0, 4, True)
    # wet footprints: door -> Noah's bunk
    prints = _footprint_track(st)
    for (tp, x, y, kind, ang, left) in prints:
        if t >= tp:
            k = ease_out_cubic(prog(t, tp, tp + 0.18))
            footprint(pen, x, y, 0.9 + 0.5 * (y - 860) / 800, kind, ang, k, left, '#6f7d88')
            if t - tp < 0.5: pen.radial(None, x, y, 60, [(0, '#ffffff', 90 * (1 - (t - tp) / 0.5)), (1, '#ffffff', 0)], sy=0.4, clip=False)


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
    dyn_refl = var in ('old_cabin', 'red') or st.sfx('wet_footstep') or st.ev('footprints')
    if dyn_refl: L.append(_live(refl_depth, refl, 'reflection', blur=0))
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
        pen.linear(pp, x0, y0, x1, y1, [(0, '#9fb6d8', 26), (0.45, '#ffffff', 10), (0.55, '#ffffff', 22), (1, '#9fb6d8', 8)])
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
            pen.radial(None, px, py, 70, [(0, '#c8d2dc', 26), (0.6, '#c8d2dc', 10), (1, '#c8d2dc', 0)], sy=0.6, clip=False)
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
            pen.radial(None, 700, 760, 260, [(0, '#dfe6ee', 120 * k), (0.6, '#dfe6ee', 60 * k), (1, '#dfe6ee', 0)], sy=0.8, clip=False)
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
    if animated: L.append(_live(0.995, steps, 'steps', blur=0))
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
    pen.linear(rect(-900, -700, 3800, 2600), 0, -700, 0, 1600, ['#05090d', '#0e1820'])
    # ceiling
    ceil = poly([(-900, -700), (2820, -700), (1860, 200), (60, 200)])
    pen.linear(ceil, 0, -700, 0, 200, ['#070c11', '#141f28']); pen.texture(ceil, 'wood', 0.35, 'overlay', 1.2)
    for i in range(9):
        u = i / 8
        pen.line(poly([(lerp(-900, 2820, u), -700), (lerp(60, 1860, u), 200)], False), 26, '#0a1016')
        pen.seg((lerp(-900, 2820, u) + 10, -700), (lerp(60, 1860, u) + 4, 200), 3, '#2a3a48', 120)
    # side walls
    for (pts, a) in (([(-900, -700), (60, 200), (60, 860), (-900, 1600)], 0), ([(1860, 200), (2820, -700), (2820, 1600), (1860, 860)], 1)):
        p = poly(pts)
        pen.linear(p, pts[0][0], 0, pts[1][0], 0, ['#0c141b', '#18242f'] if a == 0 else ['#18242f', '#0c141b'])
        pen.texture(p, 'wood', 0.4, 'overlay', 1.2, 90)
        for j in range(14):
            u = j / 13
            xa = lerp(pts[0][0], pts[1][0], u); ya0 = lerp(pts[0][1], pts[1][1], u); ya1 = lerp(pts[3][1], pts[2][1], u)
            pen.seg((xa, ya0), (xa, ya1), 2, '#05080b', 170)
    boards(pen, (60, 200, 1860, 860), wall, False, 64, 5, 0.5, var=0.12)
    pen.linear(rect(60, 200, 1800, 660), 0, 200, 0, 860, [(0, '#000000', 90), (0.4, '#000000', 0), (1, '#000000', 60)])
    pen.linear(rect(60, 200, 1800, 660), 60, 0, 1860, 0, [(0, '#000000', 110), (0.2, '#000000', 0), (0.8, '#000000', 0), (1, '#000000', 110)])
    pen.fill(rect(60, 840, 1800, 22), '#121a22'); pen.seg((60, 840), (1860, 840), 2, '#3a4a58', 120)
    # window hole + trim + sill
    hole = rect(780, 300, 320, 260)
    cv = pen.cv; pc = skia.Paint(AntiAlias=True); pc.setBlendMode(skia.BlendMode.kClear); cv.drawPath(hole, pc)
    pen.line(rect(770, 290, 340, 280), 22, '#2c3a46'); pen.line(rect(758, 278, 364, 304), 4)
    pen.seg((940, 300), (940, 560), 10, '#2c3a46'); pen.seg((780, 430), (1100, 430), 10, '#2c3a46')
    sill = rect(748, 556, 384, 26)
    pen.linear(sill, 0, 556, 0, 582, ['#4a5a68', '#26323e']); pen.texture(sill, 'wood', 0.5, 'overlay'); pen.line(sill, 3)
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
    pen.linear(fl, 0, 860, 0, 1600, [(0, '#8a98a6', 26), (1, '#8a98a6', 10)])


def _cabin7_bunks(pen, t, lit=0.4, mirror_under=True):
    bunk(pen, -80, 520, 880, 1.0, '#2e3a46', '#3e4c5a', '#28323e', True, False, lit=lit, y_mat=(690, 780), y_top=(420, 470))
    bunk(pen, 1260, 2000, 880, 1.0, '#2e3a46', '#3e4c5a', '#28323e', True, False, lit=lit, y_mat=(690, 780), y_top=(420, 470))
    if mirror_under:     # the towel bundle in the dark under Noah's bunk
        tb = smooth([(1380, 860), (1400, 830), (1700, 826), (1730, 858)], True, 0.6)
        towel_cloth(pen, tb, (1380, 826, 1730, 860), 0.5, 0, 3, 0.25)


def _window_out(pen, t, day=False):
    """Night outside Cabin 7's window: sky, moon glow, pines (static)."""
    pen.linear(rect(700, 220, 480, 420), 0, 220, 0, 560, ['#1a3048', '#2a4560', '#203648'])
    stars(pen, (700, 220, 1180, 420), 30, 5, 400)
    pen.radial(None, 1060, 300, 300, [(0, MOON, 90), (1, MOON, 0)], clip=False)
    treeline(pen, 640, 1240, 560, 200, 6, 13, '#0b1822', MOON, 60)


def _moon_shafts(pen, t):
    shaft(pen, [(780, 300), (1100, 300), (1500, 1300), (700, 1300)], MOON, 46, 4)
    pen.radial(None, 1040, 1060, 360, [(0, MOON, 40), (1, MOON, 0)], sy=0.3, clip=False)


def _cabin_light_layers(key, var, st, t_grow=None):
    """Variant light over cabin_now: doorway_glow (warm pale light + rays + haze from the doorway/mirror spot), red (lipstick
    red, slow pulse), phone_glow (faint red from the sill phone), after (flashlight on the floor raking the dust)."""
    L = []
    dx, dy = CAB_MIRROR[0], CAB_MIRROR[1]
    if var == 'doorway_glow':
        def glow(pen, t):
            pen.radial(None, dx, dy, 900, [(0, '#fff3dc', 150), (0.25, '#f3e3c4', 70), (1, '#f3e3c4', 0)], sy=0.75, clip=False)
            shaft(pen, [(dx - 70, dy + 190), (dx + 70, dy + 190), (dx + 520, 1400), (dx - 560, 1400)], '#fff0d0', 70, 5)
            for j in range(7):
                a0 = -0.9 + j * 0.3
                pen.linear(poly([(dx, dy), (dx + 1600 * math.cos(a0 + 1.57) - 30, dy + 1600 * math.sin(a0 + 1.57)),
                                 (dx + 1600 * math.cos(a0 + 1.57) + 30, dy + 1600 * math.sin(a0 + 1.57))]), dx, dy, dx, dy + 900,
                           [(0, '#fff6e4', 40), (1, '#fff6e4', 0)])
        grow = (lambda t: ease_in_out(prog(t, t_grow, t_grow + 2.2))) if t_grow else 1.0
        L.append(_cl(1.12, glow, 'doorway_light', key + ':dglow', NEAR, alpha=grow))
    if var == 'red':
        def redg(pen, t):
            pen.radial(None, dx, dy, 1100, [(0, GLOW, 120), (0.3, RED, 60), (1, RED, 0)], sy=0.7, clip=False)
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
            pen.linear(hole, 0, y0, 0, y1, ['#f6f2e8', '#e2ded2'] if var != 'red' else ['#ff8a96', '#c63449'])
            pen.radial(hole, 1190, 700, 160, [(0, '#ffffff', 200), (1, '#ffffff', 0)])
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
    pen.linear(body, 0, y - 16 * s, 0, y + 16 * s, ['#5a626a', '#2a3036', '#14181c']); pen.line(body, 3 * s)
    hd = rrect(x + 50 * s, y - 24 * s, 46 * s, 48 * s, 8 * s)
    pen.linear(hd, 0, y - 24 * s, 0, y + 24 * s, ['#6a727a', '#3a4046']); pen.line(hd, 3 * s)
    pen.fill(oval(x + 96 * s, y, 8 * s, 22 * s), '#fff8ee'); pen.radial(None, x + 100 * s, y, 70 * s, [(0, '#ffffff', 220), (1, CORE, 0)], clip=False)


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
    pen.radial(None, 960, 580, 1500, [(0, '#2a3e4e', 90), (1, '#2a3e4e', 0)], clip=False)
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
        pen.radial(None, ax, ay, 300, [(0, '#ffffff', 120 * k), (0.15, CORE, 90 * k), (0.5, FALL, 30 * k), (1, FALL, 0)], sy=0.85, clip=False)
        pen.radial(None, ax, ay, 700, [(0, CORE, 50 * k), (1, CORE, 0)], sy=0.06, clip=False)
    L.append(_live(0.99, glare, 'glare', blur=0))
    L.append(_live(0.9, lambda pen, t: motes(pen, t, (-200, -100, 2100, 1200), 110, 53, b, amb=0.05 if var != 'dark' else 0.0), 'dust', blur=0))
    if var == 'red':
        L.append(_live(0.98, lambda pen, t: pen.radial(None, 575, 860, 1100, [(0, GLOW, 50 + 20 * math.sin(t * 2.4)), (1, GLOW, 0)], sy=0.7, clip=False),
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
    def floor_live(pen, t):
        pen.cv.save(); pen.cv.translate(960, 540); pen.cv.scale(1.9, 1.9); pen.cv.translate(-1160, -1000)
        _old_cabin_refl(pen, t, st, True)
        pen.cv.restore()
    def sheen(pen, t):
        pen.linear(rect(-600, -400, 3100, 1900), -600, -400, 2500, 1500, [(0, '#ffffff', 0), (0.45, '#ffffff', 26), (0.5, '#ffffff', 8), (1, '#ffffff', 0)])
        pen.texture(rect(-600, -400, 3100, 1900), 'grunge', 0.1, 'screen', 2.0)
        pen.radial(None, 960, 540, 1500, [(0, '#000000', 0), (0.6, '#000000', 0), (1, '#05070c', 220)], sy=0.6, clip=False)
    L = [_live(1.6, floor_live, 'old_floor', blur=0), _cl(1.0, sheen, 'glass_sheen', 'ocf:sheen', NEAR)]
    return _sp('mirror/old_cabin_floor', L, {})
