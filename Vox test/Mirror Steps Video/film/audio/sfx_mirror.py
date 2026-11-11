"""SFX for "If An Eighth Step Appears On Your Mirror...": the 56 new names of plan/sound_plan.json (names.new), plus
overrides of room_tone / clock_tick, the queen's presence layer and this film's perspectives. Installed into sfx.py
(`sfx.install` is called at import), so use it through sfx.render / sfx.render_event like every other name.

Sources, in this order: the owner's new Epidemic files (catalog_epidemic_mirror.json via library.mirror()), the police
film's Epidemic files and the free library (library.entries), then synthesis layers (modal glass / bell partials, stick-
slip friction, sub thumps, formant calls). Every name is layered 2-4 deep, varied by seed, and processed per space.

Spaces (SPACE_LU offsets in brackets)
    close [+1]   near, small wooden cabin early reflections        inside [0]  the cabin room (Cabin 7)
    outside [-3] night exterior (forest IR, open)                  far [-8]    distance: low-pass, wet forest tail
    mirror [-4]  heard through the glass: low-pass 4 kHz, hollow comb, small bright glass room
    memory [-3]  memories: low-pass 5 kHz, tape wow, wide hall      phone / dry / police spaces as in sfx.py

Names and parameters (all accept seed/space/level; beds take dur)
  beds      ambience_camp_night dur owl=1 wind=0.6 | ambience_dawn dur loop=None (seconds: an exactly seamless loop of
            that length) stutter=0 (0..1 detune + stutter) | ambience_memory dur | ambience_mirror dur | room_tone dur |
            lantern_hum dur | wind_chimes dur | tv_through_wall dur | kitchen_far dur | coffee_percolator dur |
            queen_presence dur (whispers, reversed breaths, time shimmer)
  bells     bell_cracked strike='clapper'|'padlock'|'drop'|'touch'|'roll', part=None|'note'|'rattle'
            (THE REAL BELL: a clean hand-bell note, then a thin rattle like a dropped spoon: the crack's buzz on the
            upper partials + 8-14 bouncing metal clinks)   bell_clean (THE FAKE: the same bell's measured partials
            resynthesised with no beating, 4-6 s decay, long church reverb)   spoon_drop kind=None|'clink'
  glass     nail_click_glass (one crisp nail click + a short glass ring)  glass_tap  glass_resonance (pane ring/hum)
            lipstick_draw strokes=1 clean=False | lipstick_smear kind=None|'crumb' | glass_wipe strokes|n soft sleeve
  cloth     towel_cloth kind='flap'|'rub'|'pull'|'snatch'|'throw' | towel_drop | cloth_grab kind=None|'sock'|'lace' |
            cloth_press kind='satin'|'stretch'|'creak' dur | jacket_cloth kind=None|'scrape' | lace_pull n=1 | tape_peel
  wood      bed_creak kind=None|'pat' | wood_thud | body_fall | crate_break | crate_creak | mirror_handle
            kind='creak'|'bump'|'scrape' | screen_door | window_slide | door_creak (sfx.py)
  water     water_drip n=1 kind=None|'pour' dur | drop_reverse | sprinkler_spit kind=None|'die' n rhythm loop_id
            (loop_id: mix.py renders the cue once per loop_id and reuses the identical buffer)
  steps     bare_foot_step | wet_footstep bare=True | footsteps_run dur approach=-1 | footsteps_gravel n|dur wet soft
  metal     gate_chain kind=None|'fence'|'tape_flutter' | gate_creak | padlock | excavator_creak
  misc      candy_wrapper | flashlight_click | phone_handle kind='set_down'|'pick_up' | phone_message | watch_beep n=2 |
            clock_tick dur bpm (Epidemic wall clock) | clock_tick_backward n=1 | chair_scrape | bus_door dur |
            kids_far dur | voices_calling_far dur | owl dist | moth_flutter dur
"""
import hashlib
import numpy as np

X = None          # the sfx module (set by install)
NEW_LEVEL_LU = dict(
    ambience_camp_night=-24, ambience_dawn=-26, ambience_memory=-27, ambience_mirror=-30, room_tone=-31,
    lantern_hum=-38, wind_chimes=-30, tv_through_wall=-31, kitchen_far=-29, coffee_percolator=-28, queen_presence=-16,
    bare_foot_step=-6, bed_creak=-8, bell_clean=-3, bell_cracked=-3, body_fall=-3, bus_door=-10, candy_wrapper=-9,
    chair_scrape=-10, clock_tick_backward=-4, cloth_grab=-9, cloth_press=-10, crate_break=-2, crate_creak=-7,
    drop_reverse=-8, excavator_creak=-17, flashlight_click=-9, footsteps_gravel=-9, footsteps_run=-8, gate_chain=-6,
    gate_creak=-7, glass_resonance=-6, glass_tap=-8, glass_wipe=-6, jacket_cloth=-10, kids_far=-17, lace_pull=-11,
    lipstick_draw=-7, lipstick_smear=-7, mirror_handle=-7, moth_flutter=-17, nail_click_glass=-3, owl=-18, padlock=-5,
    phone_handle=-8, phone_message=-8, screen_door=-8, spoon_drop=-6, sprinkler_spit=-8, tape_peel=-9, towel_cloth=-8,
    towel_drop=-6, voices_calling_far=-17, watch_beep=-12, water_drip=-8, wet_footstep=-8, window_slide=-9,
    wood_thud=-3, clock_tick=-8,
    impact_hit=1, stinger=0, braam=-1, sub_drop=-2,          # hits: REF_MIRROR hit peak +3 / +10 LU over the voice
    towel_whip=-8, lipstick_stamp=-1, number_thump=-3, ring_tick=-11, rubber_stamp=-4, tape_rewind=-9)   # v3: cards
NEW_BEDS = ('ambience_camp_night', 'ambience_dawn', 'ambience_memory', 'ambience_mirror', 'lantern_hum', 'wind_chimes',
            'tv_through_wall', 'kitchen_far', 'coffee_percolator', 'queen_presence', 'kids_far', 'voices_calling_far')
NEW_SPACES = dict(far=-8.0, mirror=-4.0, memory=-3.0, outside=-3.0, inside=0.0, close=1.0)
NEW_DEFAULT_SPACE = dict(ambience_camp_night='outside', ambience_dawn='inside', ambience_memory='memory',
                         ambience_mirror='mirror', bell_clean='far', kids_far='memory', voices_calling_far='memory',
                         bus_door='memory', excavator_creak='outside', owl='far', gate_chain='outside',
                         gate_creak='outside', footsteps_gravel='outside', footsteps_run='far', wind_chimes='outside',
                         tv_through_wall='outside', kitchen_far='far', coffee_percolator='far', queen_presence='mirror',
                         wet_footstep='mirror', clock_tick='inside', clock_tick_backward='inside', lantern_hum='close')
_PEAK = dict(impact_hit=-2.0, stinger=-2.0, braam=-2.5, sub_drop=-2.5, bell_cracked=-5.0, crate_break=-4.0, nail_click_glass=-5.0, wood_thud=-5.0, body_fall=-5.0,
             lipstick_stamp=-3.0, number_thump=-4.0, rubber_stamp=-5.0, ring_tick=-10.0,
             clock_tick_backward=-5.0, bell_clean=-6.0, glass_resonance=-6.0)
_CACHE = {}


# ============================================================================================ helpers
def E(*kw):
    """Mirror-film Epidemic entries whose slug contains every keyword."""
    return X.LIB.mirror(*kw)


def P(key, entries, mode='onset', **seg):
    uniq = list({e['id']: e for e in entries}.values())          # one entry can match two keyword sets
    return X.pool('mx:' + key, lambda: uniq, mode, **seg)


def ex(entries, dur, rng, xfade=1.5):
    e = entries[int(rng.integers(len(entries)))]
    return X.excerpt(e, dur, rng, xfade)


def h32(s):
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)


def env_exp(n, att, tau):
    t = np.arange(n) / X.SR
    return ((1 - np.exp(-t / max(att, 1e-4))) * np.exp(-t / tau)).astype(np.float32)


def burst(dur, lo, hi, att, tau, seed):
    """Band-limited noise burst (stereo), envelope attack att, exponential decay tau."""
    y = X.bp(X.noise(dur, seed), lo, hi, 2) * env_exp(X.n_(dur), att, tau)
    return X.st(y)


def stickslip(dur, f0, jitter, seed, lo=700, hi=3200, rise=0.0):
    """Waxy friction: band-passed noise gated by an irregular pulse train (stick-slip) around f0 Hz."""
    rng = np.random.default_rng(seed); n = X.n_(dur); g = np.zeros(n, np.float32); t = 0.0
    while t < dur:
        i = int(t * X.SR); w = X.n_(rng.uniform(0.002, 0.006))
        g[i:i + w] += np.hanning(min(w, n - i)) * rng.uniform(0.5, 1.0)
        t += 1.0 / (f0 * (1 + rise * t / dur)) * (1 + rng.uniform(-jitter, jitter))
    y = X.bp(X.noise(dur, seed + 1), lo, hi, 2) * (0.25 + g)
    return X.st(y)


def shift(y, st_):
    return X.rate(y, X.semis(st_))


def thump(f0=90, f1=50, dur=0.25, seed=0):
    return X.st(X.sub_boom(f0, f1, dur, 0.0, seed))


def wood_knock(rng, f=(150, 330, 610, 1150), dur=0.35, amp=(1, 0.6, 0.35, 0.2)):
    d = [0.09, 0.05, 0.03, 0.02]
    return X.st(X.modal([fi * rng.uniform(0.95, 1.05) for fi in f], d, amp, dur, int(rng.integers(1 << 30)), 0.0015))


def ir_glass():
    if 'glass' not in X._IR:
        X._IR['glass'] = X._unit(X._shoebox((1.3, 1.1, 1.7), (0.4, 0.5, 0.9), (0.8, 0.6, 0.9),
                                            (0.93, 0.93, 0.92, 0.93, 0.9, 0.93), 4, (0.5, 0.7, 0.8, 0.7, 0.5), 1.0, 31))
    return X._IR['glass']


def ir_cabin():
    if 'cabin' not in X._IR:
        X._IR['cabin'] = X._unit(X._shoebox((5.2, 4.4, 2.6), (1.6, 1.3, 1.1), (3.5, 3.0, 1.5),
                                            (0.78, 0.8, 0.76, 0.8, 0.62, 0.8), 3, (0.55, 0.5, 0.42, 0.32, 0.22), 1.0, 22))
    return X._IR['cabin']


def conv(y, h, wet, dry=1.0, predelay=0.0, hpf=None):
    y = X.st(y); s = X.hp(y, hpf) if hpf else y
    w = X._conv(s, h) * wet
    out = np.zeros((len(y) + len(h) + X.n_(predelay), 2), np.float32)
    out[:len(y)] += y * dry
    X.place(out, w, X.n_(predelay))
    return X._trim_tail(out)


def wow(y, depth_ms=1.4, f=0.55, seed=0):
    """Tape wow and flutter: a slowly varying delay line."""
    y = X.st(y); n = len(y); t = np.arange(n) / X.SR
    ph = np.random.default_rng(seed).uniform(0, 6.28, 3)
    d = (depth_ms * (np.sin(2 * np.pi * f * t + ph[0]) + 0.35 * np.sin(2 * np.pi * 3.3 * t + ph[1]))
         + 0.12 * np.sin(2 * np.pi * 11 * t + ph[2]) + 3.0) * 1e-3 * X.SR
    idx = np.arange(n) - d
    return np.stack([np.interp(idx, np.arange(n), y[:, c]) for c in range(2)], 1).astype(np.float32)


def comb(y, delays=(0.0029, 0.0047), gains=(0.42, 0.28)):
    y = X.st(y); out = y.copy()
    for d, g in zip(delays, gains):
        k = X.n_(d); out[k:] += y[:-k] * g
    return out


def loop_seamless(y, period, xf=1.2):
    """Exactly `period` seconds that tile without a seam (the tail crossfaded into the head)."""
    n, k = X.n_(period), X.n_(xf)
    if len(y) < n + k:
        y = np.pad(y, ((0, n + k - len(y)), (0, 0)))
    out = y[:n].copy()
    w = np.sin(np.linspace(0, np.pi / 2, k)) ** 2
    out[:k] = y[:k] * w[:, None] + y[n:n + k] * (1 - w)[:, None]
    return out


# ============================================================================================ spaces
_POLICE_SPACE = None


def space(y, kind, seed=0, wet=None):
    """Perspective processing for this film (police kinds are passed through to sfx.py's original space())."""
    y = X.st(y)
    if kind in (None, 'dry'):
        return y
    if kind == 'close':
        return conv(y, ir_cabin(), 0.09 if wet is None else wet, predelay=0.001)
    if kind == 'inside':
        return conv(X.lp(y, 14000, 1), ir_cabin(), 0.32 if wet is None else wet)
    if kind == 'outside':
        return X.width(X.reverb(X.lp(y, 12000, 1), 'forest', 0.22 if wet is None else wet, 0.004, hpf=90), 0.85)
    if kind == 'far':
        x = X.eq(X.lp(X.hp(y, 140, 2), 3600, 2), ('peak', 900, -2, 0.9))
        return X.width(X.reverb(x, 'forest', 0.65 if wet is None else wet, 0.03, dry=0.55), 0.6)
    if kind == 'mirror':
        x = comb(X.lp(X.hp(y, 90, 2), 4000, 2))
        x = conv(x, ir_glass(), 0.42 if wet is None else wet, predelay=0.004)
        return X.width(x, 0.75)
    if kind == 'memory':
        x = wow(X.lp(X.hp(y, 120, 2), 5000, 2), seed=seed)
        x = X.sat(x, 1.3)
        return X.width(X.reverb(x, 'hall', 0.32 if wet is None else wet, 0.015, hpf=200), 1.15)
    return _POLICE_SPACE(y, kind, seed, wet)


# ============================================================================================ beds
def r_ambience_camp_night(rng, sp, dur=30.0, owl=1.0, wind=0.6, **_):
    lake = ex(E('lake', 'frogs'), dur, rng, 3.0)
    lay = [(0, lake)]
    cr = E('forest', 'night', 'crickets')
    if cr:
        c = X.lp(ex(cr, dur, rng, 3.0), 9000, 2)
        lay.append((0, c * 0.45 * X.peak(lake) / (X.peak(c) + 1e-9)))
    fo = X.src(category='sfx/ambience', has=['ambforst_night'])
    if fo:
        f = ex(fo, dur, rng, 2.0); lay.append((0, X.lp(f, 7000, 2) * 0.3 * X.peak(lake) / (X.peak(f) + 1e-9)))
    W = X.src(category='sfx/ambience', has=['civitas__wind'])
    if W and wind > 0:
        w = ex(W, dur, rng, 2.0); lay.append((0, X.lp(X.hp(w, 80), 2500, 2) * wind * 0.5 * X.peak(lake) / (X.peak(w) + 1e-9)))
    O = X.src(category='sfx/ambience', has=['owl'])
    if O and owl > 0:
        t = rng.uniform(6, 30)
        while t < dur - 4:
            o = X.audio(O[int(rng.integers(len(O)))])
            o = X.pan(X.fade(X.pnorm(X.lp(o, 2200, 2)), 0.01, 0.3), rng.uniform(-0.8, 0.8)) * X.peak(lake) * 0.35
            lay.append((t, X.reverb(o, 'forest', 0.6))); t += rng.uniform(35, 70) / owl
    return X.fade(X._seq(lay, 0)[:X.n_(dur)], 1.0, 1.5), 0.0, 0.0, False


_DAWN = {}


def _dawn_window(e, length):
    """Start of the calmest `length` s of the dawn chorus (lowest crest of 1 s RMS: avoids roosters and close calls)."""
    k = (e['id'], round(length, 2))
    if k not in _DAWN:
        y = X.mono(X.audio(e)); hop = X.SR // 2
        r = np.array([np.sqrt(np.mean(y[i:i + X.SR] ** 2) + 1e-12) for i in range(0, len(y) - X.SR, hop)])
        w = int(length * 2)
        best = min(range(0, max(1, len(r) - w)), key=lambda i: (r[i:i + w].max() / np.median(r[i:i + w])))
        _DAWN[k] = best * 0.5
    return _DAWN[k]


def r_ambience_dawn(rng, sp, dur=20.0, loop=None, stutter=0.0, **_):
    """The other side: a dawn chorus with no wind and no rumble. loop=19.48 renders exactly one seamless loop."""
    B = E('birdsong', 'dawn')
    if not B:
        y = ex(X.src(category='sfx/ambience', has=['crow']) or X.src('ambience_night'), dur, rng)
    else:
        e = B[0]; L = (loop or dur) + 1.5
        a = X.audio(e); s0 = X.n_(_dawn_window(e, min(L, 60.0)))
        y = a[s0:s0 + X.n_(L)] if not (dur > 60 and not loop) else X.excerpt(e, dur, rng, 3.0)
    y = X.eq(X.hp(y, 260, 3), ('hs', 7000, -3, 0.7), ('peak', 2500, 1.5, 0.8))
    if loop:
        y = loop_seamless(y, loop)
    if stutter > 0:                                   # the loop is breaking: pitch wobble + 80 ms repeats
        y = wow(y, 6 * stutter, 0.9, int(rng.integers(1 << 20)))
        n = X.n_(0.08)
        for i in range(0, len(y) - 2 * n, X.n_(0.7)):
            if rng.uniform() < stutter * 0.6:
                y[i + n:i + 2 * n] = y[i:i + n]
    if not loop:
        y = X.fade(y[:X.n_(dur)], 0.6, 0.8)
    return y, 0.0, 0.0, False


def r_ambience_memory(rng, sp, dur=10.0, **_):
    B = E('birdsong', 'dawn')
    lay = []
    if B:
        b = X.excerpt(B[0], dur, rng, 2.0); lay.append((0, X.lp(b, 7000, 2)))
    L = E('lake', 'frogs')
    if L:
        l = X.lp(ex(L, dur, rng), 3000, 2); lay.append((0, l * 0.4))
    kids = r_kids_far(rng, 'memory', dur=dur)[0]
    lay.append((0, kids * 0.12))
    y = X._seq(lay, 0)[:X.n_(dur)]
    return X.fade(y, 0.4, 0.6), 0.0, 0.0, False


def r_ambience_mirror(rng, sp, dur=10.0, **_):
    """Inside the glass: hollow glassy room tone, a faint high whine, sub pressure, a breath of whisper."""
    R = E('room_tone', 'wooden_cabin')
    base = ex(R, dur, rng, 2.0) if R else X.st(X.lp(X.noise(dur, 3), 3000, 2) * 0.01)
    base = comb(X.pnorm(base), (0.0031, 0.0052, 0.0083), (0.5, 0.35, 0.2))
    t = np.arange(X.n_(dur)) / X.SR
    whine = (np.sin(2 * np.pi * 6280 * t) + 0.6 * np.sin(2 * np.pi * 6293 * t)) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t))
    sub = np.sin(2 * np.pi * 29.1 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * t + 1))
    glass = sum(a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) for f, a in ((587.3, 1), (880.6, 0.5), (1318.5, 0.25)))
    glass = glass * (0.5 + 0.5 * np.sin(2 * np.pi * 0.045 * t)) ** 2
    lay = [(0, base), (0, X.st(whine.astype(np.float32)) * 0.006), (0, X.st(sub.astype(np.float32)) * 0.18),
           (0, X.st(X.lp(glass.astype(np.float32), 2000, 1)) * 0.02)]
    Wh = E('whisper', 'ghostly')
    if Wh:
        w = X.lp(ex(Wh, dur, rng, 2.0), 2500, 2); lay.append((0, w * 0.06 * X.peak(base) / (X.peak(w) + 1e-9)))
    y = conv(X._seq(lay, 0)[:X.n_(dur)], ir_glass(), 0.5)[:X.n_(dur)]
    return X.fade(y, 0.8, 1.0), 0.0, 0.0, True


def r_room_tone(rng, sp, dur=10.0, **_):
    R = E('room_tone', 'wooden_cabin')
    if R:
        y = X.lp(ex(R, dur, rng, 2.0), 9000, 2)
    else:
        E2 = X.src('room_tone', has=['roomtone']) or X.src('room_tone'); y = X.lp(ex(E2, dur, rng, 2.0), 9000, 2)
    return X.fade(y, 0.5, 0.8), 0.0, 0.0, False


def r_lantern_hum(rng, sp, dur=10.0, **_):
    t = np.arange(X.n_(dur)) / X.SR
    h = sum((0.7 / k) * np.sin(2 * np.pi * 120 * k * t + rng.uniform(0, 6)) for k in range(1, 7))
    coil = np.sin(2 * np.pi * 8930 * t) * 0.04
    nz = X.bp(X.noise(dur, int(rng.integers(1 << 20))), 2000, 6000, 2) * 0.05
    y = X.st((h * 0.4 + coil + nz).astype(np.float32))
    return X.fade(y, 0.4, 0.4), 0.0, 0.0, False


def r_wind_chimes(rng, sp, dur=8.0, **_):
    C = X.src(category='sfx/ambience', has=['windchimes'])
    if C:
        y = X.hp(ex(C, dur, rng, 1.5), 400, 2)
    else:
        y = r_kitchen_far(rng, sp, dur=dur)[0]
    return X.fade(y, 0.4, 0.6), 0.0, 0.0, False


def _murmur(rng, dur, st_=0.0):
    M = X.src('crowd_whisper', has=['restaurant', 'crowd', 'talk'])
    m = ex(M, dur + 1, rng, 1.0)
    return shift(m, st_)[:X.n_(dur)] if st_ else m[:X.n_(dur)]


def r_tv_through_wall(rng, sp, dur=4.0, **_):
    m = _murmur(rng, dur, -1.0)
    m = X.eq(X.lp(X.hp(m, 180, 2), 1100, 3), ('peak', 450, 4, 1.0))
    t = np.arange(len(m)) / X.SR
    m = m * (0.75 + 0.25 * np.sin(2 * np.pi * 0.31 * t))[:, None]
    return X.fade(m, 0.3, 0.5), 0.0, 0.0, False


def r_kitchen_far(rng, sp, dur=3.0, **_):
    lay = [(0, X.bp(X.st(X.noise(dur, int(rng.integers(1 << 20)))), 3000, 8000, 2) * 0.02)]       # griddle hiss
    C = P('clinks', E('small', 'decorative_bell') + E('glass', 'tap'), 'onset', gap=0.08, max_len=0.3, keep=-24)
    t = rng.uniform(0.1, 0.6)
    while t < dur - 0.3:
        g = X.fade(C.get(rng, rj=0.1, fo=0.05)[:X.n_(0.12)], 0.001, 0.05)
        lay.append((t, X.pan(shift(g, rng.uniform(-7, 2)) * rng.uniform(0.2, 0.6), rng.uniform(-0.6, 0.6))))
        t += rng.exponential(0.5) + 0.1
    lay.append((0, _murmur(rng, dur, 0) * 0.08))
    return X.fade(X._seq(lay, 0)[:X.n_(dur)], 0.3, 0.5), 0.0, 0.0, False


def r_coffee_percolator(rng, sp, dur=2.0, **_):
    n = X.n_(dur); y = np.zeros(n, np.float32); t = 0.0
    while t < dur - 0.06:
        L = rng.uniform(0.015, 0.045); k = X.n_(L); tt = np.arange(k) / X.SR
        f = rng.uniform(280, 700) * (1 + 1.8 * tt / L)
        b = np.sin(2 * np.pi * np.cumsum(f) / X.SR) * np.hanning(k) * rng.uniform(0.3, 1)
        i = int(t * X.SR); y[i:i + k] += b[:n - i]
        t += rng.exponential(1 / 22)
    gurgle = X.lp(X.noise(dur, int(rng.integers(1 << 20))), 220, 2) * 0.6
    out = X.st(y * 0.5 + gurgle) + X.bp(X.st(X.noise(dur, 7)), 3500, 9000, 2) * 0.02
    return X.fade(out, 0.2, 0.3), 0.0, 0.0, False


def r_queen_presence(rng, sp, dur=2.0, **_):
    """The queen near the glass: female whisper grains (some reversed), a ghostly whisper bed, a reversed breath and the
    time-magic shimmer slowed and lowered."""
    lay = []
    Wf = P('qwhisper', E('whisper', 'female') + E('whisper', 'ghostly'), 'phrase', gap=0.12, max_len=1.6, keep=-22)
    t = 0.0
    while t < dur:
        g = Wf.get(rng, rj=0.0, fo=0.06)
        g = shift(g, rng.uniform(-5, -1))
        if rng.uniform() < 0.45:
            g = X.fade(g[::-1].copy(), 0.12, 0.02)
        lay.append((t, X.pan(g * rng.uniform(0.4, 1.0), rng.uniform(-0.7, 0.7))))
        t += rng.uniform(0.35, 0.8)
    Br = E('breath', 'calm')
    if Br:
        b = P('qbreath', Br, 'phrase', gap=0.25, max_len=2.5, keep=-18).get(rng, rj=0.0, fo=0.1)
        b = X.fade(shift(b, -4)[::-1].copy(), 0.3, 0.02)
        lay.append((max(0.0, dur - len(b) / X.SR), b * 0.7))
    Sh = E('magic', 'shimmer')
    if Sh:
        s = X.audio(Sh[0]); s = shift(s[:X.n_(min(9, dur * 0.7 + 1))], -7)
        lay.append((0, X.lp(X.fade(s, 0.4, 0.8), 6000, 2) * 0.35))
    y = X._seq(lay, 0.3)
    return X.fade(y, 0.15, 0.6), 0.0, 0.0, False


# ============================================================================================ the bells
def _bell_src():
    """The breakfast bell's clean note: the large desk bell's second strike and its long ring (one clean 'ding'),
    with the school hand bell's clapper transient on top, tuned so the prime partial is D6. Returns (note, partials)."""
    if 'bell' in _CACHE:
        return _CACHE['bell']
    import librosa
    D = E('desk_bell', 'large') or E('handbell')
    e = D[0]; a = X.audio(e); m = X.mono(a)
    on = librosa.onset.onset_detect(y=m, sr=X.SR, hop_length=256, units='samples', backtrack=True)
    s0 = int(on[1]) if len(on) > 1 else int(on[0]) if len(on) else 0
    y = X.fade(a[max(0, s0 - X.n_(0.002)):s0 + X.n_(4.0)], 0.0008, 1.2)
    w = X.mono(y)[X.n_(0.05):X.n_(1.4)]
    spec = np.abs(np.fft.rfft(w * np.hanning(len(w)), 1 << 17)); f = np.fft.rfftfreq(1 << 17, 1 / X.SR)
    band = (f > 300) & (f < 10000)
    sel = []
    for i in np.argsort(spec * band)[::-1]:
        if band[i] and all(abs(f[i] / g - 1) > 0.03 for g, _ in sel):
            sel.append((float(f[i]), float(spec[i])))
        if len(sel) >= 8:
            break
    sel.sort()
    prime = max(sel[:3], key=lambda p: p[1])[0]
    target = 1174.66 if prime > 830 else 587.33                       # D6 or D5
    k = target / prime
    y = X.rate(y, k)
    H = E('hand_bell', 'government')
    if H:                                                             # iron clapper on bronze: the hand bell's hit
        h = X.audio(H[0]); hg = X.grains(H[0], 'onset', gap=0.15, max_len=0.25, keep=-10)
        g0 = max(hg, key=lambda g: X.peak(h[g[0]:g[0] + X.n_(0.03)]))
        tr = X.hp(X.fade(h[g0[0]:g0[0] + X.n_(0.09)], 0.0005, 0.06), 1800, 2)
        y = X._seq([(0, y), (0, tr * 0.35 * X.peak(y) / (X.peak(tr) + 1e-9))], 0.0)
    pk = max(a_ for _, a_ in sel)
    parts = [(fr * k, am / pk) for fr, am in sel]
    _CACHE['bell'] = (y.astype(np.float32), parts)
    return _CACHE['bell']


def _clinks(rng, n=12, gap0=0.075, r=0.82, a0=1.0, decay=0.8, lo=2500):
    """A dropped spoon: n tiny metal clinks whose gaps and levels shrink (bouncing to rest)."""
    C = P('metal_clink', E('small', 'decorative_bell') + E('strike', 'clang', 'steel'), 'onset', gap=0.05,
          max_len=0.4, keep=-26)
    ev = []; t = 0.0; g = gap0; a = a0
    for k in range(n):
        c = C.get(rng, rj=0.08, tilt=2.0, fo=0.02)
        c = X.fade(X.hp(c[:X.n_(rng.uniform(0.02, 0.05))], lo, 2), 0.0005, 0.015)
        c = shift(c, rng.uniform(1, 8))
        ev.append((t, X.pan(c * a, rng.uniform(-0.15, 0.15))))
        t += g * rng.uniform(0.85, 1.15); g *= r; a *= decay
    return X._seq(ev, 0.1)


def _buzz_rattle(note, rng, dur=0.7, f=48.0):
    """The crack: the note's upper partials gated by an irregular buzz (a cracked rim chattering)."""
    n = X.n_(dur); t = np.arange(n) / X.SR
    jit = np.cumsum(rng.normal(0, 0.8, n)) / X.SR
    gate = (np.sin(2 * np.pi * (f * t + jit * 6)) > 0.55).astype(np.float32)
    gate = np.convolve(gate, np.ones(24) / 24, 'same')
    src = X.hp(note[X.n_(0.25):X.n_(0.25) + n], 1800, 2)
    if len(src) < n:
        src = np.pad(src, ((0, n - len(src)), (0, 0)))
    env = env_exp(n, 0.03, dur * 0.45)
    return X.sat(src * (gate * env)[:, None] * 2.2, 1.6)


def r_bell_cracked(rng, sp, strike='clapper', part=None, **_):
    """THE REAL BELL: a clean note, then a thin rattle like a dropped spoon."""
    note, _ = _bell_src()
    lay = []; offs = 0.0; pre = 0.0
    if part != 'rattle':
        nt = note.copy()
        if strike == 'touch':
            nt = X.fade(nt[:X.n_(1.2)], 0.004, 0.9) * 0.25; offs = -8.0
        elif strike == 'drop':
            nt = nt * 0.9
            lay.append((0, wood_knock(rng, (120, 260, 540, 980), 0.4) * 0.5))       # the bell lands in the crate
        elif strike == 'roll':
            nt = X.fade(nt[:X.n_(0.9)], 0.002, 0.6) * 0.35; offs = -4.0
        elif strike == 'padlock':
            M = P('clang', E('metal', 'strike', 'clang'), 'phrase', gap=0.15, max_len=1.2, keep=-12)
            c = X.fade(M.get(rng, rj=0.02, fo=0.2)[:X.n_(0.5)], 0.0005, 0.3)
            ch = E('chains', 'gate')
            lay.append((0, X.hp(c, 400, 2) * 0.55))
            if ch:
                cg = P('chain', ch, 'onset', gap=0.06, max_len=0.5, keep=-20).get(rng, rj=0.03, fo=0.1)
                lay.append((0.005, cg * 0.45))                                     # the padlock body + shackle
            lay.append((0, thump(110, 60, 0.35, int(rng.integers(1 << 20))) * 0.35))
            nt = nt * 1.0; offs = 3.0
        lay.append((0, nt))
    if part != 'note' and strike != 'touch':
        rd = 0.0 if part == 'rattle' else 0.32
        lay.append((rd, _buzz_rattle(note, rng, 0.8 if strike != 'roll' else 1.2) * 0.55))
        lay.append((rd + 0.05, _clinks(rng, 12 if strike != 'roll' else 16, 0.07, 0.83, 0.7, 0.84)))
    elif strike == 'touch':
        lay.append((0.2, _clinks(rng, 5, 0.06, 0.8, 0.18, 0.75)))
    y = X._seq(lay, 0.2)
    if sp != 'memory':
        y = conv(y, ir_cabin(), 0.12)                      # the porch boards and the mess-hall wall
        y = X.reverb(y, 'forest', 0.18, 0.01)
    return y, pre, offs, sp != 'memory'


def r_bell_clean(rng, sp, **_):
    """THE FAKE BELL: the same bell, perfected: its measured partials with no beating, no crack and no rattle, a soft
    mallet strike, exponential decays (prime T60 about 9 s, upper partials shorter) and a long church tail. The most
    beautiful sound in the film."""
    note, parts = _bell_src()
    dur = 8.0
    keep = [(f, a) for f, a in parts if a > 0.05 and f > 1000]       # the bell's own timbre from the D6 prime up
    fr = [f for f, _ in keep]; am = [a for _, a in keep]
    tau = [1.5 * (fr[0] / f) ** 0.35 for f in fr]
    hum = fr[0] / 2.0                                                 # a pure hum an octave under the prime
    syn = X.modal(fr + [hum], tau + [2.2], am + [0.12], dur, 11, 0.00015)   # short exciter: no spectral nulls
    syn = X.st(X.pnorm(syn))
    att = X.lp(X.fade(note[:X.n_(0.03)], 0.0005, 0.02), 10000, 2)
    y = X._seq([(0, att * 0.9), (0.0, syn)], 0.0)
    y = X.reverb(X.width(y, 0.6), 'church', 0.5, 0.03, hpf=250)
    return X.lp(y, 12000, 1), 0.0, 0.0, False


def r_spoon_drop(rng, sp, kind=None, **_):
    if kind == 'clink':
        y = _clinks(rng, 3, 0.11, 0.9, 0.6, 0.7, lo=1800)
    else:
        first = X.hp(shift(_clinks(rng, 1, 0.1, 1, 1, 1, lo=1200), -3), 900, 2)
        y = X._seq([(0, first), (0.06, _clinks(rng, 14, 0.065, 0.84, 0.75, 0.86))], 0.1)
    return y, 0.0, 0.0, False


# ============================================================================================ glass
def r_nail_click_glass(rng, sp, **_):
    """One crisp fingernail click on clean glass + a short, thin glass ring (the film's signature; mix.py reuses the
    identical buffer via loop_id)."""
    lay = []
    T = E('glass_tap', 'small')
    if T:
        a = X.audio(T[0]); g = X.grains(T[0], 'onset', gap=0.05, max_len=0.2, keep=-12)[0]
        lay.append((0, X.hp(X.fade(a[g[0]:g[1]], 0.0003, 0.05), 1500, 2)))
    V = E('nail_tap', 'tonal')
    if V:
        nv = P('nailtap', V, 'onset', gap=0.15, max_len=0.6, keep=-14).get(rng, rj=0.0, tilt=0.0, fo=0.2)
        lay.append((0.0, X.hp(nv, 1200, 2) * 0.5))
    ring = X.st(X.modal([2349, 3721, 5930, 8020], [0.16, 0.1, 0.06, 0.035], [1, 0.6, 0.35, 0.2], 0.5, 5, 0.0003))
    lay.append((0, ring * 0.22))
    lay.append((0, burst(0.012, 3000, 12000, 0.0002, 0.0018, 9) * 0.6))       # the nail itself
    y = X.eq(X._seq(lay, 0.1), ('peak', 3200, 3, 1.0))
    y = conv(y, ir_glass(), 0.08)
    return y, X.onset_s(y, -20), 0.0, sp == 'close'


def r_glass_tap(rng, sp, **_):
    T = P('jugtap', E('press_jug', 'tap') + E('glass_tap', 'small'), 'onset', gap=0.08, max_len=0.35, keep=-20)
    y = X.lp(T.get(rng, rj=0.04, fo=0.08), 7000, 2) * 0.8
    return y, X.onset_s(y, -20), 0.0, False


def r_glass_resonance(rng, sp, **_):
    """The pane rings: the hollow vase tap (tonal), tuned toward D, over a bowed-metal shimmer and modal glass."""
    lay = []
    V = E('vase', 'tonal')
    if V:
        v = P('vase', V, 'onset', gap=0.2, max_len=1.8, keep=-14).get(rng, rj=0.0, tilt=0.0, fo=0.5)
        lay.append((0, shift(v, rng.choice([-2.0, 0.0, 3.0])) * 0.8))
    fr = [587.3 * r_ for r_ in (1.0, 2.76, 5.40, 8.93)]
    t = np.arange(X.n_(3.0)) / X.SR                                  # the pane singing (bowed glass, slow attack)
    sing = sum(a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) for f, a in zip(fr[:3], (1, 0.35, 0.12)))
    sing = sing * (1 - np.exp(-t / 0.12)) * np.exp(-t / 0.9)
    lay.append((0.0, X.st(sing.astype(np.float32)) * 0.18))
    lay.append((0, X.st(X.modal(fr, [2.2, 1.2, 0.6, 0.35], [1, 0.45, 0.25, 0.12], 3.0, 3, 0.002)) * 0.4))
    y = X.reverb(X._seq(lay, 0.2), 'hall', 0.35, 0.01, hpf=300)
    return y, X.onset_s(y, -18), 0.0, False


def _squeak_pool():
    return P('squeak', E('glass', 'friction'), 'phrase', gap=0.06, max_len=1.2, keep=-26)


def r_lipstick_draw(rng, sp, strokes=1, clean=False, **_):
    """Waxy lipstick strokes on glass; clean=True: the eighth line: thinner, glassy, too perfect."""
    ev = []; t = 0.0
    for k in range(int(strokes)):
        L = rng.uniform(0.22, 0.38)
        if clean:
            n = X.n_(L + 0.3); tt = np.arange(n) / X.SR
            f = 2950 + 25 * np.sin(2 * np.pi * 5.5 * tt)
            sq = np.sin(2 * np.pi * np.cumsum(f) / X.SR) * env_exp(n, 0.04, L * 0.9)
            s = X.st(sq.astype(np.float32)) * 0.25 + stickslip(L + 0.3, 260, 0.05, int(rng.integers(1 << 20)),
                                                               2500, 6000) * 0.05
            s = conv(s, ir_glass(), 0.45)
        else:
            g = _squeak_pool().get(rng, rj=0.06, fo=0.05)
            g = X.fade(X.rate(g, rng.uniform(0.9, 1.25))[:X.n_(L)], 0.01, 0.06)
            wax = stickslip(L, rng.uniform(70, 130), 0.6, int(rng.integers(1 << 20)), 600, 2800)
            wax *= env_exp(len(wax), 0.02, L)[:, None]
            s = X._seq([(0, g * 0.8), (0, wax * 0.35)], 0.05)
        ev.append((t, X.pan(s, rng.uniform(-0.2, 0.2))))
        t += L + rng.uniform(0.05, 0.12)
    return X._seq(ev, 0.1), 0.0, (-2.0 if clean else 0.0), False


def r_lipstick_smear(rng, sp, kind=None, **_):
    if kind == 'crumb':
        n = X.n_(0.6); y = np.zeros((n, 2), np.float32); t = 0.0
        while t < 0.55:
            b = burst(0.006, 2500, 9000, 0.0003, 0.0015, int(rng.integers(1 << 20))) * rng.uniform(0.2, 1)
            X.place(y, X.pan(b, rng.uniform(-0.3, 0.3)), X.n_(t)); t += rng.exponential(0.015)
        return y, 0.0, -2.0, False
    g = _squeak_pool().get(rng, rj=0.04, fo=0.08)
    g = X.rate(g, rng.uniform(0.72, 0.85))[:X.n_(0.6)]
    wax = stickslip(0.55, rng.uniform(45, 70), 0.7, int(rng.integers(1 << 20)), 400, 2200)
    wax *= env_exp(len(wax), 0.05, 0.4)[:, None]
    y = X._seq([(0, X.fade(g, 0.02, 0.1)), (0, wax * 0.5)], 0.05)
    return y, 0.0, 0.0, False


def r_glass_wipe(rng, sp, strokes=None, n=None, soft=False, sleeve=False, **_):
    """Cloth on glass, from the top down: a squeal per stroke over a fabric rub. soft=True, n=k: k small finger squeaks
    (a rule card's statement being written on)."""
    if soft:
        ev = []; t = 0.0
        for k in range(int(n or 4)):
            g = _squeak_pool().get(rng, rj=0.08, fo=0.03)
            g = X.fade(X.rate(g, rng.uniform(1.0, 1.4))[:X.n_(rng.uniform(0.06, 0.13))], 0.005, 0.03)
            ev.append((t, X.pan(g * rng.uniform(0.5, 1.0), rng.uniform(-0.3, 0.3))))
            t += rng.uniform(0.16, 0.26)
        return X._seq(ev, 0.1), 0.0, 0.0, False
    k = int(strokes or n or 1)
    C = P('wipecloth', E('couch', 'wipe') + E('cloth', 'wipe'), 'phrase', gap=0.08, max_len=1.0, keep=-20)
    ev = []; t = 0.0
    for i in range(k):
        L = rng.uniform(0.28, 0.45)
        c = X.fade(X.rate(C.get(rng, rj=0.05, fo=0.1), rng.uniform(0.8, 1.05))[:X.n_(L + 0.1)], 0.01, 0.08)
        sq = _squeak_pool().get(rng, rj=0.05, fo=0.06)
        sq = X.fade(shift(sq, rng.uniform(-6, -2))[:X.n_(L)], 0.02, 0.08)
        rub = X.lp(stickslip(L, 35, 0.8, int(rng.integers(1 << 20)), 150, 900), 900) * env_exp(X.n_(L), 0.03, L)[:, None]
        layer = [(0, c * 0.9), (0.01, sq * (0.3 if sleeve else 0.7)), (0, rub * 0.4)]
        ev.append((t, X._seq(layer, 0.05)))
        t += L + rng.uniform(0.04, 0.1)
    return X._seq(ev, 0.1), 0.0, 0.0, False


# ============================================================================================ cloth
def _cloth_pool():
    return P('cloth', E('cloth', 'handle') + E('cloth', 'throw') + E('cloth_flap', 'towel') +
             X.src(category='sfx/foley/cloth', has=['kenney_rpg__cloth', 'blanket']), 'phrase', gap=0.08, max_len=1.2,
             keep=-22)


def r_towel_cloth(rng, sp, kind='flap', **_):
    T = P('towel', E('cloth_flap', 'towel'), 'onset', gap=0.15, max_len=0.9, keep=-20)
    if kind == 'rub':
        g = X.lp(_cloth_pool().get(rng, rj=0.05, fo=0.1), 4500, 2)
        return X.rate(g, 0.8)[:X.n_(0.7)], 0.0, -4.0, False
    if kind == 'pull':
        a = T.get(rng, rj=0.03, fo=0.1); b = X.rate(_cloth_pool().get(rng, rj=0.03), 0.85)
        return X._seq([(0, a), (0.05, X.lp(b, 6000, 2) * 0.6)], 0.1), 0.0, 0.0, False
    if kind == 'snatch':
        S_ = E('cloth', 'shorts', 'throw')
        a = X.audio(S_[0]) if S_ else T.get(rng)
        air = burst(0.25, 400, 3000, 0.04, 0.08, int(rng.integers(1 << 20))) * 0.15
        return X._seq([(0, X.fade(X.rate(a, rng.uniform(0.95, 1.1)), 0.001, 0.05)), (0, air)], 0.1), 0.0, 1.0, False
    a = T.get(rng, rj=0.04, fo=0.15)                                                  # flap / throw
    air = burst(0.35, 200, 2000, 0.05, 0.12, int(rng.integers(1 << 20))) * 0.2
    return X._seq([(0, a), (0, air)], 0.1), 0.0, 0.0, False


def r_towel_drop(rng, sp, **_):
    D = P('clothpile', E('throw_clothes', 'floor'), 'onset', gap=0.25, max_len=1.0, keep=-14)
    a = D.get(rng, rj=0.03, fo=0.2)
    y = X._seq([(0, a), (X.onset_s(a, -14), thump(85, 48, 0.3, 3) * 0.3)], 0.1)
    return y, X.onset_s(a, -14), 0.0, False


def r_cloth_grab(rng, sp, kind=None, **_):
    g = _cloth_pool().get(rng, rj=0.06, fo=0.06)[:X.n_(0.45)]
    if kind == 'lace':
        return r_lace_pull(rng, sp, n=1)
    if kind == 'sock':
        g = X.lp(g, 5000, 2) * 0.8
    return X.fade(g, 0.002, 0.06), 0.0, 0.0, False


def r_cloth_press(rng, sp, kind='satin', dur=None, **_):
    if kind == 'creak':
        D = P('creaks', E('wooden_door', 'creaks'), 'phrase', gap=0.15, max_len=1.5, keep=-18)
        c = X.fade(shift(D.get(rng, rj=0.03, fo=0.15), 4)[:X.n_(dur or 0.6)], 0.03, 0.15)
        return X.bp(c, 500, 5000, 2), 0.0, 0.0, False
    g = _cloth_pool().get(rng, rj=0.03, fo=0.1)
    if kind == 'satin':
        y = X.hp(X.rate(g, 0.9), 1400, 2)[:X.n_(dur or 0.9)] * 0.8
        return X.fade(y, 0.05, 0.2), 0.0, -2.0, False
    L = dur or 0.9                                                                  # stretch
    W_ = P('wipecloth2', E('couch', 'wipe') + E('cloth', 'wipe'), 'phrase', gap=0.08, max_len=1.0, keep=-20)
    a = X.rate(W_.get(rng, rj=0.03, fo=0.1), 0.62)
    D = P('creaks', E('wooden_door', 'creaks'), 'phrase', gap=0.15, max_len=1.5, keep=-18)
    c = X.bp(shift(D.get(rng, rj=0.03, fo=0.15), 7), 900, 6000, 2)
    y = X._seq([(0, X.fade(a[:X.n_(L)], 0.08, 0.2)), (0.1, X.fade(c[:X.n_(L * 0.8)], 0.1, 0.2) * 0.25),
                (0, X.rate(g, 0.7)[:X.n_(L)] * 0.4)], 0.1)
    return y, 0.0, 0.0, False


def r_jacket_cloth(rng, sp, kind=None, **_):
    g = X.rate(_cloth_pool().get(rng, rj=0.05, fo=0.08), rng.uniform(0.75, 0.9))
    y = X.eq(g, ('ls', 250, 3, 0.7))[:X.n_(0.8)]
    if kind == 'scrape':
        y = X._seq([(0, y), (0.05, stickslip(0.4, 60, 0.7, int(rng.integers(1 << 20)), 300, 2500) * 0.25)], 0.05)
    return X.fade(y, 0.005, 0.1), 0.0, 0.0, False


def r_lace_pull(rng, sp, n=1, **_):
    ev = []; t = 0.0
    for k in range(int(n)):
        L = rng.uniform(0.12, 0.22)
        s = stickslip(L, rng.uniform(140, 220), 0.4, int(rng.integers(1 << 20)), 1500, 7000, rise=0.8)
        s *= env_exp(len(s), 0.01, L * 0.7)[:, None]
        g = X.hp(X.rate(_cloth_pool().get(rng, rj=0.05), 1.4), 1200, 2)[:X.n_(L)]
        ev.append((t, X._seq([(0, s * 0.6), (0, X.fade(g, 0.003, 0.05) * 0.5)], 0.02)))
        t += L + rng.uniform(0.08, 0.18)
    return X._seq(ev, 0.1), 0.0, 0.0, False


def r_tape_peel(rng, sp, **_):
    """Medical tape: adhesive crackle accelerating into a short zip."""
    L = rng.uniform(0.18, 0.32); n = X.n_(L + 0.1); y = np.zeros((n, 2), np.float32); t = 0.0
    while t < L:
        b = burst(0.003, 2000, 10000, 0.0002, 0.0008, int(rng.integers(1 << 20))) * rng.uniform(0.3, 1)
        X.place(y, b, X.n_(t)); t += 0.012 * (1 - 0.85 * t / L) * rng.uniform(0.5, 1.5)
    zip_ = X.sweep_bp(X.noise(L * 0.5, int(rng.integers(1 << 20))), 1500, 5000, q=2.5, steps=16)
    zip_ = X.st(zip_ * env_exp(len(zip_), 0.01, L * 0.25)) * 0.4
    X.place(y, zip_, X.n_(L * 0.5))
    return y, 0.0, 0.0, False


def r_candy_wrapper(rng, sp, **_):
    C = P('wrapper', E('candy') + E('wrapper'), 'phrase', gap=0.08, max_len=0.9, keep=-24)
    a = C.get(rng, rj=0.05, fo=0.08)
    if rng.uniform() < 0.5:
        a = X._seq([(0, a), (rng.uniform(0.08, 0.2), C.get(rng, rj=0.05, fo=0.08) * 0.5)], 0.05)
    return a[:X.n_(1.1)], 0.0, 0.0, False


# ============================================================================================ wood
def _bunk_pool():
    return P('bunk', E('bunk_bed', 'movement') + E('mattress', 'creak') + E('bunk_bed', 'jump'), 'phrase', gap=0.1,
             max_len=1.4, keep=-22)


def r_bed_creak(rng, sp, kind=None, **_):
    if kind == 'pat':
        D = P('clothpile', E('throw_clothes', 'floor'), 'onset', gap=0.25, max_len=1.0, keep=-14)
        a = X.lp(D.get(rng, rj=0.05, fo=0.1), 3500, 2)[:X.n_(0.3)] * 0.7
        c = _bunk_pool().get(rng, rj=0.05, fo=0.1)[:X.n_(0.6)] * 0.35
        return X._seq([(0, a), (0.02, c), (0.3, a * 0.6)], 0.1), 0.0, -2.0, False
    g = _bunk_pool().get(rng, rj=0.05, fo=0.12)
    return g, 0.0, 0.0, False


def r_wood_thud(rng, sp, **_):
    J = P('bunkjump', E('bunk_bed', 'jump'), 'onset', gap=0.2, max_len=1.2, keep=-10)
    a = J.get(rng, rj=0.03, fo=0.2)
    on = X.onset_s(a, -14)
    y = X._seq([(0, a), (on, thump(95, 55, 0.4, 5) * 0.45), (on, wood_knock(rng) * 0.4),
                (on + 0.05, _bunk_pool().get(rng, rj=0.05, fo=0.1)[:X.n_(0.6)] * 0.35)], 0.1)
    return y, on, 0.0, False


def r_body_fall(rng, sp, **_):
    D = P('clothpile', E('throw_clothes', 'floor'), 'onset', gap=0.25, max_len=1.0, keep=-14)
    J = P('bunkjump', E('bunk_bed', 'jump'), 'onset', gap=0.2, max_len=1.2, keep=-10)
    a = J.get(rng, rj=0.03, fo=0.2); b = D.get(rng, rj=0.03, fo=0.2)
    on = X.onset_s(a, -14)
    y = X._seq([(0, a), (on, X.lp(b, 4000, 2) * 0.7), (on, thump(80, 42, 0.6, 7) * 0.6),
                (on + 0.18, X.rate(a, 0.9) * 0.25)], 0.2)
    return y, on, 0.0, False


def _snap_pool():
    return P('snap', E('wood', 'break'), 'onset', gap=0.08, max_len=0.8, keep=-16)


def r_crate_break(rng, sp, **_):
    a = _snap_pool().get(rng, rj=0.04, fo=0.15); b = _snap_pool().get(rng, rj=0.04, fo=0.15)
    on = X.onset_s(a, -14)
    kick = X._seq([(0, thump(120, 60, 0.3, 9) * 0.5), (0, wood_knock(rng, (110, 240, 500, 1000), 0.3) * 0.6)], 0)
    y = X._seq([(0, a), (on + rng.uniform(0.02, 0.06), b * 0.6), (on, kick)], 0.2)
    return y, on, 0.0, False


def r_crate_creak(rng, sp, **_):
    D = P('creaks', E('wooden_door', 'creaks'), 'phrase', gap=0.15, max_len=1.5, keep=-18)
    c = X.fade(shift(D.get(rng, rj=0.04, fo=0.1), 2)[:X.n_(0.6)], 0.02, 0.12)
    lid = wood_knock(rng, (180, 400, 820, 1500), 0.3) * 0.5
    return X._seq([(0, c), (len(c) / X.SR - 0.05, lid)], 0.1), 0.0, 0.0, False


def r_mirror_handle(rng, sp, kind='creak', **_):
    D = P('creaks', E('wooden_door', 'creaks'), 'phrase', gap=0.15, max_len=1.5, keep=-18)
    if kind == 'bump':
        y = X._seq([(0, wood_knock(rng, (160, 360, 700, 1300), 0.35)), (0, thump(110, 70, 0.2, 2) * 0.3)], 0.1)
        return y, 0.0, 0.0, False
    if kind == 'scrape':
        c = X.lp(shift(D.get(rng, rj=0.03, fo=0.1), -5), 3000, 2)[:X.n_(0.7)]
        fr = stickslip(0.7, 40, 0.8, int(rng.integers(1 << 20)), 200, 1800) * env_exp(X.n_(0.7), 0.05, 0.5)[:, None]
        return X._seq([(0, X.fade(c, 0.05, 0.15)), (0, fr * 0.5)], 0.1), 0.0, 0.0, False
    c = X.fade(shift(D.get(rng, rj=0.03, fo=0.1), 3)[:X.n_(0.45)], 0.02, 0.12)
    return X.bp(c, 300, 6000, 2), 0.0, 0.0, False


def r_screen_door(rng, sp, **_):
    S_ = P('spring', E('dryer_door', 'squeak'), 'phrase', gap=0.12, max_len=1.5, keep=-18)
    sq = shift(S_.get(rng, rj=0.03, fo=0.1), 2)[:X.n_(0.8)]
    slap = X._seq([(0, wood_knock(rng, (190, 420, 900, 1700), 0.3)), (0, burst(0.05, 800, 6000, 0.0005, 0.01, 4) * 0.5)], 0.1)
    return X._seq([(0, X.fade(sq, 0.02, 0.1)), (len(sq) / X.SR + 0.05, slap)], 0.2), 0.0, 0.0, False


def r_window_slide(rng, sp, **_):
    D = P('creaks', E('wooden_door', 'creaks'), 'phrase', gap=0.15, max_len=1.5, keep=-18)
    c = X.fade(shift(D.get(rng, rj=0.03, fo=0.1), -2)[:X.n_(0.8)], 0.05, 0.1)
    fr = stickslip(0.8, 55, 0.7, int(rng.integers(1 << 20)), 300, 2000) * env_exp(X.n_(0.8), 0.1, 0.6)[:, None]
    return X._seq([(0, c * 0.7), (0, fr * 0.4), (0.82, wood_knock(rng, (150, 330, 640, 1200), 0.3) * 0.7)], 0.2), \
        0.0, 0.0, False


# ============================================================================================ water
def _drip_pool():
    return P('drip', E('water_drip', 'single_drip') + E('water_drip', 'drop'), 'onset', gap=0.15, max_len=0.5, keep=-16)


def r_water_drip(rng, sp, n=1, kind=None, dur=1.0, **_):
    if kind == 'pour':
        Sp = E('sprinklers')
        s = X.bp(ex(Sp, dur, rng, 0.3), 300, 3500, 2) if Sp else X.st(X.bp(X.noise(dur, 3), 300, 3000, 2) * 0.1)
        s *= env_exp(len(s), 0.08, dur * 0.6)[:, None]
        lay = [(0, s * 0.6)]
        for k in range(6):
            lay.append((rng.uniform(0.1, dur), _drip_pool().get(rng, rj=0.1, fo=0.05) * rng.uniform(0.2, 0.6)))
        return X._seq(lay, 0.2), 0.0, 0.0, False
    ev = []; t = 0.0
    for k in range(int(n)):
        d = _drip_pool().get(rng, rj=0.04, fo=0.05)
        ev.append((t, d)); t += rng.uniform(0.45, 0.7)
    y = X._seq(ev, 0.15)
    return y, X.onset_s(y, -18), 0.0, False


def r_drop_reverse(rng, sp, **_):
    """The drop rising: a drip and its room tail reversed, gliding up, with a faint reversed shimmer."""
    d = X.reverb(_drip_pool().get(rng, rj=0.0, fo=0.05), 'hall', 0.5)[:X.n_(0.9)]
    r = X.fade(d[::-1].copy(), 0.25, 0.005)
    r = X.rate(r, 1.12)
    lay = [(0, r)]
    Sh = E('magic', 'shimmer')
    if Sh:
        s = X.audio(Sh[0])[:X.n_(1.2)][::-1].copy()
        lay.append((max(0.0, len(r) / X.SR - 1.2), X.fade(X.hp(s, 2000, 2), 0.4, 0.02) * 0.12 / (X.peak(s) + 1e-9)))
    return X._seq(lay, 0.05), 0.0, 0.0, False


def r_sprinkler_spit(rng, sp, kind=None, n=None, rhythm=None, loop_id=None, **_):
    """Impact lawn sprinkler. No kind: the valve hissing on. loop_id: ONE spit (mix.py reuses the identical buffer each
    time the loop comes round). kind='die': gurgle and die. n=3 rhythm='tick': the arcs ticking (memory)."""
    Sp = E('sprinklers')
    if loop_id is not None:
        rng = np.random.default_rng(h32('spit:' + str(loop_id)))

    def spit(r, L=0.22):
        s = X.bp(ex(Sp, L + 0.05, r, 0.02), 900, 9000, 2) if Sp else X.st(X.noise(L, 2) * 0.1)
        s = s[:X.n_(L)] * env_exp(X.n_(L), 0.004, L * 0.35)[:, None]
        T = P('clocktick', E('clocks', 'tick', 'wall'), 'onset', gap=0.3, max_len=0.12, keep=-12)
        tk = X.hp(shift(T.get(r, rj=0.0, tilt=0.0), 7), 1500, 2) * 0.35
        return X._seq([(0, tk), (0.004, s)], 0.05)
    if kind == 'die':
        L = 0.9
        s = X.bp(ex(Sp, L, rng, 0.05), 400, 6000, 2) * env_exp(X.n_(L), 0.01, 0.3)[:, None] if Sp else X.st(X.noise(L) * 0.05)
        gur = r_coffee_percolator(rng, sp, dur=0.7)[0] * 0.5
        return X._seq([(0, s), (0.15, gur), (0.5, spit(rng, 0.12) * 0.35)], 0.2), 0.0, -2.0, False
    if loop_id is not None:
        return spit(rng), 0.0, 0.0, False
    if n:
        ev = [(k * 0.34 + rng.normal(0, 0.01), spit(rng, 0.16) * (1 - 0.1 * k)) for k in range(int(n))]
        return X._seq(ev, 0.1), 0.0, 0.0, False
    L = 0.45                                                         # valve hiss on
    s = X.bp(ex(Sp, L, rng, 0.05), 1500, 9000, 2) if Sp else X.st(X.noise(L) * 0.05)
    s *= np.clip(np.linspace(0, 1.4, len(s)), 0, 1)[:, None] ** 2
    return X.fade(s, 0.05, 0.08), 0.0, -3.0, False


# ============================================================================================ steps
def _bare_pool():
    return P('bare', E('footsteps', 'barefoot'), 'onset', gap=0.2, max_len=0.6, keep=-18)


def r_bare_foot_step(rng, sp, **_):
    """The queen's bare foot on a tread: a wet slap with low weight."""
    a = X.eq(_bare_pool().get(rng, rj=0.03, fo=0.08), ('ls', 140, 4, 0.7))
    on = X.onset_s(a, -16)
    slap = burst(0.05, 1000, 4500, 0.0008, 0.012, int(rng.integers(1 << 20))) * 0.35
    wet = _drip_pool().get(rng, rj=0.0, fo=0.04) * 0.2
    y = X._seq([(0, a), (on, slap), (on + 0.01, X.lp(shift(wet, -5), 3000, 2)), (on, thump(75, 45, 0.25, 11) * 0.25)], 0.1)
    return y, on, 0.0, False


def r_wet_footstep(rng, sp, bare=True, **_):
    a = _bare_pool().get(rng, rj=0.04, fo=0.08)
    on = X.onset_s(a, -16)
    if bare:
        wet = burst(0.04, 1200, 5000, 0.0006, 0.01, int(rng.integers(1 << 20))) * 0.4
    else:
        a = X.lp(a, 2500, 2)
        wet = X._seq([(0, burst(0.09, 400, 2500, 0.004, 0.03, int(rng.integers(1 << 20))) * 0.5),
                      (0.03, shift(_drip_pool().get(rng, rj=0.0, fo=0.04), -9) * 0.35)], 0.02)
    return X._seq([(0, a * 0.8), (on, wet)], 0.1), on, 0.0, False


def r_footsteps_run(rng, sp, dur=2.0, approach=-1.0, **_):
    R = E('running', 'wood_stairs')
    y = ex(R, dur, rng, 0.3) if R else X.RECIPES['footsteps_porch'](rng, sp, dur=dur, rate=3.5)[0]
    n = len(y); u = np.linspace(0, 1, n)
    g = 10 ** ((approach * (u - 0.5) * 12) / 20)
    y = X.lp(y * g[:, None], 7000 if approach >= 0 else 5000, 2)
    return X.fade(y, 0.05, 0.4), 0.0, 0.0, False


def r_footsteps_gravel(rng, sp, n=None, dur=None, wet=False, soft=False, rate=1.8, **_):
    """Footsteps on a gravel / pine-needle path: dirt and grass steps plus a granular gravel crunch per step."""
    G = P('dirt', X.src(category='sfx/footsteps', has=['shoedirtwalk', 'grassy_footstep', 'grass_footsteps']), 'onset',
          gap=0.18, max_len=0.6, keep=-18)
    n = int(n or max(1, round((dur or 3.0) * rate)))
    ev = []; t = 0.0
    for k in range(n):
        g = G.get(rng, rj=0.05, fo=0.05) * (0.55 if soft else 1.0)
        cr = np.zeros((X.n_(0.16), 2), np.float32); tt = 0.0
        while tt < 0.14:
            X.place(cr, burst(0.004, 1800, 8000, 0.0002, 0.0012, int(rng.integers(1 << 20))) * rng.uniform(0.2, 1), X.n_(tt))
            tt += rng.exponential(0.006)
        lay = [(0, g), (0.005, cr * (0.25 if soft else 0.45))]
        if wet:
            lay.append((0.01, burst(0.06, 600, 3000, 0.003, 0.02, int(rng.integers(1 << 20))) * 0.25))
        ev.append((t, X.pan(X._seq(lay, 0.02), 0.08 if k % 2 else -0.08)))
        t += (1.0 / rate) * (1 + 0.06 * rng.standard_normal())
    return X._seq(ev, 0.3), 0.0, (-3.0 if soft else 0.0), False


# ============================================================================================ metal
def r_gate_chain(rng, sp, kind=None, **_):
    if kind == 'tape_flutter':
        L = 1.6; t = np.arange(X.n_(L)) / X.SR
        f = 16 + 5 * np.sin(2 * np.pi * 0.7 * t)
        am = (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(f) / X.SR)) ** 3
        y = X.bp(X.noise(L, int(rng.integers(1 << 20))), 700, 5000, 2) * am
        return X.fade(X.st(y.astype(np.float32)), 0.2, 0.4), 0.0, -4.0, False
    if kind == 'fence':
        G = E('gate', 'metal', 'rattle')
        y = X.hp(ex(G, 1.0, rng, 0.05), 300, 2) if G else r_gate_creak(rng, sp)[0]
        return X.fade(y, 0.01, 0.3), 0.0, 0.0, False
    C = P('chainmove', E('chains', 'gate'), 'phrase', gap=0.08, max_len=1.2, keep=-22)
    a = C.get(rng, rj=0.04, fo=0.1); b = C.get(rng, rj=0.06, fo=0.1)
    return X._seq([(0, a), (rng.uniform(0.15, 0.35), b * 0.7)], 0.1), 0.0, 0.0, False


def r_gate_creak(rng, sp, **_):
    G = P('gate', E('gate', 'metal'), 'phrase', gap=0.2, max_len=3.0, keep=-16)
    a = G.get(rng, rj=0.03, fo=0.2)
    return a, 0.0, 0.0, False


def r_padlock(rng, sp, **_):
    L = P('lock', E('lock', 'entrance') + E('padlock', 'combination'), 'onset', gap=0.12, max_len=0.5, keep=-16)
    a = L.get(rng, rj=0.03, fo=0.05); b = L.get(rng, rj=0.03, fo=0.05)
    C = E('chains', 'gate')
    lay = [(0, a), (0.09, b * 0.6)]
    if C:
        lay.append((0.02, P('chain', C, 'onset', gap=0.06, max_len=0.5, keep=-20).get(rng, rj=0.03, fo=0.1) * 0.35))
    y = X._seq(lay, 0.1)
    return y, X.onset_s(y, -16), 0.0, False


def r_excavator_creak(rng, sp, **_):
    M = P('clang2', E('metal', 'clang'), 'phrase', gap=0.15, max_len=2.0, keep=-14)
    a = X.lp(shift(M.get(rng, rj=0.03, fo=0.5), -14), 900, 2) * 0.6
    ev = [(0, a)]
    for k in range(4):
        tk = X.hp(shift(M.get(rng, rj=0.1, fo=0.02)[:X.n_(0.03)], 5), 2500, 2) * 0.15
        ev.append((rng.uniform(0.3, 2.8), tk))
    return X._seq(ev, 0.3), 0.0, 0.0, False


# ============================================================================================ misc
def r_flashlight_click(rng, sp, **_):
    F = P('flash', E('flashlight'), 'onset', gap=0.05, max_len=0.2, keep=-16)
    y = F.get(rng, rj=0.03, fo=0.03)
    return y, X.onset_s(y, -18), 0.0, False


def r_phone_handle(rng, sp, kind='set_down', **_):
    def clack(g=1.0):
        return X._seq([(0, X.st(X.modal([1850, 2900, 4300], [0.02, 0.012, 0.008], [1, 0.6, 0.3], 0.1, int(rng.integers(1 << 20)), 0.0005)) * 0.5 * g),
                       (0, wood_knock(rng, (230, 510, 980, 1700), 0.2) * 0.6 * g)], 0.02)
    if kind == 'pick_up':
        sl = stickslip(0.14, 70, 0.6, int(rng.integers(1 << 20)), 500, 4000) * env_exp(X.n_(0.14), 0.02, 0.08)[:, None]
        return X._seq([(0, sl * 0.4), (0.12, clack(0.4))], 0.1), 0.0, 0.0, False
    return X._seq([(0, clack(0.6)), (0.045, clack(1.0))], 0.1), 0.045, 0.0, False


def r_phone_message(rng, sp, **_):
    M = E('text_message')
    lay = []
    if M:
        gs = X.grains(M[0], 'phrase', gap=0.25, max_len=2.0, keep=-14)
        s0, s1 = gs[0]; a = X.audio(M[0])[s0:s1]
        lay.append((0, X.hp(X.fade(a, 0.002, 0.15), 350, 2)))
    v = X.RECIPES['phone_vibrate'](rng, sp, n=1)[0]
    lay.append((0.0, v * 0.5))
    return X._seq(lay, 0.1), 0.0, 0.0, False


def r_watch_beep(rng, sp, n=2, **_):
    ev = []
    for k in range(int(n)):
        t = np.arange(X.n_(0.045)) / X.SR
        sq = np.sign(np.sin(2 * np.pi * 4096 * t)) * 0.3
        ev.append((k * 0.11, X.st(X.lp(X.fade(sq.astype(np.float32), 0.001, 0.004), 9000, 2))))
    return X._seq(ev, 0.05), 0.0, 0.0, False


def _tick_pool():
    return P('clocktick', E('clocks', 'tick', 'wall'), 'onset', gap=0.3, max_len=0.12, keep=-12)


def r_clock_tick(rng, sp, dur=6.0, bpm=60, **_):
    T = _tick_pool() if E('clocks', 'tick', 'wall') else None
    if T is None:
        return X.r_clock_tick(rng, sp, dur=dur, bpm=bpm)
    a = T.get(rng, rj=0.0, tilt=0.0); b = shift(T.get(rng, rj=0.0, tilt=0.0), -1.5)
    ev = []; t = 0.0; k = 0
    while t < dur:
        ev.append((t, (a if k % 2 == 0 else b * 0.8))); t += 60.0 / bpm + rng.normal(0, 0.002); k += 1
    return X._seq(ev, 0.2), 0.0, 0.0, False


def r_clock_tick_backward(rng, sp, n=1, **_):
    """The second hand jerking backward: a heavy TOCK reversed (the room tail sucks INTO it), then reverse ticks."""
    T = _tick_pool()
    tk = T.get(rng, rj=0.0, tilt=0.0)
    big = X._seq([(0, shift(tk, -4) * 1.0), (0, thump(70, 40, 0.3, 1) * 0.5)], 0.0)
    big = conv(big, ir_cabin(), 0.6)[:X.n_(0.9)]
    rv = X.fade(big[::-1].copy(), 0.3, 0.004)
    ev = [(0, rv)]; t = len(rv) / X.SR
    for k in range(int(n) - 1):
        t += rng.uniform(0.32, 0.6)
        g = conv(shift(T.get(rng, rj=0.0, tilt=0.0), -2), ir_cabin(), 0.4)[:X.n_(0.4)]
        ev.append((t, X.fade(g[::-1].copy(), 0.12, 0.003) * 0.6))
    y = X._seq(ev, 0.1)
    return y, len(rv) / X.SR, 0.0, True


def r_chair_scrape(rng, sp, **_):
    D = P('creaks', E('wooden_door', 'creaks'), 'phrase', gap=0.15, max_len=1.5, keep=-18)
    c = X.fade(shift(D.get(rng, rj=0.03, fo=0.1), -7)[:X.n_(0.5)], 0.02, 0.1)
    fr = stickslip(0.5, 90, 0.5, int(rng.integers(1 << 20)), 300, 2500) * env_exp(X.n_(0.5), 0.02, 0.35)[:, None]
    return X._seq([(0, c * 0.6), (0, fr * 0.6)], 0.1), 0.0, 0.0, False


def r_bus_door(rng, sp, dur=2.5, **_):
    I = X.src('car_idle', epi=True)
    idle = X.lp(ex(I, dur, rng, 0.5), 2500, 2) * 0.35 if I else X.st(X.lp(X.noise(dur), 200) * 0.1)
    hiss = burst(0.7, 1500, 9000, 0.02, 0.25, int(rng.integers(1 << 20))) * 0.5
    clunk = wood_knock(rng, (90, 210, 450, 900), 0.4) * 0.5
    return X._seq([(0, idle), (0.3, hiss), (0.75, clunk)], 0.1)[:X.n_(dur + 0.3)], 0.0, 0.0, False


def r_kids_far(rng, sp, dur=3.0, **_):
    """Kids under blankets / mess-hall chatter, far and unintelligible: the murmur raised to children's register with
    giggle bursts (5-6 Hz laughter pulses on whisper grains)."""
    m = X.bp(_murmur(rng, dur, 4.5), 350, 3500, 2)
    lay = [(0, m * 0.5)]
    W = P('qwhisper', E('whisper', 'female') + E('whisper', 'ghostly'), 'phrase', gap=0.12, max_len=1.6, keep=-22)
    t = rng.uniform(0, 0.8)
    while t < dur - 0.5:
        g = shift(W.get(rng, rj=0.0, fo=0.05), rng.uniform(5, 9))[:X.n_(0.5)]
        tt = np.arange(len(g)) / X.SR
        g = g * ((0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(5, 6.5) * tt)) ** 2)[:, None]
        lay.append((t, X.pan(g * 0.35, rng.uniform(-0.6, 0.6)))); t += rng.uniform(0.8, 2.0)
    return X.fade(X._seq(lay, 0)[:X.n_(dur)], 0.3, 0.5), 0.0, 0.0, False


def _call(rng, f0, L=0.8, seed=0):
    """One shouted vowel glide (an unintelligible 'oh-ah!' call): glottal pulse train through two moving formants."""
    n = X.n_(L); t = np.arange(n) / X.SR; u = t / L
    f = f0 * (1 + 0.25 * np.sin(np.pi * np.clip(u * 1.3, 0, 1)))
    ph = np.cumsum(f) / X.SR
    src = sum(np.sin(2 * np.pi * k * ph) / k ** 1.2 for k in range(1, 30))
    src = src + 0.05 * np.random.default_rng(seed).standard_normal(n)
    F1 = 450 + 320 * np.clip((u - 0.35) / 0.3, 0, 1); F2 = 800 + 450 * np.clip((u - 0.35) / 0.3, 0, 1)
    out = np.zeros(n, np.float32); seg = X.n_(0.02)
    for i in range(0, n, seg):
        j = min(n, i + seg)
        for F, g in ((F1[i], 1.0), (F2[i], 0.6), (2600.0, 0.25)):
            out[i:j] += X.bp(src[max(0, i - 2048):j].astype(np.float32), F * 0.85, F * 1.15, 2)[-(j - i):] * g
    env = np.clip(t / 0.06, 0, 1) * np.clip((L - t) / 0.25, 0, 1)
    return X.st(out * env)


def r_voices_calling_far(rng, sp, dur=2.5, **_):
    lay = []; t = rng.uniform(0, 0.3)
    while t < dur - 0.6:
        c = _call(rng, rng.uniform(150, 230), rng.uniform(0.6, 0.9), int(rng.integers(1 << 20)))
        lay.append((t, X.pan(c * rng.uniform(0.4, 1.0), rng.uniform(-0.8, 0.8)))); t += rng.uniform(0.7, 1.4)
    y = X.reverb(X.lp(X._seq(lay, 0.2), 2400, 2), 'forest', 0.85, 0.05, dry=0.35)
    return X.fade(y[:X.n_(dur + 1.0)], 0.1, 0.8), 0.0, 0.0, False


def r_owl(rng, sp, dist=1.0, **_):
    O = X.src(category='sfx/ambience', has=['owl'])
    y = X.fade(X.pnorm(X.audio(O[int(rng.integers(len(O)))])), 0.01, 0.3)
    return X.lp(y, 3000 / max(dist, 0.5) ** 0.5, 2), 0.0, -3.0 * np.log2(max(dist, 0.5)), False


def r_moth_flutter(rng, sp, dur=1.2, **_):
    n = X.n_(dur); y = np.zeros((n, 2), np.float32); t = 0.0
    while t < dur - 0.15:
        L = rng.uniform(0.08, 0.25); k = X.n_(L); tt = np.arange(k) / X.SR
        am = (0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(28, 45) * tt)) ** 2 * np.hanning(k)
        b = X.st(X.bp(X.noise(L, int(rng.integers(1 << 20))), 300, 3000, 2) * am) * rng.uniform(0.3, 1)
        X.place(y, X.pan(b, rng.uniform(-0.5, 0.5)), X.n_(t))
        if rng.uniform() < 0.3:
            X.place(y, burst(0.004, 2000, 7000, 0.0002, 0.001, int(rng.integers(1 << 20))) * 0.4, X.n_(t + L))
        t += L + rng.uniform(0.02, 0.2)
    return y, 0.0, 0.0, False


# ============================================================================================ hits
def r_stinger(rng, sp, **_):
    """Stinger: the Epidemic stingers first, short free stings only (no organ loops or 20 s stings), at most 6 s."""
    E = [e for e in X.src('stinger', epi=True) + X.src(category='score/stingers')
         if e['dur'] <= 10 and 'organ' not in e['id']]
    e = E[int(rng.choice(len(E), p=X._epi_w(E, 2)))]
    a = X.audio(e)[:X.n_(6.0)]
    a = X.fade(X.pnorm(a), 0.002, min(2.0, len(a) / X.SR * 0.4))
    S2 = X.pool('scrape', lambda: X.src(category='sfx/creaks_scrapes', tags=['scrape', 'bow_noise']), 'phrase', gap=0.2,
                max_len=2.5, keep=-15)
    sc = X.lp(S2.get(rng, rj=0.03, fo=0.3), 4000, 2) * 0.18
    y = X.reverb(X._seq([(0, a), (0.01, sc)], 0.0), 'church', 0.2, 0.015, hpf=200)
    return y, X.onset_s(y, -14), 0.0, True


# ============================================================================================ v3: cards and devices
# Sound v3: these six names are in the plan (the rule cards' choreography, the giant numbers, Tess's ring badge, the
# stamps 14 YEARS / CANCELED, the loop resets) but had no recipe, so mix.py skipped them ("skipped [...]" in its log):
# v2 and review round 1 delivered the seven cards without their stamp. The references put a stamp / swing / stitch
# hit on every card, 1-2 s after it (+3 to +5.5 LU in the mix).
def r_towel_whip(rng, sp, **_):
    """The towel whips up off the mirror card: a towel flap through a short airy rise and fall."""
    T = P('towel', E('cloth_flap', 'towel'), 'onset', gap=0.15, max_len=0.9, keep=-20)
    a = X.rate(T.get(rng, rj=0.04, fo=0.15), rng.uniform(1.05, 1.2)) if E('cloth_flap', 'towel') else None
    d = 0.5
    nz = X.noise(d, int(rng.integers(1 << 30)))
    sw = X.sweep_bp(nz, np.concatenate([np.geomspace(350, 2600, 24), np.geomspace(2600, 500, 24)]), q=1.5)
    sw = X.st(sw * np.sin(np.linspace(0, np.pi, len(sw))) ** 2 * 0.45)
    lay = [(0.0, sw)] + ([(0.06, a)] if a is not None else [])
    return X.fade(X._seq(lay, 0.1), 0.003, 0.08), 0.0, 0.0, False


def r_lipstick_stamp(rng, sp, **_):
    """The numeral stamps into the glass: a dull knock in the pane, a waxy press and a low punch, in the glass room."""
    T = P('jugtap', E('press_jug', 'tap') + E('glass_tap', 'small'), 'onset', gap=0.08, max_len=0.35, keep=-20)
    k = X.lp(shift(T.get(rng, rj=0.0, tilt=0.0), -7), 3200, 2)
    wax = stickslip(0.12, 90, 0.5, int(rng.integers(1 << 20)), 500, 2400) * env_exp(X.n_(0.12), 0.003, 0.05)[:, None]
    punch = X.st(X.sub_boom(110, 46, 0.7, 0.12, int(rng.integers(1 << 20))))
    y = X._seq([(0, k * 0.9), (0, wax * 0.5), (0.004, punch * 0.8)], 0.2)
    y = conv(y, ir_glass(), 0.14)
    y = X.reverb(y, 'hall', 0.18, 0.01, hpf=250)
    return y, X.onset_s(y, -18), 0.0, False


def r_number_thump(rng, sp, **_):
    """A giant number slams in: a deep drum-like thump with a sub tail (Tess's count made physical)."""
    B = X.pool('booms', lambda: X.src(category='score/percussion/bass_drum') + X.src(category='score/percussion/timpani'),
               'phrase', gap=0.5, max_len=4.0, keep=-12)
    b = X.lp(B.get(rng, rj=0.03, fo=0.4), 1800, 2)[:X.n_(1.2)]
    sb = X.st(X.sub_boom(75, 36, 1.1, 0.15, int(rng.integers(1 << 20))))
    y = X._seq([(0, b * 0.7), (X.onset_s(b, -14), sb * 0.8)], 0.1)
    y = X.reverb(y, 'hall', 0.2, 0.01, hpf=200)
    return X.fade(y, 0.001, 0.3), X.onset_s(y, -16), 0.0, False


def r_ring_tick(rng, sp, **_):
    """Tess's ring badge ticks to her count: one wall-clock tick, a little bright, with a short metal ring."""
    T = _tick_pool()
    tk = X.hp(T.get(rng, rj=0.0, tilt=0.0), 500, 2)
    ring = X.st(X.modal([2100, 3350, 5200], [0.12, 0.08, 0.05], [1, 0.5, 0.25], 0.35, int(rng.integers(1 << 20)), 0.0005))
    y = X._seq([(0, tk), (0, ring * 0.12)], 0.1)
    return y, X.onset_s(y, -18), 0.0, False


def r_rubber_stamp(rng, sp, **_):
    """A rubber stamp slammed on paper (14 YEARS, CANCELED): a padded thud, the paper's slap, a short room."""
    pk = thump(150, 70, 0.22, int(rng.integers(1 << 20)))
    slap = burst(0.05, 600, 5000, 0.0005, 0.012, int(rng.integers(1 << 20)))
    kn = wood_knock(rng, f=(180, 410, 760), dur=0.2, amp=(1, 0.4, 0.2))
    y = X._seq([(0, pk * 0.9), (0, slap * 0.5), (0, kn * 0.4)], 0.1)
    y = conv(y, ir_cabin(), 0.2)
    return y, X.onset_s(y, -18), 0.0, False


def r_tape_rewind(rng, sp, dur=0.6, **_):
    """The loop resets: the room's last half second scrubbed backward, pitch falling like a stopped tape."""
    d = float(dur)
    nz = X.noise(d, int(rng.integers(1 << 30)))
    f = np.geomspace(3800, 260, 48)
    sc = X.sweep_bp(nz, f, q=2.4) * np.linspace(1.0, 0.3, len(nz))
    t = np.arange(len(nz)) / X.SR
    wob = np.sin(2 * np.pi * np.cumsum(140 * (1 - 0.8 * t / d) * (1 + 0.15 * np.sin(2 * np.pi * 9 * t))) / X.SR)
    y = X.st((sc * 0.6 + wob * 0.12 * np.exp(-t / (d * 0.6))).astype(np.float32))
    y = X.fade(X._seq([(0, y)], 0.05), 0.02, 0.08)
    return wow(y, 2.5, 3.0, int(rng.integers(1 << 20))), 0.0, 0.0, False


# ============================================================================================ install
def install(mod):
    """Register this film's recipes, spaces and levels in the sfx module (called by sfx.py at import)."""
    global X, _POLICE_SPACE
    X = mod
    if getattr(mod, '_MIRROR_INSTALLED', False):
        return
    mod.r_clock_tick = mod.RECIPES['clock_tick']           # the police recipe stays reachable (fallback)
    _POLICE_SPACE = mod.space
    mod.space = space
    names = [k[2:] for k in globals() if k.startswith('r_')]
    for k in names:
        mod.RECIPES[k] = globals()['r_' + k]
    mod.LEVEL_LU.update(NEW_LEVEL_LU)
    mod.SPACE_LU.update(NEW_SPACES)
    mod.SPACES = tuple(mod.SPACE_LU)
    mod.BEDS = tuple(sorted(set(mod.BEDS) | set(NEW_BEDS)))
    for k, v in NEW_DEFAULT_SPACE.items():
        mod.DEFAULT_SPACE[k] = v
    for k, v in _PEAK.items():
        mod.PEAK_CAP[k] = v
    mod.NAMES = tuple(sorted(set(mod.NAMES) | set(names)))
    mod.MIRROR_NAMES = tuple(sorted(names))
    mod._MIRROR_INSTALLED = True
