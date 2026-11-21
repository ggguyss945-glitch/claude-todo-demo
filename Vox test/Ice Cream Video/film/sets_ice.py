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
  serving window facing his door. Kessler's window is seen past the truck's rear end from our living-room window.
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
IC_TV = (3.4, 5.42, 1.26, 0.74, 0.6)  # flat TV: centre x, y (screen plane), w, h, bottom Y; facing -y
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
IC_TRUCK_B = (1.43, -14.45, 90.0)
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
_GR.setdefault('ic_ins_warm', dict(exposure=0.03, contrast=1.02, pivot=0.26, gamma=1.04, sat=1.06, wb=(1.05, 1.0, 0.94), floor='#100c08',
                                   bloom=0.6, bloom_thr=232, vignette=0.45, grain=0.35, shoulder=0.55))

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
    snow = '#cad6ee' if night else '#f2eee8'
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
    return Piece(name, (cx, G + 1.5, cy), lambda pen, v, ps=parts: draw_parts(pen, v, ps), block=foot)


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
        far = (Pp[0] + bx * 12, Pp[2] + by * 12)
        if v.d(far[0], far[1]) > 0.5:
            ex, ey = v.p(far[0], G + 1.2, far[1])
            pen.line(poly([(x, y), (ex, ey)], False), max(4.0, 0.9 * s), IC_ORANGE, 40 * beacon, blur=max(4.0, 0.5 * s))
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
    c = '#aab4cc' if tod in ('night', '1958') else '#f2ece6'
    for i in range(9):
        ph = (t * 0.22 + i / 9.0 + rng.uniform(0, 0.05)) % 1.0
        P = (x + ph * 2.6 + 0.3 * math.sin(t * 0.7 + i), Y + 0.2 + ph * 3.2, y + ph * 0.8)
        if v.d(P[0], P[2]) < 0.5: continue
        px, py = v.p(*P); s = v.s(P[0], P[2])
        rr = (0.25 + ph * 0.9) * s
        pen.fill(oval(px, py, rr, rr * 0.8), c, 110 * k * (1 - ph) ** 1.2, blur=rr * 0.5)


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
            amb = '#8a8a98'
            steady = [Lamp(kind='dir', c='#ffe0b8', k=1.0, d=_norm3((-0.55, -0.45, 0.7)))]
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
                var.append(('pink', [Lamp(P[0], P[1], P[2], 9.0, IC_PINK, 1.7, (1.0, 1.0, 0.7), fall=1.25)], _kfn(o.get('truck_win', 1.0), 504)))
            pl = o.get('plow')
            if pl:
                x = pl.get('x', 0.0)
                xs = x if not callable(x) else 0.0
                ly = pl.get('y', IC_PLOW_LANE[0])
                var.append(('beacon', [Lamp(xs, IC_G + 3.2, ly, 16.0, IC_ORANGE, 1.6, fall=1.2)], _kfn(pl.get('beacon', ic_pass(0.0, 1e6)), 505)))
            ps = o.get('porches')
            if ps is not None:
                for i in range(4):
                    sp_ = ps[i] if isinstance(ps, (list, tuple)) else ps
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
            kn = [_kfn(nb[i] if isinstance(nb, (list, tuple)) else (nb if nb is not None else 0.0), 510 + i) for i in range(len(IC_NEIGHBOURS))]
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
                        pen.glow(x, y, 1.6 * s, '#ffc070', 120 * k); pen.glow(x, y, 0.12 * s, '#fff4d8', 250 * k)
                        gx, gy = v.p(P_[0], IC_SNOWY, P_[2] - 1.2 * H['face'])
                        pen.ellipse_glow(gx, gy, 2.0 * s, 0.5 * s, '#ffc070', 55 * k)
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
        M('kwalk_mid', 1.4, -19.6, G + (0.03 if o.get('kwalk') == 'shoveled' else IC_SNOW - IC_SINK), 'stand', "halfway up Kessler's walk (Mr. Kessler halfway to the window, facing north)", (0, 1))
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
                M('kessler_window_b', 1.42, -16.3, G + 0.02, 'stand', "Mr. Kessler at the pink window (position B), facing it", (0, 1))
                M('cage', 1.0, -18.2, IC_FOOT, 'stand', 'the kids under the blanket where his legs cage them (south of the truck)', (0, -1))
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
    sc = 0.17 * s
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
        sp = sp.add(_curtain_gap_layer(0.06))
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
_icam('ic_ext_kessler', 820, 520, 1.5, 3.2, -2.6, 186, _env(f=(1.0, 2.6)), "from our yard across the lane to Kessler's house: his window, his chimney (the truck at A on the right)", 'street')
_icam('ic_ext_lane', 860, 540, IC_G + 1.7, -19.0, -12.4, 90, _env(f=(1.0, 2.6)), 'down Birch Lane from the west: our house left, Kessler\'s right, the truck gliding in (no tracks behind)', 'street')
_icam('ic_ext_lane_e', 860, 540, IC_G + 1.7, 19.5, -11.6, -90, _env(f=(1.0, 2.6)), 'up Birch Lane from the east: our house right, Kessler\'s left', 'street')
_icam('ic_ext_truck', 760, 520, IC_G + 0.18 + 1.3, -3.6, -7.1, 116, _env(), 'the truck at A from our walk at child height: the serving window, the sign, the flake', 'street')
_icam('ic_ext_curb', 1000, 470, IC_G + 0.95, -1.5, -6.35, 160, _env(), 'low at the kerb, up at the serving window (he leans down, further than a man can bend)', 'street', pitch=-12.0)
_icam('ic_ext_window_close', 1650, 520, IC_G + 1.95, -0.58, -5.6, 180, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.1)), 'the truck window close-up: the pink glow, the frost, the mitten bunting', 'street')
_icam('ic_ext_door', 950, 520, IC_G + 1.5, -2.1, -5.4, 0, _env(), 'our front door from the walk: the stoop, the glass strip, the porch light', 'street')
_icam('ic_ext_yard', 700, 520, IC_G + 1.9, 2.0, -16.5, 16, _env(f=(1.0, 2.2)), "the yard wide from the lane: the fence, Dad's car, our roof (the chase route)", 'street')
_icam('ic_ext_roof', 760, 420, IC_G + 1.25, 1.2, -5.4, -8, _env(), 'up at our roof and eave from the yard (him on the roof)', 'street', pitch=-16.0)
_icam('ic_ext_kwide', 760, 520, IC_G + 1.6, 12.0, -20.6, -76, _env(), "Kessler's porch and the truck at B (its serving window facing his door)", 'street')
_icam('ic_ext_kporch', 900, 520, IC_G + 1.5, 2.6, -17.2, 196, _env(), "Kessler's porch and door from his walk", 'street')
_icam('ic_ext_kdoor', 980, 520, IC_G + 1.25, 1.6, -20.0, 182, _env(), "close on Kessler's doorway at child height (the huddle)", 'street')
_icam('ic_ext_kout', 820, 520, IC_KFLOOR + 1.45, 1.4, -23.2, 2, _env(), "from Kessler's doorway out: the truck at B, its pink window facing us, our house across the lane", 'street')
_icam('ic_ext_bathout', 900, 540, 1.55, -0.5, 0.25, 176, _env(x=(940, 980), y=(520, 560), zoom=(1.0, 1.03)), 'POV through our bathroom window across the lane to Kessler\'s door', 'street')
_icam('ic_ext_plow', 820, 520, IC_G + 1.6, -6.0, -4.6, 162, _env(), "the plow passing on Birch Lane (the orange beacon sweeping), from our yard", 'street')
_icam('ic_ext_gap', 1050, 520, 1.25, 3.4, 0.3, 182, _env(x=(920, 1000), y=(500, 560), zoom=(1.0, 1.06)), 'POV through the curtain crack: the truck at A, Kessler\'s window beyond', 'street')


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
    var.append(_phone_lamp(o, seed + 2)); var.append(_flash_lamp(o, seed + 3))
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
    def draw(pen, t):
        pf = v.poly3(fq)
        if not pf.isEmpty():
            b = pf.computeTightBounds()
            k = kp(t)
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


def ic_hatch(pen, v, k=0.0):
    """The attic hatch in the hall ceiling: k 0 closed (a flush panel, a pull cord) .. 1 dropped open (the panel hangs
    from its far hinge; the dark attic above, rafters)."""
    x0, x1, y0, y1 = IC_HATCH
    C = IC_CEIL
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
        pen.fill(rect(cxk - W * 0.01, wy0, W * 0.02, wy1 - wy0), mix('#8aa0d0', IC_PINK, pk), 150)
    pen.fill(rrect(b.left() + W * 0.1, b.top() + H * 0.6, W * 0.8, H * 0.5, H * 0.12), '#0e1014', 230)
    if skull > 0.01:                                                           # glimpse 2: in the crack, a long white skull
        sx, sy = cxk, wy0 + (wy1 - wy0) * 0.45
        sk = poly([(sx - W * 0.012, sy - H * 0.1), (sx + W * 0.012, sy - H * 0.1), (sx + W * 0.009, sy + H * 0.1), (sx, sy + H * 0.14), (sx - W * 0.009, sy + H * 0.1)])
        pen.fill(sk, '#ece8e0', 230 * skull, blur=1.5)
        for dx in (-1, 1): pen.fill(oval(sx + dx * W * 0.005, sy - H * 0.05, W * 0.0035), '#ff2020', 250 * skull)
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
