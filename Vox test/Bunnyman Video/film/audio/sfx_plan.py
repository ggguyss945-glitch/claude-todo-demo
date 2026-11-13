"""sfx_plan.py: the final mix's sound-design pass over the picture's SFX cue sheet (the Bunnyman film).

film.py writes W/cues/sfx_cues.json from the picture: every drawn action at its frame. That sheet stays the source
and its timings are never moved (they are the picture's sync). This pass, applied by mix.py with `--plan full`
(audio/final_mix.sh), only
  1. re-levels picture cues that measure buried or too busy in the full-length checks (EDIT: empty until those
     checks are run on this film),
  2. adds the sounds the picture does not draw (ADD): the beds of every place (the woods at night, the house, the
     attic bulb, the bathroom, the dawn, the hospital), the off-screen sounds the narration hears (the soft tap at
     midnight, the egg rattling on the mat, the knocks, the window exploding in the kitchen, the back door, the drag,
     the hatchet on the stairs, the fight in the hall, the key from outside, the sirens), and the small foley of
     close-ups (the peephole, the egg, the ring, the diary's lock and pages, the light switch, the zipper).
     An ADD row is skipped when the picture's sheet already has a cue of that name within 1.5 s of it (the picture
     wins: no doubled sounds).
Every added cue is anchored to the narration (music_plan.resolve: 'sN' / 'eN' / 'wN:word' +- s, or seconds), so it
follows the recording, not a shot list, and survives picture changes. The 8 sound tests (audio/sfx_tests.py) use
the same cues.

    apply(cues, lines) -> (cues, log)      cues: the picture's list (not modified); log: what changed, one line each
    python3 sfx_plan.py [--cues W/cues] [--table]     prints the pass (dry run)
"""
import copy, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import music_plan as MP                                   # noqa: E402

# --------------------------------------------------------------------------------------------- EDIT (picture cues)
# (name, t0, t1, match params (subset), change, why). t0 / t1: anchors or seconds (the window the cue's t falls in).
# change: {'add_db': x} | {'gain_db': x} | {'min_db': x} (raise to at least x) | {'params': {...}} | {'drop': True}
EDIT = []

THIN_MIN_GAP = 0.26                                       # (the dummy film's jaw ticks: no such cues in this film)
THIN_GAIN = {'tv': -13.0, None: -10.0}
THIN_QUIET = []

# --------------------------------------------------------------------------------------------- ADD
# (anchor, name, gain_db, space, params, why). params 'dur': 'until:<anchor>' -> seconds to that anchor.
ADD = [
    # ---- cold open: the treeline at night, the 1987 tape, the hospital
    ('s0', 'ambience_woods', 2.0, 'porch', {'dur': 'until:e2+0.4', 'owl': 0.7, 'wind': 0.5}, 'the edge of the woods'),
    ('s0+5.3', 'owl_hoot', -2.0, 'woods', {}, 'an owl in the trees'),
    ('e2+0.1', 'tape_glitch', 2.0, 'tv', {'kind': 'tracking', 'dur': 0.35}, 'into the 1987 tape (the VHS jingle)'),
    ('s7+1.55', 'tape_glitch', -5.0, 'tv', {'kind': 'stop', 'dur': 0.7}, 'the tape stops'),
    ('s7+1.9', 'ambience_woods', 0.0, 'window', {'dur': 'until:s16', 'owl': 0.4, 'wind': 0.4}, 'the night again'),
    ('s12', 'room_tone_house', 0.0, None, {'dur': 'until:s16', 'hum': 0.25}, 'the rules on the fridge: the house'),
    ('s16', 'hospital_room', 0.0, None, {'dur': 'until:s19'}, '"I\'m telling you this from a hospital."'),
    # ---- 1987
    ('w24:photo+0.15', 'flash_pop', -2.0, 'close', {'memory': True}, '"There\'s a photo from that morning."'),
    ('s29', 'ambience_woods', 0.0, 'porch', {'dur': 'until:s32', 'owl': 0.4, 'wind': 0.6}, 'Holloway Woods, 1987'),
    ('s31+0.4', 'dogs_search', 2.0, 'woods', {'dur': 5.0}, '"The search dogs lost her scent..."'),
    ('s32', 'ambience_dawn', -4.0, 'porch', {'dur': 'until:s36', 'birds': 0.5}, 'sunrise on Easter morning, 1987'),
    ('s36', 'ambience_woods', -2.0, 'porch', {'dur': 'until:s45', 'owl': 0.5, 'wind': 0.6}, 'the sightings'),
    # ---- the house, Dad, June
    ('s45', 'room_tone_house', 0.0, None, {'dur': 'until:s61', 'hum': 0.25}, 'the last house on Orchard Road'),
    ('s45', 'ambience_woods', -4.0, 'outside', {'dur': 'until:s61', 'owl': 0.2}, 'the woods behind it'),
    ('w46:porch+0.2', 'light_switch', 0.0, 'close', {'kind': 'porch'}, 'Grandma left the porch light on'),
    ('w47:switched+0.15', 'light_switch', 0.0, 'close', {'kind': 'porch_off'}, 'Mom switched it off'),
    ('w48:flashlight', 'flashlight_click', -4.0, 'porch', {'kind': 'on'}, 'Dad\'s flashlight'),
    ('s60+0.3', 'fridge_paper', 0.0, 'close', {}, '"At sundown, the rules went up on the fridge."'),
    # ---- rule 1
    ('w62:lock+0.1', 'lock_turn', -2.0, 'inside', {}, '"Lock every door at sundown."'),
    ('s61', 'room_tone_house', 0.0, None, {'dur': 'until:s92', 'hum': 0.25}, 'the house at night'),
    ('s61', 'house_creaks', -2.0, None, {'dur': 'until:s92', 'density': 0.08}, 'the house settling'),
    ('s61', 'ambience_woods', 0.0, 'outside', {'dur': 'until:s70+0.5', 'owl': 0.3, 'wind': 0.4}, 'outside, shut out'),
    ('s70', 'ambience_woods', 2.0, 'window', {'dur': 'until:s92', 'owl': 0.6, 'wind': 0.5}, 'June\'s open window'),
    ('w69:curtains+0.1', 'curtain_close', 0.0, None, {'dur': 1.1}, '"I close the curtains downstairs"'),
    ('w69:curtains+1.6', 'curtain_close', -2.0, None, {'dur': 0.9}, 'the second window'),
    ('w69:run+0.05', 'footsteps_wood_inside', -2.0, None, {'stairs': True, 'run': True, 'direction': 'up', 'n': 7},
     '"then run up to June\'s room"'),
    ('s70-0.6', 'door_creak', -4.0, None, {'dur': 1.0}, 'June\'s door'),
    ('s73+0.8', 'owl_hoot', -3.0, 'woods', {}, 'the owl while he stands there'),
    ('s87-0.35', 'wood_creak', -4.0, 'inside', {'kind': 'creak', 'dur': 0.6}, 'the board behind us ("I turn around.")'),
    # ---- the comment prompt: the tape is paused
    ('s92-0.05', 'vhs_pause', 0.0, None, {'kind': 'pause', 'dur': 'until:s100-0.25'}, 'the VHS pause'),
    ('s100-0.25', 'vhs_pause', 0.0, None, {'kind': 'play'}, 'play: "Rule number two."'),
    # ---- rule 2
    ('s100', 'room_tone_house', 0.0, None, {'dur': 'until:s130', 'hum': 0.25}, 'the house'),
    ('s100', 'old_clock', -3.0, None, {'dur': 'until:s109', 'bpm': 60}, 'midnight'),
    ('s100', 'ambience_woods', -2.0, 'outside', {'dur': 'until:s109', 'owl': 0.3, 'wind': 0.3}, 'outside'),
    ('w104:tap+0.05', 'egg_tap', 0.0, None, {}, '"...one soft tap on the front door."'),
    ('s105+0.35', 'peephole', 0.0, None, {}, '"Through the peephole"'),
    ('s109-0.2', 'ambience_woods', -4.0, 'porch', {'dur': 'until:s113', 'owl': 0.2}, 'the backyard (memory)'),
    ('w109:carries+0.1', 'oven_mitt', -2.0, None, {'dur': 1.4}, 'in oven mitts'),
    ('w109:fire-0.4', 'burn_barrel', 2.0, None, {'dur': 'until:s113+0.6', 'ignite': True}, '"...and sets it on fire"'),
    ('s112+0.3', 'plastic_melt', 2.0, None, {'dur': 2.6}, '"They smell sweet when they melt."'),
    ('s113', 'ambience_woods', -2.0, 'outside', {'dur': 'until:s130', 'owl': 0.3, 'wind': 0.3}, 'outside again'),
    ('w114:rattles+0.12', 'egg_rattle', 2.0, 'outside', {'dur': 1.5}, '"...the egg rattles."'),
    ('s116+0.25', 'door_creak', -2.0, None, {'dur': 1.4, 'slow': 1.3}, '"I open the door."'),
    ('s117+0.1', 'chain_lock', -6.0, None, {'kind': 'rattle'}, '"Just a crack."'),
    ('w118:egg+0.05', 'egg_open', 2.0, None, {}, '"And I open the egg."'),
    ('w119:rolling', 'ring_roll', 2.0, None, {'dur': 2.0}, '"Inside, rolling around, is a gold ring."'),
    ('s126+0.2', 'footsteps_wood_inside', -4.0, None, {'stairs': True, 'direction': 'down', 'n': 6, 'rate': 1.4},
     'Mom comes down the stairs'),
    ('w127:takes+0.05', 'ring_hand', 0.0, None, {'kind': 'take'}, '"takes the ring out of my hand"'),
    ('w129:pocket', 'ring_hand', 2.0, None, {'kind': 'pocket'}, '"She puts it in her pocket."'),
    # ---- rule 3
    ('s130', 'room_tone_house', 0.0, None, {'dur': 'until:s160', 'hum': 0.25}, 'the house'),
    ('s130', 'old_clock', -3.0, None, {'dur': 'until:s160', 'bpm': 60}, '1:13'),
    ('s130', 'ambience_woods', -4.0, 'outside', {'dur': 'until:s160', 'owl': 0.2, 'wind': 0.3}, 'outside'),
    ('e135+0.08', 'knock_family', 2.0, 'inside', {'groups': 'gaps:e135+0.08,e137+0.03,e139+0.02'},
     'the 2-3-2 knock in the narration\'s gaps ("Two knocks. A pause. Three more. A pause. Two.")'),
    ('w147:knock+0.35', 'knock_family', -2.0, 'close', {'soft': True, 'memory': True, 'beat': 0.42},
     'Grandma taps it on her kitchen table'),
    ('s155-0.05', 'knock_family', 0.0, 'inside', {'soft': True, 'groups': 'gaps:s155-0.05,s156-0.5,s157-0.53'},
     '"Two. Three. Two." recalled'),
    # ---- rule 4
    ('s160', 'room_tone_house', 0.0, None, {'dur': 'until:s196', 'hum': 0.25}, 'the house'),
    ('s160', 'ambience_woods', -4.0, 'outside', {'dur': 'until:s196', 'owl': 0.2, 'wind': 0.3}, 'outside'),
    ('w164:creaks-0.2', 'slot_flap', 0.0, None, {'action': 'open'}, 'the brass flap creaks open'),
    ('s180+1.4', 'footsteps_stairs', -6.0, None, {'direction': 'down', 'n': 6, 'rate': 1.2, 'weight': 0.3},
     'June creeps down the stairs in her socks'),
    ('w180:kneels', 'cloth_rustle', -4.0, None, {'kind': 'rustle'}, 'she kneels at the slot'),
    ('s192+0.35', 'slot_flap', 2.0, None, {'action': 'snap'}, '"Mom closes the mail slot."'),
    ('w193:smooths', 'cloth_rustle', -2.0, None, {'kind': 'rustle'}, 'she smooths June\'s hair'),
    # ---- rule 5
    ('s196', 'room_tone_house', 0.0, None, {'dur': 'until:s206', 'hum': 0.25}, 'the house'),
    ('s200-0.4', 'clock_tick', -6.0, 'inside', {'dur': 3.0}, '"At 2:47, I wake up."'),
    ('w201:blanket', 'cloth_rustle', -4.0, None, {'kind': 'rustle'}, 'June\'s blanket'),
    ('s205', 'bulb', -6.0, 'inside', {'kind': 'buzz', 'dur': 'until:s206'}, 'the light under the attic door'),
    ('s206-0.9', 'attic_door', 0.0, 'inside', {'action': 'open'}, 'the attic door'),
    ('s206', 'bulb', -2.0, 'attic', {'kind': 'buzz', 'dur': 'until:s232'}, 'the attic\'s bare bulb'),
    ('s206', 'room_tone_house', -4.0, 'attic', {'dur': 'until:s232', 'hum': 0.1}, 'the attic'),
    ('w207:dress', 'cloth_rustle', -6.0, 'attic', {'kind': 'rustle'}, 'the tiny yellow dress'),
    ('w208:lock', 'diary_lock', 0.0, 'attic', {}, '"a diary with a pink plastic lock"'),
    ('s210', 'page_flip', 0.0, 'attic', {'n': 1}, '"The first half is crayon."'),
    ('s215', 'page_flip', 0.0, 'attic', {'n': 2, 'rate': 2.5}, '"Then Easter, 1987."'),
    ('s219', 'page_flip', -2.0, 'attic', {'n': 4, 'rate': 1.6}, '"page after page"'),
    ('s224', 'page_flip', 0.0, 'attic', {'n': 1}, '"And on the very last page"'),
    ('s229+0.4', 'wood_creak', -6.0, 'attic', {'kind': 'creak', 'dur': 0.8}, 'Mom in the dark corner'),
    # ---- rule 6
    ('s232', 'room_tone_house', 0.0, None, {'dur': 'until:s242', 'hum': 0.25}, 'the house'),
    ('s232', 'ambience_woods', -4.0, 'outside', {'dur': 'until:s242', 'owl': 0.0, 'wind': 0.4}, 'outside'),
    ('w236:explodes', 'window_smash', 0.0, None, {}, '"...the kitchen window explodes."'),
    ('w237:crashes', 'door_crash', 0.0, None, {}, '"The back door crashes open."'),
    ('s238+0.2', 'wet_drag', 0.0, None, {'dur': 'until:e240+0.6'}, '"Something heavy comes inside. Wet. Dragging."'),
    ('s241+0.35', 'cloth_rustle', -2.0, None, {'kind': 'grab'}, '"I grab June"'),
    ('w241:run', 'footsteps_wood_inside', 0.0, None, {'run': True, 'n': 6}, '"and run."'),
    ('s242+0.35', 'attic_door', -2.0, 'close', {'action': 'close'}, 'the bathroom door shut'),
    ('s243+0.05', 'lock_turn', 2.0, 'close', {}, '"Lock."'),
    ('s242', 'room_tone_house', -2.0, 'bathroom', {'dur': 'until:s286', 'hum': 0.2}, 'the dark bathroom'),
    ('s244+1.2', 'bathtub', 0.0, None, {'kind': 'settle'}, 'in the empty bathtub'),
    ('w244:hand+0.1', 'breath', -6.0, None, {'kind': 'held', 'dur': 2.0}, 'my hand over her mouth'),
    ('s245+0.3', 'hatchet_step', 0.0, None, {'n': 4, 'rate': 0.8}, '"Footsteps on the stairs. Slow."'),
    ('s248-0.3', 'hatchet_step', 2.0, None, {'n': 1}, '"Thunk." (the head lands on the word)'),
    ('s249-0.3', 'hatchet_step', 2.0, None, {'n': 1}, '"Thunk."'),
    ('s250+0.6', 'hatchet_step', 0.0, None, {'n': 2, 'rate': 0.8}, 'up to the landing'),
    ('w251:turns-0.2', 'doorknob', 2.0, None, {'kind': 'turn'}, '"The doorknob turns. Gently."'),
    ('s257+0.35', 'paper_under_door', 2.0, None, {'dur': 1.3}, '"Something slides under the door."'),
    ('s270', 'struggle', 0.0, None, {'kind': 'shake'}, '"The whole hallway shakes."'),
    ('s271+1.0', 'struggle', 2.0, None, {'kind': 'slam'}, '"Something slams into the bathroom door."'),
    ('s272', 'struggle', -4.0, None, {'kind': 'wall'}, '"Screaming."'),
    ('w273:crack+0.05', 'struggle', 0.0, None, {'kind': 'crack'}, '"A wet, heavy crack."'),
    # ---- rule 7
    ('s286', 'ambience_dawn', -6.0, 'outside', {'dur': 'until:s313', 'birds': 0.5}, 'the dawn birds outside'),
    ('s289+1.0', 'knock_door', 0.0, 'door', {'soft': True, 'n': 3}, '"Mom knocks, softly."'),
    ('w297:turns-0.6', 'key_outside', 2.0, None, {}, '"The lock turns by itself. From the outside."'),
    ('s300', 'room_tone_house', 0.0, None, {'dur': 'until:s322', 'hum': 0.2}, 'the wrecked hall'),
    ('w313:kneels', 'cloth_rustle', -4.0, None, {'kind': 'rustle'}, 'Mom kneels with the dress'),
    ('w313:hand+0.2', 'cloth_rustle', -8.0, None, {'kind': 'rustle'}, 'her hand over June\'s eyes'),
    ('w355:pull', 'cloth_rustle', 0.0, None, {'kind': 'grab'}, '"I pull June\'s face out"'),
    ('w355:push+0.1', 'cloth_rustle', -2.0, None, {'kind': 'grab'}, '"and push my own face into it"'),
    # ---- after
    ('s360+0.1', 'tinnitus', -6.0, None, {'dur': 4.0}, '"When I open my eyes..."'),
    ('s370+0.3', 'sirens_arrive', 0.0, 'street', {'dur': 9.0}, '"When the police came"'),
    ('s371', 'hospital_room', 0.0, None, {'dur': 'until:s386'}, 'Holloway State Hospital'),
    ('s376', 'hospital_corridor', -8.0, None, {'dur': 'until:s386', 'busy': 0.2}, 'the visiting room\'s corridor'),
    # ---- the outro
    ('w388:light+0.25', 'light_switch', 0.0, 'close', {'kind': 'wall'}, '"You can turn a light on now."'),
    ('w395:zipper+0.1', 'zipper', -2.0, 'close', {'dur': 1.0}, '"It has a zipper in the back"'),
]
DEDUP_S = 1.5                                             # an ADD row yields to a picture cue of its name this close


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


def apply(cues, lines):
    """The picture's cue list -> the mixed cue list (a new list) and a log of every change."""
    out = [copy.deepcopy(c) for c in cues if isinstance(c, dict)]
    log = []
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
    have = {}
    for c in out:
        try:
            have.setdefault(str(c.get('name')), []).append(float(c['t']))
        except (KeyError, TypeError, ValueError):
            pass
    for a, name, g, space, params, why in ADD:
        try:
            t = _t(a, lines)
            p = dict(params)
            if isinstance(p.get('dur'), str) and p['dur'].startswith('until:'):
                p['dur'] = round(max(0.3, _t(p['dur'][6:], lines) - t), 2)
            if isinstance(p.get('groups'), str) and p['groups'].startswith('gaps:'):
                gs = [_t(x, lines) for x in p['groups'][5:].split(',')]
                p['groups'] = [round(x - gs[0], 3) for x in gs]
        except Exception as e:
            log.append(f'ADD {name} at {a}: bad anchor ({e!r}): skipped'); continue
        if any(abs(t - x) < DEDUP_S for x in have.get(name, [])):
            log.append(f'ADD  {name:18s} {t:7.2f} skipped: the picture already has it'); continue
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
