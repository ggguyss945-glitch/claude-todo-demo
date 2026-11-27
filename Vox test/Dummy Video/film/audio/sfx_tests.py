"""Dummy film sound tests: 8 renders in W/mix/tests/ (W = film/_work), each through the whole pipeline: mix.py on a
window of the film (the narration with its line voicing, this test's SFX cue sheet, the score with music_plan.py's
full plan: the dark track map, the tension events and the film's identity, the show theme on the TV and Mister Winks's
rotting theme), as the final mix will run it.

    python3 sfx_tests.py [1 2 ... 8] [--jobs 2]     (default: all, two mixes at a time)

    1 case_coffee        147-199.5   the latches, the empty case, the warm velvet, the spoon from the kitchen, "Clink.
                                     Clink. Clink.", Mister Winks in Grandpa's chair, the mug, two sugars
    2 upstairs_kiddo     214.5-262.5 Mom's voice and your voice from upstairs ('upstairs'), "See you in the morning,
                                     kiddo" from the kitchen ('dummy'), the 180-degree head turn, the jaw, the slow clack
    3 joke_laughtrack    268-335     the joke ('dummy'), the snort, the clack, the glove, the TV and the VCR turning on,
                                     the show theme on the TV, the studio laughter swelling as he moves and stands, the
                                     lamp, the empty chair, the flashlight, the little steps down the hall
    4 hand_inside        350.5-410   3 AM, the flashlight on the stairs, the hand through the slot, a warm hand, the
                                     three squeezes, the paper, "Kiddo, it's me" ('dummy'), the jaw clacks shut
    5 tape_cry           432-472.5   the TV: young Grandpa's lips, the tape stops, the dummy looks into the camera and
                                     cries ('tv'), the studio audience laughs
    6 owens_goodnight    551.5-583   "Say goodnight, Mister Winks", the head turn, click, the wink, "Goodnight, Owen."
                                     in near silence + the low hit, the lamp out, "It worked!", face down on the rug
    7 blink_click        652.5-668   in your arms he opens his eyes, tries to wink: both eyelids close, click, click
    8 ending             663-end     the museum van, the window, the glass case, the sting, coffee with two sugars,
                                     "See you in the morning, kiddo.", the end; plus the fallback checks (an unknown
                                     name, a keyword guess, an unknown space, a bad params / time / gain: warn, no crash)

Each test writes <name>.wav (the mix of the window, 48 kHz 24-bit) and <name>.json: the cue sheet, mix.py's report
and the measurements:
    per one-shot SFX cue (rendered alone with the same seed): transient_ms (its loudest transient vs the cue time: the
    picture's sync), phone_band_db (loudness left above 300 Hz: what a phone speaker plays), vs_voice_LU (the cue's
    momentary max vs the narration's there), vs_music_LU (vs the music stem there: does it read over the score)
    per identity event (the show theme / the Winks theme, from stems/score_show.wav): its 1 s loudness median vs the
    voice's integrated level, and its share of energy in the voice band (1-4 kHz)
    flags: a cue more than 40 ms off, thinner than -15 dB on a phone, more than 20 LU under the voice (his per-word
    'speech' jaw ticks: 26) or 12 LU under the music; an identity layer more than 24 LU under the voice
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
# no single transient to sync (beds, breaths, cloth, creaks, slides, swells, laughter waves): not sync-checked
SLOW_ONSET = ('breath', 'mom_breath', 'mom_sob', 'cloth_rustle', 'riser', 'whoosh', 'door_creak', 'wood_creak', 'velvet',
              'spoon_stir', 'hand_slot', 'studio_laugh', 'applause', 'owen_cry', 'owen_giggle', 'tv_on', 'vcr',
              'lamp_flicker', 'car_pass', 'van_pull_away', 'paper', 'paper_slide', 'case_lid', 'glove_lift', 'sip',
              'snort', 'heart_monitor', 'tape_glitch', 'winks_laugh', 'footsteps_hall', 'tiny_steps', 'keys_jangle',
              'hand_squeeze', 'mom_scream')
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


def speech_clacks(i, space='tight', gain=-11.0, every=1):
    """The light jaw clacks while the dummy talks: one per word of line i (as characters.Winks.talk emits them on
    every snap shut), a little after the word's onset."""
    l = LINES[i]
    ws = [t for w, t in WORDS if l['t'] - 0.05 <= t <= l['end']]
    return [ev(t + 0.12, 'dummy_clack', gain + float(np.random.default_rng(int(t * 100)).uniform(-3, 2)), space,
               kind='speech') for k, t in enumerate(ws) if k % every == 0]


def beds(a, b, house=True, clock=True, creaks=True, tone_gain=0.0):
    out = []
    if house:
        out.append(ev(a, 'room_tone_house', tone_gain, dur=round(b - a, 2), hum=0.2))
    if clock:
        out.append(ev(a, 'old_clock', 0.0, dur=round(b - a, 2), bpm=60))
    if creaks:
        out.append(ev(a, 'house_creaks', 0.0, dur=round(b - a, 2), density=0.1))
    return out


@test
def t01_case_coffee():
    a, b = 147.0, 199.5
    return a, b, beds(a, b) + [
        ev(a, 'ambience_night', -6.0, 'window', dur=b - a, dog=0.0, wind=0.4, buzz=0.0),
        ev(152.05, 'case_latch', -2.0, pan=-0.15), ev(152.33, 'case_latch', -2.0, pan=0.15),     # "She pops the latches"
        ev(153.0, 'case_lid', -2.0, action='open'),
        ev(A('s62') + 0.1, 'velvet', 2.0, dur=1.2),                    # "And the velvet is still warm."
        ev(161.85, 'spoon_stir', 2.0, 'next_room', dur=3.0),           # "From the kitchen, there's a sound."
        ev(164.94 - 0.14, 'spoon_clink', 2.0, 'next_room', times=[0.0, 165.998 - 164.94, 166.638 - 164.94]),
        ev(A('s68') + 1.5, 'wood_creak', -10.0, 'next_room', kind='tick', dur=0.15),   # sitting up straight
        ev(A('w71:picks') + 0.1, 'mug_set', -2.0, kind='pickup'),     # Mom picks it up
        ev(A('w71:smells') + 0.05, 'breath', -12.0, kind='sniff'),     # and smells it
        ev(A('w71:smells') + 1.6, 'breath', -8.0, kind='gasp'),
        ev(A('e73') + 0.05, 'mug_set', -3.0),                          # sets it down
    ]


@test
def t02_upstairs_kiddo():
    a, b = 214.5, 262.5
    return a, b, beds(a, b) + [
        ev(219.9, 'footsteps_hall', -2.0, 'upstairs', n=3, rate=1.6),   # someone walking overhead before "Honey?"
        ev(A('w90:hand'), 'cloth_rustle', -8.0, kind='grab'),           # "Her hand finds yours."
        ev(228.7, 'footsteps_hall', -3.0, 'upstairs', n=2, rate=1.4),
        ev(A('w104:mouth') - 0.4, 'cloth_rustle', -4.0, kind='grab'),   # Mom's hand flies to her mouth
        ev(A('w104:mouth') - 0.3, 'breath', -8.0, kind='gasp'),
        ev(A('s106') + 0.4, 'cloth_rustle', -6.0, kind='rustle'),       # she starts to stand up
        ev(A('s107') + 0.3, 'cloth_rustle', -4.0, kind='grab'),         # you pull her back down
        ev(A('s108') - 2.6, 'wood_creak', -4.0, 'next_room', kind='grind', dur=3.2),   # the head turning, 180 degrees
        ev(A('s109') + 0.1, 'dummy_jaw', -6.0, 'next_room', kind='drop'),
        ev(A('w111:clack'), 'dummy_clack', 0.0, 'tight', kind='slow'),  # "Clack."
    ] + speech_clacks(103, 'next_room')


@test
def t03_joke_laughtrack():
    a, b = 268.0, 335.0
    tv = A('s132')
    stand = A('w140:stands')
    return a, b, beds(a, 296.0, creaks=False) + beds(326.0, b, clock=False) + [
        ev(A('s124') + 0.05, 'snort', 0.0),                            # "Owen snorts."
        ev(A('w127:clack'), 'dummy_clack', 0.0, 'next_room', kind='snap'),   # "Clack."
        ev(A('w128:lifts'), 'cloth_rustle', -14.0, 'next_room', kind='glove'),
        ev(A('w128:lifts') + 0.03, 'wood_creak', -10.0, 'next_room', kind='tick', dur=0.15),
        ev(A('s129') + 0.3, 'cloth_rustle', -2.0, kind='grab'),        # you clamp a hand over Owen's mouth
        ev(tv, 'tv_on', 0.0),                                          # "Then the TV turns on by itself."
        ev(A('s133') + 0.2, 'vcr', -2.0, action='play'),               # the tape in Grandpa's old VCR
        ev(tv + 0.3, 'tape_hiss', 0.0, dur=round(A('s143') + 0.05 - tv - 0.3, 2)),
        ev(A('s135') + 0.3, 'studio_laugh', 0.0, size='medium'),       # "a studio audience is laughing"
        ev(A('s136') + 0.2, 'studio_laugh', 2.0, size='huge', swell=1.5),   # "A huge, roaring wave of laughter"
        ev(A('s138') + 0.3, 'studio_laugh', -1.0, size='medium', align='peak'),   # his fingers curl
        ev(A('s138') + 0.35, 'wood_creak', -8.0, 'next_room', kind='tick', dur=0.2),
        ev(A('s139') + 0.4, 'studio_laugh', 0.0, size='medium', align='peak'),    # his elbow bends
        ev(A('s139') + 0.45, 'wood_creak', -6.0, 'next_room', kind='tick', dur=0.25),
        ev(A('s140') + 0.2, 'studio_laugh', 3.0, size='huge', swell=2.5),         # "The audience roars"
        ev(A('w140:hands') + 0.15, 'wood_knock', -4.0, 'next_room', n=2, spacing=0.12),   # both hands flat on the table
        ev(stand - 0.2, 'wood_creak', -4.0, 'next_room', kind='creak', dur=0.8),        # stands up on the chair
        ev(stand + 0.6, 'wood_knock', -3.0, 'next_room', n=2, spacing=0.2, size=1.2),
        ev(A('s143'), 'lamp_flicker', 0.0, dur=1.15, times=[0.0, 0.07, 0.16, 0.22, 0.31, 1.15]),
        ev(A('w145:clicks'), 'flashlight_click', -6.0, 'next_room', kind='on'),
        ev(A('s147') + 0.1, 'tiny_steps', 0.0, 'inside', n=8, rate=2.8, approach=-1.0),   # moving slowly down the hall
    ]


@test
def t04_hand_inside():
    a, b = 350.5, 410.0
    return a, b, beds(a, b) + [
        ev(A('s156') + 1.6, 'flashlight_click', -6.0, 'inside', kind='on'),   # the flashlight comes back
        ev(A('s156') + 1.7, 'flashlight_hum', 0.0, dur=round(A('s158') - A('s156'), 2)),
        ev(A('s158') + 0.1, 'cloth_rustle', -2.0, kind='grab'),        # "I grab him."
        ev(A('s158') + 0.15, 'wood_knock', -6.0, n=1),
        ev(A('s159') + 0.4, 'cloth_rustle', -10.0, kind='slot', dur=1.4),     # the hand through the slot
        ev(A('s161') + 0.6, 'wood_creak', -12.0, 'tight', kind='tick', dur=0.12),
        ev(A('w163:takes') + 0.2, 'hand_squeeze', -6.0),               # it takes hold of my hand
        # the three squeezes a beat BEFORE "Once." "Twice." "Three times." (the cast puts them on the words, where the
        # narration buries them: tests measured -20..-26 LU under the voice there)
        ev(374.60, 'hand_squeeze', -6.0), ev(375.56, 'hand_squeeze', -6.0), ev(376.36, 'hand_squeeze', -6.0),
        ev(A('w169:fingertips') + 0.2, 'paper', -10.0, dur=0.6),      # something folded, like paper
        ev(A('w184:pull') + 0.1, 'cloth_rustle', -10.0, kind='slot', dur=0.8),   # I pull my hand out
        ev(A('w185:clacks'), 'dummy_clack', 0.0, 'tight', kind='snap'),  # his jaw clacks shut
    ] + [c for i in range(172, 184) if LINES[i]['who'] == 'G' for c in speech_clacks(i, 'tight', -12.0, 2)]


@test
def t05_tape_cry():
    a, b = 432.0, 472.5
    return a, b, beds(a, b, clock=False) + [
        ev(a, 'tape_hiss', 2.0, dur=b - a),
        ev(A('w209:stops') + 0.15, 'tape_glitch', 0.0, kind='stop', dur=0.9),   # the tape stops mid-joke
        ev(A('s210') + 0.4, 'tape_glitch', -6.0, kind='tracking', dur=0.5),     # he turns to the camera
        ev(A('s218') + 0.05, 'studio_laugh', 3.0, size='huge', swell=0.6),       # "And the studio audience laughs."
        ev(A('s218') + 6.5, 'studio_laugh', -4.0, size='medium'),
    ]


@test
def t06_owens_goodnight():
    a, b = 551.5, 583.0
    return a, b, beds(a, b, creaks=False) + [
        ev(A('s260') + 0.1, 'cloth_rustle', -2.0, kind='grab'),        # I catch Mom's wrist
        ev(A('s262') + 0.3, 'cloth_rustle', -6.0, kind='rustle', dur=0.6),     # I kneel
        ev(A('s263') - 0.6, 'owen_cry', -4.0, kind='cry', dur=4.0),    # Owen is crying
        ev(A('w265:turns') - 0.1, 'wood_creak', -4.0, 'tight', kind='grind', dur=1.4),   # the head turns to Owen
        ev(A('w266:click') - 0.05, 'eyelid_click', -2.0, kind='shut'),  # "Click."
        ev(A('w266:click') + 0.37, 'eyelid_click', -8.0, kind='open'),  # "His eyelid winks."
        ev(A('e268') - 0.05, 'goodnight_hit', 0.0),                    # "Goodnight, Owen." lands
        ev(A('s271') + 0.05, 'lamp_out', 0.0, kind='out'),             # "The lamp goes out."
        ev(A('s272') + 0.1, 'lamp_out', 0.0, kind='on'),               # "When it comes back on"
        ev(A('w272:slides') + 0.1, 'cloth_rustle', -10.0, kind='slot', dur=0.9),   # slides his hand out
        ev(A('w272:jumps') + 0.1, 'footsteps_wood_inside', -4.0, n=2, run=True),   # jumps up
        ev(A('w272:jumps') + 0.8, 'dummy_thud', 0.0, kind='rug'),     # the dummy falls face down
        ev(A('w272:jumps') + 1.3, 'cloth_rustle', -4.0, kind='grab'),  # throws his arms around Mom
        ev(A('s275') + 0.2, 'cloth_rustle', -6.0, kind='grab'),        # he hugs me too
    ] + speech_clacks(268, 'tight', -9.0)


@test
def t07_blink_click():
    a, b = 652.5, 668.0
    return a, b, beds(a, b, creaks=False) + [
        ev(A('w312:opens') + 0.6, 'eyelid_click', -6.0, kind='open'),  # in my arms he opens his eyes
        ev(A('w314:wink') + 0.3, 'wood_creak', -12.0, 'tight', kind='tick', dur=0.1),   # the effort, a shudder
        ev(660.95, 'eyelid_click', 0.0, kind='shut'),                  # both of his eyelids close:
        ev(661.40, 'eyelid_click', 0.0, kind='shut'),                  # click, click
        ev(A('s317') + 0.3, 'breath', -8.0, kind='gasp'),              # "Owen can't wink."
    ]


@test
def t08_ending():
    a, b = 663.0, FULL
    museum = A('s325')
    sting = A('s330')
    return a, b, [
        ev(a, 'room_tone_house', 0.0, dur=museum - a + 0.5),
        ev(A('w319:museum'), 'car_pass', 2.0, 'window', kind='arrive', dur=5.0),   # the man from the museum comes
        ev(A('s324') + 0.4, 'car_door_close', -2.0, 'window'),
        ev(A('w324:waves') + 0.5, 'van_pull_away', 3.0, 'window', dur=6.0),          # the van pulls away
        ev(museum, 'museum_tone', 0.0, dur=sting - museum + 0.3),
        ev(684.9, 'eyelid_click', -2.0, 'behind_glass', kind='shut'),  # he'll try to wink at you
        ev(685.35, 'eyelid_click', -2.0, 'behind_glass', kind='shut'),
        ev(sting, 'room_tone_house', 0.0, dur=b - sting),
        ev(sting, 'old_clock', 0.0, dur=b - sting),
        ev(A('w331:drinks') - 0.6, 'spoon_stir', -2.0, dur=1.6),       # coffee, two sugars
        ev(A('w331:drinks') + 1.15, 'spoon_clink', -4.0, n=1),
        ev(A('w331:drinks') + 1.7, 'sip', -6.0),
        ev(A('s332') + 0.3, 'mug_set', -4.0),
        ev(A('w333:stopped') - 0.9, 'footsteps_hall', -4.0, n=3, rate=1.5, approach=1.0),   # on his way to bed
        ev(A('w333:stopped') + 0.2, 'wood_creak', -10.0, 'inside', kind='creak', dur=0.6),   # the doorway's board
        # fallback checks (must warn, not crash): an alias, a keyword guess, an unknown space, a name nothing fits,
        # params that are not a dict, a cue without a time, a gain that is not a number, an fx-less space object
        ev(sting + 1.0, 'laughter', -40.0), ev(sting + 1.2, 'creepy_lamp_hum', -40.0),
        ev(sting + 1.4, 'eyelid_click', -40.0, space='the_moon'), ev(sting + 1.6, 'zzz_not_a_sound', 0.0),
        {'t': sting + 1.8, 'name': 'dummy_clack', 'gain_db': -40.0, 'params': [1, 2]},
        {'name': 'dummy_clack', 'gain_db': 0.0}, {'t': sting + 2.0, 'name': 'sip', 'gain_db': 'loud'},
        {'t': sting + 2.2, 'name': 'tiny_steps', 'gain_db': -40.0, 'space': {'x': 1}},
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
        if ck['phone_band_db'] < -15 and e['resolved'] not in ('goodnight_hit',):
            w.append(f"{ck['phone_band_db']} dB above 300 Hz (thin on a phone)")
        speech_tick = e['resolved'] == 'dummy_clack' and (e.get('params') or {}).get('kind') == 'speech'
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
            if e['type'] not in ('show', 'winks') or e['t'] + e.get('len', 0) < a or e['t'] > b:
                continue
            i0 = max(0, int((max(e['t'], a) - a + 0.5) / 0.25)); i1 = int((min(e['t'] + e.get('len', 0), b) - a - 0.5) / 0.25)
            seg = sm[i0:max(i0 + 1, i1)]
            seg = seg[seg > -70]
            x = SX.mono(show[int((max(e['t'], a) - a) * SR):int((min(e['t'] + e.get('len', 0), b) - a) * SR)])
            P = np.abs(np.fft.rfft(x)) ** 2 if len(x) > 1000 else np.ones(10); f = np.fft.rfftfreq(len(x), 1 / SR) if len(x) > 1000 else np.ones(10)
            r = {'t': e['t'], 'type': e['type'], 'space': e.get('space'), 'len': e.get('len'),
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
           '--who-fx', '', '--score-stems']
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


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    argv = sys.argv[1:]
    jobs = 2
    if '--jobs' in argv:
        k = argv.index('--jobs'); jobs = int(argv[k + 1]); argv = argv[:k] + argv[k + 2:]
    which = [int(x) for x in argv if not x.startswith('--')] or list(range(1, len(TESTS) + 1))
    with ThreadPoolExecutor(max_workers=max(1, jobs)) as ex:
        for name, flags in ex.map(run, which):
            for f in flags or []:
                print('   flag', name, f)
