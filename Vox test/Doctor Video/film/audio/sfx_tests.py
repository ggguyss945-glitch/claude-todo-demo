"""Doctor film sound tests ("If Your Doctor Calls At 3 AM... DON'T ASK WHAT THEY FOUND"): 8 renders in W/mix/tests/
(W = film/_work), each through the whole pipeline: mix.py on a window of the film (the narration with its line voicing:
phone / recording / door / whisper / rooms; this test's SFX cue sheet; the score with music_plan.py's plan: the
dark track map, the tension events and the film's identity, the ORIGINAL HOLD MUSIC of audio/hold.py), as the final
mix will run it.

    python3 sfx_tests.py [1 2 ... 8] [--jobs 1]     (default: all, one mix at a time: the machine is shared)
    python3 sfx_tests.py --sheet                     W/mix/tests/tests_sheet.png

    1 cold_open             0-58      the 3 AM ring, the waiting room, "Take a seat.", the phone system and the hold music
    2 call_3am              219-282   rule 1: seven rings, the receiver, Halverson on the line, hung up, the cord
    3 unplugged_hold        305-362   rule 2: the unplugged phone rings, the hold music, the receiver on the counter, rooms
    4 pen_click_hall        359-414   rule 3: "I'm so thirsty", the hand, the pen click alone, the pen scratching
    5 knock_note_match      418-497   rule 4: the knock, the peephole, the rain and her car, the note, the match, the fire
    6 waiting_room_ticket   590-718   rule 6: the tubes, the TV, the ceiling's hold music, NOW SERVING, the ticket
    7 pulse_to_question     717-790   rule 7: the count slowing the hold music, the heartbeat and the clock, the cut, tape
    8 car_to_er             918-980   the back seat, the warped car radio, "Not on my shift.", the ER doors, the ER

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
VO = os.path.join(W, 'align', 'vo_en.wav')
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
              'sit_down', 'tiny_steps', 'now_serving')
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


@test
def t01_cold_open():
    """The trailer and the hold music: the 3 AM ring, the waiting room's tubes under the very tall man, "Take a seat.
    It can wait." "Don't sit down.", the phone system ("Your call is important to us. Please hold.") and the hold
    music under the rules in the medicine cabinet"""
    a, b = 0.0, 58.0
    return a, b, [
        ev(0.05, 'landline_ring', -3.0, 'next_room', n=1, on=1.2),            # three in the morning
        ev(A('s2') + 1.0, 'waiting_room', 0.0, dur=round(A('e6') + 0.6 - A('s2') - 1.0, 2), flicker=0.5),
        ev(A('w2:folded') + 0.2, 'sit_down', -6.0, 'waiting', kind='plastic'),   # folded into the little chair
        ev(A('w4:take') - 0.6, 'pen_click', -4.0, 'waiting', n=2, spacing=0.3),
        ev(A('e6') + 0.6, 'house_night', 0.0, dur=round(b - A('e6') - 0.6, 2), fridge=0.6, clock=0.6),
        ev(A('w10:medicine') - 0.4, 'medicine_cabinet', -2.0, action='open'),  # behind the mirror
    ]


@test
def t02_call_3am():
    """Rule 1: the landline at 3 AM (seven rings), the receiver lifted and tilted, Halverson on the line ('phone'
    voice), "Don't you dare tell me what you found.", hung up, ringing again, the cord yanked out of the wall"""
    a, b = 219.0, 282.0
    r0 = A('e67') + 0.1
    return a, b, house(a, b, fridge=0.6, clock=0.7) + [
        ev(r0, 'landline_ring', 0.0, 'close', n=7, cycle=1.75, on=1.1),
        ev(A('w73:picked') + 0.05, 'receiver_up', 0.0),
        ev(A('s78') - 0.5, 'line_hiss', -6.0, dur=round(A('e80') + 0.6 - A('s78') + 0.5, 2)),
        ev(A('e83') + 0.25, 'receiver_down', 0.0, kind='hang'),
        ev(A('e84') + 0.15, 'landline_ring', 0.0, 'close', n=3, cycle=1.55, on=1.0),
        ev(A('w88:pulled') + 0.1, 'cord_yank', 0.0),
    ]


@test
def t03_unplugged_hold():
    """Rule 2: the cord on the floor, the phone rings anyway, Grandma picks it up: no voice, just hold music (the
    landline version), the recorded lady ('recording' voice), the receiver set down on the counter like a sleeping
    baby, the music playing all night, then from the hallway, the living room, Grandpa's chair ('rooms')"""
    a, b = 305.0, 362.0
    return a, b, house(a, b, fridge=0.5, clock=0.6) + [
        ev(A('s107') - 0.7, 'landline_ring', 0.0, 'close', n=1, on=1.2),
        ev(A('e108') - 0.35, 'receiver_up', 0.0),
        ev(A('w117:set') + 0.3, 'receiver_down', 0.0, kind='set'),
    ]


@test
def t04_pen_click_hall():
    """Rule 3: Milo in the kitchen ("I'm so thirsty", 'whisper'), Grandma's hand over his mouth, "Not out loud.",
    then from the dark hallway a pen click (alone in a silence), the scratch of a pen on paper"""
    a, b = 359.0, 414.0
    return a, b, house(a, b, fridge=0.7, clock=0.7) + [
        ev(A('s127') + 1.0, 'tiny_steps', -6.0, 'inside', n=6),
        ev(A('s135') - 0.25, 'cloth_rustle', -4.0, kind='grab', dur=0.6),     # the hand over his mouth
        ev(A('w138:click') + 0.35, 'pen_click', 2.0, 'inside', n=1, pan=-0.35),
        ev(A('w139:scratch') + 0.2, 'pen_scratch', 0.0, 'inside', dur=3.4, pan=-0.35),
    ]


@test
def t05_knock_note_match():
    """Rule 4: the knock at 3:40, the peephole, Halverson on the porch in the rain ('door' voice), her car idling in
    the driveway, the paper sliding under the door, the warning signs, the match struck over the sink, the paper
    burning"""
    a, b = 418.0, 497.0
    return a, b, house(a, b, fridge=0.4, clock=0.5, rain=0.0) + [
        ev(a, 'rain_house', 0.0, dur=round(b - a, 2)),
        ev(a, 'halverson_car', -2.0, 'outside', dur=round(b - a, 2), rain=0.0),
        ev(A('w149:knocked') + 0.1, 'knock_door', 0.0, 'inside', n=4, force=0.8),
        ev(A('s150') + 0.2, 'peephole', 0.0),
        ev(A('w168:slid') - 0.3, 'paper_under_door', 0.0, 'close', dur=1.3),
        ev(A('w179:match') + 0.15, 'match_strike', 0.0),
        ev(A('w179:match') + 1.3, 'paper_burn', 0.0, dur=round(b - A('w179:match') - 1.3, 2)),
    ]


@test
def t06_waiting_room_ticket():
    """Rule 6: the living room is a waiting room: buzzing tubes half dead, the dead TV, the ceiling speaker's hold
    music, "Now serving: 1979." (the sign's sour ding), the still grey people, Grandpa, HIM in the armchair, his pen,
    the ticket torn from the machine across the room, "Take a seat. It can wait." """
    a, b = 590.0, 718.0
    return a, b, [
        ev(a, 'waiting_room', 0.0, dur=round(b - a, 2), flicker=0.6, tv=0.6, buzz=0.7),
        ev(A('s223') - 0.25, 'now_serving', 0.0, sour=0.7),
        ev(A('w244:clicking') + 0.4, 'pen_click', 0.0, 'waiting', n=3, spacing=0.32),
        ev(A('s245') + 3.6, 'ticket_tear', 0.0),
        ev(A('w243:clipboard') + 0.3, 'clipboard', -4.0, 'waiting'),
    ]


@test
def t07_pulse_to_question():
    """Rule 7: he takes the wrist; "One... Two... Three...": the hold music slows and sags at every count, the
    heartbeat through the wrist and the wall clock slow with it; cut dead on "What did you find?"; one strip of tape
    per question"""
    a, b = 717.0, 790.0
    c1, c2, c3 = A('w258:one'), A('w260:two'), A('w267:three')
    cues = [ev(a, 'waiting_room', -4.0, dur=round(A('w270:what') - a, 2), flicker=0.4, tv=0.0, buzz=0.4),
            ev(c1, 'pulse_count', 0.0, dur=round(A('w270:what') - 0.05 - c1, 2),
               counts=[0.0, round(c2 - c1, 3), round(c3 - c1, 3)], bpm=[62, 48, 36, 27], clock=0.7)]
    for q, ln in enumerate((272, 273, 274, 275), 1):
        cues.append(ev(A(f'e{ln}') + 0.12, 'tape_peel', 0.0, 'tight', q=q))
    cues.append(ev(A('e270') + 0.15, 'tape_peel', -3.0, 'tight', q=1))
    return a, b, cues


@test
def t08_car_to_er():
    """The rescue: in the car in the rain ("Every question I had. And she answered every single one."), the
    rear-view mirror, Doctor Later in the back seat clicking his pen, "It can wait," (the car radio's warped hold
    music), "Not tonight. Not on my shift.", she drives faster, the ER doors open, Mom with a wheelchair, the ER warm
    and alive"""
    a, b = 918.0, 980.0
    er = A('s348')
    return a, b, [
        ev(a, 'drive_rain', 0.0, dur=round(er - a + 0.6, 2), speed='fast'),
        ev(A('w334:clicking') + 0.3, 'pen_click', -2.0, 'car', n=3, spacing=0.34, pan=0.25),
        ev(er - 0.4, 'er_doors', 0.0, 'er'),
        ev(er + 0.2, 'er_bustle', 0.0, dur=round(b - er - 0.2, 2), monitors=0.7, gurney=0.5),
        ev(A('w349:running') + 0.2, 'wheelchair', 0.0, 'er', dur=3.5),
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
           '--who-fx', '', '--score-stems', '--plan', 'auto']
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
