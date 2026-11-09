# EP01 "Never Move Grandpa": the full-episode shot table (the single source of the board, the timeline and the asset usage).
# Each S(...) is one shot. `cut` = index of the word the shot is cut on (cut = that word's onset - 1 frame, snapped), or
# ('f', frame) for the approved test shots. Times, words and QA are computed by make_board.py from episodes/ep01/word_onsets.json.
# Units: studs (1 stud = 0.32 m) for camera heights/distances; fov = vertical degrees; Z = push in image scale (0.19 = +19 %).
# Event anchors: an int = word index (the event lands on that word's onset), a float = episode seconds.

SHOTS = []
def S(key, cut, part, **kw):
    kw.update(key=key, cut=cut, part=part); SHOTS.append(kw); return kw

def push(Z, mode='fov', **drift):
    m = {'type': 'push', 'Z': Z, 'mode': mode, 'ease': 'linear'}
    return m, {k: v for k, v in drift.items()}

def cam(h=None, d=None, yaw=None, pitch=None, fov=70, move=None, roll=None, accent=None, note=None, **extra):
    mv, drift = move if isinstance(move, tuple) else (move, {})
    c = {'fov': fov, 'height_studs': h, 'dist_studs': d, 'yaw_deg': yaw, 'pitch_deg': pitch, 'move': mv}
    if drift: c['drift'] = drift
    if roll: c['roll'] = {'deg': [0, roll], 'ease': 'linear'}
    if accent: c['accent'] = accent
    if note: c['note'] = note
    c.update(extra)
    return {k: v for k, v in c.items() if v is not None}

def ev(at, what, sfx=None, **kw):
    e = {'at': at, 'what': what}
    if sfx: e['sfx'] = sfx
    e.update(kw); return e

def who(name, kit, pose=None, face=None, note=None):
    c = {'who': name, 'kit': kit}
    if pose: c['pose'] = pose
    if face: c['face'] = face
    if note: c['note'] = note
    return c

GP = "K.makeGnome('grandpa', { lantern: 0 })"
GP_LIT = "K.makeGnome('grandpa', { lantern: 1, lanternLight: 3 })"
HERO_B = "K.makeCharacter('heroBarefoot')"
THEO = "K.makeCharacter('theo')"

# =================================================================== the rule, the world, Grandpa (part 1 = s01-s24, 0-26.55 s)
# Part numbers (the 3rd argument) are the 5 parallel modules, balanced by work (make_board.py prints the balance).
# s01-s05: the approved 5-second test, builders and params unchanged (copied from test5_timeline.json by make_board.py).
S('sky_to_street', ('f', 0), 1, cast=[who('neighbour gnome (frame 0, ECU)', "K.makeFamilyGnome(2, { lod: 'hero', lantern: 0 })", 'gnomeIdle, gaze -4'), who('street gnomes', "K.makeFamilyGnome(i, { lantern: 0 })", '1-2 per lawn, facing their houses')], test='s01', type='opener (accent)', loc='street_night', tod='night', size='ECU -> WS', angle='eye -> high', grade='night', light='nightStreet (P1)',
  pic="Opener (approved test s01): bright ECU of a neighbour's gnome (purple dotted hat) seen from its house side, snap pull-back to the porch-out view of our street: every gnome on every lawn faces the lens (= its house), lanterns unlit, lamps lit.",
  accent='snap pull-back + crane up, roll -15 -> 0 (0.8 outExpo + 0.2 outQuad, t1 1.0 s) + linear push +10 %', assets=['street_night', 'gnome_family', 'fx_sparkles'], sfx=['W1 airy whoosh (peak 0.12 s)', 'A_NIGHT crickets bed starts'])
S('porch_couple', ('f', 55), 1, cast=[who('Grandma', "K.makeCharacter('grandma')", 'sit on the swing (frame left), inner hand to Grandpa', 'neutral'), who('Grandpa', "K.makeCharacter('grandpa')", 'sit (frame right)', 'neutral')], test='s02', type='plain push', loc='porch_set', tod='night', size='MS two-shot', angle='eye', grade='porch', light='porchGlow',
  pic="Approved test s02: Grandma (left) and Grandpa (right) on a porch swing at night, over a white spindle rail; lit window, wall lanterns, side table with teacup.",
  assets=['porch_set', 'grandma_human', 'grandpa_human', 'fx_sparkles'], sfx=[])
S('grandma_cu', ('f', 89), 1, cast=[who('Grandma', "K.makeCharacter('grandma')", 'sit, swing held still', 'content')], test='s03', type='reaction CU', loc='porch_set', tod='night', size='CU', angle='eye', grade='porch', light='porchGlow',
  pic="Approved test s03: Grandma, content (^^); her glasses flash a 4-point star glint on \"die\".", assets=['porch_set', 'grandma_human', 'fx_star_glint', 'fx_sparkles'], sfx=[])
S('poof_swing', ('f', 126), 1, cast=[who('Grandma -> Grandma gnome', "K.makeCharacter('grandma') -> K.makeGnome('grandma', { lantern: false })", 'sit; gnome x1.35 on the seat from f134', 'content'), who('Grandpa -> Grandpa gnome', "K.makeCharacter('grandpa') -> K.makeGnome('grandpa', { lantern: 0 })", 'sit; gnome x1.35 on the seat from f134', 'content')], test='s04', type='plain push + VFX burst', loc='porch_set', tod='night', size='MS', angle='low', grade='porch -> magic (in-shot, 8 frames)', light='porchGlow -> magicGlow',
  pic="Approved test s04: magic dust builds; on \"turn\" a TF burst (streaks, fat sparkles, ring, core) over a short opaque poof hides the swap: the couple become two gnomes standing on the swing; the grade swings warm.",
  accent='punch-in +22 % in 0.15 s under the poof', assets=['porch_set', 'grandma_human', 'grandpa_human', 'gnome_grandma', 'gnome_grandpa', 'fx_burst', 'fx_magic_dust', 'fx_grade_blend'], sfx=['M1 shimmer swell from 2.10', 'P1 poof (transient 2.240)'])
S('gnome_hero', ('f', 175), 1, cast=[who('Grandpa gnome', GP + ' + softenBeard', 'gnomeIdle, gaze up 10; lantern UNLIT'), who('3 family gnomes', 'K.makeFamilyGnome(2..4)', 'lawn0, lawn2, bedFront1')], test='s05', type='character intro', loc='lawn_closeup', tod='night', size='CU -> ECU', angle='extreme low', grade='nightHigh', light='nightLawn + warm window key',
  pic="Approved test s05: Grandpa as a glazed gnome in his flowerbed under the bedroom window, from below at 3/4 on his lantern side; lantern UNLIT, no blink, no head turn. Ends on the cut before \"First\" (the test held it to 3.77 s only because its audio stopped there).",
  assets=['lawn_closeup', 'gnome_grandpa', 'gnome_family', 'fx_sparkles', 'fx_magic_dust'], sfx=['M1 tail', 'A_NIGHT'])

S('grandma_armchair', 11, 1, type='plain push (world montage)', loc='grandma_room', tod='interior day', size='MS', angle='eye (seated head)', grade='day', light='interiorDay (NEW: hemi #ffe8d0/#6a4a3a 1.1, window key #fff3e0 2.0 from upper front-left, lamp 2 cd)',
  pic="Grandma (same Grandma as the porch) in her rose wingback armchair, knitting on her lap, slippers flat on the shag rug; standard lamp, side table with the teacup, net-curtained window with daylight, framed photos.",
  cast=[who('Grandma', "K.makeCharacter('grandma')", 'sit, hands in lap', 'content')],
  cam=cam(h=3.6, d=7.5, yaw=-15, pitch=-4, fov=70, move=push(0.18, crane_studs=-0.1), note='seated head in the upper 35 %, feet and rug in the lower third (the shrink must read at the feet)'),
  assets=['grandma_room', 'grandma_human'], sfx=['A_ROOM'])
S('grandma_armchair', 15, 1, type='list jump cut (same set-up)', phase='short', loc='grandma_room', tod='interior day', size='MS', angle='eye (seated head)', grade='day', light='interiorDay',
  pic="Jump cut, identical camera: Grandma is smaller (x0.8), sunk into the chair, slippers dangling off the rug, sleeves swallowing her hands. Mirrors s95/s96 at 71.",
  cast=[who('Grandma (short)', "K.makeCharacter('grandma', { scale: 0.8, hand: 'sleeve' })", 'sit, feet dangling', 'wonder')],
  cam=cam(h=3.6, d=7.5, yaw=-15, pitch=-4, fov=70, move=push(0.18), note='same start framing as s06 (a jump cut, not a continuation)'),
  assets=['grandma_room', 'grandma_short'], sfx=['A_ROOM'])
S('glasses_dawn', 16, 1, type='plain push + in-shot glint', loc='dawn_lawn', tod='dawn', size='MS', angle='high (18 deg down)', grade='dawn', light='dawn (P4)',
  pic="Sunrise on a dewy front lawn: the Grandma gnome (lavender hat, rose coat, apron) stands new by the path wearing her round glasses, tilted; a grandkid kneels and straightens them on \"glasses\"; the lens flashes the same 4-point star glint as s03.",
  cast=[who('Grandma gnome', "K.makeGnome('grandma', { lantern: false })", 'gnomeIdle; glasses tilted 8 deg until the event'), who('grandkid', "K.makeCharacter('grandkid')", 'kneel, armR reach (rises from 6.30 over 0.3 s)', 'content')],
  cam=cam(h=4.5, d=6.0, yaw=25, pitch=-18, fov=60, move=push(0.20, crane_studs=-0.3), roll=-1.0),
  ev=[ev(23, 'glasses snap level (8 frames outBack) + star glint on the lens (peak 120 px)', 'T_GLINT (optional)')],
  assets=['dawn_lawn', 'gnome_grandma', 'grandkid', 'fx_star_glint', 'fx_dew'], sfx=['A_DAWN'])
S('lawn_stare', 24, 1, cast=[who('Grandpa gnome', GP, 'bed0, facing the house'), who('5 family gnomes', "K.makeFamilyGnome(POINTED[i], { lantern: 0, lod: 'mid' })", 'bedFront0, lawn0-3, bedFront1; gnomeIdle amp 0.4')], test='s06', type='rule image (pull-back accent)', loc='lawn_closeup', tod='night', size='low WS', angle='low (gnome eye level)', grade='nightHigh', light='nightLawn + two lit windows',
  pic="Approved test s06 builder, unchanged: low wide from behind a lawn gnome, the family of gnomes on our lawn all staring at the house, Grandpa in his bed under the lit bedroom window, lanterns unlit (the plant), TF moon over the roof; slow pull-back. Moved here from the test's silent tail (3.77-5.00 s), where the episode voice says \"First, your grandma gets shorter\".",
  accent='pull -10 % (linear)', assets=['lawn_closeup', 'gnome_grandpa', 'gnome_family', 'fx_sparkles'], sfx=['A_NIGHT'])
S('agent_board', 31, 1, type='insert (sign, pushed into)', loc='hero_lot', tod='day', size='MS -> INS', angle='eye', grade='day', light='day (sun el 45, pcfsoft)',
  pic="Our house by day: the estate-agent board on our lawn by the path, FOR SALE / 3 BED · BIG GARDEN / COMES WITH ANCESTORS; two family gnomes pose either side of the post like agents; Grandpa small in his flowerbed under the bedroom window behind. The push ends with COMES WITH ANCESTORS filling the centre on \"ancestors\". (Plant: the board returns with SOLD at 26.6 s.)",
  cast=[who('2 family gnomes', 'K.makeFamilyGnome(1) + K.makeFamilyGnome(3)', 'gnomeIdle, turned 20 deg toward the lens', None), who('Grandpa gnome', GP, 'in bed0 (background)')],
  cam=cam(h=4.8, d=9.0, yaw=10, pitch=-3, fov=60, move=push(0.26, truck_studs=0.2), note='board text centre on the frame centre at the end; nothing in the caption band'),
  assets=['hero_lot', 'agent_board', 'gnome_family', 'gnome_grandpa'], sfx=['A_DAY'])
S('keepoff_sign', 36, 1, type='insert (sign) + light-state event', loc='dusk_street', tod='dusk', size='WS', angle='low', grade='dusk', light='dusk (sun el 6, side)',
  pic="Sunset street: KEEP OFF THE LAWN AFTER DARK sign in the left-centre foreground; behind it a kid hops stone to stone up a garden path toward his porch; on \"dark\" curtains snap shut down the street, window by window.",
  cast=[who('grandkid', "K.makeCharacter('grandkid')", 'jump (hop 0.45 s cycle, stone to stone)', None)],
  cam=cam(h=1.6, d=7.0, yaw=-20, pitch=6, fov=70, move=push(0.15, truck_studs=0.3)),
  ev=[ev(43, 'curtains snap shut on 6 lit windows, 0.12 s apart, nearest first (curtainCascade)', 'CURTAIN swish (optional)')],
  assets=['dusk_street', 'keep_off_sign', 'grandkid', 'fx_curtains'], sfx=['A_DUSK'])
S('nextdoor_plastic', 44, 1, type='plain push', loc='next_door', tod='day', size='MS', angle='eye', grade='day', light='day',
  pic="Next door's lawn by day: three glossy plastic gnomes in a row with $4.99 stickers, facing the STREET (decorations), a hose reel, a red kennel REX; the dog lies chewing the nearest plastic gnome's hat; on \"plastic\" the hat squeaks.",
  cast=[who('3 plastic gnomes', "K.makePlasticGnome({ finish: 'glossy' })", 'static, facing the street'), who('the dog (REX)', 'C.makeDog()', 'lie + chew (head bob 2 Hz), tail wag', None)],
  cam=cam(h=4.0, d=8.5, yaw=-12, pitch=-6, fov=65, move=push(0.19, truck_studs=-0.2)),
  ev=[ev(49, 'the dog bites the hat: hat squashes 15 % for 6 frames', 'SQUEAK')],
  assets=['next_door', 'gnome_plastic', 'dog'], sfx=['A_DAY'])
S('kennel_hole', 50, 1, type='insert (top-down, truck along the lead)', loc='next_door', tod='day (later, longer shadows)', size='INS', angle='top-down', grade='day', light='day (sun el 30)',
  pic="Top-down: the empty REX kennel at the top of frame, its red lead running down across the grass into a neat round black hole; the camera trucks along the lead and arrives over the hole on \"hole\", when the lead gives one small tug toward it. No dog.",
  cam=cam(h=9.0, pitch=-90, fov=50, move=push(0.15, truck_studs=3.2), accent='truck along the lead, 3.2 studs in 1.28 s (about 700 px/s), linear', note='hole centred on the frame centre at the cut-out'),
  ev=[ev(55, 'lead tugs 0.1 stud toward the hole (spring)', 'CHAIN_TUG')],
  assets=['next_door'], sfx=['A_DAY'])
S('gate_bonk', 56, 1, type='action (rule image)', loc='gate_lot', tod='night', size='MWS', angle='low (gnome eye level, outside the gate)', grade='nightHigh', light='nightLawn',
  pic="Night: a family gnome (red hat, blue coat, unlit lantern swinging) toddles down its path toward the lens and the open gate; at the property line it bonks an invisible wall on \"garden\": light ripples spread across the shimmer curtain between it and the lens; it springs back, wobbling.",
  cast=[who('family gnome 0', 'K.makeFamilyGnome(0) + K.gnomeHop', 'hops 0.1 stud @ 2.5 Hz, +-8 deg roll, 3 studs travel; bonk spring-back 0.15 stud')],
  cam=cam(h=1.4, d=5.5, yaw=0, pitch=3, fov=60, move=push(0.15), note='camera on the street side of the gate: the ripple is in the frame centre'),
  ev=[ev(63, 'bonk: ripple rings + 12-sparkle burst + shake 4 px 0.3 s', 'BONK')],
  assets=['gate_lot', 'gnome_toddler', 'fx_property_line', 'fx_burst', 'fx_sparkles', 'fx_shake'], sfx=['HOPS', 'A_NIGHT'])
S('family_hands', 64, 1, type='action', loc='gate_lot', tod='night', size='MS', angle='slightly high', grade='nightHigh', light='nightLawn',
  pic="Same gate: a grown-up's hands (plaid sleeves) outlined in soft gold lift the gnome over the line; the curtain parts in a gold flash; the gate swings shut behind them and the latch clicks on \"out\".",
  cast=[who('Dad (arms only)', "K.makeCharacter('dad')", 'carry (arms 80 deg)'), who('family gnome 0', 'K.makeFamilyGnome(0)', 'carried')],
  cam=cam(h=3.6, d=5.0, yaw=20, pitch=-12, fov=65, move=push(0.19)),
  ev=[ev(65, 'gnome crosses the line: curtain parts (gold flash, 10 gold sparkles)', 'SHIMMER_S'), ev(69, 'gate leaf swings shut (6 frames) and latches', 'LATCH')],
  assets=['gate_lot', 'dad_arms', 'gnome_family', 'fx_gold_outline', 'fx_property_line', 'fx_sparkles'], sfx=['A_NIGHT'])
S('hero_taps_hat', 70, 1, type='hero intro (plain push + roll)', loc='hero_lot', tod='day (spring)', size='MS', angle='eye (kneeling)', grade='day', light='day (spring sun el 40)',
  pic="Spring, our front garden: the hero (11, mustard hoodie, messy brown hair, freckles) kneels in the tulips beside Grandpa gnome, standing in his spot right under the hero's bedroom window and facing it, and taps the gnome's hat with one finger on \"grandpa\". (Plant: the spot.)",
  cast=[who('the hero (11)', "K.makeCharacter('hero')", 'kneel; armR point -> tap (6 frames)', 'grin'), who('Grandpa gnome', GP, 'in bed0, facing the window; gnomeIdle')],
  cam=cam(h=3.0, d=7.0, yaw=35, pitch=4, fov=70, move=push(0.22), roll=1.0, note='3/4 from the street side so the bedroom window is in the top third'),
  ev=[ev(71, 'tap on the hat (hat tip wobbles +-6 deg, spring)', 'TOK')],
  assets=['hero_lot', 'hero', 'gnome_grandpa'], sfx=['A_DAY'])
S('goodnight_window', 75, 1, type='OTS', loc='hero_room', tod='night (interior)', size='OTS', angle='eye', grade='bedroom', light='bedroomNight (NEW P2: hemi #b9a8ff/#5a2a4a 1.3, lamp 4 cd)',
  pic="Night, the hero's own bedroom (later Theo's): over his shoulder he waves through the window glass; below in the flowerbed Grandpa gnome looks up, lit by the window spill. The view outside is darker than the room.",
  cast=[who('the hero (11)', "K.makeCharacter('hero')", 'wave (armR 160 deg, +-15 deg @ 2 Hz)', None, 'back to camera')],
  cam=cam(h=4.9, d=2.2, yaw=25, pitch=-14, fov=70, move=push(0.15)),
  assets=['hero_room', 'hero', 'gnome_grandpa', 'fx_sparkles'], sfx=['A_ROOM'])
S('gnome_blink_night', 78, 1, type='creature CU + blink', loc='lawn_closeup', tod='night', size='CU', angle='low', grade='nightHigh', light='nightLawn + warm window spill key from above',
  pic="Close on Grandpa gnome from below, gazing up at the lit window (gaze up 20 deg); on \"blinks\" his eyes close for exactly 2 frames. The first blink of the episode.",
  cast=[who('Grandpa gnome', GP, 'gnomeIdle; gaze up 20')],
  cam=cam(h=0.9, d=1.6, yaw=-15, pitch=14, fov=70, move=push(0.20)),
  ev=[ev(80, 'blink, 2 frames (K.gnomeBlink)', 'TIK')],
  assets=['lawn_closeup', 'gnome_grandpa', 'fx_sparkles'], sfx=['A_NIGHT'])
S('fb_grandpa_walk', 81, 1, type='flashback, follow truck', loc='hero_lot', era='2010s', tod='night (sepia flashback)', size='MS', angle='eye', grade='sepia', light='nightLawn, graded sepia',
  pic="Flashback, warm sepia: human Grandpa (navy cardigan, white walrus moustache, round gold glasses, tartan slippers, flashlight on) strolls our dark lawn left to right, straight past the KEEP OFF sign by the gate; the house with lit windows behind him.",
  cast=[who('Grandpa (man)', "K.makeCharacter('grandpa')", 'walkCycle period 1.0 s, legs 25, armR holds the flashlight forward', 'content')],
  cam=cam(h=4.4, d=9.0, yaw=0, pitch=-2, fov=70, move=push(0.12, truck_studs=7.0), note='follow: the truck keeps Grandpa (3.5 studs/s) centred'),
  assets=['hero_lot', 'grandpa_human', 'flashlight', 'fx_beam', 'keep_off_sign'], sfx=['A_NIGHT (sepia: LPF 6 kHz)'])
S('fb_flashlight', 90, 1, type='list insert', loc='hero_lot', era='2010s', tod='night (sepia)', size='INS', angle='eye', grade='sepia', light='nightLawn, sepia',
  pic="Insert: Grandpa's hand clicks the flashlight on; the beam blooms across the wet grass.",
  cast=[who("Grandpa's hand", "K.makeCharacter('grandpa') (hand socket)", 'holds the torch')],
  cam=cam(h=3.2, d=2.0, yaw=60, pitch=-10, fov=45, move=push(0.25)),
  ev=[ev(90, 'flashlight on (1 frame) + beam', 'CLICK_TORCH')],
  assets=['grandpa_human', 'flashlight', 'fx_beam'], sfx=[])
S('fb_slippers', 91, 1, type='list insert', loc='hero_lot', era='2010s', tod='night (sepia)', size='INS', angle='ground level', grade='sepia', light='nightLawn, sepia + beam spill',
  pic="Insert: tartan slippers step onto wet grass at ground level, dew glinting in the beam.",
  cast=[who("Grandpa's feet", "K.makeCharacter('grandpa')", 'walkCycle (feet only)')],
  cam=cam(h=0.4, d=2.4, yaw=80, pitch=2, fov=45, move=push(0.20)),
  ev=[ev(91, 'slipper lands (6 frames after the cut)', 'STEP_WET')],
  assets=['grandpa_human', 'fx_dew'], sfx=[])
S('fb_lap', 92, 1, type='list insert (top-down)', loc='hero_lot', era='2010s', tod='night (sepia)', size='WS', angle='top-down aerial', grade='sepia', light='nightLawn, sepia',
  pic="Top-down over our lawn: Grandpa's worn lap path (a faint flattened-grass loop) with his flashlight dot travelling round it; the loop has a small kink, a dent toward the house, under one window. (Rewatch clue: it pays at 70.9 s.)",
  cast=[who('Grandpa (tiny, from above)', "K.makeCharacter('grandpa')", 'walkCycle along the loop')],
  cam=cam(h=34, pitch=-90, fov=45, move=push(0.15), roll=4.0, note='kink at upper-right of centre; the house edge along the top of frame'),
  assets=['hero_lot', 'grandpa_human', 'fx_beam'], sfx=[])
S('fb_wink', 94, 1, type="dialogue (Grandpa's line)", loc='hero_lot', era='2010s', tod='night (sepia)', size='CU', angle='low', grade='sepia', light='flashlight under the chin (point #fff1d0 2.5 cd) + sepia night',
  pic="\"Checking for moles,\" he'd say: Grandpa holds the flashlight under his chin like a ghost story and winks on \"he'd\".",
  cast=[who('Grandpa (man)', "K.makeCharacter('grandpa')", 'armR torch under the chin', 'talk -> wink')],
  cam=cam(h=3.9, d=2.8, yaw=-10, pitch=8, fov=70, move=push(0.22), roll=-1.0),
  ev=[ev(97, 'face swap talk -> wink (NEW face)', None, kind='face')],
  assets=['grandpa_human', 'flashlight', 'face_wink'], sfx=[])
S('fb_big_ones', 99, 1, type="dialogue (Grandpa's line)", loc='hero_lot', era='2010s', tod='night (sepia)', size='MS', angle='eye', grade='sepia', light='sepia night + torch',
  pic="\"Big ones.\" Grandpa spreads his hands wide like a fisherman's tall tale, eyebrows up, the torch beam swinging sideways.",
  cast=[who('Grandpa (man)', "K.makeCharacter('grandpa')", 'snap to arms wide (armLz/armRz 80) in 8 frames outBack from the cut', 'wonder')],
  cam=cam(h=4.4, d=7.0, yaw=8, pitch=-2, fov=70, move=push(0.18)),
  assets=['grandpa_human', 'flashlight', 'fx_beam'], sfx=[])

# =================================================================== twist 1 and the main reveal (part 2 = s25-s41, 26.55-46.30 s)
S('sold_truck_dusk', 101, 2, type='establishing (dusk)', loc='hero_lot', tod='dusk', size='WS', angle='eye', grade='dusk', light='dusk (sun el 5, long soft shadows, windows lit)',
  pic="Dusk, the evening before the move: our house from the street; a red SOLD sticker slaps across the COMES WITH ANCESTORS board on \"moved\"; the moving truck at the kerb, back open, a box marked BALCONY GNOME on top; at the picket fence a small boy in blue pyjamas hugging a grey-blue stuffed whale stares through the pickets at Grandpa in his flowerbed (Theo, unnamed).",
  cast=[who('Theo (unnamed)', THEO + ' + whale', 'hug the whale, head turned to Grandpa', 'wonder'), who('Grandpa gnome', GP, 'bed0')],
  cam=cam(h=5.0, d=26, yaw=-8, pitch=-2, fov=60, move=push(0.15, 'dolly', truck_studs=0.4)),
  ev=[ev(106, 'SOLD sticker slaps on (scale 1.3 -> 1 in 4 frames)', 'SLAP_STICKER')],
  assets=['hero_lot', 'agent_board', 'moving_truck', 'theo', 'whale', 'gnome_grandpa', 'gnome_family'], sfx=['A_DUSK'])
S('hall_clock', 107, 2, type='insert (motif: 9:00)', loc='hall', tod='night (interior)', size='INS', angle='eye', grade='bedroom', light='bedroomNight (hall: one ceiling lamp 3 cd)',
  pic="Night, our hall: the wall clock at 9:00 (Roman numerals); below it the hero's rolled-up sleeping bag and three boxes marked THEO by the front door. The minute hand ticks onto XII on \"nine\".",
  cam=cam(h=6.5, d=3.0, yaw=0, pitch=-15, fov=50, move=push(0.25)),
  ev=[ev(108, 'minute hand ticks to 12 (2-frame snap + 3-frame wobble)', 'TICK_CLOCK')],
  assets=['hall'], sfx=['A_ROOM'])
S('empty_spot', 109, 2, type='twist image + silence beat', loc='hero_lot', tod='night', size='CU', angle='high', grade='nightHigh', light='nightLawn + window',
  pic="Under his old window (lit, curtains half drawn): in the tulips only a ring of flat pale soil where Grandpa stood, two small boot dents. Held through the pause after \"empty\".",
  cam=cam(h=3.2, d=3.2, yaw=0, pitch=-38, fov=60, move=push(0.20), note='looking down into the bed from the lawn: ring in the frame centre, the lit sill and the bottom of the window across the top'),
  assets=['hero_lot', 'fx_sparkles'], sfx=['A_NIGHT drops to near-silence from 28.87 (silence beat)'])
S('run_out_barefoot', 113, 2, type='action (boot-level tracking accent)', loc='hero_lot', tod='night', size='WS -> MS', angle='ground level', grade='nightHigh', light='nightLawn + porch light spill',
  pic="Ground level: the front door bangs open (porch light), the hero's bare blocky feet thump onto the wet grass running toward the lens; the KEEP OFF sign looms in the right foreground as the camera tracks backward.",
  cast=[who('the hero (11)', HERO_B, 'runCycle 0.5 s (6 studs/s jog)', 'shock')],
  cam=cam(h=0.5, d=4.0, yaw=0, pitch=8, fov=70, move=push(0.10, 'dolly', dolly_back_studs=9.5), accent='boot-level tracking: dolly back 9.5 studs at the run speed'),
  ev=[ev(115, 'door bangs open', 'DOOR_BANG'), ev(117, 'first bare foot lands, then every 0.25 s', 'FEET_WET')],
  assets=['hero_lot', 'hero', 'keep_off_sign'], sfx=['A_NIGHT'])
S('gate_truck_thumb', 120, 2, type='THUMBNAIL frame (OTS low)', loc='hero_lot', tod='night', size='MS', angle='low OTS', grade='night', light='nightStreet (lamp pool by the truck)',
  pic="Grandpa gnome at the very edge of our garden, boots on the shimmering property line at the open gate, staring up at the moving truck's open back across the sidewalk (cargo dome light on, the BALCONY GNOME box); lantern unlit. (Thumbnail frame; the tear comes next.)",
  cast=[who('Grandpa gnome', GP, 'at the gate, facing the street (turned 180 deg from his spot); gnomeIdle')],
  cam=cam(h=0.7, d=1.8, yaw=150, pitch=12, fov=70, move=push(0.22, crane_studs=0.15)),
  assets=['hero_lot', 'gnome_grandpa', 'moving_truck', 'fx_property_line', 'fx_sparkles'], sfx=['A_NIGHT'])
S('gnome_tear', 129, 2, type='creature CU', loc='hero_lot', tod='night', size='CU', angle='low', grade='night', light='lamp-post warm key + cool rim',
  pic="Close on his painted face, front and low: on \"with\" a dewdrop wells at one eye and runs down his cheek into the beard.",
  cast=[who('Grandpa gnome', GP, 'gnomeIdle; gaze up 15 (at the truck)')],
  cam=cam(h=1.0, d=1.4, yaw=-5, pitch=12, fov=70, move=push(0.24), roll=1.0),
  ev=[ev(134, 'tear wells (0.15 s) then runs (0.45 s)', None)],
  assets=['gnome_grandpa', 'fx_tear', 'fx_sparkles'], sfx=['A_NIGHT'])
S('hero_arms_out', 136, 2, type="dialogue (the hero's line)", loc='hero_lot', tod='night', size='MS', angle='low (gnome POV)', grade='night', light='porch light behind + lamp key',
  pic="\"Come on, then.\" The hero, kneeling on the path, holds out his arms toward the lens (Grandpa's POV), whispering.",
  cast=[who('the hero (11)', HERO_B, 'kneel; both arms reach forward 70 deg', 'heartfelt')],
  cam=cam(h=1.4, d=5.5, yaw=0, pitch=10, fov=70, move=push(0.18), note='arms and face both in frame'),
  assets=['hero_lot', 'hero'], sfx=[])
S('pick_up', 139, 2, type='action + VFX (hides the hand-off)', loc='hero_lot', tod='night', size='MS', angle='eye', grade='night', light='nightStreet',
  pic="He hugs the gnome off the ground; as the boots leave the line a gold ripple runs along it (same gold as s15) and hides the hand-off.",
  cast=[who('the hero (11)', HERO_B, 'reach -> hug (8 frames outQuad from \"picked\"), stands up', 'heartfelt'), who('Grandpa gnome', GP, 'parented to the hero torso at contact')],
  cam=cam(h=4.2, d=8.0, yaw=-20, pitch=-4, fov=70, move=push(0.19)),
  ev=[ev(140, 'lift + gold ripple along the line + 6 gold sparkles', 'CLINK')],
  assets=['hero_lot', 'hero', 'gnome_grandpa', 'fx_property_line', 'fx_gold_outline', 'fx_sparkles'], sfx=['SHIMMER_S'])
S('gold_arms', 143, 2, type='callback image (gold outline)', loc='hero_lot', tod='night', size='CU', angle='slightly high', grade='night', light='nightStreet',
  pic="His arms around the gnome, outlined in gold like the grown-up's hands at 16.8 s; the lantern swings on its ring, still unlit.",
  cast=[who('the hero (11)', HERO_B, 'hug', None, 'arms and chest only'), who('Grandpa gnome', GP, 'held; lantern pendulum +-12 deg at 1.4 Hz decaying')],
  cam=cam(h=4.6, d=2.4, yaw=15, pitch=-20, fov=60, move=push(0.20), roll=-1.0),
  assets=['hero', 'gnome_grandpa', 'fx_gold_outline', 'fx_sparkles'], sfx=['CREAK_LANTERN'])
S('lawn_moves', 146, 2, type='reveal (shake accent)', loc='hero_lot', tod='night', size='WS', angle='ground level', grade='nightHigh', light='nightLawn',
  pic="Ground level across the lawn: the whole lawn bulges like a duvet with something under it, a long wave rolling toward the house; the hero on the path, small at frame left, freezes.",
  cast=[who('the hero (11)', HERO_B + ' + gnome', 'hug, frozen', 'shock')],
  cam=cam(h=0.4, d=12, yaw=-30, pitch=4, fov=70, move=push(0.15), accent='shake +-8 px (spikes 20) from \"moved\", decaying 0.5 s'),
  ev=[ev(149, 'the bulge surges 0.8 stud + shake', 'SUBBOOM (whoosh + sub-boom + rumble to 39.5)')],
  assets=['hero_lot', 'hero', 'gnome_grandpa', 'mole_field', 'fx_shake', 'fx_soil'], sfx=['A_NIGHT'])
S('mounds_dozens', 150, 2, type='reveal of quantity (crane-up pull-back accent)', loc='street_night', tod='night', size='WS -> EWS', angle='high', grade='night', light='nightStreet',
  pic="Crane up and back over the lawns: dozens of mounds push up across our lawn and the neighbours', crumbs popping off their tops; the hero tiny on our path.",
  cast=[who('the hero (11)', HERO_B + ' + gnome', 'hug', None, 'tiny')],
  cam=cam(h=6.0, d=10, yaw=-20, pitch=-35, fov=60, move={'type': 'crane_pullback', 'x': 2.5, 'ease': 'outExpo', 'crane_up_studs': 18, 't0': 0, 't1': 0.88},
          accent='crane-up pull-back x2.5 outExpo (half done in 0.1 s) + linear push +8 % on top'),
  ev=[ev(152, 'mounds rise staggered 0.05-0.15 s apart', 'CRUMBLE')],
  assets=['street_night', 'mole_field', 'hero', 'gnome_family', 'fx_soil'], sfx=[])
S('reflector_eyes', 153, 2, type='creature CU (strong push)', loc='hero_lot', tod='night', size='CU', angle='low', grade='nightHigh', light='nightLawn; a street lamp behind the lens so the eyes retro-reflect',
  pic="Right in front of the lens a mound; on \"eyes\" two round amber reflector eyes light up in the turf; on \"reflectors\" a sweep of light flashes them like bike reflectors in a headlight.",
  cam=cam(h=0.4, d=2.2, yaw=0, pitch=4, fov=55, move=push(0.28)),
  ev=[ev(154, 'eyes on (0 -> 1 in 3 frames)', 'PLINK'), ev(157, 'reflector flash (star glint sweep, 0.25 s)', None)],
  assets=['moles', 'mole_field', 'fx_star_glint'], sfx=['SUBBOOM rumble tail'])
S('snout_reveal', 158, 2, type='creature intro (punch-in accent)', loc='hero_lot', tod='night', size='ECU', angle='extreme low', grade='nightHigh', light='nightLawn + cool rim',
  pic="The turf splits and a pink star-shaped snout unfurls and sniffs, its tentacles wriggling (\"Moles,\"); on \"big\" a second, much bigger snout (x1.8) rises behind it and fills the frame as the camera punches in.",
  cam=cam(h=0.3, d=1.8, yaw=10, pitch=20, fov=70, move={'type': 'punch', 'x': 1.6, 't0_word': 159, 'dur': 0.45, 'ease': 'inQuad', 'base_push': 0.10}, roll=10,
          accent='punch-in x1.6 in 0.45 s on \"big\" (+10 deg roll) over a +10 % base push'),
  ev=[ev(158, 'turf tears, snout 1 unfurls (0.3 s outBack)', 'SNIFF'), ev(159, 'snout 2 (scale 1.8) rises + punch-in', None)],
  assets=['moles', 'mole_field', 'fx_soil'], sfx=[])
S('lantern_lights', 161, 2, type='light-state event (P3 magic glow moment)', loc='hero_lot', tod='night', size='CU', angle='low', grade='nightHigh -> magic 60 % (in-shot, 8 frames)', light='nightLawn -> magicGlow (lantern source)',
  pic="The gnome in the hero's arms, his lantern hand toward us; on \"lit\" the little lantern lights by itself: a warm pool on the gnome's face and the yellow hoodie, gold motes rising.",
  cast=[who('the hero (11)', HERO_B, 'hug', None, 'chest and chin'), who('Grandpa gnome', GP_LIT, 'held; K.lanternLightUp on \"lit\"')],
  cam=cam(h=2.4, d=1.6, yaw=-20, pitch=12, fov=70, move=push(0.19)),
  ev=[ev(163, 'lantern 0 -> 1 in 3 frames (overshoot 1.5), halo 0.2 s; grade warms over 8 frames to 60 % magic; 12 gold motes', 'TINK_WHOOSH')],
  assets=['hero', 'gnome_grandpa', 'fx_grade_blend', 'fx_magic_dust', 'fx_sparkles'], sfx=[])
S('ring_edge', 164, 2, type='insert (top-down) + silence beat', loc='hero_lot', tod='night', size='INS (aerial)', angle='top-down', grade='nightHigh', light='nightLawn + lantern ring',
  pic="Top-down: a gold circle of light on the grass around the hero's bare feet; mounds roll in from all sides and on \"edge\" their snouts snap back at the rim. Held through the pause.",
  cast=[who('the hero (11)', HERO_B + ' + lit gnome', 'hug, from above')],
  cam=cam(h=16, pitch=-90, fov=50, move=push(0.15), roll=6.0),
  ev=[ev(169, 'snouts recoil at the rim (0.15 s spring)', 'FIP')],
  assets=['hero', 'gnome_grandpa', 'moles', 'mole_field', 'fx_lantern_ring'], sfx=[])
S('street_cascade', 170, 2, type='fast truck accent + light cascade', loc='street_night', tod='night', size='WS (high)', angle='high', grade='night', light='nightStreet',
  pic="Down the street, dark gardens, mounds prowling on the lawns; from \"Every\" lanterns pop on garden by garden toward the camera, each gnome's face lit from below as it stares at its house, as the camera trucks fast along the kerb. Our lot is already lit; next door stays dark.",
  cast=[who('street gnomes', 'K.makeFamilyGnome(i)', 'static, facing their houses')],
  cam=cam(h=9.0, d=0, yaw=0, pitch=-25, fov=60, move=push(0.10, truck_studs=30), accent='fast truck along the kerb from 44.58 s, about 1900 px/s (30 studs in 0.95 s), linear'),
  ev=[ev(173, 'lantern cascade starts (12 lanterns, 0.15-0.3 s apart, toward camera)', 'TINKS'), ev(175, 'nearest lantern lights', None)],
  assets=['street_night', 'gnome_family', 'mole_field', 'fx_lantern_cascade', 'fx_lantern_ring', 'fx_sparkles'], sfx=['A_NIGHT'])
S('nextdoor_dark', 176, 2, type='plain push', loc='next_door', tod='night', size='MS', angle='eye', grade='night (temperature -24)', light='nightStreet, no lantern',
  pic="Next door's lawn, dark: the plastic gnomes still facing the street with their black plastic lanterns; on \"door\" a mound rolls over one and it tips into a hole. Our gold ring glows past the fence at frame right.",
  cast=[who('plastic gnomes', "K.makePlasticGnome({ finish: 'glossy' })", 'static; one tips (rot 0 -> 70 deg, drops 1.5 studs)')],
  cam=cam(h=4.0, d=8.0, yaw=-15, pitch=-8, fov=65, move=push(0.19)),
  ev=[ev(178, 'plastic gnome tips into a hole', 'CLATTER')],
  assets=['next_door', 'gnome_plastic', 'mole_field', 'fx_lantern_ring'], sfx=['A_NIGHT'])
S('lit_gnome_cu', 179, 3, type='creature CU (rule restated)', loc='street_night', tod='night', size='CU', angle='low', grade='nightHigh', light='nightLawn + lantern key from below',
  pic="A lit street gnome (orange hat), face lit from below by its own lantern like the TF fairies, unblinking, staring at its house; behind it a mound noses the edge of its pool and backs off.",
  cast=[who('family gnome 4', "K.makeFamilyGnome(4, { lantern: 1, lanternLight: 2.5 })", 'gnomeIdle')],
  cam=cam(h=1.0, d=1.5, yaw=-30, pitch=15, fov=70, move=push(0.22), roll=1.5),
  assets=['gnome_family', 'mole_field', 'fx_lantern_ring', 'fx_sparkles', 'fx_magic_dust'], sfx=[])
S('fence_aerial', 182, 3, type='reframe image (slow crane up) + silence beat', loc='aerial_street', tod='night', size='EWS', angle='high aerial', grade='night', light='nightStreet',
  pic="High aerial along the street: an unbroken chain of lantern circles runs between the lawns and the houses, a fence of light; mounds prowl outside it; one gap at next door. Held through the pause after \"fence\".",
  cam=cam(h=60, d=40, yaw=0, pitch=-35, fov=50, move=push(0.12, crane_studs=4)),
  assets=['aerial_street', 'fx_lantern_ring', 'mole_field', 'gnome_family'], sfx=['A_NIGHT + distant rumble'])

# =================================================================== the dilemma, the attempt (part 3 = s42-s57, 46.30-65.43 s)
S('theo_intro', 185, 3, type='character intro (push + roll)', loc='hero_room', tod='night (interior)', size='CU', angle='low', grade='bedroom', light='bedroomNight (nightlight star projector + warm lantern glow through the window)',
  pic="In the old room, half empty: Theo asleep on a bare mattress on the floor hugging his whale, a yellow \"6\" birthday badge on his pyjamas, boxes marked THEO, star projections on the ceiling. The badge glints on \"six\".",
  cast=[who('Theo (6)', THEO + ' + whale + badge6', 'lying on his side, hug', 'sleeping')],
  cam=cam(h=1.2, d=2.4, yaw=-25, pitch=8, fov=70, move=push(0.30), roll=10, note='character-intro push +30 % with roll (a strong push, not an accent)'),
  ev=[ev(190, 'badge glint (star, 90 px)', None)],
  assets=['hero_room', 'theo', 'whale', 'badge6', 'fx_star_glint', 'fx_sparkles'], sfx=['A_ROOM'])
S('theo_window_out', 191, 3, type='plain push (dolly)', loc='hero_lot', tod='night', size='MS', angle='eye-low', grade='nightHigh', light='nightLawn + lantern pool + window',
  pic="Outside: Theo's window, the room lit softly by the nightlight, Theo asleep inside; the empty ring of soil in the flowerbed below; the hero stands at frame left holding the lit gnome, looking in.",
  cast=[who('the hero (11)', HERO_B + ' + lit gnome', 'hug, looking at the window', 'sad'), who('Theo', THEO, 'asleep inside', 'sleeping')],
  cam=cam(h=2.5, d=6.0, yaw=20, pitch=4, fov=70, move=push(0.19, 'dolly')),
  assets=['hero_lot', 'hero_room', 'hero', 'gnome_grandpa', 'theo', 'whale', 'fx_lantern_ring', 'fx_sparkles'], sfx=['A_NIGHT'])
S('take_window_dark', 198, 3, type='what-if (truck + light-state event)', loc='hero_lot', tod='night', size='WS', angle='eye', grade='nightHigh', light='nightLawn; the lantern ring moves with the hero',
  pic="Profile WS: the hero takes one step toward the truck; the circle of light slides with him off the flowerbed, which goes black; two mounds glide toward it; on \"dark\" Theo's window light snaps off.",
  cast=[who('the hero (11)', HERO_B + ' + lit gnome', 'one walk step (0.73 s cycle) toward the gate', 'determined')],
  cam=cam(h=4.5, d=18, yaw=90, pitch=-3, fov=65, move=push(0.12, truck_studs=1.5)),
  ev=[ev(201, 'mounds start drifting toward the bed', None), ev(204, "Theo's window off (1 frame) + mounds surge 0.5 stud", 'THUD_LOW')],
  assets=['hero_lot', 'hero', 'gnome_grandpa', 'mole_field', 'fx_lantern_ring', 'fx_window_dark'], sfx=['A_NIGHT'])
S('gnome_waiting', 205, 3, type='creature CU (POV high)', loc='hero_lot', tod='night', size='CU', angle='high (the hero\'s POV)', grade='nightHigh', light='lantern from below + cool hemi',
  pic="Looking down into his arms: the gnome, lantern lit, eyes open, looking up at him, waiting. No blink.",
  cast=[who('Grandpa gnome', GP_LIT, 'held; gaze up 25; NO blink')],
  cam=cam(h=4.3, d=1.2, yaw=0, pitch=-40, fov=70, move=push(0.20)),
  assets=['gnome_grandpa', 'hero', 'fx_sparkles', 'fx_magic_dust'], sfx=[])
S('truck_clock', 213, 3, type='insert (clock + note)', loc='truck_cab', tod='night (cab)', size='INS', angle='eye', grade='night', light='cabNight (dashboard glow 1 cd, street lamp through the windscreen)',
  pic="Inside the truck cab: the red LED dashboard clock reads 11:52, colon blinking; a yellow sticky note on the steering wheel: LEAVE 6 AM.",
  cam=cam(h=3.6, d=1.6, yaw=-10, pitch=-8, fov=45, move=push(0.25)),
  assets=['truck_cab'], sfx=['A_NIGHT (muffled)'])
S('balcony_box', 219, 3, type='insert (hands)', loc='hero_lot', tod='night', size='INS', angle='top-down', grade='night', light='truck cargo dome light + lantern',
  pic="On the truck ramp, his hands rip open the BALCONY GNOME box (Grandpa tucked under one arm, lantern lit) and on \"plastic\" lift out Mom's shiny plastic gnome: red hat, $4.99 sticker, dead dot eyes, smile.",
  cast=[who('the hero (hands)', HERO_B, 'armR rip, then lift'), who('plastic gnome', "K.makePlasticGnome({ finish: 'glossy' })", 'in the box, lifted out')],
  cam=cam(h=6.5, pitch=-90, fov=50, move=push(0.22)),
  ev=[ev(221, 'tape rips', 'RIP'), ev(223, 'plastic gnome lifted out (8-frame pose)', None)],
  assets=['moving_truck', 'gnome_plastic', 'hero'], sfx=[])
S('plant_plastic', 225, 3, type='action', loc='hero_lot', tod='night', size='MS', angle='eye (kneeling)', grade='nightHigh', light='nightLawn + lantern',
  pic="Under Theo's lit window, the hero kneels and plants the plastic gnome in Grandpa's empty ring; it wobbles; he backs off with Grandpa and the light leaves the bed.",
  cast=[who('the hero (11)', HERO_B + ' + lit gnome', 'kneelPlace -> stand, step back', 'determined'), who('plastic gnome', "K.makePlasticGnome({ finish: 'glossy' })", 'planted, wobble spring')],
  cam=cam(h=3.0, d=7.0, yaw=-25, pitch=0, fov=70, move=push(0.18)),
  ev=[ev(225, 'plastic gnome thunks into the soil', 'THUNK_PLASTIC')],
  assets=['hero_lot', 'hero', 'gnome_grandpa', 'gnome_plastic', 'fx_lantern_ring'], sfx=['A_NIGHT'])
S('gulp', 228, 3, type='creature action + VFX (hides the swallow)', loc='hero_lot', tod='night', size='CU', angle='low', grade='nightHigh', light='nightLawn (no lantern on the bed: cool)',
  pic="GULP: a mound surges over the plastic gnome, the turf closing round it like a mouth; it sinks in 6 frames, the turf seals and burps crumbs. \"Gone.\": the $4.99 price sticker flutters down onto the bare soil.",
  cam=cam(h=0.8, d=2.5, yaw=-25, pitch=6, fov=70, move=push(0.20), note='event shake 6 px for 0.3 s on GULP'),
  ev=[ev(228, 'swallow (moleField.swallow) + soil burst', 'GULP'), ev(229, 'price sticker flutters down (0.4 s)', 'FLUTTER')],
  assets=['hero_lot', 'gnome_plastic', 'moles', 'mole_field', 'fx_soil', 'fx_sticker', 'fx_shake'], sfx=[])
S('mounds_closer', 230, 3, type='action (dolly push)', loc='hero_lot', tod='night', size='WS', angle='low', grade='nightHigh', light='nightLawn',
  pic="Low behind the mounds as they roll across our lawn toward the house: the dark flowerbed and Theo's lit window ahead.",
  cam=cam(h=0.6, d=10, yaw=0, pitch=5, fov=70, move=push(0.19, 'dolly')),
  ev=[ev(232, 'mounds travel 3 studs/s toward the bed', 'RUMBLE_ROLL')],
  assets=['hero_lot', 'mole_field', 'moles'], sfx=['A_NIGHT'])
S('mounds_flowers', 234, 3, type='list insert', loc='hero_lot', tod='night', size='CU', angle='low', grade='nightHigh', light='nightLawn + window spill',
  pic="Snouts poke up among the tulips, sniffing the stems; the tulips quiver.",
  cam=cam(h=0.6, d=1.8, yaw=-20, pitch=6, fov=60, move=push(0.22)),
  ev=[ev(236, 'tulips shake, snouts wriggle', 'SNIFF')],
  assets=['hero_lot', 'moles'], sfx=[])
S('mounds_bricks', 237, 3, type='list insert', loc='hero_lot', tod='night', size='CU', angle='low', grade='nightHigh', light='nightLawn + window spill',
  pic="Mounds bump over the flowerbed's brick edging under the window, jostling a brick loose.",
  cam=cam(h=0.7, d=2.0, yaw=15, pitch=4, fov=60, move=push(0.20)),
  ev=[ev(239, 'a brick tips out (10 deg)', 'BRICK')],
  assets=['hero_lot', 'mole_field'], sfx=[])
S('eyes_fog_glass', 240, 3, type='list insert (reverse, inside)', loc='hero_room', tod='night (interior)', size='CU', angle='eye', grade='bedroom', light='bedroomNight; the amber eyes glow outside',
  pic="From inside the room: Theo asleep in the foreground; behind him at the window two amber eyes rise outside the glass and their breath fogs the pane on \"glass\".",
  cast=[who('Theo', THEO + ' + whale', 'asleep', 'sleeping')],
  cam=cam(h=2.0, d=3.0, yaw=0, pitch=2, fov=70, move=push(0.25)),
  ev=[ev(242, 'fog blooms on the pane (0.35 s)', 'BREATH')],
  assets=['hero_room', 'theo', 'whale', 'moles', 'fx_glass_fog'], sfx=['A_ROOM'])
S('ran_back', 243, 3, type='action (high WS)', loc='hero_lot', tod='night', size='WS', angle='high', grade='nightHigh', light='nightLawn + lantern ring',
  pic="High: the hero runs back with the lit gnome and plants his bare feet in the flowerbed on \"back\"; on \"backed off\" the circle of light pushes the mounds back like a tide.",
  cast=[who('the hero (11)', HERO_B + ' + lit gnome', 'runCycle -> stand (stop on \"back\")', 'angry')],
  cam=cam(h=10, d=14, yaw=-30, pitch=-35, fov=65, move=push(0.16, crane_studs=-0.5)),
  ev=[ev(246, 'feet plant in the bed', 'FEET_WET'), ev(249, 'tide: mounds pushed back 3 studs in 0.5 s', 'TIDE')],
  assets=['hero_lot', 'hero', 'gnome_grandpa', 'mole_field', 'fx_lantern_ring'], sfx=[])
S('stand_guard', 251, 3, type='reaction MS', loc='hero_lot', tod='night', size='MS', angle='eye', grade='nightHigh', light='lantern under-light + cool rim',
  pic="\"Fine.\" Angry brows, he hugs the gnome tighter; behind him across the lawn the truck waits at the kerb, back open.",
  cast=[who('the hero (11)', HERO_B + ' + lit gnome', 'hug tighter (4 deg squeeze)', 'angry')],
  cam=cam(h=4.6, d=6.5, yaw=-15, pitch=-2, fov=70, move=push(0.19)),
  assets=['hero_lot', 'hero', 'gnome_grandpa', 'moving_truck'], sfx=[])
S('tomorrow_night', 257, 4, type='reaction CU', loc='hero_lot', tod='night', size='CU', angle='eye', grade='nightHigh', light='lantern under-light',
  pic="Slow push on his face as it sinks in: worried; behind him the snouts wait just outside the light, amber eye pairs at its edge.",
  cast=[who('the hero (11)', HERO_B, 'hug', 'sad')],
  cam=cam(h=4.6, d=2.4, yaw=10, pitch=0, fov=70, move=push(0.25)),
  assets=['hero', 'moles', 'fx_lantern_ring'], sfx=['SNIFF (distant)'])
S('head_grind', 260, 4, type='creature action (creepy head turn)', loc='hero_lot', tod='night', size='CU', angle='low', grade='nightHigh', light='lantern + cool rim',
  pic="Close on the gnome in his arms: his ceramic head grinds round 150 deg, away from the hero, in stepped jerks.",
  cast=[who('Grandpa gnome', GP_LIT, 'K.gnomeHeadTurn(t, t0 = 66.55 - shot start, 0.8 s, 0 -> 150, jitter 2.5 every 3 frames)')],
  cam=cam(h=2.6, d=1.4, yaw=-35, pitch=10, fov=70, move=push(0.20)),
  ev=[ev(66.55, 'head turn starts (0.8 s inOutSine, ends 0.1 s before the cut)', 'GRIND (peaks on \"head\")')],
  assets=['gnome_grandpa', 'hero', 'fx_sparkles'], sfx=[])
S('away_to_window', 264, 4, type='OTS + whip pan accent (replaces the script\'s rack focus)', loc='hero_lot', tod='night', size='OTS', angle='low', grade='nightHigh', light='lantern + window',
  pic="Lower and closer, over the gnome's turned head: the hero's hurt face above (\"away from me\"); on \"toward\" the camera whips past the hat to Theo's window: Theo asleep behind the glass, lit.",
  cast=[who('the hero (11)', HERO_B, 'hug', 'sad'), who('Theo', THEO, 'asleep inside', 'sleeping')],
  cam=cam(h=2.3, d=0.9, yaw=160, pitch=20, fov=70, move={'type': 'whip_pan', 't0_word': 267, 'dur': 0.5, 'deg': 55, 'ease': 'inOutSine', 'base_push': 0.12},
          accent='whip pan 55 deg (about 1500 px) in 0.5 s from \"toward\", inOutSine, frames sharp; +12 % push'),
  assets=['hero', 'gnome_grandpa', 'hero_room', 'theo'], sfx=[])

# =================================================================== twist 2 and the choice (part 4 = s58-s76, 65.43-86.77 s)
S('fb_flashlight', 271, 4, owner=1, callback='s20', type='callback (exact set-up of s20)', loc='hero_lot', era='2010s', tod='night (sepia)', size='INS', angle='eye', grade='sepia', light='nightLawn, sepia',
  pic="Callback: the same flashlight insert as s20, same framing and grade.", ev=[ev(271, 'flashlight on', 'CLICK_TORCH')], assets=['grandpa_human', 'flashlight', 'fx_beam'], sfx=[])
S('fb_slippers', 272, 4, owner=1, callback='s21', type='callback (exact set-up of s21)', loc='hero_lot', era='2010s', tod='night (sepia)', size='INS', angle='ground level', grade='sepia', light='sepia',
  pic="Callback: the same slippers insert as s21.", ev=[ev(272, 'slipper lands', 'STEP_WET')], assets=['grandpa_human', 'fx_dew'], sfx=[])
S('fb_lap', 273, 4, owner=1, callback='s22', type='callback (exact set-up of s22)', loc='hero_lot', era='2010s', tod='night (sepia)', size='WS', angle='top-down aerial', grade='sepia', light='sepia',
  pic="Callback: the same top-down lap as s22, the kink again in frame.", assets=['hero_lot', 'grandpa_human', 'fx_beam'], sfx=[])
S('fb_one_stop', 275, 4, type='flashback reveal (crane-down accent)', loc='hero_lot', era='2010s', tod='night (sepia)', size='aerial -> MS', angle='top-down -> eye (behind)', grade='sepia', light='sepia night + torch + window',
  pic="From the lap's top-down view the camera cranes down into the kink: Grandpa stops in this flowerbed under the window, flashlight resting on the lawn; inside, the hero aged 5 asleep.",
  cast=[who('Grandpa (man)', "K.makeCharacter('grandpa')", 'walk -> stop on \"stop\", torch pointed at the lawn', 'heartfelt'), who('the hero aged 5', "K.makeCharacter('heroKid5')", 'asleep in bed', 'sleeping')],
  cam=cam(h=34, pitch=-90, fov=45, move={'type': 'crane_down', 'from_h': 34, 'to_h': 4.6, 'to_pitch': -4, 'dur': 1.4, 'ease': 'outCubic', 'base_push': 0.10},
          accent='crane down 34 -> 4.6 studs and tilt -90 -> -4 deg in 1.4 s outCubic (about 2400 px), then +10 % push'),
  ev=[ev(277, 'Grandpa stops (walk -> stand, 8 frames)', None)],
  assets=['hero_lot', 'hero_room', 'grandpa_human', 'flashlight', 'fx_beam', 'hero_kid5'], sfx=['STEP_WET stops'])
S('hero_wet_eyes', 282, 4, type='reaction CU', loc='hero_lot', tod='night', size='CU', angle='eye', grade='nightHigh', light='lantern under-light (warm) + cool rim',
  pic="Back in the present: his eyes fill (wet-eyes decal), a choked half-laugh; the gnome warm in his arms at frame bottom.",
  cast=[who('the hero (11)', HERO_B + ' + lit gnome', 'hug', 'wetEyes')],
  cam=cam(h=4.6, d=2.3, yaw=-10, pitch=-2, fov=70, move=push(0.22), roll=-1.0),
  assets=['hero', 'gnome_grandpa', 'fx_sparkles'], sfx=[])
S('fb_checking_me', 285, 4, type='flashback (mirror pair A)', loc='hero_room', era='2010s', tod='night (sepia)', size='MS', angle='eye (inside)', grade='sepia', light='bedroomNight, sepia; torch beam outside',
  pic="From inside the room: the hero aged 5 asleep in his bed in the foreground; at the window Grandpa's kind face at the glass, his hand flat on the pane, his flashlight beam pointed at the lawn below, not into the room.",
  cast=[who('the hero aged 5', "K.makeCharacter('heroKid5')", 'asleep', 'sleeping'), who('Grandpa (man)', "K.makeCharacter('grandpa')", 'armL flat on the glass, armR torch down', 'heartfelt')],
  cam=cam(h=3.0, d=6.0, yaw=0, pitch=0, fov=70, move=push(0.19)),
  assets=['hero_room', 'hero_kid5', 'grandpa_human', 'flashlight', 'fx_beam'], sfx=[])
S('bw_dad', 290, 4, type='flashback (mirror pair B, identical framing to s66)', loc='hero_room', era='1960s', tod='night (B&W)', size='MS', angle='eye (inside)', grade='bw', light='bedroomNight, B&W',
  pic="The identical set-up in black and white, the 1960s: a younger Grandpa (dark hair and moustache) at the same window; asleep in an iron bed, a small boy with Dad's sticking-out ears.",
  cast=[who('young Dad', "K.makeCharacter('dadKid')", 'asleep', 'sleeping'), who('young Grandpa', "K.makeCharacter('grandpaYoung')", 'armL on the glass, torch down', 'heartfelt')],
  cam=cam(h=3.0, d=6.0, yaw=0, pitch=0, fov=70, move=push(0.19), note='same camera numbers as s66 (mirror pair)'),
  assets=['hero_room', 'dad_kid', 'grandpa_young', 'flashlight', 'fx_beam'], sfx=[])
S('decades_window', 296, 4, type='montage jump cut 1 (exterior set-up)', phase='1990s', loc='hero_lot', era='1990s', tod='night (sepia)', size='MS', angle='eye-low (outside)', grade='sepia', light='sepia night + torch beam from frame left',
  pic="Outside the same window in the 1990s: yellow floral wallpaper, a little girl with pigtails asleep in a bunk; a flashlight beam from frame left (Grandpa off-screen) lies across the sill.",
  cast=[who('a 1990s kid', "K.makeCharacter('cousinKid')", 'asleep', 'sleeping')],
  cam=cam(h=2.5, d=6.0, yaw=20, pitch=4, fov=70, move=push(0.18), note='same framing as s45 (Theo\'s window from outside)'),
  assets=['hero_lot', 'hero_room', 'cousin_kid', 'fx_beam'], sfx=[])
S('decades_window', 299, 4, type='montage jump cut 2 (same set-up, now)', phase='now', loc='hero_lot', tod='night', size='MS', angle='eye-low (outside)', grade='nightHigh', light='nightLawn + lantern glow on the glass',
  pic="Same set-up, now: Theo asleep with his whale; instead of the flashlight, the gold lantern light lies on the glass.",
  cast=[who('Theo', THEO + ' + whale', 'asleep', 'sleeping')],
  cam=cam(h=2.5, d=6.0, yaw=20, pitch=4, fov=70, move=push(0.18)),
  assets=['hero_lot', 'hero_room', 'theo', 'whale', 'fx_lantern_ring'], sfx=['A_NIGHT'])
S('lawn_stare_lit', 305, 4, type='callback of s09 (same framing, lit)', loc='lawn_closeup', tod='night', size='low WS', angle='low (gnome eye level)', grade='nightHigh', light='nightLawn + lit lanterns',
  pic="The s09 framing again: low behind our family gnomes staring at the house, every lantern lit now, Theo's window lit with a small sleeping shape; in Grandpa's spot the hero stands holding him.",
  cast=[who('the hero (11)', HERO_B + ' + lit gnome', 'hug, in the bed', None, 'back to camera'), who('family gnomes', 'K.makeFamilyGnome(i, { lantern: 1 })', 'as s09')],
  cam=cam(h=1.4, d=3.0, fov=70, move={'type': 'pull', 'Z': 0.10, 'mode': 'fov', 'ease': 'linear'}, note='copy the s09 (part1 lawn_stare) camera block: near_slot bedFront0, back 3.0, side -1.6, height 1.4, aim 3.0'),
  assets=['lawn_closeup', 'hero', 'gnome_grandpa', 'gnome_family', 'fx_lantern_ring', 'hero_room', 'theo', 'fx_sparkles'], sfx=['A_NIGHT'])
S('big_in_window', 311, 4, type='reverse (inside): size contrast', loc='hero_room', tod='night (interior)', size='CU', angle='eye (inside)', grade='bedroom', light='bedroomNight + lantern from outside',
  pic="From inside: the hero's face fills the window from outside, big against the frame, lit gold by the lantern; Theo small and asleep at the bottom of frame.",
  cast=[who('the hero (11)', HERO_B, 'looking in', 'heartfelt'), who('Theo', THEO, 'asleep (foreground bottom)', 'sleeping')],
  cam=cam(h=2.2, d=4.0, yaw=0, pitch=6, fov=70, move=push(0.19)),
  assets=['hero_room', 'hero', 'theo', 'whale', 'fx_sparkles'], sfx=['A_ROOM'])
S('theo_lantern_cheek', 315, 4, type='reaction CU', loc='hero_room', tod='night (interior)', size='CU', angle='high', grade='bedroom', light='bedroomNight + warm lantern band across his cheek',
  pic="\"Theo was.\" Theo asleep, a band of gold lantern light across his cheek through the glass.",
  cast=[who('Theo', THEO + ' + whale', 'asleep', 'sleeping')],
  cam=cam(h=3.0, d=1.6, yaw=10, pitch=-45, fov=70, move=push(0.18)),
  assets=['hero_room', 'theo', 'whale', 'fx_sparkles'], sfx=[])
S('knelt_bed', 317, 4, type='plain push + silence beat', loc='hero_lot', tod='night', size='MS', angle='eye-low', grade='nightHigh', light='nightLawn + lantern',
  pic="He kneels in the soil beside the hole the plastic gnome left (sunken soil, the $4.99 sticker), Grandpa in both hands, the lit window above. Held through the pause.",
  cast=[who('the hero (11)', HERO_B + ' + lit gnome', 'kneel (10-frame snap on \"knelt\")', 'heartfelt')],
  cam=cam(h=2.2, d=7.0, yaw=-30, pitch=4, fov=70, move=push(0.16)),
  ev=[ev(318, 'kneel', 'KNEEL')],
  assets=['hero_lot', 'hero', 'gnome_grandpa', 'fx_lantern_ring', 'fx_sparkles'], sfx=['A_NIGHT'])
S('hero_goodnight', 323, 4, type='reaction CU', loc='hero_lot', tod='night', size='CU', angle='eye', grade='nightHigh', light='lantern under-light',
  pic="The hero, kneeling, whispers goodnight to the gnome in his hands, tender.",
  cast=[who('the hero (11)', HERO_B, 'kneel', 'heartfelt')],
  cam=cam(h=3.4, d=2.0, yaw=-10, pitch=0, fov=70, move=push(0.20)),
  assets=['hero', 'fx_sparkles'], sfx=[])
S('slow_blink', 327, 4, type='creature CU + slow blink', loc='hero_lot', tod='night', size='CU -> ECU', angle='eye (gnome level)', grade='nightHigh', light='lantern under-light (warm) + cool rim',
  pic="Close on the gnome in his hands: on \"blinked\" a slow blink (4 frames closed, half-closed frames either side); on \"sorry\" the lids settle a little low, like he is sorry.",
  cast=[who('Grandpa gnome', GP_LIT, 'held; gaze at the hero')],
  cam=cam(h=2.5, d=1.3, yaw=-10, pitch=0, fov=70, move=push(0.28)),
  ev=[ev(329, 'slow blink (K.gnomeBlink frames 4, slow)', 'TIK_SLOW'), ev(334, 'lids settle to 0.3', None)],
  assets=['gnome_grandpa', 'fx_sparkles', 'fx_magic_dust'], sfx=[])
S('set_down_let_go', 335, 4, type='insert (hands)', loc='hero_lot', tod='night', size='INS', angle='slightly high', grade='nightHigh', light='lantern',
  pic="His hands set the gnome back in its ring of soil, facing the window; on \"go\" the hands open and lift away: empty hands in lantern light.",
  cast=[who('the hero (hands)', HERO_B, 'kneelPlace -> hands lift (8 frames on \"go\")'), who('Grandpa gnome', GP_LIT, 'set in bed0, facing the window')],
  cam=cam(h=2.0, d=2.2, yaw=-20, pitch=-30, fov=55, move=push(0.20)),
  ev=[ev(337, 'gnome touches the soil', 'SET_DOWN'), ev(342, 'hands lift away', None)],
  assets=['hero', 'gnome_grandpa', 'fx_lantern_ring'], sfx=[])
S('fwoom_flare', 343, 5, type='magic glow moment (P3) + strong push', loc='hero_lot', tod='night', size='CU', angle='low', grade='nightHigh -> magic (in-shot on FWOOM, 8 frames)', light='magicGlow (rig.fwoom)',
  pic="FWOOM: low on the gnome in his bed; the lantern flares white-gold, a burst ring and gold/pink motes fly out, the grade swings warm; on \"flared\" a second, smaller pulse.",
  cast=[who('Grandpa gnome', "K.makeGnome('grandpa', { lantern: 1, lanternLight: 8 })", 'K.setLantern 1 -> 6 -> 2')],
  cam=cam(h=0.6, d=2.2, yaw=-15, pitch=14, fov=70, move=push(0.24), note='event shake +-10 px for 0.4 s on FWOOM'),
  ev=[ev(86.86, 'FWOOM (on the vowel): lantern 8 -> 50 cd in 0.15 s, emissive x25, burst + streaks, grade to magic in 8 frames', 'FWOOM'), ev(346, 'second pulse (to 20 cd)', None)],
  assets=['gnome_grandpa', 'fx_fwoom', 'fx_burst', 'fx_grade_blend', 'fx_magic_dust', 'fx_sparkles', 'fx_shake'], sfx=[])
S('light_rolls', 347, 5, type='fast truck accent (following the wave)', loc='hero_lot', tod='night', size='WS', angle='ground level', grade='magic', light='magicGlow',
  pic="Ground level: a rolling wall of gold light sweeps across the lawn left to right past the lens, lighting every blade, sparkles kicked up at its front.",
  cam=cam(h=0.5, d=6.0, yaw=90, pitch=2, fov=70, move=push(0.12, truck_studs=11), accent='fast truck with the wave, 8 studs/s (about 1900 px/s)'),
  ev=[ev(349, 'the wave passes the lens', 'PASS')],
  assets=['hero_lot', 'fx_fwoom', 'fx_sparkles', 'mole_field'], sfx=['FWOOM tail'])
S('mounds_sink', 352, 5, type='quantity (top-down aerial, crane drift)', loc='hero_lot', tod='night', size='WS (aerial)', angle='top-down aerial', grade='magic', light='magicGlow',
  pic="Top-down over the lawn: as the ring passes, every mound deflates in turn and the turf settles flat behind it.",
  cam=cam(h=14, d=12, yaw=-10, pitch=-90, fov=60, move=push(0.12, crane_studs=2.0)),
  ev=[ev(354, 'mounds sink, staggered 0.15 s, following the ring', 'DEFLATE')],
  assets=['hero_lot', 'mole_field', 'moles', 'fx_fwoom', 'gnome_grandpa'], sfx=[])
S('eyes_wink_out', 356, 5, type='creature event list', loc='hero_lot', tod='night', size='MS', angle='low', grade='magic -> night (blend 1 -> 0.4 over the shot)', light='magicGlow decaying',
  pic="Low across the dark lawn beyond the light: five amber eye pairs blink out one pair at a time, the last on the final \"pair\".",
  cam=cam(h=1.0, d=8.0, yaw=0, pitch=2, fov=60, move=push(0.19)),
  ev=[ev(357, 'pair 1 out', 'BLIPS'), ev(358, 'pair 2 out', None), ev(359, 'pair 3 out', None), ev(360, 'pair 4 out', None), ev(361, 'pair 5 (last) out', None)],
  assets=['moles', 'mole_field', 'fx_fwoom', 'fx_grade_blend'], sfx=[])
S('quiet_wide', 362, 5, type='quiet wide', loc='hero_lot', tod='night', size='WS', angle='slightly high', grade='nightHigh', light='nightLawn + steady lantern (level 1)',
  pic="The diminishing image: a small gnome in a flowerbed, lantern low and steady, a sleeping boy's window above, the hero tiny on the lawn sitting back on his heels.",
  cast=[who('the hero (11)', HERO_B, 'sitFloor', 'content', 'tiny'), who('Grandpa gnome', GP_LIT, 'bed0, facing the window')],
  cam=cam(h=7.0, d=24, yaw=-10, pitch=-10, fov=60, move=push(0.12, 'dolly')),
  assets=['hero_lot', 'hero', 'gnome_grandpa', 'gnome_family', 'fx_lantern_ring', 'fx_sparkles'], sfx=['A_NIGHT returns'])

# =================================================================== dawn, the truck, the photos, 71 (part 5 = s77-s97, 86.77-113.30 s; FWOOM s77-s81 is above)
S('dawn_theo_out', 369, 5, type='establishing (dawn)', loc='hero_lot', tod='dawn', size='WS', angle='low', grade='dawn', light='dawn (P4: sun el 10 behind-side, lanterns 0.5)',
  pic="Pink dawn over our house: the front door opens on \"came\" and Theo pads out onto the dewy step in striped socks, pyjamas, whale under his arm; the hero sits muddy-kneed by Grandpa in the flowerbed.",
  cast=[who('Theo (6)', "K.makeCharacter('theo', socks)", 'walkCycle 1.0 s, small steps', 'sleeping -> wonder'), who('the hero (11, muddy)', HERO_B + ' (mud)', 'sitFloor', 'content'), who('Grandpa gnome', "K.makeGnome('grandpa', { lantern: 0.5 })", 'bed0')],
  cam=cam(h=0.8, d=12, yaw=15, pitch=6, fov=70, move=push(0.15, 'dolly')),
  ev=[ev(372, 'front door opens (14 frames)', 'DOOR_CREAK')],
  assets=['hero_lot', 'theo', 'theo_socks', 'whale', 'hero_muddy', 'gnome_grandpa', 'fx_dew'], sfx=['A_DAWN'])
S('theo_asks', 377, 5, type="dialogue (Theo's line)", loc='hero_lot', tod='dawn', size='MCU', angle='eye (Theo height)', grade='dawn', light='dawn',
  pic="\"Is he nice?\" Theo points at the gnome, sleepy and curious.",
  cast=[who('Theo (6)', THEO + ' + whale', 'point (0.45 s rise)', 'wonder')],
  cam=cam(h=3.8, d=3.0, yaw=-10, pitch=0, fov=70, move=push(0.18)),
  assets=['theo', 'whale', 'fx_dew'], sfx=[])
S('hero_nicest', 380, 5, type="dialogue (the hero's line)", loc='hero_lot', tod='dawn', size='CU', angle='eye', grade='dawn', light='dawn (sun rim)',
  pic="\"The nicest.\" The hero smiles with wet eyes, a smudge of mud on his cheek.",
  cast=[who('the hero (11, muddy)', HERO_B + ' (mud)', 'sitFloor', 'wetEyes')],
  cam=cam(h=3.2, d=2.2, yaw=10, pitch=0, fov=70, move=push(0.18)),
  assets=['hero_muddy'], sfx=[])
S('nudge_theo', 382, 5, type="dialogue (two-shot)", loc='hero_lot', tod='dawn', size='MS', angle='eye', grade='dawn', light='dawn',
  pic="\"Say goodnight, and he'll blink.\" Two-shot: the hero, kneeling, nudges Theo forward toward the gnome with a hand on his shoulder.",
  cast=[who('the hero (11, muddy)', HERO_B + ' (mud)', 'kneel; hand on shoulder (16 frames)', 'heartfelt'), who('Theo (6)', THEO + ' + whale', 'stand, small step forward', 'wonder')],
  cam=cam(h=3.5, d=8.0, yaw=-20, pitch=-2, fov=70, move=push(0.19)),
  assets=['hero_muddy', 'theo', 'whale', 'gnome_grandpa', 'fx_dew'], sfx=[])
S('theo_blink_twoshot', 388, 5, type='deep two-shot + blink', loc='hero_lot', tod='dawn', size='CU (foreground) + MS', angle='low', grade='dawn', light='dawn',
  pic="Low: the gnome's face 3/4 in the left foreground, big; Theo behind at right waves shyly and mouths goodnight; on \"blinked\" the gnome blinks (2 frames).",
  cast=[who('Grandpa gnome', "K.makeGnome('grandpa', { lantern: 0.5 })", 'gaze at Theo'), who('Theo (6)', THEO + ' + whale', 'wave (small, 2 Hz)', 'content')],
  cam=cam(h=1.1, d=1.6, yaw=40, pitch=6, fov=70, move=push(0.20)),
  ev=[ev(393, 'blink, 2 frames', 'TIK')],
  assets=['gnome_grandpa', 'theo', 'whale'], sfx=[])
S('theo_o', 394, 5, type='reaction CU', loc='hero_lot', tod='dawn', size='CU', angle='eye (Theo height)', grade='dawn', light='dawn',
  pic="\"At Theo.\" Theo's mouth becomes a delighted \"o\".",
  cast=[who('Theo (6)', THEO, 'stand', 'wonder')],
  cam=cam(h=3.6, d=2.0, yaw=-10, pitch=0, fov=70, move=push(0.16)),
  assets=['theo'], sfx=['ENGINE starts (off-screen) at 100.37'])
S('truck_pov', 396, 5, type='POV from the moving truck (dolly-back accent)', loc='street_night', tod='dawn', size='WS', angle='eye (from the cargo bay)', grade='dawn', light='dawn (sun low ahead)',
  pic="From the open back of the moving truck at sunrise, pulling away: box edges frame the shot; the street recedes; on every lawn a gnome faces its house, lanterns dimmed; Theo small on our lawn beside Grandpa.",
  cam=cam(h=6.0, d=0, yaw=180, pitch=-6, fov=70, move=push(0.10, 'dolly', dolly_back_studs=10), accent='dolly back with the truck 0 -> 6 studs/s (truck leaving) + handheld 0.3 deg'),
  assets=['street_night', 'moving_truck', 'gnome_family', 'gnome_grandpa', 'theo'], sfx=['ENGINE', 'RATTLE', 'A_DAWN'])
S('grandpa_turned', 404, 5, type='tele CU + head turn (silence beat)', loc='hero_lot', tod='dawn', size='CU (tele)', angle='eye (from the truck)', grade='dawn', light='dawn',
  pic="Tele from the truck: Grandpa in his flowerbed with his head turned toward the truck, looking at us, Theo beside him; as the truck turns the corner he turns back to Theo's window. Held through the pause.",
  cast=[who('Grandpa gnome', "K.makeGnome('grandpa', { lantern: 0.5 })", 'head yaw 90 -> 0 (gnomeHeadTurn 0.8 s from 103.05)'), who('Theo (6)', THEO + ' + whale', 'stand', 'content')],
  cam=cam(h=4.0, d=40, yaw=180, pitch=-4, fov=25, move=push(0.15), note='handheld truck vibration +-3 px'),
  ev=[ev(103.05, 'head turns back to the window (0.8 s)', 'GRIND (soft)')],
  assets=['hero_lot', 'gnome_grandpa', 'theo'], sfx=['ENGINE fades'])
S('polaroid_stack', 406, 5, type='list (in-shot drops), top-down insert', loc='back_garden', tod='dusk (photos in day)', size='INS', angle='top-down', grade='dusk (photo textures in day)', light='dusk',
  pic="Top-down on a garden table at dusk: Polaroids drop one by one onto a pile, each the same gnome under the same window with Theo beside him, older in each (7, 10, 16, 25, 40).",
  cam=cam(h=7.0, pitch=-90, fov=45, move=push(0.22), roll=-2.0),
  ev=[ev(407, 'photo 1 lands', 'DROPS'), ev(409, 'photo 2 lands', None), ev(410, 'photo 3 lands', None), ev(104.75, 'photo 4 lands', None)],
  assets=['back_garden', 'garden_table', 'polaroids', 'gnome_grandpa_aged', 'theo_aged', 'fx_photo_look'], sfx=['A_DUSK'])
S('phone_reveal', 411, 5, type='reveal (pull-back accent)', loc='back_garden', tod='dusk', size='ECU -> MCU', angle='eye', grade='dusk', light='dusk (sun low, warm side light)',
  pic="ECU of a phone screen with a new photo from Theo: the gnome, mossy and faded, hat green with lichen, under the window; pull back: the phone is in an old, freckled hand with a mustard cardigan cuff.",
  cast=[who('the narrator at 71 (hand)', "K.makeCharacter('heroOld')", 'holding the phone')],
  cam=cam(h=3.6, d=1.0, yaw=0, pitch=-10, fov=50, move={'type': 'pull', 'x': 2.5, 'ease': 'outExpo', 'dur': 0.9}, accent='pull-back x2.5 outExpo + linear push +6 % after'),
  ev=[ev(412, 'message ping, the photo slides up', 'PING')],
  assets=['phone', 'polaroids', 'hero_old', 'gnome_grandpa_aged', 'back_garden'], sfx=[])
S('phone_swipes', 416, 5, type='list (in-shot swipes)', loc='back_garden', tod='dusk', size='INS', angle='top-down (over his shoulder)', grade='dusk (photos in day)', light='dusk',
  pic="Over his shoulder, his thumb swipes: \"Grandpa\" (the gnome close, mossy), \"same flowerbed\" (another year's tulips), \"same window\" (another year's curtains, Theo grey at the window).",
  cast=[who('the narrator at 71', "K.makeCharacter('heroOld')", 'phone in the right hand, thumb swipes')],
  cam=cam(h=4.6, d=1.4, yaw=200, pitch=-35, fov=45, move=push(0.19)),
  ev=[ev(417, 'swipe to the flowerbed photo (8 frames)', 'SWIPE'), ev(420, 'swipe to the window photo', None)],
  assets=['phone', 'polaroids', 'hero_old', 'gnome_grandpa_aged', 'theo_aged'], sfx=[])
S('photo_midblink', 422, 5, type='insert (full-frame photo)', loc='polaroids', tod='photo (day)', size='INS (full frame)', angle='eye', grade='day (photo look)', light='day (photo)',
  pic="The newest photo fills the frame: Grandpa gnome caught mid-blink (lids half shut), Theo at 66 (bald, grey beard) giving a thumbs up beside him, and a little girl in pyjamas waving from the window above: Theo's granddaughter.",
  cast=[who('Grandpa gnome (aged)', "K.makeGnome('grandpa', { age: 0.9 })", 'lids 0.55'), who('Theo at 66', 'C.theoAt(66)', 'thumbs up', 'grin'), who("Theo's granddaughter", "K.makeCharacter('theoGranddaughter')", 'wave in the window', 'openSmile')],
  cam=cam(h=3.0, d=4.0, fov=50, move=push(0.25)),
  assets=['polaroids', 'gnome_grandpa_aged', 'theo_aged', 'theo_granddaughter', 'fx_photo_look'], sfx=[])
S('old_reveal', 425, 5, type='character reveal (punch-in accent)', loc='back_garden', tod='dusk', size='CU', angle='eye (seated)', grade='dusk', light='dusk (warm side sun)',
  pic="I'm 71: the narrator, grey hair and moustache, mustard cardigan, olive fishing hat, freckles, on a garden bench with the phone; content.",
  cast=[who('the narrator at 71', "K.makeCharacter('heroOld')", 'sit', 'content')],
  cam=cam(h=3.5, d=2.6, yaw=-15, pitch=0, fov=70, move={'type': 'punch', 'x': 1.5, 't0_word': 426, 'dur': 0.5, 'ease': 'linear', 'base_push': 0.10}, roll=10,
          accent='punch-in x1.5 in 0.5 s on \"seventy\" + roll 10 deg'),
  assets=['back_garden', 'hero_old', 'phone'], sfx=['A_DUSK'])
S('bench_granddaughter', 428, 5, type='mirror of s06 (same composition)', loc='back_garden', tod='dusk', size='MS', angle='eye (seated head)', grade='dusk', light='dusk',
  pic="The s06 composition at dusk: the narrator on the bench, slippers on the grass; his granddaughter beside him, hands on hips, frowning at him.",
  cast=[who('the narrator at 71', "K.makeCharacter('heroOld')", 'sit', 'content'), who('granddaughter', "K.makeCharacter('granddaughter')", 'stand, hands on hips (arms 30 out)', 'sideGlance')],
  cam=cam(h=3.6, d=7.5, yaw=-15, pitch=-4, fov=70, move=push(0.18), note='same numbers as s06'),
  assets=['back_garden', 'hero_old', 'granddaughter'], sfx=['A_DUSK'])
S('bench_granddaughter', 434, 5, type='mirror jump cut of s07', phase='short', loc='back_garden', tod='dusk', size='MS', angle='eye (seated head)', grade='dusk', light='dusk',
  pic="Jump cut, same camera: he is smaller (x0.85), slippers dangling off the grass, sleeves over his hands.",
  cast=[who('the narrator at 71 (short)', "K.makeCharacter('heroOld', { scale: 0.85, hand: 'sleeve' })", 'sit, feet dangling', 'wonder'), who('granddaughter', "K.makeCharacter('granddaughter')", 'as s95', 'sideGlance')],
  cam=cam(h=3.6, d=7.5, yaw=-15, pitch=-4, fov=70, move=push(0.18)),
  assets=['back_garden', 'hero_old_short', 'granddaughter'], sfx=[])
S('final_window', 435, 5, type='ending (strong push to the frame-0 match)', loc='back_garden', tod='blue hour -> night', size='MS -> ECU', angle='eye (from the window side)', grade='night (matches frame 0)', light='nightStreet-like: warm window spill 2.8 cd from behind the lens, galaxy sky, TF moon',
  pic="Reverse angle from the granddaughter's lit window: he lowers himself into the striped deck chair facing it (facing the lens), the TF moon rising behind his hat; a long linear push ends on an ECU of his face in the same screen position and size as frame 0's gnome face; on \"window\" a dandelion clock beside the chair releases its seeds. Last frame = loop match to frame 0.",
  cast=[who('the narrator at 71', "K.makeCharacter('heroOld')", 'sit-down (0.4 s, 12 frames) then sit', 'content')],
  cam=cam(h=3.4, d=7.0, yaw=0, pitch=2, fov=62, move={'type': 'push', 'Z': 0.8, 'mode': 'dolly', 'ease': 'linear'}, accent='strong push x1.8 (dolly) to the frame-0 ECU framing; fov 62 like s01 frame 0', note='match frame 0: face centre at the frame-0 gnome eyes position, moon at az -16 el 32 relative to the view'),
  ev=[ev(439, 'dandelion seeds lift (burst puff 14)', 'POOF_SOFT')],
  assets=['back_garden', 'hero_old', 'fx_dandelion', 'fx_sparkles'], sfx=['A_NIGHT crickets fade in (loop into s01)'])
