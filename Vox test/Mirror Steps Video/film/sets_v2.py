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
                  clock_theirs, FRAME, NEAR, STEP_XY, EIGHTH, PANE, FW, MPIV, RED, RED_HI, RED_DK, GLOW, CORE, FALL, grass)
from engine.core import (Pen, col, mix, rgb, poly, smooth, rect, rrect, oval, union, minus, moved, clamp, lerp, prog, ease,
                         ease_in_out, ease_out_cubic, ease_in_cubic, ease_out_back, noise1, hash01, text, text_width, LINE)
from engine.scene import Layer
from engine.room3d import Cam3, Scene3, Xf, v3, norm, ID, clip_poly_near, draw_plane

V1VIEWS = dict(VIEWS)          # the v1 views as they were before v2 registered over some names (aliases build on these)

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
    'night': dict(wall='#50559a', wall_dk='#2e3166', wall_lt='#6e74bc', seam='#1d1f44', rail='#3a3d72',
                  floor='#625e94', floor_dk='#3a3762', floor_lt='#7e7ab8', floor_seam='#25223f', dust='#9a96c8',
                  roof='#232450', roof_dk='#141534', beam='#363870', beam_lt='#7478c0',
                  wood='#7a6488', wood_dk='#4e3f66', wood_lt='#a08ab8', mat='#9aa0d0', mat_st='#5c6198', mat_dk='#5a5f92',
                  paint='#b9bdd8', paint_dk='#8a8eb0', metal='#8a90b4', sky0='#2c3a7c', sky1='#5a5fa8', moon='#cfd8ff',
                  key='#9fa8ff', warm='#ffd58a', pool='#f0a84e', outline='#14152e', paper='#cfd0e4', tape='#cdbf7a',
                  red_glint=0.0, glow_door=0.0, red=0.0),
    'theirs': dict(wall='#dcb878', wall_dk='#b89050', wall_lt='#f2d498', seam='#7e5a2e', rail='#c8a060',
                   floor='#d2b070', floor_dk='#ae8c4e', floor_lt='#ead09a', floor_seam='#7a5a30', dust='#f2e0b0',
                   roof='#b08c50', roof_dk='#8a6a38', beam='#bc9858', beam_lt='#e6c47e',
                   wood='#c49e5e', wood_dk='#987440', wood_lt='#e2c080', mat='#ece6d2', mat_st='#cfc096', mat_dk='#b8a880',
                   blanket1='#3f8f6a', blanket2='#3f6fa8',
                   paint='#f4ead6', paint_dk='#d4c6a8', metal='#b9b2a4', sky0='#f0a888', sky1='#ffd8a8', moon='#fff2d0',
                   key='#ffe2a8', warm='#ffe2a8', pool='#ffd59a', outline='#3a2414', paper='#f8f0dc', tape='#e8d79a',
                   red_glint=0.0, glow_door=0.0, red=0.0),
}
PAL['red'] = dict(PAL['night'], wall='#7a3c80', wall_dk='#34123a', wall_lt='#9a52a8', seam='#14040e', rail='#3a1236',
                  floor='#642c64', floor_dk='#2c0e2e', floor_lt='#8a3e8a', floor_seam='#10030a', dust='#8a4a7e',
                  roof='#1e0716', roof_dk='#12040c', beam='#2e0c26', beam_lt='#6e2a62',
                  wood='#5a204e', wood_dk='#32102c', wood_lt='#7e3470', mat='#7a3a6e', mat_st='#52244a', mat_dk='#4a1e44',
                  paint='#c890b4', paint_dk='#8a5a7c', metal='#8a5a7e', sky0='#1e0820', sky1='#3e1238', moon='#ff9ab4',
                  key='#ff2d55', warm='#ff5a7a', pool='#ff2d55', outline='#0e0208', paper='#c8a0b8', tape='#a07080', red=1.0)
PAL['after'] = dict(PAL['night'])
# MEMORY (the real past, sepia paper): cream #f1e2c4, tan #c9a878, faded teal #6f9a96, faded orange #d08a52, dark #4a3a2c
PAL['past_day'] = dict(PAL['theirs'], wall='#c9a878', wall_dk='#9a7a58', wall_lt='#e8d4ae', seam='#6a5038', rail='#b8946a',
                       floor='#b89a70', floor_dk='#8a6a48', floor_lt='#dcc49a', floor_seam='#5a4430', dust='#f1e2c4',
                       roof='#8a6a48', roof_dk='#6a5038', beam='#a07e58', beam_lt='#d8bc90',
                       wood='#a88660', wood_dk='#7a5c3e', wood_lt='#d0b088', mat='#ece0c4', mat_st='#c9b08a', mat_dk='#b8a07a',
                       paint='#f1e2c4', paint_dk='#d0bc98', metal='#a89a84', sky0='#e8d8b8', sky1='#f8eedc', moon='#fff8e8',
                       key='#f8e8c8', warm='#fff0d0', pool='#f1e2c4', outline='#3a2c20', paper='#f6ead2', tape='#d8c49a',
                       blanket1='#d08a52', blanket2='#6f9a96', swim=['#6f9a96', '#d08a52', '#a08a7a', '#d8c08a'], cubby_cols=['#6f9a96', '#d08a52', '#c9a878', '#8a7a6a', '#6f9a96', '#7a9a6a'])
PAL['past_morning'] = dict(PAL['past_day'], wall='#c2a67e', floor='#b09470', sky0='#e0dcc8', sky1='#f0ead8', key='#eee6d0')
PAL['past_night'] = dict(PAL['past_day'], wall='#6a5440', wall_dk='#4a3a2c', wall_lt='#9a7a58', seam='#2a2018', rail='#5a4634',
                         floor='#5e4a38', floor_dk='#40322a', floor_lt='#8a6e52', floor_seam='#241a14', dust='#a08a6a',
                         roof='#3a2e24', roof_dk='#2a2018', beam='#4a3a2c', beam_lt='#7a6046',
                         wood='#7a5e44', wood_dk='#4e3a2a', wood_lt='#a08060', mat='#c9b08a', mat_st='#9a8060', mat_dk='#8a7050',
                         paint='#d8c4a0', paint_dk='#a89070', sky0='#2a2420', sky1='#4a4036', moon='#f1e2c4', key='#d8c4a0',
                         warm='#ffd9a0', pool='#ffd9a0', outline='#1a120c', paper='#d8c4a0')
PAL['theirs_queen'] = dict(PAL['theirs'])
PAL['theirs_break'] = dict(PAL['theirs'], wall='#c8aa70', wall_dk='#9a7a44', floor='#b89a60', red=0.25)

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
        self.past = side == 'past'                  # memory: the real cabin 14 years ago (OURS layout, lived-in, sepia)
        self.ours = side in ('ours', 'past')        # OURS geometry (not flipped), the mirror at the mirror spot
        self.now = side == 'ours'                   # tonight: dust, the phone, the padlock, the demolition sticker
        self.dressed = side in ('theirs', 'past')   # lived-in: made bunks, curtains, the lantern, full cubbies
        self.dark = side == 'ours' or var in ('sepia_night',)
        if self.past: self.P = PAL['past_' + {'sepia_night': 'night', 'sepia_morning': 'morning'}.get(var, 'day')]
        self.refl_scene = None
        self.tilt = 0.0                 # the mirror's in-plane tilt (deg): -13 when you tilt it (146.3 s)
        self.glass_mode = 'reflect'     # 'reflect' (the room in the glass) | 'clear' (the other side shows through)
        self.refl_alpha = 0.2

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
        # each strip reaches 12 % of a strip into its neighbours: under a dolly the bands slide a little apart, and the
        # overlap (hidden under the nearer strip) keeps the seam closed
        ov = 0.12 / n
        if along_t:
            t0, t1 = max(0.0, h * (i / n - ov)), min(h, h * ((i + 1) / n + ov))
            tc = h * (i + 0.5) / n

            def d(pen, ww, hh, t0=t0, h_=h):
                pen.cv.translate(0, -t0); draw(pen, w, h_)
            sc.plane(O + V * (t0 / 100), U, V, w, t1 - t0, d, order, '%s%d' % (name, i), tag, two_sided,
                     centre=O + V * (tc / 100) + U * (w / 200), readable=False)
        else:
            s0, s1 = max(0.0, w * (i / n - ov)), min(w, w * ((i + 1) / n + ov))
            scn = w * (i + 0.5) / n

            def d(pen, ww, hh, s0=s0, w_=w):
                pen.cv.translate(-s0, 0); draw(pen, w_, h)
            sc.plane(O + U * (s0 / 100), U, V, s1 - s0, h, d, order, '%s%d' % (name, i), tag, two_sided,
                     centre=O + U * (scn / 100) + V * (h / 200), readable=False)


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
            if cx.now or (cx.past and cx.dark):
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
        if not ours:                                    # THEIRS only: the doorway 1.8 m up the back wall
            pen.cv.clipPath(_doorway_hole_cm(DROP), skia.ClipOp.kDifference, True)
        back_wall(pen, w, h)

    sc.plane((0, HR, D), (1, 0, 0), (0, -1, 0), W * 100, HR * 100, back_wall_holed, -100, 'back_wall', wall_tag, readable=False)

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
        if cx.now:
            _sign_text(pen, 'EXIT', (x0 + x1) / 2, yt - 16, 7, '#d9e0ff', 900, 200)
    sc.plane((W, HR, 0), (-1, 0, 0), (0, -1, 0), W * 100, HR * 100, front_wall, -100, 'front_wall', wall_tag, readable=False)

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
        if cx.now:
            pen.fill(rrect(10, 33, 100, 196, 8), '#000000', 70)          # mattress stack
            if cx.mirror_state not in ('absent',):
                pen.fill(rrect(MIR[0] * 100 - 4, (D - MIR_LEAN - 0.04) * 100, (MIR[1] - MIR[0]) * 100 + 8, (MIR_LEAN + 0.04) * 100, 4), '#000000', 110)
        if cx.now or (cx.past and cx.dark):
            # the dust film: smooth, pale, thicker along the walls; scuffs only near the door
            pen.texture(r, 'grunge', 0.22, 'screen', 0.4)
            _hgrad(pen, w, h, [(0, P['dust'], 70), (0.15, P['dust'], 0), (0.85, P['dust'], 0), (1, P['dust'], 70)])
            # the moon patch through the window (projected window onto the floor along the moonlight)
            for poly_, a in _moon_patch_floor():
                pen.fill(poly(poly_), P['key'], int(a * 2.2))
                pen.fill(poly(poly_), '#eef1ff', int(a * 1.6))
        else:
            _hgrad(pen, w, h, [(0, P['floor_dk'], 90), (0.2, P['floor_dk'], 0)])
            for poly_, a in _moon_patch_floor(theirs=True):
                pen.fill(poly(poly_), P['warm'], int(a * 2.4))
                pen.fill(poly(poly_), '#fff6e0', int(a * 1.8))
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
    if cx.past:
        if cx.dark:
            sc.light((wx + 0.3, 1.1, D - 0.2), '#ffd9a0', 140, 1.1, name='lantern')
            sc.light((2.8, 2.2, 3.2), '#8a6a48', 50, 2.6, name='ambient')
        else:
            sc.light((wx, 1.5, D - 0.3), '#fff2d8', 110, 1.3, name='window')
            sc.light((2.8, 2.3, 3.0), '#f1e2c4', 60, 3.0, name='fill')
        return
    if cx.ours:
        moon_a = 0.6 if var in ('after', 'phone_glow') else (0.35 if var == 'red' else 1.0)
        sc.light((wx, 1.45, D - 0.25), '#aab2ff', 120 * moon_a, 1.1, name='moon_window')
        sc.light((wx + 0.45, 0.25, 4.6), '#aab4ff', 55 * moon_a, 1.1, name='moon_floor')
        sc.light((4.0, 1.3, 0.6), '#6a72c8', 45 * moon_a, 1.5, name='door_fill')
        sc.light((2.8, 2.6, 3.2), '#5a5fa8', 40 * moon_a, 2.6, name='ambient')
        if cx.st is not None and _flash_on(cx.st, cx.t) and var in ('night', 'flash', 'doorway_glow') and cx.mirror_state != 'absent':
            sc.light((2.66, 0.85, 5.75), '#ffd58a', 55, 0.8, name='beam_bounce')
        if var == 'doorway_glow' or (cx.mirror_state == 'doorway' and var not in ('red',)):
            sc.light((2.66, 0.75, 6.0), '#ffc070', 85, 1.0, name='doorway_gold')
            sc.light((2.66, 0.1, 5.3), '#ffb060', 60, 0.8, name='doorway_floor')
        if var == 'red':
            sc.light((2.66, 0.8, 6.0), '#ff2d55', 75, 0.75, name='red_pour')
            sc.light((2.66, 0.05, 5.0), '#ff2d55', 50, 0.6, name='red_floor')
            sc.light((2.8, 2.4, 3.0), '#9a4ab0', 70, 2.6, name='magenta_fill')
        if var in ('after', 'phone_glow'):
            sc.light((2.3, 0.18, 3.3), '#ffd58a', 140, 1.0, name='flashlight_floor')
            sc.light((3.4, 0.4, 5.0), '#f0a84e', 70, 1.2, name='pool_bounce')
        if var == 'phone_glow':
            sc.light((2.2, 1.0, 4.4), '#c8d8ff', 70, 0.7, name='phone')
    else:
        sun = 0.75 if var == 'dawn_break' else 1.0
        sc.light((wx, 1.5, D - 0.3), '#ffcc66', 70 * sun, 1.0, name='sun_window')
        sc.light((wx - 0.5, 0.2, 4.4), '#ffd070', 70 * sun, 1.1, name='sun_floor')
        sc.light((2.8, 2.3, 3.0), '#ffcf8a', 55 * sun, 3.0, name='warm_fill')
        sc.light((2.66, 2.6, D - 0.2), '#9fa8ff', 55, 0.7, name='doorway_blue')
        if var == 'dawn_break':
            sc.light((2.66, 2.4, 5.6), '#ff3b5c', 45, 1.3, name='red_leak')


def _outside_front(sc, cx):
    """What the open front door shows: the moonlit path, the pines and (OURS) the mess hall 40 m away with its porch
    light; (THEIRS) the wash house in early sun."""
    P = cx.P; ours = cx.ours
    x0, x1, h = DOOR

    def scene(pen, w, h_):
        if cx.dark:
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
        pen.fill(rect(0, 0, w, h_), P['floor_dk'] if cx.dark else '#c8b47a')
        pen.texture(rect(0, 0, w, h_), 'asphalt', 0.3, 'overlay', 0.3)
        pen.fill(rect(w * 0.42, 0, w * 0.16, h_), P['floor'] if cx.dark else '#d8c48a')
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
    _bunk_frame(sc, P, *LBUNK, made=cx.dressed, ticking=True, noah=False, ours=ours, name='lbunk',
                blanket=P.get('blanket2', '#3f6fa8'), room_x=LBUNK[1] - 0.04)
    _bunk_frame(sc, P, *NBUNK, made=cx.dressed, ticking=True, noah=True, ours=ours, name='nbunk',
                blanket=P.get('blanket1', '#c0563a'))
    if cx.now:
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
            pen.fill(rect(0, 0, w, h), '#d8cc98' if cx.dressed else _lt(P['tape'], 0.15), 240)
            pen.line(rect(0, 0, w, h), 0.3, _dk(P['tape'], 0.4), 120)
            _sign_text(pen, nm, w / 2, h * 0.78, 3.6, '#2a2440', 800)
        sc.plane((W - 0.341, y, z + 0.06), (0, 0, -1), (0, -1, 0), 12, 4.6, label, 0.03, 'cubbylabel', 'cubby')
        # contents: theirs full (clothes, comics, a flashlight, a canteen); ours empty, dust (NOAH: a cobweb)
        yb = cy0 + 0.02 if row == 1 else (cy0 + cy1) / 2 + 0.01
        zc0 = cz0 + colm * cw + 0.03
        if cx.dressed:
            cols = P.get('cubby_cols', ['#3f8fa0', '#d84a4a', '#e0b84a', '#6a4fa8', '#4aa86a', '#2f8a3a'])
            sc.box(W - 0.3, yb, zc0, W - 0.04, yb + 0.12, zc0 + cw - 0.06, dict(all=cols[k], top=_lt(cols[k], 0.2), left=_lt(cols[k], 0.1)),
                   0.01, 'cubbyclothes', 'cubby', P['outline'], 0.6)
            if k % 2 == 0:
                sc.box(W - 0.28, yb + 0.12, zc0 + 0.04, W - 0.06, yb + 0.15, zc0 + 0.24, dict(all='#f2e6c0', top='#e85a3a', left='#f4d040'),
                       0.01, 'comics', 'cubby', P['outline'], 0.5)
        elif nm == 'NOAH' and cx.now:
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
        if cx.dark:
            _vgrad(pen, w, h, [P['sky0'], P['sky1'], mix(P['sky1'], '#ffffff', 0.15)])
            moon_xy = (w * 0.62, h * 0.28)
            _R(pen, None, moon_xy[0], moon_xy[1], 160, [(0, P['moon'], 120), (0.3, P['moon'], 40), (1, P['moon'], 0)], clip=False)
            pen.fill(oval(moon_xy[0], moon_xy[1], 18), P['moon']); pen.fill(oval(moon_xy[0] + 5, moon_xy[1] - 4, 15), '#ffffff', 150)
            for i in range(9):
                pine(pen, w * (i + 0.3 * _h(i, 3)) / 8, h * 0.98, h * (0.45 + 0.35 * _h(i, 4)), i, _dk(P['sky0'], 0.4), P['key'], 60, 0, 8, 0.4)
            pen.fill(rect(0, h * 0.94, w, h * 0.06), _dk(P['sky0'], 0.5))
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
        if cx.now:   # the torn screen: mesh with a jagged hole and a curled flap
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
    if cx.dressed:
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
        info['lantern'] = v3(x1 - 0.3, y0, D - 0.08)
    else:
        info['lantern'] = None
    # ---------------------------------------------------------------- the clock on the back wall
    ckx, cky, ckr = CLOCK

    def clock_face(pen, w, h):
        r = w / 2
        sec = 6 * 3600 + 59 * 60 + 40 if cx.dressed else (23 * 3600 + 59 * 60 + 5)
        pen.fill(oval(r + 0.6, r + 1.2, r), '#000000', 90)
        pen.fill(oval(r, r, r), P['metal']); pen.line(oval(r, r, r), 0.7, P['outline'])
        pen.fill(oval(r, r, r * 0.86), '#f2ecd8' if cx.dressed else '#c6c8e4')
        for k in range(60):
            a = k * math.pi / 30
            r0 = 0.72 if k % 5 == 0 else 0.8
            pen.seg((r + math.cos(a) * r * r0, r + math.sin(a) * r * r0), (r + math.cos(a) * r * 0.84, r + math.sin(a) * r * 0.84),
                    0.7 if k % 5 == 0 else 0.25, '#2a2a3a', 230)
        for k in range(1, 13):
            a = k * math.pi / 6 - math.pi / 2
            _sign_text(pen, str(k), r + math.cos(a) * r * 0.58, r + math.sin(a) * r * 0.58 + 1.0, 2.6, '#2a2a3a', 800)
        _sign_text(pen, 'CEDAR LAKE', r, r * 1.38, 1.6, '#5a4a3a' if cx.dressed else '#4a4a6a', 800)
    sc.plane((ckx - ckr, cky + ckr, D - 0.03), (1, 0, 0), (0, -1, 0), ckr * 200, ckr * 200, clock_face, -60, 'clock', 'clock')
    info['clock'] = (v3(ckx, cky, D - 0.035), ckr)
    # ---------------------------------------------------------------- left wall: CABIN RULES sign (front), pennant, calendar
    def rules(pen, w, h):
        pen.fill(rect(0, 0, w, h), '#e8dcb8' if cx.dressed else P['paper']); pen.line(rect(0, 0, w, h), 0.8, P['outline'])
        pen.texture(rect(0, 0, w, h), 'paper', 0.4, 'overlay', 0.15)
        if cx.now: pen.texture(rect(0, 0, w, h), 'grunge', 0.35, 'multiply', 0.2)
        _sign_text(pen, 'CABIN RULES', w / 2, 9, 5.2, '#2a3a6a' if cx.now else '#1a4a8a', 900)
        pen.seg((6, 12), (w - 6, 12), 0.5, '#c0302a', 220)
        for i, s in enumerate(('LIGHTS OUT 9:30', 'NO FOOD IN CABINS', 'SHOES OFF', 'BE KIND')):
            _sign_text(pen, s, 6, 20 + i * 7.2, 3.6, '#2a2a3a', 700, 230, 0, 'left')
        if cx.dressed:
            pen.fill(oval(w - 9, h - 9, 5), '#f0c030'); _sign_text(pen, ':)', w - 9, h - 7.5, 4.0, '#3a2a10', 900)
    sc.plane((0.003, 1.75, 0.9), (0, 0, 1), (0, -1, 0), 46, 54, rules, -50, 'rules', 'decor')

    def calendar(pen, w, h):
        pen.fill(rect(0, 0, w, h), P['paper'] if cx.now else '#fbf6ea'); pen.line(rect(0, 0, w, h), 0.6, P['outline'])
        _vgrad(pen, w, h * 0.42, ['#3a6aa0' if cx.dressed else '#4a5a8e', '#6ab0c8' if cx.dressed else '#6a78a8'])
        for i in range(5):
            pine(pen, w * (i + 0.5) / 5, h * 0.4, h * 0.22, i, '#2a4a3a' if cx.dressed else '#2a2f5a', None, 0, 0, 6, 0.4)
        _sign_text(pen, 'JULY', w / 2, h * 0.52, 4.6, '#c0302a', 900)
        for r_ in range(5):
            for c_ in range(7):
                gx, gy = 3 + c_ * (w - 6) / 7, h * 0.57 + r_ * (h * 0.4) / 5
                pen.line(rect(gx, gy, (w - 6) / 7, h * 0.08), 0.15, '#6a6a7a', 160)
                if r_ * 7 + c_ < 18: pen.seg((gx + 0.5, gy + 0.5), (gx + (w - 6) / 7 - 0.5, gy + h * 0.08 - 0.5), 0.3, '#c0302a', 150)
        if ours: pen.texture(rect(0, 0, w, h), 'grunge', 0.4, 'multiply', 0.2)
    if ours: sc.plane((3.18, 1.82, D - 0.01), (1, 0, 0), (0, -1, 0), 30, 44, calendar, -50, 'calendar', 'decor')

    def pennant(pen, w, h):
        tri = poly([(0, 0), (w, h * 0.5), (0, h)])
        pen.fill(tri, '#3f7a4a' if cx.dressed else '#3a5a6a'); pen.line(tri, 0.6, P['outline'])
        _sign_text(pen, 'CEDAR LAKE', w * 0.38, h * 0.6, 4.2, '#f4f0e0' if cx.dressed else '#c8cce8', 900)
        pen.fill(rect(-2, -2, 3, h + 4), '#8a6a40')
    if ours: sc.plane((3.7, 2.08, D - 0.01), (1, 0, 0), (0, -1, 0), 64, 24, pennant, -50, 'pennant', 'decor')
    # ---------------------------------------------------------------- front-left: broom, mattress stack (tonight only)
    for i in (range(4) if cx.now else ()):
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
        pen.fill(oval(pb[0], pb[1] + 0.045 * k, 0.035 * k, 0.045 * k), '#c8c8d8' if cx.now else '#fff8e0', 230)
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
    if cx.now: sc.custom((0.7, 2.92, 6.0), nest, 0, 'nest', 'decor')
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
    xm_ = (x0 + x1) / 2
    info['phone_spot'] = (v3(xm_ - 0.18, y0 + 0.003, D - 0.05), v3(xm_ - 0.14, y0 + 0.004, D - 0.12))
    if False:

        def phone(pen, w, h):
            pen.fill(rrect(0, 0, w, h, 1.2), '#1a1c2c'); pen.line(rrect(0, 0, w, h, 1.2), 0.35, '#7a80b0')
            _L(pen, rrect(0.5, 0.5, w - 1, h - 1, 1.0), 0, 0, w, h, ['#20284a', '#06070e', '#141a34'])
            _L(pen, poly([(0, h * 0.2), (w, h * 0.05), (w, h * 0.15), (0, h * 0.32)]), 0, 0, 0, h, [(0, '#dfe6ff', 0), (0.5, '#dfe6ff', 90), (1, '#dfe6ff', 0)])
            if red: _R(pen, None, w * 0.6, h * 0.35, w * 0.7, [(0, GLOW, 160), (1, GLOW, 0)], clip=False)
        pass
    # ---------------------------------------------------------------- THEIRS extras: swimsuits, drawings, duffel, polaroid, towel+drop, shoe
    if cx.dressed:
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
        if cx.now:
            r = rect(w * 0.18, h_ * 0.26, w * 0.64, 26)
            pen.fill(r, '#ff7a1a'); pen.line(r, 0.6, '#3a1a08')
            _sign_text(pen, 'DEMOLITION', w / 2, h_ * 0.26 + 11, 6.4, '#1a0a04', 900)
            _sign_text(pen, 'SAT 7:00 AM · KEEP OUT', w / 2, h_ * 0.26 + 20, 3.4, '#1a0a04', 800)
    # outside face: seen from z < 0 looking +z with the door swung toward -z: origin at the hinge top, U along dirv
    sc.plane((x1, h, 0.0), dirv, (0, -1, 0), (x1 - x0) * 100, h * 100, door_out, 0, 'door', 'door')
    info['door'] = v3((x0 + x1) / 2, 0, 0)


# ====================================================================== the mirror (OURS), its reflection, the doorway
def mirror_plane(tilt=0.0):
    """(O, U, V, w_cm, h_cm, normal): the leaning mirror's front plane, origin at the frame's top-left; tilt (deg, the
    v1 sense: negative = top to the left) turns it about its centre in its own plane."""
    yt = math.sqrt(MIR_H ** 2 - (MIR_LEAN - 0.02) ** 2)
    O = v3(MIR[0], yt, D - 0.02)
    V = norm(v3(0, -yt, -(MIR_LEAN - 0.02)))
    U = v3(1, 0, 0)
    n = norm(np.cross(U, V))           # pointing into the room (-z, a little up)
    w, h = (MIR[1] - MIR[0]) * 100, MIR_H * 100
    if tilt:
        a = math.radians(-tilt)
        C = O + U * (w / 200) + V * (h / 200)
        U2 = U * math.cos(a) + V * math.sin(a); V2 = -U * math.sin(a) + V * math.cos(a)
        O = C - U2 * (w / 200) - V2 * (h / 200); U, V = U2, V2
    return O, U, V, w, h, n


MFW = 6.0          # frame width cm


def mirror_glass_pts(grow=0.0, tilt=0.0):
    """3D corners of the glass (inside the frame)."""
    O, U, V, w, h, n = mirror_plane(tilt)
    g = MFW - grow
    return [O + U * (g / 100) + V * (g / 100), O + U * ((w - g) / 100) + V * (g / 100), O + U * ((w - g) / 100) + V * ((h - g) / 100),
            O + U * (g / 100) + V * ((h - g) / 100)]


def mirror_local_H(cam, xf=ID, tilt=0.0):
    """Homography: v1 mirror-local px (PANE 300..1620 x -1092..2252, the lipstick steps' space) -> design px for this
    camera. The pane maps onto the glass rectangle."""
    O, U, V, w, h, n = mirror_plane(tilt)
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
    tilt = cx.tilt
    O, U, V, w, h, n = mirror_plane(tilt)
    O0, U0, V0, w0_, h0_, n0 = mirror_plane(0.0)
    ms = cx.mirror_state
    info['mirror_plane'] = (O, U, V, w, h, n)
    info['glass3d'] = mirror_glass_pts(0.0, tilt)
    gpts = mirror_glass_pts(0.6, tilt)

    def glass_item(pen, cam, xf):
        pts = [xf.p(p) for p in gpts]
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
            if cx.glass_mode == 'clear':
                # the other side shows through: erase the glass in this layer (the inner world is a deeper layer);
                # the room's reflection stays at 20 %
                cv.drawPaint(skia.Paint(BlendMode=skia.BlendMode.kClear))
                if refl is not None:
                    cv.saveLayerAlpha(None, int(255 * cx.refl_alpha))
                    xr = Xf.reflect_plane(O0, n0).then(xf)
                    pen.fill(rect(-4000, -4000, 9000, 9000), _dk(P['wall'], 0.45))
                    refl.render(pen, cam, xr, skip=('mirror', 'decor'), tex=getattr(refl, 'tex', None))
                    pen.fill(rect(-4000, -4000, 9000, 9000), '#04061a', 175)
                    cv.restore()
                draw_plane(pen, cam, xf, O, U, V, w, h, _glass_surface(P, ms), True, 0.01)
                cv.restore()
                return
            if refl is not None:
                xr = Xf.reflect_plane(O0, n0).then(xf)
                pen.fill(rect(-4000, -4000, 9000, 9000), _dk(P['wall'], 0.45))
                refl.render(pen, cam, xr, skip=('mirror', 'decor'), tex=getattr(refl, 'tex', None))
                # the reflection is darker, cooler and a little green-grey (old silvering loses light)
                pen.fill(rect(-4000, -4000, 9000, 9000), '#04061a' if cx.now else _dk(P['outline'], 0.3), 200 if ms == 'glass' else 225)
                pen.fill(rect(-4000, -4000, 9000, 9000), '#2a4050' if cx.now else P['wall_dk'], 30)
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
    if ms == 'covered':
        def drape(pen, w_, h_):
            outline = smooth([(-4, -6), (w_ * 0.5, -10), (w_ + 4, -6), (w_ + 7, h_ * 0.5), (w_ + 3, h_ * 0.78), (w_ * 0.6, h_ * 0.8 + 6),
                              (w_ * 0.3, h_ * 0.78), (-5, h_ * 0.8), (-8, h_ * 0.4)], True, 0.7)
            towel_cloth(pen, outline, (0, 0, w_, h_ * 0.8), 0.2, 0.3, 7, 0.8, True, '#e0a060', '#efe6d6')
        sc.plane(O + n * 0.02, U, V, w, h, drape, -39.0, 'drape', 'mirror')


def _glass_surface(P, ms):
    """Sheen, silvering spots at the edges, the dust film and finger smudges on the glass (mirror plane cm)."""
    def g(pen, w, h):
        inner = rect(MFW, MFW, w - 2 * MFW, h - 2 * MFW)
        _L(pen, inner, 0, 0, w, h * 0.42, [(0, '#ffffff', 0), (0.26, '#e8ecff', 0), (0.33, '#e8ecff', 95), (0.40, '#ffffff', 22),
                                           (0.47, '#ffffff', 0), (0.55, '#e8ecff', 48), (0.6, '#ffffff', 0)])
        _L(pen, inner, 0, h * 0.5, w, h * 0.95, [(0, '#ffffff', 0), (0.45, '#dfe6ff', 0), (0.5, '#dfe6ff', 40), (0.56, '#ffffff', 0)])
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
    'red': dict(tread='#4e1a4c', tread_lt='#6e2a6a', riser='#26082a', edge='#ff2d55', glow='#ff4060', wall='#5e2a5e',
                wall_dk='#26082a', wall_lt='#82388a', fog='#5a1e5a', spill='#e85a8a', moon='#c2185b', floor='#6a3a6a',
                floor_dk='#3a1a3a', rail='#300a2e', rail_lt='#8a3a8a', outline='#0e0208', gold_room='#e8608a'),
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
        # review round 2 (B10): Noah's white sneaker on the gold floor beside his bed ("you see the shoe beside the bed")
        def shoe_s(pen, w, h):
            S1.sneaker(pen, w / 2, h / 2, 0.075, 15)
        sc.plane((0.12, yb + 0.003, 2.85), (1, 0, 0), (0, 0, -1), 34, 22, shoe_s, -55, 'gshoe', 'bottom')
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
    sc.plane((gw / 2, MIR_H - 0.06, 0.0), (-1, 0, 0), (0, -1, 0), gw * 100, MIR_H * 100, _frame_hole(fr), 0.3, 'dframe', 'door',
             two_sided=False)
    # wall around the doorway (seen from the stairs side): plum boards
    def dwall(pen, w, h):
        hole = rect((hw + 0.6 - gw / 2) * 100, 30 - 6, gw * 100, MIR_H * 100)
        pen.cv.clipPath(hole, skia.ClipOp.kDifference, True)
        _planks(pen, w, h, dict(wall=S['wall_dk'], wall_dk=S['riser'], wall_lt=S['wall'], seam=S['outline']), 18.0, 23, True, None, 0.8)
    sc.plane((hw + 0.6, MIR_H + 0.24, 0.002), (-1, 0, 0), (0, -1, 0), (ST_W + 1.2) * 100, (MIR_H + 0.5) * 100, dwall, 0.2, 'dwall', 'door',
             two_sided=False)
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
            c = P.get('swim', SWIM)[i]
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
    info['drop'] = v3((wx0 + wx1) / 2 + 0.05, 0.36, D - 0.5)          # review round 2 (B19): hangs low enough to be in the floor views
    # the battery lantern on the sill
    def lantern_c(pen, cam, xf):
        p = xf.p(v3(wx1 - 0.3, wy0, D - 0.08))              # review round 2 (M8): clear of the curtain
        if cam.dist(p) < 0.1: return
        x, y = cam.pt(p); k = cam.px_per_m(p)
        # review round 2 (M8): standing ON the sill (y is the lantern's base; it was drawn 12 cm up, hanging in the window)
        lantern(pen, x, y, 0.0025 * k / 0.9, 1.0, '#ffd9a0', '#3a4a3a', True)
    sc.custom((wx1 - 0.3, wy0 + 0.1, D - 0.08), lantern_c, -60, 'lantern', 'window')
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
    if not cx.past: _stairs_theirs(sc, cx, info)


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


# A travelling shot (film.py: a shot with `cam3` keys) rebuilds its view every frame with that frame's camera: film.py sets
# MOVE = {'cam': Cam3, 'd0': float, 'memo': {}} around the build. The views then take MOVE's camera and d0, the room models
# are built once per shot (memo) and drawn as live bands from baked plane textures (Scene3.live_bands), and every live
# overlay (light shafts, the beam, the clock hands, the lipstick, the prints) is placed for that frame's camera.
MOVE = None


def _mv(cam, d0):
    """The view's camera and d0, or the travelling shot's (MOVE)."""
    if MOVE is None: return cam, d0
    return MOVE['cam'], (MOVE.get('d0') or d0)


def _memo(key, build):
    if MOVE is None: return build()
    m = MOVE.setdefault('memo', {})
    if key not in m: m[key] = build()
    return m[key]


def cabin_layers(cx, cam, view_key, d0, bands=None, xf=None):
    """Static cached layers of the cabin model for one camera: (layers, scene, info, xf). In a travelling shot (MOVE) the
    model is built once per shot and drawn live for the frame's camera."""
    mk = ('cabin', cx.side, cx.var, _sig(cx), getattr(cx, 'glass_mode', None), getattr(cx, 'tilt', 0.0), getattr(cx, '_force_ms', None),
          getattr(cx, 'refl_alpha', None))
    sc, info = _memo(mk, lambda: cabin_scene(cx))
    cx.refl_scene = sc
    xf = xf if xf is not None else (ID if cx.ours else Xf.flip_x(W))
    key = 'v2:%s:%s:%s:%s' % (cx.side, view_key, cx.var, _sig(cx))
    bands = bands or _bands(d0)
    if MOVE is not None:
        L = sc.live_bands(cam, d0, bands, xf, depths={0: 0.6, 1: 1.0, 2: 2.0} if len(bands) == 3 else {0: 0.5, 1: 1.0})
    else:
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

    def pool(pen, t, b=b):                                   # DIRECTION_V2 1.2: the beam's warm floor pool (#f0a84e / #ffd58a)
        sx, sy, ax, ay, k = b.at(t)
        if k > 0.01: hot_spot(pen, ax, ay, b.spot * 1.35, k * 0.75, 0.5, c='#f0a84e', core='#ffd58a')
    L.append(_live(dep * 1.001, pool, 'beam_pool', blur=0))
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


def steps_live(cam, xf, d0, st, var, glow_extra=0.0, show_eighth=True, name='lipstick', tilt=0.0):
    """The lipstick steps (and the 8th line behind the glass) on the mirror via the mirror-local homography."""
    Hm = mirror_local_H(cam, xf, tilt)
    from engine.room3d import _skmat
    M = _skmat(Hm)
    O, U, V, w, h, n = mirror_plane(tilt)
    dep = sdep(cam, xf, d0, O + U * (w / 200) + V * (h / 200), 0.003)
    glass_q = clip_poly_near(cam, [xf.p(p) for p in mirror_glass_pts(0.6, tilt)])

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
            eighth_line(pen, t, e, 0.6, 1.0, 1.0, rot=tilt)
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
    'doorway_down': ((2.66, 1.12, 5.72), (2.66, -0.95, 7.7), 70.0, 0.0),     # 10 behind you looking down through the doorway
    'dutch_low': ((3.7, 0.42, 2.7), (3.1, 1.25, 6.3), 76.0, 8.0),           # 11 dutch low angle (climax)
    'floor_wide': ((1.05, 0.62, 1.9), (3.5, 0.45, 5.7), 74.0, 0.0),         # 12 the ending wide on the floor
    'doorway': ((2.95, 1.15, 4.35), (2.66, 0.86, 6.4), 56.0, 0.0),          # MS of the doorway
    'bunk_rail': ((3.85, 1.25, 3.55), (5.05, 1.35, 5.1), 64.0, 0.0),        # MS: grown Noah hits the top rail
    'floor_cu': ((2.72, 0.24, 4.95), (2.66, 0.18, 6.3), 62.0, 0.0),         # low: the floor at the mirror spot
}


def _ours_anchors(cam, xf, d0):
    A = {}
    pts = OURS_PTS
    for k, (P, h) in pts.items():
        a = _anc(cam, xf, d0, P, h)
        if cam.dist(xf.p(v3(P))) > 0.15: A[k] = a
    return A


OURS_PTS = {'tess_door': ((4.0, 0, 0.9), 1.68), 'you_door': ((3.6, 0, 1.3), 1.76), 'you_mirror': ((2.66, 0, 5.35), 1.76),
           'you_kneel': ((2.7, 0, 5.55), 1.76), 'tess_mirror': ((1.85, 0, 5.1), 1.68), 'tess_beside': ((3.35, 0, 5.0), 1.68),
           'tess_center': ((2.9, 0, 3.6), 1.68), 'noah_stand': ((3.8, 0, 4.6), 1.86), 'noah_floor': ((3.3, 0, 4.4), 1.86),
           'you_floor': ((2.4, 0, 4.1), 1.76), 'tess_sill': ((1.82, 0, 5.75), 1.68), 'noah_bunk_edge': ((4.6, 0, 5.2), 1.86),
           'doorway': ((2.665, 0, 6.2), 1.6), 'mirror': ((2.665, 0, 6.25), 1.6), 'sill': ((1.82, 0.95, 6.3), 0.2),
           'phone': ((1.68, 0.95, 6.28), 0.15), 'clock': ((CLOCK[0], CLOCK[1] - CLOCK[2], 6.38), 0.3),
           'cubby_noah': ((5.4, 2.0, 6.0), 0.3), 'bundle': ((5.0, 0.05, 5.5), 0.2)}


def _ours_light(cx, cam, xf, d0, st, vname, info, beam=True):
    """Live/cached light for OURS views: moon shafts + motes, Tess's beam (if on) aimed at the mirror, the clock hands, the
    lipstick steps on the glass, the doorway's gold (or red) spill."""
    L = []
    t0 = st.t0
    P = cx.P
    var = cx.var
    if var in ('night', 'flash', 'doorway_glow', 'after', 'phone_glow'):
        L += shaft_layer(cam, xf, d0, '%s:%s' % (vname, var), P, False, 44 if var != 'after' else 26)
    if 'clock' in info and cam.dist(xf.p(info['clock'][0])) > 0.3:
        L.append(clock_live(cam, xf, d0, info, st, 'ours'))
    ms = cx.mirror_state
    b = None
    if beam and var in ('night', 'flash', 'doorway_glow') and any(_flash_on(st, tt) for tt in (st.t0, (st.t0 + st.t1) / 2, st.t1)):
        aim = info.get('mirror_centre', v3(2.66, 0.8, 6.2)) if ms != 'absent' else v3(5.0, 0.2, 5.4)
        # Tess stands beside or behind the camera: her lamp enters from the lower left, off frame (the assembler drives
        # the beam from her rig when she is in shot: sp.info['beam'].override)
        R = cam.R
        src = cam.C + R[2] * 0.9 - R[0] * 0.7 - R[1] * 0.45     # just off the lower-left corner: the cone crosses the frame
        if src[1] < 0.35: src = src + v3(0.0, 0.35 - float(src[1]), 0.0)   # review round 2: a camera low at the floor put the lamp under the boards
        bl, b = beam_layers(cam, xf, d0, st, src, [(t0, aim + v3(0.15, 0.1, 0)), (t0 + 1.2, aim + v3(-0.1, -0.05, 0)),
                                                   (t0 + 2.6, aim + v3(0.08, 0.12, 0))], seed=int(t0) % 17, a=0.52, spot=230)
        L += bl
    if ms in ('glass', 'dark') and cam.dist(xf.p(v3(2.66, 0.8, 6.3))) > 0.3:
        L.append(steps_live(cam, xf, d0, st, var))
        if b is not None:
            L.append(glass_glint_live(cam, xf, d0, b, src))
    if ms == 'doorway' or var == 'doorway_glow' or var == 'red':
        L += doorway_spill(cam, xf, d0, cx, st)
    if 'phone_spot' in info and any(str(st.v('phone', tt)).startswith('sill') for tt in (st.t0, st.t1)):
        pl = phone_live(cam, xf, d0, st, info)
        if pl is not None: L.append(pl)
    if var in ('after', 'phone_glow'):
        L += flashlight_floor_live(cam, xf, d0, st, var)
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
    weak = cx.mirror_state != 'doorway'                 # the glass is back (614.9): the red glows through, no rays

    def draw(pen, t):
        pulse = (0.82 + 0.18 * math.sin(t * 2 * math.pi / 1.2)) if red else (0.9 + 0.1 * math.sin(t * 1.3))
        _R(pen, None, cxp, cyp, 1.4 * k_px, [(0, c, 50 * pulse), (0.35, c, 22 * pulse), (1, c, 0)], sy=0.9, clip=False)
        # floor pool in front of the doorway
        fp = cam.pt(xf.p(v3(2.66, 0.0, 5.6)))
        _R(pen, None, fp[0], fp[1], 1.1 * k_px, [(0, c2, 70 * pulse), (0.5, c, 28 * pulse), (1, c, 0)], sy=0.35, clip=False)
        # rays fanning out of the opening
        for i in range(6 if not weak else 0):
            a = -0.9 + 1.8 * i / 5 + 0.05 * math.sin(t * 0.7 + i)
            L_ = (1.6 + 0.6 * _h(i, 3)) * k_px
            w0 = 0.08 * k_px
            q = poly([(cxp - w0, cyp), (cxp + w0, cyp), (cxp + math.sin(a) * L_ + w0 * 4, cyp + math.cos(a) * L_ * 0.55 + 0.3 * k_px),
                      (cxp + math.sin(a) * L_ - w0 * 4, cyp + math.cos(a) * L_ * 0.55 + 0.3 * k_px)])
            _L(pen, q, cxp, cyp, cxp + math.sin(a) * L_, cyp + math.cos(a) * L_ * 0.55, [(0, c, 30 * pulse), (1, c, 0)])
        if steam:
            for i in range(5):
                ph = (t * 0.35 + i * 0.2) % 1.0
                x = cxp + (math.sin(t * 0.8 + i * 1.7) * 0.15 + (i - 2) * 0.06) * k_px
                y = cyp - ph * 1.2 * k_px
                _R(pen, None, x, y, (0.08 + 0.2 * ph) * k_px, [(0, '#ffe2a8', 80 * (1 - ph)), (1, '#ffe2a8', 0)], sy=1.6, clip=False)
    return [_live(dep, draw, 'doorway_spill', blur=None)]


def ours_view(vname, var, st, shot, cam=None, d0=None, extra=None):
    cx = CabinCtx('ours', var or 'night', st, st.t0)
    pos, look, fov, roll = OURS_CAMS[vname] if (cam is None and MOVE is None) else (None, None, None, None)
    cam = cam or (MOVE['cam'] if MOVE is not None else Cam3(pos, look=look, fov=fov, roll=roll))
    d0 = d0 or (MOVE['d0'] if MOVE is not None else max(1.0, cam.dist(v3(2.66, 0.9, 6.0))))
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
    'window': ((4.25, 1.3, 4.3), (3.7, 1.2, 6.4), 62.0, 0.0),               # 3 window wide
    'towel_floor': ((4.55, 0.2, 4.55), (3.75, 0.12, 6.0), 62.0, 0.0),       # 4 floor level across the towel and the drop
    'bunk_2s': ((2.35, 1.15, 3.25), (0.6, 0.75, 5.25), 62.0, 0.0),          # 5 the bunk 2-shot
    'queen_3s': ((3.0, 1.35, 2.55), (0.9, 0.75, 5.2), 66.0, 0.0),           # 6 the Queen 3-shot
    'top_stairs': ((2.93, 3.35, 6.15), (1.7, 0.25, 3.4), 74.0, 0.0),        # 8 high from the top of the stairs (Tess's view)
    'ots_noah': ((0.55, 1.05, 5.55), (2.7, 1.0, 3.0), 60.0, 0.0),           # 9 OTS past Noah
    'dip_low': ((1.35, 0.62, 4.0), (0.5, 0.5, 5.35), 56.0, 0.0),            # 10 the mattress dip, low
    'overhead': ((2.2, 3.55, 2.4), (1.5, 0.0, 3.75), 80.0, 0.0),            # high angle on the floor (the prints)
    'floor_prints': ((2.75, 0.5, 0.55), (1.25, 0.0, 3.1), 68.0, 0.0),        # low wide at the wash-house door
    'door_wash': ((2.9, 1.3, 3.9), (1.6, 1.05, 0.0), 66.0, 0.0),            # the wash-house door swings in
    'swimsuits': ((2.05, 1.75, 4.05), (0.9, 1.55, 5.25), 56.0, 0.0),        # the swimsuits on the top rail
    'lantern': ((3.88, 1.22, 5.25), (3.72, 1.04, 6.33), 44.0, 0.0),            # insert: the lantern on the sill (review round 2, M8: on it)
    'clock': ((4.45, 2.02, 5.45), (4.45, 2.1, 6.4), 40.0, 0.0),             # insert: the clock 6:59
    'knot': ((1.35, 0.5, 4.25), (0.8, 0.08, 4.95), 46.0, 0.0),              # insert: the half-tied lace
    'shoe': ((1.55, 0.62, 3.95), (0.95, 0.04, 4.85), 52.0, 0.0),            # insert: one shoe on, the other beside the bed
    'hands': ((1.7, 1.1, 3.9), (0.8, 0.7, 5.3), 50.0, 0.0),                 # POV plates for the hand inserts
    'hands_jerk': ((1.6, 1.15, 3.7), (1.5, 1.0, 6.4), 54.0, 0.0),
}


def _theirs_anchors(cam, xf, d0):
    """Anchors in THEIRS world coords (the model is flipped, so these are given directly in world x)."""
    A = {}
    pts = THEIRS_PTS
    for k, (P, h) in pts.items():
        p = v3(P)
        if cam.dist(p) > 0.15:
            x, y, hh, dep = cam.anchor(p, h, d0)
            A[k] = Anchor(x, y, dep, hh)
    return A


THEIRS_PTS = {'noah_bunk': ((0.95, B_LOW, 4.95), 1.5), 'noah_seat': ((0.95, B_LOW, 4.95), 1.5), 'queen_bunk': ((0.95, B_LOW, 5.32), 1.92),
           'you_bunk_end': ((1.0, B_LOW, 4.35), 1.76), 'you_stand': ((1.75, 0, 4.4), 1.76), 'you_room': ((2.3, 0, 3.6), 1.76),
           'queen_corner': ((4.1, 0, 5.75), 1.92), 'tess_doorway': ((2.93, DROP, 6.22), 1.68), 'doorway': ((2.93, DROP, 6.3), 1.6),
           'stairs_foot': ((1.25, 0, 5.4), 1.76), 'tread8': ((1.04, DROP - 1.6, 5.95), 1.76), 'tread1': ((2.93, DROP - 0.2, 5.95), 1.76),
           'towel': ((3.78, 0.0, 5.9), 0.2), 'drop': ((3.83, 0.62, 5.9), 0.1), 'shoe': ((1.18, 0, 4.71), 0.12),
           'dip': ((0.95, B_LOW, 4.32), 0.2), 'door_wash': ((1.6, 0, 0.1), 1.76), 'clock': ((4.45, 1.97, 6.38), 0.3),
           'window': ((3.78, 1.42, 6.38), 0.95)}


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
        r = 0.032 * k                     # review round 2 (B19): a bead ~3 % of the frame height on the floor views
        # review round 2 (B19): by film time (a merged shot carries one prop state): the drips tap the towel, one drop rises
        # (335.25-337.09) and hangs; on the loop (345.06 on) the same drop falls again
        if 337.09 <= t < 345.0 or (t < 335.25 and t > 348.0 and (st_.startswith('hanging') or d_raw.startswith('hanging'))):
            yy = y + 0.004 * k * math.sin(t * 2.0)
        elif 335.25 <= t < 337.09 or d_raw.startswith('rising'):
            u = ease_in_out(prog(t, 335.25, 337.09)); yy = lerp(ty, y, u)
        else:
            ph = ((t - 297.59) % 1.6) / 1.6
            yy = lerp(y - 0.25 * k, ty, ph ** 2)
            if ph > 0.95:
                _R(pen, None, tx, ty, 0.05 * k, [(0, '#e8f6ff', 160), (1, '#e8f6ff', 0)], sy=0.3, clip=False)
        # its shadow on the towel below (darker as it nears), so it reads as a bead in the air, not a speck on the wall
        near_ = clamp(1.0 - abs(ty - yy) / max(1.0, 0.5 * k))
        _R(pen, None, tx, ty, 1.6 * r, [(0, '#3a2a10', 60 + 60 * near_), (1, '#3a2a10', 0)], sy=0.32, clip=False)
        drop = S1._drop_path(x, yy, r, 1.35)
        _R(pen, None, x, yy, 2.4 * r, [(0, '#ffffff', 70), (1, '#ffffff', 0)], clip=False)
        pen.fill(drop, '#bcd8e8', 240)
        # the room upside down inside it: a tiny warm window and floor band, inverted
        pen.cv.save(); pen.cv.clipPath(drop, skia.ClipOp.kIntersect, True)
        pen.fill(rect(x - r, yy - r * 1.4, 2 * r, r * 0.9), '#c99660', 230)
        pen.fill(rect(x - r * 0.3, yy + r * 0.1, r * 0.6, r * 0.5), '#fff2d0', 230)
        pen.cv.restore()
        pen.line(drop, max(1.5, 0.003 * k), '#4a6070', 230)
        pen.fill(oval(x - r * 0.35, yy - r * 0.2, r * 0.22), '#ffffff', 230)
    return _live(dep, draw, 'drop', blur=0)


def theirs_view(vname, var, st, shot, extra=None):
    cx = CabinCtx('theirs', var or 'dawn', st, st.t0)
    pos, look, fov, roll = THEIRS_CAMS[vname]
    cam = Cam3(pos, look=look, fov=fov, roll=roll)
    cam, d0 = _mv(cam, max(0.8, cam.dist(v3(1.3, 0.9, 5.2))))
    L, sc, info, xf = cabin_layers(cx, cam, vname, d0)
    L += _theirs_live(cx, cam, xf, d0, st, vname, info)
    if vname in ('floor_prints', 'overhead', 'master', 'door_wash', 'reverse', 'top_stairs', 'bunk_2s', 'queen_3s', 'towel_floor', 'shoe'):
        pl = prints_live(cam, xf, d0, st)
        if pl is not None: L += pl
    if vname == 'door_wash':
        L.append(door_wash_live(cam, d0, st))
    if (var or '') == 'dawn_break':
        L.append(red_leak_layer())
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
    'down': ((0.0, 1.32, 0.12), (0.0, -1.7, 2.4), 70.0, 0.0),           # 1 down from our doorway
    'up': ((0.12, -1.2, 2.95), (0.0, 0.85, -0.1), 64.0, 0.0),          # 2 up from the dawn cabin to the doorway (Tess in it)
    'low': ((0.18, -1.5, 2.5), (0.0, 0.1, 0.35), 72.0, 0.0),           # low angle up the stairs
    'treads': ((0.02, -0.05, 0.3), (0.0, -0.7, 1.05), 62.0, 0.0),      # 4 feet on treads
    'ots_climb_down': ((0.14, 0.8, 0.1), (0.0, -1.3, 1.9), 70.0, 0.0),    # 5 OTS going down (290.7)
    'ots_climb_up': ((0.12, -0.95, 2.15), (0.0, 0.55, -0.05), 68.0, 0.0),  # 5 OTS climbing (546-600)
    'pov_down': ((0.0, 0.15, 0.85), (0.0, -1.05, 1.75), 74.0, 0.0),    # 6 POV looking down at the step below
    'railing': ((-0.28, -0.05, 0.45), (0.38, -1.55, 2.3), 62.0, 0.0),   # down along the railing (the hand through the balusters)
}


def stairs_view(vname, var, st, shot):
    var = var or 'stairs'
    t0 = st.t0
    key = vname
    if vname == 'ots_climb': key = 'ots_climb_down' if t0 < 400 else 'ots_climb_up'
    pos, look, fov, roll = STAIRS_CAMS[key]
    cam = Cam3(pos, look=look, fov=fov, roll=roll)
    dstate = str(st.v('doorway', t0))

    def _build():
        sc_ = stairs_scene('red' if var == 'red' else 'stairs')
        _stairs_lights(sc_, var, dstate)
        _doorway_top(sc_, var, st, dstate)
        return sc_
    sc = _memo(('stairs', var, dstate), _build)
    cam, d0 = _mv(cam, max(0.6, cam.dist(v3(0.0, -0.8, 1.2))))
    bands = _bands(d0, 0.7, 1.5)
    if MOVE is not None:
        L = sc.live_bands(cam, d0, bands)
    else:
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
    sc.light((0.0, -1.5, 2.6), '#ffcf8a' if not red else '#e8608a', 120, 1.2, name='gold_bottom')
    sc.light((0.6, -0.6, 1.0), '#c63449' if not red else '#ff2d55', 30 if not red else 50, 1.2, name='red_edge_fill')


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
    sc.plane((gw / 2 - 0.06, MIR_H - 0.12, -0.05), (-1, 0, 0), (0, -1, 0), (gw - 0.12) * 100, (MIR_H - 0.12) * 100, view_in, -10,
             'dview', 'door', two_sided=False)


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
                pen.seg(pa, pb, max(2.0, 0.05 * k), glow, int(45 * br))
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


# ====================================================================== the section (the dollhouse cutaway, one fixed framing)
SEC = dict(cab=(110, 150, 900, 540), sill=(900, 540), tread_w=68.0, tread_h=44.0, gold=(1410, 470, 1880, 960), gold_floor=892)


def _sec_treads():
    x0, y0 = SEC['sill']; tw, th = SEC['tread_w'], SEC['tread_h']
    return [(x0 + (k - 1) * tw, y0 + k * th, tw) for k in range(1, N_STEPS + 1)]       # (x left, y top, width) for tread k


def section_view(var, st, shot):
    """The crossing as a cross-section: Cabin 7 upper left in blue night, the white frame in its back wall, eight red
    treads stepping down to the right through the plum fog, the gold cabin lower right. Always this framing (setup reuse)."""
    red = var == 'red'
    S = SPAL['red' if red else 'stairs']
    P = PAL['red' if red else 'night']; T = PAL['theirs_break' if red else 'theirs']
    cx0, cy0, cx1, cy1 = SEC['cab']; gx0, gy0, gx1, gy1 = SEC['gold']; gf = SEC['gold_floor']

    def void(pen, t):
        _L(pen, rect(-900, -600, 3800, 2400), 0, -200, 0, 1300, [S['wall_dk'], S['fog'], mix(S['fog'], S['spill'], 0.3), S['riser']])
        _R(pen, None, 1500, 900, 900, [(0, S['spill'], 90), (1, S['spill'], 0)], sy=0.5, clip=False)
        _R(pen, None, 500, 300, 900, [(0, S['moon'], 50), (1, S['moon'], 0)], sy=0.6, clip=False)
        for i in range(40):
            x, y = _h(i, 3) * 2400 - 200, _h(i, 4) * 1300 - 100
            pen.fill(oval(x, y, 1.5 + 3 * _h(i, 5)), '#ffffff', 30)

    def cabin(pen, t):
        # roof gable, walls in section (cut faces darker), interior blue, floor slab
        roof = poly([(cx0 - 40, cy0 + 10), ((cx0 + cx1) / 2, cy0 - 120), (cx1 + 40, cy0 + 10)])
        pen.fill(roof, P['roof_dk']); pen.line(roof, 4, P['outline'])
        inside = rect(cx0, cy0, cx1 - cx0, cy1 - cy0)
        _L(pen, inside, 0, cy0, 0, cy1, [P['wall_dk'], P['wall'], P['wall_lt']])
        _planks(pen, cx1 - cx0, cy1 - cy0, P, 34.0, 7, True, None, 1.6, 0.18, False, 0.1) if False else None
        for i in range(int((cx1 - cx0) / 34)):
            pen.seg((cx0 + i * 34, cy0), (cx0 + i * 34, cy1), 2.0, P['seam'], 160)
        # the window with the moon, the clock, the left bunk, a rafter line
        wr = rect(cx0 + 300, cy0 + 120, 120, 110)
        _L(pen, wr, 0, cy0 + 120, 0, cy0 + 230, [P['sky0'], P['sky1']]); pen.fill(oval(cx0 + 380, cy0 + 150, 12), P['moon'])
        pen.line(wr, 6, P['paint']); pen.seg((cx0 + 360, cy0 + 120), (cx0 + 360, cy0 + 230), 4, P['paint'])
        _R(pen, None, cx0 + 360, cy0 + 175, 260, [(0, P['key'], 60), (1, P['key'], 0)], clip=False)
        pen.fill(oval(cx0 + 220, cy0 + 70, 20), P['metal']); pen.fill(oval(cx0 + 220, cy0 + 70, 16), '#c6c8e4')
        pen.seg((cx0 + 220, cy0 + 70), (cx0 + 220, cy0 + 58), 2.5, '#1a1a24'); pen.seg((cx0 + 220, cy0 + 70), (cx0 + 230, cy0 + 72), 2.5, '#1a1a24')
        for (bx, by, bw, bh) in ((cx0 + 30, cy1 - 230, 200, 18), (cx0 + 30, cy1 - 110, 200, 18)):
            pen.fill(rect(bx, by, bw, bh), P['mat']); pen.line(rect(bx, by, bw, bh), 2.5, P['outline'])
        for bx in (cx0 + 34, cx0 + 222):
            pen.fill(rect(bx, cy1 - 260, 10, 260), P['wood']); pen.line(rect(bx, cy1 - 260, 10, 260), 2, P['outline'])
        # floor slab cut (planks end-on) and the back wall cut with the doorway
        slab = rect(cx0 - 40, cy1, cx1 - cx0 + 80, 30)
        pen.fill(slab, P['floor_dk']); pen.line(slab, 3, P['outline'])
        for i in range(0, int(cx1 - cx0 + 80), 22): pen.seg((cx0 - 40 + i, cy1 + 2), (cx0 - 40 + i, cy1 + 28), 1.5, P['outline'], 140)
        wall = rect(cx1 - 6, cy0 - 10, 26, cy1 - cy0 + 40)
        pen.fill(wall, P['wall_dk']); pen.line(wall, 3, P['outline'])
        lw_ = rect(cx0 - 26, cy0 - 10, 26, cy1 - cy0 + 40)
        pen.fill(lw_, P['wall_dk']); pen.line(lw_, 3, P['outline'])
        # the doorway in the back wall: the white chipped frame (seen edge-on as a white band) and the dark opening
        dh = 250
        pen.fill(rect(cx1 - 6, cy1 - dh, 26, dh), '#1a0f26')
        pen.fill(rect(cx1 - 14, cy1 - dh - 12, 12, dh + 12), '#e8e4d8'); pen.line(rect(cx1 - 14, cy1 - dh - 12, 12, dh + 12), 2, P['outline'])
        pen.fill(rect(cx1 + 20, cy1 - dh - 12, 10, dh + 12), '#e8e4d8'); pen.line(rect(cx1 + 20, cy1 - dh - 12, 10, dh + 12), 2, P['outline'])
        pen.fill(rect(cx1 - 14, cy1 - dh - 12, 44, 12), '#e8e4d8'); pen.line(rect(cx1 - 14, cy1 - dh - 12, 44, 12), 2, P['outline'])

    def treads(pen, t):
        for (x, y, w) in _sec_treads():
            blk = rect(x, y, w + 2, gf - y + 6)
            pen.fill(blk, mix(S['tread'], S['wall'], 0.4)); pen.line(blk, 2, S['outline'], 200)
            top = rect(x, y, w + 2, 12)
            pen.fill(top, S['tread_lt']); pen.fill(rect(x, y, w + 2, 4), S['edge'])
            pen.line(top, 2.5, S['outline'])
        # the railing on the room side (in section: balusters as lines in front)
        tr = _sec_treads()
        pts = [(x + 10, y - 70) for (x, y, w) in tr]
        pen.line(poly([(SEC['sill'][0] + 10, SEC['sill'][1] - 70)] + pts, False), 6, S['rail_lt'])
        for (x, y, w) in tr:
            pen.seg((x + 10, y), (x + 10, y - 70), 3.5, S['rail_lt'])

    def gold(pen, t):
        inside = rect(gx0, gy0, gx1 - gx0, gf - gy0)
        _L(pen, inside, 0, gy0, 0, gf, [T['wall_dk'], T['wall'], T['wall_lt']])
        for i in range(int((gx1 - gx0) / 30)):
            pen.seg((gx0 + i * 30, gy0), (gx0 + i * 30, gf), 1.8, T['seam'], 140)
        # roof, window with the peach dawn, gingham, the clock 6:59, Noah's bunk at the foot of the stairs
        roof = poly([(gx0 - 30, gy0 + 8), ((gx0 + gx1) / 2, gy0 - 90), (gx1 + 30, gy0 + 8)])
        pen.fill(roof, T['roof_dk']); pen.line(roof, 4, T['outline'])
        wr = rect(gx0 + 250, gy0 + 120, 110, 100)
        _L(pen, wr, 0, gy0 + 120, 0, gy0 + 220, [T['sky0'], T['sky1']]); pen.line(wr, 6, T['paint'])
        gingham(pen, rect(gx0 + 236, gy0 + 112, 30, 112), (gx0 + 236, gy0 + 112, gx0 + 266, gy0 + 224), '#e9c64a', 0.4)
        _R(pen, None, gx0 + 305, gy0 + 170, 300, [(0, '#ffe2a8', 120), (1, '#ffe2a8', 0)], clip=False)
        pen.fill(oval(gx0 + 400, gy0 + 70, 20), '#d8d0c0'); pen.fill(oval(gx0 + 400, gy0 + 70, 16), '#f2ecd8')
        pen.seg((gx0 + 400, gy0 + 70), (gx0 + 396, gy0 + 58), 2.5, '#1a1a24'); pen.seg((gx0 + 400, gy0 + 70), (gx0 + 412, gy0 + 66), 2, '#1a1a24')
        bx = gx0 + 60
        pen.fill(rect(bx, gf - 120, 190, 22), '#c0563a'); pen.line(rect(bx, gf - 120, 190, 22), 2.5, T['outline'])
        pen.fill(rect(bx, gf - 250, 190, 18), '#3f6fa8'); pen.line(rect(bx, gf - 250, 190, 18), 2.5, T['outline'])
        for x in (bx, bx + 182):
            pen.fill(rect(x, gf - 280, 10, 280), T['wood']); pen.line(rect(x, gf - 280, 10, 280), 2, T['outline'])
        for i, c in enumerate(SWIM):
            pen.fill(rrect(bx + 20 + i * 40, gf - 232, 26, 40, 8), c); pen.line(rrect(bx + 20 + i * 40, gf - 232, 26, 40, 8), 1.5, T['outline'])
        slab = rect(gx0 - 20, gf, gx1 - gx0 + 40, 30)
        pen.fill(slab, T['floor_dk']); pen.line(slab, 3, T['outline'])
        wall = rect(gx1 - 6, gy0 - 10, 26, gf - gy0 + 40); pen.fill(wall, T['wall_dk']); pen.line(wall, 3, T['outline'])
        if red:
            pen.fill(inside, '#ff2d55', 60)

    L = [_cl(30, void, 'void', 'v2sec:void:%s' % red, (-900, -600, 2900, 1800)),
         _cl(1.05, gold, 'gold', 'v2sec:gold:%s' % red, (1200, 300, 2000, 1100)),
         _cl(1.0, treads, 'treads', 'v2sec:treads:%s' % red, (800, 380, 1600, 1100)),
         _cl(0.98, cabin, 'cabin', 'v2sec:cabin:%s' % red, (-100, -60, 1100, 640))]
    edge_c = S['glow']

    def live(pen, t):
        br = 0.6 + 0.4 * math.sin(t * 2 * math.pi / 2.4)
        if red:
            pu = 0.8 + 0.2 * math.sin(t * 2 * math.pi / 1.2)
            _R(pen, None, cx1, cy1 - 120, 460, [(0, '#ff2d55', 120 * pu), (1, '#ff2d55', 0)], clip=False)
        for (x, y, w) in _sec_treads():
            pen.seg((x, y + 2), (x + w, y + 2), 9, edge_c, int(60 * br)); pen.seg((x, y + 2), (x + w, y + 2), 3, '#ffb0bc', int(170 * br))
        for i in range(4):
            xx = (i * 500 + t * 18) % 2200 - 200
            _R(pen, None, xx, 760 + 60 * math.sin(t * 0.4 + i), 460, [(0, S['fog'], 70), (1, S['fog'], 0)], sy=0.18, clip=False)
    L.append(_live(0.97, live, 'sec_live', blur=0))
    L.append(_live(0.96, lambda pen, t: motes(pen, t, (900, 420, 1500, 920), 30, 515, None, '#ffe8c8', 0.25, speed=(4, 9)), 'sec_dust', blur=0))
    if not red and str(st.v('flashlight', st.t0)).startswith('tess'):
        # Tess's beam in our cabin, pointed through the doorway down the stairs
        b = Beam(lambda t: (cx1 - 120, cy1 - 150, SEC['sill'][0] + 300, SEC['sill'][1] + 200 + 10 * math.sin(t * 1.5),
                            0.0 if str(st.v('flashlight', t)).startswith('tess_running') else 0.9), w0=14, spread=0.2, spot=60, a=0.3)
        L.append(b.layer(0.95, 'beam'))
    an = {'you_top': Anchor(SEC['sill'][0] - 40, SEC['sill'][1], 1.0, 150), 'tess_door': Anchor(SEC['cab'][2] - 120, SEC['cab'][3], 1.0, 150),
          'noah_bunk': Anchor(gx0 + 150, gf - 98, 1.0, 120), 'gold_floor': Anchor(gx0 + 330, gf, 1.0, 150)}
    for k, (x, y, w) in enumerate(_sec_treads(), 1):
        an['tread%d' % k] = Anchor(x + w / 2, y, 1.0, 150)
    return _sp('stairs/section', L, an, None, 1.0, 0.0, None, dict(world='stairs', section=SEC))


@view('stairs', 'section')
def _v_section(var, st, shot):
    return section_view(var, st, shot)


# ====================================================================== the mirror (set 'mirror'): it always reads as glass
def _glass_frame_pt(u, v, tilt=0.0, off=0.0):
    """A point on the mirror plane at fractions (u across the glass, v down it), pushed `off` m into the room."""
    O, U, V, w, h, n = mirror_plane(tilt)
    return O + U * (w / 100 * u) + V * (h / 100 * v) + n * off


MIRROR_CAMS = {
    # name: (u, v of the look point on the glass, distance into the room (m), (dx, dy) camera offset, fov)
    'glass_cu': (0.56, 0.5, 0.62, (0.06, 0.08), 56.0),         # the steps, the left frame edge in shot
    'glass_wide': (0.5, 0.5, 2.15, (0.0, 0.05), 52.0),         # the whole mirror on the back wall
    'glass_tilt': (0.5, 0.5, 1.95, (0.0, 0.05), 54.0),
    'queen_glass': (0.5, 0.52, 1.05, (0.02, 0.06), 56.0),      # she stands on the 8th line inside the glass
    'reflection': (0.5, 0.42, 1.25, (0.22, 0.32), 52.0),       # OTS on your reflection
    'through': (0.48, 0.5, 0.8, (0.05, 0.05), 56.0),           # the other side through the glass
    'towel_over': (0.5, 0.5, 1.7, (0.15, 0.12), 54.0),
}


def mirror_cam(vname, tilt=0.0):
    u, v, dist, (dx, dy), fov = MIRROR_CAMS[vname]
    O, U, V, w, h, n = mirror_plane(0.0)
    look = _glass_frame_pt(u, v)
    pos = look + n * dist + v3(1, 0, 0) * dx + v3(0, 1, 0) * dy
    return Cam3(pos, look=look, fov=fov)


def inner_world_layers(kind, cam, d0, st, var, tilt=0.0, key=''):
    """What is behind the glass when the other side shows through. kind: 'stairs' (the plum stairwell under the 8th
    step, v1 coords via the glass homography, on a deeper layer for parallax), 'red' (the same in climax red),
    'dawn' (THEIRS from the top of their stairs, gold and mirror-flipped)."""
    O, U, V, w, h, n = mirror_plane(tilt)
    gc = O + U * (w / 200) + V * (h / 200)
    dg = cam.dist(gc)
    dep = (dg + 1.4) / d0
    if kind == 'dawn':
        tcam = Cam3((2.93, 3.2, 6.05), look=(1.6, 0.4, 3.6), fov=62)
        cx = CabinCtx('theirs', 'dawn', st, st.t0)
        sc, info = cabin_scene(cx)
        cx.refl_scene = sc
        xf = Xf.flip_x(W)
        lay = Layer(dep, lambda pen, t: (pen.fill(rect(-2000, -2000, 6000, 5000), '#c99660'), sc.render(pen, tcam, xf)), 'inner_dawn',
                    cache='v2:inner_dawn:%s' % key, bounds=(-600, -400, 2520, 1480))
        return [lay, _live(dep * 0.99, lambda pen, t: frozen_motes(pen, t, (200, 100, 1700, 1000), 50, 91), 'inner_motes', blur=0)]
    red = kind == 'red'
    S = SPAL['red' if red else 'stairs']
    Hm = mirror_local_H(cam, ID, tilt)
    from engine.room3d import _skmat
    M = _skmat(Hm)

    def static(pen, t):
        pen.cv.concat(M)
        x0, y0, x1, y1 = PANE
        big = rect(x0 - 2600, y0 - 1600, x1 - x0 + 5200, y1 - y0 + 3200)
        _L(pen, big, 0, y0, 0, y1, [S['wall_dk'], S['fog'], mix(S['fog'], S['spill'], 0.25), S['riser']])
        # the stairwell falling away under the 8th step: treads converging, red edges, the gold at the bottom
        for j in range(14):
            u = j / 14.0
            yy = 905 + 300 * u ** 0.75
            wd = 520 * (1 - u) + 50
            q = poly([(575 - wd, yy), (575 + wd * 0.7, yy), (575 + wd * 0.66, yy + 26 * (1 - u) + 4), (575 - wd * 0.95, yy + 26 * (1 - u) + 4)])
            pen.fill(q, mix(S['tread'], S['tread_lt'], 0.3 * (1 - u)))
            pen.seg((575 - wd, yy), (575 + wd * 0.7, yy), 5 * (1 - u) + 1.5, S['edge'], int(220 * (1 - 0.6 * u)))
        _R(pen, None, 575, 1250, 420, [(0, S['spill'], 140), (1, S['spill'], 0)], sy=0.4, clip=False)
        # the railing on the room side, receding
        pts = [(575 - (520 * (1 - j / 14) + 50) - 30, 905 + 300 * (j / 14) ** 0.75 - 260 * (1 - j / 14) - 40) for j in range(15)]
        pen.line(poly(pts, False), 10, S['rail_lt'], 200)
        for j in range(0, 14, 2):
            x, y = pts[j]; pen.seg((x, y), (x + 10, 905 + 300 * (j / 14) ** 0.75), 6 * (1 - j / 14) + 2, S['rail'], 230)
        # our moonlight from above
        _R(pen, None, 960, -300, 1400, [(0, S['moon'], 70), (1, S['moon'], 0)], sy=0.6, clip=False)

    gq = [(Hm @ np.array([x, y, 1.0])) for (x, y) in ((575, 930), (960, 200), (960, 1400))]
    gp = [(p[0] / p[2], p[1] / p[2]) for p in gq]
    kpx = math.hypot(gp[1][0] - gp[2][0], gp[1][1] - gp[2][1]) / 1200.0          # design px per mirror-local px

    def alive(pen, t):
        br = 0.7 + 0.3 * math.sin(t * 2 * math.pi / 2.4)
        ex, ey = gp[0]
        _R(pen, None, ex, ey, 520 * kpx, [(0, S['glow'], 70 * br), (0.5, S['glow'], 24 * br), (1, S['glow'], 0)], sy=0.35, clip=False)
        for i in range(4):
            yy = gp[1][1] + (gp[2][1] - gp[1][1]) * (i + 0.5) / 4 + 30 * kpx * math.sin(t * 0.35 + i)
            xx = gp[1][0] - 700 * kpx + ((t * 40 + i * 400) % 1600) * kpx
            _R(pen, None, xx, yy, 600 * kpx, [(0, S['fog'], 70), (1, S['fog'], 0)], sy=0.2, clip=False)
    return [Layer(dep, static, 'inner_%s' % kind, cache='v2:inner:%s:%s' % (kind, key), bounds=(-700, -500, 2620, 1580)),
            _live(dep * 0.995, alive, 'inner_fog', blur=None),
            _live(dep * 0.99, lambda pen, t: motes(pen, t, (-100, -100, 2020, 1180), 46, 711, None, '#e8dcff', 0.12, fall=10,
                                                   speed=(3, 8)), 'inner_dust', blur=0)]


def mirror_view(vname, var, st, shot):
    var = var or 'night'
    t0 = st.t0
    pal_var = 'red' if var == 'red' else 'night'
    cx = CabinCtx('ours', pal_var, st, t0)
    mraw = str(st.raw.get('mirror', ''))
    tilt = TILT_V2 if (vname == 'glass_tilt' or mraw.startswith('tilted')) else 0.0
    cx.tilt = tilt
    # what the glass shows
    inner = None
    if var in ('stairs',) or vname == 'queen_glass':
        inner = 'stairs'
    elif vname == 'through':
        inner = 'dawn' if var == 'dawn' else ('red' if var == 'red' else 'stairs')
    if inner:
        cx.glass_mode = 'clear'; cx.refl_alpha = 0.2
    cam = mirror_cam(vname, tilt)
    O, U, V, w, h, n = mirror_plane(tilt)
    gc = O + U * (w / 200) + V * (h / 200)
    cam, d0 = _mv(cam, max(0.4, cam.dist(gc)))
    # mirror_state: towel views keep the towel; the mirror views show glass otherwise
    if vname == 'towel_over':
        st_m = 'towel'
    else:
        st_m = 'glass'
    cx_ms = st_m
    CabinCtx.mirror_state = property(lambda self, f=CabinCtx.mirror_state.fget: getattr(self, '_force_ms', None) or f(self))
    cx._force_ms = cx_ms
    bands = [(-1e9, d0 * 0.55, 'near', 0.5), (d0 * 0.55, 999.0, 'wall', 1.0)]
    L, sc, info, xf = cabin_layers(cx, cam, 'mirror_' + vname + ':%s:%.0f' % (inner or 'refl', tilt), d0, bands)
    if inner:
        L += inner_world_layers(inner, cam, d0, st, var, tilt, '%s:%s:%.0f' % (vname, var, tilt))
    # light: the beam on the glass (night), the steps, the 8th line
    if var in ('night', 'red') and vname not in ('towel_over',):
        live, b = _ours_light(cx, cam, xf, d0, st, 'm_' + vname, info, beam=(var == 'night'))
        for l in live:
            if l.name in ('beam', 'dust'): l.alpha = 0.45      # close on the glass the lamp's haze must not wash it out
        L += [l for l in live if l.name not in ('lipstick',)]
    L.append(steps_live(cam, xf, d0, st, 'red' if var == 'red' else var, tilt=tilt))
    if vname == 'towel_over':
        L += towel_over_layers(cam, xf, d0, st, tilt)
    # anchors: the 8th line, each drawn step, the Queen's spot behind the glass, the glass centre
    Hm = mirror_local_H(cam, xf, tilt)
    def mp(x, y):
        p = Hm @ np.array([x, y, 1.0]); return p[0] / p[2], p[1] / p[2]
    an = {}
    sc_px = cam.px_per_m(gc) * (w - 2 * MFW) / 100 / (PANE[2] - PANE[0])       # design px per mirror-local px
    ex, ey = mp(EIGHTH[0] + EIGHTH[2] / 2, EIGHTH[1])
    an['eighth'] = Anchor(ex, ey, 1.04, 230 * sc_px * 4.2)
    an['queen_step'] = Anchor(ex, ey, 1.04, 230 * sc_px * 4.2)
    for k in range(7):
        x, y = mp(*STEP_XY[k]); an['step%d' % (k + 1)] = Anchor(x, y, 1.0, 1)
        sx_, sy_ = mp(STEP_XY[k][0] - 30, STEP_XY[k][1]); an['queen_on_step%d' % (k + 1)] = Anchor(sx_, sy_, 1.04, 230 * sc_px * 4.2 * 1.25 ** (7 - k))
    gx, gy = cam.pt(gc); an['glass'] = Anchor(gx, gy, 1.0, cam.px_per_m(gc) * 1.48)
    an['top_step'] = an['step1']; an['bottom_step'] = an['step7']
    info_out = dict(info, cam3=cam, d0=d0, xf=xf, model=sc, world='ours' if not inner else ('theirs' if inner == 'dawn' else 'stairs'),
                    glass=clip_poly_near(cam, [xf.p(p) for p in mirror_glass_pts(0.6, tilt)]), mirror_H=Hm, mirror_xf=None, tilt=tilt)
    return _sp('mirror/' + vname, L, an, None, 1.0, 0.0, None, info_out, None)


TILT_V2 = -13.0


def towel_over_layers(cam, xf, d0, st, tilt):
    """The orange-striped towel thrown over the glass: it drapes over the frame top, hangs in folds; fingertips press
    through it (info['press'] or the plan's cloth_press cues); at towel_drop it falls flat."""
    O, U, V, w, h, n = mirror_plane(tilt)
    dep = sdep(cam, xf, d0, O + U * (w / 200) + V * (h / 200), 0.008)
    drop_t = st.ev('towel_drop')
    if drop_t is None:
        cues = st.sfx('towel_drop'); drop_t = cues[0] if cues else None
    presses_t = st.sfx('cloth_press')
    Hm, _ = cam.H(xf.p(O + n * 0.03 - U * 0.05 - V * 0.04), xf.d(U), xf.d(V), 0.01)
    from engine.room3d import _skmat
    M = _skmat(Hm)
    tw, th = w + 10, h * 0.92

    def body(pen, t, fall=0.0):
        pen.cv.save(); pen.cv.concat(M)
        pen.cv.translate(0, fall * h * 1.1)
        outline = smooth([(0, 2), (tw * 0.5, -3), (tw, 2), (tw + 3, th * 0.6), (tw - 2, th), (tw * 0.7, th + 8), (tw * 0.35, th + 3), (-2, th + 6),
                          (-4, th * 0.5)], True, 0.7)
        towel_cloth(pen, outline, (0, 0, tw, th), 0.22, 0.0, 7, 0.75, True, '#e0a060', '#efe6d6')
        for i in range(4):
            fx = tw * (0.15 + 0.23 * i)
            _L(pen, rect(fx - 4, 0, 8, th), fx - 4, 0, fx + 4, 0, [(0, '#000000', 0), (0.5, '#000000', 60), (1, '#000000', 0)])
        pen.cv.restore()

    def presses(pen, t):
        if drop_t is not None and t >= drop_t: return
        pen.cv.save(); pen.cv.concat(M)
        for j, tp in enumerate(presses_t):
            k = clamp(1.0 - abs(t - tp - 0.25) / 0.6)
            if k <= 0: continue
            for f in range(5):
                px, py = tw * (0.3 + 0.1 * f), th * (0.32 + 0.03 * abs(f - 2))
                # bounded paths: under the perspective matrix an unbounded radial shades the whole canvas (0.7 s a frame)
                _R(pen, oval(px, py, 4.6), px, py, 4.5, [(0, '#ffffff', 90 * k), (0.6, '#000000', 50 * k), (1, '#000000', 0)])
                _R(pen, oval(px, py - 1, 2.6), px, py - 1, 2.5, [(0, '#c63449', 150 * k), (1, '#c63449', 0)])
        pen.cv.restore()

    def falling(pen, t):
        if drop_t is None or not (drop_t <= t < drop_t + 0.4): return
        body(pen, t, ease_in_cubic(prog(t, drop_t, drop_t + 0.35)))
    still = Layer(dep, body, 'towel', cache='v2:towel_over:%d' % int(st.t0 * 10), bounds=FRAME,
                  alpha=(lambda t: 0.0 if (drop_t is not None and t >= drop_t) else 1.0))
    return [still, _live(dep * 0.999, presses, 'towel_press', blur=None), _live(dep * 0.998, falling, 'towel_fall', blur=None)]


def _reg_mirror(vname):
    @view('mirror', vname)
    def _v(var, st, shot, vname=vname):
        return mirror_view(vname, var, st, shot)
    return _v


for _vn in MIRROR_CAMS:
    _reg_mirror(_vn)


# ====================================================================== relighting v1 sets (exteriors, memories)
def _unpre(arr):
    a = arr[..., 3].astype(np.float32)
    c = arr[..., :3].astype(np.float32) * (255.0 / np.maximum(a, 1.0))[..., None]
    return a, c


def _repre(arr, a, c):
    arr[..., :3] = np.clip(c * (a / 255.0)[..., None], 0, 255).astype(np.uint8)


def relight_night(arr):
    """v1 navy night -> v2 OURS exterior (blue-violet, coloured, never black): luma lifted (p50 ~85-100), cool pixels rotated
    toward #5a5fa8, warm practicals kept warm. Baked once per cache."""
    a, c = _unpre(arr)
    if not (a > 0).any(): return
    B, G, R = c[..., 0], c[..., 1], c[..., 2]
    L = 0.0722 * B + 0.7152 * G + 0.2126 * R
    L2 = np.interp(L, [0, 15, 30, 55, 90, 150, 220, 255], [28, 58, 80, 104, 132, 178, 236, 255])
    sc = c * (L2 / np.maximum(L, 1.0))[..., None]
    tint = np.array([168.0, 95.0, 90.0])                        # #5a5fa8 in BGR
    tl = 0.0722 * 168 + 0.7152 * 95 + 0.2126 * 90
    tc = tint[None, None, :] * (L2 / tl)[..., None]
    warm = (R > B + 18)
    w = np.where(warm, 0.0, 0.5)[..., None]
    _repre(arr, a, sc * (1 - w) + tc * w)


_SEP = np.array([[74, 58, 44], [140, 108, 80], [201, 168, 120], [241, 226, 196], [252, 246, 232]], np.float64)   # RGB ramp


def relight_sepia(arr):
    """Memory: sepia paper (cream #f1e2c4, tan #c9a878, dark #4a3a2c) keeping 25 % of the original chroma (faded teal and
    orange survive), luma 130-160 typical."""
    a, c = _unpre(arr)
    if not (a > 0).any(): return
    B, G, R = c[..., 0], c[..., 1], c[..., 2]
    L = 0.0722 * B + 0.7152 * G + 0.2126 * R
    L2 = np.interp(L, [0, 40, 90, 150, 210, 255], [56, 92, 126, 156, 188, 212])
    u = np.clip((L2 - 56) / (232 - 56), 0, 1) * 4
    i0 = np.clip(np.floor(u).astype(int), 0, 3); f = (u - i0)[..., None]
    ramp = _SEP[i0] * (1 - f) + _SEP[i0 + 1] * f                 # RGB
    ramp = ramp[..., ::-1]                                       # BGR
    orig = c * (L2 / np.maximum(L, 1.0))[..., None]
    _repre(arr, a, ramp * 0.86 + orig * 0.14)


RELIGHT = {'night': relight_night, 'sepia': relight_sepia}


def relit(sp, mode, key):
    """Apply a bake-time relight to every cached layer of a v1 SetPiece (and a lift to its dark live layers)."""
    fn = RELIGHT[mode]
    for l in sp:
        if l.cache:
            l.relight = fn
            l.cache = '%s:rl_%s' % (l.cache if isinstance(l.cache, str) else 'uid%d' % l._uid, mode)
        elif l.name in ('pines', 'trees', 'pines_near', 'sway') and mode == 'night':
            l.tint = ('#8a90ff', 0.35)        # live swaying pines: a cheap cool lift (a per-frame relight costs ~0.3 s at 2560)
    return sp


def v1_alias(set1, view1, var1, st, shot, mode, name, zoom=None, flip=False, extra=None):
    """Build a v1 view (set1/view1/var1) for a v2 shot, relit (mode 'night' | 'sepia'), optionally zoomed about a point
    (zoom=(cx, cy, k)) or flipped left-right."""
    sh = dict(shot or {}); sh['set'], sh['view'], sh['var'] = set1, view1, var1
    fn = V1VIEWS[(set1, view1)]
    sp = fn(var1, st, sh)
    sp.name = name
    if zoom or flip:
        zx, zy, zk = zoom if zoom else (960.0, 540.0, 1.0)
        new = []
        for l in sp:
            d0 = l.draw

            def dr(pen, t, d0=d0):
                pen.cv.save(); pen.cv.translate(960, 540)
                if flip: pen.cv.scale(-1, 1)
                pen.cv.scale(zk, zk); pen.cv.translate(-zx, -zy)
                d0(pen, t); pen.cv.restore()
            l.draw = dr
            if l.cache:
                l.cache = '%s:z%.0f,%.0f,%.2f%s' % (l.cache, zx, zy, zk, ':f' if flip else '')
                b = l.bounds
                l.bounds = (min(b[0], -900), min(b[1], -560), max(b[2], 2820), max(b[3], 1640))
            new.append(l)
        for k_, an in list(sp.anchors.items()):
            x = 960 + (an.x - zx) * zk; y = 540 + (an.y - zy) * zk
            if flip: x = 1920 - x
            sp.anchors[k_] = Anchor(x, y, an.depth, an.height * (zk if an.height > 2 else 1))
    relit(sp, mode, name)
    if extra: sp.extend([l for l in extra(sp, st) if l is not None])
    sp.info = dict(sp.info, world='ours' if mode == 'night' else 'memory', v1=(set1, view1, var1))
    return sp


def _night_var(st, t=None):
    return 'moon_flash' if any(_flash_on(st, tt) for tt in (st.t0, st.t1)) else 'moon'


# ---------------------------------------------------------------------- warm practicals and life for the relit exteriors
def warm_lights(pts, name='practicals', depth=3.0):
    """Warm practical lights (x, y, r, colour) with a slow breath."""
    def draw(pen, t):
        for i, (x, y, r, c) in enumerate(pts):
            b = 0.9 + 0.1 * math.sin(t * 1.7 + i)
            _R(pen, None, x, y, r, [(0, c, 150 * b), (0.25, c, 60 * b), (1, c, 0)], clip=False)
            pen.fill(oval(x, y, max(2.0, r * 0.05)), '#fff3d6', 230)
    return _live(depth, draw, name, blur=0)


def x_marks(pts, name='xmarks', depth=1.0):
    """Orange spray-paint X marks on the condemned cabins."""
    def draw(pen, t):
        for (x, y, s_) in pts:
            for (a, b) in (((-1, -1), (1, 1)), ((1, -1), (-1, 1))):
                p = poly([(x + a[0] * 30 * s_, y + a[1] * 26 * s_), (x + b[0] * 30 * s_, y + b[1] * 26 * s_)], False)
                pen.line(p, 9 * s_, '#ff7a1a', 225); pen.line(p, 13 * s_, '#ff7a1a', 60)
    return _cl(depth, draw, name, 'v2xm:%s' % (','.join('%.0f' % p[0] for p in pts)), FRAME)


def _ext(set1, view1, var1=None, zoom=None, flip=False, extra=None):
    def fn(var, st, shot):
        v1var = var1 or (_night_var(st) if var in ('night', None) else var)
        return v1_alias(set1, view1, v1var, st, shot, 'night', '%s/%s' % (shot.get('set'), shot.get('view')), zoom, flip, extra)
    return fn


def _ff_layer(box=(100, 300, 1820, 900), n=10, seed=5, depth=2.0):
    return _live(depth, lambda pen, t: fireflies(pen, t, box, n, seed), 'fireflies', blur=0)


VIEWS[('camp_gate', 'wide')] = _ext('camp_gate', 'wide', extra=lambda sp, st: [_ff_layer()])
VIEWS[('camp_gate', 'keys_cu')] = _ext('camp_gate', 'keys_cu')
VIEWS[('camp_gate', 'notice')] = _ext('camp_gate', 'notice')
VIEWS[('camp_gate', 'poster')] = _ext('camp_gate', 'poster')
VIEWS[('camp_gate', 'poster_ecu')] = _ext('camp_gate', 'poster', zoom=(1000, 640, 2.2))
VIEWS[('camp_gate', 'gate_reverse')] = _ext('camp_gate', 'wide', flip=True, zoom=(960, 600, 1.12), extra=lambda sp, st: [_ff_layer(seed=9)])
VIEWS[('camp_gate', 'fence_track')] = _ext('camp_path', 'path_track', extra=lambda sp, st: [_ff_layer(seed=11)])
VIEWS[('camp_gate', 'aerial')] = _ext('camp_path', 'aerial', 'moon',
                                     extra=lambda sp, st: [x_marks([(600, 640, 0.7), (900, 600, 0.7), (1200, 640, 0.7)], depth=1.0),
                                                           warm_lights([(1600, 360, 60, '#ffb84d'), (1390, 455, 40, '#ffb84d')], depth=1.0)])
VIEWS[('camp_path', 'cabins_row')] = _ext('camp_path', 'cabins_row', 'moon', extra=lambda sp, st: [_ff_layer(seed=13)])
VIEWS[('camp_path', 'path_run')] = _ext('camp_path', 'path_track', extra=lambda sp, st: [_ff_layer(seed=17)])
VIEWS[('caretaker', 'wide')] = _ext('caretaker', 'wide', 'tv', extra=lambda sp, st: [_ff_layer(seed=19)])
VIEWS[('mess_porch', 'bell_ecu')] = _ext('mess_porch', 'bell_ecu')
VIEWS[('mess_porch', 'bell_hit')] = _ext('mess_porch', 'bell_ecu', 'bell_hit')
VIEWS[('mess_porch', 'boot')] = _ext('mess_porch', 'boot_ecu', 'run')
VIEWS[('mess_porch', 'crate_cu')] = _ext('mess_porch', 'crate_cu')
VIEWS[('mess_porch', 'porch_low')] = _ext('mess_porch', 'porch_low')
VIEWS[('mess_porch', 'wide')] = _ext('mess_porch', 'wide')


@view('mess_porch', 'porch_crate')
def _v_porch_crate2(var, st, shot):
    v1var = 'bell_hit' if var == 'bell_hit' else 'run'
    sp = v1_alias('mess_porch', 'porch_run', v1var, st, shot, 'night', 'mess_porch/porch_crate')
    if var == 'bell_hit':
        # the climax red begins at the strike: a red rim light from the right, pulsing
        sp.append(_live(0.9, lambda pen, t: _R(pen, None, 1900, 500, 1100, [(0, '#ff2d55', 70 * (0.8 + 0.2 * math.sin(t * 5.2))),
                                                                          (1, '#ff2d55', 0)], sy=0.9, clip=False), 'red_rim', blur=0))
    return sp


@view('mess_porch', 'high_wide')
def _v_porch_high(var, st, shot):
    """HIGH WIDE from the mess-hall porch toward Cabin 7's door (54.6 s and 453.6 s): the porch rail and boards in the
    foreground, the SAVE FOR THE MUSEUM crate right of the screen door, the path, Cabin 7 across it."""
    v1var = _night_var(st)
    sh = dict(shot); sh['set'], sh['view'], sh['var'] = 'camp_path', 'cabins_row', 'moon'
    bg = V1VIEWS[('camp_path', 'cabins_row')]('moon', st, sh)
    L = []
    for l in bg:
        d0 = l.draw

        def dr(pen, t, d0=d0):
            pen.cv.save(); pen.cv.translate(960, 330); pen.cv.scale(0.78, 0.78); pen.cv.translate(-1150, -560); d0(pen, t); pen.cv.restore()
        l.draw = dr
        if l.cache: l.cache = '%s:hw' % l.cache
        l.depth = (l.depth if not callable(l.depth) else 1.0) * 1.8; l.ref_depth = l.ref_depth * 1.8
        L.append(l)

    def porch(pen, t):
        # boards of the porch (high, looking down and across), the rail posts, the screen door edge, the crate
        P = PAL['night']
        q = poly([(-900, 760), (2820, 760), (2820, 1640), (-900, 1640)])
        pen.fill(q, P['floor'])
        for i in range(-30, 60):
            x = 960 + i * 60
            pen.seg((960 + (x - 960) * 0.55, 760), (960 + (x - 960) * 1.6, 1640), 2.2, P['floor_seam'], 200)
        pen.texture(q, 'wood', 0.22, 'overlay', 0.8, 90)
        pen.fill(rect(-900, 740, 3720, 26), P['wood']); pen.line(rect(-900, 740, 3720, 26), 3, P['outline'])
        for x in (-300, 380, 1060, 1740, 2420):
            r = rect(x, 520, 34, 240); pen.fill(r, P['wood']); pen.line(r, 3, P['outline'])
        pen.fill(rect(-900, 560, 3720, 22), P['wood_lt']); pen.line(rect(-900, 560, 3720, 22), 3, P['outline'])
        # screen door edge at the right and the crate right of it
        sd = rect(1180, -200, 130, 980); pen.fill(sd, P['wood_dk']); pen.line(sd, 4, P['outline'])
        S1.mesh(pen, (1192, -180, 1298, 760), 14, '#8a8eb8', 70)
        crate(pen, 1390, 840, 1760, 1070, 1.0, 0.5, '#8a7550', 0.0, True, True, 3, 1.0, True)
    L += [_cl(0.75, porch, 'porch_fg', 'v2:porch_high', NEAR)]
    L.append(warm_lights([(1500, 640, 90, '#ffb84d')], 'porch_lamp', 0.8))
    L.append(_ff_layer((100, 300, 1820, 700), 8, 23, 1.8))
    if any(_flash_on(st, tt) for tt in (st.t0, st.t1)):
        b = Beam(aim_fn((1300, 900), (900, 520), 1.0, 8, 3), w0=20, spread=0.25, spot=80, a=0.3)
        L.append(b.layer(1.2, 'beam'))
    sp = _sp('mess_porch/high_wide', L, {'tess_porch': Anchor(1250, 1000, 0.75, 700), 'cabin7_door': Anchor(1063, 525, 1.8, 180),
                                          'crate': Anchor(1575, 950, 0.75, 1)}, None)
    for l in sp:
        if l.cache and l.name != 'porch_fg':
            l.relight = relight_night; l.cache = '%s:rl_night' % l.cache
    sp.info['world'] = 'ours'
    return sp


@view('cabin_now', 'door')
def _v_cab_door2(var, st, shot):
    """Cabin 7's front door from outside: the board wall, the number plaque, the orange X, the DEMOLITION sticker, the
    hasp with the padlock (locked, hanging open from 71.9 s, gone when Tess takes it at 463)."""
    return cabin_front_view('door', var, st, shot)


@view('camp_path', 'cabin7_door')
def _v_cab7_door(var, st, shot):
    return cabin_front_view('cabin7_door', var, st, shot)


def cabin_front_view(vname, var, st, shot):
    P = PAL['night']
    pad = str(st.v('padlock', st.t0))

    def wall(pen, t):
        _L(pen, rect(-900, -600, 3800, 2400), 0, -600, 0, 400, [P['sky0'], P['sky1']])
        for i in range(10):
            pine(pen, -500 + i * 330, 60, 520 + 160 * _h(i, 2), i, '#1a1f48', P['key'], 60, 0, 9, 0.42)
        # the cabin's front: boards, eave, the door, casing
        fr = rect(-200, 0, 2320, 1300)
        _planks(pen, 2320, 1300, P, 70.0, 31, True, lambda p, w, h: _vgrad(p, w, h, [(0, '#000000', 90), (0.4, '#000000', 0)]), 3.0,
                0.25, True, 0.2) if False else None
        pen.cv.save(); pen.cv.translate(-200, 0)
        _planks(pen, 2320, 1300, P, 70.0, 31, True, None, 3.0, 0.25, True, 0.2)
        pen.cv.restore()
        pen.fill(rect(-260, -60, 2440, 70), P['roof_dk']); pen.line(rect(-260, -60, 2440, 70), 4, P['outline'])
        door = rect(700, 180, 420, 920)
        pen.fill(rect(670, 150, 480, 950), P['wood_dk']); pen.line(rect(670, 150, 480, 950), 4, P['outline'])
        pen.cv.save(); pen.cv.translate(700, 180)
        _planks(pen, 420, 920, P, 70.0, 37, True, None, 3.0, 0.25, True, 0.2, P['wood'], P['wood_dk'], P['wood_lt'], P['seam'])
        pen.cv.restore()
        pen.line(door, 4, P['outline'])
        for y in (230, 620, 1010):
            pen.fill(rect(700, y, 420, 40), P['wood_dk'], 220); pen.line(rect(700, y, 420, 40), 3, P['outline'], 180)
        # DEMOLITION sticker and orange X
        r = rect(760, 420, 300, 120); pen.fill(r, '#ff7a1a'); pen.line(r, 3, '#3a1a08')
        _sign_text(pen, 'DEMOLITION', 910, 478, 44, '#1a0a04', 900)
        _sign_text(pen, 'SAT 7:00 AM · KEEP OUT', 910, 520, 22, '#1a0a04', 800)
        for (a, b) in (((1250, 260), (1520, 560)), ((1520, 260), (1250, 560))):
            pen.line(poly([a, b], False), 26, '#ff7a1a', 220)
        # the number plaque 7
        pl = rrect(1240, 640, 150, 170, 14); pen.fill(pl, '#d8d4c8'); pen.line(pl, 4, P['outline'])
        _sign_text(pen, '7', 1315, 780, 130, '#2a2440', 900)
        _sign_text(pen, 'CABIN', 1315, 676, 26, '#2a2440', 900)
        # old search tape tangled on the rail
        pen.line(poly([(-200, 1180), (300, 1140), (520, 1190)], False), 18, P['tape'], 220)
        # hasp on the jamb
        pen.fill(rrect(640, 600, 70, 26, 6), P['metal']); pen.line(rrect(640, 600, 70, 26, 6), 3, P['outline'])
        pen.fill(oval(674, 640, 16), P['metal']); pen.line(oval(674, 640, 16), 3, P['outline'])
        # porch step and ground
        pen.fill(rect(-900, 1100, 3800, 600), '#2c3060'); pen.fill(rect(500, 1100, 820, 60), P['wood']); pen.line(rect(500, 1100, 820, 60), 3, P['outline'])

    def lock(pen, t):
        v = str(st.v('padlock', t))
        if v.startswith('tess_hand') or v.startswith('struck'): return
        sw = 3.0 * math.sin(t * 2.2) if v.startswith('hasp_open') else 0.0
        padlock(pen, 674, 700, 1.4, 0.6, sw, 1.0 if v.startswith('hasp_open') else 0.0)
    L = [_cl(1.0, wall, 'front', 'v2:c7front', NEAR), _live(0.98, lock, 'padlock', blur=0),
         _live(1.6, lambda pen, t: fireflies(pen, t, (-200, 0, 2100, 700), 6, 41), 'fireflies', blur=0),
         _live(0.9, lambda pen, t: motes(pen, t, (0, 0, 1920, 1080), 30, 51, None, '#dfe4ff', 0.08), 'dust', blur=0)]
    if any(_flash_on(st, tt) for tt in (st.t0, st.t1)):
        b = Beam(aim_fn((300, 1300), [(st.t0, 700, 680), (st.t0 + 1.2, 880, 560)], 1.0, 8, 7), w0=24, spread=0.3, spot=150, a=0.35)
        L.append(b.layer(0.95, 'beam'))
    sp = _sp('cabin_now/' + vname, L, {'padlock': Anchor(674, 700, 0.98, 1), 'tess_door': Anchor(560, 1240, 0.8, 1100),
                                        'door': Anchor(910, 1100, 1.0, 900)}, None)
    sp.info['world'] = 'ours'
    return sp


# ====================================================================== the bells: the real cracked bell and the fake perfect one
BRASS = '#c8963e'


def brass_bell(pen, cx, cy, s=1.0, rot=0.0, light=0.8, crack=True, vib=0.0, t=0.0, red=0.0, gleam=0.0, mouth=0.35, c=BRASS,
               clapper=0.0, patina=True, outline='#1d1408'):
    """A cast brass camp breakfast bell (about 260 px tall at s=1, mouth down at rot 0, centred on its waist): crown loop,
    shoulder, waist, flared sound bow, a thick lip with the mouth seen as an ellipse (the dark inside and the clapper),
    engraved bands, speculars, verdigris, THE CRACK in the rim (crack=True), vib = ringing (rim wobble lines),
    gleam = the fake bell's perfect shine."""
    cv = pen.cv
    cv.save(); cv.translate(cx, cy); cv.rotate(rot)
    if vib: cv.translate(vib * 2.5 * s * math.sin(t * 95), 0)
    k = s
    dark, mid, hi = _dk(c, 0.62), mix(_dk(c, 0.35), c, light), mix(c, '#fff4d0', 0.55 * light + 0.35 * gleam)
    # crown (the hanging loop) and the shoulder
    loop = ring_path(0, -150 * k, 22 * k, 13 * k)
    pen.fill(loop, mid); pen.line(loop, 3 * k, outline)
    body = smooth([(-30 * k, -128 * k), (30 * k, -128 * k), (52 * k, -104 * k), (60 * k, -40 * k), (70 * k, 30 * k), (96 * k, 86 * k),
                   (112 * k, 108 * k), (-112 * k, 108 * k), (-96 * k, 86 * k), (-70 * k, 30 * k), (-60 * k, -40 * k), (-52 * k, -104 * k)], True, 0.55)
    _L(pen, body, -112 * k, 0, 112 * k, 0, [_dk(dark, 0.3), dark, mid, hi, mid, dark, _dk(dark, 0.45)])
    if patina:
        for i in range(9):
            px, py = (-80 + 160 * _h(i, 71)) * k * 0.7, (-90 + 180 * _h(i, 72)) * k
            pen.fill(_blob(px, py, (6 + 12 * _h(i, 73)) * k, (4 + 8 * _h(i, 74)) * k, 8, i, 0.4), '#4a7a5a', int(90 * (1 - gleam)))
    pen.texture(body, 'grunge', 0.3 * (1 - gleam), 'multiply', 0.5 * k)
    # speculars: a long vertical streak and a hot spot on the sound bow
    _L(pen, body, -40 * k, 0, -10 * k, 0, [(0, '#ffffff', 0), (0.5, '#fff8e0', 110 * light + 100 * gleam), (1, '#ffffff', 0)])
    _R(pen, body, -46 * k, 74 * k, 34 * k, [(0, '#ffffff', 150 * light + 100 * gleam), (1, '#ffffff', 0)], sy=0.7)
    if red: _L(pen, body, 112 * k, 0, 0, 0, [(0, '#ff3a50', 170 * red), (1, '#ff3a50', 0)])
    # engraved bands
    for yy, hw in ((-96 * k, 50 * k), (-60 * k, 58 * k), (66 * k, 86 * k)):
        pen.seg((-hw, yy), (hw, yy), 2.4 * k, _dk(c, 0.55), 200)
        pen.seg((-hw, yy + 2.5 * k), (hw, yy + 2.5 * k), 1.2 * k, hi, 140)
    pen.line(body, 4 * k, outline)
    # the lip (thick rim) and the mouth ellipse: dark inside, the clapper
    mw, mh = 112 * k, 112 * k * mouth
    mo = oval(0, 112 * k, mw, mh)
    pen.fill(mo, _dk(c, 0.5)); pen.line(mo, 3.5 * k, outline)
    inner = oval(0, 112 * k + 3 * k, mw * 0.86, mh * 0.72)
    _R(pen, inner, 0, 112 * k - mh * 0.3, mw, [(0, '#0e0904'), (1, '#2a1c0c')])
    cl_x = clapper * 30 * k * math.sin(t * 9)
    pen.fill(oval(cl_x, 112 * k + mh * 0.1, 12 * k, 12 * k), dark); pen.line(oval(cl_x, 112 * k + mh * 0.1, 12 * k, 12 * k), 2 * k, outline)
    pen.line(oval(0, 112 * k, mw, mh), 2 * k, hi, 150)
    if crack:
        pts = [(40 * k, 112 * k + mh * 0.9), (44 * k, 100 * k), (37 * k, 86 * k), (46 * k, 70 * k), (40 * k, 52 * k), (44 * k, 40 * k)]
        pen.line(poly(pts, False), 3.6 * k, '#0e0904', 240); pen.line(poly([(x + 1.6 * k, y) for x, y in pts], False), 1.2 * k, hi, 160)
    if vib:
        for j in range(3):
            pen.line(oval(0, 112 * k, mw * (1.08 + 0.08 * j) + 6 * k * math.sin(t * 60 + j), mh * (1.2 + 0.2 * j)), 3 * k, '#fff2c8',
                     int(150 * vib * (1 - j * 0.3)))
    cv.restore()
    return body


def ring_path(cx, cy, r, w):
    return minus(oval(cx, cy, r, r), oval(cx, cy, r - w, r - w))


def _bell_plate(pen, day=False, sepia=False, boards=True):
    P = PAL['night']
    if sepia:
        pen.fill(rect(-900, -560, 3800, 2300), '#c9a878')
        for i in range(-10, 40): pen.seg((i * 90, -600), (i * 90 + 60, 1700), 6, '#8a6a48', 160)
        pen.texture(rect(-900, -560, 3800, 2300), 'wood', 0.35, 'overlay', 1.2, 90)
        return
    # crate interior / porch boards at night, lit warm by the beam
    pen.fill(rect(-900, -560, 3800, 2300), P['wood_dk'])
    for i in range(-10, 40):
        pen.fill(rect(i * 120, -600, 116, 2300), mix(P['wood'], P['wood_dk'], _h(i, 5)))
        pen.seg((i * 120, -600), (i * 120, 1700), 5, P['outline'], 200)
    pen.texture(rect(-900, -560, 3800, 2300), 'wood', 0.3, 'overlay', 1.4, 90)
    for i in range(40):
        x, y = _h(i, 81) * 2200 - 140, 700 + _h(i, 82) * 600
        pen.seg((x, y), (x + 90 * (_h(i, 83) - 0.5), y - 40 * _h(i, 84)), 4, '#c8a860', 200)       # straw


@view('mess_porch', 'bell_ecu')
def _v_bell_ecu2(var, st, shot):
    """The real bell in the crate: a cast brass bell lying in straw between the slats, the crack in its rim, the beam on it."""
    def bg(pen, t): _bell_plate(pen)

    def bl(pen, t):
        brass_bell(pen, 980, 560, 2.3, -62, 0.85, True, 0.0, t, 0.0, 0.0, 0.42)

    def slats(pen, t):
        P = PAL['night']
        for x in (-200, 1560):
            r = rect(x, -600, 520, 2300); pen.fill(r, P['wood']); pen.line(r, 6, P['outline'])
            pen.texture(r, 'wood', 0.3, 'overlay', 1.2, 90)
    L = [_cl(2.2, bg, 'crate_in', 'v2:bellbg', (-900, -560, 2820, 1640)), _cl(1.0, bl, 'bell', 'v2:bell_crate', FRAME),
         _cl(0.6, slats, 'slats', 'v2:bell_slats', NEAR)]
    bl_, b = S1._beam_layers(st, var if var else 'moon_flash', (2300, -500), [(st.t0, 960, 560), (st.t1, 1060, 600)], 1.0, 8, 29,
                             spot=420, dust_box=(0, 0, 1920, 1080), n_dust=50, a=0.22)
    L += bl_
    L.append(_live(0.9, lambda pen, t: _R(pen, None, 1000, 560, 520, [(0, '#ffd58a', 60), (1, '#ffd58a', 0)], clip=False), 'warm', blur=0))
    sp = _sp('mess_porch/bell_ecu', L, {'crack': Anchor(1130, 640, 1.0, 1), 'bell': Anchor(980, 560, 1.0, 1)}, None, beam=b)
    sp.info['world'] = 'ours'
    return sp


@view('mess_porch', 'bell_hit')
def _v_bell_hit2(var, st, shot):
    """CONTACT at 535.36: the bell on the porch boards, the padlock swung into the rim, the spark, a 2-frame white flash,
    the rim vibrating (wobble lines), the crack rattling; red rim light begins (the climax)."""
    ts = 535.36

    def bg(pen, t): _bell_plate(pen)

    def bl(pen, t):
        vib = math.exp(-(t - ts) * 2.0) if t >= ts else 0.0
        red = clamp((t - ts + 0.3) / 0.8) * 0.8
        brass_bell(pen, 900, 560, 2.2, -8, 0.85, True, vib, t, red, 0.0, 0.42, clapper=vib)
        # the padlock swinging in from the right on its shackle
        u = clamp((t - (ts - 0.4)) / 0.4)
        px = lerp(1900, 1210, ease_in_cubic(u)) + (40 * math.exp(-(t - ts) * 4) if t > ts else 0)
        py = lerp(260, 760, ease_in_cubic(u))
        padlock(pen, px, py, 3.0, 0.8, -30 * (1 - u), 1.0)
        if vib > 0.05:
            # the crack rattles: short jagged ticks along it
            for j in range(5):
                a = vib * (0.5 + 0.5 * math.sin(t * 70 + j))
                pen.seg((990 + j * 3, 760 - j * 32), (1004 + j * 3, 750 - j * 32), 3, '#fff2c8', int(220 * a))

    def flare(pen, t):
        if t < ts - 0.02: return
        u = t - ts
        k = math.exp(-u * 7)
        _R(pen, None, 1190, 770, 700, [(0, '#ffffff', 255 * k), (0.15, '#fff2d6', 200 * k), (1, '#fff2d6', 0)], clip=False)
        _R(pen, None, 1190, 770, 1600, [(0, '#fff2d6', 120 * k), (1, '#fff2d6', 0)], sy=0.04, clip=False)
        for j in range(14):
            ang = 2 * math.pi * _h(j, 3); d = 900 * u * (0.5 + _h(j, 4))
            pen.fill(oval(1190 + math.cos(ang) * d, 770 + math.sin(ang) * d + 400 * u * u, 5), '#ffe8b0', int(255 * max(0, 1 - u * 2)))
    L = [_cl(2.2, bg, 'boards', 'v2:bellbg', (-900, -560, 2820, 1640)), _live(1.0, bl, 'bell', blur=0), _live(0.95, flare, 'strike_flare', blur=0),
         _live(0.9, lambda pen, t: _R(pen, None, 1920, 400, 1200, [(0, '#ff2d55', 110 * clamp((t - ts) / 0.8)), (1, '#ff2d55', 0)],
                                      clip=False), 'red_rim', blur=0)]
    sp = _sp('mess_porch/bell_hit', L, {'contact': Anchor(1190, 770, 1.0, 1), 'bell': Anchor(900, 560, 1.0, 1)}, None)
    sp.info['world'] = 'climax'
    return sp


@view('cabin_dawn', 'far_porch')
def _v_far_porch(var, st, shot):
    """Telephoto through THEIR window: across the frozen lawn, the mess-hall porch with a GLEAMING bell swinging by itself
    (511.6-531.5 s): too perfect, clean rings (the rings are HUD)."""
    T = PAL['theirs']
    tb = st.ev('fake_bell')
    t_on = 511.9

    def bg(pen, t):
        _L(pen, rect(-900, -560, 3800, 2300), 0, -400, 0, 700, [T['sky0'], T['sky1'], '#fff0d0'])
        for i in range(12):
            pine(pen, -600 + i * 300, 640, 520 + 200 * _h(i, 4), i, '#8a9a70', '#ffe6b0', 80, 0, 9, 0.42)
        pen.fill(rect(-900, 640, 3800, 1100), '#a8b46a'); pen.texture(rect(-900, 640, 3800, 1100), 'grunge', 0.2, 'overlay', 1.0)
        # the mess hall porch (gold morning): posts, roof, the bracket where the bell hangs
        pen.fill(rect(300, 120, 1400, 560), '#d8a870'); pen.line(rect(300, 120, 1400, 560), 5, T['outline'])
        for i in range(12): pen.seg((300 + i * 120, 120), (300 + i * 120, 680), 3, T['seam'], 160)
        pen.fill(poly([(240, 130), (960, -160), (1760, 130)]), '#a9743f'); pen.line(poly([(240, 130), (960, -160), (1760, 130)]), 5, T['outline'])
        _sign_text(pen, 'MESS HALL', 1000, 210, 64, '#4a2a10', 900)
        for x in (360, 820, 1300, 1640):
            pen.fill(rect(x, 230, 40, 460), '#c48f55'); pen.line(rect(x, 230, 40, 460), 4, T['outline'])
        pen.fill(rect(300, 680, 1400, 50), '#a8763f'); pen.line(rect(300, 680, 1400, 50), 4, T['outline'])
        pen.fill(rrect(860, 250, 200, 30, 8), '#3a3430'); pen.line(rrect(860, 250, 200, 30, 8), 4, T['outline'])

    def bl(pen, t):
        sw = 22 * math.sin((t - t_on) * 2 * math.pi / 0.9) * clamp((t - t_on) / 0.3) if t >= t_on else 0.0
        brass_bell(pen, 960, 430, 1.05, sw, 1.0, False, 0.0, t, 0.0, 1.0, 0.3, c='#e0b050', patina=False)
        # perfect gleam star
        k = 0.6 + 0.4 * math.sin(t * 7)
        _R(pen, None, 920, 400, 60, [(0, '#ffffff', 220 * k), (1, '#ffffff', 0)], clip=False)
        pen.seg((920 - 40 * k, 400), (920 + 40 * k, 400), 2, '#ffffff', int(230 * k)); pen.seg((920, 400 - 40 * k), (920, 400 + 40 * k), 2, '#ffffff', int(230 * k))
    L = [_cl(3.0, bg, 'far_porch', 'v2:far_porch', (-900, -560, 2820, 1640)), _live(2.95, bl, 'fake_bell', blur=0),
         _live(1.5, lambda pen, t: frozen_motes(pen, t, (0, 0, 1920, 1080), 40, 61), 'motes', blur=0)]

    def frame(pen, t):
        # the window frame and gingham edges in the foreground (we look through THEIR window)
        P = PAL['theirs']
        for r in (rect(-900, -560, 860, 2300), rect(1980, -560, 900, 2300), rect(-900, -560, 3800, 300), rect(-900, 1000, 3800, 700)):
            pen.fill(r, P['paint'])
        pen.line(rect(-40, -260, 2020, 1260), 8, P['outline'])
        gingham(pen, rect(-900, -560, 1000, 2300), (-900, -560, 100, 1740), '#e9c64a', 0.6)
    L.append(_cl(0.5, frame, 'window_frame', 'v2:far_frame', NEAR, blur=6))
    sp = _sp('cabin_dawn/far_porch', L, {'bell': Anchor(960, 430, 2.95, 1)}, None)
    sp.info['world'] = 'theirs'
    return sp


@view('cabin_dawn', 'window_out')
def _v_window_out2(var, st, shot):
    """LOOP A through THEIR window: the frozen gold lawn, the sprinkler (the same arcs at 297.7 and 414.6: cue-timed),
    the pines, and the far mess-hall porch with ITS BELL (the fake one swings by itself from 511.6)."""
    T = PAL['theirs']
    cues = st.sfx_cues('sprinkler_spit')
    on = next((c['t'] for c in cues if not (c.get('params') or {}).get('loop_id') and (c.get('params') or {}).get('kind') != 'die'), None)
    spits = [c['t'] for c in cues if (c.get('params') or {}).get('loop_id')]
    die = next((c['t'] for c in cues if (c.get('params') or {}).get('kind') == 'die'), None)
    if spits and on is None: on = spits[0] - 0.4
    if spits and die is None: die = spits[-1] + 0.72
    fake_on = 511.9

    def outside(pen, t):
        _L(pen, rect(-900, -700, 3800, 1400), 0, -700, 0, 640, [T['sky0'], '#ffd8b0', T['sky1']])
        _R(pen, None, 600, 560, 900, [(0, '#fff2d0', 200), (1, '#fff2d0', 0)], sy=0.5, clip=False)
        treeline(pen, -900, 2900, 640, 300, 22, 181, '#7e8c5a', '#ffe6b0', 80)
        pen.fill(rect(-900, 640, 3800, 900), '#a8b45a')
        _L(pen, rect(-900, 640, 3800, 900), 0, 640, 0, 1400, [(0, '#ffe6a0', 120), (1, '#7a9a40', 255)])
        p = poly([(1180, 700), (1300, 700), (1700, 1400), (900, 1400)])
        pen.fill(p, '#e0c08a'); pen.texture(p, 'asphalt', 0.25, 'overlay')
        # the mess hall far off, gold in the low sun, its porch and the bell bracket
        pen.fill(rect(1300, 520, 420, 150), '#d8a870'); pen.line(rect(1300, 520, 420, 150), 3, T['outline'])
        pen.fill(poly([(1280, 524), (1510, 450), (1740, 524)]), '#a9743f'); pen.line(poly([(1280, 524), (1510, 450), (1740, 524)]), 3, T['outline'])
        for x in (1320, 1440, 1580, 1700): pen.fill(rect(x, 560, 10, 110), '#c48f55')
        pen.fill(rect(1300, 664, 420, 12), '#a8763f')
        grass(pen, -900, 2900, 1080, 40, 200, 183, '#7a9a40', '#fff2c0')

    def bell_far(pen, t):
        sw = 24 * math.sin((t - fake_on) * 2 * math.pi / 0.9) * clamp((t - fake_on) / 0.3) if t >= fake_on else 0.0
        brass_bell(pen, 1460, 600, 0.13, sw, 1.0, False, 0.0, t, 0.0, 1.0, 0.3, c='#e0b050', patina=False)
        if t >= fake_on:
            k = 0.6 + 0.4 * math.sin(t * 7)
            _R(pen, None, 1455, 592, 26, [(0, '#ffffff', 230 * k), (1, '#ffffff', 0)], clip=False)

    def spr(pen, t):
        sprinkler(pen, 900, 760, t, spits, on, die, 0.9, '#f4fbff')

    def frame(pen, t):
        P = T
        pen.fill(minus(rect(-900, -700, 3800, 2400), rect(160, 80, 1600, 920)), P['paint'])
        pen.texture(minus(rect(-900, -700, 3800, 2400), rect(160, 80, 1600, 920)), 'wood', 0.2, 'overlay', 1.0, 90)
        pen.line(rect(160, 80, 1600, 920), 10, _dk(P['paint'], 0.3)); pen.line(rect(140, 60, 1640, 960), 4, P['outline'])
        pen.seg((960, 80), (960, 1000), 26, P['paint']); pen.line(rect(947, 80, 26, 920), 3, P['outline'])
        pen.fill(rect(120, 990, 1680, 60), _dk(P['paint'], 0.08)); pen.line(rect(120, 990, 1680, 60), 4, P['outline'])
        for (cx0, cx1, sk) in ((-200, 260, 1), (1660, 2120, -1)):         # gingham frozen at 12 degrees
            cp = smooth([(cx0, 40), (cx1, 40), (cx1 - 10 + sk * 60, 1160), (cx0 + 10 + sk * 60, 1170)], True, 0.25)
            gingham(pen, cp, (cx0, 40, cx1, 1170), '#e9c64a', 2.0)
            pen.line(cp, 4, P['outline'], 200)
        lantern(pen, 560, 960, 1.1, 1.0, '#ffd9a0', '#3a4a3a', True)     # review round 2 (M8): on the sill's left, as in every view
    L = [_cl(4.0, outside, 'outside', 'v2:wout:out', (-900, -700, 2820, 1500)), _live(3.6, bell_far, 'fake_bell', blur=0),
         _live(3.0, spr, 'sprinkler', blur=0), _live(2.0, lambda pen, t: frozen_motes(pen, t, (160, 80, 1760, 1000), 40, 71), 'motes', blur=0),
         _cl(1.0, frame, 'window_frame', 'v2:wout:frame', NEAR)]
    sp = _sp('cabin_dawn/window_out', L, dict(sprinkler=Anchor(900, 760, 3.0, 1), bell_far=Anchor(1460, 600, 3.6, 1)), None)
    sp.info['world'] = 'theirs'
    return sp


# ====================================================================== MEMORY (sepia paper): the past cabin in 3D + relit v1 memories
PAST_CAMS = {
    'bunk_morning': ((3.15, 1.15, 3.3), (5.0, 0.75, 5.3), 62.0),
    'bunk_night': ((3.2, 2.0, 3.25), (5.0, 1.12, 5.3), 64.0),      # review round 2 (B17): high enough to see Noah on the top bunk
    'wake': ((4.05, 0.78, 4.1), (5.1, 0.55, 5.4), 52.0),
    'towel_wet': ((2.9, 0.55, 3.3), (3.4, 0.0, 5.6), 62.0),
    'socks': ((3.45, 0.95, 3.8), (4.85, 0.6, 5.0), 54.0),
    'open_window': ((2.65, 1.15, 3.9), (1.45, 0.85, 6.2), 62.0),
    'flash_445': ((3.25, 1.2, 4.15), (2.66, 0.85, 6.3), 62.0),
    'lantern_game': ((3.7, 1.45, 3.1), (2.5, 0.55, 6.0), 66.0),
    'kids_game': ((2.45, 1.3, 5.6), (3.4, 0.35, 2.0), 68.0),
}


def memory_gate_layer(seed=0):
    """The film gate over a memory: rounded corners (radius 6 % of H), soft edge falloff, specks, a 1 px gate weave."""
    def draw(pen, t):
        fi = int(t * 24)
        dx, dy = (_h(fi, seed) - 0.5) * 2.0, (_h(fi, seed + 1) - 0.5) * 2.0
        cv = pen.cv
        cv.save(); cv.translate(dx, dy)
        r = 0.06 * 1080
        hole = rrect(14, 10, 1892, 1060, r)
        pen.fill(minus(rect(-200, -200, 2320, 1480), hole), '#120c08')
        _L(pen, hole, 0, 0, 1920, 0, [(0, '#2a1c10', 90), (0.08, '#2a1c10', 0), (0.92, '#2a1c10', 0), (1, '#2a1c10', 90)])
        for i in range(5):
            if _h(fi * 7 + i, seed + 2) < 0.55:
                x, y = _h(fi * 7 + i, seed + 3) * 1920, _h(fi * 7 + i, seed + 4) * 1080
                rr = 1.2 + 3.0 * _h(fi * 7 + i, seed + 5)
                pen.fill(_blob(x, y, rr, rr * 0.7, 7, fi + i, 0.4), '#1a1008' if _h(fi + i, 9) < 0.7 else '#fff6e0', 170)
        if _h(fi, seed + 6) < 0.18:                                  # a hair / scratch now and then
            x = _h(fi, seed + 7) * 1920
            pen.seg((x, 0), (x + 6, 1080), 1.0, '#fff6e0', 70)
        cv.restore()
    return Layer(1.0, draw, 'memory_gate', screen=True, blur=0)


def past_view(vname, var, st, shot):
    var = var or 'sepia_day'
    cx = CabinCtx('past', var, st, st.t0)
    pos, look, fov = PAST_CAMS[vname]
    cam = Cam3(pos, look=look, fov=fov)
    d0 = max(0.8, cam.dist(v3(look)) * 0.8)
    L, sc, info, xf = cabin_layers(cx, cam, 'past_' + vname, d0)
    if cx.dark:
        lp = cam.pt(v3(WIN[1] - 0.12, WIN[2] + 0.14, D - 0.08)); k = cam.px_per_m(v3(WIN[1] - 0.12, WIN[2], D - 0.08))
        dep = sdep(cam, xf, d0, v3(WIN[1] - 0.12, WIN[2], D - 0.08), 0.003)
        L.append(_live(dep, lambda pen, t: (_R(pen, None, lp[0], lp[1], 0.9 * k, [(0, '#ffd9a0', 120 * (0.9 + 0.1 * math.sin(t * 9))),
                                                                              (1, '#ffd9a0', 0)], clip=False),
                                           moths(pen, t, lp[0], lp[1], 0.25 * k, 5, 3, '#f1e2c4')), 'lantern', blur=0))
    else:
        L += shaft_layer(cam, xf, d0, 'past:%s:%s' % (vname, var), cx.P, True, 40)
    L.append(_live(0.9, lambda pen, t: motes(pen, t, (0, 0, 1920, 1080), 40, 93, None, '#fff6e0', 0.14, speed=(4, 9)), 'motes', blur=0))
    if vname == 'towel_wet':          # critic B5: the same striped towel lying wet between the bunks (it was missing)
        q = [cam.pt(v3(p_)) for p_ in ((3.0, 0.01, 4.85), (3.85, 0.01, 4.7), (3.95, 0.01, 5.25), (3.05, 0.01, 5.45))]
        bx = (min(p_[0] for p_ in q), min(p_[1] for p_ in q), max(p_[0] for p_ in q), max(p_[1] for p_ in q))
        dep_t = sdep(cam, xf, d0, v3(3.45, 0.0, 5.05), 0.004)

        def _towel(pen, t, q=q, bx=bx):
            pth = smooth([q[0], ((q[0][0] + q[1][0]) / 2, (q[0][1] + q[1][1]) / 2 + 6), q[1], q[2],
                          ((q[2][0] + q[3][0]) / 2, (q[2][1] + q[3][1]) / 2 - 5), q[3]], True, 0.3)
            pen.fill(moved(pth, 4, 7), '#000000', 70)
            towel_cloth(pen, pth, bx, 1.0, wet=0.8, seed=4, lit=0.85)
            pen.line(pth, 2.0, '#3a2a1a', 160)
        L.append(_live(dep_t, _towel, 'towel_wet', blur=None))
    L.append(memory_gate_layer())
    an = _ours_anchors(cam, xf, d0)
    for nm, P_, hh in (('kid_bunk', (5.1, B_LOW, 5.3), 1.25), ('noah_top', (5.1, B_TOP, 5.3), 1.5), ('kid_floor', (3.4, 0, 4.6), 1.25),
                       ('kids_floor', (3.2, 0, 4.0), 1.25), ('noah_mirror', (2.66, 0, 5.6), 1.5)):
        if cam.dist(v3(P_)) > 0.2:
            x, y, h, dep = cam.anchor(v3(P_), hh, d0); an[nm] = Anchor(x, y, dep, h)
    return _sp('memory/' + vname, L, an, None, 1.0, 0.0, None, dict(info, cam3=cam, d0=d0, xf=xf, model=sc, world='memory'))


def _reg_past(vname):
    @view('memory', vname)
    def _v(var, st, shot, vname=vname):
        return past_view(vname, var, st, shot)
    return _v


for _vn in PAST_CAMS:
    _reg_past(_vn)

_MEMVAR = {'sepia_day': 'memory_day', 'sepia_night': 'memory_night', 'sepia_morning': 'memory_morning'}


def _mem(view1, zoom=None, flip=False, extra=None):
    def fn(var, st, shot):
        v1var = _MEMVAR.get(var or 'sepia_day', 'memory_day')
        sp = v1_alias('memory', view1, v1var, st, shot, 'sepia', 'memory/%s' % shot.get('view'), zoom, flip, extra)
        for l in sp:                     # v1's cream mist / halation layers are live: tone them down under the sepia grade
            if not l.cache and l.name in ('mist', 'halation', 'haze', 'fog', 'glow', 'sun', 'motes', 'light', 'mem_mist', 'mem_motes'):
                l.alpha = 0.45
        sp.append(memory_gate_layer())
        return sp
    return fn


def _sepia_cl(draw, key, depth=1.0, bounds=NEAR):
    l = Layer(depth, draw, key, cache='v2mem:' + key, bounds=bounds)
    l.relight = relight_sepia
    return l


def _kitchen_props(sp, st):
    """At least eight props in the kitchen memories (the v1 kitchen wall was bare): shelf with pots, ladles on hooks, a
    coffee urn, mugs, a stack of plates, a wall clock, the pass-through counter, a fly swatter, a calendar."""
    def draw(pen, t):
        pen.fill(rect(-900, 760, 3800, 900), '#9a7a58'); pen.line(rect(-900, 760, 3800, 30), 4, '#3a2c20')
        pen.fill(rect(-900, 760, 3800, 30), '#c9a878')
        pen.fill(rect(120, 250, 700, 22), '#7a5c3e'); pen.line(rect(120, 250, 700, 22), 3, '#3a2c20')
        for i, (x, w_, h_) in enumerate(((160, 120, 90), (320, 150, 120), (520, 110, 80), (660, 130, 100))):
            pen.fill(rrect(x, 250 - h_, w_, h_, 10), '#a89a84'); pen.line(rrect(x, 250 - h_, w_, h_, 10), 3, '#3a2c20')
            pen.fill(rect(x - 10, 250 - h_ - 8, w_ + 20, 10), '#7a6a5a')
        for i in range(5):
            x = 150 + i * 140
            pen.seg((x, 330), (x, 470), 6, '#8a7a6a'); pen.fill(oval(x, 480, 26, 14), '#8a7a6a'); pen.line(oval(x, 480, 26, 14), 3, '#3a2c20')
        pen.fill(rrect(1500, 430, 170, 330, 30), '#b0a090'); pen.line(rrect(1500, 430, 170, 330, 30), 4, '#3a2c20')
        pen.fill(rect(1560, 620, 50, 30), '#4a3a2c'); _sign_text(pen, 'COFFEE', 1585, 520, 26, '#3a2c20', 900)
        for i in range(4):
            pen.fill(rrect(1000 + i * 80, 700, 60, 60, 8), ['#6f9a96', '#d08a52', '#f1e2c4', '#6f9a96'][i]); pen.line(rrect(1000 + i * 80, 700, 60, 60, 8), 3, '#3a2c20')
        for i in range(6):
            pen.fill(oval(1250, 740 - i * 12, 80, 16), '#f1e2c4'); pen.line(oval(1250, 740 - i * 12, 80, 16), 2, '#3a2c20')
        pen.fill(oval(1760, 200, 70), '#e8d8b8'); pen.line(oval(1760, 200, 70), 5, '#3a2c20')
        pen.seg((1760, 200), (1760, 150), 5, '#3a2c20'); pen.seg((1760, 200), (1800, 200), 5, '#3a2c20')
        pen.fill(rect(900, 160, 150, 200), '#f6ead2'); pen.line(rect(900, 160, 150, 200), 3, '#3a2c20')
        _sign_text(pen, 'JULY', 975, 200, 30, '#8a3a2a', 900)
        pen.seg((1880, 300), (1840, 620), 6, '#7a5c3e'); pen.fill(rrect(1800, 230, 90, 90, 10), '#6f9a96', 200)
    return [_sepia_cl(draw, 'kitchen_props', 0.9)]


def _spoon_live(sp, st):
    """The spoon drops on the table and bounces (the simile gets its shot)."""
    t_drop = st.t0 + 0.2

    def draw(pen, t):
        u = t - t_drop
        if u < 0: y = 300; rot = -20
        else:
            y = min(760, 300 + 2400 * u * u)
            if 300 + 2400 * u * u >= 760:
                ub = u - math.sqrt(460 / 2400.0)
                y = 760 - 120 * abs(math.sin(ub * 9)) * math.exp(-ub * 5)
            rot = -20 + 300 * min(u, 0.6)
        pen.cv.save(); pen.cv.translate(960, y); pen.cv.rotate(rot)
        pen.fill(oval(-90, 0, 46, 30), '#d8d0c0'); pen.line(oval(-90, 0, 46, 30), 4, '#3a2c20')
        pen.fill(rrect(-50, -9, 220, 18, 9), '#d8d0c0'); pen.line(rrect(-50, -9, 220, 18, 9), 4, '#3a2c20')
        pen.fill(oval(-100, -8, 18, 9), '#ffffff', 160)
        pen.cv.restore()
    return [_live(0.95, draw, 'spoon', blur=0)]


def _car_overlay(sp, st):
    def draw(pen, t):
        body = rrect(1050, 600, 760, 300, 70)
        pen.fill(rect(1080, 880, 700, 30), '#2a2018', 120)
        pen.fill(body, '#8a7a6a'); pen.line(body, 5, '#3a2c20')
        pen.fill(rrect(1150, 520, 520, 150, 50), '#7a6a5a'); pen.line(rrect(1150, 520, 520, 150, 50), 5, '#3a2c20')
        pen.fill(rrect(1190, 545, 200, 110, 20), '#f1e2c4'); pen.fill(rrect(1420, 545, 220, 110, 20), '#e8d8b8')
        for x in (1180, 1680): pen.fill(oval(x, 900, 70), '#2a2018'); pen.fill(oval(x, 900, 30), '#a89a84')
        pen.fill(oval(1800, 720, 26, 18), '#fff6e0')
    return [_sepia_cl(draw, 'moms_car', 0.95)]


def _payphone(sp, st):
    def draw(pen, t):
        pen.fill(rrect(1380, 200, 260, 560, 20), '#7a6a5a'); pen.line(rrect(1380, 200, 260, 560, 20), 5, '#3a2c20')
        pen.fill(rrect(1420, 260, 180, 120, 10), '#c9a878'); _sign_text(pen, 'PHONE', 1510, 330, 40, '#3a2c20', 900)
        for r_ in range(4):
            for c_ in range(3):
                pen.fill(oval(1460 + c_ * 50, 450 + r_ * 50, 16), '#e8d8b8'); pen.line(oval(1460 + c_ * 50, 450 + r_ * 50, 16), 2, '#3a2c20')
        pen.line(smooth([(1400, 420), (1300, 600), (1250, 760)], False), 8, '#3a2c20')
    return [_sepia_cl(draw, 'payphone', 1.0)]


def _percolator(sp, st):
    def draw(pen, t):
        pen.fill(rect(500, 760, 920, 60), '#4a3a2c'); pen.line(rect(500, 760, 920, 60), 4, '#1a120c')
        pot = smooth([(850, 760), (1070, 760), (1040, 420), (880, 420)], True, 0.4)
        pen.fill(pot, '#b0a090'); pen.line(pot, 5, '#3a2c20')
        pen.fill(oval(960, 400, 60, 30), '#d8c8b0'); pen.line(oval(960, 400, 60, 30), 4, '#3a2c20')
        pen.fill(oval(960, 375, 26, 26), '#f1e2c4'); pen.line(oval(960, 375, 26, 26), 4, '#3a2c20')
        pen.line(smooth([(1060, 500), (1140, 520), (1120, 660), (1050, 680)], False), 14, '#3a2c20')
        _R(pen, None, 960, 800, 200, [(0, '#ffb070', 160), (1, '#ffb070', 0)], sy=0.3, clip=False)

    def bubble(pen, t):
        k = 0.5 + 0.5 * math.sin(t * 14)
        _R(pen, None, 960, 372, 22, [(0, '#ffffff', 160 * k), (1, '#ffffff', 0)], clip=False)
        for i in range(4):
            ph = (t * 0.5 + i * 0.25) % 1.0
            _R(pen, None, 960 + 30 * math.sin(t + i), 340 - ph * 300, 30 + 50 * ph, [(0, '#fff6e0', 90 * (1 - ph)), (1, '#fff6e0', 0)],
               sy=1.5, clip=False)
    return [_sepia_cl(draw, 'percolator', 1.0), _live(0.98, bubble, 'perc_steam', blur=0)]


for _vn, args in {
        'dock': ('dock',), 'pocket': ('pocket',), 'red_candy': ('pocket',), 'porch_drop': ('porch_steps',),
        'bell_ring_porch': ('bell_ring_porch',), 'sprinkler_lawn': ('sprinkler_lawn',), 'watch_cu': ('watch_cu',),
        'card_queen': ('card_queen',), 'kids_mouths': ('kids_game',), 'bench': ('bench',), 'breakfast_table': ('breakfast_table',),
        'night_window': ('night_window',), 'search_pines': ('search_pines',), 'search_window': ('search_pines',),
        'kitchen_staff': ('kitchen_staff',), 'director': ('kitchen_staff',), 'buses': ('buses',), 'bus_window': ('buses', (1225, 600, 1.8)),
        'gate_close': ('gate_close',), 'crate_bell': ('storage_shed',), 'run_barefoot': ('path_run',), 'bus_run': ('path_run',),
        'legs': ('porch_steps',), 'officer': ('porch_steps',), 'polaroid': ('polaroid',), 'dad_photo': ('polaroid',),
        'tape_wrap': ('polaroid',), 'car_door': ('polaroid',)}.items():
    VIEWS[('memory', _vn)] = _mem(*args)
VIEWS[('memory', 'menu_board')] = _mem('kitchen', extra=_kitchen_props)
VIEWS[('memory', 'kitchen_15')] = _mem('kitchen', extra=_kitchen_props)
VIEWS[('memory', 'office_phone')] = _mem('kitchen', extra=lambda sp, st: _kitchen_props(sp, st) + _payphone(sp, st))
VIEWS[('memory', 'percolator')] = _mem('kitchen', extra=lambda sp, st: _kitchen_props(sp, st) + _percolator(sp, st))
VIEWS[('memory', 'spoon')] = _mem('breakfast_table', extra=_spoon_live)
VIEWS[('memory', 'moms_car')] = _mem('gate_close', extra=_car_overlay)
VIEWS[('memory', 'car_20')] = _mem('gate_close', zoom=(1300, 600, 1.6), extra=_car_overlay)


@view('memory', 'bell_ecu')
def _v_mem_bell2(var, st, shot):
    """D8 planted (and 523.4): the cracked bell ringing on the porch boards, sepia: the real bell, not a cone."""
    def bg(pen, t): _bell_plate(pen, sepia=True)
    ts = st.t0 + 0.25

    def bl(pen, t):
        vib = math.exp(-(t - ts) * 2.0) if t >= ts else 0.0
        brass_bell(pen, 940, 560, 2.2, -10, 0.9, True, vib, t, 0.0, 0.0, 0.42, c='#c9a878', clapper=vib, outline='#3a2c20')
    L = [_sepia_cl(bg, 'mem_bell_bg', 2.0, (-900, -560, 2820, 1640)), _live(1.0, bl, 'bell', blur=0),
         _live(0.9, lambda pen, t: motes(pen, t, (0, 0, 1920, 1080), 30, 95, None, '#fff6e0', 0.14), 'motes', blur=0), memory_gate_layer()]
    sp = _sp('memory/bell_ecu', L, {'bell': Anchor(940, 560, 1.0, 1), 'rim': Anchor(1120, 760, 1.0, 1)}, None)
    sp.info['world'] = 'memory'
    return sp


# ====================================================================== bokeh plates (every CU / ECU sits on one: 4.7)
BOKEH = {
    'ours': ['#5a5fa8', '#7b80c8', '#7b80c8', '#5a5fa8', '#ffd58a', '#7b80c8', '#ffd58a'],
    'ending': ['#5a5fa8', '#7b80c8', '#ffd58a', '#f0a84e', '#7b80c8'],
    'theirs': ['#ffcf8a', '#f6b9a0', '#ffcf8a', '#ffe2a8'],
    'climax': ['#c2185b', '#ff2d55', '#c2185b', '#ae3a6a'],
    'stairs': ['#c63449', '#9fa8ff', '#ffcf8a', '#ff4060', '#6a4a8e'],
    'memory': ['#f1e2c4', '#fff6e0'],
}


def bokeh_discs(palette, seed=0, n=12, depth=4.0, alpha=1.0, name='bokeh'):
    """Out-of-focus light discs: diameter 45-165 design px, a little brighter than the surround (+22-38 luma), drifting
    3-8 px/s and breathing; a faint brighter rim like a real lens."""
    cols = BOKEH[palette]

    def draw(pen, t):
        for i in range(n):
            r = 22 + 60 * _h(i, seed + 1)
            sp_ = 3 + 5 * _h(i, seed + 2); ang = 6.283 * _h(i, seed + 3)
            x = -100 + ((_h(i, seed + 4) * 2120 + math.cos(ang) * sp_ * t) % 2120)
            y = -60 + ((_h(i, seed + 5) * 1200 + math.sin(ang) * sp_ * t) % 1200)
            c = cols[i % len(cols)]
            b = alpha * (0.75 + 0.25 * math.sin(t * (0.6 + 0.5 * _h(i, seed + 6)) + i))
            _R(pen, None, x, y, r, [(0, c, 70 * b), (0.78, c, 84 * b), (0.9, c, 110 * b), (1, c, 0)], clip=False)
    return _live(depth, draw, name, blur=0)


def bokeh_from(sp, palette, seed=0, blur=16.0, dim=0.04, n=12):
    """Turn a set into a bokeh plate: every set layer far behind (blurred, a little dimmed), plus drifting discs."""
    out = []
    for l in sp:
        if l.name in ('beam', 'dust', 'moths', 'lipstick', 'glass_glint', 'clock_hands', 'drips', 'drop', 'edge_glow'): continue
        if callable(l.depth): continue
        l.blur = blur
        if l.cache: l.dim = dim
        l.depth = max(l.depth, 1.0) * 3.0; l.ref_depth = l.ref_depth * 3.0 if l.ref_depth >= 1.0 else 3.0 * max(1.0, l.depth / 3.0)
        out.append(l)
    out.append(bokeh_discs(palette, seed, n, 2.6))
    sp2 = SetPiece(sp.name, out, {'face': Anchor(960, 560, 1.0, 1.0)}, sp.grade, 1.0, 6.75, None, sp._fx, dict(sp.info, insert=True, bokeh=palette))
    return sp2


def _pal_for(set_, var):
    if var in ('red',): return 'climax'
    if set_ == 'cabin_dawn': return 'theirs'
    if set_ == 'stairs': return 'stairs'
    if set_ == 'memory': return 'memory'
    if var in ('after', 'phone_glow'): return 'ending'
    return 'ours'


@view('cabin_now', 'bokeh')
def _v_bokeh_ours(var, st, shot):
    views = ['three_q', 'reverse', 'master', 'profile']
    vname = views[int(_h(int(float(shot.get('t0', 0)) * 10), 7) * len(views))]
    base = ours_view(vname, var or 'night', st, shot)
    return bokeh_from(base, _pal_for('cabin_now', var), int(st.t0))


@view('cabin_dawn', 'bokeh')
def _v_bokeh_theirs(var, st, shot):
    views = ['bunk_2s', 'master', 'window', 'reverse']
    vname = views[int(_h(int(float(shot.get('t0', 0)) * 10), 7) * len(views))]
    base = theirs_view(vname, var or 'dawn', st, shot)
    return bokeh_from(base, _pal_for('cabin_dawn', var), int(st.t0))


@view('stairs', 'bokeh')
def _v_bokeh_stairs(var, st, shot):
    base = stairs_view('up' if st.t0 > 400 else 'low', var or 'stairs', st, shot)
    return bokeh_from(base, _pal_for('stairs', var), int(st.t0))


@view('stairs', 'queen_ecu')
def _v_queen_ecu(var, st, shot):
    base = stairs_view('low', var or 'red', st, shot)
    sp = bokeh_from(base, _pal_for('stairs', var), 13, 20.0, 0.2, 14)
    # the chipped white frame edge on the left (inside the glass, flash-forward of 605 s)
    def edge(pen, t):
        _frame_draw(PAL['night'])(pen, 0, 0) if False else None
        r = rect(-200, -300, 150, 1700); pen.fill(r, '#e8e4d8'); pen.line(r, 6, LINE)
        for i in range(8):
            pen.fill(_blob(-60, 100 + i * 130, 14, 20, 8, i, 0.4), '#8f8a7e')
    sp.append(_cl(0.9, edge, 'frame_edge', 'v2:qecu_edge', NEAR))
    return sp


def _bokeh_v1(set1, view1, pal):
    def fn(var, st, shot):
        base = v1_alias(set1, view1, _night_var(st), st, shot, 'night', '%s/bokeh' % shot.get('set'))
        return bokeh_from(base, pal, int(st.t0))
    return fn


VIEWS[('camp_gate', 'bokeh')] = _bokeh_v1('camp_gate', 'wide', 'ours')
VIEWS[('camp_path', 'bokeh')] = _bokeh_v1('camp_path', 'path_track', 'ours')
VIEWS[('mess_porch', 'bokeh')] = _bokeh_v1('mess_porch', 'wide', 'ours')


# ====================================================================== OURS inserts on the 3D model
OURS_INSERTS = {
    'clock': ((1.15, 2.05, 5.75), (1.15, 2.12, 6.4), 34.0),
    'cubby': ((4.45, 2.15, 5.0), (5.45, 2.1, 5.85), 44.0),
    'sill': ((1.82, 1.25, 5.62), (1.75, 0.96, 6.3), 42.0),
    'hands': ((2.3, 1.05, 4.6), (2.66, 0.7, 6.3), 52.0),
    'towel_label': None,
}


def _reg_ours_insert(vname):
    @view('cabin_now', vname)
    def _v(var, st, shot, vname=vname):
        pos, look, fov = OURS_INSERTS[vname]
        cam = Cam3(pos, look=look, fov=fov)
        sp = ours_view(vname, var or 'night', st, shot, cam=cam, d0=max(0.4, cam.dist(v3(look))))
        if vname == 'hands':           # a plate for the hand inserts: the room soft behind the hands
            for l in sp:
                if l.cache: l.blur = 10.0; l.dim = 0.1
            sp.dof = 6.75
            sp.info['insert'] = True
        return sp
    return _v


for _vn in ('clock', 'cubby', 'sill', 'hands'):
    _reg_ours_insert(_vn)
VIEWS[('cabin_now', 'towel_label')] = _ext('cabin_now', 'towel_label', 'flash')
VIEWS[('cabin_now', 'phone_screen')] = _ext('cabin_now', 'phone_screen', 'phone_glow')
VIEWS[('cabin_now', 'towel_over')] = lambda var, st, shot: mirror_view('towel_over', 'night', st, shot)


# ====================================================================== splits and plates
def split_view(var, st, shot):
    """Two panels side by side (D4 floors, D5 eyes, the loop twins, the bells): each panel is a full set view centred in
    its half (the divider, labels and chips are HUD)."""
    panels = (shot.get('split') or {}).get('panels') or []
    L = []
    an = {}
    for side_i, pan in enumerate(panels[:2]):
        sh2 = dict(shot); sh2['set'], sh2['view'], sh2['var'] = pan['set'], pan['view'], pan['var']
        if pan.get('src_t') is not None:
            dt = float(pan['src_t']) - float(shot['t0'])
            sh2['t0'], sh2['t1'] = float(shot['t0']) + dt, float(shot['t1']) + dt
        try:
            sp = S1.build(pan['set'], pan['view'], pan['var'], sh2)
        except Exception:
            continue
        ox = -480 if side_i == 0 else 480
        dt_ = (float(pan['src_t']) - float(shot['t0'])) if pan.get('src_t') is not None else 0.0
        for l in sp:
            d0 = l.draw

            def dr(pen, t, d0=d0, ox=ox, dt_=dt_, si=side_i):
                cv = pen.cv
                cv.save()
                cv.clipRect(skia.Rect.MakeLTRB(-2000 if si == 0 else 960, -2000, 960 if si == 0 else 4000, 4000))
                cv.translate(ox, 0)
                d0(pen, t + dt_)
                cv.restore()
            l.draw = dr
            if l.cache:
                l.cache = '%s:split%d' % (l.cache if isinstance(l.cache, str) else 'u%d' % l._uid, side_i)
                l.bounds = NEAR
            L.append(l)
        for k, a in sp.anchors.items():
            an['%s_%s' % ('L' if side_i == 0 else 'R', k)] = Anchor(a.x / 1.0 + ox, a.y, a.depth, a.height)
    sp = _sp('split/' + shot.get('view', 'x'), L, an, None)
    sp.info['world'] = 'split'
    return sp


for _vn in ('bells', 'eyes', 'floors', 'twins'):
    VIEWS[('split', _vn)] = split_view


# ====================================================================== live props that change inside a shot
def phone_live(cam, xf, d0, st, info):
    """Tess's phone face up on the sill (110.71 -> 674.43): black glass reflecting the moon, a red glint from 118.87."""
    O, P_ = info['phone_spot']
    if cam.dist(xf.p(P_)) < 0.12: return None
    dep = sdep(cam, xf, d0, P_, 0.004)

    def draw(pen, t):
        v = str(st.v('phone', t))
        if not v.startswith('sill'): return
        red = 1.0 if ('red' in v or t >= 118.87) else 0.0

        def ph(p, w, h):
            p.fill(rrect(0, 0, w, h, 1.2), '#1a1c2c'); p.line(rrect(0, 0, w, h, 1.2), 0.35, '#7a80b0')
            _L(p, rrect(0.5, 0.5, w - 1, h - 1, 1.0), 0, 0, w, h, ['#20284a', '#06070e', '#141a34'])
            _L(p, poly([(0, h * 0.2), (w, h * 0.05), (w, h * 0.15), (0, h * 0.32)]), 0, 0, 0, h,
               [(0, '#dfe6ff', 0), (0.5, '#dfe6ff', 100), (1, '#dfe6ff', 0)])
            p.fill(oval(w * 0.66, h * 0.22, 1.1), '#e8ecff', 200)                          # the moon in its glass
            if red:
                _R(p, None, w * 0.6, h * 0.4, w * 0.75, [(0, GLOW, 150 * (0.75 + 0.25 * math.sin(t * 3.1))), (1, GLOW, 0)], clip=False)
        draw_plane(pen, cam, xf, O, (1, 0, 0), (0, 0, -1), 7.4, 15, ph, True, 0.01)
    return _live(dep, draw, 'phone', blur=None)


def flashlight_floor_live(cam, xf, d0, st, var):
    """The ending: the flashlight lies on the floor and rakes a warm pool across the boards (dust in its beam)."""
    src = v3(2.25, 0.06, 3.35); aim = v3(3.7, 0.0, 5.35)
    if cam.dist(xf.p(src)) < 0.15: return []
    s2, a2 = cam.pt(xf.p(src)), cam.pt(xf.p(aim))
    k = cam.px_per_m(xf.p(src))
    dep = sdep(cam, xf, d0, (src + aim) / 2, 0.004)

    def body(pen, t):
        ang = math.degrees(math.atan2(a2[1] - s2[1], a2[0] - s2[0]))
        pen.cv.save(); pen.cv.translate(*s2); pen.cv.rotate(ang)
        L_, R_ = 0.24 * k, 0.03 * k
        pen.fill(rrect(-L_, -R_, L_, 2 * R_, R_), '#2a2c38'); pen.line(rrect(-L_, -R_, L_, 2 * R_, R_), max(1.0, 0.005 * k), LINE)
        pen.fill(rrect(-0.05 * k, -R_ * 1.3, 0.05 * k, 2.6 * R_, R_ * 0.5), '#8a8ea8'); pen.fill(oval(0, 0, R_ * 0.4, R_ * 1.1), '#fff3d6')
        pen.cv.restore()
    b = Beam(lambda t: (s2[0], s2[1], a2[0], a2[1], 0.85 + 0.03 * math.sin(t * 7)), w0=10.0, spread=0.36, spot=0.0, a=0.28)
    pool = _live(dep, lambda pen, t: (_R(pen, None, a2[0], a2[1], 1.1 * cam.px_per_m(xf.p(aim)),
                                         [(0, '#ffd58a', 120), (0.4, '#f0a84e', 60), (1, '#f0a84e', 0)], sy=0.35, clip=False)), 'pool', blur=None)
    return [pool, b.layer(dep * 0.999, 'floor_beam', spot=False), _live(dep * 0.998, body, 'flashlight', blur=None),
            _live(dep * 0.997, lambda pen, t: motes(pen, t, (min(s2[0], a2[0]) - 200, min(s2[1], a2[1]) - 300, max(s2[0], a2[0]) + 200,
                                                             max(s2[1], a2[1]) + 60), 40, 151, b, amb=0.04), 'beam_dust', blur=0)]


def prints_live(cam, xf, d0, st):
    """THEIRS: two trails of wet footprints from the wash-house door to Noah's bunk (THEIRS world coords). Review round 2 (B1):
    each print appears on its own wet_footstep cue of the sound plan (params trail A / B, i, bare), 26 cm long, dark wet wood
    with a sheen and a small splash glint as it lands; trail A is bare feet, trail B a shoe print then a bare foot. After the
    walk (173.7 s) both trails stay on the floor, drying slowly."""
    cues = [c for c in S1._plan_cues(163.0, 174.5) if c['name'] == 'wet_footstep' and (c.get('params') or {}).get('trail')]
    if cues and st.t1 < 163.9: cues = []
    track = [(float(c['t']), c['params']['trail'], int(c['params'].get('i', 0)), 'bare' if c['params'].get('bare', True) else 'shoe') for c in cues]
    if not track and 173.7 < st.t0 < 545:
        track = [(0.0, 'A', i, 'bare') for i in range(7)] + [(0.0, 'B', i, 'shoe' if i % 2 == 0 else 'bare') for i in range(7)]
    if not track: return None
    door, end = v3(1.62, 0, 0.2), v3(1.26, 0, 4.42)
    dz = norm(end - door); side = v3(dz[2], 0, -dz[0])                        # across the trail
    pts = []
    for (tt, trail, i, kind) in track:
        u = (i + 0.5) / 7.0
        left = (i % 2 == 0)
        P_ = door + (end - door) * u + side * ((-0.16 if trail == 'A' else 0.16) + (0.065 if left else -0.065))
        pts.append((tt, P_, kind, left))
    ang = math.degrees(math.atan2(dz[0], dz[2]))
    out = []
    for j, (tt, P_, kind, left) in enumerate(pts):
        if cam.dist(P_) < 0.25: continue

        def draw(pen, t, tt=tt, P_=P_, kind=kind, left=left):
            if t < tt: return
            k = clamp((t - tt) / 0.1)
            dry = 1.0 - 0.3 * clamp((t - tt) / 40.0)
            sp = clamp(1.0 - (t - tt) / 0.35)

            def fp(p, w, h):
                footprint(p, w / 2, h / 2, 0.28, kind, ang, k * dry, left, '#4a2e10', '#fff6dc')
                footprint(p, w / 2, h / 2, 0.28, kind, ang, 0.45 * k * dry, left, '#3a2208', '#ffffff')
                if sp > 0.01:                                                    # the splash as it lands
                    p.fill(oval(w / 2, h / 2, 16 * (1.4 - sp)), '#fff6dc', int(120 * sp))
            draw_plane(pen, cam, ID, P_ + v3(-0.17, 0.002, 0.22), (1, 0, 0), (0, 0, -1), 34, 44, fp, True, 0.01)
        # each print on the floor band at its own distance (one layer at the trail's middle hid the prints in the near band)
        out.append(_live(sdep(cam, xf, d0, P_, 0.003), draw, 'print%d' % j, blur=None))
    return out or None


def door_wash_live(cam, d0, st):
    """THEIRS: the wash-house door swings in (door_creak cue), wet morning light on the boards."""
    cues = st.sfx('door_creak')
    t_open = cues[0] if cues else st.t0 + 0.2
    hx = flip(DOOR[1])

    def draw(pen, t):
        a = math.radians(78 * ease_out_cubic(prog(t, t_open, t_open + 1.1)))
        U = v3(math.cos(a), 0, math.sin(a))
        T = PAL['theirs']

        def door(p, w, h):
            _planks(p, w, h, T, 15.0, 13, True, None, 0.8, 0.2, True, 0.2, T['wood'], T['wood_dk'], T['wood_lt'], T['seam'])
            p.line(rect(0, 0, w, h), 1.0, T['outline'])
            p.fill(oval(w - 8, h / 2 + 8, 2.4), T['metal'])
        # the light pouring in through the opening
        o = [cam.pt(v3(hx, 0, 0.0)), cam.pt(v3(hx + 0.9 * (1 - math.cos(a)) + 0.0, 0, 0.0))]
        if a > 0.05:
            q = [cam.pt(v3(hx + 0.02, 0.0, 0.0)), cam.pt(v3(hx + 0.88, 0.0, 0.0)), cam.pt(v3(hx + 1.1, 0.0, 1.6)), cam.pt(v3(hx - 0.1, 0.0, 1.8))]
            _L(pen, poly(q), q[0][0], q[0][1], q[3][0], q[3][1], [(0, '#fff2d0', 150 * min(1, a)), (1, '#fff2d0', 0)])
        draw_plane(pen, cam, ID, v3(hx, DOOR[2], 0.0), U, (0, -1, 0), 90, DOOR[2] * 100, door, True, 0.01)
    return _live(sdep(cam, ID, d0, v3(hx + 0.4, 1.0, 0.2), 0.003), draw, 'wash_door', blur=None)



# ====================================================================== the light arc
def red_leak_layer(k0=1.0):
    """dawn_break (534.7-609.9): red leaks in from the frame edges (8-15 % of the frame), stuttering with the gold."""
    def draw(pen, t):
        st_ = 0.75 + 0.25 * (1.0 if _h(int(t * 12), 17) > 0.2 else 0.3)
        k = k0 * st_ * (0.85 + 0.15 * math.sin(t * 5.3))
        for (x0, y0, x1, y1) in ((0, 0, 260, 0), (1920, 0, 1660, 0), (0, 0, 0, 200), (0, 1080, 0, 880)):
            if y0 == y1:
                _L(pen, rect(min(x0, x1) if x0 < x1 else x1, -100, abs(x1 - x0) + 1, 1300), x0, 0, x1, 0, [(0, '#ff2d55', 120 * k), (1, '#ff2d55', 0)])
            else:
                _L(pen, rect(-100, min(y0, y1), 2120, abs(y1 - y0) + 1), 0, y0, 0, y1, [(0, '#ff2d55', 90 * k), (1, '#ff2d55', 0)])
    return Layer(1.0, draw, 'red_leak', screen=True, blur=0)


# Per-tenth targets of DIRECTION_V2 2.1 (luma p50 range, red-pixel share max %) and what the sets do to meet them
ARC = [((0, 70), (95, 110), 0.5, 'night, warm memories'), ((70, 140), (95, 110), 1.0, 'night, sepia, the glass'),
       ((140, 210), (85, 100), 1.5, 'night, mirror, gold reflection'), ((210, 280), (90, 105), 1.5, 'night, gold doorway'),
       ((280, 350), (135, 150), 1.0, 'gold'), ((350, 420), (130, 145), 1.0, 'gold and sepia'), ((420, 490), (120, 135), 1.5, 'gold cooling near her'),
       ((490, 560), (95, 110), 8.0, 'gold breaking, red from 534.7'), ((560, 630), (60, 75), 18.0, 'red and plum'),
       ((630, 700), (90, 100), 2.0, 'blue with a warm pool')]


def arc_fx(t, world=None):
    """Per-frame post trims for the light arc (merged into every v2 SetPiece's fx): a slow climb of the red in the THEIRS
    break (534.7-560), the climax pulse (560-628, period 1.2 s), nothing elsewhere (the worlds carry the arc)."""
    d = {}
    if t < 140.0 and world == 'ours':
        d['exposure'] = 0.36                       # tenths 1-2: night is coloured and readable (luma 95-110)
    if 350.0 <= t < 420.0 and world in ('theirs', 'theirs_break'):
        d['exposure'] = -0.06
    if 420.0 <= t < 490.0 and world in ('theirs', 'theirs_break'):
        d['exposure'] = -0.3                       # tenth 7: the gold cools near her (120-135)
    if 534.7 <= t < 560.0 and world in ('theirs', 'theirs_break'):
        d['red'] = 0.08 + 0.12 * clamp((t - 534.7) / 25.0)
    if 560.0 <= t < 628.2 and world in ('climax', 'ours', 'stairs'):
        d['exposure'] = 0.06 * math.sin(t * 2 * math.pi / 1.2)
    return d
