"""plan/make_plan.py (v2): resolve plan/shotlist.py into plan/shots.json and plan/sound_plan.json.

    python3 plan/make_plan.py            # writes both JSON files, then run plan/validate.py

PLAN_V2.md documents every field. In short:

shots.json
    meta: title, fps, size, duration, lead, version 2, sources
    shots[]: the v1 fields (id, t0, t1, dur, section, lines, cut_on_clause, clause_offset, set, view, var, side, type, frame,
             cam, lens, grade, dof, chars, props, hud, captions, header, counter, tr, intensity, energy, sfx, mus, voice_fx,
             fx_post, bg) plus the v2 fields world, look, cls, chip, glint, queen, hold, reuse, setup, setup_reused, errfix,
             device, teaser, split, plate, montage, loop, card, time_card, v1 (a fallback {set, view, var, grade} that the v1
             sets.py can render today)
    captions[]: t0, t1, text, line, on_cut (2-5 word phrases, re-chunked on the cuts)
    header, counter (the ring badge), rule_cards[], sections[], holds[], queen_ladder[], devices[], errors{} (1-33 -> ids)
sound_plan.json
    the v1 cues re-homed onto the v2 shots (dropped / moved where the picture changed, see SFX_DROP / SFX_MOVE), the v2
    shot cues, and the automatic device cues (card choreography, giant numbers, stamps, highlighter, chalk diagrams, count
    pops, ring ticks, flash and glitch cuts, side-switch glints, loop rewinds, pixel-sort); names, beds, the unchanged music
    sections / intensity / events (re-homed), voice FX, wishlist, stats.
"""
import bisect, json, math, os, re, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dsl
from dsl import SHOTS, LINES, DUR, LEAD, resolve, t, e, w
import shotlist as SL

FILM = dsl.FILM
END = 700.0                    # narration ends 698.58; 1.4 s of black tail with the end card and the bell (42,000 frames)
FPS = 60
TITLE = 'If The Queen Of Spades Appears In Your Mirror... DON\'T MAKE A WISH'
V1_SOUND = os.path.join(HERE, 'v1', 'sound_plan_v1.json')

# ---------------------------------------------------------------- the v1 sound tables, unchanged (names, music map, intensity)
EXISTING = ['knock_door', 'doorbell_chime', 'footsteps_porch', 'footsteps_wood_inside', 'car_pass', 'car_idle', 'car_door_open',
            'car_door_close', 'siren_far', 'police_radio_squelch', 'radio_click', 'radio_static', 'bodycam_beep', 'phone_ring',
            'phone_busy', 'phone_vibrate', 'phone_pickup', 'mail_slot', 'paper', 'pen_click', 'key_in_lock', 'lock_turn',
            'chain_lock', 'door_creak', 'breath', 'heartbeat', 'whoosh', 'riser', 'braam', 'impact_hit', 'sub_drop', 'stinger',
            'glitch', 'ui_pop', 'typing', 'tinnitus', 'ambience_night', 'room_tone', 'clock_tick', 'countdown_tick', 'tv_off',
            'crowd_whisper']

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



# ---------------------------------------------------------------- new SFX names for the v2 picture devices (DIRECTION_V2 7, rank 6)
# name: (description, how to build it: Epidemic first, then library / synthesis), fallback = an existing name + params to use
# until the sound pass builds the new one
NEW_V2 = {
    'towel_whip': ('the orange-striped towel whipped up off the rule card (cloth whip, 0.3 s)', 'E "cloth whip / towel snap"; L sfx/foley/cloth', ('towel_cloth', dict(kind='snatch'))),
    'glass_thud': ('the mirror card settling: a small glass-and-wood thud', 'E "glass pane set down"; S modal glass + wood knock', ('mirror_handle', dict(kind='bump'))),
    'lipstick_stamp': ('the rule numeral stamping into the glass in lipstick: soft waxy impact with crumbs (+3-5 LU over its surround)', 'E "stamp soft impact"; S waxy thump + crumb ticks', ('lipstick_draw', dict(strokes=1))),
    'number_thump': ('a giant number / type beat slamming in: low punchy thump with a short ring tail', 'E "ui impact low"; S sub thump + ring', ('impact_hit', dict(size=0.6))),
    'highlighter_squeak': ('a highlighter swiped across paper', 'E "marker on paper squeak"', ('paper', {})),
    'rubber_stamp': ('a rubber stamp slammed on paper (14 YEARS, CANCELED)', 'E "rubber stamp"', ('impact_hit', dict(size=0.4))),
    'chalk_draw': ('chalk lines drawn on glass for the diagrams (soft scratch)', 'E "chalk on board"; S band-passed friction', ('lipstick_draw', dict(clean=True))),
    'glint_whoosh': ('the 3-frame glass glint on a side switch: a tiny bright glass whoosh', 'E "glass shimmer whoosh short"; S filtered noise + modal ring', ('whoosh', dict(kind='soft'))),
    'tape_rewind': ('the loop reset: a 0.2 s tape rewind scrub', 'E "tape rewind short"; S pitch-swept noise', ('drop_reverse', {})),
    'pixel_glitch': ('the pixel-sort glitch (589.6, 697.95): digital crunch', 'E "digital glitch"; existing glitch layer', ('glitch', dict(dur=0.3, amount=0.9))),
    'diagram_pop': ('a diagram element or count numeral popping in (tiny chalk tick / pop)', 'S soft click + chalk tick', ('ui_pop', {})),
    'ring_tick': ('Tess\'s ring-timer badge ticking one step (kind call: the bigger tick when she calls a number)', 'S tiny wood tick; existing countdown_tick layer', ('countdown_tick', {})),
    'flash_hit': ('a white flash cut: short bright air hit (no low end)', 'E "camera flash whoosh short"; S noise burst', ('whoosh', dict(kind='hard'))),
}
NEW_V2_NAMES = set(NEW_V2)

# ---------------------------------------------------------------- the v1 cues that the v2 picture no longer has, or moved
# (v1 time, name) -> drop | new time. Cues of the old counter and the old rule cards are regenerated (see device_cues).
SFX_DROP = [(5.60, 'ui_pop'), (7.52, 'stinger'), (10.67, 'ui_pop'), (125.48, 'lace_pull'), (287.27, 'ui_pop'), (461.10, 'ui_pop'),
            (530.87, 'stinger'), (603.25, 'stinger')]
SFX_MOVE = {(25.14, 'excavator_creak'): 27.30, (34.24, 'ambience_memory'): 36.65, (39.19, 'footsteps_gravel'): 40.40,
            (49.21, 'candy_wrapper'): 51.10, (122.87, 'impact_hit'): 122.87, (212.54, 'stinger'): 213.10, (218.15, 'paper'): 221.30,
            (221.42, 'car_door_close'): 220.40, (308.27, 'ui_pop'): 307.90, (362.99, 'ui_pop'): 362.80, (466.12, 'cloth_press'): 466.20,
            (466.52, 'bed_creak'): 467.30, (532.39, 'whoosh'): 531.90, (540.40, 'glitch'): 538.70, (615.13, 'body_fall'): 614.90,
            (619.37, 'ui_pop'): 619.40, (685.79, 'glass_resonance'): 685.31}
SFX_NOTE = {(383.77, 'bed_creak'): 'the bunk creaks under her: she has been sitting there all along',
            (3.85, 'whoosh'): 'kinetic title whoosh in (WIPE THE GLASS)'}
V1_CARD_NOTES = ('card in:', 'card lands:', 'title RULE N', 'statement written on', 'finger-wipe exit')

# ---------------------------------------------------------------- sections (same names as v1; starts on the v2 cuts)
SECTIONS = [  # (name, t0, title)
    ('hook', 0.0, 'Cold open: the premise, the flash-forwards'),
    ('arrival', dsl.T(7), '11:57 PM, the camp, Tess, Mom\'s text'),
    ('porch', dsl.T(19), 'The mess hall porch and the cracked bell'),
    ('cabin', dsl.T(24), 'The caretaker\'s house, Cabin 7, the towel'),
    ('steps', dsl.T(31), 'Seven steps, the game, the eighth step'),
    ('seven', dsl.T(43), 'There are seven rules'),
    ('rule1', SL.card_times(1)[0], 'Rule 1: count the steps'),
    ('rule2', SL.card_times(2)[0], 'Rule 2: keep your wishes to yourself'),
    ('rule3', SL.card_times(3)[0], 'Rule 3: leave somebody on your side'),
    ('rule4', SL.card_times(4)[0], 'Rule 4: ask what he wished for'),
    ('rule5', SL.card_times(5)[0], 'Rule 5: ring the real bell'),
    ('rule6', SL.card_times(6)[0], 'Rule 6: let him go first'),
    ('rule7', SL.card_times(7)[0], 'Rule 7: cover anything that reflects'),
    ('ending', dsl.T(268), 'Just after midnight: Hi, Mom; the phone'),
]
HOLDS = {  # DIRECTION_V2 2.2: id -> (t0, t1, length, what changes)
    'H1': (283.5, 286.1, 2.6, 'she leans into the light; the drawn smile; the lips talk'),
    'H2': (464.7, 468.4, 3.7, 'she sits; the mattress dips'),
    'H3': (478.0, 481.1, 3.1, 'the drawing splits into teeth on "back"'),
    'H4': (531.6, 534.7, 3.1, 'the full face turns to the lens, then the smile goes off'),
    'H5': (562.5, 565.2, 2.7, 'the age morph'),
    'H6': (589.5, 591.6, 2.1, 'the jaw drops into the void, with Noah\'s face inside'),
    'H7': (604.6, 607.4, 2.8, 'the POV tilt from your boots to her foot to her face'),
    'H8': (622.0, 625.6, 3.6, 'she lifts her foot toward an erased step'),
    'H9': (661.6, 665.0, 3.4, 'the long pause on "Hi, Mom"'),
    'H10': (692.0, 695.7, 3.7, 'her tiny figure on the phone\'s 8th line, climbing one step'),
}
ERRORS = {  # DIRECTION_V2 6: n -> the v1 error (short)
    1: 'she never sits', 2: 'Noah and the Queen vanish from the 488 wide', 3: 'open palm for "in your fist"', 4: 'a mark but no candy',
    5: 'the tape vanishes, then is back on', 6: 'no shoulder hit', 7: 'a waist grab, no yank', 8: 'no bell on screen; the X on a window',
    9: 'the real bell is never struck', 10: 'the beam stays after Tess leaves', 11: 'no opening in frame for the shove',
    12: 'whose voice and face at 589', 13: 'no keys', 14: 'the tape design changes', 15: 'no 8th line on the phone',
    16: 'the phone jumps from hand to floor', 17: 'fist, open, fist, open', 18: 'already grown, no morph',
    19: 'the face turns into a paper card', 20: 'her mouth frozen while she talks', 21: 'Noah too big, then standing',
    22: 'a white half-disc glitch at 255', 23: 'the clipped text bubble', 24: 'the finger hides the watch digits',
    25: 'the phone steps appear late', 26: 'the face in the wrong world at 283.5', 27: 'the dawn cabin behind you on the stairs',
    28: '"Instead" has no picture', 29: 'grown Noah\'s yellow eyes', 30: '"Breakfast was canceled" over a bare wall',
    31: 'the other side\'s doorway at floor level, no stairs', 32: 'the padlock never planted', 33: 'the mirror never reads as a mirror',
}

# ---------------------------------------------------------------- looks, grades, chips, classes
CLS = {'EWS': 'wide', 'WS': 'wide', 'SEC': 'wide', 'MS': 'mid', 'OTS': 'mid', '2S': 'mid', 'MCU': 'face', 'CU': 'face', 'ECU': 'face',
       'INSERT': 'insert', 'DOC': 'insert', 'DIAGRAM': 'insert', 'SPLIT': 'insert', 'UI': 'insert', 'TYPE': 'insert', 'MONTAGE': 'insert',
       'POV': 'pov', 'CARD': 'card', 'BLACK': 'black'}
LOOK = {'ours': 'night_v2', 'stairs': 'stairs_v2', 'theirs': 'dawn_v2', 'theirs_break': 'dawn_v2', 'memory': 'memory_sepia',
        'climax': 'climax_v2', 'ending': 'ending_v2', 'ui': 'phone_dark', 'card': 'rule_card', 'black': 'neutral'}
VAR_LOOK = {'dawn_queen': 'dawn_queen_v2', 'dawn_break': 'dawn_break_v2', 'bell_hit': 'climax_v2', 'red': 'climax_v2',
            'doorway_glow': 'night_v2', 'after': 'ending_v2', 'phone_glow': 'ending_v2'}
# side-switch family by where the camera physically is (DIRECTION_V2 1.2): in Cabin 7 / the camp (looking into the glass counts as
# ours) or in the other side's cabin; the stairs, memories, UI, cards and type are neutral and do not reset the side
OURS_SETS = ('cabin_now', 'mirror', 'camp_gate', 'camp_path', 'mess_porch', 'caretaker')


def family(o):
    if o['set'] in OURS_SETS: return 'ours'
    if o['set'] == 'cabin_dawn': return 'theirs'
    if o['set'] == 'split' or o['set'] == 'type': return None
    return None

# v2 view -> the v1 view sets.py can render today (fallback for previews until the new views land)
V1_VIEW = {
    ('cabin_now', 'master'): ('cabin_now', 'wide'), ('cabin_now', 'reverse'): ('cabin_now', 'wide'), ('cabin_now', 'profile'): ('cabin_now', 'mirror_ots'),
    ('cabin_now', 'overhead'): ('cabin_now', 'floor_end'), ('cabin_now', 'ots_mirror'): ('cabin_now', 'mirror_ots'), ('cabin_now', 'three_q'): ('cabin_now', 'two_shot'),
    ('cabin_now', 'bokeh'): ('cabin_now', 'two_shot'), ('cabin_now', 'door'): ('cabin_now', 'cabin_door'), ('cabin_now', 'cubby'): ('cabin_now', 'wide'),
    ('cabin_now', 'floor_cu'): ('cabin_now', 'floor_low'), ('cabin_now', 'doorway_down'): ('cabin_now', 'doorway'), ('cabin_now', 'floor_wide'): ('cabin_now', 'floor_end'),
    ('cabin_now', 'dutch_low'): ('cabin_now', 'wide'), ('cabin_now', 'bunk_rail'): ('cabin_now', 'bunk_hit'), ('cabin_now', 'window_out'): ('cabin_now', 'wide'),
    ('mirror', 'glass_cu'): ('mirror', 'mirror_cu'), ('mirror', 'glass_wide'): ('cabin_now', 'mirror_ots'), ('mirror', 'glass_tilt'): ('mirror', 'queen_step_tilt'),
    ('mirror', 'through'): ('mirror', 'old_cabin_refl'), ('mirror', 'queen_glass'): ('mirror', 'queen_step_tilt'), ('mirror', 'towel_over'): ('cabin_now', 'towel_over'),
    ('mirror', 'reflection'): ('cabin_now', 'mirror_ots'),
    ('stairs', 'down'): ('mirror_world', 'stairs'), ('stairs', 'up'): ('cabin_dawn', 'doorway_back'), ('stairs', 'section'): ('mirror_world', 'stairs'),
    ('stairs', 'treads'): ('mirror_world', 'feet'), ('stairs', 'ots_climb'): ('mirror_world', 'stairs'), ('stairs', 'pov_down'): ('mirror_world', 'feet'),
    ('stairs', 'low'): ('mirror_world', 'stairs'), ('stairs', 'railing'): ('mirror_world', 'railing'), ('stairs', 'queen_ecu'): ('mirror_world', 'eye'),
    ('stairs', 'bokeh'): ('mirror_world', 'stairs'),
    ('cabin_dawn', 'master'): ('cabin_dawn', 'wide'), ('cabin_dawn', 'reverse'): ('cabin_dawn', 'doorway_back'), ('cabin_dawn', 'towel_floor'): ('cabin_dawn', 'towel'),
    ('cabin_dawn', 'bunk_2s'): ('cabin_dawn', 'noah_ms'), ('cabin_dawn', 'queen_3s'): ('cabin_dawn', 'queen_bunk'), ('cabin_dawn', 'top_stairs'): ('cabin_dawn', 'wide'),
    ('cabin_dawn', 'ots_noah'): ('cabin_dawn', 'noah_cu'), ('cabin_dawn', 'dip_low'): ('cabin_dawn', 'mattress_dip'), ('cabin_dawn', 'door_wash'): ('cabin_dawn', 'wide'),
    ('cabin_dawn', 'floor_prints'): ('mirror', 'old_cabin_floor'), ('cabin_dawn', 'overhead'): ('mirror', 'old_cabin_floor'), ('cabin_dawn', 'lantern'): ('cabin_dawn', 'window'),
    ('cabin_dawn', 'knot'): ('cabin_dawn', 'knot_cu'), ('cabin_dawn', 'bokeh'): ('cabin_dawn', 'noah_cu'), ('cabin_dawn', 'far_porch'): ('cabin_dawn', 'window_out'),
    ('cabin_dawn', 'swimsuits'): ('cabin_dawn', 'wide'), ('cabin_dawn', 'hands'): ('cabin_dawn', 'candy'),
    ('camp_gate', 'aerial'): ('camp_path', 'aerial'), ('camp_gate', 'poster_ecu'): ('camp_gate', 'poster'), ('camp_gate', 'fence_track'): ('camp_path', 'path_track'),
    ('camp_gate', 'bokeh'): ('camp_gate', 'wide'), ('camp_gate', 'gate_reverse'): ('camp_gate', 'wide'),
    ('camp_path', 'cabin7_door'): ('camp_path', 'cabins_row'), ('camp_path', 'path_run'): ('camp_path', 'path_track'), ('camp_path', 'bokeh'): ('camp_path', 'path'),
    ('mess_porch', 'high_wide'): ('mess_porch', 'wide'), ('mess_porch', 'slats'): ('mess_porch', 'bell_slats'), ('mess_porch', 'porch_crate'): ('mess_porch', 'porch_run'),
    ('mess_porch', 'boot'): ('mess_porch', 'boot_ecu'), ('mess_porch', 'bell_hit'): ('mess_porch', 'bell_ecu'), ('mess_porch', 'bokeh'): ('mess_porch', 'porch_run'),
}
V1_MEMORY = {'porch_drop': 'porch_steps', 'bunk_morning': 'cabin_morning', 'lantern_game': 'lipstick_game', 'kids_mouths': 'kids_game',
             'office_phone': 'kitchen', 'tape_wrap': 'polaroid', 'car_door': 'polaroid', 'kitchen_15': 'kitchen', 'car_20': 'kitchen',
             'percolator': 'kitchen', 'open_window': 'night_window', 'dad_photo': 'polaroid', 'red_candy': 'pocket', 'wake': 'cabin_morning',
             'towel_wet': 'cabin_morning', 'search_window': 'search_pines', 'legs': 'porch_steps', 'officer': 'porch_steps', 'director': 'kitchen_staff',
             'menu_board': 'kitchen', 'bus_window': 'buses', 'crate_bell': 'storage_shed', 'flash_445': 'lipstick_game', 'bus_run': 'path_run',
             'run_barefoot': 'path_run', 'spoon': 'breakfast_table', 'socks': 'cabin_morning', 'moms_car': 'gate_close'}
V1_VAR = {'night': None, 'stairs': 'void', 'sepia_day': 'memory_day', 'sepia_night': 'memory_night', 'sepia_morning': 'memory_morning'}
V1_GRADE = {
    'camp_gate': 'camp_night', 'camp_path': 'camp_night', 'mess_porch': 'camp_night', 'caretaker': 'camp_night',
    ('mess_porch', 'run'): 'camp_night_run', ('mess_porch', 'bell_hit'): 'climax_red',
    'cabin_now': 'cabin_flash', ('cabin_now', 'doorway_glow'): 'cabin_doorway', ('cabin_now', 'red'): 'climax_red',
    ('cabin_now', 'after'): 'cabin_after', ('cabin_now', 'phone_glow'): 'cabin_after',
    'mirror': 'cabin_flash', ('mirror', 'old_cabin'): 'mirror_old_cabin', ('mirror', 'void'): 'mirror_world', ('mirror', 'red'): 'climax_red',
    'mirror_world': 'mirror_world', ('mirror_world', 'red'): 'climax_red',
    'cabin_dawn': 'dawn_normal', ('cabin_dawn', 'dawn_queen'): 'dawn_queen', ('cabin_dawn', 'dawn_break'): 'dawn_break',
    'memory': 'memory', ('memory', 'memory_night'): 'memory_night', ('memory', 'memory_morning'): 'memory_morning',
    'ui': 'phone_dark', 'rule_mirror': 'rule_card', 'black': 'neutral',
}


def v1_fallback(s):
    st, vw, var = s['set'], s['view'], s['var']
    src = s.get('plate') or ((s.get('split') or {}).get('panels') or [None])[0]
    if st in ('type', 'diagram', 'split') and src:
        st, vw, var = src['set'], src['view'], src['var']
    elif st in ('type', 'diagram', 'split'):
        st, vw, var = 'mirror', 'glass_cu', 'night'
    if st == 'memory':
        s1, v1 = 'memory', V1_MEMORY.get(vw, vw)
    else:
        s1, v1 = V1_VIEW.get((st, vw), (st, vw))
    var1 = V1_VAR.get(var, var)
    if var1 is None:
        var1 = 'moon_flash' if s1 in ('camp_gate', 'camp_path', 'mess_porch', 'caretaker') else 'flash'
    if s1 == 'mirror_world' and var1 not in ('void', 'void_noah', 'red'): var1 = 'void'
    if s1 == 'cabin_dawn' and var1 not in ('dawn', 'dawn_queen', 'dawn_break'): var1 = 'dawn'
    g = V1_GRADE.get((s1, var1)) or V1_GRADE.get(s1, 'neutral')
    return dict(set=s1, view=v1, var=var1, grade=g)


# =================================================================================================== helpers
def write_json(path, obj):
    """Indented JSON with every array that holds no objects written on one line (camera keys, acts, word lists)."""
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


CAM_DEF = {'push': dict(rate=0.03), 'creep': dict(rate=0.015), 'fast': dict(rate=0.06), 'pull': dict(rate=-0.03),
           'reveal': dict(rate=-0.08), 'drift': dict(rate=0.02, dx=30), 'track': dict(rate=0.01, dx=70),
           'hand': dict(rate=0.025, shake=18), 'crane': dict(rate=0.025, dy=-25), 'tilt': dict(rate=0.02, dy=-90),
           'orbit': dict(rate=0.02, dx=30), 'whip': dict(), 'move': dict()}


def cam_keys(c, t0, t1):
    d = t1 - t0
    mv = c['mv']
    df = CAM_DEF[mv]
    x, y, z = c.get('x', 960), c.get('y', 540), c.get('z', 1.0)
    r0 = c.get('roll0', c.get('roll', 0.0))            # roll alone = a constant dutch angle (climax only)
    r1 = c.get('roll', r0)
    if mv in ('whip', 'move'):
        x1, y1, z1 = c['x1'], c['y1'], c['z1']
    else:
        rate = c.get('rate', df.get('rate', 0.0))
        x1 = x + c.get('dx', df.get('dx', 0.0)) * d
        y1 = y + c.get('dy', df.get('dy', 0.0)) * (d if mv != 'tilt' else 1.0)
        if rate < 0:                                   # pull-outs start tight so they never open wider than the frame
            z = max(z, 1.0 * (1 - rate * d) + 0.02)
            z1 = z * (1 + rate * d)
        else:
            z1 = z * (1 + rate * d)
    ease = {'reveal': 'out', 'whip': 'in_out', 'move': 'push', 'tilt': 'in_out'}.get(mv, 'lin')
    shake = c.get('shake', df.get('shake', 2.0))
    out = dict(move=mv, keys=[[round(t0, 3), x, y, round(z, 4), r0], [round(t1, 3), round(x1, 1), round(y1, 1), round(z1, 4), r1]],
               ease=ease, shake=shake, rate_pct_s=round((z1 / z - 1) / d * 100, 2) if d > 0 else 0.0,
               pan_px_s=round(math.hypot(x1 - x, y1 - y) / d, 1) if d > 0 else 0.0)
    if c.get('silence'): out['silence'] = True
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


def ampm(sec):
    sec = int(math.floor(sec)) % 86400
    h, m = sec // 3600, (sec // 60) % 60
    return '%d:%02d %s' % ((h % 12) or 12, m, 'AM' if h < 12 else 'PM')


CLOCK_T0 = t(7)                           # 19.40: 23:57:00
BACK_T0 = w(108, 'behind')                # 278.97: the cabin clock runs backward for 2.84 s
BACK_T1 = BACK_T0 + 2.84
LOOP_T0 = w(117, 'a')                     # 297.59: the dawn loop phase (audio/cues.py DAWN_PHASE0)
LOOP_P = round((w(167, 'outside') - LOOP_T0) / 6, 3)
REAL_BELL = w(220, 'hits')
SEVEN_AM = 538.70                         # D9: the other side's clock passes 7:00:00


def ours_clock(tt):
    base = 23 * 3600 + 57 * 60
    if tt < BACK_T0: return base + (tt - CLOCK_T0)
    if tt < BACK_T1: return base + (BACK_T0 - CLOCK_T0) - (tt - BACK_T0)
    return base + (BACK_T0 - CLOCK_T0) - (BACK_T1 - BACK_T0) + (tt - BACK_T1)


def theirs_clock(tt):
    if tt >= SEVEN_AM: return 7 * 3600
    return 6 * 3600 + 59 * 60 + 40 + ((tt - LOOP_T0) % LOOP_P)


def chip_for(world, side, t0):
    """The place/time chip of a shot's world (DIRECTION_V2 1.2): text and style."""
    if world in ('ours', 'ending') or (world == 'climax' and side in ('ours', 'mirror')):
        return dict(text='CABIN 7 · ' + ampm(ours_clock(max(t0, CLOCK_T0))), style='ours')
    if world in ('theirs', 'theirs_break') or (world == 'climax' and side == 'theirs'):
        return dict(text='THE OTHER SIDE · ' + ('7:00 AM' if t0 >= SEVEN_AM else '6:59 AM'), style='theirs')
    if world == 'memory':
        return dict(text='14 YEARS AGO', style='memory')
    return None                                                     # stairs, ui, card, black: no chip


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
        near = min(((t0 - c) for c in cstarts), key=abs, default=9)
        on_clause = any(-0.35 <= (t0 - c) <= 0.15 for c in cstarts)
        if s['side'] == 'card':
            rule_n = int(s['hud'][0]['n'])
        st, changes = {}, []
        for tt, kw in states:
            if tt <= t0 + 1e-6: st.update(kw)
            elif tt < t1: changes.append([round(tt, 3), kw])
        props = dict(st)
        props.update(s.get('props', {}))
        if changes: props['changes_in_shot'] = changes
        side = s['side']
        clock_side = prev_side if side in ('card', 'stairs') else side
        if side not in ('card', 'black', 'ui'): prev_side = side if side != 'stairs' else prev_side
        if t0 < CLOCK_T0 - 0.3 or side == 'black':
            mode, now = 'hidden', None
        elif clock_side == 'memory':
            mode, now = 'memory', '14 YEARS AGO'
        elif clock_side == 'theirs':
            mode, now = ('stuck' if t0 >= SEVEN_AM else 'theirs'), clock_str(theirs_clock(t0))
        else:
            mode, now = 'ours', clock_str(ours_clock(max(t0, CLOCK_T0)))
        left = 'CABIN 7 · CAMP CEDAR LAKE  //  ' + ('INTRODUCTION' if rule_n == 0 else 'RULE %d OF 7' % rule_n)
        cam = cam_keys(s['cam'], t0, t1)
        world = s['world']
        look = VAR_LOOK.get(s['var']) if world not in ('memory', 'ui', 'card', 'black') else None
        look = look or LOOK[world]
        if world == 'card': look = 'rule_card'
        o = dict(id=sid, t0=t0, t1=t1, dur=d, section=sec, lines=lines, cut_on_clause=on_clause, clause_offset=round(near, 3),
                 set=s['set'], view=s['view'], var=s['var'], side=side, world=world, look=look, type=s['type'], cls=CLS[s['type']],
                 frame=s['frame'], cam=cam, lens=s.get('lens'), grade=s.get('grade') or look, dof=s.get('dof'),
                 chars=s.get('chars', []), props=props, hud=s.get('hud', []),
                 captions=s.get('captions', side not in ('card', 'black')),
                 header=dict(left=left, clock_mode=mode, clock_at_t0=now, opacity=0.20),
                 tr=s.get('tr', 'cut'), intensity=round(lerp_curve(INTENSITY, (t0 + t1) / 2), 1), energy=s.get('energy', ''),
                 sfx=s.get('sfx', []), mus=s.get('mus', []), v1=v1_fallback(s))
        for key in ('voice_fx', 'fx_post', 'bg', 'note', 'hold', 'setup', 'errfix', 'device', 'teaser', 'split', 'plate', 'montage',
                    'loop', 'card', 'time_card', 'past'):
            if key in s: o[key] = s[key]
        if 'reuse' in s: o['reuse_t'] = s['reuse']
        if s.get('bg'):
            f = v1_fallback(dict(set=s['bg']['set'], view=s['bg']['view'], var=s['bg']['var']))
            o['v1']['bg'] = dict(set=f['set'], view=f['view'], var=f['var'], post=s['bg'].get('post'))
        o['chip_override'] = s.get('chip')
        o['queen'] = queen_entry(s, o)
        if o['cls'] == 'face':                                    # DIRECTION_V2 4.7: every CU / ECU sits on a bokeh plate
            o['bokeh'] = dict(palette={'ours': 'ours', 'ending': 'ours', 'theirs': 'theirs', 'theirs_break': 'theirs', 'memory': 'memory',
                                       'climax': 'climax', 'stairs': 'stairs', 'ui': 'ours'}.get(world, 'ours'),
                              plate='%s/%s blurred' % (s['set'], s['view']) if s['view'] != 'bokeh' else 'own', discs='45-165 px, +22-38 luma, drift 3-8 px/s')
            if o['dof'] is None and s['view'] not in ('phone_screen',): o['dof'] = dict(focus=1.0, dof=6.75)
        out.append(o)
    finish(out)
    rehome(out)
    return out, cards


def queen_entry(s, o):
    q = dict(s['q']) if s.get('q') else None
    qc = [c for c in o['chars'] if c['who'] == 'queen']
    if q is None and qc:
        q = dict(stage=qc[0].get('stage'))
    if q is None: return None
    if qc and 'stage' not in q: q['stage'] = qc[0].get('stage')
    q.setdefault('step', None)
    q['on_screen'] = bool(qc) or s.get('card') is not None
    return q


def finish(out):
    """Second pass: reuse ids, setup reuse, side-switch glints, chips (text on every shot; pop on the first shot after a switch),
    world blocks, punch-ins."""
    starts = [o['t0'] for o in out]
    def owner(tt):
        return out[max(0, min(len(out) - 1, bisect.bisect_right(starts, tt + 1e-6) - 1))]
    seen = {}
    for o in out:
        key = (o['set'], o['view'])
        o['setup_reused'] = key in seen and o['type'] not in ('CARD', 'BLACK')
        seen.setdefault(key, o['id'])
        if 'reuse_t' in o:
            o['reuse'] = owner(o.pop('reuse_t'))['id']
    # glints: a cut between the ours family (ours, mirror) and the theirs family (theirs, stairs)
    prev = None
    for o in out:
        fam = family(o)
        o['family'] = fam
        o['glint'] = bool(prev and fam and prev != fam)
        if o['tr'] == 'glint' and not o['glint']: o['tr'] = 'cut'
        if o['glint'] and o['tr'] == 'cut': o['tr'] = 'glint'
        if fam: prev = fam
    # chips: text on every shot (its world's place and time); pop (drawn 0.4 s in, held for the shot) on the first shot of
    # an OURS / THEIRS side after a switch, on every entry into a memory (the 14 YEARS AGO stamp) and where the shot list
    # forces one; never on flash-forwards (they carry their red RULE chip) and never in the hook's premise images (before 16 s)
    last_fam, last_world = None, None
    for o in out:
        ch = chip_for(o['world'], o['side'], o['t0'])
        if o.get('family') == 'ours' and ch and ch['style'] == 'theirs': ch = chip_for('ours', 'ours', o['t0'])
        if o.get('family') == 'theirs' and ch and ch['style'] == 'ours': ch = chip_for('theirs', 'theirs', o['t0'])
        ov = o.pop('chip_override', None)
        if ov:
            ch = dict(text=ov.replace('{ours}', ampm(ours_clock(max(o['t0'], CLOCK_T0)))),
                      style='theirs' if ov.startswith('THE') else ('memory' if ov.startswith('14') else 'ours'))
        fam = o.get('family')                                     # where the camera is (the glint rule): through-glass = ours
        pop = False
        if ch and not o.get('teaser') and o['type'] not in ('CARD', 'BLACK') and o['t0'] >= 16.0:
            if o['world'] == 'memory': pop = last_world != 'memory'
            elif fam and fam != last_fam: pop = not o.get('time_card')
        if ov: pop = True
        if ch: ch['pop'] = pop
        o['chip'] = ch
        if fam and not o.get('teaser'): last_fam = fam
        if o['type'] not in ('CARD',): last_world = o['world']
        for h in o['hud']:
            if h.get('type') in ('chip', 'diagram', 'split') and isinstance(h.get('text'), str):
                h['text'] = h['text'].replace('{ours}', ampm(ours_clock(max(o['t0'], CLOCK_T0))))
        for p in (o.get('split') or {}).get('panels', []):
            if isinstance(p.get('chip'), str): p['chip'] = p['chip'].replace('{ours}', ampm(ours_clock(max(o['t0'], CLOCK_T0))))
        for h in o['hud']:
            if h.get('type') == 'dials':
                for side_ in ('left', 'right'):
                    if isinstance(h[side_].get('chip'), str):
                        h[side_]['chip'] = h[side_]['chip'].replace('{ours}', ampm(ours_clock(max(o['t0'], CLOCK_T0))))
        o['frame'] = o['frame'].replace('{ours}', ampm(ours_clock(max(o['t0'], CLOCK_T0))))
    # punch-ins
    for tt, kk, word in SL.PUNCHES:
        o = owner(tt)
        if not o['cam'].get('snap'):
            o['cam']['snap'] = [round(tt, 3), kk, 0.1]
            o['cam']['snap_word'] = word


def rehome(out):
    """An SFX, music or HUD item authored on one shot but timed inside another moves to the shot that contains it. Pinned
    labels, tags and red X stay only on their own picture (trimmed to its end); every other HUD device stays on its shot."""
    starts = [o['t0'] for o in out]
    def owner(tt):
        return out[max(0, min(len(out) - 1, bisect.bisect_right(starts, tt) - 1))]
    for key in ('sfx', 'mus', 'hud'):
        moved = []
        for o in out:
            keep = []
            for item in o[key]:
                tt = item['t']
                if key == 'hud' and item['type'] not in ('label', 'tag', 'red_x'):
                    keep.append(item); continue
                if o['t0'] - 0.02 <= tt < o['t1'] - 0.02:
                    if key == 'hud':
                        item['hold'] = round(min(item.get('hold', 1.2), o['t1'] - tt), 2)
                    keep.append(item)
                else:
                    moved.append(item)
            o[key] = keep
        for item in moved:
            if key == 'hud': continue
            owner(item['t'])[key].append(item)
        for o in out: o[key].sort(key=lambda it: it['t'])


# =================================================================================================== captions (5.5)
FUNC = set('a an the of to in on at for with and or but if as by from that your his her my their its you he she i we they it is was are '
           'be been has had have so than then when where who what like into onto over under about'.split())


CAP_TARGET, CAP_SIX = 1.3, 1.0


def make_captions(cards, cut_times):
    """Phrases of 2-5 words (6 allowed with a penalty: with one-line captions and 2,182 words, a 5-word cap cannot go under
    548 captions; the brief asks about 500-520), broken where a cut falls (so the caption changes with the picture) and at
    punctuation, never after a function word, rarely on a lone word. Dynamic programme per narration line; cost = |chunk
    length - 1.3 s| x 1.6 + 3.0 for one word + 1.0 for six + 2.4 for a break with no cut near it - 1.3 for a break on a cut
    - 1.2 at punctuation + 2.4 after a function word. A caption starts at its first word - 0.08 s, snapped onto a cut within
    0.2 s; it ends where the next starts (or 0.25 s after the line)."""
    cuts = sorted(cut_times)
    def cut_near(x, lo=-0.35, hi=0.12):
        i = bisect.bisect_left(cuts, x + lo)
        return [c for c in cuts[i:i + 4] if x + lo <= c <= x + hi]
    caps = []
    for L in LINES:
        words = [[wd, tt] for wd, tt in L['words']]
        for j in range(len(words)):
            if words[j][1] is None: words[j][1] = words[j - 1][1] if j else L['t']
        n = len(words)
        nxt = LINES[L['i'] + 1]['t'] if L['i'] + 1 < len(LINES) else END
        end_t = min(L['end'] + 0.25, nxt - 0.06)
        def wt(j): return words[j][1] if j < n else end_t
        # dynamic programme over break positions
        best = [(0.0, None)] + [(1e9, None)] * n
        for j in range(1, n + 1):
            for i in range(max(0, j - 6), j):
                k = j - i
                dur = wt(j) - wt(i)
                cost = abs(dur - CAP_TARGET) * 1.6
                if k == 1 and n > 1: cost += 3.0
                if k == 6: cost += CAP_SIX
                last = words[j - 1][0]
                if j < n:
                    if last.lower().strip('",.?!;:') in FUNC: cost += 2.4
                    if last[-1] in ',.?!;:': cost -= 1.2
                    cost += -1.3 if cut_near(wt(j) - 0.08) else 2.4
                if dur > 2.4: cost += (dur - 2.4) * 4
                c = best[i][0] + cost
                if c < best[j][0]: best[j] = (c, i)
        idx, j = [], n
        while j > 0:
            i = best[j][1]; idx.append((i, j)); j = i
        idx.reverse()
        for ci, (i, j) in enumerate(idx):
            c0 = words[i][1] - 0.08
            cn = cut_near(words[i][1] - 0.08, -0.2, 0.2)
            if cn: c0 = min(cn, key=lambda c: abs(c - (words[i][1] - 0.08)))
            if ci + 1 < len(idx):
                c1 = words[idx[ci + 1][0]][1] - 0.08
                cn1 = cut_near(c1, -0.2, 0.2)
                if cn1: c1 = min(cn1, key=lambda c: abs(c - c1))
            else:
                c1 = end_t
            text = ' '.join(x[0] for x in words[i:j])
            if L['who'] != 'N':
                if ci == 0: text = '"' + text
                if ci == len(idx) - 1: text = text + '"'
            for a, b in cards:
                if c0 < b and c1 > a:
                    if c0 >= a: c0 = b
                    else: c1 = a
            if c1 - c0 >= 0.3:
                caps.append(dict(t0=round(c0, 3), t1=round(c1, 3), text=text, line=L['i']))
    caps.sort(key=lambda c: c['t0'])
    for a, b in zip(caps, caps[1:]):
        if a['t1'] > b['t0']: a['t1'] = b['t0']
    for c in caps:
        c['on_cut'] = any(abs(c['t0'] - x) <= 0.2 for x in cut_near(c['t0'], -0.2, 0.2))
    return [c for c in caps if c['t1'] - c['t0'] >= 0.25]


# =================================================================================================== counter (the ring badge)
def counter_track():
    start = w(112, 'sixty')
    calls = [(start, 60), (w(137, 'forty'), 45), (w(206, 'twenty'), 20), (w(246, 'five'), 5), (w(258, 'collar'), 0)]
    steps = []
    for (ta, va), (tb, vb) in zip(calls, calls[1:]):
        n = va - vb
        for j in range(n):
            steps.append([round(ta + (tb - ta) * j / n, 3), va - j, 'call' if j == 0 else 'step'])
    steps.append([round(calls[-1][0], 3), 0, 'zero'])
    return dict(visible=[round(start, 3), SL.card_times(7)[0]], hidden_on=['card'], dim_on={'memory': 0.6}, steps=steps, kind='ring',
                look='RING TIMER BADGE top right under the header at (1760, 118) design px: a thin ring that depletes clockwise with the count '
                     '(60 = full), the number inside in Montserrat 800, label TESS above at 35 %; each step a 0.12 s tick of the ring; '
                     'Tess\'s calls (60, 45, 20, 5) pop to 1.35x with a red flash, in sync with the giant numbers (type beat 4); 0 at the '
                     'collar pull flashes red and the badge leaves with the card 7 glitch',
                why='time on the two sides runs at different speeds: the count is dilated (one step every 4-6 s) and lands exactly on her calls')


def value_at(steps, tt):
    v = None
    for a, b, _ in steps:
        if a <= tt + 1e-6: v = b
    return v


# =================================================================================================== sound
def bed_ranges(shots):
    def bed(s):
        st, var, side = s['set'], s['var'], s['side']
        if side == 'black': return ()
        if side == 'card': return ('card_dip',)
        if side == 'ui' or st in ('type', 'split', 'diagram'): return ('inherit',)
        if st in ('camp_gate', 'camp_path', 'caretaker', 'mess_porch'):
            b = ['ambience_camp_night']
            if st == 'mess_porch': b.append('wind_chimes')
            if st == 'caretaker': b.append('tv_through_wall')
            return tuple(b)
        if st == 'cabin_now':
            b = ['room_tone', 'ambience_camp_night(muffled -10 dB, LP 2 kHz)']
            if var in ('doorway_glow', 'red'): b.append('ambience_dawn(through the doorway -14 dB)')
            return tuple(b)
        if st in ('mirror', 'stairs'):
            return ('ambience_mirror', 'room_tone(-6 dB)') if s['world'] != 'theirs' else ('ambience_mirror', 'ambience_dawn(through glass -16 dB)')
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


def v1_cues():
    """The v1 cues, minus the old counter and old card cues (regenerated), minus SFX_DROP, with SFX_MOVE applied."""
    sp = json.load(open(V1_SOUND))
    out = []
    for c in sp['sfx']:
        if c['name'] == 'countdown_tick': continue
        if any(c.get('note', '').startswith(p) for p in V1_CARD_NOTES): continue
        key = (round(c['t'], 2), c['name'])
        if any(abs(c['t'] - a) < 0.02 and c['name'] == b for a, b in SFX_DROP): continue
        c = {k: v for k, v in c.items() if k not in ('shot', 'exists')}
        for (a, b), nt in SFX_MOVE.items():
            if abs(c['t'] - a) < 0.02 and c['name'] == b:
                c['note'] = (c.get('note', '') + ' (v1 %.2f -> v2 %.2f: re-timed to the new picture)' % (c['t'], nt)).strip()
                c['t'] = nt
        for (a, b), note in SFX_NOTE.items():
            if abs(c['t'] - a) < 0.02 and c['name'] == b: c['note'] = note
        c['origin'] = 'v1'
        out.append(c)
    return out, sp


def device_cues(shots, ctr):
    """Cues for the v2 picture devices (DIRECTION_V2 5.3-5.5, 7 rank 6)."""
    cues = []
    def add(tt, name, g, sp, note, hit=False, **params):
        d = dict(t=round(tt, 3), name=name, gain_db=g, space=sp, note=note, origin='device')
        if hit: d['hit'] = True
        if params: d['params'] = params
        cues.append(d)
    for s in shots:
        for h in s['hud']:
            ty = h['type']
            if ty == 'rule_card':
                t0 = h['appear']
                add(t0, 'glitch', -4, 'dry', 'card in: 2-frame static', dur=0.12, amount=0.8)
                add(t0, 'towel_whip', -4, 'close', 'card %d: the towel whips up off the mirror card' % h['n'])
                add(t0, 'glass_resonance', -2, 'close', 'card lands: the pane rings, the riser peaks here', hit=True)
                add(t0 + 0.13, 'glass_thud', -6, 'close', 'the mirror card settles (4 % overshoot)')
                add(h['rule_write'][0], 'lipstick_draw', -6, 'close', 'RULE written in lipstick by the bullet tip (0.35 s)', strokes=4)
                add(h['numeral_stamp']['t'], 'lipstick_stamp', -3, 'close', 'the numeral %d stamps in (+3-5 LU over the surround)' % h['n'], hit=True)
                if h['words']:
                    add(h['words'][0][1], 'glass_wipe', -14, 'close', 'statement written on (soft grease-pencil squeaks per word)', n=len(h['words']), soft=True)
                add(h['underline_at'], 'lipstick_draw', -8, 'close', 'the command underline swipe in lipstick', strokes=1)
                add(h['wipe_out'], 'glass_wipe', -5, 'close', 'finger-wipe exit smear (carried 0.2 s over the next shot)', strokes=1)
            elif ty == 'like_sub':
                for k, what in enumerate(('like', 'subscribe', 'bell')):
                    add(h['t'] + 0.35 + 0.5 * k, 'ui_pop', -16, 'dry', 'cursor clicks %s' % what)
            elif ty == 'giant_number':
                add(h['t'], 'number_thump', -2, 'dry', 'giant %d slams in (type beat 4)' % h['value'], hit=True)
            elif ty == 'typebeat' and h['n'] in (3, 5):
                add(h['t'], 'number_thump', -3, 'dry', 'type beat %d: %s' % (h['n'], h['text']), hit=True)
            elif ty == 'stamp':
                add(h['t'], 'rubber_stamp', -3, 'close', 'stamp %s' % h['text'], hit=True)
            elif ty == 'highlight':
                add(h['t'], 'highlighter_squeak', -8, 'close', 'highlighter swipe: %s' % h['text'])
            elif ty in ('diagram', 'map', 'level_guide', 'eye_line', 'dials'):
                did = h.get('id', ty)
                if did in ('D1', 'D3', 'D4', 'D5', 'D6', 'D10', 'map', 'level_guide', 'eye_line', 'dials', 'loop_split', 'D8'):
                    add(h['t'], 'chalk_draw', -12, 'close', 'chalk lines draw on (%s)' % did)
                add(h['t'] + 0.05, 'diagram_pop', -10, 'dry', 'diagram %s pops in' % did)
            elif ty == 'count_pop':
                add(h['t'], 'diagram_pop', -18 if not h.get('erase') else -16, 'dry', 'numeral %d %s' % (h['n'], 'ticks off' if h.get('erase') else 'pops'),
                    kind='tick_off' if h.get('erase') else 'pop')
            elif ty == 'teaser':
                add(h['t'], 'flash_hit', -8, 'dry', 'flash-forward %s: red border in' % h['chip'])
                add(s['t1'] - 0.06, 'glitch', -8, 'dry', 'flash-forward glitch out', dur=0.08, amount=0.7)
            elif ty == 'circle':
                add(h['t'], 'lipstick_draw', -8, 'close', 'lipstick circle: %s' % h['text'], strokes=1)
            elif ty in ('label', 'tag'):
                add(h['t'], 'ui_pop' if ty == 'label' else 'lipstick_draw', -10 if ty == 'label' else -12, 'dry' if ty == 'label' else 'close',
                    '%s %s pops in' % (ty, h['text']), **({} if ty == 'label' else dict(strokes=1)))
            elif ty == 'doc':
                for mk in h.get('marks') or []:
                    if mk['what'] == 'chalk': add(mk['t'], 'chalk_draw', -10, 'close', 'chalk: %s' % mk.get('text', ''))
                    elif mk['what'] == 'underline': add(mk['t'], 'highlighter_squeak', -12, 'close', 'underline: %s' % mk.get('text', ''))
        tr = s['tr']
        if s.get('glint'):
            add(s['t0'], 'glint_whoosh', -14, 'dry', 'side switch: glass glint (%s)' % s['world'])
        if tr == 'white':
            add(s['t0'], 'flash_hit', -8, 'dry', 'white flash cut')
        elif tr == 'rewind':
            add(s['t0'], 'tape_rewind', -6, 'dry', 'loop reset: rewind glitch')
        elif tr == 'glitch' and s['side'] != 'card':
            add(s['t0'], 'glitch', -8, 'dry', 'glitch cut', dur=0.08, amount=0.7)
        for fp in s.get('fx_post') or []:
            if fp.get('white', 0) >= 0.5: add(fp['t'], 'flash_hit', -8, 'dry', 'white flash in the shot')
            if fp.get('rewind'): add(fp['t'], 'tape_rewind', -6, 'dry', 'loop reset: rewind scrub')
            if fp.get('pixel_sort'): add(fp['t'], 'pixel_glitch', -2, 'dry', 'pixel-sort: Noah\'s face into hers', hit=True)
        for c in s['chars']:
            for a in c.get('acts') or []:
                if c['who'] == 'queen' and a[2].get('pixel_sort') and a[1] == 'talk':
                    add(589.65, 'pixel_glitch', -6, 'dry', 'S4: Noah\'s face glitches inside the void'); break
    for a, v, kind in ctr['steps']:
        if kind == 'step':
            add(a, 'ring_tick', -20, 'dry', 'ring badge step %d (tiny)' % v)
        elif kind in ('call', 'zero'):
            add(a, 'ring_tick', -4, 'dry', 'ring badge: Tess calls %d' % v, kind='call')
    # one per name and 0.1 s
    seen, out = set(), []
    for c in sorted(cues, key=lambda c: c['t']):
        k = (c['name'], round(c['t'] * 10))
        if k in seen: continue
        seen.add(k); out.append(c)
    return out


def merge_cues(base, extra):
    """base (v1) + extra (v2 shot cues and device cues): an extra cue replaces a base cue of the same name within 0.12 s; a
    device flash/glitch/thump is skipped when a v1 hit already sits within 0.1 s (the hit stays the picture's sound)."""
    out = list(base)
    for c in extra:
        same = [b for b in out if b['name'] == c['name'] and abs(b['t'] - c['t']) < 0.12]
        if same and c.get('origin') == 'device':
            continue
        if c.get('origin') == 'device' and c['name'] in ('ui_pop', 'lipstick_draw') and 'pops in' in c['note'] and \
                any(b['name'] == 'ui_pop' and abs(b['t'] - c['t']) < 0.4 for b in out):
            continue                                              # the v1 tag / label pop is already there
        if c['name'] in ('flash_hit', 'number_thump', 'rubber_stamp') and any(b.get('hit') and abs(b['t'] - c['t']) < 0.1 for b in out
                                                                               if b['name'] in ('impact_hit', 'braam', 'stinger', 'sub_drop')):
            c = dict(c, gain_db=c['gain_db'] - 6, hit=False, note=c['note'] + ' (layer under the v1 hit)')
        for b in same: out.remove(b)
        out.append(c)
    return sorted(out, key=lambda c: (c['t'], c['name']))


def main():
    shots, cards = build()
    cut_times = [s['t0'] for s in shots[1:]]
    caps = make_captions(cards, cut_times)
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
                                       title_at=h['title_at'], text=h['text'], command=h['command'], sentence_end=e(ti), cut=s['t1'],
                                       visible=round(s['t1'] - s['t0'], 2), reflection=h['reflection'], glass=h['glass']))
    meta = dict(title=TITLE, version=2, fps=FPS, size=[2560, 1440], design=[1920, 1080], duration=END, narration_end=DUR, frames=int(round(END * FPS)),
                lead=LEAD, timeline=os.path.relpath(dsl.TIMELINE, FILM), generated_by='plan/make_plan.py from plan/shotlist.py',
                brief='DIRECTION_V2.md', fields='PLAN_V2.md')
    header = dict(left_format='CABIN 7 · CAMP CEDAR LAKE  //  INTRODUCTION | RULE n OF 7 (n from the latest rule card)',
                  look='cap height 1.0 % H at y = 0.052 H, white at 20 % opacity, "RULE n OF 7" at 35 %; clock right-aligned, same size',
                  clock=dict(ours='23:57:00 at %.2f s, real time; runs BACKWARD %.2f-%.2f s (glitch flicker), then forward again from there' % (CLOCK_T0, BACK_T0, BACK_T1),
                             theirs='06:59:40 + ((t - %.2f) mod %.3f): reaches :59 and snaps back to :40 with a 2-frame glitch; 07:00:00 from %.2f (D9)' % (LOOP_T0, LOOP_P, SEVEN_AM),
                             memory='"14 YEARS AGO" in place of the clock', stairs='keeps the clock of the side the camera came from',
                             hidden='before 19.10 s and on the black tail'),
                  side_rule='the clock shows the time of the side the camera is on (shots[].header.clock_mode)',
                  chips='top-left under the header, cap height 1.4 % H, 0.4 s pop; shots[].chip.text on every shot, drawn when chip.pop is true')
    secs = []
    for i, (nm, a, title) in enumerate(SECTIONS):
        b = SECTIONS[i + 1][1] if i + 1 < len(SECTIONS) else END
        ss = [s for s in shots if s['section'] == nm]
        secs.append(dict(name=nm, t0=round(a, 3), t1=round(b, 3), title=title, shots=len(ss), cuts_per_min=round(len(ss) / ((b - a) / 60), 1),
                         intensity=[round(min(s['intensity'] for s in ss), 1), round(max(s['intensity'] for s in ss), 1)]))
    holds = []
    for hid, (a, b, ln, what) in HOLDS.items():
        sh = [s for s in shots if s.get('hold') == hid]
        holds.append(dict(id=hid, brief=[a, b, ln], what=what, shot=sh[0]['id'] if sh else None,
                          t0=sh[0]['t0'] if sh else None, t1=sh[0]['t1'] if sh else None, dur=sh[0]['dur'] if sh else None))
    ladder = [dict(shot=s['id'], t0=s['t0'], **{k: v for k, v in s['queen'].items()}) for s in shots if s.get('queen')]
    devices = [dict(shot=s['id'], t0=s['t0'], type=s['type'], **s['device']) for s in shots if s.get('device')]
    errors = {str(n): dict(error=ERRORS[n], shots=[s['id'] for s in shots if n in (s.get('errfix') or [])]) for n in sorted(ERRORS)}
    doc = dict(meta=meta, sections=secs, rule_cards=rule_cards, holds=holds, queen_ladder=ladder, devices=devices, errors=errors,
               header=header, counter=ctr, captions=caps, shots=shots)
    write_json(os.path.join(HERE, 'shots.json'), doc)

    # ------------------------------------------------------------------ sound plan
    base, sp1 = v1_cues()
    authored = []
    for s in shots:
        for c in s['sfx']:
            c = dict(c); c['origin'] = 'v2'; authored.append(c)
    for c in SL.V2_SFX:
        c = dict(c); c['origin'] = 'v2'; authored.append(c)
    dev = device_cues(shots, ctr)
    cues = merge_cues(base, authored + dev)
    starts = [s['t0'] for s in shots]
    def owner(tt):
        return shots[max(0, min(len(shots) - 1, bisect.bisect_right(starts, tt + 1e-6) - 1))]
    for c in cues:
        c['shot'] = owner(c['t'])['id']
        c['exists'] = c['name'] in EXISTING
        c['t'] = round(c['t'], 3)
    events = []
    for m in sp1['music']['events']:
        m = dict(m); m['shot'] = owner(m['t'])['id']; events.append(m)
    for s in shots:
        for m in s['mus']:
            m = dict(m); m['shot'] = s['id']; events.append(m)
    events.sort(key=lambda m: m['t'])
    names_used = sorted({c['name'] for c in cues})
    unknown = [n for n in names_used if n not in EXISTING and n not in NEW and n not in NEW_V2]
    if unknown: raise SystemExit('SFX names not declared: %s' % unknown)
    beds = bed_ranges(shots)
    for b in beds:
        for nm in b['beds']:
            base_ = nm.split('(')[0].split(' ')[0]
            if base_ not in EXISTING and base_ not in NEW and base_ not in ('card_dip', 'inherit'):
                raise SystemExit('bed name not declared: %s' % base_)
    mins = END / 60
    hits = [c for c in cues if c.get('hit')]
    silences = [m for m in events if m['type'] == 'silence']
    hit_events = []
    for c in sorted(hits, key=lambda c: c['t']):
        if not hit_events or c['t'] - hit_events[-1] > 0.15: hit_events.append(c['t'])
    rises = [m for m in events if m['type'] == 'swell']
    stats = dict(cues=len(cues), per_min=round(len(cues) / mins, 1), hit_cues=len(hits), hits=len(hit_events), hits_per_min=round(len(hit_events) / mins, 1),
                 rises=len(rises), rises_per_min=round(len(rises) / mins, 2), rise_len_median=round(statistics.median(r.get('len', 13) for r in rises), 1),
                 one_shots_per_min=round(len([c for c in cues if c['name'] not in ('ambience_camp_night', 'ambience_dawn', 'ambience_memory', 'ambience_mirror', 'room_tone')]) / mins, 1),
                 silences=len(silences), silences_per_min=round(len(silences) / mins, 2),
                 silence_len_median=round(statistics.median(m['len'] for m in silences), 2) if silences else 0,
                 risers=len([m for m in events if m['type'] == 'riser']), names_used=len(names_used),
                 new_names_used=len([n for n in names_used if n not in EXISTING]), new_v2_names_used=len([n for n in names_used if n in NEW_V2]),
                 from_v1=len([c for c in cues if c.get('origin') == 'v1']), from_v2_shots=len([c for c in cues if c.get('origin') == 'v2']),
                 from_devices=len([c for c in cues if c.get('origin') == 'device']))
    newd = {n: dict(desc=NEW[n][0], build=NEW[n][1]) for n in sorted(NEW)}
    newd.update({n: dict(desc=v[0], build=v[1], fallback=dict(name=v[2][0], params=v[2][1]), v2=True) for n, v in sorted(NEW_V2.items())})
    sp = dict(meta=dict(title=TITLE, version=2, duration=END, generated_by='plan/make_plan.py',
                        sources=dict(epidemic_new='film/_work/samples/epidemic/{sfx,music} (owner downloads; use FIRST when present)',
                                     epidemic_police='Police Officer Video/v2/_work/pov2/samples/epidemic (74 SFX, 6 music)',
                                     free='audio/catalog.json', v1_plan='plan/v1/sound_plan_v1.json (the v1 cues re-homed here)')),
              rules=sp1['rules'] + ['v2: every v1 cue keeps its film time unless SFX_MOVE re-timed it to the new picture; its shot id is the v2 shot that '
                                    'contains it (cue ids "<shot>:<name>:<k>" are new: an old film_events.json does not apply)',
                                    'v2: the new device names (names.new with v2=true) have a fallback existing name + params until built',
                                    'v2: card stamps rise 3-5 LU over their surround; quiet stretches (arrival, memories, the ending) may drop: LRA 4.5-6 LU at -14 LUFS'],
              names=dict(existing=[n for n in EXISTING], used_existing=[n for n in names_used if n in EXISTING], new=newd),
              sfx=cues, beds=beds,
              music=dict(sections=MUSIC_SECTIONS, intensity=[[round(a, 2), round(b / 10, 2)] for a, b in INTENSITY], events=events,
                         note='sections, intensity and events are v1\'s (the music map in audio/cues.py is unchanged); events re-homed to v2 shots'),
              voice_fx={str(k): dict(fx=v[0], how=v[1], line=LINES[k]['en']) for k, v in VOICE_FX.items()},
              epidemic_wishlist=dict(note='The owner offered to download Epidemic files for this film into film/_work/samples/epidemic/{sfx,music}. '
                                          'These are the searches that would lift the sound most; everything has a fallback (free library or synthesis).',
                                     sfx=[dict(names=a, search=b) for a, b in WISHLIST_SFX] +
                                         [dict(names=n, search=v[1].split('"')[1] if '"' in v[1] else v[1]) for n, v in sorted(NEW_V2.items())],
                                     music=[dict(sections=a, search=b) for a, b in WISHLIST_MUSIC]),
              stats=stats)
    write_json(os.path.join(HERE, 'sound_plan.json'), sp)
    print('shots %d, captions %d, sfx cues %d (%d hits; v1 %d, v2 %d, devices %d), music events %d, beds %d' % (
        len(shots), len(caps), len(cues), len(hits), stats['from_v1'], stats['from_v2_shots'], stats['from_devices'], len(events), len(beds)))


if __name__ == '__main__':
    main()
