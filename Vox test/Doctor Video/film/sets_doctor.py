"""sets_doctor.py: the sets of "If Your Doctor Calls At 3 AM... DON'T ASK WHAT THEY FOUND".

Run inside sets.py's namespace at import, after sets_bunny.py (like characters_doctor.py inside characters.py), so it
reuses the Bunnyman film's set engine (BView cameras on a plan in metres, per-face light maps, BSet staging API) and
everything here is part of `sets`:  import sets as ST;  sp = ST.dr_living('wide', state='wait').  The older films'
builders are unchanged; every new name starts with dr_ / DR_ / D_ / _d. See SETS.md (staging guide) and DR_API below.

RUTH'S HOUSE: one floor plan in metres. x = east (right when you face the back of the house), y = from the front wall
(Larch Street, y 0) back toward the yard, Y = up; floor Y 0, ceiling D_CEIL 2.55, the yard / driveway D_GROUND -0.5.
Living room (Grandpa's brown armchair by the picture window; the waiting room is this room transformed), hall (front door
with peephole; the living-room DOOR, the kitchen doorway, the bathroom door), kitchen (wall phone + cord + jack, counter,
sink under the window, fridge, wall clock), bathroom (the mirrored medicine cabinet with the yellow card inside its door).
Outside: the porch, the driveway with Doctor Halverson's car (nose to the house, headlights on), Larch Street and, at its
west end, the bus stop under the flickering streetlight. Every view is a camera on this plan (DR_CAMS / ST.plan_map), so
a cut keeps every wall, door, lamp and chair where the last shot had it.

STAGING DATA (sp = any builder's result; same API as the Bunnyman sets):
  sp.anchors[name] -> Spot (.x .y design px of the feet / point, .depth, .ppm px per metre there, .height of a 1.85 m adult,
                     .X .Yp .Y plan point, .kind 'stand'|'seat'|'kneel'|'lie'|'surface'|'point'|'floor_sit', .turn, .seat_y)
  sp.spot(x, y, Y), sp.ppm_at(x, y), sp.floor_y(x, y), sp.pick(sx, sy), sp.turn_for(x, y, fx, fy), sp.walkable(x, y),
  sp.order_at(x, y) (furniture-aware draw order), sp.light_kw(x, y, Y) (figure tint / dim), sp.shadow(x, y)
  ST.stage_figure(sp, who, spot, ...) -> (Layer, Acting): the one-call staging recipe (height, feet, facing, seat, light).
  Depth-to-scale rule: ppm = S / depth (depth along the view axis); a figure of real height m is m * ppm px tall at its feet.
  sp.info: 'view' (BView), 'cam_env' (allowed camera move), 'floors', 'blocks' (furniture footprints), plus per set:
  'mirror_quad' (bathroom / car mirror screen quads), 'roof_y' (car), 'wheel' (car steering wheel centre + radius), ...
"""
import math
import numpy as np
import skia

# ====================================================================================================== plan + palette
D_CEIL = 2.55
D_GROUND = -0.5                                               # the yard, the driveway and the street are 0.5 m below the floor
D_HOUSE = (-5.6, 4.6, 0.0, 9.6)
D_LIV = (-5.6, -1.2, 0.0, 5.4)
D_HALL = (-1.2, 0.4, 0.0, 9.6)
D_KIT = (-5.6, -1.2, 5.4, 9.6)
D_BATH = (0.4, 2.8, 5.8, 9.6)
D_FDOOR = (-0.85, 0.05, 2.03)        # front door on y 0 (x0, x1, h): hinge at x0 (west), swings into the hall; knob east
D_LDOOR = (2.2, 3.1, 2.03)           # the living-room door on x -1.2 (y0, y1, h): hinge at y0, swings into the living room
D_KDOOR = (6.0, 6.9, 2.05)           # the kitchen doorway on x -1.2 (no leaf)
D_BDOOR = (6.3, 7.05, 2.03)          # the bathroom door on x 0.4: hinge at y1, swings into the bathroom
D_RDOOR = (3.4, 4.2, 2.03)           # Ruth's bedroom door on x 0.4 (closed; the room is not built)
D_LWIN = (-4.6, -2.2, 0.75, 2.1)     # the living-room picture window on y 0 (x0, x1, sill, top)
D_SWIN = (3.9, 4.9, 0.85, 2.05)      # the living-room side window on x -5.6 (y0, y1, sill, top): Grandpa's last row
D_KWIN = (-3.9, -2.7, 1.0, 2.0)      # the kitchen window over the sink on y 9.6
D_HWIN = (-0.78, -0.02, 0.95, 1.95)  # the little window at the end of the hall on y 9.6
D_BWIN = (1.0, 1.6, 1.4, 1.95)       # the bathroom's frosted window on y 9.6 (over the tub)
D_RWIN = (1.6, 2.8, 0.85, 2.05)      # Ruth's bedroom front window on y 0 (seen from outside)
D_PEEP_Y, D_KNOB_Y = 1.5, 0.97

# living room furniture ('now'; 1979 swaps colours; the waiting room takes the couch, table and rug out)
D_ARM = Box(-3.95, 0.98, 0.95, 0.92, 0.0, 1.02, 180)          # Grandpa's brown armchair: back to the picture window, facing +y
D_ARM_SEAT = 0.46
D_SIDE = (-5.0, 0.72, 0.25, 0.62)                            # round side table left of the armchair (x, y, r, h): lamp, coffee
D_COUCH = Box(-3.45, 4.92, 2.0, 0.88, 0.0, 0.84, 0)          # couch along the back wall, facing the window
D_COUCH_SEAT = 0.45
D_COFFEE = Box(-3.45, 3.72, 1.05, 0.52, 0.0, 0.42, 0)
D_TV = Box(-1.78, 0.62, 0.86, 0.52, 0.0, 0.74, -160)         # the console TV in the front-east corner, facing the couch
D_CURIO = Box(-5.38, 2.0, 0.9, 0.4, 0.0, 1.8, 90)             # curio cabinet on the west wall, facing into the room (+x)
D_RUG = (-3.45, 3.0, 1.55, 1.05)
D_LCLOCK = (-1.2, 1.95, 4.35)                                # living-room wall clock on the east wall (x, Y, y)
# the waiting room (rule 6): three rows of four bolted plastic chairs facing the armchair, the ticket machine near the door,
# NOW SERVING 1979 over the armchair, the TV on a bracket in the front-east corner, four troffers (two dead, one flickering)
D_ROWS_Y = (2.35, 3.45, 4.55)
D_ROW_X = (-4.78, -4.26, -3.74, -3.22)
D_SEAT_H = 0.45
D_TICKET = (-1.72, 1.45)                                      # the take-a-number machine on its pole (x, y), dispenser at 1.18 m
D_TICKET_Y = 1.18
D_SIGN = (-3.95, 0.3, 2.06, 2.46)                            # NOW SERVING sign: centre x, y, bottom, top (hung from the ceiling)
D_TROFFERS = [(-4.55, 1.65), (-2.6, 1.65), (-4.55, 3.95), (-2.6, 3.95)]
# kitchen
D_KCOUNTER = (-5.6, -1.2, 8.98, 9.6)                         # the counter run along the back wall
D_KRETURN = (-1.82, -1.2, 8.0, 9.6)                          # the counter return along the east wall (under the phone's reach)
D_KSINK = (-3.72, -2.88)                                     # the sink bowl x range under the window
D_FRIDGE = Box(-5.24, 7.95, 0.78, 0.72, 0.0, 1.66, 90)        # the fridge on the west wall, facing +x
D_STOVE = Box(-4.62, 9.29, 0.76, 0.62, 0.0, 0.91, 0)         # in the back counter run, its front facing the room (-y)
D_KTABLE = Box(-3.55, 7.05, 1.1, 0.76, 0.0, 0.75, 0)
D_PHONE = (-1.2, 1.42, 7.45)                                 # the wall phone on the kitchen's east wall (x, Y of the base centre, y)
D_JACK = (-1.2, 0.3, 7.8)                                    # its wall jack on the baseboard (the line cord runs down to it)
D_KCLOCK = (-2.7, 1.98, 5.4)                                 # the kitchen clock on the front wall (x, Y, y)
D_COUNTER_Y = 0.92
# bathroom
D_CAB = (2.8, 6.47, 7.03, 1.25, 1.95)                        # medicine cabinet on the east wall: x, y0 (hinge), y1, Y0, Y1
D_BSINK = (2.55, 6.75)                                       # the pedestal sink under it (front edge x 2.32)
D_TOILET = (2.42, 7.75)
D_TUB = Box(1.25, 9.22, 1.7, 0.76, 0.0, 0.56, 0)              # along the back wall, its long side facing -y
# outside
D_DRIVE = (-8.7, -5.95, -12.2, -0.6)                         # the driveway (x0, x1, y0, y1) at D_GROUND, west of the house
D_CAR = (-7.3, -4.6)                                          # Halverson's car: centre (x, y) parked nose to the house
D_STREET = (-12.2, -19.0)                                    # Larch Street: kerb y (north) .. y (south); centre y -15.6
D_BUS = (-46.0, -20.4)                                       # the bus-stop bench at the west end, under the flickering light
D_PORCH = (-1.6, 0.85, -1.9, 0.0)                            # the front porch deck (x0, x1, y0, y1) at floor level
D_PLIGHT = (0.32, 1.95, -0.06)                               # the porch light by the door (x, Y, y)

DP = dict(
    trim='#f0e9da', ceil='#e6dfd2',
    liv_paper='#cdbf9e', liv_ink='#a0644a', liv_ink2='#7e8a62', carpet='#8a6a52', carpet_ink='#6a4c3a',
    liv79_paper='#d9a64a', liv79_ink='#a8481e', liv79_ink2='#6e5a1e', shag='#b05a26',
    wait_paper='#a8ad86', wait_ink='#7a7a52',
    hall_paper='#4a6258', hall_ink='#7a9486', hall_wains='#efe8d8', runner='#7a2630',
    kit_wall='#cfe3d2', kit_ink='#e8f2ea', cab='#f1ead8', cab_d='#c8bea6', counter='#f2d77a', floor_a='#ece6d8', floor_b='#33363c',
    bath_tile='#a8d0d8', bath_wall='#e8eef0', bath_floor='#f2f0ea',
    arm='#6e4128', arm_d='#4a2a18', arm79='#8e5432', arm79_d='#62361e',
    couch='#7a7a5a', couch_d='#55553c', couch79='#c87a2a', couch79_d='#8a4e18',
    siding='#b8c4cc', siding_d='#8e9aa4', roof='#3e3c42', door_red='#7e2a2a', brick='#8e4a3a',
)
D_NIGHT_AMB = '#2c3354'              # inside at night, lamps off (streetlight + moon through the windows)
D_LAMP = '#ffc98a'                   # tungsten
D_TUBE = '#d8f2a0'                   # the villain's fluorescent light: sickly green-yellow
D_HEAD = '#fff2d6'                   # Halverson's headlights
D_SODIUM = '#ffb060'                 # streetlights
D_SUN = '#ffbe72'                    # sunrise
D_CLINIC = '#fff6e8'                 # the doctors' world: warm, bright


# ====================================================================================================== grades
_GR = _epost.GRADES
_GR.setdefault('dr_night', dict(contrast=1.08, pivot=0.24, gamma=1.06, sat=1.12, wb=(1.0, 1.0, 1.02), floor='#070a16',
                                bloom=0.85, bloom_thr=226, vignette=0.38, grain=0.7, shoulder=0.45))
_GR.setdefault('dr_dark', dict(contrast=1.06, pivot=0.24, gamma=1.08, sat=1.05, wb=(0.95, 0.99, 1.08), floor='#05070f',
                               bloom=0.9, bloom_thr=224, vignette=0.34, grain=0.8, shoulder=0.45))
# the villain's world: sickly fluorescent green-yellow, crushed and dirty, the blacks lifted green
_GR.setdefault('dr_wait', dict(exposure=-0.02, contrast=1.14, pivot=0.26, gamma=1.0, sat=0.78, wb=(1.0, 1.06, 0.82), floor='#0c1008',
                               bloom=0.8, bloom_thr=222, vignette=0.32, grain=1.2, shoulder=0.5))
_GR.setdefault('dr_1979', dict(exposure=0.06, contrast=0.96, pivot=0.26, gamma=1.04, sat=0.82, wb=(1.08, 1.0, 0.84), floor='#160e0a',
                               bloom=0.8, bloom_thr=224, vignette=0.42, grain=1.3, soft=0.5, shoulder=0.5))
_GR.setdefault('dr_sunrise79', dict(exposure=0.12, contrast=0.98, pivot=0.26, gamma=1.04, sat=0.86, wb=(1.12, 1.0, 0.82), floor='#1a120c',
                                    bloom=1.0, bloom_thr=218, vignette=0.4, grain=1.2, soft=0.5, shoulder=0.55))
_GR.setdefault('dr_sunrise', dict(exposure=0.1, contrast=1.02, pivot=0.25, gamma=1.04, sat=1.04, wb=(1.08, 1.0, 0.9), floor='#120c10',
                                  bloom=0.95, bloom_thr=220, vignette=0.38, grain=0.6, shoulder=0.5))
_GR.setdefault('dr_ext', dict(contrast=1.1, pivot=0.22, gamma=1.0, sat=1.1, wb=(0.97, 1.0, 1.05), floor='#04060e',
                              bloom=1.0, bloom_thr=226, vignette=0.36, grain=0.8, shoulder=0.45))
# the doctors' world: warm, bright, clean, safe
_GR.setdefault('dr_clinic', dict(exposure=0.12, contrast=1.02, pivot=0.27, gamma=1.06, sat=1.08, wb=(1.04, 1.0, 0.96), floor='#141210',
                                 bloom=0.6, bloom_thr=236, vignette=0.55, grain=0.4, shoulder=0.55))
_GR.setdefault('dr_er', dict(exposure=0.1, contrast=1.04, pivot=0.26, gamma=1.05, sat=1.06, wb=(1.02, 1.0, 0.98), floor='#0e1012',
                             bloom=0.7, bloom_thr=234, vignette=0.5, grain=0.4, shoulder=0.55))
_GR.setdefault('dr_office', dict(contrast=1.06, pivot=0.24, gamma=1.06, sat=1.06, wb=(1.04, 1.0, 0.96), floor='#0a0a12',
                                 bloom=0.85, bloom_thr=226, vignette=0.4, grain=0.6, shoulder=0.5))
_GR.setdefault('dr_er_night', dict(exposure=0.06, contrast=1.08, pivot=0.23, gamma=1.03, sat=1.12, wb=(1.03, 1.0, 0.97), floor='#05070e',
                                   bloom=0.9, bloom_thr=228, vignette=0.38, grain=0.6, shoulder=0.5))
_GR.setdefault('dr_car', dict(contrast=1.1, pivot=0.22, gamma=1.02, sat=1.12, wb=(0.98, 1.0, 1.04), floor='#04060c',
                              bloom=1.0, bloom_thr=224, vignette=0.36, grain=0.7, shoulder=0.45))
_GR.setdefault('dr_hall_night', dict(contrast=1.1, pivot=0.24, gamma=1.0, sat=0.9, wb=(0.98, 1.03, 0.96), floor='#06080a',
                                     bloom=0.8, bloom_thr=226, vignette=0.3, grain=0.9, shoulder=0.5))
_GR.setdefault('dr_morning', dict(exposure=0.14, contrast=1.02, pivot=0.26, gamma=1.05, sat=1.1, wb=(1.06, 1.0, 0.92), floor='#14100c',
                                  bloom=0.9, bloom_thr=226, vignette=0.5, grain=0.4, shoulder=0.55))
_GR.setdefault('dr_ins', dict(contrast=1.04, pivot=0.25, gamma=1.04, sat=1.02, wb=(1.02, 1.0, 0.97), floor='#0a0808',
                              bloom=0.4, bloom_thr=240, vignette=0.5, grain=0.5, shoulder=0.5))
_GR.setdefault('dr_ins_wait', dict(contrast=1.12, pivot=0.26, gamma=1.0, sat=0.8, wb=(1.0, 1.05, 0.84), floor='#0a0e08',
                                   bloom=0.6, bloom_thr=230, vignette=0.36, grain=1.0, shoulder=0.5))
_GR.setdefault('dr_ins_bright', dict(exposure=0.08, contrast=1.02, pivot=0.27, gamma=1.05, sat=1.06, wb=(1.03, 1.0, 0.97), floor='#121010',
                                     bloom=0.4, bloom_thr=240, vignette=0.6, grain=0.3, shoulder=0.55))


# ====================================================================================================== small helpers
DR_CAMS = []                                                  # the names of this film's cameras (in CAMS)


def _dcam(name, S, h, eye, x, y, yaw, env=None, note='', room='', pitch=0.0):
    _cam(name, S, h, eye, x, y, yaw, env, note, room, pitch)
    if name not in DR_CAMS: DR_CAMS.append(name)


def _env(x=(880, 1040), y=(450, 600), zoom=(1.0, 1.12), f=(1.0, 1.8)):
    return dict(x=x, y=y, zoom=zoom, f=f)


def _r4p(r):
    x0, x1, y0, y1 = r
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _walls_of(r):
    """The four inside wall runs of a room rectangle, visible side inward: [(side, a, b, u(x, y))], side in
    front (y0) / west (x0) / back (y1) / east (x1); u = metres along a -> b."""
    x0, x1, y0, y1 = r
    return [('front', (x1, y0), (x0, y0), lambda x, y: x1 - x), ('west', (x0, y0), (x0, y1), lambda x, y: y - y0),
            ('back', (x0, y1), (x1, y1), lambda x, y: x - x0), ('east', (x1, y1), (x1, y0), lambda x, y: y1 - y)]


def _hole_x(u_of, xa, xb, ya, yb, v0, v1):
    """A hole (u0, v0, u1, v1) in a wall run for a plan span (xa, ya) .. (xb, yb)."""
    ua, ub = u_of(xa, ya), u_of(xb, yb)
    return (min(ua, ub), v0, max(ua, ub), v1)


def _box_pts(cx, cy, hw, hd):
    return [(cx - hw, cy - hd), (cx + hw, cy - hd), (cx + hw, cy + hd), (cx - hw, cy + hd)]


def _lvl(spec, seed, t=0.0):
    return _kfn(spec, seed)(t)


def _carpet_art(base, ink, seed=1, shag=False):
    def art(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'fabric', 0.7, 'overlay', 2.2)
        p_.texture(rect(0, 0, W, H), 'grunge', 0.35, 'overlay', 3.0)
        rng = np.random.default_rng(seed)
        n = int(W * H / (60 if shag else 420))
        for _ in range(min(n, 9000)):
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            if shag:
                a = rng.uniform(0, 6.28); L = rng.uniform(1.0, 2.4)
                p_.seg((x, y), (x + math.cos(a) * L, y + math.sin(a) * L), 0.7, mix(ink, '#ffffff', rng.uniform(0, 0.25)), 90)
            else:
                p_.fill(oval(x, y, rng.uniform(0.4, 1.0)), ink, 50)
    return art


def _rug_braided(p_, cx, cy, rx, ry, cols=('#6e3a2c', '#9a7a52', '#4a5a4a', '#b8a888', '#7a4a34', '#5a4a3a', '#8a6a4a')):
    rug_oval(p_, cx, cy, rx, ry, cols)


def _photo(p_, W, H, x, y, w, h, kind='grandpa', frame='#4a2e1c'):
    """A framed picture on a wall (cm frame, x, y = top-left): 'grandpa' (his portrait: moustache, brown cardigan),
    'wedding' (Ruth and Grandpa, 1960s), 'nurse' (Mom's nursing-school graduation, the cap), 'kids' (the narrator and
    Milo, school photo), 'milo' (Milo with a dinosaur), 'landscape', 'lake'."""
    def fn(q, w_, h_):
        if kind in ('grandpa', 'wedding', 'nurse', 'kids', 'milo'):
            q.linear(rect(0, 0, w_, h_), 0, 0, 0, h_, ['#b8a68a', '#7e6c56'] if kind in ('grandpa', 'wedding') else ['#8ab0d0', '#4a6a90'])
            people = {'grandpa': [(0.5, '#5a3a24', '#6e4128', 1.0, 'm')], 'wedding': [(0.33, '#5a3a24', '#2a2a30', 0.9, 'm'), (0.67, '#4a2a1a', '#f2efe6', 0.85, 'f')],
                      'nurse': [(0.5, '#3a2418', '#f4f4f0', 0.95, 'cap')], 'kids': [(0.36, '#4a3020', '#7a2430', 0.9, ''), (0.68, '#a87a4a', '#5aa070', 0.7, '')],
                      'milo': [(0.5, '#a87a4a', '#5aa070', 0.8, 'dino')]}[kind]
            for (u, hair, top, sz, tag) in people:
                x_ = w_ * u
                q.fill(smooth([(x_ - w_ * 0.2 * sz, h_), (x_ - w_ * 0.17 * sz, h_ * 0.64), (x_, h_ * 0.58), (x_ + w_ * 0.17 * sz, h_ * 0.64), (x_ + w_ * 0.2 * sz, h_)], True, 0.6), top)
                q.fill(oval(x_, h_ * (0.44 + 0.1 * (1 - sz)), w_ * 0.11 * sz, h_ * 0.12 * sz), '#e6c4a8')
                q.fill(oval(x_, h_ * (0.36 + 0.1 * (1 - sz)), w_ * 0.12 * sz, h_ * 0.06 * sz), hair)
                if tag == 'm': q.seg((x_ - w_ * 0.04, h_ * 0.5), (x_ + w_ * 0.04, h_ * 0.5), max(0.5, w_ * 0.02), '#4a2e1c')
                if tag == 'f': q.fill(oval(x_ + w_ * 0.1, h_ * 0.34, w_ * 0.12, h_ * 0.05), '#ffffff', 170)
                if tag == 'cap': q.fill(rect(x_ - w_ * 0.09, h_ * 0.27, w_ * 0.18, h_ * 0.05), '#ffffff')
                if tag == 'dino':
                    q.fill(smooth([(x_ + w_ * 0.12, h_ * 0.85), (x_ + w_ * 0.2, h_ * 0.7), (x_ + w_ * 0.32, h_ * 0.66), (x_ + w_ * 0.36, h_ * 0.75), (x_ + w_ * 0.26, h_ * 0.86)], True, 0.7), '#4aa86a')
        elif kind == 'lake':
            q.linear(rect(0, 0, w_, h_), 0, 0, 0, h_, ['#9ab8d0', '#e8d8b0'])
            q.fill(poly([(0, h_ * 0.6), (w_ * 0.3, h_ * 0.35), (w_ * 0.55, h_ * 0.55), (w_ * 0.8, h_ * 0.4), (w_, h_ * 0.55), (w_, h_ * 0.62), (0, h_ * 0.62)]), '#5a6a5a')
            q.fill(rect(0, h_ * 0.62, w_, h_ * 0.38), '#6a90b0')
        else:
            q.linear(rect(0, 0, w_, h_), 0, 0, 0, h_, ['#7a9ab0', '#d8c48a'])
            q.fill(poly([(0, h_ * 0.7), (w_ * 0.4, h_ * 0.45), (w_ * 0.7, h_ * 0.62), (w_, h_ * 0.5), (w_, h_), (0, h_)]), '#4a5a3a')
    _hframe(p_, W, H, x, y, w, h, 'poster', frame=frame, fn=fn)


def _sunburst_clock(p_, x, y, r, hh=3, mm=0, c='#c8a04a', face='#f4ecd8'):
    """A 1960s sunburst wall clock (cm frame centre x, y, radius r of the face)."""
    for k in range(16):
        a = 2 * math.pi * k / 16
        L = r * (2.2 if k % 2 == 0 else 1.7)
        p_.seg((x + math.cos(a) * r, y + math.sin(a) * r), (x + math.cos(a) * L, y + math.sin(a) * L), max(0.8, r * 0.12), c)
        p_.fill(oval(x + math.cos(a) * L, y + math.sin(a) * L, r * 0.1), _lighten(c, 0.2))
    p_.fill(oval(x + 0.8, y + 1.5, r), '#000000', 70)
    p_.fill(oval(x, y, r), c); p_.fill(oval(x, y, r * 0.86), face)
    _hands(p_, x, y, r * 0.86, hh, mm)


def _hands(p_, x, y, r, hh, mm, ss=None, col_='#1a1a1a'):
    for k in range(12):
        a = 2 * math.pi * k / 12
        p_.seg((x + math.sin(a) * r * 0.78, y - math.cos(a) * r * 0.78), (x + math.sin(a) * r * 0.92, y - math.cos(a) * r * 0.92), max(0.5, r * 0.06), '#2a2a2a')
    am = 2 * math.pi * mm / 60; ah = 2 * math.pi * ((hh % 12) + mm / 60) / 12
    p_.seg((x, y), (x + math.sin(ah) * r * 0.5, y - math.cos(ah) * r * 0.5), max(0.8, r * 0.1), col_)
    p_.seg((x, y), (x + math.sin(am) * r * 0.78, y - math.cos(am) * r * 0.78), max(0.6, r * 0.065), col_)
    if ss is not None:
        a_ = 2 * math.pi * ss / 60
        p_.seg((x - math.sin(a_) * r * 0.15, y + math.cos(a_) * r * 0.15), (x + math.sin(a_) * r * 0.85, y - math.cos(a_) * r * 0.85), max(0.4, r * 0.03), '#c82a2a')
    p_.fill(oval(x, y, max(0.6, r * 0.07)), '#a8262a')


def _office_clock(p_, x, y, r, hh=3, mm=0, ss=None):
    """An institutional wall clock: black rim, white face, numerals (the waiting room's: 'the clock on the wall')."""
    p_.fill(oval(x + 1.0, y + 1.8, r * 1.08), '#000000', 80)
    p_.fill(oval(x, y, r * 1.08), '#1e2024'); p_.fill(oval(x, y, r * 0.98), '#f2f0e8')
    p_.radial(oval(x, y, r * 0.98), x - r * 0.3, y - r * 0.4, r * 1.4, [(0, '#ffffff', 60), (1, '#000000', 30)])
    for k in range(1, 13):
        a = 2 * math.pi * k / 12
        btext(p_, str(k), x + math.sin(a) * r * 0.74, y - math.cos(a) * r * 0.74 + r * 0.07, 'sans_b', r * 0.19, '#1a1a1a', 230, 'center')
    _hands(p_, x, y, r * 0.98, hh, mm, ss)


def _notice(p_, x, y, w, h, title, lines=(), c='#f4f0e2', ink='#2a3a3a', accent='#3a6a5a', tape=True, font='sans_b'):
    """A paper notice pinned / taped on a wall (cm frame)."""
    p_.fill(rect(x + 0.6, y + 1.0, w, h), '#000000', 70)
    p_.fill(rect(x, y, w, h), c)
    p_.texture(rect(x, y, w, h), 'paper', 0.5, 'multiply', 0.4)
    p_.fill(rect(x, y, w, h * 0.2), accent)
    btext(p_, title, x + w / 2, y + h * 0.15, font, h * 0.1, '#ffffff', 240, 'center')
    for i, s in enumerate(lines):
        btext(p_, s, x + w / 2, y + h * (0.36 + 0.15 * i), 'sans', h * 0.075, ink, 220, 'center')
    if tape:
        for sx in (x + 1, x + w - 5):
            p_.fill(rect(sx, y - 1.2, 4, 2.6), '#f2e8b8', 170)


def _wall_jack(p_, x, y, plugged=True):
    p_.fill(rrect(x - 3.2, y - 4.2, 6.4, 8.4, 0.8), '#ece4d0'); p_.line(rrect(x - 3.2, y - 4.2, 6.4, 8.4, 0.8), 0.5, '#000000', 140)
    p_.fill(rect(x - 1.2, y - 0.9, 2.4, 1.8), '#1a1a1a')
    if plugged: p_.fill(rect(x - 1.4, y - 1.1, 2.8, 2.2), '#d8d2c0'); p_.line(rect(x - 1.4, y - 1.1, 2.8, 2.2), 0.4, '#000000', 160)


# ---------------------------------------------------------------------------------------------- rain (live, screen space)
def dr_rain(pen, t, box=(-400, -300, 2720, 1680), k=1.0, seed=3, speed=1.0, angle=0.12, c='#c8d4ec', a=46, n=420, far=False, L=None, w=None):
    """Falling rain streaks over a design-space box (a live layer; cheap: n short lines). far=True: thin, slow, dense haze.
    L / w: streak length / width in px (rain seen far away, in a lamp's cone or a headlight beam, is short and fine)."""
    x0, y0, x1, y1 = box
    if k <= 0.01: return
    rng = np.random.default_rng(seed)
    W, H = x1 - x0, y1 - y0
    N = int(n * k)
    xs = rng.uniform(0, 1, N); ys = rng.uniform(0, 1, N); ln = rng.uniform(0.6, 1.4, N)
    sp = (1.8 if not far else 0.9) * speed
    L = (60 if not far else 26) if L is None else L
    w = (1.6 if not far else 1.0) if w is None else w
    path = skia.Path()
    for i in range(N):
        yy = y0 + ((ys[i] + t * sp * (0.8 + 0.4 * ln[i])) % 1.0) * (H + L) - L
        xx = x0 + xs[i] * W + (yy - y0) * angle
        xx = x0 + ((xx - x0) % W)
        path.moveTo(xx, yy); path.lineTo(xx + L * ln[i] * angle, yy + L * ln[i])
    p = skia.Paint(Color=col(c, int(a * (1.0 if not far else 0.8))), AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                   StrokeCap=skia.Paint.kRound_Cap)
    pen.cv.drawPath(path, p)


def dr_glass_rain(pen, t, quad_path, bounds, k=1.0, seed=5, lit_c='#9aa8c8'):
    """Raindrops on a window pane and a few rivulets running down it (live; clipped to the projected glass)."""
    if k <= 0.01 or quad_path is None or quad_path.isEmpty(): return
    x0, y0, x1, y1 = bounds
    rng = np.random.default_rng(seed)
    cv = pen.cv
    cv.save(); cv.clipPath(quad_path, skia.ClipOp.kIntersect, True)
    W, H = x1 - x0, y1 - y0
    s = max(3.0, W / 90.0)
    for i in range(int(260 * k)):
        x, y = x0 + rng.uniform(0, W), y0 + rng.uniform(0, H)
        r = s * rng.uniform(0.08, 0.26)
        pen.fill(oval(x, y, r * 0.7, r * 0.85), lit_c, 48)
        pen.fill(oval(x, y + r * 0.35, r * 0.5, r * 0.35), '#000000', 30)
        pen.fill(oval(x - r * 0.15, y - r * 0.25, r * 0.2), '#ffffff', 60)
    for i in range(int(6 * k)):
        x = x0 + rng.uniform(0.05, 0.95) * W
        ph = (t * rng.uniform(0.06, 0.16) + rng.uniform(0, 1)) % 1.0
        ya, yb = y0 + H * max(0.0, ph - 0.3), y0 + H * ph
        pts = [(x + s * 0.4 * math.sin(yy * 0.05 + i), yy) for yy in np.linspace(ya, yb, 8)]
        pen.line(smooth(pts, False, 0.8), s * 0.1, lit_c, 70)
        pen.fill(oval(pts[-1][0], pts[-1][1], s * 0.16, s * 0.22), lit_c, 110)
    cv.restore()


# ====================================================================================================== furniture
def dr_armchair_parts(B=None, c=None, cd=None, era='now', doily=True, afghan=False):
    """Grandpa's brown armchair: a deep club recliner (since 1979). Short dark feet, a skirted base, a puffy seat cushion,
    padded rolled arms, a tall rounded back with a pillow-top cushion, the wooden recline lever on its right side; 'now'
    it is worn (rubbed arms, a crocheted doily on the headrest); era '1979' it is new (brighter velour)."""
    B = B or D_ARM
    c = c or (DP['arm79'] if era == '1979' else DP['arm'])
    cd = cd or (DP['arm79_d'] if era == '1979' else DP['arm_d'])
    w2, d2 = B.w / 2, B.d / 2
    P = []
    for (u, n) in ((-w2 + 0.09, -d2 + 0.09), (w2 - 0.09, -d2 + 0.09), (-w2 + 0.09, d2 - 0.09), (w2 - 0.09, d2 - 0.09)):
        P.append(Part(sub(B, u - 0.03, u + 0.03, n - 0.03, n + 0.03, 0.0, 0.07), {'all': '#2a180c'}))
    P.append(Part(sub(B, -w2 + 0.04, w2 - 0.04, -d2 + 0.05, d2 - 0.03, 0.07, 0.3), {'all': dict(fill=cd, art=_cushion_art(cd)),
                                                                                   'front': dict(fill=c, art=_skirt_art(c))}))
    seat_c = _lighten(c, 0.06)
    P.append(Part(fn=lambda pen, v: box_extrude(pen, v, B, -w2 + 0.2, w2 - 0.2, -d2 + 0.24, d2 - 0.01, 0.3, D_ARM_SEAT,
                                                 lambda W, H: rounded_rect_pts(W, H, 6.0, 2.0, bulge=2.2), seat_c, _darken(c, 0.04),
                                                 _cushion_art(seat_c, cd)), ref=B.at(0, 0.1, 0.38), tag='seat'))

    def back(pen, v):
        U3 = (B.U[0], 0.0, B.U[1]); N3 = (B.N[0], 0.0, B.N[1])
        W, H = (B.w - 0.06) * 100, (B.Y1 - 0.3) * 100

        def art(p_, W_, H_):
            _cushion_art(c, cd)(p_, W_, H_)
            for k in (0.3, 0.55):                                          # channel tufting
                p_.line(poly([(W_ * 0.22, H_ * k), (W_ * 0.78, H_ * k)], False), 1.2, cd, 120)
            if era != '1979':
                p_.fill(oval(W_ * 0.5, H_ * 0.16, W_ * 0.2, H_ * 0.07), '#000000', 30)       # the dark patch where his head rested
            if doily and era != '1979': _doily_shape(p_, W_ * 0.5, 16, 15, 10)
        extrude(pen, v, B.at(-w2 + 0.03, -d2 + 0.26, B.Y1), U3, (0.0, -1.0, 0.0), rounded_rect_pts(W, H, 22.0, 2.0, bulge=1.5),
                _scale3(N3, -0.24), c, _darken(c, 0.15), art, art_back=_cushion_art(_darken(c, 0.06), cd))
    P.append(Part(fn=back, ref=B.at(0, -d2 + 0.12, 0.7), tag='back'))
    for s_ in (-1, 1):
        u0, u1 = (-w2, -w2 + 0.2) if s_ < 0 else (w2 - 0.2, w2)

        def arm(pen, v, u0=u0, u1=u1):
            def art(p_, W, H):
                _arm_roll_art(c, cd)(p_, W, H)
                if era != '1979': p_.fill(oval(W / 2, H * 0.12, W * 0.32, H * 0.06), '#e8d0b0', 34)      # rubbed shiny
            box_extrude(pen, v, B, u0, u1, -d2 + 0.12, d2, 0.07, 0.66, lambda W, H: _arm_profile(W, H), c, _darken(c, 0.1), art)
        P.append(Part(fn=arm, ref=B.at((u0 + u1) / 2, 0.12, 0.4), tag='arm_l' if s_ < 0 else 'arm_r'))
    # the recline lever (the chair's right side = screen left when it faces the camera)
    def lever(pen, v):
        p0 = B.at(w2 + 0.012, 0.18, 0.36); p1 = B.at(w2 + 0.03, 0.26, 0.52)
        if v.d(p0[0], p0[2]) < 0.2: return
        a_, b_ = v.p(*p0), v.p(*p1); s = v.s(p0[0], p0[2])
        pen.seg(a_, b_, max(2.0, 0.03 * s) + 2, LINE); pen.seg(a_, b_, max(1.5, 0.03 * s), lit('#7a4a24', p0, None))
        pen.fill(oval(b_[0], b_[1], max(1.5, 0.022 * s)), lit('#8a5a2c', p1, None))
    P.append(Part(fn=lever, ref=B.at(w2 + 0.02, 0.2, 0.4), tag='lever'))
    if afghan:
        P.append(Part(fn=lambda pen, v: _afghan_over(pen, v, B), ref=B.at(0, -d2 + 0.3, 0.8), tag='back'))
    return P


def _afghan_over(pen, v, B):
    F = Face(B.at(-0.3, -B.d / 2 + 0.29, B.Y1 - 0.02), (B.U[0], 0, B.U[1]), (0, -1, 0), 60.0, 30.0, (B.N[0], 0, B.N[1]), 'front')
    shape = poly([(0, 0), (60, 0), (60, 20), (52, 30), (44, 20), (36, 30), (28, 20), (20, 30), (12, 20), (4, 30), (0, 22)])
    draw_face(pen, v, F, _afghan_art, '#2a1e1a', shape=shape, ao=False, lw=1.0)


def dr_arm_seat():
    p_ = D_ARM.at(0, -D_ARM.d / 2 + 0.42, 0)
    return (p_[0], p_[2])


def _round_table(pen, v, x, y, r, h, top='#6a3e22'):
    """A small round wooden side table (three splayed legs)."""
    s = v.s(x, y)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        fx, fy = x + math.cos(a) * r * 0.75, y + math.sin(a) * r * 0.75
        p0 = v.p(x + math.cos(a) * r * 0.35, h - 0.05, y + math.sin(a) * r * 0.35); p1 = v.p(fx, 0.0, fy)
        pen.seg(p0, p1, max(2.0, 0.035 * s) + 2, LINE); pen.seg(p0, p1, max(1.4, 0.035 * s), lit(_darken(top, 0.15), (fx, 0.3, fy), None))
    pen.fill(ellipse3(v, x, y, r, r, h - 0.03), lit(_darken(top, 0.25), (x, h, y), None))
    tp = ellipse3(v, x, y, r, r, h)
    pen.fill(tp, lit(top, (x, h, y), (0, 1, 0))); pen.line(tp, 1.2)


def dr_table_lamp(pen, v, x, y, Y, k=0.0, shade='#efe2c4', base='#b89a5a', h=0.52):
    """A table lamp standing at (x, Y, y): ginger-jar base, harp, pleated drum shade (k = lit)."""
    s = v.s(x, y)
    bx, by = v.p(x, Y, y)
    jar = smooth([(bx - 0.06 * s, by), (bx - 0.085 * s, by - 0.1 * s), (bx - 0.05 * s, by - 0.2 * s), (bx + 0.05 * s, by - 0.2 * s),
                  (bx + 0.085 * s, by - 0.1 * s), (bx + 0.06 * s, by)], True, 0.7)
    pen.fill(jar, lit(base, (x, Y + 0.1, y), None)); pen.line(jar, 1.0)
    pen.linear(jar, bx - 0.09 * s, 0, bx + 0.09 * s, 0, [(0, '#ffffff', 60), (0.4, '#ffffff', 0), (1, '#000000', 60)])
    pen.seg(v.p(x, Y + 0.2, y), v.p(x, Y + h - 0.2, y), max(1.0, 0.01 * s), lit('#c8a860', (x, Y + 0.3, y), None))
    _shade(pen, v, x, y, Y + h - 0.24, Y + h, 0.17, 0.12, shade, k)


def dr_lamp_glow(pen, v, x, y, Y, k, h=0.52, c='#ffd9a0'):
    if k <= 0.01: return
    _shade(pen, v, x, y, Y + h - 0.24, Y + h, 0.17, 0.12, '#efe2c4', k)
    gx, gy = v.p(x, Y + h - 0.12, y); s = v.s(x, y)
    pen.glow(gx, gy, 0.9 * s, c, 70 * k)
    pen.glow(gx, gy, 0.25 * s, '#fff2d8', 60 * k)


def dr_cup(pen, v, x, Y, y, c='#f2ece0', steam=0.0, t=0.0, coffee=True):
    """A coffee cup on its saucer at (x, Y, y) (vertex-lit), with a curl of steam (steam 0..1)."""
    s = v.s(x, y)
    if v.d(x, y) < 0.15: return
    sau = ellipse3(v, x, y, 0.075, 0.075, Y + 0.008)
    pen.fill(sau, lit(c, (x, Y, y), (0, 1, 0))); pen.line(sau, 0.8)
    top = ellipse3(v, x, y, 0.043, 0.043, Y + 0.085)
    b = _rb(top)
    cx_, cy_ = v.p(x, Y + 0.01, y)
    body = union(top, poly([(b[0], (b[1] + b[3]) / 2), (b[2], (b[1] + b[3]) / 2), (cx_ + 0.035 * s, cy_), (cx_ - 0.035 * s, cy_)]))
    pen.fill(body, lit(c, (x, Y + 0.05, y), None)); pen.line(body, 0.9)
    hx_, hy_ = v.p(x + 0.052, Y + 0.05, y)
    pen.line(oval(hx_, hy_, 0.016 * s, 0.022 * s), max(1.0, 0.009 * s), lit(c, (x, Y, y), None))
    pen.fill(top, '#e8e2d4'); pen.fill(ellipse3(v, x, y, 0.036, 0.036, Y + 0.082), '#4a2a16' if coffee else '#e8e2d4'); pen.line(top, 0.8)
    if steam > 0.01:
        for j in range(2):
            pts = [(cx_ + (j - 0.5) * 0.02 * s + 0.012 * s * math.sin(t * 1.6 + q * 0.9 + j * 2), cy_ - (0.1 + q * 0.035) * s) for q in range(7)]
            pen.line(smooth(pts, False, 0.8), max(1.0, 0.006 * s), '#ffffff', 60 * steam)


def dr_console_tv(pen, v, B=None, era='now', screen=0.0, t=0.0, wait=False):
    """The wooden console TV (four tapered legs, the screen, speaker cloth, knobs); era 1979 newer walnut; screen 0..1 =
    a dead grey-blue glow ('showing nothing')."""
    B = B or D_TV
    wood = '#5a3a22' if era == '1979' else '#4a3020'

    def front(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'wood', 0.6, 'overlay', 0.8, 90)
        sx, sy, sw, sh = W * 0.06, H * 0.12, W * 0.62, H * 0.62
        p_.fill(rrect(sx - 2, sy - 2, sw + 4, sh + 4, 5), '#2a1a10')
        p_.fill(rrect(sx, sy, sw, sh, 6), '#1c2226')
        p_.radial(rrect(sx, sy, sw, sh, 6), sx + sw * 0.35, sy + sh * 0.35, sw, [(0, '#5a6a72', 120), (1, '#000000', 0)])
        p_.fill(rect(W * 0.73, H * 0.12, W * 0.21, H * 0.45), '#3a2a1e'); pat(p_, W, H, 'stripe', '#000000', 0)
        for k in range(8): p_.seg((W * 0.74, H * (0.15 + k * 0.05)), (W * 0.93, H * (0.15 + k * 0.05)), 0.6, '#1a120a', 160)
        for k in range(2): p_.fill(oval(W * 0.835, H * (0.66 + k * 0.1), 2.0), '#c8b080'); p_.line(oval(W * 0.835, H * (0.66 + k * 0.1), 2.0), 0.5, '#000000', 160)
    body = Box(B.cx, B.cy, B.w, B.d, 0.22, B.Y1, B.fa)
    draw_box(pen, v, body, {'front': dict(fill=wood, art=front), 'top': dict(fill=_lighten(wood, 0.08), art=_wood_art), 'all': _darken(wood, 0.1)})
    w2, d2 = B.w / 2, B.d / 2
    for (u, n) in ((-w2 + 0.06, -d2 + 0.06), (w2 - 0.06, -d2 + 0.06), (-w2 + 0.06, d2 - 0.06), (w2 - 0.06, d2 - 0.06)):
        p0 = B.at(u, n, 0.22); p1 = B.at(u * 1.08, n * 1.05, 0.0)
        if v.d(p0[0], p0[2]) < 0.2: continue
        s = v.s(p0[0], p0[2])
        pen.seg(v.p(*p0), v.p(*p1), max(2.0, 0.025 * s) + 2, LINE); pen.seg(v.p(*p0), v.p(*p1), max(1.5, 0.025 * s), lit(wood, p0, None))
    # a framed photo of Grandpa and a little plant on top
    if era != '1979':
        P = B.at(-0.18, -0.05, B.Y1)
        if v.d(P[0], P[2]) > 0.3:
            s = v.s(P[0], P[2]); px, py = v.p(*P)
            fr = rect(px - 0.08 * s, py - 0.2 * s, 0.16 * s, 0.2 * s)
            pen.fill(fr, lit('#c8a860', P, None)); pen.fill(rect(px - 0.065 * s, py - 0.185 * s, 0.13 * s, 0.17 * s), lit('#8a7a64', P, None))
            pen.fill(oval(px, py - 0.12 * s, 0.025 * s, 0.03 * s), lit('#d8b8a0', P, None)); pen.line(fr, 0.9)


def dr_tv_screen_quad(B=None):
    """The console TV's screen as a 3D quad [(x, Y, y)] (for the glow)."""
    B = B or D_TV
    w2, d2 = B.w / 2, B.d / 2
    H = B.Y1 - 0.22
    u0, u1 = -w2 + B.w * 0.06, -w2 + B.w * 0.68
    Y1, Y0 = B.Y1 - H * 0.12, B.Y1 - H * 0.74
    n = d2 + 0.004
    return [B.at(u0, n, Y1), B.at(u1, n, Y1), B.at(u1, n, Y0), B.at(u0, n, Y0)]


def dr_curio(pen, v, B=None, era='now'):
    """Grandma's curio cabinet: dark wood, glass doors, plates and teacups on three shelves, photos on top."""
    B = B or D_CURIO

    def front(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'wood', 0.6, 'overlay', 0.8, 90)
        gx, gw = 6, W - 12
        for k, (y0, y1) in enumerate(((8, H * 0.32), (H * 0.35, H * 0.6), (H * 0.63, H * 0.85))):
            p_.fill(rect(gx, y0, gw, y1 - y0), '#2a2420')
            for j in range(3):                                            # plates on edge + cups
                cx_ = gx + gw * (0.2 + 0.3 * j)
                if k == 0: p_.fill(oval(cx_, y1 - 12, 10.5), '#f2ece0'); p_.line(oval(cx_, y1 - 12, 8), 0.7, '#4a7aa8', 200)
                else: p_.fill(rrect(cx_ - 5, y1 - 10, 10, 9, 2), ['#f2ece0', '#e8c8c8', '#c8d8e8'][j]); p_.line(rrect(cx_ - 5, y1 - 10, 10, 9, 2), 0.5, '#000000', 120)
            p_.fill(rect(gx, y1 - 1.2, gw, 1.2), '#5a4030')
            p_.linear(rect(gx, y0, gw, y1 - y0), gx, y0, gx + gw, y1, [(0, '#ffffff', 0), (0.3, '#ffffff', 40), (0.36, '#ffffff', 0)])
        p_.fill(rect(W / 2 - 0.8, 8, 1.6, H * 0.85 - 8), '#3a2418')
        p_.fill(rect(4, H * 0.88, W - 8, H * 0.1), '#4a3020'); p_.fill(oval(W / 2, H * 0.93, 1.5), '#c8a860')
    draw_box(pen, v, B, {'front': dict(fill='#5a3a26', art=front), 'top': dict(fill='#6a4630', art=_wood_art), 'all': '#4a2e1c'})


# ---------------------------------------------------------------------------------------------- plastic waiting-room chairs
D_CHAIR_BLUE = '#4a7aa0'
D_CHAIR_ER = '#3f8f8a'


def dr_chair_row(cx, cy, n=4, pitch=0.52, fa=0, c=D_CHAIR_BLUE, frame='#8a9098', empty=(), worn=0.0):
    """A row of n moulded plastic chairs bolted to one steel beam (Box frame fa: 0 = the seats face -y). Returns the
    parts and the seat plan points [(x, y)] (left to right seen from the front)."""
    L = n * pitch
    B = Box(cx, cy, L, 0.5, 0.0, 0.85, fa)
    P = []
    for u in (-L / 2 + 0.05, L / 2 - 0.05) + tuple(-L / 2 + pitch * k for k in range(1, n)):
        for nn in (-0.17, 0.17):                                           # splayed steel legs at the ends and between seats
            P.append(Part(sub(B, u - 0.018, u + 0.018, nn - 0.018, nn + 0.018, 0.0, 0.36), {'all': frame}, tag='leg'))
    seats = []
    for k in range(n):
        u = -L / 2 + pitch * (k + 0.5)
        cc = mix(c, '#9a9a8a', worn * _h(k, int(cx * 10)))
        def seat_fn(pen, v, u_=u, cc_=cc):
            # the steel beam the row is bolted to runs under every seat: drawn first, so the pan always covers it
            draw_box(pen, v, sub(B, u_ - pitch / 2 - 0.004, u_ + pitch / 2 + 0.004, -0.04, 0.04, 0.33, 0.385), {'all': _darken(frame, 0.2)})
            box_extrude(pen, v, B, u_ - pitch / 2 + 0.025, u_ + pitch / 2 - 0.025, -0.2, 0.23, 0.38, D_SEAT_H,
                        lambda W, H: rounded_rect_pts(W, H, 2.5, 3.0, bulge=-1.2), cc_, _darken(cc_, 0.18))
        P.append(Part(fn=seat_fn, ref=B.at(u, 0.02, 0.42), tag='seat'))
        # the back: a curved moulded shell tilted back, on a steel spine
        def back(pen, v, u_=u, cc_=cc):
            U3 = (B.U[0], 0.0, B.U[1]); N3 = (B.N[0], 0.0, B.N[1])
            tilt = 0.16
            V3 = _norm3((-N3[0] * tilt, -1.0, -N3[2] * tilt))
            O = B.at(u_ - pitch / 2 + 0.035, -0.2 - tilt * 0.4, 0.84)
            extrude(pen, v, O, U3, V3, rounded_rect_pts((pitch - 0.07) * 100, 34.0, 6.0, 3.0, bulge=1.0), _scale3(N3, -0.025), cc_, _darken(cc_, 0.2),
                    lambda p_, W, H, c_=cc_: p_.linear(rect(0, 0, W, H), 0, 0, 0, H, [(0, '#ffffff', 40), (0.5, '#ffffff', 0), (1, '#000000', 40)]))
            a_, b_ = B.at(u_, -0.21, 0.4), B.at(u_, -0.25, 0.52)
            if v.d(a_[0], a_[2]) > 0.2:
                s = v.s(a_[0], a_[2]); pen.seg(v.p(*a_), v.p(*b_), max(1.5, 0.02 * s) + 1.5, LINE); pen.seg(v.p(*a_), v.p(*b_), max(1.2, 0.02 * s), lit(frame, a_, None))
        P.append(Part(fn=back, ref=B.at(u, -0.22, 0.65), tag='back'))
        sp_ = B.at(u, -0.02, 0)
        seats.append((sp_[0], sp_[2]))
    return P, seats, B


def dr_rows_layout():
    """The waiting room's rows: [(row index, Box centre (x, y))]: three rows of four facing the armchair (-y)."""
    cx = sum(D_ROW_X) / len(D_ROW_X)
    return [(i, (cx, y)) for i, y in enumerate(D_ROWS_Y)]


# ---------------------------------------------------------------------------------------------- the waiting room's fixtures
def dr_ticket_machine(pen, v, x=None, y=None, ticket='', tear=0.0, era='wait'):
    """The red take-a-number dispenser on its chrome pole with a heavy round base and a TAKE A NUMBER plate; a strip of
    tickets hangs from the slot (ticket = the text on the hanging one; tear 0..1 = the front ticket pulled away)."""
    x = D_TICKET[0] if x is None else x; y = D_TICKET[1] if y is None else y
    if v.d(x, y) < 0.25: return
    s = v.s(x, y)
    base = ellipse3(v, x, y, 0.2, 0.2, 0.0)
    pen.fill(ellipse3(v, x, y, 0.2, 0.2, 0.03), lit('#3a3c40', (x, 0.03, y), (0, 1, 0)))
    pen.fill(base, lit('#2a2c30', (x, 0.0, y), None)); pen.line(base, 1.0)
    p0, p1 = v.p(x, 0.03, y), v.p(x, D_TICKET_Y - 0.1, y)
    pen.seg(p0, p1, max(2.0, 0.035 * s) + 2, LINE); pen.seg(p0, p1, max(1.5, 0.035 * s), lit('#c8ccd0', (x, 0.6, y), None))
    pen.seg((p0[0] - 0.006 * s, p0[1]), (p1[0] - 0.006 * s, p1[1]), max(0.6, 0.006 * s), '#ffffff', 90)
    # the TAKE A NUMBER plate on the pole
    pl = v.p(x, 0.98, y)
    plate = rrect(pl[0] - 0.13 * s, pl[1] - 0.05 * s, 0.26 * s, 0.1 * s, 0.012 * s)
    pen.fill(plate, lit('#f2efe6', (x, 0.98, y), None)); pen.line(plate, 0.9)
    btext(pen, 'TAKE A NUMBER', pl[0], pl[1] + 0.012 * s, 'sans_b', 0.036 * s, '#b8201e', 240, 'center')
    # the dispenser: a red rounded body with a black nose and the ticket slot
    cx_, cy_ = v.p(x, D_TICKET_Y, y)
    body = smooth([(cx_ - 0.12 * s, cy_ + 0.07 * s), (cx_ - 0.14 * s, cy_ - 0.04 * s), (cx_ - 0.07 * s, cy_ - 0.11 * s), (cx_ + 0.07 * s, cy_ - 0.11 * s),
                   (cx_ + 0.14 * s, cy_ - 0.04 * s), (cx_ + 0.12 * s, cy_ + 0.07 * s)], True, 0.8)
    pen.fill(body, lit('#c41e22', (x, D_TICKET_Y, y), None)); pen.line(body, 1.2)
    pen.linear(body, cx_ - 0.14 * s, 0, cx_ + 0.14 * s, 0, [(0, '#ffffff', 50), (0.35, '#ffffff', 0), (1, '#000000', 70)])
    pen.fill(oval(cx_ - 0.06 * s, cy_ - 0.07 * s, 0.03 * s, 0.015 * s), '#ffffff', 90)
    nose = rrect(cx_ - 0.05 * s, cy_ + 0.03 * s, 0.1 * s, 0.05 * s, 0.01 * s)
    pen.fill(nose, '#1a1a1c'); pen.line(nose, 0.9)
    # the ticket strip: a few tickets hanging out of the slot, the front one with its number / name
    tw, th = 0.055 * s, 0.075 * s
    for k in range(3):
        ty = cy_ + 0.08 * s + k * th
        if k == 0 and tear > 0.0: continue
        tk = rect(cx_ - tw / 2, ty, tw, th - 0.004 * s)
        cc = '#f2ead2' if era == 'wait' else '#f4f0e4'
        pen.fill(tk, lit(cc, (x, D_TICKET_Y - 0.1, y), None)); pen.line(tk, 0.6, '#3a3a3a', 160)
        if k == 0 and ticket:
            btext(pen, ticket, cx_, ty + th * 0.6, 'sans_b', max(3.0, th * 0.32), '#9a1a1a', 220, 'center')
        pen.dashed(poly([(cx_ - tw / 2, ty + th - 0.004 * s), (cx_ + tw / 2, ty + th - 0.004 * s)], False), max(0.5, 0.004 * s), '#5a5a5a', 160, 2, 2)


def dr_now_serving(pen, v, digits='1979', k=1.0, lit_=True, x=None, y=None, Y0=None, Y1=None, label=True):
    """The NOW SERVING sign hung on two chains from the ceiling: a black box, the label in white, four red seven-segment
    digits that stopped a long time ago (k = their glow)."""
    x = D_SIGN[0] if x is None else x; y = D_SIGN[1] if y is None else y
    Y0 = D_SIGN[2] if Y0 is None else Y0; Y1 = D_SIGN[3] if Y1 is None else Y1
    w = 1.0
    if v.d(x, y) < 0.3: return
    s = v.s(x, y)
    for sx in (-0.38, 0.38):                                             # chains
        a_, b_ = v.p(x + sx, D_CEIL, y), v.p(x + sx, Y1, y)
        pen.dashed(poly([a_, b_], False), max(0.8, 0.008 * s), '#5a5a5a', 230, max(1.5, 0.012 * s), max(0.8, 0.006 * s))
    if v.hy > y: F = Face((x + w / 2, Y1, y + 0.03), (-1, 0, 0), (0, -1, 0), w * 100, (Y1 - Y0) * 100, (0, 0, 1), 'front')
    else: F = Face((x - w / 2, Y1, y - 0.03), (1, 0, 0), (0, -1, 0), w * 100, (Y1 - Y0) * 100, (0, 0, -1), 'front')

    def art(p_, W, H):
        p_.fill(rect(0, 0, W, H), '#141416')
        p_.fill(rect(2, 2, W - 4, H - 4), '#0a0a0c')
        if label:
            btext(p_, 'NOW SERVING', W / 2, H * 0.27, 'sans_b', H * 0.17, '#e8e4dc', 235, 'center', spacing=0.08)
        dh = H * 0.5
        dw = len(digits) * (dh * 0.52 + dh * 0.22) - dh * 0.22
        _seg7_text(p_, digits, W / 2 - dw / 2, H * 0.38, dh, '#ff2a1e' if lit_ else '#3a0c0a', '#2a0a08')
    draw_face(pen, v, F, art, '#141416', ao=False, unlit=True, lw=1.4)
    # the box's depth (top edge)
    top = v.poly3([(x - w / 2, Y1, y - 0.03), (x + w / 2, Y1, y - 0.03), (x + w / 2, Y1, y + 0.03), (x - w / 2, Y1, y + 0.03)])
    if not top.isEmpty(): pen.fill(top, '#2a2a2e'); pen.line(top, 0.8)


_SEG = {'0': 'abcfed', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd', '6': 'afgedc', '7': 'abc', '8': 'abcdefg', '9': 'abcdfg',
        '-': 'g', ' ': ''}


def _seg7(p_, ch, x, y, h, on, off, slant=0.08):
    """One seven-segment digit (top-left x, y; height h) in a cm / px frame."""
    w = h * 0.52; t = h * 0.11
    segs = {'a': ((t * 0.6, 0), (w - t * 0.6, 0)), 'g': ((t * 0.6, h / 2), (w - t * 0.6, h / 2)), 'd': ((t * 0.6, h), (w - t * 0.6, h)),
            'f': ((0, t * 0.6), (0, h / 2 - t * 0.6)), 'b': ((w, t * 0.6), (w, h / 2 - t * 0.6)),
            'e': ((0, h / 2 + t * 0.6), (0, h - t * 0.6)), 'c': ((w, h / 2 + t * 0.6), (w, h - t * 0.6))}
    lit_s = _SEG.get(ch, '')
    for nm, (a_, b_) in segs.items():
        pa = (x + a_[0] + slant * (h - a_[1]), y + a_[1]); pb = (x + b_[0] + slant * (h - b_[1]), y + b_[1])
        p_.seg(pa, pb, t, on if nm in lit_s else off, 255 if nm in lit_s else 200)


def _seg7_text(p_, s, x, y, h, on, off):
    w = h * 0.52
    for i, ch in enumerate(s):
        _seg7(p_, ch, x + i * (w + h * 0.22), y, h, on, off)


def dr_sign_glow(pen, v, k=1.0):
    """The red digits' glow (emissive, drawn over the light map)."""
    if k <= 0.01: return
    x, y, Y0, Y1 = D_SIGN
    if v.d(x, y) < 0.3: return
    gx, gy = v.p(x + 0.12, (Y0 + Y1) / 2, y)
    s = v.s(x, y)
    pen.ellipse_glow(gx, gy, 0.6 * s, 0.2 * s, '#ff2a1e', 70 * k)


def dr_troffer(pen, v, x, y, k=0.0, w=1.2, d=0.6, c=D_TUBE, dead=False):
    """A 2 x 4 fluorescent ceiling troffer: steel frame, two tubes behind a prismatic diffuser (k = lit; dead tubes are
    grey with blackened ends)."""
    q = [(x - w / 2, D_CEIL - 0.005, y - d / 2), (x + w / 2, D_CEIL - 0.005, y - d / 2), (x + w / 2, D_CEIL - 0.005, y + d / 2), (x - w / 2, D_CEIL - 0.005, y + d / 2)]
    path = v.poly3(q)
    if path.isEmpty(): return
    pen.fill(path, '#d8dad4' if not dead else '#a8aaa4'); pen.line(path, 1.0, '#6a6c68')
    for j in (-1, 1):
        qq = [(x - w / 2 + 0.06, D_CEIL - 0.01, y + j * d * 0.22 - 0.05), (x + w / 2 - 0.06, D_CEIL - 0.01, y + j * d * 0.22 - 0.05),
              (x + w / 2 - 0.06, D_CEIL - 0.01, y + j * d * 0.22 + 0.05), (x - w / 2 + 0.06, D_CEIL - 0.01, y + j * d * 0.22 + 0.05)]
        tp = v.poly3(qq)
        if tp.isEmpty(): continue
        if dead or k <= 0.01:
            pen.fill(tp, '#9a9c94')
            for e in (0, 1):
                ex = x + (-w / 2 + 0.1 if e == 0 else w / 2 - 0.1)
                ep = v.poly3([(ex - 0.05, D_CEIL - 0.011, y + j * d * 0.22 - 0.05), (ex + 0.05, D_CEIL - 0.011, y + j * d * 0.22 - 0.05),
                              (ex + 0.05, D_CEIL - 0.011, y + j * d * 0.22 + 0.05), (ex - 0.05, D_CEIL - 0.011, y + j * d * 0.22 + 0.05)])
                if not ep.isEmpty(): pen.fill(ep, '#3a3a34', 180)
        else:
            pen.fill(tp, mix('#9a9c94', '#fbfff0', k))


def dr_troffer_glow(pen, v, x, y, k, w=1.2, d=0.6, c=D_TUBE):
    if k <= 0.01: return
    q = [(x - w / 2 + 0.04, D_CEIL - 0.012, y - d / 2 + 0.04), (x + w / 2 - 0.04, D_CEIL - 0.012, y - d / 2 + 0.04),
         (x + w / 2 - 0.04, D_CEIL - 0.012, y + d / 2 - 0.04), (x - w / 2 + 0.04, D_CEIL - 0.012, y + d / 2 - 0.04)]
    path = v.poly3(q)
    if path.isEmpty(): return
    pen.fill(path, mix(c, '#ffffff', 0.55), 235 * k)
    b = _rb(path); s = v.s(x, y)
    pen.ellipse_glow((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, max(20.0, (b[2] - b[0]) * 0.8), max(10.0, (b[3] - b[1]) * 1.6), c, 80 * k)


def dr_wall_tv(pen, v, P=(-1.5, 2.08, 0.42), facing=(-0.62, 0.78), k=0.0, t=0.0):
    """A CRT TV on a ceiling-corner bracket (the waiting room's: 'showing nothing': a dull blue-grey glow, k 0..1)."""
    x, Y, y = P
    if v.d(x, y) < 0.3: return
    fa = math.degrees(math.atan2(facing[0], -facing[1]))
    B = Box(x, y, 0.56, 0.46, Y - 0.22, Y + 0.2, fa)

    def front(p_, W, H):
        p_.fill(rect(0, 0, W, H), '#2a2c30')
        sc = rrect(4, 4, W - 8, H - 12, 5)
        p_.fill(sc, mix('#1a2024', '#6a7c88', k))
        if k > 0.01:
            p_.radial(sc, W / 2, H / 2 - 4, W * 0.6, [(0, '#b8c8d0', 90 * k), (1, '#000000', 0)])
            for yy in np.arange(6, H - 10, 2.0): p_.fill(rect(4, yy, W - 8, 0.6), '#000000', 40)
        p_.fill(oval(W - 8, H - 4, 1.4), '#c82a2a' if k > 0 else '#3a1010')
    draw_box(pen, v, B, {'front': dict(fill='#2a2c30', art=front), 'all': '#202226'})
    br = v.p(x - facing[0] * 0.2, Y + 0.2, y - facing[1] * 0.2); bt = v.p(x - facing[0] * 0.2, D_CEIL, y - facing[1] * 0.2)
    pen.seg(br, bt, max(2.0, 0.03 * v.s(x, y)), '#3a3c40')


def dr_wall_tv_glow(pen, v, P=(-1.5, 2.08, 0.42), facing=(-0.62, 0.78), k=0.0, t=0.0):
    if k <= 0.01: return
    x, Y, y = P
    if v.d(x, y) < 0.3: return
    fx, fy = x + facing[0] * 0.3, y + facing[1] * 0.3
    gx, gy = v.p(fx, Y, fy)
    fl = 0.85 + 0.15 * noise1(t * 9.0, 41)
    pen.glow(gx, gy, 0.9 * v.s(x, y), '#8aa0b0', 50 * k * fl)


# ---------------------------------------------------------------------------------------------- the kitchen wall phone
D_RECEIVER = (-1.5, D_COUNTER_Y, 8.32)                       # where Grandma lays the receiver on the counter ("like a sleeping baby")
D_PLUG_FLOOR = (-1.42, 0.0, 7.55)                            # the pulled line cord's plug lying on the floor


def _coil_cord(pen, pts, s, c='#e8dcbe', r=0.012, pitch=0.012, w=None):
    """A coiled telephone cord along a screen polyline pts (design px): s = px per metre there."""
    path = smooth(pts, False, 0.8)
    meas = skia.PathMeasure(path, False)
    L = meas.getLength()
    if L <= 1: return
    rr = max(1.2, r * s); step = max(1.5, pitch * s)
    w = w or max(0.8, 0.0045 * s)
    pen.line(path, rr * 1.6 + 1.5, LINE, 200)
    pen.line(path, rr * 1.6, _darken(c, 0.2))
    d = 0.0
    loops = skia.Path()
    while d < L:
        ok = meas.getPosTan(d)
        if not ok: break
        (px, py), (tx, ty) = ok
        nx, ny = -ty, tx
        loops.moveTo(px - nx * rr - tx * rr * 0.4, py - ny * rr - ty * rr * 0.4)
        loops.quadTo(px + tx * rr * 0.9, py + ty * rr * 0.9, px + nx * rr - tx * rr * 0.4, py + ny * rr - ty * rr * 0.4)
        d += step
    p = skia.Paint(Color=col(c), AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap)
    pen.cv.drawPath(loops, p)
    p2 = skia.Paint(Color=col('#ffffff', 70), AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=max(0.5, w * 0.4))
    pen.cv.drawPath(loops, p2)


def _sag(a, b, n=12, sag=0.0):
    """Points of a hanging curve from a to b (3D) sagging `sag` metres below the chord (a parabola)."""
    out = []
    for i in range(n + 1):
        u = i / n
        out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u - sag * 4 * u * (1 - u), a[2] + (b[2] - a[2]) * u))
    return out


def dr_phone_points():
    """Plan points of the wall phone: base centre, the hook (handset hung), the coil cord's socket at the base bottom,
    the line cord's exit, the jack."""
    x, Y, y = D_PHONE
    return dict(base=(x - 0.045, Y, y), hook=(x - 0.1, Y + 0.02, y - 0.03), cord_base=(x - 0.07, Y - 0.115, y - 0.035),
                line_out=(x - 0.04, Y - 0.115, y + 0.035), jack=D_JACK, receiver_counter=D_RECEIVER, plug_floor=D_PLUG_FLOOR)


def dr_wall_phone(pen, v, phone='hung', cord='in', ring=0.0, t=0.0, era='now'):
    """The kitchen wall phone (a cream rotary wall set: the handset hung vertically on its left, the dial on the right),
    its coiled handset cord and the grey line cord down the wall to the jack on the baseboard.
    phone 'hung' | 'off' (the handset is in someone's hand: the cast draws the coil cord to anchors['phone_cord_base'])
    | 'counter' (the handset lying on the counter, the coil stretched to it); cord 'in' | 'out' (pulled from the wall: it
    hangs down and lies on the floor, plug and all, the jack empty); ring 0..1 = the ringing shiver."""
    x, Y, y = D_PHONE
    if v.d(x, y) < 0.2: return
    body_c = '#efe3c4' if era == 'now' else '#d9a640'
    sh = 0.0015 * ring * math.sin(t * 2 * math.pi * 20)
    jig = 0.004 * ring * math.sin(t * 2 * math.pi * 17 + 1.0)
    B = Box(x - 0.045 + sh, y, 0.13, 0.09, Y - 0.115, Y + 0.105, -90)
    s = v.s(x, y)
    P = dr_phone_points()

    # the line cord first (behind the body)
    lo = (P['line_out'][0] + sh, P['line_out'][1], P['line_out'][2])
    if cord == 'in':
        pts = _sag(lo, (D_JACK[0] - 0.012, D_JACK[1] + 0.02, D_JACK[2]), 10, 0.0)
        pts = [lo, (lo[0] + 0.005, lo[1] - 0.3, lo[2] + 0.06), (D_JACK[0] - 0.01, D_JACK[1] + 0.35, D_JACK[2] - 0.02), (D_JACK[0] - 0.012, D_JACK[1] + 0.03, D_JACK[2])]
        sp = [v.p(*q) for q in pts]
        pen.line(smooth(sp, False, 0.8), max(1.4, 0.006 * s) + 1.6, LINE, 200); pen.line(smooth(sp, False, 0.8), max(1.0, 0.006 * s), lit('#c8c4bc', lo, None))
    else:
        fl = D_PLUG_FLOOR
        pts = [lo, (lo[0] - 0.01, lo[1] - 0.4, lo[2] + 0.02), (lo[0] - 0.03, 0.25, lo[2] + 0.05), (fl[0] + 0.05, 0.01, fl[2] - 0.15),
               (fl[0] - 0.08, 0.005, fl[2] - 0.05), (fl[0] + 0.02, 0.005, fl[2] + 0.06), (fl[0], 0.005, fl[2])]
        sp = [v.p(*q) for q in pts]
        pen.line(smooth(sp, False, 0.8), max(1.4, 0.006 * s) + 1.6, LINE, 200); pen.line(smooth(sp, False, 0.8), max(1.0, 0.006 * s), lit('#c8c4bc', lo, None))
        px_, py_ = v.p(*fl)
        plug = rrect(px_ - 0.012 * s, py_ - 0.008 * s, 0.024 * s, 0.014 * s, 0.003 * s)
        pen.fill(plug, lit('#e8e4d8', fl, (0, 1, 0))); pen.line(plug, 0.8)

    def front(p_, W, H):
        p_.linear(rect(0, 0, W, H), 0, 0, W, 0, [(0, '#ffffff', 50), (0.4, '#ffffff', 0), (1, '#000000', 40)])
        dx_, dy_, dr = W * 0.66, H * 0.62, W * 0.27
        p_.fill(oval(dx_, dy_, dr), _darken(body_c, 0.08)); p_.line(oval(dx_, dy_, dr), 0.5, '#000000', 160)
        for k in range(10):                                                # finger wheel holes
            a = math.radians(-60 + k * 30)
            p_.fill(oval(dx_ + math.cos(a) * dr * 0.7, dy_ + math.sin(a) * dr * 0.7, dr * 0.15), '#f8f4ea'); p_.line(oval(dx_ + math.cos(a) * dr * 0.7, dy_ + math.sin(a) * dr * 0.7, dr * 0.15), 0.3, '#000000', 160)
        p_.fill(oval(dx_, dy_, dr * 0.38), '#f8f4ea'); p_.line(oval(dx_, dy_, dr * 0.38), 0.3, '#000000', 120)
        btext(p_, '555-0179', dx_, dy_ + 0.6, 'sans', dr * 0.16, '#3a3a3a', 200, 'center')
        p_.fill(rect(dx_ + dr * 0.55, dy_ + dr * 0.3, dr * 0.15, dr * 0.5), '#b8b0a0')                   # finger stop
    draw_box(pen, v, B, {'front': dict(fill=body_c, art=front), 'all': _darken(body_c, 0.12), 'top': _lighten(body_c, 0.05)})
    if phone == 'hung':
        hx, hY, hy = x - 0.105 + sh + jig, Y + 0.0, y - 0.035
        top, bot = v.p(hx, hY + 0.105, hy), v.p(hx, hY - 0.105, hy)
        hs = v.s(hx, hy)
        hand = union(union(oval(top[0], top[1] + 0.02 * hs, 0.028 * hs, 0.03 * hs), oval(bot[0], bot[1] - 0.02 * hs, 0.028 * hs, 0.03 * hs)),
                     rrect(top[0] - 0.014 * hs, top[1], 0.028 * hs, bot[1] - top[1], 0.01 * hs))
        pen.fill(hand, lit(_lighten(body_c, 0.04), (hx, hY, hy), (-1, 0, 0))); pen.line(hand, max(0.8, 0.005 * hs))
        pen.linear(hand, top[0] - 0.03 * hs, 0, top[0] + 0.03 * hs, 0, [(0, '#ffffff', 60), (0.45, '#ffffff', 0), (1, '#000000', 50)])
        for q, sg in ((top, 1), (bot, -1)):
            for k in range(3): pen.fill(oval(q[0] - 0.008 * hs + k * 0.008 * hs, q[1] + sg * 0.02 * hs, 0.002 * hs), '#5a5040', 160)
        cb = (x - 0.075 + sh, Y - 0.115, y - 0.035)
        tail = [v.p(hx, hY - 0.135, hy), v.p(hx - 0.01, hY - 0.4, hy + 0.01), v.p(cb[0] - 0.005, cb[1] - 0.12, cb[2]), v.p(*cb)]
        _coil_cord(pen, tail, hs, lit(body_c, (hx, 1.1, hy), None), r=0.009, pitch=0.01)
    elif phone == 'counter':
        rx, rY, ry = D_RECEIVER
        cb = (x - 0.075 + sh, Y - 0.115, y - 0.035)
        pts = [v.p(*cb), v.p(cb[0] - 0.02, cb[1] - 0.25, cb[2] + 0.2), v.p(rx + 0.12, rY + 0.03, ry - 0.2), v.p(rx + 0.04, rY + 0.02, ry - 0.1)]
        _coil_cord(pen, pts, s, lit(body_c, (x, 1.1, y), None), r=0.009, pitch=0.012)
        dr_receiver_lying(pen, v, rx, rY, ry, body_c)


def dr_receiver_lying(pen, v, x, Y, y, c='#efe3c4', ang=20.0):
    """The handset lying on its side on a surface at (x, Y, y), turned `ang` degrees about the vertical."""
    if v.d(x, y) < 0.15: return
    a = math.radians(ang)
    ex, ey = math.sin(a) * 0.1, math.cos(a) * 0.1
    pa, pb = (x - ex, Y + 0.03, y - ey), (x + ex, Y + 0.03, y + ey)
    sa, sb = v.p(*pa), v.p(*pb); s = v.s(x, y)
    sh = shadow_on_floor
    pen.fill(ellipse3(v, x, y, 0.13, 0.05, Y + 0.001), '#000000', 70)
    hand = union(union(oval(sa[0], sa[1], 0.032 * s, 0.026 * s), oval(sb[0], sb[1], 0.032 * s, 0.026 * s)),
                 poly([(sa[0], sa[1] - 0.012 * s), (sb[0], sb[1] - 0.012 * s), (sb[0], sb[1] + 0.01 * s), (sa[0], sa[1] + 0.01 * s)]))
    pen.fill(hand, lit(c, (x, Y + 0.03, y), (0, 1, 0))); pen.line(hand, max(0.8, 0.005 * s))
    pen.linear(hand, 0, min(sa[1], sb[1]) - 0.03 * s, 0, max(sa[1], sb[1]) + 0.03 * s, [(0, '#ffffff', 60), (0.5, '#ffffff', 0), (1, '#000000', 60)])


# ---------------------------------------------------------------------------------------------- kitchen pieces
def _chrome_pulls(p_, W, H, n, y, inset=0.0):
    dw = W / n
    for i in range(n):
        r = rect(i * dw + 2, 3 + inset, dw - 4, H - 6 - inset)
        p_.line(r, 0.9, '#8a8270', 170)
        kx = i * dw + (dw - 9 if i % 2 == 0 else 9)
        p_.fill(rrect(kx - 3.5, y - 0.8, 7, 1.6, 0.8), '#d8dce0'); p_.line(rrect(kx - 3.5, y - 0.8, 7, 1.6, 0.8), 0.4, '#3a3a3a', 200)


def dr_counters(pen, v, o):
    """The kitchen's cream cabinets with chrome pulls, the butter-yellow counter with its chrome edge, the white tile
    splash, the stainless sink under the window, the stove with its hood light, the upper cabinets."""
    x0, x1, y0, y1 = D_KCOUNTER
    cab = DP['cab'] if o.get('era') != '1979' else '#e8d098'
    ctop = DP['counter'] if o.get('era') != '1979' else '#d89a3a'

    def base_art(n):
        def art(p_, W, H):
            p_.texture(rect(0, 0, W, H), 'grunge', 0.18, 'overlay', 0.6)
            _chrome_pulls(p_, W, H, n, 12)
        return art
    runs = [((x0 + 0.0, D_STOVE.cx - D_STOVE.w / 2), 'back'), ((D_STOVE.cx + D_STOVE.w / 2, x1 - 0.62), 'back')]
    for ((a_, b_), _) in runs:
        if b_ - a_ < 0.05: continue
        B = Box((a_ + b_) / 2, (y0 + y1) / 2, b_ - a_, y1 - y0, 0.1, D_COUNTER_Y - 0.04, 0)
        draw_box(pen, v, Box((a_ + b_) / 2, (y0 + y1) / 2 + 0.04, b_ - a_, y1 - y0 - 0.08, 0.0, 0.1, 0), {'all': '#2a2622'}, skip=('top',))   # the recessed toe kick first
        draw_box(pen, v, B, {'front': dict(fill=cab, art=base_art(max(1, int(round((b_ - a_) / 0.45))))), 'all': _darken(cab, 0.18)})
        draw_box(pen, v, Box((a_ + b_) / 2, (y0 + y1) / 2 - 0.01, b_ - a_, y1 - y0 + 0.03, D_COUNTER_Y - 0.04, D_COUNTER_Y, 0),
                 {'all': '#c8ccd0', 'top': dict(fill=ctop, art=lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'grunge', 0.25, 'overlay', 0.6))})
    # the return along the east wall (under the phone's reach): front faces -x
    rx0, rx1, ry0, ry1 = D_KRETURN
    B = Box((rx0 + rx1) / 2, (ry0 + y0) / 2, y0 - ry0, rx1 - rx0, 0.1, D_COUNTER_Y - 0.04, -90)
    draw_box(pen, v, Box((rx0 + rx1) / 2 + 0.04, (ry0 + y0) / 2, y0 - ry0, rx1 - rx0 - 0.08, 0.0, 0.1, -90), {'all': '#2a2622'}, skip=('top',))
    draw_box(pen, v, B, {'front': dict(fill=cab, art=base_art(2)), 'all': _darken(cab, 0.18)})
    draw_box(pen, v, Box((rx0 + rx1) / 2 - 0.01, (ry0 + y1) / 2, y1 - ry0, rx1 - rx0 + 0.03, D_COUNTER_Y - 0.04, D_COUNTER_Y, -90),
             {'all': '#c8ccd0', 'top': dict(fill=ctop, art=lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'grunge', 0.25, 'overlay', 0.6))})
    # splash tiles on the back wall and the east wall above the counter
    for (O, U, W_, nrm) in (((x0, 1.42, 9.598), (1, 0, 0), (x1 - x0) * 100, (0, 0, -1)), ((-1.202, 1.42, 9.6), (0, 0, -1), (9.6 - ry0) * 100, (-1, 0, 0))):
        F = Face(O, U, (0, -1, 0), W_, (1.42 - D_COUNTER_Y) * 100, nrm, 'wall')
        holes = [rect((D_KWIN[0] - x0) * 100, 0, (D_KWIN[1] - D_KWIN[0]) * 100, (1.42 - D_KWIN[2]) * 100)] if nrm == (0, 0, -1) else None
        draw_face(pen, v, F, lambda p_, W, H: (pat(p_, W, H, 'tile', '#d8d8d0', 255, scale=0.72), p_.fill(rect(0, 0, W, 2.2), '#2a6a5a')),
                  '#f4f2ea', holes=holes, ao={'bottom': 6}, line=False)
    # the sink: a stainless double bowl inset in the counter, a chrome faucet
    if v.cam_h > D_COUNTER_Y:
        q = [(D_KSINK[0], D_COUNTER_Y + 0.001, 9.08), (D_KSINK[1], D_COUNTER_Y + 0.001, 9.08), (D_KSINK[1], D_COUNTER_Y + 0.001, 9.5), (D_KSINK[0], D_COUNTER_Y + 0.001, 9.5)]
        pen.fill(v.poly3(q), lit('#b8bcc4', (-3.3, D_COUNTER_Y, 9.3), (0, 1, 0)))
        for (a_, b_) in ((D_KSINK[0] + 0.03, -3.32), (-3.28, D_KSINK[1] - 0.03)):
            q2 = [(a_, D_COUNTER_Y + 0.002, 9.11), (b_, D_COUNTER_Y + 0.002, 9.11), (b_, D_COUNTER_Y + 0.002, 9.47), (a_, D_COUNTER_Y + 0.002, 9.47)]
            pen.fill(v.poly3(q2), lit('#5a6068', (-3.3, D_COUNTER_Y, 9.3), (0, 1, 0)))
        pen.line(v.poly3(q), 1.0)
    fx_, fy_ = v.p(-3.3, D_COUNTER_Y, 9.53); s = v.s(-3.3, 9.53)
    tip = v.p(-3.3, D_COUNTER_Y + 0.26, 9.36)
    path = smooth([(fx_, fy_), v.p(-3.3, D_COUNTER_Y + 0.3, 9.53), tip], False, 1.0)
    pen.line(path, max(2.0, 0.022 * s) + 2, LINE); pen.line(path, max(1.5, 0.022 * s), lit('#d0d4da', (-3.3, 1.1, 9.5), None))
    for sx in (-0.1, 0.1):
        hp = v.p(-3.3 + sx, D_COUNTER_Y + 0.05, 9.53)
        pen.fill(oval(hp[0], hp[1], max(2.0, 0.018 * s)), lit('#e0e4ea', (-3.3, 1.0, 9.5), None)); pen.line(oval(hp[0], hp[1], max(2.0, 0.018 * s)), 0.8)
    # upper cabinets either side of the window, over the stove a hood with its light
    for (a_, b_) in ((x0, -4.05), (-2.55, -1.2)):
        B = Box((a_ + b_) / 2, 9.43, b_ - a_, 0.34, 1.45, 2.25, 0)
        draw_box(pen, v, B, {'front': dict(fill=cab, art=lambda p_, W, H, n=max(1, int(round((b_ - a_) / 0.42))): (p_.texture(rect(0, 0, W, H), 'grunge', 0.18, 'overlay', 0.6),
                                                                                                                         _chrome_pulls(p_, W, H, n, H - 9))),
                             'all': _darken(cab, 0.2), 'bottom': _darken(cab, 0.35)})
    dr_stove(pen, v, o)


def dr_stove(pen, v, o):
    B = D_STOVE
    era = o.get('era')
    c = '#f4f2ec' if era != '1979' else '#c8a040'

    def front(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'grunge', 0.15, 'overlay', 0.5)
        p_.fill(rrect(8, 22, W - 16, H - 36, 2), _darken(c, 0.05)); p_.line(rrect(8, 22, W - 16, H - 36, 2), 0.9, '#3a3a3a', 160)
        p_.fill(rect(16, 30, W - 32, 18), '#1a1c20', 220)
        p_.fill(rrect(12, 15, W - 24, 3.4, 1.5), '#d8dce0')
        for k in range(4): p_.fill(oval(12 + k * (W - 24) / 3, 6, 2.6), '#2a2a2a'); p_.fill(oval(12 + k * (W - 24) / 3, 6, 1.2), '#d8dce0')
        p_.fill(rect(0, H - 9, W, 9), '#2a2a2a')

    def top(p_, W, H):
        for (cx_, cy_) in ((W * 0.27, H * 0.32), (W * 0.73, H * 0.32), (W * 0.27, H * 0.72), (W * 0.73, H * 0.72)):
            p_.fill(oval(cx_, cy_, 9.0), '#1a1a18'); p_.line(oval(cx_, cy_, 5.5), 0.8, '#5a5a50'); p_.line(oval(cx_, cy_, 2.5), 0.8, '#5a5a50')
    draw_box(pen, v, B, {'front': dict(fill=c, art=front), 'top': dict(fill='#e8e8e2', art=top), 'all': _darken(c, 0.15)})
    draw_box(pen, v, Box(B.cx, B.cy + 0.28, B.w, 0.06, B.Y1, B.Y1 + 0.14, 0), {'all': c})
    hood = Box(B.cx, 9.38, B.w + 0.04, 0.44, 1.62, 1.76, 0)
    draw_box(pen, v, hood, {'all': '#c8ccd0', 'bottom': '#2a2a2c', 'front': dict(fill='#d8dce0', art=lambda p_, W, H: p_.fill(rect(4, H - 4, W - 8, 1.2), '#8a8a8a'))})
    # a kettle on the back burner
    kx, ky = B.cx + 0.17, B.cy + 0.12
    if v.d(kx, ky) > 0.3:
        s = v.s(kx, ky); px, py = v.p(kx, B.Y1, ky)
        k_ = smooth([(px - 0.1 * s, py), (px - 0.11 * s, py - 0.08 * s), (px - 0.05 * s, py - 0.15 * s), (px + 0.05 * s, py - 0.15 * s), (px + 0.11 * s, py - 0.08 * s), (px + 0.1 * s, py)], True, 0.8)
        pen.fill(k_, lit('#c8342a' if era != '1979' else '#e88a2a', (kx, B.Y1 + 0.1, ky), None)); pen.line(k_, 1.0)
        pen.line(smooth([(px - 0.06 * s, py - 0.15 * s), (px, py - 0.22 * s), (px + 0.06 * s, py - 0.15 * s)], False, 1.0), max(1.0, 0.012 * s), '#2a2a2a')


def dr_fridge(pen, v, o):
    """The rounded cream fridge (1960s, Grandma kept it): chrome handle, Mom's schedule, Milo's dinosaur drawing,
    magnets; 1979 it is avocado green."""
    B = D_FRIDGE
    era = o.get('era')
    c = '#efe8d6' if era != '1979' else '#9aa04a'

    def front(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'grunge', 0.2, 'overlay', 0.5)
        p_.linear(rect(0, 0, W, H), 0, 0, W, 0, [(0, '#ffffff', 40), (0.3, '#ffffff', 0), (1, '#000000', 45)])
        p_.fill(rect(0, H * 0.3, W, 1.2), '#6a6250')
        p_.fill(rrect(W - 12, H * 0.38, 4.5, H * 0.16, 2), '#d8dce0'); p_.line(rrect(W - 12, H * 0.38, 4.5, H * 0.16, 2), 0.5, '#3a3a3a', 200)
        p_.fill(rrect(W - 12, H * 0.12, 4.5, H * 0.1, 2), '#d8dce0')
        if era != '1979':
            # Milo's dinosaur drawing, Mom's shift schedule, a Larkfield General magnet
            p_.fill(rect(8, H * 0.08, 24, 18), '#fbf7ee'); p_.fill(rect(8.6, H * 0.08 + 0.8, 24, 18), '#000000', 30)
            p_.fill(smooth([(12, H * 0.08 + 14), (16, H * 0.08 + 8), (22, H * 0.08 + 7), (28, H * 0.08 + 10), (26, H * 0.08 + 15)], True, 0.7), '#4aa86a')
            p_.fill(oval(30, H * 0.08 + 4, 1.4), '#e84a5a')
            p_.fill(rect(10, H * 0.42, 30, 38), '#ffffff')
            btext(p_, 'MOM - NIGHTS', 25, H * 0.42 + 5, 'hand', 3.6, '#2a3a8a', 230, 'center')
            for k in range(7):
                p_.seg((12, H * 0.42 + 9 + k * 4), (38 - (k % 3) * 3, H * 0.42 + 9 + k * 4), 0.5, '#5a6aa8', 170)
            p_.fill(oval(25, H * 0.42 - 0.5, 1.6), '#4a8ad8')
            p_.fill(rrect(36, H * 0.64, 10, 6, 1.5), '#2a6aa8'); btext(p_, 'LGH', 41, H * 0.64 + 4.2, 'sans_b', 3.0, '#ffffff', 230, 'center')
        p_.fill(rect(0, H - 6, W, 6), '#2a2622')
    fs = B.faces()
    draw_face(pen, v, fs['front'], front, c, ao=False)
    for nm in ('left', 'right', 'top'):
        draw_face(pen, v, fs[nm], None, _darken(c, 0.1) if nm != 'top' else _lighten(c, 0.04), ao=False)


def dr_kitchen_table(pen, v, o):
    """The formica table with its chrome band and legs, a sugar bowl, Milo's water glass."""
    B = D_KTABLE
    era = o.get('era')
    top = '#f2e6c8' if era != '1979' else '#e8b86a'
    parts = table_parts(B, top, leg='#c8ccd0', apron=0.0, thick=0.04, legw=0.035)
    draw_parts(pen, v, parts)
    edge = Box(B.cx, B.cy, B.w + 0.01, B.d + 0.01, B.Y1 - 0.035, B.Y1 - 0.005, B.fa)
    draw_box(pen, v, edge, {'all': '#d8dce2'}, skip=('top', 'bottom'))
    gx, gy = B.cx + 0.3, B.cy - 0.12
    if v.d(gx, gy) > 0.3:
        s = v.s(gx, gy); px, py = v.p(gx, B.Y1, gy)
        gl = poly([(px - 0.032 * s, py - 0.12 * s), (px + 0.032 * s, py - 0.12 * s), (px + 0.026 * s, py), (px - 0.026 * s, py)])
        pen.fill(gl, '#c8dce8', 110); pen.fill(rect(px - 0.028 * s, py - 0.05 * s, 0.056 * s, 0.05 * s), '#a8c8e0', 90); pen.line(gl, 0.8, '#5a6a7a')
        pen.seg((px - 0.022 * s, py - 0.11 * s), (px - 0.018 * s, py - 0.01 * s), max(0.6, 0.004 * s), '#ffffff', 140)


def dr_kitchen_chairs():
    """The three red vinyl kitchen chairs round the table: [(name, x, y, fa, face)]."""
    B = D_KTABLE
    out = []
    for i, (u, n, fa, face) in enumerate(((-0.3, -0.6, 0, (0, 1)), (0.3, -0.6, 0, (0, 1)), (-0.82, 0.0, 90, (1, 0)))):
        if i == 2:
            c = (B.cx - 0.82, B.cy)
        else:
            q = B.at(u, n, 0); c = (q[0], q[2])
        out.append(('kchair%d' % i, c[0], c[1], fa, face))
    return out


def _cafe_curtain_d(pen, v, era='now'):
    """Red-check cafe curtains on a tension rod across the lower half of the sink window."""
    rodY = (D_KWIN[2] + D_KWIN[3]) / 2 + 0.02
    O = (D_KWIN[0] - 0.02, rodY, 9.6 - 0.07)
    F = Face(O, (1, 0, 0), (0, -1, 0), (D_KWIN[1] - D_KWIN[0] + 0.04) * 100, (rodY - D_KWIN[2] + 0.02) * 100, (0, 0, -1), 'front')
    W, H = F.W, F.H
    shape = poly([(0, 0), (W, 0)] + [(x, H - 1.2 * abs(math.sin(x * 0.25))) for x in np.linspace(W, 0, 24)])
    ink = '#c83a3a' if era != '1979' else '#d87a2a'

    def art(p_, W, H):
        p_.fill(rect(0, 0, W, H), '#f2ead8')
        pat(p_, W, H, 'gingham', ink, 200, scale=1.0)
        for k in range(int(W / 6)):
            p_.linear(rect(k * 6, 0, 6, H), k * 6, 0, k * 6 + 6, 0, [(0, '#000000', 40), (0.5, '#ffffff', 20), (1, '#000000', 40)])
        p_.fill(rect(W * 0.48, 0, W * 0.04, H), '#000000', 30)
        p_.fill(rect(0, 0, W, 1.4), '#c8ccd0')
    draw_face(pen, v, F, art, '#f2ead8', shape=shape, ao=False, lw=0.9)


# ---------------------------------------------------------------------------------------------- the bathroom pieces
CARD_FACE = '#d8c088'                                        # the card: "the paper so old it had gone the colour of weak tea"


def _card_art_small(p_, x, y, w, h, k=1.0, tape=True):
    """The yellow rules card as seen in the room (cm frame, top-left x, y): typed lines too small to read, the tape."""
    p_.fill(rect(x + 0.3, y + 0.5, w, h), '#000000', 70 * k)
    p_.fill(rect(x, y, w, h), CARD_FACE, 255 * k)
    p_.texture(rect(x, y, w, h), 'paper', 0.6 * k, 'multiply', 0.3)
    p_.linear(rect(x, y, w, h), x, y, x + w, y + h, [(0, '#8a6a30', 0), (0.7, '#8a6a30', 0), (1, '#8a6a30', 60 * k)])
    p_.fill(rect(x + w * 0.2, y + h * 0.07, w * 0.6, h * 0.05), '#2a2420', 200 * k)
    for i in range(7):
        yy = y + h * (0.2 + 0.1 * i)
        p_.fill(rect(x + w * 0.08, yy, w * (0.8 - 0.12 * ((i * 3) % 4) / 3), h * 0.03), '#2a2420', 170 * k)
    if tape:
        for (tx, ty) in ((x - 0.6, y - 0.6), (x + w - 2.4, y - 0.6)):
            p_.fill(rect(tx, ty, 3.0, 1.6), '#f0e2a8', 190 * k)


def dr_cabinet_door(o):
    """The medicine cabinet's mirrored door (Door: hinge at its front edge y0; opens toward the room). Face a = inside
    (the yellow card taped to it), face b = the mirror."""
    x, y0, y1, Y0, Y1 = D_CAB
    card = o.get('card', True)
    marks = o.get('card_marks', not card)

    def inside(p_, W, H):
        p_.fill(rect(0, 0, W, H), '#e8e6e0')
        p_.fill(rect(2, 2, W - 4, H - 4), '#d0ccc4')
        p_.texture(rect(0, 0, W, H), 'grunge', 0.3, 'overlay', 0.5)
        if card:
            _card_art_small(p_, W * 0.5 - 6.2, H * 0.22, 12.4, 7.6 * 1.25)
        elif marks:
            for (tx, ty) in ((W * 0.5 - 6.8, H * 0.22 - 0.6), (W * 0.5 + 3.8, H * 0.22 - 0.6)):
                p_.fill(rect(tx, ty, 3.0, 1.6), '#c8b880', 120)                    # the old tape's ghosts
            p_.line(rect(W * 0.5 - 6.2, H * 0.22, 12.4, 9.5), 0.4, '#a89a70', 60)

    def mirror(p_, W, H):
        p_.fill(rect(0, 0, W, H), '#c8ccd0')
        p_.fill(rect(1.5, 1.5, W - 3, H - 3), '#5a6670')
        p_.linear(rect(1.5, 1.5, W - 3, H - 3), 0, 0, W, H, [(0, '#8a9aa8', 255), (0.45, '#4a5660', 255), (1, '#3a444c', 255)])
        p_.linear(rect(1.5, 1.5, W - 3, H - 3), 0, 0, W, H, [(0, '#ffffff', 0), (0.3, '#ffffff', 50), (0.36, '#ffffff', 0), (0.5, '#ffffff', 25), (0.54, '#ffffff', 0)])
        p_.fill(rect(1.5, H - 7, W - 3, 5.5), '#000000', 40)
    D = Door((x - 0.02, y0), y1 - y0, Y1 - Y0, (0.0, 1.0), 1, Y0, art_a=inside, art_b=mirror, thick=0.025, col='#d8dade')
    return D


def dr_cabinet_box(pen, v, o):
    """The cabinet's recess (shelves, amber pill bottles, a toothbrush glass, bandages) and its chrome frame."""
    x, y0, y1, Y0, Y1 = D_CAB
    dep = 0.13
    empty = o.get('cab_empty', False)
    # the back and the shelves (faces inside the wall)
    back = Face((x + dep, Y1, y0), (0, 0, 1), (0, -1, 0), (y1 - y0) * 100, (Y1 - Y0) * 100, (-1, 0, 0), 'wall')
    draw_face(pen, v, back, lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'plaster', 0.4, 'overlay', 0.5), '#e4e2dc', ao={'top': 6, 'bottom': 6, 'left': 6, 'right': 6})
    for (ya, yb) in ((y0, y0), (y1, y1)):
        F = Face((x, Y1, ya), (1, 0, 0), (0, -1, 0), dep * 100, (Y1 - Y0) * 100, (0, 0, 1) if ya == y0 else (0, 0, -1), 'side')
        draw_face(pen, v, F, None, '#d8d6d0', ao=False, lw=0.8)
    for sY in (Y0 + 0.005, Y0 + 0.24, Y0 + 0.47):
        F = Face((x, sY, y0), (0, 0, 1), (1, 0, 0), (y1 - y0) * 100, dep * 100, (0, 1, 0), 'top')
        draw_face(pen, v, F, None, '#f0f0ec', ao=False, lw=0.7)
        if empty and sY > Y0 + 0.1: continue
        rng = np.random.default_rng(int(sY * 100))
        yy = y0 + 0.04
        while yy < y1 - 0.05:
            w_ = rng.uniform(0.03, 0.05); h_ = rng.uniform(0.07, 0.15)
            kind = rng.uniform()
            cxx = x + dep * 0.5
            if v.d(cxx, yy) > 0.1:
                px, py = v.p(cxx, sY, yy + w_ / 2); s = v.s(cxx, yy)
                r = rrect(px - w_ * 0.5 * s, py - h_ * s, w_ * s, h_ * s, w_ * 0.2 * s)
                cc = '#c8782a' if kind < 0.5 else ('#f2f2ee' if kind < 0.8 else '#8ab0d0')
                pen.fill(r, lit(cc, (cxx, sY + h_ / 2, yy), (-1, 0, 0))); pen.line(r, 0.7)
                pen.fill(rect(px - w_ * 0.5 * s, py - h_ * s, w_ * s, h_ * 0.22 * s), lit('#f2f2ee' if kind < 0.5 else '#3a6aa8', (cxx, sY + h_, yy), None))
                if kind < 0.5: pen.fill(rect(px - w_ * 0.42 * s, py - h_ * 0.65 * s, w_ * 0.84 * s, h_ * 0.3 * s), lit('#fbf7ee', (cxx, sY + h_ / 2, yy), None))
            yy += w_ + rng.uniform(0.01, 0.03)
    # chrome frame round the recess
    fr = Face((x - 0.012, Y1 + 0.02, y0 - 0.02), (0, 0, 1), (0, -1, 0), (y1 - y0 + 0.04) * 100, (Y1 - Y0 + 0.04) * 100, (-1, 0, 0), 'front')
    draw_face(pen, v, fr, lambda p_, W, H: p_.linear(rect(0, 0, W, H), 0, 0, W, H, [(0, '#f8f8f8', 255), (0.5, '#a8acb0', 255), (1, '#e8eaec', 255)]),
              '#c8ccd0', holes=[rect(2, 2, (y1 - y0) * 100, (Y1 - Y0) * 100)], ao=False, lw=0.9)


def dr_vanity_light(pen, v, k=0.0):
    """The bar light over the cabinet: a chrome bar with three frosted globes."""
    x, y0, y1, Y0, Y1 = D_CAB
    for j in range(3):
        yy = y0 + (y1 - y0) * (0.18 + 0.32 * j)
        P = (x - 0.08, Y1 + 0.16, yy)
        if v.d(P[0], P[2]) < 0.15: continue
        s = v.s(P[0], P[2]); px, py = v.p(*P)
        pen.fill(oval(px, py, 0.05 * s), mix(lit('#e8e4dc', P, None), '#fff8e8', k)); pen.line(oval(px, py, 0.05 * s), 0.9)
    a_, b_ = v.p(x - 0.03, Y1 + 0.2, y0 + 0.02), v.p(x - 0.03, Y1 + 0.2, y1 - 0.02)
    pen.seg(a_, b_, max(2.0, 0.02 * v.s(x, y0)), '#b8bcc0')


def dr_pedestal_sink(pen, v):
    x, y = D_BSINK
    B = Box(x, y, 0.56, 0.44, 0.78, 0.88, -90)
    s = v.s(x, y)
    a_, b_ = v.p(x + 0.02, 0.0, y), v.p(x + 0.02, 0.78, y)
    col_ = lit('#f4f2ee', (x, 0.4, y), None)
    ped = poly([(a_[0] - 0.09 * s, a_[1]), (a_[0] + 0.09 * s, a_[1]), (b_[0] + 0.06 * s, b_[1]), (b_[0] - 0.06 * s, b_[1])])
    pen.fill(ped, col_); pen.line(ped, 1.0)
    draw_box(pen, v, B, {'all': '#ecebe6', 'top': dict(fill='#f8f6f2', art=lambda p_, W, H: (p_.fill(oval(W / 2, H * 0.55, W * 0.36, H * 0.32), '#d8dce0'),
                                                                                                 p_.line(oval(W / 2, H * 0.55, W * 0.36, H * 0.32), 0.6, '#5a5a5a', 160)))})
    for sy in (-0.12, 0.12):
        P = (x + 0.17, 0.9, y + sy)
        if v.d(P[0], P[2]) > 0.15:
            q = v.p(*P); pen.fill(oval(q[0], q[1], max(1.5, 0.018 * v.s(P[0], P[2]))), lit('#e8eaec', P, None)); pen.line(oval(q[0], q[1], max(1.5, 0.018 * v.s(P[0], P[2]))), 0.7)


def dr_toilet(pen, v):
    x, y = D_TOILET
    tank = Box(x + 0.12, y, 0.48, 0.2, 0.42, 0.78, -90)
    bowl = Box(x - 0.08, y, 0.38, 0.5, 0.0, 0.4, -90)
    draw_box(pen, v, bowl, {'all': '#f0eeea', 'top': '#f6f4f0'})
    draw_box(pen, v, tank, {'all': '#f0eeea', 'top': '#f8f6f2'})


def dr_tub(pen, v):
    B = D_TUB
    draw_box(pen, v, B, {'front': dict(fill='#eef2f2', art=lambda p_, W, H: p_.linear(rect(0, 0, W, H), 0, 0, 0, H, [(0, '#ffffff', 40), (1, '#000000', 40)])),
                         'top': dict(fill='#f4f6f6', art=lambda p_, W, H: (p_.fill(rrect(6, 6, W - 12, H - 12, 10), '#c8d0d4'))), 'all': '#e0e6e6'})
    # the shower curtain (aqua, pulled half across)
    F = Face((B.cx - B.w / 2, 2.0, B.cy - B.d / 2 - 0.02), (1, 0, 0), (0, -1, 0), B.w * 55, 135.0, (0, 0, -1), 'front')
    sh = poly([(0, 0), (B.w * 55, 0)] + [(x, 135 - 2 * abs(math.sin(x * 0.2))) for x in np.linspace(B.w * 55, 0, 16)])

    def art(p_, W, H):
        for i in range(int(W / 7)):
            p_.linear(rect(i * 7, 0, 7, H), i * 7, 0, i * 7 + 7, 0, [(0, '#000000', 40), (0.5, '#ffffff', 40), (1, '#000000', 40)])
        for (cx_, cy_) in ((12, 30), (40, 60), (22, 95), (60, 40), (70, 110)): p_.line(oval(cx_, cy_, 5), 1.0, '#ffffff', 90)
    draw_face(pen, v, F, art, '#8ac8c8', shape=sh, ao=False, lw=0.9)
    a_, b_ = v.p(B.cx - B.w / 2, 2.02, B.cy - B.d / 2 - 0.02), v.p(B.cx + B.w / 2, 2.02, B.cy - B.d / 2 - 0.02)
    pen.seg(a_, b_, max(1.5, 0.012 * v.s(B.cx, B.cy)), '#c8ccd0')


# ---------------------------------------------------------------------------------------------- hall pieces
def dr_front_door_art(side='in', lite_k=0.0):
    """The front door: deep red outside / white inside, four panels, a little half-moon lite at the top, the peephole at
    1.5 m, the deadbolt and the brass knob (on the east side)."""
    col_ = DP['door_red'] if side == 'out' else '#efe9dc'

    def art(p_, W, H):
        p_.fill(rect(0, 0, W, H), col_)
        p_.texture(rect(0, 0, W, H), 'wood', 0.25, 'overlay', 0.6, 90)
        sw = 11.0
        for (y0, y1) in ((H * 0.24, H * 0.58), (H * 0.63, H - 12)):
            for (x0, x1) in ((sw, W / 2 - 3.5), (W / 2 + 3.5, W - sw)):
                pr = rect(x0, y0, x1 - x0, y1 - y0)
                p_.fill(pr, _darken(col_, 0.05)); p_.fill(rect(x0 + 3, y0 + 3, x1 - x0 - 6, y1 - y0 - 6), _lighten(col_, 0.03))
                p_.line(pr, 0.9, '#000000', 90); p_.fill(rect(x0, y1 - 1.2, x1 - x0, 1.2), '#ffffff', 70)
        # the half-moon lite (a hole would show the porch: drawn as glass lit by the porch light)
        lite = inter(oval(W / 2, H * 0.17, W * 0.3, H * 0.09), rect(0, 0, W, H * 0.17))
        p_.fill(lite, mix('#141a2a', '#ffdca0', lite_k)); p_.line(lite, 1.2, '#2a2420', 200)
        for k in (-1, 0, 1): p_.seg((W / 2, H * 0.17), (W / 2 + k * W * 0.2, H * 0.17 - H * 0.07 * (1 - abs(k) * 0.3)), 0.8, '#2a2420', 200)
        kx = 7.5 if side == 'in' else W - 7.5                     # face a (outside) runs hinge -> latch, face b latch -> hinge
        ky = H - D_KNOB_Y * 100
        p_.fill(rrect(kx - 3.2, ky - 9, 6.4, 18, 2.6), '#a8843a'); p_.fill(oval(kx, ky, 3.4), '#c9a24a'); p_.fill(oval(kx - 1.0, ky - 1.2, 1.3), '#fff0c0', 200)
        p_.line(oval(kx, ky, 3.4), 0.7, '#3a2a10', 220)
        by = H - (D_KNOB_Y + 0.17) * 100
        p_.fill(oval(kx, by, 3.0), '#b8944a'); p_.line(oval(kx, by, 3.0), 0.7, '#3a2a10', 220)
        p_.seg((kx - 2.2, by), (kx + 2.2, by), 1.6, '#6a4a1a')
        py_ = H - D_PEEP_Y * 100
        p_.fill(oval(W / 2, py_, 2.2), '#b8944a'); p_.fill(oval(W / 2, py_, 1.1), '#1a1c22'); p_.fill(oval(W / 2 - 0.4, py_ - 0.4, 0.4), '#c8d0e8', 220)
        p_.line(oval(W / 2, py_, 2.2), 0.6, '#3a2a10', 220)
        if side == 'out':
            p_.fill(rect(W / 2 - 9, H * 0.6, 18, 3), '#c9a24a')                    # a brass kick plate / number
            btext(p_, '27', W / 2, H * 0.22, 'serif_b', 9, '#c9a24a', 230, 'center')
        p_.line(rect(0, 0, W, H), 1.0, '#000000', 120)
    return art


def dr_front_door(o):
    ang = o.get('front_door', 0.0)
    ang = ang if not callable(ang) else 0.0
    D = Door((D_FDOOR[0], 0.03), D_FDOOR[1] - D_FDOOR[0], D_FDOOR[2], (1.0, 0.0), 1, 0.0,
             art_a=dr_front_door_art('out'), art_b=dr_front_door_art('in', o.get('porch_lite', 0.0)), col='#efe9dc')
    return D, ang


def dr_panel_door(hinge, width, cd, swing, latch_a='right', col_='#efe9dc', kind='six'):
    return Door(hinge, width, 2.03, cd, swing, 0.0, art_a=door_art(kind, latch_a, bolt=False), art_b=door_art(kind, 'left' if latch_a == 'right' else 'right', bolt=False), col=col_)


def dr_coat_rack(pen, v, x=0.18, y=0.75):
    """A bentwood coat stand by the front door: Ruth's grey coat, Mom's navy scrub jacket, a scarf, an umbrella."""
    if v.d(x, y) < 0.3: return
    s = v.s(x, y)
    a_, b_ = v.p(x, 0.0, y), v.p(x, 1.85, y)
    for k in range(3):
        ang = 2 * math.pi * k / 3
        f = v.p(x + math.cos(ang) * 0.22, 0.0, y + math.sin(ang) * 0.22)
        pen.seg(v.p(x, 0.25, y), f, max(1.5, 0.02 * s) + 2, LINE); pen.seg(v.p(x, 0.25, y), f, max(1.2, 0.02 * s), lit('#5a3a22', (x, 0.2, y), None))
    pen.seg(a_, b_, max(2.0, 0.032 * s) + 2, LINE); pen.seg(a_, b_, max(1.5, 0.032 * s), lit('#6a4228', (x, 1.0, y), None))
    for (dx, dy, c_, ln) in ((-0.14, 0.03, '#6a6a70', 1.0), (0.12, -0.04, '#2a3a5a', 0.75), (0.02, 0.12, '#8a2a3a', 0.5)):
        top = v.p(x + dx * 0.4, 1.72, y + dy * 0.4)
        bot = v.p(x + dx, 1.72 - ln * 0.95, y + dy)
        coat = smooth([(top[0] - 0.05 * s, top[1]), (top[0] + 0.05 * s, top[1]), (bot[0] + 0.17 * s * ln, bot[1]), (bot[0] - 0.17 * s * ln, bot[1])], True, 0.5)
        pen.fill(coat, lit(c_, (x + dx, 1.3, y + dy), None)); pen.line(coat, 1.0)
        pen.linear(coat, bot[0] - 0.17 * s, 0, bot[0] + 0.17 * s, 0, [(0, '#000000', 70), (0.5, '#000000', 0), (1, '#000000', 80)])
    um = [v.p(x + 0.2, 0.0, y - 0.05), v.p(x + 0.17, 0.85, y - 0.04)]
    pen.seg(um[0], um[1], max(2.0, 0.03 * s) + 2, LINE); pen.seg(um[0], um[1], max(1.5, 0.03 * s), lit('#2a2a30', (x, 0.4, y), None))


def dr_hall_table(pen, v, x=-0.95, y=1.35):
    """A narrow demilune table against the hall's west wall: a doily, a bowl, a small lamp, Grandpa's photo."""
    B = Box(x, y, 0.75, 0.3, 0.0, 0.78, 90)
    draw_parts(pen, v, table_parts(B, '#5a3620', apron=0.06, legw=0.035))
    P = (x + 0.02, 0.78, y - 0.2)
    if v.d(P[0], P[2]) > 0.3:
        s = v.s(P[0], P[2]); px, py = v.p(*P)
        bowl = smooth([(px - 0.08 * s, py - 0.04 * s), (px + 0.08 * s, py - 0.04 * s), (px + 0.05 * s, py), (px - 0.05 * s, py)], True, 0.6)
        pen.fill(bowl, lit('#6a8aa8', P, None)); pen.line(bowl, 0.9)


# ====================================================================================================== the rooms
def _win_glass_quads(wall_pts, u0, u1, sill, top, inset=0.06):
    """3D quads of a window's glass (one quad for the whole opening, slightly inside the wall plane)."""
    a, b = wall_pts
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy); fx, fy = dx / L, dy / L
    nx, ny = fy, -fx
    def P(u, Y): return (a[0] + fx * u - nx * inset, Y, a[1] + fy * u - ny * inset)
    return [P(u0, top), P(u1, top), P(u1, sill), P(u0, sill)]


def _glass_layer(name, v, quads, order, k=1.0, seed=5, c='#9aa8c8'):
    """A live layer: rain on the window glass (drops + rivulets) clipped to the projected panes."""
    paths = []
    for q in quads:
        pth = v.poly3(q)
        if not pth.isEmpty(): paths.append(pth)
    if not paths: return None
    clip = paths[0]
    for p_ in paths[1:]: clip = union(clip, p_)
    b = _rb(clip)
    d = max(0.3, min(v.d(q[0][0], q[0][2]) for q in quads))

    def draw(pen, t):
        dr_glass_rain(pen, t, clip, (b[0], b[1], b[2], b[3]), k, seed, c)
    lay = Layer(d, draw, name, blur=None)
    lay.order = order
    return lay


def _rain_out_layer(v, name='rain_out', k=1.0, box=None, seed=3, order=None, c='#b8c4dc', a=50):
    """Live rain beyond the windows: drawn right after the cached outside (so walls hide it, windows show it)."""
    def draw(pen, t):
        dr_rain(pen, t, box or (-500, -400, 2900, 1800), k, seed, 1.0, 0.1, c, a * 0.32, 260, far=True)
        dr_rain(pen, t, box or (-500, -400, 2900, 1800), k * 0.4, seed + 1, 1.25, 0.12, c, a * 0.4, 90)
    lay = Layer(30.0, draw, name, blur=None)
    lay.order = ORDER_OUT - 1.0 if order is None else order
    return lay


class DrRoom(Room):
    """A room of Ruth's house: far=True when it is seen through a doorway of another room (its door leaves are then left
    to the main room, so nothing is drawn twice)."""
    R = (0, 1, 0, 1)

    def __init__(self, far=False):
        self.far = far
        self.poly = _r4p(self.R)


def _wall_runs(pen, v, R, holes, paper, ink=None, kind=None, art=None, **kw):
    """Draw a room's four walls: holes = {side: [(xa, ya, xb, yb, v0, v1), ...]} in plan coordinates; art = {side: fn}."""
    for (side, a, b, u_of) in _walls_of(R):
        hs = [_hole_x(u_of, xa, xb, ya, yb, v0, v1) for (xa, ya, xb, yb, v0, v1) in holes.get(side, [])]
        wall(pen, v, a, b, 0.0, D_CEIL, paper, ink, kind, hs, art=(art or {}).get(side), **kw)


# ---------------------------------------------------------------------------------------------- living room
class DrLiving(DrRoom):
    """The living room. o['state']: 'now' | '1979' | 'wait' (the waiting room). o['tod']: 'night' | 'sunrise'."""
    name = 'living'
    R = D_LIV

    def lights(self, o):
        st, tod = o.get('state', 'now'), o.get('tod', 'night')
        amb = {'now': D_NIGHT_AMB, '1979': '#3a3248', 'wait': '#2e3626'}[st]
        street = Lamp(kind='win', c='#8a9ad8' if st != '1979' else '#a8a0c8', k=0.55, soft=10.0,
                      panes=_panes_y(D_LWIN[0], D_LWIN[1], D_LWIN[2], D_LWIN[3], 0.0), d=_norm3((-0.35, -0.45, 1.0)),
                      only={'floor', 'wall', 'top', 'front', 'side'})
        side = Lamp(kind='win', c='#8a9ad8', k=0.4, soft=10.0, panes=_panes_x(D_SWIN[0], D_SWIN[1], D_SWIN[2], D_SWIN[3], -5.6),
                    d=_norm3((1.0, -0.4, -0.2)), only={'floor', 'wall', 'top', 'front', 'side'})
        steady = [street, side]
        if tod == 'sunrise':
            amb = '#5e5258' if st != '1979' else '#6a5450'
            steady = [Lamp(kind='win', c=D_SUN, k=1.25, soft=14.0, panes=_panes_y(D_LWIN[0], D_LWIN[1], D_LWIN[2], D_LWIN[3], 0.0),
                           d=_norm3((0.3, -0.32, 1.0))),
                      Lamp(kind='win', c='#ffd8a8', k=0.5, soft=14.0, panes=_panes_x(D_SWIN[0], D_SWIN[1], D_SWIN[2], D_SWIN[3], -5.6),
                           d=_norm3((1.0, -0.3, -0.3)))]
        lampL = [Lamp(D_SIDE[0], D_SIDE[3] + 0.4, D_SIDE[1], 4.6, D_LAMP, 1.9, (1.0, 0.75, 0.85), fall=1.6)]
        ceilL = [Lamp(-3.4, D_CEIL - 0.15, 2.7, 6.5, '#ffe2b8', 1.5, (1.0, 0.6, 0.2), fall=1.3)]
        headL = [Lamp(kind='win', c=D_HEAD, k=1.4, soft=16.0, panes=_panes_y(D_LWIN[0], D_LWIN[1], D_LWIN[2], D_LWIN[3], 0.0),
                      d=_norm3((0.62, 0.16, 1.0)), only={'floor', 'wall', 'ceil', 'top', 'front', 'side'}),
                 Lamp(-3.4, 1.0, 0.6, 3.5, D_HEAD, 0.35, fall=1.4)]
        hallL = [Lamp(-1.0, 2.0, 2.65, 3.4, '#ffd8a0', 0.7, fall=1.5)]
        var = [('lamp', lampL, _kfn(o.get('lamp', 0.0), 201)), ('ceiling', ceilL, _kfn(o.get('ceiling', 0.0), 202)),
               ('headlights', headL, _kfn(o.get('headlights', 0.0), 203)), ('hall', hallL, _kfn(o.get('hall', 0.0), 204))]
        if st == 'wait':
            tubes = o.get('tubes')
            for i, (x, y) in enumerate(D_TROFFERS):
                spec = (tubes[i] if tubes else (1.0, 0.0, dict(flick=None, k=1.0, amount=1.0), 0.0)[i])
                if spec in (0, 0.0, None): continue
                var.append(('tube%d' % i, [Lamp(x, D_CEIL - 0.08, y, 5.2, D_TUBE, 1.55, (1.0, 0.7, 0.25), fall=1.35)], _dr_tube_kfn(spec, 210 + i)))
            var.append(('sign_red', [Lamp(D_SIGN[0], (D_SIGN[2] + D_SIGN[3]) / 2, D_SIGN[1] + 0.2, 1.8, '#ff3a2a', 0.5, fall=1.6)], _kfn(o.get('sign', 1.0), 215)))
            var.append(('tv', [Lamp(-1.75, 1.9, 0.75, 2.8, '#9ab0c0', 0.35, fall=1.6)], _kfn(o.get('tv', 1.0), 216)))
        return amb, steady, var

    def shell(self, pen, v, o):
        st = o.get('state', 'now')
        x0, x1, y0, y1 = D_LIV
        if st == '1979':
            floor_rect(pen, v, x0, x1, y0, y1, 0.0, DP['shag'], None, art=_carpet_art(DP['shag'], '#7a3010', 3, shag=True))
        else:
            rug = st == 'now'
            def fart(p_, W, H, rug=rug, st=st):
                _carpet_art(DP['carpet'], DP['carpet_ink'], 2)(p_, W, H)
                if rug: _rug_braided(p_, *floor_uv(x0, y1, D_RUG[0], D_RUG[1]), D_RUG[2] * 100, D_RUG[3] * 100)
                if st == 'wait':
                    p_.texture(rect(0, 0, W, H), 'grunge', 0.3, 'multiply', 2.2)
                    for (rx, ry) in ((D_ARM.cx, D_ARM.cy), (-2.0, 2.9)):              # worn paths in the pile
                        u_, w_ = floor_uv(x0, y1, rx, ry)
                        p_.fill(oval(u_, w_, 60, 40), '#000000', 30)
            floor_rect(pen, v, x0, x1, y0, y1, 0.0, DP['carpet'] if st == 'now' else '#6e6448', None, art=fart)
        paper, ink, ink2, kind, wc = {'now': (DP['liv_paper'], DP['liv_ink'], DP['liv_ink2'], 'ditsy', '#d8ccb0'),
                                      '1979': (DP['liv79_paper'], DP['liv79_ink'], DP['liv79_ink2'], 'roses', '#6a4024'),
                                      'wait': (DP['wait_paper'], DP['wait_ink'], '#6a6e4a', 'ditsy', '#9a9a7a')}[st]
        holes = {'front': [(D_LWIN[0], 0.0, D_LWIN[1], 0.0, D_LWIN[2], D_LWIN[3])],
                 'west': [(-5.6, D_SWIN[0], -5.6, D_SWIN[1], D_SWIN[2], D_SWIN[3])],
                 'east': [(-1.2, D_LDOOR[0], -1.2, D_LDOOR[1], 0.0, D_LDOOR[2])]}
        _wall_runs(pen, v, D_LIV, holes, paper, ink, kind, art=self.wall_art(o), wains=0.9, wcol=wc, seed=21, ink2=ink2,
                   scale=1.6 if st == '1979' else 1.15, trim='#efe6d4' if st != '1979' else '#7a4a28', rail=None)
        ceil_rect(pen, v, x0, x1, y0, y1, D_CEIL, c=DP['ceil'] if st != 'wait' else '#c8ccb8',
                  art=(lambda p_, W, H: pat(p_, W, H, 'tile', '#a8ac98', 160, scale=4.0)) if st == 'wait' else None)
        F, panes = window_unit(pen, v, (-1.2, 0.0), (-5.6, 0.0), -1.2 - D_LWIN[1], -1.2 - D_LWIN[0], D_LWIN[2], D_LWIN[3], lites=(3, 1),
                               frame='#efe9dc' if st != '1979' else '#e8dcc0')
        window_unit(pen, v, (-5.6, 0.0), (-5.6, 5.4), D_SWIN[0], D_SWIN[1], D_SWIN[2], D_SWIN[3], lites=(2, 2), frame='#efe9dc')
        if st != 'wait':
            fx_ = v.p(-3.4, D_CEIL, 2.7)                                         # the ceiling fixture (frosted dome)
            if v.cam_h < D_CEIL and v.d(-3.4, 2.7) > 0.3:
                pen.fill(ellipse3(v, -3.4, 2.7, 0.22, 0.22, D_CEIL - 0.06), lit('#efe8d8', (-3.4, D_CEIL - 0.1, 2.7), (0, -1, 0)))
                pen.line(ellipse3(v, -3.4, 2.7, 0.22, 0.22, D_CEIL - 0.06), 1.0)

    def wall_art(self, o):
        st = o.get('state', 'now')
        clk = o.get('clock', (3, 0))
        live_clock = callable(clk)

        def east(p_, W, H):
            u = 5.4 - D_LCLOCK[2]
            if not live_clock:
                h_, m_ = clk[0], clk[1]
                if st == 'wait': _office_clock(p_, u * 100, H - D_LCLOCK[1] * 100, 15, h_, m_, clk[2] if len(clk) > 2 else None)
                else: _sunburst_clock(p_, u * 100, H - D_LCLOCK[1] * 100, 10, h_, m_, '#c8a04a' if st == 'now' else '#d87a2a')
            _light_switch(p_, (5.4 - D_LDOOR[0] + 0.18) * 100, H - 120)
            if st == 'wait':
                _notice(p_, 40, H - 175, 42, 52, 'PLEASE', ('TAKE A NUMBER', 'AND WAIT', 'YOUR TURN'), accent='#8a2a22')
            else:
                _photo(p_, W, H, 30, H - 190, 46, 36, 'lake')
        def back(p_, W, H):
            if st == 'wait':
                _notice(p_, 140, H - 190, 60, 48, 'YOUR CALL', ('IS IMPORTANT', 'TO US', 'PLEASE HOLD'), accent='#3a5a4a')
                _notice(p_, 300, H - 182, 34, 44, 'IT CAN', ('WAIT', '', ''), accent='#5a5a3a', c='#e8e2c8')
                _photo(p_, W, H, 380, H - 200, 40, 50, 'grandpa', frame='#3a3428')
            else:
                _photo(p_, W, H, 160, H - 205, 40, 50, 'grandpa')
                _photo(p_, W, H, 215, H - 196, 52, 40, 'wedding')
                _photo(p_, W, H, 280, H - 205, 36, 46, 'nurse' if st == 'now' else 'lake')
                if st == 'now': _photo(p_, W, H, 330, H - 196, 46, 36, 'kids')
        def west(p_, W, H):
            if st == 'wait':
                _notice(p_, 50, H - 200, 50, 40, 'NO PHONE', ('CALLS AFTER', 'MIDNIGHT', ''), accent='#2a3a5a', c='#e8e4d0')
        def front(p_, W, H):
            if st != '1979':
                _photo(p_, W, H, 30, H - 196, 36, 46, 'milo' if st == 'now' else 'landscape')
        return {'east': east, 'back': back, 'west': west, 'front': front}

    def pieces(self, o):
        st = o.get('state', 'now')
        era = '1979' if st == '1979' else 'now'
        P = []
        ap = dr_armchair_parts(era=era)
        P.append(Piece('armchair', (D_ARM.cx, 0.5, D_ARM.cy), lambda pen, v, parts=ap: draw_parts(pen, v, parts),
                       occupant=[dr_arm_seat()], front=ap, block=D_ARM.footprint()))
        lamp_k = o.get('lamp', 0.0)
        cup = o.get('coffee', False)
        keys = o.get('keys', st != '1979')

        def side(pen, v):
            _round_table(pen, v, D_SIDE[0], D_SIDE[1], D_SIDE[2], D_SIDE[3], '#5a3420' if era == 'now' else '#7a4a2a')
            dr_table_lamp(pen, v, D_SIDE[0] - 0.06, D_SIDE[1] - 0.05, D_SIDE[3], 0.0, '#efe2c4' if era == 'now' else '#e8a84a',
                          '#b89a5a' if era == 'now' else '#c86a2a')
            if cup: dr_cup(pen, v, D_SIDE[0] + 0.1, D_SIDE[3], D_SIDE[1] + 0.08)
            if keys: dr_keys(pen, v, D_SIDE[0] + 0.11, D_SIDE[3], D_SIDE[1] - 0.1)
        P.append(Piece('sidetable', (D_SIDE[0], 0.4, D_SIDE[1]), side, block=_circ(D_SIDE[0], D_SIDE[1], D_SIDE[2] + 0.04)))
        P.append(Piece('curio', (D_CURIO.cx, 0.9, D_CURIO.cy), lambda pen, v: dr_curio(pen, v, era=era), block=D_CURIO.footprint()))
        dc = {'now': '#7e6a3e', '1979': '#c8742a', 'wait': '#5e6046'}[st]
        P.append(Piece('curtains', (-3.4, 1.5, 0.12), lambda pen, v: curtain_pair(pen, v, (-1.2, 0.0), (-5.6, 0.0), -1.2 - D_LWIN[1], -1.2 - D_LWIN[0],
                                                                                 D_LWIN[3], 2.0, 0.0, o.get('curtains', 1.0), dc, seed=3, sheer=False)))
        P.append(Piece('curtains_side', (-5.48, 1.5, 4.4), lambda pen, v: curtain_pair(pen, v, (-5.6, 0.0), (-5.6, 5.4), D_SWIN[0], D_SWIN[1], D_SWIN[3], 1.9, 0.0,
                                                                                      o.get('curtains', 1.0), dc, seed=4, sheer=False)))
        if not self.far:
            ang = o.get('door', 0.0)
            ang = 0.0 if callable(ang) else ang
            D = dr_living_door()
            P.append(Piece('door', (-1.23 - 0.45 * math.sin(math.radians(ang)), 1.0, 2.2 + 0.45 * math.cos(math.radians(ang))),
                           lambda pen, v, D=D, ang=ang: D.draw(pen, v, ang)))
        if st in ('now', '1979'):
            cp = couch_parts(D_COUCH, DP['couch'] if era == 'now' else DP['couch79'], DP['couch_d'] if era == 'now' else DP['couch79_d'], afghan=era == 'now')
            P.append(Piece('couch', (D_COUCH.cx, 0.45, D_COUCH.cy), lambda pen, v, parts=cp: draw_parts(pen, v, parts),
                           occupant=[(s_[1], s_[2]) for s_ in couch_seats(D_COUCH)], front=cp, block=D_COUCH.footprint()))
            P.append(Piece('coffee', (D_COFFEE.cx, 0.3, D_COFFEE.cy), lambda pen, v: draw_parts(pen, v, table_parts(D_COFFEE, '#6a3e22' if era == 'now' else '#8a5a2a', apron=0.06)),
                           block=D_COFFEE.footprint()))
            P.append(Piece('tv', (D_TV.cx, 0.4, D_TV.cy), lambda pen, v: dr_console_tv(pen, v, era=era), block=D_TV.footprint()))
        else:
            for (ri, (cx, cy)) in dr_rows_layout():
                parts, seats, B = dr_chair_row(cx, cy, len(D_ROW_X), D_ROW_X[1] - D_ROW_X[0], 0, D_CHAIR_BLUE, worn=0.5)
                P.append(Piece('row%d' % ri, (cx, 0.45, cy), lambda pen, v, parts=parts: draw_parts(pen, v, parts), occupant=seats, front=parts,
                               block=B.footprint()))
            tk = o.get('ticket', '')
            if tk != 'f' and o.get('tear', 0.0) != 'f':          # a live ticket / tear: the live layer draws the machine
                P.append(Piece('ticket_machine', (D_TICKET[0], 0.6, D_TICKET[1]), lambda pen, v: dr_ticket_machine(pen, v, ticket=tk, tear=o.get('tear', 0.0)),
                               block=_circ(D_TICKET[0], D_TICKET[1], 0.22)))
            P.append(Piece('sign', (D_SIGN[0], 2.2, D_SIGN[1]), lambda pen, v: dr_now_serving(pen, v, o.get('serving', '1979'), lit_=True)))
            P.append(Piece('wall_tv', (-1.5, 2.0, 0.42), lambda pen, v: dr_wall_tv(pen, v, k=0.0)))
            P.append(Piece('troffers', (-3.4, D_CEIL, 2.8), lambda pen, v: [dr_troffer(pen, v, x, y, 0.0, dead=(i in (1, 3))) for i, (x, y) in enumerate(D_TROFFERS)]))
        return P

    def glows(self, v, o):
        st = o.get('state', 'now')
        G = []
        kl = _kfn(o.get('lamp', 0.0), 201)
        G.append(('sidetable_glow', (D_SIDE[0], 0.9, D_SIDE[1]), lambda pen, t: dr_lamp_glow(pen, v, D_SIDE[0] - 0.06, D_SIDE[1] - 0.05, D_SIDE[3], kl(t))))
        kc = _kfn(o.get('ceiling', 0.0), 202)
        if st != 'wait':
            def ceil_glow(pen, t):
                k = kc(t)
                if k <= 0.01 or v.cam_h > D_CEIL or v.d(-3.4, 2.7) < 0.3: return
                pen.fill(ellipse3(v, -3.4, 2.7, 0.2, 0.2, D_CEIL - 0.065), '#fff6e4', 230 * k)
                gx, gy = v.p(-3.4, D_CEIL - 0.08, 2.7); pen.glow(gx, gy, 0.8 * v.s(-3.4, 2.7), '#ffe8c0', 80 * k)
            G.append(('ceiling_glow', (-3.4, D_CEIL, 2.7), ceil_glow))
        if st == 'wait':
            tubes = o.get('tubes')
            for i, (x, y) in enumerate(D_TROFFERS):
                spec = (tubes[i] if tubes else (1.0, 0.0, dict(flick=None, k=1.0, amount=1.0), 0.0)[i])
                if spec in (0, 0.0, None): continue
                kf = _dr_tube_kfn(spec, 210 + i)
                G.append(('troffers_glow%d' % i, (x, D_CEIL, y), (lambda x_, y_, kf_: lambda pen, t: dr_troffer_glow(pen, v, x_, y_, kf_(t)))(x, y, kf)))
            ks = _kfn(o.get('sign', 1.0), 215)
            G.append(('sign_glow', (D_SIGN[0], 2.2, D_SIGN[1]), lambda pen, t: dr_sign_glow(pen, v, ks(t))))
            kt = _kfn(o.get('tv', 1.0), 216)
            G.append(('wall_tv_glow', (-1.5, 2.0, 0.42), lambda pen, t: (dr_wall_tv(pen, v, k=kt(t), t=t), dr_wall_tv_glow(pen, v, k=kt(t), t=t))))
        if o.get('tod') == 'sunrise':
            def sun_glow(pen, t):
                c_ = v.p(-3.4, 1.45, 0.0)
                if v.d(-3.4, 0.0) < 0.3: return
                pen.ellipse_glow(c_[0], c_[1], 1.6 * v.s(-3.4, 0.0), 0.7 * v.s(-3.4, 0.0), '#ffd8a0', 90)
            G.append(('sun_glow', (-3.4, 1.4, 0.05), sun_glow))
        return G

    def spots(self, v, o):
        st = o.get('state', 'now')
        S = {}
        cx, cy = dr_arm_seat()
        S['armchair'] = _mk_spot(v, 'armchair', cx, cy, 0.0, 'seat', "Grandpa's brown armchair by the window, facing into the room (+y); seat 0.46 m",
                                 face=(0, 1), seat_Y=D_ARM_SEAT)
        S['armchair_front'] = _mk_spot(v, 'armchair_front', D_ARM.cx + 0.1, 1.95, 0.0, 'stand', 'in front of the armchair (bringing the coffee, the narrator facing HIM): faces -y', face=(0, -1))
        S['armchair_arm_r'] = _mk_spot(v, 'armchair_arm_r', D_ARM.cx + D_ARM.w / 2 - 0.1, D_ARM.cy + 0.15, 0.66, 'surface', "the chair's right arm top (his near hand / the ticket)")
        S['side_top'] = _mk_spot(v, 'side_top', D_SIDE[0] + 0.1, D_SIDE[1] + 0.08, D_SIDE[3], 'surface', 'the side table top by the chair (the coffee cup sits here)')
        S['keys'] = _mk_spot(v, 'keys', D_SIDE[0] + 0.11, D_SIDE[1] - 0.1, D_SIDE[3], 'surface', "Grandma's car keys on the side table")
        S['window'] = _mk_spot(v, 'window', -2.45, 0.42, 0.0, 'stand', 'at the picture window right of the chair, looking out at the driveway and down the street (faces -x -y)',
                               face=(-0.7, -0.7))
        S['window_glass'] = _mk_spot(v, 'window_glass', -2.72, 0.0, 1.45, 'point', 'the glass at the narrator\'s eye line')
        S['door'] = _mk_spot(v, 'door', -1.55, 2.65, 0.0, 'stand', 'just inside the living-room door (opening it: faces -x into the room)', face=(-1, 0))
        S['door_knob'] = _mk_spot(v, 'door_knob', -1.24, 3.02, D_KNOB_Y, 'point', 'the living-room door knob (room side, door closed)')
        S['room_mid'] = _mk_spot(v, 'room_mid', -2.7, 2.8, 0.0, 'stand', 'the middle of the room (in the waiting room: the aisle east of the rows)')
        S['clock'] = _mk_spot(v, 'clock', D_LCLOCK[0] - 0.02, D_LCLOCK[2], D_LCLOCK[1], 'point', 'the wall clock on the east wall')
        S['window_side'] = _mk_spot(v, 'window_side', -5.2, 4.4, 0.0, 'stand', 'at the side window', face=(-1, 0))
        if st in ('now', '1979'):
            for (nm, x, y) in couch_seats(D_COUCH):
                S['couch_' + nm] = _mk_spot(v, 'couch_' + nm, x, y, 0.0, 'seat', 'on the couch (%s seat), facing the window' % nm, face=(0, -1), seat_Y=D_COUCH_SEAT)
            S['coffee_top'] = _mk_spot(v, 'coffee_top', D_COFFEE.cx, D_COFFEE.cy, D_COFFEE.Y1, 'surface', 'the coffee table top')
            S['tv_screen'] = _mk_spot(v, 'tv_screen', D_TV.cx, D_TV.cy, 0.5, 'point', 'the console TV screen')
        else:
            for (ri, (cx_, cy_)) in dr_rows_layout():
                _, seats, _ = dr_chair_row(cx_, cy_, len(D_ROW_X), D_ROW_X[1] - D_ROW_X[0], 0)
                for i, (sx, sy) in enumerate(seats):
                    nm = 'seat_r%d_%d' % (ri, i)
                    S[nm] = _mk_spot(v, nm, sx, sy, 0.0, 'seat', 'waiting-room chair: row %d (0 front, 2 last), seat %d from the west (window) end; faces the armchair (-y)' % (ri, i),
                                     face=(0, -1), seat_Y=D_SEAT_H, row=ri, col=i)
            S['grandpa_seat'] = S['seat_r2_0']
            S['grandpa_seat'].note = 'GRANDPA: the last row, by the window (seat_r2_0); faces the armchair (-y)'
            S['ticket_slot'] = _mk_spot(v, 'ticket_slot', D_TICKET[0], D_TICKET[1], D_TICKET_Y - 0.06, 'point', 'the ticket machine slot (where he tears the ticket: the strip hangs below)')
            S['ticket_machine'] = _mk_spot(v, 'ticket_machine', D_TICKET[0] + 0.25, D_TICKET[1] + 0.3, 0.0, 'stand', 'beside the ticket machine (the narrator by the door)', face=(-1, -0.4))
            S['sign'] = _mk_spot(v, 'sign', D_SIGN[0], D_SIGN[1], (D_SIGN[2] + D_SIGN[3]) / 2, 'point', 'NOW SERVING 1979 over the armchair')
            S['carpet_l'] = _mk_spot(v, 'carpet_l', D_ARM.cx - 0.85, 1.75, 0.0, 'surface', "his left hand flat on the carpet (screen right in a front view)")
            S['carpet_r'] = _mk_spot(v, 'carpet_r', D_ARM.cx + 0.85, 1.75, 0.0, 'surface', 'his right hand flat on the carpet')
            S['aisle_front'] = _mk_spot(v, 'aisle_front', -2.55, 1.85, 0.0, 'stand', 'the narrator in front of the front row, facing HIM', face=(-0.8, -0.6))
            S['tv'] = _mk_spot(v, 'tv', -1.5, 0.42, 2.05, 'point', 'the TV on its bracket (showing nothing)')
        return S


def _dr_tube_kfn(spec, seed):
    """A troffer's level: a number, f(t), or dict(flick=None (random bursts) | [(t0, dur)], k, amount) -> f(t). A flickering
    tube stutters like a starter that never quite catches."""
    if isinstance(spec, dict) and 'flick' in spec and spec['flick'] is None:
        k = spec.get('k', 1.0); amt = spec.get('amount', 1.0)

        def f(t):
            u = math.floor(t * 14.0)
            h = _h(int(u), seed)
            base = 1.0 if h > 0.22 else (0.15 + 0.4 * _h(int(u), seed + 3))
            slow = 0.5 + 0.5 * math.sin(t * 0.7 + seed)
            if slow < 0.18: base *= 0.2
            return k * (1 - amt + amt * base)
        return f
    return _kfn(spec, seed)


def dr_living_door():
    """The living-room door (hinge on the hall wall at y 2.2, swinging into the living room)."""
    return Door((-1.23, D_LDOOR[0]), D_LDOOR[1] - D_LDOOR[0], D_LDOOR[2], (0.0, 1.0), 1, 0.0,
                art_a=door_art('six', 'right', bolt=False), art_b=door_art('six', 'left', bolt=False), col='#efe9dc')


def dr_keys(pen, v, x, Y, y):
    """Grandma's car keys on a ring with a red plastic tag."""
    if v.d(x, y) < 0.2: return
    s = v.s(x, y); px, py = v.p(x, Y, y)
    pen.line(oval(px, py - 0.004 * s, 0.022 * s, 0.009 * s), max(0.8, 0.004 * s), lit('#c8ccd0', (x, Y, y), None))
    for k, a in enumerate((-0.6, 0.3)):
        kx, ky = px + math.cos(a) * 0.04 * s, py - 0.004 * s + math.sin(a) * 0.01 * s
        key = poly([(kx - 0.012 * s, ky - 0.004 * s), (kx + 0.03 * s, ky - 0.003 * s), (kx + 0.03 * s, ky + 0.003 * s), (kx - 0.012 * s, ky + 0.004 * s)])
        pen.fill(key, lit('#d8c070' if k else '#c8ccd0', (x, Y, y), (0, 1, 0))); pen.line(key, 0.6)
    pen.fill(rrect(px - 0.04 * s, py - 0.01 * s, 0.025 * s, 0.014 * s, 0.004 * s), lit('#c82a2a', (x, Y, y), (0, 1, 0)))


# ---------------------------------------------------------------------------------------------- hall
class DrHall(DrRoom):
    name = 'hall'
    R = D_HALL

    def lights(self, o):
        amb = o.get('amb_h', '#262c46')
        endwin = Lamp(kind='win', c='#7a8ac8', k=0.5, soft=10.0, panes=_panes_y(D_HWIN[0], D_HWIN[1], D_HWIN[2], D_HWIN[3], 9.6),
                      d=_norm3((0.0, -0.5, -1.0)), only={'floor', 'wall', 'top', 'front', 'side'})
        steady = [endwin]
        if o.get('tod') == 'sunrise':
            amb = '#5a5060'
            steady = [Lamp(kind='win', c=D_SUN, k=0.9, soft=12.0, panes=_panes_y(D_HWIN[0], D_HWIN[1], D_HWIN[2], D_HWIN[3], 9.6), d=_norm3((0.0, -0.45, -1.0)))]
        hallL = [Lamp(-0.4, D_CEIL - 0.1, 2.2, 4.0, '#ffd8a0', 1.3, (1.0, 0.6, 0.3), fall=1.4), Lamp(-0.4, D_CEIL - 0.1, 6.8, 4.0, '#ffd8a0', 1.1, (1.0, 0.6, 0.3), fall=1.4)]
        porchL = [Lamp(-0.4, 1.9, 0.15, 2.4, '#ffc888', 0.55, fall=1.5)]
        kitL = [Lamp(-1.45, 1.6, 6.45, 2.6, '#ffd0a0', 0.55, fall=1.4)]
        livL = [Lamp(-1.35, 1.6, 2.65, 2.4, o.get('living_c', '#ffd0a0'), 0.6, fall=1.4)]
        headL = [Lamp(kind='win', c=D_HEAD, k=0.6, soft=6.0, panes=[[(-0.62, 1.95, 0.0), (-0.18, 1.95, 0.0), (-0.18, 1.78, 0.0), (-0.62, 1.78, 0.0)]],
                      d=_norm3((0.45, -0.05, 1.0)), only={'ceil', 'wall', 'floor'})]
        var = [('hall', hallL, _kfn(o.get('hall', 0.0), 221)), ('porch', porchL, _kfn(o.get('porch', 0.0), 222)),
               ('kitchen', kitL, _kfn(o.get('kitchen', 0.0), 223)), ('living', livL, _kfn(o.get('living', 0.0), 224)),
               ('headlights', headL, _kfn(o.get('headlights', 0.0), 225))]
        return amb, steady, var

    def shell(self, pen, v, o):
        x0, x1, y0, y1 = D_HALL

        def fart(p_, W, H):
            p_.texture(rect(0, 0, W, H), 'wood', 0.55, 'overlay', 0.9, 90)
            pat(p_, W, H, 'boards', '#3a2412', 150, 31)
            u0, w0 = floor_uv(x0, y1, -0.92, 9.3); u1, w1 = floor_uv(x0, y1, 0.12, 0.35)
            rr = rect(u0, w0, u1 - u0, w1 - w0)
            p_.fill(rr, DP['runner']); p_.texture(rr, 'fabric', 0.6, 'overlay', 1.0)
            p_.line(rect(u0 + 4, w0 + 4, u1 - u0 - 8, w1 - w0 - 8), 2.0, '#d8b860', 160)
            for k in range(int((w1 - w0) / 60)):
                p_.line(oval((u0 + u1) / 2, w0 + 30 + k * 60, 14, 9), 1.4, '#d8b860', 120)
        floor_rect(pen, v, x0, x1, y0, y1, 0.0, '#8a5a34', None, art=fart)
        holes = {'front': [(D_FDOOR[0], 0.0, D_FDOOR[1], 0.0, 0.0, D_FDOOR[2])],
                 'west': [(-1.2, D_LDOOR[0], -1.2, D_LDOOR[1], 0.0, D_LDOOR[2]), (-1.2, D_KDOOR[0], -1.2, D_KDOOR[1], 0.0, D_KDOOR[2])],
                 'back': [(D_HWIN[0], 9.6, D_HWIN[1], 9.6, D_HWIN[2], D_HWIN[3])],
                 'east': [(0.4, D_BDOOR[0], 0.4, D_BDOOR[1], 0.0, D_BDOOR[2]), (0.4, D_RDOOR[0], 0.4, D_RDOOR[1], 0.0, D_RDOOR[2])]}

        def west(p_, W, H):
            _photo(p_, W, H, 40, H - 185, 34, 44, 'grandpa')
            _photo(p_, W, H, 420, H - 180, 30, 38, 'nurse')
            _light_switch(p_, (D_LDOOR[1] + 0.12) * 100, H - 120)
        def east(p_, W, H):
            _photo(p_, W, H, 160, H - 178, 40, 30, 'kids')
            _photo(p_, W, H, 520, H - 182, 32, 40, 'milo')
            _photo(p_, W, H, 760, H - 186, 36, 46, 'wedding')
        def front(p_, W, H):
            _light_switch(p_, (0.4 - 0.25) * 100, H - 120)
        _wall_runs(pen, v, D_HALL, holes, DP['hall_paper'], DP['hall_ink'], 'stripe', art={'west': west, 'east': east, 'front': front},
                   wains=0.95, wcol=DP['hall_wains'], seed=23, scale=0.9, pa=60)
        ceil_rect(pen, v, x0, x1, y0, y1, D_CEIL)
        window_unit(pen, v, (x0, 9.6), (x1, 9.6), D_HWIN[0] - x0, D_HWIN[1] - x0, D_HWIN[2], D_HWIN[3], lites=(1, 1))
        for yy in (2.2, 6.8):
            if v.cam_h < D_CEIL and v.d(-0.4, yy) > 0.3:
                e = ellipse3(v, -0.4, yy, 0.16, 0.16, D_CEIL - 0.05)
                pen.fill(e, lit('#efe8d8', (-0.4, D_CEIL - 0.1, yy), (0, -1, 0))); pen.line(e, 1.0)
        # the doors' frames into the kitchen doorway: nothing (open cased opening)

    def pieces(self, o):
        P = []
        if not self.far:
            D, ang = dr_front_door(o)
            P.append(Piece('front_door', (-0.4 + 0.45 * math.sin(math.radians(ang)) * 0, 1.0, 0.05 + 0.45 * math.sin(math.radians(ang))),
                           lambda pen, v, D=D, ang=ang: D.draw(pen, v, ang)))
            la = o.get('door', 0.0); la = 0.0 if callable(la) else la
            DL = dr_living_door()
            P.append(Piece('living_door', (-1.25 - 0.45 * math.sin(math.radians(la)), 1.0, 2.2 + 0.45 * math.cos(math.radians(la))),
                           lambda pen, v, D=DL, ang=la: D.draw(pen, v, ang)))
            ba = o.get('bath_door', 0.0); ba = 0.0 if callable(ba) else ba
            DB = dr_bath_door()
            P.append(Piece('bath_door', (0.43 + 0.37 * math.sin(math.radians(ba)), 1.0, 7.05 - 0.37 * math.cos(math.radians(ba))),
                           lambda pen, v, D=DB, ang=ba: D.draw(pen, v, ang)))
            DR = Door((0.43, D_RDOOR[1]), D_RDOOR[1] - D_RDOOR[0], 2.03, (0.0, -1.0), 1, 0.0, art_a=door_art('six', 'right', bolt=False),
                      art_b=door_art('six', 'left', bolt=False), col='#efe9dc')
            P.append(Piece('ruth_door', (0.43, 1.0, 3.8), lambda pen, v, D=DR: D.draw(pen, v, 0.0)))
        P.append(Piece('coat_rack', (0.12, 1.0, 0.75), lambda pen, v: dr_coat_rack(pen, v, 0.12, 0.75), block=_circ(0.12, 0.75, 0.22)))
        P.append(Piece('hall_table', (-1.05, 0.5, 1.35), lambda pen, v: dr_hall_table(pen, v, -1.05, 1.35), block=_box_pts(-1.05, 1.35, 0.15, 0.38)))
        return P

    def glows(self, v, o):
        kh = _kfn(o.get('hall', 0.0), 221)

        def g(pen, t):
            k = kh(t)
            if k <= 0.01 or v.cam_h > D_CEIL: return
            for yy in (2.2, 6.8):
                if v.d(-0.4, yy) < 0.3: continue
                pen.fill(ellipse3(v, -0.4, yy, 0.14, 0.14, D_CEIL - 0.055), '#fff6e4', 230 * k)
                gx, gy = v.p(-0.4, D_CEIL - 0.08, yy); pen.glow(gx, gy, 0.7 * v.s(-0.4, yy), '#ffe8c0', 70 * k)
        kp = _kfn(o.get('porch', 0.0), 222)

        def lite(pen, t):                                                       # the porch light through the half-moon lite
            k = kp(t)
            if k <= 0.01 or self.far: return
            fa = o.get('front_door', 0.0)
            if callable(fa) or fa > 2: return
            cx_, cy_ = v.p(-0.4, 1.78, 0.04)
            if v.d(-0.4, 0.04) < 0.3: return
            s = v.s(-0.4, 0.04)
            path = inter(oval(cx_, cy_, 0.27 * s, 0.183 * s), rect(cx_ - 0.3 * s, cy_ - 0.2 * s, 0.6 * s, 0.2 * s))
            pen.fill(path, '#ffdca0', 200 * k)
            pen.glow(cx_, cy_ - 0.06 * s, 0.6 * s, '#ffc880', 60 * k)
        return [('hall_glow', (-0.4, D_CEIL, 4.5), g), ('front_door_glow', (-0.4, 1.8, 0.06), lite)]

    def spots(self, v, o):
        S = {}
        S['door_inside'] = _mk_spot(v, 'door_inside', -0.4, 0.5, 0.0, 'stand', 'inside the front door, facing it (-y)', face=(0, -1))
        S['peephole_eye'] = _mk_spot(v, 'peephole_eye', -0.4, 0.3, 0.0, 'stand', 'eye to the peephole (the narrator on tiptoe: 1.5 m)', face=(0, -1))
        S['peephole'] = _mk_spot(v, 'peephole', -0.4, 0.07, D_PEEP_Y, 'point', 'the peephole (inside face)')
        S['knob'] = _mk_spot(v, 'knob', D_FDOOR[1] - 0.075, 0.07, D_KNOB_Y, 'point', 'the front door knob (inside, east side)')
        S['deadbolt'] = _mk_spot(v, 'deadbolt', D_FDOOR[1] - 0.075, 0.07, D_KNOB_Y + 0.17, 'point', 'the deadbolt thumb-turn')
        S['under_door'] = _mk_spot(v, 'under_door', -0.35, 0.12, 0.0, 'surface', 'the floor just inside the door: the results slide under here')
        S['door_through'] = _mk_spot(v, 'door_through', -0.35, -0.3, 0.0, 'stand', 'in the open front doorway (the narrator stepping out)', face=(0, -1))
        S['hall_mid'] = _mk_spot(v, 'hall_mid', -0.4, 4.5, 0.0, 'stand', 'the middle of the hall')
        S['hall_back'] = _mk_spot(v, 'hall_back', -0.4, 8.7, 0.0, 'stand', 'the dark end of the hall (where the pen clicks)')
        S['living_door'] = _mk_spot(v, 'living_door', -0.85, 2.65, 0.0, 'stand', 'at the living-room door, facing it (-x): "When I opened the door..."', face=(-1, 0))
        S['living_knob'] = _mk_spot(v, 'living_knob', -1.18, 3.02, D_KNOB_Y, 'point', 'the living-room door knob (hall side)')
        S['kitchen_door'] = _mk_spot(v, 'kitchen_door', -0.85, 6.45, 0.0, 'stand', 'at the kitchen doorway', face=(-1, 0))
        S['bath_door'] = _mk_spot(v, 'bath_door', 0.0, 6.68, 0.0, 'stand', 'at the bathroom door', face=(1, 0))
        return S


def dr_bath_door():
    return Door((0.43, D_BDOOR[1]), D_BDOOR[1] - D_BDOOR[0], 2.03, (0.0, -1.0), 1, 0.0, art_a=door_art('six', 'right', bolt=False),
                art_b=door_art('six', 'left', bolt=False), col='#efe9dc')


# ---------------------------------------------------------------------------------------------- kitchen
class DrKitchen(DrRoom):
    name = 'kitchen'
    R = D_KIT

    def lights(self, o):
        era = o.get('era', 'now')
        amb = '#2a3150' if era != '1979' else '#34304a'
        win = Lamp(kind='win', c='#8a9ad8', k=0.6, soft=8.0, panes=_panes_y(D_KWIN[0], D_KWIN[1], D_KWIN[2], D_KWIN[3], 9.6),
                   d=_norm3((0.15, -0.5, -1.0)), only={'floor', 'top', 'front', 'side', 'wall'})
        steady = [win]
        if o.get('tod') == 'sunrise':
            amb = '#5e5460'
            steady = [Lamp(kind='win', c=D_SUN, k=1.0, soft=12.0, panes=_panes_y(D_KWIN[0], D_KWIN[1], D_KWIN[2], D_KWIN[3], 9.6), d=_norm3((0.35, -0.4, -1.0)))]
        hood = [Lamp(D_STOVE.cx, 1.55, 9.3, 3.4, '#ffcf90', 1.25, (1.0, 0.7, 0.5), fall=1.5)]
        ceil_ = [Lamp(D_KTABLE.cx, 2.0, D_KTABLE.cy, 6.0, '#ffe0b0', 1.7, (1.0, 0.75, 0.6), fall=1.35)]
        hall_ = [Lamp(-1.0, 1.7, 6.45, 2.4, '#ffd8a0', 0.5, fall=1.5)]
        fire = [Lamp(-3.3, 1.15, 9.25, 3.0, '#ff9a48', 1.6, fall=1.5)]
        night = [Lamp(-1.24, 1.05, 8.3, 1.9, '#ffd8a0', 0.75, fall=1.4)]
        var = [('hood', hood, _kfn(o.get('hood', 1.0), 231)), ('ceiling', ceil_, _kfn(o.get('ceiling', 0.0), 232)),
               ('hall', hall_, _kfn(o.get('hall', 0.0), 233)), ('fire', fire, _kfn(o.get('fire', 0.0), 234)),
               ('nightlight', night, _kfn(o.get('nightlight', 1.0), 235))]
        return amb, steady, var

    def shell(self, pen, v, o):
        x0, x1, y0, y1 = D_KIT
        era = o.get('era', 'now')
        fa, fb = (DP['floor_a'], DP['floor_b']) if era != '1979' else ('#e8c880', '#8a5a2a')
        floor_rect(pen, v, x0, x1, y0, y1, 0.0, fa, 'checker', fb, seed=41, scale=1.0)
        holes = {'back': [(D_KWIN[0], 9.6, D_KWIN[1], 9.6, D_KWIN[2], D_KWIN[3])],
                 'east': [(-1.2, D_KDOOR[0], -1.2, D_KDOOR[1], 0.0, D_KDOOR[2])]}
        clk = o.get('clock', (3, 0))

        def front(p_, W, H):
            if not callable(clk):
                u = -1.2 - D_KCLOCK[0]
                _kitchen_clock(p_, u * 100, H - D_KCLOCK[1] * 100, 13, clk[0], clk[1], era)
            _calendar_d(p_, (-1.2 - (-3.75)) * 100 - 15, H - 178, 30, 42, era)
            # a plate rail by the hall doorway: three of Ruth's good plates and the egg timer (the wall was bare)
            sx_ = (-1.2 - (-1.95)) * 100
            p_.fill(rect(sx_ - 36, H - 150, 72, 3.2), '#6a4a2e' if era != '1979' else '#7a4a22'); p_.fill(rect(sx_ - 36, H - 146.8, 72, 1.2), '#000000', 70)
            for k, pc in enumerate(('#e8eef4', '#f2e8d0', '#e8eef4')):
                px_ = sx_ - 22 + k * 22
                p_.fill(oval(px_ + 0.8, H - 159.2, 9.6), '#000000', 60)
                p_.fill(oval(px_, H - 160, 9.6), pc); p_.line(oval(px_, H - 160, 9.6), 0.5, '#000000', 150)
                p_.line(oval(px_, H - 160, 6.2), 0.9, '#3a5a8a' if k != 1 else '#a86a3a', 190)
                p_.fill(oval(px_, H - 160, 2.0), '#3a5a8a' if k != 1 else '#a86a3a', 150)
            for k in range(2):                                                  # the brackets
                bx_ = sx_ - 28 + k * 56
                p_.fill(poly([(bx_ - 1.5, H - 146.8), (bx_ + 1.5, H - 146.8), (bx_ + 1.5, H - 138)]), '#4a321e')
        def east(p_, W, H):
            u = 9.6 - D_JACK[2]
            _wall_jack(p_, u * 100, H - D_JACK[1] * 100, plugged=o.get('cord', 'in') == 'in')
            _light_switch(p_, (9.6 - 5.85) * 100, H - 120)
            nx_ = (9.6 - 8.3) * 100                                                  # outlet + the shell nightlight above the counter
            p_.fill(rrect(nx_ - 3.5, H - 112, 7, 11, 0.8), '#ece4d0'); p_.line(rrect(nx_ - 3.5, H - 112, 7, 11, 0.8), 0.4, '#000000', 140)
            p_.fill(oval(nx_, H - 109, 3.2, 3.6), '#f8ecd0')
            # Ruth's numbers card pinned by the phone ("IMPORTANT NUMBERS" in her hand; LARKFIELD GENERAL crossed out)
            cx_ = (9.6 - 7.05) * 100
            p_.fill(rect(cx_ - 8, H - 170, 16, 22), '#000000', 60); p_.fill(rect(cx_ - 8.6, H - 171, 16, 22), '#f4efe0')
            btext(p_, 'NUMBERS', cx_ - 0.6, H - 166, 'hand', 2.4, '#2a3a8a', 230, 'center')
            for k in range(5): p_.seg((cx_ - 7, H - 162 + k * 3.2), (cx_ + 5 - (k % 3) * 2, H - 162 + k * 3.2), 0.4, '#3a4a9a', 180)
            p_.seg((cx_ - 7.5, H - 155.6), (cx_ + 5.5, H - 155.6), 0.6, '#2a2a2a', 220)
            p_.fill(oval(cx_ - 0.6, H - 170, 0.8), '#c82a2a')
        def west(p_, W, H):
            _photo(p_, W, H, 110, H - 200, 30, 38, 'milo')
        paper = DP['kit_wall'] if era != '1979' else '#e8d498'
        _wall_runs(pen, v, D_KIT, holes, paper, DP['kit_ink'] if era != '1979' else '#d8a850', 'ditsy', art={'front': front, 'east': east, 'west': west},
                   wains=0.0, seed=25, scale=1.0, pa=90)
        ceil_rect(pen, v, x0, x1, y0, y1, D_CEIL)
        window_unit(pen, v, (x0, 9.6), (x1, 9.6), D_KWIN[0] - x0, D_KWIN[1] - x0, D_KWIN[2], D_KWIN[3], lites=(2, 1))
        _cafe_curtain_d(pen, v, era)
        dr_counters(pen, v, o)
        if v.cam_h < D_CEIL and v.d(D_KTABLE.cx, D_KTABLE.cy) > 0.3:          # the schoolhouse pendant over the table
            top = v.p(D_KTABLE.cx, D_CEIL, D_KTABLE.cy); bot = v.p(D_KTABLE.cx, 2.1, D_KTABLE.cy)
            pen.seg(top, bot, max(1.0, 0.008 * v.s(D_KTABLE.cx, D_KTABLE.cy)), '#2a2a2a')
            pen.fill(ellipse3(v, D_KTABLE.cx, D_KTABLE.cy, 0.17, 0.17, 2.02), lit('#efe8d8', (D_KTABLE.cx, 2.05, D_KTABLE.cy), None))
            sh = v.poly3([(D_KTABLE.cx - 0.08, 2.15, D_KTABLE.cy), (D_KTABLE.cx + 0.08, 2.15, D_KTABLE.cy), (D_KTABLE.cx + 0.17, 2.02, D_KTABLE.cy), (D_KTABLE.cx - 0.17, 2.02, D_KTABLE.cy)])
            pen.fill(sh, lit('#f2ece0', (D_KTABLE.cx, 2.08, D_KTABLE.cy), None)); pen.line(sh, 1.0)
        paper_ = o.get('paper')
        if paper_ == 'ash' and v.cam_h > D_COUNTER_Y:
            px, py = v.p(-3.5, D_COUNTER_Y - 0.15, 9.3); s = v.s(-3.5, 9.3)
            pen.fill(_blob(px, py, 0.08 * s, 0.03 * s, 9, 3, 0.4), '#1a1614', 230)
            pen.fill(_blob(px + 0.02 * s, py - 0.004 * s, 0.05 * s, 0.018 * s, 9, 4, 0.4), '#3a3632', 200)

    def pieces(self, o):
        era = o.get('era', 'now')
        P = [Piece('fridge', (D_FRIDGE.cx, 0.9, D_FRIDGE.cy), lambda pen, v: dr_fridge(pen, v, o), block=D_FRIDGE.footprint()),
             Piece('table', (D_KTABLE.cx, 0.4, D_KTABLE.cy), lambda pen, v: dr_kitchen_table(pen, v, o), block=D_KTABLE.footprint())]
        for (nm, x, y, fa, face) in dr_kitchen_chairs():
            P.append(Piece(nm, (x, 0.45, y), (lambda x_, y_, fa_: lambda pen, v: _kchair(pen, v, x_, y_, fa_))(x, y, fa), block=_circ(x, y, 0.24)))
        ph = o.get('phone', 'hung'); rg = o.get('ring', 0.0)
        if not callable(ph) and not callable(rg) and ph != 'f' and rg != 'f':
            P.append(Piece('phone', (D_PHONE[0] - 0.05, 1.3, D_PHONE[2]), lambda pen, v: dr_wall_phone(pen, v, ph, o.get('cord', 'in'), rg, 0.0, era)))
        return P

    def glows(self, v, o):
        kh = _kfn(o.get('hood', 1.0), 231)

        def hood(pen, t):
            k = kh(t)
            if k <= 0.01: return
            q = v.poly3([(D_STOVE.cx - 0.3, 1.619, 9.2), (D_STOVE.cx + 0.3, 1.619, 9.2), (D_STOVE.cx + 0.3, 1.619, 9.5), (D_STOVE.cx - 0.3, 1.619, 9.5)])
            if not q.isEmpty() and v.cam_h < 1.62: pen.fill(q, '#fff2d8', 220 * k)
            gx, gy = v.p(D_STOVE.cx, 1.58, 9.35)
            if v.d(D_STOVE.cx, 9.35) > 0.3: pen.glow(gx, gy, 0.5 * v.s(D_STOVE.cx, 9.35), '#ffe0b0', 70 * k)
        kc = _kfn(o.get('ceiling', 0.0), 232)

        def pend(pen, t):
            k = kc(t)
            if k <= 0.01 or v.d(D_KTABLE.cx, D_KTABLE.cy) < 0.3: return
            gx, gy = v.p(D_KTABLE.cx, 2.0, D_KTABLE.cy)
            pen.fill(ellipse3(v, D_KTABLE.cx, D_KTABLE.cy, 0.16, 0.16, 2.015), '#fff6e4', 240 * k)
            pen.glow(gx, gy, 0.8 * v.s(D_KTABLE.cx, D_KTABLE.cy), '#ffe8c0', 80 * k)
        return [('hood_glow', (D_STOVE.cx, 1.6, 9.35), hood), ('pendant_glow', (D_KTABLE.cx, 2.05, D_KTABLE.cy), pend)]

    def spots(self, v, o):
        S = {}
        P = dr_phone_points()
        S['phone'] = _mk_spot(v, 'phone', -1.58, 7.42, 0.0, 'stand', 'Grandma at the wall phone, facing it (+x); the receiver at her right ear', face=(1, 0))
        S['phone_beside'] = _mk_spot(v, 'phone_beside', -1.8, 6.95, 0.0, 'stand', 'the narrator beside her, leaning in to hear the tilted receiver', face=(0.55, 0.85))
        S['phone_base'] = _mk_spot(v, 'phone_base', *P['base'][::2], P['base'][1], kind='point', note='the wall phone body (centre)')
        S['phone_hook'] = _mk_spot(v, 'phone_hook', P['hook'][0], P['hook'][2], P['hook'][1], 'point', 'the handset hung on its hook (the grip centre: pick up here)')
        S['phone_cord_base'] = _mk_spot(v, 'phone_cord_base', P['cord_base'][0], P['cord_base'][2], P['cord_base'][1], 'point',
                                        "the coil cord's socket at the base bottom (CH.draw_coil_cord's base end)")
        S['jack'] = _mk_spot(v, 'jack', D_JACK[0] + 0.01, D_JACK[2], D_JACK[1], 'point', 'the wall jack on the baseboard (the line cord: "pulled the cord out of the wall")')
        S['receiver_counter'] = _mk_spot(v, 'receiver_counter', D_RECEIVER[0], D_RECEIVER[2], D_RECEIVER[1], 'surface', 'the receiver laid on the counter like a sleeping baby')
        S['plug_floor'] = _mk_spot(v, 'plug_floor', D_PLUG_FLOOR[0], D_PLUG_FLOOR[2], 0.0, 'surface', '"The phone cord was lying on the kitchen floor" (the plug end)')
        S['counter'] = _mk_spot(v, 'counter', -1.5, 8.75, D_COUNTER_Y, 'surface', 'the counter return under the phone')
        S['sink'] = _mk_spot(v, 'sink', -3.3, 8.6, 0.0, 'stand', 'at the sink under the window (burning the paper): faces +y', face=(0, 1))
        S['sink_bowl'] = _mk_spot(v, 'sink_bowl', -3.52, 9.29, D_COUNTER_Y - 0.17, 'surface', 'the bottom of the left sink bowl (the paper burns here)')
        S['window'] = _mk_spot(v, 'window', -3.3, 9.58, 1.5, 'point', 'the window over the sink')
        S['floor_rock'] = _mk_spot(v, 'floor_rock', -2.1, 8.5, 0.0, 'floor_sit', "Grandma sitting on the floor, her back against the counter return's cabinets (under the "
                                   'receiver that plays the hold music), rocking Milo: faces -x', face=(-1, 0))
        S['floor_kneel'] = _mk_spot(v, 'floor_kneel', -2.95, 8.25, 0.0, 'kneel', 'the narrator crouching in front of them (picking Milo up): faces +x', face=(1, 0.3))
        S['milo_enter'] = _mk_spot(v, 'milo_enter', -1.45, 6.45, 0.0, 'stand', 'Milo coming in from the hall doorway (faces -x)', face=(-1, 0.2))
        S['hall_doorway'] = _mk_spot(v, 'hall_doorway', -1.2, 6.45, 0.0, 'stand', 'in the doorway to the dark hall')
        S['table_top'] = _mk_spot(v, 'table_top', D_KTABLE.cx, D_KTABLE.cy, D_KTABLE.Y1, 'surface', 'the kitchen table top (Milo\'s water glass at +0.3, -0.12)')
        for (nm, x, y, fa, face) in dr_kitchen_chairs():
            S[nm] = _mk_spot(v, nm, x, y, 0.0, 'seat', 'a red kitchen chair at the table', face=face, seat_Y=0.46)
        S['kitchen_mid'] = _mk_spot(v, 'kitchen_mid', -2.3, 7.9, 0.0, 'stand', 'the open floor between the table and the sink')
        S['fridge'] = _mk_spot(v, 'fridge', D_FRIDGE.cx + 0.75, D_FRIDGE.cy, 0.0, 'stand', 'at the fridge', face=(-1, 0))
        S['clock'] = _mk_spot(v, 'clock', D_KCLOCK[0], D_KCLOCK[2] + 0.02, D_KCLOCK[1], 'point', 'the kitchen clock')
        return S


def _kitchen_clock(p_, x, y, r, hh, mm, era='now'):
    """A red plastic kitchen clock (1979: harvest gold)."""
    c = '#c83a32' if era != '1979' else '#d8a040'
    p_.fill(oval(x + 1.0, y + 1.6, r * 1.12), '#000000', 80)
    p_.fill(oval(x, y, r * 1.12), c); p_.fill(oval(x, y, r * 0.92), '#f6f2e6')
    p_.fill(oval(x - r * 0.4, y - r * 0.6, r * 0.5, r * 0.25), '#ffffff', 50)
    _hands(p_, x, y, r * 0.92, hh, mm)


def _calendar_d(p_, x, y, w, h, era='now'):
    """The Larkfield General calendar (Mom's hospital); 1979 a feed-store calendar."""
    p_.fill(rect(x + 1, y + 1.5, w, h), '#000000', 70)
    p_.fill(rect(x, y, w, h), '#f4efe2'); p_.fill(rect(x, y, w, h * 0.42), '#3a7aa8' if era != '1979' else '#a86a2a')
    btext(p_, 'LARKFIELD GENERAL' if era != '1979' else 'MILLER FEED & SEED', x + w / 2, y + h * 0.12, 'sans_b', h * 0.055, '#ffffff', 230, 'center')
    if era != '1979':
        p_.fill(rect(x + w * 0.45, y + h * 0.17, w * 0.1, h * 0.18), '#ffffff'); p_.fill(rect(x + w * 0.37, y + h * 0.23, w * 0.26, h * 0.06), '#ffffff')
    btext(p_, 'APRIL' if era != '1979' else 'MARCH 1979', x + w / 2, y + h * 0.5, 'sans_b', h * 0.06, '#3a3a3a', 230, 'center')
    for r in range(5):
        for c in range(7):
            p_.fill(rect(x + 2 + c * (w - 4) / 7, y + h * 0.56 + r * h * 0.085, (w - 4) / 7 - 0.6, h * 0.075), '#e8e2d2')


# ---------------------------------------------------------------------------------------------- bathroom
class DrBath(DrRoom):
    name = 'bath'
    R = D_BATH

    def lights(self, o):
        amb = '#2c3452'
        win = Lamp(kind='win', c='#8a9ad8', k=0.4, soft=12.0, panes=_panes_y(D_BWIN[0], D_BWIN[1], D_BWIN[2], D_BWIN[3], 9.6), d=_norm3((0.0, -0.5, -1.0)))
        steady = [win]
        if o.get('tod') == 'sunrise':
            amb = '#5a5462'
        van = [Lamp(2.55, 2.2, 6.75, 3.4, '#fff0d4', 0.95, (1.0, 0.8, 0.7), fall=1.6)]
        ceil_ = [Lamp(1.6, D_CEIL - 0.1, 7.6, 4.5, '#fff0d8', 1.2, (1.0, 0.6, 0.3), fall=1.4)]
        hall_ = [Lamp(0.25, 1.6, 6.67, 2.4, '#ffd8a0', 0.6, fall=1.5)]
        lamp_ = [Lamp(2.55, 1.15, 7.25, 3.0, D_LAMP, 1.2, fall=1.5)]
        var = [('vanity', van, _kfn(o.get('vanity', 1.0), 241)), ('ceiling', ceil_, _kfn(o.get('ceiling', 0.0), 242)),
               ('hall', hall_, _kfn(o.get('hall', 0.0), 243)), ('lamp', lamp_, _kfn(o.get('lamp', 0.0), 244))]
        return amb, steady, var

    def shell(self, pen, v, o):
        x0, x1, y0, y1 = D_BATH
        floor_rect(pen, v, x0, x1, y0, y1, 0.0, DP['bath_floor'], 'hex', '#3a6a7a', '#f2f0ea', seed=43)
        holes = {'west': [(0.4, D_BDOOR[0], 0.4, D_BDOOR[1], 0.0, D_BDOOR[2])],
                 'back': [(D_BWIN[0], 9.6, D_BWIN[1], 9.6, D_BWIN[2], D_BWIN[3])],
                 'east': [(2.8, D_CAB[1], 2.8, D_CAB[2], D_CAB[3], D_CAB[4], )]}

        def tile_art(side):
            def art(p_, W, H):
                th = 120.0
                p_.fill(rect(0, H - th, W, th), DP['bath_tile'])
                p_.cv.save(); p_.cv.translate(0, H - th); pat(p_, W, th, 'tile', '#6a9aa4', 220, scale=1.0); p_.cv.restore()
                p_.fill(rect(0, H - th - 3, W, 3), '#1a2a30'); p_.fill(rect(0, H - th - 3, W, 0.8), '#ffffff', 60)
                if side == 'front':
                    p_.fill(rect(60, H - 140, 50, 2.5), '#c8ccd0'); p_.fill(rect(64, H - 138, 42, 40), '#e8c8d0')   # towel bar + towel
                    p_.line(rect(64, H - 138, 42, 40), 0.6, '#000000', 120)
            return art
        for (side, a, b, u_of) in _walls_of(D_BATH):
            hs = []
            for (xa, ya, xb, yb, v0, v1) in holes.get(side, []):
                hs.append(_hole_x(u_of, xa, xb, ya, yb, v0, v1) + ((('nocase',) if side == 'east' else ())))
            hs = [((h[0], h[1], h[2], h[3], '', 'nocase') if len(h) > 4 else h) for h in hs]
            wall(pen, v, a, b, 0.0, D_CEIL, DP['bath_wall'], None, None, hs, art=tile_art(side), wains=0.0, base_h=0.0, crown=0.04, seed=27,
                 thick=(0.0 if side == 'east' else WT))
        ceil_rect(pen, v, x0, x1, y0, y1, D_CEIL)
        window_unit(pen, v, (x0, 9.6), (x1, 9.6), D_BWIN[0] - x0, D_BWIN[1] - x0, D_BWIN[2], D_BWIN[3], lites=(1, 1))
        F = Face((D_BWIN[0], D_BWIN[3], 9.55), (1, 0, 0), (0, -1, 0), (D_BWIN[1] - D_BWIN[0]) * 100, (D_BWIN[3] - D_BWIN[2]) * 100, (0, 0, -1), 'front')
        draw_face(pen, v, F, lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'grunge', 0.6, 'overlay', 0.4), '#a8b4c8', ao=False, lw=0.8)
        # mirror-cabinet recess (clipped to its hole in the wall)
        q = [(2.8, D_CAB[4], D_CAB[1]), (2.8, D_CAB[4], D_CAB[2]), (2.8, D_CAB[3], D_CAB[2]), (2.8, D_CAB[3], D_CAB[1])]
        clip = v.poly3(q)
        if not clip.isEmpty() and v.hx < 2.8:
            pen.cv.save(); pen.cv.clipPath(clip, skia.ClipOp.kIntersect, True)
            dr_cabinet_box(pen, v, o)
            pen.cv.restore()
            fr = Face((2.788, D_CAB[4] + 0.025, D_CAB[1] - 0.025), (0, 0, 1), (0, -1, 0), (D_CAB[2] - D_CAB[1] + 0.05) * 100, (D_CAB[4] - D_CAB[3] + 0.05) * 100, (-1, 0, 0), 'front')
            draw_face(pen, v, fr, lambda p_, W, H: p_.linear(rect(0, 0, W, H), 0, 0, W, H, [(0, '#f8f8f8', 255), (0.5, '#a8acb0', 255), (1, '#e8eaec', 255)]),
                      '#c8ccd0', holes=[rect(2.5, 2.5, W_ - 5, H_ - 5) for (W_, H_) in [((D_CAB[2] - D_CAB[1] + 0.05) * 100, (D_CAB[4] - D_CAB[3] + 0.05) * 100)]], ao=False, lw=0.9)
        dr_vanity_light(pen, v, 0.0)

    def pieces(self, o):
        ang = o.get('cabinet', 0.0)
        ang = 0.0 if callable(ang) else ang * 105.0 if ang <= 1.0 else ang
        D = dr_cabinet_door(o)
        P = [Piece('sink', (D_BSINK[0], 0.6, D_BSINK[1]), lambda pen, v: dr_pedestal_sink(pen, v), block=_box_pts(D_BSINK[0], D_BSINK[1], 0.22, 0.28)),
             Piece('toilet', (D_TOILET[0], 0.4, D_TOILET[1]), lambda pen, v: dr_toilet(pen, v), block=_box_pts(D_TOILET[0], D_TOILET[1], 0.35, 0.22)),
             Piece('tub', (D_TUB.cx, 0.3, D_TUB.cy), lambda pen, v: dr_tub(pen, v), block=D_TUB.footprint()),
             Piece('cabinet_door', (D_CAB[0] - 0.28 * math.sin(math.radians(ang)) - 0.02, 1.6, D_CAB[1] + 0.28 * math.cos(math.radians(ang))),
                   lambda pen, v, D=D, ang=ang: D.draw(pen, v, ang))]
        if not self.far:
            ba = o.get('bath_door', 80.0); ba = 80.0 if callable(ba) else ba
            DB = dr_bath_door()
            P.append(Piece('bath_door', (0.43 + 0.37 * math.sin(math.radians(ba)), 1.0, 7.05 - 0.37 * math.cos(math.radians(ba))),
                           lambda pen, v, D=DB, ang=ba: D.draw(pen, v, ang)))
        if o.get('lamp_prop'):
            P.append(Piece('lamp_prop', (2.55, 1.0, 7.25), lambda pen, v: dr_table_lamp(pen, v, 2.6, 7.28, 0.9, 0.0, h=0.42)))
        return P

    def glows(self, v, o):
        kv = _kfn(o.get('vanity', 1.0), 241)
        kl = _kfn(o.get('lamp', 0.0), 244)

        def g(pen, t):
            k = kv(t)
            if k > 0.01:
                x, y0, y1, Y0, Y1 = D_CAB
                for j in range(3):
                    yy = y0 + (y1 - y0) * (0.18 + 0.32 * j)
                    if v.d(x - 0.08, yy) < 0.15: continue
                    px, py = v.p(x - 0.08, Y1 + 0.16, yy); s = v.s(x - 0.08, yy)
                    pen.fill(oval(px, py, 0.048 * s), '#fffaf0', 240 * k)
                    pen.glow(px, py, 0.3 * s, '#fff0d0', 90 * k)
            if o.get('lamp_prop'): dr_lamp_glow(pen, v, 2.6, 7.28, 0.9, kl(t), h=0.42)
        return [('vanity_glow', (D_CAB[0] - 0.1, 2.1, 6.75), g)]

    def spots(self, v, o):
        S = {}
        S['sink'] = _mk_spot(v, 'sink', 2.02, 6.75, 0.0, 'stand', 'at the sink facing the medicine cabinet (+x)', face=(1, 0))
        S['sink_watch'] = _mk_spot(v, 'sink_watch', 1.55, 7.45, 0.0, 'stand', 'the narrator watching Grandma at the cabinet', face=(0.75, -0.65))
        S['door_in'] = _mk_spot(v, 'door_in', 0.75, 6.68, 0.0, 'stand', 'just inside the bathroom door', face=(1, 0))
        S['mirror'] = _mk_spot(v, 'mirror', D_CAB[0] - 0.03, (D_CAB[1] + D_CAB[2]) / 2, (D_CAB[3] + D_CAB[4]) / 2, 'point', 'the cabinet mirror centre (closed)')
        ang = o.get('cabinet', 0.0)
        ang = 0.0 if callable(ang) else ang * 105.0 if ang <= 1.0 else ang
        D = dr_cabinet_door(o)
        cp = D.point(ang, (D_CAB[2] - D_CAB[1]) * 0.5, 0.33, 'a', 0.003)
        S['card'] = _mk_spot(v, 'card', cp[0], cp[2], cp[1], 'point', 'the yellow card taped inside the cabinet door (at the current door angle): "tapped the little yellow card"')
        S['cab_shelf'] = _mk_spot(v, 'cab_shelf', D_CAB[0] + 0.06, (D_CAB[1] + D_CAB[2]) / 2, D_CAB[3] + 0.245, 'surface', 'the middle shelf inside')
        S['tub_edge'] = _mk_spot(v, 'tub_edge', D_TUB.cx, D_TUB.cy - 0.32, 0.0, 'seat', 'sitting on the tub edge', face=(0, -1), seat_Y=0.56)
        return S


# ====================================================================================================== outside: Larch Street
D_EAVE = 2.85
D_RIDGE = 5.2
D_LAMPS = [(-30.0, -12.6), (-6.0, -12.6), (18.0, -12.6), (42.0, -12.6)]       # sodium streetlights on the north kerb
D_BUS_LAMP = (-44.6, -21.1)                                                   # the flickering streetlight over the bus stop
D_MAPLE = (3.2, -6.2)
D_NEIGH = [(-21.0, -15.0, 0.0, 'w'), (8.4, 17.5, 0.0, 'e'), (-30.0, -20.0, 0.0, 'w2')]   # neighbours (x0, x1, front y, tag)
D_ACROSS = [(-38.0, -27.0), (-22.0, -11.0), (-6.0, 5.0), (10.0, 21.0)]          # houses across the street (x0, x1), front at y -24.5
D_CAR_FA = 180                                                                 # the car faces +y (nose to the house)
DCAR = dict(L=4.45, W=1.78, H=1.46, wb=2.62, hood=0.92, belt=0.98)


def dr_sky(pen, v, tod='night', box=(-800, -600, 2720, 1680)):
    """The sky over Larch Street: a low overcast night (dark, the sodium glow of the town on the cloud bottoms near the
    horizon, rain-cloud texture) or a washed sunrise after the rain."""
    x0, y0, x1, y1 = box
    r = rect(x0, y0, x1 - x0, y1 - y0)
    H = v.h
    if tod == 'night':
        pen.linear(r, 0, H - 1.0 * v.S, 0, H + 20, [(0, '#05070c'), (0.55, '#0b0e18'), (0.85, '#1a1824'), (1, '#33262a')])
        rng = np.random.default_rng(13)
        for i in range(14):
            az = rng.uniform(-180, 180); el = rng.uniform(4, 28)
            q = sky_dir(v, az, el)
            if q is None: continue
            w = rng.uniform(0.4, 0.9) * v.S; h = w * 0.1
            _cloud(pen, q[0], q[1], w, h, int(rng.integers(0, 999)), '#0c0f1a', '#2a2834', 120)
    else:
        pen.linear(r, 0, H - 1.0 * v.S, 0, H + 20, [(0, '#5a6a98'), (0.6, '#c8a0a0'), (1, '#ffd0a0')])
        sp_ = sky_dir(v, 100.0, 4.0)
        if sp_: pen.radial(None, sp_[0], sp_[1], 1.3 * v.S, [(0, '#fff0c8', 220), (0.3, '#ffb070', 100), (1, '#ff9a6a', 0)], sy=0.45, clip=False)


def dr_far_ring(pen, v, tod='night', R=85.0, cx=-8.0, cy=-10.0, G=D_GROUND):
    """Closes the horizon all round: two rings of distant tree crowns and roofs (rounded silhouettes in the haze)."""
    c_far = '#0e111a' if tod == 'night' else '#8a7a86'
    c_near = '#080a10' if tod == 'night' else '#5e4e5c'
    for (RR, col_, hs, seed) in ((R * 1.3, c_far, 0.9, 3), (R, c_near, 1.15, 5)):
        rng = np.random.default_rng(seed)
        N = 720
        hgt = np.full(N, 4.0)
        az = np.arange(N) / 2.0
        for _ in range(170):                                               # tree crowns: rounded bumps
            c_ = rng.uniform(0, 360); w_ = rng.uniform(2.2, 5.5); A = rng.uniform(3.0, 7.5)
            dd = (az - c_ + 180) % 360 - 180
            hgt = np.maximum(hgt, 4.0 + A * np.sqrt(np.clip(1 - (dd / w_) ** 2, 0, 1)))
        for _ in range(40):                                                # roofs: low gables
            c_ = rng.uniform(0, 360); w_ = rng.uniform(1.2, 2.2); A = rng.uniform(5.0, 6.5)
            dd = np.abs((az - c_ + 180) % 360 - 180)
            hgt = np.maximum(hgt, np.where(dd < w_, A - (dd / w_) * 1.6, 0))
        segs, cur = [], []
        for i in range(N + 1):
            a = math.radians(az[i % N])
            x, y = cx + math.sin(a) * RR, cy + math.cos(a) * RR
            if v.d(x, y) < 2.0:
                if cur: segs.append(cur); cur = []
                continue
            cur.append((v.p(x, G + hgt[i % N] * hs, y), v.p(x, G - 1.0, y)))
        if cur: segs.append(cur)
        for sg in segs:
            if len(sg) < 2: continue
            path = poly([a_ for (a_, b_) in sg] + [sg[-1][1], sg[0][1]])
            pen.fill(path, col_)
    if tod == 'night':
        pen.linear(rect(-800, v.h - 0.06 * v.S, 3500, 0.12 * v.S), 0, v.h - 0.06 * v.S, 0, v.h + 0.06 * v.S, [(0, '#3a2a2a', 0), (0.5, '#3a2a2a', 50), (1, '#3a2a2a', 0)])


def _ext_light_d(tod):
    if tod in ('sunrise', 'dawn'):
        return '#7a6a78', [Lamp(kind='dir', c='#ffc890', k=0.9, d=_norm3((-0.75, -0.25, 0.6)))]
    return '#2e3a62', [Lamp(kind='dir', c='#8a9ad8', k=0.35, d=_norm3((0.3, -0.8, 0.5)))]


def dr_house_ext(pen, v, tod='night', glow=None, porch_light=1.0, door_open=0.0):
    """Ruth's house from outside: a one-storey bungalow, pale blue-grey clapboard over a brick foundation, white trim,
    a hip roof of dark shingles, the picture window (living room) left of the porch, Ruth's bedroom window right, the red
    front door under a little gabled porch roof on two posts, three steps, the porch light. glow = {'living': k,
    'bedroom': k, 'hall': k} windows lit from inside."""
    glow = glow or {}
    G = D_GROUND
    x0, x1, y0, y1 = D_HOUSE
    sid = DP['siding'] if tod == 'night' else '#c8d0d6'
    walls = [('front', (x0, y0), (x1, y0)), ('west', (x0, y1), (x0, y0)), ('east', (x1, y0), (x1, y1)), ('back', (x1, y1), (x0, y1))]
    walls.sort(key=lambda w: -v.d((w[1][0] + w[2][0]) / 2, (w[1][1] + w[2][1]) / 2))
    wins = {'front': [(D_LWIN[0] - x0, D_LWIN[1] - x0, D_LWIN[2], D_LWIN[3], 'living'), (D_RWIN[0] - x0, D_RWIN[1] - x0, D_RWIN[2], D_RWIN[3], 'bedroom')],
            'west': [(y1 - D_SWIN[1], y1 - D_SWIN[0], D_SWIN[2], D_SWIN[3], 'living'), (y1 - 8.3, y1 - 7.3, 1.0, 2.0, 'kitchen')],
            'east': [(1.0, 2.2, 0.9, 2.0, 'bedroom'), (6.6, 7.6, 1.0, 2.0, 'kids')], 'back': []}
    for (nm, a, b) in walls:
        F = wall_face(a, b, G, D_EAVE)
        if not v.visible(F.O, F.n): continue
        holes = []
        for (u0, u1, sill, top, room) in wins[nm]:
            holes.append(rect(u0 * 100, (D_EAVE - top) * 100, (u1 - u0) * 100, (top - sill) * 100))
        if nm == 'front':
            holes.append(rect((D_FDOOR[0] - x0) * 100, (D_EAVE - D_FDOOR[2]) * 100, (D_FDOOR[1] - D_FDOOR[0]) * 100, D_FDOOR[2] * 100))

        def art(p_, W, H, nm=nm):
            pat(p_, W, H, 'clapboard', '#000000', 150)
            p_.texture(rect(0, 0, W, H), 'grunge', 0.3, 'overlay', 1.2)
            fh = (0.0 - G) * 100
            p_.fill(rect(0, H - fh, W, fh), DP['brick'])
            p_.cv.save(); p_.cv.translate(0, H - fh); pat(p_, W, fh, 'brick', '#c8b8a0', 200, 3, DP['brick']); p_.cv.restore()
            p_.fill(rect(0, 0, W, 10), DP['trim']); p_.fill(rect(0, H - fh - 4, W, 4), DP['trim'])
            for (u0, u1, sill, top, room) in wins[nm]:
                p_.fill(rect(u0 * 100 - 7, (D_EAVE - top) * 100 - 8, (u1 - u0) * 100 + 14, (top - sill) * 100 + 16), DP['trim'])
                for sx_ in ((u0 * 100 - 34, u1 * 100 + 8) if (u1 - u0) < 1.5 else ()):
                    sh = rect(sx_, (D_EAVE - top) * 100, 26, (top - sill) * 100)
                    p_.fill(sh, '#2e4a5a'); p_.line(sh, 0.8, '#000000', 160)
                    for k in range(int((top - sill) * 100 / 9)): p_.fill(rect(sx_ + 3, (D_EAVE - top) * 100 + 4 + k * 9, 20, 2.0), '#000000', 70)
            if nm == 'front':
                p_.fill(rect((D_FDOOR[0] - x0) * 100 - 9, (D_EAVE - D_FDOOR[2]) * 100 - 9, (D_FDOOR[1] - D_FDOOR[0]) * 100 + 18, D_FDOOR[2] * 100 + 9), DP['trim'])
                btext(p_, '27', (0.55 - x0) * 100, (D_EAVE - 1.75) * 100, 'serif_b', 13, '#2a2a2a', 230, 'center')
        draw_face(pen, v, F, art, sid, holes=holes, ao=False)
        for (u0, u1, sill, top, room) in wins[nm]:
            _ext_window(pen, v, a, b, u0, u1, sill, top, glow.get(room, 0.0), 'night' if tod == 'night' else 'dawn')
        if nm == 'front':
            Fd = Face((D_FDOOR[0], D_FDOOR[2], -0.02), (1, 0, 0), (0, -1, 0), (D_FDOOR[1] - D_FDOOR[0]) * 100, D_FDOOR[2] * 100, (0, 0, -1), 'front')
            if door_open <= 0.01:
                draw_face(pen, v, Fd, dr_front_door_art('out'), DP['door_red'], ao=False)
            else:
                q = v.poly3([(D_FDOOR[0], 0.0, 0.0), (D_FDOOR[1], 0.0, 0.0), (D_FDOOR[1], D_FDOOR[2], 0.0), (D_FDOOR[0], D_FDOOR[2], 0.0)])
                if not q.isEmpty():
                    pen.cv.save(); pen.cv.clipPath(q, skia.ClipOp.kIntersect, True)
                    pen.fill(q, '#3a2a20')
                    try:
                        with lighting('#5a483c', [Lamp(-0.4, D_CEIL - 0.1, 2.2, 4.2, '#ffd8a0', 1.7, (1.0, 0.6, 0.3), fall=1.4),
                                                  Lamp(-0.4, D_CEIL - 0.1, 6.8, 4.0, '#ffd8a0', 0.7, (1.0, 0.6, 0.3), fall=1.4)]):
                            H_ = DrHall(far=True)
                            H_.shell(pen, v, dict(hall=1.0))
                            for P_ in sorted(H_.pieces(dict()), key=lambda p_: -v.d(p_.ref[0], p_.ref[2])): P_.draw(pen, v)
                            Dd, _ = dr_front_door(dict(front_door=door_open))
                            Dd.draw(pen, v, door_open)
                    finally:
                        pen.cv.restore()
    _dr_hip_roof(pen, v, tod)


def _dr_hip_roof(pen, v, tod):
    x0, x1, y0, y1 = D_HOUSE
    ov = 0.4
    a0, a1, b0, b1 = x0 - ov, x1 + ov, y0 - ov, y1 + ov
    ym = (y0 + y1) / 2
    r0, r1 = x0 + (y1 - y0) / 2, x1 - (y1 - y0) / 2                       # the ridge ends (45 degree hips)
    E, R = D_EAVE - 0.05, D_RIDGE
    planes = [([(a0, E, b0), (a1, E, b0), (r1, R, ym), (r0, R, ym)], (0, 0, -1)), ([(a1, E, b1), (a0, E, b1), (r0, R, ym), (r1, R, ym)], (0, 0, 1)),
              ([(a0, E, b1), (a0, E, b0), (r0, R, ym)], (-1, 0, 0)), ([(a1, E, b0), (a1, E, b1), (r1, R, ym)], (1, 0, 0))]
    planes.sort(key=lambda p_: -v.d(sum(q[0] for q in p_[0]) / len(p_[0]), sum(q[2] for q in p_[0]) / len(p_[0])))
    for (q, nn) in planes:
        cen = (sum(p_[0] for p_ in q) / len(q), sum(p_[1] for p_ in q) / len(q), sum(p_[2] for p_ in q) / len(q))
        nrm = _norm3((nn[0] * (R - E), (y1 - y0) / 2, nn[2] * (R - E)))
        if not v.visible(cen, nrm): continue
        path = v.poly3(q)
        if path.isEmpty(): continue
        pen.fill(path, lit(DP['roof'], cen, nrm))
        b = _rb(path)
        pen.cv.save(); pen.cv.clipPath(path, skia.ClipOp.kIntersect, True)
        step = max(3.0, 0.16 * v.s(cen[0], cen[2]))
        yy = b[1]
        while yy < b[3]:
            pen.seg((b[0], yy), (b[2], yy), max(0.6, step * 0.08), '#000000', 70); yy += step
        pen.texture(path, 'grunge', 0.35, 'overlay', 1.0)
        if tod == 'night': pen.linear(path, 0, b[1], 0, b[3], [(0, '#8a9ad8', 40), (1, '#000000', 0)])
        pen.cv.restore()
        pen.line(path, 1.2)
    fa = v.poly3([(a0, E, b0), (a1, E, b0), (a1, E - 0.2, b0), (a0, E - 0.2, b0)])                       # the fascia board
    if not fa.isEmpty() and v.hy < b0: pen.fill(fa, lit(DP['trim'], (0, E, b0), (0, 0, -1))); pen.line(fa, 1.0)


def dr_porch(pen, v, tod='night', light=1.0):
    """The front porch: concrete deck and steps (three risers down to the walk), wrought-iron rails, two white posts and
    a little gable roof over the door, the doormat."""
    G = D_GROUND
    x0, x1, y0, y1 = D_PORCH
    for k in range(2):                                                      # two steps (three risers of 1/6 m) down to the walk
        ya, yb = y0 - 0.3 * (k + 1), y0 - 0.3 * k
        draw_box(pen, v, Box(-0.38, (ya + yb) / 2, 1.3, yb - ya, G, -(0.5 / 3) * (k + 1), 0),
                 {'all': '#8a8c8e', 'top': dict(fill='#a8aaa8', art=lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'asphalt', 0.4, 'overlay', 0.8))})
    deck = Box((x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0, G, 0.0, 0)
    draw_box(pen, v, deck, {'all': '#7e8082', 'top': dict(fill='#9a9c9a', art=lambda p_, W, H: (p_.texture(rect(0, 0, W, H), 'asphalt', 0.4, 'overlay', 0.8),
                                                                                              p_.fill(rect((-0.85 - x0) * 100, 10, 90, 55), '#6a3a2a'),
                                                                                              btext(p_, 'WELCOME', (-0.4 - x0) * 100, 42, 'serif_b', 9, '#c8a870', 200, 'center')))})
    for px in (x0 + 0.08, x1 - 0.08):
        draw_box(pen, v, Box(px, y0 + 0.08, 0.1, 0.1, 0.0, 2.45, 0), {'all': '#f2ece0'})
    for px in (-0.38 - 0.62, -0.38 + 0.62):                                 # iron hand rails down both sides of the steps
        if v.d(px, y0) < 0.3: continue
        a_, b_ = v.p(px, 0.85, y0 + 0.05), v.p(px, 0.85 + G, y0 - 0.6)
        pen.seg(a_, b_, max(1.5, 0.02 * v.s(px, y0)) + 1.5, LINE); pen.seg(a_, b_, max(1.2, 0.02 * v.s(px, y0)), '#1a1a1c')
        for k in range(4):
            u = k / 3
            yy = y0 + 0.05 - 0.65 * u
            fl = 0.0 if yy > y0 else -(0.5 / 3) * min(3, int((y0 - yy) / 0.3) + 1)
            pen.seg(v.p(px, 0.85 + G * u * 0.92, yy), v.p(px, fl, yy), max(1.0, 0.01 * v.s(px, yy)), '#1a1a1c')
    # the gabled porch roof
    E, R = 2.5, 3.15
    ya, yb = y0 - 0.15, 0.0
    for (q, nn) in (([(x0 - 0.1, E, ya), (-0.38, R, ya), (-0.38, R, yb), (x0 - 0.1, E, yb)], (-1, 1, 0)), ([(-0.38, R, ya), (x1 + 0.1, E, ya), (x1 + 0.1, E, yb), (-0.38, R, yb)], (1, 1, 0))):
        cen = (sum(p_[0] for p_ in q) / 4, sum(p_[1] for p_ in q) / 4, sum(p_[2] for p_ in q) / 4)
        nrm = _norm3((nn[0] * (R - E), (x1 - x0) / 2, 0))
        path = v.poly3(q)
        if not path.isEmpty():
            pen.fill(path, lit(DP['roof'], cen, nrm)); pen.line(path, 1.0)
    tri = v.poly3([(x0 - 0.1, E, ya), (-0.38, R, ya), (x1 + 0.1, E, ya)])
    if not tri.isEmpty() and v.hy < ya:
        pen.fill(tri, lit(DP['trim'], (-0.38, 2.7, ya), (0, 0, -1))); pen.line(tri, 1.0)
        und = v.poly3([(x0 - 0.1, E, ya), (x1 + 0.1, E, ya), (x1 + 0.1, E - 0.12, ya), (x0 - 0.1, E - 0.12, ya)])
        pen.fill(und, lit(DP['trim'], (-0.38, 2.45, ya), (0, 0, -1))); pen.line(und, 0.8)


def dr_porch_light_draw(pen, v, k=1.0):
    porch_lantern(pen, v, D_PLIGHT, k, facing=(0, 0, -1))


def dr_ground_front(pen, v, tod='night'):
    """Lawns, the front walk, the driveway (wet concrete), the sidewalk, Larch Street (wet asphalt with the streetlights
    and Halverson's headlights shining in it), the far sidewalk, lawns across."""
    G = D_GROUND
    wet = tod == 'night'
    grass = '#1c2a26' if wet else '#4a6a3a'
    F = floor_face(-130.0, 130.0, -130.0, 9.5, G)

    def lawn(p_, W, H):
        p_.linear(rect(0, 0, W, H), 0, 0, 0, H, [(0, grass, 255), (1, _darken(grass, 0.3), 255)])
        p_.texture(rect(0, 0, W, H), 'grunge', 0.6, 'overlay', 5.0)
        p_.texture(rect(0, 0, W, H), 'fabric', 0.4, 'overlay', 0.8)
    draw_face(pen, v, F, lawn, grass, ao=False, line=False)

    def strip(x0, x1, y0, y1, c, kind='asphalt', Y=G + 0.004, ink=None, refl=()):
        Fs = floor_face(x0, x1, y0, y1, Y)

        def art(p_, W, H):
            p_.texture(rect(0, 0, W, H), kind, 0.6, 'overlay', 1.6 if kind == 'asphalt' else 0.8)
            if ink: ink(p_, W, H)
            if wet:
                for (rx, ry, rc, ra) in refl:                                      # streaks of reflected light on the wet surface
                    u_, w_ = floor_uv(x0, y1, rx, ry)
                    p_.linear(rect(u_ - 40, w_ - 600, 80, 700), u_ - 40, 0, u_ + 40, 0, [(0, rc, 0), (0.5, rc, ra), (1, rc, 0)])
        draw_face(pen, v, Fs, art, c, ao=False, line=False)
    # the street, kerbs, sidewalks
    refl = [(lx, ly - 2.5, '#ffb060', 70) for (lx, ly) in D_LAMPS] + [(D_BUS_LAMP[0], D_BUS_LAMP[1] + 1.5, '#c8f0a0', 50)]

    def street_ink(p_, W, H):
        x0 = -90.0
        for k in range(36):                                                       # the yellow centre line, dashed
            u_ = (k * 5.0) * 100
            p_.fill(rect(u_, (D_STREET[0] - (D_STREET[0] + D_STREET[1]) / 2) * -100 + 0, 300, 9), '#c8a83a', 120)
        p_.fill(rect(0, 0, W, 6), '#5a5a5a', 120); p_.fill(rect(0, H - 6, W, 6), '#5a5a5a', 120)
    strip(-90.0, 90.0, D_STREET[1], D_STREET[0], '#26282e' if wet else '#4a4c50', 'asphalt', G - 0.12, street_ink, refl)
    strip(-90.0, 90.0, D_STREET[0], D_STREET[0] + 1.25, '#5a5c60' if wet else '#a8a8a0', 'asphalt', G + 0.002,
          lambda p_, W, H: [p_.fill(rect(k * 150, 0, 1.2, H), '#000000', 90) for k in range(int(W / 150))])
    strip(-90.0, 90.0, D_STREET[1] - 1.4, D_STREET[1], '#5a5c60' if wet else '#a8a8a0', 'asphalt', G + 0.002,
          lambda p_, W, H: [p_.fill(rect(k * 150, 0, 1.2, H), '#000000', 90) for k in range(int(W / 150))])
    # the driveway (concrete, a puddle catching the headlights) and the front walk
    dx0, dx1, dy0, dy1 = D_DRIVE

    def drive_ink(p_, W, H):
        p_.fill(rect(0, H * 0.5, W, 1.2), '#000000', 90)
        if wet:
            u_, w_ = floor_uv(dx0, dy1, -6.6, -1.6)
            p_.fill(_blob(u_, w_, 70, 30, 11, 5, 0.3), '#8a96b8', 60)
    strip(dx0, dx1, dy0, dy1, '#5e6064' if wet else '#a8a49a', 'asphalt', G + 0.006, drive_ink)
    strip(-0.75, 0.0, D_STREET[0] + 1.25, D_PORCH[2] - 0.9, '#5e6064' if wet else '#a8a49a', 'asphalt', G + 0.006,
          lambda p_, W, H: [p_.fill(rect(0, k * 90, W, 1.0), '#000000', 90) for k in range(int(H / 90))])
    # the opposite kerb lawns
    if wet:
        pass


def dr_streetlight(pen, v, x, y, k=1.0, c=D_SODIUM, arm=1.0, h=6.2, cone=True, G=D_GROUND):
    """A streetlight: a grey pole, a curved arm reaching over the street, the cobra-head lamp; k = brightness (cone and
    pool are drawn by dr_streetlight_glow)."""
    if v.d(x, y) < 0.5: return
    s = v.s(x, y)
    b_, t_ = v.p(x, G, y), v.p(x, G + h, y)
    pc = lit('#6e7078', (x, G + 3.0, y), None)
    pen.seg(b_, t_, max(1.5, 0.16 * s) + 2, LINE); pen.seg(b_, t_, max(1.2, 0.16 * s), pc)
    pen.seg((b_[0] - 0.04 * s, b_[1]), (t_[0] - 0.04 * s, t_[1]), max(0.6, 0.03 * s), '#ffffff', 26)
    ex, ey = x, y - 1.6 * arm
    pts = [t_, v.p(x, G + h + 0.35, y - 0.5 * arm), v.p(ex, G + h + 0.25, ey)]
    pen.line(smooth(pts, False, 0.9), max(1.2, 0.1 * s) + 2, LINE); pen.line(smooth(pts, False, 0.9), max(1.0, 0.1 * s), pc)
    hx, hy = v.p(ex, G + h + 0.18, ey); hs = v.s(ex, ey)
    head = rrect(hx - 0.32 * hs, hy - 0.08 * hs, 0.64 * hs, 0.16 * hs, 0.06 * hs)
    pen.fill(head, '#3a3c40'); pen.line(head, 1.0)
    pen.fill(oval(hx, hy + 0.06 * hs, 0.24 * hs, 0.05 * hs), mix('#3a3a3a', '#fff0d0', k))


def dr_streetlight_glow(pen, v, x, y, k=1.0, c=D_SODIUM, arm=1.0, h=6.2, G=D_GROUND, rain=True, t=0.0):
    """The lamp's glow, its cone through the rain and the pool on the ground (emissive; drawn live)."""
    if k <= 0.01 or v.d(x, y) < 0.5: return
    ex, ey = x, y - 1.6 * arm
    hx, hy = v.p(ex, G + h + 0.12, ey); hs = v.s(ex, ey)
    pen.glow(hx, hy, 1.4 * hs, c, 110 * k)
    pen.glow(hx, hy, 0.35 * hs, '#fff6e0', 220 * k)
    gx, gy = v.p(ex, G, ey)
    pen.ellipse_glow(gx, gy, 3.4 * hs, max(4.0, 0.9 * hs * clamp(abs(v.h - gy) / max(1.0, 3.4 * hs), 0.12, 1.0)), c, 85 * k)
    # a soft column of light under the head (the rain makes the beam visible), no hard edges
    cw = 1.2 * hs
    pen.linear(rect(hx - cw, hy, 2 * cw, max(1.0, gy - hy)), hx - cw, 0, hx + cw, 0, [(0, c, 0), (0.5, c, 26 * k), (1, c, 0)])
    if rain:
        cv = pen.cv
        clip = oval(hx, (hy + gy) / 2, 1.3 * hs, max(4.0, (gy - hy) * 0.55))
        cv.save(); cv.clipPath(clip, skia.ClipOp.kIntersect, True)
        dr_rain(pen, t, (hx - 1.4 * hs, hy, hx + 1.4 * hs, gy), k, abs(int(x * 7)) % 97, 1.2, 0.1, mix(c, '#ffffff', 0.4), 60, max(24, int(hs * 1.2)),
                L=clamp(hs * 0.55, 5.0, 60.0), w=clamp(hs * 0.016, 0.7, 1.6))
        cv.restore()


def dr_bus_stop(pen, v, G=D_GROUND):
    """The bus stop at the west end of Larch Street (south side, facing the street +y): a slatted bench on two concrete
    legs, the BUS STOP sign on its pole, a bin."""
    x, y = D_BUS
    if v.d(x, y) < 0.5: return
    B = Box(x, y, 1.8, 0.5, G, G + 0.45, 180)
    for u in (-0.7, 0.7):
        draw_box(pen, v, sub(B, u - 0.06, u + 0.06, -0.2, 0.2, G, G + 0.42), {'all': '#8a8a86'})
    for k in range(4):
        n = -0.2 + k * 0.13
        draw_box(pen, v, sub(B, -0.9, 0.9, n - 0.05, n + 0.05, G + 0.42, G + 0.46), {'all': '#7a7462', 'top': '#9a947e'})
    for k in range(3):                                                      # the backrest slats
        Yb = G + 0.62 + k * 0.13
        draw_box(pen, v, sub(B, -0.9, 0.9, -0.26, -0.21, Yb, Yb + 0.09), {'all': '#8a846e'})
    for u in (-0.7, 0.7):                                                   # the backrest posts
        draw_box(pen, v, sub(B, u - 0.04, u + 0.04, -0.27, -0.2, G + 0.42, G + 1.0), {'all': '#6a6a66'})
    sx, sy = x + 1.3, y - 0.1
    if v.d(sx, sy) > 0.5:
        s = v.s(sx, sy)
        a_, b_ = v.p(sx, G, sy), v.p(sx, G + 2.6, sy)
        pen.seg(a_, b_, max(1.2, 0.05 * s) + 1.5, LINE); pen.seg(a_, b_, max(1.0, 0.05 * s), lit('#8a8c90', (sx, G + 1.5, sy), None))
        px, py = v.p(sx, G + 2.35, sy)
        sg = rrect(px - 0.24 * s, py - 0.2 * s, 0.48 * s, 0.4 * s, 0.03 * s)
        pen.fill(sg, lit('#e8e4d8', (sx, G + 2.35, sy), (0, 0, 1))); pen.line(sg, 1.0)
        pen.fill(rect(px - 0.2 * s, py - 0.16 * s, 0.4 * s, 0.12 * s), lit('#1a5a8a', (sx, G + 2.35, sy), (0, 0, 1)))
        btext(pen, 'BUS', px, py - 0.06 * s, 'sans_b', 0.09 * s, '#ffffff', 240, 'center')
        btext(pen, 'STOP', px, py + 0.1 * s, 'sans_b', 0.1 * s, '#1a1a1a', 240, 'center')
        btext(pen, '14', px, py + 0.18 * s, 'sans_b', 0.06 * s, '#c82a2a', 240, 'center')
    bx_, by_ = x - 1.25, y - 0.05
    if v.d(bx_, by_) > 0.5:
        draw_box(pen, v, Box(bx_, by_, 0.42, 0.42, G, G + 0.8, 180), {'all': '#3a5a3a', 'top': '#1a2a1a'})


def dr_neighbour(pen, v, x0, x1, yf=0.0, depth=9.0, tod='night', lit_room=None, seed=0, G=D_GROUND, c='#9a9488'):
    """A neighbour's one-storey house (front at yf, facing -y; or across the street facing +y when yf < -20)."""
    facing_n = yf < -20
    y0, y1 = (yf - depth, yf) if facing_n else (yf, yf + depth)
    sid = mix(c, '#2a2e40', 0.35) if tod == 'night' else c
    front = (x1, y1) if facing_n else (x0, y0)
    walls = [((x1, y1), (x0, y1)) if facing_n else ((x0, y0), (x1, y0)), ((x0, y0), (x0, y1)) if facing_n else ((x0, y1), (x0, y0)),
             ((x1, y1), (x1, y0)) if facing_n else ((x1, y0), (x1, y1))]
    for (a, b) in walls:
        F = wall_face(a, b, G, 2.8)
        if not v.visible(F.O, F.n): continue
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        rng = np.random.default_rng(abs(int(seed)))
        wins = []
        for k in range(int(L / 3.2)):
            u = 1.0 + k * 3.2 + rng.uniform(0, 0.5)
            if u + 1.1 < L - 0.4: wins.append((u, u + 1.1))

        def art(p_, W, H, wins=wins):
            pat(p_, W, H, 'clapboard', '#000000', 140)
            p_.texture(rect(0, 0, W, H), 'grunge', 0.3, 'overlay', 1.2)
            for (u0, u1) in wins:
                p_.fill(rect(u0 * 100 - 6, H - 215, (u1 - u0) * 100 + 12, 125), '#e8e4d8', 200)
        draw_face(pen, v, F, art, sid, ao=False)
        for i, (u0, u1) in enumerate(wins):
            k = 1.0 if (lit_room is not None and i == lit_room and a == walls[0][0]) else 0.0
            _ext_window(pen, v, a, b, u0, u1, 0.95, 2.05, k, 'night' if tod == 'night' else 'dawn')
    yr = (y0 + y1) / 2
    q = [(x0 - 0.3, 2.8, y0 - 0.3), (x1 + 0.3, 2.8, y0 - 0.3), ((x0 + x1) / 2, 4.6, yr), ]
    for (qq, nn) in (([(x0 - 0.3, 2.75, y0 - 0.3), (x1 + 0.3, 2.75, y0 - 0.3), (x1 + 0.3, 4.6, yr), (x0 - 0.3, 4.6, yr)], (0, 1, -1)),
                     ([(x1 + 0.3, 2.75, y1 + 0.3), (x0 - 0.3, 2.75, y1 + 0.3), (x0 - 0.3, 4.6, yr), (x1 + 0.3, 4.6, yr)], (0, 1, 1))):
        cen = (sum(p_[0] for p_ in qq) / 4, sum(p_[1] for p_ in qq) / 4, sum(p_[2] for p_ in qq) / 4)
        if not v.visible(cen, _norm3(nn)): continue
        path = v.poly3(qq)
        if not path.isEmpty(): pen.fill(path, lit('#3a3a40', cen, _norm3(nn))); pen.line(path, 1.0)


def dr_mailbox(pen, v, x=-1.5, y=-11.4, G=D_GROUND):
    if v.d(x, y) < 0.4: return
    s = v.s(x, y)
    a_, b_ = v.p(x, G, y), v.p(x, G + 1.0, y)
    pen.seg(a_, b_, max(1.2, 0.08 * s) + 1.5, LINE); pen.seg(a_, b_, max(1.0, 0.08 * s), '#5a4a3a')
    B = Box(x, y, 0.2, 0.45, G + 1.0, G + 1.22, 90)
    draw_box(pen, v, B, {'all': '#2a3a5a', 'top': '#3a4a6a'})


# ---------------------------------------------------------------------------------------------- Doctor Halverson's car
def _car_profile(L, H, hood, belt):
    """The car's side silhouette below the beltline (cm, x from the rear bumper, y down from the beltline...): returns
    (lower body pts, greenhouse pts) in a frame with x along the car (0 = rear) and y down from the roof (cm)."""
    l, h, hd, bt = L * 100, H * 100, hood * 100, belt * 100
    ground = h - 4
    lower = [(0, h - bt + 6), (6, h - bt), (l * 0.18, h - bt - 2), (l * 0.76, h - bt - 2), (l * 0.86, h - hd), (l - 8, h - hd + 4), (l, h - hd + 16),
             (l, ground - 22), (l - 6, ground - 10), (l - 8, ground - 10), (0, ground - 12), (0, h - bt + 6)]
    # greenhouse: rear window slope, roof, windshield
    gh = [(l * 0.06, h - bt + 1), (l * 0.2, 4), (l * 0.56, 0), (l * 0.76, h - bt - 4)]
    return lower, gh


class _DPart(Part):
    """A Part whose sort depth is a function of the view (dfn(v) -> depth): car glass sorts by its nearest corner, the
    interior always behind the near glass, the roof always over the interior."""

    def __init__(self, dfn, **kw):
        Part.__init__(self, **kw)
        self.dfn = dfn

    def depth(self, v): return self.dfn(v)


def _hull2(pts):
    """Convex hull of 2D points (monotone chain)."""
    P = sorted(set((round(p_[0], 2), round(p_[1], 2)) for p_ in pts))
    if len(P) < 3: return P

    def cr(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p_ in P:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p_) <= 0: lo.pop()
        lo.append(p_)
    for p_ in reversed(P):
        while len(up) >= 2 and cr(up[-2], up[-1], p_) <= 0: up.pop()
        up.append(p_)
    return lo[:-1] + up[:-1]


def _seg3(pen, v, a, b, w, c, alpha=255, outline=True):
    """A 3D segment (x, Y, y) -> (x, Y, y) drawn with a screen width w, clipped at the near plane."""
    da, db = v.d3(*a), v.d3(*b); nr = v.near + 0.02
    if da < nr and db < nr: return
    if da < nr:
        t_ = (nr - da) / (db - da); a = tuple(a[i] + (b[i] - a[i]) * t_ for i in range(3))
    elif db < nr:
        t_ = (nr - db) / (da - db); b = tuple(b[i] + (a[i] - b[i]) * t_ for i in range(3))
    pa, pb = v.p(*a), v.p(*b)
    if outline: pen.seg(pa, pb, w + 2.0, LINE, alpha)
    pen.seg(pa, pb, w, c, alpha)


def dr_car_parts(cx=None, cy=None, fa=D_CAR_FA, col_='#4a6e80', lights=True, Y0=D_GROUND, glass_k=0.62, interior=True, plate='KID DOC'):
    """Halverson's car (a small dark-teal hatchback, ten years old, a hospital parking permit on the glass) as furniture
    Parts on the plan: the lower body (an extruded side profile with round wheel arches), the nose and tail (grille,
    headlamps, bumpers, the plate), four wheels with tread width and alloy rims, the cabin (roof, windshield with wipers,
    rear glass, both side windows as separate glass parts with their pillars, so a seated figure sorts between the far and
    the near window), door mirrors, the seats with headrests, the dash and the wheel. Returns (parts, seats {name: (x,
    y)}, Box). fa 180 = facing +y."""
    cx = D_CAR[0] if cx is None else cx; cy = D_CAR[1] if cy is None else cy
    L, W, H = DCAR['L'], DCAR['W'], DCAR['H']
    B = Box(cx, cy, L, W, Y0, Y0 + H, fa - 90)       # Box 'u' runs along the car (rear -> front), 'n' across (+n = the car's right side)
    P = []
    belt = Y0 + DCAR['belt']
    hood = Y0 + DCAR['hood']
    u_r, u_f = -L / 2, L / 2
    U3 = (B.U[0], 0.0, B.U[1]); N3 = (B.N[0], 0.0, B.N[1]); DN = (0.0, -1.0, 0.0)
    l = L * 100.0
    gnd = (belt + 0.2 - Y0) * 100.0                  # the profile's y of the ground (y runs down from belt + 0.2)
    bot = gnd - 17.0                                 # the sills: 17 cm clear of the road
    hd = (belt - hood) * 100.0 + 20.0

    def arch(xc, r=35.0, n=9):
        cy_ = gnd - 31.0
        b0 = math.asin(clamp((bot - cy_) / r, -1.0, 1.0))
        return [(xc + r * math.cos(a), cy_ + r * math.sin(a)) for a in np.linspace(b0, -math.pi - b0, n)]

    WHEELS = ((u_r + 0.82, 1), (u_r + 0.82, -1), (u_f - 0.88, 1), (u_f - 0.88, -1))

    def wheel_vis(v, uw, side):
        return v.visible(B.at(uw, side * (W / 2 + 0.015), Y0 + 0.31), (B.N[0] * side, 0.0, B.N[1] * side))

    def draw_wheel(pen, v, uw, side):
        r_t, r_r = 0.31, 0.2
        Yc = Y0 + r_t

        def ring(r, nn, n=22):
            pts = [B.at(uw + math.cos(2 * math.pi * k / n) * r, side * nn, Yc + math.sin(2 * math.pi * k / n) * r) for k in range(n)]
            q = _clip_near3(v, pts)
            return [v.p(*p_) for p_ in q] if len(q) >= 3 else None
        outer = ring(r_t, W / 2 + 0.015); inner = ring(r_t, W / 2 - 0.2)
        if outer is None: return
        if inner is not None:                                           # the tyre's tread width (the hull of its two faces)
            hull = _hull2(outer + inner)
            if len(hull) >= 3:
                hp = poly(hull); pen.fill(hp, '#0c0c0e'); pen.line(hp, 1.0)
        n = (B.N[0] * side, 0.0, B.N[1] * side)
        c = B.at(uw, side * (W / 2 + 0.015), Yc)
        if not v.visible(c, n): return
        tp = poly(outer); pen.fill(tp, '#17171a'); pen.line(tp, 1.0)
        s = v.s(c[0], c[2])
        rim = ring(r_r, W / 2 + 0.02)
        if rim:
            rp = poly(rim); pen.fill(rp, lit('#aeb2ba', c, n)); pen.line(rp, 0.8)
            cx_, cy_ = v.p(*c)
            for k in range(5):
                a = 2 * math.pi * k / 5 + 0.3
                e = B.at(uw + math.cos(a) * r_r * 0.94, side * (W / 2 + 0.02), Yc + math.sin(a) * r_r * 0.94)
                if v.d3(*e) > v.near: pen.seg((cx_, cy_), v.p(*e), max(1.0, 0.045 * s), lit('#5e626a', c, n))
            hub = ring(0.055, W / 2 + 0.025, 10)
            if hub: pen.fill(poly(hub), lit('#32343a', c, n)); pen.line(poly(hub), 0.5)

    def body(pen, v):
        for (uw, side) in WHEELS:
            if not wheel_vis(v, uw, side): draw_wheel(pen, v, uw, side)
        prof = [(0, 34), (3, 24), (10, 20), (l * 0.74, 20), (l * 0.8, 22), (l * 0.9, hd + 2), (l - 10, hd + 6), (l - 2, hd + 14), (l, hd + 24),
                (l, bot - 16), (l - 4, bot - 4), (l - 10, bot)] + arch(l - 88.0) + arch(82.0) + [(8, bot), (2, bot - 6), (0, bot - 18)]
        O = B.at(u_r, W / 2 - 0.02, belt + 0.2)

        def side_art(p_, Wc, Hc):
            p_.linear(rect(0, 0, Wc, Hc), 0, 0, 0, Hc, [(0, '#ffffff', 60), (0.3, '#ffffff', 0), (0.55, '#000000', 0), (1, '#000000', 80)])
            p_.fill(rect(0, 40, Wc, 1.4), '#000000', 70)                                   # the swage line
            p_.fill(rect(0, 41.4, Wc, 1.0), '#ffffff', 40)
            for sx_ in (Wc * 0.36, Wc * 0.565, Wc * 0.745):                                # door seams
                p_.seg((sx_, 23), (sx_, bot - 3), 0.9, '#000000', 150)
            for hx_ in (Wc * 0.395, Wc * 0.6): p_.fill(rrect(hx_, 33, 11, 2.6, 1.2), '#c8ccd0'); p_.line(rrect(hx_, 33, 11, 2.6, 1.2), 0.4, '#000000', 150)
            p_.fill(rect(10, bot - 7, Wc - 20, 7), '#000000', 90)                          # the dark sill
            p_.fill(oval(Wc * 0.88, 30, 2.4, 1.6), '#ffb040')                              # the side repeater
            p_.fill(rrect(Wc * 0.2, 27, 9, 6, 2), '#000000', 110)                          # the fuel flap
        extrude(pen, v, O, U3, DN, prof, _scale3(N3, -(W - 0.04)), col_, _darken(col_, 0.15), side_art)
        for side in (1, -1):                                               # wet sheen along the shoulder line (streetlight / sky)
            n = (B.N[0] * side, 0.0, B.N[1] * side)
            if not v.visible(B.at(0, side * W / 2, belt), n): continue
            pts = [v.p(*B.at(u_r + 0.1 + (L - 0.2) * k / 10, side * (W / 2 - 0.01), belt + 0.17 - (0.0 if k < 8 else (k - 7) * 0.08))) for k in range(11)]
            pen.line(smooth(pts, False, 0.8), max(1.0, 0.012 * v.s(B.cx, B.cy)), '#b8c8e8', 110)
        hpts = [v.p(*B.at(u_f - 1.0 + 0.95 * k / 6, 0.0, hood + 0.02 + 0.01 * k)) for k in range(7)]
        pen.line(smooth(hpts, False, 0.8), max(1.0, 0.01 * v.s(B.cx, B.cy)), '#a8b8d8', 90)
        # the nose and the tail (art on the vertical end faces of the extrusion)
        hwf = W / 2 - 0.03

        def nose(p_, Wc, Hc):
            p_.fill(rect(0, 0, Wc, Hc), col_)
            p_.linear(rect(0, 0, Wc, Hc), 0, 0, 0, Hc, [(0, '#ffffff', 40), (0.4, '#000000', 0), (1, '#000000', 70)])
            gr = rrect(50, 3, Wc - 100, 11, 3)
            p_.fill(gr, '#101216'); p_.line(gr, 0.6, '#000000', 200)
            for k in range(3): p_.fill(rect(53, 5.4 + k * 3.0, Wc - 106, 0.8), '#3a3e46')
            p_.fill(oval(Wc / 2, 8.5, 3.6, 3.0), '#c8ccd2'); p_.line(oval(Wc / 2, 8.5, 3.6, 3.0), 0.4, '#000000', 180)
            for x_ in (5, Wc - 47):
                bz = rrect(x_ - 1.5, 1.5, 45, 15, 5)
                p_.fill(bz, '#8e949c'); p_.line(bz, 0.6, '#000000', 200)
                lm = rrect(x_ + 1, 3.5, 40, 11, 4)
                p_.fill(lm, '#fff6e0' if lights else '#c8ccd0'); p_.line(lm, 0.5, '#000000', 160)
                p_.fill(oval(x_ + (12 if x_ < 20 else 30), 9, 5.5, 4.4), '#ffffff' if lights else '#e2e4e8')
                p_.fill(oval(x_ + (33 if x_ < 20 else 9), 9.4, 3.2, 3.0), '#ffc060' if lights else '#d8a850', 230)   # the indicator
            bm = rect(0, 19, Wc, 14)
            p_.fill(bm, '#22252a'); p_.linear(bm, 0, 19, 0, 33, [(0, '#ffffff', 36), (0.3, '#ffffff', 0), (1, '#000000', 60)])
            p_.fill(rrect(36, 34.5, Wc - 72, 4.6, 2), '#0c0d10')
            pl = rrect(Wc / 2 - 26, 20.2, 52, 11.6, 1.6)
            p_.fill(pl, '#f2f0e6'); p_.line(pl, 0.5, '#000000', 200)
            btext(p_, plate, Wc / 2, 29.2, 'sans_b', 8.6, '#1c2a5a', 240, 'center', spacing=0.06)

        def tail(p_, Wc, Hc):
            p_.fill(rect(0, 0, Wc, Hc), col_)
            p_.linear(rect(0, 0, Wc, Hc), 0, 0, 0, Hc, [(0, '#ffffff', 36), (0.4, '#000000', 0), (1, '#000000', 70)])
            for x_ in (3, Wc - 21):
                tl = rrect(x_, 2, 18, 24, 4)
                p_.fill(tl, '#ff3a2a' if lights else '#8a2a2a'); p_.line(tl, 0.5, '#000000', 200)
                p_.fill(rrect(x_ + 3, 17, 12, 6, 2), '#ffe8d8' if lights else '#b8a8a0', 200)
            p_.seg((24, 3), (Wc - 24, 3), 0.9, '#000000', 150)                               # the hatch shut line
            p_.fill(rrect(Wc / 2 - 9, 6, 18, 3.4, 1.5), '#c8ccd0')
            pl = rrect(Wc / 2 - 26, 13, 52, 11.6, 1.6)
            p_.fill(pl, '#f2f0e6'); p_.line(pl, 0.5, '#000000', 200)
            btext(p_, plate, Wc / 2, 22, 'sans_b', 8.6, '#1c2a5a', 240, 'center', spacing=0.06)
            bm = rect(0, 31, Wc, 15)
            p_.fill(bm, '#22252a'); p_.linear(bm, 0, 31, 0, 46, [(0, '#ffffff', 36), (0.3, '#ffffff', 0), (1, '#000000', 60)])
            for x_ in (10, Wc - 22): p_.fill(rrect(x_, 35, 12, 4, 1.5), '#c82a22', 200)       # reflectors
        Fn = Face(B.at(u_f + 0.006, hwf, Y0 + 0.7), _scale3(N3, -1), DN, 2 * hwf * 100, 40.0, U3, 'front')
        if v.visible(Fn.O, U3): draw_face(pen, v, Fn, nose, col_, ao=False, lw=1.0)
        Ft = Face(B.at(u_r - 0.006, -hwf, Y0 + 0.84), N3, DN, 2 * hwf * 100, 49.0, _scale3(U3, -1), 'back')
        if v.visible(Ft.O, _scale3(U3, -1)): draw_face(pen, v, Ft, tail, col_, ao=False, lw=1.0)
    P.append(Part(fn=body, ref=B.at(0, 0, Y0 + 0.5), tag='body'))
    for (uw, side) in WHEELS:
        def wheel(pen, v, uw=uw, side=side):
            if wheel_vis(v, uw, side): draw_wheel(pen, v, uw, side)
        P.append(_DPart((lambda uw_, side_: lambda v: min(v.d(B.cx, B.cy), v.d(*B.at(uw_, side_ * (W / 2 + 0.2), 0)[0::2])) - 0.05)(uw, side),
                        fn=wheel, ref=B.at(uw, side * (W / 2 + 0.2), Y0 + 0.3), tag='wheel'))
    # the cabin: roof + glass (each its own part)
    gh = [(u_r + 0.12, belt), (u_r + 0.62, Y0 + H - 0.02), (u_f - 1.95, Y0 + H), (u_f - 1.02, belt + 0.02)]
    hw = W / 2 - 0.1

    def quad(pts, mat, glass=False, extra=None):
        def fn(pen, v):
            path = v.poly3(pts)
            if path.isEmpty(): return
            cen = (sum(p_[0] for p_ in pts) / 4, sum(p_[1] for p_ in pts) / 4, sum(p_[2] for p_ in pts) / 4)
            if glass:
                pen.fill(path, '#0a0e14', int(255 * glass_k))
                b = _rb(path)
                pen.linear(path, b[0], b[1], b[2], b[3], [(0, '#9ab0d8', 0), (0.35, '#9ab0d8', 55), (0.42, '#9ab0d8', 10), (0.6, '#9ab0d8', 0), (0.7, '#9ab0d8', 30), (1, '#9ab0d8', 0)])
                pen.line(path, 1.4, '#0a0c10', 230)
            else:
                pen.fill(path, lit(mat, cen, (0, 1, 0)))
                b = _rb(path)
                pen.linear(path, b[0], b[1], b[2], b[3], [(0, '#b8c8e8', 0), (0.4, '#b8c8e8', 46), (0.55, '#b8c8e8', 0)])
                pen.line(path, 1.0)
            if extra: extra(pen, v)
        return fn
    roof = [B.at(gh[1][0], hw, gh[1][1]), B.at(gh[2][0], hw, gh[2][1]), B.at(gh[2][0], -hw, gh[2][1]), B.at(gh[1][0], -hw, gh[1][1])]
    nearest = lambda pts: (lambda v: min(v.d(q[0], q[2]) for q in pts))
    P.append(_DPart(lambda v: v.d(B.cx, B.cy) - 0.3, fn=quad(roof, col_), ref=B.at((gh[1][0] + gh[2][0]) / 2, 0, Y0 + H), tag='roof'))
    wind = [B.at(gh[2][0], hw, gh[2][1]), B.at(gh[3][0], hw + 0.08, gh[3][1]), B.at(gh[3][0], -hw - 0.08, gh[3][1]), B.at(gh[2][0], -hw, gh[2][1])]

    def wipers(pen, v):
        s = v.s(B.cx, B.cy)
        if not v.visible(B.at(gh[3][0], 0, belt + 0.2), _norm3((U3[0], 0.9, U3[2]))): return
        for (n0, n1) in ((-0.62, -0.1), (0.02, 0.56)):
            a_ = B.at(gh[3][0] - 0.03, n0, gh[3][1] + 0.025); b_ = B.at(gh[3][0] - 0.16, n1, gh[3][1] + 0.115)
            _seg3(pen, v, a_, b_, max(1.0, 0.014 * s), '#0c0d10', 255, False)
        # the hospital parking permit low in the corner of the glass
        pq = v.poly3([B.at(gh[3][0] - 0.05, 0.56, gh[3][1] + 0.04), B.at(gh[3][0] - 0.05, 0.7, gh[3][1] + 0.04), B.at(gh[3][0] - 0.15, 0.69, gh[3][1] + 0.105),
                      B.at(gh[3][0] - 0.15, 0.55, gh[3][1] + 0.105)])
        if not pq.isEmpty() and False: pen.fill(pq, '#8aa0b8', 130)
    P.append(_DPart(nearest(wind), fn=quad(wind, None, True, wipers), ref=B.at((gh[2][0] + gh[3][0]) / 2, 0, belt + 0.25), tag='windshield'))
    rear = [B.at(gh[0][0], hw + 0.08, gh[0][1]), B.at(gh[1][0], hw, gh[1][1]), B.at(gh[1][0], -hw, gh[1][1]), B.at(gh[0][0], -hw - 0.08, gh[0][1])]
    P.append(_DPart(nearest(rear), fn=quad(rear, None, True), ref=B.at((gh[0][0] + gh[1][0]) / 2, 0, belt + 0.25), tag='rear_glass'))
    for side in (1, -1):
        sw = [B.at(gh[0][0] + 0.06, side * (hw + 0.07), belt + 0.02), B.at(gh[1][0], side * hw, gh[1][1] - 0.03), B.at(gh[2][0], side * hw, gh[2][1] - 0.03),
              B.at(gh[3][0] - 0.04, side * (hw + 0.07), belt + 0.03)]

        def sidewin(pen, v, sw=sw, side=side):
            path = v.poly3(sw)
            if path.isEmpty(): return
            pen.fill(path, '#0e141c', int(255 * glass_k))
            b = _rb(path)
            pen.linear(path, b[0], b[1], b[2], b[3], [(0, '#9ab0d8', 0), (0.3, '#9ab0d8', 40), (0.36, '#9ab0d8', 0), (1, '#9ab0d8', 0)])
            pen.line(path, 1.2, '#0a0c10', 230)
            # the pillars and the roof rail round this side's glass (body colour), and the door mirror
            s = v.s(B.cx, B.cy)
            nrm = (B.N[0] * side, 0.3, B.N[1] * side)
            pc = _darken(lit(col_, B.at(0.0, side * hw, belt + 0.3), _norm3(nrm)), 0.3)
            wpx = max(2.0, 0.06 * s)
            pb0, pb1 = B.at(u_f - 2.15, side * (hw + 0.06), belt + 0.02), B.at(u_f - 2.15, side * hw, Y0 + H - 0.03)
            _seg3(pen, v, pb0, pb1, max(2.0, 0.075 * s), _darken(col_, 0.45), 255, False)          # the B pillar (black-out)
            _seg3(pen, v, sw[3], sw[2], wpx, pc)                                                   # the A pillar
            _seg3(pen, v, sw[0], sw[1], wpx * 1.5, pc)                                             # the C pillar
            _seg3(pen, v, sw[1], sw[2], wpx * 0.8, pc)                                             # the roof rail
            _seg3(pen, v, sw[0], sw[3], max(1.5, 0.03 * s), _darken(col_, 0.3), 255, False)        # the belt-line rubber
            mq = [B.at(gh[3][0] - 0.2, side * (hw + 0.08), belt + 0.03), B.at(gh[3][0] - 0.2, side * (hw + 0.27), belt + 0.05),
                  B.at(gh[3][0] - 0.2, side * (hw + 0.27), belt + 0.17), B.at(gh[3][0] - 0.2, side * (hw + 0.1), belt + 0.17)]
            mp = v.poly3(mq)
            if not mp.isEmpty():
                pen.fill(mp, _darken(lit(col_, mq[1], None), 0.45)); pen.line(mp, 1.0)
        P.append(_DPart((lambda pts: lambda v: min(v.d(q[0], q[2]) for q in pts))(sw), fn=sidewin, ref=B.at(-0.2, side * (W / 2 + 0.05), belt + 0.3),
                        tag='window_r' if side > 0 else 'window_l'))
    if interior:                                                            # what you see through the glass: seats, dash, wheel
        dk = '#23262e'
        for n_ in (-0.37, 0.37):
            P.append(Part(sub(B, -0.42, -0.22, n_ - 0.24, n_ + 0.24, belt - 0.45, belt + 0.3), {'all': dk, 'top': '#30343c'}, tag='seat_back'))
            P.append(Part(sub(B, -0.4, -0.27, n_ - 0.12, n_ + 0.12, belt + 0.33, belt + 0.5), {'all': dk, 'top': '#30343c'}, tag='seat_back'))
        P.append(Part(sub(B, -1.62, -1.45, -0.7, 0.7, belt - 0.45, belt + 0.28), {'all': dk, 'top': '#30343c'}, tag='rear_seat'))
        P.append(Part(sub(B, u_f - 1.45, u_f - 1.08, -0.78, 0.78, belt - 0.3, belt + 0.0), {'all': '#16181c', 'top': '#202228'}, tag='dash'))

        def wheel_ring(pen, v):
            c = B.at(0.42, -0.37, belt + 0.08)
            if v.d(c[0], c[2]) < 0.2: return
            pts = [B.at(0.42 + 0.06 * math.sin(2 * math.pi * k / 18), -0.37 + 0.18 * math.cos(2 * math.pi * k / 18), belt + 0.08 + 0.17 * math.sin(2 * math.pi * k / 18)) for k in range(19)]
            pen.line(poly([v.p(*q) for q in pts], False), max(1.5, 0.03 * v.s(c[0], c[2])), '#0e0f12')
        P.append(Part(fn=wheel_ring, ref=B.at(0.42, -0.37, belt), tag='wheel'))
        cen = (B.cx, B.cy)
        P = [(_DPart((lambda v, c=cen: v.d(c[0], c[1]) + 0.08), box=p_.box, mats=p_.mats, fn=p_.fn, ref=p_.ref, tag=p_.tag, skip=p_.skip)
              if p_.tag in ('seat_back', 'rear_seat', 'dash') or (p_.tag == 'wheel' and p_.fn is wheel_ring) else p_) for p_ in P]
    seats = {'driver': B.at(-0.05, -0.37, 0)[0::2], 'passenger': B.at(-0.05, 0.37, 0)[0::2], 'back_l': B.at(-1.05, -0.38, 0)[0::2], 'back_r': B.at(-1.05, 0.38, 0)[0::2]}
    return P, seats, B


def dr_headlight_beams(pen, v, B, k=1.0, t=0.0, rain=True, reach=9.0):
    """Two headlight beams from the car (Box from dr_car_parts) through the rain: soft cones on the ground + the glare."""
    if k <= 0.01: return
    W = DCAR['W']; hood = B.Y0 + DCAR['hood']
    fwd = (B.U[0], B.U[1])
    for side in (1, -1):
        hl = B.at(B.w / 2 + 0.01, side * (W / 2 - 0.28), B.Y0 + 0.61)
        if v.d(hl[0], hl[2]) < 0.2: continue
        s = v.s(hl[0], hl[2])
        far_c = (hl[0] + fwd[0] * reach, hl[2] + fwd[1] * reach)
        sp_ = 0.42 * reach
        pa = (far_c[0] - fwd[1] * sp_ * side * -1, far_c[1] + fwd[0] * sp_ * side * -1)
        q = [(hl[0], B.Y0 + 0.02, hl[2]), (far_c[0] + fwd[1] * sp_, B.Y0 + 0.01, far_c[1] - fwd[0] * sp_), (far_c[0] - fwd[1] * sp_, B.Y0 + 0.01, far_c[1] + fwd[0] * sp_)]
        path = v.poly3(q)
        if not path.isEmpty():
            a_, b_ = v.p(*q[0]), v.p(far_c[0], B.Y0, far_c[1])
            pen.cv.save(); pen.cv.clipPath(path, skia.ClipOp.kIntersect, True)
            pen.linear(None, a_[0], a_[1], b_[0], b_[1], [(0, '#fff2d6', 60 * k), (0.4, '#fff2d6', 18 * k), (1, '#fff2d6', 0)])
            pen.cv.restore()
        qa = [(hl[0], hl[1] + 0.05, hl[2]), (far_c[0] + fwd[1] * sp_ * 0.6, hl[1] + 0.9, far_c[1] - fwd[0] * sp_ * 0.6),
              (far_c[0] - fwd[1] * sp_ * 0.6, hl[1] - 0.3, far_c[1] + fwd[0] * sp_ * 0.6)]
        cone = v.poly3(qa)
        if not cone.isEmpty():
            a_, b_ = v.p(*qa[0]), v.p(far_c[0], hl[1], far_c[1])
            pen.linear(cone, a_[0], a_[1], b_[0], b_[1], [(0, '#fff2d6', 70 * k), (0.4, '#fff2d6', 22 * k), (1, '#fff2d6', 0)])
            if rain:
                bb = _rb(cone)
                pen.cv.save(); pen.cv.clipPath(cone, skia.ClipOp.kIntersect, True)
                dr_rain(pen, t, (bb[0], bb[1], bb[2], bb[3]), k, 11 + side, 1.3, 0.08, '#fff6e0', 90, max(40, int((bb[2] - bb[0]) * (bb[3] - bb[1]) / 2500)),
                        L=clamp(s * 0.5, 5.0, 60.0), w=clamp(s * 0.014, 0.7, 1.6))
                pen.cv.restore()
        px, py = v.p(*hl); s = v.s(hl[0], hl[2])
        facing = clamp((-(hl[0] - v.hx) * fwd[0] - (hl[2] - v.hy) * fwd[1]) / max(1e-3, math.hypot(hl[0] - v.hx, hl[2] - v.hy)), 0, 1)
        pen.glow(px, py, (0.5 + 2.2 * facing ** 3) * s, '#fff2d6', (90 + 150 * facing ** 2) * k)
        pen.glow(px, py, 0.12 * s, '#ffffff', 230 * k)


def dr_taillight_glow(pen, v, B, k=1.0):
    if k <= 0.01: return
    W = DCAR['W']; belt = B.Y0 + DCAR['belt']
    for side in (1, -1):
        tl = B.at(-B.w / 2 - 0.01, side * (W / 2 - 0.15), B.Y0 + 0.7)
        if v.d(tl[0], tl[2]) < 0.3 or not v.visible(tl, (-B.U[0], 0.0, -B.U[1])): continue
        px, py = v.p(*tl); s = v.s(tl[0], tl[2])
        pen.glow(px, py, 0.6 * s, '#ff3020', 100 * k)


def dr_exhaust(pen, v, B, t=0.0, k=1.0):
    """Puffs of exhaust from the tailpipe curling up into the rain (the engine is running)."""
    if k <= 0.01: return
    tp = B.at(-B.w / 2 - 0.05, -0.5, B.Y0 + 0.22)
    if v.d(tp[0], tp[2]) < 0.3: return
    s = v.s(tp[0], tp[2])
    for i in range(6):
        ph = (t * 0.45 + i / 6.0) % 1.0
        P = (tp[0] - B.U[0] * ph * 1.2, tp[1] + ph * 0.9, tp[2] - B.U[1] * ph * 1.2)
        px, py = v.p(*P)
        r = (0.08 + 0.35 * ph) * s
        pen.fill(oval(px + 0.1 * s * math.sin(t + i), py, r, r * 0.8), '#c8d0e0', 46 * k * (1 - ph) * min(1, ph * 6), blur=r * 0.5)


def dr_car_in_view(v, name='car', lights=True, beams=True, exhaust=True, order_fn=None, amb=None, steady=None, cx=None, cy=None):
    """Halverson's car as layers for a view: the car split into the parts behind and in front of the driver's seat
    (cached), plus live layers (beams with rain, tail glow, exhaust). order_fn(depth) -> draw order (outside a window:
    ORDER_SHELL + 20 + 0.1 d, like BSet.order_at for points outside)."""
    parts, seats, B = dr_car_parts(cx, cy, lights=lights)
    amb = amb or '#3e4a76'
    steady = steady if steady is not None else [Lamp(kind='dir', c='#9aa8e0', k=0.45, d=_norm3((0.3, -0.8, 0.5))),
                                                Lamp(-6.0, D_GROUND + 6.0, -14.2, 14.0, D_SODIUM, 0.7, fall=1.3)]
    occ = seats['driver']
    do = v.d(occ[0], occ[1])
    of = order_fn or (lambda d_: d_)
    back = [p_ for p_ in parts if p_.depth(v) >= do - 0.14]
    front = [p_ for p_ in parts if p_.depth(v) < do - 0.14]
    L = []
    key = 'drcar:%s:%.2f,%.2f,%.1f,%.1f,%d' % (v.name, v.hx, v.hy, v.yaw, v.S, int(lights))
    L += blit(max(0.3, do + 0.1), (lambda ps: lambda pen: draw_parts(pen, v, ps))(back), name + '_back', key + ':b', FRAME, amb, steady, (), order=of(do + 0.1))
    if front:
        L += blit(max(0.3, do - 0.2), (lambda ps: lambda pen: draw_parts(pen, v, ps))(front), name + '_front', key + ':f', FRAME, amb, steady, (), order=of(do - 0.15))
    if beams:
        lay = Layer(max(0.3, do), lambda pen, t: (dr_headlight_beams(pen, v, B, 1.0, t), dr_taillight_glow(pen, v, B, 1.0)), name + '_beams', blur=None)
        lay.order = of(do - 0.2); L.append(lay)
    if exhaust:
        lay = Layer(max(0.3, do), lambda pen, t: dr_exhaust(pen, v, B, t), name + '_exhaust', blur=None)
        lay.order = of(do - 0.18); L.append(lay)
    return L, seats, B


def _dr_outside_front(pen, v, tod='night', car=False, glow=None, bus=True):
    """Everything seen from inside the front rooms through their windows (cached): the sky, the street, the houses
    across, the streetlights (their glow is live), the bus stop. The car is NOT here (dr_car_in_view adds it as its own
    layers so Halverson can sit in it)."""
    tt = 'night' if tod == 'night' else 'dawn'
    dr_sky(pen, v, tt)
    dr_far_ring(pen, v, tt)
    with lighting(*_ext_light_d(tod)):
        dr_ground_front(pen, v, tod)
        for (x0, x1) in D_ACROSS:
            dr_neighbour(pen, v, x0, x1, -24.5, 9.0, tod, lit_room=(1 if x0 == -38.0 else None), seed=int(x0))
        for (x0, x1, yf, tag) in D_NEIGH[:2]:
            dr_neighbour(pen, v, x0, x1, yf, 10.0, tod, seed=int(x0) + 5)
        for i, (x, y) in enumerate([(-14.0, -21.5), (2.0, -21.0), (24.0, -21.8), (-36.0, -22.0), D_MAPLE]):
            if v.d(x, y) < 1.0: continue
            bx, by = v.p(x, D_GROUND, y)
            draw_tree(pen, bx, by, (7.5 if i < 4 else 8.5) * v.s(x, y), 0.0, 500 + i, 0.0, '#0e1218' if tod == 'night' else '#3a3a34', None, 5)
        for (x, y) in D_LAMPS + [D_BUS_LAMP]:
            dr_streetlight(pen, v, x, y, 1.0, arm=1.0 if y > -15 else -1.0)
        dr_bus_stop(pen, v)
        dr_mailbox(pen, v)


def _dr_outside_back(pen, v, tod='night'):
    """The back yard through the kitchen / bathroom / hall windows: a fence, the neighbour's garage light, wet trees."""
    tt = 'night' if tod == 'night' else 'dawn'
    dr_sky(pen, v, tt)
    dr_far_ring(pen, v, tt, cy=10.0)
    with lighting(*_ext_light_d(tod)):
        F = floor_face(-90.0, 90.0, 9.6, 90.0, D_GROUND)
        draw_face(pen, v, F, lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'grunge', 0.6, 'overlay', 5.0), '#1a2622', ao=False, line=False)
        for i, x in enumerate(np.arange(-12.0, 12.0, 0.15)):
            if v.d(x, 18.0) < 1: continue
            pen.seg(v.p(x, D_GROUND, 18.0), v.p(x, D_GROUND + 1.8, 18.0), max(1.0, 0.1 * v.s(x, 18.0)), '#2a2a26' if i % 12 else '#1a1a18')
        for i, (x, y) in enumerate([(-6.0, 21.0), (3.0, 24.0), (9.0, 22.0)]):
            if v.d(x, y) < 1: continue
            bx, by = v.p(x, D_GROUND, y)
            draw_tree(pen, bx, by, 8.0 * v.s(x, y), 0.0, 600 + i, 0.0, '#0e1218', None, 5)
        gx, gy = v.p(6.0, 2.0, 26.0)
        if v.d(6.0, 26.0) > 1: pen.glow(gx, gy, 2.0 * v.s(6.0, 26.0), '#ffc880', 50)


def _street_glows(v, tod='night', flicker_bus=True, rain=True):
    """Live layer: the streetlights' glow, cones and pools (and the bus-stop light flickering)."""
    if tod != 'night': return None

    def draw(pen, t):
        for (x, y) in D_LAMPS:
            dr_streetlight_glow(pen, v, x, y, 1.0, D_SODIUM, 1.0, rain=rain, t=t)
        k = dr_bus_flicker(t) if flicker_bus else 1.0
        dr_streetlight_glow(pen, v, D_BUS_LAMP[0], D_BUS_LAMP[1], k, '#d0f0b0', -1.0, rain=rain, t=t)
    lay = Layer(30.0, draw, 'street_glow', blur=None)
    lay.order = ORDER_OUT - 0.5
    return lay


def dr_bus_flicker(t, seed=77):
    """The bus-stop streetlight: mostly on, buzzing, dropping out in short stutters every few seconds."""
    return flicker(t, seed, 1.0, None, 0.35) * (0.25 if (math.floor(t * 0.37) % 3 == 1 and (t * 0.37) % 1.0 < 0.08) else 1.0)


# ====================================================================================================== house cameras + builders
# living room (the narrator's eye ~1.5 m; seated people need the seat at |turn| >= 0.5 from the camera: noted per camera)
_dcam('dr_liv_wide', 760, 470, 1.55, -1.55, 5.05, -140, _env(), "from the back-east corner: Grandpa's armchair by the picture window (3/4), "
      'the side table and lamp, the couch (or the rows), the curio; the door is behind camera-left', 'living')
_dcam('dr_liv_chair', 980, 500, 1.3, -2.25, 2.85, -138, _env(), 'medium on the armchair at 3/4 (seated figure turn ~0.6): the window behind it', 'living')
_dcam('dr_liv_window', 860, 520, 1.5, -2.6, 0.95, 216, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.08), f=(1.0, 1.6)),
      "the narrator's eyes at the picture window: the driveway (Halverson's car, headlights, rain), Larch Street, the bus stop at its west end", 'living')
_dcam('dr_liv_window_bus', 3200, 540, 1.5, -2.45, 0.62, 244.5, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.06), f=(1.0, 1.5)),
      "past her car, down Larch Street through the glass: the bus stop under the flickering streetlight (telephoto POV)", 'living')
_dcam('dr_liv_door', 880, 480, 1.5, -4.55, 1.85, 78, _env(), 'from beside the armchair toward the living-room door (it opens: the narrator in the doorway, the hall behind)', 'living')
_dcam('dr_liv_sunrise', 860, 480, 1.45, -2.0, 3.6, -125, _env(), 'sunrise: the armchair against the glowing window (Grandpa still; Ruth with her ticket)', 'living')
# the waiting room
_dcam('dr_wait_wide', 680, 470, 1.55, -1.45, 3.95, -125, _env(), "the narrator's view from the door: the rows (3/4), HIM in the armchair under NOW SERVING, "
      'the TV in the corner', 'living')
_dcam('dr_wait_front', 680, 480, 1.6, -2.05, 5.2, -158, _env(), 'from behind the last row: the backs of the waiting, HIM facing us at the front', 'living')
_dcam('dr_wait_rows', 820, 480, 1.45, -1.65, 1.05, -58, _env(), 'the rows at 3/4 from the front-east (the grey people turn ~-0.65; Grandpa at the far end by the window)', 'living')
_dcam('dr_wait_him', 1000, 520, 1.3, -2.35, 2.75, -132, _env(), 'HIM in the armchair at 3/4 under the sign (the ticket held out)', 'living')
_dcam('dr_wait_grandpa', 1100, 500, 1.3, -2.55, 4.05, -78, _env(), 'Grandpa in the last row by the window (turn ~-0.8)', 'living')
_dcam('dr_wait_side', 760, 480, 1.4, -5.15, 2.75, 112, _env(), 'from the west wall across the room: HIM (left) reaching all the way to the ticket machine by the door (right)', 'living')
_dcam('dr_wait_machine', 1150, 520, 1.3, -2.75, 2.45, 128, _env(), 'the ticket machine by the door (the long arm comes in from the left)', 'living')
# hall
_dcam('dr_hall_door', 820, 480, 1.5, -0.4, 4.6, 180, _env(), 'down the hall to the front door (peephole, deadbolt): the living-room door on the right', 'hall')
_dcam('dr_hall_back', 820, 480, 1.5, -0.42, 0.55, 0, _env(), 'from the front door down the dark hall: living-room door and kitchen doorway left, bathroom door right', 'hall')
_dcam('dr_hall_livdoor', 900, 490, 1.5, 0.15, 1.2, -55, _env(), 'the living-room door from the hall (3/4): "When I opened the door..."', 'hall')
_dcam('dr_hall_peep', 2100, 560, 1.48, -0.2, 0.6, 196, _env(x=(920, 1000), y=(500, 580), zoom=(1.0, 1.05), f=(1.0, 1.4)), 'close on the peephole and deadbolt', 'hall')
_dcam('dr_hall_floor', 1300, 300, 0.32, -0.15, 0.95, 186, _env(x=(900, 1020), y=(240, 380), zoom=(1.0, 1.08), f=(1.0, 1.6)),
      'low at the bottom of the front door: the paper sliding under it', 'hall')
# kitchen
_dcam('dr_kit_phone', 980, 500, 1.45, -3.35, 7.85, 98, _env(), 'the phone wall: Ruth at the wall phone (profile / 3/4), the dark hall doorway beside it, the counter', 'kitchen')
_dcam('dr_kit_wide', 760, 470, 1.55, -1.42, 6.3, -47, _env(), 'from the hall doorway: the table, the fridge, the sink under the window', 'kitchen')
_dcam('dr_kit_sink', 960, 500, 1.5, -2.15, 7.55, -32, _env(), 'the sink under the window (the paper burning, the match)', 'kitchen')
_dcam('dr_kit_floor', 820, 440, 0.8, -2.75, 7.45, 31, _env(y=(400, 500)), 'low on the kitchen floor: Ruth rocking Milo against the counter-return cabinets at 3/4 '
      '(turn ~0.65), the sink and its window behind them', 'kitchen')
_dcam('dr_kit_phone_side', 980, 500, 1.45, -2.42, 8.82, 152, _env(), 'along the phone wall: Ruth at the phone in PROFILE (facing screen-left), the narrator beside her, '
      'the receiver counter in the foreground left, the dark hall doorway behind them', 'kitchen')
_dcam('dr_kit_hall', 980, 500, 1.4, -3.75, 6.5, 90, _env(), 'from the table to the doorway into the dark hall (the pen click, the scratching)', 'kitchen')
_dcam('dr_kit_front', 820, 480, 1.5, -2.8, 9.0, 205, _env(), 'from the sink toward the front wall: the clock, the table, the doorway', 'kitchen')
# bathroom
_dcam('dr_bath_sink', 900, 500, 1.5, 1.0, 8.6, 128, _env(), 'the sink and the medicine cabinet at 3/4 from the tub end', 'bath')
_dcam('dr_bath_mirror', 980, 520, 1.55, 2.72, 6.75, -90, _env(), "from the mirror's place: Ruth's face as she swings it aside, the doorway behind", 'bath')
_dcam('dr_bath_cabinet', 1500, 540, 1.6, 1.6, 6.88, 93, _env(x=(910, 1010), y=(490, 590), zoom=(1.0, 1.06), f=(1.0, 1.5)),
      'the cabinet straight on: the mirror / the open door with the yellow card', 'bath')
_dcam('dr_bath_door', 900, 490, 1.55, 0.05, 6.7, 95, _env(), 'from the hall through the bathroom door', 'bath')


def _house_extras(sp, v, o, wins, car=False, rain=True, tod='night', glass=True):
    """Live layers every view with windows gets: rain beyond the glass, rain on the glass, the streetlights' glow, and
    (car=True) Halverson's car in the driveway as its own layers (so she can sit in it, order = BSet.order_at)."""
    L = []
    if rain and tod == 'night':
        L.append(_rain_out_layer(v))
        if glass and wins:
            g = _glass_layer('glass_rain', v, wins, ORDER_SHELL - 0.05)
            if g is not None: L.append(g)
    sg = _street_glows(v, tod)
    if sg is not None: L.append(sg)
    if car:
        cl, seats, B = dr_car_in_view(v, order_fn=lambda d_: ORDER_SHELL + 20.0 + 0.1 * d_)
        L += cl
        sp.info['car_seats'] = seats
        for nm, (x, y) in seats.items():
            sp.anchors['car_' + nm] = _mk_spot(v, 'car_' + nm, x, y, D_GROUND, 'seat', "Halverson's car, %s seat (outside: order = sp.order_at)" % nm,
                                               face=(0, 1), seat_Y=0.42)
    return sp.add(*L)


def dr_living(view='wide', state='now', tod='night', lamp=None, ceiling=0.0, headlights=0.0, hall=0.0, door=0.0, coffee=False, keys=None,
              clock=(3, 0), tubes=None, sign=1.0, tv=1.0, ticket='', tear=0.0, rain=None, car=None, serving='1979', **kw):
    """Ruth's living room. state 'now' | '1979' | 'wait' (the waiting room: rows of bolted chairs, the ticket machine,
    NOW SERVING 1979, the TV on a bracket, troffers: tubes = [spec x 4] (default on, dead, flickering, dead)).
    view 'wide' | 'chair' | 'window' | 'door' | 'sunrise' (state now / 1979) or, for the waiting room,
    'wide' | 'front' | 'rows' | 'him' | 'grandpa' | 'side' | 'machine' (also 'chair' / 'window' / 'door' work there).
    tod 'night' | 'sunrise'. Lights (level specs): lamp (side-table lamp; default on in 1979, off now), ceiling,
    headlights (Halverson's beams through the picture window, rule 4-5), hall (light through the open door).
    door: the living-room door angle (deg, 0 shut .. 95 open into the room). coffee: the cup on the side table.
    car: Halverson's car in the driveway (default: now + night); rain (default: night)."""
    if state == 'wait' and view in ('wide', 'front', 'rows', 'him', 'grandpa', 'side', 'machine'):
        name = 'dr_wait_' + view
    else:
        name = 'dr_liv_' + view
    v = cam(name)
    if lamp is None: lamp = 1.0 if (state == '1979' and tod == 'night') else 0.0
    if car is None: car = False
    if rain is None: rain = (tod == 'night' and state != '1979')
    if keys is None: keys = state != '1979'
    o = dict(state=state, tod=tod, lamp=lamp, ceiling=ceiling, headlights=headlights, hall=hall, door=door, coffee=coffee, keys=keys,
             clock=clock if not callable(clock) else 'f', sign=sign, tv=tv, ticket=ticket if not callable(ticket) else 'f', tear=tear if not callable(tear) else 'f', serving=serving)
    if tubes is not None: o['tubes'] = tubes
    main = DrLiving()
    far = [DrHall(far=True)] if (door and not callable(door) and door > 3) or callable(door) else []
    grade = {'now': 'dr_night', '1979': 'dr_1979', 'wait': 'dr_wait'}[state]
    if tod == 'sunrise': grade = 'dr_sunrise79' if state == '1979' else 'dr_sunrise'
    if state == 'now' and tod == 'night' and not (lamp or ceiling or headlights): grade = 'dr_dark'
    out = lambda pen, v_: _dr_outside_front(pen, v_, tod if state != '1979' else ('night' if tod == 'night' else 'sunrise'))
    dyn = []
    if callable(clock):
        dyn.append(dr_live_wall_clock(v, 'living', clock, state))
    if callable(door):
        dyn.append(_live_door_layer('door_live', v, dr_living_door(), door, main, o))
    fk = dict(focus=45.0, dof=1.4) if view == 'window_bus' else (dict(focus=8.0, dof=0.9) if view == 'window' else {})
    sp = build_view(name, v, main, o, far=far, outside=out, grade=grade, dyn=dyn, info_extra=dict(state=state, tod=tod), **fk)
    wins = [_win_glass_quads(((-1.2, 0.0), (-5.6, 0.0)), -1.2 - D_LWIN[1], -1.2 - D_LWIN[0], D_LWIN[2], D_LWIN[3]),
            _win_glass_quads(((-5.6, 0.0), (-5.6, 5.4)), D_SWIN[0], D_SWIN[1], D_SWIN[2], D_SWIN[3])]
    sp = _house_extras(sp, v, o, wins, car=car, rain=rain, tod='night' if tod == 'night' else 'sunrise')
    _to_wall(sp, ('curtains', 'curtains_side'))
    if callable(ticket) or callable(tear):
        tkf = ticket if callable(ticket) else (lambda t: ticket)
        trf = tear if callable(tear) else (lambda t: tear)
        amb, steady, var = main.lights(o)
        sp = sp.add(live_layer('ticket_machine', v, (D_TICKET[0], 0.6, D_TICKET[1]), lambda pen, v_, t: dr_ticket_machine(pen, v_, ticket=tkf(t), tear=trf(t)),
                               amb, steady, var))
    sp.info['note'] = ('Seated people need |turn| >= 0.5: the armchair reads in wide / chair / him / side; the rows in rows / grandpa / side '
                       '(front-on in front: the chair backs hide them); stage with ST.stage_figure(sp, who, spot).')
    return sp


def _far_clipped(R, quad):
    """A room seen through a doorway (quad: four (x, Y, y) corners of the opening): its furniture is clipped to that
    opening, so it can never show through another far room that stands in front of it (far furniture is drawn over every
    far shell)."""
    orig = R.pieces

    def pieces(o):
        out = []
        for P in orig(o):
            def draw(pen, v, P=P):
                path = v.poly3(quad)
                if path.isEmpty(): return
                pen.cv.save(); pen.cv.clipPath(path, skia.ClipOp.kIntersect, True)
                try:
                    P.draw(pen, v)
                finally:
                    pen.cv.restore()
            out.append(Piece(P.name, P.ref, draw, block=P.block, vis=P.vis))
        return out
    R.pieces = pieces
    return R


D_KDOOR_QUAD = [(-1.2, 0.0, D_KDOOR[0]), (-1.2, 0.0, D_KDOOR[1]), (-1.2, D_KDOOR[2], D_KDOOR[1]), (-1.2, D_KDOOR[2], D_KDOOR[0])]
D_LDOOR_QUAD = [(-1.2, 0.0, D_LDOOR[0]), (-1.2, 0.0, D_LDOOR[1]), (-1.2, D_LDOOR[2], D_LDOOR[1]), (-1.2, D_LDOOR[2], D_LDOOR[0])]


def _to_wall(sp, names, order=None):
    """Things that hang flat on a wall (curtains) sort wrongly by their centre when the wall is oblique to the lens:
    draw them straight after the shell and the rain on the glass, before every piece of furniture."""
    for l_ in sp:
        if l_.name.split(':')[0] in names: l_.order = (ORDER_SHELL - 0.06) if order is None else order
    return sp


def _live_door_layer(name, v, D, ang_fn, room, o):
    amb, steady, var = room.lights(o)
    return live_layer(name, v, (D.hinge[0], 1.0, D.hinge[1]), lambda pen, v_, t: D.draw(pen, v_, ang_fn(t)), amb, steady, var)


def dr_live_wall_clock(v, room, clock, state='now'):
    """A wall clock whose time is f(t) -> (h, m) or (h, m, s) (the clock slowing down, rule 7): drawn live on its wall."""
    if room == 'living':
        F = Face((-1.2 - 0.005, D_LCLOCK[1] + 0.2, D_LCLOCK[2] + 0.2), (0, 0, -1), (0, -1, 0), 40.0, 40.0, (-1, 0, 0), 'wall')
        kind = 'office' if state == 'wait' else 'sunburst'
    else:
        F = Face((D_KCLOCK[0] + 0.2, D_KCLOCK[1] + 0.2, 5.4 + 0.005), (-1, 0, 0), (0, -1, 0), 40.0, 40.0, (0, 0, 1), 'wall')
        kind = 'kitchen'

    def draw(pen, t):
        tm = clock(t)
        if not v.visible(F.O, F.n): return
        m, _ = fmat(v, F.O, _scale3(F.Uu, 0.01), _scale3(F.Vu, 0.01))
        pen.cv.save(); pen.cv.concat(m)
        if kind == 'office': _office_clock(pen, 20, 20, 15, tm[0], tm[1], tm[2] if len(tm) > 2 else None)
        elif kind == 'sunburst': _sunburst_clock(pen, 20, 20, 10, tm[0], tm[1])
        else: _kitchen_clock(pen, 20, 20, 13, tm[0], tm[1])
        pen.cv.restore()
    c = F.centre()
    lay = Layer(max(0.3, v.d(c[0], c[2])), draw, 'clock_live', blur=None)
    lay.order = ORDER_SHELL - 0.04
    return lay


def dr_hall(view='door', hall=0.0, porch=1.0, kitchen=0.3, living=0.0, door=0.0, front_door=0.0, bath_door=0.0, headlights=0.0, tod='night',
            living_state='now', **kw):
    """The hall: view 'door' (to the front door), 'back' (down the dark hall), 'livdoor' (the living-room door at 3/4),
    'peep' (close on the peephole), 'floor' (low at the door: the paper slides under it). door = the living-room door
    angle (0..95 or f(t)); living_state 'wait' shows the waiting room through it (green-yellow light spills out)."""
    v = cam('dr_hall_' + view)
    o = dict(hall=hall, porch=porch, kitchen=kitchen, living=living, door=door if not callable(door) else 'f', front_door=front_door,
             bath_door=bath_door, headlights=headlights, tod=tod, porch_lite=_lvl(porch, 0) if not callable(porch) else 0.6)
    if living_state == 'wait':
        o['living_c'] = D_TUBE
        if not living: o['living'] = 0.8
    main = DrHall()
    far = []
    if callable(door) or door > 3: far.append(_far_living(living_state))       # first = drawn last: nearer than the kitchen
    far.append(_far_clipped(DrKitchen(far=True), D_KDOOR_QUAD))
    if bath_door and (callable(bath_door) or bath_door > 3): far.append(DrBath(far=True))
    dyn = []
    if callable(door): dyn.append(_live_door_layer('living_door_live', v, dr_living_door(), door, main, o))
    sp = build_view('dr_hall_' + view, v, main, o, far=far, outside=lambda pen, v_: _dr_outside_front(pen, v_, tod),
                    grade='dr_hall_night' if tod == 'night' else 'dr_sunrise', dyn=dyn, focus=None)
    return sp


class _FarLiving(DrLiving):
    pass


def _far_living(state):
    R = DrLiving(far=True)
    R._state = state
    orig = R.lights, R.shell, R.pieces, R.glows, R.spots

    def wrap(f):
        return lambda *a: f(*a[:-1], dict(a[-1], state=state))
    R.lights = lambda o: orig[0](dict(o, state=state))
    R.shell = lambda pen, v, o: orig[1](pen, v, dict(o, state=state))
    R.pieces = lambda o: orig[2](dict(o, state=state))
    R.glows = lambda v, o: orig[3](v, dict(o, state=state))
    R.spots = lambda v, o: orig[4](v, dict(o, state=state))
    return R


def dr_kitchen(view='phone', era='now', tod='night', hood=1.0, ceiling=0.0, hall=0.0, fire=0.0, phone='hung', cord='in', ring=0.0, clock=(3, 0),
               paper=None, rain=None, **kw):
    """The kitchen. view 'phone' | 'wide' | 'sink' | 'floor' | 'hall' | 'front'. era 'now' | '1979' (harvest gold, the same
    wall phone). phone 'hung' | 'off' | 'counter' or f(t); cord 'in' | 'out' (pulled from the wall: it lies on the floor);
    ring = f(t) 0..1 (the phone shivers); hood = the stove light (on all night); fire = the paper burning in the sink
    (level spec: lights the window and Ruth); paper None | 'ash'. clock = (h, m) or f(t)."""
    v = cam('dr_kit_' + view)
    if rain is None: rain = tod == 'night' and era == 'now'
    o = dict(era=era, tod=tod, hood=hood, ceiling=ceiling, hall=hall, fire=fire, phone=phone if not callable(phone) else 'f', cord=cord,
             ring=ring if not callable(ring) else 'f', clock=clock if not callable(clock) else 'f', paper=paper)
    main = DrKitchen()
    far = [DrHall(far=True)]
    dyn = []
    if callable(phone) or callable(ring):
        phf = phone if callable(phone) else (lambda t: phone)
        rgf = ring if callable(ring) else (lambda t: ring)
        amb, steady, var = main.lights(o)
        dyn.append(live_layer('phone_live', v, (D_PHONE[0] - 0.05, 1.3, D_PHONE[2]), lambda pen, v_, t: dr_wall_phone(pen, v_, phf(t), cord, rgf(t), t, era),
                              amb, steady, var))
    if callable(clock): dyn.append(dr_live_wall_clock(v, 'kitchen', clock))
    grade = 'dr_1979' if era == '1979' else ('dr_night' if tod == 'night' else 'dr_sunrise')
    sp = build_view('dr_kit_' + view, v, main, o, far=far, outside=lambda pen, v_: _dr_outside_back(pen, v_, tod), grade=grade, dyn=dyn)
    wins = [_win_glass_quads(((-5.6, 9.6), (-1.2, 9.6)), D_KWIN[0] + 5.6, D_KWIN[1] + 5.6, D_KWIN[2], D_KWIN[3])]
    if rain and tod == 'night':
        sp = sp.add(_rain_out_layer(v), _glass_layer('glass_rain', v, wins, ORDER_SHELL - 0.05))
    return sp


def dr_bath(view='sink', cabinet=0.0, card=True, vanity=1.0, ceiling=0.0, hall=0.0, bath_door=80.0, tod='night', lamp=0.0, lamp_prop=False,
            cab_empty=False, **kw):
    """The bathroom and the medicine cabinet. view 'sink' | 'mirror' | 'cabinet' | 'door'. cabinet = the mirror door open
    0..1 (or degrees > 1; 1 = 105 deg) or f(t); card: the yellow card taped inside the door (False after the narrator tears it
    out: the tape ghosts stay); cab_empty: the shelves cleared (the outro). vanity = the light bar over it."""
    v = cam('dr_bath_' + view)
    o = dict(cabinet=cabinet if not callable(cabinet) else 0.0, card=card, vanity=vanity, ceiling=ceiling, hall=hall, bath_door=bath_door, tod=tod,
             lamp=lamp, lamp_prop=lamp_prop, cab_empty=cab_empty)
    main = DrBath()
    dyn = []
    if callable(cabinet):
        D = dr_cabinet_door(o)
        dyn.append(live_layer('cabinet_door_live', v, (D_CAB[0] - 0.15, 1.6, D_CAB[1] + 0.2),
                              lambda pen, v_, t: D.draw(pen, v_, (lambda a_: a_ * 105.0 if a_ <= 1.0 else a_)(cabinet(t))), *main.lights(o)))
        sp = build_view('dr_bath_' + view, v, main, o, far=[DrHall(far=True)], outside=lambda pen, v_: _dr_outside_back(pen, v_, tod), grade='dr_night', dyn=dyn)
        return sp.without('cabinet_door')
    return build_view('dr_bath_' + view, v, main, o, far=[DrHall(far=True)], outside=lambda pen, v_: _dr_outside_back(pen, v_, tod), grade='dr_night', dyn=dyn)


# ---------------------------------------------------------------------------------------------- outside views (the street as a room)
class DrStreet(Room):
    """Larch Street as a 'room' for the generic builder: the shell holds the sky, the ground, the houses, the streetlights
    and Ruth's house + porch; the car is a piece (Halverson sits in it: the windows / body sort round her)."""
    name = 'street'
    poly = [(-90.0, -40.0), (90.0, -40.0), (90.0, -0.02), (-90.0, -0.02)]

    def lights(self, o):
        tod = o.get('tod', 'night')
        amb, steady = _ext_light_d(tod)
        steady = list(steady)
        if tod == 'night':
            for (x, y) in D_LAMPS:
                steady.append(Lamp(x, D_GROUND + 6.0, y - 1.6, 14.0, D_SODIUM, 1.9, (1.0, 0.6, 0.2), fall=1.35))
        porch = [Lamp(D_PLIGHT[0], D_PLIGHT[1], D_PLIGHT[2] - 0.3, 6.5, '#ffc888', 1.6, fall=1.5)]
        heads = [Lamp(D_CAR[0], D_GROUND + 0.7, D_CAR[1] + 3.2, 6.5, D_HEAD, 1.5, (1.0, 1.0, 0.6), fall=1.4)]
        hall = [Lamp(-0.4, 1.2, -0.6, 3.5, '#ffd8a0', 1.2, fall=1.5)]
        bus = [Lamp(D_BUS_LAMP[0], D_GROUND + 6.0, D_BUS_LAMP[1] + 1.6, 9.0, '#c8f0b0', 1.4, (1.0, 0.6, 0.2), fall=1.4)]
        var = [('porch', porch, _kfn(o.get('porch', 1.0), 251)), ('headlights', heads, _kfn(o.get('headlights', 1.0 if o.get('car') else 0.0), 252)),
               ('door_light', hall, _kfn(o.get('door_light', 0.0), 253)), ('bus_light', bus, o.get('bus_fn') or _kfn(1.0 if tod == 'night' else 0.0, 254))]
        return amb, steady, var

    def shell(self, pen, v, o):
        tod = o.get('tod', 'night')
        tt = 'night' if tod == 'night' else 'dawn'
        dr_sky(pen, v, tt)
        dr_far_ring(pen, v, tt)
        dr_ground_front(pen, v, tod)
        for (x0, x1) in D_ACROSS:
            dr_neighbour(pen, v, x0, x1, -24.5, 9.0, tod, lit_room=(1 if x0 == -38.0 else None), seed=int(x0))
        for (x0, x1, yf, tag) in D_NEIGH[:2]:
            dr_neighbour(pen, v, x0, x1, yf, 10.0, tod, seed=int(x0) + 5)
        trees = [(-14.0, -21.5, 7.5), (2.0, -21.0, 7.5), (24.0, -21.8, 7.5), (-36.0, -22.0, 7.5), (-52.0, -22.5, 7.0)]
        trees.sort(key=lambda q: -v.d(q[0], q[1]))
        for i, (x, y, h) in enumerate(trees):
            if v.d(x, y) < 1.0: continue
            bx, by = v.p(x, D_GROUND, y)
            draw_tree(pen, bx, by, h * v.s(x, y), 0.0, 500 + i, 0.0, '#0e1218' if tod == 'night' else '#3a3a34', None, 5)
        for (x, y) in D_LAMPS + [D_BUS_LAMP]:
            if v.d(x, y) > 0.8: dr_streetlight(pen, v, x, y, 1.0, arm=1.0 if y > -15 else -1.0)
        dr_bus_stop(pen, v)
        dr_mailbox(pen, v)
        dr_house_ext(pen, v, tod, glow=o.get('glow', {}), door_open=o.get('front_door', 0.0) if not callable(o.get('front_door', 0.0)) else 0.0)
        dr_porch(pen, v, tod)
        if v.d(D_MAPLE[0], D_MAPLE[1]) > 1.0:
            bx, by = v.p(D_MAPLE[0], D_GROUND, D_MAPLE[1])
            draw_tree(pen, bx, by, 8.5 * v.s(D_MAPLE[0], D_MAPLE[1]), 0.0, 504, 0.0, '#0e1218' if tod == 'night' else '#3a3a34', None, 5)

    def pieces(self, o):
        P = []
        if o.get('car'):
            parts, seats, B = dr_car_parts(lights=o.get('car_lights', True))
            P.append(Piece('car', (B.cx, D_GROUND + 0.6, B.cy), lambda pen, v, parts=parts: draw_parts(pen, v, parts),
                           occupant=[seats['driver']], front=parts, block=B.footprint()))
        return P

    def glows(self, v, o):
        tod = o.get('tod', 'night')
        G = []
        kp = _kfn(o.get('porch', 1.0), 251)
        G.append(('porch_lantern', (D_PLIGHT[0], D_PLIGHT[1], D_PLIGHT[2] - 0.05), lambda pen, t: dr_porch_light_draw(pen, v, kp(t))))
        return G

    def spots(self, v, o):
        S = {}
        G = D_GROUND
        S['porch_door'] = _mk_spot(v, 'porch_door', -0.4, -0.55, 0.0, 'stand', 'on the porch at the front door, facing it (Halverson knocking: +y)', face=(0, 1))
        S['porch_knock'] = _mk_spot(v, 'porch_knock', -0.15, -0.02, 1.45, 'point', 'where her knuckles meet the door')
        S['porch_step'] = _mk_spot(v, 'porch_step', -0.38, -2.05, -0.5 / 3, 'stand', 'on the top step', face=(0, 1))
        S['walk'] = _mk_spot(v, 'walk', -0.38, -4.2, G, 'stand', 'on the front walk', face=(0, 1))
        S['walk_run'] = _mk_spot(v, 'walk_run', -2.6, -3.4, G, 'stand', 'Halverson running from her car to the steps (path: car door -> walk_run -> porch_step)', face=(0.7, 0.7))
        S['car_door'] = _mk_spot(v, 'car_door', D_CAR[0] - 1.25, D_CAR[1] + 0.05, G, 'stand', "beside the driver's door (outside)", face=(1, 0))
        S['driveway'] = _mk_spot(v, 'driveway', -6.2, -1.8, G, 'stand', 'the top of the driveway, by the car\'s nose')
        S['lawn'] = _mk_spot(v, 'lawn', -3.4, -2.2, G, 'stand', 'the lawn under the picture window')
        S['window_out'] = _mk_spot(v, 'window_out', -2.6, -0.02, 1.45, 'point', 'the picture window from outside (the narrator\'s face at the glass)')
        S['bus_bench'] = _mk_spot(v, 'bus_bench', D_BUS[0], D_BUS[1] - 0.04, G, 'seat', 'the bus-stop bench (HIM folded on it, facing the street +y; knees above his head)',
                                  face=(0, 1), seat_Y=0.45)
        S['bus_lamp'] = _mk_spot(v, 'bus_lamp', D_BUS_LAMP[0], D_BUS_LAMP[1] + 1.6, G + 6.0, 'point', 'the flickering streetlight over the bus stop (lamp head)')
        S['street_mid'] = _mk_spot(v, 'street_mid', -6.0, -15.6, G - 0.12, 'stand', 'the middle of Larch Street')
        if o.get('car'):
            _, seats, B = dr_car_parts()
            for nm, (x, y) in seats.items():
                S['car_' + nm] = _mk_spot(v, 'car_' + nm, x, y, G, 'seat', "Halverson's car: %s seat (hip point; seat top 0.42 m above the ground)" % nm,
                                          face=(0, 1), seat_Y=0.42)
        return S


_dcam('dr_ext_house', 820, 520, D_GROUND + 1.6, -1.8, -19.9, 4, _env(f=(1.0, 2.6)), "Ruth's house from across Larch Street: the porch, the picture window, the car in the driveway", 'street')
_dcam('dr_ext_porch', 980, 520, D_GROUND + 1.62, 1.45, -2.75, -38, _env(), 'the porch from the walk at 3/4: the red door, the porch light, Halverson knocking', 'street')
_dcam('dr_ext_door', 900, 500, D_GROUND + 1.55, -0.2, -4.6, 2, _env(), 'up the steps to the front door (open: the narrator in the doorway with Milo)', 'street')
_dcam('dr_ext_driveway', 900, 520, 1.55, -1.3, -0.45, -124, _env(), 'from the porch to the driveway: the car nose-in, headlights in our eyes, the rain in the beams', 'street')
_dcam('dr_ext_car', 1000, 520, D_GROUND + 1.45, -5.1, -1.3, -146, _env(), "the car from the front-right: Halverson in the driver's seat through the windshield, phone at her ear", 'street')
_dcam('dr_ext_street', 1200, 520, D_GROUND + 1.5, -9.6, -11.4, -100, _env(f=(1.0, 2.4)), 'down Larch Street to the west: the bus stop under its flickering light at the end', 'street')
_dcam('dr_ext_bus', 2300, 600, D_GROUND + 1.45, -39.0, -15.6, -124, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.06), f=(1.0, 1.6)),
      'telephoto on the bus-stop bench under the flickering streetlight (HIM folded there, waiting)', 'street')
_dcam('dr_ext_bus_far', 2900, 540, D_GROUND + 1.6, -6.5, -11.3, -110, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.06), f=(1.0, 1.6)),
      'from the end of the driveway down the street: the bus stop small and far under its light', 'street')
_dcam('dr_ext_peephole', 560, 540, D_PEEP_Y, -0.4, -0.06, 180, _env(x=(940, 980), y=(520, 560), zoom=(1.0, 1.02), f=(1.0, 1.2)),
      "through the peephole: the fisheye porch, Halverson in the rain, her car's headlights beyond", 'street', pitch=24.0)


def dr_front(view='house', tod='night', car=None, rain=None, porch=1.0, headlights=None, front_door=0.0, glow=None, bus_flicker=True, **kw):
    """Outside Ruth's house on Larch Street. view 'house' (from across the street), 'porch' (the door at 3/4), 'door' (up the
    steps to the open door), 'driveway' (from the porch to the car), 'car' (Halverson through the windshield), 'street'
    (down the street to the bus stop), 'bus' (telephoto on the bench), 'peephole' (the fisheye from inside the door).
    car: Halverson's car in the driveway, engine running, headlights on (default: night); rain (default: night);
    tod 'night' | 'sunrise' (the end: the rain gone, wet and gold, no car); front_door: open (> 0) = warm hall light."""
    v = cam('dr_ext_' + view)
    if car is None: car = tod == 'night'
    if rain is None: rain = tod == 'night'
    if headlights is None: headlights = 1.0 if car else 0.0
    glow = dict(glow or {})
    o = dict(tod=tod, car=car, porch=porch, headlights=headlights, front_door=front_door if not callable(front_door) else 0.0, glow=glow,
             door_light=1.0 if (front_door and not callable(front_door)) else 0.0)
    if bus_flicker and tod == 'night': o['bus_fn'] = dr_bus_flicker
    main = DrStreet()
    dyn = []
    if car:
        _, _, B = dr_car_parts()
        def _beams(pen, t):
            cut = None
            if v.hy < -0.05 and v.hx > D_HOUSE[0]:               # from in front of the house its front wall hides the beams behind it
                cut = v.poly3([(D_HOUSE[0], D_GROUND, 0.0), (D_HOUSE[1], D_GROUND, 0.0), (D_HOUSE[1], D_RIDGE, 0.0), (D_HOUSE[0], D_RIDGE, 0.0)])
                if cut.isEmpty(): cut = None
            if cut is not None:
                pen.cv.save(); pen.cv.clipPath(cut, skia.ClipOp.kDifference, True)
            try:
                dr_headlight_beams(pen, v, B, _lvl(headlights, 252, t), t, rain); dr_taillight_glow(pen, v, B, 1.0)
            finally:
                if cut is not None: pen.cv.restore()
        lay = Layer(max(0.3, v.d(B.cx, B.cy)), _beams, 'car_beams', blur=None)
        lay.order = v.d(B.cx, B.cy) - 0.25
        dyn.append(lay)
        lay2 = Layer(max(0.3, v.d(B.cx, B.cy)), lambda pen, t: dr_exhaust(pen, v, B, t), 'car_exhaust', blur=None)
        lay2.order = v.d(B.cx, B.cy) - 0.2
        dyn.append(lay2)
    if tod == 'night':
        def glows(pen, t):
            for (x, y) in D_LAMPS:
                dr_streetlight_glow(pen, v, x, y, 1.0, D_SODIUM, 1.0, rain=rain, t=t)
            dr_streetlight_glow(pen, v, D_BUS_LAMP[0], D_BUS_LAMP[1], dr_bus_flicker(t) if bus_flicker else 1.0, '#d0f0b0', -1.0, rain=rain, t=t)
        lay = Layer(40.0, glows, 'street_glow', blur=None); lay.order = ORDER_SHELL - 0.5
        dyn.append(lay)
    if rain:
        def far_rain(pen, t): dr_rain(pen, t, (-500, -400, 2900, 1800), 1.0, 7, 0.9, 0.1, '#a8b4cc', 22, 320, far=True)
        def near_rain(pen, t): dr_rain(pen, t, (-500, -400, 2900, 1800), 1.0, 8, 1.4, 0.12, '#c8d0e4', 34, 120)
        l1 = Layer(30.0, far_rain, 'rain_far', blur=None); l1.order = ORDER_SHELL - 0.6
        l2 = Layer(0.5, near_rain, 'rain_near', blur=None); l2.order = 0.2
        dyn += [l1, l2]
    lens, grade, cover = 'lens', ('dr_ext' if tod == 'night' else 'dr_sunrise'), None
    if view == 'peephole':
        lens, grade, cover = (PEEPHOLE_LENS or _peep_lens()), 'porch_warm', PEEP
    sp = build_view('dr_ext_' + view, v, main, o, outside=None, lens=lens, grade=grade, dyn=dyn, cover=cover,
                    focus=(v.d(-0.4, -0.6) if view == 'peephole' else None), dof=0.6)
    sp.info['note'] = 'Outside: figures order = sp.order_at(x, y); Halverson in the car: stage at anchors car_driver (the windshield / near window sort round her).'
    return sp


# ====================================================================================================== other locations
class DrBox(Room):
    """A generic rectangular room for the other locations (each on its own little plan, metres): cfg = dict(name, R (x0,
    x1, y0, y1), H (ceiling), floor=dict(base, kind, ink, ink2, scale, art), walls=dict(paper, ink, kind, wains, wcol, trim,
    rail, base_h, pa, scale, ink2), holes={side: [(xa, ya, xb, yb, v0, v1)]}, art={side: fn}, windows=[(side, (xa, ya, xb, yb,
    sill, top), lites, frame)], ceil=dict(c, art), lights=fn(o), pieces=fn(o), spots=fn(v, o), glows=fn(v, o), shell_x=fn(pen,
    v, o) (extra static drawing after the walls))."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.name = cfg['name']
        self.poly = _r4p(cfg['R'])

    def lights(self, o): return self.cfg['lights'](o)

    def shell(self, pen, v, o):
        c = self.cfg
        x0, x1, y0, y1 = c['R']
        H = c.get('H', 2.7)
        fl = dict(c.get('floor', {}))
        floor_rect(pen, v, x0, x1, y0, y1, 0.0, fl.get('base', '#c8c0b0'), fl.get('kind', 'tile'), fl.get('ink', '#a89e88'), fl.get('ink2'),
                   seed=fl.get('seed', 3), art=fl.get('art'), scale=fl.get('scale', 1.0))
        wk = dict(c.get('walls', {}))
        paper = wk.pop('paper', '#d8d4c8'); ink = wk.pop('ink', None); kind = wk.pop('kind', None)
        arts = c.get('art', {})
        if callable(arts): arts = arts(o)
        for (side, a, b, u_of) in _walls_of(c['R']):
            hs = [_hole_x(u_of, xa, xb, ya, yb, v0, v1) for (xa, ya, xb, yb, v0, v1) in c.get('holes', {}).get(side, [])]
            hs += [_hole_x(u_of, xa, xb, ya, yb, sill, top) for (sd, (xa, ya, xb, yb, sill, top), lites, fr) in c.get('windows', []) if sd == side]
            wall(pen, v, a, b, 0.0, H, paper, ink, kind, hs, art=arts.get(side), **wk)
        cl = c.get('ceil', {})
        ceil_rect(pen, v, x0, x1, y0, y1, H, c=cl.get('c', '#e8e6e0'), art=cl.get('art'))
        for (sd, (xa, ya, xb, yb, sill, top), lites, fr) in c.get('windows', []):
            for (side, a, b, u_of) in _walls_of(c['R']):
                if side != sd: continue
                ua, ub = sorted((u_of(xa, ya), u_of(xb, yb)))
                window_unit(pen, v, a, b, ua, ub, sill, top, lites=lites, frame=fr)
        if c.get('shell_x'): c['shell_x'](pen, v, o)

    def pieces(self, o): return self.cfg.get('pieces', lambda o: [])(o)

    def glows(self, v, o): return self.cfg.get('glows', lambda v, o: [])(v, o)

    def spots(self, v, o): return self.cfg.get('spots', lambda v, o: {})(v, o)


def _box_build(cfg, view, o, outside=None, grade='dr_clinic', dyn=None, wins=(), rain=False, focus=None, dof=0.8, extra_info=None):
    v = cam(view)
    room = DrBox(cfg)
    sp = build_view(view, v, room, o, outside=outside, grade=grade, dyn=dyn, focus=focus, dof=dof, info_extra=extra_info)
    if rain:
        L = [_rain_out_layer(v)]
        g = _glass_layer('glass_rain', v, list(wins), ORDER_SHELL - 0.05) if wins else None
        if g is not None: L.append(g)
        sp = sp.add(*L)
    return sp


def _ceiling_panel_light(pen, v, x, y, Y, k=1.0, w=1.2, d=0.6, c='#fff8ec'):
    """A lit ceiling panel (emissive): the warm, even light of the doctors' world."""
    q = [(x - w / 2, Y - 0.006, y - d / 2), (x + w / 2, Y - 0.006, y - d / 2), (x + w / 2, Y - 0.006, y + d / 2), (x - w / 2, Y - 0.006, y + d / 2)]
    path = v.poly3(q)
    if path.isEmpty() or v.cam_h > Y: return
    pen.fill(path, mix('#d8d8d0', '#fffdf6', k)); pen.line(path, 1.0, '#9a9a90')
    if k > 0.01:
        b = _rb(path)
        pen.ellipse_glow((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, max(20.0, (b[2] - b[0]) * 0.75), max(10.0, (b[3] - b[1]) * 1.4), c, 70 * k)


def _dino_sil(p_, x, y, s, kind=0, c='#4aa86a', a=255):
    """A cute dinosaur silhouette (cm frame; s = height cm): 0 long-neck, 1 T-rex, 2 triceratops, 3 stegosaurus."""
    if kind == 0:
        body = union(oval(x, y, s * 0.5, s * 0.28), smooth([(x + s * 0.3, y - s * 0.1), (x + s * 0.5, y - s * 0.7), (x + s * 0.62, y - s * 0.95), (x + s * 0.78, y - s * 0.93),
                                                          (x + s * 0.66, y - s * 0.78), (x + s * 0.5, y - s * 0.05)], True, 0.8))
        body = union(body, poly([(x - s * 0.4, y - s * 0.05), (x - s * 1.0, y + s * 0.12), (x - s * 0.45, y + s * 0.1)]))
        for lx in (-0.3, -0.12, 0.15, 0.32): body = union(body, rect(x + lx * s - s * 0.05, y + s * 0.1, s * 0.1, s * 0.32))
    elif kind == 1:
        body = smooth([(x - s * 0.8, y + s * 0.05), (x - s * 0.2, y - s * 0.35), (x + s * 0.2, y - s * 0.75), (x + s * 0.58, y - s * 0.78), (x + s * 0.62, y - s * 0.55),
                       (x + s * 0.3, y - s * 0.5), (x + s * 0.25, y - s * 0.15), (x + s * 0.1, y + s * 0.15), (x - s * 0.2, y + s * 0.1)], True, 0.7)
        for lx in (-0.12, 0.08): body = union(body, rect(x + lx * s, y + s * 0.05, s * 0.1, s * 0.4))
    elif kind == 2:
        body = union(oval(x, y, s * 0.55, s * 0.3), poly([(x + s * 0.45, y - s * 0.3), (x + s * 0.85, y - s * 0.55), (x + s * 0.9, y + s * 0.05), (x + s * 0.5, y + s * 0.1)]))
        body = union(body, poly([(x + s * 0.8, y - s * 0.2), (x + s * 1.1, y - s * 0.4), (x + s * 0.85, y - s * 0.12)]))
        for lx in (-0.35, -0.15, 0.15, 0.32): body = union(body, rect(x + lx * s - s * 0.06, y + s * 0.12, s * 0.12, s * 0.28))
    else:
        body = union(oval(x, y, s * 0.6, s * 0.3), poly([(x - s * 0.5, y), (x - s * 1.05, y + s * 0.15), (x - s * 0.5, y + s * 0.12)]))
        for k in range(5):
            px = x - s * 0.4 + k * s * 0.2
            body = union(body, poly([(px - s * 0.09, y - s * 0.22), (px, y - s * 0.5 + 0.06 * s * abs(k - 2)), (px + s * 0.09, y - s * 0.22)]))
        for lx in (-0.35, -0.12, 0.15, 0.35): body = union(body, rect(x + lx * s - s * 0.06, y + s * 0.15, s * 0.12, s * 0.28))
    p_.fill(body, c, a)
    p_.fill(oval(x + s * (0.62 if kind == 0 else (0.45 if kind == 1 else (0.8 if kind == 2 else 0.5))), y - s * (0.88 if kind == 0 else (0.68 if kind == 1 else (0.2 if kind == 2 else 0.05))), s * 0.03), '#1a1a1a', a)


def _poster_art(p_, x, y, w, h, kind):
    """Clinic / hospital posters (cm frame): 'dinos' (DINOSAURS!), 'wash' (WASH YOUR HANDS), 'fast' (stroke signs),
    'heart' (the heart diagram), 'chart' (an eye chart), 'diploma', 'drawing' (a kid's crayon drawing), 'breathe'."""
    def fn(q, W, H):
        if kind == 'dinos':
            q.fill(rect(0, 0, W, H), '#fff4d8')
            btext(q, 'DINOSAURS!', W / 2, H * 0.14, 'head', H * 0.1, '#d8582a', 240, 'center')
            for i, (cx_, cy_, k_, c_) in enumerate(((W * 0.3, H * 0.42, 0, '#4aa86a'), (W * 0.72, H * 0.45, 1, '#d8582a'), (W * 0.28, H * 0.8, 2, '#4a8ad8'), (W * 0.7, H * 0.82, 3, '#a85ad8'))):
                _dino_sil(q, cx_, cy_, H * 0.16, k_, c_)
        elif kind == 'wash':
            q.fill(rect(0, 0, W, H), '#e8f4f8')
            btext(q, 'WASH YOUR', W / 2, H * 0.16, 'head', H * 0.1, '#2a6aa8', 240, 'center')
            btext(q, 'HANDS!', W / 2, H * 0.29, 'head', H * 0.12, '#2a6aa8', 240, 'center')
            q.fill(oval(W / 2, H * 0.62, W * 0.26, H * 0.18), '#f4c8a8'); q.line(oval(W / 2, H * 0.62, W * 0.26, H * 0.18), 0.6, '#5a3a2a', 200)
            for k in range(7): q.line(oval(W * (0.3 + 0.07 * k), H * (0.5 + 0.04 * (k % 3)), W * 0.03), 0.5, '#4a9ad8', 220)
        elif kind == 'fast':
            q.fill(rect(0, 0, W, H), '#ffffff')
            q.fill(rect(0, 0, W, H * 0.16), '#c82a2a'); btext(q, 'STROKE? ACT F.A.S.T.', W / 2, H * 0.11, 'sans_b', H * 0.065, '#ffffff', 245, 'center')
            for i, (L, s_) in enumerate((('F', 'Face drooping'), ('A', 'Arm weakness'), ('S', 'Speech'), ('T', 'Time to call'))):
                yy = H * (0.28 + 0.18 * i)
                q.fill(oval(W * 0.16, yy, H * 0.06), '#c82a2a'); btext(q, L, W * 0.16, yy + H * 0.025, 'sans_b', H * 0.07, '#ffffff', 250, 'center')
                btext(q, s_, W * 0.3, yy + H * 0.02, 'sans_b', H * 0.05, '#2a2a2a', 240)
        elif kind == 'heart':
            q.fill(rect(0, 0, W, H), '#f8f2ea')
            btext(q, 'YOUR HEART', W / 2, H * 0.13, 'sans_b', H * 0.08, '#8a2a2a', 240, 'center')
            hh = union(oval(W * 0.42, H * 0.45, W * 0.17, H * 0.14), oval(W * 0.58, H * 0.45, W * 0.17, H * 0.14))
            hh = union(hh, poly([(W * 0.27, H * 0.5), (W * 0.73, H * 0.5), (W * 0.5, H * 0.85)]))
            q.fill(hh, '#d84a4a'); q.line(hh, 0.8, '#6a1a1a', 220)
            q.line(smooth([(W * 0.5, H * 0.3), (W * 0.48, H * 0.2), (W * 0.56, H * 0.15)], False), 2.0, '#4a6ad8', 230)
        elif kind == 'chart':
            q.fill(rect(0, 0, W, H), '#ffffff')
            for i, row in enumerate(('E', 'F P', 'T O Z', 'L P E D', 'P E C F D')):
                btext(q, row, W / 2, H * (0.15 + 0.16 * i), 'sans_b', H * (0.14 - 0.022 * i), '#1a1a1a', 240, 'center')
        elif kind == 'diploma':
            q.fill(rect(0, 0, W, H), '#f8f0dc')
            btext(q, 'Doctor of Medicine', W / 2, H * 0.4, 'formal', H * 0.12, '#2a2a3a', 240, 'center')
            q.fill(oval(W * 0.78, H * 0.78, H * 0.1), '#c8a040')
            for k in range(4): q.seg((W * 0.2, H * (0.55 + 0.08 * k)), (W * 0.65, H * (0.55 + 0.08 * k)), 0.4, '#5a5a5a', 160)
        elif kind == 'breathe':
            q.linear(rect(0, 0, W, H), 0, 0, 0, H, ['#bfe0f0', '#f0e8c8'])
            btext(q, 'Questions are', W / 2, H * 0.4, 'caveat_b', H * 0.13, '#2a4a6a', 240, 'center')
            btext(q, 'welcome here', W / 2, H * 0.58, 'caveat_b', H * 0.13, '#2a4a6a', 240, 'center')
            q.fill(oval(W * 0.5, H * 0.8, H * 0.06), '#f2c84a')
        else:                                                                           # a kid's crayon drawing
            q.fill(rect(0, 0, W, H), '#fbf8ee')
            _dino_sil(q, W * 0.45, H * 0.6, H * 0.35, (int(x) % 4), ['#4aa86a', '#d8582a', '#4a8ad8', '#a85ad8'][int(y) % 4], 200)
            q.fill(oval(W * 0.85, H * 0.18, H * 0.1), '#f2c84a')
            btext(q, 'THANK YOU', W / 2, H * 0.12, 'kid', H * 0.1, '#c83a3a', 220, 'center')
    _hframe(p_, 0, 0, x, y, w, h, 'poster', frame='#e8e4dc' if kind not in ('diploma', 'heart') else '#5a3a24', fn=fn)


def _stickers(p_, x0, y0, w, h, n=8, seed=0):
    """Dinosaur stickers scattered on a surface (cm frame)."""
    rng = np.random.default_rng(seed)
    for i in range(n):
        x, y = x0 + rng.uniform(0, w), y0 + rng.uniform(0, h)
        s = rng.uniform(3.0, 5.0)
        p_.fill(oval(x, y, s * 0.8), '#ffffff', 230)
        _dino_sil(p_, x - s * 0.15, y + s * 0.1, s * 0.6, int(rng.integers(0, 4)), ['#4aa86a', '#d8582a', '#4a8ad8', '#a85ad8', '#e8b83a'][i % 5])


# ---------------------------------------------------------------------------------------------- props for the doctors' world
def dr_exam_table(pen, v, B):
    """The pediatric exam table: a cream padded top with the paper roll pulled over it, a pull-out step, drawers in the
    base covered in dinosaur stickers."""
    w2, d2 = B.w / 2, B.d / 2

    def base_front(p_, W, H):
        p_.fill(rect(0, 0, W, H), '#e8eef2')
        for k in range(3):
            r = rect(4 + k * (W - 8) / 3, 6, (W - 8) / 3 - 4, H * 0.5)
            p_.line(r, 0.8, '#7a8a94', 200); p_.fill(rrect(4 + k * (W - 8) / 3 + (W - 8) / 6 - 6, 10, 12, 2.2, 1), '#a8b0b8')
        _stickers(p_, 6, 8, W - 12, H * 0.5, 9, 4)
    base = Box(B.cx, B.cy, B.w, B.d, 0.0, 0.62, B.fa)
    draw_box(pen, v, base, {'front': dict(fill='#e8eef2', art=base_front), 'all': '#d0d8de', 'top': '#c8d0d6'})
    top = Box(B.cx, B.cy, B.w, B.d + 0.02, 0.62, 0.8, B.fa)
    draw_box(pen, v, top, {'all': '#5a8aa8', 'top': dict(fill='#6a9ab8', art=lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'fabric', 0.5, 'overlay', 0.6))})
    paper = Box(B.cx, B.cy, B.w - 0.02, B.d * 0.62, 0.8, 0.806, B.fa)
    draw_box(pen, v, paper, {'all': '#f8f8f4', 'top': dict(fill='#fbfbf8', art=lambda p_, W, H: [p_.seg((0, k * 9), (W, k * 9), 0.3, '#c8c8c0', 120) for k in range(int(H / 9))])})
    head = Box(*B.at(-w2 + 0.22, 0, 0)[0::2], 0.44, B.d, 0.8, 0.95, B.fa)
    draw_box(pen, v, head, {'all': '#5a8aa8', 'top': '#6a9ab8'})
    step = Box(*B.at(0.1, d2 + 0.18, 0)[0::2], 0.6, 0.3, 0.0, 0.28, B.fa)
    draw_box(pen, v, step, {'all': '#d0d8de', 'top': '#8a9aa4'})


def dr_stool(pen, v, x, y, seat=0.55, c='#3a3a40'):
    """A doctor's rolling stool: five castor legs, a gas column, a round black seat."""
    if v.d(x, y) < 0.3: return
    s = v.s(x, y)
    for k in range(5):
        a = 2 * math.pi * k / 5
        pen.seg(v.p(x, 0.08, y), v.p(x + math.cos(a) * 0.28, 0.04, y + math.sin(a) * 0.28), max(1.5, 0.025 * s), '#2a2a2e')
        q = v.p(x + math.cos(a) * 0.28, 0.02, y + math.sin(a) * 0.28); pen.fill(oval(q[0], q[1], max(1.5, 0.02 * s)), '#1a1a1c')
    pen.seg(v.p(x, 0.08, y), v.p(x, seat - 0.06, y), max(2.0, 0.035 * s) + 2, LINE); pen.seg(v.p(x, 0.08, y), v.p(x, seat - 0.06, y), max(1.5, 0.035 * s), '#a8acb0')
    pen.fill(ellipse3(v, x, y, 0.2, 0.2, seat - 0.06), lit(_darken(c, 0.3), (x, seat, y), None))
    tp = ellipse3(v, x, y, 0.2, 0.2, seat)
    pen.fill(tp, lit(c, (x, seat, y), (0, 1, 0))); pen.line(tp, 1.0)


def dr_office_chair(pen, v, x, y, fa=0, c='#2a2c34'):
    """A rolling office chair (fa: 0 = the sitter faces -y)."""
    if v.d(x, y) < 0.3: return
    B = Box(x, y, 0.5, 0.48, 0.0, 0.5, fa)
    dr_stool(pen, v, x, y, 0.42, c)
    seat = sub(B, -0.24, 0.24, -0.22, 0.22, 0.42, 0.5)
    draw_box(pen, v, seat, {'all': _darken(c, 0.1), 'top': c})
    back = sub(B, -0.22, 0.22, -0.27, -0.2, 0.56, 1.05)
    draw_box(pen, v, back, {'all': c})


def dr_monitor(pen, v, x, Y, y, fa=0, k=1.0, kind='chart', w=0.52, h=0.32):
    """A flat computer monitor on its stand at (x, Y, y), screen facing direction fa (Box convention); kind 'chart' (a
    patient chart), 'results' (a list of lab results), 'off'."""
    B = Box(x, y, w, 0.04, Y + 0.1, Y + 0.1 + h, fa)

    def front(p_, W, H):
        p_.fill(rect(0, 0, W, H), '#16181c')
        if kind != 'off':
            p_.fill(rect(2, 2, W - 4, H - 4), mix('#20262e', '#e8eef4', k))
            p_.fill(rect(2, 2, W - 4, 4), mix('#20262e', '#3a6aa8', k))
            for i in range(9):
                yy = 9 + i * (H - 12) / 9
                p_.fill(rect(4, yy, (W - 10) * (0.4 + 0.5 * ((i * 7) % 5) / 5), 1.4), mix('#20262e', '#5a6a7a', k))
                if kind == 'results' and i % 3 == 1: p_.fill(rect(W - 14, yy - 0.2, 9, 1.8), mix('#20262e', '#d84a3a', k))
    draw_box(pen, v, B, {'front': dict(fill='#16181c', art=front), 'all': '#1e2024'})
    sb = Box(x, y, 0.06, 0.06, Y, Y + 0.12, fa)
    draw_box(pen, v, sb, {'all': '#2a2c30'})
    draw_box(pen, v, Box(x, y, 0.22, 0.16, Y, Y + 0.015, fa), {'all': '#2a2c30'})


def dr_monitor_glow(pen, v, x, Y, y, k=1.0, w=0.52, h=0.32, c='#cfe0f4'):
    if k <= 0.01 or v.d(x, y) < 0.3: return
    gx, gy = v.p(x, Y + 0.1 + h / 2, y)
    pen.glow(gx, gy, 0.7 * v.s(x, y), c, 50 * k)


def dr_papers(pen, v, x, Y, y, n=8, c='#f4f4ee', seed=0, folders=True, ang=0.0):
    """A stack of lab results / folders on a desk at (x, Y, y)."""
    if v.d(x, y) < 0.2: return
    rng = np.random.default_rng(seed)
    hh = 0.0
    for i in range(n):
        th = 0.008 if not folders else 0.012
        a = math.radians(ang + rng.uniform(-8, 8))
        dx, dy = rng.uniform(-0.01, 0.01), rng.uniform(-0.01, 0.01)
        q = []
        for (u, w) in ((-0.15, -0.11), (0.15, -0.11), (0.15, 0.11), (-0.15, 0.11)):
            q.append((x + dx + u * math.cos(a) - w * math.sin(a), Y + hh + th, y + dy + u * math.sin(a) + w * math.cos(a)))
        path = v.poly3(q)
        if path.isEmpty(): continue
        cc = c if not folders or i % 2 else ['#e8c86a', '#8ab0d8', '#d88a8a', '#a8d0a0'][i % 4]
        pen.fill(path, lit(cc, (x, Y + hh, y), (0, 1, 0))); pen.line(path, 0.7)
        hh += th


def dr_desk_phone(pen, v, x, Y, y):
    """A hospital desk phone with its keypad and the handset in its cradle."""
    B = Box(x, y, 0.22, 0.2, Y, Y + 0.06, 0)
    draw_box(pen, v, B, {'all': '#2a2c30', 'top': dict(fill='#3a3c42', art=lambda p_, W, H: [p_.fill(rect(W * 0.55 + (k % 3) * 2.6, H * 0.25 + (k // 3) * 2.6, 2.0, 1.8), '#8a8c92') for k in range(12)])})
    hs = Box(x - 0.05, y, 0.06, 0.2, Y + 0.06, Y + 0.1, 0)
    draw_box(pen, v, hs, {'all': '#2a2c30', 'top': '#34363c'})


def dr_mug(pen, v, x, Y, y, c='#d84a3a', steam=0.0, t=0.0):
    if v.d(x, y) < 0.2: return
    s = v.s(x, y)
    top = ellipse3(v, x, y, 0.045, 0.045, Y + 0.1)
    b = _rb(top); bx, by = v.p(x, Y, y)
    body = union(top, poly([(b[0], (b[1] + b[3]) / 2), (b[2], (b[1] + b[3]) / 2), (bx + 0.045 * s, by), (bx - 0.045 * s, by)]))
    pen.fill(body, lit(c, (x, Y + 0.05, y), None)); pen.line(body, 0.9)
    pen.fill(ellipse3(v, x, y, 0.038, 0.038, Y + 0.098), '#3a2010')
    hx, hy = v.p(x + 0.055, Y + 0.05, y)
    pen.line(oval(hx, hy, 0.015 * s, 0.025 * s), max(1.0, 0.01 * s), lit(c, (x, Y, y), None))
    if steam > 0.01:
        for j in range(2):
            pts = [(bx + (j - 0.5) * 0.02 * s + 0.012 * s * math.sin(t * 1.6 + q * 0.9 + j * 2), by - (0.13 + q * 0.035) * s) for q in range(7)]
            pen.line(smooth(pts, False, 0.8), max(1.0, 0.006 * s), '#ffffff', 60 * steam)


def dr_desk_lamp(pen, v, x, Y, y, k=1.0, c='#2a5a6a'):
    """An adjustable desk lamp (k = on)."""
    if v.d(x, y) < 0.2: return
    s = v.s(x, y)
    p0, p1, p2 = v.p(x, Y, y), v.p(x - 0.05, Y + 0.32, y + 0.04), v.p(x + 0.12, Y + 0.45, y - 0.02)
    pen.fill(ellipse3(v, x, y, 0.07, 0.07, Y + 0.005), lit(c, (x, Y, y), (0, 1, 0)))
    pen.line(poly([p0, p1, p2], False), max(1.5, 0.012 * s) + 1.5, LINE); pen.line(poly([p0, p1, p2], False), max(1.2, 0.012 * s), lit('#a8acb0', (x, Y + 0.3, y), None))
    hd = poly([(p2[0] - 0.04 * s, p2[1] - 0.03 * s), (p2[0] + 0.05 * s, p2[1] - 0.04 * s), (p2[0] + 0.08 * s, p2[1] + 0.05 * s), (p2[0] - 0.06 * s, p2[1] + 0.06 * s)])
    pen.fill(hd, lit(c, (x + 0.12, Y + 0.45, y), None)); pen.line(hd, 1.0)
    if k > 0.01:
        pen.fill(oval(p2[0] + 0.01 * s, p2[1] + 0.055 * s, 0.065 * s, 0.015 * s), '#fff6e0', 230 * k)
        pen.glow(p2[0], p2[1] + 0.07 * s, 0.4 * s, '#ffe0b0', 90 * k)


def dr_white_coat_hook(pen, v, x, Y, y, fa_dir=(1, 0)):
    """A white coat hanging on a wall hook (the narrator's office / Halverson's office)."""
    if v.d(x, y) < 0.3: return
    s = v.s(x, y)
    top = v.p(x, Y, y); bot = v.p(x + fa_dir[0] * 0.05, Y - 1.05, y + fa_dir[1] * 0.05)
    coat = smooth([(top[0] - 0.06 * s, top[1]), (top[0] + 0.06 * s, top[1]), (bot[0] + 0.24 * s, bot[1]), (bot[0] - 0.24 * s, bot[1])], True, 0.5)
    pen.fill(coat, lit('#f4f4f0', (x, Y - 0.5, y), None)); pen.line(coat, 1.0)
    pen.linear(coat, bot[0] - 0.24 * s, 0, bot[0] + 0.24 * s, 0, [(0, '#000000', 50), (0.5, '#000000', 0), (1, '#000000', 60)])
    pen.seg((top[0], top[1] + 0.05 * s), (bot[0], bot[1]), max(0.6, 0.004 * s), '#c8c8c0')
    pen.fill(rect(bot[0] + 0.06 * s, top[1] + 0.32 * s, 0.1 * s, 0.07 * s), lit('#e8e8e4', (x, Y - 0.35, y), None))
    pen.fill(rect(bot[0] + 0.08 * s, top[1] + 0.3 * s, 0.012 * s, 0.05 * s), '#2a4a8a'); pen.fill(rect(bot[0] + 0.1 * s, top[1] + 0.3 * s, 0.012 * s, 0.05 * s), '#c82a2a')


def dr_plant(pen, v, x, y, Y=0.0, h=0.9, c='#3a7a4a'):
    if v.d(x, y) < 0.3: return
    s = v.s(x, y)
    px, py = v.p(x, Y, y)
    pot = poly([(px - 0.15 * s, py - 0.32 * s), (px + 0.15 * s, py - 0.32 * s), (px + 0.11 * s, py), (px - 0.11 * s, py)])
    pen.fill(pot, lit('#c86a4a', (x, Y + 0.2, y), None)); pen.line(pot, 1.0)
    for k in range(11):
        a = -math.pi / 2 + (k - 5) * 0.24
        L_ = (h * 0.7 + h * 0.3 * _h(k, 5)) * s
        tip = (px + math.cos(a) * L_ * 0.6, py - 0.32 * s + math.sin(a) * L_)
        lf = smooth([(px, py - 0.32 * s), ((px + tip[0]) / 2 - 0.05 * s, (py - 0.32 * s + tip[1]) / 2), tip, ((px + tip[0]) / 2 + 0.05 * s, (py - 0.32 * s + tip[1]) / 2)], True, 0.9)
        pen.fill(lf, lit(c if k % 3 else _lighten(c, 0.15), (x, Y + 0.6, y), None)); pen.line(lf, 0.8)


# ---------------------------------------------------------------------------------------------- Doctor Halverson's clinic (day)
C_R = (0.0, 3.8, 0.0, 3.4)
C_TABLE = Box(3.32, 1.85, 1.8, 0.7, 0.0, 0.8, -90)            # along the east wall, its long side facing the room (-x)
C_STOOL = (2.35, 1.55)
C_CHAIR = (0.5, 2.15)


def _clinic_cfg():
    def lights(o):
        win = Lamp(kind='win', c='#fff4e0', k=1.2, soft=16.0, panes=_panes_y(1.6, 2.8, 0.9, 2.0, 3.4), d=_norm3((-0.2, -0.45, -1.0)))
        panels = [Lamp(1.3, 2.55, 1.7, 5.5, '#fff6ea', 0.72, (1.0, 0.7, 0.4), fall=1.3), Lamp(2.8, 2.55, 1.7, 5.5, '#fff6ea', 0.72, (1.0, 0.7, 0.4), fall=1.3)]
        return '#948c84', [win] + panels, []

    def art(o):
        def frieze(p_, W, H):
            p_.fill(rect(0, H - 190, W, 16), '#f4e8c8'); p_.fill(rect(0, H - 190, W, 1.2), '#c8a870'); p_.fill(rect(0, H - 175, W, 1.2), '#c8a870')
            for k in range(int(W / 30)):
                _dino_sil(p_, 15 + k * 30, H - 181, 8, k % 4, ['#4aa86a', '#e8783a', '#4a8ad8', '#a85ad8'][k % 4], 230)
        def west(p_, W, H):
            frieze(p_, W, H)
            p_.fill(rect(70, H - 160, 22, 150), '#fff8e8'); p_.line(rect(70, H - 160, 22, 150), 0.6, '#c8a870', 200)       # the height chart
            for k in range(16):
                p_.seg((70, H - 10 - k * 10), (76 + (4 if k % 2 == 0 else 0), H - 10 - k * 10), 0.6, '#5a4a3a', 220)
            _dino_sil(p_, 88, H - 168, 16, 0, '#4aa86a')
            _poster_art(p_, 140, H - 180, 50, 66, 'wash')
            _poster_art(p_, 230, H - 190, 70, 52, 'breathe')
        def back(p_, W, H):
            frieze(p_, W, H)
            _poster_art(p_, 20, H - 175, 56, 72, 'dinos')
            for i in range(3): _poster_art(p_, 300 + i * 26, H - 160 + (i % 2) * 8, 22, 18, 'drawing')
        def front(p_, W, H):
            frieze(p_, W, H)
            _poster_art(p_, 40, H - 175, 36, 50, 'chart')
            _light_switch(p_, 3.8 * 100 - 140, H - 120)
        def east(p_, W, H):
            frieze(p_, W, H)
            for i in range(4): _poster_art(p_, 60 + i * 50, H - 158 - (i % 2) * 6, 34, 26, 'drawing')
        return {'west': west, 'back': back, 'front': front, 'east': east}

    def pieces(o):
        P = [Piece('exam_table', (C_TABLE.cx, 0.5, C_TABLE.cy), lambda pen, v: dr_exam_table(pen, v, C_TABLE), block=C_TABLE.footprint()),
             Piece('stool', (C_STOOL[0], 0.3, C_STOOL[1]), lambda pen, v: dr_stool(pen, v, C_STOOL[0], C_STOOL[1]), block=_circ(C_STOOL[0], C_STOOL[1], 0.25)),
             Piece('chair', (C_CHAIR[0], 0.4, C_CHAIR[1]), lambda pen, v: _kchair(pen, v, C_CHAIR[0], C_CHAIR[1], 90), block=_circ(C_CHAIR[0], C_CHAIR[1], 0.25))]

        def counter(pen, v):
            B = Box(0.85, 3.1, 1.5, 0.6, 0.0, 0.9, 0)
            draw_box(pen, v, B, {'front': dict(fill='#f0e8d8', art=lambda p_, W, H: (_chrome_pulls(p_, W, H, 3, 12), _stickers(p_, 4, 18, W - 8, H - 30, 7, 2))),
                                 'all': '#d8d0c0', 'top': '#e8dcc0'})
            for (dx, c_) in ((-0.5, '#f2f2ee'), (-0.35, '#c8e0f0'), (0.45, '#f2f2ee')):
                Px = (0.85 + dx, 0.9, 3.15)
                if v.d(Px[0], Px[2]) > 0.3:
                    s = v.s(Px[0], Px[2]); px_, py_ = v.p(*Px)
                    jar = rrect(px_ - 0.05 * s, py_ - 0.16 * s, 0.1 * s, 0.16 * s, 0.015 * s)
                    pen.fill(jar, lit(c_, (Px[0], 1.0, Px[2]), None)); pen.line(jar, 0.8)
            fx_, fy_ = v.p(1.2, 0.9, 3.3); s = v.s(1.2, 3.3)
            pen.line(smooth([(fx_, fy_), v.p(1.2, 1.18, 3.3), v.p(1.2, 1.15, 3.12)], False), max(1.5, 0.02 * s), '#c8ccd2')
            UB = Box(0.85, 3.22, 1.5, 0.35, 1.5, 2.2, 0)
            draw_box(pen, v, UB, {'front': dict(fill='#f0e8d8', art=lambda p_, W, H: (_chrome_pulls(p_, W, H, 3, H - 8), _stickers(p_, 4, 6, W - 8, H - 14, 5, 7))),
                                  'all': '#d8d0c0', 'bottom': '#c8c0b0'})
        P.append(Piece('counter', (0.85, 0.5, 3.1), counter, block=_box_pts(0.85, 3.1, 0.75, 0.3)))

        def desk(pen, v):
            B = Box(2.7, 0.3, 1.0, 0.5, 0.0, 0.76, 180)
            draw_parts(pen, v, table_parts(B, '#d8c8a8', apron=0.05, legw=0.04))
            dr_monitor(pen, v, 2.7, 0.76, 0.22, 180, 1.0, 'chart')
            dr_mug(pen, v, 3.05, 0.76, 0.35, '#4a8ad8')
            dr_papers(pen, v, 2.35, 0.76, 0.35, 4, seed=3)
        P.append(Piece('desk', (2.7, 0.4, 0.3), desk, block=_box_pts(2.7, 0.3, 0.5, 0.25)))
        P.append(Piece('plant', (0.3, 0.4, 0.35), lambda pen, v: dr_plant(pen, v, 0.3, 0.35)))
        return P

    def glows(v, o):
        return [('panels', (2.0, 2.6, 1.7), lambda pen, t: [_ceiling_panel_light(pen, v, x, 1.7, 2.6, 1.0) for x in (1.3, 2.8)]),
                ('monitor_glow', (2.7, 1.0, 0.22), lambda pen, t: dr_monitor_glow(pen, v, 2.7, 0.76, 0.22, 0.8))]

    def spots(v, o):
        S = {}
        tc = C_TABLE.at(0.15, C_TABLE.d / 2 - 0.08, 0)
        S['exam_table'] = _mk_spot(v, 'exam_table', tc[0], tc[2], 0.0, 'seat', 'Milo sitting on the exam table edge, legs dangling (perch: seat 0.81 m; faces -x)',
                                   face=(-1, 0), seat_Y=0.81, perch=True)
        S['table_lie'] = _mk_spot(v, 'table_lie', C_TABLE.cx + 0.05, C_TABLE.cy, 0.81, 'lie', 'lying on the exam table (head north: +y)')
        S['stool'] = _mk_spot(v, 'stool', C_STOOL[0], C_STOOL[1], 0.0, 'seat', "Halverson on her rolling stool, facing Milo (+x)", face=(1, 0.25), seat_Y=0.55)
        S['parent_chair'] = _mk_spot(v, 'parent_chair', C_CHAIR[0], C_CHAIR[1], 0.0, 'seat', 'Mom on the chair by the west wall (faces +x)', face=(1, 0), seat_Y=0.46)
        S['stand_table'] = _mk_spot(v, 'stand_table', 2.45, 2.1, 0.0, 'stand', 'standing at the table (Halverson taking blood)', face=(1, 0))
        S['counter_top'] = _mk_spot(v, 'counter_top', 0.85, 3.05, 0.9, 'surface', 'the counter by the sink (vials, cotton)')
        S['door'] = _mk_spot(v, 'door', 0.85, 0.45, 0.0, 'stand', 'just inside the door', face=(0, 1))
        S['desk_top'] = _mk_spot(v, 'desk_top', 2.6, 0.32, 0.76, 'surface', 'her desk by the door (the chart on the screen)')
        return S
    return dict(name='clinic', R=C_R, H=2.6, floor=dict(base='#e8e2d4', kind='checker', ink='#d4c8b0', scale=1.0),
                walls=dict(paper='#f2ead8', ink='#e8d8b8', kind='ditsy', wains=0.9, wcol='#bfe0d8', trim='#f8f4ea', pa=60, seed=31),
                holes={'front': [(0.4, 0.0, 1.3, 0.0, 0.0, 2.1)]}, windows=[('back', (1.6, 3.4, 2.8, 3.4, 0.9, 2.0), (2, 1), '#f8f8f4')],
                art=art, ceil=dict(c='#f4f2ec', art=lambda p_, W, H: pat(p_, W, H, 'tile', '#d8d8d0', 200, scale=4.0)),
                lights=lights, pieces=pieces, glows=glows, spots=spots,
                shell_x=lambda pen, v, o: _blinds(pen, v, 1.6, 2.8, 2.0, 0.9, 3.36, 0.3))


_dcam('dr_clinic_wide', 760, 480, 1.55, 0.35, 0.45, 52, _env(), "Halverson's exam room from the door: Milo on the table (3/4), her stool, Mom's chair, the dinosaur frieze", 'clinic')
_dcam('dr_clinic_table', 1000, 500, 1.3, 1.25, 2.85, 118, _env(), 'medium on the exam table: Milo perched, Halverson on her stool ("her smile went careful")', 'clinic')
_dcam('dr_clinic_door', 820, 480, 1.5, 3.0, 3.05, -140, _env(), 'reverse: from the table end toward the door and her desk', 'clinic')


def _outside_day(pen, v):
    """Daylight outside a clinic window: a soft sky, a parking lot's trees, spring green."""
    pen.linear(rect(-800, -600, 3600, 2400), 0, v.h - 1.0 * v.S, 0, v.h + 40, [(0, '#8ab4dc'), (0.7, '#c8dcec'), (1, '#eef2f0')])
    vg = lifted(v, -3.0)
    ground(pen, vg, 8.0, 90.0, -40.0, 60.0, tod='day87', c='#7a9a6a')
    for i, x in enumerate(np.arange(-12.0, 16.0, 3.8)):
        y = 16.0 + 3 * _h(i, 3)
        if vg.d(x, y) < 1: continue
        bx, by = vg.p(x, 0.0, y)
        pen.fill(oval(bx, by - 3.2 * vg.s(x, y), 2.2 * vg.s(x, y), 2.0 * vg.s(x, y)), '#6a9a5a')
        pen.seg((bx, by), (bx, by - 2.0 * vg.s(x, y)), max(1.0, 0.25 * vg.s(x, y)), '#5a4a3a')


def dr_clinic(view='wide', **kw):
    """Doctor Halverson's pediatric exam room (day, bright and warm): view 'wide' | 'table' | 'door'."""
    return _box_build(_clinic_cfg(), 'dr_clinic_' + view, dict(kw), outside=_outside_day, grade='dr_clinic')


# ---------------------------------------------------------------------------------------------- the 3 AM offices (Halverson's, the narrator's)
O_R = (0.0, 3.0, 0.0, 3.4)
O_DESK = Box(1.5, 2.15, 1.5, 0.75, 0.0, 0.75, 0)              # the desk faces the door (-y); the sitter is behind it
O_CHAIR = (1.5, 2.85)


def _office_cfg(owner='halverson', door_ang=35.0):
    narr = owner == 'narrator'

    def lights(o):
        amb = '#262a40'
        lot = Lamp(kind='win', c=D_SODIUM, k=0.45, soft=14.0, panes=_panes_x(1.2, 2.6, 0.9, 2.0, 3.0), d=_norm3((-1.0, -0.4, 0.1)))
        lamp_ = [Lamp(O_DESK.cx + 0.5, 1.3, O_DESK.cy, 3.4, '#ffd8a0', 1.0, (1.0, 0.7, 0.6), fall=1.6)]
        mon = [Lamp(O_DESK.cx - 0.25, 1.0, O_DESK.cy - 0.1, 2.4, '#bcd0f0', 0.7, fall=1.5)]
        ceil_ = [Lamp(1.5, 2.5, 1.7, 5.0, '#fff4e4', 1.2, (1.0, 0.6, 0.3), fall=1.3)]
        hall = [Lamp(0.75, 1.5, -0.4, 3.0, '#d8e8d0', 0.4, fall=1.5)]
        return amb, [lot], [('lamp', lamp_, _kfn(o.get('lamp', 1.0), 261)), ('monitor', mon, _kfn(o.get('monitor', 1.0), 262)),
                            ('ceiling', ceil_, _kfn(o.get('ceiling', 0.0), 263)), ('hall', hall, _kfn(o.get('hall', 0.3), 264))]

    def art(o):
        def back(p_, W, H):
            _poster_art(p_, 30, H - 200, 44, 34, 'diploma')
            if narr:
                _photo(p_, W, H, 90, H - 196, 40, 30, 'milo', frame='#2a2a2a')            # Milo, 22, at a finish line
                _poster_art(p_, 150, H - 196, 46, 36, 'breathe')
            else:
                for i in range(4): _poster_art(p_, 90 + i * 30, H - 188 + (i % 2) * 8, 24, 20, 'drawing')
            p_.fill(rect(220, H - 175, 60, 42), '#f4f4f0'); p_.line(rect(220, H - 175, 60, 42), 0.8, '#8a8a8a')      # whiteboard
            for k in range(4): p_.seg((225, H - 168 + k * 8), (265 - k * 4, H - 168 + k * 8), 0.6, ['#2a4a9a', '#c82a2a', '#2a8a4a', '#2a4a9a'][k], 200)
        def west(p_, W, H):
            _poster_art(p_, 120, H - 190, 46, 60, 'wash' if not narr else 'dinos')
            p_.fill(rect(200, H - 175, 70, 50), '#c8a070'); p_.line(rect(200, H - 175, 70, 50), 0.8, '#5a3a20')      # cork board
            for k in range(5): p_.fill(rect(205 + (k % 3) * 21, H - 170 + (k // 3) * 22, 17, 18), ['#fff8e0', '#e8f0ff', '#ffe8e8'][k % 3])
        def front(p_, W, H):
            _office_clock(p_, 230, H - 220, 14, 3, 2)
            _light_switch(p_, (3.0 - 1.35) * 100, H - 120)
        return {'back': back, 'west': west, 'front': front}

    def pieces(o):
        stack = o.get('stack', 1.0)

        def desk(pen, v):
            draw_parts(pen, v, table_parts(O_DESK, '#8a6a4a', apron=0.12, legw=0.05))
            Y = O_DESK.Y1
            dr_monitor(pen, v, O_DESK.cx - 0.25, Y, O_DESK.cy + 0.15, 180, 1.0, 'results')
            dr_desk_lamp(pen, v, O_DESK.cx + 0.55, Y, O_DESK.cy + 0.2, 0.0)
            if stack: dr_papers(pen, v, O_DESK.cx + 0.3, Y, O_DESK.cy - 0.05, int(12 * stack), seed=5)
            dr_desk_phone(pen, v, O_DESK.cx - 0.6, Y, O_DESK.cy - 0.1)
            dr_mug(pen, v, O_DESK.cx + 0.05, Y, O_DESK.cy - 0.22, '#f2f2ee' if narr else '#3a6aa8')
            dr_mug(pen, v, O_DESK.cx - 0.05, Y, O_DESK.cy + 0.05, '#d8a83a')
            P = (O_DESK.cx + 0.6, Y, O_DESK.cy - 0.25)                          # a little plastic T-rex
            if v.d(P[0], P[2]) > 0.2:
                s = v.s(P[0], P[2]); px, py = v.p(*P)
                pen.cv.save(); pen.cv.translate(px, py); pen.cv.scale(0.008 * s, 0.008 * s)
                _dino_sil(pen, 0, -8, 10, 1, '#4aa86a'); pen.cv.restore()
        P = [Piece('desk', (O_DESK.cx, 0.4, O_DESK.cy), desk, block=O_DESK.footprint()),
             Piece('chair', (O_CHAIR[0], 0.45, O_CHAIR[1]), lambda pen, v: dr_office_chair(pen, v, O_CHAIR[0], O_CHAIR[1], 180), block=_circ(O_CHAIR[0], O_CHAIR[1], 0.3)),
             Piece('file_cab', (0.3, 0.6, 2.9), lambda pen, v: draw_box(pen, v, Box(0.3, 2.95, 0.5, 0.6, 0.0, 1.3, 90),
                                                                         {'front': dict(fill='#9aa0a8', art=lambda p_, W, H: [p_.fill(rrect(W / 2 - 8, 12 + k * H / 4, 16, 2.5, 1), '#d8dce0') for k in range(4)]),
                                                                          'all': '#8a9098'}), block=_box_pts(0.3, 2.95, 0.3, 0.25)),
             Piece('coat', (0.12, 1.4, 1.6), lambda pen, v: dr_white_coat_hook(pen, v, 0.06, 1.85, 1.6)),
             Piece('plant', (2.75, 0.4, 0.35), lambda pen, v: dr_plant(pen, v, 2.75, 0.35, 0.0, 0.7, '#5a7a4a'))]
        if not callable(o.get('door', door_ang)):
            D = Door((1.2, -0.02), 0.9, 2.03, (-1.0, 0.0), 1, 0.0, art_a=_hosp_door_art(), art_b=_hosp_door_art(), col='#d8d4c8')
            P.append(Piece('door', (0.9, 1.0, 0.2), lambda pen, v, D=D: D.draw(pen, v, o.get('door', door_ang))))
        return P

    def glows(v, o):
        kl = _kfn(o.get('lamp', 1.0), 261); km = _kfn(o.get('monitor', 1.0), 262)
        return [('desk_glow', (O_DESK.cx, 1.0, O_DESK.cy), lambda pen, t: (dr_desk_lamp(pen, v, O_DESK.cx + 0.55, O_DESK.Y1, O_DESK.cy + 0.2, kl(t)),
                                                                           dr_monitor_glow(pen, v, O_DESK.cx - 0.25, O_DESK.Y1, O_DESK.cy + 0.15, km(t))))]

    def spots(v, o):
        S = {}
        S['desk_chair'] = _mk_spot(v, 'desk_chair', O_CHAIR[0], O_CHAIR[1] - 0.05, 0.0, 'seat', 'at the desk, facing the door (-y)', face=(0, -1), seat_Y=0.48)
        S['desk_top'] = _mk_spot(v, 'desk_top', O_DESK.cx, O_DESK.cy - 0.1, O_DESK.Y1, 'surface', 'the desk top')
        S['results'] = _mk_spot(v, 'results', O_DESK.cx + 0.3, O_DESK.cy - 0.05, O_DESK.Y1 + 0.1, 'surface', 'the stack of test results that came back late')
        S['phone'] = _mk_spot(v, 'phone', O_DESK.cx - 0.6, O_DESK.cy - 0.1, O_DESK.Y1 + 0.08, 'point', 'the desk phone (handset)')
        S['door'] = _mk_spot(v, 'door', 0.75, 0.4, 0.0, 'stand', 'in the doorway', face=(0, 1))
        S['window'] = _mk_spot(v, 'window', 2.6, 1.9, 0.0, 'stand', 'at the window (rain, the parking lot)', face=(1, 0))
        return S
    return dict(name='office', R=O_R, H=2.6, floor=dict(base='#9aa098', kind='tile', ink='#7a8078', scale=2.0),
                walls=dict(paper='#d8dcd0' if not narr else '#d4dce0', wains=0.0, trim='#b8c0b8', base_h=0.1, seed=33),
                holes={'front': [(0.3, 0.0, 1.2, 0.0, 0.0, 2.05)]}, windows=[('east', (3.0, 1.2, 3.0, 2.6, 0.9, 2.0), (2, 1), '#e8ece6')],
                art=art, ceil=dict(c='#e8e8e2', art=lambda p_, W, H: pat(p_, W, H, 'tile', '#c8ccc4', 200, scale=4.0)),
                lights=lights, pieces=pieces, glows=glows, spots=spots,
                shell_x=lambda pen, v, o: _blinds(pen, v, 1.2, 2.6, 2.0, 0.9, 2.96, 0.25) if False else None)


_dcam('dr_office_desk', 980, 500, 1.35, 0.45, 0.75, 32, _env(), 'the doctor at the desk at 3/4 (lamp, screen, the stack of results, the phone)', 'office')
_dcam('dr_office_wide', 760, 480, 1.55, 0.7, 0.3, 22, _env(), 'the little office from the door', 'office')
_dcam('dr_office_door', 820, 480, 1.45, 2.2, 3.05, -150, _env(), 'from behind the desk to the door ajar on the dark hallway', 'office')


def _outside_lot(pen, v, tod='night'):
    """The hospital parking lot at night through the office window: sodium lamps, wet cars, rain."""
    dr_sky(pen, v, 'night')
    with lighting('#2a3050', [Lamp(kind='dir', c='#8a9ad8', k=0.3, d=_norm3((0.3, -0.8, 0.5)))]):
        F = floor_face(-60, 60, -60, 60, -6.0)
        draw_face(pen, v, F, lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'asphalt', 0.6, 'overlay', 3.0), '#1e2026', ao=False, line=False)
    vg = lifted(v, -6.0)
    for i, (x, y) in enumerate(((12, 4), (12, 18), (24, 10), (24, 26), (36, 6))):
        if vg.d(x, y) < 1: continue
        dr_streetlight(pen, vg, x, y, 1.0, h=7.0, G=0.0)
        hx, hy = vg.p(x, 7.0, y - 1.6); pen.glow(hx, hy, 1.4 * vg.s(x, y), D_SODIUM, 120)


def dr_office(view='desk', owner='halverson', lamp=1.0, monitor=1.0, ceiling=0.0, stack=1.0, door=35.0, rain=True, **kw):
    """A small hospital office at 3 AM (owner 'halverson': her office when she calls; 'narrator': the narrator's, years
    later: Milo's photo, 'Questions are welcome here'). view 'desk' | 'wide' | 'door'. door = angle of the door (open onto
    the dark hall), stack 0..1 = the pile of late results."""
    o = dict(lamp=lamp, monitor=monitor, ceiling=ceiling, stack=stack, door=door, owner=owner)
    wins = [_win_glass_quads(((3.0, 3.4), (3.0, 0.0)), 3.4 - 2.6, 3.4 - 1.2, 0.9, 2.0)]
    return _box_build(_office_cfg(owner, door), 'dr_office_' + view, o, outside=_outside_lot, grade='dr_office', wins=wins, rain=rain)


# ---------------------------------------------------------------------------------------------- Larkfield General: the ER bay
E_R = (0.0, 3.2, 0.0, 3.6)
E_BED = Box(1.55, 2.2, 0.95, 2.05, 0.0, 0.66, 0)              # the stretcher, head at the back wall (+y)
E_IV = (2.35, 2.95)
E_MON = (2.25, 1.55, 3.55)                                    # the monitor on its arm (x, Y, y), screen facing -y


def dr_ecg(pen, x, y, w, h, t=0.0, bpm=140, c='#5aff8a', a=255):
    """A scrolling ECG trace in a box (design px), beating at bpm."""
    period = 60.0 / bpm
    pts = []
    n = 120
    for i in range(n + 1):
        u = i / n
        tt = (t * 0.9 - (1 - u) * 1.6)
        ph = (tt % period) / period
        val = 0.0
        if 0.1 < ph < 0.14: val = -0.15
        elif 0.14 < ph < 0.17: val = 1.0 - (ph - 0.14) * 20
        elif 0.17 < ph < 0.2: val = -0.35
        elif 0.35 < ph < 0.48: val = 0.18 * math.sin((ph - 0.35) / 0.13 * math.pi)
        pts.append((x + u * w, y + h * 0.6 - val * h * 0.5))
    pen.line(poly(pts, False), max(1.0, h * 0.04), c, a)
    pen.fill(oval(pts[-1][0], pts[-1][1], max(1.5, h * 0.05)), '#ffffff', a)


def dr_er_monitor(pen, v, t=0.0, live=True, bpm=140, P=E_MON):
    """The bedside monitor on its wall arm: ECG, SpO2 and the numbers (HR 140)."""
    x, Y, y = P
    if v.d(x, y) < 0.2: return
    B = Box(x, y - 0.06, 0.46, 0.08, Y - 0.17, Y + 0.17, 0)
    draw_box(pen, v, B, {'all': '#2a2c32', 'front': '#2a2c32'})
    F = Face((x - 0.21, Y + 0.15, y - 0.101), (1, 0, 0), (0, -1, 0), 42.0, 30.0, (0, 0, -1), 'front')
    if not v.visible(F.O, F.n): return
    m, _ = fmat(v, F.O, _scale3(F.Uu, 0.01), _scale3(F.Vu, 0.01))
    pen.cv.save(); pen.cv.concat(m)
    pen.fill(rect(0, 0, 42, 30), '#05080a')
    dr_ecg(pen, 1.5, 3, 28, 9, t if live else 0.6, bpm, '#5aff8a')
    dr_ecg(pen, 1.5, 13, 28, 7, t * 0.7 + 0.3 if live else 0.3, bpm, '#5ad8ff', 200)
    btext(pen, str(bpm), 36, 10, 'sans_b', 7, '#5aff8a', 255, 'center')
    btext(pen, '98', 36, 20, 'sans_b', 5.5, '#5ad8ff', 255, 'center')
    btext(pen, 'HR', 36, 3.5, 'sans', 2.2, '#5aff8a', 220, 'center'); btext(pen, 'SpO2', 36, 14, 'sans', 2.2, '#5ad8ff', 220, 'center')
    pen.fill(rect(1.5, 23, 28, 0.4), '#3a3a3a')
    btext(pen, 'NIBP 98/62', 2, 28, 'sans', 3, '#f2d84a', 230)
    pen.cv.restore()


def dr_iv_pole(pen, v, x=None, y=None, bag=True, Y0=0.0):
    x = E_IV[0] if x is None else x; y = E_IV[1] if y is None else y
    if v.d(x, y) < 0.2: return
    s = v.s(x, y)
    for k in range(5):
        a = 2 * math.pi * k / 5
        pen.seg(v.p(x, Y0 + 0.06, y), v.p(x + math.cos(a) * 0.25, Y0 + 0.03, y + math.sin(a) * 0.25), max(1.2, 0.02 * s), '#8a8e94')
    a_, b_ = v.p(x, Y0 + 0.05, y), v.p(x, Y0 + 2.0, y)
    pen.seg(a_, b_, max(1.5, 0.02 * s) + 1.5, LINE); pen.seg(a_, b_, max(1.2, 0.02 * s), '#c8ccd0')
    hk = v.p(x, Y0 + 1.95, y)
    pen.seg((hk[0] - 0.12 * s, hk[1]), (hk[0] + 0.12 * s, hk[1]), max(1.0, 0.012 * s), '#c8ccd0')
    if bag:
        bx, by = hk[0] - 0.1 * s, hk[1] + 0.03 * s
        bg = rrect(bx - 0.07 * s, by, 0.14 * s, 0.24 * s, 0.03 * s)
        pen.fill(bg, '#dcecf4', 200); pen.fill(rect(bx - 0.06 * s, by + 0.08 * s, 0.12 * s, 0.15 * s), '#c8e4f0', 160); pen.line(bg, 0.9)
        pen.fill(rect(bx - 0.04 * s, by + 0.03 * s, 0.08 * s, 0.04 * s), '#ffffff')
        btext(pen, 'NS', bx, by + 0.065 * s, 'sans_b', 0.025 * s, '#2a4a8a', 230, 'center')
        pen.line(smooth([(bx, by + 0.24 * s), (bx - 0.05 * s, by + 0.5 * s), v.p(E_BED.cx + 0.25, 0.75, E_BED.cy - 0.1)], False, 0.8), max(0.8, 0.005 * s), '#e8f0f4', 200)


def _er_bay_cfg():
    def lights(o):
        panels = [Lamp(1.6, 2.65, 1.6, 5.0, '#fff6ea', 0.8, (1.0, 0.7, 0.4), fall=1.25), Lamp(1.6, 2.65, 2.8, 4.0, '#fff6ea', 0.55, (1.0, 0.7, 0.4), fall=1.3)]
        return '#7c8288', panels, [('exam', [Lamp(E_BED.cx, 2.4, E_BED.cy, 2.6, '#ffffff', 0.8, (1.0, 0.5, 0.2), fall=1.5)], _kfn(o.get('exam', 1.0), 271))]

    def art(o):
        def back(p_, W, H):
            p_.fill(rect(60, H - 175, 200, 40), '#c8d0d8'); p_.line(rect(60, H - 175, 200, 40), 0.8, '#6a7480')                    # the headwall rail
            for k, c_ in enumerate(('#2a8a4a', '#ffffff', '#f2d84a', '#2a2a2a')):                                                   # O2, air, vac outlets
                p_.fill(oval(85 + k * 22, H - 155, 5.5), c_); p_.line(oval(85 + k * 22, H - 155, 5.5), 0.6, '#3a3a3a')
            p_.fill(rect(270, H - 150, 26, 34), '#e84a3a'); p_.fill(rect(273, H - 147, 20, 6), '#ffffff')                         # sharps box
            p_.fill(rect(20, H - 140, 30, 18), '#f2f2f0'); p_.line(rect(20, H - 140, 30, 18), 0.6, '#7a7a7a')                       # glove box
            for k, c_ in enumerate(('#8ab0e8', '#e8a8c8', '#a8e8b8')): p_.fill(rect(22 + k * 9, H - 144, 8, 4), c_)
        def west(p_, W, H):
            _poster_art(p_, 130, H - 185, 46, 60, 'fast')
            _office_clock(p_, 240, H - 215, 14, 4, 22)
        def east(p_, W, H):
            p_.fill(rect(40, H - 210, 150, 80), '#e8ecf0'); p_.line(rect(40, H - 210, 150, 80), 0.8, '#8a929a')                    # supply cabinet glass
            for k in range(3):
                for j in range(6): p_.fill(rect(46 + j * 24, H - 204 + k * 26, 20, 18), ['#c8e0f0', '#f0e0c8', '#e0f0d8'][(j + k) % 3])
        return {'back': back, 'west': west, 'east': east}

    def pieces(o):
        bp = hosp_bed_parts(E_BED)
        P = [Piece('bed', (E_BED.cx, 0.4, E_BED.cy), lambda pen, v: draw_parts(pen, v, bp), occupant=[(E_BED.cx, E_BED.cy)], front=bp, block=E_BED.footprint()),
             Piece('iv', (E_IV[0], 1.0, E_IV[1]), lambda pen, v: dr_iv_pole(pen, v), block=_circ(E_IV[0], E_IV[1], 0.25)),
             Piece('counter', (0.3, 0.5, 2.6), lambda pen, v: draw_box(pen, v, Box(0.3, 2.6, 1.2, 0.55, 0.0, 0.9, 90),
                                                                        {'front': dict(fill='#e8ecf0', art=lambda p_, W, H: _chrome_pulls(p_, W, H, 3, 12)),
                                                                         'all': '#c8d0d8', 'top': '#d8e0e8'}), block=_box_pts(0.3, 2.6, 0.28, 0.6)),
             Piece('stool', (0.85, 0.3, 1.2), lambda pen, v: dr_stool(pen, v, 0.85, 1.2))]
        if not o.get('live_monitor'):
            P.append(Piece('monitor', (E_MON[0], E_MON[1], E_MON[2] - 0.1), lambda pen, v: dr_er_monitor(pen, v, 0.0, False)))
        return P

    def shell_x(pen, v, o):
        # the curtain track across the open front and the curtain pulled back to the east side
        a_, b_ = v.p(0.0, 2.6, 0.05), v.p(3.2, 2.6, 0.05)
        pen.seg(a_, b_, max(1.5, 0.015 * v.s(1.6, 0.05)), '#a8acb0')
        F = Face((2.55, 2.55, 0.06), (1, 0, 0), (0, -1, 0), 65.0, 230.0, (0, 0, -1), 'front')
        shp = poly([(0, 0), (65, 0)] + [(x, 230 - 3 * abs(math.sin(x * 0.3))) for x in np.linspace(65, 0, 14)])
        draw_face(pen, v, F, lambda p_, W, H: [p_.linear(rect(k * 8, 0, 8, H), k * 8, 0, k * 8 + 8, 0, [(0, '#000000', 40), (0.5, '#ffffff', 30), (1, '#000000', 40)])
                                               for k in range(int(W / 8) + 1)], '#9ac8d8', shape=shp, ao=False, lw=0.9)
        for x in (1.0, 2.2):
            _ceiling_panel_light(pen, v, x, 1.8, 2.7, 1.0, 0.6, 1.2)

    def spots(v, o):
        S = {}
        S['bed_lie'] = _mk_spot(v, 'bed_lie', E_BED.cx, E_BED.cy, 0.66, 'lie', 'Milo lying on the stretcher (head at the back wall, +y)')
        S['bed_edge'] = _mk_spot(v, 'bed_edge', E_BED.cx - 0.3, E_BED.cy - 0.4, 0.0, 'seat', 'sitting on the stretcher edge (faces -x)', face=(-1, 0), seat_Y=0.66, perch=True)
        S['nurse'] = _mk_spot(v, 'nurse', 0.75, 2.0, 0.0, 'stand', "at the bed's left (Mom / the nurse, starting the IV)", face=(1, 0))
        S['doctor'] = _mk_spot(v, 'doctor', 2.45, 1.55, 0.0, 'stand', "at the bed's right (the ER doctor)", face=(-1, 0.2))
        S['foot'] = _mk_spot(v, 'foot', E_BED.cx, 0.75, 0.0, 'stand', 'at the foot of the bed (the narrator / Halverson)', face=(0, 1))
        S['monitor'] = _mk_spot(v, 'monitor', E_MON[0], E_MON[2] - 0.11, E_MON[1], 'point', 'the monitor screen (HR 140)')
        S['iv_bag'] = _mk_spot(v, 'iv_bag', E_IV[0] - 0.1, E_IV[1], 1.8, 'point', 'the IV bag (fluids)')
        S['iv_hand'] = _mk_spot(v, 'iv_hand', E_BED.cx + 0.28, E_BED.cy - 0.15, 0.74, 'point', "Milo's right hand on the sheet (where the IV line goes)")
        return S
    return dict(name='er_bay', R=E_R, H=2.7, floor=dict(base='#d8dce0', kind='tile', ink='#b8c0c8', scale=2.0),
                walls=dict(paper='#d6e6e8', wains=1.0, wcol='#a8ccd2', trim='#e8c86a', base_h=0.12, seed=35),
                holes={'front': [(0.05, 0.0, 3.15, 0.0, 0.0, 2.6)]}, art=art, ceil=dict(c='#eef0ee', art=lambda p_, W, H: pat(p_, W, H, 'tile', '#ccd2d0', 200, scale=4.0)),
                lights=lights, pieces=pieces, spots=spots, shell_x=shell_x,
                glows=lambda v, o: [])


_dcam('dr_er_bay', 900, 500, 1.55, 0.35, 0.25, 32, _env(), 'the ER bay at 3/4 from the curtain: Milo on the stretcher, the IV pole, the monitor; Mom on the left', 'er_bay')
_dcam('dr_er_bay_side', 960, 500, 1.4, 2.9, 0.6, -28, _env(), 'the bay from the right: Mom and the nurse working at the bed, the monitor above', 'er_bay')
_dcam('dr_er_monitor', 2600, 560, 1.5, 1.6, 1.4, 30, _env(x=(920, 1000), y=(500, 580), zoom=(1.0, 1.05), f=(1.0, 1.4)), 'close on the monitor ("beeped like they were cheering")', 'er_bay')


def _outside_er_floor(pen, v):
    """Beyond the open curtain: the bright ER floor (the nurses' station, the opposite bays' curtains, people)."""
    pen.fill(rect(-800, -600, 3600, 2400), '#e8eef0')
    with lighting('#c8d0d4', [Lamp(1.6, 2.6, -3.0, 9.0, '#ffffff', 0.6, fall=1.2)]):
        F = floor_face(-12, 15, -9, 0, 0.0)
        draw_face(pen, v, F, lambda p_, W, H: pat(p_, W, H, 'tile', '#b8c0c8', 200, scale=2.0), '#d8dce0', ao=False, line=False)
        wall(pen, v, (15, -9), (-12, -9), 0.0, 2.8, '#dce6ea', None, None, [], wains=1.0, wcol='#b8d0d8', seed=36)
        ceil_rect(pen, v, -12, 15, -9, 0, 2.8, c='#eef0ee')
        B = Box(1.6, -6.0, 4.5, 0.8, 0.0, 1.1, 0)
        draw_box(pen, v, B, {'front': dict(fill='#7aa8b8', art=lambda p_, W, H: btext(p_, 'NURSES', W / 2, H * 0.5, 'sans_b', 14, '#ffffff', 220, 'center')), 'all': '#6a98a8', 'top': '#e8ecf0'})
        for x in (-6.0, 9.0):
            F2 = Face((x - 1.2, 2.5, -4.0), (1, 0, 0), (0, -1, 0), 240, 230, (0, 0, 1), 'front')
            draw_face(pen, v, F2, lambda p_, W, H: [p_.linear(rect(k * 10, 0, 10, H), k * 10, 0, k * 10 + 10, 0, [(0, '#000000', 30), (0.5, '#ffffff', 20), (1, '#000000', 30)]) for k in range(24)],
                      '#9ac8d8', ao=False)
        for (x, y) in ((-1.0, -5.0), (3.5, -5.2)):
            dr_monitor(pen, v, x, 1.1, y, 0, 1.0, 'chart')


def dr_er_bay(view='bay', live_monitor=True, bpm=140, exam=1.0, **kw):
    """The ER bay (bright, safe): the stretcher, the IV pole with fluids, the monitor (live ECG at bpm), the curtain pulled
    back onto the busy ER floor. view 'bay' | 'side' | 'monitor'."""
    name = 'dr_er_' + ('monitor' if view == 'monitor' else ('bay_side' if view == 'side' else 'bay'))
    o = dict(live_monitor=live_monitor, exam=exam)
    dyn = []
    if live_monitor:
        v = cam(name)
        lay = Layer(max(0.3, v.d(E_MON[0], E_MON[2])), lambda pen, t: dr_er_monitor(pen, v, t, True, bpm), 'monitor_live', blur=None)
        lay.order = v.d(E_MON[0], E_MON[2] - 0.1)
        dyn.append(lay)
    return _box_build(_er_bay_cfg(), name, o, outside=_outside_er_floor, grade='dr_er', dyn=dyn)


# ---------------------------------------------------------------------------------------------- Larkfield General: the ER waiting room (bright and real)
W_R = (0.0, 9.0, 0.0, 7.0)
W_ROWS = [(1.1, 2.5), (1.1, 3.75), (1.1, 5.0)]                  # (x of the first seat, y) three rows of seven facing the TV (+y)
W_PITCH = 0.6
W_DESK = Box(8.45, 3.6, 2.6, 0.7, 0.0, 1.05, -90)               # the triage desk along the east wall, facing -x
W_CHEST, W_ROCK = (0, 2), (0, 3)                                # the man with chest pain, the empty chair still rocking


def dr_single_chair(pen, v, x, y, fa=180, c=D_CHAIR_ER, rock=0.0):
    """A free-standing moulded plastic chair (fa: 180 = faces +y); rock (degrees) tips it back and forth on its back legs."""
    if abs(rock) < 0.01:
        _plastic_chair(pen, v, x, y, fa, c)
        return
    # tilt by drawing in a lifted / shifted view: approximate the rock as a small forward-back shift of the seat and back
    th = math.radians(rock)
    B = Box(x, y, 0.46, 0.46, 0.0, 0.46, fa)
    nx, ny = B.N
    parts = []
    for (u, n) in ((-0.2, -0.2), (0.2, -0.2), (-0.2, 0.2), (0.2, 0.2)):
        lift = max(0.0, math.sin(th) * (n + 0.2)) if rock > 0 else max(0.0, -math.sin(th) * (0.2 - n))
        parts.append(Part(sub(B, u - 0.015, u + 0.015, n - 0.015, n + 0.015, lift, 0.43 + lift), {'all': '#9aa0a8'}))
    lift_s = abs(math.sin(th)) * 0.2
    parts.append(Part(fn=lambda pen, v: box_extrude(pen, v, B, -0.22, 0.22, -0.22, 0.22, 0.42 + lift_s, 0.47 + lift_s, lambda W, H: rounded_rect_pts(W, H, 2.0), c, _darken(c, 0.2)),
                      ref=B.at(0, 0, 0.45)))
    sh = math.sin(th) * 0.3
    parts.append(Part(fn=lambda pen, v: box_extrude(pen, v, B, -0.22, 0.22, -0.24 - sh, -0.2 - sh, 0.62 + lift_s, 0.88 + lift_s, lambda W, H: rounded_rect_pts(W, H, 5.0, 2.0), c, _darken(c, 0.2)),
                      ref=B.at(0, -0.22, 0.75)))
    draw_parts(pen, v, parts)


def dr_er_seats():
    out = []
    for ri, (x0, y) in enumerate(W_ROWS):
        for i in range(7):
            out.append((ri, i, x0 + i * W_PITCH, y))
    return out


def _er_wait_cfg():
    def lights(o):
        panels = [Lamp(x, 2.75, y, 5.5, '#fff8ee', 0.7, (1.0, 0.7, 0.4), fall=1.25) for x in (2.0, 5.0, 8.0) for y in (2.0, 5.0)]
        door = Lamp(kind='win', c='#3a4a7a', k=0.4, soft=12.0, panes=[[(6.5, 2.2, 0.0), (8.3, 2.2, 0.0), (8.3, 0.1, 0.0), (6.5, 0.1, 0.0)]], d=_norm3((0.0, -0.3, 1.0)))
        return '#8a8e94', panels + [door], [('tv', [Lamp(4.5, 2.0, 6.7, 3.0, '#ffc89a', 0.4, fall=1.5)], _kfn(o.get('tv', 1.0), 281))]

    def art(o):
        def back(p_, W, H):
            _poster_art(p_, 60, H - 190, 46, 60, 'fast')
            _poster_art(p_, 120, H - 185, 46, 60, 'heart')
            p_.fill(rect(560, H - 200, 160, 46), '#2a6aa8'); btext(p_, 'CHEST PAIN?', 640, H - 182, 'sans_b', 14, '#ffffff', 250, 'center')
            btext(p_, 'TELL THE NURSE RIGHT AWAY', 640, H - 164, 'sans_b', 8.5, '#ffffff', 245, 'center')
            _office_clock(p_, 760, H - 225, 15, 5, 12)
        def west(p_, W, H):
            _poster_art(p_, 220, H - 185, 50, 60, 'wash')
            _poster_art(p_, 320, H - 190, 70, 52, 'breathe')
        def front(p_, W, H):
            p_.fill(rect(30, H - 240, 160, 40), '#c82a2a'); btext(p_, 'EMERGENCY', 110, H - 212, 'sans_b', 22, '#ffffff', 250, 'center')
        def east(p_, W, H):
            p_.fill(rect(200, H - 240, 180, 36), '#3a7a8a'); btext(p_, 'TRIAGE', 290, H - 214, 'sans_b', 20, '#ffffff', 250, 'center')
        return {'back': back, 'west': west, 'front': front, 'east': east}

    def pieces(o):
        P = []
        rock = o.get('rock', 0.0)
        for (ri, i, x, y) in dr_er_seats():
            if (ri, i) == W_ROCK and (callable(rock) or rock): continue
            P.append(Piece('chair_r%d_%d' % (ri, i), (x, 0.45, y), (lambda x_, y_: lambda pen, v: dr_single_chair(pen, v, x_, y_, 180))(x, y),
                           occupant=[(x, y + 0.02)], front=None, block=_circ(x, y, 0.24)))
        if not callable(rock) and rock and rock != 'f':
            x, y = [(q[2], q[3]) for q in dr_er_seats() if (q[0], q[1]) == W_ROCK][0]
            P.append(Piece('chair_rock', (x, 0.45, y), lambda pen, v: dr_single_chair(pen, v, x, y, 180, rock=rock)))

        def desk(pen, v):
            draw_box(pen, v, W_DESK, {'front': dict(fill='#7aa8b8', art=lambda p_, W, H: (p_.fill(rect(0, 0, W, 8), '#e8ecf0'), btext(p_, 'PLEASE CHECK IN HERE', W / 2, H * 0.55, 'sans_b', 7, '#ffffff', 240, 'center'))),
                                      'all': '#6a98a8', 'top': '#e8ecf0'})
            gl = Face((W_DESK.cx - 0.3, 2.1, W_DESK.cy - 1.25), (0, 0, 1), (0, -1, 0), 250, 100, (-1, 0, 0), 'front')
            draw_face(pen, v, gl, lambda p_, W, H: p_.linear(rect(0, 0, W, H), 0, 0, W, H, [(0, '#ffffff', 40), (0.4, '#ffffff', 10), (1, '#ffffff', 40)]), '#d8e8f0',
                      ao=False, unlit=True, lw=1.0, holes=None) if False else None
            dr_monitor(pen, v, W_DESK.cx + 0.1, 1.05, W_DESK.cy - 0.6, -90, 1.0, 'chart')
        P.append(Piece('desk', (W_DESK.cx, 0.5, W_DESK.cy), desk, block=W_DESK.footprint()))
        P.append(Piece('vending', (0.45, 0.9, 6.4), lambda pen, v: draw_box(pen, v, Box(0.45, 6.4, 0.9, 0.75, 0.0, 1.85, 90),
                                                                             {'front': dict(fill='#2a6aa8', art=lambda p_, W, H: [p_.fill(rect(6 + (k % 4) * W * 0.15, 10 + (k // 4) * H * 0.13, W * 0.11, H * 0.08),
                                                                                                                                         ['#d84a3a', '#4a8ad8', '#e8c84a', '#5ab85a'][k % 4]) for k in range(20)]),
                                                                              'all': '#1a4a7a'}), block=_box_pts(0.45, 6.4, 0.38, 0.45)))
        P.append(Piece('plant', (8.6, 0.4, 6.5), lambda pen, v: dr_plant(pen, v, 8.6, 6.5)))
        P.append(Piece('plant2', (0.4, 0.4, 0.5), lambda pen, v: dr_plant(pen, v, 0.4, 0.5, 0.0, 1.0, '#4a8a5a')))
        P.append(Piece('magazines', (6.0, 0.3, 3.8), lambda pen, v: (draw_parts(pen, v, table_parts(Box(6.0, 3.8, 0.6, 0.6, 0.0, 0.45, 0), '#c8a878', apron=0.04)),
                                                                     dr_papers(pen, v, 6.0, 0.45, 3.8, 4, '#e8d8c8', 9, True, 20)), block=_box_pts(6.0, 3.8, 0.3, 0.3)))
        P.append(Piece('cooler', (8.6, 0.6, 5.6), lambda pen, v: (draw_box(pen, v, Box(8.6, 5.6, 0.35, 0.35, 0.0, 1.0, -90), {'all': '#e8ecf0'}),
                                                                  draw_box(pen, v, Box(8.6, 5.6, 0.28, 0.28, 1.0, 1.45, -90), {'all': '#a8d0f0'}))))
        P.append(Piece('tv', (4.5, 2.2, 6.9), lambda pen, v: draw_box(pen, v, Box(4.5, 6.95, 1.2, 0.08, 1.75, 2.45, 0),
                                                                       {'all': '#1a1a1e', 'front': dict(fill='#1a1a1e', art=lambda p_, W, H: (p_.linear(rect(3, 3, W - 6, H - 6), 0, 0, W, H, ['#f2b86a', '#e85a4a', '#4a8ad8']),
                                                                                                                                              p_.fill(oval(W * 0.35, H * 0.6, W * 0.12), '#f8e8c8')))})))
        return P

    def shell_x(pen, v, o):
        for x in (2.0, 5.0, 8.0):
            for y in (2.0, 5.0):
                _ceiling_panel_light(pen, v, x, y, 2.8, 1.0)
        # the automatic sliding doors (glass, night outside)
        F = Face((6.5, 2.2, 0.02), (1, 0, 0), (0, -1, 0), 180, 220, (0, 0, 1), 'front')
        draw_face(pen, v, F, lambda p_, W, H: (p_.fill(rect(0, 0, W, H), '#1a2234', 160), p_.fill(rect(W / 2 - 1, 0, 2, H), '#a8b0b8'),
                                               p_.linear(rect(0, 0, W, H), 0, 0, W, H, [(0, '#ffffff', 0), (0.3, '#ffffff', 40), (0.36, '#ffffff', 0)])), '#1a2234', ao=False, unlit=True)

    def spots(v, o):
        S = {}
        for (ri, i, x, y) in dr_er_seats():
            S['seat_r%d_%d' % (ri, i)] = _mk_spot(v, 'seat_r%d_%d' % (ri, i), x, y + 0.02, 0.0, 'seat', 'ER waiting chair row %d seat %d (faces the TV, +y)' % (ri, i),
                                                   face=(0, 1), seat_Y=0.46)
        S['chest_seat'] = S['seat_r%d_%d' % W_CHEST]; S['chest_seat'].note = 'the man holding his chest sits here'
        S['rock_seat'] = S['seat_r%d_%d' % W_ROCK]; S['rock_seat'].note = 'the empty chair still rocking (rock=f(t) degrees; CH.chair_rock)'
        S['desk_nurse'] = _mk_spot(v, 'desk_nurse', 8.85, 3.6, 0.0, 'stand', 'the triage nurse behind the desk', face=(-1, 0))
        S['desk_front'] = _mk_spot(v, 'desk_front', 7.6, 3.6, 0.0, 'stand', 'at the desk', face=(1, 0))
        S['nurse_walk'] = _mk_spot(v, 'nurse_walk', 3.0, 2.0, 0.0, 'stand', 'the nurse walking straight up to him ("Sir, you don\'t wait"): in front of row 0', face=(-0.3, 1))
        S['entrance'] = _mk_spot(v, 'entrance', 7.4, 0.8, 0.0, 'stand', 'just inside the sliding doors', face=(0, 1))
        return S
    return dict(name='er_wait', R=W_R, H=2.8, floor=dict(base='#d8d4c8', kind='checker', ink='#c4bca8', scale=1.6),
                walls=dict(paper='#e6ece4', wains=1.0, wcol='#a8c8c0', trim='#8ab0a8', base_h=0.1, seed=37),
                holes={'front': [(6.5, 0.0, 8.3, 0.0, 0.0, 2.2)]}, art=art, ceil=dict(c='#f0f0ea', art=lambda p_, W, H: pat(p_, W, H, 'tile', '#d0d4cc', 200, scale=4.0)),
                lights=lights, pieces=pieces, spots=spots, shell_x=shell_x)


_dcam('dr_er_wait', 760, 480, 1.6, 8.3, 0.6, -48, _env(), 'the ER waiting room from the doors: rows of chairs, the TV, the triage desk (bright, real)', 'er_wait')
_dcam('dr_er_wait_chairs', 1050, 500, 1.35, 3.6, 1.15, -32, _env(), 'the man holding his chest and the empty chair beside him at 3/4 (seated turn ~0.55)', 'er_wait')
_dcam('dr_er_desk', 900, 500, 1.55, 6.2, 1.6, 70, _env(), 'the triage desk', 'er_wait')


def dr_er_wait(view='wide', rock=0.0, **kw):
    """The ER waiting room: bright and real. view 'wide' | 'chairs' | 'desk'. rock = the empty chair's tilt (degrees, or
    f(t) -> degrees: use CH.chair_rock(t, t_left))."""
    name = {'wide': 'dr_er_wait', 'chairs': 'dr_er_wait_chairs', 'desk': 'dr_er_desk'}[view]
    o = dict(rock=rock if not callable(rock) else 'f')
    dyn = []
    if callable(rock):
        v = cam(name)
        room = DrBox(_er_wait_cfg()); amb, steady, var = room.lights(o)
        x, y = [(q[2], q[3]) for q in dr_er_seats() if (q[0], q[1]) == W_ROCK][0]
        dyn.append(live_layer('chair_rock', v, (x, 0.45, y), lambda pen, v_, t: dr_single_chair(pen, v_, x, y, 180, rock=rock(t)), amb, steady, var))
    return _box_build(_er_wait_cfg(), name, o, outside=lambda pen, v: _outside_lot(pen, v), grade='dr_er', dyn=dyn)


# ---------------------------------------------------------------------------------------------- Larkfield General: the ER entrance at night
ER_OPEN = (-2.4, 2.4, 0.12, 2.6)                                # the glazed entrance: x0, x1, sill (the sidewalk), head
ER_LOBBY = (-3.4, 3.4, 0.05, 6.6)


def _er_wall_art(lit_only=False):
    def art(p_, W, H):
        if not lit_only:
            p_.fill(rect(0, H - 360, W, 360), '#8a4a3a'); p_.cv.save(); p_.cv.translate(0, H - 360); pat(p_, W, 360, 'brick', '#c8b8a0', 180, 4, '#8a4a3a'); p_.cv.restore()
            p_.fill(rect(0, 0, W, H - 360), '#b8b4aa'); p_.texture(rect(0, 0, W, H - 360), 'grunge', 0.4, 'overlay', 1.5)
        for k in range(14):                                               # the upper floors' windows: most of them lit, people working
            for j in range(2):
                x_ = 120 + k * 220; y_ = 90 + j * 230
                if abs(x_ - 1600) < 300 and j == 1: continue
                lit_ = ((k * 3 + j) % 4) != 0
                if lit_only and not lit_: continue
                p_.fill(rect(x_, y_, 140, 110), '#ffe2a8' if lit_ else '#1a2030')
                if lit_:
                    p_.fill(rect(x_, y_ + 62, 140, 48), '#f2c888'); p_.fill(rect(x_ + 68, y_, 4, 110), '#8a7a5a')
                    if (k + j) % 3 == 0: p_.fill(oval(x_ + 40, y_ + 58, 12, 16), '#6a5a4a', 200)      # someone at a window
                if not lit_only: p_.line(rect(x_, y_, 140, 110), 2.0, '#4a4a4a')
        for x_ in (300, 700, 2500, 2900):                                 # ground-floor windows (lit: the ER never sleeps)
            p_.fill(rect(x_, H - 300, 260, 180), '#ffecc0')
            p_.fill(rect(x_, H - 300, 260, 40), '#f4d8a0'); p_.fill(rect(x_ + 128, H - 300, 4, 180), '#8a7a5a')
            if not lit_only: p_.line(rect(x_, H - 300, 260, 180), 2.0, '#3a3a3a')
        if not lit_only:
            p_.fill(rect(1600 - 262, H - 284, 524, 284), '#e8e4da')            # the entrance surround (pale stone)
            p_.line(rect(1600 - 262, H - 284, 524, 284), 2.0, '#3a3a3a')
        hd = rect(1600 - 240, H - 276, 480, 20)                              # the lit header over the doors
        p_.fill(hd, '#fff6e0'); btext(p_, 'EMERGENCY  ENTRANCE', 1600, H - 261, 'sans_b', 13, '#c81e1e', 250, 'center', spacing=0.12)
    return art


def _er_lobby(pen, v):
    """The lobby behind the glass: warm and bright (the doctors' world): terrazzo, a triage desk, a corridor door, the
    ceiling panels. Drawn clipped to the entrance opening."""
    x0, x1, s0, s1 = ER_OPEN
    q = v.poly3([(x0, s0, 0.0), (x1, s0, 0.0), (x1, s1, 0.0), (x0, s1, 0.0)])
    if q.isEmpty(): return
    cv = pen.cv
    cv.save(); cv.clipPath(q, skia.ClipOp.kIntersect, True)
    pen.fill(q, '#f4ead8')
    try:
        with lighting('#e2d6c2', [Lamp(0.0, 2.9, 2.2, 7.0, '#fff2d8', 1.1, (1.0, 0.7, 0.4), fall=1.2), Lamp(0.0, 2.9, 5.0, 6.0, '#fff2d8', 0.9, (1.0, 0.7, 0.4), fall=1.2)]):
            lx0, lx1, ly0, ly1 = ER_LOBBY
            floor_rect(pen, v, lx0, lx1, ly0, ly1, 0.12, '#efe4d0', 'checker', '#dccdb4', seed=5, scale=1.4)
            for (side, a, b, u_of) in _walls_of((lx0, lx1, ly0, ly1)):
                if side == 'front': continue
                def wart(p_, W, H, side=side):
                    p_.fill(rect(0, H - 110, W, 110), '#9ec8c0'); p_.fill(rect(0, H - 114, W, 6), '#f4efe0')
                    if side == 'back':
                        p_.fill(rect(W / 2 - 150, H - 215, 110, 215), '#dfe6e2'); p_.line(rect(W / 2 - 150, H - 215, 110, 215), 2, '#5a6a66')       # the doors to the bays
                        p_.fill(rect(W / 2 - 96, H - 205, 4, 205), '#5a6a66'); p_.fill(rect(W / 2 - 132, H - 170, 26, 44), '#bfe0ea'); p_.fill(rect(W / 2 - 86, H - 170, 26, 44), '#bfe0ea')
                        sg = rect(W / 2 + 40, H - 236, 250, 46)
                        p_.fill(sg, '#3f8f8a'); btext(p_, 'TRIAGE', W / 2 + 165, H - 204, 'sans_b', 28, '#ffffff', 250, 'center', spacing=0.1)
                        p_.fill(rect(W / 2 - 300, H - 230, 90, 90), '#ffffff'); p_.fill(rect(W / 2 - 266, H - 220, 22, 70), '#d8423a'); p_.fill(rect(W / 2 - 290, H - 196, 70, 22), '#d8423a')
                wall(pen, v, a, b, 0.12, 3.0, '#f6efe0', None, None, [], art=wart)
            ceil_rect(pen, v, lx0, lx1, ly0, ly1, 3.0, c='#f2ece0')
            draw_box(pen, v, Box(1.2, 4.9, 2.6, 0.7, 0.12, 1.17, 0), {'all': '#3f8f8a', 'top': '#f2f4f0', 'front': dict(fill='#4a9a94', art=lambda p_, W, H: btext(
                p_, 'WE ARE HERE', W / 2, H * 0.6, 'sans_b', 17, '#e8f6f2', 235, 'center', spacing=0.1))})
            for (cx_, cy_) in ((-1.9, 4.2), (-1.9, 3.5)):                         # two waiting chairs, a plant
                draw_box(pen, v, Box(cx_, cy_, 0.5, 0.5, 0.12, 0.58, 90), {'all': D_CHAIR_ER, 'top': _lighten(D_CHAIR_ER, 0.15)})
                draw_box(pen, v, Box(cx_ - 0.24, cy_, 0.5, 0.06, 0.58, 1.0, 90), {'all': D_CHAIR_ER})
        for (cx_, cy_) in ((0.0, 2.0), (0.0, 4.6)):                               # the ceiling panels (emissive)
            pq = v.poly3([(cx_ - 0.6, 2.99, cy_ - 0.3), (cx_ + 0.6, 2.99, cy_ - 0.3), (cx_ + 0.6, 2.99, cy_ + 0.3), (cx_ - 0.6, 2.99, cy_ + 0.3)])
            if not pq.isEmpty() and v.cam_h < 2.99: pen.fill(pq, '#fffbee')
    finally:
        cv.restore()


def _er_door_panels(pen, v, k=0.0):
    """The glazed entrance: two fixed side lights, the two sliding leaves (k 0 shut .. 1 open: they slide behind the side
    lights), the steel frame."""
    x0, x1, s0, s1 = ER_OPEN
    k = clamp(k)
    def glass(xa, xb, y, a=46):
        qq = v.poly3([(xa, s0, y), (xb, s0, y), (xb, s1 - 0.2, y), (xa, s1 - 0.2, y)])
        if qq.isEmpty(): return
        pen.fill(qq, '#dff2f6', a)
        b = _rb(qq)
        pen.linear(qq, b[0], b[1], b[2], b[3], [(0, '#ffffff', 0), (0.3, '#ffffff', 46), (0.36, '#ffffff', 0), (0.7, '#ffffff', 0), (0.76, '#ffffff', 26), (0.8, '#ffffff', 0)])
        pen.line(qq, 2.2, '#8a949c', 255)
        s = v.S / max(0.3, v.d((xa + xb) / 2, y))
        ym = s0 + 1.05
        _seg3(pen, v, (xa + 0.06, ym, y), (xb - 0.06, ym, y), max(1.5, 0.03 * s), '#b4bcc4', 255, False)              # the push rail
    glass(x0, -1.2, 0.0); glass(1.2, x1, 0.0)
    glass(-1.2 - k * 1.14, 0.0 - k * 1.14, -0.04, 40); glass(0.0 + k * 1.14, 1.2 + k * 1.14, -0.04, 40)
    hq = v.poly3([(x0, s1 - 0.2, -0.05), (x1, s1 - 0.2, -0.05), (x1, s1, -0.05), (x0, s1, -0.05)])
    if not hq.isEmpty(): pen.fill(hq, '#6a747c'); pen.line(hq, 1.0)
    sq = v.poly3([(-0.25, s1 - 0.14, -0.06), (0.25, s1 - 0.14, -0.06), (0.25, s1 - 0.06, -0.06), (-0.25, s1 - 0.06, -0.06)])
    if not sq.isEmpty(): pen.fill(sq, '#1a1c20'); pen.fill(oval(*v.p(0.0, s1 - 0.1, -0.06), max(1.5, 0.02 * v.S / max(0.3, v.d(0, 0)))), '#3ae06a' if k > 0.02 else '#e04a3a')


def dr_er_facade(pen, v, doors=0.0, t=0.0, part='all'):
    """The ER entrance: a brick and concrete front with its windows lit, the canopy over the drive on four columns,
    EMERGENCY in red letters, the glazed entrance with automatic sliding doors (doors 0 shut .. 1 open) and the bright,
    warm lobby behind. part 'all' | 'wall' (no doors: they are a live layer) | 'canopy'."""
    G = 0.0
    F = wall_face((-16.0, 0.0), (16.0, 0.0), G, 9.0)
    if v.visible(F.O, F.n) and part in ('all', 'wall'):
        _er_lobby(pen, v)
        x0, x1, s0, s1 = ER_OPEN
        holes = [rect(1600 + x0 * 100, 900 - s1 * 100, (x1 - x0) * 100, (s1 - s0) * 100 + 14)]
        draw_face(pen, v, F, _er_wall_art(), '#b8b4aa', holes=holes, ao=False)
        if part == 'all': _er_door_panels(pen, v, doors)
    if part in ('all', 'canopy'):
        for (cx_, cy_) in ((-5.5, -0.6), (5.5, -0.6), (-5.5, -6.2), (5.5, -6.2)):
            draw_box(pen, v, Box(cx_, cy_, 0.35, 0.35, 0.0, 3.6, 0), {'all': '#c8c4bc'})
        cq = Box(0.0, -3.3, 12.4, 6.6, 3.6, 4.1, 0)
        draw_box(pen, v, cq, {'all': '#d8d4cc', 'bottom': dict(fill='#c8c4bc', art=lambda p_, W, H: [p_.fill(rect(60 + k * 160, H / 2 - 20, 90, 40), '#fffbe8') for k in range(8)]),
                              'front': dict(fill='#d8d4cc', art=lambda p_, W, H: (p_.fill(rect(W / 2 - 330, 6, 660, H - 12), '#ffffff'),
                                                                                     btext(p_, 'EMERGENCY', W / 2, H * 0.78, 'sans_b', H * 0.7, '#d81e1e', 255, 'center')))})


def _er_emissive(pen, v, k=1.0):
    """Everything at the ER that makes its own light, drawn over the night: the lit windows, the header and the lobby
    seen through the glass stay as bright as they are; the EMERGENCY sign, the canopy's down-lights and their warm pools
    on the wet tarmac."""
    F = wall_face((-16.0, 0.0), (16.0, 0.0), 0.0, 9.0)
    if v.visible(F.O, F.n):
        draw_face(pen, v, F, _er_wall_art(True), None, ao=False, unlit=True, line=False)
    Ff = Face((-3.3, 4.04, -6.602), (1, 0, 0), (0, -1, 0), 660, 38, (0, 0, -1), 'front')
    if v.visible(Ff.O, Ff.n):
        draw_face(pen, v, Ff, lambda p_, W, H: (p_.fill(rect(0, 0, W, H), '#fff8ec'), btext(p_, 'EMERGENCY', W / 2, H * 0.84, 'sans_b', H * 0.86, '#e01e1e', 255, 'center')),
                  '#fff8ec', ao=False, unlit=True, lw=1.0)
        p_ = v.p(0.0, 3.85, -6.62)
        if v.d(0.0, -6.62) > 0.5: pen.ellipse_glow(p_[0], p_[1], 3.8 * v.s(0, -6.62), 0.7 * v.s(0, -6.62), '#ff3020', 70 * k)
    if v.cam_h < 3.6:
        for i in range(8):
            x = -5.4 + i * 1.6
            pq = v.poly3([(x - 0.45, 3.595, -3.5), (x + 0.45, 3.595, -3.5), (x + 0.45, 3.595, -3.1), (x - 0.45, 3.595, -3.1)])
            if not pq.isEmpty(): pen.fill(pq, '#fffbe8', 240)
    for x in (-3.5, 0.0, 3.5):
        if v.d(x, -3.3) > 0.5:
            q = v.p(x, 3.55, -3.3); pen.glow(q[0], q[1], 1.4 * v.s(x, -3.3), '#fff0d0', 60 * k)
            g = v.p(x, 0.0, -3.3); s = v.s(x, -3.3)
            pen.ellipse_glow(g[0], g[1], 3.2 * s, max(4.0, 0.8 * s * clamp(abs(v.h - g[1]) / max(1.0, 3.2 * s), 0.15, 1.0)), '#ffe8c0', 50 * k)
    if v.d(0.0, 0.3) > 0.5:                                                   # the lobby's light spilling out of the doors
        q = v.p(0.0, 1.3, 0.0); s = v.s(0.0, 0.0)
        kc = clamp(v.d(0.0, 0.0) / 16.0, 0.4, 1.0)                           # close views: less haze over the lobby (keeps TRIAGE legible)
        pen.ellipse_glow(q[0], q[1], 3.4 * s, 1.8 * s, '#fff0d0', 46 * k * kc)
        g = v.p(0.0, 0.12, -1.0)
        pen.ellipse_glow(g[0], g[1], 3.0 * s, max(4.0, 0.9 * s * clamp(abs(v.h - g[1]) / max(1.0, 3.0 * s), 0.15, 1.0)), '#fff0d0', 70 * k)


def _er_ext_cfg():
    def lights(o):
        canopy = [Lamp(x, 3.5, -3.3, 7.0, '#fff4e0', 1.3, (1.0, 0.6, 0.3), fall=1.3) for x in (-3.5, 3.5)]
        lobby = Lamp(0.0, 1.4, -0.4, 8.0, '#fff0d0', 1.25, fall=1.3)
        return '#3a4468', canopy + [lobby, Lamp(0.0, 3.5, -3.3, 7.0, '#fff4e0', 1.2, (1.0, 0.6, 0.3), fall=1.3)], [('sign', [Lamp(0.0, 3.85, -6.7, 6.0, '#ff2a2a', 0.8, fall=1.4)], _kfn(1.0, 291))]

    def shell(pen, v, o):
        dr_sky(pen, v, 'night')
        dr_far_ring(pen, v, 'night', R=90.0, cx=0.0, cy=0.0, G=0.0)
        F = floor_face(-90, 90, -90, 30, 0.0)
        draw_face(pen, v, F, lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'asphalt', 0.7, 'overlay', 1.6), '#24262c', ao=False, line=False)
        sw = floor_face(-16, 16, -1.2, 0.0, 0.12)
        draw_face(pen, v, sw, lambda p_, W, H: [p_.fill(rect(k * 150, 0, 1.2, H), '#000000', 90) for k in range(22)], '#7a7c80', ao=False)
        kerb = v.poly3([(-16, 0.12, -1.2), (16, 0.12, -1.2), (16, 0.0, -1.2), (-16, 0.0, -1.2)])
        if not kerb.isEmpty(): pen.fill(kerb, lit('#8a8c90', (0, 0.06, -1.2), (0, 0, -1)))
        for k in range(6):                                                    # painted bay lines + the red AMBULANCE ONLY
            xx = -7.5 + k * 3.0
            pen.fill(v.poly3([(xx - 0.05, 0.002, -1.4), (xx + 0.05, 0.002, -1.4), (xx + 0.05, 0.002, -7.0), (xx - 0.05, 0.002, -7.0)]), '#d8d4b8', 120)
        dr_er_facade(pen, v, 0.0 if callable(o.get('doors', 0.0)) else o.get('doors', 0.0), part='wall' if callable(o.get('doors', 0.0)) else 'all')
        if callable(o.get('doors', 0.0)): dr_er_facade(pen, v, 0.0, part='canopy')

    def pieces(o):
        P = []
        if o.get('car'):
            parts, seats, B = dr_car_parts(1.8, -3.4, fa=90, lights=True, Y0=0.0)
            P.append(Piece('car', (B.cx, 0.6, B.cy), lambda pen, v, parts=parts: draw_parts(pen, v, parts), occupant=[seats['driver']], front=parts, block=B.footprint()))
        P.append(Piece('ambulance', (-8.0, 1.2, -4.5), lambda pen, v: dr_ambulance(pen, v, -8.0, -4.5)))
        return P

    def glows(v, o):
        def g(pen, t):
            _er_emissive(pen, v)
        return [('lights_glow', (0.0, 3.0, 20.0), g)]

    def spots(v, o):
        S = {}
        S['doors'] = _mk_spot(v, 'doors', 0.0, -0.3, 0.12, 'stand', 'at the sliding doors (threshold)', face=(0, 1))
        S['inside'] = _mk_spot(v, 'inside', 0.0, 1.6, 0.12, 'stand', 'in the lobby just inside the doors (Mom with the wheelchair, running out): give the figure '
                               'layer order = sp.info["inside_order"] (behind the glass, in front of the lobby)', face=(0, -1))
        S['curb'] = _mk_spot(v, 'curb', 1.2, -1.6, 0.0, 'stand', 'at the kerb by the car', face=(0, 1))
        S['car_stop'] = _mk_spot(v, 'car_stop', 1.8, -3.4, 0.0, 'point', "where Halverson's car stops under the canopy (car centre, facing -x)")
        if o.get('car'):
            _, seats, B = dr_car_parts(1.8, -3.4, fa=90, Y0=0.0)
            for nm, (x, y) in seats.items():
                S['car_' + nm] = _mk_spot(v, 'car_' + nm, x, y, 0.0, 'seat', 'the car under the canopy: %s seat' % nm, face=(-1, 0), seat_Y=0.42)
        S['car_door_r'] = _mk_spot(v, 'car_door_r', 1.8, -2.4, 0.0, 'stand', 'outside the car\'s right-hand doors (kerb side)', face=(0, 1))
        return S
    return dict(name='er_ext', R=(-30.0, 30.0, -40.0, -0.05), lights=lights, shell=shell, pieces=pieces, glows=glows, spots=spots)


def dr_ambulance(pen, v, x, y, fa=0):
    """A parked ambulance: white box body with the red stripe and STAR OF LIFE, its light bar off."""
    if v.d(x, y) < 0.5: return
    B = Box(x, y, 2.2, 5.8, 0.0, 2.7, fa)
    box = Box(*B.at(0, -0.7, 0)[0::2], 2.2, 4.0, 0.45, 2.7, fa)
    cab = Box(*B.at(0, 2.1, 0)[0::2], 2.0, 1.6, 0.45, 2.1, fa)

    def side_art(p_, W, H):
        p_.fill(rect(0, H * 0.45, W, 18), '#d82a2a'); p_.fill(rect(0, H * 0.45 + 20, W, 6), '#2a5ad8')
        cx_, cy_ = W * 0.5, H * 0.25
        for a in (0, 60, 120):
            p_.cv.save(); p_.cv.translate(cx_, cy_); p_.cv.rotate(a); p_.fill(rect(-8, -26, 16, 52), '#2a5ad8'); p_.cv.restore()
    draw_box(pen, v, box, {'all': dict(fill='#f2f2ee', art=side_art), 'top': '#e8e8e4'})
    draw_box(pen, v, cab, {'all': '#f2f2ee', 'top': '#e8e8e4', 'front': dict(fill='#f2f2ee', art=lambda p_, W, H: p_.fill(rect(10, 10, W - 20, H * 0.45), '#1a2230'))})
    for (u, n) in ((-0.9, -2.2), (0.9, -2.2), (-0.9, 1.9), (0.9, 1.9)):
        c = B.at(u * 1.12, n, 0.38)
        if v.d(c[0], c[2]) < 0.3: continue
        px, py = v.p(*c); s = v.s(c[0], c[2])
        pen.fill(oval(px, py, 0.12 * s, 0.38 * s), '#121214')


_dcam('dr_er_ext', 820, 520, 1.6, 7.5, -15.0, -24, _env(), 'Larkfield General: the ER entrance at night in the rain (canopy, EMERGENCY, the sliding doors)', 'er_ext')
_dcam('dr_er_doors', 980, 520, 1.55, 2.4, -6.2, -8, _env(), 'the sliding doors from where the car stops (they open before we reach them; Mom running out)', 'er_ext')


def dr_er_entrance(view='ext', doors=0.0, car=False, rain=True, **kw):
    """The ER entrance at night. view 'ext' | 'doors'. doors 0..1 or f(t) (the automatic doors sliding open); car: the
    car stopped under the canopy (facing -x)."""
    cfg = _er_ext_cfg()
    cfg['shell_x'] = None
    o = dict(doors=doors if not callable(doors) else doors, car=car)

    class _R(DrBox):
        def shell(self, pen, v, o_): cfg['shell'](pen, v, o_)
    v = cam('dr_er_' + view)
    room = _R(dict(cfg, walls={}, floor={}))
    dyn = []
    if callable(doors):
        lay = Layer(max(0.3, v.d(0.0, 0.0)), lambda pen, t: _er_doors_live(pen, v, doors(t)), 'doors_live', blur=None)
        lay.order = ORDER_SHELL - 0.45
        dyn.append(lay)
    if rain:
        def r1(pen, t): dr_rain(pen, t, (-500, -400, 2900, 1800), 1.0, 9, 0.9, 0.1, '#a8b4cc', 24, 320, far=True)
        def r2(pen, t): dr_rain(pen, t, (-500, -400, 2900, 1800), 1.0, 10, 1.4, 0.12, '#c8d0e4', 34, 110)
        l1 = Layer(30.0, r1, 'rain_far', blur=None); l1.order = ORDER_SHELL - 0.6
        l2 = Layer(0.5, r2, 'rain_near', blur=None); l2.order = 0.2
        dyn += [l1, l2]
    o2 = dict(o); o2['doors'] = 'f' if callable(doors) else doors
    sp = build_view('dr_er_' + view, v, room, dict(o, doors=doors), outside=None, grade='dr_er_night', dyn=dyn)
    for l_ in sp:
        if l_.name == 'lights_glow': l_.order = ORDER_SHELL - 0.2          # the emissive pass sits right on the building, under everyone
    sp.info['inside_order'] = ORDER_SHELL - 0.3
    sp.info['note'] = ('Figures in the lobby (anchor inside): layer.order = sp.info["inside_order"] (the glass doors are drawn over them: live doors at '
                       'ORDER_SHELL - 0.45). Outside figures: sp.order_at(x, y).')
    return sp


def _er_doors_live(pen, v, k):
    _er_door_panels(pen, v, k)


# ---------------------------------------------------------------------------------------------- the long hospital hallway at night (one plastic chair at the end)
HH_R = (0.0, 2.6, 0.0, 32.0)
HH_LIGHTS = [2.0 + 4.0 * k for k in range(8)]                    # ceiling lights along the hall; only some are on at night
HH_CHAIR = (1.3, 31.35)


def _hosp_hall_cfg():
    def lights(o):
        steady = []
        var = []
        on = o.get('on', (0, 3, 6))
        for i, y in enumerate(HH_LIGHTS):
            if i in on: steady.append(Lamp(1.3, 2.6, y, 4.2, '#e8f0e8', 0.9, (1.0, 0.6, 0.3), fall=1.3))
        var.append(('end', [Lamp(1.3, 2.6, 30.8, 4.0, '#d8f0b0', 1.1, (1.0, 0.6, 0.3), fall=1.3)], o.get('end_fn') or _kfn(1.0, 301)))
        return '#1e2430', steady, var

    def art(o):
        def doors(p_, W, H, mirror=False):
            for k, u in enumerate(np.arange(3.0, 30.0, 5.5)):
                x_ = u * 100
                p_.fill(rect(x_, H - 210, 95, 210), '#c8ccc4'); p_.line(rect(x_, H - 210, 95, 210), 1.0, '#5a605a')
                p_.fill(rect(x_ + 30, H - 190, 36, 46), '#3a4450'); p_.fill(rrect(x_ + 80, H - 110, 7, 16, 2), '#a8acb0')
                p_.fill(rect(x_ + 30, H - 230, 36, 14), '#2a5a7a'); btext(p_, '%d' % (310 + k * 2 + (1 if mirror else 0)), x_ + 48, H - 219, 'sans_b', 8, '#ffffff', 230, 'center')
            p_.fill(rect(0, H - 95, W, 4), '#d8d8d0'); p_.fill(rect(0, H - 92, W, 1.2), '#000000', 70)
        return {'west': lambda p_, W, H: doors(p_, W, H, False), 'east': lambda p_, W, H: doors(p_, W, H, True),
                'back': lambda p_, W, H: (p_.fill(rect(W / 2 - 45, H - 200, 90, 100), '#0c1220'), p_.line(rect(W / 2 - 45, H - 200, 90, 100), 3.0, '#c8ccc4'))}

    def pieces(o):
        return [Piece('last_chair', (HH_CHAIR[0], 0.45, HH_CHAIR[1]), lambda pen, v: _plastic_chair(pen, v, HH_CHAIR[0], HH_CHAIR[1], 0, D_CHAIR_BLUE),
                      occupant=[HH_CHAIR], block=_circ(HH_CHAIR[0], HH_CHAIR[1], 0.26))]

    def shell_x(pen, v, o):
        on = o.get('on', (0, 3, 6))
        for i, y in enumerate(HH_LIGHTS):
            _ceiling_panel_light(pen, v, 1.3, y, 2.7, 1.0 if i in on else 0.0, 0.6, 1.2, '#e8f0e8')

    def glows(v, o):
        f = o.get('end_fn') or _kfn(1.0, 301)
        return [('end_glow', (1.3, 2.6, 30.8), lambda pen, t: _ceiling_panel_light(pen, v, 1.3, 30.8, 2.7, f(t), 0.6, 1.2, D_TUBE))]

    def spots(v, o):
        S = {}
        S['last_chair'] = _mk_spot(v, 'last_chair', HH_CHAIR[0], HH_CHAIR[1] + 0.02, 0.0, 'seat', 'the last plastic chair at the end of the hall (something very tall folded up in it), facing us (-y)',
                                   face=(0, -1), seat_Y=0.46)
        S['hall_near'] = _mk_spot(v, 'hall_near', 1.3, 2.5, 0.0, 'stand', 'near end of the hall (the narrator stepping out of the office)', face=(0, 1))
        S['hall_mid'] = _mk_spot(v, 'hall_mid', 1.3, 14.0, 0.0, 'stand', 'the middle of the hall')
        S['office_door'] = _mk_spot(v, 'office_door', 0.35, 3.45, 0.0, 'stand', "the narrator's office door (west wall)", face=(1, 0))
        return S
    return dict(name='hosp_hall', R=HH_R, H=2.7, floor=dict(base='#a8aca4', kind='checker', ink='#949890', scale=1.4),
                walls=dict(paper='#c8d4cc', wains=1.1, wcol='#a8bcb4', trim='#8aa094', base_h=0.1, seed=39), art=art,
                ceil=dict(c='#d8dcd8', art=lambda p_, W, H: pat(p_, W, H, 'tile', '#b8bcb8', 200, scale=4.0)),
                lights=lights, pieces=pieces, glows=glows, spots=spots, shell_x=shell_x)


_dcam('dr_hosp_hall', 900, 500, 1.6, 1.3, 0.6, 0, _env(f=(1.0, 3.0)), 'down the long hospital hallway at night: pools of light, then dark, one plastic chair at the end', 'hosp_hall')
_dcam('dr_hosp_hall_chair', 3000, 520, 1.5, 1.3, 9.0, 0, _env(x=(910, 1010), y=(490, 570), zoom=(1.0, 1.05), f=(1.0, 1.5)),
      'telephoto on the last chair under the flickering light', 'hosp_hall')


def dr_hosp_hall(view='hall', on=(0, 3, 6), flicker_end=True, **kw):
    """The long hospital hallway at night (the narrator's, years later). view 'hall' | 'chair'. on = which ceiling lights
    burn (indices into HH_LIGHTS); the last one over the chair flickers."""
    o = dict(on=tuple(on))
    if flicker_end: o['end_fn'] = lambda t: dr_bus_flicker(t, 91)
    return _box_build(_hosp_hall_cfg(), 'dr_hosp_hall' + ('' if view == 'hall' else '_chair'), o, grade='dr_hall_night',
                      focus=(22.0 if view == 'chair' else None))


# ---------------------------------------------------------------------------------------------- the cardiologist's office (morning)
CD_R = (0.0, 3.6, 0.0, 3.4)
CD_DESK = Box(1.8, 2.05, 1.6, 0.8, 0.0, 0.75, 0)
CD_DOC = (1.8, 2.75)
CD_PAT = [(1.3, 1.25), (2.35, 1.25)]


def _cardio_cfg():
    def lights(o):
        sun = Lamp(kind='win', c='#ffd8a0', k=1.3, soft=16.0, panes=_panes_y(1.0, 2.6, 0.9, 2.1, 3.4), d=_norm3((0.35, -0.4, -1.0)))
        return '#9a928a', [sun, Lamp(1.8, 2.6, 1.7, 5.0, '#fff4e8', 0.7, (1.0, 0.6, 0.3), fall=1.3)], []

    def art(o):
        return {'west': lambda p_, W, H: (_poster_art(p_, 120, H - 190, 50, 64, 'heart'), _poster_art(p_, 200, H - 186, 44, 34, 'diploma')),
                'east': lambda p_, W, H: (_poster_art(p_, 140, H - 190, 44, 34, 'diploma'), _photo(p_, W, H, 220, H - 186, 40, 30, 'lake')),
                'front': lambda p_, W, H: _office_clock(p_, 140, H - 220, 13, 8, 5)}

    def pieces(o):
        def desk(pen, v):
            draw_parts(pen, v, table_parts(CD_DESK, '#7a4a2a', apron=0.15, legw=0.05))
            Y = CD_DESK.Y1
            dr_monitor(pen, v, CD_DESK.cx + 0.45, Y, CD_DESK.cy + 0.15, 180, 1.0, 'chart')
            dr_mug(pen, v, CD_DESK.cx - 0.25, Y, CD_DESK.cy - 0.25, '#f2f2ee', steam=1.0)
            dr_mug(pen, v, CD_DESK.cx + 0.05, Y, CD_DESK.cy + 0.1, '#3a6aa8', steam=0.8)
            dr_papers(pen, v, CD_DESK.cx - 0.5, Y, CD_DESK.cy, 3, seed=8)
            P = (CD_DESK.cx + 0.05, Y, CD_DESK.cy - 0.18)                    # the plastic heart model on its stand
            if v.d(P[0], P[2]) > 0.2:
                s = v.s(P[0], P[2]); px, py = v.p(*P)
                pen.fill(rect(px - 0.05 * s, py - 0.02 * s, 0.1 * s, 0.02 * s), '#2a2a2a')
                hh = union(oval(px - 0.03 * s, py - 0.11 * s, 0.045 * s, 0.05 * s), oval(px + 0.03 * s, py - 0.11 * s, 0.045 * s, 0.05 * s))
                hh = union(hh, poly([(px - 0.07 * s, py - 0.1 * s), (px + 0.07 * s, py - 0.1 * s), (px, py - 0.025 * s)]))
                pen.fill(hh, lit('#d84a4a', (P[0], Y + 0.1, P[2]), None)); pen.line(hh, 0.8)
                pen.line(smooth([(px, py - 0.15 * s), (px - 0.01 * s, py - 0.19 * s), (px + 0.03 * s, py - 0.2 * s)], False), max(1.0, 0.012 * s), '#4a6ad8')
        P = [Piece('desk', (CD_DESK.cx, 0.4, CD_DESK.cy), desk, block=CD_DESK.footprint()),
             Piece('doc_chair', (CD_DOC[0], 0.45, CD_DOC[1]), lambda pen, v: dr_office_chair(pen, v, CD_DOC[0], CD_DOC[1], 180), block=_circ(CD_DOC[0], CD_DOC[1], 0.3)),
             Piece('plant', (3.25, 0.4, 3.1), lambda pen, v: dr_plant(pen, v, 3.25, 3.1))]
        for i, (x, y) in enumerate(CD_PAT):
            P.append(Piece('pat_chair%d' % i, (x, 0.45, y), (lambda x_, y_: lambda pen, v: _kchair(pen, v, x_, y_, 180))(x, y), block=_circ(x, y, 0.25)))
        P.append(Piece('shelf', (0.25, 1.0, 1.7), lambda pen, v: bookcase(pen, v, Box(0.2, 1.7, 1.1, 0.32, 0.0, 1.9, 90))))
        return P

    def spots(v, o):
        S = {}
        S['doctor_chair'] = _mk_spot(v, 'doctor_chair', CD_DOC[0], CD_DOC[1] - 0.05, 0.0, 'seat', 'the cardiologist behind the desk (faces -y)', face=(0, -1), seat_Y=0.48)
        for i, (x, y) in enumerate(CD_PAT):
            S['patient_chair%d' % i] = _mk_spot(v, 'patient_chair%d' % i, x, y + 0.02, 0.0, 'seat', 'a chair facing the desk (+y): Ruth in chair 0, Mom in chair 1',
                                                face=(0, 1), seat_Y=0.46)
        S['desk_top'] = _mk_spot(v, 'desk_top', CD_DESK.cx, CD_DESK.cy, CD_DESK.Y1, 'surface', 'the desk top (two coffees, the heart model)')
        S['coffee'] = _mk_spot(v, 'coffee', CD_DESK.cx - 0.25, CD_DESK.cy - 0.25, CD_DESK.Y1, 'surface', "the coffee the cardiologist brought Ruth")
        return S
    return dict(name='cardio', R=CD_R, H=2.7, floor=dict(base='#b89a78', kind='boards', ink='#7a5a3a', scale=1.0, seed=7),
                walls=dict(paper='#e8e0cc', wains=0.9, wcol='#c8d8c8', trim='#f4efe0', seed=41), art=art,
                windows=[('back', (1.0, 3.4, 2.6, 3.4, 0.9, 2.1), (2, 2), '#f8f6f0')], ceil=dict(c='#f2efe8'),
                lights=lights, pieces=pieces, spots=spots)


_dcam('dr_cardio', 900, 500, 1.4, 3.35, 1.65, -88, _env(), "the cardiologist's office in the morning, from the side: Ruth and the doctor in profile across the desk, coffee", 'cardio')
_dcam('dr_cardio_ruth', 1000, 500, 1.35, 2.95, 2.9, -137, _env(), 'over the desk at 3/4 on Ruth (turn ~0.5)', 'cardio')


def _outside_morning(pen, v):
    pen.linear(rect(-800, -600, 3600, 2400), 0, v.h - 1.0 * v.S, 0, v.h + 40, [(0, '#8ab0d8'), (0.65, '#f0d8c0'), (1, '#ffe8c8')])
    vg = lifted(v, -8.0)
    for i, x in enumerate(np.arange(-14.0, 18.0, 3.6)):
        y = 20.0 + 4 * _h(i, 5)
        if vg.d(x, y) < 1: continue
        bx, by = vg.p(x, 0.0, y)
        pen.fill(oval(bx, by - 3.0 * vg.s(x, y), 2.4 * vg.s(x, y), 2.2 * vg.s(x, y)), '#8aaa6a')


def dr_cardio(view='side', **kw):
    """The cardiologist's office, that same morning (warm sun): view 'side' | 'ruth'."""
    return _box_build(_cardio_cfg(), 'dr_cardio' + ('' if view == 'side' else '_ruth'), dict(kw), outside=_outside_morning, grade='dr_morning')


# ====================================================================================================== the car interior
# Halverson's car from inside, on its own little plan (metres): x across (+x = the passenger's side; left-hand drive),
# y along the car (+y = forward), Y up from the cabin floor. Night and rain: parked in Ruth's driveway (speed 0, the dome
# light on for the pulse) or driving to Larkfield General (speed 1: streetlights pass, the wipers beat).
K_HW = 0.72                                                  # half the cabin's width
K_ROOF = 1.24
K_BELT = 0.64                                                # the window sills
K_SEAT_Y = 0.33                                              # the seat cushions' top
K_FRONT = {'driver': (-0.37, 0.0), 'passenger': (0.37, 0.0)}
K_BACK = {'back_l': (-0.38, -1.02), 'back_r': (0.38, -1.02)}
K_MIRROR = (0.0, 1.08, 0.5)                                  # the rear-view mirror's centre (x, Y, y)
K_WHEEL = (-0.37, 0.76, 0.5, 0.185)                          # the steering wheel: centre x, Y, y and radius
K_EYE = (0.37, 1.04, 0.06)                                   # the front passenger's (the narrator's) eye
K_WS = [(-0.66, 0.74, 1.0), (0.66, 0.74, 1.0), (0.56, 1.2, 0.48), (-0.56, 1.2, 0.48)]       # the windshield glass
K_RW = [(0.6, 0.82, -1.72), (-0.6, 0.82, -1.72), (-0.5, 1.2, -1.28), (0.5, 1.2, -1.28)]      # the rear window glass
K_SPEED = 13.0                                               # m/s on the way to the hospital
K_LAMP_GAP = 30.0
K_COL = dict(seat='#7a84a4', seat_d='#5c6686', trim='#4a5068', card='#666e8c', dash='#3c4052', liner='#b4b8c6', carpet='#30323e', body='#4a6e80')


def _k_seat_profile(part='back'):
    """A car seat's side view in two convex pieces (extrude needs convex profiles): the reclined back and the cushion,
    as (cm forward from the seat's rear, cm down from the top of the back at Y 0.9)."""
    if part == 'back': return [(0, 7), (3, 1), (9, 0), (14, 3), (27, 57), (14, 64), (11, 60)]
    return [(12, 57), (58, 54), (70, 55), (74, 62), (73, 74), (16, 78), (11, 70)]


def _k_seat_parts(x, y_rear, w=0.5, rests=None, tag='seat'):
    """A seat as Parts: the extruded profile (cushion + reclined back) and its headrests (x centres)."""
    P = []

    def body(pen, v):
        def cap(p_, W, H):
            p_.linear(rect(0, 0, W, H), 0, 0, W, 0, [(0, '#000000', 50), (0.5, '#000000', 0), (1, '#ffffff', 20)])
            p_.line(smooth([(12, 6), (22, 52), (62, 52)], False, 0.6), 0.9, '#000000', 90)         # the bolster seam
        for part in (('back', 'cushion') if v.hy > y_rear + 0.3 else ('cushion', 'back')):
            extrude(pen, v, (x - w / 2, 0.9, y_rear), (0.0, 0.0, 1.0), (0.0, -1.0, 0.0), _k_seat_profile(part), (w, 0.0, 0.0), K_COL['seat_d'], K_COL['seat'], cap)
        # the upholstery seams on the back's face and across the cushion
        if v.hy > y_rear + 0.2:
            sw_ = max(0.8, 0.006 * v.S / max(0.3, v.d(x, y_rear + 0.2)))
            xs = [x - w / 2 + 0.07, x + w / 2 - 0.07] + ([x] if w > 1.0 else [])
            for sx in xs:
                _seg3(pen, v, (sx, 0.86, y_rear + 0.145), (sx, 0.37, y_rear + 0.265), sw_, '#000000', 70, False)
                _seg3(pen, v, (sx, 0.355, y_rear + 0.3), (sx, 0.35, y_rear + 0.7), sw_, '#000000', 70, False)
            _seg3(pen, v, (x - w / 2 + 0.03, 0.62, y_rear + 0.205), (x + w / 2 - 0.03, 0.62, y_rear + 0.205), sw_, '#000000', 60, False)
    P.append(Part(fn=body, ref=(x, 0.5, y_rear + 0.32), tag=tag))
    for hx in (rests if rests is not None else (x,)):
        def rest(pen, v, hx=hx):
            for dx in (-0.06, 0.06):
                _seg3(pen, v, (hx + dx, 0.88, y_rear + 0.07), (hx + dx, 0.98, y_rear + 0.06), max(1.5, 0.012 * v.s(hx, y_rear)), lit('#8a909a', (hx, 0.95, y_rear), None))
            box_extrude(pen, v, Box(hx, y_rear + 0.06, 0.27, 0.11, 0.96, 1.14, 180), -0.135, 0.135, -0.055, 0.055, 0.96, 1.14,
                        lambda W, H: rounded_rect_pts(W, H, 5.0, 4.0), K_COL['seat'], K_COL['seat_d'])
        P.append(Part(fn=rest, ref=(hx, 1.05, y_rear + 0.06), tag=tag + '_rest'))
    return P


def _k_lamp_ys(t, speed, side):
    """The y (car frame) of the streetlights on one side (+1 right / -1 left) at time t: they slide back as the car drives."""
    off = (K_SPEED * speed * t + (0.0 if side > 0 else K_LAMP_GAP * 0.5)) % K_LAMP_GAP
    return [k * K_LAMP_GAP - off for k in range(-3, 5)]


def _k_pass_level(side, speed, base=0.0):
    """f(t) 0..1: how much of a passing sodium lamp falls into the cabin from one side."""
    if not speed:
        f = lambda t: base
        f.const = base
        return f

    def f(t):
        k = 0.0
        for y in _k_lamp_ys(t, speed, side):
            k = max(k, math.exp(-((y - 1.0) / 5.5) ** 2))
        return base + (1.0 - base) * k
    return f


def dr_car_outside(pen, v, t=0.0, speed=1.0, static=False):
    """The night outside the car windows. static=True: the sky, the wet road and the dark edge of town (cached);
    else the live part: the streetlights sliding past (their glow, pole and streak on the wet road) and a few lit windows."""
    H = v.h
    if static:
        pen.linear(rect(-900, -700, 3800, 2600), 0, H - 0.9 * v.S, 0, H, [(0, '#04060c'), (0.6, '#0a0e1a'), (1, '#1c1a26')])
        pen.linear(rect(-900, H, 3800, 2000), 0, H, 0, H + 0.6 * v.S, [(0, '#12141c'), (1, '#07080c')])
        rng = np.random.default_rng(31)
        pts = [(-900, H + 2)]
        x = -900.0
        while x < 2900:
            w = rng.uniform(60, 220); h = rng.uniform(0.02, 0.075) * v.S
            pts += [(x, H - h * 0.6), (x + w * 0.5, H - h), (x + w, H - h * 0.7)]
            x += w
        pts.append((2900, H + 2))
        pen.fill(poly(pts), '#06080e')
        pen.linear(rect(-900, H - 0.05 * v.S, 3800, 0.1 * v.S), 0, H - 0.05 * v.S, 0, H + 0.05 * v.S, [(0, '#3a3040', 0), (0.5, '#3a3040', 70), (1, '#3a3040', 0)])
        if v.fy > 0.2:                                                       # looking forward: the wet road in our own headlights
            G = -0.42
            q = [(-1.6, G, 2.4), (1.6, G, 2.4), (9.0, G, 46.0), (-9.0, G, 46.0)]
            pth = v.poly3(q)
            if not pth.isEmpty():
                a_, b_ = v.p(0.0, G, 3.0), v.p(0.0, G, 46.0)
                pen.linear(pth, a_[0], a_[1], b_[0], b_[1], [(0, '#fff2d6', 150), (0.35, '#fff2d6', 70), (1, '#fff2d6', 0)])
        return
    for side in (1, -1):
        for y in _k_lamp_ys(t, speed, side):
            x = side * 6.2
            if v.d3(x, 5.4, y) < 1.0: continue
            d = v.d3(x, 5.4, y)
            hx, hy = v.p(x, 5.4, y)
            if hx < -700 or hx > 2620: continue
            s = v.S / d
            bx, by = v.p(x + side * 1.4, 0.0 - 0.45, y)
            pen.seg((bx, by), (bx, hy), max(1.0, 0.1 * s), '#0c0e14', 220)
            pen.glow(hx, hy, 1.6 * s, D_SODIUM, 120)
            pen.glow(hx, hy, 0.4 * s, '#fff6e0', 230)
            gx, gy = v.p(x * 0.55, -0.45, y)
            pen.ellipse_glow(gx, gy, 3.2 * s, max(3.0, 0.5 * s), D_SODIUM, 55)
    if v.fy > 0.2:                                                          # the centre line running under the car
        G = -0.42
        for k in range(12):
            y0 = ((k * 9.0 - K_SPEED * speed * t) % 108.0) + 2.5
            pq = v.poly3([(-1.75, G, y0), (-1.6, G, y0), (-1.6, G, y0 + 3.2), (-1.75, G, y0 + 3.2)])
            if not pq.isEmpty(): pen.fill(pq, '#e8d890', int(150 * clamp(1.2 - y0 / 45.0, 0.0, 1.0)))
    dr_rain(pen, t, (-500, -400, 2900, 1800), 1.0, 21, 1.0 + 0.6 * speed, 0.1 + 0.25 * speed * (1.0 if abs(v.fx) > 0.5 else 0.0) * (-1.0 if v.fx < 0 else 1.0), '#a8b4cc', 30, 260, far=True)
    rng = np.random.default_rng(57)
    for i in range(7):                                                      # a few windows still lit, far back from the road
        side = 1 if i % 2 else -1
        y = ((i * 37.0 - K_SPEED * speed * t * 0.999) % 200.0) - 80.0
        x = side * rng.uniform(13.0, 19.0)
        if v.d3(x, 1.4, y) < 2.0: continue
        px, py = v.p(x, 1.4, y); s = v.S / v.d3(x, 1.4, y)
        pen.fill(rect(px - 0.5 * s, py - 0.45 * s, 1.0 * s, 0.9 * s), '#ffca80', 150)
        pen.glow(px, py, 1.2 * s, '#ffb060', 40)


def dr_car_glass_rain(pen, t, clip, bounds, k=1.0, speed=1.0, dirx=0.0, seed=7, c='#b8c8e8'):
    """Rain on the car's glass: fine beads; at speed they crawl back along the side windows (dirx = their screen direction)
    leaving short tails, a few rivulets run down. Live; clipped to the projected panes."""
    if k <= 0.01 or clip is None or clip.isEmpty(): return
    x0, y0, x1, y1 = bounds[0], bounds[1], bounds[2], bounds[3]
    W, H = max(1.0, x1 - x0), max(1.0, y1 - y0)
    rng = np.random.default_rng(seed)
    cv = pen.cv
    cv.save(); cv.clipPath(clip, skia.ClipOp.kIntersect, True)
    pen.fill(rect(x0, y0, W, H), '#0a1020', 46)                                   # the glass's tint
    n = int(clamp(W * H / 5200.0, 60, 520) * k)
    xs = rng.uniform(0, 1, n); ys = rng.uniform(0, 1, n); rs = rng.uniform(1.3, 3.4, n); vs = rng.uniform(0.3, 1.0, n)
    mv = 90.0 * speed
    for i in range(n):
        x = x0 + ((xs[i] * W + dirx * mv * vs[i] * t) % W)
        y = y0 + ((ys[i] * H + (12.0 + 30.0 * speed * (0.0 if dirx else 1.0)) * vs[i] * t * 0.4) % H)
        r = rs[i]
        if dirx and speed:
            pen.seg((x, y), (x - dirx * r * 5.0 * vs[i], y - r * 0.6), r * 0.7, c, 34)
        pen.fill(oval(x, y, r * 0.8, r), c, 70)
        pen.fill(oval(x - r * 0.25, y - r * 0.3, r * 0.3), '#ffffff', 90)
    for i in range(int(7 * k)):
        x = x0 + rng.uniform(0.04, 0.96) * W
        ph = (t * rng.uniform(0.08, 0.2) + rng.uniform(0, 1)) % 1.0
        ya, yb = y0 + H * max(0.0, ph - 0.25), y0 + H * ph
        pts = [(x + 6.0 * math.sin(yy * 0.03 + i) + dirx * (yy - ya) * 0.35 * speed, yy) for yy in np.linspace(ya, yb, 8)]
        pen.line(smooth(pts, False, 0.8), 1.6, c, 60)
        pen.fill(oval(pts[-1][0], pts[-1][1], 2.4, 3.2), c, 110)
    cv.restore()


def dr_wipers(pen, v, t=0.0, k=1.0, period=1.25):
    """The two wipers sweeping the windshield (k 0 = parked at the bottom)."""
    G = _norm3((0.0, 0.46, -0.52))
    ph = 0.5 * (1.0 - math.cos(2.0 * math.pi * (t / period))) if k > 0.01 else 0.0
    th = math.radians(8.0 + 96.0 * ph)
    for px in (-0.38, 0.22):
        P0 = (px, 0.765, 0.975)
        d = (math.cos(th), math.sin(th) * G[1], math.sin(th) * G[2])
        a_ = _add3(P0, d, 0.12); b_ = _add3(P0, d, 0.56)
        s = v.S / max(0.3, v.d3(*P0))
        _seg3(pen, v, P0, a_, max(1.2, 0.012 * s), '#0a0b0e', 255, False)
        _seg3(pen, v, a_, b_, max(1.8, 0.02 * s), '#0a0b0e', 255, False)


class DrCarCabin(Room):
    """The inside of Halverson's car (see the constants above). o: speed, dome, dash, wheel (draw the steering wheel), view."""
    name = 'car'
    poly = [(-K_HW, -1.7), (K_HW, -1.7), (K_HW, 1.0), (-K_HW, 1.0)]

    def lights(self, o):
        sp = o.get('speed', 1.0)
        amb = '#46507c'
        dash = [Lamp(-0.3, 0.82, 0.5, 1.9, '#8ad8d0', 0.8, fall=1.3), Lamp(0.2, 0.7, 0.6, 1.4, '#ffb070', 0.4, fall=1.4)]
        dome = [Lamp(0.0, 1.16, -0.25, 2.6, '#ffe2b8', 1.5, (1.0, 0.8, 0.3), fall=1.25)]
        sl = [Lamp(-1.5, 1.7, 0.3, 3.4, D_SODIUM, 1.25, fall=1.2)]
        sr = [Lamp(1.5, 1.7, 0.3, 3.4, D_SODIUM, 1.25, fall=1.2)]
        var = [('dash', dash, _kfn(o.get('dash', 1.0), 271)), ('dome', dome, _kfn(o.get('dome', 0.0), 272)),
               ('street_l', sl, _k_pass_level(-1, sp, 0.18)), ('street_r', sr, _k_pass_level(1, sp, 0.3 if not sp else 0.12))]
        fill = [Lamp(0.0, 1.05, 0.2, 3.4, '#7a88c4', 0.45, fall=1.1),                # the night through the windshield
                Lamp(0.0, 1.5, -2.3, 3.0, '#8a9ad8', 0.5, fall=1.2)]                 # and through the rear window (a rim on the headrests)
        return amb, fill, var

    def shell(self, pen, v, o):
        C = K_COL
        # floor and roof liner
        draw_face(pen, v, floor_face(-K_HW, K_HW, -1.72, 1.02, 0.0), lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'fabric', 0.5, 'overlay', 0.8), C['carpet'], ao=14)
        draw_face(pen, v, ceil_face(-K_HW, K_HW, -1.3, 0.5, K_ROOF), lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'fabric', 0.3, 'overlay', 0.6), C['liner'], ao=10)
        # the two side walls: door cards below the belt, pillars, the roof rail; the windows are holes
        for side in (-1, 1):
            a, b = ((-K_HW, -1.72), (-K_HW, 1.05)) if side < 0 else ((K_HW, 1.05), (K_HW, -1.72))
            F = wall_face(a, b, 0.0, K_ROOF)
            if not v.visible(F.O, F.n): continue
            W_ = 277.0

            def uu(y, side=side): return (y + 1.72) * 100.0 if side < 0 else (1.05 - y) * 100.0
            fr = [(uu(-0.26), 60), (uu(1.0), 60), (uu(0.47), 8), (uu(-0.26), 8)]
            rr = [(uu(-1.22), 60), (uu(-0.38), 60), (uu(-0.38), 8), (uu(-1.04), 8)]

            def art(p_, W, H, uu=uu):
                p_.fill(rect(0, 60, W, H - 60), C['card'])
                p_.linear(rect(0, 60, W, H - 60), 0, 60, 0, H, [(0, '#ffffff', 26), (0.3, '#000000', 0), (1, '#000000', 80)])
                for (y0, y1) in ((-1.26, -0.34), (-0.3, 0.98)):                       # the two doors: armrest, pull, speaker, shut lines
                    u0, u1 = sorted((uu(y0), uu(y1)))
                    p_.line(rrect(u0 + 2, 62, u1 - u0 - 4, H - 68, 4), 0.8, '#000000', 120)
                    ar = rrect(u0 + 12, 76, (u1 - u0) * 0.62, 9, 4)
                    p_.fill(ar, C['trim']); p_.line(ar, 0.6, '#000000', 160)
                    p_.fill(rrect(u0 + (u1 - u0) * 0.42, 68, 13, 3.4, 1.6), '#b8bcc4')
                    cx_ = u0 + (u1 - u0) * 0.76
                    p_.fill(oval(cx_, 100, 9), '#15171d')
                    for k in range(5): p_.line(oval(cx_, 100, 1.6 + k * 1.6), 0.4, '#3a3e48', 200)
                p_.fill(rect(0, 58.5, W, 3.0), '#12141a')                               # the belt-line rubber
            draw_face(pen, v, F, art, C['trim'], holes=[poly(fr), poly(rr)], ao=8)
        # the rear: the C pillars either side of the rear glass, the header over it
        for side in (-1, 1):
            q = [(side * K_HW, 0.82, -1.72), (side * 0.6, 0.82, -1.72), (side * 0.5, 1.2, -1.28), (side * K_HW, K_ROOF, -1.28)]
            pth = v.poly3(q)
            if not pth.isEmpty() and v.hy > -1.5: pen.fill(pth, lit(C['liner'], q[0], None, 0.7)); pen.line(pth, 0.8)
        hq = v.poly3([(-0.5, 1.2, -1.28), (0.5, 1.2, -1.28), (K_HW, K_ROOF, -1.28), (-K_HW, K_ROOF, -1.28)])
        if not hq.isEmpty() and v.hy > -1.2: pen.fill(hq, lit(C['liner'], (0, 1.22, -1.28), None, 0.75))
        shelf = v.poly3([(-K_HW, 0.82, -1.72), (K_HW, 0.82, -1.72), (K_HW, 0.82, -1.4), (-K_HW, 0.82, -1.4)])
        if not shelf.isEmpty() and v.cam_h > 0.82: pen.fill(shelf, lit('#262a34', (0, 0.82, -1.55), (0, 1, 0)))
        # the windshield's header and the A pillars seen from inside
        if v.hy < 0.9:
            for side in (-1, 1):
                _seg3(pen, v, (side * 0.69, 0.74, 1.0), (side * 0.59, 1.2, 0.48), max(3.0, 0.07 * v.S / max(0.3, v.d(side * 0.64, 0.74))), lit(C['trim'], (side * 0.6, 1.0, 0.7), None))
            _seg3(pen, v, (-0.58, 1.215, 0.48), (0.58, 1.215, 0.48), max(3.0, 0.05 * v.S / max(0.3, v.d(0.0, 0.48))), lit(C['trim'], (0, 1.2, 0.48), None))
        # the dome light
        dq = v.poly3([(-0.09, K_ROOF - 0.004, -0.31), (0.09, K_ROOF - 0.004, -0.31), (0.09, K_ROOF - 0.004, -0.19), (-0.09, K_ROOF - 0.004, -0.19)])
        if not dq.isEmpty() and v.cam_h < K_ROOF: pen.fill(dq, lit('#8a8c94', (0.0, K_ROOF, -0.25), None, 0.7)); pen.line(dq, 0.8)

    def pieces(self, o):
        C = K_COL
        P = []
        view = o.get('view', 'front')
        for nm, (x, y) in K_FRONT.items():
            if view == 'back' or (view == 'driver' and nm == 'passenger'): continue      # the lens sits where these would be
            parts = _k_seat_parts(x, y - 0.38)
            P.append(Piece('seat_' + nm, (x, 0.5, y - 0.06), lambda pen, v, parts=parts: draw_parts(pen, v, parts), occupant=[(x, y)], front=parts,
                           block=_box_pts(x, y - 0.02, 0.25, 0.37)))
        bench = _k_seat_parts(0.0, -1.42, 1.4, rests=(-0.38, 0.38), tag='bench')
        P.append(Piece('bench', (0.0, 0.5, -1.1), lambda pen, v: draw_parts(pen, v, bench), occupant=list(K_BACK.values()), front=bench,
                       block=_box_pts(0.0, -1.05, 0.7, 0.37)))

        def console(pen, v):
            draw_box(pen, v, Box(0.0, 0.1, 0.2, 0.9, 0.0, 0.34, 180), {'all': C['dash'], 'top': '#2a2e38'})
            gx = (0.0, 0.34, 0.32)
            if v.d(gx[0], gx[2]) > 0.2:
                s = v.s(gx[0], gx[2])
                _seg3(pen, v, gx, (0.0, 0.5, 0.3), max(1.5, 0.018 * s), '#14161a')
                kx, ky = v.p(0.0, 0.52, 0.3); pen.fill(oval(kx, ky, 0.028 * s), '#2a2c34'); pen.line(oval(kx, ky, 0.028 * s), 0.8)
        if view != 'back': P.append(Piece('console', (0.0, 0.2, 0.1), console, block=_box_pts(0.0, 0.1, 0.1, 0.45)))
        if view == 'front':
            P.append(Piece('near_side', (0.9, 0.9, 0.3), lambda pen, v: dr_car_near_side(pen, v)))

        def dash(pen, v):
            B = Box(0.0, 0.83, 2 * K_HW, 0.4, 0.0, 0.74, 180)                  # the dash: its face toward the cabin (-y) is the box 'back'... fa 180: front faces +y

            def face(p_, W, H):
                p_.linear(rect(0, 0, W, H), 0, 0, 0, H, [(0, '#ffffff', 22), (0.25, '#000000', 0), (1, '#000000', 90)])
                # (art x runs from the passenger's side to the driver's as seen from the seats)
                cl = rrect(W - 62, 3, 44, 15, 6)                                   # the instrument cluster in front of the driver
                p_.fill(cl, '#0a0c10'); p_.line(cl, 0.6, '#000000', 220)
                for (cx_, r_) in ((W - 51, 6.0), (W - 31, 6.0)):
                    p_.line(oval(cx_, 10.5, r_), 0.8, '#7ae0d8', 220)
                    p_.seg((cx_, 10.5), (cx_ + r_ * 0.7, 10.5 - r_ * 0.5), 0.8, '#ff6a4a', 240)
                st = rrect(W / 2 - 13, 6, 26, 30, 3)                                # the centre stack: vents, the radio's clock
                p_.fill(st, '#0e1014'); p_.line(st, 0.6, '#000000', 220)
                p_.fill(rrect(W / 2 - 10, 9, 20, 6, 1.5), '#1a1c22')
                p_.fill(rrect(W / 2 - 10, 18, 20, 7, 1.5), '#0a1a18')
                btext(p_, o.get('clock', '4:07'), W / 2, 24, 'vhs', 7.5, '#7af0e0', 235, 'center')
                for k in range(3): p_.fill(oval(W / 2 - 7 + k * 7, 31, 2.0), '#2a2e38')
                gb = rrect(10, 16, 46, 20, 3)                                       # the glove box
                p_.line(gb, 0.7, '#000000', 150); p_.fill(rrect(30, 19, 7, 2.4, 1), '#3a3e48')
                for x_ in (6, W - 16): p_.fill(rrect(x_, 4, 10, 6, 2), '#0c0e12')    # the outer vents
            draw_box(pen, v, B, {'back': dict(fill=C['dash'], art=face), 'all': C['dash'], 'top': dict(fill='#262a34', art=lambda p_, W, H: p_.linear(
                rect(0, 0, W, H), 0, 0, 0, H, [(0, '#000000', 70), (1, '#ffffff', 14)]))})
            # the cowl over the cluster
            hq = v.poly3([(-0.6, 0.74, 0.64), (-0.14, 0.74, 0.64), (-0.18, 0.8, 0.72), (-0.56, 0.8, 0.72)])
            if not hq.isEmpty(): pen.fill(hq, lit('#1c1f28', (-0.37, 0.78, 0.68), (0, 0.5, -0.5))); pen.line(hq, 0.8)
        P.append(Piece('dash', (0.0, 0.5, 0.7), dash, block=_box_pts(0.0, 0.83, K_HW, 0.2)))
        if o.get('wheel', True):
            P.append(Piece('wheel', (K_WHEEL[0], K_WHEEL[1], K_WHEEL[2] - 0.02), lambda pen, v: dr_car_wheel(pen, v)))
        P.append(Piece('mirror', (K_MIRROR[0], K_MIRROR[1], K_MIRROR[2]), lambda pen, v: dr_car_mirror(pen, v, o)))
        return P

    def glows(self, v, o):
        kd = _kfn(o.get('dome', 0.0), 272)

        def dome(pen, t):
            k = kd(t)
            if k <= 0.01 or v.cam_h > K_ROOF: return
            dq = v.poly3([(-0.085, K_ROOF - 0.005, -0.305), (0.085, K_ROOF - 0.005, -0.305), (0.085, K_ROOF - 0.005, -0.195), (-0.085, K_ROOF - 0.005, -0.195)])
            if dq.isEmpty(): return
            pen.fill(dq, '#fff2d8', 235 * k)
            b = _rb(dq); pen.ellipse_glow((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, max(20.0, (b[2] - b[0]) * 1.2), max(12.0, (b[3] - b[1]) * 2.0), '#ffe2b8', 80 * k)
        return [('dome_glow', (0.0, K_ROOF, -0.25), dome)]

    def spots(self, v, o):
        S = {}
        for nm, (x, y) in K_FRONT.items():
            S[nm] = _mk_spot(v, nm, x, y, 0.0, 'seat', 'the %s seat (hip point; faces forward +y; seat top %.2f m above the cabin floor)' % (nm, K_SEAT_Y), face=(0, 1), seat_Y=K_SEAT_Y)
        for nm, (x, y) in K_BACK.items():
            S[nm] = _mk_spot(v, nm, x, y, 0.0, 'seat', 'the back seat, %s (back_r: Milo, behind the narrator; back_l: HIM, folded, behind the driver)' % ('left' if x < 0 else 'right'),
                             face=(0, 1), seat_Y=K_SEAT_Y)
        S['wheel'] = _mk_spot(v, 'wheel', K_WHEEL[0], K_WHEEL[2], K_WHEEL[1], 'point', 'the steering wheel hub')
        for nm, a in (('wheel_10', 150.0), ('wheel_2', 30.0)):
            P = _k_wheel_pt(math.radians(a))
            S[nm] = _mk_spot(v, nm, P[0], P[2], P[1], 'point', "the wheel rim at %s o'clock (her hands)" % nm.split('_')[1])
        S['mirror'] = _mk_spot(v, 'mirror', K_MIRROR[0], K_MIRROR[2], K_MIRROR[1], 'point', 'the rear-view mirror')
        S['roof_back_l'] = _mk_spot(v, 'roof_back_l', K_BACK['back_l'][0], K_BACK['back_l'][1], K_ROOF, 'point', 'the roof liner over the back-left seat (his head bends against it)')
        S['lap_back_r'] = _mk_spot(v, 'lap_back_r', K_BACK['back_r'][0], K_BACK['back_r'][1] + 0.2, K_SEAT_Y + 0.14, 'surface', "Milo's lap / wrist on the back seat")
        S['narrator_eye'] = _mk_spot(v, 'narrator_eye', K_EYE[0], K_EYE[2], K_EYE[1], 'point', "the narrator's eye (front passenger): looks up-left at the mirror")
        return S


def dr_car_near_side(pen, v):
    """The passenger side of the car from outside (for the lens at the passenger's window): the door skins, the roof and
    the pillars with the two window openings (no glass in them: the faces must read), the door mirror."""
    col_ = K_COL['body']
    F = wall_face((0.9, -2.4), (0.9, 2.05), -0.25, 1.3)
    def uu(y): return (y + 2.4) * 100.0
    def bb(Y): return (1.3 - Y) * 100.0
    shape = poly([(uu(-2.36), bb(0.3)), (uu(-2.34), bb(0.72)), (uu(-1.8), bb(0.86)), (uu(-1.32), bb(1.275)), (uu(0.44), bb(1.285)), (uu(1.04), bb(0.74)),
                  (uu(1.9), bb(0.58)), (uu(1.99), bb(0.4)), (uu(1.99), bb(-0.25)), (uu(-2.36), bb(-0.25))])
    fr = poly([(uu(-0.24), bb(0.67)), (uu(0.97), bb(0.67)), (uu(0.5), bb(1.19)), (uu(-0.24), bb(1.19))])
    rr = poly([(uu(-1.2), bb(0.67)), (uu(-0.36), bb(0.67)), (uu(-0.36), bb(1.19)), (uu(-1.0), bb(1.19))])

    def art(p_, W, H):
        p_.linear(rect(0, 0, W, H), 0, 0, 0, H, [(0, '#ffffff', 50), (0.12, '#ffffff', 0), (0.5, '#000000', 0), (1, '#000000', 90)])
        p_.fill(rect(0, bb(0.665), W, 2.4), '#12141a')                                   # the belt-line rubber
        p_.fill(rect(0, bb(0.63), W, 1.2), '#b8c8e8', 90)                                # the wet shoulder line
        for y_ in (-1.26, -0.3, 1.0):
            p_.seg((uu(y_), bb(0.66)), (uu(y_), bb(-0.2)), 1.0, '#000000', 150)
        p_.fill(rect(uu(-0.36), bb(1.19), 12, bb(0.67) - bb(1.19)), '#101216')           # the B pillar (black-out)
        for y_ in (-0.5, 0.72):
            hd = rrect(uu(y_), bb(0.56), 12, 3.0, 1.4)
            p_.fill(hd, '#c8ccd0'); p_.line(hd, 0.5, '#000000', 160)
        mr = rrect(uu(0.78), bb(0.86), 21, 14, 4)                                        # the door mirror
        p_.fill(mr, _darken(col_, 0.2)); p_.line(mr, 0.8, '#000000', 200)
        for w_ in (fr, rr): p_.line(w_, 1.6, '#0c0e12', 255)
        rng = np.random.default_rng(4)                                                   # beads of rain on the paint
        for i in range(160):
            x_, y_ = rng.uniform(0, W), rng.uniform(bb(1.28), bb(0.3))
            p_.fill(oval(x_, y_, 0.35, 0.5), '#c8d8f0', 70)
    draw_face(pen, v, F, art, col_, holes=[fr, rr], shape=shape, ao=False, lw=1.4)


def _k_wheel_pt(a, r=None):
    """A point on the steering wheel rim: a = angle (rad) from 3 o'clock, counter-clockwise seen from the driver."""
    x, Y, y, R = K_WHEEL
    r = R if r is None else r
    up = _norm3((0.0, 0.9, 0.42))                                # the wheel plane leans toward the dash at the top
    return (x + math.cos(a) * r, Y + math.sin(a) * r * up[1], y + math.sin(a) * r * up[2])


def dr_car_wheel(pen, v):
    """The steering wheel on its column: a thick rim, three spokes, the horn pad."""
    x, Y, y, R = K_WHEEL
    if v.d(x, y) < 0.15: return
    s = v.S / max(0.2, v.d(x, y))
    _seg3(pen, v, (x, Y - 0.02, y + 0.04), (x, Y - 0.1, y + 0.22), max(3.0, 0.07 * s), '#15171c')
    rim = [_k_wheel_pt(2 * math.pi * k / 28) for k in range(28)]
    q = _clip_near3(v, rim)
    if len(q) < 3: return
    pts = [v.p(*p_) for p_ in q]
    for a in (math.radians(180), math.radians(0), math.radians(270)):
        _seg3(pen, v, (x, Y, y), _k_wheel_pt(a, R * 0.95), max(2.0, 0.035 * s), '#1e2028', 255, False)
    pen.line(poly(pts), max(3.0, 0.036 * s) + 2.0, LINE)
    pen.line(poly(pts), max(3.0, 0.036 * s), '#2a2d36')
    pen.line(poly(pts), max(1.0, 0.008 * s), '#5a5e6a', 120)
    hx, hy = v.p(x, Y, y)
    hub = [v.p(*_k_wheel_pt(2 * math.pi * k / 14, R * 0.3)) for k in range(14)]
    pen.fill(poly(hub), '#22252d'); pen.line(poly(hub), 1.0)


def _k_mirror_frame(o=None):
    """The mirror glass as a Face tilted toward the front passenger: (Face, unit normal). The normal bisects the lines
    from the mirror to the narrator's eye and to the middle of the back seat, so that seat is what the narrator sees."""
    M = K_MIRROR
    E = (K_EYE[0], K_EYE[1], K_EYE[2]); T = (0.0, 0.92, -1.02)
    n = _norm3(_add3(_norm3(_sub3(E, M)), _norm3(_sub3(T, M))))
    Uu = _norm3(_cross3((0.0, 1.0, 0.0), n))                        # along the mirror's width
    if _dot3(Uu, (1.0, 0.0, 0.0)) > 0: Uu = _scale3(Uu, -1.0)        # art x runs from +x (passenger) to -x: Uu x Vu = n
    Vu = _norm3(_cross3(n, Uu))
    if Vu[1] > 0: Vu = _scale3(Vu, -1.0)
    W, H = 25.0, 7.6
    O = _add3(_add3(M, Uu, -W / 200.0), Vu, -H / 200.0)
    return Face(O, Uu, Vu, W, H, n, 'front'), n


def k_reflect(P):
    """A cabin point mirrored in the rear-view mirror (where its reflection appears to be, behind the glass)."""
    F, n = _k_mirror_frame()
    d = _dot3(_sub3(P, K_MIRROR), n)
    return _add3(P, n, -2.0 * d)


def _k_mirror_uv(P, eye=K_EYE):
    """Mirror-frame (cm) position where cabin point P is seen reflected from `eye`."""
    F, n = _k_mirror_frame()
    Pr = k_reflect(P)
    E = (eye[0], eye[1], eye[2])
    dv = _sub3(Pr, E)
    den = _dot3(dv, n)
    if abs(den) < 1e-6: return None
    tt = _dot3(_sub3(K_MIRROR, E), n) / den
    X = _add3(E, dv, tt)
    return F.uv(X)


def dr_car_mirror(pen, v, o=None):
    """The rear-view mirror on its stalk: a dark shell; in its glass, the back seat as the narrator sees it (the bench
    and its headrests against the rain-streaked rear window). The film draws Milo and HIM into it at the 'mirror_*' spots,
    clipped to info['mirror_quad']."""
    F, n = _k_mirror_frame()
    M = K_MIRROR
    if v.d(M[0], M[2]) < 0.12: return
    s = v.S / max(0.15, v.d(M[0], M[2]))
    _seg3(pen, v, (M[0], M[1] + 0.02, M[2] + 0.01), (0.0, 1.2, 0.5), max(2.0, 0.02 * s), '#14161b')
    back = _clip_near3(v, [F.pt(-0.8, -0.8), F.pt(F.W + 0.8, -0.8), F.pt(F.W + 0.8, F.H + 0.8), F.pt(-0.8, F.H + 0.8)])
    if len(back) >= 3:
        bp = poly([v.p(*p_) for p_ in back])
        pen.fill(bp, '#101216'); pen.line(bp, 1.2)
    if not v.visible(F.O, F.n): return

    def art(p_, W, H):
        p_.fill(rect(0, 0, W, H), '#0a0c12')
        def U(P):
            q = _k_mirror_uv(P)
            return q if q is not None else (0.0, 0.0)
        rw = [U(P) for P in K_RW]
        p_.fill(poly(rw), '#0e1322')
        b = _rb(poly(rw))
        p_.linear(poly(rw), 0, b[1], 0, b[3], [(0, '#1a2440', 200), (1, '#0a0e18', 200)])
        rng = np.random.default_rng(9)
        p_.cv.save(); p_.cv.clipPath(poly(rw), skia.ClipOp.kIntersect, True)
        for i in range(2):
            gx, gy = rng.uniform(b[0] + 2, b[2] - 2), rng.uniform(b[1] + 0.5, b[3] - 1.2)
            p_.radial(None, gx, gy, 1.6, [(0, D_SODIUM, 150), (1, D_SODIUM, 0)])
        for i in range(60):
            x_, y_ = rng.uniform(b[0], b[2]), rng.uniform(b[1], b[3])
            p_.fill(oval(x_, y_, 0.07, 0.1), '#9ab0d8', 110)
        p_.cv.restore()
        p_.line(poly(rw), 0.12, '#000000', 220)
        # the bench's back and the two headrests against it
        top = [U((x_, 0.9, -1.36)) for x_ in (-0.72, -0.4, 0.0, 0.4, 0.72)]
        bot = [U((x_, 0.3, -1.1)) for x_ in (0.72, -0.72)]
        p_.fill(poly(top + bot), '#1e2334'); p_.line(poly(top, False), 0.1, '#000000', 200)
        for hx in (-0.38, 0.38):
            c0 = U((hx - 0.135, 1.14, -1.36)); c1 = U((hx + 0.135, 0.96, -1.36))
            x0, x1 = sorted((c0[0], c1[0])); y0, y1 = sorted((c0[1], c1[1]))
            hr = rrect(x0, y0, x1 - x0, y1 - y0, 0.35)
            p_.fill(hr, '#2a3048'); p_.line(hr, 0.1, '#000000', 200)
            p_.linear(hr, 0, y0, 0, y1, [(0, '#8a9ad8', 70), (0.4, '#8a9ad8', 0)])
        p_.linear(rect(0, 0, W, H), 0, 0, W, H, [(0, '#ffffff', 26), (0.3, '#ffffff', 0), (0.7, '#ffffff', 0), (1, '#ffffff', 16)])
    draw_face(pen, v, F, art, '#0a0c12', ao=False, unlit=True, lw=1.4)


def dr_car_ext_front(pen, v):
    """What the lens on the hood sees of the car itself: the bonnet, the cowl and the wiper spindles, the A pillars, the
    roof's leading edge and the door mirrors (the glass and the wipers are their own live layer)."""
    col_ = K_COL['body']
    hood = [(-0.8, 0.74, 1.04), (0.8, 0.74, 1.04), (0.76, 0.56, 1.95), (-0.76, 0.56, 1.95)]
    hp = v.poly3(hood)
    if not hp.isEmpty():
        pen.fill(hp, lit(col_, (0.0, 0.66, 1.5), (0.0, 1.0, 0.2)))
        b = _rb(hp)
        pen.linear(hp, 0, b[1], 0, b[3], [(0, '#b8c8e8', 60), (0.3, '#b8c8e8', 0), (1, '#000000', 60)])
        pen.line(hp, 1.2)
        for sx in (-0.42, 0.42):
            _seg3(pen, v, (sx, 0.735, 1.08), (sx * 0.9, 0.57, 1.93), 1.2, '#000000', 90, False)
    cowl = v.poly3([(-0.8, 0.74, 1.04), (0.8, 0.74, 1.04), (0.7, 0.745, 0.99), (-0.7, 0.745, 0.99)])
    if not cowl.isEmpty(): pen.fill(cowl, '#101216')
    for side in (-1, 1):
        s = v.S / max(0.3, v.d(side * 0.65, 0.8))
        pc = _darken(lit(col_, (side * 0.64, 1.0, 0.75), (side * 0.6, 0.3, 0.7)), 0.15)
        _seg3(pen, v, (side * 0.71, 0.74, 1.0), (side * 0.6, 1.215, 0.48), max(4.0, 0.085 * s), pc)
        fq = [(side * 0.8, 0.74, 1.04), (side * 0.71, 0.74, 1.0), (side * 0.6, 1.215, 0.48), (side * 0.76, 1.215, 0.3), (side * 0.9, 0.74, 0.5)]
        fp = v.poly3(fq)
        if not fp.isEmpty(): pen.fill(fp, _darken(pc, 0.25)); pen.line(fp, 1.0)
        mq = [(side * 0.86, 0.76, 0.86), (side * 1.07, 0.78, 0.86), (side * 1.07, 0.9, 0.86), (side * 0.88, 0.9, 0.86)]
        mp = v.poly3(mq)
        if not mp.isEmpty(): pen.fill(mp, _darken(pc, 0.2)); pen.line(mp, 1.0)
    s = v.S / max(0.3, v.d(0.0, 0.48))
    _seg3(pen, v, (-0.6, 1.225, 0.47), (0.6, 1.225, 0.47), max(4.0, 0.06 * s), _darken(lit(col_, (0.0, 1.22, 0.47), (0.0, 0.6, 0.6)), 0.1))


_dcam('dr_car_front', 1700, 520, 1.0, 2.25, 0.3, -90, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.1), f=(1.0, 1.5)),
      "the front seats from outside the passenger's window: the narrator near, Halverson at the wheel beyond; the car faces screen-right", 'car')
_dcam('dr_car_back', 640, 500, 0.98, 0.0, -0.1, 180, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.1), f=(1.0, 1.5)),
      'the back seat from between the front seats: Milo on screen-left (back_r), HIM folded on screen-right (back_l), the rear window behind', 'car')
_dcam('dr_car_mirror', 2500, 540, K_EYE[1], K_EYE[0], K_EYE[2], math.degrees(math.atan2(K_MIRROR[0] - K_EYE[0], K_MIRROR[2] - K_EYE[2])),
      _env(x=(920, 1000), y=(500, 580), zoom=(1.0, 1.06), f=(1.0, 1.4)), "the rear-view mirror from the narrator's seat: the back seat in the glass", 'car')
_dcam('dr_car_windshield', 1500, 440, 1.2, 0.0, 2.25, 180, _env(x=(900, 1020), y=(400, 500), zoom=(1.0, 1.1), f=(1.0, 1.5)),
      'through the windshield from the bonnet: Halverson driving on screen-right, the narrator on screen-left, the wipers beating', 'car')
_dcam('dr_car_driver', 900, 520, 1.02, 0.68, -0.1, -105, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.1), f=(1.0, 1.5)),
      "Halverson at the wheel from the passenger's side at 3/4 (the narrator's look at her): the wheel at the right edge, her window and the rain "
      'behind her, the back seat (HIM, back_l) over her shoulder on the left', 'car')


def dr_car(view='front', speed=1.0, dome=0.0, dash=1.0, wheel=True, wipers=None, rain=1.0, clock='4:07', **kw):
    """Inside Halverson's car at night in the rain. view 'front' (the two front seats from the passenger side), 'driver'
    (her at the wheel, 3/4, from the passenger seat), 'back' (the back seat), 'mirror' (the rear-view mirror close-up),
    'windshield' (both of them through the windshield from the bonnet). speed 1 = driving (streetlights pass, wipers), 0 =
    parked in the driveway; dome = the dome light (level spec: on while she takes Milo's pulse); wheel=False leaves the
    steering wheel to CH.draw_steering_wheel (info['wheel'] = its screen centre and radius). Anchors: driver, passenger,
    back_l, back_r (seats), wheel, wheel_10, wheel_2, mirror, roof_back_l, lap_back_r; in 'mirror': mirror_back_l /
    mirror_back_r (where the back-seat people appear in the glass: their ppm and seat_y are those of the reflection)."""
    v = cam('dr_car_' + view)
    if wipers is None: wipers = 1.0 if speed else 0.0
    o = dict(speed=speed, dome=dome, dash=dash, wheel=wheel, clock=clock, no_veil=True, tod='night', view=view)
    main = DrCarCabin()
    dyn = []
    lay = Layer(40.0, lambda pen, t: dr_car_outside(pen, v, t, speed), 'car_pass', blur=None)
    lay.order = ORDER_OUT - 1.0
    dyn.append(lay)
    amb, steady, var = main.lights(o)
    # the glass: tint, rain, the wipers on the windshield
    panes = []
    if v.hx > -K_HW: panes.append([(-K_HW, K_BELT, -1.22), (-K_HW, K_BELT, 0.98), (-K_HW, 1.16, 0.47), (-K_HW, 1.16, -1.04)])
    if v.hx < K_HW: panes.append([(K_HW, K_BELT, 0.98), (K_HW, K_BELT, -1.22), (K_HW, 1.16, -1.04), (K_HW, 1.16, 0.47)])
    if v.hy > -1.2: panes.append(K_RW)
    if view != 'windshield': panes.append(K_WS)
    if rain:
        clips = [pth for pth in (v.poly3(q) for q in panes) if not pth.isEmpty()]
        if clips:
            clip = clips[0]
            for p_ in clips[1:]: clip = union(clip, p_)
            cb = _rb(clip)
            gl_ = Layer(max(0.3, v.d(0.0, 0.0)), lambda pen, t: dr_car_glass_rain(pen, t, clip, cb, rain, speed, -v.ry if abs(v.ry) > 0.5 else 0.0), 'glass_rain', blur=None)
            gl_.order = ORDER_SHELL - 0.05
            dyn.append(gl_)
    if view != 'windshield' and v.hy < 0.9:
        wl = Layer(max(0.3, v.d(0.0, 0.8)), lambda pen, t: dr_wipers(pen, v, t, wipers), 'wipers', blur=None)
        wl.order = ORDER_SHELL - 0.04
        dyn.append(wl)
    sp = build_view('dr_car_' + view, v, main, o, outside=lambda pen, v_: dr_car_outside(pen, v_, static=True), grade='dr_car', dyn=dyn,
                    focus=max(0.6, v.d(0.0, 0.0)) if view != 'mirror' else 0.6, dof=0.7)
    if view == 'windshield':
        dq = v.d(0.0, 0.75)
        sp = sp.add(*blit(max(0.3, dq), lambda pen: dr_car_ext_front(pen, v), 'car_ext', 'drcar:ext:%s' % v.name, FRAME, '#3e4a76',
                          [Lamp(kind='dir', c='#9aa8e0', k=0.45, d=_norm3((0.3, -0.8, -0.5)))], [('street_l', var[2][1], var[2][2]), ('street_r', var[3][1], var[3][2])],
                          order=0.9))
        wsp = v.poly3(K_WS)

        def glass(pen, t):
            if wsp.isEmpty(): return
            b = _rb(wsp)
            pen.fill(wsp, '#0a1020', 70)
            pen.cv.save(); pen.cv.clipPath(wsp, skia.ClipOp.kIntersect, True)
            for side in (1, -1):                                             # the streetlights slide up the glass as reflections
                for y in _k_lamp_ys(t, speed, side):
                    u = (y + 40.0) / 80.0
                    if not (0.0 < u < 1.0): continue
                    gx = (b[0] + b[2]) / 2 + side * (b[2] - b[0]) * 0.28
                    gy = b[3] - (b[3] - b[1]) * (1.0 - u) * 1.2
                    pen.ellipse_glow(gx, gy, (b[2] - b[0]) * 0.16, (b[3] - b[1]) * 0.1, D_SODIUM, 46)
            pen.linear(None, b[0], b[1], b[2], b[3], [(0, '#9ab0d8', 30), (0.3, '#9ab0d8', 0), (0.75, '#9ab0d8', 0), (1, '#9ab0d8', 22)])
            pen.cv.restore()
            dr_car_glass_rain(pen, t, wsp, b, rain * 0.8, speed, 0.0, 9)
            dr_wipers(pen, v, t, wipers)
        gl = Layer(max(0.3, dq), glass, 'windshield', blur=None); gl.order = 1.0
        sp = sp.add(gl)
    # staging extras
    hx, hy = v.p(K_WHEEL[0], K_WHEEL[1], K_WHEEL[2])
    sp.info['wheel'] = dict(x=hx, y=hy, r=K_WHEEL[3] * v.S / max(0.2, v.d(K_WHEEL[0], K_WHEEL[2])), plan=K_WHEEL)
    sp.info['roof_y'] = {nm: v.p(x, K_ROOF, y)[1] for nm, (x, y) in list(K_FRONT.items()) + list(K_BACK.items())}
    F, n = _k_mirror_frame()
    if v.visible(F.O, F.n):
        sp.info['mirror_quad'] = [v.p(*c) for c in F.corners()]
        for nm, (x, y) in K_BACK.items():
            Pr = k_reflect((x, 0.0, y)); Ps = k_reflect((x, K_SEAT_Y, y))
            d = max(0.2, v.d3(*Pr))
            px, py = v.p(*Pr)
            s_ = v.spot(Pr[0], Pr[2], Pr[1], 'the reflection of %s in the rear-view mirror: draw the figure here (flipped left-right), clipped to '
                        'info["mirror_quad"]; ppm and seat_y are the reflection\'s' % nm, 'seat')
            s_.seat_y = v.p(*Ps)[1]
            s_.turn = 0.0
            sp.anchors['mirror_' + nm] = s_
        sp.info['mirror_roof_y'] = v.p(*k_reflect((K_BACK['back_l'][0], K_ROOF, K_BACK['back_l'][1])))[1]
    sp.info['note'] = ('The car faces screen-right in front / driver; in back and windshield the camera looks backward, so the driver\'s side is '
                       'screen-right. Seated figures: sp.anchors[seat], order = sp.order_at(x, y); the roof: info["roof_y"][seat].')
    return sp


# ====================================================================================================== Milo at 22: the morning run
# "He's twenty-two now. He checks his blood sugar on his phone, and he runs marathons." A riverside path at sunrise on its
# own plan (metres): the path runs along x (the runner goes +x), the river behind it (+y), the lens on the near verge.
RN_PATH = (-1.5, 1.5)                                        # the path's y range
RN_RAIL = 2.1                                                # the guard rail between the path and the river
RN_BANK = 62.0                                               # the far bank


class DrRunPath(Room):
    name = 'run'
    poly = [(-60.0, RN_PATH[0]), (60.0, RN_PATH[0]), (60.0, RN_PATH[1]), (-60.0, RN_PATH[1])]

    def lights(self, o):
        return '#a8948c', [Lamp(kind='dir', c='#ffcf98', k=0.95, d=_norm3((-0.5, -0.32, -0.8)))], []

    def shell(self, pen, v, o):
        H = v.h
        box = rect(-900, -700, 3800, 2600)
        pen.linear(box, 0, H - 1.0 * v.S, 0, H + 10, [(0, '#5a86c8'), (0.45, '#a8c0dc'), (0.8, '#ffd8b0'), (1, '#ffe8c0')])
        sun = sky_dir(v, 18.0, 5.0)
        if sun:
            pen.radial(None, sun[0], sun[1], 1.5 * v.S, [(0, '#fff6d8', 255), (0.12, '#ffe2a0', 190), (0.45, '#ffb878', 60), (1, '#ff9a6a', 0)], clip=False)
            pen.fill(oval(sun[0], sun[1], 0.09 * v.S), '#fffbe8')
        rng = np.random.default_rng(5)
        for i in range(9):
            q = sky_dir(v, rng.uniform(-170, 170), rng.uniform(8, 30))
            if q is None: continue
            w = rng.uniform(0.5, 1.1) * v.S
            _cloud(pen, q[0], q[1], w, w * 0.1, int(rng.integers(0, 999)), '#f2c8b0', '#fff2dc', 150)
        # the far hills and the far bank's trees (two hazy ridges)
        for (R, hgt, c_, seed) in ((420.0, 46.0, '#9aa8c4', 3), (190.0, 22.0, '#7a94a8', 7)):
            rng = np.random.default_rng(seed)
            pts = []
            for a in np.arange(-178.0, 180.0, 2.0):
                x, y = math.sin(math.radians(a)) * R, math.cos(math.radians(a)) * R
                if v.d(x, y) < 5.0: continue
                hh = hgt * (0.55 + 0.45 * math.sin(a * 0.07 + seed) * math.sin(a * 0.031 + 1.3 * seed)) + rng.uniform(0, hgt * 0.08)
                pts.append(v.p(x, max(2.0, hh), y))
            if len(pts) > 2:
                pts.sort(key=lambda q: q[0])
                pen.fill(poly([(pts[0][0], H + 4)] + pts + [(pts[-1][0], H + 4)]), c_)
        # the river: a broad band of light back to the far bank
        Fw = floor_face(-400.0, 400.0, RN_RAIL + 1.2, 400.0, -1.2)

        def water(p_, W, Hh):
            p_.linear(rect(0, 0, W, Hh), 0, 0, 0, Hh, [(0, '#d8b89a'), (0.04, '#a8b0c8'), (0.3, '#7a98bc'), (1, '#5a7aa8')])
        draw_face(pen, v, Fw, water, '#8aa0c0', ao=False, line=False, unlit=True)
        if sun:
            gx = sun[0]
            pen.linear(rect(gx - 0.22 * v.S, H, 0.44 * v.S, 0.3 * v.S), gx - 0.22 * v.S, 0, gx + 0.22 * v.S, 0, [(0, '#ffe2b0', 0), (0.5, '#ffe2b0', 70), (1, '#ffe2b0', 0)])
        # the near ground: grass both sides, the path
        Fg = floor_face(-400.0, 400.0, -60.0, RN_RAIL + 1.2, 0.0)

        def grass(p_, W, Hh):
            p_.texture(rect(0, 0, W, Hh), 'grunge', 0.5, 'overlay', 4.0)
        draw_face(pen, v, Fg, grass, '#6a8a4a', ao=False, line=False)

    def spots(self, v, o):
        S = {}
        S['runner'] = _mk_spot(v, 'runner', 0.0, 0.0, 0.0, 'stand', 'Milo, 22, running along the path (+x: screen-right in side; toward the lens in front)', face=(1, 0))
        S['runner_ahead'] = _mk_spot(v, 'runner_ahead', 3.0, 0.2, 0.0, 'stand', 'three metres further on', face=(1, 0))
        S['runner_behind'] = _mk_spot(v, 'runner_behind', -3.0, -0.2, 0.0, 'stand', 'three metres back', face=(1, 0))
        S['rail'] = _mk_spot(v, 'rail', 0.6, RN_RAIL, 0.9, 'point', 'the guard rail top (he stops, leans, checks his phone)')
        S['rail_stand'] = _mk_spot(v, 'rail_stand', 0.6, RN_RAIL - 0.45, 0.0, 'stand', 'standing at the rail, facing the river (+y)', face=(0, 1))
        return S


def _rn_scroll(pen, v, t, speed):
    """The path and everything that slides past a runner who stays in frame: the tarmac with its edge lines and the
    kilometre paint, the guard rail and its posts, the lamp posts, the bank's reeds and the young trees."""
    off = speed * t
    x_lo, x_hi = v.hx - 46.0, v.hx + 46.0
    # the path
    pq = v.poly3([(x_lo, 0.004, RN_PATH[0]), (x_hi, 0.004, RN_PATH[0]), (x_hi, 0.004, RN_PATH[1]), (x_lo, 0.004, RN_PATH[1])])
    if not pq.isEmpty():
        pen.fill(pq, lit('#8a8c94', (v.hx, 0.0, 0.0), (0, 1, 0)))
        b = _rb(pq); pen.linear(pq, 0, b[1], 0, b[3], [(0, '#ffd8a8', 90), (1, '#3a3a4a', 40)])
    for yy in (RN_PATH[0] + 0.12, RN_PATH[1] - 0.12):
        lq = v.poly3([(x_lo, 0.006, yy - 0.04), (x_hi, 0.006, yy - 0.04), (x_hi, 0.006, yy + 0.04), (x_lo, 0.006, yy + 0.04)])
        if not lq.isEmpty(): pen.fill(lq, '#f2ecd8', 170)
    k0 = math.floor((x_lo + off) / 6.0)
    for k in range(int(k0), int(k0) + 17):                                    # the centre dashes
        x = k * 6.0 - off
        dq = v.poly3([(x, 0.006, -0.05), (x + 2.2, 0.006, -0.05), (x + 2.2, 0.006, 0.05), (x, 0.006, 0.05)])
        if not dq.isEmpty(): pen.fill(dq, '#f2ecd8', 150)
    # long morning shadows of the rail posts across the path, the rail, the posts
    items = []
    k0 = math.floor((x_lo + off) / 2.4)
    for k in range(int(k0), int(k0) + 40):
        x = k * 2.4 - off
        items.append((v.d(x, RN_RAIL), 'post', x, k))
    k0 = math.floor((x_lo + off) / 23.0)
    for k in range(int(k0), int(k0) + 5):
        x = k * 23.0 - off + 12.0
        items.append((v.d(x, RN_RAIL + 0.75), 'tree', x, k))
        items.append((v.d(x + 11.5, RN_RAIL + 0.5), 'lamp', x + 11.5, k))
    for (d, kind, x, k) in sorted(items, key=lambda q: -q[0]):
        if d < 0.6: continue
        if kind == 'post':
            s = v.S / d
            sh = v.poly3([(x - 0.04, 0.007, RN_RAIL), (x + 0.04, 0.007, RN_RAIL), (x + 0.9, 0.007, RN_RAIL - 1.9), (x + 0.82, 0.007, RN_RAIL - 1.9)])
            if not sh.isEmpty(): pen.fill(sh, '#2a2a4a', 50)
            _seg3(pen, v, (x, 0.0, RN_RAIL), (x, 0.92, RN_RAIL), max(1.5, 0.07 * s), '#a8acb4')
        elif kind == 'tree':
            bx, by = v.p(x, 0.0, RN_RAIL + 0.75); s = v.S / d
            hh = (3.6 + 1.0 * _h(int(k), 3)) * s
            pen.seg((bx, by), (bx, by - hh * 0.5), max(1.5, 0.16 * s), '#5a4a3a')
            for (dx, dy, r, c_) in ((0, -0.62, 0.34, '#4a7a3a'), (-0.16, -0.5, 0.26, '#5a8a44'), (0.17, -0.52, 0.27, '#42703a'), (0.02, -0.82, 0.24, '#6a9a4c')):
                pen.fill(oval(bx + dx * hh, by + dy * hh, r * hh, r * hh * 0.92), c_)
            pen.fill(oval(bx - 0.12 * hh, by - 0.74 * hh, 0.14 * hh, 0.1 * hh), '#ffe8b0', 70)
        else:
            s = v.S / d
            _seg3(pen, v, (x, 0.0, RN_RAIL + 0.5), (x, 3.6, RN_RAIL + 0.5), max(1.5, 0.09 * s), '#3e424c')
            hx, hy = v.p(x, 3.7, RN_RAIL + 0.3)
            pen.fill(rrect(hx - 0.28 * s, hy - 0.07 * s, 0.56 * s, 0.14 * s, 0.05 * s), '#3a3e48')
    for (Y, w_) in ((0.9, 0.07), (0.5, 0.05)):                                # the two rails: true quads (they run past the lens)
        rq = v.poly3([(x_lo, Y - w_ / 2, RN_RAIL), (x_hi, Y - w_ / 2, RN_RAIL), (x_hi, Y + w_ / 2, RN_RAIL), (x_lo, Y + w_ / 2, RN_RAIL)])
        if not rq.isEmpty(): pen.fill(rq, '#b4b8c0'); pen.line(rq, 0.8, '#3a3a44', 200)
    # the kilometre paint on the tarmac: 21 K (he runs marathons)
    xk = ((30.0 - off) % 84.0) - 30.0 + v.hx
    for i, ch_ in enumerate('21K'):
        cq = [(xk + i * 0.6, 0.007, -0.9), (xk + i * 0.6 + 0.45, 0.007, -0.9), (xk + i * 0.6 + 0.45, 0.007, -0.35), (xk + i * 0.6, 0.007, -0.35)]
        if min(v.d(q[0], q[2]) for q in cq) < 0.6: continue
        m_, _ = fmat(v, (xk + i * 0.6, 0.007, -0.35), (0.01, 0.0, 0.0), (0.0, 0.0, -0.01))
        pen.cv.save(); pen.cv.concat(m_)
        btext(pen, ch_, 22, 50, 'sans_b', 56, '#f2ecd8', 170, 'center')
        pen.cv.restore()


_dcam('dr_run_side', 1300, 610, 1.25, 0.0, -6.5, 0, _env(x=(900, 1020), y=(560, 660), zoom=(1.0, 1.1), f=(1.0, 1.4)),
      'Milo at 22 running in profile (screen-right), the river and the sunrise behind him', 'run')
_dcam('dr_run_front', 1500, 600, 1.3, 7.2, -2.3, -72, _env(x=(900, 1020), y=(550, 650), zoom=(1.0, 1.1), f=(1.0, 1.4)),
      'he runs toward the lens at 3/4, the path and the rail receding behind him', 'run')
_dcam('dr_run_rail', 1700, 560, 1.35, 2.6, -1.9, -27, _env(x=(900, 1020), y=(510, 610), zoom=(1.0, 1.08), f=(1.0, 1.4)),
      'he stops at the rail and checks his blood sugar on his phone (3/4, the river behind)', 'run')


def dr_run(view='side', speed=3.4, **kw):
    """Milo at 22 on his morning run: a riverside path at sunrise (the doctors' world: warm and bright). view 'side'
    (profile; the scenery scrolls at `speed` m/s while he stays on anchors['runner']), 'front' (3/4 from ahead), 'rail' (he
    stops at the rail with his phone: speed 0). Anchors: runner, runner_ahead, runner_behind, rail, rail_stand."""
    v = cam('dr_run_' + view)
    if view == 'rail': speed = 0.0
    o = dict(tod='day', no_veil=True, speed=speed)
    main = DrRunPath()
    amb, steady, var = main.lights(o)

    def scroll(pen, t):
        with lighting(amb, steady, 1.0): _rn_scroll(pen, v, t, speed)
    lay = Layer(max(0.5, v.d(0.0, RN_RAIL)), scroll, 'run_scroll', blur=None)
    lay.order = ORDER_SHELL - 0.5
    fx_, fy_ = (0.6, RN_RAIL - 0.45) if view == 'rail' else (0.0, 0.0)
    sp = build_view('dr_run_' + view, v, main, o, outside=None, grade='dr_morning', dyn=[lay], focus=max(1.0, v.d(fx_, fy_)), dof=0.25)
    sp.info['note'] = 'Stage him with ST.stage_figure(sp, "milo22", "runner"); the ground scrolls under him (speed m/s), so his run cycle stays in place.'
    return sp


# ====================================================================================================== the outro: a lamp, a phone
# "Okay. Breathe. You can turn a light on now." A bedside corner (its own plan): the lamp, a phone face-up beside it, a
# glass of water, the bed's edge; the night outside the window is only night.
OU_R = (0.0, 3.2, 0.0, 3.0)
OU_STAND = Box(1.25, 2.72, 0.62, 0.44, 0.0, 0.62, 0)          # the nightstand against the back wall, facing -y
OU_BED = Box(2.45, 2.0, 1.3, 2.0, 0.0, 0.56, 0)               # the bed: its head against the back wall
OU_PHONE = (1.38, OU_STAND.Y1, 2.62)
OU_LAMP = (1.08, OU_STAND.Y1, 2.78)


def dr_cell(pen, v, P, state='off', t=0.0, name='Dr. Halverson', ang=12.0):
    """A phone lying face-up on a surface (P = x, Y, y): state 'off' | 'ring' (an incoming call: the name, the two
    buttons, the screen pulsing) | 'lock' (3:00 on the lock screen)."""
    x, Y, y = P
    if v.d(x, y) < 0.2: return
    a = math.radians(ang)
    U = (math.cos(a), 0.0, math.sin(a)); V = (math.sin(a), 0.0, -math.cos(a))          # art x along U, art y toward the viewer (-V... away = up the screen)
    O = (x - U[0] * 0.0375 - V[0] * 0.08, Y + 0.009, y - U[2] * 0.0375 - V[2] * 0.08)
    F = Face(O, U, V, 7.5, 16.0, (0.0, 1.0, 0.0), 'top')

    def art(p_, W, H):
        body = rrect(0, 0, W, H, 1.0)
        p_.fill(body, '#15171c')
        sc = rrect(0.35, 0.35, W - 0.7, H - 0.7, 0.75)
        if state == 'off':
            p_.fill(sc, '#0a0b0e'); p_.linear(sc, 0, 0, W, H, [(0, '#ffffff', 26), (0.4, '#ffffff', 0)])
        elif state == 'lock':
            p_.fill(sc, '#1a2440'); p_.linear(sc, 0, 0, 0, H, [(0, '#3a4a7a', 255), (1, '#141a2c', 255)])
            btext(p_, '3:00', W / 2, 5.4, 'sans', 2.6, '#f2f4f8', 240, 'center')
        else:
            pulse = 0.75 + 0.25 * math.sin(t * 6.0)
            p_.fill(sc, mix('#1c3a2c', '#2a5a40', pulse))
            p_.fill(oval(W / 2, 4.6, 1.5), '#e8f0e8'); p_.fill(oval(W / 2, 4.2, 0.6), '#5a8a6a'); p_.fill(oval(W / 2, 5.5, 1.0, 0.6), '#5a8a6a')
            btext(p_, name, W / 2, 8.0, 'sans_b', 0.95, '#ffffff', 245, 'center')
            btext(p_, 'incoming call', W / 2, 9.2, 'sans', 0.62, '#c8e8d0', 220, 'center')
            p_.fill(oval(1.9, 13.3, 0.95), '#e04a3a'); p_.fill(oval(W - 1.9, 13.3, 0.95 * (0.9 + 0.1 * pulse)), '#3ad06a')
    draw_face(pen, v, F, art, '#15171c', ao=False, unlit=state != 'off', lw=1.0, shape=rrect(0, 0, 7.5, 16.0, 1.0))


def _outro_cfg():
    def lights(o):
        amb = '#343a58'
        win = Lamp(kind='win', c='#8a9ad8', k=0.5, soft=12.0, panes=_panes_x(1.0, 2.0, 0.9, 2.0, 0.0), d=_norm3((1.0, -0.45, 0.2)),
                   only={'floor', 'wall', 'top', 'front', 'side'})
        lamp_ = [Lamp(OU_LAMP[0], OU_LAMP[1] + 0.42, OU_LAMP[2] - 0.06, 4.2, D_LAMP, 2.0, (1.0, 0.8, 0.9), fall=1.45)]
        scr = [Lamp(OU_PHONE[0], OU_PHONE[1] + 0.15, OU_PHONE[2], 1.3, '#9af0b8', 0.7, fall=1.4)]
        return amb, [win], [('lamp', lamp_, _kfn(o.get('lamp', 1.0), 281)), ('screen', scr, _kfn(o.get('screen', 0.0), 282))]

    def art(o):
        def back(p_, W, H):
            _photo(p_, W, H, 60, H - 196, 36, 46, 'kids')
            _photo(p_, W, H, 196, H - 190, 40, 30, 'lake')
        def west(p_, W, H):
            _photo(p_, W, H, 222, H - 190, 34, 44, 'milo')
        return {'back': back, 'west': west}

    def pieces(o):
        def stand(pen, v):
            draw_box(pen, v, OU_STAND, {'front': dict(fill='#7a4e30', art=lambda p_, W, H: (p_.texture(rect(0, 0, W, H), 'wood', 0.4, 'overlay', 0.8),
                                                                                           p_.line(rrect(4, 5, W - 8, 22, 2), 0.8, '#000000', 150), p_.fill(oval(W / 2, 16, 2.2), '#c8a060'),
                                                                                           p_.line(rrect(4, 31, W - 8, H - 36, 2), 0.8, '#000000', 150), p_.fill(oval(W / 2, 44, 2.2), '#c8a060'))),
                                        'top': dict(fill='#8a5a38', art=lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'wood', 0.4, 'overlay', 0.8)), 'all': '#6a4228'})
            dr_table_lamp(pen, v, OU_LAMP[0], OU_LAMP[2], OU_LAMP[1], 0.0, '#f2e4c4', '#5a8a8a')
            dr_cell(pen, v, OU_PHONE, o.get('phone', 'off') if not callable(o.get('phone')) else 'off')
            gx, gy = v.p(OU_STAND.cx + 0.22, OU_STAND.Y1, OU_STAND.cy - 0.1)                 # a glass of water
            if v.d(OU_STAND.cx + 0.22, OU_STAND.cy - 0.1) > 0.2:
                s = v.s(OU_STAND.cx + 0.22, OU_STAND.cy - 0.1)
                g = poly([(gx - 0.034 * s, gy - 0.12 * s), (gx + 0.034 * s, gy - 0.12 * s), (gx + 0.028 * s, gy), (gx - 0.028 * s, gy)])
                pen.fill(g, '#8a98a8', 60); pen.fill(poly([(gx - 0.032 * s, gy - 0.085 * s), (gx + 0.032 * s, gy - 0.085 * s), (gx + 0.028 * s, gy), (gx - 0.028 * s, gy)]), '#6a88a8', 80)
                pen.line(g, 0.9, '#3a4a5a', 200)
        P = [Piece('nightstand', (OU_STAND.cx, 0.4, OU_STAND.cy), stand, block=OU_STAND.footprint())]
        bp = bed_parts(OU_BED, 0.0, 'made')
        P.append(Piece('bed', (OU_BED.cx, 0.4, OU_BED.cy), lambda pen, v: draw_parts(pen, v, bp), block=OU_BED.footprint()))
        P.append(Piece('rug', (1.3, 0.0, 1.4), lambda pen, v: None))
        return P

    def glows(v, o):
        kl = _kfn(o.get('lamp', 1.0), 281)
        G = [('nightstand_glow', (OU_LAMP[0], OU_LAMP[1] + 0.4, OU_LAMP[2]), lambda pen, t: dr_lamp_glow(pen, v, OU_LAMP[0], OU_LAMP[2], OU_LAMP[1], kl(t)))]
        ph = o.get('phone', 'off')
        if callable(ph) or ph != 'off':
            G.append(('phone_live', (OU_PHONE[0], OU_PHONE[1], OU_PHONE[2] - 0.02), lambda pen, t: dr_cell(pen, v, OU_PHONE, ph(t) if callable(ph) else ph, t)))
        return G

    def spots(v, o):
        S = {}
        S['phone'] = _mk_spot(v, 'phone', OU_PHONE[0], OU_PHONE[2], OU_PHONE[1] + 0.01, 'surface', 'the phone on the nightstand (a hand picks it up)')
        S['lamp_switch'] = _mk_spot(v, 'lamp_switch', OU_LAMP[0] + 0.02, OU_LAMP[2] - 0.08, OU_LAMP[1] + 0.2, 'point', "the lamp's switch (a hand turns the light on)")
        S['bed_edge'] = _mk_spot(v, 'bed_edge', OU_BED.cx - OU_BED.w / 2 + 0.12, 2.1, 0.0, 'seat', 'sitting on the edge of the bed by the nightstand (faces -x)', face=(-1, 0), seat_Y=0.56)
        S['stand_top'] = _mk_spot(v, 'stand_top', OU_STAND.cx, OU_STAND.cy - 0.05, OU_STAND.Y1, 'surface', 'the nightstand top')
        S['floor'] = _mk_spot(v, 'floor', 1.3, 1.5, 0.0, 'stand', 'standing by the bed', face=(0, 1))
        return S
    return dict(name='outro', R=OU_R, H=2.6, floor=dict(base='#8a6a4a', kind='boards', ink='#5a4028', seed=9),
                walls=dict(paper='#c8b8a0', ink='#a88a6a', kind='ditsy', wains=0.0, trim='#efe6d4', seed=51, scale=1.2),
                windows=[('west', (0.0, 1.0, 0.0, 2.0, 0.9, 2.0), (2, 2), '#efe9dc')], art=art, ceil=dict(c='#e6dfd2'),
                lights=lights, pieces=pieces, glows=glows, spots=spots)


_dcam('dr_outro_table', 1050, 520, 1.15, 1.0, 0.75, 8, _env(), 'the bedside: the lamp, the phone beside it, the glass of water, the bed (the lamp comes on)', 'outro')
_dcam('dr_outro_phone', 1500, 540, 1.07, 1.4, 1.98, 2, _env(x=(920, 1000), y=(500, 580), zoom=(1.0, 1.06), f=(1.0, 1.4)),
      'close, looking down at the phone under the lamp ("if your phone rings at three in the morning... pick up")', 'outro', pitch=33.0)
_dcam('dr_outro_wide', 780, 500, 1.4, 0.45, 0.4, 32, _env(), 'the room: window, nightstand, bed', 'outro')


def _outside_plain_night(pen, v):
    dr_sky(pen, v, 'night')


def dr_outro(view='table', lamp=1.0, phone='off', **kw):
    """The outro's quiet set: a bedside table with a lamp (lamp = level spec: dict(on=t) turns the light on at t), a phone
    lying beside it (phone 'off' | 'lock' | 'ring' or f(t)), a glass of water, the bed. view 'table' | 'phone' | 'wide'.
    The empty medicine cabinet is ST.dr_bath('cabinet', cabinet=1.0, card=False)."""
    o = dict(lamp=lamp, phone=phone, screen=(lambda t: 1.0 if (phone(t) if callable(phone) else phone) != 'off' else 0.0) if (callable(phone) or phone != 'off') else 0.0)
    sp = _box_build(_outro_cfg(), 'dr_outro_' + view, o, outside=_outside_plain_night, grade='dr_night', rain=False)
    return sp


# ====================================================================================================== inserts
# Close-ups of the film's props, drawn flat in design space (1920 x 1080, margin for a camera drift). Every insert is
# ST.dr_insert(name, prop_kw=dict | f(t) -> dict, motion=f(t) -> (dx, dy, dscale, drot)); DR_INSERTS lists them.
_IBG = (-520, -420, 2960, 1920)
D_RULES = [(1, "If the doctor calls after midnight, don't ask what they found."),
           (2, "If they put you on hold, don't hang up. Ever."),
           (3, "Never say what hurts out loud after dark. He's listening."),
           (4, "If someone in a white coat knocks, don't open the door. Real doctors don't make house calls."),
           (5, "Nobody goes to the hospital before sunrise. It can wait."),
           (6, "If you see him sitting in the chair, take a number, and wait your turn."),
           (7, "Never, ever let him take your pulse.")]
D_SIGNS = ['Very thirsty.', 'Peeing a lot.', 'Tired.', 'Losing weight.', 'Sweet-smelling breath.', 'Breathing fast and deep.']
D_SIGNS_END = ["If you see these, don't wait.", "I'll be in my car."]
D_ADVICE = [("Something feels wrong?", "Say it out loud to someone you trust."),
            ("Always thirsty, always tired, peeing a lot, losing weight?", "Tell a doctor."),
            ("Chest pain. Trouble breathing. A face that droops. The worst headache of your life.", "Don't wait. Call your emergency number."),
            ("Ask questions.", "All of them."),
            ("A call feels strange?", "Hang up. Find the real number. Call back.")]


def _ibg(pen, c1, c2=None, vign=120):
    r = rect(*_IBG)
    if c2 is None: pen.fill(r, c1)
    else: pen.linear(r, 0, _IBG[1], 0, _IBG[1] + _IBG[3], [c1, c2])
    if vign: pen.radial(None, 960, 540, 1500, [(0, '#000000', 0), (0.55, '#000000', 0), (1, '#000000', vign)])


def _ins_drop(pen, path, dx=10, dy=18, a=100, blur=14):
    cv = pen.cv
    cv.save(); cv.translate(dx, dy); pen.fill(path, '#000000', a, blur=blur); cv.restore()


def _typed(pen, s, x, y, size=30, c='#2a2018', a=230, seed=0, font='mono', align='left'):
    """Typewriter text: each letter sits a hair off the line and takes the ribbon unevenly."""
    f = skia.Font(bfont(font), size)
    f.setSubpixel(True); f.setEdging(skia.Font.Edging.kAntiAlias)
    g = f.textToGlyphs(s); ws = f.getWidths(g)
    w = sum(ws)
    xx = x - (w / 2 if align == 'center' else (w if align == 'right' else 0.0))
    for i, (ch_, wd) in enumerate(zip(s, ws)):
        h = _h(i * 7 + seed * 131, 17)
        p = skia.Paint(Color=col(c, int(a * (0.72 + 0.28 * h))), AntiAlias=True)
        pen.cv.drawString(ch_, xx + (h - 0.5) * 0.6, y + (_h(i * 3 + seed, 5) - 0.5) * size * 0.07, f, p)
        if h > 0.86: pen.cv.drawString(ch_, xx + 0.9, y + 0.3, f, skia.Paint(Color=col(c, int(a * 0.3)), AntiAlias=True))
        xx += wd
    return w


def _tea_paper(pen, r, seed=1, edge=1.0, c=None):
    """Paper gone the colour of weak tea: fibres, foxing, darker edges, an old fold."""
    c = c or CARD_FACE
    b = _rb(r)
    pen.fill(r, c)
    pen.texture(r, 'paper', 0.55, 'multiply', 0.9)
    pen.texture(r, 'grunge', 0.22, 'multiply', 2.2)
    cv = pen.cv
    cv.save(); cv.clipPath(r, skia.ClipOp.kIntersect, True)
    cx_, cy_ = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    pen.radial(None, cx_, cy_, max(b[2] - b[0], b[3] - b[1]) * 0.72, [(0, '#8a5a20', 0), (0.62, '#8a5a20', 0), (1, '#6a4418', int(120 * edge))])
    rng = np.random.default_rng(seed)
    for i in range(26):
        fx, fy = rng.uniform(b[0], b[2]), rng.uniform(b[1], b[3])
        rr = rng.uniform(3, 16)
        pen.fill(_blob(fx, fy, rr, rr * rng.uniform(0.6, 1.0), 9, int(rng.integers(0, 99)), 0.35), '#7a4a1c', int(rng.uniform(14, 44)))
    pen.linear(None, b[0], b[1], b[2], b[3], [(0, '#ffffff', 40), (0.35, '#ffffff', 0), (1, '#3a2408', 40)])
    cv.restore()


def _tape(pen, x, y, w, h, rot=0.0, c='#e8d68a', a=190, torn=True, seed=0):
    """A strip of old yellowed tape (centre x, y)."""
    cv = pen.cv
    cv.save(); cv.translate(x, y); cv.rotate(rot)
    rng = np.random.default_rng(seed + 3)
    if torn:
        n = 7
        l = [(-w / 2 + rng.uniform(-3, 3), -h / 2 + h * k / n) for k in range(n + 1)]
        r_ = [(w / 2 + rng.uniform(-3, 3), h / 2 - h * k / n) for k in range(n + 1)]
        path = poly(l + r_)
    else:
        path = rect(-w / 2, -h / 2, w, h)
    pen.fill(path, '#000000', 40, blur=4)
    pen.fill(path, c, a)
    pen.linear(path, 0, -h / 2, 0, h / 2, [(0, '#ffffff', 60), (0.3, '#ffffff', 0), (1, '#8a6a20', 60)])
    pen.texture(path, 'grunge', 0.3, 'multiply', 1.0)
    pen.line(path, 1.0, '#6a5420', 90)
    cv.restore()


def _ins_card(pen, t, hl=0, show=7, back=False, reveal=1.0, bg='door', tilt=-1.4, torn=False, k=1.0, **kw):
    """The yellow rules card. Front: seven rules typed on a typewriter on paper the colour of weak tea, taped by its top
    corners inside the medicine cabinet's door (hl = rule lit by the lamp, show = rules shown). back=True: the back of
    the card in the narrator's light: the squares the tape left, and, in faded ink from 1979, the signature Doctor Later
    (reveal 0..1 brings the ink up). bg 'door' (the cabinet door's white enamel) | 'dark' (held in the dark)."""
    if bg == 'door':
        _ibg(pen, '#dfe4e6', '#b8c0c6', 90)
        pen.texture(rect(*_IBG), 'grunge', 0.2, 'multiply', 2.0)
        pen.linear(rect(*_IBG), 0, 0, 1920, 0, [(0, '#000000', 50), (0.2, '#000000', 0), (0.85, '#ffffff', 0), (1, '#ffffff', 40)])
        for (rx, ry) in ((140, 180), (1790, 860), (1700, 120)):                 # rust freckles in the enamel
            pen.fill(_blob(rx, ry, 9, 6, 9, rx, 0.4), '#8a4a20', 90)
        pen.fill(rect(_IBG[0], 1010, _IBG[2], 10), '#8a9298'); pen.fill(rect(_IBG[0], 1020, _IBG[2], 400), '#aab2b8')
    else:
        _ibg(pen, '#1a1c26', '#0c0d14', 160)
        pen.radial(None, 960, 500, 1100, [(0, '#ffe2b0', 60), (1, '#ffe2b0', 0)])
    W, H = 1180, 720
    x0, y0 = 960 - W / 2, 540 - H / 2 + 10
    cv = pen.cv
    cv.save(); cv.translate(960, 540); cv.rotate(tilt); cv.translate(-960, -540)
    card = rrect(x0, y0, W, H, 6)
    if torn:                                                                   # the top edge torn where it came off the tape
        rng = np.random.default_rng(12)
        top = [(x0 + W * k_ / 40, y0 + (rng.uniform(0, 9) if (k_ < 6 or k_ > 34) else rng.uniform(0, 2))) for k_ in range(41)]
        card = poly(top + [(x0 + W, y0 + H), (x0, y0 + H)])
    _ins_drop(pen, card, 8, 14, 110, 12)
    _tea_paper(pen, card, 3)
    ink = '#2a2018'
    if not back:
        _typed(pen, 'FOR WHEN THE DOCTOR CALLS AT NIGHT', x0 + W / 2, y0 + 78, 33, ink, 235, 1, align='center')
        cv.drawLine(x0 + W / 2 - 345, y0 + 90, x0 + W / 2 + 345, y0 + 90, skia.Paint(Color=col(ink, 170), AntiAlias=True, StrokeWidth=2.2))
        y = y0 + 150
        size, lh = 29, 39
        maxc = 57
        hls = hl if isinstance(hl, (tuple, list)) else ((hl,) if hl else ())
        for (n, txt) in D_RULES[:int(show)]:
            words = txt.split(' '); lines = []; cur = ''
            for w_ in words:
                t_ = (cur + ' ' + w_).strip()
                if len(t_) <= maxc: cur = t_
                else: lines.append(cur); cur = w_
            if cur: lines.append(cur)
            if n in hls:
                band = rrect(x0 + 44, y - 30, W - 88, lh * len(lines) + 10, 6)
                pen.fill(band, '#fff2c0', 120); pen.line(band, 1.2, '#b8862a', 110)
            _typed(pen, '%d.' % n, x0 + 62, y, size, ink, 240, n)
            for i, l_ in enumerate(lines):
                _typed(pen, l_, x0 + 122, y + i * lh, size, ink, 238 if n in hls else 225, n * 10 + i)
            y += lh * len(lines) + 19
    else:
        for (tx, ty) in ((x0 + 70, y0 + 34), (x0 + W - 70, y0 + 34)):          # where the tape was: paler squares, a shred left
            sq = rect(tx - 62, ty - 30, 124, 60)
            pen.fill(sq, '#f2e2b0', 110); pen.line(sq, 1.0, '#8a6a30', 70)
            _tape(pen, tx - 20, ty - 4, 60, 34, 6, a=150, seed=int(tx))
        a_ = int(255 * clamp(reveal, 0.0, 1.0))
        inkc = '#4a3620'
        btext(pen, 'Doctor Later', x0 + W / 2, y0 + H * 0.62, 'formal', 190, inkc, int(a_ * 0.72), 'center')
        fl = smooth([(x0 + 250, y0 + H * 0.72), (x0 + 520, y0 + H * 0.745), (x0 + 820, y0 + H * 0.725), (x0 + 960, y0 + H * 0.7)], False, 0.9)
        pen.line(fl, 3.2, inkc, int(a_ * 0.55))
        btext(pen, '1979', x0 + W - 120, y0 + H - 60, 'cursive', 56, inkc, int(a_ * 0.5), 'right')
        for k_ in range(7):                                                    # the typed side ghosting through the old paper
            pen.fill(rect(x0 + 90, y0 + 150 + k_ * 62, W - 220 - (k_ * 53) % 180, 3), '#5a4020', 26)
    cv.restore()
    if not back and bg == 'door' and not torn:
        cv.save(); cv.translate(960, 540); cv.rotate(tilt); cv.translate(-960, -540)
        _tape(pen, x0 + 70, y0 + 6, 150, 62, -8, seed=1); _tape(pen, x0 + W - 70, y0 + 6, 150, 62, 7, seed=2)
        cv.restore()


def _ins_phone(pen, t, state='hung', ring=None, cord='in', night=0.4, era='now', **kw):
    """The kitchen wall phone, close: the cream rotary set on the mint wallpaper, the handset hung on its cradle (state
    'hung' | 'off'), the coiled cord; ring = f(t) 0..1 (it shivers on the wall, the bell lines); cord 'out': the line cord
    hangs loose (pulled from the jack)."""
    rg = ring(t) if callable(ring) else (ring or 0.0)
    wall = DP['kit_wall'] if era != '1979' else '#e8d498'
    _ibg(pen, wall, None, 0)
    pat(pen, 1920, 1080, 'ditsy', DP['kit_ink'] if era != '1979' else '#d8a850', 150, 25, None, 3.0)
    body_c = '#efe3c4' if era != '1979' else '#d9a640'
    sh = 5.0 * rg * math.sin(t * 2 * math.pi * 20)
    cv = pen.cv
    # the line cord down the wall
    if cord == 'in':
        pen.line(smooth([(1010, 800), (1016, 960), (1004, 1200), (1010, 1500)], False, 0.8), 10, LINE, 200)
        pen.line(smooth([(1010, 800), (1016, 960), (1004, 1200), (1010, 1500)], False, 0.8), 7, '#c8c4bc')
    else:
        pen.line(smooth([(1010, 800), (1030, 930), (1150, 1010), (1260, 1060), (1330, 1150)], False, 0.9), 10, LINE, 200)
        pen.line(smooth([(1010, 800), (1030, 930), (1150, 1010), (1260, 1060), (1330, 1150)], False, 0.9), 7, '#c8c4bc')
    cv.save(); cv.translate(sh, 0)
    body = rrect(720, 200, 520, 620, 46)
    _ins_drop(pen, body, 16, 22, 110, 18)
    pen.fill(body, body_c)
    pen.linear(body, 720, 0, 1240, 0, [(0, '#ffffff', 70), (0.3, '#ffffff', 0), (1, '#000000', 60)])
    pen.linear(body, 0, 200, 0, 820, [(0, '#ffffff', 40), (0.2, '#ffffff', 0), (1, '#000000', 50)])
    pen.line(body, 4)
    # the dial
    dx_, dy_, dr = 1040, 560, 168
    pen.fill(oval(dx_ + 4, dy_ + 6, dr + 4), '#000000', 60, blur=6)
    pen.fill(oval(dx_, dy_, dr), _darken(body_c, 0.1)); pen.line(oval(dx_, dy_, dr), 3)
    for k_ in range(10):
        a = math.radians(-60 + k_ * 30)
        hx_, hy_ = dx_ + math.cos(a) * dr * 0.7, dy_ + math.sin(a) * dr * 0.7
        pen.fill(oval(hx_, hy_, dr * 0.14), '#f8f4ea'); pen.line(oval(hx_, hy_, dr * 0.14), 2.2)
        btext(pen, str((k_ + 1) % 10), hx_, hy_ + 9, 'sans_b', 26, '#3a3630', 220, 'center')
    pen.fill(oval(dx_, dy_, dr * 0.38), '#f8f4ea'); pen.line(oval(dx_, dy_, dr * 0.38), 2.2)
    btext(pen, '555-0179', dx_, dy_ + 9, 'sans_b', 25, '#3a3a3a', 220, 'center')
    pen.fill(rrect(dx_ + dr * 0.56, dy_ + dr * 0.34, 22, 78, 6), '#b8b0a0'); pen.line(rrect(dx_ + dr * 0.56, dy_ + dr * 0.34, 22, 78, 6), 2)
    # the cradle and the handset
    for cy_ in (300, 720):
        hook = rrect(742, cy_ - 22, 150, 44, 16)
        pen.fill(hook, _darken(body_c, 0.14)); pen.line(hook, 2.5)
    if state == 'hung':
        jig = 7.0 * rg * math.sin(t * 2 * math.pi * 17 + 1.0)
        cv.save(); cv.translate(jig, 0)
        hs = union(union(rrect(770, 240, 96, 150, 40), rrect(770, 630, 96, 150, 40)), rrect(792, 300, 52, 420, 20))
        _ins_drop(pen, hs, 12, 14, 90, 10)
        pen.fill(hs, _lighten(body_c, 0.05))
        pen.linear(hs, 770, 0, 866, 0, [(0, '#ffffff', 80), (0.4, '#ffffff', 0), (1, '#000000', 60)])
        pen.line(hs, 4)
        for cy_ in (300, 720):
            for i in range(7):
                a = 2 * math.pi * i / 6
                px_, py_ = (818, cy_) if i == 6 else (818 + math.cos(a) * 20, cy_ + math.sin(a) * 20)
                pen.fill(oval(px_, py_, 4.2), '#5a5040', 190)
        cv.restore()
        tail = [(818 + jig, 780), (800, 930), (850, 1010), (905, 900), (912, 822)]
        _coil2d(pen, tail, body_c)
    else:
        tail = [(912, 822), (900, 960), (760, 1100), (520, 1240)]
        _coil2d(pen, tail, body_c)
    cv.restore()
    if rg > 0.02:                                                              # the bell's lines
        for side in (-1, 1):
            for k_ in range(3):
                r_ = 380 + k_ * 46 + 16 * math.sin(t * 40 + k_)
                a0 = (200 if side < 0 else -20)
                arc = skia.Path(); arc.addArc(skia.Rect.MakeLTRB(980 - r_, 510 - r_, 980 + r_, 510 + r_), a0, 40)
                pen.line(arc, 7 - k_ * 1.5, '#3a3a3a', int(150 * rg * (1 - k_ * 0.25)))
    if night:
        pen.fill(rect(*_IBG), '#0c1230', int(190 * night))
        pen.radial(None, 700, 700, 1200, [(0, '#ffd8a0', int(60 * night)), (1, '#ffd8a0', 0)])


def _coil2d(pen, pts, c='#efe3c4', r=13.0, pitch=9.0):
    """A coiled handset cord along a 2D curve (screen px)."""
    path = smooth(pts, False, 0.9)
    m = skia.PathMeasure(path, False)
    L = m.getLength()
    n = max(8, int(L / pitch))
    P = []
    for i in range(n + 1):
        d = L * i / n
        pos, tan = m.getPosTan(d)
        nx, ny = -tan.y(), tan.x()
        o = math.sin(i * math.pi) * 0.0
        s_ = 1 if i % 2 == 0 else -1
        P.append((pos.x() + nx * r * s_, pos.y() + ny * r * s_))
    cp = smooth(P, False, 1.0)
    pen.line(cp, 7.5, LINE, 220); pen.line(cp, 4.6, c); pen.line(cp, 1.4, '#ffffff', 70)


def _ins_phone_counter(pen, t, music=1.0, night=0.35, **kw):
    """The receiver laid on the butter-yellow counter 'like a sleeping baby', its coiled cord trailing back to the wall;
    the hold music still coming out of it (music 0..1: small shivers of sound from the earpiece)."""
    _ibg(pen, DP['counter'], _darken(DP['counter'], 0.25), 60)
    pen.texture(rect(*_IBG), 'grunge', 0.3, 'multiply', 2.0)
    for i in range(40):                                                        # the counter's little boomerang flecks
        x, y = _h(i, 1) * 2400 - 240, _h(i, 2) * 1500 - 210
        pen.line(smooth([(x, y), (x + 14, y - 8), (x + 26, y + 3)], False), 3, ['#c8a04a', '#e8f0d8', '#b8c8a0'][i % 3], 120)
    pen.fill(rect(_IBG[0], _IBG[1], _IBG[2], 190 - _IBG[1]), '#f4f2ea'); pat(pen, 1920, 190, 'tile', '#d8d8d0', 255, 0, None, 3.0)   # the splash tiles
    pen.fill(rect(_IBG[0], 176, _IBG[2], 22), '#c8ccd0'); pen.line(rect(_IBG[0], 176, _IBG[2], 22), 2)
    body_c = '#efe3c4'
    _coil2d(pen, [(1500, -200), (1560, 120), (1420, 330), (1250, 470), (1195, 560)], body_c, 15, 10)
    cv = pen.cv
    cv.save(); cv.translate(940, 600); cv.rotate(-14)
    hs = union(union(rrect(-430, -86, 240, 172, 70), rrect(190, -86, 240, 172, 70)), rrect(-300, -46, 600, 92, 34))
    _ins_drop(pen, hs, 14, 30, 110, 22)
    pen.fill(hs, _lighten(body_c, 0.04))
    pen.linear(hs, 0, -86, 0, 86, [(0, '#ffffff', 90), (0.4, '#ffffff', 0), (1, '#000000', 80)])
    pen.line(hs, 5)
    for cx_ in (-310, 310):
        pen.fill(oval(cx_, 0, 70, 62), _darken(body_c, 0.06)); pen.line(oval(cx_, 0, 70, 62), 3)
        for i in range(7):
            a = 2 * math.pi * i / 6
            px_, py_ = (cx_, 0) if i == 6 else (cx_ + math.cos(a) * 30, math.sin(a) * 27)
            pen.fill(oval(px_, py_, 6.5), '#4a4234', 200)
    if music > 0.02:                                                           # the thin tune leaking from the earpiece
        for k_ in range(3):
            ph = (t * 0.9 + k_ / 3.0) % 1.0
            r_ = 90 + ph * 150
            arc = skia.Path(); arc.addArc(skia.Rect.MakeLTRB(-310 - r_, -r_, -310 + r_, r_), 150, 60)
            pen.line(arc, 6, '#5a4a2a', int(120 * music * (1 - ph)))
    cv.restore()
    if night:
        pen.fill(rect(*_IBG), '#0c1230', int(190 * night))
        pen.radial(None, 1500, 240, 900, [(0, '#ffd8a0', int(90 * night)), (1, '#ffd8a0', 0)])


def _ins_phone_cord(pen, t, night=0.5, **kw):
    """'The phone cord was lying on the kitchen floor': the line cord and its little clear plug on the checker tiles, the
    empty jack on the baseboard above it."""
    _ibg(pen, DP['floor_a'], None, 0)
    cv = pen.cv
    cv.save(); cv.translate(960, 760); cv.rotate(-18); cv.translate(-960, -760)
    S_ = 300
    for i in range(-6, 12):
        for j in range(-2, 8):
            if (i + j) % 2 == 0: pen.fill(rect(i * S_ - 300, 380 + j * S_, S_, S_), DP['floor_b'])
    cv.restore()
    pen.texture(rect(*_IBG), 'grunge', 0.25, 'multiply', 2.0)
    wall = rect(_IBG[0], _IBG[1], _IBG[2], 250 - _IBG[1])
    pen.fill(wall, DP['kit_wall']); pat(pen, 1920, 250, 'ditsy', DP['kit_ink'], 150, 25, None, 3.0)
    base = rect(_IBG[0], 250, _IBG[2], 150)
    pen.fill(base, '#ece6d6'); pen.linear(base, 0, 250, 0, 400, [(0, '#ffffff', 60), (0.2, '#ffffff', 0), (1, '#000000', 70)])
    pen.line(poly([(_IBG[0], 250), (_IBG[0] + _IBG[2], 250)], False), 3); pen.fill(rect(_IBG[0], 392, _IBG[2], 26), '#000000', 70, blur=10)
    jk = rrect(1180, 268, 150, 110, 10)                                         # the jack: empty
    pen.fill(jk, '#e4dcc8'); pen.line(jk, 3)
    pen.fill(rrect(1226, 300, 58, 46, 5), '#1a1a1a'); pen.fill(rect(1244, 336, 22, 12), '#1a1a1a')
    for sx in (1196, 1314): pen.fill(oval(sx, 323, 6), '#a8a090'); pen.line(oval(sx, 323, 6), 1.5)
    pts = [(760, -420), (790, 60), (700, 420), (430, 640), (560, 860), (900, 800), (1120, 700)]
    cord = smooth(pts, False, 0.9)
    cv.save(); cv.translate(6, 12); pen.line(cord, 16, '#000000', 80, blur=6); cv.restore()
    pen.line(cord, 15, LINE, 220); pen.line(cord, 10.5, '#c8c4bc'); pen.line(cord, 3, '#ffffff', 80)
    cv.save(); cv.translate(1120, 700); cv.rotate(-24)
    plug = rrect(-6, -26, 96, 52, 8)
    _ins_drop(pen, plug, 6, 10, 90, 8)
    pen.fill(plug, '#e8e8e0', 235); pen.linear(plug, 0, -26, 0, 26, [(0, '#ffffff', 120), (0.5, '#ffffff', 0), (1, '#000000', 50)])
    pen.line(plug, 3)
    for k_ in range(4): pen.fill(rect(54 + k_ * 9, -16, 4.5, 32), '#c8a040')
    pen.fill(poly([(10, -26), (52, -40), (60, -34), (24, -22)]), '#e8e8e0', 235); pen.line(poly([(10, -26), (52, -40), (60, -34), (24, -22)]), 2)
    cv.restore()
    if night:
        pen.fill(rect(*_IBG), '#0c1230', int(190 * night))
        pen.radial(None, 1300, 100, 1000, [(0, '#ffd8a0', int(70 * night)), (1, '#ffd8a0', 0)])


def _ins_badge(pen, t, wet=1.0, swing=None, **kw):
    """Doctor Halverson's hospital badge clipped crooked to the pocket of her wet raincoat: LARKFIELD GENERAL, her photo,
    Dr. Anna Halverson, PEDIATRICS, and two dinosaur stickers stuck on by patients."""
    coat = '#5a6a4a'
    _ibg(pen, coat, _darken(coat, 0.35), 110)
    pen.texture(rect(*_IBG), 'fabric', 0.55, 'overlay', 1.6)
    pen.line(smooth([(300, -400), (360, 300), (330, 1500)], False), 9, _darken(coat, 0.4), 200)                 # the coat's front edge
    pk = poly([(520, 300), (1560, 250), (1600, 1500), (500, 1500)])                                               # the breast pocket flap
    pen.fill(pk, _lighten(coat, 0.05)); pen.line(pk, 5, _darken(coat, 0.5))
    pen.dashed(poly([(540, 330), (1545, 282)], False), 3, _darken(coat, 0.45), 200, 16, 10)
    sw = (swing(t) if callable(swing) else (swing or 0.0))
    cv = pen.cv
    cv.save(); cv.translate(1000, 300); cv.rotate(-7.5 + sw)
    clip_ = rrect(-60, -66, 120, 110, 12)
    pen.fill(clip_, '#b8bcc4'); pen.linear(clip_, 0, -66, 0, 44, [(0, '#ffffff', 120), (0.5, '#ffffff', 0), (1, '#000000', 80)]); pen.line(clip_, 4)
    pen.fill(rrect(-30, 30, 60, 70, 8), '#3a3e46'); pen.line(rrect(-30, 30, 60, 70, 8), 3)
    W, H = 640, 440
    card = rrect(-W / 2, 90, W, H, 26)
    _ins_drop(pen, card, 10, 18, 120, 14)
    pen.fill(card, '#f6f6f2'); pen.line(card, 4)
    cv.save(); cv.clipPath(card, skia.ClipOp.kIntersect, True)
    pen.fill(rect(-W / 2, 90, W, 96), '#1e6a8a')
    btext(pen, 'LARKFIELD GENERAL', -W / 2 + 34, 152, 'sans_b', 44, '#ffffff', 245, 'left', spacing=0.03)
    pen.fill(rect(W / 2 - 96, 106, 64, 64), '#ffffff'); pen.fill(rect(W / 2 - 72, 112, 16, 52), '#d8423a'); pen.fill(rect(W / 2 - 90, 130, 52, 16), '#d8423a')
    ph = rrect(-W / 2 + 34, 216, 190, 232, 10)                                                                    # her photo
    pen.fill(ph, '#c8d8e4')
    cv.save(); cv.clipPath(ph, skia.ClipOp.kIntersect, True)
    px_, py_ = -W / 2 + 129, 330
    pen.fill(oval(px_, py_ + 150, 110, 90), '#5a9ac8')                                                            # scrubs
    pen.fill(rect(px_ - 22, py_ + 40, 44, 50), '#e8bfa4')
    pen.fill(oval(px_, py_ - 62, 34, 28), '#b8904a')                                                              # the messy bun
    pen.fill(oval(px_, py_, 62, 72), '#f0c8ac')
    hair = smooth([(px_ - 66, py_ + 6), (px_ - 60, py_ - 56), (px_, py_ - 82), (px_ + 60, py_ - 56), (px_ + 66, py_ + 6), (px_ + 44, py_ - 30), (px_, py_ - 44), (px_ - 44, py_ - 30)], True, 0.7)
    pen.fill(hair, '#b8904a')
    for ex in (-22, 22): pen.fill(oval(px_ + ex, py_ - 2, 6, 7), '#4a3020')
    pen.line(smooth([(px_ - 20, py_ + 30), (px_, py_ + 40), (px_ + 20, py_ + 30)], False), 4, '#8a4a3a')
    for (fx, fy) in ((-30, 14), (-18, 18), (20, 15), (31, 12)): pen.fill(oval(px_ + fx, py_ + fy, 2.4), '#c8946a')
    cv.restore(); pen.line(ph, 3)
    btext(pen, 'Dr. Anna Halverson', -W / 2 + 248, 282, 'sans_b', 37, '#1a2a3a', 245)
    pen.fill(rrect(-W / 2 + 252, 312, 250, 50, 8), '#e8f2f6')
    btext(pen, 'PEDIATRICS', -W / 2 + 266, 349, 'sans_b', 34, '#1e6a8a', 245, spacing=0.05)
    for i in range(12): pen.fill(rect(-W / 2 + 254 + i * 13, 398, 5 + (i * 7) % 5, 44), '#1a1a1a')                # the barcode
    cv.restore()
    # the dinosaur stickers (one green long-neck, one orange T-rex: curling at a corner)
    for (sx, sy, kind, c_, rot) in ((W / 2 - 78, 478, 0, '#4aa86a', 14), (W / 2 - 196, 440, 1, '#e8823a', -11)):
        cv.save(); cv.translate(sx, sy); cv.rotate(rot)
        st = rrect(-58, -44, 116, 88, 20)
        pen.fill(st, '#000000', 50, blur=4); pen.fill(st, '#fffdf2'); pen.line(st, 2.5)
        cv.save(); cv.scale(4.4, 4.4); _dino_sil(pen, 0, 2, 9, kind, c_); cv.restore()
        cv.restore()
    cv.restore()
    if wet:                                                                     # rain on the coat and the badge
        rng = np.random.default_rng(8)
        for i in range(int(130 * wet)):
            x, y = rng.uniform(-200, 2100), rng.uniform(-150, 1250)
            r = rng.uniform(3, 9)
            pen.fill(oval(x, y, r * 0.8, r), '#dfeaf4', 60); pen.fill(oval(x - r * 0.25, y - r * 0.3, r * 0.3), '#ffffff', 150)
        for i in range(9):
            x = rng.uniform(100, 1800); y = rng.uniform(-100, 700); L = rng.uniform(120, 420)
            pen.line(smooth([(x, y), (x + 6, y + L * 0.5), (x - 4, y + L)], False), 4, '#dfeaf4', 60)
    pen.radial(None, 1500, 100, 1300, [(0, '#ffc888', 70), (1, '#ffc888', 0)])                                     # the porch light
    pen.fill(rect(*_IBG), '#0a1028', 60)


def _lab_sheet(pen, W=820, H=1060, show=8, marker=True, faint=1.0):
    """Milo's lab results as a sheet in its own px frame (0, 0)-(W, H): the printed report on top, and under it, in marker,
    in big careful letters, the warning signs (show = how many of the 8 marker lines are written)."""
    sheet = rect(0, 0, W, H)
    pen.fill(sheet, '#fbfaf5'); pen.texture(sheet, 'paper', 0.3, 'multiply', 0.8)
    ink = '#2a2e38'
    a = int(235 * faint)
    pen.fill(rect(40, 36, 46, 46), '#1e6a8a', a); pen.fill(rect(57, 42, 12, 34), '#ffffff', a); pen.fill(rect(46, 53, 34, 12), '#ffffff', a)
    btext(pen, 'LARKFIELD GENERAL', 100, 62, 'sans_b', 27, '#1e6a8a', a, spacing=0.03)
    btext(pen, 'Laboratory report', 100, 86, 'sans', 17, ink, int(a * 0.8))
    btext(pen, 'STAT', W - 46, 70, 'sans_b', 30, '#c8302a', a, 'right', spacing=0.08)
    pen.fill(rect(40, 100, W - 80, 2.5), ink, a)
    rows = [('Patient', 'MILO, 7 y'), ('Ordered by', 'A. HALVERSON, MD  Pediatrics'), ('Reported', '02:41')]
    for i, (k_, v_) in enumerate(rows):
        btext(pen, k_, 44, 132 + i * 26, 'sans', 17, ink, int(a * 0.7)); btext(pen, v_, 190, 132 + i * 26, 'sans_b', 17, ink, a)
    pen.fill(rect(40, 200, W - 80, 30), '#e4ecf0', a)
    for (x_, s_) in ((50, 'TEST'), (360, 'RESULT'), (560, 'RANGE')): btext(pen, s_, x_, 221, 'sans_b', 15, ink, int(a * 0.8), spacing=0.06)
    tests = [('GLUCOSE', '612 mg/dL', '70 - 140', True), ('KETONES', 'LARGE', 'negative', True), ('pH (venous)', '7.21', '7.32 - 7.42', True),
             ('BICARBONATE', '11 mmol/L', '22 - 29', True), ('SODIUM', '131 mmol/L', '135 - 145', False)]
    for i, (n_, r_, rg_, hi) in enumerate(tests):
        y = 258 + i * 31
        btext(pen, n_, 50, y, 'sans', 18, ink, a)
        btext(pen, r_, 360, y, 'sans_b', 20 if i == 0 else 18, '#c8302a' if hi else ink, a)
        btext(pen, rg_, 560, y, 'sans', 16, ink, int(a * 0.7))
        if hi: btext(pen, 'H' if i < 2 else 'L', 520, y, 'sans_b', 17, '#c8302a', a)
        pen.fill(rect(40, y + 9, W - 80, 1), ink, 40)
    if marker:
        mk = '#1c2c6a'
        circ = smooth([(346, 236), (500, 228), (538, 250), (500, 272), (350, 270), (336, 252)], True, 0.9)   # 612 ringed in marker
        pen.line(circ, 6, '#c8302a', 215)
        y0 = 474
        n = int(show)
        for i, s_ in enumerate(D_SIGNS[:max(0, min(6, n))]):
            y = y0 + i * 72
            pen.line(smooth([(52, y - 22), (64, y - 8), (86, y - 38)], False), 7, mk, 225)                  # a tick
            btext(pen, s_, 108, y, 'hand', 62, mk, 238, skew=-0.03)
        if n > 6:
            pen.fill(rect(48, y0 + 6 * 72 - 36, W - 96, 5), mk, 200)
            btext(pen, D_SIGNS_END[0], W / 2, y0 + 6 * 72 + 28, 'hand', 56, '#c8302a', 240, 'center')
            pen.line(smooth([(250, y0 + 6 * 72 + 42), (420, y0 + 6 * 72 + 47), (560, y0 + 6 * 72 + 41)], False), 6, '#c8302a', 220)
        if n > 7:
            btext(pen, D_SIGNS_END[1], W / 2, y0 + 6 * 72 + 96, 'hand', 52, mk, 238, 'center')
    pen.linear(sheet, 0, 0, W, H, [(0, '#ffffff', 0), (0.6, '#ffffff', 0), (1, '#8a8a7a', 50)])
    pen.line(sheet, 2.5, '#3a3a3a', 190)


def _ins_results(pen, t, show=8, slide=1.0, bg='floor', zoom='page', tilt=-3.0, **kw):
    """Milo's lab results with Doctor Halverson's marker note: 'Very thirsty. Peeing a lot. Tired. Losing weight.
    Sweet-smelling breath. Breathing fast and deep. If you see these, don't wait. I'll be in my car.' show = marker lines
    written (0..8: the six signs, then the two last lines); bg 'floor' (the hall floor: slide 0..1 brings the sheet in
    under the front door) | 'hand' (held up in the dark hall) | 'sink' (lying in the steel sink); zoom 'page' | 'note'
    (the marker lines fill the frame: legible at any size)."""
    cv = pen.cv
    if bg == 'floor':
        _ibg(pen, '#8a5a34', None, 0)
        cv.save(); cv.translate(960, 540); cv.rotate(90); cv.translate(-960, -540)
        pen.texture(rect(-800, -800, 3600, 2700), 'wood', 0.55, 'overlay', 1.2)
        cv.restore()
        for k_ in range(-3, 14): pen.fill(rect(k_ * 205 - 60, _IBG[1], 4, _IBG[3]), '#3a2412', 170)
        door = rect(_IBG[0], _IBG[1], _IBG[2], 150 - _IBG[1])
        pen.fill(door, '#e6e0d2'); pen.linear(door, 0, -420, 0, 150, [(0, '#000000', 0), (0.8, '#000000', 20), (1, '#000000', 90)])
        pen.fill(rect(_IBG[0], 150, _IBG[2], 20), '#0a0a0c')                                    # the gap under the door: the porch light in it
        pen.fill(rect(_IBG[0], 150, _IBG[2], 20), '#ffc888', 150)
        pen.linear(rect(_IBG[0], 170, _IBG[2], 330), 0, 170, 0, 500, [(0, '#ffc888', 120), (1, '#ffc888', 0)])
        pen.fill(rect(_IBG[0], 132, _IBG[2], 20), '#b8b0a0'); pen.line(poly([(_IBG[0], 152), (_IBG[0] + _IBG[2], 152)], False), 3)
    elif bg == 'sink':
        _sink_bg(pen)
    else:
        _ibg(pen, '#20222e', '#0e0f16', 150)
        pen.radial(None, 960, 420, 1200, [(0, '#ffd8a0', 70), (1, '#ffd8a0', 0)])
    W, H = 820, 1060
    if zoom == 'note':
        sc, ox, oy = 1.6, 960, 540 - (738 - H / 2) * 1.6
    elif bg == 'floor':
        sc, ox, oy = 0.85, 960, 622
    else:
        sc, ox, oy = 0.98, 960, 560
    if bg == 'floor':
        oy += -(1.0 - clamp(slide, 0.0, 1.0)) * (H * sc + 200)
    cv.save(); cv.translate(ox, oy); cv.rotate(tilt if zoom != 'note' else tilt * 0.4); cv.scale(sc, sc); cv.translate(-W / 2, -H / 2)
    _ins_drop(pen, rect(0, 0, W, H), 10 / sc, 16 / sc, 110, 14 / sc)
    _lab_sheet(pen, W, H, show)
    cv.restore()
    if bg == 'floor':                                                             # the door's bottom edge covers the part still outside
        pen.fill(rect(_IBG[0], _IBG[1], _IBG[2], 132 - _IBG[1]), '#e6e0d2')
        pen.linear(rect(_IBG[0], _IBG[1], _IBG[2], 150 - _IBG[1]), 0, -420, 0, 150, [(0, '#000000', 0), (0.8, '#000000', 20), (1, '#000000', 90)])
        pen.fill(rect(_IBG[0], 132, _IBG[2], 20), '#b8b0a0'); pen.line(poly([(_IBG[0], 152), (_IBG[0] + _IBG[2], 152)], False), 3)
        pen.fill(rect(*_IBG), '#0a1030', 70)


def _sink_bg(pen):
    """The kitchen's stainless sink from above: the yellow counter round it, one bowl, the drain."""
    _ibg(pen, DP['counter'], None, 0)
    pen.texture(rect(*_IBG), 'grunge', 0.3, 'multiply', 2.0)
    rim = rrect(150, 60, 1620, 960, 70)
    pen.fill(rim, '#c4c8ce'); pen.line(rim, 5)
    bowl = rrect(210, 120, 1500, 840, 90)
    pen.fill(bowl, '#8e949c')
    pen.radial(bowl, 960, 540, 900, [(0, '#b8bec6', 255), (0.7, '#8a9098', 255), (1, '#5e646c', 255)])
    pen.linear(bowl, 210, 120, 1710, 960, [(0, '#ffffff', 60), (0.3, '#ffffff', 0), (1, '#000000', 60)])
    for k_ in range(26): pen.line(poly([(260 + k_ * 56, 150), (240 + k_ * 56, 930)], False), 1.2, '#ffffff', 26)
    pen.line(bowl, 4, '#3a3e44')
    pen.fill(oval(1420, 300, 62), '#4a4e56'); pen.line(oval(1420, 300, 62), 4)
    for k_ in range(6):
        a = k_ * math.pi / 3
        pen.fill(oval(1420 + math.cos(a) * 30, 300 + math.sin(a) * 30, 8), '#16181c')
    pen.fill(oval(1420, 300, 9), '#16181c')


def _flame(pen, x, y, h, w, t, seed=0, a=235):
    """One flame (base x, y): a flickering tongue, yellow core, orange skin."""
    k1 = noise1(t * 7.0, seed); k2 = noise1(t * 9.0, seed + 7)
    tip = (x + w * 0.5 * k1, y - h * (0.85 + 0.25 * k2))
    out = smooth([(x - w * 0.5, y), (x - w * 0.42, y - h * 0.4), tip, (x + w * 0.4, y - h * 0.38), (x + w * 0.5, y)], True, 0.9)
    pen.fill(out, '#ff7a1e', int(a * 0.85)); pen.linear(out, 0, y - h, 0, y, [(0, '#ff3a10', 120), (0.5, '#ff9a2a', 0)])
    core = smooth([(x - w * 0.24, y), (x - w * 0.16, y - h * 0.3), (x + w * 0.2 * k1, y - h * 0.58), (x + w * 0.18, y - h * 0.28), (x + w * 0.24, y)], True, 0.9)
    pen.fill(core, '#ffe27a', a); pen.fill(oval(x, y - h * 0.1, w * 0.12, h * 0.1), '#fffbe0', a)


def _ins_burn(pen, t, burn=0.0, match=1.0, **kw):
    """'Grandma put the paper in the sink and lit it with a match.' The lab sheet in the steel sink, a lit match at its
    corner (match 0..1), the fire eating the sheet from that corner (burn 0..1; at 1 only curled ash is left). The
    flames flicker with t."""
    _sink_bg(pen)
    cv = pen.cv
    b = clamp(burn, 0.0, 1.0)
    W, H = 820, 1060
    sc = 0.7
    cv.save(); cv.translate(880, 560); cv.rotate(68); cv.scale(sc, sc); cv.translate(-W / 2, -H / 2)
    # the fire front: a ragged disc growing from the sheet's corner (W, H)
    R = 80 + b * 1500
    rng = np.random.default_rng(5)
    front = [(W + 60 + math.cos(a_) * R * (1 + 0.1 * rng.uniform(-1, 1)), H + 60 + math.sin(a_) * R * (1 + 0.1 * rng.uniform(-1, 1))) for a_ in np.linspace(0, 2 * math.pi, 40, endpoint=False)]
    burnt = smooth(front, True, 0.8) if b > 0.001 else None
    sheet = rect(0, 0, W, H)
    _ins_drop(pen, sheet, 12, 18, 110, 16)
    if burnt is not None:
        ash = inter(sheet, burnt)
        pen.fill(ash, '#1c1a18'); pen.texture(ash, 'grunge', 0.5, 'overlay', 1.0)
        for i in range(14):
            ax, ay = rng.uniform(0, W), rng.uniform(0, H)
            pen.line(smooth([(ax, ay), (ax + rng.uniform(-60, 60), ay + rng.uniform(-60, 60)), (ax + rng.uniform(-90, 90), ay + rng.uniform(-90, 90))], False), 2, '#4a4642', 120)
    cv.save()
    cv.clipPath(sheet, skia.ClipOp.kIntersect, True)
    if burnt is not None: cv.clipPath(burnt, skia.ClipOp.kDifference, True)
    _lab_sheet(pen, W, H, 8)
    if burnt is not None:                                                         # the scorched margin ahead of the fire
        for (w_, c_, a_) in ((150, '#6a4a20', 60), (90, '#3a2410', 120), (44, '#120c08', 220)):
            pen.line(burnt, w_, c_, a_, blur=w_ * 0.25)
    cv.restore()
    if burnt is not None:
        edge = skia.Path(burnt)
        cv.save(); cv.clipPath(sheet, skia.ClipOp.kIntersect, True)
        pen.line(edge, 9, '#ff8a2a', int(230 * (0.7 + 0.3 * noise1(t * 6, 3)))); pen.line(edge, 3.5, '#ffe9a0', 230)
        cv.restore()
    cv.restore()
    # flames along the fire front (in screen space, so they always rise)
    if 0.001 < b < 0.999:
        m = skia.Matrix(); m.setTranslate(880, 560); m.preRotate(68); m.preScale(sc, sc); m.preTranslate(-W / 2, -H / 2)
        vis = []
        for i, (fx, fy) in enumerate(front):
            if 0 <= fx <= W and 0 <= fy <= H:
                q = m.mapXY(fx, fy); vis.append((q.x(), q.y(), i))
        for (qx, qy, i) in sorted(vis, key=lambda q_: q_[1]):
            hh = (120 + 150 * _h(i, 3)) * (0.6 + 0.8 * math.sin(math.pi * b))
            _flame(pen, qx, qy, hh, hh * 0.5, t, i)
        if vis:
            cx_ = sum(q_[0] for q_ in vis) / len(vis); cy_ = sum(q_[1] for q_ in vis) / len(vis)
            pen.radial(None, cx_, cy_ - 60, 900, [(0, '#ffb060', 130), (1, '#ffb060', 0)])
    if match > 0.01 and b < 0.35:                                                 # the match at the corner
        mx, my = 1210, 880
        cv.save(); cv.translate(mx, my); cv.rotate(-38)
        pen.fill(rrect(0, -7, 330, 14, 4), '#e8d8a8', int(255 * match)); pen.line(rrect(0, -7, 330, 14, 4), 2.5, LINE, int(255 * match))
        pen.fill(rrect(-6, -9, 70, 18, 8), '#2a1a12', int(255 * match))
        pen.fill(oval(-8, 0, 17, 14), '#3a1410', int(255 * match))
        cv.restore()
        _flame(pen, mx - 12, my + 6, 150, 70, t, 91, int(240 * match))
        pen.radial(None, mx, my - 60, 520, [(0, '#ffc070', int(120 * match)), (1, '#ffc070', 0)])
    pen.fill(rect(*_IBG), '#0a1030', int(110 * (1 - 0.6 * math.sin(math.pi * b))))


def _ins_ticket(pen, t, text='MILO', old=0.0, bg='wait', tilt=4.0, number='', **kw):
    """A paper ticket from the take-a-number machine: text = what it says ('MILO', 'RUTH', or '' for Grandpa's: so old
    the ink is gone, only a ghost where it was); old 0..1 yellows and softens the paper; bg 'wait' (the sick green dark of
    the waiting room) | 'dawn' (the armchair's arm in the sunrise) | 'dark'."""
    if bg == 'wait':
        _ibg(pen, '#3c4630', '#141a10', 150); pen.radial(None, 960, 300, 1300, [(0, D_TUBE, 60), (1, D_TUBE, 0)])
    elif bg == 'dawn':
        _ibg(pen, DP['arm'], _darken(DP['arm'], 0.4), 120); pen.texture(rect(*_IBG), 'fabric', 0.6, 'overlay', 1.6)
        pen.radial(None, 300, 200, 1500, [(0, D_SUN, 110), (1, D_SUN, 0)])
    else:
        _ibg(pen, '#1e2028', '#0c0d12', 150)
    if not text: old = max(old, 0.85)
    paper = mix('#f6f0e2', '#cdb78a', old)
    W, H = 560, 760
    cv = pen.cv
    cv.save(); cv.translate(960, 550); cv.rotate(tilt); cv.translate(-W / 2, -H / 2)
    rng = np.random.default_rng(4)
    top = [(W * k_ / 28, (6 if k_ % 2 else 0) + rng.uniform(-1.5, 1.5)) for k_ in range(29)]                   # the torn perforation
    tk = poly(top + [(W, H - 14), (W - 14, H), (14, H), (0, H - 14)])
    _ins_drop(pen, tk, 10, 18, 120, 14)
    if old > 0.3: _tea_paper(pen, tk, 9, 0.8, paper)
    else:
        pen.fill(tk, paper); pen.texture(tk, 'paper', 0.35, 'multiply', 0.8)
    a = int(255 * (1 - 0.55 * old))
    red = mix('#c4201e', '#9a6a4a', old)
    band = inter(tk, rect(0, 0, W, 150))
    pen.fill(band, red, a)
    btext(pen, 'PLEASE TAKE A SEAT', W / 2, 96, 'sans_b', 38, paper, a, 'center', spacing=0.05)
    btext(pen, 'YOUR TURN', W / 2, 226, 'sans_b', 40, red, int(a * 0.9), 'center', spacing=0.12)
    pen.fill(rect(60, 250, W - 120, 4), red, int(a * 0.8))
    if text:
        size = 210 if len(text) <= 4 else 170
        btext(pen, text, W / 2 + 3, 470, 'head', size, red, 70, 'center', spacing=0.02)                        # the stamp's double strike
        btext(pen, text, W / 2, 466, 'head', size, '#1a1414', 235, 'center', spacing=0.02)
    else:
        btext(pen, '0000', W / 2, 466, 'head', 200, '#6a5430', 26, 'center', spacing=0.02)                       # a ghost of where the ink was
    pen.fill(rect(60, 520, W - 120, 4), red, int(a * 0.8))
    btext(pen, 'IT CAN WAIT', W / 2, 600, 'sans_b', 44, red, int(a * 0.85), 'center', spacing=0.1)
    btext(pen, 'No. ' + (number or ('%04d' % (1979 if not text else (7 if text == 'MILO' else 12)))), W / 2, 680, 'mono', 34, '#3a3028', int(a * 0.7), 'center')
    pen.linear(tk, 0, 0, W, H, [(0, '#ffffff', 40), (0.4, '#ffffff', 0), (1, '#000000', 50)])
    pen.line(tk, 3, '#2a2420', 200)
    cv.restore()


def _ins_sign(pen, t, digits='1979', k=1.0, flick=None, **kw):
    """NOW SERVING: 1979. The sign hung on its chains: red numbers that stopped moving a long time ago (k = glow;
    flick = f(t) 0..1 multiplies it: a tired segment stutter)."""
    kk = k * (flick(t) if callable(flick) else 1.0)
    _ibg(pen, '#4a5236', '#1c2214', 150)
    pat(pen, 1920, 1080, 'ditsy', '#6a6e4a', 120, 21, None, 3.2)
    pen.fill(rect(*_IBG), '#0c1008', 90)
    for cx_ in (520, 1400):
        pen.dashed(poly([(cx_, -420), (cx_, 250)], False), 12, '#6a6a66', 240, 26, 12)
        pen.dashed(poly([(cx_ + 5, -420), (cx_ + 5, 250)], False), 4, '#2a2a28', 200, 12, 26, 13)
    box = rrect(300, 240, 1320, 600, 16)
    _ins_drop(pen, box, 18, 30, 140, 26)
    pen.fill(box, '#141416'); pen.line(box, 6)
    pen.fill(rrect(330, 270, 1260, 540, 8), '#08080a')
    btext(pen, 'NOW SERVING', 960, 400, 'sans_b', 112, '#e8e4dc', 240, 'center', spacing=0.1)
    pen.fill(rect(420, 440, 1080, 5), '#3a3a3a')
    dh = 290.0
    dw = len(digits) * (dh * 0.52 + dh * 0.22) - dh * 0.22
    on = mix('#3a0c0a', '#ff2a1e', clamp(kk, 0, 1))
    _seg7_text(pen, digits, 960 - dw / 2 - 12, 480, dh, on, '#240a08')
    if kk > 0.02:
        pen.radial(None, 960, 625, 900, [(0, '#ff2a1e', int(90 * kk)), (1, '#ff2a1e', 0)], sy=0.5, clip=False)
    pen.linear(box, 300, 240, 1620, 840, [(0, '#ffffff', 30), (0.25, '#ffffff', 0), (1, '#000000', 40)])
    for (sx, sy) in ((330, 262), (1590, 262), (330, 818), (1590, 818)): pen.fill(oval(sx, sy, 7), '#5a5a5a')


def _later_finger(pen, pts, w0=46.0, w1=20.0, c='#141418'):
    """One of HIS fingers: long, thin, black, jointed (pts = the joints from the knuckle to the tip, screen px)."""
    n = len(pts)
    for i in range(n - 1):
        a_, b_ = pts[i], pts[i + 1]
        wa = w0 + (w1 - w0) * i / (n - 1); wb = w0 + (w1 - w0) * (i + 1) / (n - 1)
        dx, dy = b_[0] - a_[0], b_[1] - a_[1]; L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        seg = smooth([(a_[0] + nx * wa / 2, a_[1] + ny * wa / 2), ((a_[0] + b_[0]) / 2 + nx * (wa + wb) * 0.21, (a_[1] + b_[1]) / 2 + ny * (wa + wb) * 0.21),
                      (b_[0] + nx * wb / 2, b_[1] + ny * wb / 2), (b_[0] - nx * wb / 2, b_[1] - ny * wb / 2),
                      ((a_[0] + b_[0]) / 2 - nx * (wa + wb) * 0.21, (a_[1] + b_[1]) / 2 - ny * (wa + wb) * 0.21), (a_[0] - nx * wa / 2, a_[1] - ny * wa / 2)], True, 0.6)
        pen.fill(seg, c); pen.line(seg, 3, '#000000', 230)
        pen.line(poly([(a_[0] + nx * wa * 0.22, a_[1] + ny * wa * 0.22), (b_[0] + nx * wb * 0.22, b_[1] + ny * wb * 0.22)], False), max(2.0, wa * 0.12), '#5a6078', 110)
    for i, q in enumerate(pts[:-1]):                                             # the knuckles
        w = (w0 + (w1 - w0) * i / (n - 1)) * 0.62
        pen.fill(oval(q[0], q[1], w, w), c); pen.line(oval(q[0], q[1], w, w), 2.5, '#000000', 230)
        pen.fill(oval(q[0] - w * 0.25, q[1] - w * 0.3, w * 0.3), '#6a7088', 110)
    tip = pts[-1]; pr = pts[-2]
    dx, dy = tip[0] - pr[0], tip[1] - pr[1]; L = math.hypot(dx, dy) or 1.0
    nail = smooth([(tip[0] - dy / L * w1 * 0.4, tip[1] + dx / L * w1 * 0.4), (tip[0] + dx / L * w1 * 0.9, tip[1] + dy / L * w1 * 0.9), (tip[0] + dy / L * w1 * 0.4, tip[1] - dx / L * w1 * 0.4)], True, 0.5)
    pen.fill(nail, '#2a2c36'); pen.line(nail, 2, '#000000', 230)


def _ins_wrist(pen, t, press=1.0, count=0, cold=1.0, free=0.0, **kw):
    """Rule seven: the narrator's forearm, palm up, the hoodie cuff pushed back, and HIS two long black fingers pressed to
    the inside of the wrist, counting (press 0..1 lowers them onto the skin; count = 1, 2, 3: a slow beat ring under the
    tips; cold: the skin blanches blue round them; free 0..1: the wrist pulls away)."""
    _ibg(pen, '#3c4630', '#12170e', 160)
    pen.radial(None, 700, 200, 1400, [(0, D_TUBE, 70), (1, D_TUBE, 0)])
    cv = pen.cv
    fr = clamp(free, 0.0, 1.0)
    cv.save(); cv.translate(-520 * fr, 60 * fr)
    cv.save(); cv.translate(560, 600); cv.rotate(-90)
    s = 430.0
    cuff = '#7a2434'
    sl = poly([(-0.72 * s, 2.3 * s), (0.76 * s, 2.3 * s), (0.84 * s, 5.0 * s), (-0.8 * s, 5.0 * s)])        # the sleeve runs on out of frame
    pen.fill(sl, cuff); pen.linear(sl, -0.8 * s, 0, 0.84 * s, 0, [(0, '#ffffff', 30), (0.5, '#000000', 0), (1, '#000000', 120)])
    cv.restore()
    _hand_palm(pen, 560, 600, s, cuff=cuff, curl=0.28, ang=-90.0)
    # the inside of the wrist: tendons, two veins
    cv.save(); cv.translate(560, 600); cv.rotate(-90)
    for (x_, c_, w_) in ((-0.1, '#c4927d', 5), (0.08, '#c4927d', 5)):
        pen.line(smooth([(x_ * s, 0.66 * s), (x_ * s * 0.9, 0.9 * s), (x_ * s, 1.15 * s)], False), w_, c_, 110)
    for pts in ([(-0.2, 0.7), (-0.14, 0.92), (-0.2, 1.16)], [(0.2, 0.66), (0.24, 0.9), (0.15, 1.15)]):
        pen.line(smooth([(a_ * s, b_ * s) for (a_, b_) in pts], False), 7, '#6a8ab0', 90, blur=2)
    cv.restore()
    wx, wy = 560 + 0.9 * s, 600.0                                               # the pulse point on the wrist (screen)
    if cold > 0.01:
        pen.radial(None, wx, wy - 20, 210, [(0, '#bcd0f0', int(120 * cold * press)), (1, '#bcd0f0', 0)])
    if count:
        ph = (t * 0.55) % 1.0
        pen.line(oval(wx, wy - 10, 60 + 120 * ph, 44 + 90 * ph), 5, '#e8f0ff', int(150 * (1 - ph)))
    cv.restore()
    # HIS fingers: down out of the dark above, the two tips flat on the wrist
    lift = (1.0 - clamp(press, 0.0, 1.0)) * 150.0 + 240.0 * fr
    for i, dx in enumerate((-46.0, 44.0)):
        tipx, tipy = wx + dx, wy - 26 + i * 16 - lift
        pts = [(tipx + 760 + i * 70, tipy - 980), (tipx + 470 + i * 40, tipy - 560), (tipx + 200 + i * 16, tipy - 250), (tipx + 44, tipy - 60), (tipx, tipy)]
        cv.save(); cv.translate(14, 22)
        pen.line(smooth(pts[2:], False, 0.8), 40, '#000000', int(110 * press * (1 - fr)), blur=14); cv.restore()
        _later_finger(pen, pts, 84.0, 40.0)
    pen.fill(rect(*_IBG), '#0c1008', 50)


def _ins_clipboard(pen, t, pen_=True, click=None, **kw):
    """His clipboard with no paper on it: brown board, the steel clip holding only a torn corner; it lies on the grey
    white coat across his knees, the click pen beside it (click = f(t) 0..1 presses the button)."""
    _ibg(pen, '#8a8c88', '#4a4c4a', 140)
    pen.texture(rect(*_IBG), 'fabric', 0.6, 'overlay', 1.8); pen.texture(rect(*_IBG), 'grunge', 0.4, 'multiply', 2.4)
    for pts in ([(-300, 300), (500, 420), (1200, 380), (2300, 500)], [(-300, 900), (700, 980), (1500, 900), (2300, 1000)]):
        pen.line(smooth(pts, False, 0.9), 14, '#2a2c2a', 70, blur=6)
    pen.fill(rect(*_IBG), '#1a200e', 70)
    cv = pen.cv
    cv.save(); cv.translate(900, 560); cv.rotate(-6)
    W, H = 640, 880
    bd = rrect(-W / 2, -H / 2, W, H, 26)
    _ins_drop(pen, bd, 16, 26, 130, 20)
    pen.fill(bd, '#7a5230'); pen.texture(bd, 'wood', 0.5, 'overlay', 1.0, 90); pen.texture(bd, 'grunge', 0.35, 'multiply', 1.4)
    pen.linear(bd, -W / 2, -H / 2, W / 2, H / 2, [(0, '#ffffff', 36), (0.3, '#ffffff', 0), (1, '#000000', 70)])
    pen.line(bd, 4)
    ghost = rrect(-W / 2 + 46, -H / 2 + 110, W - 92, H - 170, 4)                 # the paler rectangle where paper lay for years
    pen.fill(ghost, '#f2e0c0', 30); pen.line(ghost, 1.5, '#3a2410', 60)
    scrap = poly([(-90, -H / 2 + 60), (86, -H / 2 + 60), (98, -H / 2 + 150), (52, -H / 2 + 132), (20, -H / 2 + 166), (-30, -H / 2 + 138), (-70, -H / 2 + 158)])
    pen.fill(scrap, '#e8dcc0'); pen.texture(scrap, 'paper', 0.4, 'multiply', 0.8); pen.line(scrap, 2, '#5a4a30', 190)
    cl = rrect(-150, -H / 2 - 16, 300, 120, 18)
    pen.fill(cl, '#b4b8c0'); pen.linear(cl, 0, -H / 2 - 16, 0, -H / 2 + 104, [(0, '#ffffff', 130), (0.4, '#ffffff', 0), (1, '#000000', 90)]); pen.line(cl, 4)
    pen.fill(rrect(-70, -H / 2 - 40, 140, 52, 20), '#9a9ea6'); pen.line(rrect(-70, -H / 2 - 40, 140, 52, 20), 4)
    pen.fill(oval(0, -H / 2 - 14, 13), '#3a3e46')
    for sx in (-124, 124): pen.fill(oval(sx, -H / 2 + 80, 7), '#6a6e76')
    cv.restore()
    if pen_:
        cv.save(); cv.translate(1500, 600); cv.rotate(74)
        _click_pen(pen, click(t) if callable(click) else (click or 0.0))
        cv.restore()


def _click_pen(pen, k=0.0, L=620.0):
    """A retractable ballpoint lying along +x from (0, 0) (the button end) to (L, 0) (the tip): k 0..1 = the button down,
    the point out."""
    k = clamp(k, 0.0, 1.0)
    barrel = rrect(70, -22, L - 190, 44, 14)
    _ins_drop(pen, rrect(0, -22, L, 44, 14), 8, 14, 110, 10)
    btn = rrect(18 * k, -12, 62, 24, 8)
    pen.fill(btn, '#b4b8c0'); pen.line(btn, 3)
    pen.fill(barrel, '#1c2030'); pen.linear(barrel, 0, -22, 0, 22, [(0, '#ffffff', 80), (0.35, '#ffffff', 0), (1, '#000000', 90)]); pen.line(barrel, 3.5)
    clip_ = rrect(84, -34, 220, 16, 6)
    pen.fill(clip_, '#b4b8c0'); pen.linear(clip_, 0, -34, 0, -18, [(0, '#ffffff', 130), (1, '#000000', 60)]); pen.line(clip_, 3)
    ring = rect(70, -24, 26, 48); pen.fill(ring, '#b4b8c0'); pen.line(ring, 3)
    cone = poly([(L - 120, -22), (L - 30, -9), (L - 30, 9), (L - 120, 22)])
    pen.fill(cone, '#b4b8c0'); pen.linear(cone, 0, -22, 0, 22, [(0, '#ffffff', 130), (0.4, '#ffffff', 0), (1, '#000000', 90)]); pen.line(cone, 3)
    if k > 0.05:
        tip = poly([(L - 30, -5), (L - 30 + 26 * k, -2.5), (L - 30 + 26 * k, 2.5), (L - 30, 5)])
        pen.fill(tip, '#d8c080'); pen.line(tip, 2)


def _ins_pen(pen, t, click=None, **kw):
    """'And he was clicking his pen.' The click pen held in HIS long black fingers, the thumb on the button (click = f(t)
    0..1: the thumb presses, the point comes out)."""
    k = clamp(click(t) if callable(click) else (click or 0.0), 0.0, 1.0)
    _ibg(pen, '#3c4630', '#10140c', 160)
    pen.radial(None, 1300, 150, 1400, [(0, D_TUBE, 80), (1, D_TUBE, 0)])
    cv = pen.cv
    # the fingers behind the pen (index and middle wrapped round the barrel)
    _later_finger(pen, [(2300, 1400), (1700, 1040), (1250, 800), (980, 690), (800, 706)], 70.0, 34.0)
    _later_finger(pen, [(2300, 1150), (1760, 880), (1340, 660), (1090, 560), (930, 575)], 66.0, 32.0)
    cv.save(); cv.translate(560, 330); cv.rotate(26)
    _click_pen(pen, k, 900.0)
    cv.restore()
    # the thumb over the button end
    tx, ty = 560 + 30 * k * math.cos(math.radians(26)) - 4, 330 + 30 * k * math.sin(math.radians(26)) - 2
    _later_finger(pen, [(2300, 300), (1500, 120), (980, 110), (700, 200), (tx + 30, ty + 6)], 76.0, 40.0)
    if k > 0.5: pen.line(oval(tx, ty, 60, 60), 4, '#e8f0d0', int(120 * (k - 0.5) * 2))
    pen.fill(rect(*_IBG), '#0c1008', 40)


def _ins_tape(pen, t, loose=0.0, eyes=1.0, gap=4, **kw):
    """His head, close: old yellowed medical tape wound round and round, one thin gap, and in the gap two pale, patient
    eyes (eyes 0..1). loose 0..1: the strips come away one by one from the top (each lifts at one end, curls and
    hangs), and there is only dark under them."""
    _ibg(pen, '#2c3424', '#0c100a', 170)
    cv = pen.cv
    head = smooth([(560, 1500), (500, 700), (640, 60), (960, -420), (1280, 60), (1420, 700), (1360, 1500)], True, 0.7)
    pen.fill(head, '#0a0b0c')
    N = 11
    rng = np.random.default_rng(6)
    lo = clamp(loose, 0.0, 1.0)
    strips = []
    for i in range(N):
        y = -60 + i * 108 + rng.uniform(-10, 10)
        strips.append((i, y, rng.uniform(-3.5, 3.5), 118 + rng.uniform(-8, 14)))
    cv.save(); cv.clipPath(head, skia.ClipOp.kIntersect, True)
    strips[gap] = (strips[gap][0], strips[gap][1] - 30, strips[gap][2] * 0.3, strips[gap][3])
    strips[gap + 1] = (strips[gap + 1][0], strips[gap + 1][1] + 30, strips[gap + 1][2] * 0.3, strips[gap + 1][3])
    if eyes > 0.01:                                                              # the gap: his eyes in their dark sockets
        gy = (strips[gap][1] + strips[gap][3] / 2 + strips[gap + 1][1] - strips[gap + 1][3] / 2) / 2
        for ex in (800, 1120):
            pen.fill(oval(ex, gy, 96, 46), '#050506')
            eye = oval(ex, gy, 58, 26)
            pen.fill(eye, '#d8dcd0', int(255 * eyes)); pen.fill(oval(ex, gy, 22, 22), '#aab4b8', int(255 * eyes)); pen.fill(oval(ex, gy, 8.5), '#0a0a0c', int(255 * eyes))
            pen.fill(oval(ex - 8, gy - 7, 4.5), '#ffffff', int(230 * eyes))
            pen.line(smooth([(ex - 66, gy - 6), (ex, gy - 31), (ex + 66, gy - 6)], False), 7, '#050506', int(255 * eyes))
    cv.restore()
    for (i, y, rot, h) in strips:
        k = clamp(lo * (N + 1.5) - i, 0.0, 1.0)                                  # this strip's own peel 0..1
        cv.save(); cv.translate(960, y); cv.rotate(rot)
        w = 1700.0
        if k < 0.999:
            x_cut = -w / 2 + w * (1 - k)                                         # what is still stuck (from the left)
            st = rect(-w / 2, -h / 2, x_cut + w / 2, h)
            cv.save()
            inv = skia.Matrix(); inv.setRotate(-rot); inv.preTranslate(-960, -y)
            hp = skia.Path(head); hp.transform(inv)
            cv.clipPath(hp, skia.ClipOp.kIntersect, True)
            pen.fill(st, '#000000', 60, blur=5)
            pen.fill(st, mix('#d8c47a', '#c0a85a', _h(i, 3)))
            pen.texture(st, 'fabric', 0.5, 'overlay', 0.9); pen.texture(st, 'grunge', 0.4, 'multiply', 1.6)
            pen.linear(st, 0, -h / 2, 0, h / 2, [(0, '#ffffff', 50), (0.25, '#ffffff', 0), (0.8, '#3a2a08', 0), (1, '#3a2a08', 110)])
            for xx in np.arange(-w / 2, x_cut, 26.0): pen.fill(rect(xx, -h / 2, 1.2, h), '#6a5420', 40)
            pen.line(poly([(-w / 2, -h / 2), (x_cut, -h / 2)], False), 2.5, '#5a4418', 170); pen.line(poly([(-w / 2, h / 2), (x_cut, h / 2)], False), 3, '#3a2a0c', 200)
            cv.restore()
        if k > 0.001:                                                            # the lifted end: a curl hanging off the head
            x_cut = -w / 2 + w * (1 - k)
            L = min(520.0, w * k)
            sway = 10 * math.sin(t * 1.3 + i)
            curl = smooth([(x_cut, 0), (x_cut + L * 0.3, -40 - 60 * k), (x_cut + L * 0.62 + sway, 30 + 120 * k), (x_cut + L * 0.5 + sway, 150 + 240 * k)], False, 0.9)
            pen.line(curl, h * 0.82, '#000000', 70, blur=6)
            pen.line(curl, h * 0.8, '#8a7434', 255, cap='butt'); pen.line(curl, h * 0.8 - 8, '#b89e58', 255, cap='butt')
            pen.line(curl, 3, '#5a4418', 160)
        cv.restore()
    pen.radial(None, 700, 250, 1500, [(0, D_TUBE, 60), (1, D_TUBE, 0)])
    pen.linear(rect(*_IBG), 0, 0, 1920, 0, [(0, '#000000', 110), (0.3, '#000000', 0), (0.7, '#000000', 0), (1, '#000000', 130)])


def _ins_glucose(pen, t, value=104, bg='morning', trend='flat', name='Milo', **kw):
    """Milo's phone, fifteen years on: his glucose sensor's app: the big number (value, mg/dL), 'In range', the last
    three hours running along the green band. bg 'morning' (the river and the sunrise behind, out of focus) | 'dark'."""
    if bg == 'morning':
        _ibg(pen, '#a8c0dc', '#ffe0b8', 60)
        pen.fill(rect(_IBG[0], 620, _IBG[2], 900), '#7a98bc'); pen.fill(rect(_IBG[0], 880, _IBG[2], 700), '#6a8a4a')
        pen.radial(None, 1500, 560, 700, [(0, '#fff2c8', 230), (0.3, '#ffd8a0', 120), (1, '#ffd8a0', 0)], clip=False)
        pen.fill(rect(*_IBG), '#ffffff', 26, blur=0)
    else:
        _ibg(pen, '#20222e', '#0c0d14', 150)
    cv = pen.cv
    cv.save(); cv.translate(960, 560); cv.rotate(-5.0)
    W, H = 520, 1020
    body = rrect(-W / 2, -H / 2, W, H, 62)
    _ins_drop(pen, body, 14, 24, 130, 22)
    pen.fill(body, '#14161b'); pen.line(body, 4)
    sc = rrect(-W / 2 + 16, -H / 2 + 16, W - 32, H - 32, 48)
    pen.fill(sc, '#f6f8f4')
    cv.save(); cv.clipPath(sc, skia.ClipOp.kIntersect, True)
    pen.fill(rect(-W / 2, -H / 2, W, 250), '#2f9a6a')
    btext(pen, '6:42', -W / 2 + 46, -H / 2 + 62, 'sans_b', 26, '#ffffff', 235)
    btext(pen, 'Good morning, %s' % name, 0, -H / 2 + 128, 'sans_b', 34, '#ffffff', 245, 'center')
    btext(pen, 'sensor active', 0, -H / 2 + 172, 'sans', 24, '#d8f2e4', 230, 'center')
    disc = oval(0, -H / 2 + 400, 176)
    pen.fill(disc, '#ffffff'); pen.line(disc, 14, '#2f9a6a')
    btext(pen, str(value), -10, -H / 2 + 438, 'sans_b', 150, '#1a3a2c', 250, 'center')
    btext(pen, 'mg/dL', 0, -H / 2 + 500, 'sans', 30, '#4a6a5a', 230, 'center')
    ax, ay = 196, -H / 2 + 400                                                    # the trend arrow
    da = {'flat': 0.0, 'up': -45.0, 'down': 45.0}.get(trend, 0.0)
    cv.save(); cv.translate(ax, ay); cv.rotate(da)
    pen.fill(oval(0, 0, 34), '#2f9a6a'); pen.line(poly([(-16, 0), (14, 0)], False), 7, '#ffffff'); pen.line(poly([(4, -11), (16, 0), (4, 11)], False), 7, '#ffffff')
    cv.restore()
    btext(pen, 'In range', 0, -H / 2 + 650, 'sans_b', 44, '#2f9a6a', 245, 'center')
    gx0, gx1, gy0, gy1 = -W / 2 + 50, W / 2 - 50, -H / 2 + 700, -H / 2 + 900       # the graph
    pen.fill(rrect(gx0, gy0, gx1 - gx0, gy1 - gy0, 12), '#eef2ee')
    pen.fill(rect(gx0, gy0 + 60, gx1 - gx0, 80), '#c8ecd4')
    pts = []
    for i in range(37):
        u = i / 36.0
        vv = 118 + 20 * math.sin(u * 5.2 + 0.6) - 14 * u + 6 * math.sin(u * 17)
        if i == 36: vv = float(value)
        pts.append((gx0 + u * (gx1 - gx0), gy0 + 60 + 80 * (1 - (vv - 70) / 110.0)))
    pen.line(smooth(pts, False, 0.9), 6, '#1a6a4a')
    pen.fill(oval(pts[-1][0], pts[-1][1], 11), '#1a6a4a'); pen.line(oval(pts[-1][0], pts[-1][1], 11), 3, '#ffffff')
    for i, s_ in enumerate(('3 h', '2 h', '1 h', 'now')): btext(pen, s_, gx0 + i * (gx1 - gx0) / 3, gy1 + 34, 'sans', 20, '#6a7a72', 220, 'center')
    cv.restore()
    pen.linear(sc, -W / 2, -H / 2, W / 2, H / 2, [(0, '#ffffff', 46), (0.3, '#ffffff', 0), (1, '#000000', 20)])
    cam_ = oval(0, -H / 2 + 36, 9); pen.fill(cam_, '#14161b')
    cv.restore()


def _ins_clock_d(pen, t, time=(4, 12, 0), slow=0.0, bg='wait', **kw):
    """The clock on the waiting room's wall (a plain institutional dial, a red second hand). time = (h, m, s) or f(t) ->
    (h, m, s): give it a second hand that brakes ('the clock on the wall slowed down'); slow 0..1 adds the after-image of
    a hand dragging through thick time. bg 'wait' | 'kitchen' (Ruth's red kitchen clock at night)."""
    tm = time(t) if callable(time) else time
    hh, mm = tm[0], tm[1]; ss = tm[2] if len(tm) > 2 else 0.0
    if bg == 'wait':
        _ibg(pen, '#8a9068', '#3e4430', 150)
        pat(pen, 1920, 1080, 'ditsy', '#6a6e4a', 130, 21, None, 3.2)
        pen.fill(rect(*_IBG), '#141a08', 110)
        rimc = '#2a2c2a'
    else:
        _ibg(pen, DP['kit_wall'], None, 0); pat(pen, 1920, 1080, 'ditsy', DP['kit_ink'], 150, 25, None, 3.0)
        pen.fill(rect(*_IBG), '#0c1230', 120)
        rimc = '#c83a32'
    R = 420.0
    pen.fill(oval(985, 570, R + 14), '#000000', 130, blur=22)
    pen.fill(oval(960, 540, R), rimc); pen.fill(oval(960, 540, R * 0.9), '#f2f0e4' if bg == 'wait' else '#f8f4e8'); pen.line(oval(960, 540, R), 6)
    if bg == 'wait': pen.texture(oval(960, 540, R * 0.9), 'grunge', 0.35, 'multiply', 1.6)
    for k_ in range(60):
        a = 2 * math.pi * k_ / 60
        r0 = R * (0.76 if k_ % 5 == 0 else 0.82)
        pen.seg((960 + math.sin(a) * r0, 540 - math.cos(a) * r0), (960 + math.sin(a) * R * 0.86, 540 - math.cos(a) * R * 0.86), 7 if k_ % 5 == 0 else 2.5, '#1a1a1a')
    for k_ in range(1, 13):
        a = 2 * math.pi * k_ / 12
        btext(pen, str(k_), 960 + math.sin(a) * R * 0.63, 540 - math.cos(a) * R * 0.63 + 26, 'sans_b', 74, '#1a1a1a', 240, 'center')
    am = 2 * math.pi * (mm + ss / 60.0) / 60; ah = 2 * math.pi * ((hh % 12) + mm / 60.0) / 12; asec = 2 * math.pi * ss / 60
    pen.seg((960, 540), (960 + math.sin(ah) * R * 0.46, 540 - math.cos(ah) * R * 0.46), 20, '#1a1a1a')
    pen.seg((960, 540), (960 + math.sin(am) * R * 0.7, 540 - math.cos(am) * R * 0.7), 12, '#1a1a1a')
    if slow > 0.01:
        for k_ in range(1, 7):
            a2 = asec - k_ * 0.045 * slow * 3.0
            pen.seg((960, 540), (960 + math.sin(a2) * R * 0.78, 540 - math.cos(a2) * R * 0.78), 5, '#c82a2a', int(90 * slow * (1 - k_ / 7.0)))
    pen.seg((960 - math.sin(asec) * 70, 540 + math.cos(asec) * 70), (960 + math.sin(asec) * R * 0.78, 540 - math.cos(asec) * R * 0.78), 5, '#c82a2a')
    pen.fill(oval(960, 540, 20), '#c82a2a'); pen.line(oval(960, 540, 20), 3)
    pen.linear(oval(960, 540, R * 0.9), 560, 160, 1360, 920, [(0, '#ffffff', 80), (0.35, '#ffffff', 0), (1, '#000000', 30)])
    if bg == 'wait': pen.radial(None, 500, 100, 1500, [(0, D_TUBE, 70), (1, D_TUBE, 0)])


def _ins_coffee(pen, t, steam=1.0, cold=0.0, tod='sunrise', **kw):
    """'At sunrise, Grandma brought him a cup of coffee.' The cup and saucer on the little round table by the armchair in
    the first sun (steam 0..1; cold 0..1: no steam, a skin on the coffee: he never drank it)."""
    _ibg(pen, DP['liv79_paper'], _darken(DP['liv79_paper'], 0.3), 100)
    pat(pen, 1920, 1080, 'roses', DP['liv79_ink'], 140, 21, DP['liv79_ink2'], 3.0)
    pen.fill(rect(*_IBG), '#3a1e10', 70)
    arm = rrect(1380, 380, 1200, 1300, 150)                                      # the brown armchair's arm at the edge of frame
    pen.fill(arm, DP['arm79']); pen.texture(arm, 'fabric', 0.6, 'overlay', 1.6)
    pen.linear(arm, 1380, 0, 2400, 0, [(0, '#ffffff', 40), (0.2, '#000000', 0), (1, '#000000', 120)]); pen.line(arm, 5)
    top = oval(820, 930, 900, 300)
    pen.fill(oval(840, 965, 900, 300), '#000000', 100, blur=20)
    pen.fill(top, '#7a4a2a'); pen.texture(top, 'wood', 0.5, 'overlay', 1.2)
    pen.linear(top, 0, 630, 0, 1230, [(0, '#ffffff', 40), (0.4, '#000000', 0), (1, '#000000', 90)]); pen.line(top, 5)
    pen.fill(oval(840, 870, 380, 96), '#000000', 90, blur=14)
    sau = oval(820, 846, 380, 100)
    pen.fill(sau, '#d8cdb8'); pen.line(sau, 4); pen.line(oval(820, 842, 300, 76), 5, '#b86a2a', 200)
    cup = smooth([(590, 560), (600, 760), (680, 836), (960, 836), (1040, 760), (1050, 560)], True, 0.5)
    hd = smooth([(1040, 610), (1150, 600), (1180, 690), (1110, 770), (1030, 750)], False, 0.9)
    pen.line(hd, 40, LINE); pen.line(hd, 30, '#d8cdb8')
    pen.fill(cup, '#d8cdb8'); pen.linear(cup, 590, 0, 1050, 0, [(0, '#ffffff', 60), (0.3, '#ffffff', 0), (1, '#000000', 80)])
    cv = pen.cv
    cv.save(); cv.clipPath(cup, skia.ClipOp.kIntersect, True)
    pen.fill(rect(560, 640, 520, 44), '#b86a2a'); pen.fill(rect(560, 696, 520, 14), '#d8a040')
    cv.restore(); pen.line(cup, 5)
    rim = oval(820, 560, 230, 62)
    pen.fill(rim, '#e2d8c4'); pen.line(rim, 5)
    cof = oval(820, 566, 204, 50)
    pen.fill(cof, mix('#3a1e10', '#4a2e1c', cold)); pen.linear(cof, 620, 520, 1020, 610, [(0, '#ffffff', 60), (0.4, '#ffffff', 0)])
    if cold > 0.3: pen.line(oval(800, 566, 150, 34), 3, '#8a6a4a', int(120 * cold))
    st = clamp(steam * (1 - cold), 0.0, 1.0)
    if st > 0.02:
        for i in range(3):
            x = 740 + i * 80
            ph = t * 0.35 + i * 0.37
            pts = [(x + 26 * math.sin(ph * 2 + k_ * 0.9), 520 - k_ * 86) for k_ in range(6)]
            pen.line(smooth(pts, False, 1.0), 26, '#ffffff', int(70 * st), blur=10)
    pen.radial(None, 200, 100, 1700, [(0, D_SUN, 130), (0.6, D_SUN, 30), (1, D_SUN, 0)])            # the first sun through the window
    pen.linear(rect(*_IBG), 0, 0, 1920, 1080, [(0, '#ffe2b0', 50), (0.5, '#ffe2b0', 0)])


def _ins_advice(pen, t, show=5, hl=0, **kw):
    """The outro's list, written on a notepad under the lamp: how to beat the Waiting Man, for real (show = items written,
    hl = item lit). Big enough to read on a phone."""
    _ibg(pen, '#8a5a38', '#4a2e1c', 120)
    pen.texture(rect(*_IBG), 'wood', 0.5, 'overlay', 1.4)
    pen.radial(None, 300, 60, 1900, [(0, D_LAMP, 150), (0.6, D_LAMP, 30), (1, D_LAMP, 0)])
    x0, y0, W, H = 170, 26, 1580, 1030
    pad = rrect(x0, y0, W, H, 10)
    _ins_drop(pen, pad, 12, 20, 130, 18)
    pen.fill(pad, '#fbf6e6'); pen.texture(pad, 'paper', 0.3, 'multiply', 0.8)
    pen.fill(rect(x0, y0, W, 96), '#1e6a8a')
    btext(pen, 'HOW TO BEAT THE WAITING MAN', x0 + W / 2, y0 + 68, 'sans_b', 56, '#ffffff', 248, 'center', spacing=0.05)
    y = y0 + 168
    for i, (lead, ans) in enumerate(D_ADVICE[:int(show)]):
        ll = _wrap_hand(lead, 'sans_b', 43, W - 230)
        hgt = len(ll) * 52 + 66
        if hl == i + 1:
            pen.fill(rrect(x0 + 30, y - 46, W - 60, hgt + 6, 12), '#ffe9a0', 170)
        pen.fill(oval(x0 + 84, y - 12, 30), '#1e6a8a'); btext(pen, str(i + 1), x0 + 84, y + 2, 'sans_b', 38, '#ffffff', 250, 'center')
        for k_, l_ in enumerate(ll): btext(pen, l_, x0 + 140, y + k_ * 52, 'sans_b', 43, '#22303a', 245)
        btext(pen, ans, x0 + 140, y + len(ll) * 52 + 6, 'hand', 58, '#c8302a', 245, skew=-0.03)
        y += hgt + 34
    pen.linear(pad, x0, y0, x0 + W, y0 + H, [(0, '#ffffff', 0), (0.7, '#ffffff', 0), (1, '#8a6a3a', 40)])
    pen.line(pad, 3, '#3a3a3a', 200)


DR_INSERTS = {
    'card': (_ins_card, 'dr_ins', 'the yellow typed card taped inside the medicine cabinet: the seven rules (hl=n, show=n)'),
    'card_back': (lambda pen, t, **kw: _ins_card(pen, t, **dict(dict(back=True, bg='dark', torn=True, tilt=2.0), **kw)), 'dr_ins',
                  'the back of the card: in faded ink from 1979, signed Doctor Later (reveal 0..1)'),
    'phone': (_ins_phone, 'dr_ins', 'the kitchen wall phone (ring=f(t), state hung | off, cord in | out)'),
    'phone_counter': (_ins_phone_counter, 'dr_ins', 'the receiver laid on the counter like a sleeping baby, the hold music still playing (music 0..1)'),
    'phone_cord': (_ins_phone_cord, 'dr_ins', 'the line cord and its plug lying on the kitchen floor, the jack empty'),
    'badge': (_ins_badge, 'dr_ins', "Doctor Halverson's badge clipped crooked to her wet raincoat: Dr. Anna Halverson, Pediatrics (two dinosaur stickers)"),
    'results': (_ins_results, 'dr_ins', "Milo's lab results with the marker note (show=0..8 marker lines, slide 0..1 under the door, bg floor | hand | sink)"),
    'note': (lambda pen, t, **kw: _ins_results(pen, t, **dict(dict(zoom='note', bg='hand'), **kw)), 'dr_ins',
             'the marker note filling the frame: the six warning signs, "If you see these, don\'t wait. I\'ll be in my car." (show=0..8)'),
    'burn': (_ins_burn, 'dr_ins', 'the paper burning in the sink (burn 0..1, match 0..1; flames flicker with t)'),
    'ticket': (_ins_ticket, 'dr_ins_wait', "a paper ticket: text 'MILO' | 'RUTH' | '' (Grandpa's: the ink gone); bg wait | dawn | dark"),
    'sign': (_ins_sign, 'dr_ins_wait', 'NOW SERVING: 1979 (digits, k, flick=f(t))'),
    'clipboard': (_ins_clipboard, 'dr_ins_wait', 'his clipboard with no paper on it, the click pen beside it (click=f(t))'),
    'pen': (_ins_pen, 'dr_ins_wait', 'the click pen in HIS long black fingers, the thumb on the button (click=f(t))'),
    'wrist': (_ins_wrist, 'dr_ins_wait', "the narrator's wrist, HIS two long black fingers on the pulse (press, count, cold, free)"),
    'tape': (_ins_tape, 'dr_ins_wait', 'the old yellow tape round his head, the thin gap, two pale patient eyes (loose 0..1: strip by strip; eyes)'),
    'glucose': (_ins_glucose, 'dr_ins_bright', "Milo's phone at 22: his blood sugar, in range (value, trend, bg morning | dark)"),
    'clock': (_ins_clock_d, 'dr_ins_wait', 'the wall clock slowing down (time=(h, m, s) or f(t), slow 0..1; bg wait | kitchen)'),
    'coffee': (_ins_coffee, 'dr_ins', '1979, sunrise: the cup of coffee on the little table by the armchair (steam, cold)'),
    'advice': (_ins_advice, 'dr_ins_bright', 'the outro list on a notepad: how to beat the Waiting Man (show=0..5, hl=n)'),
}


def dr_insert(name, prop_kw=None, motion=None, t0=0.0, grade=None):
    """A close-up insert from DR_INSERTS: prop_kw = dict or f(t) -> dict for the drawing (a dict may hold f(t) values for
    the keys that take one: ring, click, flick, time), motion = f(t) -> (dx, dy, dscale, drot) drifting the whole insert
    (a slow handheld float; keep |dx|, |dy| < 300 px, the art carries that margin). One sharp plane: no lens, no DOF."""
    fn, gr, note = DR_INSERTS[name]
    static = not callable(prop_kw) and motion is None and not any(callable(v_) for v_ in (prop_kw or {}).values()) and name not in ('burn', 'phone_counter', 'tape', 'coffee')

    def draw(pen, t):
        kw = prop_kw(t) if callable(prop_kw) else dict(prop_kw or {})
        cv = pen.cv
        if motion is not None:
            dx, dy, ds, dr = motion(t)
            cv.save(); cv.translate(960 + dx, 540 + dy); cv.rotate(dr); cv.scale(1 + ds, 1 + ds); cv.translate(-960, -540)
        fn(pen, t - t0, **kw)
        if motion is not None: cv.restore()
    key = 'drins:%s:%s' % (name, _okey(prop_kw or {}) if isinstance(prop_kw, dict) else 'f')
    lay = Layer(1.0, draw, 'insert', cache=key if static else False, bounds=(-460, -320, 2380, 1400), blur=0)
    return BSet('dr_ins_' + name, [lay], {}, {}, lens=None, grade=grade or gr, focus=1.0, dof=0.0, cover=(-460, -320, 2380, 1400), info={'note': note})


# ====================================================================================================== staging: Doctor Later, the plan map, the registry
_stage_figure_base = stage_figure


def stage_figure(sp, who, spot, act=None, turn=None, seed=1, expr='neutral', name=None, light=True, acting=None, perch=None):
    """One cast member on a set the way the staging data says (see sets_bunny.stage_figure). Doctor film addition: Doctor
    Later ('later') on a seat Spot is perched with his own rig, a.perch(seat_y, perch): perch = 'armchair' | 'plastic' |
    'bench' | 'car' | 'low' (default from the spot's name), so he folds onto the armchair, the bus bench or the back seat."""
    s = sp.anchors[spot] if isinstance(spot, str) else spot
    if who == 'later' and s.kind == 'seat':
        nm = spot if isinstance(spot, str) else ''
        kind = perch or ('armchair' if 'armchair' in nm else ('bench' if 'bus' in nm else ('car' if 'back_' in nm else 'plastic')))

        def act2(a, acting=acting):
            a.perch(s.seat_y if s.seat_y is not None else s.y - 0.45 * s.ppm, kind)
            if acting: acting(a)
        return _stage_figure_base(sp, who, s, 'stand', turn, seed, expr, name, light, act2)
    return _stage_figure_base(sp, who, spot, act, turn, seed, expr, name, light, acting)


def _dr_plan_panels():
    """The Doctor film's plan panels (same dict as sets_bunny._plan_panels): Ruth's house, the waiting room, Larch Street,
    then every other location on its own little plan, each with its furniture footprints and its cameras."""
    def blocks(*sets_, drop=()):
        b = {}
        for sp_ in sets_:
            for k_, q in (sp_.info.get('blocks') or {}).items():
                if k_ not in drop and not k_.startswith('far_'): b[k_] = q
        return b

    def marks(sp_, names):
        return [(sp_.anchors[n].X, sp_.anchors[n].Yp, n) for n in names if n in sp_.anchors]
    lv, hl, kt, bt = dr_living('wide'), dr_hall('door'), dr_kitchen('wide'), dr_bath('sink')
    wt = dr_living('wide', state='wait')
    P = []
    P.append(dict(title="RUTH'S HOUSE  (27 Larch Street; floor Y 0)", ext=(-6.3, 5.2, -2.6, 10.3), ray=1.5,
                  floors=[('bedrooms (not built: no camera looks there)', _r4p((0.4, 4.6, 0.0, 5.8))), ('(not built)', _r4p((2.8, 4.6, 5.8, 9.6))),
                          ('LIVING ROOM', _r4p(D_LIV)), ('HALL', _r4p(D_HALL)), ('KITCHEN', _r4p(D_KIT)), ('BATHROOM', _r4p(D_BATH)), ('porch', _r4p(D_PORCH))],
                  blocks=dict(blocks(lv, kt, bt, hl), counter=_r4p(D_KCOUNTER), counter_return=_r4p(D_KRETURN)),
                  doors=[((D_FDOOR[0], 0.0), (D_FDOOR[1], 0.0), 'front door'), ((-1.2, D_LDOOR[0]), (-1.2, D_LDOOR[1]), 'living-room door'),
                         ((-1.2, D_KDOOR[0]), (-1.2, D_KDOOR[1]), 'kitchen doorway'), ((0.4, D_BDOOR[0]), (0.4, D_BDOOR[1]), 'bath'),
                         ((0.4, D_RDOOR[0]), (0.4, D_RDOOR[1]), "Ruth's room")],
                  windows=[((D_LWIN[0], 0.0), (D_LWIN[1], 0.0)), ((-5.6, D_SWIN[0]), (-5.6, D_SWIN[1])), ((D_KWIN[0], 9.6), (D_KWIN[1], 9.6)),
                           ((D_HWIN[0], 9.6), (D_HWIN[1], 9.6)), ((D_BWIN[0], 9.6), (D_BWIN[1], 9.6)), ((D_RWIN[0], 0.0), (D_RWIN[1], 0.0))],
                  lines=[], marks=[(D_PHONE[0] - 0.02, D_PHONE[2], 'wall phone'), (D_JACK[0] - 0.02, D_JACK[2] + 0.25, 'jack'), (D_CAB[0] - 0.05, (D_CAB[1] + D_CAB[2]) / 2, 'medicine cabinet'),
                                   (-3.3, 9.3, 'sink'), (D_RECEIVER[0], D_RECEIVER[2], 'receiver'), (-2.1, 8.5, 'floor_rock'), (-0.4, 0.1, 'peephole')],
                  cams=[k for k in DR_CAMS if CAMS[k]['room'] in ('living', 'hall', 'kitchen', 'bath') and not k.startswith('dr_wait')]))
    P.append(dict(title='THE WAITING ROOM  (the living room, rule 6)', ext=(-6.2, -0.6, -0.5, 5.9), ray=1.3,
                  floors=[('WAITING ROOM', _r4p(D_LIV))], blocks=blocks(wt),
                  doors=[((-1.2, D_LDOOR[0]), (-1.2, D_LDOOR[1]), 'door')], windows=[((D_LWIN[0], 0.0), (D_LWIN[1], 0.0)), ((-5.6, D_SWIN[0]), (-5.6, D_SWIN[1]))],
                  lines=[], marks=[(D_SIGN[0], D_SIGN[1] - 0.1, 'NOW SERVING'), (-1.5, 0.42, 'TV'), (D_ROW_X[0], D_ROWS_Y[2], 'Grandpa')] +
                  [(x, y, 'tube%d%s' % (i, '' if i in (0, 2) else ' (dead)')) for i, (x, y) in enumerate(D_TROFFERS)],
                  cams=[k for k in DR_CAMS if k.startswith('dr_wait')]))
    ex = dr_front('house')
    _, _, CB = dr_car_parts()
    P.append(dict(title='LARCH STREET  (ground Y %.1f)' % D_GROUND, ext=(-50.0, 12.0, -30.0, 11.0), ray=7.0,
                  floors=[("Ruth's house", _r4p(D_HOUSE)), ('driveway', _r4p(D_DRIVE)), ('Larch Street', [(-50, D_STREET[1]), (12, D_STREET[1]), (12, D_STREET[0]), (-50, D_STREET[0])]),
                          ('porch', _r4p(D_PORCH))] + [('', [(x0, 0.0), (x1, 0.0), (x1, 10.0), (x0, 10.0)]) for (x0, x1, yf, tag) in D_NEIGH[:2]] +
                  [('', [(x0, -33.5), (x1, -33.5), (x1, -24.5), (x0, -24.5)]) for (x0, x1) in D_ACROSS],
                  blocks={'car': CB.footprint()}, doors=[((D_FDOOR[0], 0.0), (D_FDOOR[1], 0.0), '')], windows=[((D_LWIN[0], 0.0), (D_LWIN[1], 0.0))],
                  lines=[], marks=[(D_BUS[0], D_BUS[1], 'bus stop bench'), (D_BUS_LAMP[0], D_BUS_LAMP[1], 'flickering lamp')] + [(x, y, 'lamp') for (x, y) in D_LAMPS if -50 < x < 12] +
                  [(D_MAPLE[0], D_MAPLE[1], 'maple')],
                  cams=[k for k in DR_CAMS if CAMS[k]['room'] == 'street'] + ['dr_liv_window_bus']))
    for (title, sp_, R_, ray, room, mk) in (
            ("DOCTOR HALVERSON'S EXAM ROOM", dr_clinic('wide'), C_R, 1.0, 'clinic', ('exam_table', 'stool', 'parent_chair', 'door')),
            ('A HOSPITAL OFFICE AT 3 AM', dr_office('desk'), O_R, 1.0, 'office', ('desk_chair', 'phone', 'results', 'door')),
            ('ER BAY', dr_er_bay('bay'), E_R, 1.0, 'er_bay', ('bed_lie', 'bed_edge', 'monitor', 'iv_bag')),
            ('ER WAITING ROOM', dr_er_wait('wide'), W_R, 1.8, 'er_wait', ('chest_seat', 'rock_seat', 'desk_front', 'entrance')),
            ("THE CARDIOLOGIST'S OFFICE", dr_cardio('side'), CD_R, 1.0, 'cardio', ('doctor_chair', 'patient_chair0', 'patient_chair1', 'coffee')),
            ('THE OUTRO: A BEDSIDE', dr_outro('table'), OU_R, 1.0, 'outro', ('phone', 'lamp_switch', 'bed_edge'))):
        P.append(dict(title=title, ext=(R_[0] - 0.5, R_[1] + 0.5, R_[2] - 0.6, R_[3] + 0.5), ray=ray, floors=[('', _r4p(R_))], blocks=blocks(sp_), doors=[], windows=[], lines=[],
                      marks=marks(sp_, mk), cams=[k for k in DR_CAMS if CAMS[k]['room'] == room]))
    hh = dr_hosp_hall('hall')
    P.append(dict(title='THE LONG HOSPITAL HALLWAY', ext=(-6.0, 8.6, -1.0, 33.0), ray=5.0, floors=[('', _r4p(HH_R))], blocks=blocks(hh), doors=[], windows=[], lines=[],
                  marks=[(HH_CHAIR[0], HH_CHAIR[1], 'the last chair')], cams=[k for k in DR_CAMS if CAMS[k]['room'] == 'hosp_hall']))
    ee = dr_er_entrance('ext')
    P.append(dict(title='LARKFIELD GENERAL: THE ER ENTRANCE', ext=(-10.0, 16.0, -18.0, 4.0), ray=4.0, floors=[('hospital', [(-10, 0), (16, 0), (16, 4), (-10, 4)])],
                  blocks=blocks(ee), doors=[], windows=[], lines=[], marks=marks(ee, tuple(ee.anchors)[:6]), cams=[k for k in DR_CAMS if CAMS[k]['room'] == 'er_ext']))
    ck = dr_car('front')
    P.append(dict(title="INSIDE HALVERSON'S CAR  (+y = forward)", ext=(-1.6, 2.8, -2.3, 3.3), ray=0.9,
                  floors=[('cabin', DrCarCabin.poly), ('bonnet', [(-0.8, 1.04), (0.8, 1.04), (0.76, 1.95), (-0.76, 1.95)])], blocks=blocks(ck), doors=[],
                  windows=[((-K_HW, -1.2), (-K_HW, 0.95)), ((K_HW, -1.2), (K_HW, 0.95)), ((-0.6, 1.0), (0.6, 1.0)), ((-0.55, -1.72), (0.55, -1.72))], lines=[],
                  marks=[(x, y, nm) for nm, (x, y) in list(K_FRONT.items()) + list(K_BACK.items())] + [(K_WHEEL[0], K_WHEEL[2], 'wheel'), (K_MIRROR[0], K_MIRROR[2], 'mirror')],
                  cams=[k for k in DR_CAMS if CAMS[k]['room'] == 'car']))
    P.append(dict(title='MILO AT 22: THE RIVER PATH  (he runs +x)', ext=(-9.0, 9.0, -8.0, 6.0), ray=3.0,
                  floors=[('path', [(-9, RN_PATH[0]), (9, RN_PATH[0]), (9, RN_PATH[1]), (-9, RN_PATH[1])]), ('river', [(-9, RN_RAIL + 1.2), (9, RN_RAIL + 1.2), (9, 6), (-9, 6)])],
                  blocks={}, doors=[], windows=[], lines=[[(-9, RN_RAIL), (9, RN_RAIL)]], marks=[(0.0, 0.0, 'runner'), (0.6, RN_RAIL - 0.45, 'rail_stand')],
                  cams=[k for k in DR_CAMS if CAMS[k]['room'] == 'run']))
    return P


def dr_plan_map(path, pw=900, ph=1000, cols=4):
    """The Doctor film's floor plans with every camera (lens dot, direction, horizontal field of view of the 1920 design
    frame, the CAMS name), the furniture footprints (the walk-blocking polygons of sp.walkable) and the main marks -> JPEG."""
    import cv2
    tiles = []
    for P in _dr_plan_panels():
        surf = skia.Surface(pw, ph); cv = surf.getCanvas(); pen = Pen(cv)
        cv.clear(skia.Color4f(0.97, 0.96, 0.93, 1.0))
        x0, x1, y0, y1 = P['ext']
        k = min((pw - 60) / (x1 - x0), (ph - 120) / (y1 - y0))
        ox = (pw - k * (x1 - x0)) / 2; oy = 80 + (ph - 100 - k * (y1 - y0)) / 2

        def S(x, y): return (ox + (x - x0) * k, oy + (y1 - y) * k)

        def Q(pts, closed=True): return poly([S(x, y) for x, y in pts], closed)
        btext(pen, P['title'], 24, 44, 'sans_b', 26, '#202020', 255)
        btext(pen, '1 m = %.0f px   +y up the page   +x right' % k, 24, 68, 'sans', 16, '#505050', 255)
        for nm, q in P['floors']:
            nb = 'not built' in nm
            pen.fill(Q(q), '#d4d0ca' if nb else '#e6dccb'); pen.line(Q(q), 1.5 if nb else 3.0, '#8a847c' if nb else '#3a3530', 255)
        for nm, q in P['floors']:
            if nm:
                cx_ = sum(p_[0] for p_ in q) / len(q); cy_ = max(p_[1] for p_ in q)
                sx_, sy_ = S(cx_, cy_)
                btext(pen, nm, sx_, sy_ + 20, 'sans_b', 15, '#6a5a48', 255, 'center')
        for l_ in P['lines']: pen.line(Q(l_, False), 1.6, '#7a7068', 220)
        for (a_, b_, nm) in P['doors']:
            pen.line(Q([a_, b_], False), 7.0, '#e6dccb', 255); pen.line(Q([a_, b_], False), 2.0, '#b0602a', 255)
            if nm:
                sx_, sy_ = S((a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2)
                btext(pen, nm, sx_ + 4, sy_ - 6, 'sans', 13, '#b0602a', 255)
        for (a_, b_) in P['windows']: pen.line(Q([a_, b_], False), 7.0, '#9cc4e4', 255)
        for nm, q in P['blocks'].items():
            if q is None: continue
            pen.fill(Q(q), '#a89c8c', 200); pen.line(Q(q), 1.2, '#4a4038', 255)
            if not nm.startswith(('kchair', 'row', 'pat_chair', 'seat_', 'chair')) and k > 20:
                sx_ = sum(S(*p_)[0] for p_ in q) / len(q); sy_ = sum(S(*p_)[1] for p_ in q) / len(q)
                btext(pen, nm, sx_, sy_ + 4, 'sans', 12, '#1a1a1a', 255, 'center')
        for (mx, my, nm) in P['marks']:
            sx_, sy_ = S(mx, my)
            pen.fill(oval(sx_, sy_, 3.5), '#2a6a3a'); btext(pen, nm, sx_ + 6, sy_ + 4, 'sans', 12, '#2a6a3a', 255)
        for nm in P['cams']:
            c = CAMS[nm]
            hf = math.atan(960.0 / c['S']); yaw = math.radians(c['yaw'])
            L = P['ray']
            cx_, cy_ = c['x'], c['y']
            pa = (cx_ + L * math.sin(yaw - hf), cy_ + L * math.cos(yaw - hf))
            pb = (cx_ + L * math.sin(yaw + hf), cy_ + L * math.cos(yaw + hf))
            pen.fill(Q([(cx_, cy_), pa, pb]), '#d83a2a', 40); pen.line(Q([(cx_, cy_), pa], False), 1.3, '#c0281a', 220)
            pen.line(Q([(cx_, cy_), pb], False), 1.3, '#c0281a', 220)
            sx_, sy_ = S(cx_, cy_)
            pen.fill(oval(sx_, sy_, 4.5), '#c0281a')
            bx_, by_ = S(cx_ - 0.3 * L * math.sin(yaw), cy_ - 0.3 * L * math.cos(yaw))
            btext(pen, nm.replace('dr_', ''), bx_, by_ + 4, 'sans_b', 12, '#8a1a10', 255, 'center')
        img = surf.makeImageSnapshot().toarray()[:, :, :3]
        tiles.append(np.ascontiguousarray(img))
    while len(tiles) % cols: tiles.append(np.full_like(tiles[0], 240))
    rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
    cv2.imwrite(path, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 88])
    return path


DR_SETS = {'dr_living': dr_living, 'dr_hall': dr_hall, 'dr_kitchen': dr_kitchen, 'dr_bath': dr_bath, 'dr_front': dr_front, 'dr_clinic': dr_clinic,
           'dr_office': dr_office, 'dr_er_bay': dr_er_bay, 'dr_er_wait': dr_er_wait, 'dr_er_entrance': dr_er_entrance, 'dr_hosp_hall': dr_hosp_hall,
           'dr_cardio': dr_cardio, 'dr_car': dr_car, 'dr_run': dr_run, 'dr_outro': dr_outro}
# builder -> its views (the 'view' argument); DR_INSERTS lists the inserts; DR_CAMS the cameras (CAMS[name] = S, h, eye, x, y, yaw, env, note, room)
DR_API = {
    'dr_living': dict(views=('wide', 'chair', 'window', 'window_bus', 'door', 'sunrise'), wait_views=('wide', 'front', 'rows', 'him', 'grandpa', 'side', 'machine'),
                      states=('now', '1979', 'wait'), tod=('night', 'sunrise')),
    'dr_hall': dict(views=('door', 'back', 'livdoor', 'peep', 'floor')),
    'dr_kitchen': dict(views=('phone', 'phone_side', 'wide', 'sink', 'floor', 'hall', 'front'), era=('now', '1979'), tod=('night', 'sunrise')),
    'dr_bath': dict(views=('sink', 'mirror', 'cabinet', 'door')),
    'dr_front': dict(views=('house', 'porch', 'door', 'driveway', 'car', 'street', 'bus', 'bus_far', 'peephole'), tod=('night', 'sunrise')),
    'dr_clinic': dict(views=('wide', 'table', 'door')), 'dr_office': dict(views=('desk', 'wide', 'door'), owner=('halverson', 'narrator')),
    'dr_er_bay': dict(views=('bay', 'side', 'monitor')), 'dr_er_wait': dict(views=('wide', 'chairs', 'desk')), 'dr_er_entrance': dict(views=('ext', 'doors')),
    'dr_hosp_hall': dict(views=('hall', 'chair')), 'dr_cardio': dict(views=('side', 'ruth')),
    'dr_car': dict(views=('front', 'driver', 'back', 'mirror', 'windshield')), 'dr_run': dict(views=('side', 'front', 'rail')),
    'dr_outro': dict(views=('table', 'phone', 'wide')),
}
SETS.update(DR_SETS)
__all__ += list(DR_SETS) + ['dr_insert', 'DR_INSERTS', 'DR_CAMS', 'DR_API', 'DR_SETS', 'dr_plan_map', 'stage_figure', 'D_RULES', 'D_SIGNS', 'D_SIGNS_END', 'D_ADVICE',
            'dr_car_parts', 'dr_car_in_view', 'dr_rain', 'dr_glass_rain', 'dr_wipers', 'dr_cell', 'k_reflect', 'dr_bus_flicker']
