"""Bunnyman film sound tests: 8 renders in W/mix/tests/ (W = film/_work), each through the whole pipeline: mix.py on a
window of the film (the narration with its line voicing: door / slot / memory / whisper; this test's SFX cue sheet;
the score with music_plan.py's full plan: the dark track map, the tension events and the film's identity, the
ORIGINAL Pemberton's jingle in its versions), as the final mix will run it.

    python3 sfx_tests.py [1 2 ... 8] [--jobs 1]     (default: all, one mix at a time: the machine is shared)
    python3 sfx_tests.py --sheet                     W/mix/tests/tests_sheet.png: every test's spectrogram (cues marked,
                                                     identity spans shaded) over its 1 s voice / music / SFX / jingle profile

    1 cold_open          0-47        the night at the treeline, the three warnings, a tape glitch into the 1987 VHS
                                     commercial under the narrator's own "Hop, hop, hop along..." (every word on its
                                     note), the tape stopping, "humming it ever since" (Mom's hum), the seven rules
    2 song_from_woods    196-258     rule 1: "At 11:07, the song starts. From the woods." -- the dying speaker far
                                     across the yard, the curtains, running upstairs, June at her open window, the owl,
                                     he waves back, the song dies as he stops waving, he points, the board behind us,
                                     Mom in the doorway, "I told you not to look at the treeline." ('door' off)
    3 egg_and_ring       285-358     rule 2: one soft tap, the peephole, the egg on the mat, the burn barrel (oven
                                     mitts, the fire, the plastic melting), the rattle, the door, the egg opened, the
                                     ring rolling, "You opened it.", Mom on the stairs, the ring taken, the pocket
    4 family_knock       366-416     rule 3: the 2-3-2 knock on the jingle's beat in the narration's gaps, "Seven.",
                                     Grandma remembered ('memory' voice, her table knock, her music box), "Two. Three.
                                     Two." recalled, the secret knock
    5 slot_and_cry       424-499     rule 4: the brass flap creaking open, "Mama?" through the slot ('slot' voice),
                                     June in her socks on the stairs, "Is she humming?" "Yeah.", the real Laurie
                                     trying to sing the jingle and crying through the slot, the flap snapped shut,
                                     "Bedtime, bunny.", Mom humming
    6 window_to_lock     598-618     rule 6: the kitchen window explodes, the back door crashes in, something heavy,
                                     wet, dragging; I grab June and run; the bathroom door, the lock, the empty tub
    7 hatchet_and_fight  615-698     the slow steps up the stairs with the hatchet knocking every step ("Thunk.
                                     Thunk."), the doorknob, the girl under the door ('door' voice), the drawing slid
                                     under it, GET OUT OF MY HOUSE / IT'S MY HOUSE, the hallway shaking, the slam on
                                     the door, the wet heavy crack, then nothing, Mom softly
    8 climax_count       768-917     Mom kneels with the yellow dress, "Close your eyes. And count to seven." on the
                                     minor music box, One / Two / Three on the count's scale, the reveal, Four / Five,
                                     the swap, Six / Seven -> cut to silence; plus the fallback checks (an alias, a
                                     keyword guess, an unknown space, a name nothing fits, bad params / time / gain:
                                     warn, never crash)

Each test writes <name>.wav (the mix of the window, 48 kHz 24-bit) and <name>.json: the cue sheet, mix.py's report
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
              'music_box_wind', 'dogs_search', 'zipper', 'curtain_close', 'slot_flap', 'struggle', 'bathtub')
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


def house(a, b, tone=True, creaks=True, clock=False):
    out = []
    if tone:
        out.append(ev(a, 'room_tone_house', 0.0, dur=round(b - a, 2), hum=0.25))
    if creaks:
        out.append(ev(a, 'house_creaks', -2.0, dur=round(b - a, 2), density=0.08))
    if clock:
        out.append(ev(a, 'old_clock', -3.0, dur=round(b - a, 2), bpm=60))
    return out


@test
def t01_cold_open():
    a, b = 0.0, 47.0
    return a, b, [
        ev(0.0, 'ambience_woods', 2.0, 'porch', dur=17.6, owl=0.7, wind=0.5, crickets=0.6),
        ev(5.6, 'owl_hoot', -2.0, 'woods', pan=-0.4),
        ev(17.05, 'tape_glitch', 2.0, 'tv', kind='tracking', dur=0.35),           # into the 1987 tape
        ev(A('s7') + 1.55, 'tape_glitch', -5.0, 'tv', kind='stop', dur=0.7),       # the tape stops: back to the night
        ev(A('s7') + 1.9, 'ambience_woods', 0.0, 'window', dur=round(b - A('s7') - 1.9, 2), owl=0.4, wind=0.4),
    ] + house(A('s7') + 1.9, b, creaks=False)


@test
def t02_song_from_woods():
    a, b = 196.0, 258.2
    open_w = A('s70')                                                              # June's window is open
    return a, b, house(a, b) + [
        ev(a, 'ambience_woods', 0.0, 'outside', dur=round(open_w - a + 0.5, 2), owl=0.3, wind=0.4),
        ev(open_w, 'ambience_woods', 2.0, 'window', dur=round(b - open_w, 2), owl=0.6, wind=0.5),
        ev(A('w69:curtains') + 0.1, 'curtain_close', 0.0, dur=1.1),                # "I close the curtains downstairs"
        ev(A('w69:curtains') + 1.6, 'curtain_close', -2.0, dur=0.9, pan=0.4),
        ev(A('w69:run') + 0.05, 'footsteps_wood_inside', -2.0, stairs=True, run=True, direction='up', n=7),
        ev(open_w - 0.6, 'door_creak', -4.0, dur=1.0),                             # June's door
        ev(A('s73') + 0.8, 'owl_hoot', -3.0, 'woods', pan=0.5),
        ev(A('s87') - 0.35, 'wood_creak', -4.0, 'inside', kind='creak', dur=0.6),   # the board behind us
    ]


@test
def t03_egg_and_ring():
    a, b = 285.0, 358.5
    tap = A('w104:tap')
    rattle = A('w114:rattles')
    return a, b, house(a, b, clock=True) + [
        ev(a, 'ambience_woods', -2.0, 'outside', dur=round(A('s109') - a, 2), owl=0.3, wind=0.3),
        ev(tap + 0.05, 'egg_tap', 0.0),                                             # "...one soft tap on the front door."
        ev(A('s105') + 0.35, 'peephole', 0.0),                                      # "Through the peephole"
        # the memory: every Easter, the burn barrel in the backyard
        ev(A('s109') - 0.2, 'ambience_woods', -4.0, 'porch', dur=round(A('s113') - A('s109'), 2), owl=0.2),
        ev(A('w109:carries') + 0.1, 'oven_mitt', -2.0, dur=1.4),
        ev(A('w109:fire') - 0.4, 'burn_barrel', 2.0, dur=round(A('s113') - A('w109:fire') + 0.6, 2), ignite=True),
        ev(A('s112') + 0.3, 'plastic_melt', 2.0, dur=2.6),                          # "They smell sweet when they melt."
        ev(A('s113'), 'ambience_woods', -2.0, 'outside', dur=round(b - A('s113'), 2), owl=0.3, wind=0.3),
        ev(rattle + 0.12, 'egg_rattle', 2.0, 'outside', dur=1.5),                   # "...the egg rattles."
        ev(A('s116') + 0.25, 'door_creak', -2.0, dur=1.4, slow=1.3),                # "I open the door."
        ev(A('s117') + 0.1, 'chain_lock', -6.0, kind='rattle'),                     # "Just a crack."
        ev(A('w118:egg') + 0.05, 'egg_open', 2.0),                                  # "And I open the egg."
        ev(A('w119:rolling'), 'ring_roll', 2.0, dur=2.0),                           # "Inside, rolling around..."
        ev(A('s126') + 0.2, 'footsteps_wood_inside', -4.0, stairs=True, direction='down', n=6, rate=1.4),
        ev(A('w127:takes') + 0.05, 'ring_hand', 0.0, kind='take'),                  # "takes the ring out of my hand"
        ev(A('w129:pocket'), 'ring_hand', 2.0, kind='pocket'),                      # "She puts it in her pocket."
    ]


@test
def t04_family_knock():
    a, b = 366.0, 416.3
    # the knock's three groups sit in the narration's gaps, each group on the jingle's beat (0.476 s quarter)
    g1 = A('e135') + 0.08; g2 = A('e137') + 0.03; g3 = A('e139') + 0.02
    t0 = g1
    mem = A('s147')
    return a, b, house(a, b, clock=True) + [
        ev(a, 'ambience_woods', -4.0, 'outside', dur=round(b - a, 2), owl=0.2, wind=0.3),
        ev(t0, 'knock_family', 2.0, 'inside', groups=[0.0, round(g2 - t0, 3), round(g3 - t0, 3)]),
        # Grandma remembered: she taps the family knock on her kitchen table (soft, memory)
        ev(A('w147:knock') + 0.35, 'knock_family', -2.0, 'close', soft=True, memory=True, beat=0.42),
        # "Two. Three. Two." -- recalled in my head: the knock again, soft, far, on the words
        ev(A('s155') - 0.05, 'knock_family', 0.0, 'inside', soft=True,
           groups=[0.0, round(A('s156') - A('s155'), 3) - 0.45, round(A('s157') - A('s155'), 3) - 0.48]),
    ]


@test
def t05_slot_and_cry():
    a, b = 424.0, 499.0
    return a, b, house(a, b, clock=True) + [
        ev(a, 'ambience_woods', -4.0, 'outside', dur=round(b - a, 2), owl=0.2, wind=0.3),
        ev(A('w164:creaks') - 0.2, 'slot_flap', 0.0, action='open'),                # the brass flap creaks open
        ev(A('s180') + 1.4, 'footsteps_stairs', -6.0, direction='down', n=6, rate=1.2, weight=0.3),   # in her socks
        ev(A('w180:kneels'), 'cloth_rustle', -4.0, kind='rustle'),
        ev(A('s192') + 0.35, 'slot_flap', 2.0, action='snap'),                      # "Mom closes the mail slot."
        ev(A('w193:smooths'), 'cloth_rustle', -2.0, kind='rustle'),
    ]


@test
def t06_window_to_lock():
    a, b = 597.5, 618.0
    return a, b, house(a, b, creaks=False) + [
        ev(a, 'ambience_woods', -4.0, 'outside', dur=round(b - a, 2), owl=0.0, wind=0.4),
        ev(A('w236:explodes'), 'window_smash', 0.0),                               # "the kitchen window explodes."
        ev(A('w237:crashes'), 'door_crash', 0.0),                                   # "The back door crashes open."
        ev(A('s238') + 0.2, 'wet_drag', 0.0, dur=round(A('e240') - A('s238') + 0.6, 2)),   # heavy... wet... dragging
        ev(A('s241') + 0.35, 'cloth_rustle', -2.0, kind='grab'),                    # "I grab June"
        ev(A('w241:run'), 'footsteps_wood_inside', 0.0, run=True, n=6),             # "and run."
        ev(A('s242') + 0.35, 'attic_door', -2.0, 'close', action='close'),          # the bathroom door shut
        ev(A('s243') + 0.05, 'lock_turn', 2.0, 'close'),                            # "Lock."
        ev(A('s244') + 1.2, 'bathtub', 0.0, kind='settle'),                         # in the empty bathtub
        ev(A('w244:hand') + 0.1, 'breath', -6.0, kind='held', dur=2.0),             # my hand over her mouth
    ]


@test
def t07_hatchet_and_fight():
    a, b = 615.0, 698.0
    th1, th2 = A('s248'), A('s249')                                                # "Thunk." "Thunk."
    shake, slam, crack = A('s270'), A('s271') + 1.0, A('w273:crack')
    return a, b, [
        ev(a, 'room_tone_house', -2.0, 'bathroom', dur=round(b - a, 2), hum=0.2),
        ev(A('s245') + 0.3, 'hatchet_step', 0.0, n=4, rate=0.8),                    # "Footsteps on the stairs. Slow."
        ev(th1 - 0.3, 'hatchet_step', 2.0, n=1),                                    # the Thunk lands on the word
        ev(th2 - 0.3, 'hatchet_step', 2.0, n=1),
        ev(A('s250') + 0.6, 'hatchet_step', 0.0, n=2, rate=0.8),
        ev(A('w251:turns') - 0.2, 'doorknob', 2.0, kind='turn'),                    # "The doorknob turns. Gently."
        ev(A('s257') + 0.35, 'paper_under_door', 2.0, dur=1.3),                     # "Something slides under the door."
        ev(shake, 'struggle', 0.0, kind='shake'),                                   # "The whole hallway shakes."
        ev(slam, 'struggle', 2.0, kind='slam'),                                     # "Something slams into the bathroom door."
        ev(A('s272'), 'struggle', -4.0, kind='wall'),                               # "Screaming."
        ev(crack + 0.05, 'struggle', 0.0, kind='crack'),                            # "A wet, heavy crack."
    ]


@test
def t08_climax_count():
    a, b = 768.0, 917.0
    return a, b, house(a, b, creaks=False) + [
        ev(a, 'ambience_dawn', -8.0, 'window', dur=round(A('s322') - a, 2), birds=0.4),
        ev(A('w313:kneels'), 'cloth_rustle', -4.0, kind='rustle'),                  # Mom kneels with the dress
        ev(A('w313:hand') + 0.2, 'cloth_rustle', -8.0, kind='rustle'),              # her hand over June's eyes
        ev(A('w355:pull'), 'cloth_rustle', 0.0, kind='grab'),                       # I pull June's face out
        ev(A('w355:push') + 0.1, 'cloth_rustle', -2.0, kind='grab'),                # and push my own face into it
        # fallback checks (must warn, not crash): an alias, a keyword guess, an unknown space, a name nothing fits,
        # params that are not a dict, a cue without a time, a gain that is not a number, a space that is not a name
        ev(a + 1.0, 'secret_knock', -40.0), ev(a + 1.2, 'creepy_owl_call', -40.0),
        ev(a + 1.4, 'egg_tap', -40.0, space='the_moon'), ev(a + 1.6, 'zzz_not_a_sound', 0.0),
        {'t': a + 1.8, 'name': 'ring_drop', 'gain_db': -40.0, 'params': [1, 2]},
        {'name': 'egg_open', 'gain_db': 0.0}, {'t': a + 2.0, 'name': 'peephole', 'gain_db': 'loud'},
        {'t': a + 2.2, 'name': 'page_flip', 'gain_db': -40.0, 'space': {'x': 1}},
    ]


# ------------------------------------------------------------------------------------------------- measurement
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
            if e['type'] not in ('show', 'winks', 'jingle') or e['t'] + e.get('len', 0) < a or e['t'] > b:
                continue
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
