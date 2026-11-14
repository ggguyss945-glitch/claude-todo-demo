"""sfx_plan.py: the final mix's sound-design pass over the picture's SFX cue sheet (the Bunnyman film).

film.py writes W/cues/sfx_cues.json from the picture: every drawn action at its frame. That sheet stays the source
and its timings are never moved (they are the picture's sync). This pass, applied by mix.py with `--plan full`
(audio/final_mix.sh), only
  0. maps the picture's names onto this film's recipes (PICTURE, the final mix: film.py names some sounds the recipes
     know by other names or not at all, e.g. footsteps_grass, hatchet_thunk, mail_slot, count_thump, hum), drops the
     picture's cues that another layer already carries (its 'hum' / 'jingle' / 'count_thump' cues where the score's
     identity layer plays that version: music_plan.IDENTITY), and drops the library scream the owner rejected,
  1. re-levels picture cues that measure buried or too busy in the full-length checks (EDIT: empty until those
     checks are run on this film),
  2. adds the sounds the picture does not draw (ADD): the beds of every place (the woods at night, the house, the
     attic bulb, the bathroom, the dawn, the hospital), the off-screen sounds the narration hears (the soft tap at
     midnight, the egg rattling on the mat, the knocks, the window exploding in the kitchen, the back door, the drag,
     the hatchet on the stairs, the fight in the hall, the key from outside, the sirens), and the small foley of
     close-ups (the peephole, the egg, the ring, the diary's lock and pages, the light switch, the zipper).
     An ADD row is skipped when the picture's sheet already has a cue of the same sound within 2 s of it (the same
     recipe after resolving, or the same FAMILY: knock_door / knock_family, mail_slot / slot_flap, the lock and key
     sounds, footsteps and hatchet treads...; the picture wins: no doubled sounds). A row with 'snap': name moves onto
     the picture's nearest cue of that name (within 1.2 s).
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
EDIT = [
    # the porch switch inserts: Grandma's fingertip pushes it up (on), Mom's pushes it down (off); film.py gives no kind
    ('light_switch', 's46-0.5', 's46+1.5', {}, {'params': {'kind': 'porch'}}, 'Grandma: the porch light on'),
    ('light_switch', 's47-0.5', 'e47', {}, {'params': {'kind': 'porch_off'}}, 'Mom: the porch light off'),
    # the attic's bare bulb under the whole attic scene: present, not a hum you notice (-14 was 26 LU under the voice)
    ('bulb', 's206-0.5', 's206+0.5', {'dur': 4.0}, {'drop': True}, 'a second bulb buzz on the first one'),
    ('bulb', 's206-0.5', 's206+0.5', {'kind': 'buzz'}, {'gain_db': -8.0}, 'the attic bulb'),
    # the first full mix (measure_mix.py): buried cues raised, cues over the narration lowered
    ('paper', 's12', 'e12', {}, {'add_db': 6.0}, 'the laminated rules pressed on the fridge (23 LU under)'),
    ('paper', 's24-0.3', 'e24', {}, {'add_db': 6.0}, 'the Courier (24 LU under)'),
    ('footsteps_grass', 's29-0.3', 's31', {}, {'gain_db': -2.0}, 'the mascot and Laurie walking into the woods (22 LU under)'),
    ('footsteps_wood_inside', 'w69:then-0.2', 's70', {}, {'add_db': 3.0}, 'the run up the stairs (19 LU under)'),
    ('knock_family', 'w337:knocked-0.6', 'w337:waved', {}, {'gain_db': -13.0}, 'her knock under the line (6.5 LU over it)'),
    ('knock_door', 's345', 'e345', {}, {'add_db': 4.0}, 'the recalled count under the line (19 LU under)'),
    ('window_smash', 's236', 'e236+0.3', {}, {'gain_db': 1.0}, '"explodes" stays readable (+1.1 LU over the line)'),
    ('door_crash', 's237', 'e237', {}, {'gain_db': 0.0}, '"crashes open" stays readable (+2 LU over the line)'),
    ('sirens_arrive', 's370-0.5', 'e370', {}, {'add_db': 10.0}, 'the patrol cars arriving (24 LU under)'),
    ('paper', 's323-0.3', 'e323', {}, {'add_db': 4.0}, 'the Courier at the reveal (20 LU under)'),
    ('breath', 's386', 'e387+0.3', {}, {'gain_db': -8.0}, '"Breathe." (masked at -12)'),
    ('knock_door', 's406', 'e406', {}, {'gain_db': -4.0}, 'the like that lands like a knock (5.9 LU over the line)'),
    ('light_switch', 's407-0.3', 'e407', {}, {'gain_db': 0.0}, 'Grandma\'s porch light on at "And subscribe." (19 LU under)'),
]

THIN_MIN_GAP = 0.26                                       # (the dummy film's jaw ticks: no such cues in this film)
THIN_GAIN = {'tv': -13.0, None: -10.0}
THIN_QUIET = []

# --------------------------------------------------------------------------------------------- ADD
# (anchor, name, gain_db, space, params, why). params 'dur': 'until:<anchor>' -> seconds to that anchor.
ADD = [
    # ---- cold open: the treeline at night, the 1987 tape, the hospital
    ('s0', 'ambience_woods', 2.0, 'porch', {'dur': 'until:e2+0.4', 'owl': 0.7, 'wind': 0.5}, 'the edge of the woods'),
    ('s0+5.3', 'owl_hoot', -2.0, 'woods', {}, 'an owl in the trees'),
    ('e2-0.3', 'tape_glitch', 0.0, 'tv', {'kind': 'tracking', 'dur': 1.1, 'keep': True},
     '"don\'t." over black and VHS static, into the 1987 tape (the picture cuts to it at 17.84)'),
    ('s7+1.55', 'tape_glitch', -5.0, 'tv', {'kind': 'stop', 'dur': 0.7}, 'the tape stops'),
    ('s7+1.9', 'ambience_woods', 0.0, 'window', {'dur': 'until:s16', 'owl': 0.4, 'wind': 0.4}, 'the night again'),
    ('s12', 'room_tone_house', 0.0, None, {'dur': 'until:s16', 'hum': 0.25}, 'the rules on the fridge: the house'),
    ('s16', 'hospital_room', 0.0, None, {'dur': 'until:s19'}, '"I\'m telling you this from a hospital."'),
    # ---- 1987
    ('s29', 'ambience_woods', 0.0, 'porch', {'dur': 'until:s32', 'owl': 0.4, 'wind': 0.6}, 'Holloway Woods, 1987'),
    ('s31+0.4', 'dogs_search', 2.0, 'woods', {'dur': 5.0}, '"The search dogs lost her scent..."'),
    ('s32', 'ambience_dawn', -4.0, 'porch', {'dur': 'until:s36', 'birds': 0.5}, 'sunrise on Easter morning, 1987'),
    ('s36', 'ambience_woods', -2.0, 'porch', {'dur': 'until:s45', 'owl': 0.5, 'wind': 0.6}, 'the sightings'),
    # ---- the house, Dad, June
    ('s45', 'room_tone_house', 0.0, None, {'dur': 'until:s61', 'hum': 0.25}, 'the last house on Orchard Road'),
    ('s45', 'ambience_woods', -4.0, 'outside', {'dur': 'until:s61', 'owl': 0.2}, 'the woods behind it'),
    ('w46:porch+0.2', 'light_switch', 0.0, 'close', {'kind': 'porch'}, 'Grandma left the porch light on'),
    ('w47:switched+0.15', 'light_switch', 0.0, 'close', {'kind': 'porch_off'}, 'Mom switched it off'),
    ('s60+0.3', 'fridge_paper', 0.0, 'close', {}, '"At sundown, the rules went up on the fridge."'),
    # ---- rule 1
    ('w62:lock+0.1', 'lock_turn', -2.0, 'inside', {}, '"Lock every door at sundown."'),
    ('s61', 'room_tone_house', 0.0, None, {'dur': 'until:s92', 'hum': 0.25}, 'the house at night'),
    ('s61', 'house_creaks', -2.0, None, {'dur': 'until:s92', 'density': 0.08}, 'the house settling'),
    ('s61', 'ambience_woods', 0.0, 'outside', {'dur': 'until:s70+0.5', 'owl': 0.3, 'wind': 0.4}, 'outside, shut out'),
    ('s70', 'ambience_woods', 2.0, 'window', {'dur': 'until:s92', 'owl': 0.6, 'wind': 0.5}, 'June\'s open window'),
    ('w69:curtains+0.1', 'curtain_close', 0.0, None, {'dur': 1.1}, '"I close the curtains downstairs"'),
    ('w69:run+0.05', 'footsteps_wood_inside', -2.0, None, {'stairs': True, 'run': True, 'direction': 'up', 'n': 7},
     '"then run up to June\'s room"'),
    ('s70+0.05', 'door_creak', -6.0, None, {'dur': 0.9}, 'June\'s door pushed open as the narrator comes in'),
    ('s73+0.8', 'owl_hoot', -3.0, 'woods', {}, 'the owl while he stands there'),
    ('s87-0.35', 'wood_creak', -4.0, 'inside', {'kind': 'creak', 'dur': 0.6}, 'the board behind us ("I turn around.")'),
    # ---- the comment prompt: the tape is paused
    ('s92-0.05', 'vhs_pause', 0.0, None, {'kind': 'pause', 'dur': 'until:s100-0.25'}, 'the VHS pause'),
    # ---- rule 2
    ('s100', 'room_tone_house', 0.0, None, {'dur': 'until:s130', 'hum': 0.25}, 'the house'),
    ('s100', 'old_clock', -3.0, None, {'dur': 'until:s109', 'bpm': 60}, 'midnight'),
    ('s100', 'ambience_woods', -2.0, 'outside', {'dur': 'until:s109', 'owl': 0.3, 'wind': 0.3}, 'outside'),
    ('w104:tap+0.05', 'egg_tap', 0.0, None, {}, '"...one soft tap on the front door."'),
    ('w105:porch-0.3', 'peephole', 0.0, None, {}, '"Through the peephole" (the eye goes to it after the last step)'),
    ('s109-0.2', 'ambience_woods', -4.0, 'porch', {'dur': 'until:s113', 'owl': 0.2}, 'the backyard (memory)'),
    ('w109:carries+0.1', 'oven_mitt', -2.0, None, {'dur': 1.4}, 'in oven mitts'),
    ('w109:fire-0.4', 'burn_barrel', 2.0, None, {'dur': 'until:s113+0.6', 'ignite': True}, '"...and sets it on fire"'),
    ('s112+0.3', 'plastic_melt', 2.0, None, {'dur': 2.6}, '"They smell sweet when they melt."'),
    ('s113', 'ambience_woods', -2.0, 'outside', {'dur': 'until:s130', 'owl': 0.3, 'wind': 0.3}, 'outside again'),
    ('w114:rattles+0.12', 'egg_rattle', 2.0, 'outside', {'dur': 1.5}, '"...the egg rattles."'),
    ('s116+0.25', 'door_creak', -2.0, None, {'dur': 1.4, 'slow': 1.3}, '"I open the door."'),
    ('w118:egg+0.05', 'egg_open', 2.0, None, {}, '"And I open the egg."'),
    ('w119:rolling', 'ring_roll', 2.0, None, {'dur': 2.0}, '"Inside, rolling around, is a gold ring."'),
    ('w127:takes+0.7', 'ring_hand', 0.0, None, {'kind': 'take'}, '"takes the ring out of my hand" (the give, film.py)'),
    ('w129:pocket', 'ring_hand', 2.0, None, {'kind': 'pocket', 'snap': 'cloth_rustle'}, '"She puts it in her pocket."'),
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
    ('s180+0.3', 'footsteps_stairs', -8.0, None, {'direction': 'down', 'n': 6, 'rate': 1.75, 'weight': 0.25},
     'June creeps down the stairs in her socks (the last tread before she kneels)'),
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
    ('s229+0.4', 'wood_creak', -8.0, 'attic', {'kind': 'creak', 'dur': 0.8}, 'Mom rocking in the dark corner'),
    ('s229+1.95', 'wood_creak', -9.0, 'attic', {'kind': 'creak', 'dur': 0.8}, 'the rocker, back'),
    ('s229+3.5', 'wood_creak', -10.0, 'attic', {'kind': 'creak', 'dur': 0.8}, 'the rocker, forward'),
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
DEDUP_S = 2.0                                             # an ADD row yields to a picture cue of its sound this close

# --------------------------------------------------------------------------------------------- PICTURE (the final mix)
# film.py's names -> (recipe, params set over the cue's, gain_db or None to keep the picture's, why). None drops it.
PICTURE = {
    'footsteps_grass': ('footsteps_grass', {}, None, 'grass, not a wooden porch'),
    'footsteps_heavy': ('footsteps_wood_inside', {'weight': 1.0}, None, 'the Bunnyman on the kitchen floor'),
    'wet_step': ('footsteps_wood_inside', {'weight': 1.0, 'n': 1}, -2.0, 'a wet, heavy step'),
    'floor_creak_heavy': ('wood_creak', {'kind': 'creak', 'dur': 0.8}, -4.0, 'the boards under his weight'),
    'stairs_creak': ('wood_creak', {'kind': 'creak', 'dur': 0.6}, -10.0, 'a stair under June\'s socks'),
    'hatchet_thunk': ('hatchet_step', {'thunk_only': True, 'n': 1}, None, 'the head on the tread (n=4 was four steps a cue)'),
    'wind_gust': ('wind_gust', {}, None, 'a gust in the trees'),
    'pen_write': None,                                    # a pen under "They just don't believe a word I say": nothing fits
    'magic_sparkle': None,                                # a sleight of hand makes no sound (a sparkle would be a cartoon)
    'birds_dawn': ('ambience_dawn', {'dur': 3.0, 'birds': 0.9}, None, 'dawn birds'),
    'birds_day': ('ambience_dawn', {'dur': 2.5, 'birds': 0.8}, None, 'birds by day'),
    'creek': ('creek', {}, -2.0, 'the creek in the ravine'),
    'police_radio': ('police_radio', {}, -6.0, 'the patrol cars\' radios'),
    'deadbolt': ('lock_turn', {}, -2.0, 'the front door\'s deadbolt'),
    'wet_crack': ('struggle', {'kind': 'crack'}, None, 'a wet, heavy crack'),
    'swap': ('swap', {}, None, 'the trade'),
    'marker_strike': ('marker_strike', {}, None, 'struck through'),
    'water_tap': ('water_tap', {}, -2.0, 'Mom at the sink'),
    'magnet_click': ('magnet_click', {}, None, 'the bunny magnet (radio_click was a radio\'s key)'),
    'key_turn': ('key_in_lock', {}, -8.0, 'Mom\'s key, seen from the hall (the lock already turned)'),
    'count_thump': None,                                  # the score's count notes (music_plan IDENTITY) carry the count
    'scream_far': None,                                   # the owner rejected the library screams: the narration screams
    'dogs_bark_far': ('dogs_search', {'dur': 4.0}, None, 'the search dogs'),
    'crowd_cheer': ('crowd_parade', {'dur': 3.5, 'cheer': 1.0, 'swell_at': 1.2}, None, 'a cheer (not a 20 s bed)'),
    'camera_flash': ('flash_pop', {}, None, 'the 1987 flash'),
    'vhs_glitch': ('tape_glitch', {'kind': 'tracking', 'dur': 0.3}, None, 'the tape\'s tracking (not a VCR clunk)'),
    'paper_slide': ('paper_under_door', {}, None, 'the drawing under the door'),
    'knob_turn': ('doorknob', {'kind': 'turn'}, None, 'the bathroom knob'),
    'bulb_hum': ('bulb', {'kind': 'buzz'}, None, 'the attic bulb'),
    'bulb_tink': ('lamp_out', {'kind': 'out'}, None, 'the porch bulb going dark (bulb was a pull chain)'),
    'curtain_draw': ('curtain_close', {}, None, 'the curtains'),
    'fire_whoosh': ('burn_barrel', {'ignite': True, 'dur': 2.0}, None, 'the egg flaring in the barrel (not 15 s of fire)'),
    'sirens': ('sirens_arrive', {}, None, 'the patrol cars arriving'),
}
WHO_HUM = {'mom': ('hum', 'M', -5.0), 'laurie87': ('hum', 'J', 0.0), 'june': ('hum', 'J', 0.0),
           'narrator_new': ('hum_x', 'X', None), 'narrator_neat': ('hum_x', 'X', None)}
FAMILY = {'knock_door': 'knock', 'knock_family': 'knock', 'egg_tap': 'knock', 'mail_slot': 'slot', 'slot_flap': 'slot',
          'curtain_close': 'curtain', 'curtain_flutter': 'curtain', 'paper_slide': 'paper_door',
          'paper_under_door': 'paper_door', 'lock_turn': 'lock', 'key_outside': 'lock', 'key_in_lock': 'lock',
          'sirens_arrive': 'siren', 'siren_far': 'siren', 'footsteps_wood_inside': 'steps', 'footsteps_stairs': 'steps',
          'footsteps_porch': 'steps', 'footsteps_hall': 'steps', 'footsteps_grass': 'steps', 'hatchet_step': 'steps',
          'struggle': 'struggle', 'attic_door': 'door_shut', 'burn_barrel': 'fire', 'light_switch': 'switch',
          'lamp_out': 'switch', 'flashlight_click': 'flashlight', 'bulb': 'bulb', 'dogs_search': 'dogs',
          'doorknob': 'knob', 'flash_pop': 'flash', 'camera_shutter': 'flash', 'tape_glitch': 'tape', 'vcr': 'tape',
          'vhs_pause': 'vhs', 'wet_drag': 'drag', 'hospital_room': 'hospital', 'hospital_tone': 'hospital'}


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
                                   'crowd_parade', 'hospital_room', 'hospital_corridor', 'house_creaks', 'old_clock'):
            return float(p['dur'])
    except (TypeError, ValueError):
        pass
    return 0.0


def picture_pass(out, lines, log):
    """PICTURE: film.py's names onto this film's recipes, the identity layer's versions dropped from the SFX sheet."""
    try:
        idt = MP.identity_events(lines)
    except Exception as e:
        idt = []; log.append(f'PICTURE: no identity events ({e!r})')
    def ident(vers, a, b):
        return [e for e in idt if e.get('type') == 'jingle' and e.get('version') in vers
                and e['t'] - 1.5 < b and e['t'] + float(e.get('len') or 3.0) + 1.5 > a]
    def at(a, default=None):
        try:
            return MP.resolve(a, lines)
        except Exception:
            return default
    res, n0 = [], len(out)
    girl = [e for e in idt if e.get('type') == 'jingle' and e.get('version') == 'girl']
    bath = (at('s242'), at('s286')) if at('s242') and at('s286') else None   # locked in the bathroom: 4:30 -> 6:12
    try:                                                  # the picture's shots: an 'outside' cue on an exterior shot is
        shots = json.load(open(os.path.join(MP.W, 'cues', 'shots.json')))   # heard out there, not through the door
    except Exception:
        shots = []
    def exterior(tt):
        for sh in shots:
            if sh.get('t0', 0) <= tt < sh.get('t1', 0):
                return sh.get('space') == 'outside'
        return False
    for c in out:
        nm = c.get('name'); p = dict(c.get('params') or {}) if isinstance(c.get('params'), dict) else {}
        try:
            t = float(c['t'])
        except (KeyError, TypeError, ValueError):
            res.append(c); continue
        why = None
        if nm == 'hum':                                   # the hums: the score's identity hum where it plays one
            d = float(p.get('dur') or 2.5)
            if ident(('hum', 'hum_x'), t, t + d):
                log.append(f'PIC  hum   {t:7.2f} dropped: the identity layer hums here'); continue
            ver, who, tr = WHO_HUM.get(str(p.get('who')), ('hum', 'M', -5.0))
            np_ = {'version': ver, 'who': who, 'phrases': [0, 1] if d > 2.4 else [0], 'dur': round(d + 1.0, 2),
                   'stop': 'fade'}
            if tr is not None:
                np_['transpose'] = tr
            c = dict(c, name='jingle', params=np_, gain_db=4.0, space='inside' if c.get('space') != 'close' else 'close')
            why = f'hum -> jingle {ver} ({who}), the picture\'s humming'
        elif nm == 'jingle' and p.get('version') in ('tinny_woods', 'speaker', None):
            if ident(('speaker',), t, t + float(p.get('dur') or 10.0)):
                log.append(f'PIC  jingle {t:7.2f} dropped: the identity layer plays the dying speaker'); continue
            p['version'] = 'speaker'; c = dict(c, params=p); why = 'tinny_woods -> speaker'
        elif nm == 'knock_door':                          # every knock on its frame, one knock per cue
            if p.get('kind') == 'table':                  # Grandma's knuckles on the kitchen table (the memory)
                c = dict(c, name='knock_family', params={'times': [0.0], 'soft': True}); why = 'Grandma\'s table knock'
            elif p.get('pattern') == '2-3-2':             # the family knock on the front door
                f = 0.75 if not p.get('soft') else 0.5
                c = dict(c, name='knock_family', params={'times': [0.0], 'force': f}); why = 'the family knock (2-3-2)'
            elif p.get('index') is not None or p.get('group') is not None:
                p.setdefault('n', 1); c = dict(c, params=p); why = 'one knock per cue'
        elif nm == 'mail_slot':                           # police mail_slot = open AND snap shut in one cue
            k = p.get('kind')
            c = dict(c, name='slot_flap', params={'action': 'open' if 'open' in str(k) else 'snap'},
                     gain_db=0.0 if 'open' in str(k) else -2.0)
            why = f'mail_slot {k} -> slot_flap'
        elif nm == 'door_slam':                           # struggle's default was the 5 s fight
            if p.get('kind') == 'bathroom':
                c = dict(c, name='attic_door', params={'action': 'close'}, gain_db=-2.0); why = 'the bathroom door shut'
            else:
                c = dict(c, name='struggle', params={'kind': 'slam'}); why = 'one slam'
        elif nm == 'struggle' and not p.get('kind'):      # "The whole hallway shakes." (default was the full fight)
            c = dict(c, params={'kind': 'shake'}); why = 'the hallway shakes'
        elif nm == 'vhs_pause' and p.get('kind', 'pause') == 'pause' and not p.get('dur'):
            nxt = [float(x['t']) for x in out if x.get('name') == 'vhs_pause' and float(x.get('t', 0)) > t + 1.0
                   and (x.get('params') or {}).get('kind') in ('play', 'resume')]
            if nxt:                                       # the paused tape hums until PLAY (the default was 2.5 s)
                p['dur'] = round(min(nxt) - t, 2); c = dict(c, params=p); why = 'the pause holds until PLAY'
        elif nm == 'vhs_pause' and p.get('kind') == 'rewind':
            c = dict(c, name='vcr', params={'action': 'rewind', 'dur': p.get('dur', 3.0)}); why = 'the tape rewinds'
        elif nm == 'egg_tap':                              # we are in the hall when it taps: inside, and it must read
            c = dict(c, space='inside', gain_db=2.0); why = 'the one soft tap, heard in the hall'
        elif nm in ('key_in_lock', 'key_turn'):            # Mom's one key: no bunch jingling before the click
            q = dict(p); q['jingle'] = False
            c = dict(c, name='key_in_lock', params=q, gain_db=-8.0 if nm == 'key_turn' else c.get('gain_db', 0.0))
            why = 'one key, the click on the frame'
        elif nm == 'room_tone' and p.get('kind') in ('hospital_hum', 'hospital'):
            log.append(f'PIC  room_tone {t:7.2f} dropped: hospital_room (sfx_plan ADD) is the hospital'); continue
        elif nm == 'ambience_night' and t < 130.0:        # the cold open and the sightings: the woods bed (ADD) is the night
            log.append(f'PIC  ambience_night {t:7.2f} dropped: ambience_woods (ADD) covers it'); continue
        elif nm == 'fire_crackle':                        # the barrel burns from the shot until the bedroom (s113)
            e_ = at('s113', t + float(p.get('dur') or 6.0))
            c = dict(c, name='burn_barrel', params={'dur': round(max(1.0, e_ - t), 2)}); why = 'the barrel until s113'
        elif nm == 'girl_cry' and girl:                   # her crying takes over from the broken song
            g = girl[0]; s0 = g['t'] + float(g.get('len') or 5.0) - 0.75
            e_ = at('s192+0.25', t + float(p.get('dur') or 6.0))
            c = dict(c, t=round(max(t, s0), 3), params={'dur': round(max(1.5, e_ - max(t, s0)), 2)}, space='slot',
                     gain_db=6.0, seed=3)                 # seed 3: a cry that starts at once (others open with gasps)
            why = 'her cry after the song, through the open slot, until Mom shuts it'
        elif nm == 'swap':                                # the trade's thump on the picture's flash (its impact_hit)
            imp = [float(x['t']) for x in out if x.get('name') == 'impact_hit' and abs(float(x.get('t', -9)) - t) <= 0.3]
            t2 = min(imp, key=lambda x: abs(x - t)) if imp else t
            c = dict(c, name='swap', t=round(t2, 3), params=p); why = f'the trade, on the flash at {t2:.2f}'
        elif nm in PICTURE:
            m = PICTURE[nm]
            if m is None:
                log.append(f'PIC  {nm:18s} {t:7.2f} dropped'); continue
            rn, extra, g, why = m
            q = dict(p); q.update(extra)
            c = dict(c, name=rn, params=q)
            if g is not None:
                c['gain_db'] = g
        if c.get('space') == 'outside' and not (c.get('params') or {}).get('through_walls') and exterior(t) \
                and not (c.get('name') in ('ambience_night', 'ambience_dawn', 'ambience_woods', 'room_tone')
                         and float((c.get('params') or {}).get('dur') or 30.0) > 4.0):
            c = dict(c, space='porch'); why = (why or c.get('name')) + ', on an exterior shot: porch, not through the door'
        if c.get('name') == 'struggle' and bath and bath[0] <= t <= bath[1] and c.get('space') in (None, 'inside'):
            c = dict(c, space='door'); why = (why or 'the fight') + ', heard through the bathroom door'
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
            if isinstance(p.get('groups'), str) and p['groups'].startswith('gaps:'):
                gs = [_t(x, lines) for x in p['groups'][5:].split(',')]
                p['groups'] = [round(x - gs[0], 3) for x in gs]
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
