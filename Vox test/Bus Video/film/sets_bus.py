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
BU_LOPEN = (0.8, 3.4, 2.25)           # the cased opening hall <-> living room on x -3.2 (y0, y1, height)
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
_GR.setdefault('bu_morning', dict(exposure=0.16, contrast=1.02, pivot=0.26, gamma=1.05, sat=1.12, wb=(1.06, 1.0, 0.9), floor='#141008',
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


def _lv(spec, seed, t=0.0):
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


_bcam('bu_ext_house', 820, 520, BU_G + 1.6, -1.6, -24.0, 4, _env(f=(1.0, 2.6)), "the house from across Larch Street: porch, picture window, bus 9 in the driveway, his bus at the kerb", 'street')
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
