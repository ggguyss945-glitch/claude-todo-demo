# sfx_walls.py: THIS film's SFX block ("If Your Little Brother Says Someone Lives In The Walls... DON'T LAUGH").
# Run inside sfx.py's namespace (sfx.py execs it after sfx_ice.py, just before RECIPES), so it uses sfx.py's helpers
# directly (src, pool, grains, audio, excerpt, reverb, eq, lp, hp, bp, modal, noise, fade, pnorm, place, _seq, rate,
# pan, st, mono, onset_s, peak) and the earlier films' recipes (r_deadbolt, r_bulb, r_cloth_rustle, ...). Sources: the
# linked libraries first (W/samples: the police set's crickets, heavy shoes on wood, the deadbolt; the mirror set's
# wrappers, metal gate rattle, wooden stairs; the ice set's sliding wood windows, friction scrape; the dummy set's metal
# clicks; the free CC0 / CC-BY files of catalog.json: Oculus fan loops, owlishmedia pencil and cloth, VSCO ratchet);
# synthesis only where nothing fits or as a layer (chewing, the snore, nail stick-slip, sheet-metal modes, keypad
# beeps, the garage opener). Every source and licence: audio/ATTRIBUTION.md ("The Walls film").
#
# NAMES the picture emits (film.py sfx cues {t, name, gain_db, pan, params, space}); params in brackets.
#   inside the walls  wall_scratch [dur, travel (p0, p1), nails 0..1] (nails dragging on studs and lath behind the
#                     plaster), wall_crawl [dur, speed, travel] (crawling fast inside the wall: hand / knee thumps on
#                     the studs, the body dragging, a stud creaking), chewing [dur, rate] (slow, careful chewing behind
#                     the pantry plaster), wall_knock (alias: knock_door through the wall)
#   kitchen           deadbolt_slow [dur] (the bolt turning slowly by itself, then the Click: the click lands ON the
#                     cue: pre_s = dur), bread_bag [kind twist|open|fold, dur] (the bread bag twisted shut)
#   hall / attic      light_switch (the hall switch: the earlier films' recipe), attic_light [dur] (the sealed attic's
#                     bulb coming on above: the filament's tink and its buzz, through the ceiling), bulb kind=buzz
#   bedroom           closet_slide [action open|close, speed] (the closet's back panel sliding), vent_rattle [dur]
#                     (the floor vent's grille rattling), pencil_mark [strokes] (a pencil on the doorframe), snore [n]
#                     (Dad snoring down the hall, through the open door)
#   night             august_night [dur, fans, crickets, inside] (BED: crickets through the window screens, box fans
#                     in the windows), box_fan [dur] (BED: one fan)
#   the call / police dial_911 (the earlier recipe: the keys 9-1-1, ring-back, pickup), sirens_arrive [n_cars]
#                     (alias 'sirens': three cars), boots_stairs [dur, officers, direction] (heavy boots up the stairs),
#                     handcuffs (the ratchets closing, the chain)
#   garage            keypad [n, accepted] (the old code's keys and beeps), garage_door [dur, action] (the opener)
#   aliases           scratching, crawling, deadbolt_turn, bag_twist, chew, attic_bulb, closet_panel, floor_vent,
#                     pencil, crickets, fans, phone_911, sirens, boots, cuffs, dad_snore, mask_off ... (WALLS_ALIASES)
# Spaces added: 'in_wall' (inside the wall right by the listener: plaster and studs, the cavity's boom, close and
# dull), 'in_wall_far' (further along the wall), 'vent' (through the floor vent's sheet-metal duct).
# Owner, 23 Nov: every recipe eases its own edges (fade() / ramps) and render_event() applies fade() again at the end;
# everyday foley sits under the voice (LEVEL_LU <= -6 here); none of these is a scare hit.

WALLS_NAMES = ('wall_scratch', 'wall_crawl', 'chewing', 'deadbolt_slow', 'bread_bag', 'attic_light', 'closet_slide',
               'vent_rattle', 'pencil_mark', 'snore', 'august_night', 'box_fan', 'boots_stairs', 'handcuffs', 'keypad',
               'garage_door')
NAMES = NAMES + WALLS_NAMES
LEVEL_LU.update(wall_scratch=-9, wall_crawl=-7, chewing=-13, deadbolt_slow=-10, bread_bag=-10, attic_light=-16,
                closet_slide=-8, vent_rattle=-6, pencil_mark=-12, snore=-10, august_night=-27, box_fan=-29,
                boots_stairs=-6, handcuffs=-9, keypad=-10, garage_door=-11)
PEAK_CAP.update(vent_rattle=-6.0, boots_stairs=-6.0, wall_crawl=-6.0)
BEDS = BEDS + ('august_night', 'box_fan')
BED_BUS = BED_BUS + ('august_night', 'box_fan')
DUR_BEDS = DUR_BEDS + ('attic_light',)
WALLS_PHONE_FIX = ('wall_crawl', 'boots_stairs', 'closet_slide')
SPACE_LU.update(in_wall=-3.0, in_wall_far=-6.0, vent=-2.0)
SPACE_ALIAS.update(wall='in_wall', walls='in_wall', inside_wall='in_wall', pantry='in_wall', pantry_wall='in_wall',
                   plaster='in_wall', behind_wall='in_wall', bedroom_wall='in_wall', far_wall='in_wall_far',
                   along_wall='in_wall_far', duct='vent', grille='vent', floor_vent='vent', bedroom='close',
                   parents_room='close', boys_room='close', closet='next_room', hall_closet='next_room',
                   down_the_hall='inside', upstairs_hall='inside', garage='next_room', lawn='street', curb='street')
SPACES = tuple(SPACE_LU)
DEFAULT_SPACE.update(wall_scratch='in_wall', wall_crawl='in_wall', chewing='in_wall', deadbolt_slow='close',
                     bread_bag='close', attic_light='attic_above', closet_slide='next_room', vent_rattle='close',
                     pencil_mark='close', snore='inside', august_night='dry', box_fan='dry', boots_stairs='inside',
                     handcuffs='close', keypad='close', garage_door='close')


def _space_walls(y, kind, seed=0, wet=None):
    if kind == 'in_wall':                               # plaster and studs right by the bed: dull, the cavity's boom
        x = hp(lp(y, 1700, 2), 70, 2)
        x = eq(x, ('peak', 160, 4.0, 1.2), ('peak', 520, 2.0, 1.5), ('hs', 1200, -5.0, 0.7))
        return reverb(x, 'box', 0.22 if wet is None else wet, 0.002)
    if kind == 'in_wall_far':                           # further along the wall: duller, the stud bays between
        x = hp(lp(y, 1000, 2), 80, 2)
        x = eq(x, ('peak', 140, 3.0, 1.2), ('hs', 800, -6.0, 0.7))
        return reverb(x, 'box', 0.35 if wet is None else wet, 0.004)
    if kind == 'vent':                                  # the floor vent: a sheet-metal duct, a tin ring
        x = eq(bp(y, 250, 3000, 2), ('peak', 1100, 6.0, 4.0), ('peak', 2400, 4.0, 5.0))
        d = n_(0.0065); fl = np.zeros_like(x); fl[d:] = x[:-d] * 0.4
        return reverb(x + fl, 'box', 0.25 if wet is None else wet, 0.001)
    return None


_space_prev_walls = space


def space(y, kind, seed=0, wet=None):             # noqa: F811 (this film's spaces first, then every earlier one)
    r = _space_walls(st(y), kind, seed, wet)
    return r if r is not None else _space_prev_walls(y, kind, seed, wet)


# ---------------------------------------------------------------------------------------------------- helpers
def _wp(key, has, mode='onset', **seg):
    """A grain pool over the library files whose id holds any of `has` (no 'serves' needed)."""
    return pool('walls_' + key, lambda: src(has=list(has)), mode, **seg)


def _add(*ys):
    """Sum stereo sounds of different lengths (zero-padded to the longest)."""
    ys = [st(y) for y in ys]
    out = np.zeros((max(len(y) for y in ys), 2), np.float32)
    for y in ys:
        out[:len(y)] += y
    return out


def _travel(y, p0, p1):
    """Pan a stereo sound from p0 to p1 (-1 left .. 1 right), equal power."""
    m = mono(st(y)); th = (np.linspace(p0, p1, len(m)) + 1) * np.pi / 4
    return np.stack([m * np.cos(th), m * np.sin(th)], 1).astype(np.float32)


def _env(n, a, r):
    e = np.ones(n, np.float32); a, r = min(n // 2, n_(a)), min(n // 2, n_(r))
    if a > 1: e[:a] = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    if r > 1: e[-r:] = np.cos(np.linspace(0, np.pi / 2, r)) ** 2
    return e


def _thump(rng, f=120.0, d=0.18, amp=1.0):
    """A soft body on a stud: a low modal thump with a dull tap on top."""
    s = int(rng.integers(1 << 30))
    y = modal([f, f * 1.6, f * 2.7], [0.06, 0.04, 0.02], [1.0, 0.5, 0.2], d, s)
    tap = lp(noise(0.012, s + 1), 1800, 2) * np.hanning(n_(0.012))
    y[:len(tap)] += tap * 0.3
    return st(y.astype(np.float32)) * amp


def _metal_tick(rng, base=1.0, d=0.06):
    s = int(rng.integers(1 << 30))
    f = np.array([2350.0, 3900.0, 5700.0, 7400.0]) * base * rng.uniform(0.95, 1.05)
    return st(modal(list(f), [0.03, 0.02, 0.012, 0.008], [1.0, 0.6, 0.35, 0.2], d, s, exc=0.0003))


# ---------------------------------------------------------------------------------------------------- inside the walls
def r_wall_scratch(rng, sp, dur=3.0, travel=None, nails=1.0, **_):
    """Nails dragging on studs and lath behind the plaster: strokes of stick-slip friction (an impulse train at
    60-160 Hz through a 0.9-5 kHz band, one resonant peak per stroke) over the ice set's thumb-on-ribbon friction,
    pauses between strokes, now and then the knuckles bump a stud. travel (p0, p1) moves it along the wall."""
    d = max(0.6, float(dur)); out = np.zeros((n_(d) + n_(0.4), 2), np.float32)
    try:
        fr = bp(excerpt(_pick(rng, src(has=['scrape_ribbon_friction'])), d, rng), 700, 5000, 2) * 0.5
        place(out, fr, 0)
    except (KeyError, ValueError, IndexError):
        pass
    t = rng.uniform(0.0, 0.12)
    while t < d - 0.15:
        L = rng.uniform(0.18, 0.6); n = n_(L); s = int(rng.integers(1 << 30))
        imp = (rng.random(n) < rng.uniform(60, 160) / SR).astype(np.float32) * rng.uniform(0.4, 1.0, n).astype(np.float32)
        g = bp(noise(L, s)[:n] * 0.25 + imp, 900, 5200, 2)
        g = eq(g, ('peak', rng.uniform(1600, 3400), 6.0, 2.5))
        env = np.sin(np.pi * np.linspace(0, 1, n)) ** 0.5
        place(out, st(g * env * float(nails) * rng.uniform(0.6, 1.0)), n_(t))
        if rng.random() < 0.25:
            place(out, _thump(rng, rng.uniform(110, 160), 0.15, 0.5), n_(t))
        t += L + rng.uniform(0.04, 0.35)
    if travel:
        out = _travel(out, float(travel[0]), float(travel[1]))
    return fade(pnorm(out), 0.06, 0.25), 0.0, 0.0, False


def r_wall_crawl(rng, sp, dur=3.0, speed=1.0, travel=(-0.7, 0.7), **_):
    """Crawling fast inside the wall: hands and knees thumping the studs in a quick uneven gait (2.5-4 per second x
    speed), the body dragging (cloth through a dark band), a stud creaking once or twice; travel (p0, p1) along it."""
    d = max(0.8, float(dur)); out = np.zeros((n_(d) + n_(0.5), 2), np.float32)
    t = 0.05; k = 0
    while t < d - 0.1:
        f = rng.uniform(95, 150) if k % 2 else rng.uniform(140, 200)          # hand (lighter), knee (heavier)
        place(out, _thump(rng, f, 0.16, rng.uniform(0.55, 1.0) * (1.0 if k % 2 else 0.75)), n_(t))
        t += (1.0 / (3.2 * float(speed))) * rng.uniform(0.55, 1.25) * (0.6 if k % 2 == 0 else 1.0)
        k += 1
    try:
        cl = r_cloth_rustle(rng, sp, dur=d)[0]
        place(out, lp(st(cl), 1500, 2) * 0.6, 0)
    except Exception:
        place(out, st(bp(noise(d, int(rng.integers(1 << 30))), 200, 1400, 2)) * 0.08, 0)
    try:
        C = pool('door_creak', lambda: src('door_creak', category='sfx/door_creak'), 'phrase', gap=0.2, max_len=4.0,
                 keep=-18)
        for _k in range(1 + int(d > 2.5)):
            place(out, lp(rate(C.get(rng, rj=0.05, fo=0.2), 0.7), 1800, 2)[:n_(0.9)] * 0.45, n_(rng.uniform(0.1, d - 0.8)))
    except Exception:
        pass
    if travel:
        out = _travel(out, float(travel[0]), float(travel[1]))
    return fade(pnorm(out), 0.03, 0.2), 0.0, 0.0, False


def r_chewing(rng, sp, dur=4.0, rate_=1.25, **kw):
    """Slow, careful chewing behind the pantry plaster: each jaw cycle a soft wet squelch (a 300-1500 Hz burst, 40 ms
    in, 130 ms out), a crumb's dry crackle now and then, the jaw's dull knock; a pause, a swallow."""
    d = max(1.0, float(dur)); r_ = float(kw.get('rate', rate_)); out = np.zeros((n_(d) + n_(0.4), 2), np.float32)
    t = rng.uniform(0.05, 0.2); k = 0
    while t < d - 0.25:
        s = int(rng.integers(1 << 30)); L = 0.2
        g = bp(noise(L, s), rng.uniform(280, 380), rng.uniform(1200, 1700), 2)
        e = np.concatenate([np.linspace(0, 1, n_(0.04)) ** 2, np.exp(-np.arange(n_(L) - n_(0.04)) / (0.045 * SR))])
        y = st(g[:len(e)] * e) * rng.uniform(0.6, 1.0)
        if rng.random() < 0.45:                                              # a crumb
            c = hp(noise(0.03, s + 2), 2500, 2) * (rng.random(n_(0.03)) < 0.08)
            y[:len(c)] += st(c) * 0.25
        place(out, y, n_(t)); place(out, _thump(rng, rng.uniform(85, 110), 0.1, 0.25), n_(t + 0.01))
        k += 1
        t += (1.0 / r_) * rng.uniform(0.85, 1.2) + (rng.uniform(0.5, 1.0) if k % 6 == 0 else 0.0)
    return fade(pnorm(out), 0.05, 0.3), 0.0, 0.0, False


def r_snore(rng, sp, n=2, depth=1.0, **_):
    """Dad snoring down the hall: the soft palate fluttering on the in-breath (a 28-36 Hz pulse train through a
    nasal-throat band, swelling and falling over ~1.4 s), a soft breathy out-breath, a pause; n cycles."""
    ev, t = [], 0.0
    for _k in range(max(1, int(n))):
        s = int(rng.integers(1 << 30)); L = rng.uniform(1.2, 1.6); m = n_(L); tt = np.arange(m) / SR
        f0 = rng.uniform(28, 36) * (1 + 0.08 * np.sin(2 * np.pi * 0.7 * tt))
        ph = np.cumsum(f0) / SR
        pulse = (0.5 + 0.5 * np.cos(2 * np.pi * ph)) ** 6
        z = noise(L, s)[:m] * pulse
        z = eq(bp(z, 90, 1300, 2), ('peak', 300, 6.0, 1.5), ('peak', 650, 4.0, 2.0), ('peak', 1100, 2.0, 3.0))
        z = lp(z, 1600, 2) * np.sin(np.pi * np.linspace(0, 1, m)) ** 1.2 * float(depth)   # a throat, not a hiss
        out_b = lp(noise(1.0, s + 3), 1100, 2) * np.sin(np.pi * np.linspace(0, 1, n_(1.0))) ** 2 * 0.12
        ev += [(t, st(z)), (t + L + 0.15, st(out_b))]
        t += L + 1.3 + rng.uniform(0.5, 0.9)
    return fade(pnorm(_seq(ev, 0.3)), 0.05, 0.3), 0.0, 0.0, False


# ---------------------------------------------------------------------------------------------------- kitchen
def r_deadbolt_slow(rng, sp, dur=2.2, **_):
    """The deadbolt on the garage door turning SLOWLY, all by itself, from the other side: the police set's
    deadbolt turn slowed (the thumb-turn's grind), a faint metal friction under it, then the Click (the dummy set's
    metal click on top of the bolt's own seat). pre_s = the click: the cue time is "Click."."""
    d = max(0.8, float(dur))
    g = r_deadbolt(rng, sp, action='slide')[0]
    turn = rate(g, 0.55)[:n_(d)]
    turn = turn * _env(len(turn), 0.25, 0.08)[:, None]
    gr = st(bp(noise(d, int(rng.integers(1 << 30))), 1200, 4200, 2) * np.sin(np.pi * np.linspace(0, 1, n_(d))) ** 2) * 0.02
    try:
        ck = _wp('mclick', ['metal_click_close'], 'onset', gap=0.12, max_len=0.25, keep=-18).get(rng, rj=0.02, fo=0.03)
    except KeyError:
        ck = _metal_tick(rng, 0.8, 0.08)
    ck = _add(pnorm(ck) * 0.9, _metal_tick(rng, 0.6, 0.07) * 0.3)
    y = _seq([(0.0, turn * 0.6), (0.0, gr), (d, ck)], 0.4)
    return y, d + onset_s(ck, -12), 0.0, False


def r_bread_bag(rng, sp, kind='twist', dur=1.4, **_):
    """The bread bag: 'twist' (twisted shut: crinkles accelerating with the turns), 'open' (untwisted, opened), 'fold'
    (folded neatly: slower, softer). The mirror set's wrapper crinkles slowed (a bigger bag) over a synthesised crinkle
    (sparse clicks high-passed 2.5-9 kHz, their density following the hands)."""
    d = max(0.5, float(dur)); n = n_(d); s = int(rng.integers(1 << 30))
    dens = {'twist': np.linspace(0.3, 1.0, n) ** 1.5, 'open': np.linspace(1.0, 0.4, n), 'fold': np.full(n, 0.35)}[
        kind if kind in ('twist', 'open', 'fold') else 'twist']
    clicks = (rng.random(n) < 0.004 * dens).astype(np.float32) * rng.uniform(0.2, 1.0, n).astype(np.float32)
    cr = bp(clicks + noise(d, s)[:n] * 0.04 * dens, 2500, 9000, 2)
    cr = eq(cr, ('peak', 4200, 3.0, 1.0)) * np.sin(np.pi * np.linspace(0, 1, n)) ** 0.4
    y = st(cr)
    try:
        E = src(has=['candy_in_wrapper', 'wrapper_lollipop'])
        w = rate(excerpt(_pick(rng, E), d / 0.75, rng), 0.75)[:n]
        y[:len(w)] += hp(w, 400, 2) * 0.8
    except (KeyError, ValueError, IndexError):
        pass
    return fade(pnorm(y), 0.04, 0.12), 0.0, 0.0, False


# ---------------------------------------------------------------------------------------------------- hall / attic
def r_attic_light(rng, sp, dur=4.0, **_):
    """The sealed attic's bare bulb coming on above the hall (the dead switch): the filament's tink, its buzz rising
    over 0.4 s and holding for dur (r_bulb's 120 Hz buzz and whine)."""
    d = max(1.0, float(dur))
    b = r_bulb(rng, sp, kind='buzz', dur=d)[0]
    b = b * np.concatenate([np.linspace(0, 1, n_(0.4)) ** 2, np.ones(len(b) - n_(0.4))])[:, None]
    tink = st(modal([4300.0, 6300.0, 9100.0], [0.04, 0.02, 0.01], [1.0, 0.5, 0.2], 0.12, int(rng.integers(1 << 30)),
                    exc=0.0002)) * 0.08
    return fade(_seq([(0.0, tink), (0.005, b * 6.0)], 0.1), 0.0, 0.3), 0.0, 0.0, False


# ---------------------------------------------------------------------------------------------------- bedroom
def r_closet_slide(rng, sp, action='open', speed=1.0, **_):
    """The closet's back panel sliding in its track: the ice set's wooden sliding-window takes slowed (a heavier,
    wider panel), the panel's low rumble, its bump as it seats; 'close' ends on the seat."""
    sp_ = max(0.3, float(speed))
    try:
        P = _wp('wslide', ['windows_wood_sliding'], 'phrase', gap=0.3, max_len=1.6, keep=-16)
        g = rate(P.get(rng, rj=0.03, fo=0.1), 0.72 * sp_)
    except KeyError:
        g = st(bp(noise(1.4, int(rng.integers(1 << 30))), 300, 2500, 2)) * 0.2
    L = len(g) / SR
    rum = st(lp(noise(L, int(rng.integers(1 << 30))), 260, 2)) * np.sin(np.pi * np.linspace(0, 1, len(g)))[:, None] * 0.35
    bump = _thump(rng, 125, 0.22, 0.7)
    ev = [(0.0, g), (0.0, rum), (L - 0.05, bump)] if action != 'open' else [(0.0, bump * 0.4), (0.04, g), (0.04, rum)]
    y = _seq(ev, 0.3)
    return fade(y, 0.02, 0.2), 0.0, 0.0, False


def r_vent_rattle(rng, sp, dur=1.2, **_):
    """The floor vent's grille rattling: the mirror set's metal gate rattle (high-passed, sped up: a smaller, thinner
    metal) and 2-3 bursts of sheet-metal ticks (15-30 per second) as the grille shivers in its frame."""
    d = max(0.4, float(dur)); out = np.zeros((n_(d) + n_(0.3), 2), np.float32)
    try:
        g = hp(rate(excerpt(_pick(rng, src(has=['gate_metal_open_close_rattle'])), d / 1.35, rng), 1.35), 500, 2)[:n_(d)]
        place(out, g * 0.7, 0)
    except (KeyError, ValueError, IndexError):
        pass
    t = 0.0
    for _b in range(int(rng.integers(2, 4))):
        L = rng.uniform(0.15, 0.35); rt = rng.uniform(15, 30); tt = t
        while tt < min(d, t + L):
            place(out, _metal_tick(rng, rng.uniform(0.25, 0.4), 0.05) * rng.uniform(0.4, 1.0), n_(tt))
            tt += 1.0 / rt * rng.uniform(0.6, 1.4)
        t += L + rng.uniform(0.08, 0.3)
        if t > d - 0.1:
            break
    return fade(pnorm(out), 0.01, 0.15), 0.0, 0.0, False


def r_pencil_mark(rng, sp, strokes=3, **_):
    """A pencil on the doorframe: the graphite touching the painted wood (a tiny tap), then strokes (the owlishmedia
    CC0 pencil-on-paper takes cut to 0.15-0.4 s, the paper's hiss taken down, a woody low-mid)."""
    ev, t = [], 0.0
    try:
        P = _wp('pencil', ['paper_pencil_scratch'], 'phrase', gap=0.08, max_len=0.5, keep=-20)
    except KeyError:
        P = None
    for k in range(max(1, int(strokes))):
        if k == 0:
            ev.append((0.0, _thump(rng, 900, 0.03, 0.15)))
        if P is not None and len(P):
            g = P.get(rng, rj=0.05, fo=0.04)[:n_(rng.uniform(0.15, 0.4))]
        else:
            g = st(bp(noise(0.3, int(rng.integers(1 << 30))), 1500, 6000, 2)) * 0.2
        g = eq(hp(g, 400, 2), ('peak', 1200, 3.0, 1.0), ('hs', 7000, -6.0, 0.7))
        ev.append((t + 0.03, fade(g, 0.01, 0.04)))
        t += len(g) / SR + rng.uniform(0.08, 0.22)
    return fade(_seq(ev, 0.2), 0.0, 0.1), 0.02, 0.0, False


# ---------------------------------------------------------------------------------------------------- night
def _fan(rng, d, rr=1.0):
    try:
        y = excerpt(_pick(rng, src(has=['machfan_fan_loop'])), d / rr + 0.2, rng, 2.0)
        return rate(y, rr)[:n_(d)]
    except (KeyError, ValueError, IndexError):            # synth: blade pass at ~23 Hz on a dark noise
        n = n_(d); tt = np.arange(n) / SR
        z = lp(noise(d, int(rng.integers(1 << 30))), 900, 2) * (1 + 0.3 * np.sin(2 * np.pi * 23 * rr * tt))
        return st(z * 0.2)


def r_box_fan(rng, sp, dur=20.0, **_):
    """BED: one box fan in a window (the Oculus CC-BY fan loop, looped with crossfades)."""
    return fade(_fan(rng, float(dur)), 0.6, 0.8), 0.0, 0.0, False


def r_august_night(rng, sp, dur=30.0, fans=1.0, crickets=1.0, inside=True, **_):
    """BED: an August night in the heat wave: crickets (the police set's suburban night crickets) through the open
    window screens, two box fans in the windows (slightly different speeds, left and right), the far suburb.
    inside=False: out on the porch (crickets full, the fans muffled behind the windows)."""
    d = float(dur)
    try:
        E = src(has=['suburban_night_evening_ambience_crickets', 'suburban_night_crickets_distant'])
        c = excerpt(_pick(rng, E), d, rng, 2.0)
    except (KeyError, ValueError, IndexError):
        c = st(bp(noise(d, int(rng.integers(1 << 30))), 3800, 5200, 2)) * 0.05
    if inside:
        c = eq(lp(c, 5500, 2), ('hs', 3000, -3.0, 0.7)) * 0.5
    f1, f2 = _fan(rng, d, 0.97), _fan(rng, d, 1.04)
    fs = _add(pan(f1, -0.6), pan(f2, 0.5)) * (0.6 if inside else 0.18)
    if not inside:
        fs = lp(fs, 900, 2)
    y = _add(c * float(crickets), fs * float(fans))
    return fade(y, 0.8, 1.0), 0.0, 0.0, False


# ---------------------------------------------------------------------------------------------------- police
def r_boots_stairs(rng, sp, dur=3.0, officers=2, direction='up', **_):
    """Heavy boots on the wooden stairs: officers hurrying up (the police set's heavy shoes on wood, each step with
    the tread's low boom; a tread creaking now and then), each officer a stream ~3 steps per second, offset; 'up'
    comes nearer (louder) over dur, 'down' goes away."""
    d = max(0.8, float(dur)); out = np.zeros((n_(d) + n_(0.6), 2), np.float32)
    try:
        P = _wp('boots', ['shoes_wood_heavy', 'running_over_wood_stairs'], 'onset', gap=0.15, max_len=0.35, keep=-16)
    except KeyError:
        P = None
    for o in range(max(1, int(officers))):
        t = 0.08 + o * rng.uniform(0.12, 0.3); p = rng.uniform(-0.3, 0.3)
        while t < d - 0.1:
            if P is not None and len(P):
                g = P.get(rng, rj=0.04, fo=0.05) * rng.uniform(0.7, 1.0)
            else:
                g = st(bp(noise(0.08, int(rng.integers(1 << 30))), 200, 3000, 2)) * 0.5
            g = _add(g, _thump(rng, rng.uniform(80, 110), 0.2, 0.6))
            prog = t / d
            gain = (0.45 + 0.55 * prog) if direction == 'up' else (1.0 - 0.55 * prog) if direction == 'down' else 1.0
            place(out, pan(g, p) * gain, n_(t))
            t += (1 / 3.0) * rng.uniform(0.85, 1.15)
    return fade(pnorm(out), 0.02, 0.25), 0.0, 0.0, False


def r_handcuffs(rng, sp, n=2, **_):
    """Handcuffs closing: per cuff a ratchet run (the VSCO CC0 ratchet's clicks, high-passed and short; 5-7 clicks at
    ~25 ms) with a hard metal tick on top, the chain's clink between the cuffs."""
    ev, t = [], 0.0
    try:
        P = _wp('ratchet', ['ratchet1_slow', 'ratchet1_fast'], 'onset', gap=0.015, max_len=0.04, keep=-20)
    except KeyError:
        P = None
    for c in range(max(1, int(n))):
        for k in range(int(rng.integers(5, 8))):
            g = hp(P.get(rng, rj=0.03, fo=0.005), 1500, 2) if (P is not None and len(P)) else _metal_tick(rng, 1.2, 0.03)
            ev.append((t, _add(g * 0.5, _metal_tick(rng, 1.4, 0.03) * 0.35)))
            t += rng.uniform(0.02, 0.03)
        t += 0.08
        for k in range(3):
            ev.append((t + k * rng.uniform(0.04, 0.07), _metal_tick(rng, 0.9, 0.08) * 0.5))
        t += rng.uniform(0.35, 0.6)
    return fade(_seq(ev, 0.2), 0.0, 0.1), 0.0, 0.0, False


# ---------------------------------------------------------------------------------------------------- garage
def r_keypad(rng, sp, n=4, accepted=True, **_):
    """The garage keypad: n soft rubber keys (a dull click and a tiny plastic tick), each with its 2.4 kHz beep
    (90 ms), then (accepted) the double beep."""
    ev, t = [], 0.0
    tt = np.arange(n_(0.09)) / SR
    beep = st(np.sin(2 * np.pi * 2400 * tt) * _env(len(tt), 0.004, 0.01)) * 0.25
    for k in range(max(1, int(n))):
        ev += [(t, _add(_thump(rng, 700, 0.03, 0.2), _metal_tick(rng, 0.7, 0.015) * 0.1)), (t + 0.02, beep)]
        t += rng.uniform(0.35, 0.5)
    if accepted:
        ev += [(t + 0.1, beep), (t + 0.25, beep)]
    return fade(_seq(ev, 0.2), 0.0, 0.05), 0.0, 0.0, False


def r_garage_door(rng, sp, dur=6.0, action='open', **_):
    """The garage door opener: the motor's hum (90 Hz and its harmonics, a slight wobble), the chain drive's clatter,
    the door panels rumbling over the rollers (a bump at each panel joint), the clunk at the end."""
    d = max(2.0, float(dur)); n = n_(d); tt = np.arange(n) / SR; s = int(rng.integers(1 << 30))
    mot = sum(a * np.sin(2 * np.pi * f * tt * (1 + 0.004 * np.sin(2 * np.pi * 0.8 * tt))) for f, a in
              ((90, 1.0), (180, 0.5), (270, 0.25), (540, 0.08)))
    cl = bp(((rng.random(n) < 25 / SR) * rng.uniform(0.3, 1, n)).astype(np.float32), 900, 3500, 2)
    rum = lp(noise(d, s), 300, 2) * 0.6
    y = st((mot * 0.12 + cl * 0.6 + rum * 0.5) * _env(n, 0.3, 0.4))
    ev = [(0.0, y)] + [(j, _thump(rng, 95, 0.25, 0.5)) for j in np.arange(0.8, d - 0.6, 1.1)]
    ev.append((d - 0.3, _thump(rng, 70, 0.35, 1.0)))
    return fade(_seq(ev, 0.4), 0.2, 0.3), 0.0, 0.0, False


WALLS_ALIASES = {
    'scratching': ('wall_scratch', {}), 'scratch': ('wall_scratch', {}), 'wall_scratching': ('wall_scratch', {}),
    'nails_wall': ('wall_scratch', {}), 'crawl': ('wall_crawl', {}), 'crawling': ('wall_crawl', {}),
    'wall_crawling': ('wall_crawl', {}), 'crawl_away': ('wall_crawl', {'speed': 1.3}), 'chew': ('chewing', {}),
    'chewing_wall': ('chewing', {}), 'eating': ('chewing', {}), 'deadbolt_turn': ('deadbolt_slow', {}),
    'deadbolt_self': ('deadbolt_slow', {}), 'bolt_turn': ('deadbolt_slow', {}), 'lock_self': ('deadbolt_slow', {}),
    'bag_twist': ('bread_bag', {'kind': 'twist'}), 'bread': ('bread_bag', {}), 'plastic_bag': ('bread_bag', {}),
    'bag_fold': ('bread_bag', {'kind': 'fold'}), 'hall_switch': ('light_switch', {'kind': 'wall'}),
    'switch': ('light_switch', {'kind': 'wall'}), 'switch_flip': ('light_switch', {'kind': 'wall'}),
    'click': ('light_switch', {'kind': 'wall'}), 'attic_bulb': ('attic_light', {}), 'light_on': ('attic_light', {}),
    'bulb_buzz': ('bulb', {'kind': 'buzz'}), 'buzz': ('bulb', {'kind': 'buzz'}), 'closet_panel': ('closet_slide', {}),
    'panel_slide': ('closet_slide', {}), 'back_wall_slide': ('closet_slide', {}), 'vent': ('vent_rattle', {}),
    'grille': ('vent_rattle', {}), 'floor_vent': ('vent_rattle', {}), 'pencil': ('pencil_mark', {}),
    'pencil_marks': ('pencil_mark', {}), 'crickets': ('august_night', {}), 'heat_wave': ('august_night', {}),
    'night_ambience': ('august_night', {}), 'fans': ('box_fan', {}), 'fan': ('box_fan', {}),
    'phone_911': ('dial_911', {}), 'dial': ('dial_911', {}), 'dialing': ('dial_911', {}),
    'sirens': ('sirens_arrive', {'n_cars': 3}), 'police_sirens': ('sirens_arrive', {'n_cars': 3}),
    'police_arrive': ('sirens_arrive', {'n_cars': 3}), 'siren': ('sirens_arrive', {'n_cars': 3}),
    'boots': ('boots_stairs', {}), 'stairs_boots': ('boots_stairs', {}), 'officers_stairs': ('boots_stairs', {}),
    'cuffs': ('handcuffs', {}), 'dad_snore': ('snore', {}), 'snoring': ('snore', {}),
    'wall_knock': ('knock_door', {'n': 3, 'force': 0.6, 'space': 'in_wall'}),
    'knocking_wall': ('knock_door', {'n': 4, 'force': 0.6, 'space': 'in_wall'}),
    'pipes_knock': ('knock_door', {'n': 3, 'force': 0.5, 'space': 'in_wall'}),
    'keypad_beep': ('keypad', {}), 'garage_code': ('keypad', {}), 'garage': ('garage_door', {}),
    'garage_opener': ('garage_door', {}), 'mask_off': ('glove_squeak', {'kind': 'stretch', 'knuckles': False}),
    'mask_pull': ('glove_squeak', {'kind': 'stretch', 'knuckles': False}),
    'rubber_mask': ('glove_squeak', {'kind': 'squeak', 'knuckles': False}), 'tuck_in': ('cloth_rustle', {}),
    'lock_door': ('lock_turn', {}), 'door_lock': ('lock_turn', {}), 'engine': ('car_idle', {}),
    'radio': ('police_radio', {}),
}
ALIASES.update(WALLS_ALIASES)
# keyword guesses for unknown names: this film's first (the Ice film's 'click' -> leg_click, 'crawl' -> attic_crawl,
# 'siren' -> ambulance would put spider legs and an ambulance into Larkspur Lane)
KEYWORDS = [('scratch', 'wall_scratch'), ('crawl', 'wall_crawl'), ('chew', 'chewing'), ('bag', 'bread_bag'),
            ('bolt', 'deadbolt_slow'), ('switch', 'light_switch'), ('bulb', 'attic_light'), ('closet', 'closet_slide'),
            ('panel', 'closet_slide'), ('vent', 'vent_rattle'), ('grille', 'vent_rattle'), ('pencil', 'pencil_mark'),
            ('cricket', 'august_night'), ('fan', 'box_fan'), ('911', 'dial_911'), ('dial', 'dial_911'),
            ('siren', 'sirens_arrive'), ('boot', 'boots_stairs'), ('stair', 'boots_stairs'), ('cuff', 'handcuffs'),
            ('snor', 'snore'), ('keypad', 'keypad'), ('garage', 'garage_door'), ('knock', 'knock_door'),
            ('mask', 'glove_squeak'), ('radio', 'police_radio'), ('window', 'window_slide'), ('click', 'light_switch'),
            ('night', 'august_night'), ('lock', 'lock_turn')] + KEYWORDS
