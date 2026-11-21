"""sfx_plan.py: the final mix's sound-design pass over the picture's SFX cue sheet ("If The Ice Cream Truck Plays Its
Song In Winter... DON'T GO OUTSIDE"). THIS film's tables (EDIT, ADD, PICTURE, FAMILY, ROOM, SHIFT, DOUBLE_S) are
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
EDIT = [
    # sound fix round (the sound critic's minors; the picture's cue frames for these were off the words: re-check each
    # on the new cue sheets, the rows only act on a cue inside their window)
    ('skin_stretch', 'Past where a face should end', 'His skin pulls long#pulls', {}, {'at': 'His skin pulls long#pulls -0.12'},
     'minor 5: the skin stretch came 1.1 s before "pulls long"'),
    ('leg_tip_tile', 'Under the door, a needle-thin', 'Under the door, a needle-thin leg tip slides in#slides -0.3', {},
     {'at': 'Under the door, a needle-thin leg tip slides in#slides -0.15'},
     'minor 4: the needle tip came 2.3 s before "slides in"'),
    ('door_tap', 'Then... a soft tap', 'end:Then... a soft tap at the front door', {},
     {'at': 'Then... a soft tap#a -0.3'}, 'minor 8: the tap landed on the word "tap": now in the pause after "Then..."'),
    ('furnace_die', 'Click. -0.6', 'Click. +0.3', {}, {'at': 'Click. -0.1'},
     'minor 11: the relay click just before the word "Click.", not on it'),
    ('leg_punch', 'A long brown leg punches out', "end:A long brown leg punches out, jointed like a spider's", {},
     {'add_db': -4.0}, 'the picture\'s punch lands on "punches out": 4 dB down so the line stays 3+ LU over it'),
]
THIN_MIN_GAP = 0.26
THIN_GAIN = {None: -10.0}
THIN_QUIET = []

# --------------------------------------------------------------------------------------------- ADD
# (anchor, name, gain_db, space, params, why). params 'dur': 'until:<anchor>' -> seconds to that anchor.
ADD = [
    # ---- the cold: the night is always there, under the picture's own room tones
    ('If the ice cream truck plays its song', 'cold_night', -2.0, None, {'dur': 'until:Larkfield. Minus thirty-one',
                                                                          'creaks': 0.3}, 'the cold open: icy wind'),
    ('Every morning at six#scrape -0.1', 'shovel_scrape', -2.0, 'cold_street', {'far': True},
     '"Scrape.": Mr. Kessler\'s shovel at six, across the street'),
    ('The plow pulled away', 'plow_pass', -4.0, None, {'dur': 9.0, 'peak': 3.0}, 'the plow pulls away, its blade'),
    ('And under the radio static', 'radio_static', -6.0, 'close', {'dur': 'until:Rule number one +1.0', 'bells': 0.0},
     'the radio static the three notes come through'),
    ('Eleven-oh-two. Minus thirty-three', 'frozen_still', 0.0, None, {'dur': 'until:Maple. Cedar. Closer'},
     'still frozen air before the song'),
    # ---- his truck idles all night (in the mix, never narrated)
    ('The song stops. Right outside#stops', 'truck_idle', -2.0, None,
     {'dur': 'until:Stop. His song is playing +6.0'}, 'only the idle remains when the song stops'),
    ('Rule number two', 'truck_idle', -6.0, None, {'dur': 'until:Lina is walking toward the pink window', 'inside': True},
     'his engine through the walls (position A, 2:30 to 8:48)'),
    ('Lina is walking toward the pink window', 'truck_idle', -3.0, None, {'dur': 'until:I duck under him'},
     'outside with him: the engine close'),
    ('I duck under him', 'truck_idle', -6.0, None, {'dur': 'until:Then the song moves', 'inside': True},
     'back inside: through the walls again'),
    ('The truck has rolled across the street', 'truck_idle', -6.0, None,
     {'dur': 'until:The truck glides into the white', 'far': True}, 'his engine across the street at Kessler\'s'),
    # ---- the radio
    ('Static. Bells', 'radio_bells', 0.0, 'close', {}, '"Static. Bells.": his bells cut Adam off'),
    ('Static. And bells', 'radio_bells', -2.0, 'close', {}, '"Static. And bells.": the jammed call'),
    ('I grab the radio. No bells', 'radio_static', -4.0, 'close', {'dur': 2.0, 'bells': 0.0},
     '"No bells in the static. He\'s busy.": clean static'),
    # ---- the plow, the horn, the porch lights, the ambulance
    ('Then an orange light sweeps the street', 'plow_pass', -10.0, None, {'dur': 8.0, 'peak': 2.5},
     'Dad\'s plow passing the street (far)'),
    ('Orange light sweeps the window', 'plow_pass', -8.0, None, {'dur': 8.0, 'peak': 2.0}, 'it\'s really him'),
    ("Dad's plow roars onto Birch Lane", 'plow_pass', 0.0, None, {'dur': 9.0, 'peak': 1.5}, 'the plow roars in'),
    ("Horn blaring, again and again", 'plow_horn', 0.0, None, {'n': 5, 'gap': 0.45}, 'the horn, again and again'),
    ('Porch lights click on', 'street_wakes', 0.0, None, {'n': 6, 'span': 5.0}, 'porch lights and doors along the street'),
    ('The truck glides into the white', 'ambulance', -6.0, None, {'dur': 'until:Paramedics said twenty +2.0'},
     'the ambulance arriving out of the white'),
    # ---- the morning
    ('In the morning, Dad, Lina and I shovel', 'shovel_morning', 0.0, None, {'dur': 'until:Lina brings him cocoa +2.0'},
     'three people shoveling his walk'),
    ('His chimney smokes again', 'furnace_start', -6.0, 'inside', {}, 'his furnace lit again'),
    ('Lina brings him cocoa +1.2', 'cocoa_mug', -4.0, 'close', {}, 'the cocoa set down'),
    # ---- the stinger
    ('Two nights later', 'frozen_still', 0.0, None, {'dur': "until:That's why I wrote one more"},
     'still frozen air across town'),
    ('The truck slows at a house', 'truck_idle', -4.0, None, {'dur': 4.0, 'far': True}, 'his engine, slowing'),
    # ---- sound fix round
    ('Lina grabs my coat#grabs -0.05', 'cloth_rustle', -2.0, 'close', {'kind': 'grab'},
     'minor 12: Lina grabbing my coat had no sound'),
    ('Door shut +0.6', 'hall_clicks', 0.0, None, {'dur': 'until:The clicking stops -0.05', 'rate': 1.0, 'keep': True},
     'M3: his leg tips pacing behind the bathroom door, stopping on "The clicking stops."'),
]
DEDUP_S = 2.0                                             # an ADD row yields to a picture cue of its sound this close
# a picture cue of these names closer than this to the last one of the same name is a doubled tick: dropped
DOUBLE_S = {'light_switch': 0.3, 'porch_light': 0.3, 'leg_click': 0.09, 'door_tap': 0.25,
            'furnace_die': 1.5}   # sound fix: leg clicks 60 ms apart were doubles (minor 6); the furnace died twice (11)

# picture name -> (recipe, extra params, gain or None, why); None drops the cue
PICTURE = {
    # his chime, Lina's humming and the voices are not SFX: the score's identity layer and the narration carry them
    'chime': None, 'jingle': None, 'ice_cream_chime': None, 'truck_song': None, 'music_box': None, 'humming': None,
    'hum_song': None, 'typing': None,
    # NO TIRE SOUND for his truck: any car / tire name on him becomes the engine-only glide
    'car_pass': ('truck_glide', {}, None, 'his truck: engine only, no tires'),
    'tire_crunch': ('truck_glide', {}, None, 'no tire tracks: engine only'),
    'van_idle': ('truck_idle', {}, None, 'his van idling'), 'bus_idle': ('truck_idle', {}, None, 'his van idling'),
    'car_idle': ('truck_idle', {}, None, 'his van idling'),
    'snow_crunch': ('snow_walk', {'n': 1}, None, 'one step in snow'),
    'footsteps_grass': ('snow_walk', {}, None, 'steps outside are in snow'),
    'footsteps_porch': ('snow_walk', {}, None, 'the porch is snowed in'),
    'streetlight_flicker': ('street_flicker', {}, None, 'the streetlight flickers'),
    'flicker': ('street_flicker', {}, None, 'the streetlight flickers'),
    'lock_check': ('deadbolt', {}, -4.0, 'I check every lock'),
    'rule_tape': ('tape_rip', {}, -8.0, 'a rule taped to the door'),
    'breath_cloud': ('breath', {}, -10.0, 'breath clouding in the cold room'),
    'wind': ('cold_night', {}, None, 'the cold night'),
    'radio': ('radio_squelch', {}, None, 'the two-way radio'),
    'walkie': ('radio_squelch', {}, None, 'the two-way radio'),
    'dash_radio': ('radio_static', {}, None, 'the two-way radio'),
    'siren_far': ('ambulance', {}, None, 'the ambulance'), 'sirens_arrive': ('ambulance', {}, None, 'the ambulance'),
    'bus_horn': ('plow_horn', {}, None, 'the plow\'s horn'),
    # first full mix: the picture's names the mix did not know (skipped, or a wrong keyword fallback)
    'paper_flutter': ('paper', {}, -6.0, 'the rule card\'s paper'),
    'slap': ('cloth_rustle', {'kind': 'grab'}, 2.0, 'I slap the cone out of her hand (hand_slap has no source here)'),
    'door_pound': ('knock_door', {'force': 1.0}, None, 'Mom pounding on the door (was a door-creak fallback)'),
    'glass_squeak': ('glass_slide', {}, -4.0, 'his face slides up the frosted glass: a long squeak over the slide (was a short wipe)'),
    'door_open_far': ('door_open_street', {}, -6.0, 'doors open along the street (was a pen-click fallback)'),
    'pencil_write': ('pen_scratch', {}, None, 'rule eight written (was a pen-click fallback)'),
    'porch_light_click': ('porch_light', {}, None, 'porch lights click on (was a leg-click fallback)'),
    'cloth_tear': ('cloth_rip', {}, None, 'the coat / blanket tears'),
    'blanket_wrap': ('cloth_rustle', {}, None, 'a blanket wrapped round (was the blanket-yank fallback)'),
    'footsteps_run': ('footsteps_hall', {}, None, 'running down the hall'),
    'attic_click': ('leg_click', {'surface': 'wood'}, None, 'one click through the ceiling (was a whole 4 s crawl per click)'),
    'attic_scuttle': ('attic_crawl', {}, None, 'scuttling in the attic'),
    'glove_snow': ('snow_scuff', {}, None, 'a glove in the snow'),
    'hatch_rattle': ('wood_creak', {'kind': 'tick'}, -2.0, 'the hatch rattles in its frame (was a second hatch drop)'),
    'leg_slide': ('leg_tip_tile', {}, None, 'the needle tip slides in on the tile'),
    'leg_withdraw': ('leg_tip_tile', {}, -4.0, 'the tip pulls back'),
    'radio_grab': ('cloth_rustle', {'kind': 'grab'}, -2.0, 'Adam grabs the radio'),
    'sh_jaw_strain': ('jaw_strain', {}, -6.0, 'his jaw strains (sound fix: a tendon creak and bone ratchet, was a wood creak)'),
    'sh_jaw_close': ('bone_crack', {}, -6.0, 'the jaw snaps shut as the skull shrinks back'),
    'sh_smile_creak': ('skin_stretch', {'kind': 'creak'}, -6.0, 'the smile creaks wider (was a door creak)'),
    'streetlight_buzz': ('lamp_flicker', {'kind': 'buzz'}, -4.0, 'the streetlight buzzes'),
    'coat_rustle': ('cloth_rustle', {}, None, 'coats on'), 'sock_pull': ('cloth_rustle', {}, -4.0, 'a sock pulled on'),
    'boot_on': ('cloth_rustle', {}, -2.0, 'boots pulled on (was a frozen-boot fallback)'),
    'slipper_shuffle': ('snow_scuff', {}, -4.0, 'Kessler shuffles out onto his snowy step'),
    'phone_buzz': ('phone_vibrate', {}, -4.0, 'the phone (was a waiting-room bed fallback)'),
    'tape_press': ('tape_peel', {}, -8.0, 'the rule taped on (was a door-tap fallback)'),
    'flicker_sting': ('street_flicker', {}, None, 'the streetlight flickers'),
    'sh_eyes_sink': None, 'sh_eyes_red': None,        # the score's hit on "red" carries the eyes
    'sh_uniform_split': ('uniform_tear', {}, -4.0, 'the uniform splits'),
    'sh_pour': ('scuttle', {}, -4.0, 'he pours out of the window, legs first on the truck'),
    'sh_land': None,                                  # leg_stab_snow + the hit on the same frame
    # sound fix round: the nine names that fell back to keywords in the first mix
    'cloth_grab': ('cloth_rustle', {'kind': 'grab'}, None, 'a hand grabs cloth'),
    'sh_bone_crack': ('bone_crack', {'n': 2}, -4.0, 'the skin hardens: two dry cracks'),
    'leg_pry': ('leg_pry', {}, -2.0, 'a leg wedges in and pries'),
    'leg_lift': ('leg_click', {'surface': 'metal'}, -8.0, 'a leg lifts off (a light click)'),
    'towel_stuff': ('cloth_rustle', {}, -4.0, 'towels stuffed in the gap (was the towel-jam slam)'),
    'snow_step': ('snow_walk', {'n': 1}, None, 'one step in snow'),
    'leg_hook': ('blanket_yank', {}, None, 'a leg hooks the blanket and pulls'),
    'plow_roar': ('plow_pass', {'peak': 1.0}, None, 'the plow roars in (the ADD row yields to it)'),
    'legs_fold': ('leg_click', {'surface': 'metal', 'n': 4}, -6.0, 'the legs fold away'),
    'sh_jaw_drop': None,                              # the shot's own jaw_drop sits on "drops" 0.9 s earlier (a double)
}
WHO_HUM = {}
FAMILY = {'footsteps_wood_inside': 'steps', 'footsteps_porch': 'steps', 'footsteps_grass': 'steps',
          'doorknob': 'knob', 'light_switch': 'switch', 'morning_bus': 'bus9_morning', 'ambience_dawn': 'dawn',
          'dial_911': 'call', 'siren_far': 'siren'}


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


ROOM = {'house_night': ('house_hum', {}, 0.0), 'house_powered': ('house_hum', {}, 0.0),
        'house_dead': ('house_cold', {}, 0.0), 'house_cold': ('house_cold', {}, 0.0),
        'night_out': ('cold_night', {'creaks': 0.4}, 0.0), 'still': ('frozen_still', {}, 0.0),
        'morning': ('frozen_still', {}, -6.0)}
SPACE_MAP = {'yard': 'snow', 'street_far': 'cold_street'}
# recipes whose transient sits off the picture's frame by a fixed amount (filled by measure_mix.py on the first mix)
SHIFT = {'porch_light_click': -0.11}   # first full mix: the porch light's click landed 116 ms after the frame
# sound fix round (critic minor 10): the cast's walk cycles emit wooden steps for every space; outdoors they are snow
INDOOR_STEPS = ('footsteps_wood_inside', 'footsteps_hall', 'footsteps_stairs')
OUTDOOR_SPACES = ('outside', 'snow', 'yard', 'street', 'cold_street', 'porch')
STEP_NAMES = ('snow_walk', 'snow_run', 'snow_deep', 'footsteps_wood_inside', 'footsteps_hall')
STACK_S = 0.04
# OFF_WORDS (minors 6-8): (recipe names, from, to, why): their transients move off the spoken words into the gaps
VO_PATH = os.path.join(MP.W, 'align', 'vo_en.wav')
OFF_MAX = 0.45
ON_WORD_DB = {'impact_hit': -6.0}
OFF_WORDS = [
    (('leg_click',), "A long brown leg punches out", 'end:Another. Click. Click', 'the leg clicks before "Click."'),
    (('leg_click',), 'The house is as cold as the street', 'end:Across the ceiling', 'the ceiling clicks before "Click."'),
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
        elif nm in PICTURE:
            m = PICTURE[nm]
            if m is None:
                log.append(f'PIC  {nm:18s} {t:7.2f} dropped'); continue
            rn, extra, g, why = m
            q = dict(p); q.update(extra)
            for k in ('index', 'who', 'step'):
                q.pop(k, None)
            c = dict(c, name=rn, params=q)
            if g is not None:
                c['gain_db'] = g
        if c.get('name') in INDOOR_STEPS and c.get('space') in OUTDOOR_SPACES:      # minor 10: wood steps in the snow
            q = {k: v for k, v in (c.get('params') or {}).items() if k in ('n', 'rate', 'dur')}
            c = dict(c, name='snow_walk', params=q, space='snow')
            why = (why + '; ' if why else '') + 'an indoor step outdoors -> a step in snow'
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


def apply(cues, lines):
    """The picture's cue list -> the mixed cue list (a new list) and a log of every change."""
    out = [copy.deepcopy(c) for c in cues if isinstance(c, dict)]
    log = []
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
