"""sets_v2.py: the v2 sets (DIRECTION_V2 section 4) built on engine/room3d.py.

Imported at the end of sets.py, which it extends: every v2 (set, view) registers in sets.VIEWS with @view, so
`sets.build_shot(shot)` builds v1 and v2 views alike. SETS.md documents the views, variants, anchors and the geography.

The cabins are ONE model (`cabin_scene`): Cabin 7 tonight (OURS) and, flipped left-right (`Xf.flip_x`, text kept readable),
the other side (THEIRS: 14 years younger, golden, frozen at 6:59 AM, with the stairs along the back wall up to the doorway).
Every angle is a `Cam3`; the glass shows a true reflection of the same model (`Xf.reflect_z`). Units: metres.

Geography (top view, OURS; x right from the left wall, z from the door wall to the back wall):
    back wall z = 6.4: left bunk (along the left wall, x 0.08-0.92) | clock x 1.15 | window x 1.45-2.2 | MIRROR x 2.39-2.94 |
                       calendar, pennant | Noah's bunk (along the right wall, x 4.68-5.52) with the 6 cubbies above it
    front wall z = 0:  door x 3.55-4.45 (padlock on the hasp outside), rules sign + broom + mattress stack at front-left
    THEIRS = x -> 5.6 - x: Noah's bunk on the left, the 8 steps rising along the back wall to the doorway (x 2.66-3.21,
    1.8 m up), window, clock 6:59, other bunk; their floor is 1.8 m below our floor.
"""
import math
import numpy as np
import skia
import sets as S1
from sets import (SetPiece, Anchor, St, Beam, VIEWS, view, _sp, _cl, _live, _R, _L, _h, _lt, _dk, _clip, _unclip, _blob,
                  _tx, _ttext, motes, fireflies, mist, moths, stars, twinkle, moon, pine, treeline, draw_beam, hot_spot,
                  aim_fn, wall_clock, lipstick_steps, eighth_line, towel_cloth, phone_prop, swimsuits, footprint, candy,
                  gingham, bell, crate, sprinkler, padlock, lantern, sneaker, _steps_state, _clock_sec, clock_ours,
                  clock_theirs, FRAME, NEAR, STEP_XY, EIGHTH, PANE, FW, MPIV, RED, RED_HI, RED_DK, GLOW, CORE, FALL)
from engine.core import (Pen, col, mix, rgb, poly, smooth, rect, rrect, oval, union, minus, moved, clamp, lerp, prog, ease,
                         ease_in_out, ease_out_cubic, ease_in_cubic, ease_out_back, noise1, hash01, text, text_width, LINE)
from engine.scene import Layer
from engine.room3d import Cam3, Scene3, Xf, v3, norm, ID, clip_poly_near, draw_plane

# v2 variants -> the 4.8 grade presets (a shot's own `grade` / `look` wins)
S1.DEFAULT_GRADE.update({'night': 'night_v2', 'doorway_glow': 'night_v2', 'red': 'climax_v2', 'after': 'ending_v2',
                         'phone_glow': 'ending_v2', 'dawn': 'dawn_v2', 'dawn_queen': 'dawn_queen_v2', 'dawn_break': 'dawn_break_v2',
                         'stairs': 'stairs_v2', 'sepia_day': 'memory_sepia', 'sepia_night': 'memory_sepia',
                         'sepia_morning': 'memory_sepia', 'bell_hit': 'night_v2'})

# ====================================================================== dimensions (metres)
W, D = 5.6, 6.4                 # Cabin 7 interior: width (x), depth (z: door wall 0 -> back wall 6.4)
HW, HR = 2.6, 3.9               # wall top, ridge (the ridge runs along z at x = W / 2)
MIR = (2.39, 2.94)              # mirror / doorway spot on the back wall (x); glass 1.48 x 0.43 in a 6 cm frame
MIR_H = 1.60                    # mirror height (full length, standing on the floor, leaning back 7.8 deg)
MIR_LEAN = 0.22                 # its foot stands 0.22 m out from the back wall
WIN = (1.45, 2.20, 0.95, 1.90)  # window x0, x1, sill y, top y
CLOCK = (1.15, 2.12, 0.15)      # x, y, r
DOOR = (3.55, 4.45, 2.05)       # front door x0, x1, height
LBUNK = (0.08, 0.92, 4.25, 6.30)   # left bunk x0, x1, z0, z1 (OURS)
NBUNK = (4.68, 5.52, 4.25, 6.30)   # Noah's bunk (OURS)
CUBBY = (4.55, 6.15, 1.92, 2.48)   # cubby shelf on the right wall: z0, z1, y0, y1 (depth 0.34)
B_LOW, B_TOP = 0.46, 1.52          # mattress top heights (lower, upper bunk)
DROP = 1.8                          # THEIRS floor is DROP below ours; their doorway sill is DROP up their back wall
TREAD, RISE = 0.24, 0.20            # stairs (THEIRS run along the back wall; 8 treads, tread 1 = the landing at the doorway)


def flip(x): return W - x


# ====================================================================== palettes per world / variant
PAL = {
    'night': dict(wall='#4a4f8e', wall_dk='#2e3166', wall_lt='#6a70b8', seam='#1d1f44', rail='#3a3d72',
                  floor='#5a5688', floor_dk='#3a3762', floor_lt='#7a76b2', floor_seam='#25223f', dust='#9a96c8',
                  roof='#2a2c58', roof_dk='#1a1b40', beam='#3c3e74', beam_lt='#7478c0',
                  wood='#7a6488', wood_dk='#4e3f66', wood_lt='#a08ab8', mat='#9aa0d0', mat_st='#5c6198', mat_dk='#5a5f92',
                  paint='#b9bdd8', paint_dk='#8a8eb0', metal='#8a90b4', sky0='#2c3a7c', sky1='#5a5fa8', moon='#cfd8ff',
                  key='#9fa8ff', warm='#ffd58a', pool='#f0a84e', outline='#14152e', paper='#cfd0e4', tape='#cdbf7a',
                  red_glint=0.0, glow_door=0.0, red=0.0),
    'theirs': dict(wall='#d9a96a', wall_dk='#b07c46', wall_lt='#f0c88a', seam='#7a4e2a', rail='#c48f55',
                   floor='#c99660', floor_dk='#a8763f', floor_lt='#e6b678', floor_seam='#7a5030', dust='#f2d8a8',
                   roof='#a9743f', roof_dk='#875a30', beam='#b8834c', beam_lt='#e3b070',
                   wood='#b98650', wood_dk='#8c5e34', wood_lt='#dcae74', mat='#e9e2cf', mat_st='#c9b48e', mat_dk='#b5a07a',
                   paint='#f4ead6', paint_dk='#d4c6a8', metal='#b9b2a4', sky0='#f6b9a0', sky1='#ffe7c2', moon='#fff2d0',
                   key='#ffe2a8', warm='#ffe2a8', pool='#ffd59a', outline='#3a2414', paper='#f8f0dc', tape='#e8d79a',
                   red_glint=0.0, glow_door=0.0, red=0.0),
}
PAL['red'] = dict(PAL['night'], wall='#57183d', wall_dk='#2e0a20', wall_lt='#8a2a5a', seam='#1a0610', rail='#45122f',
                  floor='#4a1430', floor_dk='#2a0818', floor_lt='#7a2448', floor_seam='#14040c', dust='#c05a7e',
                  roof='#2a0a1c', roof_dk='#1a0610', beam='#3a0f28', beam_lt='#ae3a6a',
                  wood='#6a2244', wood_dk='#3e1028', wood_lt='#a03a66', mat='#9a4a6e', mat_st='#6a2a4a', mat_dk='#5a2240',
                  paint='#d48aa6', paint_dk='#9a5070', metal='#a0607e', sky0='#2a0a2a', sky1='#5a1640', moon='#ff9ab4',
                  key='#ff2d55', warm='#ff5a7a', pool='#ff2d55', outline='#12030a', paper='#d8a0b4', tape='#c08070', red=1.0)
PAL['after'] = dict(PAL['night'])
PAL['theirs_queen'] = dict(PAL['theirs'])
PAL['theirs_break'] = dict(PAL['theirs'], wall='#c99a62', wall_dk='#9a6a3c', floor='#b88654', red=0.25)

VAR_PAL = {'night': 'night', 'flash': 'night', 'doorway_glow': 'night', 'phone_glow': 'after', 'after': 'after', 'red': 'red',
           'dawn': 'theirs', 'dawn_queen': 'theirs_queen', 'dawn_break': 'theirs_break', 'stairs': 'night'}


# ====================================================================== plane materials (all in plane cm)
def _planks(pen, w, h, P, bw=16.0, seed=0, vertical=True, lit=None, seam_w=1.0, grain=0.22, nails=True, knots=0.25,
            base=None, dk=None, lt=None, seam=None, off=0.0, ends=0.0):
    """Board wall/floor in plane cm: tone-varied boards, grain, seams with a lit edge, nails, knots. lit(pen, w, h) adds
    the light gradients over the boards."""
    base = base or P['wall']; dk = dk or P['wall_dk']; lt = lt or P['wall_lt']; seam = seam or P['seam']
    r = rect(0, 0, w, h)
    pen.fill(r, base)
    L = w if vertical else h
    n = int(math.ceil((L + off) / bw)) + 1
    for i in range(n):
        a0 = i * bw - off
        tone = mix(base, dk if _h(i, seed) < 0.5 else lt, 0.10 + 0.22 * _h(i, seed + 1))
        rr = rect(a0, 0, bw, h) if vertical else rect(0, a0, w, bw)
        pen.fill(rr, tone)
    if lit: lit(pen, w, h)
    pen.texture(r, 'wood', grain, 'overlay', 0.22, 90 if vertical else 0)
    for i in range(n + 1):
        a0 = i * bw - off
        if vertical:
            pen.seg((a0, 0), (a0, h), seam_w, seam, 210); pen.seg((a0 + seam_w * 0.9, 0), (a0 + seam_w * 0.9, h), seam_w * 0.5, lt, 70)
        else:
            pen.seg((0, a0), (w, a0), seam_w, seam, 210); pen.seg((0, a0 + seam_w * 0.9), (w, a0 + seam_w * 0.9), seam_w * 0.5, lt, 70)
        if ends and i < n:
            for j in range(int(ends)):
                v = _h(i * 3 + j, seed + 5)
                if vertical: pen.seg((a0, v * h), (a0 + bw, v * h), seam_w * 0.8, seam, 170)
                else: pen.seg((v * w, a0), (v * w, a0 + bw), seam_w * 0.8, seam, 170)
    for i in range(int(n * knots)):
        kx = _h(i, seed + 20) * w; ky = _h(i, seed + 21) * h
        rr = 0.8 + 1.2 * _h(i, seed + 22)
        pen.fill(oval(kx, ky, rr * (1.0 if vertical else 2.4), rr * (2.4 if vertical else 1.0)), dk, 150)
    if nails:
        for i in range(n):
            for f in ((0.06, 0.48, 0.92) if vertical else (0.1, 0.9)):
                if vertical: nx, ny = i * bw - off + bw * 0.5, f * h
                else: nx, ny = f * w, i * bw - off + bw * 0.5
                pen.fill(oval(nx, ny, 0.55), '#000000', 140)


def _vgrad(pen, w, h, stops):
    _L(pen, rect(0, 0, w, h), 0, 0, 0, h, stops)


def _hgrad(pen, w, h, stops):
    _L(pen, rect(0, 0, w, h), 0, 0, w, 0, stops)


def _pool(pen, x, y, rx, ry, c, a, core=None):
    """Light pool (radial, plane cm)."""
    _R(pen, None, x, y, rx, [(0, c, a), (0.45, c, a * 0.55), (1, c, 0)], sy=ry / rx, clip=False)
    if core: _R(pen, None, x, y, rx * 0.4, [(0, core, a * 0.8), (1, core, 0)], sy=ry / rx, clip=False)


def _sign_text(pen, s, x, y, size, c, weight=800, a=255, spacing=0.0, align='center'):
    text(pen.cv, s, x, y, weight, size, c, a, spacing, align)


# ====================================================================== the cabin model
class CabinCtx:
    """What the cabin model is built for: side ('ours' / 'theirs'), palette, prop states at a time, var."""

    def __init__(self, side, var, st=None, t=0.0):
        self.side, self.var, self.st, self.t = side, var, st, t
        self.P = PAL[VAR_PAL.get(var, 'night' if side == 'ours' else 'theirs')]
        self.ours = side == "ours"
        self.refl_scene = None

    def prop(self, k, default=None):
        if self.st is None: return default
        v = self.st.v(k, self.t)
        return default if v is None else v

    @property
    def mirror_state(self):
        m = str(self.prop('mirror', 'glass'))
        d = str(self.prop('doorway', 'none'))
        if m.startswith('glass returning'): return 'glass'
        if d.startswith('gold') or d.startswith('navy') or d.startswith('red') or m.startswith('doorway'): return 'doorway'
        if m.startswith('wrapped') or m == 'not_found' or m.startswith('unwrapped'): return 'absent'
        if m.startswith('towel') or 'towel_over' in m: return 'towel'
        if m.startswith('covered'): return 'covered'
        if m.startswith('dark'): return 'dark'
        return 'glass'


def _mk_strips(sc, O, U, V, w, h, draw, n, along_t=True, order=0, name='', tag=None, two_sided=True):
    """A plane split into n strips (for parallax bands); the drawing is continuous across strips."""
    O, U, V = v3(O), norm(U), norm(V)
    for i in range(n):
        if along_t:
            t0, t1 = h * i / n, h * (i + 1) / n
            t1e = min(h, t1 + h * 0.02)

            def d(pen, ww, hh, t0=t0, h_=h):
                pen.cv.translate(0, -t0); draw(pen, w, h_)
            sc.plane(O + V * (t0 / 100), U, V, w, t1e - t0, d, order, '%s%d' % (name, i), tag, two_sided)
        else:
            s0, s1 = w * i / n, w * (i + 1) / n
            s1e = min(w, s1 + w * 0.02)

            def d(pen, ww, hh, s0=s0, w_=w):
                pen.cv.translate(-s0, 0); draw(pen, w_, h)
            sc.plane(O + U * (s0 / 100), U, V, s1e - s0, h, d, order, '%s%d' % (name, i), tag, two_sided)


def _obox(sc, P0, P1, w, h, faces, order=0, name='', tag=None, up=(0, 1, 0)):
    """An oriented box along the segment P0 -> P1 with cross-section w (sideways) x h (along `up` projected): rafters,
    handrails, posts at an angle. faces: {'top','bottom','side_a','side_b','end'} colours or draw fns ('all' default)."""
    P0, P1 = v3(P0), v3(P1)
    a = P1 - P0; L = np.linalg.norm(a); a = a / L
    u = v3(up); u = norm(u - a * np.dot(u, a))
    s = norm(np.cross(u, a))
    allc = faces.get('all')
    hw, hh = w / 2, h / 2
    # four long faces (as planes from P0 along a), plus the two ends
    defs = [('top', P0 + u * hh - s * hw, s, a, w, L, u), ('bottom', P0 - u * hh + s * hw, -s, a, w, L, -u),
            ('side_a', P0 + s * hw + u * hh, -u, a, h, L, s), ('side_b', P0 - s * hw - u * hh, u, a, h, L, -s)]
    for nm, O, U_, V_, ww, ll, nrm in defs:
        f = faces.get(nm, allc)
        if f is None: continue
        cen = O + U_ * ww / 2 + V_ * ll / 2

        def drw(pen, w_, h_, f=f):
            if callable(f): f(pen, w_, h_)
            else: pen.fill(rect(0, 0, w_, h_), f)
        sc.plane(O, U_, V_, ww * 100, ll * 100, drw, order, name + nm, tag, two_sided=False, centre=cen)
    for nm, O, nrm in (('end0', P0, -a), ('end1', P1, a)):
        f = faces.get('end', allc)
        if f is None: continue
        O2 = O - s * hw + u * hh

        def drw(pen, w_, h_, f=f):
            pen.fill(rect(0, 0, w_, h_), f if not callable(f) else '#000000')
        U2, V2 = (s, -u) if nm == 'end1' else (-s, -u)
        O3 = O2 if nm == 'end1' else O + s * hw + u * hh
        sc.plane(O3, U2, V2, w * 100, h * 100, drw, order, name + nm, tag, two_sided=False)


def _shade(c, k):
    """k < 0 darker, > 0 lighter."""
    return _dk(c, -k) if k < 0 else _lt(c, k)


def cabin_scene(cx, parts=('shell', 'props')):
    """The Cabin 7 model (OURS coordinates; THEIRS is rendered through Xf.flip_x). Returns (Scene3, info)."""
    P = cx.P; ours = cx.ours
    sc = Scene3()
    info = {}
    mstate = cx.mirror_state if ours else 'doorway_theirs'
    # ---------------------------------------------------------------- shell
    wall_tag = 'shell'

    def back_wall(pen, w, h):
        # plane: origin (0, HR, D) U +x, V -y; w 560, h 390; gable clip
        gable = poly([(0, (HR - HW) * 100), (W * 50, 0), (W * 100, (HR - HW) * 100), (W * 100, HR * 100), (0, HR * 100)])
        pen.cv.clipPath(gable, skia.ClipOp.kIntersect, True)

        def lit(pen, w, h):
            _vgrad(pen, w, h, [(0, P['wall_dk'], 255), (0.35, P['wall'], 0), (0.8, P['wall'], 0), (1, P['wall_dk'], 200)])
            if ours:
                # moon glow around the window, darker gable corners
                _pool(pen, (WIN[0] + WIN[1]) * 50, (HR - (WIN[2] + WIN[3]) / 2) * 100, 300, 230, P['key'], 95)
                _pool(pen, (WIN[0] + WIN[1]) * 50, (HR - (WIN[2] + WIN[3]) / 2) * 100, 120, 110, '#c8d0ff', 60)
                _hgrad(pen, w, h, [(0, '#000000', 70), (0.15, '#000000', 0), (0.85, '#000000', 0), (1, '#000000', 70)])
            else:
                _pool(pen, (flip(WIN[0]) + flip(WIN[1])) * 50, (HR - (WIN[2] + WIN[3]) / 2) * 100, 300, 230, P['warm'], 110)
        _planks(pen, w, h, P, 17.0, 3, True, lit, 0.9)
        # top plate / rail at wall-top height and a chair rail
        pen.fill(rect(0, (HR - HW) * 100 - 6, w, 8), P['rail']); pen.seg((0, (HR - HW) * 100 + 2), (w, (HR - HW) * 100 + 2), 0.8, P['seam'], 200)
        pen.fill(rect(0, (HR - 0.92) * 100, w, 5), P['rail'], 230)
        pen.seg((0, (HR - 0.92) * 100 + 5), (w, (HR - 0.92) * 100 + 5), 0.8, P['seam'], 200)
        pen.seg((0, (HR - 0.92) * 100), (w, (HR - 0.92) * 100), 0.6, P['wall_lt'], 120)
        # skirting
        pen.fill(rect(0, h - 9, w, 9), P['wall_dk'])
        pen.seg((0, h - 9), (w, h - 9), 0.8, P['wall_lt'], 90)

    def win_hole():
        x0, x1, y0, y1 = WIN
        return rect(x0 * 100, (HR - y1) * 100, (x1 - x0) * 100, (y1 - y0) * 100)

    def back_wall_holed(pen, w, h):
        hole = win_hole()
        pen.cv.clipPath(hole, skia.ClipOp.kDifference, True)
        if ours and mstate == 'doorway':
            pen.cv.clipPath(_doorway_hole_cm(), skia.ClipOp.kDifference, True)
        if not ours:
            pen.cv.clipPath(_doorway_hole_cm(DROP), skia.ClipOp.kDifference, True)
        back_wall(pen, w, h)

    sc.plane((0, HR, D), (1, 0, 0), (0, -1, 0), W * 100, HR * 100, back_wall_holed, -100, 'back_wall', wall_tag)

    def side_wall(pen, w, h, left=True):
        def lit(pen, w, h):
            _vgrad(pen, w, h, [(0, P['wall_dk'], 220), (0.3, P['wall'], 0), (0.85, P['wall'], 0), (1, P['wall_dk'], 200)])
            # light from the back (window side) on the near end: horizontal falloff toward the door
            _hgrad(pen, w, h, [(0, P['wall_lt'], 70 if ours else 120), (0.6, P['wall_lt'], 0)] if left else
                   [(0.4, P['wall_lt'], 0), (1, P['wall_lt'], 70 if ours else 120)])
        _planks(pen, w, h, P, 17.0, 5 if left else 6, True, lit, 0.9)
        pen.fill(rect(0, 0, w, 8), P['rail']); pen.fill(rect(0, h - 9, w, 9), P['wall_dk'])
        pen.fill(rect(0, (HW - 0.92) * 100, w, 5), P['rail'], 230)
        pen.seg((0, (HW - 0.92) * 100 + 5), (w, (HW - 0.92) * 100 + 5), 0.8, P['seam'], 200)

    # left wall: inner face seen from inside (looking -x): origin (0, HW, 0), U +z, V -y
    _mk_strips(sc, (0, HW, 0), (0, 0, 1), (0, -1, 0), D * 100, HW * 100, lambda p, w, h: side_wall(p, w, h, True), 4, False,
               -100, 'lwall', wall_tag)
    _mk_strips(sc, (W, HW, D), (0, 0, -1), (0, -1, 0), D * 100, HW * 100, lambda p, w, h: side_wall(p, w, h, False), 4, False,
               -100, 'rwall', wall_tag)

    # front wall (door wall) seen from inside: origin (W, HR, 0), U -x, V -y
    def front_wall(pen, w, h):
        door = rect((W - DOOR[1]) * 100, (HR - DOOR[2]) * 100, (DOOR[1] - DOOR[0]) * 100, DOOR[2] * 100)
        pen.cv.clipPath(door, skia.ClipOp.kDifference, True)
        back_wall(pen, w, h)
        # door casing
        x0, x1 = (W - DOOR[1]) * 100, (W - DOOR[0]) * 100; yt = (HR - DOOR[2]) * 100
        for r_ in (rect(x0 - 9, yt - 9, 9, DOOR[2] * 100 + 9), rect(x1, yt - 9, 9, DOOR[2] * 100 + 9), rect(x0 - 9, yt - 9, x1 - x0 + 18, 9)):
            pen.fill(r_, P['wood']); pen.line(r_, 0.8, P['outline'], 160)
        if ours:
            # CABIN RULES card is on the left wall; here: hooks and an old fire-escape card
            _sign_text(pen, 'EXIT', (x0 + x1) / 2, yt - 16, 7, '#d9e0ff' if ours else '#7a3a20', 900, 200)
    sc.plane((W, HR, 0), (-1, 0, 0), (0, -1, 0), W * 100, HR * 100, front_wall, -100, 'front_wall', wall_tag)

    # floor (strips along z): origin (0, 0, 0), U +x, V +z
    def floor(pen, w, h):
        r = rect(0, 0, w, h)
        pen.fill(r, P['floor'])
        n = int(w / 14) + 1
        for i in range(n):
            tone = mix(P['floor'], P['floor_dk'] if _h(i, 41) < 0.5 else P['floor_lt'], 0.12 + 0.25 * _h(i, 42))
            pen.fill(rect(i * 14, 0, 14, h), tone)
        # light: brighter toward the back (window side), darker at the walls
        _hgrad(pen, w, h, [(0, P['floor_dk'], 200), (0.18, P['floor_dk'], 0), (0.82, P['floor_dk'], 0), (1, P['floor_dk'], 200)])
        _vgrad(pen, w, h, [(0, P['floor_dk'], 150), (0.5, P['floor_dk'], 0), (1, P['floor_lt'], 40)])
        pen.texture(r, 'wood', 0.2, 'overlay', 0.22, 90)
        for i in range(n + 1):
            pen.seg((i * 14, 0), (i * 14, h), 0.9, P['floor_seam'], 220)
            pen.seg((i * 14 + 0.8, 0), (i * 14 + 0.8, h), 0.45, P['floor_lt'], 70)
            for j in range(3):                   # staggered butt joints
                y = (_h(i * 3 + j, 43) + j) / 3 * h
                pen.seg((i * 14, y), (i * 14 + 14, y), 0.8, P['floor_seam'], 190)
                pen.fill(oval(i * 14 + 3, y - 2.5, 0.5), '#000000', 140); pen.fill(oval(i * 14 + 11, y - 2.5, 0.5), '#000000', 140)
        # ambient occlusion: wall junctions and contact shadows under the furniture (plane cm: x, z)
        _vgrad(pen, w, h, [(0.0, '#000000', 90), (0.06, '#000000', 0), (0.92, '#000000', 0), (1.0, '#000000', 110)])
        for (a, b, c, d) in (LBUNK, NBUNK):
            for gx in (0, 1):
                pass
            sh = rrect(a * 100 - 6, c * 100 - 6, (b - a) * 100 + 12, (d - c) * 100 + 12, 10)
            pen.fill(sh, '#000000', 60, blur=8)
            pen.fill(rrect(a * 100 + 4, c * 100 + 4, (b - a) * 100 - 8, (d - c) * 100 - 8, 6), '#000000', 70)
        if ours:
            pen.fill(rrect(10, 33, 100, 196, 8), '#000000', 70)          # mattress stack
            if cx.mirror_state not in ('absent',):
                pen.fill(rrect(MIR[0] * 100 - 4, (D - MIR_LEAN - 0.04) * 100, (MIR[1] - MIR[0]) * 100 + 8, (MIR_LEAN + 0.04) * 100, 4), '#000000', 110)
        if ours:
            # the dust film: smooth, pale, thicker along the walls; scuffs only near the door
            pen.texture(r, 'grunge', 0.22, 'screen', 0.4)
            _hgrad(pen, w, h, [(0, P['dust'], 70), (0.15, P['dust'], 0), (0.85, P['dust'], 0), (1, P['dust'], 70)])
            # the moon patch through the window (projected window onto the floor along the moonlight)
            for poly_, a in _moon_patch_floor():
                pen.fill(poly(poly_), P['key'], int(a * 1.6))
                pen.fill(poly(poly_), '#e8ecff', int(a * 0.5))
        else:
            _hgrad(pen, w, h, [(0, P['floor_dk'], 90), (0.2, P['floor_dk'], 0)])
            for poly_, a in _moon_patch_floor(theirs=True):
                pen.fill(poly(poly_), P['warm'], int(a * 1.4))
    _mk_strips(sc, (0, 0, 0), (1, 0, 0), (0, 0, 1), W * 100, D * 100, floor, 5, True, -120, 'floor', wall_tag)

    # roof slopes (inner faces) with boards across, and the rafters / tie beams / ridge
    slope = math.hypot(W / 2, HR - HW)

    def roof(pen, w, h):
        _planks(pen, w, h, P, 20.0, 9, False, lambda p, w_, h_: _hgrad(p, w_, h_, [(0, P['roof_dk'], 255), (1, P['roof'], 0)]),
                0.8, 0.18, False, 0.1, P['roof'], P['roof_dk'], P['beam'], P['roof_dk'])
    _mk_strips(sc, (0, HW, D), (W / 2 / slope, (HR - HW) / slope, 0), (0, 0, -1), slope * 100, D * 100, roof, 4, True, -110,
               'roofL', wall_tag)
    _mk_strips(sc, (W, HW, 0), (-W / 2 / slope, (HR - HW) / slope, 0), (0, 0, 1), slope * 100, D * 100, roof, 4, True, -110,
               'roofR', wall_tag)
    bm = dict(top=P['beam'], bottom=P['beam'], side_a=P['beam_lt'], side_b=P['roof_dk'], end=P['roof_dk'])
    for z in np.arange(0.4, D, 0.8):
        _obox(sc, (0.0, HW, z), (W / 2, HR - 0.04, z), 0.06, 0.14, bm, 0, 'raftL', 'beams', up=(0, 0, 1))
        _obox(sc, (W, HW, z), (W / 2, HR - 0.04, z), 0.06, 0.14, bm, 0, 'raftR', 'beams', up=(0, 0, 1))
    for z in (1.6, 3.2, 4.8):
        sc.box(0.0, HW - 0.14, z - 0.05, W, HW, z + 0.05, dict(bottom=P['beam'], front=P['beam_lt'], back=P['roof_dk'],
                                                                 top=P['beam']), 0, 'tie', 'beams', P['outline'], 0.5)
    sc.box(W / 2 - 0.05, HR - 0.18, 0, W / 2 + 0.05, HR - 0.02, D, dict(bottom=P['beam'], left=P['beam_lt'], right=P['roof_dk']),
           0, 'ridge', 'beams')
    _cabin_lights(sc, cx)
    _outside_front(sc, cx)
    if 'props' in parts:
        _cabin_props(sc, cx, info)
    return sc, info


def _cabin_lights(sc, cx):
    """Point lights washed over every surface (model space = OURS coords; THEIRS flips with the room)."""
    P = cx.P; var = cx.var
    wx = (WIN[0] + WIN[1]) / 2
    if cx.ours:
        moon_a = 0.6 if var in ('after', 'phone_glow') else (0.35 if var == 'red' else 1.0)
        sc.light((wx, 1.45, D - 0.25), '#9fa8ff', 95 * moon_a, 1.1, name='moon_window')
        sc.light((wx + 0.45, 0.25, 4.6), '#aab4ff', 55 * moon_a, 1.1, name='moon_floor')
        sc.light((4.0, 1.3, 0.6), '#6a72c8', 45 * moon_a, 1.5, name='door_fill')
        sc.light((2.8, 2.6, 3.2), '#5a5fa8', 40 * moon_a, 2.6, name='ambient')
        if cx.st is not None and _flash_on(cx.st, cx.t) and var in ('night', 'flash', 'doorway_glow') and cx.mirror_state != 'absent':
            sc.light((2.66, 0.85, 5.75), '#ffd58a', 55, 0.8, name='beam_bounce')
        if var == 'doorway_glow' or (cx.mirror_state == 'doorway' and var not in ('red',)):
            sc.light((2.66, 0.75, 6.05), '#ffcf8a', 150, 1.25, name='doorway_gold')
            sc.light((2.66, 0.1, 5.2), '#ffb86a', 90, 0.9, name='doorway_floor')
        if var == 'red':
            sc.light((2.66, 0.8, 6.0), '#ff2d55', 190, 1.6, name='red_pour')
            sc.light((2.66, 0.1, 4.8), '#c2185b', 140, 1.4, name='red_floor')
            sc.light((2.8, 2.4, 3.0), '#ae3a6a', 90, 2.5, name='red_fill')
        if var in ('after', 'phone_glow'):
            sc.light((2.3, 0.18, 3.3), '#ffd58a', 140, 1.0, name='flashlight_floor')
            sc.light((3.4, 0.4, 5.0), '#f0a84e', 70, 1.2, name='pool_bounce')
        if var == 'phone_glow':
            sc.light((2.2, 1.0, 4.4), '#c8d8ff', 70, 0.7, name='phone')
    else:
        sun = 0.75 if var == 'dawn_break' else 1.0
        sc.light((wx, 1.5, D - 0.3), '#ffe2a8', 95 * sun, 1.15, name='sun_window')
        sc.light((wx - 0.5, 0.2, 4.4), '#ffd59a', 80 * sun, 1.2, name='sun_floor')
        sc.light((2.8, 2.3, 3.0), '#ffcf8a', 55 * sun, 3.0, name='warm_fill')
        sc.light((2.66, 2.6, D - 0.2), '#9fa8ff', 55, 0.7, name='doorway_blue')
        if var == 'dawn_break':
            sc.light((2.66, 2.4, 5.6), '#ff3b5c', 90, 1.6, name='red_leak')


def _outside_front(sc, cx):
    """What the open front door shows: the moonlit path, the pines and (OURS) the mess hall 40 m away with its porch
    light; (THEIRS) the wash house in early sun."""
    P = cx.P; ours = cx.ours
    x0, x1, h = DOOR

    def scene(pen, w, h_):
        if ours:
            _vgrad(pen, w, h_, [P['sky0'], P['sky1'], '#6a70b0'])
            for i in range(14):
                pine(pen, w * (i + 0.4 * _h(i, 13)) / 13, h_ * 0.78, h_ * (0.35 + 0.3 * _h(i, 14)), i + 40, '#1a1f48', P['key'], 50, 0, 8, 0.4)
            # the mess hall across the path: dark lodge, warm porch light, the crate
            lx = w * 0.55
            pen.fill(rect(lx - 160, h_ * 0.56, 320, h_ * 0.22), '#23264e'); pen.line(rect(lx - 160, h_ * 0.56, 320, h_ * 0.22), 1.2, '#0e0f26')
            pen.fill(poly([(lx - 190, h_ * 0.57), (lx, h_ * 0.44), (lx + 190, h_ * 0.57)]), '#1a1c40')
            _R(pen, None, lx - 60, h_ * 0.63, 90, [(0, '#ffb84d', 200), (0.3, '#ffb84d', 70), (1, '#ffb84d', 0)], clip=False)
            pen.fill(oval(lx - 60, h_ * 0.63, 5), '#fff3d6')
            pen.fill(rect(lx + 30, h_ * 0.71, 40, 18), '#4a3a3a')
            pen.fill(rect(0, h_ * 0.78, w, h_ * 0.22), '#2a2e5a')
            _R(pen, None, w * 0.5, h_ * 0.9, w * 0.4, [(0, '#5a62a8', 120), (1, '#5a62a8', 0)], sy=0.3, clip=False)
        else:
            _vgrad(pen, w, h_, [P['sky0'], P['sky1'], '#fff0d0'])
            for i in range(14):
                pine(pen, w * (i + 0.4 * _h(i, 13)) / 13, h_ * 0.78, h_ * (0.3 + 0.3 * _h(i, 14)), i + 40, '#8a9a70', '#ffe6b0', 80, 0, 8, 0.4)
            pen.fill(rect(w * 0.4, h_ * 0.6, 160, h_ * 0.18), '#d8b080'); pen.line(rect(w * 0.4, h_ * 0.6, 160, h_ * 0.18), 1.0, '#6a4a2a')
            _sign_text(pen, 'WASH HOUSE', w * 0.4 + 80, h_ * 0.64, 10, '#4a2a10', 900)
            pen.fill(rect(0, h_ * 0.78, w, h_ * 0.22), '#b8b478')
    sc.plane((x0 - 3.0, 5.5, -9.0), (1, 0, 0), (0, -1, 0), 900, 650, scene, -200, 'outside_front', 'shell')

    def ground(pen, w, h_):
        pen.fill(rect(0, 0, w, h_), '#2c3060' if ours else '#c8b47a')
        pen.texture(rect(0, 0, w, h_), 'asphalt', 0.3, 'overlay', 0.3)
        pen.fill(rect(w * 0.42, 0, w * 0.16, h_), '#3a3e70' if ours else '#d8c48a')
    sc.plane((x0 - 3.0, -0.25, 0.0), (1, 0, 0), (0, 0, -1), 900, 900, ground, -190, 'ground_front', 'shell')
    # the porch step outside the door
    sc.box(x0 - 0.3, -0.25, -0.5, x1 + 0.3, -0.02, 0.0, dict(top=P['wood'], front=P['wood_dk'], all=P['wood_dk']), -150, 'step', 'shell',
           P['outline'], 0.6)


def _doorway_hole_cm(y0=0.0):
    """The doorway opening in the back wall plane coords (cm, origin top-left at y = HR): the mirror's glass area
    (y0 = DROP for THEIRS, where the doorway is 1.8 m up the wall)."""
    gx0, gx1 = MIR[0] + 0.06, MIR[1] - 0.06
    return rect(gx0 * 100, (HR - (y0 + MIR_H - 0.06)) * 100, (gx1 - gx0) * 100, (MIR_H - 0.12) * 100)


def _moon_patch_floor(theirs=False):
    """Window projected onto the floor along the moonlight (plane cm, floor coords x, z). Returns [(poly, alpha)]."""
    L = np.array([0.22, -0.62, -1.0]) if not theirs else np.array([-0.3, -0.75, -1.0])
    x0, x1, y0, y1 = WIN
    out = []
    # four panes (2 x 2) leave mullion shadows
    xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
    for (a, b, c, d) in ((x0 + 0.03, xm - 0.02, ym + 0.02, y1 - 0.03), (xm + 0.02, x1 - 0.03, ym + 0.02, y1 - 0.03),
                         (x0 + 0.03, xm - 0.02, y0 + 0.03, ym - 0.02), (xm + 0.02, x1 - 0.03, y0 + 0.03, ym - 0.02)):
        pts = []
        for (px, py) in ((a, d), (b, d), (b, c), (a, c)):
            s = py / -L[1]
            pts.append(((px + L[0] * s) * 100, (D + L[2] * s) * 100))
        out.append((pts, 46))
    return out


def _bunk_frame(sc, P, x0, x1, z0, z1, made=False, ticking=True, noah=False, ours=True, tag='bunk', name='bunk', blanket='#5a6a4a',
                room_x=None):
    """A two-tier camp bunk: 4 posts, rails, slats, two mattresses, an end ladder. Along z (head at z1)."""
    pw = 0.07
    wood, wd, wl = P['wood'], P['wood_dk'], P['wood_lt']
    post = dict(front=wood, left=wl, right=wd, back=wd, top=wl)
    for (px, pz) in ((x0, z0), (x1 - pw, z0), (x0, z1 - pw), (x1 - pw, z1 - pw)):
        sc.box(px, 0, pz, px + pw, B_TOP + 0.42, pz + pw, post, 0, name + 'post', tag, P['outline'], 0.9)
    for y in (B_LOW - 0.16, B_TOP - 0.16):
        rail = dict(front=wood, top=wl, bottom=wd, left=wood, right=wood, back=wd)
        sc.box(x0, y - 0.1, z0 + pw, x0 + 0.05, y, z1 - pw, rail, 0, name + 'railL', tag, P['outline'], 0.7)
        sc.box(x1 - 0.05, y - 0.1, z0 + pw, x1, y, z1 - pw, rail, 0, name + 'railR', tag, P['outline'], 0.7)
        sc.box(x0 + pw, y - 0.14, z0, x1 - pw, y, z0 + 0.04, rail, 0, name + 'end', tag, P['outline'], 0.7)
        sc.box(x0 + pw, y - 0.3, z1 - 0.04, x1 - pw, y, z1, rail, 0, name + 'head', tag, P['outline'], 0.7)
    # safety rail of the top bunk (room side)
    rx = x0 if room_x is None else room_x
    sc.box(rx, B_TOP + 0.18, z0 + pw, rx + 0.04, B_TOP + 0.26, z1 - pw, dict(all=wood, top=wl), 0, name + 'toprail', tag,
           P['outline'], 0.7)
    # mattresses
    for (y, k) in ((B_LOW, 0), (B_TOP, 1)):
        mz0, mz1 = z0 + 0.06, z1 - 0.06

        def mat_top(pen, w, h, k=k):
            if made and k == 0:
                pen.fill(rect(0, 0, w, h), blanket)
                for i in range(0, int(w), 12):
                    pen.seg((i, 0), (i, h), 2.4, _dk(blanket, 0.25), 120)
                for j in range(0, int(h), 12):
                    pen.seg((0, j), (w, j), 2.4, _lt(blanket, 0.2), 90)
                pen.fill(rrect(8, 6, w - 16, 34, 10), P['paper']); pen.line(rrect(8, 6, w - 16, 34, 10), 0.9, P['outline'], 150)
                return
            pen.fill(rect(0, 0, w, h), P['mat'])
            if ticking:
                for i in range(int(w / 6) + 1):
                    if i % 3 == 0: pen.fill(rect(i * 6, 0, 2.2, h), P['mat_st'], 200)
            pen.texture(rect(0, 0, w, h), 'fabric', 0.25, 'overlay', 0.18)
            _vgrad(pen, w, h, [(0, P['mat_dk'], 120), (0.3, P['mat_dk'], 0)])
            for i in range(4):                    # tufts
                for j in range(9):
                    pen.fill(oval(w * (i + 0.5) / 4, h * (j + 0.5) / 9, 1.1), P['mat_dk'], 160)
            if noah and k == 0 and ours:
                pen.fill(rrect(w * 0.55, h * 0.72, 16, 10, 2), '#c8b45a', 150)   # a faded sticker
        def mat_side(pen, w, h):
            pen.fill(rect(0, 0, w, h), P['mat_dk'])
            if ticking:
                for i in range(int(w / 6) + 1):
                    if i % 3 == 0: pen.fill(rect(i * 6, 0, 2.2, h), _dk(P['mat_st'], 0.15), 200)
            pen.seg((0, 1), (w, 1), 1.0, P['outline'], 160); pen.seg((0, h - 1), (w, h - 1), 1.0, P['outline'], 160)
        sc.box(x0 + 0.04, y - 0.13, mz0, x1 - 0.04, y, mz1, dict(top=mat_top, left=mat_side, right=mat_side, front=mat_side,
                                                                back=mat_side), 0.01, name + 'mat%d' % k, tag)
    # slats under the bottom mattress
    for j in range(7):
        z = z0 + 0.15 + j * (z1 - z0 - 0.3) / 6
        sc.box(x0 + 0.05, B_LOW - 0.17, z - 0.035, x1 - 0.05, B_LOW - 0.14, z + 0.035, dict(all=wd, bottom=_dk(wd, 0.3)), 0, name + 'slat', tag)
    # ladder at the foot end
    lx = x1 - 0.18 if ours else x0 + 0.06
    for k in range(3):
        y = 0.45 + k * 0.38
        sc.box(x0 + 0.12, y, z0 - 0.03, x1 - 0.12, y + 0.04, z0, dict(all=wood, top=wl), 0, name + 'rung', tag, P['outline'], 0.6)


def _cabin_props(sc, cx, info):
    P = cx.P; ours = cx.ours; t = cx.t
    # ---------------------------------------------------------------- bunks
    _bunk_frame(sc, P, *LBUNK, made=not ours, ticking=True, noah=False, ours=ours, name='lbunk',
                blanket='#3f6fa8' if not ours else '#5a6a4a', room_x=LBUNK[1] - 0.04)
    _bunk_frame(sc, P, *NBUNK, made=not ours, ticking=True, noah=True, ours=ours, name='nbunk',
                blanket='#c0563a' if not ours else '#5a6a4a')
    if ours:
        # N.B. carved in the front post, search tape round it
        x0, x1, z0, z1 = NBUNK

        def carve(pen, w, h):
            pen.fill(rect(0, 0, w, h), P['wood'])
            _sign_text(pen, 'N.B.', w / 2, 46, 3.2, P['wood_dk'], 900)
        sc.plane((x0, 1.05, z0 - 0.002), (1, 0, 0), (0, -1, 0), 7, 60, carve, 0.02, 'carve', 'bunk')
        # faded search tape wrapped around the front post (bands + a hanging tail)
        tape_c = P['tape']

        def tape(pen, w, h):
            for y in (8, 22):
                pen.fill(rect(0, y, w, 7), tape_c, 230); pen.seg((0, y), (w, y), 0.4, _dk(tape_c, 0.4), 160)
                _sign_text(pen, 'SEARCH', w / 2, y + 5.6, 4.2, _dk(tape_c, 0.7), 900, 180)
        sc.plane((x0 - 0.003, 1.2, z0 - 0.003), (1, 0, 0), (0, -1, 0), 8, 34, tape, 0.03, 'tape', 'bunk')
        sc.quad([(x0 + 0.01, 0.96, z0 - 0.01), (x0 + 0.04, 0.96, z0 - 0.01), (x0 - 0.05, 0.42, z0 - 0.06), (x0 - 0.09, 0.45, z0 - 0.05)],
                tape_c, 220, P['outline'], 0.4, 0.03, 'tapetail', 'bunk')
    # ---------------------------------------------------------------- cubbies on the right wall above Noah's bunk (OURS)
    cz0, cz1, cy0, cy1 = CUBBY
    names = ['TY', 'ELI', 'SAM', 'LUIS', 'JAKE', 'NOAH']
    cw = (cz1 - cz0) / 3
    sc.box(W - 0.34, cy0, cz0, W, cy0 + 0.02, cz1, dict(all=P['wood'], top=P['wood_lt'], left=P['wood_lt']), 0, 'cubbyshelf', 'cubby', P['outline'], 0.7)
    sc.box(W - 0.34, (cy0 + cy1) / 2 - 0.01, cz0, W, (cy0 + cy1) / 2 + 0.01, cz1, dict(all=P['wood'], left=P['wood_lt']), 0, 'cubbymid', 'cubby', P['outline'], 0.7)
    sc.box(W - 0.34, cy1 - 0.02, cz0, W, cy1, cz1, dict(all=P['wood'], left=P['wood_lt']), 0, 'cubbytop', 'cubby', P['outline'], 0.7)
    for i in range(4):
        z = cz0 + i * cw
        sc.box(W - 0.34, cy0, z - 0.01, W, cy1, z + 0.01, dict(all=P['wood'], left=P['wood_lt'], front=P['wood_dk']), 0, 'cubbydiv', 'cubby', P['outline'], 0.7)
    for k, nm in enumerate(names):
        row, colm = k // 3, k % 3
        z = cz0 + colm * cw + cw / 2
        y = (cy1 - 0.035) if row == 0 else ((cy0 + cy1) / 2 - 0.035)

        def label(pen, w, h, nm=nm):
            pen.fill(rect(0, 0, w, h), '#d8cc98' if not ours else _lt(P['tape'], 0.15), 240)
            pen.line(rect(0, 0, w, h), 0.3, _dk(P['tape'], 0.4), 120)
            _sign_text(pen, nm, w / 2, h * 0.78, 3.6, '#2a2440', 800)
        sc.plane((W - 0.341, y, z + 0.06), (0, 0, -1), (0, -1, 0), 12, 4.6, label, 0.03, 'cubbylabel', 'cubby')
        # contents: theirs full (clothes, comics, a flashlight, a canteen); ours empty, dust (NOAH: a cobweb)
        yb = cy0 + 0.02 if row == 1 else (cy0 + cy1) / 2 + 0.01
        zc0 = cz0 + colm * cw + 0.03
        if not ours:
            cols = ['#3f8fa0', '#d84a4a', '#e0b84a', '#6a4fa8', '#4aa86a', '#2f8a3a']
            sc.box(W - 0.3, yb, zc0, W - 0.04, yb + 0.12, zc0 + cw - 0.06, dict(all=cols[k], top=_lt(cols[k], 0.2), left=_lt(cols[k], 0.1)),
                   0.01, 'cubbyclothes', 'cubby', P['outline'], 0.6)
            if k % 2 == 0:
                sc.box(W - 0.28, yb + 0.12, zc0 + 0.04, W - 0.06, yb + 0.15, zc0 + 0.24, dict(all='#f2e6c0', top='#e85a3a', left='#f4d040'),
                       0.01, 'comics', 'cubby', P['outline'], 0.5)
        elif nm == 'NOAH':
            def web(pen, w, h):
                for i in range(7):
                    a = math.pi * 0.5 * i / 6
                    pen.seg((0, 0), (math.cos(a) * w, math.sin(a) * h), 0.25, '#d8dcff', 120)
                for r_ in (6, 11, 16):
                    pts = [(math.cos(math.pi * 0.5 * i / 6) * r_, math.sin(math.pi * 0.5 * i / 6) * r_) for i in range(7)]
                    pen.line(poly(pts, False), 0.2, '#d8dcff', 100)
            sc.plane((W - 0.33, yb + 0.24, zc0 + cw - 0.07), (0, 0, -1), (0, -1, 0), 20, 20, web, 0.05, 'web', 'cubby')
    # ---------------------------------------------------------------- the window (frame, mullions, sill, screen, outside)
    x0, x1, y0, y1 = WIN
    fr = P['paint']; frd = P['paint_dk']

    def outside(pen, w, h):
        if ours:
            _vgrad(pen, w, h, [P['sky0'], P['sky1'], '#7078b8'])
            moon_xy = (w * 0.62, h * 0.28)
            _R(pen, None, moon_xy[0], moon_xy[1], 160, [(0, P['moon'], 120), (0.3, P['moon'], 40), (1, P['moon'], 0)], clip=False)
            pen.fill(oval(moon_xy[0], moon_xy[1], 18), P['moon']); pen.fill(oval(moon_xy[0] + 5, moon_xy[1] - 4, 15), '#ffffff', 150)
            for i in range(9):
                pine(pen, w * (i + 0.3 * _h(i, 3)) / 8, h * 0.98, h * (0.45 + 0.35 * _h(i, 4)), i, '#1a1f48', P['key'], 60, 0, 8, 0.4)
            pen.fill(rect(0, h * 0.94, w, h * 0.06), '#141838')
        else:
            _vgrad(pen, w, h, [P['sky0'], P['sky1'], '#ffe2b8'])
            _R(pen, None, w * 0.4, h * 0.85, 300, [(0, '#fff2d0', 150), (1, '#fff2d0', 0)], sy=0.6, clip=False)
            for i in range(9):
                pine(pen, w * (i + 0.3 * _h(i, 3)) / 8, h * 0.98, h * (0.35 + 0.3 * _h(i, 4)), i, '#7a8c6c', '#ffe6b0', 90, 0, 8, 0.4)
            pen.fill(rect(0, h * 0.9, w, h * 0.1), '#a8b46a')
    # the outside picture sits 3 m behind the window (parallax through the glass)
    sc.plane((x0 - 1.2, y1 + 1.2, D + 3.0), (1, 0, 0), (0, -1, 0), (x1 - x0 + 2.4) * 100, (y1 - y0 + 2.4) * 100, outside, -200,
             'outside', 'shell')
    # glass: faint reflection sheen
    def wglass(pen, w, h):
        _L(pen, rect(0, 0, w, h), 0, 0, w, h, [(0, '#ffffff', 26), (0.4, '#ffffff', 0), (0.6, '#ffffff', 10), (1, '#ffffff', 0)])
        if ours:   # the torn screen: mesh with a jagged hole and a curled flap
            hole = _blob(w * 0.66, h * 0.35, w * 0.16, h * 0.14, 11, 5, 0.5)
            pen.cv.save(); pen.cv.clipPath(hole, skia.ClipOp.kDifference, True)
            for i in range(0, int(w) + 1, 2):
                pen.seg((i, 0), (i, h), 0.18, '#c8ccf0', 70)
            for j in range(0, int(h) + 1, 2):
                pen.seg((0, j), (w, j), 0.18, '#c8ccf0', 70)
            pen.cv.restore()
            pen.line(hole, 0.5, '#d8dcff', 160)
            flap = poly([(w * 0.62, h * 0.24), (w * 0.8, h * 0.22), (w * 0.76, h * 0.4)])
            pen.fill(flap, '#9aa0d0', 120); pen.line(flap, 0.3, '#e0e4ff', 140)
    sc.plane((x0, y1, D - 0.005), (1, 0, 0), (0, -1, 0), (x1 - x0) * 100, (y1 - y0) * 100, wglass, -90, 'wglass', 'shell')
    win_parts = dict(front=fr, top=_lt(fr, 0.1), bottom=frd, left=frd, right=_lt(fr, 0.05), back=frd)
    xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
    for (a, b, c, d) in ((x0 - 0.06, x0, y0, y1), (x1, x1 + 0.06, y0, y1), (x0 - 0.06, x1 + 0.06, y1, y1 + 0.06),
                         (xm - 0.02, xm + 0.02, y0, y1), (x0, x1, ym - 0.02, ym + 0.02)):
        sc.box(a, c, D - 0.05, b, d, D, win_parts, -80, 'wframe', 'window', P['outline'], 0.8)
    # the sill (with the phone on it)
    sc.box(x0 - 0.1, y0 - 0.04, D - 0.15, x1 + 0.1, y0, D, dict(top=_lt(fr, 0.08), front=frd, left=frd, right=fr), -70, 'sill', 'window',
           P['outline'], 0.8)
    # chipped paint flecks on the sill front
    info['sill'] = v3(xm, y0, D - 0.08)
    if not ours:
        # gingham curtains frozen at 12 degrees, the lantern on the sill
        for side in (0, 1):
            xa = x0 - 0.08 if side == 0 else x1 - 0.18
            sway = math.radians(12) * (1 if side == 0 else -1)

            def cur(pen, w, h, side=side):
                gingham(pen, rect(0, 0, w, h), (0, 0, w, h), '#e9c64a', 0.28, 1.0, 1.0)
                pen.line(rect(0, 0, w, h), 0.6, P['outline'], 180)
                for i in range(4):
                    pen.seg((w * (i + 0.5) / 4, 0), (w * (i + 0.5) / 4 + 2, h), 1.6, _dk('#e9c64a', 0.3), 90)
            O = v3(xa, y1 + 0.08, D - 0.08)
            U = v3(1, 0, 0)
            V = norm(v3(math.sin(sway) * 0.0, -1.0, -math.tan(abs(sway)) * 0.6))
            sc.plane(O, U, V, 26, (y1 - y0 + 0.08) * 100 * 0.95, cur, 0.05, 'curtain', 'window')
        sc.box(x0 - 0.12, y1 + 0.08, D - 0.09, x1 + 0.12, y1 + 0.1, D - 0.07, dict(all='#8a6a40'), 0.04, 'rod', 'window')
        info['lantern'] = v3(x1 - 0.12, y0, D - 0.08)
    else:
        info['lantern'] = None
    # ---------------------------------------------------------------- the clock on the back wall
    ckx, cky, ckr = CLOCK

    def clock_face(pen, w, h):
        r = w / 2
        sec = 6 * 3600 + 59 * 60 + 40 if not ours else (23 * 3600 + 59 * 60 + 5)
        pen.fill(oval(r + 0.6, r + 1.2, r), '#000000', 90)
        pen.fill(oval(r, r, r), P['metal']); pen.line(oval(r, r, r), 0.7, P['outline'])
        pen.fill(oval(r, r, r * 0.86), '#f2ecd8' if not ours else '#c6c8e4')
        for k in range(60):
            a = k * math.pi / 30
            r0 = 0.72 if k % 5 == 0 else 0.8
            pen.seg((r + math.cos(a) * r * r0, r + math.sin(a) * r * r0), (r + math.cos(a) * r * 0.84, r + math.sin(a) * r * 0.84),
                    0.7 if k % 5 == 0 else 0.25, '#2a2a3a', 230)
        for k in range(1, 13):
            a = k * math.pi / 6 - math.pi / 2
            _sign_text(pen, str(k), r + math.cos(a) * r * 0.58, r + math.sin(a) * r * 0.58 + 1.0, 2.6, '#2a2a3a', 800)
        _sign_text(pen, 'CEDAR LAKE', r, r * 1.38, 1.6, '#5a4a3a' if not ours else '#4a4a6a', 800)
    sc.plane((ckx - ckr, cky + ckr, D - 0.03), (1, 0, 0), (0, -1, 0), ckr * 200, ckr * 200, clock_face, -60, 'clock', 'clock')
    info['clock'] = (v3(ckx, cky, D - 0.035), ckr)
    # ---------------------------------------------------------------- left wall: CABIN RULES sign (front), pennant, calendar
    def rules(pen, w, h):
        pen.fill(rect(0, 0, w, h), '#e8dcb8' if not ours else P['paper']); pen.line(rect(0, 0, w, h), 0.8, P['outline'])
        pen.texture(rect(0, 0, w, h), 'paper', 0.4, 'overlay', 0.15)
        if ours: pen.texture(rect(0, 0, w, h), 'grunge', 0.35, 'multiply', 0.2)
        _sign_text(pen, 'CABIN RULES', w / 2, 9, 5.2, '#2a3a6a' if ours else '#1a4a8a', 900)
        pen.seg((6, 12), (w - 6, 12), 0.5, '#c0302a', 220)
        for i, s in enumerate(('LIGHTS OUT 9:30', 'NO FOOD IN CABINS', 'SHOES OFF', 'BE KIND')):
            _sign_text(pen, s, 6, 20 + i * 7.2, 3.6, '#2a2a3a', 700, 230, 0, 'left')
        if not ours:
            pen.fill(oval(w - 9, h - 9, 5), '#f0c030'); _sign_text(pen, ':)', w - 9, h - 7.5, 4.0, '#3a2a10', 900)
    sc.plane((0.003, 1.75, 0.9), (0, 0, 1), (0, -1, 0), 46, 54, rules, -50, 'rules', 'decor')

    def calendar(pen, w, h):
        pen.fill(rect(0, 0, w, h), P['paper'] if ours else '#fbf6ea'); pen.line(rect(0, 0, w, h), 0.6, P['outline'])
        _vgrad(pen, w, h * 0.42, ['#3a6aa0' if not ours else '#4a5a8e', '#6ab0c8' if not ours else '#6a78a8'])
        for i in range(5):
            pine(pen, w * (i + 0.5) / 5, h * 0.4, h * 0.22, i, '#2a4a3a' if not ours else '#2a2f5a', None, 0, 0, 6, 0.4)
        _sign_text(pen, 'JULY', w / 2, h * 0.52, 4.6, '#c0302a', 900)
        for r_ in range(5):
            for c_ in range(7):
                gx, gy = 3 + c_ * (w - 6) / 7, h * 0.57 + r_ * (h * 0.4) / 5
                pen.line(rect(gx, gy, (w - 6) / 7, h * 0.08), 0.15, '#6a6a7a', 160)
                if r_ * 7 + c_ < 18: pen.seg((gx + 0.5, gy + 0.5), (gx + (w - 6) / 7 - 0.5, gy + h * 0.08 - 0.5), 0.3, '#c0302a', 150)
        if ours: pen.texture(rect(0, 0, w, h), 'grunge', 0.4, 'multiply', 0.2)
    sc.plane((3.18, 1.82, D - 0.01), (1, 0, 0), (0, -1, 0), 30, 44, calendar, -50, 'calendar', 'decor')

    def pennant(pen, w, h):
        tri = poly([(0, 0), (w, h * 0.5), (0, h)])
        pen.fill(tri, '#3f7a4a' if not ours else '#3a5a6a'); pen.line(tri, 0.6, P['outline'])
        _sign_text(pen, 'CEDAR LAKE', w * 0.38, h * 0.6, 4.2, '#f4f0e0' if not ours else '#c8cce8', 900)
        pen.fill(rect(-2, -2, 3, h + 4), '#8a6a40')
    sc.plane((3.7, 2.08, D - 0.01), (1, 0, 0), (0, -1, 0), 64, 24, pennant, -50, 'pennant', 'decor')
    # ---------------------------------------------------------------- front-left: broom, mattress stack
    for i in range(4):
        y = i * 0.15
        dx = 0.04 * math.sin(i * 1.7)
        sc.box(0.12 + dx, y, 0.35 + dx * 0.5, 1.02 + dx, y + 0.14, 2.25, dict(top=P['mat'] if i == 3 else P['mat_dk'], all=P['mat_dk'],
                                                                     right=P['mat']), 0, 'mstack', 'decor', P['outline'], 0.6)
    _obox(sc, (0.08, 0.02, 0.22), (0.16, 1.32, 0.12), 0.03, 0.03, dict(all=P['wood_lt']), 0, 'broom', 'decor')
    sc.quad([(0.02, 0.0, 0.32), (0.2, 0.0, 0.32), (0.13, 0.3, 0.2), (0.06, 0.3, 0.2)], '#8a7a4a' if not ours else '#6a6070', 255,
            P['outline'], 0.8, 0.05, 'broomhead', 'decor')
    # ---------------------------------------------------------------- the bare bulb on the tie beam
    def bulb(pen, cam, xf):
        a = xf.p(v3(W / 2, HW - 0.14, 3.2)); b = xf.p(v3(W / 2, 2.12, 3.2))
        if cam.dist(a) < 0.1 or cam.dist(b) < 0.1: return
        pa, pb = cam.pt(a), cam.pt(b)
        k = cam.px_per_m(b)
        pen.seg(pa, pb, max(0.8, 0.008 * k), P['outline'])
        pen.fill(oval(pb[0], pb[1] + 0.045 * k, 0.035 * k, 0.045 * k), '#c8c8d8' if ours else '#fff8e0', 230)
        pen.line(oval(pb[0], pb[1] + 0.045 * k, 0.035 * k, 0.045 * k), max(0.8, 0.006 * k), P['outline'])
        pen.fill(rect(pb[0] - 0.02 * k, pb[1] - 0.005 * k, 0.04 * k, 0.03 * k), P['metal'])
    sc.custom((W / 2, 2.2, 3.2), bulb, 0, 'bulb', 'decor')
    # cobweb + dead wasp nest in the back-left rafters
    def nest(pen, cam, xf):
        p = xf.p(v3(0.7, 2.92, 6.0))
        if cam.dist(p) < 0.1: return
        x, y = cam.pt(p); k = cam.px_per_m(p)
        b = _blob(x, y + 0.06 * k, 0.07 * k, 0.09 * k, 9, 4, 0.25)
        pen.fill(b, '#5a5470' if ours else '#a08a6a'); pen.line(b, max(0.8, 0.006 * k), P['outline'])
        for i in range(3): pen.seg((x - 0.05 * k, y + (0.03 + 0.04 * i) * k), (x + 0.05 * k, y + (0.035 + 0.04 * i) * k), max(0.5, 0.004 * k), P['outline'], 140)
        for i in range(8):
            a = -0.2 + 1.6 * i / 7
            pen.seg((x - 0.25 * k, y - 0.1 * k), (x - 0.25 * k + math.cos(a) * 0.4 * k, y - 0.1 * k + math.sin(a) * 0.4 * k), max(0.4, 0.002 * k),
                    '#d8dcff' if ours else '#fff6e0', 90)
    sc.custom((0.7, 2.92, 6.0), nest, 0, 'nest', 'decor')
    # ---------------------------------------------------------------- the mirror (OURS) / the bundle under Noah's bunk
    if ours:
        ms = cx.mirror_state
        if ms == 'absent':
            # wrapped in the striped towel under Noah's bunk
            x0b, x1b, z0b, z1b = NBUNK

            def bundle_top(pen, w, h):
                towel_cloth(pen, rect(0, 0, w, h), (0, 0, w, h), 0.18, 0.0, 3, 0.85, True, '#d89a5a', '#e8e0d0')
            sc.box(x0b + 0.2, 0.02, z0b + 0.5, x0b + 0.45, 0.16, z0b + 1.95, dict(top=bundle_top, left=bundle_top, front=bundle_top,
                                                                               right=bundle_top), 0.02, 'bundle', 'mirror', P['outline'], 0.8)
        else:
            _mirror_model(sc, cx, info)
    # ---------------------------------------------------------------- the phone on the sill (from 110.71, OURS)
    ph = str(cx.prop('phone', 'tess_pocket'))
    if ours and ph.startswith('sill'):
        red = 1.0 if 'red' in ph or cx.t >= 118.87 else 0.0
        xm_ = (x0 + x1) / 2

        def phone(pen, w, h):
            pen.fill(rrect(0, 0, w, h, 1.2), '#1a1c2c'); pen.line(rrect(0, 0, w, h, 1.2), 0.35, '#7a80b0')
            _L(pen, rrect(0.5, 0.5, w - 1, h - 1, 1.0), 0, 0, w, h, ['#20284a', '#06070e', '#141a34'])
            _L(pen, poly([(0, h * 0.2), (w, h * 0.05), (w, h * 0.15), (0, h * 0.32)]), 0, 0, 0, h, [(0, '#dfe6ff', 0), (0.5, '#dfe6ff', 90), (1, '#dfe6ff', 0)])
            if red: _R(pen, None, w * 0.6, h * 0.35, w * 0.7, [(0, GLOW, 160), (1, GLOW, 0)], clip=False)
        sc.plane((xm_ - 0.18, y0 + 0.003, D - 0.05), (1, 0, 0), (0, 0, -1), 7.4, 15, phone, -65, 'phone', 'window')
        info['phone'] = v3(xm_ - 0.14, y0 + 0.004, D - 0.12)
    # ---------------------------------------------------------------- THEIRS extras: swimsuits, drawings, duffel, polaroid, towel+drop, shoe
    if not ours:
        _theirs_props(sc, cx, info)
    # the door (open, swung in against the front wall) with the padlock hasp outside
    _door_model(sc, cx, info)


def _door_model(sc, cx, info):
    """The front door, swung OUT (so it never blocks the room); seen from outside in cabin_now/door and through the doorway
    in the reverse views. Its outside face carries the orange DEMOLITION sticker; the hasp + padlock are on the jamb."""
    P = cx.P; ours = cx.ours
    x0, x1, h = DOOR
    dirv = norm(v3(0.17, 0, -0.98))          # from the hinge (x1, z 0) toward the latch edge: swung out ~100 deg

    def door_out(pen, w, h_):
        _planks(pen, w, h_, P, 15.0, 13, True, None, 0.8, 0.2, True, 0.2, P['wood'], P['wood_dk'], P['wood_lt'], P['seam'])
        for y in (15, h_ / 2, h_ - 15):
            pen.fill(rect(0, y - 6, w, 12), P['wood_dk'], 200); pen.line(rect(0, y - 6, w, 12), 0.6, P['outline'], 150)
        if ours:
            r = rect(w * 0.18, h_ * 0.26, w * 0.64, 26)
            pen.fill(r, '#ff7a1a'); pen.line(r, 0.6, '#3a1a08')
            _sign_text(pen, 'DEMOLITION', w / 2, h_ * 0.26 + 11, 6.4, '#1a0a04', 900)
            _sign_text(pen, 'SAT 7:00 AM · KEEP OUT', w / 2, h_ * 0.26 + 20, 3.4, '#1a0a04', 800)
    # outside face: seen from z < 0 looking +z with the door swung toward -z: origin at the hinge top, U along dirv
    sc.plane((x1, h, 0.0), dirv, (0, -1, 0), (x1 - x0) * 100, h * 100, door_out, 0, 'door', 'door')
    info['door'] = v3((x0 + x1) / 2, 0, 0)


# ====================================================================== the mirror (OURS), its reflection, the doorway
def mirror_plane():
    """(O, U, V, w_cm, h_cm, normal): the leaning mirror's front plane, origin at the frame's top-left."""
    yt = math.sqrt(MIR_H ** 2 - (MIR_LEAN - 0.02) ** 2)
    O = v3(MIR[0], yt, D - 0.02)
    V = norm(v3(0, -yt, -(MIR_LEAN - 0.02)))
    U = v3(1, 0, 0)
    n = norm(np.cross(V, U))           # pointing into the room (-z, a little up)
    return O, U, V, (MIR[1] - MIR[0]) * 100, MIR_H * 100, n


MFW = 6.0          # frame width cm


def mirror_glass_pts(grow=0.0):
    """3D corners of the glass (inside the frame)."""
    O, U, V, w, h, n = mirror_plane()
    g = MFW - grow
    return [O + U * (g / 100) + V * (g / 100), O + U * ((w - g) / 100) + V * (g / 100), O + U * ((w - g) / 100) + V * ((h - g) / 100),
            O + U * (g / 100) + V * ((h - g) / 100)]


def mirror_local_H(cam, xf=ID):
    """Homography: v1 mirror-local px (PANE 300..1620 x -1092..2252, the lipstick steps' space) -> design px for this
    camera. The pane maps onto the glass rectangle."""
    O, U, V, w, h, n = mirror_plane()
    gx0, gy0 = MFW, MFW
    gw, gh = w - 2 * MFW, h - 2 * MFW
    px0, py0, px1, py1 = PANE
    su = gw / (px1 - px0); sv = gh / (py1 - py0)            # cm per mirror-local px
    Ow = O + U * ((gx0 - px0 * su) / 100) + V * ((gy0 - py0 * sv) / 100)
    Hm, _ = cam.H(xf.p(Ow), xf.d(U * su), xf.d(V * sv), 0.01)
    return Hm


def _frame_draw(P, lit=0.6, seed=3, doorway=False):
    base = mix(P['paint'], '#e8e4d8', 0.25) if P is PAL['night'] or P is PAL['after'] else P['paint']
    wood = P['wood_dk']

    def fr(pen, w, h):
        outer = rect(0, 0, w, h); inner = rect(MFW, MFW, w - 2 * MFW, h - 2 * MFW)
        ring = minus(outer, inner)
        _L(pen, ring, 0, 0, w, 0, [_lt(base, 0.1), base, _dk(base, 0.18)])
        pen.texture(ring, 'wood', 0.25, 'overlay', 0.15, 90)
        pen.cv.save(); pen.cv.clipPath(ring, skia.ClipOp.kIntersect, True)
        for i in range(22):
            side = i % 4; u = _h(i, seed)
            if side == 0: px, py = MFW * _h(i, seed + 1), u * h
            elif side == 1: px, py = w - MFW * _h(i, seed + 1), u * h
            elif side == 2: px, py = u * w, MFW * _h(i, seed + 1)
            else: px, py = u * w, h - MFW * _h(i, seed + 1)
            rr = MFW * (0.06 + 0.16 * _h(i, seed + 2))
            chip = _blob(px, py, rr * (1.6 if side < 2 else 1.0), rr * (1.0 if side < 2 else 1.6), 8, seed + i, 0.45)
            pen.fill(chip, wood); pen.line(chip, 0.12, _dk(wood, 0.4), 160)
        pen.cv.restore()
        pen.seg((MFW * 0.5, MFW * 0.45), (w - MFW * 0.5, MFW * 0.45), 0.3, '#ffffff', 120)
        pen.line(inner, 0.5, '#000000', 200)
        pen.line(outer, 0.7, P['outline'])
        if doorway:
            # the raw splintered edge of the wall boards just inside the frame
            for i in range(26):
                side = i % 4; u = _h(i, seed + 50)
                if side == 0: a, b = (MFW, MFW + u * (h - 2 * MFW)), (MFW + 1.5 + 3 * _h(i, 51), MFW + u * (h - 2 * MFW) + 2)
                elif side == 1: a, b = (w - MFW, MFW + u * (h - 2 * MFW)), (w - MFW - 1.5 - 3 * _h(i, 51), MFW + u * (h - 2 * MFW) + 2)
                elif side == 2: a, b = (MFW + u * (w - 2 * MFW), MFW), (MFW + u * (w - 2 * MFW) + 1.5, MFW + 2 + 3 * _h(i, 51))
                else: continue
                sp = poly([a, b, (a[0] + (1.2 if side != 1 else -1.2), a[1] + 3.5)])
                pen.fill(sp, '#c9a87a'); pen.line(sp, 0.15, '#3a2414', 200)
    return fr


def _mirror_model(sc, cx, info):
    """The leaning mirror in Cabin 7: frame (white, chipped), glass with a true reflection of the room (reverse angle,
    darker), sheen, silvering spots, dust film. In the doorway state the glass is replaced by the opening onto the stairs."""
    P = cx.P
    O, U, V, w, h, n = mirror_plane()
    ms = cx.mirror_state
    info['mirror_plane'] = (O, U, V, w, h, n)
    info['glass3d'] = mirror_glass_pts()

    def glass_item(pen, cam, xf):
        pts = [xf.p(p) for p in mirror_glass_pts(0.6)]
        q = clip_poly_near(cam, pts)
        if len(q) < 3: return
        gp = poly(q)
        cv = pen.cv
        cv.save(); cv.clipPath(gp, skia.ClipOp.kIntersect, True)
        if ms in ('doorway',):
            _doorway_view(pen, cam, xf, cx)
        elif ms in ('glass', 'dark', 'towel', 'covered'):
            # true reflection of the room in the leaning glass (the mirror itself excluded)
            refl = cx.refl_scene
            if refl is not None:
                xr = Xf.reflect_plane(O + V * 0.0, n).then(xf)
                pen.fill(rect(-4000, -4000, 9000, 9000), _dk(P['wall'], 0.45))
                refl.render(pen, cam, xr, skip=('mirror',))
                # the reflection is darker, cooler and a little green-grey (old silvering loses light)
                pen.fill(rect(-4000, -4000, 9000, 9000), '#04061a' if cx.ours else '#2a1a10', 175 if ms == 'glass' else 222)
                pen.fill(rect(-4000, -4000, 9000, 9000), '#2a4050', 34)
            draw_plane(pen, cam, xf, O, U, V, w, h, _glass_surface(P, ms), True, 0.01)
        cv.restore()
    sc.custom(O + U * (w / 200) + V * (h / 200), glass_item, -40, 'glass', 'mirror')
    sc.plane(O, U, V, w, h, _frame_draw(P, doorway=(ms == 'doorway')), -39.9, 'mframe', 'mirror')
    # the frame's thickness (side faces) so it reads as an object standing on the floor
    for (x_, s_) in ((MIR[0], -1), (MIR[1], 1)):
        sc.quad([O + U * ((x_ - MIR[0])) + v3(0, 0, 0), O + U * (x_ - MIR[0]) + V * (h / 100),
                 O + U * (x_ - MIR[0]) + V * (h / 100) + v3(0, 0, 0.035), O + U * (x_ - MIR[0]) + v3(0, 0, 0.035)],
                _dk(P['paint'], 0.35), 255, P['outline'], 0.6, -39.95, 'mside', 'mirror')
    info['mirror_centre'] = O + U * (w / 200) + V * (h / 200)


def _glass_surface(P, ms):
    """Sheen, silvering spots at the edges, the dust film and finger smudges on the glass (mirror plane cm)."""
    def g(pen, w, h):
        inner = rect(MFW, MFW, w - 2 * MFW, h - 2 * MFW)
        _L(pen, inner, 0, 0, w, h * 0.5, [(0, '#ffffff', 0), (0.30, '#e8ecff', 0), (0.36, '#e8ecff', 70), (0.43, '#ffffff', 10),
                                          (0.5, '#ffffff', 0), (0.58, '#e8ecff', 34), (0.62, '#ffffff', 0)])
        # bevel: a thin bright line just inside the frame, darker on the lower right
        pen.line(rect(MFW + 0.6, MFW + 0.6, w - 2 * MFW - 1.2, h - 2 * MFW - 1.2), 0.5, '#dfe6ff', 150)
        pen.seg((w - MFW - 0.8, MFW + 1), (w - MFW - 0.8, h - MFW - 1), 0.5, '#000000', 160)
        pen.cv.save(); pen.cv.clipPath(inner, skia.ClipOp.kIntersect, True)
        for i in range(34):
            e = i % 4; u = _h(i, 7)
            if e == 0: px, py = MFW + 2 + 4 * _h(i, 8), MFW + u * (h - 2 * MFW)
            elif e == 1: px, py = w - MFW - 2 - 4 * _h(i, 8), MFW + u * (h - 2 * MFW)
            elif e == 2: px, py = MFW + u * (w - 2 * MFW), MFW + 2 + 4 * _h(i, 8)
            else: px, py = MFW + u * (w - 2 * MFW), h - MFW - 2 - 6 * _h(i, 8)
            rr = 0.4 + 1.8 * _h(i, 9) ** 2
            pen.fill(_blob(px, py, rr, rr * 0.8, 9, i, 0.5), '#8a8ea8', 40 + int(50 * _h(i, 10)))
            pen.fill(_blob(px, py, rr * 0.55, rr * 0.45, 7, i + 1, 0.5), '#0a0a14', 170)
        pen.texture(inner, 'grunge', 0.10, 'screen', 0.18)
        for i in range(4):
            px = MFW + (0.2 + 0.6 * _h(i, 40)) * (w - 2 * MFW); py = MFW + (0.3 + 0.5 * _h(i, 41)) * (h - 2 * MFW)
            _R(pen, None, px, py, 6, [(0, '#c8d2ff', 26), (1, '#c8d2ff', 0)], sy=0.7, clip=False)
        if ms == 'dark':
            pen.fill(inner, '#000000', 220)
        pen.cv.restore()
    return g


def _doorway_view(pen, cam, xf, cx):
    """Through the doorway (OURS side): the stair shaft descending away from the back wall to gold light (red after 534.7,
    navy-dark while Tess is gone is a THEIRS state: our side keeps the gold)."""
    st = stairs_scene(cx.var if cx.var in ('red',) else 'stairs', from_ours=True)
    xm = (MIR[0] + MIR[1]) / 2
    xs = Xf(np.eye(3), [xm, 0.0, D]).then(xf)
    pen.fill(rect(-4000, -4000, 9000, 9000), '#1a0f26')
    st.render(pen, cam, xs)


# ====================================================================== the stairs (inside the glass)
SPAL = {
    'stairs': dict(tread='#4a2c66', tread_lt='#6a4a8e', riser='#2c1a3e', edge='#c63449', glow='#ff4060', wall='#3a2450',
                   wall_dk='#22142e', wall_lt='#5a3a7a', fog='#4a2c62', spill='#ffcf8a', moon='#9fa8ff', floor='#e8b070',
                   floor_dk='#c08048', rail='#2e1a3e', rail_lt='#6a4a8a', outline='#0e0612', gold_room='#ffd08a'),
    'red': dict(tread='#4a1030', tread_lt='#7a1e48', riser='#2a0818', edge='#ff2d55', glow='#ff4060', wall='#57183d',
                wall_dk='#2a0818', wall_lt='#8a2a5a', fog='#6a1840', spill='#ff5a5a', moon='#c2185b', floor='#c0503a',
                floor_dk='#7a2028', rail='#3a0a20', rail_lt='#ae3a6a', outline='#12030a', gold_room='#ff7a5a'),
}
ST_W = 0.90         # stair width
ST_T = 0.25         # tread depth (the ours-side shaft)
N_STEPS = 8


def stairs_scene(var='stairs', from_ours=False, bottom=True, tess=None, doorway_state='gold'):
    """The 8-step stair shaft in stairs-local coords: x across (-0.45..0.45), y up (0 = our floor at the doorway sill),
    z down the stairs (0 = the doorway). Tread k (1 = top .. 8 = bottom) has its top at y = -0.2 k and spans
    z = 0.25 (k - 1) .. 0.25 k. Left: a plum wall; right: the 9-baluster railing over the fog; bottom: the gold room."""
    S = SPAL['red' if var == 'red' else 'stairs']
    sc = Scene3()
    hw = ST_W / 2
    zb = ST_T * N_STEPS            # 2.0: the bottom of the stairs
    yb = -RISE * N_STEPS - 0.2     # -1.8: their floor

    # treads and risers
    for k in range(1, N_STEPS + 1):
        y = -RISE * k; z0, z1 = ST_T * (k - 1), ST_T * k
        u = (k - 1) / (N_STEPS - 1)             # 0 top .. 1 bottom: gold spill grows toward the bottom

        def top(pen, w, h, u=u, k=k):
            base = mix(S['tread'], S['tread_lt'], 0.25)
            pen.fill(rect(0, 0, w, h), base)
            # planks across the tread
            for i in range(0, int(w), 15):
                pen.seg((i, 0), (i, h), 0.6, S['riser'], 160)
            pen.texture(rect(0, 0, w, h), 'wood', 0.22, 'overlay', 0.2, 90)
            # light: moon from above on the upper treads, gold from below on the lower ones
            _L(pen, rect(0, 0, w, h), 0, 0, 0, h, [(0, S['moon'], 70 * (1 - u)), (1, S['moon'], 0)])
            _R(pen, None, w * 0.5, h * 0.5, w * 0.8, [(0, S['spill'], 90 * u ** 1.5), (1, S['spill'], 0)], sy=0.5, clip=False)
            # the red edge strip at the nosing (front edge, toward z0 = toward the top of the stairs: t = h is z0 side?)
            pen.fill(rect(0, h - 4.0, w, 4.0), S['edge']); pen.seg((0, h - 4.2), (w, h - 4.2), 0.6, '#ff8a9a', 200)
            pen.seg((0, h - 0.2), (w, h - 0.2), 0.6, S['outline'], 220)
            # worn middle
            _R(pen, None, w * 0.5, h * 0.55, w * 0.25, [(0, '#000000', 40), (1, '#000000', 0)], sy=0.6, clip=False)
        # top face: origin (x0, y, z1) U +x V -z  -> t = 0 at z1 (far), t = h at z0 (near edge = nosing)
        sc.plane((-hw, y, z1), (1, 0, 0), (0, 0, -1), ST_W * 100, ST_T * 100, top, 0, 'tread%d' % k, 'tread')

        def riser(pen, w, h, u=u):
            pen.fill(rect(0, 0, w, h), S['riser'])
            _L(pen, rect(0, 0, w, h), 0, 0, 0, h, [(0, S['glow'], 90), (0.25, S['glow'], 0)])
            _R(pen, None, w * 0.5, h, w * 0.7, [(0, S['spill'], 60 * u), (1, S['spill'], 0)], sy=0.4, clip=False)
            pen.seg((0, 0.3), (w, 0.3), 0.6, S['outline'], 200)
        sc.plane((-hw, y + RISE, z0), (1, 0, 0), (0, -1, 0), ST_W * 100, RISE * 100, riser, 0.001, 'riser%d' % k, 'tread')
    # the left wall (plum boards), the shaft ceiling, the stringer on the right
    def lwall(pen, w, h):
        _planks(pen, w, h, dict(wall=S['wall'], wall_dk=S['wall_dk'], wall_lt=S['wall_lt'], seam=S['outline']), 18.0, 21, True,
                lambda p, w_, h_: (_L(p, rect(0, 0, w_, h_), 0, 0, w_, 0, [(0, S['moon'], 70), (0.4, S['moon'], 0)]),
                                   _L(p, rect(0, 0, w_, h_), 0, 0, w_, 0, [(0.55, S['spill'], 0), (1, S['spill'], 120)])),
                0.8, 0.2, False, 0.1)
        # the stair line drawn on the wall (shadow of the treads)
        pts = []
        for k in range(N_STEPS + 1):
            pts += [(ST_T * k * 100 + 20, (1.7 + RISE * k) * 100), (ST_T * (k + 1) * 100 + 20, (1.7 + RISE * k) * 100)]
        pen.line(poly(pts, False), 1.2, S['outline'], 120)
    sc.plane((-hw, 1.7, -0.2), (0, 0, 1), (0, -1, 0), (zb + 0.8) * 100, 3.7 * 100, lwall, -50, 'lwall', 'shaft')
    def ceil(pen, w, h):
        pen.fill(rect(0, 0, w, h), S['wall_dk'])
        for i in range(0, int(h), 25): pen.seg((0, i), (w, i), 0.8, S['outline'], 160)
        _L(pen, rect(0, 0, w, h), 0, 0, 0, h, [(0, S['moon'], 50), (0.4, S['moon'], 0)])
    sc.plane((-hw - 0.2, 1.65, -0.2), (1, 0, 0), norm((0, -0.75, 1.0)), (ST_W + 0.5) * 100, 3.0 * 100, ceil, -50, 'ceil', 'shaft')
    # the fog void beyond the railing (right) and below
    def fog(pen, w, h):
        _vgrad(pen, w, h, [S['wall_dk'], S['fog'], mix(S['fog'], S['spill'], 0.35)])
        for i in range(6):
            yy = h * (0.2 + 0.13 * i)
            _R(pen, None, w * (0.3 + 0.4 * _h(i, 61)), yy, w * 0.5, [(0, S['wall_lt'], 60), (1, S['wall_lt'], 0)], sy=0.12, clip=False)
    sc.plane((hw + 2.5, 2.0, -0.5), (0, 0, 1), (0, -1, 0), (zb + 2.5) * 100, 4.5 * 100, fog, -150, 'fog', 'shaft')
    # stringer under the treads on the railing side
    sp = [(hw, 0.0, 0.0)]
    for k in range(1, N_STEPS + 1):
        sp += [(hw, -RISE * k, ST_T * (k - 1)), (hw, -RISE * k, ST_T * k)]
    sp += [(hw, yb, zb), (hw, yb, -0.05)]
    sc.quad([(hw + 0.02, 0.0, 0.0), (hw + 0.02, -RISE * N_STEPS, zb), (hw + 0.02, -RISE * N_STEPS - 0.25, zb), (hw + 0.02, -0.25, 0.0)],
            S['rail'], 255, S['outline'], 0.8, -0.2, 'stringer', 'rail')
    # railing: 9 balusters + handrail following the pitch
    for i in range(9):
        z = 0.1 + i * (zb - 0.2) / 8
        yfoot = -RISE * (int(z / ST_T) + 1)
        sc.box(hw - 0.03, yfoot, z - 0.02, hw + 0.01, yfoot + 0.86, z + 0.02, dict(all=S['rail'], left=S['rail_lt'], front=S['rail_lt']),
               0, 'baluster', 'rail', S['outline'], 0.5)
    _obox(sc, (hw - 0.01, 0.86 - 0.05, -0.05), (hw - 0.01, -RISE * N_STEPS + 0.86 - 0.05, zb + 0.05), 0.06, 0.05,
          dict(top=S['rail_lt'], side_a=S['rail'], side_b=S['rail_lt'], bottom=S['rail']), 0, 'handrail', 'rail')
    # newel post at the bottom
    sc.box(hw - 0.05, yb, zb - 0.02, hw + 0.04, yb + 1.15, zb + 0.07, dict(all=S['rail'], left=S['rail_lt'], top=S['rail_lt']), 0,
           'newel', 'rail', S['outline'], 0.6)
    if bottom:
        # the gold room at the bottom: their floor, Noah's bunk corner, a sun shaft
        def gfloor(pen, w, h):
            pen.fill(rect(0, 0, w, h), S['floor'])
            for i in range(0, int(w), 14): pen.seg((i, 0), (i, h), 0.8, S['floor_dk'], 200)
            _R(pen, None, w * 0.45, h * 0.3, w * 0.6, [(0, S['gold_room'], 200), (1, S['gold_room'], 0)], sy=0.6, clip=False)
        sc.plane((-2.5, yb, zb), (1, 0, 0), (0, 0, 1), 500, 400, gfloor, -60, 'gfloor', 'bottom')
        def gwall(pen, w, h):
            pen.fill(rect(0, 0, w, h), mix(S['floor'], '#ffffff', 0.15))
            for i in range(0, int(w), 17): pen.seg((i, 0), (i, h), 0.8, S['floor_dk'], 180)
            _vgrad(pen, w, h, [(0, S['gold_room'], 0), (1, S['gold_room'], 120)])
        sc.plane((-2.5, yb + 2.6, zb + 4.0), (1, 0, 0), (0, -1, 0), 500, 260, gwall, -70, 'gwall', 'bottom')
        # Noah's bunk at the foot of the stairs (right, beyond the newel)
        bw = dict(all='#b98650', top='#dcae74', left='#dcae74', front='#c99660')
        sc.box(0.55, yb, zb + 0.15, 1.45, yb + 0.46, zb + 2.2, dict(all='#c0563a', top='#d8704a', left='#e0805a', front='#b04a30'), 0,
               'gbunk', 'bottom', '#3a2414', 0.8)
        for (px, pz) in ((0.5, zb + 0.1), (1.45, zb + 0.1)):
            sc.box(px, yb, pz, px + 0.07, yb + 1.9, pz + 0.07, bw, 0, 'gpost', 'bottom', '#3a2414', 0.7)
    # the doorway frame at the top (seen from below / inside): white chipped, upright
    fr = _frame_draw(PAL['night'], doorway=True)
    gw = (MIR[1] - MIR[0])
    def frame_in(pen, w, h):
        fr(pen, w, h)
    sc.plane((-gw / 2, MIR_H - 0.06, 0.0), (1, 0, 0), (0, -1, 0), gw * 100, MIR_H * 100, _frame_hole(fr), 0.3, 'dframe', 'door')
    # wall around the doorway (seen from the stairs side): plum boards
    def dwall(pen, w, h):
        hole = rect((hw + 0.6 - gw / 2) * 100, 30, gw * 100, MIR_H * 100)
        pen.cv.clipPath(hole, skia.ClipOp.kDifference, True)
        _planks(pen, w, h, dict(wall=S['wall_dk'], wall_dk=S['riser'], wall_lt=S['wall'], seam=S['outline']), 18.0, 23, True, None, 0.8)
    sc.plane((-hw - 0.6, MIR_H + 0.24, 0.002), (1, 0, 0), (0, -1, 0), (ST_W + 1.2) * 100, (MIR_H + 0.5) * 100, dwall, 0.2, 'dwall', 'door')
    return sc


def _frame_hole(fr):
    def d(pen, w, h):
        fr(pen, w, h)
    return d


# ====================================================================== THEIRS: what the other side adds (built in OURS coords, then flipped)
SWIM = ['#1fb5b0', '#ff6b5a', '#8a5cf0', '#ffe14a']


def _theirs_props(sc, cx, info):
    P = cx.P; t = cx.t
    x0, x1, z0, z1 = NBUNK
    # swimsuits over the top rail of Noah's bunk (room side x0), one drip each (the drips are live in the views)
    def suits(pen, w, h):
        xs = [10, 52, 94, 136]
        for i, x in enumerate(xs):
            c = SWIM[i]
            if i % 2 == 0:      # a one-piece folded over the rail: straps, a scooped back, the fold
                body = smooth([(x + 2, 0), (x + 26, 0), (x + 24, 14), (x + 28, 30), (x + 22, 42), (x + 14, 44), (x + 6, 42), (x, 30),
                               (x + 4, 14)], True, 0.7)
                pen.fill(body, c); pen.line(body, 0.6, P['outline'])
                pen.fill(smooth([(x + 8, 18), (x + 20, 18), (x + 18, 30), (x + 10, 30)], True, 0.8), _dk(c, 0.18), 160)
                for sx_ in (x + 6, x + 22): pen.seg((sx_, -3), (sx_, 4), 1.2, _dk(c, 0.25), 220)
            else:               # trunks: waistband with a drawstring, two legs
                body = poly([(x, 0), (x + 30, 0), (x + 31, 26), (x + 17, 28), (x + 15, 16), (x + 13, 28), (x - 1, 26)])
                pen.fill(body, c); pen.line(body, 0.6, P['outline'])
                pen.fill(rect(x, 0, 30, 5), _lt(c, 0.25)); pen.seg((x + 14, 5), (x + 12, 12), 0.5, '#ffffff', 220)
                pen.seg((x + 16, 5), (x + 19, 11), 0.5, '#ffffff', 220)
            pen.seg((x + 4, 3), (x + 4, 40 if i % 2 == 0 else 24), 0.8, _lt(c, 0.45), 120)
            pen.fill(_blob(x + 15, 50 if i % 2 == 0 else 34, 1.2, 1.9, 7, i, 0.2), '#e8f6ff', 220)
    sc.plane((x0 - 0.015, B_TOP + 0.26, z0 + 0.2), (0, 0, 1), (0, -1, 0), 175, 62, suits, 0.05, 'swimsuits', 'bunk')
    info['swim_drips'] = [v3(x0 - 0.016, B_TOP + 0.26 - (0.5 if i % 2 == 0 else 0.34), z0 + 0.2 + (15 + xx) / 100)
                          for i, xx in enumerate((10, 52, 94, 136))]
    # the other shoe beside Noah's bunk, on the floor at the foot end (room side)
    def shoe(pen, w, h):
        sneaker(pen, w / 2, h / 2, 0.06, -10)
    sc.plane((x0 - 0.4, 0.002, z0 + 0.55), (1, 0, 0), (0, 0, -1), 30, 18, shoe, 0.05, 'shoe', 'floorprops')
    info['shoe'] = v3(x0 - 0.25, 0, z0 + 0.46)
    # the towel under the window (flat on the floor) and where the drop hangs
    wx0, wx1, wy0, wy1 = WIN

    def towel(pen, w, h):
        b = smooth([(4, 6), (w * 0.4, 0), (w - 4, 8), (w - 2, h * 0.6), (w - 8, h - 2), (w * 0.5, h - 6), (6, h - 3), (0, h * 0.4)], True, 0.8)
        towel_cloth(pen, b, (0, 0, w, h), 0.16, 0.6, 5, 1.0, True, '#e0a060', '#efe6d6')
        _R(pen, None, w * 0.55, h * 0.45, w * 0.3, [(0, '#5a3a20', 70), (1, '#5a3a20', 0)], sy=0.6, clip=False)
    sc.plane((wx0 - 0.05, 0.004, D - 0.25), (1, 0, 0), (0, 0, -1), 82, 52, towel, 0.04, 'towel', 'floorprops')
    info['towel'] = v3((wx0 + wx1) / 2, 0.01, D - 0.5)
    info['drop'] = v3((wx0 + wx1) / 2 + 0.05, 0.62, D - 0.5)
    # the battery lantern on the sill
    def lantern_c(pen, cam, xf):
        p = xf.p(v3(wx1 - 0.12, wy0, D - 0.08))
        if cam.dist(p) < 0.1: return
        x, y = cam.pt(p); k = cam.px_per_m(p)
        lantern(pen, x, y - 0.12 * k, 0.0025 * k / 0.9, 1.0, '#ffd9a0', '#3a4a3a', True)
    sc.custom((wx1 - 0.12, wy0 + 0.1, D - 0.08), lantern_c, -60, 'lantern', 'window')
    # kids' drawings taped to the right wall above the bunk head (OURS coords -> THEIRS left wall)
    for i, (zz, yy, cc) in enumerate(((5.0, 1.62, '#3f8fe0'), (5.4, 1.72, '#e05a3a'), (5.8, 1.6, '#3ab05a'))):
        def drawing(pen, w, h, i=i, cc=cc):
            pen.fill(rect(0, 0, w, h), '#fbf8ee'); pen.line(rect(0, 0, w, h), 0.4, P['outline'], 180)
            if i == 0:
                pen.fill(oval(w * 0.7, h * 0.25, 4), '#f4c020'); pen.fill(rect(0, h * 0.7, w, h * 0.3), '#5ab04a')
                pen.line(poly([(w * 0.2, h * 0.7), (w * 0.35, h * 0.45), (w * 0.5, h * 0.7)]), 0.6, '#8a4a2a')
            elif i == 1:
                pen.fill(rect(w * 0.15, h * 0.6, w * 0.7, h * 0.3), '#3a7ad0'); pen.fill(oval(w * 0.5, h * 0.35, 5), cc)
                _sign_text(pen, 'LAKE', w / 2, h * 0.22, 3.0, '#2a2a6a', 800)
            else:
                for k in range(3): pen.fill(oval(w * (0.25 + 0.25 * k), h * 0.6, 3.5), cc)
                _sign_text(pen, 'NOAH', w / 2, h * 0.3, 3.4, '#2a6a2a', 900)
            pen.fill(rect(w * 0.4, -1, w * 0.2, 3), '#e8dca0', 220)
        sc.plane((W - 0.004, yy, zz - 0.13), (0, 0, 1), (0, -1, 0), 26, 20, drawing, -45, 'drawing', 'decor')
    # pennant bright on the right wall (OURS coords) above the drawings
    def pennant(pen, w, h):
        tri = poly([(0, 0), (w, h * 0.5), (0, h)])
        pen.fill(tri, '#2f8a3a'); pen.line(tri, 0.6, P['outline'])
        _sign_text(pen, 'CEDAR LAKE', w * 0.38, h * 0.6, 4.2, '#fffbe8', 900)
    sc.plane((W - 0.004, 2.0, 4.4), (0, 0, 1), (0, -1, 0), 64, 24, pennant, -45, 'pennant2', 'decor')
    # duffel bag on the floor by the other bunk; Polaroid camera on the other bunk
    lx0, lx1, lz0, lz1 = LBUNK
    def duffel(pen, cam, xf):
        pass
    sc.box(lx1 + 0.05, 0.0, lz0 - 0.65, lx1 + 0.4, 0.28, lz0 - 0.05, dict(all='#2f6a8a', top='#4a8ab0', left='#3a7a9a', front='#285a78'),
           0, 'duffel', 'floorprops', P['outline'], 0.8)
    sc.box(lx0 + 0.3, B_LOW, lz0 + 0.5, lx0 + 0.42, B_LOW + 0.09, lz0 + 0.6, dict(all='#f2f0e8', top='#ffffff', front='#e8e4d8'), 0.01,
           'polaroid', 'bunk', P['outline'], 0.5)
    # the 8 stairs along the back wall up to the doorway (OURS coords: landing at the mirror spot, treads stepping down to +x)
    _stairs_theirs(sc, cx, info)


def _stairs_theirs(sc, cx, info):
    S = SPAL['red' if cx.var == 'red' or cx.P is PAL['theirs_break'] and cx.t > 560 else 'stairs']
    P = cx.P
    zf, zb = D - 0.9, D
    land0, land1 = MIR[0] - 0.05, 3.0
    treads = [(1, land0, land1, DROP - RISE)]
    for k in range(2, N_STEPS + 1):
        treads.append((k, land1 + (k - 2) * TREAD, land1 + (k - 1) * TREAD, DROP - RISE * k))
    for (k, xa, xb, yt) in treads:
        u = (k - 1) / 7.0

        def top(pen, w, h, u=u):
            pen.fill(rect(0, 0, w, h), mix(S['tread'], S['tread_lt'], 0.3))
            pen.texture(rect(0, 0, w, h), 'wood', 0.2, 'overlay', 0.2)
            _L(pen, rect(0, 0, w, h), 0, 0, 0, h, [(0, P['warm'], 70), (1, P['warm'], 0)])
            pen.fill(rect(0, h - 4, w, 4), S['edge']); pen.seg((0, h - 4.2), (w, h - 4.2), 0.6, '#ff8a9a', 220)
        sc.box(xa, yt - 0.05, zf - 0.02, xb, yt, zb, dict(top=top, front=S['edge'], left=S['riser'], right=S['edge'], all=S['riser']), 0,
               'ttread%d' % k, 'stairs', S['outline'], 0.6)

        def panel(pen, w, h, k=k):
            pen.fill(rect(0, 0, w, h), mix(S['tread'], S['wall'], 0.5))
            for i in range(0, int(w) + 1, 12): pen.seg((i, 0), (i, h), 0.6, S['outline'], 150)
            pen.texture(rect(0, 0, w, h), 'wood', 0.2, 'overlay', 0.2, 90)
            _vgrad(pen, w, h, [(0, S['glow'], 70), (0.08, S['glow'], 0), (0.75, '#000000', 0), (1, '#000000', 90)])
        def riser_f(pen, w, h):
            pen.fill(rect(0, 0, w, h), S['riser']); _vgrad(pen, w, h, [(0, S['glow'], 80), (0.2, S['glow'], 0)])
        # the closed side under each tread (panelled), its riser toward the next step down
        sc.box(xa, 0.0, zf, xb, yt - 0.05, zb, dict(front=panel, right=riser_f, left=riser_f, top=S['riser']), 0.01,
               'tblock%d' % k, 'stairs', S['outline'], 0.5)
    # stringer face on the room side with a glowing red trim
    def stringer(pen, w, h):
        pen.fill(rect(0, 0, w, h), S['riser'])
        for i in range(0, int(w), 16): pen.seg((i, 0), (i, h), 0.6, S['outline'], 150)
        _L(pen, rect(0, 0, w, h), 0, 0, 0, h, [(0, S['glow'], 60), (0.2, S['glow'], 0)])
    # balusters + handrail on the room side
    x_hi, x_lo = land0 + 0.05, treads[-1][2] - 0.04
    for i in range(9):
        x = x_hi + i * (x_lo - x_hi) / 8
        k = 1
        for (kk, xa, xb, yt) in treads:
            if xa <= x < xb + 1e-6: k = kk; ytop = yt
        if i == 8: ytop = treads[-1][3]
        sc.box(x - 0.022, ytop, zf + 0.03, x + 0.022, ytop + 0.88, zf + 0.075, dict(all=S['rail'], front=S['rail_lt'], left=S['rail_lt']),
               0.02, 'tbal', 'rail', S['outline'], 0.5)
    _obox(sc, (x_hi - 0.06, treads[0][3] + 0.9, zf + 0.05), (x_lo + 0.08, treads[-1][3] + 0.9, zf + 0.05), 0.06, 0.05,
          dict(top=S['rail_lt'], side_a=S['rail_lt'], side_b=S['rail'], bottom=S['rail']), 0.02, 'thand', 'rail')
    sc.box(x_lo + 0.04, 0.0, zf + 0.01, x_lo + 0.12, treads[-1][3] + 0.98, zf + 0.09, dict(all=S['rail'], front=S['rail_lt'], top=S['rail_lt']),
           0.02, 'tnewel', 'rail', S['outline'], 0.6)
    info['stairs_theirs'] = treads
    info['tread_pt'] = {k: v3((xa + xb) / 2, yt, (zf + zb) / 2) for (k, xa, xb, yt) in treads}
    # the doorway: white chipped frame set in the back wall 1.8 m up; the opening shows our blue night (or navy, or red)
    gw = MIR[1] - MIR[0]
    O = v3(MIR[0], DROP + MIR_H, D - 0.01)
    dstate = str(cx.prop('doorway', 'gold'))

    def opening(pen, w, h):
        inner = rect(MFW, MFW, w - 2 * MFW, h - 2 * MFW)
        if dstate.startswith('navy'):
            _vgrad(pen, w, h, ['#0a0d22', '#141a3a', '#0a0c1c'])
        elif dstate.startswith('red') or cx.var == 'red':
            _vgrad(pen, w, h, ['#3a0a20', '#ae3a6a', '#ff2d55'])
        else:
            # our cabin at night seen through: blue-violet, a rafter, the beam's glow
            _vgrad(pen, w, h, ['#2b2d57', '#454985', '#5b5fa0'])
            for i in range(3): pen.fill(rect(0, 18 + i * 40, w, 6), '#1f2046', 220)
            _R(pen, None, w * 0.5, h * 0.75, w * 0.8, [(0, '#fff3d6', 120), (1, '#ffd58a', 0)], sy=1.2, clip=False)
        _frame_draw(PAL['theirs'], doorway=True)(pen, w, h)
    sc.plane(O, (1, 0, 0), (0, -1, 0), gw * 100, MIR_H * 100, opening, -30, 'tdoor', 'stairs')
    info['doorway_theirs'] = (v3((MIR[0] + MIR[1]) / 2, DROP, D - 0.05), gw)


# ====================================================================== view framework
def _sig(cx):
    return '%s|%s|%s|%s' % (cx.mirror_state if cx.ours else 'theirs', str(cx.prop('phone', ''))[:8], str(cx.prop('doorway', ''))[:4],
                            str(cx.prop('padlock', ''))[:6])


def _bands(d0, near=0.72, far=1.45):
    return [(-1e9, near * d0, 'near'), (near * d0, far * d0, 'mid'), (far * d0, 999.0, 'far')]


def cabin_layers(cx, cam, view_key, d0, bands=None, xf=None):
    """Static cached layers of the cabin model for one camera: (layers, scene, info, xf)."""
    sc, info = cabin_scene(cx)
    cx.refl_scene = sc
    xf = xf if xf is not None else (ID if cx.ours else Xf.flip_x(W))
    key = 'v2:%s:%s:%s:%s' % (cx.side, view_key, cx.var, _sig(cx))
    bands = bands or _bands(d0)
    L = sc.layers(cam, d0, bands, key, xf)
    bandmap(cam, bands, L)
    return L, sc, info, xf


def bandmap(cam, bands, layers):
    """Remember which cached layer depth holds which camera distances, so live overlays on a surface (the clock hands,
    the lipstick, the beam's pool) sit just in front of the layer that holds that surface."""
    cam._bandmap = [(b[0], b[1], l.depth) for b, l in zip(bands, layers)]


def sdep(cam, xf, d0, P, eps=0.002):
    """Layer depth for an overlay on the surface at model point P."""
    d = cam.dist(xf.p(v3(P)))
    for (a, b, ld) in getattr(cam, '_bandmap', []):
        if (a <= d or a <= -1e8) and d < b: return max(0.2, ld - eps)
    return max(0.3, d / d0)


def _anc(cam, xf, d0, P, h_m=1.72, note=''):
    p = xf.p(v3(P)); x, y, h, dep = cam.anchor(p, h_m, d0)
    return Anchor(x, y, dep, h, note)


def _flash_on(st, t):
    v = str(st.v('flashlight', t))
    return v.startswith('tess_on') or v.startswith('tess_running') or v.startswith('tess_doorway')


def _beam_k(st):
    def k(t):
        if not _flash_on(st, t): return 0.0
        s = st.since('flashlight', t)
        return clamp(s / 0.08) if s < 1e3 else 1.0
    return k


def _proj_fn(cam, xf):
    return lambda P: cam.pt(xf.p(v3(P)))


def beam_layers(cam, xf, d0, st, src, aims, seed=0, wobble=9.0, spread=0.26, spot=150, a=0.36, n_dust=70, sweep=None,
                kfn=None, dust_box=None, depth=None):
    """Tess's beam between 3D points: src (hand) and aims [(t, P), ...] or a single P. Returns (layers, Beam)."""
    pr = _proj_fn(cam, xf)
    s2 = pr(src)
    if isinstance(aims, (list, tuple)) and len(aims) and isinstance(aims[0], (list, tuple)) and len(aims[0]) == 2 and \
            isinstance(aims[0][0], (int, float)) and not isinstance(aims[0][1], (int, float)):
        a2 = [(tt, *pr(P)) for (tt, P) in aims]
    else:
        a2 = pr(aims)
    kf = kfn or _beam_k(st)
    b = Beam(aim_fn(s2, a2, kf, wobble, seed, sweep=sweep), w0=22.0, spread=spread, spot=spot, a=a, spot_sy=0.55)
    aim0 = aims[0][1] if (isinstance(aims, (list, tuple)) and len(aims) and isinstance(aims[0], (list, tuple))
                          and len(aims[0]) == 2 and isinstance(aims[0][0], (int, float))) else aims
    dep = depth or sdep(cam, xf, d0, aim0, 0.006)
    L = [b.layer(dep, 'beam')]
    if n_dust:
        bx = dust_box or (min(s2[0], (a2 if isinstance(a2, tuple) else a2[0][1:])[0]) - 300, -100, 2100, 1200)
        L.append(_live(dep * 0.97, lambda pen, t: motes(pen, t, bx, n_dust, seed + 9, b, amb=0.05), 'dust', blur=0))
    return L, b


def shaft_layer(cam, xf, d0, key, P, theirs=False, a=34):
    """Volumetric moon (or sun) shafts from the window to the floor patch, cached; plus drifting motes inside them."""
    L3 = np.array([0.22, -0.62, -1.0]) if not theirs else np.array([-0.3, -0.75, -1.0])
    x0, x1, y0, y1 = WIN
    c = P['key'] if not theirs else P['warm']
    win = [v3(x0, y1, D), v3(x1, y1, D), v3(x1, y0, D), v3(x0, y0, D)]
    flo = [p + L3 * (p[1] / -L3[1]) for p in win]

    def draw(pen, t):
        for i in range(4):
            a_, b_ = win[i], win[(i + 1) % 4]; c_, d_ = flo[(i + 1) % 4], flo[i]
            q = clip_poly_near(cam, [xf.p(a_), xf.p(b_), xf.p(c_), xf.p(d_)])
            if len(q) >= 3:
                pa, pb = cam.pt(xf.p((a_ + b_) / 2)), cam.pt(xf.p((c_ + d_) / 2))
                _L(pen, poly(q), pa[0], pa[1], pb[0], pb[1], [(0, c, a), (0.7, c, a * 0.4), (1, c, 0)])
    mid = (win[0] + flo[2]) / 2
    dep = sdep(cam, xf, d0, mid, 0.001)
    lay = Layer(dep, draw, 'shafts', cache='v2:shaft:%s' % key, bounds=(-420, -280, 2340, 1360), blur=None)
    pts = [cam.pt(xf.p(p)) for p in win + flo if cam.dist(xf.p(p)) > 0.1]
    if not pts: return [lay]
    bx = (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
    m = _live(dep * 0.98, lambda pen, t: motes(pen, t, bx, 40, 77, None, c=c, amb=0.35 if not theirs else 0.0,
                                               speed=(8.0, 18.0) if not theirs else (0.0, 0.0)), 'shaft_dust', blur=0)
    return [lay, m]


def clock_live(cam, xf, d0, info, st, side, name='clock_hands'):
    """Hands of the back-wall clock (ours: real time with the backward jerk; theirs: the 6:59:40 loop / 7:00 after the bell)."""
    (C, r) = info['clock']
    O = C + v3(-r, r, 0.004)
    dep = sdep(cam, xf, d0, C, 0.002)

    def draw(pen, t):
        if side == 'theirs':
            sec, jit = 6 * 3600 + clock_theirs(t), 0.0
        else:
            sec, jit = _clock_sec(t, st, 'ours')

        def hands(p, w, h):
            rr = w / 2; s = sec % 43200
            for (ang, L, wd, c) in ((2 * math.pi * s / 43200 - math.pi / 2, 0.5, 1.4, '#1a1a24'),
                                    (2 * math.pi * (s % 3600) / 3600 - math.pi / 2, 0.75, 1.0, '#1a1a24'),
                                    (2 * math.pi * math.floor(s % 60) / 60 - math.pi / 2 + math.radians(jit), 0.8, 0.45, '#c0302a')):
                p.seg((rr - math.cos(ang) * rr * 0.12, rr - math.sin(ang) * rr * 0.12), (rr + math.cos(ang) * rr * L, rr + math.sin(ang) * rr * L), wd, c)
            p.fill(oval(rr, rr, 1.0), '#c0302a')
        draw_plane(pen, cam, xf, O, (1, 0, 0), (0, -1, 0), r * 200, r * 200, hands, True, 0.01)
    return _live(dep, draw, name, blur=None)


def steps_live(cam, xf, d0, st, var, glow_extra=0.0, show_eighth=True, name='lipstick'):
    """The lipstick steps (and the 8th line behind the glass) on the mirror via the mirror-local homography."""
    Hm = mirror_local_H(cam, xf)
    from engine.room3d import _skmat
    M = _skmat(Hm)
    O, U, V, w, h, n = mirror_plane()
    dep = sdep(cam, xf, d0, O + U * (w / 200) + V * (h / 200), 0.003)
    glass_q = clip_poly_near(cam, [xf.p(p) for p in mirror_glass_pts(0.6)])

    def draw(pen, t):
        if len(glass_q) < 3: return
        kw = steps_v2(st, var, t)
        if glow_extra: kw['glow'] = max(kw['glow'], glow_extra)
        cv = pen.cv
        cv.save(); cv.clipPath(poly(glass_q), skia.ClipOp.kIntersect, True)
        cv.concat(M)
        e = st.ev('eighth_draw')
        ev = str(st.v('eighth', t))
        if show_eighth and (e is not None or ev.startswith('present') or ev.startswith('drawn') or ev.startswith('glow')):
            eighth_line(pen, t, e, 0.6, 1.0, 1.0)
        lipstick_steps(pen, t, **kw)
        cv.restore()
    return _live(dep, draw, name, blur=None)


def _cam_for(shot, base):
    """Per-shot camera tweaks: none for now (the 2.5D engine camera keys move over the cached room)."""
    return base


def _num_at(s):
    import re
    m = re.match(r'\s*(\d+)', str(s)); return int(m.group(1)) if m else 0


def steps_v2(st, var, t):
    """lipstick_steps kwargs from the v2 props: steps_drawn (the hook draw-on), smeared ('1 at 134.95', '2-5 by 138.6', '7',
    'streaked'), erased ('1-3 by 619.7', 3, 7: wiped from the top down), the red glow in the climax."""
    kw = _steps_state(st, var, t)                      # v1: draw-on, glow, wipe var
    # smears (v2 key 'smeared')
    sm_raw = str(st.raw.get('smeared', '0'))
    sm = [0.0] * 7
    import re
    ts = [float(x) for x in re.findall(r'(\d+\.\d+)', sm_raw)]
    if sm_raw.startswith('streaked'):
        kw['wipe'] = 1100.0; kw['fade'] = 0.85
    elif ' at ' in sm_raw and ts:
        n = _num_at(sm_raw)
        for k in range(n - 1): sm[k] = 1.0
        sm[n - 1] = ease_out_cubic(prog(t, ts[0], ts[0] + 0.22))
    elif ' by ' in sm_raw and ts:
        a, b = [int(x) for x in re.findall(r'(\d+)-(\d+)', sm_raw)[0]]
        for k in range(a - 1): sm[k] = 1.0
        cues = [c for c in st.sfx('lipstick_smear') if c >= st.t0 - 0.05]
        tk = cues if len(cues) >= (b - a + 1) else [st.t0 + (ts[0] - st.t0) * (j + 0.5) / (b - a + 1) for j in range(b - a + 1)]
        for j, k in enumerate(range(a - 1, b)):
            sm[k] = ease_out_cubic(prog(t, tk[j], tk[j] + 0.22))
    else:
        n = _num_at(sm_raw)
        for k in range(min(7, n)): sm[k] = 1.0
    for (tc, d_) in st.changes:
        if 'smeared' in d_ and t >= tc:
            n = int(d_['smeared']); sm = [1.0 if k < n else sm[k] for k in range(7)]
    kw['smear'] = sm
    # wiping (v2 key 'erased'): steps wiped from the top down
    er_raw = str(st.raw.get('erased', '0'))
    ts = [float(x) for x in re.findall(r'(\d+\.\d+)', er_raw)]
    n_er = float(_num_at(er_raw))
    if ' by ' in er_raw and ts:
        a, b = [int(x) for x in re.findall(r'(\d+)-(\d+)', er_raw)[0]]
        cues = [c for c in st.sfx('glass_wipe') if c >= st.t0 - 0.05]
        t_a = cues[0] - 0.05 if cues else st.t0
        n_er = (a - 1) + (b - a + 1) * clamp((t - t_a) / max(0.2, ts[0] - t_a))
    for (tc, d_) in st.changes:
        if 'erased' in d_:
            if t >= tc: n_er = float(d_['erased'])
            elif n_er < float(d_['erased']) and ' by ' not in er_raw:
                n_er = n_er + (float(d_['erased']) - n_er) * clamp((t - st.t0) / max(0.2, tc - st.t0))
    if n_er >= 6.95:
        kw['erased'] = True; kw['wipe'] = None
        kw['last'] = (1.0 - prog(t, st.t0, st.t0 + 1.2)) if st.t0 < 621.5 else 0.0
    elif n_er > 0.01:
        kw['wipe'] = 300 + 80 * n_er - 40
    if var == 'red' or str(st.raw.get('mirror', '')).startswith('glass returning'):
        kw['glow'] = max(kw.get('glow', 0.0), 0.75 + 0.25 * math.sin(t * 2 * math.pi / 1.2))
    return kw


# ====================================================================== OURS views (cabin_now)
OURS_CAMS = {
    # name: (pos, look, fov, roll)                                           DIRECTION_V2 4.1 angle
    'master': ((4.05, 2.02, 0.32), (2.55, 0.95, 6.4), 80.0, 0.0),          # 1 master high-wide from the door
    'reverse': ((2.66, 1.35, 5.95), (3.95, 1.0, 0.0), 74.0, 0.0),           # 2 reverse from the mirror spot toward the door
    'under_bunk': ((5.05, 0.13, 3.55), (5.15, 0.12, 6.2), 72.0, 0.0),       # 3 floor level under Noah's bunk
    'profile': ((1.2, 1.25, 3.85), (4.6, 0.9, 6.25), 70.0, 0.0),           # 4 profile along the back wall
    'overhead': ((2.9, 3.55, 3.4), (2.75, 0.0, 4.6), 82.0, 0.0),            # 5 overhead (the floor, the phone)
    'ots_mirror': ((2.98, 1.12, 4.55), (2.62, 0.82, 6.4), 58.0, 0.0),      # 6 OTS behind you at the mirror
    'three_q': ((0.95, 1.42, 3.7), (3.3, 0.85, 6.2), 72.0, 0.0),            # 9 three-quarter from the left bunk
    'doorway_down': ((2.66, 1.45, 5.3), (2.66, -0.7, 7.6), 70.0, 0.0),      # 10 behind you looking down through the doorway
    'dutch_low': ((3.7, 0.42, 2.7), (3.1, 1.25, 6.3), 76.0, 8.0),           # 11 dutch low angle (climax)
    'floor_wide': ((1.05, 0.62, 1.9), (3.5, 0.45, 5.7), 74.0, 0.0),         # 12 the ending wide on the floor
    'doorway': ((2.95, 1.15, 4.35), (2.66, 0.86, 6.4), 56.0, 0.0),          # MS of the doorway
    'bunk_rail': ((3.85, 1.25, 3.55), (5.05, 1.35, 5.1), 64.0, 0.0),        # MS: grown Noah hits the top rail
    'floor_cu': ((2.72, 0.24, 4.95), (2.66, 0.18, 6.3), 62.0, 0.0),         # low: the floor at the mirror spot
}


def _ours_anchors(cam, xf, d0):
    A = {}
    pts = {'tess_door': ((4.0, 0, 0.9), 1.68), 'you_door': ((3.6, 0, 1.3), 1.76), 'you_mirror': ((2.66, 0, 5.35), 1.76),
           'you_kneel': ((2.7, 0, 5.55), 1.76), 'tess_mirror': ((1.85, 0, 5.1), 1.68), 'tess_beside': ((3.35, 0, 5.0), 1.68),
           'tess_center': ((2.9, 0, 3.6), 1.68), 'noah_stand': ((3.8, 0, 4.6), 1.86), 'noah_floor': ((3.3, 0, 4.4), 1.86),
           'you_floor': ((2.4, 0, 4.1), 1.76), 'tess_sill': ((1.82, 0, 5.75), 1.68), 'noah_bunk_edge': ((4.6, 0, 5.2), 1.86),
           'doorway': ((2.665, 0, 6.2), 1.6), 'mirror': ((2.665, 0, 6.25), 1.6), 'sill': ((1.82, 0.95, 6.3), 0.2),
           'phone': ((1.68, 0.95, 6.28), 0.15), 'clock': ((CLOCK[0], CLOCK[1] - CLOCK[2], 6.38), 0.3),
           'cubby_noah': ((5.4, 2.0, 6.0), 0.3), 'bundle': ((5.0, 0.05, 5.5), 0.2)}
    for k, (P, h) in pts.items():
        a = _anc(cam, xf, d0, P, h)
        if cam.dist(xf.p(v3(P))) > 0.15: A[k] = a
    return A


def _ours_light(cx, cam, xf, d0, st, vname, info, beam=True):
    """Live/cached light for OURS views: moon shafts + motes, Tess's beam (if on) aimed at the mirror, the clock hands, the
    lipstick steps on the glass, the doorway's gold (or red) spill."""
    L = []
    t0 = st.t0
    P = cx.P
    var = cx.var
    if var in ('night', 'flash', 'doorway_glow', 'after', 'phone_glow'):
        L += shaft_layer(cam, xf, d0, '%s:%s' % (vname, var), P, False, 30 if var != 'after' else 22)
    if 'clock' in info and cam.dist(xf.p(info['clock'][0])) > 0.3:
        L.append(clock_live(cam, xf, d0, info, st, 'ours'))
    ms = cx.mirror_state
    b = None
    if beam and var in ('night', 'flash', 'doorway_glow') and any(_flash_on(st, tt) for tt in (st.t0, (st.t0 + st.t1) / 2, st.t1)):
        aim = info.get('mirror_centre', v3(2.66, 0.8, 6.2)) if ms != 'absent' else v3(5.0, 0.2, 5.4)
        # Tess stands beside or behind the camera: her lamp enters from the lower left, off frame (the assembler drives
        # the beam from her rig when she is in shot: sp.info['beam'].override)
        R = cam.R
        src = cam.C + R[2] * 0.45 - R[0] * 0.6 - R[1] * 0.3
        bl, b = beam_layers(cam, xf, d0, st, src, [(t0, aim + v3(0.15, 0.1, 0)), (t0 + 1.2, aim + v3(-0.1, -0.05, 0)),
                                                   (t0 + 2.6, aim + v3(0.08, 0.12, 0))], seed=int(t0) % 17)
        L += bl
    if ms in ('glass', 'dark') and cam.dist(xf.p(v3(2.66, 0.8, 6.3))) > 0.3:
        L.append(steps_live(cam, xf, d0, st, var))
        if b is not None:
            L.append(glass_glint_live(cam, xf, d0, b, src))
    if ms == 'doorway' or var == 'doorway_glow' or var == 'red':
        L += doorway_spill(cam, xf, d0, cx, st)
    return L, b


def glass_glint_live(cam, xf, d0, beam, src):
    """The flashlight seen IN the glass: the lamp's reflection (a hot point with a soft bloom) where the mirror reflects
    the source, clipped to the glass; it rides the beam's strength."""
    O, U, V, w, h, n = mirror_plane()
    R = Xf.reflect_plane(O, n)
    p = R.p(v3(src))
    q = clip_poly_near(cam, [xf.p(x) for x in mirror_glass_pts(0.6)])
    dep = sdep(cam, xf, d0, O + U * (w / 200) + V * (h / 200), 0.004)
    if len(q) < 3 or cam.dist(xf.p(p)) < 0.2: return _live(dep, lambda pen, t: None, 'glass_glint')
    x, y = cam.pt(xf.p(p)); k = cam.px_per_m(xf.p(p))

    def draw(pen, t):
        kk = beam.at(t)[4]
        if kk < 0.02: return
        pen.cv.save(); pen.cv.clipPath(poly(q), skia.ClipOp.kIntersect, True)
        _R(pen, None, x, y, 0.5 * k, [(0, '#fff3d6', 150 * kk), (0.25, '#ffd58a', 60 * kk), (1, '#ffd58a', 0)], clip=False)
        _R(pen, None, x, y, 0.06 * k, [(0, '#ffffff', 255 * kk), (1, '#fff3d6', 0)], clip=False)
        pen.cv.restore()
    return _live(dep, draw, 'glass_glint', blur=None)


def doorway_spill(cam, xf, d0, cx, st):
    """Gold rays and haze spilling from the doorway into the blue cabin (red after 534.7 / in the red var), gold steam
    wisps for the kitchen smell (264-270 s), a breathing pulse (red: period 1.2 s)."""
    red = cx.var == 'red' or str(cx.prop('doorway', '')).startswith('red')
    c = '#ff2d55' if red else '#ffcf8a'
    c2 = '#c2185b' if red else '#ffe2a8'
    G = [cam.pt(xf.p(p)) for p in mirror_glass_pts(1.0) if cam.dist(xf.p(p)) > 0.1]
    if len(G) < 4: return []
    cxp = sum(p[0] for p in G) / 4; cyp = sum(p[1] for p in G) / 4
    k_px = cam.px_per_m(xf.p(v3(2.66, 0.8, 6.3)))
    dep = sdep(cam, xf, d0, v3(2.66, 0.8, 6.2), 0.005)
    steam = (not red) and st.t1 > 263.5 and st.t0 < 271.0

    def draw(pen, t):
        pulse = (0.82 + 0.18 * math.sin(t * 2 * math.pi / 1.2)) if red else (0.9 + 0.1 * math.sin(t * 1.3))
        _R(pen, None, cxp, cyp, 1.6 * k_px, [(0, c, 90 * pulse), (0.35, c, 40 * pulse), (1, c, 0)], sy=0.9, clip=False)
        # floor pool in front of the doorway
        fp = cam.pt(xf.p(v3(2.66, 0.0, 5.6)))
        _R(pen, None, fp[0], fp[1], 1.3 * k_px, [(0, c2, 110 * pulse), (0.5, c, 45 * pulse), (1, c, 0)], sy=0.35, clip=False)
        # rays fanning out of the opening
        for i in range(6):
            a = -0.9 + 1.8 * i / 5 + 0.05 * math.sin(t * 0.7 + i)
            L_ = (1.6 + 0.6 * _h(i, 3)) * k_px
            w0 = 0.08 * k_px
            q = poly([(cxp - w0, cyp), (cxp + w0, cyp), (cxp + math.sin(a) * L_ + w0 * 4, cyp + math.cos(a) * L_ * 0.55 + 0.3 * k_px),
                      (cxp + math.sin(a) * L_ - w0 * 4, cyp + math.cos(a) * L_ * 0.55 + 0.3 * k_px)])
            _L(pen, q, cxp, cyp, cxp + math.sin(a) * L_, cyp + math.cos(a) * L_ * 0.55, [(0, c, 46 * pulse), (1, c, 0)])
        if steam:
            for i in range(5):
                ph = (t * 0.35 + i * 0.2) % 1.0
                x = cxp + (math.sin(t * 0.8 + i * 1.7) * 0.15 + (i - 2) * 0.06) * k_px
                y = cyp - ph * 1.2 * k_px
                _R(pen, None, x, y, (0.08 + 0.2 * ph) * k_px, [(0, '#ffe2a8', 80 * (1 - ph)), (1, '#ffe2a8', 0)], sy=1.6, clip=False)
    return [_live(dep, draw, 'doorway_spill', blur=None)]


def ours_view(vname, var, st, shot, cam=None, d0=None, extra=None):
    cx = CabinCtx('ours', var or 'night', st, st.t0)
    pos, look, fov, roll = OURS_CAMS[vname] if cam is None else (None, None, None, None)
    cam = cam or Cam3(pos, look=look, fov=fov, roll=roll)
    d0 = d0 or max(1.0, cam.dist(v3(2.66, 0.9, 6.0)))
    L, sc, info, xf = cabin_layers(cx, cam, vname, d0)
    live, b = _ours_light(cx, cam, xf, d0, st, vname, info)
    L += live
    if extra: L += extra(cx, cam, xf, d0, info)
    an = _ours_anchors(cam, xf, d0)
    info_out = dict(info, cam3=cam, d0=d0, xf=xf, model=sc, world='ours')
    if cx.mirror_state in ('glass', 'dark', 'doorway', 'towel'):
        info_out['glass'] = clip_poly_near(cam, [xf.p(p) for p in mirror_glass_pts(0.6)])
        info_out['mirror_H'] = mirror_local_H(cam, xf)
    return _sp('cabin_now/' + vname, L, an, None, 1.0, 0.0, None, info_out, b)


def _reg_ours(vname):
    @view('cabin_now', vname)
    def _v(var, st, shot, vname=vname):
        return ours_view(vname, var, st, shot)
    return _v


for _vn in ('master', 'reverse', 'under_bunk', 'profile', 'overhead', 'ots_mirror', 'three_q', 'doorway_down', 'dutch_low',
            'floor_wide', 'doorway', 'bunk_rail', 'floor_cu'):
    _reg_ours(_vn)


# ====================================================================== THEIRS views (cabin_dawn): cameras in THEIRS world coords
THEIRS_CAMS = {
    # name: (pos, look, fov, roll)                                          DIRECTION_V2 4.4 angle
    'master': ((1.75, 2.0, 0.3), (2.55, 1.35, 6.4), 80.0, 0.0),             # 1 from the cabin door: stairs, doorway, bunk, window
    'reverse': ((1.25, 0.95, 4.15), (2.95, 2.55, 6.4), 72.0, 0.0),          # 2 from the bunk up the stairs to the doorway
    'window': ((3.05, 1.3, 4.35), (3.78, 1.3, 6.4), 58.0, 0.0),             # 3 window wide
    'towel_floor': ((4.55, 0.2, 4.55), (3.75, 0.12, 6.0), 62.0, 0.0),       # 4 floor level across the towel and the drop
    'bunk_2s': ((2.35, 1.15, 3.25), (0.6, 0.75, 5.25), 62.0, 0.0),          # 5 the bunk 2-shot
    'queen_3s': ((3.0, 1.35, 2.55), (0.9, 0.75, 5.2), 66.0, 0.0),           # 6 the Queen 3-shot
    'top_stairs': ((2.93, 3.35, 6.15), (1.7, 0.25, 3.4), 74.0, 0.0),        # 8 high from the top of the stairs (Tess's view)
    'ots_noah': ((0.55, 1.05, 5.55), (2.7, 1.0, 3.0), 60.0, 0.0),           # 9 OTS past Noah
    'dip_low': ((1.35, 0.62, 4.0), (0.5, 0.5, 5.35), 56.0, 0.0),            # 10 the mattress dip, low
    'overhead': ((2.2, 3.55, 2.4), (1.5, 0.0, 3.75), 80.0, 0.0),            # high angle on the floor (the prints)
    'floor_prints': ((3.4, 0.36, 0.9), (1.0, 0.0, 4.1), 70.0, 0.0),         # low wide at the wash-house door
    'door_wash': ((2.9, 1.3, 3.9), (1.6, 1.05, 0.0), 66.0, 0.0),            # the wash-house door swings in
    'swimsuits': ((2.05, 1.75, 4.05), (0.9, 1.55, 5.25), 56.0, 0.0),        # the swimsuits on the top rail
    'lantern': ((3.9, 1.18, 5.65), (3.95, 1.03, 6.35), 40.0, 0.0),          # insert: the lantern on the sill
    'clock': ((4.45, 2.05, 5.8), (4.45, 2.12, 6.4), 34.0, 0.0),             # insert: the clock 6:59
    'knot': ((1.35, 0.5, 4.25), (0.8, 0.08, 4.95), 46.0, 0.0),              # insert: the half-tied lace
    'shoe': ((1.55, 0.62, 3.95), (0.95, 0.04, 4.85), 52.0, 0.0),            # insert: one shoe on, the other beside the bed
    'hands': ((1.7, 1.1, 3.9), (0.8, 0.7, 5.3), 50.0, 0.0),                 # POV plates for the hand inserts
    'hands_jerk': ((1.6, 1.15, 3.7), (1.5, 1.0, 6.4), 54.0, 0.0),
}


def _theirs_anchors(cam, xf, d0):
    """Anchors in THEIRS world coords (the model is flipped, so these are given directly in world x)."""
    A = {}
    pts = {'noah_bunk': ((0.95, B_LOW, 5.15), 1.5), 'noah_seat': ((0.95, B_LOW, 5.15), 1.5), 'queen_bunk': ((0.95, B_LOW, 4.65), 1.92),
           'you_bunk_end': ((1.0, B_LOW, 4.35), 1.76), 'you_stand': ((1.75, 0, 4.4), 1.76), 'you_room': ((2.3, 0, 3.6), 1.76),
           'queen_corner': ((4.1, 0, 5.75), 1.92), 'tess_doorway': ((2.93, DROP, 6.22), 1.68), 'doorway': ((2.93, DROP, 6.3), 1.6),
           'stairs_foot': ((1.25, 0, 5.4), 1.76), 'tread8': ((1.04, DROP - 1.6, 5.95), 1.76), 'tread1': ((2.93, DROP - 0.2, 5.95), 1.76),
           'towel': ((3.78, 0.0, 5.9), 0.2), 'drop': ((3.83, 0.62, 5.9), 0.1), 'shoe': ((1.18, 0, 4.71), 0.12),
           'dip': ((0.95, B_LOW, 4.75), 0.2), 'door_wash': ((1.6, 0, 0.1), 1.76), 'clock': ((4.45, 1.97, 6.38), 0.3),
           'window': ((3.78, 1.42, 6.38), 0.95)}
    for k, (P, h) in pts.items():
        p = v3(P)
        if cam.dist(p) > 0.15:
            x, y, hh, dep = cam.anchor(p, h, d0)
            A[k] = Anchor(x, y, dep, hh)
    return A


def frozen_motes(pen, t, box, n=60, seed=0, c='#fff6dc', a=200):
    """THEIRS dust: motes hang still in the sun and only twinkle."""
    x0, y0, x1, y1 = box
    for i in range(n):
        x = x0 + _h(i, seed) * (x1 - x0); y = y0 + _h(i, seed + 1) * (y1 - y0)
        tw = max(0.0, math.sin(t * (1.1 + 2.3 * _h(i, seed + 2)) + 6.28 * _h(i, seed + 3))) ** 2
        r = 1.2 + 2.6 * _h(i, seed + 4)
        _R(pen, None, x, y, r * (1.6 + 2.0 * tw), [(0, c, a * (0.25 + 0.75 * tw)), (0.45, c, a * 0.4 * (0.3 + tw)), (1, c, 0)], clip=False)


def _theirs_live(cx, cam, xf, d0, st, vname, info):
    """THEIRS live layers: sun shafts with frozen twinkling motes, the clock loop, swimsuit drips, the hanging drop,
    the lantern's breath of light, the dawn_break stutter (via fx), the doorway's beam when Tess is in it."""
    L = []
    P = cx.P
    L += shaft_layer(cam, xf, d0, 'T:%s:%s' % (vname, cx.var), P, True, 44)[:1]
    # frozen motes in the sun shaft region (screen box from the window and its floor patch)
    win = [v3(WIN[0], WIN[3], D), v3(WIN[1], WIN[2], D), v3(WIN[0] - 0.4, 0.0, D - 2.5), v3(WIN[1] - 0.6, 0.0, D - 1.6)]
    pts = [cam.pt(xf.p(p)) for p in win if cam.dist(xf.p(p)) > 0.15]
    if pts:
        bx = (min(p[0] for p in pts) - 80, min(p[1] for p in pts) - 40, max(p[0] for p in pts) + 80, max(p[1] for p in pts) + 40)
        dep = sdep(cam, xf, d0, v3(WIN[0], 1.0, D - 1.2), 0.001)
        L.append(_live(dep, lambda pen, t: frozen_motes(pen, t, bx, 46, 31, '#fff2d0'), 'motes', blur=0))
    if 'clock' in info and cam.dist(xf.p(info['clock'][0])) > 0.25:
        L.append(clock_live(cam, xf, d0, info, st, 'theirs'))
    # swimsuit drips: each suit drips on its own period (the loop moves; the suits do not)
    if info.get('swim_drips'):
        drips = [(cam.pt(xf.p(p)), cam.px_per_m(xf.p(p)), i) for i, p in enumerate(info['swim_drips']) if cam.dist(xf.p(p)) > 0.2]
        if drips:
            dep = sdep(cam, xf, d0, info['swim_drips'][0], 0.002)

            def drip(pen, t):
                for (x, y), k, i in drips:
                    ph = ((t - 297.59) / 19.48 * 6 + i * 0.37) % 1.0
                    yy = y + k * 0.45 * ph ** 2.2
                    a = 230 if ph < 0.92 else 0
                    pen.fill(_blob(x, yy, 0.012 * k, 0.018 * k, 7, i, 0.15), '#e8f6ff', a)
                    pen.fill(oval(x - 0.004 * k, yy - 0.005 * k, 0.004 * k), '#ffffff', a)
            L.append(_live(dep, drip, 'drips', blur=0))
    # the lantern's warm breath (the only light that "lives" on the sill)
    if info.get('lantern') is not None and cam.dist(xf.p(info['lantern'])) > 0.2:
        lp = cam.pt(xf.p(info['lantern'] + v3(0, 0.14, 0))); k = cam.px_per_m(xf.p(info['lantern']))
        dep = sdep(cam, xf, d0, info['lantern'], 0.003)
        brk = cx.var == 'dawn_break'

        def lan(pen, t):
            f = 1.0
            if brk: f = 0.35 + 0.65 * (1.0 if _h(int(t * 14), 3) > 0.25 else 0.15)
            _R(pen, None, lp[0], lp[1], 0.45 * k, [(0, '#ffd9a0', 90 * f), (0.4, '#ffd9a0', 30 * f), (1, '#ffd9a0', 0)], clip=False)
        L.append(_live(dep, lan, 'lantern_glow', blur=0))
    # the drop under the window: hanging (with the room upside down inside it) or falling and splashing
    if info.get('drop') is not None and cam.dist(xf.p(info['drop'])) > 0.2 and vname in ('towel_floor', 'window', 'master', 'overhead', 'floor_prints'):
        L.append(drop_live(cam, xf, d0, st, info))
    # Tess's beam from the doorway down the stairs (when she is in it with the lamp)
    fl = [str(st.v('flashlight', tt)) for tt in (st.t0, st.t1)]
    if any(v.startswith('tess_doorway') or v.startswith('tess_on') for v in fl) and not str(cx.prop('doorway', '')).startswith('navy'):
        src = v3(2.93, DROP + 1.15, D - 0.1)
        if cam.dist(src) > 0.4:
            bl, b = beam_layers(cam, xf, d0, st, src, [(st.t0, v3(1.5, 0.6, 5.6)), (st.t0 + 1.5, v3(1.3, 0.3, 5.3))], seed=5,
                                spread=0.2, a=0.2, n_dust=40,
                                kfn=lambda t: 1.0 if not str(st.v('flashlight', t)).startswith('tess_running') else 0.0)
            L += bl
    return L


def drop_live(cam, xf, d0, st, info):
    """The drop: drips tap the towel; at 335.25-337.09 one rises and hangs (the room drawn upside down inside it); the
    same drop falls again in the loop."""
    p = info['drop']
    x, y = cam.pt(xf.p(p)); k = cam.px_per_m(xf.p(p))
    tx, ty = cam.pt(xf.p(info['towel']))
    dep = sdep(cam, xf, d0, p, 0.004)
    d_raw = str(st.raw.get('drop', 'none'))

    def draw(pen, t):
        st_ = str(st.v('drop', t))
        r = 0.022 * k
        if st_.startswith('hanging') or d_raw.startswith('hanging'):
            yy = y + 0.004 * k * math.sin(t * 2.0)
        elif d_raw.startswith('rising'):
            u = ease_in_out(prog(t, 335.25, 337.09)); yy = lerp(ty, y, u)
        else:
            ph = ((t - 297.59) % 1.6) / 1.6
            yy = lerp(y - 0.25 * k, ty, ph ** 2)
            if ph > 0.95:
                _R(pen, None, tx, ty, 0.05 * k, [(0, '#e8f6ff', 160), (1, '#e8f6ff', 0)], sy=0.3, clip=False)
        drop = S1._drop_path(x, yy, r, 1.35)
        pen.fill(drop, '#cfe6f2', 230)
        # the room upside down inside it: a tiny warm window and floor band, inverted
        pen.cv.save(); pen.cv.clipPath(drop, skia.ClipOp.kIntersect, True)
        pen.fill(rect(x - r, yy - r * 1.4, 2 * r, r * 0.9), '#c99660', 230)
        pen.fill(rect(x - r * 0.3, yy + r * 0.1, r * 0.6, r * 0.5), '#fff2d0', 230)
        pen.cv.restore()
        pen.line(drop, max(1.0, 0.002 * k), '#6a8090', 200)
        pen.fill(oval(x - r * 0.35, yy - r * 0.2, r * 0.22), '#ffffff', 230)
    return _live(dep, draw, 'drop', blur=0)


def theirs_view(vname, var, st, shot, extra=None):
    cx = CabinCtx('theirs', var or 'dawn', st, st.t0)
    pos, look, fov, roll = THEIRS_CAMS[vname]
    cam = Cam3(pos, look=look, fov=fov, roll=roll)
    d0 = max(0.8, cam.dist(v3(1.3, 0.9, 5.2)))
    L, sc, info, xf = cabin_layers(cx, cam, vname, d0)
    L += _theirs_live(cx, cam, xf, d0, st, vname, info)
    if extra: L += extra(cx, cam, xf, d0, info)
    an = _theirs_anchors(cam, xf, d0)
    return _sp('cabin_dawn/' + vname, L, an, None, 1.0, 0.0, None, dict(info, cam3=cam, d0=d0, xf=xf, model=sc, world='theirs'))


def _reg_theirs(vname):
    @view('cabin_dawn', vname)
    def _v(var, st, shot, vname=vname):
        return theirs_view(vname, var, st, shot)
    return _v


for _vn in THEIRS_CAMS:
    _reg_theirs(_vn)


# ====================================================================== the stairs (set 'stairs'): the crossing, inside the glass
STAIRS_CAMS = {
    # name: (pos, look, fov, roll) in stairs-local coords (x across, y up from our floor, z down the stairs)   4.3 views
    'down': ((0.0, 1.5, -0.75), (0.0, -1.65, 2.35), 64.0, 0.0),        # 1 down from our doorway
    'up': ((0.12, -1.2, 2.95), (0.0, 0.85, -0.1), 64.0, 0.0),          # 2 up from the dawn cabin to the doorway (Tess in it)
    'low': ((0.18, -1.5, 2.5), (0.0, 0.1, 0.35), 72.0, 0.0),           # low angle up the stairs
    'treads': ((0.02, -0.05, 0.3), (0.0, -0.7, 1.05), 62.0, 0.0),      # 4 feet on treads
    'ots_climb_down': ((0.16, 0.95, -0.4), (0.0, -1.2, 1.8), 68.0, 0.0),   # 5 OTS going down (290.7)
    'ots_climb_up': ((0.12, -0.95, 2.15), (0.0, 0.55, -0.05), 68.0, 0.0),  # 5 OTS climbing (546-600)
    'pov_down': ((0.0, 0.15, 0.85), (0.0, -1.05, 1.75), 74.0, 0.0),    # 6 POV looking down at the step below
    'railing': ((1.55, -0.25, 1.05), (0.0, -0.65, 1.0), 60.0, 0.0),    # along the railing (the hand through the balusters)
}


def stairs_view(vname, var, st, shot):
    var = var or 'stairs'
    t0 = st.t0
    key = vname
    if vname == 'ots_climb': key = 'ots_climb_down' if t0 < 400 else 'ots_climb_up'
    pos, look, fov, roll = STAIRS_CAMS[key]
    cam = Cam3(pos, look=look, fov=fov, roll=roll)
    dstate = str(st.v('doorway', t0))
    sc = stairs_scene('red' if var == 'red' else 'stairs')
    _stairs_lights(sc, var, dstate)
    _doorway_top(sc, var, st, dstate)
    d0 = max(0.6, cam.dist(v3(0.0, -0.8, 1.2)))
    bands = _bands(d0, 0.7, 1.5)
    L = sc.layers(cam, d0, bands, 'v2:stairs:%s:%s:%s' % (key, var, dstate[:4]))
    bandmap(cam, bands, L)
    L += _stairs_live(sc, cam, d0, st, var, key)
    an = {}
    for k in range(1, N_STEPS + 1):
        P = v3(0.0, -RISE * k, ST_T * (k - 0.5))
        if cam.dist(P) > 0.15:
            x, y, h, dep = cam.anchor(P, 1.72, d0); an['tread%d' % k] = Anchor(x, y, dep, h)
    for nm, P, hh in (('doorway', v3(0, 0.0, 0.0), 1.68), ('tess_doorway', v3(0, 0.0, -0.15), 1.68), ('bottom', v3(0, -1.8, 2.3), 1.72),
                      ('noah_bunk', v3(0.95, -1.8 + B_LOW, 2.9), 1.5), ('you_stairs', v3(0, -RISE * 3, ST_T * 2.5), 1.76),
                      ('queen_tread8', v3(0, -RISE * 8, ST_T * 7.5), 1.92), ('queen_below', v3(0, -RISE * 4, ST_T * 3.5), 1.92)):
        if cam.dist(P) > 0.15:
            x, y, h, dep = cam.anchor(P, hh, d0); an[nm] = Anchor(x, y, dep, h)
    return _sp('stairs/' + vname, L, an, None, 1.0, 0.0, None, dict(cam3=cam, d0=d0, xf=ID, model=sc, world='stairs'))


def _stairs_lights(sc, var, dstate):
    red = var == 'red'
    sc.light((0.0, 1.2, -0.3), '#9fa8ff' if not red else '#c2185b', 90 if not dstate.startswith('navy') else 30, 1.0, name='moon_top')
    sc.light((0.0, -1.5, 2.6), '#ffcf8a' if not red else '#ff2d55', 150, 1.3, name='gold_bottom')
    sc.light((0.6, -0.6, 1.0), '#c63449' if not red else '#ff2d55', 60 if not red else 110, 1.4, name='red_edge_fill')


def _doorway_top(sc, var, st, dstate):
    """The doorway at the top seen from the stairs: our blue cabin through the white frame (or navy-dark, or red)."""
    gw = MIR[1] - MIR[0]

    def view_in(pen, w, h):
        if dstate.startswith('navy'):
            _vgrad(pen, w, h, ['#090b1e', '#121634', '#0a0c1a'])
        elif var == 'red' or dstate.startswith('red'):
            _vgrad(pen, w, h, ['#5a1640', '#ae3a6a', '#3a0a20'])
        else:
            _vgrad(pen, w, h, ['#3a3d72', '#5a5fa8', '#454985'])
            for i in range(3): pen.fill(rect(0, 14 + i * 34, w, 5), '#2b2d57', 230)
            _R(pen, None, w * 0.55, h * 0.4, w, [(0, '#fff3d6', 90), (1, '#ffd58a', 0)], clip=False)
    sc.plane((-gw / 2 + 0.06, MIR_H - 0.12, -0.05), (1, 0, 0), (0, -1, 0), (gw - 0.12) * 100, (MIR_H - 0.12) * 100, view_in, -10,
             'dview', 'door')


def _stairs_live(sc, cam, d0, st, var, key):
    """Fog bands drifting, falling dust, the red edge glow breathing (2.4 s), the gold glow from below."""
    L = []
    red = var == 'red'
    edges = []
    for k in range(1, N_STEPS + 1):
        y = -RISE * k; z0 = ST_T * (k - 1)
        a, b = v3(-ST_W / 2, y, z0), v3(ST_W / 2, y, z0)
        if cam.dist(a) > 0.1 and cam.dist(b) > 0.1:
            edges.append((cam.pt(a), cam.pt(b), cam.px_per_m((a + b) / 2), k))
    if edges:
        dep = sdep(cam, ID, d0, v3(0, -RISE * 4, ST_T * 3.5), 0.004)
        glow = '#ff4060' if not red else '#ff2d55'

        def eg(pen, t):
            br = 0.65 + 0.35 * math.sin(t * 2 * math.pi / 2.4)
            for (pa, pb, k, n) in edges:
                pen.seg(pa, pb, max(2.0, 0.05 * k), glow, int(70 * br))
                pen.seg(pa, pb, max(1.0, 0.018 * k), '#ffb0bc', int(150 * br))
        L.append(_live(dep, eg, 'edge_glow', blur=None))
    # fog bands (big soft ellipses drifting) and falling dust
    gp = cam.pt(v3(0.0, -1.8, 2.4)) if cam.dist(v3(0.0, -1.8, 2.4)) > 0.2 else (960, 900)
    fogc = SPAL['red' if red else 'stairs']['fog']

    def fog(pen, t):
        for i in range(5):
            x = (i * 520 + t * (14 + 6 * i)) % 2600 - 340
            y = 300 + i * 140 + 30 * math.sin(t * 0.3 + i)
            _R(pen, None, x, y, 520, [(0, fogc, 60), (0.5, fogc, 24), (1, fogc, 0)], sy=0.22, clip=False)
        _R(pen, None, gp[0], gp[1], 700, [(0, '#ffcf8a' if not red else '#ff2d55', 60 + 14 * math.sin(t * 1.3)), (1, '#ffcf8a', 0)],
           sy=0.6, clip=False)
    L.append(_live(max(0.5, sdep(cam, ID, d0, v3(0, -1.0, 1.2), 0.01)), fog, 'fog', blur=None))
    L.append(_live(max(0.45, sdep(cam, ID, d0, v3(0, -0.6, 0.8), 0.012)),
                   lambda pen, t: motes(pen, t, (-100, -100, 2020, 1180), 60, 311, None, '#e8dcff' if not red else '#ffb0c0', 0.16,
                                        fall=12, speed=(3, 8)), 'falling_dust', blur=0))
    return L


def _reg_stairs(vname):
    @view('stairs', vname)
    def _v(var, st, shot, vname=vname):
        return stairs_view(vname, var, st, shot)
    return _v


for _vn in ('down', 'up', 'low', 'treads', 'ots_climb', 'pov_down', 'railing'):
    _reg_stairs(_vn)
