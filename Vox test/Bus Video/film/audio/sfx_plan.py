"""sfx_plan.py: the final mix's sound-design pass over the picture's SFX cue sheet ("If The School Bus Stops At
Midnight... DON'T GET ON").

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
    # first full mix: the walks sat 18-22 LU under the voice + music (masked)
    ('footsteps_wood_inside', 0.0, 1e4, {}, {'add_db': 3.0}, 'house steps masked (18-22 LU under)'),
    ('footsteps_grass', 0.0, 1e4, {}, {'add_db': 3.0}, 'lawn steps masked (18-20 LU under)'),
]
THIN_MIN_GAP = 0.26                                       # (the dummy film's jaw ticks: no such cues in this film)
THIN_GAIN = {'tv': -13.0, None: -10.0}
THIN_QUIET = []

# --------------------------------------------------------------------------------------------- ADD
# (anchor, name, gain_db, space, params, why). params 'dur': 'until:<anchor>' -> seconds to that anchor.
ADD = [
    # ---- Grandma Della and bus 9 (warm, never a threat)
    ('s27-0.3', 'morning_bus', -4.0, None, {'dur': 'until:e28+0.4', 'kids': 0.5},
     'bus 9 in the morning: every kid gets a good morning, by name'),
    # ---- rule 6: the call goes through
    ('e249+0.1', 'dial_911', -8.0, 'close', {'kind': 'call'}, '"Call 911.": the keys, one ring, the operator picks up'),
    # ---- after the bell: the real adults arrive
    ('s371', 'siren_far', -12.0, 'outside', {'dur': 'until:s376', 'dist': 1.0}, 'the officers coming to the school lot'),
    # ---- the morning
    ('s386', 'ambience_dawn', -8.0, 'window', {'dur': 'until:s389', 'birds': 0.6}, 'the morning at home: birds'),
    ('s389-0.4', 'morning_bus', -4.0, None, {'dur': 'until:e396+0.5', 'kids': 0.4}, 'bus 9, the new girl in seat 21'),
]
DEDUP_S = 2.0                                             # an ADD row yields to a picture cue of its sound this close

# picture name -> (recipe, extra params, gain or None, why); None drops the cue
PICTURE = {
    'neck_tick': ('wood_creak', {'kind': 'tick', 'dur': 0.15}, None, 'his neck, one tick'),
    'neck_ratchet': ('wood_creak', {'kind': 'grind', 'dur': 1.1}, -2.0, 'his head turning all the way round'),
    'bus_rumble': ('bus_idle', {'kind': 'bus9', 'rattle': 0.3}, -10.0, 'the 1994 tape\'s bus'),
    'cart_squeak': ('wheelchair', {}, -12.0, 'the TV cart rolled in'),
    'vcr_insert': ('vhs_tape', {'action': 'insert'}, -4.0, 'the tape into the VCR'),
    'tape_warble': ('tape_glitch', {'kind': 'warble'}, None, 'the tape warbles'),
    'tape_slowdown': ('tape_slide', {}, -4.0, 'the voice slides down like a slowing tape'),
    'vhs_noise': ('tape_glitch', {'kind': 'tracking'}, -8.0, 'snow after the tape'),
    'like_pop': ('ui_pop', {}, -14.0, 'the likes on the post'),
    'tape_press': ('touch_tap', {}, -10.0, 'the tape pressed flat on the door'),
    'fabric_turn': ('cloth_rustle', {}, -10.0, 'the backpack turned to the wall'),
    'loudspeaker_crackle': ('pa_crackle', {'kind': 'on'}, -4.0, 'his loudspeaker comes on'),
    'loudspeaker_click': ('pa_crackle', {'kind': 'on'}, -4.0, 'over the loudspeaker'),
    'ws_unfold_clack': ('his_unfold', {'n': 1}, None, 'one joint of him unfolding, like a ladder'),
    'clipboard_lift': ('clipboard', {}, -8.0, 'his clipboard'),
    'hand_slap': ('cloth_rustle', {'kind': 'grab', 'dur': 0.6}, -2.0, 'my hand slaps over his mouth'),
    'paper_slide': ('paper_under_door', {'dur': 1.0}, -2.0, 'the yellow ticket under the door'),
    'dial_beep': ('touch_tap', {}, -10.0, 'a key on the phone'),
    'call_fail': ('dial_911', {'kind': 'fail'}, -6.0, 'no bars: the call drops'),
    'keys_jingle': ('keys_jangle', {}, -6.0, 'Grandma grabs her keys'),
    'door_open': ('doorknob', {'kind': 'turn'}, -6.0, 'the back door'),
    'door_creak_open': ('door_creak', {'dur': 1.2}, -6.0, 'Grandma\'s door opens on the hallway'),
    'glass_pound': ('knock_door', {'n': 1, 'force': 0.8}, None, 'Grandma\'s fists on bus 9\'s glass doors, across the yard'),
    'skin_slide': ('hand_squeeze', {}, -6.0, 'a small hand slides into mine'),
    'kid_laugh_far': ('owen_giggle', {}, -12.0, 'Sami laughing upstairs'),
    'phone_light_click': ('flashlight_click', {}, -6.0, 'the phone light on'),
    'deadbolt_slide': ('deadbolt', {}, 0.0, 'the deadbolt slides'),
    'hat_crumple': ('cloth_rustle', {'kind': 'grab', 'dur': 0.5}, -6.0, 'the hat crushed on the ceiling'),
    'glove_slap_wall': ('knock_door', {'n': 1, 'force': 0.55, 'soft': True}, -2.0, 'a glove slaps the wall'),
    'lights_blink': ('lamp_flicker', {'dur': 0.4, 'buzz': 0.4}, -6.0, 'the lights blink'),
    'hand_slip': ('cloth_rustle', {'dur': 0.5}, -4.0, 'Sami\'s hand slips out of mine'),
    'bus_door_fold': ('bus_door', {'action': 'open'}, None, 'his bus doors fold open'),
    'bus_door_spring': ('bus_door', {'action': 'open'}, None, 'bus 9\'s doors spring open'),
    'door_slap': ('bus_door',{'action': 'close', 'slap': 1.0}, 2.0, 'his doors slap shut an inch from my fingers'),
    'broom_clatter_in': ('wood_knock', {'n': 2, 'spacing': 0.14}, -6.0, 'the broom tossed in, clattering'),
    'bus_drive': ('bus9_drive', {'speed': 'fast'}, -4.0, 'bus 9 on the night road'),
    'engine_start_bus': ('bus9_start', {}, -2.0, 'bus 9 starts'),
    'engine_rev_bus': ('bus_pull_away', {}, 0.0, 'Grandma hits the gas'),
    'metal_rip': ('mirror_rip', {}, 2.0, 'his bumper rips our side mirror off'),
    'amber_hum': None,                                    # his doors' amber light: the score's bed carries it
    'body_catch': ('cloth_rustle', {'kind': 'grab'}, -2.0, 'he tumbles into my arms'),
    'arm_stretch_creak': ('wood_creak', {'kind': 'grind', 'dur': 2.0}, -6.0, 'his arm stretching down the aisle'),
    'door_motor': ('bus_door', {'action': 'close', 'slap': 0.0}, -2.0, 'the doors start folding shut'),
    'wood_crack': ('broom_crack', {}, 2.0, 'the broom cracks'),
    'door_slam_bus': ('bus_door', {'action': 'close', 'slap': 1.0}, 2.0, 'the doors slam on an empty aisle'),
    'paper_flip': ('page_flip', {}, -6.0, 'his clipboard\'s pages'),
    'pencil_line': ('pen_scratch', {'dur': 1.6}, -6.0, 'a line through one name'),
    'marker_write': ('pen_scratch', {'dur': 2.0}, -6.0, 'rule eight written under Grandma\'s seven'),
    'marker_x': ('marker_strike', {}, -4.0, 'the 1994 tape crossed out'),
    'paper_flutter': ('paper', {'dur': 0.6}, -12.0, 'the rules paper'),
    'typing': None,                                       # the rules are handwritten: the paper and the sting carry it
    'room_tone_drop': None,                               # the power_down cue is the moment; the dead tone follows
    'ui_pop': ('ui_pop', {}, -9.0, 'card pops, under the voice'),
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
                  'hatchet_step'):
            n = float(p.get('n') or (4 if cn == 'hatchet_step' else 1))
            r = float(p.get('rate') or (0.75 if cn == 'hatchet_step' else 1.8))
            return max(0.0, (n - 1) / r + (0.3 if cn == 'hatchet_step' else 0.0))
        if p.get('dur') and cn in ('struggle', 'wet_drag', 'paper_under_door', 'ambience_woods', 'ambience_dawn',
                                   'ambience_night', 'room_tone', 'room_tone_house', 'burn_barrel', 'bulb', 'dogs_search',
                                   'crowd_parade', 'hospital_room', 'hospital_corridor', 'house_creaks', 'old_clock',
                                   'house_night', 'waiting_room', 'drive_rain', 'halverson_car', 'er_bustle',
                                   'office_3am', 'rain_house', 'streetlight', 'breath', 'line_hiss',
                                   'morning_bus', 'bus9_drive', 'bus_idle', 'siren_far', 'suburb_night', 'tape_hiss'):
            return float(p['dur'])
    except (TypeError, ValueError):
        pass
    return 0.0


ROOM = {'house_night': ('house_night', {'fridge': 0.6, 'clock': 0.6, 'creaks': 0.3}, 0.0),
        'house_evening': ('house_night', {'fridge': 0.5, 'clock': 0.3, 'creaks': 0.2}, -4.0),
        'house_dead': ('house_night', {'fridge': 0.0, 'clock': 0.6, 'creaks': 0.4}, 0.0),   # the power is out
        'morning': ('house_night', {'fridge': 0.5, 'clock': 0.2, 'creaks': 0.0}, -4.0)}
SPACE_MAP = {'classroom': 'inside'}
# first full mix (measure_mix.py): these recipes' transients sat off the picture's frame by a fixed amount
# (bus_door open -183 ms, his_unfold +200 ms, broom_bend +350 ms, tire_screech +126 ms, bus_pull_away +95 ms): the
# cue moves by the opposite so the transient lands on the frame
SHIFT = {'bus_door_fold': 0.18, 'bus_door_spring': 0.18, 'ws_unfold_clack': -0.2, 'broom_rip': -0.34, 'broom_jam': -0.34,
         'tyre_screech': -0.12, 'engine_rev_bus': -0.09, 'bus_pull_away': -0.09}


def picture_pass(out, lines, log):
    """PICTURE: film.py's names onto this film's recipes; what another layer carries is dropped."""
    res, n0 = [], len(out)
    skips = [float(c['t']) for c in out if c.get('name') == 'tape_skip']
    last = {}                                             # name -> last kept t (doubled ticks)
    first_letter = True
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
        if nm == 'vhs_glitch' and any(abs(t - s) < 0.15 for s in skips):
            log.append(f'PIC  vhs_glitch         {t:7.2f} dropped: the tape_skip on this frame plays it'); continue
        if nm in ('glove_slap_wall', 'neck_ratchet') and t - last.get(nm, -9.0) < 0.6:
            log.append(f'PIC  {nm:18s} {t:7.2f} dropped: doubled ({t - last[nm]:.2f} s after the last)'); continue
        last[nm] = t
        if nm == 'bus_ambience':
            log.append(f'PIC  bus_ambience       {t:7.2f} dropped: the ADD morning_bus bed carries bus 9\'s mornings')
            continue
        if nm == 'room_tone' and p.get('kind') in ROOM:
            rn, extra, g = ROOM[p['kind']]
            q = dict(extra); q['dur'] = p.get('dur', 10.0)
            c = dict(c, name=rn, params=q, gain_db=float(c.get('gain_db', 0.0) or 0.0) + g)
            why = f'room tone {p["kind"]} -> {rn}'
        elif nm == 'letter_clink':
            if first_letter:                              # the first letter: the screw backing out, then the tink
                first_letter = False
                c = dict(c, t=round(t - 0.75, 3), name='mailbox_unscrew', params={'n': 1}, gain_db=-6.0)
                why = 'Grandma unscrews the first letter (the tink on the picture\'s frame)'
            else:
                c = dict(c, name='spoon_clink', params={'n': 1}, gain_db=-14.0); why = 'a tin letter comes off'
        elif nm == 'glass_pound':
            g = float(c.get('gain_db', 0.0) or 0.0) - 4.0
            c = dict(c, name='knock_door', params={'n': 1, 'force': 0.8}, gain_db=g, space='street')
            why = 'Grandma\'s fists on bus 9\'s glass doors, across the yard'
        elif nm == 'tape_rewind':
            if p.get('dur'):
                c = dict(c, name='tape_glitch', params={'kind': 'warble', 'dur': p['dur']}); why = 'the tape slips'
            else:
                c = dict(c, name='bus_rewind', params={}); why = 'the bus rewinds into the dark'
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
        if why:
            log.append(f'PIC  {nm:18s} {t:7.2f} -> {c["name"]} {c.get("params")} {c.get("gain_db", 0):+.1f} dB  ({why})')
        res.append(c)
    log.append(f'PICTURE: {n0} picture cues -> {len(res)}')
    return res


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
