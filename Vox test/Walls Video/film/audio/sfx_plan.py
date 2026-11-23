"""sfx_plan.py: the final mix's sound-design pass over the picture's SFX cue sheet ("If Your Little Brother Says
Someone Lives In The Walls... DON'T LAUGH"; the Ice Cream film's tables replaced: ADD, PICTURE, ROOM, SPACE_MAP,
OFF_WORDS are this film's, EDIT and SHIFT wait for the first full mix). THIS film's tables (EDIT, ADD, PICTURE, FAMILY, ROOM, SHIFT, DOUBLE_S) are
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
EDIT = []          # the Walls film: filled from the first full mix's measures (the picture is not built yet)
THIN_MIN_GAP = 0.26
THIN_GAIN = {None: -10.0}
THIN_QUIET = []

# --------------------------------------------------------------------------------------------- ADD
# (anchor, name, gain_db, space, params, why). params 'dur': 'until:<anchor>' -> seconds to that anchor.
ADD = [
    # ---- the August nights: crickets through the window screens, the box fans (under the picture's own room tones)
    ('A heat wave', 'box_fan', -4.0, None, {'dur': 'until:The old owner, Mr. Pell'}, '"Fans in every window."'),
    ('That first night, I woke up at three', 'august_night', -2.0, None,
     {'dur': "until:In the morning, Dad couldn't find"}, 'the first night: Dad in the doorway'),
    ('On the fifth night, I went down for water', 'august_night', -4.0, None, {'dur': 'until:Rule number two'},
     'the dark kitchen at two in the morning'),
    ('That night, I heard chewing', 'august_night', -5.0, None, {'dur': 'until:I told Dad. Dad said I was dreaming'},
     'the pantry at night'),
    ('That night at two, I stood in the upstairs hall', 'august_night', -5.0, None, {'dur': 'until:Rule number five'},
     'the upstairs hall at two'),
    ('That night, I heard it through the wall', 'august_night', -5.0, None, {'dur': 'until:Rule number six'},
     'the bedroom: the song in the wall'),
    ('That night, at three, I woke up', 'august_night', -3.0, None, {'dur': 'until:Then sirens'},
     'the 3 a.m. house, the call, the climax'),
    # ---- the signs (the picture may draw them too: an ADD row yields to its own cue within DEDUP_S)
    ("It still opened on Mr. Pell's old code", 'keypad', -3.0, None, {'n': 4}, 'the old code still works'),
    ('By morning, there would be three police cars#handcuffs', 'handcuffs', -4.0, 'street', {'n': 1},
     'the man on our curb in handcuffs'),
    ('Click. -0.15', 'deadbolt_slow', 0.0, None, {'dur': 2.4}, 'the deadbolt turns by itself; the click before "Click."'),
    ('The bag, folded neatly, twisted shut again#twisted', 'bread_bag', -2.0, None, {'kind': 'twist', 'dur': 1.4},
     'the bread bag twisted shut'),
    ('That night, I heard chewing +0.3', 'chewing', 0.0, None, {'dur': 'until:There was a crack in the plaster'},
     '"Slow. Careful.": chewing inside the pantry wall'),
    ('And then it was gone#crawling', 'wall_crawl', 0.0, None, {'dur': 3.5, 'speed': 1.4, 'travel': [-0.6, 0.9]},
     'crawling away inside the wall, fast, up toward the ceiling'),
    ('That night at two, I stood in the upstairs hall#flipped', 'light_switch', -2.0, None, {'kind': 'wall'},
     'the switch that does nothing'),
    ('Somewhere above me, in a place that was sealed#light', 'attic_light', 0.0, None,
     {'dur': 'until:I flipped the switch off'}, 'the sealed attic\'s bulb comes on, buzzing'),
    ('I flipped the switch off#off', 'light_switch', -2.0, None, {'kind': 'wall'}, 'off again'),
    ('Then the knocking started +0.2', 'knock_door', -3.0, 'in_wall', {'n': 3, 'force': 0.55},
     'the knocking inside the wall by the bed'),
    # ---- 3 a.m.
    ('I heard my dad snore#snore -0.3', 'snore', -2.0, None, {'n': 1}, 'the real Dad, asleep down the hall'),
    ('And he tucked Theo in', 'cloth_rustle', -4.0, None, {}, 'the blanket tucked in'),
    ('I heard the back wall of my closet slide#slide -0.5', 'closet_slide', 0.0, None, {'action': 'open', 'speed': 0.9},
     'the closet\'s back panel slides'),
    ("I slipped in, shut it, locked it#locked", 'lock_turn', -2.0, None, {}, 'the parents\' door locked'),
    ('Mom grabbed her phone and dialed#dialed +0.2', 'dial_911', -2.0, 'close', {}, 'nine-one-one'),
    ('Scratching, inside the bedroom wall', 'wall_scratch', 0.0, 'in_wall',
     {'dur': 'until:Behind the dresser', 'travel': [-0.8, 0.0]}, 'scratching inside the bedroom wall'),
    ('Behind the dresser', 'wall_scratch', -1.0, 'in_wall', {'dur': 1.4, 'travel': [0.0, 0.5]}, 'behind the dresser'),
    ('Behind the headboard', 'wall_scratch', 0.0, 'in_wall', {'dur': 1.3, 'travel': [0.5, 0.9]}, 'behind the headboard'),
    ('Then the vent by the floor rattled#rattled -0.1', 'vent_rattle', 0.0, None, {'dur': 1.2}, 'the floor vent rattles'),
    # ---- the police
    ('Then sirens', 'sirens_arrive', -3.0, 'outside', {'dur': 'until:The officers found him +2.0', 'n_cars': 3},
     'three police cars arriving, through the walls'),
    ('Heavy boots on the stairs -0.3', 'boots_stairs', 0.0, None, {'dur': 2.5, 'officers': 3, 'direction': 'up'},
     'heavy boots up the stairs'),
    ('When Officer Reyes pulled the mask off#pulled', 'glove_squeak', -2.0, None, {'kind': 'stretch', 'knuckles': False},
     'the rubber mask pulled off'),
]
DEDUP_S = 2.0                                             # an ADD row yields to a picture cue of its sound this close
# a picture cue of these names closer than this to the last one of the same name is a doubled tick: dropped
DOUBLE_S = {'light_switch': 0.3, 'porch_light': 0.3, 'leg_click': 0.09, 'door_tap': 0.25,
            'furnace_die': 1.5}   # sound fix: leg clicks 60 ms apart were doubles (minor 6); the furnace died twice (11)

# picture name -> (recipe, extra params, gain or None, why); None drops the cue
PICTURE = {
    # the motif and every sung line are not SFX: the score's identity layer and the voice track carry them
    'chime': None, 'jingle': None, 'music_box': None, 'humming': None, 'singing': None, 'song': None, 'hum': None,
    # the August heat: wind / cold names from the earlier films land on the August night
    'wind': ('august_night', {}, None, 'the August night'), 'cold_night': ('august_night', {}, None, 'the August night'),
    'house_hum': ('room_tone_house', {}, None, 'no furnace in August'),
    # THIS film's picture names (full mix 1): every name the picture writes, mapped on purpose
    'laugh': None, 'sigh': None,           # Dad's laugh / sigh are in his voice take: no canned laugh or sigh
    'crawl_thump': None,                   # the wall_crawl recipe (from 'scuttle') carries the hand and knee thumps
    'scuttle': ('wall_crawl', {'speed': 1.3}, None, 'the crawl inside the wall, fast'),
    'box_set': ('box_drop', {}, -14.0, 'the GONE FOREVER box set on the top shelf'),
    'switch_click': None,                  # a doubled tick: the picture's light_switch 0.25 s before is the flip
    'rubber_peel': ('glove_squeak', {'kind': 'stretch', 'knuckles': False}, None, 'the rubber mask pulled off'),
    'pipe_knock': ('knock_door', {'n': 3, 'force': 0.5}, None, 'the pipes knock, inside the wall'),
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


ROOM = {'house_night': ('august_night', {}, 0.0), 'night_in': ('august_night', {}, 0.0),
        'night_out': ('august_night', {'inside': False}, 0.0), 'house_powered': ('room_tone_house', {}, 0.0),
        'house_day': ('room_tone_house', {}, 0.0), 'morning': ('room_tone_house', {}, -3.0)}
SPACE_MAP = {'wall': 'in_wall', 'vent': 'vent'}
# recipes whose transient sits off the picture's frame by a fixed amount (filled by measure_mix.py on the first mix)
SHIFT = {}                          # the Walls film: filled from the first full mix
# sound fix round (critic minor 10): the cast's walk cycles emit wooden steps for every space; outdoors they are snow
INDOOR_STEPS = ('footsteps_wood_inside', 'footsteps_hall', 'footsteps_stairs')
OUTDOOR_SPACES = ('outside', 'snow', 'yard', 'street', 'cold_street', 'porch')
STEP_NAMES = ('footsteps_grass', 'footsteps_porch', 'footsteps_wood_inside', 'footsteps_hall')
STACK_S = 0.04
# OFF_WORDS (minors 6-8): (recipe names, from, to, why): their transients move off the spoken words into the gaps
VO_PATH = os.path.join(MP.W, 'align', 'vo_en.wav')
OFF_MAX = 0.45
ON_WORD_DB = {'impact_hit': -6.0}
OFF_WORDS = [
    (('deadbolt_slow', 'deadbolt', 'lock_turn'), 'And I watched the deadbolt', 'end:Click.', 'the bolt\'s click before "Click."'),
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
        if c.get('name') in INDOOR_STEPS and c.get('space') in OUTDOOR_SPACES:      # wood steps outdoors: the lawn
            q = {k: v for k, v in (c.get('params') or {}).items() if k in ('n', 'rate', 'dur')}
            c = dict(c, name='footsteps_grass', params=q, space='outside')
            why = (why + '; ' if why else '') + 'an indoor step outdoors -> a step on the August lawn'
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
