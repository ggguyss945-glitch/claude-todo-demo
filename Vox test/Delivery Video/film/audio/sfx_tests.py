"""Delivery film sound tests: 8 short renders in W/mix/tests/ (W = film/_work).

    python3 sfx_tests.py [1 2 ... 8]     (default: all)

Tests 1-7 put this film's SFX on the real narration (vo_en.wav at -14 LUFS, line voicing from mix.LINE_FX: the
driver's 'doorbell' lines, the 'box' voice, X lines with 'hall') at the house levels (sfx.LEVEL_LU), no music, then a
true-peak limiter at -1 dBTP. Test 8 runs the whole pipeline (mix.py: voice + SFX cue sheet + score.py) on the
ending, 586-643 s: the music is the director's W/cues/music_cues.json with the music_plan.py map added by mix.py
(--plan auto, shifted to the window), as the final mix will run it; its SFX sheet includes an unknown SFX name and an
unknown space on purpose (the mix must fall back with a warning, not crash). Each test writes <name>.wav and
<name>.json (the cue list, levels and measurements).
Listening checks by measurement (tests 1-7, per one-shot cue, in <name>.json 'check'): transient_ms (the loudest
transient vs the cue time; the picture's sync), phone_band_db (loudness left above 300 Hz: what a phone speaker
plays), vs_voice_here_LU (the cue against the narration at that moment). measure.flags lists cues more than 40 ms
off, thinner than -15 dB on a phone, or 20 LU under the voice.
"""
import json, os, subprocess, sys, time
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sfx as SX
import mix as MX
import music_plan as MP

SR = 48000
W = SX.W
OUT = os.path.join(W, 'mix', 'tests')
TL = os.path.join(W, 'align', 'timeline.json')
VO = os.path.join(W, 'align', 'vo_en.wav')
WHO_FX = {'X': 'hall'}            # tests voice the hallway X lines with 'hall' (box lines keep their 'box' fx)
# no single transient to sync (breaths, cloth, a vibration motor ramping up, creaks, slides): not sync-checked
SLOW_ONSET = ('breath', 'mom_breath', 'mom_sob', 'phone_vibrate', 'curtain_flutter', 'cloth_rustle', 'tinnitus', 'riser',
              'whoosh', 'door_creak', 'box_creak', 'box_scrape', 'van_pull_away', 'window_slide', 'heartbeat')


def ev(t, name, gain_db=0.0, space=None, pan=0.0, **params):
    e = {'t': float(t), 'name': name, 'gain_db': gain_db, 'pan': pan}
    if space:
        e['space'] = space
    if params:
        e['params'] = params
    return e


def L(i, end=False, off=0.0):
    return MP.resolve(('e' if end else 's') + str(i), LINES) + off


TL_J = json.load(open(TL))
LINES = TL_J['lines']

TESTS = {}


def test(fn):
    TESTS[len(TESTS) + 1] = fn
    return fn


@test
def t01_doorbell_3am():
    """3:07: the phone lights up, 'Your package has been delivered', the house ding-dong, the app chime, the camera."""
    a, b = 25.5, 44.0
    return a, b, [
        ev(a, 'room_tone_house', dur=b - a), ev(a, 'ambience_suburb', dur=b - a, dog=0.0),
        ev(L(10, off=0.9), 'phone_notify'),                         # "your phone lights up"
        ev(L(13, off=0.15), 'doorbell_dingdong'),                   # "...when the doorbell rings" (the house chime)
        ev(L(13, off=0.25), 'doorbell_cam_chime', -2.0),            # and the doorbell app on your phone
        ev(L(14, off=0.5), 'touch_tap', n=2, spacing=0.22),         # you open the doorbell camera
        ev(L(14, off=1.4), 'hazard_ticks', -2.0, space='app', dur=b - L(14, off=1.4)),   # the camera's live audio
        ev(L(14, off=1.4), 'van_idle', -3.0, space='app', dur=b - L(14, off=1.4)),
    ]


@test
def t02_driver_through_doorbell():
    """The driver's lines through the doorbell camera ('doorbell' line fx), the app, RETURN."""
    a, b = 68.0, 99.5
    return a, b, [
        ev(a, 'room_tone_house', dur=b - a),
        ev(a, 'hazard_ticks', -1.0, space='app', dur=b - a), ev(a, 'van_idle', -2.0, space='app', dur=b - a),
        ev(a, 'ambience_suburb', -3.0, space='app', dur=b - a, dog=0.0),
        ev(L(31, off=0.3), 'touch_tap', n=2, spacing=0.25),         # you open the delivery app
        ev(L(33, off=-0.2), 'ui_pop', -4.0), ev(L(37, off=-0.05), 'phone_notify', -4.0, vibrate=False),
        ev(L(38, off=0.6), 'touch_tap', n=1),                       # you press the button on the doorbell
        ev(L(42, off=0.3), 'box_tap', -2.0, n=2),                   # (the driver taps the box)
    ]


@test
def t03_tablet_signature():
    """Rule 1: the tablet held up, your initial on the line, 'Just finish it', the stylus, the flickering timestamp."""
    a, b = 118.0, 141.0
    return a, b, [
        ev(a, 'room_tone_house', dur=b - a), ev(a, 'hazard_ticks', -2.0, space='app', dur=b - a),
        ev(L(52, off=0.6), 'touch_tap', -2.0, space='app', n=2),    # he taps the tablet awake
        ev(L(55, off=0.2), 'stylus_scribble', 0.0, dur=1.1),        # the half-written initial (the picture's ink)
        ev(L(57, off=1.6), 'stylus_scribble', -3.0, space='app', dur=0.5),
        ev(L(58, off=-0.2), 'touch_tap', -2.0, space='app'),
        ev(L(60, off=1.4), 'camera_shutter', -2.0),                 # (a photo flash on the tablet)
        ev(L(56, off=0.2), 'heartbeat', -6.0, bpm=64, bpm_end=80, dur=8.0),
    ]


@test
def t04_keys_bowl_hey_buddy():
    """Rule 3: 3:11, the keys set down in the bowl behind you, 'Hey, buddy' ('hall' fx), you don't turn round."""
    a, b = 229.0, 250.0
    return a, b, [
        ev(a, 'room_tone_house', 1.0, dur=b - a, clock=0.6),
        ev(L(107, off=2.4), 'footsteps_hall', -2.0, n=3, rate=1.4, approach=-0.6),
        ev(L(107, off=4.05), 'keys_drop', 0.0, surface='bowl'),      # "...down in the bowl"
        ev(L(110, off=-0.25), 'breath', -3.0, kind='held', dur=6.0),
        ev(L(110, off=-0.05), 'tinnitus', -6.0, dur=5.0),
    ]


@test
def t05_box_knocks_mar():
    """Rule 5: the box knocks two-then-one (low thump, through the door), mom's sound, 'Mar?' from inside the box."""
    a, b = 376.0, 404.0
    k0 = L(164, off=0.6)
    out = [ev(a, 'room_tone_house', dur=b - a), ev(a, 'box_voice', dur=b - a, space='box', gain_db=-2.0)]
    out.append(ev(k0, 'box_knock', 0.0, pattern=[2, 1], strength=1.0))     # "Then the box knocks."
    for t, g, nip, grp in ((L(167, off=0.05), 0.0, 1, 1), (L(167, off=0.35), -1.0, 2, 1), (L(169, off=0.0), 0.0, 1, 2)):
        out.append(ev(t, 'box_knock', g, n_in_pattern=nip, group=grp, strength=1.05))
    out += [ev(L(170, off=1.0), 'mom_sob', -2.0, dur=2.5, intensity=0.6),
            ev(L(179, off=0.3), 'mom_breath', -1.0, kind='gasp'),
            ev(L(179, off=0.6), 'mom_breath', -4.0, kind='shaky', dur=2.0),
            ev(L(173, end=True, off=-0.15), 'box_creak', 3.0, space='outside', dur=0.8)]   # the box shifts: "Mar?"
    return a, b, out


@test
def t06_box_left_driver_leaves():
    """Rule 6: the box set against the door, the scrape across the welcome mat, the photo, the walk back, the van."""
    a, b = 460.5, 472.5
    return a, b, [
        ev(a, 'room_tone_house', dur=b - a), ev(a, 'ambience_suburb', -2.0, dur=b - a, space='outside'),
        ev(a, 'hazard_ticks', 0.0, space='outside', dur=b - a), ev(a, 'van_idle', 0.0, space='outside', dur=b - a),
        ev(L(206, off=1.3), 'box_drop', 0.0, space='outside'),
        ev(L(207, off=0.1), 'box_scrape', 0.0, space='outside', dur=1.0),    # "You hear it scrape across the mat"
        ev(L(208, off=1.2), 'camera_shutter', -2.0, space='outside'),
        ev(L(209, off=0.3), 'footsteps_porch', -1.0, n=6, approach=-1.0),
        ev(L(209, off=2.6), 'van_step', 0.0, space='street'),
        ev(L(209, off=3.0), 'car_door_close', -2.0, space='street'),
        ev(L(210, off=0.3), 'phone_notify', -2.0),                     # "The app updates."
    ]


@test
def t07_lily_room():
    """Rule 7: up the stairs two at a time, the door open a crack, the window wide open, the curtains, the phone."""
    a, b = 526.5, 553.0
    return a, b, [
        ev(a, 'room_tone_house', 0.0, dur=b - a),
        ev(L(235, off=0.2), 'footsteps_stairs', 0.0, direction='up', n=7, rate=3.2, weight=0.8),
        ev(L(236, off=1.2), 'footsteps_hall', -1.0, n=4, rate=2.4, approach=0.4),
        ev(L(241, off=0.4), 'door_creak', -3.0, dur=1.2),             # you push the door open
        ev(L(242, off=0.0), 'ambience_suburb', 2.0, dur=b - L(242), space='window', dog=0.2, wind=0.8),
        ev(L(242, off=0.0), 'hazard_ticks', 0.0, space='window', dur=b - L(242)),
        ev(L(243, off=-0.4), 'curtain_flutter', 0.0, dur=b - L(243) + 0.4, wind=0.8),
        ev(L(245, off=0.3), 'phone_vibrate', -2.0, n=1),              # your phone buzzes in your hand
        ev(L(246, off=-0.05), 'phone_notify', -2.0, vibrate=False),
        ev(L(244, off=0.5), 'breath', -4.0, kind='nervous', dur=4.0),
    ]


def test8_cues():
    """The ending through mix.py: 588 s (the hazards stop) to the end card."""
    a = 586.0
    hz_off = L(261, off=2.0)
    sfx = [
        ev(a, 'ambience_suburb', 0.0, dur=L(263) - a + 2.0, space='window'),
        ev(a, 'hazard_ticks', 0.0, space='window', dur=hz_off - a + 0.5, t_off=hz_off),
        ev(a, 'van_idle', 0.0, space='window', dur=L(262, off=1.0) - a),
        ev(L(262, off=0.6), 'van_pull_away', 0.0, space='window', dur=6.5),
        ev(L(263), 'ambience_dawn', 0.0, dur=L(274) - L(263) + 1.0),
        ev(L(264, off=0.6), 'chain_lock', -4.0, action='unlock'),
        ev(L(264, off=1.2), 'door_creak', -2.0, dur=1.5),
        ev(L(266, off=0.2), 'box_open', 0.0, keys=True),              # "The tape has been cut." / the keys
        ev(L(268, off=0.5), 'keys_drop', -6.0, surface='carpet', rust=True),
        ev(L(274), 'room_tone_house', -1.0, dur=24.0),
        ev(L(274, off=2.6), 'phone_notify', 0.0),                     # "your phone lights up again"
        ev(L(277, off=0.2), 'touch_tap', -2.0, n=2),
        ev(L(281, off=0.5), 'ambience_suburb', 0.0, dur=10.0, space='outside', dog=0.0),
        # Lily's knock: small knuckles, two, a pause, one (far down the street, then at the door)
        ev(L(283, off=0.05), 'box_knock', -3.0, space='outside', strength=0.7, n_in_pattern=1, group=1),
        ev(L(283, off=0.33), 'box_knock', -4.0, space='outside', strength=0.65, n_in_pattern=2, group=1),
        ev(L(285, off=0.0), 'box_knock', -2.0, space='outside', strength=0.75, n_in_pattern=1, group=2),
        # fallback checks (must warn, not crash): an alias, a keyword guess, an unknown space, a name nothing fits
        ev(L(270), 'house_tone', -40.0, dur=1.0), ev(L(270, off=0.5), 'box_rattle', -40.0),
        ev(L(271), 'touch_tap', -40.0, space='the_moon'), ev(L(271, off=0.5), 'zzz_not_a_sound', 0.0),
    ]
    return sfx


def render_window(a, b, cues, who_fx=WHO_FX):
    n = int(round((b - a) * SR))
    v, sr = sf.read(VO, dtype='float32', start=int(a * SR), stop=int(a * SR) + n)
    v = v.mean(1) if v.ndim > 1 else v
    v = np.pad(v, (0, max(0, n - len(v))))
    fx_of = lambda l: l.get('fx') or who_fx.get(l.get('who'))
    spans = [(l['t'] - a, l['end'] - a, fx_of(l)) for l in LINES if fx_of(l) and l['end'] > a and l['t'] < b]
    v = MX.apply_line_fx(v, spans)
    full_l = GAIN_VO
    v = v * np.float32(10 ** ((-14.0 - full_l) / 20))
    bus = np.zeros((n, 2), np.float32)
    SX.reset()
    log = []
    vm = -0.691 + 10 * np.log10(SX._blocks(SX.st(v), 0.4, 0.05) + 1e-20)     # the voice's momentary loudness
    for k, c in enumerate(sorted(cues, key=lambda c: c['t'])):
        name, params, note = SX.resolve(c['name'], c.get('params') or {})
        sp = c.get('space')
        if name in SX.TIMED:
            params.setdefault('cue_t', c['t'])
        y, pre = SX.render_event(name, seed=k + 1, space=sp, **params)
        y = y * 10 ** (c.get('gain_db', 0.0) / 20)
        if c.get('pan'):
            y = SX.pan(y, c['pan'])
        SX.place(bus, y, int(round((c['t'] - a - pre) * SR)))
        bed = name in SX.BEDS or (name in SX.DUR_BEDS and 'dur' in params)
        L_ = SX.lufs_int(y) if (name in SX.BEDS or name in SX.DUR_BEDS) else SX.mom_max(y)
        ent = {'t': round(c['t'], 2), 'name': c['name'], 'resolved': name, 'space': sp or SX.DEFAULT_SPACE[name],
               'gain_db': c.get('gain_db', 0.0), 'params': c.get('params'), 'dur': round(len(y) / SR, 2),
               'loud_rel_voice_LU': round(L_ + 14.0, 1)}
        if not bed:                                    # listening checks by measurement (one-shots)
            j0 = max(0, int((c['t'] - a) / 0.05)); j1 = j0 + max(1, int(min(len(y) / SR - pre, 1.0) / 0.05))
            Mm = SX.mom_max(y)
            ent['check'] = {
                'transient_ms': round(1000 * (SX.onset_s(y, -12) - pre)),           # loudest transient vs cue time
                'phone_band_db': round(SX.mom_max(SX.hp(SX.hp(y, 300, 2), 300, 2)) - Mm, 1),   # left above 300 Hz
                'vs_voice_here_LU': round(Mm - float(vm[j0:j1].max()), 1) if j0 < len(vm) else None}
        log.append(ent)
    mixd = bus + np.stack([v, v], 1)
    y, gr, _f = MX.tp_limit(mixd, -1.0)
    ck = [e for e in log if 'check' in e]
    flags = [f"{e['t']} {e['resolved']}: " + ', '.join(
        w for w, bad in ((f"transient {e['check']['transient_ms']} ms off the cue", abs(e['check']['transient_ms']) > 40
                          and not (e.get('params') or {}).get('jingle') and e['resolved'] not in SLOW_ONSET),
                         (f"{e['check']['phone_band_db']} dB above 300 Hz (thin on a phone)", e['check']['phone_band_db'] < -15),
                         (f"{e['check']['vs_voice_here_LU']} LU under the voice there (masked)",
                          (e['check']['vs_voice_here_LU'] or 0) < -20)) if bad)
             for e in ck]
    return y, log, {'voice_lufs': round(SX.lufs_int(np.stack([v, v], 1)), 1), 'sfx_lufs': round(SX.lufs_int(bus), 1),
                    'mix_lufs': round(SX.lufs_int(y), 1), 'true_peak': round(float(MX.true_peak(y)), 1),
                    'limiter_gr_db': round(gr, 1), 'flags': [f for f in flags if not f.endswith(': ')]}


def run_test8():
    name = '08_ending_full_mix'
    cdir = os.path.join(OUT, 'cues_t8'); os.makedirs(cdir, exist_ok=True)
    json.dump(test8_cues(), open(os.path.join(cdir, 'sfx_cues.json'), 'w'), indent=0)
    film_mc = os.path.join(W, 'cues', 'music_cues.json')       # the director's picture-derived music cues
    if os.path.exists(film_mc):
        mc = json.load(open(film_mc)); mc.pop('track_map', None); msrc = 'film.py music_cues.json + mix.py --plan auto'
    else:
        mc = MP.music_cues(LINES, TL_J['duration_en'] + 2.5); msrc = 'music_plan.music_cues()'
    json.dump(mc, open(os.path.join(cdir, 'music_cues.json'), 'w'), indent=0)
    odir = os.path.join(OUT, 'mix_t8')
    cmd = [sys.executable, os.path.join(HERE, 'mix.py'), TL, VO, '-', cdir, odir, '--t0', '586', '--langs', 'en',
           '--who-fx', 'X=hall', '--no-stems']
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    open(os.path.join(OUT, name + '.log'), 'w').write(r.stdout + '\n' + r.stderr)
    if r.returncode != 0:
        print(r.stdout[-3000:], r.stderr[-3000:]); raise SystemExit('test 8 failed')
    os.replace(os.path.join(odir, 'mix_en.wav'), os.path.join(OUT, name + '.wav'))
    rep = json.load(open(os.path.join(odir, 'mix_report.json')))
    json.dump({'cues': os.path.join(cdir, 'sfx_cues.json'), 'music': msrc, 'report': rep,
               'seconds': round(time.time() - t0, 1)},
              open(os.path.join(OUT, name + '.json'), 'w'), indent=1)
    print(name, json.dumps(rep['langs']['en']), 'fallbacks:', rep.get('sfx_fallbacks'), 'skipped:', rep.get('sfx_skipped'))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    which = [int(x) for x in sys.argv[1:]] or list(range(1, 9))
    if any(k <= 7 for k in which):
        vfull, _ = sf.read(VO, dtype='float32')
        GAIN_VO = SX.lufs_int(SX.st(vfull.mean(1) if vfull.ndim > 1 else vfull)); del vfull
    for k in which:
        if k == 8:
            run_test8(); continue
        fn = TESTS[k]
        a, b, cues = fn()
        t0 = time.time()
        y, log, meas = render_window(a, b, cues)
        name = fn.__name__[1:]
        sf.write(os.path.join(OUT, name + '.wav'), y, SR, subtype='PCM_24')
        json.dump({'film_window': [a, b], 'about': fn.__doc__, 'measure': meas, 'cues': log},
                  open(os.path.join(OUT, name + '.json'), 'w'), indent=1)
        print(f'{name}: {b - a:.1f} s {meas} in {time.time() - t0:.1f} s', flush=True)
