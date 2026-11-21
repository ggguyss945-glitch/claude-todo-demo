"""Ice Cream film sound tests ("If The Ice Cream Truck Plays Its Song In Winter... DON'T GO OUTSIDE"): 8 renders in
W/mix/tests/ (W = film/_work), each through the whole pipeline: mix.py on a window of the film with the real narration
as aligned (W/align/vo_en.wav on W/align/timeline.json) and its line voicing (his+truck, mimic+radio with his bells,
radio, mimic+door, whisper; the narrator dry), this test's SFX cue sheet (sfx_ice.py names, as the picture will cue
them), and the score with music_plan.py's plan: the track map, the tension events and HIS CHIME (chime_ice.py). Every
window and cue is anchored on the script's words (music_plan.resolve): re-run after a new voice edit.

    python3 audio/sfx_tests.py [1 2 ... 8] [--jobs 1]     (default: all, one mix at a time: the machine is shared)
    python3 audio/sfx_tests.py --sheet                     W/mix/tests/tests_sheet.png

    1 hook_far_chime        the cold open: the icy wind, "Who's cold?" over the chime's burst, "That was the problem."
    2 driveby_song_stops    the truck glides by (engine only), the flicker (glimpse 1), the song stops dead outside
    3 shatter_power_skull   the slap, the cone shatters, "Click." the furnace dies, the lights die, the TV skull
    4 fake_dad_bells        the fake Dad on the radio (bells under him), the real Dad, "Static. Bells."
    5 transformation        the smile, skin, bone cracks, the jaw's pop, the uniform tears, the legs punch out
    6 chase_home            one sock, legs stabbing the snow, the coat speared, fence / car / roof, the drop, the slam
    7 attic_leg_under_door  clicks across the ceiling, the hatch, the leg tip under the door, the towel
    8 climax_warm_turn      the chime hangs on the empty beat, the plow and its horn, porch lights, falls apart, the
                            ambulance, "Bye, Benny."

and the measurements (per cue: transient vs the cue time, phone band, vs voice, vs music; per chime event: its level
vs the voice and its voice-band share; flags as in the Bus film's tests).
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
VO = os.path.join(W, 'align', 'vo_en.wav')   # the narration exactly as TL aligned it
TL_J = json.load(open(TL))
LINES = TL_J['lines']
FULL = TL_J['duration_en'] + 2.5
# no single transient to sync (beds, glides, scuttles, slides, stretches): not sync-checked
SLOW_ONSET = ('cold_night', 'frozen_still', 'house_hum', 'house_cold', 'truck_idle', 'truck_glide', 'plow_pass',
              'shovel_morning', 'radio_static', 'frost_creep', 'attic_crawl', 'scuttle', 'ambulance', 'skin_stretch',
              'uniform_tear', 'boot_stuck', 'leg_tip_tile', 'snow_run', 'snow_walk', 'snow_deep', 'street_wakes',
              'plow_horn', 'furnace_die', 'window_crack', 'curtain_yank', 'street_flicker', 'serving_window',
              'radio_bells', 'radio_squelch', 'frost_wipe', 'blanket_yank')
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


def bed(a, b, name, gain_db=0.0, **params):
    return ev(a, name, gain_db, dur=round(b - a, 2), **params)


@test
def t01_hook_far_chime():
    """The cold open: the icy wind over the roofs, frost on the dark window, "Who's cold?..." over the chime's burst
    (his voice from the pink window), "That was the problem." """
    a, b = max(0.0, A('If the ice cream truck plays its song') - 0.6), A('end:That was the problem') + 2.5
    return a, b, [bed(a, b, 'cold_night', 0.0, creaks=0.4),
                  ev(A('And if Mom knocks') + 0.2, 'frost_creep', -6.0, dur=2.5),
                  ev(A("Who's cold? Who wants") - 0.7, 'truck_speaker', -2.0)]


@test
def t02_driveby_song_stops():
    """The drive-by: the truck glides down Birch Lane (engine only, no tires), the serving window glow, the
    streetlight flickers (glimpse 1), the song stops dead outside: only his idle; no breath cloud."""
    a, b = A('The truck glides down Birch Lane') - 1.0, A('end:And that smile breathes') + 2.5
    t_stop = A('The song stops. Right outside#stops')
    return a, b, [bed(a, b, 'cold_night', -8.0, inside=True, creaks=0.2), bed(a, b, 'house_hum', 0.0),
                  ev(A('The truck glides down Birch Lane') + 3.5, 'truck_glide', 0.0, dur=9.0, peak=3.5),
                  ev(A('The streetlight flickers'), 'street_flicker', -2.0, 'street', n=4),
                  bed(t_stop, b, 'truck_idle', 0.0)]


@test
def t03_shatter_power_skull():
    """The couch: "I slap it." the cone hits the floor and shatters like glass, "Click." the furnace dies, every light
    goes out (the house hum stops), the long white skull in the black TV, the curtain yanked shut."""
    a, b = A("Lina's on the couch") - 0.5, A('end:I yank the curtain shut') + 2.0
    t_click = A('Click.')
    return a, b, [bed(a, t_click + 2.2, 'house_hum', 0.0), bed(t_click + 2.0, b, 'house_cold', 0.0),
                  bed(a, b, 'truck_idle', -6.0, inside=True),
                  ev(A('I slap it') + 0.15, 'blanket_yank', -8.0, 'close'),
                  ev(A('It hits the floor#shatters') - 0.25, 'cone_shatter', 0.0),
                  ev(t_click, 'furnace_die', 0.0),
                  ev(A('Every light in the house goes out'), 'power_cut', 0.0),
                  ev(A('I yank the curtain shut') + 0.3, 'curtain_yank', 0.0)]


@test
def t04_fake_dad_bells():
    """The fake Dad on the radio (the copy, his bells faint under it: audio only), "Silence.", "Sleep is warm", the leg
    shadow, the REAL Dad (clean, "Over."), "Told you what?", "Static. Bells." cutting Adam off."""
    a, b = A('The radio crackles') - 0.8, A("end:The pink one doesn't") + 2.0
    out = [bed(a, b, 'house_cold', 0.0), bed(a, b, 'truck_idle', -6.0, inside=True),
           ev(A('The radio crackles'), 'radio_static', 0.0, dur=1.2, bells=0.3)]
    for ph in ('Adam. Do NOT go', 'Then keep her warm, kiddo'):
        out += [ev(A(ph) - 0.25, 'radio_squelch', 0.0, on=True), ev(A('end:' + ph) + 0.05, 'radio_squelch', -2.0, on=False)]
    for ph in ('Adam? Passing our street', 'Told you what', 'say again, Adam'):
        out += [ev(A(ph) - 0.25, 'radio_clean', 0.0)]
    out += [ev(A('Then an orange light sweeps the street'), 'plow_pass', -10.0, dur=8.0, peak=2.5),
            ev(A('Static. Bells') - 0.05, 'radio_bells', 0.0, dur=2.2)]
    return a, b, out


@test
def t05_transformation():
    """The transformation, a foot from Adam's face (the chime cheerful through it): the smile keeps going, the skin
    pulls long and hard, bone cracks, the eyes, the jaw drops (the deep pop), the uniform bulges and splits, a leg
    punches out and plants ("Click."), another, two more, he pours out of the window."""
    a, b = A('He keeps smiling. Keeps waving') - 0.6, A('end:Head first. Legs last') + 2.0
    return a, b, [bed(a, b, 'cold_night', -4.0, creaks=0.0), bed(a, b, 'truck_idle', -2.0),
                  ev(A('His skin pulls long'), 'skin_stretch', 0.0, dur=2.0),
                  ev(A('Like a mask made of bone') - 0.3, 'bone_crack', 0.0, n=3),
                  ev(A('His jaw drops') + 0.05, 'jaw_drop', 0.0),
                  ev(A('Behind him, the striped uniform#bulges'), 'uniform_tear', 0.0),
                  ev(A('A long brown leg punches out#punches'), 'leg_punch', 0.0, surface='metal'),
                  ev(A('end:jointed like a spider') + 0.3, 'leg_click', 0.0, surface='metal'),
                  ev(A('Click. Another') + 0.6, 'leg_punch', -2.0, surface='metal'),
                  ev(A('Click. Another') + 1.5, 'leg_click', 0.0, surface='metal', n=2),
                  ev(A('He pours out of the window'), 'scuttle', -2.0, surface='car', dur=1.6)]


@test
def t06_chase_home():
    """The chase home: the foot ripped out of the frozen boot, the run in one sock (knee-deep), legs stabbing the snow,
    one spearing the coat, along the fence, over Dad's car, onto the roof, the drop at the door, the slam."""
    a, b = A('I rip my foot out') - 0.8, A('end:and slam the door') + 2.0
    t0 = A('I rip my foot out')
    return a, b, [bed(a, b, 'cold_night', 0.0, creaks=0.0),
                  ev(t0 - 0.3, 'boot_rip', 0.0),
                  ev(t0 + 0.6, 'snow_deep', -2.0, n=8, rate=2.4),
                  ev(A('Legs stab the snow'), 'leg_stab_snow', 0.0, n=3),
                  ev(A('One spears my coat'), 'leg_spear_coat', 0.0),
                  ev(A('He scuttles along our fence'), 'scuttle', 0.0, surface='fence', dur=1.8),
                  ev(A("Over Dad's car"), 'scuttle', 0.0, surface='car', dur=1.4),
                  ev(A('Up onto our roof'), 'scuttle', -2.0, surface='roof', dur=1.6),
                  ev(A('And drops. Right in front'), 'leg_stab_snow', 2.0, n=2),
                  ev(A('I duck under him#slam') + 0.1, 'door_slam', 0.0)]


@test
def t07_attic_leg_under_door():
    """Rule 6: clicks across the ceiling (he is in the attic, following them), the hallway hatch drops open, a leg
    between them, the dive into the bathroom, the needle-thin leg tip under the door on the tile, the towel jammed
    down on it, it pulls back, the clicking stops."""
    a, b = A('Click. Click. Click') - 1.0, A('end:The clicking stops') + 2.5
    return a, b, [bed(a, b, 'house_cold', 0.0),
                  ev(A('Click. Click. Click'), 'attic_crawl', 0.0, dur=4.5),
                  ev(A('The hallway hatch drops open') + 0.2, 'hatch_drop', 0.0),
                  ev(A('A leg reaches between us'), 'leg_click', 0.0, surface='wood', n=2),
                  ev(A('Under the door, a needle-thin') + 0.4, 'leg_tip_tile', 0.0, dur=2.2),
                  ev(A('I jam the towel down') + 0.4, 'towel_jam', 0.0),
                  ev(A('It pulls back'), 'leg_tip_tile', -6.0, dur=0.6)]


@test
def t08_climax_warm_turn():
    """The climax: the old man starts to shiver, the song reaches the empty beat and HANGS, Dad's plow roars in, the
    horn again and again, porch lights and doors, "Cold. Alone.", the song falls apart, the truck glides into the
    white, the mitten drops, the ambulance, "Bye, Benny." """
    a, b = A('And the old man starts to shiver') - 0.5, A('end:Mr. Kessler whispers') + 3.0
    return a, b, [bed(a, A('The truck glides into the white') + 3.0, 'cold_night', -2.0, creaks=0.0),
                  bed(a, A('The truck glides into the white'), 'truck_idle', -4.0, far=True),
                  ev(A("Dad's plow roars onto Birch Lane"), 'plow_pass', 0.0, dur=9.0, peak=1.5),
                  ev(A('Horn blaring, again and again'), 'plow_horn', 0.0, n=5, gap=0.45),
                  ev(A('Porch lights click on'), 'street_wakes', 0.0, n=6, span=5.0),
                  ev(A('The truck glides into the white'), 'truck_glide', -4.0, dur=7.0, peak=1.0),
                  ev(A("Lina's mitten drops into the snow") + 0.4, 'mitten_drop', 0.0),
                  ev(A('The truck glides into the white') + 2.0, 'ambulance', -6.0, dur=10.0)]


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
           '--score-stems', '--plan', 'auto'] + os.environ.get('ICE_MIX_ARGS', '--bed-p50 -14').split()
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
        for col, lab, colr in ((1, 'voice', 'k'), (2, 'music', 'tab:blue'), (3, 'sfx', 'tab:red'), (4, 'chime', 'tab:green')):
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
