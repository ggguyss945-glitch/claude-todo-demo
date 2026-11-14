"""plan/make_plan.py: resolve plan/shotlist.py into plan/shots.json and plan/sound_plan.json.

    python3 plan/make_plan.py            # writes both JSON files, then run plan/validate.py

shots.json
    meta: title, fps, size, duration, lead, sources
    shots[]: id, t0, t1, dur, section, lines (indices overlapping the shot), cut_on_clause, set, view, var, side, type,
             frame, cam {move, keys [[t, x, y, zoom, roll]...], ease, shake, rate_pct_s, pan_px_s, snap?, hit?}, lens, grade,
             dof, chars[] {who, at, view, expr, acts [[t, clip, params]], mode, ...}, props (full state at t0 + changes inside
             the shot), hud[] (tags, red X, labels, time card, phone UI, rule card, counter events), captions (bool),
             header {left, clock_mode, clock_at_t0}, counter (value at t0 or null), tr (transition in), intensity (0-10),
             energy (what moves), voice_fx, fx_post, bg (rule cards), sfx[] (also in sound_plan), mus[]
    captions[]: t0, t1, text, line   (one line, ~5 words, hidden under rule cards)
    header: spec of the in-world clock; counter: spec + steps; rule_cards[]; sections[]
sound_plan.json
    names {existing[], new{}}; sfx[] (every cue, with shot id, perspective, notes, exists); beds[]; music {sections[],
    intensity[[t, 0..1]], events[]}; voice_fx{}; epidemic_wishlist{sfx[], music[]}; stats
"""
import json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dsl
from dsl import SHOTS, LINES, DUR, LEAD, resolve, t, e, w
import shotlist as SL

FILM = dsl.FILM
END = 700.0                    # narration ends 698.58; 1.4 s of black tail with the hit and bell tails (42,000 frames)
FPS = 60
TITLE = 'If An Eighth Step Appears On Your Mirror... WIPE THE GLASS CLEAN'

# ---------------------------------------------------------------- existing SFX names (audio/sfx.py NAMES)
EXISTING = ['knock_door', 'doorbell_chime', 'footsteps_porch', 'footsteps_wood_inside', 'car_pass', 'car_idle', 'car_door_open',
            'car_door_close', 'siren_far', 'police_radio_squelch', 'radio_click', 'radio_static', 'bodycam_beep', 'phone_ring',
            'phone_busy', 'phone_vibrate', 'phone_pickup', 'mail_slot', 'paper', 'pen_click', 'key_in_lock', 'lock_turn',
            'chain_lock', 'door_creak', 'breath', 'heartbeat', 'whoosh', 'riser', 'braam', 'impact_hit', 'sub_drop', 'stinger',
            'glitch', 'ui_pop', 'typing', 'tinnitus', 'ambience_night', 'room_tone', 'clock_tick', 'countdown_tick', 'tv_off',
            'crowd_whisper']

# new names: description, how to build it (E = owner's new Epidemic download first, L = free library, S = synthesis layer)
NEW = {
    'lipstick_draw': ('waxy lipstick stroke on glass (squeak + crumbly drag); clean=True: thinner, glassy, too-perfect line', 'E "marker on glass / squeak"; S: band-passed friction noise with stick-slip'),
    'lipstick_smear': ('finger smearing lipstick on glass; kind crumb = tiny crumbs rubbed between fingers', 'E "finger squeak glass"; L sfx/creaks_scrapes'),
    'nail_click_glass': ('ONE crisp fingernail click on clean glass (the film\'s signature sound, used at 143.29 and 690.19 identically)', 'E "nail tap glass"; S: 2-3 kHz modal click + short glass ring'),
    'glass_tap': ('soft fingertip on glass', 'E "glass tap"; L sfx/clicks'),
    'glass_wipe': ('towel or sleeve wiping glass: squeal strokes (strokes=n, soft=True for the rule-card write-on)', 'E "glass wipe cloth squeak"'),
    'glass_resonance': ('glass pane ring / hum hit layer (rule cards, reveals, glass going dark)', 'L score/percussion/bowed_metals + vibraring; S modal glass'),
    'mirror_handle': ('wooden mirror frame: scrape on floorboards, creak in the grip, bump', 'L sfx/creaks_scrapes, sfx/impacts/wood'),
    'towel_cloth': ('terry towel: rub, pull, snatch, flap/throw', 'E "towel cloth flap"; L sfx/foley/cloth'),
    'towel_drop': ('a towel falling straight down, soft heavy thump', 'E "cloth drop floor"; L impacts soft'),
    'cloth_press': ('fabric stretching over fingertips; satin rustle of the queen\'s dress; cotton seams straining', 'L sfx/foley/cloth slowed; E "fabric stretch"'),
    'cloth_grab': ('a hand grabbing a sleeve, collar or shoulder', 'L sfx/foley/cloth'),
    'jacket_cloth': ('canvas work jacket: scrape on a frame, swish, taken off', 'L sfx/foley/cloth + zipper'),
    'wet_footstep': ('wet footprint appearing (bare=True slap, False sneaker squelch), heard through glass', 'E "wet footsteps wood barefoot"'),
    'bare_foot_step': ('the queen\'s bare foot on a stair tread: wet slap, low weight', 'E "barefoot step wood wet"'),
    'water_drip': ('drip onto a towel / puddle; kind pour = water wrung out of a towel', 'E "water drip cloth"; L'),
    'drop_reverse': ('a drip played backward rising (the drop coming up), and the suck-back on loop resets', 'S from water_drip reversed + pitch rise'),
    'sprinkler_spit': ('impact lawn sprinkler: valve hiss on, two spits, gurgle and die; loop_id A/B must reuse the identical sample', 'E "lawn sprinkler impact"'),
    'bell_clean': ('THE FAKE BELL: one perfect clean bell note, long beautiful reverb, no rattle (far)', 'E "hand bell ring single"; S modal bell, D5'),
    'bell_cracked': ('THE REAL BELL: clean note then a thin rattle like a dropped spoon (strike padlock|clapper|drop|touch|roll, part note|rattle)', 'E "hand bell" + "spoon drop" layered; S rattle = amplitude-modulated buzz'),
    'spoon_drop': ('a spoon dropped on a table, bouncing (kind clink = light cutlery)', 'E "spoon drop table"'),
    'crate_creak': ('wooden crate creak; lid thump', 'L sfx/creaks_scrapes, impacts/wood'),
    'crate_break': ('kicking a slatted crate apart: crack and splinter', 'E "wooden crate break kick"; L impacts plank'),
    'padlock': ('padlock shackle popping open / snapping shut', 'E "padlock open"; existing lock_turn layer'),
    'gate_chain': ('chain pulled through gate bars; fence rattle; kind tape_flutter = plastic tape fluttering', 'E "chain link fence rattle chain"'),
    'gate_creak': ('metal gate swinging shut', 'E "metal gate creak"'),
    'flashlight_click': ('flashlight switch', 'E "flashlight switch click"; L sfx/clicks'),
    'phone_message': ('text message received tone + short vibrate', 'E "phone message notification"'),
    'candy_wrapper': ('cellophane twist wrapper crinkle (hand, fist, palm)', 'E "candy wrapper cellophane"'),
    'bed_creak': ('bunk bed / mattress springs: sit, scoot, pat (kind pat = soft hand pat on the mattress)', 'E "bunk bed creak mattress springs"'),
    'body_fall': ('a body hitting wooden floorboards', 'E "body fall wood floor"; L impacts soft heavy'),
    'wood_thud': ('shoulder into a bunk + bunk rattle; the wall shuddering', 'L impacts wood heavy'),
    'tape_peel': ('medical tape: picking at the edge, slipping off', 'E "tape peel"'),
    'clock_tick_backward': ('a heavy clock tick reversed (TOCK-tick), n reverse ticks', 'S from clock_tick reversed + lower pitch'),
    'coffee_percolator': ('a camp coffee percolator bubbling far away', 'E "coffee percolator"'),
    'kitchen_far': ('distant camp kitchen: clinks, a griddle hiss', 'E "kitchen ambience distant"'),
    'lantern_hum': ('battery lantern hum', 'S 120 Hz hum + filtered noise'),
    'wind_chimes': ('porch wind chimes', 'L sfx/ambience oculus windchimes'),
    'footsteps_gravel': ('footsteps on a gravel / pine-needle path (wet=True for wet grass, soft=True sneaking)', 'E "footsteps gravel"; existing footsteps engine'),
    'footsteps_run': ('someone running away on gravel and porch boards (approach=-1)', 'E "running footsteps gravel"'),
    'screen_door': ('screen door spring creak and slap', 'E "screen door"'),
    'chair_scrape': ('a kitchen chair scraping back (heard through the phone)', 'E "chair scrape"'),
    'phone_handle': ('a phone set down on / picked up from a wooden sill', 'L sfx/clicks + impacts light'),
    'lace_pull': ('a shoelace pulled through eyelets (n pulls)', 'L sfx/foley/cloth slowed'),
    'kids_far': ('memory: kids giggling under blankets / mess hall chatter, far and filtered', 'E "kids laughing distant"'),
    'voices_calling_far': ('memory: a search party calling a name in morning mist (no intelligible words)', 'E "search party calling distant"'),
    'bus_door': ('memory: school bus door hiss and idle', 'E "school bus door"'),
    'excavator_creak': ('parked excavator: cooling metal ticks', 'S metal ticks; L metals'),
    'owl': ('a far owl', 'L sfx/ambience owl'),
    'watch_beep': ('digital watch button chirp (memory)', 'S 4 kHz square chirp'),
    'window_slide': ('wooden window sash sliding down (memory)', 'L creaks_scrapes'),
    'moth_flutter': ('moths flapping at a lantern', 'S filtered flutter; E "moth flutter"'),
    'tv_through_wall': ('a TV murmur behind a window', 'S filtered voices from crowd_whisper; L'),
    'ambience_camp_night': ('camp night bed: crickets, frogs, pine wind, lake lapping, rare owl (replaces suburban ambience_night)', 'E "forest night crickets frogs lake"; L oculus forest night loop'),
    'ambience_dawn': ('the other side: a dawn chorus that repeats EXACTLY every 19.48 s (the loop), no wind', 'E "dawn birds summer"'),
    'ambience_mirror': ('inside the glass: hollow glassy room tone, faint high whine, sub pressure', 'S'),
    'ambience_memory': ('memories: bright summer morning, lake lap, gulls, far kids, tape wow and low-pass', 'E "summer camp morning ambience"'),
}
SPACES = ('close', 'inside', 'outside', 'far', 'mirror', 'memory', 'phone', 'dry')

# ---------------------------------------------------------------- sections, intensity
SECTIONS = [  # (name, t0, title)
    ('hook', 0.0, 'Cold open: the rule premise'),
    ('arrival', SL.T(7, 0.03), '11:57 PM, the camp, Tess, Mom\'s text'),
    ('porch', SL.T(19), 'The mess hall porch and the cracked bell'),
    ('cabin', SL.T(24), 'The caretaker\'s house, Cabin 7, the towel'),
    ('steps', SL.T(31), 'Seven steps, the game, the eighth step'),
    ('seven', SL.T(43), 'There are seven rules'),
    ('rule1', SL.card_times(1)[0], 'Rule 1: count the steps'),
    ('rule2', SL.card_times(2)[0], 'Rule 2: keep your wishes to yourself'),
    ('rule3', SL.card_times(3)[0], 'Rule 3: leave somebody on your side'),
    ('rule4', SL.card_times(4)[0], 'Rule 4: ask what he wished for'),
    ('rule5', SL.card_times(5)[0], 'Rule 5: ring the real bell'),
    ('rule6', SL.card_times(6)[0], 'Rule 6: let him go first'),
    ('rule7', SL.card_times(7)[0], 'Rule 7: cover anything that reflects'),
    ('ending', SL.T(268), 'Just after midnight: Hi, Mom; the phone'),
]
INTENSITY = [(0, 6), (3.9, 9), (5.4, 7), (8.1, 6), (12.7, 4), (19.2, 3.5), (30, 3), (43, 3.5), (54.3, 4), (63, 4.5), (67.5, 4.5),
             (71.4, 5), (75.8, 3.5), (88.7, 5), (100, 5.5), (117.3, 6), (118.9, 8), (121, 7), (125, 7.5), (129.8, 8.5), (133.6, 6),
             (141, 6.5), (143.3, 8), (148.2, 8), (154.2, 6), (163.6, 7), (174, 6), (180, 7), (182.8, 8), (186.3, 4.5), (196.3, 6.5),
             (198.15, 9), (203.5, 9), (208.3, 7), (211.5, 7.5), (218, 5), (229.8, 5.5), (237.7, 6.5), (245.2, 7), (248.4, 9), (252.2, 9),
             (256.9, 8), (260.4, 8), (263.9, 6), (269.2, 8.5), (273.4, 7), (279, 8), (283.8, 9.5), (287.4, 7), (289.9, 6), (290.6, 3),
             (305.7, 4.5), (315, 5.5), (320, 4), (331.7, 5), (334.9, 7), (338.7, 7), (345, 7.5), (349.9, 8.5), (350.4, 8.5), (353.5, 7.5),
             (358.4, 8.5), (366.6, 8), (367.8, 9), (371, 5), (382, 5.5), (386.6, 6), (394.5, 7), (397.1, 7.5), (398.9, 4), (411.3, 3.5),
             (414.3, 5.5), (419.5, 6.5), (424.7, 5), (433, 4), (445, 5.5), (446.3, 8), (449.7, 7.5), (462.6, 7.5), (464.5, 8), (477.9, 9),
             (481.4, 5), (488, 4.5), (499.9, 7), (502.4, 8.5), (508, 8), (511.4, 8.5), (518.2, 7), (528.8, 8), (531.5, 9), (533.7, 9.5),
             (535.4, 10), (539.2, 8), (542, 9), (545.2, 9), (551.3, 9), (557.3, 9.5), (565, 8.5), (572, 9), (576.2, 9), (585.6, 10),
             (589.6, 10), (594, 9), (596, 7.5), (602.4, 9), (605.2, 10), (607.3, 10), (609.5, 9.5), (614.7, 9), (621.8, 9), (625.5, 9.5),
             (628.2, 10), (628.9, 2.5), (641.9, 3.5), (653.7, 4), (660.9, 5), (661.4, 2), (666.8, 3.5), (673, 5), (677.4, 6.5), (685, 7),
             (689.4, 8), (690.2, 9), (696.8, 9.5), (697.2, 10), (698.62, 0), (END, 0)]

MUSIC_SECTIONS = [
    dict(id='M1', t0=0.0, t1=19.18, mood='cold glassy dread, one huge hit, then grief', key='D minor (D-A drone, Eb rub)', intensity='6 -> 9 -> 4',
         source='new Epidemic "dark drone" in D if downloaded, else in_continuum_dream_cave (D) low section', layers='sub drone, music-box bell motif (D5-F5-E5-A4), WIPE THE GLASS hit + braam',
         notes='bed dips 6 dB under the premise lines 5-6; the hit at 3.92 is one of the three loudest bed moments of the film'),
    dict(id='M2', t0=19.18, t1=54.34, mood='night, nostalgic, uneasy', key='D', intensity='3 -> 4', source='tefu_sayuri_hayashi_egnell (D), quiet sections',
         layers='low strings swell under the time card, music-box motif on the memory inserts', notes='quietest stretch; no pulse'),
    dict(id='M3', t0=54.34, t1=88.66, mood='sneaking; warm memory flickers', key='D', intensity='4 -> 5 -> 3.5', source='tefu continues; score.py music-box over the towel memories',
         layers='soft tick pulse while sneaking past the caretaker (67.5-71.4), memory pads', notes='the real cracked bell is planted at 65.92 in a memory'),
    dict(id='M4', t0=88.66, t1=129.8, mood='creeping build to the eighth step, then the rule hook', key='D', intensity='5 -> 8 -> 8.5',
         source='in_continuum_dream_cave (D) rising sections', layers='silence 117.6 -> hit 118.87, punch-in hits, a 7 s riser into the rule 1 card',
         notes='two 13 s swells: 104-117 and 121-130'),
    dict(id='M5', t0=129.8, t1=203.53, mood='discovery inside the glass; the queen\'s first turn', key='D / B', intensity='6 -> 9',
         source='a_massive_mist_ethan_sloan (B) mid sections for the old-cabin reflection; drones return for the stairs',
         layers='warm detuned pad for the too-normal reflection (154-174), silence before the voice (181.6), grief dip for the voicemail (186-196), silence + hit on the head turn (198.15)',
         notes='riser into the rule 2 card'),
    dict(id='M6', t0=203.53, t1=269.24, mood='the hand, the wish, "You have it", the doorway', key='Bb over D pedal', intensity='7 -> 9 -> 6',
         source='dark_forebodings_ethan_sloan (A#) for 211-260; drop to drones for the doorway', layers='grief dip 218-237, silence 247 -> "You have it" hit, stinger on the fingers, braam on the doorway',
         notes='do not layer the D drone under the A# track; crossfade at 210.9 and 260.4'),
    dict(id='M7', t0=269.24, t1=350.38, mood='the queen\'s face; stepping into the too-normal dawn', key='D -> warm modal', intensity='8.5 -> 9.5 -> 3 -> 8.5',
         source='drones + stinger for 269-290; then score.py: music-box + warm detuned pad + soft strings (the dawn world has no horror track)',
         layers='pulse_on at the face (283.8), pulse off at the step-through, stopped-time tinnitus on the hanging drop, swell into 45',
         notes='the dawn side must sound still and clean: no low rumble, no wind'),
    dict(id='M8', t0=350.38, t1=446.33, mood='the loop; grief; the morning he vanished', key='D minor', intensity='8.5 -> 5 -> 4 -> 5.5',
         source='tefu (D) + score.py piano and strings; memory pads for 398.9-446', layers='hit on the face flash (367.8), silence 397.3, memory swell, riser into rule 5',
         notes='the quietest bed of the film is the memory stretch (-18 LU); never fully silent'),
    dict(id='M9', t0=446.33, t1=542.03, mood='urgency, temptation, the fake bell, the real bell', key='Bb / D', intensity='8 -> 4.5 -> 10',
         source='from_hell_christoffer_moe_ditlevsen (A#) for 449-478 and 499-535; score.py only for the temptation (481-499)',
         layers='low pulse in, temptation dip to -18 LU, fake bell in a cleared space, the deepest silence (533.2-534.95), REAL BELL hit',
         notes='the fake bell must be the most beautiful sound in the film; the real bell the ugliest'),
    dict(id='M10', t0=542.03, t1=609.48, mood='climax: escape, aging, the shoe, the foot below yours', key='D', intensity='9 -> 10',
         source='from_hell peak sections, then new Epidemic "horror tension build" if downloaded', layers='climax pulse, silence 588.6 -> "Wait" hit, thin bed at 595-600 (memory), biggest hit at 605.21',
         notes='loudest minute of the bed except the very end'),
    dict(id='M11', t0=609.48, t1=628.94, mood='wipe the glass', key='D', intensity='9.5 -> 10 -> out', source='dark_tunnels_ethan_sloan (F) high section or drones',
         layers='riser into rule 7, wipes, silence while the foot hangs, sub drop when the glass goes dark, then near silence', notes=''),
    dict(id='M12', t0=628.94, t1=END, mood='relief and grief, then the phone', key='D major-ish -> D minor', intensity='2.5 -> 5 -> 10 -> 0',
         source='new Epidemic "emotional strings piano" if downloaded, else score.py strings + piano', layers='warm swell on "Hi, Mom", a true pause (661.6), final riser from 677.4, final stinger 696.9, hard out at 698.62',
         notes='after black: one faint perfect bell note'),
]

VOICE_FX = {
    68: ('below', 'Noah below the stairs: low-pass 3.5 kHz, dark short reverb 0.8 s, -2 dB'),
    97: ('queen', 'dry close + an octave-down whisper double at -18 dB + glass reverb 1.2 s'),
    110: ('queen', 'as 97'), 196: ('queen', 'as 97'),
    137: ('far', 'Tess through the doorway: low-pass 5 kHz, room 0.5 s, -3 dB'),
    206: ('far_outside', 'Tess on the porch: exterior slap, -3 dB'),
    246: ('far', 'as 137'),
    249: ('queen_child', 'Noah\'s voice from her mouth: the queen glass reverb + whisper double, no pitch change'),
    279: ('phone', 'lines.py fx=phone'),
    299: ('phone_child', 'phone band-pass 300-3400 Hz + the queen glass reverb + slight bit crush (lines.py fx=phone)'),
}

WISHLIST_SFX = [
    ('nail_click_glass, glass_tap', 'fingernail tap on glass / mirror, single'),
    ('lipstick_draw, lipstick_smear', 'marker or crayon squeak on glass; finger rubbing glass'),
    ('glass_wipe', 'cloth wiping window glass, squeaky strokes'),
    ('bell_clean, bell_cracked', 'hand bell / school bell single ring (2-3 different), brass bell hit with metal'),
    ('bell_cracked', 'spoon dropped on a table (the rattle layer)'),
    ('sprinkler_spit', 'lawn sprinkler, impact sprinkler start and stop'),
    ('water_drip, drop_reverse', 'water drips on fabric / towel, single drops'),
    ('wet_footstep, bare_foot_step', 'wet barefoot footsteps on wood; wet sneaker squelch'),
    ('towel_cloth, towel_drop', 'towel flap, cloth throw, cloth drop on floor'),
    ('candy_wrapper', 'candy wrapper cellophane crinkle'),
    ('crate_break, crate_creak', 'wooden crate break / kick apart, wood splinter'),
    ('padlock, gate_chain, gate_creak', 'padlock open, chain pulled through metal gate, chain-link fence rattle, metal gate creak'),
    ('bed_creak', 'bunk bed creak, mattress springs sit down'),
    ('body_fall, wood_thud', 'body fall on wooden floor; shoulder hit on wooden bed frame'),
    ('tape_peel', 'tape peel, medical tape'),
    ('flashlight_click', 'flashlight switch on/off'),
    ('phone_message', 'phone text message notification'),
    ('screen_door', 'screen door open and slam with spring'),
    ('chair_scrape', 'chair scrape on floor'),
    ('coffee_percolator, kitchen_far', 'coffee percolator; distant kitchen ambience'),
    ('footsteps_gravel, footsteps_run', 'footsteps on gravel path walking and running'),
    ('ambience_camp_night', 'forest night ambience with crickets and frogs near a lake (2-3 min)'),
    ('ambience_dawn', 'dawn birds / morning chorus, summer, calm (1-2 min)'),
    ('ambience_memory', 'summer camp / lake morning ambience with distant kids'),
    ('kids_far, voices_calling_far', 'kids laughing distant; people calling out searching in a forest (no clear words)'),
    ('bus_door', 'school bus door open and close'),
]
WISHLIST_MUSIC = [
    ('M1, M4, M5', 'dark ambient horror drone, unpulsed, D minor or A minor (2 tracks, 2-3 min)'),
    ('M7, M8', 'eerie innocent / nostalgic memory: music box or celesta lullaby, warm but detuned (1-2 tracks)'),
    ('M8, M12', 'sad piano with low strings, slow, D minor (grief)'),
    ('M9, M10', 'horror tension build with slow pulse and risers, climaxing (2-3 min)'),
    ('M12', 'emotional strings and piano, reunion / bittersweet, D (1 track)'),
    ('all', 'a few horror stingers, braams and risers with long tails (the new film needs ~60 hits)'),
]


# =================================================================================================== helpers
def write_json(path, obj):
    """Indented JSON with every array that holds no objects written on one line (camera keys, acts, word lists)."""
    import re
    txt = json.dumps(obj, indent=1, ensure_ascii=False)
    pat = re.compile(r'\[[^\[\]{}]*\]')
    while True:
        new = pat.sub(lambda m: re.sub(r'\s*\n\s*', ' ', m.group(0)).replace('[ ', '[').replace(' ]', ']'), txt)
        if new == txt: break
        txt = new
    txt = re.sub(r'\[\s*\n\s*(\[[^{}]*?\])\s*\n\s*\]', lambda m: '[' + m.group(1) + ']', txt)
    open(path, 'w').write(txt + '\n')


def lerp_curve(keys, x):
    for (x0, y0), (x1, y1) in zip(keys, keys[1:]):
        if x0 <= x <= x1:
            return y0 if x1 == x0 else y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return keys[-1][1]


CAM_DEF = {'push': dict(rate=0.028), 'creep': dict(rate=0.010), 'fast': dict(rate=0.06), 'pull': dict(rate=-0.03),
           'reveal': dict(rate=-0.10), 'drift': dict(rate=0.012, dx=27), 'track': dict(rate=0.005, dx=60),
           'hand': dict(rate=0.015, shake=15), 'crane': dict(rate=0.02, dy=-25), 'tilt': dict(rate=0.02), 'orbit': dict(rate=0.02, dx=30),
           'whip': dict(), 'move': dict()}


def cam_keys(c, t0, t1):
    d = t1 - t0
    mv = c['mv']
    df = CAM_DEF[mv]
    x, y, z = c.get('x', 960), c.get('y', 540), c.get('z', 1.0)
    r0 = c.get('roll0', 0.0)
    r1 = c.get('roll', r0)
    if mv in ('whip', 'move'):
        x1, y1, z1 = c['x1'], c['y1'], c['z1']
    else:
        rate = c.get('rate', df.get('rate', 0.0))
        x1 = x + c.get('dx', df.get('dx', 0.0)) * d
        y1 = y + c.get('dy', df.get('dy', 0.0)) * d
        z1 = max(1.0 if z >= 1.0 else z, z * (1 + rate * d)) if rate < 0 else z * (1 + rate * d)
    ease = {'reveal': 'out', 'whip': 'in_out', 'move': 'push'}.get(mv, 'lin')
    shake = c.get('shake', df.get('shake', 2.0))
    out = dict(move=mv, keys=[[round(t0, 3), x, y, round(z, 4), r0], [round(t1, 3), round(x1, 1), round(y1, 1), round(z1, 4), r1]],
               ease=ease, shake=shake, rate_pct_s=round((z1 / z - 1) / d * 100, 2) if d > 0 else 0.0,
               pan_px_s=round(math.hypot(x1 - x, y1 - y) / d, 1) if d > 0 else 0.0)
    if 'snap' in c:
        st, k = c['snap']
        out['snap'] = [round(st, 3), k, 0.1]
    if 'hit' in c:
        out['hit'] = [[round(a, 3), b] for a, b in c['hit']]
    return out


def clause_starts():
    """Clause starts: every line start and every word after , . ? ! ; within a line (REF cut_vs_text)."""
    out = []
    for L in LINES:
        prev = None
        for i, (wd, tt) in enumerate(L['words']):
            if tt is None: continue
            if i == 0 or (prev and prev[-1] in ',.?!;:'):
                out.append(tt)
            prev = wd
    return sorted(out)


def clock_str(sec):
    sec = int(math.floor(sec)) % 86400
    return '%02d:%02d:%02d' % (sec // 3600, (sec // 60) % 60, sec % 60)


CLOCK_T0 = t(7)                           # 19.40: 23:57:00
BACK_T0 = w(108, 'behind')                # 278.97 / the clock line: header runs backward for 2.84 s
BACK_T1 = BACK_T0 + 2.84
LOOP_T0 = w(117, 'a')                     # 297.59: the dawn loop phase (resets at every sprinkler spit pair)
LOOP_P = round((w(167, 'outside') - LOOP_T0) / 6, 3)
REAL_BELL = w(220, 'hits')


def ours_clock(tt):
    base = 23 * 3600 + 57 * 60
    if tt < BACK_T0: return base + (tt - CLOCK_T0)
    if tt < BACK_T1: return base + (BACK_T0 - CLOCK_T0) - (tt - BACK_T0)
    return base + (BACK_T0 - CLOCK_T0) - (BACK_T1 - BACK_T0) + (tt - BACK_T1)


def theirs_clock(tt):
    if tt >= REAL_BELL: return 7 * 3600
    return 6 * 3600 + 59 * 60 + 40 + ((tt - LOOP_T0) % LOOP_P)


# =================================================================================================== build
def build():
    shots = sorted(SHOTS, key=lambda s: s['t0'])
    for a, b in zip(shots, shots[1:]):
        a['t1'] = b['t0']
    shots[-1]['t1'] = END
    cards = [(s['t0'], s['t1']) for s in shots if s['side'] == 'card']
    cstarts = clause_starts()
    states = sorted(SL.STATES, key=lambda x: x[0])
    sec_t = [s[1] for s in SECTIONS]
    rule_n = 0
    prev_side = 'ours'
    out = []
    for k, s in enumerate(shots):
        t0, t1 = round(s['t0'], 3), round(s['t1'], 3)
        s = resolve(s, t0, t1)
        d = round(t1 - t0, 3)
        sid = 'S%03d' % (k + 1)
        sec = SECTIONS[max(i for i, x in enumerate(sec_t) if x <= t0 + 1e-6)][0]
        lines = [L['i'] for L in LINES if min(t1, L['end']) - max(t0, L['t']) > 0.04]
        near = min((abs(t0 - c) for c in cstarts), default=9)
        on_clause = any(-0.35 <= (t0 - c) <= 0.15 for c in cstarts)
        if s['side'] == 'card':
            rule_n = int(s['hud'][0]['n'])
        st = {}
        changes = []
        for tt, kw in states:
            if tt <= t0 + 1e-6: st.update(kw)
            elif tt < t1: changes.append([round(tt, 3), kw])
        st.pop('side', None)
        props = dict(st)
        props.update(s.get('props', {}))
        if changes: props['changes_in_shot'] = changes
        side = s['side']
        clock_side = prev_side if side == 'card' else side
        if side not in ('card', 'black'): prev_side = side
        if t0 < CLOCK_T0 - 0.3 or side == 'black':
            mode, now = 'hidden', None
        elif clock_side == 'memory':
            mode, now = 'memory', '14 YEARS AGO'
        elif clock_side == 'theirs':
            mode, now = ('stuck' if t0 >= REAL_BELL else 'theirs'), clock_str(theirs_clock(t0))
        else:
            mode, now = 'ours', clock_str(ours_clock(max(t0, CLOCK_T0)))
        left = 'CABIN 7 · CAMP CEDAR LAKE  //  ' + ('INTRODUCTION' if rule_n == 0 else 'RULE %d OF 7' % rule_n)
        cam = cam_keys(s['cam'], t0, t1)
        o = dict(id=sid, t0=t0, t1=t1, dur=d, section=sec, lines=lines, cut_on_clause=on_clause, clause_offset=round(near, 3),
                 set=s['set'], view=s['view'], var=s['var'], side=side, type=s['type'], frame=s['frame'], cam=cam,
                 lens=s.get('lens'), grade=s.get('grade') or GRADE_FOR.get((s['set'], s['var'])) or GRADE_FOR.get(s['set']),
                 dof=s.get('dof'), chars=s.get('chars', []), props=props, hud=s.get('hud', []),
                 captions=s.get('captions', side not in ('card', 'black')),
                 header=dict(left=left, clock_mode=mode, clock_at_t0=now),
                 tr=s.get('tr', 'cut'), intensity=round(lerp_curve(INTENSITY, (t0 + t1) / 2), 1), energy=s.get('energy', ''),
                 sfx=s.get('sfx', []), mus=s.get('mus', []))
        for key in ('voice_fx', 'fx_post', 'bg', 'note'):
            if key in s: o[key] = s[key]
        out.append(o)
    rehome(out)
    return out, cards


def rehome(out):
    """An SFX, music or HUD item authored on one shot but timed inside another moves to the shot that contains it (shots
    split by the short-cut pass). Pinned labels and tags stay only if at least 0.5 s of them is visible in their own shot."""
    starts = [o['t0'] for o in out]
    import bisect
    def owner(tt):
        return out[max(0, min(len(out) - 1, bisect.bisect_right(starts, tt) - 1))]
    for key in ('sfx', 'mus', 'hud'):
        moved = []
        for o in out:
            keep = []
            for item in o[key]:
                tt = item['t']
                if key == 'hud' and item['type'] in ('rule_card', 'like_sub', 'phone', 'time_card', 'counter_in', 'counter_call'):
                    keep.append(item); continue
                if o['t0'] - 0.02 <= tt < o['t1'] - 0.02:
                    if key == 'hud' and item['type'] in ('label', 'tag', 'red_x'):
                        item['hold'] = round(min(item.get('hold', 1.2), o['t1'] - tt), 2)
                    keep.append(item)
                else:
                    moved.append(item)
            o[key] = keep
        for item in moved:
            tgt = owner(item['t'])
            if key == 'hud' and item['type'] in ('label', 'red_x'):
                continue                                   # a pinned label does not survive onto a different picture
            tgt[key].append(item)
        for o in out: o[key].sort(key=lambda it: it['t'])


GRADE_FOR = {
    'camp_gate': 'camp_night', 'camp_path': 'camp_night', 'mess_porch': 'camp_night', 'caretaker': 'camp_night',
    ('mess_porch', 'run'): 'camp_night_run', ('mess_porch', 'bell_hit'): 'climax_red',
    'cabin_now': 'cabin_flash', ('cabin_now', 'doorway_glow'): 'cabin_doorway', ('cabin_now', 'red'): 'climax_red',
    ('cabin_now', 'after'): 'cabin_after', ('cabin_now', 'phone_glow'): 'cabin_after',
    'mirror': 'cabin_flash', ('mirror', 'old_cabin'): 'mirror_old_cabin', ('mirror', 'queen'): 'mirror_world', ('mirror', 'red'): 'climax_red',
    ('mirror', 'dark'): 'mirror_world', ('mirror', 'wipe'): 'cabin_flash',
    'mirror_world': 'mirror_world', ('mirror_world', 'red'): 'climax_red',
    'cabin_dawn': 'dawn_normal', ('cabin_dawn', 'dawn_queen'): 'dawn_queen', ('cabin_dawn', 'dawn_break'): 'dawn_break',
    'memory': 'memory', ('memory', 'memory_night'): 'memory_night', ('memory', 'memory_morning'): 'memory_morning',
    'ui': 'phone_dark', 'rule_mirror': 'rule_card', 'black': 'neutral',
}


FUNC = set('a an the of to in on at for with and or but if as by from that your his her my their its you he she i we they it is was are '
           'be been has had have so than then when where who what like into onto over under about'.split())


def chunk_words(words, max_w=7, max_c=34):
    """Split a line into balanced one-line captions (REF: median 5 words, p90 8, 1.5-1.7 s): as few chunks as the word and
    character limits allow, breaks pulled to punctuation and never after a function word ('on', 'a', 'the', 'your'...)."""
    n_w = len(words)
    text_len = len(' '.join(x[0] for x in words))
    n = max(1, math.ceil(n_w / max_w), math.ceil(text_len / max_c))
    if n == 1: return [words]
    breaks, prev = [], 0
    for j in range(1, n):
        target = n_w * j / n
        best, best_k = 1e9, None
        for k in range(prev + 2, n_w - 1 * (n - j) - 1 + 1):
            last = words[k - 1][0]
            sc = abs(k - target)
            if last.lower().strip('",.?!;:') in FUNC: sc += 2.5
            if last[-1] in ',.?!;:': sc -= 1.6
            if len(' '.join(x[0] for x in words[prev:k])) > max_c + 4: sc += 3
            if sc < best: best, best_k = sc, k
        if best_k is None: break
        breaks.append(best_k); prev = best_k
    out, a = [], 0
    for b in breaks + [n_w]:
        out.append(words[a:b]); a = b
    return [c for c in out if c]


def make_captions(cards):
    caps = []
    for L in LINES:
        words = [[wd, tt] for wd, tt in L['words']]
        for j in range(len(words)):                       # a word the aligner could not time inherits its neighbour's time
            if words[j][1] is None: words[j][1] = words[j - 1][1] if j else L['t']
        chunks = chunk_words(words)
        nxt = LINES[L['i'] + 1]['t'] if L['i'] + 1 < len(LINES) else END
        for ci, ch in enumerate(chunks):
            c0 = ch[0][1] - 0.08
            c1 = (chunks[ci + 1][0][1] - 0.08) if ci + 1 < len(chunks) else min(L['end'] + 0.25, nxt - 0.06)
            text = ' '.join(x[0] for x in ch)
            if L['who'] != 'N':
                if ci == 0: text = '"' + text
                if ci == len(chunks) - 1: text = text + '"'
            for a, b in cards:                            # hidden under rule cards
                if c0 < b and c1 > a:
                    if c0 >= a: c0 = b
                    else: c1 = a
            if c1 - c0 >= 0.3:
                caps.append(dict(t0=round(c0, 3), t1=round(c1, 3), text=text, line=L['i']))
    return caps


def counter_track():
    start = w(112, 'sixty')
    calls = [(start, 60), (t(137), 45), (t(206), 20), (t(246), 5), (w(258, 'collar'), 0)]
    steps = []
    for (ta, va), (tb, vb) in zip(calls, calls[1:]):
        n = va - vb
        for j in range(n):
            steps.append([round(ta + (tb - ta) * j / n, 3), va - j, 'call' if j == 0 else 'step'])
    steps.append([round(calls[-1][0], 3), 0, 'zero'])
    return dict(visible=[round(start, 3), SL.card_times(7)[0]], hidden_on=['card'], dim_on={'memory': 0.6}, steps=steps,
                look='small dark pill (navy #0b1822 at 80 %) with a thin red outline, top right under the header at (1760, 118) design px; '
                     'label TESS in 14 px letter-spaced white at 35 % above a 46 px Montserrat 800 number; each step a 0.12 s scale tick; '
                     'Tess\'s calls (60, 45, 20, 5) pop to 1.35x with a red flash and glow for 0.25 s; 0 at the collar pull flashes red',
                why='time on the two sides runs at different speeds: the count is dilated (one step every 4-6 s) and lands exactly on her calls')


def value_at(steps, tt):
    v = None
    for a, b, _ in steps:
        if a <= tt + 1e-6: v = b
    return v


def bed_ranges(shots):
    def bed(s):
        st, var, side = s['set'], s['var'], s['side']
        if side == 'black': return ()
        if side == 'card': return ('card_dip',)
        if side == 'ui': return ('inherit',)
        if st in ('camp_gate', 'camp_path', 'caretaker', 'mess_porch'):
            b = ['ambience_camp_night']
            if st == 'mess_porch': b.append('wind_chimes')
            if st == 'caretaker': b.append('tv_through_wall')
            return tuple(b)
        if st == 'cabin_now':
            b = ['room_tone', 'ambience_camp_night(muffled -10 dB, LP 2 kHz)']
            if var in ('doorway_glow', 'red'): b.append('ambience_dawn(through the doorway -14 dB)')
            return tuple(b)
        if st in ('mirror', 'mirror_world'):
            return ('ambience_mirror', 'room_tone(-6 dB)') if var != 'old_cabin' else ('ambience_mirror', 'ambience_dawn(through glass -16 dB)')
        if st == 'cabin_dawn':
            return ('ambience_dawn(loop %.2f s)' % LOOP_P, 'lantern_hum') + (('ambience_dawn detunes and stutters',) if var == 'dawn_break' else ())
        if st == 'memory': return ('ambience_memory(filtered: LP 5 kHz, tape wow)',)
        return ('room_tone',)
    out, cur = [], None
    for s in shots:
        b = bed(s)
        if b == ('inherit',) and cur: b = cur['beds']
        if cur and cur['beds'] == b:
            cur['t1'] = s['t1']
        else:
            cur = dict(t0=s['t0'], t1=s['t1'], beds=b, set=s['set'])
            out.append(cur)
    for r in out:
        r['beds'] = list(r['beds'])
        r['dur'] = round(r['t1'] - r['t0'], 2)
    return out


def derive_rises(min_gain=1.5, max_len=16.0):
    """Music swells from the intensity curve: every climb of >= min_gain points (0-10) inside max_len seconds becomes a
    'swell' event that peaks at the top of the climb (AUDIO_SPEC 3: ~2.5-2.7 rises of +12-13 LU per minute, ~13 s long)."""
    out, keys = [], INTENSITY
    i = 0
    while i < len(keys) - 1:
        j = i
        while j + 1 < len(keys) and keys[j + 1][1] >= keys[j][1]: j += 1
        if j > i:
            top_t, top_v = keys[j]
            k = i
            while k < j and top_t - keys[k][0] > max_len: k += 1
            lo_t, lo_v = keys[k]
            if top_v - lo_v >= min_gain:
                out.append(dict(t=round(top_t, 2), len=round(top_t - lo_t, 2), level=round(top_v / 10, 2), **{'from': lo_v, 'to': top_v}))
        i = max(j, i + 1)
    return out


def main():
    shots, cards = build()
    caps = make_captions(cards)
    ctr = counter_track()
    for s in shots:
        s['counter'] = None if (s['side'] in ('card', 'black') or not (ctr['visible'][0] <= s['t0'] + 0.5 < ctr['visible'][1] or
                                                                       ctr['visible'][0] <= s['t1'] - 0.05 < ctr['visible'][1])) else value_at(ctr['steps'], max(s['t0'], ctr['visible'][0]))
    rule_cards = []
    for s in shots:
        for h in s['hud']:
            if h['type'] == 'rule_card':
                li, ti = SL.RULE_LINES[h['n']]
                rule_cards.append(dict(n=h['n'], shot=s['id'], appear=s['t0'], rule_word=w(li, 'Rule'), lead=round(w(li, 'Rule') - s['t0'], 3),
                                       title_at=h['title_at'], text=h['text'], sentence_end=e(ti), cut=s['t1'], visible=round(s['t1'] - s['t0'], 2)))
    meta = dict(title=TITLE, fps=FPS, size=[2560, 1440], design=[1920, 1080], duration=END, narration_end=DUR, frames=int(round(END * FPS)),
                lead=LEAD, timeline=os.path.relpath(dsl.TIMELINE, FILM), generated_by='plan/make_plan.py from plan/shotlist.py')
    header = dict(left_format='CABIN 7 · CAMP CEDAR LAKE  //  INTRODUCTION | RULE n OF 7 (n from the latest rule card)',
                  look='cap height 1.0 % H at y = 0.052 H, white at 20 % opacity, "RULE n OF 7" at 35 %; clock right-aligned, same size',
                  clock=dict(ours='23:57:00 at %.2f s, real time; runs BACKWARD %.2f-%.2f s (glitch flicker), then forward again from there' % (CLOCK_T0, BACK_T0, BACK_T1),
                             theirs='06:59:40 + ((t - %.2f) mod %.3f): reaches :59 and snaps back to :40 with a 2-frame glitch; frozen at 07:00:00 from the real bell %.2f' % (LOOP_T0, LOOP_P, REAL_BELL),
                             memory='"14 YEARS AGO" in place of the clock', hidden='before 19.10 s and on the black tail'),
                  side_rule='the clock shows the time of the side the camera is on (shots[].header.clock_mode)')
    secs = []
    for i, (nm, a, title) in enumerate(SECTIONS):
        b = SECTIONS[i + 1][1] if i + 1 < len(SECTIONS) else END
        ss = [s for s in shots if s['section'] == nm]
        secs.append(dict(name=nm, t0=round(a, 3), t1=round(b, 3), title=title, shots=len(ss),
                         intensity=[round(min(s['intensity'] for s in ss), 1), round(max(s['intensity'] for s in ss), 1)]))
    doc = dict(meta=meta, sections=secs, rule_cards=rule_cards, header=header, counter=ctr, captions=caps, shots=shots)
    write_json(os.path.join(HERE, 'shots.json'), doc)

    # ------------------------------------------------------------------ sound plan
    cues = []
    for s in shots:
        for c in s['sfx']:
            c = dict(c)
            c['shot'] = s['id']
            c['exists'] = c['name'] in EXISTING
            cues.append(c)
    for a, v, kind in ctr['steps']:
        if kind == 'step':
            cues.append(dict(t=a, name='countdown_tick', gain_db=-20, space='dry', note='counter step %d (tiny)' % v, exists=True, shot=None))
    cues.sort(key=lambda c: c['t'])
    for c in cues:
        if c['shot'] is None:
            c['shot'] = next(s['id'] for s in shots if s['t0'] <= c['t'] < s['t1'])
    events = []
    for s in shots:
        for m in s['mus']:
            m = dict(m); m['shot'] = s['id']; events.append(m)
    events.sort(key=lambda m: m['t'])
    names_used = sorted({c['name'] for c in cues})
    unknown = [n for n in names_used if n not in EXISTING and n not in NEW]
    if unknown: raise SystemExit('SFX names not declared: %s' % unknown)
    beds = bed_ranges(shots)
    for b in beds:
        for nm in b['beds']:
            base = nm.split('(')[0].split(' ')[0]
            if base not in EXISTING and base not in NEW and base not in ('card_dip', 'inherit'):
                raise SystemExit('bed name not declared: %s' % base)
    mins = END / 60
    hits = [c for c in cues if c.get('hit')]
    silences = [m for m in events if m['type'] == 'silence']
    hit_events = []
    for c in sorted(hits, key=lambda c: c['t']):          # layered hit cues within 0.15 s are one hit event
        if not hit_events or c['t'] - hit_events[-1] > 0.15: hit_events.append(c['t'])
    rises = derive_rises()
    events.extend(dict(t=r['t'], type='swell', level=r['level'], len=r['len'], note='auto: intensity rise %.1f -> %.1f' % (r['from'], r['to']), shot=None) for r in rises)
    # the bed breathes: fill every gap of more than 30 s between swell / riser peaks with a 13 s swell that peaks on the
    # strongest hit event in the gap (AUDIO_SPEC 3 and REF 7: ~2.7 rises of +12-13 LU per minute, ~13 s long)
    while True:
        peaks = sorted([m['t'] for m in events if m['type'] in ('swell', 'riser')] + [0.0, END - 2])
        gap = next(((a, b) for a, b in zip(peaks, peaks[1:]) if b - a > 30), None)
        if not gap: break
        a, b = gap
        cand = [x for x in hit_events if a + 13 <= x <= b - 6]
        tt = max(cand, key=lambda x: lerp_curve(INTENSITY, x)) if cand else round((a + b) / 2, 2)
        events.append(dict(t=round(tt, 2), type='swell', level=round(lerp_curve(INTENSITY, tt) / 10, 2), len=13.0,
                           note='breathing swell (+12 LU over 13 s) peaking on %s' % ('a hit' if cand else 'mid-gap'), shot=None))
        rises.append(dict(t=tt, len=13.0))
    events.sort(key=lambda m: m['t'])
    for m in events:
        if m.get('shot') is None: m['shot'] = next((s['id'] for s in shots if s['t0'] <= m['t'] < s['t1']), shots[-1]['id'])
    stats = dict(cues=len(cues), per_min=round(len(cues) / mins, 1), hit_cues=len(hits), hits=len(hit_events), hits_per_min=round(len(hit_events) / mins, 1),
                 rises=len(rises), rises_per_min=round(len(rises) / mins, 2), rise_len_median=round(statistics.median(r['len'] for r in rises), 1),
                 one_shots_per_min=round(len([c for c in cues if c['name'] not in ('ambience_camp_night', 'ambience_dawn', 'ambience_memory', 'ambience_mirror', 'room_tone')]) / mins, 1),
                 silences=len(silences), silences_per_min=round(len(silences) / mins, 2),
                 silence_len_median=round(statistics.median(m['len'] for m in silences), 2) if silences else 0,
                 risers=len([m for m in events if m['type'] == 'riser']), names_used=len(names_used),
                 new_names_used=len([n for n in names_used if n not in EXISTING]))
    sp = dict(meta=dict(title=TITLE, duration=END, generated_by='plan/make_plan.py',
                        sources=dict(epidemic_new='film/_work/samples/epidemic/{sfx,music} (owner downloads; use FIRST when present)',
                                     epidemic_police='Police Officer Video/v2/_work/pov2/samples/epidemic (74 SFX, 6 music)',
                                     free='audio/catalog.json')),
              rules=['every one-shot lands on its picture time; hits within -0.05..+0.10 s of the frame; the bed dips 15 dB in the 0.3 s before each hit',
                     'loop_id cues (sprinkler A/B, drip) must use the identical rendered sample each time (the time loop is heard)',
                     'nail_click_glass at 143.29 and 690.19 is the same sample',
                     'perspective: close (dry, near), inside (cabin room), outside (night exterior), far (distance + low-pass), mirror (heard through glass: '
                     'low-pass 4 kHz, hollow comb, -4 dB), memory (low-pass 5 kHz, light tape wow, wide reverb), phone (band-pass), dry (design layers)',
                     'music the whole time (>= 97 %), bed -11.5 LU under the voice, LRA 17, 85 % of bed energy below 250 Hz, unpulsed minor drone with a flat-2 rub',
                     'a riser of +13 LU over 5 s peaks at voice level ON each rule card, then decays over 4-5 s'],
              names=dict(existing=[n for n in EXISTING], used_existing=[n for n in names_used if n in EXISTING],
                         new={n: dict(desc=NEW[n][0], build=NEW[n][1]) for n in sorted(NEW)}),
              sfx=cues, beds=beds,
              music=dict(sections=MUSIC_SECTIONS, intensity=[[round(a, 2), round(b / 10, 2)] for a, b in INTENSITY], events=events),
              voice_fx={str(k): dict(fx=v[0], how=v[1], line=LINES[k]['en']) for k, v in VOICE_FX.items()},
              epidemic_wishlist=dict(note='The owner offered to download Epidemic files for this film into film/_work/samples/epidemic/{sfx,music}. '
                                          'These are the searches that would lift the sound most; everything has a fallback (free library or synthesis).',
                                     sfx=[dict(names=a, search=b) for a, b in WISHLIST_SFX], music=[dict(sections=a, search=b) for a, b in WISHLIST_MUSIC]),
              stats=stats)
    write_json(os.path.join(HERE, 'sound_plan.json'), sp)
    print('shots %d, captions %d, sfx cues %d (%d hits), music events %d, beds %d' % (len(shots), len(caps), len(cues), len(hits), len(events), len(beds)))


if __name__ == '__main__':
    main()
