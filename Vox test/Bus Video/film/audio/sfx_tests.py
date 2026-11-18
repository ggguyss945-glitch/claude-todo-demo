"""Bus film sound tests ("If The School Bus Stops At Midnight... DON'T GET ON"): 8 renders in W/mix/tests/ (W =
film/_work), each through the whole pipeline: mix.py on a window of the film (the real narration as aligned:
W/align/vo_en.wav on W/align/timeline.json (tools/align.py writes both from W/narration/narration_en.wav), with its line voicing: tv, his, loudspeaker, door, mimic,
mimic_slide, whisper, radio, phone, memory; this test's SFX cue sheet; the score with music_plan.py's plan: the track
map, the tension events and the identity, the ORIGINAL "Ride Right" jingle of audio/jingle_bus.py), as the final mix
will run it. Every window is anchored on the script's lines and words: re-run after a new voice edit.

    python3 sfx_tests.py [1 2 ... 8] [--jobs 1]     (default: all, one mix at a time: the machine is shared)
    python3 sfx_tests.py --sheet                     W/mix/tests/tests_sheet.png

    1 his_bus_midnight      rule 1: the air brakes, his idle, the PA reading the post, "I know your name!", fweet-fweet
    2 roll_call_almost      rule 2: the gloves, the roll call through the door, "Here!", "Almost.", click-clack
    3 fake_grandma_door     rule 3: three knocks, the fake Grandma, "...Clever." (the tape slide), the peephole
    4 hand_in_dark          rule 4: the lights die, the hand in the dark, the glove, the walkie, the lights snap back
    5 lighthouse_walkie     rule 4's end: the walkie, "LIGHTHOUSE!"
    6 chase_mirror          rule 6: the chase, the swerve, the mirror ripped off, his windows behind
    7 school_259_bell       rule 7: 2:59, the broom bending and cracking, "Theo.", the long whistle, the 3:00 bell
    8 warm_ending           the grin slips, Theo home, the porch light, the morning bus

and the measurements:
    per one-shot SFX cue (rendered alone with the same seed): transient_ms (its loudest transient vs the cue time: the
    picture's sync), phone_band_db (loudness left above 300 Hz: what a phone speaker plays), vs_voice_LU (the cue's
    momentary max vs the narration's there), vs_music_LU (vs the music stem there: does it read over the score)
    per identity event (the jingle's versions and the children's tunes, from stems/score_show.wav): its 1 s loudness
    median vs the voice's integrated level, and its share of energy in the voice band (1-4 kHz)
    flags: a cue more than 40 ms off, thinner than -15 dB on a phone, more than 20 LU under the voice or 12 LU under
    the music; an identity layer more than 24 LU under the voice
"""
import json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sfx as SX
import music_plan as MP

SR = 48000
W = SX.W
OUT = os.path.join(W, 'mix', 'tests')
TL = os.path.join(W, 'align', 'timeline.json')
VO = os.path.join(W, 'align', 'vo_en.wav')   # the narration exactly as TL aligned it (align.py's copy of narration_en.wav)
TL_J = json.load(open(TL))
LINES = TL_J['lines']
WORDS = json.load(open(os.path.join(W, 'align', 'asr_cache.json')))['en_words']
FULL = TL_J['duration_en'] + 2.5
# no single transient to sync (beds, slides, drags, rolls, rattles, cries, the jingle): not sync-checked
SLOW_ONSET = ('breath', 'mom_breath', 'mom_sob', 'cloth_rustle', 'riser', 'whoosh', 'door_creak', 'wood_creak',
              'paper', 'paper_slide', 'car_pass', 'footsteps_hall', 'footsteps_stairs', 'footsteps_wood_inside',
              'tape_glitch', 'vcr', 'lamp_flicker', 'curtain_flutter',
              'ambience_woods', 'owl_hoot', 'crowd_parade', 'hospital_corridor', 'hospital_room', 'burn_barrel',
              'plastic_melt', 'egg_rattle', 'ring_roll', 'ring_hand', 'oven_mitt', 'girl_cry', 'jingle', 'attic_door',
              'chest_lid', 'page_flip', 'wet_drag', 'doorknob', 'paper_under_door', 'sirens_arrive', 'vhs_pause',
              'music_box_wind', 'dogs_search', 'zipper', 'curtain_close', 'slot_flap', 'struggle', 'bathtub',
              'house_night', 'landline_ring', 'line_hiss', 'pen_scratch', 'paper_burn', 'rain_house', 'halverson_car',
              'waiting_room', 'pulse_count', 'tape_peel', 'drive_rain', 'er_doors', 'er_bustle', 'wheelchair',
              'sit_down', 'tiny_steps', 'now_serving',
              'suburb_night', 'bus_idle', 'his_bus_interior', 'school_night', 'morning_bus', 'bus_fast_night',
              'cat_rumble', 'broom_bend', 'tape_slide', 'school_bell', 'bus_pull_away', 'flag_rope', 'ticket_slide',
              'glove_squeak', 'walkie', 'pa_crackle', 'whistle', 'page_flip', 'tire_screech', 'bus_swerve')
TESTS = {}


def test(fn):
    TESTS[len(TESTS) + 1] = fn
    return fn


def A(anchor):
    return MP.resolve(anchor, LINES)


def ev(t, name, gain_db=0.0, space=None, pan=0.0, **params):
    e = {'t': round(float(t), 3), 'name': name, 'gain_db': gain_db, 'pan': pan}
    if space:
        e['space'] = space
    if params:
        e['params'] = params
    return e


def house(a, b, fridge=0.6, clock=0.5, rain=0.0, creaks=0.3):
    """Grandma's house at night (sfx house_night: room tone, the fridge, the wall clock, creaks, rain)."""
    return [ev(a, 'house_night', 0.0, dur=round(b - a, 2), fridge=fridge, clock=clock, rain=rain, creaks=creaks)]


def night_in(a, b, dog=0.3):
    """Inside the house at night: Larch Street through the windows (suburb_night inside=True)."""
    return [ev(a, 'suburb_night', 0.0, dur=round(b - a, 2), dog=dog, inside=True)]


@test
def t01_his_bus_midnight():
    """Rule 1: his bus arrives at midnight: the air brakes, his idling diesel at the curb, the PA crackles on, the
    jingle's first bars on the horn, he reads the post ("Sami. First grade..."), "Great smile, Mina!", "He read it off
    my phone.", "I know your name! That makes us friends!", "Fweet-fweet." """
    a, b = A('s65') - 0.6, A('e78') + 2.5
    return a, b, night_in(a, b) + [
        ev(A('s67') + 0.1, 'bus_air_brake', -2.0, 'window'),
        ev(A('s67') + 1.2, 'bus_idle', 0.0, 'window', dur=round(b - A('s67') - 1.2, 2), kind='his'),
        ev(A('w70:crackles') - 0.1, 'pa_crackle', 0.0, 'street', kind='on'),
        ev(A('e72') + 0.15, 'pa_crackle', -2.0, 'street', kind='off'),
        ev(A('s74') - 0.35, 'pa_crackle', -1.0, 'street', kind='on'),
        ev(A('e74') + 0.1, 'pa_crackle', -2.0, 'street', kind='off'),
        ev(A('s77') - 0.3, 'pa_crackle', -1.0, 'street', kind='on'),
        ev(A('s77'), 'cat_rumble', 0.0, dur=3.0),
        ev(A('s78') + 0.05, 'whistle', 0.0, 'street', kind='short'),
    ]


@test
def t02_roll_call_almost():
    """Rule 2: the gloves on the doorframe, the roll call through the front door, "He..." -- the hand slaps over his
    mouth, "Silence.", "Here!" in Sami's voice from the porch, "Almost.", "Click-clack.", the ticket under the door."""
    a, b = A('s100') - 0.6, A('e121') + 1.5
    return a, b, night_in(a, b, 0.0) + [
        ev(A('s100') + 0.3, 'glove_squeak', -2.0, 'outside', kind='stretch'),
        ev(A('s100') - 0.2, 'tape_skip', -4.0),
        ev(A('w111:slaps') + 0.05, 'cloth_rustle', 2.0, 'close'),
        ev(A('s113'), 'cat_rumble', 0.0, dur=3.5),
        ev(A('s117') + 0.05, 'ticket_punch', 0.0, 'outside'),
        ev(A('s118') + 0.2, 'ticket_slide', -2.0, 'close'),
    ]


@test
def t03_fake_grandma_door():
    """Rule 3: three knocks, the fake Grandma ("Mina, open up!"), "What's the word?", the voice slides down like a
    slowing tape: "...Clever.", the peephole goes white, the real Grandma pounding on bus 9's glass, the whisper."""
    a, b = A('s134') - 0.5, A('e153') + 1.5
    return a, b, night_in(a, b, 0.2) + [
        ev(A('w134:knocks') - 0.2, 'knock_door', 0.0, 'inside', n=3, force=0.75),
        ev(A('s143') - 0.05, 'tape_slide', -2.0, dur=1.1),
        ev(A('s144') - 0.1, 'peephole', 0.0, 'close'),
        ev(A('s144'), 'cat_rumble', 0.0, dur=3.0),
        ev(A('w147:pounding'), 'knock_door', -6.0, 'street', n=5, force=0.9, material='glass', accel=0.2),
        ev(A('s152') - 0.3, 'glove_squeak', -6.0, 'outside', kind='squeak', knuckles=False),
    ]


@test
def t04_hand_in_dark():
    """Rule 4: "Two ten." every light dies (the mains dive, total black), a small cold hand, "I'm still holding a
    hand.", the phone light, the white glove with one knuckle too many, the walkie in his other glove, "I rip free.",
    the lights snap back on."""
    a, b = A('s161') - 0.5, A('e182') + 1.0
    return a, b, [
        ev(a, 'house_night', 0.0, dur=round(A('w162:dies') - a, 2), fridge=0.6, clock=0.4, creaks=0.2),
        ev(A('w162:dies') - 0.05, 'power_down', 0.0, 'inside'),
        ev(A('s164') + 0.4, 'glove_squeak', -10.0, 'tight', kind='squeak', knuckles=False),
        ev(A('w170:walkie') + 0.2, 'walkie', -8.0, 'upstairs', kind='glitch'),
        ev(A('s172') + 0.3, 'light_switch', -1.0, 'close', kind='wall'),
        ev(A('s173'), 'glove_squeak', 0.0, 'close', kind='stretch'),
        ev(A('s173') - 0.3, 'cat_rumble', 2.0, dur=5.0),
        ev(A('s177') + 0.5, 'walkie', -2.0, 'close', kind='glitch'),
        ev(A('s179') + 0.05, 'cloth_rustle', 3.0, 'close'),
        ev(A('w180:snap') - 0.05, 'power_up', 0.0, 'inside'),
        ev(A('w180:snap') + 0.2, 'house_night', 0.0, dur=round(b - A('w180:snap') - 0.2, 2), fridge=0.6, clock=0.4),
    ]


@test
def t05_lighthouse_walkie():
    """Rule 4's end: upstairs, Sami hugging Rex, "You told me on the walkie to say our word..." (his glitchy squelch
    on the walkie under "walkie"), "Sami... what did you say?", "LIGHTHOUSE!", "Then it's not our word anymore." """
    a, b = A('s183') - 0.5, A('e189') + 1.5
    return a, b, [
        ev(a, 'house_night', 0.0, dur=round(b - a, 2), fridge=0.3, clock=0.4),
        ev(A('w185:walkie') - 0.1, 'walkie', -4.0, 'close', kind='engage'),
        ev(A('w185:walkie') + 0.35, 'walkie', -6.0, 'close', kind='glitch'),
        ev(A('e185') + 0.1, 'walkie', -6.0, 'close', kind='beep'),
        ev(A('s187') - 0.15, 'tape_skip', -2.0),
        ev(A('s188'), 'cat_rumble', 0.0, dur=3.5),
    ]


@test
def t06_chase_mirror():
    """Rule 6: bus 9 flat out at night, his dark bus ahead, the head out of the window turning backwards, his brake
    lights, the swerve, the mirror ripped off, the road empty, his amber windows behind us, "Fweet-fweet." """
    a, b = A('s272') - 1.0, A('e285') + 1.5
    return a, b, [
        ev(a, 'bus_fast_night', 0.0, dur=round(b - a, 2)),
        ev(A('s277') + 0.4, 'tire_screech', -6.0, 'street'),
        ev(A('w278:swerves') - 0.1, 'bus_swerve', 0.0, 'bus'),
        ev(A('w279:rips') - 0.05, 'mirror_rip', 0.0, 'bus'),
        ev(A('s281'), 'cat_rumble', 0.0, dur=4.0),
        ev(A('s284') + 0.05, 'whistle', -4.0, 'street', kind='short', far=True),
    ]


@test
def t07_school_259_bell():
    """Rule 7: "Two fifty-nine.", "What's your name?", "Fweet-fweet." the doors fold, Grandma jams the broom, the
    handle bends, Mina's voice from inside, the broom cracks, "Theo.", "THEO!", the long whistle against the clock,
    "...HERE!", the doors slam on an empty aisle, three o'clock: the school bell."""
    a, b = A('s336') - 0.5, A('e365') + 3.0
    return a, b, [
        ev(a, 'school_night', 0.0, dur=round(b - a, 2)),
        ev(a, 'his_bus_interior', -4.0, dur=round(A('s364') - a, 2)),
        ev(A('s343') + 0.05, 'whistle', 0.0, 'school', kind='short'),
        ev(A('s344') + 0.2, 'bus_door', -2.0, 'school', action='open'),
        ev(A('s345') + 0.6, 'broom_bend', 0.0, 'school', dur=1.4),
        ev(A('s346'), 'broom_bend', 2.0, 'school', dur=1.6),
        ev(A('w353:cracks') - 0.05, 'broom_crack', 0.0, 'school'),
        ev(A('w360:blows'), 'whistle', 2.0, 'school', kind='long'),
        ev(A('w363:slam') - 0.05, 'bus_door', 2.0, 'school', action='close'),
        ev(A('w365:bell') - 0.2, 'school_bell', 0.0, 'school', dur=4.0),
    ]


@test
def t08_warm_ending():
    """The warm turn: Grandma gasps, sees Theo, kneels ("Six mornings..."), she won't pull away until the porch light
    comes on, and for the first time in thirty-two years it does; the clipboard of names; the morning: the apology,
    the hug, "Brakes, mirrors, names." on the morning bus."""
    a, b = A('s371') - 0.8, A('e388') + 2.0
    return a, b, [
        ev(a, 'school_night', -3.0, dur=round(A('s375') - a, 2)),
        ev(A('s375'), 'bus_idle', -2.0, 'street', dur=round(A('s378') - A('s375'), 2), kind='bus9', rattle=0.0),
        ev(A('e377') - 0.4, 'light_switch', 0.0, 'street', kind='porch'),
        ev(A('s378'), 'page_flip', -4.0, 'close'),
        ev(A('s386'), 'morning_bus', 0.0, dur=round(b - A('s386'), 2), kids=0.5),
        ev(A('s387') + 0.1, 'cloth_rustle', -2.0, 'close'),
    ]


def _mom(x):
    return -0.691 + 10 * np.log10(SX._blocks(SX.st(x), 0.4, 0.05) + 1e-20)


def measure(name, a, b, cues, odir):
    sd = os.path.join(odir, 'stems')
    voice = sf.read(os.path.join(sd, 'voice_en.wav'), dtype='float32')[0]
    music = sf.read(os.path.join(sd, 'music.wav'), dtype='float32')[0]
    show_p = os.path.join(sd, 'score_show.wav')
    show = sf.read(show_p, dtype='float32')[0] if os.path.exists(show_p) else None
    Lv = SX.lufs_int(voice)
    vm, mm = _mom(voice), _mom(music)
    SX.reset()
    order = sorted([c for c in cues if isinstance(c.get('t'), (int, float))], key=lambda c: c['t'])
    log = []
    for c in order:
        name0 = c['name']
        cn, params, note = SX.resolve(name0, c.get('params') if isinstance(c.get('params'), dict) else {})
        if cn is None or not isinstance(c.get('gain_db', 0), (int, float)) or float(c.get('gain_db', 0)) <= -30:
            continue
        try:
            y, pre = SX.render_event(cn, seed=int(c['seed']), space=c.get('space') if isinstance(c.get('space'), str)
                                     else None, **params)
        except Exception as e:
            log.append({'t': c['t'], 'name': name0, 'error': repr(e)[:120]}); continue
        y = y * 10 ** (float(c.get('gain_db', 0.0)) / 20)
        bed = cn in SX.BEDS or (cn in SX.DUR_BEDS and 'dur' in params)
        Lc = SX.lufs_int(y) if bed else SX.mom_max(y)
        ent = {'t': c['t'], 'name': name0, 'resolved': cn, 'space': c.get('space') or SX.DEFAULT_SPACE[cn],
               'gain_db': c.get('gain_db', 0.0), 'params': c.get('params'), 'dur': round(len(y) / SR, 2),
               ('loud_I_rel_voice_LU' if bed else 'loud_M_rel_voice_LU'): round(Lc - Lv, 1)}
        if not bed:
            j0 = max(0, int((c['t'] - a) / 0.05)); j1 = j0 + max(1, int(min(len(y) / SR - pre, 1.0) / 0.05))
            Mm = SX.mom_max(y)
            ent['check'] = {
                'transient_ms': round(1000 * (SX.onset_s(y, -12) - pre)),
                'phone_band_db': round(SX.mom_max(SX.hp(SX.hp(y, 300, 2), 300, 2)) - Mm, 1),
                'vs_voice_LU': round(Mm - float(vm[j0:j1].max()), 1) if j0 < len(vm) else None,
                'vs_music_LU': round(Mm - float(mm[j0:j1].max()), 1) if j0 < len(mm) else None}
        log.append(ent)
    flags = []
    for e in log:
        ck = e.get('check')
        if not ck:
            continue
        w = []
        if abs(ck['transient_ms']) > 40 and e['resolved'] not in SLOW_ONSET:
            w.append(f"transient {ck['transient_ms']} ms off the cue")
        if ck['phone_band_db'] < -15 and e['resolved'] not in ('goodnight_hit', 'struggle', 'window_smash', 'door_crash'):
            w.append(f"{ck['phone_band_db']} dB above 300 Hz (thin on a phone)")
        speech_tick = False
        if (ck['vs_voice_LU'] or 0) < (-26 if speech_tick else -20):   # his per-word ticks ride under his own line
            w.append(f"{ck['vs_voice_LU']} LU under the voice there")
        if (ck['vs_music_LU'] or 0) < -12 and not speech_tick:
            w.append(f"{ck['vs_music_LU']} LU under the music there")
        if w:
            flags.append(f"{e['t']} {e['resolved']}: " + ', '.join(w))
    ident = []
    if show is not None:
        sm = -0.691 + 10 * np.log10(SX._blocks(SX.st(show), 1.0, 0.25) + 1e-20)
        for e in MP.identity_events(LINES):
            if e['type'] not in ('show', 'winks', 'jingle', 'hold') or e['t'] + e.get('len', 0) < a + 1.0 or e['t'] > b - 1.0:
                continue                                   # (less than 1 s inside the window: nothing to measure)
            i0 = max(0, int((max(e['t'], a) - a + 0.5) / 0.25)); i1 = int((min(e['t'] + e.get('len', 0), b) - a - 0.5) / 0.25)
            seg = sm[i0:max(i0 + 1, i1)]
            seg = seg[seg > -70]
            if not len(seg):                               # a short event (the cut "Seven"): its momentary max
                x0 = int((max(e['t'], a) - a) * SR); x1 = int((min(e['t'] + max(0.4, e.get('len', 0)), b) - a) * SR)
                if x1 > x0 + 100:
                    seg = np.array([SX.mom_max(SX.st(show[x0:x1]))])
            x = SX.mono(show[int((max(e['t'], a) - a) * SR):int((min(e['t'] + e.get('len', 0), b) - a) * SR)])
            P = np.abs(np.fft.rfft(x)) ** 2 if len(x) > 1000 else np.ones(10); f = np.fft.rfftfreq(len(x), 1 / SR) if len(x) > 1000 else np.ones(10)
            r = {'t': e['t'], 'type': e['type'], 'version': e.get('version') or e.get('slug'), 'space': e.get('space'),
                 'len': e.get('len'),
                 'level_1s_median_rel_voice_LU': round(float(np.median(seg)) - Lv, 1) if len(seg) else None,
                 'voice_band_share_pct': round(100 * float(P[(f >= 1000) & (f < 4000)].sum() / P.sum()), 1)}
            ident.append(r)
            if r['level_1s_median_rel_voice_LU'] is None or r['level_1s_median_rel_voice_LU'] < -24:
                flags.append(f"{e['t']} {e['type']}: {r['level_1s_median_rel_voice_LU']} LU under the voice (lost)")
    sfx_ = sf.read(os.path.join(sd, 'sfx.wav'), dtype='float32')[0]
    prof = []
    for j in range(int(len(voice) / SR)):
        seg = slice(j * SR, (j + 1) * SR)
        row = [round(a + j, 1)]
        for x in (voice, music, sfx_) + ((show,) if show is not None else ()):
            m = x[seg]
            row.append(round(SX.mom_max(m) - Lv, 1) if np.abs(m).max() > 1e-6 else -99.0)
        prof.append(row)
    return log, ident, flags, prof


def run(k):
    fn = TESTS[k]
    a, b, cues = fn()
    for i, c in enumerate(cues):                     # explicit seeds: the measurement renders the same takes
        c.setdefault('seed', 1000 * k + i)
    name = f'{k:02d}_' + fn.__name__.split('_', 1)[1]
    cdir = os.path.join(OUT, 'cues', name); os.makedirs(cdir, exist_ok=True)
    json.dump(cues, open(os.path.join(cdir, 'sfx_cues.json'), 'w'), indent=0)
    json.dump(MP.music_cues(LINES, FULL), open(os.path.join(cdir, 'music_cues.json'), 'w'), indent=0)
    odir = os.path.join(OUT, 'mix_' + name)
    cmd = [sys.executable, os.path.join(HERE, 'mix.py'), TL, VO, '-', cdir, odir, '--t0', str(a), '--langs', 'en',
           '--score-stems', '--plan', 'auto'] + os.environ.get('BUS_MIX_ARGS', '--bed-p50 -14').split()   # (the Bus film: -16 left the music 42-85 % present)
    if b < FULL - 0.01:
        cmd += ['--t1', str(b)]
    t0 = time.time()
    env = dict(os.environ, OMP_NUM_THREADS='1', NUMBA_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    open(os.path.join(OUT, name + '.log'), 'w').write(r.stdout + '\n' + r.stderr)
    if r.returncode != 0:
        print(name, 'FAILED\n', r.stdout[-2500:], r.stderr[-2500:]); return name, None
    os.replace(os.path.join(odir, 'mix_en.wav'), os.path.join(OUT, name + '.wav'))
    rep = json.load(open(os.path.join(odir, 'mix_report.json')))
    log, ident, flags, prof = measure(name, a, b, cues, odir)
    json.dump({'film_window': [a, b], 'about': fn.__doc__ or '', 'report': rep, 'identity': ident, 'flags': flags,
               'profile_1s_cols': ['film s', 'voice', 'music', 'sfx', 'show'], 'profile_1s': prof,
               'cues': log, 'seconds': round(time.time() - t0, 1)},
              open(os.path.join(OUT, name + '.json'), 'w'), indent=1)
    import shutil
    shutil.rmtree(odir, ignore_errors=True)          # stems are large: the measurements are in the json
    en = rep['langs']['en']
    print(f"{name}: {b - a:.1f} s, mix {en['mix_lufs']} LUFS TP {en['true_peak_dbtp']}, bed {en['bed_rel_voice']} LU "
          f"(speech median {en['bed_speech_median']}), music {en['music_rel_voice']} LU present {en['music_present_pct']}%, "
          f"fallbacks {len(rep.get('sfx_fallbacks', []))}, flags {len(flags)}, {time.time() - t0:.0f} s", flush=True)
    return name, flags


def sheet():
    """W/mix/tests/tests_sheet.png: per test, the mix's spectrogram (log frequency) and its 1 s profile (voice, music,
    SFX, the identity stem, LU rel the voice's integrated level), with the cue times marked."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from scipy import signal
    names = [f'{k:02d}_' + fn.__name__.split('_', 1)[1] for k, fn in TESTS.items()]
    names = [n for n in names if os.path.exists(os.path.join(OUT, n + '.json'))]
    fig, axs = plt.subplots(len(names) * 2, 1, figsize=(16, 3.6 * len(names)), dpi=80,
                            gridspec_kw={'height_ratios': [2, 1] * len(names)})
    for k, nm in enumerate(names):
        j = json.load(open(os.path.join(OUT, nm + '.json')))
        a, b = j['film_window']
        x = sf.read(os.path.join(OUT, nm + '.wav'), dtype='float32')[0].mean(1)
        f, t, S = signal.spectrogram(x, SR, nperseg=4096, noverlap=3072)
        S = 10 * np.log10(S + 1e-14); vm = np.percentile(S, 99.5)
        ax = axs[2 * k]
        ax.pcolormesh(t + a, f, S, shading='auto', cmap='magma', vmin=vm - 80, vmax=vm, rasterized=True)
        ax.set_yscale('log'); ax.set_ylim(40, 16000); ax.set_xlim(a, b)
        en = j['report']['langs']['en']
        ax.set_title(f"{nm}: {j['about'].strip().splitlines()[0][:80] if j['about'] else ''}  |  mix {en['mix_lufs']} LUFS, "
                     f"TP {en['true_peak_dbtp']}, bed {en['bed_rel_voice']} LU, flags {len(j['flags'])}", fontsize=9,
                     loc='left')
        for c in j['cues']:
            ax.axvline(c['t'], color='cyan', lw=0.6, alpha=0.6)
        for e in j['identity']:
            ax.axvspan(e['t'], e['t'] + (e.get('len') or 0.4), color='lime', alpha=0.12)
        P = np.array(j['profile_1s'], float)
        ax2 = axs[2 * k + 1]
        for col, lab, colr in ((1, 'voice', 'k'), (2, 'music', 'tab:blue'), (3, 'sfx', 'tab:red'), (4, 'jingle', 'tab:green')):
            if P.shape[1] > col:
                ax2.plot(P[:, 0] + 0.5, np.maximum(P[:, col], -45), color=colr, lw=1, label=lab)
        ax2.set_xlim(a, b); ax2.set_ylim(-45, 8); ax2.grid(alpha=0.3); ax2.legend(fontsize=7, ncol=4, loc='lower right')
        ax2.set_ylabel('LU rel voice', fontsize=7)
    plt.tight_layout()
    p = os.path.join(OUT, 'tests_sheet.png')
    plt.savefig(p)
    print('wrote', p)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    argv = sys.argv[1:]
    if '--sheet' in argv:
        sheet(); sys.exit(0)
    jobs = 1
    if '--jobs' in argv:
        k = argv.index('--jobs'); jobs = int(argv[k + 1]); argv = argv[:k] + argv[k + 2:]
    which = [int(x) for x in argv if not x.startswith('--')] or list(range(1, len(TESTS) + 1))
    with ThreadPoolExecutor(max_workers=max(1, jobs)) as ex:
        for name, flags in ex.map(run, which):
            for f in flags or []:
                print('   flag', name, f)
