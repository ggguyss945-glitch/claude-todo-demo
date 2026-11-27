"""sets.py: environments, animated set elements and props for the police film ("If A Police Officer Knocks...") and
the delivery film ("If A Delivery Driver Rings...", section at the end of this docstring).

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

DELIVERY FILM ("If A Delivery Driver Rings Your Doorbell At 3 AM... DON'T SIGN FOR IT"; full notes in SETS.md)
The police builders above take extra keyword args whose defaults keep the police film unchanged:
    porch_doorbell / porch_peephole(..., vehicle='patrol'|'van'|'wagon'|None, van=dict(driver, door, drive, head), hazard,
        box, tod='night'|'dawn', windows, era='now'|'memory');  street_wide(..., vehicle, van, hazard, era, upstairs_left)
    hallway(..., stairs=False, bowl='house', door_open=0 | f(t), outside=dict(tod, era, box, vehicle, van, hazard, car_X))
Delivery builders (police off, 3:07 AM defaults; all registered in SETS / build()):
    delivery_porch(view='doorbell'|'peephole', van, hazard=True, box=None|'door'|'boots'|dict(at, state, knock), ir, tod, era)
    delivery_street(van, hazard, era)      delivery_hall(stairs, bowl, lamp, door_open, outside)
    porch_doorway(tod='dawn'|'night', era, box, van, door_open)   memory_porch('doorway'|'street')   sunrise_porch('doorbell'|'doorway')
    hall_back(bowl, upstairs, hazard)      upstairs_hall(lily_door, window_open, hall_light, mom_door)
    lily_room(view='room'|'window', window_open, bed='sleeping'|'empty'|'made', hazard, drive)   side_yard(window_open, hazard)
    phone_bg(bg)  + app_phone(cv, screen, t, x, y, scale) on the HUD (APP_SCREENS)
    insert(name) with label, label_to, label_lily, tablet_sign, tablet_lily, key_bowl, key_bowl_dad, box_keys, van_seat,
        hazard_switch (prop_kw / motion as before; tablet / box_inside / keyring come from characters.py)
Timing helpers: hazard(t, rate, t_on, t_off) -> 0..1, hazard_ticks(t0, t1, ...) -> [(t, 'on'|'off')] (SFX), knock_pulse(times).
Drawing: delivery_van(pen, x, y, length, t, facing, wheel, bounce, pitch, hz, head, brake, driver, door), WINDOWS_3AM,
    doorway_camera(sp). Grades registered by name: 'dawn', 'memory', 'nightlight'.

DUMMY FILM ("If Your Grandpa's Ventriloquist Dummy Tells You A Joke... DON'T LAUGH"; section at the end; SETS.md)
Grandpa's house is ONE floor plan (HView: house coordinates x, Y, y in metres; every view is a camera placed in it), so
the kitchen seen from the hall, from the couch and from its own doorway is the same kitchen with the same chair. Light is
modelled: static layers are albedo x a light map (_lmap: ambient + lamps); a lamp that changes is a 'plus' layer whose
alpha is its level (engine Layer(blend='plus')), so flickers / lamps going out cost nothing.
    gp_hall(view='kitchen'|'door'|'stairs', light, kitchen, living, case='closed'|'open'|None, envelope, latch, den, clock,
            beam=dict(keys=[(t, x, y)], Y, aim, on), tod, steam, chair, mug, door)
        'kitchen': down the hall to the lit kitchen opening (Grandpa's chair: anchor 'kitchen_chair'), the bench with the
        case, the grandfather clock (pendulum_ticks()), the knee-high flashlight beam; 'door': toward the front door;
        'stairs': up the stairs (anchor 'step3').
    gp_kitchen(view='table'|'chair', kitchen, mug, steam, chair, tod='night'|'morning', sway)   anchors chair, chair_stand, table, mug
    gp_living(view='tv'|'couch', lamp, tv=dict(on, snow, mode, pulse), kitchen, content, tod)   the CRT shows the 1974 tape live
        (tv_level(sp.info['tv'], t) = the light it throws); anchors kitchen_chair, bookcase_top, couch_l/m/r, mom, window
    gp_den(lamp, hall, moon)     the armchair (anchor 'armchair'), the rug (anchor 'rug'), posters; lamp goes out: dict(out=...)
    gp_studio(view='full'|'close', laugh=laugh_waves([...]), applause, vhs, bezel, track)   1974 'Saturday Morning with
        Walter Kemp' full frame through engine.post fx['vhs'] (wobble, tracking band, chroma, CRT curve); anchors stool, knee
    studio_content(figures, laugh) -> content f(pen, W, H, t) for a CRT face (gp_living(content=...))
    hospital(view='bed'|'close', bpm, flat, light, hall)   live ECG; monitor_beeps(t0, t1, bpm, flat); anchors bed_head, bed_lap, chair
    museum(view='case'|'wide', spot)   the vitrine (glass layer in front of anchor 'display'), the plaque
    street_morning(view='window'|'outside', van=dict(drive=('out', t0, t1, x0, x1)))   8 AM, museum_van(); anchors owen / owen_window
    stage_1962(spot, curtain)    sepia first show (grade 'memory');   bedroom_doorway(hall, door)   anchor 'doorway' (backlit)
    insert(name) / gp_insert(name, ...) for GP_INSERTS: letter (prop_kw hl=n, smear, show), letter_close, envelope, ps, latches
        (latch), case_open (warm), mug (stir=f(t)), back_slot (hand, paper), squeeze (squeeze=squeeze_pulses([...]), take),
        family_photo, poster_1962, vcr (tape, play)
    rule_card_lie(cv, n, text, t, reveal, mode='tear'|'smear'|'flicker') on the HUD: the rule card that lies.
    shaky_text(pen, s, x, y, size, ...) Grandpa's shaky hand (steady=True: the hand that changed rule six).
Grades registered: gp_house, gp_dark, tv_glow, hospital, vhs74, museum, morning. Every view lists its safe camera
envelope in info['cam_env'] (checked by tools/sets_sheet.py --frame).
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


def curtain_gust(t, seed=0):
    """0..1 gust strength of a night draught through an open window (slow swells with quicker flutters)."""
    return clamp(0.5 + 0.42 * noise1(t * 0.55, seed + 70) + 0.22 * noise1(t * 1.7, seed + 71))


def _curtain_billow(pen, x, y, w, h, t, side=-1, c='#9a7ab0', amt=1.0, seed=0, lit=None, folds=5):
    """A curtain panel at an OPEN window, blown into the room: hung from (x, y), width w, height h, gathered on its outer
    side (side -1 = the left panel, its free edge on the right). The draught lifts the hem (up to ~30 % of h), swings the
    free edge across the opening and bellies the cloth toward the camera (a lit inner face shows on the bulge)."""
    g = curtain_gust(t, seed) * amt
    n = 14
    top = [(x + w * i / n, y) for i in range(n + 1)]
    bot = []
    for i in range(n + 1):
        u = i / n
        fr = u if side < 0 else 1 - u                                   # 0 at the gathered edge, 1 at the free edge
        lift = g * h * (0.08 + 0.26 * fr ** 1.3)
        swing = -side * g * w * (0.15 + 0.55 * fr) + w * 0.12 * g * noise1(t * 1.6 + u * 1.2, seed + 5)
        wave = 9.0 * g * math.sin(u * 3.0 * math.pi - t * 5.2 + seed) + 5.0 * noise1(t * 2.3 + u * 3.0, seed + 9)
        bot.append((x + w * u + swing, y + h - lift + wave))
    # the free edge bows inward (into the room) as the panel bellies
    edge_i = n if side < 0 else 0
    ex0, ey0 = top[edge_i]; ex1, ey1 = bot[edge_i]
    belly = -side * g * w * 0.45
    mid = [((ex0 + ex1) / 2 + belly + 4 * noise1(t * 1.9, seed + 11), (ey0 + ey1) / 2)]
    if side < 0:
        pts = top + mid + bot[::-1]
    else:
        pts = mid + top + bot[::-1]
    path = smooth(pts, True, 0.55)
    dk = _darken(c, 0.28)
    pen.linear(path, x, 0, x + w, 0, [c, dk] * (folds // 2) + [c])
    for i in range(1, folds):                                           # fold lines follow the blown hem
        j = int(round(i / folds * n))
        a_ = top[j]; b_ = bot[j]
        cx_ = (a_[0] + b_[0]) / 2 + belly * 0.4 * (j / n if side < 0 else 1 - j / n)
        pen.line(smooth([a_, (cx_, (a_[1] + b_[1]) / 2), b_], False), max(2, w * 0.012), _darken(c, 0.45), 170)
    if g > 0.05:                                                        # the bulge catches the light: the cloth's inner face
        bx = (ex0 + ex1) / 2 + belly * 0.6 - side * w * 0.18
        by = (ey0 + ey1) / 2 + h * 0.08
        pen.radial(path, bx, by, w * 0.9, [(0, _lighten(c, 0.35), 150 * min(1.0, g)), (1, _lighten(c, 0.35), 0)], sy=1.8)
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
        info['doorway_cam'] = (dx + dw / 2, dy + dh * 0.52, 1.3, 1.0)         # (x, y, dolly zoom, optical factor)
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
    if name in GP_INSERTS: return gp_insert(name, t0, prop_kw, motion, hand, bg_dim)
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
    anchors['box_door'] = v.anchor(-0.8, 0.84, note='the box against the front door (its street face)')
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
    if at == 'door': b.setdefault('X', -0.8); b.setdefault('Dn', 0.42); b.setdefault('label', 'near')     # fix 3: in the lens, in focus, label to the camera
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
    for l in L:                                          # dynamic outside layers stay sharp (no per-frame DOF blur)
        if not l.cache: l.blur = 0
    if tod == 'dawn':                                    # daylight outside vs the dark hall
        for l in L:
            if l.name != 'box': l.tint = ('#ffe9da', 0.95)
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
        q = v.quad([(-0.46, 0.002, Db), (0.46, 0.002, Db), (0.95, 0.002, Db * 0.47), (-0.75, 0.002, Db * 0.47)])
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
        pen.fill(q, '#04050c', 175 * (1 - clamp(th * 1.6)))                       # fix 3: the leaf in the dark hall's shadow
        if th > 0.005:
            pen.fill(q, '#000000', 80 * clamp(th * 3))
            gx = tr[0]                                                            # the lit crack: a thin bright slit
            slit = poly([tr, (dx1, dy0), (dx1, dy1), br])
            pen.fill(slit, MOON_GLOW, 235 * clamp(1.4 - th))
            pen.glow((tr[0] + dx1) / 2, (dy0 + dy1) / 2, max(8.0, (dx1 - tr[0]) * 2.5), MOON_GLOW, 90 * clamp(1.4 - th))
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
        if window_open:                                     # lower sash raised all the way: a black night gap below
            gy = wy0 + (wy1 - wy0) * 0.46                   # the raised sash's bottom rail
            gap = rect(wx0, gy, wx1 - wx0, wy1 - gy)
            pen.linear(gap, 0, gy, 0, wy1, [(0, '#02030a', 225), (0.7, '#05070f', 205), (1, '#0a0f22', 190)])
            pen.linear(rect(wx0, wy1 - 26, wx1 - wx0, 26), 0, wy1 - 26, 0, wy1, [(0, '#7a9ae0', 0), (1, '#7a9ae0', 70)])   # cold sill light
            gl = rect(wx0, wy0, wx1 - wx0, gy - wy0)        # two sashes of glass overlapped above it
            pen.fill(gl, '#b8c8ec', 46)
            pen.fill(poly([(wx0 + 20, gy - 6), (wx0 + 62, gy - 6), (wx0 + 118, wy0 + 6), (wx0 + 76, wy0 + 6)]), '#e6eeff', 40)
            pen.line(rect(wx0 + 5, wy0 + 5, wx1 - wx0 - 10, gy - wy0 - 5), 9, '#d8d0e0')
            pen.seg(((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, gy), 8, '#d8d0e0')
            pen.seg((wx0, gy), (wx1, gy), 16, '#d8d0e0'); pen.seg((wx0, gy + 8), (wx1, gy + 8), 3, LINE)
            pen.seg((wx0 + 12, gy - 14), (wx1 - 12, gy - 14), 3, '#a89eb8')
            for ex in (wx0 + 3, wx1 - 3):                    # the empty side tracks of the open sash
                pen.seg((ex, gy + 10), (ex, wy1), 5, '#bdb4c8')
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
            if window_open:                                  # the night air blows them into the room
                _curtain_billow(pen, x_, wy0 - 44, cw, (wy1 - wy0) + 150, t, side, '#9a7ab0', curtains * wind, 31 + side,
                                lit=(MOON_GLOW, 60) if side < 0 else ('#c8d6ff', 50))
            else:
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
            if bed in ('sleeping', 'awake'):         # Lily in bed: a curled shape under the covers, her head on the pillow
                cx_, cy_ = v.p((X0 + X1) / 2 + 0.06, Yq + 0.1, 2.5); ks = v.s(2.5)
                mound = _blob(cx_, cy_, 0.36 * ks, 0.15 * ks, 11, 8, 0.12)
                pen.fill(mound, '#3a4a8a'); pen.linear(mound, 0, cy_ - 0.15 * ks, 0, cy_ + 0.15 * ks, [(0, '#8a9ae0', 90), (1, '#000000', 60)])
                pen.line(mound, 2.5, LINE)
                # review 4: she must read as a sleeping child (the bed read empty before "her bed is empty"): her hair
                # fanned on the pillow, her face (eyes shut) above the quilt's edge, the quilt pulled up to her chin
                hs = v.s(D0 - 0.3)
                hx, hy = v.p((X0 + X1) / 2 + 0.04, Ym + 0.2, D0 - 0.3)
                pen.fill(_blob(hx, hy - 0.02 * hs, 0.16 * hs, 0.1 * hs, 9, 3, 0.2), '#6a4430'); pen.line(_blob(hx, hy - 0.02 * hs, 0.16 * hs, 0.1 * hs, 9, 3, 0.2), 2, LINE, 180)
                fx_, fy_ = hx + 0.01 * hs, hy + 0.045 * hs
                face = oval(fx_, fy_, 0.085 * hs, 0.06 * hs)
                pen.fill(face, '#d6b6a6'); pen.line(face, 2, LINE, 200)
                pen.fill(_blob(fx_, fy_ - 0.05 * hs, 0.09 * hs, 0.035 * hs, 7, 5, 0.2), '#6a4430')        # her fringe
                for e in (-1, 1):                    # eyes shut ('sleeping') / wide open, looking toward the vent ('awake')
                    if bed == 'awake':
                        pen.fill(oval(fx_ + e * 0.035 * hs, fy_ + 0.006 * hs, 0.02 * hs, 0.017 * hs), '#f4f0f0')
                        pen.fill(oval(fx_ + e * 0.035 * hs + 0.008 * hs, fy_ + 0.007 * hs, 0.009 * hs), '#1a1418')
                        pen.line(oval(fx_ + e * 0.035 * hs, fy_ + 0.006 * hs, 0.02 * hs, 0.017 * hs), 1.5, LINE, 220)
                    else:
                        pen.line(smooth([(fx_ + e * 0.035 * hs - 0.016 * hs, fy_ + 0.004 * hs), (fx_ + e * 0.035 * hs, fy_ + 0.013 * hs),
                                         (fx_ + e * 0.035 * hs + 0.016 * hs, fy_ + 0.004 * hs)], False), 2, '#3a2418')
                pen.fill(oval(fx_, fy_ + 0.075 * hs, 0.13 * hs, 0.03 * hs), '#3a4a8a'); pen.line(smooth([(fx_ - 0.13 * hs, fy_ + 0.07 * hs), (fx_, fy_ + 0.05 * hs), (fx_ + 0.13 * hs, fy_ + 0.07 * hs)], False), 2.5, LINE)   # the quilt's edge at her chin
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
         _cl(2.0, bed_layer, 'bed', _key('lr', 'bed3', bed), (box[0], v.y(1.3, Db), v.x(0.0, 1.35), box[3])),
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


_PHOTO341 = {}


def photo_lily_scene():
    """The 3:41 delivery photo as one scene, shared by the in-app thumbnail and the film's full-screen photo shots.
    side_yard from the grass, flash-lit: Lily (8) in the open lower sash, leaning out on the sill, one small hand reaching a
    short way out and down onto the tablet's signature box; the driver in the foreground from behind (cap, shoulders at
    the bottom of the frame), his arm raised in a plain overhead reach, holding the glowing tablet up to her sill (the low
    camera makes the reach read; no stretched limbs), his head turned over his shoulder so one eye and the grin catch the
    flash. Returns dict(draw=fn(pen, t) in set design coords 1920x1080, crops={full, lily, arm, finger} (16:9 design rects),
    tablet=(x, y), window=(x0, y0, x1, y1))."""
    if 'scene' in _PHOTO341: return _PHOTO341['scene']
    CH = _CH()
    sp = side_yard(window_open=True, hazard=lambda t: 1.0)
    wx0, wy0, wx1, wy1 = sp.info['window']
    oy0 = wy0 + (wy1 - wy0) * 0.47                                     # the raised lower sash
    LB = dict(cx=(wx0 + wx1) / 2 - 10, cy=oy0 + (wy1 - oy0) * 0.52, scale=0.1)
    LP = CH.Pose(lean=0.35, h_nod=0.3, h_tilt=-6.0, hl_out=34.0, hl_down=78.0, hl_fwd=210.0, hl_shape='point',
                 hr_out=20.0, hr_down=200.0, hr_fwd=120.0, hr_shape='open', brow_sad=0.25, brow_up=0.35, smile=0.12, pupil=1.15,
                 look_x=0.55, look_y=0.85, lock=0.0) if CH else None
    if CH:
        _, tip = CH.hand_pos('lily', LP, 1, **LB)
    else:
        tip = ((wx0 + wx1) / 2 + 30, wy1 + 20)
    TAB = 70.0
    tx, ty = tip[0] + 0.12 * TAB, tip[1]                              # her fingertip lands on the signature box
    # fix 3: the driver stands ON the wheelie bin against the wall under her window (1 m up), so a man of 1.8 m reaches the
    # tablet with a bent arm (shoulder, elbow, a forearm of natural length): no stretched limbs, the geometry holds
    vw = sp.info['view']
    DD, BIN_Y = 3.08, 0.98                                             # his depth (just off the wall) and the bin lid height
    DRH = 1.8 * vw.s(DD)
    gx, gy = tx, ty + 0.42 * TAB                                       # his grip under the tablet
    XD = (gx - 960.0) / vw.s(DD) + 0.36                                # his centre: right of the grip, the arm reaches up-left
    dx_, dy_ = vw.p(XD, BIN_Y, DD)
    DP = CH.Pose(turn=2.0, h_turn=-1.8, lean=-0.05, hl_out=40.0, hl_down=-200.0, hl_fwd=60.0, hl_up=0.0, hl_shape='grip',
                 hr_out=14.0, hr_down=330.0, hr_fwd=24.0, smile=1.0, grin=1.0, teeth=1.0, lock=1.0, look_x=-0.6) if CH else None
    if CH:                                                             # solve the reach (Gauss-Newton on out / down)
        for _ in range(8):
            w0, _t = CH.hand_pos('driver', DP, 1, x=dx_, y_feet=dy_, height=DRH)
            ex_, ey_ = gx - w0[0], gy - w0[1]
            if abs(ex_) + abs(ey_) < 0.5: break
            J = []
            for key in ('hl_out', 'hl_down'):
                v0 = getattr(DP, key); setattr(DP, key, v0 + 5.0)
                w1, _t = CH.hand_pos('driver', DP, 1, x=dx_, y_feet=dy_, height=DRH)
                setattr(DP, key, v0)
                J.append(((w1[0] - w0[0]) / 5.0, (w1[1] - w0[1]) / 5.0))
            det = J[0][0] * J[1][1] - J[1][0] * J[0][1]
            if abs(det) < 1e-9: break
            d_out = (ex_ * J[1][1] - ey_ * J[1][0]) / det
            d_down = (J[0][0] * ey_ - J[0][1] * ex_) / det
            DP.hl_out += d_out; DP.hl_down += d_down
    lit = dict(rim='#e8f0ff', rim_a=150, side=1, key=-0.1)

    def window_in(pen, t):                                             # her room through the window (no curtain here)
        q = rect(wx0, wy0, wx1 - wx0, wy1 - wy0)
        pen.radial(q, (wx0 + wx1) / 2 - 30, wy1 - 20, (wx1 - wx0) * 0.95, [(0, '#fff0c8'), (0.55, '#b8a8a8'), (1, '#3a3450')])
        pen.fill(rect(wx0, wy0, wx1 - wx0, (wy1 - wy0) * 0.35), '#4a3e5e', 150)
        _glow_stars(pen, lambda r: (wx0 + r.uniform(0.1, 0.9) * (wx1 - wx0), wy0 + r.uniform(0.05, 0.3) * (wy1 - wy0), 5), 6, 13, 160)
        pen.fill(rect(wx0, wy0, wx1 - wx0, oy0 - wy0), '#9aa6c8', 36)
        for sd in (-1, 1):                                             # her curtains pushed to the jambs, lifting in the draught
            x0 = wx0 if sd < 0 else wx1
            cur = smooth([(x0, oy0), (x0 - sd * 0.16 * (wx1 - wx0), oy0), (x0 - sd * 0.12 * (wx1 - wx0), oy0 + (wy1 - oy0) * 0.6),
                          (x0 - sd * 0.2 * (wx1 - wx0), wy1), (x0, wy1)], True, 0.6)
            pen.fill(cur, '#b9a6d4', 230); pen.line(cur, 2, LINE, 200)
        pen.radial(None, (wx0 + wx1) / 2, (wy0 + wy1) / 2, (wx1 - wx0) * 1.3, [(0, '#fff0c8', 46), (1, '#fff0c8', 0)], clip=False)

    def sash(pen, t):                                                  # the raised lower sash, in front of her room
        pen.seg((wx0, oy0), (wx1, oy0), 14, '#a8a294'); pen.seg((wx0, oy0 + 7), (wx1, oy0 + 7), 3, LINE)

    def lily(pen):
        cv = pen.cv
        cv.save(); cv.clipPath(rect(wx0, oy0 + 6, wx1 - wx0, wy1 + 14 - oy0 - 6), skia.ClipOp.kIntersect, True)
        CH.draw_bust(pen, 'lily', LB['cx'], LB['cy'], LB['scale'], LP, light=lit)
        cv.restore()

    def wheelie_bin(pen):                                              # the green wheelie bin he climbed on (lid at 0.98 m)
        bs = vw.s(DD + 0.05)
        bx, by = vw.p(XD, 0.0, DD + 0.05); ty_ = vw.y(BIN_Y, DD + 0.05)
        body = poly([(bx - 0.31 * bs, ty_ + 0.04 * bs), (bx + 0.31 * bs, ty_ + 0.04 * bs), (bx + 0.27 * bs, by), (bx - 0.27 * bs, by)])
        pen.fill(body, '#1c3a2a'); pen.linear(body, bx - 0.31 * bs, 0, bx + 0.31 * bs, 0, [(0, '#000000', 70), (0.4, '#7fd0a0', 26), (1, '#000000', 110)])
        for k in range(1, 4): pen.seg((bx - 0.28 * bs + k * 0.14 * bs, ty_ + 0.14 * bs), (bx - 0.25 * bs + k * 0.13 * bs, by - 0.08 * bs), 2.5, '#0e2016', 200)
        pen.line(body, 3, LINE)
        lid = rrect(bx - 0.35 * bs, ty_ - 0.02 * bs, 0.7 * bs, 0.08 * bs, 0.02 * bs)
        pen.fill(lid, '#24483a'); pen.fill(rect(bx - 0.35 * bs, ty_ - 0.02 * bs, 0.7 * bs, 0.02 * bs), '#9ad8b4', 70); pen.line(lid, 3, LINE)
        pen.radial(None, bx, ty_, 0.9 * bs, [(0, '#e8f0ff', 60), (1, '#e8f0ff', 0)], sy=0.5, clip=False)     # the flash on the lid

    def front(pen):
        wheelie_bin(pen)
        pen.glow(tx, ty, TAB * 1.7, '#e8f0ff', 150)
        CH.draw(pen, 'driver', dx_, dy_, DRH, DP, light=dict(rim='#ffa31f', rim_a=150, side=1, key=-0.45))
        CH.draw_tablet(pen, tx, ty, TAB, screen='sign', sig='lily', ink=0.4, ts='3:41 AM', angle=-6)
        # review 4: the flash flares off the tablet's glass right over the signature box, so the photo never spells her
        # name (the reveal is "the signature reads... Lily" at 571 s, on the tablet insert); her finger stays on top
        sgx, sgy = tx + 0.5, ty - 3.5
        pen.radial(None, sgx - 2, sgy, 19, [(0, '#ffffff', 252), (0.45, '#f6f9ff', 230), (0.8, '#e8f0ff', 90), (1, '#e8f0ff', 0)], sy=0.62, clip=False)
        pen.cv.save(); pen.cv.rotate(-6, tx, ty)
        pen.fill(poly([(tx - 18, ty - 20), (tx - 9, ty - 20), (tx + 15, ty + 10), (tx + 6, ty + 10)]), '#ffffff', 120)   # a specular streak
        pen.cv.restore()
        CH.draw_hand(pen, 'driver', gx, gy + 8, TAB * 0.5, 'grip', 180.0, 1)
        CH.draw_arm(pen, 'lily', 1, LP, light=lit, **LB)

    def draw(pen, t=0.0):
        figs = [(3.391, lambda p_: window_in(p_, t)), (3.386, lily), (3.385, lambda p_: sash(p_, t))] + ([(1.0, front)] if CH else [])
        _set_snapshot(pen, sp, 0, 0, 1920, 1080, (0, 0, 1920, 1080), figs, t=t, exclude=('lily_window',))

    def c169(x, y, w): return (x, y, x + w, y + w * 9.0 / 16.0)
    hx_, hy_ = dx_, dy_ - DRH * 0.91                                   # his head (for framing the grin)
    crops = {'full': c169(450, 440, 1060), 'lily': c169(wx0 - 130, wy0 - 40, 420), 'arm': c169(tx - 270, ty - 140, 520),
             'finger': c169(tx - 125, ty - 92, 250)}
    sc = dict(draw=draw, crops=crops, tablet=(tx, ty), window=(wx0, wy0, wx1, wy1), head=(hx_, hy_), driver_h=DRH)
    _PHOTO341['scene'] = sc
    return sc


def _photo_lily_art(p_, w, h):
    """3:41 AM, from below (photo_lily_scene, cropped for the app's photo box)."""
    sc = photo_lily_scene()
    x0, y0, x1, y1 = sc['crops']['full']
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    hw = (y1 - y0) / 2 * w / h if w / h < (x1 - x0) / (y1 - y0) else (x1 - x0) / 2
    hh = hw * h / w
    cv = p_.cv
    cv.save(); cv.clipPath(rect(0, 0, w, h), skia.ClipOp.kIntersect, True)
    cv.scale(w / (2 * hw), h / (2 * hh)); cv.translate(-(cx - hw), -(cy - hh))
    sc['draw'](p_, 0.0)
    cv.restore()
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
              photo_k=1.0, notify_k=None, sig_k=1.0):
    """The delivery app on the police phone (same body, glass, hand hook engine.hud._hand, palette and fonts as
    hud.phone), drawn on the HUD canvas. screen (t = seconds since this screen appeared):
      'notify_delivered'  lock screen 3:07, banner 'Your package has been delivered.'
      'order'             ORDER DETAILS: 1 item, SIGNATURE REQUIRED, Recipient: This address, Sender: RETURN
      'notify_photo'      lock screen 3:11, banner 'Delivery photo added.'
      'photo_hall'        DELIVERY PHOTO 3:11 AM: you from behind in the front hall, lit by your screen (photo_k fades it in)
      'photo_gone'        the same item: 'No delivery photo on file.' (the photo never existed)
      'attempted'         Delivery attempted / Package left at door / Return pickup scheduled for 6:12 a.m. (tracker)
      'notify_return'     lock screen 3:41, banner 'Return complete.'
      'photo_lily'        DELIVERY PHOTO 3:41 AM from below: Lily signing at her window; Signed by: 'Lily.' (child's hand);
                          sig_k 0 = only the photo and 'Return complete' (the name stays hidden until the narrator reads it),
                          0..1 = the SIGNED BY row slides up with an empty signature line, 1 = the name written in
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
                rk = clamp(sig_k * 2.0)                                   # the SIGNED BY row comes in, then the name
                ko = clamp(rk * 2.0); rk = clamp(rk * 2.0 - 1.0)          # (the big 'Return complete' goes first)
                if ko < 1:
                    T('Return complete', yy + 6, 15, NL_AMBER, 800, 0.0, aa=1 - ko)
                if rk > 0:
                    cv.save(); cv.translate(0, 18 * (1 - ease_out_cubic(rk)))
                    T('SIGNED BY', yy, 10, '#8a93ad', 700, 0.22, aa=rk)
                    pen.seg((-70, yy + 46), (70, yy + 46), 1.5, '#4a5068', a * rk)
                    if sig_k >= 0.999: _child_hand(pen, 'Lily.', -38, yy + 40, 30, a)
                    T('Return complete', yy + 72, 13, NL_AMBER, 800, 0.0, aa=rk)
                    cv.restore()
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


def porch_doorway(tod='dawn', era='now', box='door', van=None, hazard=True, door_open=0.92, car_X=2.2, wall='#3b3a48',
                  door_c='#4f2c20', lamp_spill=0.0):
    """The front door open onto the porch, from just inside the hall (camera 1.45 m from the door: the doorway fills the
    frame height): the hall's damask wall and wainscot around the casing, the transom, the stairs' newel and first
    balusters on the left, the door leaf swung in (door_open 0..1 or f(t) animates it), the porch world beyond with the
    box at the threshold (backlit at night: a tall dark shape in the doorway) and the van.
    tod 'dawn' (6:12: your mother opens the door; box=dict(state='open'), the tape cut; daylight pours in across the
    floor; no van by default), 'night' (3 AM), era 'memory' (21 years ago, grade 'memory': dad goes out to sign).
    Anchors: porch_out (just outside), threshold (inside, at the door), hall_near (beside the camera)."""
    if van is None: van = (tod != 'dawn')
    vehicle = 'van' if van else None
    bx = box if not (tod == 'dawn' and box == 'door') else dict(at='door', state='open')
    v = View(620, 430, 1.5)
    Db, Dn, HW, CH = 1.45, 0.4, 1.35, 2.5
    box_ = FRAME
    s_ = v.s(Db)
    dw, dh = 0.92 * s_, 2.05 * s_
    dx, dy = v.x(-0.46, Db), v.gy(Db) - dh
    th_fn = door_open if callable(door_open) else (lambda t: float(door_open))

    def front(pen, t):
        wall_p = minus(v.quad([(-HW, 0, Db), (HW, 0, Db), (HW, CH, Db), (-HW, CH, Db)]), rect(dx, dy, dw, dh))
        x0, y0 = v.p(-HW, CH, Db); x1, y1 = v.p(HW, 0, Db)
        cv = pen.cv; cv.save(); cv.clipPath(wall_p, skia.ClipOp.kIntersect, True)
        _wallpaper(pen, wall_p, (x0, y0, x1, y1), s_, wall, _darken(wall, 0.3), 'damask', 170)
        pen.linear(wall_p, 0, y0, 0, y1, [(0, '#000000', 90), (0.5, '#000000', 0), (1, '#000000', 60)])
        pen.linear(v.quad([(-HW, 0, Db), (HW, 0, Db), (HW, 0.9, Db), (-HW, 0.9, Db)]), 0, v.y(0.9, Db), 0, v.gy(Db), ['#2a2626', '#1c1919'])
        for X0 in (-HW + 0.08, 0.6):
            pen.line(v.quad([(X0, 0.14, Db), (X0 + 0.45, 0.14, Db), (X0 + 0.45, 0.78, Db), (X0, 0.78, Db)]), 3, '#0e0c0c', 200)
        pen.fill(v.quad([(-HW, 0.88, Db), (HW, 0.88, Db), (HW, 0.94, Db), (-HW, 0.94, Db)]), '#4a4440')
        pen.fill(v.quad([(-HW, 0, Db), (HW, 0, Db), (HW, 0.12, Db), (-HW, 0.12, Db)]), '#2e2a28')
        cv.restore()
        tx0, ty0 = v.p(-0.46, 2.36, Db); tx1, ty1 = v.p(0.46, 2.14, Db)                       # transom
        pen.shape(rect(tx0 - 10, ty0 - 10, tx1 - tx0 + 20, ty1 - ty0 + 20), '#b8b0a0', 3)
        lc = '#ffe6cc' if tod == 'dawn' else '#ffd9a0'
        pen.radial(rect(tx0, ty0, tx1 - tx0, ty1 - ty0), (tx0 + tx1) / 2 - 60, ty1, (tx1 - tx0) * 0.7, [(0, lc), (1, mix('#141a28', lc, 0.5))])
        for k in range(1, 4): pen.seg((tx0 + (tx1 - tx0) * k / 4, ty0), (tx0 + (tx1 - tx0) * k / 4, ty1), 5, '#b8b0a0')
        tw = 0.09 * s_
        pen.shape(minus(rect(dx - tw, dy - tw, dw + 2 * tw, dh + tw), rect(dx, dy, dw, dh)), '#b8b0a0', 2.5)
        pen.fill(rect(dx, dy, 0.035 * s_, dh), '#6a5e50'); pen.fill(rect(dx + dw - 0.035 * s_, dy, 0.035 * s_, dh), '#8a7e6e')
        pen.fill(rect(dx, dy, dw, 0.03 * s_), '#5a5044'); pen.fill(rect(dx, dy + dh - 0.02 * s_, dw, 0.02 * s_), '#8a7a5a')
        sx_, sy_ = v.p(0.68, 1.25, Db)
        pen.shape(rrect(sx_, sy_, 0.08 * s_, 0.12 * s_, 4), '#cfc8b8', 2.5); pen.fill(rect(sx_ + 0.03 * s_, sy_ + 0.035 * s_, 0.02 * s_, 0.05 * s_), '#9a9488')

    def sides(pen, t):
        _side_wall(pen, v, -HW, Db, Dn, 0, CH, wall, _darken(wall, 0.3), 'dots', 150, wains=0.9, wc='#2a2626')
        _side_wall(pen, v, HW, Db, Dn, 0, CH, wall, _darken(wall, 0.3), 'dots', 150, wains=0.9, wc='#2a2626')
        ceil = v.quad([(-HW, CH, Db), (HW, CH, Db), (HW, CH, Dn), (-HW, CH, Dn)])
        pen.linear(ceil, 0, v.y(CH, Dn), 0, v.y(CH, Db), ['#08080b', '#1a1a20'])
        _floorboards(pen, v, -HW, HW, Db, Dn, '#33261c', '#1a120c')
        _rug(pen, v, -0.5, 0.5, Db - 0.06, Dn, '#4a1e22', '#1e0c0e', '#9a7a42')

    def stairs(pen, t):
        _hall_stairs_side(pen, v, -HW, -0.55, Db - 0.16, Dn, CH, wall, Dend=Dn + 0.02)

    L = [_cl(Db, front, 'front_wall', _key('pdw', 'front', wall, tod), (v.x(-HW, Db) - 30, v.y(CH, Db) - 30, v.x(HW, Db) + 30, v.gy(Db) + 30)),
         _cl(1.0, sides, 'walls', _key('pdw', 'sides', wall), box_),
         _cl(0.8, stairs, 'stairs', _key('pdw', 'stairs', wall), (box_[0], box_[1], v.x(-0.3, Db), box_[3]))]
    _exposure(L, 0.32, ('front_wall', 'walls', 'stairs'))
    L += _hall_doorway_layers(v, Db, dx, dy, dw, dh, door_c, th_fn,
                              dict(tod=tod, era=era, box=bx, vehicle=vehicle, van=van if isinstance(van, dict) else None, hazard=hazard,
                                   car_X=car_X), CH)
    if lamp_spill > 0.01:
        L.append(Layer(0.9, lambda pen, t: pen.radial(None, box_[2], v.y(1.2, 0.9), 900, [(0, '#ffcf8f', 60 * lamp_spill), (1, '#ffcf8f', 0)],
                                                      clip=False), 'lamp_spill', blur=0))
    grade = 'memory' if era == 'memory' else (Grade('interior_dim').lerp('dawn', 0.45) if tod == 'dawn' else 'interior_dim')
    a = {'porch_out': v.anchor(0.1, Db + 0.9, note='on the porch just outside the doorway (seen through it)'),
         'threshold': v.anchor(0.05, Db - 0.25, note='inside, at the open door'), 'hall_near': v.anchor(0.55, 0.85, note='beside the camera')}
    return SetPiece('porch_doorway', L, a, {}, lens=None, grade=grade, focus=Db, dof=1.2, cover=FRAME,
                    info={'view': v, 'door_open': th_fn, 'door_rect': (dx, dy, dw, dh), 'hazard': _hazard_fn(hazard) if van else (lambda t: 0.0)})


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
    """A slow dolly push toward the open front door of hallway(door_open=...) from info['doorway_cam'] (the far hall
    view; for the doorway filling the frame use porch_doorway(), whose home camera frames it: an optical punch-in on the
    frame-sized hall layers would blow the layer cache at 2560)."""
    from engine.camera import push_in as _push
    x, y, z, f = sp.info.get('doorway_cam', (960, 540, 1.0, 1.0))
    c = _push(t0, t1, x, y, z, rate=rate, shake=shake)
    return c.snap(t0 - 1.0, f, 0.001) if f > 1.0 else c


__all__ += ['doorway_camera']


# ######################################################################################################################
# DUMMY FILM: "If Your Grandpa's Ventriloquist Dummy Tells You A Joke... DON'T LAUGH"   (SETS.md, section "Dummy film")
# Grandpa Walter Kemp's old house at night, laid out on ONE floor plan (every view is a camera placed in it, so the
# kitchen seen from the hall, from the couch and from its own doorway is the same kitchen), the hospital room, the 1974
# TV studio (on the CRT in the living room and full frame through engine.post fx['vhs']), the 1962 stage, the museum,
# the street at 8 AM, your bedroom doorway, the inserts and the torn rule card. Light is modelled, not painted: every
# static layer is drawn as albedo and multiplied by a light map (ambient + lamps); a lamp that changes (the hall light,
# the living-room lamp that flickers, the den lamp that goes out) is its own 'plus' layer (albedo x that lamp) whose
# alpha is the lamp's level, so lights add up exactly and a flicker costs nothing.
# ######################################################################################################################

_epost.GRADES.setdefault('gp_house', dict(contrast=1.07, pivot=0.24, gamma=1.0, sat=1.1, wb=(1.03, 1.0, 0.96), floor='#090a12',
                                         bloom=0.75, bloom_thr=228, vignette=0.4, grain=0.7, shoulder=0.45))
_epost.GRADES.setdefault('gp_dark', dict(contrast=1.05, pivot=0.24, gamma=0.97, sat=1.05, wb=(0.96, 0.99, 1.08), floor='#06070e',
                                        bloom=0.85, bloom_thr=226, vignette=0.36, grain=0.8, shoulder=0.45))
_epost.GRADES.setdefault('tv_glow', dict(contrast=1.06, pivot=0.24, gamma=1.0, sat=1.05, wb=(0.93, 1.0, 1.1), floor='#070912',
                                        bloom=0.9, bloom_thr=224, vignette=0.38, grain=0.8, shoulder=0.45))
_epost.GRADES.setdefault('hospital', dict(contrast=1.02, pivot=0.25, gamma=1.0, sat=0.72, wb=(0.93, 1.03, 1.03), floor='#091013',
                                         bloom=0.6, bloom_thr=232, vignette=0.42, grain=0.9, shoulder=0.5))
_epost.GRADES.setdefault('vhs74', dict(exposure=0.08, contrast=0.94, pivot=0.3, gamma=1.04, sat=0.92, wb=(1.07, 1.0, 0.86), floor='#1a130f',
                                      bloom=0.9, bloom_thr=222, vignette=0.6, grain=0.0, soft=0.6, shoulder=0.55))
_epost.GRADES.setdefault('museum', dict(contrast=1.1, pivot=0.24, gamma=0.98, sat=0.98, wb=(0.98, 1.0, 1.04), floor='#05070a',
                                       bloom=0.75, bloom_thr=228, vignette=0.32, grain=0.6, shoulder=0.5))
_epost.GRADES.setdefault('morning', dict(exposure=0.2, contrast=1.0, pivot=0.25, gamma=1.05, sat=0.9, wb=(0.99, 1.0, 1.04),
                                        floor='#0f1116', bloom=0.6, bloom_thr=232, vignette=0.45, grain=0.5, shoulder=0.5))

GP_AMB = '#2c3550'           # the house at night: moonlit navy ambient (multiplies the albedo)
GP_LAMP = '#ffcf94'          # tungsten lamps
GP_KLAMP = '#ffbf6a'         # the kitchen pendant through amber glass
GP_MOON = '#6f84c4'
GP_TV = '#a8c8ff'            # CRT light
GP_WOOD, GP_WOOD_D = '#6a4126', '#3a2214'


class HView(View):
    """A camera placed on Grandpa's floor plan. House coordinates (metres): x right when facing the back of the house,
    y from the front wall toward the back, Y up from the floor. The camera stands at (cam_x, cam_y), eye cam_h, facing
    +1 (toward the back) or -1 (toward the front). Every View method takes HOUSE coordinates: p(x, Y, y), x(x, y),
    y(Y, y), s(y) (px per metre at that distance), quad([(x, Y, y), ...]), anchor(x, y, Y) (depth = distance)."""

    def __init__(self, S, horizon, cam_h, cam_x, cam_y, facing=1, cx=960.0):
        View.__init__(self, S, horizon, cam_h, cx)
        self.hx, self.hy, self.f = float(cam_x), float(cam_y), (1 if facing > 0 else -1)

    def d(self, y): return max(0.04, (y - self.hy) * self.f)

    def p(self, x, Y, y):
        k = self.S / self.d(y)
        return (self.cx + (x - self.hx) * self.f * k, self.h - (Y - self.cam_h) * k)

    def x(self, x, y): return self.cx + (x - self.hx) * self.f * self.S / self.d(y)

    def y(self, Y, y): return self.h - (Y - self.cam_h) * self.S / self.d(y)

    def s(self, y): return self.S / self.d(y)

    def gy(self, y): return self.y(0.0, y)

    def anchor(self, x, y, Y=0.0, note=''):
        px, py = self.p(x, Y, y); D = self.d(y)
        return Anchor(px, py, D, 1.85 * self.S / D, note)


# ---- the floor plan (metres; see HView)
HALL_X = (-1.35, 1.35); HALL_BACK = 6.0; CEIL = 2.6
STAIR_X = (0.5, 1.35); STAIR_Y0, STAIR_RISE, STAIR_RUN, STAIR_N = 0.9, 0.19, 0.26, 14
KOPEN = (-1.15, 0.25, 2.15)                  # the kitchen opening at the end of the hall (x0, x1, top)
LIV_X = (-6.0, -1.35); ARCH_Y = (3.4, 4.8); LDOOR = (-2.55, -1.6, 2.05)     # living room; arch from the hall; door to the kitchen
TV_X = (-5.25, -4.35); COUCH = (-4.75, -2.65, 1.5, 2.4); LWIN = (-4.6, -2.8); BOOK_X = (-5.9, -5.05)
KIT_X = (-5.6, 1.35); KIT_Y = (6.0, 10.0)
TABLE = (-1.5, -0.4, 7.8, 8.6, 0.76); GCHAIR = (-0.95, 8.85); PENDANT = (-0.95, 8.2, 1.62); KWIN = (-1.55, -0.35, 1.05, 2.0)
BENCH = (-1.35, -0.95, 1.45, 2.35, 0.46); CASE = (-1.31, -0.91, 1.5, 2.32, 0.46, 0.27)


def _kfn(spec, seed=0, default=1.0):
    """A light's level -> f(t) 0..1. spec: a number, f(t), None (= default), or dict(k=1.0, flick=[(t0, dur), ...] (flicker
    bursts), out=[(t0, t1), ...] (switched off / blown, ~60 ms bulb ramps), on=t (comes on at t), off=t (goes off at t),
    amount=1.0 (flicker depth))."""
    if spec is None: spec = default
    if callable(spec): return spec
    if not isinstance(spec, dict) or not any(spec.get(k_) is not None for k_ in ('flick', 'out', 'on', 'off')):
        v = float(spec.get('k', 1.0)) if isinstance(spec, dict) else float(spec)
        f0 = lambda t: v
        f0.const = v                                        # a steady light: _lit bakes it into the base layer
        return f0
    k = float(spec.get('k', 1.0)); fl = spec.get('flick'); outs = list(spec.get('out', ()))
    if spec.get('off') is not None: outs.append((spec['off'], 1e9))
    if spec.get('on') is not None: outs.append((-1e9, spec['on']))
    amt = spec.get('amount', 1.0)

    def f(t):
        v = k * (flicker(t, seed, amt, fl) if fl else 1.0)
        for (a, b) in outs:
            if a - 0.06 <= t <= b + 0.06:
                v *= 1.0 - clamp(min((t - a) / 0.06 + 1.0, (b - t) / 0.06 + 1.0))
        return v
    return f


_LMAP_POS = [0.0, 0.22, 0.5, 0.78, 1.0]
_LMAP_FALL = [1.0, 0.72, 0.36, 0.1, 0.0]


def _lmap(pen, hv, box, ambient, lights, k=1.0):
    """Multiply everything this layer has drawn so far by a light map: `ambient` (hex, the unlit level) plus lights
    [(x, Y, y, r_m, hex, k[, sy])] (house coordinates on the lit surface; radial falloff of radius r_m metres, sy squashes
    it: floor pools ~0.3). Alpha is kept (kModulate with an opaque map); a map value of 1 = the albedo itself."""
    cv = pen.cv
    x0, y0, x1, y1 = box
    cv.saveLayer(skia.Rect.MakeLTRB(x0, y0, x1, y1), skia.Paint(BlendMode=skia.BlendMode.kModulate))
    cv.drawColor(col(ambient))
    for L_ in lights:
        x, Y, y, r, c, kk = L_[:6]
        sy = L_[6] if len(L_) > 6 else 1.0
        if hv.d(y) <= 0.05: continue
        px, py = hv.p(x, Y, y); R = r * hv.s(y)
        a = clamp(kk * k, 0, 4)
        r_, g_, b_ = rgb(c)
        cs = [skia.Color(int(min(255, r_ * a * f)), int(min(255, g_ * a * f)), int(min(255, b_ * a * f)), 255) for f in _LMAP_FALL]
        m = skia.Matrix(); m.setScale(1.0, sy, px, py)
        sh = skia.GradientShader.MakeRadial(skia.Point(px, py), R, cs, _LMAP_POS, skia.TileMode.kClamp, 0, m)
        cv.drawRect(skia.Rect.MakeLTRB(px - R, py - R * sy, px + R, py + R * sy), skia.Paint(Shader=sh, BlendMode=skia.BlendMode.kPlus))
    cv.restore()


def _lit(depth, art, name, key, bounds, hv, ambient, lights, var=(), **kw):
    """Static lit layers for one piece of the set: the base layer = albedo x (ambient + constant lights), and for each
    variable light (vname, lights, f(t)) a 'plus' layer = albedo x that light, alpha = its level (cached; skipped at 0).
    A light whose level is steady (_kfn of a number: f.const) is baked into the base layer instead (one layer, cheap)."""
    lights = list(lights); dyn = []
    for (vn, vl, kf) in var:
        if not vl: continue
        c = getattr(kf, 'const', None)
        if c is None: dyn.append((vn, vl, kf)); continue
        key = key + ':%s=%.3f' % (vn, c)
        if c > 0.001: lights += [tuple(q[:5]) + (q[5] * c,) + tuple(q[6:]) for q in vl]

    def base(pen, t):
        art(pen); _lmap(pen, hv, bounds, ambient, lights)
    L = [Layer(depth, base, name, cache=key, bounds=bounds, **kw)]
    for (vn, vl, kf) in dyn:

        def add(pen, t, vl=vl):
            art(pen); _lmap(pen, hv, bounds, '#000000', vl)
        L.append(Layer(depth, add, name + ':' + vn, cache=key + ':' + vn, bounds=bounds, alpha=kf, blend='plus', **kw))
    return L


def _hface(pen, hv, tl, tr, br, bl, W, H, fn):
    """Draw fn(pen) in a flat W x H frame (cm, y down) mapped in perspective onto the house quad tl, tr, br, bl
    (each (x, Y, y))."""
    _draw_face(pen, W, H, [hv.p(*tl), hv.p(*tr), hv.p(*br), hv.p(*bl)], fn)


def _pattern(pen, W, H, kind, ink, a=150, seed=0):
    """Wallpaper motifs in a cm frame."""
    cv = pen.cv
    if kind == 'damask':
        dx, dy = 32.0, 40.0
        j = 0; y = 6.0
        while y < H + dy:
            x = (dx / 2 if j % 2 else 0.0) + 4.0
            while x < W + dx:
                m = smooth([(x, y - 12), (x + 6, y - 3), (x + 10, y + 2), (x + 3, y + 5), (x, y + 13), (x - 3, y + 5), (x - 10, y + 2),
                            (x - 6, y - 3)], True, 0.8)
                pen.fill(m, ink, a); pen.fill(oval(x, y - 18, 1.8), ink, a)
                pen.line(smooth([(x - 9, y + 14), (x, y + 19), (x + 9, y + 14)], False), 1.2, ink, a * 0.8)
                x += dx
            y += dy; j += 1
    elif kind == 'stripe':
        x = 0.0; k = 0
        while x < W:
            pen.fill(rect(x, 0, 5.0, H), ink, a * (0.55 if k % 2 else 1.0)); x += 15.0; k += 1
    elif kind == 'trellis':                                   # 70s mustard: small diamonds and dots
        y = 0.0; j = 0
        while y < H + 20:
            x = (10.0 if j % 2 else 0.0)
            while x < W + 20:
                pen.line(poly([(x, y - 9), (x + 7, y), (x, y + 9), (x - 7, y)]), 1.3, ink, a)
                pen.fill(oval(x, y, 1.6), ink, a)
                x += 20.0
            y += 18.0; j += 1
    elif kind == 'kitchen':                                   # cream with tiny teapots and sprigs
        rng = np.random.default_rng(seed)
        y = 10.0; j = 0
        while y < H + 30:
            x = (17.0 if j % 2 else 3.0)
            while x < W + 30:
                if (int(x) + j) % 3 == 0:
                    pen.fill(oval(x, y, 4.0, 3.2), ink, a); pen.fill(rrect(x + 3, y - 1.5, 3.5, 1.4, 0.6), ink, a)
                    pen.fill(rect(x - 1.2, y - 4.6, 2.4, 1.4), ink, a)
                else:
                    for q in range(3):
                        ang = q * 2.1 + rng.uniform(0, 0.4)
                        pen.fill(oval(x + math.cos(ang) * 2.6, y + math.sin(ang) * 2.6, 1.4), ink, a * 0.8)
                x += 34.0
            y += 26.0; j += 1
    elif kind == 'panel':                                     # wood panelling (den): vertical boards with grooves
        x = 0.0; k = 0
        while x < W:
            pen.fill(rect(x, 0, 30.0, H), ink, a * (0.18 + 0.22 * _h(k, seed)))
            pen.fill(rect(x, 0, 1.6, H), '#000000', 110); x += 30.0; k += 1


def _hwall(pen, hv, a, b, Y0, Y1, paper, ink=None, kind='damask', wains=0.0, wc=GP_WOOD_D, holes=(), base_h=0.14,
           pa=150, art=None, trim='#4a2e1c', rail=None, seed=0):
    """A wall from floor point a = (x, y) to b = (x, y), heights Y0..Y1 (drawn flat in cm, mapped in perspective).
    holes: [(u0, v0, u1, v1[, 'arch'])] metres along the wall from a / up from Y0, cut out (doorways, arches, windows)
    and cased with `trim`. wains = wainscot height (m), rail = picture-rail height (m). art(pen, W, H) draws frames /
    posters in the same cm frame (v measured DOWN from the top edge)."""
    Lm = math.hypot(b[0] - a[0], b[1] - a[1]); W = Lm * 100.0; H = (Y1 - Y0) * 100.0

    def hole_path(h):
        u0, v0, u1, v1 = h[:4]
        r = rect(u0 * 100, H - v1 * 100, (u1 - u0) * 100, (v1 - v0) * 100)
        if len(h) > 4 and h[4] == 'arch':
            rr = (u1 - u0) * 50
            r = union(rect(u0 * 100, H - v1 * 100 + rr, (u1 - u0) * 100, (v1 - v0) * 100 - rr), oval((u0 + u1) * 50, H - v1 * 100 + rr, rr, rr * 0.8))
        return r

    def fn(p_):
        cv = p_.cv
        wall = rect(0, 0, W, H)
        hp = [hole_path(h) for h in holes]
        for q in hp: wall = minus(wall, q)
        cv.save(); cv.clipPath(wall, skia.ClipOp.kIntersect, True)
        p_.fill(rect(0, 0, W, H), paper)
        p_.texture(rect(0, 0, W, H), 'plaster', 0.32, 'overlay', 0.45)
        if ink: _pattern(p_, W, H, kind, ink, pa, seed)
        if rail:
            ry = H - rail * 100
            p_.fill(rect(0, ry - 2.5, W, 5.0), trim); p_.fill(rect(0, ry - 2.5, W, 1.2), '#ffffff', 50)
        if wains:
            wy = H - wains * 100
            p_.fill(rect(0, wy, W, H - wy), wc); p_.texture(rect(0, wy, W, H - wy), 'wood', 0.5, 'overlay', 0.7, 90)
            x = 8.0
            while x < W - 30:                                  # raised panels
                pr = rect(x, wy + 12, 52, H - wy - 12 - base_h * 100 - 8)
                p_.fill(pr, _lighten(wc, 0.06)); p_.line(pr, 1.6, '#000000', 120)
                p_.fill(rect(x, wy + 12, 52, 2.2), '#ffffff', 40)
                x += 62.0
            p_.fill(rect(0, wy - 4, W, 8), _lighten(wc, 0.12)); p_.fill(rect(0, wy - 4, W, 2), '#ffffff', 60)
        p_.fill(rect(0, H - base_h * 100, W, base_h * 100), _darken(trim, 0.1)); p_.fill(rect(0, H - base_h * 100, W, 2), '#ffffff', 40)
        p_.fill(rect(0, 0, W, 6), _darken(trim, 0.2))                                       # crown moulding
        if art: art(p_, W, H)
        cv.restore()
        for h, q in zip(holes, hp):                                                         # casings round the openings
            if len(h) > 5 and h[5] == 'nocase': continue
            p_.line(q, 9.0, trim); p_.line(q, 2.0, '#000000', 140)
    _hface(pen, hv, (a[0], Y1, a[1]), (b[0], Y1, b[1]), (b[0], Y0, b[1]), (a[0], Y0, a[1]), W, H, fn)


def _rb(path):
    """A path's bounds as plain floats (x0, y0, x1, y1). Never use Rect.asScalars() on a temporary: it is a view of freed
    memory (garbage bounds -> a loop drawing a billion siding lines)."""
    b = path.getBounds()
    return float(b.left()), float(b.top()), float(b.right()), float(b.bottom())


def _backing(pen, hv, y, x0, x1, Y0, Y1, c, holes=()):
    """An oversized flat plane at y (house coords) behind a back wall, minus `holes` [(x0, x1, Y0, Y1)]: drawn first in the
    farthest layer so the parallax gaps at the room's seams (ceiling / side walls / floor sliding over the far wall under a
    camera move) show wall colour instead of nothing."""
    q = hv.quad([(x0, Y1, y), (x1, Y1, y), (x1, Y0, y), (x0, Y0, y)])
    for (hx0, hx1, hY0, hY1) in holes:
        q = minus(q, hv.quad([(hx0, hY1, y), (hx1, hY1, y), (hx1, hY0, y), (hx0, hY0, y)]))
    pen.fill(q, c)


def _hfloor(pen, hv, x0, x1, y0, y1, kind='boards', c0='#7a5234', c1='#5a3a22', Y=0.0, runner=None, seed=0):
    """A floor rectangle x0..x1, y0..y1 at height Y (drawn flat in cm, mapped in perspective). kind 'boards' (oak boards
    along y), 'checker' (30 cm linoleum tiles c0 / c1), 'carpet'. runner = (x0, x1, y0, y1, colour, border) on top."""
    W = abs(x1 - x0) * 100.0; H = abs(y1 - y0) * 100.0

    def fn(p_):
        r = rect(0, 0, W, H)
        if kind == 'boards':
            p_.fill(r, c0); p_.texture(r, 'wood', 0.6, 'overlay', 0.9, 90)
            u = 0.0; i = 0
            while u < W:
                p_.fill(rect(u, 0, 12.0, H), c1, 60 + 70 * _h(i, seed))
                p_.fill(rect(u, 0, 0.9, H), '#140c06', 200)
                j = _h(i, seed + 3) * 180
                while j < H:
                    p_.fill(rect(u, j, 12.0, 0.8), '#140c06', 170); j += 120 + 140 * _h(int(j) + i, seed + 5)
                u += 12.0; i += 1
        elif kind == 'checker':
            p_.fill(r, c0)
            n = int(W / 30) + 1; m = int(H / 30) + 1
            for i in range(n):
                for j in range(m):
                    if (i + j) % 2: p_.fill(rect(i * 30, j * 30, 30, 30), c1)
            p_.texture(r, 'grunge', 0.35, 'overlay', 0.6)
            for i in range(n + 1): p_.fill(rect(i * 30 - 0.4, 0, 0.8, H), '#000000', 60)
        else:
            p_.fill(r, c0); p_.texture(r, 'fabric', 0.6, 'overlay', 0.7)
        if runner:
            rx0, rx1, ry0, ry1, rc, rb = runner
            ux0 = (min(rx0, rx1) - min(x0, x1)) * 100; vy0 = (max(y0, y1) - max(ry0, ry1)) * 100
            rr = rect(ux0, vy0, abs(rx1 - rx0) * 100, abs(ry1 - ry0) * 100)
            p_.fill(rr, rc); p_.texture(rr, 'fabric', 0.7, 'overlay', 0.8)
            ir = rect(ux0 + 8, vy0 + 8, abs(rx1 - rx0) * 100 - 16, abs(ry1 - ry0) * 100 - 16)
            p_.line(ir, 3.0, rb); p_.line(rr, 2.0, '#000000', 150)
            cxm = ux0 + abs(rx1 - rx0) * 50
            yy = vy0 + 40
            while yy < vy0 + abs(ry1 - ry0) * 100 - 30:
                dm = poly([(cxm, yy - 16), (cxm + 18, yy), (cxm, yy + 16), (cxm - 18, yy)])
                p_.fill(dm, rb, 220); p_.fill(oval(cxm, yy, 4), rc); yy += 70
    # far edge at the top of the cm frame
    if hv.f > 0:
        tl, tr, br, bl = (min(x0, x1), Y, max(y0, y1)), (max(x0, x1), Y, max(y0, y1)), (max(x0, x1), Y, min(y0, y1)), (min(x0, x1), Y, min(y0, y1))
    else:
        tl, tr, br, bl = (max(x0, x1), Y, min(y0, y1)), (min(x0, x1), Y, min(y0, y1)), (min(x0, x1), Y, max(y0, y1)), (max(x0, x1), Y, max(y0, y1))
        if runner:                                                      # runner given in house coords: mirror for the frame
            rx0, rx1, ry0, ry1, rc, rb = runner
            runner = (x0 + x1 - rx1, x0 + x1 - rx0, y0 + y1 - ry1, y0 + y1 - ry0, rc, rb)
    _hface(pen, hv, tl, tr, br, bl, W, H, fn)


def _hceil(pen, hv, x0, x1, y0, y1, Y=CEIL, c='#d8d0bc'):
    """A plaster ceiling (seen from below)."""
    q = hv.quad([(x0, Y, y0), (x1, Y, y0), (x1, Y, y1), (x0, Y, y1)])
    pen.fill(q, c); pen.texture(q, 'plaster', 0.35, 'overlay', 0.6)


def _hbox(pen, hv, x0, x1, Y0, Y1, y0, y1, c, top=None, side=None, lw=None, line=True, tex=None, faces=None):
    """An axis-aligned box: draws the faces the camera can see (front toward the camera, one side, top or bottom).
    faces: optional dict face -> fn(pen, W, H) drawing flat art (cm) on that face ('front', 'top', 'side')."""
    xa, xb = min(x0, x1), max(x0, x1); ya, yb = min(y0, y1), max(y0, y1)
    yn = ya if hv.f > 0 else yb                                           # the face toward the camera
    lw = lw if lw is not None else max(1.0, 0.008 * hv.s(yn))
    out = []
    if hv.hx < xa: xs = xa
    elif hv.hx > xb: xs = xb
    else: xs = None
    if xs is not None:
        q = [(xs, Y1, yb if hv.f > 0 else ya), (xs, Y1, yn), (xs, Y0, yn), (xs, Y0, yb if hv.f > 0 else ya)]
        out.append(('side', q, side or _darken(c, 0.28)))
    if Y1 < hv.cam_h:
        yf = yb if hv.f > 0 else ya
        out.append(('top', [(xa, Y1, yf), (xb, Y1, yf), (xb, Y1, yn), (xa, Y1, yn)], top or _lighten(c, 0.1)))
    elif Y0 > hv.cam_h:
        yf = yb if hv.f > 0 else ya
        out.append(('bottom', [(xa, Y0, yn), (xb, Y0, yn), (xb, Y0, yf), (xa, Y0, yf)], _darken(c, 0.45)))
    fl, fr = (xa, xb) if hv.f > 0 else (xb, xa)
    out.append(('front', [(fl, Y1, yn), (fr, Y1, yn), (fr, Y0, yn), (fl, Y0, yn)], c))
    for name, q, cc in out:
        path = hv.quad(q)
        pen.fill(path, cc)
        if tex: pen.texture(path, tex, 0.45, 'overlay', 1.0, 90)
        if faces and name in faces:
            W = (math.hypot(q[1][0] - q[0][0], q[1][2] - q[0][2])) * 100; H = abs(q[0][1] - q[3][1]) * 100
            if name == 'top': H = math.hypot(q[0][0] - q[3][0], q[0][2] - q[3][2]) * 100
            _hface(pen, hv, q[0], q[1], q[2], q[3], W, H, lambda p_, f=faces[name], W=W, H=H: f(p_, W, H))
        if line: pen.line(path, lw, LINE, 210)
    return out


def _hframe(pen, W, H, x, y, w, h, kind='photo', frame='#3a2414', seed=0, fn=None):
    """A framed picture on a wall, in the wall's cm frame (x, y = top-left, cm). kind: 'photo' (sepia family photo),
    'poster' (fn draws the poster art in a w x h cm frame), 'mirror', 'landscape'."""
    fw = max(2.0, min(w, h) * 0.07)
    pen.fill(rect(x + 1.5, y + 2.5, w, h), '#000000', 90)
    pen.fill(rect(x, y, w, h), frame); pen.fill(rect(x + fw * 0.3, y + fw * 0.3, w - fw * 0.6, h - fw * 0.6), _lighten(frame, 0.14))
    ix, iy, iw, ih = x + fw, y + fw, w - 2 * fw, h - 2 * fw
    cv = pen.cv; cv.save(); cv.clipPath(rect(ix, iy, iw, ih), skia.ClipOp.kIntersect, True)
    if kind == 'mirror':
        pen.linear(rect(ix, iy, iw, ih), ix, iy, ix + iw, iy + ih, ['#3a4258', '#7a849c', '#2a3040'])
    elif kind == 'landscape':
        pen.linear(rect(ix, iy, iw, ih), 0, iy, 0, iy + ih, ['#7a9ab0', '#d8c48a'])
        pen.fill(poly([(ix, iy + ih * 0.7), (ix + iw * 0.4, iy + ih * 0.4), (ix + iw * 0.7, iy + ih * 0.62), (ix + iw, iy + ih * 0.5),
                       (ix + iw, iy + ih), (ix, iy + ih)]), '#4a5a3a')
    elif fn is not None:
        cv.translate(ix, iy); fn(pen, iw, ih); cv.translate(-ix, -iy)
    else:
        _sepia_photo(pen, ix, iy, iw, ih, seed)
    pen.fill(poly([(ix, iy + ih * 0.4), (ix + iw * 0.4, iy), (ix + iw * 0.55, iy), (ix, iy + ih * 0.6)]), '#ffffff', 22)
    cv.restore()
    pen.line(rect(x, y, w, h), max(0.8, fw * 0.15), LINE, 220)


def _sepia_photo(pen, x, y, w, h, seed=0):
    """A small old photograph: a man in a suit with a small figure on his knee (seed varies the pose), sepia."""
    pen.linear(rect(x, y, w, h), 0, y, 0, y + h, ['#c8b08a', '#8a6a48'])
    pen.radial(None, x + w * 0.5, y + h * 0.4, w * 0.7, [(0, '#e8d4ae', 160), (1, '#e8d4ae', 0)], clip=False)
    mx = x + w * (0.4 + 0.1 * _h(seed, 3)); my = y + h * 0.95
    pen.fill(smooth([(mx - w * 0.2, my), (mx - w * 0.18, my - h * 0.45), (mx, my - h * 0.52), (mx + w * 0.18, my - h * 0.45), (mx + w * 0.2, my)], True, 0.5), '#3a2a1c')
    pen.fill(oval(mx, my - h * 0.62, w * 0.09, h * 0.1), '#b89870')
    pen.fill(oval(mx, my - h * 0.68, w * 0.09, h * 0.05), '#4a3a2a')
    dx = mx + w * 0.17; dy = my - h * 0.36                                                     # the little figure on his knee
    pen.fill(rrect(dx - w * 0.07, dy - h * 0.02, w * 0.14, h * 0.2, w * 0.03), '#5a2a22')
    pen.fill(oval(dx, dy - h * 0.1, w * 0.07, h * 0.08), '#d8b896')
    pen.fill(oval(dx, dy - h * 0.16, w * 0.07, h * 0.035), '#8a4a2a')


# ---------------------------------------------------------------------------------------------- small house props
def _lamp_shade(pen, x, y, s, k=1.0, c='#e8dcc0', kind='drum', pleat=True):
    """A lamp shade (bottom centre at x, y; s px per metre) glowing at level k (emissive; draw after the light map)."""
    if kind == 'drum':
        sh = poly([(x - 0.17 * s, y - 0.3 * s), (x + 0.17 * s, y - 0.3 * s), (x + 0.22 * s, y), (x - 0.22 * s, y)])
    else:                                                   # 'bell': flared 60s shade
        sh = smooth([(x - 0.13 * s, y - 0.32 * s), (x + 0.13 * s, y - 0.32 * s), (x + 0.2 * s, y - 0.1 * s), (x + 0.26 * s, y),
                     (x - 0.26 * s, y), (x - 0.2 * s, y - 0.1 * s)], True, 0.4)
    off = _darken(c, 0.62)
    pen.fill(sh, mix(off, c, k))
    if k > 0.01:
        pen.radial(sh, x, y - 0.12 * s, 0.32 * s, [(0, '#fff6e2', 255 * k), (0.6, mix(c, '#fff0d0', 0.5), 235 * k), (1, c, 120 * k)])
    if pleat:
        for i in range(-6, 7):
            u = i / 6.0
            pen.seg((x + u * 0.17 * s, y - 0.3 * s), (x + u * 0.22 * s, y), max(0.8, 0.004 * s), _darken(c, 0.25), 90)
    pen.line(sh, max(1.0, 0.007 * s), LINE, 220)
    if k > 0.01:
        pen.fill(oval(x, y + 0.004 * s, 0.215 * s, 0.025 * s), '#fff8ea', 240 * k)


def _flashlight_beam(pen, x, y, ax, ay, s, k=1.0, spread=0.32, length=None, c='#fff2c8'):
    """A small flashlight seen in the dark: the bright lens at (x, y), the beam toward (ax, ay) (a direction point),
    s = px per metre at the torch. Draw on a dynamic layer at the torch's depth."""
    if k <= 0.01: return
    dx, dy = ax - x, ay - y; L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    ln = length or 3.2 * s
    nx_, ny_ = -uy, ux
    w0, w1 = 0.02 * s, ln * spread
    beam = poly([(x + nx_ * w0, y + ny_ * w0), (x + ux * ln + nx_ * w1, y + uy * ln + ny_ * w1),
                 (x + ux * ln - nx_ * w1, y + uy * ln - ny_ * w1), (x - nx_ * w0, y - ny_ * w0)])
    pen.linear(beam, x, y, x + ux * ln, y + uy * ln, [(0, c, 120 * k), (0.35, c, 46 * k), (1, c, 0)])
    pen.glow(x, y, 0.35 * s, c, 150 * k)
    pen.glow(x, y, 0.08 * s, '#ffffff', 250 * k)


def _steam(pen, x, y, s, t, k=1.0, seed=0):
    """Coffee steam rising from a mug rim at (x, y): three soft wisps that curl and fade (s = px per metre)."""
    if k <= 0.01: return
    for i in range(3):
        ph = t * 0.55 + i * 0.37 + seed
        pts = []
        for j in range(9):
            u = j / 8.0
            yy = y - u * 0.26 * s
            xx = x + (i - 1) * 0.018 * s + 0.03 * s * u * noise1(ph * 1.3 + u * 2.2, seed + i) + 0.012 * s * math.sin(ph * 3 + u * 6)
            pts.append((xx, yy))
        a = 70 * k * (0.6 + 0.4 * (0.5 + 0.5 * noise1(t * 0.8 + i, seed + 7)))
        pen.line(smooth(pts, False, 0.8), max(1.2, 0.018 * s), '#f4ecdf', a, blur=max(0.6, 0.006 * s))


def _mug_art(pen, x, y, s, spoon=True, logo=True):
    """Grandpa's mug (cream enamel, the old show's logo in red), bottom centre at (x, y), s px per metre, seen from the
    front slightly above. Coffee inside, the spoon handle sticking out."""
    w, h = 0.085 * s, 0.1 * s
    body = smooth([(x - w / 2, y - h), (x + w / 2, y - h), (x + w / 2 * 0.98, y - h * 0.1), (x + w * 0.42, y), (x - w * 0.42, y),
                   (x - w / 2 * 0.98, y - h * 0.1)], True, 0.3)
    hd = smooth([(x + w * 0.48, y - h * 0.82), (x + w * 0.85, y - h * 0.78), (x + w * 0.9, y - h * 0.35), (x + w * 0.48, y - h * 0.25)], False, 0.8)
    pen.line(hd, max(1.5, 0.014 * s), LINE); pen.line(hd, max(1.0, 0.009 * s), '#e6dcc6')
    pen.fill(oval(x, y, w * 0.55, w * 0.1), '#000000', 90)
    pen.fill(body, '#e9dfc8'); pen.linear(body, x - w / 2, 0, x + w / 2, 0, [(0, '#ffffff', 60), (0.4, '#ffffff', 0), (1, '#000000', 50)])
    if logo:
        pen.fill(oval(x - w * 0.04, y - h * 0.52, w * 0.24, h * 0.2), '#c8322a', 230)
        pen.fill(oval(x - w * 0.04, y - h * 0.52, w * 0.12, h * 0.1), '#f4d24a', 230)
    pen.line(body, max(1.0, 0.009 * s), LINE)
    top = oval(x, y - h, w / 2, w * 0.13)
    pen.fill(top, '#d8ccb4'); pen.fill(oval(x, y - h + w * 0.015, w * 0.43, w * 0.1), '#3a2010')
    pen.fill(oval(x - w * 0.12, y - h + w * 0.005, w * 0.1, w * 0.025), '#a8784a', 160)
    if spoon:
        pen.line(poly([(x + w * 0.12, y - h + w * 0.03), (x + w * 0.42, y - h - 0.075 * s)], False), max(1.5, 0.008 * s), '#b8bcc4')
        pen.line(poly([(x + w * 0.12, y - h + w * 0.03), (x + w * 0.42, y - h - 0.075 * s)], False), max(0.6, 0.003 * s), '#ffffff', 160)
    pen.line(top, max(0.8, 0.007 * s), LINE, 200)


# ---------------------------------------------------------------------------------------------- the kitchen (house coords)
def _kitchen_outside(pen, hv, t=0.0, tod='night'):
    """Through the kitchen window: the back yard at night (or morning)."""
    x0, y0 = hv.p(KWIN[0] - 0.4, KWIN[3] + 0.4, KIT_Y[1] + 0.05); x1, y1 = hv.p(KWIN[1] + 0.4, KWIN[2] - 0.3, KIT_Y[1] + 0.05)
    r = rect(x0, y0, x1 - x0, y1 - y0)
    if tod == 'morning':
        pen.linear(r, 0, y0, 0, y1, ['#b8c6d8', '#dfe2e0', '#a8b49a'])
        draw_tree(pen, x0 + (x1 - x0) * 0.7, y1, (y1 - y0) * 1.6, t, 52, 0.4, '#5a6450', None, 4)
    else:
        pen.linear(r, 0, y0, 0, y1, ['#0b1430', '#1a2448', '#0c1020'])
        pen.radial(None, x0 + (x1 - x0) * 0.25, y0 + (y1 - y0) * 0.3, (x1 - x0) * 0.6, [(0, '#3a4c84', 120), (1, '#3a4c84', 0)], clip=False)
        draw_tree(pen, x0 + (x1 - x0) * 0.72, y1, (y1 - y0) * 1.5, t, 52, 0.4, '#05070d', None, 4)
        pen.fill(rect(x0, y0 + (y1 - y0) * 0.78, x1 - x0, (y1 - y0) * 0.22), '#060810')
        for i in range(2):
            wx = x0 + (x1 - x0) * (0.18 + 0.4 * i); wy = y0 + (y1 - y0) * 0.62
            pen.fill(rect(wx, wy, (x1 - x0) * 0.05, (y1 - y0) * 0.06), '#d9b47c' if i == 0 else '#0a0d16')


def _kitchen_room(pen, hv, tod='night'):
    """Back wall (window, cafe curtains, cabinets, sink, the sunburst clock), fridge, stove, the right wall with the back
    door and the calendar, the checker floor and the ceiling. Albedo only (lit by _lmap)."""
    xa, xb = KIT_X; ya, yb = KIT_Y
    yn = max(ya - 0.7, hv.hy + 0.3)                        # reaches under the opening: no seam on a push through it
    _kitchen_outside(pen, hv, 0.0, tod)
    _backing(pen, hv, yb, xa - 1.0, xb + 1.0, -0.8, CEIL + 1.2, '#b8a888', [(KWIN[0], KWIN[1], KWIN[2], KWIN[3])])
    _hfloor(pen, hv, xa, xb, yn, yb, 'checker', '#e6dcc4', '#2c2a30')
    _hceil(pen, hv, xa, xb, yn, yb, CEIL, '#e8dcc0')
    wu0, wu1 = KWIN[0] - xa, KWIN[1] - xa

    def back_art(p_, W, H):
        # sunburst clock
        cx, cy = (-2.85 - xa) * 100, H - 185
        for k in range(16):
            ang = k * math.pi / 8
            p_.line(poly([(cx + math.cos(ang) * 14, cy + math.sin(ang) * 14), (cx + math.cos(ang) * 30, cy + math.sin(ang) * 30)], False), 3.0, '#b8902a')
        p_.fill(oval(cx, cy, 14), '#f2ead6'); p_.line(oval(cx, cy, 14), 2.0, '#b8902a')
        # cafe curtains (red gingham) on a rod across the lower window half, a valance on top
        p_.fill(rect(wu0 * 100 - 12, H - KWIN[3] * 100 - 14, (wu1 - wu0) * 100 + 24, 18), '#b8322a')
        for i in range(12):
            p_.fill(rect(wu0 * 100 - 12 + i * ((wu1 - wu0) * 100 + 24) / 12, H - KWIN[3] * 100 - 14, ((wu1 - wu0) * 100 + 24) / 24, 18), '#f0e6d6', 160)
        cy0 = H - (KWIN[2] + 0.45) * 100
        for side in (0, 1):
            cxp = wu0 * 100 + (0 if side == 0 else (wu1 - wu0) * 50)
            cur = rect(cxp, cy0, (wu1 - wu0) * 50, 45)
            p_.fill(cur, '#c8443a')
            for i in range(9): p_.fill(rect(cxp + i * (wu1 - wu0) * 50 / 9, cy0, (wu1 - wu0) * 25 / 9, 45), '#f4ece0', 150)
            for j in range(4): p_.fill(rect(cxp, cy0 + j * 11.25, (wu1 - wu0) * 50, 5.6), '#f4ece0', 110)
            p_.line(cur, 1.5, '#5a1a14', 180)
        p_.fill(rect(wu0 * 100 - 6, cy0 - 3, (wu1 - wu0) * 100 + 12, 3), '#c9b06a')
        # a framed sampler and a calendar
        p_.fill(rect((0.55 - xa) * 100, H - 200, 26, 34), '#f4ecd8'); p_.fill(rect((0.55 - xa) * 100, H - 200, 26, 10), '#c8322a')
        p_.line(rect((0.55 - xa) * 100, H - 200, 26, 34), 1.2, LINE)
    _hwall(pen, hv, (xa, yb), (xb, yb), 0.0, CEIL, '#efe2b8', '#b88a4a', 'kitchen', 0.0, holes=[(wu0, KWIN[2], wu1, KWIN[3])],
           base_h=0.1, pa=120, art=back_art, trim='#f2ead8', seed=4)
    # window sill + mullion
    pen.fill(hv.quad([(KWIN[0] - 0.05, KWIN[2], yb), (KWIN[1] + 0.05, KWIN[2], yb), (KWIN[1] + 0.05, KWIN[2] - 0.04, yb - 0.1),
                      (KWIN[0] - 0.05, KWIN[2] - 0.04, yb - 0.1)]), '#f2ead8')
    mx = (KWIN[0] + KWIN[1]) / 2
    pen.seg(hv.p(mx, KWIN[2], yb), hv.p(mx, KWIN[3], yb), max(2.0, 0.035 * hv.s(yb)), '#f2ead8')
    pen.seg(hv.p(KWIN[0], (KWIN[2] + KWIN[3]) / 2, yb), hv.p(KWIN[1], (KWIN[2] + KWIN[3]) / 2, yb), max(2.0, 0.03 * hv.s(yb)), '#f2ead8')
    # right wall: the back door (half glass) and a calendar
    def right_art(p_, W, H):
        p_.fill(rect(150, H - 120, 40, 52), '#f4ecd8'); p_.fill(rect(150, H - 120, 40, 18), '#3a6a9a')
        p_.line(rect(150, H - 120, 40, 52), 1.2, LINE)
    _hwall(pen, hv, (xb, yn), (xb, yb), 0.0, CEIL, '#efe2b8', '#b88a4a', 'kitchen', 0.0, holes=[(ya + 1.0 - yn, 0.0, ya + 1.85 - yn, 2.05)],
           base_h=0.1, pa=120, art=right_art, trim='#f2ead8', seed=5)
    door = hv.quad([(xb, 2.05, ya + 1.0), (xb, 2.05, ya + 1.85), (xb, 0.0, ya + 1.85), (xb, 0.0, ya + 1.0)])
    pen.fill(door, '#e8dcc0'); pen.fill(hv.quad([(xb, 1.9, ya + 1.12), (xb, 1.9, ya + 1.73), (xb, 1.2, ya + 1.73), (xb, 1.2, ya + 1.12)]),
                                          '#1a2448' if tod != 'morning' else '#c8d4e0')
    pen.line(door, 2, LINE, 200)
    # base cabinets + counter + sink under the window, upper cabinets, fridge, stove
    cy0 = yb - 0.62
    _hbox(pen, hv, -2.3, 0.3, 0.0, 0.86, cy0, yb, '#8fbca6', top='#e8e0cc',
          faces={'front': lambda p_, W, H: _cab_doors(p_, W, H, 4)})
    _hbox(pen, hv, -2.34, 0.34, 0.86, 0.91, cy0 - 0.03, yb, '#d8302a', top='#efe8d8')
    sk = hv.quad([(KWIN[0] + 0.15, 0.911, cy0 + 0.1), (KWIN[1] - 0.15, 0.911, cy0 + 0.1), (KWIN[1] - 0.15, 0.911, yb - 0.12), (KWIN[0] + 0.15, 0.911, yb - 0.12)])
    pen.fill(sk, '#b8c0c8'); pen.line(sk, 1.5, LINE, 200)
    fx_, fy_ = hv.p(mx, 1.12, yb - 0.08)
    pen.line(smooth([hv.p(mx, 0.92, yb - 0.08), hv.p(mx, 1.12, yb - 0.08), hv.p(mx, 1.1, yb - 0.22)], False, 0.8), max(2.0, 0.02 * hv.s(yb)), '#c8ccd2')
    for (ux0, ux1) in ((-2.3, -1.7), (-0.2, 0.3)):
        _hbox(pen, hv, ux0, ux1, 1.45, 2.25, yb - 0.34, yb, '#8fbca6', faces={'front': lambda p_, W, H: _cab_doors(p_, W, H, 1, upper=True)})
    # fridge (rounded 50s cream fridge with a chrome handle)
    _hbox(pen, hv, -3.35, -2.55, 0.0, 1.62, yb - 0.7, yb - 0.02, '#ece4cc', top='#f4ecd8',
          faces={'front': lambda p_, W, H: (p_.fill(rect(W - 14, 30, 6, 36), '#c8ccd2'), p_.fill(rect(4, 52, W - 8, 1.5), '#000000', 80),
                                            p_.fill(rect(W * 0.2, 8, W * 0.6, 6), '#b8a888', 160))})
    # stove (white enamel, back panel with clock and knobs) + the red kettle
    _hbox(pen, hv, 0.36, 1.1, 0.0, 0.9, yb - 0.66, yb - 0.02, '#ece8e0', top='#2a2a2e',
          faces={'front': lambda p_, W, H: (p_.line(rect(8, 22, W - 16, H - 36), 2.0, '#a8a8a8'), p_.fill(rect(W * 0.35, 30, W * 0.3, 4), '#c8ccd2'),
                                            [p_.fill(oval(12 + i * (W - 24) / 4, 10, 3.2), '#2a2a2a') for i in range(5)])})
    _hbox(pen, hv, 0.36, 1.1, 0.9, 1.2, yb - 0.08, yb - 0.02, '#ece8e0')
    kx, ky = hv.p(0.6, 0.9, yb - 0.42); ks = hv.s(yb - 0.42)
    kt = smooth([(kx - 0.11 * ks, ky), (kx - 0.12 * ks, ky - 0.1 * ks), (kx - 0.05 * ks, ky - 0.17 * ks), (kx + 0.05 * ks, ky - 0.17 * ks),
                 (kx + 0.12 * ks, ky - 0.1 * ks), (kx + 0.11 * ks, ky)], True, 0.5)
    pen.shape(kt, '#c8322a', max(1.0, 0.008 * ks)); pen.line(poly([(kx + 0.1 * ks, ky - 0.1 * ks), (kx + 0.2 * ks, ky - 0.16 * ks)], False), max(1.5, 0.02 * ks), '#c8322a')


def _cab_doors(p_, W, H, n, upper=False):
    """Cabinet doors with chrome pulls on a front face (cm frame)."""
    dw = W / n
    for i in range(n):
        r = rect(i * dw + 3, 4 if upper else 14, dw - 6, H - (8 if upper else 22))
        p_.line(r, 1.6, '#000000', 110); p_.fill(rect(i * dw + 3, 4 if upper else 14, dw - 6, 2), '#ffffff', 70)
        hx = i * dw + (dw - 12 if i % 2 == 0 else 9)
        p_.fill(rrect(hx, (H - 18 if upper else 30), 3.0, 12, 1.2), '#d8dce2')
    if not upper: p_.fill(rect(0, 2, W, 7), '#000000', 40)


def _table_art(pen, hv, mug=True, cloth=False):
    """The kitchen table (yellow formica, chrome edge, chrome legs), the mug in front of Grandpa's chair."""
    x0, x1, y0, y1, Y = TABLE
    yn = y0 if hv.f > 0 else y1
    yf = y1 if hv.f > 0 else y0
    for (lx, ly) in ((x0 + 0.06, y0 + 0.06), (x1 - 0.06, y0 + 0.06), (x0 + 0.06, y1 - 0.06), (x1 - 0.06, y1 - 0.06)):
        a_, b_ = hv.p(lx, 0, ly), hv.p(lx, Y - 0.03, ly)
        w = max(1.5, 0.032 * hv.s(ly))
        pen.seg(a_, b_, w + 2, LINE, 220); pen.seg(a_, b_, w, '#c8ccd4'); pen.seg((a_[0] - w * 0.2, a_[1]), (b_[0] - w * 0.2, b_[1]), w * 0.25, '#ffffff', 150)
    top = hv.quad([(x0, Y, yf), (x1, Y, yf), (x1, Y, yn), (x0, Y, yn)])
    pen.fill(top, '#d6b85e'); pen.texture(top, 'grunge', 0.3, 'overlay', 0.6)
    _hface(pen, hv, (x0, Y, yf), (x1, Y, yf), (x1, Y, yn), (x0, Y, yn), (x1 - x0) * 100, (y1 - y0) * 100,
           lambda p_: [p_.fill(oval(10 + 13 * i % 100, 7 + (37 * i) % 70, 1.4, 0.7), '#b89a40', 140) for i in range(40)])
    pen.line(top, max(1.0, 0.008 * hv.s(yn)), LINE, 220)
    ed = hv.quad([(x0, Y, yn), (x1, Y, yn), (x1, Y - 0.04, yn), (x0, Y - 0.04, yn)])
    pen.fill(ed, '#d8dce4'); pen.fill(hv.quad([(x0, Y - 0.012, yn), (x1, Y - 0.012, yn), (x1, Y - 0.02, yn), (x0, Y - 0.02, yn)]), '#ffffff', 170)
    pen.line(ed, max(1.0, 0.006 * hv.s(yn)), LINE, 200)
    if mug:
        mx, my = hv.p(GCHAIR[0] + 0.02, Y, GCHAIR[1] - 0.42)
        _mug_art(pen, mx, my, hv.s(GCHAIR[1] - 0.42))
        sx, sy_ = hv.p(GCHAIR[0] + 0.25, Y, GCHAIR[1] - 0.45)                      # the sugar bowl
        ss = hv.s(GCHAIR[1] - 0.45)
        pen.fill(oval(sx, sy_ - 0.03 * ss, 0.05 * ss, 0.035 * ss), '#c8c0b0'); pen.line(oval(sx, sy_ - 0.03 * ss, 0.05 * ss, 0.035 * ss), 1.2, LINE, 200)
        pen.fill(oval(sx, sy_ - 0.06 * ss, 0.045 * ss, 0.012 * ss), '#d8d0c0')


def _gchair_art(pen, hv, part='back'):
    """Grandpa's chair: a dark wooden captain's chair with arms and a spindle back and a faded red cushion, facing the
    hall (toward -y). part 'back' (back rail, spindles, seat: behind whoever sits in it) or 'arms' (the arm rests and
    their front posts: in front)."""
    cx, cy = GCHAIR
    hw, sd = 0.27, 0.22
    Ys = 0.46
    wood, dk = '#5a3420', '#2e1a0e'
    if part == 'back':
        yb_ = cy + sd                                                   # the back's plane
        # spindles + top rail (curved) + back legs
        for i in range(7):
            u = -1 + 2 * i / 6
            a_, b_ = hv.p(cx + u * hw * 0.82, Ys + 0.04, yb_), hv.p(cx + u * hw * 0.78, 1.0 - 0.04 * u * u, yb_ + 0.02)
            w = max(1.2, 0.022 * hv.s(yb_))
            pen.seg(a_, b_, w + 1.5, LINE, 220); pen.seg(a_, b_, w, wood)
        rail = [hv.p(cx + u * hw * 1.05, 1.02 - 0.05 * u * u, yb_ + 0.02) for u in np.linspace(-1, 1, 9)]
        pen.line(poly(rail, False), max(4.0, 0.07 * hv.s(yb_)), LINE); pen.line(poly(rail, False), max(3.0, 0.058 * hv.s(yb_)), wood)
        pen.line(poly(rail, False), max(1.0, 0.012 * hv.s(yb_)), '#ffffff', 50)
        for sx in (-1, 1):
            a_, b_ = hv.p(cx + sx * hw, 0.0, yb_), hv.p(cx + sx * hw * 1.02, 1.02, yb_ + 0.02)
            w = max(2.0, 0.04 * hv.s(yb_)); pen.seg(a_, b_, w + 2, LINE); pen.seg(a_, b_, w, dk)
        # seat (seen from above) + cushion + front legs
        seat = hv.quad([(cx - hw, Ys, cy + sd), (cx + hw, Ys, cy + sd), (cx + hw, Ys, cy - sd), (cx - hw, Ys, cy - sd)])
        pen.fill(seat, wood); pen.texture(seat, 'wood', 0.5, 'overlay', 1.0, 90); pen.line(seat, 1.5, LINE, 200)
        cu = hv.quad([(cx - hw * 0.85, Ys + 0.04, cy + sd * 0.8), (cx + hw * 0.85, Ys + 0.04, cy + sd * 0.8), (cx + hw * 0.85, Ys + 0.04, cy - sd * 0.9),
                      (cx - hw * 0.85, Ys + 0.04, cy - sd * 0.9)])
        pen.fill(cu, '#9a3a30'); pen.texture(cu, 'fabric', 0.6, 'overlay', 0.8)
        fr = hv.quad([(cx - hw, Ys, cy - sd), (cx + hw, Ys, cy - sd), (cx + hw, Ys - 0.05, cy - sd), (cx - hw, Ys - 0.05, cy - sd)])
        pen.fill(fr, dk); pen.line(fr, 1.2, LINE, 200)
        for sx in (-1, 1):
            a_, b_ = hv.p(cx + sx * hw * 0.92, 0.0, cy - sd), hv.p(cx + sx * hw * 0.92, Ys - 0.04, cy - sd)
            w = max(2.0, 0.04 * hv.s(cy - sd)); pen.seg(a_, b_, w + 2, LINE); pen.seg(a_, b_, w, dk)
    else:
        for sx in (-1, 1):
            ar = [hv.p(cx + sx * hw * 1.02, 0.7, cy + sd), hv.p(cx + sx * hw * 1.06, 0.72, cy - sd * 0.9)]
            pen.line(poly(ar, False), max(3.0, 0.05 * hv.s(cy)), LINE); pen.line(poly(ar, False), max(2.0, 0.04 * hv.s(cy)), wood)
            a_, b_ = hv.p(cx + sx * hw * 1.0, Ys, cy - sd * 0.85), hv.p(cx + sx * hw * 1.05, 0.71, cy - sd * 0.9)
            w = max(1.5, 0.028 * hv.s(cy - sd)); pen.seg(a_, b_, w + 1.5, LINE); pen.seg(a_, b_, w, wood)


def _dinette_chair(pen, hv, x, y, face):
    """A chrome dinette chair with red vinyl, at (x, y) facing +x (face=1) or -x (-1), seen across the table."""
    Ys = 0.46; hw = 0.2
    sx0, sx1 = x - hw, x + hw
    bx = x - face * hw                                               # its back is on the far side from where it faces
    for (lx, ly) in ((sx0 + 0.03, y - hw + 0.03), (sx1 - 0.03, y - hw + 0.03), (sx0 + 0.03, y + hw - 0.03), (sx1 - 0.03, y + hw - 0.03)):
        pen.seg(hv.p(lx, 0, ly), hv.p(lx, Ys - 0.04, ly), max(1.5, 0.022 * hv.s(ly)) + 1.5, LINE, 200)
        pen.seg(hv.p(lx, 0, ly), hv.p(lx, Ys - 0.04, ly), max(1.2, 0.022 * hv.s(ly)), '#c8ccd4')
    _hbox(pen, hv, sx0, sx1, Ys - 0.06, Ys, y - hw, y + hw, '#a82a24', top='#c0362e', lw=max(1.0, 0.006 * hv.s(y)))
    for ly in (y - hw * 0.85, y + hw * 0.85):                        # the chrome back posts
        pen.seg(hv.p(bx, Ys, ly), hv.p(bx, 0.9, ly), max(1.5, 0.02 * hv.s(ly)) + 1.5, LINE, 200)
        pen.seg(hv.p(bx, Ys, ly), hv.p(bx, 0.9, ly), max(1.2, 0.02 * hv.s(ly)), '#c8ccd4')
    q = [(bx, 0.9, y - hw * 0.9), (bx, 0.9, y + hw * 0.9), (bx, 0.66, y + hw * 0.9), (bx, 0.66, y - hw * 0.9)]
    _hface(pen, hv, *q, 36, 24, lambda p_: (p_.fill(rrect(0, 0, 36, 24, 7), '#c0362e'), p_.texture(rrect(0, 0, 36, 24, 7), 'fabric', 0.4, 'overlay', 0.6),
                                           p_.line(rrect(2, 2, 32, 20, 6), 1.0, '#7a1410', 160), p_.fill(rrect(3, 3, 30, 5, 3), '#ffffff', 50),
                                           p_.line(rrect(0, 0, 36, 24, 7), 2.4, '#c8ccd4'), p_.line(rrect(0, 0, 36, 24, 7), 0.8, LINE)))


def _pendant_art(pen, hv, k=1.0, sway=0.0):
    """The amber glass dome pendant over the table (emissive at level k), its cord to the ceiling."""
    x, y, Yb = PENDANT
    px, py = hv.p(x + sway, Yb, y); s = hv.s(y)
    cx_, cy_ = hv.p(x, CEIL, y)
    pen.seg((cx_, cy_), (px, py - 0.22 * s), max(1.0, 0.008 * s), '#1a1410')
    pen.fill(oval(cx_, cy_, 0.05 * s, 0.015 * s), '#3a2a1a')
    dome = smooth([(px - 0.2 * s, py), (px - 0.17 * s, py - 0.1 * s), (px - 0.08 * s, py - 0.2 * s), (px, py - 0.23 * s), (px + 0.08 * s, py - 0.2 * s),
                   (px + 0.17 * s, py - 0.1 * s), (px + 0.2 * s, py)], True, 0.5)
    pen.fill(dome, mix('#4a2a10', '#e8962a', k))
    if k > 0.01:
        pen.radial(dome, px, py - 0.03 * s, 0.26 * s, [(0, '#fff2c0', 255 * k), (0.5, '#ffb84a', 230 * k), (1, '#c86a1a', 160 * k)])
    for i in range(-3, 4):
        pen.line(smooth([(px + i * 0.05 * s, py), (px + i * 0.035 * s, py - 0.12 * s), (px + i * 0.01 * s, py - 0.21 * s)], False), max(0.6, 0.004 * s), '#7a3a10', 90)
    pen.line(dome, max(1.0, 0.008 * s), LINE, 220)
    pen.fill(oval(px, py, 0.2 * s, 0.03 * s), mix('#3a2410', '#fff4d0', k))
    if k > 0.01: pen.glow(px, py + 0.01 * s, 0.25 * s, '#ffd890', 140 * k)


KITCHEN_LIGHTS = [(PENDANT[0], 1.3, PENDANT[1], 3.0, GP_KLAMP, 0.72), (PENDANT[0], TABLE[4], PENDANT[1], 1.0, '#ffe8b8', 0.3, 0.5),
                  (PENDANT[0], 1.5, KIT_Y[1], 2.6, GP_KLAMP, 0.42), (PENDANT[0], 0.0, PENDANT[1] + 0.3, 2.2, GP_KLAMP, 0.5, 0.35),
                  (GCHAIR[0], 0.7, GCHAIR[1] + 0.2, 0.9, '#ffd8a0', 0.25), (-3.0, 1.2, KIT_Y[1], 3.0, GP_KLAMP, 0.22)]
KITCHEN_NIGHT = [(KWIN[0] * 0.5 + KWIN[1] * 0.5, 1.5, KIT_Y[1], 1.6, GP_MOON, 0.55), (-0.95, 0.0, 9.0, 1.6, GP_MOON, 0.25, 0.4)]


def _kitchen_layers(hv, tag, kf, box, tod='night', mug=True, steam=None, chair=True, sway=None):
    """The kitchen's layers seen from any HView (depths = distances): room, Grandpa's chair, the table (+ mug, the
    dinette chairs, the chair's arms), the pendant (emissive) and the steam (live). kf = the pendant's level f(t)."""
    amb = '#1c2034' if tod == 'night' else '#c8ccd2'
    lights = KITCHEN_NIGHT if tod == 'night' else [(-0.95, 1.5, KIT_Y[1], 3.0, '#e8eef8', 0.6)]
    var = [('pendant', KITCHEN_LIGHTS, kf)] if tod == 'night' else []
    L = []
    L += _lit(hv.d(KIT_Y[1] - 0.3), lambda p: _kitchen_room(p, hv, tod), 'k_room', _key('gp', tag, 'kroom', tod), box, hv, amb, lights, var)
    if chair:
        L += _lit(hv.d(GCHAIR[1] + 0.18), lambda p: _gchair_art(p, hv, 'back'), 'k_chair', _key('gp', tag, 'kchair', tod), box, hv, amb, lights, var)

    def table(p):
        _dinette_chair(p, hv, TABLE[0] - 0.3, (TABLE[2] + TABLE[3]) / 2, 1)
        _dinette_chair(p, hv, TABLE[1] + 0.3, (TABLE[2] + TABLE[3]) / 2, -1)
        if chair: _gchair_art(p, hv, 'arms')
        _table_art(p, hv, mug)
    L += _lit(hv.d(TABLE[2] + 0.35), table, 'k_table', _key('gp', tag, 'ktable', mug, chair, tod), box, hv, amb, lights, var)
    sw = sway or (lambda t: 0.0)
    L.append(Layer(hv.d(PENDANT[1]), lambda pen, t: _pendant_art(pen, hv, kf(t) if tod == 'night' else 0.15, sw(t)), 'k_pendant', blur=None))
    if mug:
        stf = _kfn(steam, 3, 1.0)
        mx, my = hv.p(GCHAIR[0] + 0.02, TABLE[4] + 0.1, GCHAIR[1] - 0.42)
        ms = hv.s(GCHAIR[1] - 0.42)
        L.append(Layer(hv.d(GCHAIR[1] - 0.43), lambda pen, t: _steam(pen, mx, my, ms, t, stf(t), 5), 'k_steam', blur=None))
    return L


# ---------------------------------------------------------------------------------------------- the front hall
def _case3d(pen, hv, state='closed', envelope=True, latch=0.0):
    """The black leather case on the hall bench (CASE: x0, x1, y0, y1, Y0, h). state 'closed' (the envelope taped to the
    lid) | 'open' (lid up against the wall, the red velvet, the dummy-shaped hollow) | 'none'."""
    if state in (None, 'none'): return
    x0, x1, y0, y1, Y0, h = CASE
    leather, ld = '#2a2730', '#141218'
    brass = '#c9a24a'

    def stitch(p_, W, H, m=3.5):
        p_.dashed(rrect(m, m, W - 2 * m, H - 2 * m, 4), 0.9, '#8a8478', 150, 3.0, 2.2)

    def front_art(p_, W, H):                               # the side facing the hall: latches, handle, the seam
        p_.linear(rect(0, 0, W, H), 0, 0, 0, H, ['#3a3742', leather, ld])
        p_.texture(rect(0, 0, W, H), 'grunge', 0.4, 'overlay', 0.5)
        sy = H * 0.38
        p_.fill(rect(0, sy - 1.2, W, 2.4), '#0a090c'); p_.fill(rect(0, sy + 1.2, W, 0.8), '#5a5662', 160)
        stitch(p_, W, H)
        for u in (0.22, 0.78):
            lx = W * u
            op = clamp(latch)
            p_.fill(rrect(lx - 4.5, sy - 2, 9, 9, 1.5), brass); p_.line(rrect(lx - 4.5, sy - 2, 9, 9, 1.5), 0.8, LINE)
            p_.cv.save(); p_.cv.translate(lx, sy - 2); p_.cv.rotate(-150 * op)
            p_.fill(rrect(-3.5, -9, 7, 10, 1.5), _lighten(brass, 0.15)); p_.line(rrect(-3.5, -9, 7, 10, 1.5), 0.8, LINE)
            p_.cv.restore()
            p_.fill(oval(lx - 1.5, sy + 3, 1.2), '#fff4c0', 200)
        hx = W / 2
        p_.fill(rrect(hx - 9, sy - 3, 3, 6, 1), brass); p_.fill(rrect(hx + 6, sy - 3, 3, 6, 1), brass)
        p_.line(smooth([(hx - 7.5, sy - 1), (hx - 6, sy - 7), (hx + 6, sy - 7), (hx + 7.5, sy - 1)], False), 3.2, '#1a1820')
        for (cx_, cy_) in ((2, 2), (W - 2, 2), (2, H - 2), (W - 2, H - 2)):
            p_.fill(oval(cx_, cy_, 3.2), brass, 230)

    def end_art(p_, W, H):
        p_.linear(rect(0, 0, W, H), 0, 0, W, 0, [leather, '#3a3742', ld]); stitch(p_, W, H)
        p_.fill(rect(0, H * 0.38 - 1.2, W, 2.4), '#0a090c')
        for (cx_, cy_) in ((2, 2), (W - 2, 2), (2, H - 2), (W - 2, H - 2)): p_.fill(oval(cx_, cy_, 3.2), brass, 230)

    def lid_art(p_, W, H):                                 # the top of the lid (W across the case, H along it)
        p_.linear(rect(0, 0, W, H), 0, 0, W, H, ['#34313c', leather, '#1c1a22'])
        p_.texture(rect(0, 0, W, H), 'grunge', 0.4, 'overlay', 0.6); stitch(p_, W, H)
        p_.fill(poly([(W * 0.1, 0), (W * 0.35, 0), (W * 0.05, H * 0.4), (0, H * 0.3)]), '#ffffff', 22)
        if envelope:
            cv = p_.cv; cv.save(); cv.translate(W * 0.52, H * 0.55); cv.rotate(-4)
            e = rect(-14, -8.5, 28, 17)
            p_.fill(rect(-13, -7.5, 28, 17), '#000000', 90)
            p_.fill(e, '#ece2c8'); p_.texture(e, 'paper', 0.5, 'overlay', 0.4)
            p_.line(poly([(-14, -8.5), (0, 1.5), (14, -8.5)], False), 0.5, '#8a7a60', 160)
            for (tx, ang) in ((-12, 35), (12, -35)):
                cv.save(); cv.translate(tx, -8.5); cv.rotate(ang); p_.fill(rect(-5, -1.6, 10, 3.2), '#e8d8a0', 170); cv.restore()
            for i in range(3):
                p_.line(smooth([(-7 + i * 0.6, 2 + i * 2.2), (-2, 1 + i * 2.2), (3, 2.4 + i * 2.2), (8 - i * 2, 1.4 + i * 2.2)], False), 0.45, '#2a3060', 200)
            cv.restore()

    if state == 'closed':
        _hbox(pen, hv, x0, x1, Y0, Y0 + h, y0, y1, leather, faces={'front': end_art, 'side': front_art, 'top': lid_art},
              lw=max(1.0, 0.006 * hv.s(y0)))
        return
    # open: the base, the velvet inside, the lid standing up against the wall behind it
    hb = h * 0.62
    Yt = Y0 + hb
    lid = [(x0 + 0.01, Yt + 0.42, y1), (x0 + 0.01, Yt + 0.42, y0), (x0 + 0.03, Yt, y0), (x0 + 0.03, Yt, y1)]
    lq = hv.quad(lid)
    pen.fill(lq, '#7a1420'); _hface(pen, hv, *lid, 82, 42, lambda p_: (p_.fill(rect(0, 0, 82, 42), '#8a1a26'), p_.texture(rect(0, 0, 82, 42), 'fabric', 0.7, 'overlay', 0.5),
                                                                      p_.line(rect(2, 2, 78, 38), 1.0, '#4a0a12', 200),
                                                                      p_.fill(rect(30, 8, 22, 12), '#5a0e18', 150)))
    pen.line(lq, 1.5, LINE, 220)
    _hbox(pen, hv, x0, x1, Y0, Yt, y0, y1, leather, faces={'front': end_art, 'side': front_art}, lw=max(1.0, 0.006 * hv.s(y0)))
    m = 0.025
    inner = [(x0 + m, Yt, y1 - m), (x1 - m, Yt, y1 - m), (x1 - m, Yt, y0 + m), (x0 + m, Yt, y0 + m)]
    pen.fill(hv.quad(inner), '#3a0810')
    bot = [(x0 + m, Y0 + 0.03, y1 - m), (x1 - m, Y0 + 0.03, y1 - m), (x1 - m, Y0 + 0.03, y0 + m), (x0 + m, Y0 + 0.03, y0 + m)]
    cv = pen.cv; cv.save(); cv.clipPath(hv.quad(inner), skia.ClipOp.kIntersect, True)
    _hface(pen, hv, *bot, 35, 77, lambda p_: _velvet_hollow(p_, 35, 77))
    wall_far = hv.quad([(x0 + m, Y0 + 0.03, y1 - m), (x1 - m, Y0 + 0.03, y1 - m), (x1 - m, Yt, y1 - m), (x0 + m, Yt, y1 - m)])
    pen.fill(wall_far, '#6a1018'); pen.texture(wall_far, 'fabric', 0.6, 'overlay', 0.5)
    wall_l = hv.quad([(x0 + m, Y0 + 0.03, y0 + m), (x0 + m, Y0 + 0.03, y1 - m), (x0 + m, Yt, y1 - m), (x0 + m, Yt, y0 + m)])
    pen.fill(wall_l, '#7a1420'); pen.texture(wall_l, 'fabric', 0.6, 'overlay', 0.5)
    cv.restore()
    pen.line(hv.quad(inner), 1.5, '#c9a24a', 200)


def _velvet_hollow(p_, W, H):
    """Red velvet bed of the case with the dummy-shaped hollow (head at the far end, top of the frame), seen from above."""
    p_.fill(rect(0, 0, W, H), '#9a1c2a'); p_.texture(rect(0, 0, W, H), 'fabric', 0.75, 'overlay', 0.4)
    p_.radial(rect(0, 0, W, H), W / 2, H * 0.45, H * 0.6, [(0, '#c8303e', 120), (1, '#4a0810', 160)])
    cx = W / 2
    sil = union(oval(cx, H * 0.14, W * 0.2, W * 0.22),                                                  # head
                smooth([(cx - W * 0.28, H * 0.27), (cx + W * 0.28, H * 0.27), (cx + W * 0.3, H * 0.55), (cx + W * 0.22, H * 0.6),
                        (cx + W * 0.2, H * 0.94), (cx + W * 0.03, H * 0.95), (cx, H * 0.62), (cx - W * 0.03, H * 0.95), (cx - W * 0.2, H * 0.94),
                        (cx - W * 0.22, H * 0.6), (cx - W * 0.3, H * 0.55)], True, 0.35))
    sil = union(sil, smooth([(cx - W * 0.3, H * 0.29), (cx - W * 0.42, H * 0.45), (cx - W * 0.36, H * 0.58), (cx - W * 0.27, H * 0.5)], True, 0.5))
    sil = union(sil, smooth([(cx + W * 0.3, H * 0.29), (cx + W * 0.42, H * 0.45), (cx + W * 0.36, H * 0.58), (cx + W * 0.27, H * 0.5)], True, 0.5))
    p_.fill(sil, '#4a0610')
    p_.cv.save(); p_.cv.clipPath(sil, skia.ClipOp.kIntersect, True)
    p_.radial(sil, cx - W * 0.1, H * 0.35, H * 0.5, [(0, '#6a0c18', 200), (1, '#2a0208', 230)])
    p_.cv.restore()
    p_.line(sil, 1.6, '#d8485a', 150)                                                                   # the lit rim of the hollow
    p_.line(moved(sil, 0.8, 1.0), 1.2, '#1a0006', 160)


def _bench_art(pen, hv):
    """The carved hall bench against the left wall (seat, high back panel, arms), Grandpa's hat and coat on the hooks."""
    x0, x1, y0, y1, Ys = BENCH
    wood = '#5a3420'
    _hbox(pen, hv, x0, x1, Ys - 0.06, Ys, y0, y1, wood, tex='wood', lw=max(1.0, 0.006 * hv.s(y0)))
    _hbox(pen, hv, x0 + 0.04, x1 - 0.04, 0.0, Ys - 0.06, y0 + 0.04, y0 + 0.08, _darken(wood, 0.3))
    _hbox(pen, hv, x0 + 0.04, x1 - 0.04, 0.0, Ys - 0.06, y1 - 0.08, y1 - 0.04, _darken(wood, 0.3))
    for yy in (y0, y1 - 0.06):
        _hbox(pen, hv, x0, x1, Ys, Ys + 0.24, yy, yy + 0.06, wood, tex='wood')
    bp = hv.quad([(x0 + 0.01, Ys, y0), (x0 + 0.01, Ys, y1), (x0 + 0.01, 1.12, y1), (x0 + 0.01, 1.12, y0)])
    pen.fill(bp, _darken(wood, 0.1)); pen.texture(bp, 'wood', 0.5, 'overlay', 1.0, 0)
    _hface(pen, hv, (x0 + 0.012, 1.12, y0), (x0 + 0.012, 1.12, y1), (x0 + 0.012, Ys, y1), (x0 + 0.012, Ys, y0), (y1 - y0) * 100, (1.12 - Ys) * 100,
           lambda p_: [p_.line(rect(6 + i * ((y1 - y0) * 100 - 12) / 3, 8, ((y1 - y0) * 100 - 12) / 3 - 6, (1.12 - Ys) * 100 - 16), 2.0, '#1a0e06', 160)
                       for i in range(3)])
    pen.line(bp, 1.5, LINE, 200)
    # hooks rail above with Grandpa's long coat and fedora
    rail = hv.quad([(x0 + 0.005, 1.72, y0 + 0.1), (x0 + 0.005, 1.72, y1 - 0.1), (x0 + 0.005, 1.64, y1 - 0.1), (x0 + 0.005, 1.64, y0 + 0.1)])
    pen.fill(rail, wood); pen.line(rail, 1.2, LINE, 200)
    cy_ = y0 + 0.55
    hx, hy = hv.p(x0 + 0.07, 1.68, cy_); s = hv.s(cy_)
    pen.fill(oval(hx, hy, 0.015 * s), '#c9a24a')
    coat = smooth([(hx - 0.02 * s, hy), (hx + 0.03 * s, hy), (hx + 0.13 * s, hy + 0.1 * s), (hx + 0.15 * s, hy + 0.55 * s), (hx + 0.18 * s, hy + 1.02 * s),
                   (hx + 0.02 * s, hy + 1.06 * s), (hx - 0.13 * s, hy + 1.03 * s), (hx - 0.12 * s, hy + 0.5 * s), (hx - 0.11 * s, hy + 0.1 * s)], True, 0.35)
    pen.fill(coat, '#34343c'); pen.texture(coat, 'fabric', 0.6, 'overlay', 1.0)
    pen.cv.save(); pen.cv.clipPath(coat, skia.ClipOp.kIntersect, True)
    pen.linear(coat, hx - 0.13 * s, 0, hx + 0.18 * s, 0, [(0, '#000000', 110), (0.45, '#000000', 0), (1, '#000000', 140)])
    for sx in (-1, 1):                                                   # the sleeves hanging at its sides
        pen.line(smooth([(hx + sx * 0.1 * s, hy + 0.12 * s), (hx + sx * 0.13 * s, hy + 0.45 * s), (hx + sx * 0.11 * s, hy + 0.72 * s)], False),
                 max(1.0, 0.012 * s), '#16161c', 220)
    pen.cv.restore()
    lap = smooth([(hx - 0.06 * s, hy + 0.04 * s), (hx + 0.07 * s, hy + 0.04 * s), (hx + 0.02 * s, hy + 0.36 * s), (hx - 0.01 * s, hy + 0.36 * s)], True, 0.4)
    pen.fill(lap, '#24242a'); pen.line(lap, max(0.8, 0.005 * s), LINE, 200)
    for k in range(3): pen.fill(oval(hx + 0.005 * s, hy + (0.45 + 0.13 * k) * s, 0.012 * s), '#1a1410')
    pen.line(coat, max(1.0, 0.007 * s), LINE, 220)
    fx, fy = hv.p(x0 + 0.08, 1.74, y0 + 0.2); fs = hv.s(y0 + 0.2)
    brim = oval(fx, fy, 0.15 * fs, 0.04 * fs)
    crown = smooth([(fx - 0.1 * fs, fy), (fx - 0.09 * fs, fy - 0.12 * fs), (fx, fy - 0.1 * fs), (fx + 0.09 * fs, fy - 0.12 * fs), (fx + 0.1 * fs, fy)], True, 0.6)
    pen.fill(brim, '#4a3a2a'); pen.fill(crown, '#4a3a2a'); pen.fill(rect(fx - 0.1 * fs, fy - 0.035 * fs, 0.2 * fs, 0.025 * fs), '#1a1410')
    pen.line(union(brim, crown), max(1.0, 0.006 * fs), LINE, 220)


def _stairs_house(pen, hv, light='#000000'):
    """The staircase along the right wall (x 0.5..1.35) rising toward the back, its side panel with the closet door,
    balusters, handrail and newel post (drawn far -> near; works from any camera that looks along +y)."""
    xa, xb = STAIR_X
    side = [(xa, 0, STAIR_Y0)]
    for k in range(STAIR_N):
        yk = STAIR_Y0 + k * STAIR_RUN
        side += [(xa, (k + 1) * STAIR_RISE, yk), (xa, (k + 1) * STAIR_RISE, yk + STAIR_RUN)]
    side += [(xa, 0, STAIR_Y0 + STAIR_N * STAIR_RUN)]
    panel = hv.quad(side)
    pen.fill(panel, '#8a7a62'); pen.texture(panel, 'plaster', 0.3, 'overlay', 0.8)
    cd = hv.quad([(xa, 0, 2.4), (xa, 1.2, 2.4), (xa, 1.2, 3.05), (xa, 0, 3.05)])
    pen.fill(cd, '#5a3a24'); pen.texture(cd, 'wood', 0.5, 'overlay', 1.0, 90); pen.line(cd, 2, LINE, 220)
    pen.fill(oval(*hv.p(xa, 0.58, 2.52), max(1.5, 0.018 * hv.s(2.52))), '#c9a64a')
    pen.line(panel, 2, LINE, 200)
    for k in range(STAIR_N - 1, -1, -1):
        yk = STAIR_Y0 + k * STAIR_RUN; Y0, Y1 = k * STAIR_RISE, (k + 1) * STAIR_RISE
        if hv.d(yk) < 0.08: continue
        if Y1 < hv.cam_h:
            pen.fill(hv.quad([(xa, Y1, yk), (xb, Y1, yk), (xb, Y1, yk + STAIR_RUN), (xa, Y1, yk + STAIR_RUN)]), '#6a4228')
            pen.fill(hv.quad([(xa + 0.15, Y1, yk), (xb - 0.12, Y1, yk), (xb - 0.12, Y1, yk + STAIR_RUN), (xa + 0.15, Y1, yk + STAIR_RUN)]), '#6a1e24')
        r = hv.quad([(xa, Y0, yk), (xb, Y0, yk), (xb, Y1, yk), (xa, Y1, yk)])
        pen.fill(r, '#3a2416')
        pen.fill(hv.quad([(xa + 0.15, Y0, yk - 0.001), (xb - 0.12, Y0, yk - 0.001), (xb - 0.12, Y1, yk - 0.001), (xa + 0.15, Y1, yk - 0.001)]), '#4a141a')
        pen.line(poly([hv.p(xa, Y1, yk), hv.p(xb, Y1, yk)], False), max(1.5, 0.012 * hv.s(yk)), '#a8804a', 230)
        pen.line(poly([hv.p(xa + 0.15, Y0 + 0.012, yk), hv.p(xb - 0.12, Y0 + 0.012, yk)], False), max(1.0, 0.008 * hv.s(yk)), '#c9a64a', 200)

    def Yh(y): return 0.95 + STAIR_RISE + (y - STAIR_Y0) * STAIR_RISE / STAIR_RUN
    for k in range(STAIR_N):
        for f in (0.3, 0.75):
            y = STAIR_Y0 + k * STAIR_RUN + STAIR_RUN * f
            if hv.d(y) < 0.1: continue
            a_, b_ = hv.p(xa + 0.05, (k + 1) * STAIR_RISE, y), hv.p(xa + 0.05, Yh(y), y)
            w = max(2.0, 0.024 * hv.s(y))
            pen.seg(a_, b_, w + 2, LINE, 200); pen.seg(a_, b_, w, '#5a3420'); pen.seg((a_[0] - w * 0.2, a_[1]), (b_[0] - w * 0.2, b_[1]), w * 0.3, '#a07a50', 150)
    ys = [y for y in np.linspace(STAIR_Y0 - 0.05, STAIR_Y0 + STAIR_N * STAIR_RUN, 12) if hv.d(y) > 0.1]
    rail = [hv.p(xa + 0.05, Yh(y), y) for y in ys]
    if len(rail) > 1:
        pen.line(poly(rail, False), max(5.0, 0.055 * hv.s(1.6)), LINE); pen.line(poly(rail, False), max(3.5, 0.042 * hv.s(1.6)), '#4a2a16')
        pen.line(poly(rail, False), max(1.0, 0.01 * hv.s(1.6)), '#c8986a', 120)
    if hv.d(STAIR_Y0 - 0.05) > 0.12:
        nx, ny = hv.p(xa + 0.05, 0, STAIR_Y0 - 0.05); s0 = hv.s(STAIR_Y0 - 0.05)
        post = rect(nx - 0.06 * s0, ny - 1.15 * s0, 0.12 * s0, 1.15 * s0)
        pen.shape(post, '#4a2a16', 3); pen.fill(rect(nx + 0.02 * s0, ny - 1.15 * s0, 0.04 * s0, 1.15 * s0), '#2a160a')
        pen.shape(oval(nx, ny - 1.26 * s0, 0.07 * s0), '#5a3420', 3); pen.fill(oval(nx - 0.02 * s0, ny - 1.28 * s0, 0.02 * s0), '#c8986a', 160)


HALL_PAPER, HALL_INK = '#4f6a52', '#36503a'


def _hall_walls_art(pen, hv, den=0.0):
    """Left wall (living-room arch, Grandpa's poster and photos), right wall above the stairs (photos up the stairs),
    the den door at the end on the right, the ceiling and the upstairs gallery."""
    xa, xb = HALL_X
    yn = hv.hy + 0.3 * hv.f

    def left_art(p_, W, H):
        u = lambda y: (y - yn) * 100
        _hframe(p_, W, H, u(2.78), H - 205, 52, 66, 'poster', fn=lambda q, w, h: _poster_art(q, w, h, '1974'))
        for i, (y, Yc, w, h) in enumerate(((3.05, 1.82, 22, 28), (5.15, 1.6, 30, 24), (5.55, 1.88, 20, 26))):
            _hframe(p_, W, H, u(y), H - Yc * 100, w, h, 'photo', seed=i + 1)
    _hwall(pen, hv, (xa, yn), (xa, HALL_BACK), 0.0, CEIL, HALL_PAPER, HALL_INK, 'damask', 0.95,
           holes=[(ARCH_Y[0] - yn, 0.0, ARCH_Y[1] - yn, 2.3, 'arch')], art=left_art, rail=2.2, seed=1)

    def right_art(p_, W, H):
        u = lambda y: (y - yn) * 100
        for i in range(5):
            y = 1.3 + i * 0.62; Yc = 1.75 + (y - STAIR_Y0) * STAIR_RISE / STAIR_RUN
            _hframe(p_, W, H, u(y), H - (Yc + 0.3) * 100, 24 + 6 * (i % 2), 30, 'photo', seed=10 + i)
    _hwall(pen, hv, (xb, yn), (xb, HALL_BACK), 0.0, 5.2, HALL_PAPER, HALL_INK, 'damask', 0.0,
           holes=[(4.85 - yn, 0.0, 5.75 - yn, 2.05)], art=right_art, seed=2)
    # den door (dark panelled, ajar by `den`)
    dq = [(xb, 2.05, 4.85), (xb, 2.05, 5.75), (xb, 0.0, 5.75), (xb, 0.0, 4.85)]
    pen.fill(hv.quad(dq), '#07070a')
    ang = math.radians(80.0) * clamp(den)
    xf = xb - 0.9 * math.sin(ang); yf = 4.85 + 0.9 * math.cos(ang)
    leaf = [(xb, 2.05, 4.85), (xf, 2.05, yf), (xf, 0.0, yf), (xb, 0.0, 4.85)]
    _hface(pen, hv, *leaf, 90, 205, lambda p_: (p_.fill(rect(0, 0, 90, 205), '#4a2a18'), p_.texture(rect(0, 0, 90, 205), 'wood', 0.6, 'overlay', 0.8, 90),
                                               [p_.line(rect(12, 12 + j * 64, 66, 54), 2.0, '#1a0c06', 170) for j in range(3)],
                                               p_.fill(oval(80, 105, 3.5), '#c9a24a')))
    pen.line(hv.quad(leaf), 1.5, LINE, 200)
    # ceiling over the corridor + under the landing; the stairwell opening; the gallery fascia and railing
    _hceil(pen, hv, xa, STAIR_X[0], yn, HALL_BACK, CEIL, '#9a8e78')
    _hceil(pen, hv, STAIR_X[0], xb, yn, 1.3, CEIL, '#9a8e78')
    _hceil(pen, hv, STAIR_X[0], xb, 4.6, HALL_BACK, 2.66, '#9a8e78')
    pen.fill(hv.quad([(STAIR_X[0], CEIL, 1.3), (xb, CEIL, 1.3), (xb, 5.2, 1.3), (STAIR_X[0], 5.2, 1.3)]), '#14141a')
    pen.fill(hv.quad([(STAIR_X[0], CEIL, 1.3), (STAIR_X[0], CEIL + 0.22, 1.3), (STAIR_X[0], CEIL + 0.22, 4.6), (STAIR_X[0], CEIL, 4.6)]), '#5a4630')
    for y in np.arange(1.45, 4.55, 0.17):
        a_, b_ = hv.p(STAIR_X[0] + 0.02, CEIL + 0.22, y), hv.p(STAIR_X[0] + 0.02, CEIL + 1.1, y)
        pen.seg(a_, b_, max(2.0, 0.024 * hv.s(y)), '#5a3420')
    pen.line(poly([hv.p(STAIR_X[0] + 0.02, CEIL + 1.1, 1.35), hv.p(STAIR_X[0] + 0.02, CEIL + 1.1, 4.55)], False), max(4.0, 0.05 * hv.s(1.6)), '#3a2010')
    # the ceiling fixture (frosted bowl) base
    fx, fy = hv.p(-0.42, CEIL, 2.6); fs = hv.s(2.6)
    pen.fill(oval(fx, fy + 0.02 * fs, 0.12 * fs, 0.03 * fs), '#8a7a5a')


def _poster_art(pen, w, h, kind='1974'):
    """Framed show posters (cm frame w x h). '1974': SATURDAY MORNING with WALTER KEMP (the TV show, orange sunburst);
    '1962': THE AMAZING WALTER KEMP & MISTER WINKS at the Palace (sepia); 'live': WALTER KEMP LIVE (teal, 60s)."""
    cv = pen.cv
    if kind == '1974':
        pen.fill(rect(0, 0, w, h), '#f2c23a')
        cx, cy = w / 2, h * 0.42
        for k in range(14):
            a0 = k * math.pi / 7; a1 = a0 + math.pi / 14
            pen.fill(poly([(cx, cy), (cx + math.cos(a0) * w, cy + math.sin(a0) * w), (cx + math.cos(a1) * w, cy + math.sin(a1) * w)]), '#ef8a2a')
        pen.fill(oval(cx, cy, w * 0.2), '#c8322a')
        _winks_face(pen, cx, cy, w * 0.17)
        pen.fill(rect(0, h * 0.7, w, h * 0.3), '#2a6a8a')
        text(cv, 'SATURDAY', w / 2, h * 0.79, 900, h * 0.075, '#f4ead0', 255, 0.06)
        text(cv, 'MORNING', w / 2, h * 0.87, 900, h * 0.075, '#f4ead0', 255, 0.06)
        text(cv, 'WITH WALTER KEMP', w / 2, h * 0.95, 800, h * 0.045, '#f2c23a', 255, 0.08)
    elif kind == '1962':
        pen.fill(rect(0, 0, w, h), '#e2d0a8'); pen.texture(rect(0, 0, w, h), 'paper', 0.6, 'overlay', 0.5)
        text(cv, 'THE PALACE', w / 2, h * 0.1, 800, h * 0.05, '#5a3a20', 255, 0.2)
        text(cv, 'WALTER KEMP', w / 2, h * 0.24, 900, h * 0.09, '#3a2210', 255, 0.04)
        pen.fill(oval(w / 2, h * 0.5, w * 0.26), '#5a3a20'); _winks_face(pen, w / 2, h * 0.5, w * 0.22, sepia=True)
        text(cv, '& MISTER WINKS', w / 2, h * 0.84, 900, h * 0.07, '#3a2210', 255, 0.04)
        text(cv, 'FIRST APPEARANCE  •  1962', w / 2, h * 0.93, 700, h * 0.035, '#5a3a20', 255, 0.12)
    else:
        pen.fill(rect(0, 0, w, h), '#2a7a7a')
        text(cv, 'LIVE!', w / 2, h * 0.18, 900, h * 0.12, '#f2c23a', 255, 0.06)
        _winks_face(pen, w / 2, h * 0.5, w * 0.24)
        text(cv, 'WALTER KEMP', w / 2, h * 0.86, 900, h * 0.08, '#f4ead0', 255, 0.04)


def _winks_face(pen, cx, cy, r, sepia=False, grin=0.0):
    """Mister Winks's painted face as printed on posters, mugs and photos: red side-parted hair, pillbox cap, freckles,
    rosy cheeks, big glossy eyes, the two slot lines of the hinged jaw and the painted grin (a graphic, not the cast rig)."""
    c = (lambda h: mix(h, '#a08060', 0.75)) if sepia else (lambda h: h)
    face = smooth([(cx - r * 0.78, cy - r * 0.2), (cx - r * 0.7, cy - r * 0.78), (cx, cy - r), (cx + r * 0.7, cy - r * 0.78), (cx + r * 0.78, cy - r * 0.2),
                   (cx + r * 0.62, cy + r * 0.62), (cx, cy + r * 0.95), (cx - r * 0.62, cy + r * 0.62)], True, 0.7)
    pen.fill(face, c('#ecc4ad')); pen.line(face, max(1.0, r * 0.04), LINE)
    hair = smooth([(cx - r * 0.82, cy - r * 0.1), (cx - r * 0.86, cy - r * 0.75), (cx - r * 0.2, cy - r * 1.08), (cx + r * 0.6, cy - r * 0.98),
                   (cx + r * 0.86, cy - r * 0.55), (cx + r * 0.75, cy - r * 0.42), (cx + r * 0.1, cy - r * 0.62), (cx - r * 0.45, cy - r * 0.5),
                   (cx - r * 0.66, cy - r * 0.08)], True, 0.6)
    pen.fill(hair, c('#b9431f')); pen.line(hair, max(1.0, r * 0.035), LINE)
    pen.line(smooth([(cx - r * 0.3, cy - r * 0.98), (cx - r * 0.42, cy - r * 0.62)], False), max(0.8, r * 0.03), c('#7a2410'))
    cap = rrect(cx + r * 0.05, cy - r * 1.28, r * 0.62, r * 0.36, r * 0.08)
    pen.fill(cap, c('#7d1d2b')); pen.fill(rect(cx + r * 0.05, cy - r * 1.0, r * 0.62, r * 0.07), c('#d6b257')); pen.line(cap, max(0.8, r * 0.03), LINE)
    for sx in (-1, 1):
        ex, ey = cx + sx * r * 0.33, cy - r * 0.18
        pen.fill(oval(ex, ey, r * 0.2, r * 0.23), '#ffffff' if not sepia else '#efe2c8'); pen.line(oval(ex, ey, r * 0.2, r * 0.23), max(0.8, r * 0.03), LINE)
        pen.fill(oval(ex + r * 0.02, ey + r * 0.02, r * 0.11), c('#6f97b8')); pen.fill(oval(ex + r * 0.02, ey + r * 0.02, r * 0.055), '#0a0a10')
        pen.fill(oval(ex - r * 0.03, ey - r * 0.04, r * 0.035), '#ffffff')
        pen.fill(oval(cx + sx * r * 0.5, cy + r * 0.22, r * 0.17, r * 0.11), c('#d8455a'), 150)
    for i in range(7):
        pen.fill(oval(cx + (i - 3) * r * 0.1, cy + r * (0.08 + 0.05 * (i % 2)), r * 0.022), c('#a85a3a'), 200)
    gw = r * (0.42 + 0.12 * grin)
    pen.fill(smooth([(cx - gw, cy + r * 0.38), (cx, cy + r * (0.52 + 0.05 * grin)), (cx + gw, cy + r * 0.38), (cx, cy + r * 0.62)], True, 0.7), c('#b01f2d'))
    for sx in (-1, 1):
        pen.line(poly([(cx + sx * r * 0.3, cy + r * 0.44), (cx + sx * r * 0.32, cy + r * 0.86)], False), max(0.8, r * 0.035), '#3a2418')


def _grandfather_clock(pen, hv, x, y, t, clock='12:40', part='case'):
    """A tall grandfather clock against the end wall (x, y = front-centre on the floor). part 'case' (static) or 'live'
    (the dial hands for `clock` = 'H:MM' or f(t) -> minutes past midnight, and the pendulum swinging at 0.5 Hz)."""
    s = hv.s(y)
    bx, by = hv.p(x, 0.0, y)
    w = 0.5 * s
    if part == 'case':
        body = poly([(bx - w * 0.5, by), (bx + w * 0.5, by), (bx + w * 0.42, by - 1.45 * s), (bx + w * 0.5, by - 1.55 * s), (bx + w * 0.5, by - 2.15 * s),
                     (bx - w * 0.5, by - 2.15 * s), (bx - w * 0.5, by - 1.55 * s), (bx - w * 0.42, by - 1.45 * s)])
        pen.fill(body, '#4a2614'); pen.texture(body, 'wood', 0.6, 'overlay', 1.2, 90); pen.line(body, max(1.0, 0.01 * s), LINE)
        hood = smooth([(bx - w * 0.56, by - 2.15 * s), (bx - w * 0.5, by - 2.3 * s), (bx, by - 2.4 * s), (bx + w * 0.5, by - 2.3 * s), (bx + w * 0.56, by - 2.15 * s)], True, 0.6)
        pen.shape(hood, '#3a1c0e', max(1.0, 0.01 * s))
        win = rrect(bx - w * 0.28, by - 1.4 * s, w * 0.56, 0.9 * s, w * 0.1)
        pen.fill(win, '#0c0806'); pen.fill(poly([(bx - w * 0.28, by - 1.0 * s), (bx - w * 0.1, by - 1.4 * s), (bx + w * 0.02, by - 1.4 * s), (bx - w * 0.28, by - 0.8 * s)]), '#ffffff', 30)
        pen.line(win, max(1.0, 0.008 * s), '#c9a24a')
        pen.fill(oval(bx, by - 1.85 * s, w * 0.36), '#efe6cc'); pen.line(oval(bx, by - 1.85 * s, w * 0.36), max(1.0, 0.012 * s), '#c9a24a')
        for k in range(12):
            a = k * math.pi / 6
            pen.seg((bx + math.cos(a) * w * 0.29, by - 1.85 * s + math.sin(a) * w * 0.29), (bx + math.cos(a) * w * 0.33, by - 1.85 * s + math.sin(a) * w * 0.33),
                    max(0.8, 0.006 * s), '#2a2014')
        return
    # live: hands + pendulum
    if callable(clock): mins = clock(t)
    else:
        hh, mm = (int(v) for v in str(clock).split(':')); mins = hh * 60 + mm + t / 60.0
    cx, cy = bx, by - 1.85 * s
    ah = math.radians((mins / 60.0 % 12) * 30 - 90); am = math.radians((mins % 60) * 6 - 90)
    pen.seg((cx, cy), (cx + math.cos(ah) * w * 0.18, cy + math.sin(ah) * w * 0.18), max(1.2, 0.012 * s), '#1a1410')
    pen.seg((cx, cy), (cx + math.cos(am) * w * 0.28, cy + math.sin(am) * w * 0.28), max(1.0, 0.008 * s), '#1a1410')
    sw = 0.16 * math.sin(t * math.pi)                                        # 1 s period: tick on every swing end
    px, py = cx, by - 1.38 * s
    ex, ey = px + math.sin(sw) * 0.62 * s, py + math.cos(sw) * 0.62 * s
    pen.cv.save(); pen.cv.clipPath(rrect(bx - w * 0.28, by - 1.4 * s, w * 0.56, 0.9 * s, w * 0.1), skia.ClipOp.kIntersect, True)
    pen.seg((px, py), (ex, ey), max(1.0, 0.008 * s), '#b89040')
    pen.fill(oval(ex, ey, 0.06 * s), '#c9a24a'); pen.fill(oval(ex - 0.015 * s, ey - 0.015 * s, 0.02 * s), '#fff0c0', 180)
    pen.cv.restore()


def pendulum_ticks(t0, t1):
    """Grandfather-clock tick times between t0 and t1 (one per pendulum swing end, 1 s apart) -> [t] for the SFX."""
    k = math.ceil(t0 - 0.5); out = []
    while k + 0.5 <= t1:
        out.append(round(k + 0.5, 3)); k += 1
    return out


def _beam_fn(beam):
    """beam spec -> f(t) -> None | (x, Y, y, aim_x, aim_Y, aim_y, k): a flashlight carried at knee height. beam =
    dict(keys=[(t, x, y), ...] (house coords on the floor plan), Y=0.5, aim=(dx, dY, dy) direction (default along the
    walk), on=t (clicks on), off=t) or f(t) returning the tuple."""
    if beam is None: return lambda t: None
    if callable(beam): return beam
    ks = sorted(beam['keys']); Yb = beam.get('Y', 0.5); on = beam.get('on', ks[0][0]); off = beam.get('off', 1e9)
    aim = beam.get('aim')

    def f(t):
        if t < on or t > off: return None
        if t <= ks[0][0]: x, y = ks[0][1], ks[0][2]; i = 0
        elif t >= ks[-1][0]: x, y = ks[-1][1], ks[-1][2]; i = len(ks) - 2
        else:
            for i in range(len(ks) - 1):
                if ks[i][0] <= t <= ks[i + 1][0]:
                    u = ease_in_out((t - ks[i][0]) / max(1e-6, ks[i + 1][0] - ks[i][0]))
                    x = lerp(ks[i][1], ks[i + 1][1], u); y = lerp(ks[i][2], ks[i + 1][2], u); break
        if aim: ax, aY, ay = aim
        else:
            i = max(0, min(i, len(ks) - 2)); ax, ay = ks[i + 1][1] - ks[i][1], ks[i + 1][2] - ks[i][2]; aY = -0.15
            n = math.hypot(ax, ay) or 1.0; ax, ay = ax / n, ay / n
        k = clamp((t - on) / 0.05) * (1.0 - 0.06 * (0.5 + 0.5 * noise1(t * 9.0, 41)))
        bob = 0.015 * math.sin(t * 2 * math.pi * 1.6)                           # a little walker's bob
        return (x, Yb + bob, y, ax, aY, ay, k)
    return f


def _beam_layers(hv, bf, name='beam', order_max=None):
    """The knee-high flashlight: the beam cone, its pool on the floor and walls (live, depth follows it). order_max: draw
    it no deeper than this (over a floor / wall plate that is one layer nearer than the beam really is)."""
    def depth(t):
        b = bf(t)
        return hv.d(b[2]) if b else 50.0

    R = 4.0                                                                      # authored at ref depth R (the depth moves)

    def draw(pen, t):
        b = bf(t)
        if not b: return
        x, Y, y, ax, aY, ay, k = b
        if hv.d(y) < 0.2: return
        g = hv.d(y) / R                                    # the engine scales this layer by R / depth: pre-scale so the
        pen.cv.save(); pen.cv.translate(960, 540); pen.cv.scale(g, g); pen.cv.translate(-960, -540)   # beam lands where hv puts it
        try: _beam_draw(pen, t, x, Y, y, ax, aY, ay, k)
        finally: pen.cv.restore()

    def _beam_draw(pen, t, x, Y, y, ax, aY, ay, k):
        px, py = hv.p(x, Y, y); s = hv.s(y)
        toward = -(ay * hv.f)                                                    # > 0: aimed back at the camera
        yl = y + ay * 1.4
        if hv.d(yl) > 0.2:                                                       # the pool where it lands on the floor
            fx, fy = hv.p(x + ax * 1.4, 0.0, yl); fs = hv.s(yl)
            pen.radial(None, fx, fy, 1.0 * fs, [(0, '#fff0c8', 150 * k), (0.45, '#ffe6b0', 60 * k), (1, '#ffe6b0', 0)], sy=0.32, clip=False)
        pen.radial(None, px, py + 0.3 * s, 2.2 * s, [(0, '#ffe8b8', 34 * k), (1, '#ffe8b8', 0)], sy=0.6, clip=False)   # spill round it
        if toward > 0.5:                                                         # pointed at you: a blinding disc + streak
            g = clamp((toward - 0.5) * 2)
            pen.glow(px, py, 0.9 * s * (0.6 + 0.4 * g), '#fff4d8', 200 * k * g)
            pen.glow(px, py, 0.18 * s, '#ffffff', 255 * k)
            pen.radial(None, px, py, 1.3 * s, [(0, '#fff4d8', 110 * k * g), (1, '#fff4d8', 0)], sy=0.06, clip=False)
        else:
            tx, ty = hv.p(x + ax * 1.0, Y + aY, y + ay * 1.0)
            _flashlight_beam(pen, px, py, tx, ty, s, k, 0.32, 2.4 * s)
            pen.glow(px, py, 0.22 * s, '#fff8e8', 230 * k)
    lay = Layer(depth, draw, name, blur=None, ref_depth=R)
    if order_max is not None: lay.order = lambda t: min(depth(t), order_max)
    return lay


def gp_hall(view='kitchen', light=1.0, kitchen=1.0, living=0.6, case='closed', envelope=True, latch=0.0, den=0.0, clock='12:40',
            beam=None, tod='night', steam=1.0, chair=True, mug=True, door=0.0):
    """Grandpa's front hall (green damask over walnut wainscot, the burgundy runner, the grandfather clock, framed show
    posters, the stairs on the right). view:
      'kitchen'  from just inside the front door down the hall to the KITCHEN OPENING at the end: through it, lit by the
                 amber pendant, Grandpa's chair at the table facing you (anchor 'kitchen_chair': where Mister Winks sits),
                 the steaming mug, the window behind; the hall bench with the black leather case (case 'closed' with the
                 envelope taped to the lid | 'open' (the red velvet hollow) | None) and Grandpa's coat and hat on the hooks;
                 the living-room arch (left) and the den door at the end on the right (den 0..1 ajar).
      'door'     the reverse: from the hall toward the front door (stairs coming down on the left, the bench on the right).
      'stairs'   from the foot of the stairs looking up (anchor 'step3': three steps up, where he sits at 3 AM).
    light = the hall's ceiling light (level spec: number | f(t) | dict(flick=, out=, on=, off=)), kitchen = the pendant,
    living = the living-room lamp glowing through the arch, beam = the knee-high flashlight moving down the hall
    (dict(keys=[(t, x, y)], on=t) on the floor plan; see _beam_fn), clock = the grandfather clock ('H:MM' runs on with t,
    or f(t) -> minutes past midnight; pendulum_ticks() gives its tick times). Lens 'lens', grade 'gp_house'
    ('gp_dark' with the lights off)."""
    if view == 'door': return _gp_hall_door(light, case, envelope, latch, tod, door)
    if view == 'stairs': return _gp_stairs(light, beam, tod)
    hv = HView(560, 470, 1.5, -0.35, 0.2, 1)
    kf, hf, lvf = _kfn(kitchen, 21), _kfn(light, 22), _kfn(living, 23)
    box = FRAME
    yn = hv.hy + 0.3
    amb = '#262c44'
    moon = [(-0.35, 0.0, 0.9, 1.8, GP_MOON, 0.35, 0.4), (-1.35, 1.2, 1.0, 1.4, GP_MOON, 0.25)]
    hall_l = [(-1.35, 1.6, 2.6, 2.6, GP_LAMP, 0.95), (0.5, 1.2, 2.4, 2.2, GP_LAMP, 0.75), (-0.4, 0.0, 2.6, 2.7, GP_LAMP, 0.9, 0.35),
              (-0.42, CEIL, 2.6, 1.0, GP_LAMP, 0.75), (-0.4, 1.5, HALL_BACK, 2.4, GP_LAMP, 0.35), (-1.1, 0.6, 1.9, 1.5, GP_LAMP, 0.7),
              (1.35, 2.2, 3.0, 2.2, GP_LAMP, 0.6)]
    kit_l = [(-0.45, 1.2, HALL_BACK, 1.7, GP_KLAMP, 0.6), (-0.45, 0.0, 5.2, 2.0, GP_KLAMP, 0.95, 0.3), (-1.35, 0.9, 5.4, 1.3, GP_KLAMP, 0.45),
             (0.5, 0.8, 5.0, 1.2, GP_KLAMP, 0.35), (1.35, 1.0, 5.5, 1.1, GP_KLAMP, 0.4)]
    liv_l = [(-1.35, 1.0, ARCH_Y[0] + 0.3, 1.1, GP_LAMP, 0.55), (-0.9, 0.0, 3.9, 1.2, GP_LAMP, 0.4, 0.35)]
    var = [('hall', hall_l, hf), ('kitchen', kit_l, kf), ('living', liv_l, lvf)]
    # the kitchen through the opening (only what the opening can show, with room for pushes and pans)
    ox0, oy0 = hv.p(KOPEN[0], KOPEN[2], HALL_BACK); ox1, oy1 = hv.p(KOPEN[1], 0.0, HALL_BACK)
    kbox = (ox0 - (ox1 - ox0) * 0.9, oy0 - (oy1 - oy0) * 0.5, ox1 + (ox1 - ox0) * 0.9, oy1 + (oy1 - oy0) * 0.35)
    L = _kitchen_layers(hv, 'hallk', kf, kbox, 'night', mug, steam, chair)

    def end_art(p_):
        _backing(p_, hv, HALL_BACK, -2.6, 2.6, -0.9, CEIL + 1.4, _darken(HALL_PAPER, 0.3), [(KOPEN[0], KOPEN[1], 0.0, KOPEN[2])])

        def art(q, W, H):
            _hframe(q, W, H, 165, H - 196, 34, 44, 'photo', seed=7)
        _hwall(p_, hv, (HALL_X[0], HALL_BACK), (HALL_X[1], HALL_BACK), 0.0, CEIL, HALL_PAPER, HALL_INK, 'damask', 0.95,
               holes=[(KOPEN[0] - HALL_X[0], 0.0, KOPEN[1] - HALL_X[0], KOPEN[2])], art=art, rail=2.2, seed=3)
        for jx, jf in ((KOPEN[0], 1), (KOPEN[1], -1)):                     # the opening's jambs (wall thickness)
            if (hv.hx - jx) * jf > 0:
                jq = hv.quad([(jx, KOPEN[2], HALL_BACK), (jx, KOPEN[2], HALL_BACK + 0.16), (jx, 0.0, HALL_BACK + 0.16), (jx, 0.0, HALL_BACK)])
                p_.fill(jq, '#5a3820'); p_.texture(jq, 'wood', 0.4, 'overlay', 1.0, 90); p_.line(jq, 1.2, LINE, 200)
        hq = hv.quad([(KOPEN[0], KOPEN[2], HALL_BACK), (KOPEN[1], KOPEN[2], HALL_BACK), (KOPEN[1], KOPEN[2], HALL_BACK + 0.16), (KOPEN[0], KOPEN[2], HALL_BACK + 0.16)])
        p_.fill(hq, '#4a2e18')
        _grandfather_clock(p_, hv, 0.85, HALL_BACK - 0.28, 0.0, clock, 'case')
    ebox = (hv.x(-2.6, HALL_BACK), hv.y(CEIL + 1.4, HALL_BACK), hv.x(2.6, HALL_BACK), hv.y(-0.9, HALL_BACK))
    L += _lit(hv.d(HALL_BACK), end_art, 'h_end', _key('gp', 'hall', 'end'), ebox, hv, amb, moon, var)

    def beyond(p_):                                                           # the dark living room through the arch
        q = hv.quad([(HALL_X[0], 0, ARCH_Y[0]), (HALL_X[0], 2.4, ARCH_Y[0]), (HALL_X[0], 2.4, ARCH_Y[1]), (HALL_X[0], 0, ARCH_Y[1])])
        b = q.getBounds()
        p_.fill(rect(b.left() - 60, b.top() - 20, b.width() + 120, b.height() + 40), '#3a3448')
        _hwall(p_, hv, (LIV_X[0], ARCH_Y[0] - 1.0), (LIV_X[0], ARCH_Y[1] + 1.0), 0.0, CEIL, '#7a6a40', '#5a4a2a', 'trellis', 0.0, seed=8)
        _hfloor(p_, hv, LIV_X[0], HALL_X[0], ARCH_Y[0] - 1.0, ARCH_Y[1] + 1.0, 'carpet', '#5a4a3a')
        _hbox(p_, hv, -4.0, -3.2, 0.0, 0.85, ARCH_Y[0] + 0.3, ARCH_Y[0] + 1.1, '#6a3a24')                          # an armchair back
    abox = (hv.x(HALL_X[0], ARCH_Y[1]) - 80, hv.y(2.6, ARCH_Y[0]), hv.x(HALL_X[0], ARCH_Y[0]) + 60, hv.gy(ARCH_Y[0]) + 40)
    L += _lit(hv.d(ARCH_Y[1]) + 1.2, beyond, 'h_arch', _key('gp', 'hall', 'arch'), abox, hv, '#1e2238', [], [('living', [(-3.0, 1.2, ARCH_Y[0] + 0.5, 2.6, GP_LAMP, 1.0)], lvf)])
    L += _lit(3.0, lambda p_: _hall_walls_art(p_, hv, den), 'h_walls', _key('gp', 'hall', 'walls', round(den, 2)), box, hv, amb, moon, var)
    fbox = (box[0], hv.gy(HALL_BACK) - 10, box[2], box[3])
    L += _lit(2.9, lambda p_: _hfloor(p_, hv, HALL_X[0], HALL_X[1], yn, HALL_BACK, 'boards', '#7a5234', '#4a2e1a',
                                       runner=(-0.95, 0.15, 0.55, 5.85, '#6a1c24', '#c8a050')), 'h_floor', _key('gp', 'hall', 'floor'), fbox, hv, amb, moon, var)
    sbox = (hv.x(STAIR_X[0], HALL_BACK) - 40, box[1], box[2], box[3])
    L += _lit(2.0, lambda p_: _stairs_house(p_, hv), 'h_stairs', _key('gp', 'hall', 'stairs'), sbox, hv, amb, moon, var)
    bbox = (box[0], hv.y(2.0, BENCH[2]), hv.x(BENCH[1] + 0.2, BENCH[2]), hv.gy(BENCH[2]) + 30)

    def bench(p_):
        _bench_art(p_, hv); _case3d(p_, hv, case, envelope, latch)
    L += _lit(hv.d(1.3), bench, 'h_bench', _key('gp', 'hall', 'bench', case, envelope, round(latch, 2)), bbox, hv, amb, moon, var)

    # practicals: the ceiling bowl glowing, the kitchen opening's haze, the clock's hands and pendulum, the beam
    def fixture(pen, t):
        k = hf(t)
        fx, fy = hv.p(-0.42, CEIL, 2.6); s = hv.s(2.6)
        bowl = smooth([(fx - 0.16 * s, fy + 0.02 * s), (fx - 0.12 * s, fy + 0.09 * s), (fx, fy + 0.12 * s), (fx + 0.12 * s, fy + 0.09 * s), (fx + 0.16 * s, fy + 0.02 * s)], True, 0.6)
        pen.fill(bowl, mix('#2e2c2a', '#fff6e0', k)); pen.line(bowl, 1.5, LINE, 200)
        if k > 0.02: pen.glow(fx, fy + 0.07 * s, 0.6 * s, '#ffe2b0', 120 * k)
    L.append(Layer(hv.d(2.6), fixture, 'h_fixture', blur=None))

    def haze(pen, t):
        k = kf(t)
        if k < 0.02: return
        cx_, cy_ = hv.p((KOPEN[0] + KOPEN[1]) / 2, 1.0, HALL_BACK); s = hv.s(HALL_BACK)
        pen.radial(None, cx_, cy_, 1.6 * s, [(0, '#ffc070', 46 * k), (1, '#ffc070', 0)], sy=1.2, clip=False)
    L.append(Layer(hv.d(HALL_BACK) - 0.05, haze, 'h_haze', blur=0))
    L.append(Layer(hv.d(HALL_BACK - 0.3), lambda pen, t: _grandfather_clock(pen, hv, 0.85, HALL_BACK - 0.28, t, clock, 'live'), 'h_clock', blur=None))
    bf = _beam_fn(beam)
    if beam is not None: L.append(_beam_layers(hv, bf, order_max=2.85))   # over the floor + wall plates (2.9 / 3.0)
    a = {'kitchen_chair': hv.anchor(GCHAIR[0], GCHAIR[1], 0.47, 'seated in Grandpa\'s chair (seat height; the table hides his legs)'),
         'kitchen_stand': hv.anchor(GCHAIR[0], GCHAIR[1], 0.5, 'standing ON the chair seat'),
         'kitchen_table': hv.anchor(GCHAIR[0], GCHAIR[1] - 0.3, TABLE[4], 'on the table in front of the chair (his glove)'),
         'mug': hv.anchor(GCHAIR[0] + 0.02, GCHAIR[1] - 0.42, TABLE[4], 'the mug'),
         'kitchen_door': hv.anchor(-0.45, HALL_BACK - 0.2, note='in the kitchen opening'),
         'hall_mid': hv.anchor(-0.45, 3.0), 'hall_near': hv.anchor(-0.4, 1.5), 'hall_end': hv.anchor(-0.45, 5.3),
         'case': hv.anchor((CASE[0] + CASE[1]) / 2, (CASE[2] + CASE[3]) / 2, CASE[4] + CASE[5], 'top of the case'),
         'bench_stand': hv.anchor(-0.65, 1.5, note='standing at the bench, looking down at the case'),
         'arch': hv.anchor(-1.2, (ARCH_Y[0] + ARCH_Y[1]) / 2, note='in the living-room arch'),
         'stairs_low': hv.anchor(0.92, STAIR_Y0 + 2 * STAIR_RUN + 0.13, 3 * STAIR_RISE, 'three steps up'),
         'stairs_mid': hv.anchor(0.92, STAIR_Y0 + 7 * STAIR_RUN + 0.13, 8 * STAIR_RISE),
         'den_door': hv.anchor(1.0, 5.3, note='at the den door')}
    paths = {'down_hall': [a['kitchen_door'], a['hall_end'], a['hall_mid'], a['hall_near']]}
    info = {'view': hv, 'kitchen': kf, 'hall_light': hf, 'living': lvf, 'beam': bf, 'kopen': (ox0, oy0, ox1, oy1),
            'cam_env': dict(x=(780, 1140), y=(470, 620), zoom=(1.0, 2.2), f=(1.0, 3.2), note='push down the hall to the opening')}
    return SetPiece('gp_hall', L, a, paths, lens='lens', grade='gp_house', focus=hv.d(GCHAIR[1]), dof=1.2, cover=FRAME, info=info)


UP_CEIL = 5.2                         # the upstairs ceiling over the stairwell
LANDING_Y = STAIR_Y0 + STAIR_N * STAIR_RUN


def _gp_stairs(light=0.0, beam=None, tod='night'):
    """From the foot of the stairs looking up: the flight rising away, the banister on the left over the dark hall (the
    kitchen opening glows at its end), the family photos climbing the right wall, the landing at the top under a tall
    moonlit window. Anchors: step3 (three steps up, where Mister Winks sits at 3 AM, facing down), step1, step6,
    landing, foot (where you stand). beam: his flashlight (dict(keys=[(t, x, y)], Y, aim=(dx, dY, dy)) on the plan);
    aim it at the lens (aim=(0, 0.45, -1)) and it flares."""
    hv = HView(540, 585, 1.5, 0.92, 0.12, 1)
    hf = _kfn(light, 31)
    box = FRAME
    amb = '#202640'
    moon = [(0.9, 3.9, 6.0, 2.4, GP_MOON, 1.1), (0.92, 2.7, 5.0, 2.2, GP_MOON, 0.8, 0.5), (1.35, 3.4, 4.6, 2.0, GP_MOON, 0.6),
            (0.92, 1.6, 3.4, 1.6, GP_MOON, 0.35), (-0.45, 1.0, 6.0, 1.4, '#ffbf6a', 0.25)]
    hall_l = [(0.92, 2.2, 1.6, 2.6, GP_LAMP, 0.8), (0.5, 1.4, 2.2, 2.0, GP_LAMP, 0.7)]
    var = [('hall', hall_l, hf)]

    def upper(p_):
        def win_art(q, W, H):
            wx0, wx1 = (0.6 + 1.35) * 100, (1.25 + 1.35) * 100
            wv0 = H - (4.6 - 2.66) * 100; wv1 = H - (3.3 - 2.66) * 100
            q.fill(rect(wx0 - 6, wv1, wx1 - wx0 + 12, 6), '#e8e0d0')
        # landing back wall with the window (the night sky through it), the landing floor, the upstairs ceiling, the
        # dark doorway of the upstairs hall on the left
        wq = hv.quad([(0.6, 4.6, HALL_BACK), (1.25, 4.6, HALL_BACK), (1.25, 3.3, HALL_BACK), (0.6, 3.3, HALL_BACK)])
        b = wq.getBounds()
        p_.linear(rect(b.left(), b.top(), b.width(), b.height()), 0, b.top(), 0, b.bottom(), ['#2a3a70', '#4a5a94', '#1a2244'])
        draw_tree(p_, b.left() + b.width() * 0.35, b.bottom() + b.height() * 0.1, b.height() * 1.1, 0.0, 77, 0.3, '#060812', None, 4)
        _moon(p_, b.left() + b.width() * 0.68, b.top() + b.height() * 0.25, b.width() * 0.12)
        _backing(p_, hv, HALL_BACK, -2.6, 2.8, 1.8, UP_CEIL + 1.5, _darken(HALL_PAPER, 0.4), [(0.6, 1.25, 3.3, 4.6)])
        _hwall(p_, hv, (HALL_X[0], HALL_BACK), (HALL_X[1], HALL_BACK), 2.66, UP_CEIL, HALL_PAPER, HALL_INK, 'damask', 0.0,
               holes=[(0.6 - HALL_X[0], 3.3 - 2.66, 1.25 - HALL_X[0], 4.6 - 2.66, 'arch'), (-0.75 - HALL_X[0], 0.0, 0.1 - HALL_X[0], 2.05)], art=win_art, seed=9)
        dq = hv.quad([(-0.75, 4.71, HALL_BACK + 0.01), (0.1, 4.71, HALL_BACK + 0.01), (0.1, 2.66, HALL_BACK + 0.01), (-0.75, 2.66, HALL_BACK + 0.01)])
        _hfloor(p_, hv, HALL_X[0], HALL_X[1], LANDING_Y, HALL_BACK, 'boards', '#7a5234', '#4a2e1a', Y=2.66)
        _hceil(p_, hv, -2.6, 2.8, 0.3, HALL_BACK, UP_CEIL, '#6a6254')
        for i in range(2):                                                  # window muntins
            xm = 0.6 + 0.65 * (i + 1) / 3
            p_.seg(hv.p(xm, 3.3, HALL_BACK), hv.p(xm, 4.45, HALL_BACK), max(1.5, 0.02 * hv.s(HALL_BACK)), '#e8e0d0')
        p_.seg(hv.p(0.6, 3.95, HALL_BACK), hv.p(1.25, 3.95, HALL_BACK), max(1.5, 0.02 * hv.s(HALL_BACK)), '#e8e0d0')
    ubox = (box[0], box[1], box[2], hv.y(2.0, HALL_BACK))
    L = _lit(hv.d(HALL_BACK), upper, 'st_upper', _key('gp', 'stairs', 'upper'), ubox, hv, amb, moon, var)

    def walls(p_):
        def right_art(q, W, H):
            u = lambda y: (y - 0.22) * 100
            for i in range(5):
                y = 1.3 + i * 0.62; Yc = 1.75 + (y - STAIR_Y0) * STAIR_RISE / STAIR_RUN
                _hframe(q, W, H, u(y), H - (Yc + 0.3) * 100, 24 + 6 * (i % 2), 30, 'photo', seed=10 + i)
        _hwall(p_, hv, (HALL_X[1], 0.22), (HALL_X[1], HALL_BACK), 0.0, UP_CEIL, HALL_PAPER, HALL_INK, 'damask', 0.0, art=right_art, seed=2)
        # the hall beyond the banister: its far end with the kitchen opening (dark), the left wall, the ceiling
        _hwall(p_, hv, (HALL_X[0], HALL_BACK), (STAIR_X[0], HALL_BACK), 0.0, CEIL, HALL_PAPER, HALL_INK, 'damask', 0.95,
               holes=[(KOPEN[0] - HALL_X[0], 0.0, KOPEN[1] - HALL_X[0], KOPEN[2])], rail=2.2, seed=3)
        oq = hv.quad([(KOPEN[0], KOPEN[2], HALL_BACK + 0.01), (KOPEN[1], KOPEN[2], HALL_BACK + 0.01), (KOPEN[1], 0, HALL_BACK + 0.01), (KOPEN[0], 0, HALL_BACK + 0.01)])
        p_.fill(oq, '#3a2a20')
        aq = hv.quad([(HALL_X[0], 2.5, ARCH_Y[0] - 0.1), (HALL_X[0], 2.5, ARCH_Y[1] + 0.1), (HALL_X[0], -0.3, ARCH_Y[1] + 0.1), (HALL_X[0], -0.3, ARCH_Y[0] - 0.1)])
        p_.fill(aq, '#15131c')                                              # the dark living room through the arch
        _hwall(p_, hv, (HALL_X[0], 0.55), (HALL_X[0], HALL_BACK), 0.0, CEIL, HALL_PAPER, HALL_INK, 'damask', 0.95,
               holes=[(ARCH_Y[0] - 0.55, 0.0, ARCH_Y[1] - 0.55, 2.3, 'arch')], rail=2.2, seed=1)
        _hfloor(p_, hv, HALL_X[0], STAIR_X[0], 0.55, HALL_BACK, 'boards', '#7a5234', '#4a2e1a', runner=(-0.95, 0.15, 0.55, 5.85, '#6a1c24', '#c8a050'))
        _hceil(p_, hv, HALL_X[0], STAIR_X[0], 0.55, HALL_BACK, CEIL, '#5a5248')
        p_.fill(hv.quad([(STAIR_X[0], CEIL, 1.3), (STAIR_X[0], CEIL + 0.22, 1.3), (STAIR_X[0], CEIL + 0.22, HALL_BACK), (STAIR_X[0], CEIL, HALL_BACK)]), '#5a4630')
        for y in np.arange(1.45, HALL_BACK, 0.17):
            a_, b_ = hv.p(STAIR_X[0] + 0.02, CEIL + 0.22, y), hv.p(STAIR_X[0] + 0.02, CEIL + 1.1, y)
            p_.seg(a_, b_, max(2.0, 0.024 * hv.s(y)), '#5a3420')
        p_.line(poly([hv.p(STAIR_X[0] + 0.02, CEIL + 1.1, 1.35), hv.p(STAIR_X[0] + 0.02, CEIL + 1.1, HALL_BACK)], False), max(4.0, 0.05 * hv.s(2.0)), '#3a2010')
    L += _lit(3.2, walls, 'st_walls', _key('gp', 'stairs', 'walls'), box, hv, amb, moon, var)
    L += _lit(1.6, lambda p_: _stairs_house(p_, hv), 'st_flight', _key('gp', 'stairs', 'flight'), box, hv, amb, moon, var)
    bf = _beam_fn(beam)
    if beam is not None: L.append(_beam_layers(hv, bf))

    def moonbeam(pen, t):                                       # a shaft of moonlight down the top of the flight
        a_, b_ = hv.p(0.6, 4.6, HALL_BACK), hv.p(1.25, 4.6, HALL_BACK)
        c_, d_ = hv.p(1.3, 2.0, 3.6), hv.p(0.55, 2.0, 3.6)
        sh = poly([a_, b_, c_, d_])
        pen.linear(sh, 0, a_[1], 0, c_[1], [(0, '#9fb4f0', 40), (1, '#9fb4f0', 0)])
    L.append(Layer(hv.d(4.8), moonbeam, 'st_moonbeam', cache=_key('gp', 'stairs', 'mb'), bounds=box, blur=0))
    st = lambda k: hv.anchor(0.92, STAIR_Y0 + (k - 1) * STAIR_RUN + 0.13, k * STAIR_RISE, 'sitting on step %d (the tread top)' % k)
    a = {'step1': st(1), 'step3': st(3), 'step6': st(6), 'landing': hv.anchor(0.92, LANDING_Y + 0.4, 2.66, 'on the landing'),
         'foot': hv.anchor(0.92, 0.75, note='at the foot of the stairs')}
    info = {'view': hv, 'beam': bf, 'hall_light': hf, 'cam_env': dict(x=(860, 1060), y=(440, 640), zoom=(1.0, 1.25), f=(1.0, 1.8))}
    return SetPiece('gp_stairs', L, a, {}, lens='lens', grade='gp_dark', focus=1.3, dof=1.6, cover=FRAME, info=info)


def _gp_hall_door(light=1.0, case='closed', envelope=True, latch=0.0, tod='night', door=0.0):
    """The front hall from inside, facing the front door: the door (oval glass: moonlight, or 8 AM daylight), the stairs
    coming down on the left (their newel post by the door), the hall bench with the case on the right under Grandpa's
    coat and hat, the arch to the living room at the right edge. door 0..1 (or f(t)) swings it open into the hall
    (outside: the porch and the street, morning or night). Anchors: door (just inside it), bench_stand, case, mid,
    stairs_foot."""
    hv = HView(560, 470, 1.5, -0.4, 3.7, -1)
    hf = _kfn(light, 32)
    dfn = door if callable(door) else (lambda t, d=float(door): d)
    box = FRAME
    morning = tod == 'morning'
    amb = '#c8ccd8' if morning else '#262c44'
    moon = ([(-0.4, 1.4, 0.0, 2.6, '#f4f0e6', 0.8), (-0.4, 0.0, 0.9, 2.2, '#f4f0e6', 0.7, 0.35)] if morning else
            [(-0.4, 1.4, 0.05, 1.6, GP_MOON, 0.55), (-0.4, 0.0, 0.8, 1.6, GP_MOON, 0.4, 0.35)])
    hall_l = [(-1.35, 1.6, 2.4, 2.6, GP_LAMP, 0.9), (0.5, 1.2, 2.2, 2.2, GP_LAMP, 0.7), (-0.4, 0.0, 2.4, 2.6, GP_LAMP, 0.85, 0.35),
              (-0.42, CEIL, 2.6, 1.0, GP_LAMP, 0.7), (-0.4, 1.4, 0.0, 2.2, GP_LAMP, 0.45), (-1.1, 0.6, 1.9, 1.5, GP_LAMP, 0.7)]
    var = [('hall', hall_l, hf)] if not morning else []
    DX0, DX1, DH = -0.85, 0.05, 2.1

    def front(p_):
        _backing(p_, hv, 0.0, -2.6, 2.6, -0.9, UP_CEIL + 0.6, _darken(HALL_PAPER, 0.35), [(DX0, DX1, 0.0, DH)])

        def art(q, W, H):
            u0 = (HALL_X[1] - 0.05) * 100; u1 = (HALL_X[1] + 0.85) * 100
            q.fill(rect(u0 - 4, H - (DH + 0.42) * 100, u1 - u0 + 8, 30), '#3a2414')                      # transom frame
            q.fill(rect(u0 + 6, H - (DH + 0.36) * 100, u1 - u0 - 12, 20), '#7a8ac0' if not morning else '#f4f0e0')
            for i in range(1, 4): q.fill(rect(u0 + i * (u1 - u0) / 4 - 1, H - (DH + 0.36) * 100, 2, 20), '#3a2414')
            text(q.cv, '4 1 7', (u0 + u1) / 2, H - (DH + 0.21) * 100, 800, 9, '#3a2414', 230, 0.3)
        _hwall(p_, hv, (HALL_X[1], 0.0), (HALL_X[0], 0.0), 0.0, CEIL, HALL_PAPER, HALL_INK, 'damask', 0.95,
               holes=[(HALL_X[1] - DX1, 0.0, HALL_X[1] - DX0, DH, None, 'nocase')], art=art, rail=2.2, seed=6)
        # what the door opens onto: porch boards, the street
        oq = hv.quad([(DX0, DH, -0.02), (DX1, DH, -0.02), (DX1, 0, -0.02), (DX0, 0, -0.02)])
        b = oq.getBounds()
        p_.cv.save(); p_.cv.clipPath(oq, skia.ClipOp.kIntersect, True)
        if morning:
            p_.linear(oq, 0, b.top(), 0, b.bottom(), ['#b8c8dc', '#dfe4e8', '#c8c8c0'])
        else:
            p_.linear(oq, 0, b.top(), 0, b.bottom(), ['#0e1630', '#1c2448', '#0a0c14'])
        hz_ = b.top() + b.height() * 0.62
        for i, hx_ in enumerate((-0.2, 0.35, 0.8)):                     # houses across the street
            x_ = b.left() + b.width() * hx_; w_ = b.width() * 0.42
            p_.fill(rect(x_, hz_ - b.height() * 0.16, w_, b.height() * 0.16), ('#8a8a90', '#9a8a7a', '#7a8a8a')[i] if morning else '#0c1020')
            p_.fill(poly([(x_ - w_ * 0.05, hz_ - b.height() * 0.16), (x_ + w_ / 2, hz_ - b.height() * 0.26), (x_ + w_ * 1.05, hz_ - b.height() * 0.16)]),
                    '#5a4a48' if morning else '#080a14')
        draw_tree(p_, b.left() + b.width() * 0.15, hz_, b.height() * 0.55, 0.0, 61, 0.3, '#6a6a5a' if morning else '#04060c', None, 4)
        p_.fill(rect(b.left(), hz_, b.width(), b.height() * 0.1), '#8a8a88' if morning else '#10121a')
        p_.fill(rect(b.left(), hz_ + b.height() * 0.1, b.width(), b.height() * 0.3), '#7a6a58' if morning else '#120e0c')
        p_.cv.restore()
        # the casing
        cs = hv.quad([(DX0 - 0.09, DH + 0.09, 0.0), (DX1 + 0.09, DH + 0.09, 0.0), (DX1 + 0.09, 0, 0.0), (DX0 - 0.09, 0, 0.0)])
        p_.line(cs, max(3.0, 0.06 * hv.s(0.0)), '#3a2414')
    fbox = (hv.x(2.6, 0.0), hv.y(UP_CEIL + 0.6, 0.0), hv.x(-2.6, 0.0), hv.y(-0.9, 0.0))
    L = _lit(hv.d(0.0), front, 'hd_front', _key('gp', 'hdoor', 'front', tod), fbox, hv, amb, moon, var)

    def leaf(pen, t):                                                     # the door: hinged on the stairs side (x = DX1)
        o = clamp(dfn(t)); ang = math.radians(95.0) * o
        xf = DX1 - 0.9 * math.cos(ang); yf = 0.0 + 0.9 * math.sin(ang)
        q = [(DX1, DH, 0.0), (xf, DH, yf), (xf, 0.0, yf), (DX1, 0.0, 0.0)]
        if o < 0.01: q = [(DX1, DH, 0.0), (DX0, DH, 0.0), (DX0, 0.0, 0.0), (DX1, 0.0, 0.0)]

        def art(p_):
            p_.fill(rect(0, 0, 90, 210), '#4a2414'); p_.texture(rect(0, 0, 90, 210), 'wood', 0.6, 'overlay', 0.8, 90)
            p_.line(rect(14, 120, 62, 76), 2.0, '#1a0a04', 170)
            gl = oval(45, 58, 24, 36)
            p_.fill(gl, '#8ea0d8' if not morning else '#f4f0e4'); p_.texture(gl, 'grunge', 0.35, 'overlay', 0.5)
            for k in range(5): p_.line(oval(45, 58, 24 - k * 4.5, 36 - k * 6.5), 0.8, '#ffffff', 60)
            p_.line(gl, 3.0, '#2a1408')
            p_.fill(oval(8 if o < 0.01 else 82, 110, 3.5), '#c9a24a')
        _hface(pen, hv, *q, 90, 210, art)
        pen.line(hv.quad(q), 1.5, LINE, 220)
        if o > 0.01:                                                      # light through the open door across the floor
            c = '#fff4dc' if morning else '#8fa4e0'
            a_, b_ = hv.p(DX0, 0.0, 0.0), hv.p(DX1, 0.0, 0.0)
            c_, d_ = hv.p(DX1 + 0.3, 0.0, 2.2), hv.p(DX0 - 0.3, 0.0, 2.2)
            pen.linear(poly([a_, b_, c_, d_]), 0, a_[1], 0, c_[1], [(0, c, 110 * o), (1, c, 0)])
    L.append(Layer(2.95, leaf, 'hd_door', blur=None, ref_depth=hv.d(0.3)))

    def walls(p_):
        _hwall(p_, hv, (HALL_X[0], 0.0), (HALL_X[0], 4.0), 0.0, CEIL, HALL_PAPER, HALL_INK, 'damask', 0.95,
               holes=[(ARCH_Y[0], 0.0, ARCH_Y[1], 2.3, 'arch')], rail=2.2, seed=1)
        def right_art(q, W, H):
            for i in range(3):
                y = 1.3 + i * 0.62; Yc = 1.75 + (y - STAIR_Y0) * STAIR_RISE / STAIR_RUN
                _hframe(q, W, H, y * 100, H - (Yc + 0.3) * 100, 24 + 6 * (i % 2), 30, 'photo', seed=10 + i)
        _hwall(p_, hv, (HALL_X[1], 0.0), (HALL_X[1], 4.0), 0.0, UP_CEIL, HALL_PAPER, HALL_INK, 'damask', 0.0, art=right_art, seed=2)
        _hfloor(p_, hv, HALL_X[0], HALL_X[1], 0.0, 4.0, 'boards', '#7a5234', '#4a2e1a', runner=(-0.95, 0.15, 0.55, 4.0, '#6a1c24', '#c8a050'))
        _hceil(p_, hv, HALL_X[0], STAIR_X[0], 0.0, 4.0, CEIL, '#9a8e78')
        _hceil(p_, hv, STAIR_X[0], HALL_X[1], 0.0, 1.3, CEIL, '#9a8e78')
        fx, fy = hv.p(-0.42, CEIL, 2.6); fs = hv.s(2.6)
        p_.fill(oval(fx, fy + 0.02 * fs, 0.12 * fs, 0.03 * fs), '#8a7a5a')
    L += _lit(3.0, walls, 'hd_walls', _key('gp', 'hdoor', 'walls', tod), box, hv, amb, moon, var)

    def stairs(p_):                                                       # the flight coming down toward the door
        xa, xb = STAIR_X
        side = [(xa, 0, STAIR_Y0)]
        for k in range(STAIR_N):
            yk = STAIR_Y0 + k * STAIR_RUN
            side += [(xa, (k + 1) * STAIR_RISE, yk), (xa, (k + 1) * STAIR_RISE, yk + STAIR_RUN)]
        ycut = hv.hy - 0.2
        side = [q for q in side if q[2] <= ycut]
        side += [(xa, 0.95 + STAIR_RISE + (ycut - STAIR_Y0) * STAIR_RISE / STAIR_RUN - 0.95 - 0.0, ycut), (xa, 0, ycut)]
        sp_ = side
        for k in range(STAIR_N):                                          # far (by the door) -> near
            yk = STAIR_Y0 + k * STAIR_RUN; Y0, Y1 = k * STAIR_RISE, (k + 1) * STAIR_RISE
            if hv.d(yk + STAIR_RUN) < 0.15: continue
            p_.fill(hv.quad([(xa, Y0, yk), (xb, Y0, yk), (xb, Y1, yk), (xa, Y1, yk)]), '#3a2416')
            if Y1 < hv.cam_h:
                p_.fill(hv.quad([(xa, Y1, yk), (xb, Y1, yk), (xb, Y1, yk + STAIR_RUN), (xa, Y1, yk + STAIR_RUN)]), '#6a4228')
                p_.fill(hv.quad([(xa + 0.15, Y1, yk), (xb - 0.12, Y1, yk), (xb - 0.12, Y1, yk + STAIR_RUN), (xa + 0.15, Y1, yk + STAIR_RUN)]), '#6a1e24')
                p_.line(poly([hv.p(xa, Y1, yk), hv.p(xb, Y1, yk)], False), max(1.2, 0.01 * hv.s(yk)), '#a8804a', 220)
        if len(sp_) > 2:
            panel = hv.quad(sp_); p_.fill(panel, '#8a7a62'); p_.texture(panel, 'plaster', 0.3, 'overlay', 0.8); p_.line(panel, 2, LINE, 200)
        def Yh(y): return 0.95 + STAIR_RISE + (y - STAIR_Y0) * STAIR_RISE / STAIR_RUN
        for k in range(STAIR_N):
            y = STAIR_Y0 + k * STAIR_RUN + STAIR_RUN * 0.5
            if hv.d(y) < 0.25: continue
            a_, b_ = hv.p(xa + 0.05, (k + 1) * STAIR_RISE, y), hv.p(xa + 0.05, Yh(y), y)
            w = max(2.0, 0.024 * hv.s(y)); p_.seg(a_, b_, w + 2, LINE, 200); p_.seg(a_, b_, w, '#5a3420')
        ys = [y for y in np.linspace(STAIR_Y0 - 0.05, LANDING_Y, 12) if hv.d(y) > 0.25]
        if len(ys) > 1:
            rail = [hv.p(xa + 0.05, Yh(y), y) for y in ys]
            p_.line(poly(rail, False), max(5.0, 0.055 * hv.s(2.0)), LINE); p_.line(poly(rail, False), max(3.5, 0.042 * hv.s(2.0)), '#4a2a16')
        nx, ny = hv.p(xa + 0.05, 0, STAIR_Y0 - 0.05); s0 = hv.s(STAIR_Y0 - 0.05)
        p_.shape(rect(nx - 0.06 * s0, ny - 1.15 * s0, 0.12 * s0, 1.15 * s0), '#4a2a16', 3)
        p_.shape(oval(nx, ny - 1.26 * s0, 0.07 * s0), '#5a3420', 3)
    L += _lit(2.6, stairs, 'hd_stairs', _key('gp', 'hdoor', 'stairs', tod), box, hv, amb, moon, var)

    def bench(p_):
        _bench_art(p_, hv); _case3d(p_, hv, case, envelope, latch)
    L += _lit(hv.d(1.9), bench, 'hd_bench', _key('gp', 'hdoor', 'bench', case, envelope, round(latch, 2), tod), box, hv, amb, moon, var)

    def fixture(pen, t):
        k = hf(t) if not morning else 0.0
        fx, fy = hv.p(-0.42, CEIL, 2.6); s = hv.s(2.6)
        bowl = smooth([(fx - 0.16 * s, fy + 0.02 * s), (fx - 0.12 * s, fy + 0.09 * s), (fx, fy + 0.12 * s), (fx + 0.12 * s, fy + 0.09 * s), (fx + 0.16 * s, fy + 0.02 * s)], True, 0.6)
        pen.fill(bowl, mix('#2e2c2a' if not morning else '#b8b0a0', '#fff6e0', k)); pen.line(bowl, 1.5, LINE, 200)
        if k > 0.02: pen.glow(fx, fy + 0.07 * s, 0.6 * s, '#ffe2b0', 120 * k)
    L.append(Layer(hv.d(2.6), fixture, 'hd_fixture', blur=None))
    a = {'door': hv.anchor(-0.4, 0.45, note='just inside the front door'), 'outside': hv.anchor(-0.4, -0.5, note='on the porch, in the doorway'),
         'mid': hv.anchor(-0.45, 2.6), 'bench_stand': hv.anchor(-0.7, 1.9, note='at the bench'),
         'case': hv.anchor((CASE[0] + CASE[1]) / 2, (CASE[2] + CASE[3]) / 2, CASE[4] + CASE[5], 'top of the case'),
         'stairs_foot': hv.anchor(0.9, 0.6), 'stairs_low': hv.anchor(0.92, STAIR_Y0 + 2 * STAIR_RUN + 0.13, 3 * STAIR_RISE)}
    info = {'view': hv, 'hall_light': hf, 'door': dfn, 'cam_env': dict(x=(820, 1100), y=(460, 620), zoom=(1.0, 1.25), f=(1.0, 2.0))}
    return SetPiece('gp_hall_door', L, a, {'enter': [a['outside'], a['door'], a['mid']]}, lens='lens',
                    grade='morning' if morning else 'gp_house', focus=2.0, dof=1.5, cover=FRAME, info=info)


def gp_kitchen(view='table', kitchen=1.0, mug=True, steam=1.0, chair=True, tod='night', sway=0.0):
    """Grandpa's kitchen (the same kitchen the hall and the couch look into): mint cabinets, cream teapot wallpaper,
    black-and-cream checker floor, the red kettle, the amber glass pendant over the yellow formica table, Grandpa's
    dark captain's chair with the red cushion at the far side facing you, the mug of coffee (still steaming) with the
    spoon in it and the sugar bowl, the cafe curtains, the window behind the chair. view:
      'table'  from the kitchen opening (standing): the whole table, the chair, the window
      'chair'  seated eye height, close across the table: the chair fills the middle, the mug in front (the glove lifts
               off the table here; push in on the face)
    kitchen = the pendant level spec (flickers: dict(flick=...)); sway = pendant sway amplitude (m) or f(t) -> offset.
    tod 'morning': the same kitchen in grey daylight (the last scenes: the new Owen drinks his coffee).
    Anchors: chair (seated, seat height), chair_stand (standing on the seat), table (his glove on the table), mug,
    beside (standing at the table's near-left corner: Mom picking up the mug)."""
    if view == 'chair':
        hv = HView(1050, 600, 1.12, GCHAIR[0], GCHAIR[1] - 1.95, 1)
    else:
        hv = HView(820, 520, 1.55, GCHAIR[0] + 0.1, HALL_BACK + 0.25, 1)
    kf = _kfn(kitchen, 41)
    swf = sway if callable(sway) else (lambda t, a=float(sway): a * math.sin(t * 1.3) if a else 0.0)
    box = FRAME
    L = _kitchen_layers(hv, 'kit_' + view, kf, box, tod, mug, steam, chair, swf)
    a = {'chair': hv.anchor(GCHAIR[0], GCHAIR[1], 0.47, 'seated in Grandpa\'s chair (seat height)'),
         'chair_stand': hv.anchor(GCHAIR[0], GCHAIR[1], 0.5, 'standing on the seat'),
         'table': hv.anchor(GCHAIR[0], GCHAIR[1] - 0.3, TABLE[4], 'his glove on the table'),
         'mug': hv.anchor(GCHAIR[0] + 0.02, GCHAIR[1] - 0.42, TABLE[4], 'the mug (rim ~0.1 m above)'),
         'beside': hv.anchor(TABLE[0] - 0.15, TABLE[2] + 0.1, note='standing at the near-left corner of the table'),
         'near': hv.anchor(GCHAIR[0] + 0.5, TABLE[2] - 0.4, note='standing on the near side of the table')}
    grade = 'morning' if tod == 'morning' else 'gp_house'
    info = {'view': hv, 'kitchen': kf, 'cam_env': dict(x=(820, 1100), y=(440, 640), zoom=(1.0, 1.3), f=(1.0, 2.6))}
    return SetPiece('gp_kitchen', L, a, {}, lens='lens', grade=grade, focus=hv.d(GCHAIR[1]), dof=1.6 if view == 'chair' else 1.0,
                    cover=FRAME, info=info)


# ---------------------------------------------------------------------------------------------- the living room
LIV_PAPER, LIV_INK = '#a08a48', '#7a6430'
BOOK_H = 1.85                                         # the bookcase's top (room for him to sit up there)
TVBOX = (-5.12, -4.48, 0.62, 1.16, 5.5, 5.96)          # x0, x1, Y0, Y1, y0, y1 of the CRT set on the cabinet
TVSCR = (-5.06, -4.66, 0.7, 1.06)                    # the picture tube's face on the TV front (x0, x1, Y0, Y1)
LAMP_POS = (-2.38, 2.05, 1.52)                       # the floor lamp beside the couch (x, y, shade bottom Y)


def _tv_spec(tv):
    """tv spec -> f(t) -> (mode, level): mode 'off' | 'snow' | 'blue' | 'tape'; level 0..1 = the screen's brightness.
    tv = None / 'off' | a mode string | dict(on=t (switches itself on), snow=0.6 (seconds of static first), blue=0.0
    (seconds of the VCR's blue screen), mode='tape', off=t, k=1.0, pulse=f(t) -> 0..1 (the picture's brightness:
    the laughter waves)) | f(t) -> (mode, level)."""
    if tv is None or tv == 'off': return lambda t: ('off', 0.0)
    if callable(tv): return tv
    if isinstance(tv, str): return lambda t, m=tv: (m, 1.0)
    on = tv.get('on', -1e9); sn = tv.get('snow', 0.6); bl = tv.get('blue', 0.0); off = tv.get('off', 1e9)
    k = tv.get('k', 1.0); pulse = tv.get('pulse'); mode = tv.get('mode', 'tape')

    def f(t):
        if t < on or t >= off: return ('off', 0.0)
        u = t - on
        if u < 0.08: return ('snow', k * u / 0.08)
        if u < sn: return ('snow', k)
        if u < sn + bl: return ('blue', k)
        return (mode, k * (pulse(t) if pulse else 1.0))
    return f


def _crt_face(pen, W, H, t, mode, lvl, content=None, seed=0):
    """What is on the picture tube (a W x H frame, 4:3): 'off' (dark curved glass with the room's reflection), 'snow'
    (static), 'blue' (the VCR's blue screen with PLAY), 'tape' (content(pen, W, H, t): the 1974 show) with scanlines,
    a rolling bar, a soft glow and the glass curvature shading."""
    cv = pen.cv
    tube = rrect(0, 0, W, H, min(W, H) * 0.09)
    cv.save(); cv.clipPath(tube, skia.ClipOp.kIntersect, True)
    if mode == 'off' or lvl <= 0.01:
        pen.fill(tube, '#1a201e')
        pen.radial(tube, W * 0.4, H * 0.35, W * 0.8, [(0, '#3a4440', 255), (1, '#0e1210', 255)])
    elif mode == 'snow':
        pen.fill(tube, '#7a7e80')
        pen.texture(tube, 'noise', 0.95, 'overlay', 0.08 * W / 46.0, 0.0, (t * 9731) % 512, (t * 6151) % 512)
        pen.texture(tube, 'noise', 0.7, 'overlay', 0.13 * W / 46.0, 90.0, (t * 3313) % 512, (t * 1777) % 512)
        for i in range(3):
            yy = ((t * 1.7 + i * 0.37) % 1.0) * H
            pen.fill(rect(0, yy, W, H * 0.04), '#ffffff', 60)
    elif mode == 'blue':
        pen.fill(tube, '#1a3ad0')
        text(cv, 'PLAY  ▶', W * 0.08, H * 0.16, 800, H * 0.09, '#e8f0ff', 255, 0.08, 'left')
    else:
        pen.fill(tube, '#20140c')
        if content is not None: content(pen, W, H, t)
        # VHS on a CRT: a slow rolling bar, scanlines, a little snow
        yb = ((t * 0.09 + 0.3) % 1.25 - 0.12) * H
        pen.linear(rect(0, yb - H * 0.06, W, H * 0.12), 0, yb - H * 0.06, 0, yb + H * 0.06, [(0, '#ffffff', 0), (0.5, '#ffffff', 40), (1, '#ffffff', 0)])
        pen.texture(tube, 'noise', 0.22, 'overlay', 0.06 * W / 46.0, 0.0, (t * 9731) % 512, (t * 6151) % 512)
    if mode != 'off' and lvl > 0.01:
        n = int(H / max(0.6, H / 120.0))
        for i in range(0, n, 2):
            pen.fill(rect(0, i * H / n, W, H / n * 0.5), '#000000', 70)
        pen.fill(tube, '#000000', 255 * (1 - clamp(lvl)))
    pen.radial(tube, W / 2, H / 2, W * 0.72, [(0, '#000000', 0), (0.7, '#000000', 40), (1, '#000000', 170)])     # tube falloff
    pen.fill(poly([(W * 0.06, H * 0.08), (W * 0.42, H * 0.04), (W * 0.2, H * 0.36), (W * 0.04, H * 0.5)]), '#ffffff', 26)  # glass sheen
    cv.restore()
    pen.line(tube, max(0.6, W * 0.012), '#000000', 230)


def _tv_cabinet_art(pen, hv):
    """The walnut TV cabinet (an open shelf with the VCR, a stack of tapes), the CRT on top with its wood-grain
    shell, the dial knobs, the rabbit-ears antenna. Static; the tube's face is drawn live (_crt_face)."""
    _hbox(pen, hv, -5.3, -4.3, 0.0, 0.62, 5.46, 6.0, '#5a3820', top='#6a4228', tex='wood',
          faces={'front': lambda p_, W, H: _cab_front(p_, W, H)})
    x0, x1, Y0, Y1, y0, y1 = TVBOX
    def tv_front(p_, W, H):
        p_.fill(rect(0, 0, W, H), '#4a3020'); p_.texture(rect(0, 0, W, H), 'wood', 0.6, 'overlay', 0.8, 0)
        p_.fill(rrect(3, 3, (TVSCR[1] - x0) * 100 + 3, H - 6, 4), '#1a1614')
        kx = (TVSCR[1] - x0) * 100 + 10
        p_.fill(rect(kx - 2, 4, W - kx - 2, H - 8), '#2a2420')
        for j, yy in enumerate((12, 24)):
            p_.fill(oval(kx + 5, yy, 3.6), '#c8c0b0'); p_.line(oval(kx + 5, yy, 3.6), 0.6, LINE)
            p_.seg((kx + 5, yy), (kx + 5 + 2.6 * math.cos(j * 2.0), yy + 2.6 * math.sin(j * 2.0)), 0.6, '#2a2420')
        for i in range(5): p_.fill(rect(kx + 1, 34 + i * 2.6, 8, 1.0), '#5a5248')
        text(p_.cv, 'ZENITH', kx + 5, H - 6, 800, 2.2, '#c9a24a', 230, 0.1)
    _hbox(pen, hv, x0, x1, Y0, Y1, y0, y1, '#4a3020', top='#5a3a24', tex='wood', faces={'front': tv_front})
    ax, ay = hv.p((x0 + x1) / 2, Y1, (y0 + y1) / 2); s = hv.s((y0 + y1) / 2)
    pen.fill(oval(ax, ay, 0.05 * s, 0.02 * s), '#1a1a1a')
    for sgn in (-1, 1):
        pen.line(poly([(ax, ay), (ax + sgn * 0.28 * s, ay - 0.42 * s)], False), max(1.0, 0.006 * s), '#b8bcc4')
        pen.fill(oval(ax + sgn * 0.28 * s, ay - 0.42 * s, 0.01 * s), '#d8dce4')


def _cab_front(p_, W, H):
    """The cabinet face: two doors below, the open shelf above with the VCR and a stack of tapes."""
    p_.fill(rect(4, 4, W - 8, H * 0.42), '#140c06')
    vx, vy, vw, vh = 8, 7, W * 0.55, H * 0.2
    p_.fill(rect(vx, vy, vw, vh), '#2a2a2e'); p_.fill(rect(vx, vy, vw, 2), '#5a5a62')
    p_.fill(rect(vx + 3, vy + vh * 0.35, vw * 0.45, vh * 0.28), '#0a0a0c')                       # the tape slot
    p_.fill(rect(vx + vw * 0.62, vy + vh * 0.3, vw * 0.3, vh * 0.4), '#061008')                  # the clock window
    for i in range(4): p_.fill(rect(vx + vw * 0.08 + i * 4, vy + vh * 0.78, 3, 1.4), '#8a8a92')
    for i in range(4):
        p_.fill(rect(vx + vw + 6 + i * 5.5, vy + 2 + i * 0.5, 4.5, vh + 3 - i * 0.5), ('#2a2a30', '#1a2a4a', '#2a2a30', '#4a1a1a')[i])
        p_.fill(rect(vx + vw + 6.6 + i * 5.5, vy + 6, 3.3, 6), '#e8e0d0', 200)
    for i in range(2):
        r = rect(6 + i * (W - 12) / 2, H * 0.5, (W - 12) / 2 - 3, H * 0.44)
        p_.line(r, 1.4, '#000000', 140); p_.fill(oval(i * (W - 12) / 2 + (W - 12) / 2 - 6 + (6 if i == 0 else -((W - 12) / 2 - 12)), H * 0.72, 1.6), '#c9a24a')


def _vcr_clock(pen, hv, t, blink=True):
    """The VCR's green clock (blinking 12:00) on the cabinet shelf (live)."""
    W = 100.0; x0 = -5.3 + (8 + 100 * 0.55 * 0.62) / 100.0
    q0 = (x0 + 0.01, 0.62 - 0.07 - 0.2 * 0.62 * 0.3, 5.459)
    px, py = hv.p(-5.3 + (8 + 55 * 0.62 + 55 * 0.15) / 100.0, 0.62 - (7 + 12.4 * 0.5) / 100.0, 5.455)
    s = hv.s(5.455)
    on = (not blink) or (t % 1.0) < 0.55
    if on:
        text(pen.cv, '12:00', px, py + 0.012 * s, 800, 0.028 * s, '#5aff8a', 230, 0.05)
        pen.glow(px, py, 0.04 * s, '#3aff6a', 60)


def _coffee_table(p_, hv):
    """The low walnut coffee table (y 3.3..3.9) with a candy dish, TV Guide magazines and a glass ashtray."""
    x0, x1, y0, y1 = -4.25, -3.15, 3.3, 3.9
    for (lx, ly) in ((x0 + 0.05, y0 + 0.05), (x1 - 0.05, y0 + 0.05), (x0 + 0.05, y1 - 0.05), (x1 - 0.05, y1 - 0.05)):
        p_.seg(hv.p(lx, 0, ly), hv.p(lx, 0.36, ly), max(2.0, 0.03 * hv.s(ly)), '#2a1408')
    _hbox(p_, hv, x0, x1, 0.36, 0.42, y0, y1, '#5a3820', top='#7a4e2c', tex='wood')
    cx, cy = hv.p(-3.95, 0.42, 3.6); s = hv.s(3.6)
    p_.fill(oval(cx, cy, 0.11 * s, 0.035 * s), '#c8a838'); p_.fill(oval(cx, cy - 0.01 * s, 0.08 * s, 0.022 * s), '#e85a3a')
    for i, c in enumerate(('#d8c8a8', '#8ab0c8')):
        mq = hv.quad([(-3.6 + i * 0.03, 0.425 + i * 0.006, 3.45 + i * 0.02), (-3.32 + i * 0.03, 0.425 + i * 0.006, 3.45 + i * 0.02),
                      (-3.32 + i * 0.03, 0.425 + i * 0.006, 3.75 + i * 0.02), (-3.6 + i * 0.03, 0.425 + i * 0.006, 3.75 + i * 0.02)])
        p_.fill(mq, c); p_.line(mq, 1.0, LINE, 180)


def _couch_art(pen, hv, side='front'):
    """The rust velour 70s couch (seat cushions, rolled arms, tufted back) facing +y. Works from both views."""
    x0, x1, y0, y1 = COUCH
    c, cd = '#a4482a', '#6a2a18'
    Ys = 0.44
    yb, yf = y0, y1                                           # back at the front-window side, the seat front facing the TV
    if hv.f > 0:                                              # seen from behind (from the TV it's the front)
        pass
    # base / skirt
    _hbox(pen, hv, x0 + 0.05, x1 - 0.05, 0.0, Ys - 0.08, yb + 0.05, yf - 0.02, cd, tex='fabric')
    # back rest
    _hbox(pen, hv, x0 + 0.08, x1 - 0.08, Ys - 0.1, 0.92, yb, yb + 0.25, c, top=_lighten(c, 0.08), tex='fabric',
          faces={'front': lambda p_, W, H: [p_.line(rrect(4 + i * (W - 8) / 3, 4, (W - 8) / 3 - 3, H - 10, 6), 1.4, '#3a1208', 160) for i in range(3)]})
    # seat cushions (three)
    w3 = (x1 - x0 - 0.36) / 3
    for i in range(3):
        cx0 = x0 + 0.18 + i * w3
        _hbox(pen, hv, cx0 + 0.005, cx0 + w3 - 0.005, Ys - 0.08, Ys + 0.04, yb + 0.25, yf, c, top=_lighten(c, 0.1), tex='fabric')
    # arms
    for ax0 in (x0, x1 - 0.18):
        _hbox(pen, hv, ax0, ax0 + 0.18, 0.0, 0.66, yb, yf, c, top=_lighten(c, 0.12), tex='fabric')


def _floor_lamp_art(pen, hv, part='stand'):
    """The brass floor lamp with a pleated cream drum shade beside the couch (stand static; the shade is emissive)."""
    x, y, Yb = LAMP_POS
    a_, b_ = hv.p(x, 0.0, y), hv.p(x, Yb + 0.05, y)
    s = hv.s(y)
    pen.fill(oval(a_[0], a_[1], 0.16 * s, 0.04 * s), '#8a6a2a'); pen.line(oval(a_[0], a_[1], 0.16 * s, 0.04 * s), 1.2, LINE, 200)
    pen.seg(a_, b_, max(2.5, 0.022 * s) + 2, LINE, 220); pen.seg(a_, b_, max(2.0, 0.022 * s), '#b8903a')
    pen.seg((a_[0] - 0.006 * s, a_[1]), (b_[0] - 0.006 * s, b_[1]), max(0.8, 0.006 * s), '#f0d890', 150)


def _bookcase_art(pen, hv):
    """The tall dark bookcase on the front wall (books, framed photos, a little trophy, Grandpa's photo with the
    dummy). Its top (Y 2.3) is where Mister Winks sits at rule 5 (anchor 'bookcase_top')."""
    x0, x1 = BOOK_X
    y0, y1 = 0.0, 0.36

    def front(p_, W, H):
        p_.fill(rect(0, 0, W, H), '#2a160c')
        sh = [H - 8 - i * (H - 16) / 5 for i in range(6)]       # five shelves
        rng = np.random.default_rng(12)
        for i in range(5):
            top_, bot = sh[i + 1] + 3, sh[i] - 1
            p_.fill(rect(4, top_, W - 8, bot - top_), '#120804')
            x = 6.0
            if i == 3:                                                  # the framed photo of Grandpa with the dummy
                _hframe(p_, W, H, 8, bot - 26, 20, 24, 'photo', seed=3); x = 32
            if i == 1:                                                  # a small gold trophy
                p_.fill(rect(W - 18, bot - 4, 10, 4), '#5a4a20'); p_.fill(poly([(W - 17, bot - 4), (W - 9, bot - 4), (W - 11, bot - 14), (W - 15, bot - 14)]), '#c9a24a')
                p_.fill(oval(W - 13, bot - 16, 4, 2.5), '#e8c860')
            while x < W - (22 if i == 1 else 6):
                bw = rng.uniform(2.5, 5.0); bh = (bot - top_) * rng.uniform(0.62, 0.95)
                c_ = ('#6a1a1a', '#1a3a5a', '#3a5a2a', '#8a6a2a', '#4a2a4a', '#b8a888', '#2a2a2a')[int(rng.integers(0, 7))]
                lean = rng.uniform(0, 1) < 0.08
                p_.fill(rect(x, bot - bh, bw, bh), c_); p_.fill(rect(x, bot - bh + bh * 0.15, bw, 0.8), '#e8d8a0', 140)
                x += bw + 0.4
        for y_ in sh: p_.fill(rect(0, y_ - 2, W, 4), '#4a2a16')
        p_.fill(rect(0, 0, 4, H), '#4a2a16'); p_.fill(rect(W - 4, 0, 4, H), '#4a2a16'); p_.fill(rect(0, 0, W, 6), '#4a2a16')
    _hbox(pen, hv, x0, x1, 0.0, BOOK_H, y0, y1, '#3a2010', top='#4a2a16', tex='wood', faces={'front': front})


def _living_shell(pen, hv, part='back'):
    """Walls, floor and ceiling of the living room (house coords). part 'back' = back wall (TV wall with the doorway to
    the kitchen), 'front' = front wall (window + drapes), plus the side walls and the floor / ceiling the view sees."""
    xa, xb = LIV_X
    yn = hv.hy + 0.3 * hv.f
    if hv.f > 0:
        # back wall (y 6.0) seen from the couch: the doorway to the kitchen (the kitchen layers show through)
        def art(q, W, H):
            _hframe(q, W, H, (-3.55 - xa) * 100, H - 200, 64, 46, 'landscape')
            _hframe(q, W, H, (-4.0 - xa) * 100, H - 170, 22, 28, 'photo', seed=21)
        _hwall(pen, hv, (xa, HALL_BACK), (xb, HALL_BACK), 0.0, CEIL, LIV_PAPER, LIV_INK, 'trellis', 0.9,
               holes=[(LDOOR[0] - xa, 0.0, LDOOR[1] - xa, LDOOR[2])], art=art, rail=2.25, seed=11, wc='#4a2e1a')
        for jx, jf in ((LDOOR[0], 1), (LDOOR[1], -1)):
            if (hv.hx - jx) * jf > 0:
                jq = hv.quad([(jx, LDOOR[2], HALL_BACK), (jx, LDOOR[2], HALL_BACK + 0.16), (jx, 0.0, HALL_BACK + 0.16), (jx, 0.0, HALL_BACK)])
                pen.fill(jq, '#5a3820'); pen.line(jq, 1.2, LINE, 200)
        _hwall(pen, hv, (xb, yn), (xb, HALL_BACK), 0.0, CEIL, LIV_PAPER, LIV_INK, 'trellis', 0.9,
               holes=[(ARCH_Y[0] - yn, 0.0, ARCH_Y[1] - yn, 2.3, 'arch')], rail=2.25, seed=12, wc='#4a2e1a')
        aq = hv.quad([(xb, 2.3, ARCH_Y[0]), (xb, 2.3, ARCH_Y[1]), (xb, 0, ARCH_Y[1]), (xb, 0, ARCH_Y[0])])
        def lart(q, W, H):
            _hframe(q, W, H, (3.2 - yn) * 100, H - 190, 40, 52, 'poster', fn=lambda p2, w, h: _poster_art(p2, w, h, 'live'))
        _hwall(pen, hv, (xa, yn), (xa, HALL_BACK), 0.0, CEIL, LIV_PAPER, LIV_INK, 'trellis', 0.9, art=lart, rail=2.25, seed=13, wc='#4a2e1a')
        _hfloor(pen, hv, xa, xb, yn, HALL_BACK, 'carpet', '#5a5a36')
        _hceil(pen, hv, xa, xb, yn, HALL_BACK, CEIL, '#8a8070')
    else:
        # front wall (y 0) seen from the TV end: the window with drapes, the street at night beyond
        def art(q, W, H):
            _hframe(q, W, H, (xb * -1 + 1.35 - 0.0) * 0 + 30, H - 190, 30, 38, 'photo', seed=31)
        _hwall(pen, hv, (xb, 0.0), (xa, 0.0), 0.0, CEIL, LIV_PAPER, LIV_INK, 'trellis', 0.9,
               holes=[(xb - LWIN[1], 0.85, xb - LWIN[0], 2.1)], art=art, rail=2.25, seed=14, wc='#4a2e1a')
        _hwall(pen, hv, (xa, yn), (xa, 0.0), 0.0, CEIL, LIV_PAPER, LIV_INK, 'trellis', 0.9, rail=2.25, seed=15, wc='#4a2e1a')
        _hwall(pen, hv, (xb, 0.0), (xb, yn), 0.0, CEIL, LIV_PAPER, LIV_INK, 'trellis', 0.9,
               holes=[(ARCH_Y[0], 0.0, ARCH_Y[1], 2.3, 'arch')], rail=2.25, seed=16, wc='#4a2e1a')
        _hfloor(pen, hv, xa, xb, 0.0, yn, 'carpet', '#5a5a36')
        _hceil(pen, hv, xa, xb, 0.0, yn, CEIL, '#8a8070')


def _window_night(pen, hv, tod='night', t=0.0):
    """The street through the living-room window (behind the drapes)."""
    q = hv.quad([(LWIN[0], 2.1, -0.02), (LWIN[1], 2.1, -0.02), (LWIN[1], 0.85, -0.02), (LWIN[0], 0.85, -0.02)])
    b = q.getBounds()
    pen.cv.save(); pen.cv.clipPath(q, skia.ClipOp.kIntersect, True)
    if tod == 'morning':
        pen.linear(q, 0, b.top(), 0, b.bottom(), ['#b8c8dc', '#e0e4e6'])
    else:
        pen.linear(q, 0, b.top(), 0, b.bottom(), ['#0c1430', '#1a2448'])
    hz = b.top() + b.height() * 0.66
    for i in range(3):
        x_ = b.left() + b.width() * (0.05 + 0.33 * i); w_ = b.width() * 0.26
        pen.fill(rect(x_, hz - b.height() * 0.2, w_, b.height() * 0.2), '#8a8478' if tod == 'morning' else '#0c1020')
        pen.fill(poly([(x_ - w_ * 0.05, hz - b.height() * 0.2), (x_ + w_ / 2, hz - b.height() * 0.32), (x_ + w_ * 1.05, hz - b.height() * 0.2)]),
                 '#5a4a48' if tod == 'morning' else '#080a14')
        if tod != 'morning' and i == 1: pen.fill(rect(x_ + w_ * 0.4, hz - b.height() * 0.13, w_ * 0.16, b.height() * 0.07), '#d9b47c')
    _streetlamp(pen, b.left() + b.width() * 0.82, hz + b.height() * 0.05, b.height() * 0.9 / 5.0, 1, 0.0 if tod == 'morning' else 1.0)
    pen.fill(rect(b.left(), hz, b.width(), b.height()), '#7a7a74' if tod == 'morning' else '#0e1018')
    pen.cv.restore()
    for i in range(1, 3):
        xm = LWIN[0] + (LWIN[1] - LWIN[0]) * i / 3
        pen.seg(hv.p(xm, 2.1, 0.0), hv.p(xm, 0.85, 0.0), max(2.0, 0.03 * hv.s(0.0)), '#e8e0d0')
    pen.seg(hv.p(LWIN[0], 1.5, 0.0), hv.p(LWIN[1], 1.5, 0.0), max(2.0, 0.03 * hv.s(0.0)), '#e8e0d0')


def _drapes_art(pen, hv, t=0.0, open_=0.0):
    """Heavy rust-orange drapes either side of the front window + a sheer, on a brass rod (front wall, y ~0.08)."""
    y = 0.1
    for side in (-1, 1):
        xo = LWIN[0] - 0.35 if side < 0 else LWIN[1] - 0.05
        tl = hv.p(xo + (0.4 if side > 0 else 0.0), 2.25, y) if hv.f < 0 else hv.p(xo, 2.25, y)
        a_ = hv.p(xo, 2.25, y); b_ = hv.p(xo + 0.42, 2.25, y)
        xs = sorted([a_[0], b_[0]])
        w = xs[1] - xs[0]; top = a_[1]; h = hv.p(xo, 0.05, y)[1] - top
        _curtain(pen, xs[0], top, w, h, t, side, '#b8562a', 0.15, 31 + side, folds=6)
    a_ = hv.p(LWIN[0] - 0.4, 2.3, y); b_ = hv.p(LWIN[1] + 0.4, 2.3, y)
    pen.line(poly([a_, b_], False), max(2.0, 0.018 * hv.s(y)), '#b8903a')


def _tv_screen_layer(hv, tvf, content, name='tv_screen'):
    """The CRT's face drawn live in perspective (content: f(pen, W, H, t) for 'tape'; the default is the studio)."""
    x0, x1, Y0, Y1 = TVSCR
    yf = TVBOX[4] - 0.003
    q = [(x0, Y1, yf), (x1, Y1, yf), (x1, Y0, yf), (x0, Y0, yf)] if hv.f > 0 else [(x1, Y1, yf), (x0, Y1, yf), (x0, Y0, yf), (x1, Y0, yf)]
    W, H = (x1 - x0) * 100, (Y1 - Y0) * 100

    def draw(pen, t):
        mode, lvl = tvf(t)
        _hface(pen, hv, *q, W, H, lambda p_: _crt_face(p_, W, H, t, mode, lvl, content or _studio_on_tv))
    return Layer(hv.d(yf), draw, name, blur=None)


def _tv_glow_layer(hv, tvf, name='tv_glow'):
    def draw(pen, t):
        mode, lvl = tvf(t)
        if mode == 'off' or lvl <= 0.01: return
        x, y = (TVSCR[0] + TVSCR[1]) / 2, TVBOX[4]
        px, py = hv.p(x, (TVSCR[2] + TVSCR[3]) / 2, y); s = hv.s(y)
        c = {'snow': '#d8e0ff', 'blue': '#4a6aff'}.get(mode, '#b8d0ff')
        pen.radial(None, px, py, 1.4 * s, [(0, c, 70 * lvl), (0.4, c, 22 * lvl), (1, c, 0)], clip=False)
    return Layer(hv.d(TVBOX[4]) - 0.02, draw, name, blur=0)


def tv_level(tvf, t):
    """0..1 light the TV throws into the room at t (for the cast's light and the room's 'tv' light layer)."""
    m, l = tvf(t)
    if m == 'off': return 0.0
    flick = 0.88 + 0.12 * (0.5 + 0.5 * noise1(t * 6.0, 91))
    return l * flick * (1.15 if m == 'snow' else 1.0)


def gp_living(view='tv', lamp=1.0, tv=None, kitchen=1.0, steam=1.0, chair=True, mug=True, tod='night', content=None, moon=1.0):
    """The living room (mustard trellis wallpaper over dark wainscot, olive carpet, the rust velour couch, the brass floor
    lamp, the walnut cabinet with the CRT and the VCR, the tall bookcase on the front wall). view:
      'tv'     from the couch (seated): the back wall with the TV on its cabinet (left), the doorway to the kitchen
               (right of centre: through it, lit, Grandpa's chair at the table; anchor 'kitchen_chair' = Mister Winks),
               the arch to the hall at the right edge, the bookcase's end on the left
      'couch'  the reverse, from the TV end: the couch under the lamp, the front window with drapes, the bookcase
               (anchor 'bookcase_top': where Mister Winks sits at rule 5), Mom's spot in front of it.
    lamp = the floor lamp's level (flicker / out: dict(flick=[(t0, d)], out=[(t0, t1)])), tv = the TV (see _tv_spec:
    dict(on=t, snow=0.6, mode='tape', pulse=f(t)); tv_level(sp.info['tv'], t) gives the light it throws), kitchen = the
    pendant seen through the doorway, content = f(pen, W, H, t) drawing the tape (default: the 1974 studio with the
    audience; the cast adds Walter and the dummy through studio_figures). lens 'lens', grade 'gp_house' / 'tv_glow'."""
    tvf = _tv_spec(tv)
    lf, kf = _kfn(lamp, 51), _kfn(kitchen, 52)
    tvl = _kfn(0.0) if (tv is None or tv == 'off') else (lambda t: tv_level(tvf, t))
    box = FRAME
    amb = '#1c2034' if tod == 'night' else '#c4c8d0'
    lamp_l = [(LAMP_POS[0], 1.3, LAMP_POS[1], 3.0, GP_LAMP, 0.95), (LAMP_POS[0], 0.0, LAMP_POS[1], 2.0, GP_LAMP, 0.85, 0.4),
              (-3.7, 0.6, 2.0, 1.8, GP_LAMP, 0.6), (LAMP_POS[0], CEIL, LAMP_POS[1], 1.6, GP_LAMP, 0.6), (-2.0, 1.4, 0.0, 2.4, GP_LAMP, 0.5),
              (-5.5, 1.6, 0.36, 1.8, GP_LAMP, 0.35), (-2.6, 1.3, HALL_BACK, 3.2, GP_LAMP, 0.32), (-2.8, 0.0, 3.4, 2.4, GP_LAMP, 0.45, 0.4),
              (-1.35, 1.2, 3.0, 2.2, GP_LAMP, 0.4)]
    tv_l = [(-4.8, 0.9, 5.5, 2.2, GP_TV, 0.62), (-3.7, 0.6, 2.3, 2.0, GP_TV, 0.42), (-4.8, 0.0, 4.6, 1.8, GP_TV, 0.45, 0.4),
            (-4.8, CEIL, 5.0, 1.6, GP_TV, 0.25), (-6.0, 1.2, 4.8, 1.6, GP_TV, 0.3)]
    kit_l = [(-2.08, 0.0, 5.6, 1.6, GP_KLAMP, 0.7, 0.35), (-2.08, 1.2, HALL_BACK, 1.2, GP_KLAMP, 0.5), (-1.35, 1.0, 5.2, 1.0, GP_KLAMP, 0.3)]
    moon_l = [(-3.7, 1.2, 0.1, 2.6, GP_MOON, 0.55 * moon), (-3.7, 0.7, 1.6, 1.6, GP_MOON, 0.3 * moon)]
    if tod == 'morning':
        moon_l = [(-3.7, 1.4, 0.1, 4.0, '#f0f0ea', 0.9), (-3.7, 0.0, 2.0, 3.0, '#f0f0ea', 0.5, 0.4)]
    var = [('lamp', lamp_l, lf), ('tv', tv_l, tvl), ('kitchen', kit_l, kf)] if tod == 'night' else []
    if view == 'couch':
        hv = HView(760, 480, 1.58, -3.6, 4.75, -1)
        L = []

        def back(p_):
            _living_shell(p_, hv)
            _window_night(p_, hv, tod)
        L += _lit(hv.d(0.0), back, 'lv_room', _key('gp', 'liv', 'couch', 'room', tod, moon), box, hv, amb, moon_l, var)
        L += _lit(hv.d(0.12), lambda p_: _drapes_art(p_, hv), 'lv_drapes', _key('gp', 'liv', 'couch', 'drapes', tod), box, hv, amb, moon_l, var)
        L += _lit(hv.d(0.2), lambda p_: _bookcase_art(p_, hv), 'lv_bookcase', _key('gp', 'liv', 'couch', 'book', tod), box, hv, amb, moon_l, var)
        L += _lit(hv.d(1.9), lambda p_: _couch_art(p_, hv), 'lv_couch', _key('gp', 'liv', 'couch', 'couch', tod), box, hv, amb, moon_l, var)

        table = lambda p_: _coffee_table(p_, hv)
        L += _lit(hv.d(3.6), table, 'lv_table', _key('gp', 'liv', 'couch', 'table', tod), box, hv, amb, moon_l, var)
        L += _lit(hv.d(LAMP_POS[1]), lambda p_: _floor_lamp_art(p_, hv), 'lv_lamp_stand', _key('gp', 'liv', 'couch', 'lstand', tod), box, hv, amb, moon_l, var)
        sx, sy = hv.p(LAMP_POS[0], LAMP_POS[2], LAMP_POS[1]); ss = hv.s(LAMP_POS[1])
        L.append(Layer(hv.d(LAMP_POS[1]) - 0.01, lambda pen, t: (_lamp_shade(pen, sx, sy, ss, lf(t)),
                                                                pen.glow(sx, sy - 0.15 * ss, 0.9 * ss, '#ffd8a0', 70 * lf(t)) if lf(t) > 0.02 else None),
                       'lv_shade', blur=None))
        a = {'bookcase_top': hv.anchor((BOOK_X[0] + BOOK_X[1]) / 2, 0.2, BOOK_H, 'sitting on top of the bookcase'),
             'mom': hv.anchor(-4.75, 1.3, note='standing in front of the bookcase'),
             'couch_l': hv.anchor(-4.2, 1.9, 0.44, 'seated (couch, left)'), 'couch_m': hv.anchor(-3.7, 1.9, 0.44, 'seated (middle)'),
             'couch_r': hv.anchor(-3.15, 1.9, 0.44, 'seated (right, by the lamp)'), 'window': hv.anchor(-3.7, 0.55, note='at the front window (behind the couch)'),
             'you': hv.anchor(-3.4, 3.8, note='standing near the coffee table')}
        info = {'view': hv, 'lamp': lf, 'tv': tvf, 'kitchen': kf, 'cam_env': dict(x=(800, 1120), y=(420, 640), zoom=(1.0, 1.3), f=(1.0, 2.4))}
        return SetPiece('gp_living', L, a, {}, lens='lens', grade='gp_house' if tod == 'night' else 'morning', focus=3.0, dof=1.2, cover=FRAME, info=info)
    # view 'tv' (from the couch)
    hv = HView(900, 520, 1.12, -3.7, 2.05, 1)
    dx0, dy0 = hv.p(LDOOR[0], LDOOR[2], HALL_BACK); dx1, dy1 = hv.p(LDOOR[1], 0.0, HALL_BACK)
    kbox = (dx0 - (dx1 - dx0) * 1.2, dy0 - (dy1 - dy0) * 0.5, dx1 + (dx1 - dx0) * 1.2, dy1 + (dy1 - dy0) * 0.35)
    L = _kitchen_layers(hv, 'livk', kf, kbox, tod, mug, steam, chair)
    L += _lit(hv.d(HALL_BACK), lambda p_: _living_shell(p_, hv), 'lv_room', _key('gp', 'liv', 'tv', 'room', tod, moon), box, hv, amb, moon_l, var)

    def beyond_arch(p_):
        q = hv.quad([(LIV_X[1], 2.3, ARCH_Y[0]), (LIV_X[1], 2.3, ARCH_Y[1]), (LIV_X[1], 0, ARCH_Y[1]), (LIV_X[1], 0, ARCH_Y[0])])
        b = q.getBounds(); p_.fill(rect(b.left() - 40, b.top() - 40, b.width() + 400, b.height() + 80), '#2a2a34')
        _stairs_house(p_, hv)
    L += _lit(hv.d(ARCH_Y[1]) + 1.5, beyond_arch, 'lv_arch', _key('gp', 'liv', 'tv', 'arch', tod), (hv.x(LIV_X[1], ARCH_Y[1]) - 60, box[1], box[2], box[3]),
              hv, '#141826', [], [('kitchen', [(0.0, 1.0, 5.5, 2.0, GP_KLAMP, 0.4)], kf)])
    L += _lit(hv.d(5.73), lambda p_: _tv_cabinet_art(p_, hv), 'lv_tvset', _key('gp', 'liv', 'tv', 'tvset', tod), box, hv, amb, moon_l, var)
    L.append(_tv_screen_layer(hv, tvf, content))
    L.append(_tv_glow_layer(hv, tvf))
    L.append(Layer(hv.d(5.45), lambda pen, t: _vcr_clock(pen, hv, t), 'lv_vcr_clock', blur=None))
    L += _lit(hv.d(3.6), lambda p_: _coffee_table(p_, hv), 'lv_table', _key('gp', 'liv', 'tv', 'table', tod), box, hv, amb, moon_l, var)
    a = {'kitchen_chair': hv.anchor(GCHAIR[0], GCHAIR[1], 0.47, 'Grandpa\'s chair through the doorway (seat height)'),
         'kitchen_stand': hv.anchor(GCHAIR[0], GCHAIR[1], 0.5, 'standing on the chair seat'),
         'kitchen_door': hv.anchor((LDOOR[0] + LDOOR[1]) / 2, HALL_BACK - 0.25, note='in the doorway to the kitchen'),
         'tv_stand': hv.anchor(-4.0, 5.0, note='standing by the TV'), 'room_mid': hv.anchor(-3.4, 3.9),
         'arch': hv.anchor(-1.6, (ARCH_Y[0] + ARCH_Y[1]) / 2, note='in the arch to the hall')}
    info = {'view': hv, 'lamp': lf, 'tv': tvf, 'tv_level': tvl, 'kitchen': kf,
            'tv_screen': [hv.p(TVSCR[0], TVSCR[3], TVBOX[4]), hv.p(TVSCR[1], TVSCR[2], TVBOX[4])],
            'kdoor': (dx0, dy0, dx1, dy1), 'cam_env': dict(x=(700, 1300), y=(440, 620), zoom=(1.0, 1.3), f=(1.0, 3.4))}
    return SetPiece('gp_living', L, a, {}, lens='lens', grade='gp_house' if tod == 'night' else 'morning', focus=hv.d(GCHAIR[1]), dof=0.8,
                    cover=FRAME, info=info)


# ---------------------------------------------------------------------------------------------- the 1974 TV studio
STUDIO_STOOL = (960, 760)               # design point: the stool's seat top (Walter sits here, the dummy on his knee)


def laugh_waves(times, dur=2.6, peak=1.0):
    """Studio laughter envelope -> f(t) 0..1: one roaring wave per start time (fast swell ~0.35 s, a ragged tail)."""
    ts = sorted(times)

    def f(t):
        v = 0.0
        for t0 in ts:
            u = t - t0
            if 0 <= u < dur * 1.6:
                env = clamp(u / 0.35) * math.exp(-max(0.0, u - 0.6) / (dur * 0.45))
                v = max(v, peak * env * (0.86 + 0.14 * noise1(t * 7.0, 77)))
        return clamp(v)
    return f


def _bubble_text(pen, s, x, y, size, fill='#ffd23a', edge='#c8261e', shadow='#5a1a10', spacing=0.02, weight=900):
    """Chunky 70s show lettering: a fat outline, a drop shadow and a light top edge."""
    cv = pen.cv
    for (dx, dy, c, w) in ((size * 0.06, size * 0.08, shadow, size * 0.22), (0, 0, edge, size * 0.2)):
        f = skia.Font(typeface(weight), size)
        tw = text_width(s, weight, size, spacing)
        p = skia.Paint(AntiAlias=True, Color=col(c), Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeJoin=skia.Paint.kRound_Join)
        blob = skia.TextBlob.MakeFromString(s, f)
        cv.drawTextBlob(blob, x - tw / 2 + dx, y + dy, p)
    text(cv, s, x, y, weight, size, fill, 255, spacing, 'center')
    cv.save(); cv.clipRect(skia.Rect.MakeLTRB(x - 3000, y - size * 0.8, x + 3000, y - size * 0.55))
    text(cv, s, x, y, weight, size, '#fff6c8', 200, spacing, 'center'); cv.restore()


def _cloud_cutout(pen, x, y, w, seed=0):
    bumps = [(x - w * 0.32, y, w * 0.2), (x - w * 0.1, y - w * 0.12, w * 0.24), (x + w * 0.16, y - w * 0.08, w * 0.22), (x + w * 0.34, y + w * 0.02, w * 0.16)]
    p = rrect(x - w * 0.48, y - w * 0.02, w * 0.96, w * 0.2, w * 0.1)
    for (bx, by, br) in bumps: p = union(p, oval(bx, by, br))
    pen.fill(moved(p, w * 0.03, w * 0.04), '#000000', 60)
    pen.fill(p, '#f6f2e6'); pen.line(p, max(2.0, w * 0.018), '#3a7ac8')
    pen.fill(oval(x - w * 0.1, y - w * 0.18, w * 0.08, w * 0.04), '#ffffff', 200)


def _studio_static(pen, era=1974):
    """The stage of 'Saturday Morning with Walter Kemp' (1920 x 1080 design, drawn over -260..2180 x -160..1240):
    a sunburst flat with cardboard clouds, hills and lollipop trees, the marquee sign, the teal riser with stars, the
    stool, the little side table with a glass of milk. Painted bright: the VHS grade (vhs74) and fx['vhs'] age it."""
    x0, y0, x1, y1 = -260, -160, 2180, 1240
    cx, cy = 960, 470
    pen.fill(rect(x0, y0, x1 - x0, y1 - y0), '#f0a838')
    for k in range(24):                                                          # the sunburst
        a0 = k * math.pi / 12; a1 = a0 + math.pi / 24
        pen.fill(poly([(cx, cy), (cx + math.cos(a0) * 2600, cy + math.sin(a0) * 2600), (cx + math.cos(a1) * 2600, cy + math.sin(a1) * 2600)]), '#f6c64a')
    pen.radial(None, cx, cy, 1300, [(0, '#fff2c0', 150), (1, '#fff2c0', 0)], clip=False)
    # rainbow arc
    for i, c in enumerate(('#e8463a', '#f2963a', '#f6d23a', '#5ab05a', '#3a8ad8', '#7a5ac8')):
        r = 720 - i * 34
        pen.line(smooth([(cx + math.cos(a) * r, cy + 150 + math.sin(a) * r * 0.75) for a in np.linspace(math.pi * 1.05, math.pi * 1.95, 14)], False), 34, c)
    for (x, y, w, sd) in ((330, 230, 380, 1), (1600, 180, 420, 2), (1250, 360, 260, 3), (620, 420, 220, 4)):
        _cloud_cutout(pen, x, y, w, sd)
    # hills + lollipop trees
    for (hx, hy, hw, c) in ((300, 820, 900, '#5ab04a'), (1650, 800, 1000, '#4a9a3a'), (960, 860, 1400, '#6ac05a')):
        h = smooth([(hx - hw * 0.6, 1300), (hx - hw * 0.5, hy + 60), (hx, hy - 80), (hx + hw * 0.5, hy + 60), (hx + hw * 0.6, 1300)], True, 0.6)
        pen.fill(h, c); pen.line(h, 5, '#2a5a2a')
    for (tx, ty, s, c) in ((180, 720, 1.0, '#3a8a3a'), (1760, 690, 1.15, '#e8463a'), (1540, 760, 0.8, '#3a8a3a'), (420, 770, 0.75, '#f2963a')):
        pen.fill(rect(tx - 9 * s, ty, 18 * s, 160 * s), '#8a5a2a'); pen.line(rect(tx - 9 * s, ty, 18 * s, 160 * s), 3, LINE)
        pen.fill(oval(tx, ty - 40 * s, 80 * s), c); pen.line(oval(tx, ty - 40 * s, 80 * s), 5, LINE)
        pen.line(smooth([(tx - 50 * s, ty - 50 * s), (tx, ty - 90 * s), (tx + 40 * s, ty - 40 * s)], False), 4, '#ffffff', 90)
    # the riser: teal with gold stars, a lip
    rs = rect(x0, 840, x1 - x0, y1 - 840)
    pen.fill(rs, '#1f8a8a'); pen.linear(rs, 0, 840, 0, 1100, [(0, '#000000', 0), (1, '#000000', 120)])
    pen.fill(rect(x0, 832, x1 - x0, 22), '#f2c23a'); pen.line(rect(x0, 832, x1 - x0, 22), 3, LINE)
    for i in range(14):
        sx = x0 + 90 + i * 180; sy = 950 + (i % 2) * 70
        st = poly([(sx + math.cos(a) * (26 if j % 2 == 0 else 11), sy + math.sin(a) * (26 if j % 2 == 0 else 11))
                   for j, a in enumerate(np.linspace(-math.pi / 2, 1.5 * math.pi, 11)[:-1])])
        pen.fill(st, '#f2d24a', 230)
    # the stool (chrome legs, red seat) and the side table with a glass of milk
    sx, sy = STUDIO_STOOL
    for dx in (-48, 48, -20, 20):
        pen.line(poly([(sx + dx * 0.6, sy + 10), (sx + dx, 850)], False), 9, LINE); pen.line(poly([(sx + dx * 0.6, sy + 10), (sx + dx, 850)], False), 6, '#c8ccd4')
    pen.line(oval(sx, sy + 70, 40, 8), 5, '#c8ccd4')
    seat = oval(sx, sy, 62, 17)
    pen.fill(rect(sx - 62, sy, 124, 14), '#8a1a1a'); pen.fill(seat, '#d8322a'); pen.line(union(seat, rect(sx - 62, sy, 124, 14)), 4, LINE)
    tx, ty = 1290, 740
    pen.fill(rect(tx - 6, ty, 12, 100), '#c8ccd4'); pen.line(rect(tx - 6, ty, 12, 100), 3, LINE)
    pen.fill(oval(tx, ty, 70, 14), '#e8463a'); pen.line(oval(tx, ty, 70, 14), 3, LINE)
    pen.fill(rrect(tx - 16, ty - 64, 32, 62, 5), '#f6f4ee'); pen.fill(rect(tx - 16, ty - 64, 32, 14), '#ffffff', 120); pen.line(rrect(tx - 16, ty - 64, 32, 62, 5), 3, LINE)


def _studio_sign(pen, t=0.0, live=False, chase=1.0):
    """The marquee sign over the stage: SATURDAY MORNING (bubble letters) on a rounded red board ringed with bulbs, the
    'with WALTER KEMP' ribbon. live=True draws only the bulbs (chasing)."""
    bx, by, bw, bh = 470, 40, 980, 250
    if not live:
        board = rrect(bx, by, bw, bh, 70)
        pen.fill(moved(board, 10, 14), '#000000', 90); pen.fill(board, '#c8261e'); pen.line(board, 7, LINE)
        pen.fill(rrect(bx + 26, by + 26, bw - 52, bh - 52, 50), '#e8463a')
        _bubble_text(pen, 'SATURDAY', 960, by + 112, 92)
        _bubble_text(pen, 'MORNING', 960, by + 205, 92)
        rb = poly([(620, 300), (1300, 300), (1340, 338), (1300, 376), (620, 376), (580, 338)])
        pen.fill(moved(rb, 6, 8), '#000000', 80); pen.fill(rb, '#2a6ab0'); pen.line(rb, 5, LINE)
        text(pen.cv, 'with WALTER KEMP', 960, 354, 900, 44, '#f6f2e6', 255, 0.04)
        return
    n = 34
    for i in range(n):
        u = i / n
        per = 2 * (bw + bh); d = u * per
        if d < bw: x, y = bx + d, by
        elif d < bw + bh: x, y = bx + bw, by + d - bw
        elif d < 2 * bw + bh: x, y = bx + bw - (d - bw - bh), by + bh
        else: x, y = bx, by + bh - (d - 2 * bw - bh)
        on = chase <= 0 or ((i + int(t * 8 * chase)) % 3 != 0)
        pen.fill(oval(x, y, 11), '#fff6d0' if on else '#8a6a3a')
        if on: pen.glow(x, y, 26, '#ffe28a', 120)


def _applause_sign(pen, x, y, k):
    """The red APPLAUSE box (lit at level k)."""
    r = rrect(x - 150, y - 42, 300, 84, 10)
    pen.fill(moved(r, 6, 8), '#000000', 90)
    pen.fill(r, mix('#3a0c0c', '#e8261e', k)); pen.line(r, 6, LINE)
    text(pen.cv, 'APPLAUSE', x, y + 16, 900, 44, mix('#7a3a30', '#fff2e8', k), 255, 0.08)
    if k > 0.05: pen.glow(x, y, 220, '#ff4a3a', 110 * k)


def _audience(pen, t, laugh, y_base=1080, n=17, seed=0, scale=1.0, dark='#0e0a0c', rim='#f6b858'):
    """Two rows of audience heads from behind (kids and parents), dark against the bright stage; laughter shakes them,
    tips heads back, lifts a few clapping hands. laugh = f(t) 0..1."""
    lv = laugh(t) if laugh else 0.0
    for row in range(2):
        yb = y_base + (0 if row == 0 else 70 * scale)
        k = row * 0.25
        for i in range(n + row):
            x = -120 + (2160 / (n - 1)) * (i + (0.5 if row else 0.0)) + 30 * (_h(i, seed + row) - 0.5)
            kid = _h(i, seed + 5 + row) < 0.45
            r = (42 if kid else 56) * scale * (1.0 + 0.2 * row)
            ph = _h(i, seed + 9) * 6.28
            bob = lv * (14 + 10 * _h(i, seed + 3)) * scale * abs(math.sin(t * (9 + 3 * _h(i, seed + 4)) + ph))
            tip = lv * 8 * math.sin(t * 5 + ph)
            hy = yb - (190 if kid else 250) * scale * (1.0 + 0.15 * row) - bob
            cv = pen.cv; cv.save(); cv.translate(x, hy); cv.rotate(tip)
            body = smooth([(-r * 1.9, 260 * scale), (-r * 1.7, r * 1.2), (-r * 0.6, r * 0.9), (r * 0.6, r * 0.9), (r * 1.7, r * 1.2), (r * 1.9, 260 * scale)], True, 0.5)
            pen.fill(body, mix(dark, '#2a2028', k)); pen.fill(oval(0, 0, r, r * 1.08), mix(dark, '#2a2028', k))
            if _h(i, seed + 11) < 0.3:                                              # pigtails / a cap / big 70s hair
                pen.fill(oval(-r * 0.95, r * 0.2, r * 0.32, r * 0.5), mix(dark, '#2a2028', k)); pen.fill(oval(r * 0.95, r * 0.2, r * 0.32, r * 0.5), mix(dark, '#2a2028', k))
            elif _h(i, seed + 11) > 0.8:
                pen.fill(oval(0, -r * 0.1, r * 1.35, r * 1.2), mix(dark, '#2a2028', k))
            pen.line(smooth([(-r * 0.7, -r * 0.75), (0, -r * 1.1), (r * 0.7, -r * 0.75)], False), max(2.0, r * 0.09), rim, 120)
            cv.restore()
            if lv > 0.4 and _h(i, seed + 13) < 0.35:                                # clapping hands up
                cl = abs(math.sin(t * 14 + ph))
                hx = x + (r * 1.1 if _h(i, seed + 14) < 0.5 else -r * 1.1)
                for sgn in (-1, 1):
                    pen.fill(oval(hx + sgn * r * 0.25 * cl, hy - r * 0.6 - lv * 20 * scale, r * 0.26, r * 0.36), mix(dark, '#2a2028', k))


def studio_content(figures=None, laugh=None, applause=None, era=1974, crop=True):
    """The tape's picture as a content function f(pen, W, H, t) for a screen of W x H (4:3): the studio (cached sprite),
    the marquee bulbs, the APPLAUSE sign (lit by applause(t) or laugh(t) > 0.35), figures(pen, t) drawn in the studio's
    1920 x 1080 design space (Walter on the stool with the dummy on his knee: the cast), then the audience in front.
    crop=True takes the 4:3 middle of the 16:9 stage (x 240..1680)."""
    lf = laugh or (lambda t: 0.0)
    af = applause or (lambda t: clamp((lf(t) - 0.35) * 3.0))

    def content(pen, W, H, t):
        cv = pen.cv; cv.save()
        if crop: cv.scale(W / 1440.0, H / 1080.0); cv.translate(-240, 0)
        else: cv.scale(W / 1920.0, H / 1080.0)
        _sprite(pen, ('studio74', era), lambda p_: (_studio_static(p_, era), _studio_sign(p_)), (-260, -160, 2180, 1240))
        _studio_sign(pen, t, live=True)
        _applause_sign(pen, 1690 if not crop else 1500, 470, af(t))
        if figures: figures(pen, t)
        _audience(pen, t, lf, 1120, 13 if crop else 17)
        cv.restore()
    return content


_studio_on_tv = studio_content(laugh=laugh_waves([1.0]))


def gp_studio(view='full', laugh=None, applause=None, vhs=None, bezel=0.0, track=0.35, era=1974):
    """'Saturday Morning with Walter Kemp', 1974, as the tape shows it, FULL FRAME (for the push into the screen):
    the cheerful stage (sunburst, cardboard clouds, rainbow, lollipop trees, the marquee sign with chasing bulbs, the teal
    riser with stars, the red stool, the glass of milk), the APPLAUSE box (lights with the laughter), the audience's heads
    in the foreground shaking with each wave (laugh = f(t) 0..1, e.g. laugh_waves([t0, t1, ...])). Walter and the dummy are
    the cast: anchor 'stool' (seat top, depth 1.0), 'knee' (where the dummy sits), 'stand' (Walter standing).
    view 'full' (the show's wide) | 'close' (the studio camera tighter on the stool: the dummy's look into the lens).
    The tape look is engine post fx['vhs'] (wobble, tracking band (track 0..1), chroma bleed, snow, scanlines, the CRT
    glass curve; bezel 0..1 shows the TV's plastic round the tube) via sp.fx(t); grade 'vhs74'. vhs=False turns it off."""
    lf = laugh or (lambda t: 0.0)
    af = applause or (lambda t: clamp((lf(t) - 0.35) * 3.0))
    zoom = 1.0 if view == 'full' else 1.0
    L = [Layer(3.0, lambda pen, t: _studio_static(pen, era), 'st_stage', cache=_key('gp', 'studio', era), bounds=(-260, -160, 2180, 1240)),
         Layer(2.6, lambda pen, t: _studio_sign(pen), 'st_sign', cache=_key('gp', 'studio', 'sign'), bounds=(380, -40, 1540, 420)),
         Layer(2.59, lambda pen, t: _studio_sign(pen, t, live=True), 'st_bulbs', blur=None),
         Layer(2.6, lambda pen, t: _applause_sign(pen, 1690, 470, af(t)), 'st_applause', blur=None),
         Layer(0.62, lambda pen, t: _audience(pen, t, lf, 1120, 17), 'st_audience', blur=None)]

    def spots(pen, t):
        for (x, c) in ((420, '#fff2c8'), (1500, '#ffe0f0')):
            pen.cone(x, -60, 30, 520, 980, c, 34, 60)
    L.append(Layer(2.0, spots, 'st_spots', cache=_key('gp', 'studio', 'spots'), bounds=(-200, -100, 2120, 1180), blur=0))
    a = {'stool': Anchor(STUDIO_STOOL[0], STUDIO_STOOL[1], 1.0, 760.0, 'the stool seat top (Walter sits; height = a 1.85 m adult standing on the riser)'),
         'knee': Anchor(STUDIO_STOOL[0] + 70, STUDIO_STOOL[1] - 40, 1.0, 760.0, 'the dummy on his right knee'),
         'stand': Anchor(STUDIO_STOOL[0] + 260, 845, 1.0, 760.0, 'standing on the riser beside the stool')}
    use_vhs = vhs is not False

    def fx(t):
        return {'vhs': dict(t=t, track=track, bezel=bezel)} if use_vhs else {}
    cam_hint = (960, 600, 1.0) if view == 'full' else (1010, 560, 1.7)
    info = {'laugh': lf, 'applause': af, 'cam_home': cam_hint, 'cam_env': dict(x=(860, 1080), y=(480, 640), zoom=(1.0, 2.2), f=(1.0, 1.6))}
    return SetPiece('gp_studio', L, a, {}, lens=None, grade='vhs74', focus=1.0, dof=0.0, cover=(-260, -160, 2180, 1240), fx=fx, info=info)


# ---------------------------------------------------------------------------------------------- the den
DEN = dict(W=2.0, D=3.9, CH=2.5)                     # half width, back wall distance, ceiling (den-local View coordinates)
DEN_CHAIR = (-0.3, 2.65)                             # Grandpa's armchair (X, D): faces the door
DEN_LAMP = (0.55, 2.85, 1.45)                         # the reading lamp beside it (X, D, shade bottom Y)


def _vbox(pen, v, X0, X1, Y0, Y1, D0, D1, c, top=None, side=None, tex=None, faces=None, lw=None):
    """_hbox for a plain View (camera at X = 0 looking along +D)."""
    hv = HView(v.S, v.h, v.cam_h, 0.0, 0.0, 1, v.cx)
    return _hbox(pen, hv, X0, X1, Y0, Y1, D0, D1, c, top, side, lw, True, tex, faces)


def _armchair(pen, hv, x, y, face=-1, c='#2f5a3e', part='all'):
    """Grandpa's green leather wingback armchair at (x, y) (plan coords of hv), facing -y (toward the camera) when
    face=-1. Buttoned back, rolled arms, wings, a worn seat cushion, short mahogany legs."""
    hw, hd = 0.44, 0.42
    Ys = 0.46
    yb = y + hd if face < 0 else y - hd
    yf = y - hd if face < 0 else y + hd
    cd = _darken(c, 0.35)
    if part in ('all', 'back'):
        bk = [(x - hw + 0.04, 1.22, yb), (x + hw - 0.04, 1.22, yb), (x + hw - 0.04, Ys, yb), (x - hw + 0.04, Ys, yb)]
        _hface(pen, hv, *bk, 80, 76, lambda p_: (p_.fill(rrect(0, 0, 80, 80, 14), c), p_.texture(rect(0, 0, 80, 76), 'grunge', 0.35, 'overlay', 0.5),
                                                [p_.fill(oval(14 + 13 * (i % 5), 14 + 14 * (i // 5), 1.6), _darken(c, 0.5)) for i in range(15)],
                                                p_.radial(rect(0, 0, 80, 76), 40, 20, 60, [(0, '#ffffff', 40), (1, '#ffffff', 0)]),
                                                p_.line(rrect(0, 0, 80, 80, 14), 1.5, LINE)))
        for sgn in (-1, 1):                                                   # the wings
            wq = hv.quad([(x + sgn * (hw - 0.02), 1.18, yb), (x + sgn * (hw + 0.02), 1.05, yb - 0.3 * (1 if face < 0 else -1)),
                          (x + sgn * (hw + 0.02), 0.7, yb - 0.3 * (1 if face < 0 else -1)), (x + sgn * (hw - 0.02), 0.7, yb)])
            pen.fill(wq, _lighten(c, 0.05)); pen.line(wq, 1.4, LINE, 210)
        _hbox(pen, hv, x - hw + 0.08, x + hw - 0.08, Ys - 0.1, Ys + 0.04, min(yb, yf), max(yb, yf), c, top=_lighten(c, 0.12), tex='grunge')
    if part in ('all', 'arms'):
        for sgn in (-1, 1):
            ax0 = x + sgn * hw - (0.13 if sgn > 0 else 0.0)
            _hbox(pen, hv, ax0, ax0 + 0.13, 0.12, 0.66, min(yb, yf), max(yb, yf), c, top=_lighten(c, 0.15), tex='grunge')
            fx, fy = hv.p(ax0 + 0.065, 0.66, yf); fs = hv.s(yf)
            pen.fill(oval(fx, fy, 0.075 * fs, 0.05 * fs), _lighten(c, 0.1)); pen.line(oval(fx, fy, 0.075 * fs, 0.05 * fs), 1.2, LINE, 200)
        _hbox(pen, hv, x - hw + 0.02, x + hw - 0.02, 0.1, Ys - 0.1, min(yb, yf), max(yb, yf), cd)
        for sgn in (-1, 1):
            a_, b_ = hv.p(x + sgn * (hw - 0.06), 0.0, yf + 0.03 * face), hv.p(x + sgn * (hw - 0.06), 0.1, yf + 0.03 * face)
            pen.seg(a_, b_, max(2.0, 0.04 * hv.s(yf)), '#3a1a0c')


def gp_den(lamp=1.0, hall=0.5, moon=1.0):
    """Grandpa's den, from its door (the end of the hall): dark walnut panelling hung with his framed show posters
    (SATURDAY MORNING 1974, THE PALACE 1962, LIVE!) and photos, the green leather wingback armchair facing you with the
    brass reading lamp beside it (lamp: the level spec; 'The lamp goes out': dict(out=[(t0, t1)])), the oriental rug
    (Mister Winks lies face down on it later), a side table with his pipe and glasses, a shelf of trophies with an
    EMPTY dummy stand, a curtained window. Anchors: armchair (Owen seated: seat height), knee_front (you kneel there),
    mom (standing at the chair's left), rug (the dummy face down), door. lens 'lens', grade 'gp_house'."""
    hv = HView(700, 520, 1.5, 0.0, -0.3, 1)
    lf = _kfn(lamp, 61); hf = _kfn(hall, 62)
    W_, D_, CH_ = DEN['W'], DEN['D'], DEN['CH']
    box = FRAME
    amb = '#1c1e30'
    moon_l = [(-W_, 1.3, 2.4, 1.8, GP_MOON, 0.6 * moon), (-1.0, 0.0, 2.4, 1.6, GP_MOON, 0.3 * moon, 0.4)]
    lamp_l = [(DEN_LAMP[0], 1.2, DEN_LAMP[1], 2.4, GP_LAMP, 1.0), (DEN_LAMP[0], 0.0, DEN_LAMP[1] - 0.4, 2.0, GP_LAMP, 0.85, 0.4),
              (DEN_CHAIR[0], 0.8, DEN_CHAIR[1] - 0.3, 1.3, GP_LAMP, 0.7), (0.3, 1.5, D_, 2.2, GP_LAMP, 0.55), (W_, 1.3, 3.0, 1.8, GP_LAMP, 0.4)]
    hall_l = [(0.0, 0.0, 0.8, 1.6, GP_LAMP, 0.5, 0.4), (0.0, 1.2, D_, 2.4, GP_LAMP, 0.18)]
    var = [('lamp', lamp_l, lf), ('hall', hall_l, hf)]

    def room(p_):
        def back_art(q, W, H):
            _hframe(q, W, H, 70, H - 200, 50, 66, 'poster', fn=lambda p2, w, h: _poster_art(p2, w, h, '1974'))
            _hframe(q, W, H, 150, H - 196, 44, 60, 'poster', fn=lambda p2, w, h: _poster_art(p2, w, h, '1962'))
            _hframe(q, W, H, 300, H - 192, 40, 52, 'poster', fn=lambda p2, w, h: _poster_art(p2, w, h, 'live'))
            _hframe(q, W, H, 228, H - 150, 22, 28, 'photo', seed=41)
        _hwall(p_, hv, (-W_, D_), (W_, D_), 0.0, CH_, '#5a3420', '#2a1408', 'panel', 0.0, art=back_art, pa=200, trim='#3a1e0e', seed=21)
        def left_art(q, W, H):
            _hframe(q, W, H, 300, H - 170, 26, 32, 'photo', seed=42)
        _hwall(p_, hv, (-W_, 0.25), (-W_, D_), 0.0, CH_, '#5a3420', '#2a1408', 'panel', 0.0, holes=[(1.6, 0.85, 2.7, 2.05)], art=left_art,
               pa=200, trim='#3a1e0e', seed=22)
        wq = hv.quad([(-W_, 2.05, 1.85), (-W_, 2.05, 2.95), (-W_, 0.85, 2.95), (-W_, 0.85, 1.85)])
        p_.fill(wq, '#1a2650')
        for (u0, u1) in ((1.7, 2.0), (2.55, 2.85)):                             # heavy drapes
            dq = hv.quad([(-W_ + 0.03, 2.2, u0 + 0.05), (-W_ + 0.03, 2.2, u1 + 0.05), (-W_ + 0.03, 0.4, u1 + 0.05), (-W_ + 0.03, 0.4, u0 + 0.05)])
            p_.fill(dq, '#5a1a1e'); p_.texture(dq, 'fabric', 0.6, 'overlay', 1.0, 90); p_.line(dq, 1.5, LINE, 200)
        def right_art(q, W, H):
            q.fill(rect(150, H - 160, 120, 4), '#3a1e0e'); q.fill(rect(150, H - 110, 120, 4), '#3a1e0e')
            for i in range(4):
                tx = 165 + i * 28
                q.fill(poly([(tx - 4, H - 160), (tx + 4, H - 160), (tx + 2, H - 176), (tx - 2, H - 176)]), '#c9a24a'); q.fill(oval(tx, H - 179, 4), '#e8c860')
            q.fill(rect(215, H - 156, 4, 40), '#2a1408'); q.fill(rect(207, H - 118, 20, 3), '#2a1408')       # the empty dummy stand
            q.fill(rrect(210, H - 160, 14, 6, 2), '#2a1408')
        _hwall(p_, hv, (W_, 0.25), (W_, D_), 0.0, CH_, '#5a3420', '#2a1408', 'panel', 0.0, art=right_art, pa=200, trim='#3a1e0e', seed=23)
        _hfloor(p_, hv, -W_, W_, 0.25, D_, 'boards', '#6a4426', '#3a2212')
        rug = (-1.05, 0.85, 0.9, 2.2)
        _hface(p_, hv, (rug[0], 0.004, rug[3]), (rug[1], 0.004, rug[3]), (rug[1], 0.004, rug[2]), (rug[0], 0.004, rug[2]), 190, 155, _rug_art)
        _hceil(p_, hv, -W_, W_, 0.25, D_, CH_, '#4a3424')
    L = _lit(hv.d(D_), room, 'den_room', _key('gp', 'den', 'room', moon), box, hv, amb, moon_l, var)

    def furniture(p_):
        _hbox(p_, hv, -1.4, -0.95, 0.0, 0.58, 2.45, 2.9, '#4a2814', top='#5a3420', tex='wood')
        px, py = hv.p(-1.17, 0.58, 2.65); s = hv.s(2.65)
        p_.line(smooth([(px - 0.08 * s, py - 0.02 * s), (px + 0.03 * s, py), (px + 0.06 * s, py - 0.04 * s)], False), max(2.0, 0.014 * s), '#2a1408')   # pipe
        p_.fill(oval(px + 0.07 * s, py - 0.05 * s, 0.022 * s, 0.018 * s), '#3a1a0a')
        p_.line(oval(px - 0.1 * s, py - 0.01 * s, 0.03 * s, 0.015 * s), 1.2, '#c8b890'); p_.line(oval(px - 0.03 * s, py - 0.01 * s, 0.03 * s, 0.015 * s), 1.2, '#c8b890')
        _armchair(p_, hv, DEN_CHAIR[0], DEN_CHAIR[1], -1, part='back')
        _floor_lamp_den(p_, hv)
    L += _lit(hv.d(DEN_CHAIR[1] + 0.3), furniture, 'den_chair', _key('gp', 'den', 'chair', moon), box, hv, amb, moon_l, var)
    L += _lit(hv.d(DEN_CHAIR[1] - 0.45), lambda p_: _armchair(p_, hv, DEN_CHAIR[0], DEN_CHAIR[1], -1, part='arms'), 'den_arms',
              _key('gp', 'den', 'arms', moon), box, hv, amb, moon_l, var)
    sx, sy = hv.p(DEN_LAMP[0], DEN_LAMP[2], DEN_LAMP[1]); ss = hv.s(DEN_LAMP[1])
    L.append(Layer(hv.d(DEN_LAMP[1]) - 0.02, lambda pen, t: (_lamp_shade(pen, sx, sy, ss, lf(t), '#d8c49a', 'bell'),
                                                            pen.glow(sx, sy - 0.12 * ss, 1.0 * ss, '#ffd8a0', 80 * lf(t)) if lf(t) > 0.02 else None), 'den_shade', blur=None))
    a = {'armchair': hv.anchor(DEN_CHAIR[0], DEN_CHAIR[1] - 0.05, 0.5, 'seated in the armchair (seat height)'),
         'knee_front': hv.anchor(DEN_CHAIR[0] + 0.05, DEN_CHAIR[1] - 0.95, note='kneeling in front of the chair'),
         'mom': hv.anchor(DEN_CHAIR[0] - 0.85, DEN_CHAIR[1] - 0.6, note='standing at the chair\'s left'),
         'rug': hv.anchor(-0.1, 1.5, 0.0, 'lying face down on the rug'), 'door': hv.anchor(0.0, 0.5, note='in the doorway')}
    info = {'view': hv, 'lamp': lf, 'hall': hf, 'cam_env': dict(x=(800, 1120), y=(440, 640), zoom=(1.0, 1.3), f=(1.0, 2.6))}
    return SetPiece('gp_den', L, a, {}, lens='lens', grade='gp_house', focus=hv.d(DEN_CHAIR[1]), dof=1.2, cover=FRAME, info=info)


def _rug_art(p_):
    """An oriental rug (190 x 155 cm frame): border bands, a medallion."""
    W, H = 190, 155
    p_.fill(rect(0, 0, W, H), '#6a1a1e'); p_.texture(rect(0, 0, W, H), 'fabric', 0.7, 'overlay', 0.6)
    for k, c in enumerate(('#1a2a4a', '#c89a4a', '#2a1a3a')):
        p_.line(rect(6 + k * 7, 6 + k * 7, W - 12 - k * 14, H - 12 - k * 14), 4.5, c)
    med = poly([(W / 2, H * 0.2), (W * 0.72, H / 2), (W / 2, H * 0.8), (W * 0.28, H / 2)])
    p_.fill(med, '#1a2a4a'); p_.line(med, 2.0, '#c89a4a')
    p_.fill(oval(W / 2, H / 2, 12, 9), '#c89a4a')
    for i in range(int(W / 3)):
        p_.seg((i * 3, 0), (i * 3, -4), 1.0, '#d8c8a0', 200); p_.seg((i * 3, H), (i * 3, H + 4), 1.0, '#d8c8a0', 200)


def _floor_lamp_den(p_, hv):
    x, y, Yb = DEN_LAMP
    a_, b_ = hv.p(x, 0.0, y), hv.p(x, Yb + 0.05, y); s = hv.s(y)
    p_.fill(oval(a_[0], a_[1], 0.15 * s, 0.04 * s), '#6a4a1a')
    p_.seg(a_, b_, max(2.5, 0.02 * s) + 2, LINE, 220); p_.seg(a_, b_, max(2.0, 0.02 * s), '#b8903a')


# ---------------------------------------------------------------------------------------------- your bedroom doorway (home)
def bedroom_doorway(hall=1.0, door=0.85, moon=1.0):
    """Your bedroom at home, months later, from your bed (lying, eye ~0.75 m): the dark room (band poster, a pennant,
    the desk and chair with clothes over it), the bed's foot in the foreground, and the open doorway in the far wall
    with the warm hall light behind it, so whoever stops there is a silhouette with a rim (anchor 'doorway').
    hall = the hall light level; door = how far the door is open (0..1). lens 'lens', grade 'gp_dark'."""
    hv = HView(700, 600, 0.78, 0.0, -0.1, 1)
    hf = _kfn(hall, 71)
    D_, W_, CH_ = 3.3, 1.7, 2.4
    DXa, DXb = -0.15, 0.7
    box = FRAME
    amb = '#141828'
    moon_l = [(-W_, 1.2, 2.6, 1.6, GP_MOON, 0.5 * moon), (-0.6, 0.0, 2.6, 1.5, GP_MOON, 0.3 * moon, 0.4)]
    hall_l = [((DXa + DXb) / 2, 0.0, D_ - 0.6, 1.4, GP_LAMP, 0.9, 0.3), ((DXa + DXb) / 2, 1.0, D_, 1.3, GP_LAMP, 0.55),
              (W_, 1.0, D_ - 0.5, 1.2, GP_LAMP, 0.35)]
    var = [('hall', hall_l, hf)]

    def beyond(p_):
        q = hv.quad([(DXa, 2.05, D_), (DXb, 2.05, D_), (DXb, 0.0, D_), (DXa, 0.0, D_)]); b = q.getBounds()
        p_.fill(rect(b.left() - 60, b.top() - 60, b.width() + 120, b.height() + 120), '#e8c890')
        _hwall(p_, hv, (DXa - 1.0, D_ + 1.2), (DXb + 1.0, D_ + 1.2), 0.0, CH_, '#d8c49a', '#b8a070', 'stripe', 0.0, pa=60, seed=71)
        _hfloor(p_, hv, DXa - 1.0, DXb + 1.0, D_, D_ + 1.2, 'boards', '#a8784a', '#7a5432')
    L = _lit(hv.d(D_ + 1.0), beyond, 'bd_hall', _key('gp', 'bed', 'hall'), box, hv, '#4a3a2a', [], [('hall', [((DXa + DXb) / 2, 1.6, D_ + 1.0, 2.0, '#fff0d0', 1.0)], hf)])

    def room(p_):
        def back_art(q, W, H):
            q.fill(rect(25, H - 205, 46, 64), '#1a1a2a'); q.fill(rect(29, H - 201, 38, 40), '#c83a3a')
            text(q.cv, 'THE MOTH', 48, H - 150, 900, 7, '#f0e0d0', 230, 0.1)
            q.fill(poly([(250, H - 200), (330, H - 188), (250, H - 176)]), '#2a5aa8'); text(q.cv, 'GO!', 272, H - 185, 900, 7, '#ffffff', 230, 0.1)
        _hwall(p_, hv, (-W_, D_), (W_, D_), 0.0, CH_, '#4a5a7a', '#3a4a68', 'stripe', 0.0, holes=[(DXa + W_, 0.0, DXb + W_, 2.05)], art=back_art, pa=90,
               trim='#d8d0c0', seed=72)
        _hwall(p_, hv, (-W_, 0.3), (-W_, D_), 0.0, CH_, '#4a5a7a', '#3a4a68', 'stripe', 0.0, holes=[(1.9, 0.95, 2.7, 1.95)], pa=90, trim='#d8d0c0', seed=73)
        wq = hv.quad([(-W_, 1.95, 2.2), (-W_, 1.95, 3.0), (-W_, 0.95, 3.0), (-W_, 0.95, 2.2)]); p_.fill(wq, '#1e2c5a')
        for (u0, u1) in ((2.05, 2.25), (2.95, 3.15)):
            dq = hv.quad([(-W_ + 0.02, 2.1, u0), (-W_ + 0.02, 2.1, u1), (-W_ + 0.02, 0.8, u1), (-W_ + 0.02, 0.8, u0)]); p_.fill(dq, '#3a3a5a')
        _hwall(p_, hv, (W_, 0.3), (W_, D_), 0.0, CH_, '#4a5a7a', '#3a4a68', 'stripe', 0.0, pa=90, trim='#d8d0c0', seed=74)
        _hfloor(p_, hv, -W_, W_, 0.3, D_, 'carpet', '#4a4a5a')
        _hceil(p_, hv, -W_, W_, 0.3, D_, CH_, '#5a5a66')
        _hbox(p_, hv, 0.95, 1.65, 0.0, 0.75, 1.6, 2.2, '#5a4a3a', top='#6a5a48', tex='wood')                        # desk
        _hbox(p_, hv, 0.75, 1.15, 0.0, 0.45, 1.85, 2.2, '#3a3a44')                                                  # chair + clothes
        cq = hv.quad([(0.72, 0.95, 2.2), (1.18, 0.95, 2.2), (1.2, 0.3, 1.95), (0.7, 0.35, 1.95)])
        p_.fill(cq, '#6a3a3a'); p_.line(cq, 1.2, LINE, 200)
    L += _lit(hv.d(D_), room, 'bd_room', _key('gp', 'bed', 'room', moon), box, hv, amb, moon_l, var)

    def leaf(p_):
        ang = math.radians(100.0) * clamp(door)
        xf = DXb - 0.85 * math.cos(ang); yf = D_ - 0.85 * math.sin(ang)
        q = [(DXb, 2.05, D_), (xf, 2.05, yf), (xf, 0.0, yf), (DXb, 0.0, D_)]
        _hface(p_, hv, *q, 85, 205, lambda pp: (pp.fill(rect(0, 0, 85, 205), '#d8d0c0'), [pp.line(rect(10, 10 + j * 64, 65, 56), 1.5, '#8a8478', 180) for j in range(3)]))
        p_.line(hv.quad(q), 1.5, LINE, 200)
    L += _lit(hv.d(D_ - 0.4), leaf, 'bd_door', _key('gp', 'bed', 'door', round(door, 2)), box, hv, amb, moon_l, var)

    def foot(pen, t):                                                     # the bed's foot and your blanket, out of focus
        pen.fill(smooth([(-200, 1180), (-200, 900), (500, 860), (1100, 880), (1700, 840), (2150, 920), (2150, 1180)], True, 0.5), '#2a2f4a')
        pen.fill(smooth([(-200, 1000), (600, 930), (1300, 960), (2150, 940), (2150, 1180), (-200, 1180)], True, 0.5), '#1e2238')
    L.append(Layer(0.5, foot, 'bd_foot', cache=_key('gp', 'bed', 'foot'), bounds=(-330, 700, 2250, 1310)))
    a = {'doorway': hv.anchor((DXa + DXb) / 2, D_ + 0.05, note='standing in the doorway, backlit'),
         'hall': hv.anchor((DXa + DXb) / 2, D_ + 0.8, note='in the hall beyond the door')}
    info = {'view': hv, 'hall': hf, 'cam_env': dict(x=(840, 1080), y=(460, 640), zoom=(1.0, 1.3), f=(1.0, 2.6))}
    return SetPiece('bedroom_doorway', L, a, {}, lens='lens', grade='gp_dark', focus=hv.d(D_), dof=1.4, cover=FRAME, info=info)


# ---------------------------------------------------------------------------------------------- the hospital room
MON = (1.05, 1.62, 3.15)                    # the heart monitor's screen centre (X, Y, D) in the hospital view


def ecg(t, bpm=72.0, flat=None):
    """The heart monitor's trace value at time t (-1..1): P wave, QRS spike, T wave; after `flat` it decays to a flat line."""
    if flat is not None and t >= flat: return 0.0
    ph = (t * bpm / 60.0) % 1.0
    v = 0.12 * math.exp(-((ph - 0.12) / 0.03) ** 2) - 0.15 * math.exp(-((ph - 0.24) / 0.008) ** 2) + 1.0 * math.exp(-((ph - 0.27) / 0.012) ** 2) \
        - 0.3 * math.exp(-((ph - 0.3) / 0.01) ** 2) + 0.25 * math.exp(-((ph - 0.5) / 0.05) ** 2)
    return v


def monitor_beeps(t0, t1, bpm=72.0, flat=None):
    """Beep times (each QRS spike) between t0 and t1 -> [t]; at `flat` the monitor's continuous alarm starts (the SFX
    names it 'monitor_flatline' at that time)."""
    P = 60.0 / bpm; out = []
    k = math.floor(t0 / P)
    while (k + 0.27) * P <= t1:
        tb = (k + 0.27) * P
        if tb >= t0 and (flat is None or tb < flat): out.append(round(tb, 3))
        k += 1
    return out


def _monitor_screen(pen, x, y, w, h, t, bpm=72.0, flat=None, k=1.0):
    """The bedside monitor's screen (live): green ECG sweep, HR, SpO2, blood pressure; red alarm text when flat."""
    pen.fill(rrect(x, y, w, h, h * 0.04), '#020806')
    sweep = 2.4
    n = 90
    pts = []
    tn = t
    xs = ((tn / sweep) % 1.0) * w
    for i in range(n + 1):
        u = i / n; xx = x + u * w
        age = (xs - u * w) / w
        if age < 0: age += 1.0
        tt = tn - age * sweep
        pts.append((xx, y + h * 0.36 - ecg(tt, bpm, flat) * h * 0.22, age))
    for i in range(n):
        a = clamp(1.0 - pts[i][2] * 1.1) * 255 * k
        if pts[i][2] > 0.97 or a < 6: continue
        pen.seg(pts[i][:2], pts[i + 1][:2], max(1.0, h * 0.018), '#4aff7a', a)
    pen.fill(rect(x + xs, y + h * 0.05, w * 0.03, h * 0.62), '#020806')
    flatd = flat is not None and t >= flat
    hr = '0' if flatd else str(int(bpm + 2 * math.sin(t * 0.3)))
    text(pen.cv, hr, x + w * 0.86, y + h * 0.42, 900, h * 0.26, '#ff4a4a' if flatd else '#4aff7a', 255 * k, 0.0)
    text(pen.cv, 'HR', x + w * 0.86, y + h * 0.14, 800, h * 0.08, '#4aff7a', 200 * k, 0.1)
    text(pen.cv, '96', x + w * 0.2, y + h * 0.88, 900, h * 0.16, '#5ad0ff', 230 * k, 0.0)
    text(pen.cv, '118/74', x + w * 0.6, y + h * 0.88, 900, h * 0.14, '#ffd84a', 230 * k, 0.0)
    if flatd and (t * 2) % 1.0 < 0.6:
        text(pen.cv, 'ASYSTOLE', x + w * 0.4, y + h * 0.14, 900, h * 0.1, '#ff3a3a', 255 * k, 0.12)


def hospital(view='bed', bpm=72.0, flat=None, light=1.0, hall=1.0, blinds=0.5):
    """The hospital room at night (last week): pale mint walls, the bed with its head raised and a pale-blue blanket
    (Grandpa is the cast: anchor 'bed_head' (his head on the pillow), 'bed_lap' (the dummy on his lap), 'bed_hand'),
    the visitor chair beside it ('chair': where the nurses sat Mister Winks), the heart monitor on its wall arm with
    the live ECG (bpm; flat = the time it flatlines; monitor_beeps() gives the beep times), the IV pole, the window with
    half-open blinds (city lights), the privacy curtain, the reading light over the bed (light), the corridor light
    under the door (hall). view 'bed' (from the foot, across) | 'close' (tighter, lower: the wrist grab).
    lens 'lens', grade 'hospital'."""
    if view == 'close':
        hv = HView(980, 560, 1.25, -0.1, 0.4, 1)
    else:
        hv = HView(800, 520, 1.55, -0.25, 0.1, 1)
    lf, hf = _kfn(light, 81), _kfn(hall, 82)
    W_, D_, CH_ = 2.2, 4.2, 2.7
    BED = (-0.5, 0.5, 2.0, 4.05, 0.62)            # x0, x1, y0 (foot), y1 (head), mattress top
    box = FRAME
    amb = '#2c3e46'
    win_l = [(1.0, 1.6, D_, 2.4, '#7a9ad0', 0.8), (0.6, 0.7, 3.4, 1.8, '#7a9ad0', 0.4), (-1.2, 1.2, 2.6, 2.0, '#5a7a8a', 0.35)]
    mon_l = [(MON[0], MON[1], MON[2], 0.9, '#4aff8a', 0.55), (0.6, 0.8, 3.3, 0.9, '#4aff8a', 0.25)]
    read_l = [(0.0, 1.7, BED[3] - 0.1, 1.5, '#ffd8a8', 0.6), (0.0, BED[4], 3.3, 1.2, '#ffd8a8', 0.38, 0.6), (-1.1, 0.7, 2.7, 1.2, '#ffd8a8', 0.3)]
    hall_l = [(-W_, 0.0, 1.0, 1.6, '#d8e8e0', 0.5, 0.3)]
    var = [('reading', read_l, lf), ('hall', hall_l, hf)]

    def room(p_):
        def back_art(q, W, H):
            q.fill(rect(70, H - 160, 300, 26), '#c8d0cc'); q.line(rect(70, H - 160, 300, 26), 1.5, LINE, 200)       # headwall panel
            for i in range(5):
                q.fill(rrect(84 + i * 56, H - 154, 16, 14, 3), ('#e8e8e8', '#3a7a3a', '#e8e8e8', '#3a5aa8', '#e8e8e8')[i])
            q.fill(rect(150, H - 132, 3, 40), '#a8b0b0')
        def back_art2(q, W, H):
            back_art(q, W, H)
            q.fill(rect(20, H - 210, 70, 50), '#f2f4f2'); q.line(rect(20, H - 210, 70, 50), 1.5, '#8a9090')          # whiteboard
            text(q.cv, 'ROOM 412', 55, H - 198, 800, 5.5, '#2a4a8a', 230, 0.06)
            text(q.cv, 'NURSE: DANA', 55, H - 188, 700, 4.5, '#2a2a2a', 210, 0.04)
            text(q.cv, 'KEMP, WALTER', 55, H - 178, 700, 4.5, '#2a2a2a', 210, 0.04)
            text(q.cv, 'GOAL: REST', 55, H - 168, 700, 4.5, '#c83a3a', 210, 0.04)
            cx_, cy_ = 230, H - 225                                                                        # wall clock 11:40
            q.fill(oval(cx_, cy_, 13), '#f4f4f0'); q.line(oval(cx_, cy_, 13), 2.0, '#3a3a3a')
            q.seg((cx_, cy_), (cx_ - 5, cy_ - 9), 1.6, '#1a1a1a'); q.seg((cx_, cy_), (cx_ - 11, cy_ - 4), 1.0, '#1a1a1a')
        _hwall(p_, hv, (-W_, D_), (W_, D_), 0.0, CH_, '#a8c4b8', None, 'stripe', 0.0, holes=[(W_ + 0.55, 0.9, W_ + 1.75, 2.15)], art=back_art2,
               trim='#c8d4cc', base_h=0.1, seed=81)
        wq = hv.quad([(0.55, 2.15, D_ + 0.01), (1.75, 2.15, D_ + 0.01), (1.75, 0.9, D_ + 0.01), (0.55, 0.9, D_ + 0.01)]); b = wq.getBounds()
        p_.cv.save(); p_.cv.clipPath(wq, skia.ClipOp.kIntersect, True)
        p_.linear(wq, 0, b.top(), 0, b.bottom(), ['#0a1430', '#1a2a58'])
        rng = np.random.default_rng(8)
        for i in range(30):                                                  # city lights
            lx = b.left() + rng.uniform(0, 1) * b.width(); ly = b.top() + b.height() * rng.uniform(0.55, 0.95)
            p_.fill(rect(lx, ly, b.width() * 0.012, b.height() * 0.018), ('#ffd890', '#ffffff', '#ff9a5a')[i % 3], 200)
        p_.fill(rect(b.left(), b.top() + b.height() * 0.75, b.width(), b.height() * 0.25), '#0a0e1a', 160)
        nb = 16
        for i in range(nb):                                                  # blinds (half open: slats with gaps)
            yy = b.top() + b.height() * i / nb
            p_.fill(rect(b.left(), yy, b.width(), b.height() / nb * (0.35 + 0.6 * (1 - blinds))), '#c8ccc4')
            p_.fill(rect(b.left(), yy, b.width(), 1.2), '#ffffff', 90)
        p_.cv.restore()
        _hwall(p_, hv, (-W_, hv.hy + 0.35), (-W_, D_), 0.0, CH_, '#a8c4b8', None, 'stripe', 0.0, trim='#c8d4cc', base_h=0.1, seed=82)
        _hwall(p_, hv, (W_, hv.hy + 0.35), (W_, D_), 0.0, CH_, '#a8c4b8', None, 'stripe', 0.0, trim='#c8d4cc', base_h=0.1, seed=83)
        _hfloor(p_, hv, -W_, W_, hv.hy + 0.35, D_, 'checker', '#c8c4b4', '#b8b4a4')
        _hceil(p_, hv, -W_, W_, hv.hy + 0.35, D_, CH_, '#b8c0bc')
        # the privacy curtain on its track (left)
        for i in range(9):
            y0_ = 1.0 + i * 0.32
            cq = hv.quad([(-1.55, 2.45, y0_), (-1.55, 2.45, y0_ + 0.32), (-1.55, 0.25, y0_ + 0.32), (-1.55, 0.25, y0_)])
            p_.fill(cq, '#9ac0a8' if i % 2 else '#8ab498')
        p_.line(poly([hv.p(-1.55, 2.5, 1.0), hv.p(-1.55, 2.5, D_)], False), 3, '#d8dcd8')
    L = _lit(hv.d(D_), room, 'hp_room', _key('gp', 'hosp', view, 'room', blinds), box, hv, amb, win_l + mon_l, var)

    def furniture(p_):
        x0, x1, y0, y1, Ym = BED
        _hbox(p_, hv, x0 - 0.04, x1 + 0.04, 0.28, Ym - 0.12, y0, y1, '#d8dcd8', tex='grunge')                 # frame
        for (lx, ly) in ((x0, y0 + 0.05), (x1, y0 + 0.05)):
            p_.seg(hv.p(lx, 0.0, ly), hv.p(lx, 0.3, ly), max(2.0, 0.025 * hv.s(ly)), '#8a9090')
        hb = hv.quad([(x0 - 0.05, 1.2, y1), (x1 + 0.05, 1.2, y1), (x1 + 0.05, 0.3, y1), (x0 - 0.05, 0.3, y1)]); p_.fill(hb, '#c8ccc8'); p_.line(hb, 1.5, LINE, 200)
        mt = [(x0, Ym, y0), (x1, Ym, y0), (x1, Ym, y1 - 0.8), (x0, Ym, y1 - 0.8)]
        p_.fill(hv.quad(mt), '#e8eceb')
        bk = hv.quad([(x0, Ym, y1 - 0.8), (x1, Ym, y1 - 0.8), (x1, Ym + 0.55, y1 - 0.1), (x0, Ym + 0.55, y1 - 0.1)]); p_.fill(bk, '#e4e8e6')     # raised back
        pl = hv.quad([(x0 + 0.08, Ym + 0.6, y1 - 0.12), (x1 - 0.08, Ym + 0.6, y1 - 0.12), (x1 - 0.08, Ym + 0.32, y1 - 0.42), (x0 + 0.08, Ym + 0.32, y1 - 0.42)])
        p_.fill(pl, '#d8dcd8'); p_.line(pl, 1.2, LINE, 160)
        for sx_ in (x0 - 0.07, x1 + 0.07):                                    # side rails
            for Yr in (Ym + 0.12, Ym + 0.3):
                p_.line(poly([hv.p(sx_, Yr, y1 - 1.35), hv.p(sx_, Yr, y1 - 0.35)], False), max(1.5, 0.018 * hv.s(y1 - 0.8)), '#a8b0b4')
            for yy in (y1 - 1.3, y1 - 0.4):
                p_.seg(hv.p(sx_, Ym + 0.05, yy), hv.p(sx_, Ym + 0.3, yy), max(1.5, 0.018 * hv.s(yy)), '#a8b0b4')
        cq = hv.quad([(-0.14, Ym + 0.06, y0 - 0.03), (0.14, Ym + 0.06, y0 - 0.03), (0.14, Ym - 0.3, y0 - 0.03), (-0.14, Ym - 0.3, y0 - 0.03)])
        p_.fill(cq, '#8a6a3a'); p_.fill(hv.quad([(-0.12, Ym + 0.02, y0 - 0.035), (0.12, Ym + 0.02, y0 - 0.035), (0.12, Ym - 0.28, y0 - 0.035), (-0.12, Ym - 0.28, y0 - 0.035)]), '#f0ece0')
        bl = smooth([hv.p(x0 - 0.06, Ym + 0.04, y0 - 0.02), hv.p(x1 + 0.06, Ym + 0.04, y0 - 0.02), hv.p(x1 + 0.08, Ym + 0.1, y1 - 0.9), hv.p(x0 - 0.08, Ym + 0.1, y1 - 0.9)], True, 0.25)
        p_.fill(bl, '#8aa8c8'); p_.texture(bl, 'fabric', 0.6, 'overlay', 1.0)
        fq = hv.quad([(x0 - 0.06, Ym + 0.04, y0 - 0.02), (x1 + 0.06, Ym + 0.04, y0 - 0.02), (x1 + 0.06, 0.32, y0 - 0.02), (x0 - 0.06, 0.32, y0 - 0.02)])
        p_.fill(fq, '#7a98b8'); p_.line(bl, 1.4, LINE, 200)
        rail = [hv.p(x1 + 0.08, Ym + 0.28, y) for y in (y1 - 1.3, y1 - 0.3)]
        p_.line(poly(rail, False), max(2.0, 0.025 * hv.s(y1 - 0.8)), '#b8c0c4')
        # visitor chair (left of the bed): vinyl, steel
        _hbox(p_, hv, -1.35, -0.85, 0.0, 0.45, 2.55, 3.0, '#4a6a7a', top='#5a7a8a')
        _hbox(p_, hv, -1.35, -0.85, 0.45, 0.95, 2.98, 3.06, '#4a6a7a')
        # IV pole + bag (right of the bed's head)
        ix, iy = hv.p(0.85, 0.0, 3.55); s = hv.s(3.55)
        p_.seg((ix, iy), (ix, iy - 1.9 * s), max(1.5, 0.012 * s), '#c8ccd0')
        p_.fill(rrect(ix + 0.02 * s, iy - 1.85 * s, 0.12 * s, 0.2 * s, 0.03 * s), '#d8e8f0', 200); p_.line(rrect(ix + 0.02 * s, iy - 1.85 * s, 0.12 * s, 0.2 * s, 0.03 * s), 1.0, LINE, 160)
        p_.line(smooth([(ix + 0.08 * s, iy - 1.65 * s), (ix + 0.02 * s, iy - 1.2 * s), (ix - 0.25 * s, iy - 0.9 * s)], False), max(0.8, 0.004 * s), '#e8f0f0', 180)
        # monitor on its arm
        mx, my = hv.p(MON[0], MON[1], MON[2]); ms = hv.s(MON[2])
        p_.seg(hv.p(1.45, 1.9, D_), (mx + 0.1 * ms, my - 0.1 * ms), max(2.0, 0.025 * ms), '#a8b0b4')
        p_.fill(rrect(mx - 0.22 * ms, my - 0.16 * ms, 0.44 * ms, 0.32 * ms, 0.02 * ms), '#3a4044'); p_.line(rrect(mx - 0.22 * ms, my - 0.16 * ms, 0.44 * ms, 0.32 * ms, 0.02 * ms), 1.5, LINE)
        # the over-bed reading light
        lx, ly = hv.p(0.0, 2.05, BED[3] - 0.05); ls = hv.s(BED[3] - 0.05)
        p_.fill(rrect(lx - 0.35 * ls, ly - 0.04 * ls, 0.7 * ls, 0.08 * ls, 0.02 * ls), '#d8dcd8'); p_.line(rrect(lx - 0.35 * ls, ly - 0.04 * ls, 0.7 * ls, 0.08 * ls, 0.02 * ls), 1.2, LINE)
    L += _lit(hv.d(3.0), furniture, 'hp_bed', _key('gp', 'hosp', view, 'bed'), box, hv, amb, win_l + mon_l, var)
    mx, my = hv.p(MON[0], MON[1], MON[2]); ms = hv.s(MON[2])
    L.append(Layer(hv.d(3.0) - 0.05, lambda pen, t: (_monitor_screen(pen, mx - 0.2 * ms, my - 0.14 * ms, 0.4 * ms, 0.28 * ms, t, bpm, flat),
                                                       pen.glow(mx, my, 0.5 * ms, '#4aff8a', 26)), 'hp_monitor', blur=None))
    lx, ly = hv.p(0.0, 2.05, BED[3] - 0.05); ls = hv.s(BED[3] - 0.05)
    L.append(Layer(hv.d(BED[3] - 0.05) - 0.01, lambda pen, t: (pen.fill(rect(lx - 0.33 * ls, ly + 0.02 * ls, 0.66 * ls, 0.02 * ls), mix('#6a6a64', '#fff8e8', lf(t))),
                                                              pen.glow(lx, ly + 0.05 * ls, 0.6 * ls, '#ffe8c8', 90 * lf(t))), 'hp_light', blur=None))
    x0, x1, y0, y1, Ym = BED
    a = {'bed_head': hv.anchor(0.0, y1 - 0.35, Ym + 0.45, 'his head on the pillow (raised back)'),
         'bed_lap': hv.anchor(0.0, y1 - 1.05, Ym + 0.12, 'on the blanket over his lap'),
         'bed_hand': hv.anchor(-0.4, y1 - 1.0, Ym + 0.15, 'his left hand on the blanket'),
         'chair': hv.anchor(-1.1, 2.78, 0.47, 'the visitor chair seat'), 'bedside': hv.anchor(-0.85, 2.3, note='standing at the bed\'s left side'),
         'door': hv.anchor(-1.9, 0.9, note='coming in (the door is behind the camera, left)')}
    info = {'view': hv, 'reading': lf, 'hall': hf, 'bpm': bpm, 'flat': flat, 'cam_env': dict(x=(840, 1100), y=(440, 620), zoom=(1.0, 1.3), f=(1.0, 2.4))}
    return SetPiece('hospital', L, a, {}, lens='lens', grade='hospital', focus=hv.d(y1 - 0.6), dof=1.2, cover=FRAME, info=info)


# ---------------------------------------------------------------------------------------------- the museum
MUS_CASE = (0.0, 6.0)                   # the vitrine on its plinth (x, y on the gallery plan)


def _plaque_art(p_, W, H):
    """The black plaque with brass edge (W x H cm frame)."""
    p_.fill(rect(0, 0, W, H), '#c9a24a'); p_.fill(rect(1.2, 1.2, W - 2.4, H - 2.4), '#141416')
    cv = p_.cv
    text(cv, 'MISTER WINKS', W / 2, H * 0.3, 900, H * 0.17, '#e8dcc0', 255, 0.12)
    text(cv, 'Ventriloquist figure  •  carved and painted wood  •  c. 1958', W / 2, H * 0.52, 700, H * 0.075, '#c8bca0', 255, 0.04)
    text(cv, 'Performed with Walter Kemp for sixty years.', W / 2, H * 0.68, 700, H * 0.075, '#c8bca0', 255, 0.04)
    text(cv, 'Gift of the Kemp family', W / 2, H * 0.86, 600, H * 0.065, '#8a8270', 255, 0.06)


def _vitrine_art(pen, hv, part='plinth'):
    """The museum case: a charcoal plinth with the plaque (part 'plinth'), the little red velvet chair inside and the
    case's back panel (part 'inside'), the glass box's edges and reflections (part 'glass', in front of the dummy)."""
    cx, cy = MUS_CASE
    px0, px1, py0, py1, PH = cx - 0.55, cx + 0.55, cy - 0.32, cy + 0.32, 0.95
    if part == 'plinth':
        _hbox(pen, hv, px0, px1, 0.0, PH, py0, py1, '#2a2c30', top='#3a3c42', tex='grunge')
        _hface(pen, hv, (cx - 0.3, 0.74, py0 - 0.003), (cx + 0.3, 0.74, py0 - 0.003), (cx + 0.3, 0.5, py0 - 0.003), (cx - 0.3, 0.5, py0 - 0.003), 60, 24,
               lambda q: _plaque_art(q, 60, 24))
        return
    gx0, gx1, gy0, gy1, GT = cx - 0.5, cx + 0.5, cy - 0.27, cy + 0.27, PH + 1.05
    if part == 'inside':
        bq = hv.quad([(gx0, GT, gy1), (gx1, GT, gy1), (gx1, PH, gy1), (gx0, PH, gy1)])
        pen.fill(bq, '#3a1418'); pen.texture(bq, 'fabric', 0.6, 'overlay', 0.8)
        fq = hv.quad([(gx0, PH + 0.005, gy1), (gx1, PH + 0.005, gy1), (gx1, PH + 0.005, gy0), (gx0, PH + 0.005, gy0)])
        pen.fill(fq, '#5a1a20'); pen.texture(fq, 'fabric', 0.7, 'overlay', 0.8)
        # the small velvet chair he sits in
        _hbox(pen, hv, cx - 0.17, cx + 0.17, PH, PH + 0.2, cy - 0.05, cy + 0.2, '#7a1a24', top='#9a2a32', tex='fabric')
        _hbox(pen, hv, cx - 0.17, cx + 0.17, PH + 0.2, PH + 0.62, cy + 0.17, cy + 0.22, '#7a1a24', tex='fabric')
        for sx in (-1, 1):
            _hbox(pen, hv, cx + sx * 0.17 - (0.04 if sx > 0 else 0.0), cx + sx * 0.17 + (0.0 if sx > 0 else 0.04), PH + 0.2, PH + 0.36, cy - 0.05, cy + 0.2, '#6a141c')
        return
    # glass: the box edges (bright hairlines), reflections, the spot's hot reflection on the top front edge
    s = hv.s(gy0)
    corners = [(gx0, GT, gy0), (gx1, GT, gy0), (gx1, PH, gy0), (gx0, PH, gy0)]
    fq = hv.quad(corners); b = fq.getBounds()
    pen.fill(fq, '#a8c0d0', 14)
    pen.cv.save(); pen.cv.clipPath(fq, skia.ClipOp.kIntersect, True)
    for (u, w, a) in ((0.1, 0.08, 34), (0.22, 0.025, 26), (0.68, 0.05, 22)):
        x0_ = b.left() + b.width() * u
        pen.fill(poly([(x0_, b.bottom()), (x0_ + b.width() * w, b.bottom()), (x0_ + b.width() * (w + 0.45), b.top()), (x0_ + b.width() * 0.45, b.top())]), '#ffffff', a)
    pen.linear(fq, 0, b.top(), 0, b.bottom(), [(0, '#ffffff', 30), (0.25, '#ffffff', 0), (1, '#ffffff', 10)])
    pen.cv.restore()
    for (a_, b_) in ((corners[0], corners[1]), (corners[1], corners[2]), (corners[0], corners[3]), ((gx0, GT, gy1), (gx1, GT, gy1)),
                     ((gx0, GT, gy0), (gx0, GT, gy1)), ((gx1, GT, gy0), (gx1, GT, gy1)), ((gx1, PH, gy0), (gx1, PH, gy1))):
        pen.seg(hv.p(*a_), hv.p(*b_), max(1.0, 0.004 * s), '#e8f4ff', 150)
    tx, ty = hv.p(cx - 0.12, GT, gy0)
    pen.glow(tx, ty, 0.08 * s, '#ffffff', 160)


def museum(view='case', spot=1.0):
    """The museum, three states away: a hushed dark-teal gallery. Mister Winks sits behind glass in a vitrine on a
    charcoal plinth (a little red velvet chair, red velvet backing), lit by one warm spotlight from above; the plaque
    (MISTER WINKS, c. 1958, 'Performed with Walter Kemp for sixty years', Gift of the Kemp family); behind, a big
    1974 show poster and the wall title. view 'case' (close on the vitrine; anchor 'display' = his seat, depth inside
    the glass; the glass is its own layer IN FRONT of him with edges and reflections) | 'wide' (the gallery: velvet rope,
    a bench, other cases, a visitor's spot). lens 'lens', grade 'museum'."""
    if view == 'wide':
        hv = HView(760, 480, 1.6, 0.3, 1.6, 1)
    else:
        hv = HView(1250, 470, 1.45, 0.0, 3.2, 1)
    sf = _kfn(spot, 91)
    cx, cy = MUS_CASE
    box = FRAME
    amb = '#1c262c'
    spot_l = [(cx, 1.5, cy, 1.0, '#fff0d8', 1.0), (cx, 0.95, cy - 0.3, 0.8, '#fff0d8', 0.8), (cx, 0.0, cy - 0.9, 1.6, '#fff0d8', 0.6, 0.3),
              (cx, 1.4, 9.0, 3.0, '#f0e0c8', 0.45)]
    const = [(-2.4, 1.8, 9.0, 1.8, '#f0dcc0', 0.55), (2.15, 1.7, 9.0, 1.6, '#f0dcc0', 0.6), (0.0, 2.55, 9.0, 1.6, '#f0dcc0', 0.45),
             (-2.6, 1.3, 7.2, 1.2, '#f0dcc0', 0.6), (2.8, 1.3, 6.6, 1.2, '#f0dcc0', 0.6), (0.0, 0.0, 4.0, 3.0, '#8ab0c0', 0.25, 0.3)]
    var = [('spot', spot_l, sf)]

    def room(p_):
        def back_art(q, W, H):
            _hframe(q, W, H, 555, H - 250, 120, 160, 'poster', frame='#1a1a1a', fn=lambda p2, w, h: _poster_art(p2, w, h, '1974'))
            text(q.cv, 'WALTER KEMP & MISTER WINKS', 400, H - 262, 900, 17, '#f0f4f4', 240, 0.12)
            text(q.cv, 'SIXTY YEARS OF SATURDAY MORNINGS', 400, H - 246, 800, 9, '#b8c8c8', 230, 0.2)
            _hframe(q, W, H, 150, H - 220, 56, 74, 'photo', seed=91); _hframe(q, W, H, 230, H - 205, 44, 58, 'photo', seed=92)
        _hwall(p_, hv, (-4.0, 9.0), (4.0, 9.0), 0.0, 3.4, '#22383e', '#1a2c32', 'stripe', 0.0, art=back_art, pa=40, trim='#101618', base_h=0.12, seed=91)
        _hwall(p_, hv, (-4.0, hv.hy + 0.4), (-4.0, 9.0), 0.0, 3.4, '#22383e', None, 'stripe', 0.0, trim='#101618', seed=92)
        _hwall(p_, hv, (4.0, hv.hy + 0.4), (4.0, 9.0), 0.0, 3.4, '#22383e', None, 'stripe', 0.0, trim='#101618', seed=93)
        _hfloor(p_, hv, -4.0, 4.0, hv.hy + 0.4, 9.0, 'boards', '#3a2a20', '#22180f')
        _hceil(p_, hv, -4.0, 4.0, hv.hy + 0.4, 9.0, 3.4, '#101418')
        for (vx, vy) in ((-2.6, 7.2), (2.8, 6.6)):                         # other cases: a 70s TV camera, a ribbon microphone
            _hbox(p_, hv, vx - 0.4, vx + 0.4, 0.0, 0.9, vy - 0.3, vy + 0.3, '#2a2c30', top='#3a3c42')
            gq = hv.quad([(vx - 0.38, 1.7, vy - 0.28), (vx + 0.38, 1.7, vy - 0.28), (vx + 0.38, 0.9, vy - 0.28), (vx - 0.38, 0.9, vy - 0.28)])
            p_.fill(gq, '#a8c0d0', 20); p_.line(gq, 1.0, '#c8e0f0', 90)
            ox, oy = hv.p(vx, 1.15, vy); os_ = hv.s(vy)
            if vx < 0:
                p_.fill(rrect(ox - 0.18 * os_, oy - 0.12 * os_, 0.3 * os_, 0.2 * os_, 0.02 * os_), '#3a3a40'); p_.fill(oval(ox + 0.16 * os_, oy - 0.02 * os_, 0.06 * os_), '#1a1a1e')
            else:
                p_.fill(rrect(ox - 0.05 * os_, oy - 0.2 * os_, 0.1 * os_, 0.14 * os_, 0.03 * os_), '#b8bcc4'); p_.seg((ox, oy - 0.06 * os_), (ox, oy + 0.25 * os_), max(1.0, 0.01 * os_), '#8a8e94')
        if view == 'wide':
            for sx in (-1.3, 1.3):                                               # stanchions and the velvet rope
                a_, b_ = hv.p(sx, 0.0, 4.6), hv.p(sx, 0.95, 4.6)
                p_.seg(a_, b_, max(2.0, 0.03 * hv.s(4.6)), '#c9a24a'); p_.fill(oval(b_[0], b_[1], 0.035 * hv.s(4.6)), '#e8c860')
            rp = [hv.p(x, 0.9 - 0.18 * (1 - (x / 1.3) ** 2), 4.6) for x in np.linspace(-1.3, 1.3, 12)]
            p_.line(poly(rp, False), max(2.5, 0.03 * hv.s(4.6)), '#8a1a24')
            _hbox(p_, hv, -1.0, 1.0, 0.0, 0.45, 2.4, 2.8, '#2a1a10', top='#4a2e1a', tex='wood')
    L = _lit(hv.d(9.0), room, 'mu_room', _key('gp', 'mus', view, 'room'), box, hv, amb, const, var)
    L += _lit(hv.d(cy + 0.3), lambda p_: _vitrine_art(p_, hv, 'inside'), 'mu_inside', _key('gp', 'mus', view, 'inside'), box, hv, amb, const, var)
    L += _lit(hv.d(cy - 0.32), lambda p_: _vitrine_art(p_, hv, 'plinth'), 'mu_plinth', _key('gp', 'mus', view, 'plinth'), box, hv, amb, const, var)
    L.append(Layer(hv.d(cy - 0.28), lambda pen, t: _vitrine_art(pen, hv, 'glass'), 'mu_glass', cache=_key('gp', 'mus', view, 'glass'), bounds=box, blur=0))

    def spot_cone(pen, t):
        k = sf(t)
        if k < 0.02: return
        a_ = hv.p(cx - 0.12, 3.4, cy); b_ = hv.p(cx + 0.12, 3.4, cy)
        c_ = hv.p(cx + 0.55, 0.95, cy); d_ = hv.p(cx - 0.55, 0.95, cy)
        cone = poly([a_, b_, c_, d_])
        pen.linear(cone, 0, a_[1], 0, c_[1], [(0, '#fff2d8', 40 * k), (1, '#fff2d8', 8 * k)])
    L.append(Layer(hv.d(cy) - 0.01, spot_cone, 'mu_spot', blur=0))
    a = {'display': hv.anchor(cx, cy + 0.06, 0.95 + 0.2, 'seated on the little chair inside the case (seat height)'),
         'visitor': hv.anchor(0.6, 4.2, note='a visitor at the rope'), 'plaque': hv.anchor(cx, cy - 0.33, 0.62, 'the plaque')}
    info = {'view': hv, 'spot': sf, 'cam_env': dict(x=(860, 1060), y=(440, 640), zoom=(1.0, 1.25), f=(1.0, 2.4))}
    return SetPiece('museum', L, a, {}, lens='lens', grade='museum', focus=hv.d(cy), dof=1.0 if view == 'case' else 0.6, cover=FRAME, info=info)


# ---------------------------------------------------------------------------------------------- the museum van, the morning street
def _mvan_body(pen, s, facing):
    """The museum's van: a clean white high-roof van, a burgundy band, gold lettering (static sprite art)."""
    cv = pen.cv
    cv.save()
    if facing > 0: cv.scale(-1, 1)
    lw = max(1.2, 0.035 * s)

    def P(a, b): return (a * s, -b * s)
    body = _van_profile(s)
    pen.linear(body, 0, -2.55 * s, 0, -0.3 * s, ['#f2f0ea', '#e2dfd6', '#b8b4a8'])
    cv.save(); cv.clipPath(body, skia.ClipOp.kIntersect, True)
    pen.fill(rect(-3.1 * s, -1.2 * s, 6.2 * s, 0.22 * s), '#6a1a24'); pen.fill(rect(-3.1 * s, -1.2 * s, 6.2 * s, 0.03 * s), '#c9a24a')
    cvt = cv; cvt.save()
    if facing > 0: cvt.scale(-1, 1)
    fx = -1 if facing > 0 else 1
    lx = (1.15 if fx > 0 else -1.15) * s
    text(cvt, 'MERIDIAN MUSEUM', lx, -1.75 * s, 900, 0.32 * s, '#6a1a24', 255, 0.06)
    text(cvt, 'of STAGE & SCREEN', lx, -1.42 * s, 700, 0.18 * s, '#8a6a2a', 255, 0.2)
    text(cvt, 'FINE ART TRANSPORT', lx, -0.72 * s, 800, 0.13 * s, '#4a4a48', 230, 0.3)
    cvt.restore()
    pen.linear(rect(-3.1 * s, -0.8 * s, 6.2 * s, 0.5 * s), 0, -0.8 * s, 0, -0.3 * s, [(0, '#5a5048', 0), (1, '#5a5048', 110)])
    cv.restore()
    sc = '#8a867c'
    pen.line(poly([P(-2.05, 0.42), P(-2.05, 1.36), P(-1.6, 2.24), P(-0.62, 2.24), P(-0.62, 0.42)]), lw * 0.6, sc, 220)
    pen.line(rrect(-0.53 * s, -2.27 * s, 1.4 * s, 1.85 * s, 0.05 * s), lw * 0.6, sc, 200)
    pen.fill(poly([P(-2.22, 1.3), P(-1.66, 2.26), P(-1.55, 2.26), P(-2.06, 1.37)]), '#2a3446')
    win = poly([P(-1.95, 1.44), P(-1.53, 2.13), P(-0.74, 2.13), P(-0.74, 1.44)])
    pen.linear(win, 0, -2.13 * s, 0, -1.44 * s, ['#8a9ab0', '#3a4458'])
    hx, hy = -1.12, 1.84
    pen.fill(union(oval(*P(hx, hy), 0.12 * s, 0.15 * s), rrect(*P(hx - 0.3, 1.66), 0.62 * s, 0.4 * s, 0.12 * s)), '#1a1c22', 230)
    pen.line(win, lw * 0.8, '#05060a')
    pen.fill(rrect(*P(-0.96, 1.29), 0.2 * s, 0.06 * s, 0.025 * s), '#5a5a58')
    pen.shape(rrect(*P(-2.34, 1.88), 0.2 * s, 0.42 * s, 0.05 * s), '#24262b', lw * 0.6)
    pen.fill(rect(*P(-0.5, 0.36), 1.36 * s, 0.07 * s), '#1a1b1e')
    pen.shape(rrect(*P(-3.04, 0.62), 0.42 * s, 0.32 * s, 0.06 * s), '#3a3c40', lw * 0.6)
    pen.shape(rrect(*P(2.72, 0.5), 0.33 * s, 0.22 * s, 0.05 * s), '#3a3c40', lw * 0.6)
    pen.line(body, lw, LINE)
    for wx in (-1.92, 1.8): pen.fill(oval(*P(wx, 0.36), 0.49 * s), '#050607')
    cv.restore()


def museum_van(pen, x, y, length, t=0.0, facing=1, wheel=0.0, bounce=0.0, brake=False):
    """The museum van in side view ((x, y) = centre between the wheels on the ground; facing +1 = nose right): body
    sprite, live wheels and brake lights."""
    s = length / VAN_LEN
    cv = pen.cv
    pen.radial(None, x, y + 0.04 * s, 3.5 * s, [(0, '#000000', 150), (0.75, '#000000', 90), (1, '#000000', 0)], sy=0.09, clip=False)
    cv.save(); cv.translate(x, y + bounce)
    _sprite(pen, ('mvan', facing), lambda p_: _mvan_body(p_, _VAN_S, facing), (-3.25 * _VAN_S, -2.75 * _VAN_S, 3.25 * _VAN_S, 0.1 * _VAN_S), scale=s / _VAN_S)
    if facing > 0: cv.scale(-1, 1)
    for wx in (-1.92, 1.8):
        cx_, cy_ = wx * s, -0.36 * s
        pen.fill(oval(cx_, cy_, 0.38 * s), '#08090b'); pen.fill(oval(cx_, cy_, 0.24 * s), '#9aa0a8')
        for k in range(6):
            a = math.radians(-wheel + k * 60)
            pen.fill(oval(cx_ + math.cos(a) * 0.14 * s, cy_ + math.sin(a) * 0.14 * s, 0.03 * s), '#3a3c40')
        pen.fill(oval(cx_, cy_, 0.06 * s), '#d0d4d8')
    pen.fill(rrect(2.9 * s, -1.5 * s, 0.09 * s, 0.38 * s, 0.02 * s), '#ff3a2a' if brake else '#7a1a14')
    cv.restore()
    if brake:
        F = 1 if facing > 0 else -1
        pen.glow(x - F * 2.95 * s, y + bounce - 1.3 * s, 0.7 * s, '#ff3020', 140)


def _van_drive(drive, t):
    """drive = ('out', t0, t1, x0, x1) (eases off from x0 to x1) -> (x, moving, wheel deg)."""
    if not drive: return None
    mode, t0, t1, x0, x1 = drive
    u = clamp((t - t0) / max(1e-6, t1 - t0))
    e = u * u if mode == 'out' else ease_in_out(u)
    x = lerp(x0, x1, e)
    return x, (0 < u < 1), (x - x0) / 0.36 * 57.3


def _street_morning_far(pen, hv, facing=-1):
    """The street in grey 8 AM light as seen from Grandpa's front window / from across it: sky, the houses opposite,
    autumn trees, sidewalk, the road."""
    def P(x, Y, y): return hv.p(x, Y, y)
    yfar = -16.0 if facing < 0 else 16.0
    sky = rect(-400, -300, 2720, 1100)
    pen.linear(sky, 0, -300, 0, hv.y(0.0, yfar) + 40, ['#9aaac0', '#c8d0d8', '#e2e2dc'])
    for i, hx in enumerate(range(-22, 18, 8)):
        x0 = hx; w = 6.5
        c = ('#a8968a', '#8a9aa0', '#b4a890', '#9a8a98', '#a0a890')[i % 5]
        hb = hv.quad([(x0, 0.0, yfar), (x0 + w, 0.0, yfar), (x0 + w, 5.6, yfar), (x0, 5.6, yfar)])
        pen.fill(hb, c); _siding(pen, hb, *_rb(hb), 6, '#000000', 30)
        pen.fill(hv.quad([(x0 - 0.3, 5.6, yfar), (x0 + w / 2, 7.6, yfar), (x0 + w + 0.3, 5.6, yfar)]), '#4a3e3a')
        for (wx, wy) in ((x0 + 1.2, 1.2), (x0 + 4.2, 1.2), (x0 + 1.2, 3.6), (x0 + 4.2, 3.6)):
            q = hv.quad([(wx, wy + 1.2, yfar), (wx + 1.0, wy + 1.2, yfar), (wx + 1.0, wy, yfar), (wx, wy, yfar)])
            pen.fill(q, '#4a5260'); pen.line(q, 2, '#e8e4dc')
    for (tx, tc) in ((-14.0, '#c86a2a'), (-3.0, '#d8a03a'), (9.0, '#b8502a')):
        bx, by = hv.p(tx, 0.0, yfar * 0.8); s = hv.s(yfar * 0.8)
        pen.fill(rect(bx - 0.18 * s, by - 3.2 * s, 0.36 * s, 3.2 * s), '#3a2a20')
        for k in range(6):
            pen.fill(oval(bx + (k - 2.5) * 0.7 * s, by - (3.6 + 0.8 * (k % 2)) * s, 1.4 * s, 1.1 * s), mix(tc, '#e8b860', 0.15 * (k % 3)), 235)
    pen.fill(hv.quad([(-40, 0.0, yfar), (40, 0.0, yfar), (40, 0.0, yfar * 0.62), (-40, 0.0, yfar * 0.62)]), '#9a9a8e')
    pen.fill(hv.quad([(-40, 0.0, yfar * 0.62), (40, 0.0, yfar * 0.62), (40, 0.0, yfar * 0.24), (-40, 0.0, yfar * 0.24)]), '#5a5c60')
    pen.fill(hv.quad([(-40, 0.0, yfar * 0.43 - 0.06), (40, 0.0, yfar * 0.43 - 0.06), (40, 0.0, yfar * 0.43 + 0.06), (-40, 0.0, yfar * 0.43 + 0.06)]), '#d8c86a', 160)
    pen.fill(hv.quad([(-40, 0.0, yfar * 0.24), (40, 0.0, yfar * 0.24), (40, 0.0, yfar * 0.16), (-40, 0.0, yfar * 0.16)]), '#a8a89c')
    pen.fill(hv.quad([(-40, 0.0, yfar * 0.16), (40, 0.0, yfar * 0.16), (40, 0.0, yfar * 0.01), (-40, 0.0, yfar * 0.01)]), '#6a7a4a')


def street_morning(view='window', van=None, owen=True):
    """8 AM: the museum van takes him. view 'window': from inside the living room behind the couch, the front window
    (drapes open, grey morning) with the street outside; Owen stands at the glass (anchor 'owen', seen from behind) and
    waves as the van pulls away (van = dict(drive=('out', t0, t1, x0, x1)) on the house plan (x decreasing = to the right
    of frame); default parked at the curb). view 'outside': across the street, Grandpa's house (siding, white trim,
    the porch, the living-room window: anchor 'owen_window' is Owen inside the glass waving: draw him BEFORE the
    'so_glass' layer's reflections). lens 'lens', grade 'morning'."""
    vs = dict(drive=None, x=-5.5); vs.update(van or {})
    if view == 'outside':
        return _street_outside(vs)
    hv = HView(820, 500, 1.6, -3.7, 4.3, -1)
    box = FRAME
    amb = '#7a808c'
    day = [(-3.7, 1.4, 0.0, 3.6, '#f4f2ec', 0.85), (-3.7, 0.0, 1.0, 2.6, '#f4f2ec', 0.5, 0.35), (-3.7, 0.9, 1.6, 1.8, '#f4f2ec', 0.45)]

    def outside(p_):
        _street_morning_far(p_, hv, -1)
    L = [Layer(hv.d(-16.0), lambda pen, t: outside(pen), 'sm_street', cache=_key('gp', 'sm', 'street'), bounds=box, ref_depth=hv.d(-16.0))]
    vY = -7.0

    def van_layer(pen, t):
        dv = _van_drive(vs['drive'], t)
        x = dv[0] if dv else vs['x']
        wheel = dv[2] if dv else 0.0
        px, py = hv.p(x, 0.0, vY); s = hv.s(vY)
        museum_van(pen, px, py, VAN_LEN * s, t, -1, wheel, 0.0, brake=bool(dv and not dv[1] and t < vs['drive'][1]))
    L.append(Layer(hv.d(vY), van_layer, 'sm_van', blur=None))

    def room(p_):
        _hwall(p_, hv, (LIV_X[1], 0.0), (LIV_X[0], 0.0), 0.0, CEIL, LIV_PAPER, LIV_INK, 'trellis', 0.9,
               holes=[(LIV_X[1] - LWIN[1], 0.85, LIV_X[1] - LWIN[0], 2.1)], rail=2.25, seed=14, wc='#4a2e1a')
        for i in range(1, 3):
            xm = LWIN[0] + (LWIN[1] - LWIN[0]) * i / 3
            p_.seg(hv.p(xm, 2.1, 0.0), hv.p(xm, 0.85, 0.0), max(2.0, 0.03 * hv.s(0.0)), '#e8e0d0')
        p_.seg(hv.p(LWIN[0], 1.5, 0.0), hv.p(LWIN[1], 1.5, 0.0), max(2.0, 0.03 * hv.s(0.0)), '#e8e0d0')
        sl = hv.quad([(LWIN[0] - 0.08, 0.85, 0.0), (LWIN[1] + 0.08, 0.85, 0.0), (LWIN[1] + 0.08, 0.85, 0.16), (LWIN[0] - 0.08, 0.85, 0.16)])
        p_.fill(sl, '#e8e0d0'); p_.line(sl, 1.2, LINE, 200)
        _hwall(p_, hv, (LIV_X[0], 3.0), (LIV_X[0], 0.0), 0.0, CEIL, LIV_PAPER, LIV_INK, 'trellis', 0.9, rail=2.25, seed=15, wc='#4a2e1a')
        _hwall(p_, hv, (LIV_X[1], 0.0), (LIV_X[1], 3.0), 0.0, CEIL, LIV_PAPER, LIV_INK, 'trellis', 0.9, rail=2.25, seed=16, wc='#4a2e1a')
        _hfloor(p_, hv, LIV_X[0], LIV_X[1], 0.0, 3.0, 'carpet', '#5a5a36')
        _hceil(p_, hv, LIV_X[0], LIV_X[1], 0.0, 3.0, CEIL, '#8a8070')
        for side in (-1, 1):                                                    # drapes pulled open
            xo = LWIN[0] - 0.55 if side < 0 else LWIN[1] + 0.05
            a_ = hv.p(xo + 0.5, 2.25, 0.08); b_ = hv.p(xo, 2.25, 0.08)
            xs = sorted([a_[0], b_[0]]); top = a_[1]; h = hv.p(xo, 0.05, 0.08)[1] - top
            _curtain(p_, xs[0], top, xs[1] - xs[0], h, 0.0, side, '#b8562a', 0.0, 41 + side, folds=7)
        _bookcase_art(p_, hv)
    L += _lit(hv.d(0.0), room, 'sm_room', _key('gp', 'sm', 'room'), box, hv, amb, day, [])
    L += _lit(hv.d(1.9), lambda p_: _couch_art(p_, hv), 'sm_couch', _key('gp', 'sm', 'couch'), box, hv, amb, day, [])
    a = {'owen': hv.anchor(-3.7, 0.55, note='standing at the front window, his back to us'),
         'mom': hv.anchor(-2.6, 1.0, note='by the window, right'), 'van': hv.anchor(vs['x'], vY, note='the van at the curb')}
    info = {'view': hv, 'van': vs, 'cam_env': dict(x=(820, 1100), y=(430, 620), zoom=(1.0, 1.2), f=(1.0, 2.2))}
    return SetPiece('street_morning', L, a, {}, lens='lens', grade='morning', focus=hv.d(0.5), dof=0.8, cover=FRAME, info=info)


def _street_outside(vs):
    """Grandpa's house from across the street at 8 AM (see street_morning)."""
    hv = HView(1500, 520, 1.5, -2.6, -17.0, 1)
    box = FRAME
    amb = '#9aa0aa'
    day = [(-2.6, 3.0, 0.0, 9.0, '#f4f2ec', 0.5)]
    HX0, HX1 = -6.6, 1.8

    def far(pen):
        pen.linear(rect(box[0], box[1], box[2] - box[0], hv.gy(8.0) + 10 - box[1]), 0, box[1], 0, 700, ['#9aaac0', '#d0d6dc'])
        pen.fill(rect(box[0], hv.gy(8.0) - 4, box[2] - box[0], box[3] - hv.gy(8.0) + 4), '#7a8060')
        for (tx, c) in ((-11.0, '#c86a2a'), (6.0, '#d8a03a')):
            bx, by = hv.p(tx, 0.0, 6.0); s = hv.s(6.0)
            pen.fill(rect(bx - 0.2 * s, by - 3.5 * s, 0.4 * s, 3.5 * s), '#3a2a20')
            for k in range(7): pen.fill(oval(bx + (k - 3) * 0.8 * s, by - (4.2 + 0.9 * (k % 2)) * s, 1.6 * s, 1.3 * s), c, 235)
    L = [Layer(hv.d(8.0), lambda pen, t: far(pen), 'so_far', cache=_key('gp', 'so', 'far'), bounds=box)]

    def house(p_):
        def front_art(q, W, H):
            q.fill(rect(0, 0, W, H), '#9aaab8')
            y = 0.0
            while y < H:
                q.fill(rect(0, y, W, 1.2), '#000000', 40); q.fill(rect(0, y + 1.2, W, 1.0), '#ffffff', 40); y += 14
            for (wx0, wx1, wy0, wy1) in ((LWIN[0], LWIN[1], 0.85, 2.1), (-0.85 - 0.0, 0.05, 0.0, 2.1), (-4.4, -3.0, 3.6, 4.9), (-1.0, 0.2, 3.6, 4.9)):
                u0 = (wx0 - HX0) * 100; u1 = (wx1 - HX0) * 100
                q.fill(rect(u0 - 10, H - wy1 * 100 - 10, u1 - u0 + 20, (wy1 - wy0) * 100 + 20), '#f0ece4')
            q.fill(rect(0, 0, W, 10), '#f0ece4')
        _hwall(p_, hv, (HX0, 0.0), (HX1, 0.0), 0.0, 6.2, '#9aaab8', None, 'stripe', 0.0,
               holes=[(LWIN[0] - HX0, 0.85, LWIN[1] - HX0, 2.1), (-0.85 - HX0, 0.0, 0.05 - HX0, 2.1), (-4.4 - HX0, 3.6, -3.0 - HX0, 4.9), (-1.0 - HX0, 3.6, 0.2 - HX0, 4.9)],
               art=front_art, trim='#f0ece4', base_h=0.3, seed=95)
        ch = hv.quad([(HX1 - 1.6, 9.2, 0.3), (HX1 - 1.0, 9.2, 0.3), (HX1 - 1.0, 6.5, 0.3), (HX1 - 1.6, 6.5, 0.3)])
        p_.fill(ch, '#7a3a2a'); _bricks(p_, ch, *_rb(ch), 4, 9, '#000000', 50); p_.line(ch, 2, LINE)
        roof = hv.quad([(HX0 - 0.4, 6.2, 0.0), (HX1 + 0.4, 6.2, 0.0), ((HX0 + HX1) / 2, 8.6, 0.0)])
        p_.fill(roof, '#4a3e3a'); p_.texture(roof, 'grunge', 0.4, 'overlay', 1.0); p_.line(roof, 3, LINE)
        gw = hv.quad([((HX0 + HX1) / 2 - 0.4, 7.4, -0.01), ((HX0 + HX1) / 2 + 0.4, 7.4, -0.01), ((HX0 + HX1) / 2 + 0.4, 6.6, -0.01), ((HX0 + HX1) / 2 - 0.4, 6.6, -0.01)])
        p_.fill(gw, '#5a6070'); p_.line(gw, 3, '#f0ece4')
        for (wx0, wx1, wy0, wy1) in ((LWIN[0], LWIN[1], 0.85, 2.1), (-4.4, -3.0, 3.6, 4.9), (-1.0, 0.2, 3.6, 4.9)):
            for sx_, sw_ in ((wx0 - 0.42, 0.34), (wx1 + 0.08, 0.34)):
                sq = hv.quad([(sx_, wy1, -0.01), (sx_ + sw_, wy1, -0.01), (sx_ + sw_, wy0, -0.01), (sx_, wy0, -0.01)])
                p_.fill(sq, '#2a4a3a'); p_.line(sq, 1.2, LINE, 200)
        p_.fill(hv.quad([(HX0, 0.3, -0.01), (HX1, 0.3, -0.01), (HX1, 0.0, -0.01), (HX0, 0.0, -0.01)]), '#7a7068')
        for (wx0, wx1, wy0, wy1) in ((-4.4, -3.0, 3.6, 4.9), (-1.0, 0.2, 3.6, 4.9)):
            p_.fill(hv.quad([(wx0, wy1, 0.0), (wx1, wy1, 0.0), (wx1, wy0, 0.0), (wx0, wy0, 0.0)]), '#5a6070')
        p_.fill(hv.quad([(-0.85, 2.1, 0.0), (0.05, 2.1, 0.0), (0.05, 0.0, 0.0), (-0.85, 0.0, 0.0)]), '#4a2414')
        # porch: floor, columns, steps, railing
        _hbox(p_, hv, -1.6, 0.8, 0.0, 0.45, -1.8, 0.0, '#d8d4cc', top='#8a7a6a')
        for px_ in (-1.5, 0.7):
            _hbox(p_, hv, px_ - 0.08, px_ + 0.08, 0.45, 2.6, -1.78, -1.62, '#f0ece4')
        _hbox(p_, hv, -1.7, 0.9, 2.6, 2.85, -1.85, 0.0, '#f0ece4', top='#5a4e4a')
        for k in range(3): _hbox(p_, hv, -0.8, 0.0, 0.0, 0.15 * (3 - k), -1.8 - 0.28 * (k + 1), -1.8 - 0.28 * k, '#c8c4bc', top='#a89c8c')
        _hfloor(p_, hv, -9.0, 5.0, -4.2, 0.0, 'carpet', '#6a7a4a')
        _hfloor(p_, hv, -0.75, -0.05, -4.2, -2.6, 'carpet', '#b8b4a8')
        _hfloor(p_, hv, -12.0, 8.0, -5.6, -4.2, 'carpet', '#a8a89c')
        _hfloor(p_, hv, -14.0, 10.0, -13.0, -5.6, 'carpet', '#5a5c60')
        mx, my = hv.p(1.4, 0.0, -4.0); ms = hv.s(-4.0)
        p_.seg((mx, my), (mx, my - 1.0 * ms), max(2.0, 0.06 * ms), '#5a4030')
        p_.fill(rrect(mx - 0.25 * ms, my - 1.3 * ms, 0.5 * ms, 0.3 * ms, 0.12 * ms), '#2a2a2e')
        text(p_.cv, 'KEMP', mx, my - 1.1 * ms, 900, 0.1 * ms, '#e8e0d0', 240, 0.1)
    L += _lit(hv.d(0.0), house, 'so_house', _key('gp', 'so', 'house'), box, hv, amb, day, [])
    wq = [(LWIN[0], 2.1, 0.0), (LWIN[1], 2.1, 0.0), (LWIN[1], 0.85, 0.0), (LWIN[0], 0.85, 0.0)]

    def inside(pen, t):                                                         # dim room behind the glass
        q = hv.quad(wq); pen.fill(q, '#3a3430'); b = q.getBounds()
        pen.linear(q, 0, b.top(), 0, b.bottom(), [(0, '#5a4a3a', 255), (1, '#2a221c', 255)])
    L.append(Layer(hv.d(1.2), inside, 'so_inside', cache=_key('gp', 'so', 'inside'), bounds=box))

    def glass(pen, t):
        q = hv.quad(wq); b = q.getBounds()
        pen.cv.save(); pen.cv.clipPath(q, skia.ClipOp.kIntersect, True)
        pen.linear(q, 0, b.top(), 0, b.bottom(), [(0, '#d8e0ec', 70), (0.6, '#d8e0ec', 20), (1, '#d8e0ec', 40)])
        for u in (0.1, 0.55):
            x0_ = b.left() + b.width() * u
            pen.fill(poly([(x0_, b.bottom()), (x0_ + b.width() * 0.1, b.bottom()), (x0_ + b.width() * 0.35, b.top()), (x0_ + b.width() * 0.25, b.top())]), '#ffffff', 30)
        pen.cv.restore()
        for i in range(1, 3):
            xm = LWIN[0] + (LWIN[1] - LWIN[0]) * i / 3
            pen.seg(hv.p(xm, 2.1, 0.0), hv.p(xm, 0.85, 0.0), max(2.0, 0.03 * hv.s(0.0)), '#f0ece4')
        pen.seg(hv.p(LWIN[0], 1.5, 0.0), hv.p(LWIN[1], 1.5, 0.0), max(2.0, 0.03 * hv.s(0.0)), '#f0ece4')
    L.append(Layer(hv.d(-0.02), glass, 'so_glass', cache=_key('gp', 'so', 'glass'), bounds=box, blur=0))
    vY = -6.6

    def van_layer(pen, t):
        dv = _van_drive(vs['drive'], t)
        x = dv[0] if dv else vs['x']
        px, py = hv.p(x, 0.0, vY); s = hv.s(vY)
        museum_van(pen, px, py, VAN_LEN * s, t, 1, dv[2] if dv else 0.0)
    L.append(Layer(hv.d(vY), van_layer, 'so_van', blur=None))
    a = {'owen_window': hv.anchor(-3.7, 0.6, note='Owen standing inside the front window (draw before so_glass)'),
         'porch': hv.anchor(-0.4, -1.0, 0.45, 'on the porch')}
    info = {'view': hv, 'van': vs, 'cam_env': dict(x=(760, 1160), y=(420, 640), zoom=(1.0, 1.1), f=(1.0, 3.0))}
    return SetPiece('street_morning', L, a, {}, lens='lens', grade='morning', focus=hv.d(0.0), dof=0.3, cover=FRAME, info=info)


# ---------------------------------------------------------------------------------------------- 1962: the first show
def stage_1962(spot=1.0, curtain=1.0):
    """The Palace, 1962, his very first show (sepia, grade 'memory'): a small proscenium stage, red velvet curtains
    swagged open (curtain 0..1: 0 = closed), footlights, a hard spotlight circle on the boards, the stool and a
    microphone stand, the dark backdrop, the audience's heads at the bottom. Anchors: stool (seat top), stand."""
    v = View(820, 480, 1.4)
    sf = _kfn(spot, 97)
    cf = curtain if callable(curtain) else (lambda t, c=float(curtain): c)

    def back(pen, t):
        pen.fill(rect(-330, -230, 2580, 1540), '#140c0a')
        pen.fill(rect(-330, 700, 2580, 700), '#4a3020'); pen.texture(rect(-330, 700, 2580, 700), 'wood', 0.6, 'overlay', 1.4, 90)
        for i in range(30): pen.seg((-330 + i * 90, 700), (-330 + i * 90 - (i - 15) * 30, 1310), 2, '#1a1008', 160)
        pen.linear(rect(-330, -230, 2580, 940), 0, -230, 0, 700, ['#1a0e0c', '#2a1410'])
        for i in range(16):
            x = -200 + i * 150
            pen.fill(rect(x, -230, 70, 930), '#24100c', 160)
        sx, sy = 960, 720
        for dx in (-40, 40):
            pen.line(poly([(sx + dx * 0.5, sy - 40), (sx + dx, sy + 120)], False), 7, '#8a7a6a')
        pen.fill(oval(sx, sy - 44, 52, 14), '#3a2a20'); pen.line(oval(sx, sy - 44, 52, 14), 3, LINE)
        mx = 1180
        pen.seg((mx, 840), (mx, 560), 5, '#8a8a8a'); pen.fill(oval(mx, 840, 40, 10), '#3a3a3a'); pen.fill(rrect(mx - 14, 520, 28, 48, 12), '#a8a8a8')

    def spot_fn(pen, t):
        k = sf(t)
        if k < 0.02: return
        pen.cone(960, -230, 40, 380, 1000, '#fff6e0', 40 * k, 50)
        pen.radial(None, 960, 800, 420, [(0, '#fff6e0', 140 * k), (0.8, '#fff6e0', 90 * k), (1, '#fff6e0', 0)], sy=0.22, clip=False)

    def proscenium(pen, t):
        o = clamp(cf(t))
        pen.fill(minus(rect(-400, -300, 2720, 1700), rrect(80, 40, 1760, 1100, 60)), '#2a1a12')
        pen.fill(rect(-400, -300, 2720, 160), '#6a1a1a')
        for i in range(24):
            pen.fill(poly([(-400 + i * 120, -140), (-340 + i * 120, -60), (-280 + i * 120, -140)]), '#7a2222')
        for side in (-1, 1):
            w = 260 + (1 - o) * 760
            x0 = 80 if side < 0 else 1840 - w
            cur = smooth([(x0, 40), (x0 + w, 40), (x0 + w - (120 * o if side < 0 else -120 * o) * 0.0, 400), (x0 + (w * 0.55 if side < 0 else w * 0.45), 1140),
                          (x0 + (0 if side < 0 else w), 1140)], True, 0.4)
            pen.fill(rect(x0, 40, w, 1100), '#8a1a1a')
            for k in range(8):
                pen.fill(rect(x0 + k * w / 8, 40, w / 16, 1100), '#5a0c0c', 140)
            pen.line(rect(x0, 40, w, 1100), 4, LINE)
            if o > 0.3:
                tx = x0 + (w * 0.75 if side < 0 else w * 0.25)
                pen.line(smooth([(tx - 30, 560), (tx, 600), (tx + 30, 560)], False), 10, '#d8b04a')
        for i in range(14):                                                    # footlights
            fx = 160 + i * 124
            pen.fill(rrect(fx - 26, 1090, 52, 22, 8), '#3a2a1a'); pen.fill(oval(fx, 1092, 18, 8), '#fff2c8')
            pen.glow(fx, 1088, 60, '#ffe6a8', 100)
    L = [Layer(2.0, back, 'st62_back', cache=_key('gp', '1962', 'back'), bounds=(-330, -230, 2250, 1310)),
         Layer(1.98, spot_fn, 'st62_spot', blur=0),
         Layer(0.9, proscenium, 'st62_frame', blur=None),
         Layer(0.6, lambda pen, t: _audience(pen, t, None, 1180, 15, 7, 1.1, '#0a0806', '#e8d0a0'), 'st62_audience', blur=None)]
    a = {'stool': Anchor(960, 676, 2.0, 640.0, 'the stool seat (on the stage, depth 2)'), 'stand': Anchor(1120, 840, 2.0, 640.0, 'standing at the microphone')}
    info = {'spot': sf, 'curtain': cf, 'cam_env': dict(x=(880, 1040), y=(480, 600), zoom=(1.0, 1.3), f=(1.0, 1.6))}
    return SetPiece('stage_1962', L, a, {}, lens='lens', grade='memory', focus=2.0, dof=1.0, cover=FRAME, info=info)


# ---------------------------------------------------------------------------------------------- shaky handwriting
_HAND_FONT = '/usr/share/fonts/opentype/inter/Inter-ThinItalic.otf'
_HAND_TF = {}


def _hand_tf():
    if 'tf' not in _HAND_TF:
        tf = skia.Typeface.MakeFromFile(_HAND_FONT) if os.path.exists(_HAND_FONT) else None
        _HAND_TF['tf'] = tf or typeface(600)
    return _HAND_TF['tf']


def _tremor(x, y, seed):
    return (math.sin(x * 1.7 + seed * 3.1 + math.sin(y * 1.3 + seed)) * 0.5 + math.sin(y * 2.3 - x * 0.7 + seed * 5.7) * 0.35
            + math.sin(x * 4.1 + y * 3.7 + seed * 1.9) * 0.15)


def _warp_glyph(p, size, amp, seed):
    """Resample a glyph outline and push it through a smooth tremor field (both edges of a stroke move together, so it
    reads as a shaking pen, not a jagged outline)."""
    out = skia.Path()
    cm = skia.PathMeasure(p, False)
    step = max(0.6, size * 0.035); f = 1.0 / (size * 0.11)
    while True:
        L = cm.getLength()
        if L > 0:
            n = max(2, int(L / step))
            pts = []
            for i in range(n + 1):
                pos, _ = cm.getPosTan(min(L, i * L / n))
                x, y = pos.x(), pos.y()
                pts.append((x + amp * _tremor(x * f, y * f, seed), y + amp * _tremor(y * f + 7, x * f + 3, seed + 11)))
            out.moveTo(*pts[0])
            for q in pts[1:]: out.lineTo(*q)
            if cm.isClosed(): out.close()
        if not cm.nextContour(): break
    return out


def shaky_text(pen, s, x, y, size, c='#26306a', a=235, seed=0, shake=1.0, w=None, steady=False):
    """Grandpa's shaky hospital handwriting (a thin italic hand pushed through a tremor field, baseline drift, letters
    wandering in size and angle). steady=True: the neater, colder hand (rule six - the one HE changed). Returns width."""
    rng = np.random.default_rng(seed)
    font = skia.Font(_hand_tf(), size)
    glyphs = font.textToGlyphs(s); widths = font.getWidths(glyphs)
    k = 0.35 if steady else 1.0
    pw = (w if w is not None else size * 0.03) * (0.8 if steady else 1.0)
    st = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=pw, Color=col(c, a), StrokeCap=skia.Paint.kRound_Cap,
                    StrokeJoin=skia.Paint.kRound_Join)
    fl = skia.Paint(AntiAlias=True, Color=col(c, a))
    px = x; drift = 0.0
    for g, wd in zip(glyphs, widths):
        drift = drift * 0.85 + rng.normal(0, size * 0.012 * k)
        sc = 1 + rng.normal(0, 0.05 * k)
        p = font.getPath(g)
        if p is not None and not p.isEmpty():
            m = skia.Matrix(); m.setScale(sc, sc * (1 + rng.normal(0, 0.04 * k))); m.postRotate(rng.normal(0, 2.5 * k)); m.postTranslate(px, y + drift)
            q = skia.Path(p); q.transform(m)
            q = _warp_glyph(q, size, size * 0.022 * shake * k, seed * 13 + int(px))
            pen.cv.drawPath(q, fl); pen.cv.drawPath(q, st)
        px += wd * sc * (1 + rng.normal(0, 0.03 * k))
    return px - x


def _shaky_lines(s, size, maxw):
    """Word-wrap for the handwriting (font metrics of the hand)."""
    font = skia.Font(_hand_tf(), size)
    out, cur = [], ''
    for wd in s.split(' '):
        tryl = (cur + ' ' + wd).strip()
        if font.measureText(tryl) > maxw and cur: out.append(cur); cur = wd
        else: cur = tryl
    if cur: out.append(cur)
    return out


LETTER_RULES = [(1, 'Keep him in the case.'), (2, 'He does voices.'), (3, "Don't laugh at his jokes."), (4, 'Never put your hand inside him.'),
                (5, "If someone is talking and their lips don't move, it isn't them talking."),
                (6, "If he's ever on someone's lap, don't pull him off. Have them say \"Say goodnight, Mister Winks.\""),
                (7, 'Never say goodnight to him.')]
PS_TEXT = ("P.S. He'll change one of my rules. He'll make it sound like a way to stop him. There is no way to stop him. "
           "Just never say the word.")


def _notepaper(pen, w, h, torn_bottom=True, torn_top=False, seed=0, header=True):
    """Hospital notepad paper (centred at 0, 0): faint blue rules, a red margin, the letterhead, a torn edge."""
    x0, y0 = -w / 2, -h / 2
    rng = np.random.default_rng(seed)
    pts = [(x0, y0)]
    if torn_top:
        pts = [(x0 + w * i / 24, y0 + rng.uniform(0, h * 0.03)) for i in range(25)]
    else:
        pts = [(x0, y0), (x0 + w, y0)]
    if torn_bottom:
        bot = [(x0 + w - w * i / 26, y0 + h - rng.uniform(0, h * 0.035) - (h * 0.02 if i % 5 == 0 else 0)) for i in range(27)]
    else:
        bot = [(x0 + w, y0 + h), (x0, y0 + h)]
    paper = poly(pts + ([(x0 + w, y0)] if not torn_top else []) + bot)
    pen.shadow(paper, w * 0.012, w * 0.02, w * 0.025, '#000000', 140)
    pen.fill(paper, '#f2eee2'); pen.texture(paper, 'paper', 0.55, 'overlay', 1.0)
    pen.cv.save(); pen.cv.clipPath(paper, skia.ClipOp.kIntersect, True)
    lh = h / 17.0
    for i in range(3, 18):
        pen.fill(rect(x0, y0 + i * lh, w, max(1.0, h * 0.0018)), '#8ab0d8', 150)
    pen.fill(rect(x0 + w * 0.12, y0, max(1.0, w * 0.003), h), '#e06a6a', 170)
    if header:
        text(pen.cv, 'RIVERSIDE MEMORIAL HOSPITAL', x0 + w * 0.56, y0 + lh * 1.1, 800, lh * 0.32, '#3a6aa8', 220, 0.14)
        text(pen.cv, 'PATIENT NOTES  •  4TH FLOOR', x0 + w * 0.56, y0 + lh * 1.6, 600, lh * 0.22, '#3a6aa8', 180, 0.18)
        pen.fill(oval(x0 + w * 0.2, y0 + lh * 1.25, lh * 0.32), '#3a6aa8', 200)
        pen.fill(rect(x0 + w * 0.2 - lh * 0.06, y0 + lh * 1.05, lh * 0.12, lh * 0.4), '#ffffff')
        pen.fill(rect(x0 + w * 0.2 - lh * 0.2, y0 + lh * 1.19, lh * 0.4, lh * 0.12), '#ffffff')
    pen.linear(paper, x0, y0, x0 + w, y0 + h, [(0, '#c8a868', 30), (0.6, '#c8a868', 0), (1, '#8a6a3a', 50)])     # age
    pen.cv.restore()
    pen.line(paper, max(1.0, w * 0.002), '#8a8478', 200)
    return paper, lh


_NOTEPATH = {}


def _notepaper_cached(pen, w, h, torn_bottom=True, torn_top=False, seed=0, header=True):
    """_notepaper through a sprite (the shadow blur and paper texture are the expensive part): returns (paper path, lh)."""
    k = (w, h, torn_bottom, torn_top, seed, header)
    if k not in _NOTEPATH:
        rec = skia.PictureRecorder(); c2 = rec.beginRecording(skia.Rect.MakeLTRB(-w, -h, w, h))
        _NOTEPATH[k] = _notepaper(Pen(c2), w, h, torn_bottom, torn_top, seed, header)
        rec.finishRecordingAsPicture()
    _sprite(pen, ('gp_notepaper',) + k, lambda p_: _notepaper(p_, w, h, torn_bottom, torn_top, seed, header),
            (-w / 2 - 40, -h / 2 - 40, w / 2 + 60, h / 2 + 70))
    return _NOTEPATH[k]


def _prop_letter(pen, t, hl=0, smear=0.0, show=7, hla=None, bracket=0.0, **kw):
    """Grandpa's letter: the seven rules in his shaky hand on hospital notepaper, the bottom torn off (the P.S. went with
    it). Rule six is in the neater, colder hand (he changed it). hl = rule number to light (the rest dim), or a tuple of
    rule numbers (hla = their highlight alphas 0..1, so a second band fades in instead of blinking); bracket 0..1 draws a
    red pen bracket joining rules six and seven down the margin ('side by side'); smear 0..1 runs rule six's ink (the lie
    revealed), show = how many rules are written (0..7)."""
    w, h = 760, 1040
    paper, lh = _notepaper_cached(pen, w, h, True, False, 3)
    x0, y0 = -w / 2 + w * 0.15, -h / 2 + lh * 2.95
    _sprite(pen, ('gp_letter', show), lambda p_: _letter_ink(p_, w, h, lh, show), (-w / 2, -h / 2, w / 2, h / 2))
    hls = tuple(hl) if isinstance(hl, (tuple, list)) else ((hl,) if hl else ())
    if hls:
        als = list(hla) if hla is not None else [1.0] * len(hls)
        bands = []
        for n in hls:
            y = _letter_rule_y(n, lh, w)
            bands.append(skia.Rect.MakeXYWH(-w / 2 + w * 0.13, y[0] - lh * 0.75, w * 0.86, (y[1] - y[0]) + lh * 0.95))
        cv = pen.cv
        cv.save(); cv.clipPath(paper, skia.ClipOp.kIntersect, True)
        cv.save()
        for b, a_ in zip(bands, als):
            if a_ > 0.0: cv.clipRect(b, skia.ClipOp.kDifference)
        pen.fill(rect(-w / 2, -h / 2, w, h), '#000000', 95); cv.restore()
        for b, a_ in zip(bands, als):
            if 0.0 < a_ < 0.999:                                          # a band fading in: the dim lifts off it gradually
                cv.save(); cv.clipRect(b, skia.ClipOp.kIntersect); pen.fill(rect(-w / 2, -h / 2, w, h), '#000000', 95 * (1.0 - a_)); cv.restore()
            if a_ > 0.0:
                cv.drawRect(b, skia.Paint(Color=col('#ffe066', int(255 * a_)), BlendMode=skia.BlendMode.kMultiply, AntiAlias=True))
        cv.restore()
    if bracket > 0.01:                                                     # the red pen: six and seven, side by side
        y6, y7 = _letter_rule_y(6, lh, w), _letter_rule_y(7, lh, w)
        top, bot = y6[0] - lh * 0.55, y7[1] + lh * 0.25
        xm = -w / 2 + w * 0.105
        k = clamp(bracket)
        pts = [(xm + 26, top), (xm, top + 18), (xm, bot - 18), (xm + 26, bot)]
        seg = [(xm + 26, top), (xm, top + 18)]
        L_ = (bot - top)
        if k > 0.15: seg.append((xm, top + 18 + (L_ - 36) * clamp((k - 0.15) / 0.7)))
        if k > 0.85: seg += [(xm, bot - 18), (xm + 26 * clamp((k - 0.85) / 0.15), bot - 18 + 18 * clamp((k - 0.85) / 0.15))]
        pen.line(poly(seg, False), 7.0, '#c8202a', 235)
        if k > 0.95:
            for (xa, yy) in ((x0 + 22, y6[1] + lh * 0.12), (x0 + 30, y7[0] + lh * 0.12)):   # 'Say goodnight' / 'Never say goodnight'
                pen.line(smooth([(xa, yy), (xa + w * 0.25, yy + 4), (xa + w * 0.46, yy + 1)], False), 5.0, '#c8202a', 200)
    if smear > 0.01:                                                       # rule six runs: ink drips and a smudge
        y6 = _letter_rule_y(6, lh, w)
        rng = np.random.default_rng(66)
        pen.cv.save(); pen.cv.clipPath(paper, skia.ClipOp.kIntersect, True)
        pen.fill(rect(x0 - 10, y6[0] - lh * 0.7, w * 0.8, y6[1] - y6[0] + lh), '#2a2a5a', 70 * smear, blur=12)
        for i in range(9):
            dx = x0 + rng.uniform(0, w * 0.75); ln = lh * (0.6 + 2.4 * rng.uniform()) * smear
            pen.line(poly([(dx, y6[0]), (dx + rng.uniform(-4, 4), y6[0] + ln)], False), rng.uniform(2.0, 4.5), '#26306a', 190)
            pen.fill(oval(dx, y6[0] + ln, 3.4), '#26306a', 200)
        pen.cv.restore()


def _letter_rule_y(n, lh, w):
    """(top, bottom) baseline y of rule n's lines on the letter."""
    y = -1040 / 2 + lh * 4.0
    for (k, s) in LETTER_RULES:
        nl = len(_shaky_lines('%d. %s' % (k, s), 34, w * 0.76))
        if k == n: return (y, y + (nl - 1) * lh)
        y += nl * lh + lh * 0.25
    return (y, y)


def _letter_ink(p_, w, h, lh, show):
    x0 = -w / 2 + w * 0.15
    shaky_text(p_, 'For whoever is in my house tonight -', x0, -h / 2 + lh * 2.95, 36, seed=1, shake=1.3)
    y = -h / 2 + lh * 4.0
    for (k, s) in LETTER_RULES:
        lines = _shaky_lines('%d. %s' % (k, s), 34, w * 0.76)
        if k <= show:
            for i, ln in enumerate(lines):
                shaky_text(p_, ln, x0 + (0 if i == 0 else 22), y + i * lh, 34, c='#1a1c3a' if k == 6 else '#26306a', seed=10 + k * 7 + i,
                           shake=1.15, steady=(k == 6))
        y += len(lines) * lh + lh * 0.25


def _prop_ps(pen, t, **kw):
    """The torn-off end of the letter: a corner of the same notepaper, ragged on two edges, the P.S. and the signature
    'Walter. The real one.'"""
    w, h = 620, 470
    rng = np.random.default_rng(9)
    x0, y0 = -w / 2, -h / 2
    top = [(x0 + w * i / 20, y0 + rng.uniform(0, h * 0.05)) for i in range(21)]
    right = [(x0 + w - rng.uniform(0, w * 0.04), y0 + h * i / 12) for i in range(1, 12)]
    paper = poly(top + right + [(x0 + w * 0.7, y0 + h), (x0, y0 + h)])
    pen.shadow(paper, 8, 12, 14, '#000000', 140)
    pen.fill(paper, '#f0ebde'); pen.texture(paper, 'paper', 0.6, 'overlay', 1.0)
    pen.cv.save(); pen.cv.clipPath(paper, skia.ClipOp.kIntersect, True)
    lh = 1040 / 17.0
    for i in range(0, 9): pen.fill(rect(x0, y0 + 20 + i * lh, w, 1.6), '#8ab0d8', 150)
    pen.fill(rect(x0 + 760 * 0.12 - 40, y0, 2.2, h), '#e06a6a', 170)
    pen.fill(poly([(x0 + w * 0.45, y0 + h), (x0 + w * 0.7, y0 + h * 0.6), (x0 + w * 0.9, y0 + h)]), '#000000', 18)       # a fold crease
    pen.cv.restore()

    def ink(p_):
        lines = _shaky_lines(PS_TEXT, 33, w * 0.82)
        for i, ln in enumerate(lines):
            shaky_text(p_, ln, x0 + 48, y0 + 20 + lh * (i + 0.85), 33, seed=200 + i, shake=1.5)
        yy = y0 + 20 + lh * (len(lines) + 0.95)
        shaky_text(p_, 'Walter. The real one.', x0 + w * 0.36, yy, 36, seed=250, shake=1.7)
    _sprite(pen, 'gp_ps_ink', ink, (x0, y0, x0 + w, y0 + h))


def _prop_envelope(pen, t, **kw):
    """The envelope taped to the case's lid: cream, a little foxed, two strips of yellowed tape, 'For whoever is in my
    house tonight.' in the shaky hand."""
    w, h = 900, 520
    e = rect(-w / 2, -h / 2, w, h)
    pen.shadow(e, 6, 10, 12, '#000000', 160)
    pen.fill(e, '#ece2c6'); pen.texture(e, 'paper', 0.6, 'overlay', 1.0)
    pen.linear(e, -w / 2, -h / 2, w / 2, h / 2, [(0, '#c8a868', 40), (0.5, '#c8a868', 0), (1, '#8a6a3a', 60)])
    pen.line(poly([(-w / 2, -h / 2), (0, h * 0.06), (w / 2, -h / 2)], False), 2.0, '#a8987a', 200)
    pen.line(e, 2.0, '#8a7e64', 220)
    _sprite(pen, 'gp_env_ink', lambda p_: (shaky_text(p_, 'For whoever is in', -w * 0.36, h * 0.12, 64, seed=301, shake=1.4),
                                           shaky_text(p_, 'my house tonight.', -w * 0.3, h * 0.12 + 86, 64, seed=302, shake=1.4)),
            (-w / 2, -h / 2, w / 2, h / 2))
    for (tx, ty, ang) in ((-w / 2 + 40, -h / 2 + 10, 38), (w / 2 - 40, -h / 2 + 10, -38), (-w / 2 + 40, h / 2 - 10, -38), (w / 2 - 40, h / 2 - 10, 38)):
        pen.cv.save(); pen.cv.translate(tx, ty); pen.cv.rotate(ang)
        tp = rect(-90, -26, 180, 52)
        pen.fill(tp, '#e8d49a', 150); pen.texture(tp, 'grunge', 0.4, 'overlay', 0.8)
        pen.line(poly([(-90, -26), (-86, -14), (-91, 0), (-85, 12), (-90, 26)], False), 1.5, '#b8a060', 160)
        pen.cv.restore()


def _leather_bg(pen, t):
    """The case's black leather lid filling the frame (in focus behind the envelope / latches): grain, stitching."""
    r = rect(-700, -500, 3320, 2080)
    pen.linear(r, -700, -500, 2620, 1580, ['#2c2a34', '#1a1820', '#0e0d12'])
    pen.texture(r, 'grunge', 0.5, 'overlay', 0.5)
    pen.texture(r, 'skin', 0.35, 'overlay', 1.5)
    pen.dashed(rrect(-140, -60, 2200, 1200, 40), 4.0, '#8a8478', 170, 18, 12)
    pen.radial(None, 500, 200, 1500, [(0, '#ffe2b8', 50), (1, '#ffe2b8', 0)], clip=False)


def _prop_latches(pen, t, latch=0.0, **kw):
    """The case's front: the seam, two brass latches (latch 0..1 or (l, r) flips them open), the leather handle."""
    l1, l2 = (latch, latch) if not isinstance(latch, (tuple, list)) else latch
    W = 1700
    pen.fill(rect(-W / 2 - 400, -40, W + 800, 22), '#08070a'); pen.fill(rect(-W / 2 - 400, -18, W + 800, 6), '#4a4652', 200)
    for (lx, op) in ((-520, l1), (520, l2)):
        op = clamp(op)
        base = rrect(lx - 90, -60, 180, 150, 18)
        pen.shadow(base, 6, 10, 10, '#000000', 160)
        pen.radial(base, lx - 30, -20, 220, [(0, '#f8e2a0'), (0.55, '#c9a24a'), (1, '#7a5a22')]); pen.line(base, 4, '#3a2a10')
        for (sx, sy) in ((-60, -30), (60, -30), (-60, 60), (60, 60)):
            pen.fill(oval(lx + sx, sy, 9), '#8a6a2a'); pen.line(poly([(lx + sx - 5, sy), (lx + sx + 5, sy)], False), 2, '#4a3a1a')
        pen.cv.save(); pen.cv.translate(lx, -50); pen.cv.rotate(-165 * ease_out_back(op, 1.4))
        hasp = rrect(-62, -150, 124, 160, 24)
        pen.shadow(hasp, 4, 8, 8, '#000000', 150)
        pen.radial(hasp, -20, -110, 200, [(0, '#fff0b8'), (0.5, '#d8b04a'), (1, '#8a6a22')]); pen.line(hasp, 4, '#3a2a10')
        pen.fill(rrect(-30, -130, 60, 34, 10), '#8a6a2a', 200); pen.fill(rrect(-48, -146, 30, 112, 12), '#ffffff', 45)
        pen.cv.restore()
        pen.fill(oval(lx, 60, 22, 16), '#3a2a10'); pen.fill(oval(lx, 56, 18, 12), '#c9a24a')
    hx = 0
    for sx in (-110, 110):
        pen.fill(rrect(hx + sx - 30, -50, 60, 70, 10), '#c9a24a'); pen.line(rrect(hx + sx - 30, -50, 60, 70, 10), 3, '#3a2a10')
    hd = smooth([(hx - 120, -30), (hx - 100, -170), (hx + 100, -170), (hx + 120, -30)], False, 0.9)
    pen.line(hd, 62, '#000000', 120); pen.line(hd, 56, '#1e1c22'); pen.line(hd, 10, '#4a4652', 160)


def _prop_case_open(pen, t, warm=1.0, **kw):
    """The open case from above: the leather rim, the brass hinges, the lid's velvet lining (top), and the red velvet bed
    pressed into the shape of him: the hollow (warm: a faint shimmer rising off it)."""
    W, H = 760, 1260
    pen.shadow(rrect(-W / 2, -H / 2 + 300, W, H - 300, 30), 10, 18, 24, '#000000', 170)
    lid = rrect(-W / 2, -H / 2 - 120, W, 420, 30)
    pen.fill(lid, '#1c1a22'); pen.fill(rrect(-W / 2 + 26, -H / 2 - 94, W - 52, 368, 18), '#7a1420'); pen.texture(rrect(-W / 2 + 26, -H / 2 - 94, W - 52, 368, 18), 'fabric', 0.7, 'overlay', 1.0)
    pen.fill(rrect(-W / 4, -H / 2 - 40, W / 2, 160, 12), '#5a0e18', 200); pen.line(rrect(-W / 4, -H / 2 - 40, W / 2, 160, 12), 3, '#3a060c', 200)
    body = rrect(-W / 2, -H / 2 + 300, W, H - 300, 30)
    pen.fill(body, '#1c1a22'); pen.texture(body, 'grunge', 0.5, 'overlay', 0.6)
    for hx in (-W * 0.28, W * 0.28):
        pen.fill(rrect(hx - 50, -H / 2 + 280, 100, 40, 8), '#c9a24a'); pen.line(rrect(hx - 50, -H / 2 + 280, 100, 40, 8), 3, '#3a2a10')
    pen.cv.save(); pen.cv.translate(-W / 2 + 34, -H / 2 + 334)
    pen.cv.scale((W - 68) / 35.0, (H - 368) / 77.0)
    _velvet_hollow(pen, 35, 77)
    pen.cv.restore()
    pen.dashed(rrect(-W / 2 + 12, -H / 2 + 312, W - 24, H - 324, 22), 3.0, '#8a8478', 160, 14, 10)
    if warm > 0.01:
        for i in range(7):
            ph = t * 0.6 + i * 0.37
            x = -W * 0.3 + i * W * 0.1
            pts = [(x + 14 * math.sin(ph * 3 + j * 0.8), 300 - j * 90 - (ph % 1.0) * 90) for j in range(8)]
            pen.line(smooth(pts, False, 0.8), 6, '#ffc8a0', 22 * warm, blur=6)
        pen.radial(None, 0, 160, 420, [(0, '#ff8a60', 36 * warm), (1, '#ff8a60', 0)], clip=False)


def _prop_mug(pen, t, stir=None, spoon=True, sugar=2, **kw):
    """Grandpa's mug of coffee on the kitchen table, from above at 3/4: the show logo, the coffee's surface, the spoon
    (stir = f(t) -> angle in turns while stirring, or None = resting), two sugar-cube wrappers beside it, the sugar bowl."""
    s = 1000.0
    w, h = 0.32 * s, 0.34 * s
    x, y = 0, 150
    pen.radial(None, x + 40, y + 20, 340, [(0, '#000000', 150), (1, '#000000', 0)], sy=0.32, clip=False)
    body = smooth([(x - w / 2, y - h), (x + w / 2, y - h), (x + w / 2, y - h * 0.08), (x + w * 0.4, y + 6), (x - w * 0.4, y + 6), (x - w / 2, y - h * 0.08)], True, 0.25)
    hd = smooth([(x + w * 0.48, y - h * 0.82), (x + w * 0.9, y - h * 0.78), (x + w * 0.95, y - h * 0.3), (x + w * 0.48, y - h * 0.22)], False, 0.8)
    pen.line(hd, 44, LINE); pen.line(hd, 34, '#e6dcc6')
    pen.fill(body, '#ece2cc'); pen.linear(body, x - w / 2, 0, x + w / 2, 0, [(0, '#ffffff', 80), (0.35, '#ffffff', 0), (1, '#000000', 60)])
    pen.cv.save(); pen.cv.clipPath(body, skia.ClipOp.kIntersect, True)
    _winks_face(pen, x - w * 0.06, y - h * 0.5, w * 0.2)
    text(pen.cv, 'SATURDAY MORNING', x - w * 0.06, y - h * 0.16, 900, w * 0.07, '#c8322a', 255, 0.04)
    pen.cv.restore()
    pen.line(body, 5, LINE)
    rim = oval(x, y - h, w / 2, w * 0.17)
    pen.fill(rim, '#d8ccb4'); pen.line(rim, 4, LINE, 220)
    cof = oval(x, y - h + 10, w * 0.44, w * 0.14)
    pen.fill(cof, '#3a1e0c')
    an = (stir(t) if callable(stir) else 0.0) * 2 * math.pi
    pen.cv.save(); pen.cv.clipPath(cof, skia.ClipOp.kIntersect, True)
    for r in (0.12, 0.24, 0.34):                                                   # swirl on the coffee
        pen.line(oval(x, y - h + 10, w * r, w * r * 0.32), 3, '#7a4a24', 90 if stir else 40)
    pen.fill(oval(x - w * 0.12 + 18 * math.cos(an), y - h + 4 + 6 * math.sin(an), w * 0.1, w * 0.025), '#c8945a', 120)
    pen.cv.restore()
    if spoon:
        sx, sy = x + w * 0.16 * math.cos(an), y - h + 10 + w * 0.05 * math.sin(an)
        hx_, hy_ = sx + w * 0.55, sy - h * 0.62
        pen.line(poly([(sx, sy), (hx_, hy_)], False), 16, LINE); pen.line(poly([(sx, sy), (hx_, hy_)], False), 11, '#c0c4cc')
        pen.line(poly([(sx + 2, sy - 3), (hx_ + 2, hy_ - 3)], False), 3, '#ffffff', 160)
        pen.fill(oval(hx_, hy_, 16, 9), '#c0c4cc'); pen.line(oval(hx_, hy_, 16, 9), 3, LINE)
    for i in range(sugar):                                                          # two torn sugar-cube wrappers
        cx_, cy_ = x - 300 + i * 70, y + 40 + i * 30
        pen.cv.save(); pen.cv.translate(cx_, cy_); pen.cv.rotate(-20 + 34 * i)
        wr = poly([(-34, -22), (30, -26), (36, 20), (-30, 24)])
        pen.fill(wr, '#f4f0e6'); pen.line(wr, 2.5, '#8a8478', 220)
        text(pen.cv, 'SUGAR', 0, 6, 900, 13, '#c8322a', 230, 0.08)
        pen.cv.restore()
    bx, by = x + 330, y - 40
    pen.fill(oval(bx, by, 120, 40), '#000000', 90)
    bowl = smooth([(bx - 110, by - 80), (bx + 110, by - 80), (bx + 90, by), (bx - 90, by)], True, 0.5)
    pen.fill(bowl, '#e8e4dc'); pen.line(bowl, 4, LINE)
    pen.fill(oval(bx, by - 80, 110, 30), '#d8d0c0'); pen.line(oval(bx, by - 80, 110, 30), 3, LINE, 200)
    for k in range(5):
        pen.fill(rect(bx - 70 + k * 28, by - 98 - (k % 2) * 10, 24, 22), '#fbfaf6'); pen.line(rect(bx - 70 + k * 28, by - 98 - (k % 2) * 10, 24, 22), 1.5, '#a8a49c')


def _bg_kitchen_table(pen, t):
    r = rect(-700, -500, 3320, 2080)
    pen.fill(r, '#e8cf72'); pen.texture(r, 'grunge', 0.3, 'overlay', 0.8)
    pen.fill(rect(-700, -500, 3320, 620), '#efe2b8')
    pen.fill(rect(-700, 80, 3320, 60), '#d8dce4')
    pen.fill(rect(800, -500, 520, 520), '#1a2448'); pen.line(rect(800, -500, 520, 520), 20, '#f2ead8')
    pen.radial(None, 960, 300, 1300, [(0, '#ffd890', 120), (0.6, '#ffb860', 30), (1, '#000000', 140)], clip=False)


def _prop_slot(pen, t, hand=0.0, paper=0.0, **kw):
    """The back of Mister Winks: the burgundy usher's jacket (centre seam, a half-belt with two brass buttons), the
    slot cut through it into the hollow wooden body (dark inside, the head stick's lever glinting). hand 0..1 slides your
    hand in (fingers vanish into the dark); paper 0..1 pushes a folded corner of hospital notepaper out of the slot."""
    jk, jsh, jhi = '#7d1d2b', '#4e0f19', '#a8384a'
    back = smooth([(-520, -620), (520, -620), (560, -200), (540, 700), (-540, 700), (-560, -200)], True, 0.4)
    pen.fill(back, jk); pen.texture(back, 'fabric', 0.7, 'overlay', 1.0)
    pen.linear(back, -560, 0, 560, 0, [(0, '#000000', 110), (0.3, '#000000', 0), (0.7, '#000000', 0), (1, '#000000', 130)])
    pen.seg((0, -620), (0, 700), 5, jsh); pen.seg((4, -620), (4, 700), 2, jhi, 120)
    pen.fill(smooth([(-520, -620), (-200, -680), (200, -680), (520, -620), (420, -560), (0, -600), (-420, -560)], True, 0.5), '#5a6070')   # collar
    belt = rect(-380, 360, 760, 70)
    pen.fill(belt, jsh); pen.line(belt, 3, LINE)
    for bx in (-300, 300):
        pen.radial(oval(bx, 395, 24), bx - 8, 386, 30, [(0, '#fff0b8'), (0.6, '#d8b04c'), (1, '#8a6a22')]); pen.line(oval(bx, 395, 24), 3, LINE)
    slot = rrect(-110, -260, 220, 360, 30)
    pen.fill(rrect(-124, -274, 248, 388, 36), '#3a2414')                          # the carved wooden lip
    pen.texture(rrect(-124, -274, 248, 388, 36), 'wood', 0.6, 'overlay', 1.0, 90)
    pen.fill(slot, '#060304')
    pen.radial(slot, 0, -140, 200, [(0, '#3a1a0a', 200), (1, '#060304', 0)])
    pen.line(poly([(30, -220), (40, 40)], False), 18, '#2a1a0c'); pen.line(poly([(26, -220), (34, 40)], False), 4, '#8a6a3a', 140)   # the head stick
    pen.line(rrect(-124, -274, 248, 388, 36), 4, LINE)
    pen.line(rrect(-110, -260, 220, 360, 30), 3, '#000000', 200)
    if paper > 0.01:
        u = clamp(paper)
        pen.cv.save(); pen.cv.clipPath(minus(rect(-1000, -1000, 2000, 2000), rect(-110, -1000, 220, 1000 - 260 + 360 * (1 - u))), skia.ClipOp.kIntersect, True)
        pen.cv.restore()
        pen.cv.save(); pen.cv.clipPath(union(rect(-2000, 100, 4000, 2000), slot), skia.ClipOp.kIntersect, True)
        py = 100 - 40 + 260 * u
        pc = poly([(-60, py - 260), (70, py - 250), (80, py + 30), (-50, py + 40)])
        pen.fill(pc, '#f0ebde'); pen.texture(pc, 'paper', 0.6, 'overlay', 1.0)
        for i in range(3): pen.fill(rect(-60, py - 200 + i * 60, 140, 2), '#8ab0d8', 140)
        pen.line(pc, 2.5, '#8a8478')
        pen.cv.restore()


def _slot_hand(part):
    def draw(pen, t, kw=None):
        h = clamp((kw or {}).get('hand', 0.0))
        if h <= 0.01: return
        CHm = _CH()
        y = 820 - 860 * ease_in_out(h)
        cv = pen.cv
        cv.save()
        if part == 'in':                                                       # fingers inside: clipped to the slot
            cv.clipPath(rrect(-110, -260, 220, 360, 30), skia.ClipOp.kIntersect, True)
            if CHm is not None: CHm.draw_hand(pen, 'you', 0, y, 300, 'flat', 180.0, 1)
            else: draw_hand(pen, 0, y, 1.0, 180.0, 'flat', skin='#d8b8a0', sleeve='#4a5a7a')
            pen.fill(rect(-120, -270, 240, 400), '#000000', 150)
        else:                                                                  # the wrist and sleeve below the slot
            cv.clipPath(rect(-2000, 100, 4000, 3000), skia.ClipOp.kIntersect, True)
            if CHm is not None: CHm.draw_hand(pen, 'you', 0, y, 300, 'flat', 180.0, 1)
            sl = rrect(-90, y + 230, 180, 900, 40)
            pen.fill(sl, '#3a4a6a'); pen.texture(sl, 'fabric', 0.6, 'overlay', 1.0); pen.line(sl, 4, LINE)
        cv.restore()
    return draw


def _prop_squeeze(pen, t, squeeze=None, take=1.0, **kw):
    kw = dict(kw, take=take)
    """Inside the dummy: the dark carved hollow, the head stick and its jaw cord, your hand pushed in from below left and
    a warm old hand (a gold wedding band) coming from above that lets go of the stick and closes round yours. squeeze =
    f(t) -> 0..1 (three pulses = 'I love you'); each pulse tightens the grip and warms the light."""
    k = clamp(squeeze(t)) if callable(squeeze) else clamp(float(squeeze or 0.0))
    pen.fill(rect(-1200, -800, 2400, 1600), '#0a0604')
    rng = np.random.default_rng(14)
    for i in range(40):                                                         # gouge marks of the carving
        x = rng.uniform(-1200, 1200); y = rng.uniform(-800, 800); ln = rng.uniform(120, 420); a = rng.uniform(-0.5, 0.5)
        pts = [(x + math.cos(a) * ln * u, y + math.sin(a) * ln * u + 18 * math.sin(u * 3)) for u in (0, 0.33, 0.66, 1.0)]
        pen.line(smooth(pts, False), rng.uniform(14, 34), '#1e120a', 200)
        pen.line(smooth([(p[0], p[1] - 6) for p in pts], False), 2.5, '#5a3a1e', 110)
    pen.radial(None, 60, 0, 900, [(0, '#ffb070', 70 + 70 * k), (0.5, '#c86a30', 30 + 30 * k), (1, '#000000', 0)], clip=False)
    pen.line(poly([(260, -900), (220, 200)], False), 64, '#3a2414'); pen.line(poly([(250, -900), (212, 200)], False), 12, '#8a6a3a', 150)
    pen.line(smooth([(240, -300), (330, -200), (300, 100)], False), 5, '#c8b890', 170)
    CHm = _CH()
    tk = ease_in_out(clamp(kw.get('take', 1.0)))
    tight = 1.0 - 0.07 * k
    ox, oy, oa = lerp(250, -120, tk), lerp(-520, 60, tk), lerp(10.0, -42.0, tk) - 8 * k
    if CHm is not None:
        CHm.draw_hand(pen, 'you', -250, 560, 560, 'open', 145.0, 1)
        pen.cv.save(); pen.cv.translate(ox, oy); pen.cv.scale(tight, tight)
        CHm.draw_hand(pen, 'grandpa', 0, 0, 560, 'grip', oa, -1)
        pen.cv.restore()
    else:
        draw_hand(pen, -250, 560, 1.3, 145.0, 'flat', skin='#d8b8a0', sleeve='#3a4a6a')
        draw_hand(pen, ox, oy, 1.3 * tight, oa, 'hold', skin='#c8a088', sleeve='#6a5a4a')
    gx, gy = ox + 70 * tight, oy + 300 * tight
    pen.glow(gx, gy, 70, '#ffe8a8', 60 + 140 * k)                                # his wedding band glints
    sl = smooth([(-1200, 900), (-700, 520), (-560, 640), (-900, 1100)], True, 0.5)
    pen.fill(sl, '#2a3450'); pen.line(sl, 4, LINE)


def _prop_photo_family(pen, t, **kw):
    """A framed 1970s photo (colour faded to amber): young Walter in his TV suit on the show's stool with Mister Winks on
    his knee, both 'smiling' at the camera. Uses the cast's figures when characters.py provides them."""
    W, H = 760, 980
    fr = rect(-W / 2, -H / 2, W, H)
    pen.shadow(fr, 10, 16, 18, '#000000', 160)
    pen.fill(fr, '#4a2a16'); pen.texture(fr, 'wood', 0.6, 'overlay', 1.0, 90)
    pen.fill(rect(-W / 2 + 40, -H / 2 + 40, W - 80, H - 80), '#e8e0cc')
    ix, iy, iw, ih = -W / 2 + 90, -H / 2 + 90, W - 180, H - 220
    cv = pen.cv; cv.save(); cv.clipPath(rect(ix, iy, iw, ih), skia.ClipOp.kIntersect, True)
    pen.linear(rect(ix, iy, iw, ih), 0, iy, 0, iy + ih, ['#d8a050', '#c86a3a', '#6a3a2a'])
    for k in range(10):
        a0 = k * math.pi / 5
        pen.fill(poly([(0, iy + ih * 0.3), (math.cos(a0) * 900, iy + ih * 0.3 + math.sin(a0) * 900), (math.cos(a0 + 0.3) * 900, iy + ih * 0.3 + math.sin(a0 + 0.3) * 900)]), '#e8b860', 120)
    CHm = _CH()
    drew = False
    if CHm is not None and hasattr(CHm, 'draw_lap'):
        try:
            aw = CHm.Acting('walter74'); aw.vent_pose(); P = aw.at(1.0); P.smile = max(getattr(P, 'smile', 0.0), 0.6)
            ad = CHm.Acting('winks'); ad.sit_dummy(); D = ad.at(1.0)
            CHm.draw_lap(pen, 'walter74', -60, iy + ih + 40, ih * 1.05, P, D, side=1)
            drew = True
        except Exception:
            drew = False
    if not drew:
        _sepia_photo(pen, ix, iy, iw, ih, 1)
    pen.fill(rect(ix, iy, iw, ih), '#f0c890', 50)
    pen.linear(rect(ix, iy, iw, ih), ix, iy, ix + iw, iy + ih, [(0, '#ffffff', 40), (0.5, '#ffffff', 0), (1, '#3a1a0a', 70)])
    cv.restore()
    shaky_text(pen, "Walt & Winks - '74", -W / 2 + 120, H / 2 - 70, 40, c='#3a3020', seed=410, shake=0.6)
    pen.fill(poly([(-W / 2 + 40, -H / 2 + 40), (-W / 2 + 300, -H / 2 + 40), (-W / 2 + 40, -H / 2 + 360)]), '#ffffff', 26)


def _prop_poster(pen, t, kind='1962', **kw):
    W, H = 700, 1000
    fr = rect(-W / 2, -H / 2, W, H)
    pen.shadow(fr, 10, 16, 18, '#000000', 160)
    pen.cv.save(); pen.cv.translate(-W / 2, -H / 2)
    _poster_art(pen, W, H, kind)
    pen.cv.restore()
    if kind == '1962':
        pen.fill(fr, '#8a6a3a', 40); pen.texture(fr, 'paper', 0.5, 'overlay', 1.0)
        for (cx_, cy_) in ((-W / 2 + 20, -H / 2 + 20), (W / 2 - 20, -H / 2 + 20)):
            pen.fill(oval(cx_, cy_, 10), '#c8c4bc'); pen.line(oval(cx_, cy_, 10), 2, LINE)
    pen.line(fr, 3, '#3a2a1a')


def _prop_vcr(pen, t, tape=1.0, play=True, **kw):
    """The VCR on the cabinet shelf, close: the silver deck, the blinking 12:00, the PLAY light, the tape half-in with its
    handwritten label 'SAT. MORNING w/ WALTER KEMP - 1974'."""
    W, H = 1500, 300
    deck = rrect(-W / 2, -H / 2, W, H, 16)
    pen.shadow(deck, 8, 14, 16, '#000000', 170)
    pen.linear(deck, 0, -H / 2, 0, H / 2, ['#5a5a62', '#3a3a40', '#26262a']); pen.line(deck, 4, LINE)
    pen.fill(rect(-W / 2 + 60, -H / 2 + 60, 620, 110), '#0c0c0e')
    u = clamp(tape)
    if u > 0:
        tw = 560; th = 80 + 60 * u
        sp_ = rect(-W / 2 + 90, -H / 2 + 75 - th * 0.15, tw, th)
        pen.fill(rect(-W / 2 + 90, -H / 2 + 75 + th * 0.85, tw, 14), '#000000', 140)
        pen.fill(sp_, '#1a1a1e'); pen.line(sp_, 3, LINE)
        lb = rect(-W / 2 + 120, -H / 2 + 75 - th * 0.15 + 12, tw - 60, th - 24)
        pen.fill(lb, '#e2ddce'); pen.line(lb, 2, '#8a8478')
        shaky_text(pen, 'SAT. MORNING w/ WALTER KEMP  1974', -W / 2 + 132, -H / 2 + 75 - th * 0.15 + th * 0.62, 25, c='#2a2a6a', seed=501, shake=0.5)
    win = rect(260, -H / 2 + 70, 360, 100)
    pen.fill(win, '#061008')
    if (t % 1.0) < 0.55: text(pen.cv, '12:00', 440, -H / 2 + 145, 800, 64, '#5aff8a', 240, 0.08); pen.glow(440, -H / 2 + 120, 110, '#3aff6a', 60)
    pen.fill(oval(680, -H / 2 + 90, 12), '#ff3a2a' if play else '#3a1a1a')
    if play: pen.glow(680, -H / 2 + 90, 40, '#ff3a2a', 120)
    text(pen.cv, 'PLAY', 680, -H / 2 + 130, 800, 20, '#c8c8cc', 200, 0.1)
    for i, lbl in enumerate(('REW', 'PLAY', 'FF', 'STOP', 'EJECT')):
        bx = -W / 2 + 120 + i * 120
        pen.fill(rrect(bx - 45, H / 2 - 90, 90, 44, 6), '#8a8a92'); pen.line(rrect(bx - 45, H / 2 - 90, 90, 44, 6), 2, LINE)
        text(pen.cv, lbl, bx, H / 2 - 22, 800, 16, '#c8c8cc', 200, 0.1)
    text(pen.cv, 'VIDEOSTAR  HQ', W / 2 - 160, H / 2 - 40, 900, 28, '#c8c8cc', 220, 0.12)


def _bg_table_lamp(pen, t):
    r = rect(-700, -500, 3320, 2080)
    pen.linear(r, 0, -500, 0, 1580, ['#3a2416', '#5a3a22', '#2a1a10']); pen.texture(r, 'wood', 0.7, 'overlay', 2.6, 90)
    pen.radial(None, 300, 100, 1600, [(0, '#ffcf8f', 110), (0.55, '#ffcf8f', 26), (1, '#000000', 140)], clip=False)


def _bg_shelf(pen, t):
    r = rect(-700, -500, 3320, 2080)
    pen.fill(r, '#2a160c')
    for i in range(30):
        x = -600 + i * 110
        pen.fill(rect(x, -300, 70, 900), ('#6a1a1a', '#1a3a5a', '#3a5a2a', '#8a6a2a')[i % 4], 200)
    pen.fill(rect(-700, 600, 3320, 60), '#4a2a16')
    pen.radial(None, 1400, 200, 1600, [(0, '#ffcf8f', 80), (1, '#000000', 160)], clip=False)


def _bg_cabinet(pen, t):
    r = rect(-700, -500, 3320, 2080)
    pen.fill(r, '#140c06'); pen.fill(rect(-700, 260, 3320, 1400), '#5a3820'); pen.texture(rect(-700, 260, 3320, 1400), 'wood', 0.6, 'overlay', 2.0, 0)
    pen.radial(None, 960, 0, 1500, [(0, '#a8c8ff', 70), (1, '#000000', 120)], clip=False)


def _bg_dark(pen, t): pen.fill(rect(-700, -500, 3320, 2080), '#050304')


def _bg_jacket(pen, t):
    r = rect(-700, -500, 3320, 2080)
    pen.linear(r, 0, -500, 0, 1580, ['#2a1a20', '#1a1014']); pen.radial(None, 960, 300, 1300, [(0, '#ffcf8f', 60), (1, '#000000', 0)], clip=False)


GP_INSERTS = {
    'letter': dict(prop=_prop_letter, bg=_bg_table_lamp, pos=(960, 560), scale=0.98, rot=-3, hand=('you', 1310, 940, 330, 'grip', 200.0, -1), grade='face_close'),
    'letter_close': dict(prop=_prop_letter, bg=_bg_table_lamp, pos=(1100, 760), scale=1.9, rot=-3, grade='face_close'),
    'envelope': dict(prop=_prop_envelope, bg=_leather_bg, bgd=1.03, pos=(960, 560), scale=1.0, rot=-4, grade='face_close'),
    'ps': dict(prop=_prop_ps, bg=_bg_dark, pos=(960, 540), scale=1.35, rot=5, hand=('you', 600, 870, 330, 'grip', 150.0, 1), grade='face_close'),
    'latches': dict(prop=_prop_latches, bg=_leather_bg, bgd=1.03, pos=(960, 600), scale=0.85, rot=0, grade='face_close'),
    'case_open': dict(prop=_prop_case_open, bg=_bg_table_lamp, pos=(960, 560), scale=0.78, rot=90, grade='face_close'),
    'mug': dict(prop=_prop_mug, bg=_bg_kitchen_table, pos=(960, 600), scale=1.25, rot=0, grade='gp_house', steam=(960, 330, 1100)),
    'back_slot': dict(prop=_prop_slot, bg=_bg_jacket, pos=(960, 560), scale=0.92, rot=0, grade='face_close', slot=True),
    'squeeze': dict(prop=_prop_squeeze, bg=_bg_dark, pos=(960, 540), scale=0.9, rot=0, grade='gp_dark'),
    'family_photo': dict(prop=_prop_photo_family, bg=_bg_shelf, pos=(960, 560), scale=0.95, rot=2, grade='face_close'),
    'poster_1962': dict(prop=lambda pen, t, **kw: _prop_poster(pen, t, '1962'), bg=_bg_dark, pos=(960, 540), scale=0.95, rot=-2, grade='memory'),
    'vcr': dict(prop=_prop_vcr, bg=_bg_cabinet, pos=(960, 600), scale=1.0, rot=0, grade='tv_glow'),
}


def gp_insert(name, t0=0.0, prop_kw=None, motion=None, hand=None, bg_dim=0.3):
    """Dummy-film inserts (also reachable as insert(name)): close-ups with background DOF (background depth 3 blurred and
    darkened, prop sharp at depth 1, a hand at 0.92). names (GP_INSERTS): letter (the seven rules; prop_kw hl=n lights rule
    n, smear=0..1 runs rule six, show=0..7), letter_close, envelope, ps (the torn P.S.), latches (latch=0..1 or (l, r)),
    case_open (warm=0..1), mug (stir=f(t)->turns, sugar=2; the steam is live), back_slot (hand=0..1, paper=0..1),
    squeeze (squeeze=f(t) 0..1: use squeeze_pulses(); take 0..1: the old hand lets go of the stick and takes yours), family_photo (Walter and Winks '74), poster_1962, vcr (tape=0..1, play).
    motion = f(t) -> (dx, dy, dscale, drot); hand = None (default) | False | (who, x, y, size, shape, angle, side)."""
    spec = GP_INSERTS[name]
    bgd = spec.get('bgd', 3.0)
    L = [Layer(bgd, spec['bg'], 'insert_bg', cache=_key('gpins', name, 'bg'), bounds=(-700, -500, 2620, 1580), dim=bg_dim * (0.4 if bgd < 2 else 1.0))]

    def kw_at(t):
        kw = {}
        if prop_kw: kw.update(prop_kw(t - t0) if callable(prop_kw) else prop_kw)
        return kw

    def pose(t):
        x, y = spec['pos']; s = spec['scale']; r = spec['rot']
        if motion:
            dx, dy, ds, dr = motion(t - t0); x += dx; y += dy; s *= (1 + ds); r += dr
        return x, y, s, r

    def prop(pen, t):
        x, y, s, r = pose(t)
        pen.cv.save(); pen.cv.translate(x, y); pen.cv.rotate(r); pen.cv.scale(s, s)
        spec['prop'](pen, t - t0, **kw_at(t))
        pen.cv.restore()
    L.append(Layer(1.0, prop, 'insert_prop', blur=0))
    if spec.get('slot'):
        for part, d in (('out', 0.995), ('in', 0.99)):
            fn = _slot_hand(part)

            def sl(pen, t, fn=fn):
                x, y, s, r = pose(t)
                pen.cv.save(); pen.cv.translate(x, y); pen.cv.rotate(r); pen.cv.scale(s, s); fn(pen, t, kw_at(t)); pen.cv.restore()
            L.append(Layer(d, sl, 'insert_hand_' + part, blur=0))
    if spec.get('steam'):
        sx, sy, ss = spec['steam']
        L.append(Layer(0.98, lambda pen, t: _steam(pen, sx, sy, ss, t, 1.0, 9), 'insert_steam', blur=0))
    hs = spec.get('hand') if hand is None else hand
    if hs:
        who, hx, hy, hsz, shp, ang, side = hs

        def hand_fn(pen, t):
            x, y, s, r = pose(t)
            dx, dy = x - spec['pos'][0], y - spec['pos'][1]
            CHm = _CH()
            if CHm is not None:
                CHm.draw_hand(pen, who, hx + dx, hy + dy, hsz, shp, ang, side)
            else:
                draw_hand(pen, hx + dx, hy + dy, hsz / 330.0, ang - 180, 'hold', side=side)
        L.append(Layer(0.92, hand_fn, 'insert_hand', blur=0))
    return SetPiece('insert:' + name, L, {}, {}, lens=None, grade=spec.get('grade', 'face_close'), focus=1.0, dof=6.75, cover=FRAME,
                    info={'spec': spec, 'pose': pose})


def squeeze_pulses(times, dur=0.42):
    """f(t) -> 0..1 for the squeeze insert / the cast: one quick squeeze (grip in 0.12 s, release) at each time."""
    def f(t):
        v = 0.0
        for t0 in times:
            u = t - t0
            if 0 <= u < dur: v = max(v, math.sin(math.pi * clamp(u / dur)) ** 0.7)
        return v
    return f


# ---------------------------------------------------------------------------------------------- the rule card that lies
def _rule_card_picture(n, text_, t, **kw):
    from engine import hud as _H
    rec = skia.PictureRecorder()
    c2 = rec.beginRecording(skia.Rect.MakeLTRB(-200, -200, DW + 200, DH + 200))
    _H.rule_card(c2, n, text_, t, scrim=0.0, **kw)
    return rec.finishRecordingAsPicture()


def _tear_path(y0, seed=6, amp=9.0):
    rng = np.random.default_rng(seed)
    pts = [(-400, y0)]
    x = -400.0
    while x < DW + 400:
        x += rng.uniform(22, 54)
        pts.append((x, y0 + rng.uniform(-amp, amp) + 0.012 * (x - DW / 2)))
    return pts


def rule_card_lie(cv, n, text_, t, reveal=None, mode='tear', scrim=0.35, alpha=255, y=0.0, **kw):
    """The police rule card (engine.hud.rule_card) for the rule that LIES, with its damage when the lie comes out.
    t = seconds since the card appeared (as rule_card); reveal = the card-clock second the lie is revealed (None = an
    intact card). mode:
      'tear'    the card rips along a jagged line through its first text line: the halves slide apart and tilt, a red
                seam glows in the gap, the frame jolts for two frames (u = 0..1 over 0.45 s after reveal)
      'smear'   the ink runs: the rule's words drip down the screen in long streaks and 'LIE' is scrawled across it in
                Grandpa's shaky red hand
      'flicker' a two-frame glitch with 'LIE?' (rule two, when the thing CLAIMS it is the lie: a false lead)
    Draw it on the HUD canvas (design coordinates) like rule_card; the hard cut / sting is the cue sheet's job (cue
    'rule_lie' at the reveal)."""
    if t < 0: return
    pen = Pen(cv)
    if scrim:
        pen.radial(None, DW / 2, DH / 2 + y, 900, [(0, '#000000', 255 * scrim), (1, '#000000', 255 * scrim * 0.45)], sy=0.75)
    pic = _rule_card_picture(n, text_, t, alpha=alpha, y=y, **kw)
    u = 0.0 if reveal is None or t < reveal else clamp((t - reveal) / 0.45)
    if mode == 'tear' and u > 0:
        e = ease_out_back(u, 1.2)
        ty = 661 + y
        pts = _tear_path(ty, 6 + n)
        top = poly([(-400, -400)] + pts + [(DW + 400, -400)])
        bot = poly([(-400, DH + 400)] + pts + [(DW + 400, DH + 400)])
        jolt = (9 * math.sin(t * 90) if u < 0.12 else 0.0)
        for path, dx, dy, rot in ((top, -26 * e + jolt, -34 * e, -2.2 * e), (bot, 30 * e - jolt, 46 * e, 3.0 * e)):
            cv.save()
            cv.translate(DW / 2 + dx, ty + dy); cv.rotate(rot); cv.translate(-DW / 2, -ty)
            cv.clipPath(path, skia.ClipOp.kIntersect, True)
            cv.drawPicture(pic)
            cv.restore()
        seam = poly([p for p in pts if 330 < p[0] < DW - 330], False)
        cv.save(); cv.clipRect(skia.Rect.MakeLTRB(330, -400, DW - 330, DH + 400))
        pen.line(seam, 10 + 18 * e, '#ff2a2a', 90 * e, blur=10)
        pen.line(seam, 2.5, '#ff6a5a', 200 * e)
        cv.restore()
        return
    if mode == 'smear' and u > 0:
        cv.drawPicture(pic)
        rng = np.random.default_rng(60 + n)
        for i in range(18):                                                    # the letters run: tapered drips
            x = DW / 2 - 360 + rng.uniform(0, 720)
            y0 = 650 + y + rng.uniform(-10, 50)
            ln = (40 + 300 * rng.uniform() ** 1.6) * ease_in_out(u)
            wdt = rng.uniform(3.0, 8.0)
            drip = poly([(x - wdt / 2, y0), (x + wdt / 2, y0), (x + wdt * 0.25, y0 + ln), (x - wdt * 0.25, y0 + ln)])
            pen.fill(drip, '#f2f2f2', 210); pen.fill(oval(x, y0 + ln, wdt * 0.5, wdt * 0.75), '#f2f2f2', 230)
        cv.save(); cv.translate(DW / 2 - 330, 720 + y); cv.rotate(-6)
        k = clamp((t - reveal - 0.15) / 0.5)
        if k > 0:
            cv.saveLayer(None, skia.Paint(Alphaf=k))
            shaky_text(pen, 'LIE', 0, 0, 230, c='#d8262e', a=255, seed=666, shake=2.2, w=10)
            cv.restore()
        cv.restore()
        return
    if mode == 'flicker' and reveal is not None and 0 <= t - reveal < 0.12:
        cv.save(); cv.translate(14 * math.sin(t * 200), 0); cv.drawPicture(pic); cv.restore()
        text(cv, 'LIE?', DW / 2 + 260, 470 + y, 900, 64, '#d8262e', 230, 0.1)
        return
    cv.drawPicture(pic)


# ---------------------------------------------------------------------------------------------- dummy-film registry
SETS.update({'gp_hall': gp_hall, 'gp_kitchen': gp_kitchen, 'gp_living': gp_living, 'gp_den': gp_den, 'gp_studio': gp_studio,
             'hospital': hospital, 'museum': museum, 'street_morning': street_morning, 'stage_1962': stage_1962,
             'bedroom_doorway': bedroom_doorway})
__all__ += ['HView', 'gp_hall', 'gp_kitchen', 'gp_living', 'gp_den', 'gp_studio', 'hospital', 'museum', 'street_morning', 'stage_1962',
            'bedroom_doorway', 'gp_insert', 'GP_INSERTS', 'rule_card_lie', 'shaky_text', 'laugh_waves', 'studio_content', 'squeeze_pulses',
            'monitor_beeps', 'ecg', 'pendulum_ticks', 'tv_level', 'museum_van', 'LETTER_RULES', 'PS_TEXT']


# ---------------------------------------------------------------------------------------------- Bunnyman film additions
# The Bunnyman film's sets (the Orchard Road house on one floor plan, the yard and the treeline, the woods and the bridge,
# 1987, the hospital, the inserts) live in sets_bunny.py, run here in this module's namespace (so they are part of `sets`).
# See its docstring and SETS.md.
_BUNNY_SETS_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sets_bunny.py')
exec(compile(open(_BUNNY_SETS_SRC).read(), _BUNNY_SETS_SRC, 'exec'))
