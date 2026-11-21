# sfx_ice.py: THIS film's SFX block ("If The Ice Cream Truck Plays Its Song In Winter... DON'T GO OUTSIDE").
# Run inside sfx.py's namespace (sfx.py execs it just before RECIPES, like every earlier film's block), so it uses
# sfx.py's helpers directly (src, _has, pool, grains, audio, excerpt, reverb, eq, lp, hp, bp, modal, sub_boom, noise,
# fade, pnorm, place, _seq, rate, pan, st, mono, onset_s, peak). Sources: the owner's new Epidemic set first
# (W/samples/epidemic_ice, names ice_* in epidemic_catalog.ICE_MAP), then the earlier sets; synthesis only fills gaps
# (leg clicks' chitin modes, the jaw's pop, the furnace relay, varispeed run-downs, the truck's doppler glide).
# Every source and licence: audio/ATTRIBUTION.md. Verdicts on the new files: W/mix/sfx_review.md.
#
# NAMES the picture emits (film.py sfx cues {t, name, gain_db, pan, params, space}); params in brackets.
#   night / cold     cold_night [dur, creaks 0..1, inside] (BED: icy wind over the roofs, distant creaks),
#                    frozen_still [dur] (BED: still frozen air, ice ticks, a far tree crack), house_hum [dur] (BED:
#                    the powered house: fridge + furnace fan), house_cold [dur] (BED: the dead house after the cut)
#   snow             snow_walk / snow_run / snow_deep [n, dur, rate, approach, foot], snow_scuff, mitten_drop,
#                    boot_stuck (the boot frozen to the snow, ice creaking under the pull), boot_rip (foot ripped out)
#   shovels / plow   shovel_scrape [far] (Kessler's 6 AM scrape), shovel_morning [dur] (BED: three people shoveling),
#                    plow_pass [dur, peak] (the snowplow, its blade), plow_horn [n, gap] (horn blaring)
#   his truck        truck_idle [dur, far, inside] (BED: an idling van in the cold), truck_glide [dur, peak] (the
#                    truck gliding by: engine only, NO tire sound), serving_window [open], truck_speaker (his speaker
#                    horn switching on: pop and hum)
#   the cone         door_tap (soft tap at the front door), cone_set (soft frosty set-down on the doormat),
#                    window_crack (the kitchen window open a crack), cone_shatter (shatters like glass on the floor)
#   power / cold in  furnace_die (relay click, fan winding down), power_cut (the house hum stopping, lights out),
#                    furnace_start (the morning: the chimney smokes again), frost_creep [dur] (frost on the glass,
#                    inside), doorknob_frost, frost_wipe (frost wiped off the bathroom window)
#   radio            radio_squelch [on], radio_static [dur, bells 0..1] (BED), radio_bells (his burst of bells in the
#                    static), radio_clean (Dad's clean key-up: no bells)
#   transformation   skin_stretch, bone_crack [n], jaw_drop (the deep pop), uniform_tear (bulge, split),
#                    leg_punch (a leg punching out of the uniform and planting with a hard click)
#   spider legs      leg_click [surface metal|wood|ice|snow, n], leg_stab_snow [n], leg_spear_coat, scuttle [surface
#                    fence|car|roof, dur], attic_crawl [dur] (clicks crossing the ceiling), hatch_drop, leg_tip_tile
#                    (a needle tip sliding under the door on tile), blanket_yank, towel_jam
#   street / end     porch_light [far], street_wakes [n] (porch lights clicking on, doors opening along the street),
#                    door_open_street, ambulance [dur] (arriving), cocoa_mug (a mug set down), curtain_yank
#   aliases          door_knock_soft, pounding (Mom at the door), knee_deep, glide, chime_far ... (ICE_ALIASES)
# Spaces added: 'snow' (out in deep snow: dead, no slap), 'cold_street' (the street at minus forty: clear and far),
# 'attic_above' (from the hallway, through the ceiling). Unknown names fall back through resolve() (KEYWORDS) and a
# name nothing fits is skipped by mix.py with a warning, never a crash.

ICE_NAMES = ('cold_night', 'frozen_still', 'house_hum', 'house_cold', 'snow_walk', 'snow_run', 'snow_deep',
             'snow_scuff', 'mitten_drop', 'boot_stuck', 'boot_rip', 'shovel_scrape', 'shovel_morning', 'plow_pass',
             'plow_horn', 'truck_idle', 'truck_glide', 'serving_window', 'truck_speaker', 'door_tap', 'cone_set',
             'window_crack', 'cone_shatter', 'furnace_die', 'power_cut', 'furnace_start', 'frost_creep',
             'doorknob_frost', 'frost_wipe', 'radio_squelch', 'radio_static', 'radio_bells', 'radio_clean',
             'skin_stretch', 'bone_crack', 'jaw_drop', 'uniform_tear', 'leg_punch', 'leg_click', 'leg_stab_snow',
             'leg_spear_coat', 'scuttle', 'attic_crawl', 'hatch_drop', 'leg_tip_tile', 'blanket_yank', 'towel_jam',
             'porch_light', 'street_wakes', 'door_open_street', 'ambulance', 'cocoa_mug', 'curtain_yank', 'door_slam')
NAMES = NAMES + ICE_NAMES
# one-shots: momentary max, LU rel the voice at gain_db 0; beds: integrated
LEVEL_LU.update(cold_night=-25, frozen_still=-30, house_hum=-31, house_cold=-32, snow_walk=-9, snow_run=-7,
                snow_deep=-7, snow_scuff=-10, mitten_drop=-14, boot_stuck=-7, boot_rip=-4, shovel_scrape=-12,
                shovel_morning=-22, plow_pass=-6, plow_horn=-3, truck_idle=-26, truck_glide=-12, serving_window=-6,
                truck_speaker=-10, door_tap=-8, cone_set=-9, window_crack=-9, cone_shatter=-1, furnace_die=-6,
                power_cut=-3, furnace_start=-12, frost_creep=-14, doorknob_frost=-9, frost_wipe=-10,
                radio_squelch=-9, radio_static=-20, radio_bells=-4, radio_clean=-10, skin_stretch=-5,
                bone_crack=-3, jaw_drop=-1, uniform_tear=-3, leg_punch=-1, leg_click=-6, leg_stab_snow=-4,
                leg_spear_coat=-3, scuttle=-7, attic_crawl=-10, hatch_drop=-2, leg_tip_tile=-12, blanket_yank=-5,
                towel_jam=-4, porch_light=-10, street_wakes=-9, door_open_street=-10, ambulance=-14, cocoa_mug=-9,
                curtain_yank=-6, door_slam=-2)
PEAK_CAP.update(door_slam=-3.0, cone_shatter=-2.0, power_cut=-3.0, jaw_drop=-2.0, leg_punch=-2.0, bone_crack=-3.0, hatch_drop=-3.0,
                plow_horn=-4.0, leg_stab_snow=-3.0, leg_spear_coat=-3.0, towel_jam=-3.0, boot_rip=-4.0,
                uniform_tear=-3.0, radio_bells=-4.0, furnace_die=-4.0, serving_window=-4.0, leg_click=-4.0,
                door_tap=-5.0, snow_run=-5.0, snow_deep=-5.0)
BEDS = BEDS + ('cold_night', 'frozen_still', 'house_hum', 'house_cold', 'truck_idle', 'shovel_morning')
DUR_BEDS = DUR_BEDS + ('radio_static', 'frost_creep', 'attic_crawl', 'scuttle', 'ambulance')
BED_BUS = BED_BUS + ('cold_night', 'frozen_still', 'house_hum', 'house_cold', 'truck_idle', 'shovel_morning',
                     'radio_static')
HITS = HITS + ('cone_shatter', 'power_cut', 'jaw_drop', 'leg_punch', 'hatch_drop', 'bone_crack', 'radio_bells')
SPACE_LU.update(snow=-1.0, cold_street=-3.0, attic_above=-4.0)
SPACE_ALIAS.update(yard='snow', front_yard='snow', snowbank='snow', birch_lane='cold_street', across_street='cold_street',
                   kessler='cold_street', kesslers='cold_street', ceiling='attic_above', hallway_ceiling='attic_above',
                   living_room='close', kitchen='close', bath='bathroom', truck='street', serving='street',
                   window_pink='street', frosted_door='door', front_door='door', walkie='radio', radio3='radio')
SPACES = tuple(SPACE_LU)
DEFAULT_SPACE.update({k: 'dry' for k in ('cold_night', 'frozen_still', 'house_hum', 'house_cold', 'truck_idle',
                                        'shovel_morning', 'radio_static', 'attic_crawl')})
DEFAULT_SPACE.update(snow_walk='snow', snow_run='snow', snow_deep='snow', snow_scuff='snow', mitten_drop='snow',
                     boot_stuck='snow', boot_rip='snow', shovel_scrape='cold_street', plow_pass='dry', plow_horn='dry',
                     truck_glide='dry', serving_window='street', truck_speaker='street', door_tap='inside',
                     cone_set='porch', window_crack='close', cone_shatter='close', furnace_die='inside',
                     power_cut='inside', furnace_start='inside', frost_creep='close', doorknob_frost='close',
                     frost_wipe='bathroom', radio_squelch='close', radio_bells='close', radio_clean='close',
                     skin_stretch='street', bone_crack='street', jaw_drop='street', uniform_tear='street',
                     leg_punch='street', leg_click='street', leg_stab_snow='snow', leg_spear_coat='snow',
                     scuttle='snow', hatch_drop='inside', leg_tip_tile='bathroom', blanket_yank='snow',
                     towel_jam='bathroom', porch_light='cold_street', street_wakes='dry', door_open_street='cold_street',
                     ambulance='dry', cocoa_mug='close', curtain_yank='close', door_slam='inside')


def _space_ice(y, kind, seed=0, wet=None):
    if kind == 'snow':                                  # deep snow: everything absorbed, no slap; the street far off
        x = eq(y, ('hs', 6000, -2.0, 0.7))
        return reverb(x, 'street', 0.10 if wet is None else wet, 0.012)
    if kind == 'cold_street':                           # across the street at minus forty: clear, far, a dry slap
        x = eq(lp(y, 7000, 2), ('ls', 200, -3.0, 0.7))
        x = reverb(x, 'street', 0.38 if wet is None else wet, 0.02)
        sl = np.zeros_like(x); k = n_(0.14); sl[k:] = x[:-k] * 0.12
        return x + lp(sl, 2500, 2)
    if kind == 'attic_above':                           # in the attic, heard from below through the ceiling
        x = lp(reverb(y, 'attic', 0.35 if wet is None else wet, 0.003), 2400, 2)
        return eq(x, ('peak', 180, 3.0, 1.0))
    return None


_space_prev_ice = space


def space(y, kind, seed=0, wet=None):             # noqa: F811 (this film's spaces first, then every earlier one)
    r = _space_ice(st(y), kind, seed, wet)
    return r if r is not None else _space_prev_ice(y, kind, seed, wet)


# ---------------------------------------------------------------------------------------------------- helpers
def _ip(key, name, keys=(), mode='onset', **seg):
    """A grain pool over the files serving source name `name` (keys narrow it)."""
    return pool('ice_' + key + '|' + ','.join(keys), lambda: (_has(name, *keys) or src(name)) if keys else src(name),
                mode, **seg)


def _ix(name, keys, dur, rng, xfade=1.5):
    E = (_has(name, *keys) if keys else src(name)) or src(name)
    return excerpt(_pick(rng, E), float(dur), rng, xfade)


def _vary(y, r):
    """Varispeed by a ratio curve r (len(y)): r < 1 slower and lower."""
    y = st(y); n = len(y)
    pos = np.cumsum(np.asarray(r, float)); pos = np.clip(pos - pos[0], 0, n - 2)
    end = int(np.searchsorted(pos, n - 2)); pos = pos[:max(2, end)]
    i = pos.astype(np.int64); f = (pos - i)[:, None].astype(np.float32)
    return (y[i] * (1 - f) + y[i + 1] * f).astype(np.float32)


def _pass(y, peak_t, depth=0.06, width=0.9, lo_gain=-14.0):
    """A pass-by: pitch ratio 1+depth falling to 1-depth around peak_t, pan sweep, level rising and falling."""
    y = st(y); n = len(y); t = np.arange(n) / SR
    u = (t - peak_t) / 1.6
    r = 1 + depth * (-np.tanh(u))
    z = _vary(y, r); m = len(z); tt = np.arange(m) / SR
    uu = (tt - peak_t) / 1.6
    g = 10 ** ((lo_gain * (1 - 1 / (1 + uu ** 2))) / 20)
    p = np.clip(np.tanh(uu) * width, -1, 1)
    out = np.stack([z[:, 0] * g * np.sqrt((1 - p) / 2) * 1.414, z[:, 1] * g * np.sqrt((1 + p) / 2) * 1.414], 1)
    cut = 2500 + 9000 / (1 + uu ** 2)                    # distance takes the top off
    return lp(out.astype(np.float32), float(np.median(cut)), 1)


def _chitin(rng, surface='metal', hard=1.0):
    """One leg plant: a hard chitin click (synth modes) + a recorded metal click + the surface's own body."""
    s = int(rng.integers(1 << 20))
    c = st(modal([2600 * rng.uniform(0.9, 1.15), 4100 * rng.uniform(0.9, 1.1), 7300], [0.006, 0.004, 0.002],
                 [1.0, 0.6, 0.35], 0.05, s)) * 0.8
    try:
        P = _ip('click', 'ice_metal_click', (), 'onset', gap=0.08, max_len=0.25, keep=-18)
        c = _seq([(0, c), (0.0, hp(P.get(rng, rj=0.08)[:n_(0.12)], 900, 2) * 0.55)], 0.05)
    except KeyError:
        pass
    body = {'metal': ([420, 1130, 2240], [0.05, 0.03, 0.02]), 'wood': ([180, 410, 950], [0.03, 0.02, 0.012]),
            'ice': ([1800, 3300, 5200], [0.03, 0.02, 0.012]), 'tile': ([1500, 2900, 4600], [0.02, 0.015, 0.01]),
            'snow': ([90, 160, 300], [0.02, 0.015, 0.01])}.get(surface, ([420, 1130, 2240], [0.05, 0.03, 0.02]))
    b = st(modal(body[0], body[1], [0.7, 0.4, 0.25], 0.2, s + 1)) * (0.5 if surface != 'snow' else 0.2)
    y = _seq([(0, c * hard), (0.0, b)], 0.1)
    if surface == 'snow':
        y = _seq([(0, y * 0.5), (0.0, _snow_crunch(rng, 0.9))], 0.1)
    if surface == 'ice':
        try:
            y = _seq([(0, y), (0.004, hp(_ip('icetick', 'ice_ice_crackle', (), 'onset', gap=0.05, max_len=0.2,
                                               keep=-20).get(rng, rj=0.1)[:n_(0.15)], 1500, 2) * 0.4)], 0.1)
        except KeyError:
            pass
    return fade(y, 0.0005, 0.03)


def _snow_crunch(rng, hard=0.7, deep=False):
    P = _ip('crunch', 'ice_snow_walk', (), 'onset', gap=0.2, max_len=0.6, keep=-18)
    g = P.get(rng, rj=0.06, fo=0.05)
    if deep:
        g = eq(rate(g, 0.86), ('ls', 160, 4.0, 0.7))
    return g * (0.5 + 0.5 * hard)


def _snow_steps(rng, src_name, key, n, dur, rate_, approach, deep=False, weight=0.7):
    P = _ip(key, src_name, (), 'onset', gap=0.18 if not deep else 0.3, max_len=0.7 if not deep else 1.0, keep=-20)
    n = int(n or max(1, round((dur or 3.0) * rate_)))
    ev = []; t = 0.0
    for k in range(n):
        g = P.get(rng, rj=0.05, fo=0.05)
        if deep:                                         # knee-deep: the leg plunges, a slower heavier crunch, a drag
            g = eq(rate(g, rng.uniform(0.8, 0.88)), ('ls', 150, 5.0, 0.7))
            try:
                dr = _ip('scuff', 'ice_snow_scuff', (), 'phrase', gap=0.2, max_len=0.8, keep=-20).get(rng, rj=0.08)
                g = _seq([(0, g), (rng.uniform(0.05, 0.12), lp(dr[:n_(0.5)], 3000, 2) * 0.45)], 0.05)
            except KeyError:
                pass
        prog = k / max(1, n - 1)
        gdb = approach * (prog - 0.5) * 9 + (-1.0 if k % 2 else 0) + rng.normal(0, 0.7)
        g = lp(g, 9000 * 2 ** (approach * (prog - 0.5) * 1.2), 1) * 10 ** (gdb / 20) * (0.6 + 0.6 * weight)
        ev.append((t, pan(g, 0.07 if k % 2 else -0.07)))
        t += (1.0 / rate_) * (1 + 0.06 * rng.standard_normal())
    return _seq(ev, 0.4)


def _bells(dur, seed):
    try:
        import chime_ice as CH
        return CH.bells(float(dur), int(seed))
    except Exception as e:                               # never lose the cue over the bells
        warn(f'chime bells unavailable ({repr(e)[:60]}): a synthetic bell')
        return st(modal([1318.5, 1760.0, 2349.3], [0.6, 0.5, 0.4], [1, 0.6, 0.4], float(dur), seed)) * 0.3


def _radio_band(y, lo=320.0, hi=3100.0, drive=1.8):
    m = mono(y)
    m = eq(lp(hp(m, lo, 4), hi, 4), ('peak', 1500, 3.0, 1.0))
    pk = peak(m) + 1e-9
    return st((np.tanh(drive * m / pk) / np.tanh(drive) * pk).astype(np.float32))


# ---------------------------------------------------------------------------------------------------- night / cold
def r_cold_night(rng, sp, dur=30.0, creaks=0.4, inside=False, **_):
    """BED: the cold snap over Birch Lane: icy wind over the roofs (the new set's winter winds, the low roar cut, a
    thin whistle kept), the still frozen air between gusts, distant creaks of frozen wood now and then.
    inside=True: through the walls (dark, low, 10 dB down)."""
    d = float(dur)
    y = _ix('ice_wind', ('general',), d, rng, 2.5)
    y = eq(lp(hp(y, 140, 2), 7000, 2), ('peak', 2400, -2.0, 0.8))
    g = _ix('ice_wind', ('designed',), d, rng, 3.0)
    y = y + lp(hp(g, 500, 2), 5000, 2) * 0.35            # the thin whistle over the roofs
    if creaks > 0:
        try:
            C = _ip('creak', 'ice_creaks', (), 'phrase', gap=0.3, max_len=2.5, keep=-22)
            t = rng.uniform(3, 8)
            while t < d - 3:
                if rng.uniform() < creaks:
                    c = reverb(lp(C.get(rng, rj=0.1), 2600, 2) * 0.22, 'street', 0.5)
                    place(y, pan(c, rng.uniform(-0.7, 0.7)), n_(t))
                t += rng.uniform(6, 15)
        except KeyError:
            pass
    if inside:
        y = lp(y, 900, 2) * 0.3
    return fade(y, 1.5, 2.0), 0.0, 0.0, False


def r_frozen_still(rng, sp, dur=20.0, **_):
    """BED: still frozen air: almost nothing (a faint low air), ice ticking somewhere close, a far tree or eave cracking
    in the cold once in a while."""
    d = float(dur)
    y = lp(hp(_ix('ice_wind', ('general',), d, rng, 3.0), 100, 2), 900, 2) * 0.25
    try:
        T = _ip('tick', 'ice_ice_crackle', ('subtle',), 'onset', gap=0.06, max_len=0.25, keep=-22)
        B = _ip('farcrack', 'ice_ice_break', (), 'onset', gap=0.3, max_len=1.5, keep=-14)
        t = rng.uniform(0.5, 2)
        while t < d - 1:
            place(y, pan(hp(T.get(rng, rj=0.1), 1200, 2) * 0.06, rng.uniform(-0.8, 0.8)), n_(t))
            t += rng.exponential(1.4)
        for t in rng.uniform(3, max(3.5, d - 3), max(1, int(d / 15))):
            place(y, reverb(lp(B.get(rng, rj=0.08), 1800, 2) * 0.12, 'hall', 0.7), n_(t))
    except KeyError:
        pass
    return fade(y, 1.5, 2.0), 0.0, 0.0, False


def r_house_hum(rng, sp, dur=20.0, **_):
    """BED: the house with its power on: the fridge's hum (the doctor set), the furnace's low fan and hiss (the new
    set's wall heater), very low: the sound that STOPS at the power cut."""
    d = float(dur)
    f = lp(_ix('ice_fridge_hum', (), d, rng, 2.0), 1200, 2)
    h = lp(hp(_ix('ice_furnace', ('wall_heater',), d, rng, 2.0), 60, 2), 3000, 2) * 0.6
    return fade(f + h, 0.8, 1.2), 0.0, 0.0, False


def r_house_cold(rng, sp, dur=20.0, **_):
    """BED: the dead house after the cut: no hum at all, the wind outside through the walls, the frame ticking and
    creaking as it contracts, frost fizzing at the glass now and then."""
    d = float(dur)
    y = lp(hp(_ix('ice_wind', (), d, rng, 3.0), 80, 2), 700, 2) * 0.35
    try:
        C = _ip('hcreak', 'ice_creaks', (), 'phrase', gap=0.3, max_len=2.0, keep=-22)
        F = _ip('fizz', 'ice_ice_crackle', ('squeeze',), 'phrase', gap=0.2, max_len=2.0, keep=-22)
        t = rng.uniform(2, 5)
        while t < d - 2:
            if rng.uniform() < 0.5:
                place(y, reverb(lp(C.get(rng, rj=0.08), 2000, 2) * 0.18, 'living', 0.4), n_(t))
            else:
                place(y, pan(hp(F.get(rng, rj=0.1), 1500, 2) * 0.05, rng.uniform(-0.6, 0.6)), n_(t))
            t += rng.uniform(4, 10)
    except KeyError:
        pass
    return fade(y, 1.0, 1.5), 0.0, 0.0, False


# ---------------------------------------------------------------------------------------------------- snow
def r_snow_walk(rng, sp, n=None, dur=None, rate=1.7, approach=0.0, weight=0.7, foot=None, **_):
    """Boots on deep, dry, squeaky snow (the new set's snow walks)."""
    y = _snow_steps(rng, 'ice_snow_walk', 'walk', n, dur, rate, approach, False, weight)
    if foot in ('L', 'R'):
        y = pan(y, -0.08 if foot == 'L' else 0.08)
    return eq(hp(y, 90, 2), ('peak', 2800, 2.0, 0.9)), min(0.12, onset_s(y, -12)), 0.0, False


def r_snow_run(rng, sp, n=None, dur=None, rate=3.0, approach=0.0, weight=0.9, foot=None, **_):
    """Running in snow (the new set's snow runs, single strides cut out)."""
    y = _snow_steps(rng, 'ice_snow_run', 'run', n, dur, rate, approach, False, weight)
    return eq(hp(y, 90, 2), ('peak', 2600, 2.0, 0.9)), min(0.1, onset_s(y, -12)), 0.0, False


def r_snow_deep(rng, sp, n=None, dur=None, rate=1.6, approach=0.0, weight=1.0, **_):
    """'Knee-deep snow.' Each leg plunging in and dragging out: a slower, lower crunch with a scuff behind it."""
    y = _snow_steps(rng, 'ice_snow_run', 'deep', n, dur, rate, approach, True, weight)
    return hp(y, 70, 2), min(0.12, onset_s(y, -12)), 0.0, False


def r_snow_scuff(rng, sp, **_):
    """A boot scuffing through snow."""
    y = _ip('scuff1', 'ice_snow_scuff', (), 'phrase', gap=0.2, max_len=1.2, keep=-18).get(rng, rj=0.06, fo=0.08)
    return hp(y, 90, 2), min(0.1, onset_s(y, -14)), 0.0, False


def r_mitten_drop(rng, sp, **_):
    """'Lina's mitten drops into the snow.' A soft woollen pat into powder: tiny, close, a hush."""
    g = _snow_crunch(rng, 0.2)[:n_(0.25)]
    g = lp(rate(g, 1.25), 5000, 2) * 0.5
    pat = st(lp(noise(0.05, int(rng.integers(1 << 20))), 1400, 2) * np.hanning(n_(0.05))) * 0.3
    return fade(_seq([(0, pat), (0.005, g)], 0.1), 0.001, 0.08), 0.0, 0.0, False


def r_boot_stuck(rng, sp, **_):
    """'My boot doesn't move. Frozen to the snow.' The pull against the ice: a strained creak of packed ice under load
    (the new set's crunchy ice pressure), a low groan."""
    P = _ip('press', 'ice_ice_crackle', ('crunchy',), 'phrase', gap=0.25, max_len=2.0, keep=-18)
    g = P.get(rng, rj=0.04)[:n_(1.2)]
    g = eq(rate(g, 0.8), ('ls', 200, 4.0, 0.7))
    groan = st(lp(modal([95, 141, 230], [0.4, 0.3, 0.2], [1, 0.5, 0.3], 0.9, int(rng.integers(1 << 20))), 600, 2)) * 0.25
    return fade(_seq([(0, g), (0.1, groan)], 0.2), 0.02, 0.2), 0.0, 0.0, False


def r_boot_rip(rng, sp, **_):
    """'I rip my foot out of the boot.' A crack of the ice seal, a sock sliding out of the boot (cloth friction),
    snow spraying."""
    try:
        c = _ip('seal', 'ice_ice_break', (), 'onset', gap=0.15, max_len=0.4, keep=-14).get(rng, rj=0.05)[:n_(0.3)]
    except KeyError:
        c = st(noise(0.05, 3)) * 0.3
    cl = _ip('slide', 'ice_cloth', ('scrape', 'flap'), 'phrase', gap=0.2, max_len=0.8, keep=-20).get(rng, rj=0.1)[:n_(0.4)]
    spray = _snow_crunch(rng, 1.0)
    y = _seq([(0, hp(c, 300, 2) * 0.9), (0.03, cl * 0.6), (0.12, spray * 0.8)], 0.2)
    return y, onset_s(y, -14), 0.0, False


# ---------------------------------------------------------------------------------------------------- shovels / plow
def r_shovel_scrape(rng, sp, far=True, **_):
    """'Every morning at six, you hear Mr. Kessler's shovel. Scrape.' One long pusher-shovel scrape on the frozen walk
    (the new set's metal snow pusher), and the knock of the blade emptied; far=True: across the street."""
    P = _ip('scrape', 'ice_shovel_scrape', ('metal',), 'phrase', gap=0.35, max_len=3.5, keep=-14)
    g = P.get(rng, rj=0.03, fo=0.2)
    knock = st(modal([310, 720, 1650], [0.05, 0.03, 0.02], [1, 0.5, 0.3], 0.2, int(rng.integers(1 << 20)))) * 0.25
    y = _seq([(0, g), (len(g) / SR + 0.25, knock)], 0.3)
    if far:
        y = lp(y, 4500, 2)
    return y, min(0.15, onset_s(y, -14)), 0.0, False


def r_shovel_morning(rng, sp, dur=20.0, **_):
    """BED: the morning: Dad, Lina and Adam shoveling Kessler's walk: three shovels at three places (left, centre, right),
    each its own rhythm of dig, lift, throw and scrape; the still morning air."""
    d = float(dur)
    y = lp(hp(_ix('ice_wind', ('general',), d, rng, 3.0), 120, 2), 1500, 2) * 0.12
    D = _ip('dig', 'ice_shovel_dig', (), 'phrase', gap=0.3, max_len=2.0, keep=-18)
    S = _ip('mscrape', 'ice_shovel_scrape', (), 'phrase', gap=0.35, max_len=3.0, keep=-14)
    for who, (p, lvl, per) in enumerate(((-0.55, 0.7, 2.6), (0.05, 0.9, 2.2), (0.6, 0.55, 3.1))):   # Dad, Adam, Lina
        t = rng.uniform(0, 1.5)
        while t < d - 1.5:
            g = (S if rng.uniform() < 0.35 else D).get(rng, rj=0.06, fo=0.15)[:n_(2.0)]
            place(y, pan(g * lvl * 0.5, p), n_(t))
            t += per * rng.uniform(0.8, 1.3)
    return fade(reverb(y, 'street', 0.2), 1.0, 1.5), 0.0, 0.0, False


def r_plow_pass(rng, sp, dur=9.0, peak=None, **_):
    """'The plow pulled away.' / 'Dad's plow roars onto Birch Lane.' A big truck (the new set's lorry) passing with its
    steel blade grinding the road (metal scrapes slowed and darkened), a doppler sweep; pre_s puts its peak on t."""
    d = float(dur); pk = float(peak if peak is not None else d * 0.5)
    eng = _ix('ice_lorry', ('lorry',), d, rng, 1.5)
    eng = eq(hp(eng, 40, 2), ('ls', 120, 3.0, 0.7))
    bl = _ix('ice_metal_scrape', (), d, rng, 0.5) if src('ice_metal_scrape') else _ix('ice_shovel_scrape', ('metal',), d, rng)
    bl = lp(rate(bl, 0.7), 2600, 2)[:n_(d)]
    y = eng[:n_(d)].copy(); y[:len(bl)] += bl * 0.45
    y = _pass(y, pk, 0.04, 0.8, -16.0)
    return fade(y, 0.5, 1.0), pk, 0.0, False


def r_plow_horn(rng, sp, n=3, gap=0.55, **_):
    """'Horn blaring, again and again.' Air-horn blasts (the new set's fire-truck / truck air horns), n of them."""
    P = _ip('horn', 'ice_air_horn', (), 'phrase', gap=0.25, max_len=2.5, keep=-10)
    ev = []; t = 0.0
    for k in range(int(n)):
        g = P.get(rng, rj=0.01, tilt=0.5, fo=0.08)[:n_(rng.uniform(0.7, 1.4))]
        g = fade(g, 0.01, 0.12)
        ev.append((t, g)); t += len(g) / SR + float(gap) * rng.uniform(0.8, 1.2)
    y = reverb(_seq(ev, 0.3), 'street', 0.25)
    return y, onset_s(y, -14), 0.0, True


# ---------------------------------------------------------------------------------------------------- his truck
def r_truck_idle(rng, sp, dur=20.0, far=False, inside=False, **_):
    """BED: his truck idling at the curb all night: the new set's van idle, slowed a touch and darkened (a low, steady
    hum, never a rattle), the exhaust burble low; far=True across the street; inside=True through the glass."""
    d = float(dur)
    y = rate(_ix('ice_van_idle', (), d / 0.92 + 1, rng, 2.0), 0.92)[:n_(d)]
    y = eq(lp(hp(y, 35, 2), 2200, 2), ('ls', 110, 2.0, 0.7))
    if far:
        y = reverb(lp(y, 1200, 2), 'street', 0.4) * 0.5
    if inside:
        y = lp(y, 500, 2) * 0.4
    return fade(y, 1.5, 2.0), 0.0, 0.0, False


def r_truck_glide(rng, sp, dur=9.0, peak=None, **_):
    """'The truck glides down Birch Lane... Behind it, no tire tracks.' The engine only (the van idle, revved a little
    and swept by): NO tire hiss, no road noise, no crunch of snow; a doppler glide; pre_s puts the closest point on t."""
    d = float(dur); pk = float(peak if peak is not None else d * 0.5)
    y = rate(_ix('ice_van_idle', ('mercedes',), d * 1.1 + 1, rng, 2.0), 1.1)[:n_(d)]
    y = eq(lp(hp(y, 40, 2), 3000, 2), ('ls', 100, 2.0, 0.7))
    y = _pass(y, pk, 0.03, 0.85, -14.0)
    return fade(y, 0.8, 1.2), pk, 0.0, False


def r_serving_window(rng, sp, open=True, **_):
    """'The serving window slides open.' The new set's small plastic sliding window (open or close), a frosty seal
    cracking as it opens, and a warm hiss of air (open)."""
    P = _ip('swin', 'ice_serving_window', (), 'phrase', gap=0.25, max_len=1.5, keep=-14)
    gs = [P.get(rng, rj=0.02) for _ in range(3)]
    g = gs[0] if open else gs[1]
    ev = [(0, g)]
    if open:
        try:
            ev.append((0.0, hp(_ip('seal2', 'ice_ice_crackle', ('subtle',), 'onset', gap=0.05, max_len=0.3,
                                   keep=-18).get(rng, rj=0.1), 1500, 2) * 0.25))
        except KeyError:
            pass
        ev.append((0.1, st(lp(hp(noise(1.2, 9), 600, 2), 3500, 2) * np.hanning(n_(1.2))) * 0.03))
    y = _seq(ev, 0.2)
    return y, onset_s(y, -14), 0.0, False


def r_truck_speaker(rng, sp, **_):
    """His roof speaker horn switching on: a pop through the horn, a short mains hum and a crackle (the chime follows)."""
    s = int(rng.integers(1 << 20))
    pop = st(sub_boom(120, 60, 0.12, 0.6, s)) * 0.6
    t = np.arange(n_(0.6)) / SR
    hum = st((np.sin(2 * np.pi * 120 * t) + 0.4 * np.sin(2 * np.pi * 360 * t)).astype(np.float32) * np.exp(-t / 0.25)) * 0.12
    cr = st(hp(noise(0.3, s + 1), 1500, 2) * (np.random.default_rng(s).uniform(0, 1, n_(0.3)) > 0.98)) * 0.3
    y = _seq([(0, pop), (0.01, hum), (0.02, cr)], 0.2)
    y = mono(y)
    return st(eq(lp(hp(y, 300, 4), 5000, 4), ('peak', 1600, 4.0, 1.4))), 0.0, 0.0, False


# ---------------------------------------------------------------------------------------------------- the cone
def r_door_tap(rng, sp, n=1, **_):
    """'A soft tap at the front door.' One (or n) soft, deliberate knuckle taps on the wood, heard from inside."""
    return r_knock_door(rng, sp, n=int(n), spacing=0.45, force=0.25, soft=True)


def r_cone_set(rng, sp, **_):
    """The cone set down on the doormat: a soft, frosty set-down (a muffled pat on the bristle mat, a tiny crackle of
    frost, the paper wrapper's whisper)."""
    s = int(rng.integers(1 << 20))
    pat = st(lp(noise(0.06, s), 900, 2) * np.hanning(n_(0.06))) * 0.6
    fr = hp(_ip('frost1', 'ice_ice_crackle', ('subtle',), 'onset', gap=0.05, max_len=0.4, keep=-20).get(rng, rj=0.1),
            2000, 2)[:n_(0.35)] * 0.25
    wr = st(bp(noise(0.25, s + 2), 2500, 7000, 2) * np.hanning(n_(0.25))) * 0.05
    y = _seq([(0, pat), (0.01, fr), (0.02, wr)], 0.2)
    return y, 0.0, 0.0, False


def r_window_crack(rng, sp, **_):
    """'The kitchen window is open a crack.' A wooden sash sliding a little (the new set's wood sliding window), the
    cold air hissing in through the gap."""
    P = _ip('kwin', 'ice_house_window', (), 'phrase', gap=0.25, max_len=1.5, keep=-14)
    g = P.get(rng, rj=0.03)[:n_(0.9)]
    air = st(lp(hp(noise(2.0, 4), 800, 2), 5000, 2) * np.minimum(1, np.arange(n_(2.0)) / n_(0.4))) * 0.025
    return fade(_seq([(0, g), (0.2, air)], 0.3), 0.003, 0.5), 0.0, 0.0, False


def r_cone_shatter(rng, sp, **_):
    """'It hits the floor and shatters like glass.' A small hard object hitting the floorboards (a dull knock), then
    glass breaking (the bus / bunny sets' glass, the bright short burst only), an ice crack under it (the new set's ice
    break) and frozen shards skittering away; no boom, it is a small thing."""
    G = _ip('glass', 'ice_glass_break', ('smash',), 'onset', gap=0.2, max_len=1.2, keep=-10)
    g = hp(G.get(rng, rj=0.04, fo=0.3), 500, 2)
    try:
        ic = _ip('icebr', 'ice_ice_break', (), 'onset', gap=0.2, max_len=0.8, keep=-12).get(rng, rj=0.05)[:n_(0.6)]
    except KeyError:
        ic = g * 0
    knock = st(modal([160, 420, 980], [0.05, 0.03, 0.015], [1, 0.4, 0.25], 0.15, int(rng.integers(1 << 20)))) * 0.6
    ev = [(0, knock), (0.004, g * 0.9), (0.006, ic * 0.5)]
    for k in range(6):                                   # shards skittering away on the boards
        tk = st(modal([rng.uniform(3500, 7000)], [0.01], [1.0], 0.03, k)) * rng.uniform(0.05, 0.15)
        ev.append((0.15 + rng.exponential(0.2), pan(tk, rng.uniform(-0.8, 0.8))))
    y = _seq(ev, 0.4)
    return y, onset_s(y, -14), 0.0, False


# ---------------------------------------------------------------------------------------------------- power / cold in
def r_furnace_die(rng, sp, **_):
    """'Click. The furnace stops.' The relay's hard click in the basement, the burner's whoosh cut, the blower fan
    winding down to nothing (the new set's wall-heater run slowed to a stop), a tick of cooling metal."""
    s = int(rng.integers(1 << 20))
    click = st(modal([1900, 3400, 650], [0.01, 0.006, 0.03], [1, 0.6, 0.5], 0.08, s)) * 0.9
    fan = _ix('ice_furnace', ('wall_heater',), 4.0, rng, 0.5)
    r = np.clip(1 - (np.arange(len(fan)) / len(fan)) * 1.15, 0.05, 1) ** 1.4
    fan = _vary(fan, r)
    fan = lp(fan, 3500, 2) * np.linspace(1, 0, len(fan))[:, None] ** 2
    tick = st(modal([2900], [0.02], [1], 0.06, s + 4)) * 0.12
    y = _seq([(0, click), (0.02, fan * 0.6), (2.4, tick)], 0.3)
    return y, 0.0, 0.0, False


def r_power_cut(rng, sp, **_):
    """'Every light in the house goes out.' The house hum (fridge + fan) STOPPING: a mains clunk, the hum's pitch and
    level falling away in half a second, the lights' buzz cut (the new set's light-switch off), then nothing."""
    s = int(rng.integers(1 << 20))
    hum = _ix('ice_fridge_hum', (), 1.2, rng, 0.3)
    r = np.clip(1 - np.arange(len(hum)) / (0.8 * SR), 0.1, 1) ** 2
    hum = _vary(hum, r) * np.linspace(1, 0, len(_vary(hum, r)))[:, None]
    try:
        sw = _ip('swoff', 'ice_light_switch', (), 'onset', gap=0.15, max_len=0.4, keep=-14).get(rng, rj=0.03)[:n_(0.3)]
    except KeyError:
        sw = st(modal([2200, 3800], [0.008, 0.005], [1, 0.5], 0.04, s))
    clunk = st(sub_boom(85, 45, 0.35, 0.3, s)) * 0.5
    y = _seq([(0, sw * 0.8), (0.0, clunk), (0.0, hum * 1.2)], 0.3)
    return y, onset_s(y, -14), 0.0, False


def r_furnace_start(rng, sp, **_):
    """The morning: Kessler's furnace lit again (the new set's boiler start), warm and far."""
    y = _ix('ice_furnace', ('boiler',), 5.0, rng, 0.5)
    return fade(lp(y, 6000, 2), 0.05, 1.0), 0.0, 0.0, False


def r_frost_creep(rng, sp, dur=4.0, **_):
    """'Frost creeps across the windows. On the inside.' A fine, crawling crackle on the glass: the new set's subtle
    ice-pressure cracks and crackle squeezes, thinned to a fizz, getting denser."""
    d = float(dur)
    P = _ip('creep', 'ice_ice_crackle', ('subtle', 'squeeze'), 'onset', gap=0.03, max_len=0.25, keep=-24)
    y = np.zeros((n_(d + 0.5), 2), np.float32)
    t = 0.0
    while t < d:
        g = hp(P.get(rng, rj=0.15), 1800, 2)[:n_(0.2)] * (0.3 + 0.7 * t / d)
        place(y, pan(g * 0.5, rng.uniform(-0.6, 0.6)), n_(t))
        t += rng.exponential(0.09 * (1.4 - t / d))
    return fade(y, 0.2, 0.4), 0.0, 0.0, False


def r_doorknob_frost(rng, sp, **_):
    """'The doorknob grows frost.' A short, close crystalline crackle on metal and a tiny metallic ping as the brass
    contracts."""
    y, _, _, _ = r_frost_creep(rng, sp, dur=1.4)
    ping = st(modal([3150, 5200], [0.25, 0.12], [1, 0.4], 0.6, int(rng.integers(1 << 20)))) * 0.08
    return _seq([(0, y), (0.6, ping)], 0.3), 0.0, 0.0, False


def r_frost_wipe(rng, sp, **_):
    """'I wipe frost off the bathroom window.' A sleeve wiping cold glass: a squeaky, gritty swipe (the new set's
    cloth friction), the frost crumbling off."""
    g = _ip('wipe', 'ice_cloth', ('scrape',), 'phrase', gap=0.2, max_len=1.2, keep=-18).get(rng, rj=0.05)[:n_(0.9)]
    fr = hp(_ip('crumb', 'ice_ice_crackle', ('crunchy',), 'onset', gap=0.05, max_len=0.3, keep=-20).get(rng, rj=0.1),
            1500, 2)[:n_(0.3)] * 0.3
    return _seq([(0, eq(g, ('peak', 2500, 4.0, 1.0))), (0.1, fr)], 0.2), 0.0, 0.0, False


# ---------------------------------------------------------------------------------------------------- radio
def r_radio_squelch(rng, sp, on=True, **_):
    """The two-way radio: the key-up click and squelch burst (on) or the squelch tail (off) (the bus set's walkie)."""
    P = _ip('sq', 'ice_squelch', ('engage', 'squelch'), 'phrase', gap=0.15, max_len=0.6 if on else 0.4, keep=-14)
    g = P.get(rng, rj=0.03)
    return _radio_band(g, 350, 3200, 1.5), 0.0, 0.0, True


def r_radio_static(rng, sp, dur=3.0, bells=0.0, **_):
    """BED (dur): radio static between words (the bus set's station-search crackle), radio band; bells 0..1: HIS bells
    hidden in it (chime_ice.bells through the same band) for the jammed calls."""
    d = float(dur)
    y = _radio_band(_ix('ice_static', ('station',), d, rng, 0.5), 300, 3400, 1.4)
    if bells and bells > 0:
        b = _radio_band(_bells(d, int(rng.integers(1 << 20))), 700, 3600, 1.2)
        y[:min(len(y), len(b))] += b[:min(len(y), len(b))] * 0.6 * float(bells)
    return fade(y, 0.05, 0.2), 0.0, 0.0, True


def r_radio_bells(rng, sp, dur=2.2, **_):
    """'Static. Bells.' His burst: the squelch opens, the static swells hard and his bells ring right through it
    (chime_ice bells through the radio band), then cut."""
    d = float(dur)
    sq = _ip('sq2', 'ice_squelch', ('squelch',), 'phrase', gap=0.15, max_len=0.5, keep=-14).get(rng, rj=0.03)
    stat = _ix('ice_static', (), d, rng, 0.3) * np.linspace(0.5, 1, n_(d))[:, None]
    b = _bells(d, int(rng.integers(1 << 20)))
    y = _seq([(0, sq), (0.05, stat), (0.1, b * 1.4)], 0.1)
    y = _radio_band(y, 350, 3800, 2.2)
    y[-n_(0.03):] *= np.linspace(1, 0, n_(0.03))[:, None]
    return y, 0.0, 0.0, True


def r_radio_clean(rng, sp, **_):
    """The REAL Dad keying up: a clean squelch click, a short hiss, no bells."""
    g = _ip('sq3', 'ice_squelch', ('engage',), 'phrase', gap=0.15, max_len=0.35, keep=-14).get(rng, rj=0.02)
    h = st(bp(noise(0.25, 6), 500, 3000, 2)) * 0.03
    return _radio_band(_seq([(0, g), (0.05, h)], 0.1), 350, 3200, 1.2), 0.0, 0.0, True


# ---------------------------------------------------------------------------------------------------- transformation
def r_skin_stretch(rng, sp, dur=1.6, **_):
    """'His skin pulls long. White. Hard.' A slow rubbery stretch (the bus set's latex pulls, slowed an octave and
    darkened) with a dry creak of something hardening, no wetness."""
    d = float(dur)
    try:
        g = _ix('glove_squeak', (), d * 0.5 + 0.2, rng, 0.3)
    except KeyError:
        g = st(bp(noise(d, 2), 300, 2000, 2)) * 0.3
    g = lp(rate(g, 0.5), 3500, 2)[:n_(d)]
    cr = lp(_ip('screak', 'ice_door_creak', (), 'phrase', gap=0.3, max_len=2.0, keep=-20).get(rng, rj=0.05), 2500, 2)
    cr = rate(cr, 0.7)[:n_(d)]
    y = _seq([(0, g), (0.2, cr * 0.5)], 0.2)
    return fade(y, 0.15, 0.3), 0.0, 0.0, False


def r_bone_crack(rng, sp, n=1, **_):
    """Bone cracks (the new set's 'Gore' bone files and the bunny set's snaps): only the dry crack transients, cut short
    and high-passed, nothing wet; n cracks."""
    P = _ip('bone', 'ice_bone', (), 'onset', gap=0.12, max_len=0.35, keep=-12)
    ev = []; t = 0.0
    for k in range(int(n)):
        g = hp(P.get(rng, rj=0.05, fo=0.04), 180, 2)[:n_(0.3)]
        ev.append((t, eq(g, ('peak', 1800, 2.0, 1.0)))); t += rng.uniform(0.09, 0.22)
    y = _seq(ev, 0.15)
    return y, onset_s(y, -14), 0.0, False


def r_jaw_drop(rng, sp, **_):
    """'His jaw drops. Down to his chest.' A deep POP (the joint letting go: a low sub pop with a dry crack), a creaking
    hinge sliding down an octave (a door creak slowed), then a hollow, dark air from the open mouth."""
    s = int(rng.integers(1 << 20))
    pop = st(sub_boom(70, 32, 0.6, 0.4, s))
    cr, _, _, _ = r_bone_crack(rng, sp, n=1)
    hinge = _ip('hinge', 'ice_door_creak', (), 'phrase', gap=0.3, max_len=2.0, keep=-20).get(rng, rj=0.03)
    hinge = lp(rate(hinge, 0.5), 2000, 2)[:n_(1.4)] * np.linspace(1, 0.3, n_(1.4))[:len(rate(hinge, 0.5)[:n_(1.4)]), None]
    air = st(lp(hp(noise(1.6, s + 3), 80, 2), 400, 2) * np.hanning(n_(1.6))) * 0.08
    y = _seq([(0, cr * 0.7), (0.0, pop * 0.9), (0.08, hinge * 0.5), (0.3, air)], 0.4)
    return y, onset_s(y, -14), 0.0, False


def r_uniform_tear(rng, sp, **_):
    """'The striped uniform bulges. Splits.' Cloth straining (slow friction), then a hard tear (the bus set's cloth
    rips)."""
    strain = _ip('strain', 'ice_cloth', ('scrape', 'grab'), 'phrase', gap=0.2, max_len=1.2, keep=-20).get(rng, rj=0.05)
    strain = lp(rate(strain, 0.7), 4000, 2)[:n_(0.8)]
    rip = _ip('rip', 'ice_cloth_rip', (), 'phrase', gap=0.15, max_len=0.8, keep=-14).get(rng, rj=0.05)
    y = _seq([(0, strain * 0.5), (0.6, rip)], 0.3)
    return y, 0.6 + onset_s(rip, -14), 0.0, False


def r_leg_punch(rng, sp, surface='metal', **_):
    """'A long brown leg punches out, jointed like a spider's. Click.' A rip of cloth, a fast swish of the leg
    unfolding (three joint clicks), and the hard click as it plants on the truck roof (surface)."""
    rip = _ip('rip2', 'ice_cloth_rip', (), 'phrase', gap=0.15, max_len=0.5, keep=-14).get(rng, rj=0.06)[:n_(0.35)]
    sw = st(bp(noise(0.35, int(rng.integers(1 << 20))), 400, 3000, 2) * np.hanning(n_(0.35)) ** 2) * 0.25
    joints = [(0.12 + 0.05 * k, _chitin(rng, 'wood', 0.35)) for k in range(3)]
    plant = _chitin(rng, surface, 1.2)
    y = _seq([(0, rip * 0.8), (0.05, sw)] + joints + [(0.42, plant * 1.3)], 0.3)
    return y, 0.42, 0.0, False                            # the plant ("Click.") lands on t


def r_leg_click(rng, sp, surface='metal', n=1, **_):
    """One hard leg plant (or n in a run): chitin on metal (the truck roof), wood (fence, floor), ice, tile or snow."""
    ev = [(k * rng.uniform(0.11, 0.2), _chitin(rng, str(surface), 1.0)) for k in range(int(n))]
    y = _seq(ev, 0.15)
    return y, onset_s(y, -14), 0.0, False


def r_leg_stab_snow(rng, sp, n=1, **_):
    """'Legs stab the snow.' A needle leg driving deep into packed snow: a hard crunch with a click at its tip, a
    short thud under it; n stabs."""
    ev = []; t = 0.0
    for k in range(int(n)):
        c = _snow_crunch(rng, 1.0)[:n_(0.35)]
        tip = _chitin(rng, 'ice', 0.7)
        th = st(sub_boom(95, 55, 0.18, 0.2, int(rng.integers(1 << 20)))) * 0.4
        ev += [(t, tip), (t + 0.004, c), (t, th)]
        t += rng.uniform(0.15, 0.35)
    y = _seq(ev, 0.2)
    return y, onset_s(y, -14), 0.0, False


def r_leg_spear_coat(rng, sp, **_):
    """'One spears my coat. I tear free.' A puncture through the padded coat (a short tear), the leg's click, then the
    longer rip of tearing free."""
    p = _ip('rip3', 'ice_cloth_rip', (), 'phrase', gap=0.15, max_len=0.5, keep=-14).get(rng, rj=0.08)[:n_(0.18)]
    tip = _chitin(rng, 'wood', 0.6)
    rip = _ip('rip4', 'ice_cloth_rip', (), 'phrase', gap=0.15, max_len=0.8, keep=-14).get(rng, rj=0.05)
    y = _seq([(0, tip), (0.0, p), (0.35, rip * 0.9)], 0.3)
    return y, onset_s(y, -14), 0.0, False


def r_scuttle(rng, sp, surface='fence', dur=2.0, rate=13.0, **_):
    """'He scuttles along our fence. Over Dad's car. Up onto our roof.' Many legs clicking fast and unevenly over the
    surface: fence (wood rail), car (hollow sheet metal booming), roof (snowy shingles: crunch + wood); rate = clicks/s."""
    d = float(dur); surf = str(surface)
    mat = {'fence': 'wood', 'car': 'metal', 'roof': 'snow', 'ice': 'ice', 'tile': 'tile'}.get(surf, 'wood')
    y = np.zeros((n_(d + 0.5), 2), np.float32)
    t = 0.0; k = 0
    while t < d:
        c = _chitin(rng, mat, rng.uniform(0.5, 1.0))
        if surf == 'car' and k % 5 == 0:
            c = _seq([(0, c), (0, st(modal([92, 141, 260], [0.25, 0.2, 0.1], [1, 0.6, 0.3], 0.5, k)) * 0.35)], 0.1)
        if surf == 'roof' and k % 4 == 0:
            c = _seq([(0, c), (0, _snow_crunch(rng, 0.5)[:n_(0.2)] * 0.5)], 0.1)
        place(y, pan(c, np.clip(-0.6 + 1.2 * t / d + rng.uniform(-0.15, 0.15), -1, 1)), n_(t))
        t += rng.exponential(1.0 / float(rate)); k += 1
    return fade(y, 0.02, 0.2), 0.0, 0.0, False


def r_attic_crawl(rng, sp, dur=4.0, rate=6.0, **_):
    """'Click. Click. Click. Across the ceiling.' Leg plants on the attic joists, heard from below: each a dull click
    through the ceiling with the boards' thump, crossing from one side to the other."""
    d = float(dur)
    y = np.zeros((n_(d + 1.0), 2), np.float32)
    t = 0.0
    while t < d:
        c = _chitin(rng, 'wood', rng.uniform(0.7, 1.0))
        th = st(modal([110, 230], [0.08, 0.05], [1, 0.5], 0.2, int(rng.integers(1 << 20)))) * 0.5
        g = _seq([(0, c), (0, th)], 0.1)
        place(y, pan(g, np.clip(-0.8 + 1.6 * t / d, -1, 1)), n_(t))
        t += rng.uniform(0.6, 1.3) / float(rate) * 3
    y = space(y, 'attic_above', 0)
    return fade(y, 0.01, 0.3), 0.0, 0.0, True


def r_hatch_drop(rng, sp, **_):
    """'The hallway hatch drops open.' The ceiling hatch swinging down hard on its hinges (the new set's wood hatch),
    the bang at the end of its swing, a shower of grit."""
    P = _ip('hatch', 'ice_hatch', ('wood',), 'phrase', gap=0.25, max_len=1.5, keep=-14)
    g = P.get(rng, rj=0.03)
    bang = st(modal([140, 330, 760], [0.12, 0.06, 0.03], [1, 0.5, 0.3], 0.4, int(rng.integers(1 << 20))))
    grit = st(hp(noise(0.6, 7), 2500, 2) * np.exp(-np.arange(n_(0.6)) / n_(0.2))) * 0.04
    y = _seq([(0, g * 0.8), (0.12, bang * 0.9), (0.14, grit)], 0.4)
    return y, 0.12, 0.0, False


def r_leg_tip_tile(rng, sp, dur=1.5, **_):
    """'Under the door, a needle-thin leg tip slides in. Feeling for Lina's sock.' A fine scratch of the needle sliding
    on the tile (metal scrapes, thinned high), tiny taps as it feels around."""
    d = float(dur)
    sc = hp(_ix('ice_metal_scrape', (), d, rng, 0.3) if src('ice_metal_scrape') else st(noise(d, 3)) * 0.2, 2500, 2)
    sc = sc[:n_(d)] * np.linspace(0.3, 1, n_(d))[:len(sc[:n_(d)]), None] * 0.3
    taps = [(rng.uniform(0.2, d), _chitin(rng, 'tile', 0.25)) for _ in range(4)]
    y = _seq([(0, sc)] + taps, 0.2)
    return fade(y, 0.05, 0.2), 0.0, 0.0, False


def r_blanket_yank(rng, sp, **_):
    """'One hooks the blanket and PULLS.' A leg hooking the wool (a click, a snag) and a hard heavy yank of cloth."""
    sn = _chitin(rng, 'wood', 0.5)
    fl = _ip('flap', 'ice_towel', ('flap',), 'onset', gap=0.15, max_len=0.6, keep=-14).get(rng, rj=0.05)
    fl = eq(rate(fl, 0.8), ('ls', 200, 4.0, 0.7))
    sw = st(bp(noise(0.4, 5), 200, 2000, 2) * np.hanning(n_(0.4))) * 0.3
    y = _seq([(0, sn), (0.08, sw), (0.12, fl)], 0.3)
    return y, onset_s(y, -14), 0.0, False


def r_towel_jam(rng, sp, **_):
    """'I jam the towel down on it. Hard.' A folded towel slammed onto the tile (the new set's towel flap, heavy), the
    leg tip crunching under it, a knock of the floor."""
    fl = _ip('towel', 'ice_towel', (), 'onset', gap=0.15, max_len=0.5, keep=-14).get(rng, rj=0.04)
    fl = eq(rate(fl, 0.85), ('ls', 180, 5.0, 0.7))
    tip = _chitin(rng, 'tile', 0.8)
    th = st(modal([120, 260], [0.06, 0.03], [1, 0.4], 0.2, int(rng.integers(1 << 20)))) * 0.6
    y = _seq([(0, fl), (0.01, th), (0.02, tip * 0.6)], 0.3)
    return y, onset_s(y, -14), 0.0, False


# ---------------------------------------------------------------------------------------------------- street / end
def r_porch_light(rng, sp, **_):
    """'Porch lights click on.' A porch-light switch (the new set's light switches), the bulb's faint ping on."""
    g = _ip('sw', 'ice_light_switch', (), 'onset', gap=0.15, max_len=0.4, keep=-14).get(rng, rj=0.04)[:n_(0.3)]
    ping = st(modal([4200], [0.05], [1], 0.1, int(rng.integers(1 << 20)))) * 0.05
    return _seq([(0, g), (0.03, ping)], 0.2), 0.0, 0.0, False


def r_door_open_street(rng, sp, **_):
    """A neighbour's front door opening across the street: the lock, the door unsticking from the frost, its creak."""
    try:
        lk, _, _, _ = r_lock_turn(rng, sp)
    except Exception:
        lk = st(modal([2500, 4100], [0.01, 0.006], [1, 0.5], 0.05, 3))
    cr = _ip('dcreak', 'ice_door_creak', ('wooden',), 'phrase', gap=0.3, max_len=1.6, keep=-18).get(rng, rj=0.05)
    y = _seq([(0, lk * 0.7), (0.35, cr * 0.7)], 0.3)
    return y, 0.0, 0.0, False


def r_street_wakes(rng, sp, n=5, span=4.0, **_):
    """'Porch lights click on. One. Another. Doors open.' n porch lights and doors along Birch Lane, each further away
    and to a different side, over span seconds (the first lands on t)."""
    ev = []
    for k in range(int(n)):
        t = 0.0 if k == 0 else rng.uniform(0.4, 1.0) * span * k / max(1, n - 1)
        far = 0.2 + 0.8 * k / max(1, n - 1)
        g, _, _, _ = r_porch_light(rng, sp)
        g = space(g, 'cold_street', k)
        g = lp(g, 7000 - 4000 * far, 2) * 10 ** (-9 * far / 20)
        ev.append((t, pan(g, rng.choice([-1, 1]) * rng.uniform(0.2, 0.8))))
        if k % 2 == 1:
            d, _, _, _ = r_door_open_street(rng, sp)
            ev.append((t + rng.uniform(0.6, 1.2), pan(lp(space(d, 'cold_street', k), 4000, 2) * 10 ** (-9 * far / 20),
                                                  rng.uniform(-0.8, 0.8))))
    return _seq(ev, 0.5), 0.0, 0.0, True


def r_ambulance(rng, sp, dur=10.0, **_):
    """'Call an ambulance.' The ambulance arriving out of the white: the siren from far off (the doctor set's sirens),
    approaching, its last wail winding down as it pulls up."""
    d = float(dur)
    y = _ix('ice_siren', ('in_motion', 'distant'), d, rng, 1.0)[:n_(d)]
    u = np.linspace(0, 1, len(y))
    y = y * (10 ** ((-18 * (1 - u) ** 1.5) / 20))[:, None].astype(np.float32)
    y = lp(y, 5500, 2)
    tail = int(min(len(y), n_(1.5)))
    r = np.ones(len(y)); r[-tail:] = np.linspace(1, 0.55, tail)
    y = _vary(y, r)
    return fade(y, 1.0, 0.8), 0.0, 0.0, False


def r_cocoa_mug(rng, sp, **_):
    """'Lina brings him cocoa.' A warm mug set down on a wooden table (the dummy set's mug and teacup sounds)."""
    try:
        return r_mug_set(rng, sp)
    except Exception:
        g = _ip('mug', 'ice_mug', (), 'onset', gap=0.15, max_len=0.5, keep=-14).get(rng, rj=0.03)
        return g, onset_s(g, -14), 0.0, False


def r_curtain_yank(rng, sp, **_):
    """'I yank the curtain shut.' A fast, hard draw of the curtain rings along the rod."""
    try:
        y, pre, o, spc = r_curtain_close(rng, sp)
        return rate(y, 1.25), pre, o, spc
    except Exception:
        fl = _ip('cflap', 'ice_cloth', ('flap',), 'onset', gap=0.15, max_len=0.5, keep=-14).get(rng, rj=0.05)
        return fl, 0.0, 0.0, False


def r_door_slam(rng, sp, **_):
    """'I duck under him, get inside, and slam the door.' The front door slammed hard: the wood's impact (the bunny set's
    door impacts), the frame's boom, the latch snapping home."""
    try:
        g = _ip('dslam', 'ice_door_kick', ('impact',), 'onset', gap=0.2, max_len=0.8, keep=-12).get(rng, rj=0.03)
    except KeyError:
        g = st(noise(0.1, 3)) * 0.3
    s_ = int(rng.integers(1 << 20))
    boom = st(modal([95, 180, 410], [0.18, 0.1, 0.05], [1, 0.6, 0.3], 0.5, s_)) * 0.8
    latch = st(modal([2300, 3900], [0.012, 0.008], [1, 0.5], 0.06, s_ + 1)) * 0.5
    y = _seq([(0, g), (0.0, boom), (0.035, latch)], 0.3)
    return y, onset_s(y, -14), 0.0, False


ICE_ALIASES = {
    'wind_night': ('cold_night', {}), 'cold_snap': ('cold_night', {}), 'icy_wind': ('cold_night', {}),
    'still_air': ('frozen_still', {}), 'frozen_air': ('frozen_still', {}), 'room_tone_cold': ('house_cold', {}),
    'house_dead': ('house_cold', {}), 'fridge': ('house_hum', {}), 'snow_steps': ('snow_walk', {}),
    'footsteps_snow': ('snow_walk', {}), 'run_snow': ('snow_run', {}), 'knee_deep': ('snow_deep', {}),
    'scrape': ('shovel_scrape', {}), 'shovel': ('shovel_scrape', {}), 'shoveling': ('shovel_morning', {}),
    'snowplow': ('plow_pass', {}), 'plow': ('plow_pass', {}), 'horn_blaring': ('plow_horn', {'n': 4}),
    'plow_horn_blaring': ('plow_horn', {'n': 5}), 'van_idle_cold': ('truck_idle', {}), 'engine_idle': ('truck_idle', {}),
    'glide': ('truck_glide', {}), 'truck_pass': ('truck_glide', {}), 'window_open': ('serving_window', {'open': True}),
    'window_close': ('serving_window', {'open': False}), 'serving_window_open': ('serving_window', {'open': True}),
    'serving_window_close': ('serving_window', {'open': False}), 'speaker_on': ('truck_speaker', {}),
    'door_knock_soft': ('door_tap', {}), 'tap_door': ('door_tap', {}), 'pounding': ('knock_door', {'n': 4, 'force': 1.0}),
    'pound_door': ('knock_door', {'n': 4, 'force': 1.0}), 'cone_down': ('cone_set', {}), 'cone_doormat': ('cone_set', {}),
    'shatter': ('cone_shatter', {}), 'glass_shatter': ('cone_shatter', {}), 'furnace_stop': ('furnace_die', {}),
    'furnace_click': ('furnace_die', {}), 'lights_out': ('power_cut', {}), 'blackout': ('power_cut', {}),
    'frost': ('frost_creep', {}), 'frost_glass': ('frost_creep', {}), 'knob_frost': ('doorknob_frost', {}),
    'squelch': ('radio_squelch', {}), 'radio_on': ('radio_squelch', {'on': True}),
    'radio_off': ('radio_squelch', {'on': False}), 'static': ('radio_static', {}), 'static_bells': ('radio_bells', {}),
    'bells_static': ('radio_bells', {}), 'radio_jam': ('radio_bells', {}), 'stretch': ('skin_stretch', {}),
    'bone_cracks': ('bone_crack', {'n': 3}), 'jaw_pop': ('jaw_drop', {}), 'tear_uniform': ('uniform_tear', {}),
    'leg_out': ('leg_punch', {}), 'leg_burst': ('leg_punch', {}), 'click': ('leg_click', {}),
    'leg_plant': ('leg_click', {}), 'stab_snow': ('leg_stab_snow', {}), 'leg_stab': ('leg_stab_snow', {}),
    'coat_spear': ('leg_spear_coat', {}), 'scuttle_fence': ('scuttle', {'surface': 'fence'}),
    'scuttle_car': ('scuttle', {'surface': 'car'}), 'scuttle_roof': ('scuttle', {'surface': 'roof'}),
    'ceiling_clicks': ('attic_crawl', {}), 'attic_clicks': ('attic_crawl', {}), 'hatch': ('hatch_drop', {}),
    'needle_tile': ('leg_tip_tile', {}), 'leg_under_door': ('leg_tip_tile', {}), 'yank_blanket': ('blanket_yank', {}),
    'towel': ('towel_jam', {}), 'porch_lights': ('street_wakes', {}), 'doors_open': ('street_wakes', {'n': 4}),
    'siren_arrive': ('ambulance', {}), 'mug': ('cocoa_mug', {}), 'cocoa': ('cocoa_mug', {}),
    'boot_frozen': ('boot_stuck', {}), 'foot_rip': ('boot_rip', {}), 'mitten': ('mitten_drop', {}),
    'kitchen_window': ('window_crack', {}), 'curtain_shut': ('curtain_yank', {}), 'wipe_frost': ('frost_wipe', {}),
    # the earlier films' loose words that would land on the wrong sound here
    'horn': ('plow_horn', {}), 'bone': ('bone_crack', {}), 'slam': ('door_slam', {}), 'door_shut': ('door_slam', {}),
    'door_open': ('door_creak', {}), 'door_close': ('door_slam', {}), 'stab': ('leg_stab_snow', {}),
    'spider': ('scuttle', {}), 'crawl': ('attic_crawl', {}), 'engine': ('truck_idle', {}), 'pop': ('jaw_drop', {}),
    'glass': ('cone_shatter', {}), 'siren': ('ambulance', {}), 'legs': ('scuttle', {}), 'skin': ('skin_stretch', {}),
    'tear': ('uniform_tear', {}), 'rip': ('uniform_tear', {}),
}
ALIASES.update(ICE_ALIASES)
# keyword guesses for unknown names: this film's first (the bus film's 'radio' -> dash_radio, 'horn' -> bus_horn and
# 'idle' -> bus_idle guesses would put a school bus into Birch Lane)
KEYWORDS = [('snow', 'snow_walk'), ('shovel', 'shovel_scrape'), ('plow', 'plow_pass'), ('horn', 'plow_horn'),
            ('truck', 'truck_idle'), ('idle', 'truck_idle'), ('window', 'serving_window'), ('cone', 'cone_set'),
            ('shatter', 'cone_shatter'), ('furnace', 'furnace_die'), ('power', 'power_cut'), ('frost', 'frost_creep'),
            ('ice', 'frost_creep'), ('radio', 'radio_squelch'), ('static', 'radio_static'), ('bell', 'radio_bells'),
            ('bone', 'bone_crack'), ('jaw', 'jaw_drop'), ('leg', 'leg_click'), ('click', 'leg_click'),
            ('scuttle', 'scuttle'), ('attic', 'attic_crawl'), ('hatch', 'hatch_drop'), ('towel', 'towel_jam'),
            ('blanket', 'blanket_yank'), ('porch', 'porch_light'), ('siren', 'ambulance'), ('ambulance', 'ambulance'),
            ('mug', 'cocoa_mug'), ('wind', 'cold_night'), ('curtain', 'curtain_yank'), ('mitten', 'mitten_drop'),
            ('boot', 'boot_stuck'), ('tap', 'door_tap'), ('knock', 'knock_door')] + KEYWORDS
