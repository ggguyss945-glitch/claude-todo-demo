"""sets_walls.py: the sets of "If Your Little Brother Says Someone Lives In The Walls... DON'T LAUGH" (Night Policy).

Run inside sets.py's namespace at import, after sets_ice.py (it reuses the set engine: BView cameras on a plan in
metres, per-face light maps, Room / Piece / build_view, BuBox rooms, door_art / Door, bu_bed_parts, the Doctor film's
far ring, neighbours, streetlights and car, the bus film's room runs, patrol_car / lightbar for the police) and
everything here is part of `sets`:  import sets as ST;  sp = ST.wl_boys('wide').  Every new name starts with wl_ / WL_ /
_wl.  WL_API lists every builder's views; WL_INSERTS every insert.

ONE GEOGRAPHY: 14 Larkspur Lane, Maple Falls, an August heat wave. Plan in metres: x = east, y = north (from the front
wall y 0 toward the back yard), Y = up. Ground floor Y 0, upstairs WL_UP 2.9 (ceiling WL_UH 2.4 above it); the yards,
the driveway and the street WL_G -0.5 (the road 0.12 lower than the kerbs).
  GROUND FLOOR (x -6 .. 6, y 0 .. 10): the living room front-west (WL_LIV: Mr. Pell's green armchair facing south-east
  with the floor vent half under it, the couch along the back wall, moving boxes, a box fan in every window: the front
  window and two on the west wall); the entry hall and stairs in the middle (not built); the kitchen back-east (WL_KIT:
  the counter and sink along the back wall under the window, the note and the bread bag on it, the fridge, the table, the
  door from the garage on the east wall with its deadbolt and a plug-in nightlight beside it, the walk-in pantry in the
  back-east corner (WL_PAN) with shelves of cereal boxes and the plaster CRACK on its east wall).
  The kitchen's east wall (x 6.0) is the old outside wall: the garage was added later with its own wall at x 6.35, so
  a 0.35 m cavity runs the whole length between them (behind the pantry crack, "along the whole kitchen, up toward the
  ceiling"); the garage (WL_GAR, floor WL_GF) has the keypad beside its door.
  UPSTAIRS (Y WL_UP): the hall (WL_UHALL, 1.4 m wide, from the stair opening at its front end to the window at its back
  end; the dead switch on its west wall opposite the hall closet; a plug-in nightlight low on the west wall); the boys'
  room front-east (WL_BOYS: Theo's bed on the west wall, Sam's bed on the east wall (the wall by Sam's bed), the window
  between them, the door on the west wall with the pencil marks on its casing, a floor vent, TWO closets on the back
  wall: Theo's (west) and Sam's (east, its back wall SLIDES), and between them the DEAD SPACE (WL_DEAD, 0.45 m wide, 2.4 m
  deep: the sleeping bag, Dad's flashlight, the folded bread bags, the empty GONE FOREVER box)); the hall closet
  (WL_HCL, next to Theo's closet) with the sealed attic hatch in its ceiling; the parents' room back-west (WL_PAR: the
  bed with its headboard on the west wall, the nightstand with Mom's phone, the dresser on the back wall, the floor vent
  by the front wall, the door on the hall with a push-button privacy lock).
  OUTSIDE: our porch (the stone frog with the key under it beside the bottom step), the attached garage and its keypad,
  the driveway, the attic dormer on the front roof (its window shows the attic light), Larkspur Lane (kerbs y -8 and
  -16), Mrs. Dabrowski's house directly across (front y -24), the streetlight, three police cars at our kerb at the end.
Plan: _work/sets/floorplan.jpg (wl_plan_map).

STAGING DATA: identical to the Ice / Bus sets: sp.anchors[name] -> Spot (.x .y design px, .depth, .ppm, .height of a
1.85 m adult, .X .Yp .Y plan, .kind, .turn, .seat_y); ST.stage_figure(sp, who, spot, ...). Depth-to-scale rule: ppm =
S / depth. Every camera is in WL_CAMS (the plan map draws them), so cuts keep screen direction.
NIGHT RULE: the frame is dark but the SUBJECT is lit (moonlight through the windows, the hall nightlight, the phone, the
attic line, the kitchen nightlight by the garage door, an officer's flashlight, the police bars).
"""
import math
import numpy as np
import skia

# ====================================================================================================== plan
WL_G = D_GROUND                        # yards / driveway / sidewalks (-0.5); the road is 0.12 lower
WL_ROAD = WL_G - 0.12
WL_UP = 2.9                            # upstairs floor
WL_CEIL = 2.5                          # ground-floor ceiling height
WL_UH = 2.4                            # upstairs ceiling height (above WL_UP)
WL_EAVE, WL_RIDGE, WL_RIDGE_Y = WL_UP + WL_UH, 7.6, 5.0
WL_HOUSE = (-6.0, 6.0, 0.0, 10.0)
WL_LIV = (-6.0, -0.6, 0.0, 5.6)
WL_LOPEN = (1.0, 3.0, 2.2)             # the cased opening living room <-> entry on x -0.6 (y0, y1, h)
WL_LWIN_F = (-4.9, -3.3, 0.75, 2.05)   # the living room's front window on y 0 (x0, x1, sill, top) - a box fan in it
WL_LWIN_W = [(0.9, 2.0), (3.4, 4.5)]   # its two west windows on x -6.0 (y0, y1); sill / top as the front one
WL_ARM = Box(-3.6, 3.2, 0.95, 0.9, 0.0, 1.05, 45)          # Mr. Pell's green armchair, facing south-east (the room)
WL_VENT_L = (-3.32, 2.92)              # the floor vent, half under the chair's front edge (centre x, y; 0.30 x 0.12 m)
WL_COUCH = Box(-2.4, 5.13, 2.0, 0.9, 0.0, 0.84, 0)         # along the back wall, facing the front
WL_KIT = (1.4, 6.0, 3.6, 10.0)
WL_KOPEN = (4.4, 5.4, 2.1)             # the kitchen's doorway from the entry on x 1.4 (y0, y1, h)
WL_KWIN = (2.2, 3.2, 1.05, 2.0)        # the window over the sink on y 10
WL_GDOOR = (4.4, 5.25, 2.05)           # the door from the garage on x 6.0 (y0, y1 hinge, h); deadbolt on the kitchen side
WL_PAN = (4.8, 6.0, 8.6, 10.0)         # the walk-in pantry (back-east corner of the kitchen)
WL_PDOOR = (5.0, 5.75, 2.03)           # its door on y 8.6 (x0, x1 hinge, h)
WL_CRACK = (6.0, 9.42, 1.38)           # the plaster crack on the pantry's east wall (x, y, Y centre): behind the cereal
WL_COUNTER = Box(3.0, 9.69, 3.2, 0.62, 0.0, 0.92, 0)       # along the back wall, facing the room (-y)
WL_NOTE = (3.95, 9.62)                 # the note on the counter (x, y), WL_BREAD the bread bag
WL_BREAD = (4.3, 9.66)
WL_KNL = (6.0, 0.32, 5.62)             # the plug-in nightlight by the garage door (x, Y, y)
WL_GAR = (6.35, 12.0, 0.0, 8.0)        # the garage (its own wall at x 6.35; the cavity x 6.0 .. 6.35)
WL_GF = -0.4                           # garage floor
WL_GARDOOR = (6.9, 11.45, WL_GF + 2.15)  # the garage door on y 0 (x0, x1, top)
WL_KEYPAD = (11.75, WL_G + 1.42)       # the keypad on the garage front wall (x, Y centre)
# upstairs
WL_UHALL = (-0.6, 0.8, 1.6, 9.0)
WL_STAIR = (-0.6, 0.8, 2.1)            # the stair opening on the hall's front end (y 1.6): x0, x1, h
WL_SWITCH = (-0.6, 5.0, 1.2)           # the dead switch on the hall's west wall (x, y, height above the floor)
WL_HNL = (-0.6, 0.3, 3.1)              # the hall nightlight (x, height, y)
WL_BOYS = (0.8, 6.0, 0.0, 4.8)
WL_BDOOR = (3.6, 4.45, 2.03)           # the boys' door on x 0.8 (y0 latch, y1 hinge, h); swings into the room
WL_BWIN = (2.8, 4.0, 0.85, 2.0)        # their window on y 0 (x0, x1, sill, top)
WL_TBED = Box(1.33, 1.08, 0.95, 1.95, WL_UP, WL_UP + 0.5, 180)   # Theo's bed on the west wall, head at the front
WL_SBED = Box(5.47, 1.08, 0.95, 1.95, WL_UP, WL_UP + 0.5, 180)   # Sam's bed on the east wall (the wall by Sam's bed)
WL_TCL = (2.2, 3.2, 4.8, 5.55)         # Theo's closet (x0, x1, y0, y1), door 2.3 .. 3.1
WL_SCL = (3.65, 4.65, 4.8, 5.55)       # Sam's closet, door 3.75 .. 4.55; its back wall (y 5.55) slides west
WL_DEAD = (3.2, 3.65, 4.8, 7.2)        # the dead space between them: a foot and a half wide
WL_HCL = (0.8, 2.2, 4.8, 6.2)          # the hall closet; its door on the hall (x 0.8, y 5.1 .. 5.85)
WL_HCDOOR = (5.1, 5.85, 2.0)
WL_HATCH = (1.1, 1.8, 5.15, 5.85)      # the attic hatch in the hall closet's ceiling
WL_VENT_B = (1.75, 3.95)               # the boys' floor vent
WL_MARKS = (0.8, 3.53)                 # the doorframe pencil marks: on the boys' door casing, room side (x, y)
WL_PAR = (-6.0, -0.6, 4.6, 9.0)
WL_PARDOOR = (6.8, 7.65, 2.03)         # the parents' door on x -0.6 (y0 latch, y1 hinge, h); swings into their room
WL_PWIN = (-5.2, -4.0, 0.85, 2.0)      # their window on y 9.0
WL_PBED = Box(-4.95, 6.8, 1.6, 2.05, WL_UP, WL_UP + 0.5, 90)    # head (the headboard) against the west wall
WL_DRESSER = Box(-2.4, 8.72, 1.3, 0.52, WL_UP, WL_UP + 0.92, 0)
WL_NSTAND = Box(-5.75, 8.12, 0.45, 0.4, WL_UP, WL_UP + 0.58, 90)
WL_VENT_P = (-3.4, 4.76)               # the parents' floor vent, by the front wall
# outside
WL_FDOOR = (0.0, 0.9, 2.05)            # the front door on y 0 (x0, x1, h)
WL_PORCH = (-1.0, 1.9, -1.7, 0.0)      # the porch deck at floor level
WL_STEPS = (0.0, 0.9, -2.5, -1.7)      # three steps down to the walk
WL_FROG = (1.22, -2.22)                # the stone frog beside the bottom step (the key under it)
WL_PLIGHT = (1.3, 1.95, -0.06)
WL_DRIVE = (6.6, 11.8, -8.0, 0.0)
WL_KN, WL_KS = -8.0, -16.0             # our kerb / Mrs. Dabrowski's kerb
WL_LAMP = (-7.2, -8.4)
WL_LAMPS = [(-30.0, -8.4), (22.0, -15.6)]
WL_DAB = (-3.0, 7.0, -33.0, -24.0)     # Mrs. Dabrowski's house (front y -24, facing north)
WL_DABDOOR = (1.8, 2.7, 2.05)
WL_POLICE_CARS = [(-5.8, -9.35, 1), (0.4, -9.35, -1), (6.6, -9.35, -1)]    # (x, y, facing) at our kerb
WL_DORMER = (0.85, 2.15, 1.6)          # the attic dormer on the front roof (x0, x1, front y)

WL_MOON = '#9ab4ff'
WL_NIGHTL = '#ffcf8a'                  # the plug-in nightlights (warm)
WL_ATTIC = '#ffd060'                   # the attic's thin yellow line
WL_WARM = '#ffc98a'
WL_RED, WL_BLUE = '#ff2a3a', '#3a6aff'
WL_PAL = dict(siding='#a9b3a8', trim='#f0ede4', door='#2e4a3a', shutter='#2a2e34', roof='#3a3c42', gar_door='#e8e6de',
              dab_siding='#d8c890', dab_door='#7a2a2a', liv_paper='#c8c0a4', liv_ink='#a89a74', kit_paper='#e8e0c4',
              hall_paper='#bfc4b0', hall_ink='#a0a890', boys_paper='#b8c8d8', boys_ink='#90a8c0', par_paper='#d8c8c0', par_ink='#b8a098',
              floor='#9a6a40', armchair='#4a6a3a', armchair_d='#2e4a26', couch='#7a5a4a', couch_d='#5a3e32', box='#c8a070')

# ====================================================================================================== grades
_GR.setdefault('wl_night', dict(exposure=0.12, contrast=1.08, pivot=0.24, gamma=1.06, sat=1.04, wb=(0.94, 1.0, 1.1), floor='#070a16',
                                bloom=0.9, bloom_thr=224, vignette=0.42, grain=0.6, shoulder=0.45))
_GR.setdefault('wl_ext', dict(contrast=1.08, pivot=0.24, gamma=1.04, sat=1.06, wb=(0.95, 1.0, 1.08), floor='#060a16',
                              bloom=1.0, bloom_thr=222, vignette=0.36, grain=0.6, shoulder=0.45))
_GR.setdefault('wl_warm', dict(exposure=0.04, contrast=1.04, pivot=0.25, gamma=1.04, sat=1.08, wb=(1.06, 1.0, 0.92), floor='#0e0a08',
                               bloom=0.85, bloom_thr=226, vignette=0.42, grain=0.45, shoulder=0.5))
_GR.setdefault('wl_day', dict(exposure=0.04, contrast=1.04, pivot=0.26, gamma=1.02, sat=1.08, wb=(1.05, 1.0, 0.93), floor='#14100c',
                              bloom=0.8, bloom_thr=230, vignette=0.38, grain=0.35, shoulder=0.55))
_GR.setdefault('wl_police', dict(exposure=-0.02, contrast=1.1, pivot=0.24, gamma=1.02, sat=1.1, wb=(0.98, 1.0, 1.04), floor='#06080e',
                                 bloom=1.0, bloom_thr=220, vignette=0.4, grain=0.6, shoulder=0.45))
_GR.setdefault('wl_dead', dict(contrast=1.12, pivot=0.22, gamma=1.06, sat=0.96, wb=(1.0, 1.0, 1.02), floor='#060504',
                               bloom=0.9, bloom_thr=226, vignette=0.55, grain=0.8, shoulder=0.45))
_GR.setdefault('wl_ins', dict(contrast=1.04, pivot=0.25, gamma=1.04, sat=1.04, wb=(1.0, 1.0, 1.0), floor='#0a0a0c',
                              bloom=0.5, bloom_thr=236, vignette=0.5, grain=0.45, shoulder=0.5))
_GR.setdefault('wl_ins_night', dict(contrast=1.06, pivot=0.25, gamma=1.04, sat=1.0, wb=(0.95, 1.0, 1.08), floor='#060a14',
                                    bloom=0.7, bloom_thr=230, vignette=0.5, grain=0.6, shoulder=0.5))

WL_CAMS = []


def _wcam(name, S, h, eye, x, y, yaw, env=None, note='', room='', pitch=0.0):
    _cam(name, S, h, eye, x, y, yaw, env or _env(), note, room, pitch)
    if name not in WL_CAMS: WL_CAMS.append(name)


def wl_police(t0=0.0, mode='sweep', k=1.0, ramp=1.5):
    """Level specs for the police light bars (red, blue) from t0 (fading up over `ramp` s): pass police=ST.wl_police(t0)."""
    def r(t): return 0.0 if t < t0 else k * min(1.0, (t - t0) / ramp) * lightbar(t, mode)[0]
    def b(t): return 0.0 if t < t0 else k * min(1.0, (t - t0) / ramp) * lightbar(t, mode)[1]
    return (r, b)


def _pol(o):
    """(red spec, blue spec) from o['police']: None | True (on from 0) | (r, b) level specs."""
    p = o.get('police')
    if not p: return (0.0, 0.0)
    if p is True: return wl_police(-10.0)
    return p


def _wl_var_common(o, seed, phone_at=None, flash_at=None, police_panes=None, police_d=(0.0, 0.55, 1.0)):
    """Variable lights every room shares: Mom's phone, an officer's flashlight, the police bars through the windows."""
    P = o.get('phone_at', phone_at or (0.0, 1.1, 0.0)); F_ = o.get('flash_at', flash_at or (0.0, 1.4, 0.0))
    var = [('phone', [Lamp(P[0], P[1], P[2], 2.6, '#e8f0ff', 1.3, (1.0, 1.0, 0.8), fall=1.6)], _kfn(o.get('phone', 0.0), seed)),
           ('flash', [Lamp(F_[0], F_[1], F_[2], 5.0, '#fff4dc', 1.8, (1.0, 1.0, 0.6), fall=1.4)], _kfn(o.get('flash', 0.0), seed + 1))]
    if police_panes:
        pr, pb = _pol(o)
        var.append(('police_r', [Lamp(kind='win', c=WL_RED, k=1.6, soft=10.0, panes=police_panes, d=_norm3(police_d))], _kfn(pr, seed + 2)))
        var.append(('police_b', [Lamp(kind='win', c=WL_BLUE, k=1.9, soft=10.0, panes=police_panes, d=_norm3((-police_d[0], police_d[1], police_d[2])))], _kfn(pb, seed + 3)))
    return var


def _wl_amb(o, night='#20263c'):
    if o.get('tod') in ('day', 'morning'): return '#8a8478'
    return mix(night, '#6a7aa8', 0.3)                  # night: dark, but the room still reads


def _wl_grade(o, warm=('lamp', 'ceil', 'kitchen_light', 'hall_light')):
    if o.get('tod') in ('day', 'morning'): return 'wl_day'
    if o.get('police'): return 'wl_police'
    if any(_static(o.get(k_, 0.0)) > 0.3 for k_ in warm): return 'wl_warm'
    return 'wl_night'


# ====================================================================================================== outside: sky, trees, ground
def wl_sky(pen, v, tod='night', box=(-900, -700, 2820, 1780)):
    """August: a clear summer night (stars, the moon) or a hazy hot blue day."""
    if tod == 'night':
        ic_sky(pen, v, 'night', box)
        return
    x0, y0, x1, y1 = box
    H = v.h
    pen.linear(rect(x0, y0, x1 - x0, y1 - y0), 0, H - 1.0 * v.S, 0, H + 20, [(0, '#3a7ad0'), (0.55, '#78a8e0'), (0.9, '#cfe0ea'), (1, '#e8eee8')])
    rng = np.random.default_rng(8)
    for i in range(7):
        q = sky_dir(v, rng.uniform(-180, 180), rng.uniform(8, 30))
        if q: _cloud(pen, q[0], q[1], rng.uniform(0.5, 0.9) * v.S, 0.06 * v.S, int(rng.integers(0, 999)), '#f4f6f8', '#ffffff', 170)


def _wl_tree(pen, v, x, y, h, tod='night', seed=0):
    """A full August maple: a dark trunk and a crown of leafy masses (no bare winter branches)."""
    if v.d(x, y) < 1.0: return
    bx, by = v.p(x, WL_G, y); s = v.s(x, y)
    night = tod == 'night'
    tr = poly([(bx - 0.16 * s, by), (bx + 0.16 * s, by), (bx + 0.1 * s, by - 0.55 * h * s), (bx - 0.1 * s, by - 0.55 * h * s)])
    pen.fill(tr, '#14100e' if night else '#4a3a2e'); pen.line(tr, 1.0)
    rng = np.random.default_rng(300 + seed)
    c0, c1 = ('#0c1610', '#16241a') if night else ('#2e5226', '#4a7a36')
    for i in range(7):
        cx = bx + rng.uniform(-0.32, 0.32) * h * s; cy = by - (0.55 + rng.uniform(0.05, 0.38)) * h * s
        _bush(pen, cx, cy + 0.2 * h * s, rng.uniform(0.45, 0.7) * h * s, rng.uniform(0.35, 0.5) * h * s, seed * 10 + i, c0, c1)


def _wl_strip(pen, v, x0, x1, y0, y1, Y, c, kind='asphalt', ink=None):
    F = floor_face(x0, x1, y0, y1, Y)
    def art(p_, W, H):
        p_.texture(rect(0, 0, W, H), kind, 0.6, 'overlay', 1.6 if kind == 'asphalt' else 0.8)
        if ink: ink(p_, W, H)
    draw_face(pen, v, F, art, c, ao=False, line=False)


def wl_ground(pen, v, tod='night'):
    """Lawns (dry August grass), Larkspur Lane, the kerbs (with their faces), sidewalks, our walk, the driveways."""
    night = tod == 'night'
    grass = '#18241c' if night else '#6a7e44'
    F = floor_face(-130.0, 130.0, -130.0, 40.0, WL_G)
    def lawn(p_, W, H):
        p_.linear(rect(0, 0, W, H), 0, 0, 0, H, [(0, grass, 255), (1, _darken(grass, 0.2), 255)])
        p_.texture(rect(0, 0, W, H), 'grunge', 0.6, 'overlay', 5.0); p_.texture(rect(0, 0, W, H), 'fabric', 0.4, 'overlay', 0.8)
    draw_face(pen, v, F, lawn, grass, ao=False, line=False)
    road = '#23252b' if night else '#55575c'
    walk = '#55575c' if night else '#b0aea6'
    def street_ink(p_, W, H):
        for k in range(40): p_.fill(rect(k * 500, (WL_KN - WL_KS) * 50 - 5, 300, 10), '#c8a83a', 110)
    _wl_strip(pen, v, -120.0, 120.0, WL_KS, WL_KN, WL_ROAD, road, 'asphalt', street_ink)
    lines = lambda p_, W, H: [p_.fill(rect(k * 150, 0, 1.2, H), '#000000', 90) for k in range(int(W / 150))]
    _wl_strip(pen, v, -120.0, 120.0, -7.6, -6.4, WL_G + 0.003, walk, 'asphalt', lines)
    _wl_strip(pen, v, -120.0, 120.0, -17.6, -16.4, WL_G + 0.003, walk, 'asphalt', lines)
    for (yk, sgn) in ((WL_KN, 1), (WL_KS, -1)):                                 # the kerb faces (the curb Pell sits on)
        a, b = ((-120.0, yk), (120.0, yk)) if sgn == 1 else ((120.0, yk), (-120.0, yk))
        Fk = wall_face(a, b, WL_ROAD, WL_G)
        draw_face(pen, v, Fk, lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'grunge', 0.5, 'overlay', 1.0), '#8a8a86' if not night else '#4a4c52', ao=False, line=False)
        _wl_strip(pen, v, -120.0, 120.0, yk - 0.15 if sgn == 1 else yk, yk if sgn == 1 else yk + 0.15, WL_G + 0.002, '#9a9a94' if not night else '#5e6066', 'asphalt')
    dx0, dx1, dy0, dy1 = WL_DRIVE
    _wl_strip(pen, v, dx0, dx1, dy0, dy1, WL_G + 0.006, '#4e5054' if night else '#a8a49a', 'asphalt',
              lambda p_, W, H: [p_.fill(rect(0, k * 300, W, 1.2), '#000000', 90) for k in range(int(H / 300))])
    _wl_strip(pen, v, WL_STEPS[0] + 0.05, WL_STEPS[1] - 0.05, -6.4, WL_STEPS[2], WL_G + 0.006, walk, 'asphalt',
              lambda p_, W, H: [p_.fill(rect(0, k * 90, W, 1.0), '#000000', 90) for k in range(int(H / 90))])
    _wl_strip(pen, v, 1.85, 2.65, -22.4, -17.6, WL_G + 0.006, walk, 'asphalt')                   # Mrs. Dabrowski's walk
    _wl_strip(pen, v, 8.0, 11.0, -27.0, -16.0, WL_G + 0.006, '#4e5054' if night else '#a8a49a', 'asphalt')
    bed = floor_face(-6.0, -1.0, -0.7, 0.0, WL_G + 0.01)                        # the flower bed along our front
    draw_face(pen, v, bed, lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'grunge', 0.8, 'overlay', 2.0), '#2a2018', ao=False, line=False)


def _wl_ext_light(tod):
    if tod in ('day', 'morning'):
        return '#9a948a', [Lamp(kind='dir', c='#fff0d0', k=1.0, d=_norm3((-0.5, -0.7, 0.5)))]
    return '#3a4672', [Lamp(kind='dir', c='#9aaee8', k=0.55, d=_norm3((0.3, -0.8, 0.6)))]


# ====================================================================================================== houses
WL_WINS_EXT = {   # name: (wall, c0, c1, sill, top)  absolute Y; the glow names for o['win']
    'liv': ('front', WL_LWIN_F[0], WL_LWIN_F[1], WL_LWIN_F[2], WL_LWIN_F[3]),
    'liv_w1': ('west', WL_LWIN_W[0][0], WL_LWIN_W[0][1], WL_LWIN_F[2], WL_LWIN_F[3]),
    'liv_w2': ('west', WL_LWIN_W[1][0], WL_LWIN_W[1][1], WL_LWIN_F[2], WL_LWIN_F[3]),
    'dining': ('front', 2.6, 4.4, 0.85, 2.05),
    'bath': ('front', -4.5, -3.6, WL_UP + 1.15, WL_UP + 1.9),
    'stair': ('front', -0.15, 0.45, WL_UP + 1.0, WL_UP + 1.8),
    'boys': ('front', WL_BWIN[0], WL_BWIN[1], WL_UP + WL_BWIN[2], WL_UP + WL_BWIN[3]),
    'par': ('back', WL_PWIN[0], WL_PWIN[1], WL_UP + WL_PWIN[2], WL_UP + WL_PWIN[3]),
    'kitchen': ('back', WL_KWIN[0], WL_KWIN[1], WL_KWIN[2], WL_KWIN[3]),
}
_WL_WALLS = {'front': ((-6.0, 0.0), (6.0, 0.0)), 'west': ((-6.0, 10.0), (-6.0, 0.0)), 'east': ((6.0, 0.0), (6.0, 10.0)), 'back': ((6.0, 10.0), (-6.0, 10.0))}


def _wl_wquad(wall_, c0, c1, Y0, Y1, off=0.012, walls=None):
    a, b = (walls or _WL_WALLS)[wall_]
    def P(c, Y):
        if wall_ in ('front', 'back'): return (c, Y, a[1] - off if wall_ == 'front' else a[1] + off)
        return (a[0] - off if wall_ == 'west' else a[0] + off, Y, c)
    return [P(c0, Y1), P(c1, Y1), P(c1, Y0), P(c0, Y0)]


def _wl_window_art(p_, ua, ub, yt, yb, night, fan=False, shutters=True, lites=2):
    if shutters:
        for sx in (ua - 32, ub + 6):
            p_.fill(rect(sx, yt, 26, yb - yt), WL_PAL['shutter']); p_.line(rect(sx, yt, 26, yb - yt), 0.8)
            for k in range(int((yb - yt) / 9)): p_.fill(rect(sx + 3, yt + 4 + k * 9, 20, 2), '#000000', 70)
    p_.fill(rect(ua - 6, yt - 8, ub - ua + 12, yb - yt + 16), WL_PAL['trim'])
    p_.fill(rect(ua, yt, ub - ua, yb - yt), '#10141c' if night else '#4a5a6a')
    p_.linear(rect(ua, yt, ub - ua, yb - yt), ua, yt, ub, yb, [(0, '#ffffff', 0), (0.5, '#a8b8d8', 40 if night else 100), (1, '#ffffff', 0)])
    if fan:                                                                    # a box fan sitting in the lower sash
        fw = min(ub - ua - 10, 52); fx = (ua + ub) / 2 - fw / 2; fy = yb - fw - 4
        p_.fill(rect(fx, fy, fw, fw), '#1c1e22' if night else '#6a6c70'); p_.line(rect(fx, fy, fw, fw), 0.8)
        p_.line(oval(fx + fw / 2, fy + fw / 2, fw * 0.4), 0.7, '#8a8c90', 150)
    for k in range(1, lites): p_.fill(rect(ua + (ub - ua) * k / lites - 2, yt, 4, yb - yt), WL_PAL['trim'])
    p_.fill(rect(ua, (yt + yb) / 2 - 2, ub - ua, 4), WL_PAL['trim'])
    p_.fill(rect(ua - 10, yb, ub - ua + 20, 6), '#e2ddd0')


def _wl_gable_roof(pen, v, x0, x1, y0, y1, Ye, Yr, col, gables=(True, True), side_col=None, oh=0.35):
    """A gable roof with its ridge along x at the middle of y0..y1 (eave Ye, ridge Yr), shingle courses, gable ends."""
    ym = (y0 + y1) / 2
    X0, X1 = x0 - oh, x1 + oh
    for (q, n) in (([(X0, Ye, y0 - oh), (X1, Ye, y0 - oh), (X1, Yr, ym), (X0, Yr, ym)], (0, 0.8, -0.6)),
                   ([(X1, Ye, y1 + oh), (X0, Ye, y1 + oh), (X0, Yr, ym), (X1, Yr, ym)], (0, 0.8, 0.6))):
        cen = (sum(p_[0] for p_ in q) / 4, sum(p_[1] for p_ in q) / 4, sum(p_[2] for p_ in q) / 4)
        if not v.visible(cen, _norm3(n)): continue
        path = v.poly3(q)
        if path.isEmpty(): continue
        pen.fill(path, lit(col, cen, _norm3(n)))
        for k in range(12):
            f = (k + 0.5) / 12
            A = (q[0][0], q[0][1] + (q[3][1] - q[0][1]) * f, q[0][2] + (q[3][2] - q[0][2]) * f)
            B_ = (q[1][0], A[1], A[2])
            if v.d(A[0], A[2]) > 0.3 and v.d(B_[0], B_[2]) > 0.3: pen.seg(v.p(*A), v.p(*B_), 1.0, '#000000', 80)
        pen.line(path, 1.2)
    for (xx, n, on) in ((x0, (-1, 0, 0), gables[0]), (x1, (1, 0, 0), gables[1])):
        if not on: continue
        tri = [(xx, Ye, y0), (xx, Ye, y1), (xx, Yr - 0.12, ym)]
        if not v.visible(tri[2], n): continue
        path = v.poly3(tri)
        if not path.isEmpty():
            pen.fill(path, lit(_darken(side_col or col, 0.05), tri[2], n)); pen.line(path, 1.0)


def _wl_walls(pen, v, walls, Y0, Y1, sid, art_fn, skip=()):
    for wall_, (a, b) in walls.items():
        if wall_ in skip: continue
        F = wall_face(a, b, Y0, Y1)
        if not v.visible(F.O, F.n): continue
        draw_face(pen, v, F, (lambda wall_, a, b: lambda p_, W, H: art_fn(p_, W, H, wall_, a, b))(wall_, a, b), sid, ao=False, lw=1.2)


def wl_house_ext(pen, v, o):
    """14 Larkspur Lane from outside: two storeys of grey-sage clapboard, white trim, black shutters, the dark green front
    door, the attic dormer on the front roof slope (its little window: the attic light), the attached garage east."""
    tod = o.get('tod', 'night'); night = tod == 'night'
    G = WL_G
    def art(p_, W, H, wall_, a, b):
        pat(p_, W, H, 'clapboard', '#000000', 120)
        p_.texture(rect(0, 0, W, H), 'grunge', 0.3, 'overlay', 1.2)
        p_.fill(rect(0, H - (0.0 - G) * 100 - 2, W, (0.0 - G) * 100 + 2), '#6e6a64')
        p_.fill(rect(0, H - (WL_UP - G) * 100 - 6, W, 8), WL_PAL['trim'])
        u_of, L = _u_of(a, b)
        for nm, (w_, c0, c1, sl, tp) in WL_WINS_EXT.items():
            if w_ != wall_: continue
            ua, ub = sorted((u_of(c0, a[1]) if wall_ in ('front', 'back') else u_of(a[0], c0), u_of(c1, a[1]) if wall_ in ('front', 'back') else u_of(a[0], c1)))
            _wl_window_art(p_, ua * 100, ub * 100, H - (tp - G) * 100, H - (sl - G) * 100, night, fan=nm.startswith('liv') or nm in ('boys', 'dining'),
                           shutters=nm not in ('stair', 'bath'))
        if wall_ == 'front':
            ua, ub = u_of(WL_FDOOR[0], 0) * 100, u_of(WL_FDOOR[1], 0) * 100
            yt = H - (WL_FDOOR[2] - G) * 100; yb = H - (0.0 - G) * 100
            p_.fill(rect(ua - 12, yt - 14, ub - ua + 24, yb - yt + 14), WL_PAL['trim']); p_.line(rect(ua - 12, yt - 14, ub - ua + 24, yb - yt + 14), 0.8)
            p_.cv.save(); p_.cv.translate(ua, yt)
            door_art('four', 'right', bolt=False, col=WL_PAL['door'])(p_, ub - ua, yb - yt)
            p_.cv.restore()
            for k in range(3): p_.fill(rect(ua + 10 + k * (ub - ua - 20) / 3 + 2, yt + 10, (ub - ua - 20) / 3 - 4, 18), '#121620' if night else '#5a6a7a')
            btext(p_, '14', u_of(-0.45, 0) * 100, H - (1.75 - G) * 100, 'serif_b', 15, '#1a1a1a', 230, 'center')
    _wl_walls(pen, v, _WL_WALLS, G, WL_EAVE, WL_PAL['siding'], art)
    _wl_gable_roof(pen, v, -6.0, 6.0, 0.0, 10.0, WL_EAVE, WL_RIDGE, WL_PAL['roof'], side_col=WL_PAL['siding'])
    wl_dormer(pen, v, o)


def _wl_roof_Y(y):
    """Height of the main roof's front slope above plan y (for the dormer)."""
    return WL_EAVE + (WL_RIDGE - WL_EAVE) * (y + 0.35) / (WL_RIDGE_Y + 0.35)


def wl_dormer(pen, v, o):
    """The little gabled dormer on the front slope over the hall closet: the attic window (dark; lit = the attic light)."""
    x0, x1, yf = WL_DORMER
    yb = yf + 1.3
    Yb, Yt = _wl_roof_Y(yf), _wl_roof_Y(yf) + 0.95
    night = o.get('tod', 'night') == 'night'
    F = wall_face((x0, yf), (x1, yf), Yb, Yt)
    if v.visible(F.O, F.n):
        def art(p_, W, H):
            pat(p_, W, H, 'clapboard', '#000000', 110)
            wx0, wx1 = W * 0.28, W * 0.72; wy0, wy1 = H * 0.18, H * 0.78
            p_.fill(rect(wx0 - 5, wy0 - 5, wx1 - wx0 + 10, wy1 - wy0 + 10), WL_PAL['trim'])
            p_.fill(rect(wx0, wy0, wx1 - wx0, wy1 - wy0), '#0c1018' if night else '#4a5a6a')
            p_.fill(rect((wx0 + wx1) / 2 - 2, wy0, 4, wy1 - wy0), WL_PAL['trim'])
        draw_face(pen, v, F, art, WL_PAL['siding'], ao=False, lw=1.0)
    for (xx, n) in ((x0, (-1, 0, 0)), (x1, (1, 0, 0))):                        # side cheeks: bottom edge follows the slope
        q = [(xx, Yt, yf), (xx, Yt, yb), (xx, _wl_roof_Y(yb), yb), (xx, Yb, yf)]
        if v.visible(q[0], n):
            path = v.poly3(q)
            if not path.isEmpty(): pen.fill(path, lit(_darken(WL_PAL['siding'], 0.08), q[0], n)); pen.line(path, 0.8)
    xm = (x0 + x1) / 2
    for (q, n) in (([(x0 - 0.08, Yt, yf - 0.1), (xm, Yt + 0.45, yf - 0.1), (xm, Yt + 0.45, yb), (x0 - 0.08, Yt, yb)], (-0.7, 0.7, 0)),
                   ([(xm, Yt + 0.45, yf - 0.1), (x1 + 0.08, Yt, yf - 0.1), (x1 + 0.08, Yt, yb), (xm, Yt + 0.45, yb)], (0.7, 0.7, 0))):
        if v.visible(q[0], _norm3(n)):
            path = v.poly3(q)
            if not path.isEmpty(): pen.fill(path, lit(WL_PAL['roof'], q[0], _norm3(n))); pen.line(path, 1.0)
    tri = [(x0, Yt, yf - 0.01), (x1, Yt, yf - 0.01), (xm, Yt + 0.42, yf - 0.01)]
    if v.visible(tri[0], (0, 0, -1)):
        path = v.poly3(tri)
        if not path.isEmpty(): pen.fill(path, lit(WL_PAL['trim'], tri[0], (0, 0, -1))); pen.line(path, 0.8)


def _wl_dormer_quad():
    x0, x1, yf = WL_DORMER
    Yb = _wl_roof_Y(yf); H = 0.95; W = x1 - x0
    return [(x0 + W * 0.28, Yb + H * 0.82, yf - 0.01), (x0 + W * 0.72, Yb + H * 0.82, yf - 0.01), (x0 + W * 0.72, Yb + H * 0.22, yf - 0.01),
            (x0 + W * 0.28, Yb + H * 0.22, yf - 0.01)]


_WL_GWALLS = {'front': ((6.0, 0.0), (12.0, 0.0)), 'east': ((12.0, 0.0), (12.0, 8.0)), 'back': ((12.0, 8.0), (6.0, 8.0))}


def wl_garage_ext(pen, v, o):
    """The attached garage: white panel door (four rows), the keypad on the wall right of it (Mr. Pell's old code)."""
    night = o.get('tod', 'night') == 'night'
    Ye = 2.65
    def art(p_, W, H, wall_, a, b):
        pat(p_, W, H, 'clapboard', '#000000', 120)
        p_.texture(rect(0, 0, W, H), 'grunge', 0.3, 'overlay', 1.2)
        p_.fill(rect(0, H - 12, W, 12), '#6e6a64')
        if wall_ != 'front': return
        ua, ub = (WL_GARDOOR[0] - 6.0) * 100, (WL_GARDOOR[1] - 6.0) * 100
        yt = H - (WL_GARDOOR[2] - WL_G) * 100; yb = H
        p_.fill(rect(ua - 10, yt - 10, ub - ua + 20, yb - yt + 10), WL_PAL['trim'])
        p_.fill(rect(ua, yt, ub - ua, yb - yt), WL_PAL['gar_door'] if not night else '#9a9c9e')
        rh = (yb - yt) / 4
        for r_ in range(4):
            p_.line(rect(ua, yt + r_ * rh, ub - ua, rh), 1.0, '#000000', 120)
            for c_ in range(8):
                cw = (ub - ua) / 8
                if r_ == 0: p_.fill(rect(ua + c_ * cw + 6, yt + 8, cw - 12, rh - 16), '#101418' if night else '#4a5a6a')
                else: p_.line(rect(ua + c_ * cw + 6, yt + r_ * rh + 6, cw - 12, rh - 12), 0.7, '#000000', 80)
        kx = (WL_KEYPAD[0] - 6.0) * 100; ky = H - (WL_KEYPAD[1] - WL_G) * 100
        p_.fill(rrect(kx - 6, ky - 8, 12, 16, 1.5), '#8a8c90'); p_.line(rrect(kx - 6, ky - 8, 12, 16, 1.5), 0.6)
        p_.fill(rrect(kx - 4.5, ky - 4.5, 9, 3, 0.8), '#8a8c90')
        for i in range(3):
            for j in range(4): p_.fill(rect(kx - 4.2 + i * 3, ky - 1 + j * 2.2, 2.2, 1.6), '#c8f0c0' if night else '#d8d8d0', 220)
    _wl_walls(pen, v, _WL_GWALLS, WL_G, Ye, WL_PAL['siding'], art)
    _wl_gable_roof(pen, v, 6.0, 12.0, 0.0, 8.0, Ye, 4.1, WL_PAL['roof'], gables=(False, True), side_col=WL_PAL['siding'], oh=0.3)


def wl_porch(pen, v, o):
    """The porch deck, the steps, two posts and the little shed roof over the door, the porch light, the stone frog."""
    G = WL_G
    x0, x1, y0, y1 = WL_PORCH
    draw_box(pen, v, Box((x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0, G, 0.0, 0), {'top': dict(fill='#8a8a84', art=lambda p_, W, H: [
        p_.fill(rect(0, k * 14, W, 1.0), '#000000', 90) for k in range(int(H / 14))]), 'all': '#d8d4c8'}, lw=1.0)
    sx0, sx1, sy0, sy1 = WL_STEPS
    for k in range(3):
        yy0 = sy0 + k * (sy1 - sy0) / 3
        draw_box(pen, v, Box((sx0 + sx1) / 2, (yy0 + sy1) / 2, sx1 - sx0, sy1 - yy0, G, G + (k + 1) * (0.0 - G) / 3, 0),
                 {'top': '#9a9a94', 'all': '#c8c4b8'}, lw=0.8)
    for px in (x0 + 0.1, x1 - 0.1):
        draw_box(pen, v, Box(px, y0 + 0.1, 0.12, 0.12, 0.0, 2.6, 0), {'all': WL_PAL['trim']}, lw=0.8)
    q = [(x0 - 0.15, 2.95, 0.0), (x1 + 0.15, 2.95, 0.0), (x1 + 0.15, 2.6, y0 - 0.2), (x0 - 0.15, 2.6, y0 - 0.2)]
    if v.d(q[2][0], q[2][2]) > 0.3:
        path = v.poly3(q)
        if not path.isEmpty():
            pen.fill(path, lit(WL_PAL['roof'], q[0], _norm3((0, 0.9, -0.3)))); pen.line(path, 1.0)
        draw_box(pen, v, Box((x0 + x1) / 2, y0 - 0.2, x1 - x0 + 0.3, 0.05, 2.45, 2.62, 0), {'all': WL_PAL['trim']}, lw=0.8)
    lx, lY, ly = WL_PLIGHT
    if v.d(lx, ly) > 0.4:
        draw_box(pen, v, Box(lx, ly - 0.04, 0.14, 0.1, lY - 0.13, lY + 0.13, 0), {'all': '#1a1a1a', 'front': '#f4e0b0' if o.get('porch') else '#3a3a38'}, lw=0.6)
    wl_frog(pen, v, WL_FROG[0], WL_G, WL_FROG[1], lift=o.get('frog_lift', 0.0), key=o.get('key', True))


def wl_frog(pen, v, x, Y, y, s=1.0, lift=0.0, key=True):
    """The stone frog by the front step: squat, mossy grey, big lidded eyes; the brass key under it (lift 0..1 tips it)."""
    if v.d(x, y) < 0.15: return
    k = v.s(x, y) * s
    bx, by = v.p(x, Y, y)
    if key:
        kx, ky = bx + 0.03 * k, by - 0.004 * k
        pen.fill(oval(kx - 0.045 * k, ky, 0.022 * k, 0.012 * k), '#c8a048'); pen.line(oval(kx - 0.045 * k, ky, 0.022 * k, 0.012 * k), 0.8)
        pen.fill(rect(kx - 0.025 * k, ky - 0.004 * k, 0.07 * k, 0.008 * k), '#c8a048')
        pen.fill(rect(kx + 0.03 * k, ky, 0.012 * k, 0.008 * k), '#c8a048')
    cv = pen.cv; cv.save(); cv.translate(bx + 0.09 * k, by); cv.rotate(-28.0 * lift); cv.translate(-(bx + 0.09 * k), -by)
    pen.fill(oval(bx, by, 0.13 * k, 0.025 * k), '#000000', 110, blur=0.02 * k)
    body = union(oval(bx, by - 0.06 * k, 0.12 * k, 0.07 * k), oval(bx - 0.03 * k, by - 0.12 * k, 0.075 * k, 0.06 * k))
    c = lit('#646a60', (x, Y + 0.1, y), None)
    pen.fill(body, c); pen.texture(body, 'grunge', 0.7, 'overlay', 0.5)
    pen.fill(oval(bx + 0.02 * k, by - 0.03 * k, 0.09 * k, 0.03 * k), '#5a6a4a', 110)
    for ex in (-0.075, 0.015):
        e = oval(bx + ex * k, by - 0.165 * k, 0.03 * k, 0.026 * k)
        pen.fill(e, c); pen.line(e, 0.8)
        pen.fill(oval(bx + ex * k, by - 0.162 * k, 0.014 * k, 0.008 * k), '#2a2c28')
    pen.line(smooth([(bx - 0.1 * k, by - 0.11 * k), (bx - 0.03 * k, by - 0.095 * k), (bx + 0.03 * k, by - 0.11 * k)], False), 0.9, '#2a2c28', 200)
    pen.line(body, 1.1)
    cv.restore()


def wl_dab_ext(pen, v, o):
    """Mrs. Dabrowski's house across the lane: butter-yellow siding, a red door, her porch and flower boxes."""
    night = o.get('tod', 'night') == 'night'
    x0, x1, y0, y1 = WL_DAB
    walls = {'front': ((x1, y1), (x0, y1)), 'west': ((x0, y1), (x0, y0)), 'east': ((x1, y0), (x1, y1))}
    def art(p_, W, H, wall_, a, b):
        pat(p_, W, H, 'clapboard', '#000000', 110)
        p_.texture(rect(0, 0, W, H), 'grunge', 0.3, 'overlay', 1.2)
        p_.fill(rect(0, H - 50, W, 50), '#6e6a64')
        if wall_ != 'front': return
        u = lambda x: (x1 - x) * 100
        for (c0, c1) in ((-1.9, -0.3), (4.2, 5.8)):
            ua, ub = sorted((u(c0), u(c1)))
            _wl_window_art(p_, ua, ub, H - (2.05 - WL_G) * 100, H - (0.85 - WL_G) * 100, night, shutters=True)
            p_.fill(rect(ua - 4, H - (0.85 - WL_G) * 100 + 6, ub - ua + 8, 18), '#5a3a24')
            for k in range(6): p_.fill(oval(ua + 8 + k * (ub - ua - 16) / 5, H - (0.85 - WL_G) * 100 + 4, 6), ('#d84a5a', '#f2d04a', '#e88aa8')[k % 3])
        ua, ub = sorted((u(WL_DABDOOR[0]), u(WL_DABDOOR[1])))
        yt = H - (WL_DABDOOR[2] - WL_G) * 100
        p_.fill(rect(ua - 10, yt - 12, ub - ua + 20, H - 50 - yt + 12), WL_PAL['trim'])
        p_.cv.save(); p_.cv.translate(ua, yt); door_art('six', 'left', bolt=False, col=WL_PAL['dab_door'])(p_, ub - ua, H - 50 - yt); p_.cv.restore()
    _wl_walls(pen, v, walls, WL_G, WL_G + 3.0, WL_PAL['dab_siding'] if not night else mix(WL_PAL['dab_siding'], '#2a2e40', 0.3), art)
    _wl_gable_roof(pen, v, x0, x1, y0, y1, WL_G + 3.0, WL_G + 6.0, '#4a3a34', side_col=WL_PAL['dab_siding'])
    draw_box(pen, v, Box(2.25, -23.3, 2.6, 1.4, WL_G, WL_G + 0.45, 0), {'top': '#8a7a6a', 'all': '#e8e2d4'}, lw=0.8)


def wl_ext_draw(pen, v, o, ours=True):
    """Everything outside that does not move (cached): sky, far ring, ground, houses, trees, streetlight poles."""
    tod = o.get('tod', 'night')
    wl_sky(pen, v, tod)
    dr_far_ring(pen, v, 'night' if tod == 'night' else 'dawn')
    with lighting(*_wl_ext_light(tod)):
        wl_ground(pen, v, tod)
        for (x0, x1) in ((-26.0, -15.0), (-14.0, -5.0), (10.0, 21.0), (24.0, 34.0)):
            dr_neighbour(pen, v, x0, x1, -24.5, 9.0, tod, lit_room=(1 if x0 == -14.0 and tod == 'night' else None), seed=int(x0))
        for (x0, x1) in ((-22.0, -10.5), (15.0, 26.0)):
            dr_neighbour(pen, v, x0, x1, 0.0, 10.0, tod, seed=int(x0) + 5)
        wl_dab_ext(pen, v, o)
        for i, (x, y, h) in enumerate([(-8.6, -4.5, 8.0), (13.6, -5.0, 8.5), (-6.0, -20.5, 8.0), (9.0, -20.0, 7.5), (-24.0, -6.0, 8.0), (28.0, -20.5, 8.0)]):
            _wl_tree(pen, v, x, y, h, tod, i)
        for (x, y) in WL_LAMPS:
            if v.d(x, y) > 0.8: dr_streetlight(pen, v, x, y, 1.0, arm=1.0)


def wl_ext_glow(v, o, name='ext_glow'):
    """Live light: the streetlights, our porch light, lit windows (o['win'] = {name: level}), the attic dormer
    (o['attic']: the attic light Mrs. Dabrowski sees), the keypad's green backlight, the police bars."""
    tod = o.get('tod', 'night')
    kp = _kfn(o.get('porch', 0.0), 702); ka = _kfn(o.get('attic', 0.0), 703)
    wins = {nm: _kfn(lv, 710 + i) for i, (nm, lv) in enumerate((o.get('win') or {}).items())}
    def draw(pen, t):
        if tod == 'night':
            for (x, y) in WL_LAMPS + [WL_LAMP]:
                dr_streetlight_glow(pen, v, x, y, 1.0, D_SODIUM, 1.0, rain=False, t=t)
    def draw_house(pen, t):
        k = kp(t)
        if k > 0.01 and v.d(WL_PLIGHT[0], WL_PLIGHT[2]) > 0.3:
            x, y = v.p(*WL_PLIGHT); s = v.s(WL_PLIGHT[0], WL_PLIGHT[2])
            pen.glow(x, y, 1.4 * s, '#ffc070', 110 * k); pen.glow(x, y, 0.1 * s, '#fff4d8', 240 * k)
        for nm, kf in wins.items():
            k = kf(t)
            if k <= 0.01 or nm not in WL_WINS_EXT: continue
            w_, c0, c1, sl, tp = WL_WINS_EXT[nm]
            q = _wl_wquad(w_, c0, c1, sl, tp)
            n = {'front': (0, 0, -1), 'back': (0, 0, 1), 'west': (-1, 0, 0), 'east': (1, 0, 0)}[w_]
            if not v.visible(q[0], n): continue
            path = v.poly3(q)
            if path.isEmpty(): continue
            bb = path.computeTightBounds()
            pen.linear(path, 0, bb.top(), 0, bb.bottom(), [(0, '#ffd090', 200 * k), (1, '#e89a48', 220 * k)])
            pen.glow((bb.left() + bb.right()) / 2, (bb.top() + bb.bottom()) / 2, bb.width(), '#ffb060', 40 * k)
        k = ka(t)
        if k > 0.01 and v.visible((1.5, 6.5, -0.5), (0, 0, -1)):
            path = v.poly3(_wl_dormer_quad())
            if not path.isEmpty():
                bb = path.computeTightBounds()
                pen.fill(path, '#ffcc66', 200 * k)
                pen.glow((bb.left() + bb.right()) / 2, (bb.top() + bb.bottom()) / 2, 1.6 * bb.width(), WL_ATTIC, 60 * k)
        if tod == 'night' and v.d(WL_KEYPAD[0], -0.03) > 0.5:
            x, y = v.p(WL_KEYPAD[0], WL_KEYPAD[1], -0.03); s = v.s(WL_KEYPAD[0], -0.03)
            pen.glow(x, y, 0.14 * s, '#a8ffb0', 70)
    lay = Layer(30.0, draw, name, blur=None); lay.order = ORDER_SHELL - 0.5
    lay2 = Layer(10.0, draw_house, name + '_house', blur=None); lay2.order = ORDER_SHELL - 0.5
    return [lay, lay2]


def _wl_police_layers(v, o):
    """The patrol cars at our kerb (side-view cruisers: only for cameras that look across the lane) and their light
    pools on the road; their red / blue bars follow o['police'] (wl_police(t0))."""
    pr, pb = _pol(o)
    fr, fb = _kfn(pr, 731), _kfn(pb, 732)
    L = []
    side_on = abs(math.sin(math.radians(v.yaw))) < 0.26 and abs(getattr(v, 'pitch', 0.0)) < 14
    for i, (px, py, fc) in enumerate(WL_POLICE_CARS):
        if v.d(px, py) < 3.0: continue
        def car(pen, t, px=px, py=py, fc=fc, i=i):
            vg = lifted(v, WL_ROAD)
            r_, b_ = fr(t + 0.37 * i), fb(t + 0.37 * i)
            x_, y_ = vg.p(px, 0.0, py); s = vg.s(px, py)
            if side_on:
                f_ = fc if math.cos(math.radians(v.yaw)) > 0 else -fc
                patrol_car(pen, x_, y_, 4.9 * s, t, facing=f_, lights=(r_, b_), head=False, figures=())
            k = max(r_, b_)
            if k > 0.01:
                pen.ellipse_glow(x_, y_, 3.5 * s, 0.9 * s, WL_RED if r_ >= b_ else WL_BLUE, 70 * k)
        lay = Layer(max(0.3, v.d(px, py)), car, 'police_car_%d' % i, blur=None)
        lay.order = v.d(px, py)
        L.append(lay)
    return L


class WlStreet(Room):
    """Larkspur Lane as a room: the shell is wl_ext_draw; the pieces are our house, the garage, the porch, the lamp."""
    name = 'street'
    poly = [(-90.0, -40.0), (90.0, -40.0), (90.0, 30.0), (-90.0, 30.0)]

    def lights(self, o):
        tod = o.get('tod', 'night')
        amb, steady = _wl_ext_light(tod)
        steady = list(steady)
        if tod == 'night':
            for (x, y) in WL_LAMPS + [WL_LAMP]:
                steady.append(Lamp(x, WL_G + 6.0, y - 1.6, 14.0, D_SODIUM, 1.7, (1.0, 0.6, 0.2), fall=1.35))
        pr, pb = _pol(o)
        var = [('porch', [Lamp(WL_PLIGHT[0], WL_PLIGHT[1], WL_PLIGHT[2] - 0.3, 6.0, '#ffc888', 1.6, fall=1.5)], _kfn(o.get('porch', 0.0), 702)),
               ('police_r', [Lamp(-2.0, WL_G + 1.6, -9.4, 20.0, WL_RED, 1.3, fall=1.3)], _kfn(pr, 731)),
               ('police_b', [Lamp(3.0, WL_G + 1.6, -9.4, 20.0, '#4a72ff', 1.4, fall=1.3)], _kfn(pb, 732)),
               ('flash', [Lamp(*o.get('flash_at', (0.0, WL_G + 1.4, -6.0)), R=6.0, c='#fff4dc', k=1.6, fall=1.4)], _kfn(o.get('flash', 0.0), 733))]
        return amb, steady, var

    def shell(self, pen, v, o):
        wl_ext_draw(pen, v, o)

    def pieces(self, o):
        return [Piece('house', (0.0, 2.0, 5.0), lambda pen, v: wl_house_ext(pen, v, o), block=_r4p(WL_HOUSE)),
                Piece('garage', (9.2, 1.5, 4.0), lambda pen, v: wl_garage_ext(pen, v, o), block=_r4p(WL_GAR)),
                Piece('porch', (0.45, -0.2, -1.0), lambda pen, v: wl_porch(pen, v, o), block=_r4p((WL_PORCH[0], WL_PORCH[1], WL_STEPS[2], 0.0))),
                Piece('our_lamp', (WL_LAMP[0], WL_G + 3.0, WL_LAMP[1]), lambda pen, v: dr_streetlight(pen, v, WL_LAMP[0], WL_LAMP[1], 1.0, arm=1.0),
                      block=_circ(WL_LAMP[0], WL_LAMP[1], 0.15))]

    def spots(self, v, o):
        S = {}
        G = WL_G
        S['porch_door'] = _mk_spot(v, 'porch_door', 0.45, -0.55, 0.0, 'stand', 'on the porch at the front door, facing it (+y)', face=(0, 1))
        S['porch_out'] = _mk_spot(v, 'porch_out', 0.6, -0.9, 0.0, 'stand', 'on the porch facing out (Mom at the door, Mrs. Dabrowski talking)', face=(0, -1))
        S['step_bottom'] = _mk_spot(v, 'step_bottom', 0.45, -2.75, G, 'stand', 'at the foot of the steps (Mrs. Dabrowski with the pie)', face=(0, 1))
        S['walk'] = _mk_spot(v, 'walk', 0.45, -4.8, G, 'stand', 'on the front walk', face=(0, 1))
        S['frog'] = _mk_spot(v, 'frog', WL_FROG[0], WL_FROG[1], G, 'surface', 'the stone frog (the key under it)')
        S['frog_kneel'] = _mk_spot(v, 'frog_kneel', WL_FROG[0] + 0.1, WL_FROG[1] - 0.5, G, 'stand', 'crouched at the frog (Dad: "Handy")', face=(0, 1))
        S['keypad'] = _mk_spot(v, 'keypad', WL_KEYPAD[0], -0.03, WL_KEYPAD[1], 'point', 'the garage keypad')
        S['keypad_stand'] = _mk_spot(v, 'keypad_stand', WL_KEYPAD[0] - 0.15, -0.6, G, 'stand', 'at the keypad (facing it)', face=(0, 1))
        S['garage_door'] = _mk_spot(v, 'garage_door', 9.2, -0.4, G, 'stand', 'in front of the garage door')
        S['driveway'] = _mk_spot(v, 'driveway', 9.2, -4.5, G, 'stand', 'on the driveway (the movers, the boxes)')
        S['boys_window'] = _mk_spot(v, 'boys_window', 3.4, -0.02, WL_UP + 1.45, 'point', "the boys' window from outside")
        S['attic_window'] = _mk_spot(v, 'attic_window', 1.5, WL_DORMER[2] - 0.02, _wl_roof_Y(WL_DORMER[2]) + 0.5, 'point', 'the attic dormer window (the attic light)')
        S['curb_sit'] = _mk_spot(v, 'curb_sit', 1.0, WL_KN - 0.3, WL_ROAD, 'seat', 'Mr. Pell sitting on our kerb, feet in the gutter, facing the lane',
                                 face=(0, -1), seat_Y=WL_G - WL_ROAD)
        S['curb_officer'] = _mk_spot(v, 'curb_officer', 2.1, WL_KN + 0.5, G, 'stand', 'Officer Reyes on the sidewalk beside him', face=(-0.6, -0.8))
        S['to_car'] = _mk_spot(v, 'to_car', 0.4, WL_KN - 0.4, WL_ROAD, 'stand', 'walking to the car (he looks up at the window)', face=(0, 1))
        for i, (px, py, fc) in enumerate(WL_POLICE_CARS):
            S['police_%d' % i] = _mk_spot(v, 'police_%d' % i, px, py, WL_ROAD, 'surface', 'patrol car %d (centre between the wheels)' % i)
        S['dab_door'] = _mk_spot(v, 'dab_door', 2.25, -23.0, WL_G + 0.45, 'stand', "on Mrs. Dabrowski's porch", face=(0, 1))
        S['dab_walk'] = _mk_spot(v, 'dab_walk', 2.25, -18.5, G, 'stand', "on her walk, crossing with the pie", face=(0, 1))
        S['street_mid'] = _mk_spot(v, 'street_mid', 2.0, -12.0, WL_ROAD, 'stand', 'the middle of Larkspur Lane')
        return S


def _window_out_layer():
    """Screen-space foreground for the POV out of the boys' window: the sash, the box fan's edge, soft."""
    def draw(pen, t):
        pen.fill(minus(rect(-400, -300, 2720, 1700), rrect(170, 70, 1580, 940, 8)), '#1c1a1c')
        pen.fill(rect(-400, 515, 2720, 50), '#2a2628')
        pen.fill(rect(934, -300, 52, 1700), '#2a2628')
    return Layer(0.3, draw, 'window_frame', blur=8)


_wcam('wl_ext_house', 1250, 600, WL_G + 1.65, 3.0, -21.5, 0, _env(f=(1.0, 2.6)), 'our house from across Larkspur Lane (Mrs. Dabrowski\'s yard): porch, garage, the dormer, the lane', 'street')
_wcam('wl_ext_porch', 1000, 520, WL_G + 1.55, 0.45, -6.2, 3, _env(), 'up the walk to the porch and the front door; the stone frog by the bottom step', 'street')
_wcam('wl_ext_frog', 1400, 470, WL_G + 0.8, 1.55, -3.25, -12, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.1)), 'low on the stone frog beside the step', 'street', pitch=30.0)
_wcam('wl_ext_garage', 900, 520, WL_G + 1.6, 8.4, -6.4, 18, _env(), 'the garage door and the keypad from the driveway', 'street')
_wcam('wl_ext_keypad', 1500, 520, WL_G + 1.5, 11.05, -0.95, 28, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.1)), 'close on the keypad beside the garage door', 'street')
_wcam('wl_ext_across', 1100, 560, 1.55, 0.6, -1.2, 180, _env(f=(1.0, 2.4)), "from our porch across the lane to Mrs. Dabrowski's house", 'street')
_wcam('wl_ext_curb', 820, 540, WL_G + 1.55, 1.6, -3.6, 184, _env(f=(1.0, 2.2)), 'from our lawn to the kerb: the police cars, the man on the curb', 'street')
_wcam('wl_ext_up', 900, 900, WL_G + 1.3, 3.0, -8.2, 2, _env(), "from the kerb up at the boys' window (\"That was my room\")", 'street')
_wcam('wl_ext_from_window', 820, 540, WL_UP + 1.4, 3.4, 0.4, 180, _env(x=(920, 1000), y=(500, 560), zoom=(1.0, 1.06)),
      "POV down from the boys' window to the lawn and the kerb", 'street', pitch=30.0)


def wl_street(view='house', tod='night', porch=0.0, win=None, attic=0.0, police=None, frog_lift=0.0, key=True, flash=0.0, flash_at=None, **kw):
    """Larkspur Lane. view: house | porch | frog | garage | keypad | across | curb | up | from_window. tod 'night' |
    'day' (moving day, the pie on Saturday) | 'morning'. porch: porch light; win: {liv, liv_w1, liv_w2, dining, bath, stair,
    boys, par, kitchen}: lit windows (levels); attic: the attic dormer lit (Mrs. Dabrowski: "right around two"); police:
    None | True | ST.wl_police(t0) -> three patrol cars at our kerb, bars sweeping red / blue (cars drawn in the views
    that look across the lane: house, curb, up, across); frog_lift 0..1 tips the frog (the key under it); key: the key
    there; flash / flash_at: an officer's flashlight."""
    v = cam('wl_ext_' + view)
    o = dict(tod=tod, porch=porch, win=dict(win or {}), attic=attic, police=police, frog_lift=frog_lift if not callable(frog_lift) else 0.0,
             key=key, flash=flash, flash_at=flash_at or (1.0, WL_G + 1.4, -7.0), no_veil=True)
    o.update(kw)
    main = WlStreet()
    dyn = list(wl_ext_glow(v, o))
    if police: dyn += _wl_police_layers(v, o)
    amb, steady, var = main.lights(o)
    if callable(frog_lift):
        dyn.append(live_layer('frog_live', v, (WL_FROG[0], WL_G, WL_FROG[1]), lambda pen, v_, t: wl_frog(pen, v_, WL_FROG[0], WL_G, WL_FROG[1], lift=frog_lift(t), key=key),
                              amb, steady, var, order=v.d(*WL_FROG) - 0.02))
    grade = 'wl_day' if tod in ('day', 'morning') else ('wl_police' if police else 'wl_ext')
    sp = build_view('wl_ext_' + view, v, main, o, outside=None, grade=grade, dyn=dyn, dof=0.6)
    L = {l.name: l for l in sp}
    if 'house' in L and 'garage' in L: L['garage'].order = min(L['garage'].order, L['house'].order - 0.01) if v.hx > 6.0 else max(L['garage'].order, L['house'].order + 0.01)
    if view == 'from_window': sp = sp.add(_window_out_layer())
    sp.info['note'] = 'Outside: figures order = sp.order_at(x, y). Pell on the kerb: anchor curb_sit (seat). Police: wl_police(t0).'
    return sp


# ====================================================================================================== interior props
def _wl_outside(o):
    """The night (or day) through our windows: sky, lawns, the lane, the houses (cached; the engine veils it at night)."""
    def f(pen, v):
        wl_ext_draw(pen, v, o)
    return f


def _wl_fan_art(p_, W, H, night=True):
    """A box fan's face (cm frame): plastic frame, the blades a soft blur behind the round grille, the knob."""
    p_.fill(rrect(0, 0, W, H, 4), '#d8dadc' if not night else '#c8cacc')
    cx, cy, r = W / 2, H / 2, min(W, H) * 0.44
    p_.fill(oval(cx, cy, r), '#2a2c30')
    for k in range(5):
        a = k * 72.0
        bl = smooth([(cx, cy), (cx + r * 0.9 * math.cos(math.radians(a)), cy + r * 0.9 * math.sin(math.radians(a))),
                     (cx + r * 0.85 * math.cos(math.radians(a + 30)), cy + r * 0.85 * math.sin(math.radians(a + 30)))], True, 0.6)
        p_.fill(bl, '#8a8e94', 90)
    p_.fill(oval(cx, cy, r * 0.82), '#9a9ea4', 40)
    for k in range(1, 6): p_.line(oval(cx, cy, r * k / 5.5), 0.5, '#e8eaec', 200)
    p_.seg((cx - r, cy), (cx + r, cy), 0.5, '#e8eaec', 200); p_.seg((cx, cy - r), (cx, cy + r), 0.5, '#e8eaec', 200)
    p_.fill(oval(cx, cy, r * 0.14), '#e8eaec')
    p_.fill(oval(W - 6, H - 6, 2.2), '#3a3c40')


def _wl_fan_piece(name, cx, cy, Y0, fa, o):
    B = Box(cx, cy, 0.52, 0.15, Y0, Y0 + 0.52, fa)
    night = o.get('tod', 'night') == 'night'
    return Piece(name, (cx, Y0 + 0.26, cy), lambda pen, v: draw_box(pen, v, B, {'front': dict(fill='#d0d2d4', art=lambda p_, W, H: _wl_fan_art(p_, W, H, night)),
                                                                              'all': '#b8babc'}, lw=0.8), block=B.footprint())


def _wl_vent_art(p_, ax, by, w=30.0, d=12.0, ang=0.0):
    """A floor register in a floor's cm frame: metal frame, eight louvres, dark slots (the dark under the house)."""
    p_.cv.save(); p_.cv.translate(ax, by); p_.cv.rotate(ang)
    p_.fill(rect(-w / 2 - 2, -d / 2 - 2, w + 4, d + 4), '#8a8478'); p_.line(rect(-w / 2 - 2, -d / 2 - 2, w + 4, d + 4), 0.6)
    p_.fill(rect(-w / 2, -d / 2, w, d), '#0c0a08')
    for k in range(9):
        x = -w / 2 + 1 + k * (w - 2) / 8
        p_.fill(rect(x - 0.7, -d / 2 + 0.6, 1.4, d - 1.2), '#a8a294'); p_.fill(rect(x + 0.3, -d / 2 + 0.6, 0.4, d - 1.2), '#5a564e')
    p_.cv.restore()


def _wl_boxes(pen, v, specs, Y0=0.0):
    """Moving boxes: specs [(cx, cy, w, d, h, fa, label)] (stacked by giving Y0 offsets in label tuples)."""
    for (cx, cy, w, d, h, fa, lab, y0) in specs:
        B = Box(cx, cy, w, d, Y0 + y0, Y0 + y0 + h, fa)
        def art(p_, W, H, lab=lab):
            p_.texture(rect(0, 0, W, H), 'paper', 0.4, 'multiply', 0.8)
            p_.fill(rect(0, 0, W, 5), '#c8b078', 200)
            if lab: btext(p_, lab, W / 2, H * 0.55, 'caveat_b', min(14.0, W / max(3, len(lab)) * 1.6), '#2a2a2a', 220, 'center')
        draw_box(pen, v, B, {'front': dict(fill=WL_PAL['box'], art=art), 'top': dict(fill='#d4ac78', art=lambda p_, W, H: p_.fill(rect(W / 2 - 3, 0, 6, H), '#c8b078', 220)),
                             'all': '#b88e5e'}, lw=0.8)


def _wl_door(hinge, w, h, cd, swing, Y0, a_latch, b_latch, bolt_a=False, turn=0.0, col='#efe9dc', kind='six', art_a=None, art_b=None):
    return Door(hinge, w, h, cd, swing, Y0, art_a=art_a or door_art(kind, a_latch, bolt=bolt_a, turn=turn), art_b=art_b or door_art(kind, b_latch, bolt=False), col=col)


def _door_piece(name, D, ang, Ymid):
    dx, dy = D.dir(ang)
    ref = (D.hinge[0] + dx * D.w / 2, Ymid, D.hinge[1] + dy * D.w / 2)
    return Piece(name, ref, lambda pen, v, D=D, a=ang: D.draw(pen, v, a))


def _wl_louvre_art(p_, W, H):
    """The hall closet's louvred door (hall side): stiles, rails, two banks of slats; the knob."""
    p_.fill(rect(0, 0, W, H), '#ece6d8'); p_.texture(rect(0, 0, W, H), 'wood', 0.25, 'overlay', 0.8, 90)
    for (y0, y1) in ((10, H * 0.47), (H * 0.53, H - 10)):
        p_.fill(rect(9, y0, W - 18, y1 - y0), '#2a2620')
        n = int((y1 - y0) / 4.2)
        for k in range(n):
            yy = y0 + k * (y1 - y0) / n
            p_.fill(rect(9, yy, W - 18, 2.6), '#ddd6c6'); p_.fill(rect(9, yy + 2.6, W - 18, 0.6), '#9a9284')
        p_.line(rect(9, y0, W - 18, y1 - y0), 0.8, '#000000', 120)
    p_.fill(oval(W - 7, H * 0.5, 2.6), '#b89a58'); p_.line(oval(W - 7, H * 0.5, 2.6), 0.5)


def _wl_marks_face(fresh=True):
    """The pencil marks on the boys' door casing (room side, the front jamb at y WL_MARKS[1]): L age 4 / 8 / 12, and one
    more, higher than all of them, in fresh dark pencil, dated last week. -> Face + art."""
    x, y = WL_MARKS
    F = Face((x + 0.012, WL_UP + 2.0, y - 0.075), (0.0, 0.0, 1.0), (0.0, -1.0, 0.0), 9.0, 200.0, (1.0, 0.0, 0.0), 'wall')
    def art(p_, W, H):
        p_.fill(rect(0, 0, W, H), '#f0ece2'); p_.line(rect(0, 0, W, H), 0.5, '#000000', 80)
        for (Ym, lab) in ((1.02, 'L 4'), (1.27, 'L 8'), (1.50, 'L 12')):
            yy = H - Ym * 100
            p_.seg((0.6, yy), (W - 0.6, yy), 0.45, '#6a6a70', 170)
            btext(p_, lab, 1.0, yy - 0.8, 'hand', 2.6, '#6a6a70', 160)
        if fresh:
            yy = H - 1.86 * 100
            p_.seg((0.4, yy), (W - 0.4, yy), 0.6, '#2a2a30', 240)
            btext(p_, 'L', 1.0, yy - 0.8, 'hand', 2.8, '#2a2a30', 235)
    return F, art


# ---------------------------------------------------------------------------------------------- the living room
def _wl_liv_cfg(o):
    night = o.get('tod', 'night') == 'night'
    sl, tp = WL_LWIN_F[2], WL_LWIN_F[3]
    def lights(o):
        amb = _wl_amb(o, '#1e2438')
        sky = WL_MOON if night else '#fff0d0'
        k = 0.85 if night else 1.5
        steady = [Lamp(kind='win', c=sky, k=k, soft=10.0, panes=_panes_y(WL_LWIN_F[0], WL_LWIN_F[1], sl, tp, 0.0), d=_norm3((-0.25, -0.5, 1.0)))]
        for (y0, y1) in WL_LWIN_W:
            steady.append(Lamp(kind='win', c=sky, k=k * 0.8, soft=10.0, panes=_panes_x(y0, y1, sl, tp, -6.0), d=_norm3((1.0, -0.5, 0.3))))
        var = [('lamp', [Lamp(-0.95, 1.45, 5.2, 5.0, WL_WARM, 1.5, (1.0, 0.6, 0.35), fall=1.4)], _kfn(o.get('lamp', 0.0), 801)),
               ('ceil', [Lamp(-3.3, 2.45, 2.8, 6.0, '#ffe8c8', 1.2, (1.0, 0.5, 0.2), fall=1.3)], _kfn(o.get('ceil', 0.0), 802))]
        var += _wl_var_common(o, 803, (-2.6, 1.1, 3.0), (-1.2, 1.4, 2.0))
        return amb, steady, var
    def back(p_, W, H):                                                         # run (-6, 5.6) -> (-0.6, 5.6): u = x + 6
        _bu_photo(p_, 2.4 * 100, H - 175, 46, 34, 'kids')
        _light_switch(p_, 5.1 * 100, H - 120, True)
    def east(p_, W, H):                                                         # run (-0.6, 5.6) -> (-0.6, 0): u = 5.6 - y
        _light_switch(p_, (5.6 - 3.25) * 100, H - 120, True)
    wins = {'front': [(WL_LWIN_F[0], 0.0, WL_LWIN_F[1], 0.0, sl, tp, (2, 2))],
            'west': [(-6.0, y0, -6.0, y1, sl, tp, (2, 2)) for (y0, y1) in WL_LWIN_W]}
    holes = {'east': [(-0.6, WL_LOPEN[0], -0.6, WL_LOPEN[1], 0.0, WL_LOPEN[2])]}
    runs = _rect_runs(WL_LIV, holes, wins, {'back': back, 'east': east})
    rug = _bu_rug_art(WL_LIV[0], WL_LIV[3], -2.8, 3.2, 1.5, 1.05, ('#6a3a2c', '#c8b898', '#3a4a6a', '#9a7a52', '#5a4a3a'))
    def floor_art(p_, W, H):
        rug(p_, W, H)
        _wl_vent_art(p_, (WL_VENT_L[0] - WL_LIV[0]) * 100, (WL_LIV[3] - WL_VENT_L[1]) * 100)

    def pieces(o):
        ap = dr_armchair_parts(WL_ARM, WL_PAL['armchair'], WL_PAL['armchair_d'], doily=False)
        aseat = WL_ARM.at(0, -WL_ARM.d / 2 + 0.42, 0)
        P = [Piece('armchair', (WL_ARM.cx, 0.4, WL_ARM.cy), lambda pen, v: draw_parts(pen, v, ap), occupant=[(aseat[0], aseat[2])], front=ap, block=WL_ARM.footprint())]
        cp = couch_parts(WL_COUCH, WL_PAL['couch'], WL_PAL['couch_d'], afghan=False, blanket=False)
        P.append(Piece('couch', (WL_COUCH.cx, 0.4, WL_COUCH.cy), lambda pen, v: draw_parts(pen, v, cp), occupant=[(x, y) for (n, x, y) in couch_seats(WL_COUCH)],
                       front=cp, block=WL_COUCH.footprint()))
        lk = _static(o.get('lamp', 0.0))
        P.append(Piece('floor_lamp', (-0.95, 1.0, 5.2), lambda pen, v: lamp_floor(pen, v, -0.95, 5.2, 1.15, 1.5, lk), block=_circ(-0.95, 5.2, 0.18)))
        bx = [(-1.15, 0.55, 0.6, 0.45, 0.45, 8, 'BOOKS', 0.0), (-1.2, 0.6, 0.5, 0.4, 0.38, -6, 'KITCHEN', 0.45), (-1.25, 1.25, 0.55, 0.45, 0.5, 15, 'THEO', 0.0)]
        if o.get('boxes', True):
            P.append(Piece('boxes', (-1.2, 0.4, 0.8), lambda pen, v: _wl_boxes(pen, v, bx), block=_r4p((-1.55, -0.85, 0.3, 1.55))))
        P.append(_wl_fan_piece('fan_front', (WL_LWIN_F[0] + WL_LWIN_F[1]) / 2, 0.1, sl, 180, o))
        for i, (y0, y1) in enumerate(WL_LWIN_W):
            P.append(_wl_fan_piece('fan_w%d' % (i + 1), -5.9, (y0 + y1) / 2, sl, 90, o))
        return P

    def spots(v, o):
        S = {}
        aseat = WL_ARM.at(0, -WL_ARM.d / 2 + 0.42, 0)
        S['armchair'] = _mk_spot(v, 'armchair', aseat[0], aseat[2], 0.0, 'seat', "Mr. Pell's green armchair (facing south-east)", face=WL_ARM.N, seat_Y=0.46)
        fr = WL_ARM.at(0, WL_ARM.d / 2 + 0.45, 0)
        S['chair_front'] = _mk_spot(v, 'chair_front', fr[0], fr[2], 0.0, 'stand', 'standing at the chair, facing it (lifting the cushion)', face=(-WL_ARM.N[0], -WL_ARM.N[1]))
        st = WL_ARM.at(0, -0.02, 0.48)
        S['chair_seat'] = _mk_spot(v, 'chair_seat', st[0], st[2], 0.48, 'surface', 'the seat cushion top (warm; the drawings under it)')
        S['vent'] = _mk_spot(v, 'vent', WL_VENT_L[0], WL_VENT_L[1], 0.0, 'surface', 'the floor vent half under the chair ("Vent\'s right under it")')
        for (n, x, y) in couch_seats(WL_COUCH):
            S['couch_' + n] = _mk_spot(v, 'couch_' + n, x, y, 0.0, 'seat', 'the couch, %s seat (facing the front)' % n, face=(0, -1), seat_Y=COUCH_SEAT)
        S['fan_front'] = _mk_spot(v, 'fan_front', (WL_LWIN_F[0] + WL_LWIN_F[1]) / 2, 0.1, WL_LWIN_F[2] + 0.26, 'point', 'the box fan in the front window')
        S['window_w1'] = _mk_spot(v, 'window_w1', -5.5, sum(WL_LWIN_W[0]) / 2, 0.0, 'stand', 'at the first west window (facing it)', face=(-1, 0))
        S['room_mid'] = _mk_spot(v, 'room_mid', -2.4, 2.4, 0.0, 'stand', 'the middle of the room')
        S['opening'] = _mk_spot(v, 'opening', -0.95, 2.0, 0.0, 'stand', 'at the opening to the entry (facing in, -x)', face=(-1, 0))
        return S
    return dict(name='living', R=WL_LIV, H=WL_CEIL, floor=dict(base=WL_PAL['floor'], kind='boards', ink='#4a2e1a', seed=11, art=floor_art), runs=runs,
                walls=dict(paper=WL_PAL['liv_paper'], ink=WL_PAL['liv_ink'], kind='stripe', wains=0.0, seed=17, scale=0.9, pa=50),
                ceil=dict(c='#ece6da'), lights=lights, pieces=pieces, spots=spots)


# ---------------------------------------------------------------------------------------------- the kitchen
_WL_KIT_POLY = [(1.4, 3.6), (6.0, 3.6), (6.0, 8.6), (4.8, 8.6), (4.8, 10.0), (1.4, 10.0)]


def wl_garage_door(bolt=1.0):
    """The door from the garage, kitchen side (art_a): the deadbolt thumb-turn above the knob (bolt 1 locked, 0 open)."""
    return _wl_door((6.0, WL_GDOOR[1]), WL_GDOOR[1] - WL_GDOOR[0], WL_GDOOR[2], (0.0, -1.0), -1, 0.0, 'right', 'left', bolt_a=True, turn=bolt, kind='four', col='#f2eee4')


def wl_bread(pen, v, x, Y, y, state='twisted', fa=10.0):
    """Half a loaf in its clear bag on the counter: 'twisted' (folded neatly, twisted shut: someone polite) | 'open'."""
    if v.d(x, y) < 0.2 or not state: return
    B = Box(x, y, 0.3, 0.13, Y, Y + 0.11, fa)
    draw_box(pen, v, B, {'top': dict(fill='#d8a868', art=lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'paper', 0.5, 'overlay', 0.8)), 'all': '#e8c890'}, lw=0.7)
    tip = B.at(-0.19 if state == 'twisted' else -0.24, 0.0, Y + 0.06)
    if v.d(tip[0], tip[2]) > 0.2:
        px, py = v.p(*tip); s = v.s(tip[0], tip[2])
        if state == 'twisted':
            tw = poly([(px - 0.05 * s, py - 0.02 * s), (px + 0.02 * s, py - 0.006 * s), (px + 0.02 * s, py + 0.006 * s), (px - 0.05 * s, py + 0.02 * s)])
            pen.fill(tw, '#eef2f8', 200); pen.line(tw, 0.7)
            pen.fill(rect(px - 0.004 * s, py - 0.012 * s, 0.012 * s, 0.024 * s), '#3a7ad0')
        else:
            op = poly([(px - 0.06 * s, py - 0.05 * s), (px + 0.03 * s, py - 0.03 * s), (px + 0.03 * s, py + 0.03 * s), (px - 0.08 * s, py + 0.04 * s)])
            pen.fill(op, '#eef2f8', 150); pen.line(op, 0.6)
    q = [B.at(-0.17, 0.08, Y + 0.13), B.at(0.17, 0.08, Y + 0.13), B.at(0.17, 0.08, Y), B.at(-0.17, 0.08, Y)]
    if v.d(q[0][0], q[0][2]) > 0.2:
        path = v.poly3(q)
        if not path.isEmpty(): pen.fill(path, '#f4f8ff', 50); pen.line(path, 0.5, '#ffffff', 120)


def wl_note(pen, v, x, Y, y, fa=-8.0):
    """Mr. Pell's note lying on the counter: a cream notepaper sheet, shaky blue lines of writing (legible: the insert)."""
    if v.d(x, y) < 0.15: return
    F = Face(Box(x, y, 0.15, 0.21, Y, Y, fa).at(-0.075, 0.105, Y + 0.002), _norm3((math.cos(math.radians(fa)), 0.0, math.sin(math.radians(fa)))),
             _norm3((math.sin(math.radians(fa)), 0.0, -math.cos(math.radians(fa)))), 15.0, 21.0, (0.0, 1.0, 0.0), 'top')
    def art(p_, W, H):
        p_.fill(rect(0, 0, W, H), '#f4ecd4')
        for k in range(9): p_.seg((1.5, 3.0 + k * 1.9), (W - 1.5 - (4 if k in (1, 7) else 0), 3.0 + k * 1.9), 0.35, '#2a3a8a', 190)
    draw_face(pen, v, F, art, '#f4ecd4', ao=False, lw=0.5, two_sided=True)


def _wl_kit_cfg(o):
    night = o.get('tod', 'night') == 'night'
    def lights(o):
        amb = _wl_amb(o, '#1c2236')
        steady = [Lamp(kind='win', c=WL_MOON if night else '#fff0d0', k=0.9 if night else 1.4, soft=10.0, panes=_panes_y(WL_KWIN[0], WL_KWIN[1], WL_KWIN[2], WL_KWIN[3], 10.0),
                       d=_norm3((0.35, -0.5, -1.0)))]
        if o.get('nightlight', True) and night:
            steady.append(Lamp(WL_KNL[0] - 0.08, WL_KNL[1], WL_KNL[2], 2.6, WL_NIGHTL, 1.15, (0.6, 1.0, 1.0), fall=1.5))
        var = [('kitchen_light', [Lamp(3.6, 2.45, 6.6, 6.0, '#fff0d8', 1.3, (1.0, 0.5, 0.2), fall=1.3)], _kfn(o.get('kitchen_light', 0.0), 811)),
               ('pantry_light', [Lamp(5.4, 2.3, 9.3, 2.8, '#ffe8c0', 1.2, (1.0, 0.5, 0.2), fall=1.4)], _kfn(o.get('pantry_light', 0.0), 812))]
        var += _wl_var_common(o, 813, (3.4, 1.1, 7.0), (2.2, 1.4, 5.0))
        return amb, steady, var
    def back(p_, W, H):                                                         # run (1.4, 10) -> (4.8, 10): u = x - 1.4
        for k in range(int(3.4 * 100 / 15)):                                     # the tile backsplash
            p_.fill(rect(k * 15, H - 145, 14, 52), '#e8eef0' if k % 2 else '#d8e4e8')
        _wall_clock(p_, (4.25 - 1.4) * 100, H - 205, 11, 10, 3)
    def east(p_, W, H):                                                         # run (6, 8.6) -> (6, 3.6): u = 8.6 - y
        _light_switch(p_, (8.6 - 5.55) * 100, H - 120, True)
        x = (8.6 - WL_KNL[2]) * 100; y = H - WL_KNL[1] * 100                    # the plug-in nightlight by the garage door
        p_.fill(rrect(x - 3.5, y - 5, 7, 10, 1), '#efe6d0'); p_.fill(rrect(x - 2.5, y - 4, 5, 6, 2), '#ffe6b0' if night else '#e8e0c8')
    def pfront(p_, W, H):                                                       # run (4.8, 8.6) -> (6.0, 8.6)
        pass
    runs = [_run((6.0, 3.6), (1.4, 3.6)), _run((1.4, 3.6), (1.4, 10.0), holes=[(1.4, WL_KOPEN[0], 1.4, WL_KOPEN[1], 0.0, WL_KOPEN[2])]),
            _run((1.4, 10.0), (4.8, 10.0), wins=[(WL_KWIN[0], 10.0, WL_KWIN[1], 10.0, WL_KWIN[2], WL_KWIN[3], (2, 2))], art=back),
            _run((4.8, 10.0), (4.8, 8.6)), _run((4.8, 8.6), (6.0, 8.6), holes=[(WL_PDOOR[0], 8.6, WL_PDOOR[1], 8.6, 0.0, WL_PDOOR[2])], art=pfront),
            _run((6.0, 8.6), (6.0, 3.6), holes=[(6.0, WL_GDOOR[0], 6.0, WL_GDOOR[1], 0.0, WL_GDOOR[2])], art=east)]

    def pieces(o):
        P = []
        cnt = WL_COUNTER
        def counter(pen, v):
            draw_box(pen, v, cnt, {'top': dict(fill='#d8d0c0', art=lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'grunge', 0.3, 'overlay', 1.0)),
                                   'front': dict(fill='#7a8a7a', art=lambda p_, W, H: [p_.line(rect(6 + k * W / 6, 10, W / 6 - 12, H - 20), 1.0, '#000000', 90) for k in range(6)]),
                                   'all': '#6a7a6a'}, lw=1.0)
            sk = Box(2.7, 9.7, 0.6, 0.42, 0.78, 0.93, 0)
            draw_box(pen, v, sk, {'top': '#9aa4b0', 'all': '#8a949e'}, lw=0.8, skip=('bottom',))
            A = (2.7, 0.93, 9.95); B_ = (2.7, 1.22, 9.95)
            if v.d(A[0], A[2]) > 0.3: pen.seg(v.p(*A), v.p(*B_), max(1.0, 0.025 * v.s(A[0], A[2])), '#c8ccd4')
            if o.get('note', True): wl_note(pen, v, WL_NOTE[0], 0.92, WL_NOTE[1])
            if o.get('bread', 'twisted'): wl_bread(pen, v, WL_BREAD[0], 0.92, WL_BREAD[1], o.get('bread', 'twisted'))
        P.append(Piece('counter', (cnt.cx, 0.5, cnt.cy), counter, block=cnt.footprint()))
        for (cx, w) in ((1.75, 0.7), (3.95, 1.3)):
            up = Box(cx, 9.82, w, 0.35, 1.45, 2.3, 0)
            P.append(Piece('cabinet_%d' % int(cx * 10), (cx, 1.9, 9.82), (lambda up: lambda pen, v: draw_box(pen, v, up, {'all': '#7a8a7a', 'front': dict(fill='#7a8a7a', art=lambda p_, W, H: [
                p_.line(rect(4 + k * W / max(1, int(W / 45)), 6, W / max(1, int(W / 45)) - 8, H - 12), 1.0, '#000000', 90) for k in range(max(1, int(W / 45)))])}, lw=1.0, skip=('bottom',)))(up)))
        fr = Box(1.78, 8.45, 0.75, 0.7, 0.0, 1.8, 90)
        def fridge(pen, v):
            def art(p_, W, H):
                p_.fill(rect(0, 0, W, H), '#e8eae8'); p_.line(rect(2, H * 0.32, W - 4, 2), 1.0, '#9a9a9a')
                p_.fill(rect(W - 12, 20, 4, 40), '#b8b8b8'); p_.fill(rect(W - 12, H * 0.36, 4, 60), '#b8b8b8')
                for (dx, dy, c) in ((0.2, 0.42, '#f8f0d8'), (0.5, 0.48, '#d8f0f8'), (0.3, 0.62, '#f8e0e8')):          # Theo's drawings (the ones that fall off)
                    p_.fill(rect(W * dx, H * dy, 24, 30), c); p_.line(rect(W * dx, H * dy, 24, 30), 0.4)
                    p_.line(smooth([(W * dx + 6, H * dy + 24), (W * dx + 12, H * dy + 6), (W * dx + 18, H * dy + 24)], False), 0.8, '#c82a2a', 200)
            draw_box(pen, v, fr, {'front': dict(fill='#e8eae8', art=art), 'all': '#d8dad8'}, lw=1.0)
        P.append(Piece('fridge', (fr.cx, 0.9, fr.cy), fridge, block=fr.footprint()))
        st = Box(3.6, 3.92, 0.76, 0.62, 0.0, 0.92, 180)
        P.append(Piece('stove', (st.cx, 0.5, st.cy), lambda pen, v: draw_box(pen, v, st, {'front': dict(fill='#e8e4dc', art=lambda p_, W, H: (p_.fill(rect(8, 22, W - 16, H * 0.5), '#2a2a2a'), p_.line(rect(8, 22, W - 16, H * 0.5), 1.0))),
                                                                                       'top': dict(fill='#1a1a1a', art=lambda p_, W, H: [p_.line(oval(W * (0.28 + 0.44 * (k % 2)), H * (0.3 + 0.4 * (k // 2)), 10), 1.4, '#5a5a5a') for k in range(4)]),
                                                                                       'all': '#d8d4cc'}, lw=1.0), block=st.footprint()))
        tb = Box(3.3, 6.4, 1.2, 0.85, 0.0, 0.75, 0)
        P.append(Piece('table', (tb.cx, 0.4, tb.cy), lambda pen, v: draw_parts(pen, v, table_parts(tb, '#a8845a', apron=0.06)), block=tb.footprint()))
        for (cx, cy, fa) in ((3.3, 5.75, 180), (3.3, 7.05, 0)):
            ch = Box(cx, cy, 0.42, 0.42, 0.0, 0.45, fa)
            def chair(pen, v, ch=ch):
                draw_parts(pen, v, table_parts(ch, '#8a6440', apron=0.03, thick=0.04, legw=0.035))
                draw_box(pen, v, sub(ch, -0.2, 0.2, -0.21, -0.17, 0.45, 0.92), {'all': '#8a6440'}, lw=0.7)
            P.append(Piece('chair_%d' % fa, (cx, 0.3, cy), chair, block=ch.footprint()))
        ga = o.get('gdoor', 0.0); ga = 0.0 if callable(ga) else ga
        if not callable(o.get('bolt')):
            P.append(_door_piece('garage_door', wl_garage_door(_static(o.get('bolt', 1.0), 1.0)), ga, 1.0))
        pa = o.get('pantry_door', 0.0)
        PD = _wl_door((WL_PDOOR[1], 8.6), WL_PDOOR[1] - WL_PDOOR[0], WL_PDOOR[2], (-1.0, 0.0), 1, 0.0, 'right', 'left', kind='four')
        P.append(_door_piece('pantry_door', PD, pa, 1.0))
        return P

    def glows(v, o):
        def nl(pen, t):
            if not (o.get('nightlight', True) and night) or v.d(WL_KNL[0], WL_KNL[2]) < 0.3: return
            x, y = v.p(WL_KNL[0] - 0.01, WL_KNL[1], WL_KNL[2]); s = v.s(WL_KNL[0], WL_KNL[2])
            pen.glow(x, y, 0.35 * s, WL_NIGHTL, 120); pen.glow(x, y, 0.04 * s, '#fff6e0', 230)
        return [('kit_nightlight', (WL_KNL[0], WL_KNL[1], WL_KNL[2]), nl)]

    def spots(v, o):
        S = {}
        S['note'] = _mk_spot(v, 'note', WL_NOTE[0], WL_NOTE[1], 0.92, 'surface', "Mr. Pell's note on the counter")
        S['bread'] = _mk_spot(v, 'bread', WL_BREAD[0], WL_BREAD[1], 0.92, 'surface', 'the bread bag (twisted shut again)')
        S['counter_front'] = _mk_spot(v, 'counter_front', 3.95, 8.95, 0.0, 'stand', 'at the counter reading the note (facing it, +y)', face=(0, 1))
        S['sink'] = _mk_spot(v, 'sink', 2.7, 8.95, 0.0, 'stand', 'at the sink (Sam, water at two in the morning)', face=(0, 1))
        S['deadbolt'] = _mk_spot(v, 'deadbolt', 5.98, WL_GDOOR[0] + 0.08, 1.2, 'point', 'the deadbolt thumb-turn (kitchen side)')
        S['knob'] = _mk_spot(v, 'knob', 5.98, WL_GDOOR[0] + 0.08, 0.95, 'point', 'the knob of the door from the garage')
        S['door_in'] = _mk_spot(v, 'door_in', 5.45, 4.82, 0.0, 'stand', 'at the door from the garage, facing it (+x) (Mom checking the lock)', face=(1, 0))
        S['pantry_door'] = _mk_spot(v, 'pantry_door', 5.38, 8.15, 0.0, 'stand', 'at the pantry door (facing it, +y)', face=(0, 1))
        S['kitchen_mid'] = _mk_spot(v, 'kitchen_mid', 2.6, 5.5, 0.0, 'stand', 'the middle of the kitchen')
        S['doorway'] = _mk_spot(v, 'doorway', 1.75, 4.9, 0.0, 'stand', 'in the doorway from the entry (facing in, +x)', face=(1, 0))
        S['table_n'] = _mk_spot(v, 'table_n', 3.3, 7.05, 0.0, 'seat', 'the chair on the table\'s back side (facing -y)', face=(0, -1), seat_Y=0.45)
        S['table_s'] = _mk_spot(v, 'table_s', 3.3, 5.75, 0.0, 'seat', 'the chair on the table\'s front side (facing +y)', face=(0, 1), seat_Y=0.45)
        S['fridge'] = _mk_spot(v, 'fridge', 2.2, 8.45, 0.0, 'stand', 'at the fridge (Theo\'s drawings)', face=(-1, 0))
        return S
    return dict(name='kitchen', R=(1.4, 6.0, 3.6, 10.0), poly=_WL_KIT_POLY, H=WL_CEIL, floors=[(1.4, 6.0, 3.6, 8.6), (1.4, 4.8, 8.6, 10.0)],
                floor=dict(base='#c8c0b0', kind='checker', ink='#6a5a4a', seed=31), runs=runs,
                walls=dict(paper=WL_PAL['kit_paper'], ink='#c8b890', kind='gingham', wains=0.0, seed=33, scale=1.0, pa=40),
                ceil=dict(c='#ece6da', rects=[(1.4, 6.0, 3.6, 8.6), (1.4, 4.8, 8.6, 10.0)]), lights=lights, pieces=pieces, glows=glows, spots=spots)


def _wl_pan_cfg(o):
    """The walk-in pantry: shelves of cereal boxes on the east wall; the CRACK in the plaster behind them."""
    def lights(o):
        amb = _wl_amb(o, '#1a1e30')
        steady = []
        if o.get('nightlight', True) and o.get('tod', 'night') == 'night':
            steady.append(Lamp(5.3, 0.6, 8.0, 2.5, WL_NIGHTL, 0.5, fall=1.6))
        var = [('pantry_light', [Lamp(5.4, 2.3, 9.3, 2.8, '#ffe8c0', 1.3, (1.0, 0.5, 0.2), fall=1.4)], _kfn(o.get('pantry_light', 0.0), 812)),
               ('crack', [Lamp(WL_CRACK[0] - 0.05, WL_CRACK[2], WL_CRACK[1], 1.2, '#ffe4a8', 0.9, fall=1.8)], _kfn(o.get('crack', 0.0), 815))]
        var += _wl_var_common(o, 816, (5.4, 1.4, 9.0), (5.4, 1.45, 8.7))
        return amb, steady, var
    def east(p_, W, H):                                                         # run (6, 10) -> (6, 8.6): u = 10 - y
        cx = (10.0 - WL_CRACK[1]) * 100; cy = H - WL_CRACK[2] * 100
        pts = [(cx - 3, cy - 14), (cx - 1, cy - 8), (cx - 2.5, cy - 3), (cx + 0.5, cy + 2), (cx - 0.5, cy + 8), (cx + 1.5, cy + 14)]
        p_.line(smooth(pts, False, 0.3), 1.6, '#1a1612', 230)
        p_.line(smooth([(cx - 2.5, cy - 3), (cx - 7, cy - 1), (cx - 10, cy + 3)], False, 0.3), 0.7, '#2a241e', 180)
        p_.line(smooth([(cx + 0.5, cy + 2), (cx + 5, cy + 5)], False, 0.3), 0.6, '#2a241e', 160)
        for (dx, dy, r) in ((2, 6, 1.4), (-4, -9, 1.0), (3, -4, 0.8)): p_.fill(oval(cx + dx, cy + dy, r), '#f4f0e4', 180)
    runs = _rect_runs(WL_PAN, {'front': [(WL_PDOOR[0], 8.6, WL_PDOOR[1], 8.6, 0.0, WL_PDOOR[2])]}, None, {'east': east})
    def pieces(o):
        P = []
        def shelves(pen, v):
            for Yb in (0.42, 0.82, 1.2, 1.62, 2.0):
                draw_box(pen, v, Box(5.82, 9.3, 1.36, 0.34, Yb, Yb + 0.03, -90), {'all': '#c8b898', 'top': '#d8c8a8'}, lw=0.7)
            rng = np.random.default_rng(4)
            cols = ['#d84a3a', '#f2c23a', '#3a7ad0', '#6ab04a', '#e88a3a', '#8a4ab0']
            for i, yy in enumerate((8.8, 8.98, 9.16, 9.62, 9.8)):                 # cereal on the 1.2 shelf, a gap at the crack (y 9.42)
                draw_box(pen, v, Box(5.84, yy, 0.17, 0.07, 1.23, 1.23 + 0.29, -90), {'front': dict(fill=cols[i], art=(lambda c: lambda p_, W, H: (
                    p_.fill(oval(W / 2, H * 0.42, W * 0.3), '#fff4d8', 200), p_.fill(rect(2, H * 0.08, W - 4, H * 0.12), _darken(c, 0.3))))(cols[i])), 'all': _darken(cols[i], 0.15)}, lw=0.6)
            for i, yy in enumerate(np.linspace(8.78, 9.82, 7)):                   # cans on 0.82
                draw_box(pen, v, Box(5.86, yy, 0.08, 0.08, 0.85, 0.97, -90), {'front': cols[(i + 2) % 6], 'all': '#a8a8a8'}, lw=0.5)
            for i, yy in enumerate((8.85, 9.2, 9.55, 9.85)):                      # jars on 1.62
                draw_box(pen, v, Box(5.86, yy, 0.1, 0.1, 1.65, 1.8, -90), {'all': ('#c87a3a', '#e8c86a', '#a83a4a', '#8a6a3a')[i]}, lw=0.5)
            for i, yy in enumerate((8.9, 9.45)):                                  # flour / rice on 0.42
                draw_box(pen, v, Box(5.84, yy, 0.3, 0.16, 0.45, 0.75, -90), {'all': '#f0ead8'}, lw=0.6)
        P.append(Piece('shelves', (5.82, 1.2, 9.3), shelves, block=_r4p((5.64, 6.0, 8.62, 9.98))))
        return P
    def glows(v, o):
        kc = _kfn(o.get('crack', 0.0), 815)
        def g(pen, t):                                                          # light through the crack from the other side
            k = kc(t)
            if k < 0.01 or v.d(WL_CRACK[0], WL_CRACK[1]) < 0.15: return
            pts = [(WL_CRACK[0] - 0.003, WL_CRACK[2] + dz, WL_CRACK[1] + dy) for (dy, dz) in ((0.03, 0.14), (0.01, 0.08), (0.025, 0.03), (-0.005, -0.02), (0.005, -0.08), (-0.015, -0.14))]
            P2 = [v.p(*p) for p in pts]
            s = v.s(WL_CRACK[0], WL_CRACK[1])
            pen.line(smooth(P2, False, 0.3), max(1.0, 0.006 * s), '#fff2c8', 235 * k)
            x, y = v.p(WL_CRACK[0], WL_CRACK[2], WL_CRACK[1])
            pen.glow(x, y, 0.18 * s, '#ffd890', 90 * k)
        return [('crack_glow', (WL_CRACK[0] - 0.02, WL_CRACK[2], WL_CRACK[1]), g)]
    def spots(v, o):
        S = {}
        S['crack'] = _mk_spot(v, 'crack', WL_CRACK[0] - 0.01, WL_CRACK[1], WL_CRACK[2], 'point', 'the crack in the plaster behind the cereal (the eye on the other side)')
        S['crack_lean'] = _mk_spot(v, 'crack_lean', 5.45, WL_CRACK[1], 0.0, 'stand', 'leaning in to the crack (facing +x)', face=(1, 0))
        S['pantry_mid'] = _mk_spot(v, 'pantry_mid', 5.3, 9.1, 0.0, 'stand', 'in the pantry')
        return S
    return dict(name='pantry', R=WL_PAN, H=WL_CEIL, floor=dict(base='#b8aa94', kind='lino', ink='#7a6a54', seed=35), runs=runs,
                walls=dict(paper='#e8e2d0', ink='#c8c0a8', kind=None, wains=0.0, seed=37), ceil=dict(c='#ece6da'), lights=lights, pieces=pieces, glows=glows, spots=spots)


# ---------------------------------------------------------------------------------------------- upstairs
_WU = WL_UP                            # (upstairs floor: short name used below)


def wl_boys_door():
    return _wl_door((0.8, WL_BDOOR[1]), WL_BDOOR[1] - WL_BDOOR[0], WL_BDOOR[2], (0.0, -1.0), 1, _WU, 'right', 'left')


def wl_par_door(lock=0.0):
    """The parents' door: art_a = their room's side, with the push-button privacy lock (lock 1 = locked)."""
    return _wl_door((-0.6, WL_PARDOOR[1]), WL_PARDOOR[1] - WL_PARDOOR[0], WL_PARDOOR[2], (0.0, -1.0), -1, _WU, 'right', 'left', bolt_a=True, turn=lock)


def wl_hcl_door():
    return Door((0.8, WL_HCDOOR[1]), WL_HCDOOR[1] - WL_HCDOOR[0], WL_HCDOOR[2], (0.0, -1.0), -1, _WU, art_a=_wl_louvre_art,
                art_b=door_art('plank', 'left', bolt=False, knob=False), col='#ece6d8')


def wl_closet_door(which='sam'):
    if which == 'theo':
        return _wl_door((2.3, 4.8), 0.8, 2.0, (1.0, 0.0), -1, _WU, 'right', 'left', kind='four')
    return _wl_door((4.55, 4.8), 0.8, 2.0, (-1.0, 0.0), 1, _WU, 'left', 'right', kind='four', art_a=door_art('plank', 'right', bolt=False), art_b=door_art('four', 'left', bolt=False))


def _wl_up_light(o, seed, night_amb='#1a2034'):
    return _wl_amb(o, night_amb)


def _wl_hall_spill(o, seed):
    """Light from the hall into a bedroom through its door: the hall nightlight (warm, low) and the hall ceiling light."""
    return [('hall_light', [Lamp(0.1, _WU + 2.3, 4.6, 4.5, '#ffe8c8', 1.0, (1.0, 0.5, 0.2), fall=1.3)], _kfn(o.get('hall_light', 0.0), seed))]


def _wl_uhall_cfg(o):
    night = o.get('tod', 'night') == 'night'
    def lights(o):
        amb = _wl_amb(o, '#1a1e32')
        steady = [Lamp(kind='win', c=WL_MOON if night else '#fff0d0', k=0.7 if night else 1.2, soft=10.0, panes=_panes_y(-0.25, 0.45, _WU + 0.95, _WU + 1.9, 9.0), d=_norm3((0.0, -0.4, -1.0)))]
        if o.get('nightlight', True) and night:
            steady.append(Lamp(WL_HNL[0] + 0.1, _WU + WL_HNL[1], WL_HNL[2], 3.4, WL_NIGHTL, 1.2, (0.7, 1.0, 1.0), fall=1.4))
        var = [('hall_light', [Lamp(0.1, _WU + 2.3, 4.6, 5.5, '#ffe8c8', 1.3, (1.0, 0.5, 0.2), fall=1.3)], _kfn(o.get('hall_light', 0.0), 821)),
               ('attic', [Lamp(0.7, _WU + 1.0, 5.47, 1.6, WL_ATTIC, 0.8 * _static(o.get('attic_spill', 1.0), 1.0), fall=1.6)], _kfn(o.get('attic', 0.0), 822)),
               ('boys_moon', [Lamp(1.2, _WU + 1.0, 4.0, 2.2, WL_MOON, 0.5, fall=1.5)], _kfn(o.get('boys_moon', 1.0 if night else 0.0), 823)),
               ('par_lamp', [Lamp(-0.9, _WU + 1.0, 7.2, 2.4, WL_WARM, 0.8, fall=1.5)], _kfn(o.get('par_lamp', 0.0), 824))]
        var += _wl_var_common(o, 825, (0.1, _WU + 1.1, 4.0), (0.1, _WU + 1.4, 3.0))
        pr, pb = _pol(o)
        var += [('police_r', [Lamp(1.2, _WU + 1.6, 4.0, 3.0, WL_RED, 0.9, fall=1.4)], _kfn(pr, 826)), ('police_b', [Lamp(1.2, _WU + 1.6, 4.0, 3.0, WL_BLUE, 1.1, fall=1.4)], _kfn(pb, 827))]
        return amb, steady, var
    sw = _static(o.get('switch', 0.0))
    def west(p_, W, H):                                                         # run (-0.6, 1.6) -> (-0.6, 9): u = y - 1.6
        _light_switch(p_, (WL_SWITCH[1] - 1.6) * 100, H - WL_SWITCH[2] * 100, sw > 0.5)       # the switch that does nothing
        _light_switch(p_, (2.05 - 1.6) * 100, H - 120, True)
        x = (WL_HNL[2] - 1.6) * 100; y = H - WL_HNL[1] * 100                    # the plug-in nightlight
        p_.fill(rrect(x - 3.5, y - 5, 7, 10, 1), '#efe6d0'); p_.fill(rrect(x - 2.5, y - 4, 5, 6, 2), '#ffe6b0' if night else '#e8e0c8')
        _bu_photo(p_, (3.6 - 1.6) * 100, H - 165, 34, 44, 'kids')
    def east(p_, W, H):                                                         # run (0.8, 9) -> (0.8, 1.6): u = 9 - y
        _bu_photo(p_, (9.0 - 6.9) * 100, H - 160, 40, 30, 'grandpa')
    runs = [_run((0.8, 1.6), (-0.6, 1.6), holes=[(0.75, 1.6, -0.55, 1.6, 0.0, WL_STAIR[2])]),
            _run((-0.6, 1.6), (-0.6, 9.0), holes=[(-0.6, WL_PARDOOR[0], -0.6, WL_PARDOOR[1], 0.0, WL_PARDOOR[2])], art=west),
            _run((-0.6, 9.0), (0.8, 9.0), wins=[(-0.25, 9.0, 0.45, 9.0, 0.95, 1.9, (1, 2))]),
            _run((0.8, 9.0), (0.8, 1.6), holes=[(0.8, WL_BDOOR[0], 0.8, WL_BDOOR[1], 0.0, WL_BDOOR[2]), (0.8, WL_HCDOOR[0], 0.8, WL_HCDOOR[1], 0.0, WL_HCDOOR[2])], art=east)]
    def runner(p_, W, H):
        p_.fill(rect(30, 40, W - 60, H - 80), '#5a2e32'); p_.line(rect(36, 46, W - 72, H - 92), 1.0, '#c8a868', 160)
    def pieces(o):
        P = []
        if not callable(o.get('boys_door')): P.append(_door_piece('boys_door', wl_boys_door(), _static(o.get('boys_door', 80.0), 80.0), _WU + 1.0))
        if not callable(o.get('closet')): P.append(_door_piece('hall_closet_door', wl_hcl_door(), _static(o.get('closet', 0.0)), _WU + 1.0))
        P.append(_door_piece('par_door', wl_par_door(_static(o.get('lock', 0.0))), _static(o.get('par_door', 70.0), 70.0), _WU + 1.0))
        NP = Box(-0.35, 2.35, 0.24, 0.24, _WU, _WU + 1.05, 90)                      # the banister newel post at the stair opening
        P.append(Piece('newel', (NP.cx, _WU + 0.5, NP.cy), lambda pen, v: (draw_box(pen, v, NP, {'all': '#5a3a24', 'top': '#6a4a2e'}, lw=0.8),
                                                                        draw_box(pen, v, Box(-0.35, 1.95, 0.06, 0.8, _WU + 0.92, _WU + 0.98, 0), {'all': '#5a3a24'}, lw=0.6)), block=NP.footprint()))
        return P
    def glows(v, o):
        ka = _kfn(o.get('attic', 0.0), 822)
        cl = o.get('closet', 0.0)
        def nl(pen, t):
            if not (o.get('nightlight', True) and night) or v.d(WL_HNL[0], WL_HNL[2]) < 0.3: return
            x, y = v.p(WL_HNL[0] + 0.01, _WU + WL_HNL[1], WL_HNL[2]); s = v.s(WL_HNL[0], WL_HNL[2])
            pen.glow(x, y, 0.45 * s, WL_NIGHTL, 120); pen.glow(x, y, 0.04 * s, '#fff6e0', 230)
        def attic(pen, t):                                                      # the thin yellow line leaking round the closet door
            k = ka(t)
            if k < 0.01: return
            ang = cl(t) if callable(cl) else _static(cl)
            x = 0.8 - 0.012
            if not v.visible((x, _WU + 1.0, 5.47), (-1, 0, 0)) or v.d(x, 5.47) < 0.2: return
            s = v.s(x, 5.47)
            y0, y1, h = WL_HCDOOR[0], WL_HCDOOR[1], WL_HCDOOR[2]
            if ang < 3:
                for (A, B_) in (((x, _WU + h, y0), (x, _WU + h, y1)), ((x, _WU + 0.01, y0), (x, _WU + h, y0)), ((x, _WU + 0.01, y0 + 0.02), (x, _WU + 0.01, y1 - 0.02))):
                    pen.seg(v.p(*A), v.p(*B_), max(4.0, 0.04 * s), WL_ATTIC, 70 * k)
                    pen.seg(v.p(*A), v.p(*B_), max(1.5, 0.012 * s), '#fff0a8', 240 * k)
                for yc in list(np.arange(10.0, 200 * 0.47, 4.2)) + list(np.arange(200 * 0.53, 190.0, 4.2)):      # light through the louvres
                    Yl = _WU + h - (yc + 2.8) / 100.0
                    pen.seg(v.p(x - 0.002, Yl, y0 + 0.1), v.p(x - 0.002, Yl, y1 - 0.1), max(1.0, 0.006 * s), '#ffd870', 90 * k)
                pts = [v.p(x, _WU + 1.0, (y0 + y1) / 2)]
                pen.glow(pts[0][0], pts[0][1], 0.5 * s, WL_ATTIC, 26 * k)
            else:                                                               # open a crack: a sliver of yellow at the gap
                D = wl_hcl_door(); dx, dy = D.dir(ang)
                A = (0.8 - 0.01, _WU + 0.02, y0); B_ = (0.8 - 0.01, _WU + h, y0)
                L = (D.hinge[0] + dx * D.w, D.hinge[1] + dy * D.w)
                q = [(A[0], _WU + h, A[2]), (L[0], _WU + h, L[1]), (L[0], _WU + 0.02, L[1]), (A[0], _WU + 0.02, A[2])]
                path = v.poly3(q)
                if not path.isEmpty(): pen.fill(path, '#ffd870', 120 * k)
        return [('hall_nightlight', (WL_HNL[0], _WU + WL_HNL[1], WL_HNL[2]), nl), ('attic_line', (0.79, _WU + 1.0, 5.47), attic)]
    def spots(v, o):
        S = {}
        S['switch'] = _mk_spot(v, 'switch', WL_SWITCH[0] + 0.01, WL_SWITCH[1], _WU + WL_SWITCH[2], 'point', 'the hall switch that does nothing')
        S['switch_stand'] = _mk_spot(v, 'switch_stand', -0.2, WL_SWITCH[1], _WU, 'stand', 'at the dead switch (facing it, -x)', face=(-1, 0))
        S['closet_door'] = _mk_spot(v, 'closet_door', 0.79, 5.47, _WU + 1.0, 'point', 'the hall closet door (the line of light round it)')
        S['closet_front'] = _mk_spot(v, 'closet_front', 0.35, 5.47, _WU, 'stand', 'in front of the hall closet (facing it, +x)', face=(1, 0))
        S['boys_door'] = _mk_spot(v, 'boys_door', 0.45, 4.02, _WU, 'stand', "in the hall at the boys' door (facing it, +x)", face=(1, 0))
        S['par_door'] = _mk_spot(v, 'par_door', -0.25, 7.22, _WU, 'stand', "in the hall at the parents' door (facing it, -x)", face=(-1, 0))
        S['hall_mid'] = _mk_spot(v, 'hall_mid', 0.1, 5.8, _WU, 'stand', 'the middle of the hall (walking it: carrying Theo)', face=(0, 1))
        S['stair_top'] = _mk_spot(v, 'stair_top', 0.1, 2.2, _WU, 'stand', 'at the top of the stairs')
        S['ceiling'] = _mk_spot(v, 'ceiling', -0.1, 5.0, _WU + WL_UH, 'point', 'the ceiling over the switch ("Off.")')
        return S
    rug = lambda p_, W, H: runner(p_, W, H)
    return dict(name='uhall', R=WL_UHALL, Y0=_WU, H=WL_UH, floor=dict(base=WL_PAL['floor'], kind='boards', ink='#4a2e1a', seed=51, art=rug), runs=runs,
                walls=dict(paper=WL_PAL['hall_paper'], ink=WL_PAL['hall_ink'], kind='ditsy', wains=0.0, seed=53, scale=0.9, pa=60),
                ceil=dict(c='#ece6da'), lights=lights, pieces=pieces, glows=glows, spots=spots)


def _wl_closet_cfg(which, o):
    """Theo's / Sam's closet (0.75 m deep): rod, a few shirts, the shelf. Sam's back wall (y 5.55) is a panel that SLIDES
    west (o['slide'] 0..1: the cavity behind it, dark, studs); o['hole']: the ragged hole the officers made in its west
    wall into the dead space."""
    R = WL_SCL if which == 'sam' else WL_TCL
    sam = which == 'sam'
    slide = _static(o.get('slide', 0.0)) if sam else 0.0
    def lights(o):
        amb = _wl_amb(o, '#141a2c')
        var = _wl_var_common(o, 840 if sam else 845, ((R[0] + R[1]) / 2, _WU + 1.2, 4.4), ((R[0] + R[1]) / 2, _WU + 1.4, 4.0))
        var.append(('moon_in', [Lamp((R[0] + R[1]) / 2, _WU + 1.0, 4.5, 1.6, WL_MOON, 0.6, fall=1.6)], _kfn(o.get('moon_in', 1.0 if o.get('tod', 'night') == 'night' else 0.0), 848)))
        return amb, [], var
    dx0, dx1 = (R[0] + 0.1, R[1] - 0.1)
    holes = {'front': [(dx0, 4.8, dx1, 4.8, 0.0, 2.0)]}
    runs = _rect_runs(R, holes)
    def shell_x(pen, v, o):
        rod_y = R[3] - 0.3
        A = (R[0] + 0.02, _WU + 1.75, rod_y); B_ = (R[1] - 0.02, _WU + 1.75, rod_y)
        if v.d(A[0], A[2]) > 0.2 and v.d(B_[0], B_[2]) > 0.2: pen.seg(v.p(*A), v.p(*B_), max(1.0, 0.02 * v.s(A[0], A[2])), '#b8b8b8')
        draw_box(pen, v, Box((R[0] + R[1]) / 2, R[3] - 0.17, R[1] - R[0], 0.34, _WU + 1.9, _WU + 1.93, 0), {'all': '#e0d8c8'}, lw=0.6)
        cols = ['#c83a3a', '#3a6ab0', '#e8e0c8', '#4a8a4a'] if not sam else ['#2a3a5a', '#7a7a7a', '#c8a03a']
        for i, c in enumerate(cols):
            x = (R[1] - 0.1 - i * 0.07) if (sam and o.get('hole')) else (R[0] + 0.18 + i * 0.16)      # shoved aside when the officers cut through
            sh = Box(x, rod_y, 0.42, 0.04, _WU + 1.05, _WU + 1.72, 90)
            draw_box(pen, v, sh, {'all': c}, lw=0.6)
        if sam and slide > 0.01:                                                # the back wall slid west: the cavity behind
            gx0, gx1 = R[1] - 0.92 * slide, R[1] - 0.02
            q = [(gx0, _WU + 2.0, R[3] - 0.005), (gx1, _WU + 2.0, R[3] - 0.005), (gx1, _WU + 0.02, R[3] - 0.005), (gx0, _WU + 0.02, R[3] - 0.005)]
            path = v.poly3(q)
            if not path.isEmpty():
                pen.fill(path, '#050505')
                for k in range(3):
                    sx = gx0 + (gx1 - gx0) * (k + 0.5) / 3
                    pen.seg(v.p(sx, _WU + 2.0, R[3] + 0.3), v.p(sx, _WU + 0.02, R[3] + 0.3), max(1.0, 0.03 * v.s(sx, R[3])), '#2a2018', 200)
                pen.line(path, 1.0)
            F = Face((gx0 - 0.9, _WU + 2.02, R[3] - 0.012), (1, 0, 0), (0, -1, 0), 90.0, 202.0, (0, 0, -1), 'wall')
            draw_face(pen, v, F, lambda p_, W, H: (p_.texture(rect(0, 0, W, H), 'paper', 0.3, 'multiply', 0.8), p_.line(rect(1, 1, W - 2, H - 2), 0.8, '#000000', 120)),
                      '#d8d4c8', ao=False, lw=0.8)
        if sam and o.get('hole'):                                               # the officers' hole in the west wall (into the dead space)
            pts = [(R[0] + 0.005, _WU + Y_, y_) for (y_, Y_) in ((5.08, 0.35), (5.12, 1.5), (5.26, 1.68), (5.42, 1.45), (5.5, 0.9), (5.46, 0.3), (5.28, 0.15))]
            path = v.poly3(pts)
            if not path.isEmpty():
                pen.fill(path, '#0a0806'); pen.fill(path, '#8a9ab8', 60)
                pen.line(path, max(2.0, 0.025 * v.s(R[0], 5.2)), '#f4f0e8', 230); pen.line(path, 1.0, '#5a5448', 220)
    def spots(v, o):
        c = ((R[0] + R[1]) / 2, (R[2] + R[3]) / 2)
        S = {('sam' if sam else 'theo') + '_closet_in': _mk_spot(v, ('sam' if sam else 'theo') + '_closet_in', c[0], c[1] + 0.05, _WU, 'stand',
                                                              ("inside Sam's closet (he goes in; the back wall slides)" if sam else "inside Theo's closet"), face=(0, 1))}
        if sam: S['slide_panel'] = _mk_spot(v, 'slide_panel', R[1] - 0.45, R[3] - 0.02, _WU + 1.0, 'point', "Sam's closet back wall (it slides)")
        return S
    return dict(name=which + '_closet', R=R, Y0=_WU, H=2.1, floor=dict(base='#8a6a48', kind='boards', ink='#4a2e1a', seed=61), runs=runs,
                walls=dict(paper='#e4dccc', ink=None, kind=None, wains=0.0, seed=63), ceil=dict(c='#e0d8cc'), lights=lights, spots=spots, shell_x=shell_x)


def _wl_hcl_cfg(o):
    """The hall closet: coats, a vacuum, boxes on the shelf, and the sealed attic HATCH in its ceiling (painted shut; o['attic']
    lights the thin yellow line round its edge)."""
    def lights(o):
        amb = _wl_amb(o, '#141828')
        var = [('attic', [Lamp((WL_HATCH[0] + WL_HATCH[1]) / 2, _WU + 2.3, (WL_HATCH[2] + WL_HATCH[3]) / 2, 1.8, WL_ATTIC, 1.0, (0.2, 1.0, 1.0), fall=1.5)], _kfn(o.get('attic', 0.0), 822))]
        var += _wl_var_common(o, 850, (0.6, _WU + 1.2, 5.47), (0.4, _WU + 1.5, 5.47))
        return amb, [], var
    runs = _rect_runs(WL_HCL, {'west': [(0.8, WL_HCDOOR[0], 0.8, WL_HCDOOR[1], 0.0, WL_HCDOOR[2])]})
    def hatch_art(p_, W, H):
        hx0, hx1, hy0, hy1 = ((WL_HATCH[0] - WL_HCL[0]) * 100, (WL_HATCH[1] - WL_HCL[0]) * 100, (WL_HATCH[2] - WL_HCL[2]) * 100, (WL_HATCH[3] - WL_HCL[2]) * 100)
        p_.fill(rect(hx0 - 6, hy0 - 6, hx1 - hx0 + 12, hy1 - hy0 + 12), '#e8e2d4'); p_.line(rect(hx0 - 6, hy0 - 6, hx1 - hx0 + 12, hy1 - hy0 + 12), 0.8)
        p_.fill(rect(hx0, hy0, hx1 - hx0, hy1 - hy0), '#d8d2c4'); p_.line(rect(hx0, hy0, hx1 - hx0, hy1 - hy0), 1.2, '#2a2620', 200)
        for k in range(5): p_.seg((hx0 + 8 + k * 12, hy0 + 3), (hx0 + 4 + k * 12, hy0 - 4), 0.6, '#8a8070', 150)   # old paint over the seam
    def shell_x(pen, v, o):
        A = (0.85, _WU + 1.75, 5.9); B_ = (2.15, _WU + 1.75, 5.9)
        if v.d(A[0], A[2]) > 0.2: pen.seg(v.p(*A), v.p(*B_), max(1.0, 0.02 * v.s(A[0], A[2])), '#b8b8b8')
        for i, c in enumerate(('#3a3a4a', '#7a3a2a', '#4a5a3a')):
            draw_box(pen, v, Box(1.15 + i * 0.22, 5.9, 0.06, 0.5, _WU + 0.75, _WU + 1.72, 0), {'all': c}, lw=0.6)
        draw_box(pen, v, Box(1.5, 6.03, 1.4, 0.34, _WU + 1.9, _WU + 1.93, 0), {'all': '#e0d8c8'}, lw=0.6)
        _wl_boxes(pen, v, [(1.2, 6.03, 0.4, 0.3, 0.28, 0, 'XMAS', 1.93), (1.75, 6.03, 0.45, 0.3, 0.22, 0, '', 1.93)], _WU)
    def glows(v, o):
        ka = _kfn(o.get('attic', 0.0), 822)
        def g(pen, t):
            k = ka(t)
            if k < 0.01: return
            Yc = _WU + WL_UH - 0.004
            q = [(WL_HATCH[0], Yc, WL_HATCH[2]), (WL_HATCH[1], Yc, WL_HATCH[2]), (WL_HATCH[1], Yc, WL_HATCH[3]), (WL_HATCH[0], Yc, WL_HATCH[3])]
            if v.d((WL_HATCH[0] + WL_HATCH[1]) / 2, (WL_HATCH[2] + WL_HATCH[3]) / 2) < 0.15: return
            s = v.s((WL_HATCH[0] + WL_HATCH[1]) / 2, (WL_HATCH[2] + WL_HATCH[3]) / 2)
            path = v.poly3(q)
            if path.isEmpty(): return
            pen.line(path, max(1.2, 0.008 * s), '#fff0a0', 240 * k)
            pen.line(path, max(3.0, 0.03 * s), WL_ATTIC, 80 * k, blur=0.01 * s)
        return [('hatch_line', ((WL_HATCH[0] + WL_HATCH[1]) / 2, _WU + WL_UH, (WL_HATCH[2] + WL_HATCH[3]) / 2), g)]
    def spots(v, o):
        return {'hatch': _mk_spot(v, 'hatch', (WL_HATCH[0] + WL_HATCH[1]) / 2, (WL_HATCH[2] + WL_HATCH[3]) / 2, _WU + WL_UH, 'point', 'the sealed attic hatch'),
                'hcl_in': _mk_spot(v, 'hcl_in', 1.3, 5.5, _WU, 'stand', 'inside the hall closet (under the hatch)')}
    return dict(name='hall_closet', R=WL_HCL, Y0=_WU, H=WL_UH, floor=dict(base='#8a6a48', kind='boards', ink='#4a2e1a', seed=65), runs=runs,
                walls=dict(paper='#e4dccc', ink=None, kind=None, wains=0.0, seed=67), ceil=dict(c='#e8e2d4', art=hatch_art),
                lights=lights, spots=spots, shell_x=shell_x, glows=glows)


def _wl_boys_cfg(o):
    night = o.get('tod', 'night') == 'night'
    wpan = _panes_y(WL_BWIN[0], WL_BWIN[1], _WU + WL_BWIN[2], _WU + WL_BWIN[3], 0.0)
    def lights(o):
        amb = _wl_amb(o, '#1a2036')
        steady = [Lamp(kind='win', c=WL_MOON if night else '#fff0d0', k=(1.7 * _static(o.get('moon', 1.0), 1.0)) if night else 1.5, soft=10.0, panes=wpan, d=_norm3((-0.3, -0.5, 1.0)))]
        if o.get('nightlight', True) and night:                                # the hall nightlight's warm spill through the door
            steady.append(Lamp(0.3, _WU + 0.4, 4.0, 2.6, WL_NIGHTL, 0.7, (0.6, 1.0, 1.0), fall=1.5))
        var = [('ceil', [Lamp(3.4, _WU + 2.35, 2.4, 6.0, '#fff0d8', 1.2, (1.0, 0.5, 0.2), fall=1.3)], _kfn(o.get('ceil', 0.0), 831)),
               ('lamp', [Lamp(5.6, _WU + 0.95, 2.35, 3.0, WL_WARM, 1.2, (1.0, 0.6, 0.3), fall=1.4)], _kfn(o.get('lamp', 0.0), 832))]
        var += _wl_hall_spill(o, 833)
        var += _wl_var_common(o, 834, (3.4, _WU + 1.1, 2.4), (1.4, _WU + 1.5, 3.9), police_panes=wpan, police_d=(0.15, 0.65, 1.0))
        return amb, steady, var
    def east(p_, W, H):                                                         # run (6, 4.8) -> (6, 0): u = 4.8 - y (the wall by Sam's bed)
        p_.fill(rect((4.8 - 1.6) * 100 - 30, H - 205, 60, 80), '#1a2a4a'); p_.line(rect((4.8 - 1.6) * 100 - 30, H - 205, 60, 80), 0.8)   # a space poster
        for (dx, dy, r) in ((-12, -40, 6), (10, -20, 3), (-4, 0, 2)): p_.fill(oval((4.8 - 1.6) * 100 + dx, H - 165 + dy, r), '#f4e8b0')
    def west(p_, W, H):                                                         # run (0.8, 0) -> (0.8, 4.8): u = y
        _bu_photo(p_, 1.1 * 100, H - 170, 52, 68, 'dino', frame='#4a8ad8')
        _light_switch(p_, (WL_BDOOR[0] - 0.12) * 100, H - 120, True)
    def back(p_, W, H):                                                         # run (0.8, 4.8) -> (6, 4.8): u = x - 0.8
        btext(p_, 'THEO', (1.55 - 0.8) * 100, H - 190, 'kid', 16, '#4aa06a', 240, 'center')
    wins = {'front': [(WL_BWIN[0], 0.0, WL_BWIN[1], 0.0, WL_BWIN[2], WL_BWIN[3], (2, 2))]}
    holes = {'west': [(0.8, WL_BDOOR[0], 0.8, WL_BDOOR[1], 0.0, WL_BDOOR[2])],
             'back': [(2.3, 4.8, 3.1, 4.8, 0.0, 2.0), (3.75, 4.8, 4.55, 4.8, 0.0, 2.0)]}
    runs = _rect_runs(WL_BOYS, holes, wins, {'east': east, 'west': west, 'back': back})
    rug = _bu_rug_art(WL_BOYS[0], WL_BOYS[3], 3.4, 2.3, 1.1, 0.8, ('#4aa06a', '#e8d870', '#4a8ad8', '#f4f0e0'))
    def floor_art(p_, W, H):
        rug(p_, W, H)
        _wl_vent_art(p_, (WL_VENT_B[0] - WL_BOYS[0]) * 100, (WL_BOYS[3] - WL_VENT_B[1]) * 100)
    def pieces(o):
        tb = bu_bed_parts(WL_TBED, _WU, o.get('theo_bed', 'made'), '#e8e4dc', quilt_c='#3a6a9a', dino=True)
        sb = bu_bed_parts(WL_SBED, _WU, o.get('sam_bed', 'made'), '#6a4428', ('#3a4a6a', '#8a9ab0', '#5a6a4a', '#c8b898'), '#4a5a7a')
        P = [Piece('theo_bed', (WL_TBED.cx, _WU + 0.4, WL_TBED.cy), lambda pen, v: draw_parts(pen, v, tb), block=WL_TBED.footprint()),
             Piece('sam_bed', (WL_SBED.cx, _WU + 0.4, WL_SBED.cy), lambda pen, v: draw_parts(pen, v, sb), block=WL_SBED.footprint())]
        NS = Box(5.6, 2.35, 0.4, 0.36, _WU, _WU + 0.55, -90)
        lk = _static(o.get('lamp', 0.0))
        P.append(Piece('nightstand', (NS.cx, _WU + 0.3, NS.cy), lambda pen, v: (draw_box(pen, v, NS, {'all': '#6a4428', 'front': dict(fill='#6a4428', art=lambda p_, W, H: p_.line(rect(4, 6, W - 8, H * 0.38), 0.8, '#000000', 110))}),
                                                                             dr_table_lamp(pen, v, 5.6, 2.42, _WU + 0.55, lk, '#f2e2c8', '#4a8ad8', 0.4)), block=NS.footprint()))
        P.append(_wl_fan_piece('fan', (WL_BWIN[0] + WL_BWIN[1]) / 2, 0.1, _WU + WL_BWIN[2], 180, o))
        TB = Box(1.2, 4.45, 0.7, 0.4, _WU, _WU + 0.45, 180)
        P.append(Piece('toybox', (TB.cx, _WU + 0.25, TB.cy), lambda pen, v: draw_box(pen, v, TB, {'all': '#4a8ad8', 'top': '#3a7ac8', 'front': dict(fill='#4a8ad8', art=lambda p_, W, H: (
            btext(p_, 'TOYS', W / 2, H * 0.6, 'kid', H * 0.35, '#fff6dc', 240, 'center'), _dino_sil(p_, W * 0.82, H * 0.6, H * 0.3, 2, '#e8d870')))}), block=TB.footprint()))
        if o.get('boxes', True):
            P.append(Piece('boxes', (5.55, _WU + 0.3, 4.3), lambda pen, v: _wl_boxes(pen, v, [(5.55, 4.3, 0.55, 0.45, 0.42, -8, 'SAM', 0.0)], _WU), block=_r4p((5.25, 5.85, 4.05, 4.55))))
        if not callable(o.get('door')): P.append(_door_piece('boys_door', wl_boys_door(), _static(o.get('door', 80.0), 80.0), _WU + 1.0))
        P.append(_door_piece('theo_closet_door', wl_closet_door('theo'), _static(o.get('theo_closet', 0.0)), _WU + 1.0))
        if not callable(o.get('sam_closet')): P.append(_door_piece('sam_closet_door', wl_closet_door('sam'), _static(o.get('sam_closet', 0.0)), _WU + 1.0))
        if o.get('marks', True):
            F, art = _wl_marks_face(o.get('fresh', True))
            P.append(Piece('pencil_marks', (WL_MARKS[0] + 0.02, _WU + 1.4, WL_MARKS[1] - 0.04), lambda pen, v: draw_face(pen, v, F, art, '#f0ece2', ao=False, lw=0.5)))
        return P
    def spots(v, o):
        S = {}
        S['theo_bed'] = _mk_spot(v, 'theo_bed', WL_TBED.cx, WL_TBED.cy - 0.1, _WU + 0.5, 'lie', "Theo's bed (head at the front wall, under the window side)")
        S['sam_bed'] = _mk_spot(v, 'sam_bed', WL_SBED.cx, WL_SBED.cy - 0.1, _WU + 0.5, 'lie', "Sam's bed (head at the front; the wall by his bed on his right)")
        S['sam_pillow'] = _mk_spot(v, 'sam_pillow', WL_SBED.cx, 0.35, _WU + 0.62, 'point', "Sam's head on the pillow")
        S['theo_pillow'] = _mk_spot(v, 'theo_pillow', WL_TBED.cx, 0.35, _WU + 0.62, 'point', "Theo's head on the pillow")
        S['theo_kneel'] = _mk_spot(v, 'theo_kneel', 2.15, 0.95, _WU, 'stand', "kneeling beside Theo's bed, facing it (-x): tucking him in", face=(-1, 0))
        S['sam_edge'] = _mk_spot(v, 'sam_edge', 4.85, 1.3, _WU, 'seat', "sitting on the edge of Sam's bed (facing -x)", face=(-1, 0), seat_Y=0.5)
        S['doorway'] = _mk_spot(v, 'doorway', 0.78, 4.02, _WU, 'stand', 'in the doorway (facing in, +x): "Dad" watching us sleep', face=(1, 0))
        S['door_in'] = _mk_spot(v, 'door_in', 1.35, 3.9, _WU, 'stand', 'one step into the room (the moonlight hits his face)', face=(1, -0.4))
        S['sam_closet'] = _mk_spot(v, 'sam_closet', 4.15, 4.4, _WU, 'stand', "in front of Sam's closet (facing it, +y)", face=(0, 1))
        S['theo_closet'] = _mk_spot(v, 'theo_closet', 2.7, 4.4, _WU, 'stand', "in front of Theo's closet (facing it, +y)", face=(0, 1))
        S['sam_wall'] = _mk_spot(v, 'sam_wall', 5.99, 1.0, _WU + 0.75, 'point', "the wall by Sam's bed (the voice inside it)")
        S['window'] = _mk_spot(v, 'window', 3.4, 0.45, _WU, 'stand', 'at the window (facing out, -y)', face=(0, -1))
        S['vent'] = _mk_spot(v, 'vent', WL_VENT_B[0], WL_VENT_B[1], _WU, 'surface', "the boys' floor vent")
        S['marks'] = _mk_spot(v, 'marks', WL_MARKS[0] + 0.02, WL_MARKS[1] - 0.04, _WU + 1.5, 'point', 'the pencil marks on the doorframe')
        S['marks_fresh'] = _mk_spot(v, 'marks_fresh', WL_MARKS[0] + 0.02, WL_MARKS[1] - 0.04, _WU + 1.86, 'point', 'the fresh mark, dated last week')
        S['room_mid'] = _mk_spot(v, 'room_mid', 3.3, 2.6, _WU, 'stand', 'the middle of the room')
        return S
    return dict(name='boys', R=WL_BOYS, Y0=_WU, H=WL_UH, floor=dict(base='#9a6a44', kind='boards', ink='#4a2e1a', seed=43, art=floor_art), runs=runs,
                walls=dict(paper=WL_PAL['boys_paper'], ink=WL_PAL['boys_ink'], kind='stars', wains=0.0, seed=47, scale=1.0, pa=110),
                ceil=dict(c='#eef2f4'), lights=lights, pieces=pieces, spots=spots)


def _wl_par_cfg(o):
    night = o.get('tod', 'night') == 'night'
    wpan = _panes_x(4.75, 5.55, _WU + 0.85, _WU + 2.0, -6.0)
    def lights(o):
        amb = _wl_amb(o, '#1a1e32')
        steady = [Lamp(kind='win', c=WL_MOON if night else '#fff0d0', k=0.8 if night else 1.4, soft=10.0, panes=_panes_y(WL_PWIN[0], WL_PWIN[1], _WU + WL_PWIN[2], _WU + WL_PWIN[3], 9.0),
                       d=_norm3((0.3, -0.5, -1.0))),
                  Lamp(kind='win', c=WL_MOON if night else '#fff0d0', k=0.6 if night else 1.2, soft=10.0, panes=wpan, d=_norm3((1.0, -0.45, 0.2)))]
        var = [('lamp', [Lamp(-5.7, _WU + 0.95, 8.1, 3.2, WL_WARM, 1.3, (1.0, 0.6, 0.3), fall=1.4)], _kfn(o.get('lamp', 0.0), 861)),
               ('ceil', [Lamp(-3.3, _WU + 2.35, 6.8, 6.0, '#fff0d8', 1.2, (1.0, 0.5, 0.2), fall=1.3)], _kfn(o.get('ceil', 0.0), 862))]
        var += _wl_hall_spill(o, 863)
        var += _wl_var_common(o, 864, (-4.4, _WU + 1.0, 6.5), (-1.0, _WU + 1.5, 7.2), police_panes=wpan, police_d=(1.0, 0.7, 0.3))
        return amb, steady, var
    def front(p_, W, H):                                                        # run (-0.6, 4.6) -> (-6, 4.6): u = -0.6 - x
        _bu_photo(p_, (-0.6 + 2.4) * 100, H - 165, 50, 38, 'kids')
    def back(p_, W, H):                                                         # run (-6, 9) -> (-0.6, 9): u = x + 6
        _bu_photo(p_, (-2.4 + 6.0) * 100, H - 175, 28, 36, 'grandpa')
    wins = {'back': [(WL_PWIN[0], 9.0, WL_PWIN[1], 9.0, WL_PWIN[2], WL_PWIN[3], (2, 2))], 'west': [(-6.0, 4.75, -6.0, 5.55, 0.85, 2.0, (1, 2))]}
    holes = {'east': [(-0.6, WL_PARDOOR[0], -0.6, WL_PARDOOR[1], 0.0, WL_PARDOOR[2])]}
    runs = _rect_runs(WL_PAR, holes, wins, {'front': front, 'back': back})
    rug = _bu_rug_art(WL_PAR[0], WL_PAR[3], -3.6, 6.8, 1.2, 1.4, ('#7a4a5a', '#c8a888', '#5a6a7a', '#e8d8c0', '#8a5a4a'))
    def floor_art(p_, W, H):
        rug(p_, W, H)
        _wl_vent_art(p_, (WL_VENT_P[0] - WL_PAR[0]) * 100, (WL_PAR[3] - WL_VENT_P[1]) * 100)
    def pieces(o):
        bp = bu_bed_parts(WL_PBED, _WU, o.get('bed', 'turned'), '#5a3a24', ('#8a4a5a', '#e8d8b0', '#5a6a8a', '#c8a888', '#7a8a5a'), '#6a4a5a')
        P = [Piece('bed', (WL_PBED.cx, _WU + 0.4, WL_PBED.cy), lambda pen, v: draw_parts(pen, v, bp), block=WL_PBED.footprint())]
        NS = WL_NSTAND
        lk = _static(o.get('lamp', 0.0))
        def ns(pen, v):
            draw_box(pen, v, NS, {'all': '#5a3a24', 'front': dict(fill='#5a3a24', art=lambda p_, W, H: p_.line(rect(4, 6, W - 8, H * 0.38), 0.8, '#000000', 110))})
            dr_table_lamp(pen, v, NS.cx, NS.cy + 0.08, _WU + 0.58, lk, '#f2e2c8', '#8a6a8a', 0.42)
            if o.get('phone_on_stand', True):
                draw_box(pen, v, Box(NS.cx + 0.02, NS.cy - 0.1, 0.075, 0.15, _WU + 0.58, _WU + 0.59, 90), {'all': '#16161c', 'top': '#2a3450' if _static(o.get('phone', 0.0)) > 0.1 else '#16161c'}, lw=0.5)
        P.append(Piece('nightstand', (NS.cx, _WU + 0.3, NS.cy), ns, block=NS.footprint()))
        DS = WL_DRESSER
        P.append(Piece('dresser', (DS.cx, _WU + 0.4, DS.cy), lambda pen, v: (draw_box(pen, v, DS, {'all': '#6a4428', 'top': '#7a5434', 'front': dict(fill='#6a4428', art=lambda p_, W, H: [
            (p_.line(rect(4, 6 + k * (H - 10) / 3, W - 8, (H - 10) / 3 - 4), 0.9, '#000000', 110), p_.fill(oval(W * 0.3, 6 + k * (H - 10) / 3 + (H - 10) / 6, 1.6), '#c8a858'),
             p_.fill(oval(W * 0.7, 6 + k * (H - 10) / 3 + (H - 10) / 6, 1.6), '#c8a858')) for k in range(3)])}), _dresser_things(pen, v, DS)), block=DS.footprint()))
        P.append(_wl_fan_piece('fan', (WL_PWIN[0] + WL_PWIN[1]) / 2, 8.9, _WU + WL_PWIN[2], 0, o))
        if not callable(o.get('door')): P.append(_door_piece('par_door', wl_par_door(_static(o.get('lock', 0.0))), _static(o.get('door', 0.0)), _WU + 1.0))
        return P
    def spots(v, o):
        S = {}
        S['bed_dad'] = _mk_spot(v, 'bed_dad', -4.85, 6.4, _WU + 0.5, 'lie', "Dad asleep (snoring) on the bed's front half")
        S['bed_mom'] = _mk_spot(v, 'bed_mom', -4.85, 7.2, _WU + 0.5, 'lie', "Mom on the bed's back half (nearest her phone)")
        S['bed_edge'] = _mk_spot(v, 'bed_edge', -3.75, 6.8, _WU, 'seat', 'sitting on the foot of the bed (facing +x, the door)', face=(1, 0), seat_Y=0.5)
        S['bed_huddle'] = _mk_spot(v, 'bed_huddle', -4.4, 7.4, _WU + 0.5, 'seat', 'the family huddled on the bed (facing the door)', face=(1, 0), seat_Y=0.0)
        S['door_in'] = _mk_spot(v, 'door_in', -1.05, 7.22, _WU, 'stand', 'just inside the door, facing it (+x): shut it, lock it', face=(1, 0))
        S['lock'] = _mk_spot(v, 'lock', -0.62, WL_PARDOOR[0] + 0.07, _WU + 0.95, 'point', 'the push-button lock on the knob (room side)')
        S['phone'] = _mk_spot(v, 'phone', WL_NSTAND.cx + 0.02, WL_NSTAND.cy - 0.1, _WU + 0.59, 'surface', "Mom's phone on the nightstand")
        S['vent'] = _mk_spot(v, 'vent', WL_VENT_P[0], WL_VENT_P[1], _WU, 'surface', 'the floor vent by the front wall (it rattles; the voice sings through it)')
        S['dresser'] = _mk_spot(v, 'dresser', WL_DRESSER.cx, 8.98, _WU + 0.6, 'point', 'the wall behind the dresser (scratching)')
        S['headboard'] = _mk_spot(v, 'headboard', -5.99, 6.8, _WU + 0.8, 'point', 'the wall behind the headboard (scratching)')
        S['room_mid'] = _mk_spot(v, 'room_mid', -2.6, 6.6, _WU, 'stand', 'the middle of the room')
        S['window'] = _mk_spot(v, 'window', -5.6, 5.15, _WU, 'stand', 'at the side window (police lights)', face=(-1, 0))
        return S
    return dict(name='parents', R=WL_PAR, Y0=_WU, H=WL_UH, floor=dict(base=WL_PAL['floor'], kind='boards', ink='#4a2e1a', seed=71, art=floor_art), runs=runs,
                walls=dict(paper=WL_PAL['par_paper'], ink=WL_PAL['par_ink'], kind='roses', wains=0.0, seed=73, scale=0.9, pa=50),
                ceil=dict(c='#ece4d8'), lights=lights, pieces=pieces, spots=spots)


def _wl_dead_cfg(o):
    """The dead space: raw studs, lath and plaster keys, a dusty subfloor; his sleeping bag along it, Dad's flashlight, our
    bread bags folded in a neat pile, four empty yogurt cups stacked, and at the far end the box from our garage that says
    GONE FOREVER, lid off, empty. Lit by an officer's flashlight (o['flash'], default on) from the hole."""
    def lights(o):
        amb = '#0c0c12'
        var = [('flash', [Lamp(*o.get('flash_at', (3.42, _WU + 1.35, 4.95)), R=5.0, c='#fff4dc', k=2.2, w=(1.0, 1.0, 0.7), fall=1.25)], _kfn(o.get('flash', 1.0), 871)),
               ('dad_flash', [Lamp(3.4, _WU + 0.2, 6.2, 1.8, '#fff0c8', 1.2, fall=1.5)], _kfn(o.get('dad_flash', 0.0), 872))]
        pr, pb = _pol(o)
        var += [('police_r', [Lamp(3.6, _WU + 1.2, 4.9, 2.5, WL_RED, 0.6, fall=1.5)], _kfn(pr, 873)), ('police_b', [Lamp(3.6, _WU + 1.2, 4.9, 2.5, WL_BLUE, 0.7, fall=1.5)], _kfn(pb, 874))]
        return amb, [], var
    def studs(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'grunge', 0.6, 'overlay', 1.2)
        for k in range(int(H / 5)): p_.fill(rect(0, k * 5, W, 3.2), '#8a6a48', 160)            # lath strips
        rng = np.random.default_rng(int(W))
        for i in range(int(W * H / 500)):                                                         # plaster keys squeezed through
            p_.fill(oval(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.5, 1.3), rng.uniform(0.4, 0.8)), '#d8d0bc', 120)
        for k in range(int(W / 40) + 1): p_.fill(rect(k * 40 - 2.5, 0, 5, H), '#7a5a3a', 235)     # studs
    def east(p_, W, H):                                                                           # run (3.65, 7.2) -> (3.65, 4.8): u = 7.2 - y
        studs(p_, W, H)
        if o.get('hole', True):                                                                   # the hole from Sam's closet
            cx = (7.2 - 5.3) * 100; pts = [(cx - 20, H - 40), (cx - 14, H - 62), (cx - 24, H - 96), (cx - 12, H - 128), (cx + 2, H - 122), (cx + 10, H - 140), (cx + 22, H - 104),
                                           (cx + 16, H - 78), (cx + 24, H - 50), (cx + 6, H - 34)]
            p_.fill(poly(pts), '#1a1e2a'); p_.line(poly(pts), 2.4, '#f0ece2', 235); p_.line(poly(pts), 0.8, '#6a6458', 200)
    runs = [_run((3.65, 7.2), (3.65, 4.8), art=east), _run((3.2, 4.8), (3.2, 7.2), art=studs), _run((3.2, 7.2), (3.65, 7.2), art=studs), _run((3.65, 4.8), (3.2, 4.8), art=studs)]
    def ceil_art(p_, W, H):
        p_.fill(rect(0, 0, W, H), '#16120e')
        for k in range(int(H / 40) + 1): p_.fill(rect(0, k * 40, W, 6), '#4a3a28', 220)
    def pieces(o):
        P = []
        def bag(pen, v):
            B = Box(3.42, 5.9, 0.4, 1.6, _WU, _WU + 0.09, 0)
            box_extrude(pen, v, B, -0.2, 0.2, -0.8, 0.8, _WU, _WU + 0.1, lambda W, H: rounded_rect_pts(W, H, 4.0, 1.0, bulge=2.0), '#a8502e', '#7a3420',
                        lambda p_, W, H: (p_.texture(rect(0, 0, W, H), 'fabric', 0.6, 'overlay', 0.8), p_.seg((W * 0.85, 0), (W * 0.85, H), 1.0, '#c8c8b0', 160)))
            draw_box(pen, v, Box(3.42, 6.55, 0.3, 0.2, _WU + 0.08, _WU + 0.2, 0), {'all': '#6a5a4a'}, lw=0.6)        # a rolled-up sweater pillow at the far end
        P.append(Piece('sleeping_bag', (3.42, _WU + 0.05, 5.9), bag))
        def flash(pen, v):                                                                         # Dad's flashlight, lying on the bag
            B = Box(3.36, 5.35, 0.06, 0.26, _WU + 0.1, _WU + 0.16, 12)
            draw_box(pen, v, B, {'all': '#1a1a1a', 'top': '#2a2a2a'}, lw=0.6)
            draw_box(pen, v, sub(B, -0.04, 0.04, 0.13, 0.17, _WU + 0.095, _WU + 0.165), {'all': '#e8c020', 'front': '#f4f0d8'}, lw=0.5)
        P.append(Piece('flashlight', (3.36, _WU + 0.12, 5.35), flash))
        def bags(pen, v):                                                                          # our bread bags, folded in a neat pile
            for k in range(6):
                draw_box(pen, v, Box(3.32, 6.74 - 0.003 * k, 0.2, 0.14, _WU + 0.005 + k * 0.012, _WU + 0.015 + k * 0.012, 4 * (k % 2) - 2),
                         {'top': dict(fill='#f2f4f8', art=lambda p_, W, H: (p_.fill(rect(W * 0.15, H * 0.3, W * 0.5, H * 0.4), ('#d84a3a', '#3a7ad0')[k % 2], 180))), 'all': '#e8ecf2'}, lw=0.4)
            for k in range(4):                                                                     # four yogurt cups, stacked
                c = Box(3.55, 6.74, 0.07, 0.07, _WU + k * 0.025, _WU + 0.08 + k * 0.025, 0)
                draw_box(pen, v, c, {'all': '#f4f0e8', 'top': '#e8d0e0'}, lw=0.4)
        P.append(Piece('bread_bags', (3.4, _WU + 0.05, 6.74), bags))
        def gone(pen, v):                                                                          # the GONE FOREVER box, empty, the lid leaning
            B = Box(3.43, 7.0, 0.4, 0.32, _WU, _WU + 0.32, 0)
            def side(p_, W, H):
                p_.texture(rect(0, 0, W, H), 'paper', 0.4, 'multiply', 0.8)
                p_.fill(rect(0, H * 0.1, W, 5), '#c8b078', 220)
                btext(p_, 'GONE', W / 2, H * 0.48, 'caveat_b', 10, '#1a1a1a', 240, 'center'); btext(p_, 'FOREVER', W / 2, H * 0.78, 'caveat_b', 10, '#1a1a1a', 240, 'center')
            draw_box(pen, v, B, {'front': dict(fill=WL_PAL['box'], art=side), 'all': '#b88e5e'}, lw=0.8, skip=('top',))
            inner = [B.at(-0.19, 0.15, _WU + 0.32), B.at(0.19, 0.15, _WU + 0.32), B.at(0.19, -0.15, _WU + 0.32), B.at(-0.19, -0.15, _WU + 0.32)]
            path = v.poly3(inner)
            if not path.isEmpty(): pen.fill(path, '#100c08'); pen.line(path, 0.8)
            lid = [(3.24, _WU + 0.42, 7.18), (3.62, _WU + 0.42, 7.18), (3.62, _WU + 0.02, 7.12), (3.24, _WU + 0.02, 7.12)]
            path = v.poly3(lid)
            if not path.isEmpty():
                pen.fill(path, lit('#c8a070', lid[0], (0, 0.2, -1))); pen.line(path, 0.8)
                for (a_, b_) in ((lid[0], lid[3]), (lid[1], lid[2])):
                    pen.seg(v.p(a_[0] + (0.03 if a_[0] < 3.4 else -0.03), a_[1], a_[2]), v.p(b_[0] + (0.03 if b_[0] < 3.4 else -0.03), b_[1], b_[2]), 2.0, '#d8c898', 200)  # torn tape
        P.append(Piece('gone_forever', (3.43, _WU + 0.2, 7.0), gone))
        return P
    def spots(v, o):
        S = {}
        S['sleeping_bag'] = _mk_spot(v, 'sleeping_bag', 3.42, 5.9, _WU + 0.09, 'lie', 'his sleeping bag along the dead space (lying, head at the far end)')
        S['crouch'] = _mk_spot(v, 'crouch', 3.42, 5.6, _WU, 'stand', 'crouched in the dead space (found)', face=(0, -1))
        S['flashlight'] = _mk_spot(v, 'flashlight', 3.36, 5.35, _WU + 0.13, 'surface', "Dad's flashlight")
        S['bread_bags'] = _mk_spot(v, 'bread_bags', 3.32, 6.74, _WU + 0.08, 'surface', 'our bread bags, folded in a neat pile')
        S['gone_forever'] = _mk_spot(v, 'gone_forever', 3.43, 7.0, _WU + 0.32, 'surface', 'the GONE FOREVER box (empty)')
        S['hole'] = _mk_spot(v, 'hole', 3.65, 5.3, _WU + 0.95, 'point', "the hole into Sam's closet")
        return S
    return dict(name='dead_space', R=WL_DEAD, Y0=_WU, H=WL_UH, floor=dict(base='#6a5a44', kind='boards', ink='#3a2a1a', seed=81), runs=runs,
                walls=dict(paper='#8a7a62', ink=None, kind=None, wains=0.0, seed=83), ceil=dict(c='#16120e', art=ceil_art),
                lights=lights, pieces=pieces, spots=spots)


# ====================================================================================================== builders
_WL_DEF = dict(tod='night', nightlight=True)


def _wl_o(kw, extra=None):
    o = dict(_WL_DEF)
    if extra: o.update(extra)
    o.update(kw)
    return o


def _wl_entry_far():
    return _dark_far('entry', _r4p((-0.6, 1.4, 0.0, 9.0)), 0.0, WL_CEIL)


def _wl_live_door(name, v, D_fn, ang, ref, amb, steady, var, order=None):
    """A door drawn live: D_fn(t) -> Door, ang number or f(t)."""
    def fn(pen, v_, t):
        a = ang(t) if callable(ang) else ang
        D_fn(t).draw(pen, v_, a)
    return live_layer(name, v, ref, fn, amb, steady, var, order=order)


def wl_living(view='wide', **kw):
    """The living room. view: wide | chair | vent | window. tod 'night' | 'day' | 'morning' ("warm in the morning");
    levels (number or f(t)): lamp, ceil, phone (+phone_at), flash (+flash_at); boxes (moving boxes, default True)."""
    o = _wl_o(kw)
    v = cam('wl_liv_' + view)
    main = BuBox(_wl_liv_cfg(o))
    sp = build_view('wl_liv_' + view, v, main, o, far=[_wl_entry_far()], outside=_wl_outside(o), grade=_wl_grade(o))
    sp.info['note'] = 'Living room: the armchair faces south-east (anchor armchair, seat_y); the vent is half under its front edge.'
    return sp


def wl_kitchen(view='wide', **kw):
    """The kitchen (and the pantry). view: wide | counter | door | water | pantry | crack. tod; levels: kitchen_light,
    pantry_light, crack (the sliver of light through the plaster crack), phone, flash; nightlight (by the garage door,
    default on at night: it keeps the deadbolt readable); bolt 1 locked .. 0 unlocked, or f(t) (the deadbolt turning by
    itself); gdoor (deg, the door from the garage); pantry_door (deg); note True; bread 'twisted' | 'open' | None."""
    o = _wl_o(kw, dict(bolt=1.0, note=True, bread='twisted'))
    v = cam('wl_kit_' + view)
    if view in ('pantry', 'crack'):
        o.setdefault('pantry_door', 85.0)
        main = BuBox(_wl_pan_cfg(o))
        far = [BuBox(_wl_kit_cfg(dict(o, _far=True)), far=True)]
    else:
        main = BuBox(_wl_kit_cfg(o))
        far = [BuBox(_wl_pan_cfg(dict(o, _far=True)), far=True), _wl_entry_far(), _dark_far('garage', _r4p(WL_GAR), WL_GF, 2.6)]
    dyn = []
    amb, steady, var = main.lights(o)
    if callable(o.get('bolt')) and view not in ('pantry', 'crack'):
        bf = o['bolt']; ga = _static(o.get('gdoor', 0.0))
        dyn.append(_wl_live_door('garage_door', v, lambda t: wl_garage_door(bf(t)), ga, (6.0, 1.0, 4.82), amb, steady, var))
    sp = build_view('wl_kit_' + view, v, main, o, far=far, outside=_wl_outside(o), grade=_wl_grade(o), dyn=dyn)
    sp.info['note'] = 'Kitchen: the note / bread on the counter (anchors note, bread); the deadbolt (anchor deadbolt); the pantry crack (anchor crack).'
    return sp


def wl_hall(view='down', **kw):
    """The upstairs hall (and the hall closet). view: down | switch | closet | back | hatch (inside the closet, up at the
    sealed hatch). Levels: hall_light, attic (the thin yellow line: round the closet door / round the hatch), boys_moon
    (moonlight spilling from the boys' door), par_lamp, phone, flash, police; switch 0 / 1 (the dead switch down / up);
    closet (deg: 0 shut, ~6 = "opened just a crack", or f(t)); boys_door (deg, default 80, or f(t)); par_door (deg,
    default 70); lock; nightlight (default on at night)."""
    o = _wl_o(kw)
    v = cam('wl_hall_' + view)
    if view == 'hatch':
        o.setdefault('closet', 80.0)
        main = BuBox(_wl_hcl_cfg(o))
        far = [BuBox(_wl_uhall_cfg(dict(o, _far=True)), far=True)]
    else:
        main = BuBox(_wl_uhall_cfg(o))
        far = [BuBox(_wl_boys_cfg(dict(o, _far=True, door=_static(o.get('boys_door', 80.0), 80.0))), far=True),
               BuBox(_wl_par_cfg(dict(o, _far=True, door=_static(o.get('par_door', 70.0), 70.0))), far=True),
               BuBox(_wl_hcl_cfg(o), far=True), _dark_far('stairwell', _r4p((-0.6, 0.8, 0.0, 1.6)), _WU - 2.9, 5.3)]
    dyn = []
    amb, steady, var = main.lights(o)
    if callable(o.get('closet')) and view != 'hatch':
        dyn.append(_wl_live_door('hall_closet_door', v, lambda t: wl_hcl_door(), o['closet'], (0.75, _WU + 1.0, 5.47), amb, steady, var))
    if callable(o.get('boys_door')) and view != 'hatch':
        dyn.append(_wl_live_door('boys_door', v, lambda t: wl_boys_door(), o['boys_door'], (0.75, _WU + 1.0, 4.02), amb, steady, var))
    sp = build_view('wl_hall_' + view, v, main, o, far=far, outside=_wl_outside(o), grade=_wl_grade(o, ('hall_light',)), dyn=dyn)
    sp.info['note'] = 'Upstairs hall: switch (the dead switch), closet_door (the line of light), boys_door / par_door anchors.'
    return sp


def _wl_slide_layer(v, sf, o, amb, steady, var):
    """Sam's closet back wall sliding (f(t) 0..1), drawn live just in front of the closets (behind the room's shell)."""
    cfg = _wl_closet_cfg('sam', o)
    def fn(pen, v_, t):
        cfg2 = _wl_closet_cfg('sam', dict(o, slide=sf(t)))
        cfg2['shell_x'](pen, v_, dict(o, slide=sf(t)))
    return live_layer('sam_closet_slide', v, (4.15, _WU + 1.0, 5.4), fn, amb, steady, var, order=ORDER_FAR - 0.5)


def wl_boys(view='wide', **kw):
    """The boys' room. view: wide | closets | door_pov (from Sam's pillow to the doorway) | doorway | theo | sam_wall |
    doorframe (the pencil marks) | closet_sam. tod 'night' | 'morning' (the pencil marks); moon (level of the moonlight,
    default 1); nightlight (the hall's, spilling through the door); levels ceil, lamp, hall_light, phone, flash, police
    (ST.wl_police(t0): red / blue on the ceiling through the window); door (deg, default 80, or f(t)); sam_closet /
    theo_closet (deg or f(t)); slide 0..1 or f(t) (Sam's closet back wall); hole (the officers' hole from Sam's closet into
    the dead space); marks / fresh (the pencil marks, the fresh top one); theo_bed / sam_bed 'made' | 'turned' | 'empty'."""
    o = _wl_o(kw)
    v = cam('wl_boys_' + view)
    main = BuBox(_wl_boys_cfg(o))
    far = [BuBox(_wl_closet_cfg('theo', o), far=True), BuBox(_wl_closet_cfg('sam', o), far=True),
           BuBox(_wl_uhall_cfg(dict(o, _far=True, boys_door=_static(o.get('door', 80.0), 80.0))), far=True)]
    dyn = []
    amb, steady, var = main.lights(o)
    if callable(o.get('slide')): dyn.append(_wl_slide_layer(v, o['slide'], o, amb, steady, var))
    if callable(o.get('sam_closet')):
        dyn.append(_wl_live_door('sam_closet_door', v, lambda t: wl_closet_door('sam'), o['sam_closet'], (4.15, _WU + 1.0, 4.75), amb, steady, var))
    if callable(o.get('door')):
        dyn.append(_wl_live_door('boys_door', v, lambda t: wl_boys_door(), o['door'], (0.85, _WU + 1.0, 4.02), amb, steady, var))
    sp = build_view('wl_boys_' + view, v, main, o, far=far, outside=_wl_outside(o), grade=_wl_grade(o, ('ceil', 'lamp', 'hall_light')), dyn=dyn)
    sp.info['note'] = "Boys' room: doorway (\"Dad\" in the doorway), door_in (moonlit), theo_kneel, sam_closet, sam_wall, marks / marks_fresh."
    return sp


def wl_parents(view='wide', **kw):
    """The parents' room. view: wide | door | vent | bed. Levels: lamp, ceil, hall_light, phone (Mom's phone; phone_at),
    flash, police (red / blue on the ceiling through the side window: "Blue light on the ceiling"); door (deg, default 0 =
    shut, or f(t)); lock 0 / 1 (the push-button lock); bed 'made' | 'turned'; phone_on_stand (default True)."""
    o = _wl_o(kw)
    v = cam('wl_par_' + view)
    main = BuBox(_wl_par_cfg(o))
    far = [BuBox(_wl_uhall_cfg(dict(o, _far=True, par_door=_static(o.get('door', 0.0)))), far=True)]
    dyn = []
    amb, steady, var = main.lights(o)
    if callable(o.get('door')) or callable(o.get('lock')):
        lf = o.get('lock', 0.0)
        dyn.append(_wl_live_door('par_door', v, lambda t: wl_par_door(lf(t) if callable(lf) else lf), o.get('door', 0.0), (-0.65, _WU + 1.0, 7.22), amb, steady, var))
    sp = build_view('wl_par_' + view, v, main, o, far=far, outside=_wl_outside(o), grade=_wl_grade(o, ('ceil', 'lamp')), dyn=dyn)
    sp.info['note'] = "Parents' room: door_in / lock, phone, vent (the song through the grille), dresser / headboard (the scratching)."
    return sp


def _wl_hole_layer():
    """Screen-space foreground for the look through the officers' hole: broken drywall round a ragged opening, soft."""
    def draw(pen, t):
        hole = poly([(560, 140), (700, 90), (760, 150), (930, 50), (1080, 120), (1290, 90), (1350, 260), (1470, 400), (1390, 560), (1440, 780), (1240, 900),
                     (1160, 1030), (930, 960), (780, 1050), (610, 900), (470, 830), (520, 640), (420, 470), (500, 300)])
        pen.fill(minus(rect(-400, -300, 2720, 1700), hole), '#d8d2c4'); pen.fill(minus(rect(-400, -300, 2720, 1700), hole), '#0a0c14', 150)
        pen.line(hole, 26, '#f4f0e4', 200); pen.line(hole, 8, '#8a8070', 220)
    return Layer(0.25, draw, 'hole_frame', blur=10)


def wl_dead(view='slot', **kw):
    """The dead space between the closets. view: slot (down its length from its end: an officer's flashlight on the
    sleeping bag, Dad's flashlight, the bread bags folded in a neat pile, the empty GONE FOREVER box) | hole (the same, through
    the ragged hole in Sam's closet wall). Levels: flash
    (default 1; flash_at), dad_flash (Dad's flashlight on), police; hole (default True). view 'hole': through the hole."""
    o = _wl_o(kw, dict(flash=1.0, hole=True))
    v = cam('wl_dead_' + view)
    main = BuBox(_wl_dead_cfg(o))
    sp = build_view('wl_dead_' + view, v, main, o, far=[], outside=None, grade='wl_dead')
    if view == 'hole': sp = sp.add(_wl_hole_layer())
    sp.info['note'] = 'Dead space (0.45 m wide): sleeping_bag (lie), crouch, flashlight, bread_bags, gone_forever, hole.'
    return sp


# ------------------------------------------------------------------------------------------------ the cameras
_wcam('wl_liv_wide', 640, 470, 1.6, -1.0, 0.55, -52, _env(), 'the living room from the front-east corner: the green armchair facing us, the fans in the west windows, the couch', 'living')
_wcam('wl_liv_chair', 820, 520, 1.25, -2.1, 2.1, -55, _env(), 'the armchair close (warm in August; the cushion; the vent under it)', 'living')
_wcam('wl_liv_vent', 900, 470, 0.55, -2.75, 2.25, -45, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.08)), 'low on the floor vent half under the chair', 'living', pitch=28.0)
_wcam('wl_liv_window', 820, 520, 1.4, -4.2, 1.45, -90, _env(), 'a west window with its box fan', 'living')
_wcam('wl_kit_wide', 640, 520, 1.6, 1.75, 4.0, 52, _env(), 'the kitchen from the entry side: counter and window left, the pantry door, the door from the garage right', 'kitchen')
_wcam('wl_kit_counter', 1000, 470, 1.62, 3.95, 8.8, 6, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.08)), 'the note on the counter (and the bread bag)', 'kitchen', pitch=46.0)
_wcam('wl_kit_door', 760, 440, 1.45, 4.2, 4.6, 85, _env(), 'the door from the garage, the deadbolt, the nightlight', 'kitchen')
_wcam('wl_kit_water', 800, 500, 1.45, 2.0, 6.2, 112, _env(), "Sam's view at 2 a.m. from the sink side: the dark kitchen, the deadbolt turning", 'kitchen')
_wcam('wl_kit_pantry', 560, 480, 1.5, 5.1, 8.45, 52, _env(x=(920, 1000), y=(500, 560), zoom=(1.0, 1.06)), 'inside the pantry: the shelves, the cereal, the crack', 'kitchen')
_wcam('wl_kit_crack', 1100, 560, 1.45, 5.5, WL_CRACK[1], 90, _env(x=(920, 1000), y=(500, 560), zoom=(1.0, 1.08)), 'close on the crack behind the cereal (leaning in)', 'kitchen')
_wcam('wl_hall_down', 700, 520, _WU + 1.5, -0.05, 2.0, 2, _env(), 'down the upstairs hall from the stairs: the switch left, the closet right, the parents\' door, the end window', 'hall')
_wcam('wl_hall_switch', 700, 520, _WU + 1.45, 0.55, 3.4, -40, _env(), 'at the dead switch (Sam), the closet door glowing at the right edge', 'hall')
_wcam('wl_hall_closet', 520, 420, _WU + 1.5, -0.5, 5.47, 90, _env(x=(920, 1000), y=(480, 560), zoom=(1.0, 1.06)), 'the hall closet door face-on (the line of light; open a crack)', 'hall')
_wcam('wl_hall_back', 700, 520, _WU + 1.5, 0.1, 8.7, 180, _env(), "from the parents' door back down the hall: the closet, the boys' door", 'hall')
_wcam('wl_hall_hatch', 520, 540, _WU + 1.45, 0.95, 5.47, 90, _env(x=(920, 1000), y=(500, 560), zoom=(1.0, 1.06)), 'inside the hall closet, up at the sealed hatch', 'hall', pitch=-58.0)
_wcam('wl_boys_wide', 700, 430, _WU + 1.6, 1.25, 4.35, 135, _env(), "the boys' room from the door corner: both beds, the window and its fan, the wall by Sam's bed", 'boys')
_wcam('wl_boys_closets', 640, 540, _WU + 1.5, 3.3, 0.45, 0, _env(), 'from the window: the two closets, the doorway left, the bed ends', 'boys')
_wcam('wl_boys_door_pov', 900, 520, _WU + 0.85, 5.45, 0.45, -50, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.12)), "from Sam's pillow to the doorway (\"Dad\" standing there)", 'boys')
_wcam('wl_boys_doorway', 800, 520, _WU + 1.5, 4.2, 2.2, -60, _env(), 'the doorway at 3/4 from the room (he steps in; the moonlight)', 'boys')
_wcam('wl_boys_theo', 900, 520, _WU + 1.15, 3.1, 2.9, -125, _env(), "Theo's bed (kneeling, tucking him in)", 'boys')
_wcam('wl_boys_sam_wall', 900, 520, _WU + 1.0, 3.6, 1.3, 90, _env(), "Sam's bed and the wall by it (the voice in the wall)", 'boys')
_wcam('wl_boys_doorframe', 1300, 540, _WU + 1.45, 2.0, 3.3, -80, _env(x=(920, 1000), y=(480, 580), zoom=(1.0, 1.1)), 'the pencil marks on the doorframe', 'boys')
_wcam('wl_boys_closet_sam', 700, 520, _WU + 1.45, 4.6, 3.85, -40, _env(), "Sam's closet (the back wall slides; the hole)", 'boys')
_wcam('wl_par_wide', 640, 470, _WU + 1.6, -0.95, 5.0, -70, _env(), "the parents' room from the door side: the bed and headboard, the nightstand, the dresser, the vent", 'parents')
_wcam('wl_par_door', 700, 500, _WU + 1.5, -3.4, 6.2, 75, _env(), 'the door from inside (shut, locked)', 'parents')
_wcam('wl_par_vent', 900, 470, _WU + 0.6, -3.4, 5.65, 180, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.08)), 'low on the floor vent (the voice through the grille)', 'parents', pitch=30.0)
_wcam('wl_par_bed', 760, 520, _WU + 1.35, -2.3, 5.3, -60, _env(), 'the family on the bed (the phone, the headboard)', 'parents')
_wcam('wl_dead_slot', 900, 470, _WU + 1.6, 3.42, 4.86, 0, _env(x=(930, 990), y=(500, 560), zoom=(1.0, 1.05)), 'down the dead space from its end (an officer peering in, flashlight): the bag, the flashlight, the bags, the box', 'dead', pitch=30.0)
_wcam('wl_dead_hole', 520, 500, _WU + 1.45, 3.8, 5.12, -14, _env(x=(930, 990), y=(500, 560), zoom=(1.0, 1.04)), "through the ragged hole in Sam's closet wall into the dead space", 'dead', pitch=22.0)


# ====================================================================================================== inserts
WL_NOTE_LINES = ['Welcome home.', 'A few things about the old girl.', 'She settles at night.', 'The pipes knock.', 'Mice come in the fall.',
                 'One hall switch does nothing.', "The attic is sealed, don't bother.", 'Be happy here.', 'L. Pell']
WL_RULES = [(1, 'Lock every door, every night. Even the garage door. Even the little basement window.'),
            (2, "Count the cookies. If something is missing, say it out loud. Don't say mice."),
            (3, 'If the big chair is warm, and nobody sat in it, tell.'),
            (4, 'Never open the hall closet at night. Never look in the walls alone.'),
            (5, 'Know your address. Sing it.'),
            (6, "If someone is inside, don't look for him. Get away from him, get behind a locked door with a phone, and call.")]
WL_RULE7 = 'Believe me.'
_SAM_INK = '#22305a'                   # Sam's ballpoint (a 12-year-old's careful printing)


def _wl_counter_bg(pen, night=False):
    _ibg_b(pen, '#d8d0c0' if not night else '#4a5060', '#b8b0a0' if not night else '#2a3040', 120)
    pen.texture(rect(*_IBGB), 'grunge', 0.35, 'overlay', 1.0)
    for k in range(60):
        pen.fill(oval(-400 + (k * 197) % 2800, -300 + (k * 131) % 1800, 3), '#ffffff' if not night else '#8a90a0', 40)


def _wli_note(pen, t, hl=None, show=9, **kw):
    """Mr. Pell's note on the counter, word for word, in his shaky hand (hl = the line being read: a warm highlight)."""
    _wl_counter_bg(pen)
    pen.cv.save(); pen.cv.translate(960, 540); pen.cv.rotate(-2.0)
    pen.cv.scale(0.92, 0.92)
    W, H = 1060, 960
    x0, y0 = -W / 2, -H / 2 - 20
    pen.fill(rect(x0 + 14, y0 + 22, W, H), '#000000', 100, blur=22)
    pen.fill(rect(x0, y0, W, H), '#f4ecd4'); pen.texture(rect(x0, y0, W, H), 'paper', 0.45, 'multiply', 1.0)
    for i in range(int(H / 88)): pen.fill(rect(x0 + 40, y0 + 120 + i * 88, W - 80, 2), '#a8b8d0', 90)
    for i, ln in enumerate(WL_NOTE_LINES[:show]):
        yy = y0 + 112 + i * 92 + (14 if i == 8 else 0)
        xx = x0 + (560 if i == 8 else 70)
        if hl is not None and hl == i:
            pen.fill(rect(xx - 14, yy - 58, btext_width(ln, 'hand', 58) + 40, 76), '#ffe88a', 150)
        _shaky(pen, ln, xx, yy, 58, '#1e2a5a', 245, 40 + i, 'hand')
    pen.cv.restore()


def _notebook(pen, W=1560, H=980, tilt=-1.2):
    """Theo's dinosaur notebook open flat: the green cover's edge with a dinosaur sticker, the spiral, a lined page.
    Leaves the canvas translated to the page's top-left (call pen.cv.restore())."""
    _ibg_b(pen, '#7a5a3a', '#4a3420', 130); pen.texture(rect(*_IBGB), 'wood', 0.35, 'overlay', 1.2, 90)
    pen.cv.save(); pen.cv.translate(960, 545); pen.cv.rotate(tilt); pen.cv.translate(-W / 2, -H / 2)
    pen.fill(rect(-60, -30, W + 90, H + 60), '#000000', 110, blur=24)
    pen.fill(rrect(-60, -30, W + 90, H + 60, 20), '#3a8a5a'); pen.texture(rrect(-60, -30, W + 90, H + 60, 20), 'fabric', 0.4, 'overlay', 1.0)
    pen.fill(rect(0, 0, W, H), '#f8f4e8'); pen.texture(rect(0, 0, W, H), 'paper', 0.4, 'multiply', 1.0)
    for i in range(int((H - 110) / 58)): pen.fill(rect(0, 120 + i * 58, W, 2.2), '#8ab0d8', 120)
    pen.fill(rect(150, 0, 3, H), '#d88a8a', 140)
    for k in range(int(H / 44)):                                                # the spiral
        pen.fill(oval(-22, 22 + k * 44, 11, 15), '#2a2a2a', 200); pen.line(oval(-22, 22 + k * 44, 11, 15), 3.2, '#c8c8d0', 230)
    _dino_sil(pen, W - 120, 74, 34, 1, '#4aa06a')
    return W, H


def _wli_rules(pen, t, show=6, hl=0, seven=0.0, **kw):
    """The notebook page: THEO'S RULES in Sam's printing, word for word; rule 7 is a BLANK line (seven 0..1 writes "Believe
    me." on it at the very end); hl = the rule being read (7 = the empty line Theo taps)."""
    W, H = _notebook(pen)
    btext(pen, "THEO'S RULES", 190, 88, 'kid', 54, _SAM_INK, 250)
    yy = 178
    for (n, txt) in WL_RULES[:show]:
        lines = _wrap(txt, 58)
        if hl == n: pen.fill(rect(160, yy - 44, W - 200, 58 * len(lines) + 4), '#fff08a', 150)
        btext(pen, '%d.' % n, 166, yy, 'kid', 38, _SAM_INK, 245)
        for j, ln in enumerate(lines): btext(pen, ln, 214, yy + j * 58, 'kid', 37, _SAM_INK, 240)
        yy += 58 * len(lines)
    if show >= 6:
        if hl == 7: pen.fill(rect(160, yy - 44, W - 200, 62), '#fff08a', 150)
        btext(pen, '7.', 166, yy, 'kid', 38, _SAM_INK, 245)
        if seven > 0.01:
            ws = WL_RULE7.split(); nw = int(math.ceil(len(ws) * clamp(seven)))
            btext(pen, ' '.join(ws[:nw]), 214, yy, 'kid', 40, _SAM_INK, 248)
    pen.cv.restore()


def _wli_rule(pen, t, n=1, write=1.0, **kw):
    """One rule large on the notebook page (legible while it is read). n 1..6; n 7 = the blank line (write > 0: "Believe me.")."""
    W, H = _notebook(pen, tilt=-0.6 if n % 2 else 0.6)
    btext(pen, 'RULE NUMBER %s' % 'ONE TWO THREE FOUR FIVE SIX SEVEN'.split()[n - 1], 200, 100, 'kid', 58, _SAM_INK, 250)
    if n <= 6:
        lines = _wrap(dict(WL_RULES)[n], 34)
        words = sum(len(l.split()) for l in lines); nw = int(math.ceil(words * clamp(write)))
        k = 0
        for j, ln in enumerate(lines):
            shown = ' '.join(ln.split()[:max(0, nw - k)]); k += len(ln.split())
            btext(pen, shown, 200, 268 + j * 116, 'kid', 76, _SAM_INK, 250)
    else:
        pen.fill(rect(196, 330, W - 300, 3), _SAM_INK, 60)
        if write > 0.01:
            ws = WL_RULE7.split(); nw = int(math.ceil(len(ws) * clamp(write)))
            btext(pen, ' '.join(ws[:nw]), 220, 318, 'kid', 96, _SAM_INK, 250)
    pen.cv.restore()


def _frog2d(pen, x, y, s=1.0, lift=0.0, key=True, night=False):
    if key:
        k = s
        pen.fill(rect(x - 40 * k, y - 12 * k, 300 * k, 24 * k), '#000000', 80, blur=6 * k)
        kc = '#d8b050' if not night else '#a89048'
        x0_ = x; x = x - 230 * k
        pen.fill(oval(x - 70 * k, y - 4 * k, 46 * k, 34 * k), kc); pen.fill(oval(x - 70 * k, y - 4 * k, 18 * k, 13 * k), '#5a5040')
        pen.fill(rect(x - 26 * k, y - 12 * k, 230 * k, 18 * k), kc)
        for (dx, h) in ((150, 26), (176, 18), (196, 30)): pen.fill(rect(x + dx * k, y + 4 * k, 14 * k, h * k), kc)
        pen.line(union(oval(x - 70 * k, y - 4 * k, 46 * k, 34 * k), rect(x - 26 * k, y - 12 * k, 230 * k, 18 * k)), 2.4, '#5a4a20', 200)
        x = x0_
    cv = pen.cv; cv.save(); cv.translate(x + 260 * s, y + 20 * s); cv.rotate(-24.0 * lift); cv.translate(-(x + 260 * s), -(y + 20 * s))
    c = '#8a8e84' if not night else '#5a6070'
    body = union(oval(x + 40 * s, y - 120 * s, 260 * s, 140 * s), oval(x - 30 * s, y - 250 * s, 170 * s, 130 * s))
    pen.fill(oval(x + 40 * s, y + 10 * s, 290 * s, 40 * s), '#000000', 120, blur=20 * s)
    pen.fill(body, c); pen.texture(body, 'grunge', 0.8, 'overlay', 0.8)
    pen.linear(body, 0, y - 380 * s, 0, y + 20 * s, [(0, '#ffffff', 50), (1, '#000000', 90)])
    for (dx, dy, r) in ((60, -60, 70), (160, -110, 40), (-60, -180, 30)): pen.fill(oval(x + dx * s, y + dy * s, r * s, r * 0.6 * s), '#5a7a4a', 110)   # moss
    for ex in (-130, 50):
        e = oval(x + ex * s, y - 330 * s, 66 * s, 58 * s)
        pen.fill(e, c); pen.line(e, 3, '#2a2c28', 200)
        pen.fill(oval(x + ex * s, y - 326 * s, 34 * s, 20 * s), '#2a2c28')
        pen.line(smooth([(x + (ex - 58) * s, y - 344 * s), (x + ex * s, y - 360 * s), (x + (ex + 58) * s, y - 344 * s)], False), 4 * s, '#2a2c28', 200)  # heavy lids
    pen.line(smooth([(x - 200 * s, y - 200 * s), (x - 40 * s, y - 165 * s), (x + 110 * s, y - 205 * s)], False), 4 * s, '#2a2c28', 220)
    for fx in (-160, 220): pen.fill(oval(x + fx * s, y - 14 * s, 70 * s, 26 * s), _darken(c, 0.1)); pen.line(oval(x + fx * s, y - 14 * s, 70 * s, 26 * s), 2.4)
    pen.line(body, 3.2, '#2a2c28', 220)
    cv.restore()


def _wli_frog(pen, t, lift=0.0, key=True, tod='day', **kw):
    """The stone frog by the front step, the key under it (lift 0..1 tips it up: the key shows)."""
    night = tod == 'night'
    _ibg_b(pen, '#6a7a44' if not night else '#1a2a2a', '#3a4a2a' if not night else '#0a1216', 140)
    pen.texture(rect(*_IBGB), 'grunge', 0.6, 'overlay', 4.0)
    pen.fill(rect(-520, -420, 1180, 1920), '#a8a49a' if not night else '#4a4e58'); pen.texture(rect(-520, -420, 1180, 1920), 'asphalt', 0.6, 'overlay', 1.2)   # the step
    pen.fill(rect(640, -420, 30, 1920), '#000000', 90)
    _frog2d(pen, 1180, 760, 1.25, lift, key, night)


def _wli_keypad(pen, t, press=None, tod='night', **kw):
    """The garage keypad on the siding: twelve rubber keys with a green backlight; press = the key lit ('1'..'9', '0')."""
    night = tod == 'night'
    _ibg_b(pen, '#7a8a8a' if not night else '#2a3442', '#5a6a6a' if not night else '#141a24', 120)
    for k in range(14): pen.fill(rect(-520, -420 + k * 140, 2960, 8), '#000000', 70)                      # clapboard
    pen.cv.save(); pen.cv.translate(960, 560); pen.cv.rotate(1.5)
    body = rrect(-250, -360, 500, 720, 46)
    pen.fill(moved(body, 14, 20), '#000000', 110, blur=24); pen.fill(body, '#8e9094'); pen.line(body, 3)
    pen.linear(body, 0, -360, 0, 360, [(0, '#ffffff', 50), (1, '#000000', 60)])
    pen.fill(rrect(-170, -300, 340, 70, 10), '#4a4c50'); btext(pen, 'ENTER CODE', 0, -252, 'sans_b', 30, '#c8c8c8', 220, 'center')
    keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#']
    for i, kk in enumerate(keys):
        cx, cy = -130 + (i % 3) * 130, -150 + (i // 3) * 120
        r = rrect(cx - 50, cy - 44, 100, 88, 18)
        lit_ = press == kk
        pen.fill(r, '#a8f0b0' if (night and lit_) else ('#d8ecd8' if night else '#e4e4e0'))
        if night: pen.glow(cx, cy, 70, '#8affa0', 90 if lit_ else 30)
        pen.line(r, 2.2, '#3a3c40')
        btext(pen, kk, cx, cy + 18, 'sans_b', 50, '#2a2c30', 240, 'center')
    pen.cv.restore()


def _wli_deadbolt(pen, t, turn=1.0, **kw):
    """The deadbolt thumb-turn on the kitchen side of the door from the garage, at night (the nightlight below): turn 1 =
    locked (the bar across), 0 = unlocked (the bar upright). "Click. Unlocked. From the kitchen side." """
    _ibg_b(pen, '#c8c2b4', '#8a8478', 150)
    pen.texture(rect(*_IBGB), 'wood', 0.25, 'overlay', 1.0, 90)
    pen.fill(rect(-520, -420, 2960, 1920), '#0a1020', 120)
    pen.radial(None, 1180, 1200, 1100, [(0, '#ffcf8a', 110), (1, '#ffcf8a', 0)])                         # the nightlight's warm glow from below
    pen.fill(rect(1500, -420, 60, 1920), '#000000', 80)                                                   # the door edge / casing
    cx, cy = 960, 470
    rose = oval(cx, cy, 190)
    pen.fill(moved(rose, 10, 16), '#000000', 110, blur=18)
    pen.fill(rose, '#b8964a'); pen.radial(rose, cx - 60, cy - 70, 240, [(0, '#fff0c0', 160), (1, '#6a5020', 120)]); pen.line(rose, 3, '#4a3a18')
    pen.cv.save(); pen.cv.translate(cx, cy); pen.cv.rotate(90.0 * (1.0 - clamp(turn)))
    bar = rrect(-150, -42, 300, 84, 38)
    pen.fill(moved(bar, 6, 10), '#000000', 120, blur=10)
    pen.fill(bar, '#c8a858'); pen.linear(bar, 0, -42, 0, 42, [(0, '#fff4c8', 200), (1, '#6a5020', 180)]); pen.line(bar, 3, '#4a3a18')
    pen.cv.restore()
    for (dx, dy) in ((-130, -130), (130, 130)): pen.fill(oval(cx + dx, cy + dy, 12), '#6a5020')
    kn = oval(cx, cy + 520, 150)                                                                           # the knob below
    pen.fill(kn, '#b8964a'); pen.radial(kn, cx - 40, cy + 470, 200, [(0, '#fff0c0', 150), (1, '#6a5020', 120)]); pen.line(kn, 3, '#4a3a18')


def _wli_bread(pen, t, state='twisted', **kw):
    """The bread bag on the counter: folded neatly under, twisted shut again (like someone polite had been eating our food)."""
    _wl_counter_bg(pen)
    pen.cv.save(); pen.cv.translate(900, 560); pen.cv.rotate(-6.0)
    loaf = rrect(-520, -200, 860, 400, 150)
    pen.fill(moved(loaf, 20, 30), '#000000', 100, blur=26)
    pen.fill(loaf, '#d8a868'); pen.texture(loaf, 'paper', 0.5, 'overlay', 1.0)
    for k in range(7): pen.line(smooth([(-460 + k * 110, -190), (-470 + k * 110, 0), (-460 + k * 110, 190)], False), 2.4, '#a8783a', 150)
    bag = rrect(-560, -230, 940, 460, 160)
    pen.fill(bag, '#eef2fa', 90); pen.line(bag, 3, '#ffffff', 200)
    pen.fill(rrect(-380, -110, 460, 220, 30), '#f4f0e8', 220); pen.line(rrect(-380, -110, 460, 220, 30), 2, '#c83a3a', 200)
    btext(pen, 'WHITE', -150, -10, 'head', 70, '#c83a3a', 240, 'center'); btext(pen, 'sandwich bread', -150, 60, 'sans_b', 34, '#3a5a9a', 230, 'center')
    if state == 'twisted':
        tw = poly([(370, -150), (520, -26), (700, -60), (700, 60), (520, 26), (370, 150)])
        pen.fill(tw, '#eef2fa', 170); pen.line(tw, 2.6, '#ffffff', 220)
        for k in range(5): pen.line(smooth([(530 + k * 30, -40), (545 + k * 30, 0), (530 + k * 30, 40)], False), 1.6, '#a8b0c0', 160)
        pen.fill(rrect(506, -46, 30, 92, 8), '#2a6ad0'); pen.line(rrect(506, -46, 30, 92, 8), 1.6)            # the twist tie, wound tight
    else:
        op = poly([(370, -170), (700, -280), (760, -40), (720, 200), (370, 170)])
        pen.fill(op, '#eef2fa', 120); pen.line(op, 2.4, '#ffffff', 200)
    pen.cv.restore()


def _crayon(pen, pts, c, w=10, a=230, closed=False):
    pen.line(smooth(pts, closed, 0.4), w, c, a); pen.line(smooth([(x + 2, y + 2) for (x, y) in pts], closed, 0.4), w * 0.5, c, a * 0.5)


def _drawing(pen, x, y, s=1.0, rot=0.0, seed=0):
    """One of Theo's drawings: crayon on printer paper - a tall man INSIDE a wall (the wall's lines round him), a sad dog
    face with long ears, a red shirt; a little house and a sun in the corner. Every one the same."""
    pen.cv.save(); pen.cv.translate(x, y); pen.cv.rotate(rot); pen.cv.scale(s, s)
    W, H = 420, 560
    pen.fill(rect(-W / 2 + 10, -H / 2 + 16, W, H), '#000000', 90, blur=14)
    pen.fill(rect(-W / 2, -H / 2, W, H), '#fbfaf4'); pen.texture(rect(-W / 2, -H / 2, W, H), 'paper', 0.4, 'multiply', 0.8)
    for k in range(5): pen.seg((-W / 2, -H / 2 + 112 * k + 40), (W / 2, -H / 2 + 112 * k + 40 + 6 * ((k + seed) % 3 - 1)), 1.2, '#000000', 30)   # fold creases
    for k in range(9):                                                         # the wall: rows of bricks round him
        yy = -230 + k * 54
        _crayon(pen, [(-180, yy), (180, yy + 4)], '#b86a3a', 5, 200)
        for j in range(4): _crayon(pen, [(-160 + j * 100 + (k % 2) * 50, yy), (-160 + j * 100 + (k % 2) * 50, yy + 52)], '#b86a3a', 4, 170)
    pen.fill(rrect(-70, -200, 140, 430, 40), '#fbfaf4', 245)                    # the gap he stands in
    _crayon(pen, [(-70, -200), (-70, 230)], '#5a3a2a', 7); _crayon(pen, [(70, -200), (70, 230)], '#5a3a2a', 7)
    _crayon(pen, [(-40, 40), (-46, 210)], '#7a7a7a', 9); _crayon(pen, [(30, 40), (36, 210)], '#7a7a7a', 9)     # long legs
    shirt = poly([(-52, -70), (52, -70), (46, 50), (-46, 50)])
    pen.fill(shirt, '#d83a3a', 230)
    for k in range(4): _crayon(pen, [(-50, -50 + k * 28), (50, -50 + k * 28)], '#2a1a1a', 4, 200)
    _crayon(pen, [(-52, -60), (-70, 60)], '#d83a3a', 9); _crayon(pen, [(52, -60), (66, 60)], '#d83a3a', 9)
    face = oval(0, -120, 46, 50)
    pen.fill(face, '#9a7a5a', 230); pen.line(face, 4, '#3a2a1a', 220)
    _crayon(pen, [(-40, -150), (-62, -100), (-58, -40)], '#5a3a2a', 12); _crayon(pen, [(40, -150), (62, -100), (58, -40)], '#5a3a2a', 12)   # droopy ears
    for ex in (-18, 18):
        _crayon(pen, [(ex - 12, -128), (ex, -124), (ex + 12, -128)], '#1a1a1a', 5)                                   # heavy, sad, half-closed
        pen.fill(oval(ex, -120, 5), '#1a1a1a', 220)
    pen.fill(oval(0, -98, 10, 7), '#1a1a1a', 230)
    _crayon(pen, [(-14, -80), (0, -86), (14, -80)], '#1a1a1a', 4)
    _crayon(pen, [(130, -230), (150, -250), (170, -230)], '#e8c020', 6); pen.fill(oval(150, -240, 18), '#f2d040', 200)
    pen.cv.restore()


def _wli_drawings(pen, t, state='spread', n=4, **kw):
    """Theo's drawings under the cushion: 'folded' (folded very small, a little stack on the chair's green deck) |
    'spread' (opened and fanned: every one the same tall man inside a wall, sad dog face, red shirt)."""
    _ibg_b(pen, WL_PAL['armchair'], WL_PAL['armchair_d'], 150)
    pen.texture(rect(*_IBGB), 'fabric', 0.6, 'overlay', 1.4)
    if state == 'folded':
        for k in range(5):
            r = rrect(760 + k * 6, 470 - k * 14, 380, 220, 6)
            pen.fill(moved(r, 8, 12), '#000000', 90, blur=10); pen.fill(r, '#f4f2ea'); pen.line(r, 1.6, '#a8a498')
            pen.seg((770 + k * 6, 580 - k * 14), (1130 + k * 6, 580 - k * 14), 1.2, '#c8c4b8')
        return
    for i in range(min(4, n)):
        _drawing(pen, 520 + i * 300, 560 + (i % 2) * 30, 0.95, -12 + i * 8, i)


def _wli_switch(pen, t, on=0.0, **kw):
    """The hall switch that does nothing: an old cream toggle plate on the hall's wallpaper, the nightlight glow from below;
    on 0 (down) .. 1 (up)."""
    _ibg_b(pen, WL_PAL['hall_paper'], _darken(WL_PAL['hall_paper'], 0.3), 160)
    rng = np.random.default_rng(3)
    for i in range(160): pen.fill(oval(rng.uniform(-500, 2400), rng.uniform(-400, 1500), rng.uniform(5, 9)), WL_PAL['hall_ink'], 110)
    pen.fill(rect(-520, -420, 2960, 1920), '#0a1020', 110)
    pen.radial(None, 700, 1500, 1200, [(0, WL_NIGHTL, 90), (1, WL_NIGHTL, 0)])
    plate = rrect(760, 180, 400, 640, 30)
    pen.fill(moved(plate, 12, 18), '#000000', 110, blur=20); pen.fill(plate, '#ece4cc'); pen.line(plate, 3, '#6a6050')
    pen.linear(plate, 0, 180, 0, 820, [(0, '#ffffff', 40), (1, '#000000', 50)])
    for sy in (240, 760): pen.fill(oval(960, sy, 14), '#c8bea6'); pen.seg((948, sy), (972, sy), 2.4, '#6a6050')
    pen.fill(rrect(915, 420, 90, 160, 12), '#4a4234')
    k = clamp(on)
    tog = rrect(928, 500 - 150 if k > 0.5 else 500, 64, 150, 24)
    pen.fill(moved(tog, 6, 10), '#000000', 110, blur=8); pen.fill(tog, '#f8f2e0'); pen.line(tog, 2.4, '#6a6050')


def _wli_vent(pen, t, rattle=0.0, **kw):
    """The floor vent grille in the parents' room: louvres onto the dark (rattle: the grille shaking, level or f(t))."""
    _ibg_b(pen, WL_PAL['floor'], _darken(WL_PAL['floor'], 0.4), 150)
    for k in range(9): pen.fill(rect(-520, -420 + k * 230, 2960, 4), '#2a1a0e', 160)
    pen.texture(rect(*_IBGB), 'wood', 0.5, 'overlay', 1.0, 0)
    pen.fill(rect(-520, -420, 2960, 1920), '#0a1020', 110)
    j = 6.0 * rattle * math.sin(t * 70.0)
    pen.cv.save(); pen.cv.translate(960 + j, 560)
    fr = rrect(-620, -270, 1240, 540, 14)
    pen.fill(moved(fr, 10, 16), '#000000', 120, blur=18); pen.fill(fr, '#9a948a'); pen.line(fr, 3)
    pen.fill(rect(-560, -210, 1120, 420), '#030303')
    for k in range(16):
        x = -540 + k * 72
        sl = rect(x, -205, 40, 410)
        pen.fill(sl, '#b8b2a6'); pen.linear(sl, x, 0, x + 40, 0, [(0, '#e8e4dc', 220), (1, '#5a564e', 220)])
    for (dx, dy) in ((-590, -240), (590, 240)): pen.fill(oval(dx, dy, 10), '#5a564e')
    pen.cv.restore()


def _wli_phone(pen, t, state='call', secs=0, **kw):
    """Mom's phone at three in the morning: 'dial' (the keypad, 9-1-1 typed) | 'call' (Emergency call, 911, the timer)."""
    _ibg_b(pen, '#2a2236', '#0c0a14', 160)
    scr = _phone2d(pen)
    pen.linear(scr, 0, -540, 0, 540, [(0, '#1a1a22'), (1, '#0c0c12')])
    btext(pen, '3:04', -170, -488, 'sans_b', 30, '#f4f6ff', 240, 'center')
    if state == 'dial':
        btext(pen, '911', 0, -250, 'sans', 130, '#f4f6ff', 250, 'center')
        for i, kk in enumerate(['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#']):
            cx, cy = -150 + (i % 3) * 150, -60 + (i // 3) * 130
            pen.fill(oval(cx, cy, 56), '#3a3a44'); btext(pen, kk, cx, cy + 20, 'sans', 56, '#ffffff', 245, 'center')
        pen.fill(oval(0, 470, 62), '#2ac85a')
        pen.line(smooth([(-22, 452), (-14, 492), (22, 488)], False), 9, '#ffffff', 240)
    else:
        btext(pen, 'Emergency call', 0, -300, 'sans', 46, '#c8d0e8', 235, 'center')
        btext(pen, '911', 0, -180, 'sans', 140, '#f4f6ff', 250, 'center')
        btext(pen, '00:%02d' % int(secs), 0, -100, 'sans', 44, '#c8d0e8', 230, 'center')
        for i, lab in enumerate(['mute', 'keypad', 'speaker']):
            cx = -160 + i * 160
            pen.fill(oval(cx, 140, 56), '#3a3a44'); btext(pen, lab, cx, 230, 'sans', 26, '#c8d0e8', 220, 'center')
        pen.fill(oval(0, 430, 62), '#e83a3a')
        pen.line(smooth([(-26, 430), (0, 418), (26, 430)], False), 10, '#ffffff', 240)
    pen.cv.restore()
    pen.glow(960, 540, 700, '#8aa8ff', 34)


def _wli_marks(pen, t, fresh=1.0, **kw):
    """The doorframe of my room, the next morning: pencil lines - L, age four; L, age eight; L, age twelve (old, faded) -
    and one more, higher than all of them, fresh dark pencil, dated last week."""
    _ibg_b(pen, '#b8c8d8', '#8a9ab0', 120)
    for k in range(40): pen.fill(oval(-400 + (k * 173) % 1300, -300 + (k * 211) % 1800, 6), '#90a8c0', 120)           # the stars paper
    pen.fill(rect(820, -420, 360, 1920), '#f2eee4'); pen.texture(rect(820, -420, 360, 1920), 'wood', 0.25, 'overlay', 0.8, 90)
    pen.fill(rect(800, -420, 22, 1920), '#000000', 60); pen.fill(rect(1180, -420, 30, 1920), '#000000', 90)
    pen.radial(None, 1300, 200, 1400, [(0, '#fff0d0', 70), (1, '#fff0d0', 0)])                                          # morning light
    # metres on the frame: the insert spans about Y 0.9 .. 2.05 (1 m = 760 px), Y 2.0 near the top
    def yy(Y): return 1120 - (Y - 0.9) * 760
    for (Y, lab) in ((1.02, 'L  age 4  \'62'), (1.27, 'L  age 8  \'66'), (1.50, 'L  age 12  \'70')):
        pen.seg((850, yy(Y)), (1060, yy(Y) + 3), 3.0, '#7a7a82', 170)
        btext(pen, lab, 860, yy(Y) - 14, 'hand', 40, '#7a7a82', 165)
    if fresh > 0.01:
        a = 245 * clamp(fresh)
        pen.seg((846, yy(1.86)), (1100, yy(1.86) - 2), 4.2, '#26262c', a)
        btext(pen, 'L', 860, yy(1.86) - 16, 'hand', 46, '#26262c', a)
        btext(pen, '8/19', 940, yy(1.86) - 16, 'hand', 42, '#26262c', a)


WL_INSERTS = {
    'note': (_wli_note, 'wl_ins', "Mr. Pell's note, word for word, shaky (hl = line index 0..8 being read; show)"),
    'rules': (_wli_rules, 'wl_ins', "Theo's rules in the dinosaur notebook, Sam's printing; 7 is a blank line (show 1..6, hl 1..7, seven 0..1)"),
    'rule': (_wli_rule, 'wl_ins', 'one rule big on the notebook page (n 1..7; write 0..1; n 7 = the blank line / "Believe me.")'),
    'frog': (_wli_frog, 'wl_ins', 'the stone frog by the step, the key under it (lift 0..1, key, tod)'),
    'keypad': (_wli_keypad, 'wl_ins_night', "the garage keypad (Mr. Pell's old code still works): press '1'..'0', tod"),
    'deadbolt': (_wli_deadbolt, 'wl_ins_night', 'the deadbolt thumb-turn, kitchen side: turn 1 locked .. 0 unlocked (f(t): turning by itself)'),
    'bread': (_wli_bread, 'wl_ins', "the bread bag twisted shut again (state 'twisted' | 'open')"),
    'drawings': (_wli_drawings, 'wl_ins', "Theo's drawings under the cushion (state 'folded' | 'spread')"),
    'switch': (_wli_switch, 'wl_ins_night', 'the hall switch that does nothing (on 0 / 1)'),
    'vent': (_wli_vent, 'wl_ins_night', 'the floor vent grille (rattle level / f(t))'),
    'phone': (_wli_phone, 'wl_ins_night', "Mom's phone: state 'dial' (911 typed) | 'call' (Emergency call 911, secs)"),
    'marks': (_wli_marks, 'wl_ins', 'the pencil marks on the doorframe; the fresh top one (fresh 0..1)'),
}


def wl_insert(name, prop_kw=None, motion=None, t0=0.0, grade=None):
    """A close-up insert from WL_INSERTS (flat 1920 x 1080 design space with margin for a drift): prop_kw dict (values may
    be f(t)) or f(t) -> dict; motion f(t) -> (dx, dy, dscale, drot)."""
    fn, gr, note = WL_INSERTS[name]
    static = not callable(prop_kw) and motion is None and not any(callable(v_) for v_ in (prop_kw or {}).values()) and name not in ('vent',)

    def draw(pen, t):
        kw = prop_kw(t) if callable(prop_kw) else dict(prop_kw or {})
        kw = {k_: (v_(t) if callable(v_) else v_) for k_, v_ in kw.items()}
        cv = pen.cv
        if motion is not None:
            dx, dy, ds, dr = motion(t)
            cv.save(); cv.translate(960 + dx, 540 + dy); cv.rotate(dr); cv.scale(1 + ds, 1 + ds); cv.translate(-960, -540)
        fn(pen, t - t0, **kw)
        if motion is not None: cv.restore()
    key = 'wlins:%s:%s' % (name, _okey(prop_kw or {}) if isinstance(prop_kw, dict) else 'f')
    lay = Layer(1.0, draw, 'insert', cache=key if static else False, bounds=(-460, -320, 2380, 1400), blur=0)
    return BSet('wl_ins_' + name, [lay], {}, {}, lens=None, grade=grade or gr, focus=1.0, dof=0.0, cover=(-460, -320, 2380, 1400), info={'note': note})


# ====================================================================================================== the plan map, the registry
def _wl_plan_panels():
    def blocks(*sets_):
        b = {}
        for sp_ in sets_:
            for k_, q in (sp_.info.get('blocks') or {}).items():
                if not k_.startswith('far_') and q: b[k_] = q
        return b
    def marks(sp_, names):
        return [(sp_.anchors[n].X, sp_.anchors[n].Yp, n) for n in names if n in sp_.anchors]
    lv, kt = wl_living('wide'), wl_kitchen('wide')
    hl, bo, pa, de = wl_hall('down'), wl_boys('wide'), wl_parents('wide'), wl_dead('slot')
    P = [dict(title='GROUND FLOOR  (floor Y 0, ceiling %.1f)' % WL_CEIL, ext=(-7.0, 13.0, -3.0, 11.0), ray=1.2,
              floors=[('LIVING ROOM', _r4p(WL_LIV)), ('KITCHEN', _WL_KIT_POLY), ('PANTRY', _r4p(WL_PAN)), ('entry + stairs', _r4p((-0.6, 1.4, 0.0, 9.0))),
                      ('GARAGE (floor %.1f)' % WL_GF, _r4p(WL_GAR)), ('cavity', _r4p((6.0, 6.35, 0.0, 10.0))), ('porch', _r4p(WL_PORCH))],
              blocks=blocks(lv, kt),
              doors=[((WL_FDOOR[0], 0.0), (WL_FDOOR[1], 0.0), 'front door'), ((6.0, WL_GDOOR[0]), (6.0, WL_GDOOR[1]), 'from the garage (deadbolt)'),
                     ((WL_PDOOR[0], 8.6), (WL_PDOOR[1], 8.6), 'pantry'), ((-0.6, WL_LOPEN[0]), (-0.6, WL_LOPEN[1]), ''), ((1.4, WL_KOPEN[0]), (1.4, WL_KOPEN[1]), ''),
                     ((WL_GARDOOR[0], 0.0), (WL_GARDOOR[1], 0.0), 'garage door')],
              windows=[((WL_LWIN_F[0], 0.0), (WL_LWIN_F[1], 0.0))] + [((-6.0, a), (-6.0, b)) for (a, b) in WL_LWIN_W] + [((WL_KWIN[0], 10.0), (WL_KWIN[1], 10.0))],
              lines=[], marks=marks(lv, ('armchair', 'vent')) + marks(kt, ('note', 'deadbolt', 'door_in')) + [(WL_CRACK[0], WL_CRACK[1], 'crack'), (WL_FROG[0], WL_FROG[1], 'frog'), (WL_KEYPAD[0], 0.0, 'keypad')],
              cams=[k for k in WL_CAMS if CAMS[k]['room'] in ('living', 'kitchen')]),
         dict(title='UPSTAIRS  (floor Y %.1f, ceiling +%.1f)' % (_WU, WL_UH), ext=(-7.0, 7.0, -1.0, 10.0), ray=1.2,
              floors=[('HALL', _r4p(WL_UHALL)), ("BOYS'", _r4p(WL_BOYS)), ("PARENTS'", _r4p(WL_PAR)), ("Theo's", _r4p(WL_TCL)), ("Sam's", _r4p(WL_SCL)),
                      ('DEAD SPACE', _r4p(WL_DEAD)), ('hall closet (hatch)', _r4p(WL_HCL)), ('bath (not built)', _r4p((-6.0, -0.6, 0.0, 4.6)))],
              blocks=blocks(bo, pa),
              doors=[((0.8, WL_BDOOR[0]), (0.8, WL_BDOOR[1]), "boys'"), ((-0.6, WL_PARDOOR[0]), (-0.6, WL_PARDOOR[1]), "parents' (lock)"),
                     ((0.8, WL_HCDOOR[0]), (0.8, WL_HCDOOR[1]), 'closet'), ((2.3, 4.8), (3.1, 4.8), ''), ((3.75, 4.8), (4.55, 4.8), '')],
              windows=[((WL_BWIN[0], 0.0), (WL_BWIN[1], 0.0)), ((WL_PWIN[0], 9.0), (WL_PWIN[1], 9.0)), ((-6.0, 4.75), (-6.0, 5.55))],
              lines=[[(WL_HATCH[0], WL_HATCH[2]), (WL_HATCH[1], WL_HATCH[2]), (WL_HATCH[1], WL_HATCH[3]), (WL_HATCH[0], WL_HATCH[3]), (WL_HATCH[0], WL_HATCH[2])]],
              marks=marks(bo, ('doorway', 'theo_kneel', 'sam_wall', 'marks')) + marks(hl, ('switch',)) + marks(pa, ('vent', 'lock', 'phone')) + marks(de, ('gone_forever',)),
              cams=[k for k in WL_CAMS if CAMS[k]['room'] in ('hall', 'boys', 'parents', 'dead')])]
    ex = wl_street('house')
    P.append(dict(title='LARKSPUR LANE  (ground Y %.1f; road %.2f)' % (WL_G, WL_ROAD), ext=(-16.0, 16.0, -34.0, 11.0), ray=4.0,
                  floors=[('Larkspur Lane', [(-16, WL_KS), (16, WL_KS), (16, WL_KN), (-16, WL_KN)]), ('driveway', _r4p(WL_DRIVE)), ('porch', _r4p(WL_PORCH))],
                  blocks={'our house': _r4p(WL_HOUSE), 'garage': _r4p(WL_GAR), "Mrs. Dabrowski's": _r4p(WL_DAB)},
                  doors=[((WL_FDOOR[0], 0.0), (WL_FDOOR[1], 0.0), ''), ((WL_DABDOOR[0], WL_DAB[3]), (WL_DABDOOR[1], WL_DAB[3]), '')], windows=[],
                  lines=[], marks=marks(ex, ('frog', 'keypad', 'curb_sit', 'police_0', 'police_1', 'police_2', 'dab_door')),
                  cams=[k for k in WL_CAMS if CAMS[k]['room'] == 'street']))
    return P


def wl_plan_map(path, pw=900, ph=1000, cols=3):
    """This film's floor plans with every camera -> JPEG (the Doctor film's renderer on this film's panels)."""
    import inspect
    src = inspect.getsource(dr_plan_map).replace('def dr_plan_map(', 'def _wl_plan_map_impl(').replace('_dr_plan_panels()', '_wl_plan_panels()')
    ns = dict(globals()); exec(src, ns)
    return ns['_wl_plan_map_impl'](path, pw, ph, cols)


WL_SETS = {'wl_street': wl_street, 'wl_living': wl_living, 'wl_kitchen': wl_kitchen, 'wl_hall': wl_hall, 'wl_boys': wl_boys, 'wl_parents': wl_parents,
           'wl_dead': wl_dead, 'wl_insert': wl_insert}
WL_API = {nm: sorted({k[len(pre):] for k in WL_CAMS if k.startswith(pre)}) for nm, pre in (
    ('wl_street', 'wl_ext_'), ('wl_living', 'wl_liv_'), ('wl_kitchen', 'wl_kit_'), ('wl_hall', 'wl_hall_'), ('wl_boys', 'wl_boys_'),
    ('wl_parents', 'wl_par_'), ('wl_dead', 'wl_dead_'))}
WL_API['wl_insert'] = sorted(WL_INSERTS)
__all__ += ['wl_street', 'wl_living', 'wl_kitchen', 'wl_hall', 'wl_boys', 'wl_parents', 'wl_dead', 'wl_insert', 'wl_plan_map', 'wl_police', 'wl_frog',
            'WL_API', 'WL_INSERTS', 'WL_RULES', 'WL_RULE7', 'WL_NOTE_LINES', 'WL_CAMS', 'WL_POLICE_CARS']
