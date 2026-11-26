# sfx_obsession.py: THIS film's SFX block ("If a Girl Is OBSESSED With Being Your Only Friend... DON'T WRITE YOUR NAME").
# Run inside sfx.py's namespace (sfx.py execs it after sfx_buttons.py, just before RECIPES), so it uses sfx.py's
# helpers directly (src, pool, audio, excerpt, reverb, eq, lp, hp, bp, modal, noise, fade, _seq, st, mono, pan,
# _varispeed) and the earlier films' recipes (r_car_idle, r_whoosh, r_wind_gust, r_phone_vibrate, ...). Sources: the
# owner's new set W/samples/epidemic_obsession FIRST (read in place: chalk on boards, letterbox flaps, swing chains,
# lockers, buckets, scrub brushes, paint rollers, cafeterias, drawers, cutlery, car idles and indicators, fluorescent
# hums, switches, sneaker squeaks, shoebox lids, dust trickles, swooshes), then synthesis for the layers (chalk grit
# on pavement, the stub rolling, a wood floor's body, the floodlight breaker). Licences: audio/ATTRIBUTION.md.
#
# NAMES the picture emits (film.py sfx cues {t, name, gain_db, pan, params, space}); params in brackets.
#   Evie (CAST.md "Sound events she emits": the cast's gain_db IS the level in LU against the voice, so these names
#   have LEVEL_LU 0 and DEFAULT_GAIN gives a cue without gain_db the cast's level)
#     chalk_scrape [kind write|creep|slide|flatten|rise|stretch, dur, surface pavement|step|wood|board]
#     chalk_tap [kind tap|beat|land|stop, surface]   chalk_stub_drop [kind drop|bounce]   chalk_roll [dur]
#     chalk_dust_whoosh [dur] (the drain: powder on the wind)   phone_tap   swing_creak
#   the family: brush_scrub [wet] (one stroke on concrete), paint_roll (one roller pass); footsteps_* / knock_door /
#     cloth_rustle are the earlier films' recipes (aliases below)
#   the script's beats (audio/beats.py): ping [kind note|low|chat, note] (ONE note of "Stick Like Glue",
#     audio/motif_obsession.py), clank (the caretaker's floodlight breaker: "Clank. Floodlight.")
#   foley  letterbox [action lift|close|rattle], locker [action open|close|slam], bucket_down, bucket_water [dur],
#          drawer [action open|close], fork_plate, indicator [dur, rate], floodlight [action on|off], sneaker_squeak
#          [n], shoebox_lid [action on|off], swing_chains [dur] (BED)
#   beds   cafeteria [dur], school_corridor [dur], car_cabin [dur, indicator], floodlight_hum [dur]
#   reused porch_light, light_switch, phone_vibrate (phone_buzz), suburb_night (night_suburb), house_hum, wind_gust
#          (wind), cloth_rustle (hoodie), footsteps_hall / footsteps_porch / footsteps_stairs (aliases)
# Owner, 23 Nov: every recipe eases its own edges and render_event() applies fade() again; everyday foley sits under
# the voice (LEVEL_LU <= -9, the cast's chalk at -10..-24); 'clank' is a startle (-7 LU outside), none is a scare hit.

OBSESSION_NAMES = ('chalk_scrape', 'chalk_tap', 'chalk_stub_drop', 'chalk_roll', 'chalk_dust_whoosh', 'phone_tap',
                   'swing_creak', 'brush_scrub', 'paint_roll', 'clank', 'letterbox', 'locker', 'bucket_down',
                   'bucket_water', 'drawer', 'fork_plate', 'indicator', 'floodlight', 'sneaker_squeak', 'shoebox_lid',
                   'swing_chains', 'cafeteria', 'school_corridor', 'car_cabin', 'floodlight_hum')
NAMES = NAMES + OBSESSION_NAMES
R_PING_BUTTONS = r_ping                                  # the Buttons film's chat ping (kind 'chat')
LEVEL_LU.update(chalk_scrape=0, chalk_tap=0, chalk_stub_drop=0, chalk_roll=0, chalk_dust_whoosh=0, phone_tap=0,
                swing_creak=0, brush_scrub=0, paint_roll=0, clank=0, letterbox=-9, locker=-11, bucket_down=-12,
                bucket_water=-17, drawer=-13, fork_plate=-12, indicator=-19, floodlight=-3, sneaker_squeak=-10,
                shoebox_lid=-13, swing_chains=-22, cafeteria=-27, school_corridor=-29, car_cabin=-27,
                floodlight_hum=-24)
# the cast's levels (CAST.md) for a cue that carries no gain_db (mix.py reads DEFAULT_GAIN)
DEFAULT_GAIN = dict(globals().get('DEFAULT_GAIN', {}))
DEFAULT_GAIN.update(chalk_scrape=-14.0, chalk_tap=-16.0, chalk_stub_drop=-10.0, chalk_roll=-19.0,
                    chalk_dust_whoosh=-12.0, phone_tap=-22.0, swing_creak=-22.0, brush_scrub=-16.0, paint_roll=-18.0)
# the cast's names: loudness decides (their gain_db then sets the level), so the caps only guard the transients
PEAK_CAP.update(chalk_scrape=-1.0, chalk_tap=-2.0, chalk_stub_drop=-1.0, chalk_roll=-1.0, chalk_dust_whoosh=-1.0,
                phone_tap=-2.0, swing_creak=-1.0, brush_scrub=-1.0, paint_roll=-1.0, clank=-2.0, locker=-8.0,
                fork_plate=-9.0, letterbox=-3.0, floodlight=-3.0, sneaker_squeak=-6.0)
BEDS = BEDS + ('swing_chains', 'cafeteria', 'school_corridor', 'car_cabin', 'floodlight_hum')
BED_BUS = BED_BUS + ('swing_chains', 'cafeteria', 'school_corridor', 'car_cabin', 'floodlight_hum')
DUR_BEDS = DUR_BEDS + ('chalk_roll', 'bucket_water', 'indicator')
OBSESSION_PHONE_FIX = ('chalk_stub_drop', 'bucket_down', 'drawer', 'shoebox_lid')
SPACE_ALIAS.update(hall_floor='inside', landing='inside', doormat='inside', path='outside', pavement='outside',
                   playground='outside', square='outside', swings='outside', lunch_hall='inside', corridor='inside',
                   locker='close', kitchen='close', dinner='close', mom_car='car', bedroom='close', window='window')
SPACES = tuple(SPACE_LU)
DEFAULT_SPACE.update(chalk_scrape='close', chalk_tap='close', chalk_stub_drop='inside', chalk_roll='inside',
                     chalk_dust_whoosh='outside', phone_tap='close', swing_creak='outside', brush_scrub='outside',
                     paint_roll='outside', clank='outside', letterbox='inside', locker='close', bucket_down='outside',
                     bucket_water='outside', drawer='close', fork_plate='close', indicator='car', floodlight='outside',
                     sneaker_squeak='outside', shoebox_lid='close', swing_chains='outside', cafeteria='dry',
                     school_corridor='dry', car_cabin='dry', floodlight_hum='outside')


# ---------------------------------------------------------------------------------------------------- helpers
def _op(key, has, mode='onset', nothas=None, **seg):
    """A grain pool over the obsession set's files whose slug holds any of `has`."""
    return pool('ob_' + key, lambda: src(has=list(has), nothas=nothas), mode, **seg)


def _ob_add(*ys):
    ys = [st(y) for y in ys if y is not None and len(y)]
    out = np.zeros((max(len(y) for y in ys), 2), np.float32)
    for y in ys:
        out[:len(y)] += y
    return out


def _nb(rng, dur, lo, hi, shape=1.0):
    """A band-limited noise burst with a raised-sine envelope (mono)."""
    k = max(8, n_(dur))
    w = np.sin(np.linspace(0, np.pi, k)) ** shape
    return mono(bp(noise(dur + 0.01, int(rng.integers(1 << 30)))[:k] * w, lo, hi, 2))


def _grit(rng, env, density=900.0, lo=1800, hi=7500):
    """Chalk grit on pavement: a dense random crackle of tiny bursts that follows env (mono, len(env))."""
    k = len(env); y = np.zeros(k, np.float32)
    t = 0.0; T = k / SR
    while t < T:
        i = n_(t); g = _nb(rng, rng.uniform(0.0008, 0.003), lo, hi) * rng.uniform(0.2, 1.0) * env[min(i, k - 1)]
        y[i:i + len(g)] += g[:max(0, k - i)]
        t += rng.exponential(1.0 / density)
    return y


def _surface(y, rng, surface, env=None):
    """The ground under the chalk: pavement / step (concrete: the board's squeak tamed, grit and a dry scuff added),
    wood (the hall boards: a soft hollow body), board (as recorded)."""
    y = st(y)
    if surface in ('pavement', 'step', 'path', 'concrete'):
        y = eq(y, ('peak', 3300, -6.0, 1.2), ('peak', 5200, -4.0, 1.5), ('ls', 300, 2.0, 0.7))
        e = env if env is not None else np.abs(mono(y))
        e = np.convolve(e, np.ones(n_(0.01)) / n_(0.01), 'same')
        e = e / (e.max() + 1e-9)
        y = y + st(_grit(rng, e[:len(y)], 1100 if surface != 'step' else 800)) * (0.35 * np.abs(y).max())
    elif surface in ('wood', 'floor', 'boards', 'hall'):
        b = mono(y)
        body = lp(b, 900, 2)
        y = eq(y, ('peak', 3300, -5.0, 1.2), ('peak', 320, 4.0, 1.2)) + st(body) * 0.3
    return y


# ---------------------------------------------------------------------------------------------------- Evie's chalk
CHALK_HAS = ('chalk_stick_single_stroke', 'objects_writing_chalk_on_board', 'chalk_stick_write_on_chalk_board',
             'chalk_scratch_writing_blackboard')


def r_chalk_scrape(rng, sp, kind='write', dur=None, surface=None, **_):
    """Chalk on the ground. write: one stroke of a letter (a recorded chalk stroke, trimmed to dur, on the surface);
    creep: the long fingers coming or going across the hall floor (soft, a slow finger rhythm); slide: Evie gliding
    flat across the ground (a long smooth drag); flatten: lying down flat (a short falling drag); rise: standing up out
    of the ground (a rising drag); stretch: the neck stretching up (a long, soft, rising drag: never a crack)."""
    kind = str(kind); d = float(dur or {'write': 0.42, 'creep': 1.6, 'slide': 1.8, 'flatten': 0.7, 'rise': 1.4,
                                       'stretch': 2.4}.get(kind, 0.5))
    surf = surface or ('wood' if kind == 'creep' else 'pavement')
    if kind == 'write':
        g = _op('chalk_stroke', CHALK_HAS, 'onset', gap=0.06, max_len=1.0, keep=-22).get(rng, rj=0.06, fi=0.003, fo=0.05)
        if len(g) < n_(d):                                   # a long stroke: two grains overlapped
            g2 = _op('chalk_stroke', CHALK_HAS, 'onset', gap=0.06, max_len=1.0, keep=-22).get(rng, rj=0.06)
            g = _seq([(0.0, g), (max(0.05, len(g) / SR - 0.06), g2)], 0.1)
        y = fade(_surface(g[:n_(d + 0.08)], rng, surf), 0.004, 0.07)
        return y, 0.004, 0.0, False
    E = src(has=['objects_writing_chalk_on_board', 'chalk_stick_write_on_chalk_board'])
    base = excerpt(E[int(rng.integers(len(E)))], d + 0.2, rng, 0.3) if E else st(noise(d + 0.2, 5)) * 0.05
    k = len(base); tt = np.arange(k) / SR; x = tt / max(d, 0.1)
    air = _nb(rng, d + 0.2, 500, 4200, 0.6)[:k]
    if kind == 'creep':                                      # fingers, softly, a slow 3 Hz walk of fingertips
        env = (0.55 + 0.45 * np.sin(2 * np.pi * 3.0 * tt) ** 2) * np.minimum(1, np.minimum(tt / 0.25, (d - tt) / 0.4))
        y = lp(st(mono(base) * 0.7 + air * 0.25), 3500, 2)
    elif kind == 'slide':
        env = np.sin(np.pi * np.clip(x, 0, 1)) ** 0.7
        y = lp(st(mono(base) * 0.35 + air * 0.6), 2800, 2)
    elif kind == 'flatten':
        env = np.clip(1 - x, 0, 1) ** 1.3 * np.minimum(1, tt / 0.06)
        y = _varispeed(st(mono(base) * 0.4 + air * 0.5), 1.1, 0.7, k)
        y = lp(y, 2600, 2)
    elif kind == 'rise':
        env = np.clip(x, 0, 1) ** 1.2 * np.minimum(1, (d - tt) / 0.25).clip(0, 1)
        y = _varispeed(st(mono(base) * 0.4 + air * 0.5), 0.75, 1.2, k)
        y = hp(y, 250, 2)
    else:                                                    # stretch: long, soft, smooth, rising slowly
        env = np.sin(np.pi * np.clip(x, 0, 1)) ** 1.2
        y = _varispeed(lp(st(mono(base) * 0.25 + air * 0.7), 2200, 2), 0.8, 1.15, k)
    y = st(y)[:k] * np.clip(env, 0, 1)[:k, None].astype(np.float32)
    y = _surface(y, rng, surf if kind in ('slide', 'creep') else 'board', np.clip(env, 0, 1))
    return fade(y[:n_(d)], 0.05, 0.25), 0.05, 0.0, False


def _chalk_click(rng, amp=1.0):
    """The chalk's own contact: a 1 ms click and a brittle little body (no ring)."""
    y = np.zeros(n_(0.04), np.float32)
    c = _nb(rng, 0.0012, 1800, 8000); y[:len(c)] += c
    m = modal([rng.uniform(1700, 2100), rng.uniform(3000, 3500)], [0.004, 0.0025], [1.0, 0.4], 0.04,
              int(rng.integers(1 << 30)), exc=0.0003)
    y[:len(m)] += m * 0.4
    return y * amp


def r_chalk_tap(rng, sp, kind='tap', surface=None, **_):
    """One soft chalk tap. tap / beat (the motif's tap on every beat: softer, rounder): the stub tapped on the ground;
    land: her sneakers landing as she stands up (a soft dull pat); stop: the rolling stub stopping at the bottom stair."""
    kind = str(kind)
    if kind == 'land':
        y = _seq([(0.0, _nb(rng, 0.03, 90, 700, 1.0) * 0.9), (0.012, _chalk_click(rng, 0.25))], 0.15)
        return fade(lp(st(y), 3000, 2), 0.002, 0.06), 0.0, 0.0, False
    g = _op('chalk_stroke', CHALK_HAS, 'onset', gap=0.06, max_len=1.0, keep=-22).get(rng, rj=0.04, fi=0.001, fo=0.01)
    head = fade(g[:n_(0.05)], 0.0005, 0.03)
    surf = surface or ('wood' if kind == 'stop' else 'pavement')
    thump = (modal([210.0, 480.0, 930.0], [0.03, 0.015, 0.008], [1.0, 0.5, 0.2], 0.08, int(rng.integers(1 << 30)),
                   exc=0.002) if surf in ('wood', 'floor', 'hall') else _nb(rng, 0.012, 250, 1400, 1.0))
    y = _seq([(0.0, _chalk_click(rng, 0.8)), (0.0, head * 0.6), (0.001, st(thump) * 0.35)], 0.1)
    if kind == 'beat':
        y = lp(y, 4500, 2)
    return fade(y, 0.0008, 0.05), 0.0, 0.0, False


def r_chalk_stub_drop(rng, sp, kind='drop', **_):
    """The chalk stub through the slot onto the hall boards: a small hard impact (the new set's thick marker and dice
    drops, made smaller), the chalk's brittle click, the board's knock; bounce: one smaller hop."""
    a = 1.0 if kind == 'drop' else 0.4
    g = _op('stub', ('marker_thick_drop_on_floor', 'dice_single_drop', 'eraser_rubber_drop'), 'onset', gap=0.08,
            max_len=0.4, keep=-18).get(rng, rj=0.03, fi=0.0005, fo=0.03)
    g = _varispeed(st(g), 1.35, 1.35, int(len(g) / 1.35))
    board = modal([180.0, 410.0, 760.0], [0.05, 0.025, 0.012], [1.0, 0.45, 0.2], 0.15, int(rng.integers(1 << 30)),
                  exc=0.002)
    y = _seq([(0.0, g * 0.8 * a), (0.0, _chalk_click(rng, 0.7 * a)), (0.001, st(board) * 0.4 * a)], 0.2)
    if kind == 'drop':                                       # the little hop after the landing
        y = _seq([(0.0, y), (rng.uniform(0.09, 0.13), _chalk_click(rng, 0.3)), (0.2, _chalk_click(rng, 0.12))], 0.2)
    return fade(y, 0.0005, 0.08), 0.0, 0.0, False


def r_chalk_roll(rng, sp, dur=1.6, **_):
    """The stub rolling across the boards to the bottom stair: an uneven tick as its flat sides turn over, the
    boards' faint hollow rumble, slowing, then a tiny stop."""
    d = float(dur); k = n_(d); tt = np.arange(k) / SR
    out = np.zeros(k, np.float32); t = 0.0; rate = rng.uniform(9, 12)
    while t < d * 0.92:
        u = t / d
        i = n_(t); c = _chalk_click(rng, rng.uniform(0.25, 0.5) * (1 - 0.6 * u))
        out[i:i + len(c)] += c[:max(0, k - i)]
        t += 1.0 / (rate * (1 - 0.7 * u) + 1.5) * rng.uniform(0.8, 1.25)
    rum = lp(_nb(rng, d, 120, 700, 0.3)[:k], 600, 2) * (1 - tt / d) * 0.25
    y = _seq([(0.0, st(out + rum)), (d * 0.93, _chalk_click(rng, 0.35))], 0.15)
    return fade(lp(y, 6500, 2), 0.01, 0.1), 0.0, 0.0, False


def r_chalk_dust_whoosh(rng, sp, dur=3.4, **_):
    """The drain: Evie's chalk-white colour lifting away on the wind as dust. A soft airy whoosh (the new set's light
    swoosh, slowed), powder trickling (sand on sand, high-passed, thinned), a wind swell that carries it off."""
    d = float(dur); k = n_(d); tt = np.arange(k) / SR; x = tt / d
    S = src(has=['dirt_sand_dust_sand_trickling'])
    pw = excerpt(S[0], d, rng, 0.5) if S else st(noise(d, 2)) * 0.02
    pw = hp(st(pw), 1800, 2)[:k] * 0.6
    W = src(has=['swooshes_whoosh_designed_swoosh_light'])
    sw = _varispeed(st(audio(W[0])), 0.55, 0.45, n_(min(d, 2.8))) if W else np.zeros((n_(1), 2), np.float32)
    wind = lp(hp(st(_nb(rng, d, 200, 2500, 0.5)), 180, 2), 1800, 2)[:k] * 0.5
    env = np.clip(x / 0.25, 0, 1) ** 1.5 * np.clip((1 - x) / 0.6, 0, 1) ** 1.2
    y = _ob_add(pw * env[:, None], wind * env[:, None], sw * 0.8)[:k]
    th = (np.linspace(-0.2, 0.75, k) + 1) * np.pi / 4                  # carried off to screen right
    m = mono(y); y = np.stack([m * np.cos(th), m * np.sin(th)], 1).astype(np.float32) + y * 0.3
    return fade(y, 0.15, 0.8), 0.25 * d, 0.0, False


def r_phone_tap(rng, sp, **_):
    """A fingertip on a phone screen: a tiny soft click and the glass's dull pat."""
    y = _seq([(0.0, _nb(rng, 0.003, 1500, 5000) * 0.6), (0.0, _nb(rng, 0.012, 200, 900) * 0.4)], 0.05)
    return fade(lp(st(y), 6000, 2), 0.0005, 0.02), 0.0, 0.0, False


def r_swing_creak(rng, sp, **_):
    """One swing reaching the end of its arc: a chain creak from the new set's playground swings."""
    g = _op('swing', ('playground_swing',), 'phrase', gap=0.12, max_len=0.9, keep=-20).get(rng, rj=0.04, fo=0.08)
    return fade(lp(g, 7000, 2), 0.01, 0.1), 0.0, 0.0, False


def r_swing_chains(rng, sp, dur=12.0, **_):
    """BED: the swings moving in the playground: the new set's chain recordings, looped with crossfades."""
    E = src(has=['playground_swing'])
    y = excerpt(E[int(rng.integers(len(E)))], dur, rng, 1.0) if E else st(noise(dur, 3)) * 0.01
    return fade(lp(y, 7000, 2), 0.8, 1.2), 0.0, 0.0, False


# ---------------------------------------------------------------------------------------------------- the family
def r_brush_scrub(rng, sp, wet=True, **_):
    """One stroke of Mom's scrub brush on the wet path (the new set's brush scrubs), a little water under it."""
    g = _op('scrub', ('cleaning_brush_scrub', 'brush_scrub_carpet', 'brush_scub_scrape_floor_wood',
                      'cloth_movement_scrubbing_floor'), 'onset', gap=0.1, max_len=0.8, keep=-20).get(rng, rj=0.04, fo=0.06)
    y = eq(st(g), ('peak', 2500, -2.0, 1.0))
    if wet:
        y = y + st(_nb(rng, len(y) / SR, 2500, 8000, 0.7)[:len(y)]) * 0.05
    return fade(y, 0.005, 0.06), 0.0, 0.0, False


def r_paint_roll(rng, sp, **_):
    """One pass of the caretaker's paint roller over the square (the new set's rollers)."""
    g = _op('roller', ('paint_roller', 'roller_painting'), 'phrase', gap=0.2, max_len=1.6, keep=-20).get(rng, rj=0.03,
                                                                                                          fo=0.12)
    return fade(lp(st(g), 9000, 2), 0.02, 0.15), 0.0, 6.0, False      # +6: a roller pass reads low on momentary


# ---------------------------------------------------------------------------------------------------- the beats
def r_ping(rng, sp, kind='note', note=0, **_):            # noqa: F811 (THIS film's ping: one note of the song)
    """The message ping = ONE note of "Stick Like Glue" (audio/motif_obsession.py: note = which note of the song,
    0-based); kind 'low': the rule-7 pings, an octave lower and darker; kind 'chat': the Buttons film's chat ping."""
    if kind == 'chat':
        return R_PING_BUTTONS(rng, sp)
    import motif_obsession as MO
    allm = MO.all_notes()
    m = allm[int(note) % len(allm)][2]
    y = MO.ping_note(m + (12 if kind == 'low' else 24), MO.TUNE_CENTS, 1.0, 0.55 if kind == 'low' else 0.32,
                     kind == 'low', int(rng.integers(1 << 20)))
    return fade(y, 0.001, 0.15), 0.0, 0.0, False


def r_clank(rng, sp, **_):
    """'Clank. Floodlight.': the caretaker throws the old floodlight's breaker on the school wall: a heavy metal
    clunk (the new set's metal slam, pitched down), the lamp housing's low ring, then the fluorescent buzz striking."""
    g = _op('metal', ('doors_metal_open_close_slam', 'doors_metal_slam_hall'), 'onset', gap=0.15, max_len=0.6,
            keep=-16).get(rng, rj=0.02, fi=0.0005, fo=0.08)
    g = _varispeed(st(g), 0.72, 0.72, int(len(g) / 0.72))
    ring = modal([96.0, 211.0, 447.0, 905.0], [0.25, 0.15, 0.08, 0.04], [1.0, 0.6, 0.3, 0.12], 0.8,
                 int(rng.integers(1 << 30)), exc=0.003)
    hum = r_floodlight_hum(rng, sp, dur=2.0)[0] * 0.5
    y = _seq([(0.0, g), (0.0, st(ring) * 0.35), (0.12, hum)], 0.3)
    return fade(y, 0.0005, 0.5), 0.0, 0.0, False


def r_floodlight_hum(rng, sp, dur=10.0, **_):
    """BED: the floodlight's buzz (the new set's fluorescent hums), thin and high on the school wall."""
    E = src(has=['fluorescent_light_buzz_medium'])
    y = excerpt(E[0], dur, rng, 1.0) if E else st(noise(dur, 4)) * 0.005
    return fade(hp(y, 90, 2), 0.3, 0.8), 0.0, 0.0, False


def r_floodlight(rng, sp, action='on', **_):
    """The floodlight switching: on = the clunk and the strike; off = a smaller clunk, the buzz dying."""
    if action == 'on':
        return r_clank(rng, sp)
    y, _, _, _ = r_clank(rng, sp)
    return fade(y[:n_(0.8)] * 0.6, 0.0005, 0.5), 0.0, 0.0, False


# ---------------------------------------------------------------------------------------------------- foley
def r_letterbox(rng, sp, action='lift', **_):
    """Our front door's letterbox (the new set's letterbox flaps and mail slots). lift: the flap pushed up slowly from
    outside, its spring straining (slowed a little); close: the flap snapping shut; rattle: three quick flaps."""
    P = _op('slot', ('letterbox_flap', 'metal_mail_slot', 'mailbox_metal_spring_open_close', 'mailbox_2_metal_open'),
            'phrase', gap=0.15, max_len=1.2, keep=-18)
    if action == 'rattle':
        ev = [(k * rng.uniform(0.11, 0.16), P.get(rng, rj=0.05, fo=0.05)[:n_(0.25)] * (0.9 - 0.2 * k)) for k in range(3)]
        y = _seq(ev, 0.4)
    elif action == 'lift':
        g = P.get(rng, rj=0.03, fo=0.1)
        y = _varispeed(st(g), 0.82, 0.78, int(len(g) / 0.8)) * 0.8
    else:
        y = P.get(rng, rj=0.03, fo=0.08)
    return fade(y, 0.003, 0.1), 0.0, 0.0, False


def r_locker(rng, sp, action='open', **_):
    """A school locker (the new set's metal locker doors): open (the latch and the door), close, slam (in the hall)."""
    if action == 'slam':
        g = _op('lk_slam', ('doors_metal_slam_hall', 'doors_metal_open_close_slam'), 'onset', gap=0.2, max_len=1.5,
                keep=-16).get(rng, rj=0.03, fo=0.15)
    else:
        g = _op('lk', ('medicine_locker_metal', 'keys_in_locker', 'doors_metal_open_close_slam'), 'phrase', gap=0.15,
                max_len=1.2, keep=-18).get(rng, rj=0.04, fo=0.1)
        g = g * (0.8 if action == 'close' else 0.7)
    return fade(g, 0.002, 0.12), 0.0, 0.0, False


def r_bucket_down(rng, sp, **_):
    """Mom's bucket set down by the door: a plastic bucket full of water on concrete, the water slopping."""
    g = _op('bucket', ('bucket_full_of_water_set_down', 'bucket_with_water_inside_put_down'), 'phrase', gap=0.25,
            max_len=1.5, keep=-18).get(rng, rj=0.03, fo=0.2)
    return fade(g, 0.002, 0.2), 0.0, 0.0, False


def r_bucket_water(rng, sp, dur=3.0, **_):
    """Water moving in the bucket (the brush dunked, the water poured out on the path)."""
    E = src(has=['water_movement_plastic_bucket', 'water_pour_bucket', 'water_drip_movement_in_metal_bucket'])
    y = excerpt(E[int(rng.integers(len(E)))], dur, rng, 0.5) if E else st(noise(dur, 6)) * 0.01
    return fade(y, 0.1, 0.4), 0.0, 0.0, False


def r_drawer(rng, sp, action='open', **_):
    """Adam's desk drawer: the new set's drawer slides, the metal taken off and a small wooden body added."""
    g = _op('drawer', ('drawers_metal',), 'phrase', gap=0.2, max_len=1.2, keep=-18).get(rng, rj=0.04, fo=0.1)
    body = modal([150.0, 330.0, 690.0], [0.04, 0.02, 0.01], [1.0, 0.4, 0.15], 0.12, int(rng.integers(1 << 30)),
                 exc=0.004)
    y = _seq([(0.0, eq(lp(st(g), 3500, 2), ('peak', 2600, -6.0, 1.0))), (len(g) / SR * 0.85, st(body) * 0.3)], 0.15)
    return fade(y, 0.004, 0.1), 0.0, 0.0, False


def r_fork_plate(rng, sp, **_):
    """'Mom put her fork down.': one piece of cutlery set down on a china plate (the new set's), quiet and deliberate."""
    g = _op('fork', ('knife_cutlery_put_down_on_china_plate', 'cutlery_handful_down_on_plate'), 'onset', gap=0.15,
            max_len=0.8, keep=-16).get(rng, rj=0.02, fo=0.1)
    return fade(eq(g, ('hs', 6000, -3.0, 0.7)), 0.001, 0.12), 0.0, 0.0, False


def r_indicator(rng, sp, dur=6.0, rate=None, **_):
    """Mom's car indicator at the red light (the new set's interior turn indicators), from inside the cabin."""
    E = src(has=['turn_indicator', 'hazard_warning_lights_internal'])
    y = excerpt(E[int(rng.integers(len(E)))], dur, rng, 0.6) if E else st(noise(dur, 7)) * 0.001
    if rate:
        y = _varispeed(y, float(rate) / 1.5, float(rate) / 1.5, int(len(y) * 1.5 / float(rate)))
    return fade(y, 0.05, 0.2), 0.0, 0.0, False


def r_car_cabin(rng, sp, dur=12.0, indicator=False, **_):
    """BED: inside Mom's car at a red light: the engine idling through the floor (the new set's interior idles,
    low-passed: we are in the cabin), optionally the indicator."""
    E = src(has=['interior_car_diesel_engine_idle', 'cadillac_1960_on_board_idle'])
    y = excerpt(E[int(rng.integers(len(E)))], dur, rng, 1.0) if E else r_car_idle(rng, sp, dur=dur)[0]
    y = eq(lp(st(y), 1800, 2), ('ls', 120, 2.0, 0.7))
    if indicator:
        y = _ob_add(y, r_indicator(rng, sp, dur=dur)[0] * 0.35)
    return fade(y[:n_(dur)], 0.8, 1.2), 0.0, 0.0, False


def r_sneaker_squeak(rng, sp, n=1, **_):
    """A white sneaker squeaking on the wet step / the school floor (the new set's sneaker squeaks)."""
    P = _op('sneak', ('sneakers_squeak', 'shoe_squeaks'), 'onset', gap=0.1, max_len=0.5, keep=-18)
    ev = [(k * rng.uniform(0.35, 0.5), P.get(rng, rj=0.04, fo=0.05)) for k in range(int(n))]
    return fade(_seq(ev, 0.2), 0.002, 0.06), 0.0, 0.0, False


def r_shoebox_lid(rng, sp, action='off', **_):
    """The shoebox Danny slides over: its cardboard lid lifted off / put on (the new set's shoebox lids)."""
    g = _op('lid', ('shoe_box_put_on_lid', 'cardboard_box_lid_put_on'), 'phrase', gap=0.15, max_len=1.2,
            keep=-18).get(rng, rj=0.03, fo=0.1)
    if action == 'off':
        g = fade(g[:int(len(g) * 0.6)] * 0.7, 0.03, 0.08)     # the lid lifting: the slide without the final tap
    return fade(g, 0.003, 0.1), 0.0, 0.0, False


def r_cafeteria(rng, sp, dur=20.0, **_):
    """BED: the lunch hall: the new set's cafeteria walla and cutlery, distant, the top taken off (kids far off)."""
    E = src(has=['walla_cafeteria_indoor', 'restaurant_bar_cafeteria_big'])
    y = excerpt(E[int(rng.integers(len(E)))], dur, rng, 1.5) if E else st(noise(dur, 8)) * 0.01
    y = eq(lp(hp(st(y), 150, 2), 4500, 2), ('peak', 2500, 2.0, 1.0))
    return fade(y, 1.0, 1.5), 0.0, 0.0, False


def r_school_corridor(rng, sp, dur=20.0, **_):
    """BED: the school corridor between lessons: the cafeteria walla far down the hall, a locker slamming now and
    then far off, the fluorescent hum overhead."""
    w = r_cafeteria(rng, sp, dur=dur)[0]
    w = reverb(lp(w, 1500, 2), 'hall', 0.35, 0.01) * 0.5
    h = r_floodlight_hum(rng, sp, dur=dur)[0] * 0.15
    ev = []
    t = rng.uniform(2.0, 5.0)
    while t < dur - 2.0:
        ev.append((t, lp(r_locker(rng, sp, action='slam')[0], 2500, 2) * 0.12)); t += rng.uniform(5.0, 9.0)
    s = _seq(ev, 1.0) if ev else np.zeros((n_(1), 2), np.float32)
    return fade(_ob_add(w[:n_(dur)], h[:n_(dur)], reverb(s, 'hall', 0.5, 0.01)[:n_(dur)]), 1.0, 1.5), 0.0, 0.0, False


OBSESSION_ALIASES = {
    'chalk': ('chalk_scrape', {}), 'chalk_write': ('chalk_scrape', {'kind': 'write'}),
    'chalk_letters': ('chalk_scrape', {'kind': 'write'}), 'chalk_creep': ('chalk_scrape', {'kind': 'creep'}),
    'chalk_slide': ('chalk_scrape', {'kind': 'slide'}), 'chalk_flat': ('chalk_scrape', {'kind': 'flatten'}),
    'chalk_rise': ('chalk_scrape', {'kind': 'rise'}), 'neck_stretch': ('chalk_scrape', {'kind': 'stretch'}),
    'chalk_fingers': ('chalk_scrape', {'kind': 'creep'}), 'stub_drop': ('chalk_stub_drop', {}),
    'stub_roll': ('chalk_roll', {}), 'chalk_stub_roll': ('chalk_roll', {}), 'dust_whoosh': ('chalk_dust_whoosh', {}),
    'drain': ('chalk_dust_whoosh', {}), 'touch_tap': ('phone_tap', {}), 'screen_tap': ('phone_tap', {}),
    'key_tap': ('phone_tap', {}), 'phone_buzz': ('phone_vibrate', {'n': 1}), 'buzz': ('phone_vibrate', {'n': 1}),
    'swing': ('swing_creak', {}), 'swings': ('swing_chains', {}), 'scrub': ('brush_scrub', {}),
    'brush': ('brush_scrub', {}), 'roller': ('paint_roll', {}), 'paint_roller': ('paint_roll', {}),
    'floodlight_clank': ('clank', {}), 'breaker': ('clank', {}), 'letterbox_lift': ('letterbox', {'action': 'lift'}),
    'letterbox_close': ('letterbox', {'action': 'close'}), 'letterbox_rattle': ('letterbox', {'action': 'rattle'}),
    'mail_flap': ('letterbox', {}), 'locker_open': ('locker', {'action': 'open'}),
    'locker_close': ('locker', {'action': 'close'}), 'locker_slam': ('locker', {'action': 'slam'}),
    'bucket': ('bucket_down', {}), 'bucket_set_down': ('bucket_down', {}), 'water_slosh': ('bucket_water', {}),
    'desk_drawer': ('drawer', {}), 'fork_down': ('fork_plate', {}), 'fork': ('fork_plate', {}),
    'turn_signal': ('indicator', {}), 'car_interior': ('car_cabin', {}), 'red_light': ('car_cabin', {'indicator': True}),
    'flood_hum': ('floodlight_hum', {}), 'squeak': ('sneaker_squeak', {}), 'sneaker': ('sneaker_squeak', {}),
    'shoebox': ('shoebox_lid', {}), 'box_lid': ('shoebox_lid', {}), 'lunch_hall': ('cafeteria', {}),
    'lunch': ('cafeteria', {}), 'corridor': ('school_corridor', {}), 'hallway_school': ('school_corridor', {}),
    'night_suburb': ('suburb_night', {}), 'night_ambience': ('suburb_night', {}), 'wind': ('wind_gust', {}),
    'drain_wind': ('wind_gust', {'strength': 0.8}), 'hoodie': ('cloth_rustle', {'kind': 'grab'}),
    'landing_light': ('light_switch', {}), 'switch': ('light_switch', {}), 'footsteps_walk': ('footsteps_hall', {}),
    'footsteps_run': ('footsteps_hall', {'rate': 3.2, 'weight': 0.7}), 'footsteps_wood': ('footsteps_wood_inside', {}),
    'footsteps_stair': ('footsteps_stairs', {}), 'footsteps_pavement': ('footsteps_porch', {}),
}
# final mix: the rest of film.py's names (no keyword guesses: card_slide had fallen to a jar lid, the phone set
# face-down to a notification, five beds were skipped)
OBSESSION_ALIASES.update({
    'school_lunch_hall': ('cafeteria', {}), 'house_morning': ('room_tone_house', {}),
    'house_evening': ('room_tone_house', {}), 'playground_day': ('school_pickup', {}),
    'playground_evening': ('ambience_suburb', {}), 'suburb_dawn': ('ambience_dawn', {}),
    'card_drop': ('paper', {}), 'card_slide': ('paper_slide', {}), 'phone_screen_light': ('phone_tap', {}),
    'phone_face_down': ('tablet_down', {}), 'car_interior_idle': ('car_cabin', {}),
    'car_indicator': ('indicator', {}), 'bucket_slosh': ('bucket_water', {}), 'footsteps_gravel': ('footsteps_porch', {}),
    'floodlight_on': ('floodlight', {'action': 'on'}), 'porch_light_click': ('porch_light', {}),
    'letterbox_flap': ('letterbox', {}), 'drawer_open': ('drawer', {'action': 'open'}),
})
ALIASES.update(OBSESSION_ALIASES)
KEYWORDS = [('chalk', 'chalk_scrape'), ('stub', 'chalk_stub_drop'), ('dust', 'chalk_dust_whoosh'),
            ('letterbox', 'letterbox'), ('slot', 'letterbox'), ('swing', 'swing_creak'), ('locker', 'locker'),
            ('bucket', 'bucket_down'), ('scrub', 'brush_scrub'), ('roller', 'paint_roll'), ('paint', 'paint_roll'),
            ('cafeteria', 'cafeteria'), ('corridor', 'school_corridor'), ('drawer', 'drawer'), ('fork', 'fork_plate'),
            ('plate', 'fork_plate'), ('indicator', 'indicator'), ('signal', 'indicator'), ('flood', 'floodlight'),
            ('clank', 'clank'), ('sneaker', 'sneaker_squeak'), ('squeak', 'sneaker_squeak'),
            ('shoebox', 'shoebox_lid'), ('buzz', 'phone_vibrate'), ('tap', 'chalk_tap')] + KEYWORDS
