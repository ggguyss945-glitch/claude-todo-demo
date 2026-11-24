# sfx_buttons.py: THIS film's SFX block ("If Your Mom's Eyes Turn Into Buttons... DON'T KEEP HER SECRET").
# Run inside sfx.py's namespace (sfx.py execs it after sfx_walls.py, just before RECIPES), so it uses sfx.py's helpers
# directly (src, pool, audio, excerpt, reverb, eq, lp, hp, bp, modal, noise, fade, place, _seq, rate, pan, st, mono,
# _varispeed) and the earlier films' recipes (r_typing, r_fridge_hum, r_car_idle, r_room_tone, ...). Sources: the
# linked libraries first (W/samples, read in place: the school set's playground walla, the car idle, the clothes
# pile, the glass-door squeak; the free CC0 files of catalog.json: civitas talk for the headset leak); synthesis where
# nothing fits (the tik, the ping, the marker, the window motor, the rolling buttons, the jar lid's threads). No new
# outside files. Every source and licence: audio/ATTRIBUTION.md ("The Buttons film").
#
# NAMES the picture emits (film.py sfx cues {t, name, gain_db, pan, params, space}); params in brackets.
#   the motif's sounds  tik [kind jar|tap|empty] (one small button dropping into a glass jar: a tiny glassy tick and a
#                       short rattle, varied by the cue's seed; never metallic; 'tap' = the Blank's button fingertips
#                       on glass, no rattle; 'empty' = into the empty jar), ping [kind chat|muffled] (the game chat's
#                       message: soft, friendly, a little hollow; 'muffled' = face down on the bed). W/align/beats.json
#                       places the script's 16 Tik / Ping beats (audio/beats.py, merged by mix.py).
#   kitchen             helpline_kitchen [dur, keys, murmur] (BED: laptop keys in bursts, a caller murmuring in Mom's
#                       headset, the fridge), headset_murmur [dur], microwave_door [action open|close], marker_squeak
#                       [strokes] (the fridge whiteboard marker), lamp_swing [dur, bump] (the lamp swinging on its cord
#                       after her head knocks it), jar_lid [turns] (the lid screwed tight)
#   bedroom / closet    closet_clicks [n, spacing] (click. Click. Click. like somebody counting), coat_buttons [n,
#                       spacing, times] (the red coat's buttons closing one by one, soft clicks in tempo),
#                       cardigan_fall [dur] (the Blank folding down into an empty cardigan), buttons_roll [dur, n]
#                       (two buttons rolling on the floor and stopping), tablet_down [surface bed|table]
#   outside             school_pickup [dur, kids, car] (BED: the snow-day pickup: kids far off, a car idling, the
#                       snow's hush), car_window [action down|up], tires_snow [dur] (the car pulling away on snow,
#                       leaving tracks), palms_glass [n] (palms on the lobby's glass door: never a knock)
#   aliases             fridge, laptop_keys, music_box_wind, car_door_swing, guard_radio, police_notebook, notebook,
#                       streetlight_hum, door_hall, phone_ring_once ... (BUTTONS_ALIASES)
# Owner, 23 Nov: every recipe eases its own edges and render_event() applies fade() again; everyday foley sits under
# the voice (LEVEL_LU <= -9 here); none of these is a scare hit.

BUTTONS_NAMES = ('tik', 'ping', 'helpline_kitchen', 'headset_murmur', 'microwave_door', 'marker_squeak', 'lamp_swing',
                 'closet_clicks', 'coat_buttons', 'cardigan_fall', 'buttons_roll', 'jar_lid', 'school_pickup',
                 'car_window', 'tires_snow', 'palms_glass', 'tablet_down')
NAMES = NAMES + BUTTONS_NAMES
LEVEL_LU.update(tik=-7, ping=-9, helpline_kitchen=-27, headset_murmur=-27, microwave_door=-11, marker_squeak=-12,
                lamp_swing=-13, closet_clicks=-11, coat_buttons=-12, cardigan_fall=-11, buttons_roll=-13, jar_lid=-12,
                school_pickup=-25, car_window=-13, tires_snow=-11, palms_glass=-10, tablet_down=-12)
PEAK_CAP.update(tik=-6.0, ping=-8.0, palms_glass=-8.0, closet_clicks=-9.0, coat_buttons=-10.0)
BEDS = BEDS + ('helpline_kitchen', 'school_pickup')
BED_BUS = BED_BUS + ('helpline_kitchen', 'school_pickup')
DUR_BEDS = DUR_BEDS + ('headset_murmur',)
BUTTONS_PHONE_FIX = ('cardigan_fall', 'tablet_down')
SPACE_ALIAS.update(kitchen='close', kitchen_table='close', lobby='outside', lobby_door='outside', pickup='street',
                   school='street', snow='street', car='car', closet='next_room', in_closet='next_room',
                   windowsill='close', bedroom='close', son_room='inside', tablet='close')
SPACES = tuple(SPACE_LU)
DEFAULT_SPACE.update(tik='close', ping='close', helpline_kitchen='dry', headset_murmur='close', microwave_door='close',
                     marker_squeak='close', lamp_swing='close', closet_clicks='next_room', coat_buttons='close',
                     cardigan_fall='close', buttons_roll='close', jar_lid='close', school_pickup='dry',
                     car_window='street', tires_snow='street', palms_glass='outside', tablet_down='close')


# ---------------------------------------------------------------------------------------------------- helpers
def _bx_add(*ys):
    ys = [st(y) for y in ys]
    out = np.zeros((max(len(y) for y in ys), 2), np.float32)
    for y in ys:
        out[:len(y)] += y
    return out


def _burst(rng, dur, lo, hi, shape=1.0):
    """A short band-limited noise burst with a raised-sine envelope."""
    k = n_(dur)
    w = np.sin(np.linspace(0, np.pi, k)) ** shape
    return mono(bp(noise(dur + 0.01, int(rng.integers(1 << 30)))[:k] * w, lo, hi, 2))


def _plastic_tick(rng, amp=1.0, bright=1.0):
    """A small plastic button touching something hard: a 1 ms click and the button's own short 'tk' (no ring)."""
    y = np.zeros(n_(0.03), np.float32)
    c = _burst(rng, 0.0012, 1500, 7000 * bright)
    y[:len(c)] += c * 0.9
    m = modal([rng.uniform(2800, 3600), rng.uniform(5200, 6400)], [0.006, 0.003], [1.0, 0.35], 0.03,
              int(rng.integers(1 << 30)), exc=0.0003)
    y[:len(m)] += m * 0.5
    return y * amp


def _glass(rng, scale=1.0, amp=1.0, dec=1.0):
    """A small glass jar's wall: few partials, short decays, a beating pair (glass shimmer). Never a metal ring."""
    f = np.array([1870.0, 1893.0, 3240.0, 4410.0, 6150.0]) * scale * rng.uniform(0.985, 1.015, 5)
    d = np.array([0.11, 0.09, 0.05, 0.03, 0.012]) * dec
    a = np.array([1.0, 0.6, 0.45, 0.22, 0.08]) * amp
    return modal(list(f), list(d), list(a), 0.35 * dec + 0.05, int(rng.integers(1 << 30)), exc=0.0005)


# ---------------------------------------------------------------------------------------------------- the motif's
def r_tik(rng, sp, kind='jar', **_):
    """One small button dropping into a glass jar: the glassy tick, two to four bounces, a short rattle against the
    buttons already in it. Varied each time (the cue's seed): the jar's pitch, the bounces, the rattle."""
    sc = rng.uniform(0.93, 1.07)
    lead = 0.004
    ev = [(lead, _glass(rng, sc, 1.0, 0.9) + 0.0), (lead, _plastic_tick(rng, 0.8))]
    if kind != 'tap':
        t, a, gap = lead, 1.0, rng.uniform(0.045, 0.07)
        for _k in range(int(rng.integers(2, 5)) - (kind == 'empty')):
            t += gap; a *= rng.uniform(0.35, 0.5); gap *= rng.uniform(0.55, 0.7)
            ev += [(t, _glass(rng, sc * rng.uniform(0.97, 1.03), a, 0.6)), (t, _plastic_tick(rng, a * 0.8))]
        if kind == 'jar':                                     # the buttons already in the jar shift
            for _k in range(int(rng.integers(3, 7))):
                ev.append((lead + rng.uniform(0.02, 0.14), _plastic_tick(rng, rng.uniform(0.08, 0.22), 0.8)))
    else:
        ev[0] = (lead, _glass(rng, sc, 0.6, 0.6))
    y = lp(_seq(ev, 0.05), 9500, 2)
    if kind == 'empty':
        y = reverb(y, 'box', 0.12, 0.0)
    return fade(y, 0.001, 0.06), lead, 0.0, False


def r_ping(rng, sp, kind='chat', **_):
    """The game chat's message: two soft notes a fourth apart (E6 -> A6, the film's key), a short pitch blip into
    each, odd harmonics through a little tube (hollow), the tablet's small speaker. 'muffled': face down on the bed."""
    out = np.zeros(n_(0.7), np.float32)
    for t0, f, d, a in ((0.0, 1318.5, 0.16, 0.8), (0.075, 1760.0, 0.30, 1.0)):
        t = np.arange(n_(d * 2.2)) / SR
        fr = f * 2 ** ((-0.6 * np.exp(-t / 0.008)) / 12)
        ph = 2 * np.pi * np.cumsum(fr) / SR
        y = (np.sin(ph) + 0.18 * np.sin(3 * ph) + 0.05 * np.sin(5 * ph)) * np.exp(-t / d) * (1 - np.exp(-t / 0.002))
        i = n_(t0); out[i:i + len(y)] += (y * a)[:len(out) - i]
    d = n_(0.0011); h = np.copy(out)
    for k in range(1, 4):                                     # the hollow: a short tube's comb
        h[k * d:] += out[:-k * d] * (0.38 ** k)
    y = eq(hp(lp(st(h), 8500, 2), 320, 2), ('peak', 1150, 3.0, 1.4))
    if kind == 'muffled':
        y = eq(lp(y, 1600, 2), ('peak', 300, 3.0, 1.0))
    return fade(y, 0.001, 0.08), 0.0, 0.0, False


# ---------------------------------------------------------------------------------------------------- kitchen
def r_headset_murmur(rng, sp, dur=6.0, **_):
    """A caller's voice leaking from Mom's headset: free CC0 talk (civitas), small and tinny, under everything."""
    E = src(has=['civitas__talk'])
    y = excerpt(E[int(rng.integers(len(E)))], dur, rng, 1.0) if E else noise(dur, 3) * 0.05
    y = eq(bp(st(y), 500, 2800, 2), ('peak', 1700, 5.0, 1.5))
    return fade(st(mono(y)), 0.4, 0.6), 0.0, 0.0, False


def r_helpline_kitchen(rng, sp, dur=20.0, keys=1.0, murmur=1.0, **_):
    """BED: the help line at the kitchen table: laptop keys in bursts with pauses (Mom typing notes), the caller
    murmuring in her headset, the fridge."""
    k = r_typing(rng, sp, dur=dur, cps=5.5)[0][:n_(dur)]
    gate = np.repeat((rng.random(int(dur / 1.5) + 2) < 0.55).astype(np.float32), n_(1.5))[:len(k)]
    gate = np.convolve(gate, np.hanning(n_(0.3)) / (n_(0.3) / 2), 'same')
    k = hp(k * np.clip(gate, 0, 1)[:, None], 400, 2) * 0.5 * keys
    m = r_headset_murmur(rng, sp, dur=dur)[0] * 0.22 * murmur
    f = r_fridge_hum(rng, sp, dur=dur)[0] * 0.6
    return fade(_bx_add(k, m, f)[:n_(dur)], 0.8, 1.2), 0.0, 0.0, False


def r_microwave_door(rng, sp, action='open', **_):
    """The microwave door: the button's plastic press, the latch, the door on its spring, the hollow box."""
    s = lambda: int(rng.integers(1 << 30))
    box = modal([182.0, 415.0, 960.0], [0.05, 0.03, 0.012], [1.0, 0.5, 0.2], 0.2, s(), exc=0.004)
    latch = modal([1150.0, 2480.0, 3900.0], [0.012, 0.008, 0.004], [1.0, 0.6, 0.3], 0.05, s(), exc=0.0005)
    swing = _burst(rng, 0.35, 300, 2500, 2.0) * 0.08
    if action == 'open':
        ev = [(0.0, _plastic_tick(rng, 0.6)), (0.05, latch * 0.7), (0.06, box * 0.5), (0.1, swing), (0.42, box * 0.25)]
    else:
        ev = [(0.0, swing), (0.3, latch), (0.3, box * 0.8)]
    return fade(lp(_seq(ev, 0.15), 7000, 2), 0.002, 0.08), (0.05 if action == 'open' else 0.3), 0.0, False


def r_marker_squeak(rng, sp, strokes=3, **_):
    """The fridge whiteboard marker: felt dragging on the board and the stick-slip squeak, stroke by stroke."""
    ev, t = [], 0.0
    for _k in range(int(strokes)):
        d = rng.uniform(0.22, 0.55); n = n_(d); tt = np.arange(n) / SR
        env = np.sin(np.linspace(0, np.pi, n)) ** 0.6
        felt = mono(bp(noise(d + 0.01, int(rng.integers(1 << 30)))[:n], 900, 5000, 2)) * env * 0.25
        f0 = rng.uniform(1300, 2300) * (1 + 0.08 * np.sin(2 * np.pi * rng.uniform(3, 7) * tt))
        sq = np.sin(2 * np.pi * np.cumsum(f0) / SR) * env
        gate = np.convolve((rng.random(n // 480 + 1) < 0.45).astype(float).repeat(480)[:n], np.hanning(960) / 480, 'same')
        ev.append((t, (felt + sq * 0.18 * gate).astype(np.float32)))
        t += d + rng.uniform(0.07, 0.18)
    return fade(_seq(ev, 0.1), 0.01, 0.05), 0.0, 0.0, False


def r_lamp_swing(rng, sp, dur=4.0, bump=True, **_):
    """The lamp swinging on its cord after her head knocks it: a dull knock on the shade, then the hook's small
    creak at each swing, dying away."""
    ev = []
    if bump:
        ev.append((0.0, modal([310.0, 760.0, 1500.0], [0.05, 0.03, 0.012], [1.0, 0.4, 0.15], 0.15,
                              int(rng.integers(1 << 30)), exc=0.003) * 0.9))
    P = _creak_pool()
    t, a = 0.25, 0.5
    while t < dur - 0.4 and a > 0.04:
        g = hp(st(P.get(rng, rj=0.04, tilt=1.0, fo=0.05)[:n_(0.35)]), 500, 2)
        ev.append((t, g * a))
        t += rng.uniform(0.72, 0.82); a *= 0.7
    return fade(_seq(ev, 0.3), 0.002, 0.2), 0.0, 0.0, False


def r_jar_lid(rng, sp, turns=3, **_):
    """The lid screwed on tight: the lid set on the glass (a small tink), the threads grinding twist by twist, the
    hand's regrips, a last snug tick."""
    ev = [(0.0, _glass(rng, 0.9, 0.35, 0.6))]
    t = 0.12
    for _k in range(int(turns)):
        d = rng.uniform(0.22, 0.34); n = n_(d); tt = np.arange(n) / SR
        g = mono(bp(noise(d + 0.01, int(rng.integers(1 << 30)))[:n], 1800, 6000, 2))
        g *= (0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(32, 45) * tt)) * np.sin(np.linspace(0, np.pi, n)) ** 0.7
        ev.append((t, g * 0.22)); t += d + rng.uniform(0.1, 0.16)
    ev.append((t - 0.08, _plastic_tick(rng, 0.5)))
    return fade(lp(_seq(ev, 0.1), 8000, 2), 0.002, 0.05), 0.0, 0.0, False


# ---------------------------------------------------------------------------------------------------- bedroom
def r_closet_clicks(rng, sp, n=3, spacing=0.75, **_):
    """'click. Click. Click. Like somebody counting': a button snapped through its hole, behind the closet door,
    evenly spaced, each a little louder."""
    ev = []
    for k in range(int(n)):
        a = 0.6 + 0.4 * k / max(1, int(n) - 1)
        ev.append((k * spacing * rng.uniform(0.98, 1.02), _plastic_tick(rng, a, 0.8) + 0.0))
        ev.append((k * spacing + 0.004, modal([240.0, 520.0], [0.03, 0.015], [0.4, 0.15], 0.06,
                                              int(rng.integers(1 << 30)), exc=0.002) * a))
    return fade(_seq(ev, 0.2), 0.001, 0.05), 0.0, 0.0, False


def r_coat_buttons(rng, sp, n=6, spacing=0.6, times=None, **_):
    """The red coat's buttons closing themselves one by one, in tempo: wool pulled, the button pushed through its
    hole (a soft plastic tick under cloth)."""
    ts = [float(x) for x in times] if times else [k * spacing for k in range(int(n))]
    P = _cloth_pool(); ev = []
    for t in ts:
        ev.append((max(0.0, t - 0.12), P.get(rng, rj=0.03, tilt=1.0, fo=0.04)[:n_(0.18)] * 0.35))
        ev.append((t, lp(st(_plastic_tick(rng, 0.7, 0.7)), 5000, 2)))
    return fade(_seq(ev, 0.2), 0.01, 0.06), ts[0], 0.0, False


def r_cardigan_fall(rng, sp, dur=1.4, **_):
    """The Blank folding in on herself, down to a flat, empty cardigan: a long soft cloth slide, then the light fall
    of wool on the floor (the clothes-pile recording), settling."""
    E = src(has=['cloth_impact_throw_clothes_on_floor_pile'])
    R = src(has=['owlish_sound_effects_pack_cloth_rustle'])
    sl = excerpt(R[int(rng.integers(len(R)))], max(0.4, dur - 0.5), rng, 0.3) if R else noise(dur, 1) * 0.02
    sl = lp(st(sl), 5000, 2) * np.linspace(0.2, 1.0, len(sl))[:, None] * 0.5
    hit = audio(E[0])[:n_(1.2)] if E else st(_burst(rng, 0.2, 80, 900)) * 0.5
    at = max(0.3, dur - 0.55)
    return fade(lp(_seq([(0.0, sl), (at, hit)], 0.2), 6000, 2), 0.15, 0.25), at, 0.0, False


def r_buttons_roll(rng, sp, dur=2.2, n=2, **_):
    """Two buttons rolling across the floorboards and stopping: each a soft rumble with the boards' little ticks,
    slowing, a last wobble faster and faster, and still."""
    ev = []
    for b in range(int(n)):
        t0 = b * rng.uniform(0.12, 0.2); d = dur * rng.uniform(0.75, 1.0) - t0; k = n_(d); tt = np.arange(k) / SR
        sp_ = np.clip(1 - tt / d, 0, 1)
        rum = mono(bp(noise(d + 0.01, int(rng.integers(1 << 30)))[:k], 250, 1400, 2)) * sp_ * 0.12
        y = rum.astype(np.float32)
        t, rate_ = 0.0, rng.uniform(22, 30)
        while t < d * 0.8:
            i = n_(t); tk = _plastic_tick(rng, 0.25 * (1 - t / d) + 0.05, 0.6)
            y[i:i + len(tk)] += tk[:max(0, k - i)]
            t += 1.0 / max(5.0, rate_ * (1 - t / d)) * rng.uniform(0.8, 1.2)
        t, w = d * 0.8, 9.0                                  # the wobble before it lies flat
        while t < d - 0.02:
            i = n_(t); tk = _plastic_tick(rng, 0.18, 0.6)
            y[i:i + len(tk)] += tk[:max(0, k - i)]
            t += 1.0 / w; w = min(45.0, w * 1.18)
        ev.append((t0, pan(st(y), rng.uniform(-0.3, 0.3))))
    return fade(lp(_seq(ev, 0.1), 7000, 2), 0.02, 0.05), 0.0, 0.0, False


def r_tablet_down(rng, sp, surface='bed', **_):
    """The tablet set face down: 'bed' (a soft thump into the duvet), 'table' (its glass back on wood, a short
    slide)."""
    if surface == 'table':
        ev = [(0.0, modal([620.0, 1480.0, 3100.0], [0.02, 0.01, 0.005], [1.0, 0.5, 0.2], 0.05,
                          int(rng.integers(1 << 30)), exc=0.001) * 0.8),
              (0.03, _burst(rng, 0.15, 1500, 5000, 2.0) * 0.06)]
    else:
        ev = [(0.0, _burst(rng, 0.05, 60, 420, 1.0) * 1.0), (0.01, _burst(rng, 0.12, 600, 3000, 2.0) * 0.08)]
    return fade(_seq(ev, 0.1), 0.002, 0.05), 0.0, 0.0, False


# ---------------------------------------------------------------------------------------------------- outside
def r_school_pickup(rng, sp, dur=20.0, kids=1.0, car=1.0, **_):
    """BED: the snow-day school pickup: kids far across the lot (the school set's playground walla, high end taken
    off by the snow), a car idling near, a little wind."""
    E = src(has=['ambience_school_kids_playground', 'ambience_school_few_close_big_crowd'])
    k = excerpt(E[int(rng.integers(len(E)))], dur, rng, 1.5) if E else noise(dur, 2) * 0.01
    k = eq(lp(hp(st(k), 180, 2), 2600, 2), ('hs', 1500, -4.0, 0.7)) * 0.5 * kids
    c = r_car_idle(rng, sp, dur=dur)[0][:n_(dur)] * 0.35 * car
    w = lp(st(noise(dur, int(rng.integers(1 << 30)))), 400, 2) * 0.02
    return fade(_bx_add(k, c, w)[:n_(dur)], 1.0, 1.5), 0.0, 0.0, False


def r_car_window(rng, sp, action='down', dur=1.6, **_):
    """The car's power window: the motor's whine through the door, the glass sliding in its felt, the stop."""
    k = n_(dur); tt = np.arange(k) / SR
    f = (108.0 if action == 'down' else 98.0) * (1 - 0.06 * tt / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    mot = sum(np.sin(h * ph) / h ** 0.8 for h in range(1, 9)) * 0.12
    gl = mono(bp(noise(dur + 0.01, int(rng.integers(1 << 30)))[:k], 900, 3500, 2)) * 0.05
    env = np.minimum(1, np.minimum(tt / 0.05, (dur - tt) / 0.03))
    stop = modal([140.0, 380.0], [0.04, 0.02], [1.0, 0.3], 0.12, int(rng.integers(1 << 30)), exc=0.003) * 0.5
    y = _seq([(0.0, ((mot + gl) * env).astype(np.float32)), (dur - 0.02, stop)], 0.1)
    return fade(lp(y, 5000, 2), 0.02, 0.08), 0.0, 0.0, False


def r_tires_snow(rng, sp, dur=4.0, **_):
    """The car pulling away on snow, leaving only tracks: the idle rising as it goes, packed snow crunching under
    the tyres (a dense soft crackle), moving off and away."""
    c = r_car_idle(rng, sp, dur=dur + 1.0)[0]
    eng = _varispeed(c, 1.0, 1.45, n_(dur))
    k = n_(dur); tt = np.arange(k) / SR
    cr = np.zeros(k, np.float32); t = 0.05
    while t < dur - 0.05:
        i = n_(t); g = _burst(rng, rng.uniform(0.004, 0.012), 300, 2600) * rng.uniform(0.2, 0.6)
        cr[i:i + len(g)] += g[:max(0, k - i)]
        t += rng.uniform(0.006, 0.02)
    away = np.clip(1.15 - tt / dur, 0, 1) ** 1.5
    y = _bx_add(eng * 0.6, lp(st(cr), 2800, 2) * 0.5) * away[:, None]
    return fade(_travel_b(y, 0.0, 0.7), 0.05, 0.6), 0.0, 0.0, False


def _travel_b(y, p0, p1):
    m = mono(st(y)); th = (np.linspace(p0, p1, len(m)) + 1) * np.pi / 4
    return np.stack([m * np.cos(th), m * np.sin(th)], 1).astype(np.float32)


def r_palms_glass(rng, sp, n=2, **_):
    """Palms on the lobby's glass door: the soft flat of a hand (no knuckles: never a knock), the big pane's low
    shiver, the skin's faint squeak as it drags."""
    ev = []
    for k in range(int(n)):
        t = k * rng.uniform(0.16, 0.24)
        th = _burst(rng, 0.018, 90, 420, 1.0) * 0.9
        pane = modal([175.0, 410.0, 760.0, 1240.0], [0.08, 0.05, 0.03, 0.015], [1.0, 0.5, 0.25, 0.1], 0.25,
                     int(rng.integers(1 << 30)), exc=0.006) * 0.45
        ev += [(t, th), (t, pane)]
    S = src(has=['glass_friction_finger_rub_and_squeak_on_glass_door'])
    if S:
        ev.append((ev[-1][0] + 0.08, lp(audio(S[0])[:n_(0.4)], 4000, 2) * 0.12))
    return fade(_seq(ev, 0.2), 0.003, 0.1), 0.0, 0.0, False


BUTTONS_ALIASES = {
    'button_jar': ('tik', {}), 'button_drop': ('tik', {}), 'jar_tik': ('tik', {}), 'finger_tap': ('tik', {'kind': 'tap'}),
    'fingertips': ('tik', {'kind': 'tap'}), 'chat_ping': ('ping', {}), 'message': ('ping', {}),
    'tablet_ping': ('ping', {}), 'helpline': ('helpline_kitchen', {}), 'call_center': ('helpline_kitchen', {}),
    'headset': ('headset_murmur', {}), 'laptop_keys': ('typing', {'cps': 5.5}), 'laptop': ('typing', {'cps': 5.5}),
    'fridge': ('fridge_hum', {}), 'microwave': ('microwave_door', {}), 'marker': ('marker_squeak', {}),
    'whiteboard': ('marker_squeak', {}), 'lamp': ('lamp_swing', {}), 'closet_click': ('closet_clicks', {}),
    'counting': ('closet_clicks', {}), 'buttons_close': ('coat_buttons', {}), 'coat_close': ('coat_buttons', {}),
    'cardigan': ('cardigan_fall', {}), 'collapse': ('cardigan_fall', {}), 'buttons_rolling': ('buttons_roll', {}),
    'lid': ('jar_lid', {}), 'lid_on': ('jar_lid', {}), 'pickup': ('school_pickup', {}), 'kids_far': ('school_pickup', {}),
    'power_window': ('car_window', {}), 'tire_tracks': ('tires_snow', {}), 'pull_away': ('tires_snow', {}),
    'car_door_swing': ('car_door_open', {}), 'guard_radio': ('police_radio', {'dur': 2.0}),
    'police_notebook': ('page_flip', {'n': 1}), 'notebook': ('page_flip', {'n': 1}),
    'notes': ('pen_scratch', {'dur': 1.6}), 'palms': ('palms_glass', {}), 'glass_door': ('palms_glass', {}),
    'streetlight_hum': ('streetlight', {'flicker': 0.0}), 'tablet_face_down': ('tablet_down', {}),
    'door_hall': ('door_creak', {'space': 'inside'}), 'door_down_hall': ('door_creak', {'space': 'inside'}),
    'phone_ring_once': ('phone_ring', {'n': 1}), 'ring_once': ('phone_ring', {'n': 1}),
    'music_box_crank': ('music_box_wind', {}),
}
ALIASES.update(BUTTONS_ALIASES)
# keyword guesses for unknown names: this film's first (the Walls film's 'click' -> light_switch, 'window' ->
# window_slide stay behind these)
KEYWORDS = [('tik', 'tik'), ('jar', 'tik'), ('ping', 'ping'), ('chat', 'ping'), ('helpline', 'helpline_kitchen'),
            ('headset', 'headset_murmur'), ('microwave', 'microwave_door'), ('marker', 'marker_squeak'),
            ('lamp', 'lamp_swing'), ('coat', 'coat_buttons'), ('button', 'coat_buttons'), ('cardigan', 'cardigan_fall'),
            ('roll', 'buttons_roll'), ('lid', 'jar_lid'), ('pickup', 'school_pickup'), ('school', 'school_pickup'),
            ('car_window', 'car_window'), ('tire', 'tires_snow'), ('tyre', 'tires_snow'), ('palm', 'palms_glass'),
            ('glass', 'palms_glass'), ('tablet', 'tablet_down'), ('fridge', 'fridge_hum'), ('keys', 'typing'),
            ('typing', 'typing')] + KEYWORDS
