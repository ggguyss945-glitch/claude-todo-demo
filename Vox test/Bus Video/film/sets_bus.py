"""sets_bus.py: the sets of "If The School Bus Stops At Midnight... DON'T GET ON" (Night Policy).

Run inside sets.py's namespace at import, after sets_bunny.py and sets_doctor.py (like characters_bus.py inside
characters.py), so it reuses their set engine (BView cameras on a plan in metres, per-face light maps, Room / Piece /
build_view, BSet staging API, the Doctor film's Larch Street sky / far ring / neighbours / streetlights) and everything
here is part of `sets`:  import sets as ST;  sp = ST.bu_living('wide').  Every new name starts with bu_ / BU_ / _bu.

THE HOUSE (Grandma Della's, Larch Street, Larkfield): one floor plan in metres. x = east, y = from the front wall (Larch
Street, y 0) toward the back yard, Y = up; ground floor Y 0, upstairs floor BU_UP 2.95, the yard / driveway / street
BU_G -0.5. Ground floor: the front hall on the west (front door with two frosted panes, a peephole and the rules taped
inside; the stairs along the west wall rising +y from y 3.2 to 6.84; a side window over the driveway; the back door at
the end), the living room east of it through a wide cased opening (picture window + curtains with a gap, the couch along
the back wall facing the window, Grandma's armchair, the old TV in the front-east corner, the floor lamp). Upstairs: the
narrow hall (1.2 m wide, 2.4 m ceiling) from Grandma's door (the only deadbolt, at its front end) back to the landing;
Grandma's room at the front-west (a window over the driveway); Sami's room at the back (his door off the hall).
Outside: the porch and steps, the lawn, the walk, our mailbox at the kerb, bus 9 parked in the driveway along the west
side of the house (nose toward the back, its folding door facing the house), HIS bus at the kerb (heading west, its
door facing our walk), the flickering streetlight at the end of the driveway. Plan: _work/sets/floorplan.jpg.

Other locations, each on its own little plan: inside his bus / inside bus 9 (one bus plan: x across, +x = the door side,
y back from the windshield, floor Y 0), bus 9 on the night road (the chase), Larkfield Elementary at 2:57 AM, Theo's
stop, the 1994 classroom with the TV cart and the Channel 6 studio on the tape, bus 9 in the morning, the inserts.

STAGING DATA: identical to the Doctor / Bunnyman sets (see sets_doctor's docstring): sp.anchors[name] -> Spot (.x .y
design px of the feet / point, .depth, .ppm px per metre there, .height of a 1.85 m adult, .X .Yp .Y plan, .kind,
.turn, .seat_y), sp.spot / ppm_at / floor_y / pick / turn_for / walkable / order_at / light_kw / shadow,
ST.stage_figure(sp, who, spot, ...). Depth-to-scale rule: ppm = S / depth; a figure m metres tall is m * ppm px tall
at its feet. Every view's camera is in BU_CAMS (CAMS table; the plan map draws them), so cuts keep screen direction.
"""
import math
import numpy as np
import skia

# ====================================================================================================== plan
BU_G = D_GROUND                       # the yard, the driveway and the street (-0.5)
BU_UP = 2.95                          # the upstairs floor
BU_CEIL = 2.5                         # ground-floor ceiling
BU_UH = 2.4                           # upstairs ceiling height above BU_UP
BU_HOUSE = (-5.6, 4.6, 0.0, 9.6)
BU_HALL = (-5.6, -3.2, 0.0, 9.6)      # the front hall (with the stairs along the west wall)
BU_LIV = (-3.2, 2.4, 0.0, 5.8)        # the living room
BU_FDOOR = (-4.4, -3.5, 2.05)         # the front door on y 0: hinge x0 (west), knob x1 (east); swings into the hall
BU_LOPEN = (0.3, 3.2, 2.25)           # the cased opening hall <-> living room on x -3.2 (y0, y1, height)
BU_PWIN = (-2.0, 0.8, 0.7, 2.1)       # the picture window on y 0 (x0, x1, sill, top)
BU_HWIN = (1.25, 2.05, 1.0, 2.0)      # the hall's side window on x -5.6 over the driveway (y0, y1, sill, top)
BU_BDOOR = (-4.6, -3.75, 2.05)        # the back door at the end of the hall, on y 9.6 (x0, x1, h)
BU_KDOOR = (0.9, 1.8, 2.05)           # the dark kitchen doorway on the living room's back wall y 5.8 (x0, x1, h)
BU_ST = (-5.6, -4.6, 3.2, 15, 0.26)   # stairs: x0, x1, y of the first riser, risers, run; top at y 6.84
BU_ST_TOP = BU_ST[2] + (BU_ST[3] - 1) * BU_ST[4]
BU_RISE = BU_UP / BU_ST[3]
BU_UHALL = (-4.6, -3.4, 3.2, 8.2)     # the upstairs hall (corridor); the landing west of it at y >= BU_ST_TOP
BU_LAND = (-5.6, -4.6, BU_ST_TOP, 8.2)
BU_GRAN = (-5.6, -1.6, 0.0, 3.2)      # Grandma's room (upstairs)
BU_GDOOR = (-4.45, -3.55, 2.03)       # Grandma's door on y 3.2 (hinge x1 east, latch x0 west); swings into her room (-y)
BU_GWIN = (1.0, 2.1, 0.85, 2.05)      # her window on x -5.6 over the driveway (y0, y1, sill, top above BU_UP)
BU_GFWIN = (-3.4, -2.5, 0.85, 2.05)   # her front window on y 0
BU_SAMI = (-3.4, 0.8, 5.4, 9.6)       # Sami's room (upstairs, back)
BU_SDOOR = (5.6, 6.4, 2.03)           # his door on x -3.4 (y0 hinge, y1)
BU_SWIN = (-2.3, -1.1, 0.9, 2.0)      # his window on y 9.6
BU_MDOOR = (3.6, 4.4)                 # Mina's door (closed; room not built) on x -3.4
BU_PORCH = (-5.2, -2.7, -1.8, 0.0)    # porch deck at floor level (x0, x1, y0, y1)
BU_STEPS = (-4.45, -3.45, -2.6, -1.8) # three steps down to the walk
BU_WALK = (-4.3, -3.6)                # the front walk (x0, x1) from the steps to the sidewalk
BU_PLIGHT = (-3.2, 1.95, -0.06)       # the porch light, east of the door
BU_MAILBOX = (-3.0, -11.65)           # our mailbox at the kerb (letters on the street side)
BU_DRIVE = (-10.0, -6.6, -12.2, 6.2)  # the driveway (x0, x1, y0, y1) at BU_G
BU_BUS9 = (-8.3, -1.0, 180.0)         # bus 9 parked: centre (x, y), facing +y (nose toward the back yard)
BU_HISBUS = (-0.2, -13.75, -90.0)     # his bus at the kerb: centre, heading west (-x); door side +y (our walk)
BU_LAMP = (-6.4, -12.6)               # the flickering streetlight at the end of the driveway (arm over the street)
BU_LAMPS = [(-30.0, -12.6), (18.0, -12.6), (42.0, -12.6)]
BU_NAME = 'HAYES'                     # the stick-on letters on our mailbox (rule one: Grandma unscrews them)
BU_HOUSE_NO = '17'

BU_AMBER = '#ffaa3c'                  # his bus: the amber of its windows
BU_SODIUM = '#ffb060'
BU_HEADS = '#ffd25a'                  # his headlights: yellow
BU_WARM = '#ffc98a'
BU_PAL = dict(liv_paper='#c9b48e', liv_ink='#9a7a56', hall_paper='#8a9a7a', hall_ink='#6e7e60', wains='#efe6d2', trim='#f2ebdc',
              carpet='#7a5e48', floor='#8a5a34', up_paper='#b8a888', gran_paper='#c8a8a0', gran_ink='#a07a76', sami_paper='#a8c8d8',
              sami_ink='#e8f2f4', siding='#d8c9a3', shutter='#2e4a3e', door='#6a2e2a', roof='#3a3638', bus9='#e8b020', his='#9a7a2c')

# ====================================================================================================== grades
_GR.setdefault('bu_night', dict(contrast=1.08, pivot=0.24, gamma=1.05, sat=1.08, wb=(0.98, 1.0, 1.04), floor='#06080f',
                                bloom=0.8, bloom_thr=226, vignette=0.4, grain=0.7, shoulder=0.45))
_GR.setdefault('bu_warm', dict(exposure=0.06, contrast=1.04, pivot=0.25, gamma=1.05, sat=1.08, wb=(1.06, 1.0, 0.92), floor='#0e0a08',
                               bloom=0.85, bloom_thr=226, vignette=0.42, grain=0.5, shoulder=0.5))
_GR.setdefault('bu_dark', dict(contrast=1.1, pivot=0.22, gamma=1.08, sat=0.95, wb=(0.95, 0.99, 1.08), floor='#04050b',
                               bloom=0.9, bloom_thr=222, vignette=0.36, grain=0.9, shoulder=0.45))
# HIS world: sickly sodium-amber, crushed, the blacks lifted brown, dirty tape grain
_GR.setdefault('bu_amber', dict(exposure=0.0, contrast=1.14, pivot=0.25, gamma=1.0, sat=0.82, wb=(1.08, 1.0, 0.78), floor='#100a04',
                                bloom=1.0, bloom_thr=214, vignette=0.34, grain=1.3, shoulder=0.5))
_GR.setdefault('bu_ext', dict(contrast=1.1, pivot=0.22, gamma=1.0, sat=1.08, wb=(0.98, 1.0, 1.05), floor='#04060e',
                              bloom=1.0, bloom_thr=222, vignette=0.36, grain=0.8, shoulder=0.45))
_GR.setdefault('bu_road', dict(contrast=1.12, pivot=0.22, gamma=1.02, sat=1.05, wb=(1.0, 1.0, 1.04), floor='#04050a',
                               bloom=1.0, bloom_thr=220, vignette=0.36, grain=0.9, shoulder=0.45))
_GR.setdefault('bu_morning', dict(exposure=0.0, contrast=1.02, pivot=0.26, gamma=1.05, sat=1.12, wb=(1.06, 1.0, 0.9), floor='#141008',
                                  bloom=0.9, bloom_thr=228, vignette=0.45, grain=0.35, shoulder=0.55))
_GR.setdefault('bu_class', dict(exposure=0.02, contrast=1.06, pivot=0.25, gamma=1.04, sat=0.86, wb=(1.04, 1.0, 0.9), floor='#0c0a08',
                                bloom=0.9, bloom_thr=222, vignette=0.45, grain=1.1, soft=0.4, shoulder=0.5))
_GR.setdefault('bu_vhs94', dict(exposure=0.1, contrast=1.0, pivot=0.26, gamma=1.02, sat=1.15, wb=(1.04, 1.0, 0.94), floor='#140c10',
                                bloom=0.9, bloom_thr=220, vignette=0.3, grain=1.2, soft=0.6, shoulder=0.55))
_GR.setdefault('bu_ins', dict(contrast=1.04, pivot=0.25, gamma=1.04, sat=1.04, wb=(1.02, 1.0, 0.97), floor='#0a0808',
                              bloom=0.5, bloom_thr=236, vignette=0.5, grain=0.5, shoulder=0.5))
_GR.setdefault('bu_ins_amber', dict(contrast=1.12, pivot=0.26, gamma=1.0, sat=0.86, wb=(1.08, 1.0, 0.8), floor='#0e0804',
                                    bloom=0.7, bloom_thr=228, vignette=0.4, grain=1.1, shoulder=0.5))


def bu_vhs_dirt(k=0.35, track=0.1):
    """The tape dirt on HIS world (his bus, the school, his close-ups): a light, flat VHS layer (no CRT tube) for sp.fx."""
    return lambda t: {'vhs': dict(t=t, k=k, curve=0.0, glass=0.0, scan=0.25, glow=0.5, track=track, bezel=0.0, tube=False, head=0.4)}


# ====================================================================================================== helpers
BU_CAMS = []


def _bcam(name, S, h, eye, x, y, yaw, env=None, note='', room='', pitch=0.0):
    _cam(name, S, h, eye, x, y, yaw, env or _env(), note, room, pitch)
    if name not in BU_CAMS: BU_CAMS.append(name)


def _bu_lv(spec, seed, t=0.0):
    return _kfn(spec, seed)(t)


def _static(spec, default=0.0):
    """The value a level spec has for static (cached) art: numbers pass, callables / dicts fall back to default."""
    return spec if isinstance(spec, (int, float)) else default


def _run(a, b, holes=(), wins=(), art=None, Y0=None, Y1=None, paper=None, ink=None, kind=None, wains=None, **kw):
    """One wall run a -> b (visible side on its right), holes / windows in plan coordinates (xa, ya, xb, yb, v0, v1)."""
    return dict(a=a, b=b, holes=list(holes), wins=list(wins), art=art, Y0=Y0, Y1=Y1, paper=paper, ink=ink, kind=kind, wains=wains, kw=kw)


def _rect_runs(R, holes=None, wins=None, art=None):
    holes, wins, art = holes or {}, wins or {}, art or {}
    return [_run(a, b, holes.get(s, ()), wins.get(s, ()), art.get(s)) for (s, a, b, u) in _walls_of(R)]


def _u_of(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy); fx, fy = dx / L, dy / L
    return (lambda x, y: (x - a[0]) * fx + (y - a[1]) * fy), L


class BuBox(Room):
    """A room of this film on any plan: cfg = dict(name, R (x0, x1, y0, y1) or poly, Y0 (floor), H (ceiling height),
    floors=[(x0, x1, y0, y1)] (default [R]), floor=dict(base, kind, ink, ink2, scale, seed, art), runs=[_run(...)],
    walls=dict(paper, ink, kind, wains, wcol, trim, seed, scale, pa) (defaults for the runs), ceil=dict(c, art, rects),
    lights=fn(o) -> (amb, steady, var), pieces=fn(o), spots=fn(v, o), glows=fn(v, o), shell_x=fn(pen, v, o)."""

    def __init__(self, cfg, far=False):
        self.cfg, self.far = cfg, far
        self.name = cfg['name']
        self.poly = cfg.get('poly') or _r4p(cfg['R'])

    def lights(self, o): return self.cfg['lights'](o)

    def shell(self, pen, v, o):
        c = self.cfg
        Y0 = c.get('Y0', 0.0); H = c.get('H', BU_CEIL)
        fl = dict(c.get('floor', {}))
        if c.get('shell_pre'): c['shell_pre'](pen, v, o)
        for fr in c.get('floors') or [c['R']]:
            floor_rect(pen, v, fr[0], fr[1], fr[2], fr[3], Y0, fl.get('base', '#8a6a4a'), fl.get('kind', 'boards'), fl.get('ink', '#5a3a22'),
                       fl.get('ink2'), seed=fl.get('seed', 3), art=fl.get('art'), scale=fl.get('scale', 1.0))
        wk = dict(c.get('walls', {}))
        d_paper = wk.pop('paper', '#d8d4c8'); d_ink = wk.pop('ink', None); d_kind = wk.pop('kind', None); d_wains = wk.pop('wains', 0.0)
        runs = c.get('runs')
        if runs is None: runs = _rect_runs(c['R'])
        for r in runs:
            u_of, L = _u_of(r['a'], r['b'])
            hs = [(min(u_of(xa, ya), u_of(xb, yb)), v0, max(u_of(xa, ya), u_of(xb, yb)), v1) for (xa, ya, xb, yb, v0, v1) in r['holes']]
            hs += [(min(u_of(xa, ya), u_of(xb, yb)), sl, max(u_of(xa, ya), u_of(xb, yb)), tp) for (xa, ya, xb, yb, sl, tp, *_r) in r['wins']]
            ry0 = Y0 if r['Y0'] is None else r['Y0']; ry1 = (Y0 + H) if r['Y1'] is None else r['Y1']
            kw = dict(wk); kw.update(r['kw'])
            wall(pen, v, r['a'], r['b'], ry0, ry1, r['paper'] or d_paper, r['ink'] if r['ink'] is not None else d_ink, r['kind'] or d_kind,
                 hs, wains=d_wains if r['wains'] is None else r['wains'], art=r['art'], **kw)
        cl = c.get('ceil', {})
        if cl is not False:
            for cr in cl.get('rects') or [c['R']]:
                ceil_rect(pen, v, cr[0], cr[1], cr[2], cr[3], Y0 + H, c=cl.get('c', '#e8e2d6'), art=cl.get('art'))
        for r in runs:
            u_of, L = _u_of(r['a'], r['b'])
            for (xa, ya, xb, yb, sl, tp, *rest) in r['wins']:
                ua, ub = sorted((u_of(xa, ya), u_of(xb, yb)))
                window_unit(pen, v, r['a'], r['b'], ua, ub, sl, tp, Y0=(Y0 if r['Y0'] is None else r['Y0']), lites=(rest[0] if rest else (2, 2)),
                            frame=(rest[1] if len(rest) > 1 else '#f1ece0'))
        if c.get('shell_x'): c['shell_x'](pen, v, o)

    def pieces(self, o): return self.cfg.get('pieces', lambda o: [])(o)

    def glows(self, v, o): return self.cfg.get('glows', lambda v, o: [])(v, o)

    def spots(self, v, o): return self.cfg.get('spots', lambda v, o: {})(v, o)


def _dark_far(name, poly, Y0=0.0, H=BU_CEIL, c='#0a0c14'):
    """A room seen through an opening that is just darkness (not built: the kitchen, Mina's room)."""
    R = (min(p_[0] for p_ in poly), max(p_[0] for p_ in poly), min(p_[1] for p_ in poly), max(p_[1] for p_ in poly))
    return BuBox(dict(name=name, R=R, Y0=Y0, H=H, floor=dict(base='#1a1612', kind=None), walls=dict(paper='#1c1c22'), ceil=dict(c='#16161c'),
                      lights=lambda o: ('#141826', [], [])), far=True)


def _phone_lamp(o, seed=301):
    """Mina's phone light (the blackout key light): o['phone'] = level spec, o['phone_at'] = (x, Y, y)."""
    P = o.get('phone_at', (0.0, 1.1, 4.6))
    return ('phone', [Lamp(P[0], P[1], P[2], 3.2, '#e8f0ff', 2.2, (1.0, 1.0, 0.8), fall=1.6)], _kfn(o.get('phone', 0.0), seed))


def _flash_lamp(o, seed=302):
    """Grandma's / Sami's flashlight: o['flash'] level, o['flash_at'] = (x, Y, y)."""
    P = o.get('flash_at', (0.0, 1.0, 0.0))
    return ('flash', [Lamp(P[0], P[1], P[2], 4.5, '#fff2d0', 1.8, (1.0, 1.0, 0.6), fall=1.5)], _kfn(o.get('flash', 0.0), seed))


# ====================================================================================================== house props
def _bu_tape(p_, x, y, w, h, rot=0.0, a=170):
    p_.cv.save(); p_.cv.translate(x, y); p_.cv.rotate(rot)
    p_.fill(rect(-w / 2, -h / 2, w, h), '#efe2a8', a); p_.line(rect(-w / 2, -h / 2, w, h), 0.3, '#a89a6a', 90)
    p_.cv.restore()


BU_RULES = [(1, ["At midnight, turn off every light that faces the street.", "Take our name off anything he can see from the road.",
                 "He can only call the names he can read."]),
            (2, ['If he calls your name, never answer. Never say "here" to him.', "If one of us calls you, look first.",
                 "Only answer a face you know."]),
            (3, ["If anyone says I sent them, they have to say our word.", "You never say it first.", "Never say it where anyone else can hear."]),
            (4, ["If the lights go out, find Sami and hold his hand.", "Don't let go until the lights come back."]),
            (5, ["If he gets inside, lock yourselves in my room.", "Open the door only for the word."]),
            (6, ["If he takes one of you, don't chase him on foot.", "Come get me. We meet him at his last stop."]),
            (7, ["Never get on his bus. Not for anybody.", "Not even for Sami."])]
BU_RULE8 = (8, ["Sit with the one who sits alone.", "Ask their name."])


def _rules_sheet_small(p_, x, y, w, h, eighth=False, k=1.0):
    """The rules on lined paper, taped inside the front door (cm frame, tiny: legible only in the insert)."""
    p_.fill(rect(x + 0.6, y + 0.8, w, h), '#000000', 60, blur=1.2)
    p_.fill(rect(x, y, w, h), '#f4efe0'); p_.texture(rect(x, y, w, h), 'paper', 0.4, 'multiply', 0.6)
    for i in range(int(h / 1.4)):
        p_.fill(rect(x + 1, y + 2.4 + i * 1.4, w - 2, 0.12), '#8ab0d8', 120)
    p_.fill(rect(x + 3.2, y, 0.15, h), '#d88a8a', 120)
    btext(p_, 'RULES', x + w / 2, y + 2.2, 'caveat_b', 2.2, '#2a2a5a', 230, 'center')
    yy = y + 4.0
    for (n, lines) in BU_RULES:
        p_.fill(rect(x + 4.0, yy - 0.5, w - 6.5, 0.32), '#2a2a5a', 150)
        yy += 1.4 * (1 if n not in (1, 2, 3) else 1.4)
    if eighth:
        p_.fill(rect(x + 4.0, yy + 0.4, w - 9, 0.36), '#3a3a3a', 170)
    for (tx, ty) in ((x + 1.5, y - 0.3), (x + w - 1.5, y - 0.3)):
        _bu_tape(p_, tx, ty, 4.0, 1.4, (-0.3 if tx < x + 5 else 0.25))


def bu_front_door_art(side='in', rules=True, eighth=False, frost_lit=0.0, bolt=1.0):
    """The front door (a deep red, four panels) with two narrow frosted panes side by side in the upper half and the
    peephole between them; inside: the rules taped under the panes, a deadbolt above the knob. side 'in' | 'out'."""
    def art(p_, W, H):
        c = BU_PAL['door']
        p_.fill(rect(0, 0, W, H), c)
        p_.texture(rect(0, 0, W, H), 'wood', 0.35, 'overlay', 0.8, 90)
        for (x0, y0, w, h) in ((10, H - 95, W / 2 - 15, 80), (W / 2 + 5, H - 95, W / 2 - 15, 80)):
            p_.fill(rect(x0, y0, w, h), _darken(c, 0.12)); p_.line(rect(x0, y0, w, h), 1.0, '#000000', 90)
            p_.line(rect(x0 + 3, y0 + 3, w - 6, h - 6), 0.6, '#ffffff', 30)
        # the frosted panes (glass is drawn cut through: the art fills them pale; the frosted look, lit from behind)
        for x0 in (14, W / 2 + 6):
            r = rrect(x0, 26, W / 2 - 20, 58, 3)
            p_.fill(r, mix('#c8ccd4', '#ffe0a8', frost_lit)); p_.texture(r, 'grunge', 0.45, 'overlay', 0.5)
            for k in range(7):
                p_.line(smooth([(x0 + 2, 30 + k * 8), (x0 + 10, 28 + k * 8), (x0 + W / 2 - 24, 31 + k * 8)], False), 0.6, '#ffffff', 50)
            p_.line(r, 1.6, '#3a2018', 230)
        # peephole between the panes at 1.55 m
        py = H - 155
        p_.fill(oval(W / 2, py, 1.6), '#b89a5a'); p_.fill(oval(W / 2, py, 0.8), '#101010')
        knob_x = 8 if side == 'in' else W - 8
        p_.fill(oval(knob_x, H - 97, 3.0), '#c8a858'); p_.line(oval(knob_x, H - 97, 3.0), 0.6)
        p_.fill(oval(knob_x, H - 114, 2.4), '#c8a858'); p_.line(oval(knob_x, H - 114, 2.4), 0.6)
        if side == 'in':
            p_.fill(rrect(knob_x - 1.2, H - 117 - 2.0 * bolt, 2.4, 6, 1), '#a88a48')
            if rules:
                _rules_sheet_small(p_, W / 2 - 14, 92, 28, 30, eighth)
    return art


class BuDoorLeaf(Door):
    """A Door whose glass panes are real holes (the porch / hall behind shows through the frosted panes)."""
    pass


def bu_backpack(pen, v, x, y, Y, fa=0.0, name=True, s=1.0):
    """Sami's green dinosaur backpack (spikes along the top, a name tag SAMI on the front pocket). fa = the way its
    FRONT faces (Box convention: 0 = -y)."""
    B = Box(x, y, 0.3 * s, 0.16 * s, Y, Y + 0.38 * s, fa)
    def front(p_, W, H):
        p_.fill(rrect(0, 0, W, H, 8), '#4aa06a'); p_.texture(rect(0, 0, W, H), 'fabric', 0.6, 'overlay', 0.5)
        p_.fill(rrect(4, H * 0.45, W - 8, H * 0.45, 5), '#3a8a5a'); p_.line(rrect(4, H * 0.45, W - 8, H * 0.45, 5), 0.6, '#1a3a2a', 160)
        p_.fill(oval(W * 0.3, H * 0.25, 2.2), '#ffffff'); p_.fill(oval(W * 0.3, H * 0.25, 1.1), '#1a1a1a')
        p_.fill(oval(W * 0.7, H * 0.25, 2.2), '#ffffff'); p_.fill(oval(W * 0.7, H * 0.25, 1.1), '#1a1a1a')
        if name:
            p_.fill(rrect(W * 0.18, H * 0.58, W * 0.64, H * 0.16, 1.5), '#fff6dc')
            btext(p_, 'SAMI', W / 2, H * 0.7, 'kid', H * 0.13, '#c83a2a', 255, 'center')
    def back(p_, W, H):
        p_.fill(rrect(0, 0, W, H, 8), '#3e8a5c'); p_.texture(rect(0, 0, W, H), 'fabric', 0.6, 'overlay', 0.5)
        for xx in (W * 0.28, W * 0.72): p_.fill(rrect(xx - 2.5, 4, 5, H - 8, 2.5), '#2a5a3e')
    draw_box(pen, v, B, {'front': dict(fill='#4aa06a', art=front), 'back': dict(fill='#3e8a5c', art=back), 'sides': '#3a8a5a', 'top': '#4aa06a'}, lw=0.8)
    # spikes along the top (orange)
    for k in range(4):
        u = (-0.11 + k * 0.073) * s
        P0 = B.at(u - 0.025 * s, 0, Y + 0.38 * s); P1 = B.at(u, 0, Y + 0.44 * s); P2 = B.at(u + 0.025 * s, 0, Y + 0.38 * s)
        q = v.poly3([P0, P1, P2])
        if not q.isEmpty(): pen.fill(q, lit('#e88a3a', P1, None)); pen.line(q, 0.7)


def bu_walkie(pen, v, x, Y, y, ang=20.0, c='#e8c020', led=0.0, s=1.0):
    """A kid's walkie-talkie lying on a surface (yellow body, black grille, antenna, a red talk LED: led 0..1)."""
    if v.d(x, y) < 0.2: return
    a = math.radians(ang)
    U = (math.cos(a), math.sin(a)); N = (-math.sin(a), math.cos(a))
    def P(u, n, h=0.0): return (x + U[0] * u + N[0] * n, Y + h, y + U[1] * u + N[1] * n)
    L, Wd = 0.17 * s, 0.065 * s
    top = v.poly3([P(-L / 2, -Wd / 2, 0.03), P(L / 2, -Wd / 2, 0.03), P(L / 2, Wd / 2, 0.03), P(-L / 2, Wd / 2, 0.03)])
    base = v.poly3([P(-L / 2, -Wd / 2), P(L / 2, -Wd / 2), P(L / 2, Wd / 2, 0.0), P(-L / 2, Wd / 2)])
    if top.isEmpty(): return
    pen.fill(base, '#000000', 90, blur=2)
    pen.fill(top, lit(c, P(0, 0, 0.03), (0, 1, 0))); pen.line(top, 1.0)
    g = v.poly3([P(-L * 0.3, -Wd * 0.32, 0.031), P(L * 0.1, -Wd * 0.32, 0.031), P(L * 0.1, Wd * 0.32, 0.031), P(-L * 0.3, Wd * 0.32, 0.031)])
    if not g.isEmpty(): pen.fill(g, '#1a1a1a', 220)
    pen.seg(v.p(*P(L / 2 - 0.01, Wd * 0.25, 0.03)), v.p(*P(L / 2 + 0.07 * s, Wd * 0.25, 0.035)), max(1.0, 0.008 * v.s(x, y)), '#1a1a1a')
    lx, ly = v.p(*P(L * 0.3, 0, 0.032))
    pen.fill(oval(lx, ly, max(1.0, 0.006 * v.s(x, y))), mix('#5a1010', '#ff3a2a', led))
    if led > 0.05: pen.glow(lx, ly, 0.03 * v.s(x, y), '#ff4a2a', 120 * led)


def bu_broom(pen, v, A, B_, k=1.0, bend=0.0, crack=0.0):
    """The porch broom: handle from A (x, Y, y) (the head end) to B_ (the tip). bend 0..1 bows the handle (the doors
    squeezing it), crack 0..1 splits it in the middle."""
    if v.d(A[0], A[2]) < 0.2 and v.d(B_[0], B_[2]) < 0.2: return
    n = 9
    pts = []
    for i in range(n):
        f = i / (n - 1)
        P = (A[0] + (B_[0] - A[0]) * f, A[1] + (B_[1] - A[1]) * f + bend * 0.18 * math.sin(math.pi * f), A[2] + (B_[2] - A[2]) * f)
        pts.append(v.p(*P))
    s = v.s((A[0] + B_[0]) / 2, (A[2] + B_[2]) / 2)
    w = max(1.4, 0.03 * s)
    if crack > 0.01:
        m = n // 2
        a1, a2 = pts[:m + 1], pts[m:]
        for seg_ in (a1, a2):
            pen.line(poly(seg_, False), w + 2, LINE); pen.line(poly(seg_, False), w, '#b88a4a')
        for k_ in range(3):
            pen.seg(pts[m], (pts[m][0] + (k_ - 1) * w * 1.4, pts[m][1] - w * (1.5 + k_ * 0.6) * crack), max(0.8, w * 0.35), '#e8c890')
    else:
        pen.line(poly(pts, False), w + 2, LINE); pen.line(poly(pts, False), w, '#b88a4a')
        pen.line(poly(pts, False), max(0.6, w * 0.3), '#e8c890', 90)
    # bristles at A
    hx, hy = v.p(*A); ex, ey = pts[1]
    ang = math.atan2(hy - ey, hx - ex)
    L = 0.34 * s; Wd = 0.28 * s
    cx, cy = hx + math.cos(ang) * L * 0.4, hy + math.sin(ang) * L * 0.4
    pen.cv.save(); pen.cv.translate(cx, cy); pen.cv.rotate(math.degrees(ang) - 90)
    br = poly([(-Wd * 0.25, -L * 0.45), (Wd * 0.25, -L * 0.45), (Wd * 0.55, L * 0.5), (-Wd * 0.55, L * 0.5)])
    pen.fill(br, '#c8a858'); pen.line(br, 1.0)
    for k_ in range(9):
        xx = -Wd * 0.5 + k_ * Wd / 8
        pen.seg((xx * 0.5, -L * 0.3), (xx, L * 0.48), max(0.5, 0.004 * s), '#8a6a2a', 160)
    pen.fill(rect(-Wd * 0.28, -L * 0.5, Wd * 0.56, L * 0.12), '#8a2a2a'); pen.cv.restore()


def bu_stairs(pen, v, x0, x1, y0, n, run, rise, Y0=0.0, tread='#6a4428', riser='#efe6d2', runner='#5a3a5a', upto=None):
    """A straight flight rising +y: n risers from (y0, Y0); treads in wood with a carpet runner, white risers, drawn far
    -> near for the camera (each step a box from the floor up to its tread)."""
    steps = []
    m = n if upto is None else upto
    for i in range(m):
        ya = y0 + i * run; yb = ya + run if i < n - 1 else ya + run
        steps.append((i, ya, yb, Y0 + (i + 1) * rise))
    steps.sort(key=lambda q: -v.d((x0 + x1) / 2, (q[1] + q[2]) / 2))
    rw = (x1 - x0) * 0.62
    for (i, ya, yb, top) in steps:
        B = Box((x0 + x1) / 2, (ya + yb) / 2, x1 - x0, yb - ya, top - rise, top, 0)
        def tart(p_, W, H, rw=rw):
            p_.texture(rect(0, 0, W, H), 'wood', 0.5, 'overlay', 0.9, 0)
            p_.fill(rect((W - rw * 100) / 2, 0, rw * 100, H), runner); p_.texture(rect((W - rw * 100) / 2, 0, rw * 100, H), 'fabric', 0.5, 'overlay', 0.8)
            p_.line(rect((W - rw * 100) / 2 + 3, -2, rw * 100 - 6, H + 4), 0.8, '#d8b860', 120)
        def rart(p_, W, H, rw=rw):
            p_.fill(rect((W - rw * 100) / 2, 0, rw * 100, H), _darken(runner, 0.15))
        draw_box(pen, v, B, {'top': dict(fill=tread, art=tart), 'front': dict(fill=riser, art=rart), 'sides': '#e8dcc8', 'back': riser}, lw=0.8)


# ====================================================================================================== the buses
# A conventional school bus as Parts on any plan: centre (cx, cy), facing fa (Box convention: 0 = nose toward -y,
# 90 = +x, 180 = +y, -90 = -x), ground G. Its own right side (the folding door) is the Box 'left' face. kind 'bus9'
# (Grandma's: warm yellow, black rub rails, LARKFIELD SCHOOL DISTRICT, the number 9) or 'his' (an older, rounder bus in
# faded dirty yellow, no number, amber-lit windows). Emissives (windows, headlights, flashers, brake lights) are drawn
# by bu_bus_emit as a live layer so they glow and can change in the shot.
BU_BUS_L, BU_BUS_W, BU_BUS_HOOD = 10.4, 2.44, 1.45
BU_BUS_Y0, BU_BUS_Y1 = 0.42, 3.0                      # body bottom / roof above the ground
BU_BUS_FLOOR = 0.95                                   # cabin floor above the ground (3 steps up)
BU_BUS_NWIN = 10


def _bus_col(kind):
    if kind == 'his':
        return dict(body='#8e7228', dark='#4a3a18', roof='#6e5820', rail='#1e1a12', glass='#0e0c08', text='#2a2416', trim='#3a3020')
    return dict(body=BU_PAL['bus9'], dark='#8a6410', roof='#d8a01a', rail='#141414', glass='#141a22', text='#141414', trim='#202020')


def bu_bus_frame(cx, cy, fa, G=BU_G):
    """The bus body Box (cabin part, behind the hood) and helpers: body Box, hood Box, Lt, Lb (body length)."""
    Lb = BU_BUS_L - BU_BUS_HOOD
    th = math.radians(fa); N = (math.sin(th), -math.cos(th))
    bc = (cx - N[0] * BU_BUS_HOOD / 2, cy - N[1] * BU_BUS_HOOD / 2)
    body = Box(bc[0], bc[1], BU_BUS_W, Lb, G + BU_BUS_Y0, G + BU_BUS_Y1, fa)
    hc = (cx + N[0] * (BU_BUS_L / 2 - BU_BUS_HOOD / 2), cy + N[1] * (BU_BUS_L / 2 - BU_BUS_HOOD / 2))
    hood = Box(hc[0], hc[1], 1.86, BU_BUS_HOOD, G + 0.62, G + 1.72, fa)
    return body, hood, Lb


def _win_xs(Lb, side):
    """Window spans along a side face (cm, art x from 0): side 'door' runs rear -> front, 'driver' front -> rear."""
    W = Lb * 100
    xs = []
    front_gap, rear_gap = 150.0, 60.0
    span = W - front_gap - rear_gap
    pitch = span / BU_BUS_NWIN
    for i in range(BU_BUS_NWIN):
        a = rear_gap + i * pitch + 6; b = a + pitch - 12
        xs.append((a, b) if side == 'door' else (W - b, W - a))
    return xs


def _bus_side_art(kind, side, Lb, number='9'):
    col = _bus_col(kind)
    def art(p_, W, H):
        p_.fill(rect(0, 0, W, H), col['body'])
        p_.texture(rect(0, 0, W, H), 'grunge', 0.55 if kind == 'his' else 0.25, 'overlay', 1.4)
        if kind == 'his':
            rng = np.random.default_rng(7 if side == 'door' else 8)
            for i in range(26):                                                 # rust streaks under the windows
                x = rng.uniform(20, W - 20); p_.linear(rect(x, 100, rng.uniform(2, 6), rng.uniform(30, 120)), x, 100, x, 220,
                                                         [(0, '#4a2a10', 150), (1, '#4a2a10', 0)])
        top = 26.0 if kind == 'bus9' else 34.0
        for (a, b) in _win_xs(Lb, side):
            r = rrect(a, top, b - a, 74, 5 if kind == 'bus9' else 10)
            p_.fill(r, col['glass']); p_.line(r, 3.0, col['trim'])
            p_.fill(rect(a, top + 36, b - a, 3), col['trim'], 200)                # the split sash
        for (yy, hh) in ((118, 5), (150, 6), (200, 6)):
            p_.fill(rect(0, yy, W, hh), col['rail'], 230 if kind == 'bus9' else 170)
        txt = 'LARKFIELD SCHOOL DISTRICT' if kind == 'bus9' else ''
        if txt:
            btext(p_, txt, W * 0.45, 140, 'head', 15, col['text'], 230, 'center', spacing=0.05)
        if kind == 'bus9':
            nx = W - 175 if side == 'door' else 175
            btext(p_, number, nx, 186, 'head', 26, col['text'], 240, 'center')
        # wheel wells
        for f in (0.22, 0.86):
            x = (W * f) if side == 'door' else (W * (1 - f))
            p_.fill(oval(x, H + 6, 62, 58), '#0a0a0a')
        if side == 'door':                                                       # the entrance door frame (panels: bu_bus_door)
            p_.fill(rect(W - 128, 16, 104, H - 16), '#0c0a08'); p_.line(rect(W - 128, 16, 104, H - 16), 3.0, col['trim'])
        else:
            p_.fill(rrect(20, top - 4, 110, 84, 6), col['glass']); p_.line(rrect(20, top - 4, 110, 84, 6), 3.0, col['trim'])   # driver's window
            # the stop arm folded flat against the side
            sx = 150
            oc = [(sx + 22 * math.cos(math.radians(22.5 + 45 * k)), 118 + 22 * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
            p_.fill(poly(oc), '#b8241e' if kind == 'bus9' else '#6a2a1a'); p_.line(poly(oc), 1.0)
            btext(p_, 'STOP', sx, 124, 'sans_b', 12, '#ffffff', 220 if kind == 'bus9' else 120, 'center')
        if kind == 'his':
            p_.texture(rect(0, 0, W, H), 'grunge', 0.5, 'multiply', 2.2)
    return art


def _bus_front_art(kind, cobweb=False):
    col = _bus_col(kind)
    def art(p_, W, H):
        p_.fill(rect(0, 0, W, H), col['body']); p_.texture(rect(0, 0, W, H), 'grunge', 0.5 if kind == 'his' else 0.22, 'overlay', 1.2)
        # SCHOOL BUS header, flashers
        p_.fill(rrect(W * 0.2, 8, W * 0.6, 24, 4), col['body'])
        btext(p_, 'SCHOOL BUS' if kind == 'bus9' else 'SCHOOL  BUS', W / 2, 27, 'head', 20, col['text'], 235 if kind == 'bus9' else 140, 'center')
        for (x, c) in ((W * 0.08, '#c87a1a'), (W * 0.16, '#a01a12'), (W * 0.84, '#a01a12'), (W * 0.92, '#c87a1a')):
            p_.fill(oval(x, 20, 9), c); p_.line(oval(x, 20, 9), 1.2)
        # windshield (two panes) from 1.75 to 2.75 above the ground
        y0 = (BU_BUS_Y1 - 2.78) * 100; y1 = (BU_BUS_Y1 - 1.76) * 100
        for (a, b) in ((10, W / 2 - 3), (W / 2 + 3, W - 10)):
            r = rrect(a, y0, b - a, y1 - y0, 8)
            p_.fill(r, col['glass']); p_.line(r, 3.0, col['trim'])
        # wipers (cobwebs in his)
        for (bx, ang) in ((W * 0.28, -28), (W * 0.72, -28)):
            ex, ey = bx + 70 * math.cos(math.radians(ang)), y1 - 6 + 70 * math.sin(math.radians(ang))
            p_.line(poly([(bx, y1 - 6), (ex, ey)], False), 2.2, '#101010')
            if cobweb and kind == 'his':
                for k in range(6):
                    p_.line(smooth([(bx + 8 * k, y1 - 6 - 3 * k), (bx + 20 + 6 * k, y1 - 22 - 4 * k), (ex - 6 * k, ey - 2 * k)], False), 0.5, '#e8e4d8', 150)
                for k in range(4):
                    p_.line(smooth([(bx + 2, y1 - 8), (bx + 18 + k * 9, y1 - 30 + k * 2), (bx + 46, y1 - 14)], False), 0.4, '#e8e4d8', 110)
        if kind == 'his': p_.texture(rect(0, 0, W, H), 'grunge', 0.45, 'multiply', 2.0)
    return art


def _bus_back_art(kind, number='9'):
    col = _bus_col(kind)
    def art(p_, W, H):
        p_.fill(rect(0, 0, W, H), col['body']); p_.texture(rect(0, 0, W, H), 'grunge', 0.5 if kind == 'his' else 0.22, 'overlay', 1.2)
        btext(p_, 'SCHOOL BUS' if kind == 'bus9' else 'SCHOOL  BUS', W / 2, 27, 'head', 20, col['text'], 235 if kind == 'bus9' else 130, 'center')
        for (x, c) in ((W * 0.08, '#c87a1a'), (W * 0.16, '#a01a12'), (W * 0.84, '#a01a12'), (W * 0.92, '#c87a1a')):
            p_.fill(oval(x, 20, 9), c); p_.line(oval(x, 20, 9), 1.2)
        # the emergency door with its window, the two rear windows
        p_.fill(rrect(W / 2 - 50, 40, 100, H - 60, 4), _darken(col['body'], 0.06)); p_.line(rrect(W / 2 - 50, 40, 100, H - 60, 4), 2.0, col['trim'])
        p_.fill(rrect(W / 2 - 40, 50, 80, 70, 6), col['glass']); p_.line(rrect(W / 2 - 40, 50, 80, 70, 6), 2.5, col['trim'])
        for a in (16, W - 86):
            p_.fill(rrect(a, 50, 70, 70, 6), col['glass']); p_.line(rrect(a, 50, 70, 70, 6), 2.5, col['trim'])
        btext(p_, 'EMERGENCY DOOR', W / 2, 136, 'sans_b', 8, col['text'], 200 if kind == 'bus9' else 90, 'center')
        for x in (W * 0.1, W * 0.9):
            p_.fill(rrect(x - 12, H - 70, 24, 34, 4), '#5a0a08'); p_.line(rrect(x - 12, H - 70, 24, 34, 4), 1.0)
        if kind == 'bus9':
            btext(p_, number, W / 2, H - 20, 'head', 22, col['text'], 230, 'center')
        for (yy, hh) in ((150, 5), (200, 6)):
            p_.fill(rect(0, yy, W / 2 - 52, hh), col['rail']); p_.fill(rect(W / 2 + 52, yy, W / 2 - 52, hh), col['rail'])
        if kind == 'his': p_.texture(rect(0, 0, W, H), 'grunge', 0.45, 'multiply', 2.0)
    return art


def _bus_hood_art(kind):
    col = _bus_col(kind)
    def art(p_, W, H):
        p_.fill(rect(0, 0, W, H), col['body']); p_.texture(rect(0, 0, W, H), 'grunge', 0.4 if kind == 'his' else 0.2, 'overlay', 1.0)
        g = rrect(W * 0.3, H * 0.18, W * 0.4, H * 0.55, 6)
        p_.fill(g, '#1a1a1a'); p_.line(g, 1.5)
        for k in range(7): p_.fill(rect(W * 0.3 + 4, H * 0.18 + 6 + k * H * 0.075, W * 0.4 - 8, 2.5), '#5a5a5a' if kind == 'bus9' else '#3a3a2a')
        for x in (W * 0.14, W * 0.86):
            p_.fill(oval(x, H * 0.42, 13), '#2a2a2a'); p_.fill(oval(x, H * 0.42, 9), '#d8d4c0' if kind == 'bus9' else '#8a7a50'); p_.line(oval(x, H * 0.42, 13), 1.2)
        if kind == 'his': p_.texture(rect(0, 0, W, H), 'grunge', 0.45, 'multiply', 2.0)
    return art


def _wheel_part(B, n, side, G, r=0.5):
    """A wheel on the body side: n along the bus (local), side +1 (Box +u = its left) / -1."""
    def fn(pen, v):
        u = side * (B.w / 2 + 0.015)
        pts = [B.at(u, n + math.cos(a) * r, G + r + math.sin(a) * r) for a in np.linspace(0, 2 * math.pi, 22)]
        q = v.poly3(pts)
        if q.isEmpty(): return
        nrm = (B.U[0] * side, 0.0, B.U[1] * side)
        if not v.visible(pts[0], nrm): return
        pen.fill(q, '#141414'); pen.line(q, 1.0)
        pts2 = [B.at(u + side * 0.01, n + math.cos(a) * r * 0.52, G + r + math.sin(a) * r * 0.52) for a in np.linspace(0, 2 * math.pi, 18)]
        q2 = v.poly3(pts2)
        if not q2.isEmpty(): pen.fill(q2, lit('#8a8a80', pts2[0], nrm)); pen.line(q2, 0.8)
    return Part(fn=fn, ref=B.at(side * B.w / 2, n, G + r), tag='wheel')


def bu_bus_parts(cx, cy, fa, kind='bus9', G=BU_G, cobweb=False, mirror_l=True, mirror_r=True, number='9'):
    """The bus as Parts (body, hood, fenders, bumpers, wheels, mirrors). See the section note."""
    col = _bus_col(kind)
    body, hood, Lb = bu_bus_frame(cx, cy, fa, G)
    rr = 0.32 if kind == 'his' else 0.14
    def rshape(W, H, r=rr * 100): return rrect(0, 0, W, H + r, r)
    def body_fn(pen, v):
        fs = body.faces()
        order = sorted(fs.items(), key=lambda kv: -v.d(kv[1].centre()[0], kv[1].centre()[2]))
        for nm, F in order:
            if nm == 'bottom': continue
            if nm == 'left': draw_face(pen, v, F, _bus_side_art(kind, 'door', Lb, number), col['body'], lw=1.2)
            elif nm == 'right': draw_face(pen, v, F, _bus_side_art(kind, 'driver', Lb, number), col['body'], lw=1.2)
            elif nm == 'front': draw_face(pen, v, F, _bus_front_art(kind, cobweb), col['body'], lw=1.2, shape=rshape(F.W, F.H))
            elif nm == 'back': draw_face(pen, v, F, _bus_back_art(kind, number), col['body'], lw=1.2, shape=rshape(F.W, F.H))
            elif nm == 'top':
                draw_face(pen, v, F, lambda p_, W, H: (p_.fill(rect(0, 0, W, H), col['roof']), p_.texture(rect(0, 0, W, H), 'grunge', 0.5, 'overlay', 2.0),
                                                       [p_.fill(rect(0, k * 70, W, 3), _darken(col['roof'], 0.2), 160) for k in range(int(H / 70))]), col['roof'], lw=1.2)
        if kind == 'his':                                                        # the rounded crown along the roof
            cr = Box(body.cx, body.cy, body.w - 0.5, body.d - 0.3, body.Y1, body.Y1 + 0.12, body.fa)
            draw_box(pen, v, cr, {'all': _darken(col['roof'], 0.05), 'top': col['roof']}, lw=0.8)
    P = [Part(fn=body_fn, ref=(body.cx, G + 1.5, body.cy), tag='body')]
    P.append(Part(hood, {'front': dict(fill=col['body'], art=_bus_hood_art(kind)), 'all': col['body'], 'top': _darken(col['body'], 0.04)}, tag='hood'))
    fen = sub(hood, -1.17, 1.17, -0.68, 0.55, G + 0.45, G + 1.2)
    P.append(Part(fen, {'all': _darken(col['body'], 0.06), 'top': col['body'], 'front': '#1a1a1a'}, tag='fender'))
    th = math.radians(fa); N = (math.sin(th), -math.cos(th))
    fb = Box(cx + N[0] * (BU_BUS_L / 2 + 0.08), cy + N[1] * (BU_BUS_L / 2 + 0.08), 2.3, 0.16, G + 0.35, G + 0.6, fa)
    rb = Box(cx - N[0] * (BU_BUS_L / 2 + 0.08), cy - N[1] * (BU_BUS_L / 2 + 0.08), 2.4, 0.16, G + 0.35, G + 0.6, fa)
    P += [Part(fb, {'all': '#141414'}, tag='bumper'), Part(rb, {'all': '#141414'}, tag='bumper')]
    n_front = Lb / 2 + BU_BUS_HOOD * 0.45; n_rear = -Lb / 2 + 2.3
    for n in (n_front, n_rear):
        for sd in (-1, 1):
            P.append(_wheel_part(body, n, sd, G))
    for sd, ok in ((-1, mirror_r), (1, mirror_l)):                               # big side mirrors on arms (-u = the door side)
        if not ok: continue
        def mfn(pen, v, sd=sd):
            A = body.at(sd * (body.w / 2), body.d / 2 - 0.05, G + 2.0)
            Bm = body.at(sd * (body.w / 2 + 0.32), body.d / 2 + 0.15, G + 2.1)
            pen.seg(v.p(*A), v.p(*Bm), max(1.0, 0.03 * v.s(A[0], A[2])), '#1a1a1a')
            mb = Box(Bm[0], Bm[2], 0.22, 0.08, G + 1.85, G + 2.3, body.fa)
            draw_box(pen, v, mb, {'all': '#1a1a1a', 'front': '#2a2a2a', 'back': dict(fill='#3a4048', art=lambda p_, W, H: p_.fill(rect(2, 2, W - 4, H - 4), '#5a6878'))}, lw=0.8)
        P.append(Part(fn=mfn, ref=body.at(sd * (body.w / 2 + 0.3), body.d / 2 + 0.1, G + 2.0), tag='mirror'))
    if not mirror_r:                                                             # the stub of the ripped-off mirror arm
        def stub(pen, v):
            A = body.at(-(body.w / 2), body.d / 2 - 0.05, G + 2.0); Bm = body.at(-(body.w / 2 + 0.12), body.d / 2 + 0.03, G + 2.04)
            pen.seg(v.p(*A), v.p(*Bm), max(1.0, 0.03 * v.s(A[0], A[2])), '#1a1a1a')
        P.append(Part(fn=stub, ref=body.at(-(body.w / 2 + 0.1), body.d / 2, G + 2.0), tag='mirror'))
    return P


def bu_bus_door_quad(cx, cy, fa, G=BU_G):
    """3D corners of the entrance doorway on the door side (rear-bottom, front-bottom, front-top, rear-top)."""
    body, hood, Lb = bu_bus_frame(cx, cy, fa, G)
    u = -(body.w / 2 + 0.005)
    n0 = Lb / 2 - 1.28; n1 = Lb / 2 - 0.24
    return [body.at(u, n0, G + 0.3), body.at(u, n1, G + 0.3), body.at(u, n1, G + BU_BUS_Y1 - 0.16), body.at(u, n0, G + BU_BUS_Y1 - 0.16)]


def bu_bus_door(pen, v, cx, cy, fa, kind='his', k=0.0, G=BU_G, inside=None, broom=0.0, bend=0.0, crack=0.0, amber=1.0):
    """The folding entrance door, k 0 closed .. 1 open: two glass leaves per side folding to the jambs; inside (when
    open) the steps and the amber (his) / warm (bus 9) light; broom > 0: the porch broom wedged across the opening."""
    q = bu_bus_door_quad(cx, cy, fa, G)
    if v.d((q[0][0] + q[1][0]) / 2, (q[0][2] + q[1][2]) / 2) < 0.3: return
    body, hood, Lb = bu_bus_frame(cx, cy, fa, G)
    if not v.visible(q[0], (-body.U[0], 0.0, -body.U[1])): return
    def P(f, h): return (q[0][0] + (q[1][0] - q[0][0]) * f, q[0][1] + h, q[0][2] + (q[1][2] - q[0][2]) * f)
    Hd = q[3][1] - q[0][1]
    path = v.poly3(q)
    inner = '#2a1a08' if kind == 'his' else '#1a1a1e'
    pen.fill(path, inner)
    if k > 0.02:                                                                  # the steps and the light inside
        for i in range(3):
            st = v.poly3([P(0.08, 0.05 + i * 0.22), P(0.92, 0.05 + i * 0.22), P(0.92, 0.12 + i * 0.22), P(0.08, 0.12 + i * 0.22)])
            pen.fill(st, '#3a3020' if kind == 'his' else '#3a3a3e', 220)
        b = path.computeTightBounds()
        if kind == 'his':
            pen.linear(path, 0, b.top(), 0, b.bottom(), [(0, '#ffd890', 235 * amber * k), (0.45, BU_AMBER, 215 * amber * k), (1, '#7a4010', 170 * k)])
            pen.glow((b.left() + b.right()) / 2, (b.top() + b.bottom()) / 2, b.width() * 1.2, BU_AMBER, 70 * amber * k)
        else:
            pen.linear(path, 0, b.top(), 0, b.bottom(), [(0, '#ffe0a8', 120 * k), (1, '#3a3020', 80 * k)])
    leaf = 0.5 * (1.0 - 0.82 * k)
    gl = '#0e0c08' if kind == 'his' else '#18202a'
    for side in (0, 1):
        f0, f1 = (0.0, leaf) if side == 0 else (1.0 - leaf, 1.0)
        for (fa_, fb_) in ((f0, (f0 + f1) / 2), ((f0 + f1) / 2, f1)):
            lp = v.poly3([P(fa_, 0.0), P(fb_, 0.0), P(fb_, Hd), P(fa_, Hd)])
            pen.fill(lp, _bus_col(kind)['trim']); pen.line(lp, 1.0)
            g1 = v.poly3([P(fa_ + 0.012, Hd * 0.52), P(fb_ - 0.012, Hd * 0.52), P(fb_ - 0.012, Hd - 0.05), P(fa_ + 0.012, Hd - 0.05)])
            g2 = v.poly3([P(fa_ + 0.012, 0.06), P(fb_ - 0.012, 0.06), P(fb_ - 0.012, Hd * 0.48), P(fa_ + 0.012, Hd * 0.48)])
            for g in (g1, g2):
                if not g.isEmpty():
                    pen.fill(g, gl, 230)
                    if kind == 'his' and amber > 0: pen.fill(g, BU_AMBER, 60 * amber)
    pen.line(path, 2.0)
    if broom > 0.01:
        A = P(-0.25, Hd * 0.55); B_ = P(1.25, Hd * 0.42)
        bu_broom(pen, v, A, B_, broom, bend, crack)


def bu_bus_emit(pen, v, cx, cy, fa, kind='his', win=1.0, heads=0.0, flash=0.0, tail=0.0, brake=0.0, G=BU_G, seats=None, t=0.0):
    """Emissive light of a bus (live): win = amber / warm window glow (seats = {window index: level} overrides), heads
    = headlights (+ beams on the road), flash = the roof flashers, tail / brake = rear lamps."""
    body, hood, Lb = bu_bus_frame(cx, cy, fa, G)
    c = BU_AMBER if kind == 'his' else '#ffe2a8'
    top = 0.26 if kind == 'bus9' else 0.34
    for side, sd in (('door', -1), ('driver', 1)):
        u = sd * (body.w / 2 + 0.006)
        if not v.visible(body.at(u, 0, G + 2), (body.U[0] * sd, 0.0, body.U[1] * sd)): continue
        for i, (a, b) in enumerate(_win_xs(Lb, side)):
            k = win if not seats else seats.get(i, 0.0)
            if callable(k): k = k(t)
            if k <= 0.01: continue
            def nn(cm): return (Lb / 2 - cm / 100.0) * (1 if side == 'driver' else -1) * -1 if False else ((-Lb / 2 + cm / 100.0) if side == 'door' else (Lb / 2 - cm / 100.0))
            Yt = G + BU_BUS_Y1 - top; Yb = Yt - 0.74
            q = v.poly3([body.at(u, nn(a), Yt), body.at(u, nn(b), Yt), body.at(u, nn(b), Yb), body.at(u, nn(a), Yb)])
            if q.isEmpty(): continue
            bb = q.computeTightBounds()
            pen.linear(q, 0, bb.top(), 0, bb.bottom(), [(0, mix(c, '#fff4d8', 0.35), 230 * k), (1, c, 200 * k)])
            pen.glow((bb.left() + bb.right()) / 2, (bb.top() + bb.bottom()) / 2, (bb.right() - bb.left()) * 0.9, c, 50 * k)
    th = math.radians(fa); N = (math.sin(th), -math.cos(th))
    if heads > 0.01:
        for sd in (-1, 1):
            P = hood.at(sd * hood.w * 0.36, hood.d / 2 + 0.02, G + 1.08)
            if v.d(P[0], P[2]) < 0.3: continue
            if not v.visible(P, (N[0], 0.0, N[1])): continue
            x, y = v.p(*P); s = v.s(P[0], P[2])
            pen.glow(x, y, 0.9 * s, BU_HEADS if kind == 'his' else '#fff2d6', 160 * heads)
            pen.glow(x, y, 0.2 * s, '#ffffff', 240 * heads)
        # the beams on the road ahead (a soft wedge of light on the ground)
        A = hood.at(0, hood.d / 2, G); far = (A[0] + N[0] * 14, A[2] + N[1] * 14)
        L_ = (far[0] - (-N[1]) * 3.5, far[1] - N[0] * 3.5); R_ = (far[0] + (-N[1]) * 3.5, far[1] + N[0] * 3.5)
        wq = v.poly3([(A[0] + N[1] * 0.9, G + 0.01, A[2] - N[0] * 0.9), (A[0] - N[1] * 0.9, G + 0.01, A[2] + N[0] * 0.9), (R_[0], G + 0.01, R_[1]), (L_[0], G + 0.01, L_[1])])
        if not wq.isEmpty():
            bb = wq.computeTightBounds(); x0, y0 = v.p(A[0], G, A[2])
            pen.radial(wq, x0, y0, max(40.0, max(bb.width(), bb.height())), [(0, BU_HEADS if kind == 'his' else '#fff2d6', 90 * heads), (1, '#ffd890', 0)], clip=True)
    if flash > 0.01:
        for (u, nn_, c2) in ((-0.95, 1, '#ff2a1a'), (0.95, 1, '#ff2a1a'), (-1.1, 1, '#ffa01a'), (1.1, 1, '#ffa01a')):
            P = body.at(u, body.d / 2 + 0.01, G + BU_BUS_Y1 - 0.2)
            if v.d(P[0], P[2]) < 0.3 or not v.visible(P, (N[0], 0.0, N[1])): continue
            x, y = v.p(*P); s = v.s(P[0], P[2])
            pen.glow(x, y, 0.5 * s, c2, 160 * flash)
    if tail > 0.01 or brake > 0.01:
        k = max(tail * 0.5, brake)
        for sd in (-1, 1):
            P = body.at(sd * body.w * 0.4, -body.d / 2 - 0.01, G + 0.95)
            if v.d(P[0], P[2]) < 0.3 or not v.visible(P, (-N[0], 0.0, -N[1])): continue
            x, y = v.p(*P); s = v.s(P[0], P[2])
            pen.glow(x, y, (0.5 + 0.6 * brake) * s, '#ff2414', 170 * k)
            pen.glow(x, y, 0.12 * s, '#ffd0c0', 220 * k)


def bu_bus_piece(name, cx, cy, fa, kind, G=BU_G, door=0.0, broom=0.0, bend=0.0, crack=0.0, cobweb=False, mirror_r=True, occupants=None, amber=1.0):
    """A bus as one Piece of a set (its door drawn into it when `door` is a number; a live layer when it is f(t))."""
    parts = bu_bus_parts(cx, cy, fa, kind, G, cobweb, mirror_r=mirror_r)
    if not callable(door) and not callable(broom) and not callable(bend) and not callable(crack):
        parts.append(Part(fn=lambda pen, v: bu_bus_door(pen, v, cx, cy, fa, kind, door, G, broom=broom, bend=bend, crack=crack, amber=amber),
                          ref=bu_bus_door_quad(cx, cy, fa, G)[1], tag='door'))
    body, hood, Lb = bu_bus_frame(cx, cy, fa, G)
    return Piece(name, (cx, G + 1.5, cy), lambda pen, v, ps=parts: draw_parts(pen, v, ps), occupant=occupants, front=parts if occupants else None,
                 block=[(body.at(u, n, 0)[0], body.at(u, n, 0)[2]) for (u, n) in ((-1.25, -Lb / 2), (1.25, -Lb / 2), (1.25, Lb / 2 + BU_BUS_HOOD), (-1.25, Lb / 2 + BU_BUS_HOOD))])


def bu_bus_spots(v, pre, cx, cy, fa, G=BU_G, kind='his'):
    """Spots on a bus seen from outside: <pre>door (on the ground at the door, facing it), <pre>step (the bottom step,
    0.3 m up), <pre>top (the top of the steps inside, facing out), <pre>driver (the driver's seat, hip point),
    <pre>window<i> (window i of the door side: a point at the glass)."""
    body, hood, Lb = bu_bus_frame(cx, cy, fa, G)
    S = {}
    U, N = body.U, body.N
    def plan(u, n): p_ = body.at(u, n, 0); return p_[0], p_[2]
    nd = Lb / 2 - 0.76
    x, y = plan(-(body.w / 2 + 0.55), nd); S[pre + 'door'] = _mk_spot(v, pre + 'door', x, y, G, 'stand', 'on the ground at the bus door, facing it', face=(U[0], U[1]))
    x, y = plan(-(body.w / 2 - 0.05), nd); S[pre + 'step'] = _mk_spot(v, pre + 'step', x, y, G + 0.3, 'stand', 'on the bottom step of the bus door', face=(U[0], U[1]))
    x, y = plan(-(body.w / 2 - 0.75), nd); S[pre + 'top'] = _mk_spot(v, pre + 'top', x, y, G + BU_BUS_FLOOR, 'stand', 'at the top of the steps inside (facing out of the door)', face=(-U[0], -U[1]))
    x, y = plan(body.w / 2 - 0.55, Lb / 2 - 0.6); S[pre + 'driver'] = _mk_spot(v, pre + 'driver', x, y, G + BU_BUS_FLOOR, 'seat', "the driver's seat", face=(N[0], N[1]), seat_Y=0.45)
    for i, (a, b) in enumerate(_win_xs(Lb, 'door')):
        n = -Lb / 2 + (a + b) / 200.0
        x, y = plan(-(body.w / 2 + 0.01), n)
        S['%swindow%d' % (pre, i)] = _mk_spot(v, '%swindow%d' % (pre, i), x, y, G + BU_BUS_Y1 - 0.65, 'point', 'door-side window %d (0 = rear)' % i)
    return S


# ====================================================================================================== outside: Larch Street
BU_WINS_EXT = {   # windows on the house outside: name -> (wall, (u0, u1) along the wall plan coordinate, sill, top, Y base)
    'hall': ('west', (BU_HWIN[0], BU_HWIN[1]), BU_HWIN[2], BU_HWIN[3], 0.0),
    'liv': ('front', (BU_PWIN[0], BU_PWIN[1]), BU_PWIN[2], BU_PWIN[3], 0.0),
    'den': ('front', (2.5, 3.6), 0.9, 2.05, 0.0),
    'gran': ('front', (BU_GFWIN[0], BU_GFWIN[1]), BU_GFWIN[2], BU_GFWIN[3], BU_UP),
    'gran_w': ('west', (BU_GWIN[0], BU_GWIN[1]), BU_GWIN[2], BU_GWIN[3], BU_UP),
    'mina': ('front', (-0.6, 0.4), 0.85, 2.05, BU_UP),
    'mina2': ('front', (2.3, 3.3), 0.85, 2.05, BU_UP),
    'sami': ('back', (BU_SWIN[0], BU_SWIN[1]), BU_SWIN[2], BU_SWIN[3], BU_UP),
    'kitchen': ('back', (0.6, 1.8), 1.0, 2.0, 0.0),
}
_WALL_PTS = {'front': ((-5.6, 0.0), (4.6, 0.0)), 'west': ((-5.6, 9.6), (-5.6, 0.0)), 'east': ((4.6, 0.0), (4.6, 9.6)), 'back': ((4.6, 9.6), (-5.6, 9.6))}
BU_EAVE, BU_RIDGE, BU_RIDGE_Y = BU_UP + BU_UH, 7.7, 4.8


def _ext_quad(wall_, u0, u1, Y0, Y1, off=0.0):
    a, b = _WALL_PTS[wall_]
    def P(c, Y):
        if wall_ in ('front', 'back'): return (c, Y, a[1] - off if wall_ == 'front' else a[1] + off)
        return (a[0] - off if wall_ == 'west' else a[0] + off, Y, c)
    return [P(u0, Y1), P(u1, Y1), P(u1, Y0), P(u0, Y0)]


def bu_house_ext(pen, v, o):
    """Grandma Della's house from outside: pale butter clapboard, dark green shutters, the deep red front door, a grey
    shingle gable roof, the porch (bu_porch). Window glows are live (bu_house_glow)."""
    tod = o.get('tod', 'night'); night = tod == 'night'
    sid = BU_PAL['siding']
    G = BU_G
    for wall_, (a, b) in _WALL_PTS.items():
        F = wall_face(a, b, G, BU_EAVE)
        if not v.visible(F.O, F.n): continue
        def art(p_, W, H, wall_=wall_, a=a, b=b):
            pat(p_, W, H, 'clapboard', '#000000', 120)
            p_.texture(rect(0, 0, W, H), 'grunge', 0.3, 'overlay', 1.2)
            p_.fill(rect(0, H - (0.0 - G) * 100 - 2, W, (0.0 - G) * 100 + 2), '#7a6e62')                 # the foundation
            p_.texture(rect(0, H - (0.0 - G) * 100, W, (0.0 - G) * 100), 'grunge', 0.6, 'overlay', 1.0)
            p_.fill(rect(0, H - (BU_UP - G) * 100 - 6, W, 8), '#efe6d2')                                   # the band between floors
            u_of, L = _u_of(a, b)
            for nm, (w_, (c0, c1), sl, tp, Yb) in BU_WINS_EXT.items():
                if w_ != wall_: continue
                ua, ub = sorted((u_of(c0, a[1]) if wall_ in ('front', 'back') else u_of(a[0], c0), u_of(c1, a[1]) if wall_ in ('front', 'back') else u_of(a[0], c1)))
                ua *= 100; ub *= 100
                yt = H - (Yb + tp - G) * 100; yb = H - (Yb + sl - G) * 100
                for sx in (ua - 34, ub + 6):                                                               # shutters
                    p_.fill(rect(sx, yt, 28, yb - yt), BU_PAL['shutter']); p_.line(rect(sx, yt, 28, yb - yt), 0.8)
                    for k in range(int((yb - yt) / 9)): p_.fill(rect(sx + 3, yt + 4 + k * 9, 22, 2), '#000000', 70)
                p_.fill(rect(ua - 6, yt - 8, ub - ua + 12, yb - yt + 16), '#f2ebdc')
                p_.fill(rect(ua, yt, ub - ua, yb - yt), '#10141c' if night else '#5a6a7a')
                p_.linear(rect(ua, yt, ub - ua, yb - yt), ua, yt, ub, yb, [(0, '#ffffff', 0), (0.5, '#a8b8d8', 40 if night else 90), (1, '#ffffff', 0)])
                nl = 2
                for k in range(1, nl): p_.fill(rect(ua + (ub - ua) * k / nl - 2, yt, 4, yb - yt), '#f2ebdc')
                p_.fill(rect(ua, (yt + yb) / 2 - 2, ub - ua, 4), '#f2ebdc')
                p_.fill(rect(ua - 10, yb, ub - ua + 20, 6), '#e8dfcc')
            if wall_ == 'front':                                                                           # the front door + casing
                ua, ub = u_of(BU_FDOOR[0], 0) * 100, u_of(BU_FDOOR[1], 0) * 100
                yt = H - (BU_FDOOR[2] - G) * 100; yb = H - (0.0 - G) * 100
                p_.fill(rect(ua - 12, yt - 14, ub - ua + 24, yb - yt + 14), '#f2ebdc'); p_.line(rect(ua - 12, yt - 14, ub - ua + 24, yb - yt + 14), 0.8)
                if not o.get('door_open'):
                    p_.cv.save(); p_.cv.translate(ua, yt)
                    bu_front_door_art('out', frost_lit=o.get('frost_lit', 0.0))(p_, ub - ua, yb - yt)
                    p_.cv.restore()
                else:
                    p_.fill(rect(ua, yt, ub - ua, yb - yt), '#2a2018')
                bx = u_of(-2.95, 0) * 100                                                                  # house number by the door
                btext(p_, BU_HOUSE_NO, bx, H - (1.75 - G) * 100, 'serif_b', 14, '#2a2a2a', 220, 'center')
            if wall_ == 'back':
                ua, ub = sorted((u_of(BU_BDOOR[0], 9.6) * 100, u_of(BU_BDOOR[1], 9.6) * 100))
                yt = H - (BU_BDOOR[2] - G) * 100; yb = H - (0.0 - G) * 100
                p_.fill(rect(ua - 8, yt - 10, ub - ua + 16, yb - yt + 10), '#f2ebdc'); p_.fill(rect(ua, yt, ub - ua, yb - yt), '#5a4a3a')
                p_.fill(rect(ua + 10, yt + 12, ub - ua - 20, 80), '#10141c')
        draw_face(pen, v, F, art, sid, ao=False, lw=1.2)
    # the roof: two slopes over the front / back walls, gables on the west / east walls
    x0, x1 = -5.95, 4.95
    for (q, n) in (([(x0, BU_EAVE, -0.35), (x1, BU_EAVE, -0.35), (x1, BU_RIDGE, BU_RIDGE_Y), (x0, BU_RIDGE, BU_RIDGE_Y)], (0, 0.8, -0.6)),
                   ([(x1, BU_EAVE, 9.95), (x0, BU_EAVE, 9.95), (x0, BU_RIDGE, BU_RIDGE_Y), (x1, BU_RIDGE, BU_RIDGE_Y)], (0, 0.8, 0.6))):
        cen = (sum(p_[0] for p_ in q) / 4, sum(p_[1] for p_ in q) / 4, sum(p_[2] for p_ in q) / 4)
        if not v.visible(cen, _norm3(n)): continue
        path = v.poly3(q)
        if path.isEmpty(): continue
        pen.fill(path, lit(BU_PAL['roof'], cen, _norm3(n)))
        b = path.computeTightBounds()
        for k in range(14):                                                        # shingle courses
            f = (k + 0.5) / 14
            A = (q[0][0], q[0][1] + (q[3][1] - q[0][1]) * f, q[0][2] + (q[3][2] - q[0][2]) * f)
            B_ = (q[1][0], A[1], A[2])
            if v.d(A[0], A[2]) > 0.3 and v.d(B_[0], B_[2]) > 0.3: pen.seg(v.p(*A), v.p(*B_), 1.0, '#000000', 80)
        pen.line(path, 1.2)
    for (xx, n) in ((-5.6, (-1, 0, 0)), (4.6, (1, 0, 0))):
        tri = [(xx, BU_EAVE, 0.0), (xx, BU_EAVE, 9.6), (xx, BU_RIDGE - 0.15, BU_RIDGE_Y)]
        if not v.visible(tri[2], n): continue
        path = v.poly3(tri)
        if not path.isEmpty():
            pen.fill(path, lit(_darken(sid, 0.05), tri[2], n)); pen.line(path, 1.0)
    # chimney
    cB = Box(2.9, 5.6, 0.7, 0.6, BU_RIDGE - 1.6, BU_RIDGE + 0.9, 0)
    draw_box(pen, v, cB, {'all': '#7a3a2e', 'top': '#2a2a2a'}, lw=1.0)


def bu_porch(pen, v, o):
    """The porch deck, three steps down to the walk, two posts, its little roof, the railing; the porch broom leaning
    by the door (o['broom'] == 'porch')."""
    x0, x1, y0, y1 = BU_PORCH
    G = BU_G
    deck = Box((x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0, G, 0.0, 0)
    draw_box(pen, v, deck, {'top': dict(fill='#8a7a6a', art=lambda p_, W, H: pat(p_, W, H, 'boards', '#3a2e22', 150, 5)), 'all': '#e8e0cc'}, lw=1.0)
    sx0, sx1, sy0, sy1 = BU_STEPS
    n = 3; run = (sy1 - sy0) / n; rise = (0.0 - G) / n
    for i in range(n):
        B = Box((sx0 + sx1) / 2, sy0 + (i + 0.5) * run + 0.0, sx1 - sx0, (sy1 - sy0) - i * run, G, G + (i + 1) * rise, 0)
        B = Box((sx0 + sx1) / 2, (sy0 + i * run + sy1) / 2, sx1 - sx0, sy1 - (sy0 + i * run), G, G + (i + 1) * rise, 0)
        draw_box(pen, v, B, {'top': '#8a7a6a', 'front': '#e8e0cc', 'sides': '#d8d0bc'}, lw=0.8)
    # posts, roof, railing (west part only: the steps are open)
    for (px, py) in ((x0 + 0.08, y0 + 0.08), (x1 - 0.08, y0 + 0.08)):
        draw_box(pen, v, Box(px, py, 0.12, 0.12, 0.0, 2.6, 0), {'all': '#f2ebdc'}, lw=0.8)
    rq = [(x0 - 0.15, 2.62, y0 - 0.2), (x1 + 0.15, 2.62, y0 - 0.2), (x1 + 0.15, 2.95, 0.0), (x0 - 0.15, 2.95, 0.0)]
    if v.cam_h < 2.7:
        pq = v.poly3([(x0 - 0.15, 2.62, y0 - 0.2), (x1 + 0.15, 2.62, y0 - 0.2), (x1 + 0.15, 2.62, 0.0), (x0 - 0.15, 2.62, 0.0)])
        if not pq.isEmpty(): pen.fill(pq, lit('#d8d0c0', (x0, 2.6, -0.9), (0, -1, 0))); pen.line(pq, 0.8)
    else:
        pq = v.poly3(rq)
        if not pq.isEmpty(): pen.fill(pq, lit(BU_PAL['roof'], ((x0 + x1) / 2, 2.8, -1.0), _norm3((0, 0.85, -0.5)))); pen.line(pq, 1.0)
    fq = v.poly3([(x0 - 0.15, 2.72, y0 - 0.2), (x1 + 0.15, 2.72, y0 - 0.2), (x1 + 0.15, 2.52, y0 - 0.2), (x0 - 0.15, 2.52, y0 - 0.2)])
    if not fq.isEmpty() and v.visible((x0, 2.6, y0 - 0.2), (0, 0, -1)): pen.fill(fq, lit('#f2ebdc', (x0, 2.6, y0 - 0.2), (0, 0, -1))); pen.line(fq, 0.8)
    for (ax, bx) in ((x0 + 0.08, sx0 - 0.02), (sx1 + 0.02, x1 - 0.08)):
        A = (ax, 0.85, y0 + 0.08); B_ = (bx, 0.85, y0 + 0.08)
        if v.d(A[0], A[2]) > 0.3 and v.d(B_[0], B_[2]) > 0.3:
            pen.seg(v.p(*A), v.p(*B_), max(1.2, 0.05 * v.s(A[0], A[2])), lit('#f2ebdc', A, (0, 0, -1)))
            for k in range(int((bx - ax) / 0.12)):
                xx = ax + 0.06 + k * 0.12
                pen.seg(v.p(xx, 0.05, y0 + 0.08), v.p(xx, 0.85, y0 + 0.08), max(0.8, 0.02 * v.s(xx, y0)), lit('#f2ebdc', A, (0, 0, -1)))
    # the porch light lantern (its glow is live)
    lx, lY, ly = BU_PLIGHT
    if v.d(lx, ly) > 0.3:
        draw_box(pen, v, Box(lx, ly - 0.05, 0.14, 0.12, lY - 0.12, lY + 0.12, 0), {'all': '#1a1a1a', 'front': '#d8c890'}, lw=0.8)
    if o.get('broom') == 'porch':
        bu_broom(pen, v, (-4.62, 0.05, -0.12), (-4.95, 1.38, -0.05))


def bu_mailbox(pen, v, letters=1.0, x=None, y=None, G=BU_G, flag=False):
    """Our mailbox at the kerb: a black box on a white post, the family name in stick-on letters on both sides and the
    house number on the post. letters 0..1: how many letters are still on (0 = all unscrewed: pale ghost outlines)."""
    x = BU_MAILBOX[0] if x is None else x; y = BU_MAILBOX[1] if y is None else y
    if v.d(x, y) < 0.3: return
    s = v.s(x, y)
    pen.fill(ellipse3(v, x, y, 0.18, 0.1, G), '#000000', 90)
    draw_box(pen, v, Box(x, y, 0.09, 0.09, G, G + 1.0, 0), {'all': '#f2ebdc', 'front': dict(fill='#f2ebdc', art=lambda p_, W, H: btext(p_, BU_HOUSE_NO, W / 2, 26, 'serif_b', 6, '#1a1a1a', 230, 'center'))}, lw=0.8)
    B = Box(x, y, 0.22, 0.48, G + 1.0, G + 1.22, 90)
    nm = BU_NAME
    def side(p_, W, H):
        p_.fill(rect(0, 0, W, H), '#1e2226'); p_.texture(rect(0, 0, W, H), 'grunge', 0.4, 'overlay', 0.8)
        n_on = int(round(clamp(letters) * len(nm)))
        cw = (W - 8) / len(nm)
        for i, ch in enumerate(nm):
            cx = 4 + cw * (i + 0.5)
            if i < n_on:
                p_.fill(rect(cx - cw * 0.42, 5, cw * 0.84, H - 10), '#f4f0e0', 240)
                btext(p_, ch, cx, H - 6, 'sans_b', H * 0.6, '#1a1a1a', 250, 'center')
            else:
                p_.line(rect(cx - cw * 0.42, 5, cw * 0.84, H - 10), 0.5, '#8a8a7a', 120)
                p_.fill(oval(cx, 6.5, 0.6), '#8a8a8a'); p_.fill(oval(cx, H - 6.5, 0.6), '#8a8a8a')
    draw_box(pen, v, B, {'left': dict(fill='#1e2226', art=side), 'right': dict(fill='#1e2226', art=side), 'top': '#2a3036', 'all': '#1e2226'}, lw=0.8)
    if flag:
        A = B.at(0.12, 0.1, G + 1.15)
        pen.seg(v.p(*A), v.p(A[0], G + 1.4, A[2]), max(1.0, 0.012 * s), '#c82a1a')


def bu_ground(pen, v, tod='night'):
    """Lawns, the walk, the driveway, sidewalks, Larch Street (dry asphalt, the sodium pools are live)."""
    G = BU_G
    night = tod == 'night'
    grass = '#1c2a24' if night else '#4a6a3a'
    F = floor_face(-130.0, 130.0, -130.0, 30.0, G)
    def lawn(p_, W, H):
        p_.linear(rect(0, 0, W, H), 0, 0, 0, H, [(0, grass, 255), (1, _darken(grass, 0.25), 255)])
        p_.texture(rect(0, 0, W, H), 'grunge', 0.6, 'overlay', 5.0); p_.texture(rect(0, 0, W, H), 'fabric', 0.4, 'overlay', 0.8)
    draw_face(pen, v, F, lawn, grass, ao=False, line=False)

    def strip(x0, x1, y0, y1, c, kind='asphalt', Y=G + 0.004, ink=None):
        Fs = floor_face(x0, x1, y0, y1, Y)
        def art(p_, W, H):
            p_.texture(rect(0, 0, W, H), kind, 0.6, 'overlay', 1.6 if kind == 'asphalt' else 0.8)
            if ink: ink(p_, W, H)
        draw_face(pen, v, Fs, art, c, ao=False, line=False)
    def street_ink(p_, W, H):
        for k in range(36): p_.fill(rect(k * 500, (D_STREET[0] - D_STREET[1]) * 50 - 5, 300, 10), '#c8a83a', 110)
        p_.fill(rect(0, 0, W, 6), '#5a5a5a', 120); p_.fill(rect(0, H - 6, W, 6), '#5a5a5a', 120)
    walk = '#5a5c60' if night else '#a8a8a0'
    strip(-90.0, 90.0, D_STREET[1], D_STREET[0], '#24262c' if night else '#4a4c50', 'asphalt', G - 0.12, street_ink)
    lines = lambda p_, W, H: [p_.fill(rect(k * 150, 0, 1.2, H), '#000000', 90) for k in range(int(W / 150))]
    strip(-90.0, 90.0, D_STREET[0], D_STREET[0] + 1.25, walk, 'asphalt', G + 0.002, lines)
    strip(-90.0, 90.0, D_STREET[1] - 1.4, D_STREET[1], walk, 'asphalt', G + 0.002, lines)
    dx0, dx1, dy0, dy1 = BU_DRIVE
    strip(dx0, dx1, dy0, dy1, '#4e5054' if night else '#a8a49a', 'asphalt', G + 0.006, lambda p_, W, H: [p_.fill(rect(0, k * 300, W, 1.2), '#000000', 90) for k in range(int(H / 300))])
    strip(BU_WALK[0], BU_WALK[1], D_STREET[0] + 1.25, BU_STEPS[2], walk, 'asphalt', G + 0.006,
          lambda p_, W, H: [p_.fill(rect(0, k * 90, W, 1.0), '#000000', 90) for k in range(int(H / 90))])
    # flower bed along the front of the house
    bed = floor_face(-5.6, 4.6, -0.7, 0.0, G + 0.01)
    draw_face(pen, v, bed, lambda p_, W, H: (p_.texture(rect(0, 0, W, H), 'grunge', 0.8, 'overlay', 2.0)), '#2a2018', ao=False, line=False)


def _shrubs(pen, v, tod='night'):
    for i, (x, y, r) in enumerate(((-5.2, -0.35, 0.45), (-2.4, -0.35, 0.5), (1.4, -0.38, 0.55), (3.9, -0.35, 0.5), (-1.0, -0.33, 0.4))):
        if v.d(x, y) < 0.6: continue
        bx, by = v.p(x, BU_G, y); s = v.s(x, y)
        _bush(pen, bx, by, 2 * r * s, 1.3 * r * s, 40 + i, '#0e1a14' if tod == 'night' else '#2a4a2a', '#1e3026' if tod == 'night' else '#4a6a3a')


def _bu_ext_light(tod):
    if tod in ('sunrise', 'dawn', 'day', 'morning'):
        return '#8a8090', [Lamp(kind='dir', c='#ffd8a0', k=1.0, d=_norm3((-0.6, -0.5, 0.6)))]
    return '#3a4672', [Lamp(kind='dir', c='#8a9ad8', k=0.5, d=_norm3((0.3, -0.8, 0.5)))]


def bu_ext_draw(pen, v, o, house=False):
    """Everything outside that does not move (cached): sky, far ring, ground, the houses across and beside, trees,
    streetlight poles, our house, porch, shrubs, the mailbox."""
    tod = o.get('tod', 'night')
    tt = 'night' if tod == 'night' else 'dawn'
    dr_sky(pen, v, tt)
    dr_far_ring(pen, v, tt)
    with lighting(*_bu_ext_light(tod)):
        bu_ground(pen, v, tod)
        for (x0, x1) in D_ACROSS:
            dr_neighbour(pen, v, x0, x1, -24.5, 9.0, tod, lit_room=(1 if x0 == -38.0 else None), seed=int(x0))
        for (x0, x1, yf, tag) in ((-22.0, -14.5, 0.0, 'w'), (8.4, 17.5, 0.0, 'e')):
            dr_neighbour(pen, v, x0, x1, yf, 10.0, tod, seed=int(x0) + 5)
        for i, (x, y, h) in enumerate([(-14.0, -21.5, 7.5), (2.0, -21.0, 7.5), (24.0, -21.8, 7.5), (-36.0, -22.0, 7.5), (3.4, -6.4, 8.5), (-12.5, 4.0, 9.0)]):
            if v.d(x, y) < 1.0: continue
            bx, by = v.p(x, BU_G, y)
            draw_tree(pen, bx, by, h * v.s(x, y), 0.0, 520 + i, 0.0, '#0e1218' if tod == 'night' else '#3a3a34', None, 5)
        for (x, y) in BU_LAMPS + ([BU_LAMP] if house == 'all' else []):
            if v.d(x, y) > 0.8: dr_streetlight(pen, v, x, y, 1.0, arm=1.0)
        if house == 'all':                                              # (outside seen through a window: everything in one go)
            bu_house_ext(pen, v, o); _shrubs(pen, v, tod); bu_porch(pen, v, o); bu_mailbox(pen, v, o.get('letters', 1.0))


def bu_ext_glow(v, o, name='ext_glow', order=None):
    """Live: the streetlights (ours flickers: o['street'] level spec), the porch light (o['porch']), the house window
    glows (o['win'] = {name: level}), the frosted door panes lit from the hall (o['frost_lit'])."""
    ks = _kfn(o.get('street', 1.0), 401); kp = _kfn(o.get('porch', 0.0), 402)
    wins = {nm: _kfn(lv, 410 + i) for i, (nm, lv) in enumerate((o.get('win') or {}).items())}
    tod = o.get('tod', 'night')
    def draw(pen, t):
        if tod == 'night':
            for (x, y) in BU_LAMPS:
                dr_streetlight_glow(pen, v, x, y, 1.0, BU_SODIUM, 1.0, rain=False, t=t)
            dr_streetlight_glow(pen, v, BU_LAMP[0], BU_LAMP[1], ks(t), BU_SODIUM, 1.0, rain=False, t=t)
    def draw_house(pen, t):
        k = kp(t)
        if k > 0.01 and v.d(BU_PLIGHT[0], BU_PLIGHT[2]) > 0.3:
            x, y = v.p(*BU_PLIGHT); s = v.s(BU_PLIGHT[0], BU_PLIGHT[2])
            pen.glow(x, y, 1.6 * s, '#ffc070', 110 * k); pen.glow(x, y, 0.12 * s, '#fff4d8', 240 * k)
            gx, gy = v.p(BU_PLIGHT[0], 0.0, -0.8)
            pen.ellipse_glow(gx, gy, 1.6 * s, 0.5 * s, '#ffc070', 60 * k)
        for nm, kf in wins.items():
            k = kf(t)
            if k <= 0.01 or nm not in BU_WINS_EXT: continue
            w_, (c0, c1), sl, tp, Yb = BU_WINS_EXT[nm]
            q = _ext_quad(w_, c0, c1, Yb + sl, Yb + tp, 0.01)
            a, b = _WALL_PTS[w_]
            F = wall_face(a, b, 0, 1)
            if not v.visible(q[0], F.n): continue
            path = v.poly3(q)
            if path.isEmpty(): continue
            bb = path.computeTightBounds()
            pen.linear(path, 0, bb.top(), 0, bb.bottom(), [(0, '#ffd090', 200 * k), (1, '#e89a48', 220 * k)])
            pen.glow((bb.left() + bb.right()) / 2, (bb.top() + bb.bottom()) / 2, bb.width(), '#ffb060', 40 * k)
    lay = Layer(30.0, draw, name, blur=None)
    lay.order = (ORDER_SHELL - 0.5) if order is None else order
    lay2 = Layer(10.0, draw_house, name + '_house', blur=None)
    lay2.order = lay.order
    return [lay, lay2]


def _bu_reorder(sp, v):
    """Painter's fix-ups the per-piece depth sort cannot know: the house (and its porch, window glows) hides bus 9 when
    the camera is east of the house's west wall; the glows sit just in front of the house."""
    L = {l.name: l for l in sp}
    if 'house' not in L: return sp
    b9 = [l.order for l in sp if l.name in ('bus9', 'bus9_front')]
    if b9 and v.hx > BU_HOUSE[0]:
        L['house'].order = min(b9) - 0.05
        if 'porch' in L: L['porch'].order = min(L['porch'].order, min(b9) - 0.06)
    for nm in ('ext_glow_house', 'outside_glow_house'):
        if nm in L: L[nm].order = min(L['house'].order, L.get('porch', L['house']).order) - 0.01
    return sp


class BuStreet(Room):
    """Larch Street as a room: the shell is bu_ext_draw; the pieces are bus 9 (driveway) and his bus (kerb)."""
    name = 'street'
    poly = [(-90.0, -40.0), (90.0, -40.0), (90.0, 30.0), (-90.0, 30.0)]

    def lights(self, o):
        tod = o.get('tod', 'night')
        amb, steady = _bu_ext_light(tod)
        steady = list(steady)
        if tod == 'night':
            for (x, y) in BU_LAMPS:
                steady.append(Lamp(x, BU_G + 6.0, y - 1.6, 14.0, BU_SODIUM, 1.9, (1.0, 0.6, 0.2), fall=1.35))
        street = [Lamp(BU_LAMP[0], BU_G + 6.0, BU_LAMP[1] - 1.6, 15.0, BU_SODIUM, 2.0, (1.0, 0.6, 0.2), fall=1.3)]
        porch = [Lamp(BU_PLIGHT[0], BU_PLIGHT[1], BU_PLIGHT[2] - 0.3, 6.5, '#ffc888', 1.6, fall=1.5)]
        hb = BU_HISBUS
        his_in = [Lamp(hb[0], BU_G + 2.2, hb[1] + 1.8, 7.0, BU_AMBER, 1.5, (0.6, 1.0, 0.4), fall=1.4)]
        th = math.radians(hb[2]); N = (math.sin(th), -math.cos(th))
        his_heads = [Lamp(hb[0] + N[0] * 8.0, BU_G + 0.8, hb[1] + N[1] * 8.0, 9.0, BU_HEADS, 1.6, (1.0, 1.0, 0.5), fall=1.3)]
        b9 = BU_BUS9
        cab9 = [Lamp(b9[0], BU_G + 2.0, b9[1] + 3.6, 4.0, '#fff0d0', 1.2, fall=1.5)]
        var = [('street', street, _kfn(o.get('street', 1.0) if tod == 'night' else 0.0, 401)), ('porch', porch, _kfn(o.get('porch', 0.0), 402)),
               ('his_in', his_in, _kfn(o.get('his_win', 1.0) if o.get('his') else 0.0, 403)),
               ('his_heads', his_heads, _kfn(o.get('his_heads', 0.0) if o.get('his') else 0.0, 404)),
               ('cab9', cab9, _kfn(o.get('cab9', 0.0), 405)), _flash_lamp(o, 406)]
        return amb, steady, var

    def shell(self, pen, v, o):
        bu_ext_draw(pen, v, o)

    def pieces(self, o):
        tod = o.get('tod', 'night')
        P = [Piece('house', (-0.5, 2.0, 4.8), lambda pen, v: (bu_house_ext(pen, v, o), _shrubs(pen, v, tod)), block=_r4p(BU_HOUSE)),
             Piece('porch', (-3.95, 0.5, -0.9), lambda pen, v: bu_porch(pen, v, o), block=_r4p((BU_PORCH[0], BU_PORCH[1], BU_STEPS[2], 0.0))),
             Piece('mailbox', (BU_MAILBOX[0], BU_G + 1.0, BU_MAILBOX[1]), lambda pen, v: bu_mailbox(pen, v, o.get('letters', 1.0)), block=_circ(BU_MAILBOX[0], BU_MAILBOX[1], 0.25)),
             Piece('our_lamp', (BU_LAMP[0], BU_G + 3.0, BU_LAMP[1]), lambda pen, v: dr_streetlight(pen, v, BU_LAMP[0], BU_LAMP[1], 1.0, arm=1.0), block=_circ(BU_LAMP[0], BU_LAMP[1], 0.15))]
        if o.get('bus9', True):
            b = BU_BUS9
            P.append(bu_bus_piece('bus9', b[0], b[1], b[2], 'bus9', door=o.get('door9', 0.0), broom=1.0 if o.get('broom') == 'bus9' else 0.0,
                                  mirror_r=o.get('mirror9', True), occupants=[bu_bus_seat_pt(b, 'driver')]))
        if o.get('his'):
            b = (o.get('his_x', BU_HISBUS[0]), BU_HISBUS[1], BU_HISBUS[2])
            P.append(bu_bus_piece('his_bus', b[0], b[1], b[2], 'his', door=o.get('his_door', 0.0), occupants=[bu_bus_seat_pt(b, 'driver')]))
        return P

    def glows(self, v, o):
        G = []
        if o.get('his'):
            b = (o.get('his_x', BU_HISBUS[0]), BU_HISBUS[1], BU_HISBUS[2])
            kw = _kfn(o.get('his_win', 1.0), 403); kh = _kfn(o.get('his_heads', 0.0), 404)
            G.append(('his_bus_glow', (b[0], 1.5, b[1]), lambda pen, t: bu_bus_emit(pen, v, b[0], b[1], b[2], 'his', kw(t), kh(t), 0.0, 0.0, 0.0, t=t)))
        if o.get('bus9', True):
            b = BU_BUS9; kc = _kfn(o.get('cab9', 0.0), 405); kf = _kfn(o.get('flash', 0.0), 406)
            def g9(pen, t, b=b):
                bu_bus_emit(pen, v, b[0], b[1], b[2], 'bus9', 0.0, 0.0, 0.0, 0.0, 0.0)
                k = max(kc(t), kf(t))
                if k > 0.01:
                    P = bu_bus_seat_pt(b, 'driver'); x, y = v.p(P[0], BU_G + 2.1, P[1]); s = v.s(P[0], P[1])
                    if v.d(P[0], P[1]) > 0.3: pen.glow(x, y, 1.2 * s, '#fff0c8', 130 * k); pen.glow(x, y, 0.15 * s, '#ffffff', 220 * kf(t))
            G.append(('bus9_glow', (b[0], 1.5, b[1]), g9))
        return G

    def spots(self, v, o):
        S = {}
        G = BU_G
        S['porch_door'] = _mk_spot(v, 'porch_door', -3.95, -0.5, 0.0, 'stand', 'on the porch at the front door, facing it (+y)', face=(0, 1))
        S['doorframe'] = _mk_spot(v, 'doorframe', BU_FDOOR[1] + 0.08, -0.03, 1.6, 'point', 'the doorframe (east casing) from outside: where the gloves curl')
        S['doorframe_w'] = _mk_spot(v, 'doorframe_w', BU_FDOOR[0] - 0.08, -0.03, 1.6, 'point', 'the doorframe (west casing) from outside')
        S['porch_knock'] = _mk_spot(v, 'porch_knock', -3.8, -0.02, 1.45, 'point', 'where knuckles meet the door')
        S['peephole_out'] = _mk_spot(v, 'peephole_out', (BU_FDOOR[0] + BU_FDOOR[1]) / 2, -0.03, 1.55, 'point', 'the peephole (outside)')
        S['porch_step'] = _mk_spot(v, 'porch_step', -3.95, -2.15, G + 2 * (0.0 - G) / 3, 'stand', 'on the porch steps (the third tape-skip)', face=(0, 1))
        S['walk'] = _mk_spot(v, 'walk', -3.95, -5.0, G, 'stand', 'on the front walk', face=(0, 1))
        S['lawn_mid'] = _mk_spot(v, 'lawn_mid', -2.2, -6.6, G, 'stand', 'the middle of the lawn (the second tape-skip)', face=(0.2, 1))
        S['mailbox'] = _mk_spot(v, 'mailbox', BU_MAILBOX[0] + 0.45, BU_MAILBOX[1] - 0.15, G, 'stand', 'beside our mailbox (the first tape-skip)', face=(0.1, 1))
        S['mailbox_box'] = _mk_spot(v, 'mailbox_box', BU_MAILBOX[0], BU_MAILBOX[1], G + 1.1, 'point', 'the mailbox letters (Grandma unscrews them)')
        S['mailbox_front'] = _mk_spot(v, 'mailbox_front', BU_MAILBOX[0], BU_MAILBOX[1] + 0.55, G, 'stand', 'Grandma at the mailbox (facing it, -y)', face=(0, -1))
        S['window_out'] = _mk_spot(v, 'window_out', -0.6, -0.02, 1.45, 'point', 'the picture window from outside (the curtain gap)')
        S['gran_window_out'] = _mk_spot(v, 'gran_window_out', -5.62, 1.55, BU_UP + 1.45, 'point', "Grandma's window over the driveway, from outside")
        S['yard_west'] = _mk_spot(v, 'yard_west', -6.1, 6.0, G, 'stand', 'the side yard between the house and bus 9 (the flashlight goes out here)', face=(0, -1))
        S['back_corner'] = _mk_spot(v, 'back_corner', -5.9, 9.9, G, 'stand', 'the back corner of the house (Grandma out the back door)', face=(-0.4, -1))
        S['lamp'] = _mk_spot(v, 'lamp', BU_LAMP[0], BU_LAMP[1] - 1.6, G + 6.0, 'point', 'the flickering streetlight head')
        S['street_mid'] = _mk_spot(v, 'street_mid', -2.0, -15.6, G - 0.12, 'stand', 'the middle of Larch Street')
        S.update(bu_bus_spots(v, 'b9_', BU_BUS9[0], BU_BUS9[1], BU_BUS9[2], G, 'bus9'))
        hb = (o.get('his_x', BU_HISBUS[0]), BU_HISBUS[1], BU_HISBUS[2])
        S.update(bu_bus_spots(v, 'his_', hb[0], hb[1], hb[2], G, 'his'))
        return S


def bu_bus_seat_pt(b, which='driver'):
    """Plan point (x, y) of a seat in a bus placed at b = (cx, cy, fa): 'driver'."""
    body, hood, Lb = bu_bus_frame(b[0], b[1], b[2])
    P = body.at(body.w / 2 - 0.55, Lb / 2 - 0.6, 0)
    return (P[0], P[2])


_bcam('bu_ext_house', 820, 470, BU_G + 3.0, -1.6, -24.0, 4, _env(f=(1.0, 2.6)), "the house from across Larch Street: porch, picture window, bus 9 in the driveway, his bus at the kerb", 'street')
_bcam('bu_ext_street', 900, 470, 1.5, -3.6, -1.5, 188, _env(f=(1.0, 2.2)), 'from the porch down the walk: the lawn, our mailbox, his bus at the kerb under the flickering light (the tape-skips)', 'street')
_bcam('bu_ext_curb', 960, 520, BU_G + 1.35, -1.0, -8.6, -150, _env(), 'across the lawn at his bus door (folding open: he unfolds out of it)', 'street')
_bcam('bu_ext_mailbox', 1500, 520, BU_G + 1.25, -2.0, -9.6, -158, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.1)), 'close on our mailbox (the letters on / unscrewed)', 'street')
_bcam('bu_ext_porch', 980, 520, BU_G + 1.62, -1.2, -4.8, -34, _env(), 'the porch at 3/4 from the lawn: the red door, the frosted panes, the porch light', 'street')
_bcam('bu_ext_door', 900, 500, BU_G + 1.6, -3.95, -4.4, 0, _env(), 'up the steps to the front door', 'street')
_bcam('bu_ext_frame', 1300, 520, 1.55, -2.55, -1.25, -52, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.08)), 'close on the door and its frame from the porch (the gloves curling round)', 'street')
_bcam('bu_ext_driveway', 860, 500, 1.55, -3.2, -1.2, -66, _env(), 'from the porch across the side yard to bus 9 (its folding door, Grandma in the cab)', 'street')
_bcam('bu_ext_bus9door', 1250, 520, BU_G + 1.5, -4.9, 0.4, -70, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.08)), "close on bus 9's folding doors (the porch broom wedged through them)", 'street')
_bcam('bu_ext_sideyard', 860, 500, BU_G + 1.55, -5.2, -2.6, 12, _env(), 'along the side yard between the house and bus 9 (Grandma and her flashlight crossing)', 'street')
_bcam('bu_ext_peephole', 560, 540, 1.55, (BU_FDOOR[0] + BU_FDOOR[1]) / 2, -0.06, 180, _env(x=(940, 980), y=(520, 560), zoom=(1.0, 1.02), f=(1.0, 1.2)),
      'through the peephole: the fisheye porch and steps', 'street', pitch=20.0)
_bcam('bu_ext_gap', 1050, 520, 1.42, -0.6, 0.3, 186, _env(x=(920, 1000), y=(500, 560), zoom=(1.0, 1.06)), 'POV through the gap in the curtains: his bus at the kerb, our mailbox', 'street')
_bcam('bu_ext_granout', 760, 380, BU_UP + 1.45, -5.4, 1.55, -96, _env(x=(920, 1000), y=(500, 560), zoom=(1.0, 1.06)),
      "POV from Grandma's window down to the driveway: bus 9's roof and cab (the flashlight blinking)", 'street', pitch=38.0)


def bu_front(view='house', tod='night', his=True, his_door=0.0, his_win=1.0, his_heads=0.0, his_x=None, porch=0.0, street=1.0, letters=1.0,
             win=None, broom='porch', door9=0.0, cab9=0.0, flash=0.0, flash_at=None, mirror9=True, frost_lit=0.0, bus9=True, **kw):
    """Larch Street at night. view: 'house' | 'street' | 'curb' | 'mailbox' | 'porch' | 'door' | 'frame' | 'driveway' |
    'bus9door' | 'sideyard' | 'peephole' | 'gap' (through the curtain gap) | 'granout' (down from Grandma's window).
    his: his bus at the kerb (his_door 0..1 or f(t): the folding door; his_win: amber windows; his_heads: headlights;
    his_x: slide it along the kerb (pulling away)). porch: porch light; street: the flickering streetlight (level spec,
    e.g. ST.bu_flicker(...)); letters: the mailbox letters 0..1; win: {'liv','hall','gran','gran_w','mina','den','sami'}:
    lit windows; broom: 'porch' | 'bus9' (wedged through bus 9's doors) | None; door9: bus 9's door; cab9: bus 9's cab
    light; flash: Grandma's flashlight (in bus 9's cab: the three blinks); frost_lit: the door panes lit from the hall."""
    v = cam('bu_ext_' + view)
    o = dict(tod=tod, his=his, his_door=his_door if not callable(his_door) else 0.0, his_win=his_win, his_heads=his_heads, porch=porch,
             street=street, letters=letters, win=dict(win or {}), broom=broom, door9=door9 if not callable(door9) else 0.0, cab9=cab9, flash=flash,
             flash_at=flash_at or (BU_BUS9[0], BU_G + 2.0, BU_BUS9[1] + 3.6), mirror9=mirror9, frost_lit=frost_lit, bus9=bus9)
    if his_x is not None: o['his_x'] = his_x
    o.update(kw)
    main = BuStreet()
    dyn = list(bu_ext_glow(v, o))
    amb, steady, var = main.lights(o)
    if his and callable(his_door):
        hb = (o.get('his_x', BU_HISBUS[0]), BU_HISBUS[1], BU_HISBUS[2])
        q = bu_bus_door_quad(*hb)
        dyn.append(live_layer('his_door', v, q[1], lambda pen, v_, t: bu_bus_door(pen, v_, hb[0], hb[1], hb[2], 'his', his_door(t)), amb, steady, var,
                              order=v.d(q[1][0], q[1][2]) - 0.05))
    lens, grade, cover = 'lens', 'bu_ext', None
    if view == 'peephole':
        lens, grade, cover = (PEEPHOLE_LENS or _peep_lens()), 'bu_ext', PEEP
    sp = build_view('bu_ext_' + view, v, main, o, outside=None, lens=lens, grade=grade, dyn=dyn, cover=cover,
                    focus=(v.d(-3.95, -1.0) if view == 'peephole' else None), dof=0.6)
    _bu_reorder(sp, v)
    if view == 'gap':
        sp = sp.add(_curtain_gap_layer())
    if view == 'granout':
        sp = sp.add(_window_frame_layer())
    sp.info['note'] = 'Outside: figures order = sp.order_at(x, y). Bus seats: anchors b9_driver / his_driver (the bus body sorts round them).'
    return sp


def _curtain_gap_layer(gap=0.22):
    """Screen-space foreground for the POV through the curtain gap: the two curtain panels out of focus either side."""
    def draw(pen, t):
        w = 1920 * (0.5 - gap / 2)
        for (x0, x1, s) in ((-400, w, 1), (1920 - w, 2320, -1)):
            r = rect(x0, -300, x1 - x0, 1700)
            pen.fill(r, '#3a1e22')
            for k in range(7):
                xx = x0 + (x1 - x0) * (k + 0.5) / 7
                pen.linear(rect(xx - 60, -300, 120, 1700), xx - 60, 0, xx + 60, 0, [(0, '#000000', 0), (0.5, '#000000', 90), (1, '#000000', 0)])
            edge = w if s == 1 else 1920 - w
            pen.linear(rect(edge - 80, -300, 160, 1700), edge - 80 * s, 0, edge + 80 * s, 0, [(0, '#5a2e30', 0), (1, '#ffb070', 70)])
    return Layer(0.2, draw, 'curtain_gap', blur=14)


def _window_frame_layer():
    """Screen-space foreground for a POV out of a window: sash frame and muntins, slightly soft."""
    def draw(pen, t):
        pen.fill(minus(rect(-400, -300, 2720, 1700), rrect(150, 60, 1620, 960, 8)), '#2a2420')
        pen.fill(rect(-400, 520, 2720, 46), '#3a3430')
        pen.fill(rect(936, -300, 48, 1700), '#3a3430')
    return Layer(0.3, draw, 'window_frame', blur=8)


def bu_flicker(t0=0.0, mode='approach', seed=11):
    """Level spec for the streetlight: 'approach' = steady with three hard flickers at t0, t0 + 2.2, t0 + 4.4 (the
    tape-skips: mailbox, lawn, porch steps), 'nervous' = random short dips."""
    if mode == 'approach':
        def f(t):
            for tk in (t0, t0 + 2.2, t0 + 4.4):
                d = t - tk
                if 0.0 <= d < 0.32: return 0.08 + 0.5 * (int(d * 30) % 2) * (d > 0.12)
            return 1.0
        return f
    rng = np.random.default_rng(seed); dips = sorted(rng.uniform(0, 60, 40))
    def g(t):
        for tk in dips:
            if 0 <= t - tk < 0.12: return 0.15
        return 1.0
    return g


# ====================================================================================================== inside the house
def _bu_photo(p_, x, y, w, h, kind='bus', frame='#5a3a20'):
    """A framed photo on a wall (cm frame): 'bus' (Grandma, young, beside bus 9 in 1994), 'kids' (Mina and Sami),
    'grandpa', 'school' (a class photo), 'dino' (Sami's dinosaur poster)."""
    p_.fill(rect(x - w / 2 - 3, y - h / 2 - 3, w + 6, h + 6), frame); p_.line(rect(x - w / 2 - 3, y - h / 2 - 3, w + 6, h + 6), 0.6)
    r = rect(x - w / 2, y - h / 2, w, h)
    if kind == 'bus':
        p_.fill(r, '#c8d8e0'); p_.fill(rect(x - w / 2, y + h * 0.15, w, h * 0.35), '#8a9a6a')
        p_.fill(rrect(x - w * 0.42, y - h * 0.18, w * 0.62, h * 0.38, 2), '#e8b020'); p_.fill(rect(x + w * 0.2, y - h * 0.02, w * 0.18, h * 0.22), '#e8b020')
        for k in range(4): p_.fill(rect(x - w * 0.38 + k * w * 0.13, y - h * 0.12, w * 0.09, h * 0.1), '#2a3a4a')
        btext(p_, '9', x - w * 0.1, y + h * 0.14, 'head', h * 0.12, '#1a1a1a', 220, 'center')
        p_.fill(oval(x + w * 0.32, y - h * 0.08, w * 0.05), '#6a4a3a'); p_.fill(rect(x + w * 0.28, y - h * 0.03, w * 0.08, h * 0.25), '#2a3a6a')
    elif kind == 'kids':
        p_.fill(r, '#e8d8b8')
        for (cx, hh, c) in ((x - w * 0.18, 0.62, '#c84a6a'), (x + w * 0.2, 0.42, '#4aa06a')):
            p_.fill(oval(cx, y + h * 0.5 - hh * h - h * 0.08, w * 0.09), '#8a5a3a')
            p_.fill(rrect(cx - w * 0.12, y + h * 0.5 - hh * h + h * 0.02, w * 0.24, hh * h, 3), c)
    elif kind == 'grandpa':
        p_.fill(r, '#d8c8a8'); p_.fill(oval(x, y - h * 0.08, w * 0.22, h * 0.24), '#8a6a4a'); p_.fill(rrect(x - w * 0.32, y + h * 0.15, w * 0.64, h * 0.4, 4), '#3a3a4a')
    elif kind == 'school':
        p_.fill(r, '#c8d0d8')
        for row in range(2):
            for k in range(6):
                cx = x - w * 0.4 + k * w * 0.16; cy = y - h * 0.1 + row * h * 0.3
                p_.fill(oval(cx, cy, w * 0.04), '#8a6a4a'); p_.fill(rect(cx - w * 0.05, cy + w * 0.04, w * 0.1, h * 0.12), ['#c84a4a', '#4a6ac8', '#e8b020'][(k + row) % 3])
    elif kind == 'dino':
        p_.fill(r, '#fff4d8'); btext(p_, 'DINOSAURS!', x, y - h * 0.36, 'head', h * 0.11, '#d8582a', 240, 'center')
        for i, (dx, dy, k_, c_) in enumerate(((-0.22, -0.05, 0, '#4aa06a'), (0.22, -0.02, 1, '#d8582a'), (-0.2, 0.3, 2, '#4a8ad8'), (0.22, 0.32, 3, '#a85ad8'))):
            _dino_sil(p_, x + dx * w, y + dy * h, h * 0.16, k_, c_)
    p_.texture(r, 'grunge', 0.25, 'overlay', 0.6)
    p_.linear(r, x - w / 2, y - h / 2, x + w / 2, y + h / 2, [(0, '#ffffff', 50), (0.4, '#ffffff', 0), (1, '#ffffff', 0)])


def _bu_rug_art(x0, y1, cx, cy, rx, ry, cols):
    def art(p_, W, H):
        u, w = floor_uv(x0, y1, cx, cy)
        _rug_braided(p_, u, w, rx * 100, ry * 100, cols)
    return art


def _bu_house_light(o, amb_night='#262c48'):
    if o.get('blackout'): return '#0b0d16'
    if o.get('tod') == 'morning': return '#8a8070'
    return amb_night


# ---------------------------------------------------------------------------------------------- the living room
BU_COUCH = Box(-0.6, 4.72, 2.1, 0.9, 0.0, 0.84, 0)                # along the back, facing the window (-y)
BU_COFFEE = Box(-0.6, 3.55, 1.1, 0.55, 0.0, 0.42, 0)
BU_ARM = Box(1.72, 2.95, 0.92, 0.9, 0.0, 1.02, -90)               # Grandma's armchair facing west
BU_TV = Box(1.82, 0.62, 0.86, 0.52, 0.0, 0.74, -138)              # the old console TV in the front-east corner, facing the couch
BU_BENCH = Box(-0.6, 0.24, 2.0, 0.4, 0.0, 0.45, 180)              # the window bench under the picture window
BU_FLAMP = (-1.95, 5.25)
BU_SHELF = Box(2.22, 4.55, 1.0, 0.32, 0.0, 1.9, -90)
BU_CURT_C = '#7a2e34'


def _liv_cfg(o):
    st = o.get('tod', 'night')
    def lights(o):
        gap = _static(o.get('curtains', 0.12), 0.12)
        amb = _bu_house_light(o)
        win = Lamp(kind='win', c='#7a88c8' if st != 'morning' else '#ffe0b0', k=(0.25 + 0.6 * gap) if st != 'morning' else 1.4, soft=10.0,
                   panes=_panes_y(BU_PWIN[0], BU_PWIN[1], BU_PWIN[2], BU_PWIN[3], 0.0), d=_norm3((0.15, -0.45, 1.0)))
        steady = [win] if not o.get('blackout') else []
        gx = -0.6
        heads = [Lamp(kind='win', c=BU_HEADS, k=2.2, soft=6.0, panes=_panes_y(gx - 0.18 - 0.6 * gap, gx + 0.18 + 0.6 * gap, BU_PWIN[2], BU_PWIN[3], 0.0),
                      d=_norm3((0.35, -0.12, 1.0)), only={'floor', 'wall', 'ceil', 'top', 'front', 'side'}),
                 Lamp(-0.6, 1.4, 0.4, 3.2, BU_HEADS, 0.8, fall=1.6)]
        var = [('lamp', [Lamp(BU_FLAMP[0], 1.45, BU_FLAMP[1], 4.8, BU_WARM, 1.5, (1.0, 0.6, 0.35), fall=1.4)], _kfn(o.get('lamp', 0.0), 311)),
               ('ceil', [Lamp(-0.4, 2.42, 2.9, 5.6, '#ffe8c8', 1.2, (1.0, 0.5, 0.2), fall=1.3)], _kfn(o.get('ceil', 0.0), 312)),
               ('tv', [Lamp(BU_TV.cx - 0.3, 0.6, BU_TV.cy + 0.35, 4.2, '#8aa8ff', 1.0, fall=1.5)], _kfn(o.get('tv', 0.0), 313)),
               ('heads', heads, _kfn(o.get('heads', 0.0), 314)),
               ('hall', [Lamp(-3.7, 2.0, 2.0, 3.4, BU_WARM, 0.8, fall=1.4)], _kfn(o.get('hall', 0.0), 315)),
               _phone_lamp(o), _flash_lamp(o)]
        return amb, steady, var

    def east(p_, W, H):
        _bu_photo(p_, (5.8 - 1.2) * 100, H - 165, 46, 34, 'bus')
        _bu_photo(p_, (5.8 - 0.55) * 100, H - 172, 26, 32, 'grandpa')
        _wall_clock(p_, (5.8 - 2.2) * 100, H - 190, 13, 11, 58)
    def back(p_, W, H):
        _bu_photo(p_, (-0.95 + 3.2) * 100, H - 175, 40, 30, 'kids')
        _bu_photo(p_, (-0.15 + 3.2) * 100, H - 178, 30, 38, 'school')
        _light_switch(p_, (0.7 + 3.2) * 100, H - 120)
    def west(p_, W, H):
        _light_switch(p_, (BU_LOPEN[1] + 0.15) * 100, H - 120)
    holes = {'west': [(-3.2, BU_LOPEN[0], -3.2, BU_LOPEN[1], 0.0, BU_LOPEN[2])], 'back': [(BU_KDOOR[0], 5.8, BU_KDOOR[1], 5.8, 0.0, BU_KDOOR[2])]}
    wins = {'front': [(BU_PWIN[0], 0.0, BU_PWIN[1], 0.0, BU_PWIN[2], BU_PWIN[3], (3, 2))]}
    runs = _rect_runs(BU_LIV, holes, wins, {'east': east, 'back': back, 'west': west})
    rug = _bu_rug_art(BU_LIV[0], BU_LIV[3], -0.6, 3.5, 1.5, 1.0, ('#6e3a2c', '#9a7a52', '#3a4a5a', '#b8a888', '#7a4a34', '#5a4a3a', '#8a6a4a'))

    def pieces(o):
        parts = couch_parts(BU_COUCH, '#8a4a32', '#5a2e20', afghan=True)
        seats = couch_seats(BU_COUCH)
        P = [Piece('couch', (BU_COUCH.cx, 0.4, BU_COUCH.cy), lambda pen, v: draw_parts(pen, v, parts), occupant=[(x, y) for (n, x, y) in seats],
                   front=parts, block=BU_COUCH.footprint())]
        ap = dr_armchair_parts(BU_ARM, '#4a6a5a', '#2e4a3e', doily=True)
        aseat = BU_ARM.at(0, -BU_ARM.d / 2 + 0.42, 0)
        P.append(Piece('armchair', (BU_ARM.cx, 0.4, BU_ARM.cy), lambda pen, v: draw_parts(pen, v, ap), occupant=[(aseat[0], aseat[2])], front=ap, block=BU_ARM.footprint()))
        P.append(Piece('coffee', (BU_COFFEE.cx, 0.3, BU_COFFEE.cy), lambda pen, v: (draw_parts(pen, v, table_parts(BU_COFFEE, '#6a4428', apron=0.06)),
                                                                                     _coffee_things(pen, v)), block=BU_COFFEE.footprint()))
        tvk = _static(o.get('tv', 0.0))
        P.append(Piece('tv', (BU_TV.cx, 0.4, BU_TV.cy), lambda pen, v: dr_console_tv(pen, v, BU_TV, 'now', tvk), block=BU_TV.footprint()))
        lk = _static(o.get('lamp', 0.0))
        P.append(Piece('floor_lamp', (BU_FLAMP[0], 1.0, BU_FLAMP[1]), lambda pen, v: lamp_floor(pen, v, BU_FLAMP[0], BU_FLAMP[1], 0.0, 1.55, lk), block=_circ(BU_FLAMP[0], BU_FLAMP[1], 0.18)))
        P.append(Piece('shelf', (BU_SHELF.cx, 1.0, BU_SHELF.cy), lambda pen, v: bookcase(pen, v, BU_SHELF), block=BU_SHELF.footprint()))
        P.append(Piece('bench', (BU_BENCH.cx, 0.3, BU_BENCH.cy), lambda pen, v: draw_box(pen, v, BU_BENCH, {'top': '#e8dcc0', 'front': '#d8ccb0', 'all': '#c8bca0'}),
                       block=BU_BENCH.footprint()))
        bp = o.get('backpack', 'window')
        if bp == 'window':
            P.append(Piece('backpack', (0.15, 0.6, 0.26), lambda pen, v: bu_backpack(pen, v, 0.15, 0.26, 0.45, 0.0, True)))
        elif bp == 'wall':
            P.append(Piece('backpack', (2.18, 0.3, 2.0), lambda pen, v: bu_backpack(pen, v, 2.18, 2.0, 0.0, 90.0, True)))
        cg = o.get('curtains', 0.12); cgs = _static(cg, 0.12)
        if not callable(cg) and not o.get('no_curtains'):
            P.append(Piece('curtains', (-0.6, 1.4, 0.14), lambda pen, v: curtain_pair(pen, v, (2.4, 0.0), (-3.2, 0.0), 2.4 - BU_PWIN[1], 2.4 - BU_PWIN[0],
                                                                                      2.3, 2.25, 0.0, cgs, BU_CURT_C, sheer=True)))
        if o.get('walkie', True):
            sx, sy = seats[2][1], seats[2][2]
            P.append(Piece('walkie', (sx + 0.15, 0.5, sy - 0.05), lambda pen, v: bu_walkie(pen, v, sx + 0.18, COUCH_SEAT + 0.04, sy - 0.08, -25.0)))
        return P

    def glows(v, o):
        G = []
        kl = _kfn(o.get('lamp', 0.0), 311)
        def lampg(pen, t):
            k = kl(t)
            if k > 0.01 and v.d(*BU_FLAMP) > 0.3:
                x, y = v.p(BU_FLAMP[0], 1.42, BU_FLAMP[1]); s = v.s(*BU_FLAMP)
                pen.glow(x, y, 0.8 * s, '#ffd090', 90 * k)
        G.append(('floor_lamp_glow', (BU_FLAMP[0], 1.4, BU_FLAMP[1]), lampg))
        kt = _kfn(o.get('tv', 0.0), 313)
        def tvg(pen, t):
            k = kt(t) * (0.8 + 0.2 * math.sin(t * 13.0) * math.sin(t * 3.1))
            if k <= 0.01: return
            q = dr_tv_screen_quad(BU_TV)
            path = v.poly3(q)
            if path.isEmpty(): return
            pen.fill(path, '#9ab8ff', 170 * k); b = path.computeTightBounds()
            pen.glow((b.left() + b.right()) / 2, (b.top() + b.bottom()) / 2, b.width() * 1.4, '#8aa8ff', 70 * k)
        G.append(('tv_glow', (BU_TV.cx, 0.5, BU_TV.cy), tvg))
        kh = _kfn(o.get('heads', 0.0), 314); gap = _static(o.get('curtains', 0.12), 0.12)
        def curt(pen, t):                                                     # his headlights through the curtains: the fabric glows
            k = kh(t)
            if k <= 0.01: return
            q = [(BU_PWIN[0] - 0.25, 2.3, 0.1), (BU_PWIN[1] + 0.25, 2.3, 0.1), (BU_PWIN[1] + 0.25, 0.05, 0.1), (BU_PWIN[0] - 0.25, 0.05, 0.1)]
            if v.d(-0.6, 0.1) < 0.3: return
            path = v.poly3(q)
            if path.isEmpty(): return
            b = path.computeTightBounds(); cx = (b.left() + b.right()) / 2
            pen.radial(path, cx, b.top() + b.height() * 0.45, b.width() * 0.7, [(0, '#ffd880', 150 * k), (0.6, BU_HEADS, 80 * k), (1, '#a85020', 25 * k)], sy=1.2)
            pen.cv.save(); pen.cv.clipPath(path, skia.ClipOp.kIntersect, True)
            for j in range(16):                                               # the folds catch the light unevenly
                fx = b.left() + b.width() * (j + 0.5) / 16
                pen.linear(rect(fx - b.width() / 32, b.top(), b.width() / 16, b.height()), fx - b.width() / 32, 0, fx + b.width() / 32, 0,
                           [(0, '#000000', 0), (0.5, '#3a1a08', 70 * k), (1, '#000000', 0)])
            pen.cv.restore()
            gx0, gx1 = v.p(-0.6 - 0.2 - 0.6 * gap, 1.4, 0.1)[0], v.p(-0.6 + 0.2 + 0.6 * gap, 1.4, 0.1)[0]
            pen.fill(rect(min(gx0, gx1), b.top(), abs(gx1 - gx0), b.height()), '#fff2c0', 150 * k)
            pen.glow(cx, b.top() + b.height() * 0.4, b.width() * 1.2, BU_HEADS, 60 * k)
        G.append(('curtains_glow', (-0.6, 1.3, 0.12), curt))
        return G

    def spots(v, o):
        S = {}
        for (n, x, y) in couch_seats(BU_COUCH):
            S['couch_' + n] = _mk_spot(v, 'couch_' + n, x, y, 0.0, 'seat', 'the couch, %s seat (facing the window, -y)' % n, face=(0, -1), seat_Y=COUCH_SEAT)
        sx, sy = couch_seats(BU_COUCH)[2][1:]
        S['walkie'] = _mk_spot(v, 'walkie', sx + 0.18, sy - 0.08, COUCH_SEAT + 0.04, 'surface', "Mina's walkie on the cushion beside her (right seat)")
        S['couch_front'] = _mk_spot(v, 'couch_front', -0.6, 4.0, 0.0, 'stand', 'standing in front of the couch', face=(0, 1))
        aseat = BU_ARM.at(0, -BU_ARM.d / 2 + 0.42, 0)
        S['armchair'] = _mk_spot(v, 'armchair', aseat[0], aseat[2], 0.0, 'seat', "Grandma's armchair (facing west)", face=(-1, 0), seat_Y=0.46)
        S['window'] = _mk_spot(v, 'window', -0.6, 0.6, 0.0, 'stand', 'at the picture window, facing the curtain gap (-y)', face=(0, -1))
        S['window_gap'] = _mk_spot(v, 'window_gap', -0.6, 0.12, 1.45, 'point', 'the gap in the curtains (eye height)')
        S['bench'] = _mk_spot(v, 'bench', -1.2, 0.24, 0.45, 'surface', 'the window bench top')
        S['backpack'] = _mk_spot(v, 'backpack', 0.15 if o.get('backpack', 'window') == 'window' else 2.18, 0.26 if o.get('backpack', 'window') == 'window' else 2.0,
                                 0.45 if o.get('backpack', 'window') == 'window' else 0.0, 'surface', "Sami's backpack (rule one: Grandma turns it to the wall)")
        S['backpack_reach'] = _mk_spot(v, 'backpack_reach', 0.15, 0.8, 0.0, 'stand', 'Grandma reaching for the backpack on the bench', face=(0, -1))
        S['room_mid'] = _mk_spot(v, 'room_mid', 0.0, 2.4, 0.0, 'stand', 'the middle of the room')
        S['opening'] = _mk_spot(v, 'opening', -2.85, 2.1, 0.0, 'stand', 'at the opening to the hall (facing it, -x)', face=(-1, 0))
        S['kitchen_door'] = _mk_spot(v, 'kitchen_door', 1.35, 5.4, 0.0, 'stand', 'at the dark kitchen doorway', face=(0, 1))
        S['lamp_switch'] = _mk_spot(v, 'lamp_switch', BU_FLAMP[0], BU_FLAMP[1], 1.2, 'point', 'the floor lamp switch')
        S['tv_screen'] = _mk_spot(v, 'tv_screen', BU_TV.cx - 0.15, BU_TV.cy + 0.15, 0.55, 'point', 'the TV screen')
        return S

    rects = [BU_LIV]
    return dict(name='living', R=BU_LIV, H=BU_CEIL, floor=dict(base='#8a5a34', kind='boards', ink='#4a2e1a', seed=11, art=rug), runs=runs,
                walls=dict(paper=BU_PAL['liv_paper'], ink=BU_PAL['liv_ink'], kind='ditsy', wains=0.0, seed=17, scale=0.9, pa=70, rail=0.9),
                ceil=dict(c='#e8e0d0', rects=rects), lights=lights, pieces=pieces, glows=glows, spots=spots)


def _coffee_things(pen, v):
    Y = BU_COFFEE.Y1
    dr_cup(pen, v, BU_COFFEE.cx - 0.3, Y, BU_COFFEE.cy + 0.05, '#e8e0d0', coffee=True)
    B = Box(BU_COFFEE.cx + 0.2, BU_COFFEE.cy - 0.02, 0.24, 0.17, Y, Y + 0.025, 8)               # Grandma's route book
    draw_box(pen, v, B, {'top': dict(fill='#2a4a7a', art=lambda p_, W, H: btext(p_, 'ROUTE 9', W / 2, H * 0.55, 'sans_b', 3.0, '#e8e0c0', 220, 'center')), 'all': '#1a2a4a'}, lw=0.6)


# ---------------------------------------------------------------------------------------------- the front hall + stairs
def bu_front_door_leaf(rules=True, eighth=False, frost_lit=0.0):
    return Door((BU_FDOOR[0], 0.02), BU_FDOOR[1] - BU_FDOOR[0], BU_FDOOR[2], (1.0, 0.0), 1, 0.0,
                art_a=bu_front_door_art('out', frost_lit=frost_lit), art_b=bu_front_door_art('in', rules, eighth, frost_lit), col=BU_PAL['door'])


def bu_door_panes(D, ang=0.0, side='b'):
    """3D quads of the two frosted panes of the front door leaf D at angle ang, on face b (inside) or a (outside)."""
    B = D.box(ang); F = B.faces()['back' if side == 'b' else 'front']
    W = D.w * 100
    out = []
    for x0 in (14, W / 2 + 6):
        x1 = x0 + W / 2 - 20
        out.append([F.pt(x0, 26), F.pt(x1, 26), F.pt(x1, 84), F.pt(x0, 84)])
    return out


def _frost_layer(v, D, spec, name='frost'):
    """His blurred silhouette through the frosted panes (from inside): a crooked hat and the pale smear of the grin.
    spec: level 0..1 or f(t)."""
    kf = _kfn(spec, 331)
    quads = bu_door_panes(D, 0.0, 'b')
    def draw(pen, t):
        k = kf(t)
        if k <= 0.01: return
        paths = [v.poly3(q) for q in quads]
        paths = [p_ for p_ in paths if not p_.isEmpty()]
        if not paths: return
        clip = paths[0]
        for p_ in paths[1:]: clip = union(clip, p_)
        b = clip.computeTightBounds()
        cx, w, h = (b.left() + b.right()) / 2, b.width(), b.height()
        pen.cv.save(); pen.cv.clipPath(clip, skia.ClipOp.kIntersect, True)
        pen.fill(oval(cx + w * 0.05, b.top() + h * 0.62, w * 0.42, h * 0.42), '#1a140c', 200 * k, blur=max(2.0, w * 0.08))
        hat = poly([(cx - w * 0.35, b.top() + h * 0.32), (cx + w * 0.42, b.top() + h * 0.22), (cx + w * 0.62, b.top() - h * 0.5), (cx - w * 0.05, b.top() - h * 0.5)])
        pen.fill(hat, '#5a4a1a', 210 * k, blur=max(2.0, w * 0.06))
        pen.fill(rrect(cx - w * 0.3, b.top() + h * 0.7, w * 0.62, h * 0.07, h * 0.03), '#f4ecd8', 170 * k, blur=max(1.5, w * 0.03))
        pen.cv.restore()
    lay = Layer(max(0.3, v.d(-3.95, 0.0)), draw, name, blur=None)
    lay.order = v.d(-3.95, 0.02) - 0.03
    return lay


def _stair_knee(pen, v):
    """The closed side of the flight (x -4.6) under the stringer, facing the hall (+x), with the banister above."""
    x0, x1, y0, n, run = BU_ST
    if v.hx <= x1: return
    pts = [(x1, 0.0, y0)] + [(x1, BU_RISE * (i + 1) - 0.06, y0 + i * run) for i in range(n)] + [(x1, 0.0, y0 + (n - 1) * run)]
    pts = [(x1, 0.0, y0), (x1, BU_RISE - 0.06, y0), (x1, BU_UP - 0.06, y0 + (n - 1) * run), (x1, 0.0, y0 + (n - 1) * run)]
    path = v.poly3(pts)
    if not path.isEmpty():
        pen.fill(path, lit('#e8dcc8', (x1, 1.0, 5.0), (1, 0, 0))); pen.line(path, 1.0)
        bb = path.computeTightBounds()
        for k in range(1, 6):                                                   # panel moulding lines
            f = k / 6
            A = (x1 + 0.005, 0.12, y0 + f * (n - 1) * run); B_ = (x1 + 0.005, BU_RISE + f * (BU_UP - BU_RISE) - 0.2, A[2])
            pen.seg(v.p(*A), v.p(*B_), 0.8, '#000000', 50)
    # banister: newel post, balusters, the sloped rail
    pen_w = lambda P, m: max(1.0, m * v.s(P[0], P[2]))
    np_ = (x1 + 0.05, 0.0, y0 - 0.02)
    if v.d(np_[0], np_[2]) > 0.3:
        draw_box(pen, v, Box(np_[0], np_[2] + 0.04, 0.09, 0.09, 0.0, 1.1, 0), {'all': '#5a3a22', 'top': '#6a4428'}, lw=0.8)
    for i in range(0, n - 1, 1):
        for j in (0.25, 0.75):
            yy = y0 + (i + j) * run; Yb = BU_RISE * (i + 1); Yt = Yb + 0.86
            if v.d(x1 + 0.04, yy) > 0.3: pen.seg(v.p(x1 + 0.04, Yb, yy), v.p(x1 + 0.04, Yt, yy), pen_w((x1, 0, yy), 0.018), lit('#f2ebdc', (x1, Yb, yy), (1, 0, 0)))
    A = (x1 + 0.05, 1.05, y0); B_ = (x1 + 0.05, BU_UP + 0.9, y0 + (n - 1) * run)
    if v.d(A[0], A[2]) > 0.3 and v.d(B_[0], B_[2]) > 0.3:
        pen.seg(v.p(*A), v.p(*B_), pen_w(A, 0.05) + 1.5, LINE); pen.seg(v.p(*A), v.p(*B_), pen_w(A, 0.05), lit('#6a4428', A, (0, 1, 0)))


def _hall_cfg(o):
    def lights(o):
        amb = _bu_house_light(o, '#22283e')
        side = Lamp(kind='win', c='#7a8ac8', k=0.45, soft=10.0, panes=_panes_x(BU_HWIN[0], BU_HWIN[1], BU_HWIN[2], BU_HWIN[3], -5.6),
                    d=_norm3((1.0, -0.4, 0.15)), only={'floor', 'wall', 'top', 'front', 'side'})
        steady = [side] if not o.get('blackout') else []
        D = bu_front_door_leaf()
        pq = bu_door_panes(D, 0.0, 'a')
        porch = [Lamp(kind='win', c='#ffc888', k=0.9, soft=8.0, panes=pq, d=_norm3((0.2, -0.25, 1.0)), only={'floor', 'wall', 'ceil', 'side', 'top'})]
        heads = [Lamp(kind='win', c=BU_HEADS, k=1.4, soft=8.0, panes=pq, d=_norm3((-0.2, -0.1, 1.0)), only={'floor', 'wall', 'ceil', 'side', 'top'})]
        hallL = [Lamp(-4.2, 2.42, 1.6, 4.0, '#ffd8a0', 1.3, (1.0, 0.6, 0.3), fall=1.4), Lamp(-4.2, 2.42, 7.6, 4.0, '#ffd8a0', 1.1, (1.0, 0.6, 0.3), fall=1.4)]
        upL = [Lamp(-5.1, 4.9, 6.0, 4.5, '#ffd8a0', 0.9, fall=1.4)]
        livL = [Lamp(-2.6, 1.7, 2.1, 3.2, BU_WARM, 0.7, fall=1.4)]
        var = [('hall', hallL, _kfn(o.get('hall', 0.0), 321)), ('porch', porch, _kfn(o.get('porch', 0.0), 322)), ('heads', heads, _kfn(o.get('heads', 0.0), 323)),
               ('up', upL, _kfn(o.get('up', 0.0), 324)), ('liv', livL, _kfn(o.get('liv', 0.0), 325)), _phone_lamp(o), _flash_lamp(o)]
        return amb, steady, var

    x0, x1, y0, n, run = BU_ST
    top = BU_UP + BU_UH
    def front(p_, W, H):
        _light_switch(p_, (-3.2 - (-3.3)) * 100 + 8, H - 118)
        for k in range(3):                                                      # coat hooks with a raincoat and Sami's little jacket
            hx = (-3.2 - (-5.3 + k * 0.22)) * 100
            p_.fill(oval(hx, H - 175, 1.6), '#8a7a5a')
        p_.fill(smooth([((-3.2 + 5.3) * 100 - 6, H - 172), ((-3.2 + 5.3) * 100 + 8, H - 172), ((-3.2 + 5.3) * 100 + 12, H - 90), ((-3.2 + 5.3) * 100 - 12, H - 92)], True, 0.6), '#3a4a6a')
    def east(p_, W, H):
        _bu_photo(p_, (9.6 - 5.2) * 100, H - 170, 34, 26, 'school')
        _bu_photo(p_, (9.6 - 8.2) * 100, H - 175, 28, 36, 'grandpa')
    def westlow(p_, W, H):
        _bu_photo(p_, 70, H - 170, 30, 24, 'kids')
    runs = [_run((-3.2, 0.0), (-5.6, 0.0), holes=[(BU_FDOOR[0], 0.0, BU_FDOOR[1], 0.0, 0.0, BU_FDOOR[2])], art=front),
            _run((-5.6, 0.0), (-5.6, y0), wins=[(-5.6, BU_HWIN[0], -5.6, BU_HWIN[1], BU_HWIN[2], BU_HWIN[3], (1, 2))], art=westlow),
            _run((-5.6, y0), (-5.6, BU_ST_TOP), Y1=top),
            _run((-5.6, BU_ST_TOP), (-5.6, 9.6)),
            _run((-5.6, 9.6), (-3.2, 9.6), holes=[(BU_BDOOR[0], 9.6, BU_BDOOR[1], 9.6, 0.0, BU_BDOOR[2])]),
            _run((-3.2, 9.6), (-3.2, 0.0), holes=[(-3.2, BU_LOPEN[0], -3.2, BU_LOPEN[1], 0.0, BU_LOPEN[2]), (-3.2, 7.0, -3.2, 7.9, 0.0, 2.05)], art=east),
            _run((x1, y0), (x0, y0), Y0=BU_CEIL, Y1=top, wains=0.0),
            _run((x1, BU_ST_TOP), (x1, y0), Y0=BU_CEIL, Y1=top, wains=0.0)]
    def runner(p_, W, H):
        u0, w0 = floor_uv(-5.6, 9.6, -4.35, 9.2); u1, w1 = floor_uv(-5.6, 9.6, -3.55, 0.35)
        rr = rect(u0, w0, u1 - u0, w1 - w0)
        p_.fill(rr, '#5a2a3a'); p_.texture(rr, 'fabric', 0.6, 'overlay', 1.0)
        p_.line(rect(u0 + 4, w0 + 4, u1 - u0 - 8, w1 - w0 - 8), 2.0, '#d8b860', 160)
        um, wm = floor_uv(-5.6, 9.6, -3.95, 0.3)
        p_.fill(rrect(um - 40, wm - 28, 80, 50, 6), '#3a3026'); btext(p_, 'WELCOME', um, wm + 6, 'sans_b', 11, '#c8b890', 200, 'center')

    def shell_x(pen, v, o):
        ceil_rect(pen, v, x0, x1, y0, BU_ST_TOP, top, c='#e2dccf')
        for yy in (1.6, 7.6):
            if v.cam_h < BU_CEIL and v.d(-4.2, yy) > 0.3:
                e = ellipse3(v, -4.2, yy, 0.16, 0.16, BU_CEIL - 0.04)
                pen.fill(e, lit('#efe8d8', (-4.2, BU_CEIL - 0.1, yy), (0, -1, 0))); pen.line(e, 1.0)

    def pieces(o):
        P = []
        fa = o.get('door', 0.0); fa = 0.0 if callable(fa) else fa
        D = bu_front_door_leaf(o.get('rules', True), o.get('eighth', False), _static(o.get('frost_lit', 0.0)))
        P.append(Piece('front_door', (-3.95, 1.0, 0.03 + 0.45 * math.sin(math.radians(fa))), lambda pen, v, D=D, a=fa: D.draw(pen, v, a)))
        P.append(Piece('stairs', (x0 + 0.5, 1.0, (y0 + BU_ST_TOP) / 2), lambda pen, v: (bu_stairs(pen, v, x0, x1, y0, n, run, BU_RISE, 0.0), _stair_knee(pen, v)),
                       block=_r4p((x0, x1 + 0.08, y0 - 0.06, BU_ST_TOP))))
        ba = o.get('back_door', 0.0); ba = 0.0 if callable(ba) else ba
        DB = Door((BU_BDOOR[0], 9.58), BU_BDOOR[1] - BU_BDOOR[0], BU_BDOOR[2], (1.0, 0.0), -1, 0.0, art_a=door_art('glass', 'right', bolt=True),
                  art_b=door_art('glass', 'left', bolt=True), col='#e8e0d0')
        P.append(Piece('back_door', ((BU_BDOOR[0] + BU_BDOOR[1]) / 2, 1.0, 9.55 - 0.4 * math.sin(math.radians(ba))), lambda pen, v, D=DB, a=ba: D.draw(pen, v, a)))
        P.append(Piece('hall_table', (-5.42, 0.5, 0.75), lambda pen, v: _hall_table(pen, v), block=_box_pts(-5.42, 0.75, 0.17, 0.4)))
        tk = o.get('ticket', 0.0)
        if tk:
            P.append(Piece('ticket', (-3.9, 0.02, 0.2), lambda pen, v: _floor_ticket(pen, v, -3.9, 0.06 + 0.18 * _static(tk, 1.0))))
        return P

    def glows(v, o):
        G = []
        kh = _kfn(o.get('hall', 0.0), 321)
        def g(pen, t):
            k = kh(t)
            if k <= 0.01 or v.cam_h > BU_CEIL: return
            for yy in (1.6, 7.6):
                if v.d(-4.2, yy) < 0.3: continue
                pen.fill(ellipse3(v, -4.2, yy, 0.14, 0.14, BU_CEIL - 0.045), '#fff6e4', 230 * k)
                gx, gy = v.p(-4.2, BU_CEIL - 0.08, yy); pen.glow(gx, gy, 0.7 * v.s(-4.2, yy), '#ffe8c0', 70 * k)
        G.append(('hall_glow', (-4.2, BU_CEIL, 4.5), g))
        kp = _kfn(o.get('porch', 0.0), 322); khd = _kfn(o.get('heads', 0.0), 323)
        D = bu_front_door_leaf()
        def panes(pen, t):
            k1, k2 = kp(t), khd(t)
            if (k1 <= 0.01 and k2 <= 0.01) or self_far(o): return
            fa = o.get('door', 0.0)
            if callable(fa) or fa > 2: return
            for q in bu_door_panes(D, 0.0, 'b'):
                if v.d(q[0][0], q[0][2]) < 0.25: continue
                path = v.poly3(q)
                if path.isEmpty(): continue
                b = path.computeTightBounds()
                if k1 > 0.01: pen.fill(path, '#ffdca0', 170 * k1)
                if k2 > 0.01: pen.fill(path, '#ffd060', 200 * k2)
                pen.glow((b.left() + b.right()) / 2, (b.top() + b.bottom()) / 2, b.width() * 2.0, '#ffc070', 50 * max(k1, k2))
        G.append(('panes_glow', (-3.95, 1.5, 0.05), panes))
        return G

    def spots(v, o):
        S = {}
        S['door_inside'] = _mk_spot(v, 'door_inside', -3.95, 0.55, 0.0, 'stand', 'inside the front door, facing it (-y)', face=(0, -1))
        S['peephole_eye'] = _mk_spot(v, 'peephole_eye', -3.95, 0.3, 0.0, 'stand', 'eye to the peephole (Mina on tiptoe: 1.55 m)', face=(0, -1))
        S['peephole'] = _mk_spot(v, 'peephole', -3.95, 0.07, 1.55, 'point', 'the peephole (inside face)')
        S['knob'] = _mk_spot(v, 'knob', BU_FDOOR[1] - 0.08, 0.07, 0.97, 'point', 'the front door knob (inside, east side)')
        S['deadbolt'] = _mk_spot(v, 'deadbolt', BU_FDOOR[1] - 0.08, 0.07, 1.14, 'point', 'the front door deadbolt thumb-turn')
        S['rules'] = _mk_spot(v, 'rules', -3.95, 0.07, 0.98, 'point', 'the rules taped inside the door (centre)')
        S['panes'] = _mk_spot(v, 'panes', -3.95, 0.07, 1.5, 'point', 'the frosted panes (his silhouette)')
        S['under_door'] = _mk_spot(v, 'under_door', -3.9, 0.16, 0.0, 'surface', 'the floor just inside the door: the ticket slides under here')
        S['hall_mid'] = _mk_spot(v, 'hall_mid', -4.0, 2.3, 0.0, 'stand', 'the hall between the door and the stairs')
        S['stairs_foot'] = _mk_spot(v, 'stairs_foot', -5.1, 2.85, 0.0, 'stand', 'at the foot of the stairs, facing up (+y)', face=(0, 1))
        for k in (2, 6, 10, 13):
            S['stair%d' % k] = _mk_spot(v, 'stair%d' % k, -5.1, y0 + (k + 0.5) * run, (k + 1) * BU_RISE, 'stand', 'on tread %d of the stairs (facing up +y)' % (k + 1), face=(0, 1))
        S['side_window'] = _mk_spot(v, 'side_window', -5.25, 1.65, 0.0, 'stand', 'at the hall side window (bus 9 across the yard), facing -x', face=(-1, 0))
        S['back_door'] = _mk_spot(v, 'back_door', -4.2, 9.1, 0.0, 'stand', 'at the back door (Grandma slips out), facing +y', face=(0, 1))
        S['opening'] = _mk_spot(v, 'opening', -3.45, 2.1, 0.0, 'stand', 'in the opening to the living room')
        return S

    rects = [(-4.6, -3.2, 0.0, 9.6), (-5.6, -4.6, 0.0, y0), (-5.6, -4.6, BU_ST_TOP, 9.6)]
    return dict(name='hall', R=BU_HALL, H=BU_CEIL, floor=dict(base='#7a4e2e', kind='boards', ink='#3a2412', seed=31, art=runner), runs=runs,
                walls=dict(paper=BU_PAL['hall_paper'], ink=BU_PAL['hall_ink'], kind='stripe', wains=0.9, wcol=BU_PAL['wains'], seed=23, scale=0.9, pa=60),
                ceil=dict(c='#e6dfd2', rects=rects), lights=lights, pieces=pieces, glows=glows, spots=spots, shell_x=shell_x)


def self_far(o): return o.get('_far', False)


def _hall_table(pen, v):
    B = Box(-5.42, 0.75, 0.8, 0.34, 0.0, 0.78, 90)
    draw_parts(pen, v, table_parts(B, '#5a3a22', apron=0.08))
    Y = 0.78
    pen.fill(ellipse3(v, -5.42, 0.55, 0.1, 0.07, Y + 0.005), lit('#6a8aa8', (-5.42, Y, 0.55), (0, 1, 0)))         # the keys bowl
    if v.d(-5.45, 0.98) > 0.3:
        dr_table_lamp(pen, v, -5.45, 0.98, Y, 0.0, '#efe2c4', '#7a8a6a', 0.42)


def _floor_ticket(pen, v, x, y):
    q = v.poly3([(x - 0.045, 0.004, y - 0.022), (x + 0.045, 0.004, y - 0.022), (x + 0.045, 0.004, y + 0.022), (x - 0.045, 0.004, y + 0.022)])
    if q.isEmpty(): return
    pen.fill(q, lit('#f0c830', (x, 0.0, y), (0, 1, 0))); pen.line(q, 0.8)
    cx, cy = v.p(x, 0.005, y); pen.fill(oval(cx, cy, max(1.0, 0.007 * v.s(x, y)), max(0.6, 0.003 * v.s(x, y))), '#1a1408')


# ---------------------------------------------------------------------------------------------- upstairs: the hall, Grandma's room, Sami's room
def bu_gran_door(bolt=1.0):
    return Door((BU_GDOOR[1], 3.2), BU_GDOOR[1] - BU_GDOOR[0], BU_GDOOR[2], (-1.0, 0.0), 1, BU_UP,
                art_a=door_art('six', 'right', bolt=False), art_b=door_art('six', 'left', bolt=True, turn=bolt, chain=False), col='#efe9dc')


def bu_sami_door():
    return Door((-3.4, BU_SDOOR[0]), BU_SDOOR[1] - BU_SDOOR[0], BU_SDOOR[2], (0.0, 1.0), -1, BU_UP,
                art_a=_kid_door_art(), art_b=door_art('six', 'right', bolt=False), col='#efe9dc')


def _kid_door_art():
    base = door_art('six', 'left', bolt=False)
    def art(p_, W, H):
        base(p_, W, H)
        p_.fill(rrect(W / 2 - 22, 40, 44, 14, 3), '#4aa06a'); btext(p_, 'SAMI', W / 2, 51, 'kid', 11, '#fff6dc', 250, 'center')
        _dino_sil(p_, W / 2 + 14, 75, 8, 1, '#d8582a')
    return art


def _up_cfg(o):
    U, T = BU_UP, BU_UP + BU_UH
    x0, x1, y0, n, run = BU_ST
    def lights(o):
        amb = _bu_house_light(o, '#1e2238')
        nl = Lamp(-3.45, U + 0.25, 7.6, 2.2, '#ffd8a0', 0.7, fall=1.6)                        # the plug-in nightlight
        steady = [] if o.get('blackout') else [nl]
        upL = [Lamp(-4.0, T - 0.08, 4.6, 4.2, '#ffd8a0', 1.3, (1.0, 0.6, 0.3), fall=1.35), Lamp(-4.5, T - 0.08, 7.5, 3.6, '#ffd8a0', 1.1, (1.0, 0.6, 0.3), fall=1.4)]
        gran = [Lamp(-4.0, U + 1.6, 2.6, 3.0, BU_WARM, 0.9, fall=1.4)]
        sami = [Lamp(-2.9, U + 1.0, 6.0, 2.8, '#d8f0b0', 0.7, fall=1.4)]
        var = [('up', upL, _kfn(o.get('up', 0.0), 341)), ('gran', gran, _kfn(o.get('gran', 0.0), 342)), ('sami', sami, _kfn(o.get('sami', 0.0), 343)),
               _phone_lamp(o), _flash_lamp(o)]
        return amb, steady, var

    def east(p_, W, H):
        _bu_photo(p_, (8.2 - 7.3) * 100, H - 170, 28, 22, 'kids')
        _bu_photo(p_, (8.2 - 5.0) * 100, H - 175, 30, 38, 'school')
        p_.fill(rrect((8.2 - 7.6) * 100 - 5, H - 28, 10, 14, 2), '#f2ece0')                         # the nightlight
    def westc(p_, W, H):
        _bu_photo(p_, (5.0 - 3.2) * 100, H - 172, 34, 26, 'bus')
    runs = [_run((-3.4, 3.2), (-4.6, 3.2), holes=[(BU_GDOOR[0], 3.2, BU_GDOOR[1], 3.2, 0.0, BU_GDOOR[2])]),
            _run((-4.6, 3.2), (-4.6, BU_ST_TOP), art=westc),
            _run((-5.6, BU_ST_TOP), (-5.6, 8.2)),
            _run((-5.6, 8.2), (-3.4, 8.2), holes=[(-4.5, 8.2, -3.7, 8.2, 0.0, 2.03)]),
            _run((-3.4, 8.2), (-3.4, 3.2), holes=[(-3.4, BU_SDOOR[0], -3.4, BU_SDOOR[1], 0.0, BU_SDOOR[2]), (-3.4, BU_MDOOR[0], -3.4, BU_MDOOR[1], 0.0, 2.03)], art=east),
            _run((-5.6, y0), (-5.6, BU_ST_TOP), Y0=0.0, Y1=T),
            _run((x1, y0), (x0, y0), Y0=BU_CEIL, Y1=T, wains=0.0),
            _run((x1, BU_ST_TOP), (x1, y0), Y0=BU_CEIL, Y1=T, wains=0.0)]
    def runner(p_, W, H):
        u0, w0 = floor_uv(-5.6, 8.2, -4.35, 8.0); u1, w1 = floor_uv(-5.6, 8.2, -3.65, 3.35)
        rr = rect(u0, w0, u1 - u0, w1 - w0); p_.fill(rr, '#4a5a7a'); p_.texture(rr, 'fabric', 0.6, 'overlay', 1.0)
        p_.line(rect(u0 + 4, w0 + 4, u1 - u0 - 8, w1 - w0 - 8), 1.6, '#c8b890', 150)

    def shell_x(pen, v, o):
        for (xx, yy) in ((-4.0, 4.6), (-4.5, 7.5)):
            if v.cam_h < T and v.d(xx, yy) > 0.3:
                e = ellipse3(v, xx, yy, 0.15, 0.15, T - 0.04)
                pen.fill(e, lit('#efe8d8', (xx, T - 0.1, yy), (0, -1, 0))); pen.line(e, 1.0)

    def pieces(o):
        P = []
        ga = o.get('gran_door', 0.0); ga = 0.0 if callable(ga) else ga
        GD = bu_gran_door(_static(o.get('bolt', 1.0), 1.0))
        P.append(Piece('gran_door', (-4.0, U + 1.0, 3.18 - 0.45 * math.sin(math.radians(ga))), lambda pen, v, D=GD, a=ga: D.draw(pen, v, a)))
        sa = o.get('sami_door', 0.0); sa = 0.0 if callable(sa) else sa
        SD = bu_sami_door()
        P.append(Piece('sami_door', (-3.38 + 0.4 * math.sin(math.radians(sa)), U + 1.0, 6.0), lambda pen, v, D=SD, a=sa: D.draw(pen, v, a)))
        MD = Door((-3.4, BU_MDOOR[0]), BU_MDOOR[1] - BU_MDOOR[0], 2.03, (0.0, 1.0), -1, U, art_a=door_art('six', 'left', bolt=False), art_b=door_art('six', 'right', bolt=False), col='#efe9dc')
        P.append(Piece('mina_door', (-3.38, U + 1.0, 4.0), lambda pen, v, D=MD: D.draw(pen, v, 0.0)))
        BD = Door((-4.5, 8.2), 0.8, 2.03, (1.0, 0.0), -1, U, art_a=door_art('six', 'left', bolt=False), art_b=door_art('six', 'right', bolt=False), col='#efe9dc')
        P.append(Piece('bath_door', (-4.1, U + 1.0, 8.18), lambda pen, v, D=BD: D.draw(pen, v, 0.0)))
        P.append(Piece('stairs_down', (x0 + 0.5, 1.5, (y0 + BU_ST_TOP) / 2), lambda pen, v: bu_stairs(pen, v, x0, x1, y0, n, run, BU_RISE, 0.0),
                       vis=lambda v: v.hx < x1 + 0.02 or v.hy > BU_ST_TOP - 0.2))
        return P

    def glows(v, o):
        ku = _kfn(o.get('up', 0.0), 341)
        def g(pen, t):
            k = ku(t)
            if k <= 0.01 or v.cam_h > T: return
            for (xx, yy) in ((-4.0, 4.6), (-4.5, 7.5)):
                if v.d(xx, yy) < 0.3: continue
                pen.fill(ellipse3(v, xx, yy, 0.13, 0.13, T - 0.045), '#fff6e4', 230 * k)
                gx, gy = v.p(xx, T - 0.08, yy); pen.glow(gx, gy, 0.6 * v.s(xx, yy), '#ffe8c0', 70 * k)
        def nl(pen, t):
            if o.get('blackout') or v.d(-3.42, 7.6) < 0.3: return
            gx, gy = v.p(-3.42, U + 0.25, 7.6); pen.glow(gx, gy, 0.25 * v.s(-3.42, 7.6), '#ffd8a0', 120)
        return [('up_glow', (-4.0, T, 6.0), g), ('nightlight', (-3.42, U + 0.25, 7.6), nl)]

    def spots(v, o):
        S = {}
        S['hall_front'] = _mk_spot(v, 'hall_front', -4.0, 3.6, U, 'stand', "just outside Grandma's door (facing it, -y)", face=(0, -1))
        S['hall_mid'] = _mk_spot(v, 'hall_mid', -4.0, 5.2, U, 'stand', 'the middle of the upstairs hall (he fills it bent double: ceiling %.2f)' % T)
        S['hall_back'] = _mk_spot(v, 'hall_back', -4.0, 7.4, U, 'stand', 'the back of the hall by the landing')
        S['landing'] = _mk_spot(v, 'landing', -5.1, 7.5, U, 'stand', 'the landing at the head of the stairs (facing down, -y)', face=(0, -1))
        S['sami_door'] = _mk_spot(v, 'sami_door', -3.75, 6.0, U, 'stand', "at Sami's door (facing it, +x)", face=(1, 0))
        S['wall_l'] = _mk_spot(v, 'wall_l', -4.6, 5.0, U + 1.7, 'point', 'the hall wall, west side (his glove flat on it)')
        S['wall_r'] = _mk_spot(v, 'wall_r', -3.4, 5.0, U + 1.7, 'point', 'the hall wall, east side (his other glove)')
        S['ceiling'] = _mk_spot(v, 'ceiling', -4.0, 5.0, T, 'point', 'the hall ceiling (his hat crushed against it)')
        return S

    poly_ = [(-4.6, 3.2), (-3.4, 3.2), (-3.4, 8.2), (-5.6, 8.2), (-5.6, BU_ST_TOP), (-4.6, BU_ST_TOP)]
    floors = [(-4.6, -3.4, 3.2, 8.2), (-5.6, -4.6, BU_ST_TOP, 8.2)]
    return dict(name='uphall', R=(-5.6, -3.4, 3.2, 8.2), poly=poly_, Y0=U, H=BU_UH, floors=floors, floor=dict(base='#7a4e2e', kind='boards', ink='#3a2412', seed=33, art=runner),
                runs=runs, walls=dict(paper=BU_PAL['up_paper'], ink='#8a7a5a', kind='stripe', wains=0.9, wcol=BU_PAL['wains'], seed=27, scale=0.9, pa=50),
                ceil=dict(c='#e6dfd2', rects=floors + [(x0, x1, y0, BU_ST_TOP)]), lights=lights, pieces=pieces, glows=glows, spots=spots, shell_x=shell_x)


BU_GBED = Box(-2.6, 1.45, 1.4, 2.0, BU_UP, BU_UP + 0.5, -90)


def _gran_cfg(o):
    U = BU_UP
    def lights(o):
        amb = _bu_house_light(o, '#1e2238')
        win = Lamp(kind='win', c='#c8a070', k=0.55, soft=10.0, panes=_panes_x(BU_GWIN[0], BU_GWIN[1], U + BU_GWIN[2], U + BU_GWIN[3], -5.6),
                   d=_norm3((1.0, -0.35, 0.2)))
        win2 = Lamp(kind='win', c='#7a88c8', k=0.35, soft=10.0, panes=_panes_y(BU_GFWIN[0], BU_GFWIN[1], U + BU_GFWIN[2], U + BU_GFWIN[3], 0.0), d=_norm3((0.1, -0.4, 1.0)))
        steady = [] if o.get('blackout') else [win, win2]
        var = [('lamp', [Lamp(-1.85, U + 0.95, 2.5, 3.6, BU_WARM, 1.4, (1.0, 0.6, 0.3), fall=1.4)], _kfn(o.get('lamp', 0.0), 351)),
               ('ceil', [Lamp(-3.6, U + BU_UH - 0.08, 1.6, 4.5, '#ffe8c8', 1.1, (1.0, 0.5, 0.2), fall=1.3)], _kfn(o.get('ceil', 0.0), 352)),
               ('hall', [Lamp(-4.0, U + 1.6, 3.6, 2.6, '#ffd8a0', 0.8, fall=1.5)], _kfn(o.get('hall', 0.0), 353)),
               _phone_lamp(o), _flash_lamp(o)]
        return amb, steady, var
    def east(p_, W, H):
        _bu_photo(p_, (3.2 - 1.45) * 100, H - 185, 44, 32, 'bus')
    def front(p_, W, H):
        _bu_photo(p_, (-1.6 - (-4.55)) * 100, H - 150, 22, 28, 'grandpa')
        p_.fill(rect((-1.6 - (-2.1)) * 100 - 14, H - 190, 28, 36), '#f4efe0'); p_.line(rect((-1.6 - (-2.1)) * 100 - 14, H - 190, 28, 36), 0.5)   # a calendar
        btext(p_, 'AUGUST', (-1.6 - (-2.1)) * 100, H - 182, 'sans_b', 3.5, '#a03a2a', 230, 'center')
        for i in range(5):
            for j in range(7): p_.fill(rect((-1.6 - (-2.1)) * 100 - 12 + j * 3.5, H - 176 + i * 4.5, 2.6, 3.2), '#d8d0c0')
    holes = {'back': [(BU_GDOOR[0], 3.2, BU_GDOOR[1], 3.2, 0.0, BU_GDOOR[2])]}
    wins = {'west': [(-5.6, BU_GWIN[0], -5.6, BU_GWIN[1], BU_GWIN[2], BU_GWIN[3], (2, 2))],
            'front': [(BU_GFWIN[0], 0.0, BU_GFWIN[1], 0.0, BU_GFWIN[2], BU_GFWIN[3], (2, 2))]}
    runs = _rect_runs(BU_GRAN, holes, wins, {'east': east, 'front': front})
    rug = _bu_rug_art(BU_GRAN[0], BU_GRAN[3], -4.2, 1.6, 0.8, 0.55, ('#7a4a5a', '#c8a888', '#5a6a7a', '#e8d8c0', '#8a5a4a'))

    def pieces(o):
        bp = bu_bed_parts(BU_GBED, U, o.get('bed', 'made'), '#6a4428', ('#8a4a5a', '#e8d8b0', '#5a6a8a', '#c8a888', '#7a8a5a'), '#8a4a5a')
        P = [Piece('bed', (BU_GBED.cx, U + 0.4, BU_GBED.cy), lambda pen, v: draw_parts(pen, v, bp), block=BU_GBED.footprint())]
        NS = Box(-1.86, 2.55, 0.42, 0.4, U, U + 0.6, -90)
        lk = _static(o.get('lamp', 0.0))
        P.append(Piece('nightstand', (NS.cx, U + 0.4, NS.cy), lambda pen, v: (draw_box(pen, v, NS, {'all': '#6a4428', 'front': dict(fill='#6a4428', art=lambda p_, W, H: (
            p_.line(rect(4, 8, W - 8, H * 0.35), 0.8, '#000000', 110), p_.fill(oval(W / 2, 8 + H * 0.17, 1.6), '#c8a858')))}),
            dr_table_lamp(pen, v, -1.86, 2.6, U + 0.6, lk, '#f2e2c8', '#8a6a8a', 0.42)), block=NS.footprint()))
        DS = Box(-4.6, 0.28, 1.1, 0.5, U, U + 0.85, 180)
        P.append(Piece('dresser', (DS.cx, U + 0.4, DS.cy), lambda pen, v: (draw_box(pen, v, DS, {'all': '#6a4428', 'top': '#7a5434', 'front': dict(fill='#6a4428', art=lambda p_, W, H: [
            (p_.line(rect(4, 6 + k * (H - 10) / 3, W - 8, (H - 10) / 3 - 4), 0.9, '#000000', 110), p_.fill(oval(W * 0.3, 6 + k * (H - 10) / 3 + (H - 10) / 6, 1.6), '#c8a858'),
             p_.fill(oval(W * 0.7, 6 + k * (H - 10) / 3 + (H - 10) / 6, 1.6), '#c8a858')) for k in range(3)])}),
            _dresser_things(pen, v, DS)), block=DS.footprint()))
        P.append(Piece('rocker', (-5.0, U + 0.5, 2.62), lambda pen, v: rocking_chair(pen, v, -5.0, 2.62, U, 150), block=_circ(-5.0, 2.62, 0.32)))
        da = o.get('door', 0.0); da = 0.0 if callable(da) else da
        GD = bu_gran_door(_static(o.get('bolt', 1.0), 1.0))
        P.append(Piece('door', (-4.0, U + 1.0, 3.18 - 0.45 * math.sin(math.radians(da))), lambda pen, v, D=GD, a=da: D.draw(pen, v, a)))
        return P

    def glows(v, o):
        kl = _kfn(o.get('lamp', 0.0), 351)
        def g(pen, t):
            k = kl(t)
            if k > 0.01 and v.d(-1.86, 2.6) > 0.3:
                x, y = v.p(-1.86, U + 0.95, 2.6); pen.glow(x, y, 0.7 * v.s(-1.86, 2.6), '#ffd090', 100 * k)
        return [('lamp_glow', (-1.86, U + 0.9, 2.6), g)]

    def spots(v, o):
        S = {}
        S['door_sit'] = _mk_spot(v, 'door_sit', -4.0, 2.88, U, 'floor_sit', 'sitting on the floor, her back against the door (facing -y)', face=(0, -1))
        S['door_in'] = _mk_spot(v, 'door_in', -4.0, 2.55, U, 'stand', 'inside, facing the door (+y)', face=(0, 1))
        S['deadbolt'] = _mk_spot(v, 'deadbolt', BU_GDOOR[0] + 0.08, 3.17, U + 1.14, 'point', 'the deadbolt thumb-turn (inside)')
        S['knob'] = _mk_spot(v, 'knob', BU_GDOOR[0] + 0.08, 3.17, U + 0.97, 'point', 'the door knob (inside)')
        S['window'] = _mk_spot(v, 'window', -5.2, 1.55, U, 'stand', 'at the window over the driveway, facing out (-x)', face=(-1, 0))
        S['window_glass'] = _mk_spot(v, 'window_glass', -5.57, 1.55, U + 1.45, 'point', 'the window glass (eye height)')
        S['bed_edge'] = _mk_spot(v, 'bed_edge', -3.42, 1.45, U, 'seat', 'sitting on the side of the bed (facing -x)', face=(-1, 0), seat_Y=0.52)
        S['bed'] = _mk_spot(v, 'bed', -2.6, 1.45, U + 0.52, 'lie', 'lying on the bed (head east)')
        S['room_mid'] = _mk_spot(v, 'room_mid', -3.8, 1.6, U, 'stand', 'the middle of the room')
        S['rocker'] = _mk_spot(v, 'rocker', -5.0, 2.62, U, 'seat', 'the rocking chair by the window', face=(0.5, -0.87), seat_Y=0.45)
        return S

    return dict(name='gran', R=BU_GRAN, Y0=U, H=BU_UH, floor=dict(base='#7a5434', kind='boards', ink='#3a2412', seed=37, art=rug), runs=runs,
                walls=dict(paper=BU_PAL['gran_paper'], ink=BU_PAL['gran_ink'], kind='roses', wains=0.0, seed=41, scale=0.9, pa=60),
                ceil=dict(c='#ece4d8'), lights=lights, pieces=pieces, glows=glows, spots=spots)


def bu_bed_parts(B, Y0, state='made', frame='#6a4428', quilt=('#5a7ab0', '#e8d8b0', '#8a5a7a', '#c8b898'), quilt_c='#6a7aa8', dino=False):
    """A bed (frame colour, a patchwork / dinosaur quilt, pillow; state 'made' | 'turned' | 'empty'). Head at B's back (-n)."""
    w2, d2 = B.w / 2, B.d / 2
    P = []
    for (u, n) in ((-w2 + 0.03, -d2 + 0.03), (w2 - 0.03, -d2 + 0.03), (-w2 + 0.03, d2 - 0.03), (w2 - 0.03, d2 - 0.03)):
        P.append(Part(sub(B, u - 0.03, u + 0.03, n - 0.03, n + 0.03, Y0, Y0 + 0.3), {'all': frame}))
    P.append(Part(sub(B, -w2, w2, -d2, d2, Y0 + 0.18, Y0 + 0.32), {'all': frame}))
    P.append(Part(sub(B, -w2 + 0.02, w2 - 0.02, -d2 + 0.02, d2 - 0.02, Y0 + 0.32, Y0 + 0.5), {'all': '#f2eee6', 'top': '#f8f6f0'}))
    P.append(Part(fn=lambda pen, v: box_extrude(pen, v, B, -w2, w2, -d2 - 0.05, -d2 + 0.005, Y0, Y0 + 1.0, lambda W, H: rounded_rect_pts(W, H, 10.0, 0.0), frame, _darken(frame, 0.2)),
                  ref=B.at(0, -d2 - 0.02, 0.5), tag='head'))
    P.append(Part(fn=lambda pen, v: box_extrude(pen, v, B, -w2, w2, d2 - 0.005, d2 + 0.04, Y0, Y0 + 0.6, lambda W, H: rounded_rect_pts(W, H, 6.0, 0.0), frame, _darken(frame, 0.2)),
                  ref=B.at(0, d2 + 0.02, 0.4), tag='foot'))
    P.append(Part(fn=lambda pen, v: box_extrude(pen, v, B, -w2 + 0.1, w2 - 0.1, -d2 + 0.05, -d2 + 0.38, Y0 + 0.5, Y0 + 0.62,
                                                 lambda W, H: rounded_rect_pts(W, H, 5.0, 3.0, bulge=1.5), '#fbfaf6', '#d8d4cc'), ref=B.at(0, -d2 + 0.2, 0.55), tag='pillow'))
    def qart(p_, W, H):
        if dino:
            p_.fill(rect(0, 0, W, H), quilt_c)
            for i in range(int(W / 22) + 1):
                for j in range(int(H / 22) + 1):
                    _dino_sil(p_, 10 + i * 22 + (j % 2) * 11, 12 + j * 22, 6, (i + j) % 4, ('#e8d870', '#f4f0e0', '#e88a3a', '#8ad0a0')[(i * 3 + j) % 4])
        else:
            s_ = 16.0
            for i in range(int(W / s_) + 1):
                for j in range(int(H / s_) + 1):
                    p_.fill(rect(i * s_, j * s_, s_, s_), quilt[(i * 2 + j * 3) % len(quilt)])
                    p_.line(rect(i * s_ + 1, j * s_ + 1, s_ - 2, s_ - 2), 0.5, '#3a2a2a', 90)
        p_.texture(rect(0, 0, W, H), 'fabric', 0.5, 'overlay', 0.5)
    if state != 'empty':
        n0 = -d2 + 0.42 if state != 'turned' else -d2 + 0.66
        P.append(Part(fn=lambda pen, v: box_extrude(pen, v, B, -w2 - 0.03, w2 + 0.03, n0, d2, Y0 + 0.28, Y0 + 0.56,
                                                     lambda W, H: rounded_rect_pts(W, H, 3.0, 0.0, bulge=2.0), quilt_c, _darken(quilt_c, 0.2), qart), ref=B.at(0, 0.2, 0.5), tag='quilt'))
    else:
        P.append(Part(fn=lambda pen, v: box_extrude(pen, v, B, -w2 - 0.03, w2 + 0.03, d2 - 0.45, d2 + 0.02, Y0 + 0.28, Y0 + 0.62,
                                                     lambda W, H: rounded_rect_pts(W, H, 6.0, 0.0, bulge=4.0), quilt_c, _darken(quilt_c, 0.2), qart), ref=B.at(0, d2 - 0.2, 0.5), tag='quilt'))
    return P


def _dresser_things(pen, v, DS):
    Y = DS.Y1
    P = DS.at(-0.3, 0.0, Y)
    F = Face((P[0] - 0.09, Y + 0.24, P[2]), (1, 0, 0), (0, -1, 0), 18.0, 24.0, (0, 0, 1), 'front')
    draw_face(pen, v, F, lambda p_, W, H: _bu_photo(p_, W / 2, H / 2, W - 4, H - 4, 'bus'), '#5a3a20', ao=False, lw=0.8)
    B = Box(DS.cx + 0.3, DS.cy, 0.16, 0.1, Y, Y + 0.07, 0)
    draw_box(pen, v, B, {'all': '#8a3a4a', 'top': '#a84a5a'}, lw=0.6)


BU_SBED = Box(0.28, 8.6, 0.95, 1.9, BU_UP, BU_UP + 0.5, 0)


def _sami_cfg(o):
    U = BU_UP
    def lights(o):
        amb = _bu_house_light(o, '#1c2236')
        win = Lamp(kind='win', c='#7a88c8', k=0.45, soft=10.0, panes=_panes_y(BU_SWIN[0], BU_SWIN[1], U + BU_SWIN[2], U + BU_SWIN[3], 9.6), d=_norm3((0.0, -0.45, -1.0)))
        nl = Lamp(-0.55, U + 0.7, 9.25, 2.6, '#c8f0a0', 0.9 * _static(o.get('nightlight', 1.0), 1.0), fall=1.5)
        steady = [] if o.get('blackout') else [win, nl]
        var = [('ceil', [Lamp(-1.3, U + BU_UH - 0.08, 7.5, 4.5, '#fff0d8', 1.2, (1.0, 0.5, 0.2), fall=1.3)], _kfn(o.get('ceil', 0.0), 361)),
               ('hall', [Lamp(-3.0, U + 1.6, 6.0, 2.6, '#ffd8a0', 0.8, fall=1.5)], _kfn(o.get('hall', 0.0), 362)), _phone_lamp(o), _flash_lamp(o)]
        return amb, steady, var
    def east(p_, W, H):
        _bu_photo(p_, (9.6 - 7.2) * 100, H - 170, 50, 66, 'dino', frame='#4a8ad8')
    def south(p_, W, H):
        p_.fill(rect((0.8 - (-1.4)) * 100 - 30, H - 205, 60, 22), '#f4f0e0'); btext(p_, 'SAMI', (0.8 - (-1.4)) * 100, H - 188, 'kid', 16, '#4aa06a', 240, 'center')
    holes = {'west': [(-3.4, BU_SDOOR[0], -3.4, BU_SDOOR[1], 0.0, BU_SDOOR[2])]}
    wins = {'back': [(BU_SWIN[0], 9.6, BU_SWIN[1], 9.6, BU_SWIN[2], BU_SWIN[3], (2, 2))]}
    runs = _rect_runs(BU_SAMI, holes, wins, {'east': east, 'front': south})
    rug = _bu_rug_art(BU_SAMI[0], BU_SAMI[3], -1.4, 7.4, 0.9, 0.7, ('#4aa06a', '#e8d870', '#4a8ad8', '#f4f0e0'))

    def pieces(o):
        bp = bu_bed_parts(BU_SBED, U, o.get('bed', 'turned'), '#e8e4dc', quilt_c='#3a6a9a', dino=True)
        P = [Piece('bed', (BU_SBED.cx, U + 0.4, BU_SBED.cy), lambda pen, v: draw_parts(pen, v, bp), block=BU_SBED.footprint())]
        NS = Box(-0.55, 9.3, 0.4, 0.36, U, U + 0.55, 0)
        def ns(pen, v):
            draw_box(pen, v, NS, {'all': '#f2eee6', 'front': dict(fill='#f2eee6', art=lambda p_, W, H: p_.line(rect(4, 6, W - 8, H * 0.38), 0.8, '#000000', 110))})
            P_ = (NS.cx - 0.08, U + 0.55, NS.cy)
            if v.d(P_[0], P_[2]) > 0.3:                                           # the dinosaur nightlight
                x, y = v.p(*P_); s = v.s(P_[0], P_[2])
                _dino_sil(pen, x, y - 0.05 * s, 0.1 * s, 1, mix('#4aa06a', '#d8f8b0', _static(o.get('nightlight', 1.0), 1.0)))
            if o.get('walkie', True): bu_walkie(pen, v, NS.cx + 0.08, U + 0.55, NS.cy - 0.02, 60.0, '#e05a3a')
        P.append(Piece('nightstand', (NS.cx, U + 0.4, NS.cy), ns, block=NS.footprint()))
        TB = Box(-2.85, 9.2, 0.8, 0.45, U, U + 0.5, 0)
        P.append(Piece('toybox', (TB.cx, U + 0.3, TB.cy), lambda pen, v: draw_box(pen, v, TB, {'all': '#4a8ad8', 'top': '#3a7ac8', 'front': dict(fill='#4a8ad8', art=lambda p_, W, H: (
            btext(p_, 'TOYS', W / 2, H * 0.6, 'kid', H * 0.35, '#fff6dc', 240, 'center'), _dino_sil(p_, W * 0.82, H * 0.6, H * 0.3, 2, '#e8d870')))}), block=TB.footprint()))
        if o.get('rex') == 'bed':
            P.append(Piece('rex', (BU_SBED.cx, U + 0.6, BU_SBED.cy + 0.55), lambda pen, v: bu_rex(pen, v, BU_SBED.cx - 0.05, U + 0.55, BU_SBED.cy + 0.55)))
        return P

    def spots(v, o):
        S = {}
        S['bed'] = _mk_spot(v, 'bed', BU_SBED.cx, 8.6, U + 0.5, 'lie', "Sami's bed (head at the back wall)")
        S['bed_edge'] = _mk_spot(v, 'bed_edge', -0.3, 8.3, U, 'seat', 'sitting on the side of the bed (facing -x)', face=(-1, 0), seat_Y=0.5)
        S['door_in'] = _mk_spot(v, 'door_in', -2.95, 6.0, U, 'stand', 'just inside his door', face=(1, 0))
        S['room_mid'] = _mk_spot(v, 'room_mid', -1.3, 7.4, U, 'stand', 'the middle of the room (Sami hugging Rex, proud)')
        S['walkie'] = _mk_spot(v, 'walkie', -0.47, 9.28, U + 0.55, 'surface', "Sami's walkie on the nightstand")
        S['rex'] = _mk_spot(v, 'rex', BU_SBED.cx, BU_SBED.cy + 0.55, U + 0.55, 'surface', 'Rex on the bed')
        S['window'] = _mk_spot(v, 'window', -1.7, 9.2, U, 'stand', 'at his window', face=(0, 1))
        return S
    return dict(name='sami', R=BU_SAMI, Y0=U, H=BU_UH, floor=dict(base='#9a6a44', kind='boards', ink='#4a2e1a', seed=43, art=rug), runs=runs,
                walls=dict(paper=BU_PAL['sami_paper'], ink=BU_PAL['sami_ink'], kind='stars', wains=0.0, seed=47, scale=1.0, pa=120),
                ceil=dict(c='#eef2f4'), lights=lights, pieces=pieces, spots=spots)


def bu_rex(pen, v, x, Y, y, s=1.0):
    """Rex, Sami's stuffed dinosaur, sitting (soft green, felt spikes, button eyes)."""
    if v.d(x, y) < 0.2: return
    px, py = v.p(x, Y, y); k = v.s(x, y) * s
    body = union(oval(px, py - 0.09 * k, 0.11 * k, 0.1 * k), oval(px + 0.06 * k, py - 0.22 * k, 0.07 * k, 0.065 * k))
    body = union(body, smooth([(px - 0.09 * k, py - 0.04 * k), (px - 0.24 * k, py - 0.02 * k), (px - 0.1 * k, py - 0.1 * k)], True, 0.8))
    pen.fill(body, lit('#5ab07a', (x, Y + 0.1, y), None)); pen.line(body, 1.0)
    for i in range(4):
        cx_, cy_ = px - 0.05 * k + i * 0.04 * k, py - 0.2 * k + i * 0.02 * k
        sp_ = poly([(cx_ - 0.02 * k, cy_), (cx_, cy_ - 0.04 * k), (cx_ + 0.02 * k, cy_)])
        pen.fill(sp_, '#e88a3a'); pen.line(sp_, 0.6)
    pen.fill(oval(px + 0.09 * k, py - 0.235 * k, 0.012 * k), '#101010')
    pen.fill(oval(px - 0.02 * k, py - 0.02 * k, 0.05 * k, 0.03 * k), '#8ad0a0')


# ---------------------------------------------------------------------------------------------- house builders
def _bu_outside_front(o):
    """The outside through a front / side window (cached): Larch Street, our yard, both buses (his amber windows glow)."""
    def f(pen, v):
        bu_ext_draw(pen, v, o, house=False)
        with lighting(*_bu_ext_light(o.get('tod', 'night'))):
            bu_mailbox(pen, v, o.get('letters', 1.0)); bu_porch(pen, v, o)
            if v.d(*BU_LAMP) > 0.8: dr_streetlight(pen, v, BU_LAMP[0], BU_LAMP[1], 1.0, arm=1.0)
            buses = []
            if o.get('bus9', True): buses.append((BU_BUS9, 'bus9'))
            if o.get('his'): buses.append(((o.get('his_x', BU_HISBUS[0]), BU_HISBUS[1], BU_HISBUS[2]), 'his'))
            buses.sort(key=lambda q: -v.d(q[0][0], q[0][1]))
            for (b, kind) in buses:
                draw_parts(pen, v, bu_bus_parts(b[0], b[1], b[2], kind))
                bu_bus_door(pen, v, b[0], b[1], b[2], kind, o.get('his_door', 0.0) if kind == 'his' else 0.0, broom=1.0 if (kind == 'bus9' and o.get('broom') == 'bus9') else 0.0)
        for (b, kind) in buses:
            bu_bus_emit(pen, v, b[0], b[1], b[2], kind, _static(o.get('his_win', 1.0), 1.0) if kind == 'his' else 0.0, _static(o.get('his_heads', 0.0)) if kind == 'his' else 0.0)
        if o.get('tod', 'night') == 'night':
            for (x, y) in BU_LAMPS + [BU_LAMP]: dr_streetlight_glow(pen, v, x, y, 1.0, BU_SODIUM, 1.0, rain=False)
    return f


def _house_o(kw, defaults):
    o = dict(defaults); o.update(kw)
    for k_ in list(o):
        if k_ in ('phone', 'flash', 'lamp', 'ceil', 'tv', 'heads', 'hall', 'porch', 'up', 'liv', 'gran', 'sami', 'curtains', 'frost'): continue
    o['no_veil'] = True
    return o


def bu_living(view='wide', **kw):
    """The living room. view 'wide' (from the back-east corner: couch, window, the opening with the front door) |
    'reverse' (from the window: the couch face-on) | 'couch' (medium on the couch) | 'window' (the curtains and the gap) |
    'door' (from the couch through the opening to the front door) | 'hand' (close on the right seat: the walkie / the
    hand in the dark). Levels (number or f(t)): lamp, ceil, tv, heads (his headlights through the curtains), hall, phone
    (+ phone_at=(x, Y, y)), flash. curtains: gap 0 (closed) .. 1 (open), default 0.12; backpack 'window' | 'wall' | None;
    walkie True/False; blackout True (every light dead: only phone / flash light); his (his bus at the kerb outside)."""
    o = _house_o(kw, dict(tod='night', curtains=0.12, backpack='window', walkie=True, his=True, his_win=1.0, letters=1.0, broom='porch'))
    v = cam('bu_liv_' + view)
    main = BuBox(_liv_cfg(o))
    hall = BuBox(_hall_cfg(o), far=True)
    far = [hall, _dark_far('kitchen', _r4p((-3.2, 4.6, 5.8, 9.6)))]
    grade = 'bu_dark' if o.get('blackout') else ('bu_warm' if _static(o.get('lamp', 0.0)) > 0.3 or _static(o.get('ceil', 0.0)) > 0.3 else 'bu_night')
    dyn = []
    amb, steady, var = main.lights(o)
    if callable(o.get('curtains')):
        cf = o['curtains']
        dyn.append(live_layer('curtains', v, (-0.6, 1.4, 0.14), lambda pen, v_, t: curtain_pair(pen, v_, (2.4, 0.0), (-3.2, 0.0), 2.4 - BU_PWIN[1], 2.4 - BU_PWIN[0],
                                                                                                2.3, 2.25, 0.0, cf(t), BU_CURT_C, sheer=True), amb, steady, var))
    sp = build_view('bu_liv_' + view, v, main, o, far=far, outside=_bu_outside_front(o), grade=grade, dyn=dyn)
    sp.info['note'] = 'Living room: seats couch_left / couch_mid / couch_right (Mina right, her walkie beside her: anchor walkie).'
    return sp


def bu_hall(view='door', **kw):
    """The front hall. view 'door' (down the hall to the front door: frosted panes, peephole, the rules) | 'doorclose' |
    'side' (3/4 on the door from the opening: Mina at the peephole in profile) | 'stairs' (from the door: the stairs
    rising on the left, the back door at the end) | 'up' (up the stairs from their foot) | 'window' (to the side window:
    bus 9 across the yard). Levels: hall (ceiling lights), porch (through the panes), heads (his headlights through
    the panes), up (upstairs light down the stairwell), liv (living-room spill), phone, flash. door (front door, deg
    open), back_door, rules (taped inside), eighth (rule 8 added), frost (his silhouette through the panes: level spec),
    ticket (the punched ticket on the floor under the door: 0 none .. 1 slid in)."""
    o = _house_o(kw, dict(tod='night', rules=True, eighth=False, his=True, letters=1.0, broom='porch'))
    v = cam('bu_hall_' + view)
    main = BuBox(_hall_cfg(o))
    far = [BuBox(_liv_cfg(dict(o, _far=True)), far=True), _dark_far('kitchen', _r4p((-3.2, 4.6, 5.8, 9.6)))]
    up = dict(o, _far=True)
    far.append(BuBox(_up_cfg(up), far=True))
    grade = 'bu_dark' if o.get('blackout') else ('bu_warm' if _static(o.get('hall', 0.0)) > 0.3 else 'bu_night')
    dyn = []
    if o.get('frost') is not None:
        dyn.append(_frost_layer(v, bu_front_door_leaf(), o['frost']))
    amb, steady, var = main.lights(o)
    if callable(o.get('door')):
        D = bu_front_door_leaf(o.get('rules', True), o.get('eighth', False)); df = o['door']
        dyn.append(live_layer('front_door', v, (-3.95, 1.0, 0.2), lambda pen, v_, t: D.draw(pen, v_, df(t)), amb, steady, var))
    sp = build_view('bu_hall_' + view, v, main, o, far=far, outside=_bu_outside_front(o), grade=grade, dyn=dyn)
    return sp


def bu_upstairs(view='hall', **kw):
    """The upstairs hall (floor %.2f, ceiling %.2f): view 'hall' (from Grandma's doorway down the hall: he fills it bent
    double) | 'back' (from the landing toward Grandma's door) | 'stairs' (down the stairs from the landing). gran_door /
    sami_door: degrees open; up (ceiling lights), gran / sami (their rooms' light through open doors), phone, flash,
    blackout.""" % (BU_UP, BU_UP + BU_UH)
    o = _house_o(kw, dict(tod='night', gran_door=0.0, sami_door=0.0))
    v = cam('bu_up_' + view)
    main = BuBox(_up_cfg(o))
    far = [BuBox(_hall_cfg(dict(o, _far=True)), far=True)]
    if _static(o.get('gran_door', 0.0)) > 5 or callable(o.get('gran_door')): far.append(BuBox(_gran_cfg(dict(o, door=o.get('gran_door', 0.0))), far=True))
    if _static(o.get('sami_door', 0.0)) > 5 or callable(o.get('sami_door')): far.append(BuBox(_sami_cfg(o), far=True))
    grade = 'bu_dark' if o.get('blackout') else ('bu_warm' if _static(o.get('up', 0.0)) > 0.3 else 'bu_night')
    dyn = []
    amb, steady, var = main.lights(o)
    if callable(o.get('gran_door')):
        GD = bu_gran_door(_static(o.get('bolt', 1.0), 1.0)); gf = o['gran_door']
        dyn.append(live_layer('gran_door', v, (-4.0, BU_UP + 1.0, 3.1), lambda pen, v_, t: GD.draw(pen, v_, gf(t)), amb, steady, var))
    return build_view('bu_up_' + view, v, main, o, far=far, outside=lambda pen, v_: _dr_outside_back(pen, v_), grade=grade, dyn=dyn)


def bu_gran(view='door', **kw):
    """Grandma's room (upstairs, the only deadbolt): view 'door' (Mina sitting with her back against the door) | 'window'
    (to the window over the driveway) | 'wide'. lamp, ceil, hall (through the open door), phone, flash, door (deg open
    into the room or f(t)), bolt (1 thrown, 0 slid back), bed 'made' | 'turned' | 'empty'."""
    o = _house_o(kw, dict(tod='night', door=0.0, bolt=1.0, his=False, letters=0.0, broom='bus9'))
    v = cam('bu_gran_' + view)
    main = BuBox(_gran_cfg(o))
    far = [BuBox(_up_cfg(dict(o, _far=True)), far=True)] if (_static(o.get('door', 0.0)) > 5 or callable(o.get('door'))) else []
    grade = 'bu_dark' if o.get('blackout') else ('bu_warm' if _static(o.get('lamp', 0.0)) > 0.3 else 'bu_night')
    dyn = []
    amb, steady, var = main.lights(o)
    if callable(o.get('door')):
        GD = bu_gran_door(_static(o.get('bolt', 1.0), 1.0)); gf = o['door']
        dyn.append(live_layer('door', v, (-4.0, BU_UP + 1.0, 3.1), lambda pen, v_, t: GD.draw(pen, v_, gf(t)), amb, steady, var))
    return build_view('bu_gran_' + view, v, main, o, far=far, outside=_bu_outside_front(o), grade=grade, dyn=dyn)


def bu_sami(view='room', **kw):
    """Sami's room: view 'room' (from the door: the bed, the dino nightlight, the toy box) | 'bed'. ceil, hall, phone,
    flash, nightlight (0..1), bed 'made' | 'turned' | 'empty', rex ('bed' or None), walkie (his on the nightstand)."""
    o = _house_o(kw, dict(tod='night', nightlight=1.0, rex='bed', walkie=True))
    v = cam('bu_sami_' + view)
    main = BuBox(_sami_cfg(o))
    grade = 'bu_dark' if o.get('blackout') else ('bu_warm' if _static(o.get('ceil', 0.0)) > 0.3 else 'bu_night')
    return build_view('bu_sami_' + view, v, main, o, far=[], outside=lambda pen, v_: _dr_outside_back(pen, v_), grade=grade)


_bcam('bu_liv_wide', 860, 520, 1.62, 1.75, 5.45, -146, _env(), 'the living room from the back-east corner: the couch (backs), the window, the opening to the hall and the front door', 'living')
_bcam('bu_liv_reverse', 900, 520, 1.5, -1.0, 0.55, 12, _env(), 'from the window back to the couch (face-on): Mina and Sami on the couch', 'living')
_bcam('bu_liv_couch', 1050, 600, 1.15, -0.55, 1.75, 0, _env(), 'medium on the couch, face-on (empty couch / close-ups only: seated figures read best at 3/4)', 'living')
_bcam('bu_liv_couch3q', 1000, 560, 1.2, 1.35, 2.35, -42, _env(), 'the couch at 3/4 from the front-east (seated figures: Mina right seat, Sami middle)', 'living')
_bcam('bu_liv_window', 950, 500, 1.45, -0.6, 2.8, 180, _env(), 'to the picture window: the curtains, the gap', 'living')
_bcam('bu_liv_door', 900, 520, 1.15, 0.2, 4.3, -128, _env(), 'from the couch through the opening to the front door', 'living')
_bcam('bu_liv_hand', 1350, 560, 1.0, -0.15, 3.35, -8, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.08)), 'close on the right couch seat (the walkie; the hand in the dark)', 'living')
_bcam('bu_hall_door', 900, 520, 1.55, -3.95, 3.9, 180, _env(), 'down the hall to the front door', 'hall')
_bcam('bu_hall_doorclose', 1350, 520, 1.4, -3.95, 1.55, 180, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.08)), 'close on the door: panes, peephole, the rules', 'hall')
_bcam('bu_hall_side', 1000, 520, 1.45, -3.3, 1.45, -150, _env(), '3/4 on the door from the opening (Mina at the peephole in profile)', 'hall')
_bcam('bu_hall_stairs', 880, 520, 1.55, -3.85, 0.45, -6, _env(), 'from the door down the hall: the stairs rising on the left, the back door', 'hall')
_bcam('bu_hall_up', 820, 640, 1.3, -4.3, 2.0, -10, _env(), 'up the stairs from their foot', 'hall', pitch=-20.0)
_bcam('bu_hall_window', 1000, 520, 1.5, -3.6, 1.35, -98, _env(), 'to the hall side window: bus 9 across the yard', 'hall')
_bcam('bu_up_hall', 800, 520, BU_UP + 1.45, -4.0, 2.95, 0, _env(), "from Grandma's doorway down the upstairs hall (he fills it bent double)", 'uphall')
_bcam('bu_up_back', 820, 520, BU_UP + 1.5, -4.0, 8.0, 180, _env(), "from the landing toward Grandma's door", 'uphall')
_bcam('bu_up_stairs', 820, 380, BU_UP + 1.5, -5.1, 7.9, 180, _env(), 'down the stairs from the landing', 'uphall', pitch=28.0)
_bcam('bu_gran_door', 950, 520, BU_UP + 1.2, -2.5, 0.55, -32, _env(), "Grandma's room: the door with the deadbolt (Mina's back against it)", 'gran')
_bcam('bu_gran_window', 950, 520, BU_UP + 1.45, -2.7, 2.7, -112, _env(), "Grandma's room: the window over the driveway", 'gran')
_bcam('bu_gran_wide', 820, 520, BU_UP + 1.55, -1.9, 0.35, -51, _env(), "Grandma's room wide: door, window, rocker", 'gran')
_bcam('bu_sami_room', 860, 520, BU_UP + 1.4, -3.0, 6.1, 62, _env(), "Sami's room from the door", 'sami')
_bcam('bu_sami_bed', 1100, 540, BU_UP + 1.0, -1.2, 7.4, 52, _env(), "Sami's bed, Rex", 'sami')


# ====================================================================================================== inside a bus (his / bus 9)
# One bus plan for both buses, in metres: x across (+x = the door side, the bus's right), y from the windshield (y -0.2)
# back to the rear wall (y 10.5), Y up from the cabin floor (0; the ground outside is BU_IG -0.95). 11 rows of bench
# seats from y 1.3 (pitch 0.82): row r has seat 2r+1 on the left (driver side, -x) and seat 2r+2 on the right (door
# side): seat 1 is right behind the driver, seat 4 is row 1 right, seats 21 / 22 are the back row.
BU_IG = -BU_BUS_FLOOR
BU_IW = 1.2                       # half width inside
BU_IROW0, BU_IPITCH, BU_IROWS = 1.3, 0.82, 11
BU_IREAR = 10.5
BU_IWIN = (0.78, 1.5)             # window band (Y)
BU_IWALL = 1.62                   # side wall top; the roof arches to BU_IROOF
BU_IROOF = 1.98
BU_IDOOR = (-0.1, 0.92)           # the entrance (y0, y1) on x +BU_IW


def bu_seat_pos(n):
    """Plan point (x, y) of seat n's hip point (1..22) and its side ('l' / 'r')."""
    r = (n - 1) // 2; side = 'l' if n % 2 == 1 else 'r'
    y = BU_IROW0 + r * BU_IPITCH + 0.28
    return ((-0.7 if side == 'l' else 0.7), y, side)


def _bench_parts(r, side, kind, lit_=0.0):
    y0 = BU_IROW0 + r * BU_IPITCH
    x0, x1 = (-BU_IW + 0.04, -0.24) if side == 'l' else (0.24, BU_IW - 0.04)
    c = '#3a4a3a' if kind == 'his' else '#2e5a4a'
    cd = _darken(c, 0.25)
    seat = Box((x0 + x1) / 2, y0 + 0.24, x1 - x0, 0.46, 0.25, 0.42, 0)
    back = Box((x0 + x1) / 2, y0 + 0.53, x1 - x0, 0.1, 0.25, 0.98, 0)
    def bart(p_, W, H):
        p_.fill(rrect(0, 0, W, H, 6), c); p_.texture(rect(0, 0, W, H), 'grunge', 0.45 if kind == 'his' else 0.2, 'overlay', 0.8)
        p_.line(rrect(3, 3, W - 6, H - 6, 5), 0.8, '#000000', 80)
        if kind == 'his':
            for k in range(3): p_.line(smooth([(W * 0.2 + k * 20, H * 0.3), (W * 0.3 + k * 18, H * 0.45), (W * 0.25 + k * 22, H * 0.6)], False), 0.6, '#000000', 90)
    P = [Part(seat, {'all': cd, 'top': dict(fill=c, art=lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'grunge', 0.4, 'overlay', 0.8)), 'front': cd}, tag='seat'),
         Part(back, {'all': cd, 'front': dict(fill=c, art=bart), 'back': dict(fill=c, art=bart), 'top': _darken(c, 0.1)}, tag='back'),
         Part(Box(x0 + 0.06 if side == 'l' else x1 - 0.06, y0 + 0.24, 0.05, 0.05, 0.0, 0.25, 0), {'all': '#2a2a2a'}, tag='leg')]
    return P


class BuBusInterior(Room):
    """The inside of a bus: o['kind'] 'his' | 'bus9'; o['tod'] 'night' | 'morning'; o['door'] 0..1 the folding doors."""
    name = 'bus'
    poly = [(-BU_IW, -0.2), (BU_IW, -0.2), (BU_IW, BU_IREAR), (-BU_IW, BU_IREAR)]

    def __init__(self, o):
        self.o = o

    def lights(self, o):
        kind = o.get('kind', 'his'); tod = o.get('tod', 'night')
        if tod == 'morning':
            amb = '#7a7064'
            sun = Lamp(kind='win', c='#ffe0a8', k=1.1, soft=14.0, panes=[q for q in self._win_panes('l')], d=_norm3((0.9, -0.5, 0.15)))
            return amb, [sun], [_phone_lamp(o)]
        if kind == 'his':
            amb = '#4a3418'
            dome = [Lamp(0.0, BU_IROOF - 0.05, y, 3.6, BU_AMBER, 1.15, (1.0, 0.6, 0.3), fall=1.25) for y in (1.5, 4.5, 7.5)]
            seats = []
            for n, lv in (o.get('seat_lit') or {4: 1.0, 22: 1.0}).items():
                x, y, sd = bu_seat_pos(n)
                seats.append((('seat%d' % n), [Lamp(x * 1.2, 1.35, y, 1.9, '#ffb848' if n != 22 else '#ffd070', 1.6, fall=1.6)], _kfn(lv, 370 + n)))
            step = [Lamp(0.75, 1.5, 0.4, 2.6, '#ffc060', 1.7, fall=1.4)]
            var = [('dome', dome, _kfn(o.get('dome', 1.0), 369)), ('step', step, _kfn(o.get('step', 1.0), 366))] + seats + [_phone_lamp(o), _flash_lamp(o)]
            return amb, [], var
        amb = '#283048'
        dash = [Lamp(-0.5, 1.0, 0.05, 2.2, '#8ac8ff', 1.3, fall=1.5), Lamp(0.2, 1.3, 1.0, 2.4, '#c8d8ff', 0.6, fall=1.5)]
        dome = [Lamp(0.0, BU_IROOF - 0.05, y, 3.0, '#fff0d8', 0.9, (1.0, 0.4, 0.2), fall=1.4) for y in (1.5, 5.0, 8.5)]
        return amb, [], [('dash', dash, _kfn(o.get('dash', 1.0), 368)), ('dome', dome, _kfn(o.get('dome', 0.0), 369)), _phone_lamp(o), _flash_lamp(o),
                          ('mirror_amber', [Lamp(-1.0, 1.3, 0.2, 2.2, BU_AMBER, 1.0, fall=1.5)], _kfn(o.get('amber', 0.0), 367))]

    def _win_panes(self, side):
        out = []
        x = -BU_IW if side == 'l' else BU_IW
        for r in range(BU_IROWS):
            y0 = BU_IROW0 + r * BU_IPITCH + 0.08; y1 = y0 + BU_IPITCH - 0.16
            out.append([(x, BU_IWIN[1], y0), (x, BU_IWIN[1], y1), (x, BU_IWIN[0], y1), (x, BU_IWIN[0], y0)])
        return out

    def shell(self, pen, v, o):
        kind = o.get('kind', 'his'); tod = o.get('tod', 'night')
        wallc = '#6a5a3a' if kind == 'his' else '#c8c4b4'
        floorc = '#2a2620' if kind == 'his' else '#3a3e3a'
        def fart(p_, W, H):
            p_.texture(rect(0, 0, W, H), 'grunge', 0.6 if kind == 'his' else 0.3, 'overlay', 2.0)
            u0, _ = floor_uv(-BU_IW, BU_IREAR, -0.24, 0); u1, _ = floor_uv(-BU_IW, BU_IREAR, 0.24, 0)
            for k in range(int(H / 6)): p_.fill(rect(u0, k * 6, u1 - u0, 1.2), '#000000', 70)
        floor_rect(pen, v, -BU_IW, BU_IW, -0.2, BU_IREAR, 0.0, floorc, None, art=fart)
        # side walls with a window per row (holes), the front wall (windshield), the rear wall (emergency door window)
        def wins(side):
            hs = []
            for r in range(BU_IROWS):
                y0 = BU_IROW0 + r * BU_IPITCH + 0.08; y1 = y0 + BU_IPITCH - 0.16
                hs.append((y0, y1))
            return hs
        def side_art(p_, W, H):
            p_.texture(rect(0, 0, W, H), 'grunge', 0.55 if kind == 'his' else 0.25, 'overlay', 1.2)
            for k in range(int(W / 40)): p_.fill(oval(k * 40 + 20, H - BU_IWIN[0] * 100 + 8, 1.0), '#000000', 120)          # rivets
            p_.fill(rect(0, H - BU_IWIN[0] * 100 + 2, W, 4), '#000000', 60)
        left = [(-BU_IW, y1, -BU_IW, y0, BU_IWIN[0], BU_IWIN[1]) for (y0, y1) in wins('l')] + [(-BU_IW, 0.15, -BU_IW, 0.95, 0.85, 1.55)]
        right = [(BU_IW, y0, BU_IW, y1, BU_IWIN[0], BU_IWIN[1]) for (y0, y1) in wins('r')] + [(BU_IW, BU_IDOOR[0], BU_IW, BU_IDOOR[1], BU_IG, 1.8)]
        for (a, b, hs) in (((-BU_IW, BU_IREAR), (-BU_IW, -0.2), left), ((BU_IW, -0.2), (BU_IW, BU_IREAR), right)):
            u_of, L = _u_of(a, b)
            holes = [(min(u_of(xa, ya), u_of(xb, yb)), v0 - BU_IG, max(u_of(xa, ya), u_of(xb, yb)), v1 - BU_IG) for (xa, ya, xb, yb, v0, v1) in hs]
            wall(pen, v, a, b, BU_IG, BU_IWALL, wallc, None, None, holes, wains=0.0, art=side_art, casing=0.0, thick=0.05, trim=_darken(wallc, 0.3))
        # windshield wall (y -0.2) and the rear wall
        u_of, L = _u_of((BU_IW, -0.2), (-BU_IW, -0.2))
        wall(pen, v, (BU_IW, -0.2), (-BU_IW, -0.2), 0.0, BU_IWALL, wallc, None, None, [(0.06, 0.95, 2.34, 1.9)], wains=0.0, casing=0.0, thick=0.04,
             trim='#1a1a1a')
        wall(pen, v, (-BU_IW, BU_IREAR), (BU_IW, BU_IREAR), 0.0, BU_IWALL, wallc, None, None, [(0.82, 0.9, 1.58, 1.55)], wains=0.0, casing=0.0, thick=0.05,
             trim='#1a1a1a', art=lambda p_, W, H: (p_.fill(rect(70, 20, 100, H - 20), _darken(wallc, 0.1)), p_.line(rect(70, 20, 100, H - 20), 1.0, '#000000', 120),
                                                  btext(p_, 'EMERGENCY DOOR', W / 2, H - 95, 'sans_b', 5, '#a01a12', 220, 'center')))
        # the roof: an arch of strips from each wall top to the centre
        segs = 4
        for sd in (-1, 1):
            for k in range(segs):
                a0 = k / segs; a1 = (k + 1) / segs
                def pt(a): return (sd * BU_IW * math.cos(a * math.pi / 2), BU_IWALL + (BU_IROOF - BU_IWALL) * math.sin(a * math.pi / 2))
                (xa, Ya), (xb, Yb) = pt(a0), pt(a1)
                q = [(xa, Ya, -0.2), (xb, Yb, -0.2), (xb, Yb, BU_IREAR), (xa, Ya, BU_IREAR)]
                n = _norm3((-(sd) * (Yb - Ya), -(abs(xb - xa)), 0.0)) if False else _norm3((-sd * (Yb - Ya), -abs(xb - xa), 0.0))
                if v.cam_h > Ya and v.cam_h > Yb: continue
                path = v.poly3(q)
                if path.isEmpty(): continue
                cen = ((xa + xb) / 2, (Ya + Yb) / 2, BU_IREAR / 2)
                pen.fill(path, lit('#8a7a5a' if kind == 'his' else '#e8e4d8', cen, n)); pen.line(path, 0.6, '#000000', 90)
        for yy in np.arange(0.4, BU_IREAR, 0.82):                                  # roof ribs
            pts = [v.p(BU_IW * math.cos(a), BU_IWALL + (BU_IROOF - BU_IWALL) * math.sin(a), yy) for a in np.linspace(0, math.pi, 12) if v.d(0, yy) > 0.25]
            if len(pts) > 2: pen.line(poly(pts, False), 1.0, '#000000', 60)
        # the stairwell: the floor cut away at the door, three steps down to the ground
        for i, (xa, xb, Y) in enumerate(((0.5, BU_IW, -0.32), (0.8, BU_IW, -0.64), (1.0, BU_IW + 0.15, BU_IG))):
            B = Box((xa + xb) / 2, (BU_IDOOR[0] + BU_IDOOR[1]) / 2, BU_IDOOR[1] - BU_IDOOR[0], xb - xa, Y - 0.04, Y, 90)
            draw_box(pen, v, B, {'top': dict(fill='#2a2a28', art=lambda p_, W, H: p_.fill(rect(0, 0, W, 4), '#d8b020' if kind == 'bus9' else '#7a6a20', 200)), 'all': '#1a1a18'}, lw=0.8)

    def pieces(self, o):
        kind = o.get('kind', 'his')
        P = []
        hide = set(o.get('empty_rows', ()))
        for r in range(BU_IROWS):
            for side in ('l', 'r'):
                ps = _bench_parts(r, side, kind)
                n = 2 * r + (1 if side == 'l' else 2)
                x, y, _ = bu_seat_pos(n)
                P.append(Piece('seat%d' % n, (x, 0.5, y), (lambda ps_: lambda pen, v: draw_parts(pen, v, ps_))(ps), occupant=[(x, y)], front=ps,
                               block=_r4p(((-BU_IW, -0.24) if side == 'l' else (0.24, BU_IW)) + (y - 0.28, y + 0.36))))
        # the driver's seat, the dash, the wheel, the stanchion and the door lever
        def driver(pen, v):
            draw_box(pen, v, Box(-0.65, 0.62, 0.5, 0.5, 0.0, 0.45, 0), {'all': '#1a1a1a', 'top': '#2a2a2a'}, lw=0.8)
            draw_box(pen, v, Box(-0.65, 0.9, 0.5, 0.12, 0.3, 1.15, 0), {'all': '#1a1a1a', 'front': '#2a2a2a'}, lw=0.8)
        P.append(Piece('driver_seat', (-0.65, 0.5, 0.65), driver, occupant=[(-0.65, 0.62)], front=[Part(fn=driver, ref=(-0.65, 0.5, 0.65))], block=_r4p((-0.9, -0.4, 0.37, 0.96))))
        P.append(Piece('dash', (-0.2, 0.8, -0.05), lambda pen, v: _bus_dash(pen, v, o), block=_r4p((-BU_IW, BU_IW, -0.2, 0.1))))
        P.append(Piece('wheel', (-0.65, 1.0, 0.15), lambda pen, v: _bus_wheel(pen, v)))
        P.append(Piece('stanchion', (0.52, 1.0, 0.98), lambda pen, v: (pen.seg(v.p(0.52, 0.0, 0.98), v.p(0.52, BU_IWALL + 0.2, 0.98), max(1.5, 0.035 * v.s(0.52, 0.98)),
                                                                                lit('#a8a8a0', (0.52, 1.0, 0.98), None)) if v.d(0.52, 0.98) > 0.6 else None)))
        dk = o.get('door', 0.0)
        if not callable(dk):
            P.append(Piece('doors', (BU_IW, 0.6, 0.4), lambda pen, v: _bus_doors_in(pen, v, o, _static(dk))))
        return P

    def glows(self, v, o):
        kind = o.get('kind', 'his')
        G = []
        if kind == 'his' and o.get('tod', 'night') == 'night':
            sl = o.get('seat_lit') or {4: 1.0, 22: 1.0}
            for n, lv in sl.items():
                kf = _kfn(lv, 370 + n); x, y, sd = bu_seat_pos(n)
                def g(pen, t, x=x, y=y, kf=kf, n=n):
                    k = kf(t)
                    if k <= 0.01 or v.d(x, y) < 0.3: return
                    gx, gy = v.p(x * 1.25, 1.15, y); s = v.s(x, y)
                    pen.glow(gx, gy, 0.55 * s, '#ffc860' if n == 22 else BU_AMBER, (110 if n == 22 else 80) * k)
                    pen.glow(gx, gy, 0.16 * s, '#fff0c0', 90 * k)
                G.append(('seat%d_glow' % n, (x, 1.0, y - 0.05), g))
            kd = _kfn(o.get('dome', 1.0), 369)
            def domes(pen, t):
                k = kd(t)
                if k <= 0.01 or v.cam_h > BU_IROOF: return
                for y in (1.5, 4.5, 7.5):
                    if v.d(0, y) < 0.3: continue
                    pen.fill(ellipse3(v, 0.0, y, 0.18, 0.1, BU_IROOF - 0.03), '#ffb050', 200 * k)
                    gx, gy = v.p(0.0, BU_IROOF - 0.05, y); pen.glow(gx, gy, 0.5 * v.s(0, y), BU_AMBER, 90 * k)
            G.append(('domes', (0.0, BU_IROOF, 5.0), domes))
        return G

    def spots(self, v, o):
        S = {}
        for n in range(1, 23):
            x, y, sd = bu_seat_pos(n)
            S['seat%d' % n] = _mk_spot(v, 'seat%d' % n, x, y, 0.0, 'seat', 'seat %d (%s side), facing forward (-y)' % (n, 'driver' if sd == 'l' else 'door'), face=(0, -1), seat_Y=0.42)
            S['window%d' % n] = _mk_spot(v, 'window%d' % n, (-BU_IW if sd == 'l' else BU_IW) * 0.99, y, 1.15, 'point', 'the window of seat %d' % n)
            for (tag, xx) in (('win', 0.92), ('aisle', 0.46)):
                S['seat%d_%s' % (n, tag)] = _mk_spot(v, 'seat%d_%s' % (n, tag), xx if sd == 'r' else -xx, y, 0.0, 'seat', 'seat %d, %s side of the bench (two kids share a bench)' % (n, tag),
                                                     face=(0, -1), seat_Y=0.42)
        S['driver'] = _mk_spot(v, 'driver', -0.65, 0.62, 0.0, 'seat', "the driver's seat (facing the windshield, -y)", face=(0, -1), seat_Y=0.45)
        S['top_step'] = _mk_spot(v, 'top_step', 0.25, 0.42, 0.0, 'stand', 'at the top of the steps (facing the door, +x)', face=(1, 0))
        S['top_step_back'] = _mk_spot(v, 'top_step_back', 0.15, 0.7, 0.0, 'stand', 'at the top of the steps facing back down the aisle (+y)', face=(0, 1))
        S['step1'] = _mk_spot(v, 'step1', 0.65, 0.42, -0.32, 'stand', 'on the top step (facing out)', face=(1, 0))
        S['bottom_step'] = _mk_spot(v, 'bottom_step', 1.05, 0.42, BU_IG + 0.3, 'stand', 'on the bottom step (Mina never goes higher)', face=(-1, 0))
        S['outside_door'] = _mk_spot(v, 'outside_door', 1.75, 0.42, BU_IG, 'stand', 'on the ground outside the door, facing in (-x)', face=(-1, 0))
        for k in (2, 5, 8, 10):
            S['aisle%d' % k] = _mk_spot(v, 'aisle%d' % k, 0.0, BU_IROW0 + k * BU_IPITCH + 0.3, 0.0, 'stand', 'in the aisle at row %d' % k)
        S['aisle_back'] = _mk_spot(v, 'aisle_back', 0.0, BU_IREAR - 0.45, 0.0, 'stand', 'the back of the aisle (by seat 22)')
        S['radio'] = _mk_spot(v, 'radio', -0.15, -0.02, 0.95, 'point', 'the dash radio (bus 9: to the depot)')
        S['wheel'] = _mk_spot(v, 'wheel', -0.65, 0.18, 0.98, 'point', 'the steering wheel centre')
        S['door_lever'] = _mk_spot(v, 'door_lever', 0.45, 0.2, 0.95, 'point', 'the door lever')
        return S


def _bus_dash(pen, v, o):
    kind = o.get('kind', 'his')
    B = Box(-0.15, -0.08, 2.3, 0.28, 0.0, 0.92, 0)
    def front(p_, W, H):
        p_.fill(rect(0, 0, W, H), '#1e1e1e'); p_.texture(rect(0, 0, W, H), 'grunge', 0.4, 'overlay', 1.0)
    def top(p_, W, H):
        p_.fill(rect(0, 0, W, H), '#262626')
        gx = W * 0.22                                                            # gauges before the wheel
        for k, xx in enumerate((gx - 14, gx + 14)):
            p_.fill(oval(xx, H * 0.6, 9), '#0a0a0a'); p_.line(oval(xx, H * 0.6, 9), 1.0, '#8a8a8a')
            if kind == 'bus9' and o.get('tod', 'night') == 'night': p_.fill(oval(xx, H * 0.6, 7), '#2a6a8a', 160)
        rx = W * 0.47                                                            # the radio
        p_.fill(rrect(rx - 16, H * 0.25, 32, H * 0.55, 2), '#141414'); p_.line(rrect(rx - 16, H * 0.25, 32, H * 0.55, 2), 0.8, '#5a5a5a')
        p_.fill(rect(rx - 12, H * 0.35, 14, 6), '#3aa86a' if kind == 'bus9' else '#5a3a1a')
        for k in range(4): p_.fill(oval(rx + 5 + k * 3, H * 0.65, 1.1), '#8a8a8a')
        if kind == 'bus9':
            btext(p_, 'DEPOT', rx, H * 0.2, 'sans_b', 3.5, '#c8c8c8', 200, 'center')
            p_.fill(rrect(W * 0.62, H * 0.2, 14, 22, 2), '#0a0a0a'); p_.line(rrect(W * 0.62, H * 0.2, 14, 22, 2), 0.6, '#5a5a5a')       # phone mount
    draw_box(pen, v, B, {'front': dict(fill='#1e1e1e', art=front), 'top': dict(fill='#262626', art=top), 'back': dict(fill='#1e1e1e', art=front), 'all': '#1a1a1a'}, lw=0.8)
    # the radio handset on its hook (coiled cord)
    P = (-0.08, 0.98, 0.0)
    if v.d(P[0], P[2]) > 0.25:
        x, y = v.p(*P); s = v.s(P[0], P[2])
        pen.fill(rrect(x - 0.03 * s, y - 0.05 * s, 0.06 * s, 0.09 * s, 0.015 * s), '#141414'); pen.line(rrect(x - 0.03 * s, y - 0.05 * s, 0.06 * s, 0.09 * s, 0.015 * s), 0.8, '#4a4a4a')
        pen.line(smooth([(x, y + 0.04 * s), (x + 0.02 * s, y + 0.08 * s), (x - 0.01 * s, y + 0.12 * s), (x + 0.03 * s, y + 0.15 * s)], False), max(0.8, 0.006 * s), '#2a2a2a')


def _bus_wheel(pen, v):
    """The big steering wheel, tilted nearly flat, on its column."""
    c = (-0.65, 0.98, 0.18); r = 0.25; tilt = math.radians(58)
    pts = [(c[0] + r * math.cos(a), c[1] + r * math.sin(a) * math.cos(tilt), c[2] - r * math.sin(a) * math.sin(tilt)) for a in np.linspace(0, 2 * math.pi, 40)]
    if min(v.d(p_[0], p_[2]) for p_ in pts) < 0.15: return
    path = v.poly3(pts)
    if path.isEmpty(): return
    s = v.s(c[0], c[2])
    pen.line(path, max(2.0, 0.05 * s) + 2, LINE); pen.line(path, max(1.6, 0.05 * s), '#1e1e1e')
    pen.seg(v.p(*c), v.p(c[0], 0.5, c[2] - 0.15), max(1.5, 0.05 * s), '#141414')
    for a in (math.pi * 0.5, math.pi * 1.15, math.pi * 1.85):
        q = (c[0] + r * math.cos(a), c[1] + r * math.sin(a) * math.cos(tilt), c[2] - r * math.sin(a) * math.sin(tilt))
        pen.seg(v.p(*c), v.p(*q), max(1.0, 0.025 * s), '#2a2a2a')


def _bus_doors_in(pen, v, o, k, broom=0.0, bend=0.0, crack=0.0):
    """The folding doors from inside (x = +BU_IW), k 0 closed .. 1 open; broom wedged between the leaves."""
    kind = o.get('kind', 'his')
    y0, y1 = BU_IDOOR
    leaf = 0.5 * (1.0 - 0.82 * k)
    def P(f, Y): return (BU_IW - 0.01, Y, y0 + (y1 - y0) * f)
    Yb, Yt = BU_IG + 0.05, 1.78
    out = v.poly3([P(0, Yt), P(1, Yt), P(1, Yb), P(0, Yb)])
    if out.isEmpty(): return
    b = out.computeTightBounds()
    outside = o.get('door_out', '#06080e')
    from_out = v.hx > BU_IW
    if not from_out: pen.fill(out, outside)
    if kind == 'his' and o.get('tod', 'night') == 'night': pen.linear(out, 0, b.top(), 0, b.bottom(), [(0, '#000000', 0), (1, BU_AMBER, 50)])
    gl = '#0e1218'
    for side in (0, 1):
        f0, f1 = (0.0, leaf) if side == 0 else (1.0 - leaf, 1.0)
        for (fa_, fb_) in ((f0, (f0 + f1) / 2), ((f0 + f1) / 2, f1)):
            lp = v.poly3([P(fa_, Yt), P(fb_, Yt), P(fb_, Yb), P(fa_, Yb)])
            if lp.isEmpty(): continue
            pen.fill(lp, '#1a1a1a'); pen.line(lp, 1.0)
            for (ya, yb_) in ((Yb + 0.08, (Yb + Yt) / 2 - 0.03), ((Yb + Yt) / 2 + 0.03, Yt - 0.06)):
                g = v.poly3([P(fa_ + 0.03, yb_), P(fb_ - 0.03, yb_), P(fb_ - 0.03, ya), P(fa_ + 0.03, ya)])
                if not g.isEmpty() and not from_out: pen.fill(g, gl, 235); pen.fill(g, outside, 120)
                elif not g.isEmpty(): pen.fill(g, '#2a1a08', 200)
    if not from_out: pen.line(out, 2.0)
    if broom > 0.01:
        bu_broom(pen, v, P(0.5, 1.6), P(0.5, -0.5) if False else (BU_IW + 0.6, 0.2, (y0 + y1) / 2), broom, bend, crack)


def _bus_outside(o):
    """What the bus windows show (cached): night: dark yard / road verge with far lights; morning: a sunny street."""
    tod = o.get('tod', 'night'); kind = o.get('kind', 'his')
    def f(pen, v):
        if tod == 'morning':
            pen.linear(rect(-800, -600, 3600, 2400), 0, v.h - 1.0 * v.S, 0, v.h + 40, [(0, '#6a9ad0'), (0.7, '#d8d0c0'), (1, '#e8d8b8')])
            with lighting(*_bu_ext_light('morning')):
                draw_face(pen, v, floor_face(-60.0, 60.0, -200.0, 200.0, BU_IG - 0.02), lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'grunge', 0.6, 'overlay', 5.0), '#5a7a3e', ao=False, line=False)
                draw_face(pen, v, floor_face(-5.4, 2.1, -200.0, 200.0, BU_IG), lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'asphalt', 0.6, 'overlay', 1.6), '#5a5c60', ao=False, line=False)
                for k in range(-12, 12):
                    for xs in (-14.0, 10.0):
                        x0 = xs; y0 = k * 16.0 + 4 * _h(k, 2)
                        if v.d(x0, y0) < 2: continue
                        dr_neighbour(pen, v, x0 - 4, x0 + 4, y0, 7.0, 'dawn', seed=k * 7 + int(xs)) if False else None
            vg = lifted(v, BU_IG)
            for i, x in enumerate(np.arange(-40.0, 40.0, 5.0)):
                for yy in (-8.0, 8.0):
                    if vg.d(x if False else yy, x) < 1: continue
                    if vg.d(yy, x) < 1.5: continue
                    bx, by = vg.p(yy, 0.0, x)
                    draw_tree(pen, bx, by, 6.0 * vg.s(yy, x), 0.0, 700 + i, 0.0, '#3a5a34', None, 4)
        else:
            pen.fill(rect(-800, -600, 3600, 2400), '#05060a')
            pen.linear(rect(-800, v.h - 0.3 * v.S, 3600, 0.6 * v.S), 0, v.h - 0.3 * v.S, 0, v.h + 0.3 * v.S, [(0, '#000000', 0), (0.5, '#3a2a1a' if kind == 'his' else '#1a2030', 120), (1, '#000000', 0)])
            rng = np.random.default_rng(5)
            for i in range(10):
                az = rng.uniform(-180, 180); q = sky_dir(v, az, rng.uniform(0.2, 2.0))
                if q: pen.glow(q[0], q[1], 0.02 * v.S, BU_SODIUM, 120)
    return f


def bu_road_scroll(pen, v, t, speed=14.0, G=BU_IG, his=None, his_kind='his', side='ahead', amber=1.0, brake=0.0, head_out=False):
    """The night road outside a moving bus (live; bus plan: the bus drives toward -y): asphalt, the centre dashes, the
    verge, trees and poles streaming past; his = (x, y) of his bus on this plan (y < 0 ahead, y > 0 behind) or None."""
    off = (t * speed) % 12.0
    road = floor_face(-5.4, 2.1, -300.0, 300.0, G)
    draw_face(pen, v, road, lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'asphalt', 0.6, 'overlay', 1.6), '#1c1d22', ao=False, line=False)
    for k in range(-24, 24):
        y = k * 12.0 - off
        q = v.poly3([(-1.95, G + 0.005, y), (-1.85, G + 0.005, y), (-1.85, G + 0.005, y + 4.0), (-1.95, G + 0.005, y + 4.0)])
        if not q.isEmpty(): pen.fill(q, '#c8a83a', 200)
    for x in (-5.3, 2.0):
        q = v.poly3([(x, G + 0.005, -300.0), (x + 0.1, G + 0.005, -300.0), (x + 0.1, G + 0.005, 300.0), (x, G + 0.005, 300.0)])
        if not q.isEmpty(): pen.fill(q, '#d8d8d0', 150)
    for k in range(-16, 16):                                                    # trees and poles on both verges
        y = k * 9.0 - (t * speed) % 9.0
        for xx, sd in ((-9.0 - 2 * _h(k, 3), -1), (6.0 + 2 * _h(k, 5), 1)):
            if v.d(xx, y) < 1.0: continue
            bx, by = v.p(xx, G, y)
            draw_tree(pen, bx, by, (6.0 + 3 * _h(k, 7)) * v.s(xx, y), 0.0, 800 + k * 2 + (sd > 0), 0.0, '#07090c', None, 4)
    hp = v.poly3([(-1.1, G + 0.01, -1.0), (1.1, G + 0.01, -1.0), (3.0, G + 0.01, -30.0), (-4.2, G + 0.01, -30.0)])
    if not hp.isEmpty() and side == 'ahead':
        bb = hp.computeTightBounds(); x0, y0 = v.p(0.0, G, -2.0)
        pen.radial(hp, x0, y0, max(60.0, bb.height() * 1.6), [(0, '#fff2d6', 70), (0.6, '#ffe0a0', 30), (1, '#ffe0a0', 0)], clip=True)
    if his is not None:
        hx, hy = his
        draw_parts(pen, v, bu_bus_parts(hx, hy, 0.0, his_kind, G))
        bu_bus_emit(pen, v, hx, hy, 0.0, his_kind, amber, 0.0, 0.0, 0.3 * (side == 'ahead'), brake, G)


def _bus_cfg_o(kind, tod, kw):
    o = dict(kind=kind, tod=tod, door=0.0, dome=1.0 if kind == 'his' else 0.0, no_veil=True)
    o.update(kw)
    return o


def bu_bus_in(view='aisle', kind='his', tod='night', **kw):
    """Inside a bus (one plan for both buses: see BU_I*). kind 'his' (amber-dark: every seat dark except seat_lit =
    {4: 1, 22: 1} by default; dome = the dim amber dome lights) | 'bus9' (Grandma's; tod 'night' or 'morning').
    view 'aisle' (from the top of the steps down the aisle) | 'back' (from the back seat forward) | 'seat4' | 'seat22' |
    'seat21' | 'steps' (down the steps and out of the door) | 'doors' (the folding doors from inside) | 'driver' (the
    driver's seat and steps from the aisle) | 'cab' (bus 9 driving: behind Grandma, the windshield and the road) |
    'seat1' (Mina in seat 1, Grandma at the wheel) | 'radio' | 'windshield' (the driver's POV: his bus ahead) |
    'back_window' (out of the rear window). door 0..1 or f(t); broom / bend / crack (the broom in the doors);
    drive: speed m/s (the road streams past; 0 = parked); his_ahead = (x, y) of his bus on the road (y < 0 ahead);
    brake (his brake lights); amber (his windows behind: the mirror light)."""
    o = _bus_cfg_o(kind, tod, kw)
    v = cam('bu_bus_' + view)
    main = BuBusInterior(o)
    grade = {'his': 'bu_amber', 'bus9': 'bu_morning' if tod == 'morning' else 'bu_road'}[kind]
    dyn = []
    amb, steady, var = main.lights(o)
    if callable(o.get('door')) or o.get('broom'):
        dk = o['door']
        dyn.append(live_layer('doors', v, (BU_IW, 0.6, 0.4), lambda pen, v_, t: _bus_doors_in(pen, v_, o, dk(t) if callable(dk) else dk, _bu_lv(o.get('broom', 0.0), 381, t),
                                                                                           _bu_lv(o.get('bend', 0.0), 382, t), _bu_lv(o.get('crack', 0.0), 383, t)), amb, steady, var))
    drive = o.get('drive', 0.0)
    outside = _bus_outside(o)
    if drive or o.get('his_ahead') is not None or view in ('windshield', 'cab', 'back_window'):
        def road(pen, t):
            if tod == 'morning':
                return
            pen.fill(rect(-800, -600, 3600, 2400), '#040508')
            bu_road_scroll(pen, v, t, drive, BU_IG, o.get('his_ahead'), 'his', 'ahead', 0.0 if o.get('his_dark', True) else 1.0, _bu_lv(o.get('brake', 0.0), 384, t))
        lay = Layer(30.0, road, 'road', blur=None); lay.order = ORDER_OUT - 1.0
        dyn.append(lay)
    sp = build_view('bu_bus_' + view, v, main, o, outside=outside, grade=grade, dyn=dyn)
    if kind == 'his': sp._fx = bu_vhs_dirt(0.2)
    if view == 'step_out':
        sp = sp.add(_bus_skin_layer(v, kind))
    if view == 'back_window' and o.get('far_figure', True):
        sp = sp.add(_far_figure_layer(v))
    sp.info['note'] = 'Bus seats: anchors seat1..seat22 (seat Spots facing forward), driver, top_step, bottom_step, aisle<k>.'
    return sp


def _far_figure_layer(v, x=0.4, y=19.0):
    """Morning, out of the rear window: something very tall in a crooked yellow hat at the last stop (a silhouette;
    the cast can replace it: anchor 'far_figure')."""
    def draw(pen, t):
        if v.d(x, y) < 1: return
        bx, by = v.p(x, BU_IG, y); s = v.s(x, y)
        h = 2.44 * s
        body = rrect(bx - 0.12 * s, by - h, 0.24 * s, h, 0.08 * s)
        pen.fill(body, '#3a3226', 230)
        hat = poly([(bx - 0.16 * s, by - h + 0.05 * s), (bx + 0.16 * s, by - h + 0.02 * s), (bx + 0.3 * s, by - h - 0.85 * s), (bx + 0.02 * s, by - h - 0.88 * s)])
        pen.fill(hat, '#c8a030', 240)
        pen.fill(rect(bx + 0.12 * s, by - h * 0.62, 0.3 * s, 0.22 * s), '#e8e0c8', 220)
    lay = Layer(max(1.0, v.d(x, y)), draw, 'far_figure', blur=None); lay.order = ORDER_OUT - 2.0
    return lay


_bcam('bu_bus_aisle', 760, 470, 1.55, 0.12, 0.55, 0, _env(), 'from the top of the steps down the aisle: dark seats, seat 4 lit, seat 22 glowing at the back', 'bus')
_bcam('bu_bus_back', 780, 500, 1.5, 0.0, 10.15, 180, _env(), 'from the back of the aisle forward (the long arm down the aisle)', 'bus')
_bcam('bu_bus_seat4', 1100, 540, 1.2, -0.45, 1.45, 62, _env(), "seat 4 and its window (Sami's palm on the glass)", 'bus')
_bcam('bu_bus_seat22', 1050, 540, 1.25, -0.2, 8.4, 34, _env(), 'seat 22 at the back, glowing (Theo)', 'bus')
_bcam('bu_bus_seat21', 1050, 540, 1.25, 0.35, 8.4, -32, _env(), 'seat 21 at the back (the new girl in the morning)', 'bus')
_bcam('bu_bus_steps', 900, 380, 1.5, 0.05, 0.35, 92, _env(), 'from the top of the steps down and out of the door', 'bus', pitch=24.0)
_bcam('bu_bus_doors', 1000, 520, 1.05, 0.05, 0.42, 90, _env(), 'the folding doors from inside', 'bus')
_bcam('bu_bus_driver', 900, 520, 1.45, 0.42, 2.4, -152, _env(), "the driver's seat and the steps from the aisle", 'bus')
_bcam('bu_bus_cab', 800, 520, 1.42, 0.05, 1.75, -172, _env(), "bus 9 driving: behind Grandma at the wheel, the windshield, the road", 'bus')
_bcam('bu_bus_seat1', 950, 540, 1.2, 0.95, 2.05, -122, _env(), 'Mina belted in seat 1, Grandma at the wheel beyond', 'bus')
_bcam('bu_bus_radio', 1500, 540, 1.3, -0.15, 0.5, -170, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.08)), 'close on the dash radio', 'bus')
_bcam('bu_bus_windshield', 820, 500, 1.45, -0.62, 0.5, 180, _env(), "the driver's POV through the windshield: the road, his bus ahead", 'bus')
_bcam('bu_bus_back_window', 1100, 520, 1.2, 0.0, 9.7, 0, _env(), 'out of the rear window (morning: the far tall figure at the last stop)', 'bus')


def _bus_skin_layer(v, kind='his'):
    """Seen from OUTSIDE the door (view 'step_out'): the bus's door-side skin with the doorway cut out, so only the open
    door shows the inside (the steps, him at the top, the amber aisle beyond)."""
    col = _bus_col(kind)
    def draw(pen, t):
        x = BU_IW + 0.03
        F = Face((x, BU_IWALL + 0.3, -0.6), (0, 0, 1), (0, -1, 0), (BU_IREAR + 0.6) * 100, (BU_IWALL + 0.3 - BU_IG) * 100, (1, 0, 0), 'side')
        u0 = (BU_IDOOR[0] + 0.6) * 100; u1 = (BU_IDOOR[1] + 0.6) * 100
        hole = rect(u0, (BU_IWALL + 0.3 - 1.82) * 100, u1 - u0, (1.82 - BU_IG) * 100 + 2)
        def art(p_, W, H):
            p_.fill(rect(0, 0, W, H), col['body']); p_.texture(rect(0, 0, W, H), 'grunge', 0.6, 'overlay', 1.4)
            for r in range(BU_IROWS):
                a = (BU_IROW0 + r * BU_IPITCH + 0.08 + 0.6) * 100
                rr = rrect(a, (BU_IWALL + 0.3 - BU_IWIN[1]) * 100, BU_IPITCH * 100 - 16, (BU_IWIN[1] - BU_IWIN[0]) * 100, 8)
                p_.fill(rr, '#1a1206'); p_.fill(rr, BU_AMBER, 120 if kind == 'his' else 0); p_.line(rr, 3.0, col['trim'])
            for (yy, hh) in ((H - 150, 5), (H - 118, 6), (H - 70, 6)): p_.fill(rect(0, yy, W, hh), col['rail'], 170)
            p_.line(rect(u0 - 4, (BU_IWALL + 0.3 - 1.86) * 100, u1 - u0 + 8, (1.86 - BU_IG) * 100), 4.0, col['trim'])
            p_.texture(rect(0, 0, W, H), 'grunge', 0.5, 'multiply', 2.0)
        with lighting('#6a5030', [Lamp(x + 3.0, 1.0, 0.4, 8.0, '#fff2d6', 1.0, fall=1.2)]):
            draw_face(pen, v, F, art, col['body'], holes=[hole], ao=False, lw=1.2)
    lay = Layer(max(0.3, v.d(BU_IW + 0.03, 0.4)), draw, 'bus_skin', blur=None)
    lay.order = v.d(BU_IW + 0.03, 0.4) - 0.02
    return lay


_bcam('bu_bus_step_out', 760, 500, BU_IG + 1.45, BU_IW + 1.3, -0.1, -66, _env(), 'from the bottom step outside, up the steps into the amber: him at the top, the aisle beyond', 'bus', pitch=-8.0)


# ====================================================================================================== the chase road
class BuRoad(Room):
    """The night road (the chase), its own plan: the road runs along y, both buses drive toward -y; bus 9 at (0, 0),
    his bus at o['his_pos'] = (x, y) (y < 0: ahead of bus 9, > 0: behind). Ground Y 0."""
    name = 'road'
    poly = [(-30.0, -300.0), (30.0, -300.0), (30.0, 300.0), (-30.0, 300.0)]

    def lights(self, o):
        amb = '#1e2440'
        heads9 = [Lamp(0.0, 0.8, -9.0, 14.0, '#fff2d6', 1.6, (1.0, 1.0, 0.5), fall=1.3)]
        hp = o.get('his_pos', (0.0, -24.0))
        hp = hp(0.0) if callable(hp) else hp                 # his_pos may be f(t): the light keeps its start point
        his_in = [Lamp(hp[0], 2.0, hp[1], 6.0, BU_AMBER, 1.3, fall=1.4)]
        return amb, [Lamp(kind='dir', c='#7a8ac8', k=0.35, d=_norm3((0.3, -0.8, 0.5)))], [('heads9', heads9, _kfn(o.get('heads9', 1.0), 391)),
                                                                                         ('his_in', his_in, _kfn(o.get('his_win', 0.0), 392))]

    def shell(self, pen, v, o):
        dr_sky(pen, v, 'night'); dr_far_ring(pen, v, 'night', cx=0.0, cy=0.0, G=0.0)

    def pieces(self, o):
        P = [bu_bus_piece('bus9', 0.0, 0.0, 0.0, 'bus9', G=0.0, mirror_r=o.get('mirror_r', True), occupants=[bu_bus_seat_pt((0.0, 0.0, 0.0))])]
        hp = o.get('his_pos', (0.0, -24.0))
        if not callable(hp):
            P.append(bu_bus_piece('his_bus', hp[0], hp[1], 0.0, 'his', G=0.0, occupants=[bu_bus_seat_pt((hp[0], hp[1], 0.0))]))
        return P

    def glows(self, v, o):
        hp = o.get('his_pos', (0.0, -24.0))
        kw = _kfn(o.get('his_win', 0.0), 392); kb = _kfn(o.get('brake', 0.0), 393)
        G = [('bus9_emit', (0.0, 1.5, 0.0), lambda pen, t: bu_bus_emit(pen, v, 0.0, 0.0, 0.0, 'bus9', 0.0, _bu_lv(o.get('heads9', 1.0), 391, t), 0.0, 0.8, 0.0, G=0.0))]
        if not callable(hp):
            G.append(('his_emit', (hp[0], 1.5, hp[1]), lambda pen, t: bu_bus_emit(pen, v, hp[0], hp[1], 0.0, 'his', kw(t), 0.0, 0.0, 0.0, kb(t), G=0.0)))
        return G

    def spots(self, v, o):
        hp = o.get('his_pos', (0.0, -24.0))
        S = {}
        S.update(bu_bus_spots(v, 'b9_', 0.0, 0.0, 0.0, 0.0, 'bus9'))
        if not callable(hp): S.update(bu_bus_spots(v, 'his_', hp[0], hp[1], 0.0, 0.0, 'his'))
        body, hood, Lb = bu_bus_frame(hp[0] if not callable(hp) else 0.0, hp[1] if not callable(hp) else -24.0, 0.0, 0.0)
        P = body.at(body.w / 2 + 0.05, Lb / 2 - 0.6, 0)
        S['his_window'] = _mk_spot(v, 'his_window', P[0], P[2], 2.05, 'point', "his driver's window (his head comes out and turns backwards)")
        return S


def bu_road(view='side', his_pos=(0.0, -24.0), his_win=0.0, brake=0.0, speed=16.0, heads9=1.0, mirror_r=True, **kw):
    """The chase on the night road: view 'side' (beside the road: both buses side-on, the verge streaming past) | 'ahead'
    (low behind bus 9: his dark bus ahead) | 'behind' (ahead of bus 9 looking back: his amber windows following) |
    'window' (close on his driver's window). his_pos (x, y) or f(t) -> (x, y); his_win (0 dark ahead .. 1 amber),
    brake (his brake lights), speed (m/s of the verge streaming), mirror_r False after the swerve."""
    o = dict(his_pos=his_pos, his_win=his_win, brake=brake, heads9=heads9, mirror_r=mirror_r); o.update(kw)
    v = cam('bu_road_' + view)
    main = BuRoad()
    def ground(pen, t):
        off = (t * speed) % 9.0
        with lighting('#1e2440', [Lamp(0.0, 0.8, -9.0, 14.0, '#fff2d6', 1.6 * _bu_lv(heads9, 391, t), (1.0, 1.0, 0.5), fall=1.3)]):
            draw_face(pen, v, floor_face(-80.0, 80.0, -300.0, 300.0, -0.02), lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'grunge', 0.6, 'overlay', 5.0), '#141c18', ao=False, line=False)
            draw_face(pen, v, floor_face(-5.4, 2.1, -300.0, 300.0, 0.0), lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'asphalt', 0.6, 'overlay', 1.6), '#24262c', ao=False, line=False)
        for k in range(-30, 30):
            y = k * 12.0 - (t * speed) % 12.0
            q = v.poly3([(-1.95, 0.005, y), (-1.85, 0.005, y), (-1.85, 0.005, y + 4.0), (-1.95, 0.005, y + 4.0)])
            if not q.isEmpty(): pen.fill(q, '#a8902a', 200)
        trees = []
        for k in range(-30, 30):
            y = k * 9.0 - off
            for xx, sd in ((-9.0 - 2 * _h(k, 3), 0), (6.0 + 2 * _h(k, 5), 1)):
                if v.d(xx, y) > 1.0: trees.append((v.d(xx, y), xx, y, k, sd))
        for (d, xx, y, k, sd) in sorted(trees, reverse=True):
            bx, by = v.p(xx, 0.0, y)
            draw_tree(pen, bx, by, (6.0 + 3 * _h(k, 7)) * v.s(xx, y), 0.0, 800 + k * 2 + sd, 0.0, '#07090c', None, 4)
    gl = Layer(30.0, ground, 'road_ground', blur=None); gl.order = ORDER_SHELL - 1.0
    dyn = [gl]
    if callable(his_pos):
        amb, steady, var = main.lights(o)
        def hb(pen, v_, t):
            x, y = his_pos(t)
            draw_parts(pen, v_, bu_bus_parts(x, y, 0.0, 'his', 0.0))
            bu_bus_emit(pen, v_, x, y, 0.0, 'his', _bu_lv(his_win, 392, t), 0.0, 0.0, 0.0, _bu_lv(brake, 393, t), G=0.0)
        hp0 = his_pos(0.0)
        dyn.append(live_layer('his_bus', v, (hp0[0], 1.5, hp0[1]), hb, amb, steady, var))
    sp = build_view('bu_road_' + view, v, main, o, grade='bu_road', dyn=dyn)
    sp._fx = bu_vhs_dirt(0.15, 0.05)
    return sp


_bcam('bu_road_side', 820, 520, 1.3, 9.0, -9.0, -90, _env(), 'beside the road: both buses side-on, the verge streaming past', 'road')
_bcam('bu_road_ahead', 760, 500, 1.7, -1.6, 9.0, 180, _env(), 'low behind bus 9: his dark bus ahead on the empty road', 'road')
_bcam('bu_road_behind', 760, 500, 1.6, -2.6, -10.0, 8, _env(), "ahead of bus 9 looking back: Grandma's headlights, his amber windows following", 'road')
_bcam('bu_road_window', 1300, 520, 2.1, 2.6, -16.5, -112, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.08)), "close on his driver's window (the head turned backwards)", 'road')


# ====================================================================================================== Larkfield Elementary, 2:57 AM
BU_SCH_HIS = (-5.0, -3.4, 90.0)          # his bus at the doors, facing +x, its door toward the lot (-y)
BU_SCH_B9 = (-2.0, -16.5, 180.0)         # bus 9 behind Mina, nose toward his door, headlights on her
BU_SCH_FLAG = (9.0, -8.5)
BU_SCH_CLOCK = (0.0, 4.4)                # the clock over the doors (x, Y) on the facade y 0


def _school_facade(pen, v, o):
    """The school: two storeys of brick, rows of dark windows, the entrance (double glass doors under a canopy), the
    clock above the doors, LARKFIELD ELEMENTARY in letters, the green EXIT light (its glow is live)."""
    F = wall_face((-24.0, 0.0), (24.0, 0.0), 0.0, 7.6)
    if not v.visible(F.O, F.n): return
    def art(p_, W, H):
        p_.fill(rect(0, 0, W, H), '#7a4a3a'); pat(p_, W, H, 'brick', '#3a2018', 120)
        p_.texture(rect(0, 0, W, H), 'grunge', 0.5, 'overlay', 2.0)
        for row, (Yb, Yt) in enumerate(((0.95, 2.7), (4.6, 6.4))):
            for k in range(-9, 10):
                x = 2400 + k * 240
                if row == 0 and abs(k) <= 1: continue
                r = rect(x - 85, H - Yt * 100, 170, (Yt - Yb) * 100)
                p_.fill(r, '#0c1018'); p_.line(r, 3.0, '#c8c0b0')
                for j in (1, 2): p_.fill(rect(x - 85 + j * 170 / 3 - 2, H - Yt * 100, 4, (Yt - Yb) * 100), '#c8c0b0')
                p_.linear(r, x - 85, H - Yt * 100, x + 85, H - Yb * 100, [(0, '#ffffff', 0), (0.5, '#8a9ac8', 25), (1, '#ffffff', 0)])
        p_.fill(rect(2400 - 170, H - 300, 340, 300), '#c8c0b0')
        for xx in (2400 - 150, 2400 + 4):
            p_.fill(rect(xx, H - 280, 146, 280), '#0a0c10'); p_.line(rect(xx, H - 280, 146, 280), 3.0, '#8a8a88')
            p_.fill(rect(xx + 60, H - 150, 26, 6), '#b8b8b0')
        p_.fill(rect(2400 - 420, H - 3.6 * 100, 840, 50), '#e8e0d0')
        btext(p_, 'LARKFIELD ELEMENTARY', 2400, H - 3.6 * 100 + 40, 'serif_b', 40, '#2a2a2a', 240, 'center', spacing=0.08)
    draw_face(pen, v, F, art, '#7a4a3a', ao=False, lw=1.2)
    # the canopy over the doors
    cq = [(-3.0, 3.05, -2.2), (3.0, 3.05, -2.2), (3.0, 3.05, 0.0), (-3.0, 3.05, 0.0)]
    path = v.poly3(cq)
    if not path.isEmpty(): pen.fill(path, lit('#3a3e44', (0, 3.0, -1.1), (0, -1 if v.cam_h < 3.05 else 1, 0))); pen.line(path, 1.0)
    fq = v.poly3([(-3.0, 3.25, -2.2), (3.0, 3.25, -2.2), (3.0, 2.95, -2.2), (-3.0, 2.95, -2.2)])
    if not fq.isEmpty(): pen.fill(fq, lit('#5a5e64', (0, 3.1, -2.2), (0, 0, -1))); pen.line(fq, 1.0)
    for xx in (-2.8, 2.8):
        pen.seg(v.p(xx, 0.0, -2.1), v.p(xx, 3.0, -2.1), max(1.2, 0.08 * v.s(xx, -2.1)), lit('#6a6e74', (xx, 1.5, -2.1), None))
    bu_school_clock(pen, v, o.get('clock', (2, 57)))
    # the roof line
    rq = v.poly3([(-24.0, 7.6, 0.0), (24.0, 7.6, 0.0), (24.0, 8.0, -0.3), (-24.0, 8.0, -0.3)])
    if not rq.isEmpty(): pen.fill(rq, lit('#3a3a3e', (0, 7.8, -0.1), (0, 0, -1))); pen.line(rq, 1.0)


def bu_school_clock(pen, v, hm=(2, 57), x=None, Y=None, r=0.42):
    """The round school clock in a black case on the facade (hm = (h, m) or (h, m, s))."""
    x = BU_SCH_CLOCK[0] if x is None else x; Y = BU_SCH_CLOCK[1] if Y is None else Y
    if v.d(x, -0.05) < 0.3: return
    cx, cy = v.p(x, Y, -0.06); s = v.s(x, -0.06)
    R = r * s
    pen.fill(oval(cx, cy, R * 1.12), '#1a1a1a'); pen.fill(oval(cx, cy, R), lit('#f2eee2', (x, Y, -0.06), (0, 0, -1))); pen.line(oval(cx, cy, R), 1.0)
    for k in range(12):
        a = math.radians(k * 30)
        pen.seg((cx + math.sin(a) * R * 0.82, cy - math.cos(a) * R * 0.82), (cx + math.sin(a) * R * 0.95, cy - math.cos(a) * R * 0.95), max(1.0, R * 0.05), '#1a1a1a')
    h, m = hm[0], hm[1]; sec = hm[2] if len(hm) > 2 else 0
    am = math.radians((m + sec / 60.0) * 6); ah = math.radians(((h % 12) + m / 60.0) * 30)
    pen.seg((cx, cy), (cx + math.sin(ah) * R * 0.5, cy - math.cos(ah) * R * 0.5), max(1.5, R * 0.08), '#1a1a1a')
    pen.seg((cx, cy), (cx + math.sin(am) * R * 0.8, cy - math.cos(am) * R * 0.8), max(1.2, R * 0.05), '#1a1a1a')
    pen.fill(oval(cx, cy, R * 0.06), '#a01a12')


def _flagpole(pen, v, t=0.0, wind=1.0):
    x, y = BU_SCH_FLAG
    if v.d(x, y) < 0.5: return
    s = v.s(x, y)
    b_, t_ = v.p(x, 0.0, y), v.p(x, 9.0, y)
    pen.seg(b_, t_, max(1.4, 0.1 * s) + 2, LINE); pen.seg(b_, t_, max(1.2, 0.1 * s), lit('#b8bcc4', (x, 4.0, y), None))
    pen.fill(oval(t_[0], t_[1], max(1.5, 0.09 * s)), '#d8c890')
    sw = math.sin(t * 2.3) * 0.12 * wind + math.sin(t * 5.1) * 0.04 * wind
    pts = [v.p(x + 0.07, 9.0, y)] + [v.p(x + 0.07 + sw * math.sin(math.pi * f), 9.0 - 8.0 * f, y + 0.02) for f in np.linspace(0.05, 1.0, 10)]
    pen.line(poly(pts, False), max(0.8, 0.015 * s), '#d8d4c8')
    cl = v.p(x + 0.07 + sw, 1.2, y + 0.02)
    pen.fill(oval(cl[0], cl[1], max(1.0, 0.03 * s)), '#c8c8c0')                    # the clip that clinks on the pole
    pen.fill(rect(b_[0] - 0.4 * s, b_[1] - 0.1 * s, 0.8 * s, 0.1 * s), lit('#8a8a88', (x, 0.05, y), (0, 1, 0)))


class BuSchool(Room):
    name = 'school'
    poly = [(-60.0, -60.0), (60.0, -60.0), (60.0, 0.0), (-60.0, 0.0)]

    def lights(self, o):
        amb = '#283458'
        steady = [Lamp(kind='dir', c='#8a9ad8', k=0.45, d=_norm3((0.3, -0.8, 0.6))), Lamp(-16.0, 7.0, -14.0, 22.0, BU_SODIUM, 1.4, (1.0, 0.6, 0.2), fall=1.3)]
        b = BU_SCH_HIS; th = math.radians(b[2])
        his_in = [Lamp(b[0], 1.8, b[1] - 2.0, 7.0, BU_AMBER, 1.6, (0.6, 1.0, 0.4), fall=1.3), Lamp(-2.0, 1.2, -5.2, 3.5, BU_AMBER, 1.4 * _static(o.get('his_door', 1.0), 1.0), fall=1.4)]
        b9 = BU_SCH_B9
        heads9 = [Lamp(b9[0], 0.9, b9[1] + 8.0, 12.0, '#fff2d6', 1.8, (1.0, 1.0, 0.5), fall=1.25)]
        exitL = [Lamp(0.0, 2.8, -0.5, 3.0, '#60ff90', 0.6, fall=1.6)]
        police = [Lamp(4.0, 1.5, -18.0, 18.0, '#4a6aff', 1.4, fall=1.2)]
        var = [('his_in', his_in, _kfn(o.get('his_win', 1.0) if o.get('his', True) else 0.0, 501)), ('heads9', heads9, _kfn(o.get('heads9', 1.0), 502)),
               ('exit', exitL, _kfn(1.0, 503)), ('police', police, o.get('police_fn') or _kfn(0.0, 504))]
        return amb, steady, var

    def shell(self, pen, v, o):
        dr_sky(pen, v, 'night'); dr_far_ring(pen, v, 'night', cx=0.0, cy=-10.0, G=0.0)
        with lighting(*_bu_ext_light('night')):
            draw_face(pen, v, floor_face(-90.0, 90.0, -90.0, 0.0, 0.0), lambda p_, W, H: (p_.texture(rect(0, 0, W, H), 'asphalt', 0.6, 'overlay', 1.6),
                      [p_.fill(rect(0, H - k * 600 - 180, W, 6), '#d8d8c8', 70) for k in range(1, 6)]), '#2a2c30', ao=False, line=False)
            draw_face(pen, v, floor_face(-24.0, 24.0, -2.2, 0.0, 0.15), lambda p_, W, H: [p_.fill(rect(k * 150, 0, 1.2, H), '#000000', 90) for k in range(int(W / 150))],
                      '#5a5c60', ao=False, line=False)
            _school_facade(pen, v, o)
            if v.d(-16.0, -14.0) > 0.8: dr_streetlight(pen, v, -16.0, -14.0, 1.0, arm=-1.0, G=0.0)
            for i, (x, y) in enumerate(((-30.0, -6.0), (28.0, -5.0), (34.0, -20.0), (-36.0, -24.0))):
                if v.d(x, y) > 1.0:
                    bx, by = v.p(x, 0.0, y); draw_tree(pen, bx, by, 8.0 * v.s(x, y), 0.0, 900 + i, 0.0, '#0a0e14', None, 5)

    def pieces(self, o):
        P = []
        if o.get('his', True):
            b = BU_SCH_HIS
            P.append(bu_bus_piece('his_bus', b[0], b[1], b[2], 'his', G=0.0, door=o.get('his_door', 1.0) if not callable(o.get('his_door', 1.0)) else 0.0,
                                  broom=o.get('broom9', 0.0), bend=o.get('bend', 0.0), crack=o.get('crack', 0.0), cobweb=True, occupants=[bu_bus_seat_pt(b)]))
        if o.get('bus9', True):
            b = BU_SCH_B9
            P.append(bu_bus_piece('bus9', b[0], b[1], b[2], 'bus9', G=0.0, door=1.0, mirror_r=False, occupants=[bu_bus_seat_pt(b)]))
        if o.get('clipboard'):
            P.append(Piece('clipboard', (-2.2, 0.0, -5.3), lambda pen, v: _clipboard_ground(pen, v, -2.2, -5.3)))
        if o.get('tail'):
            P.append(Piece('tail', (-1.5, 0.0, -5.6), lambda pen, v: _tail_ground(pen, v, -1.5, -5.6)))
        P.append(Piece('flagpole', (BU_SCH_FLAG[0], 4.0, BU_SCH_FLAG[1]), lambda pen, v: _flagpole(pen, v, 0.0, 0.0), block=_circ(BU_SCH_FLAG[0], BU_SCH_FLAG[1], 0.4)))
        return P

    def glows(self, v, o):
        G = []
        if o.get('his', True):
            b = BU_SCH_HIS; kw = _kfn(o.get('his_win', 1.0), 501)
            G.append(('his_glow', (b[0], 1.5, b[1]), lambda pen, t: bu_bus_emit(pen, v, b[0], b[1], b[2], 'his', kw(t), 0.0, 0.0, 0.0, 0.0, G=0.0)))
        if o.get('bus9', True):
            b = BU_SCH_B9; kh = _kfn(o.get('heads9', 1.0), 502)
            G.append(('b9_glow', (b[0], 1.5, b[1]), lambda pen, t: bu_bus_emit(pen, v, b[0], b[1], b[2], 'bus9', 0.0, kh(t), 0.0, 0.0, 0.0, G=0.0)))
        def exitg(pen, t):
            if v.d(0.0, -0.05) < 0.3: return
            x, y = v.p(0.0, 2.85, -0.05); s = v.s(0.0, -0.05)
            pen.fill(rrect(x - 0.18 * s, y - 0.07 * s, 0.36 * s, 0.14 * s, 0.02 * s), '#2a8a4a'); btext(pen, 'EXIT', x, y + 0.04 * s, 'sans_b', 0.1 * s, '#c8ffd8', 250, 'center')
            pen.glow(x, y, 0.5 * s, '#60ff90', 70)
        G.append(('exit_glow', (0.0, 2.85, -0.05), exitg))
        return G

    def spots(self, v, o):
        S = {}
        b = BU_SCH_HIS
        S.update(bu_bus_spots(v, 'his_', b[0], b[1], b[2], 0.0, 'his'))
        b9 = BU_SCH_B9
        S.update(bu_bus_spots(v, 'b9_', b9[0], b9[1], b9[2], 0.0, 'bus9'))
        d = S['his_door']
        S['bottom_step'] = _mk_spot(v, 'bottom_step', d.X, d.Yp + 0.35, 0.0, 'stand', 'Mina at the bottom step of his bus (facing it, +y); she never climbs', face=(0, 1))
        S['behind_mina'] = _mk_spot(v, 'behind_mina', d.X + 0.9, d.Yp - 1.8, 0.0, 'stand', 'Grandma behind Mina (the broom), facing the door', face=(-0.3, 1))
        S['clock'] = _mk_spot(v, 'clock', BU_SCH_CLOCK[0], -0.06, BU_SCH_CLOCK[1], 'point', 'the school clock over the doors')
        S['flag_rope'] = _mk_spot(v, 'flag_rope', BU_SCH_FLAG[0] + 0.07, BU_SCH_FLAG[1], 1.2, 'point', 'the flag rope clip (clinking)')
        S['lot_kneel'] = _mk_spot(v, 'lot_kneel', -1.4, -6.2, 0.0, 'kneel', 'Grandma kneeling to Theo in the lot', face=(0, 1))
        S['asphalt'] = _mk_spot(v, 'asphalt', -2.2, -5.3, 0.0, 'surface', 'the asphalt where the clipboard clatters down')
        return S


def bu_school(view='wide', clock=(2, 57), his=True, his_door=1.0, his_win=1.0, heads9=1.0, bus9=True, broom9=0.0, bend=0.0, crack=0.0, clipboard=False,
              tail=False, police=False, wind=1.0, **kw):
    """Larkfield Elementary at 2:57 AM: view 'wide' | 'doors' (his bus parked at the doors, cobwebs in the wipers) |
    'clock' | 'flag' (the flagpole, the rope clinking) | 'reverse' (from his door back to the lot: bus 9's headlights) |
    'lot' (after: the empty lot, the clipboard on the asphalt). clock (h, m[, s]); his (his bus there); his_door 0..1;
    his_win (amber); heads9 (bus 9's headlights on Mina); broom9 / bend / crack (Grandma's broom in his doors); clipboard,
    tail (the torn dinosaur tail) on the asphalt; police (blue lights sweeping the lot); wind (the flag rope). The
    bottom-step view up into the bus is ST.bu_bus_in('step_out')."""
    o = dict(clock=clock, his=his, his_door=his_door, his_win=his_win, heads9=heads9, bus9=bus9, broom9=broom9, bend=bend, crack=crack, clipboard=clipboard, tail=tail)
    if police: o['police_fn'] = lambda t: 0.5 + 0.5 * math.sin(t * 7.0)
    o.update(kw)
    v = cam('bu_sch_' + view)
    main = BuSchool()
    amb, steady, var = main.lights(o)
    dyn = [live_layer('flag', v, (BU_SCH_FLAG[0], 4.0, BU_SCH_FLAG[1] + 0.01), lambda pen, v_, t: _flagpole(pen, v_, t, wind), amb, steady, var)]
    if his and callable(his_door):
        b = BU_SCH_HIS; q = bu_bus_door_quad(b[0], b[1], b[2], 0.0)
        dyn.append(live_layer('his_door', v, q[1], lambda pen, v_, t: bu_bus_door(pen, v_, b[0], b[1], b[2], 'his', his_door(t), 0.0, broom=_bu_lv(broom9, 511, t), bend=_bu_lv(bend, 512, t),
                                                                              crack=_bu_lv(crack, 513, t)), amb, steady, var, order=v.d(q[1][0], q[1][2]) - 0.05))
    if police:
        def pol(pen, t):
            for k in range(3):
                ph = t * 3.0 + k * 2.1
                x = 960 + 900 * math.sin(ph); pen.glow(x, 700, 600, '#3a5aff' if k % 2 == 0 else '#ff3a3a', 40 + 30 * max(0.0, math.sin(ph * 1.7)))
        pl = Layer(0.5, pol, 'police', blur=None); pl.order = 0.1; dyn.append(pl)
    sp = build_view('bu_sch_' + view, v, main, o, grade='bu_amber' if his else 'bu_ext', dyn=dyn)
    if his: sp._fx = bu_vhs_dirt(0.18, 0.06)
    return sp


def _clipboard_ground(pen, v, x, y):
    q = v.poly3([(x - 0.12, 0.012, y - 0.17), (x + 0.12, 0.012, y - 0.17), (x + 0.12, 0.012, y + 0.17), (x - 0.12, 0.012, y + 0.17)])
    if q.isEmpty(): return
    pen.fill(q, lit('#8a6a3a', (x, 0.0, y), (0, 1, 0))); pen.line(q, 1.0)
    q2 = v.poly3([(x - 0.1, 0.014, y - 0.13), (x + 0.1, 0.014, y - 0.13), (x + 0.1, 0.014, y + 0.15), (x - 0.1, 0.014, y + 0.15)])
    if not q2.isEmpty(): pen.fill(q2, lit('#f2ecd8', (x, 0.0, y), (0, 1, 0)))
    for k in range(7):
        a = (x - 0.08, 0.015, y - 0.1 + k * 0.035); b_ = (x + 0.06, 0.015, y - 0.1 + k * 0.035)
        pen.seg(v.p(*a), v.p(*b_), 0.8, '#3a3a5a', 160)


def _tail_ground(pen, v, x, y):
    if v.d(x, y) < 0.3: return
    px, py = v.p(x, 0.03, y); s = v.s(x, y)
    tl = smooth([(px - 0.18 * s, py), (px, py - 0.04 * s), (px + 0.2 * s, py - 0.01 * s), (px + 0.02 * s, py + 0.03 * s)], True, 0.8)
    pen.fill(tl, lit('#4aa06a', (x, 0.03, y), None)); pen.line(tl, 1.0)
    for k in range(3):
        cx = px - 0.08 * s + k * 0.08 * s
        pen.fill(poly([(cx - 0.02 * s, py - 0.02 * s), (cx, py - 0.07 * s), (cx + 0.02 * s, py - 0.02 * s)]), '#e88a3a')


_bcam('bu_sch_wide', 760, 520, 1.7, 9.0, -30.0, -14, _env(f=(1.0, 2.2)), 'Larkfield Elementary at 2:57 AM: the dark school, the flagpole, his bus at the doors, bus 9 pulling in', 'school')
_bcam('bu_sch_doors', 900, 520, 1.6, 3.4, -12.5, -32, _env(), 'his bus parked at the doors (cobwebs in the wipers), its door open, amber', 'school')
_bcam('bu_sch_clock', 1700, 560, 2.0, 0.0, -7.0, 0, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.08)), 'the school clock over the doors', 'school', pitch=-18.0)
_bcam('bu_sch_flag', 900, 560, 1.6, 6.0, -15.0, 22, _env(), 'the flagpole and its clinking rope', 'school', pitch=-14.0)
_bcam('bu_sch_reverse', 900, 520, 1.5, -2.2, -5.0, 176, _env(), "from his door back across the lot: bus 9's headlights, Grandma", 'school')
_bcam('bu_sch_lot', 900, 500, 1.55, 1.2, -11.0, -14, _env(), 'after: the empty lot, the clipboard on the asphalt', 'school')


# ====================================================================================================== Theo's stop
class BuTheo(Room):
    """Theo's stop, before dawn: a small one-storey house (dark), its porch light that finally comes on."""
    name = 'theo'
    poly = [(-40.0, -40.0), (40.0, -40.0), (40.0, 0.0), (-40.0, 0.0)]

    def lights(self, o):
        return '#2a3458', [Lamp(kind='dir', c='#8a9ad8', k=0.4, d=_norm3((0.3, -0.8, 0.5)))], [('porch', [Lamp(0.6, 2.0, -0.6, 7.0, '#ffc888', 1.8, fall=1.4)], _kfn(o.get('porch', 0.0), 521))]

    def shell(self, pen, v, o):
        dr_sky(pen, v, 'night'); dr_far_ring(pen, v, 'night', cx=0.0, cy=0.0, G=0.0)
        with lighting(*_bu_ext_light('night')):
            draw_face(pen, v, floor_face(-90.0, 90.0, -90.0, 20.0, 0.0), lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'grunge', 0.6, 'overlay', 5.0), '#1c2a24', ao=False, line=False)
            draw_face(pen, v, floor_face(-90.0, 90.0, -16.0, -9.5, -0.1), lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'asphalt', 0.6, 'overlay', 1.6), '#24262c', ao=False, line=False)
            draw_face(pen, v, floor_face(0.2, 1.0, -9.5, -1.2, 0.005), lambda p_, W, H: None, '#5a5c60', ao=False, line=False)
            for (x0, x1, c) in ((-26.0, -16.0, '#8a8a7a'), (16.0, 26.0, '#9a9488')):
                dr_neighbour(pen, v, x0, x1, 0.0, 9.0, 'night', seed=int(x0), G=0.0, c=c)
            dr_neighbour(pen, v, -5.0, 6.0, 0.0, 8.0, 'night', seed=77, G=0.0, c='#a8b4c0')
            for (px, py) in ((0.1, -1.2), (1.1, -1.2)):
                draw_box(pen, v, Box(px, py, 0.1, 0.1, 0.0, 2.4, 0), {'all': '#d8d4c8'}, lw=0.8)
            q = v.poly3([(-0.2, 2.45, -1.4), (1.4, 2.45, -1.4), (1.4, 2.7, 0.0), (-0.2, 2.7, 0.0)])
            if not q.isEmpty(): pen.fill(q, lit('#3a3a40', (0.6, 2.6, -0.7), _norm3((0, 0.9, -0.4)))); pen.line(q, 1.0)
            d = v.poly3([(0.15, 2.05, -0.02), (1.05, 2.05, -0.02), (1.05, 0.0, -0.02), (0.15, 0.0, -0.02)])
            if not d.isEmpty(): pen.fill(d, lit('#3a5a7a', (0.6, 1.0, -0.02), (0, 0, -1))); pen.line(d, 1.0)

    def glows(self, v, o):
        kp = _kfn(o.get('porch', 0.0), 521)
        def g(pen, t):
            k = kp(t)
            if v.d(1.25, -0.06) < 0.3: return
            x, y = v.p(1.25, 1.95, -0.06); s = v.s(1.25, -0.06)
            pen.fill(rrect(x - 0.06 * s, y - 0.1 * s, 0.12 * s, 0.2 * s, 0.02 * s), mix('#2a2a24', '#fff0c0', k)); pen.line(rrect(x - 0.06 * s, y - 0.1 * s, 0.12 * s, 0.2 * s, 0.02 * s), 1.0)
            if k > 0.01:
                pen.glow(x, y, 1.8 * s, '#ffc070', 120 * k); pen.glow(x, y, 0.2 * s, '#ffffff', 220 * k)
                gx, gy = v.p(0.6, 0.0, -1.2); pen.ellipse_glow(gx, gy, 2.0 * s, 0.6 * s, '#ffc070', 70 * k)
        return [('porch_light', (1.25, 1.95, -0.1), g)]

    def spots(self, v, o):
        return {'porch_light': _mk_spot(v, 'porch_light', 1.25, -0.06, 1.95, 'point', "Theo's porch light"),
                'walk': _mk_spot(v, 'walk', 0.6, -4.0, 0.0, 'stand', 'Theo on his front walk, going home', face=(0, 1)),
                'door': _mk_spot(v, 'door', 0.6, -0.5, 0.0, 'stand', 'at his front door', face=(0, 1))}


def bu_theo_stop(view='house', porch=0.0, **kw):
    """Theo's stop before dawn (bus 9 waits): view 'house' (from bus 9's open door: the dark house; porch = the light
    coming on, level spec) | 'wide'."""
    o = dict(porch=porch); o.update(kw)
    v = cam('bu_theo_' + view)
    sp = build_view('bu_theo_' + view, v, BuTheo(), o, grade='bu_ext')
    if view == 'house':
        def frame(pen, t):
            pen.fill(minus(rect(-400, -300, 2720, 1700), rect(330, -300, 1260, 1700)), '#16120c')
            for xx in (330, 1590):
                pen.fill(rect(xx - 14, -300, 28, 1700), '#2a2418')
            pen.fill(rect(-400, 960, 2720, 400), '#1a160e')
            pen.fill(rect(330, 930, 1260, 30), '#d8b020', 200)
        lay = Layer(0.3, frame, 'bus9_door_frame', blur=6); lay.order = 0.05
        sp = sp.add(lay)
    return sp


_bcam('bu_theo_house', 900, 520, 1.9, 0.6, -12.6, 0, _env(), "Theo's stop from bus 9's open door: the dark house, the porch light", 'theo')
_bcam('bu_theo_wide', 760, 500, 1.6, -6.0, -15.0, 22, _env(), "Theo's street, bus 9 waiting", 'theo')


# ====================================================================================================== 1994: the tape and the classroom
BU_KIDS94 = [('AMY', 'LINCOLN', '4', '#d84a6a'), ('MARCUS', 'LARKFIELD', '9', '#4a7ad8'), ('JEN', 'OAKDALE', '2', '#e8a020'),
             ('DEV', 'LARKFIELD', '7', '#4aa06a'), ('KATIE', 'LINCOLN', '4', '#a85ad8'), ('', '', '', '#e8c020')]   # the last: a small figure in a yellow raincoat


def _studio94(pen, t=0.0, view='full', W=1920, H=1080):
    """'Ride Right with Mister Whistlestop!', Channel 6, 1994, as the tape shows it (flat, bright, cheap): the painted
    sky-and-road backdrop, the cardboard bus cutout, the RIDE RIGHT board, the teal riser, the kids' row with cards."""
    pen.linear(rect(-300, -200, W + 600, H + 400), 0, 0, 0, H, [(0, '#6ab8f0'), (0.6, '#a8dcff'), (1, '#c8ecff')])
    for (cx, cy, w) in ((300, 180, 260), (900, 120, 340), (1500, 210, 280)):
        pen.fill(union(oval(cx, cy, w * 0.5, w * 0.18), union(oval(cx - w * 0.25, cy + 10, w * 0.3, w * 0.14), oval(cx + w * 0.22, cy + 8, w * 0.28, w * 0.15))), '#ffffff', 235)
    pen.fill(oval(1700, 150, 90), '#ffe060'); pen.glow(1700, 150, 200, '#fff0a0', 120)
    pen.fill(poly([(-300, 640), (W + 300, 640), (W + 300, H + 300), (-300, H + 300)]), '#7ac85a')         # painted hills and road
    pen.fill(poly([(700, 640), (1220, 640), (1700, H + 300), (200, H + 300)]), '#5a5a62')
    for k in range(5): pen.fill(rect(950, 660 + k * 70 + k * k * 6, 20, 30 + k * 8), '#ffffff', 220)
    # the RIDE RIGHT board
    pen.fill(rrect(90, 250, 560, 240, 20), '#ffffff'); pen.line(rrect(90, 250, 560, 240, 20), 8, '#d8302a')
    btext(pen, 'RIDE', 370, 345, 'head', 96, '#d8302a', 255, 'center'); btext(pen, 'RIGHT!', 370, 455, 'head', 96, '#2a5ad8', 255, 'center')
    oc = [(560 + 46 * math.cos(math.radians(22.5 + 45 * k)), 300 + 46 * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
    pen.fill(poly(oc), '#d8302a'); btext(pen, 'STOP', 560, 311, 'sans_b', 26, '#ffffff', 255, 'center')
    # the cardboard bus cutout (flat, painted, a little crooked, its prop stand showing)
    pen.cv.save(); pen.cv.translate(1180, 470); pen.cv.rotate(-1.5)
    bus = rrect(0, 0, 640, 240, 30)
    pen.fill(bus, '#f4c020'); pen.line(bus, 6, '#3a2a10')
    for k in range(6): pen.fill(rrect(40 + k * 92, 30, 70, 70, 8), '#7ac8f0'); pen.line(rrect(40 + k * 92, 30, 70, 70, 8), 3, '#3a2a10')
    pen.fill(rect(0, 130, 640, 14), '#2a2a2a'); btext(pen, 'SCHOOL BUS', 320, 200, 'head', 40, '#2a2a2a', 255, 'center')
    for x in (130, 510): pen.fill(oval(x, 245, 48), '#2a2a2a'); pen.fill(oval(x, 245, 20), '#c8c8c8')
    pen.cv.restore()
    pen.fill(poly([(1250, 720), (1270, 720), (1300, 860), (1280, 860)]), '#b89a6a')
    # the riser
    pen.fill(rect(-300, 820, W + 600, 300), '#2ab8b0'); pen.fill(rect(-300, 820, W + 600, 18), '#1a8a84')
    for k in range(14): pen.fill(_star5(60 + k * 140, 900 + (k % 2) * 60, 18), '#ffe060', 230)
    # the kids' row: cards held up (only the yellow raincoat's card is unreadable)
    if view in ('full', 'kids'):
        for i, (nm, sch, bus_, c) in enumerate(BU_KIDS94):
            x = 220 + i * 300; base = H + 40
            small = nm == ''
            hh = 300 if not small else 250
            pen.fill(rrect(x - 70, base - hh, 140, hh + 60, 40), c)
            pen.fill(oval(x, base - hh - 40, 52), '#c89070' if i % 2 else '#8a5a3a')
            if small:
                pen.fill(poly([(x - 66, base - hh - 40), (x, base - hh - 110), (x + 66, base - hh - 40)]), '#e8c020')
            card = rrect(x - 105, base - hh + 10, 210, 140, 8)
            pen.fill(card, '#ffffff'); pen.line(card, 3, '#2a2a2a')
            if not small:
                btext(pen, nm, x, base - hh + 60, 'kid', 38, '#1a1a1a', 255, 'center')
                btext(pen, sch, x, base - hh + 98, 'kid', 24, '#3a3a8a', 255, 'center')
                btext(pen, 'BUS ' + bus_, x, base - hh + 132, 'kid', 26, '#c82a2a', 255, 'center')
            else:
                for k in range(3): pen.line(smooth([(x - 80, base - hh + 50 + k * 30), (x - 20, base - hh + 42 + k * 30), (x + 70, base - hh + 55 + k * 30)], False), 4, '#5a5a6a', 160)
            pen.fill(rect(x - 100, base - hh + 135, 22, 30), '#e8b090'); pen.fill(rect(x + 78, base - hh + 135, 22, 30), '#e8b090')
    # the Channel 6 bug and the camcorder-ish date
    pen.fill(oval(1810, 990, 44), '#ffffff', 200); btext(pen, '6', 1810, 1010, 'head', 56, '#2a5ad8', 230, 'center')


def _star5(x, y, r):
    return poly([(x + (r if k % 2 == 0 else r * 0.45) * math.cos(math.radians(-90 + k * 36)), y + (r if k % 2 == 0 else r * 0.45) * math.sin(math.radians(-90 + k * 36))) for k in range(10)])


def _title94(pen, t=0.0, W=1920, H=1080):
    pen.linear(rect(-300, -200, W + 600, H + 400), 0, 0, 0, H, [(0, '#2a5ad8'), (1, '#1a2a8a')])
    for k in range(24):
        a = math.radians(k * 15 + t * 10)
        pen.fill(poly([(960, 520), (960 + 1800 * math.cos(a), 520 + 1800 * math.sin(a)), (960 + 1800 * math.cos(a + 0.13), 520 + 1800 * math.sin(a + 0.13))]), '#ffffff', 30)
    btext(pen, 'Ride Right', 960, 430, 'script', 180, '#ffe060', 255, 'center')
    btext(pen, 'with', 960, 540, 'head', 70, '#ffffff', 255, 'center')
    btext(pen, 'MISTER WHISTLESTOP!', 960, 680, 'head', 120, '#ffffff', 255, 'center', spacing=0.04)
    oc = [(1660 + 70 * math.cos(math.radians(22.5 + 45 * k)), 260 + 70 * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
    pen.fill(poly(oc), '#d8302a'); pen.line(poly(oc), 5, '#ffffff'); btext(pen, 'STOP', 1660, 277, 'sans_b', 40, '#ffffff', 255, 'center')
    pen.fill(oval(260, 880, 70), '#ffffff'); btext(pen, '6', 260, 910, 'head', 90, '#2a5ad8', 255, 'center')
    btext(pen, 'A CHANNEL 6 SAFETY SPECIAL  ·  1994', 960, 900, 'sans_b', 40, '#c8d8ff', 230, 'center')


def bu_tape94(view='full', track=0.3, vhs=True, k=1.0):
    """The 1994 tape full frame (the push into the CRT lands here): view 'full' (the studio: anchor 'host' for
    Whistlestop '94, the kids' row, the cardboard bus) | 'kids' (the cards held up; the small raincoat at the end) |
    'title' (the title card). Tape look = engine fx['vhs'] (track 0..1 tracking noise); grade 'bu_vhs94'."""
    if view == 'title':
        L = [Layer(1.0, lambda pen, t: _title94(pen, t), 'title94', blur=0, bounds=(-300, -200, 2220, 1280))]
    else:
        def draw(pen, t, view=view):
            if view == 'kids':
                pen.cv.save(); pen.cv.translate(960, 760); pen.cv.scale(1.55, 1.55); pen.cv.translate(-960, -900)
                _studio94(pen, t, 'kids'); pen.cv.restore()
            else:
                _studio94(pen, t, 'full')
        L = [Layer(1.0, draw, 'studio94', cache=_key('bu', 'studio94', view), blur=0, bounds=(-300, -200, 2220, 1280))]
    a = {'host': Anchor(860, 860, 1.0, 290.0, 'Whistlestop \'94 standing on the riser (feet; a 2.44 m figure at 290 px per metre)'),
         'kids_row': Anchor(960, 1000, 1.0, 290.0, 'the kids holding up their cards')}
    fx = (lambda t: {'vhs': dict(t=t, k=k, track=track, bezel=0.0)}) if vhs else None
    return SetPiece('bu_tape94_' + view, L, a, {}, lens=None, grade='bu_vhs94', focus=1.0, dof=0.0, cover=(-300, -200, 2220, 1280), fx=fx,
                    info={'cam_env': dict(x=(880, 1040), y=(480, 600), zoom=(1.0, 1.5), f=(1.0, 1.4))})


BU_CART = Box(5.6, 1.4, 0.62, 0.5, 0.0, 1.32, 200)
BU_TV94 = Box(5.6, 1.42, 0.56, 0.5, 1.32, 1.8, 200)


def _class_cfg(o):
    def lights(o):
        amb = '#5a4c40'
        blinds = Lamp(kind='win', c='#ffe0b0', k=0.7, soft=16.0, panes=_panes_x(1.0, 6.0, 0.9, 2.4, 0.0), d=_norm3((1.0, -0.3, 0.1)))
        return amb, [blinds], [('tv', [Lamp(BU_TV94.cx, 1.55, BU_TV94.cy + 0.6, 5.0, '#a8c8ff', 1.3, fall=1.3)], _kfn(o.get('tv', 1.0), 531))]
    def front(p_, W, H):
        p_.fill(rect(150, H - 230, 500, 130), '#2a4a3a'); p_.line(rect(150, H - 230, 500, 130), 4, '#8a6a3a')
        p_.texture(rect(150, H - 230, 500, 130), 'grunge', 0.5, 'overlay', 1.0)
        btext(p_, 'Tues. Sept. 13', 230, H - 200, 'kid', 14, '#e8e8e0', 220)
        btext(p_, 'BUS SAFETY DAY!', 400, H - 160, 'kid', 22, '#f4f0e0', 230, 'center')
        for k in range(26): p_.fill(rect(150 + k * 19.2, H - 270, 16, 20), ['#d84a4a', '#4a8ad8', '#e8c020', '#4aa06a'][k % 4]); btext(p_, chr(65 + k), 158 + k * 19.2, H - 254, 'sans_b', 12, '#ffffff', 230, 'center')
    def west(p_, W, H):
        for k in range(5):
            x = 100 + k * 100
            for j in range(14): p_.fill(rect(x - 45, H - 240 + j * 10.7, 90, 7), '#e8dcc0', 220)
    cfg = dict(name='class94', R=(0.0, 8.0, 0.0, 7.0), H=3.0, floor=dict(base='#c8c0a8', kind='tile', ink='#a8a088', seed=5),
               runs=_rect_runs((0.0, 8.0, 0.0, 7.0), {'west': [(0.0, 1.0, 0.0, 6.0, 0.9, 2.4)], 'east': [(8.0, 5.5, 8.0, 6.4, 0.0, 2.1)]}, None, {'front': front, 'west': west}),
               walls=dict(paper='#d8d0b8', ink=None, kind=None, wains=1.0, wcol='#8a9a8a', seed=5), ceil=dict(c='#e8e8e0'), lights=lights)
    def pieces(o):
        P = []
        for r in range(4):
            for c in range(4):
                x, y = 1.6 + c * 1.35, 3.0 + r * 1.0
                B = Box(x, y, 0.6, 0.45, 0.0, 0.66, 0)
                P.append(Piece('desk_%d_%d' % (r, c), (x, 0.4, y), (lambda B_: lambda pen, v: (draw_parts(pen, v, table_parts(B_, '#c8a878', leg='#6a6a6a', apron=0.0)),
                                                                                              draw_box(pen, v, Box(B_.cx, B_.cy + 0.38, 0.38, 0.36, 0.0, 0.4, 0), {'all': '#d85a3a'})))(B),
                               block=B.footprint()))
        def cart(pen, v):
            for Yb in (0.15, 0.7, 1.28):
                draw_box(pen, v, Box(BU_CART.cx, BU_CART.cy, 0.62, 0.5, Yb, Yb + 0.04, BU_CART.fa), {'all': '#2a2a30'}, lw=0.8)
            for (u, n) in ((-0.28, -0.22), (0.28, -0.22), (-0.28, 0.22), (0.28, 0.22)):
                P_ = BU_CART.at(u, n, 0.0)
                pen.seg(v.p(P_[0], 0.08, P_[2]), v.p(P_[0], 1.32, P_[2]), max(1.0, 0.02 * v.s(P_[0], P_[2])), '#3a3a40')
                pen.fill(oval(*v.p(P_[0], 0.04, P_[2]), max(1.0, 0.03 * v.s(P_[0], P_[2]))), '#101010')
            vc = Box(BU_CART.cx, BU_CART.cy, 0.42, 0.3, 0.74, 0.84, BU_CART.fa)
            draw_box(pen, v, vc, {'all': '#1a1a1a', 'front': dict(fill='#1a1a1a', art=lambda p_, W, H: (p_.fill(rect(6, 3, 18, 3), '#3aff6a'), btext(p_, '12:00', W - 10, H - 2, 'vhs', 5, '#3aff6a', 230, 'right')))}, lw=0.8)
            draw_box(pen, v, BU_TV94, {'all': '#3a3a3e', 'front': dict(fill='#3a3a3e', art=lambda p_, W, H: (p_.fill(rrect(5, 5, W - 16, H - 10, 6), '#0a0c10'),
                                                                                                             [p_.fill(oval(W - 6, 12 + k * 9, 2), '#8a8a8a') for k in range(3)]))}, lw=1.0)
        P.append(Piece('cart', (BU_CART.cx, 1.0, BU_CART.cy), cart, block=BU_CART.footprint()))
        return P
    cfg['pieces'] = pieces
    cfg['spots'] = lambda v, o: {'tv_screen': _mk_spot(v, 'tv_screen', BU_TV94.cx, BU_TV94.cy + 0.25, 1.56, 'point', 'the CRT screen (the push into the tape)'),
                                 'desk_front': _mk_spot(v, 'desk_front', 1.6, 3.38, 0.0, 'seat', 'a kid at a front desk', face=(0, -1), seat_Y=0.4)}
    return cfg


def _crt_content_layer(v, content, name='crt'):
    """Live: the tape playing on the cart's CRT (the 1920x1080 studio drawn into the projected screen, scanlines, glow)."""
    F = BU_TV94.faces()['front']
    W, H = F.W, F.H
    q = [F.pt(5, 5), F.pt(W - 11, 5), F.pt(W - 11, H - 5), F.pt(5, H - 5)]
    def draw(pen, t):
        path = v.poly3(q)
        if path.isEmpty(): return
        b = path.computeTightBounds()
        cv = pen.cv; cv.save(); cv.clipPath(path, skia.ClipOp.kIntersect, True)
        cv.translate(b.left(), b.top()); cv.scale(b.width() / 1920.0, b.height() / 1080.0)
        content(pen, t)
        cv.restore()
        cv.save(); cv.clipPath(path, skia.ClipOp.kIntersect, True)
        for k in range(int(b.height() / 3)): pen.fill(rect(b.left(), b.top() + k * 3, b.width(), 1.2), '#000000', 60)
        pen.radial(None, (b.left() + b.right()) / 2, (b.top() + b.bottom()) / 2, b.width() * 0.75, [(0, '#ffffff', 30), (0.7, '#000000', 0), (1, '#000000', 120)])
        cv.restore()
        pen.glow((b.left() + b.right()) / 2, (b.top() + b.bottom()) / 2, b.width() * 1.3, '#a8c8ff', 50)
    lay = Layer(max(0.3, v.d(BU_TV94.cx, BU_TV94.cy)), draw, name, blur=None)
    lay.order = v.d(BU_TV94.cx, BU_TV94.cy) - 0.3
    return lay


def bu_class94(view='cart', content='full', tv=1.0):
    """1994: a Larkfield classroom, lights off, blinds down, the rolling TV cart with the CRT playing the tape (content
    'full' | 'kids' | 'title'). view 'cart' (from the back over the empty desks) | 'tv' (closer: the push-in starts here)."""
    o = dict(tv=tv)
    v = cam('bu_class_' + view)
    sp = build_view('bu_class_' + view, v, BuBox(_class_cfg(o)), o, grade='bu_class',
                    outside=lambda pen, v_: pen.fill(rect(-800, -600, 3600, 2400), '#f8e8c8'))
    fn = (lambda pen, t: _title94(pen, t)) if content == 'title' else (lambda pen, t: _studio94(pen, t, content))
    sp = sp.add(_crt_content_layer(v, fn))
    sp._fx = lambda t: {'vhs': dict(t=t, k=0.25, curve=0.0, glass=0.0, scan=0.2, track=0.05, bezel=0.0, tube=False)}
    return sp


_bcam('bu_class_cart', 860, 500, 1.25, 3.4, 6.6, 150, _env(), '1994: the classroom from the back, the TV cart at the front playing the tape', 'class94')
_bcam('bu_class_tv', 1250, 520, 1.5, 5.25, 3.3, 172, _env(x=(900, 1020), y=(480, 580), zoom=(1.0, 1.6)), 'closer on the CRT (the push-in into the tape)', 'class94')


# ====================================================================================================== inserts
_IBGB = (-520, -420, 2960, 1920)


def _ibg_b(pen, c1, c2=None, vign=120):
    r = rect(*_IBGB)
    if c2 is None: pen.fill(r, c1)
    else: pen.linear(r, 0, _IBGB[1], 0, _IBGB[1] + _IBGB[3], [c1, c2])
    if vign: pen.radial(None, 960, 540, 1500, [(0, '#000000', 0), (0.55, '#000000', 0), (1, '#000000', vign)])


def _phone_frame(pen, x=960, y=540, w=560, h=1100, tilt=-3.0):
    pen.cv.save(); pen.cv.translate(x, y); pen.cv.rotate(tilt)
    body = rrect(-w / 2, -h / 2, w, h, 60)
    pen.fill(moved(body, 14, 22), '#000000', 110, blur=24)
    pen.fill(body, '#121216'); pen.line(body, 3, '#3a3a40')
    scr = rrect(-w / 2 + 18, -h / 2 + 18, w - 36, h - 36, 46)
    return scr


def _status(pen, x0, y0, w, bars=4, t=0.0):
    btext(pen, '11:52' if bars else '1:58', x0 + 40, y0 + 46, 'sans_b', 26, '#ffffff', 240)
    for k in range(4):
        hh = 8 + k * 6
        pen.fill(rect(x0 + w - 150 + k * 14, y0 + 48 - hh, 9, hh), '#ffffff', 240 if k < bars else 60)
    if not bars: btext(pen, 'No Service', x0 + w - 300, y0 + 46, 'sans', 22, '#ff8a7a', 240)
    pen.fill(rrect(x0 + w - 80, y0 + 28, 44, 20, 5), '#ffffff', 220)


def _chalkboard(pen, x, y, w, h, kid=True):
    """The first-day chalkboard photo: Sami grinning (gap-toothed) behind the little chalkboard sign."""
    pen.fill(rect(x, y, w, h), '#c8d8e0'); pen.fill(rect(x, y + h * 0.55, w, h * 0.45), '#8a7a6a')
    pen.fill(rect(x + w * 0.62, y, w * 0.38, h * 0.62), '#e8e0d0'); pen.fill(rect(x + w * 0.66, y + h * 0.06, w * 0.12, h * 0.4), BU_PAL['door'])
    if kid:
        cx = x + w * 0.5
        pen.fill(rrect(cx - w * 0.17, y + h * 0.36, w * 0.34, h * 0.6, 30), '#4aa06a')
        pen.fill(oval(cx, y + h * 0.27, w * 0.19, w * 0.19), '#4aa06a')                         # the dinosaur hood
        for k in range(5):
            bx_ = cx - w * 0.12 + k * w * 0.06; by_ = y + h * 0.27 - w * 0.17 + abs(k - 2) * w * 0.02
            pen.fill(poly([(bx_ - w * 0.02, by_), (bx_, by_ - w * 0.055), (bx_ + w * 0.02, by_)]), '#e88a3a')
        for sx in (-1, 1): pen.fill(oval(cx + sx * w * 0.13, y + h * 0.29, w * 0.022, w * 0.03), '#a06a46')
        hy, r = y + h * 0.29, w * 0.13
        pen.fill(oval(cx, hy, r), '#b07a52')
        pen.fill(inter(oval(cx, hy - r * 0.1, r * 1.05), rect(cx - 2 * r, hy - 2 * r, 4 * r, r * 1.25)), '#2a1a12')
        for sx in (-1, 1): pen.line(poly([(cx + sx * r * 0.55, hy - r * 0.32), (cx + sx * r * 0.2, hy - r * 0.38)], False), w * 0.006, '#2a1a12')
        for sx in (-1, 1): pen.fill(oval(cx + sx * w * 0.045, y + h * 0.27, w * 0.012), '#1a1a1a')
        sm = smooth([(cx - w * 0.06, y + h * 0.33), (cx, y + h * 0.37), (cx + w * 0.06, y + h * 0.33)], False)
        pen.fill(union(sm, rect(cx - w * 0.06, y + h * 0.325, w * 0.12, h * 0.008)), '#ffffff'); pen.fill(rect(cx - w * 0.008, y + h * 0.33, w * 0.016, h * 0.03), '#2a1010')
    bx, by, bw, bh = x + w * 0.2, y + h * 0.48, w * 0.6, h * 0.42
    pen.fill(rrect(bx - 8, by - 8, bw + 16, bh + 16, 6), '#a8784a'); pen.fill(rect(bx, by, bw, bh), '#24342c')
    lines = [('SAMI', 0.16), ('FIRST GRADE', 0.11), ('LARKFIELD ELEMENTARY', 0.085), ('BUS 9', 0.11), ('LARCH STREET', 0.095)]
    yy = by + bh * 0.2
    for (s_, sz) in lines:
        btext(pen, s_, bx + bw / 2, yy, 'kid', bh * sz, '#f4f2ea', 240, 'center'); yy += bh * (sz + 0.06)


def _bui_post(pen, t, show=2, hl=None, **kw):
    _ibg_b(pen, '#1a1820', '#0a0a10')
    scr = _phone_frame(pen)
    x0, y0, w, h = -262, -532, 524, 1064
    pen.cv.save(); pen.cv.clipPath(scr, skia.ClipOp.kIntersect, True)
    pen.fill(rect(x0, y0, w, h), '#ffffff'); _status_dark = None
    btext(pen, '11:52', x0 + 40, y0 + 46, 'sans_b', 26, '#1a1a1a', 240)
    pen.fill(oval(x0 + 60, y0 + 110, 26), '#e8a8b8'); btext(pen, 'mina', x0 + 100, y0 + 118, 'sans_b', 26, '#1a1a1a', 240)
    _chalkboard(pen, x0, y0 + 150, w, w * 1.05)
    yy = y0 + 150 + w * 1.05 + 46
    hp = smooth([(x0 + 40, yy - 10), (x0 + 50, yy - 22), (x0 + 62, yy - 12), (x0 + 74, yy - 22), (x0 + 84, yy - 10), (x0 + 62, yy + 10)], True)
    pen.fill(hp, '#e8304a')
    if show >= 1:
        btext(pen, '41 likes', x0 + 104, yy + 2, 'sans_b', 28, '#1a1a1a', 250)
        btext(pen, 'First day tomorrow!! So proud of this guy', x0 + 30, yy + 52, 'sans', 22, '#1a1a1a', 230)
    if show >= 2:
        cy = yy + 120
        if hl == 'comment': pen.fill(rect(x0, cy - 44, w, 90), '#fff2c0')
        pen.fill(oval(x0 + 56, cy, 30), '#5a5a5a')
        hat = poly([(x0 + 36, cy + 8), (x0 + 78, cy + 2), (x0 + 84, cy - 34), (x0 + 50, cy - 30)])
        pen.fill(hat, '#d9a928'); pen.line(hat, 1.2)
        pen.fill(poly([(x0 + 44, cy - 12), (x0 + 80, cy - 20), (x0 + 81, cy - 13), (x0 + 45, cy - 5)]), '#1a1a1a')
        btext(pen, 'ride.right.94', x0 + 100, cy - 6, 'sans_b', 22, '#1a1a1a', 240)
        btext(pen, 'Great smile!', x0 + 100, cy + 26, 'sans', 26, '#1a1a1a', 250)
    pen.cv.restore(); pen.cv.restore()


def _bui_comment(pen, t, **kw):
    _ibg_b(pen, '#f4f2ee', None, 60)
    cx, cy = 560, 540
    pen.fill(oval(cx, cy, 150), '#6a6a6a')
    pen.cv.save(); pen.cv.clipPath(oval(cx, cy, 150), skia.ClipOp.kIntersect, True)
    pen.cv.translate(cx, cy + 95); pen.cv.rotate(-12)
    hat = poly([(-62, 0), (62, 0), (54, -240), (-44, -240)])
    pen.fill(rrect(-105, -12, 210, 28, 10), '#b88a20'); pen.fill(hat, '#d9a928'); pen.line(hat, 3)
    for yb in (-80, -165):
        pen.fill(inter(hat, poly([(-120, yb + 36), (120, yb - 12), (120, yb - 40), (-120, yb + 8)])), '#1a1a1a')
    pen.cv.restore()
    btext(pen, 'ride.right.94', 780, 480, 'sans_b', 64, '#1a1a1a', 240)
    btext(pen, 'Great smile!', 780, 600, 'sans', 92, '#1a1a1a', 255)


def _bui_phone_call(pen, t, state='nobars', **kw):
    _ibg_b(pen, '#0e1018', '#05060a')
    scr = _phone_frame(pen, tilt=2.0)
    x0, y0, w, h = -262, -532, 524, 1064
    pen.cv.save(); pen.cv.clipPath(scr, skia.ClipOp.kIntersect, True)
    pen.linear(rect(x0, y0, w, h), 0, y0, 0, y0 + h, ['#1a2238', '#0a0e18'])
    bars = 0 if state == 'nobars' else 4
    _status(pen, x0, y0, w, bars)
    if state == 'nobars':
        btext(pen, '911', 0, y0 + 300, 'sans', 110, '#ffffff', 245, 'center')
        btext(pen, 'Call Failed', 0, y0 + 380, 'sans_b', 40, '#ff6a5a', 245, 'center')
        btext(pen, 'No bars', 0, y0 + 430, 'sans', 32, '#c8c8d0', 230, 'center')
        pen.fill(oval(0, y0 + 860, 70), '#3a3a44'); btext(pen, 'Retry', 0, y0 + 872, 'sans', 26, '#ffffff', 220, 'center')
    else:
        btext(pen, '911', 0, y0 + 300, 'sans', 110, '#ffffff', 245, 'center')
        btext(pen, 'Emergency call  0:%02d' % (12 + int(t)), 0, y0 + 380, 'sans', 34, '#a8f0b8', 245, 'center')
        pen.fill(oval(0, y0 + 860, 70), '#e8403a')
    pen.cv.restore(); pen.cv.restore()


def _bui_rules(pen, t, show=7, hl=0, eighth=False, **kw):
    """The rules taped inside the front door (Grandma's print on lined paper; rule 8 in Mina's hand)."""
    _ibg_b(pen, BU_PAL['door'], _darken(BU_PAL['door'], 0.3), 140)
    pen.texture(rect(*_IBGB), 'wood', 0.35, 'overlay', 1.2, 90)
    for (x0, y0, w, h) in ((-200, -300, 860, 2000), (1260, -300, 860, 2000)):
        pen.line(rect(x0, y0, w, h), 3, '#000000', 80)
    pen.cv.save(); pen.cv.translate(960, 540); pen.cv.rotate(-1.2)
    W, H = 1120, 1000 if eighth else 920
    x0, y0 = -W / 2, -H / 2
    pen.fill(rect(x0 + 16, y0 + 24, W, H), '#000000', 110, blur=20)
    pen.fill(rect(x0, y0, W, H), '#f6f1e2'); pen.texture(rect(x0, y0, W, H), 'paper', 0.45, 'multiply', 1.0)
    for i in range(int(H / 37)): pen.fill(rect(x0, y0 + 92 + i * 37, W, 2), '#8ab0d8', 120)
    pen.fill(rect(x0 + 90, y0, 3, H), '#d88a8a', 140)
    btext(pen, 'THE RULES', 0, y0 + 66, 'caveat_b', 56, '#1e2a5a', 245, 'center')
    yy = y0 + 124
    for (n, lines) in BU_RULES[:show]:
        if hl == n: pen.fill(rect(x0 + 100, yy - 28, W - 140, 37 * len(lines) + 4), '#fff08a', 170)
        btext(pen, '%d.' % n, x0 + 108, yy, 'caveat_b', 31, '#1e2a5a', 245)
        for j, ln in enumerate(lines):
            btext(pen, ln, x0 + 150, yy + j * 36, 'caveat', 30, '#1e2a5a', 240)
        yy += 36 * len(lines) + 8
    if eighth:
        yy += 14
        n, lines = BU_RULE8
        btext(pen, '8.', x0 + 108, yy, 'kid', 32, '#2a2a2a', 250)
        for j, ln in enumerate(lines): btext(pen, ln, x0 + 150, yy + j * 40, 'kid', 32, '#2a2a2a', 245)
    for (tx, ty, r) in ((x0 + 60, y0 - 4, -14), (x0 + W - 60, y0 - 4, 12), (x0 + 60, y0 + H + 4, 10), (x0 + W - 60, y0 + H + 4, -12)):
        _bu_tape(pen, tx, ty, 150, 46, r, 190)
    pen.cv.restore()


def _bui_ticket(pen, t, slide=1.0, bg='floor', **kw):
    """The yellow punched ticket: SAMI. SEAT 4. LAST STOP 3 A.M. (slide 0..1: under the door onto the boards)."""
    if bg == 'floor':
        _ibg_b(pen, '#6a4428', '#3a2414', 120)
        pen.texture(rect(*_IBGB), 'wood', 0.6, 'overlay', 1.0, 0)
        for k in range(8): pen.fill(rect(-520, -420 + k * 280, 2960, 3), '#000000', 90)
        pen.fill(rect(-520, -420, 2960, 300), '#1a0e0a'); pen.linear(rect(-520, -120, 2960, 40), 0, -120, 0, -80, [(0, '#ffd080', 120), (1, '#ffd080', 0)])
    else:
        _ibg_b(pen, '#2a1e10', '#100a04', 140)
    y = -100 + 640 * slide
    pen.cv.save(); pen.cv.translate(960, y); pen.cv.rotate(-4)
    W, H = 900, 460
    tk = rrect(-W / 2, -H / 2, W, H, 14)
    pen.fill(moved(tk, 12, 18), '#000000', 110, blur=16)
    pen.fill(tk, '#f0c830'); pen.texture(tk, 'paper', 0.5, 'multiply', 1.0)
    pen.line(rrect(-W / 2 + 18, -H / 2 + 18, W - 36, H - 36, 8), 3, '#7a5a10', 200)
    btext(pen, 'SAMI.', 0, -95, 'head', 96, '#1a1408', 250, 'center')
    pen.fill(oval(0, -18, 24), '#140c04'); pen.line(oval(0, -18, 24), 2, '#5a4a10')               # punched through the middle
    btext(pen, 'SEAT 4.', 0, 80, 'head', 66, '#1a1408', 245, 'center')
    btext(pen, 'LAST STOP 3 A.M.', 0, 160, 'head', 60, '#1a1408', 245, 'center')
    btext(pen, 'RIDE RIGHT · ADMIT ONE', 0, 205, 'sans_b', 22, '#5a4a10', 220, 'center')
    pen.cv.restore()


def _bui_walkie(pen, t, talk=0.0, bg='couch', **kw):
    _ibg_b(pen, '#7a3a28' if bg == 'couch' else '#3a3a3e', '#3a1a10', 150)
    pen.texture(rect(*_IBGB), 'fabric', 0.7, 'overlay', 1.2)
    pen.cv.save(); pen.cv.translate(960, 560); pen.cv.rotate(-18)
    body = rrect(-170, -330, 340, 660, 40)
    pen.fill(moved(body, 18, 26), '#000000', 120, blur=24)
    pen.fill(body, '#e8c020'); pen.line(body, 4)
    pen.fill(rrect(-120, -260, 240, 230, 20), '#1a1a1a')
    for k in range(9): pen.fill(rect(-100, -240 + k * 24, 200, 9), '#3a3a3a')
    pen.fill(rrect(-40, -560, 40, 240, 14), '#1a1a1a')
    pen.fill(rrect(-200, -60, 40, 160, 10), '#2a2a2a'); btext(pen, 'PTT', -180, 140, 'sans_b', 22, '#1a1a1a', 220, 'center')
    pen.fill(oval(90, 60, 20), mix('#5a1010', '#ff3a2a', talk))
    if talk > 0.05: pen.glow(90, 60, 90, '#ff3a2a', 160 * talk)
    btext(pen, 'CH 1', 0, 200, 'sans_b', 40, '#1a1a1a', 220, 'center')
    pen.cv.restore()


def _bui_punch(pen, t, click=0.0, **kw):
    _ibg_b(pen, '#3a2410', '#120a04', 160)
    pen.cv.save(); pen.cv.translate(960, 560); pen.cv.rotate(-12)
    a = 10 * click
    for sd, ang in ((1, -a), (-1, a)):
        pen.cv.save(); pen.cv.rotate(ang)
        h = poly([(-40, 0), (40, 0), (60 * sd + 20, 420), (60 * sd - 20, 420)]) if False else rrect(-50 + sd * 40, -40, 60, 470, 26)
        pen.fill(h, '#c8ccd4'); pen.line(h, 3); pen.linear(h, -50, 0, 50, 0, [(0, '#ffffff', 120), (0.5, '#ffffff', 0), (1, '#000000', 60)])
        pen.cv.restore()
    jaw = rrect(-120, -180, 240, 150, 30)
    pen.fill(jaw, '#d8dce4'); pen.line(jaw, 3); pen.fill(oval(0, -105, 26), '#2a2a2a')
    pen.fill(rrect(-90, -330, 180, 160, 30), '#b8bcc4'); pen.line(rrect(-90, -330, 180, 160, 30), 3)
    pen.cv.restore()


BU_CLIP_NAMES = [('Kayla R.', 3, True), ('Jordan P.', 7, True), ('Lucas M.', 2, True), ('Ava T.', 9, True), ('Ben S.', 5, True), ('Noor A.', 1, True),
                 ('Theo', 9, False), ('Maddie K.', 4, True), ('Sam W.', 6, True), ('Priya D.', 8, True), ('Eli G.', 3, True), ('Rosa V.', 2, True)]


def _bui_clipboard(pen, t, page='list', write=1.0, **kw):
    """His clipboard: page 'list' (names from every bus in Larkfield, each 'Sat alone', most crossed out; Theo's not) |
    'last' (today's date and one name, an unreadable scrawl: her name is never shown or said)."""
    _ibg_b(pen, '#1a1410', '#0a0806', 160)
    pen.cv.save(); pen.cv.translate(960, 560); pen.cv.rotate(2.5)
    pen.fill(rrect(-520, -640, 1040, 1300, 26), '#8a6a3a'); pen.texture(rrect(-520, -640, 1040, 1300, 26), 'wood', 0.5, 'overlay', 1.0, 90)
    pen.fill(rect(-470, -560, 940, 1180), '#efe8d2'); pen.texture(rect(-470, -560, 940, 1180), 'paper', 0.5, 'multiply', 1.2)
    pen.fill(rrect(-170, -680, 340, 120, 18), '#c8ccd4'); pen.line(rrect(-170, -680, 340, 120, 18), 3)
    if page == 'list':
        btext(pen, 'ROLL CALL', 0, -470, 'serif_b', 54, '#2a2a3a', 240, 'center')
        for i, (nm, bus_, crossed) in enumerate(BU_CLIP_NAMES):
            y = -380 + i * 76
            btext(pen, 'BUS %d' % bus_, -420, y, 'mono', 30, '#4a4a5a', 220)
            btext(pen, nm, -230, y, 'caveat_b', 44, '#1a1a3a', 245)
            btext(pen, 'Sat alone', 120, y, 'caveat', 40, '#5a2a2a', 235)
            if crossed:
                pen.line(smooth([(-430, y - 14), (0, y - 20 + 6 * math.sin(i)), (420, y - 12)], False), 5, '#1a1a1a', 230)
    else:
        btext(pen, 'ROLL CALL', 0, -470, 'serif_b', 54, '#2a2a3a', 240, 'center')
        btext(pen, 'SEPT. 3', -420, -360, 'caveat_b', 48, '#1a1a3a', 240)
        L = 700 * clamp(write)
        pen.cv.save(); pen.cv.clipPath(rect(-430, -320, L + 10, 120), skia.ClipOp.kIntersect, True)
        pts = [(-420 + k * 14, -250 + 22 * math.sin(k * 1.3) + 10 * math.sin(k * 0.4)) for k in range(52)]
        pen.line(smooth(pts, False, 0.8), 5, '#1a1a3a', 235)
        pen.cv.restore()
        btext(pen, 'Sat alone', 120, -250, 'caveat', 40, '#5a2a2a', 235 * (write > 0.95))
    pen.cv.restore()


def _bui_flashlight(pen, t, on=1.0, **kw):
    """Down in the driveway: a flashlight blinking inside bus 9's dark cab (seen through its windshield)."""
    _ibg_b(pen, '#05070c', None, 80)
    pen.fill(rrect(380, 220, 1160, 560, 30), '#0a0e16'); pen.line(rrect(380, 220, 1160, 560, 30), 10, '#c8a020')
    pen.fill(rect(950, 220, 20, 560), '#c8a020')
    pen.linear(rect(380, 220, 1160, 560), 380, 220, 1540, 780, [(0, '#8a9ac8', 30), (0.5, '#8a9ac8', 0), (1, '#8a9ac8', 25)])
    if on > 0.01:
        pen.glow(760, 520, 260, '#fff2d0', 180 * on); pen.glow(760, 520, 60, '#ffffff', 250 * on)
        pen.cone(760, 520, 30, 600, 500, '#fff2d0', 60 * on, 50)
    pen.fill(rect(-520, 780, 2960, 400), '#c8a020'); btext(pen, 'LARKFIELD SCHOOL DISTRICT', 960, 900, 'head', 70, '#1a1a1a', 220, 'center')


def _bui_clock(pen, t, time=(2, 57), **kw):
    _ibg_b(pen, '#4a2a22', '#1a0e0a', 160)
    pat(pen, 1920, 1080, 'brick', '#1a0c08', 120)
    tm = time(t) if callable(time) else time
    class _V: pass
    cx, cy, R = 960, 540, 420
    pen.fill(oval(cx, cy, R * 1.12), '#141414'); pen.fill(oval(cx, cy, R), '#f2eee2'); pen.line(oval(cx, cy, R), 3)
    for k in range(60):
        a = math.radians(k * 6); r0 = 0.9 if k % 5 else 0.8
        pen.seg((cx + math.sin(a) * R * r0, cy - math.cos(a) * R * r0), (cx + math.sin(a) * R * 0.95, cy - math.cos(a) * R * 0.95), 10 if k % 5 == 0 else 3, '#1a1a1a')
    for k in range(1, 13):
        a = math.radians(k * 30); btext(pen, str(k), cx + math.sin(a) * R * 0.66, cy - math.cos(a) * R * 0.66 + 26, 'sans_b', 72, '#1a1a1a', 240, 'center')
    h, m = tm[0], tm[1]; s = tm[2] if len(tm) > 2 else 0
    am = math.radians((m + s / 60.0) * 6); ah = math.radians(((h % 12) + m / 60.0) * 30); asec = math.radians(s * 6)
    pen.seg((cx, cy), (cx + math.sin(ah) * R * 0.5, cy - math.cos(ah) * R * 0.5), 26, '#1a1a1a')
    pen.seg((cx, cy), (cx + math.sin(am) * R * 0.82, cy - math.cos(am) * R * 0.82), 16, '#1a1a1a')
    pen.seg((cx - math.sin(asec) * R * 0.15, cy + math.cos(asec) * R * 0.15), (cx + math.sin(asec) * R * 0.88, cy - math.cos(asec) * R * 0.88), 6, '#c8201a')
    pen.fill(oval(cx, cy, 20), '#c8201a')
    pen.linear(oval(cx, cy, R), cx - R, cy - R, cx + R, cy + R, [(0, '#ffffff', 70), (0.4, '#ffffff', 0), (1, '#ffffff', 0)])


def _bui_backpack(pen, t, side='front', **kw):
    _ibg_b(pen, '#2a2420', '#120e0c', 150)
    pen.fill(rect(-520, 760, 2960, 600), '#c8bca0')
    pen.cv.save(); pen.cv.translate(960, 500)
    body = rrect(-300, -380, 600, 760, 140)
    pen.fill(moved(body, 20, 26), '#000000', 110, blur=24)
    pen.fill(body, '#4aa06a' if side == 'front' else '#3e8a5c'); pen.texture(body, 'fabric', 0.6, 'overlay', 1.0); pen.line(body, 4)
    if side == 'front':
        pen.fill(rrect(-230, 20, 460, 300, 60), '#3a8a5a'); pen.line(rrect(-230, 20, 460, 300, 60), 3)
        for sx in (-1, 1): pen.fill(oval(sx * 110, -200, 50), '#ffffff'); pen.fill(oval(sx * 110, -195, 24), '#1a1a1a')
        pen.fill(rrect(-170, 90, 340, 120, 14), '#fff6dc'); pen.line(rrect(-170, 90, 340, 120, 14), 2)
        btext(pen, 'SAMI', 0, 178, 'kid', 96, '#c83a2a', 255, 'center')
    else:
        for xx in (-150, 150): pen.fill(rrect(xx - 40, -340, 80, 700, 40), '#2a5a3e')
    for k in range(5):
        x = -220 + k * 110
        pen.fill(poly([(x - 40, -360), (x, -470), (x + 40, -360)]), '#e88a3a'); pen.line(poly([(x - 40, -360), (x, -470), (x + 40, -360)]), 3)
    pen.cv.restore()


def _bui_tail(pen, t, bg='asphalt', **kw):
    _ibg_b(pen, '#26282c', '#0e0f12', 160)
    pen.texture(rect(*_IBGB), 'asphalt', 0.7, 'overlay', 2.0)
    pen.cv.save(); pen.cv.translate(960, 560); pen.cv.rotate(-8)
    tl = smooth([(-520, 40), (-200, -60), (200, -40), (520, 20), (200, 60), (-200, 80)], True, 0.8)
    pen.fill(moved(tl, 14, 20), '#000000', 100, blur=20)
    pen.fill(tl, '#4aa06a'); pen.texture(tl, 'fabric', 0.7, 'overlay', 1.0); pen.line(tl, 4)
    for k in range(5):
        x = -360 + k * 170
        pen.fill(poly([(x - 50, -40), (x, -170), (x + 50, -40)]), '#e88a3a'); pen.line(poly([(x - 50, -40), (x, -170), (x + 50, -40)]), 3)
    for k in range(9):
        pen.line(smooth([(-520 + k * 4, 20 + k * 10), (-570 - 20 * math.sin(k), 30 + k * 9), (-600 + 10 * math.cos(k * 2), 40 + k * 8)], False), 3, '#e8e4d8', 220)
    pen.cv.restore()


def _bui_mailbox(pen, t, letters=1.0, **kw):
    _ibg_b(pen, '#0c1018', '#05070c', 120)
    pen.fill(rrect(160, 300, 1600, 520, 40), '#1e2226'); pen.texture(rrect(160, 300, 1600, 520, 40), 'grunge', 0.5, 'overlay', 1.5); pen.line(rrect(160, 300, 1600, 520, 40), 5)
    n_on = clamp(letters) * len(BU_NAME)
    cw = 1360 / len(BU_NAME)
    for i, ch in enumerate(BU_NAME):
        cx = 280 + cw * (i + 0.5)
        k = clamp(n_on - i)
        if k > 0.01:
            pen.fill(rect(cx - cw * 0.4, 380, cw * 0.8, 360), '#f4f0e0', 250 * k)
            btext(pen, ch, cx, 680, 'sans_b', 300, '#1a1a1a', 255 * k, 'center')
        pen.line(rect(cx - cw * 0.4, 380, cw * 0.8, 360), 2, '#8a8a7a', 140 * (1 - k))
        for yy in (400, 720): pen.fill(oval(cx, yy, 8), '#9a9a9a'); pen.fill(oval(cx, yy, 3), '#3a3a3a')
    pen.glow(1500, 200, 600, BU_SODIUM, 60)


def _bui_chalkboard(pen, t, **kw):
    _ibg_b(pen, '#1a1a1a', None, 0)
    _chalkboard(pen, 0, 0, 1920, 1080)


BU_INSERTS = {
    'post': (_bui_post, 'bu_ins', "Mina's post: the first-day chalkboard photo, 41 likes, the faceless comment 'Great smile!' (show 0..2, hl 'comment')"),
    'comment': (_bui_comment, 'bu_ins', "the comment close: the crooked-yellow-hat avatar, 'Great smile!'"),
    'nobars': (lambda pen, t, **kw: _bui_phone_call(pen, t, 'nobars', **kw), 'bu_ins', '911: Call Failed, No bars'),
    'call911': (lambda pen, t, **kw: _bui_phone_call(pen, t, 'call', **kw), 'bu_ins', "the 911 call connected (Grandma's phone, bars back)"),
    'rules': (_bui_rules, 'bu_ins', 'the seven rules taped inside the door (show n, hl k, eighth: rule 8 in Mina\'s hand)'),
    'ticket': (_bui_ticket, 'bu_ins_amber', 'the yellow ticket punched through: SAMI. SEAT 4. LAST STOP 3 A.M. (slide 0..1 under the door)'),
    'walkie': (_bui_walkie, 'bu_ins', "Mina's walkie on the couch cushion (talk 0..1: the red LED)"),
    'punch': (_bui_punch, 'bu_ins_amber', 'his chrome ticket punch (click 0..1)'),
    'clipboard': (_bui_clipboard, 'bu_ins_amber', "his clipboard: page 'list' (Sat alone, crossed out; Theo not) | 'last' (today's date, one unreadable name; write 0..1)"),
    'flashlight': (_bui_flashlight, 'bu_ins', "a flashlight blinking in bus 9's dark cab (on 0..1 or f(t))"),
    'clock': (_bui_clock, 'bu_ins_amber', 'the school clock close (time=(h, m[, s]) or f(t))'),
    'backpack': (_bui_backpack, 'bu_ins', "Sami's dinosaur backpack: side 'front' (SAMI) | 'back' (turned to the wall)"),
    'tail': (_bui_tail, 'bu_ins_amber', 'the torn half of the dinosaur tail on the asphalt'),
    'mailbox': (_bui_mailbox, 'bu_ins', 'the mailbox letters (letters 0..1: being unscrewed)'),
    'chalkboard': (_bui_chalkboard, 'bu_ins', 'the first-day chalkboard photo full frame'),
}


def bu_insert(name, prop_kw=None, motion=None, t0=0.0, grade=None):
    """A close-up insert from BU_INSERTS (flat, 1920 x 1080 design space with margin for a drift): prop_kw dict (values
    may be f(t) for on / time / talk / click / write / slide) or f(t) -> dict; motion f(t) -> (dx, dy, dscale, drot)."""
    fn, gr, note = BU_INSERTS[name]
    static = not callable(prop_kw) and motion is None and not any(callable(v_) for v_ in (prop_kw or {}).values())

    def draw(pen, t):
        kw = prop_kw(t) if callable(prop_kw) else dict(prop_kw or {})
        kw = {k_: (v_(t) if callable(v_) and k_ != 'time' else v_) for k_, v_ in kw.items()}
        cv = pen.cv
        if motion is not None:
            dx, dy, ds, dr = motion(t)
            cv.save(); cv.translate(960 + dx, 540 + dy); cv.rotate(dr); cv.scale(1 + ds, 1 + ds); cv.translate(-960, -540)
        fn(pen, t - t0, **kw)
        if motion is not None: cv.restore()
    key = 'buins:%s:%s' % (name, _okey(prop_kw or {}) if isinstance(prop_kw, dict) else 'f')
    lay = Layer(1.0, draw, 'insert', cache=key if static else False, bounds=(-460, -320, 2380, 1400), blur=0)
    sp = BSet('bu_ins_' + name, [lay], {}, {}, lens=None, grade=grade or gr, focus=1.0, dof=0.0, cover=(-460, -320, 2380, 1400), info={'note': note})
    if gr == 'bu_ins_amber': sp._fx = bu_vhs_dirt(0.15, 0.03)
    return sp


# ====================================================================================================== the plan map, the registry
def _bu_plan_panels():
    def blocks(*sets_):
        b = {}
        for sp_ in sets_:
            for k_, q in (sp_.info.get('blocks') or {}).items():
                if not k_.startswith('far_'): b[k_] = q
        return b

    def marks(sp_, names):
        return [(sp_.anchors[n].X, sp_.anchors[n].Yp, n) for n in names if n in sp_.anchors]
    lv, hl = bu_living('wide'), bu_hall('door')
    P = []
    P.append(dict(title="GRANDMA DELLA'S HOUSE: GROUND FLOOR  (floor Y 0)", ext=(-6.4, 5.2, -3.0, 10.2), ray=1.4,
                  floors=[('LIVING ROOM', _r4p(BU_LIV)), ('HALL', _r4p(BU_HALL)), ('kitchen (not built)', _r4p((-3.2, 4.6, 5.8, 9.6))),
                          ('den (not built)', _r4p((2.4, 4.6, 0.0, 5.8))), ('stairs', _r4p((BU_ST[0], BU_ST[1], BU_ST[2], BU_ST_TOP))), ('porch', _r4p(BU_PORCH))],
                  blocks=blocks(lv, hl), doors=[((BU_FDOOR[0], 0.0), (BU_FDOOR[1], 0.0), 'front door'), ((-3.2, BU_LOPEN[0]), (-3.2, BU_LOPEN[1]), 'opening'),
                                                 ((BU_BDOOR[0], 9.6), (BU_BDOOR[1], 9.6), 'back door'), ((BU_KDOOR[0], 5.8), (BU_KDOOR[1], 5.8), 'kitchen')],
                  windows=[((BU_PWIN[0], 0.0), (BU_PWIN[1], 0.0)), ((-5.6, BU_HWIN[0]), (-5.6, BU_HWIN[1]))], lines=[],
                  marks=marks(lv, ('couch_right', 'armchair', 'window', 'walkie', 'backpack')) + marks(hl, ('peephole_eye', 'stairs_foot', 'back_door', 'side_window')),
                  cams=[k for k in BU_CAMS if CAMS[k]['room'] in ('living', 'hall')]))
    up, gr, sm = bu_upstairs('hall'), bu_gran('door'), bu_sami('room')
    P.append(dict(title='UPSTAIRS  (floor Y %.2f, ceiling +%.1f)' % (BU_UP, BU_UH), ext=(-6.4, 1.6, -0.8, 10.2), ray=1.2,
                  floors=[("GRANDMA'S ROOM", _r4p(BU_GRAN)), ('HALL', _r4p(BU_UHALL)), ('landing', _r4p(BU_LAND)), ("SAMI'S ROOM", _r4p(BU_SAMI)),
                          ('stairwell', _r4p((BU_ST[0], BU_ST[1], BU_ST[2], BU_ST_TOP))), ("Mina's room (not built)", _r4p((-3.4, 1.6, 0.0, 5.4)))],
                  blocks=blocks(gr, sm), doors=[((BU_GDOOR[0], 3.2), (BU_GDOOR[1], 3.2), 'deadbolt'), ((-3.4, BU_SDOOR[0]), (-3.4, BU_SDOOR[1]), 'Sami'),
                                                ((-3.4, BU_MDOOR[0]), (-3.4, BU_MDOOR[1]), 'Mina')],
                  windows=[((-5.6, BU_GWIN[0]), (-5.6, BU_GWIN[1])), ((BU_GFWIN[0], 0.0), (BU_GFWIN[1], 0.0)), ((BU_SWIN[0], 9.6), (BU_SWIN[1], 9.6))], lines=[],
                  marks=marks(gr, ('door_sit', 'window')) + marks(up, ('hall_mid', 'landing')) + marks(sm, ('bed', 'room_mid')),
                  cams=[k for k in BU_CAMS if CAMS[k]['room'] in ('uphall', 'gran', 'sami')]))
    ex = bu_front('house')
    b9, hb = bu_bus_parts(*BU_BUS9), bu_bus_parts(*BU_HISBUS)
    P.append(dict(title='LARCH STREET  (ground Y %.1f)' % BU_G, ext=(-26.0, 14.0, -28.0, 12.0), ray=5.0,
                  floors=[('HOUSE', _r4p(BU_HOUSE)), ('driveway', _r4p(BU_DRIVE)), ('Larch Street', [(-26, D_STREET[1]), (14, D_STREET[1]), (14, D_STREET[0]), (-26, D_STREET[0])]),
                          ('porch', _r4p(BU_PORCH))],
                  blocks={'bus 9': ex.info['blocks'].get('bus9'), 'his bus': ex.info['blocks'].get('his_bus')}, doors=[((BU_FDOOR[0], 0.0), (BU_FDOOR[1], 0.0), '')],
                  windows=[((BU_PWIN[0], 0.0), (BU_PWIN[1], 0.0))], lines=[],
                  marks=marks(ex, ('mailbox', 'lawn_mid', 'porch_step', 'b9_door', 'his_door', 'lamp', 'yard_west')),
                  cams=[k for k in BU_CAMS if CAMS[k]['room'] == 'street']))
    bi = bu_bus_in('aisle')
    P.append(dict(title='INSIDE A BUS (his / bus 9)  +y = toward the back; +x = the door side', ext=(-2.2, 3.6, -1.2, 11.2), ray=0.9,
                  floors=[('cabin', BuBusInterior.poly)], blocks={}, doors=[((BU_IW, BU_IDOOR[0]), (BU_IW, BU_IDOOR[1]), 'door')], windows=[], lines=[],
                  marks=marks(bi, ('seat1', 'seat4', 'seat21', 'seat22', 'driver', 'top_step', 'bottom_step')), cams=[k for k in BU_CAMS if CAMS[k]['room'] == 'bus']))
    sc = bu_school('wide')
    P.append(dict(title='LARKFIELD ELEMENTARY, 2:57 AM', ext=(-16.0, 14.0, -34.0, 2.0), ray=4.0, floors=[('SCHOOL', [(-16, 0), (14, 0), (14, 2), (-16, 2)])],
                  blocks={'his bus': sc.info['blocks'].get('his_bus'), 'bus 9': sc.info['blocks'].get('bus9'), 'flag': sc.info['blocks'].get('flagpole')}, doors=[((-1.5, 0.0), (1.5, 0.0), 'doors')],
                  windows=[], lines=[], marks=marks(sc, ('bottom_step', 'behind_mina', 'clock', 'lot_kneel')), cams=[k for k in BU_CAMS if CAMS[k]['room'] == 'school']))
    rd = bu_road('side')
    P.append(dict(title='THE CHASE ROAD  (both buses drive toward -y)', ext=(-8.0, 12.0, -32.0, 12.0), ray=4.0,
                  floors=[('road', [(-5.4, -32), (2.1, -32), (2.1, 12), (-5.4, 12)])], blocks={'bus 9': rd.info['blocks'].get('bus9'), 'his bus': rd.info['blocks'].get('his_bus')},
                  doors=[], windows=[], lines=[[(-1.9, -32), (-1.9, 12)]], marks=[], cams=[k for k in BU_CAMS if CAMS[k]['room'] == 'road']))
    for (title, sp_, R_, ray, room, mk) in (("THEO'S STOP", bu_theo_stop('house'), (-8.0, 8.0, -16.0, 2.0), 3.0, 'theo', ('porch_light', 'walk')),
                                            ('1994: THE CLASSROOM', bu_class94('cart'), (0.0, 8.0, 0.0, 7.0), 1.2, 'class94', ('tv_screen', 'desk_front'))):
        P.append(dict(title=title, ext=(R_[0] - 0.5, R_[1] + 0.5, R_[2] - 0.6, R_[3] + 0.5), ray=ray, floors=[('', _r4p(R_))], blocks=blocks(sp_), doors=[], windows=[], lines=[],
                      marks=marks(sp_, mk), cams=[k for k in BU_CAMS if CAMS[k]['room'] == room]))
    for P_ in P:
        P_['blocks'] = {k_: q for k_, q in P_['blocks'].items() if q}
    return P


def bu_plan_map(path, pw=900, ph=1000, cols=4):
    """The Bus film's floor plans with every camera -> JPEG (the Doctor film's renderer on this film's panels)."""
    import inspect
    src = inspect.getsource(dr_plan_map).replace('def dr_plan_map(', 'def _bu_plan_map_impl(').replace('_dr_plan_panels()', '_bu_plan_panels()')
    ns = dict(globals()); exec(src, ns)
    return ns['_bu_plan_map_impl'](path, pw, ph, cols)


BU_SETS = {'bu_living': bu_living, 'bu_hall': bu_hall, 'bu_upstairs': bu_upstairs, 'bu_gran': bu_gran, 'bu_sami': bu_sami, 'bu_front': bu_front,
           'bu_bus_in': bu_bus_in, 'bu_road': bu_road, 'bu_school': bu_school, 'bu_theo_stop': bu_theo_stop, 'bu_class94': bu_class94, 'bu_tape94': bu_tape94,
           'bu_insert': bu_insert}
BU_API = {nm: sorted({k[len(pre):] for k in BU_CAMS if k.startswith(pre)}) for nm, pre in (
    ('bu_living', 'bu_liv_'), ('bu_hall', 'bu_hall_'), ('bu_upstairs', 'bu_up_'), ('bu_gran', 'bu_gran_'), ('bu_sami', 'bu_sami_'), ('bu_front', 'bu_ext_'),
    ('bu_bus_in', 'bu_bus_'), ('bu_road', 'bu_road_'), ('bu_school', 'bu_sch_'), ('bu_theo_stop', 'bu_theo_'), ('bu_class94', 'bu_class_'))}
BU_API['bu_tape94'] = ['full', 'kids', 'title']
BU_API['bu_insert'] = sorted(BU_INSERTS)
