"""sfx_plan.py: the final mix's sound-design pass over the picture's SFX cue sheet ("If Your Mom's Eyes Turn Into
Buttons... DON'T KEEP HER SECRET"; the Walls film's tables replaced: ADD, PICTURE, ROOM, SPACE_MAP, FAMILY are this
film's, EDIT, SHIFT and OFF_WORDS wait for the first full mix; the Tik / Ping beats come from audio/beats.py). THIS film's tables (EDIT, ADD, PICTURE, FAMILY, ROOM, SHIFT, DOUBLE_S) are
written for it; anchors are script PHRASES (music_plan.resolve), so they follow any voice edit or lines.py tag scheme.
The Bus film's notes below describe the mechanism.

film.py writes W/cues/sfx_cues.json from the picture: every drawn action at its frame. That sheet stays the source
and its timings are never moved (they are the picture's sync). This pass, applied by mix.py with `--plan full`
(audio/final_mix.sh), only
  0. maps the picture's names onto this film's recipes (PICTURE / picture_pass): sfx.py's keyword guesses sent many
     of this film's names to the wrong sound (glass_pound -> a window smash, metal_rip -> cloth, door_slap ->
     a creak, bus_drive -> rain, lights_blink -> an eyelid click) or to nothing (deadbolt_slide, engine_start_bus,
     marker_x); every name is mapped here on purpose. Drops what another layer carries (the rule cards' typing: the
     rules are Grandma's handwriting; his amber hum and the room-tone drop) and doubled ticks (a vhs_glitch on a
     tape_skip frame, a second glove slap or neck ratchet within a few frames),
  1. re-levels picture cues that measure buried or too busy in the full-length checks (EDIT),
  2. adds the sounds the picture does not draw (ADD): bus 9's warm morning cabin (Della's "good morning" and the
     new girl), the 911 call going through, the sirens coming to the school lot, the morning birds.
     An ADD row is skipped when the picture's sheet already has a cue of the same sound within 2 s of it (the same
     recipe after resolving, or the same FAMILY; the picture wins: no doubled sounds). A row with 'snap': name moves
     onto the picture's nearest cue of that name (within 1.2 s).
Every added cue is anchored to the narration (music_plan.resolve: 'sN' / 'eN' / 'wN:word' +- s, or seconds), so it
follows the recording, not a shot list, and survives picture changes.

    apply(cues, lines) -> (cues, log)      cues: the picture's list (not modified); log: what changed, one line each
    python3 sfx_plan.py [--cues W/cues]     prints the pass (dry run)
"""
import copy, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import music_plan as MP                                   # noqa: E402

# --------------------------------------------------------------------------------------------- EDIT (picture cues)
# (name, t0, t1, match params (subset), change, why). t0 / t1: anchors or seconds (the window the cue's t falls in).
# change: {'add_db': x} | {'gain_db': x} | {'min_db': x} | {'params': {...}} | {'space': s} | {'drop': True}
# Names here are the names AFTER the picture pass (the recipes).
EDIT = [           # the Buttons film (measure_mix.py + --events on the full mix)
    ('ping', 'Face down on the bed', 'Okay. Breathe', {}, {'params': {'kind': 'muffled'}},
     'the tablet face down on the bed pings once: muffled'),
    # first full mix (24 Nov): story-beat foley buried 18-25 LU under voice + music: up, still under the voice
    ('camera_shutter', 78.0, 80.0, {}, {'add_db': 4.0}, 'Mom lifts her phone: the photo is the clue'),
    ('palms_glass', 173.5, 175.5, {}, {'add_db': 6.0}, 'palms on the lobby glass'),
    ('door_creak', 236.0, 236.6, {}, {'add_db': 8.0}, '"I opened the closet." (not a rule-card creak)'),
    ('phone_ring', 272.0, 273.0, {}, {'add_db': 4.0}, '"First ring."'),
    ('coat_buttons', 541.0, 546.5, {}, {'add_db': 6.0}, 'the six buttons closing on her sung beats'),
    ('marker_squeak', 587.0, 588.5, {}, {'add_db': 6.0}, '"The marker squeaked." (the Blank lunges at it)'),
    ('marker_squeak', 588.5, 612.0, {}, {'add_db': 4.0}, 'MOM IT\'S OWEN I\'M HERE / everything'),
    ('buttons_rolling', 639.0, 641.0, {}, {'add_db': 5.0}, 'two buttons roll and stop at her slippers'),
]
THIN_MIN_GAP = 0.26
THIN_GAIN = {None: -10.0}
THIN_QUIET = []

# --------------------------------------------------------------------------------------------- ADD
# (anchor, name, gain_db, space, params, why). params 'dur': 'until:<anchor>' -> seconds to that anchor.
# The script's Tik. / Ping. beats are NOT here: audio/beats.py adds them from W/align/beats.json (mix.py).
ADD = [
    # ---- beds: the help line at the kitchen table, the fridge at night, the snow-day pickup, the streetlight
    ('Mom worked twelve-hour help-line shifts', 'helpline_kitchen', 0.0, None,
     {'dur': 'until:That night, in a game chat', 'keys': 0.3}, 'a caller in her headset, the fridge; the picture draws her keys'),
    ('After school, Mom sat behind me', 'helpline_kitchen', -2.0, None, {'dur': 'until:Rule number five'},
     'the kitchen after school: the microwave door beat'),
    ('Thursday dinner', 'helpline_kitchen', -3.0, None,
     {'dur': 'until:That night, Mom sat on my windowsill', 'keys': 0.0}, 'dinner: her headset at the window, no keys'),
    ('Two in the morning', 'fridge_hum', 0.0, None, {'dur': 'until:After school, Mom sat behind me'}, 'the 2 a.m. kitchen'),
    ('Two minutes to midnight', 'fridge_hum', 0.0, None, {'dur': "until:She'd put buttons where I'd never looked"}, 'the kitchen at midnight'),
    ('That night, a woman stood under that streetlight', 'streetlight', -4.0, None,
     {'dur': 'until:Before rule two', 'flicker': 0.0}, 'the streetlight under his window'),
    ('Under the streetlight, someone waved', 'streetlight', -4.0, None, {'dur': 'until:Okay. Breathe', 'flicker': 0.0},
     'the son\'s streetlight'),
    ('Wednesday pickup', 'school_pickup', 0.0, None, {'dur': 'until:Mom came running'},
     'kids far across the lot, a car idling, the snow\'s hush'),
    # ---- the setup, rule 1, rule 2
    ('She was at our lobby door, palms on the glass#palms', 'palms_glass', 0.0, 'outside', {'n': 2},
     'palms on the lobby\'s glass door: never a knock'),
    ('Inside my closet... click#click -0.25', 'closet_clicks', 0.0, 'closet', {'n': 3, 'spacing': 0.6},
     'click. Click. Click. like somebody counting (each just before its word: 228.7 / 229.2 / 229.9)'),
    ('Then, slowly, it sagged', 'cloth_rustle', -4.0, None, {}, 'the full coat sagging empty'),
    # ---- rule 3: the car, Mr. Dunn, the police
    ('The door swung open', 'car_door_open', -2.0, 'street', {}, 'the car door swings open'),
    ('First ring -0.5', 'phone_ring', -3.0, 'phone', {'n': 1}, 'he calls Mom: one ring'),
    ('His radio was already up', 'police_radio', -2.0, 'street', {'dur': 2.4}, 'the crossing guard\'s radio'),
    ('The arm folded back in +0.6', 'tires_snow', 0.0, None, {'dur': 4.0}, 'the car pulls away: just tire tracks'),
    ('Officer Mensah took notes', 'pen_scratch', -4.0, 'close', {'dur': 1.6}, 'his notebook'),
    ('Mom checked every lock twice', 'lock_turn', -4.0, None, {}, 'the locks'),
    # ---- rule 4, rule 5
    ('Every key she pressed', 'typing', -4.0, None, {'dur': 2.2, 'cps': 6.0}, 'the Blank typing at Mom\'s laptop'),
    ('end:Every key she pressed... my tablet pinged +0.05', 'ping', -3.0, None, {}, 'his tablet pings'),
    ('Her head set the lamp swinging#lamp', 'lamp_swing', 0.0, None, {'dur': 4.0}, 'the lamp swinging on its cord'),
    ('Two minutes to midnight. Officer Mensah was back', 'police_radio', -6.0, 'outside', {'dur': 3.0},
     'his radio, low, from the hall'),
    # ---- rule 7: the coat, the marker, the cardigan, the jar
    ('She wrapped the coat around me', 'cloth_rustle', -3.0, None, {}, 'the coat wraps loosely around him'),
    ('warm two for snug#One', 'coat_buttons', 0.0, None, {'times': [0.0, 0.72, 1.68, 2.32, 3.36, 4.88]},
     'six buttons close themselves on her sung beats (One, warm, two, snug, three, hug); the top one waits'),
    ('Under FRI, I wrote', 'marker_squeak', -3.0, None, {'strokes': 6}, 'MOM IT\'S OWEN I\'M HERE'),
    ('The marker squeaked -0.45', 'marker_squeak', 0.0, None, {'strokes': 1}, 'the squeak the Blank lunges at'),
    ('So I wrote everything', 'marker_squeak', -4.0, None, {'strokes': 8}, 'he writes everything'),
    ('Two black buttons rolled', 'buttons_roll', 0.0, None, {'dur': 2.2}, 'two buttons roll and stop at her slippers'),
    ('Lid on tight', 'jar_lid', 0.0, None, {'turns': 2}, 'the lid screwed tight'),
    ('She wound the music box#wound', 'music_box_wind', -2.0, None, {'dur': 1.6}, 'she winds the real music box'),
    ('Mom laid her phone face down', 'tablet_down', -2.0, None, {'surface': 'table'}, 'her phone face down'),
    # ---- the sting
    ('I opened his door', 'door_creak', -3.0, 'inside', {}, 'his door, down the hall'),
    ('He turned the tablet face down', 'tablet_down', 0.0, None, {'surface': 'bed'}, 'the tablet face down on the bed'),
    ('end:Face down on the bed, the tablet pinged +0.08', 'ping', 0.0, None, {'kind': 'muffled'},
     '"pinged. Once. Still waiting." (not a beats.json beat: the narrator says it)'),
]
DEDUP_S = 2.0                                             # an ADD row yields to a picture cue of its sound this close
# a picture cue of these names closer than this to the last one of the same name is a doubled tick: dropped
DOUBLE_S = {'light_switch': 0.3, 'tik': 0.12, 'ping': 0.2}

# picture name -> (recipe, extra params, gain or None, why); None drops the cue
PICTURE = {
    # the motif and every sung line are not SFX: the score's identity layer and the voice track carry them (the
    # son's tablet chime is the motif's 'chime' version)
    'chime': None, 'jingle': None, 'music_box': None, 'humming': None, 'singing': None, 'song': None, 'hum': None,
    'tablet_chime': None, 'music_box_four_notes': None,
    # film.py's names (W/cues/sfx_cues.json, 24 Nov picture) onto this film's recipes; 'name@who' rows win over 'name'
    'apartment_night': ('house_night', {'clock': 0.0, 'rain': 0.0, 'creaks': 0.15}, None,
                        'the flat at night: room tone, the fridge from the kitchen (no crickets, no clock)'),
    'apartment_day': ('room_tone_house', {'hum': 0.3}, None, 'the flat by day (the help-line bed rides on top)'),
    'key_tap': ('typing', {'dur': 0.05, 'cps': 7.0}, -18.0, 'one laptop key on the drawn frame'),
    'key_tap@owen_pj': ('touch_tap', {'n': 1}, -20.0, 'his thumb on the tablet glass: no key clack'),
    'key_tap@son': ('touch_tap', {'n': 1}, -20.0, 'the son\'s thumb on the tablet glass'),
    'fingertip_tap': ('tik', {'kind': 'tap'}, None, 'the Blank\'s button fingertips: tapping like buttons on glass'),
    'phone_shutter': ('camera_shutter', {'kind': 'tablet'}, -14.0, 'Mom lifts her phone: the photo (her lock screen)'),
    'closet_door_creak': ('door_creak', {'slow': 0.8}, -16.0, 'the closet door opening on the Brave List'),
    'knock_door': ('palms_glass', {'n': 1}, -10.0, 'palms on the lobby glass: never a knock'),
    'cardboard_open': ('box_open', {}, -10.0, 'the box on the doormat opened'),
    'button_click': ('closet_clicks', {'n': 1}, None, 'click. Click. Click. (one per drawn frame)'),
    'coat_button_close': ('coat_buttons', {'n': 1}, None, 'one red-coat button closing on her sung beat'),
    'phone_ring_out': ('phone_ring', {'n': 1}, -14.0, 'he calls Mom: one ring in his ear'),
    'car_drive_off': ('tires_snow', {'dur': 4.0}, -8.0, 'the car pulls away on snow: just tire tracks'),
    'microwave_hum': None,
    # the picture's impact_hit frames all sit ON a spoken word ("flashed.", "Buttons.", "see", "wide,", "circles.",
    # just before "NO!") and doubled the plan's boosted hits 0.6-0.8 s later (music_plan EVENTS, after the words,
    # +8..+9 LU, smooth releases): the score's word-anchored hits carry every scare
    'impact_hit': None,
    'radio_key': ('police_radio', {'dur': 1.2}, None, 'the crossing guard keys his radio'),
    'cardigan_collapse': ('cardigan_fall', {'dur': 1.6}, None, 'the Blank folds down into an empty cardigan'),
    'tablet_ping_soft': ('ping', {}, None, 'his tablet pings (every key she presses; face down on the bed)'),
    'b3_unfold': ('his_unfold', {'n': 4, 'spacing': 0.5}, -10.0, 'up, and up: the long joints unfolding behind the fridge'),
    'b3_ceiling': None,
    'ceiling_creak': ('wood_creak', {'kind': 'grind', 'dur': 2.0}, -12.0, 'her head bending along the ceiling'),
    'b3_collapse': None,
    'door_open_soft': ('door_creak', {'slow': 1.2}, -14.0, 'his son\'s door down the hall'),
}
WHO_HUM = {}
FAMILY = {'footsteps_wood_inside': 'steps', 'footsteps_porch': 'steps', 'footsteps_grass': 'steps',
          'doorknob': 'knob', 'light_switch': 'switch', 'helpline_kitchen': 'kitchen', 'fridge_hum': 'flat',
          'phone_ring': 'call', 'police_radio': 'radio', 'walkie': 'radio', 'house_night': 'flat',
          'deadbolt': 'lock', 'lock_turn': 'lock'}


def _t(a, lines):
    return float(a) if isinstance(a, (int, float)) else MP.resolve(a, lines)


def _match(c, name, a, b, sub):
    if c.get('name') != name:
        return False
    try:
        t = float(c['t'])
    except (KeyError, TypeError, ValueError):
        return False
    if not (a - 1e-3 <= t <= b + 1e-3):
        return False
    p = c.get('params') if isinstance(c.get('params'), dict) else {}
    return all(p.get(k) == v for k, v in sub.items())


def _canon(name, params=None):
    """The recipe a cue name plays (sfx.resolve; the name itself when sfx.py cannot be imported)."""
    try:
        import sfx as SX
        cn, _p, _n = SX.resolve(str(name), params if isinstance(params, dict) else {})
        return cn or str(name)
    except Exception:
        return str(name)


def _span(cn, params):
    """How long a cue's sound lasts on the picture, for the overlap test (steps: n treads at rate; else ~0)."""
    p = params if isinstance(params, dict) else {}
    try:
        if cn in ('footsteps_wood_inside', 'footsteps_stairs', 'footsteps_porch', 'footsteps_hall', 'footsteps_grass',
                  'hatchet_step', 'snow_walk', 'snow_run', 'snow_deep'):
            n = float(p.get('n') or (4 if cn == 'hatchet_step' else 1))
            r = float(p.get('rate') or (0.75 if cn == 'hatchet_step' else 1.8))
            return max(0.0, (n - 1) / r + (0.3 if cn == 'hatchet_step' else 0.0))
        if p.get('dur') and cn in ('struggle', 'wet_drag', 'paper_under_door', 'ambience_woods', 'ambience_dawn',
                                   'ambience_night', 'room_tone', 'room_tone_house', 'burn_barrel', 'bulb', 'dogs_search',
                                   'crowd_parade', 'hospital_room', 'hospital_corridor', 'house_creaks', 'old_clock',
                                   'house_night', 'waiting_room', 'drive_rain', 'halverson_car', 'er_bustle',
                                   'office_3am', 'rain_house', 'streetlight', 'breath', 'line_hiss',
                                   'morning_bus', 'bus9_drive', 'bus_idle', 'siren_far', 'suburb_night', 'tape_hiss',
                                   'cold_night', 'frozen_still', 'house_hum', 'house_cold', 'truck_idle',
                                   'shovel_morning', 'radio_static', 'frost_creep', 'attic_crawl', 'scuttle',
                                   'ambulance', 'plow_pass', 'truck_glide', 'hall_clicks'):
            return float(p['dur'])
    except (TypeError, ValueError):
        pass
    return 0.0


ROOM = {'kitchen': ('helpline_kitchen', {}, 0.0), 'kitchen_day': ('helpline_kitchen', {}, 0.0),
        'kitchen_night': ('fridge_hum', {}, 0.0), 'night_in': ('fridge_hum', {}, -3.0),
        'street_night': ('streetlight', {'flicker': 0.0}, -4.0), 'pickup': ('school_pickup', {}, 0.0),
        'snow_day': ('school_pickup', {}, 0.0), 'house_day': ('room_tone_house', {}, 0.0)}
SPACE_MAP = {'closet': 'next_room', 'lobby': 'outside'}
# recipes whose transient sits off the picture's frame by a fixed amount (filled by measure_mix.py on the first mix)
SHIFT = {'cardboard_open': -0.14, 'phone_shutter': -0.05, 'coat_button_close': -0.06,   # the Buttons film: the
         'b3_unfold': -0.3, 'cardigan_collapse': -0.3}     # first full mix's transient offsets (measure_mix.py)
# sound fix round (critic minor 10): the cast's walk cycles emit wooden steps for every space; outdoors they are snow
INDOOR_STEPS = ('footsteps_wood_inside', 'footsteps_hall', 'footsteps_stairs')
OUTDOOR_SPACES = ('outside', 'snow', 'yard', 'street', 'cold_street', 'porch')
STEP_NAMES = ('footsteps_grass', 'footsteps_porch', 'footsteps_wood_inside', 'footsteps_hall')
STACK_S = 0.04
# OFF_WORDS (minors 6-8): (recipe names, from, to, why): their transients move off the spoken words into the gaps
VO_PATH = os.path.join(MP.W, 'align', 'vo_en.wav')
OFF_MAX = 0.45
ON_WORD_DB = {'impact_hit': -6.0}
OFF_WORDS = [                       # the Buttons film: filled from the first full mix
]


def picture_pass(out, lines, log):
    """PICTURE: film.py's names onto this film's recipes; what another layer carries is dropped."""
    res, n0 = [], len(out)
    last = {}                                             # name -> last kept t (doubled ticks)
    for c in sorted(out, key=lambda c: float(c.get('t', 0.0)) if isinstance(c.get('t'), (int, float)) else 1e9):
        nm = c.get('name'); p = dict(c.get('params') or {}) if isinstance(c.get('params'), dict) else {}
        try:
            t = float(c['t'])
        except (KeyError, TypeError, ValueError):
            res.append(c); continue
        if c.get('space') in SPACE_MAP:
            c = dict(c, space=SPACE_MAP[c['space']])
        if nm in SHIFT:
            c = dict(c, t=round(t + SHIFT[nm], 3))
            log.append(f'PIC  {nm:18s} {t:7.2f} moved {SHIFT[nm]:+.2f} s (its transient onto the frame)')
        why = None
        if nm in DOUBLE_S and t - last.get(nm, -9.0) < DOUBLE_S[nm]:
            log.append(f'PIC  {nm:18s} {t:7.2f} dropped: doubled ({t - last[nm]:.2f} s after the last)'); continue
        last[nm] = t
        if nm == 'room_tone' and p.get('kind') in ROOM:
            rn, extra, g = ROOM[p['kind']]
            q = dict(extra); q['dur'] = p.get('dur', 10.0)
            c = dict(c, name=rn, params=q, gain_db=float(c.get('gain_db', 0.0) or 0.0) + g)
            why = f'room tone {p["kind"]} -> {rn}'
        elif f"{nm}@{p.get('who')}" in PICTURE or nm in PICTURE:
            m = PICTURE.get(f"{nm}@{p.get('who')}", PICTURE.get(nm))
            if m is None:
                log.append(f'PIC  {nm:18s} {t:7.2f} dropped'); continue
            rn, extra, g, why = m
            q = dict(p); q.update(extra)
            for k in ('index', 'who', 'step'):
                q.pop(k, None)
            c = dict(c, name=rn, params=q)
            if g is not None:
                c['gain_db'] = g
        if c.get('name') in INDOOR_STEPS and c.get('space') in OUTDOOR_SPACES:      # wood steps outdoors: the lawn
            q = {k: v for k, v in (c.get('params') or {}).items() if k in ('n', 'rate', 'dur')}
            c = dict(c, name='snow_walk', params=q, space='outside')
            why = (why + '; ' if why else '') + 'an indoor step outdoors -> a step in the snow'
        if why:
            log.append(f'PIC  {nm:18s} {t:7.2f} -> {c["name"]} {c.get("params")} {c.get("gain_db", 0):+.1f} dB  ({why})')
        res.append(c)
    # minor 10: several characters stepping on the same frame stacked the same step 2-3 times: one step, a little louder
    out2, last_step = [], {}
    for c in res:
        nm2 = c.get('name')
        if nm2 in STEP_NAMES and isinstance(c.get('t'), (int, float)):
            k = last_step.get(nm2)
            if k is not None and abs(float(c['t']) - float(k['t'])) < STACK_S:
                k['gain_db'] = round(min(float(k.get('gain_db', 0.0) or 0.0) + 1.5, 0.0), 2)
                log.append(f'PIC  {nm2:18s} {float(c["t"]):7.2f} merged into the step at {float(k["t"]):.2f} (stacked)')
                continue
            last_step[nm2] = c
        out2.append(c)
    log.append(f'PICTURE: {n0} picture cues -> {len(out2)}')
    return out2


def _voice_gaps(a, b):
    """Silent stretches (>= 100 ms under -45 dB, 10 ms frames) of the edited narration between a and b (s)."""
    try:
        import soundfile as sf, numpy as np
        info = sf.info(VO_PATH); sr = info.samplerate
        x, _ = sf.read(VO_PATH, start=max(0, int(a * sr)), stop=int(b * sr), dtype='float32', always_2d=True)
        x = x.mean(1); h = sr // 100; m = len(x) // h
        db = 10 * np.log10((x[:m * h].reshape(m, h) ** 2).mean(1) + 1e-12)
        q = db < -45.0
        gaps, i = [], 0
        while i < m:
            if q[i]:
                j = i
                while j < m and q[j]:
                    j += 1
                if j - i >= 10:                          # 100 ms: not a stop closure inside a word
                    gaps.append((a + i / 100.0, a + j / 100.0))
                i = j
            else:
                i += 1
        return gaps
    except Exception:
        return []


def on_words(out, lines, log):
    """ON_WORD_DB: the picture's reveal-frame impacts that land INSIDE a spoken word (the boosted score hits now wait
    for the scare beat after the word) come down by that much, so the word stays over them."""
    for c in out:
        nm = c.get('name')
        if nm not in ON_WORD_DB or not isinstance(c.get('t'), (int, float)):
            continue
        t = float(c['t'])
        if not any(l['t'] - 0.02 <= t <= l['end'] for l in lines):
            continue
        gaps = _voice_gaps(t - 0.3, t + 0.3)
        if any(g0 <= t <= g1 - 0.05 for g0, g1 in gaps):
            continue
        c['gain_db'] = round(float(c.get('gain_db', 0.0) or 0.0) + ON_WORD_DB[nm], 2)
        log.append(f'ONW  {nm:18s} {t:7.2f} {ON_WORD_DB[nm]:+.1f} dB (on a spoken word)')
    return out


def off_words(out, lines, log):
    """OFF_WORDS (minors 6-8): a short transient of these names that lands on a spoken word moves into the nearest
    silence of the narration (within OFF_MAX s), its transient 40 ms into the gap: the sound, then the word naming it."""
    for names, a, b, why in OFF_WORDS:
        try:
            ta, tb = _t(a, lines), _t(b, lines)
        except Exception as e:
            log.append(f'OFFW {a}..{b}: bad anchor ({e!r}): skipped'); continue
        gaps = _voice_gaps(ta - 1.0, tb + 1.0)
        if not gaps:
            log.append(f'OFFW {a}..{b}: no narration gaps read: skipped'); continue
        used = []
        for c in sorted([c for c in out if c.get('name') in names and isinstance(c.get('t'), (int, float))
                         and ta - 0.05 <= float(c['t']) <= tb + 0.05], key=lambda c: float(c['t'])):
            t = float(c['t'])
            if any(g0 <= t <= g1 - 0.03 for g0, g1 in gaps):
                continue                                               # already in a silence
            cand = []
            for g0, g1 in gaps:
                p = g0 + min(0.04, (g1 - g0) / 3)
                if abs(p - t) <= OFF_MAX and all(abs(p - u) > 0.08 for u in used):
                    cand.append(p)
            if not cand:
                continue
            p = min(cand, key=lambda x: abs(x - t)); used.append(p)
            log.append(f'OFFW {c["name"]:18s} {t:7.2f} -> {p:7.2f} (off the word: {why})')
            c['t'] = round(p, 3)
    return out


# THIS film (Obsession): the Buttons film's EDIT / ADD / OFF_WORDS rows name the Buttons script; they stay for
# reference but are OFF until this film's first full mix fills its own (BUTTONS_ROWS = True brings them back)
BUTTONS_ROWS = False
# THIS film's own re-levels (final mix, measure_mix.py --events on the full mix): (name, t0 s, t1 s, add_db, why)
OBSESSION_EDIT = [
    ('phone_tap', 297.0, 297.4, -6.0, 'Evie types his password: one tap jumped +3.8 LU over the voice'),
    ('chalk_scrape', 353.5, 354.0, -5.0, '"and stood up": the rise sat +0.3 LU over the words (cast sound under them)'),
]


def apply(cues, lines):
    """The picture's cue list -> the mixed cue list (a new list) and a log of every change."""
    out = [copy.deepcopy(c) for c in cues if isinstance(c, dict)]
    log = []
    if not BUTTONS_ROWS:
        log = ['sfx plan: the Buttons rows are off for this film (sfx_plan.BUTTONS_ROWS)']
        for name, ta, tb, add, why in OBSESSION_EDIT:
            hit = [c for c in out if c.get('name') == name and ta <= float(c.get('t', -1)) <= tb]
            for c in hit:
                c['gain_db'] = round(float(c.get('gain_db', 0.0) or 0.0) + add, 2)
            log.append(f'EDIT {name} {ta}-{tb} {add:+.1f} dB: {len(hit)} cue(s) ({why})')
        return out, log
    out = picture_pass(out, lines, log)
    # EDIT
    for name, a, b, sub, ch, why in EDIT:
        try:
            ta, tb = _t(a, lines), _t(b, lines)
        except Exception as e:
            log.append(f'EDIT {name} {a}..{b}: bad anchor ({e!r}): skipped'); continue
        hit = [c for c in out if _match(c, name, ta, tb, sub)]
        for c in hit:
            g0 = float(c.get('gain_db', 0.0) or 0.0)
            if ch.get('drop'):
                c['_drop'] = True
            if 'add_db' in ch:
                c['gain_db'] = round(g0 + ch['add_db'], 2)
            if 'gain_db' in ch:
                c['gain_db'] = ch['gain_db']
            if 'min_db' in ch:
                c['gain_db'] = max(g0, ch['min_db'])
            if 'params' in ch:
                c['params'] = dict(c.get('params') or {}, **ch['params'])
            if 'space' in ch:
                c['space'] = ch['space']
            if 'at' in ch:                                # moved onto a word (sound fix round)
                c['t'] = round(_t(ch['at'], lines), 3)
        log.append(f'EDIT {name:18s} {ta:7.2f}-{tb:7.2f} {sub or ""} {ch}: {len(hit)} cue(s)  ({why[:70]})')
    out = [c for c in out if not c.get('_drop')]
    out = off_words(out, lines, log)
    out = on_words(out, lines, log)
    # THIN the speech ticks
    quiet = []
    for a, b, g in THIN_QUIET:
        try:
            quiet.append((_t(a, lines), _t(b, lines) + 0.3, g))
        except Exception:
            pass
    sp = sorted([c for c in out if c.get('name') == 'dummy_clack' and (c.get('params') or {}).get('kind') == 'speech'],
                key=lambda c: float(c['t']))
    keep, last, n0 = [], -9.0, len(sp)
    for c in sp:
        t = float(c['t'])
        if t - last < THIN_MIN_GAP:
            c['_drop'] = True; continue
        last = t
        g = THIN_GAIN.get(c.get('space') if c.get('space') == 'tv' else None)
        for a, b, gq in quiet:
            if a <= t <= b:
                g = gq
        c['gain_db'] = min(float(c.get('gain_db', 0.0) or 0.0), g)
        keep.append(c)
    out = [c for c in out if not c.get('_drop')]
    log.append(f'THIN dummy_clack speech: {n0} -> {len(keep)} ticks (>= {THIN_MIN_GAP} s apart, -10 room / -13 TV / '
               f'-15 under the tape cry)')
    # ADD
    have, fam = {}, {}
    for c in out:
        try:
            tc = float(c['t'])
        except (KeyError, TypeError, ValueError):
            continue
        cn = _canon(c.get('name'), c.get('params'))
        span = _span(cn, c.get('params'))
        for k in {str(c.get('name')), cn}:
            have.setdefault(k, []).append((tc, tc + span))
        if cn in FAMILY:
            fam.setdefault(FAMILY[cn], []).append((tc, tc + span))
    for a, name, g, space, params, why in ADD:
        try:
            t = _t(a, lines)
            p = dict(params)
            if isinstance(p.get('dur'), str) and p['dur'].startswith('until:'):
                p['dur'] = round(max(0.3, _t(p['dur'][6:], lines) - t), 2)
            for k_ in ('groups', 'counts'):           # 'gaps:a,b,c' -> seconds from the first anchor
                if isinstance(p.get(k_), str) and p[k_].startswith('gaps:'):
                    gs = [_t(x, lines) for x in p[k_][5:].split(',')]
                    p[k_] = [round(x - gs[0], 3) for x in gs]
        except Exception as e:
            log.append(f'ADD {name} at {a}: bad anchor ({e!r}): skipped'); continue
        cn = _canon(name, p)
        a0, a1 = t, t + _span(cn, p)
        if a1 - a0 > 4.0:                                 # a bed yields only to a picture bed covering half of it
            near = lambda iv: sum(max(0.0, min(a1, y) - max(a0, x)) for x, y in iv) >= 0.5 * (a1 - a0)
        else:
            near = lambda iv: any(a0 - DEDUP_S < y and x < a1 + DEDUP_S for x, y in iv)
        if p.pop('keep', False):
            pass
        elif near(have.get(name, [])) or near(have.get(cn, [])) or (cn in FAMILY and near(fam.get(FAMILY[cn], []))):
            log.append(f'ADD  {name:18s} {t:7.2f} skipped: the picture already has it ({FAMILY.get(cn, cn)})'); continue
        sn = p.pop('snap', None)
        if sn:
            cand = [x for x, _y in have.get(sn, []) if abs(x - t) <= 1.2]
            if cand:
                t0_ = t; t = min(cand, key=lambda x: abs(x - t0_))
                log.append(f'SNAP {name:18s} {t0_:7.2f} -> {t:7.2f} (the picture\'s {sn})')
        c = {'t': round(t, 3), 'name': name, 'gain_db': g, 'pan': 0.0, 'params': p, 'plan': 'sfx_plan'}
        if space:
            c['space'] = space
        out.append(c)
        log.append(f'ADD  {name:18s} {t:7.2f} {g:+5.1f} dB {space or "-":9s} {p}  ({why[:70]})')
    out.sort(key=lambda c: float(c.get('t', 0.0)) if isinstance(c.get('t'), (int, float)) else 1e9)
    return out, log


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--cues', default=os.path.join(MP.W, 'cues'))
    A = ap.parse_args()
    L, _d = MP.load_lines()
    sc = json.load(open(os.path.join(A.cues, 'sfx_cues.json')))
    new, lg = apply(sc, L)
    print('\n'.join(lg))
    print(f'{len(sc)} picture cues -> {len(new)} mixed cues')
