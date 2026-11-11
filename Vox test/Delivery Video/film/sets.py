"""sets.py: environments, animated set elements and props for "If A Police Officer Knocks..." v2.

Every set is a builder returning a SetPiece: a list of engine Layers (depth-sorted by the engine) with real depth
spacing for parallax, plus anchors where characters stand and the suggested lens / grade / focus / dof / post fx.
Static parts are cached engine layers (drawn once); animated parts are small live layers. Measured drawing cost per
frame at 2560x1440 (one process, layers only): 48-110 ms per set; the patrol car ~15-25 ms of that.

Quick use (director)
    import sets
    sp = sets.porch_doorbell(police=dict(mode='sweep'), drive_in=None)
    a = sp.anchors['officer']                       # Anchor(x, y, depth, height): feet position as drawn at `depth`
    officer = Layer(a.depth, lambda pen, t: characters.draw(pen, 'officer', a.x, a.y, a.height, acting.at(t)),
                    'officer', ref_depth=a.depth)   # animate depth (a.depth -> 0.6) to walk toward the lens
    img = render_frame(sp.add(officer), cam.at(t), t, i, **sp.render_kw(), post=sp.fx(t), hud=...)
    Scene(sp.add(officer), cam, **sp.render_kw(), post=sp.fx).frame(t, i)   # same through engine.Scene

SetPiece(list)
    .name .anchors {name: Anchor} .paths {name: [Anchor, ...]} (walk routes: interpolate x, y, depth, height)
    .lens .grade .focus .dof .cover (design rect drawn) .info (view, window rects, 'lights' = f(t) -> (r, b), ...)
    .add(*layers) -> new SetPiece    .without(*names)    .layer(name)    .fx(t) -> suggested post dict ({'flash': ...})
    .render_kw() -> dict(lens, grade, focus, dof)
Anchor(x, y, depth, height, note): x, y = feet (design px at that depth), height = design px of a 1.85 m adult there.
View(S, horizon, cam_h, cx=960, ground=0): metres -> design px. p(X, Y, D), x(X, D), y(Y, D), s(D) px/m, gy(D), anchor(X, D).

Sets (all keyword args optional; police = False | True | dict(mode='sweep'|'strobe'|'wigwag', speed, strength, t_on, t_off))
    porch_doorbell(car, police, car_X=4.0, flick='random'|None|[(t0, dur)], moths=6, wind=1.0, mist, drive_in=(t0, t1),
                   doors=f(t)->{'rear': k}, figures=('driver','back'), ir=False)        lens 'doorbell' / 'doorbell_ir'
        Camera at the door (1.45 m) looking out. Officer at anchors['officer'] depth 1.0 (~1.5 m). Porch boards + doormat,
        white railing + newel posts + potted plants, post lantern with moths/flicker, rocking chair, side railings,
        portico edge, yard (path lights, flower beds, hedges, mailbox 144), sidewalk, street, parked cars, patrol car at
        the curb (light bar + red/blue spill on the yard, railing and houses), street lamps with cones, houses across
        with lit windows, bare trees (yard tree sways), tree line, sky with moon, stars and clouds, mist.
        Anchors: officer, officer_close, officer2, double, steps, path_mid, gate, car_rear_door; paths['car_to_porch'].
    porch_peephole(...same...)                       lens 'peephole', grade 'porch_warm'; officer fills ~45 % of the
        disc at depth 1.0, ~70 % at anchors['officer_close'] (0.62). Car with the second officer + back-seat man visible.
    street_wide(car, police, car_X=3.6, drive=('in'|'out'|'pass', t0, t1, X0, X1), doors, figures, bedroom_lit,
                living_lit, wind, mist, head)          lens None, grade 'night_blue'
        House 144 from across the street: two storeys, siding, shutters, porch with columns/railing/lattice/steps,
        lantern + moths, number plaque 144, mailbox, lawn + path, neighbours 142/146, street lamp, trees, parked sedan,
        patrol car in front (depth 1.1), hydrant / bin / hedge foreground (depth 0.6). info['bedroom_window'].
        Anchors: officer, double, officer2 (porch), steps, path_mid, gate, car_rear_door, car_front_door;
        paths 'porch_to_car', 'car_to_porch'.
    mother_exterior(car, police=False, car_X=4.2, drive, doors, figures, window_lit, silhouette, wind, mist, head)
        Mum's brick cottage (no. 27): hip roof, bay window with lace (optional silhouette), portico lamp, picket fence.
    car_backseat_window(police, reflect=1.0, fog=f(t)->(x, y, r, k), cage, far_street, lamp_reflection)
        Rear side window close-up: far street through the far window (7), seat/headrests/cage (1.35), the man goes at
        anchors['man'] (1.2, seated; head ~ (990, 430)), door + window frame (1.0), glass reflections (0.98) and live
        light-bar reflections (0.975). Put a card / hand_on_glass at depth 0.99. info['window'].
    hallway(police, lamp, porch_light, feet=f(t)->[x fractions], chain=0..1|f(t), slot_open=f(t)->0..1, door_c, wall,
            photo, coats, sweep=(t0, dur), flick)      lens 'lens' or None, grade 'interior_dim'
        Front door from inside (6 panels, grain, peephole glint, deadbolt, chain, mail slot), transom with porch light
        and police colours, light gap under the door with feet shadows, damask wallpaper over wainscot, coat hooks,
        console table + lamp + key bowl, THE PHOTOGRAPH on the right wall, runner rug, smoke detector.
        info: door_rect, mail_slot, peephole. Anchors: door, you, table_edge.
    kitchen(police, pendant, sway, tiles='#2f5a8a' (BLUE), clock, mug, sweep)   grade 'interior_dim'
        Blue tile backsplash, cabinets, window over the sink (police glow), fridge with drawings, stove + kettle, live
        wall clock (12:36 + t), swaying pendant lamp, the table edge across the bottom. info['tiles_rect'].
    living_room_window(car, police, drive=('out', ...), car_X, figures, curtains, lamp, doors, head, wind, glass, sweep)
        Window onto the street (car at the curb, drives off), swaying curtains, floor lamp, radiator, sill plant,
        pictures, sofa back in the foreground. Anchors: you_window, car, car_back_seat (the double's head outside).
    mother_room(police, lamp, phone_ring=f(t)->0..1, door_glow, curtains, knock=f(t))
        Floral wallpaper, armchair with throw, side table with lamp + corded phone (rattles), photos, sideboard,
        clock, window with lace and drapes, a centred doorway onto her hall with the front door at the end (glass goes
        red/blue with police). Anchors: mum_chair (seated), mum_standing, mum_door, phone.
    build(name, **kw): SETS[name](**kw); build('insert:<name>', **kw) -> insert(...).

Inserts (close-ups with background DOF: background depth 3 blurred sigma 4.5 + darkened 30 %, prop sharp at depth 1)
    insert(name, t0=0, prop_kw=dict | f(t)->dict, motion=f(t)->(dx, dy, dscale, drot), hand=None|False|(pose, x, y,
           scale, rot), bg_dim=0.3, police=True) -> SetPiece (focus 1, dof 6.75)
    names (INSERTS): licence, licence_window (pressed on the car glass, glare hides the photo), complaint,
    complaint_name, complaint_verified (zoomed, highlighted fields), notebook, radio, keys_neighbour (evidence bag),
    key_outside (key_in=0..1), lock_inside (turn=0..1, chain=0..1), photo, phone_busy, phone_table, tiles,
    mail_slot (prop_kw: feed=0..1, item='complaint'|'licence', flap).

Props: draw_prop(pen, name, x, y, scale=1.0, rot=0.0, t=0.0, cache=False, **kw)   (PROP_SIZE = size at scale 1)
    complaint (name, address, highlight='address'|'description'|'name'|'signature'|'verified', verified=False),
    licence (name, broken=True: the chipped corner, glare, photo), licence_back, notebook (lines), pen (click),
    radio (led red, talk green), keys (ring, fob='#ff7a1a', single=True: 'your key'), wallet, phone (screen 'off'|
    'calling'|'busy'|'incoming'|'lock', face_down, vibrate), bag (evidence bag: wallet, phone, keys with the orange
    ring), lock (side 'inside' thumb-turn + chain | 'outside' cylinder + key), photo (framed | loose), tiles.
    The licence and complaint share the same signature (seed 7) incl. the slip in the last letter.
    cache=True draws through a sprite raster (rotation baked in 0.25 deg steps): use it for static props that move.
draw_hand(pen, x, y, scale, rot, pose='hold'|'flat'|'pinch', skin, sleeve, side, cuff, part='all'|'back'|'front')

Animated elements (functions of t)
    lightbar(t, mode='sweep'|'strobe'|'wigwag', speed, strength, t_on, t_off) -> (red, blue) 0..1, in phase with
        engine post.police_flash(t, mode=...); drives the car's light bar and every set's red/blue spill.
    flicker(t, seed, amount, bursts=[(t0, dur)] | None, rate) -> bulb brightness (lanterns, hall lamp).
    drive(t, t0, t1, x0, x1, mode='in'|'out'|'pass') -> CarState(x, v, wheel deg, bounce, pitch, moving).
    patrol_car(pen, x, y, length, t, facing, wheel, bounce, pitch, lights, head, brake, figures, doors)
    draw_moths(pen, t, x, y, r, n), draw_tree(pen, x, y, h, t, seed, wind), headlight_sweep(pen, t, t0, dur, box)
    Also inside the sets: swaying branches, curtains, pendant lamp, mist bands, wall clocks, phone rattle,
    flickering lanterns with moths, police spill (cached layers with animated alpha: skipped while dark).
Notes: sets draw over sp.cover (doorbell: WIDE = x -1000..2920, y -600..1660). Cache keys are shared strings, so build
a set once per shot (rebuilding per frame also works, just slower in Python). Call engine set_render_size first.
"""
import bisect, math, os
import numpy as np
import skia
from engine.core import (DW, DH, LINE, CFG, Pen, col, mix, rgb, poly, smooth, rect, rrect, oval, ring, union, inter, minus,
                         moved, scaled, clamp, lerp, prog, ease, ease_in_out, ease_out_cubic, ease_in_cubic, ease_out_back,
                         noise1, hash01, text, text_width, typeface, image_from, surface_for)
from engine.scene import Layer
from engine.post import police_flash

__all__ = ['SetPiece', 'Anchor', 'View', 'lightbar', 'flicker', 'drive', 'SETS', 'build', 'PROPS', 'PROP_SIZE', 'draw_prop', 'insert',
           'INSERTS', 'headlight_sweep',
           'porch_doorbell', 'porch_peephole', 'street_wide', 'car_backseat_window', 'hallway', 'kitchen',
           'living_room_window', 'mother_exterior', 'mother_room', 'patrol_car', 'draw_moths', 'draw_tree', 'draw_hand']

WIDE = (-1000, -600, 2920, 1660)          # doorbell source rect (-760..2680, -430..1510) plus camera moves
FRAME = (-330, -230, 2250, 1310)          # flat / 'lens' shots plus camera moves
PEEP = (180, -260, 1740, 1340)            # peephole source rect (300..1620, -120..1200) plus moves


# ============================================================== set container
class Anchor:
    """Where a character stands in a set: x, y = feet position in design px as drawn at `depth`; height = design px of a
    1.85 m adult standing there; depth = the Layer depth to use (ref_depth = depth). Characters: draw(pen, who, x, y, height)."""
    __slots__ = ('x', 'y', 'depth', 'height', 'note')

    def __init__(self, x, y, depth, height, note=''):
        self.x, self.y, self.depth, self.height, self.note = float(x), float(y), float(depth), float(height), note

    def __iter__(self): return iter((self.x, self.y, self.depth, self.height))

    def __repr__(self): return 'Anchor(x=%.0f, y=%.0f, depth=%.2f, height=%.0f%s)' % (self.x, self.y, self.depth, self.height,
                                                                                    ', ' + self.note if self.note else '')


class SetPiece(list):
    """A list of engine Layers (any order; the engine depth-sorts) plus what the director needs to place people and pick
    the look: .name, .anchors {name: Anchor}, .paths {name: [Anchor, ...]} (walk routes), .lens, .grade, .focus, .dof,
    .cover (design rect the set is drawn over), .fx(t) -> post dict suggestion (police flash etc.), .info (dict)."""

    def __init__(self, name, layers, anchors=None, paths=None, lens=None, grade=None, focus=1.0, dof=0.0, cover=FRAME,
                 fx=None, info=None):
        super().__init__(layers)
        self.name, self.anchors, self.paths = name, anchors or {}, paths or {}
        self.lens, self.grade, self.focus, self.dof, self.cover = lens, grade, focus, dof, cover
        self._fx, self.info = fx, info or {}

    def add(self, *layers):
        """Return a new SetPiece with extra layers (characters, props); the engine sorts by depth."""
        s = SetPiece(self.name, list(self) + [l for l in layers if l is not None], self.anchors, self.paths, self.lens,
                     self.grade, self.focus, self.dof, self.cover, self._fx, self.info)
        return s

    def without(self, *names):
        return SetPiece(self.name, [l for l in self if l.name not in names], self.anchors, self.paths, self.lens, self.grade,
                        self.focus, self.dof, self.cover, self._fx, self.info)

    def layer(self, name):
        for l in self:
            if l.name == name: return l
        raise KeyError(name)

    def fx(self, t):
        return dict(self._fx(t)) if self._fx else {}

    def render_kw(self):
        """Keyword arguments for engine render_frame / Scene: lens, grade, focus, dof."""
        return dict(lens=self.lens, grade=self.grade, focus=self.focus, dof=self.dof)


def _key(*parts):
    return 'sets:' + ':'.join(str(p) for p in parts)


def _cl(depth, draw, name, key, bounds, **kw):
    """Cached (static) layer."""
    return Layer(depth, draw, name, cache=key, bounds=bounds, **kw)


def _exposure(layers, k, names):
    """Darken the named static layers by k (baked into their cache once; lights and glows keep their level)."""
    for l in layers:
        if l.name in names: l.dim = k
    return layers


# ============================================================== perspective helper
class View:
    """Pinhole view used to lay sets out in metres: X lateral (m, + right), Y height (m, above the set's floor),
    D = layer depth (depth 1.0 = subject plane). S = design px per metre at depth 1. horizon = design y of eye level.
    cam_h = eye height above the floor in m."""

    def __init__(self, S, horizon, cam_h, cx=960.0, ground=0.0):
        self.S, self.h, self.cam_h, self.cx, self.ground = float(S), float(horizon), float(cam_h), float(cx), float(ground)

    def p(self, X, Y, D):
        k = self.S / D
        return (self.cx + X * k, self.h - (Y - self.cam_h) * k)

    def x(self, X, D): return self.cx + X * self.S / D

    def y(self, Y, D): return self.h - (Y - self.cam_h) * self.S / D

    def s(self, D): return self.S / D

    def quad(self, pts):
        """[(X, Y, D), ...] -> skia path."""
        return poly([self.p(*q) for q in pts])

    def gy(self, D): return self.y(self.ground, D)

    def anchor(self, X, D, Y=0.0, note=''):
        x, y = self.p(X, Y, D)
        return Anchor(x, y, D, 1.85 * self.S / D, note)


# ============================================================== timed functions (lights, motion)
def lightbar(t, mode='sweep', speed=1.0, strength=1.0, t_on=None, t_off=None):
    """Patrol-car light bar -> (red, blue) intensities 0..1 at time t. Same phase as engine post.police_flash(t, mode=...):
    'sweep' = rotating beacons (smooth alternation, 0.85 Hz), 'strobe' = double flashes at 2 Hz, 'wigwag' = hard 50/50
    alternation at 1.6 Hz with a quad pulse. t_on / t_off: lights switch on/off (0 outside)."""
    if (t_on is not None and t < t_on) or (t_off is not None and t >= t_off): return 0.0, 0.0
    tt = t * speed
    if mode == 'strobe':
        r, b = police_flash(t, 1.0, speed, 'strobe').light(0.5)
        return float(r) * strength, float(b) * strength
    if mode == 'wigwag':
        ph = (tt * 1.6) % 1.0
        side = ph < 0.5
        q = (ph % 0.5) / 0.5
        pulse = 1.0 if (int(q * 8) % 2 == 0) else 0.35
        return (pulse * strength, 0.06 * strength) if side else (0.06 * strength, pulse * strength)
    phi = 2 * math.pi * 0.85 * tt
    r = max(0.0, math.cos(phi)) ** 0.7
    b = max(0.0, math.cos(phi + math.pi)) ** 0.7
    return (0.12 + 0.88 * r) * strength, (0.12 + 0.88 * b) * strength


def flicker(t, seed=0, amount=1.0, bursts=None, rate=0.12):
    """Bulb brightness (0..1, mostly 1). Irregular dips happen in bursts: `bursts` = [(t0, dur), ...] or None for sparse
    random bursts (`rate` bursts per second). amount scales the dips. Use for porch lanterns, street lamps, hall lamps."""
    def dips(u):
        v = 0.0
        k = int(math.floor(u / 0.045))
        h = _h(k, seed + 11)
        if h < 0.45: v = 0.35 + 0.55 * _h(k, seed + 12)
        return v
    inside = False
    if bursts is not None:
        for (b0, d) in bursts:
            if b0 <= t < b0 + d: inside = True; break
    else:
        k = int(math.floor(t * rate * 2))
        if _h(k, seed + 7) < 0.5:
            b0 = (k + _h(k, seed + 8) * 0.6) / (rate * 2)
            inside = b0 <= t < b0 + 0.35 + 0.5 * _h(k, seed + 9)
    base = 1.0 - 0.025 * (0.5 + 0.5 * noise1(t * 7.0, seed + 3))
    return clamp(base - (amount * dips(t) if inside else 0.0), 0.0, 1.0)


class CarState:
    __slots__ = ('x', 'v', 'wheel', 'bounce', 'pitch', 'moving')

    def __init__(self, x, v, wheel, bounce, pitch, moving):
        self.x, self.v, self.wheel, self.bounce, self.pitch, self.moving = x, v, wheel, bounce, pitch, moving


def drive(t, t0, t1, x0, x1, mode='in', wheel_r=34.0, seed=0):
    """Car motion along x (design px at the car's depth) between t0 and t1.
    mode 'in' = arrives and brakes to a stop (nose dips, rocks back), 'out' = pulls away from rest (squats), 'pass' = constant
    speed. Returns CarState(x, v px/s, wheel angle deg, bounce px (down +), pitch deg (nose down +), moving)."""
    d = x1 - x0; T = max(1e-3, t1 - t0)
    u = (t - t0) / T
    if mode == 'in':
        uc = clamp(u); x = x0 + d * (1 - (1 - uc) ** 2.2); v = d / T * 2.2 * (1 - uc) ** 1.2 if 0 <= u < 1 else 0.0
    elif mode == 'out':
        uc = clamp(u); x = x0 + d * uc ** 2.2; v = d / T * 2.2 * uc ** 1.2 if 0 < u <= 1 else 0.0
        if u > 1: x = x1 + d / T * 2.2 * (t - t1); v = d / T * 2.2
    else:
        x = x0 + d * u; v = d / T
    dist = x - x0
    wheel = -dist / max(1e-3, wheel_r) * 180 / math.pi
    moving = abs(v) > 1.0
    road = 1.2 * noise1(t * 6.0, seed + 5) if moving else 0.0
    pitch, bounce = 0.0, road
    sgn = 1.0
    if mode == 'in' and t >= t1:
        s = t - t1
        pitch = 1.3 * math.exp(-s * 3.2) * math.cos(s * 9.0) * sgn
        bounce = 2.0 * math.exp(-s * 3.5) * math.cos(s * 10.0)
    elif mode == 'in' and u > 0.6:
        pitch = 0.9 * (u - 0.6) / 0.4 * sgn
    elif mode == 'out' and 0 <= u < 0.35:
        pitch = -0.9 * math.sin(u / 0.35 * math.pi) * sgn
    return CarState(x, v, wheel, bounce, pitch, moving)


# ============================================================== small drawing helpers
def _h(i, seed=0):
    """Deterministic random 0..1 (engine hash01 with any int-able i / seed, negatives allowed)."""
    return float(hash01(abs(int(i)) * 2 + (1 if i < 0 else 0), abs(int(seed)) * 2 + (1 if seed < 0 else 0)))


def _lighten(c, k): return mix(c, '#ffffff', k)


def _darken(c, k): return mix(c, '#000000', k)


def _blob(cx, cy, rx, ry, n=9, seed=0, jag=0.22):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 1 + jag * (_h(i, seed) - 0.5) * 2
        pts.append((cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r))
    return smooth(pts, True, 0.9)


def _stars(pen, box, n, seed, ymax):
    x0, y0, x1, y1 = box
    rng = np.random.default_rng(seed)
    for i in range(n):
        x, y = rng.uniform(x0, x1), y0 + (ymax - y0) * rng.uniform(0, 1) ** 1.25
        r = rng.uniform(0.7, 2.0); a = rng.uniform(50, 210) * (1 - 0.6 * clamp((y - y0) / (ymax - y0 + 1)))
        pen.fill(oval(x, y, r), '#dfe6ff', a)
        if r > 1.85:
            pen.glow(x, y, 9, '#c9d6ff', 60)
            pen.seg((x - 7, y), (x + 7, y), 0.8, '#e8eeff', 90); pen.seg((x, y - 7), (x, y + 7), 0.8, '#e8eeff', 90)


def _moon(pen, x, y, r):
    pen.glow(x, y, r * 7.5, '#5f74b8', 46)
    pen.glow(x, y, r * 3.0, '#9fb4e8', 70)
    m = oval(x, y, r)
    pen.radial(m, x - r * 0.3, y - r * 0.3, r * 1.4, [(0, '#f4f6fb'), (0.7, '#dfe5f1'), (1, '#b9c3d8')])
    for (dx, dy, rr, a) in ((-0.3, -0.15, 0.22, 70), (0.25, 0.2, 0.3, 55), (0.1, -0.45, 0.13, 60), (-0.2, 0.4, 0.15, 50),
                            (0.45, -0.2, 0.1, 50)):
        pen.fill(oval(x + dx * r, y + dy * r, rr * r), '#a9b3c9', a)
    pen.line(m, max(1.5, r * 0.04), '#c7cfe0', 120)


def _cloud(pen, cx, cy, w, h, seed, c='#141b36', rim='#3a4878', a=230):
    parts = []
    rng = np.random.default_rng(seed)
    for i in range(7):
        px = cx + (i - 3) * w / 7 + rng.uniform(-w * 0.04, w * 0.04)
        ry = h * (0.55 + 0.45 * math.sin(math.pi * (i + 0.5) / 7)) * rng.uniform(0.8, 1.1)
        parts.append(oval(px, cy - ry * 0.3, w / 7 * 1.25, ry))
    p = parts[0]
    for q in parts[1:]: p = union(p, q)
    p = inter(p, rect(cx - w, cy - h * 3, w * 2, h * 3 + h * 0.35))
    pen.fill(moved(p, 0, -4), rim, a * 0.45, blur=3)
    pen.fill(p, c, a, blur=2)


def draw_tree(pen, x, y, h, t=0.0, seed=1, wind=1.0, c='#0b0f16', lit=None, levels=5, spread=1.0, lean=0.0):
    """Bare, spooky tree drawn from its base (x, y) with trunk height scale h (design px). Branches sway with noise:
    wind = sway amount (0 = still). lit = (hex, alpha) moon-side rim colour on the trunk and main limbs."""
    rng = np.random.default_rng(seed)
    segs = []

    def grow(px, py, ang, length, width, lev):
        sway = wind * (0.35 + lev * 0.9) * noise1(t * (0.35 + 0.08 * lev) + seed * 3.1 + lev * 0.7, seed + lev) * 0.06
        a = ang + sway
        bend = (rng.uniform(-0.25, 0.25))
        mx, my = px + math.sin(a + bend * 0.5) * length * 0.5, py - math.cos(a + bend * 0.5) * length * 0.5
        ex, ey = px + math.sin(a) * length, py - math.cos(a) * length
        segs.append((lev, (px, py), (mx, my), (ex, ey), width))
        if lev >= levels: return
        nb = 2 if lev >= 2 else 3
        if lev == 0: nb = 3
        for i in range(nb):
            da = (i - (nb - 1) / 2) * (0.62 * spread) + rng.uniform(-0.18, 0.18)
            grow(ex, ey, a + da, length * rng.uniform(0.62, 0.78), width * 0.62, lev + 1)
        if lev >= 1 and rng.uniform() < 0.6:                     # a side twig from the middle
            grow(mx, my, a + rng.choice([-1, 1]) * rng.uniform(0.6, 1.0), length * 0.45, width * 0.45, lev + 2)

    grow(x, y, lean, h * 0.42, h * 0.075, 0)
    thin = {}                                   # twigs batched into one stroked path per level (one draw call each)
    for lev, a, m, e, w in segs:
        if lev >= 2:
            p_ = thin.get(lev)
            if p_ is None: p_ = thin[lev] = [skia.Path(), w]
            p_[0].moveTo(*a); p_[0].quadTo(m[0], m[1], e[0], e[1])
            continue
        if lev <= 1:
            nx, ny = (e[1] - a[1]), -(e[0] - a[0]); n = math.hypot(nx, ny) or 1; nx, ny = nx / n, ny / n
            w0, w1 = w * 0.5, w * 0.32
            body = poly([(a[0] + nx * w0, a[1] + ny * w0), (m[0] + nx * (w0 + w1) / 2, m[1] + ny * (w0 + w1) / 2),
                         (e[0] + nx * w1, e[1] + ny * w1), (e[0] - nx * w1, e[1] - ny * w1),
                         (m[0] - nx * (w0 + w1) / 2, m[1] - ny * (w0 + w1) / 2), (a[0] - nx * w0, a[1] - ny * w0)])
            pen.fill(body, c)
            if lit: pen.line(poly([(a[0] + nx * w0 * 0.8, a[1] + ny * w0 * 0.8), (e[0] + nx * w1 * 0.8, e[1] + ny * w1 * 0.8)], False),
                             max(1.0, w * 0.12), lit[0], lit[1])
    for lev in sorted(thin):
        pen.line(thin[lev][0], max(0.8, thin[lev][1]), c, 255, cap='round')
    # root flare
    pen.fill(poly([(x - h * 0.09, y + 2), (x - h * 0.03, y - h * 0.08), (x + h * 0.03, y - h * 0.08), (x + h * 0.1, y + 2)]), c)


def _bush(pen, x, y, w, h, seed, c='#0f1a17', hi='#1d2e27', a=255):
    n = 5
    for i in range(n):
        bx = x - w / 2 + w * (i + 0.5) / n + (_h(i, seed) - 0.5) * w * 0.12
        by = y - h * (0.45 + 0.25 * math.sin(math.pi * (i + 0.5) / n))
        pen.fill(_blob(bx, by, w / n * 0.95, h * 0.55, 9, seed + i), c, a)
    for i in range(n):
        bx = x - w / 2 + w * (i + 0.5) / n
        by = y - h * (0.62 + 0.25 * math.sin(math.pi * (i + 0.5) / n))
        pen.fill(_blob(bx - w * 0.02, by, w / n * 0.55, h * 0.22, 7, seed + 20 + i), hi, a * 0.7)


def _window(pen, x, y, w, h, lit=1.0, warm=('#efcf98', '#b8864f'), dark='#121725', trim='#8f8d8c', mull=(1, 1),
            curtain=None, shade=None, glow=True, lw=2.5, sill=True, seed=0, silhouette=None):
    """Window in a wall. lit 0..1 (warm interior light), curtain = hex colour of side curtains, shade = pulled blind
    fraction 0..1, silhouette = (kind) a dark figure standing inside."""
    tw = max(2.0, w * 0.07)
    if glow and lit > 0.05:
        pen.radial(None, x + w / 2, y + h / 2, max(w, h) * 1.25, [(0, warm[1], 70 * lit), (0.5, warm[1], 26 * lit), (1, warm[1], 0)],
                   clip=False)
    frame = rect(x - tw, y - tw, w + 2 * tw, h + 2 * tw)
    pen.shape(frame, trim, lw)
    g = rect(x, y, w, h)
    if lit > 0.05:
        pen.radial(g, x + w * 0.5, y + h * 0.42, max(w, h) * 0.8, [(0, mix(dark, warm[0], lit)), (1, mix(dark, warm[1], lit))])
    else:
        pen.linear(g, x, y, x, y + h, [mix(dark, '#3a4466', 0.35), dark])
        pen.fill(poly([(x, y + h * 0.15), (x + w * 0.35, y), (x + w * 0.55, y), (x, y + h * 0.5)]), '#7f8fb8', 26)
    if silhouette:
        cx = x + w * 0.55
        sil = union(oval(cx, y + h * 0.42, w * 0.13, h * 0.13), rrect(cx - w * 0.22, y + h * 0.55, w * 0.44, h * 0.6, w * 0.15))
        pen.shade(g, sil, '#0b0b10', 235)
    if curtain:
        cw = w * 0.24
        for side in (0, 1):
            cx0 = x if side == 0 else x + w - cw
            cpath = smooth([(cx0, y), (cx0 + cw, y), (cx0 + cw * (0.8 if side == 0 else 0.2) + (cw * 0.15 if side == 0 else -cw * 0.15), y + h * 0.5),
                            (cx0 + cw * (1.0 if side == 0 else 0.0), y + h), (cx0 + (0 if side == 0 else cw), y + h)], True, 0.4)
            pen.fill(cpath, curtain, 235)
            for k in range(3):
                fx = cx0 + cw * (0.25 + 0.25 * k)
                pen.seg((fx, y + 2), (fx + (cw * 0.1 if side == 0 else -cw * 0.1), y + h - 2), max(1.0, w * 0.012), _darken(curtain, 0.35), 160)
    if shade:
        pen.fill(rect(x, y, w, h * shade), mix(warm[1], '#5a4632', 0.5) if lit > 0.05 else '#1a1d28', 235)
        pen.seg((x, y + h * shade), (x + w, y + h * shade), max(1.2, lw * 0.6), trim)
    mx, my = mull
    for i in range(1, mx + 1):
        xx = x + w * i / (mx + 1); pen.seg((xx, y), (xx, y + h), max(1.5, w * 0.035), trim)
    for j in range(1, my + 1):
        yy = y + h * j / (my + 1); pen.seg((x, yy), (x + w, yy), max(1.5, w * 0.035), trim)
    pen.line(g, max(1.0, lw * 0.6), LINE, 200)
    if sill:
        pen.shape(rect(x - tw * 1.6, y + h + tw * 0.6, w + tw * 3.2, tw * 1.1), trim, lw * 0.8)


def _siding(pen, path, x0, y0, x1, y1, step, c='#000000', a=70, hi=None, hia=30):
    pen.cv.save(); pen.cv.clipPath(path, skia.ClipOp.kIntersect, True)
    y = y0 + step
    w = max(0.8, step * 0.09)
    while y < y1:
        pen.seg((x0, y), (x1, y), w, c, a)
        if hi: pen.seg((x0, y + w * 1.2), (x1, y + w * 1.2), w * 0.8, hi, hia)
        y += step
    pen.cv.restore()


def _bricks(pen, path, x0, y0, x1, y1, bh, bw, c='#000000', a=60, seed=0, var=None):
    pen.cv.save(); pen.cv.clipPath(path, skia.ClipOp.kIntersect, True)
    rows = int((y1 - y0) / bh) + 1
    w = max(0.7, bh * 0.12)
    for r in range(rows):
        y = y0 + r * bh
        pen.seg((x0, y), (x1, y), w, c, a)
        off = (bw / 2) if r % 2 else 0.0
        xx = x0 - off
        i = 0
        while xx < x1:
            if var is not None and _h(r * 131 + i, seed) < 0.35:
                pen.fill(rect(xx + w, y + w, bw - w, bh - w), var, 40 + 60 * _h(r * 7 + i, seed + 1))
            pen.seg((xx, y), (xx, y + bh), w, c, a)
            xx += bw; i += 1
    pen.cv.restore()


def _lamp_core(pen, x, y, r, k=1.0, c='#ffcf8a'):
    """A practical light: soft halo + white-hot core (#fff8ee, so the engine blooms it)."""
    if k <= 0.01: return
    pen.glow(x, y, r * 9, c, 70 * k)
    pen.glow(x, y, r * 3.2, c, 150 * k)
    pen.fill(oval(x, y, r), mix('#7a5a30', '#fff8ee', k))


def _streetlamp(pen, x, yb, s, side=1, k=1.0, pool=True):
    """Cobra-head street lamp: pole base (x, yb), s = px per metre; the arm points to `side`."""
    h = 7.2 * s
    pole = rect(x - 0.09 * s, yb - h, 0.18 * s, h)
    pen.fill(pole, '#141822'); pen.seg((x - 0.03 * s, yb - h + 0.3 * s), (x - 0.03 * s, yb - 0.2 * s), 0.05 * s, '#2a3142', 160)
    arm = smooth([(x, yb - h + 0.2 * s), (x + side * 0.8 * s, yb - h - 0.25 * s), (x + side * 1.7 * s, yb - h - 0.15 * s)], False, 0.8)
    pen.line(arm, 0.14 * s, '#141822')
    hx, hy = x + side * 1.85 * s, yb - h - 0.1 * s
    head = smooth([(hx - 0.45 * s, hy - 0.08 * s), (hx + 0.4 * s, hy - 0.12 * s), (hx + 0.45 * s, hy + 0.08 * s), (hx - 0.4 * s, hy + 0.1 * s)], True, 0.6)
    pen.fill(head, '#1b2030')
    if k > 0.01:
        pen.cone(hx, hy + 0.1 * s, 0.7 * s, 5.5 * s, h - 0.1 * s, '#ffd79c', 34 * k, 0.6 * s)
        if pool: pen.radial(None, hx, yb + 0.1 * s, 3.4 * s, [(0, '#ffcf8a', 60 * k), (1, '#ffcf8a', 0)], sy=0.22, clip=False)
        pen.fill(oval(hx, hy + 0.1 * s, 0.32 * s, 0.07 * s), mix('#806040', '#fff8ee', k))
        pen.glow(hx, hy + 0.1 * s, 1.6 * s, '#ffd79c', 120 * k)


# ============================================================== houses
HOUSE_COLS = [('#30364a', '#151a26', '#8c8f99'), ('#3a3436', '#17151a', '#958e88'), ('#2c3838', '#121a1c', '#8a9592'),
              ('#3b3a33', '#18171a', '#97938a'), ('#34314a', '#141323', '#8e8a9c')]


def _house(pen, v, X, D, w, h, roof_h, seed=0, cols=None, porch=True, number=None, lamp=True, lit=(1, 0, 1, 0),
           storeys=1, chimney=True, brick=False, door_c='#4a2c22', garage=False, porch_lamp_k=1.0):
    """A house facade facing the camera, centred at lateral X (m), at depth D (flat facade). w, h, roof_h in metres."""
    s = v.s(D)
    wall, roofc, trim = cols or HOUSE_COLS[seed % len(HOUSE_COLS)]
    gy = v.gy(D)
    gx = v.x(X, D)
    L, R, T = gx - w / 2 * s, gx + w / 2 * s, gy - h * s
    body = rect(L, T, R - L, gy - T)
    pen.linear(body, 0, T, 0, gy, [wall, _darken(wall, 0.25)])
    if brick: _bricks(pen, body, L, T, R, gy, 0.075 * s, 0.24 * s, '#000000', 55, seed, var=_darken(wall, 0.3))
    else: _siding(pen, body, L, T, R, gy, 0.2 * s, '#000000', 65, _lighten(wall, 0.2), 28)
    pen.line(body, max(1.5, 0.05 * s), LINE)
    # roof
    ov = 0.45 * s
    if seed % 2 == 0:
        roof = poly([(L - ov, T + 0.1 * s), (gx, T - roof_h * s), (R + ov, T + 0.1 * s)])
        gable = poly([(L + 0.2 * s, T), (gx, T - roof_h * s + 0.35 * s), (R - 0.2 * s, T)])
        pen.fill(gable, _darken(wall, 0.1))
        _siding(pen, gable, L, T - roof_h * s, R, T, 0.2 * s, '#000000', 50)
        pen.fill(roof, roofc)
        pen.fill(minus(roof, moved(roof, 0, 0.18 * s)), trim, 200)
        pen.line(roof, max(1.2, 0.04 * s), LINE)
        # attic vent
        vx, vy = gx, T - roof_h * s * 0.45
        pen.shape(poly([(vx - 0.35 * s, vy + 0.3 * s), (vx, vy - 0.15 * s), (vx + 0.35 * s, vy + 0.3 * s)]), _darken(wall, 0.35), max(1, 0.03 * s))
    else:
        roof = poly([(L - ov, T + 0.1 * s), (L + w * 0.22 * s, T - roof_h * s), (R - w * 0.22 * s, T - roof_h * s), (R + ov, T + 0.1 * s)])
        pen.fill(roof, roofc)
        for k in range(1, 5):
            yy = T - roof_h * s * k / 5
            pen.seg((L - ov + (L + w * 0.22 * s - L + ov) * k / 5, yy), (R + ov - (R + ov - R + w * 0.22 * s) * k / 5, yy), max(0.8, 0.03 * s), '#000000', 60)
        pen.fill(rect(L - ov, T, R - L + 2 * ov, 0.16 * s), trim, 210)
        pen.line(roof, max(1.2, 0.04 * s), LINE)
    if chimney:
        cxm = gx + w * 0.28 * s * (1 if seed % 3 else -1)
        ch = rect(cxm - 0.35 * s, T - roof_h * s * 0.95, 0.7 * s, roof_h * s * 0.75)
        pen.shape(ch, '#2a2226', max(1, 0.03 * s)); _bricks(pen, ch, cxm - 0.35 * s, T - roof_h * s, cxm + 0.35 * s, T, 0.12 * s, 0.3 * s, '#000000', 60)
        pen.fill(rect(cxm - 0.42 * s, T - roof_h * s * 0.97, 0.84 * s, 0.14 * s), '#1a1518')
    # windows / door
    dw, dh = 0.95 * s, 2.1 * s
    doorx = gx - dw / 2 + (w * 0.18 * s if garage else 0)
    if garage:
        gw = w * 0.36 * s
        gd = rect(L + 0.4 * s, gy - 2.3 * s, gw, 2.3 * s)
        pen.shape(gd, _darken(trim, 0.45), max(1, 0.04 * s))
        for k in range(1, 4): pen.seg((L + 0.4 * s, gy - 2.3 * s * k / 4), (L + 0.4 * s + gw, gy - 2.3 * s * k / 4), max(0.8, 0.03 * s), '#000000', 90)
    wins = []
    lw_ = 1.15 * s; lh_ = 1.25 * s
    slots = [gx - w * 0.33 * s, gx + w * 0.33 * s] if not garage else [gx + w * 0.36 * s]
    for i, wx in enumerate(slots):
        wins.append((wx - lw_ / 2, gy - 2.25 * s, lw_, lh_, lit[i % len(lit)]))
    if storeys > 1:
        for i, wx in enumerate([gx - w * 0.3 * s, gx + w * 0.3 * s]):
            wins.append((wx - lw_ * 0.45, T + 0.6 * s, lw_ * 0.9, lh_ * 0.9, lit[(i + 2) % len(lit)]))
    for i, (wx, wy, ww, wh, lk) in enumerate(wins):
        _window(pen, wx, wy, ww, wh, lit=lk, lw=max(1.2, 0.04 * s), seed=seed + i, curtain='#4a2a2a' if lk and (seed + i) % 2 else None,
                shade=0.3 if lk and (seed + i) % 3 == 0 else None, mull=(1, 1))
    door = rect(doorx, gy - dh, dw, dh)
    pen.shape(rect(doorx - 0.1 * s, gy - dh - 0.1 * s, dw + 0.2 * s, dh + 0.1 * s), trim, max(1, 0.03 * s))
    pen.shape(door, door_c, max(1, 0.03 * s))
    for (py, ph) in ((0.12, 0.35), (0.55, 0.35)):
        pen.line(rect(doorx + dw * 0.15, gy - dh + dh * py, dw * 0.7, dh * ph), max(0.8, 0.025 * s), '#000000', 90)
    pen.fill(oval(doorx + dw * 0.82, gy - dh * 0.48, 0.05 * s), '#c9a64a')
    if lamp:
        lx, ly = doorx + dw + 0.35 * s, gy - dh * 0.85
        pen.radial(None, lx, ly + 0.4 * s, 2.6 * s, [(0, '#ffc98a', 80 * porch_lamp_k), (1, '#ffc98a', 0)], clip=False)
        pen.fill(rrect(lx - 0.1 * s, ly - 0.16 * s, 0.2 * s, 0.32 * s, 0.05 * s), '#1a1612')
        _lamp_core(pen, lx, ly, 0.07 * s, porch_lamp_k)
    if number:
        text(pen.cv, number, doorx - 0.35 * s, gy - dh * 0.7, 800, 0.3 * s, '#d8d0c0', 230)
    if porch:
        pr = rect(L + 0.3 * s, gy - 0.35 * s, R - L - 0.6 * s, 0.35 * s)
        pen.fill(pr, '#1d1c22')
        for k in range(int((R - L) / (0.14 * s))):
            xx = L + 0.4 * s + k * 0.14 * s
            if xx > R - 0.4 * s: break
            if abs(xx - (doorx + dw / 2)) < dw * 0.8: continue
            pen.seg((xx, gy - 1.25 * s), (xx, gy - 0.35 * s), max(0.8, 0.035 * s), trim, 200)
        for side in (-1, 1):
            x_a = doorx + dw / 2 + side * dw * 0.8
            x_b = L + 0.4 * s if side < 0 else R - 0.4 * s
            pen.seg((min(x_a, x_b), gy - 1.25 * s), (max(x_a, x_b), gy - 1.25 * s), max(1.2, 0.07 * s), trim, 230)
    return (L, T, R, gy)


# ============================================================== sprite cache (static artwork drawn once, blitted per frame)
from collections import OrderedDict as _OD
_SPR = _OD()
_SPR_BYTES = [0]
_SPR_LIMIT = int(os.environ.get('POV2_SPRITE_MB', '320')) * 1024 * 1024
_SLIN = skia.SamplingOptions(skia.FilterMode.kLinear)


def _sprite(pen, key, draw_fn, bounds, scale=1.0, alpha=1.0, rot=0.0):
    """Draw draw_fn(pen) (local coordinates inside `bounds` = (x0, y0, x1, y1)) through a cached raster at the current
    device resolution. Call with the canvas translated (not rotated) to the sprite origin; `scale` = extra local scale,
    `rot` (degrees, quantised to 0.25) is baked into the raster so the blit stays axis-aligned (a rotated blit of a
    2 Mpx image costs ~80 ms in skia raster; an axis-aligned one ~10 ms)."""
    cv = pen.cv
    m = cv.getTotalMatrix()
    dev = math.hypot(m.getScaleX(), m.getSkewY()) * abs(scale)
    d = 1.12 ** math.ceil(math.log(max(1e-3, dev * 1.05)) / math.log(1.12))
    rq = round(rot / 0.25) * 0.25
    k = (key, round(d, 4), rq)
    e = _SPR.get(k)
    x0, y0, x1, y1 = bounds
    if rq:
        ca, sa = math.cos(math.radians(rq)), math.sin(math.radians(rq))
        cs = [(x * ca - y * sa, x * sa + y * ca) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        x0, y0 = min(c[0] for c in cs), min(c[1] for c in cs); x1, y1 = max(c[0] for c in cs), max(c[1] for c in cs)
    if e is None:
        w, h = int(math.ceil((x1 - x0) * d)) + 2, int(math.ceil((y1 - y0) * d)) + 2
        arr = np.zeros((h, w, 4), np.uint8)
        srf = surface_for(arr); c2 = srf.getCanvas(); c2.scale(d, d); c2.translate(-x0, -y0)
        if rq: c2.rotate(rq)
        draw_fn(Pen(c2)); del c2, srf
        e = (image_from(arr), arr)
        _SPR[k] = e; _SPR_BYTES[0] += arr.nbytes
        while _SPR_BYTES[0] > _SPR_LIMIT and len(_SPR) > 1:
            _, old = _SPR.popitem(last=False); _SPR_BYTES[0] -= old[1].nbytes
    else:
        _SPR.move_to_end(k)
    cv.save(); cv.scale(scale / d, scale / d)
    p = skia.Paint(AntiAlias=False)
    if alpha < 0.999: p.setAlphaf(max(0.0, alpha))
    cv.drawImage(e[0], x0 * d, y0 * d, _SLIN, p)
    cv.restore()


# ============================================================== patrol car
_CAR_S = 200.0                     # car sprite drawn at length 1000 px (s = 200 px per metre)


def _car_body(pen, s, facing, figures, glare, unit, interior_k):
    """Static artwork of the cruiser (no wheels / lamps / doors): drawn once into a sprite."""
    cv = pen.cv
    cv.save()
    if facing > 0: cv.scale(-1, 1)
    lw = max(1.2, 0.035 * s)

    def P(px_, py_): return (px_ * s, -py_ * s)
    body = smooth([P(-2.52, 0.42), P(-2.55, 0.75), P(-2.35, 0.95), P(-1.1, 1.02), P(-0.45, 1.48), P(0.95, 1.5), P(1.62, 1.04),
                   P(2.45, 1.0), P(2.55, 0.78), P(2.5, 0.4), P(2.1, 0.3), P(1.85, 0.62), P(1.05, 0.62), P(0.85, 0.3),
                   P(-1.15, 0.3), P(-1.35, 0.62), P(-2.15, 0.62), P(-2.3, 0.3)], True, 0.25)
    pen.fill(body, '#101217')
    lower = inter(body, rect(-2.7 * s, -1.0 * s, 5.4 * s, 1.0 * s))
    pen.linear(lower, 0, -1.0 * s, 0, -0.3 * s, ['#2a2f39', '#0d0f13'])
    white = inter(body, poly([P(-1.12, 0.33), P(-1.05, 0.97), P(1.62, 0.99), P(1.66, 0.33)]))
    pen.linear(white, 0, -1.0 * s, 0, -0.33 * s, ['#c9ccd2', '#9ea3ad'])
    glass_f = smooth([P(-0.98, 1.0), P(-0.42, 1.42), P(-0.02, 1.43), P(-0.02, 1.0)], True, 0.15)
    glass_r = smooth([P(0.06, 1.0), P(0.06, 1.43), P(0.88, 1.43), P(1.36, 1.0)], True, 0.15)
    for gpath in (glass_f, glass_r):
        pen.linear(gpath, 0, -1.45 * s, 0, -1.0 * s, ['#1a2133', '#07090d'])
        if interior_k: pen.fill(gpath, '#2a2c33', 120 * interior_k)
    if figures:
        if 'driver' in figures:
            hx, hy = -0.45, 1.2
            pen.shade(glass_f, union(oval(*P(hx, hy), 0.16 * s, 0.19 * s), rrect(*P(hx - 0.32, 1.06), 0.64 * s, 0.4 * s, 0.12 * s)), '#020305', 245)
            pen.shade(glass_f, rrect(*P(hx - 0.22, 1.42), 0.44 * s, 0.1 * s, 0.03 * s), '#020305', 245)
            pen.shade(glass_f, rect(*P(hx - 0.27, 1.34), 0.54 * s, 0.04 * s), '#020305', 245)
        if 'back' in figures:
            hx, hy = 0.62, 1.1
            pen.shade(glass_r, union(oval(*P(hx + 0.06, hy), 0.15 * s, 0.17 * s), rrect(*P(hx - 0.33, 1.02), 0.7 * s, 0.4 * s, 0.14 * s)), '#020305', 240)
        pen.shade(glass_r, rect(*P(0.12, 1.43), 0.05 * s, 0.43 * s), '#16181d', 255)
    for gpath in (glass_f, glass_r):
        pen.shade(gpath, poly([P(-1.2, 1.0), P(-0.9, 1.0), P(0.1, 1.5), P(-0.2, 1.5)]), '#8ea2c8', 40 * glare)
        pen.shade(gpath, poly([P(0.3, 1.0), P(0.42, 1.0), P(1.2, 1.5), P(1.08, 1.5)]), '#8ea2c8', 28 * glare)
    pen.line(glass_f, lw * 0.8, '#05060a'); pen.line(glass_r, lw * 0.8, '#05060a')
    for dx in (-1.05, 0.04, 1.4):
        pen.seg(P(dx, 0.36), P(dx + 0.02, 0.98), lw * 0.7, '#20232b', 255)
    pen.seg(P(-1.05, 0.98), P(1.6, 0.99), lw * 0.7, '#20232b', 200)
    for hx in (-0.35, 0.72):
        pen.fill(rrect(*P(hx, 0.86), 0.26 * s, 0.06 * s, 0.03 * s), '#2a2d33')
    pen.shape(smooth([P(-1.0, 1.02), P(-1.22, 1.1), P(-1.25, 1.2), P(-1.02, 1.17)], True, 0.5), '#101217', lw * 0.6)
    cv.save()
    if facing > 0: cv.scale(-1, 1)
    fx = -1 if facing > 0 else 1
    text(cv, 'POLICE', 0.3 * s * fx, -0.52 * s, 900, 0.3 * s, '#141821', 235, 0.06)
    text(cv, unit, -1.85 * s * fx, -0.72 * s, 800, 0.2 * s, '#e6e8ec', 210)
    cv.restore()
    sh = P(-0.62, 0.72)
    pen.shape(smooth([(sh[0] - 0.12 * s, sh[1] - 0.12 * s), (sh[0] + 0.12 * s, sh[1] - 0.12 * s), (sh[0] + 0.1 * s, sh[1] + 0.06 * s),
                      (sh[0], sh[1] + 0.15 * s), (sh[0] - 0.1 * s, sh[1] + 0.06 * s)], True, 0.3), '#c9a64a', lw * 0.5)
    pen.seg(P(-2.5, 0.62), P(2.5, 0.62), lw * 0.6, '#2c313b', 160)
    pen.line(smooth([P(-2.3, 0.97), P(-1.1, 1.03), P(-0.45, 1.49), P(0.95, 1.51), P(1.62, 1.05), P(2.4, 1.0)], False, 0.25), lw * 0.7, '#4d5566', 170)
    pen.shape(rrect(*P(-2.75, 0.85), 0.28 * s, 0.5 * s, 0.05 * s), '#0b0c0f', lw * 0.6)
    pen.fill(rrect(*P(-2.58, 0.48), 0.14 * s, 0.14 * s, 0.03 * s), '#0b0c0f')
    pen.line(body, lw, LINE)
    # wheel arches (dark wells; wheels themselves are dynamic)
    for wx in (-1.6, 1.45):
        cx_, cy_ = P(wx, 0.36)
        pen.fill(oval(cx_, cy_, 0.4 * s), '#050607')
    # light bar housing + antenna
    pen.fill(rect(*P(-0.2, 1.52), 0.06 * s, 0.05 * s), '#0b0c0f'); pen.fill(rect(*P(0.6, 1.52), 0.06 * s, 0.05 * s), '#0b0c0f')
    bar = rrect(*P(-0.38, 1.62), 1.15 * s, 0.13 * s, 0.05 * s)
    pen.fill(bar, '#16181d'); pen.line(bar, lw * 0.7, LINE)
    pen.seg(P(1.8, 1.0), P(2.05, 1.75), lw * 0.4, '#0b0c0f')
    cv.restore()


def patrol_car(pen, x, y, length, t=0.0, facing=-1, wheel=0.0, bounce=0.0, pitch=0.0, lights=(0.0, 0.0), head=False,
               brake=False, figures=('driver', 'back'), doors=None, interior_k=0.0, glare=0.6, unit='24', dirt=0.0):
    """Police cruiser in side view, black-and-white. (x, y) = centre between the wheels at ground level, `length` = body
    length in design px, facing -1 = nose left, +1 = nose right. wheel = rotation in degrees, bounce (px, down +), pitch
    (deg, nose down +). lights = (red, blue) light bar intensities 0..1 (use lightbar(t)). head = headlights on, brake =
    brake lights. figures: 'driver' (second officer, cap) and/or 'back' (man with lowered head) as dark silhouettes.
    doors = {'rear': 0..1, 'front': 0..1} open amount (door swings toward the camera). The static body is a cached sprite;
    wheels, lamps and doors are drawn live (~5 ms at 2560)."""
    s = length / 5.0
    cv = pen.cv
    doors = doors or {}
    figures = tuple(figures or ())
    pen.radial(None, x, y + 0.04 * s, 2.9 * s, [(0, '#000000', 190), (0.75, '#000000', 120), (1, '#000000', 0)], sy=0.09, clip=False)
    cv.save(); cv.translate(x, y + bounce)
    prot = (pitch if facing > 0 else -pitch) if pitch else 0.0
    _sprite(pen, ('car', facing, figures, round(glare, 2), unit, round(interior_k, 2)),
            lambda p: _car_body(p, _CAR_S, facing, figures, glare, unit, interior_k),
            (-3.0 * _CAR_S, -1.85 * _CAR_S, 3.0 * _CAR_S, 0.1 * _CAR_S), scale=s / _CAR_S, rot=prot)
    if prot: cv.rotate(round(prot / 0.25) * 0.25)
    if facing > 0: cv.scale(-1, 1)
    lw = max(1.2, 0.035 * s)

    def P(px_, py_): return (px_ * s, -py_ * s)
    r_, b_ = lights
    hl = smooth([P(-2.5, 0.84), P(-2.2, 0.86), P(-2.18, 0.74), P(-2.52, 0.72)], True, 0.4)
    pen.fill(hl, mix('#5a5a52', '#fff8ee', 1.0 if head else 0.0))
    tl = smooth([P(2.36, 0.94), P(2.53, 0.92), P(2.55, 0.72), P(2.38, 0.74)], True, 0.4)
    pen.fill(tl, '#ff3a2a' if brake else '#6a1410')
    for wx in (-1.6, 1.45):
        cx_, cy_ = P(wx, 0.36)
        pen.fill(oval(cx_, cy_, 0.36 * s), '#08090b')
        pen.fill(oval(cx_, cy_, 0.22 * s), '#5a606a')
        pen.fill(oval(cx_, cy_, 0.17 * s), '#3a3f48')
        for k in range(5):
            a = math.radians(wheel * (1 if facing < 0 else -1) + k * 72)
            pen.seg((cx_ + math.cos(a) * 0.05 * s, cy_ + math.sin(a) * 0.05 * s), (cx_ + math.cos(a) * 0.2 * s, cy_ + math.sin(a) * 0.2 * s),
                    0.055 * s, '#7c828d', 255)
        pen.fill(oval(cx_, cy_, 0.05 * s), '#9aa0a8')
        pen.line(oval(cx_, cy_, 0.36 * s), lw * 0.8, '#000000', 255)
    def open_door(opening, seat, hinge_x, far_x, top_far, bot_far, light_c):
        # the opening: dark cabin, seat back, the dome light spilling warm onto the seat and sill
        pen.fill(opening, '#050608')
        pen.fill(seat, '#1a1c22')
        ox0, oy0, ox1, oy1 = (lambda b: (b.left(), b.top(), b.right(), b.bottom()))(opening.computeTightBounds())
        cv.save(); cv.clipPath(opening, skia.ClipOp.kIntersect, True)
        pen.radial(None, (ox0 + ox1) / 2, oy0 + (oy1 - oy0) * 0.2, (ox1 - ox0) * 0.9, [(0, light_c, 150), (0.5, light_c, 50), (1, light_c, 0)], clip=False)
        cv.restore()
        # the door panel in perspective: black lower skin, white upper panel, dark window, outline
        def edge(xx, yb, yt, f): return P(xx, yb + (yt - yb) * f)
        hb, ht = 0.33, 1.43
        def band(f0, f1): return poly([edge(hinge_x, hb, ht, f0), edge(hinge_x, hb, ht, f1), edge(far_x, bot_far, top_far, f1), edge(far_x, bot_far, top_far, f0)])
        door = band(0.0, 1.0)
        pen.fill(door, '#0e1015')
        pen.linear(band(0.0, 0.27), 0, -0.33 * s, 0, -0.62 * s, ['#0d0f13', '#2a2f39'])
        pen.linear(band(0.27, 0.61), 0, -0.62 * s, 0, -1.0 * s, ['#9ea3ad', '#c9ccd2'])
        win = band(0.64, 0.96)
        pen.linear(win, 0, -1.0 * s, 0, -1.43 * s, ['#07090d', '#1a2133'])
        pen.shade(win, poly([edge(hinge_x, hb, ht, 0.66), edge(hinge_x, hb, ht, 0.74), edge(far_x, bot_far, top_far, 0.95), edge(far_x, bot_far, top_far, 0.86)]), '#8ea2c8', 50)
        pen.seg(edge(hinge_x, hb, ht, 0.61), edge(far_x, bot_far, top_far, 0.61), lw * 0.7, '#20232b', 255)
        pen.line(win, lw * 0.7, '#05060a')
        hx_, hy_ = edge(hinge_x + (far_x - hinge_x) * 0.8, hb + (bot_far - hb) * 0.8, ht + (top_far - ht) * 0.8, 0.55)   # handle
        pen.fill(rrect(hx_ - 0.1 * s, hy_ - 0.025 * s, 0.2 * s, 0.05 * s, 0.02 * s), '#2a2d33')
        pen.line(door, lw, LINE)
    ro = doors.get('rear', 0.0)
    if ro > 0.01:
        a = ro * 75; k = math.cos(math.radians(a)); grow = 1 + 0.28 * math.sin(math.radians(a))
        far = 0.06 + 1.34 * k
        open_door(poly([P(0.06, 0.33), P(0.06, 1.42), P(0.88, 1.42), P(1.38, 0.99), P(1.4, 0.33)]), rect(*P(0.4, 0.75), 0.9 * s, 0.32 * s),
                  0.06, far, 1.0 + 0.45 * grow, 0.33 - 0.12 * (grow - 1) * 3, '#ffd9a0')
    fo = doors.get('front', 0.0)
    if fo > 0.01:
        a = fo * 70; k = math.cos(math.radians(a)); grow = 1 + 0.28 * math.sin(math.radians(a))
        open_door(poly([P(-1.02, 0.33), P(-1.0, 1.0), P(-0.4, 1.42), P(0.02, 1.42), P(0.02, 0.33)]), rect(*P(-0.8, 0.75), 0.7 * s, 0.32 * s),
                  -1.02, -1.02 + 1.06 * k, 1.0 + 0.45 * grow, 0.3, '#ffd9a0')
    rl = rrect(*P(-0.34, 1.6), 0.5 * s, 0.09 * s, 0.03 * s); bl = rrect(*P(0.23, 1.6), 0.5 * s, 0.09 * s, 0.03 * s)
    pen.fill(rl, mix('#3a0808', '#ff5040', clamp(r_)))
    pen.fill(bl, mix('#08103a', '#5a7cff', clamp(b_)))
    if r_ > 0.6: pen.fill(rrect(*P(-0.25, 1.585), 0.3 * s, 0.05 * s, 0.02 * s), '#fff8ee', 255 * clamp((r_ - 0.6) / 0.4))
    if b_ > 0.6: pen.fill(rrect(*P(0.32, 1.585), 0.3 * s, 0.05 * s, 0.02 * s), '#fff8ee', 255 * clamp((b_ - 0.6) / 0.4))
    cv.restore()
    fx = 1 if facing < 0 else -1
    if head:
        hx_, hy_ = x + (-2.45 * s) * fx, y + bounce - 0.79 * s
        pen.glow(hx_, hy_, 0.6 * s, '#fff1c8', 170)
        L5 = 5.5 * s * fx
        beam = poly([(hx_, hy_ - 0.08 * s), (hx_ - L5, hy_ - 0.5 * s), (hx_ - L5, hy_ + 0.75 * s), (hx_, hy_ + 0.1 * s)])
        pen.linear(beam, hx_, 0, hx_ - L5, 0, [(0, '#fff1c8', 110), (0.5, '#fff1c8', 36), (1, '#fff1c8', 0)])
    if brake:
        pen.glow(x + 2.46 * s * fx, y + bounce - 0.83 * s, 0.7 * s, '#ff3020', 160)
    gx_r = x + (-0.09 * s) * fx; gx_b = x + (0.48 * s) * fx
    gy_ = y + bounce - 1.555 * s
    gr = min(2.6 * s, 300.0)
    if r_ > 0.04:
        pen.radial(None, gx_r, gy_, gr, [(0, '#ff2a2a', 170 * clamp(r_)), (0.18, '#ff2020', 90 * clamp(r_)), (1, '#ff2020', 0)], clip=False)
    if b_ > 0.04:
        pen.radial(None, gx_b, gy_, gr, [(0, '#3a5cff', 170 * clamp(b_)), (0.18, '#2a4cff', 90 * clamp(b_)), (1, '#2a4cff', 0)], clip=False)


def _sedan(pen, x, y, length, c='#2a3040', facing=1, lit=0.0, seed=0):
    """Parked civilian car (static, side view), (x, y) = ground centre. lit = interior dome light 0..1."""
    s = length / 4.6
    cv = pen.cv; cv.save(); cv.translate(x, y)
    if facing > 0: cv.scale(-1, 1)
    def P(a, b): return (a * s, -b * s)
    pen.radial(None, 0, 0.03 * s, 2.6 * s, [(0, '#000000', 170), (1, '#000000', 0)], sy=0.08, clip=False)
    body = smooth([P(-2.3, 0.35), P(-2.32, 0.7), P(-2.0, 0.85), P(-0.9, 0.92), P(-0.4, 1.35), P(0.8, 1.37), P(1.4, 0.95), P(2.25, 0.88),
                   P(2.32, 0.6), P(2.28, 0.32), P(1.9, 0.28), P(1.7, 0.55), P(0.95, 0.55), P(0.75, 0.28), P(-1.05, 0.28), P(-1.25, 0.55),
                   P(-1.95, 0.55), P(-2.1, 0.3)], True, 0.25)
    pen.fill(body, c)
    pen.linear(inter(body, rect(-2.5 * s, -0.95 * s, 5 * s, 0.6 * s)), 0, -0.95 * s, 0, -0.35 * s, [_lighten(c, 0.12), _darken(c, 0.3)])
    gl = smooth([P(-0.82, 0.92), P(-0.36, 1.3), P(0.75, 1.31), P(1.25, 0.92)], True, 0.15)
    pen.linear(gl, 0, -1.3 * s, 0, -0.92 * s, ['#1e2638', '#090b10'])
    if lit: pen.fill(gl, '#e8c890', 90 * lit)
    pen.shade(gl, poly([P(-0.6, 0.92), P(-0.45, 0.92), P(0.2, 1.4), P(0.05, 1.4)]), '#8ea2c8', 40)
    pen.seg(P(0.2, 0.92), P(0.22, 1.32), max(1.5, 0.05 * s), c)
    pen.seg(P(-0.95, 0.4), P(2.1, 0.62), max(1, 0.02 * s), _lighten(c, 0.25), 90)
    pen.line(body, max(1.2, 0.03 * s), LINE)
    for wx in (-1.5, 1.35):
        cx_, cy_ = P(wx, 0.32)
        pen.fill(oval(cx_, cy_, 0.32 * s), '#08090b'); pen.fill(oval(cx_, cy_, 0.18 * s), '#4a4e56'); pen.fill(oval(cx_, cy_, 0.06 * s), '#8a8e96')
    pen.fill(smooth([P(2.2, 0.82), P(2.31, 0.8), P(2.3, 0.65), P(2.2, 0.66)], True, 0.4), '#5a1410')
    pen.fill(smooth([P(-2.25, 0.78), P(-2.05, 0.8), P(-2.05, 0.68), P(-2.28, 0.66)], True, 0.4), '#6a6a62')
    cv.restore()


def _police_pool(pen, x, y, s, lights, ry=0.18, k=1.0):
    """Red/blue light pool on the ground around a car at (x, y) (s = px per metre)."""
    r_, b_ = lights
    rr = min(5.0 * s, 560.0)
    if r_ > 0.05: pen.radial(None, x - 0.6 * s, y, rr, [(0, '#ff2020', 80 * r_ * k), (0.5, '#ff2020', 26 * r_ * k), (1, '#ff2020', 0)], sy=ry, clip=False)
    if b_ > 0.05: pen.radial(None, x + 0.6 * s, y, rr, [(0, '#2a4cff', 80 * b_ * k), (0.5, '#2a4cff', 26 * b_ * k), (1, '#2a4cff', 0)], sy=ry, clip=False)


# ============================================================== animated bits
def draw_moths(pen, t, x, y, r=60.0, n=5, seed=0, size=5.0, c='#d9cbb0', a=230):
    """Moths circling a light at (x, y): erratic orbits within radius r, flapping wings, hitting the lamp now and then."""
    for i in range(n):
        ph = _h(i, seed) * 50
        sp = 0.9 + 0.8 * _h(i, seed + 1)
        ang = t * sp * 2.4 + ph
        rr = r * (0.35 + 0.65 * (0.5 + 0.5 * noise1(t * 0.9 + ph, seed + i)))
        mx = x + math.cos(ang) * rr + r * 0.25 * noise1(t * 3.1 + ph, seed + 30 + i)
        my = y + math.sin(ang * 1.3) * rr * 0.65 + r * 0.25 * noise1(t * 2.7 + ph, seed + 60 + i)
        flap = abs(math.sin(t * (38 + 9 * _h(i, seed + 2)) + ph))
        sz = size * (0.8 + 0.5 * _h(i, seed + 3))
        wing = sz * (0.35 + 0.65 * flap)
        heading = math.atan2(math.cos(ang * 1.3) * 1.3 * 0.65, -math.sin(ang)) if True else 0
        ca, sa = math.cos(heading), math.sin(heading)
        for side in (-1, 1):
            wx, wy = -sa * side * wing, ca * side * wing
            pen.fill(poly([(mx, my), (mx + wx + ca * sz * 0.5, my + wy + sa * sz * 0.5), (mx + wx - ca * sz * 0.6, my + wy - sa * sz * 0.6)]), c, a * 0.85)
        pen.fill(oval(mx, my, sz * 0.28), mix(c, '#3a3024', 0.4), a)


def _mist(pen, t, y, w_x0, w_x1, h, n=6, seed=0, a=26, c='#a9b6d6', speed=14.0):
    """Low drifting mist bands centred on y (cheap radial ellipses)."""
    span = w_x1 - w_x0
    for i in range(n):
        rx = span / n * 0.9 * (0.8 + 0.4 * _h(i, seed))
        x = w_x0 + ((i + _h(i, seed + 1)) * span / n + t * speed * (0.6 + 0.8 * _h(i, seed + 2))) % (span + rx) - rx * 0.5
        yy = y + (_h(i, seed + 3) - 0.5) * h * 0.8
        pen.radial(None, x, yy, rx, [(0, c, a * (0.7 + 0.6 * _h(i, seed + 4))), (0.6, c, a * 0.35), (1, c, 0)], sy=h / rx * 0.9, clip=False)


def _lv(x):
    """Spill level from a light-bar intensity: 0 below the beacon's idle glow (so spill layers are skipped while dark)."""
    return clamp((x - 0.15) / 0.85)


def _combine(*fns):
    def draw(pen, t):
        for f in fns: f(pen, t)
    return draw


def _ubox(*bs):
    return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))


def _spill_pair(depth, draw_geom, key, bounds, lights_fn, kr=0.55, kb=0.6, name='spill'):
    """Two cached layers holding a surface's silhouette in red and blue light; their alpha follows lights_fn(t) (a layer
    is skipped entirely while its colour is off, so a sweeping light bar costs one layer at a time)."""
    def dr(pen, t): draw_geom(pen, '#ff2a20')
    def db(pen, t): draw_geom(pen, '#3a5cff')
    return [Layer(depth, dr, name + '_r', cache=key + ':r', bounds=bounds, alpha=lambda t: kr * _lv(lights_fn(t)[0]), blur=0),
            Layer(depth, db, name + '_b', cache=key + ':b', bounds=bounds, alpha=lambda t: kb * _lv(lights_fn(t)[1]), blur=0)]


# ============================================================== the street world (shared by porch views)
def _sky_draw(v, box, moon=(1560, 170, 34), seed=3, clouds=((420, 120, 760, 46), (1250, 60, 900, 40), (2250, 150, 700, 40)),
              stars=300, glow='#2b2c58', tod='night'):
    """Night sky (police) or tod='dawn': 6:12 sunrise (deep blue overhead -> lilac -> peach -> a hot band at the horizon,
    sun glow low on the right, pink-lit clouds, no stars, a faint daytime moon)."""
    x0, y0, x1, y1 = box

    def draw(pen, t):
        hz = v.h
        if tod == 'dawn':
            pen.linear(rect(x0, y0, x1 - x0, y1 - y0), 0, y0, 0, hz + 60,
                       [(0, '#1d2a52'), (0.38, '#4a4f86'), (0.62, '#9a7fa6'), (0.82, '#e8a88a'), (0.95, '#ffd09a'), (1, '#ffe2b0')])
            pen.radial(None, x0 + (x1 - x0) * 0.78, hz + 40, (x1 - x0) * 0.32, [(0, '#fff2cc', 230), (0.25, '#ffc888', 120),
                                                                                  (1, '#ffb070', 0)], sy=0.55, clip=False)
            if moon: pen.fill(oval(moon[0], moon[1], moon[2] * 0.8), '#e8e4f2', 70)
            for i, (cx, cy, w, h) in enumerate(clouds):
                _cloud(pen, cx, cy, w, h, seed + i, '#6a5a86', '#ffb898', 200)
            return
        pen.linear(rect(x0, y0, x1 - x0, y1 - y0), 0, y0, 0, hz + 80,
                   [(0, '#02040a'), (0.45, '#07102a'), (0.8, '#142048'), (1, glow)])
        _stars(pen, (x0, y0, x1, y1), stars, seed, hz - 40)
        pen.radial(None, (x0 + x1) / 2, hz + 60, (x1 - x0) * 0.6, [(0, '#3a2f5a', 60), (1, '#3a2f5a', 0)], sy=0.18, clip=False)
        if moon: _moon(pen, *moon)
        for i, (cx, cy, w, h) in enumerate(clouds): _cloud(pen, cx, cy, w, h, seed + i)
    return draw


def _far_draw(v, D, x_range, seed=5):
    """Distant tree line + roofs at depth D."""
    def draw(pen, t):
        s = v.s(D); gy = v.gy(D)
        X0, X1 = x_range
        rng = np.random.default_rng(seed)
        pts = [(v.x(X0, D), gy + 10)]
        X = X0
        while X < X1:
            h = rng.uniform(7, 15)
            pts.append((v.x(X, D), gy - h * s)); X += rng.uniform(2.0, 4.5)
        pts.append((v.x(X1, D), gy + 10))
        pen.fill(smooth(pts, True, 0.7), '#080b16')
        X = X0 + 3
        while X < X1:
            w = rng.uniform(8, 12); h = rng.uniform(3, 4.5); rh = rng.uniform(1.8, 3.0)
            L, R = v.x(X, D), v.x(X + w, D)
            pen.fill(poly([(L, gy), (L, gy - h * s), ((L + R) / 2, gy - (h + rh) * s), (R, gy - h * s), (R, gy)]), '#0a0e1b')
            if rng.uniform() < 0.6:
                wx = L + (R - L) * rng.uniform(0.2, 0.7)
                pen.fill(rect(wx, gy - h * s * 0.6, 0.9 * s, 0.9 * s), '#c89b62', 200)
                pen.glow(wx + 0.45 * s, gy - h * s * 0.55, 3 * s, '#c89b62', 40)
            X += w + rng.uniform(4, 9)
    return draw


def _houses_draw(v, D, xs, seed=0, lamps=(), lit=None, porch_k=1.0):
    """Row of houses facing the camera at depth D; xs = lateral centres (m). lit = f(i) -> window lit tuple (default: the
    police film's 12:36 AM pattern); porch_k scales their porch lamps (0 = off, e.g. at dawn)."""
    def draw(pen, t):
        s = v.s(D); gy = v.gy(D)
        X0 = xs[0] - 12; X1 = xs[-1] + 12
        # far lawns + trees behind
        for i, X in enumerate(xs[:-1]):
            mid = (X + xs[i + 1]) / 2
            draw_tree(pen, v.x(mid + 0.5, D + 1), v.gy(D + 1), 9.0 * v.s(D + 1), 0.0, seed + 40 + i, 0.0, '#090c15', ('#4a5a88', 70), 5)
        pen.fill(rect(v.x(X0, D), gy - 2, v.x(X1, D) - v.x(X0, D), v.gy(6.1) - gy + 4), '#0d1414')
        for i, X in enumerate(xs):
            w = 9.5 + 2.5 * _h(i, seed); h = 3.0 + (0.4 if i % 3 == 1 else 0.0) + (2.6 if i % 4 == 2 else 0)
            lt = lit(i) if lit else (1 if i % 2 == 0 else 0.8, 0 if i % 3 else 0.6, 0.9, 0)
            _house(pen, v, X, D, w, h, 2.2 + 0.6 * _h(i, seed + 1), seed=seed + i, storeys=2 if h > 5 else 1,
                   lit=lt, garage=(i % 3 == 2), number=str(141 + 2 * i) if i % 2 else None, porch_lamp_k=porch_k)
            # walkway + bushes
            gx = v.x(X, D)
            pen.fill(poly([(gx - 0.5 * s, gy), (gx + 0.5 * s, gy), (gx + 0.6 * v.s(6.1), v.gy(6.1)), (gx - 0.6 * v.s(6.1), v.gy(6.1))]), '#262830')
            for side in (-1, 1):
                _bush(pen, gx + side * (w * 0.3) * s, gy + 0.1 * s, 2.6 * s, 1.1 * s, seed + 7 * i + side, '#0b1512', '#16261f')
        # far sidewalk
        y_a, y_b = v.gy(6.1), v.gy(5.7)
        pen.fill(rect(v.x(X0, D), y_a, v.x(X1, D) - v.x(X0, D), y_b - y_a + 1), '#2a2c33')
        for k in range(-40, 40):
            xx = v.x(k * 1.6, 5.9); pen.seg((xx, y_a), (xx, y_b), 1.0, '#15171c', 160)
    return draw


def _lamps_draw(v, D, Xs, k=1.0):
    def draw(pen, t):
        for i, X in enumerate(Xs):
            _streetlamp(pen, v.x(X, D), v.gy(D), v.s(D), side=1 if X < 0 else -1, k=k)
    return draw


def _street_draw(v, x_range, d_curb=4.55, d_far=5.7, seed=1):
    def draw(pen, t):
        X0, X1 = x_range
        ya, yb = v.gy(d_far), v.gy(d_curb)
        xl, xr = -1000, 2920
        road = rect(xl, ya, xr - xl, yb - ya)
        pen.linear(road, 0, ya, 0, yb, ['#15171d', '#1b1d24'])
        pen.texture(road, 'asphalt', 0.35, 'overlay', 0.6)
        # lane line (dashed, faded) + patch work
        dm = (d_curb + d_far) / 2
        ym = v.gy(dm)
        for kx in range(-30, 30):
            xa, xb = v.x(kx * 3.0, dm), v.x(kx * 3.0 + 1.6, dm)
            pen.fill(poly([(xa, ym - 1.4), (xb, ym - 1.4), (xb, ym + 1.4), (xa, ym + 1.4)]), '#8a7a4a', 120)
        for kx in (-7, 3, 12):
            pen.fill(oval(v.x(kx, 5.3), v.gy(5.3), 0.5 * v.s(5.3), 0.09 * v.s(5.3)), '#101216')
            pen.line(oval(v.x(kx, 5.3), v.gy(5.3), 0.5 * v.s(5.3), 0.09 * v.s(5.3)), 1.2, '#2c2f37', 200)
        # near curb + sidewalk
        yc = v.gy(d_curb); yc2 = v.y(v.ground + 0.15, d_curb)
        pen.fill(rect(xl, yc2, xr - xl, yc - yc2 + 1), '#3b3d44')
        pen.fill(rect(xl, yc, xr - xl, 1.5), '#0b0c10')
        y_w0, y_w1 = v.y(v.ground + 0.15, d_curb), v.y(v.ground + 0.15, 4.2)
        walk = rect(xl, y_w0, xr - xl, y_w1 - y_w0)
        pen.linear(walk, 0, y_w0, 0, y_w1, ['#30323a', '#3a3c44'])
        pen.texture(walk, 'plaster', 0.4, 'overlay', 0.8)
        for kx in range(-40, 40):
            xa, xb = v.x(kx * 1.5, d_curb), v.x(kx * 1.5, 4.2)
            pen.seg((xa, y_w0), (xb, y_w1), 1.2, '#1a1b20', 170)
        # far curb face
        pen.fill(rect(xl, ya - 2, xr - xl, 3), '#4a4c55')
        # parked cars along the far curb
        for (X, c, f) in ((-9.5, '#3a2a2e', -1), (13.0, '#2a3a3a', -1), (-22.0, '#30343e', -1)):
            D = d_far - 0.25
            _sedan(pen, v.x(X, D), v.gy(D), 4.6 * v.s(D), c, f)
    return draw


def _yard_draw(v, d0=2.0, d1=4.2, path_w=0.6, mailbox=(1.15, 4.0), seed=2, hedge=True, lights=True):
    def draw(pen, t):
        xl, xr = -1000, 2920
        ya, yb = v.y(v.ground + 0.15, d1), v.gy(d0)
        lawn = rect(xl, ya, xr - xl, yb - ya + 60)
        pen.linear(lawn, 0, ya, 0, yb, ['#0f1a17', '#12201b', '#0c1512'])
        pen.texture(lawn, 'fabric', 0.25, 'overlay', 0.5)
        rng = np.random.default_rng(seed)
        for _ in range(900):                                           # grass tufts
            D = rng.uniform(d0, d1); X = rng.uniform(-14, 14)
            x, y = v.x(X, D), v.gy(D); s = v.s(D)
            h = rng.uniform(0.05, 0.12) * s
            pen.seg((x, y), (x + rng.uniform(-0.3, 0.3) * h, y - h), max(0.7, 0.012 * s), '#1d3329' if rng.uniform() < 0.5 else '#0a120f', 200)
        # path (slabs)
        pts = [v.p(-path_w, v.ground, d0), v.p(path_w, v.ground, d0), v.p(path_w, v.ground, d1), v.p(-path_w, v.ground, d1)]
        path = poly(pts)
        pen.linear(path, 0, ya, 0, yb, ['#34353c', '#4a4a50'])
        pen.texture(path, 'plaster', 0.5, 'overlay', 0.7)
        D = d0
        while D < d1:
            pen.seg(v.p(-path_w, v.ground, D), v.p(path_w, v.ground, D), max(0.8, 0.02 * v.s(D)), '#1b1c21', 220)
            D += 0.38
        pen.line(path, 1.2, '#15161a', 200)
        # flower beds along the path + solar path lights
        for side in (-1, 1):
            for i in range(5):
                D = d0 + 0.25 + i * (d1 - d0 - 0.4) / 5
                x, y = v.p(side * (path_w + 0.35), v.ground, D); s = v.s(D)
                _bush(pen, x, y + 0.05 * s, 0.75 * s, 0.4 * s, seed * 10 + i + (side > 0) * 50, '#0e1a14', '#1c2e22')
                for f in range(3):
                    fx = x + (_h(i * 3 + f, seed + side) - 0.5) * 0.6 * s; fy = y - (0.25 + 0.1 * _h(f, i)) * s
                    pen.fill(oval(fx, fy, 0.045 * s), ['#6a3a52', '#7a6a8a', '#5a2a3a'][f % 3], 220)
            if lights:
                for i in range(3):
                    D = d0 + 0.5 + i * 0.6
                    x, y = v.p(side * (path_w + 0.12), v.ground, D); s = v.s(D)
                    pen.fill(rect(x - 0.015 * s, y - 0.32 * s, 0.03 * s, 0.32 * s), '#141414')
                    pen.radial(None, x, y + 0.02 * s, 0.6 * s, [(0, '#e9d7a8', 70), (1, '#e9d7a8', 0)], sy=0.3, clip=False)
                    pen.fill(rrect(x - 0.05 * s, y - 0.4 * s, 0.1 * s, 0.09 * s, 0.02 * s), '#e9dcc0', 230)
                    pen.glow(x, y - 0.35 * s, 0.25 * s, '#f4e3b8', 120)
        if hedge:
            for side in (-1, 1):
                for i in range(7):
                    D = d0 + 0.15 + i * (d1 - d0) / 7
                    x, y = v.p(side * 5.6, v.ground, D); s = v.s(D)
                    _bush(pen, x, y, 1.7 * s, 1.2 * s, seed + 90 + i * 2 + (side > 0), '#0b1511', '#15241c')
        if mailbox:
            X, D = mailbox
            x, y = v.p(X, v.ground, D); s = v.s(D)
            pen.shape(rect(x - 0.05 * s, y - 1.05 * s, 0.1 * s, 1.05 * s), '#2a2420', max(1, 0.02 * s))
            box = union(rect(x - 0.28 * s, y - 1.25 * s, 0.56 * s, 0.14 * s), oval(x, y - 1.25 * s, 0.28 * s, 0.17 * s))
            box = inter(box, rect(x - 0.3 * s, y - 1.45 * s, 0.6 * s, 0.35 * s))
            pen.shape(box, '#16181e', max(1, 0.02 * s))
            pen.fill(rect(x - 0.25 * s, y - 1.37 * s, 0.5 * s, 0.03 * s), '#3a3f4c', 180)
            pen.shape(rect(x + 0.2 * s, y - 1.45 * s, 0.04 * s, 0.22 * s), '#a3262a', max(0.8, 0.015 * s))
            text(pen.cv, '144', x, y - 1.15 * s, 800, 0.11 * s, '#cfc8b8', 220)
    return draw


def _porch_floor_draw(v, d_near=0.3, d_edge=1.8, half=2.9, mat=True, pool=None):
    def draw(pen, t):
        floor = v.quad([(-half, 0, d_near), (half, 0, d_near), (half, 0, d_edge), (-half, 0, d_edge)])
        y0, y1 = v.y(0, d_edge), v.y(0, d_near)
        pen.linear(floor, 0, y0, 0, y1, ['#3a2b20', '#2e2219', '#1d1611'])
        pen.texture(floor, 'wood', 0.4, 'overlay', 1.4, 90)
        X = -half
        i = 0
        while X <= half + 1e-6:
            pen.seg(v.p(X, 0, d_near), v.p(X, 0, d_edge), max(1.0, 0.012 * v.s(d_near)), '#120c09', 200)
            if i % 3 == 1:
                D = 0.5 + 1.2 * _h(i, 4)
                pen.seg(v.p(X, 0, D), v.p(X + 0.1, 0, D), max(0.8, 0.01 * v.s(D)), '#120c09', 170)
            X += 0.1; i += 1
        # front edge nosing
        pen.fill(v.quad([(-half, 0, d_edge - 0.03), (half, 0, d_edge - 0.03), (half, -0.06, d_edge), (-half, -0.06, d_edge)]), '#4a3a2c')
        if mat:
            mpath = v.quad([(-0.45, 0.01, 0.42), (0.45, 0.01, 0.42), (0.45, 0.01, 0.78), (-0.45, 0.01, 0.78)])
            pen.shape(mpath, '#4a3a26', 2.5)
            pen.texture(mpath, 'fabric', 0.6, 'overlay', 1.5)
            inner = v.quad([(-0.36, 0.01, 0.46), (0.36, 0.01, 0.46), (0.36, 0.01, 0.72), (-0.36, 0.01, 0.72)])
            pen.line(inner, 3, '#2a1f14', 220)
            xh, yh = v.p(0, 0.01, 0.6)
            cv = pen.cv; cv.save(); cv.translate(xh, yh); cv.scale(1.0, 0.45)
            text(cv, 'HOME', 0, 0.06 * v.s(0.6), 900, 0.13 * v.s(0.6), '#20160d', 200, 0.12)
            cv.restore()
        if pool:
            X, D, r = pool
            x, y = v.p(X, 0, D)
            pen.radial(None, x, y, r * v.s(D), [(0, '#ffcf8f', 60), (0.5, '#ffcf8f', 22), (1, '#ffcf8f', 0)], sy=0.32, clip=False)
    return draw


def _railing_geom(v, D, segs, h=0.95, step=0.13, bal_w=0.045, Y0=0.0):
    """Paths for a white porch railing at depth D: segs = [(X0, X1), ...]. Returns (rails, balusters) path lists."""
    rails, bals = [], []
    s = v.s(D)
    for (X0, X1) in segs:
        rails.append(rect(v.x(X0, D), v.y(Y0 + h, D), (X1 - X0) * s, 0.085 * s))
        rails.append(rect(v.x(X0, D), v.y(Y0 + 0.12, D), (X1 - X0) * s, 0.06 * s))
        n = int((X1 - X0) / step)
        for k in range(1, n):
            X = X0 + k * (X1 - X0) / n
            bals.append(rect(v.x(X, D) - bal_w / 2 * s, v.y(Y0 + h, D), bal_w * s, (h - 0.06) * s))
    return rails, bals


def _post(v, X, D, h, w=0.18, Y0=0.0):
    s = v.s(D)
    return rect(v.x(X, D) - w / 2 * s, v.y(Y0 + h, D), w * s, h * s)


def _porch_front_draw(v, D=1.8, half=2.9, gap=0.8, lamp_x=-0.85, plants=True, light_x=None):
    def draw(pen, t):
        s = v.s(D)
        trim, trim_sh = '#c9c2b4', '#8b8a90'
        lx = v.x(lamp_x, D)
        def tcol(x):                                # warm near the lantern, cooler away from it
            k = clamp(abs(x - lx) / (6.0 * s))
            return mix('#d8cdb6', '#7d7f8c', k)
        # handrails down the steps
        for side in (-1, 1):
            X = side * (gap + 0.05)
            a = v.p(X, 0.9, D); b = v.p(X, v.ground + 0.85, D + 0.75)
            pen.line(poly([a, b], False), max(2, 0.06 * s), '#151515')
            pen.line(poly([a, b], False), max(1, 0.03 * s), '#5c5a5a')
            for k in range(1, 4):
                u = k / 4
                p0 = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
                pen.seg(p0, (p0[0], p0[1] + 0.8 * v.s(D + 0.75 * u)), max(1, 0.03 * s), '#bdb6aa', 200)
        rails, bals = _railing_geom(v, D, [(-half, -gap), (gap, half)])
        for b in bals:
            c = tcol(b.getBounds().centerX())
            pen.fill(b, c); pen.fill(rect(b.getBounds().left(), b.getBounds().top(), b.getBounds().width() * 0.35, b.getBounds().height()), _darken(c, 0.25))
            pen.line(b, max(0.8, 0.012 * s), LINE, 230)
        for r in rails:
            pen.linear(r, v.x(-half, D), 0, v.x(half, D), 0, [tcol(v.x(-half, D)), tcol(lx), tcol(v.x(half, D))])
            pen.line(r, max(1, 0.015 * s), LINE)
        # posts (newels at the steps, corners) with caps
        for X, h in ((-half, 1.05), (-gap, 1.1), (gap, 1.1), (half, 1.05)):
            p = _post(v, X, D, h, 0.16)
            c = tcol(v.x(X, D))
            pen.fill(p, c); pen.fill(rect(p.getBounds().right() - p.getBounds().width() * 0.35, p.getBounds().top(), p.getBounds().width() * 0.35,
                                          p.getBounds().height()), _darken(c, 0.3))
            pen.line(p, max(1, 0.015 * s), LINE)
            cap = rect(v.x(X, D) - 0.12 * s, v.y(h + 0.05, D), 0.24 * s, 0.06 * s)
            pen.shape(cap, c, max(1, 0.012 * s))
        # lamp post
        pp = _post(v, lamp_x, D, 1.75, 0.07)
        pen.shape(pp, '#141414', max(1, 0.012 * s))
        if plants:
            for side in (-1, 1):
                X = side * (gap + 0.45)
                x, y = v.p(X, 0, D - 0.12); ss = v.s(D - 0.12)
                pot = poly([(x - 0.17 * ss, y - 0.36 * ss), (x + 0.17 * ss, y - 0.36 * ss), (x + 0.12 * ss, y), (x - 0.12 * ss, y)])
                pen.shape(pot, '#5a3428', max(1, 0.012 * ss))
                pen.fill(rect(x - 0.19 * ss, y - 0.4 * ss, 0.38 * ss, 0.06 * ss), '#6a3e30')
                for k in range(9):
                    a = -math.pi / 2 + (k - 4) * 0.32
                    ln = (0.42 + 0.18 * _h(k, side + 5)) * ss
                    tip = (x + math.cos(a) * ln, y - 0.38 * ss + math.sin(a) * ln)
                    leaf = smooth([(x, y - 0.38 * ss), ((x + tip[0]) / 2 + 0.05 * ss, (y - 0.38 * ss + tip[1]) / 2), tip,
                                   ((x + tip[0]) / 2 - 0.05 * ss, (y - 0.38 * ss + tip[1]) / 2)], True, 0.8)
                    pen.fill(leaf, '#1d3a2a' if k % 2 else '#16301f')
                    pen.line(leaf, max(0.8, 0.008 * ss), '#0a140e', 200)
    return draw


def _porch_front_spill(v, D=1.8, half=2.9, gap=0.8):
    def geom(pen, c):
        s = v.s(D)
        rails, bals = _railing_geom(v, D, [(-half, -gap), (gap, half)])
        for p in rails + bals: pen.fill(p, c)
        for X, h in ((-half, 1.05), (-gap, 1.1), (gap, 1.1), (half, 1.05)): pen.fill(_post(v, X, D, h, 0.16), c)
    return geom


def _porch_sides_draw(v, d0=0.55, d1=1.8, half=2.9, portico=True):
    def draw(pen, t):
        for side in (-1, 1):
            X = side * half
            top0, top1 = v.p(X, 0.95, d0), v.p(X, 0.95, d1)
            bot0, bot1 = v.p(X, 0.0, d0), v.p(X, 0.0, d1)
            n = 12
            for k in range(n + 1):
                D = d0 + (d1 - d0) * k / n
                a, b = v.p(X, 0.9, D), v.p(X, 0.1, D)
                w = max(2, 0.05 * v.s(D))
                pen.seg(a, b, w + 2, LINE, 230); pen.seg(a, b, w, mix('#b8b0a2', '#6a6c78', 0.3 + 0.5 * (1 - k / n)))
            pen.line(poly([top0, top1], False), max(4, 0.09 * v.s(d0)), LINE)
            pen.line(poly([top0, top1], False), max(3, 0.07 * v.s(d0)), '#9a958c')
            pen.line(poly([bot0, bot1], False), max(3, 0.06 * v.s(d0)), '#6f6c6c')
            # floor beyond the railing (porch skirt and yard)
            pen.fill(poly([bot0, bot1, (bot1[0] + side * 3000, bot1[1]), (bot0[0] + side * 3000, bot0[1])]), '#0c1210')
        if portico:
            s = v.s(0.95)
            band = rect(-1000, v.y(2.75, 0.95), 3920, 0.32 * s)
            pen.fill(rect(-1000, -1200, 3920, v.y(2.75, 0.95) + 1200), '#141012')
            pen.texture(rect(-1000, -1200, 3920, v.y(2.75, 0.95) + 1200), 'wood', 0.35, 'overlay', 1.2)
            pen.linear(band, 0, band.getBounds().top(), 0, band.getBounds().bottom(), ['#5a5650', '#8a8076'])
            pen.line(band, 3, LINE)
    return draw


def _chair_draw(v, X=1.75, D=1.3):
    def draw(pen, t):
        s = v.s(D); x, y = v.p(X, 0, D)
        c, cd = '#8a6a48', '#4a3626'
        back = smooth([(x - 0.32 * s, y - 0.45 * s), (x - 0.34 * s, y - 1.0 * s), (x, y - 1.08 * s), (x + 0.3 * s, y - 1.0 * s), (x + 0.28 * s, y - 0.45 * s)], True, 0.5)
        pen.shape(back, c, max(1.5, 0.02 * s))
        pen.texture(back, 'fabric', 0.5, 'overlay', 0.6)
        for k in range(5):
            xx = x - 0.24 * s + k * 0.12 * s
            pen.seg((xx, y - 0.48 * s), (xx, y - 0.98 * s), max(1, 0.012 * s), cd, 200)
        seat = poly([(x - 0.38 * s, y - 0.45 * s), (x + 0.36 * s, y - 0.45 * s), (x + 0.42 * s, y - 0.38 * s), (x - 0.44 * s, y - 0.38 * s)])
        pen.shape(seat, _lighten(c, 0.1), max(1.5, 0.02 * s))
        pen.shape(rrect(x - 0.36 * s, y - 0.42 * s, 0.72 * s, 0.1 * s, 0.04 * s), '#6a4a4a', max(1, 0.015 * s))   # cushion
        for lx_ in (-0.36, 0.32):
            pen.seg((x + lx_ * s, y - 0.38 * s), (x + lx_ * s * 1.05, y), max(2, 0.035 * s), cd)
        rock = smooth([(x - 0.5 * s, y - 0.03 * s), (x, y + 0.02 * s), (x + 0.5 * s, y - 0.05 * s)], False, 0.8)
        pen.line(rock, max(2, 0.03 * s), cd)
    return draw


def _lantern(pen, x, y, s, k=1.0, glass='#ffd9a0', glow=True):
    """Coach lantern on a post top (x, y = bottom centre of the lantern), s = px per metre."""
    w, h = 0.24 * s, 0.36 * s
    if glow: _lantern_glow(pen, x, y, s, k)
    body = poly([(x - w / 2, y - h * 0.85), (x + w / 2, y - h * 0.85), (x + w * 0.4, y), (x - w * 0.4, y)])
    pen.fill(body, mix('#3a2a18', glass, 0.85 * k + 0.15))
    pen.radial(body, x, y - h * 0.45, h * 0.6, [(0, mix('#4a3a24', '#fff8ee', k)), (1, mix('#3a2a18', glass, k * 0.9))])
    pen.fill(oval(x, y - h * 0.45, w * 0.13, h * 0.17), mix('#6a5030', '#fff8ee', k))
    for xx in (x - w * 0.2, x + w * 0.2):
        pen.seg((xx, y - h * 0.85), (xx * 0.5 + x * 0.5 + (xx - x) * 0.3, y), max(1, 0.012 * s), '#151210', 220)
    pen.line(body, max(1.5, 0.02 * s), '#151210')
    roof = poly([(x - w * 0.62, y - h * 0.85), (x, y - h * 1.15), (x + w * 0.62, y - h * 0.85)])
    pen.shape(roof, '#151210', max(1, 0.015 * s))
    pen.fill(oval(x, y - h * 1.18, 0.03 * s), '#151210')
    pen.fill(rect(x - w * 0.45, y - 0.02 * s, w * 0.9, 0.04 * s), '#151210')


def _lantern_glow(pen, x, y, s, k=1.0):
    h = 0.36 * s
    pen.glow(x, y - h * 0.5, min(2.6 * s, 520.0), '#ffcf8f', 95 * k)
    pen.glow(x, y - h * 0.5, min(0.9 * s, 190.0), '#ffd9a0', 150 * k)


def _lantern_glow_draw(v, X, D, Y=1.78):
    def draw(pen, t):
        x, y = v.p(X, Y, D); _lantern_glow(pen, x, y, v.s(D), 1.0)
    return draw


def _lantern_glow_bounds(v, X, D, Y=1.78):
    x, y = v.p(X, Y, D); r = min(2.7 * v.s(D), 540.0)
    return (x - r, y - 0.18 * v.s(D) - r, x + r, y - 0.18 * v.s(D) + r)


def _lantern_layer_draw(v, X, D, Y=1.78, moths=5, seed=0, flick=None):
    def draw(pen, t):
        s = v.s(D); x, y = v.p(X, Y, D)
        k = flick(t) if flick else 1.0
        _lantern(pen, x, y, s, k, glow=False)
        if moths: draw_moths(pen, t, x, y - 0.18 * s, 0.42 * s, moths, seed, max(2.0, 0.035 * s))
    return draw


def _pool_draw(v, pools):
    def draw(pen, t):
        for (X, Y, D, r, c, a) in pools:
            x, y = v.p(X, Y, D)
            pen.radial(None, x, y, r * v.s(D), [(0, c, a), (0.45, c, a * 0.4), (1, c, 0)], sy=0.34, clip=False)
    return draw


def _car_layer_draw(v, D, car, lights_fn):
    """car: dict(x=X m, facing, t_in/t_out/mode..., figures, doors fn, head) -> draw(pen, t)."""
    def draw(pen, t):
        s = v.s(D)
        X = car.get('X', 3.0)
        st = None
        if car.get('drive'):
            dmode, t0, t1, Xa, Xb = car['drive']
            st = drive(t, t0, t1, v.x(Xa, D), v.x(Xb, D), dmode, wheel_r=0.36 * s, seed=3)
            x = st.x
        else:
            x = v.x(X, D)
        y = v.gy(D)
        kind = car.get('kind', 'patrol')
        head = car.get('head', False); head = head(t) if callable(head) else head
        brake = bool(st and st.moving and car['drive'][0] == 'in') or car.get('brake', False)
        if kind == 'van':                                   # the NIGHTLINE DELIVERY van (delivery film)
            hz = car['hazard_fn'](t) if car.get('hazard_fn') else 0.0
            door = car.get('door', 0.0); door = door(t) if callable(door) else door
            drv = car.get('driver', True); drv = drv(t) if callable(drv) else drv
            fac = car.get('facing', 1)
            if car.get('pool', True): _amber_pool(pen, x, y, s, hz, fac)
            delivery_van(pen, x, y, VAN_LEN * s, t, fac, st.wheel if st else 0.0, st.bounce if st else 0.0,
                         st.pitch if st else 0.0, hz, head, brake, drv, door, dash=car.get('dash', 1.0))
            return
        if kind == 'wagon':                                 # your parents' station wagon (memory, 21 years ago)
            _wagon(pen, x, y, 4.9 * s, car.get('color', '#5a4a3a'), car.get('facing', 1))
            return
        li = lights_fn(t)
        if car.get('pool', True): _police_pool(pen, x, y, s, li)
        doors = car['doors'](t) if callable(car.get('doors')) else car.get('doors')
        patrol_car(pen, x, y, 5.0 * s, t, car.get('facing', 1), st.wheel if st else 0.0, st.bounce if st else 0.0,
                   st.pitch if st else 0.0, li, head, brake, car.get('figures', ('driver', 'back')), doors)
    return draw


def _tree_layer_draw(v, X, D, h_m=9.0, seed=11, wind=1.0, lit=('#5a6a9a', 80)):
    def draw(pen, t):
        draw_tree(pen, v.x(X, D), v.gy(D), h_m * v.s(D), t, seed, wind, '#070a10', lit, 5)
    return draw


def _mist_draw(v, D, Xr=(-14, 14), a=16):
    def draw(pen, t):
        y = v.gy(D)
        _mist(pen, t, y - 0.25 * v.s(D), v.x(Xr[0], D), v.x(Xr[1], D), 0.6 * v.s(D), 5, 4, a * 1.2)
    return draw


def _lights_fn(police):
    if not police: return lambda t: (0.0, 0.0)
    p = dict(mode='sweep', speed=1.0, strength=1.0, t_on=None, t_off=None)
    if isinstance(police, dict): p.update(police)
    return lambda t: lightbar(t, p['mode'], p['speed'], p['strength'], p['t_on'], p['t_off'])


def _porch_world(name, v, box, car=None, police=True, lamp_X=-0.85, lamps=(-7.5, 11.0), moon=(1560, 170, 34),
                 flick=None, moths=5, tree=(-4.8, 3.3), wind=1.0, mist=True, chair=True, houses_D=8.0, peephole=False,
                 hazard=None, tod='night', windows=None, floor_near=0.3):
    """Shared porch world. Delivery-film extras (defaults keep the police film): hazard = f(t) -> 0..1 amber flashers of
    the van (amber spill on the houses, the yard and the railing), tod 'night' | 'dawn' (6:12: lights off, sunrise sky,
    warm sun wash), windows = f(i) -> lit tuple for the houses across (WINDOWS_3AM: nearly all dark)."""
    lf = _lights_fn(police)
    night = tod != 'dawn'
    if car and hazard and car.get('kind') == 'van': car.setdefault('hazard_fn', hazard)
    fl = (lambda t: flicker(t, 3, 1.0, flick if flick != 'random' else None)) if (flick and night) else None
    tag = name
    xr = (-40, 40)
    # static far field merged into one cached layer (sky, tree line, houses across, street lamps): parallax between them
    # is negligible, and one layer blits each pixel once
    backdrop = _combine(_sky_draw(v, (box[0], box[1], box[2], v.gy(houses_D) + 30), moon, tod=tod), _far_draw(v, 22, (-90, 90)),
                        _houses_draw(v, houses_D, [-33, -20, -7.5, 5.0, 17.5, 30.0], lit=windows, porch_k=1.0 if night else 0.0),
                        _lamps_draw(v, 6.0, lamps, 1.0 if night else 0.0))
    L = [
        _cl(houses_D + 1.0, backdrop, 'backdrop', _key(tag, 'backdrop'), (box[0], box[1], box[2], v.gy(4.4)), blur=0),
        _cl(5.0, _combine(_street_draw(v, xr), _yard_draw(v, lights=night)), 'ground', _key(tag, 'ground'),
            (box[0], min(v.gy(5.7) - 4, v.y(v.ground + 1.6, 4.2)), box[2], v.gy(2.0) + 70)),
        _cl(1.8, _porch_front_draw(v, lamp_x=lamp_X), 'porch_front', _key(tag, 'front'), (box[0], v.y(2.0, 1.8), box[2], v.gy(2.6) + 10)),
        _cl(1.3, _porch_floor_draw(v, d_near=floor_near, pool=(0.0, 0.75, 2.0) if night else None), 'porch_floor', _key(tag, 'floor'),
            (box[0], v.y(0, 1.85) - 4, box[2], box[3])),
    ]
    if night:
        L += [_cl(1.795, _lantern_glow_draw(v, lamp_X, 1.8), 'lantern_glow', _key(tag, 'lglow'), _lantern_glow_bounds(v, lamp_X, 1.8),
                  alpha=(lambda t: fl(t)) if fl else 1.0, blur=0),
              Layer(1.79, _lantern_layer_draw(v, lamp_X, 1.8, 1.78, moths, 2, fl), 'lantern'),
              _cl(1.29, _pool_draw(v, [(lamp_X, 0, 1.75, 2.2, '#ffcf8f', 70)]), 'lamp_pool',
                  _key(tag, 'pool'), (box[0], v.y(0, 2.4), box[2], v.y(0, 1.2)), alpha=(lambda t: fl(t)) if fl else 1.0)]
    else:
        L += [Layer(1.79, _lantern_layer_draw(v, lamp_X, 1.8, 1.78, 0, 2, lambda t: 0.0), 'lantern'),
              _cl(houses_D + 0.9, _dawn_wash(v, box, houses_D), 'sun_wash', _key(tag, 'sun'), box, blur=0)]
    if not peephole:
        L.append(_cl(0.9, _porch_sides_draw(v), 'porch_sides', _key(tag, 'sides'), box))
    if chair:
        L.append(_cl(1.25, _chair_draw(v), 'chair', _key(tag, 'chair'), (v.x(1.1, 1.3), v.y(1.3, 1.3), v.x(2.5, 1.3), v.y(-0.1, 1.3))))
    if tree:
        L.append(Layer(tree[1], _tree_layer_draw(v, tree[0], tree[1], 9.5, 11, wind), 'yard_tree'))
    if mist:
        L.append(Layer(2.7, _mist_draw(v, 2.7), 'mist', blur=0))
    if car:
        cd = car.get('D', 4.85)
        L.append(Layer(cd, _car_layer_draw(v, cd, car, lf), 'car'))
    _exposure(L, 0.28, ('ground', 'porch_floor', 'porch_sides', 'chair', 'porch_front'))
    _exposure(L, 0.12, ('backdrop',))
    if police:
        hb = (box[0], v.gy(houses_D) - 9.5 * v.s(houses_D), box[2], v.gy(houses_D) + 4)
        def house_geom(pen, c):
            s = v.s(houses_D)
            for X in [-33, -20, -7.5, 5.0, 17.5, 30.0]:
                gx, gy = v.x(X, houses_D), v.gy(houses_D)
                pen.radial(None, gx, gy - 2.2 * s, 6.5 * s, [(0, c, 255), (1, c, 0)], sy=0.45, clip=False)
        L += _spill_pair(houses_D + 0.95, house_geom, _key(tag, 'hspill'), hb, lf, 0.22, 0.26, 'houses_spill')
        L += _spill_pair(1.78, _porch_front_spill(v), _key(tag, 'fspill'), (box[0], v.y(1.3, 1.8), box[2], v.gy(1.8) + 4), lf, 0.32, 0.36, 'porch_spill')
        def yard_geom(pen, c):
            cx = v.x(car.get('X', 3.0) if car else 3.0, 4.6)
            pen.radial(None, cx, v.gy(3.6), 9 * v.s(3.6), [(0, c, 200), (0.6, c, 60), (1, c, 0)], sy=0.16, clip=False)
        L += _spill_pair(4.95, yard_geom, _key(tag, 'yspill'), (box[0], v.y(v.ground + 1.0, 4.2), box[2], v.gy(2.0) + 40), lf, 0.35, 0.4, 'yard_spill')
    if hazard and car:                                  # the van's amber flashers light the street, the yard and the railing
        cX = car.get('X', 3.0); cD = car.get('D', 4.85)
        def h_house(pen, c):
            s = v.s(houses_D)
            for X in (cX - 10, cX + 4):
                pen.radial(None, v.x(X, houses_D), v.gy(houses_D) - 1.8 * s, 7.5 * s, [(0, c, 255), (1, c, 0)], sy=0.42, clip=False)
        L += _spill_one(houses_D + 0.95, h_house, _key(tag, 'hz_h', cX), (box[0], v.gy(houses_D) - 9.5 * v.s(houses_D), box[2], v.gy(houses_D) + 4),
                        hazard, 0.3, 'houses_hazard')
        def h_yard(pen, c):
            for dX in (-2.6, 2.6):
                cx = v.x(cX + dX, cD - 0.3)
                pen.radial(None, cx, v.gy(cD - 0.4), 5.5 * v.s(cD), [(0, c, 220), (0.5, c, 70), (1, c, 0)], sy=0.2, clip=False)
        L += _spill_one(4.95, h_yard, _key(tag, 'hz_y', cX), (box[0], v.y(v.ground + 1.4, 4.4), box[2], v.gy(2.0) + 40), hazard, 0.5, 'yard_hazard')
        L += _spill_one(1.78, lambda pen, c: _porch_front_spill(v)(pen, c), _key(tag, 'hz_f'),
                        (box[0], v.y(1.3, 1.8), box[2], v.gy(1.8) + 4), hazard, 0.22, 'porch_hazard')
    return L


def porch_doorbell(car=True, police=True, car_X=4.0, flick='random', moths=6, wind=1.0, mist=True, drive_in=None,
                   doors=None, figures=('driver', 'back'), ir=False, vehicle='patrol', van=None, hazard=True, box=None,
                   tod='night', windows=None, era='now'):
    """Front porch seen by the doorbell camera beside the door (lens 'doorbell', grade 'night_blue' or 'doorbell_night').
    The officer stands at anchors['officer'] (depth 1.0, ~1.5 m from the lens). Behind him: white porch railing and steps,
    a post lantern with moths (flicker), the yard with path lights and mailbox, the patrol car at the curb (light bar ->
    police spill on the yard, railing and houses), the street, houses across, trees, sky with moon.
    drive_in = (t0, t1) makes the car arrive and brake; doors = f(t) -> {'rear': k}; police = False/True/dict(mode, speed,
    t_on, t_off). ir=True suggests lens 'doorbell_ir'.
    Delivery film: vehicle='van' (NIGHTLINE van at the curb, hazard = True | dict(rate, t_on, t_off, strength) | False;
    van = dict(driver=True|f(t), door=0..1|f(t) sliding door, head, drive=('out'|'in'|'pass', t0, t1, X0, X1), dash)),
    'wagon' (memory: the old station wagon) or None; box = 'door' | 'boots' | dict(at='door'|'boots'|(X, D), state=
    'taped'|'cut'|'open', knock=f(t)->0..1, keys=bool); tod 'night' | 'dawn'; windows=WINDOWS_3AM. Use delivery_porch()."""
    v = View(405, 380, 1.45, ground=-0.72)
    car_d = None
    if car:
        car_d = dict(X=car_X, facing=1, figures=figures, doors=doors, D=4.85)
        if drive_in: car_d['drive'] = ('in', drive_in[0], drive_in[1], car_X - 18.0, car_X); car_d['head'] = lambda t: t < drive_in[1] + 1.0
    if vehicle != 'patrol': car_d = _vehicle_spec(vehicle, car_X, 4.85, van, drive_in, era)
    hz = _hazard_fn(hazard) if vehicle == 'van' else None
    tag = 'pdb' if (vehicle == 'patrol' and tod == 'night' and windows is None) else 'pdb_%s_%s_%s%s' % (vehicle, tod, era, '_3am' if windows else '')
    L = _porch_world(tag, v, WIDE, car_d, police, flick=flick, moths=moths, wind=wind, mist=mist, hazard=hz, tod=tod, windows=windows)
    if box: L += _box_layers(v, box, tag, tod)
    anchors = {'officer': v.anchor(0.0, 1.0, note='on the porch, ~1.5 m from the lens'),
               'officer_close': v.anchor(0.0, 0.62, note='leaning toward the lens'),
               'officer2': v.anchor(-0.9, 1.25, note='second officer beside him'),
               'double': v.anchor(0.75, 1.15, note='the man in the grey coat beside the officer'),
               'steps': v.anchor(0.0, 1.95, Y=0.0, note='top of the steps'),
               'path_mid': v.anchor(0.0, 3.0, Y=-0.72, note='middle of the front path'),
               'gate': v.anchor(0.0, 4.15, Y=-0.72, note='path at the sidewalk'),
               'car_rear_door': v.anchor(car_X + 0.4, 4.4, Y=-0.72, note='beside the rear door of the car')}
    paths = {'car_to_porch': [anchors['car_rear_door'], anchors['gate'], anchors['path_mid'], anchors['steps'], anchors['double']]}
    pf = _lights_fn(police)
    info = {'view': v, 'car_X': car_X, 'lights': pf}
    if vehicle != 'patrol' or box or tod != 'night':
        _delivery_anchors(v, anchors, paths, car_X, box)
        info.update(hazard=hz or (lambda t: 0.0), box=_box_spec(box) if box else None)
    grade = 'ir_night' if ir else ('dawn' if tod == 'dawn' else ('memory' if era == 'memory' else 'doorbell_night'))
    return SetPiece('porch_doorbell', L, anchors, paths, lens='doorbell_ir' if ir else 'doorbell',
                    grade=grade, focus=1.0, dof=0.0, cover=WIDE,
                    fx=(lambda t: {'flash': police_flash(t, 0.1)}) if police else None, info=info)


def porch_peephole(car=True, police=True, car_X=2.3, flick='random', moths=5, wind=1.0, mist=True, drive_in=None, doors=None,
                   figures=('driver', 'back'), vehicle='patrol', van=None, hazard=True, tod='night', windows=None, era='now'):
    """The porch through the door's peephole (lens 'peephole', grade 'porch_warm'). Eye height 1.6 m; officer at
    anchors['officer'] (depth 1.0) fills ~45 % of the disc; anchors['officer_close'] (depth 0.62) ~70 %. Same world as
    porch_doorbell: railing, lantern + moths, path, patrol car at the curb with the second officer behind the wheel and
    the man in the back seat, houses across, moon. Delivery film: vehicle / van / hazard / tod / windows as porch_doorbell."""
    v = View(600, 560, 1.6, ground=-0.72)
    car_d = None
    if car:
        car_d = dict(X=car_X, facing=1, figures=figures, doors=doors, D=4.85)
        if drive_in: car_d['drive'] = ('in', drive_in[0], drive_in[1], car_X - 14.0, car_X); car_d['head'] = lambda t: t < drive_in[1] + 1.0
    if vehicle != 'patrol': car_d = _vehicle_spec(vehicle, car_X, 4.85, van, drive_in, era)
    hz = _hazard_fn(hazard) if vehicle == 'van' else None
    tag = 'pph' if (vehicle == 'patrol' and tod == 'night' and windows is None) else 'pph_%s_%s_%s%s' % (vehicle, tod, era, '_3am' if windows else '')
    L = _porch_world(tag, v, PEEP, car_d, police, lamps=(-3.6, 6.2), moon=(1290, 150, 30), flick=flick, moths=moths, wind=wind,
                     mist=mist, tree=(-3.6, 3.4), chair=False, peephole=True, hazard=hz, tod=tod, windows=windows)
    anchors = {'officer': v.anchor(0.0, 1.0, note='under the porch light, ~1 m from the door'),
               'officer_close': v.anchor(0.0, 0.62, note='face bulging toward the lens'),
               'officer2': v.anchor(-0.7, 1.2), 'double': v.anchor(0.55, 1.1),
               'steps': v.anchor(0.0, 1.95), 'path_mid': v.anchor(0.0, 3.0, Y=-0.72), 'gate': v.anchor(0.0, 4.15, Y=-0.72),
               'car_rear_door': v.anchor(car_X + 0.4, 4.4, Y=-0.72)}
    paths = {'car_to_porch': [anchors['car_rear_door'], anchors['gate'], anchors['path_mid'], anchors['steps'], anchors['double']]}
    info = {'view': v, 'car_X': car_X, 'lights': _lights_fn(police)}
    if vehicle != 'patrol' or tod != 'night':
        _delivery_anchors(v, anchors, paths, car_X, None)
        info['hazard'] = hz or (lambda t: 0.0)
    return SetPiece('porch_peephole', L, anchors, paths, lens='peephole', grade='dawn' if tod == 'dawn' else 'porch_warm', focus=1.0, dof=0.0,
                    cover=PEEP, fx=(lambda t: {'flash': police_flash(t, 0.1)}) if police else None, info=info)


# ============================================================== street views (house 144, mother's cottage)
def _road_draw(v, d_near, d_far, d_walk, seed=1):
    """Road between d_near (camera-side curb) and d_far (house-side curb), sidewalk to d_walk."""
    def draw(pen, t):
        xl, xr = -1000, 2920
        ya, yb = v.gy(d_far), max(v.gy(d_near), 1400)
        road = rect(xl, ya, xr - xl, yb - ya)
        pen.linear(road, 0, ya, 0, min(yb, 1300), ['#181a21', '#21232b', '#262830'])
        pen.texture(road, 'asphalt', 0.4, 'overlay', 1.0)
        dm = (d_near + d_far) / 2
        for kx in range(-14, 14):
            a, b = kx * 3.2, kx * 3.2 + 1.8
            pen.fill(v.quad([(a, 0, dm - 0.012), (b, 0, dm - 0.012), (b, 0, dm + 0.012), (a, 0, dm + 0.012)]), '#8a7a4a', 110)
        for i, X in enumerate((-6.5, 4.0)):
            c = v.p(X, 0, dm + 0.15)
            pen.fill(oval(c[0], c[1], 0.45 * v.s(dm), 0.06 * v.s(dm)), '#0e1014')
        cracks = np.random.default_rng(seed)
        for _ in range(14):
            D = cracks.uniform(min(d_far, d_near + 0.15), max(d_far, d_near + 0.15)); X = cracks.uniform(-14, 14)
            pts = [v.p(X + k * 0.6 + cracks.uniform(-0.2, 0.2), 0, D + cracks.uniform(-0.01, 0.01)) for k in range(4)]
            pen.line(poly(pts, False), 1.0, '#0b0c10', 160)
        # house-side curb + sidewalk
        yc0, yc1 = v.y(0.15, d_far), v.gy(d_far)
        pen.fill(rect(xl, yc0, xr - xl, yc1 - yc0 + 1), '#44464e')
        yw = v.y(0.15, d_walk)
        walk = rect(xl, yw, xr - xl, yc0 - yw)
        pen.linear(walk, 0, yw, 0, yc0, ['#34363d', '#40424a'])
        pen.texture(walk, 'plaster', 0.4, 'overlay', 0.8)
        for kx in range(-30, 30):
            pen.seg(v.p(kx * 1.6, 0.15, d_walk), v.p(kx * 1.6, 0.15, d_far), 1.2, '#1a1b20', 170)
        for (X, c) in ((-5.4, '#3a3036'),):
            D = d_far - 0.06
            _sedan(pen, v.x(X, D), v.gy(D), 4.6 * v.s(D), c, 1)
        # camera-side curb (very near, bottom of frame)
        if v.gy(d_near) < 1500:
            yn = v.gy(d_near)
            pen.fill(rect(xl, yn, xr - xl, 1600 - yn), '#2e3037')
            pen.fill(rect(xl, yn - 0.15 * v.s(d_near), xr - xl, 0.15 * v.s(d_near)), '#4a4c54')
    return draw


def _lawn_draw(v, d0, d1, path=(0.0, 0.6), mailbox=(1.3, None), fence=False, seed=3, hedge=True, flowers=True,
               gate_gap=0.6, number='144'):
    def draw(pen, t):
        xl, xr = -1000, 2920
        ya, yb = v.gy(d1), v.gy(d0)
        lawn = rect(xl, ya - 2, xr - xl, yb - ya + 4)
        pen.linear(lawn, 0, ya, 0, yb, ['#0e1714', '#13211b'])
        pen.texture(lawn, 'fabric', 0.25, 'overlay', 0.5)
        rng = np.random.default_rng(seed)
        for _ in range(500):
            D = rng.uniform(d0, d1); X = rng.uniform(-16, 16)
            x, y = v.p(X, 0, D); s = v.s(D); h = rng.uniform(0.06, 0.14) * s
            pen.seg((x, y), (x + rng.uniform(-0.3, 0.3) * h, y - h), max(0.7, 0.014 * s), '#1d3329' if rng.uniform() < 0.5 else '#0a120f', 190)
        if path:
            X, w = path
            pp = v.quad([(X - w, 0, d0), (X + w, 0, d0), (X + w, 0, d1), (X - w, 0, d1)])
            pen.linear(pp, 0, ya, 0, yb, ['#3a3b42', '#46474e'])
            pen.texture(pp, 'plaster', 0.5, 'overlay', 0.7)
            D = d0
            while D < d1:
                pen.seg(v.p(X - w, 0, D), v.p(X + w, 0, D), max(0.8, 0.02 * v.s(D)), '#1b1c21', 200); D += 0.045
        if flowers and path:
            X, w = path
            for side in (-1, 1):
                for i in range(4):
                    D = d0 + 0.04 + i * (d1 - d0 - 0.06) / 4
                    x, y = v.p(X + side * (w + 0.45), 0, D); s = v.s(D)
                    _bush(pen, x, y, 0.8 * s, 0.45 * s, seed * 7 + i + (side > 0) * 40, '#0e1a14', '#1c2e22')
        if hedge:
            for side in (-1, 1):
                for i in range(5):
                    D = d0 + 0.05 + i * (d1 - d0) / 5
                    x, y = v.p(side * 7.5, 0, D); s = v.s(D)
                    _bush(pen, x, y, 2.0 * s, 1.3 * s, seed + 70 + 3 * i + (side > 0), '#0b1511', '#15241c')
        if fence:
            D = d0 + 0.02; s = v.s(D)
            X0, X1 = -9.0, 9.0
            gx0, gx1 = (path[0] - gate_gap, path[0] + gate_gap) if path else (0, 0)
            X = X0
            while X < X1:
                if not (gx0 <= X <= gx1):
                    x, y = v.p(X, 0, D)
                    pk = poly([(x - 0.045 * s, y), (x - 0.045 * s, y - 0.8 * s), (x, y - 0.9 * s), (x + 0.045 * s, y - 0.8 * s), (x + 0.045 * s, y)])
                    pen.shape(pk, '#a9a49a', max(0.8, 0.012 * s))
                X += 0.16
            for Y in (0.25, 0.65):
                for (a, b) in ((X0, gx0), (gx1, X1)):
                    pen.fill(rect(v.x(a, D), v.y(Y, D), (b - a) * s, 0.05 * s), '#8f8a80')
        if mailbox and mailbox[0] is not None:
            X = mailbox[0]; D = mailbox[1] or d0 + 0.015
            x, y = v.p(X, 0, D); s = v.s(D)
            pen.shape(rect(x - 0.05 * s, y - 1.05 * s, 0.1 * s, 1.05 * s), '#2a2420', max(1, 0.02 * s))
            box = inter(union(rect(x - 0.3 * s, y - 1.25 * s, 0.6 * s, 0.14 * s), oval(x, y - 1.25 * s, 0.3 * s, 0.17 * s)),
                        rect(x - 0.32 * s, y - 1.45 * s, 0.64 * s, 0.35 * s))
            pen.shape(box, '#16181e', max(1, 0.02 * s))
            pen.fill(rect(x - 0.26 * s, y - 1.37 * s, 0.52 * s, 0.03 * s), '#3a3f4c', 180)
            pen.shape(rect(x + 0.22 * s, y - 1.47 * s, 0.04 * s, 0.24 * s), '#a3262a', max(0.8, 0.015 * s))
            text(pen.cv, number, x, y - 1.15 * s, 800, 0.12 * s, '#cfc8b8', 220)
    return draw


def _house144_draw(v, X=-0.5, D=2.2, w=11.0, bedroom_lit=0.0, living_lit=1.0, upstairs_left=0.35):
    """The family house, 2 storeys, beige siding, gable roof; windows: living room (left, lit), hall/kitchen (right),
    upstairs bedroom (right, the window the double looks at)."""
    def draw(pen, t):
        s = v.s(D); gx = v.x(X, D); gy = v.gy(D)
        L, R = gx - w / 2 * s, gx + w / 2 * s
        T = gy - 5.8 * s
        wall = '#4a4640'
        body = rect(L, T, R - L, gy - T)
        pen.linear(body, 0, T, 0, gy, ['#3a3836', '#57514a'])
        _siding(pen, body, L, T, R, gy, 0.2 * s, '#000000', 70, '#8a8070', 26)
        pen.line(body, max(1.5, 0.05 * s), LINE)
        for xx in (L, R):
            pen.fill(rect(xx - 0.1 * s, T, 0.2 * s, gy - T), '#9a948a')
        # roof
        ov = 0.5 * s; rh = 3.0 * s
        gable = poly([(L + 0.1 * s, T), (gx, T - rh + 0.3 * s), (R - 0.1 * s, T)])
        pen.linear(gable, 0, T - rh, 0, T, ['#2e2c2c', '#3e3a36'])
        _siding(pen, gable, L, T - rh, R, T, 0.2 * s, '#000000', 60)
        roof = minus(poly([(L - ov, T + 0.15 * s), (gx, T - rh), (R + ov, T + 0.15 * s), (R + ov - 0.2 * s, T + 0.15 * s), (gx, T - rh + 0.4 * s),
                           (L - ov + 0.2 * s, T + 0.15 * s)]), rect(0, 0, 0, 0))
        pen.fill(roof, '#151820'); pen.line(roof, max(1.2, 0.04 * s), LINE)
        pen.line(poly([(L - ov + 0.1 * s, T + 0.1 * s), (gx, T - rh + 0.2 * s), (R + ov - 0.1 * s, T + 0.1 * s)], False), max(1.5, 0.08 * s), '#a8a294', 200)
        # attic window (round)
        _window(pen, gx - 0.4 * s, T - rh * 0.45, 0.8 * s, 0.8 * s, lit=0.0, trim='#a8a294', mull=(1, 1), sill=False, glow=False)
        # upstairs
        ww, wh = 1.2 * s, 1.35 * s
        uy = T + 0.75 * s
        _window(pen, gx - 3.1 * s - ww / 2, uy, ww, wh, lit=upstairs_left, curtain='#5a3a3a', trim='#a8a294', mull=(1, 1), lw=max(1.2, 0.04 * s))
        _window(pen, gx + 3.1 * s - ww / 2, uy, ww, wh, lit=bedroom_lit, curtain='#3a4a5a', trim='#a8a294', mull=(1, 1), lw=max(1.2, 0.04 * s),
                shade=0.18)
        for wx in (gx - 3.1 * s, gx + 3.1 * s):                         # shutters
            for sd in (-1, 1):
                sh = rect(wx + sd * (ww / 2 + 0.12 * s) - (0.38 * s if sd < 0 else 0), uy - 0.05 * s, 0.38 * s, wh + 0.1 * s)
                pen.shape(sh, '#1e2a30', max(1, 0.03 * s))
                for k in range(6): pen.seg((sh.getBounds().left() + 0.05 * s, sh.getBounds().top() + (k + 0.6) * wh / 6),
                                           (sh.getBounds().right() - 0.05 * s, sh.getBounds().top() + (k + 0.6) * wh / 6), max(0.8, 0.02 * s), '#0e1418', 200)
        # downstairs
        dy = gy - 2.75 * s
        _window(pen, gx - 3.3 * s - 0.9 * s, dy, 1.8 * s, 1.5 * s, lit=living_lit, curtain='#6a3030', trim='#a8a294', mull=(2, 1), lw=max(1.2, 0.04 * s))
        _window(pen, gx + 3.3 * s - 0.6 * s, dy, 1.2 * s, 1.5 * s, lit=0.25, trim='#a8a294', mull=(1, 1), lw=max(1.2, 0.04 * s), shade=0.4)
        # door
        dw, dh = 1.0 * s, 2.15 * s
        door = rect(gx - dw / 2, gy - 0.72 * s - dh, dw, dh)
        pen.shape(rect(gx - dw / 2 - 0.14 * s, gy - 0.72 * s - dh - 0.14 * s, dw + 0.28 * s, dh + 0.14 * s), '#a8a294', max(1, 0.03 * s))
        pen.shape(door, '#4a2420', max(1, 0.03 * s))
        for (py, ph) in ((0.08, 0.38), (0.54, 0.38)):
            for px_ in (0.12, 0.54):
                pen.line(rect(gx - dw / 2 + dw * px_, gy - 0.72 * s - dh + dh * py, dw * 0.34, dh * ph), max(0.8, 0.02 * s), '#000000', 110)
        pen.fill(oval(gx + dw * 0.32, gy - 0.72 * s - dh * 0.47, 0.05 * s), '#c9a64a')
        pen.fill(rect(gx - dw * 0.22, gy - 0.72 * s - dh * 0.36, dw * 0.44, 0.06 * s), '#c9a64a', 200)   # mail slot
        # number plaque 144 beside the door
        nx, ny = gx + dw / 2 + 0.55 * s, gy - 0.72 * s - dh * 0.72
        pen.shape(rrect(nx - 0.42 * s, ny - 0.2 * s, 0.84 * s, 0.4 * s, 0.05 * s), '#1a1c22', max(1, 0.02 * s))
        text(pen.cv, '144', nx, ny + 0.11 * s, 800, 0.3 * s, '#e6dfcf', 240)
        pen.radial(None, gx, gy - 0.72 * s - dh * 0.6, 3.2 * s, [(0, '#ffcf8f', 70), (1, '#ffcf8f', 0)], clip=False)
        # foundation
        pen.fill(rect(L, gy - 0.72 * s, R - L, 0.72 * s), '#2a2a2e')
        pen.texture(rect(L, gy - 0.72 * s, R - L, 0.72 * s), 'plaster', 0.5)
    return draw


def _porch144_draw(v, X=-0.5, D=2.05, w=10.4, lamp_X=-0.85):
    """Porch in front of house 144 (seen from the street): floor at 0.72 m, shed roof on columns, white railing, steps."""
    def draw(pen, t):
        s = v.s(D); gx = v.x(X, D); gy = v.gy(D)
        L, R = gx - w / 2 * s, gx + w / 2 * s
        fy = gy - 0.72 * s
        # roof
        ry = gy - 3.25 * s
        roof = poly([(L - 0.35 * s, ry), (R + 0.35 * s, ry), (R + 0.2 * s, ry - 0.55 * s), (L - 0.2 * s, ry - 0.55 * s)])
        pen.fill(roof, '#14171f'); pen.line(roof, max(1, 0.03 * s), LINE)
        pen.fill(rect(L - 0.35 * s, ry, R - L + 0.7 * s, 0.3 * s), '#b0a898'); pen.line(rect(L - 0.35 * s, ry, R - L + 0.7 * s, 0.3 * s), max(1, 0.03 * s), LINE)
        # columns
        for cx in (L + 0.1 * s, gx - 1.0 * s, gx + 1.0 * s, R - 0.1 * s):
            col_ = rect(cx - 0.11 * s, ry + 0.3 * s, 0.22 * s, fy - ry - 0.3 * s)
            pen.fill(col_, '#bcb4a4'); pen.fill(rect(cx + 0.03 * s, ry + 0.3 * s, 0.08 * s, fy - ry - 0.3 * s), '#8a8478'); pen.line(col_, max(1, 0.025 * s), LINE)
        # floor edge + skirt (lattice)
        pen.fill(rect(L, fy, R - L, 0.12 * s), '#6a5a48')
        sk = rect(L, fy + 0.12 * s, R - L, 0.6 * s)
        pen.fill(sk, '#1a1a1e')
        pen.cv.save(); pen.cv.clipPath(sk, skia.ClipOp.kIntersect, True)
        for k in range(-10, int((R - L) / (0.25 * s)) + 10):
            x0 = L + k * 0.25 * s
            pen.seg((x0, fy + 0.12 * s), (x0 + 0.6 * s, fy + 0.72 * s), max(0.8, 0.03 * s), '#5a564e', 200)
            pen.seg((x0 + 0.6 * s, fy + 0.12 * s), (x0, fy + 0.72 * s), max(0.8, 0.03 * s), '#5a564e', 200)
        pen.cv.restore()
        # railing (with gap for the steps)
        for (a, b) in ((L + 0.1 * s, gx - 1.0 * s), (gx + 1.0 * s, R - 0.1 * s)):
            pen.fill(rect(a, fy - 0.95 * s, b - a, 0.09 * s), '#cfc7b6'); pen.fill(rect(a, fy - 0.16 * s, b - a, 0.06 * s), '#a8a294')
            n = int((b - a) / (0.14 * s))
            for k in range(1, n): pen.fill(rect(a + k * (b - a) / n - 0.025 * s, fy - 0.88 * s, 0.05 * s, 0.75 * s), '#bdb6a6')
            pen.line(rect(a, fy - 0.95 * s, b - a, 0.09 * s), max(0.8, 0.015 * s), LINE)
        # steps
        for i in range(4):
            sy0 = fy + i * 0.18 * s; sw = 2.0 * s + i * 0.1 * s
            st = rect(gx - sw / 2, sy0, sw, 0.18 * s)
            pen.fill(st, mix('#5a4c3e', '#3a3028', i / 4)); pen.seg((gx - sw / 2, sy0), (gx + sw / 2, sy0), max(1, 0.03 * s), '#7a6a58')
        # lamp post with lantern
        lx = v.x(lamp_X + X, D)
        pen.fill(rect(lx - 0.035 * s, fy - 1.75 * s, 0.07 * s, 1.75 * s), '#141414')
    return draw


def _cottage_draw(v, X=0.0, D=2.0, w=9.0, window_lit=1.0, silhouette=False, number='27'):
    """Mother's brick cottage: hip roof, bay window with lace curtains, small portico with lamp."""
    def draw(pen, t):
        s = v.s(D); gx = v.x(X, D); gy = v.gy(D)
        L, R = gx - w / 2 * s, gx + w / 2 * s
        T = gy - 3.2 * s
        body = rect(L, T, R - L, gy - T)
        pen.linear(body, 0, T, 0, gy, ['#3a2624', '#4e302a'])
        _bricks(pen, body, L, T, R, gy, 0.075 * s, 0.24 * s, '#120a0a', 80, 5, var='#6a3a30')
        pen.line(body, max(1.2, 0.04 * s), LINE)
        rh = 2.4 * s; ov = 0.45 * s
        roof = poly([(L - ov, T + 0.1 * s), (L + 2.2 * s, T - rh), (R - 2.2 * s, T - rh), (R + ov, T + 0.1 * s)])
        pen.fill(roof, '#1a1a22')
        for k in range(1, 7):
            u = k / 7; yy = T + 0.1 * s - (rh + 0.1 * s) * u
            xa = (L - ov) + (2.2 * s + ov) * u; xb = (R + ov) - (2.2 * s + ov) * u
            pen.seg((xa, yy), (xb, yy), max(0.8, 0.025 * s), '#0a0a10', 150)
        pen.line(roof, max(1.2, 0.04 * s), LINE)
        pen.fill(rect(L - ov, T, R - L + 2 * ov, 0.18 * s), '#cfc7b6', 230)
        ch = rect(R - 2.6 * s, T - rh - 0.6 * s, 0.7 * s, 1.6 * s)
        pen.shape(ch, '#3a2420', max(1, 0.03 * s)); _bricks(pen, ch, ch.getBounds().left(), ch.getBounds().top(), ch.getBounds().right(), ch.getBounds().bottom(), 0.12 * s, 0.3 * s, '#000000', 70)
        # bay window (left)
        bx, by, bw, bh = gx - 3.5 * s, gy - 2.55 * s, 2.6 * s, 1.6 * s
        bay = poly([(bx - 0.25 * s, by + bh + 0.3 * s), (bx - 0.25 * s, by - 0.2 * s), (bx + bw + 0.25 * s, by - 0.2 * s), (bx + bw + 0.25 * s, by + bh + 0.3 * s)])
        pen.shape(bay, '#cfc7b6', max(1, 0.03 * s))
        _window(pen, bx, by, bw, bh, lit=window_lit, warm=('#f2d39e', '#c08850'), trim='#cfc7b6', mull=(2, 1), lw=max(1.2, 0.035 * s),
                curtain='#d8cfc0', silhouette=silhouette)
        pen.cv.save(); pen.cv.clipPath(rect(bx, by, bw, bh), skia.ClipOp.kIntersect, True)       # lace pattern
        for i in range(int(bw / (0.12 * s))):
            for j in range(int(bh / (0.12 * s))):
                pen.fill(oval(bx + (i + 0.5) * 0.12 * s, by + (j + 0.5) * 0.12 * s, 0.025 * s), '#ffffff', 26)
        pen.cv.restore()
        # flower box
        pen.shape(rect(bx - 0.1 * s, by + bh + 0.08 * s, bw + 0.2 * s, 0.25 * s), '#3a2a20', max(1, 0.025 * s))
        for k in range(12):
            pen.fill(oval(bx + (k + 0.5) * bw / 12, by + bh + 0.04 * s, 0.1 * s), ['#8a3a4a', '#c9a64a', '#6a4a7a'][k % 3], 220)
        # right window
        _window(pen, gx + 2.2 * s, gy - 2.45 * s, 1.2 * s, 1.4 * s, lit=0.15, trim='#cfc7b6', mull=(1, 1), lw=max(1.2, 0.035 * s), shade=0.5)
        # door + portico
        dw, dh = 0.95 * s, 2.05 * s
        dx = gx + 0.4 * s
        pen.shape(rect(dx - 0.12 * s, gy - dh - 0.12 * s, dw + 0.24 * s, dh + 0.12 * s), '#cfc7b6', max(1, 0.03 * s))
        door = rect(dx, gy - dh, dw, dh)
        pen.shape(door, '#2a3a4a', max(1, 0.03 * s))
        pen.fill(rrect(dx + dw * 0.25, gy - dh * 0.92, dw * 0.5, dh * 0.25, 0.1 * s), '#e8c890', 230)   # door glass
        for (py, ph) in ((0.45, 0.45),):
            pen.line(rect(dx + dw * 0.15, gy - dh + dh * py, dw * 0.7, dh * ph), max(0.8, 0.02 * s), '#000000', 110)
        pen.fill(oval(dx + dw * 0.82, gy - dh * 0.47, 0.05 * s), '#c9a64a')
        pp = poly([(dx - 0.5 * s, gy - dh - 0.15 * s), (dx + dw / 2, gy - dh - 0.85 * s), (dx + dw + 0.5 * s, gy - dh - 0.15 * s)])
        pen.shape(pp, '#1a1a22', max(1, 0.03 * s))
        lx, ly = dx - 0.35 * s, gy - dh * 0.75
        pen.radial(None, lx, ly + 0.5 * s, 2.8 * s, [(0, '#ffc98a', 90), (1, '#ffc98a', 0)], clip=False)
        pen.fill(rrect(lx - 0.1 * s, ly - 0.17 * s, 0.2 * s, 0.34 * s, 0.05 * s), '#1a1612'); _lamp_core(pen, lx, ly, 0.07 * s, 1.0)
        text(pen.cv, number, dx + dw + 0.45 * s, gy - dh * 0.62, 800, 0.32 * s, '#e6dfcf', 230)
        # step
        pen.fill(rect(dx - 0.3 * s, gy - 0.1 * s, dw + 0.6 * s, 0.14 * s), '#5a5650')
    return draw


def _street_world(tag, v, house_fn, porch_fn=None, car=None, police=True, neighbours=True, lamps=((-9.5, 1.8),), tree=(-6.5, 1.75),
                  wind=1.0, moon=(1610, 120, 30), mist=True, fence=False, mailbox=1.4, number='144', house_D=2.2, extra=(),
                  hazard=None, nb_lit=(0.9, 0, 0.7, 0)):
    lf = _lights_fn(police)
    if car and hazard and car.get('kind') == 'van': car.setdefault('hazard_fn', hazard)
    box = FRAME
    def nb(pen, t):
        if not neighbours: return
        for i, X in enumerate((-17.5, 16.5)):
            _house(pen, v, X, 2.45, 10.5, 3.2 + (2.6 if i else 0), 2.4, seed=3 + i, storeys=2 if i else 1, lit=nb_lit,
                   garage=(i == 0), number=('142', '146')[i])
        draw_tree(pen, v.x(10.5, 2.7), v.gy(2.7), 11 * v.s(2.7), 0.0, 23, 0.0, '#080b12', ('#4a5a88', 70), 5)
    backdrop = _combine(_sky_draw(v, (box[0], box[1], box[2], v.gy(6) + 20), moon, seed=9,
                                  clouds=((300, 90, 700, 40), (1150, 40, 800, 36), (2000, 130, 600, 36))),
                        _far_draw(v, 6.0, (-60, 60), 8), nb)
    L = [_cl(3.0, backdrop, 'backdrop', _key(tag, 'backdrop'), (box[0], box[1], box[2], v.gy(2.45) + 8), blur=0)]
    lamp_fns = [_lamps_draw(v, lD, (lX,)) for (lX, lD) in lamps]
    L.append(_cl(house_D, _combine(house_fn, *([porch_fn] if porch_fn else []), *lamp_fns), 'house', _key(tag, 'house'),
                 (box[0], v.y(9.5, house_D), box[2], v.gy(2.05) + 8)))
    L.append(_cl(1.3, _combine(_lawn_draw(v, 1.4, 2.05 if porch_fn else house_D, mailbox=(mailbox, None), fence=fence, number=number),
                               _road_draw(v, 0.5, 1.25, 1.4)), 'ground', _key(tag, 'ground'), (box[0], v.y(1.6, 1.42), box[2], box[3])))
    if tree:
        L.append(Layer(tree[1], _tree_layer_draw(v, tree[0], tree[1], 10.0, 17, wind), 'yard_tree'))
    if mist:
        L.append(Layer(1.5, _mist_draw(v, 1.5, a=16), 'mist', blur=0))

    def fg(pen, t):
        # camera-side sidewalk edge, a fire hydrant, a wheelie bin and a dark hedge: near framing with strong parallax
        D = 0.62; s = v.s(D)
        yb = v.gy(0.5)
        hx, hy = v.p(-2.75, 0, D)
        pen.radial(None, hx, hy, 0.5 * s, [(0, '#000000', 140), (1, '#000000', 0)], sy=0.2, clip=False)
        hyd = union(rrect(hx - 0.12 * s, hy - 0.62 * s, 0.24 * s, 0.62 * s, 0.05 * s), oval(hx, hy - 0.62 * s, 0.13 * s, 0.1 * s))
        hyd = union(hyd, rect(hx - 0.2 * s, hy - 0.45 * s, 0.4 * s, 0.09 * s))
        pen.shape(hyd, '#6a1c1a', max(2, 0.02 * s)); pen.fill(rect(hx - 0.12 * s, hy - 0.62 * s, 0.07 * s, 0.6 * s), '#8a2a24', 160)
        pen.fill(oval(hx, hy - 0.66 * s, 0.05 * s), '#3a0e0c')
        bx, by = v.p(-1.35, 0, D)
        bin_ = poly([(bx - 0.3 * s, by - 1.0 * s), (bx + 0.3 * s, by - 1.0 * s), (bx + 0.26 * s, by), (bx - 0.26 * s, by)])
        pen.radial(None, bx, by, 0.6 * s, [(0, '#000000', 140), (1, '#000000', 0)], sy=0.2, clip=False)
        pen.shape(bin_, '#1c2a22', max(2, 0.02 * s)); pen.shape(rrect(bx - 0.34 * s, by - 1.08 * s, 0.68 * s, 0.1 * s, 0.03 * s), '#16221c', max(2, 0.02 * s))
        pen.fill(rect(bx - 0.3 * s, by - 0.95 * s, 0.1 * s, 0.9 * s), '#ffffff', 16)
        _bush(pen, v.x(-4.4, 0.56), v.gy(0.56) + 40, 1.3 * v.s(0.56), 0.75 * v.s(0.56), 301, '#05080a', '#0d1512')
    L.append(_cl(0.6, fg, 'foreground', _key(tag, 'fg'), (box[0], v.y(2.0, 0.56), box[2], box[3])))
    if car:
        cd = car.get('D', 1.1)
        L.append(Layer(cd, _car_layer_draw(v, cd, car, lf), 'car'))
    for k, ex in enumerate(extra):                       # more parked vehicles (e.g. the old wagon in the memory)
        L.append(Layer(ex.get('D', 1.3), _car_layer_draw(v, ex.get('D', 1.3), ex, lf), 'car%d' % (k + 2)))
    if hazard and car:
        cX = car.get('X', 3.0)
        def hh(pen, c):
            s = v.s(house_D)
            pen.radial(None, v.x(cX - 1.0, house_D), v.gy(house_D) - 1.2 * s, 7.5 * s, [(0, c, 255), (0.6, c, 90), (1, c, 0)], sy=0.45, clip=False)
        L += _spill_one(house_D - 0.01, hh, _key(tag, 'hz_h', cX), (box[0], v.y(9.5, house_D), box[2], v.gy(house_D) + 4), hazard, 0.26, 'house_hazard')
        def hl(pen, c):
            for dX in (-2.7, 2.7):
                pen.radial(None, v.x(cX + dX, 1.15), v.gy(1.12), 3.6 * v.s(1.3), [(0, c, 235), (0.5, c, 80), (1, c, 0)], sy=0.16, clip=False)
        L += _spill_one(1.29, hl, _key(tag, 'hz_l', cX), (box[0], v.y(1.0, 2.0), box[2], v.gy(0.9)), hazard, 0.5, 'lawn_hazard')
    if police:
        def hg(pen, c):
            s = v.s(house_D)
            pen.radial(None, v.x(0, house_D), v.gy(house_D) - 2.6 * s, 8 * s, [(0, c, 255), (0.6, c, 110), (1, c, 0)], sy=0.5, clip=False)
        L += _spill_pair(house_D - 0.01, hg, _key(tag, 'hsp'), (box[0], v.y(9.5, house_D), box[2], v.gy(house_D) + 4), lf, 0.24, 0.28, 'house_spill')
        def lg(pen, c):
            cx = v.x(car.get('X', 3.0) if car else 3.0, 1.3)
            pen.radial(None, cx, v.gy(1.3), 9 * v.s(1.3), [(0, c, 230), (0.5, c, 80), (1, c, 0)], sy=0.12, clip=False)
        L += _spill_pair(1.29, lg, _key(tag, 'lsp'), (box[0], v.y(1.0, 2.0), box[2], v.gy(1.0)), lf, 0.4, 0.45, 'lawn_spill')
    return L


def street_wide(car=True, police=True, car_X=3.6, drive=None, doors=None, figures=('driver', 'back'), bedroom_lit=0.0,
                living_lit=1.0, wind=1.0, mist=True, head=None, vehicle='patrol', van=None, hazard=True, era='now', upstairs_left=0.35):
    """House 144 seen from across the street: two-storey house with porch, white railing, lantern, number 144, mailbox,
    lawn and path, neighbours, street lamp, trees, moon; the patrol car at the curb in the foreground (depth 1.1).
    drive = ('in'|'out'|'pass', t0, t1, X0, X1) moves the car (wheels turn, body pitches); doors = f(t) -> {'rear': k}.
    Anchors: officer on the porch, path points, car doors, the bedroom window (upstairs right).
    Delivery film: vehicle='van' (+ van=dict(driver, door, head, drive), hazard as porch_doorbell), era='memory' (21 years
    ago: the old station wagon parked in front, a dark house, desaturated 'memory' grade). Use delivery_street()."""
    v = View(160, 600, 1.5)
    car_d = None
    if car:
        car_d = dict(X=car_X, facing=1, figures=figures, doors=doors, D=1.1)
        if drive: car_d['drive'] = drive; car_d['head'] = head if head is not None else (lambda t: True)
    hz = None; extra = ()
    if vehicle != 'patrol':
        car_d = _vehicle_spec(vehicle, car_X, 1.1, dict(van or {}, drive=drive) if drive else van, None, era)
        if vehicle == 'van': hz = _hazard_fn(hazard)
        if era == 'memory': extra = (dict(kind='wagon', X=-5.6, D=1.28, facing=1, color='#6a5a44'),)
    tag = 'swd' if vehicle == 'patrol' else 'swd_%s_%s_%.2f_%.2f_%.2f' % (vehicle, era, bedroom_lit, living_lit, upstairs_left)
    L = _street_world(tag, v, _house144_draw(v, bedroom_lit=bedroom_lit, living_lit=living_lit, upstairs_left=upstairs_left),
                      _porch144_draw(v), car_d, police, wind=wind, mist=mist, hazard=hz, extra=extra,
                      nb_lit=(0.9, 0, 0.7, 0) if vehicle == 'patrol' else (0, 0, 0.35, 0))
    # lantern on the porch post (dynamic: flicker + moths)
    fl = lambda t: flicker(t, 5, 0.8)
    lv = View(160, 600, 1.5 - 0.72)
    L.append(_cl(2.045, _lantern_glow_draw(lv, -1.35, 2.05), 'lantern_glow', _key('swd', 'lglow'), _lantern_glow_bounds(lv, -1.35, 2.05),
                 alpha=fl, blur=0))
    L.append(Layer(2.04, _lantern_layer_draw(lv, -1.35, 2.05, 1.78, 4, 7, fl), 'lantern'))
    a = {'officer': v.anchor(-0.4, 2.0, Y=0.72, note='on the porch at the door'),
         'double': v.anchor(0.4, 2.0, Y=0.72), 'officer2': v.anchor(-1.4, 2.0, Y=0.72),
         'steps': v.anchor(-0.5, 2.1, Y=0.0), 'path_mid': v.anchor(-0.5, 1.75), 'gate': v.anchor(-0.5, 1.42),
         'car_rear_door': v.anchor(car_X + 0.3, 1.2, note='kerb side of the car, rear door'),
         'car_front_door': v.anchor(car_X + 1.4, 1.2, note='driver door side (far side in reality, use for officer2)')}
    bx = v.x(-0.5 + 3.1, 2.2); by = v.gy(2.2) - (5.8 - 0.75 - 0.67) * v.s(2.2)
    info = {'view': v, 'bedroom_window': (bx, by, 2.2), 'lights': _lights_fn(police)}
    paths = {'porch_to_car': [a['officer'], a['steps'], a['path_mid'], a['gate'], a['car_rear_door']],
             'car_to_porch': [a['car_rear_door'], a['gate'], a['path_mid'], a['steps'], a['double']]}
    if vehicle != 'patrol':
        a['driver'] = a['officer']; a['van_door'] = v.anchor(car_X + 0.2, 1.2, note='beside the van\'s sliding door')
        a['van_cab'] = v.anchor(car_X - 1.3, 1.2, note='beside the van\'s cab door')
        paths['porch_to_van'] = [a['officer'], a['steps'], a['path_mid'], a['gate'], a['van_cab']]
        paths['van_to_porch'] = paths['porch_to_van'][::-1]
        info['hazard'] = hz or (lambda t: 0.0)
    return SetPiece('street_wide', L, a, paths, lens=None, grade='memory' if era == 'memory' else 'night_blue', focus=1.1, dof=0.0,
                    cover=FRAME, fx=(lambda t: {'flash': police_flash(t, 0.12)}) if police else None, info=info)


def mother_exterior(car=True, police=False, car_X=4.2, drive=None, doors=None, figures=('driver', 'back'), window_lit=1.0,
                    silhouette=False, wind=1.0, mist=True, head=None):
    """Mother's brick cottage across the street at night: bay window with lace curtains (optional silhouette), portico
    lamp, picket fence with gate, number 27; the patrol car pulls up at the curb (drive=('in', t0, t1, X0, X1))."""
    v = View(160, 600, 1.5)
    car_d = None
    if car:
        car_d = dict(X=car_X, facing=1, figures=figures, doors=doors, D=1.1)
        if drive: car_d['drive'] = drive; car_d['head'] = head if head is not None else (lambda t: True)
    L = _street_world('mex', v, _cottage_draw(v, window_lit=window_lit, silhouette=silhouette), None, car_d, police,
                      lamps=((8.5, 1.8),), tree=(-7.0, 1.7), wind=wind, mist=mist, fence=True, mailbox=-1.6, number='27',
                      house_D=2.0, moon=(420, 110, 28))
    a = {'door': v.anchor(0.85, 2.0, note="at mum's front door"), 'gate': v.anchor(0.0, 1.42), 'path_mid': v.anchor(0.0, 1.7),
         'car_rear_door': v.anchor(car_X + 0.3, 1.2), 'car_front_door': v.anchor(car_X + 1.4, 1.2),
         'window': v.anchor(-2.2, 2.0, Y=0.0, note='bay window (left)')}
    paths = {'car_to_door': [a['car_rear_door'], a['gate'], a['path_mid'], a['door']]}
    return SetPiece('mother_exterior', L, a, paths, lens=None, grade='night_blue', focus=1.1, dof=0.0, cover=FRAME,
                    fx=(lambda t: {'flash': police_flash(t, 0.12)}) if police else None, info={'view': v, 'lights': _lights_fn(police)})


# ============================================================== patrol car back-seat window (close)
def car_backseat_window(police=True, reflect=1.0, fog=None, cage=True, far_street=True, lamp_reflection=True):
    """Close-up of the patrol car's rear side window from outside (from the porch: telephoto through the peephole, or a
    flat 'lens' shot). Depths: far street seen through the car 7, interior (seat, cage, far door) 1.35, the man (director
    inserts at anchors['man'], a seated bust) 1.2, window frame + door 1.0, glass reflections 0.98 (on top of him: put
    hand_on_glass / card at depth 0.99). fog = f(t) -> (x, y, r, k) breath fog patch on the glass."""
    lf = _lights_fn(police)
    box = FRAME
    WX0, WY0, WX1, WY1 = 330, 170, 1600, 735             # window opening (design px at depth 1)

    def window_path():
        return smooth([(WX0 + 20, WY1), (WX0, WY0 + 60), (WX0 + 140, WY0), (WX1 - 300, WY0), (WX1 - 40, WY1 - 70), (WX1 - 60, WY1)], True, 0.18)

    def far(pen, t):
        pen.linear(rect(box[0], box[1], box[2] - box[0], box[3] - box[1]), 0, 100, 0, 800, ['#0b1430', '#1b2142', '#0c0f18'])
        rng = np.random.default_rng(4)
        for i in range(5):
            x = 200 + i * 420; w = 300 + rng.uniform(0, 80)
            pen.fill(rect(x, 330, w, 260), '#151a28'); pen.fill(poly([(x - 20, 330), (x + w / 2, 230), (x + w + 20, 330)]), '#0d111b')
            for j in range(2):
                if (i + j) % 2 == 0:
                    wx_ = x + 50 + j * (w - 140)
                    pen.glow(wx_ + 17, 420, 60, '#e8c48c', 60)
                    pen.fill(rect(wx_, 402, 34, 40), '#e8c48c', 230); pen.seg((wx_ + 17, 402), (wx_ + 17, 442), 3, '#3a2a1a')
        _streetlamp(pen, 1180, 590, 40, -1, 1.0, True)
        pen.fill(rect(box[0], 590, box[2] - box[0], 400), '#0a0c10')

    def interior(pen, t):
        # far door inner panel + far window frame (behind the seat), roof liner
        pen.fill(rect(box[0], box[1], box[2] - box[0], WY0 - box[1] + 40), '#0d0e12')
        pen.linear(rect(box[0], WY0 - 40, box[2] - box[0], 110), 0, WY0 - 40, 0, WY0 + 70, ['#1c1d22', '#0e0f13'])
        fw = smooth([(380, 300), (520, 230), (1350, 230), (1520, 330), (1500, 470), (400, 470)], True, 0.2)
        pen.fill(minus(rect(box[0], WY0 + 60, box[2] - box[0], 420), fw), '#121318')
        pen.line(fw, 6, '#05060a')
        # rear bench seat: backrest + headrests
        seat = smooth([(250, 980), (300, 520), (420, 470), (1480, 470), (1640, 540), (1700, 980)], True, 0.3)
        pen.linear(seat, 0, 470, 0, 900, ['#4a4a52', '#2e2f36', '#16171b'])
        pen.texture(seat, 'fabric', 0.45, 'overlay', 0.8)
        pen.line(smooth([(330, 520), (420, 482), (1480, 482), (1620, 545)], False), 5, '#6a6a74', 160)
        for x in (700, 1200):
            pen.seg((x, 490), (x - 10, 900), 6, '#121318', 230)
            for px_ in (x - 70, x + 70): pen.seg((px_, 470), (px_, 430), 7, '#7a7e86')
            hr = rrect(x - 140, 330, 280, 110, 40)
            pen.shape(hr, '#3a3b42', 5); pen.texture(hr, 'fabric', 0.4, 'overlay', 0.8)
            pen.line(smooth([(x - 120, 350), (x, 340), (x + 120, 350)], False), 4, '#5a5a64', 150)
        # seat belt
        pen.line(smooth([(1360, 300), (1300, 520), (1180, 760)], False), 22, '#141519')
        pen.fill(rrect(1170, 740, 50, 70, 8), '#6a6e76')
        # cage partition at the left
        if cage:
            cg = rect(220, WY0 - 20, 160, 900)
            pen.fill(cg, '#08090c', 200)
            for k in range(-20, 20):
                pen.seg((220 + k * 22, WY0 - 20), (220 + k * 22 + 300, WY0 + 880), 2.5, '#2a2c32', 220)
                pen.seg((220 + k * 22 + 300, WY0 - 20), (220 + k * 22, WY0 + 880), 2.5, '#2a2c32', 220)
            pen.fill(minus(rect(100, WY0 - 60, 400, 1000), cg), '#000000', 0)
            pen.line(cg, 10, '#16181d')

    def frame(pen, t):
        wp = window_path()
        outer = rect(box[0], box[1], box[2] - box[0], box[3] - box[1])
        body = minus(outer, wp)
        pen.fill(body, '#0f1115')
        # upper body black, roof edge highlight
        pen.linear(rect(box[0], box[1], box[2] - box[0], WY0 - box[1]), 0, box[1], 0, WY0, ['#06070a', '#1a1d24'])
        pen.line(smooth([(box[0], WY0 - 70), (900, WY0 - 92), (box[2], WY0 - 60)], False), 5, '#4a5262', 160)
        # white door panel below the beltline
        dp = rect(box[0], WY1 + 40, box[2] - box[0], box[3] - WY1)
        pen.linear(dp, 0, WY1 + 40, 0, 1150, ['#b8bcc5', '#8a8f9a', '#5a5f6a'])
        pen.fill(rect(box[0], WY1 + 40, box[2] - box[0], 14), '#e6e8ec', 120)
        text(pen.cv, 'POLICE', 820, 1010, 900, 150, '#141821', 235, 0.06)
        pen.shape(rrect(1450, WY1 + 110, 210, 46, 18), '#25282e', 4)                   # door handle
        pen.fill(rrect(1462, WY1 + 118, 186, 16, 8), '#5a5e66')
        pen.seg((WX1 + 160, box[1]), (WX1 + 160, box[3]), 6, '#05060a', 255)             # door seam (B pillar edge)
        pen.seg((WX0 - 120, box[1]), (WX0 - 120, box[3]), 6, '#05060a', 255)
        # window rubber + chrome
        pen.line(wp, 26, '#050608'); pen.line(wp, 6, '#5a606c', 200)
        pen.line(moved(wp, 0, 4), 3, '#000000', 150)
        # rain drops / dirt on the paint
        rng = np.random.default_rng(12)
        for _ in range(60):
            x, y = rng.uniform(box[0], box[2]), rng.uniform(WY1 + 60, 1250)
            pen.fill(oval(x, y, rng.uniform(2, 6), rng.uniform(3, 9)), '#ffffff', 22)

    def glass(pen, t):
        wp = window_path()
        pen.cv.save(); pen.cv.clipPath(wp, skia.ClipOp.kIntersect, True)
        pen.linear(rect(WX0, WY0, WX1 - WX0, WY1 - WY0), 0, WY0, 0, WY1, [(0, '#8ea6d8', 46 * reflect), (0.5, '#6a7aa8', 18 * reflect), (1, '#2a3048', 8 * reflect)])
        # reflected house + porch light (warm blob), streaks
        if lamp_reflection:
            pen.radial(None, 1260, 330, 120, [(0, '#ffe2b0', 120 * reflect), (0.3, '#ffcf8f', 50 * reflect), (1, '#ffcf8f', 0)], clip=False)
            pen.fill(oval(1260, 330, 9), '#fff2dc', 200 * reflect)
            pen.fill(rect(900, 260, 520, 6), '#c8b8a0', 40 * reflect)
            for k in range(9): pen.fill(rect(930 + k * 55, 266, 8, 120), '#c8b8a0', 26 * reflect)
        for (x0, w) in ((450, 140), (640, 50), (1080, 90)):
            pen.fill(poly([(x0, WY1), (x0 + w, WY1), (x0 + w + 420, WY0), (x0 + 420, WY0)]), '#c9d6f0', 22 * reflect)
        pen.cv.restore()

    def glass_dyn(pen, t):
        r_, b_ = lf(t)
        wp = window_path()
        pen.cv.save(); pen.cv.clipPath(wp, skia.ClipOp.kIntersect, True)
        if r_ > 0.05: pen.radial(None, 520, 230, 340, [(0, '#ff3030', 90 * r_), (1, '#ff3030', 0)], clip=False)
        if b_ > 0.05: pen.radial(None, 1380, 230, 340, [(0, '#3a5cff', 90 * b_), (1, '#3a5cff', 0)], clip=False)
        if fog:
            fx, fy, fr, fk = fog(t)
            if fk > 0.01: pen.radial(None, fx, fy, fr, [(0, '#c8d0dc', 110 * fk), (0.6, '#c8d0dc', 50 * fk), (1, '#c8d0dc', 0)], clip=False)
        pen.cv.restore()
        # roof edge / door paint glints from the light bar
        if r_ > 0.05: pen.fill(rect(box[0], WY0 - 98, 1000, 14), '#ff4040', 120 * r_); pen.radial(None, 300, WY1 + 140, 420, [(0, '#ff3030', 70 * r_), (1, '#ff3030', 0)], sy=0.3, clip=False)
        if b_ > 0.05: pen.fill(rect(900, WY0 - 98, 1000, 14), '#5a7cff', 120 * b_); pen.radial(None, 1600, WY1 + 140, 420, [(0, '#3a5cff', 70 * b_), (1, '#3a5cff', 0)], sy=0.3, clip=False)

    wb = (WX0 - 160, WY0 - 140, WX1 + 160, WY1 + 140)
    L = [_cl(7.0, far, 'far_street', _key('cbw', 'far'), (300, 160, 1640, 560))] if far_street else []
    L += [_cl(1.35, interior, 'interior', _key('cbw', 'int', cage), wb, dim=0.15),
          _cl(1.0, frame, 'car_door', _key('cbw', 'frame'), box, blur=0),
          _cl(0.98, glass, 'glass', _key('cbw', 'glass', reflect, lamp_reflection), (WX0 - 20, WY0 - 20, WX1 + 20, WY1 + 20), blur=0),
          Layer(0.975, glass_dyn, 'glass_lights', blur=0)]
    a = {'man': Anchor(990, 1150, 1.2, 1.85 * 760 / 1.2 * 0.62, note='seated: feet hidden; head centre ~ (990, 430)'),
         'hand_on_glass': Anchor(1050, 520, 0.99, 0, note='hand / card pressed on the glass (draw at depth 0.99)')}
    return SetPiece('car_backseat_window', L, a, {}, lens=None, grade='night_blue', focus=1.2, dof=4.0, cover=FRAME,
                    fx=(lambda t: {'flash': police_flash(t, 0.25)}) if police else None,
                    info={'window': (WX0, WY0, WX1, WY1), 'lights': lf})


# ============================================================== interiors: shared pieces
def _wallpaper(pen, path, box, s, base='#3a3f52', ink='#2a2e3e', kind='damask', a=150, hi=None, seed=0):
    """Wallpaper on a (front-facing) wall area. s = px per metre at that depth."""
    x0, y0, x1, y1 = box
    pen.fill(path, base)
    pen.cv.save(); pen.cv.clipPath(path, skia.ClipOp.kIntersect, True)
    pen.texture(path, 'plaster', 0.35, 'overlay', 0.8)
    if kind == 'stripe':
        k = 0; x = x0
        while x < x1:
            pen.fill(rect(x, y0, 0.06 * s, y1 - y0), ink, a * (0.6 if k % 2 else 1.0)); x += 0.16 * s; k += 1
    elif kind == 'damask':
        dx, dy = 0.32 * s, 0.4 * s
        j = 0; y = y0
        while y < y1 + dy:
            x = x0 + (dx / 2 if j % 2 else 0)
            while x < x1 + dx:
                m = smooth([(x, y - 0.12 * s), (x + 0.06 * s, y - 0.03 * s), (x + 0.1 * s, y + 0.02 * s), (x + 0.03 * s, y + 0.05 * s),
                            (x, y + 0.13 * s), (x - 0.03 * s, y + 0.05 * s), (x - 0.1 * s, y + 0.02 * s), (x - 0.06 * s, y - 0.03 * s)], True, 0.8)
                pen.fill(m, ink, a)
                pen.fill(oval(x, y - 0.18 * s, 0.018 * s), ink, a)
                x += dx
            y += dy; j += 1
    elif kind == 'floral':
        rng = np.random.default_rng(seed)
        dx, dy = 0.28 * s, 0.3 * s
        j = 0; y = y0
        while y < y1 + dy:
            x = x0 + (dx / 2 if j % 2 else 0)
            while x < x1 + dx:
                for p in range(5):
                    ang = p * 2 * math.pi / 5 + rng.uniform(0, 0.3)
                    pen.fill(oval(x + math.cos(ang) * 0.028 * s, y + math.sin(ang) * 0.028 * s, 0.022 * s), ink, a)
                pen.fill(oval(x, y, 0.014 * s), hi or _lighten(ink, 0.4), a)
                pen.line(smooth([(x, y + 0.04 * s), (x + 0.04 * s, y + 0.1 * s), (x + 0.02 * s, y + 0.15 * s)], False), max(0.8, 0.008 * s), '#3a5a3a', a * 0.8)
                x += dx
            y += dy; j += 1
    pen.cv.restore()


def _side_wall(pen, v, X, D0, D1, Y0, Y1, base, ink=None, kind='stripe', a=110, wains=0.0, wc='#2a2a30', shade=0.35):
    """A side wall (plane X = const) from depth D0 (far) to D1 (near), Y0..Y1. Stripes follow the perspective."""
    path = v.quad([(X, Y0, D0), (X, Y1, D0), (X, Y1, D1), (X, Y0, D1)])
    xa, xb = v.x(X, D0), v.x(X, D1)
    pen.linear(path, xa, 0, xb, 0, [base, _darken(base, shade)])
    pen.cv.save(); pen.cv.clipPath(path, skia.ClipOp.kIntersect, True)
    pen.texture(path, 'plaster', 0.3, 'overlay', 0.8)
    if ink:
        D = D0; k = 0
        while D > D1:
            if kind == 'stripe':
                pen.fill(v.quad([(X, Y0, D), (X, Y1, D), (X, Y1, D * 0.975), (X, Y0, D * 0.975)]), ink, a * (0.6 if k % 2 else 1.0))
            else:
                for Y in np.arange(Y0 + 0.2, Y1, 0.4):
                    x, y = v.p(X, Y + (0.2 if k % 2 else 0), D); ss = v.s(D) * 0.5
                    pen.fill(oval(x, y, 0.04 * ss, 0.08 * ss), ink, a)
            D *= 0.9; k += 1
    if wains:
        wp = v.quad([(X, Y0, D0), (X, Y0 + wains, D0), (X, Y0 + wains, D1), (X, Y0, D1)])
        pen.linear(wp, xa, 0, xb, 0, [wc, _darken(wc, shade)])
        pen.line(poly([v.p(X, Y0 + wains, D0), v.p(X, Y0 + wains, D1)], False), max(3, 0.03 * v.s(D1)), _lighten(wc, 0.2))
        D = D0
        while D > D1 + 0.05:
            pen.line(v.quad([(X, Y0 + 0.12, D), (X, Y0 + wains - 0.12, D), (X, Y0 + wains - 0.12, D * 0.88), (X, Y0 + 0.12, D * 0.88)]),
                     max(1.5, 0.012 * v.s(D)), _darken(wc, 0.4), 200)
            D *= 0.84
    pen.cv.restore()
    pen.line(path, 2, LINE, 160)
    return path


def _floorboards(pen, v, X0, X1, D0, D1, c0='#3a2a20', c1='#24190f', step=0.13, Y=0.0, tex_a=0.45):
    """Wooden floor (boards running toward the back wall) from D0 (far) to D1 (near)."""
    path = v.quad([(X0, Y, D0), (X1, Y, D0), (X1, Y, D1), (X0, Y, D1)])
    pen.linear(path, 0, v.y(Y, D0), 0, min(v.y(Y, D1), 1800), [c0, c1])
    pen.texture(path, 'wood', tex_a, 'overlay', 1.6, 90)
    X = X0; i = 0
    while X <= X1:
        pen.seg(v.p(X, Y, D0), v.p(X, Y, D1), max(1.0, 0.01 * v.s(D1)), '#0d0806', 190)
        Dj = D1 + (D0 - D1) * _h(i, 3)
        pen.seg(v.p(X, Y, Dj), v.p(X + step, Y, Dj), max(0.8, 0.008 * v.s(Dj)), '#0d0806', 160)
        X += step; i += 1
    return path


def _rug(pen, v, X0, X1, D0, D1, c='#5a2424', border='#2a1414', pat='#8a6a3a', Y=0.003):
    path = v.quad([(X0, Y, D0), (X1, Y, D0), (X1, Y, D1), (X0, Y, D1)])
    pen.fill(path, c); pen.texture(path, 'fabric', 0.6, 'overlay', 1.2)
    inner = v.quad([(X0 + 0.1, Y, D0 - 0.03), (X1 - 0.1, Y, D0 - 0.03), (X1 - 0.1, Y, D1 + 0.03), (X0 + 0.1, Y, D1 + 0.03)])
    pen.line(inner, 4, border, 220); pen.line(path, 3, border, 255)
    n = 5
    for k in range(n):
        D = D0 - (D0 - D1) * (k + 0.5) / n
        cx = (X0 + X1) / 2
        dm = v.quad([(cx, Y, D + 0.06 * D), (cx + 0.18, Y, D), (cx, Y, D - 0.06 * D), (cx - 0.18, Y, D)])
        pen.fill(dm, pat, 200); pen.line(dm, 2, border, 200)
    for k in range(int((X1 - X0) / 0.04)):                       # fringe at the far end
        X = X0 + k * 0.04
        pen.seg(v.p(X, Y, D0), v.p(X, Y, D0 + 0.02 * D0), 1.2, '#c9b89a', 180)
    return path


def _picture(pen, x, y, w, h, kind='photo', frame='#2a1f18', mat='#d8d0c0', s=100.0, seed=0, glass=True):
    """A framed picture: kind 'photo' (the family photograph), 'landscape', 'portrait', 'mirror'."""
    fw = max(3.0, min(w, h) * 0.08)
    pen.shadow(rect(x, y, w, h), 0.02 * s, 0.03 * s, 0.03 * s, '#000000', 120)
    pen.shape(rect(x, y, w, h), frame, max(1.2, fw * 0.25))
    pen.fill(rect(x + fw * 0.35, y + fw * 0.35, w - fw * 0.7, h - fw * 0.7), _lighten(frame, 0.15))
    ix, iy, iw, ih = x + fw, y + fw, w - 2 * fw, h - 2 * fw
    if kind != 'mirror':
        pen.fill(rect(ix, iy, iw, ih), mat)
        m = min(iw, ih) * 0.1
        ix, iy, iw, ih = ix + m, iy + m, iw - 2 * m, ih - 2 * m
    if kind == 'photo':
        _photo_content(pen, ix, iy, iw, ih)
    elif kind == 'landscape':
        pen.linear(rect(ix, iy, iw, ih), 0, iy, 0, iy + ih, ['#5a7a9a', '#c8b48a'])
        pen.fill(poly([(ix, iy + ih * 0.7), (ix + iw * 0.35, iy + ih * 0.35), (ix + iw * 0.6, iy + ih * 0.6), (ix + iw * 0.8, iy + ih * 0.45),
                       (ix + iw, iy + ih * 0.65), (ix + iw, iy + ih), (ix, iy + ih)]), '#3a4a3a')
    elif kind == 'portrait':
        pen.fill(rect(ix, iy, iw, ih), '#3a3028')
        pen.fill(oval(ix + iw / 2, iy + ih * 0.4, iw * 0.2, ih * 0.18), '#a89080')
        pen.fill(rrect(ix + iw * 0.2, iy + ih * 0.62, iw * 0.6, ih * 0.5, iw * 0.2), '#2a2420')
    elif kind == 'mirror':
        pen.linear(rect(ix, iy, iw, ih), ix, 0, ix + iw, 0, ['#2a3040', '#4a5268', '#252a38'])
        pen.fill(poly([(ix + iw * 0.15, iy + ih), (ix + iw * 0.3, iy + ih), (ix + iw * 0.75, iy), (ix + iw * 0.6, iy)]), '#ffffff', 30)
    if glass and kind != 'mirror':
        pen.fill(poly([(ix, iy + ih * 0.35), (ix + iw * 0.35, iy), (ix + iw * 0.5, iy), (ix, iy + ih * 0.55)]), '#ffffff', 26)
    pen.line(rect(x, y, w, h), max(1.0, fw * 0.2), LINE)


def _photo_content(pen, x, y, w, h, faded=0.0):
    """The family photograph: a lake at golden hour, mother and child on a jetty (the father took it)."""
    cv = pen.cv; cv.save(); cv.clipPath(rect(x, y, w, h), skia.ClipOp.kIntersect, True)
    pen.linear(rect(x, y, w, h), 0, y, 0, y + h * 0.55, ['#7aa0c0', '#e8c890'])
    pen.radial(None, x + w * 0.72, y + h * 0.42, w * 0.35, [(0, '#fff0c8', 200), (1, '#fff0c8', 0)], clip=False)
    pen.fill(poly([(x, y + h * 0.5), (x + w * 0.25, y + h * 0.38), (x + w * 0.45, y + h * 0.47), (x + w * 0.7, y + h * 0.36),
                   (x + w, y + h * 0.48), (x + w, y + h * 0.56), (x, y + h * 0.56)]), '#4a5a6a')
    pen.linear(rect(x, y + h * 0.55, w, h * 0.45), 0, y + h * 0.55, 0, y + h, ['#c8a878', '#3a5a7a'])
    for k in range(6):
        yy = y + h * (0.6 + k * 0.06); pen.seg((x + w * 0.1, yy), (x + w * 0.9, yy), max(0.5, h * 0.006), '#f0e0c0', 70)
    jet = poly([(x + w * 0.05, y + h), (x + w * 0.42, y + h * 0.72), (x + w * 0.5, y + h * 0.72), (x + w * 0.3, y + h)])
    pen.fill(jet, '#4a3626')
    # mother (taller) and child, silhouettes with warm rim
    mx, my = x + w * 0.44, y + h * 0.72
    pen.fill(oval(mx, my - h * 0.27, w * 0.035, h * 0.05), '#2a1e18')
    pen.fill(smooth([(mx - w * 0.05, my), (mx - w * 0.045, my - h * 0.2), (mx, my - h * 0.23), (mx + w * 0.045, my - h * 0.2), (mx + w * 0.05, my)], True, 0.5), '#5a2a30')
    pen.fill(smooth([(mx - w * 0.04, my - h * 0.3), (mx - w * 0.05, my - h * 0.24), (mx + w * 0.05, my - h * 0.24), (mx + w * 0.045, my - h * 0.31)], True), '#3a2418')
    cx_, cy_ = x + w * 0.52, y + h * 0.73
    pen.fill(oval(cx_, cy_ - h * 0.17, w * 0.026, h * 0.038), '#2a1e18')
    pen.fill(smooth([(cx_ - w * 0.035, cy_), (cx_ - w * 0.03, cy_ - h * 0.12), (cx_ + w * 0.03, cy_ - h * 0.12), (cx_ + w * 0.035, cy_)], True, 0.5), '#3a5a8a')
    pen.seg((mx + w * 0.03, my - h * 0.15), (cx_ - w * 0.02, cy_ - h * 0.1), max(1.0, w * 0.012), '#5a2a30')        # holding hands
    if faded: pen.fill(rect(x, y, w, h), '#e8d8b8', 90 * faded)
    pen.fill(rect(x, y, w, h), '#d8b880', 30)
    cv.restore()


def _table_lamp(pen, x, y, s, k=1.0, shade_c='#d8c8a0', base_c='#3a2e26', glow=True):
    """Table lamp standing at (x, y) (bottom of the base), s = px per metre."""
    if k > 0.01 and glow:
        pen.radial(None, x, y - 0.42 * s, 1.7 * s, [(0, '#ffcf8f', 70 * k), (0.5, '#ffcf8f', 26 * k), (1, '#ffcf8f', 0)], clip=False)
        pen.cone(x, y - 0.33 * s, 0.32 * s, 0.9 * s, 0.4 * s, '#ffd9a0', 60 * k, 0.05 * s)
        pen.cone(x, y - 0.75 * s, 0.2 * s, 0.6 * s, 0.4 * s, '#ffd9a0', 0, 0.05 * s)
    base = smooth([(x - 0.07 * s, y), (x - 0.1 * s, y - 0.12 * s), (x - 0.04 * s, y - 0.3 * s), (x + 0.04 * s, y - 0.3 * s),
                   (x + 0.1 * s, y - 0.12 * s), (x + 0.07 * s, y)], True, 0.6)
    pen.shape(base, base_c, max(1, 0.012 * s)); pen.fill(rect(x - 0.12 * s, y - 0.02 * s, 0.24 * s, 0.02 * s), base_c)
    shade = poly([(x - 0.11 * s, y - 0.62 * s), (x + 0.11 * s, y - 0.62 * s), (x + 0.2 * s, y - 0.34 * s), (x - 0.2 * s, y - 0.34 * s)])
    pen.fill(shade, mix(_darken(shade_c, 0.5), shade_c, k))
    pen.radial(shade, x, y - 0.4 * s, 0.25 * s, [(0, mix(shade_c, '#fff4dc', k), 255), (1, mix(_darken(shade_c, 0.5), shade_c, k * 0.8), 255)])
    pen.line(shade, max(1, 0.012 * s), LINE)
    if k > 0.01: pen.fill(oval(x, y - 0.335 * s, 0.17 * s, 0.018 * s), '#fff8ee', 230 * k)


def _door_front(pen, x, y, w, h, s, c='#4a2c20', panels=6, knob=True, deadbolt=True, chain=0.0, peep=True, slot=True,
                slot_open=0.0, inside=True, lit_gap=0.0, feet=None, trim='#b8b0a0'):
    """Panelled wooden front door seen from inside: (x, y) top-left of the leaf, w x h design px, s px/m.
    chain 0..1 (0 = hanging free, 1 = engaged), slot_open 0..1 (mail-slot flap), lit_gap = porch light under the door,
    feet = list of x fractions where shadows of feet break the light gap."""
    tw = 0.09 * s
    pen.shape(rect(x - tw, y - tw, w + 2 * tw, h + tw), trim, max(1.5, 0.012 * s))
    pen.fill(rect(x - tw * 0.4, y - tw * 0.4, w + tw * 0.8, h + tw * 0.4), _darken(trim, 0.3))
    leaf = rect(x, y, w, h)
    pen.linear(leaf, x, 0, x + w, 0, [_lighten(c, 0.06), c, _darken(c, 0.2)])
    pen.texture(leaf, 'wood', 0.55, 'overlay', 1.4, 0, x, y)
    rows = 3 if panels == 6 else 2
    for r in range(rows):
        for cl in range(2):
            ph = h * (0.24 if r < rows - 1 else 0.3) if rows == 3 else h * 0.38
            py = y + h * [0.06, 0.36, 0.64][r] if rows == 3 else y + h * [0.08, 0.53][r]
            px = x + w * (0.1 + cl * 0.45); pw = w * 0.35
            pr = rect(px, py, pw, ph)
            pen.fill(pr, _darken(c, 0.12))
            pen.fill(rect(px, py, pw, ph * 0.06), _darken(c, 0.45), 200)
            pen.fill(rect(px, py, pw * 0.06, ph), _darken(c, 0.35), 200)
            pen.fill(rect(px, py + ph * 0.94, pw, ph * 0.06), _lighten(c, 0.15), 160)
            pen.line(pr, max(1, 0.008 * s), '#000000', 120)
            pen.texture(pr, 'wood', 0.5, 'overlay', 1.1, 0, px, py)
    if lit_gap > 0.01:
        gy = y + h
        pen.fill(rect(x + 0.02 * s, gy - 0.012 * s, w - 0.04 * s, 0.014 * s), '#ffd9a0', 255 * lit_gap)
        pen.radial(None, x + w / 2, gy, w * 0.75, [(0, '#ffcf8f', 70 * lit_gap), (1, '#ffcf8f', 0)], sy=0.12, clip=False)
        for fx in (feet or []):
            pen.fill(rect(x + w * fx - 0.06 * s, gy - 0.014 * s, 0.12 * s, 0.016 * s), '#050302', 250)
    pen.line(leaf, max(1.2, 0.01 * s), LINE)
    kx = x + w * 0.86
    if knob:
        pen.shape(rrect(kx - 0.035 * s, y + h * 0.5 - 0.11 * s, 0.07 * s, 0.22 * s, 0.03 * s), '#8a7032', max(1, 0.006 * s))
        pen.radial(oval(kx, y + h * 0.5, 0.045 * s), kx - 0.015 * s, y + h * 0.5 - 0.015 * s, 0.06 * s, [(0, '#f0d890'), (1, '#8a6a2a')])
        pen.line(oval(kx, y + h * 0.5, 0.045 * s), max(1, 0.005 * s), LINE)
    if deadbolt:
        dy = y + h * 0.42
        pen.shape(oval(kx, dy, 0.04 * s), '#9a7a3a', max(1, 0.005 * s))
        pen.shape(rrect(kx - 0.012 * s, dy - 0.035 * s, 0.024 * s, 0.07 * s, 0.01 * s), '#c9a64a', max(1, 0.005 * s))
    if chain is not None:
        cy = y + h * 0.36
        pen.shape(rrect(kx - 0.02 * s, cy - 0.015 * s, 0.1 * s, 0.03 * s, 0.01 * s), '#9a8a6a', max(1, 0.004 * s))
        if chain > 0.5:
            pts = [(kx + 0.06 * s, cy), (kx + w * 0.14 + 0.06 * s, cy)]
        else:
            pts = [(kx + 0.06 * s, cy), (kx + 0.05 * s, cy + 0.12 * s), (kx + 0.03 * s, cy + 0.2 * s)]
        cp = smooth(pts, False, 0.8)
        meas = skia.PathMeasure(cp, False); L_ = meas.getLength(); n = int(L_ / (0.022 * s))
        for i in range(n):
            pos, _ = meas.getPosTan((i + 0.5) * L_ / n)
            pen.line(oval(pos.x(), pos.y(), 0.008 * s, 0.012 * s) if i % 2 else oval(pos.x(), pos.y(), 0.012 * s, 0.007 * s), max(1, 0.005 * s), '#b8a880')
    if peep:
        px, py = x + w / 2, y + h * 0.23
        pen.fill(oval(px, py, 0.03 * s), '#c9a64a'); pen.fill(oval(px, py, 0.014 * s), '#fff2d8')
        pen.line(oval(px, py, 0.03 * s), max(1, 0.005 * s), LINE)
    if slot:
        sx, sy, sw, sh = x + w * 0.3, y + h * 0.58, w * 0.4, 0.06 * s
        pen.shape(rrect(sx - 0.02 * s, sy - 0.02 * s, sw + 0.04 * s, sh + 0.04 * s, 0.01 * s), '#9a7a3a', max(1, 0.005 * s))
        pen.fill(rect(sx, sy, sw, sh), '#0a0806' if slot_open > 0.05 else '#7a5e2a')
        if slot_open > 0.05:
            pen.fill(rect(sx, sy, sw, sh * slot_open), '#ffcf8f', 120)
            pen.shape(rect(sx, sy - sh * 0.9 * slot_open, sw, sh * 0.9 * slot_open), '#c9a64a', max(1, 0.004 * s))
        pen.fill(rect(sx, sy, sw, sh * 0.25), '#c9a64a', 120)


def _near_frame(pen, box, left=(-400, 160), right=(1760, 2400), c='#0c0a0a', trim=None):
    """Very near doorway jambs framing the shot (draw on a layer at depth ~0.5)."""
    x0, y0, x1, y1 = box
    for (a, b) in (left, right):
        if a is None: continue
        r = rect(a, y0, b - a, y1 - y0)
        pen.linear(r, a, 0, b, 0, [c, _lighten(c, 0.08)] if a < 960 else [_lighten(c, 0.08), c])
        pen.texture(r, 'wood', 0.25, 'overlay', 1.6, 90)
        if trim:
            ex = b if a < 960 else a
            pen.fill(rect(ex - 14 if a < 960 else ex, y0, 14, y1 - y0), trim, 200)


def _police_window_glow(lf, x, y, r, sy=0.6, k=1.0):
    def draw(pen, t):
        r_, b_ = lf(t)
        r_, b_ = _lv(r_), _lv(b_)
        if r_ > 0.02: pen.radial(None, x - r * 0.2, y, r, [(0, '#ff2a2a', 100 * r_ * k), (0.5, '#ff2a2a', 34 * r_ * k), (1, '#ff2a2a', 0)], sy=sy, clip=False)
        if b_ > 0.02: pen.radial(None, x + r * 0.2, y, r, [(0, '#3a5cff', 100 * b_ * k), (0.5, '#3a5cff', 34 * b_ * k), (1, '#3a5cff', 0)], sy=sy, clip=False)
    return draw


def headlight_sweep(pen, t, t0, dur, box, panes=(2, 2), c='#fff0c8', a=55, direction=1, skew=0.35):
    """Headlights of a passing car sweeping across a wall: a window-shaped light patch (with mullion shadows) sliding
    across `box` (x0, y0, x1, y1) between t0 and t0 + dur. Returns True while visible."""
    u = (t - t0) / dur
    if not (0.0 <= u <= 1.0): return False
    x0, y0, x1, y1 = box
    w = (x1 - x0) * 0.32; h = (y1 - y0) * 0.7
    cx = x0 - w + (x1 - x0 + 2 * w) * (ease_in_out(u) if direction > 0 else 1 - ease_in_out(u))
    k = math.sin(math.pi * u) ** 0.6
    sk = skew * h * (1 if direction > 0 else -1) * (u - 0.5) * 2
    patch = poly([(cx - w / 2 + sk, y0 + (y1 - y0) * 0.1), (cx + w / 2 + sk, y0 + (y1 - y0) * 0.1), (cx + w / 2 - sk, y0 + (y1 - y0) * 0.1 + h),
                  (cx - w / 2 - sk, y0 + (y1 - y0) * 0.1 + h)])
    pen.cv.save(); pen.cv.clipPath(rect(x0, y0, x1 - x0, y1 - y0), skia.ClipOp.kIntersect, True)
    pen.fill(patch, c, a * k, blur=34)
    for i in range(1, panes[0]):
        xx = cx - w / 2 + w * i / panes[0]
        pen.fill(poly([(xx - 6 + sk, y0 + (y1 - y0) * 0.1), (xx + 6 + sk, y0 + (y1 - y0) * 0.1), (xx + 6 - sk, y0 + (y1 - y0) * 0.1 + h),
                       (xx - 6 - sk, y0 + (y1 - y0) * 0.1 + h)]), '#000000', 60 * k, blur=6)
    pen.cv.restore()
    return True


def _curtain(pen, x, y, w, h, t, side=-1, c='#5a2a2a', sway=1.0, seed=0, open_=0.0, folds=6, lit=None):
    """Drapery hanging from (x, y), width w, height h; sways with noise (sway), side -1 gathers left / +1 right."""
    n = folds
    pts_top = [(x + w * i / n, y) for i in range(n + 1)]
    bot = []
    for i in range(n + 1):
        u = i / n
        dx = sway * (10 + 18 * u) * noise1(t * 0.45 + u * 0.8 + seed, seed) + sway * 6 * noise1(t * 1.3 + u * 2, seed + 4)
        bot.append((x + w * u + dx * (0.3 + 0.7 * (1 - abs(u - 0.5) * 2)), y + h + 6 * math.sin(u * math.pi * n)))
    path = poly(pts_top + bot[::-1])
    pen.linear(path, x, 0, x + w, 0, [c, _darken(c, 0.25)] * (n // 2) + [c])
    for i in range(1, n):
        a_ = pts_top[i]; b_ = bot[i]
        pen.line(poly([a_, ((a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2 + 4), b_], False), max(2, w * 0.012), _darken(c, 0.45), 180)
        pen.line(poly([(a_[0] + w * 0.03, a_[1]), (b_[0] + w * 0.03, b_[1])], False), max(1.5, w * 0.008), _lighten(c, 0.18), 120)
    if lit: pen.linear(path, x, 0, x + w, 0, [(0, lit[0], 0), (1, lit[0], lit[1])] if side < 0 else [(0, lit[0], lit[1]), (1, lit[0], 0)])
    pen.line(path, max(1.5, w * 0.01), LINE, 220)


def _outside_layers(tag, v, car, police, lf, lamps=(-6.0, 7.5), moon=(1300, 160, 30), tree=(-3.6, 3.3), wind=1.0, box=FRAME):
    """The street seen from inside the house (through a window): sky, houses across, lamps, road, yard, car."""
    backdrop = _combine(_sky_draw(v, (box[0], box[1], box[2], v.gy(8) + 30), moon, seed=21, clouds=((500, 160, 700, 40), (1500, 110, 700, 36))),
                        _far_draw(v, 22, (-60, 60)), _houses_draw(v, 8.0, [-20, -7.5, 5.0, 17.5]), _lamps_draw(v, 6.0, lamps))
    L = [_cl(9.0, backdrop, 'out_backdrop', _key(tag, 'backdrop', box), (box[0], box[1], box[2], min(box[3], v.gy(4.4))), blur=0),
         _cl(5.0, _combine(_street_draw(v, (-40, 40)), _yard_draw(v, d0=1.6)), 'out_ground', _key(tag, 'ground', box),
             (box[0], max(box[1], min(v.gy(5.7) - 4, v.y(v.ground + 1.6, 4.2))), box[2], min(box[3], v.gy(1.6) + 60)))]
    if tree: L.append(Layer(tree[1], _tree_layer_draw(v, tree[0], tree[1], 9.5, 31, wind), 'out_tree'))
    if car:
        cd = car.get('D', 4.85); L.append(Layer(cd, _car_layer_draw(v, cd, car, lf), 'car'))
    if police:
        def hg(pen, c):
            s = v.s(8.0)
            for X in [-20, -7.5, 5.0, 17.5]:
                pen.radial(None, v.x(X, 8), v.gy(8) - 2.5 * s, 9 * s, [(0, c, 255), (1, c, 0)], sy=0.5, clip=False)
        L += _spill_pair(8.95, hg, _key(tag, 'hsp', box), (box[0], max(box[1], v.gy(8) - 9.5 * v.s(8)), box[2], v.gy(8) + 4), lf, 0.22, 0.26, 'out_house_spill')
    return L


# ============================================================== hallway
def hallway(police=True, lamp=1.0, porch_light=1.0, feet=None, chain=0.0, slot_open=None, door_c='#4f2c20', wall='#3b3a48',
            photo=True, coats=True, sweep=None, flick=None, stairs=False, bowl='house', door_open=0.0, outside=None):
    """Your front hall, looking at the front door from inside (lens None or 'lens', grade 'interior_dim').
    Door: 6-panel wood with grain, peephole, brass deadbolt + knob, chain (chain=0 hanging, 1 engaged), mail slot
    (slot_open = f(t) -> 0..1), transom window above (porch light + police red/blue through it), light gap under the door
    with feet shadows (feet = f(t) -> list of x fractions or None). Walls: damask wallpaper over dark wainscot; left wall
    coat hooks with coats; right wall console table with a lamp, key bowl and THE PHOTOGRAPH above it; runner rug on
    floorboards; a smoke detector. sweep = (t0, dur) headlight sweep across the right wall.
    Anchors: 'door' (someone standing at the door inside), 'you' (near camera), 'table_edge' (grip point).
    Delivery film: stairs=True (the staircase rises along the left wall toward the camera instead of the coat hooks:
    newel post, balusters, runner, under-stair panelling; anchors stairs_low / stairs_mid), bowl = 'house' | 'dad' (his
    rusted keys on the kid-made keychain) | 'empty' | None, door_open = 0..1 or f(t) (the door swings in on its hinges and
    the porch world is seen through the doorway: outside = dict(tod='night'|'dawn', era='now'|'memory', box=...,
    vehicle='van'|'wagon'|None, hazard, van, windows, car_X) -> porch, box, street, van, moon in the doorway; light spills
    in across the floor). Use delivery_hall() / porch_doorway()."""
    v = View(620, 430, 1.5)
    Db, Dn = 2.0, 0.55
    HW = 1.35; CH = 2.5
    lf = _lights_fn(police)
    box = FRAME
    dw, dh = 0.92 * v.s(Db), 2.05 * v.s(Db)
    dx, dy = v.x(-0.46, Db), v.gy(Db) - dh
    opening = bool(door_open) or callable(door_open)
    th_fn = (door_open if callable(door_open) else (lambda t: float(door_open))) if opening else (lambda t: 0.0)

    def back(pen, t):
        s = v.s(Db)
        wall_p = v.quad([(-HW, 0, Db), (HW, 0, Db), (HW, CH, Db), (-HW, CH, Db)])
        if opening:
            wall_p = minus(wall_p, rect(dx, dy, dw, dh))
            pen.cv.save(); pen.cv.clipPath(minus(rect(-2000, -2000, 6000, 6000), rect(dx, dy, dw, dh)), skia.ClipOp.kIntersect, True)
        bx0, by0 = v.p(-HW, CH, Db); bx1, by1 = v.p(HW, 0, Db)
        _wallpaper(pen, wall_p, (bx0, by0, bx1, by1), s, wall, _darken(wall, 0.3), 'damask', 170)
        pen.linear(wall_p, 0, by0, 0, by1, [(0, '#000000', 90), (0.5, '#000000', 0), (1, '#000000', 60)])
        wc = v.quad([(-HW, 0, Db), (HW, 0, Db), (HW, 0.9, Db), (-HW, 0.9, Db)])
        pen.linear(wc, 0, v.y(0.9, Db), 0, v.gy(Db), ['#2a2626', '#1c1919'])
        for X0 in (-HW + 0.08, 0.55):
            pen.line(v.quad([(X0, 0.14, Db), (X0 + 0.45, 0.14, Db), (X0 + 0.45, 0.78, Db), (X0, 0.78, Db)]), 2.5, '#0e0c0c', 200)
        pen.fill(v.quad([(-HW, 0.88, Db), (HW, 0.88, Db), (HW, 0.94, Db), (-HW, 0.94, Db)]), '#4a4440')
        pen.fill(v.quad([(-HW, 0, Db), (HW, 0, Db), (HW, 0.12, Db), (-HW, 0.12, Db)]), '#2e2a28')
        # transom window above the door (porch light behind it)
        tx0, ty0 = v.p(-0.46, 2.36, Db); tx1, ty1 = v.p(0.46, 2.14, Db)
        pen.shape(rect(tx0 - 8, ty0 - 8, tx1 - tx0 + 16, ty1 - ty0 + 16), '#b8b0a0', 3)
        pen.radial(rect(tx0, ty0, tx1 - tx0, ty1 - ty0), (tx0 + tx1) / 2 - 60, ty1, (tx1 - tx0) * 0.7,
                   [(0, mix('#20283a', '#ffd9a0', porch_light)), (1, mix('#141a28', '#9a7048', porch_light))])
        for k in range(1, 4): pen.seg((tx0 + (tx1 - tx0) * k / 4, ty0), (tx0 + (tx1 - tx0) * k / 4, ty1), 4, '#b8b0a0')
        # light switch + thermostat
        sx_, sy_ = v.p(0.68, 1.25, Db)
        pen.shape(rrect(sx_, sy_, 0.08 * s, 0.12 * s, 3), '#cfc8b8', 2); pen.fill(rect(sx_ + 0.03 * s, sy_ + 0.035 * s, 0.02 * s, 0.05 * s), '#9a9488')
        if opening:                                     # the empty frame: casing + the jamb's inner reveal
            pen.cv.restore()
            tw = 0.09 * s
            pen.shape(minus(rect(dx - tw, dy - tw, dw + 2 * tw, dh + tw), rect(dx, dy, dw, dh)), '#b8b0a0', max(1.5, 0.012 * s))
            pen.fill(rect(dx, dy, 0.035 * s, dh), '#6a5e50'); pen.fill(rect(dx + dw - 0.035 * s, dy, 0.035 * s, dh), '#8a7e6e')
            pen.fill(rect(dx, dy, dw, 0.03 * s), '#5a5044'); pen.fill(rect(dx, dy + dh - 0.02 * s, dw, 0.02 * s), '#8a7a5a')
        else:
            _door_front(pen, dx, dy, dw, dh, s, door_c, chain=None, slot=True, peep=True, lit_gap=0.0)

    def door_dyn(pen, t):
        if th_fn(t) > 0.005: return
        s = v.s(Db)
        so = slot_open(t) if slot_open else 0.0
        ft = feet(t) if feet else None
        ch = chain(t) if callable(chain) else chain
        # only the parts that change: mail slot, chain, light gap, peephole glint
        kx = dx + dw * 0.86; cy = dy + dh * 0.36
        pen.shape(rrect(kx - 0.02 * s, cy - 0.015 * s, 0.1 * s, 0.03 * s, 0.01 * s), '#9a8a6a', 1.5)
        pts = [(kx + 0.06 * s, cy), (kx + dw * 0.14 + 0.06 * s, cy)] if ch > 0.5 else [(kx + 0.06 * s, cy), (kx + 0.055 * s, cy + 0.1 * s), (kx + 0.03 * s, cy + 0.19 * s)]
        cp = smooth(pts, False, 0.8)
        meas = skia.PathMeasure(cp, False); L_ = meas.getLength(); n = max(2, int(L_ / (0.022 * s)))
        for i in range(n):
            pos, _ = meas.getPosTan((i + 0.5) * L_ / n)
            pen.line(oval(pos.x(), pos.y(), 0.008 * s, 0.012 * s) if i % 2 else oval(pos.x(), pos.y(), 0.012 * s, 0.007 * s), 1.6, '#b8a880')
        if ch > 0.5: pen.shape(rrect(dx + dw - 0.02 * s, cy - 0.02 * s, 0.05 * s, 0.04 * s, 0.01 * s), '#9a8a6a', 1.5)
        if so > 0.02:
            sx, sy, sw, sh = dx + dw * 0.3, dy + dh * 0.58, dw * 0.4, 0.06 * s
            pen.fill(rect(sx, sy, sw, sh), '#0a0806')
            pen.fill(rect(sx, sy + sh * (1 - so), sw, sh * so), '#ffcf8f', 150 * porch_light)
            pen.shape(rect(sx, sy - sh * 0.9 * so, sw, sh * 0.9 * so), '#c9a64a', 1.5)
        gy = dy + dh
        pk = porch_light
        pen.fill(rect(dx + 0.02 * s, gy - 0.012 * s, dw - 0.04 * s, 0.014 * s), '#ffd9a0', 230 * pk)
        pen.radial(None, dx + dw / 2, gy + 0.02 * s, dw * 0.8, [(0, '#ffcf8f', 60 * pk), (1, '#ffcf8f', 0)], sy=0.14, clip=False)
        for fx in (ft or []):
            pen.fill(rect(dx + dw * fx - 0.07 * s, gy - 0.014 * s, 0.14 * s, 0.017 * s), '#050302', 250)
            pen.radial(None, dx + dw * fx, gy + 0.01 * s, 0.16 * s, [(0, '#000000', 120), (1, '#000000', 0)], sy=0.2, clip=False)
        r_, b_ = lf(t)
        tx0, ty0 = v.p(-0.46, 2.36, Db); tx1, ty1 = v.p(0.46, 2.14, Db)
        if r_ > 0.02: pen.fill(rect(tx0, ty0, (tx1 - tx0) / 2, ty1 - ty0), '#ff3030', 160 * r_)
        if b_ > 0.02: pen.fill(rect((tx0 + tx1) / 2, ty0, (tx1 - tx0) / 2, ty1 - ty0), '#4a6cff', 160 * b_)
        pen.fill(oval(dx + dw / 2, dy + dh * 0.23, 0.012 * s), '#fff8ee', 220 * pk)

    def sides(pen, t):
        _side_wall(pen, v, -HW, Db, Dn, 0, CH, wall, _darken(wall, 0.3), 'dots', 150, wains=0.9, wc='#2a2626')
        _side_wall(pen, v, HW, Db, Dn, 0, CH, wall, _darken(wall, 0.3), 'dots', 150, wains=0.9, wc='#2a2626')
        # ceiling + crown moulding
        ceil = v.quad([(-HW, CH, Db), (HW, CH, Db), (HW, CH, Dn), (-HW, CH, Dn)])
        pen.linear(ceil, 0, v.y(CH, Dn), 0, v.y(CH, Db), ['#08080b', '#1a1a20'])
        for X in (-HW, HW):
            pen.line(poly([v.p(X, CH, Db), v.p(X, CH, Dn)], False), 6, '#5a5650')
        pen.line(poly([v.p(-HW, CH, Db), v.p(HW, CH, Db)], False), 5, '#5a5650')
        sx, sy = v.p(0.0, CH, 1.2)
        pen.shape(oval(sx, sy + 6, 0.07 * v.s(1.2), 0.025 * v.s(1.2)), '#c8c4bc', 2)      # smoke detector
        pen.fill(oval(sx + 10, sy + 6, 3), '#ff2a2a', 230)

    def floor(pen, t):
        _floorboards(pen, v, -HW, HW, Db, Dn, '#33261c', '#1a120c')
        _rug(pen, v, -0.5, 0.5, Db - 0.06, Dn, '#4a1e22', '#1e0c0e', '#9a7a42')
        for X in (-HW, HW):
            pen.fill(v.quad([(X, 0, Db), (X, 0.12, Db), (X, 0.12, Dn), (X, 0, Dn)]), '#2e2a28')

    def left_props(pen, t):
        if stairs:
            _hall_stairs_side(pen, v, -HW, -0.55, 1.84, Dn, CH, wall)
            return
        X = -HW + 0.02
        a, b = v.p(X, 1.72, 1.75), v.p(X, 1.72, 1.15)
        pen.line(poly([a, b], False), 18, '#3a2a20'); pen.line(poly([a, b], False), 5, '#5a4632', 200)
        hooks = [1.68, 1.48, 1.32, 1.2]
        for i, D in enumerate(hooks):
            hx, hy = v.p(X + 0.03, 1.72, D); s = v.s(D)
            pen.line(smooth([(hx, hy), (hx + 0.05 * s, hy + 0.03 * s), (hx + 0.06 * s, hy - 0.02 * s)], False), max(2, 0.012 * s), '#b8a880')
            if coats and i in (0, 2):
                c = '#2a3242' if i == 0 else '#4a3424'
                top = (hx + 0.03 * s, hy)
                coat = smooth([top, (hx + 0.14 * s, hy + 0.1 * s), (hx + 0.17 * s, hy + 0.55 * s), (hx + 0.14 * s, hy + 0.95 * s),
                               (hx - 0.06 * s, hy + 0.98 * s), (hx - 0.04 * s, hy + 0.5 * s), (hx - 0.02 * s, hy + 0.1 * s)], True, 0.5)
                pen.shadow(coat, 0.04 * s, 0.03 * s, 0.03 * s, '#000000', 120)
                pen.shape(coat, c, max(2, 0.01 * s))
                pen.texture(coat, 'fabric', 0.45, 'overlay', 0.8)
                pen.line(smooth([(hx + 0.04 * s, hy + 0.12 * s), (hx + 0.06 * s, hy + 0.5 * s), (hx + 0.03 * s, hy + 0.9 * s)], False), max(1.5, 0.008 * s), _darken(c, 0.5), 220)
            if i == 1 and coats:                      # the empty hook: your grey coat is gone
                pass
        # umbrella stand + boots
        ux, uy = v.p(X + 0.18, 0, 1.55); s = v.s(1.55)
        pen.shape(rrect(ux - 0.1 * s, uy - 0.45 * s, 0.2 * s, 0.45 * s, 0.03 * s), '#2a2e34', max(2, 0.01 * s))
        pen.line(smooth([(ux - 0.02 * s, uy - 0.45 * s), (ux - 0.04 * s, uy - 0.8 * s), (ux - 0.1 * s, uy - 0.82 * s)], False), max(3, 0.015 * s), '#141414')
        bx, by = v.p(X + 0.25, 0, 1.25); s = v.s(1.25)
        for k in range(2):
            boot = smooth([(bx + k * 0.12 * s, by - 0.3 * s), (bx + k * 0.12 * s + 0.08 * s, by - 0.3 * s), (bx + k * 0.12 * s + 0.09 * s, by - 0.06 * s),
                           (bx + k * 0.12 * s + 0.2 * s, by - 0.03 * s), (bx + k * 0.12 * s + 0.2 * s, by), (bx + k * 0.12 * s - 0.01 * s, by)], True, 0.4)
            pen.shape(boot, '#1e1a16', max(2, 0.01 * s))

    def right_props(pen, t):
        X = HW
        # console table along the right wall (D 1.75 .. 1.25), top at 0.8 m
        D0, D1, Yt, depth_ = 1.78, 1.28, 0.8, 0.38
        top = v.quad([(X, Yt, D0), (X - depth_, Yt, D0), (X - depth_, Yt, D1), (X, Yt, D1)])
        front = v.quad([(X - depth_, Yt, D0), (X - depth_, Yt - 0.12, D0), (X - depth_, Yt - 0.12, D1), (X - depth_, Yt, D1)])
        pen.fill(top, '#5a3e2a'); pen.texture(top, 'wood', 0.5, 'overlay', 1.2)
        pen.fill(front, '#3a271a'); pen.line(front, 2.5, LINE)
        for D in (D0 - 0.02, D1 + 0.02):
            pen.seg(v.p(X - depth_ + 0.03, Yt - 0.12, D), v.p(X - depth_ + 0.03, 0, D), max(4, 0.03 * v.s(D)), '#2a1c12')
        pen.seg(v.p(X - depth_ + 0.03, 0.15, D0), v.p(X - depth_ + 0.03, 0.15, D1), 4, '#2a1c12')
        pen.line(top, 2.5, LINE)
        # key bowl with the house keys
        kx, ky = v.p(X - 0.2, Yt, 1.4); s = v.s(1.4)
        if bowl == 'house' or not stairs:
            pen.shape(smooth([(kx - 0.1 * s, ky - 0.04 * s), (kx + 0.1 * s, ky - 0.04 * s), (kx + 0.07 * s, ky), (kx - 0.07 * s, ky)], True, 0.5), '#7a8a9a', 2)
            pen.line(smooth([(kx - 0.03 * s, ky - 0.05 * s), (kx, ky - 0.08 * s), (kx + 0.03 * s, ky - 0.05 * s)], False), 2.5, '#c9a64a')
        elif bowl:
            _key_bowl_small(pen, kx, ky, s, bowl)
        # the photograph above the table (on the right wall, seen in perspective)
        if photo:
            P0, P1 = 1.66, 1.42
            fr = v.quad([(X - 0.01, 1.95, P0), (X - 0.01, 1.95, P1), (X - 0.01, 1.35, P1), (X - 0.01, 1.35, P0)])
            pen.shadow(fr, 6, 6, 6, '#000000', 120)
            pen.fill(fr, '#2a1f18'); pen.line(fr, 2.5, LINE)
            inner = v.quad([(X - 0.012, 1.9, P0 - 0.012), (X - 0.012, 1.9, P1 + 0.012), (X - 0.012, 1.4, P1 + 0.012), (X - 0.012, 1.4, P0 - 0.012)])
            pen.fill(inner, '#d8d0c0')
            b = inner.getBounds()
            pen.cv.save(); pen.cv.clipPath(inner, skia.ClipOp.kIntersect, True)
            # perspective-squashed photo: draw into the inner bounds
            _photo_content(pen, b.left() + 4, b.top() + 6, b.width() - 8, b.height() - 12)
            pen.cv.restore()
            pen.fill(minus(inner, v.quad([(X - 0.012, 1.86, P0 - 0.03), (X - 0.012, 1.86, P1 + 0.03), (X - 0.012, 1.44, P1 + 0.03), (X - 0.012, 1.44, P0 - 0.03)])), '#d8d0c0')
            # small second frame
            fr2 = v.quad([(X - 0.01, 1.62, 1.36), (X - 0.01, 1.62, 1.28), (X - 0.01, 1.4, 1.28), (X - 0.01, 1.4, 1.36)])
            pen.shape(fr2, '#c9a64a', 2)
        # mirror? a light switch
        _table_lamp(pen, *v.p(X - 0.2, Yt, 1.66), v.s(1.66), 0.0)

    def lamp_glow(pen, t):
        x, y = v.p(HW - 0.2, 0.8, 1.66); s = v.s(1.66)
        pen.radial(None, v.x(HW, 1.55), y - 0.45 * s, 1.8 * s, [(0, '#ffcf8f', 60), (0.5, '#ffcf8f', 20), (1, '#ffcf8f', 0)], sy=1.2, clip=False)
        pen.radial(None, x, y - 0.42 * s, 1.7 * s, [(0, '#ffcf8f', 70), (0.5, '#ffcf8f', 26), (1, '#ffcf8f', 0)], clip=False)
        pen.cone(x, y - 0.33 * s, 0.32 * s, 0.9 * s, 0.4 * s, '#ffd9a0', 60, 0.05 * s)

    def lamp_dyn(pen, t):
        k = lamp * (flicker(t, 9, 0.7) if flick else 1.0)
        x, y = v.p(HW - 0.2, 0.8, 1.66); s = v.s(1.66)
        _table_lamp(pen, x, y, s, k, glow=False)

    def spill_dyn(pen, t):
        r_, b_ = (_lv(c) for c in lf(t))
        cx, cy = v.p(0, CH, 1.6)
        if r_ > 0.02: pen.radial(None, cx - 120, cy + 40, 460, [(0, '#ff2a2a', 70 * r_), (1, '#ff2a2a', 0)], sy=0.35, clip=False)
        if b_ > 0.02: pen.radial(None, cx + 120, cy + 40, 460, [(0, '#3a5cff', 70 * b_), (1, '#3a5cff', 0)], sy=0.35, clip=False)
        if sweep: headlight_sweep(pen, t, sweep[0], sweep[1], (v.x(HW, 1.9), v.y(2.3, 1.9), v.x(HW, 0.9), v.y(0.6, 0.9)))

    def near(pen, t):
        _near_frame(pen, box, (-400, 40), (1880, 2400), '#0b0909', '#2a2622')

    L = [_cl(Db, back, 'back_wall', _key('hall', 'back', door_c, wall, porch_light, opening), (v.x(-HW, Db) - 20, v.y(CH, Db) - 20, v.x(HW, Db) + 20, v.gy(Db) + 20)),
         Layer(Db - 0.01, door_dyn, 'door_dyn', blur=0),
         _cl(1.5, sides, 'walls', _key('hall', 'sides2', wall), box),
         _cl(1.49, floor, 'floor', _key('hall', 'floor'), (box[0], v.gy(Db) - 10, box[2], box[3])),
         _cl(1.4, left_props, 'stairs' if stairs else 'coats', _key('hall', 'left', coats, stairs),
             (box[0], v.y(2.0, 1.15) if not stairs else box[1], v.x(-0.2, 1.15) if not stairs else v.x(-0.3, 1.9), box[3])),
         _cl(1.45, right_props, 'console', _key('hall', 'right', photo, bowl if stairs else 'house'), (v.x(0.3, 1.8), v.y(2.2, 1.25), box[2], box[3])),
         _cl(1.441, lamp_glow, 'lamp_glow', _key('hall', 'lglow'), (v.x(0.0, 1.66), v.y(2.6, 1.66), v.x(HW, 1.2) + 200, v.y(-0.3, 1.66)),
             alpha=(lambda t: lamp * (flicker(t, 9, 0.7) if flick else 1.0)), blur=0),
         Layer(1.44, lamp_dyn, 'lamp'),
         Layer(1.3, spill_dyn, 'police_spill', blur=0),
         _cl(0.5, near, 'near_frame', _key('hall', 'near'), box)]
    _exposure(L, 0.32, ('back_wall', 'walls', 'floor', 'coats', 'stairs', 'console'))
    a = {'door': v.anchor(0.0, Db - 0.2, note='standing at the door, inside'), 'you': v.anchor(-0.15, 0.85, note='near the camera'),
         'table_edge': Anchor(*v.p(HW - 0.38, 0.8, 1.4), 1.4, 0, note='front edge of the console table (grip point)')}
    info = {'view': v, 'door_rect': (dx, dy, dw, dh), 'mail_slot': (dx + dw * 0.3, dy + dh * 0.58, dw * 0.4, 0.06 * v.s(Db)),
            'peephole': (dx + dw / 2, dy + dh * 0.23), 'photo_quad_depth': 1.54, 'lights': lf}
    if stairs:
        a['stairs_low'] = v.anchor(-0.95, 1.62, Y=0.38, note='on the 2nd step (feet), facing the door')
        a['stairs_mid'] = v.anchor(-0.95, 1.1, Y=0.76, note='on the 4th step')
        a['wall_sit'] = v.anchor(0.95, 1.05, note='sitting on the floor against the right wall (sit pose)')
    if opening:
        L += _hall_doorway_layers(v, Db, dx, dy, dw, dh, door_c, th_fn, outside or {}, CH)
        info['door_open'] = th_fn
        info['doorway_cam'] = (dx + dw / 2, dy + dh * 0.52, 1.3, 1.75)        # (x, y, dolly zoom, optical factor)
        a['porch_out'] = v.anchor(0.1, Db + 0.9, note='on the porch just outside the doorway (seen through it)')
    return SetPiece('hallway', L, a, {}, lens='lens', grade='interior_dim', focus=Db, dof=2.5, cover=FRAME,
                    fx=(lambda t: {'flash': police_flash(t, 0.12)}) if police else None, info=info)


# ============================================================== kitchen
def kitchen(police=True, pendant=1.0, sway=1.0, tiles='#2f5a8a', clock=True, mug=True, sweep=None):
    """Your kitchen, seen from the table: BLUE tile backsplash (the question), cabinets, sink under a window (night outside,
    police red/blue flashing through it), fridge, stove with kettle, wall clock (hands move with t), a swaying pendant lamp
    over the table, and the table edge across the bottom (the edge you grip). lens None, grade 'interior_dim'."""
    v = View(620, 420, 1.3)
    Db, Dn, HW, CH = 2.3, 0.55, 2.6, 2.5
    lf = _lights_fn(police)
    box = FRAME

    def window_out(pen, t):
        x0, y0 = v.p(-0.62, 2.05, Db); x1, y1 = v.p(0.62, 1.1, Db)
        pen.linear(rect(x0 - 40, y0 - 40, x1 - x0 + 80, y1 - y0 + 80), 0, y0, 0, y1, ['#0a1430', '#1b2245'])
        for i in range(3):
            pen.fill(rect(x0 + 40 + i * 140, y1 - 90 - (i % 2) * 30, 110, 120), '#0a0d16')
            if i != 1: pen.fill(rect(x0 + 70 + i * 140, y1 - 60 - (i % 2) * 30, 22, 26), '#d9b47c')
        draw_tree(pen, x0 + 120, y1 + 10, 300, t, 41, 0.6, '#05070c', None, 4)

    def back(pen, t):
        s = v.s(Db)
        wall_p = v.quad([(-HW, 0, Db), (HW, 0, Db), (HW, CH, Db), (-HW, CH, Db)])
        x0, y0 = v.p(-HW, CH, Db); x1, y1 = v.p(HW, 0, Db)
        pen.linear(wall_p, 0, y0, 0, y1, ['#4a4a40', '#3a3a34'])
        pen.texture(wall_p, 'plaster', 0.4)
        # blue tile backsplash
        tp = v.quad([(-HW, 0.92, Db), (HW, 0.92, Db), (HW, 1.5, Db), (-HW, 1.5, Db)])
        pen.fill(tp, tiles)
        b = tp.getBounds(); ts = 0.1 * s
        pen.cv.save(); pen.cv.clipPath(tp, skia.ClipOp.kIntersect, True)
        j = 0; yy = b.top()
        while yy < b.bottom():
            xx = b.left(); i = 0
            while xx < b.right():
                c = mix(tiles, '#ffffff' if _h(i * 31 + j, 7) > 0.5 else '#000000', 0.06 + 0.08 * _h(i * 17 + j, 8))
                pen.fill(rect(xx + 1.5, yy + 1.5, ts - 3, ts - 3), c)
                pen.fill(rect(xx + 3, yy + 3, ts * 0.5, 2.5), '#ffffff', 60)
                xx += ts; i += 1
            yy += ts; j += 1
        pen.cv.restore()
        # window (hole left for window_out: drawn as frame + glass reflection)
        wx0, wy0 = v.p(-0.62, 2.05, Db); wx1, wy1 = v.p(0.62, 1.1, Db)
        hole = rect(wx0, wy0, wx1 - wx0, wy1 - wy0)
        pen.cv.save(); pen.cv.clipPath(hole, skia.ClipOp.kIntersect, True); pen.cv.clear(skia.ColorTRANSPARENT); pen.cv.restore()
        pen.line(rect(wx0 - 10, wy0 - 10, wx1 - wx0 + 20, wy1 - wy0 + 20), 22, '#d8d0c0')
        pen.seg(((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1), 12, '#d8d0c0')
        pen.fill(rect(wx0 - 30, wy1 + 8, wx1 - wx0 + 60, 18), '#cfc8b8')
        # valance
        pen.fill(rect(wx0 - 40, wy0 - 40, wx1 - wx0 + 80, 70), '#6a3a2a'); pen.line(rect(wx0 - 40, wy0 - 40, wx1 - wx0 + 80, 70), 3, LINE)
        # upper cabinets (left and right of the window)
        for (a, bX) in ((-HW, -0.82), (0.82, HW)):
            cab = v.quad([(a, 1.55, Db), (bX, 1.55, Db), (bX, 2.3, Db), (a, 2.3, Db)])
            pen.fill(cab, '#5a4a38'); pen.texture(cab, 'wood', 0.4, 'overlay', 1.3)
            n = int(round((bX - a) / 0.5))
            for k in range(n):
                X0 = a + (bX - a) * k / n
                d = v.quad([(X0 + 0.03, 1.58, Db), (X0 + (bX - a) / n - 0.03, 1.58, Db), (X0 + (bX - a) / n - 0.03, 2.27, Db), (X0 + 0.03, 2.27, Db)])
                pen.line(d, 2.5, '#2a2018'); pen.fill(v.quad([(X0 + 0.08, 1.66, Db), (X0 + (bX - a) / n - 0.08, 1.66, Db), (X0 + (bX - a) / n - 0.08, 2.19, Db), (X0 + 0.08, 2.19, Db)]), '#4e4030')
                hx, hy = v.p(X0 + ((bX - a) / n - 0.08 if k % 2 == 0 else 0.08), 1.64, Db)
                pen.fill(rrect(hx - 3, hy - 22, 6, 22, 3), '#b8b0a0')
            pen.line(cab, 3, LINE)
        # lower cabinets + counter
        low = v.quad([(-HW, 0.0, Db), (HW, 0.0, Db), (HW, 0.88, Db), (-HW, 0.88, Db)])
        pen.fill(low, '#4e4030'); pen.texture(low, 'wood', 0.4, 'overlay', 1.3)
        for k in range(10):
            X0 = -HW + 2 * HW * k / 10
            pen.line(v.quad([(X0 + 0.03, 0.1, Db), (X0 + 2 * HW / 10 - 0.03, 0.1, Db), (X0 + 2 * HW / 10 - 0.03, 0.82, Db), (X0 + 0.03, 0.82, Db)]), 2.5, '#2a2018')
            hx, hy = v.p(X0 + 0.25, 0.74, Db); pen.fill(rrect(hx - 14, hy, 28, 5, 2), '#b8b0a0')
        pen.fill(v.quad([(-HW, 0.0, Db), (HW, 0.0, Db), (HW, 0.1, Db), (-HW, 0.1, Db)]), '#1a1612')
        ct = v.quad([(-HW - 0.05, 0.88, Db), (HW + 0.05, 0.88, Db), (HW + 0.05, 0.94, Db), (-HW - 0.05, 0.94, Db)])
        pen.fill(ct, '#8a8478'); pen.line(ct, 2, LINE)
        # sink + faucet
        fx, fy = v.p(0, 0.94, Db)
        pen.line(smooth([(fx, fy), (fx, fy - 0.3 * s), (fx + 0.12 * s, fy - 0.33 * s), (fx + 0.16 * s, fy - 0.24 * s)], False), 7, '#a8b0b8')
        # stove (right) + kettle, fridge (left)
        sx, sy = v.p(1.3, 0.94, Db)
        pen.fill(rect(sx - 0.38 * s, sy, 0.76 * s, 0.88 * s), '#2a2c30'); pen.line(rect(sx - 0.38 * s, sy, 0.76 * s, 0.88 * s), 3, LINE)
        pen.shape(rect(sx - 0.3 * s, sy + 0.25 * s, 0.6 * s, 0.4 * s), '#0e0f12', 3)
        for k in range(4): pen.fill(oval(sx - 0.27 * s + k * 0.18 * s, sy + 0.1 * s, 0.03 * s), '#8a8e96')
        kx, ky = sx - 0.12 * s, sy
        kettle = smooth([(kx - 0.12 * s, ky), (kx - 0.13 * s, ky - 0.12 * s), (kx - 0.06 * s, ky - 0.2 * s), (kx + 0.06 * s, ky - 0.2 * s), (kx + 0.13 * s, ky - 0.12 * s), (kx + 0.12 * s, ky)], True, 0.6)
        pen.shape(kettle, '#8a2a24', 3)
        pen.line(smooth([(kx - 0.07 * s, ky - 0.2 * s), (kx, ky - 0.28 * s), (kx + 0.07 * s, ky - 0.2 * s)], False), 4, '#1a1a1a')
        fxl, fyl = v.p(-2.25, 0, Db)
        fr = rect(fxl - 0.4 * s, fyl - 1.85 * s, 0.8 * s, 1.85 * s)
        pen.linear(fr, fxl - 0.4 * s, 0, fxl + 0.4 * s, 0, ['#c8c8c4', '#9a9a96'])
        pen.line(fr, 3, LINE); pen.seg((fxl - 0.4 * s, fyl - 1.25 * s), (fxl + 0.4 * s, fyl - 1.25 * s), 3, LINE)
        pen.fill(rrect(fxl + 0.28 * s, fyl - 1.75 * s, 0.04 * s, 0.4 * s, 4), '#7a7a76'); pen.fill(rrect(fxl + 0.28 * s, fyl - 1.15 * s, 0.04 * s, 0.5 * s, 4), '#7a7a76')
        for k, (mx, my, c) in enumerate(((-0.2, 1.6, '#c9a64a'), (0.05, 1.45, '#a33a3a'), (-0.1, 1.0, '#3a6a9a'))):
            pen.fill(rect(fxl + mx * s, fyl - my * s, 0.12 * s, 0.09 * s), c, 220)   # magnets / notes
        pen.fill(rect(fxl - 0.25 * s, fyl - 1.7 * s, 0.22 * s, 0.28 * s), '#e8e0c8', 230)                # a child's drawing
        pen.line(smooth([(fxl - 0.22 * s, fyl - 1.5 * s), (fxl - 0.15 * s, fyl - 1.62 * s), (fxl - 0.08 * s, fyl - 1.5 * s)], False), 2, '#3a5aa0')

    def clock_dyn(pen, t):
        if not clock: return
        cx, cy = v.p(1.75, 2.0, Db); r = 0.17 * v.s(Db)
        pen.shape(oval(cx, cy, r), '#e8e2d4', 4); pen.line(oval(cx, cy, r * 0.88), 2, '#9a9488')
        for k in range(12):
            a = k * math.pi / 6
            pen.seg((cx + math.cos(a) * r * 0.75, cy + math.sin(a) * r * 0.75), (cx + math.cos(a) * r * 0.85, cy + math.sin(a) * r * 0.85), 2.5, '#2a2a2a')
        sec = 36 * 60 + 7 + t                                           # 12:36:07 at t = 0
        for (val, per, ln, w, c) in ((sec / 3600.0, 12, 0.5, 6, '#1a1a1a'), (sec / 60.0, 60, 0.72, 4, '#1a1a1a'), (math.floor(sec), 60, 0.8, 2, '#a32a2a')):
            a = 2 * math.pi * (val % per) / per - math.pi / 2
            pen.seg((cx, cy), (cx + math.cos(a) * r * ln, cy + math.sin(a) * r * ln), w, c)
        pen.fill(oval(cx, cy, 5), '#1a1a1a')

    def sides(pen, t):
        for X in (-HW, HW):
            _side_wall(pen, v, X, Db, Dn, 0, CH, '#43433a', None, wains=0.0, shade=0.5)
        ceil = v.quad([(-HW, CH, Db), (HW, CH, Db), (HW, CH, Dn), (-HW, CH, Dn)])
        pen.linear(ceil, 0, v.y(CH, Dn), 0, v.y(CH, Db), ['#07070a', '#1c1c1e'])
        fl = v.quad([(-HW, 0, Db), (HW, 0, Db), (HW, 0, Dn), (-HW, 0, Dn)])
        pen.fill(fl, '#3a3a40')
        # checkerboard vinyl
        X = -HW; i = 0
        while X < HW:
            D = Db; j = 0
            while D > Dn + 0.05:
                Dn2 = D - 0.25 * D / 2.0
                if (i + j) % 2: pen.fill(v.quad([(X, 0, D), (X + 0.3, 0, D), (X + 0.3, 0, Dn2), (X, 0, Dn2)]), '#202024')
                D = Dn2; j += 1
            X += 0.3; i += 1
        pen.texture(fl, 'grunge', 0.4, 'overlay', 1.0)

    def pendant_dyn(pen, t):
        k = pendant
        sw = sway * 0.8 * noise1(t * 0.3, 21)
        D = 1.15
        ax, ay = v.p(0.0, CH, D); s = v.s(D)
        L_ = 0.75
        bx, by = ax + math.sin(math.radians(sw)) * L_ * s, ay + math.cos(math.radians(sw)) * L_ * s
        pen.seg((ax, ay), (bx, by), max(2, 0.01 * s), '#0e0e0e')
        shade = poly([(bx - 0.08 * s, by), (bx + 0.08 * s, by), (bx + 0.24 * s, by + 0.2 * s), (bx - 0.24 * s, by + 0.2 * s)])
        pen.fill(shade, '#2a3a2a'); pen.line(shade, max(2, 0.01 * s), LINE)
        if k > 0.01:
            pen.fill(oval(bx, by + 0.2 * s, 0.22 * s, 0.035 * s), '#fff8ee', 240 * k)

    def pendant_cone(pen, t):
        D = 1.15; ax, ay = v.p(0.0, CH, D); s = v.s(D)
        pen.cone(ax, ay + 0.95 * s, 0.44 * s, 2.2 * s, 1.4 * s, '#ffd9a0', 40, 0.1 * s)

    def table(pen, t):
        # table top across the bottom of the frame (very near), with mug and fruit bowl
        D0, D1, Y = 0.78, 0.4, 0.76
        top = v.quad([(-1.5, Y, D0), (1.5, Y, D0), (1.5, Y, D1), (-1.5, Y, D1)])
        pen.linear(top, 0, v.y(Y, D0), 0, min(1600, v.y(Y, D1)), ['#6a4a32', '#3a2618'])
        pen.texture(top, 'wood', 0.6, 'overlay', 2.0, 90)
        pen.radial(top, v.x(0, 0.7), v.y(Y, 0.7), 900, [(0, '#ffcf8f', 70), (1, '#ffcf8f', 0)], sy=0.35)
        edge = v.quad([(-1.5, Y, D0), (1.5, Y, D0), (1.5, Y - 0.04, D0), (-1.5, Y - 0.04, D0)])
        pen.fill(edge, '#2a1a10'); pen.line(top, 3, LINE)
        if mug:
            mx, my = v.p(0.42, Y, 0.66); s = v.s(0.66)
            pen.fill(oval(mx, my, 0.06 * s, 0.015 * s), '#000000', 90)
            m = union(rect(mx - 0.045 * s, my - 0.1 * s, 0.09 * s, 0.1 * s), oval(mx, my, 0.045 * s, 0.012 * s))
            pen.shape(m, '#c8c0b0', max(2, 0.008 * s)); pen.fill(oval(mx, my - 0.1 * s, 0.045 * s, 0.012 * s), '#3a2416')
            pen.line(oval(mx + 0.055 * s, my - 0.055 * s, 0.025 * s, 0.03 * s), max(3, 0.012 * s), '#c8c0b0')
            bx, by = v.p(-0.5, Y, 0.72); s = v.s(0.72)
            bowl = smooth([(bx - 0.15 * s, by - 0.06 * s), (bx + 0.15 * s, by - 0.06 * s), (bx + 0.08 * s, by), (bx - 0.08 * s, by)], True, 0.5)
            for k, (ox, c) in enumerate(((-0.07, '#a83a2a'), (0.0, '#c9a64a'), (0.07, '#8a2a3a'), (-0.03, '#6a8a3a'))):
                pen.shape(oval(bx + ox * s, by - 0.09 * s - (k == 3) * 0.04 * s, 0.05 * s), c, 2)
            pen.shape(bowl, '#d8d0c0', 2.5)

    L = [_cl(Db + 3, window_out, 'window_view', _key('kit', 'out'), (v.x(-1, Db) - 60, v.y(2.3, Db) - 60, v.x(1, Db) + 60, v.y(0.9, Db) + 60)),
         Layer(Db + 0.6, _police_window_glow(lf, v.x(0, Db), v.y(1.55, Db), 380, 0.75, 1.5), 'window_police', blur=0),
         _cl(Db, back, 'back_wall', _key('kit', 'back', tiles), (v.x(-HW, Db) - 30, v.y(CH, Db) - 30, v.x(HW, Db) + 30, v.gy(Db) + 30)),
         Layer(Db - 0.01, clock_dyn, 'clock', blur=0),
         _cl(1.4, sides, 'room', _key('kit', 'sides'), box),
         _cl(1.151, pendant_cone, 'pendant_light', _key('kit', 'cone'), (v.x(-1.6, 1.15), v.y(2.0, 1.15), v.x(1.6, 1.15), v.y(-0.6, 1.15)),
             alpha=pendant, blur=0),
         Layer(1.15, pendant_dyn, 'pendant'),
         Layer(1.3, _police_window_glow(lf, v.x(0, 1.6), v.y(1.4, 1.6), 620, 0.55, 0.55), 'police_spill', blur=0),
         Layer(1.39, (lambda pen, t: headlight_sweep(pen, t, sweep[0], sweep[1], (v.x(-HW, 1.5), v.y(2.4, 1.5), v.x(HW, 1.5), v.y(0.9, 1.5)), (2, 1), direction=-1))
               if sweep else (lambda pen, t: None), 'headlights', blur=0),
         _cl(0.62, table, 'table', _key('kit', 'table2', mug), (box[0], v.y(0.76, 0.8) - 120, box[2], box[3]))]
    _exposure(L, 0.4, ('back_wall', 'room', 'table'))
    a = {'counter': v.anchor(0.4, Db - 0.35, note='standing at the counter'), 'you_seated': v.anchor(0.0, 1.05, note='seated at the table'),
         'table_edge': Anchor(*v.p(0, 0.76, 0.5), 0.5, 0, note='near edge of the table: hands grip here')}
    tq = v.quad([(-HW, 0.92, Db), (HW, 0.92, Db), (HW, 1.5, Db), (-HW, 1.5, Db)]).getBounds()
    return SetPiece('kitchen', L, a, {}, lens=None, grade='interior_dim', focus=1.2, dof=3.0, cover=FRAME,
                    fx=(lambda t: {'flash': police_flash(t, 0.1)}) if police else None,
                    info={'view': v, 'tiles_rect': (tq.left(), tq.top(), tq.width(), tq.height()), 'lights': lf})


# ============================================================== living room window
def living_room_window(car=True, police=True, drive=None, car_X=1.2, figures=('driver', 'back'), curtains=1.0, lamp=1.0,
                       doors=None, head=None, wind=1.0, glass=1.0, sweep=None):
    """Inside the living room looking out through the front window at the street: curtains swaying at both sides,
    sill with a plant, floor lamp, radiator, picture frames, sofa back blurred in the foreground; outside the patrol
    car at the curb (drive=('out', t0, t1, X0, X1) to leave and 'turn the corner'), houses across, street lamps.
    Glass reflections + police light through the window onto the walls. lens None or 'lens', grade 'interior_dim'."""
    v = View(520, 470, 1.4, ground=-0.72)
    Db = 1.8
    WX0, WX1, WY0, WY1 = -1.25, 1.25, 0.8, 2.15
    lf = _lights_fn(police)
    car_d = None
    if car:
        car_d = dict(X=car_X, facing=1, figures=figures, doors=doors, D=4.85)
        if drive: car_d['drive'] = drive; car_d['head'] = head if head is not None else (lambda t: True)
    ov = View(520, 470, 1.4, ground=-0.72)
    s = v.s(Db)
    wx0, wy0 = v.p(WX0, WY1, Db); wx1, wy1 = v.p(WX1, WY0, Db)
    L = _outside_layers('lrw', ov, car_d, police, lf, wind=wind, box=(wx0 - 260, wy0 - 260, wx1 + 260, wy1 + 200))
    box = FRAME

    def wall(pen, t):
        wp = minus(rect(box[0], box[1], box[2] - box[0], v.gy(Db) - box[1]), rect(wx0, wy0, wx1 - wx0, wy1 - wy0))
        _wallpaper(pen, wp, (box[0], box[1], box[2], v.gy(Db)), s, '#3a3446', '#2c2738', 'stripe', 120)
        pen.linear(wp, 0, box[1], 0, v.gy(Db), [(0, '#000000', 120), (0.4, '#000000', 20), (1, '#000000', 80)])
        # window casing
        pen.line(rect(wx0 - 16, wy0 - 16, wx1 - wx0 + 32, wy1 - wy0 + 32), 30, '#cfc8b8'); pen.line(rect(wx0 - 31, wy0 - 31, wx1 - wx0 + 62, wy1 - wy0 + 62), 3, LINE)
        for k in (1, 2):
            xx = wx0 + (wx1 - wx0) * k / 3; pen.seg((xx, wy0), (xx, wy1), 14, '#cfc8b8')
        pen.seg((wx0, wy0 + (wy1 - wy0) * 0.32), (wx1, wy0 + (wy1 - wy0) * 0.32), 10, '#cfc8b8')
        sill = rect(wx0 - 60, wy1 + 14, wx1 - wx0 + 120, 26)
        pen.shape(sill, '#d8d0c0', 3)
        # radiator under the window
        rx0, ry0 = v.p(-0.9, 0.62, Db); rx1, ry1 = v.p(0.9, 0.12, Db)
        pen.shape(rect(rx0, ry0, rx1 - rx0, ry1 - ry0), '#8a8680', 3)
        for k in range(18): pen.seg((rx0 + 12 + k * (rx1 - rx0 - 24) / 17, ry0 + 8), (rx0 + 12 + k * (rx1 - rx0 - 24) / 17, ry1 - 8), 5, '#5a5650')
        # baseboard + floor strip
        pen.fill(rect(box[0], v.y(0.12, Db), box[2] - box[0], 0.12 * s), '#2a2622')
        fl = rect(box[0], v.gy(Db), box[2] - box[0], box[3] - v.gy(Db))
        pen.linear(fl, 0, v.gy(Db), 0, box[3], ['#2e2018', '#140c08']); pen.texture(fl, 'wood', 0.45, 'overlay', 1.4, 90)
        # pictures
        _picture(pen, v.x(-2.6, Db), v.y(2.0, Db), 0.55 * s, 0.7 * s, 'portrait', s=s)
        _picture(pen, v.x(1.75, Db), v.y(1.95, Db), 0.8 * s, 0.55 * s, 'landscape', s=s)
        # sill plant
        px, py = (wx0 + wx1) / 2 + 0.6 * s, wy1 + 14
        pen.shape(poly([(px - 0.1 * s, py - 0.18 * s), (px + 0.1 * s, py - 0.18 * s), (px + 0.07 * s, py), (px - 0.07 * s, py)]), '#8a4a32', 2.5)
        for k in range(7):
            a = -math.pi / 2 + (k - 3) * 0.4
            tip = (px + math.cos(a) * 0.3 * s, py - 0.18 * s + math.sin(a) * 0.3 * s)
            pen.fill(smooth([(px, py - 0.18 * s), ((px + tip[0]) / 2 + 8, (py - 0.18 * s + tip[1]) / 2), tip, ((px + tip[0]) / 2 - 8, (py - 0.18 * s + tip[1]) / 2)], True, 0.8), '#1d3a2a')

    def glass_fx(pen, t):
        pen.cv.save(); pen.cv.clipPath(rect(wx0, wy0, wx1 - wx0, wy1 - wy0), skia.ClipOp.kIntersect, True)
        for (x0_, w_) in ((0.1, 0.08), (0.22, 0.03), (0.6, 0.06)):
            xa = wx0 + (wx1 - wx0) * x0_
            pen.fill(poly([(xa, wy1), (xa + w_ * (wx1 - wx0), wy1), (xa + w_ * (wx1 - wx0) + 260, wy0), (xa + 260, wy0)]), '#c9d6f0', 16 * glass)
        lx_, ly_ = v.p(-1.9, 1.5, 0.9)
        pen.radial(None, wx0 + 140, wy0 + 160, 120, [(0, '#ffcf8f', 50 * glass * lamp), (1, '#ffcf8f', 0)], clip=False)       # lamp reflection
        pen.cv.restore()

    def curtains_dyn(pen, t):
        cw = 0.75 * s
        _curtain(pen, wx0 - cw * 0.75, wy0 - 70, cw, wy1 - wy0 + 260, t, -1, '#5a2630', curtains, 3)
        _curtain(pen, wx1 - cw * 0.25, wy0 - 70, cw, wy1 - wy0 + 260, t + 3.0, 1, '#5a2630', curtains, 7)
        pen.fill(rect(wx0 - cw, wy0 - 86, wx1 - wx0 + 2 * cw, 16), '#2a2016')
        for xx in (wx0 - cw - 8, wx1 + cw + 8): pen.fill(oval(xx, wy0 - 78, 14), '#c9a64a')

    def lamp_dyn(pen, t):
        x, y = v.p(-2.0, 0, 1.45); s2 = v.s(1.45)
        k = lamp
        if k > 0.01:
            pen.radial(None, x, y - 1.55 * s2, 1.6 * s2, [(0, '#ffcf8f', 70 * k), (0.5, '#ffcf8f', 24 * k), (1, '#ffcf8f', 0)], clip=False)
        pen.seg((x, y), (x, y - 1.45 * s2), max(3, 0.02 * s2), '#1a1612')
        pen.fill(oval(x, y, 0.16 * s2, 0.035 * s2), '#1a1612')
        shade = poly([(x - 0.13 * s2, y - 1.75 * s2), (x + 0.13 * s2, y - 1.75 * s2), (x + 0.22 * s2, y - 1.42 * s2), (x - 0.22 * s2, y - 1.42 * s2)])
        pen.fill(shade, mix('#5a4a30', '#f4e2b8', k)); pen.line(shade, 3, LINE)
        if k > 0.01: pen.fill(oval(x, y - 1.425 * s2, 0.2 * s2, 0.02 * s2), '#fff8ee', 220 * k)

    def sofa(pen, t):
        D = 0.75; s2 = v.s(D)
        x0, y0 = v.p(-1.6, 0.85, D); x1, _ = v.p(1.6, 0.85, D)
        back_ = smooth([(x0, 1180), (x0, y0 + 40), (x0 + 60, y0), (x1 - 60, y0), (x1, y0 + 40), (x1, 1180)], True, 0.3)
        pen.fill(back_, '#5a4048'); pen.texture(back_, 'fabric', 0.5, 'overlay', 1.4)
        pen.linear(back_, 0, y0, 0, y0 + 200, [(0, '#e0a888', 150), (1, '#e0a888', 0)])
        pen.line(back_, 5, LINE)
        for k in (1, 2): pen.seg((x0 + (x1 - x0) * k / 3, y0 + 30), (x0 + (x1 - x0) * k / 3, 1180), 4, '#1e1418', 200)
        cush = rrect(x0 + 120, y0 - 120, 260, 200, 60)
        pen.shape(cush, '#6a4a3a', 4); pen.texture(cush, 'fabric', 0.5, 'overlay', 1.0)

    def spill(pen, t):
        r_, b_ = lf(t)
        cx = (wx0 + wx1) / 2
        r_, b_ = _lv(r_), _lv(b_)
        if r_ > 0.05: pen.radial(None, cx - 420, v.y(1.2, Db), 640, [(0, '#ff2a2a', 52 * r_), (1, '#ff2a2a', 0)], sy=0.7, clip=False)
        if b_ > 0.05: pen.radial(None, cx + 420, v.y(1.2, Db), 640, [(0, '#3a5cff', 52 * b_), (1, '#3a5cff', 0)], sy=0.7, clip=False)

    L += [_cl(Db, wall, 'wall', _key('lrw', 'wall'), box),
          _cl(Db - 0.02, glass_fx, 'glass', _key('lrw', 'glass', glass, lamp), (wx0, wy0, wx1, wy1), blur=0),
          Layer(Db - 0.05, curtains_dyn, 'curtains'),
          Layer(Db - 0.06, spill, 'police_spill', blur=0),
          Layer(Db - 0.07, (lambda pen, t: headlight_sweep(pen, t, sweep[0], sweep[1], (box[0] + 300, v.y(2.5, Db), box[2] - 300, v.y(0.3, Db)), (3, 2)))
                if sweep else (lambda pen, t: None), 'headlights', blur=0),
          Layer(1.45, lamp_dyn, 'floor_lamp'),
          _cl(0.75, sofa, 'sofa', _key('lrw', 'sofa2'), (box[0], v.y(1.0, 0.75), box[2], 1190), blur=0)]
    _exposure(L, 0.45, ('wall', 'sofa'))
    a = {'you_window': v.anchor(-0.4, 1.25, note='standing at the window, back to camera'),
         'car': Anchor(ov.x(car_X, 4.85), ov.gy(4.85), 4.85, 1.85 * ov.s(4.85), note='patrol car at the curb (outside)'),
         'car_back_seat': Anchor(ov.x(car_X + 0.62, 4.85), ov.y(ov.ground + 1.1, 4.85), 4.85, 1.85 * ov.s(4.85), note='head of the man in the back seat')}
    return SetPiece('living_room_window', L, a, {}, lens=None, grade='interior_dim', focus=Db, dof=2.0, cover=FRAME,
                    fx=(lambda t: {'flash': police_flash(t, 0.15)}) if police else None,
                    info={'view': v, 'outside_view': ov, 'window': (wx0, wy0, wx1, wy1), 'lights': lf})


# ============================================================== mother's room
def mother_room(police=False, lamp=1.0, phone_ring=None, door_glow=1.0, curtains=1.0, knock=None):
    """Mother's sitting room: floral wallpaper, armchair with a crocheted throw, side table with lamp and a corded phone
    (phone_ring = f(t) -> 0..1 rattles the handset), family photos, wall clock, sideboard with dried flowers, window with
    lace + drapes (police red/blue outside when police=True), an open doorway (back wall, left) onto her hall with the
    front door at the end (warm glass; red/blue when police), rug on floorboards, a table lamp.
    lens None, grade 'interior_dim'. Anchors: 'mum_chair' (seated), 'mum_standing', 'mum_door' (at her front door, far),
    'phone'."""
    v = View(600, 450, 1.5)
    Db, Dn, HW, CH = 2.2, 0.55, 2.4, 2.45
    HX0, HX1, Dh = -0.6, 0.4, 3.6                    # doorway on the back wall and the hall's end (front door)
    lf = _lights_fn(police)
    box = FRAME
    s = v.s(Db)

    def hall_far(pen, t):
        # hall beyond the doorway: side walls, floor, ceiling, the front door at the end
        for X, c in ((HX0, '#3a302c'), (HX1, '#2e2624')):
            p = v.quad([(X, 0, Dh), (X, 2.3, Dh), (X, 2.3, Db - 0.05), (X, 0, Db - 0.05)])
            pen.linear(p, v.x(X, Dh), 0, v.x(X, Db), 0, [c, _darken(c, 0.4)])
        _floorboards(pen, v, HX0, HX1, Dh, Db - 0.05, '#3a2a1e', '#22180f', 0.12)
        pen.fill(v.quad([(HX0, 2.3, Dh), (HX1, 2.3, Dh), (HX1, 2.3, Db), (HX0, 2.3, Db)]), '#0c0a0a')
        ew = v.quad([(HX0, 0, Dh), (HX1, 0, Dh), (HX1, 2.3, Dh), (HX0, 2.3, Dh)])
        pen.fill(ew, '#4a3c34')
        _rug(pen, v, HX0 + 0.25, HX1 - 0.25, Dh - 0.05, Db, '#5a2a2a', '#2a1212', '#a88a5a')
        sx_, sy_ = v.p(HX0 + 0.01, 1.7, 2.9)
        pen.radial(None, sx_ + 20, sy_, 0.9 * v.s(2.9), [(0, '#ffcf8f', 120), (1, '#ffcf8f', 0)], clip=False)
        pen.fill(rrect(sx_ - 6, sy_ - 20, 16, 34, 6), '#fff4dc')
        s3 = v.s(Dh)
        x0, y0 = v.p(-0.45, 2.05, Dh); x1, y1 = v.p(0.35, 0, Dh)
        _door_front(pen, x0, y0, x1 - x0, y1 - y0, s3, '#2a3a4a', panels=4, chain=None, slot=False, peep=False)
        gx, gy = x0 + (x1 - x0) * 0.2, y0 + (y1 - y0) * 0.08
        pen.fill(rrect(gx, gy, (x1 - x0) * 0.6, (y1 - y0) * 0.24, 6), mix('#3a2a20', '#e8c890', door_glow))
        pen.radial(None, (x0 + x1) / 2, y1, (x1 - x0) * 1.4, [(0, '#e8c890', 60 * door_glow), (1, '#e8c890', 0)], sy=0.25, clip=False)
        # coat stand silhouette in the hall
        cx, cy = v.p(-0.48, 0, 2.7); s4 = v.s(2.7)
        pen.seg((cx, cy), (cx, cy - 1.75 * s4), max(2, 0.03 * s4), '#140e0a')
        pen.fill(smooth([(cx - 0.05 * s4, cy - 1.7 * s4), (cx + 0.2 * s4, cy - 1.6 * s4), (cx + 0.22 * s4, cy - 0.9 * s4), (cx - 0.02 * s4, cy - 0.95 * s4)], True, 0.5), '#2a2420')

    def hall_dyn(pen, t):
        r_, b_ = lf(t)
        x0, y0 = v.p(-0.45, 2.05, Dh); x1, y1 = v.p(0.35, 0, Dh)
        gx, gy, gw, gh = x0 + (x1 - x0) * 0.2, y0 + (y1 - y0) * 0.08, (x1 - x0) * 0.6, (y1 - y0) * 0.24
        if r_ > 0.02: pen.fill(rrect(gx, gy, gw / 2, gh, 6), '#ff3a3a', 200 * r_)
        if b_ > 0.02: pen.fill(rrect(gx + gw / 2, gy, gw / 2, gh, 6), '#4a6cff', 200 * b_)
        if knock:
            k = knock(t)
            if k > 0.01: pen.radial(None, (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0), [(0, '#ffffff', 40 * k), (1, '#ffffff', 0)], clip=False)

    def back(pen, t):
        hole = v.quad([(HX0, 0, Db), (HX1, 0, Db), (HX1, 2.1, Db), (HX0, 2.1, Db)])
        win = rect(*v.p(0.95, 2.1, Db), 1.2 * s, 1.25 * s)
        wall_p = minus(minus(v.quad([(-HW, 0, Db), (HW, 0, Db), (HW, CH, Db), (-HW, CH, Db)]), win), hole)
        x0, y0 = v.p(-HW, CH, Db); x1, y1 = v.p(HW, 0, Db)
        _wallpaper(pen, wall_p, (x0, y0, x1, y1), s, '#4a3e3a', '#8a5a5a', 'floral', 170, '#d9b67a', seed=3)
        pen.linear(wall_p, 0, y0, 0, y1, [(0, '#000000', 100), (0.5, '#000000', 10), (1, '#000000', 70)])
        dado = minus(v.quad([(-HW, 0.85, Db), (HW, 0.85, Db), (HW, 0.92, Db), (-HW, 0.92, Db)]), hole)
        pen.fill(dado, '#5a4436')
        pen.fill(minus(v.quad([(-HW, 0, Db), (HW, 0, Db), (HW, 0.12, Db), (-HW, 0.12, Db)]), hole), '#2e241e')
        pen.line(hole, 16, '#7a6a5a'); pen.line(hole, 3, LINE)
        wx, wy = v.p(0.95, 2.1, Db); ww, wh = 1.2 * s, 1.25 * s
        pen.line(rect(wx - 12, wy - 12, ww + 24, wh + 24), 24, '#d8d0c0')
        pen.seg((wx + ww / 2, wy), (wx + ww / 2, wy + wh), 10, '#d8d0c0'); pen.seg((wx, wy + wh / 2), (wx + ww, wy + wh / 2), 10, '#d8d0c0')
        pen.fill(rect(wx - 40, wy + wh + 10, ww + 80, 20), '#d8d0c0')
        for i, (X, Y, w, h, kind) in enumerate(((-2.15, 1.98, 0.4, 0.5, 'photo'), (-1.62, 2.02, 0.28, 0.36, 'portrait'),
                                                (-1.64, 1.58, 0.3, 0.24, 'landscape'), (-1.22, 1.9, 0.42, 0.32, 'photo'))):
            px, py = v.p(X, Y, Db)
            _picture(pen, px, py, w * s, h * s, kind, '#5a3e22' if i % 2 else '#c9a64a', s=s, seed=i)
        sx0, sy0 = v.p(-2.25, 0.85, Db); sx1, sy1 = v.p(-0.85, 0.0, Db)
        sb = rect(sx0, sy0, sx1 - sx0, sy1 - sy0)
        pen.fill(sb, '#4a3020'); pen.texture(sb, 'wood', 0.5, 'overlay', 1.3); pen.line(sb, 3, LINE)
        for k in range(3):
            pen.line(rect(sx0 + 12 + k * (sx1 - sx0 - 24) / 3, sy0 + 14, (sx1 - sx0 - 24) / 3 - 10, sy1 - sy0 - 40), 2.5, '#24160c')
            pen.fill(oval(sx0 + 12 + (k + 0.5) * (sx1 - sx0 - 24) / 3, sy0 + 50, 6), '#c9a64a')
        vx, vy = v.p(-2.0, 0.85, Db)
        pen.fill(oval(vx, vy, 0.18 * s, 0.025 * s), '#e8e0d0', 220)
        pen.shape(smooth([(vx - 0.06 * s, vy), (vx - 0.08 * s, vy - 0.15 * s), (vx - 0.03 * s, vy - 0.25 * s), (vx + 0.03 * s, vy - 0.25 * s),
                          (vx + 0.08 * s, vy - 0.15 * s), (vx + 0.06 * s, vy)], True, 0.6), '#3a5a7a', 2.5)
        for k in range(6):
            a = -math.pi / 2 + (k - 2.5) * 0.25
            tip = (vx + math.cos(a) * 0.32 * s, vy - 0.25 * s + math.sin(a) * 0.32 * s)
            pen.seg((vx, vy - 0.24 * s), tip, 2, '#5a4a2a'); pen.fill(oval(*tip, 0.025 * s), ['#a86a5a', '#c9a64a', '#8a5a7a'][k % 3])

    def window_out(pen, t):
        wx, wy = v.p(0.95, 2.1, Db); ww, wh = 1.2 * s, 1.25 * s
        pen.linear(rect(wx - 60, wy - 60, ww + 120, wh + 120), 0, wy, 0, wy + wh, ['#0a1430', '#1c2448'])
        pen.fill(rect(wx - 60, wy + wh * 0.62, ww + 120, wh), '#0a0d14')
        draw_tree(pen, wx + ww * 0.75, wy + wh * 0.75, wh * 0.9, t, 51, 0.5, '#05070c', None, 4)
        pen.fill(rect(wx + 30, wy + wh * 0.45, 80, 60), '#d9b47c', 220)

    def lace(pen, t):
        wx, wy = v.p(0.95, 2.1, Db); ww, wh = 1.2 * s, 1.25 * s
        pen.cv.save(); pen.cv.clipPath(rect(wx, wy, ww, wh), skia.ClipOp.kIntersect, True)
        pen.fill(rect(wx, wy, ww, wh), '#d8d0c0', 40)
        for i in range(int(ww / 18) + 1):
            for j in range(int(wh / 18) + 1):
                pen.line(oval(wx + i * 18 + (j % 2) * 9, wy + j * 18, 6), 1.5, '#ffffff', 40)
        pen.cv.restore()

    def drapes(pen, t):
        wx, wy = v.p(0.95, 2.1, Db); ww, wh = 1.2 * s, 1.25 * s
        cw = 0.5 * s
        _curtain(pen, wx - cw * 0.7, wy - 60, cw, wh + 200, t, -1, '#5a3a4a', 0.4 * curtains, 11, folds=5)
        _curtain(pen, wx + ww - cw * 0.3, wy - 60, cw, wh + 200, t + 2, 1, '#5a3a4a', 0.4 * curtains, 13, folds=5)
        pen.fill(rect(wx - cw, wy - 76, ww + 2 * cw, 18), '#3a2a1e')

    def room(pen, t):
        for X in (-HW, HW): _side_wall(pen, v, X, Db, Dn, 0, CH, '#4a3e3a', '#5a4444', 'dots', 120, wains=0.0, shade=0.55)
        ceil = v.quad([(-HW, CH, Db), (HW, CH, Db), (HW, CH, Dn), (-HW, CH, Dn)])
        pen.linear(ceil, 0, v.y(CH, Dn), 0, v.y(CH, Db), ['#070607', '#1e1a18'])
        _floorboards(pen, v, -HW, HW, Db, Dn, '#3a2a1e', '#1a120c', 0.11)
        _rug(pen, v, -1.4, 1.2, 1.95, 0.95, '#3a4a5a', '#1a222c', '#a88a5a')
        # standing lamp (left, near)
        x, y = v.p(2.05, 0, 1.4); s2 = v.s(1.4)
        pen.seg((x, y), (x, y - 1.5 * s2), max(3, 0.02 * s2), '#1a1612'); pen.fill(oval(x, y, 0.16 * s2, 0.03 * s2), '#1a1612')
        sh = poly([(x - 0.14 * s2, y - 1.8 * s2), (x + 0.14 * s2, y - 1.8 * s2), (x + 0.24 * s2, y - 1.48 * s2), (x - 0.24 * s2, y - 1.48 * s2)])
        pen.fill(sh, '#6a5a40'); pen.line(sh, 3, LINE)

    def chair(pen, t):
        D = 1.6; s2 = v.s(D)
        x, y = v.p(-1.45, 0, D)
        c = '#6a3a3a'
        back_ = smooth([(x - 0.42 * s2, y - 0.45 * s2), (x - 0.44 * s2, y - 1.05 * s2), (x - 0.3 * s2, y - 1.2 * s2), (x + 0.3 * s2, y - 1.2 * s2),
                        (x + 0.44 * s2, y - 1.05 * s2), (x + 0.42 * s2, y - 0.45 * s2)], True, 0.5)
        pen.shape(back_, c, 4); pen.texture(back_, 'fabric', 0.5, 'overlay', 1.0)
        for k in range(4): pen.seg((x - 0.3 * s2 + k * 0.2 * s2, y - 1.12 * s2), (x - 0.3 * s2 + k * 0.2 * s2, y - 0.5 * s2), 3, _darken(c, 0.35), 200)
        throw = poly([(x - 0.38 * s2, y - 1.15 * s2), (x + 0.1 * s2, y - 1.18 * s2), (x + 0.05 * s2, y - 0.75 * s2), (x - 0.4 * s2, y - 0.7 * s2)])
        pen.fill(throw, '#c9a66a', 220)
        for i in range(5):
            for j in range(4):
                pen.line(oval(x - 0.33 * s2 + i * 0.08 * s2, y - 1.1 * s2 + j * 0.1 * s2, 0.025 * s2), 2, '#8a6a3a', 200)
        seat = rrect(x - 0.45 * s2, y - 0.55 * s2, 0.9 * s2, 0.2 * s2, 0.06 * s2)
        pen.shape(seat, _lighten(c, 0.08), 4)
        for sd in (-1, 1):
            arm = rrect(x + sd * 0.42 * s2 - 0.1 * s2, y - 0.78 * s2, 0.2 * s2, 0.6 * s2, 0.08 * s2)
            pen.shape(arm, _darken(c, 0.1), 4); pen.texture(arm, 'fabric', 0.4, 'overlay', 1.0)
        pen.fill(rect(x - 0.45 * s2, y - 0.2 * s2, 0.9 * s2, 0.2 * s2), _darken(c, 0.3)); pen.line(rect(x - 0.45 * s2, y - 0.2 * s2, 0.9 * s2, 0.2 * s2), 3, LINE)
        tx, ty = v.p(-0.5, 0, 1.65); s2 = v.s(1.65)
        top = rect(tx - 0.28 * s2, ty - 0.62 * s2, 0.56 * s2, 0.05 * s2)
        pen.fill(oval(tx, ty - 0.6 * s2, 0.32 * s2, 0.05 * s2), '#e8e0d0', 200)
        pen.shape(top, '#5a3a22', 3)
        for lx_ in (-0.22, 0.22): pen.seg((tx + lx_ * s2, ty - 0.58 * s2), (tx + lx_ * s2 * 1.1, ty), 5, '#3a2414')
        pen.shape(rect(tx - 0.2 * s2, ty - 0.25 * s2, 0.4 * s2, 0.03 * s2), '#5a3a22', 2)

    def table_dyn(pen, t):
        D = 1.65; s2 = v.s(D)
        tx, ty = v.p(-0.5, 0, D)
        _table_lamp(pen, tx + 0.12 * s2, ty - 0.62 * s2, s2 * 0.9, lamp, '#e8d8b0', '#7a6a4a', glow=False)
        rk = phone_ring(t) if phone_ring else 0.0
        jit = rk * 0.012 * s2 * math.sin(t * 2 * math.pi * 18)
        px, py = tx - 0.1 * s2, ty - 0.62 * s2
        body = smooth([(px - 0.1 * s2, py), (px - 0.09 * s2, py - 0.07 * s2), (px + 0.09 * s2, py - 0.07 * s2), (px + 0.1 * s2, py)], True, 0.4)
        pen.shape(body, '#e8e0d0', 2.5)
        pen.fill(oval(px, py - 0.04 * s2, 0.035 * s2, 0.02 * s2), '#9a9488')
        lift = abs(jit) * 1.5
        hs = smooth([(px - 0.12 * s2 + jit, py - 0.09 * s2 - lift), (px - 0.08 * s2 + jit, py - 0.12 * s2 - lift), (px + 0.08 * s2 + jit, py - 0.12 * s2 - lift),
                     (px + 0.12 * s2 + jit, py - 0.09 * s2 - lift), (px + 0.08 * s2 + jit, py - 0.08 * s2), (px - 0.08 * s2 + jit, py - 0.08 * s2)], True, 0.5)
        pen.shape(hs, '#f0e8d8', 2.5)
        pen.line(smooth([(px + 0.1 * s2, py - 0.02 * s2), (px + 0.2 * s2, py + 0.05 * s2), (px + 0.15 * s2, py + 0.25 * s2), (px + 0.22 * s2, py + 0.6 * s2)], False), 2, '#c8c0b0')
        cx, cy = v.p(-0.1, 2.3, Db); r = 0.1 * s
        pen.shape(oval(cx, cy, r), '#e8e0d0', 3)
        for k in range(12):
            a = k * math.pi / 6
            pen.seg((cx + math.cos(a) * r * 0.75, cy + math.sin(a) * r * 0.75), (cx + math.cos(a) * r * 0.86, cy + math.sin(a) * r * 0.86), 1.5, '#3a3a3a')
        sec = 3600 * 12 + 50 * 60 + t
        for (val, per, ln, w) in ((sec / 3600.0, 12, 0.5, 4), (sec / 60.0, 60, 0.75, 3)):
            a = 2 * math.pi * (val % per) / per - math.pi / 2
            pen.seg((cx, cy), (cx + math.cos(a) * r * ln, cy + math.sin(a) * r * ln), w, '#1a1a1a')
        x, y = v.p(2.05, 0, 1.4); s3 = v.s(1.4)
        if lamp > 0.01: pen.fill(oval(x, y - 1.485 * s3, 0.22 * s3, 0.02 * s3), '#fff8ee', 220 * lamp)

    def glows(pen, t):
        D = 1.65; s2 = v.s(D); tx, ty = v.p(-0.5, 0, D)
        x0, y0 = tx + 0.12 * s2, ty - 0.62 * s2; s9 = s2 * 0.9
        pen.radial(None, x0, y0 - 0.42 * s9, 1.7 * s9, [(0, '#ffcf8f', 70), (0.5, '#ffcf8f', 26), (1, '#ffcf8f', 0)], clip=False)
        pen.cone(x0, y0 - 0.33 * s9, 0.32 * s9, 0.9 * s9, 0.4 * s9, '#ffd9a0', 60, 0.05 * s9)
        x, y = v.p(2.05, 0, 1.4); s3 = v.s(1.4)
        pen.radial(None, x, y - 1.6 * s3, 1.4 * s3, [(0, '#ffcf8f', 60), (1, '#ffcf8f', 0)], clip=False)

    def spill(pen, t):
        r_, b_ = (_lv(c) for c in lf(t))
        wx, wy = v.p(0.95, 2.1, Db); ww, wh = 1.2 * s, 1.25 * s
        if r_ > 0.02: pen.radial(None, wx + ww * 0.3, wy + wh, 600, [(0, '#ff2a2a', 60 * r_), (1, '#ff2a2a', 0)], sy=0.5, clip=False)
        if b_ > 0.02: pen.radial(None, wx + ww * 0.7, wy + wh, 600, [(0, '#3a5cff', 60 * b_), (1, '#3a5cff', 0)], sy=0.5, clip=False)

    L = [_cl(Db + 2, window_out, 'window_view', _key('mrm', 'out'), (v.x(0.8, Db) - 80, v.y(2.3, Db) - 80, v.x(2.3, Db) + 80, v.y(0.7, Db) + 80)),
         Layer(Db + 1, _police_window_glow(lf, v.x(1.55, Db), v.y(1.5, Db), 420, 0.8, 1.5), 'window_police', blur=0),
         _cl(2.9, hall_far, 'hall', _key('mrm', 'hall3', door_glow), (v.x(-0.8, 2.2), v.y(2.4, 2.2), v.x(0.6, 2.2), v.y(-0.1, 2.2))),
         Layer(2.85, hall_dyn, 'hall_door', blur=0),
         _cl(Db, back, 'back_wall', _key('mrm', 'back3'), (v.x(-HW, Db) - 30, v.y(CH, Db) - 30, v.x(HW, Db) + 30, v.gy(Db) + 30)),
         _cl(Db - 0.01, lace, 'lace', _key('mrm', 'lace3'), (v.x(0.8, Db), v.y(2.2, Db), v.x(2.3, Db), v.y(0.7, Db)), blur=0),
         Layer(Db - 0.03, drapes, 'drapes'),
         _cl(2.25, room, 'room', _key('mrm', 'room3'), box),
         _cl(1.6, chair, 'armchair', _key('mrm', 'chair3'), (v.x(-2.2, 1.6), v.y(1.4, 1.6), v.x(-0.1, 1.65), v.gy(1.6) + 20)),
         _cl(1.645, glows, 'lamp_glow', _key('mrm', 'glow3'), (v.x(-1.6, 1.65), v.y(2.6, 1.4), v.x(3.2, 1.4), v.y(0.2, 1.65)),
             alpha=lamp, blur=0),
         Layer(1.64, table_dyn, 'side_table'),
         Layer(1.5, spill, 'police_spill', blur=0)]
    _exposure(L, 0.3, ('back_wall', 'room', 'armchair', 'hall'))
    a = {'mum_chair': Anchor(*v.p(-1.45, 0.0, 1.57), 1.57, 1.6 * v.s(1.62), note='seated in the armchair: hips at y - 0.5 m'),
         'mum_standing': v.anchor(0.6, 1.45), 'mum_door': v.anchor(-0.05, Dh - 0.15, note='at her front door down the hall'),
         'phone': Anchor(*v.p(-0.6, 0.62, 1.65), 1.65, 0, note='the corded phone on the side table')}
    return SetPiece('mother_room', L, a, {}, lens=None, grade='interior_dim', focus=1.65, dof=2.5, cover=FRAME,
                    fx=(lambda t: {'flash': police_flash(t, 0.12)}) if police else None, info={'view': v, 'lights': lf})


# ============================================================== props (vector, any scale)
_TF = {}


def _typeface_file(name, fallback=700):
    if name not in _TF:
        path = {'mono': '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf',
                'mono_b': '/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf',
                'serif': '/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf'}.get(name)
        tf = skia.Typeface.MakeFromFile(path) if path and os.path.exists(path) else None
        _TF[name] = tf or typeface(fallback)
    return _TF[name]


def _type(cv, s, x, y, size, c='#1a1a1a', a=255, face='mono', align='left'):
    """Typed (monospace) text, baseline at y."""
    f = skia.Font(_typeface_file(face), size)
    w = f.measureText(s)
    x0 = x - w / 2 if align == 'center' else (x - w if align == 'right' else x)
    cv.drawString(s, x0, y, f, skia.Paint(Color=col(c, a), AntiAlias=True))
    return w


def _hand_text(cv, s, x, y, size, c='#1d3a8a', a=235, seed=0, slant=-0.25, weight=600, wobble=1.0):
    """Handwriting look: slanted, per-letter jitter in baseline, size and angle. Baseline at y."""
    f = skia.Font(typeface(weight), size)
    cx = x
    p = skia.Paint(Color=col(c, a), AntiAlias=True)
    for i, ch in enumerate(s):
        w = f.measureText(ch)
        if ch != ' ':
            cv.save()
            cv.translate(cx, y + size * 0.05 * wobble * math.sin(i * 1.7 + seed) + size * 0.03 * (_h(i, seed) - 0.5))
            cv.skew(slant, 0); cv.rotate((_h(i, seed + 1) - 0.5) * 6 * wobble)
            sc = 1.0 + 0.06 * wobble * (_h(i, seed + 2) - 0.5)
            cv.scale(sc, sc)
            cv.drawString(ch, 0, 0, f, p)
            cv.restore()
        cx += w * (0.92 + 0.08 * _h(i, seed + 3))
    return cx - x


def _signature(pen, x, y, w, h, seed=7, c='#1d2a6a', lw=None, mistake=True, a=240):
    """Cursive signature scribble from (x, y) (baseline), w wide. Same seed = same signature. mistake=True adds the
    little slip in the last letter (a doubled-back hook)."""
    rng = np.random.default_rng(seed)
    pts = [(x, y - h * 0.2)]
    n = 9
    for i in range(n):
        u = (i + 1) / (n + 1)
        amp = h * (0.9 if i in (0, 4) else 0.45) * rng.uniform(0.7, 1.1)
        pts.append((x + w * (u - 0.03), y - amp))
        pts.append((x + w * (u + 0.02), y + h * 0.08 * rng.uniform(-1, 1)))
    if mistake:
        ex, ey = pts[-1]
        pts += [(ex + w * 0.05, ey - h * 0.5), (ex + w * 0.02, ey - h * 0.2), (ex + w * 0.07, ey - h * 0.35), (ex + w * 0.12, ey + h * 0.05)]
    pen.line(smooth(pts, False, 0.75), lw or max(1.2, h * 0.07), c, a)
    pen.line(smooth([(x + w * 0.05, y + h * 0.25), (x + w * 0.5, y + h * 0.1), (x + w * 0.95, y + h * 0.2)], False, 0.8), (lw or max(1.2, h * 0.07)) * 0.8, c, a * 0.9)


def _paper(pen, w, h, c='#ece6d8', fold=True, shadow=True, curl=0.0):
    p = rect(-w / 2, -h / 2, w, h)
    if shadow: pen.shadow(p, w * 0.015, w * 0.025, w * 0.03, '#000000', 130)
    pen.fill(p, c); pen.texture(p, 'paper', 0.5, 'overlay', 1.0)
    if fold:
        pen.linear(rect(-w / 2, -h / 2 + h / 3 - 6, w, 12), 0, -h / 2 + h / 3 - 6, 0, -h / 2 + h / 3 + 6, [(0, '#000000', 0), (0.5, '#000000', 40), (1, '#ffffff', 30)])
        pen.linear(rect(-w / 2, -h / 2 + 2 * h / 3 - 6, w, 12), 0, -h / 2 + 2 * h / 3 - 6, 0, -h / 2 + 2 * h / 3 + 6, [(0, '#000000', 0), (0.5, '#000000', 40), (1, '#ffffff', 30)])
    pen.line(p, max(1.0, w * 0.003), '#8a8478', 200)
    return p


def _prop_complaint(pen, t, name='DANIEL J. REED', address='144 ELM STREET', highlight=None, hk=1.0, sign_seed=7, verified=False,
                    **kw):
    W, H = 700, 960
    _paper(pen, W, H)
    cv = pen.cv
    L = -W / 2 + 48; R = W / 2 - 48; y = -H / 2 + 70
    pen.fill(rect(L, y - 38, R - L, 6), '#1a1a1a')
    text(cv, 'MAPLE GROVE POLICE DEPARTMENT', 0, y - 6, 800, 22, '#1a1a1a', 255, 0.06)
    text(cv, 'COMPLAINT / INCIDENT REPORT', 0, y + 30, 900, 30, '#1a1a1a', 255, 0.04)
    _type(cv, 'REPORT NO. 24-1187        DATE: 10/31        TIME: 00:36', 0, y + 62, 15, '#333333', 255, 'mono', 'center')
    y += 92
    pen.fill(rect(L, y, R - L, 2.5), '#1a1a1a')
    rows = [('INCIDENT LOCATION', address), ('NATURE OF COMPLAINT', 'UNKNOWN PERSON REFUSING TO'), ('', 'LEAVE THE PROPERTY.')]
    hl = {}
    for (lab, val) in rows:
        y += 46
        if lab: _type(cv, lab + ':', L, y, 15, '#555555', 255, 'mono_b')
        yv = y + (20 if lab else 0)
        if lab == '': y -= 22; yv = y + 20
        _type(cv, val, L + 12, yv + 4, 21, '#111111', 255, 'mono')
        if lab == 'INCIDENT LOCATION': hl['address'] = (L, y - 18, R - L, 50)
        y += 20
    y += 40
    _type(cv, 'DESCRIPTION OF PERSON:', L, y, 15, '#555555', 255, 'mono_b')
    desc = ['MALE, APPROX. 5\'11", SLIM BUILD.', 'SHORT BROWN HAIR.', 'GREY HOODED SWEATSHIRT, DARK JEANS,', 'BARE FEET. SMALL SCAR LEFT OF MOUTH.']
    y0d = y
    for d in desc:
        y += 30; _type(cv, d, L + 12, y, 19, '#111111', 255, 'mono')
    hl['description'] = (L, y0d + 6, R - L, y - y0d + 12)
    y += 54
    pen.fill(rect(L, y - 28, R - L, 1.5), '#8a8478')
    _type(cv, 'COMPLAINANT:', L, y, 15, '#555555', 255, 'mono_b')
    _hand_text(cv, name.title(), L + 160, y + 4, 30, '#1d2a6a', 240, seed=3)
    hl['name'] = (L, y - 30, R - L, 46)
    y += 40
    _type(cv, 'RELATION TO PROPERTY:  HOMEOWNER', L, y, 15, '#555555', 255, 'mono_b')
    y += 58
    _type(cv, 'IDENTITY VERIFIED', L, y, 17, '#111111', 255, 'mono_b')
    bx = L + 230
    pen.line(rect(bx, y - 22, 28, 28), 2.5, '#111111')
    hl['verified'] = (L - 6, y - 32, 280, 46)
    if verified:
        pen.line(poly([(bx + 4, y - 8), (bx + 12, y + 2), (bx + 30, y - 30)], False), 4, '#1d2a6a')
    _type(cv, 'OFFICER:  _____________', L + 300, y, 15, '#555555', 255, 'mono_b')
    y += 80
    pen.seg((L, y), (L + 330, y), 1.5, '#333333')
    _signature(pen, L + 20, y - 8, 280, 46, sign_seed)
    _type(cv, 'SIGNATURE OF COMPLAINANT', L, y + 22, 13, '#555555', 255, 'mono_b')
    hl['signature'] = (L, y - 64, 350, 90)
    pen.seg((L + 380, y), (R, y), 1.5, '#333333')
    _type(cv, 'DATE', L + 380, y + 22, 13, '#555555', 255, 'mono_b')
    _hand_text(cv, '10/31', L + 400, y - 8, 26, '#1d2a6a', 230, seed=5)
    # stamp
    cv.save(); cv.translate(R - 90, -H / 2 + 150); cv.rotate(-12)
    pen.line(rrect(-80, -26, 160, 52, 8), 3, '#a32a2a', 150)
    text(cv, 'RECEIVED', 0, 9, 900, 24, '#a32a2a', 150, 0.08)
    cv.restore()
    if highlight and highlight in hl:
        x_, y_, w_, h_ = hl[highlight]
        pen.fill(rrect(x_ - 8, y_ - 4, w_ + 16, h_ + 8, 6), '#ffe060', 70 * hk)
        pen.line(rrect(x_ - 8, y_ - 4, w_ + 16, h_ + 8, 6), 3, '#c83a2a', 200 * hk)


def _prop_licence(pen, t, name='REED, DANIEL J', broken=True, glare=0.0, photo=True, sign_seed=7, address='144 ELM STREET',
                  wear=0.3, **kw):
    W, H = 856, 540
    r = 34
    card = rrect(-W / 2, -H / 2, W, H, r)
    if broken:
        bite = poly([(W / 2 - 120, -H / 2 - 5), (W / 2 + 5, -H / 2 - 5), (W / 2 + 5, -H / 2 + 95), (W / 2 - 22, -H / 2 + 62), (W / 2 - 40, -H / 2 + 70),
                     (W / 2 - 58, -H / 2 + 34), (W / 2 - 86, -H / 2 + 30)])
        card = minus(card, bite)
    pen.shadow(card, 8, 14, 18, '#000000', 140)
    pen.linear(card, -W / 2, 0, W / 2, 0, ['#d9e3ea', '#c8d6e0', '#e0e6dc'])
    cv = pen.cv
    cv.save(); cv.clipPath(card, skia.ClipOp.kIntersect, True)
    pen.linear(rect(-W / 2, -H / 2, W, 112), 0, -H / 2, 0, -H / 2 + 112, ['#2a4a7a', '#3a5a8a'])
    for k in range(9):                                                       # guilloche waves
        pts = [(-W / 2 + i * 20, -40 + k * 34 + 10 * math.sin(i * 0.4 + k)) for i in range(45)]
        pen.line(poly(pts, False), 1.2, '#8aa6c0', 110)
    pen.radial(None, 220, 60, 220, [(0, '#c9a64a', 60), (1, '#c9a64a', 0)], clip=False)
    cv.restore()
    text(cv, 'DRIVER LICENSE', -W / 2 + 36, -H / 2 + 52, 900, 40, '#ffffff', 255, 0.06, 'left')
    _type(cv, 'STATE OF COLUMBIA      CLASS C', -W / 2 + 38, -H / 2 + 92, 20, '#d8e2f0', 255, 'mono_b')
    # photo
    px, py, pw, ph = -W / 2 + 40, -H / 2 + 140, 230, 290
    pen.fill(rect(px, py, pw, ph), '#9aa8b4')
    if photo:
        cv.save(); cv.clipPath(rect(px, py, pw, ph), skia.ClipOp.kIntersect, True)
        pen.linear(rect(px, py, pw, ph), 0, py, 0, py + ph, ['#b4c0cc', '#8a98a6'])
        pen.fill(rrect(px + 30, py + 190, pw - 60, 160, 60), '#4a5058')                        # hoodie shoulders
        pen.fill(oval(px + pw / 2, py + 125, 62, 78), '#c0aa9e')
        pen.fill(smooth([(px + pw / 2 - 66, py + 110), (px + pw / 2 - 60, py + 50), (px + pw / 2, py + 34), (px + pw / 2 + 62, py + 52), (px + pw / 2 + 66, py + 108),
                         (px + pw / 2 + 40, py + 72), (px + pw / 2 - 40, py + 74)], True, 0.6), '#4a3428')
        for ex in (-22, 22):
            pen.fill(oval(px + pw / 2 + ex, py + 118, 9, 6), '#f0f0f0'); pen.fill(oval(px + pw / 2 + ex, py + 118, 3), '#1a1a1a')
        pen.seg((px + pw / 2 - 16, py + 160), (px + pw / 2 + 16, py + 160), 3, '#6a4a44')
        pen.seg((px + pw / 2 - 30, py + 156), (px + pw / 2 - 26, py + 164), 2.5, '#8a6a64')               # scar, left of mouth
        cv.restore()
    pen.line(rect(px, py, pw, ph), 2, '#5a6a7a')
    tx = px + pw + 36; ty = py + 18
    for lab, val in (('DL', '4471 0293 18'), ('EXP', '03/14/2029'), ('', name), ('', address), ('', 'MAPLE GROVE'), ('DOB', '03/14/1991'),
                     ('SEX', 'M   HGT 5-11   EYES BRN')):
        if lab: _type(cv, lab, tx, ty + 6, 16, '#a32a2a', 255, 'mono_b'); _type(cv, val, tx + 58, ty + 6, 24, '#111111', 255, 'mono_b')
        else: _type(cv, val, tx, ty + 6, 24, '#111111', 255, 'mono_b')
        ty += 38
    _signature(pen, tx + 10, ty + 28, 230, 34, sign_seed, '#111111')
    pen.fill(oval(W / 2 - 110, H / 2 - 90, 58), '#c9a64a', 60)                                            # hologram seal
    pen.line(oval(W / 2 - 110, H / 2 - 90, 58), 2, '#c9a64a', 120)
    if glare:
        cv.save(); cv.clipPath(card, skia.ClipOp.kIntersect, True)
        pen.fill(poly([(-W / 2 + W * 0.15, H / 2), (-W / 2 + W * 0.45, H / 2), (-W / 2 + W * 0.75, -H / 2), (-W / 2 + W * 0.45, -H / 2)]), '#ffffff', 170 * glare, blur=20)
        cv.restore()
    if wear:
        cv.save(); cv.clipPath(card, skia.ClipOp.kIntersect, True)
        pen.texture(card, 'grunge', 0.3 * wear, 'multiply', 1.0); cv.restore()
    pen.line(card, 3, '#5a6a7a')
    if broken:
        pen.line(poly([(W / 2 - 86, -H / 2 + 30), (W / 2 - 58, -H / 2 + 34), (W / 2 - 40, -H / 2 + 70), (W / 2 - 22, -H / 2 + 62), (W / 2, -H / 2 + 92)], False), 3, '#f4f8fa', 230)


def _prop_notebook(pen, t, lines=None, pen_on=True, page_turn=0.0, **kw):
    W, H = 600, 820
    lines = lines or ['144 ELM ST    00:36', 'Caller: homeowner (vehicle)', 'Subj. inside - refuses ID', '', 'Q1 kitchen tiles?  GREEN',
                      'Q2 first pet?  ...', 'Q3 photo in hall - who', '     took it?  MOTHER', '', 'Verify: ___________']
    cover = rrect(-W / 2 - 14, -H / 2 - 10, W + 28, H + 24, 18)
    pen.shadow(cover, 10, 16, 20, '#000000', 140)
    pen.shape(cover, '#1a1e26', 4)
    pg = rect(-W / 2, -H / 2 + 30, W, H - 30)
    pen.fill(pg, '#efe9da'); pen.texture(pg, 'paper', 0.5, 'overlay', 1.0)
    cv = pen.cv
    y = -H / 2 + 100
    while y < H / 2 - 10:
        pen.seg((-W / 2 + 10, y), (W / 2 - 10, y), 1.5, '#8ab0d0', 200); y += 62
    pen.seg((-W / 2 + 70, -H / 2 + 30), (-W / 2 + 70, H / 2), 2, '#d07070', 200)
    for i in range(14):                                                       # spiral
        x = -W / 2 + 30 + i * (W - 60) / 13
        pen.fill(oval(x, -H / 2 + 46, 7), '#2a2a2a')
        pen.line(smooth([(x - 6, -H / 2 + 46), (x - 3, -H / 2 + 6), (x + 6, -H / 2 + 8), (x + 5, -H / 2 + 44)], False), 4, '#9aa0a8')
    y = -H / 2 + 94
    for i, ln in enumerate(lines):
        if ln:
            parts = ln.split('  ')
            _hand_text(cv, ln, -W / 2 + 86, y - 10, 32, '#1d2a6a', 235, seed=i * 7 + 1, wobble=0.8)
            if ln.strip().endswith(('GREEN', 'MOTHER')):
                pen.line(oval(W / 2 - 110, y - 22, 92, 30), 3, '#a32a2a', 200)
        y += 62
    pen.line(poly([(W / 2 - 160, -H / 2 + 120), (W / 2 - 140, -H / 2 + 140), (W / 2 - 100, -H / 2 + 92)], False), 5, '#1d2a6a', 220)
    if pen_on:
        _prop_pen(pen, t, x=W / 2 - 40, y=H / 2 - 120, rot=-35, s=1.0)


def _prop_pen(pen, t, x=0.0, y=0.0, rot=0.0, s=1.0, click=0.0, **kw):
    cv = pen.cv; cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(s, s)
    body = rrect(-12, -230, 24, 360, 10)
    pen.shadow(body, 6, 10, 10, '#000000', 120)
    pen.linear(body, -12, 0, 12, 0, ['#2a2e36', '#5a606a', '#1a1d22'])
    pen.line(body, 2.5, LINE)
    pen.shape(poly([(-12, 130), (12, 130), (2, 168), (-2, 168)]), '#9aa0a8', 2)
    pen.fill(oval(0, 170, 2.5), '#1a1a1a')
    pen.shape(rrect(8, -220, 10, 120, 4), '#b8bcc4', 2)                            # clip
    pen.shape(rrect(-7, -250 + 12 * click, 14, 24, 4), '#9aa0a8', 2)               # button
    cv.restore()


def _prop_radio(pen, t, led=0.0, talk=0.0, cord=True, **kw):
    """Shoulder speaker-mic (lapel radio): grille, PTT, LED (led 0..1 red / talk 0..1 green), antenna stub, coiled cord."""
    W, H = 300, 420
    if cord:
        pts = [(0, H / 2 - 10)]
        for i in range(24):
            pts.append((18 * math.sin(i * 1.2) + i * 4, H / 2 + 6 + i * 16))
        pen.line(smooth(pts, False, 0.9), 12, '#111215')
        pen.line(smooth(pts, False, 0.9), 3, '#3a3d44', 160)
    body = rrect(-W / 2, -H / 2, W, H, 46)
    pen.shadow(body, 10, 16, 20, '#000000', 150)
    pen.linear(body, -W / 2, 0, W / 2, 0, ['#2a2d33', '#1b1d22', '#121317'])
    pen.line(body, 6, '#06070a')
    gr = rrect(-W / 2 + 40, -H / 2 + 60, W - 80, 220, 26)
    pen.fill(gr, '#0e0f12')
    for j in range(9):
        for i in range(7):
            pen.fill(oval(-W / 2 + 64 + i * 29 + (j % 2) * 14, -H / 2 + 82 + j * 22, 6), '#26282e')
    pen.line(gr, 3, '#2e3138')
    ptt = rrect(-W / 2 - 18, -40, 26, 120, 10)
    pen.shape(ptt, '#16181c', 4)
    for k in range(4): pen.seg((-W / 2 - 14, -24 + k * 26), (-W / 2 + 4, -24 + k * 26), 2, '#30333a')
    pen.shape(rrect(-30, H / 2 - 110, 60, 40, 10), '#202227', 3)
    text(pen.cv, 'EMERG', 0, H / 2 - 82, 800, 14, '#a33a3a', 230, 0.05)
    lx, ly = W / 2 - 60, -H / 2 + 34
    on_r, on_g = clamp(led), clamp(talk)
    pen.fill(oval(lx, ly, 10), mix('#3a0a0a', '#ff4a3a', on_r) if on_r >= on_g else mix('#0a3a12', '#5aff7a', on_g))
    if on_r > 0.05: pen.glow(lx, ly, 46, '#ff3020', 180 * on_r)
    if on_g > 0.05: pen.glow(lx, ly, 46, '#40ff60', 180 * on_g)
    pen.shape(rrect(W / 2 - 70, -H / 2 - 70, 40, 80, 14), '#16181c', 4)                 # antenna stub
    pen.fill(rect(-W / 2 + 14, -H / 2 + 20, 8, H - 40), '#ffffff', 22)                 # edge highlight
    pen.shape(rrect(-60, H / 2 - 40, 120, 26, 8), '#0b0c0f', 3)                         # clip mount


def _key_path(L=300.0, teeth_seed=1, bow='round'):
    """A house key lying along +x from its bow at (0, 0)."""
    bw = L * 0.32
    bowp = oval(0, 0, bw * 0.55, bw * 0.5) if bow == 'round' else rrect(-bw * 0.55, -bw * 0.5, bw * 1.1, bw, bw * 0.2)
    bowp = minus(bowp, oval(-bw * 0.2, 0, bw * 0.13))
    blade = [(bw * 0.45, -L * 0.055), (L, -L * 0.055), (L * 1.04, 0)]
    x = L
    rng = np.random.default_rng(teeth_seed)
    while x > bw * 0.6:
        blade.append((x, L * 0.055 + rng.uniform(0.02, 0.07) * L)); x -= L * 0.07
        blade.append((x, L * 0.055)); x -= L * 0.03
    blade.append((bw * 0.45, L * 0.055))
    return union(bowp, poly(blade))


def _prop_keys(pen, t, ring='#c9c2b4', fob=None, n=3, swing=0.0, single=False, **kw):
    """Keys on a ring. ring colour; fob = hex for a bright fob (the neighbour's orange key ring: '#ff7a1a').
    single=True draws one key (the double's key: 'your key')."""
    cv = pen.cv
    if single:
        k = _key_path(300, 3)
        pen.shadow(k, 6, 10, 10, '#000000', 130)
        pen.linear(k, 0, -60, 0, 60, ['#d8c890', '#a88a4a'])
        pen.line(k, 3, '#4a3a1a')
        pen.seg((110, -6), (300, -6), 2, '#fff2c8', 160)
        return
    rr = 70
    pen.line(oval(0, 0, rr), 9, '#5a5650'); pen.line(oval(0, 0, rr), 5, ring)
    if fob:
        cv.save(); cv.rotate(200 + 8 * math.sin(t * 3) * swing)
        f = union(oval(rr + 60, 0, 52, 40), rect(rr - 6, -12, 70, 24))
        pen.shadow(f, 5, 8, 8, '#000000', 120)
        pen.shape(f, fob, 4)
        pen.line(oval(rr + 70, 0, 22, 14), 3, _darken(fob, 0.3), 200)
        pen.fill(oval(rr + 52, -12, 14, 6), '#ffffff', 90)
        cv.restore()
    cols = [('#d8c890', '#a88a4a'), ('#c8ccd2', '#8a9098'), ('#c89a6a', '#8a5a3a'), ('#c8ccd2', '#7a8088')]
    for i in range(n):
        ang = 60 + i * 34 + 6 * math.sin(t * 2.4 + i) * swing
        cv.save(); cv.rotate(ang); cv.translate(rr + 10, 0)
        k = _key_path(250 - i * 18, i + 2, 'round' if i % 2 == 0 else 'square')
        pen.shadow(k, 5, 8, 8, '#000000', 110)
        a, b = cols[i % len(cols)]
        pen.linear(k, 0, -50, 0, 50, [a, b]); pen.line(k, 3, '#3a3020')
        cv.restore()


def _prop_wallet(pen, t, **kw):
    w = rrect(-170, -120, 340, 240, 24)
    pen.shape(w, '#5a3424', 4); pen.texture(w, 'fabric', 0.3, 'overlay', 0.8)
    pen.dashed(rrect(-156, -106, 312, 212, 18), 2.5, '#c8a070', 200, 10, 7)
    pen.fill(rect(-170, -20, 340, 6), '#3a2016', 200)
    pen.fill(rrect(40, -150, 120, 50, 6), '#e8e0d0')                         # a card sticking out
    pen.line(rrect(40, -150, 120, 50, 6), 2, '#8a8478')


def _prop_phone(pen, t, screen='off', name='MUM', face_down=False, vibrate=0.0, **kw):
    """Smartphone (prop): screen 'off' | 'calling' | 'busy' | 'incoming' | 'lock' (time 12:36); vibrate 0..1 jitters."""
    cv = pen.cv
    if vibrate: cv.translate(3 * vibrate * math.sin(t * 2 * math.pi * 30), 2 * vibrate * math.cos(t * 2 * math.pi * 23))
    W, H = 300, 620
    body = rrect(-W / 2, -H / 2, W, H, 44)
    pen.shadow(body, 8, 14, 18, '#000000', 150)
    pen.fill(body, '#15171c'); pen.line(body, 5, '#06070a')
    if face_down:
        pen.linear(body, -W / 2, 0, W / 2, 0, ['#2a2e36', '#1a1d22'])
        pen.shape(rrect(-W / 2 + 26, -H / 2 + 26, 110, 130, 30), '#0e0f12', 4)
        for (cx, cy) in ((-W / 2 + 60, -H / 2 + 62), (-W / 2 + 102, -H / 2 + 62), (-W / 2 + 60, -H / 2 + 112)):
            pen.fill(oval(cx, cy, 18), '#05060a'); pen.line(oval(cx, cy, 18), 3, '#3a3d44')
        return
    sc = rrect(-W / 2 + 14, -H / 2 + 14, W - 28, H - 28, 34)
    if screen == 'off':
        pen.linear(sc, 0, -H / 2, 0, H / 2, ['#0a0b0e', '#121418'])
        pen.fill(poly([(-W / 2 + 20, H / 2 - 60), (-W / 2 + 60, H / 2 - 20), (W / 2 - 20, -H / 2 + 120), (W / 2 - 20, -H / 2 + 40)]), '#ffffff', 14)
    else:
        bg = {'calling': ['#1a2a3a', '#0a1018'], 'busy': ['#3a1a1a', '#140808'], 'incoming': ['#1a3a2a', '#081410'], 'lock': ['#202a44', '#0a0e1a']}[screen]
        pen.linear(sc, 0, -H / 2, 0, H / 2, bg)
        if screen == 'lock':
            text(cv, '12:36', 0, -H / 2 + 170, 700, 76, '#ffffff', 240)
            text(cv, 'Saturday, October 31', 0, -H / 2 + 210, 600, 18, '#d8e0f0', 220)
        else:
            text(cv, name, 0, -H / 2 + 150, 800, 40, '#ffffff', 245, 0.04)
            sub = {'calling': 'calling' + '.' * (1 + int(t * 2) % 3), 'busy': 'User busy', 'incoming': 'incoming call'}[screen]
            text(cv, sub, 0, -H / 2 + 190, 600, 20, '#d8e0f0' if screen != 'busy' else '#ff8a7a', 230)
            pen.fill(oval(0, -H / 2 + 300, 62), '#3a4a5a'); text(cv, name[:1], 0, -H / 2 + 322, 800, 60, '#e8eef8', 230)
            if screen in ('calling', 'busy'):
                pen.fill(oval(0, H / 2 - 100, 40), '#e03a3a')
                pen.fill(rrect(-18, H / 2 - 104, 36, 10, 5), '#ffffff')
            else:
                pen.fill(oval(-80, H / 2 - 100, 40), '#e03a3a'); pen.fill(oval(80, H / 2 - 100, 40), '#3ac060')
    pen.fill(rrect(-40, -H / 2 + 26, 80, 18, 9), '#05060a')


def _prop_bag(pen, t, crinkle=0.0, **kw):
    """Clear plastic evidence bag: a wallet, a phone and a small bunch of keys with a bright orange key ring."""
    cv = pen.cv
    W, H = 700, 880
    cv.save(); cv.translate(-90, 90); cv.rotate(-8); cv.scale(0.75, 0.75); _prop_wallet(pen, t); cv.restore()
    cv.save(); cv.translate(140, -70); cv.rotate(12); cv.scale(0.6, 0.6); _prop_phone(pen, t, 'off'); cv.restore()
    cv.save(); cv.translate(-60, -170); cv.rotate(-20); cv.scale(0.55, 0.55); _prop_keys(pen, t, '#c9c2b4', '#ff7a1a', 3); cv.restore()
    bag = rrect(-W / 2, -H / 2 + 60, W, H - 60, 30)
    pen.fill(bag, '#dfe8f0', 34)
    for (x0, w, a) in ((-W / 2 + 40, 50, 60), (-W / 2 + 120, 18, 50), (W / 2 - 140, 70, 40)):
        pen.fill(poly([(x0, -H / 2 + 80), (x0 + w, -H / 2 + 80), (x0 + w + 60, H / 2 - 20), (x0 + 60, H / 2 - 20)]), '#ffffff', a)
    rng = np.random.default_rng(5 + int(crinkle * 3))
    for _ in range(14):
        x, y = rng.uniform(-W / 2 + 20, W / 2 - 20), rng.uniform(-H / 2 + 100, H / 2 - 30)
        pen.line(smooth([(x, y), (x + rng.uniform(-60, 60), y + rng.uniform(20, 70)), (x + rng.uniform(-40, 40), y + rng.uniform(80, 140))], False), 2.5, '#ffffff', 70)
    pen.line(bag, 4, '#c8d4e0', 200)
    seal = rect(-W / 2, -H / 2 + 60, W, 46)
    pen.fill(seal, '#c83a3a', 230); pen.fill(rect(-W / 2, -H / 2 + 74, W, 8), '#ffffff', 160)
    lab = rect(-W / 2 + 40, H / 2 - 220, 300, 170)
    pen.fill(lab, '#f0ece0', 235); pen.line(lab, 2, '#8a8478')
    text(cv, 'EVIDENCE', -W / 2 + 190, H / 2 - 186, 900, 30, '#c83a3a', 240, 0.06)
    for k, s_ in enumerate(('CASE  24-1187', 'ITEM  3', 'FOUND  148 ELM')):
        _type(cv, s_, -W / 2 + 56, H / 2 - 146 + k * 30, 18, '#222222', 240, 'mono_b')
    _hand_text(cv, 'outside', -W / 2 + 200, H / 2 - 86, 24, '#1d2a6a', 230, 9)


def _prop_lock(pen, t, turn=0.0, chain=0.0, side='inside', key_in=0.0, **kw):
    """Deadbolt. side 'inside': brass thumb-turn on an escutcheon plate, turn 0..1 (0 = locked, vertical), plus the chain
    (chain 0 = hanging, 1 = engaged). side 'outside': key cylinder; key_in 0..1 slides a key toward the keyway."""
    cv = pen.cv
    door = rect(-1500, -1000, 3000, 2000)
    pen.linear(door, -1500, 0, 1500, 0, ['#4f2c20', '#3a2018'])
    pen.texture(door, 'wood', 0.6, 'overlay', 2.2, 90)
    plate = rrect(-110, -230, 220, 460, 60)
    pen.shadow(plate, 6, 10, 12, '#000000', 140)
    pen.radial(plate, -40, -100, 400, [(0, '#f0d890'), (0.6, '#c9a64a'), (1, '#8a6a2a')])
    pen.line(plate, 5, '#4a3a1a')
    for sy in (-180, 180):
        pen.fill(oval(0, sy, 14), '#8a6a2a'); pen.seg((-9, sy), (9, sy), 3, '#4a3a1a')
    if side == 'inside':
        cv.save(); cv.rotate(90 * clamp(turn))
        th = rrect(-26, -110, 52, 220, 22)
        pen.shadow(th, 4, 8, 8, '#000000', 140)
        pen.linear(th, -26, 0, 26, 0, ['#e8cc80', '#c9a64a', '#8a6a2a']); pen.line(th, 4, '#4a3a1a')
        pen.fill(oval(0, 0, 40), '#b8962e'); pen.line(oval(0, 0, 40), 4, '#4a3a1a')
        cv.restore()
        # chain lock (to the right)
        pen.shape(rrect(260, -190, 160, 60, 14), '#b8a880', 4)
        pts = [(300, -160), (520, -160)] if chain > 0.5 else [(300, -160), (300, -60), (320, 40)]
        cp = smooth(pts, False, 0.8); meas = skia.PathMeasure(cp, False); L_ = meas.getLength(); n = max(2, int(L_ / 26))
        for i in range(n):
            pos, _ = meas.getPosTan((i + 0.5) * L_ / n)
            pen.line(oval(pos.x(), pos.y(), 9, 14) if i % 2 else oval(pos.x(), pos.y(), 14, 8), 5, '#d8c8a0')
        pen.fill(oval(pts[-1][0], pts[-1][1] + 14, 16), '#b8a880')
    else:
        pen.fill(oval(0, 0, 70), '#a88a3a'); pen.line(oval(0, 0, 70), 5, '#4a3a1a')
        pen.fill(oval(0, 0, 48), '#d8bc6a')
        kw_ = union(rrect(-8, -34, 16, 46, 6), oval(0, -36, 13))
        pen.fill(kw_, '#1a1208')
        if key_in > 0.01:
            cv.save(); cv.translate(0, 330 - 300 * clamp(key_in)); cv.rotate(-90); cv.scale(1.3, 1.3)
            _prop_keys(pen, t, single=True); cv.restore()


def _prop_photo(pen, t, framed=True, faded=0.0, **kw):
    if framed:
        _picture(pen, -380, -300, 760, 600, 'photo', '#2a1f18', '#e8e0d0', 600)
    else:
        p = rect(-360, -270, 720, 540)
        pen.shadow(p, 8, 12, 14, '#000000', 140)
        pen.fill(p, '#f0ece2'); _photo_content(pen, -330, -240, 660, 450, faded)
        pen.fill(poly([(-330, -240), (-200, -240), (-330, -120)]), '#ffffff', 40)


def _prop_tiles(pen, t, c='#2f5a8a', **kw):
    for j in range(-6, 7):
        for i in range(-10, 11):
            x, y = i * 120, j * 120
            cc = mix(c, '#ffffff' if _h(i * 31 + j * 7 + 100, 7) > 0.5 else '#000000', 0.05 + 0.1 * _h(i * 17 + j + 50, 8))
            tl = rrect(x - 56, y - 56, 112, 112, 6)
            pen.linear(tl, x - 56, y - 56, x - 56, y + 56, [_lighten(cc, 0.12), cc])
            pen.fill(rrect(x - 48, y - 50, 50, 8, 4), '#ffffff', 70)
    pen.texture(rect(-1300, -800, 2600, 1600), 'grunge', 0.25, 'overlay', 1.0)


def _prop_card_back(pen, t, **kw):
    """The licence seen from behind (raised against the car window): magnetic strip, barcode, the broken corner."""
    W, H = 856, 540
    card = minus(rrect(-W / 2, -H / 2, W, H, 34), poly([(-W / 2 - 5, -H / 2 - 5), (-W / 2 + 120, -H / 2 - 5), (-W / 2 + 86, -H / 2 + 30),
                                                         (-W / 2 + 58, -H / 2 + 34), (-W / 2 + 40, -H / 2 + 70), (-W / 2 + 22, -H / 2 + 62),
                                                         (-W / 2 - 5, -H / 2 + 95)]))
    pen.shadow(card, 8, 14, 18, '#000000', 140)
    pen.fill(card, '#d9e3ea')
    pen.cv.save(); pen.cv.clipPath(card, skia.ClipOp.kIntersect, True)
    pen.fill(rect(-W / 2, -H / 2 + 120, W, 80), '#1a1a1a')
    for i in range(70):
        w = 3 + 6 * _h(i, 4)
        pen.fill(rect(-W / 2 + 60 + i * 10.5, H / 2 - 170, w * 0.6, 110), '#1a1a1a')
    pen.cv.restore()
    pen.line(card, 3, '#5a6a7a')


PROPS = {'complaint': _prop_complaint, 'licence': _prop_licence, 'notebook': _prop_notebook, 'pen': _prop_pen, 'radio': _prop_radio,
         'keys': _prop_keys, 'wallet': _prop_wallet, 'phone': _prop_phone, 'bag': _prop_bag, 'lock': _prop_lock, 'photo': _prop_photo,
         'tiles': _prop_tiles, 'licence_back': _prop_card_back}
_STATIC_PROPS = ('complaint', 'licence', 'notebook', 'bag', 'photo', 'tiles', 'licence_back', 'wallet', 'keys')
PROP_SIZE = {'complaint': (700, 960), 'licence': (856, 540), 'notebook': (630, 850), 'pen': (40, 420), 'radio': (300, 420),
             'keys': (520, 520), 'wallet': (340, 300), 'phone': (300, 620), 'bag': (700, 880), 'lock': (1400, 1120), 'photo': (760, 600),
             'tiles': (2600, 1600), 'licence_back': (856, 540)}


def draw_prop(pen, name, x, y, scale=1.0, rot=0.0, t=0.0, cache=False, **kw):
    """Draw prop `name` centred at (x, y), rotated `rot` degrees, at `scale` (1.0 = insert size; PROP_SIZE gives the size in
    design px at scale 1). Works at any scale (pure vector). kw go to the prop (see PROPS functions).
    cache=True: draw through a sprite cache keyed by name + kw (use when the prop's look is static while it moves; the
    text-heavy complaint sheet costs ~85 ms live at 2560 and ~3 ms cached)."""
    cv = pen.cv
    cv.save(); cv.translate(x, y)
    if cache:
        w, h = PROP_SIZE.get(name, (1000, 1000))
        key = ('prop', name, tuple(sorted((k, repr(v)) for k, v in kw.items())))
        _sprite(pen, key, lambda p: PROPS[name](p, 0.0, **kw), (-w * 0.62, -h * 0.62, w * 0.62, h * 0.62), scale=scale, rot=rot)
    else:
        cv.rotate(rot); cv.scale(scale, scale)
        PROPS[name](pen, t, **kw)
    cv.restore()


def draw_hand(pen, x, y, scale=1.0, rot=0.0, pose='hold', skin='#c0aa9e', sleeve='#4a5058', side=1, cuff=None, part='all'):
    """Simple cartoon hand + sleeve for inserts (characters.py may replace it). (x, y) = the thumb tip on the object's
    face; the forearm comes from below (rotate with rot, degrees). pose 'hold': palm and fingers BEHIND the object
    (part='back', draw before the prop) and the thumb in FRONT (part='front', after); 'flat': palm pressed on glass
    (front only); 'pinch': fingertips holding an object's top edge from above (bag, sheet). side=1 right, -1 left hand.
    cuff = hex: a loose thread hanging from the cuff."""
    cv = pen.cv
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(scale * side, scale)
    sh = mix(skin, '#4a3430', 0.4); lw = 6
    back = part in ('all', 'back'); front = part in ('all', 'front')
    if pose == 'point':                                          # index finger extended, tip at (0, 0), arm from below
        CHm = _CH()
        if front and CHm is not None and hasattr(CHm, 'draw_hand'):      # the cast's hand rig (driver) + a sleeve
            arm = poly([(-170, 290), (40, 290), (90, 1000), (-230, 1000)])
            pen.shape(arm, sleeve, lw); pen.texture(arm, 'fabric', 0.45, 'overlay', 1.0)
            pen.shape(rrect(-185, 262, 240, 62, 22), _darken(sleeve, 0.15), lw)
            CHm.draw_hand(pen, 'driver', -66, 272, 300, 'point', 180, 1)
            cv.restore()
            return
        if front:
            arm = poly([(-70, 300), (90, 300), (150, 1000), (-110, 1000)])
            pen.shape(arm, sleeve, lw); pen.texture(arm, 'fabric', 0.45, 'overlay', 1.0)
            fist = smooth([(-62, 150), (-70, 250), (-20, 320), (70, 315), (92, 230), (80, 140), (20, 120)], True, 0.7)
            pen.shape(rrect(-17, -4, 36, 190, 18), skin, lw)                                    # the index finger
            pen.fill(rrect(-10, 6, 22, 30, 10), mix(skin, '#ffffff', 0.35), 190)                  # nail
            pen.seg((-12, 70), (14, 70), 2.5, sh, 170); pen.seg((-12, 118), (14, 118), 2.5, sh, 150)
            pen.shape(fist, skin, lw)
            for k in range(3):                                                                    # curled fingers
                pen.line(smooth([(10 + k * 22, 160), (34 + k * 22, 172), (40 + k * 22, 205)], False), 3, sh, 200)
            th = smooth([(-64, 230), (-30, 200), (20, 205), (24, 232), (-30, 250)], True, 0.7)
            pen.shape(th, skin, lw); pen.shade(fist, oval(60, 280, 60, 50), sh, 110)
            pen.shape(rrect(-80, 300, 182, 60, 22), _darken(sleeve, 0.15), lw)
        cv.restore()
        return
    if pose == 'flat':
        if front:
            arm = poly([(-80, 160), (80, 160), (120, 900), (-120, 900)])
            pen.shape(arm, sleeve, lw); pen.texture(arm, 'fabric', 0.45, 'overlay', 1.0)
            palm = smooth([(-78, 170), (-92, 40), (-70, -60), (70, -60), (92, 40), (78, 170)], True, 0.6)
            for (fx, ln, ang) in ((-58, 120, -10), (-20, 150, -3), (20, 155, 3), (58, 130, 10)):
                cv.save(); cv.translate(fx, -50); cv.rotate(ang)
                f = rrect(-18, -ln, 36, ln + 30, 18)
                pen.shape(f, skin, lw); pen.fill(rrect(-11, -ln + 6, 22, 26, 10), '#d8c8c0', 170)
                pen.seg((-12, -ln * 0.45), (12, -ln * 0.45), 2.5, sh, 160)
                cv.restore()
            pen.shape(palm, skin, lw)
            cv.save(); cv.translate(-80, 60); cv.rotate(-48)
            pen.shape(rrect(-20, -120, 40, 130, 20), skin, lw); pen.fill(rrect(-12, -112, 24, 28, 10), '#d8c8c0', 170)
            cv.restore()
            pen.shade(palm, oval(30, 80, 70, 90), sh, 90)
            pen.shape(rrect(-92, 150, 184, 56, 20), _darken(sleeve, 0.15), lw)
            if cuff: pen.line(smooth([(50, 200), (64, 260), (52, 330)], False), 3, cuff)
    elif pose == 'pinch':
        if back:
            arm = poly([(-70, -170), (70, -170), (110, -900), (-110, -900)])
            pen.shape(arm, sleeve, lw); pen.texture(arm, 'fabric', 0.45, 'overlay', 1.0)
            pen.shape(rrect(-84, -200, 168, 56, 20), _darken(sleeve, 0.15), lw)
            palm = smooth([(-70, -160), (-80, -60), (-40, -10), (50, -10), (80, -60), (70, -160)], True, 0.6)
            pen.shape(palm, skin, lw); pen.shade(palm, oval(40, -60, 60, 70), sh, 100)
        if front:
            for fx in (-36, -4, 28):
                pen.shape(rrect(fx - 15, -30, 30, 72, 15), skin, lw)
                pen.fill(rrect(fx - 9, 14, 18, 22, 8), '#d8c8c0', 170)
    else:                                                       # hold
        if back:
            arm = poly([(-60, 230), (90, 230), (140, 900), (-90, 900)])
            pen.shape(arm, sleeve, lw); pen.texture(arm, 'fabric', 0.45, 'overlay', 1.0)
            palm = smooth([(-70, 240), (-95, 150), (-60, 60), (40, 40), (100, 110), (90, 240)], True, 0.6)
            pen.shape(palm, skin, lw)
            for i, fx in enumerate((-40, -5, 30, 62)):
                pen.shape(rrect(fx - 16, 30 - i * 4, 34, 60, 16), _darken(skin, 0.08), lw)
            pen.shade(palm, oval(50, 190, 60, 70), sh, 110)
            pen.shape(rrect(-70, 220, 172, 60, 22), _darken(sleeve, 0.15), lw)
            if cuff: pen.line(smooth([(60, 270), (74, 330), (62, 400)], False), 3, cuff)
        if front:
            th = smooth([(-26, -18), (22, -22), (34, 30), (10, 140), (-58, 190), (-80, 150), (-46, 70)], True, 0.7)
            pen.shape(th, skin, lw)
            pen.fill(smooth([(-14, -8), (16, -12), (22, 22), (-12, 26)], True, 0.7), '#d8c8c0', 190)
            pen.line(smooth([(-38, 96), (-8, 108), (8, 96)], False), 3, sh, 170)
            pen.shade(th, oval(-50, 150, 40, 50), sh, 100)
    cv.restore()


# ============================================================== insert compositions
def _bg_hall(pen, t):
    pen.fill(rect(-400, -300, 2720, 1700), '#2a2836')
    _wallpaper(pen, rect(-400, -300, 2720, 1700), (-400, -300, 2320, 1400), 900, '#3b3a48', '#2a2834', 'damask', 160)
    pen.fill(rect(1300, -300, 420, 1700), '#4a2c20'); pen.texture(rect(1300, -300, 420, 1700), 'wood', 0.5)
    pen.radial(None, 380, 360, 260, [(0, '#ffd9a0', 230), (0.4, '#ffcf8f', 90), (1, '#ffcf8f', 0)], clip=False)
    pen.fill(oval(380, 360, 60), '#fff4dc', 230)
    pen.fill(rect(-400, 900, 2720, 600), '#2a1e16'); pen.fill(rect(-400, 860, 2720, 50), '#1c1714')


def _bg_wood(pen, t):
    r = rect(-500, -400, 2920, 1880)
    pen.linear(r, 0, -400, 0, 1480, ['#3a2618', '#5a3c26', '#2a1a10'])
    pen.texture(r, 'wood', 0.7, 'overlay', 3.0, 90)
    pen.radial(None, 900, 300, 1200, [(0, '#ffcf8f', 60), (1, '#ffcf8f', 0)], clip=False)


def _bg_porch(pen, t):
    pen.linear(rect(-500, -400, 2920, 1880), 0, -400, 0, 1400, ['#05070f', '#0d1530', '#141a2a'])
    for (x, y, r, c, a) in ((1500, 260, 120, '#ffcf8f', 200), (300, 420, 70, '#d9b47c', 160), (620, 380, 50, '#d9b47c', 140), (1750, 600, 40, '#ffe0b0', 120)):
        pen.fill(oval(x, y, r), c, a); pen.line(oval(x, y, r * 0.96), 4, '#ffffff', 40)
    pen.fill(rect(-500, 700, 2920, 800), '#1a1612')
    for k in range(-5, 30): pen.seg((k * 120, 700), (k * 180 - 900, 1500), 4, '#0e0b09', 160)


def _bg_uniform(pen, t):
    r = rect(-500, -400, 2920, 1880)
    pen.linear(r, -500, 0, 2400, 0, ['#141a2a', '#1c2438', '#10141f'])
    pen.texture(r, 'fabric', 0.6, 'overlay', 2.2)
    pen.line(smooth([(-200, 150), (700, 60), (1500, 120), (2300, 260)], False), 6, '#0a0d16')      # shoulder seam
    ep = poly([(200, 40), (1300, -40), (1340, 110), (240, 190)])
    pen.shape(ep, '#18203a', 5); pen.fill(oval(1240, 60, 30), '#c9a64a'); pen.line(oval(1240, 60, 30), 3, '#5a4a1a')
    pen.line(smooth([(1350, 1500), (1500, 700), (1700, 420), (2300, 360)], False), 10, '#0a0d16', 220)   # placket seam
    pen.radial(None, 1700, 160, 520, [(0, '#ffcf8f', 70), (1, '#ffcf8f', 0)], clip=False)                     # porch lamp spill


def _bg_door_inside(pen, t):
    r = rect(-600, -400, 3120, 1880)
    pen.linear(r, -600, 0, 2520, 0, ['#4f2c20', '#3e2219'])
    pen.texture(r, 'wood', 0.6, 'overlay', 2.6, 90)
    for (x, y, w, h) in ((-300, -300, 900, 500), (1100, -300, 900, 500), (-300, 760, 900, 700), (1100, 760, 900, 700)):
        pen.fill(rect(x, y, w, h), '#3a2018'); pen.line(rect(x, y, w, h), 6, '#1e100a', 200)


def _bg_tiles(pen, t):
    _prop_tiles(pen, t)


def _bg_car(pen, t):
    pen.fill(rect(-500, -400, 2920, 1880), '#0b0c10')
    seat = smooth([(-300, 1500), (-200, 300), (200, 180), (1700, 180), (2100, 300), (2200, 1500)], True, 0.3)
    pen.linear(seat, 0, 180, 0, 1200, ['#2a2b30', '#121317'])
    pen.texture(seat, 'fabric', 0.4, 'overlay', 2.0)
    for x in (300, 1500): pen.shape(rrect(x - 260, -120, 520, 260, 90), '#1e1f24', 8)
    pen.fill(rect(-500, -400, 2920, 160), '#050608')


def _bg_kitchen(pen, t):
    """Far kitchen behind the backsplash insert: dark cabinets, window glow, fridge edge."""
    pen.linear(rect(-600, -400, 3120, 1880), 0, -400, 0, 1480, ['#141a26', '#1d2433', '#0e1118'])
    pen.fill(rect(-600, -400, 3120, 380), '#232a38'); pen.fill(rect(-600, -40, 3120, 30), '#0b0e14')
    pen.radial(None, 1650, 250, 420, [(0, '#9fb6ff', 90), (1, '#9fb6ff', 0)], clip=False)
    pen.fill(rect(1500, 120, 300, 260), '#2c3a5c', 200)


_BG = {'hall': _bg_hall, 'wood': _bg_wood, 'porch': _bg_porch, 'uniform': _bg_uniform, 'door': _bg_door_inside, 'tiles': _bg_kitchen,
       'car': _bg_car}


# ---- v2.1 layered inserts (VISUAL_SPEC e: 3-5 depth layers, a practical light): every insert gets a dark foreground edge
# (depth 0.6, blurred by the DOF), the prop and the plane it sits on in focus, and a lit background; doors get the light
# leaking through the door gap (police red / blue), the photo hangs on an in-focus wall, the tiles are a kitchen corner.
def _fg_edge(kind):
    def draw(pen, t):
        if kind in ('door', 'hall'):                                   # door jamb / coat on the left edge
            pen.linear(rect(-500, -400, 760, 1880), -500, 0, 260, 0, [(0, '#050405', 255), (0.75, '#0b0a0c', 250), (1, '#0b0a0c', 0)])
            if kind == 'hall':
                pen.fill(smooth([(-200, -300), (230, -100), (320, 500), (200, 1500), (-200, 1500)], True, 0.35), '#151319')
        elif kind == 'porch':                                          # porch post on the right
            pen.fill(rect(1720, -400, 700, 1880), '#08080b')
            pen.linear(rect(1640, -400, 120, 1880), 1640, 0, 1760, 0, [(0, '#08080b', 0), (1, '#08080b', 255)])
            pen.fill(rect(1730, -400, 14, 1880), '#2a2a30', 160)
        elif kind == 'uniform':                                        # the officer's collar edge across the top corner
            pen.fill(smooth([(-500, -400), (900, -400), (520, 40), (-500, 260)], True, 0.3), '#07090f')
        elif kind == 'wood':                                           # table edge in front
            pen.fill(rect(-500, 1010, 2920, 500), '#120c08'); pen.line(smooth([(-500, 1012), (2420, 1000)], False), 8, '#3a2618', 200)
        elif kind == 'car':                                            # window pillar
            pen.fill(poly([(-500, -400), (60, -400), (-140, 1480), (-500, 1480)]), '#050608')
    return draw


def _door_gap(lf):
    """Light leaking through the gap between the door and the jamb (porch light, then the light bar's red / blue)."""
    def draw(pen, t):
        r_, b_ = lf(t); r_, b_ = _lv(r_), _lv(b_)
        c = '#ffcf8f' if max(r_, b_) < 0.15 else ('#ff3a3a' if r_ >= b_ else '#4a6cff')
        k = 0.55 + 0.45 * max(r_, b_)
        pen.fill(rect(1552, -400, 9, 1880), c, 235 * k)
        pen.radial(None, 1556, 540, 380, [(0, c, 120 * k), (1, c, 0)], sy=2.4, clip=False)
    return draw


def _jamb(pen, t):
    pen.fill(rect(1561, -400, 800, 1880), '#2a160f'); pen.texture(rect(1561, -400, 800, 1880), 'wood', 0.5, 'overlay', 2.6, 90)
    pen.fill(rect(1561, -400, 60, 1880), '#3e2219'); pen.line(rect(1621, -400, 4, 1880), 4, '#140a06', 200)
    pen.linear(rect(1561, -400, 800, 1880), 1561, 0, 1940, 0, [(0, '#000000', 40), (1, '#000000', 170)])


def _lamp_falloff(pen, t):
    """Warm hall-lamp light falling across the in-focus plane from the upper left (a practical off frame)."""
    pen.radial(None, -150, 120, 1500, [(0, '#ffcf8f', 70), (0.55, '#ffcf8f', 18), (1, '#000000', 120)], clip=False)


def _photo_wall(pen, t):
    """The hallway wall the photograph hangs on (in focus): damask, chair rail, the lamp's falloff."""
    r = rect(330, -400, 2400, 1880)
    _wallpaper(pen, r, (330, -400, 2730, 1480), 900, '#3b3a48', '#2a2834', 'damask', 150)
    pen.fill(rect(330, 900, 2400, 600), '#2a2230'); pen.fill(rect(330, 880, 2400, 26), '#4a3a30')
    pen.linear(rect(300, -400, 80, 1880), 300, 0, 380, 0, [(0, '#000000', 0), (1, '#000000', 160)])
    pen.radial(None, 200, 200, 1500, [(0, '#ffcf8f', 60), (0.6, '#ffcf8f', 10), (1, '#000000', 110)], clip=False)
    pen.fill(oval(1650, 330, 16), '#8a6a3a'); pen.line(smooth([(1650, 330), (1600, 480)], False), 5, '#6a5030')   # coat hook


def _counter(pen, t):
    """Kitchen counter edge in front of the backsplash with a mug (depth 0.8)."""
    pen.fill(rect(-500, 830, 2920, 700), '#1a1512'); pen.linear(rect(-500, 830, 2920, 60), 0, 830, 0, 890, ['#5a4a3a', '#2a2018'])
    pen.shape(rrect(1260, 600, 210, 250, 26), '#d9d2c4', 8); pen.line(smooth([(1470, 660), (1560, 690), (1550, 790), (1470, 800)], False), 18, '#1d1f26')
    pen.line(smooth([(1470, 660), (1560, 690), (1550, 790), (1470, 800)], False), 9, '#d9d2c4')
    pen.fill(rrect(1275, 610, 40, 220, 18), '#ffffff', 70)
    pen.radial(None, 1365, 860, 260, [(0, '#000000', 160), (1, '#000000', 0)], sy=0.18, clip=False)


def _tiles_light(pen, t):
    pen.radial(None, 700, -250, 1300, [(0, '#ffe6b0', 80), (0.5, '#ffe6b0', 18), (1, '#000000', 150)], clip=False)
    pen.linear(rect(-600, 600, 3120, 300), 0, 600, 0, 840, [(0, '#000000', 0), (1, '#000000', 150)])
INSERTS = {
    'licence': dict(prop='licence', bg='hall', scale=1.25, rot=-6, hand=('hold', 1130, 800, 1.05, -8)),
    'licence_window': dict(prop='licence', bg='car', scale=0.9, rot=4, kw=dict(glare=0.85, photo=False), hand=('hold', 1080, 700, 0.95, 4),
                           glass=True),
    'complaint': dict(prop='complaint', bg='hall', scale=1.02, rot=2, hand=('hold', 690, 930, 1.0, 2)),
    'complaint_name': dict(prop='complaint', bg='hall', scale=2.4, rot=2, off=(0, -470), kw=dict(highlight='name')),
    'complaint_verified': dict(prop='complaint', bg='hall', scale=2.4, rot=2, off=(260, -700), kw=dict(highlight='verified')),
    'notebook': dict(prop='notebook', bg='porch', scale=1.05, rot=-4, hand=('hold', 760, 930, 1.0, -4)),
    'radio': dict(prop='radio', bg='uniform', scale=1.6, rot=-8, kw=dict(talk=1.0)),
    'keys_neighbour': dict(prop='bag', bg='porch', scale=1.0, rot=3, hand=('pinch', 990, 150, 0.9, 3)),
    'key_outside': dict(prop='lock', bg='porch', scale=0.85, rot=0, kw=dict(side='outside', key_in=0.6)),
    'lock_inside': dict(prop='lock', bg='door', scale=0.95, rot=0, kw=dict(side='inside', turn=0.0, chain=1.0)),
    'photo': dict(prop='photo', bg='hall', scale=0.95, rot=0, off=(140, -20), wall=True),
    'phone_busy': dict(prop='phone', bg='wood', scale=1.35, rot=-4, kw=dict(screen='busy'), hand=('hold', 1110, 820, 1.0, -6)),
    'phone_table': dict(prop='phone', bg='wood', scale=1.2, rot=18, kw=dict(screen='off')),
    'tiles': dict(prop='tiles', bg='tiles', scale=1.0, rot=0, off=(0, -200), kitchen=True),
    'mail_slot': dict(prop=None, bg='door', scale=1.0, rot=0),
}


def insert(name, t0=0.0, prop_kw=None, motion=None, hand=None, bg_dim=0.3, police=True, lens=None):
    """Close-up insert composition with background DOF. name: one of INSERTS (licence, licence_window, complaint,
    complaint_name, complaint_verified, notebook, radio, keys_neighbour (evidence bag), key_outside, lock_inside, photo,
    phone_busy, phone_table, tiles, mail_slot). Layers: background at depth 3 (blurred + darkened ~30 %), prop at depth 1
    (sharp), optional hand at 0.92. prop_kw: dict or f(t) -> dict overriding the prop's options (e.g. dict(turn=0.3),
    lambda t: dict(key_in=t/2)). motion: f(t) -> (dx, dy, dscale, drot) added to the prop pose (slides, shakes).
    hand: None = default from INSERTS, False = none, or (pose, x, y, scale, rot). Use dof=6.75, focus=1 (SetPiece.dof).
    'mail_slot': the door's mail slot from inside; prop_kw=dict(feed=0..1, item='complaint'|'licence', flap=0..1)."""
    spec = INSERTS[name]
    bgf = _BG[spec['bg']]
    bgd = spec.get('bgd', 1.04 if spec['bg'] == 'door' else 3.0)    # the lock / mail slot sit ON the door: keep it in focus
    L = [_cl(bgd, bgf, 'insert_bg', _key('ins', spec['bg']), (-700, -500, 2620, 1580), dim=bg_dim * (0.5 if bgd < 2 else 1.0))]
    lf = _lights_fn(police)
    if spec['bg'] in ('porch', 'car') and police:
        def bokeh(pen, t):
            r_, b_ = lf(t)
            r_, b_ = _lv(r_), _lv(b_)
            if r_ > 0.02: pen.radial(None, 250, 250, 300, [(0, '#ff2a2a', 170 * r_), (0.5, '#ff2a2a', 150 * r_), (0.56, '#ff2020', 50 * r_), (1, '#ff2020', 0)], clip=False)
            if b_ > 0.02: pen.radial(None, 520, 230, 300, [(0, '#3a5cff', 170 * b_), (0.5, '#3a5cff', 150 * b_), (0.56, '#2a4cff', 50 * b_), (1, '#2a4cff', 0)], clip=False)
        L.append(Layer(3.0, bokeh, 'insert_police'))
    if spec.get('glass'):
        def glass(pen, t):
            pen.linear(rect(-700, -500, 3320, 2080), 0, -500, 0, 1500, [(0, '#8ea6d8', 40), (1, '#2a3048', 6)])
            for (x0, w) in ((150, 160), (420, 60), (1250, 110)):
                pen.fill(poly([(x0, 1300), (x0 + w, 1300), (x0 + w + 700, -300), (x0 + 700, -300)]), '#c9d6f0', 26)
            pen.line(smooth([(-200, -60), (900, -110), (2200, -40)], False), 60, '#050608')
            pen.line(smooth([(-200, -60), (900, -110), (2200, -40)], False), 8, '#5a606c', 200)
        L.append(_cl(0.9, glass, 'insert_glass', _key('ins', 'glass'), (-700, -500, 2620, 1580), blur=0))
    if spec['bg'] == 'door':                                           # door jamb + light leaking through the gap
        L.append(_cl(0.999, _jamb, 'insert_jamb', _key('ins', 'jamb2'), (1540, -500, 2620, 1580), blur=0))     # in front of the
        L.append(Layer(0.998, _door_gap(lf if police else (lambda t: (0.0, 0.0))), 'insert_gap', blur=0))   # prop's door panel
        L.append(_cl(0.997, _lamp_falloff, 'insert_falloff', _key('ins', 'falloff'), (-700, -500, 2620, 1580), blur=0))
    if spec.get('wall'):                                              # the photo hangs on an in-focus wall
        L.append(_cl(1.03, _photo_wall, 'insert_wall', _key('ins', 'photo_wall'), (300, -500, 2620, 1580), blur=0))
    if spec.get('kitchen'):
        L.append(_cl(0.97, _tiles_light, 'insert_tiles_light', _key('ins', 'tiles_light'), (-700, -500, 2620, 1580), blur=0))
        L.append(_cl(0.8, _counter, 'insert_counter', _key('ins', 'counter'), (-700, 500, 2620, 1580)))
    L.append(_cl(0.6, _fg_edge(spec['bg']), 'insert_fg', _key('ins', 'fg', spec['bg']), (-700, -500, 2620, 1580)))
    hspec = spec.get('hand') if hand is None else hand
    base = (960 + spec.get('off', (0, 0))[0], 540 + spec.get('off', (0, 0))[1], spec['scale'], spec['rot'])

    def pose(t):
        x, y, s, r = base
        if motion:
            dx, dy, ds, dr = motion(t - t0); x += dx; y += dy; s *= (1 + ds); r += dr
        return x, y, s, r

    if spec['prop'] is not None:
        def prop(pen, t):
            kw = dict(spec.get('kw', {}))
            if prop_kw: kw.update(prop_kw(t - t0) if callable(prop_kw) else prop_kw)
            x, y, s, r = pose(t)
            draw_prop(pen, spec['prop'], x, y, s, r, t - t0, cache=spec.get('cache', spec['prop'] in _STATIC_PROPS), **kw)
        L.append(Layer(1.0, prop, 'insert_prop', blur=0))
    else:
        L += _mail_slot_layers(prop_kw, t0)
    if hspec:
        hp, hx, hy, hs, hr = hspec

        def hand_fn(part):
            def hand_draw(pen, t):
                x, y, s, r = pose(t)
                dx, dy = x - base[0], y - base[1]
                draw_hand(pen, hx + dx, hy + dy, hs, hr, hp, part=part, **spec.get('hand_kw', {}))
            return hand_draw
        L.append(Layer(1.02, hand_fn('back'), 'insert_hand_back', blur=0))
        L.append(Layer(0.92, hand_fn('front'), 'insert_hand', blur=0))
    if spec.get('extra'): L += spec['extra'](t0)
    grade = spec.get('grade') or ('face_close' if spec['bg'] in ('hall', 'wood', 'door', 'tiles') else 'night_blue')
    return SetPiece('insert:' + name, L, {}, {}, lens=lens if lens is not None else spec.get('lens'), grade=grade,
                    focus=1.0, dof=6.75, cover=WIDE if (lens or spec.get('lens')) else FRAME, info={'spec': spec, 'pose': pose})


def _mail_slot_layers(prop_kw, t0):
    """The mail slot from inside, big: brass flap, the dark gap with porch light, a sheet (or the licence) feeding in."""
    def get(t):
        kw = dict(feed=0.0, item='complaint', flap=None)
        if prop_kw: kw.update(prop_kw(t - t0) if callable(prop_kw) else prop_kw)
        if kw['flap'] is None: kw['flap'] = clamp(kw['feed'] * 4)
        return kw
    SX, SY, SW, SH = 560, 470, 800, 120

    def slot(pen, t):
        kw = get(t)
        pen.shadow(rrect(SX - 50, SY - 50, SW + 100, SH + 100, 24), 6, 10, 14, '#000000', 160)
        plate = rrect(SX - 50, SY - 50, SW + 100, SH + 100, 24)
        pen.radial(plate, SX + 200, SY - 40, 900, [(0, '#f0d890'), (0.6, '#c9a64a'), (1, '#7a5a22')]); pen.line(plate, 6, '#4a3a1a')
        pen.fill(rect(SX, SY, SW, SH), '#0a0806')
        pen.radial(rect(SX, SY, SW, SH), SX + SW / 2, SY + SH, SW * 0.6, [(0, '#ffcf8f', 150), (1, '#ffcf8f', 10)])
        text(pen.cv, 'LETTERS', SX + SW / 2, SY + SH + 36, 900, 26, '#5a4416', 220, 0.2)
        for sx in (SX - 26, SX + SW + 26): pen.fill(oval(sx, SY + SH / 2, 10), '#7a5a22')

    def item(pen, t):
        kw = get(t)
        f = clamp(kw['feed'])
        if f <= 0.0: return
        cv = pen.cv
        cv.save(); cv.clipPath(rect(-1000, SY + 6, 3920, 2000), skia.ClipOp.kIntersect, True)
        if kw['item'] == 'licence':
            y = SY + 20 - 300 + 560 * f
            draw_prop(pen, 'licence', SX + SW / 2, y, 0.8, -90 + 4 * math.sin(t), t, cache=True)
        else:
            y = SY - 520 + 1000 * f
            draw_prop(pen, 'complaint', SX + SW / 2, y, 0.95, 1.5, t, cache=True)
        cv.restore()

    def flap(pen, t):
        kw = get(t)
        fl = clamp(kw['flap'])
        h = SH * (1 - fl * 0.85)
        pen.radial(rect(SX, SY, SW, h), SX + 200, SY, 900, [(0, '#e8cc80'), (1, '#9a7a3a')])
        pen.line(rect(SX, SY, SW, h), 4, '#4a3a1a')
        pen.fill(rect(SX + 20, SY + 8, SW - 40, 10), '#ffffff', 70)

    return [Layer(1.0, slot, 'mail_slot', blur=0), Layer(0.99, item, 'mail_item', blur=0), Layer(0.985, flap, 'mail_flap', blur=0)]


# ============================================================== registry
SETS = {'porch_doorbell': porch_doorbell, 'porch_peephole': porch_peephole, 'street_wide': street_wide,
        'car_backseat_window': car_backseat_window, 'hallway': hallway, 'kitchen': kitchen,
        'living_room_window': living_room_window, 'mother_exterior': mother_exterior, 'mother_room': mother_room}


def build(name, **kw):
    """build('hallway', police=False) -> SetPiece; build('insert:licence', ...) -> insert composition."""
    if name.startswith('insert:'): return insert(name.split(':', 1)[1], **kw)
    return SETS[name](**kw)


# ######################################################################################################################
# DELIVERY FILM: "If A Delivery Driver Rings Your Doorbell At 3 AM... DON'T SIGN FOR IT"
# The police film's world (house 144, porch, street, doorbell / peephole views, hallway, their lighting) re-dressed for
# 3:07 AM: the NIGHTLINE DELIVERY van with blinking amber hazards replaces the patrol car (amber spill replaces the
# red / blue), the tall taped box, the hall with the stairs, upstairs, Lily's room, the side of the house, the memory
# (21 years ago), sunrise at 6:12, inserts and the delivery-app screens on the police phone UI. See SETS.md.
# ######################################################################################################################
from engine import post as _epost
from engine.post import Grade
from engine.core import wrap

# grades used by the delivery sets (registered by name so the director can say grade='dawn' / 'memory')
_epost.GRADES.setdefault('dawn', dict(exposure=0.45, contrast=1.02, pivot=0.25, gamma=1.06, sat=1.0, wb=(1.1, 1.0, 0.88),
                                     floor='#0e0a10', bloom=0.7, bloom_thr=234, vignette=0.42, grain=0.5, shoulder=0.5))
_epost.GRADES.setdefault('memory', dict(exposure=0.05, contrast=0.94, pivot=0.25, gamma=1.02, sat=0.3, mono=0.4, tint='#e2caa2',
                                       wb=(1.06, 1.0, 0.9), floor='#15110d', bloom=0.6, bloom_thr=236, vignette=0.3,
                                       grain=1.2, soft=1.2, shoulder=0.5))
_epost.GRADES.setdefault('nightlight', dict(contrast=1.0, pivot=0.25, gamma=0.98, sat=0.95, wb=(0.95, 0.98, 1.1), floor='#0a0b16',
                                           bloom=0.7, bloom_thr=234, vignette=0.4, grain=0.6, shoulder=0.5))

NL_NAVY, NL_AMBER, AMBER = '#26324c', '#cf8f2c', '#ffa31f'
TAPE, TAPE_HI, KRAFT, KRAFT_SH = '#8c5a2a', '#e0a564', '#b08155', '#6e4a2c'


def WINDOWS_3AM(i):
    """Houses across at 3 AM: every window dark except one dim bedroom (somebody else is awake)."""
    return (0.0, 0.0, 0.42 if i == 3 else 0.0, 0.0)


# ============================================================== hazard flashers
def hazard(t, rate=1.25, t_on=None, t_off=None, duty=0.48):
    """Van hazard flashers -> amber 0..1 at time t: a relay blink at `rate` Hz (duty = on fraction), incandescent attack
    ~30 ms and decay ~70 ms. t_on / t_off switch them on / off (the phase restarts at t_on, so the first flash lands on it)."""
    if t_on is not None and t < t_on: return 0.0
    base = t_on if t_on is not None else 0.0
    P = 1.0 / rate
    if t_off is not None and t >= t_off:
        u0 = (t_off - base) % P; on = duty * P
        lvl = (1.0 - math.exp(-u0 / 0.03)) if u0 < on else 0.0
        return lvl * math.exp(-(t - t_off) / 0.07)
    u = (t - base) % P
    on = duty * P
    if u < on: return 1.0 - math.exp(-u / 0.03)
    return (1.0 - math.exp(-on / 0.03)) * math.exp(-(u - on) / 0.07)


def hazard_ticks(t0, t1, rate=1.25, t_on=None, t_off=None, duty=0.48):
    """Relay tick times of the flasher between t0 and t1 -> [(t, 'on' | 'off')] (SFX: the hazard light ticks)."""
    base = t_on if t_on is not None else 0.0
    P = 1.0 / rate
    k = math.floor((t0 - base) / P) - 1
    out = []
    while base + k * P <= t1:
        a = base + k * P
        for tt, kind in ((a, 'on'), (a + duty * P, 'off')):
            if t0 <= tt < t1 and (t_on is None or tt >= t_on) and (t_off is None or tt < t_off): out.append((round(tt, 3), kind))
        k += 1
    return out


def _hazard_fn(hz):
    """hazard param -> f(t) -> 0..1. True = blinking from t=0, dict(rate, t_on, t_off, duty, strength), a callable, or
    False / None = off."""
    if not hz: return lambda t: 0.0
    if callable(hz): return hz
    p = dict(rate=1.25, t_on=None, t_off=None, duty=0.48, strength=1.0)
    if isinstance(hz, dict): p.update(hz)
    return lambda t: p['strength'] * hazard(t, p['rate'], p['t_on'], p['t_off'], p['duty'])


def _spill_one(depth, draw_geom, key, bounds, fn, k=0.5, name='spill', c=AMBER):
    """One cached light-spill layer whose alpha follows fn(t) (skipped entirely while the light is off)."""
    def d(pen, t): draw_geom(pen, c)
    return [Layer(depth, d, name, cache=key, bounds=bounds, alpha=lambda t: k * fn(t), blur=0)]


def _amber_pool(pen, x, y, s, hz, facing=1):
    """Amber light on the road under the van's front and rear corner flashers."""
    if hz <= 0.03: return
    F = 1 if facing > 0 else -1
    for lx in (2.95, -2.95):
        cx = x + F * lx * s
        pen.radial(None, cx, y, min(2.6 * s, 420.0), [(0, AMBER, 130 * hz), (0.45, AMBER, 40 * hz), (1, AMBER, 0)], sy=0.16, clip=False)


# ============================================================== the NIGHTLINE DELIVERY van
VAN_LEN = 6.0                      # body length in metres (high-roof panel van, 2.55 m tall)
_VAN_S = 200.0                     # sprite drawn at 200 px per metre


def _nl_logo(cv, pen, x, y, s, a=255, fade=0.0, tag=True, dark=NL_NAVY, moon=NL_AMBER):
    """NIGHTLINE DELIVERY wordmark: crescent moon cradling a small parcel + the name. (x, y) = left end of the baseline of
    'NIGHTLINE', s = cap height in design px. fade 0..1 washes it toward the van white. Returns the width."""
    k = 1.0 - 0.45 * fade
    mx, my, mr = x + s * 0.72, y - s * 0.6, s * 0.86
    cres = minus(oval(mx, my, mr), oval(mx + mr * 0.42, my - mr * 0.2, mr * 0.8))
    pen.fill(cres, moon, a * k)
    px_, py_, pw_ = mx + mr * 0.12, my + mr * 0.12, mr * 0.56                                     # the parcel it cradles
    pen.fill(rrect(px_, py_ - pw_ * 0.7, pw_, pw_ * 0.7, mr * 0.05), moon, a * k * 0.85)
    pen.seg((px_ + pw_ * 0.5, py_ - pw_ * 0.7), (px_ + pw_ * 0.5, py_), max(1.0, mr * 0.08), dark, a * k)
    tx = x + s * 1.85
    w = text(cv, 'NIGHTLINE', tx, y, 900, s * 1.32, dark, a * k, 0.04, 'left')
    pen.fill(rect(tx, y + s * 0.18, w, s * 0.09), moon, a * k)
    text(cv, 'DELIVERY', tx + w, y + s * 0.82, 800, s * 0.52, dark, a * k, 0.42, 'right')
    if tag: text(cv, 'RETURNS  •  EXCHANGES  •  24 HR', tx + w, y + s * 1.42, 700, s * 0.26, dark, a * k * 0.8, 0.22, 'right')
    return tx + w - x


def _van_profile(s):
    def P(a, b): return (a * s, -b * s)
    pts = [(-2.95, 0.33), (-3.0, 0.42), (-3.0, 0.66), (-2.97, 0.76), (-2.95, 1.06), (-2.86, 1.15), (-2.24, 1.31), (-1.68, 2.26),
           (-1.55, 2.47), (-1.35, 2.54), (2.82, 2.55), (2.94, 2.48), (2.97, 0.5), (3.0, 0.38), (2.97, 0.3), (-2.9, 0.3)]
    body = smooth([P(*q) for q in pts], True, 0.12)
    for wx in (-1.92, 1.8):
        body = minus(body, oval(*P(wx, 0.36), 0.5 * s))
    return body


def _van_body(pen, s, facing, driver):
    """Static artwork of the van (white high-roof panel van, faded NIGHTLINE DELIVERY lettering, grime, rust): one sprite."""
    cv = pen.cv
    cv.save()
    if facing > 0: cv.scale(-1, 1)
    lw = max(1.2, 0.035 * s)

    def P(a, b): return (a * s, -b * s)
    body = _van_profile(s)
    pen.linear(body, 0, -2.55 * s, 0, -0.3 * s, ['#c3c0b6', '#b2aea2', '#8f8a7c'])
    cv.save(); cv.clipPath(body, skia.ClipOp.kIntersect, True)
    pen.linear(rect(-3.1 * s, -2.6 * s, 6.2 * s, 0.14 * s), 0, -2.6 * s, 0, -2.46 * s, ['#8a8679', '#b5b1a5'])   # roof edge
    pen.linear(rect(-3.1 * s, -2.6 * s, 6.2 * s, 1.0 * s), 0, -2.6 * s, 0, -1.6 * s, [(0, '#0a0e1c', 60), (1, '#0a0e1c', 0)])
    # beltline crease + shadow
    pen.fill(rect(-2.9 * s, -1.06 * s, 5.85 * s, 0.035 * s), '#ffffff', 90)
    pen.fill(rect(-2.9 * s, -1.02 * s, 5.85 * s, 0.05 * s), '#6a665c', 70)
    # the logo (faded, chipped) across the sliding door and the cargo panel
    cvt = cv; cvt.save()
    if facing > 0: cvt.scale(-1, 1)
    fx = -1 if facing > 0 else 1
    lx0 = (-0.4 if fx > 0 else -2.72) * s
    _nl_logo(cvt, pen, lx0, -1.56 * s, 0.29 * s, 200, 0.25)
    cvt.restore()
    rng = np.random.default_rng(11)
    for _ in range(90):                                                      # chipped paint over the letters
        cx_, cy_ = rng.uniform(-0.45, 2.8), rng.uniform(1.42, 2.05)
        r_ = rng.uniform(0.008, 0.03)
        pen.fill(oval(*P(cx_, cy_), r_ * s, r_ * s * rng.uniform(0.5, 1.0)), mix('#c3c0b6', '#b2aea2', (2.55 - cy_) / 1.25), 225)
    pen.fill(rect(-0.6 * s, -2.2 * s, 3.6 * s, 1.3 * s), '#bdb9ae', 36)
    # grime along the bottom, splash behind the wheels, rust
    pen.linear(rect(-3.1 * s, -1.0 * s, 6.2 * s, 0.75 * s), 0, -1.0 * s, 0, -0.3 * s, [(0, '#4a3d2e', 0), (0.55, '#4a3d2e', 70), (1, '#3a2e22', 170)])
    for wx in (-1.92, 1.8):
        pen.radial(None, *P(wx + 0.62, 0.62), 0.55 * s, [(0, '#3a2e22', 120), (1, '#3a2e22', 0)], sy=0.7, clip=False)
        pen.radial(None, *P(wx, 0.86), 0.32 * s, [(0, '#6a3c20', 90), (1, '#6a3c20', 0)], sy=0.5, clip=False)
    for k in range(26):                                                      # rust drips from the door bottoms / sills
        rx = rng.uniform(-2.0, 2.85); ry = 0.47 if -0.53 < rx < 0.86 else rng.uniform(0.42, 0.52)
        ln = rng.uniform(0.05, 0.2)
        pen.line(poly([P(rx, ry), P(rx + rng.uniform(-0.01, 0.01), ry - ln)], False), max(0.8, rng.uniform(0.006, 0.014) * s),
                 '#6a3a1c', rng.uniform(70, 140))
    for (rx, ry) in ((-0.2, 0.44), (2.55, 0.5), (-2.35, 0.9)):
        pen.fill(_blob(*P(rx, ry), 0.09 * s, 0.025 * s, 9, int(rx * 10) + 50, 0.4), '#6a3a1c', 110)
    cv.restore()
    # panel seams
    sc = '#6e6a60'
    cab = poly([P(-2.05, 0.42), P(-2.05, 1.36), P(-1.6, 2.24), P(-0.62, 2.24), P(-0.62, 0.42)])
    pen.line(cab, lw * 0.6, sc, 220)
    pen.line(rrect(-0.53 * s, -2.27 * s, 1.4 * s, 1.85 * s, 0.05 * s), lw * 0.6, sc, 220)             # sliding door
    pen.seg(P(0.87, 1.52), P(2.75, 1.52), lw * 0.55, '#5a564e', 200)                                   # its track
    pen.seg(P(2.88, 0.46), P(2.88, 2.48), lw * 0.5, sc, 180)
    pen.seg(P(-2.05, 0.95), P(-2.86, 1.12), lw * 0.5, sc, 160)                                          # hood line
    # windshield sliver, door window, dash glow, the driver (or his empty seat)
    pen.fill(poly([P(-2.22, 1.3), P(-1.66, 2.26), P(-1.55, 2.26), P(-2.06, 1.37)]), '#141a26')
    win = poly([P(-1.95, 1.44), P(-1.53, 2.13), P(-0.74, 2.13), P(-0.74, 1.44)])
    pen.linear(win, 0, -2.13 * s, 0, -1.44 * s, ['#222c40', '#0b0e15'])
    cv.save(); cv.clipPath(win, skia.ClipOp.kIntersect, True)
    pen.radial(None, *P(-1.7, 1.44), 0.5 * s, [(0, '#7aa08a', 90), (1, '#7aa08a', 0)], sy=0.5, clip=False)    # dash glow
    if driver:
        hx, hy = -1.12, 1.84
        sil = union(oval(*P(hx, hy), 0.13 * s, 0.16 * s), rrect(*P(hx - 0.3, 1.66), 0.62 * s, 0.4 * s, 0.12 * s))
        cap = union(rrect(*P(hx - 0.15, 2.02), 0.3 * s, 0.12 * s, 0.05 * s), rrect(*P(hx - 0.3, 1.94), 0.24 * s, 0.05 * s, 0.02 * s))
        pen.fill(union(sil, cap), '#030305', 250)
        pen.fill(oval(*P(hx - 0.06, 1.86), 0.025 * s, 0.012 * s), '#d8e0e8', 40)                      # a glint where an eye is
    else:
        pen.fill(rrect(*P(-1.22, 1.98), 0.26 * s, 0.24 * s, 0.07 * s), '#07080b', 230)                 # empty headrest
        pen.fill(rrect(*P(-1.32, 1.72), 0.44 * s, 0.3 * s, 0.08 * s), '#07080b', 230)
    pen.fill(poly([P(-1.9, 1.44), P(-1.7, 1.44), P(-1.2, 2.13), P(-1.4, 2.13)]), '#9fb0d0', 34)        # glass streaks
    pen.fill(poly([P(-1.1, 1.44), P(-1.03, 1.44), P(-0.75, 1.85), P(-0.75, 1.95)]), '#9fb0d0', 24)
    cv.restore()
    pen.line(win, lw * 0.8, '#05060a')
    # handles, mirror, fuel door, step, bumpers, lamp housings
    pen.fill(rrect(*P(-0.96, 1.29), 0.2 * s, 0.06 * s, 0.025 * s), '#4a4a48')
    pen.fill(rrect(*P(-0.47, 1.34), 0.16 * s, 0.06 * s, 0.025 * s), '#4a4a48')
    pen.seg(P(-2.02, 1.52), P(-2.22, 1.58), max(1.5, 0.04 * s), '#1e2024')
    pen.shape(rrect(*P(-2.34, 1.88), 0.2 * s, 0.42 * s, 0.05 * s), '#24262b', lw * 0.6)
    pen.line(oval(*P(1.35, 0.98), 0.09 * s), lw * 0.5, sc, 200)
    pen.fill(rect(*P(-0.5, 0.36), 1.36 * s, 0.07 * s), '#1a1b1e')
    pen.shape(rrect(*P(-3.04, 0.62), 0.42 * s, 0.32 * s, 0.06 * s), '#2e3034', lw * 0.6)
    pen.shape(rrect(*P(2.72, 0.5), 0.33 * s, 0.22 * s, 0.05 * s), '#2e3034', lw * 0.6)
    pen.line(body, lw, LINE)
    for wx in (-1.92, 1.8):                                                  # dark wheel wells (wheels are live)
        pen.fill(oval(*P(wx, 0.36), 0.49 * s), '#050607')
    cv.restore()


def _van_lamps(s):
    """Lamp lenses in van-local metres: name -> (x0, y0, x1, y1)."""
    return {'head': (-3.0, 0.82, -2.88, 1.02), 'f_amber': (-3.0, 0.68, -2.9, 0.8), 'f_side': (-2.82, 0.74, -2.62, 0.8),
            'r_red': (2.9, 1.12, 2.99, 1.5), 'r_amber': (2.9, 0.86, 2.99, 1.12), 'r_white': (2.9, 0.62, 2.99, 0.86),
            'r_side': (2.66, 0.6, 2.84, 0.66)}


def delivery_van(pen, x, y, length, t=0.0, facing=1, wheel=0.0, bounce=0.0, pitch=0.0, hz=0.0, head=False, brake=False,
                 driver=True, door=0.0, dash=1.0):
    """The NIGHTLINE DELIVERY van in side view: white high-roof panel van, faded lettering, grime and rust. (x, y) = centre
    between the wheels at ground level, length = body length in design px, facing +1 = nose right. hz = hazard flashers
    0..1 (front / rear corner lamps, side markers + their glow; use hazard(t)); head / brake lamps; driver = silhouette
    with his cap behind the wheel (False: the empty seat); door 0..1 slides the side door back (black cargo hold). The
    body is a cached sprite; wheels, lamps and the door are live (~4 ms at 2560). Cab clearance lamps glow steadily."""
    s = length / VAN_LEN
    cv = pen.cv
    F = 1 if facing > 0 else -1          # +1 = nose right
    M = -F                               # van-local x (nose at -x) -> screen x
    pen.radial(None, x, y + 0.04 * s, 3.5 * s, [(0, '#000000', 190), (0.75, '#000000', 120), (1, '#000000', 0)], sy=0.09, clip=False)
    cv.save(); cv.translate(x, y + bounce)
    prot = (pitch if facing > 0 else -pitch) if pitch else 0.0
    if prot: cv.rotate(round(prot / 0.25) * 0.25)
    key = ('van', facing, bool(driver))
    bnd = (-3.25 * _VAN_S, -2.75 * _VAN_S, 3.25 * _VAN_S, 0.1 * _VAN_S)

    def body_fn(p): _van_body(p, _VAN_S, facing, bool(driver))
    _sprite(pen, key, body_fn, bnd, scale=s / _VAN_S)
    if door > 0.01:                                                          # sliding door rolls back along its track
        dx = M * clamp(door) * 1.32 * s
        xa, xb = sorted((M * -0.52 * s, M * 0.86 * s))
        op = rect(xa, -2.27 * s, xb - xa, 1.86 * s)
        pen.fill(op, '#020203')
        pen.linear(op, 0, -2.27 * s, 0, -0.41 * s, [(0, '#1a1410', 120), (0.7, '#000000', 0), (1, '#2a2018', 90)])
        pen.seg((xa + 0.25 * (xb - xa), -2.2 * s), (xa + 0.3 * (xb - xa), -0.6 * s), max(1.0, 0.03 * s), '#16120e', 255)   # a strap
        cv.save(); cv.clipPath(moved(op, dx, 0), skia.ClipOp.kIntersect, True); cv.translate(dx, 0)
        _sprite(pen, key, body_fn, bnd, scale=s / _VAN_S)
        cv.restore()
        pen.line(moved(op, dx, 0), max(1.2, 0.035 * s), LINE)
    if facing > 0: cv.scale(-1, 1)
    lw = max(1.2, 0.035 * s)

    def R(b): return rrect(b[0] * s, -b[3] * s, (b[2] - b[0]) * s, (b[3] - b[1]) * s, 0.02 * s)
    lm = _van_lamps(s)
    pen.fill(R(lm['head']), mix('#8a8e94', '#fff8ee', 1.0 if head else 0.0))
    pen.fill(R(lm['r_white']), '#c8c8c4' if not head else '#e8e8e4')
    pen.fill(R(lm['r_red']), '#ff3a2a' if brake else '#6a1410')
    for n in ('f_amber', 'r_amber', 'f_side', 'r_side'):
        pen.fill(R(lm[n]), mix('#6a3e0e', '#ffd27a', hz))
        if hz > 0.5: pen.fill(R(lm[n]), '#fff4d8', 255 * (hz - 0.5) * 2 * 0.8)
        pen.line(R(lm[n]), lw * 0.4, LINE, 200)
    for k in range(3):                                                       # cab clearance lamps (steady)
        pen.fill(rrect((-1.4 + k * 0.17) * s, -2.6 * s, 0.09 * s, 0.05 * s, 0.02 * s), '#ffc060')
    # wheels: steel rims, eight holes turning with the wheel
    for wx in (-1.92, 1.8):
        cx_, cy_ = wx * s, -0.36 * s
        pen.fill(oval(cx_, cy_, 0.38 * s), '#08090b')
        pen.fill(oval(cx_, cy_, 0.24 * s), '#6e7278')
        pen.fill(oval(cx_, cy_, 0.19 * s), '#4e5258')
        for k in range(8):
            a = math.radians(-wheel + k * 45)
            pen.fill(oval(cx_ + math.cos(a) * 0.14 * s, cy_ + math.sin(a) * 0.14 * s, 0.028 * s), '#1a1c20')
        pen.fill(oval(cx_, cy_, 0.07 * s), '#9aa0a6'); pen.fill(oval(cx_ - 0.02 * s, cy_ - 0.02 * s, 0.025 * s), '#d0d4d8')
        pen.line(oval(cx_, cy_, 0.38 * s), lw * 0.8, '#000000')
    if hz > 0.05 and dash:                                                   # the hazard telltale blinking in the dark cab
        pen.fill(poly([(-1.8 * s, -1.5 * s), (-1.74 * s, -1.6 * s), (-1.68 * s, -1.5 * s)]), '#ff5a3a', 200 * hz)
    cv.restore()
    yb = y + bounce
    if hz > 0.03:                                                            # flasher glow (screen space)
        for (lx_, ly_, r1) in ((-2.96, 0.74, 1.0), (2.95, 0.99, 1.0), (-2.72, 0.77, 0.55), (2.75, 0.63, 0.55)):
            gx, gy = x + M * lx_ * s, yb - ly_ * s
            pen.glow(gx, gy, min(0.75 * s * r1, 180.0), '#ffd27a', 210 * hz)
            pen.glow(gx, gy, min(2.6 * s * r1, 420.0), AMBER, 80 * hz)
    for k in range(3):
        gx, gy = x + M * (-1.36 + k * 0.17) * s, yb - 2.58 * s
        pen.glow(gx, gy, min(0.22 * s, 60.0), '#ffb040', 120)
    if head:
        hx_, hy_ = x + F * 2.96 * s, yb - 0.92 * s
        pen.glow(hx_, hy_, 0.6 * s, '#fff1c8', 170)
        L5 = 5.5 * s * F
        beam = poly([(hx_, hy_ - 0.08 * s), (hx_ + L5, hy_ - 0.5 * s), (hx_ + L5, hy_ + 0.75 * s), (hx_, hy_ + 0.1 * s)])
        pen.linear(beam, hx_, 0, hx_ + L5, 0, [(0, '#fff1c8', 110), (0.5, '#fff1c8', 36), (1, '#fff1c8', 0)])
    if brake:
        pen.glow(x - F * 2.95 * s, yb - 1.3 * s, 0.7 * s, '#ff3020', 160)


def _wagon(pen, x, y, length, c='#6a5a44', facing=1):
    """Your parents' 1990s station wagon (memory, 21 years ago): long roof, faux-wood side panel, chrome strip."""
    s = length / 4.9
    cv = pen.cv; cv.save(); cv.translate(x, y)
    if facing > 0: cv.scale(-1, 1)

    def P(a, b): return (a * s, -b * s)
    pen.radial(None, 0, 0.03 * s, 2.8 * s, [(0, '#000000', 170), (1, '#000000', 0)], sy=0.08, clip=False)
    body = smooth([P(-2.45, 0.35), P(-2.48, 0.72), P(-2.1, 0.86), P(-1.0, 0.92), P(-0.55, 1.36), P(2.2, 1.38), P(2.42, 1.3),
                   P(2.46, 0.6), P(2.4, 0.32), P(2.0, 0.3), P(1.8, 0.56), P(1.0, 0.56), P(0.8, 0.3), P(-1.15, 0.3), P(-1.35, 0.56),
                   P(-2.05, 0.56), P(-2.2, 0.3)], True, 0.18)
    pen.fill(body, c)
    pen.linear(inter(body, rect(-2.6 * s, -0.95 * s, 5.2 * s, 0.65 * s)), 0, -0.95 * s, 0, -0.3 * s, [_lighten(c, 0.12), _darken(c, 0.3)])
    wood = inter(body, rect(-1.0 * s, -0.84 * s, 3.42 * s, 0.34 * s))
    pen.fill(wood, '#6a4228'); pen.texture(wood, 'wood', 0.5, 'overlay', 0.8)
    pen.line(wood, max(1.0, 0.02 * s), '#c8b890', 200)
    gl = smooth([P(-0.92, 0.94), P(-0.5, 1.3), P(2.12, 1.31), P(2.3, 1.26), P(2.32, 0.94)], True, 0.12)
    pen.linear(gl, 0, -1.3 * s, 0, -0.94 * s, ['#1e2638', '#090b10'])
    for bx in (0.3, 1.25): pen.seg(P(bx, 0.94), P(bx, 1.31), max(1.5, 0.05 * s), c)
    pen.shade(gl, poly([P(-0.6, 0.94), P(-0.45, 0.94), P(0.2, 1.4), P(0.05, 1.4)]), '#8ea2c8', 40)
    for rx in (0.0, 0.9, 1.8): pen.seg(P(rx - 0.25, 1.42), P(rx + 0.25, 1.42), max(1.0, 0.03 * s), '#a8a8a0')   # roof rack
    pen.seg(P(-0.3, 1.42), P(2.1, 1.42), max(1.0, 0.025 * s), '#8a8a84')
    pen.seg(P(-2.3, 0.62), P(2.4, 0.62), max(1.0, 0.02 * s), '#c8c8c0', 150)
    pen.line(body, max(1.2, 0.03 * s), LINE)
    for wx in (-1.6, 1.4):
        cx_, cy_ = P(wx, 0.32)
        pen.fill(oval(cx_, cy_, 0.31 * s), '#08090b'); pen.fill(oval(cx_, cy_, 0.19 * s), '#8a8c90'); pen.fill(oval(cx_, cy_, 0.07 * s), '#c0c2c6')
    pen.fill(smooth([P(2.36, 0.88), P(2.45, 0.86), P(2.45, 0.66), P(2.36, 0.67)], True, 0.4), '#5a1410')
    pen.fill(smooth([P(-2.42, 0.8), P(-2.2, 0.82), P(-2.2, 0.7), P(-2.44, 0.68)], True, 0.4), '#7a7a72')
    cv.restore()


def _vehicle_spec(vehicle, X, D, van=None, drive_in=None, era='now'):
    """Car dict for _car_layer_draw: vehicle 'van' (+ van options) | 'wagon' | None."""
    if not vehicle: return None
    if vehicle == 'wagon': return dict(kind='wagon', X=X, D=D, facing=1, color='#6a5a44')
    o = dict(van or {})
    d = dict(kind='van', X=X, D=D, facing=o.get('facing', 1), driver=o.get('driver', True), door=o.get('door', 0.0),
             head=o.get('head', False), dash=o.get('dash', 1.0), pool=o.get('pool', True), brake=o.get('brake', False))
    if o.get('drive'): d['drive'] = o['drive']
    elif drive_in: d['drive'] = ('in', drive_in[0], drive_in[1], X - 18.0, X)
    return d


def _delivery_anchors(v, anchors, paths, car_X, box):
    """Delivery-film anchors on the porch views: driver (= officer spots), box spots, van doors and the walk to the van."""
    gy = v.ground
    anchors['driver'] = anchors['officer']; anchors['driver_close'] = anchors['officer_close']
    anchors['box_boots'] = v.anchor(0.58, 1.02, note='the box standing next to his boots')
    anchors['box_door'] = v.anchor(-1.12, 0.48, note='the box against the front door (its street face)')
    anchors['van_cab'] = v.anchor(car_X - 1.4, 4.4, Y=gy, note="beside the van's cab door (curb side)")
    anchors['van_door'] = v.anchor(car_X + 0.2, 4.4, Y=gy, note="at the van's sliding door")
    paths['porch_to_van'] = [anchors['officer'], anchors['steps'], anchors['path_mid'], anchors['gate'], anchors['van_cab']]
    paths['van_to_porch'] = paths['porch_to_van'][::-1]


def _dawn_wash(v, box, houses_D):
    """6:12 AM: low sun from the right raking the houses across (warm), cool shade toward the left."""
    def draw(pen, t):
        x0, y0, x1, y1 = box
        pen.radial(None, x1 - (x1 - x0) * 0.12, v.gy(houses_D) - 2.0 * v.s(houses_D), (x1 - x0) * 0.55,
                   [(0, '#ffcf96', 90), (0.5, '#ffb07a', 34), (1, '#ffb07a', 0)], sy=0.5, clip=False)
        pen.linear(rect(x0, y0, x1 - x0, y1 - y0), x0, 0, x1, 0, [(0, '#3a4a7a', 50), (0.6, '#3a4a7a', 0)])
    return draw


# ============================================================== the box (tall, narrow, wrapped in brown tape)
BOX_W, BOX_D, BOX_H = 0.5, 0.42, 1.6        # metres: almost as tall as the driver
_BAND_Y = (0.1, 0.33, 0.6, 0.86, 1.13, 1.4)  # tape wraps (height of the band centre, m): continuous round all faces


def _tape_band(pen, path_fn, y0, y1, x0, x1, seed=0, cut=None):
    """A strip of glossy brown packing tape between y0..y1 (face-local units) from x0..x1. cut = x of a knife cut."""
    rng = np.random.default_rng(seed)
    dy = (y1 - y0)
    segs = [(x0, x1)] if cut is None else [(x0, cut - dy * 0.06), (cut + dy * 0.06, x1)]
    for (a, b) in segs:
        if b <= a: continue
        band = poly([(a, y0 + dy * rng.uniform(-0.04, 0.04)), (b, y0 + dy * rng.uniform(-0.04, 0.04)), (b, y1), (a, y1)])
        pen.fill(band, TAPE, 215)
        pen.fill(rect(a, y0 + dy * 0.12, b - a, dy * 0.14), TAPE_HI, 60)
        pen.fill(rect(a, y1 - dy * 0.1, b - a, dy * 0.1), '#4a2c12', 70)
        for k in range(int((b - a) / (dy * 1.6)) + 1):                                  # wrinkles
            xx = a + rng.uniform(0, 1) * (b - a)
            pen.seg((xx, y0 + dy * 0.2), (xx + dy * rng.uniform(-0.4, 0.4), y1 - dy * 0.2), max(0.6, dy * 0.04), TAPE_HI, 55)
    if cut is not None:                                                                # curled cut ends
        for sd in (-1, 1):
            cx = cut + sd * dy * 0.06
            pen.fill(smooth([(cx, y0), (cx + sd * dy * 0.35, y0 - dy * 0.25), (cx + sd * dy * 0.5, y0 + dy * 0.5), (cx, y1)], True, 0.6), '#a8743a', 230)


def _ship_label(pen, x, y, w, h, to=None, seed=0, a=255):
    """NIGHTLINE shipping label (w x h, any units): FROM: RETURN, TO: blank line (or `to` in a child's hand), barcode,
    SIGNATURE REQUIRED, WT 0.0 LB, SERVICE: EXCHANGE."""
    cv = pen.cv
    u = w / 100.0
    lab = rrect(x, y, w, h, 1.2 * u)
    pen.shadow(lab, 0.6 * u, 1.0 * u, 1.2 * u, '#000000', 90)
    pen.fill(lab, '#ece8dc', a); pen.texture(lab, 'paper', 0.35, 'overlay', 0.4)
    pen.fill(rect(x, y, w, 16 * u), '#16171c', a)
    cv.save(); cv.translate(x + 3 * u, y + 10 * u)
    _nl_logo(cv, pen, 0, 0, 4.0 * u, a, 0.0, tag=False, dark='#ece8dc', moon=NL_AMBER)
    cv.restore()
    text(cv, 'PRIORITY RETURN', x + w - 3 * u, y + 10 * u, 900, 4.0 * u, NL_AMBER, a, 0.06, 'right')
    yy = y + 24 * u
    _type(cv, 'FROM:', x + 4 * u, yy, 4.2 * u, '#3a3a3a', a, 'mono_b')
    text(cv, 'RETURN', x + 20 * u, yy + 0.4 * u, 900, 6.4 * u, '#111111', a, 0.08, 'left')
    yy += 13 * u
    pen.seg((x + 3 * u, yy - 6 * u), (x + w - 3 * u, yy - 6 * u), 0.35 * u, '#5a5a5a', a)
    _type(cv, 'TO:', x + 4 * u, yy + 3 * u, 4.2 * u, '#3a3a3a', a, 'mono_b')
    pen.seg((x + 15 * u, yy + 4 * u), (x + w - 6 * u, yy + 4 * u), 0.6 * u, '#222222', a)
    pen.seg((x + 15 * u, yy + 12 * u), (x + w - 6 * u, yy + 12 * u), 0.35 * u, '#8a8a8a', a)
    if to: _hand_text(cv, to, x + 18 * u, yy + 2.5 * u, 9.5 * u, '#1d2a6a', a * 0.94, seed=4, slant=-0.1, weight=700, wobble=1.8)
    yy += 20 * u
    _type(cv, 'SERVICE: EXCHANGE   1 OF 1', x + 4 * u, yy, 3.6 * u, '#222222', a, 'mono_b')
    _type(cv, 'WT 0.0 LB', x + w - 4 * u, yy, 3.6 * u, '#222222', a, 'mono_b', 'right')
    yy += 3 * u
    rng = np.random.default_rng(seed + 21)                                            # barcode
    bx = x + 4 * u
    bw_tot = w * 0.62
    while bx < x + 4 * u + bw_tot:
        ww = rng.choice([0.5, 0.9, 1.4]) * u
        if rng.uniform() < 0.62: pen.fill(rect(bx, yy, ww, 17 * u), '#111111', a)
        bx += ww + 0.45 * u
    _type(cv, 'NL 0307 2104 1987', x + 4 * u, yy + 21.5 * u, 3.4 * u, '#222222', a, 'mono')
    sr = rect(x + w * 0.7, yy, w * 0.27, 17 * u)
    pen.fill(sr, '#111111', a)
    text(cv, 'SIGNATURE', x + w * 0.835, yy + 7.6 * u, 900, 3.6 * u, '#ece8dc', a, 0.04)
    text(cv, 'REQUIRED', x + w * 0.835, yy + 12.6 * u, 900, 3.6 * u, '#ece8dc', a, 0.04)
    pen.line(lab, 0.3 * u, '#8a8478', a * 0.8)


def _box_face(pen, W, H, face='near', state='taped', label=True, seed=3, shade=0.0, tod='night', dark_edge=None):
    """One face of the box in face-local millimetres (0..W across, 0..H top -> bottom). face: 'near'/'far' (W = width,
    carries the label + SIGNATURE REQUIRED sticker when label=True), 'side' (W = depth: printed crescent, arrows)."""
    cv = pen.cv
    f = rect(0, 0, W, H)
    top, bot = ('#c69a68', '#8a6038') if tod == 'dawn' else ('#b98a58', '#7e5632')
    pen.linear(f, 0, 0, 0, H, [_darken(top, shade), _darken(mix(top, bot, 0.5), shade), _darken(bot, shade)])
    pen.texture(f, 'paper', 0.45, 'overlay', 1.6)
    pen.linear(f, 0, 0, W, 0, [(0, '#000000', 70), (0.12, '#000000', 0), (0.88, '#000000', 0), (1, '#000000', 80)])
    rng = np.random.default_rng(seed)
    for k in range(3):                                                                 # water stains
        sx, sy = rng.uniform(0.15, 0.85) * W, rng.uniform(0.25, 0.95) * H
        r_ = rng.uniform(0.12, 0.25) * W
        st = _blob(sx, sy, r_, r_ * rng.uniform(0.6, 1.2), 10, seed + k, 0.3)
        pen.fill(st, '#5a3a1c', 46); pen.line(st, 4, '#4a2e14', 50)
    pen.linear(rect(0, H * 0.9, W, H * 0.1), 0, H * 0.9, 0, H, [(0, '#3a2410', 0), (1, '#3a2410', 120)])    # damp bottom
    ink = '#1e1a16'
    if face == 'side':
        cx, cy, r_ = W * 0.5, H * 0.42, W * 0.28                                       # faded crescent stamp
        pen.fill(minus(oval(cx, cy, r_), oval(cx + r_ * 0.42, cy - r_ * 0.18, r_ * 0.82)), ink, 70)
        text(cv, 'NIGHTLINE', cx, cy + r_ * 1.5, 900, W * 0.11, ink, 70, 0.08)
        for k, ax in enumerate((W * 0.3, W * 0.7)):                                   # THIS SIDE UP arrows
            pen.fill(poly([(ax, H * 0.05), (ax + 22, H * 0.05 + 34), (ax + 8, H * 0.05 + 34), (ax + 8, H * 0.05 + 80),
                           (ax - 8, H * 0.05 + 80), (ax - 8, H * 0.05 + 34), (ax - 22, H * 0.05 + 34)]), ink, 120)
        text(cv, 'THIS SIDE UP', W * 0.5, H * 0.05 + 112, 800, W * 0.07, ink, 110, 0.08)
        text(cv, 'KEEP UPRIGHT  •  DO NOT OPEN', W * 0.5, H * 0.66, 800, W * 0.045, ink, 90, 0.06)
        # crossed straps over the wraps
        for (a, b) in (((0, H * 0.2), (W, H * 0.48)), ((0, H * 0.48), (W, H * 0.2))):
            pen.line(poly([a, b], False), 50, TAPE, 190); pen.line(poly([(a[0], a[1] - 18), (b[0], b[1] - 18)], False), 6, TAPE_HI, 60)
    else:
        if label:
            _ship_label(pen, W * 0.5 - 185, H * 0.22, 370, 260, seed=seed)
            stk = rect(W * 0.5 - 150, H * 0.22 + 290, 300, 70)
            pen.fill(stk, '#c0161c', 235); pen.line(stk, 4, '#7a0a0e', 200)
            text(cv, 'SIGNATURE REQUIRED', W * 0.5, H * 0.22 + 336, 900, 30, '#fff4ec', 240, 0.04)
        for ax in (W * 0.2, W * 0.8):
            pen.fill(poly([(ax, 40), (ax + 18, 68), (ax + 7, 68), (ax + 7, 104), (ax - 7, 104), (ax - 7, 68), (ax - 18, 68)]), ink, 120)
    cut = W * 0.5 if state in ('cut', 'open') else None
    for k, yb in enumerate(_BAND_Y):
        yc = H - yb * 1000.0
        _tape_band(pen, None, yc - 26, yc + 26, -2, W + 2, seed + k, cut if face != 'side' else (W * 0.9 if cut else None))
    if face != 'side':                                                                 # vertical seam tape down the middle
        x0, x1 = W * 0.5 - 26, W * 0.5 + 26
        if cut is None:
            pen.fill(rect(x0, -2, x1 - x0, H * 0.24), TAPE, 205); pen.fill(rect(x0 + 6, -2, 8, H * 0.24), TAPE_HI, 50)
        else:
            for sd in (-1, 1):
                pen.fill(rect(W * 0.5 + (sd - 1) * 14 + (6 if sd > 0 else 0), -2, 22, H * 0.24), TAPE, 205)
            pen.seg((W * 0.5, -2), (W * 0.5, H * 0.24), 5, '#1a0e06', 230)
    if dark_edge:                                                                     # falls into shadow toward the lens
        st = [(0, '#05040a', 200), (0.55, '#05040a', 60), (1, '#05040a', 0)]
        if dark_edge == 'right': st = [(0, '#05040a', 0), (0.45, '#05040a', 60), (1, '#05040a', 200)]
        pen.linear(f, 0, 0, W, 0, st)
    pen.linear(f, 0, 0, 0, H, [(0, '#000000', 90), (0.3, '#000000', 0), (0.8, '#000000', 0), (1, '#000000', 70)])
    pen.line(f, 5, '#3a2814', 220)


def _face_matrix(W, H, tl, tr, br, bl):
    m = skia.Matrix()
    m.setPolyToPoly([skia.Point(0, 0), skia.Point(W, 0), skia.Point(W, H), skia.Point(0, H)],
                    [skia.Point(*tl), skia.Point(*tr), skia.Point(*br), skia.Point(*bl)])
    return m


def _draw_face(pen, W, H, corners, fn):
    cv = pen.cv
    cv.save(); cv.concat(_face_matrix(W, H, *corners)); fn(pen); cv.restore()


def _box3d(pen, v, X, Dn, w=BOX_W, d=BOX_D, h=BOX_H, state='taped', label='near', seed=3, tod='night', cover=WIDE, keys=False,
           near_shade=0.0):
    """The box standing on the floor (Y = 0) at lateral X, near face at depth Dn, in true perspective (faces mapped with
    a projective matrix). label = which face carries the shipping label ('near' toward the camera, 'far' toward the
    street). state 'taped' | 'cut' (knife cut down the seam) | 'open' (flaps up, cut tape hanging)."""
    X0, X1, Db = X - w / 2, X + w / 2, Dn + d
    Wm, Dm, Hm = w * 1000, d * 1000, h * 1000
    p = v.p
    gy = 0.0
    sh = v.quad([(X0 - 0.06, gy, Dn - 0.05), (X1 + 0.06, gy, Dn - 0.05), (X1 + 0.08, gy, Db + 0.08), (X0 - 0.08, gy, Db + 0.08)])
    pen.fill(sh, '#000000', 150, blur=6)
    L = 0.24 * h / BOX_H * (d / BOX_D)
    th = math.radians(28)
    def flap(edge, out):                                     # edge: two (X, D) hinge points; out: (dX, dD) unit outward
        (xa, da), (xb, db) = edge
        ox, od = out
        q = [(xa, h, da), (xb, h, db), (xb + ox * L * math.sin(th), h + L * math.cos(th), db + od * L * math.sin(th)),
             (xa + ox * L * math.sin(th), h + L * math.cos(th), da + od * L * math.sin(th))]
        return v.quad(q)
    def flap_fill(path, k=0.0):
        pen.fill(path, _darken('#a8784a', 0.25 + k)); pen.line(path, 3, '#3a2814', 200)
    if state == 'open':
        flap_fill(flap(((X0, Db), (X1, Db)), (0, 1)), 0.15)
        flap_fill(flap(((X0, Dn), (X0, Db)), (-1, 0)), 0.2)
        flap_fill(flap(((X1, Dn), (X1, Db)), (1, 0)), 0.1)
    def side(Xs):
        if Xs < 0:   # face on the camera's left: front (Dn) edge is further left
            c = (p(Xs, h, Dn), p(Xs, h, Db), p(Xs, gy, Db), p(Xs, gy, Dn))
        else:
            c = (p(Xs, h, Db), p(Xs, h, Dn), p(Xs, gy, Dn), p(Xs, gy, Db))
        return c
    vis_side = X1 if X1 < 0 else (X0 if X0 > 0 else None)
    if vis_side is not None:
        c = side(vis_side)
        de = ('left' if vis_side < 0 else 'right') if Dn < 0.35 else None
        _draw_face(pen, Dm, Hm, c, lambda pp: _box_face(pp, Dm, Hm, 'side', state, False, seed + 1, 0.42 if tod != 'dawn' else 0.2, tod, de))
    nx0, ny0 = p(X0, h, Dn); nx1, ny1 = p(X1, gy, Dn)
    if nx1 > cover[0] and nx0 < cover[2]:
        _draw_face(pen, Wm, Hm, ((nx0, ny0), (nx1, ny0), (nx1, ny1), (nx0, ny1)),
                   lambda pp: _box_face(pp, Wm, Hm, 'near', state, label == 'near', seed, near_shade, tod))
        if near_shade > 0.3:                                 # backlit: a thin rim of porch light down its edges
            for ex in (nx0, nx1):
                pen.seg((ex, ny0 + 6), (ex, ny1 - 4), 3, '#ffcf8f' if tod != 'dawn' else '#ffe6cc', 150 * near_shade)
    if h < v.cam_h:                                          # top face seen from above
        top = v.quad([(X0, h, Dn), (X1, h, Dn), (X1, h, Db), (X0, h, Db)])
        if state == 'open':
            pen.fill(top, '#0c0805')
            inner = v.quad([(X0 + 0.02, h, Dn + 0.02), (X1 - 0.02, h, Dn + 0.02), (X1 - 0.02, h, Db - 0.02), (X0 + 0.02, h, Db - 0.02)])
            pen.linear(inner, 0, v.y(h, Db), 0, v.y(h, Dn), ['#2a1a0c', '#050302'])
        else:
            pen.fill(top, '#9a6c40'); pen.fill(inter(top, v.quad([(X - 0.03, h, Dn), (X + 0.03, h, Dn), (X + 0.03, h, Db), (X - 0.03, h, Db)])), TAPE, 220)
        pen.line(top, 3, '#3a2814', 220)
    if state == 'open':
        flap_fill(flap(((X0, Dn), (X1, Dn)), (0, -1)), 0.0)
        for (xx, dd) in ((X0 + 0.08, Dn), (X1 - 0.1, Dn)):                     # cut tape hanging off the flaps
            a_ = p(xx, h + 0.02, dd); b_ = p(xx + 0.015, h - 0.16, dd - 0.01)
            pen.line(smooth([a_, ((a_[0] + b_[0]) / 2 + 6, (a_[1] + b_[1]) / 2), b_], False), max(3, 0.05 * v.s(dd)), TAPE, 220)
    # porch-lamp / dawn light falloff over the whole box
    bb = _ubox(*[(min(q[0] for q in c_), min(q[1] for q in c_), max(q[0] for q in c_), max(q[1] for q in c_))
                 for c_ in [((nx0, ny0), (nx1, ny1))] + ([side(vis_side)] if vis_side is not None else [])])
    return bb


def _box_spec(box):
    """'door' | 'boots' | dict(at='door'|'boots'|(X, Dn), state, knock=f(t), label) -> normalised dict."""
    b = dict(at=box) if isinstance(box, str) else dict(box)
    at = b.get('at', 'door')
    if at == 'door': b.setdefault('X', -1.12); b.setdefault('Dn', 0.06); b.setdefault('label', 'far')
    elif at == 'boots': b.setdefault('X', 0.58); b.setdefault('Dn', 1.02); b.setdefault('label', 'near')
    elif at == 'threshold': b.setdefault('X', -0.18); b.setdefault('Dn', 0.62); b.setdefault('label', 'far'); b.setdefault('shade', 0.72)
    else: b['X'], b['Dn'] = at; b.setdefault('label', 'near')
    b.setdefault('state', 'taped')
    return b


def _box_layers(v, box, tag, tod='night', cover=WIDE, light=None):
    """Layer(s) for the box in a View-based set: the static artwork is one sprite (perspective faces drawn once), the
    knock jolt (box['knock'] = f(t) -> 0..1, a decaying impulse) shoves it a few px and drops a puff of dust."""
    b = _box_spec(box)
    X, Dn = b['X'], b['Dn']
    dep = max(0.2, Dn + (0.4 if Dn < 0.2 else 0.03))
    sh = b.get('shade', 0.0) * (0.55 if tod == 'dawn' else 1.0)
    key = ('box', tag, round(X, 3), round(Dn, 3), b['state'], b['label'], tod, round(sh, 2))
    knock = b.get('knock')
    bounds = [None]

    def art(p_):
        bounds[0] = _box3d(p_, v, X, Dn, state=b['state'], label=b['label'], tod=tod, cover=cover, near_shade=sh)
    # bounds: a dry run of the projection (cheap; no drawing)
    c = [v.p(X - BOX_W / 2, BOX_H + 0.4, Dn), v.p(X + BOX_W / 2, -0.05, Dn), v.p(X - BOX_W / 2, BOX_H + 0.4, Dn + BOX_D),
         v.p(X + BOX_W / 2, -0.05, Dn + BOX_D)]
    bx = (max(cover[0], min(q[0] for q in c) - 60), max(cover[1], min(q[1] for q in c) - 60),
          min(cover[2], max(q[0] for q in c) + 60), min(cover[3] + 400, max(q[1] for q in c) + 60))

    def draw(pen, t):
        k = knock(t) if knock else 0.0
        cv = pen.cv
        if k > 0.01:
            cv.save(); cv.translate(6.0 * k * math.sin(t * 61.0), -4.0 * k)
        _sprite(pen, key, art, bx)
        if k > 0.01:
            cv.restore()
            fx_, fy_ = v.p(X + BOX_W / 2, 0.02, Dn + 0.1)
            pen.radial(None, fx_, fy_, 0.25 * v.s(Dn + 0.1), [(0, '#c8b8a0', 60 * k), (1, '#c8b8a0', 0)], sy=0.4, clip=False)
    return [Layer(dep, draw, 'box')]


def knock_pulse(times, decay=0.18):
    """f(t) -> 0..1: a sharp decaying impulse at each knock time (two, a pause, one more: knock_pulse([t, t+.32, t+1.1]))."""
    ts = sorted(times)
    def f(t):
        i = bisect.bisect_right(ts, t) - 1
        return math.exp(-(t - ts[i]) / decay) if i >= 0 and t - ts[i] < 6 * decay else 0.0
    return f


# ============================================================== hall extras: stairs, key bowl, the door opening
def _hall_stairs_side(pen, v, Xw, Xs, D0, Dn, CH, wall, rise=0.19, run=0.26, Dend=0.3):
    """Staircase along the wall X = Xw (inner edge Xs) rising from the first riser at depth D0 toward the camera (seen
    from the side at eye height: treads nearly edge-on, the sawtooth stringer panel, balusters, handrail, newel post and
    a low under-stair closet door left ajar)."""
    steps = []
    k = 0
    while k < 14:
        Df = D0 - k * run
        if Df <= Dend: break
        steps.append((k, Df, max(Df - run, Dend), (k + 1) * rise)); k += 1
    for (k, Df, Dn_, Y) in steps:                                                       # treads + runner (far -> near)
        pen.fill(v.quad([(Xw, Y, Df), (Xs, Y, Df), (Xs, Y, Dn_), (Xw, Y, Dn_)]), '#4a3220')
        pen.fill(v.quad([(Xw + 0.16, Y + 0.002, Df), (Xs - 0.1, Y + 0.002, Df), (Xs - 0.1, Y + 0.002, Dn_), (Xw + 0.16, Y + 0.002, Dn_)]), '#5a2226')
        pen.line(poly([v.p(Xw, Y, Df), v.p(Xs, Y, Df)], False), max(2.0, 0.012 * v.s(Df)), '#b89a5a', 200)   # brass rod
    pts = [(Xs, 0, D0)]
    for (k, Df, Dn_, Y) in steps: pts += [(Xs, Y, Df), (Xs, Y, Dn_)]
    pts += [(Xs, 0, steps[-1][2])]
    panel = poly([v.p(*q) for q in pts])
    xa, xb = v.x(Xs, D0), v.x(Xs, Dend)
    pen.linear(panel, xa, 0, xb, 0, ['#857c6c', '#5c564c', '#34302a'])
    pen.texture(panel, 'plaster', 0.3, 'overlay', 0.8)
    cv = pen.cv; cv.save(); cv.clipPath(panel, skia.ClipOp.kIntersect, True)
    for (D1, D2) in ((D0 - 0.08, D0 - 0.5), (D0 - 0.6, D0 - 0.82)):                    # panel mouldings
        pen.line(v.quad([(Xs, 0.12, D1), (Xs, 0.32, D1), (Xs, 0.32, D2), (Xs, 0.12, D2)]), max(2.0, 0.008 * v.s(D2)), '#4a453c', 170)
    cd = v.quad([(Xs, 0.0, 1.02), (Xs, 0.62, 1.02), (Xs, 0.62, 0.72), (Xs, 0.0, 0.72)])     # under-stair closet door, ajar
    pen.fill(cd, '#9a917f'); pen.line(cd, max(2.0, 0.01 * v.s(0.72)), '#3a352c', 230)
    pen.line(poly([v.p(Xs, 0.02, 0.735), v.p(Xs, 0.6, 0.735)], False), max(3.0, 0.016 * v.s(0.72)), '#020203', 255)
    kx, ky = v.p(Xs, 0.33, 0.77); pen.fill(oval(kx, ky, 0.018 * v.s(0.77)), '#c9a64a')
    pen.linear(panel, 0, v.y(1.2, 1.0), 0, v.y(0, 1.0), [(0, '#000000', 0), (1, '#000000', 90)])
    cv.restore()
    pen.line(poly([v.p(*q) for q in pts[1:-1]], False), max(3.0, 0.014 * v.s(1.0)), '#a8a090', 230)
    pen.line(panel, max(2.0, 0.008 * v.s(1.0)), LINE, 200)
    # balusters, handrail, newel
    Xb = Xs - 0.04
    def Yh(D): return 0.95 + rise + (D0 - D) * rise / run
    for (k, Df, Dn_, Y) in steps:
        for f in (0.28, 0.72):
            D = Df - (Df - Dn_) * f
            if D <= Dend + 0.02: continue
            a_, b_ = v.p(Xb, Y, D), v.p(Xb, Yh(D), D)
            w = max(2.0, 0.02 * v.s(D))
            pen.seg(a_, b_, w + 3, LINE, 220); pen.seg(a_, b_, w, '#a89f8c')
            pen.seg((a_[0] + w * 0.25, a_[1]), (b_[0] + w * 0.25, b_[1]), w * 0.35, '#8a8272', 200)
    nx0, ny0 = v.p(Xb, 0, D0 + 0.05); s0 = v.s(D0 + 0.05)
    post = rect(nx0 - 0.055 * s0, ny0 - 1.15 * s0, 0.11 * s0, 1.15 * s0)
    pen.fill(post, '#3a2618'); pen.fill(rect(nx0 + 0.015 * s0, ny0 - 1.15 * s0, 0.04 * s0, 1.15 * s0), '#24170e')
    pen.line(post, 3, LINE)
    pen.shape(rrect(nx0 - 0.075 * s0, ny0 - 1.21 * s0, 0.15 * s0, 0.07 * s0, 0.02 * s0), '#4a3020', 3)
    pen.shape(oval(nx0, ny0 - 1.27 * s0, 0.055 * s0), '#4a3020', 3)
    pen.fill(oval(nx0 - 0.018 * s0, ny0 - 1.29 * s0, 0.015 * s0), '#c8a070', 160)
    rail = [v.p(Xb, Yh(D), D) for D in np.linspace(D0, Dend, 12)]
    pen.line(poly(rail, False), max(6.0, 0.06 * v.s(0.6)), LINE)
    pen.line(poly(rail, False), max(4.0, 0.045 * v.s(0.6)), '#4a3020')
    pen.line(poly([(x_, y_ - max(1.5, 0.01 * v.s(0.6))) for x_, y_ in rail], False), max(1.5, 0.01 * v.s(0.6)), '#9a7450', 200)
    # warm lamp light across the panel from the console lamp (right side of the hall)
    pen.radial(None, v.x(Xs, 1.5), v.y(0.9, 1.5), 1.6 * v.s(1.5), [(0, '#ffcf8f', 38), (1, '#ffcf8f', 0)], sy=0.8, clip=False)


def _rusty_keys(pen, x, y, s, rot=0.0, n=3, keychain=True, a=255):
    """Dad's keys: rusted, on a ring, with the keychain you made him in second grade (pony beads spelling DAD on a cord
    and a lopsided clay star). (x, y) = ring centre, s = ring radius in design px."""
    cv = pen.cv
    cv.save(); cv.translate(x, y); cv.rotate(rot)
    k_ = s / 70.0
    cv.scale(k_, k_)
    pen.line(oval(0, 0, 70), 10, '#3a2a1e', a); pen.line(oval(0, 0, 70), 6, '#8a5a3a', a)
    for i in range(n):
        cv.save(); cv.rotate(70 + i * 38); cv.translate(80, 0)
        kp = _key_path(250 - i * 22, i + 4, 'round' if i % 2 else 'square')
        pen.shadow(kp, 5, 8, 8, '#000000', 110)
        pen.linear(kp, 0, -50, 0, 50, ['#9a6a3a', '#6a3e20'], a / 255)
        pen.texture(kp, 'grunge', 0.6, 'multiply', 0.6)
        for j in range(5):
            pen.fill(oval(40 + j * 38, (j % 2 - 0.5) * 10, 8 + 3 * (j % 3)), '#5a2a12', 150 * a / 255)
        pen.line(kp, 3, '#2a1a0e', a)
        cv.restore()
    if keychain:
        cv.save(); cv.rotate(-35)
        pen.line(smooth([(68, 0), (130, 18), (190, 10), (250, 30)], False), 5, '#4a8a6a', a)
        for j, (c, ch) in enumerate((('#e04a4a', 'D'), ('#f0c040', 'A'), ('#4a8ae0', 'D'))):
            bx = 128 + j * 42; by = 15 + 6 * math.sin(j)
            pen.shape(rrect(bx - 18, by - 16, 36, 32, 9), c, 4)
            text(cv, ch, bx, by + 9, 900, 24, '#ffffff', a, 0.0)
        st = poly([(262 + 34 * math.cos(math.radians(90 + q * 36)) * (1 if q % 2 == 0 else 0.45) + 4 * (q == 3),
                    34 + 34 * math.sin(math.radians(90 + q * 36)) * (1 if q % 2 == 0 else 0.45)) for q in range(10)])
        pen.shape(st, '#7aa8d0', 4); pen.fill(oval(258, 28, 5), '#ffffff', 120)
        cv.restore()
    cv.restore()


def _key_bowl_small(pen, kx, ky, s, bowl='house'):
    """The key bowl on the console table as seen in the hall view (glazed ceramic); bowl 'house' | 'dad' | 'empty'."""
    b = smooth([(kx - 0.12 * s, ky - 0.05 * s), (kx + 0.12 * s, ky - 0.05 * s), (kx + 0.08 * s, ky), (kx - 0.08 * s, ky)], True, 0.5)
    pen.shape(b, '#3e5a72', 2)
    pen.fill(oval(kx, ky - 0.05 * s, 0.12 * s, 0.018 * s), '#1e2c38')
    pen.line(oval(kx, ky - 0.05 * s, 0.12 * s, 0.018 * s), 2, '#8aa6bc', 200)
    if bowl == 'dad':
        _rusty_keys(pen, kx - 0.02 * s, ky - 0.06 * s, 0.035 * s, -20, 3, True)
    elif bowl == 'house':
        pen.line(smooth([(kx - 0.03 * s, ky - 0.06 * s), (kx, ky - 0.09 * s), (kx + 0.03 * s, ky - 0.06 * s)], False), 2.5, '#c9c2b4')


class _OffsetView(View):
    """A View whose depths are measured from another plane (e.g. the porch world seen through the hall's doorway: porch
    depth 0 = the door plane, `off` metres from the hall camera)."""

    def __init__(self, base, off):
        View.__init__(self, base.S, base.h, base.cam_h, base.cx, base.ground); self.off = float(off)

    def p(self, X, Y, D): return View.p(self, X, Y, D + self.off)

    def x(self, X, D): return View.x(self, X, D + self.off)

    def y(self, Y, D): return View.y(self, Y, D + self.off)

    def s(self, D): return View.s(self, D + self.off)

    def anchor(self, X, D, Y=0.0, note=''):
        x, y = self.p(X, Y, D)
        return Anchor(x, y, D + self.off, 1.85 * self.S / (D + self.off), note)


def _shift_layers(L, off):
    for l in L:
        if not callable(l.depth): l.depth = l.depth + off; l.ref_depth = l.ref_depth + off
    return L


def _door_leaf_art(dw, dh, s, door_c):
    def art(p_):
        p_.cv.save(); p_.cv.clipRect(skia.Rect.MakeWH(dw, dh))
        _door_front(p_, 0, 0, dw, dh, s, door_c, chain=None, slot=True, peep=True)
        p_.cv.restore()
    return art


def _hall_doorway_layers(v, Db, dx, dy, dw, dh, door_c, th_fn, o, CH):
    """Porch world through the open front door (depths offset by the door distance), the box at the threshold, the door
    leaf swinging in on its hinges (perspective-mapped sprite) and the light spilling in across the hall floor."""
    tod, era = o.get('tod', 'night'), o.get('era', 'now')
    ov = _OffsetView(View(v.S, v.h, v.cam_h, v.cx, ground=-0.72), Db)
    cover = (dx - 460, dy - 380, dx + dw + 460, dy + dh + 260)
    vehicle = o.get('vehicle', 'van'); car_X = o.get('car_X', 2.2)
    car = _vehicle_spec(vehicle, car_X, 4.85, o.get('van'), None, era) if vehicle else None
    hz = _hazard_fn(o.get('hazard', True)) if vehicle == 'van' else None
    tag = 'door_%s_%s_%s' % (tod, era, vehicle)
    wins = o.get('windows', WINDOWS_3AM if (tod == 'night' and era == 'now') else None)
    L = _porch_world(tag, ov, cover, car, police=False, lamps=(-6.0, 7.0),
                     moon=(dx + dw * 0.74, dy + dh * 0.16, 15) if tod == 'night' else None, flick='random' if tod == 'night' else None,
                     moths=4, tree=(-3.4, 3.2), mist=True, chair=False, peephole=True, hazard=hz, tod=tod, windows=wins, floor_near=0.0)
    if o.get('box'):
        bs = o['box'] if isinstance(o['box'], dict) else dict(at=o['box'])
        if bs.get('at') in (None, 'door'): bs = dict(bs, at='threshold')
        L += _box_layers(ov, bs, tag, tod, cover)
    _shift_layers(L, Db)
    if tod == 'dawn':                                    # daylight outside vs the dark hall
        for l in L: l.tint = ('#ffe9da', 0.95)
    s = v.s(Db)
    art = _door_leaf_art(dw, dh, s, door_c)

    def leaf(pen, t):
        th = clamp(th_fn(t))
        ang = math.radians(84.0) * th
        Xh = -0.46; Xf = Xh + 0.92 * math.cos(ang); Dfr = Db - 0.92 * math.sin(ang)
        tl, tr, br, bl = v.p(Xh, 2.05, Db), v.p(Xf, 2.05, Dfr), v.p(Xf, 0, Dfr), v.p(Xh, 0, Db)
        cv = pen.cv
        cv.save(); cv.concat(_face_matrix(dw, dh, tl, tr, br, bl))
        _sprite(pen, ('hall_leaf', door_c, round(s, 2)), art, (0, 0, dw, dh))
        cv.restore()
        q = poly([tl, tr, br, bl])
        if th > 0.01:
            pen.fill(q, '#000000', 110 * th)                                       # turning away from the hall lamp
            e0, e1 = v.p(Xf, 2.05, Dfr), v.p(Xf, 0, Dfr)                           # the door's edge (thickness)
            ex = max(3.0, 0.045 * v.s(Dfr) * math.sin(ang))
            pen.fill(poly([e0, (e0[0] + ex, e0[1]), (e1[0] + ex, e1[1]), e1]), '#2a1810')
        pen.line(q, 3, LINE, 230)

    kind = 'dawn' if tod == 'dawn' else ('memory' if era == 'memory' else 'night')
    lc = {'dawn': '#ffd8bc', 'memory': '#ffd49a', 'night': '#ffcf8f'}[kind]

    def spill(pen, t):
        q = v.quad([(-0.46, 0.002, Db), (0.46, 0.002, Db), (0.95, 0.002, 0.95), (-0.75, 0.002, 0.95)])
        pen.cv.save(); pen.cv.clipPath(q, skia.ClipOp.kIntersect, True)
        pen.radial(None, v.x(0, Db), v.gy(Db), 2.2 * v.s(Db), [(0, lc, 120), (0.5, lc, 50), (1, lc, 0)], sy=0.55, clip=False)
        pen.cv.restore()
        pen.radial(None, v.x(0, Db), v.gy(Db) - 0.9 * v.s(Db), 1.6 * v.s(Db), [(0, lc, 40), (1, lc, 0)], sy=0.9, clip=False)
    L += [Layer(Db - 0.005, leaf, 'door_leaf', blur=0),
          _cl(1.485, spill, 'door_light', _key('hall', 'dspill', kind), FRAME, alpha=lambda t: clamp(th_fn(t) * 1.8), blur=0)]
    return L


# ============================================================== the hall seen from the front door (into the house)
def _stairs_away(pen, v, Xa, Xb, D0, rise=0.19, run=0.26, n=14, tread='#4a3220', runner='#5a2226', riser='#2e2018', upto=None):
    """A flight rising AWAY from the camera between X = Xa..Xb, first riser at depth D0: risers face the camera (lit
    edges), treads seen from above while below the eye. Drawn far -> near."""
    for k in range(n - 1, -1, -1):
        Dk = D0 + k * run; Y0, Y1 = k * rise, (k + 1) * rise
        if Y1 < v.cam_h:
            pen.fill(v.quad([(Xa, Y1, Dk), (Xb, Y1, Dk), (Xb, Y1, Dk + run), (Xa, Y1, Dk + run)]), tread)
            pen.fill(v.quad([(Xa + 0.16, Y1, Dk), (Xb - 0.14, Y1, Dk), (Xb - 0.14, Y1, Dk + run), (Xa + 0.16, Y1, Dk + run)]), runner)
        r = v.quad([(Xa, Y0, Dk), (Xb, Y0, Dk), (Xb, Y1, Dk), (Xa, Y1, Dk)])
        pen.fill(r, riser)
        pen.fill(v.quad([(Xa + 0.16, Y0, Dk - 0.001), (Xb - 0.14, Y0, Dk - 0.001), (Xb - 0.14, Y1, Dk - 0.001), (Xa + 0.16, Y1, Dk - 0.001)]),
                 _darken(runner, 0.25))
        pen.line(poly([v.p(Xa, Y1, Dk), v.p(Xb, Y1, Dk)], False), max(1.5, 0.012 * v.s(Dk)), '#8a6a44', 220)        # nosing
        pen.line(poly([v.p(Xa + 0.16, Y0 + 0.01, Dk), v.p(Xb - 0.14, Y0 + 0.01, Dk)], False), max(1.2, 0.008 * v.s(Dk)), '#b89a5a', 200)


def hall_back(lamp=1.0, bowl='house', kitchen_clock='3:11', hazard=None, flick=None, upstairs=0.0, stairs_light=0.0):
    """The front hall seen from the front door, looking into the house (the way you must NOT turn around): left wall with
    the console table, its lamp, the key bowl and the photograph; the staircase rising away on the right into the dark
    upstairs (banister, runner, under-stair panelling); an archway to the dark living room; at the far end the kitchen
    doorway (moonlit window, the microwave clock glowing `kitchen_clock`). bowl 'house' | 'dad' | 'empty'. hazard = f(t)
    amber flashes on the walls from the van through the transom behind the camera. upstairs = 0..1 light at the top of
    the stairs (mum's door opening). lens None or 'lens', grade 'interior_dim'.
    Anchors: stairs_top, stairs_mid, stairs_low (mum coming down: paths['stairs_down']), hall_end (something standing at
    the far end), table (the bowl), wall_sit (sitting against the left wall)."""
    v = View(560, 470, 1.5)
    HW, CH, Dn, Db = 1.35, 2.5, 0.45, 5.2
    Xs = 0.5                                                  # inner edge of the stairs (right side)
    S0 = 0.9                                                  # first riser depth
    hz = _hazard_fn(hazard) if hazard else (lambda t: 0.0)
    box = FRAME

    def far(pen, t):
        s = v.s(Db)
        wp = v.quad([(-HW, 0, Db), (HW, 0, Db), (HW, CH, Db), (-HW, CH, Db)])
        x0, y0 = v.p(-HW, CH, Db); x1, y1 = v.p(HW, 0, Db)
        hole = v.quad([(-0.85, 0, Db), (0.05, 0, Db), (0.05, 2.05, Db), (-0.85, 2.05, Db)])
        # the kitchen beyond: dark, a moonlit window, the microwave clock
        kx0, ky0 = v.p(-0.85, 2.05, Db); kx1, ky1 = v.p(0.05, 0, Db)
        pen.linear(hole, 0, ky0, 0, ky1, ['#0a0d18', '#05060b'])
        wx, wy = v.p(-0.6, 1.75, Db + 2.2); ww = 0.9 * v.s(Db + 2.2)
        pen.radial(None, wx + ww / 2, wy + ww * 0.4, ww * 1.6, [(0, '#5a74b8', 70), (1, '#5a74b8', 0)], clip=False)
        pen.fill(rect(wx, wy, ww, ww * 0.8), '#2a3a66'); pen.seg((wx + ww / 2, wy), (wx + ww / 2, wy + ww * 0.8), 3, '#0a0d18')
        pen.fill(rect(kx0, v.y(0.9, Db + 2.2), kx1 - kx0, 8), '#14182a')
        cx, cy = v.p(-0.25, 1.35, Db + 2.0)
        pen.fill(rrect(cx - 30, cy - 12, 60, 22, 3), '#06080a')
        text(pen.cv, kitchen_clock, cx, cy + 6, 800, 15, '#5aff9a', 220, 0.12)
        pen.glow(cx, cy, 40, '#3aff8a', 50)
        cv = pen.cv; cv.save(); cv.clipPath(minus(wp, hole), skia.ClipOp.kIntersect, True)
        _wallpaper(pen, wp, (x0, y0, x1, y1), s, '#3b3a48', '#2a2934', 'damask', 160)
        pen.fill(v.quad([(-HW, 0, Db), (HW, 0, Db), (HW, 0.9, Db), (-HW, 0.9, Db)]), '#221f20')
        cv.restore()
        pen.line(hole, max(4, 0.06 * s), '#8a8274'); pen.line(hole, 2, LINE)
        _picture(pen, *v.p(0.35, 1.85, Db), 0.4 * s, 0.5 * s, 'portrait', s=s)

    def walls(pen, t):
        # left wall with the living-room archway; right wall above the stairs; ceiling with the stairwell opening
        lw_ = v.quad([(-HW, 0, Dn), (-HW, CH, Dn), (-HW, CH, Db), (-HW, 0, Db)])
        arch = v.quad([(-HW, 0, 2.7), (-HW, 2.1, 2.7), (-HW, 2.1, 3.7), (-HW, 0, 3.7)])
        _side_wall(pen, v, -HW, Db, Dn, 0, CH, '#3b3a48', '#2a2934', 'dots', 150, wains=0.9, wc='#2a2626')
        pen.fill(arch, '#07080d'); pen.line(arch, max(4, 0.05 * v.s(3.2)), '#8a8274')
        pen.radial(None, *v.p(-HW, 1.0, 3.4), 0.7 * v.s(3.4), [(0, '#3a4a7a', 50), (1, '#3a4a7a', 0)], clip=False)   # moon in the living room
        _side_wall(pen, v, HW, Db, Dn, 0, CH + 3.0, '#34333f', '#262530', 'dots', 140, shade=0.5)
        ceil = v.quad([(-HW, CH, Dn), (Xs, CH, Dn), (Xs, CH, Db), (-HW, CH, Db)])
        pen.linear(ceil, 0, v.y(CH, Dn), 0, v.y(CH, Db), ['#060608', '#16161c'])
        pen.line(poly([v.p(-HW, CH, Dn), v.p(-HW, CH, Db)], False), 6, '#4a4640')
        pen.fill(v.quad([(Xs, CH, Dn), (HW, CH, Dn), (HW, CH, 1.3), (Xs, CH, 1.3)]), '#0c0c10')
        pen.line(poly([v.p(Xs, CH, 1.3), v.p(HW, CH, 1.3)], False), 5, '#4a4640')
        pen.fill(v.quad([(Xs, CH, 1.3), (Xs, CH + 0.25, 1.3), (Xs, CH + 0.25, Db), (Xs, CH, Db)]), '#4a4640')        # gallery edge
        lf = v.quad([(Xs, CH + 1.0, Db), (HW, CH + 1.0, Db), (HW, CH + 3.0, Db), (Xs, CH + 3.0, Db)])
        pen.fill(lf, '#0a0a0e')
        # the upstairs gallery railing over the stairwell
        for D in np.arange(1.45, Db, 0.17):
            a_, b_ = v.p(Xs + 0.02, CH + 0.25, D), v.p(Xs + 0.02, CH + 1.15, D)
            pen.seg(a_, b_, max(2.0, 0.025 * v.s(D)), '#6e6858')
        pen.line(poly([v.p(Xs + 0.02, CH + 1.15, 1.35), v.p(Xs + 0.02, CH + 1.15, Db)], False), max(4.0, 0.05 * v.s(1.4)), '#3a2618')
        # ceiling lamp (off) + smoke detector
        cx, cy = v.p(-0.4, CH, 2.4); s = v.s(2.4)
        pen.shape(oval(cx, cy + 0.03 * s, 0.18 * s, 0.05 * s), '#2a2a30', 2)

    def floor(pen, t):
        _floorboards(pen, v, -HW, Xs, Db, Dn, '#2a1e16', '#33261c')
        _rug(pen, v, -0.85, 0.15, Db - 0.4, Dn + 0.15, '#4a1e22', '#1e0c0e', '#9a7a42')
        pen.fill(v.quad([(-HW, 0, Db), (-HW, 0.12, Db), (-HW, 0.12, Dn), (-HW, 0, Dn)]), '#2e2a28')

    def stairs(pen, t):
        side = [(Xs, 0, S0)]
        for k in range(15):
            Dk = S0 + k * 0.26
            side += [(Xs, (k + 1) * 0.19, Dk), (Xs, (k + 1) * 0.19, Dk + 0.26)]
        side += [(Xs, 0, S0 + 15 * 0.26)]
        panel = poly([v.p(*q) for q in side])
        pen.linear(panel, v.x(Xs, S0), 0, v.x(Xs, Db), 0, ['#8a8272', '#4a453c', '#2a2620'])
        pen.texture(panel, 'plaster', 0.3, 'overlay', 0.8)
        cd = v.quad([(Xs, 0, 2.3), (Xs, 1.15, 2.3), (Xs, 1.15, 2.95), (Xs, 0, 2.95)])              # the closet under the stairs
        pen.fill(cd, '#6a6252'); pen.line(cd, 3, '#2a261e')
        pen.fill(v.quad([(Xs, 0.02, 2.3), (Xs, 1.13, 2.3), (Xs, 1.13, 2.34), (Xs, 0.02, 2.34)]), '#010102')
        pen.fill(oval(*v.p(Xs, 0.55, 2.4), 0.02 * v.s(2.4)), '#c9a64a')
        pen.line(panel, 3, LINE, 200)
        _stairs_away(pen, v, Xs, HW, S0, n=14)
        # balusters + handrail along the inner edge, newel post at the bottom
        def Yh(D): return 0.95 + 0.19 + (D - S0) * 0.19 / 0.26
        for k in range(14):
            for f in (0.3, 0.75):
                D = S0 + k * 0.26 + 0.26 * f
                a_, b_ = v.p(Xs + 0.05, (k + 1) * 0.19, D), v.p(Xs + 0.05, Yh(D), D)
                w = max(2.0, 0.022 * v.s(D))
                pen.seg(a_, b_, w + 2, LINE, 200); pen.seg(a_, b_, w, '#a49c8a')
        rail = [v.p(Xs + 0.05, Yh(D), D) for D in np.linspace(S0 - 0.05, S0 + 14 * 0.26, 10)]
        pen.line(poly(rail, False), max(5.0, 0.05 * v.s(1.4)), LINE); pen.line(poly(rail, False), max(3.5, 0.038 * v.s(1.4)), '#4a3020')
        nx, ny = v.p(Xs + 0.05, 0, S0 - 0.05); s0 = v.s(S0)
        post = rect(nx - 0.055 * s0, ny - 1.15 * s0, 0.11 * s0, 1.15 * s0)
        pen.shape(post, '#3a2618', 3); pen.fill(rect(nx + 0.015 * s0, ny - 1.15 * s0, 0.04 * s0, 1.15 * s0), '#24170e')
        pen.shape(oval(nx, ny - 1.25 * s0, 0.06 * s0), '#4a3020', 3)

    def console(pen, t):
        X, Yt, D0, D1, dep = -HW, 0.8, 0.75, 1.45, 0.36
        top = v.quad([(X, Yt, D0), (X + dep, Yt, D0), (X + dep, Yt, D1), (X, Yt, D1)])
        fr = v.quad([(X + dep, Yt, D0), (X + dep, Yt - 0.12, D0), (X + dep, Yt - 0.12, D1), (X + dep, Yt, D1)])
        pen.fill(top, '#5a3e2a'); pen.texture(top, 'wood', 0.5, 'overlay', 1.2); pen.line(top, 3, LINE)
        pen.fill(fr, '#3a271a'); pen.line(fr, 3, LINE)
        for D in (D0 + 0.03, D1 - 0.03):
            pen.seg(v.p(X + dep - 0.03, Yt - 0.12, D), v.p(X + dep - 0.03, 0, D), max(4, 0.03 * v.s(D)), '#2a1c12')
        kx, ky = v.p(X + 0.18, Yt, 1.2); s = v.s(1.2)
        _key_bowl_small(pen, kx, ky, s * 1.0, bowl)
        P0, P1 = 1.25, 0.85                                                                   # the photograph above
        fr2 = v.quad([(X + 0.01, 1.95, P0), (X + 0.01, 1.95, P1), (X + 0.01, 1.35, P1), (X + 0.01, 1.35, P0)])
        pen.shadow(fr2, -6, 6, 6, '#000000', 120); pen.fill(fr2, '#2a1f18'); pen.line(fr2, 3, LINE)
        inner = v.quad([(X + 0.012, 1.9, P0 - 0.02), (X + 0.012, 1.9, P1 + 0.02), (X + 0.012, 1.4, P1 + 0.02), (X + 0.012, 1.4, P0 - 0.02)])
        b = inner.getBounds(); pen.cv.save(); pen.cv.clipPath(inner, skia.ClipOp.kIntersect, True)
        _photo_content(pen, b.left(), b.top(), b.width(), b.height()); pen.cv.restore()

    lamp_pos = (v.p(-HW + 0.18, 0.8, 1.0), v.s(1.0))

    def lamp_glow(pen, t):
        (x, y), s = lamp_pos
        pen.radial(None, x, y - 0.42 * s, 1.9 * s, [(0, '#ffcf8f', 80), (0.5, '#ffcf8f', 26), (1, '#ffcf8f', 0)], clip=False)
        pen.cone(x, y - 0.33 * s, 0.32 * s, 0.9 * s, 0.4 * s, '#ffd9a0', 60, 0.05 * s)

    def lamp_dyn(pen, t):
        (x, y), s = lamp_pos
        k = lamp * (flicker(t, 9, 0.7) if flick else 1.0)
        _table_lamp(pen, x, y, s, k, glow=False)

    def dyn(pen, t):
        h = hz(t)
        if h > 0.02:                                       # the van's flashers through the transom behind us
            pen.radial(None, v.x(0.4, 2.0), v.y(2.2, 2.0), 900, [(0, AMBER, 60 * h), (1, AMBER, 0)], sy=0.5, clip=False)
        if upstairs > 0.01:
            pen.radial(None, *v.p(0.9, CH + 1.6, 4.6), 1.6 * v.s(4.6), [(0, '#ffd9a0', 90 * upstairs), (1, '#ffd9a0', 0)], clip=False)

    L = [_cl(Db, far, 'far_wall', _key('hb', 'far', kitchen_clock), (v.x(-HW, Db) - 30, v.y(CH + 0.5, Db), v.x(HW, Db) + 30, v.gy(Db) + 20)),
         _cl(3.0, walls, 'walls', _key('hb', 'walls'), box),
         _cl(2.95, floor, 'floor', _key('hb', 'floor'), (box[0], v.gy(Db) - 10, box[2], box[3])),
         _cl(2.0, stairs, 'stairs', _key('hb', 'stairs'), (v.x(Xs, Db) - 40, box[1], box[2], box[3])),
         _cl(1.1, console, 'console', _key('hb', 'console', bowl), (box[0], v.y(2.1, 0.75), v.x(-0.8, 1.5), box[3])),
         _cl(1.05, lamp_glow, 'lamp_glow', _key('hb', 'lglow'), (box[0], box[1], v.x(0.6, 1.0), v.y(-0.2, 1.0)),
             alpha=(lambda t: lamp * (flicker(t, 9, 0.7) if flick else 1.0)), blur=0),
         Layer(1.04, lamp_dyn, 'lamp'),
         Layer(1.0, dyn, 'hall_light', blur=0)]
    _exposure(L, 0.3, ('far_wall', 'walls', 'floor', 'stairs', 'console'))
    a = {'stairs_top': v.anchor(0.92, S0 + 13 * 0.26 + 0.1, Y=14 * 0.19, note='top step'),
         'stairs_mid': v.anchor(0.92, S0 + 7 * 0.26 + 0.1, Y=8 * 0.19), 'stairs_low': v.anchor(0.92, S0 + 2 * 0.26 + 0.1, Y=3 * 0.19),
         'stairs_foot': v.anchor(0.25, S0 - 0.15), 'hall_end': v.anchor(-0.35, Db - 0.35, note='at the far end, in the dark'),
         'table': Anchor(*v.p(-HW + 0.18, 0.8, 1.2), 1.2, 0, note='the key bowl'), 'wall_sit': v.anchor(-1.05, 1.9, note='sitting against the left wall'),
         'arch': v.anchor(-1.1, 3.2, note='in the living-room archway')}
    paths = {'stairs_down': [a['stairs_top'], a['stairs_mid'], a['stairs_low'], a['stairs_foot']]}
    return SetPiece('hall_back', L, a, paths, lens='lens', grade='interior_dim', focus=1.2, dof=2.0, cover=FRAME, info={'view': v, 'hazard': hz})


# ============================================================== upstairs, Lily's room, the side of the house
MOON_GLOW = '#fff0c2'


def _moon_nightlight(pen, x, y, s, k=1.0):
    """Lily's nightlight: a crescent moon with a sleepy face on a little white base. (x, y) = base bottom centre, s = px/m."""
    if k > 0.01:
        pen.glow(x, y - 0.14 * s, 1.6 * s, '#ffe8b0', 70 * k)
        pen.glow(x, y - 0.14 * s, 0.45 * s, MOON_GLOW, 160 * k)
    pen.shape(rrect(x - 0.06 * s, y - 0.03 * s, 0.12 * s, 0.03 * s, 0.01 * s), '#d8d4cc', max(1.0, 0.006 * s))
    cx, cy, r = x, y - 0.14 * s, 0.1 * s
    cres = minus(oval(cx, cy, r), oval(cx + r * 0.5, cy - r * 0.25, r * 0.85))
    pen.fill(cres, mix('#8a8270', '#fff8e4', k)); pen.line(cres, max(1.0, 0.006 * s), '#6a5a3a', 200)
    pen.seg((cx - r * 0.55, cy - r * 0.05), (cx - r * 0.35, cy + r * 0.0), max(1.0, 0.008 * s), '#6a5a3a', 200)          # sleeping eye
    pen.fill(oval(cx - r * 0.45, cy + r * 0.3, r * 0.1), '#f0a0a0', 120 * k + 40)


def _glow_stars(pen, quad_fn, n, seed, a=150):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x, y, r = quad_fn(rng)
        pts = [(x + math.cos(math.radians(-90 + q * 36)) * r * (1 if q % 2 == 0 else 0.45),
                y + math.sin(math.radians(-90 + q * 36)) * r * (1 if q % 2 == 0 else 0.45)) for q in range(10)]
        pen.fill(poly(pts), '#d8f0a8', a)


def _kid_drawing(pen, x, y, w, h, seed=0, kind='family'):
    """Crayon drawing taped to a wall: 'family' (mom and two kids holding hands under a sun, a house, no dad),
    'moon' (a big yellow moon and stars)."""
    pen.fill(rect(x, y, w, h), '#f2ede0'); pen.line(rect(x, y, w, h), max(1.0, w * 0.01), '#9a9484', 200)
    for (tx, ty) in ((x + w * 0.1, y), (x + w * 0.9, y)):
        pen.fill(rect(tx - w * 0.07, ty - h * 0.04, w * 0.14, h * 0.08), '#e8dcb0', 200)
    lw = max(1.0, w * 0.018)
    if kind == 'moon':
        pen.fill(minus(oval(x + w * 0.5, y + h * 0.48, w * 0.28), oval(x + w * 0.62, y + h * 0.4, w * 0.24)), '#f0c838')
        for k in range(5):
            pen.fill(oval(x + w * (0.15 + 0.17 * k), y + h * (0.15 + 0.6 * (k % 2)), w * 0.03), '#4a6ad0')
        return
    pen.line(oval(x + w * 0.85, y + h * 0.17, w * 0.08), lw, '#f0b020'); pen.fill(oval(x + w * 0.85, y + h * 0.17, w * 0.06), '#f8d040')
    pen.line(poly([(x + w * 0.06, y + h * 0.55), (x + w * 0.2, y + h * 0.35), (x + w * 0.34, y + h * 0.55), (x + w * 0.34, y + h * 0.8),
                   (x + w * 0.06, y + h * 0.8)]), lw, '#c83a3a')
    for i, (fx, fh, c) in enumerate(((0.5, 0.42, '#7a3aa8'), (0.66, 0.3, '#2a7ad0'), (0.78, 0.24, '#e05aa0'))):
        hx, hy = x + w * fx, y + h * (0.88 - fh)
        pen.line(oval(hx, hy, w * 0.035), lw, c)
        pen.line(poly([(hx, hy + w * 0.035), (hx, hy + h * fh * 0.55)], False), lw, c)
        pen.line(poly([(hx - w * 0.05, hy + h * fh * 0.3), (hx + w * 0.05, hy + h * fh * 0.3)], False), lw, c)
        pen.line(poly([(hx, hy + h * fh * 0.55), (hx - w * 0.03, y + h * 0.88)], False), lw, c)
        pen.line(poly([(hx, hy + h * fh * 0.55), (hx + w * 0.03, y + h * 0.88)], False), lw, c)
    pen.line(poly([(x + w * 0.04, y + h * 0.9), (x + w * 0.96, y + h * 0.9)], False), lw * 1.4, '#4aa04a')


def _night_out(pen, x, y, w, h, t, hz=0.0, seed=0, house=True, moon=True):
    """What a side window sees at night (flat backdrop, any rect): sky, a bare branch, the neighbour's dark wall, the
    amber flasher glow coming round the front of the house when hz > 0."""
    pen.linear(rect(x, y, w, h), 0, y, 0, y + h, ['#0a1430', '#1a2448', '#24305a'])
    rng = np.random.default_rng(seed)
    for _ in range(int(w * h / 4000) + 3):
        pen.fill(oval(x + rng.uniform(0, w), y + rng.uniform(0, h * 0.5), rng.uniform(0.6, 1.4)), '#dfe6ff', rng.uniform(60, 180))
    if moon: _moon(pen, x + w * 0.78, y + h * 0.16, max(6.0, w * 0.05))
    if house:
        hw = poly([(x - 10, y + h * 0.48), (x + w * 0.62, y + h * 0.3), (x + w * 0.62, y + h + 10), (x - 10, y + h + 10)])
        pen.fill(hw, '#0b0d16'); _siding(pen, hw, x - 10, y + h * 0.3, x + w * 0.62, y + h + 10, max(4.0, h * 0.05), '#000000', 90, '#1a1e2c', 40)
        pen.fill(rect(x + w * 0.2, y + h * 0.62, w * 0.18, h * 0.22), '#05060a'); pen.line(rect(x + w * 0.2, y + h * 0.62, w * 0.18, h * 0.22), 2, '#2a2e3a')
    draw_tree(pen, x + w * 0.9, y + h * 1.2, h * 1.1, t, seed + 61, 1.4, '#04060b', None, 4)
    if hz > 0.02:
        pen.radial(None, x - w * 0.1, y + h * 0.75, w * 0.9, [(0, AMBER, 120 * hz), (0.5, AMBER, 40 * hz), (1, AMBER, 0)], sy=0.8, clip=False)


def upstairs_hall(lily_door=0.07, window_open=True, hall_light=0.0, mom_door=0.0, wind=1.0, hazard=None):
    """The upstairs corridor from the top of the stairs: the stairwell banister on the left, mum's door (left) and the
    bathroom (right, ajar), framed school photos, a runner; at the end of the hall LILY's door (white, wooden pastel
    letters L-I-L-Y, glow stars, a crayon drawing), open a crack (lily_door 0..1 or f(t): hinge on the left, swings into
    her room) with the moon nightlight's glow spilling in a wedge across the floor; opened wide you see into her room:
    the window (open: the curtains moving) on her far wall. hall_light 0..1 (a lamp switched on), mom_door 0..1 light from
    mum's door opening. lens None/'lens', grade 'nightlight' or 'interior_dim'.
    Anchors: lily_door (in front of it), mom_door, top (at the top of the stairs), mid; paths['to_lily']."""
    v = View(560, 470, 1.5)
    HW, CH, Dn, Db = 0.75, 2.4, 0.45, 4.6
    ld = lily_door if callable(lily_door) else (lambda t: float(lily_door))
    hz = _hazard_fn(hazard) if hazard else (lambda t: 0.0)
    box = FRAME
    s = v.s(Db)
    dx0, dy0 = v.p(-0.42, 2.05, Db); dx1, dy1 = v.p(0.42, 0, Db)
    dw, dh = dx1 - dx0, dy1 - dy0

    def room_beyond(pen, t):                              # Lily's room through her doorway (far wall 3 m beyond)
        D2 = Db + 3.0
        q = rect(dx0 - 4, dy0 - 4, dw + 8, dh + 8)
        pen.cv.save(); pen.cv.clipPath(q, skia.ClipOp.kIntersect, True)
        pen.linear(q, 0, dy0, 0, dy1, ['#2a2a48', '#3a3256', '#2a2238'])
        wx0, wy0 = v.p(-0.35, 2.1, D2); wx1, wy1 = v.p(0.55, 0.95, D2)
        _night_out(pen, wx0, wy0, wx1 - wx0, wy1 - wy0, t, hz(t), 5, True, False)
        pen.line(rect(wx0, wy0, wx1 - wx0, wy1 - wy0), 6, '#cfc8d8')
        if not window_open: pen.seg((wx0, (wy0 + wy1) / 2), (wx1, (wy0 + wy1) / 2), 5, '#cfc8d8')
        cw = (wx1 - wx0) * 0.35
        _curtain(pen, wx0 - cw * 0.6, wy0 - 14, cw, (wy1 - wy0) + 60, t * (2.2 if window_open else 0.6), -1, '#8a6aa0', 2.2 * wind if window_open else 0.3, 21, folds=4)
        _curtain(pen, wx1 - cw * 0.4, wy0 - 14, cw, (wy1 - wy0) + 60, t * (2.2 if window_open else 0.6) + 2, 1, '#8a6aa0', 2.2 * wind if window_open else 0.3, 23, folds=4)
        mx, my = v.p(-0.9, 0.62, D2 - 0.4)
        _moon_nightlight(pen, mx, my, v.s(D2 - 0.4), 1.0)
        pen.fill(rect(dx0 - 4, v.gy(D2), dw + 8, dy1 - v.gy(D2) + 8), '#3a2e44')
        pen.radial(None, mx, my, 2.0 * v.s(D2), [(0, MOON_GLOW, 60), (1, MOON_GLOW, 0)], clip=False)
        pen.cv.restore()

    def end_wall(pen, t):
        wp = minus(v.quad([(-HW, 0, Db), (HW, 0, Db), (HW, CH, Db), (-HW, CH, Db)]), rect(dx0, dy0, dw, dh))
        x0, y0 = v.p(-HW, CH, Db); x1, y1 = v.p(HW, 0, Db)
        _wallpaper(pen, wp, (x0, y0, x1, y1), s, '#3c4058', '#2e3248', 'stripe', 120)
        tw = 0.08 * s
        pen.shape(minus(rect(dx0 - tw, dy0 - tw, dw + 2 * tw, dh + tw), rect(dx0, dy0, dw, dh)), '#c8c2b4', 2)

    def lily_leaf(pen, t):
        th = clamp(ld(t)); ang = math.radians(95.0) * th
        Xh = -0.42; Xf = Xh + 0.84 * math.cos(ang); Df_ = Db + 0.84 * math.sin(ang)
        tl, tr, br, bl = v.p(Xh, 2.05, Db), v.p(Xf, 2.05, Df_), v.p(Xf, 0, Df_), v.p(Xh, 0, Db)
        cv = pen.cv
        cv.save(); cv.concat(_face_matrix(dw, dh, tl, tr, br, bl))
        _sprite(pen, ('lily_door', round(s, 2)), lambda p_: _lily_door_face(p_, dw, dh, s), (0, 0, dw, dh))
        cv.restore()
        q = poly([tl, tr, br, bl])
        if th > 0.005:
            pen.fill(q, '#000000', 80 * clamp(th * 3))
            gx = tr[0]                                                            # the lit crack
            pen.fill(poly([tr, (dx1, dy0), (dx1, dy1), br]), MOON_GLOW, 70 * (1 - th) ** 2)
        pen.line(q, 2.5, LINE, 230)

    def wedge(pen, t):                                     # the nightlight's glow across the floor through the gap
        th = clamp(ld(t))
        if th < 0.003: return
        Xf = -0.42 + 0.84 * math.cos(math.radians(95.0) * th)
        w0 = max(0.42 - Xf, 0.07)
        Xf = 0.42 - w0
        gx = v.x(0.42, Db)
        pen.seg((gx - 2, dy0 + 6), (gx - 2, dy1), 4, MOON_GLOW, 200 * min(1.0, th * 12) * (1 - th) + 40)
        q = v.quad([(Xf, 0.002, Db), (0.42, 0.002, Db), (0.42 + w0 * 0.6, 0.002, Db - 2.6), (Xf - w0 * 1.2, 0.002, Db - 2.6)])
        pen.cv.save(); pen.cv.clipPath(q, skia.ClipOp.kIntersect, True)
        pen.radial(None, v.x(0.0, Db), v.gy(Db), 2.4 * v.s(Db), [(0, MOON_GLOW, 140), (0.6, MOON_GLOW, 40), (1, MOON_GLOW, 0)], sy=0.6, clip=False)
        pen.cv.restore()
        pen.radial(None, v.x(0.2, Db), v.y(1.0, Db), 1.2 * s, [(0, MOON_GLOW, 40 * min(1, th * 6)), (1, MOON_GLOW, 0)], clip=False)

    def sides(pen, t):
        _side_wall(pen, v, -HW, Db, 1.7, 0, CH, '#3c4058', '#2e3248', 'stripe', 110, wains=0.0, shade=0.45)
        _side_wall(pen, v, HW, Db, Dn, 0, CH, '#3c4058', '#2e3248', 'stripe', 110, wains=0.0, shade=0.45)
        # stairwell on the left (near): the drop to the hall below, its far wall with a picture
        pen.fill(v.quad([(-HW, 0, 1.7), (-HW, CH, 1.7), (-HW, CH, Dn), (-HW, -3.0, Dn)]), '#06060a')
        sw = v.quad([(-1.9, -2.6, 1.7), (-1.9, CH, 1.7), (-1.9, CH, Dn), (-1.9, -2.6, Dn)])
        pen.linear(sw, v.x(-1.9, 1.7), 0, v.x(-1.9, Dn), 0, ['#1a1c2a', '#0c0d14'])
        _picture(pen, *v.p(-1.9, 1.7, 1.25), 0.35 * v.s(1.25), 0.45 * v.s(1.25), 'landscape', s=v.s(1.25))
        pen.fill(v.quad([(-1.9, -2.6, 1.7), (-1.9, CH, 1.7), (-1.9, CH, Dn), (-1.9, -2.6, Dn)]), '#000000', 110)
        ceil = v.quad([(-HW, CH, Dn), (HW, CH, Dn), (HW, CH, Db), (-HW, CH, Db)])
        pen.linear(ceil, 0, v.y(CH, Dn), 0, v.y(CH, Db), ['#050508', '#14141c'])
        for (X, D0_, D1_, c, gap) in ((-HW, 2.2, 3.0, '#cfc8b8', mom_door), (HW, 1.5, 2.3, '#cfc8b8', -1), (HW, 3.2, 3.8, '#c0b8a8', 0.0)):
            dq = v.quad([(X, 0, D1_), (X, 2.05, D1_), (X, 2.05, D0_), (X, 0, D0_)])
            pen.fill(dq, _darken(c, 0.45)); pen.line(dq, 3, '#24222a')
            for (yy0, yy1) in ((0.15, 0.95), (1.1, 1.9)):
                pen.line(v.quad([(X, yy0, D1_ - 0.12), (X, yy1, D1_ - 0.12), (X, yy1, D0_ + 0.12), (X, yy0, D0_ + 0.12)]), 2, '#2a2830', 150)
            kx, ky = v.p(X, 1.0, D0_ + 0.08); pen.fill(oval(kx, ky, max(3, 0.025 * v.s(D0_))), '#c9a64a')
            if gap == -1:                                                                       # bathroom door ajar: black gap
                pen.fill(v.quad([(X, 0, D1_), (X, 2.05, D1_), (X, 2.05, D1_ - 0.06), (X, 0, D1_ - 0.06)]), '#010102')
        for i, (D, Y) in enumerate(((1.15, 1.55), (1.0, 1.25), (3.55, 1.6))):                   # school photos
            X = HW - 0.01
            fr = v.quad([(X, Y + 0.25, D), (X, Y + 0.25, D - 0.2), (X, Y, D - 0.2), (X, Y, D)])
            pen.fill(fr, '#2a2018'); pen.line(fr, 2, LINE)
            inner = v.quad([(X, Y + 0.22, D - 0.02), (X, Y + 0.22, D - 0.18), (X, Y + 0.03, D - 0.18), (X, Y + 0.03, D - 0.02)])
            pen.fill(inner, '#6a7a9a' if i != 1 else '#8a6a7a')
        sx, sy = v.p(0.0, CH, 2.0); pen.shape(oval(sx, sy + 6, 0.07 * v.s(2.0), 0.025 * v.s(2.0)), '#a8a49c', 2)
        pen.fill(oval(sx + 8, sy + 6, 2.5), '#ff2a2a', 230)

    def floor(pen, t):
        _floorboards(pen, v, -HW, HW, Db, Dn, '#2e2018', '#20160e', 0.12)
        _rug(pen, v, -0.38, 0.38, Db - 0.25, Dn + 0.2, '#2e3a5a', '#141a2a', '#8a7a52')

    def banister(pen, t):
        X = -HW + 0.04
        for D in np.arange(Dn + 0.05, 1.72, 0.12):
            a_, b_ = v.p(X, 0, D), v.p(X, 0.92, D)
            w = max(2.0, 0.025 * v.s(D))
            pen.seg(a_, b_, w + 2, LINE, 220); pen.seg(a_, b_, w, '#8a8272')
        rail = [v.p(X, 0.95, D) for D in (Dn, 1.72)]
        pen.line(poly(rail, False), max(5.0, 0.06 * v.s(0.8)), LINE); pen.line(poly(rail, False), max(3.5, 0.045 * v.s(0.8)), '#3a2618')
        nx, ny = v.p(X, 0, 1.75); s0 = v.s(1.75)
        pen.shape(rect(nx - 0.05 * s0, ny - 1.1 * s0, 0.1 * s0, 1.1 * s0), '#3a2618', 3)
        pen.shape(oval(nx, ny - 1.16 * s0, 0.05 * s0), '#4a3020', 3)

    def lights(pen, t):
        if hall_light > 0.01:
            pen.radial(None, v.x(0, 2.0), v.y(CH, 2.0), 2.4 * v.s(2.0), [(0, '#ffd9a0', 70 * hall_light), (1, '#ffd9a0', 0)], sy=0.9, clip=False)
        if mom_door > 0.01:
            pen.radial(None, *v.p(-HW, 1.0, 2.6), 1.4 * v.s(2.6), [(0, '#ffd9a0', 90 * mom_door), (1, '#ffd9a0', 0)], sy=1.3, clip=False)

    dkey = ('uh', window_open)
    L = [Layer(Db + 3.0, room_beyond, 'lily_room_far', blur=0),
         _cl(Db, end_wall, 'end_wall', _key('uh', 'end'), (v.x(-HW, Db) - 30, v.y(CH, Db) - 30, v.x(HW, Db) + 30, v.gy(Db) + 30)),
         Layer(Db - 0.01, lily_leaf, 'lily_door', blur=0),
         _cl(2.5, sides, 'walls', _key('uh', 'sides'), box),
         _cl(2.45, floor, 'floor', _key('uh', 'floor'), (box[0], v.gy(Db) - 10, box[2], box[3])),
         Layer(2.44, wedge, 'moon_wedge', blur=0),
         _cl(1.0, banister, 'banister', _key('uh', 'ban'), (box[0], box[1], v.x(-0.2, 1.0), box[3])),
         Layer(0.99, lights, 'hall_lights', blur=0)]
    _exposure(L, 0.3, ('end_wall', 'walls', 'floor', 'banister'))
    a = {'lily_door': v.anchor(0.0, Db - 0.45, note="in front of Lily's door"), 'mom_door': v.anchor(-0.4, 2.6),
         'top': v.anchor(0.15, 0.9, note='at the top of the stairs'), 'mid': v.anchor(0.0, 2.6)}
    return SetPiece('upstairs_hall', L, a, {'to_lily': [a['top'], a['mid'], a['lily_door']]}, lens='lens', grade='nightlight', focus=Db,
                    dof=2.0, cover=FRAME, info={'view': v, 'lily_door': ld, 'door_rect': (dx0, dy0, dw, dh)})


def _lily_door_face(pen, w, h, s):
    """Lily's bedroom door (inside face toward the hall): white paint, wooden pastel letters, glow stars, a drawing."""
    leaf = rect(0, 0, w, h)
    pen.linear(leaf, 0, 0, w, 0, ['#d8d2c6', '#c8c2b4', '#b4ae9e'])
    for (py, ph) in ((0.06, 0.38), (0.52, 0.42)):
        pen.line(rect(w * 0.12, h * py, w * 0.76, h * ph), max(1.5, 0.008 * s), '#9a9484', 200)
    for i, (ch, c) in enumerate(zip('LILY', ('#e88aa8', '#8ac0e8', '#f0c860', '#9ad08a'))):
        cx = w * (0.2 + 0.2 * i); cy = h * 0.2 + (i % 2) * h * 0.012
        text(pen.cv, ch, cx, cy, 900, h * 0.075, c, 255, 0.0, 'center', 0.0)
        text(pen.cv, ch, cx, cy, 900, h * 0.075, c, 255)
    _kid_drawing(pen, w * 0.22, h * 0.3, w * 0.56, h * 0.18, 3, 'moon')
    rng = np.random.default_rng(9)
    _glow_stars(pen, lambda r: (w * r.uniform(0.15, 0.85), h * r.uniform(0.52, 0.9), w * r.uniform(0.025, 0.05)), 7, 9, 170)
    pen.radial(oval(w * 0.86, h * 0.5, 0.03 * s), w * 0.85, h * 0.49, 0.04 * s, [(0, '#f0d890'), (1, '#8a6a2a')])
    pen.line(leaf, max(1.5, 0.006 * s), LINE)


def lily_room(view='room', window_open=False, bed='sleeping', curtains=1.0, wind=1.0, hazard=None, nightlight=1.0,
              van=None, van_X=-9.0, drive=None):
    """Lily's bedroom (she is eight). view 'room': from her doorway: the window on the far wall (it faces the side of the
    house) with lavender star curtains, the bed along the left wall under a star quilt (bed 'sleeping' = a small shape
    under the covers, 'empty' = covers thrown back, a dent in the pillow; 'made'), the crescent-moon nightlight on the
    nightstand (the room's key light), glow stars on the ceiling, crayon drawings (mum and two kids, no dad), a stuffed
    rabbit, the heating vent low on the right wall (she heard the knock through it). window_open: the lower sash up, cold
    blue night pouring in, the curtains billowing (wind). hazard = f(t)|True|dict: the van's amber flashes reach her
    window and the curtains. view 'window': at her open window looking out: sill + sash + curtains in the foreground, the
    side yard below, the fence, the neighbour's house, the street at the end of the side yard with the van at the curb
    (hazards; drive=('out', t0, t1, X0, X1) pulls it away with its headlights off). grade 'nightlight'.
    Anchors (room): bed (Lily lying), window (someone leaning out), floor_mid; (window view): yard_below (the driver),
    van."""
    hz = _hazard_fn(hazard) if hazard else (lambda t: 0.0)
    if view == 'window': return _lily_window_view(curtains, wind, hz, van, van_X, drive)
    v = View(600, 470, 1.35)
    HW, CH, Dn, Db = 1.65, 2.4, 0.5, 3.4
    box = FRAME
    s = v.s(Db)
    WX0, WX1, WY0, WY1 = -0.15, 1.05, 0.85, 2.05
    wx0, wy0 = v.p(WX0, WY1, Db); wx1, wy1 = v.p(WX1, WY0, Db)
    nl = v.p(-0.55, 0.62, Db - 0.25)                         # the nightlight on the nightstand

    def outside(pen, t):
        _night_out(pen, wx0 - 40, wy0 - 40, wx1 - wx0 + 80, wy1 - wy0 + 80, t, 0.0, 7, True, True)

    def out_dyn(pen, t):
        h = hz(t)
        if h > 0.02: pen.radial(None, wx0 - 60, wy1 - 30, (wx1 - wx0) * 1.1, [(0, AMBER, 150 * h), (0.5, AMBER, 50 * h), (1, AMBER, 0)], sy=0.9, clip=False)

    def back(pen, t):
        wp = minus(v.quad([(-HW, 0, Db), (HW, 0, Db), (HW, CH, Db), (-HW, CH, Db)]), rect(wx0, wy0, wx1 - wx0, wy1 - wy0))
        x0, y0 = v.p(-HW, CH, Db); x1, y1 = v.p(HW, 0, Db)
        _wallpaper(pen, wp, (x0, y0, x1, y1), s, '#4a4268', '#5a5280', 'floral', 120, '#e8d8a0', seed=11)
        pen.fill(minus(v.quad([(-HW, 0, Db), (HW, 0, Db), (HW, 0.1, Db), (-HW, 0.1, Db)]), rect(0, 0, 0, 0)), '#2a2438')
        pen.line(rect(wx0 - 12, wy0 - 12, wx1 - wx0 + 24, wy1 - wy0 + 24), 22, '#d8d0e0'); pen.line(rect(wx0 - 24, wy0 - 24, wx1 - wx0 + 48, wy1 - wy0 + 48), 3, LINE)
        pen.fill(rect(wx0 - 40, wy1 + 12, wx1 - wx0 + 80, 18), '#d8d0e0'); pen.line(rect(wx0 - 40, wy1 + 12, wx1 - wx0 + 80, 18), 2, LINE)
        if window_open:                                     # lower sash raised: the opening below, the sash pane above
            my = wy0 + (wy1 - wy0) * 0.08
            pen.fill(rect(wx0, wy0, wx1 - wx0, (wy1 - wy0) * 0.5), '#c9d6f0', 22)
            pen.seg((wx0, wy0 + (wy1 - wy0) * 0.5), (wx1, wy0 + (wy1 - wy0) * 0.5), 14, '#d8d0e0')
            pen.seg((wx0, wy0 + (wy1 - wy0) * 0.52), (wx1, wy0 + (wy1 - wy0) * 0.52), 3, LINE)
            pen.seg(((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy0 + (wy1 - wy0) * 0.5), 8, '#d8d0e0')
        else:
            pen.seg((wx0, (wy0 + wy1) / 2), (wx1, (wy0 + wy1) / 2), 12, '#d8d0e0'); pen.seg(((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1), 8, '#d8d0e0')
            pen.fill(poly([(wx0, wy1 - 40), (wx0 + 60, wy1), (wx0 + 140, wy0), (wx0 + 80, wy0)]), '#c9d6f0', 20)
        _kid_drawing(pen, *v.p(-1.35, 1.75, Db), 0.42 * s, 0.32 * s, 1, 'family')
        _kid_drawing(pen, *v.p(1.2, 1.6, Db), 0.3 * s, 0.26 * s, 2, 'moon')

    def curtains_dyn(pen, t):
        k = (2.6 if window_open else 0.35) * curtains * wind
        sp = 2.3 if window_open else 0.6
        cw = (wx1 - wx0) * 0.42
        for side, x_ in ((-1, wx0 - cw * 0.7), (1, wx1 - cw * 0.3)):
            _curtain(pen, x_, wy0 - 44, cw, (wy1 - wy0) + 150, t * sp + (0 if side < 0 else 2.3), side, '#9a7ab0', k, 31 + side, folds=5,
                     lit=(MOON_GLOW, 50) if side < 0 else None)
            cv = pen.cv; cv.save()
            cv.clipPath(rect(x_ - 20, wy0 - 44, cw + 40, (wy1 - wy0) + 220), skia.ClipOp.kIntersect, True)
            _glow_stars(pen, lambda r: (x_ + r.uniform(0.1, 0.9) * cw, wy0 + r.uniform(0, 1.0) * (wy1 - wy0 + 120), 7), 9, 40 + side, 120)
            cv.restore()
        pen.fill(rect(wx0 - cw, wy0 - 58, wx1 - wx0 + 2 * cw, 12), '#e8e0f0'); pen.line(rect(wx0 - cw, wy0 - 58, wx1 - wx0 + 2 * cw, 12), 2, LINE)
        h = hz(t)
        if h > 0.02:
            pen.radial(None, wx0, wy0 + (wy1 - wy0) * 0.6, (wx1 - wx0) * 0.9, [(0, AMBER, 70 * h), (1, AMBER, 0)], clip=False)

    def room(pen, t):
        for X, base in ((-HW, '#3e3858'), (HW, '#463e62')):
            _side_wall(pen, v, X, Db, Dn, 0, CH, base, '#5a5280', 'dots', 90, shade=0.5)
        ceil = v.quad([(-HW, CH, Dn), (HW, CH, Dn), (HW, CH, Db), (-HW, CH, Db)])
        pen.linear(ceil, 0, v.y(CH, Dn), 0, v.y(CH, Db), ['#0a0a14', '#1c1a2c'])
        _glow_stars(pen, lambda r: (*v.p(r.uniform(-1.5, 1.5), CH, r.uniform(Dn + 0.4, Db)), r.uniform(5, 9)), 26, 77, 130)
        fl = v.quad([(-HW, 0, Db), (HW, 0, Db), (HW, 0, Dn), (-HW, 0, Dn)])
        pen.linear(fl, 0, v.gy(Db), 0, v.gy(Dn) + 200, ['#4a3a4a', '#2a2030'])
        pen.texture(fl, 'fabric', 0.4, 'overlay', 1.2)
        rug = poly([v.p(0.35 + 0.75 * math.cos(a_), 0.002, 2.05 + 0.55 * math.sin(a_)) for a_ in np.linspace(0, 2 * math.pi, 40)])
        pen.fill(rug, '#a86a8a'); pen.texture(rug, 'fabric', 0.6, 'overlay', 1.2); pen.line(rug, 3, '#5a3a4a')
        rug2 = poly([v.p(0.35 + 0.55 * math.cos(a_), 0.003, 2.05 + 0.4 * math.sin(a_)) for a_ in np.linspace(0, 2 * math.pi, 40)])
        pen.line(rug2, 3, '#e8c8d8', 200)
        _glow_stars(pen, lambda r: (*v.p(0.35, 0.003, 2.05), 0.16 * v.s(2.05)), 1, 3, 200)
        vx0, vy0 = v.p(HW, 0.32, 2.35); vx1, vy1 = v.p(HW, 0.12, 1.95)                      # the vent
        vent = v.quad([(HW - 0.01, 0.12, 2.35), (HW - 0.01, 0.32, 2.35), (HW - 0.01, 0.32, 1.95), (HW - 0.01, 0.12, 1.95)])
        pen.fill(vent, '#c8c4bc'); pen.line(vent, 2, LINE)
        for k in range(1, 7):
            D = 2.35 - 0.4 * k / 7
            pen.seg(v.p(HW - 0.01, 0.15, D), v.p(HW - 0.01, 0.29, D), 2.5, '#2a2830')
        pen.fill(vent, '#000000', 60)
        # dresser against the right wall: front, top, three drawers, a music box and a toy on top
        X = HW; D0, D1, Yt, dep = 3.25, 2.55, 0.85, 0.45
        fr = v.quad([(X - dep, 0, D0), (X - dep, Yt, D0), (X - dep, Yt, D1), (X - dep, 0, D1)])
        end = v.quad([(X - dep, 0, D1), (X - dep, Yt, D1), (X, Yt, D1), (X, 0, D1)])
        pen.fill(end, '#8a7a92'); pen.line(end, 2.5, LINE)
        pen.linear(fr, v.x(X - dep, D0), 0, v.x(X - dep, D1), 0, ['#b8a8c4', '#9a8aa8']); pen.line(fr, 2.5, LINE)
        for k in range(3):
            y0_, y1_ = 0.08 + k * 0.25, 0.08 + k * 0.25 + 0.21
            dq = v.quad([(X - dep, y0_, D0 - 0.04), (X - dep, y1_, D0 - 0.04), (X - dep, y1_, D1 + 0.04), (X - dep, y0_, D1 + 0.04)])
            pen.line(dq, 2, '#5a4a62', 220)
            pen.fill(oval(*v.p(X - dep, (y0_ + y1_) / 2, (D0 + D1) / 2), 0.022 * v.s((D0 + D1) / 2)), '#f0d8a0')
        top = v.quad([(X, Yt, D0), (X - dep, Yt, D0), (X - dep, Yt, D1), (X, Yt, D1)])
        pen.fill(top, '#cdbcd8'); pen.line(top, 2.5, LINE)
        mx_, my_ = v.p(X - 0.22, Yt, 2.95); ms = v.s(2.95)
        pen.shape(rrect(mx_ - 0.1 * ms, my_ - 0.1 * ms, 0.2 * ms, 0.1 * ms, 0.02 * ms), '#e8a0b8', 2)              # music box
        pen.shape(oval(mx_, my_ - 0.14 * ms, 0.04 * ms, 0.05 * ms), '#f0e0e8', 2)                                 # ballerina
        pen.shape(oval(*v.p(X - 0.2, Yt + 0.08, 2.7), 0.07 * v.s(2.7)), '#6ab0e0', 2)                             # a ball

    def bed_layer(pen, t):
        X0, X1, D0, D1 = -HW, -0.62, Db - 0.02, 1.6
        Ym = 0.42
        frame_ = v.quad([(X1, 0.08, D0), (X1, Ym, D0), (X1, Ym, D1), (X1, 0.08, D1)])
        foot = v.quad([(X0, 0.0, D1), (X0, 0.62, D1), (X1, 0.62, D1), (X1, 0.0, D1)])
        pen.fill(frame_, '#c8bcd0'); pen.line(frame_, 2.5, LINE)
        hb = v.quad([(X0, 0, D0), (X0, 1.05, D0), (X1, 1.05, D0), (X1, 0, D0)])
        pen.fill(hb, '#e8dce8'); pen.line(hb, 2.5, LINE)
        for k in range(1, 5):
            pen.seg(v.p(X0 + (X1 - X0) * k / 5, 0.5, D0), v.p(X0 + (X1 - X0) * k / 5, 1.0, D0), 4, '#b8a8c0')
        pil = v.quad([(X0 + 0.1, Ym + 0.12, D0 - 0.05), (X1 - 0.08, Ym + 0.12, D0 - 0.05), (X1 - 0.08, Ym + 0.1, D0 - 0.45), (X0 + 0.1, Ym + 0.1, D0 - 0.45)])
        pen.fill(pil, '#f0ecf4'); pen.line(pil, 2, LINE)
        if bed == 'empty':
            pen.fill(oval(*v.p((X0 + X1) / 2, Ym + 0.13, D0 - 0.25), 0.12 * v.s(D0), 0.03 * v.s(D0)), '#b8b0c8')     # the dent
            q = v.quad([(X0, Ym + 0.02, 2.0), (X1 + 0.05, Ym + 0.02, 2.0), (X1 + 0.12, 0.15, D1), (X0, 0.15, D1)])        # covers thrown back
            pen.fill(q, '#3a4a8a'); _glow_stars(pen, lambda r: (*v.p(r.uniform(X0 + 0.1, X1), Ym + 0.03, r.uniform(D1 + 0.1, 1.9)), 6), 10, 5, 150)
            pen.line(q, 2.5, LINE)
            sheet = v.quad([(X0, Ym + 0.03, D0 - 0.45), (X1, Ym + 0.03, D0 - 0.45), (X1, Ym + 0.03, 2.0), (X0, Ym + 0.03, 2.0)])
            pen.fill(sheet, '#e0dcea'); pen.line(sheet, 2, LINE, 160)
        else:
            Yq = Ym + 0.1
            quilt = v.quad([(X0, Yq, D0 - 0.42), (X1 + 0.04, Yq, D0 - 0.42), (X1 + 0.04, Yq, D1 + 0.02), (X0, Yq, D1 + 0.02)])
            hem = poly([v.p(X1 + 0.04, Yq, D0 - 0.42), v.p(X1 + 0.04, Yq, D1 + 0.02), v.p(X1 + 0.05, Ym - 0.12, D1 + 0.02)] +
                       [v.p(X1 + 0.05, Ym - 0.12 + 0.03 * math.sin(k * 1.7), D1 + 0.02 + (D0 - 0.44 - D1) * k / 8) for k in range(9)])
            pen.fill(hem, '#2a3670'); pen.line(hem, 2.5, LINE)
            pen.fill(quilt, '#3a4a8a'); pen.line(quilt, 2.5, LINE)
            pen.cv.save(); pen.cv.clipPath(union(quilt, hem), skia.ClipOp.kIntersect, True)
            _glow_stars(pen, lambda r: (*v.p(r.uniform(X0, X1), Yq, r.uniform(D1, D0 - 0.4)), 7), 16, 5, 150)
            pen.cv.restore()
            if bed == 'sleeping':                    # a small curled shape under the covers, her hair on the pillow
                cx_, cy_ = v.p((X0 + X1) / 2 + 0.06, Yq + 0.08, 2.45); ks = v.s(2.45)
                mound = _blob(cx_, cy_, 0.26 * ks, 0.12 * ks, 11, 8, 0.12)
                pen.fill(mound, '#3a4a8a'); pen.linear(mound, 0, cy_ - 0.12 * ks, 0, cy_ + 0.12 * ks, [(0, '#8a9ae0', 90), (1, '#000000', 60)])
                pen.line(mound, 2.5, LINE)
                hx, hy = v.p((X0 + X1) / 2 + 0.05, Ym + 0.22, D0 - 0.28)
                pen.fill(_blob(hx, hy, 0.1 * v.s(D0), 0.065 * v.s(D0), 9, 3, 0.25), '#5a3a28')
                pen.line(smooth([(hx - 0.06 * v.s(D0), hy + 0.02 * v.s(D0)), (hx, hy + 0.05 * v.s(D0)), (hx + 0.07 * v.s(D0), hy + 0.02 * v.s(D0))], False), 2, '#3a2418')
        pen.fill(foot, '#d8ccdc'); pen.line(foot, 2.5, LINE)
        for k in range(1, 5): pen.seg(v.p(X0 + (X1 - X0) * k / 5, 0.15, D1), v.p(X0 + (X1 - X0) * k / 5, 0.58, D1), 4, '#a898b0')
        rx, ry = v.p(X0 + 0.15, Ym + 0.12, D0 - 0.15); rs = v.s(D0)                                 # stuffed rabbit
        pen.shape(oval(rx, ry - 0.08 * rs, 0.07 * rs, 0.08 * rs), '#d8ccd8', 2)
        for e in (-1, 1): pen.shape(rrect(rx + e * 0.035 * rs - 0.02 * rs, ry - 0.26 * rs, 0.04 * rs, 0.14 * rs, 0.02 * rs), '#d8ccd8', 2)
        pen.fill(oval(rx - 0.02 * rs, ry - 0.09 * rs, 0.008 * rs), '#1a1a1a'); pen.fill(oval(rx + 0.02 * rs, ry - 0.09 * rs, 0.008 * rs), '#1a1a1a')
        # nightstand + the moon nightlight
        nx, ny = v.p(-0.55, 0.0, Db - 0.25); ns = v.s(Db - 0.25)
        pen.shape(rect(nx - 0.2 * ns, ny - 0.6 * ns, 0.4 * ns, 0.6 * ns), '#e0d4e4', 2.5)
        pen.line(rect(nx - 0.16 * ns, ny - 0.5 * ns, 0.32 * ns, 0.18 * ns), 2, '#9a8aa8')

    def lights(pen, t):
        x, y = nl; ns = v.s(Db - 0.25)
        k = nightlight
        pen.radial(None, x, y - 0.2 * ns, 2.6 * ns, [(0, MOON_GLOW, 70 * k), (0.4, MOON_GLOW, 26 * k), (1, MOON_GLOW, 0)], clip=False)
        _moon_nightlight(pen, x, y, ns * 1.6, k)
        if window_open:                                                                               # cold air light
            pen.linear(v.quad([(WX0, 0.0, Db), (WX1, 0.0, Db), (WX1 + 0.6, 0.0, 1.6), (WX0 - 0.3, 0.0, 1.6)]), 0, v.gy(Db), 0, v.gy(1.6),
                       [(0, '#7a9ae0', 50), (1, '#7a9ae0', 0)])

    L = [_cl(Db + 3, outside, 'outside', _key('lr', 'out'), (wx0 - 60, wy0 - 60, wx1 + 60, wy1 + 60)),
         Layer(Db + 2.9, out_dyn, 'outside_hazard', blur=0),
         _cl(Db, back, 'back_wall', _key('lr', 'back', window_open), (v.x(-HW, Db) - 30, v.y(CH, Db) - 30, v.x(HW, Db) + 30, v.gy(Db) + 30)),
         Layer(Db - 0.02, curtains_dyn, 'curtains'),
         _cl(2.4, room, 'room', _key('lr', 'room2'), box),
         _cl(2.0, bed_layer, 'bed', _key('lr', 'bed2', bed), (box[0], v.y(1.3, Db), v.x(0.0, 1.35), box[3])),
         Layer(1.95, lights, 'nightlight', blur=0)]
    _exposure(L, 0.25, ('back_wall', 'room', 'bed'))
    a = {'bed': v.anchor(-1.1, 2.6, Y=0.55, note='lying in bed (head toward the far wall)'),
         'window': v.anchor((WX0 + WX1) / 2, Db - 0.3, note='at her window'), 'floor_mid': v.anchor(0.2, 2.0)}
    return SetPiece('lily_room', L, a, {}, lens='lens', grade='nightlight', focus=Db, dof=2.0, cover=FRAME,
                    info={'view': v, 'window': (wx0, wy0, wx1, wy1), 'nightlight': nl, 'hazard': hz})


def _lily_window_view(curtains, wind, hz, van, van_X, drive):
    """Out of Lily's open window: sill, raised sash and curtains (near), the side yard 4 m below, the fence, the
    neighbour's house, and at the end of the side yard the street with the van at the curb (hazards / pulling away)."""
    v = View(420, 330, 4.1)                                 # eye 4.1 m above the side yard
    box = FRAME
    car = _vehicle_spec('van', van_X, 14.0, dict(van or {}, drive=drive) if drive else van)
    car['hazard_fn'] = hz

    def far_world(pen, t):
        pen.linear(rect(box[0], box[1], box[2] - box[0], v.gy(30) - box[1] + 40), 0, box[1], 0, v.gy(30), ['#05081a', '#101a3a', '#1e2850'])
        _stars(pen, (box[0], box[1], box[2], v.gy(30)), 160, 41, v.gy(30) - 20)
        _moon(pen, 1580, 120, 26)
        pen.fill(rect(box[0], v.y(0, 22), v.x(-2.0, 20) - box[0], v.gy(14.5) - v.y(0, 22)), '#16181f')
        pen.fill(rect(box[0], v.gy(14.5), v.x(-2.0, 14.5) - box[0], v.gy(12.5) - v.gy(14.5)), '#2a2c33')
        for X in (-26.0, -14.0):
            _house(pen, v, X, 26.0, 10.0, 3.2, 2.2, seed=int(-X), lit=(0, 0, 0, 0), porch=False, chimney=False)
        _streetlamp(pen, v.x(-6.5, 16.0), v.gy(16.0), v.s(16.0), side=-1)

    def world(pen, t):
        # neighbour's house (right) and its dark wall along the far side of the fence
        nb = v.quad([(1.0, 0, 6.5), (14.0, 0, 6.5), (14.0, 5.5, 6.5), (1.0, 5.5, 6.5)])
        pen.fill(nb, '#141826'); _siding(pen, nb, v.x(1.0, 6.5), v.y(5.5, 6.5), v.x(14, 6.5), v.gy(6.5), 0.2 * v.s(6.5), '#000000', 80, '#20263a', 30)
        for X in (3.0, 7.5):
            _window(pen, v.x(X, 6.5), v.y(4.6, 6.5), 1.0 * v.s(6.5), 1.1 * v.s(6.5), lit=0.0, lw=2.0)
            _window(pen, v.x(X, 6.5), v.y(1.9, 6.5), 1.0 * v.s(6.5), 1.1 * v.s(6.5), lit=0.0, lw=2.0)
        pen.fill(v.quad([(1.0, 5.5, 6.5), (14.0, 5.5, 6.5), (14.0, 7.0, 8.5), (1.0, 7.0, 8.5)]), '#0a0c14')
        # side yard: grass strip, the fence, a path of stepping stones, trash cans by the house wall
        yd = v.quad([(-30, 0, 2.2), (14, 0, 2.2), (14, 0, 4.0), (-30, 0, 4.0)])
        pen.linear(yd, 0, v.gy(4.0), 0, v.gy(2.2), ['#0e1712', '#14221a'])
        pen.texture(yd, 'fabric', 0.3, 'overlay', 0.6)
        for k in range(12):
            X = -10 + k * 1.6
            pen.fill(oval(*v.p(X, 0, 3.0), 0.28 * v.s(3.0), 0.09 * v.s(3.0)), '#3a3c42')
        for X in np.arange(-12.0, 14.0, 0.16):
            a_, b_ = v.p(X, 0, 4.1), v.p(X, 1.8, 4.1)
            pen.seg(a_, b_, max(2.0, 0.1 * v.s(4.1)), '#2a2420')
        pen.fill(v.quad([(-12, 1.55, 4.08), (14, 1.55, 4.08), (14, 1.65, 4.08), (-12, 1.65, 4.08)]), '#3a3028')
        pen.fill(v.quad([(-12, 0.35, 4.08), (14, 0.35, 4.08), (14, 0.45, 4.08), (-12, 0.45, 4.08)]), '#3a3028')
        for X, c in ((-3.0, '#1c2a22'), (-2.2, '#2a2a30')):
            x_, y_ = v.p(X, 0, 2.35); ss = v.s(2.35)
            pen.shape(poly([(x_ - 0.3 * ss, y_ - 1.0 * ss), (x_ + 0.3 * ss, y_ - 1.0 * ss), (x_ + 0.26 * ss, y_), (x_ - 0.26 * ss, y_)]), c, 2)
        # our own wall falling away below the window (left edge), siding
        ow = poly([(box[0], box[1]), (v.x(-3.2, 2.0), box[1]), (v.x(-3.2, 2.0), box[3]), (box[0], box[3])])

    def amber(pen, t):
        h = hz(t)
        if h > 0.02:
            x_, y_ = v.p(van_X, 1.0, 14.0)
            pen.radial(None, x_ + 200, v.gy(3.0), 1200, [(0, AMBER, 70 * h), (1, AMBER, 0)], sy=0.35, clip=False)

    def frame(pen, t):
        # open window from inside: sill across the bottom, raised sash at the top, side casings
        pen.fill(rect(box[0], 860, box[2] - box[0], box[3] - 860), '#d0c8d8')
        pen.linear(rect(box[0], 860, box[2] - box[0], 60), 0, 860, 0, 920, ['#e8e0ee', '#a8a0b4'])
        pen.line(rect(box[0], 860, box[2] - box[0], 60), 4, LINE)
        pen.fill(rect(box[0], 920, box[2] - box[0], box[3] - 920), '#4a4262')
        pen.fill(rect(box[0], box[1], box[2] - box[0], 120 - box[1]), '#cfc6d8'); pen.line(rect(box[0], 70, box[2] - box[0], 50), 4, LINE)
        pen.fill(rect(box[0], box[1], box[2] - box[0], 70 - box[1]), '#1a2240', 200)
        for xa, xb in ((box[0], 90), (1830, box[2])):
            pen.fill(rect(xa, box[1], xb - xa, box[3] - box[1]), '#d8d0e0'); pen.line(rect(xa, box[1], xb - xa, box[3] - box[1]), 4, LINE)
        pen.fill(rect(90, 120, 14, 740), '#000000', 60)

    def curt(pen, t):
        k = 3.0 * curtains * wind
        _curtain(pen, -60, -120, 420, 1150, t * 2.4, -1, '#9a7ab0', k, 51, folds=5, lit=(MOON_GLOW, 40))
        _curtain(pen, 1600, -120, 420, 1150, t * 2.4 + 2, 1, '#9a7ab0', k, 53, folds=5)
        h = hz(t)
        if h > 0.02: pen.radial(None, 200, 600, 700, [(0, AMBER, 60 * h), (1, AMBER, 0)], clip=False)

    L = [_cl(20.0, far_world, 'outside_far', _key('lw', 'far'), box, blur=0),
         _cl(6.0, world, 'outside', _key('lw', 'world2'), (box[0], v.y(7.6, 8.5) - 10, box[2], box[3]), blur=0),
         Layer(14.0, _car_layer_draw(v, 14.0, car, lambda t: (0.0, 0.0)), 'car'),
         Layer(3.0, amber, 'hazard_spill', blur=0),
         _cl(0.5, frame, 'window_frame', _key('lw', 'frame'), box),
         Layer(0.45, curt, 'curtains')]
    a = {'yard_below': v.anchor(0.4, 3.5, note='the driver in the side yard by the fence, looking up'), 'van': v.anchor(van_X, 14.0)}
    return SetPiece('lily_window', L, a, {}, lens=None, grade='nightlight', focus=6.0, dof=1.5, cover=FRAME, info={'view': v, 'hazard': hz})


def side_yard(window_open=True, nightlight=1.0, hazard=True, curtain=1.0, wind=1.0):
    """The side of the house at night under Lily's window, looking up from the side yard (the 3:41 delivery photo is this
    view): house 144's beige siding looming overhead, the soffit and gutter of the eave seen from below against the stars,
    Lily's window on the second floor glowing with the moon nightlight (window_open: the lower sash up, her lavender
    curtain flowing out over the sill and down the siding in the wind), the dark kitchen window below, the downspout, the
    AC unit, a trash can, the fence; the van's amber flashers wash round the front corner (right) across the siding.
    Anchors: driver (on the grass below the window, back to camera), lily_window (leaning out: chest on the sill), ac.
    lens None or 'lens', grade 'nightlight'."""
    v = View(420, 930, 1.1)                                  # low camera; horizon low in frame = looking up the wall
    box = FRAME
    D = 3.4                                                   # the wall plane
    hz = _hazard_fn(hazard)
    s = v.s(D)
    WX0, WX1, WY0, WY1 = -0.75, 0.45, 3.45, 4.65              # Lily's window (sill 3.45 m above the yard)
    wx0, wy0 = v.p(WX0, WY1, D); wx1, wy1 = v.p(WX1, WY0, D)
    top = 6.1

    def sky(pen, t):
        pen.linear(rect(box[0], box[1], box[2] - box[0], box[3] - box[1]), 0, box[1], 0, 900, ['#03050e', '#0a1230', '#1a2450'])
        _stars(pen, (box[0], box[1], box[2], 400), 220, 17, 380)
        _moon(pen, 1690, 70, 26)
        draw_tree(pen, v.x(-9.0, 8.0), v.gy(8.0), 15 * v.s(8.0), 0.0, 71, 0.0, '#04060c', ('#3a4a7a', 60), 5)

    def wall(pen, t):
        w_ = v.quad([(-7.0, 0, D), (5.2, 0, D), (5.2, top, D), (-7.0, top, D)])
        pen.linear(w_, 0, v.y(top, D), 0, v.gy(D), ['#2c2a2a', '#3e3a36', '#4a4640'])
        _siding(pen, w_, v.x(-7.0, D), v.y(top, D), v.x(5.2, D), v.gy(D), 0.2 * s, '#000000', 80, '#8a8070', 26)
        pen.fill(rect(v.x(5.2, D) - 0.12 * s, v.y(top, D), 0.12 * s, v.gy(D) - v.y(top, D)), '#9a948a')        # corner board
        pen.line(w_, 3, LINE)
        # eave seen from below: soffit band with vents, fascia + gutter, the roof edge against the sky
        sof = v.quad([(-7.4, top, D), (5.6, top, D), (5.6, top, D - 0.55), (-7.4, top, D - 0.55)])
        pen.fill(sof, '#5a5650'); pen.line(sof, 3, LINE)
        for X in np.arange(-6.5, 5.2, 1.6):
            pen.fill(v.quad([(X, top, D - 0.15), (X + 0.5, top, D - 0.15), (X + 0.5, top, D - 0.4), (X, top, D - 0.4)]), '#24221e')
        fas = v.quad([(-7.4, top, D - 0.55), (5.6, top, D - 0.55), (5.6, top + 0.22, D - 0.55), (-7.4, top + 0.22, D - 0.55)])
        pen.fill(fas, '#a8a294'); pen.line(fas, 3, LINE)
        gut = v.quad([(-7.4, top + 0.02, D - 0.6), (5.6, top + 0.02, D - 0.6), (5.6, top + 0.16, D - 0.6), (-7.4, top + 0.16, D - 0.6)])
        pen.fill(gut, '#8a8a90'); pen.line(gut, 2, LINE)
        # downspout, ground-floor (kitchen) window, foundation, Lily's window casing + shutters
        dpx = v.x(2.3, D - 0.08)
        dp = rect(dpx - 0.05 * s, v.y(top, D - 0.08), 0.1 * s, v.gy(D - 0.08) - v.y(top, D - 0.08))
        pen.fill(dp, '#8a8a90'); pen.fill(rect(dpx - 0.05 * s, v.y(top, D - 0.08), 0.03 * s, dp.getBounds().height()), '#b0b0b6'); pen.line(dp, 2, LINE)
        _window(pen, v.x(-2.6, D), v.y(2.3, D), 1.1 * s, 1.0 * s, lit=0.0, trim='#a8a294', lw=3, mull=(1, 1))
        pen.fill(v.quad([(-7.0, 0, D), (5.2, 0, D), (5.2, 0.5, D), (-7.0, 0.5, D)]), '#26262c')
        pen.texture(v.quad([(-7.0, 0, D), (5.2, 0, D), (5.2, 0.5, D), (-7.0, 0.5, D)]), 'plaster', 0.5)
        pen.line(rect(wx0 - 12, wy0 - 12, wx1 - wx0 + 24, wy1 - wy0 + 24), 24, '#a8a294'); pen.line(rect(wx0 - 24, wy0 - 24, wx1 - wx0 + 48, wy1 - wy0 + 48), 3, LINE)
        pen.fill(rect(wx0 - 36, wy1 + 12, wx1 - wx0 + 72, 22), '#b8b2a4'); pen.line(rect(wx0 - 36, wy1 + 12, wx1 - wx0 + 72, 22), 3, LINE)
        for sd in (-1, 1):
            sx = wx0 - 34 - 0.34 * s if sd < 0 else wx1 + 34
            sh = rect(sx, wy0 - 8, 0.34 * s, wy1 - wy0 + 16)
            pen.shape(sh, '#1e2a30', 3)
            for k in range(7): pen.seg((sx + 6, wy0 + (k + 0.6) * (wy1 - wy0) / 7), (sx + 0.34 * s - 6, wy0 + (k + 0.6) * (wy1 - wy0) / 7), 2, '#0e1418')

    def glow(pen, t):
        q = rect(wx0, wy0, wx1 - wx0, wy1 - wy0)
        k = nightlight
        pen.radial(q, (wx0 + wx1) / 2 - 30, wy1 - 20, (wx1 - wx0) * 0.95, [(0, mix('#2a2840', '#fff0c8', k)), (0.55, mix('#1a1830', '#b8a8a8', k)), (1, '#3a3450')])
        pen.fill(rect(wx0, wy0, wx1 - wx0, (wy1 - wy0) * 0.35), '#4a3e5e', 150)                                     # her ceiling, stars
        _glow_stars(pen, lambda r: (wx0 + r.uniform(0.1, 0.9) * (wx1 - wx0), wy0 + r.uniform(0.05, 0.3) * (wy1 - wy0), 5), 6, 13, 160)
        if window_open:
            pen.fill(rect(wx0, wy0, wx1 - wx0, (wy1 - wy0) * 0.47), '#9aa6c8', 36)
            pen.seg((wx0, wy0 + (wy1 - wy0) * 0.47), (wx1, wy0 + (wy1 - wy0) * 0.47), 14, '#a8a294')
            pen.seg((wx0, wy0 + (wy1 - wy0) * 0.47 + 7), (wx1, wy0 + (wy1 - wy0) * 0.47 + 7), 3, LINE)
        else:
            pen.seg((wx0, (wy0 + wy1) / 2), (wx1, (wy0 + wy1) / 2), 12, '#a8a294')
        pen.radial(None, (wx0 + wx1) / 2, (wy0 + wy1) / 2, (wx1 - wx0) * 1.3, [(0, '#fff0c8', 46 * k), (1, '#fff0c8', 0)], clip=False)
        if window_open:                       # her curtain streaming out of the open sash and down the siding
            bx0, bx1 = wx0 + (wx1 - wx0) * 0.15, wx0 + (wx1 - wx0) * 0.55
            yb = wy0 + (wy1 - wy0) * 0.5
            n = 8
            left, right = [], []
            for i in range(n + 1):
                u = i / n
                sway = curtain * wind * (18 + 70 * u) * noise1(t * 1.1 + u * 1.6, 31)
                flap = curtain * wind * 26 * u * math.sin(t * 5.0 - u * 6.0)
                yy = yb + u * (wy1 - yb + 0.9 * s)
                out = 0.0 if yy < wy1 else (yy - wy1) * 0.15
                left.append((bx0 + sway + flap * 0.5 - out * 0.2, yy))
                right.append((bx1 + sway * 1.15 - flap * 0.4 + out * 0.4, yy + 6 * u))
            path = smooth(left + right[::-1], True, 0.5)
            pen.fill(path, '#9a7ab0', 245)
            pen.linear(path, bx0, 0, bx1 + 60, 0, [(0, '#000000', 60), (0.5, '#ffffff', 30), (1, '#000000', 80)])
            for f in (0.33, 0.66):
                pen.line(smooth([(l[0] + (r[0] - l[0]) * f, l[1]) for l, r in zip(left, right)], False, 0.6), 2.5, '#6a4a80', 200)
            pen.line(path, 2.5, LINE, 230)
            _glow_stars(pen, lambda r: (bx0 + r.uniform(0.1, 0.8) * (bx1 - bx0), yb + r.uniform(0.1, 0.9) * (wy1 - yb + 0.9 * s), 6), 7, 43, 130)

    def amber(pen, t):
        h = hz(t)
        if h > 0.02:
            pen.radial(None, box[2] + 60, v.y(1.4, D), 1500, [(0, AMBER, 170 * h), (0.4, AMBER, 70 * h), (1, AMBER, 0)], sy=0.85, clip=False)

    def ground(pen, t):
        gq = rect(box[0], v.gy(D) - 2, box[2] - box[0], box[3] - v.gy(D) + 2)
        pen.linear(gq, 0, v.gy(D), 0, box[3], ['#101a14', '#0a120e'])
        rng = np.random.default_rng(4)
        for _ in range(420):
            Dd = rng.uniform(0.9, D); X = rng.uniform(-6, 6)
            x, y = v.p(X, 0, Dd); hh = rng.uniform(0.05, 0.12) * v.s(Dd)
            pen.seg((x, y), (x + rng.uniform(-0.3, 0.3) * hh, y - hh), max(0.8, 0.012 * v.s(Dd)), '#1d3329' if rng.uniform() < 0.5 else '#0a120f', 200)
        ax, ay = v.p(1.3, 0, D - 0.42); as_ = v.s(D - 0.42)                                        # AC unit
        ac = rect(ax - 0.42 * as_, ay - 0.8 * as_, 0.84 * as_, 0.8 * as_)
        pen.fill(ac, '#5a5c62'); pen.line(ac, 3, LINE)
        for k in range(10): pen.seg((ax - 0.38 * as_, ay - 0.75 * as_ + k * 0.07 * as_), (ax + 0.38 * as_, ay - 0.75 * as_ + k * 0.07 * as_), 2, '#2a2c30')
        pen.line(oval(ax, ay - 0.4 * as_, 0.28 * as_), 3, '#2a2c30')
        tx, ty = v.p(-3.6, 0, D - 0.5); ts = v.s(D - 0.5)
        pen.shape(poly([(tx - 0.3 * ts, ty - 1.0 * ts), (tx + 0.3 * ts, ty - 1.0 * ts), (tx + 0.26 * ts, ty), (tx - 0.26 * ts, ty)]), '#1c2a22', 3)
        pen.shape(rrect(tx - 0.34 * ts, ty - 1.08 * ts, 0.68 * ts, 0.1 * ts, 0.03 * ts), '#16221c', 3)

    def fence(pen, t):
        for X in np.arange(-7.0, -3.0, 0.16):
            a_, b_ = v.p(X, 0, 1.2), v.p(X, 1.8, 1.2)
            pen.seg(a_, b_, max(3.0, 0.1 * v.s(1.2)), '#1e1a16'); pen.seg((a_[0] + 3, a_[1]), (b_[0] + 3, b_[1]), 2, '#3a3028', 160)

    L = [_cl(30.0, sky, 'sky', _key('sy', 'sky5'), box, blur=0),
         _cl(D, wall, 'wall', _key('sy', 'wall5'), box),
         Layer(D - 0.01, glow, 'lily_window', blur=0),
         Layer(D - 0.02, amber, 'hazard_spill', blur=0),
         _cl(1.5, ground, 'ground', _key('sy', 'ground5'), (box[0], v.gy(D) - 260, box[2], box[3])),
         _cl(1.2, fence, 'fence', _key('sy', 'fence5'), (box[0], v.y(2.0, 1.2), v.x(-2.8, 1.2), box[3]))]
    _exposure(L, 0.15, ('wall',))
    a = {'driver': v.anchor((WX0 + WX1) / 2 + 0.2, D - 1.0, note='below the window, looking up (back to camera)'),
         'lily_window': Anchor((wx0 + wx1) / 2, wy1 + 12, D - 0.05, 1.2 * s, note='Lily leaning out: her chest on the sill'),
         'ac': v.anchor(1.3, D - 0.42)}
    return SetPiece('side_yard', L, a, {}, lens='lens', grade='nightlight', focus=D - 1.0, dof=1.5, cover=FRAME,
                    info={'view': v, 'window': (wx0, wy0, wx1, wy1), 'hazard': hz})


# ============================================================== delivery inserts (props, backgrounds, specs)
DRIVER_SKIN, DRIVER_SLEEVE = '#c0b1aa', '#5b3f2b'


def _CH():
    """The cast module (lazy: sets stays importable on its own)."""
    try:
        import characters
        return characters
    except Exception:
        return None


def _prop_label(pen, t, to=None, **kw):
    """The box's shipping label, big: FROM: RETURN, the TO line blank (to = text in a child's hand for the final card)."""
    W, H = 900, 640
    pen.fill(rect(-W / 2 - 30, -H / 2 + 120, W + 60, 60), TAPE, 200)                     # a tape wrap across it
    _ship_label(pen, -W / 2, -H / 2, W, H, to=to, seed=3)
    pen.fill(rect(-W / 2 - 30, H / 2 - 70, W + 60, 58), TAPE, 175)
    pen.fill(rect(-W / 2 - 30, H / 2 - 62, W + 60, 9), TAPE_HI, 60)


def _prop_tablet(pen, t, sig='initial', ink=1.0, ts='3:09 AM', screen='sign', flash=0.0, glitch=0.0, **kw):
    """The driver's Nightline handheld filling the frame (characters.draw_tablet: the same device he holds)."""
    CH = _CH()
    if CH is not None and hasattr(CH, 'draw_tablet'):
        CH.draw_tablet(pen, 0, 0, 1000, screen=screen, sig=sig, ink=ink, t=t, ts=ts, flash=flash, glitch=glitch)
        return
    body = rrect(-315, -500, 630, 1000, 70)
    pen.shape(body, '#1e2026', 10)
    sc = rrect(-260, -400, 520, 600, 24); pen.fill(sc, '#e8ecf0')
    text(pen.cv, 'SIGNATURE REQUIRED', 0, -330, 900, 38, '#1a1e2a')
    pen.seg((-200, 120), (200, 120), 4, '#5a6070')
    if sig == 'initial': _hand_text(pen.cv, 'J', -180, 100, 140, '#1d2a6a', 240, 2)


def _prop_box_inside(pen, t, keys=True, flaps=1.0, **kw):
    """Looking down into the opened, empty box at sunrise: only dad's rusted keys at the bottom."""
    CH = _CH()
    if CH is not None and hasattr(CH, 'draw_box_inside'):
        CH.draw_box_inside(pen, 0, 0, 900, t, flaps, keys, 1.0, dict(key='#ffcf8f'))
        return
    pen.fill(rect(-450, -340, 900, 680), '#3a2410'); pen.fill(rect(-200, -150, 400, 300), '#120a04')
    if keys: _rusty_keys(pen, 0, 40, 60, 20)


def _prop_bowl(pen, t, keys='house', drop=1.0, **kw):
    """The key bowl on the hall table, close: glazed blue ceramic, seen from 3/4 above. keys 'house' | 'dad' | 'none';
    drop 0..1 animates a ring of keys falling into it (lands at 0.8, small bounce, settles at 1)."""
    W = 700
    rim = oval(0, -40, 340, 112)
    body = smooth([(-340, -40), (-320, 40), (-230, 150), (-80, 190), (80, 190), (230, 150), (320, 40), (340, -40)], True, 0.6)
    pen.shadow(body, 20, 40, 40, '#000000', 150)
    pen.linear(body, -340, 0, 340, 0, ['#2a4256', '#46708e', '#2a4256', '#1a2a38'])
    pen.linear(body, 0, -40, 0, 190, [(0, '#ffffff', 0), (0.7, '#000000', 40), (1, '#000000', 110)])
    pen.line(body, 7, LINE)
    pen.radial(rim, -60, -40, 360, [(0, '#1a2a38'), (0.7, '#223448'), (1, '#3a5a74')], sy=0.4)
    for k in range(10):                                                                 # glaze drips / speckles
        a_ = k * 0.6
        pen.fill(oval(-250 + k * 52, 60 + 30 * math.sin(a_), 6, 9), '#8ab0cc', 90)
    u = clamp(drop)
    if u < 0.8: ky, kr = -800 * (1 - u / 0.8) ** 2, -40 * (1 - u / 0.8)
    else:
        w_ = (u - 0.8) / 0.2; ky, kr = -38 * math.sin(math.pi * w_) * (1 - w_), 4 * math.sin(w_ * 9) * (1 - w_)
    inside = keys != 'none' and u > 0.0
    if inside:
        cv = pen.cv
        cv.save()
        if u >= 0.8: cv.clipPath(oval(0, -40, 338, 110), skia.ClipOp.kIntersect, True)
        if keys == 'dad':
            CH = _CH()
            if CH is not None and hasattr(CH, 'draw_keyring'): CH.draw_keyring(pen, -40, -60 + ky, 330, t, 1.0, -30 + kr, 0.0)
            else: _rusty_keys(pen, -40, -60 + ky, 70, -30 + kr)
        else:
            cv.save(); cv.translate(-30, -50 + ky); cv.rotate(-20 + kr); cv.scale(0.55, 0.55); _prop_keys(pen, t, '#c9c2b4', None, 3); cv.restore()
        cv.restore()
    pen.line(rim, 8, LINE); pen.line(oval(0, -40, 330, 106), 4, '#9ac0d8', 160)
    pen.fill(poly([(-250, -110), (-120, -138), (-110, -128), (-240, -100)]), '#ffffff', 90)     # glaze highlight


def _prop_hazard_btn(pen, t, hz=None, press=0.0, **kw):
    """The van's hazard switch on the dash: red double-triangle button in a black bezel, its telltale blinking with the
    flashers (hz None = hazard(t)), press 0..1 pushes it in."""
    h = hazard(t) if hz is None else hz
    bez = rrect(-260, -170, 520, 340, 60)
    pen.shadow(bez, 0, 16, 26, '#000000', 170)
    pen.linear(bez, 0, -170, 0, 170, ['#2a2c32', '#141519']); pen.line(bez, 6, '#050506')
    d = 10 * press
    btn = rrect(-200, -120 + d, 400, 240, 40)
    pen.linear(btn, 0, -120 + d, 0, 120 + d, [mix('#5a1a14', '#e8402a', h), mix('#3a0e0a', '#a02010', h)])
    pen.line(btn, 5, '#0a0405')
    tri = lambda r: poly([(0, -r * 0.9 + d), (r * 0.95, r * 0.65 + d), (-r * 0.95, r * 0.65 + d)])
    pen.line(tri(95), 14, mix('#2a0806', '#fff2e0', h)); pen.line(tri(48), 10, mix('#2a0806', '#fff2e0', h))
    if h > 0.05:
        pen.glow(0, d, 360, '#ff5a2a', 120 * h); pen.glow(0, d, 140, '#ffd0a0', 120 * h)
    pen.fill(rrect(-190, -112 + d, 380, 40, 20), '#ffffff', 30 + 30 * h)
    text(pen.cv, 'HAZARD', 0, 225, 800, 30, '#8a8c94', 200, 0.3)


def _cab_static(pen):
    """The van cab through the driver's window (static artwork): far window onto the dark street, the passenger seat with a
    clipboard of signature forms, the dash with gauges, the wheel, and the EMPTY driver's seat (cracked brown vinyl, the
    belt hanging), the door frame around the window."""
    cv = pen.cv
    pen.linear(rect(-1300, -700, 2600, 1400), 0, -700, 0, 700, ['#0a0e1c', '#141a2a', '#0a0b10'])
    fw = poly([(-900, -520), (500, -520), (700, -60), (-900, -60)])                         # far window
    pen.linear(fw, 0, -520, 0, -60, ['#101a38', '#1e2a4a']); pen.line(fw, 8, '#05060a')
    for (x, y, r) in ((-500, -200, 26), (100, -250, 18), (380, -180, 40)):                  # lamps outside, out of focus
        pen.glow(x, y, r * 3, '#ffcf8a', 120); pen.fill(oval(x, y, r), '#ffe2b0', 120)
    pen.fill(rect(-1300, -60, 2600, 900), '#141218')                                         # far door
    ps = smooth([(-200, 650), (-180, 60), (-100, -120), (300, -130), (360, 60), (380, 650)], True, 0.4)                # passenger seat
    pen.shape(ps, '#2a2420', 7)
    clip = rrect(-60, 0, 260, 340, 14); pen.shadow(clip, 8, 12, 14, '#000000', 140)
    pen.shape(clip, '#8a6a3a', 6); pen.fill(rrect(-40, 30, 220, 290, 6), '#e8e4d8')
    for k in range(8): pen.seg((-20, 70 + k * 30), (160, 70 + k * 30), 3, '#8a8a8a', 200)
    pen.shape(rrect(30, -16, 80, 40, 10), '#c0c0c8', 5)
    dash = poly([(-1300, 200), (-1300, -40), (-700, -110), (-300, -60), (-300, 120), (-1300, 260)])                    # dashboard
    pen.linear(dash, 0, -110, 0, 260, ['#22242a', '#0e0f12']); pen.line(dash, 7, LINE)
    for gx in (-1080, -900):
        g = oval(gx, 40, 70); pen.fill(g, '#050608'); pen.line(g, 5, '#3a3c44')
        pen.glow(gx, 40, 90, '#4ae0a0', 40)
        for k in range(9):
            a_ = math.radians(150 + k * 30); pen.seg((gx + math.cos(a_) * 52, 40 + math.sin(a_) * 52), (gx + math.cos(a_) * 64, 40 + math.sin(a_) * 64), 3, '#8ae0c0', 200)
        pen.seg((gx, 40), (gx + 48 * math.cos(math.radians(200 + (gx % 7) * 10)), 40 + 48 * math.sin(math.radians(200 + (gx % 7) * 10))), 4, '#ff6a3a')
    wheel = oval(-760, 220, 300, 320)                                                       # steering wheel, seen at an angle
    pen.line(wheel, 46, '#08090b'); pen.line(wheel, 30, '#1e2026')
    pen.fill(rrect(-830, 160, 140, 120, 30), '#141519'); pen.line(rrect(-830, 160, 140, 120, 30), 5, LINE)
    pen.line(poly([(-760, 220), (-800, 700)], False), 60, '#141519')
    seat = smooth([(100, 760), (60, 120), (120, -330), (220, -400), (620, -400), (720, -330), (760, 120), (720, 760)], True, 0.45)   # the driver's seat
    pen.shadow(seat, 20, 30, 40, '#000000', 160)
    pen.linear(seat, 60, 0, 760, 0, ['#4a3220', '#6a4a30', '#3a2616'])
    pen.texture(seat, 'fabric', 0.35, 'overlay', 1.4)
    for k in range(4): pen.line(smooth([(150, -250 + k * 170), (410, -270 + k * 170), (690, -250 + k * 170)], False), 5, '#2a1a0e', 180)
    pen.line(smooth([(300, -200), (330, -60), (290, 60), (340, 200)], False), 4, '#1a0e06', 220)            # a crack in the vinyl
    pen.line(seat, 8, LINE)
    hr = rrect(240, -620, 380, 230, 70); pen.shape(hr, '#5a3e28', 8)                                      # headrest
    pen.seg((330, -390), (330, -340), 18, '#8a8c90'); pen.seg((530, -390), (530, -340), 18, '#8a8c90')
    pen.line(smooth([(760, -420), (700, -100), (640, 300), (600, 760)], False), 34, '#1a1b20')               # the belt, hanging
    pen.shape(rrect(570, 280, 70, 120, 12), '#a8aab0', 5)
    pen.fill(poly([(860, -700), (1300, -700), (1300, 700), (900, 700), (820, -100)]), '#cfccc2')            # door pillar (van white)
    pen.line(poly([(860, -700), (820, -100), (900, 700)], False), 8, LINE)
    pen.fill(poly([(-1300, -700), (1300, -700), (1300, -600), (-1300, -560)]), '#c3c0b6'); pen.line(poly([(-1300, -560), (1300, -600)], False), 8, LINE)


def _prop_cab(pen, t, hz=None, driver=False, **kw):
    """Insert: the van's empty driver's seat seen through his window, the hazard telltale blinking on the dash, amber
    pulses on the glass and the seat (hz None = hazard(t))."""
    h = hazard(t) if hz is None else hz
    _sprite(pen, ('cab', bool(driver)), _cab_static, (-1300, -700, 1300, 700))
    pen.fill(poly([(-980, -40), (-955, -85), (-930, -40)]), mix('#3a0e0a', '#ff6a3a', h)); pen.glow(-955, -55, 50, '#ff5a2a', 160 * h)
    if h > 0.02:
        pen.radial(None, -1100, -300, 1300, [(0, AMBER, 90 * h), (0.5, AMBER, 30 * h), (1, AMBER, 0)], clip=False)
        pen.radial(None, 420, -200, 500, [(0, AMBER, 40 * h), (1, AMBER, 0)], clip=False)
    for (x0, w_) in ((-1100, 160), (-400, 60), (300, 120)):                                 # glass reflections
        pen.fill(poly([(x0, 700), (x0 + w_, 700), (x0 + w_ + 500, -700), (x0 + 500, -700)]), '#c9d6f0', 16)


def _bg_box(pen, t):
    """The box's face filling the frame (the label sits on it): kraft, tape wraps, stains; the box edge on the right."""
    r = rect(-700, -500, 2700, 2100)
    pen.linear(r, 0, -500, 0, 1600, ['#b88a58', '#a87a4a', '#7e5632'])
    pen.texture(r, 'paper', 0.5, 'overlay', 3.0)
    for (y, hh) in ((-120, 90), (980, 90)):
        pen.fill(rect(-700, y, 2340, hh), TAPE, 215); pen.fill(rect(-700, y + 14, 2340, 14), TAPE_HI, 60)
    pen.fill(rect(1500, -500, 90, 2100), TAPE, 200); pen.fill(rect(1512, -500, 14, 2100), TAPE_HI, 55)
    for (x, y, rr) in ((200, 860, 160), (1350, 160, 120)):
        st = _blob(x, y, rr, rr * 0.7, 10, int(x), 0.3); pen.fill(st, '#5a3a1c', 50); pen.line(st, 5, '#4a2e14', 50)
    pen.fill(rect(1640, -500, 1100, 2100), '#06070c')                                        # past the box's edge: the dark porch
    pen.linear(rect(1590, -500, 60, 2100), 1590, 0, 1650, 0, ['#5a3e22', '#1a1008'])
    pen.radial(None, 300, 0, 1500, [(0, '#ffcf8f', 60), (1, '#000000', 90)], clip=False)


def _bg_porch_dawn(pen, t):
    r = rect(-700, -500, 3300, 2100)
    pen.linear(r, 0, -500, 0, 1600, ['#6a5040', '#4a362a'])
    for k in range(-10, 30):
        x = -700 + k * 130
        pen.seg((x, -500), (x + 200, 1600), 6, '#2a1c14', 200)
    pen.texture(r, 'wood', 0.5, 'overlay', 2.0, 70)
    pen.linear(r, -700, 0, 2600, 0, [(0, '#ffcf9a', 70), (0.6, '#ffcf9a', 0), (1, '#3a4a7a', 60)])


def _bg_table(pen, t):
    """The hall console top (in focus) with the wall and the lamp behind it."""
    wall = rect(-700, -500, 3300, 900)
    _wallpaper(pen, wall, (-700, -500, 2600, 400), 900, '#3b3a48', '#2a2934', 'damask', 150)
    pen.radial(None, 1500, -100, 900, [(0, '#ffcf8f', 150), (0.5, '#ffcf8f', 50), (1, '#ffcf8f', 0)], clip=False)
    pen.fill(oval(1500, -60, 70, 30), '#fff4dc', 200)
    top = poly([(-700, 400), (2600, 400), (2600, 1600), (-700, 1600)])
    pen.linear(top, 0, 400, 0, 1600, ['#3a2818', '#5a3e2a', '#4a3220'])
    pen.texture(top, 'wood', 0.55, 'overlay', 2.6, 8)
    pen.fill(rect(-700, 390, 3300, 16), '#24170e')
    pen.radial(None, 1400, 500, 1200, [(0, '#ffcf8f', 60), (1, '#ffcf8f', 0)], sy=0.5, clip=False)


def _bg_night(pen, t):
    pen.linear(rect(-700, -500, 3300, 2100), 0, -500, 0, 1600, ['#05070f', '#0d1530', '#0a0b10'])


def _bg_dash(pen, t):
    r = rect(-700, -500, 3300, 2100)
    pen.linear(r, 0, -500, 0, 1600, ['#1a1c22', '#0c0d10'])
    pen.texture(r, 'grunge', 0.3, 'overlay', 2.0)
    for (x, y, rr, c) in ((180, 120, 150, '#4ae0a0'), (420, 140, 120, '#4ae0a0'), (1700, 900, 90, '#ffb040')):
        pen.glow(x, y, rr * 2.2, c, 60); pen.line(oval(x, y, rr), 6, c, 90)


def _fg_tablet_left(t0):
    """The driver's other hand on the tablet's left edge (brown sleeve)."""
    def draw(pen, t):
        draw_hand(pen, 705, 620, 1.05, 8, 'hold', DRIVER_SKIN, DRIVER_SLEEVE, side=-1, part='front')
    def back(pen, t):
        draw_hand(pen, 705, 620, 1.05, 8, 'hold', DRIVER_SKIN, DRIVER_SLEEVE, side=-1, part='back')
    return [Layer(1.02, back, 'insert_hand2_back', blur=0), Layer(0.92, draw, 'insert_hand2', blur=0)]


_BG.update({'box': _bg_box, 'porch_dawn': _bg_porch_dawn, 'table': _bg_table, 'night': _bg_night, 'dash': _bg_dash})
PROPS.update({'label': _prop_label, 'tablet': _prop_tablet, 'box_inside': _prop_box_inside, 'bowl': _prop_bowl,
              'hazard_btn': _prop_hazard_btn, 'cab': _prop_cab})
PROP_SIZE.update({'label': (960, 700), 'tablet': (680, 1040), 'box_inside': (1100, 900), 'bowl': (760, 520),
                  'hazard_btn': (560, 480), 'cab': (2600, 1400)})
_DH = dict(skin=DRIVER_SKIN, sleeve=DRIVER_SLEEVE)
INSERTS.update({
    'label': dict(prop='label', bg='box', bgd=1.04, scale=1.25, rot=-3, cache=True, hand=('point', 1012, 618, 0.95, -14), hand_kw=_DH,
                  grade='doorbell_night'),
    'label_to': dict(prop='label', bg='box', bgd=1.04, scale=2.5, rot=-3, off=(-110, -120), cache=True,
                     hand=('point', 1040, 600, 1.7, -14), hand_kw=_DH, grade='doorbell_night'),
    'label_lily': dict(prop='label', bg='box', bgd=1.04, scale=1.25, rot=-3, cache=True, kw=dict(to='Lily'), grade='doorbell_night'),
    'tablet_sign': dict(prop='tablet', bg='porch', scale=0.9, rot=-2, cache=False, kw=dict(sig='initial', ink=1.0),
                        hand=('hold', 1236, 620, 1.05, -8), hand_kw=_DH, extra=_fg_tablet_left, grade='doorbell_night', lens='doorbell'),
    'tablet_lily': dict(prop='tablet', bg='porch', scale=0.9, rot=-2, cache=False, kw=dict(sig='lily', ink=1.0, ts='3:41 AM'),
                        hand=('hold', 1236, 620, 1.05, -8), hand_kw=_DH, extra=_fg_tablet_left, grade='doorbell_night'),
    'key_bowl': dict(prop='bowl', bg='table', bgd=1.04, scale=1.15, rot=0, off=(-80, 120), cache=False, kw=dict(keys='house'), grade='interior_dim'),
    'key_bowl_dad': dict(prop='bowl', bg='table', bgd=1.04, scale=1.15, rot=0, off=(-80, 120), cache=False, kw=dict(keys='dad'), grade='interior_dim'),
    'box_keys': dict(prop='box_inside', bg='porch_dawn', bgd=1.5, scale=1.05, rot=4, cache=True, kw=dict(keys=True), grade='dawn'),
    'van_seat': dict(prop='cab', bg='night', scale=0.78, rot=0, cache=False, kw=dict(driver=False), grade='night_blue'),
    'hazard_switch': dict(prop='hazard_btn', bg='dash', bgd=1.04, scale=1.5, rot=-4, cache=False, grade='night_blue',
                          hand=('point', 1000, 650, 1.0, -22), hand_kw=_DH),
})


# ============================================================== the delivery app on the police phone UI
APP_SCREENS = ('notify_delivered', 'order', 'notify_photo', 'photo_hall', 'photo_gone', 'attempted', 'notify_return',
               'photo_lily', 'notify_on_way', 'on_way')


def _pose(**kw):
    CH = _CH()
    return CH.Pose(**kw) if CH is not None else None


def _set_snapshot(pen, sp, x, y, w, h, crop=(0, 0, 1920, 1080), figures=None, t=0.0, exclude=()):
    """Draw a set's layers (home camera, far -> near, no DOF / grade) into the rect (x, y, w, h), cropping the design
    rect `crop`; figures = [(depth, fn(pen))] drawn in depth order among the layers. Used for the in-app photos."""
    cx0, cy0, cx1, cy1 = crop
    cv = pen.cv
    cv.save(); cv.clipPath(rect(x, y, w, h), skia.ClipOp.kIntersect, True)
    cv.translate(x, y); cv.scale(w / (cx1 - cx0), h / (cy1 - cy0)); cv.translate(-cx0, -cy0)
    from engine.scene import _color_filter
    items = []
    for l in sp:
        if l.name in exclude or callable(l.depth): continue
        al = l.alpha(t) if callable(l.alpha) else l.alpha
        if al <= 0.001: continue
        dim = l.dim(t) if callable(l.dim) else (l.dim or 0.0)
        items.append((l.depth_at(t), 0, (lambda l_: (lambda p_: l_.draw(p_, t)))(l), dim, al))
    for d, fn in (figures or []): items.append((d, 1, fn, 0.0, 1.0))
    items.sort(key=lambda it: (-it[0], it[1]))
    for d, kind, fn, dim, al in items:
        if dim > 0.001 or al < 0.999:
            p = skia.Paint(); p.setAlphaf(al)
            if dim > 0.001: p.setColorFilter(_color_filter(1 - dim, 1 - dim, 1 - dim))
            cv.saveLayer(None, p); fn(Pen(cv)); cv.restore()
        else:
            fn(Pen(cv))
    cv.restore()


def _photo_hall_art(p_, w, h):
    """3:11 AM: you, from behind, standing in the front hallway in your socks, holding your phone, lit by its screen;
    taken from the far end of the hall (the hall view looking at the front door, stairs on the left)."""
    sp = hallway(police=False, stairs=True, lamp=0.0, porch_light=0.6, bowl='house')
    a = sp.anchors['door']
    CH = _CH()

    def you(pen):
        hx, hy = a.x, a.y - a.height * 0.62
        pen.radial(None, hx, hy, a.height * 0.6, [(0, '#bcd4ff', 150), (0.5, '#8aa8e8', 50), (1, '#8aa8e8', 0)], clip=False)
        if CH is not None:
            try:
                CH.draw(pen, 'you', a.x - 20, a.y, a.height * 0.98, CH.Pose(turn=2.0, hr_fwd=30.0, hl_fwd=30.0),
                        light=dict(rim='#bcd4ff', rim_a=120, side=1, key=-0.3))
                return
            except Exception:
                pass
        body = union(oval(a.x, a.y - a.height * 0.9, a.height * 0.075), rrect(a.x - a.height * 0.13, a.y - a.height * 0.8, a.height * 0.26, a.height * 0.8, 30))
        pen.fill(body, '#2a2e3a'); pen.rim(body, 1, -0.4, 6, '#bcd4ff', 160)
    _set_snapshot(p_, sp, 0, 0, w, h, (480, 120, 1440, 1080), [(a.depth - 0.01, you)], exclude=('near_frame',))
    p_.fill(rect(0, 0, w, h), '#0a0c18', 120)                                             # 3 AM dark, the phone glow is the key
    p_.radial(None, w * 0.5, h * 0.52, w * 0.6, [(0, '#c8d8ff', 70), (1, '#c8d8ff', 0)], clip=False)


def _photo_lily_art(p_, w, h):
    """3:41 AM, from below: Lily (8) leaning out of her open window in her pajamas, the driver (from behind, cap) holding
    his glowing tablet up to her, her small finger on the screen."""
    sp = side_yard(window_open=True, hazard=lambda t: 1.0)
    wx0, wy0, wx1, wy1 = sp.info['window']
    CH = _CH()

    def lily(pen):
        cv = pen.cv
        oy0 = wy0 + (wy1 - wy0) * 0.5                                                             # the open lower sash
        hgt = (wy1 - wy0) * 1.75
        fx_, fy_ = (wx0 + wx1) / 2 - 4, oy0 + hgt * 0.93
        tx, ty = (wx0 + wx1) / 2 + (wx1 - wx0) * 0.55, wy1 + (wy1 - wy0) * 0.1                  # the tablet, right of the sill
        pen.glow(tx, ty, (wx1 - wx0) * 0.9, '#e8f0ff', 130)
        def her(pp):
            if CH is None: pp.fill(oval(fx_, oy0 + hgt * 0.12, hgt * 0.1), '#2a2030'); return
            try:
                CH.draw(pp, 'lily', fx_, fy_, hgt, CH.Pose(lean=0.2, hl_down=40.0, hl_out=260.0, hl_fwd=160.0, hl_shape='point', expr='blank'),
                        light=dict(rim='#e8f0ff', rim_a=150, side=1, key=-0.15))
            except Exception:
                pp.fill(oval(fx_, oy0 + hgt * 0.12, hgt * 0.1), '#2a2030')
        cv.save(); cv.clipPath(rect(wx0, oy0, wx1 - wx0, wy1 - oy0 + 4), skia.ClipOp.kIntersect, True); her(pen); cv.restore()
        cv.save(); cv.clipPath(rect((wx0 + wx1) / 2, oy0, (wx1 - wx0) * 1.2, wy1 - oy0 + 0.4 * (wy1 - wy0)), skia.ClipOp.kIntersect, True)
        cv.clipPath(rect(wx0 - 40, oy0 - 400, wx1 - wx0 + 40, 400 + (wy1 - oy0) + 12), skia.ClipOp.kDifference, True)
        her(pen); cv.restore()

    def driver(pen):
        dx_, dy_ = (wx0 + wx1) / 2 + 170, 1500
        if CH is not None:
            try:
                CH.draw(pen, 'driver', dx_, dy_, 820, CH.Pose(turn=2.0, hl_down=-300.0, hl_out=-160.0, hl_fwd=60.0, hl_prop='tablet', lean=-0.1),
                        light=dict(rim='#ffa31f', rim_a=140, side=1, key=-0.5)); return
            except Exception:
                pass
        pen.fill(union(oval(dx_, dy_ - 640, 60, 70), rrect(dx_ - 150, dy_ - 560, 300, 600, 80)), '#0a0a0e')
    _set_snapshot(p_, sp, 0, 0, w, h, (610, 300, 1350, 1040), [(3.39, lily), (1.3, driver)])
    p_.fill(rect(0, 0, w, h), '#ffffff', 26)                                                 # the flash
    p_.radial(None, w * 0.55, h * 0.45, w * 0.75, [(0, '#ffffff', 40), (0.6, '#000000', 0), (1, '#000000', 150)], clip=False)


def _photo(pen, kind, x, y, w, h, ts):
    """An in-app delivery photo (cached raster per size) with the timestamp burn-in."""
    fn = {'hall': _photo_hall_art, 'lily': _photo_lily_art}[kind]
    cv = pen.cv
    cv.save(); cv.translate(x, y)
    _sprite(pen, ('app_photo', kind, round(w), round(h)), lambda p_: fn(p_, w, h), (0, 0, w, h))
    cv.restore()
    text(cv, ts, x + w - 8, y + h - 10, 800, 11, '#ffb43a', 230, 0.08, 'right', 0.8)
    pen.line(rect(x, y, w, h), 1.5, '#000000', 200)


def _app_header(pen, cv, T, H, a, title='NIGHTLINE', sub=None):
    pen.fill(rect(-138, -H / 2 + 50, 276, 50), '#16192a', a)
    cv.save(); cv.translate(-112, -H / 2 + 84)
    _nl_logo(cv, pen, 0, 0, 13, a, 0.0, tag=False, dark='#e8ecf6', moon=NL_AMBER)
    cv.restore()
    if sub: T(sub, -H / 2 + 128, 11, '#8a93ad', 700, 0.22)


def _notification(pen, cv, T, y, title, body, a, k=1.0, when='now'):
    card = rrect(-128, y, 256, 92, 18)
    pen.fill(card, '#2a2f44', a * 0.92 * k); pen.line(card, 1.5, '#4a5070', a * 0.6 * k)
    pen.fill(rrect(-116, y + 12, 26, 26, 7), '#16192a', a * k)
    pen.fill(minus(oval(-103, y + 25, 9), oval(-99, y + 23, 7.5)), NL_AMBER, a * k)
    text(cv, 'NIGHTLINE', -82, y + 30, 800, 11, '#c8cee0', a * k, 0.12, 'left')
    text(cv, when, 116, y + 30, 600, 11, '#8a93ad', a * k, 0.0, 'right')
    lines = wrap(title, 800, 15, 225)
    for i, l in enumerate(lines[:2]): text(cv, l, -116, y + 56 + i * 18, 800, 15, '#ffffff', a * k, 0.0, 'left')
    if body: text(cv, body, -116, y + 56 + len(lines[:2]) * 18, 600, 12, '#aeb6cc', a * k, 0.0, 'left')


def app_phone(cv, screen, t, x=960, y=560, scale=1.0, hand=True, skin='#c0aa9e', alpha=255, clock=None, sender=None,
              photo_k=1.0, notify_k=None):
    """The delivery app on the police phone (same body, glass, hand hook engine.hud._hand, palette and fonts as
    hud.phone), drawn on the HUD canvas. screen (t = seconds since this screen appeared):
      'notify_delivered'  lock screen 3:07, banner 'Your package has been delivered.'
      'order'             ORDER DETAILS: 1 item, SIGNATURE REQUIRED, Recipient: This address, Sender: RETURN
      'notify_photo'      lock screen 3:11, banner 'Delivery photo added.'
      'photo_hall'        DELIVERY PHOTO 3:11 AM: you from behind in the front hall, lit by your screen (photo_k fades it in)
      'photo_gone'        the same item: 'No delivery photo on file.' (the photo never existed)
      'attempted'         Delivery attempted / Package left at door / Return pickup scheduled for 6:12 a.m. (tracker)
      'notify_return'     lock screen 3:41, banner 'Return complete.'
      'photo_lily'        DELIVERY PHOTO 3:41 AM from below: Lily signing at her window; Signed by: 'Lily.' (child's hand)
      'notify_on_way'     the next night, 3:07: 'Your package is on its way. Signature required.'
      'on_way'            ORDER DETAILS again: Recipient: This address, Sender: 'Lily' in a child's handwriting.
    clock overrides the status-bar / lock time; notify_k (0..1) slides the banner in (default: over the first 0.35 s)."""
    from engine import hud as H_
    pen = Pen(cv); a = alpha
    W, H = 300.0, 600.0
    vib = 0.0
    if screen.startswith('notify_') and t < 0.6:
        vib = math.sin(t * 2 * math.pi * 26) * 3.0 * (1 - t / 0.6)
    cv.save(); cv.translate(x + vib, y); cv.scale(scale, scale)
    if hand: H_._hand(pen, W, H, skin, a, False)
    body = rrect(-W / 2, -H / 2, W, H, 46)
    pen.radial(None, 0, 24, W * 0.95, [(0, '#000000', 170 * a / 255), (0.6, '#000000', 90 * a / 255), (1, '#000000', 0)],
               sy=H * 0.62 / (W * 0.95), clip=False)
    pen.fill(body, '#15161b', a); pen.line(body, 6, LINE, a)
    scr = rrect(-W / 2 + 12, -H / 2 + 12, W - 24, H - 24, 36)
    lock = screen.startswith('notify_')
    top, bot = ('#1a2240', '#0a0d18') if lock else ('#121626', '#090b13')
    pen.linear(scr, 0, -H / 2, 0, H / 2, [top, bot], a / 255)
    cv.save(); cv.clipPath(scr, skia.ClipOp.kIntersect, True)
    pen.fill(rrect(-38, -H / 2 + 24, 76, 20, 10), '#050506', a)

    def T(s, yy, size, c='#ffffff', w=800, sp=0.02, aa=1.0, al='center', xx=0.0):
        text(cv, s, xx, yy, w, size, c, a * aa, sp, al, 0.0)
    clk = clock or {'notify_delivered': '3:07', 'order': '3:08', 'notify_photo': '3:11', 'photo_hall': '3:11', 'photo_gone': '3:12',
                    'attempted': '3:24', 'notify_return': '3:41', 'photo_lily': '3:41', 'notify_on_way': '3:07', 'on_way': '3:07'}[screen]
    if not lock:
        T(clk, -H / 2 + 40, 12, '#c8cee0', 700, 0.04, al='left', xx=-112)
        pen.fill(rrect(84, -H / 2 + 31, 22, 10, 3), '#c8cee0', a * 0.8)
    if lock:
        T(clk, -H / 2 + 150, 74, '#ffffff', 700, 0.0)
        T({'notify_on_way': 'Thursday'}.get(screen, 'Wednesday'), -H / 2 + 186, 15, '#c8d2ee', 600, 0.04)
        k = clamp(t / 0.35) if notify_k is None else notify_k
        msg = {'notify_delivered': ('Your package has been delivered.', 'Tap to view delivery details.'),
               'notify_photo': ('Delivery photo added.', 'Tap to view.'),
               'notify_return': ('Return complete.', ''),
               'notify_on_way': ('Your package is on its way.', 'Signature required.')}[screen]
        cv.save(); cv.translate(0, -40 * (1 - ease_out_cubic(k)))
        _notification(pen, cv, T, -40, msg[0], msg[1], a, k)
        cv.restore()
        pen.fill(rrect(-50, H / 2 - 30, 100, 5, 2.5), '#ffffff', a * 0.6)
    else:
        _app_header(pen, cv, T, H, a)
        if screen in ('order', 'on_way'):
            T('ORDER DETAILS', -H / 2 + 128, 11, '#8a93ad', 700, 0.22)
            if screen == 'on_way':
                T('Your package is on its way.', -H / 2 + 154, 14, '#ffffff', 800, 0.0)
            yy = -H / 2 + (178 if screen == 'on_way' else 156)
            pen.fill(rrect(-118, yy, 236, 74, 12), '#1c2134', a)
            pen.shape(rrect(-104, yy + 12, 34, 50, 4), '#a8784a', 2)                         # the tall narrow box icon
            pen.fill(rect(-104, yy + 30, 34, 6), TAPE, a)
            T('1 item', yy + 32, 15, '#ffffff', 800, 0.0, al='left', xx=-58)
            pen.fill(rrect(-58, yy + 42, 142, 20, 10), RED_UI, a)
            T('SIGNATURE REQUIRED', yy + 56, 10, '#ffffff', 800, 0.1, al='left', xx=-50)
            yy += 98
            T('RECIPIENT', yy, 10, '#8a93ad', 700, 0.22, al='left', xx=-104)
            T('This address', yy + 22, 16, '#ffffff', 800, 0.0, al='left', xx=-104)
            yy += 52
            pen.seg((-112, yy - 12), (112, yy - 12), 1.2, '#2e344a', a)
            T('SENDER', yy + 6, 10, '#8a93ad', 700, 0.22, al='left', xx=-104)
            if screen == 'order':
                T(sender or 'RETURN', yy + 44, 34, '#ffffff', 900, 0.08, al='left', xx=-104)
            else:
                _child_hand(pen, sender or 'Lily', -100, yy + 50, 34, a)
            yy += 76
            pen.seg((-112, yy - 12), (112, yy - 12), 1.2, '#2e344a', a)
            T('STATUS', yy + 6, 10, '#8a93ad', 700, 0.22)
            T('Out for delivery' if screen == 'order' else 'On its way to you', yy + 28, 14, NL_AMBER, 800, 0.0)
        elif screen in ('photo_hall', 'photo_gone', 'photo_lily'):
            T('DELIVERY PHOTO', -H / 2 + 128, 11, '#8a93ad', 700, 0.22)
            px, py, pw, ph = -126, -H / 2 + 142, 252, 252
            if screen == 'photo_gone':
                pen.fill(rrect(px, py, pw, ph, 8), '#1a1e2c', a)
                pen.line(rrect(px + 90, py + 80, 72, 56, 8), 3, '#4a5068', a)
                pen.fill(oval(px + 126, py + 108, 14), '#4a5068', a)
                T('No delivery photo', py + 178, 14, '#c8cee0', 800, 0.0)
                T('on file for this item.', py + 198, 12, '#8a93ad', 600, 0.0)
            else:
                cv.save(); cv.clipPath(rrect(px, py, pw, ph, 8), skia.ClipOp.kIntersect, True)
                _photo(pen, 'hall' if screen == 'photo_hall' else 'lily', px, py, pw, ph, '3:11 AM' if screen == 'photo_hall' else '3:41 AM')
                if photo_k < 1: pen.fill(rect(px, py, pw, ph), '#1a1e2c', a * (1 - photo_k))
                cv.restore()
            yy = py + ph + 30
            if screen == 'photo_lily':
                T('SIGNED BY', yy, 10, '#8a93ad', 700, 0.22)
                _child_hand(pen, 'Lily.', -38, yy + 40, 30, a)
                T('Return complete', yy + 72, 13, NL_AMBER, 800, 0.0)
            else:
                T('Proof of delivery', yy, 13, '#ffffff', 800, 0.0)
                T('Front hallway  •  3:11 AM' if screen == 'photo_hall' else 'Photo removed', yy + 20, 12, '#8a93ad', 600, 0.0)
        elif screen == 'attempted':
            T('DELIVERY STATUS', -H / 2 + 128, 11, '#8a93ad', 700, 0.22)
            T('Delivery attempted', -H / 2 + 160, 20, NL_AMBER, 800, 0.0)
            T('Package left at door.', -H / 2 + 186, 13, '#ffffff', 700, 0.0)
            steps = [('Out for delivery', '3:07 AM', True), ('Delivery attempted', '3:24 AM', True), ('Package left at door', '3:24 AM', True),
                     ('Return pickup', '6:12 AM', False)]
            yy = -H / 2 + 222
            for i, (lab, tm, done) in enumerate(steps):
                cy_ = yy + i * 52
                if i < len(steps) - 1: pen.seg((-88, cy_ + 8), (-88, cy_ + 52 - 8), 3, NL_AMBER if done else '#3a4058', a)
                pen.fill(oval(-88, cy_, 8), NL_AMBER if done else '#16192a', a); pen.line(oval(-88, cy_, 8), 2.5, NL_AMBER, a)
                T(lab, cy_ + 5, 12, '#ffffff' if done else '#c8cee0', 800, 0.0, al='left', xx=-72)
                T(tm, cy_ + 22, 10, '#8a93ad', 600, 0.0, al='left', xx=-72)
            pen.fill(rrect(-118, yy + 196, 236, 60, 12), '#2a2416', a)
            T('Return pickup scheduled', yy + 220, 12, '#ffd9a0', 800, 0.0)
            T('for 6:12 a.m.', yy + 240, 12, '#ffd9a0', 800, 0.0)
    cv.restore()
    pen.radial(scr, -W * 0.3, -H * 0.45, H * 0.9, [(0, '#ffffff', 16), (1, '#ffffff', 0)], a / 255)                   # glass sheen
    if hand: H_._hand(pen, W, H, skin, a, True)
    cv.restore()


RED_UI = '#d8262e'


def _child_hand(pen, s, x, y, size, a=255):
    """A child's printed handwriting (uneven, wobbly, pencil-blue): 'Lily' / 'Lily.'"""
    _hand_text(pen.cv, s, x, y, size, '#4a6ad8', a * 0.95, seed=7, slant=0.05, weight=700, wobble=2.6)


# ============================================================== delivery-film builders (defaults for 3:07 AM) + registry
def delivery_porch(view='doorbell', van=None, hazard=True, box=None, ir=False, tod='night', era='now', car_X=None, **kw):
    """The porch at 3 AM. view 'doorbell' (fisheye beside the door, lens 'doorbell' / 'doorbell_ir') or 'peephole'.
    The NIGHTLINE van idles at the curb with its hazards blinking (van = dict(driver=True|f(t), door=0..1|f(t),
    drive=('out', t0, t1, X0, X1), head=False)), houses across dark (WINDOWS_3AM), porch lantern + moths, no police.
    box = None | 'door' (against the front door: a tall slab at the left edge of the fisheye) | 'boots' (beside the
    driver; prefer characters.draw_box for an acting box) | dict(at, state='taped'|'cut'|'open', knock=knock_pulse(...)).
    tod='dawn' = sunrise 6:12 (lights off, warm sky, grade 'dawn'; pass vehicle via van=False for no van).
    era='memory' = 21 years ago (grade 'memory'). Anchors: driver, driver_close, box_boots, box_door, steps, path_mid,
    gate, van_cab, van_door; paths porch_to_van / van_to_porch. info['hazard'] = f(t) for amber rim light on people."""
    vehicle = None if van is False else 'van'
    if view == 'peephole':
        return porch_peephole(car=vehicle is not None, police=False, car_X=car_X or 2.6, vehicle=vehicle, van=van or None, hazard=hazard,
                              tod=tod, windows=WINDOWS_3AM if tod == 'night' else None, era=era, **kw)
    return porch_doorbell(car=vehicle is not None, police=False, car_X=car_X or 4.0, vehicle=vehicle, van=van or None, hazard=hazard,
                          box=box, ir=ir, tod=tod, windows=WINDOWS_3AM if tod == 'night' else None, era=era, **kw)


def delivery_street(van=None, hazard=True, era='now', car_X=3.6, bedroom_lit=0.0, living_lit=0.0, upstairs_left=0.0, **kw):
    """House 144 from across the street at 3:07: every window dark (living_lit / bedroom_lit / upstairs_left to light
    one), the white NIGHTLINE van at the curb in front (hazards blinking; van=dict(driver, door, drive, head)).
    era='memory': 21 years ago, the old wood-panel station wagon parked in front, grade 'memory'."""
    return street_wide(car=True, police=False, car_X=car_X, vehicle='van', van=van, hazard=hazard, era=era, bedroom_lit=bedroom_lit,
                       living_lit=living_lit, upstairs_left=upstairs_left, **kw)


def delivery_hall(stairs=True, bowl='house', lamp=0.0, porch_light=1.0, door_open=0.0, outside=None, **kw):
    """Your front hall at 3 AM looking at the front door (the police hall, now with the stairs on the left and the key
    bowl on the side table; lamp off by default: the phone is the light). door_open / outside as hallway()."""
    return hallway(police=False, stairs=stairs, bowl=bowl, lamp=lamp, porch_light=porch_light, door_open=door_open,
                   outside=outside, coats=False, **kw)


def porch_doorway(tod='dawn', era='now', box='door', van=None, hazard=True, door_open=0.92, lamp=0.0, car_X=2.2):
    """The front door open onto the porch, seen from inside the hall: tod 'dawn' (6:12: your mother opens the door, the
    box still on the porch, its tape cut: box=dict(state='open'); daylight pouring in), 'night' (3 AM, the box backlit at
    the threshold, the van with hazards beyond), era 'memory' (21 years ago: dad on the porch signing, grade 'memory').
    door_open 0..1 or f(t) animates the door swinging in. Push the camera to info['doorway_cam'] = (x, y, zoom) to frame
    the doorway. van=False removes the van (dawn default)."""
    if van is None: van = (tod != 'dawn')
    vehicle = 'van' if van else None
    bx = box if not (tod == 'dawn' and box == 'door') else dict(at='door', state='open')
    sp = hallway(police=False, stairs=True, lamp=lamp, door_open=door_open, coats=False,
                 outside=dict(tod=tod, era=era, box=bx, vehicle=vehicle, van=van if isinstance(van, dict) else None, hazard=hazard,
                              car_X=car_X))
    if era == 'memory': sp.grade = 'memory'
    elif tod == 'dawn': sp.grade = Grade('interior_dim').lerp('dawn', 0.45)
    return sp


def memory_porch(view='doorway', **kw):
    """21 years ago, the same house: view 'doorway' (mum's view of the open door: the box on the porch, the van at the
    curb, hazards) or 'street' (the house from across the street, the old station wagon, the van). Grade 'memory'."""
    if view == 'street': return delivery_street(era='memory', **kw)
    return porch_doorway(tod='night', era='memory', **kw)


def sunrise_porch(view='doorbell', **kw):
    """6:12 AM: the box still against the door, the tape cut, flaps open, no van. view 'doorbell' or 'doorway'."""
    if view == 'doorway': return porch_doorway(tod='dawn', **kw)
    return delivery_porch('doorbell', van=False, box=dict(at='door', state='open'), tod='dawn', **kw)


def phone_bg(bg='hall', **kw):
    """Background set for the app-phone shots (B_phone style: blurred + darkened behind app_phone() on the HUD):
    'hall' (delivery_hall), 'hall_back', 'upstairs', 'lily_room', 'porch' (the doorbell view, through the window)."""
    sp = {'hall': lambda: delivery_hall(**kw), 'hall_back': lambda: hall_back(**kw), 'upstairs': lambda: upstairs_hall(**kw),
          'lily_room': lambda: lily_room(window_open=True, bed='empty', **kw), 'porch': lambda: delivery_porch(**kw)}[bg]()
    sp.grade, sp.lens, sp.focus, sp.dof = 'phone_dark', None, 1.0, 9.0
    return sp


SETS.update({'delivery_porch': delivery_porch, 'delivery_street': delivery_street, 'delivery_hall': delivery_hall,
             'porch_doorway': porch_doorway, 'memory_porch': memory_porch, 'sunrise_porch': sunrise_porch, 'hall_back': hall_back,
             'upstairs_hall': upstairs_hall, 'lily_room': lily_room, 'side_yard': side_yard, 'phone_bg': phone_bg})
__all__ += ['delivery_porch', 'delivery_street', 'delivery_hall', 'porch_doorway', 'memory_porch', 'sunrise_porch', 'hall_back',
            'upstairs_hall', 'lily_room', 'side_yard', 'phone_bg', 'app_phone', 'APP_SCREENS', 'delivery_van', 'hazard',
            'hazard_ticks', 'knock_pulse', 'WINDOWS_3AM', 'VAN_LEN']


def doorway_camera(sp, t0=0.0, t1=6.0, rate=0.02, shake=1.2):
    """A camera framed on the open front doorway of hallway(door_open=...) / porch_doorway(): a slow dolly push from
    info['doorway_cam'] plus the held optical punch-in (engine Cam.snap), so the doorway fills ~80 % of the frame height."""
    from engine.camera import push_in as _push
    x, y, z, f = sp.info['doorway_cam']
    return _push(t0, t1, x, y, z, rate=rate, shake=shake).snap(t0 - 1.0, f, 0.001)


__all__ += ['doorway_camera']
