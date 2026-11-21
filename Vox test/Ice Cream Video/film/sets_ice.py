"""sets_ice.py: the sets of "If The Ice Cream Truck Plays Its Song In Winter... DON'T GO OUTSIDE" (Night Policy).

Run inside sets.py's namespace at import, after sets_bus.py (like characters_ice.py inside characters.py), so it reuses
the set engine (BView cameras on a plan in metres, per-face light maps, Room / Piece / build_view, BuBox rooms, BSet
staging API, the Doctor film's far ring / streetlights / car, the bus film's wheels and room runs) and everything here
is part of `sets`:  import sets as ST;  sp = ST.ic_street('house').  Every new name starts with ic_ / IC_ / _ic.

ONE GEOGRAPHY (Birch Lane, Larkfield, a cold snap at minus 31 to minus 40). Plan in metres: x = east, y = north (from
our front wall at y 0 back toward our back yard), Y = up. Our house floor Y 0; the yards, the street and Kessler's
yard IC_G -0.5 (deep snow on top: IC_SNOW m on the lawns; the street is plowed down to IC_G).
  OUR HOUSE (north side, front wall y 0, facing south onto Birch Lane), one storey + attic, x -6.4 .. 6.4, y 0 .. 9:
    kitchen (front-west, window on the front wall over the sink: the cone's outside sill; Lina's step-stool),
    hall (x -2.8 .. -1.4: the front door with a frosted panel and a CLEAR top strip; the bathroom door; the cased
    opening into the living room; the kitchen doorway; the attic HATCH in its ceiling; the bedroom doors at the back),
    bathroom (the smallest room, front, between the hall and the living room: a small frosted window onto the street),
    living room (front-east, L-shaped behind the bathroom: the picture window with curtains and Lina's crack, the couch
    with its BACK to the window facing the TV on the back wall, so the black TV screen reflects the couch and the
    curtain crack behind it; the side table with Dad's radio; the armchair; the floor lamp).
  Outside: our porch / stoop and walk (buried / shoveled), the picket fence along the front yard (buried to half its
  height), Dad's car in the driveway east of the house, our roof (snow, chimney), the streetlight at the kerb.
  BIRCH LANE: kerbs at y -8 (ours) and -16 (Kessler's), plow windrows along both.
  MR. KESSLER'S HOUSE: directly opposite (front wall y -24, facing north), his window opposite our living-room window,
  his porch and door, his chimney (smoke on / off).
  HIS TRUCK: position A (IC_TRUCK_A, until 8:48) at our kerb heading west, the serving window facing our house (between
  our front door and our living-room window); position B (IC_TRUCK_B, from 8:50) at Kessler's kerb heading east, the
  serving window facing his door across his yard (4 m west of his walk, so from our side his door and porch are seen
  past the truck's cab: Mr. Kessler shuffles out in view of our bathroom window). Kessler's window is seen past the
  truck's rear end from our living-room window (a 3 m step van 10 m away hides anything lower behind its roof).
Plan: _work/sets/floorplan.jpg (ic_plan_map).

STAGING DATA: identical to the Doctor / Bus sets: sp.anchors[name] -> Spot (.x .y design px of the feet / point,
.depth, .ppm px per metre there, .height of a 1.85 m adult, .X .Yp .Y plan, .kind, .turn, .seat_y), sp.spot / ppm_at /
floor_y / pick / turn_for / walkable / order_at / light_kw / shadow, ST.stage_figure(sp, who, spot, ...). Depth-to-scale
rule: ppm = S / depth; a figure m metres tall is m * ppm px tall at its feet. Outdoor spots in the snow stand at the
snow surface minus the sink (IC_SINK): feet are hidden in the snow, never floating on it. Every camera is in IC_CAMS.
"""
import math
import numpy as np
import skia

# ====================================================================================================== plan
IC_G = D_GROUND                       # yards / street ground (-0.5)
IC_SNOW = 0.34                        # snow depth on the lawns, the buried walks and the sidewalks
IC_SINK = 0.16                        # how deep a foot sinks into it (spots stand at IC_G + IC_SNOW - IC_SINK)
IC_SNOWY = IC_G + IC_SNOW
IC_FOOT = IC_SNOWY - IC_SINK
IC_CEIL = 2.45
IC_HOUSE = (-6.4, 6.4, 0.0, 9.0)
IC_KIT = (-6.4, -2.8, 0.0, 4.6)
IC_HALL = (-2.8, -1.4, 0.0, 9.0)
IC_BATH = (-1.4, 0.4, 0.0, 2.2)
IC_LIV_A = (0.4, 6.4, 0.0, 5.6)       # the living room: the front part (window wall) ...
IC_LIV_B = (-1.4, 0.4, 2.2, 5.6)      # ... and the part behind the bathroom (the opening to the hall)
IC_LIV_POLY = [(0.4, 0.0), (6.4, 0.0), (6.4, 5.6), (-1.4, 5.6), (-1.4, 2.2), (0.4, 2.2)]
IC_FDOOR = (-2.55, -1.65, 2.05)       # front door on y 0 (x0 hinge, x1 latch, h); swings into the hall
IC_GLASS = (0.13, 0.77, 0.95, 1.50, 1.68)   # door glass: u0, u1 across the leaf, frosted Y0..Y1, clear strip Y1..Y2
IC_BDOOR = (0.95, 1.75, 2.0)          # bathroom door on x -1.4 (y0 hinge, y1, h); swings into the bathroom (+x)
IC_LOPEN = (2.7, 4.5, 2.2)            # the cased opening hall <-> living room on x -1.4 (y0, y1, h)
IC_KDOOR = (2.5, 3.4, 2.05)           # the kitchen doorway on x -2.8 (y0, y1, h)
IC_PWIN = (2.2, 4.6, 0.72, 2.1)       # the picture window on y 0 (x0, x1, sill, top)
IC_KWIN = (-5.4, -4.3, 1.0, 1.95)     # the kitchen window on y 0
IC_BWIN = (-0.78, -0.22, 1.28, 1.86)  # the bathroom's small frosted window on y 0
IC_HATCH = (-2.55, -1.65, 5.5, 6.3)   # the attic hatch in the hall ceiling (x0, x1, y0 hinge edge .. y1)
IC_COUCH = Box(3.4, 1.72, 2.15, 0.92, 0.0, 0.84, 180)     # its back to the window, facing the TV (+y)
IC_TVSTAND = Box(3.4, 5.36, 1.5, 0.44, 0.0, 0.52, 0)
IC_TV = (3.4, 5.42, 1.48, 0.86, 0.58)  # flat TV: centre x, y (screen plane), w, h, bottom Y; facing -y
IC_SIDE = Box(4.86, 1.62, 0.5, 0.5, 0.0, 0.6, 180)        # the side table at the couch's east end (Dad's radio on it)
IC_ARM = Box(5.75, 3.5, 0.9, 0.88, 0.0, 1.0, 90)          # the armchair against the east wall facing west
IC_FLAMP = (6.0, 0.55)
IC_SHELF = Box(1.2, 5.38, 1.2, 0.32, 0.0, 1.9, 0)
IC_COATS = (-2.78, 0.45, 1.25)        # coat hooks on the hall's west wall (x, y0, y1)
IC_STOOL = (-4.85, 0.42)              # Lina's step-stool under the kitchen window
IC_PORCH = (-3.2, -1.0, -1.35, 0.0)   # the stoop at floor level (x0, x1, y0, y1)
IC_STEPS = (-2.6, -1.6, -2.15, -1.35) # three steps down to the walk
IC_WALK = (-2.5, -1.7)                # our front walk (x0, x1) from the steps to the sidewalk
IC_PLIGHT = (-1.35, 1.95, -0.07)      # our porch light, east of the door
IC_FENCE_Y = -6.3                     # the picket fence along the front yard (x -13 .. 6.6, the gate at the walk)
IC_FENCE_X = (-13.0, 6.6)
IC_GATE = (-2.6, -1.6)
IC_DRIVE = (6.9, 10.1, -8.0, 4.5)     # Dad's driveway
IC_CAR = (8.5, -1.6, 180.0)           # Dad's car: nose to the street (centre x, y, facing)
IC_KN, IC_KS = -8.0, -16.0            # north (ours) / south (Kessler's) kerbs; Birch Lane between
IC_WALK_N = (-8.0, -6.6)              # our sidewalk (y0, y1), buried
IC_WALK_S = (-17.4, -16.0)            # Kessler's sidewalk
IC_LAMP = (-5.2, -8.5)                # the streetlight at our kerb (its arm over the street), flickers
IC_LAMPS = [(-26.0, -8.5), (34.0, -8.5)]
# Mr. Kessler's house (front wall y -24, facing north onto the lane)
IC_KH = (-1.4, 8.6, -33.0, -24.0)     # x0, x1, y0 (back), y1 (front)
IC_KWIN2 = (3.6, 5.0, 0.85, 2.05)     # HIS window (front, opposite our picture window) x0, x1, sill, top (above his floor)
IC_KWIN3 = (6.2, 7.4, 0.85, 2.05)
IC_KDOOR2 = (0.95, 1.85, 2.05)        # his front door (x0 hinge, x1)
IC_KPORCH = (0.1, 2.7, -24.0, -22.6)  # his porch deck (x0, x1, y0 house, y1 front)
IC_KSTEPS = (0.9, 1.9, -22.6, -21.8)
IC_KWALK = (1.0, 1.8)
IC_KFLOOR = 0.0                       # his floor = ours (0.5 above the ground)
IC_KCHIM = (7.2, -28.4)
# his truck: (centre x, centre y, facing). fa -90 = heading west (serving side north), 90 = heading east (serving side south)
IC_TRUCK_L, IC_TRUCK_LC, IC_TRUCK_W = 6.0, 1.75, 2.25
IC_TRUCK_Y0, IC_TRUCK_Y1 = 0.5, 3.0  # body bottom / roof above the ground
IC_TRUCK_FLOOR = 0.6                  # his floor inside (above the ground) where he stands at the serving window
IC_SWIN = (-0.7, 0.7, 1.55, 2.35)     # serving window on the body's curb side: n0, n1 (body-local, + toward the front), Y0, Y1
IC_TRUCK_A = (-0.6, -9.55, -90.0)
IC_TRUCK_B = (-2.7, -14.45, 90.0)  # its cab ends short of his walk, so his door and porch stay in view from our side
IC_PLOW_LANE = (-11.0, -13.0)         # the plow's lane y (westbound, eastbound)

IC_PINK = '#ff9ec8'                   # the serving window: the warmest light in the film (the lure)
IC_STRIPE = '#e58fb4'
IC_FLAKE = '#ddebf5'
IC_ORANGE = '#ff8a1e'                 # Dad's beacon
IC_MOON = '#9ab4ff'
IC_STREET_C = '#d6e2ff'               # the streetlight: a cold mercury white
IC_WARM = '#ffc98a'
IC_RED = '#c8262a'                    # Benny's mitten
IC_LINA_MITTEN = '#f2c23a'            # Lina's (yellow, to match her coat)
IC_MITTENS = ['#c8262a', '#3a6ab0', '#2e8a5a', '#8a4ab0', '#e0e0d8', '#c87a2a', '#4a4a6a']
IC_PAL = dict(siding='#a8b4c4', siding_k='#9a8c7a', trim='#eef0f2', door='#2e4a6a', door_k='#5a3424', roof='#3a3e48', roof_k='#4a3a34',
              liv_paper='#d8c4a0', liv_ink='#b89a74', hall_paper='#b8c4b0', hall_ink='#98a890', kit_paper='#e8dcc0', bath_tile='#cfe0e4',
              floor='#9a6a40', carpet='#7a5e48', couch='#4a6a8a', couch_d='#2e4a66', curt='#7a3a4a')

# ====================================================================================================== grades
_GR.setdefault('ic_night', dict(contrast=1.08, pivot=0.24, gamma=1.04, sat=1.06, wb=(0.94, 1.0, 1.1), floor='#060a16',
                                bloom=0.9, bloom_thr=224, vignette=0.4, grain=0.6, shoulder=0.45))
_GR.setdefault('ic_ext', dict(contrast=1.1, pivot=0.24, gamma=1.0, sat=1.08, wb=(0.93, 1.0, 1.12), floor='#050a18',
                              bloom=1.0, bloom_thr=222, vignette=0.36, grain=0.6, shoulder=0.45))
_GR.setdefault('ic_warm', dict(exposure=0.05, contrast=1.04, pivot=0.25, gamma=1.05, sat=1.08, wb=(1.06, 1.0, 0.92), floor='#0e0a08',
                               bloom=0.85, bloom_thr=226, vignette=0.42, grain=0.45, shoulder=0.5))
_GR.setdefault('ic_dark', dict(contrast=1.1, pivot=0.22, gamma=1.06, sat=0.98, wb=(0.92, 0.99, 1.12), floor='#04060e',
                               bloom=0.95, bloom_thr=220, vignette=0.36, grain=0.8, shoulder=0.45))
_GR.setdefault('ic_morning', dict(exposure=0.04, contrast=1.02, pivot=0.26, gamma=1.04, sat=1.1, wb=(1.06, 1.0, 0.92), floor='#14100c',
                                  bloom=0.9, bloom_thr=228, vignette=0.45, grain=0.35, shoulder=0.55))
_GR.setdefault('ic_1958', dict(exposure=0.02, contrast=1.06, pivot=0.25, gamma=1.02, sat=0.4, mono=0.72, tint='#d8c4a4', wb=(1.0, 1.0, 1.0),
                               floor='#14100a', bloom=0.9, bloom_thr=214, vignette=0.6, grain=1.3, soft=0.35, shoulder=0.5))
_GR.setdefault('ic_ins', dict(contrast=1.04, pivot=0.25, gamma=1.04, sat=1.04, wb=(1.0, 1.0, 1.0), floor='#0a0a0c',
                              bloom=0.5, bloom_thr=236, vignette=0.5, grain=0.45, shoulder=0.5))
_GR.setdefault('ic_ins_cold', dict(contrast=1.06, pivot=0.25, gamma=1.02, sat=1.02, wb=(0.94, 1.0, 1.1), floor='#060a14',
                                   bloom=0.7, bloom_thr=230, vignette=0.45, grain=0.6, shoulder=0.5))
_GR.setdefault('ic_ins_warm', dict(exposure=0.0, contrast=1.04, pivot=0.26, gamma=1.0, sat=1.04, wb=(1.04, 1.0, 0.95), floor='#100c08',
                                   bloom=0.0, bloom_thr=250, vignette=0.6, grain=0.3, shoulder=0.6))

IC_CAMS = []


def _icam(name, S, h, eye, x, y, yaw, env=None, note='', room='', pitch=0.0):
    _cam(name, S, h, eye, x, y, yaw, env or _env(), note, room, pitch)
    if name not in IC_CAMS: IC_CAMS.append(name)


def ic_pass(t0, dur=4.0, rate=1.3, k=1.0):
    """Level spec for Dad's beacon passing: rises, sweeps (pulses at the beacon's rotation rate), fades. t0 = mid-pass."""
    def f(t):
        x = (t - t0) / max(0.1, dur / 2)
        env = max(0.0, 1.0 - x * x)
        return k * env * (0.25 + 0.75 * max(0.0, math.cos((t - t0) * rate * 2 * math.pi)) ** 3)
    return f


def ic_flicker(t0=0.0, n=3, gap=0.5, seed=5):
    """Level spec for the streetlight: steady, then n hard flickers from t0 ('for one flicker, his face is long')."""
    def f(t):
        for i in range(n):
            a = t0 + i * gap
            if a <= t < a + 0.09: return 0.05
            if a + 0.13 <= t < a + 0.17: return 0.25
        return 1.0
    return f


# ====================================================================================================== snow + ground
def _snow_art(seed=1, c='#e8eef8', sparkle=True, drift=True):
    def art(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'grunge', 0.22, 'overlay', 3.0)
        rng = np.random.default_rng(abs(int(seed)))
        if drift:
            for i in range(int(W * H / 90000) + 8):                         # soft wind ripples / drifts
                x, y = rng.uniform(0, W), rng.uniform(0, H)
                w = rng.uniform(150, 600); h = w * rng.uniform(0.05, 0.12)
                p_.fill(oval(x, y, w, h), '#ffffff', 26, blur=h * 0.8)
                p_.fill(oval(x + w * 0.1, y + h * 0.9, w * 0.8, h * 0.5), '#5a6a9a', 18, blur=h * 0.8)
        if sparkle:
            for i in range(int(W * H / 2500)):
                x, y = rng.uniform(0, W), rng.uniform(0, H)
                p_.fill(oval(x, y, rng.uniform(0.6, 1.6)), '#ffffff', int(rng.uniform(60, 200)))
    return art


def _bank(pen, v, x0, x1, y, w, h, side=1, seed=0, Y=None):
    """A plow windrow / snowbank along x at plan y (its crest), w wide, h tall: a rounded, lumpy profile drawn as four
    lit strips (far side first), a soft crest highlight and blue shadow in the hollows."""
    Y = IC_G if Y is None else Y
    n = max(6, int((x1 - x0) / 0.9))
    rng = np.random.default_rng(abs(int(seed)))
    xs = np.linspace(x0, x1, n + 1)
    hs = np.array([h * (0.78 + 0.34 * rng.random()) for _ in xs])
    hs[0] *= 0.35; hs[-1] *= 0.35                                          # tapered ends
    prof = [(-0.5, 0.0), (-0.3, 0.72), (-0.08, 1.0), (0.14, 0.92), (0.32, 0.62), (0.5, 0.0)]
    strips = []
    for j in range(len(prof) - 1):
        (a0, b0), (a1, b1) = prof[j], prof[j + 1]
        nrm = _norm3((0.0, (a1 - a0) * w, -(b1 - b0) * h))                  # across-profile normal (y, Y)
        nrm = (0.0, abs(nrm[1]) + 0.15, nrm[2] if nrm[2] != 0 else 0.0)
        nrm = _norm3((0.0, (a1 - a0) * w, (b0 - b1) * h)) if False else _norm3((0.0, abs((a1 - a0) * w), -(b1 - b0) * h * (1 if a1 > 0 else 1)))
        top = [(xs[i], Y + hs[i] * b0, y + a0 * w) for i in range(len(xs))]
        bot = [(xs[i], Y + hs[i] * b1, y + a1 * w) for i in range(len(xs))][::-1]
        mid_y = y + (a0 + a1) / 2 * w
        strips.append((abs(v.d((x0 + x1) / 2, mid_y)), top + bot, (0.0, 0.6, -1.0 if (a0 + a1) < 0 else 1.0), (b0 + b1) / 2))
    strips.sort(key=lambda s_: -s_[0])
    for (_, pts, nrm, hb) in strips:
        pts = [p_ for p_ in pts if v.d(p_[0], p_[2]) > 0.3]
        if len(pts) < 3: continue
        q = v.poly3(pts)
        if q.isEmpty(): continue
        cen = ((x0 + x1) / 2, Y + h * hb, y)
        pen.fill(q, lit(mix('#9aa8cc', '#eef4ff', hb), cen, _norm3(nrm)))
        pen.cv.save(); pen.cv.clipPath(q, skia.ClipOp.kIntersect, True)
        pen.texture(q, 'grunge', 0.22, 'overlay', 2.0)
        pen.cv.restore()
    crest = [(xs[i], Y + hs[i], y - 0.08 * w) for i in range(len(xs)) if v.d(xs[i], y) > 0.3]
    if len(crest) > 1:
        pen.line(v.poly3(crest, False), 1.2, '#ffffff', 110)


def ic_ground(pen, v, o):
    """The snow world under Birch Lane (cached): the lawns under deep snow, the plowed street, the plow windrows along
    both kerbs, our walk (o['walk'] 'buried' | 'shoveled' | 'trodden'), Kessler's walk (o['kwalk']), the driveway."""
    tod = o.get('tod', 'night')
    night = tod in ('night', '1958')
    snow = '#cad6ee' if night else '#e4e0e4'
    F = floor_face(-140.0, 140.0, -140.0, 40.0, IC_SNOWY)
    draw_face(pen, v, F, _snow_art(3), snow, ao=False, line=False)
    # the street: plowed, packed, a fresh dusting (no tracks: his truck never leaves any)
    Fs = floor_face(-140.0, 140.0, IC_KS, IC_KN, IC_G + 0.02)
    def street_art(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'grunge', 0.35, 'overlay', 2.0)
        for k in range(9):                                                   # the plow blade's long faint lines
            yy = H * (0.08 + 0.1 * k)
            p_.fill(rect(0, yy, W, 3), '#ffffff', 40); p_.fill(rect(0, yy + 5, W, 2), '#3a4a7a', 30)
        if o.get('ruts'):
            for yy in (H * 0.3, H * 0.42, H * 0.6, H * 0.72):
                p_.fill(rect(0, yy, W, 18), '#5a6a8a', 70, blur=4)
    draw_face(pen, v, Fs, street_art, '#a8b6d2' if night else '#d8d4d0', ao=False, line=False)
    # the windrows (plow banks) along both kerbs, broken at the walks / driveway
    for (x0, x1) in ((-140.0, IC_WALK[0] - 0.3), (IC_WALK[1] + 0.3, IC_DRIVE[0] - 0.2), (IC_DRIVE[1] + 0.2, 140.0)):
        _bank(pen, v, x0, x1, IC_KN + 0.55, 1.1, 0.78, 1, seed=int(x0) + 200)
    for (x0, x1) in ((-140.0, IC_KWALK[0] - 0.3), (IC_KWALK[1] + 0.3, 140.0)):
        _bank(pen, v, x0, x1, IC_KS - 0.55, 1.1, 0.72, -1, seed=int(x0) + 300)
    # our walk and Kessler's walk: trenches when shoveled, smooth / trodden otherwise
    for (wx, y0, y1, state) in ((IC_WALK, IC_KN, IC_STEPS[2], o.get('walk', 'buried')), (IC_KWALK, IC_KSTEPS[1], IC_KS, o.get('kwalk', 'buried'))):
        if state == 'shoveled':
            Fw = floor_face(wx[0], wx[1], min(y0, y1), max(y0, y1), IC_G + 0.03)
            draw_face(pen, v, Fw, lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'asphalt', 0.5, 'overlay', 1.4), '#6a7080' if night else '#9a9894', ao=False, line=False)
            for xx, nx in ((wx[0], 1), (wx[1], -1)):                       # the cut walls of the trench
                q = v.poly3([(xx, IC_G, min(y0, y1)), (xx, IC_G, max(y0, y1)), (xx, IC_SNOWY, max(y0, y1)), (xx, IC_SNOWY, min(y0, y1))])
                if not q.isEmpty() and v.visible((xx, IC_G + 0.1, (y0 + y1) / 2), (nx, 0, 0)): pen.fill(q, lit('#c4d0e8' if night else '#e8e4dc', (xx, IC_G + 0.1, (y0 + y1) / 2), (nx, 0, 0)))
        elif state == 'trodden':
            rng = np.random.default_rng(31)
            for k in range(int(abs(y1 - y0) / 0.35)):
                yy = min(y0, y1) + 0.2 + k * 0.35; xx = (wx[0] + wx[1]) / 2 + (0.12 if k % 2 else -0.12)
                if v.d(xx, yy) > 0.4: pen.fill(ellipse3(v, xx, yy, 0.09, 0.15, IC_SNOWY + 0.002), '#5a6a9a', 110)
    # the driveway (plowed by Dad before his shift: a trench to the street)
    dx0, dx1, dy0, dy1 = IC_DRIVE
    Fd = floor_face(dx0, dx1, dy0, dy1, IC_G + 0.03)
    draw_face(pen, v, Fd, lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'grunge', 0.4, 'overlay', 2.0), '#9aa6c2' if night else '#cfcbc6', ao=False, line=False)
    for xx, nx in ((dx0, 1), (dx1, -1)):
        q = v.poly3([(xx, IC_G, dy0), (xx, IC_G, dy1), (xx, IC_SNOWY + 0.25, dy1), (xx, IC_SNOWY + 0.25, dy0)])
        if not q.isEmpty() and v.visible((xx, IC_G + 0.1, (dy0 + dy1) / 2), (nx, 0, 0)): pen.fill(q, lit('#c8d4ec' if night else '#ece8e0', (xx, IC_G + 0.1, 0), (nx, 0, 0)))
    for tr in o.get('tracks') or []:                                         # footprint trails: [(kind, [(x, y), ...])]
        kind, pts = tr
        r = 0.06 if kind in ('child', 'benny') else 0.075
        for i in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            L = math.hypot(bx - ax, by - ay); n = max(1, int(L / (0.32 if kind == 'benny' else 0.4)))
            for k in range(n):
                f = (k + 0.5) / n; x = ax + (bx - ax) * f; y = ay + (by - ay) * f
                side = 0.08 if k % 2 else -0.08
                nx_, ny_ = -(by - ay) / max(L, 1e-6), (bx - ax) / max(L, 1e-6)
                x += nx_ * side; y += ny_ * side
                if v.d(x, y) > 0.4:
                    pen.fill(ellipse3(v, x, y, r, r * 1.9, IC_SNOWY + 0.003), '#4a5a8a' if night else '#a8a4b0', 150)
                    pen.fill(ellipse3(v, x + 0.01, y + 0.02, r * 0.7, r * 1.3, IC_SNOWY + 0.004), '#2a3462' if night else '#8a8698', 120)


# ====================================================================================================== houses (snow roofs)
def _icicles(pen, v, A, B_, n=14, L=0.35, seed=0):
    """A fringe of icicles hanging from the plan segment A -> B_ (3D points at the eave)."""
    rng = np.random.default_rng(abs(int(seed)))
    for k in range(n):
        f = (k + rng.uniform(0.1, 0.9)) / n
        P = (A[0] + (B_[0] - A[0]) * f, A[1], A[2] + (B_[2] - A[2]) * f)
        if v.d(P[0], P[2]) < 0.4: continue
        ln = L * rng.uniform(0.25, 1.0)
        x, y = v.p(*P); s = v.s(P[0], P[2]); w = max(1.0, 0.035 * s)
        tip = v.p(P[0], P[1] - ln, P[2])
        pen.fill(poly([(x - w, y), (x + w, y), tip]), '#e8f4ff', 220)
        pen.seg((x - w * 0.3, y), (tip[0], tip[1] - 2), max(0.6, w * 0.3), '#ffffff', 200)


def _roof_slope(pen, v, q, n, c, snow=1.0, seed=0, ridge_snow=True):
    cen = tuple(sum(p_[i] for p_ in q) / 4 for i in range(3))
    if not v.visible(cen, _norm3(n)): return
    path = v.poly3(q)
    if path.isEmpty(): return
    if snow > 0.01:
        pen.fill(path, lit(mix(c, '#dfe8f6', 0.9 * snow), cen, _norm3(n)))
        b = path.computeTightBounds()
        pen.cv.save(); pen.cv.clipPath(path, skia.ClipOp.kIntersect, True)
        pen.texture(path, 'grunge', 0.22, 'overlay', 2.0)
        rng = np.random.default_rng(abs(int(seed)))
        for k in range(10):                                                  # wind-carved lines
            f = rng.uniform(0.1, 0.9)
            A = tuple(q[0][i] + (q[3][i] - q[0][i]) * f for i in range(3)); B_ = tuple(q[1][i] + (q[2][i] - q[1][i]) * f for i in range(3))
            if v.d(A[0], A[2]) > 0.3 and v.d(B_[0], B_[2]) > 0.3: pen.seg(v.p(*A), v.p(*B_), 1.0, '#7a8ab8', 50)
        pen.cv.restore()
    else:
        pen.fill(path, lit(c, cen, _norm3(n)))
        for k in range(12):
            f = (k + 0.5) / 12
            A = tuple(q[0][i] + (q[3][i] - q[0][i]) * f for i in range(3)); B_ = tuple(q[1][i] + (q[2][i] - q[1][i]) * f for i in range(3))
            if v.d(A[0], A[2]) > 0.3 and v.d(B_[0], B_[2]) > 0.3: pen.seg(v.p(*A), v.p(*B_), 1.0, '#000000', 70)
    pen.line(path, 1.1)


def ic_house(pen, v, H, tod='night'):
    """A one-storey snowbound house from outside. H = dict(x0, x1, yf (front wall y), depth, face (+1: front faces -y,
    our side; -1: faces +y, across the street), floor (floor Y), eave (above floor), ridge (above floor), siding, trim,
    roof, door=(x0, x1, h, colour, glass), wins=[(name, x0, x1, sill, top)], chimney=(x, y, w), porch=(x0, x1, depth),
    steps=(x0, x1, run), snow 0..1, icicles, plight (x) porch light lantern, frost (window frost 0..1))."""
    x0, x1, yf, dep, fc = H['x0'], H['x1'], H['yf'], H['depth'], H['face']
    yb = yf + dep * fc                                                       # the back wall
    Fl = H.get('floor', 0.0); E = Fl + H.get('eave', 2.6); R = Fl + H.get('ridge', 4.9)
    G = IC_G
    sid, trim = H.get('siding', IC_PAL['siding']), H.get('trim', IC_PAL['trim'])
    night = tod in ('night', '1958')
    ym, yfr = (yf, yb) if fc > 0 else (yb, yf)                               # y min / max
    walls = {'front': ((x1, yf), (x0, yf)) if fc > 0 else ((x0, yf), (x1, yf)),
             'back': ((x0, yb), (x1, yb)) if fc > 0 else ((x1, yb), (x0, yb)),
             'west': ((x0, yb), (x0, yf)) if fc > 0 else ((x0, yf), (x0, yb)),
             'east': ((x1, yf), (x1, yb)) if fc > 0 else ((x1, yb), (x1, yf))}
    # outward normals: front -y*fc ... the walls are drawn from outside: wall_face(a, b) shows its right side
    for nm in ('back', 'west', 'east', 'front'):
        a, b = walls[nm]
        a_, b_ = (b, a)                                                      # walk the run so the OUTSIDE is visible
        F = wall_face(a_, b_, G, E)
        if not v.visible(F.O, F.n): continue
        L = math.hypot(b_[0] - a_[0], b_[1] - a_[1]); ux = ((b_[0] - a_[0]) / L, (b_[1] - a_[1]) / L)
        def u_of(x, y, a_=a_, ux=ux): return (x - a_[0]) * ux[0] + (y - a_[1]) * ux[1]
        def art(p_, W, Hh, nm=nm, u_of=u_of):
            pat(p_, W, Hh, 'clapboard', '#000000', 110)
            p_.texture(rect(0, 0, W, Hh), 'grunge', 0.3, 'overlay', 1.2)
            p_.fill(rect(0, Hh - (Fl - G) * 100 - 2, W, (Fl - G) * 100 + 2), '#6a6a72')       # foundation
            p_.fill(rect(0, 0, W, 8), trim)
            p_.fill(rect(0, 0, 10, Hh), trim); p_.fill(rect(W - 10, 0, 10, Hh), trim)
            for (wn, wx0, wx1, sl, tp) in H.get('wins', []):
                side = wn.split(':')[0] if ':' in wn else 'front'
                if side != nm: continue
                ua, ub = sorted((u_of(wx0, yf) if nm in ('front', 'back') else u_of(x0 if nm == 'west' else x1, wx0),
                                 u_of(wx1, yf) if nm in ('front', 'back') else u_of(x0 if nm == 'west' else x1, wx1)))
                ua *= 100; ub *= 100
                yt = Hh - (Fl + tp - G) * 100; ybm = Hh - (Fl + sl - G) * 100
                if H.get('shutters', True) and ub - ua > 70:
                    for sx in (ua - 30, ub + 6):
                        p_.fill(rect(sx, yt, 24, ybm - yt), H.get('shutter', '#2a3a52')); p_.line(rect(sx, yt, 24, ybm - yt), 0.8)
                p_.fill(rect(ua - 7, yt - 8, ub - ua + 14, ybm - yt + 16), trim)
                p_.fill(rect(ua, yt, ub - ua, ybm - yt), '#0c1222' if night else '#4a5a6e')
                p_.linear(rect(ua, yt, ub - ua, ybm - yt), ua, yt, ub, ybm, [(0, '#ffffff', 0), (0.5, '#a8c0e8', 46 if night else 80), (1, '#ffffff', 0)])
                fr = H.get('frost', 0.6)
                if fr > 0:                                                    # frost fans in the pane corners
                    for (cx_, cy_) in ((ua, yt), (ub, yt), (ua, ybm), (ub, ybm)):
                        p_.fill(oval(cx_, cy_, (ub - ua) * 0.35 * fr, (ybm - yt) * 0.3 * fr), '#e8f2ff', 70, blur=6)
                nl = 2 if ub - ua > 80 else 1
                for k in range(1, nl): p_.fill(rect(ua + (ub - ua) * k / nl - 2, yt, 4, ybm - yt), trim)
                p_.fill(rect(ua, (yt + ybm) / 2 - 2, ub - ua, 4), trim)
                p_.fill(rect(ua - 12, ybm, ub - ua + 24, 6), trim)
                p_.fill(rrect(ua - 12, ybm - 7, ub - ua + 24, 9, 4), '#eef4ff', 235)                  # snow on the sill
            dr = H.get('door')
            if dr and nm == 'front':
                ua, ub = sorted((u_of(dr[0], yf) * 100, u_of(dr[1], yf) * 100))
                yt = Hh - (Fl + dr[2] - G) * 100; ybm = Hh - (Fl - G) * 100
                p_.fill(rect(ua - 12, yt - 14, ub - ua + 24, ybm - yt + 14), trim); p_.line(rect(ua - 12, yt - 14, ub - ua + 24, ybm - yt + 14), 0.8)
                if H.get('door_open'):
                    p_.fill(rect(ua, yt, ub - ua, ybm - yt), '#0a0a10' if night else '#2a2420')
                else:
                    p_.cv.save(); p_.cv.translate(ua, yt)
                    _door_out_art(dr[3], dr[4], H.get('rules_out', False))(p_, ub - ua, ybm - yt)
                    p_.cv.restore()
            if H.get('number') and nm == 'front' and dr:
                btext(p_, H['number'], u_of(dr[1] + 0.35, yf) * 100, Hh - (Fl + 1.75 - G) * 100, 'serif_b', 13, '#2a2a2a', 220, 'center')
        draw_face(pen, v, F, art, sid, ao=False, lw=1.2)
    # the gable roof: slopes over the front / back, gables on the west / east ends
    ov = 0.35
    rx0, rx1 = x0 - ov, x1 + ov
    yfe, ybe = yf - ov * fc, yb + ov * fc
    yr = (yf + yb) / 2
    snow = H.get('snow', 1.0)
    _roof_slope(pen, v, [(rx0, E, yfe), (rx1, E, yfe), (rx1, R, yr), (rx0, R, yr)], (0, 0.8, -0.6 * fc), H.get('roof', IC_PAL['roof']), snow, 11)
    _roof_slope(pen, v, [(rx1, E, ybe), (rx0, E, ybe), (rx0, R, yr), (rx1, R, yr)], (0, 0.8, 0.6 * fc), H.get('roof', IC_PAL['roof']), snow, 12)
    for (xx, n) in ((x0, (-1, 0, 0)), (x1, (1, 0, 0))):
        tri = [(xx, E, yf), (xx, E, yb), (xx, R - 0.12, yr)]
        if not v.visible(tri[2], n): continue
        path = v.poly3(tri)
        if not path.isEmpty():
            pen.fill(path, lit(_darken(sid, 0.06), tri[2], n)); pen.line(path, 1.0)
            c = v.p(xx, (E + R) / 2 - 0.2, yr); s = v.s(xx, yr)
            if v.d(xx, yr) > 0.5: pen.fill(rrect(c[0] - 0.18 * s, c[1] - 0.22 * s, 0.36 * s, 0.4 * s, 0.05 * s), '#10141e' if night else '#3a4452', 220)
    # snow lip along the front eave (it overhangs a little) and icicles
    if snow > 0.01:
        A = (rx0, E + 0.02, yfe); B_ = (rx1, E + 0.02, yfe)
        if v.d(A[0], A[2]) > 0.3 and v.d(B_[0], B_[2]) > 0.3 and v.visible((0.5 * (x0 + x1), E, yfe), (0, 0, -fc)):
            q = v.poly3([A, B_, (rx1, E - 0.1, yfe - 0.02 * fc), (rx0, E - 0.1, yfe - 0.02 * fc)])
            if not q.isEmpty(): pen.fill(q, '#eef4ff', 230)
            if H.get('icicles', True): _icicles(pen, v, (rx0 + 0.3, E - 0.08, yfe), (rx1 - 0.3, E - 0.08, yfe), int((rx1 - rx0) * 2.2), 0.4, seed=int(x0 * 7))
    ch = H.get('chimney')
    if ch:
        cB = Box(ch[0], ch[1], ch[2], ch[2] * 0.8, R - 1.0, R + 0.9, 0)
        draw_box(pen, v, cB, {'all': dict(fill='#6a3a2e', art=lambda p_, W, Hh: pat(p_, W, Hh, 'brick', '#2a1a14', 120)), 'top': '#1a1a1a'}, lw=1.0)
        cap = Box(ch[0], ch[1], ch[2] + 0.06, ch[2] * 0.8 + 0.06, R + 0.9, R + 0.98, 0)
        draw_box(pen, v, cap, {'all': '#eef4ff'}, lw=0.8)
    pc = H.get('porch')
    if pc:
        px0, px1, pd = pc
        py0, py1 = (yf - pd, yf) if fc > 0 else (yf, yf + pd)
        deck = Box((px0 + px1) / 2, (py0 + py1) / 2, px1 - px0, pd, G, Fl, 0)
        draw_box(pen, v, deck, {'top': dict(fill='#dfe8f6', art=_snow_art(5, sparkle=False, drift=False)), 'all': '#d8d4cc'}, lw=1.0)
        st = H.get('steps')
        if st:
            sx0, sx1, run = st
            n = 3; rise = (Fl - G) / n
            outer = py0 - run if fc > 0 else py1 + run
            inner = py0 if fc > 0 else py1
            for i in range(n):
                ya = outer + (inner - outer) * i / n
                B = Box((sx0 + sx1) / 2, (ya + inner) / 2, sx1 - sx0, abs(inner - ya), G, G + (i + 1) * rise, 0)
                draw_box(pen, v, B, {'top': '#e8eef8', 'all': '#cfcbc4'}, lw=0.8)
        for px in (px0 + 0.08, px1 - 0.08):
            pyy = py0 + 0.08 if fc > 0 else py1 - 0.08
            draw_box(pen, v, Box(px, pyy, 0.12, 0.12, Fl, Fl + 2.4, 0), {'all': trim}, lw=0.8)
        roofq = [(px0 - 0.15, Fl + 2.42, py0 - 0.15 if fc > 0 else py1 + 0.15), (px1 + 0.15, Fl + 2.42, py0 - 0.15 if fc > 0 else py1 + 0.15),
                 (px1 + 0.15, Fl + 2.72, yf), (px0 - 0.15, Fl + 2.72, yf)]
        nrm = (0, 0.85, -0.5 * fc)
        cen = ((px0 + px1) / 2, Fl + 2.55, (py0 + py1) / 2)
        path = v.poly3(roofq)
        if not path.isEmpty():
            if v.visible(cen, _norm3(nrm)): pen.fill(path, lit('#dfe8f6', cen, _norm3(nrm)))
            else: pen.fill(path, lit('#d0ccc4', cen, (0, -1, 0)))
            pen.line(path, 1.0)
        A = (px0 - 0.15, Fl + 2.4, roofq[0][2]); B_ = (px1 + 0.15, Fl + 2.4, roofq[0][2])
        if H.get('icicles', True) and v.d(A[0], A[2]) > 0.4: _icicles(pen, v, A, B_, 9, 0.3, seed=int(px0 * 13) + 3)
    pl = H.get('plight')
    if pl is not None:
        lY = Fl + 1.95; ly = yf - 0.07 * fc
        if v.d(pl, ly) > 0.3: draw_box(pen, v, Box(pl, ly - 0.04 * fc, 0.14, 0.12, lY - 0.13, lY + 0.13, 0), {'all': '#1a1a1a', 'front': '#d8c890', 'back': '#d8c890'}, lw=0.8)


def _door_out_art(c, glass=None, rules=False):
    """A front door seen from outside: four raised panels, or (glass = IC_GLASS) a frosted panel with the clear strip."""
    def art(p_, W, H):
        p_.fill(rect(0, 0, W, H), c); p_.texture(rect(0, 0, W, H), 'wood', 0.3, 'overlay', 0.8, 90)
        if glass:
            u0, u1, Y0, Y1, Y2 = glass
            gy = lambda Y: H - Y * 100
            p_.fill(rect(u0 * 100, gy(Y2), (u1 - u0) * 100, gy(Y0) - gy(Y2)), '#1a2234')
            p_.fill(rect(u0 * 100, gy(Y1), (u1 - u0) * 100, gy(Y0) - gy(Y1)), '#b8c4d8', 200)
            p_.texture(rect(u0 * 100, gy(Y1), (u1 - u0) * 100, gy(Y0) - gy(Y1)), 'grunge', 0.4, 'overlay', 0.5)
            p_.line(rect(u0 * 100, gy(Y2), (u1 - u0) * 100, gy(Y0) - gy(Y2)), 2.0, '#1a1a1a', 200)
            p_.fill(rect(u0 * 100, gy(Y1) - 1.5, (u1 - u0) * 100, 3), _darken(c, 0.3))
            for (x0, y0, w, h) in ((10, H - 85, W / 2 - 15, 72), (W / 2 + 5, H - 85, W / 2 - 15, 72)):
                p_.fill(rect(x0, y0, w, h), _darken(c, 0.12)); p_.line(rect(x0, y0, w, h), 1.0, '#000000', 90)
        else:
            for (x0, y0, w, h) in ((10, 14, W / 2 - 15, H * 0.42), (W / 2 + 5, 14, W / 2 - 15, H * 0.42),
                                   (10, H * 0.5, W / 2 - 15, H * 0.44), (W / 2 + 5, H * 0.5, W / 2 - 15, H * 0.44)):
                p_.fill(rect(x0, y0, w, h), _darken(c, 0.12)); p_.line(rect(x0, y0, w, h), 1.0, '#000000', 90)
        kx = W - 9
        p_.fill(oval(kx, H - 97, 3.2), '#c8b070'); p_.line(oval(kx, H - 97, 3.2), 0.6)
        p_.fill(oval(kx, H - 114, 2.4), '#c8b070')
        if rules:
            p_.fill(rect(W * 0.22, H * 0.52, W * 0.56, 34), '#f4f0e4', 245)
            for k in range(7): p_.fill(rect(W * 0.26, H * 0.52 + 6 + k * 4, W * 0.48 * (0.6 + 0.4 * ((k * 37) % 5) / 4), 1.4), '#2a2a3a', 200)
    return art


def _ic_our_house(o):
    return dict(x0=IC_HOUSE[0], x1=IC_HOUSE[1], yf=0.0, depth=9.0, face=1, floor=0.0, eave=2.6, ridge=5.0, siding=IC_PAL['siding'],
                door=(IC_FDOOR[0], IC_FDOOR[1], IC_FDOOR[2], IC_PAL['door'], IC_GLASS), door_open=o.get('door_open', False),
                wins=[('kitchen', IC_KWIN[0], IC_KWIN[1], IC_KWIN[2], IC_KWIN[3]), ('bath', IC_BWIN[0], IC_BWIN[1], IC_BWIN[2], IC_BWIN[3]),
                      ('liv', IC_PWIN[0], IC_PWIN[1], IC_PWIN[2], IC_PWIN[3]), ('east:side', 2.2, 3.2, 0.9, 2.0), ('west:side', 6.0, 7.0, 0.9, 2.0)],
                chimney=(-4.2, 4.0, 0.7), porch=(IC_PORCH[0], IC_PORCH[1], -IC_PORCH[2]), steps=(IC_STEPS[0], IC_STEPS[1], IC_STEPS[3] - IC_STEPS[2]),
                plight=IC_PLIGHT[0], snow=1.0, frost=o.get('frost_out', 0.7), number='14', rules_out=False)


def _ic_kessler_house(o):
    return dict(x0=IC_KH[0], x1=IC_KH[1], yf=IC_KH[3], depth=IC_KH[3] - IC_KH[2], face=-1, floor=IC_KFLOOR, eave=2.55, ridge=4.7,
                siding=IC_PAL['siding_k'], trim='#e8e2d4', roof=IC_PAL['roof_k'], shutter='#3a2a22',
                door=(IC_KDOOR2[0], IC_KDOOR2[1], IC_KDOOR2[2], IC_PAL['door_k'], None), door_open=o.get('kdoor_open', False),
                wins=[('his', IC_KWIN2[0], IC_KWIN2[1], IC_KWIN2[2], IC_KWIN2[3]), ('k2', IC_KWIN3[0], IC_KWIN3[1], IC_KWIN3[2], IC_KWIN3[3]),
                      ('west:kside', -27.0, -25.8, 0.9, 2.0)],
                chimney=(IC_KCHIM[0], IC_KCHIM[1], 0.75), porch=(IC_KPORCH[0], IC_KPORCH[1], IC_KPORCH[3] - IC_KPORCH[2]),
                steps=(IC_KSTEPS[0], IC_KSTEPS[1], IC_KSTEPS[1] - IC_KSTEPS[0]) if False else (IC_KSTEPS[0], IC_KSTEPS[1], IC_KSTEPS[3] - IC_KSTEPS[2]),
                plight=2.25, snow=1.0, frost=0.8, number='15')


IC_NEIGHBOURS = [  # (x0, x1, yf, face, siding, roof, porch light x)
    (-21.0, -10.0, 0.0, 1, '#b8a890', '#3a3a40', -14.2), (13.0, 24.0, 0.0, 1, '#9aa8a0', '#40383a', 17.0),
    (-17.0, -5.0, -24.0, -1, '#a8a0b4', '#3a3a44', -9.0), (12.5, 23.5, -24.0, -1, '#c0b098', '#3e3a3a', 16.0),
    (-36.0, -25.0, 0.0, 1, '#a4b0b8', '#3a3a40', -30.0), (28.0, 39.0, -24.0, -1, '#b0a8a0', '#3a3838', 32.0),
    (27.0, 38.0, 0.0, 1, '#aab4a4', '#3a3a3e', 31.0), (-32.0, -21.0, -24.0, -1, '#b8b0a0', '#383a40', -26.0)]


def _ic_neighbour(i, era='now'):
    x0, x1, yf, fc, sid, roof, pl = IC_NEIGHBOURS[i]
    w = x1 - x0
    wins = [('front', x0 + 1.2, x0 + 2.6, 0.9, 2.05), ('front', x1 - 2.6, x1 - 1.2, 0.9, 2.05)]
    dx = x0 + w * 0.5
    return dict(x0=x0, x1=x1, yf=yf, depth=9.0, face=fc, floor=0.0, eave=2.6, ridge=4.8, siding=sid, roof=roof, trim='#e8e8e4',
                door=(dx - 0.45, dx + 0.45, 2.05, '#3a3a44' if i % 2 else '#5a2a2a', None), wins=wins, chimney=(x0 + 1.6, yf + 4.5 * fc, 0.6),
                porch=(dx - 1.2, dx + 1.2, 1.3), steps=(dx - 0.5, dx + 0.5, 0.8), plight=pl, snow=1.0, frost=0.6, icicles=i < 4)


# ====================================================================================================== street furniture
def ic_fence(pen, v, x0=None, x1=None, y=IC_FENCE_Y, gate=IC_GATE, buried=True):
    """The white picket fence along our front yard, half buried: pickets 1.0 m, the top 0.6 m out of the snow."""
    x0 = IC_FENCE_X[0] if x0 is None else x0; x1 = IC_FENCE_X[1] if x1 is None else x1
    base = IC_SNOWY - 0.02 if buried else IC_G
    top = IC_G + 1.0
    for (a, b) in ((x0, gate[0]), (gate[1], x1)):
        if b <= a: continue
        for Yr in (IC_G + 0.75, IC_G + 0.45):
            if Yr < base: continue
            A, B_ = (a, Yr, y), (b, Yr, y)
            if v.d(a, y) > 0.3 and v.d(b, y) > 0.3:
                pen.seg(v.p(*A), v.p(*B_), max(1.0, 0.06 * v.s((a + b) / 2, y)), lit('#e8ecf0', A, (0, 0, -1)))
        n = int((b - a) / 0.16)
        for k in range(n + 1):
            xx = a + k * (b - a) / max(1, n)
            if v.d(xx, y) < 0.3: continue
            s = v.s(xx, y); w = max(0.8, 0.045 * s)
            bx, by = v.p(xx, base, y); tx, ty = v.p(xx, top, y)
            pk = poly([(bx - w, by), (bx + w, by), (tx + w, ty + w * 1.2), (tx, ty), (tx - w, ty + w * 1.2)])
            pen.fill(pk, lit('#eef2f6', (xx, top, y), (0, 0, -1))); pen.line(pk, 0.7)
            pen.fill(oval(tx, ty + w * 0.9, w * 1.05, w * 0.45), '#ffffff', 170)          # a little snow on each picket
        for xx in (a, b):
            if v.d(xx, y) < 0.3: continue
            draw_box(pen, v, Box(xx, y, 0.1, 0.1, base, top + 0.08, 0), {'all': '#eef2f6', 'top': '#ffffff'}, lw=0.8)


def ic_lamp(pen, v, x, y, k=1.0):
    dr_streetlight(pen, v, x, y, k, IC_STREET_C, arm=1.0, G=IC_G)


def ic_lamp_glow(pen, v, x, y, k=1.0, t=0.0):
    dr_streetlight_glow(pen, v, x, y, k, IC_STREET_C, arm=1.0, G=IC_G, rain=False, t=t)


def ic_car(cx=None, cy=None, fa=None, col='#7a2a2a', era='now', snow=True):
    """Dad's car (a dark red sedan under a snow cap) / a 1958 car (era '1958': rounder, two-tone) as Parts."""
    cx = IC_CAR[0] if cx is None else cx; cy = IC_CAR[1] if cy is None else cy; fa = IC_CAR[2] if fa is None else fa
    P = list(dr_car_parts(cx, cy, fa, col, lights=False, Y0=IC_G, interior=False, plate="" if era == "1958" else "LKF 214")[0])
    if snow:
        def cap(pen, v):
            B = Box(cx, cy, 1.25, 1.6, IC_G + 1.42, IC_G + 1.52, fa)
            draw_box(pen, v, B, {'all': '#e8eef8', 'top': '#f4f8ff'}, lw=0.6)
            Bh = Box(cx + math.sin(math.radians(fa)) * 1.55, cy - math.cos(math.radians(fa)) * 1.55, 1.5, 1.0, IC_G + 0.98, IC_G + 1.04, fa)
            draw_box(pen, v, Bh, {'all': '#e8eef8', 'top': '#f4f8ff'}, lw=0.5)
        P.append(Part(fn=cap, ref=(cx, IC_G + 1.5, cy), tag='snow'))
    return P


# ====================================================================================================== HIS TRUCK
def ic_truck_frame(cx, cy, fa, G=IC_G):
    """(body Box (the serving box behind the cab), cab Box, Lb). Box 'left' face = the serving (curb) side."""
    L, Lc, W = IC_TRUCK_L, IC_TRUCK_LC, IC_TRUCK_W
    Lb = L - Lc
    th = math.radians(fa); N = (math.sin(th), -math.cos(th))
    bc = (cx - N[0] * (L / 2 - Lb / 2), cy - N[1] * (L / 2 - Lb / 2))
    cc = (cx + N[0] * (L / 2 - Lc / 2), cy + N[1] * (L / 2 - Lc / 2))
    body = Box(bc[0], bc[1], W, Lb, G + IC_TRUCK_Y0, G + IC_TRUCK_Y1, fa)
    cab = Box(cc[0], cc[1], W - 0.08, Lc, G + IC_TRUCK_Y0, G + IC_TRUCK_Y1 - 0.12, fa)
    return body, cab, Lb


def _stripes(p_, W, H, w=34.0, c=IC_STRIPE, c2='#fbf6f8', grime=0.2):
    p_.fill(rect(0, 0, W, H), c2)
    k = 0
    x = 0.0
    while x < W:
        if k % 2 == 0: p_.fill(rect(x, 0, w, H), c)
        x += w; k += 1
    p_.linear(rect(0, 0, W, H), 0, 0, 0, H, [(0, '#ffffff', 40), (0.6, '#ffffff', 0), (1, '#3a2a40', 70)])
    p_.texture(rect(0, 0, W, H), 'grunge', grime, 'overlay', 1.2)


def _flake_path(cx, cy, r, arms=6, rot=0.0, fat=0.12):
    """A six-armed snowflake (cm frame path): arms with two pairs of side branches."""
    path = skia.Path()
    for i in range(arms):
        a = math.radians(rot + i * 360.0 / arms)
        ca, sa = math.cos(a), math.sin(a)
        def P(u, w): return (cx + ca * u - sa * w, cy + sa * u + ca * w)
        w = r * fat * 0.5
        arm = poly([P(0, -w), P(r * 0.92, -w * 0.7), P(r, 0), P(r * 0.92, w * 0.7), P(0, w)])
        path = union(path, arm)
        for (f, bl) in ((0.42, 0.34), (0.7, 0.24)):
            for sd in (-1, 1):
                b0 = P(r * f, 0)
                b1 = P(r * f + r * bl * 0.7, sd * r * bl * 0.7)
                br = poly([P(r * f - w * 0.8, 0), (b1[0] - sa * w * 0.0, b1[1]), P(r * f + w * 0.8, 0)])
                path = union(path, stroke_path(poly([b0, b1], False), w * 1.3))
    path = union(path, oval(cx, cy, r * 0.2))
    return path


def stroke_path(path, w):
    p = skia.Paint(Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)
    out = skia.Path()
    p.getFillPath(path, out)
    return out


def _truck_side_art(serving=True, Lb=4.25, era='now'):
    """The body's side (cm frame; x 0 = the rear end, x W = the cab end on the 'left' face): stripes, the looping
    MISTER SHIVER'S sign with Sweet Treats All Year!, snowflake decals, the serving window frame (its glow is live)."""
    def art(p_, W, H):
        _stripes(p_, W, H)
        p_.fill(rect(0, H - 30, W, 30), '#d8d4d8'); p_.fill(rect(0, H - 32, W, 3), '#9a9aa4')                 # chrome rocker
        p_.fill(rect(0, 66, W, 5), '#c8c8d0'); p_.fill(rect(0, 66, W, 2), '#ffffff', 200)
        bx = W * 0.5
        if serving:
            n0, n1, Y0, Y1 = IC_SWIN
            xa = (Lb / 2 + n0) * 100; xb = (Lb / 2 + n1) * 100
            ya = (IC_TRUCK_Y1 - Y1) * 100; yb = (IC_TRUCK_Y1 - Y0) * 100
            p_.fill(rrect(xa - 14, ya - 12, xb - xa + 28, yb - ya + 30, 12), '#f4f0f2'); p_.line(rrect(xa - 14, ya - 12, xb - xa + 28, yb - ya + 30, 12), 1.6, '#8a7a84')
            p_.fill(rrect(xa, ya, xb - xa, yb - ya, 8), '#3a1a2a')
            p_.fill(rect(xa - 24, yb + 2, xb - xa + 48, 9), '#d8d4dc'); p_.line(rect(xa - 24, yb + 2, xb - xa + 48, 9), 1.0)   # the counter shelf
            for k_, fx in enumerate((xa - 60, xb + 60)):
                p_.fill(_flake_path(fx, (ya + yb) / 2, 26 - 6 * k_), '#ffffff', 235); p_.line(_flake_path(fx, (ya + yb) / 2, 26 - 6 * k_), 0.8, '#9ab0d0', 200)
        else:
            for (fx, fy, fr) in ((W * 0.25, H * 0.55, 30), (W * 0.75, H * 0.6, 24), (W * 0.5, H * 0.66, 18)):
                p_.fill(_flake_path(fx, fy, fr), '#ffffff', 235); p_.line(_flake_path(fx, fy, fr), 0.8, '#9ab0d0', 200)
        # the sign (looping script) on a cream banner across the top of the side
        bw = 300
        p_.fill(rrect(bx - bw / 2 - 8, 8, bw + 16, 54, 20), '#fff6f0'); p_.line(rrect(bx - bw / 2 - 8, 8, bw + 16, 54, 20), 2.0, '#b85a86')
        btext(p_, "Mister Shiver's", bx, 42, 'script', 31, '#c23a78', 250, 'center')
        btext(p_, 'Sweet Treats All Year!', bx, 57, 'cursive_b', 11, '#7a3a62', 240, 'center')
        # wheel arches
        for f in (0.2,):
            x = W * f
            p_.fill(oval(x, H + 8, 58, 56), '#141418')
        p_.texture(rect(0, 0, W, H), 'grunge', 0.15, 'multiply', 2.0)
        p_.fill(rect(0, 0, W, 10), '#ffffff', 220)                                                       # frost along the roofline
    return art


def _truck_cab_art(face, Lc=1.75):
    def art(p_, W, H):
        if face == 'front':
            p_.fill(rect(0, 0, W, H), '#fbf6f8')
            p_.fill(rect(0, H * 0.55, W, H * 0.45), IC_STRIPE)
            for k in range(5): p_.fill(rect(W * (0.1 + 0.2 * k) - 10, H * 0.55, 20, H * 0.45), '#fbf6f8')
            r = rrect(16, 26, W - 32, H * 0.36, 36)                                                     # the big curved windshield
            p_.fill(r, '#141a2a'); p_.line(r, 3.0, '#c8c8d0')
            p_.linear(r, 0, 26, W, 26 + H * 0.36, [(0, '#ffffff', 0), (0.45, '#c8d8ff', 60), (0.55, '#ffffff', 0)])
            p_.fill(rect(W / 2 - 3, 26, 6, H * 0.36), '#c8c8d0')
            for x in (W * 0.16, W * 0.84):                                                               # round headlights
                p_.fill(oval(x, H * 0.66, 17), '#c8c8d0'); p_.fill(oval(x, H * 0.66, 12), '#e8ecf4'); p_.line(oval(x, H * 0.66, 17), 1.2)
            g = rrect(W * 0.32, H * 0.6, W * 0.36, H * 0.22, 14)
            p_.fill(g, '#d8d8e0'); p_.line(g, 1.4)
            for k in range(6): p_.fill(rect(W * 0.34, H * 0.62 + k * H * 0.033, W * 0.32, 2.5), '#6a6a74')
            p_.fill(_flake_path(W / 2, H * 0.5, 14), '#ffffff', 240)
            p_.fill(rect(0, H - 28, W, 28), '#d8d8e0'); p_.line(rect(0, H - 28, W, 28), 1.0)
        else:
            _stripes(p_, W, H)
            p_.fill(rect(0, H - 30, W, 30), '#d8d4d8')
            wx0, wx1 = (20, W - 70) if face == 'left' else (70, W - 20)
            r = rrect(wx0, 34, wx1 - wx0, 62, 22)
            p_.fill(r, '#141a2a'); p_.line(r, 3.0, '#c8c8d0')
            p_.fill(rect(wx0 + (wx1 - wx0) * 0.55, 120, 3, H - 160), '#8a7a84', 160)                      # the door seam
            x = (W * 0.55) if face == 'left' else (W * 0.45)
            p_.fill(oval(x, H + 8, 56, 54), '#141418')
            p_.fill(rect(0, 0, W, 10), '#ffffff', 220)
    return art


def ic_truck_parts(cx, cy, fa, G=IC_G, era='now', window_open=0.0):
    """HIS TRUCK as Parts: the rounded striped body (serving side = Box 'left' face), the lower rounded cab with its big
    curved windshield, chrome bumpers, four wheels, the frosted SNOWFLAKE on the roof with the chrome speaker horn at
    its centre, the roof snow. No licence plate. The serving window's glow, frost and mitten bunting are live
    (ic_truck_emit)."""
    body, cab, Lb = ic_truck_frame(cx, cy, fa, G)
    def rshape(W, H, r): return rrect(0, 0, W, H + r, r)
    def body_fn(pen, v):
        fs = body.faces()
        order = sorted(fs.items(), key=lambda kv: -v.d(kv[1].centre()[0], kv[1].centre()[2]))
        for nm, F in order:
            if nm in ('bottom', 'front'): continue
            if nm == 'left': draw_face(pen, v, F, _truck_side_art(True, Lb, era), IC_STRIPE, lw=1.3, shape=rshape(F.W, F.H, 30))
            elif nm == 'right': draw_face(pen, v, F, _truck_side_art(False, Lb, era), IC_STRIPE, lw=1.3, shape=rshape(F.W, F.H, 30))
            elif nm == 'back':
                def back(p_, W, H):
                    _stripes(p_, W, H)
                    for a in (24, W - 84):
                        p_.fill(rrect(a, 40, 60, 70, 10), '#141a2a'); p_.line(rrect(a, 40, 60, 70, 10), 2.4, '#c8c8d0')
                    p_.fill(rrect(W / 2 - 60, H - 120, 120, 40, 10), '#fff6f0'); btext(p_, 'Stop for a treat!', W / 2, H - 94, 'cursive_b', 13, '#c23a78', 240, 'center')
                    for x in (W * 0.1, W * 0.9): p_.fill(rrect(x - 10, H - 80, 20, 26, 5), '#6a1a1a'); p_.line(rrect(x - 10, H - 80, 20, 26, 5), 1.0)
                    p_.fill(rect(0, H - 30, W, 30), '#d8d8e0')
                    p_.fill(rect(0, 0, W, 10), '#ffffff', 220)
                draw_face(pen, v, F, back, IC_STRIPE, lw=1.3, shape=rrect(0, 0, F.W, F.H + 60, 60))
            elif nm == 'top':
                draw_face(pen, v, F, lambda p_, W, H: (p_.fill(rect(0, 0, W, H), '#f4f8ff'), p_.texture(rect(0, 0, W, H), 'grunge', 0.3, 'overlay', 2.0)),
                          '#f4f8ff', lw=1.0)
        # the rounded crown (a soft step along the roof edges)
        cr = Box(body.cx, body.cy, body.w - 0.4, body.d - 0.3, body.Y1, body.Y1 + 0.1, body.fa)
        draw_box(pen, v, cr, {'all': '#e8eef8', 'top': '#ffffff'}, lw=0.7, skip=('bottom',))
    P = [Part(fn=body_fn, ref=(body.cx, G + 1.5, body.cy), tag='body')]
    def cab_fn(pen, v):
        fs = cab.faces()
        order = sorted(fs.items(), key=lambda kv: -v.d(kv[1].centre()[0], kv[1].centre()[2]))
        for nm, F in order:
            if nm in ('bottom', 'back'): continue
            if nm == 'front': draw_face(pen, v, F, _truck_cab_art('front'), '#fbf6f8', lw=1.3, shape=rrect(0, 0, F.W, F.H + 70, 70))
            elif nm in ('left', 'right'):
                draw_face(pen, v, F, _truck_cab_art(nm), IC_STRIPE, lw=1.3, shape=poly([(0, 60), (40, 0), (F.W, 0), (F.W, F.H), (0, F.H)]) if nm == 'right' else
                          poly([(0, 0), (F.W - 40, 0), (F.W, 60), (F.W, F.H), (0, F.H)]))
            elif nm == 'top':
                draw_face(pen, v, F, lambda p_, W, H: p_.fill(rect(0, 0, W, H), '#f4f8ff'), '#f4f8ff', lw=1.0)
    P.append(Part(fn=cab_fn, ref=(cab.cx, G + 1.4, cab.cy), tag='cab'))
    th = math.radians(fa); N = (math.sin(th), -math.cos(th))
    L = IC_TRUCK_L
    for (sgn, w) in ((1, 2.3), (-1, 2.32)):
        bb = Box(cx + N[0] * sgn * (L / 2 + 0.07), cy + N[1] * sgn * (L / 2 + 0.07), w, 0.14, G + 0.36, G + 0.62, fa)
        P.append(Part(bb, {'all': '#d8dae2', 'top': '#ffffff'}, tag='bumper'))
    for n in (Lb / 2 - 0.85 + 0.0, -Lb / 2 + 0.85):
        for sd in (-1, 1):
            P.append(_wheel_part(body, n, sd, G, r=0.46))
    for sd in (-1, 1):
        P.append(_wheel_part(cab, 0.05, sd, G, r=0.46))
    # the roof snowflake: a frosted plastic flake standing along the roof, the chrome horn at its centre
    def flake_fn(pen, v):
        r = 0.66; base = body.Y1 + 0.12; cyY = base + r + 0.06; n_c = -0.1
        for side in (-1, 1):                                                  # far face first
            pass
        sides = sorted((-1, 1), key=lambda s_: -v.d(*[body.at(s_ * 0.05, n_c, 0)[i] for i in (0, 2)]))
        for k, s_ in enumerate(sides):
            u = s_ * 0.05
            pts = []
            fp = _flake_path(0, 0, r * 100)
            # sample the cm path into 3D: x along n (toward the front), y up
            it = skia.Path.Iter(fp, True)
            def map_(x, y): return body.at(u, n_c + x / 100.0, cyY - y / 100.0)
            # flatten: walk the path's points via its polygon approximation
            seg = []
            meas = skia.PathMeasure(fp, True)
            contours = []
            while True:
                Lm = meas.getLength()
                if Lm <= 0: break
                m = max(8, int(Lm / 3.0))
                cont = []
                for i in range(m):
                    pos, tan = meas.getPosTan(Lm * i / m)
                    cont.append(map_(pos.x(), pos.y()))
                contours.append(cont)
                if not meas.nextContour(): break
            nrm = (body.U[0] * s_, 0.0, body.U[1] * s_)
            facing = v.visible(body.at(u, n_c, cyY), nrm)
            c = IC_FLAKE if facing else '#b8c8da'
            for cont in contours:
                q = v.poly3(cont)
                if q.isEmpty(): continue
                pen.fill(q, lit(c, body.at(u, n_c, cyY), nrm), 245)
                pen.line(q, 1.0, '#6a7a9a', 220)
            if k == 1:                                                         # the near face: frost sparkle + the horn
                x, y = v.p(*body.at(u, n_c, cyY)); s = v.s(*[body.at(u, n_c, cyY)[i] for i in (0, 2)])
                pen.glow(x, y - 0.1 * s, 0.6 * s, '#ffffff', 40)
        # the post and the chrome horn
        A = body.at(0, n_c, body.Y1 + 0.1); B_ = body.at(0, n_c, cyY - r)
        if v.d(A[0], A[2]) > 0.3:
            pen.seg(v.p(*A), v.p(*B_), max(1.0, 0.06 * v.s(A[0], A[2])), '#c8ccd4')
        hc = body.at(0, n_c, cyY)
        hs = v.s(hc[0], hc[2])
        if v.d(hc[0], hc[2]) > 0.3:
            x, y = v.p(*hc)
            bell = body.at(0.0, n_c, cyY)
            # the horn's bell opens toward the serving side (toward the houses)
            mouth = body.at(-0.32, n_c, cyY)
            mx, my = v.p(*mouth)
            pen.fill(poly([(x - 0.05 * hs, y - 0.04 * hs), (x + 0.05 * hs, y - 0.04 * hs), (mx + 0.1 * hs, my + 0.12 * hs), (mx - 0.1 * hs, my - 0.12 * hs)]), '#d8dce4')
            pen.fill(oval(mx, my, 0.1 * hs, 0.13 * hs), '#5a5e68'); pen.line(oval(mx, my, 0.1 * hs, 0.13 * hs), 1.0, '#e8ecf4')
            pen.fill(oval(x, y, 0.06 * hs), '#e8ecf4'); pen.line(oval(x, y, 0.06 * hs), 0.8)
    P.append(Part(fn=flake_fn, ref=body.at(0, -0.1, body.Y1 + 0.8), tag='flake'))
    # the serving-side wall again as its own part with the window cut through, so a figure standing inside at the
    # window (anchor truck_vendor) sorts BEHIND the wall and shows only through the window
    def side_fn(pen, v):
        F = body.faces()['left']
        n0, n1, Y0, Y1 = IC_SWIN
        xa = (Lb / 2 + n0) * 100; xb = (Lb / 2 + n1) * 100; ya = (IC_TRUCK_Y1 - Y1) * 100; yb = (IC_TRUCK_Y1 - Y0) * 100
        draw_face(pen, v, F, _truck_side_art(True, Lb, era), IC_STRIPE, holes=[rrect(xa, ya, xb - xa, yb - ya, 8)], lw=1.3, shape=rshape(F.W, F.H, 30))
    P.append(Part(fn=side_fn, ref=body.at(-body.w / 2, 0.0, G + 1.5), tag='side_front'))
    return P


def ic_truck_window_quad(cx, cy, fa, G=IC_G, inset=0.0):
    """3D corners of the serving window opening on the curb side (rear-top, front-top, front-bottom, rear-bottom)."""
    body, cab, Lb = ic_truck_frame(cx, cy, fa, G)
    n0, n1, Y0, Y1 = IC_SWIN
    u = -(body.w / 2 + 0.006 - inset)
    return [body.at(u, n0, G + Y1), body.at(u, n1, G + Y1), body.at(u, n1, G + Y0), body.at(u, n0, G + Y0)]


def ic_truck_emit(pen, v, cx, cy, fa, G=IC_G, win=1.0, open_=0.0, mittens=None, lina=False, heads=0.0, t=0.0, spill=True):
    """The truck's live light: the warm PINK serving window (the lure), frost round its edges, the mitten bunting strung
    across the inside like party flags (the oldest, small and RED, at the left end seen from outside; Lina's added at the
    right end when lina=True), the pink spill on the snow below; open_ 0..1 slides the glass aside; heads = headlights."""
    body, cab, Lb = ic_truck_frame(cx, cy, fa, G)
    q = ic_truck_window_quad(cx, cy, fa, G)
    nrm = (-body.U[0], 0.0, -body.U[1])
    th = math.radians(fa); N = (math.sin(th), -math.cos(th))
    if win > 0.01 and spill:                                                  # the spill on the snow (and the street)
        P = body.at(-(body.w / 2 + 1.6), (IC_SWIN[0] + IC_SWIN[1]) / 2, IC_G)
        if v.d(P[0], P[2]) > 0.4:
            path = ellipse3(v, P[0], P[2], 2.6 if abs(body.U[0]) > 0.5 else 2.2, 1.6, IC_SNOWY + 0.01)
            b = path.computeTightBounds()
            pen.radial(path, (b.left() + b.right()) / 2, (b.top() + b.bottom()) / 2, max(b.width(), b.height()) * 0.55,
                       [(0, IC_PINK, 70 * win), (1, IC_PINK, 0)], sy=b.height() / max(1.0, b.width()))
    if not v.visible(q[0], nrm) or v.d((q[0][0] + q[1][0]) / 2, (q[0][2] + q[1][2]) / 2) < 0.3:
        pass
    else:
        path = v.poly3(q)
        if not path.isEmpty() and win > 0.01:
            b = path.computeTightBounds()
            pen.linear(path, 0, b.top(), 0, b.bottom(), [(0, '#ffe0ee', 245 * win), (0.5, IC_PINK, 240 * win), (1, '#e0609a', 235 * win)])
            pen.cv.save(); pen.cv.clipPath(path, skia.ClipOp.kIntersect, True)
            # the inside, barely: a pale counter-back and a soft dark band low (never more than the window frame)
            pen.linear(rect(b.left(), b.top() + b.height() * 0.72, b.width(), b.height() * 0.28), 0, b.top() + b.height() * 0.72, 0, b.bottom(),
                       [(0, '#a8406a', 0), (1, '#7a2a4a', 130 * win)])
            # the mitten bunting: a sagging string near the top with single mittens hanging
            ms = list(IC_MITTENS if mittens is None else mittens)
            if lina: ms = ms + [IC_LINA_MITTEN]
            def W3(f, h):
                A = (q[0][0] + (q[1][0] - q[0][0]) * f, q[0][1] - h, q[0][2] + (q[1][2] - q[0][2]) * f)
                return v.p(A[0] - nrm[0] * 0.05, A[1], A[2] - nrm[2] * 0.05)
            hH = q[0][1] - q[3][1]
            pts = [W3(f, hH * (0.12 + 0.1 * math.sin(math.pi * f))) for f in np.linspace(0.02, 0.98, 24)]
            pen.line(smooth(pts, False), max(1.0, 0.012 * v.s(*[q[0][i] for i in (0, 2)])), '#f8f0e8', 230)
            nM = len(ms)
            for i, c in enumerate(ms):
                f = 0.07 + 0.86 * (i + 0.5) / max(nM, 1)
                x, y = W3(f, hH * (0.12 + 0.1 * math.sin(math.pi * f)))
                s = v.s(*[q[0][i_] for i_ in (0, 2)])
                sw = 0.008 * math.sin(t * 1.3 + i)
                sc = (0.11 if i == 0 else 0.15) * s                               # the red one is the smallest
                pen.cv.save(); pen.cv.translate(x, y); pen.cv.rotate(math.degrees(sw) * 8)
                m = union(rrect(-sc * 0.38, sc * 0.12, sc * 0.76, sc * 0.9, sc * 0.36), oval(sc * 0.36, sc * 0.5, sc * 0.18, sc * 0.26))
                pen.fill(m, c); pen.line(m, max(0.6, sc * 0.04), '#1a1012', 200)
                pen.fill(rect(-sc * 0.4, sc * 0.84, sc * 0.8, sc * 0.2), mix(c, '#ffffff', 0.4))
                pen.fill(rect(-sc * 0.04, 0, sc * 0.08, sc * 0.14), '#f0e8e0')                         # the clothes peg
                pen.cv.restore()
            # the glass (slides toward the front as it opens) with frost round its edges
            if open_ < 0.99:
                gf0 = open_ * 0.9
                gq = [W3(gf0, 0)]
            pen.cv.restore()
            # frost fringe round the frame (always: the cold outside)
            pen.cv.save(); pen.cv.clipPath(path, skia.ClipOp.kIntersect, True)
            pen.line(path, max(3.0, 0.08 * v.s(*[q[0][i] for i in (0, 2)])), '#ffffff', 150, blur=3)
            if open_ < 0.99:
                pen.fill(path, '#ffffff', 30 * (1 - open_))
                pen.linear(path, b.left(), b.top(), b.right(), b.bottom(), [(0, '#ffffff', 0), (0.48, '#ffffff', 50 * (1 - open_)), (0.52, '#ffffff', 0)])
            pen.cv.restore()
            pen.line(path, 1.6, '#4a2a3a')
            cx_, cy_ = (b.left() + b.right()) / 2, (b.top() + b.bottom()) / 2
            pen.glow(cx_, cy_, b.width() * 1.5, IC_PINK, 70 * win)
    if heads > 0.01:
        for sd in (-1, 1):
            Pp = cab.at(sd * cab.w * 0.34, cab.d / 2 + 0.02, G + 1.02)
            if v.d(Pp[0], Pp[2]) < 0.3 or not v.visible(Pp, (N[0], 0.0, N[1])): continue
            x, y = v.p(*Pp); s = v.s(Pp[0], Pp[2])
            pen.glow(x, y, 0.8 * s, '#fff2e0', 150 * heads); pen.glow(x, y, 0.16 * s, '#ffffff', 240 * heads)


def ic_truck_piece(name, pos, G=IC_G, era='now'):
    cx, cy, fa = pos
    parts = ic_truck_parts(cx, cy, fa, G, era)
    body, cab, Lb = ic_truck_frame(cx, cy, fa, G)
    foot = [(body.at(u, n, 0)[0], body.at(u, n, 0)[2]) for (u, n) in ((-1.15, -Lb / 2 - 0.1), (1.15, -Lb / 2 - 0.1), (1.15, Lb / 2 + IC_TRUCK_LC + 0.1), (-1.15, Lb / 2 + IC_TRUCK_LC + 0.1))]
    vend = body.at(-(body.w / 2 - 0.45), (IC_SWIN[0] + IC_SWIN[1]) / 2, 0)
    return Piece(name, (cx, G + 1.5, cy), lambda pen, v, ps=parts: draw_parts(pen, v, ps), occupant=[(vend[0], vend[2])], front=parts, block=foot)


def ic_truck_spots(v, pre, pos, G=IC_G):
    """Spots on his truck: <pre>vendor (him inside at the serving window, his feet on the truck floor, facing out),
    <pre>window (the window sill centre: a point), <pre>curb (a child at the window outside, facing it, in the snow),
    <pre>reach (a child's raised hand meets his glove here), <pre>roof (on the roof beside the flake: the legs plant
    here), <pre>roof_front / <pre>roof_back, <pre>flake (the snowflake / horn: the chime's source), <pre>window_top."""
    cx, cy, fa = pos
    body, cab, Lb = ic_truck_frame(cx, cy, fa, G)
    U, N = body.U, body.N
    n0, n1, Y0, Y1 = IC_SWIN; nm = (n0 + n1) / 2
    def plan(u, n): p_ = body.at(u, n, 0); return p_[0], p_[2]
    S = {}
    x, y = plan(-(body.w / 2 - 0.45), nm); S[pre + 'vendor'] = _mk_spot(v, pre + 'vendor', x, y, G + IC_TRUCK_FLOOR, 'stand', 'him inside at the serving window, facing out (his feet on the truck floor)', face=(-U[0], -U[1]))
    x, y = plan(-(body.w / 2 + 0.02), nm); S[pre + 'window'] = _mk_spot(v, pre + 'window', x, y, G + Y0, 'point', 'the serving window sill (centre)')
    S[pre + 'window_top'] = _mk_spot(v, pre + 'window_top', x, y, G + Y1, 'point', 'the top of the serving window')
    x, y = plan(-(body.w / 2 + 0.55), nm); S[pre + 'curb'] = _mk_spot(v, pre + 'curb', x, y, IC_G + 0.02, 'stand', 'a child at the window outside (on the plowed street), facing it', face=(U[0], U[1]))
    x, y = plan(-(body.w / 2 + 0.3), nm); S[pre + 'reach'] = _mk_spot(v, pre + 'reach', x, y, G + 1.25, 'point', 'where a raised hand meets his lowered glove')
    x, y = plan(-0.35, -0.1); S[pre + 'roof'] = _mk_spot(v, pre + 'roof', x, y, body.Y1, 'stand', 'on the roof beside the snowflake (curb half)', face=(-U[0], -U[1]))
    x, y = plan(0.0, Lb / 2 - 0.4); S[pre + 'roof_front'] = _mk_spot(v, pre + 'roof_front', x, y, body.Y1, 'stand', 'the front of the roof', face=(N[0], N[1]))
    x, y = plan(0.0, -Lb / 2 + 0.4); S[pre + 'roof_back'] = _mk_spot(v, pre + 'roof_back', x, y, body.Y1, 'stand', 'the back of the roof', face=(-N[0], -N[1]))
    x, y = plan(0.0, -0.1); S[pre + 'flake'] = _mk_spot(v, pre + 'flake', x, y, body.Y1 + 0.84, 'point', 'the snowflake and its chrome horn (where the chime comes from)')
    x, y = plan(-(body.w / 2 + 1.2), nm - 2.6); S[pre + 'behind'] = _mk_spot(v, pre + 'behind', x, y, IC_G + 0.02, 'stand', 'the street behind the truck: perfect snow, no tracks')
    return S


# ====================================================================================================== Dad's plow
def ic_plow_parts(cx, cy, fa, G=IC_G):
    """Dad's town snowplow: an orange cab-over truck with the salt hopper, the angled black blade with its yellow edge,
    six big wheels, the amber beacon on the cab roof (its sweep is live: ic_plow_emit)."""
    th = math.radians(fa); N = (math.sin(th), -math.cos(th)); Ux = (math.cos(th), math.sin(th))
    def C(n, u=0.0): return (cx + N[0] * n + Ux[0] * u, cy + N[1] * n + Ux[1] * u)
    org, dark = '#e8761a', '#2a2a2e'
    cab = Box(*C(2.0), 2.4, 2.0, G + 1.05, G + 3.0, fa)
    hop = Box(*C(-1.3), 2.5, 4.2, G + 1.15, G + 2.85, fa)
    frame = Box(*C(0.2), 2.2, 7.2, G + 0.75, G + 1.15, fa)
    def cab_art(face):
        def art(p_, W, H):
            p_.fill(rect(0, 0, W, H), org); p_.texture(rect(0, 0, W, H), 'grunge', 0.4, 'overlay', 1.4)
            if face == 'front':
                r = rrect(12, 14, W - 24, H * 0.42, 8); p_.fill(r, '#141a24'); p_.line(r, 2.5, '#1a1a1a')
                for x in (W * 0.15, W * 0.85): p_.fill(rrect(x - 16, H * 0.62, 32, 18, 4), '#f4eed8'); p_.line(rrect(x - 16, H * 0.62, 32, 18, 4), 1.0)
                p_.fill(rect(W * 0.3, H * 0.6, W * 0.4, H * 0.3), '#1a1a1a')
                btext(p_, 'LARKFIELD', W / 2, H * 0.97, 'head', 14, '#1a1a1a', 220, 'center')
            else:
                r = rrect(16, 14, W * 0.6, H * 0.42, 6); p_.fill(r, '#141a24'); p_.line(r, 2.5, '#1a1a1a')
                btext(p_, 'TOWN OF LARKFIELD', W * 0.5, H * 0.78, 'head', 11, '#1a1a1a', 220, 'center')
            for k in range(6): p_.fill(rect(0 if k % 2 else W - 0, 0, 0, 0), '#000000')
            p_.fill(rect(0, H - 14, W, 14), '#ffd23a'); [p_.fill(rect(k * 30, H - 14, 15, 14), '#1a1a1a') for k in range(int(W / 30) + 1)]
        return art
    P = [Part(frame, {'all': dark}, tag='frame'),
         Part(cab, {'front': dict(fill=org, art=cab_art('front')), 'left': dict(fill=org, art=cab_art('side')), 'right': dict(fill=org, art=cab_art('side')),
                    'all': org, 'top': '#f0f4ff'}, tag='cab'),
         Part(hop, {'all': dict(fill='#d06a18', art=lambda p_, W, H: (p_.texture(rect(0, 0, W, H), 'grunge', 0.5, 'overlay', 1.5),
                                                               [p_.fill(rect(k * 50, 0, 4, H), '#000000', 60) for k in range(int(W / 50) + 1)])), 'top': '#eef2fa'}, tag='hopper')]
    # the blade: angled across the front
    bc = C(3.55)
    blade = Box(bc[0], bc[1], 3.4, 0.22, G + 0.05, G + 1.25, fa + 22)
    P.append(Part(blade, {'front': dict(fill='#2a2a30', art=lambda p_, W, H: (p_.linear(rect(0, 0, W, H), 0, 0, 0, H, [(0, '#4a4a54'), (0.6, '#24242a'), (1, '#141418')]),
                                                                           p_.fill(rect(0, H - 10, W, 10), '#ffd23a'),
                                                                           p_.fill(rect(0, 0, W, 6), '#f0f4ff', 200))), 'all': '#202026', 'top': '#f0f4ff'}, tag='blade'))
    sp = Box(*C(3.55), 3.6, 0.6, G + 0.0, G + 0.5, fa + 22)
    P.append(Part(sp, {'all': '#e8eef8', 'top': '#ffffff'}, tag='spray'))
    body_ref = Box(*C(0.0), 2.3, 7.0, G, G + 1.0, fa)
    for n in (2.1, -0.9, -2.3):
        for sd in (-1, 1):
            P.append(_wheel_part(body_ref, n, sd, G, r=0.55))
    def beacon(pen, v):
        Pp = cab.at(0, 0.3, G + 3.12)
        if v.d(Pp[0], Pp[2]) < 0.3: return
        x, y = v.p(*Pp); s = v.s(Pp[0], Pp[2])
        pen.fill(rrect(x - 0.16 * s, y - 0.06 * s, 0.32 * s, 0.14 * s, 0.03 * s), '#1a1a1a')
        pen.fill(oval(x, y - 0.12 * s, 0.13 * s, 0.11 * s), '#d86a10'); pen.line(oval(x, y - 0.12 * s, 0.13 * s, 0.11 * s), 1.0)
    P.append(Part(fn=beacon, ref=cab.at(0, 0.3, G + 3.1), tag='beacon'))
    return P


def ic_plow_emit(pen, v, cx, cy, fa, t=0.0, beacon=1.0, heads=1.0, G=IC_G, rate=1.3):
    """Live: the amber beacon (rotating: a bright flare when it faces the camera, a beam swinging round), headlights."""
    th = math.radians(fa); N = (math.sin(th), -math.cos(th)); Ux = (math.cos(th), math.sin(th))
    cab_c = (cx + N[0] * 2.0, cy + N[1] * 2.0)
    Pp = (cab_c[0] + N[0] * 0.3, G + 3.2, cab_c[1] + N[1] * 0.3)
    if beacon > 0.01 and v.d(Pp[0], Pp[2]) > 0.3:
        x, y = v.p(*Pp); s = v.s(Pp[0], Pp[2])
        ang = t * rate * 2 * math.pi
        bx, by = math.sin(ang), math.cos(ang)
        tow = max(0.0, -(bx * v.fx + by * v.fy))                               # the beam pointing at the lens
        pen.glow(x, y, (0.6 + 2.2 * tow ** 4) * s, IC_ORANGE, (120 + 120 * tow ** 3) * beacon)
        pen.glow(x, y, 0.12 * s, '#fff0c0', 240 * beacon)
        # the beam: a long soft wedge
        side = max(0.0, bx * v.rx + by * v.ry) if False else abs(bx * v.rx + by * v.ry)
        pen.ellipse_glow(x, y, (0.6 + 1.6 * side) * s, 0.35 * s, IC_ORANGE, 60 * beacon * side)
    if heads > 0.01:
        for sd in (-1, 1):
            Hh = (cab_c[0] + N[0] * 1.02 + Ux[0] * sd * 0.85, G + 1.5, cab_c[1] + N[1] * 1.02 + Ux[1] * sd * 0.85)
            if v.d(Hh[0], Hh[2]) < 0.3 or not v.visible(Hh, (N[0], 0.0, N[1])): continue
            x, y = v.p(*Hh); s = v.s(Hh[0], Hh[2])
            pen.glow(x, y, 0.9 * s, '#fff4dc', 150 * heads); pen.glow(x, y, 0.15 * s, '#ffffff', 240 * heads)


# ====================================================================================================== sky, smoke, air
def ic_sky(pen, v, tod='night', box=(-900, -700, 2820, 1780)):
    """A clear, hard-cold sky: deep navy to a pale icy band at the horizon, stars, the bright moon with a frost halo
    (night / 1958); a pink-gold sunrise (morning)."""
    x0, y0, x1, y1 = box
    r = rect(x0, y0, x1 - x0, y1 - y0)
    H = v.h
    if tod in ('night', '1958'):
        pen.linear(r, 0, H - 1.1 * v.S, 0, H + 30, [(0, '#03050e'), (0.5, '#081028'), (0.82, '#122448'), (1, '#2e4a78')])
        rng = np.random.default_rng(21)
        for i in range(260):
            az = rng.uniform(-180, 180); el = rng.uniform(3, 70)
            q = sky_dir(v, az, el)
            if q is None or q[1] > H - 8: continue
            pen.fill(oval(q[0], q[1], rng.uniform(0.6, 1.8)), '#ffffff', int(rng.uniform(90, 255)))
        m = sky_dir(v, 200.0, 26.0)                                           # the moon: high over the south (Kessler's side)
        if m is None: m = sky_dir(v, 20.0, 30.0)
        if m is not None:
            mr = 0.028 * v.S
            pen.radial(None, m[0], m[1], mr * 14, [(0, '#dfe8ff', 70), (0.25, '#8aa8e8', 30), (1, '#2a3a6a', 0)], clip=False)
            pen.fill(oval(m[0], m[1], mr * 7.5), '#c8d8ff', 10)
            pen.line(oval(m[0], m[1], mr * 7.5), max(1.0, mr * 0.2), '#dfe8ff', 12, blur=mr * 0.5)
            pen.fill(oval(m[0], m[1], mr), '#f4f6ff')
            for (dx, dy, rr) in ((0.3, -0.2, 0.25), (-0.35, 0.15, 0.18), (0.05, 0.4, 0.14)):
                pen.fill(oval(m[0] + dx * mr, m[1] + dy * mr, rr * mr), '#c8d0e8', 160)
    elif tod == 'dawn':
        pen.linear(r, 0, H - 1.0 * v.S, 0, H + 20, [(0, '#1a2a58'), (0.6, '#6a6a98'), (0.9, '#e8a8a0'), (1, '#ffd0a8')])
    else:
        pen.linear(r, 0, H - 1.0 * v.S, 0, H + 20, [(0, '#5a7ab8'), (0.5, '#a8b8dc'), (0.85, '#f4c8b8'), (1, '#ffe2b8')])
        s_ = sky_dir(v, 100.0, 5.0)
        if s_: pen.radial(None, s_[0], s_[1], 1.4 * v.S, [(0, '#fff4d8', 230), (0.25, '#ffc890', 110), (1, '#ffa070', 0)], sy=0.5, clip=False)
        rng = np.random.default_rng(5)
        for i in range(8):
            q = sky_dir(v, rng.uniform(-180, 180), rng.uniform(6, 22))
            if q: _cloud(pen, q[0], q[1], rng.uniform(0.4, 0.8) * v.S, 0.05 * v.S, int(rng.integers(0, 999)), '#f8e8e0', '#ffffff', 140)


def ic_smoke(pen, v, x, Y, y, t, k=1.0, seed=0, tod='night'):
    """Chimney smoke: soft puffs rising and leaning with the light wind (live)."""
    if k <= 0.01 or v.d(x, y) < 0.6: return
    rng = np.random.default_rng(abs(int(seed)))
    day = tod not in ('night', '1958')
    c = '#aab4cc' if not day else ('#6c6462' if tod == 'morning' else '#8c8482')   # day smoke: a warm grey that reads on the pale sky (darker: film pass 2; morning darker still, verify pass)
    n = 9 if not day else 14
    for i in range(n):
        ph = (t * 0.22 + i / float(n) + rng.uniform(0, 0.05)) % 1.0
        P = (x + ph * 2.6 + 0.3 * math.sin(t * 0.7 + i), Y + 0.2 + ph * 3.2, y + ph * 0.8)
        if v.d(P[0], P[2]) < 0.5: continue
        px, py = v.p(*P); s = v.s(P[0], P[2])
        rr = (0.25 + ph * 0.9) * s * (1.35 if day else 1.0)
        al = (110 if not day else 225) * k * (1 - ph) ** 1.0
        pen.fill(oval(px, py, rr, rr * 0.8), c, al, blur=rr * 0.5)
        if day: pen.fill(oval(px - 0.15 * rr, py - 0.2 * rr, rr * 0.6, rr * 0.48), '#f4eee8', al * (0.3 if tod == 'morning' else 0.8), blur=rr * 0.4)


def ic_breath_air(pen, v, t, box=(0, 0, 1920, 1080), n=70, seed=3, k=1.0, c='#ffffff'):
    """Diamond dust: tiny ice crystals glinting in the air (live, screen space, drift down slowly)."""
    rng = np.random.default_rng(abs(int(seed)))
    x0, y0, x1, y1 = box
    for i in range(n):
        x = x0 + (rng.uniform(0, 1) * (x1 - x0) + 12 * math.sin(t * 0.4 + i)) % (x1 - x0)
        y = y0 + (rng.uniform(0, 1) * (y1 - y0) + t * rng.uniform(6, 18)) % (y1 - y0)
        tw = 0.5 + 0.5 * math.sin(t * rng.uniform(2, 6) + i)
        pen.fill(oval(x, y, rng.uniform(0.7, 1.6)), c, int(200 * tw * k))


def _house_win_quads(H, off=0.012):
    """{window name: 3D quad on the house's outside} from an ic_house dict (front windows + 'side:' windows)."""
    out = {}
    fc, yf = H['face'], H['yf']
    Fl = H.get('floor', 0.0)
    for (wn, wx0, wx1, sl, tp) in H.get('wins', []):
        if ':' in wn:
            side, nm = wn.split(':')
            xx = H['x0'] - off if side == 'west' else H['x1'] + off
            ys = sorted(((yf + wx0 * 0 + (wx0 - (H['x0'] if False else 0)) * 0) + 0, 0))
            y0, y1 = (yf + (wx0 - 0) * 0, 0)
            continue
        Yy = yf - off * fc
        out[wn] = [(wx0, Fl + tp, Yy), (wx1, Fl + tp, Yy), (wx1, Fl + sl, Yy), (wx0, Fl + sl, Yy)]
    return out


def _win_glow(pen, v, q, k, c0='#ffd090', c1='#e89a48', curtain=True, t=0.0):
    path = v.poly3(q)
    if path.isEmpty(): return
    bb = path.computeTightBounds()
    pen.linear(path, 0, bb.top(), 0, bb.bottom(), [(0, c0, 210 * k), (1, c1, 225 * k)])
    if curtain:                                                                # drawn curtains: dark folds at the sides
        for (f0, f1) in ((0.0, 0.22), (0.78, 1.0)):
            pen.fill(rect(bb.left() + bb.width() * f0, bb.top(), bb.width() * (f1 - f0), bb.height()), '#5a2a1a', 140 * k)
    pen.glow((bb.left() + bb.right()) / 2, (bb.top() + bb.bottom()) / 2, bb.width() * 1.1, c1, 45 * k)


# ====================================================================================================== Birch Lane
class IcStreet(Room):
    """Birch Lane as a room (night / morning / 1958 / the across-town house): the shell (sky, far ring, snow, banks,
    the far neighbours) is cached; our house, Kessler's house, the fence, Dad's car, the streetlight, HIS TRUCK and the
    plow are pieces at their real depth; window glows, porch lights, smoke, the pink window and the beacon are live."""
    name = 'street'
    poly = [(-140.0, -60.0), (140.0, -60.0), (140.0, 40.0), (-140.0, 40.0)]

    def __init__(self, o):
        self.o = o

    def _truck_pos(self, o):
        tr = o.get('truck')
        if tr in (None, False): return None
        if tr == 'A': return IC_TRUCK_A
        if tr == 'B': return IC_TRUCK_B
        return tuple(tr)

    def lights(self, o):
        tod = o.get('tod', 'night')
        night = tod in ('night', '1958')
        if night:
            amb = '#2e3c6a'
            steady = [Lamp(kind='dir', c=IC_MOON, k=0.62, d=_norm3((0.2, -0.75, 0.62)))]
        else:
            amb = '#5e6278'
            steady = [Lamp(kind='dir', c='#ffd8b0', k=0.72, d=_norm3((-0.55, -0.45, 0.7)))]
        var = []
        if night:
            var.append(('street', [Lamp(IC_LAMP[0], IC_G + 6.0, IC_LAMP[1] - 1.6, 13.0, IC_STREET_C, 1.6, (1.0, 0.6, 0.2), fall=1.35)],
                        _kfn(o.get('street', 1.0), 501)))
            var.append(('porch', [Lamp(IC_PLIGHT[0], IC_PLIGHT[1], IC_PLIGHT[2] - 0.4, 5.5, '#ffc888', 1.5, fall=1.5)], _kfn(o.get('porch', 0.0), 502)))
            var.append(('kporch', [Lamp(2.25, IC_KFLOOR + 1.95, IC_KH[3] + 0.4, 5.5, '#ffc888', 1.5, fall=1.5)], _kfn(o.get('kporch', 0.0), 503)))
            pos = self._truck_pos(o)
            if pos:
                body, cab, Lb = ic_truck_frame(*pos)
                P = body.at(-(body.w / 2 + 0.5), (IC_SWIN[0] + IC_SWIN[1]) / 2, IC_G + 1.9)
                var.append(('pink', [Lamp(P[0], P[1], P[2], 8.0, IC_PINK, 1.15, (1.0, 1.0, 0.7), fall=1.4)], _kfn(o.get('truck_win', 1.0), 504)))
            pl = o.get('plow')
            if pl:
                x = pl.get('x', 0.0)
                xs = x if not callable(x) else 0.0
                ly = pl.get('y', IC_PLOW_LANE[0])
                var.append(('beacon', [Lamp(xs, IC_G + 3.2, ly, 16.0, IC_ORANGE, 1.6, fall=1.2)], _kfn(pl.get('beacon', ic_pass(0.0, 1e6)), 505)))
            ps = o.get('porches')
            if ps is not None:
                for i in range(4):
                    sp_ = (ps[i] if i < len(ps) else 0.0) if isinstance(ps, (list, tuple)) else ps
                    x0, x1, yf, fc = IC_NEIGHBOURS[i][:4]
                    var.append(('porch%d' % i, [Lamp(IC_NEIGHBOURS[i][6], 1.95, yf - 0.5 * fc, 6.5, '#ffc888', 1.4, fall=1.5)], _kfn(sp_, 510 + i)))
        return amb, steady, var

    def shell(self, pen, v, o):
        tod = o.get('tod', 'night')
        ic_sky(pen, v, tod)
        dr_far_ring(pen, v, 'night' if tod in ('night', '1958') else 'dawn', G=IC_G)
        ic_ground(pen, v, o)
        if o.get('layout') == 'town': return
        hs = [_ic_neighbour(i) for i in range(len(IC_NEIGHBOURS))]
        hs.sort(key=lambda H: -v.d((H['x0'] + H['x1']) / 2, H['yf'] + 4.5 * H['face']))
        for H in hs:
            if v.d((H['x0'] + H['x1']) / 2, H['yf'] + 4.5 * H['face']) > 2.0:
                ic_house(pen, v, H, tod)
        for (x, y) in IC_LAMPS:
            if v.d(x, y) > 0.8: ic_lamp(pen, v, x, y)
        for i, (x, y, h) in enumerate([(-24.0, 5.0, 9.0), (11.5, 6.0, 10.0), (-20.0, -30.0, 9.5), (11.0, -31.0, 9.0), (-8.0, 9.5, 11.0)]):
            if v.d(x, y) < 1.0: continue
            bx, by = v.p(x, IC_SNOWY, y)
            draw_tree(pen, bx, by, h * v.s(x, y), 0.0, 620 + i, 0.0, '#0a0e18' if tod in ('night', '1958') else '#3a3434', None, 5)

    def pieces(self, o):
        tod = o.get('tod', 'night')
        P = []
        if o.get('layout') == 'town':
            H = dict(_ic_neighbour(1), x0=-5.0, x1=5.0, yf=-24.0, face=-1, chimney=(2.8, -28.5, 0.6), plight=None, porch=(-1.2, 1.2, 1.2), steps=(-0.5, 0.5, 0.8),
                     door=(-0.45, 0.45, 2.05, '#3a3a44', None), wins=[('a', -3.8, -2.4, 0.9, 2.05), ('b', 2.4, 3.8, 0.9, 2.05)], siding='#9aa4b0', frost=0.9)
            P.append(Piece('town_house', (0.0, 2.0, -28.5), lambda pen, v: ic_house(pen, v, H, tod), block=_r4p((-5.0, 5.0, -33.0, -24.0))))
            self.o['_town_house'] = H
        else:
            HO = _ic_our_house(o); HK = _ic_kessler_house(o)
            if tod == '1958':
                HO = dict(HO, siding='#b0a890', door=(IC_FDOOR[0], IC_FDOOR[1], IC_FDOOR[2], '#4a3a2a', None)); HK = dict(HK, siding='#a8a090')
            P.append(Piece('house', (0.0, 2.0, 4.5), lambda pen, v: ic_house(pen, v, HO, tod), block=_r4p(IC_HOUSE)))
            P.append(Piece('kessler', (IC_KH[0] * 0.5 + IC_KH[1] * 0.5, 2.0, -28.5), lambda pen, v: ic_house(pen, v, HK, tod),
                           block=_r4p((IC_KH[0], IC_KH[1], IC_KH[2], IC_KH[3]))))
            if o.get('fence', True):
                P.append(Piece('fence', (0.0, IC_G + 0.6, IC_FENCE_Y), lambda pen, v: ic_fence(pen, v), block=None))
            if o.get('car', True) and tod != '1958':
                cp = ic_car()
                P.append(Piece('car', (IC_CAR[0], IC_G + 0.8, IC_CAR[1]), lambda pen, v, ps=cp: draw_parts(pen, v, ps), block=_r4p((IC_CAR[0] - 0.95, IC_CAR[0] + 0.95, IC_CAR[1] - 2.3, IC_CAR[1] + 2.3))))
            if tod == '1958':
                for (cx_, cy_, fa_, col_) in ((-9.0, -9.3, -90.0, '#6a8a9a'), (14.0, -14.7, 90.0, '#9a5a4a')):
                    cp = ic_car(cx_, cy_, fa_, col_, era='1958', snow=True)
                    P.append(Piece('car58_%d' % int(cx_), (cx_, IC_G + 0.8, cy_), lambda pen, v, ps=cp: draw_parts(pen, v, ps)))
            P.append(Piece('our_lamp', (IC_LAMP[0], IC_G + 3.0, IC_LAMP[1]), lambda pen, v: ic_lamp(pen, v, IC_LAMP[0], IC_LAMP[1]), block=_circ(IC_LAMP[0], IC_LAMP[1], 0.15)))
        pos = self._truck_pos(o)
        if pos:
            P.append(ic_truck_piece('truck', pos))
        pl = o.get('plow')
        if pl and not callable(pl.get('x', 0.0)):
            fa = 90.0 if pl.get('dir', 1) > 0 else -90.0
            pp = ic_plow_parts(pl.get('x', 0.0), pl.get('y', IC_PLOW_LANE[0]), fa)
            P.append(Piece('plow', (pl.get('x', 0.0), IC_G + 1.5, pl.get('y', IC_PLOW_LANE[0])), lambda pen, v, ps=pp: draw_parts(pen, v, ps)))
        for it in o.get('props') or []:                                       # ('boot', x, y) | ('mitten', x, y, colour)
            P.append(_snow_prop_piece(it))
        return P

    def glows(self, v, o):
        tod = o.get('tod', 'night'); night = tod in ('night', '1958')
        G = []
        ks = _kfn(o.get('street', 1.0) if night else 0.0, 501)
        kp = _kfn(o.get('porch', 0.0), 502); kk = _kfn(o.get('kporch', 0.0), 503)
        town = o.get('layout') == 'town'
        def lampg(pen, t):
            if night and not town:
                for (x, y) in IC_LAMPS: ic_lamp_glow(pen, v, x, y, 1.0, t)
        G.append(('far_lamps', (0.0, 3.0, -60.0), lampg))
        if night and not town:
            G.append(('our_lamp_glow', (IC_LAMP[0], 3.0, IC_LAMP[1]), lambda pen, t: ic_lamp_glow(pen, v, IC_LAMP[0], IC_LAMP[1], ks(t), t)))
        if not town:
            HO = _ic_our_house(o); HK = _ic_kessler_house(o)
            wins = {nm: _kfn(lv, 520 + i) for i, (nm, lv) in enumerate((o.get('win') or {}).items())}
            qo = _house_win_quads(HO); qk = _house_win_quads(HK)
            smoke = _kfn(o.get('smoke', 0.0), 530); osmoke = _kfn(o.get('our_smoke', 1.0 if not o.get('blackout') else 0.0), 531)
            def house_g(pen, t):
                k = kp(t)
                if k > 0.01 and v.d(IC_PLIGHT[0], IC_PLIGHT[2]) > 0.3:
                    x, y = v.p(*IC_PLIGHT); s = v.s(IC_PLIGHT[0], IC_PLIGHT[2])
                    pen.glow(x, y, 1.4 * s, '#ffc070', 110 * k); pen.glow(x, y, 0.1 * s, '#fff4d8', 240 * k)
                for nm, kf in wins.items():
                    if nm in qo:
                        k = kf(t)
                        if k > 0.01 and v.visible(qo[nm][0], (0, 0, -1)): _win_glow(pen, v, qo[nm], k, curtain=(nm == 'liv'))
                if night:                                                    # the window frost catches the moon
                    for nm, q in qo.items():
                        if v.visible(q[0], (0, 0, -1)) and v.d(q[0][0], q[0][2]) > 0.4:
                            path = v.poly3(q)
                            if not path.isEmpty(): pen.fill(path, '#c8d8ff', 18)
                ok = osmoke(t)
                if ok > 0.01: ic_smoke(pen, v, -4.2, 5.0 + 0.95, 4.0, t, ok, 7, tod)
            G.append(('house_glow', (0.0, 2.0, 4.5), house_g))
            def kess_g(pen, t):
                k = kk(t)
                if k > 0.01 and v.d(2.25, IC_KH[3]) > 0.3:
                    P_ = (2.25, IC_KFLOOR + 1.95, IC_KH[3] + 0.07); x, y = v.p(*P_); s = v.s(P_[0], P_[2])
                    pen.glow(x, y, 1.4 * s, '#ffc070', 110 * k); pen.glow(x, y, 0.1 * s, '#fff4d8', 240 * k)
                for nm, kf in wins.items():
                    if nm in ('his', 'k2') and nm in qk:
                        k = kf(t)
                        if k > 0.01 and v.visible(qk[nm][0], (0, 0, 1)): _win_glow(pen, v, qk[nm], k, curtain=False)
                ks_ = smoke(t)
                if ks_ > 0.01: ic_smoke(pen, v, IC_KCHIM[0], 4.7 + 0.95, IC_KCHIM[1], t, ks_, 9, tod)
            G.append(('kessler_glow', (IC_KH[0] * 0.5 + IC_KH[1] * 0.5, 2.0, -28.5), kess_g))
            nb = o.get('porches')
            kn = [_kfn((nb[i] if i < len(nb) else 0.0) if isinstance(nb, (list, tuple)) else (nb if nb is not None else 0.0), 510 + i) for i in range(len(IC_NEIGHBOURS))]
            lit_rooms = o.get('neighbour_lit', 1.0 if night else 0.0)
            def nbr(pen, t):
                for i in range(len(IC_NEIGHBOURS)):
                    H = _ic_neighbour(i)
                    q = _house_win_quads(H)
                    nrm = (0, 0, -H['face'])
                    for j, (nm, qq) in enumerate(q.items()):
                        pass
                    for (wn, wx0, wx1, sl, tp) in H['wins']:
                        Yy = H['yf'] - 0.012 * H['face']
                        qq = [(wx0, tp, Yy), (wx1, tp, Yy), (wx1, sl, Yy), (wx0, sl, Yy)]
                        if lit_rooms > 0.01 and v.visible(qq[0], nrm) and v.d((wx0 + wx1) / 2, Yy) > 1.0 and (int(wx0 * 3) % 3 != 0):
                            _win_glow(pen, v, qq, 0.75 * lit_rooms, curtain=True)
                    k = kn[i](t) if i < 4 else 0.0
                    P_ = (H['plight'], 1.95, H['yf'] - 0.07 * H['face'])
                    if k > 0.01 and v.d(P_[0], P_[2]) > 0.5:
                        x, y = v.p(*P_); s = v.s(P_[0], P_[2])
                        pen.glow(x, y, 2.6 * s, '#ffc070', 150 * k); pen.glow(x, y, 0.22 * s, '#fff4d8', 255 * k)   # a real pool on porch + step
                        pen.glow(x, y, 0.7 * s, '#ffe0a0', 200 * k)
                        px_, py_ = v.p(P_[0], 0.45, P_[2] - 0.5 * H['face'])
                        pen.ellipse_glow(px_, py_, 1.8 * s, 0.55 * s, '#ffc070', 110 * k)
                        gx, gy = v.p(P_[0], IC_SNOWY, P_[2] - 1.2 * H['face'])
                        pen.ellipse_glow(gx, gy, 2.8 * s, 0.75 * s, '#ffc070', 95 * k)
                    if night and o.get('neighbour_smoke', True):
                        ch = H['chimney']; ic_smoke(pen, v, ch[0], 4.8 + 0.95, ch[1], t, 0.8, 40 + i, tod)
            G.append(('far_houses', (0.0, 3.0, -50.0), nbr))
        else:
            H = self.o.get('_town_house')
            def town_g(pen, t):
                if night:
                    for (wn, wx0, wx1, sl, tp) in H['wins']:
                        qq = [(wx0, tp, -23.99), (wx1, tp, -23.99), (wx1, sl, -23.99), (wx0, sl, -23.99)]
                        if v.d(wx0, -24) > 0.5: pen.fill(v.poly3(qq), '#0a1020', 120)
            G.append(('town_house_glow', (0.0, 2.0, -28.5), town_g))
        pos = self._truck_pos(o)
        if pos:
            kw = _kfn(o.get('truck_win', 1.0), 504); ko = _kfn(o.get('truck_open', 0.0), 506); kh = _kfn(o.get('truck_heads', 0.0), 507)
            ms, lina = o.get('mittens'), o.get('lina_mitten', False)
            G.append(('truck_glow', (pos[0], 1.5, pos[1]), lambda pen, t: ic_truck_emit(pen, v, pos[0], pos[1], pos[2], IC_G, kw(t), ko(t), ms, lina, kh(t), t)))
        pl = o.get('plow')
        if pl:
            kb = _kfn(pl.get('beacon', 1.0), 505)
            x = pl.get('x', 0.0)
            fa = 90.0 if pl.get('dir', 1) > 0 else -90.0
            if not callable(x):
                G.append(('plow_glow', (x, 1.5, pl.get('y', IC_PLOW_LANE[0])), lambda pen, t: ic_plow_emit(pen, v, x, pl.get('y', IC_PLOW_LANE[0]), fa, t, kb(t) if callable(pl.get('beacon')) else 1.0)))
        if night and o.get('dust', True):
            def dust(pen, t):
                if v.d(IC_LAMP[0], IC_LAMP[1]) > 1.0:
                    x, y = v.p(IC_LAMP[0], IC_G + 3.0, IC_LAMP[1] - 1.0); s = v.s(IC_LAMP[0], IC_LAMP[1])
                    ic_breath_air(pen, v, t, (x - 2.5 * s, y - 2.5 * s, x + 2.5 * s, y + 2.5 * s), 40, 9, ks(t))
                ic_breath_air(pen, v, t, (0, 0, 1920, 1080), 26, 4, 0.5)
            G.append(('dust', (0.0, 2.0, -0.5 + v.hy + 2.0 * v.fy), dust))
        return G

    def spots(self, v, o):
        S = {}
        G, F = IC_G, IC_FOOT
        def M(n, x, y, Y, kind, note, face=None, **kw): S[n] = _mk_spot(v, n, x, y, Y, kind, note, face=face, **kw)
        dx = (IC_FDOOR[0] + IC_FDOOR[1]) / 2
        M('porch_door', dx, -0.45, 0.0, 'stand', 'on our stoop at the front door, facing it (+y)', (0, 1))
        M('porch_out', dx, -0.45, 0.0, 'stand', 'on our stoop facing the street (-y)', (0, -1))
        M('door_glass', dx, -0.03, 1.58, 'point', 'the clear strip of the front-door glass (outside face)')
        M('door_knob', IC_FDOOR[1] - 0.08, -0.04, 0.98, 'point', 'the front-door knob (outside)')
        M('drop', dx, -1.0, 0.0, 'stand', 'right in front of our door (he drops here from the roof, facing the door)', (0, 1))
        M('steps', dx, -1.75, G + (0.0 - G) / 3, 'stand', 'on our steps', (0, -1))
        M('walk', dx, -4.0, G + (0.03 if o.get('walk') == 'shoveled' else IC_SNOW - IC_SINK), 'stand', 'on our front walk (in the snow unless shoveled)', (0, -1))
        M('gate', dx, IC_FENCE_Y - 0.3, F, 'stand', 'at the gate in the fence', (0, -1))
        M('sidewalk', dx, -7.3, F, 'stand', 'on our buried sidewalk', (0, -1))
        M('curb', -0.6, -7.85, G + 0.55, 'stand', 'on top of the plow bank at our kerb', (0, -1))
        M('yard_mid', 1.6, -3.6, F, 'stand', 'the middle of our front yard (knee-deep)', (0, -1))
        M('yard_run', -1.0, -5.0, F, 'stand', 'running back from the truck to the door', (0, 1))
        M('window_out', 3.4, -0.6, F + 0.0, 'stand', 'in the snow outside our picture window', (0, 1))
        M('liv_window', 3.4, -0.02, 1.45, 'point', 'our picture window (outside: the curtain crack)')
        M('kitchen_sill', (IC_KWIN[0] + IC_KWIN[1]) / 2, -0.12, IC_KWIN[2] + 0.02, 'surface', "the kitchen window's OUTSIDE sill (the cone, five minutes later)")
        M('bath_window', (IC_BWIN[0] + IC_BWIN[1]) / 2, -0.02, 1.55, 'point', 'our small frosted bathroom window (outside)')
        for i, x in enumerate((-12.0, -8.0, -4.5, 0.5, 4.0, 6.4)):
            M('fence%d' % i, x, IC_FENCE_Y, G + 1.0, 'stand', 'on the top rail of the fence (his scuttle: 0 west .. 5 east)', (1, 0))
        M('car_roof', IC_CAR[0], IC_CAR[1] + 0.2, G + 1.52, 'stand', "on Dad's car roof", (-0.6, 0.8))
        M('car_hood', IC_CAR[0], IC_CAR[1] - 1.5, G + 1.04, 'stand', "on Dad's car hood", (0, 1))
        M('eave', 5.0, -0.35, 2.6, 'stand', 'on our roof edge at the east end', (-1, 0))
        M('roof', 1.0, 2.0, 2.6 + (5.0 - 2.6) * (2.0 + 0.35) / 4.85, 'stand', 'on our front roof slope above the door side', (-1, -0.2))
        M('roof_edge_door', dx, -0.3, 2.6, 'stand', 'on the eave right above our door (he drops from here)', (0, -1))
        M('ridge', 0.0, 4.5, 5.0, 'stand', 'on our roof ridge')
        M('chimney_top', -4.2, 4.0, 5.9, 'point', 'our chimney top (smoke until the power dies)')
        M('lamp', IC_LAMP[0], IC_LAMP[1] - 1.6, G + 6.0, 'point', 'the streetlight head (it flickers)')
        M('street_mid', 1.0, -12.0, G + 0.02, 'stand', 'the middle of Birch Lane')
        M('cross1', 0.4, -10.8, G + 0.02, 'stand', 'crossing: the north half of the lane', (0.1, -1))
        M('cross2', 1.2, -13.2, G + 0.02, 'stand', 'crossing: the south half of the lane', (0.05, -1))
        M('kgate', 1.4, -16.8, F, 'stand', "on Kessler's buried sidewalk at his walk", (0, -1))
        M('kwalk_mid', 1.4, -19.6, G + (0.03 if o.get('kwalk') == 'shoveled' else IC_SNOW - IC_SINK), 'stand', "halfway down Kessler's walk", (0, 1))
        M('kessler_half', -0.65, -19.7, IC_FOOT, 'stand', "Mr. Kessler halfway from his porch to the window at B (crossing his yard, facing it)", (-0.5, 0.85))
        M('kwalk_shovel1', 0.6, -18.4, G + 0.03, 'stand', "shoveling Kessler's walk (morning: Dad)", (0.6, 0.8))
        M('kwalk_shovel2', 2.2, -20.2, G + 0.03, 'stand', "shoveling Kessler's walk (morning: Adam)", (-0.5, 0.8))
        M('kwalk_shovel3', 1.4, -21.2, G + 0.03, 'stand', "on Kessler's walk (morning: Lina with the cocoa)", (0, -1))
        M('ksteps', 1.4, -22.2, G + 2 * (0.0 - G) / 3, 'stand', "on Kessler's steps", (0, 1))
        M('kporch', 1.4, -23.1, IC_KFLOOR, 'stand', "on Kessler's porch facing the street (his one step off it)", (0, 1))
        M('kdoor', 1.4, -23.75, IC_KFLOOR, 'stand', "in Kessler's open doorway facing out (the huddle: three under one blanket)", (0, 1))
        M('kdoor_in', 1.4, -24.4, IC_KFLOOR, 'stand', "just inside Kessler's door (his dark hallway)", (0, 1))
        M('kdoor_l', 1.05, -23.65, IC_KFLOOR, 'stand', "Kessler's doorway, the west side (Adam)", (0.3, 1))
        M('kdoor_r', 1.8, -23.65, IC_KFLOOR, 'stand', "Kessler's doorway, the east side (Lina)", (-0.3, 1))
        M('kwindow', (IC_KWIN2[0] + IC_KWIN2[1]) / 2, IC_KH[3] + 0.02, IC_KFLOOR + 1.5, 'point', "HIS window (where his hand lifts and his breath fogs the glass)")
        M('kchimney', IC_KCHIM[0], IC_KCHIM[1], 4.7 + 1.0, 'point', "Kessler's chimney top (no smoke; smoke again in the morning)")
        pos = self._truck_pos(o)
        if pos:
            S.update(ic_truck_spots(v, 'truck_', pos))
            if pos == IC_TRUCK_A:
                M('boot', -0.45, -7.55, IC_FOOT, 'surface', "Adam's boot frozen in the snow (where he stood at the window)")
                M('lina_window', -0.58, -7.72, G + 0.55 - 0.1, 'stand', 'Lina at the pink window, on the bank at our kerb, facing it', (0, -1))
                M('adam_grab', -1.1, -7.3, F, 'stand', 'Adam yanking Lina back (a step behind her, facing the truck)', (0.2, -1))
                M('mitten1', -2.05, -1.6, IC_SNOWY + 0.005, 'surface', "Lina's first mitten in the snow (by our steps)")
                M('mitten2', -1.7, -4.2, IC_SNOWY + 0.005, 'surface', "Lina's second mitten (halfway down the walk)")
            if pos == IC_TRUCK_B:
                M('kessler_window_b', -2.73, -16.3, G + 0.02, 'stand', "Mr. Kessler at the pink window (position B), facing it", (0, 1))
                M('cage', -0.6, -18.4, IC_FOOT, 'stand', 'the kids under the blanket where his legs cage them (between the truck and his walk)', (0.4, -1))
        return S


def _circ(x, y, r, n=10):
    return [(x + r * math.cos(2 * math.pi * k / n), y + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def _snow_prop_piece(it):
    kind, x, y = it[0], it[1], it[2]
    if kind == 'boot':
        def fn(pen, v):
            ic_boot(pen, v, x, y)
        return Piece('boot', (x, IC_SNOWY, y), fn)
    c = it[3] if len(it) > 3 else IC_LINA_MITTEN
    return Piece('mitten_%d' % int(abs(x * 10)), (x, IC_SNOWY, y), lambda pen, v: ic_mitten(pen, v, x, y, c))


def ic_boot(pen, v, x, y, Y=None):
    """Adam's snow boot frozen upright in the snow (the shaft sticking out, the laces, a rime of ice round it)."""
    Y = IC_FOOT if Y is None else Y
    if v.d(x, y) < 0.4: return
    s = v.s(x, y)
    bx, by = v.p(x, IC_SNOWY, y)
    pen.fill(oval(bx, by, 0.16 * s, 0.05 * s), '#3a4a7a', 120, blur=2)
    sh = rrect(bx - 0.07 * s, by - 0.26 * s, 0.14 * s, 0.27 * s, 0.03 * s)
    pen.fill(sh, '#3a2a22'); pen.line(sh, 1.0)
    pen.fill(rrect(bx - 0.08 * s, by - 0.29 * s, 0.16 * s, 0.05 * s, 0.02 * s), '#c8c0b0')                  # the fleece cuff
    for k in range(4): pen.seg((bx - 0.04 * s, by - (0.08 + 0.04 * k) * s), (bx + 0.04 * s, by - (0.1 + 0.04 * k) * s), max(0.6, 0.008 * s), '#d8cca8')
    pen.fill(oval(bx, by - 0.01 * s, 0.11 * s, 0.035 * s), '#eaf4ff', 230)


def ic_mitten(pen, v, x, y, c=IC_LINA_MITTEN, rot=20.0):
    if v.d(x, y) < 0.4: return
    s = v.s(x, y); bx, by = v.p(x, IC_SNOWY, y)
    pen.cv.save(); pen.cv.translate(bx, by); pen.cv.scale(1.0, 0.45); pen.cv.rotate(rot)
    sc = 0.2 * s
    m = union(rrect(-sc * 0.4, -sc * 0.5, sc * 0.8, sc, sc * 0.38), oval(sc * 0.4, -sc * 0.05, sc * 0.18, sc * 0.26))
    pen.fill(m, c); pen.line(m, max(0.6, sc * 0.05), '#2a1a10', 200)
    pen.fill(rect(-sc * 0.42, sc * 0.35, sc * 0.84, sc * 0.18), mix(c, '#ffffff', 0.4))
    pen.cv.restore()


def ic_street(view='house', tod='night', truck='A', truck_win=1.0, truck_open=0.0, mittens=None, lina_mitten=False, truck_heads=0.0, street=1.0,
              porch=0.0, kporch=0.0, porches=None, win=None, smoke=0.0, our_smoke=None, walk='buried', kwalk='buried', tracks=None, props=None,
              plow=None, door_open=False, kdoor_open=False, blackout=False, dust=True, **kw):
    """Birch Lane. view: see IC_API['ic_street'] (house, kessler, lane, lane_e, truck, curb, window_close, door, yard, roof,
    kwide, kporch, kdoor, kout, bathout, plow, gap). tod 'night' | 'morning' | '1958'. truck 'A' | 'B' | None | (x, y, fa).
    truck_win (pink window level), truck_open 0..1 (the serving glass slid aside), mittens (colour list; None = the
    night's bunting, the small red one first), lina_mitten (hers added at the right end), truck_heads. street: the
    flickering streetlight (ST.ic_flicker(t0)); porch / kporch: our / Kessler's porch lights; porches: the neighbours'
    porch lights coming on one by one (a level spec or a list of 4); win {'liv', 'kitchen', 'bath', 'his', 'k2'}: lit
    windows; smoke: Kessler's chimney (0 at night, 1 in the morning); our_smoke; walk / kwalk 'buried' | 'shoveled' |
    'trodden'; tracks [(kind 'child' | 'adult' | 'benny', [(x, y), ...])]; props [('boot', x, y), ('mitten', x, y, c)];
    plow dict(x, y (lane), dir +1 east / -1 west, beacon level spec); door_open / kdoor_open; blackout (our house dark)."""
    o = dict(tod=tod, truck=truck, truck_win=truck_win, truck_open=truck_open, mittens=mittens, lina_mitten=lina_mitten, truck_heads=truck_heads,
             street=street, porch=porch, kporch=kporch, porches=porches, win=dict(win or {}), smoke=smoke, walk=walk, kwalk=kwalk, tracks=tracks,
             props=props, plow=plow, door_open=door_open, kdoor_open=kdoor_open, blackout=blackout, dust=dust, no_veil=True)
    if our_smoke is not None: o['our_smoke'] = our_smoke
    o.update(kw)
    v = cam('ic_ext_' + view)
    main = IcStreet(o)
    dyn = []
    amb, steady, var = main.lights(o)
    if plow and callable(plow.get('x')):
        xf = plow['x']; ly = plow.get('y', IC_PLOW_LANE[0]); fa = 90.0 if plow.get('dir', 1) > 0 else -90.0
        kb = _kfn(plow.get('beacon', 1.0), 505)
        def plow_live(pen, v_, t):
            x = xf(t)
            draw_parts(pen, v_, ic_plow_parts(x, ly, fa))
        dyn.append(live_layer('plow', v, (xf(0.0), IC_G + 1.5, ly), plow_live, amb, steady, var))
        lay = Layer(max(0.3, v.d(xf(0.0), ly)), lambda pen, t: ic_plow_emit(pen, v, xf(t), ly, fa, t, kb(t)), 'plow_glow', blur=None)
        lay.order = v.d(xf(0.0), ly) - 0.01
        dyn.append(lay)
    grade = {'night': 'ic_ext', 'morning': 'ic_morning', '1958': 'ic_1958'}.get(tod, 'ic_ext')
    sp = build_view('ic_ext_' + view, v, main, o, outside=None, lens='lens', grade=grade, dyn=dyn, dof=0.6)
    if view == 'gap':
        sp = sp.add(_curtain_gap_layer(0.16))
    if view == 'bathout':
        sp = sp.add(_ic_frosted_frame_layer())
    sp.info['note'] = ('Birch Lane: our house north (front y 0), Kessler\'s opposite (front y -24); truck A at our kerb heading west '
                       '(serving window north), truck B at his kerb heading east (serving window south). Figures order = sp.order_at(x, y).')
    sp.info['truck'] = main._truck_pos(o)
    sp.paths['lina_out'] = [sp.anchors[k_] for k_ in ('porch_out', 'steps', 'walk', 'gate', 'sidewalk') if k_ in sp.anchors]
    sp.paths['scuttle'] = [sp.anchors[k_] for k_ in ('fence2', 'fence3', 'fence4', 'fence5', 'car_hood', 'car_roof', 'eave', 'roof_edge_door', 'drop') if k_ in sp.anchors]
    sp.paths['cross'] = [sp.anchors[k_] for k_ in ('porch_out', 'steps', 'walk', 'gate', 'curb', 'cross1', 'cross2', 'kgate', 'kwalk_mid', 'ksteps', 'kdoor') if k_ in sp.anchors]
    return sp


def _ic_frosted_frame_layer(wipe=(960, 520, 520, 330)):
    """Screen-space foreground for the POV through the bathroom window: the small sash, frost thick on the glass, a wiped
    patch (cx, cy, rx, ry) he cleared with his sleeve."""
    def draw(pen, t):
        frame = minus(rect(-400, -300, 2720, 1700), rrect(260, 90, 1400, 900, 6))
        glass = rrect(260, 90, 1400, 900, 6)
        pen.cv.save(); pen.cv.clipPath(minus(glass, oval(*wipe)), skia.ClipOp.kIntersect, True)
        pen.fill(glass, '#dfe8f8', 200)
        pen.texture(glass, 'grunge', 0.6, 'overlay', 2.0)
        rng = np.random.default_rng(4)
        for i in range(60):
            x, y = rng.uniform(260, 1660), rng.uniform(90, 990)
            pen.line(poly([(x, y), (x + rng.uniform(-60, 60), y + rng.uniform(-60, 60))], False), 1.2, '#ffffff', 120)
        pen.cv.restore()
        ring = minus(oval(wipe[0], wipe[1], wipe[2] + 60, wipe[3] + 50), oval(*wipe))
        pen.fill(ring, '#e8f0ff', 110, blur=30)
        pen.fill(frame, '#e8e8ec'); pen.linear(frame, 0, 0, 0, 1080, [(0, '#5a5e6a'), (1, '#2a2c34')])
        pen.fill(rect(-400, 990, 2720, 60), '#d8dce4')
    return Layer(0.3, draw, 'bath_frame', blur=6)


_icam('ic_ext_house', 760, 540, IC_G + 1.65, 3.6, -21.5, -4, _env(f=(1.0, 2.4)), 'our house from across Birch Lane: the truck at A in front, the fence, the roof, Dad\'s car', 'street')
_icam('ic_ext_kessler', 820, 520, 1.5, 3.2, -2.6, 186, _env(x=(900, 1020), y=(480, 580), f=(1.0, 2.6)), "from our yard across the lane to Kessler's house: his window, his chimney (the truck at A on the right)", 'street')
_icam('ic_ext_lane', 860, 540, IC_G + 1.7, -19.0, -12.4, 90, _env(f=(1.0, 2.6)), 'down Birch Lane from the west: our house left, Kessler\'s right, the truck gliding in (no tracks behind)', 'street')
_icam('ic_ext_lane_e', 860, 540, IC_G + 1.7, 19.5, -11.6, -90, _env(f=(1.0, 2.6)), 'up Birch Lane from the east: our house right, Kessler\'s left', 'street')
_icam('ic_ext_truck', 800, 520, IC_FOOT + 1.15, -2.1, -4.4, 156, _env(), 'the truck at A from our walk at child height: the serving window, the sign, the flake', 'street')
_icam('ic_ext_curb', 1000, 470, IC_G + 0.95, -1.3, -6.3, 142, _env(), 'low at the kerb, up at the serving window (he leans down, further than a man can bend)', 'street', pitch=-12.0)
_icam('ic_ext_window_close', 1650, 520, IC_G + 1.95, 0.28, -5.6, 180, _env(x=(920, 1000), y=(500, 560), zoom=(1.0, 1.1)), 'the truck window close-up: the pink glow, the frost, the mitten bunting', 'street')
_icam('ic_ext_door', 950, 520, IC_G + 1.5, -2.1, -5.4, 0, _env(), 'our front door from the walk: the stoop, the glass strip, the porch light', 'street')
_icam('ic_ext_yard', 700, 520, IC_G + 1.9, 2.0, -16.5, 16, _env(f=(1.0, 2.2)), "the yard wide from the lane: the fence, Dad's car, our roof (the chase route)", 'street')
_icam('ic_ext_roof', 760, 420, IC_G + 1.25, 1.2, -5.4, -8, _env(), 'up at our roof and eave from the yard (him on the roof)', 'street', pitch=-16.0)
_icam('ic_ext_kwide', 760, 520, IC_G + 1.6, 9.0, -21.2, -72, _env(), "Kessler's porch and the truck at B (its serving window facing his door)", 'street')
_icam('ic_ext_kporch', 900, 520, IC_G + 1.5, 2.6, -17.2, 196, _env(), "Kessler's porch and door from his walk", 'street')
_icam('ic_ext_kdoor', 980, 520, IC_G + 1.25, 1.6, -20.0, 182, _env(), "close on Kessler's doorway at child height (the huddle)", 'street')
_icam('ic_ext_kout', 820, 520, IC_KFLOOR + 1.45, 1.4, -23.2, -10, _env(), "from Kessler's doorway out: the truck at B, its pink window facing us, our house across the lane", 'street')
_icam('ic_ext_bathout', 900, 540, 1.55, -0.5, 0.25, 176, _env(x=(940, 980), y=(520, 560), zoom=(1.0, 1.03)), 'POV through our bathroom window across the lane to Kessler\'s door', 'street')
_icam('ic_ext_plow', 820, 520, IC_G + 1.6, 2.4, -4.4, 198, _env(), "the plow passing on Birch Lane (the orange beacon sweeping), from our yard", 'street')
_icam('ic_ext_gap', 1000, 520, 1.25, 3.4, 0.3, 197, _env(x=(920, 1000), y=(500, 560), zoom=(1.0, 1.06)), 'POV through the curtain crack: the truck at A, Kessler\'s window beyond', 'street')


# ====================================================================================================== props shared by sets
def ic_cone(pen, v, x, Y, y, state='whole', s=1.0, t=0.0, steam=1.0):
    """HIS free one: a pink-and-white swirl cone in a waxed wrapper, steaming with cold (state 'whole' | 'shards' (on
    the floor, shattered like glass)). Drawn upright at plan point (x, Y, y), ~0.22 m tall."""
    if v.d(x, y) < 0.25: return
    k = v.s(x, y) * s
    bx, by = v.p(x, Y, y)
    if state == 'shards':
        rng = np.random.default_rng(int(abs(x * 100 + y * 10)) + 3)
        pen.fill(oval(bx, by, 0.26 * k, 0.07 * k), '#000000', 60, blur=3)
        for i in range(16):
            a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.02, 0.3) * k
            px, py = bx + math.cos(a) * r, by + math.sin(a) * r * 0.3
            sz = rng.uniform(0.008, 0.03) * k
            c = ('#f7c6dc', '#fbf3f6', '#e58fb4', '#d8a868')[i % 4]
            sh = poly([(px - sz, py), (px, py - sz * 1.3), (px + sz * 1.2, py - sz * 0.2), (px + sz * 0.3, py + sz * 0.6)])
            pen.fill(sh, c, 235); pen.line(sh, 0.6, '#ffffff', 160)
        pen.fill(oval(bx + 0.05 * k, by, 0.045 * k, 0.02 * k), '#d8a868'); pen.line(oval(bx + 0.05 * k, by, 0.045 * k, 0.02 * k), 0.6)
        return
    h = 0.22 * k
    cone = poly([(bx - 0.035 * k, by - h * 0.55), (bx + 0.035 * k, by - h * 0.55), (bx, by)])
    pen.fill(cone, '#d8a868'); pen.line(cone, 0.8)
    for i in range(3): pen.seg((bx - 0.03 * k + i * 0.02 * k, by - h * 0.5), (bx + 0.01 * k, by - h * 0.1), 0.6, '#a87838', 200)
    for i, (dy, w, c) in enumerate(((0.55, 0.05, '#fbf3f6'), (0.68, 0.045, IC_STRIPE), (0.8, 0.035, '#fbf3f6'), (0.9, 0.022, IC_STRIPE))):
        sw = oval(bx + (0.004 if i % 2 else -0.004) * k, by - h * dy, w * k, 0.03 * k)
        pen.fill(sw, c); pen.line(sw, 0.7, '#8a4a6a', 200)
    pen.fill(poly([(bx - 0.006 * k, by - h * 0.95), (bx + 0.008 * k, by - h * 1.02), (bx + 0.002 * k, by - h * 0.9)]), '#fbf3f6')
    wr = poly([(bx - 0.045 * k, by - h * 0.5), (bx + 0.045 * k, by - h * 0.5), (bx + 0.02 * k, by - h * 0.18), (bx - 0.02 * k, by - h * 0.18)])
    pen.fill(wr, '#f4f0e8', 220); pen.line(wr, 0.6, '#9a9488', 200)
    if steam > 0.01:                                                          # cold vapour falling off it
        for i in range(4):
            ph = (t * 0.5 + i / 4) % 1.0
            pen.fill(oval(bx + (0.03 * math.sin(t + i)) * k, by - h * (0.9 - ph * 0.9), (0.04 + ph * 0.05) * k, 0.03 * k), '#ffffff', 50 * (1 - ph) * steam, blur=0.03 * k)


def ic_radio(pen, v, x, Y, y, ang=20.0, led=0.0, s=1.0):
    """Dad's chunky orange-and-black two-way radio (channel three) standing on its base."""
    bu_walkie(pen, v, x, Y, y, ang, '#e8761a', led, s)


# ====================================================================================================== our house: interior
def _ic_light(o):
    """Ambient for our house: warm with the power on, cold blue after it dies."""
    if o.get('blackout'): return '#141a30'
    if o.get('tod') == 'morning': return '#8a8070'
    return '#2a2a40'


def _ic_pink_k(o, gapk=1.0):
    return (0.35 + 0.65 * gapk) if o.get('truck') == 'A' else 0.0


def _ic_common_var(o, pink_panes, pink_d, beacon_panes, seed=600):
    """Variable lights every room shares: the truck's pink through its windows, Dad's beacon sweep, the phone, the
    flashlight."""
    var = []
    if pink_panes:
        var.append(('pink', [Lamp(kind='win', c=IC_PINK, k=1.4, soft=8.0, panes=pink_panes, d=_norm3(pink_d))], _kfn(o.get('pink', 1.0 if o.get('truck') == 'A' else 0.0), seed)))
    if beacon_panes:
        var.append(('beacon', [Lamp(kind='win', c=IC_ORANGE, k=1.8, soft=8.0, panes=beacon_panes, d=_norm3((0.0, -0.3, 1.0)))], _kfn(o.get('beacon', 0.0), seed + 1)))
    P = o.get('phone_at', (0.0, 1.1, 2.0)); F_ = o.get('flash_at', (0.0, 1.0, 1.0))
    var.append(('phone', [Lamp(P[0], P[1], P[2], 2.6, '#e8f0ff', 1.1, (1.0, 1.0, 0.8), fall=1.7)], _kfn(o.get('phone', 0.0), seed + 2)))
    var.append(('flash', [Lamp(F_[0], F_[1], F_[2], 4.0, '#fff2d0', 1.3, (1.0, 1.0, 0.6), fall=1.5)], _kfn(o.get('flash', 0.0), seed + 3)))
    return var


def _ic_frost_layer(v, quads, spec, name='frost', seed=0, order=None):
    """Frost creeping across the INSIDE of the glass: feathery ferns growing in from the frame (level 0..1 or f(t))."""
    kf = _kfn(spec, 640 + seed)
    def draw(pen, t):
        k = kf(t)
        if k <= 0.01: return
        for qi, q in enumerate(quads):
            path = v.poly3(q)
            if path.isEmpty(): continue
            b = path.computeTightBounds()
            pen.cv.save(); pen.cv.clipPath(path, skia.ClipOp.kIntersect, True)
            pen.fill(path, '#dfe8f8', 50 * k)
            rng = np.random.default_rng(seed * 10 + qi)
            W, H = b.width(), b.height()
            for i in range(int(36 * k) + 4):
                ed = rng.integers(0, 4)
                if ed == 0: x, y, a = b.left(), b.top() + rng.uniform(0, H), 0.0
                elif ed == 1: x, y, a = b.right(), b.top() + rng.uniform(0, H), 180.0
                elif ed == 2: x, y, a = b.left() + rng.uniform(0, W), b.bottom(), -90.0
                else: x, y, a = b.left() + rng.uniform(0, W), b.top(), 90.0
                a = math.radians(a + rng.uniform(-35, 35))
                L = min(W, H) * rng.uniform(0.15, 0.55) * k
                pts = [(x, y)]
                for j in range(5):
                    x += math.cos(a) * L / 5; y += math.sin(a) * L / 5; a += rng.uniform(-0.4, 0.4)
                    pts.append((x, y))
                pen.line(smooth(pts, False), max(0.8, min(W, H) * 0.008), '#f4f8ff', 170)
                for j in range(1, len(pts)):
                    for sd in (-1, 1):
                        bl = L * 0.12
                        aa = a + sd * 0.9
                        pen.seg(pts[j], (pts[j][0] + math.cos(aa) * bl, pts[j][1] + math.sin(aa) * bl), max(0.6, min(W, H) * 0.004), '#ffffff', 140)
            pen.radial(path, (b.left() + b.right()) / 2, (b.top() + b.bottom()) / 2, max(W, H) * 0.75, [(0, '#ffffff', 0), (0.6, '#ffffff', 0), (1, '#e8f0ff', 170 * k)])
            pen.cv.restore()
    q0 = quads[0]
    lay = Layer(max(0.3, v.d(q0[0][0], q0[0][2])), draw, name, blur=None)
    lay.order = (min(v.d(p_[0], p_[2]) for p_ in q0) - 0.02) if order is None else order
    return lay


def _ic_outside(o):
    """Birch Lane through our front windows (cached): the sky, the snow, Kessler's house, the neighbours, the truck at
    its position with its pink window, the streetlights. Lit like the street set."""
    def f(pen, v):
        st = IcStreet(dict(o, dust=False))
        amb, steady, var = st.lights(o)
        varl = [Lamp.scaled(L_, _static(kspec(0.0) if callable(kspec) else kspec, 1.0)) for (nm, Ls, kspec) in var for L_ in Ls] if False else []
        st.shell(pen, v, dict(o))
        with lighting(amb, steady):
            ps = st.pieces(dict(o))
            ps.sort(key=lambda P: -v.d(P.ref[0], P.ref[2]))
            for P in ps:
                if P.name == 'house': continue
                P.draw(pen, v)
        tod = o.get('tod', 'night')
        if tod in ('night', '1958'):
            for (x, y) in IC_LAMPS + [IC_LAMP]: ic_lamp_glow(pen, v, x, y, 1.0)
        pos = st._truck_pos(o)
        if pos:
            ic_truck_emit(pen, v, pos[0], pos[1], pos[2], IC_G, _static(o.get('truck_win', 1.0), 1.0), _static(o.get('truck_open', 0.0)), o.get('mittens'), o.get('lina_mitten', False))
        if o.get('cone') == 'sill':
            ic_cone(pen, v, (IC_KWIN[0] + IC_KWIN[1]) / 2, IC_KWIN[2] + 0.01, -0.12)
    return f


def ic_front_door_art(side='in', rules=True, eighth=False):
    """Our front door (slate blue, two low panels) with the glass: a FROSTED panel and a CLEAR strip above it (both are
    real holes: the frosted glass is the live layer ic_door_glass); inside, the rules taped under the glass."""
    u0, u1, Y0, Y1, Y2 = IC_GLASS
    def art(p_, W, H):
        c = IC_PAL['door']
        p_.fill(rect(0, 0, W, H), c); p_.texture(rect(0, 0, W, H), 'wood', 0.3, 'overlay', 0.8, 90)
        gy = lambda Y: H - Y * 100
        p_.line(rect(u0 * 100 - 4, gy(Y2) - 4, (u1 - u0) * 100 + 8, gy(Y0) - gy(Y2) + 8), 3.0, _darken(c, 0.35), 230)
        p_.fill(rect(u0 * 100, gy(Y1) - 2, (u1 - u0) * 100, 4), _darken(c, 0.3))
        for (x0, y0, w, h) in ((10, H - 85, W / 2 - 15, 72), (W / 2 + 5, H - 85, W / 2 - 15, 72)):
            p_.fill(rect(x0, y0, w, h), _darken(c, 0.12)); p_.line(rect(x0, y0, w, h), 1.0, '#000000', 90)
        knob_x = 9 if side == 'in' else W - 9
        p_.fill(oval(knob_x, H - 98, 3.2), '#c8b070'); p_.line(oval(knob_x, H - 98, 3.2), 0.6)
        p_.fill(oval(knob_x, H - 116, 2.4), '#c8b070'); p_.line(oval(knob_x, H - 116, 2.4), 0.6)
        if side == 'in':
            p_.fill(rrect(knob_x - 1.4, H - 121, 2.8, 7, 1), '#a88a48')               # the deadbolt thumb-turn
            p_.fill(rect(knob_x + 3, H - 140, 2, 12), '#a8a8b0')                       # the chain
            if rules: _ic_rules_small(p_, W / 2, gy(Y0) + 8, W * 0.62, 34, eighth)
    return art


def _ic_rules_small(p_, cx, y, w, h, eighth=False):
    """The rules sheet as seen on the door from a distance: a white page, a heading, seven short lines, W.K."""
    p_.fill(rect(cx - w / 2 + 1, y + 1.5, w, h), '#000000', 60)
    p_.fill(rect(cx - w / 2, y, w, h), '#f6f2e6')
    btext(p_, 'RULES', cx, y + 5.5, 'sans_b', 4.2, '#1a1a2a', 230, 'center')
    for k in range(7):
        p_.fill(rect(cx - w / 2 + 3, y + 8 + k * 3.2, (w - 6) * (0.55 + 0.4 * ((k * 37) % 5) / 4), 1.1), '#2a2a3a', 210)
    if eighth: p_.fill(rect(cx - w / 2 + 3, y + 8 + 7 * 3.2, (w - 6) * 0.7, 1.3), '#2a3a8a', 220)
    btext(p_, 'W.K.', cx + w / 2 - 6, y + h - 2, 'hand', 3.6, '#1a1a2a', 230, 'center')
    for (tx, ty) in ((cx - w / 2 + 3, y), (cx + w / 2 - 3, y)): p_.fill(rect(tx - 3, ty - 1.5, 6, 3), '#e8e0c0', 200)


class IcDoor(Door):
    """A door leaf with real holes for its glass (our front door): the frosted panel and the clear strip."""
    def __init__(self, *a, glass=None, **kw):
        Door.__init__(self, *a, **kw)
        self.glass = glass

    def draw(self, pen, v, ang=0.0):
        B = self.box(ang)
        holes = None
        if self.glass:
            u0, u1, Y0, Y1, Y2 = self.glass
            H = self.h * 100
            holes = [rect(u0 * 100, H - Y2 * 100, (u1 - u0) * 100, (Y2 - Y0) * 100)]
        fs = B.faces()
        order = sorted(fs.items(), key=lambda kv: -v.d(kv[1].centre()[0], kv[1].centre()[2]))
        for nm, F in order:
            if nm == 'bottom': continue
            if nm == 'front': draw_face(pen, v, F, self.art_a, self.col, holes=holes, lw=1.0)
            elif nm == 'back': draw_face(pen, v, F, self.art_b, self.col, holes=holes, lw=1.0)
            else: draw_face(pen, v, F, None, _darken(self.col, 0.15), lw=0.8)

    def glass_quads(self, ang=0.0):
        """(frosted quad, clear quad) on the inside face of the leaf."""
        B = self.box(ang); F = B.faces()['back']
        u0, u1, Y0, Y1, Y2 = self.glass
        H = self.h * 100
        def q(Ya, Yb): return [F.pt(u0 * 100, H - Yb * 100), F.pt(u1 * 100, H - Yb * 100), F.pt(u1 * 100, H - Ya * 100), F.pt(u0 * 100, H - Ya * 100)]
        return q(Y0, Y1), q(Y1, Y2)


def ic_front_door(rules=True, eighth=False):
    return IcDoor((IC_FDOOR[0], 0.03), IC_FDOOR[1] - IC_FDOOR[0], IC_FDOOR[2], (1.0, 0.0), 1, 0.0,
                  art_a=ic_front_door_art('out', False), art_b=ic_front_door_art('in', rules, eighth), col=IC_PAL['door'], glass=IC_GLASS)


def ic_door_glass(v, D, o, name='door_glass'):
    """Live: the frosted panel (pale, lit pink from outside by his window; o['face'] level / f(t) -> (k, rise 0..1):
    the long white face sliding up behind the frost, red eyes), the clear strip (a cold sheen), o['knob_frost'] (the
    doorknob growing frost). Ordered just in front of the door leaf."""
    fq, cq = D.glass_quads(0.0)
    kp = _kfn(o.get('pink', 1.0 if o.get('truck') == 'A' else 0.0), 600)
    face = o.get('face'); kfr = _kfn(o.get('knob_frost', 0.0), 661)
    fsoft = o.get('frost_soft')         # (feather 0..1 of the panel height, panel alpha 0..1): a soft top edge (only the shots that pass it)
    def draw(pen, t):
        pf = v.poly3(fq)
        if not pf.isEmpty():
            b = pf.computeTightBounds()
            k = kp(t)
            pf0 = pf
            if fsoft:                                                   # the frost runs on up into the clear strip, faded out by the mask below
                pen.cv.saveLayer()
                pcs = v.poly3(cq)
                if not pcs.isEmpty(): pf = union(pf, pcs)
            pen.fill(pf, mix('#9aa6c4', '#f0b0d0', 0.6 * k), 175 + 40 * k)
            pen.cv.save(); pen.cv.clipPath(pf, skia.ClipOp.kIntersect, True)
            pen.texture(pf, 'grunge', 0.5, 'overlay', 0.5)
            for i in range(9):
                yy = b.top() + b.height() * (i + 0.5) / 9
                pen.line(smooth([(b.left(), yy), (b.left() + b.width() * 0.4, yy - 2), (b.right(), yy + 1)], False), 0.8, '#ffffff', 50)
            if face is not None:
                fk, rise = face(t) if callable(face) else (float(face), 1.0)
                if fk > 0.01:
                    cx = (b.left() + b.right()) / 2; w = b.width()
                    fy = b.bottom() + b.height() * 0.5 - rise * b.height() * 1.15
                    pen.fill(oval(cx, fy, w * 0.2, w * 0.42), '#f4f0ec', 220 * fk, blur=max(2.0, w * 0.05))
                    for sx in (-1, 1): pen.fill(oval(cx + sx * w * 0.08, fy - w * 0.12, w * 0.025), '#ff2a2a', 230 * fk, blur=max(1.0, w * 0.015))
            pen.cv.restore()
            if fsoft:                                                   # fade the panel's top: frost thins out towards the clear strip
                fe, fa = float(fsoft[0]), float(fsoft[1])
                hc = pf.computeTightBounds(); hc = max(1.0, b.top() - hc.top())         # the clear strip's height
                y0_, y1_ = b.top() - 0.5 * hc, b.top() + max(2.0, fe * b.height())
                mp = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
                    [skia.Point(0, y0_), skia.Point(0, y1_)],
                    [skia.Color4f(0, 0, 0, 0.0).toColor(), skia.Color4f(0, 0, 0, 0.2 * fa).toColor(), skia.Color4f(0, 0, 0, fa).toColor()],
                    [0.0, (b.top() - y0_) / (y1_ - y0_), 1.0]))
                mp.setBlendMode(skia.BlendMode.kDstIn)
                bb = pf.computeTightBounds()
                pen.cv.drawRect(skia.Rect.MakeLTRB(bb.left() - 4, bb.top() - 4, bb.right() + 4, bb.bottom() + 4), mp)
                pen.cv.restore()
            pf = pf0
            pen.glow((b.left() + b.right()) / 2, (b.top() + b.bottom()) / 2, b.width() * 0.9, IC_PINK, 40 * kp(t))
        pc = v.poly3(cq)
        if not pc.isEmpty():
            b = pc.computeTightBounds()
            pen.linear(pc, b.left(), b.top(), b.right(), b.bottom(), [(0, '#ffffff', 0), (0.45, '#c8d8ff', 40), (0.55, '#ffffff', 0)])
        k = kfr(t)
        if k > 0.01:
            P = D.knob(0.0, 'b')
            if v.d(P[0], P[2]) > 0.2:
                x, y = v.p(*P); s = v.s(P[0], P[2])
                rng = np.random.default_rng(7)
                pen.fill(oval(x, y, 0.045 * s * (0.6 + 0.4 * k)), '#e8f2ff', 200 * k)
                for i in range(int(14 * k)):
                    a = rng.uniform(0, 2 * math.pi); r = 0.05 * s * k * rng.uniform(0.6, 1.4)
                    pen.seg((x, y), (x + math.cos(a) * r, y + math.sin(a) * r), max(0.6, 0.004 * s), '#ffffff', 200)
    lay = Layer(max(0.3, v.d(fq[0][0], fq[0][2])), draw, name, blur=None)
    lay.order = min(v.d(p_[0], p_[2]) for p_ in fq) - 0.03
    return lay


def ic_hatch(pen, v, k=0.0, ajar=False):
    """The attic hatch in the hall ceiling: k 0 closed (a flush panel, a pull cord) .. 1 dropped open (the panel hangs
    from its far hinge; the dark attic above, rafters). ajar=True (the rattle, L292 only): the CLOSED panel tipped down
    95*k degrees on its hinge over a dark sliver of the hole, never the open shaft."""
    x0, x1, y0, y1 = IC_HATCH
    C = IC_CEIL
    if ajar and k > 0.0:
        L = y1 - y0
        a = math.radians(95 * k)

        def hp(x, s, dz=0.0):                                                # s: distance from the hinge (y1) along the panel
            return (x, C - 0.005 - dz - math.sin(a) * s, y1 - math.cos(a) * s)
        hole = v.poly3([(x0, C - 0.004, y0), (x1, C - 0.004, y0), (x1, C - 0.004, y1), (x0, C - 0.004, y1)])
        if not hole.isEmpty(): pen.fill(hole, '#0e0c0c')
        path = v.poly3([hp(x1, 0.0), hp(x0, 0.0), hp(x0, L), hp(x1, L)])
        if not path.isEmpty():
            pen.fill(path, lit('#ece6da', (x0, C, y0), (0, -1, 0))); pen.line(path, 1.6, '#b8b0a0')
            pen.line(v.poly3([hp(x1 - 0.05, 0.05, 0.001), hp(x0 + 0.05, 0.05, 0.001), hp(x0 + 0.05, L - 0.05, 0.001), hp(x1 - 0.05, L - 0.05, 0.001)]), 0.8, '#a8a090')
        A = hp(0.5 * (x0 + x1), L - 0.08, 0.005)
        if v.d(A[0], A[2]) > 0.3:
            pen.seg(v.p(*A), v.p(A[0], A[1] - 0.35, A[2]), 1.0, '#e8e0d0')
            x, y = v.p(A[0], A[1] - 0.37, A[2]); pen.fill(oval(x, y, max(1.5, 0.015 * v.s(A[0], A[2]))), '#c8b070')
        return
    if k > 0.02:
        D = 0.6
        for (q, n) in (([(x0, C, y0), (x1, C, y0), (x1, C + D, y0), (x0, C + D, y0)], (0, 0, 1)),
                       ([(x1, C, y1), (x0, C, y1), (x0, C + D, y1), (x1, C + D, y1)], (0, 0, -1)),
                       ([(x0, C, y1), (x0, C, y0), (x0, C + D, y0), (x0, C + D, y1)], (1, 0, 0)),
                       ([(x1, C, y0), (x1, C, y1), (x1, C + D, y1), (x1, C + D, y0)], (-1, 0, 0))):
            path = v.poly3(q)
            if not path.isEmpty(): pen.fill(path, '#0e0c0c'); pen.line(path, 0.8)
        top = v.poly3([(x0, C + D, y0), (x1, C + D, y0), (x1, C + D, y1), (x0, C + D, y1)])
        if not top.isEmpty(): pen.fill(top, '#050405')
        for xx in (x0 + 0.2, x1 - 0.2):
            path = v.poly3([(xx - 0.03, C + D, y0), (xx + 0.03, C + D, y0), (xx + 0.03, C + D, y1), (xx - 0.03, C + D, y1)])
            if not path.isEmpty(): pen.fill(path, '#1a1410')
        a = math.radians(95 * k)                                              # the panel swings down on its y1 hinge
        L = y1 - y0
        q = [(x0 + 0.02, C - 0.01, y1), (x1 - 0.02, C - 0.01, y1), (x1 - 0.02, C - math.sin(a) * L, y1 - math.cos(a) * L), (x0 + 0.02, C - math.sin(a) * L, y1 - math.cos(a) * L)]
        path = v.poly3(q)
        if not path.isEmpty():
            pen.fill(path, lit('#e4ddd0', (x0, C - 0.3, y1), (0, -0.3, -1))); pen.line(path, 1.0)
        A = (0.5 * (x0 + x1), C - math.sin(a) * L * 0.9, y1 - math.cos(a) * L * 0.9)
        if v.d(A[0], A[2]) > 0.3: pen.seg(v.p(*A), v.p(A[0], A[1] - 0.3, A[2]), 1.2, '#2a2a2a')
    else:
        q = [(x0, C - 0.005, y0), (x1, C - 0.005, y0), (x1, C - 0.005, y1), (x0, C - 0.005, y1)]
        path = v.poly3(q)
        if not path.isEmpty():
            pen.fill(path, lit('#ece6da', (x0, C, y0), (0, -1, 0))); pen.line(path, 1.6, '#b8b0a0')
            qi = [(x0 + 0.05, C - 0.006, y0 + 0.05), (x1 - 0.05, C - 0.006, y0 + 0.05), (x1 - 0.05, C - 0.006, y1 - 0.05), (x0 + 0.05, C - 0.006, y1 - 0.05)]
            pen.line(v.poly3(qi), 0.8, '#a8a090')
        A = (0.5 * (x0 + x1), C - 0.01, y0 + 0.08)
        if v.d(A[0], A[2]) > 0.3:
            pen.seg(v.p(*A), v.p(A[0], A[1] - 0.35, A[2]), 1.0, '#e8e0d0')
            x, y = v.p(A[0], A[1] - 0.37, A[2]); pen.fill(oval(x, y, max(1.5, 0.015 * v.s(A[0], A[2]))), '#c8b070')


def _ic_hatch_ceil_rects():
    x0, x1, y0, y1 = IC_HALL
    hx0, hx1, hy0, hy1 = IC_HATCH
    return [(x0, x1, y0, hy0), (x0, x1, hy1, y1), (x0, hx0, hy0, hy1), (hx1, x1, hy0, hy1)]


def _ic_house_o(kw, defaults):
    o = dict(defaults); o.update(kw)
    o['no_veil'] = True
    if o.get('blackout'):
        for k_ in ('lamp', 'ceil', 'tv', 'hall', 'kitchen_light', 'bath_light'): o[k_] = 0.0
    return o


# ---------------------------------------------------------------------------------------------- the living room
def _ic_liv_cfg(o):
    gap = _static(o.get('curtains', 0.04), 0.04)
    def lights(o):
        amb = _ic_light(o)
        win = Lamp(kind='win', c=IC_MOON if o.get('tod') != 'morning' else '#ffe0b0', k=(0.3 + 0.7 * gap) if o.get('tod') != 'morning' else 1.4, soft=10.0,
                   panes=_panes_y(IC_PWIN[0], IC_PWIN[1], IC_PWIN[2], IC_PWIN[3], 0.0), d=_norm3((-0.2, -0.45, 1.0)))
        steady = [win]
        var = [('lamp', [Lamp(IC_FLAMP[0], 1.45, IC_FLAMP[1], 5.0, IC_WARM, 1.5, (1.0, 0.6, 0.35), fall=1.4)], _kfn(o.get('lamp', 0.0), 611)),
               ('ceil', [Lamp(2.6, 2.42, 2.8, 6.0, '#ffe8c8', 1.2, (1.0, 0.5, 0.2), fall=1.3)], _kfn(o.get('ceil', 0.0), 612)),
               ('tv', [Lamp(IC_TV[0], 0.95, IC_TV[1] - 0.3, 4.2, '#8aa8ff', 1.0, fall=1.5)], _kfn(o.get('tv', 0.0), 613)),
               ('hall', [Lamp(-2.1, 2.2, 3.6, 3.4, IC_WARM, 0.8, fall=1.4)], _kfn(o.get('hall', 0.0), 614))]
        var += _ic_common_var(o, [[(IC_PWIN[0], IC_PWIN[3], 0.0), (IC_PWIN[1], IC_PWIN[3], 0.0), (IC_PWIN[1], IC_PWIN[2], 0.0), (IC_PWIN[0], IC_PWIN[2], 0.0)]]
                              if o.get('truck') == 'A' else None, (-0.3, -0.25, 1.0), _panes_y(IC_PWIN[0], IC_PWIN[1], IC_PWIN[2], IC_PWIN[3], 0.0), 615)
        return amb, steady, var

    def back(p_, W, H):
        _bu_photo(p_, (0.3 + 1.4) * 100, H - 175, 44, 34, 'kids')
        _light_switch(p_, (0.15 + 1.4) * 100, H - 120)
        _wall_clock(p_, (5.4 + 1.4) * 100, H - 200, 13, 11, 2)
    def east(p_, W, H):
        _bu_photo(p_, (5.6 - 2.0) * 100, H - 170, 40, 30, 'grandpa')
        _ic_thermostat(p_, (5.6 - 4.6) * 100, H - 150, o.get('thermo', '68'))
    def bath_back(p_, W, H):
        _bu_photo(p_, 90, H - 170, 36, 44, 'school')
    runs = [_run((6.4, 0.0), (0.4, 0.0), wins=[(IC_PWIN[0], 0.0, IC_PWIN[1], 0.0, IC_PWIN[2], IC_PWIN[3], (3, 2))]),
            _run((0.4, 0.0), (0.4, 2.2)),
            _run((0.4, 2.2), (-1.4, 2.2), art=bath_back),
            _run((-1.4, 2.2), (-1.4, 5.6), holes=[(-1.4, IC_LOPEN[0], -1.4, IC_LOPEN[1], 0.0, IC_LOPEN[2])]),
            _run((-1.4, 5.6), (6.4, 5.6), art=back),
            _run((6.4, 5.6), (6.4, 0.0), art=east)]
    rug = _bu_rug_art(IC_LIV_A[0], IC_LIV_A[3], 3.4, 3.4, 1.6, 1.1, ('#3a4a6a', '#9a7a52', '#6e3a2c', '#c8b898', '#2a3a5a', '#5a4a3a', '#8a6a4a'))

    def pieces(o):
        parts = couch_parts(IC_COUCH, IC_PAL['couch'], IC_PAL['couch_d'], afghan=False, blanket=False)
        seats = couch_seats(IC_COUCH)
        P = [Piece('couch', (IC_COUCH.cx, 0.4, IC_COUCH.cy), lambda pen, v: (draw_parts(pen, v, parts), _ic_couch_extras(pen, v, o)),
                   occupant=[(x, y) for (n, x, y) in seats], front=parts, block=IC_COUCH.footprint())]
        ap = dr_armchair_parts(IC_ARM, '#8a5a3a', '#5a3a24', doily=False)
        aseat = IC_ARM.at(0, -IC_ARM.d / 2 + 0.42, 0)
        P.append(Piece('armchair', (IC_ARM.cx, 0.4, IC_ARM.cy), lambda pen, v: draw_parts(pen, v, ap), occupant=[(aseat[0], aseat[2])], front=ap, block=IC_ARM.footprint()))
        P.append(Piece('side_table', (IC_SIDE.cx, 0.3, IC_SIDE.cy), lambda pen, v: (draw_parts(pen, v, table_parts(IC_SIDE, '#6a4428', apron=0.05)),
                                                                                    (ic_radio(pen, v, IC_SIDE.cx + 0.05, IC_SIDE.Y1, IC_SIDE.cy, -30.0, 0.0) if o.get('radio', 'table') == 'table' else None)),
                       block=IC_SIDE.footprint()))
        P.append(Piece('tv', (IC_TV[0], 0.6, IC_TV[1]), lambda pen, v: _ic_tv(pen, v), block=IC_TVSTAND.footprint()))
        lk = _static(o.get('lamp', 0.0))
        P.append(Piece('floor_lamp', (IC_FLAMP[0], 1.0, IC_FLAMP[1]), lambda pen, v: lamp_floor(pen, v, IC_FLAMP[0], IC_FLAMP[1], 0.0, 1.55, lk), block=_circ(IC_FLAMP[0], IC_FLAMP[1], 0.18)))
        P.append(Piece('shelf', (IC_SHELF.cx, 1.0, IC_SHELF.cy), lambda pen, v: bookcase(pen, v, IC_SHELF), block=IC_SHELF.footprint()))
        cg = o.get('curtains', 0.04)
        if not callable(cg):
            P.append(Piece('curtains', ((IC_PWIN[0] + IC_PWIN[1]) / 2, 1.4, 0.14),
                           lambda pen, v: curtain_pair(pen, v, (6.4, 0.0), (0.4, 0.0), 6.4 - IC_PWIN[1], 6.4 - IC_PWIN[0], 2.3, 2.25, 0.0, _static(cg, 0.04), IC_PAL['curt'], sheer=False)))
        if o.get('cone') == 'floor':
            P.append(Piece('cone', (3.2, 0.1, 2.6), lambda pen, v: ic_cone(pen, v, 3.2, 0.0, 2.6, 'shards')))
        return P

    def glows(v, o):
        G = []
        kl = _kfn(o.get('lamp', 0.0), 611)
        def lampg(pen, t):
            k = kl(t)
            if k > 0.01 and v.d(*IC_FLAMP) > 0.3:
                x, y = v.p(IC_FLAMP[0], 1.42, IC_FLAMP[1]); s = v.s(*IC_FLAMP)
                pen.glow(x, y, 0.8 * s, '#ffd090', 90 * k)
        G.append(('floor_lamp_glow', (IC_FLAMP[0], 1.4, IC_FLAMP[1]), lampg))
        kt = _kfn(o.get('tv', 0.0), 613); sk = o.get('skull', 0.0); ksk = _kfn(sk, 616)
        G.append(('tv_glow', (IC_TV[0], 0.9, IC_TV[1]), lambda pen, t: ic_tv_screen(pen, v, o, kt(t), ksk(t), t)))
        kp = _kfn(o.get('pink', 1.0 if o.get('truck') == 'A' else 0.0), 615)
        kb = _kfn(o.get('beacon', 0.0), 616)
        def curt(pen, t):                                                     # the curtains glow pink (his window) / orange (the beacon)
            k1, k2 = kp(t), kb(t)
            if k1 <= 0.01 and k2 <= 0.01: return
            q = [(IC_PWIN[0] - 0.25, 2.3, 0.1), (IC_PWIN[1] + 0.25, 2.3, 0.1), (IC_PWIN[1] + 0.25, 0.05, 0.1), (IC_PWIN[0] - 0.25, 0.05, 0.1)]
            if v.d(3.4, 0.1) < 0.3 or not v.visible(q[0], (0, 0, 1)): return
            path = v.poly3(q)
            if path.isEmpty(): return
            b = path.computeTightBounds(); cx = (b.left() + b.right()) / 2
            g = 1.0 - _static(o.get('curtains', 0.04), 0.04)
            for (k, c) in ((k1, IC_PINK), (k2, IC_ORANGE)):
                if k > 0.01:
                    pen.radial(path, cx, b.top() + b.height() * 0.45, b.width() * 0.7, [(0, c, 90 * k * g), (1, c, 15 * k * g)], sy=1.2)
            gx0, gx1 = v.p(3.4 - 0.6 * _static(o.get('curtains', 0.04), 0.04) - 0.012, 1.4, 0.1)[0], v.p(3.4 + 0.6 * _static(o.get('curtains', 0.04), 0.04) + 0.012, 1.4, 0.1)[0]
            pen.fill(rect(min(gx0, gx1), b.top(), abs(gx1 - gx0), b.height()), IC_PINK, 120 * k1)
        G.append(('curtains_glow', (3.4, 1.3, 0.12), curt))
        return G

    def spots(v, o):
        S = {}
        for (n, x, y) in couch_seats(IC_COUCH):
            S['couch_' + n] = _mk_spot(v, 'couch_' + n, x, y, 0.0, 'seat', 'the couch, %s seat (facing the TV, +y; the window behind)' % n, face=(0, 1), seat_Y=COUCH_SEAT)
        S['couch_front'] = _mk_spot(v, 'couch_front', 3.4, 2.6, 0.0, 'stand', 'standing in front of the couch, facing it', face=(0, -1))
        S['couch_behind'] = _mk_spot(v, 'couch_behind', 3.4, 0.75, 0.0, 'stand', 'between the couch back and the window, facing the curtains', face=(0, -1))
        S['curtain_crack'] = _mk_spot(v, 'curtain_crack', 3.4, 0.12, 1.3, 'point', "Lina's crack in the curtains (eye height)")
        S['curtain_l'] = _mk_spot(v, 'curtain_l', IC_PWIN[1] - 0.3, 0.2, 1.4, 'point', 'the east curtain edge (a hand yanks it shut)')
        S['side_table'] = _mk_spot(v, 'side_table', IC_SIDE.cx, IC_SIDE.cy, IC_SIDE.Y1, 'surface', "the side table top (Dad's radio)")
        S['radio'] = _mk_spot(v, 'radio', IC_SIDE.cx + 0.05, IC_SIDE.cy, IC_SIDE.Y1 + 0.12, 'point', "Dad's radio on the side table")
        S['tv_screen'] = _mk_spot(v, 'tv_screen', IC_TV[0], IC_TV[1] - 0.04, IC_TV[4] + IC_TV[3] / 2, 'point', 'the TV screen centre (black: it reflects)')
        aseat = IC_ARM.at(0, -IC_ARM.d / 2 + 0.42, 0)
        S['armchair'] = _mk_spot(v, 'armchair', aseat[0], aseat[2], 0.0, 'seat', 'the armchair (facing west)', face=(-1, 0), seat_Y=0.46)
        S['room_mid'] = _mk_spot(v, 'room_mid', 2.4, 3.4, 0.0, 'stand', 'the middle of the room')
        S['opening'] = _mk_spot(v, 'opening', -1.05, 3.6, 0.0, 'stand', 'at the opening to the hall (facing it, -x)', face=(-1, 0))
        S['floor_cone'] = _mk_spot(v, 'floor_cone', 3.2, 2.6, 0.0, 'surface', 'where the cone hits the floor and shatters')
        return S

    return dict(name='living', R=(-1.4, 6.4, 0.0, 5.6), poly=IC_LIV_POLY, H=IC_CEIL, floors=[IC_LIV_A, IC_LIV_B],
                floor=dict(base=IC_PAL['floor'], kind='boards', ink='#4a2e1a', seed=11, art=rug), runs=runs,
                walls=dict(paper=IC_PAL['liv_paper'], ink=IC_PAL['liv_ink'], kind='stripe', wains=0.0, seed=17, scale=0.9, pa=60, rail=None),
                ceil=dict(c='#ece6da', rects=[IC_LIV_A, IC_LIV_B]), lights=lights, pieces=pieces, glows=glows, spots=spots)


def _ic_thermostat(p_, x, y, temp='68'):
    p_.fill(rrect(x - 7, y - 9, 14, 18, 2), '#ece8e0'); p_.line(rrect(x - 7, y - 9, 14, 18, 2), 0.6)
    p_.fill(oval(x, y - 1, 4.5), '#c8c0b0'); p_.line(oval(x, y - 1, 4.5), 0.5)
    btext(p_, str(temp), x, y + 7, 'sans_b', 3.2, '#2a2a2a', 220, 'center')


def _ic_couch_extras(pen, v, o):
    """The one-blanket nest (o['blanket'] True: a quilt heaped over the seats), Lina's pillow."""
    if o.get('blanket'):
        B = IC_COUCH
        q = [B.at(-B.w / 2 + 0.25, 0.25, COUCH_SEAT + 0.12), B.at(B.w / 2 - 0.25, 0.25, COUCH_SEAT + 0.12), B.at(B.w / 2 - 0.2, B.d / 2 + 0.02, COUCH_SEAT - 0.05),
             B.at(B.w / 2 - 0.2, B.d / 2 + 0.03, 0.12), B.at(-B.w / 2 + 0.2, B.d / 2 + 0.03, 0.12), B.at(-B.w / 2 + 0.2, B.d / 2 + 0.02, COUCH_SEAT - 0.05)]
        path = v.poly3(q)
        if not path.isEmpty():
            pen.fill(path, lit('#9a4a5a', q[3], (0, 0, 1))); pen.texture(path, 'fabric', 0.5, 'overlay', 0.8)
            b = path.computeTightBounds()
            pen.cv.save(); pen.cv.clipPath(path, skia.ClipOp.kIntersect, True)
            for k in range(6):
                xx = b.left() + b.width() * (k + 0.5) / 6
                pen.line(rect(xx - 1, b.top(), 2, b.height()), 1.0, '#e8d8b0', 90)
            pen.cv.restore(); pen.line(path, 1.0)
    P = IC_COUCH.at(-IC_COUCH.w / 2 + 0.3, -0.1, COUCH_SEAT + 0.2)
    if v.d(P[0], P[2]) > 0.3:
        x, y = v.p(*P); s = v.s(P[0], P[2])
        pen.fill(rrect(x - 0.2 * s, y - 0.13 * s, 0.4 * s, 0.26 * s, 0.08 * s), lit('#f4c8d8', P, (0, 0, 1))); pen.line(rrect(x - 0.2 * s, y - 0.13 * s, 0.4 * s, 0.26 * s, 0.08 * s), 1.0)


def _ic_tv_quad():
    x, y, w, h, Yb = IC_TV
    return [(x + w / 2, Yb + h, y - 0.04), (x - w / 2, Yb + h, y - 0.04), (x - w / 2, Yb, y - 0.04), (x + w / 2, Yb, y - 0.04)]


def _ic_tv(pen, v):
    """The TV stand and the flat TV on it (its screen is the live layer ic_tv_screen)."""
    draw_box(pen, v, IC_TVSTAND, {'all': '#3a2a20', 'top': '#4a3628', 'front': dict(fill='#3a2a20', art=lambda p_, W, H: (p_.line(rect(6, 8, W / 2 - 9, H - 14), 1.0, '#000000', 120),
                                                                                                                       p_.line(rect(W / 2 + 3, 8, W / 2 - 9, H - 14), 1.0, '#000000', 120)))})
    x, y, w, h, Yb = IC_TV
    B = Box(x, y + 0.02, w + 0.04, 0.05, Yb - 0.02, Yb + h + 0.02, 0)
    draw_box(pen, v, B, {'all': '#141418'})
    foot = Box(x, y + 0.02, 0.3, 0.2, IC_TVSTAND.Y1, Yb, 0)
    draw_box(pen, v, foot, {'all': '#1a1a1e'})


def ic_tv_screen(pen, v, o, k=0.0, skull=0.0, t=0.0):
    """The TV screen: on (k > 0: a cold blue glow) or BLACK and reflecting the room: the window behind the couch
    (pale, the curtains either side), the couch back, and in Lina's crack (skull > 0) a long white skull, red eyes."""
    q = _ic_tv_quad()
    if v.d(IC_TV[0], IC_TV[1]) < 0.3 or not v.visible(q[0], (0, 0, -1)): return
    path = v.poly3(q)
    if path.isEmpty(): return
    b = path.computeTightBounds()
    pen.fill(path, '#06080c')
    if k > 0.01:
        pen.fill(path, '#9ab8ff', 170 * k); pen.glow((b.left() + b.right()) / 2, (b.top() + b.bottom()) / 2, b.width() * 1.3, '#8aa8ff', 70 * k)
        return
    W, H = b.width(), b.height()
    pen.cv.save(); pen.cv.clipPath(path, skia.ClipOp.kIntersect, True)
    # the reflection (mirrored room): the window in the upper middle, curtains, the couch across the lower third
    wx0, wx1 = b.left() + W * 0.28, b.left() + W * 0.72
    wy0, wy1 = b.top() + H * 0.12, b.top() + H * 0.62
    pk = 1.0 if o.get('truck') == 'A' and not o.get('curtains_shut') else 0.0
    pen.fill(rect(wx0, wy0, wx1 - wx0, wy1 - wy0), mix('#2a3448', '#6a3a5a', 0.6 * pk), 150)
    for (a0, a1) in ((wx0 - W * 0.05, b.left() + W * 0.5 - W * 0.01), (b.left() + W * 0.5 + W * 0.01, wx1 + W * 0.05)):
        pen.fill(rect(a0, wy0 - H * 0.04, a1 - a0, wy1 - wy0 + H * 0.08), '#1a1014', 200)
    cxk = b.left() + W * 0.5
    crack = _static(o.get('curtains', 0.04), 0.04)
    if crack > 0.005:
        pen.fill(rect(cxk - W * 0.022, wy0, W * 0.044, wy1 - wy0), mix('#8aa0d0', IC_PINK, pk), 150)
    pen.fill(rrect(b.left() + W * 0.1, b.top() + H * 0.6, W * 0.8, H * 0.5, H * 0.12), '#0e1014', 230)
    if o.get('us', True):                                                     # "In the black TV screen: us."
        for (fx, sc) in ((0.42, 1.0), (0.6, 0.78)):
            hx, hy = b.left() + W * fx, b.top() + H * (0.6 - 0.08 * sc)
            sil = union(oval(hx, hy, W * 0.045 * sc, H * 0.1 * sc), rrect(hx - W * 0.09 * sc, hy + H * 0.07 * sc, W * 0.18 * sc, H * 0.4, W * 0.05 * sc))
            pen.fill(sil, '#1c2230', 235); pen.line(sil, 1.0, mix('#4a5a80', IC_PINK, 0.5 * pk), 120)
    if skull > 0.01:                                                           # glimpse 2: in the crack, a long white skull
        sx, sy = cxk, wy0 + (wy1 - wy0) * 0.45
        sk = poly([(sx - W * 0.02, sy - H * 0.13), (sx + W * 0.02, sy - H * 0.13), (sx + W * 0.016, sy + H * 0.12), (sx, sy + H * 0.2), (sx - W * 0.016, sy + H * 0.12)])
        pen.fill(sk, '#ece8e0', 230 * skull, blur=1.5)
        for dx in (-1, 1): pen.fill(oval(sx + dx * W * 0.008, sy - H * 0.06, W * 0.005), '#ff2020', 250 * skull)
        pen.glow(sx, sy - H * 0.06, W * 0.03, '#ff2020', 90 * skull)
    pen.linear(path, b.left(), b.top(), b.right(), b.bottom(), [(0, '#ffffff', 0), (0.35, '#ffffff', 22), (0.42, '#ffffff', 0)])
    pen.cv.restore()
    pen.line(path, 1.0, '#000000')


# ---------------------------------------------------------------------------------------------- the hall
def _ic_hall_cfg(o):
    def lights(o):
        amb = _ic_light(o)
        steady = []
        var = [('hall', [Lamp(-2.1, 2.4, 2.2, 4.0, '#ffe8c8', 1.2, (1.0, 0.5, 0.2), fall=1.3), Lamp(-2.1, 2.4, 6.5, 4.0, '#ffe8c8', 1.0, (1.0, 0.5, 0.2), fall=1.3)],
                _kfn(o.get('hall', 0.0), 621)),
               ('liv', [Lamp(-0.6, 1.4, 3.6, 3.2, IC_WARM, 0.7, fall=1.4)], _kfn(o.get('lamp', 0.0), 622))]
        u0, u1, Y0, Y1, Y2 = IC_GLASS
        gl = [[(IC_FDOOR[0] + u0, Y2, 0.0), (IC_FDOOR[0] + u1, Y2, 0.0), (IC_FDOOR[0] + u1, Y0, 0.0), (IC_FDOOR[0] + u0, Y0, 0.0)]]
        var += _ic_common_var(o, gl if o.get('truck') == 'A' else None, (0.25, -0.2, 1.0), gl, 625)
        steady.append(Lamp(kind='win', c=IC_MOON, k=0.4, soft=12.0, panes=gl, d=_norm3((0.1, -0.5, 1.0))))
        return amb, steady, var

    def west(p_, W, H):                                                       # run (x0, y0) -> (x0, y1): u = y
        _ic_coats_art(p_, IC_COATS[0] * 0 + 45, H)
        _ic_wall_door(p_, (6.6) * 100, (7.45) * 100, H, 'LINA', True)
    def east(p_, W, H):                                                       # run (x1, y1) -> (x1, y0): u = 9 - y
        _light_switch(p_, (9.0 - 2.15) * 100, H - 120)
        _ic_wall_door(p_, (9.0 - 7.1) * 100, (9.0 - 6.25) * 100, H, None, False)
        _bu_photo(p_, (9.0 - 5.0) * 100, H - 170, 38, 30, 'kids')
    def back(p_, W, H):
        _ic_wall_door(p_, 25, 115, H, None, False)
    def front(p_, W, H):
        pass
    holes = {'front': [(IC_FDOOR[0], 0.0, IC_FDOOR[1], 0.0, 0.0, IC_FDOOR[2])],
             'east': [(-1.4, IC_BDOOR[0], -1.4, IC_BDOOR[1], 0.0, IC_BDOOR[2]), (-1.4, IC_LOPEN[0], -1.4, IC_LOPEN[1], 0.0, IC_LOPEN[2])],
             'west': [(-2.8, IC_KDOOR[0], -2.8, IC_KDOOR[1], 0.0, IC_KDOOR[2])]}
    runs = _rect_runs(IC_HALL, holes, {}, {'west': west, 'east': east, 'back': back})

    def pieces(o):
        D = ic_front_door(o.get('rules', True), o.get('eighth', False))
        P = []
        dv = o.get('door', 0.0)
        if not callable(dv):
            P.append(Piece('front_door', ((IC_FDOOR[0] + IC_FDOOR[1]) / 2, 1.0, 0.05), lambda pen, v: D.draw(pen, v, _static(dv))))
        BD = _ic_bath_door()
        bv = o.get('bath_door', 85.0)
        if not callable(bv):
            P.append(Piece('bath_door', (-1.4, 1.0, 1.35), lambda pen, v: BD.draw(pen, v, _static(bv, 85.0))))
        hk = o.get('hatch', 0.0)
        if not callable(hk):
            P.append(Piece('hatch', (-2.1, IC_CEIL, 5.9), lambda pen, v: ic_hatch(pen, v, _static(hk))))
        P.append(Piece('runner', (-2.1, 0.01, 4.0), lambda pen, v: _ic_runner(pen, v)))
        P.append(Piece('bench', (-2.6, 0.3, 1.4), lambda pen, v: draw_box(pen, v, Box(-2.6, 1.45, 0.34, 0.9, 0.0, 0.45, 90), {'top': '#7a5a3a', 'all': '#5a3a24'}),
                       block=_r4p((-2.8, -2.45, 1.0, 1.9))))
        if o.get('boots_by_door', True):
            P.append(Piece('boots', (-2.6, 0.1, 0.5), lambda pen, v: _ic_boots_mat(pen, v)))
        return P

    def glows(v, o):
        G = []
        if o.get('blackout') is not True and _static(o.get('hall', 0.0)) > 0.0:
            kh = _kfn(o.get('hall', 0.0), 621)
            def cg(pen, t):
                for yy in (2.2, 6.5):
                    if v.d(-2.1, yy) > 0.3:
                        x, y = v.p(-2.1, IC_CEIL - 0.05, yy); s = v.s(-2.1, yy)
                        pen.glow(x, y, 0.4 * s, '#fff0d0', 120 * kh(t)); pen.fill(oval(x, y, 0.16 * s, 0.05 * s), '#fff8e8', 220 * kh(t))
            G.append(('ceil_glow', (-2.1, IC_CEIL, 4.0), cg))
        return G

    def spots(v, o):
        S = {}
        dx = (IC_FDOOR[0] + IC_FDOOR[1]) / 2
        S['door_in'] = _mk_spot(v, 'door_in', dx, 0.45, 0.0, 'stand', 'inside at the front door, facing it (-y)', face=(0, -1))
        S['door_glass_in'] = _mk_spot(v, 'door_glass_in', dx, 0.02, (IC_GLASS[3] + IC_GLASS[4]) / 2, 'point', 'the clear strip (inside): "Through the clear strip of glass"')
        S['door_frost_in'] = _mk_spot(v, 'door_frost_in', dx, 0.02, (IC_GLASS[2] + IC_GLASS[3]) / 2, 'point', 'the frosted panel (inside): the face slides up it')
        S['lock'] = _mk_spot(v, 'lock', IC_FDOOR[1] - 0.09, 0.06, 1.17, 'point', 'the deadbolt (Lina scrambles for it)')
        S['knob_in'] = _mk_spot(v, 'knob_in', IC_FDOOR[1] - 0.09, 0.06, 0.98, 'point', 'the doorknob inside (it grows frost)')
        S['rules'] = _mk_spot(v, 'rules', dx, 0.05, IC_GLASS[2] - 0.17, 'point', 'the rules taped inside the door (signed W.K.)')
        S['hall_front'] = _mk_spot(v, 'hall_front', -2.1, 1.3, 0.0, 'stand', 'in the hall near the door', face=(0, -1))
        S['hall_mid'] = _mk_spot(v, 'hall_mid', -2.1, 3.4, 0.0, 'stand', 'the middle of the hall')
        S['under_hatch'] = _mk_spot(v, 'under_hatch', -2.1, 5.2, 0.0, 'stand', 'under the attic hatch (the leg reaches between them here)', face=(0, 1))
        S['hatch'] = _mk_spot(v, 'hatch', -2.1, 5.9, IC_CEIL, 'point', 'the attic hatch opening (his face lowers upside down from here)')
        S['hatch_face'] = _mk_spot(v, 'hatch_face', -2.1, 5.9, IC_CEIL - 0.45, 'point', 'his upside-down face below the open hatch')
        S['bath_door_hall'] = _mk_spot(v, 'bath_door_hall', -1.8, (IC_BDOOR[0] + IC_BDOOR[1]) / 2, 0.0, 'stand', 'in the hall at the bathroom door, facing it (+x)', face=(1, 0))
        S['coats'] = _mk_spot(v, 'coats', -2.62, 0.85, 0.0, 'stand', 'at the coat hooks (layers on)', face=(-1, 0))
        S['bench'] = _mk_spot(v, 'bench', -2.6, 1.45, 0.0, 'seat', 'the hall bench (boots on)', face=(1, 0), seat_Y=0.45)
        S['kitchen_door'] = _mk_spot(v, 'kitchen_door', -2.5, 2.95, 0.0, 'stand', 'at the kitchen doorway (facing it, -x)', face=(-1, 0))
        return S

    return dict(name='hall', R=IC_HALL, H=IC_CEIL, floor=dict(base='#8a5a34', kind='boards', ink='#4a2e1a', seed=21), runs=runs,
                walls=dict(paper=IC_PAL['hall_paper'], ink=IC_PAL['hall_ink'], kind='ditsy', wains=0.9, wcol='#efe8da', seed=23, scale=0.9, pa=60, rail=0.9),
                ceil=dict(c='#ece6da', rects=_ic_hatch_ceil_rects()), lights=lights, pieces=pieces, glows=glows, spots=spots)


def _ic_wall_door(p_, u0, u1, H, name=None, kid=False):
    """A closed bedroom door painted on a wall run (cm art frame)."""
    yt = H - 203
    p_.fill(rect(u0 - 8, yt - 8, u1 - u0 + 16, 211), '#efe8da'); p_.line(rect(u0 - 8, yt - 8, u1 - u0 + 16, 211), 0.8)
    p_.fill(rect(u0, yt, u1 - u0, 203), '#e8e2d4'); p_.line(rect(u0, yt, u1 - u0, 203), 0.8)
    for (y0, h) in ((yt + 12, 80), (yt + 108, 82)):
        p_.line(rect(u0 + 10, y0, u1 - u0 - 20, h), 0.8, '#a8a090')
    p_.fill(oval(u1 - 9, H - 98, 3), '#c8b070')
    if name:
        p_.fill(rrect((u0 + u1) / 2 - 22, yt + 30, 44, 16, 4), '#f8c8d8'); btext(p_, name, (u0 + u1) / 2, yt + 42, 'kid', 11, '#6a2a4a', 240, 'center')


def _ic_coats_art(p_, x, H):
    """Coat hooks with coats (the hall's west wall, near the front door)."""
    p_.fill(rect(20, H - 182, 100, 10), '#6a4a2a')
    for i, (c, w) in enumerate((('#1e2a4a', 36), ('#d8a820', 30), ('#7a2a2a', 34))):
        cx = 36 + i * 32
        p_.fill(oval(cx, H - 176, 2), '#c8b070')
        p_.fill(poly([(cx - 8, H - 174), (cx + 8, H - 174), (cx + w / 2, H - 100), (cx - w / 2, H - 100)]), c); p_.line(poly([(cx - 8, H - 174), (cx + 8, H - 174), (cx + w / 2, H - 100), (cx - w / 2, H - 100)]), 0.6)


def _ic_runner(pen, v):
    q = [(-2.45, 0.004, 0.6), (-1.75, 0.004, 0.6), (-1.75, 0.004, 7.6), (-2.45, 0.004, 7.6)]
    path = v.poly3(q)
    if not path.isEmpty():
        pen.fill(path, lit('#6a2e32', (-2.1, 0, 3), (0, 1, 0)))
        pen.line(path, 1.0, '#c8a868', 160)


def _ic_boots_mat(pen, v):
    q = [(-2.5, 0.006, 0.15), (-1.7, 0.006, 0.15), (-1.7, 0.006, 0.7), (-2.5, 0.006, 0.7)]
    path = v.poly3(q)
    if not path.isEmpty(): pen.fill(path, lit('#3a3a3e', (-2.1, 0, 0.4), (0, 1, 0)))
    for (x, c) in ((-2.4, '#2a3a5a'), (-2.28, '#2a3a5a'), (-1.95, '#c8a020')):
        draw_box(pen, v, Box(x, 0.45, 0.1, 0.26, 0.0, 0.28 if c != '#c8a020' else 0.2, 0), {'all': c, 'top': _darken(c, 0.3)}, lw=0.6)


def _ic_bath_door():
    return dr_panel_door((-1.4, IC_BDOOR[0]), IC_BDOOR[1] - IC_BDOOR[0], (0.0, 1.0), -1, 'right', '#efe9dc', 'six')


# ---------------------------------------------------------------------------------------------- the kitchen
def _ic_kit_cfg(o):
    def lights(o):
        amb = _ic_light(o)
        steady = [Lamp(kind='win', c=IC_MOON, k=0.6, soft=10.0, panes=_panes_y(IC_KWIN[0], IC_KWIN[1], IC_KWIN[2], IC_KWIN[3], 0.0), d=_norm3((0.3, -0.5, 1.0)))]
        var = [('kitchen_light', [Lamp(-4.6, 2.4, 2.3, 4.5, '#fff0d8', 1.3, (1.0, 0.5, 0.2), fall=1.3)], _kfn(o.get('kitchen_light', 0.0), 631))]
        var += _ic_common_var(o, _panes_y(IC_KWIN[0], IC_KWIN[1], IC_KWIN[2], IC_KWIN[3], 0.0) if o.get('truck') == 'A' else None, (0.4, -0.2, 1.0), None, 635)
        return amb, steady, var

    def west(p_, W, H):
        pass
    def back(p_, W, H):                                                       # run (-6.4, 4.6) -> (-2.8, 4.6): u = x + 6.4
        _wall_clock(p_, (3.0) * 100, H - 200, 12, 11, 2)
        p_.fill(rect(40, H - 230, 160, 70), '#e8dcc0'); p_.line(rect(40, H - 230, 160, 70), 0.6)
    def front(p_, W, H):                                                       # run (-2.8, 0) -> (-6.4, 0): u = -2.8 - x
        for k in range(int(W / 15)):                                          # tile backsplash band behind the counter
            p_.fill(rect(k * 15, H - 145, 14, 54), '#d8e4e8' if k % 2 else '#e8eef0')
    holes = {'east': [(-2.8, IC_KDOOR[0], -2.8, IC_KDOOR[1], 0.0, IC_KDOOR[2])]}
    wins = {'front': [(IC_KWIN[0], 0.0, IC_KWIN[1], 0.0, IC_KWIN[2], IC_KWIN[3], (2, 2))]}
    runs = _rect_runs(IC_KIT, holes, wins, {'back': back, 'front': front})

    def pieces(o):
        P = []
        cnt = Box(-4.6, 0.32, 3.6, 0.62, 0.0, 0.92, 180)
        def counter(pen, v):
            draw_box(pen, v, cnt, {'top': dict(fill='#d8d0c0', art=lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'grunge', 0.3, 'overlay', 1.0)),
                                   'front': dict(fill='#7a8a9a', art=lambda p_, W, H: [p_.line(rect(6 + k * W / 5, 10, W / 5 - 12, H - 20), 1.0, '#000000', 90) for k in range(5)]),
                                   'all': '#6a7a8a'}, lw=1.0)
            sk = Box(-4.85, 0.3, 0.6, 0.42, 0.78, 0.93, 180)
            draw_box(pen, v, sk, {'top': '#9aa4b0', 'all': '#8a949e'}, lw=0.8, skip=('bottom',))
            A = (-4.85, 0.93, 0.08); B_ = (-4.85, 1.2, 0.08)
            if v.d(A[0], A[2]) > 0.3: pen.seg(v.p(*A), v.p(*B_), max(1.0, 0.025 * v.s(A[0], A[2])), '#c8ccd4')
        P.append(Piece('counter', (-4.6, 0.5, 0.32), counter, block=cnt.footprint()))
        up = Box(-3.3, 0.18, 1.0, 0.35, 1.5, 2.3, 180)
        P.append(Piece('cabinet', (-3.3, 1.9, 0.18), lambda pen, v: draw_box(pen, v, up, {'all': '#7a8a9a', 'front': dict(fill='#7a8a9a', art=lambda p_, W, H: p_.line(rect(6, 6, W - 12, H - 12), 1.0, '#000000', 90))}, lw=1.0, skip=('bottom',))))
        fr = Box(-6.05, 3.6, 0.8, 0.7, 0.0, 1.8, 90)
        def fridge(pen, v):
            def art(p_, W, H):
                p_.fill(rect(0, 0, W, H), '#e8eae8'); p_.line(rect(2, H * 0.32, W - 4, 2), 1.0, '#9a9a9a')
                p_.fill(rect(W - 12, 20, 4, 40), '#b8b8b8'); p_.fill(rect(W - 12, H * 0.36, 4, 60), '#b8b8b8')
                _bu_photo(p_, W * 0.42, H * 0.18, 26, 32, 'grandpa')                  # Mom's photo (the real Mom, in scrubs)
                p_.fill(rect(W * 0.18, H * 0.48, 30, 22), '#f8f0d8'); p_.fill(rect(W * 0.5, H * 0.52, 26, 30), '#d8f0f8')
                btext(p_, 'MOM', W * 0.42, H * 0.18 + 24, 'kid', 6, '#c82a5a', 230, 'center')
            draw_box(pen, v, fr, {'front': dict(fill='#e8eae8', art=art), 'all': '#d8dad8'}, lw=1.0)
        P.append(Piece('fridge', (fr.cx, 0.9, fr.cy), fridge, block=fr.footprint()))
        st = Box(-4.6, 4.28, 0.76, 0.62, 0.0, 0.92, 0)
        def stove(pen, v):
            draw_box(pen, v, st, {'front': dict(fill='#e8e4dc', art=lambda p_, W, H: (p_.fill(rect(8, 22, W - 16, H * 0.5), '#2a2a2a'), p_.line(rect(8, 22, W - 16, H * 0.5), 1.0))),
                                  'top': dict(fill='#1a1a1a', art=lambda p_, W, H: [p_.line(oval(W * (0.28 + 0.44 * (k % 2)), H * (0.3 + 0.4 * (k // 2)), 10), 1.4, '#5a5a5a') for k in range(4)]),
                                  'all': '#d8d4cc'}, lw=1.0)
        P.append(Piece('stove', (st.cx, 0.5, st.cy), stove, block=st.footprint()))
        tb = Box(-4.3, 2.5, 1.1, 0.8, 0.0, 0.75, 0)
        if o.get('table', True):                    # table=False: a low 'window' framing would put the camera inside its corner
            P.append(Piece('table', (tb.cx, 0.4, tb.cy), lambda pen, v: draw_parts(pen, v, table_parts(tb, '#a8845a', apron=0.06)), block=tb.footprint()))
        stl = o.get('stool', 'window')
        if stl:
            sx, sy = IC_STOOL if stl == 'window' else (-5.8, 1.6)
            P.append(Piece('stool', (sx, 0.2, sy), lambda pen, v: _ic_stool(pen, v, sx, sy), block=_r4p((sx - 0.2, sx + 0.2, sy - 0.15, sy + 0.15))))
        return P

    def spots(v, o):
        S = {}
        kx = (IC_KWIN[0] + IC_KWIN[1]) / 2
        S['stool'] = _mk_spot(v, 'stool', IC_STOOL[0], IC_STOOL[1], 0.24, 'stand', "on Lina's step-stool at the window (facing it)", face=(0, -1))
        S['window_in'] = _mk_spot(v, 'window_in', kx, 0.85, 0.0, 'stand', 'at the counter facing the kitchen window', face=(0, -1))
        S['sill_out'] = _mk_spot(v, 'sill_out', kx, -0.12, IC_KWIN[2] + 0.01, 'surface', 'the OUTSIDE sill (the cone, five minutes later)')
        S['window_crack'] = _mk_spot(v, 'window_crack', kx, -0.02, IC_KWIN[2] + 0.08, 'point', 'the crack under the raised sash')
        S['fridge_photo'] = _mk_spot(v, 'fridge_photo', -5.65, 3.6, 1.6, 'point', "Mom's photo on the fridge (the real Mom)")
        S['kitchen_mid'] = _mk_spot(v, 'kitchen_mid', -4.3, 1.5, 0.0, 'stand', 'the middle of the kitchen')
        S['doorway'] = _mk_spot(v, 'doorway', -3.1, 2.95, 0.0, 'stand', 'in the kitchen doorway (facing in, -x)', face=(-1, 0))
        return S

    return dict(name='kitchen', R=IC_KIT, H=IC_CEIL, floor=dict(base='#c8c0b0', kind='checker', ink='#5a6a7a', seed=31), runs=runs,
                walls=dict(paper=IC_PAL['kit_paper'], ink='#c8b890', kind='gingham', wains=0.0, seed=33, scale=1.0, pa=50),
                ceil=dict(c='#ece6da'), lights=lights, pieces=pieces, spots=spots)


def _ic_stool(pen, v, x, y):
    """Lina's little two-step stool (pink, a daisy decal)."""
    B1 = Box(x, y, 0.4, 0.3, 0.0, 0.24, 0)
    B2 = Box(x, y + 0.08, 0.4, 0.14, 0.24, 0.4, 0)
    for B in (B1, B2):
        draw_box(pen, v, B, {'top': '#f4a8c4', 'front': dict(fill='#e888aa', art=lambda p_, W, H: p_.fill(_flake_path(W / 2, H / 2, 6), '#ffffff', 200)), 'all': '#d87898'}, lw=0.8)


# ---------------------------------------------------------------------------------------------- the bathroom
def _ic_bath_cfg(o):
    def lights(o):
        amb = _ic_light(o)
        steady = [Lamp(kind='win', c=IC_MOON, k=0.55, soft=10.0, panes=_panes_y(IC_BWIN[0], IC_BWIN[1], IC_BWIN[2], IC_BWIN[3], 0.0), d=_norm3((0.0, -0.5, 1.0)))]
        var = [('bath_light', [Lamp(-0.5, 2.3, 1.1, 3.0, '#fff4e0', 1.2, fall=1.3)], _kfn(o.get('bath_light', 0.0), 641))]
        var += _ic_common_var(o, None, (0, 0, 1), _panes_y(IC_BWIN[0], IC_BWIN[1], IC_BWIN[2], IC_BWIN[3], 0.0), 645)
        if o.get('truck') == 'B':
            var.append(('pink', [Lamp(kind='win', c=IC_PINK, k=0.9, soft=10.0, panes=_panes_y(IC_BWIN[0], IC_BWIN[1], IC_BWIN[2], IC_BWIN[3], 0.0), d=_norm3((-0.1, -0.3, 1.0)))],
                        _kfn(o.get('pink', 1.0), 649)))
        return amb, steady, var

    def east(p_, W, H):                                                       # run (0.4, 2.2) -> (0.4, 0): u = 2.2 - y
        p_.fill(rect(0, H - 120, W, 120), IC_PAL['bath_tile']); pat(p_, W, 120, 'tile', '#9ab0b8', 90) if False else None
        for k in range(int(W / 15) + 1):
            for j in range(8): p_.line(rect(k * 15, H - 120 + j * 15, 15, 15), 0.5, '#9ab0b8', 120)
    def west(p_, W, H):
        p_.fill(rect(0, H - 120, W, 120), IC_PAL['bath_tile'])
        for k in range(int(W / 15) + 1):
            for j in range(8): p_.line(rect(k * 15, H - 120 + j * 15, 15, 15), 0.5, '#9ab0b8', 120)
        p_.fill(rect(25, H - 155, 50, 4), '#c8c8d0')                                         # towel bar by the door
    def back(p_, W, H):
        p_.fill(rect(0, H - 180, W, 180), IC_PAL['bath_tile'])
        for k in range(int(W / 15) + 1):
            for j in range(12): p_.line(rect(k * 15, H - 180 + j * 15, 15, 15), 0.5, '#9ab0b8', 120)
    def front(p_, W, H):
        p_.fill(rect(0, H - 120, W, 120), IC_PAL['bath_tile'])
        for k in range(int(W / 15) + 1):
            for j in range(8): p_.line(rect(k * 15, H - 120 + j * 15, 15, 15), 0.5, '#9ab0b8', 120)
    holes = {'west': [(-1.4, IC_BDOOR[0], -1.4, IC_BDOOR[1], 0.0, IC_BDOOR[2])]}
    wins = {'front': [(IC_BWIN[0], 0.0, IC_BWIN[1], 0.0, IC_BWIN[2], IC_BWIN[3], (1, 1))]}
    runs = _rect_runs(IC_BATH, holes, wins, {'east': east, 'west': west, 'back': back, 'front': front})

    def pieces(o):
        P = []
        tub = Box(-0.5, 1.82, 1.7, 0.72, 0.0, 0.56, 0)
        def tubd(pen, v):
            draw_box(pen, v, tub, {'top': '#f4f4f0', 'all': '#eceae4'}, lw=1.0)
            inner = [tub.at(-0.75, -0.26, 0.565), tub.at(0.75, -0.26, 0.565), tub.at(0.75, 0.26, 0.565), tub.at(-0.75, 0.26, 0.565)]
            path = v.poly3(inner)
            if not path.isEmpty(): pen.fill(path, lit('#d8dce0', inner[0], (0, 1, 0))); pen.line(path, 0.8)
            A = tub.at(0.6, -0.33, 0.8); 
            if v.d(A[0], A[2]) > 0.3: pen.seg(v.p(*A), v.p(A[0], 0.62, A[2]), max(1.0, 0.02 * v.s(A[0], A[2])), '#c8ccd4')
        P.append(Piece('tub', (tub.cx, 0.3, tub.cy), tubd, block=tub.footprint()))
        sink = Box(0.12, 0.85, 0.5, 0.42, 0.78, 0.9, -90)
        def sinkd(pen, v):
            A = (0.2, 0.0, 0.85); B_ = (0.2, 0.78, 0.85)
            if v.d(A[0], A[2]) > 0.3: pen.seg(v.p(*A), v.p(*B_), max(1.5, 0.1 * v.s(A[0], A[2])), lit('#eceae4', B_, (-1, 0, 0)))
            draw_box(pen, v, sink, {'top': '#f4f4f0', 'all': '#eceae4'}, lw=1.0)
        P.append(Piece('sink', (0.12, 0.8, 0.85), sinkd, block=sink.footprint()))
        mirror = [(0.385, 1.85, 0.6), (0.385, 1.85, 1.1), (0.385, 1.15, 1.1), (0.385, 1.15, 0.6)]
        fog = _static(o.get('fog', 0.4))
        rich = bool(o.get('mirror_rich', False))

        def mird(pen, v):
            path = v.poly3(mirror)
            if path.isEmpty() or not v.visible(mirror[0], (-1, 0, 0)): return
            pen.fill(path, '#5a6a7a'); pen.fill(path, '#e8eef4', 120 * fog)
            if rich:            # opt-in (the 'window' view only: it sits at the frame edge): glass streaks, fog grain, a frame
                b = path.computeTightBounds()
                pen.linear(path, b.left(), b.top(), b.right(), b.bottom(),
                           [(0.0, '#ffffff', 0), (0.3, '#ffffff', 120), (0.4, '#ffffff', 0), (0.55, '#ffffff', 0), (0.6, '#ffffff', 80), (0.66, '#ffffff', 0)])
                pen.texture(path, 'grunge', 0.5, 'overlay', 0.8)
                pen.line(path, 9.0, '#8a929c')
            pen.line(path, 2.0, '#c8ccd4')
        P.append(Piece('mirror', (0.38, 1.5, 0.85), mird))
        toi = Box(-1.05, 0.3, 0.42, 0.6, 0.0, 0.42, 180)
        P.append(Piece('toilet', (toi.cx, 0.3, toi.cy), lambda pen, v: (draw_box(pen, v, toi, {'all': '#f0f0ec', 'top': '#f8f8f4'}, lw=1.0),
                                                                       draw_box(pen, v, Box(-1.05, 0.08, 0.44, 0.18, 0.42, 0.82, 180), {'all': '#f0f0ec'}, lw=1.0)), block=toi.footprint()))
        tw = o.get('towels', 'rack')
        if tw in ('gap', 'jammed'):
            P.append(Piece('towels_gap', (-1.3, 0.05, 1.35), lambda pen, v: _ic_towel_gap(pen, v, tw == 'jammed')))
        D = _ic_bath_door()
        dv = o.get('door', 0.0)
        if not callable(dv):
            P.append(Piece('door', (-1.4, 1.0, 1.35), lambda pen, v: D.draw(pen, v, _static(dv))))
        return P

    def spots(v, o):
        S = {}
        S['tub_sit'] = _mk_spot(v, 'tub_sit', -0.5, 1.82, 0.0, 'seat', 'in the empty tub, sitting (the two of them, one blanket)', face=(0, -1), seat_Y=0.12)
        S['floor_sit'] = _mk_spot(v, 'floor_sit', -0.6, 1.0, 0.0, 'floor_sit', 'sitting on the bath mat against the tub', face=(-1, 0))
        S['door_kneel'] = _mk_spot(v, 'door_kneel', -1.1, 1.35, 0.0, 'kneel', 'kneeling at the door, jamming the towel down (facing it, -x)', face=(-1, 0))
        S['gap'] = _mk_spot(v, 'gap', -1.38, 1.35, 0.02, 'point', 'the gap under the door (the needle-thin leg tip slides in here)')
        S['window_wipe'] = _mk_spot(v, 'window_wipe', (IC_BWIN[0] + IC_BWIN[1]) / 2, 0.45, 0.0, 'stand', 'at the small window, wiping the frost off (facing it)', face=(0, -1))
        S['window'] = _mk_spot(v, 'window', (IC_BWIN[0] + IC_BWIN[1]) / 2, 0.02, 1.55, 'point', 'the small frosted window')
        return S

    return dict(name='bath', R=IC_BATH, H=IC_CEIL, floor=dict(base='#e8e4dc', kind='hex', ink='#9aa0a8', seed=41, scale=0.6), runs=runs,
                walls=dict(paper='#dfe6e2', ink='#c8d4d0', kind='stripe', wains=0.0, seed=43, scale=0.8, pa=40),
                ceil=dict(c='#ece8e0'), lights=lights, pieces=pieces, spots=spots)


def _ic_towel_gap(pen, v, jammed=False):
    """Towels stuffed into the gap under the bathroom door (inside); jammed: one pressed down hard (on the leg tip)."""
    for i, (y0, y1, c) in enumerate(((IC_BDOOR[0] + 0.02, IC_BDOOR[0] + 0.42, '#7aa0c8'), (IC_BDOOR[0] + 0.38, IC_BDOOR[1] - 0.02, '#e8c8a8'))):
        B = Box(-1.3, (y0 + y1) / 2, 0.16, y1 - y0, 0.0, 0.1 if not (jammed and i == 1) else 0.07, 90)
        draw_box(pen, v, B, {'all': dict(fill=c, art=lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'fabric', 0.6, 'overlay', 0.6)), 'top': mix(c, '#ffffff', 0.15)}, lw=0.8)


# ---------------------------------------------------------------------------------------------- builders
_IC_HOUSE_DEF = dict(tod='night', truck='A', curtains=0.04, rules=True, eighth=False, hall=0.0, lamp=0.0, ceil=0.0, tv=0.0, radio='table')


def _ic_grade(o, warm_keys=('lamp', 'ceil', 'hall', 'kitchen_light', 'bath_light')):
    if o.get('blackout'): return 'ic_dark'
    if any(_static(o.get(k_, 0.0)) > 0.3 for k_ in warm_keys): return 'ic_warm'
    return 'ic_night'


def ic_living(view='wide', **kw):
    """Our living room. view: wide | couch | couch3q | tv | window | radio | opening. Levels (number or f(t)): lamp,
    ceil, tv (screen on), hall, pink (his window through the curtains; default on when truck='A'), beacon (Dad's
    orange sweep: ST.ic_pass(t0)), phone (+phone_at), flash. curtains: 0 shut .. 1 open (0.04 = Lina's crack) or f(t);
    skull: glimpse 2 in the black TV screen (level / f(t)); frost: frost creeping on the INSIDE of the window (0..1 / f(t));
    blanket: the one-blanket nest on the couch; radio 'table' | None (in a hand); cone 'floor' (the shards); blackout."""
    o = _ic_house_o(kw, _IC_HOUSE_DEF)
    v = cam('ic_liv_' + view)
    main = BuBox(_ic_liv_cfg(o))
    far = [BuBox(_ic_hall_cfg(dict(o, _far=True)), far=True)]
    dyn = []
    amb, steady, var = main.lights(o)
    if callable(o.get('curtains')):
        cf = o['curtains']
        dyn.append(live_layer('curtains', v, (3.4, 1.4, 0.14), lambda pen, v_, t: curtain_pair(pen, v_, (6.4, 0.0), (0.4, 0.0), 6.4 - IC_PWIN[1], 6.4 - IC_PWIN[0],
                                                                                              2.3, 2.25, 0.0, cf(t), IC_PAL['curt'], sheer=False), amb, steady, var))
    if o.get('frost') is not None:
        dyn.append(_ic_frost_layer(v, [[(IC_PWIN[0], IC_PWIN[3], 0.0), (IC_PWIN[1], IC_PWIN[3], 0.0), (IC_PWIN[1], IC_PWIN[2], 0.0), (IC_PWIN[0], IC_PWIN[2], 0.0)]],
                                   o['frost'], 'frost', 1, order=v.d(3.4, 0.0) - 0.01))
    sp = build_view('ic_liv_' + view, v, main, o, far=far, outside=_ic_outside(o), grade=_ic_grade(o), dyn=dyn)
    sp.info['tv_quad'] = _ic_tv_quad()
    sp.info['window_quad'] = [(IC_PWIN[0], IC_PWIN[3], 0.0), (IC_PWIN[1], IC_PWIN[3], 0.0), (IC_PWIN[1], IC_PWIN[2], 0.0), (IC_PWIN[0], IC_PWIN[2], 0.0)]
    sp.info['note'] = 'Living room: the couch faces the TV (+y) with its back to the window; seats couch_left / couch_mid / couch_right.'
    return sp


def ic_hall(view='door', **kw):
    """The hall. view: door | doorclose | back | hatch | bathdoor. Levels: hall (ceiling lights), lamp (living-room
    spill), pink (his window through the door glass), beacon, phone, flash. door (deg open or f(t)), rules, eighth;
    face: the long white face sliding up the frosted glass (level, or f(t) -> (k, rise 0..1)); knob_frost (0..1 / f(t));
    hatch 0 closed .. 1 dropped open (or f(t)); bath_door (deg, default 85 open; 0 shut); blackout."""
    o = _ic_house_o(kw, _IC_HOUSE_DEF)
    v = cam('ic_hall_' + view)
    main = BuBox(_ic_hall_cfg(o))
    far = [BuBox(_ic_liv_cfg(dict(o, _far=True)), far=True), BuBox(_ic_kit_cfg(dict(o, _far=True)), far=True)]
    if _static(o.get('bath_door', 85.0), 85.0) > 5 or callable(o.get('bath_door')): far.append(BuBox(_ic_bath_cfg(dict(o, _far=True)), far=True))
    dyn = []
    amb, steady, var = main.lights(o)
    D = ic_front_door(o.get('rules', True), o.get('eighth', False))
    if callable(o.get('door')):
        df = o['door']
        dyn.append(live_layer('front_door', v, (-2.1, 1.0, 0.1), lambda pen, v_, t: D.draw(pen, v_, df(t)), amb, steady, var))
    else:
        if _static(o.get('door', 0.0)) < 2: dyn.append(ic_door_glass(v, D, o))
    if callable(o.get('hatch')):
        hf = o['hatch']
        ajar = bool(o.get('hatch_ajar', False))
        dyn.append(live_layer('hatch', v, (-2.1, IC_CEIL, 5.9), lambda pen, v_, t: ic_hatch(pen, v_, hf(t), ajar), amb, steady, var))
    sp = build_view('ic_hall_' + view, v, main, o, far=far, outside=_ic_outside(o), grade=_ic_grade(o), dyn=dyn)
    sp.info['door_glass'] = D.glass_quads(0.0)
    sp.info['note'] = 'Hall: figures OUTSIDE the door go between the outside layer and the door (sp.order_at(x, y) with y < 0).'
    return sp


def ic_kitchen(view='window', **kw):
    """The kitchen. view: window | wide. kitchen_light, pink, phone, flash; sash (0 shut .. 1: the window raised a crack
    = 0.12); cone 'sill' (on the OUTSIDE sill); stool 'window' | 'away' | None; blackout."""
    o = _ic_house_o(kw, dict(_IC_HOUSE_DEF, stool='window'))
    v = cam('ic_kit_' + view)
    cfg = _ic_kit_cfg(o)
    sash = _static(o.get('sash', 0.0))
    if sash > 0:
        for r in cfg['runs']:
            r['wins'] = [w_[:6] + ((2, 2),) for w_ in r['wins']]
    main = BuBox(cfg)
    if sash > 0:
        sh = main.shell
        def shell(pen, v_, o_, sh=sh):
            sh(pen, v_, o_)
            a, b = (-2.8, 0.0), (-6.4, 0.0)
            window_unit(pen, v_, a, b, -2.8 - IC_KWIN[1], -2.8 - IC_KWIN[0], IC_KWIN[2], IC_KWIN[3], 0.0, (2, 2), '#f1ece0', sash_open=sash)
        main.shell = shell
    far = [BuBox(_ic_hall_cfg(dict(o, _far=True)), far=True)]
    dyn = []
    if o.get('frost') is not None:
        dyn.append(_ic_frost_layer(v, [[(IC_KWIN[0], IC_KWIN[3], 0.0), (IC_KWIN[1], IC_KWIN[3], 0.0), (IC_KWIN[1], IC_KWIN[2], 0.0), (IC_KWIN[0], IC_KWIN[2], 0.0)]], o['frost'], 'frost', 2))
    return build_view('ic_kit_' + view, v, main, o, far=far, outside=_ic_outside(o), grade=_ic_grade(o), dyn=dyn)


def ic_bath(view='door', **kw):
    """The bathroom (the smallest room; no gas appliances). view: door | gap (low at the door gap: the leg tip) | window
    | wide. bath_light, beacon, pink (his window across the street once he is at B), phone, flash; towels 'rack' | 'gap'
    | 'jammed'; door (deg open, 0 shut); fog (mirror 0..1); frost (on the window inside); wipe (the patch wiped clear on
    the window: 0..1); truck default 'B' (the song moved across the street)."""
    o = _ic_house_o(kw, dict(_IC_HOUSE_DEF, truck='B', towels='gap', door=0.0, blackout=True))
    v = cam('ic_bath_' + view)
    main = BuBox(_ic_bath_cfg(o))
    far = [BuBox(_ic_hall_cfg(dict(o, _far=True)), far=True)] if _static(o.get('door', 0.0)) > 5 else []
    dyn = []
    q = [[(IC_BWIN[0], IC_BWIN[3], 0.0), (IC_BWIN[1], IC_BWIN[3], 0.0), (IC_BWIN[1], IC_BWIN[2], 0.0), (IC_BWIN[0], IC_BWIN[2], 0.0)]]
    wipe = _kfn(o.get('wipe', 0.0), 651)
    def frosted(pen, t):
        path = v.poly3(q[0])
        if path.isEmpty() or not v.visible(q[0][0], (0, 0, 1)): return
        b = path.computeTightBounds()
        hole = oval((b.left() + b.right()) / 2, (b.top() + b.bottom()) / 2, b.width() * 0.36 * wipe(t), b.height() * 0.3 * wipe(t))
        pen.cv.save(); pen.cv.clipPath(minus(path, hole) if wipe(t) > 0.01 else path, skia.ClipOp.kIntersect, True)
        pen.fill(path, '#c8d4ec', 215); pen.texture(path, 'grunge', 0.6, 'overlay', 0.8)
        kb = beac(t)
        if kb > 0.01:                                                   # Dad's beacon THROUGH the frosted glass (it glows, a band sweeps)
            w_ = b.width(); ph = ((t * 1.3) % 1.0)
            pen.fill(path, IC_ORANGE, 150 * kb)
            pen.radial(path, b.left() - 0.3 * w_ + 1.6 * w_ * ph, (b.top() + b.bottom()) / 2, 0.7 * w_, [(0, '#ffd080', 235), (1, '#ff8a1e', 0)], a=kb, sy=1.6)
        pen.cv.restore()
        if kb > 0.01: pen.glow((b.left() + b.right()) / 2, (b.top() + b.bottom()) / 2, 1.1 * b.width(), IC_ORANGE, 70 * kb)
    beac = _kfn(o.get('beacon', 0.0), 652)
    lay = Layer(max(0.3, v.d(-0.5, 0.0)), frosted, 'window_frost', blur=None); lay.order = v.d(-0.5, 0.0) - 0.02
    dyn.append(lay)
    o2 = dict(o); o2['cone'] = None
    return build_view('ic_bath_' + view, v, main, o, far=far, outside=_ic_outside(o2), grade='ic_dark' if o.get('blackout') else _ic_grade(o), dyn=dyn)


_icam('ic_liv_wide', 760, 520, 1.6, 6.05, 5.25, -138, _env(), 'the living room from the back-east corner: the window and curtains, the couch (its back to the window) at 3/4, the opening to the hall', 'living')
_icam('ic_liv_couch', 900, 540, 1.15, 3.4, 4.85, 180, _env(), 'from the TV to the couch face-on, the window and the curtain crack behind them (the reverse of the reflection)', 'living')
_icam('ic_liv_couch3q', 980, 540, 1.2, 5.3, 4.1, -140, _env(), 'the couch at 3/4 from the front-east (seated figures)', 'living')
_icam('ic_liv_tv', 1250, 520, 1.08, 3.2, 2.05, 3, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.08)), 'from the couch to the black TV screen (POV: the reflection, us, the crack, the skull)', 'living')
_icam('ic_liv_window', 950, 520, 1.5, 3.1, 3.7, 180, _env(), 'to the window and curtains over the couch back', 'living')
_icam('ic_liv_radio', 1300, 360, 0.95, 4.8, 2.45, 176, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.08)), "close on Dad's radio on the side table", 'living')
_icam('ic_liv_opening', 860, 520, 1.5, 4.6, 3.6, -96, _env(), 'from the room to the opening and the hall', 'living')
_icam('ic_hall_door', 820, 520, 1.5, -2.1, 6.7, 180, _env(), 'down the hall to the front door (bath door left, coats right)', 'hall')
_icam('ic_hall_doorclose', 1150, 520, 1.4, -2.1, 1.45, 180, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.08)), 'close on the front door: the clear strip, the frosted panel, the rules, the knob', 'hall')
_icam('ic_hall_back', 820, 520, 1.55, -2.1, 0.45, 0, _env(), 'from the front door down the hall: the hatch in the ceiling, the bedroom doors', 'hall')
_icam('ic_hall_hatch', 700, 600, 1.3, -2.1, 3.9, 0, _env(), 'up at the attic hatch from the hall (it drops open; his face upside down)', 'hall', pitch=-34.0)
_icam('ic_hall_bathdoor', 900, 520, 1.4, -2.55, 3.4, 150, _env(), 'the bathroom door from the hall', 'hall')
_icam('ic_kit_window', 950, 520, 1.45, -4.85, 2.9, 180, _env(), "the kitchen window over the sink, Lina's step-stool, the outside sill", 'kitchen')
_icam('ic_kit_wide', 820, 520, 1.55, -3.15, 4.2, -128, _env(), 'the kitchen from the doorway: window, fridge (Mom\'s photo), table', 'kitchen')
_icam('ic_bath_door', 900, 520, 1.1, 0.25, 1.3, -90, _env(), 'inside the bathroom to the door (towels in the gap)', 'bath')
_icam('ic_bath_gap', 1100, 360, 0.35, -0.55, 1.35, -90, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.08)), 'low at the door gap: the needle-thin leg tip slides in under the towels', 'bath', pitch=14.0)
_icam('ic_bath_window', 1000, 520, 1.5, -0.5, 1.75, 180, _env(), 'to the small frosted window (he wipes the frost off)', 'bath')
_icam('ic_bath_wide', 760, 520, 1.6, 0.3, 2.1, -140, _env(), 'the bathroom wide: the tub, the door, the window', 'bath')


# ====================================================================================================== 1958, morning, across town
def ic_1958(view='curb', mitten=True, truck=True, **kw):
    """Birch Lane in 1958 (sepia-cold grade ic_1958, older siding, two 1958 cars at the kerbs): view 'curb' (from
    Kessler's doorway: the pink window at the kerb, Benny's small footprints leading to it), 'lane' (down the lane),
    'mitten' (close, low: one red mitten at the kerb, the truck gone). Same plan as the night (the truck at B)."""
    tracks = [('benny', [(1.4, -22.0), (1.3, -21.0), (-0.6, -19.0), (-2.6, -17.1)])]
    props = [('mitten', -2.4, -17.15, IC_RED)] if (mitten and view == 'mitten') else []
    if view == 'mitten': truck = False
    return ic_street(view, tod='1958', truck='B' if truck else None, tracks=tracks, props=props, porch=0.0, kporch=1.0 if view != 'mitten' else 0.0,
                     win=dict(his=0.8), smoke=1.0, car=True, **kw)


def ic_morning(view='kessler', **kw):
    """The morning after (sunrise, warm and safe): Kessler's walk shoveled (anchors kwalk_shovel1..3), his chimney
    smoking again, our walk shoveled, no truck. Any Birch Lane view."""
    d = dict(tod='morning', truck=None, smoke=1.0, our_smoke=1.0, walk='shoveled', kwalk='shoveled', street=0.0)
    d.update(kw)
    return ic_street(view, **d)


def ic_town(view='town', truck=True, truck_x=None, **kw):
    """Two nights later, across town: a house alone with NO chimney smoke between neighbours whose chimneys smoke; his
    truck slowing at its kerb (truck_x: slide it along the kerb), the chime ending on the missing note."""
    pos = (IC_TRUCK_B[0] if truck_x is None else truck_x, IC_TRUCK_B[1], 90.0) if truck else None
    return ic_street(view, layout='town', truck=pos, fence=False, car=False, **kw)


_icam('ic_ext_mitten', 1100, 300, IC_SNOWY + 0.5, -2.42, -18.3, 2, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.1)), 'close and low on the kerb: one red mitten (1958)', 'street', pitch=22.0)
_icam('ic_ext_town', 760, 520, IC_G + 1.7, -7.0, -6.0, 152, _env(f=(1.0, 2.0)), 'across town: the truck slowing at the house with no chimney smoke', 'street')


# ====================================================================================================== inserts
IC_RULES = [(1, 'WHEN YOU HEAR HIS SONG, CLOSE EVERY CURTAIN. IF HE CAN\'T SEE YOU, HE CAN\'T CALL YOU.'),
            (2, 'IF HE LEAVES YOU A FREE ONE, DON\'T TOUCH IT, DON\'T BRING IT IN, AND NEVER TASTE IT. NOTHING HE GIVES IS FREE.'),
            (3, 'IF THE HEAT GOES OUT, PUT ON EVERY LAYER YOU OWN, AND GET UNDER ONE BLANKET TOGETHER. NOBODY SLEEPS ALONE TONIGHT.'),
            (4, 'IF YOU STOP SHIVERING, TELL SOMEONE RIGHT AWAY. SHIVERING MEANS YOU\'RE STILL FIGHTING.'),
            (5, 'IF SOMEONE YOU LOVE KNOCKS, LOOK FOR THEIR BREATH. IN THIS COLD, EVERYONE\'S BREATH MAKES A CLOUD. HIS DOESN\'T.'),
            (6, 'IF THE HOUSE GETS AS COLD AS OUTSIDE, IT ISN\'T INSIDE ANYMORE. FIND THE SMALLEST ROOM, SHUT THE DOOR, AND BLOCK THE DRAFTS.'),
            (7, 'DON\'T GO OUTSIDE BEFORE SUNRISE. NOT FOR ANYONE. NOT FOR ANYTHING. NOT EVEN FOR ME.')]
IC_RULE8 = (8, 'Never go out for him. Go out for each other. Together, with a grown-up.')
IC_OUTRO = [('If someone stopped shivering, is sleepy, confused, or says they feel warm:', 'CALL EMERGENCY SERVICES.', 'Get them inside and dry. Wrap their middle. Stay close.'),
            ('White, waxy fingers?', 'FROSTBITE. DON\'T RUB.', 'Warm them gently against skin (under the arms).'),
            ('No heat?', 'NEVER HEAT WITH AN OVEN OR GRILL INDOORS.', 'Layers, one blanket, the smallest room.'),
            ('"Free treat."  "Your dad said it\'s okay."  "Just come to the window."', 'NEVER. TELL A GROWN-UP.', ''),
            ('This week, with a grown-up:', 'KNOCK ON THE DOOR OF SOMEONE WHO LIVES ALONE.', '')]


def _wrap(text, n):
    out, line = [], ''
    for w in text.split():
        if len(line) + len(w) + 1 > n and line: out.append(line); line = w
        else: line = (line + ' ' + w).strip()
    if line: out.append(line)
    return out


def _shaky(pen, s, x, y, size, c='#1a2238', a=245, seed=0, font='hand'):
    """Kessler's shaky hand-drawn capitals: each letter jittered a little."""
    rng = np.random.default_rng(abs(int(seed)))
    xx = x
    for ch in s:
        w = btext_width(ch, font, size)
        btext(pen, ch, xx + rng.uniform(-0.6, 0.6), y + rng.uniform(-1.4, 1.4), font, size * rng.uniform(0.96, 1.05), c, a)
        xx += w * 1.02
    return xx


def _lined_paper(pen, x0, y0, W, H, tape=True, c='#f6f1e2'):
    pen.fill(rect(x0 + 14, y0 + 22, W, H), '#000000', 110, blur=20)
    pen.fill(rect(x0, y0, W, H), c); pen.texture(rect(x0, y0, W, H), 'paper', 0.45, 'multiply', 1.0)
    for i in range(int(H / 40)): pen.fill(rect(x0, y0 + 96 + i * 40, W, 2), '#8ab0d8', 110)
    pen.fill(rect(x0 + 80, y0, 3, H), '#d88a8a', 130)
    if tape:
        for (tx, ty, r) in ((x0 + 50, y0 - 4, -14), (x0 + W - 50, y0 - 4, 12), (x0 + 50, y0 + H + 4, 10), (x0 + W - 50, y0 + H + 4, -12)):
            _bu_tape(pen, tx, ty, 140, 44, r, 190)


def _ici_rules(pen, t, show=7, hl=0, eighth=False, door='ours', **kw):
    """The seven rules taped to a door (ours: slate blue / Kessler's: brown), shaky capitals, signed W.K.; hl = the rule
    being read (a soft highlight); eighth = rule 8 added below in Adam's hand."""
    c = IC_PAL['door'] if door == 'ours' else IC_PAL['door_k']
    _ibg_b(pen, c, _darken(c, 0.3), 140); pen.texture(rect(*_IBGB), 'wood', 0.35, 'overlay', 1.2, 90)
    pen.cv.save(); pen.cv.translate(960, 540); pen.cv.rotate(-1.0)
    W, H = 1240, 1010 if eighth else 960
    x0, y0 = -W / 2, -H / 2 - (20 if eighth else 0)
    _lined_paper(pen, x0, y0, W, H)
    _shaky(pen, 'RULES FOR A COLD SNAP', x0 + 330, y0 + 70, 46, '#1a2238', 245, 3)
    yy = y0 + 132
    for (n, txt) in IC_RULES[:show]:
        lines = _wrap(txt, 64)
        if hl == n: pen.fill(rect(x0 + 92, yy - 30, W - 130, 40 * len(lines) + 6), '#fff08a', 160)
        _shaky(pen, '%d.' % n, x0 + 100, yy, 30, '#1a2238', 245, n)
        for j, ln in enumerate(lines): _shaky(pen, ln, x0 + 140, yy + j * 40, 28, '#1a2238', 240, n * 10 + j)
        yy += 40 * len(lines) + 4
    _shaky(pen, 'W.K.', x0 + W - 150, y0 + H - 26 - (50 if eighth else 0), 40, '#1a2238', 245, 99)
    if eighth:
        n, txt = IC_RULE8
        lines = _wrap(txt, 60)
        btext(pen, '8.', x0 + 100, yy + 16, 'kid', 34, '#2a3a8a', 250)
        for j, ln in enumerate(lines): btext(pen, ln, x0 + 140, yy + 16 + j * 40, 'kid', 33, '#2a3a8a', 245)
    pen.cv.restore()


def _ici_rule(pen, t, n=1, write=1.0, **kw):
    """One rule as a full card (Kessler's shaky capitals on lined paper, tape at the corners, W.K.); n 8 = Adam's.
    write 0..1 reveals it word by word (keep 1.0 while it is read: always fully legible)."""
    _ibg_b(pen, '#1a2232', '#0a0e18', 150); pen.texture(rect(*_IBGB), 'wood', 0.3, 'overlay', 1.0, 90)
    pen.cv.save(); pen.cv.translate(960, 545); pen.cv.rotate(-0.8 if n % 2 else 0.7)
    W, H = 1600, 760
    x0, y0 = -W / 2, -H / 2
    _lined_paper(pen, x0, y0, W, H)
    if n == 8:
        txt = IC_RULE8[1]
        btext(pen, 'RULE NUMBER EIGHT', x0 + 120, y0 + 82, 'kid', 54, '#2a3a8a', 250)
        lines = _wrap(txt, 40)
        words = sum(len(l.split()) for l in lines); nw = int(math.ceil(words * clamp(write)))
        k = 0
        for j, ln in enumerate(lines):
            shown = ' '.join(ln.split()[:max(0, nw - k)]); k += len(ln.split())
            btext(pen, shown, x0 + 120, y0 + 220 + j * 92, 'kid', 70, '#2a3a8a', 250)
        btext(pen, 'A.', x0 + W - 140, y0 + H - 50, 'kid', 52, '#2a3a8a', 245)
    else:
        txt = dict(IC_RULES)[n]
        _shaky(pen, 'RULE NUMBER %s' % ('ONE TWO THREE FOUR FIVE SIX SEVEN'.split()[n - 1]), x0 + 120, y0 + 92, 64, '#1a2238', 252, n)
        lines = _wrap(txt, 34)
        words = sum(len(l.split()) for l in lines); nw = int(math.ceil(words * clamp(write)))
        k = 0
        for j, ln in enumerate(lines):
            shown = ' '.join(ln.split()[:max(0, nw - k)]); k += len(ln.split())
            _shaky(pen, shown, x0 + 120, y0 + 222 + j * 92, 66, '#1a2238', 250, n * 31 + j)
        _shaky(pen, 'W.K.', x0 + W - 170, y0 + H - 46, 48, '#1a2238', 245, 77)
    pen.cv.restore()


def _snow_bg(pen, c1='#2a3a6a', c2='#0a1028'):
    _ibg_b(pen, c1, c2, 150)
    rng = np.random.default_rng(3)
    for i in range(120):
        pen.fill(oval(rng.uniform(-400, 2320), rng.uniform(-300, 1380), rng.uniform(1, 3)), '#ffffff', int(rng.uniform(60, 200)))


def _ici_doormat(pen, t, wrapper=True, **kw):
    """The cone on our doormat outside (the stoop under snow, the door's bottom edge): steaming with cold; the wrapper
    lettered "Free. For whoever's coldest.\""""
    _ibg_b(pen, '#3a4a7a', '#141c3a', 130)
    pen.fill(rect(-460, -320, 2840, 520), IC_PAL['door']); pen.texture(rect(-460, -320, 2840, 520), 'wood', 0.35, 'overlay', 1.0, 90)
    pen.fill(rect(-460, 190, 2840, 26), '#c8ccd4')
    pen.fill(poly([(-460, 1400), (2380, 1400), (2380, 220), (-460, 220)]), '#cad6ee')
    pen.texture(rect(-460, 220, 2840, 1200), 'grunge', 0.3, 'overlay', 2.0)
    mat = poly([(420, 380), (1500, 380), (1720, 980), (200, 980)])
    pen.fill(mat, '#5a3a2a'); pen.texture(mat, 'fabric', 0.7, 'overlay', 1.4); pen.line(mat, 3)
    btext(pen, 'WELCOME', 960, 760, 'serif_b', 120, '#3a2418', 160, 'center')
    pen.fill(rect(-460, 216, 2840, 40), '#000000', 60, blur=20)
    pen.radial(None, 1150, 200, 1200, [(0, IC_PINK, 70), (1, IC_PINK, 0)])                      # his window's glow from the street
    pen.cv.save(); pen.cv.translate(960, 640); pen.cv.rotate(-58)
    _cone2d(pen, 0, 0, 2.6, t)
    pen.cv.restore()
    if wrapper:
        pen.cv.save(); pen.cv.translate(1260, 880); pen.cv.rotate(-6)
        tag = rrect(-230, -70, 460, 140, 10)
        pen.fill(moved(tag, 8, 12), '#000000', 90, blur=10); pen.fill(tag, '#f6f0e6'); pen.texture(tag, 'paper', 0.4, 'multiply', 1.0)
        btext(pen, 'Free.', 0, -10, 'script', 52, '#c23a78', 250, 'center')
        btext(pen, "For whoever's coldest.", 0, 44, 'cursive_b', 34, '#7a3a62', 250, 'center')
        pen.cv.restore()


def _cone2d(pen, x, y, s=1.0, t=0.0, broken=0.0):
    """The cone in 2D (insert scale, pointing +x): waffle cone, the wrapper, the swirl, frost vapour."""
    L = 260 * s
    cone = poly([(x, y - 60 * s), (x, y + 60 * s), (x + L, y)])
    pen.fill(cone, '#d8a868'); pen.line(cone, 2.5)
    for k in range(-5, 6):
        pen.seg((x + 20 * s, y + k * 12 * s), (x + L * 0.8, y - k * 3 * s), 1.2, '#a87838', 180)
        pen.seg((x + 20 * s, y - k * 12 * s), (x + L * 0.8, y + k * 3 * s), 1.2, '#a87838', 140)
    # review: the plain white sleeve read as a paper cup: a short pink-striped vendor wrapper with a scalloped edge,
    # under ONE soft-serve swirl (a single silhouette with its ridges, not loose eggs)
    wr = poly([(x - 4 * s, y - 66 * s), (x + 58 * s, y - 50 * s), (x + 58 * s, y + 50 * s), (x - 4 * s, y + 66 * s)])
    pen.fill(wr, '#f6eef2', 240)
    pen.cv.save(); pen.cv.clipPath(wr, skia.ClipOp.kIntersect, True)
    for k in range(-4, 5):
        pen.fill(poly([(x - 10 * s, y + (k * 30 - 8) * s), (x + 70 * s, y + (k * 30 + 12) * s), (x + 70 * s, y + (k * 30 + 24) * s), (x - 10 * s, y + (k * 30 + 4) * s)]), IC_STRIPE, 220)
    pen.cv.restore()
    pen.line(wr, 1.6, '#8a4a6a')
    for k in range(7):
        pen.fill(oval(x - 4 * s, y + (-60 + 20 * k) * s, 9 * s, 7 * s), '#f6eef2')
    base = smooth([(x + 4 * s, y - 74 * s), (x - 70 * s, y - 80 * s), (x - 160 * s, y - 62 * s), (x - 226 * s, y - 30 * s), (x - 252 * s, y),
                   (x - 226 * s, y + 30 * s), (x - 160 * s, y + 62 * s), (x - 70 * s, y + 80 * s), (x + 4 * s, y + 74 * s)], True)
    pen.fill(base, '#fbf3f6'); pen.line(base, 2.4, '#8a4a6a', 230)
    for i, (dx, r, c) in enumerate(((-40, 78, '#fbf3f6'), (-100, 68, IC_STRIPE), (-150, 56, '#fbf3f6'), (-192, 40, IC_STRIPE), (-222, 22, '#fbf3f6'))):
        sw = oval(x + dx * s, y + (6 if i % 2 else -6) * s, r * 0.62 * s, r * s)
        pen.fill(sw, c); pen.line(sw, 2.0, '#8a4a6a', 220)
        pen.line(smooth([(x + dx * s, y - r * 0.8 * s), (x + (dx - 14) * s, y), (x + dx * s, y + r * 0.8 * s)], False), 1.4, '#ffffff', 150)
    for i in range(6):
        ph = (t * 0.35 + i / 6) % 1.0
        pen.fill(oval(x - 120 * s - ph * 60 * s, y + (i - 3) * 30 * s + ph * 140 * s, (30 + 60 * ph) * s, (20 + 30 * ph) * s), '#ffffff', 70 * (1 - ph), blur=20 * s)


def _ici_wrapper(pen, t, **kw):
    _ibg_b(pen, '#cad6ee', '#8a9ac4', 120); pen.texture(rect(*_IBGB), 'grunge', 0.3, 'overlay', 2.0)
    pen.radial(None, 1500, 100, 1300, [(0, IC_PINK, 80), (1, IC_PINK, 0)])
    pen.cv.save(); pen.cv.translate(960, 540); pen.cv.rotate(-4)
    tag = rrect(-640, -230, 1280, 460, 20)
    pen.fill(moved(tag, 16, 24), '#000000', 100, blur=24); pen.fill(tag, '#f6f0e6'); pen.texture(tag, 'paper', 0.45, 'multiply', 1.0)
    pen.line(rrect(-610, -200, 1220, 400, 14), 3, IC_STRIPE, 200)
    btext(pen, 'Free.', 0, -30, 'script', 160, '#c23a78', 252, 'center')
    btext(pen, "For whoever's coldest.", 0, 130, 'cursive_b', 96, '#7a3a62', 252, 'center')
    for (fx, fy) in ((-520, -140), (520, 140)): pen.fill(_flake_path(fx, fy, 40), '#e58fb4', 200)
    pen.cv.restore()


def _ici_shatter(pen, t, brk=1.0, **kw):
    """The cone hitting the floorboards and shattering like glass (brk 0 = whole, about to hit .. 1 = in pieces)."""
    _ibg_b(pen, '#4a3020', '#1a100a', 130); pen.texture(rect(*_IBGB), 'wood', 0.6, 'overlay', 1.0, 0)
    for k in range(8): pen.fill(rect(-520, -400 + k * 230, 2960, 3), '#000000', 100)
    pen.fill(rect(-520, -400, 2960, 1900), '#1a2448', 90)
    if brk < 0.05:
        pen.cv.save(); pen.cv.translate(940, 560); pen.cv.rotate(-30); _cone2d(pen, -130, 0, 2.2, t); pen.cv.restore(); return
    rng = np.random.default_rng(5)
    pen.fill(oval(960, 640, 380 * brk, 90 * brk), '#000000', 60, blur=20)
    for i in range(70):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(40, 560) * brk
        x, y = 960 + math.cos(a) * r, 620 + math.sin(a) * r * 0.42
        sz = rng.uniform(10, 46) * (1.2 - 0.5 * brk)
        c = ('#f7c6dc', '#fbf3f6', '#e58fb4', '#d8a868', '#ffffff')[i % 5]
        sh = poly([(x - sz, y), (x - sz * 0.1, y - sz * 1.1), (x + sz, y - sz * 0.2), (x + sz * 0.3, y + sz * 0.7)])
        pen.cv.save(); pen.cv.translate(x, y); pen.cv.rotate(rng.uniform(0, 360)); pen.cv.translate(-x, -y)
        pen.fill(sh, c, 240); pen.line(sh, 1.5, '#ffffff', 180); pen.line(sh, 0.8, '#5a3a4a', 120)
        pen.cv.restore()
    for i in range(14):                                                        # the glassy ring of the impact
        a = 2 * math.pi * i / 14
        pen.seg((960, 620), (960 + math.cos(a) * 520 * brk, 620 + math.sin(a) * 210 * brk), 1.4, '#ffffff', 60 * (1.0 - brk * 0.6))
    pen.fill(oval(960, 620, 240 * brk, 60 * brk), '#ffffff', 50 * (1 - brk), blur=30)


def _phone2d(pen, x=960, y=540, s=1.0, tilt=-4.0):
    pen.cv.save(); pen.cv.translate(x, y); pen.cv.rotate(tilt); pen.cv.scale(s, s)
    body = rrect(-290, -560, 580, 1120, 64)
    pen.fill(moved(body, 14, 22), '#000000', 110, blur=24); pen.fill(body, '#16161c'); pen.line(body, 3, '#4a4a54')
    scr = rrect(-270, -540, 540, 1080, 50)
    return scr


def _ici_phone(pen, t, time_='11:47', bars=0, **kw):
    """Adam's phone in the dark: NO BARS (No Service), the time, the battery; the screen lights his fingers."""
    _ibg_b(pen, '#141a2e', '#05070e', 160)
    scr = _phone2d(pen)
    pen.linear(scr, 0, -540, 0, 540, [(0, '#1e2a4a'), (1, '#0c1222')])
    btext(pen, time_, 0, -250, 'sans', 150, '#f4f6ff', 250, 'center')
    btext(pen, 'Saturday, January 17', 0, -170, 'sans', 34, '#c8d0e8', 230, 'center')
    for i in range(4):                                                         # the signal bars: empty
        r = rect(-238 + i * 22, -490 - i * 9, 14, 18 + i * 9)
        pen.fill(r, '#f4f6ff', 230 if i < bars else 50)
    btext(pen, 'No Service' if bars == 0 else 'LTE', -150, -486, 'sans_b', 26, '#f4f6ff', 240)
    pen.fill(rrect(170, -500, 60, 26, 6), '#f4f6ff', 70); pen.fill(rrect(172, -498, 20, 22, 4), '#ff5a4a', 230)
    if bars == 0:
        card = rrect(-230, 60, 460, 150, 26)
        pen.fill(card, '#2a3450', 230)
        btext(pen, 'No Service', 0, 130, 'sans_b', 40, '#ffffff', 250, 'center')
        btext(pen, 'Calls and data unavailable', 0, 180, 'sans', 28, '#c8d0e8', 235, 'center')
    pen.cv.restore()
    pen.glow(960, 540, 700, '#8aa8ff', 40)


def _ici_card(pen, t, time_='Eleven-oh-two.', temp='Minus thirty-three.', sub=None, **kw):
    """A time / temperature card: frost-rimmed dark glass, the time and the temperature in big frosty type, a small
    thermometer (the narration's words exactly, e.g. 'Eleven-oh-two.' / 'Minus thirty-three.')."""
    _ibg_b(pen, '#0e1630', '#04060e', 170)
    rng = np.random.default_rng(7)
    for i in range(160):                                                       # frost creeping in from the edges
        ed = i % 4
        x, y = ((rng.uniform(-200, 120), rng.uniform(-100, 1180)), (rng.uniform(1800, 2120), rng.uniform(-100, 1180)),
                (rng.uniform(-100, 2020), rng.uniform(-150, 90)), (rng.uniform(-100, 2020), rng.uniform(990, 1230)))[ed]
        a = rng.uniform(0, 2 * math.pi); L = rng.uniform(40, 160)
        pts = [(x, y)]
        for j in range(4): x += math.cos(a) * L / 4; y += math.sin(a) * L / 4; a += rng.uniform(-0.5, 0.5); pts.append((x, y))
        pen.line(smooth(pts, False), 2.0, '#dfe8ff', 140)
    if time_: btext(pen, time_, 960, 470, 'head', 150, '#eef4ff', 252, 'center', spacing=0.02)
    if temp: btext(pen, temp, 960, 650, 'head_r', 100, '#9ab8ff', 250, 'center', spacing=0.02)
    if sub: btext(pen, sub, 960, 770, 'head_r', 54, '#c8d4f0', 230, 'center')
    tx, ty = 1640, 540                                                          # the thermometer
    pen.fill(rrect(tx - 18, ty - 260, 36, 480, 18), '#e8eef8', 220); pen.line(rrect(tx - 18, ty - 260, 36, 480, 18), 2)
    pen.fill(oval(tx, ty + 240, 34), '#3a6aff'); pen.fill(rect(tx - 7, ty + 120, 14, 130), '#3a6aff')
    for k in range(9): pen.seg((tx + 22, ty - 230 + k * 50), (tx + 40, ty - 230 + k * 50), 2, '#c8d4f0')


def _ici_radio(pen, t, talk=0.0, static=0.0, held=False, **kw):
    """Dad's radio close: a chunky orange two-way radio, channel 3 on its little screen, the LED (talk 0..1: green when
    a voice comes through), the grille; static 0..1: a jittery noise band on the screen. held: in Adam's hand (no
    table: the dark room behind, the radio tilted toward his ear; film.py draws the hand gripping it)."""
    if held:
        _ibg_b(pen, '#221c2a', '#08070c', 140)
        pen.radial(None, 900, 420, 900, [(0, '#3a3448', 120), (1, '#0c0a10', 0)])
    else:
        _ibg_b(pen, '#2a2030', '#0c0a10', 140)
        pen.fill(rect(-460, 700, 2840, 700), '#4a3020'); pen.texture(rect(-460, 700, 2840, 700), 'wood', 0.5, 'overlay', 1.0, 0)
    pen.cv.save(); pen.cv.translate(980, 560 if not held else 500); pen.cv.rotate(-8 if not held else -14)
    body = rrect(-230, -420, 460, 840, 60)
    pen.fill(moved(body, 20, 30), '#000000', 120, blur=30); pen.fill(body, '#e8761a'); pen.texture(body, 'grunge', 0.4, 'overlay', 1.2)
    pen.fill(rrect(-170, -610, 60, 220, 24), '#1a1a1a'); pen.fill(rrect(90, -470, 70, 60, 14), '#2a2a2a')
    pen.fill(rrect(-190, -380, 380, 300, 30), '#1a1a1e')
    for k in range(9):
        for j in range(7): pen.fill(oval(-150 + k * 38, -340 + j * 38, 9), '#050506')
    pen.fill(rrect(-170, -40, 340, 150, 14), '#9ab890'); pen.line(rrect(-170, -40, 340, 150, 14), 3)
    btext(pen, 'CH 3', 0, 70, 'vhs', 110, '#1a2a1a', 240, 'center')
    if static > 0.01:
        rng = np.random.default_rng(int(t * 30))
        for i in range(30): pen.fill(rect(-160 + rng.uniform(0, 300), -30 + rng.uniform(0, 130), rng.uniform(4, 40), 3), '#1a2a1a', 160 * static)
    pen.fill(oval(130, -470, 18), '#3aff6a' if talk > 0.01 else '#2a3a2a', 255 if talk > 0.01 else 200)
    if talk > 0.01: pen.glow(1110, 120, 80, '#3aff6a', 120 * talk)
    pen.fill(rrect(-200, 160, 400, 200, 20), '#c8621a'); btext(pen, 'PUSH TO TALK', 0, 280, 'head', 38, '#2a1a0a', 220, 'center')
    pen.cv.restore()


def _ici_mittens(pen, t, lina=False, drop=0.0, **kw):
    """The mitten bunting close, inside the pink window: single children's mittens on clothes pegs along a string, the
    oldest small and RED at the left; Lina's yellow one added at the right (lina); drop 0..1: hers falling away."""
    _ibg_b(pen, '#ffd0e4', '#e070a8', 60)
    pen.radial(None, 960, 480, 1300, [(0, '#fff0f6', 200), (1, '#ff9ec8', 0)])
    for (x0, y0, w, h) in ((-460, -320, 2840, 150), (-460, 1180, 2840, 220), (-460, -320, 140, 1720), (2240, -320, 140, 1720)):
        pen.fill(rect(x0, y0, w, h), '#f4f0f2')
    ms = list(IC_MITTENS) + ([IC_LINA_MITTEN] if lina else [])
    n = len(ms)
    pts = [(-200 + 2320 * f, 260 + 160 * math.sin(math.pi * f)) for f in np.linspace(0, 1, 40)]
    pen.line(smooth(pts, False), 5, '#f8f0e8', 240); pen.line(smooth(pts, False), 1.5, '#a89888', 200)
    for i, c in enumerate(ms):
        f = 0.155 + 0.69 * (i + 0.5) / n
        x = -200 + 2320 * f; y = 260 + 160 * math.sin(math.pi * f)
        sc = 140 if i == 0 else 190
        sw = 4 * math.sin(t * 1.2 + i)
        fall = i == n - 1 and lina and drop > 0
        if fall:                                       # film pass 2: the peg stays on the string; the mitten slips out and tumbles
            pen.fill(rrect(x - 10, y - 16, 20, 46, 4), '#e8dcc8'); pen.line(rrect(x - 10, y - 16, 20, 46, 4), 1.4)
            y += 1100 * drop ** 2 + 40 * drop; sw += 160 * drop ** 1.5; x += 60 * drop
        pen.cv.save(); pen.cv.translate(x, y); pen.cv.rotate(sw)
        m = union(rrect(-sc * 0.38, sc * 0.16, sc * 0.76, sc * 0.92, sc * 0.36), oval(sc * 0.37, sc * 0.52, sc * 0.17, sc * 0.27))
        pen.fill(moved(m, 10, 14), '#7a2a4a', 90, blur=10)
        pen.fill(m, c); pen.texture(m, 'fabric', 0.7, 'overlay', 0.7)
        for k in range(5): pen.line(smooth([(-sc * 0.3, sc * (0.35 + 0.12 * k)), (0, sc * (0.38 + 0.12 * k)), (sc * 0.3, sc * (0.35 + 0.12 * k))], False), 1.4, '#000000', 50)
        pen.line(m, 2.4, '#2a1018', 220)
        pen.fill(rect(-sc * 0.42, sc * 0.88, sc * 0.84, sc * 0.22), mix(c, '#ffffff', 0.45)); pen.line(rect(-sc * 0.42, sc * 0.88, sc * 0.84, sc * 0.22), 1.5, '#2a1018', 180)
        if not fall: pen.fill(rrect(-10, -16, 20, 46, 4), '#e8dcc8'); pen.line(rrect(-10, -16, 20, 46, 4), 1.4)
        pen.cv.restore()
    pen.fill(rect(*_IBGB), '#ffffff', 18)


def _ici_boot(pen, t, **kw):
    """Adam's boot frozen upright in the snow where he stood (one sock gone with him), rimed with ice, pink light."""
    _ibg_b(pen, '#c8d4ee', '#6a7aa8', 120); pen.texture(rect(*_IBGB), 'grunge', 0.35, 'overlay', 3.0)
    pen.radial(None, 1700, 100, 1500, [(0, IC_PINK, 90), (1, IC_PINK, 0)])
    pen.fill(oval(960, 840, 360, 80), '#3a4a7a', 140, blur=20)
    sh = rrect(780, 240, 360, 640, 60)
    pen.fill(sh, '#3a2a22'); pen.texture(sh, 'fabric', 0.6, 'overlay', 1.0); pen.line(sh, 4)
    pen.fill(rrect(760, 200, 400, 110, 40), '#d8d0c0'); pen.texture(rrect(760, 200, 400, 110, 40), 'fabric', 0.8, 'overlay', 1.0); pen.line(rrect(760, 200, 400, 110, 40), 3)
    for k in range(6):
        y = 360 + k * 70
        pen.seg((820, y), (1100, y + 30), 6, '#d8cca8'); pen.seg((820, y + 30), (1100, y), 6, '#c8bc98')
    pen.fill(poly([(600, 900), (1320, 900), (1300, 780), (1140, 820), (960, 760), (780, 820), (620, 780)]), '#eef4ff')
    for i in range(40):
        x = 760 + i * 10; pen.seg((x, 820), (x + 5, 870), 2, '#ffffff', 160)
    pen.line(rrect(780, 240, 360, 640, 60), 8, '#ffffff', 60, blur=4)


def _child_hand(pen, x, y, s=1.0, rot=0.0, waxy=1.0, skin='#e8b898', sleeve='#f2c23a'):
    """Lina's small bare hand, palm up, fingers slightly curled: shaded skin, knuckle creases, nails, the cuff of her
    yellow coat; waxy 0..1 turns the fingertips white and waxy (frostbite: subtle, never gory)."""
    pen.cv.save(); pen.cv.translate(x, y); pen.cv.rotate(rot); pen.cv.scale(s, s)
    pen.fill(rrect(-260, -90, 280, 190, 60), sleeve); pen.texture(rrect(-260, -90, 280, 190, 60), 'fabric', 0.6, 'overlay', 0.8); pen.line(rrect(-260, -90, 280, 190, 60), 3)
    pen.fill(rrect(-40, -70, 60, 150, 26), mix(sleeve, '#ffffff', 0.2)); pen.line(rrect(-40, -70, 60, 150, 26), 2)
    palm = rrect(0, -80, 230, 170, 80)
    pen.fill(palm, skin)
    pen.linear(palm, 0, -80, 0, 90, [(0, '#ffffff', 40), (1, '#a86a5a', 70)])
    fingers = [(-56, 150), (-18, 175), (20, 168), (58, 140)]
    for i, (fy, L) in enumerate(fingers):
        f = rrect(200, fy - 19, L, 38, 19)
        pen.fill(f, skin); pen.linear(f, 0, fy - 19, 0, fy + 19, [(0, '#ffffff', 30), (1, '#a86a5a', 80)])
        tip = rrect(200 + L - 56, fy - 19, 56, 38, 19)
        if waxy > 0.01:
            pen.fill(tip, '#f4f2ec', 235 * waxy); pen.fill(tip, '#dfe4ec', 80 * waxy)
            pen.line(smooth([(200 + L - 56, fy - 16), (200 + L - 62, fy), (200 + L - 56, fy + 16)], False), 2, '#c8b8b0', 160 * waxy)
        pen.fill(rrect(200 + L - 26, fy - 12, 20, 24, 9), '#f8e0d8' if waxy < 0.5 else '#f8f6f2', 230)
        for k_ in (0.45, 0.72): pen.seg((200 + L * k_, fy - 12), (200 + L * k_ + 4, fy + 12), 1.6, '#9a6a5a', 120)
        pen.line(f, 2.2, '#6a3a2a', 200)
    th = rrect(60, 70, 150, 44, 22)
    pen.cv.save(); pen.cv.translate(80, 70); pen.cv.rotate(28); pen.cv.translate(-80, -70)
    pen.fill(th, skin); pen.line(th, 2.2, '#6a3a2a', 200)
    if waxy > 0.01: pen.fill(rrect(160, 70, 50, 44, 22), '#f4f2ec', 225 * waxy)
    pen.cv.restore()
    pen.line(smooth([(40, -30), (120, -10), (190, -40)], False), 2, '#9a6a5a', 120)
    pen.line(palm, 2.4, '#6a3a2a', 220)
    pen.cv.restore()


def _ici_fingers(pen, t, waxy=1.0, **kw):
    """Lina's fingertips: white, waxy (Adam does NOT rub them: he tucks them under his arms). Phone light, cold."""
    _ibg_b(pen, '#1a2240', '#080c18', 150)
    pen.fill(rect(-460, -320, 2840, 1720), '#2a3a6a', 120); pen.texture(rect(-460, -320, 2840, 1720), 'fabric', 0.5, 'overlay', 1.2)
    pen.radial(None, 900, 520, 900, [(0, '#c8d8ff', 70), (1, '#c8d8ff', 0)])
    _child_hand(pen, 620, 560, 2.0, -8.0, waxy)


def _ici_towel(pen, t, press=1.0, tip=1.0, **kw):
    """Low at the bathroom door from inside: the door's bottom edge, the gap, the towels stuffed in; a needle-thin brown
    jointed leg tip (frost on the joint) sliding in under them; press 0..1: the towel jammed down hard on it."""
    _ibg_b(pen, '#2a3040', '#0a0c14', 140)
    pen.fill(rect(-460, -320, 2840, 900), '#d8d4cc'); pen.texture(rect(-460, -320, 2840, 900), 'wood', 0.3, 'overlay', 1.0, 90)
    pen.fill(rect(-460, -320, 2840, 900), '#1a2448', 140)
    pen.fill(rect(-460, 580, 2840, 30), '#05060a')
    pen.fill(rect(-460, 610, 2840, 800), '#e8e4dc'); pen.fill(rect(-460, 610, 2840, 800), '#1a2448', 120)
    for k in range(30):
        for j in range(8): pen.line(rect(-460 + k * 100, 610 + j * 100, 100, 100), 1.5, '#5a6070', 120)
    if tip > 0.01:
        L = 700 * tip
        leg = poly([(1180, 590), (1180 - L, 640), (1180 - L - 40, 650), (1180 - L, 660), (1180, 610)])
        pen.fill(leg, '#5a3a22'); pen.line(leg, 2)
        pen.fill(oval(1180 - L * 0.45, 640, 22, 16), '#6a4a2e'); pen.line(oval(1180 - L * 0.45, 640, 22, 16), 2)
        pen.fill(oval(1180 - L * 0.45, 632, 16, 7), '#eef4ff', 220)
        pen.seg((1180 - L - 40, 650), (1180 - L - 70, 652), 2, '#3a2412')
    yb = 560 + 70 * press
    tw = rrect(300, yb - 80, 1400, 160, 60)
    pen.fill(moved(tw, 0, 20), '#000000', 90, blur=20)
    pen.fill(tw, '#7aa0c8'); pen.texture(tw, 'fabric', 0.8, 'overlay', 0.8); pen.line(tw, 3)
    for k in range(14): pen.seg((340 + k * 100, yb - 60), (360 + k * 100, yb + 60), 2, '#5a80a8', 120)
    if tip > 0.01:                                                             # the tip sticks out from under the towel's front edge
        L = 420 * tip
        A = (1050, yb + 70); Bt = (1050 - L, yb + 70 + L * 0.42)
        leg = poly([(A[0] + 12, A[1] - 14), (A[0] - 12, A[1] + 12), (Bt[0] + 4, Bt[1] + 2), (Bt[0] - 10, Bt[1] + 6), (Bt[0] + 6, Bt[1] - 4)])
        pen.fill(leg, '#5a3a22'); pen.line(leg, 2)
        J = (A[0] - L * 0.42, A[1] + L * 0.42 * 0.42)
        pen.fill(oval(J[0], J[1], 22, 17), '#6a4a2e'); pen.line(oval(J[0], J[1], 22, 17), 2)
        pen.fill(oval(J[0], J[1] - 8, 16, 7), '#eef4ff', 220)
        pen.seg(Bt, (Bt[0] - 30, Bt[1] + 10), 2, '#3a2412')
    pen.radial(None, 700, 900, 900, [(0, '#c8d8ff', 60), (1, '#c8d8ff', 0)])


def _ici_doorknob(pen, t, frost=1.0, **kw):
    """Our front doorknob from inside, growing frost (frost 0..1 or f(t)): a brass knob, the frost feathering out over it."""
    k = frost(t) if callable(frost) else frost
    _ibg_b(pen, IC_PAL['door'], _darken(IC_PAL['door'], 0.4), 140); pen.texture(rect(*_IBGB), 'wood', 0.35, 'overlay', 1.2, 90)
    pen.fill(oval(960, 560, 260), '#b89a5a'); pen.line(oval(960, 560, 260), 3)
    pen.fill(oval(960, 560, 200), '#c8a868'); pen.radial(oval(960, 560, 200), 880, 480, 260, [(0, '#fff0c0', 180), (1, '#6a5020', 60)])
    pen.fill(oval(960, 560, 60), '#a88a48')
    rng = np.random.default_rng(9)
    pen.fill(oval(960, 560, 270), '#e8f2ff', 120 * k)
    for i in range(int(260 * k)):
        a = rng.uniform(0, 2 * math.pi); r0 = rng.uniform(0, 260); L = rng.uniform(20, 90) * k
        x, y = 960 + math.cos(a) * r0, 560 + math.sin(a) * r0
        b = a + rng.uniform(-1.2, 1.2)
        pen.seg((x, y), (x + math.cos(b) * L, y + math.sin(b) * L), 2.0, '#ffffff', 190)
        for sd in (-1, 1): pen.seg((x + math.cos(b) * L * 0.5, y + math.sin(b) * L * 0.5), (x + math.cos(b + sd * 0.8) * L * 0.8, y + math.sin(b + sd * 0.8) * L * 0.8), 1.2, '#ffffff', 150)


def _ici_outro(pen, t, n=0, **kw):
    """The outro advice cards (warm, safe, legible): n 0..4 = IC_OUTRO[n] (lead-in, the instruction in big type, detail)."""
    _ibg_b(pen, '#8a5a34', '#4a2c18', 120); pen.texture(rect(*_IBGB), 'wood', 0.4, 'overlay', 1.0, 0)
    pen.radial(None, 960, 300, 1400, [(0, '#ffc880', 70), (1, '#ffc880', 0)])
    lead, big, det = IC_OUTRO[n]
    card = rrect(200, 170, 1520, 740, 40)
    pen.fill(moved(card, 14, 22), '#000000', 120, blur=24); pen.fill(card, '#f6eedf'); pen.line(card, 4, '#a87a48')
    y = 330
    for ln in _wrap(lead, 52): btext(pen, ln, 960, y, 'sans_b', 50, '#3a2414', 252, 'center'); y += 64
    y += 40
    bl = _wrap(big, 30); bs = 88.0                                    # fit every line inside the card (n=4 overflowed)
    while bs > 52 and max(btext_width(ln, 'head', bs) for ln in bl) > 1400:
        bs -= 4.0
        if bs <= 72 and len(bl) < 3: bl = _wrap(big, 22)
    for ln in bl: btext(pen, ln, 960, y, 'head', bs, '#a01c1e', 255, 'center'); y += bs * 1.18
    y += 20
    for ln in _wrap(det, 56): btext(pen, ln, 960, y, 'sans', 46, '#2a1a10', 252, 'center'); y += 60
    pen.fill(_flake_path(300, 260, 44), '#e8b070', 160)


def _ici_plow_cab(pen, t, beacon=1.0, talk=0.0, **kw):
    """Dad's plow cab at night: the windshield onto a snowy road in his headlights, the wipers, the orange beacon's sweep
    on the hood, the radio handset on its coil cord (talk: its LED)."""
    _ibg_b(pen, '#0a0c14', None, 0)
    ws = poly([(-100, 80), (2020, 80), (1900, 700), (20, 700)])
    pen.linear(ws, 0, 80, 0, 700, [(0, '#0a1430'), (0.55, '#2a3a6a'), (1, '#c8d4ee')])
    pen.fill(poly([(860, 430), (1060, 430), (1700, 700), (220, 700)]), '#e8eef8', 220)
    for k in range(5): pen.line(poly([(960 - 10 * k, 430), (960 - 160 * k - 200, 700)], False), 2, '#9aa8c8', 120)
    rng = np.random.default_rng(int(t * 24) % 1000)
    for i in range(90):
        x, y = rng.uniform(0, 1920), rng.uniform(80, 700)
        pen.fill(oval(x, y, rng.uniform(1, 3)), '#ffffff', 200)
    ang = t * 1.3 * 2 * math.pi; kb = beacon * max(0.0, math.cos(ang)) ** 2
    pen.radial(None, 960, 760, 1200, [(0, IC_ORANGE, 160 * kb), (1, IC_ORANGE, 0)])
    pen.fill(minus(rect(-460, -320, 2840, 1720), ws), '#1a1c22')
    pen.fill(rect(-460, 700, 2840, 700), '#2a2c32'); pen.fill(rect(-460, 700, 2840, 18), '#3a3c44')
    for (bx, a) in ((560, -24 + 18 * math.sin(t * 2.0)), (1360, -24 + 18 * math.sin(t * 2.0))):
        ex, ey = bx + 520 * math.cos(math.radians(180 + a)), 690 + 520 * math.sin(math.radians(180 + a))
        pen.seg((bx, 690), (ex, ey), 9, '#0a0a0a')
    pen.fill(rrect(1500, 760, 150, 250, 30), '#1a1a1a'); pen.line(rrect(1500, 760, 150, 250, 30), 2, '#3a3a3a')
    pen.fill(oval(1575, 800, 12), '#3aff6a' if talk > 0.01 else '#2a3a2a')
    pen.line(smooth([(1575, 1010), (1540, 1080), (1600, 1150), (1530, 1220), (1590, 1300)], False), 6, '#141414')
    pen.fill(rrect(300, 760, 520, 120, 16), '#141418'); btext(pen, 'CH 3', 560, 840, 'vhs', 70, '#ff9a3a', 230, 'center')


IC_INSERTS = {
    'rules': (_ici_rules, 'ic_ins', 'the seven rules taped to a door, shaky capitals, signed W.K. (show n, hl k, eighth, door ours|kessler)'),
    'rule': (_ici_rule, 'ic_ins', 'one rule as a full card, legible (n 1..7 Kessler, 8 Adam; write 0..1)'),
    'doormat': (_ici_doormat, 'ic_ins_cold', 'the cone on our doormat, steaming with cold, its wrapper "Free. For whoever\'s coldest."'),
    'wrapper': (_ici_wrapper, 'ic_ins_cold', 'the wrapper close: "Free. For whoever\'s coldest."'),
    'shatter': (_ici_shatter, 'ic_ins', 'the cone hits the floor and shatters like glass (brk 0..1)'),
    'phone': (_ici_phone, 'ic_ins_cold', 'the phone: No Service, no bars (time_, bars)'),
    'card': (_ici_card, 'ic_ins_cold', "a time / temperature card (time_ 'Eleven-oh-two.', temp 'Minus thirty-three.', sub)"),
    'radio': (_ici_radio, 'ic_ins', "Dad's radio close: CH 3 (talk 0..1: LED; static 0..1)"),
    'mittens': (_ici_mittens, 'ic_ins', 'the mitten string in the pink window (lina: hers added at the right; drop 0..1)'),
    'boot': (_ici_boot, 'ic_ins_cold', "Adam's boot frozen in the snow"),
    'fingers': (_ici_fingers, 'ic_ins_cold', "Lina's white, waxy fingertips (waxy 0..1)"),
    'towel': (_ici_towel, 'ic_ins_cold', 'the towel jammed down on the leg tip under the bathroom door (press, tip 0..1)'),
    'doorknob': (_ici_doorknob, 'ic_ins_cold', 'the doorknob growing frost (frost 0..1 or f(t))'),
    'outro': (_ici_outro, 'ic_ins_warm', 'the outro advice cards (n 0..4), warm and legible'),
    'plow_cab': (_ici_plow_cab, 'ic_ins', "Dad's plow cab: windshield, wipers, the beacon on the hood, the handset (talk)"),
}


def ic_insert(name, prop_kw=None, motion=None, t0=0.0, grade=None):
    """A close-up insert from IC_INSERTS (flat 1920 x 1080 design space with margin for a drift): prop_kw dict (values
    may be f(t)) or f(t) -> dict; motion f(t) -> (dx, dy, dscale, drot)."""
    fn, gr, note = IC_INSERTS[name]
    static = not callable(prop_kw) and motion is None and not any(callable(v_) for v_ in (prop_kw or {}).values()) and name not in ('doormat', 'mittens', 'radio', 'plow_cab', 'phone')

    def draw(pen, t):
        kw = prop_kw(t) if callable(prop_kw) else dict(prop_kw or {})
        kw = {k_: (v_(t) if callable(v_) and k_ not in ('frost',) else v_) for k_, v_ in kw.items()}
        cv = pen.cv
        if motion is not None:
            dx, dy, ds, dr = motion(t)
            cv.save(); cv.translate(960 + dx, 540 + dy); cv.rotate(dr); cv.scale(1 + ds, 1 + ds); cv.translate(-960, -540)
        fn(pen, t - t0, **kw)
        if motion is not None: cv.restore()
    key = 'icins:%s:%s' % (name, _okey(prop_kw or {}) if isinstance(prop_kw, dict) else 'f')
    lay = Layer(1.0, draw, 'insert', cache=key if static else False, bounds=(-460, -320, 2380, 1400), blur=0)
    return BSet('ic_ins_' + name, [lay], {}, {}, lens=None, grade=grade or gr, focus=1.0, dof=0.0, cover=(-460, -320, 2380, 1400), info={'note': note})


# ====================================================================================================== the plan map, the registry
def _ic_plan_panels():
    def blocks(*sets_):
        b = {}
        for sp_ in sets_:
            for k_, q in (sp_.info.get('blocks') or {}).items():
                if not k_.startswith('far_') and q: b[k_] = q
        return b

    def marks(sp_, names):
        return [(sp_.anchors[n].X, sp_.anchors[n].Yp, n) for n in names if n in sp_.anchors]
    lv, hl, kt, bt = ic_living('wide'), ic_hall('door'), ic_kitchen('window'), ic_bath('door')
    P = [dict(title='OUR HOUSE  (floor Y 0, ceiling %.2f; one storey + attic)' % IC_CEIL, ext=(-7.0, 7.0, -2.6, 9.6), ray=1.2,
              floors=[('LIVING ROOM', IC_LIV_POLY), ('HALL', _r4p(IC_HALL)), ('KITCHEN', _r4p(IC_KIT)), ('BATH', _r4p(IC_BATH)), ('stoop', _r4p(IC_PORCH)),
                      ('hatch (ceiling)', _r4p(IC_HATCH)), ('bedrooms (not built)', _r4p((-6.4, -2.8, 4.6, 9.0))), ('(not built)', _r4p((-1.4, 6.4, 5.6, 9.0)))],
              blocks=blocks(lv, hl, kt, bt),
              doors=[((IC_FDOOR[0], 0.0), (IC_FDOOR[1], 0.0), 'front door (glass)'), ((-1.4, IC_BDOOR[0]), (-1.4, IC_BDOOR[1]), 'bath'),
                     ((-1.4, IC_LOPEN[0]), (-1.4, IC_LOPEN[1]), 'opening'), ((-2.8, IC_KDOOR[0]), (-2.8, IC_KDOOR[1]), 'kitchen')],
              windows=[((IC_PWIN[0], 0.0), (IC_PWIN[1], 0.0)), ((IC_KWIN[0], 0.0), (IC_KWIN[1], 0.0)), ((IC_BWIN[0], 0.0), (IC_BWIN[1], 0.0))], lines=[],
              marks=marks(lv, ('couch_mid', 'radio', 'curtain_crack', 'tv_screen')) + marks(hl, ('door_in', 'under_hatch', 'bath_door_hall')) +
                    marks(kt, ('stool', 'sill_out')) + marks(bt, ('tub_sit', 'gap')),
              cams=[k for k in IC_CAMS if CAMS[k]['room'] in ('living', 'hall', 'kitchen', 'bath')])]
    ea, eb = ic_street('house', truck='A'), ic_street('kout', truck='B')
    bk = {'our house': _r4p(IC_HOUSE), "Kessler's": _r4p((IC_KH[0], IC_KH[1], IC_KH[2], IC_KH[3])), 'truck A': ea.info['blocks'].get('truck'),
          'truck B': eb.info['blocks'].get('truck'), "Dad's car": ea.info['blocks'].get('car')}
    P.append(dict(title='BIRCH LANE  (ground Y %.1f; snow %.2f m; truck A until 8:48, B from 8:50)' % (IC_G, IC_SNOW), ext=(-16.0, 14.0, -34.0, 10.0), ray=4.0,
                  floors=[('Birch Lane', [(-16, IC_KS), (14, IC_KS), (14, IC_KN), (-16, IC_KN)]), ('driveway', _r4p(IC_DRIVE)),
                          ("his porch", _r4p(IC_KPORCH)), ('our stoop', _r4p(IC_PORCH))],
                  blocks={k_: q for k_, q in bk.items() if q}, doors=[((IC_FDOOR[0], 0.0), (IC_FDOOR[1], 0.0), ''), ((IC_KDOOR2[0], IC_KH[3]), (IC_KDOOR2[1], IC_KH[3]), '')],
                  windows=[((IC_PWIN[0], 0.0), (IC_PWIN[1], 0.0)), ((IC_KWIN2[0], IC_KH[3]), (IC_KWIN2[1], IC_KH[3]))],
                  lines=[[(IC_FENCE_X[0], IC_FENCE_Y), (IC_GATE[0], IC_FENCE_Y)], [(IC_GATE[1], IC_FENCE_Y), (IC_FENCE_X[1], IC_FENCE_Y)]],
                  marks=marks(ea, ('truck_window', 'drop', 'boot', 'car_roof', 'lamp')) + marks(eb, ('truck_window', 'kdoor', 'kwalk_mid', 'cage')),
                  cams=[k for k in IC_CAMS if CAMS[k]['room'] == 'street']))
    return P


def ic_plan_map(path, pw=900, ph=1000, cols=2):
    """This film's floor plans with every camera -> JPEG (the Doctor film's renderer on this film's panels)."""
    import inspect
    src = inspect.getsource(dr_plan_map).replace('def dr_plan_map(', 'def _ic_plan_map_impl(').replace('_dr_plan_panels()', '_ic_plan_panels()')
    ns = dict(globals()); exec(src, ns)
    return ns['_ic_plan_map_impl'](path, pw, ph, cols)


IC_SETS = {'ic_street': ic_street, 'ic_living': ic_living, 'ic_hall': ic_hall, 'ic_kitchen': ic_kitchen, 'ic_bath': ic_bath, 'ic_1958': ic_1958,
           'ic_morning': ic_morning, 'ic_town': ic_town, 'ic_insert': ic_insert}
IC_API = {nm: sorted({k[len(pre):] for k in IC_CAMS if k.startswith(pre)}) for nm, pre in (
    ('ic_street', 'ic_ext_'), ('ic_living', 'ic_liv_'), ('ic_hall', 'ic_hall_'), ('ic_kitchen', 'ic_kit_'), ('ic_bath', 'ic_bath_'))}
IC_API['ic_insert'] = sorted(IC_INSERTS)
__all__ += ['ic_street', 'ic_living', 'ic_hall', 'ic_kitchen', 'ic_bath', 'ic_1958', 'ic_morning', 'ic_town', 'ic_insert', 'ic_plan_map', 'ic_pass', 'ic_flicker',
            'IC_API', 'IC_INSERTS', 'IC_RULES', 'IC_RULE8', 'IC_OUTRO', 'IC_TRUCK_A', 'IC_TRUCK_B', 'IC_CAMS', 'ic_cone', 'ic_boot', 'ic_mitten', 'ic_radio']
