"""music_plan.py: the music map of "If Your Doctor Calls At 3 AM... DON'T ASK WHAT THEY FOUND", built the police
film's way (intensity curve, tension events, score.py), anchored to the script lines and their words
(W/align/timeline.json, W/align/asr_cache.json): nothing is a hard-coded film time.

Two things live here:
1. The arc (AUDIO_SPEC): one track section per stretch of the story, varispeeded to D / A in score.TRACKS. The dark
   tracks carry the tension (a low bed that thickens rule by rule: ARC adds intensity from rule 3 to rule 7; risers
   peaking on reveal words; true drop-outs before the scares: "Still waiting.", the cord, the pen click, "Waiting.",
   "Grandpa.", the first question; hard stingers on the twists; a rule sting on every "Rule number N"); silence where
   silence is stronger. From the rescue on the owner's WARM tracks take over (Lens Flare 3 for the drive, Beauty Lives
   in Me for the ER, Prosper for Milo living, In Those Hazel Eyes and Follow Your Feet for the outro): the film ends
   safe and grateful. Real doctors are never scored as threats (Halverson's door scene is sad piano, not horror).
2. The film's own sound (IDENTITY, score.py 'hold' events on the stem `show`): the ORIGINAL HOLD MUSIC
   (audio/hold.py) coming back again and again, each time worse: the phone system under "Please hold." in the cold
   open, the tinny 1979 line cut dead by "It can wait until morning.", the comment prompt ("While we're on hold"),
   the unplugged landline playing it, then every room, Grandma humming it, the waiting room's ceiling speaker, the
   pulse count slowing it to a sag (cut dead on "What did you find?"), the car radio warping it with Doctor Later in
   the back seat, faint far down the hospital hall in the final twist, and redeemed, warm, under "Okay. Breathe." and
   on the end card.

Public API (unchanged): TRACK_MAP, FLATTEN, GAIN, INTENSITY, EVENTS, IDENTITY, ARC; resolve(anchor, lines) ('sN' /
'eN' = start / end of line N, 'wN:word' = that word's onset in line N (W/align/asr_cache.json), +- offset, or seconds);
track_map(lines), intensity(lines, duration), events(lines), identity_events(lines), music_cues(lines, duration),
load_lines(timeline_path=None), table(lines).

How it reaches the mix: mix.py --plan full (audio/final_mix.sh) takes this module's track map, intensity, events and
identity (snapping hits within 0.35 s to the picture's hit frames); --plan auto adds the track map and, when the
picture's sheet has no identity events of its own, IDENTITY. IDENTITY 'jingle' events render audio/jingle.py versions
in score.py (render_jingle); 'show' events play a children's tune (score.VINTAGE) clean.

CLI: python3 music_plan.py [--timeline T] [--out W/cues/music_cues_plan.json] [--table]
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.normpath(os.path.join(HERE, '..', '_work'))
TIMELINE = os.path.join(W, 'align', 'timeline.json')
WORDS = os.path.join(W, 'align', 'asr_cache.json')

# ---------------------------------------------------------------------------------------------------- arrangement
# section start, track, offset (s, in the varispeed track), why. Tracks: score.TRACKS (shifts there). The tension arc
# runs on the dark tracks (a low bed that thickens rule by rule); from the rescue on, the owner's warm tracks.
TRACK_MAP = [
    ('s0', 'are_you_alone_victor_lundberg', 22.0,
     'cold open (the trailer: the 3 AM call, "don\'t hang up", the very tall man folded into a little plastic chair, '
     '"Don\'t sit down."): a dark D sub drone that swells to one spike, stepping back under the hold music'),
    ('s15', 'the_forgotten_memories_luella_gren', 8.0,
     'Grandma Ruth and 1979: "that place", the call, the soft tinny hold music, "It can wait until morning.", the '
     'armchair, the coffee, "Still waiting.": the owner\'s sparse, sad piano (C minor -> D minor), grief not fright'),
    ('s36', 'haunted_mind_etienne_roussel', 0.0,
     'Mom the night nurse, Milo always thirsty, asleep everywhere, the jeans falling off him: a slow A-minor unease'),
    ('s49', 'when_the_sun_sets_anna_landstrom', 0.0,
     'Doctor Halverson\'s clinic (coffee-stained scrubs, dinosaur stickers, "Day or night. I mean it."): a quiet warm '
     'D-major pad: real doctors are safe'),
    ('s58', 'dark_tunnels_ethan_sloan', 2.0,
     'sundown: the medicine cabinet swung aside, the yellow card, "Nobody gets sick in this house after dark.": a flat '
     'sub drone that leaves the voice alone'),
    ('s65', 'in_continuum_dream_cave', 0.0,
     'rule 1: the landline at 3 AM, seven rings, Halverson rough and out of breath on the line, "Don\'t you dare tell '
     'me what you found.", nine rings, the cord out of the wall'),
    ('s103', 'irene_kevin_dailey', 16.0,
     'rule 2: the unplugged phone rings anyway; the hold music (identity) from the receiver, then from every room: '
     'starts near silent and builds'),
    ('s124', 'it_s_late_riverworn', 0.0,
     'rule 3: Milo in dinosaur pajamas, "I\'m so thirsty", the hand over his mouth, the pen click in the dark hallway, '
     'the scratch of a pen (C minor -> D minor); silence carries the click'),
    ('s146', 'the_haunted_luella_gren', 6.6,
     'rule 4: the knock, Halverson at the door in the rain ("This can\'t wait."), the note slid under the door, the '
     'match in the sink, her car not leaving: sparse sad piano over a thin drone (sympathy, not threat)'),
    ('s187', 'come_closer_belladonna_strings', 10.0,
     'the bus stop under the flickering streetlight: someone very tall folded up on the bench. Waiting.'),
    ('s192', 'escalation_jon_bjork', 0.0,
     'rule 5: Milo breathing deep and fast, Grandma rocking and humming the hold music, "It can wait." from every '
     'room: a steady escalation (C minor -> D minor)'),
    ('s213', 'turning_stones_stefan_ekstrom', 0.0,
     'rule 6: the living room is a waiting room: a pure dark sub drone under the ceiling speaker\'s hold music, the '
     'fluorescent buzz, NOW SERVING: 1979, the grey people, Grandpa, HIM in the armchair, the ticket: MILO'),
    ('s252', 'a_massive_mist_ethan_sloan', 0.0,
     'rule 7: the cold fingers on the wrist, the count: a low drone under the hold music slowing with every number'),
    ('s270', 'don_t_look_belladonna_strings', 0.0,
     'the narrator ASKS: the questions loosen the tape strip by strip, the faces under it, "It\'s probably nothing.", '
     'the thing between "something\'s wrong" and "I\'ll get help": horror strings rising per question'),
    ('s295', 'the_forgotten_memories_luella_gren', 69.0,
     'the wrist pulled free, the card torn out: "Doctor Later", Grandma wrote them down while she was on hold; she '
     'stares at the burned paper: the 1979 piano returns, its grief understood'),
    ('s307', 'lens_flare_3_peter_sandberg', 18.0,
     'THE RESCUE: Halverson running up the steps, the pulse in the car ("He\'s fighting. We\'re going."), the drive '
     'in the rain, "Questions are how we win.": a building, hopeful drive (A# minor -> A minor)'),
    ('s331', 'dark_forebodings_ethan_sloan', 0.0,
     'the rear-view mirror: Doctor Later folded in the back seat beside Milo, clicking his pen, "It can wait." (the '
     'car radio warps the hold music); Halverson sees him, unsurprised'),
    ('s344', 'lens_flare_3_peter_sandberg', 68.0,
     '"Not tonight. Not on my shift." -- she drives faster: the drive\'s climb resumes at its peak'),
    ('s348', 'beauty_lives_in_me_instrumental_version_johannes_bornlof', 3.8,
     'the ER: the doors open before they reach them, Mom running with a wheelchair, fluids, insulin, machines beeping '
     'like they were cheering, nobody told us to wait: the owner\'s warm track (F# major)'),
    ('s363', 'prosper_megan_wofford', 24.5,
     'Milo lived: twenty-two now, marathons, the dinosaur jeans; Grandma\'s RUTH ticket, Mom dials, "You don\'t wait. '
     'You call."; Grandma\'s questions, the cardiologist\'s coffee, the yellow card burned (C major -> D major)'),
    ('s379', 'end_of_rain_beyza', 20.0,
     'the final twist: "I\'m telling you this from a hospital. Not as a patient." A pediatrician on nights, 3 AM, the '
     'late results, the calls: a very quiet warm A-major pad, a shadow at the end of the hall, "So are we."'),
    ('s404', 'in_those_hazel_eyes_tall_oak_town', 0.0,
     'the outro ("None of this happened..."): the warm hold arrangement hands over to the owner\'s warm D-major track: '
     'the warning signs, the emergency number, the people who answer at three in the morning'),
    ('s435', 'follow_your_feet_a_month_of_sleep', 12.4,
     '"Go back to the comment...": change "don\'t" to "ask", the first name of a doctor or nurse, call someone, like, '
     'subscribe: the owner\'s bright G-major track, then the warm hold music closes the film'),
]

# slug -> share of the track's own dynamics evened out (score.FLATTEN 0.3 otherwise)
FLATTEN = {'the_forgotten_memories_luella_gren': 0.5, 'the_haunted_luella_gren': 0.45, 'end_of_rain_beyza': 0.6,
           'lens_flare_3_peter_sandberg': 0.35, 'beauty_lives_in_me_instrumental_version_johannes_bornlof': 0.55,
           'prosper_megan_wofford': 0.55, 'in_those_hazel_eyes_tall_oak_town': 0.6,
           'follow_your_feet_a_month_of_sleep': 0.6, 'when_the_sun_sets_anna_landstrom': 0.5,
           'it_s_late_riverworn': 0.5, 'are_you_alone_victor_lundberg': 0.7}
# (test 1: are_you_alone from 0 s sat 25-30 LU under the voice for 20 s (its near-silent intro): from 22 s, flattened)
# slug -> level trim (dB): the sub drones read quiet (+2.5..+4.5, measured in the earlier films); the owner's new
# melodic tracks are mid-band and loud (Follow Your Feet -7 LUFS, In Those Hazel Eyes -9.3 with a 2.2 kHz centroid:
# they sit on the voice's band): down
GAIN = {'dark_tunnels_ethan_sloan': 3.0, 'a_massive_mist_ethan_sloan': 3.5, 'dark_forebodings_ethan_sloan': 2.5,
        'end_of_rain_beyza': 3.0, 'are_you_alone_victor_lundberg': 4.0, 'turning_stones_stefan_ekstrom': 4.5,
        'when_the_sun_sets_anna_landstrom': 3.0, 'the_haunted_luella_gren': 0.5, 'in_continuum_dream_cave': 4.0,
        'escalation_jon_bjork': 3.5, 'irene_kevin_dailey': 1.0, 'the_forgotten_memories_luella_gren': -1.0,
        # test 2: rule 1 sat -14..-22 LU: in_continuum +2 -> +4
        'it_s_late_riverworn': 0.5,      # final mix: rule 3 sat 2 LU under rule 2 (-2 -> +0.5)
        'lens_flare_3_peter_sandberg': -1.5,
        'beauty_lives_in_me_instrumental_version_johannes_bornlof': -1.0, 'prosper_megan_wofford': -2.0,
        'in_those_hazel_eyes_tall_oak_town': -3.0, 'follow_your_feet_a_month_of_sleep': -7.0,
        'come_closer_belladonna_strings': 0.0, 'don_t_look_belladonna_strings': 3.0}
# (tests 7 and 8: rule 7's drone and strings sat -20..-27 LU, the ER's warm track -15..-24: a_massive_mist +2, don't_look
# +3, Beauty Lives in Me +2)

# ---------------------------------------------------------------------------------------------------- intensity
INTENSITY = [
    # cold open (strong), the hold music, the rules, "a scary voice... and a dangerous one"
    ('s0', 0.55), ('s1', 0.6), ('s2', 0.66), ('s4', 0.78), ('s6', 0.8), ('s7', 0.3), ('s9', 0.4), ('s12', 0.55),
    ('s13', 0.62), ('s14', 0.66), ('e14', 0.7),
    # Ruth, 1979 (grief), the coffee, "Still waiting."
    ('s15', 0.35), ('s18', 0.45), ('s20', 0.4), ('s26', 0.55), ('s28', 0.5), ('s29', 0.55), ('s31', 0.62),
    ('s32', 0.4), ('s35', 0.45),
    # Mom, Milo, Halverson (the calm quarter), sundown, the card
    ('s36', 0.3), ('s45', 0.36), ('s49', 0.22), ('s56', 0.25), ('s58', 0.4), ('s62', 0.48), ('s64', 0.55),
    # rule 1
    ('s65', 0.55), ('s67', 0.6), ('s72', 0.66), ('s74', 0.62), ('s80', 0.7), ('s83', 0.78), ('s85', 0.72),
    ('s88', 0.8), ('s89', 0.6), ('e91', 0.62),
    # the comment prompt (on hold)
    ('s92', 0.18), ('e102', 0.2),
    # rule 2 (thicker than rule 1)
    ('s103', 0.55), ('s107', 0.66), ('s110', 0.5), ('s114', 0.56), ('s117', 0.52), ('s119', 0.6), ('s120', 0.68),
    ('e123', 0.8),
    # rule 3
    ('s124', 0.6), ('s127', 0.5), ('s130', 0.56), ('s134', 0.66), ('s137', 0.6), ('s138', 0.75), ('s140', 0.8),
    ('s141', 0.62), ('e145', 0.66),
    # rule 4 (sympathy: Halverson is the hero), the bus stop
    ('s146', 0.62), ('s149', 0.68), ('s155', 0.56), ('s161', 0.66), ('s166', 0.6), ('s170', 0.55), ('s177', 0.62),
    ('s179', 0.66), ('s182', 0.6), ('s187', 0.72), ('s190', 0.84), ('e191', 0.86),
    # rule 5
    ('s192', 0.66), ('s195', 0.72), ('s200', 0.78), ('s201', 0.62), ('s205', 0.72), ('s207', 0.6), ('s210', 0.82),
    ('s211', 0.9), ('e212', 0.92),
    # rule 6 (the waiting room)
    ('s213', 0.75), ('s217', 0.82), ('s224', 0.78), ('s233', 0.85), ('s235', 0.88), ('s240', 0.94), ('s245', 0.9),
    ('s249', 0.96), ('e251', 0.98),
    # rule 7: the count, the questions, the faces, the card
    ('s252', 0.8), ('s255', 0.72), ('s258', 0.82), ('s262', 0.78), ('s266', 0.9), ('s268', 0.7), ('s270', 0.86),
    ('s276', 0.94), ('s280', 1.0), ('s285', 1.0), ('s287', 0.86), ('s291', 0.8), ('s293', 0.86), ('s295', 0.55),
    ('s298', 0.66), ('s302', 0.6), ('e306', 0.5),
    # the rescue (hope rising), the back seat, "Not on my shift."
    ('s307', 0.55), ('s313', 0.6), ('s320', 0.52), ('s324', 0.62), ('s330', 0.66), ('s331', 0.8), ('s335', 0.9),
    ('s340', 0.72), ('s344', 0.82), ('e346', 0.9),
    # the ER (warm, alive), Milo lived, Grandma
    ('s348', 0.7), ('s352', 0.62), ('s356', 0.55), ('s360', 0.4), ('s363', 0.45), ('s365', 0.38), ('s367', 0.3),
    ('s371', 0.45), ('s375', 0.5), ('e378', 0.45),
    # the final twist (a shadow, then "So are we.")
    ('s379', 0.35), ('s383', 0.4), ('s390', 0.45), ('s394', 0.5), ('s397', 0.58), ('s398', 0.66), ('s400', 0.5),
    # the outro (calm, warm; bright for the call to action; a little shadow on "Next time")
    ('s401', 0.25), ('s404', 0.3), ('s418', 0.34), ('s430', 0.4), ('s435', 0.5), ('s447', 0.55), ('s452', 0.35),
    ('s453', 0.3), ('e455', 0.3),
]

# ---------------------------------------------------------------------------------------------------- events
# (anchor, type, level, len[, extra]). Silences sit under the line before the scare and end on it; rule stings on every
# "Rule number N"; risers end on their anchor; 'nosnap' keeps a word's time when the picture has a hit nearby.
EVENTS = [
    # cold open
    ('s2', 'riser', 0.5, 14.0),                                       # the tall man folded into the chair...
    ('s4-0.05', 'hit', 0.7, None),                                    # "Take a seat."
    ('e5', 'silence', 0.7, 1.2),                                      # "It can wait." -> "Don't sit down."
    ('s6', 'stinger', 0.6, None),
    ('e14', 'sub_drop', 0.55, None),                                  # "...a scary voice... and a dangerous one."
    # 1979
    ('s26-0.3', 'silence', 0.6, 0.9),                                 # the kind voice on the line
    ('s30', 'swell', 0.45, 5.0),                                      # "He was still sitting there." ->
    ('s31-0.2', 'silence', 0.8, 1.6), ('e31+0.1', 'sub_drop', 0.4, None),  # "Still waiting."
    # sundown, the card
    ('e64', 'sub_drop', 0.45, None),                                  # "Nobody gets sick in this house after dark."
    # rule 1
    ('s65-0.1', 'rule', 0.7, None, {'nosnap': True}),
    ('s67-0.25', 'silence', 0.6, 0.6),                                # "At three in the morning, the phone rang."
    ('s80', 'swell', 0.5, 6.0),                                       # Halverson's "...I need you to..."
    ('s83', 'stinger', 0.55, None),                                   # "Don't you dare tell me what you found."
    ('e88-0.6', 'silence', 0.85, 2.0),                                # the cord out: "and the house went quiet."
    # rule 2
    ('s103-0.1', 'rule', 0.7, None, {'nosnap': True}),
    ('e106', 'silence', 0.5, 0.7), ('s107', 'hit', 0.6, None),         # "The phone rang anyway."
    ('s110-0.3', 'silence', 0.55, 0.6),                               # "Just music." (the hold music alone)
    ('s120', 'swell', 0.6, 9.0),                                      # ...the hallway, the living room ->
    ('s123', 'stinger', 0.6, None),                                   # "From Grandpa's chair."
    # rule 3
    ('s124-0.1', 'rule', 0.7, None, {'nosnap': True}),
    ('w138:click-0.7', 'silence', 0.9, 2.2),                          # "...I heard a pen click." (the click alone)
    ('s140', 'swell', 0.5, 5.0),                                      # "Something, in our hallway, writing down..."
    ('e145', 'sub_drop', 0.45, None),                                 # "Doctor Halverson did."
    # rule 4
    ('s146-0.1', 'rule', 0.7, None, {'nosnap': True}),
    ('e148', 'silence', 0.5, 0.6),                                    # -> "At three forty, someone knocked."
    ('s161', 'hit', 0.35, None),                                      # "This can't wait." (urgency, not fright)
    ('s187', 'riser', 0.5, 8.0),                                      # the bus stop, the flickering light ->
    ('s190', 'stinger', 0.6, None),                                   # "Knees above his head."
    ('s191-0.3', 'silence', 0.8, 1.4), ('e191', 'sub_drop', 0.5, None),     # "Waiting."
    # rule 5
    ('s192-0.1', 'rule', 0.7, None, {'nosnap': True}),
    ('s195', 'riser', 0.4, 6.0),                                      # "By four, Milo's breathing had changed."
    ('s207-0.2', 'silence', 0.6, 1.0),                                # "She stopped rocking."
    ('s210', 'riser', 0.55, 5.5),                                     # "It's saying it right now." ->
    ('s212', 'hit', 0.75, None),                                      # "It can wait." (from every room)
    # rule 6
    ('s213-0.1', 'rule', 0.7, None, {'nosnap': True}),
    ('e217+0.02', 'braam', 0.8, 3.0, {'boost': 3.5}),   # final mix: after the words, not on them                                      # "It was a waiting room."
    ('s223', 'stinger', 0.5, None),                                   # "Now serving: 1979."
    ('s234-0.3', 'silence', 0.8, 1.5), ('e234', 'sub_drop', 0.5, None),     # "Grandpa."
    ('s235', 'swell', 0.6, 14.0),                                     # HIM in the armchair -> his head
    ('s240', 'braam', 0.7, 3.5),                                      # "And his head... long, and narrow..."
    ('e250+0.02', 'hit', 0.9, None, {'boost': 3.5}),                                       # "Take a seat."
    # rule 7
    ('s252-0.1', 'rule', 0.75, None, {'nosnap': True}),
    ('w270:what-0.9', 'silence', 0.9, 1.9),   # final mix: dead through the whole question                           # the count stops; the question
    ('e270+0.02', 'hit', 0.85, None, {'boost': 3.0}),                                 # "What did you find?"
    ('s276', 'swell', 0.7, 10.0),                                     # every question, the tape looser ->
    ('e280+0.02', 'braam', 0.9, 3.5, {'boost': 3.5}),                                     # "...under the tape, there was no doctor."
    ('e285+0.02', 'stinger', 0.85, None, {'boost': 3.5}),                                   # "Then... me."
    ('s293', 'sub_drop', 0.5, None),                                  # "It can wait." (the one thing...)
    ('s298-0.3', 'silence', 0.8, 1.0), ('s298', 'hit', 0.7, None),    # "Doctor Later."
    ('e302', 'sub_drop', 0.4, None),                                  # "While she was on hold."
    # the rescue
    ('s331-0.3', 'silence', 0.7, 1.0), ('e332+0.02', 'stinger', 0.75, None, {'boost': 3.0}),    # "He was in the back seat."
    ('s335', 'hit', 0.6, None),                                       # "It can wait," (the back seat)
    ('s344', 'riser', 0.5, 4.5),                                      # -> "Not on my shift."
    ('e346', 'sub_drop', 0.3, None),
    # the ER, after
    ('e360', 'sub_drop', 0.25, None),                                 # "Still rocking a little."
    ('s367-0.2', 'silence', 0.5, 0.9),                                # "It said: Ruth."
    # the final twist
    ('s380-0.2', 'silence', 0.5, 0.8), ('s380', 'stinger', 0.35, None),     # "Not as a patient."
    ('s398', 'swell', 0.45, 7.0),                                     # the last plastic chair ->
    ('s400-0.25', 'silence', 0.55, 0.8),                              # "So are we."
    # the outro
    ('e452', 'sub_drop', 0.3, None),                                  # "...don't get on."
]

# ---------------------------------------------------------------------------------------------------- identity
# The HOLD MUSIC (audio/hold.py, score.py 'hold'): an ORIGINAL lounge tune that keeps coming back, each time worse,
# until it is redeemed in the outro. (anchor, type, level, len, extra): 'version', 'until' (an anchor: sets len),
# stop ('fade' | 'cut' | 'drag'), fade (fade-in s), off, phrases, tempo, counts (anchors: the pulse count).
IDENTITY = [
    # the cold open: the phone system ("Your call is important to us. Please hold.") and the tune under the rules
    ('s7-0.9', 'hold', 0.5, None, dict(version='landline', until='s12+0.5', stop='fade', fade=0.4)),
    # 1979: "A recording put her on hold. Soft, tinny music." -- cut dead by the kind voice
    ('s20+0.6', 'hold', 0.55, None, dict(version='phone_1979', until='s26-0.15', stop='cut', fade=0.2)),
    # the comment prompt: "Okay. Hold on. Your call is important to us..." (clean, a wink)
    ('s93', 'hold', 0.45, None, dict(version='studio', until='e102+0.4', stop='fade', fade=0.6)),
    # rule 2: the unplugged phone: "Just music. Hold music." -- then from the hallway, the living room, the chair
    ('s110-0.05', 'hold', 0.6, None, dict(version='landline', until='s120+1.0', stop='fade', fade=0.05)),
    ('s120', 'hold', 0.55, None, dict(version='rooms', until='s124-0.5', stop='fade', fade=1.5)),
    # rule 5: still playing in every room; Grandma hums along with it, rocking Milo
    ('s195', 'hold', 0.3, None, dict(version='rooms', until='s213-0.4', stop='fade', fade=2.0)),
    ('w201:humming+0.3', 'hold', 0.5, 11.0, dict(version='hum', phrases=(0, 1), stop='fade')),
    # rule 6: the waiting room's ceiling speaker
    ('s217+0.4', 'hold', 0.45, None, dict(version='ceiling', loops=5, until='s252-1.2', stop='fade', fade=1.0)),
    # rule 7: the pulse count -- slower at "One", "Two", "Three"; cut dead on the first question
    ('s257', 'hold', 0.6, None, dict(version='pulse', until='w270:what-0.05', stop='cut', fade=0.8,
                                     counts=['w258:one', 'w260:two', 'w267:three'])),
    # the rescue: the car radio, warped, while he sits in the back seat; cut on "Not on my shift."
    ('s331-0.1', 'hold', 0.5, None, dict(version='car_radio', until='e346', stop='cut', fade=0.4)),
    # the final twist: faint, far down the empty hospital hall
    ('s397', 'hold', 0.55, None, dict(version='far_hall', until='e400+0.3', stop='fade', fade=1.0)),
    # the outro: the motif redeemed (warm), and the film's last bars on the end card
    ('s401+0.2', 'hold', 0.5, None, dict(version='warm', until='s404+3.0', stop='fade', fade=0.8)),
    ('e455+0.2', 'hold', 0.6, 10.3, dict(version='warm', phrases=(2, 3), tempo=106.0, stop='fade', fade=0.6)),   # final mix: ends with the picture (1305.17 s)
]


# ---------------------------------------------------------------------------------------------------- resolve
_A = re.compile(r'^([se])(\d+)([+-][0-9.]+)?$')
_WA = re.compile(r'^w(\d+):([^+\-]+)([+-][0-9.]+)?$')
_WORDS = None


def _norm(w):
    return re.sub(r"[^a-z0-9']", '', str(w).lower().replace('mr.', 'mister'))


def _words():
    global _WORDS
    if _WORDS is None:
        try:
            _WORDS = [(_norm(w), float(t)) for w, t in json.load(open(WORDS)).get('en_words', [])]
        except Exception:
            _WORDS = []
    return _WORDS


def _line(i, lines):
    return lines[i] if i < len(lines) and lines[i].get('i', i) == i else next(x for x in lines if x.get('i') == i)


def resolve(anchor, lines):
    if isinstance(anchor, (int, float)):
        return float(anchor)
    a = str(anchor).strip()
    m = _WA.match(a)
    if m:                                               # 'w111:clack': that word's onset inside line 111
        l = _line(int(m.group(1)), lines)
        want = _norm(m.group(2))
        cand = [t for w, t in _words() if l['t'] - 0.35 <= t <= l['end'] + 0.05 and w.startswith(want)]
        t = cand[0] if cand else float(l['t'])
        return t + (float(m.group(3)) if m.group(3) else 0.0)
    m = _A.match(a)
    if not m:
        raise ValueError(f'bad anchor {anchor!r}')
    l = _line(int(m.group(2)), lines)
    t = float(l['t'] if m.group(1) == 's' else l['end'])
    return t + (float(m.group(3)) if m.group(3) else 0.0)


def load_lines(timeline_path=None):
    tl = json.load(open(timeline_path or TIMELINE))
    return tl['lines'], float(tl.get('duration_en') or max(l['end'] for l in tl['lines']))


def track_map(lines):
    out = []
    for a, s, o, _w in TRACK_MAP:
        x = {'t0': round(resolve(a, lines), 3), 'slug': s, 'off': float(o)}
        if s in FLATTEN:
            x['flatten'] = FLATTEN[s]
        if GAIN.get(s):
            x['gain_db'] = GAIN[s]
        out.append(x)
    return out


# the bed thickens rule by rule (AUDIO_SPEC: the second quarter the calmest, louder by rule 5): (from, to, + intensity)
# (final mix: rule 3 +0.03, rule 4 +0.08, rule 5 +0.1, rule 6 +0.12: the first full mix measured rules 2-4 flat)
ARC = [('s124', 's146', 0.03), ('s146', 's192', 0.05), ('s192', 's213', 0.07), ('s213', 's252', 0.09),
       ('s252', 's307', 0.1)]


def intensity(lines, duration=None):
    arc = [(resolve(a, lines), resolve(b, lines), d) for a, b, d in ARC]
    pts = sorted((round(resolve(a, lines), 3), float(min(1.0, v + sum(d for x, y, d in arc if x <= resolve(a, lines) < y))))
                 for a, v in INTENSITY)
    out = []
    for t, v in pts:
        if out and abs(out[-1][0] - t) < 0.05:
            out[-1] = [t, v]
        else:
            out.append([t, v])
    if duration:
        out.append([round(float(duration), 2), 0.0])
    return out


def events(lines):
    ev = []
    for row in EVENTS:
        a, ty, lv, ln = row[:4]
        e = {'t': round(resolve(a, lines), 3), 'type': ty, 'level': lv}
        if ln is not None:
            e['len'] = ln
        if len(row) > 4 and row[4]:
            e.update(row[4])
        ev.append(e)
    return sorted(ev, key=lambda e: e['t'])


def identity_events(lines):
    """The film's own sound: the jingle's versions (score.py 'jingle'), the children's tunes ('show'). 'until' (an
    anchor) sets len; 'anchors' [(beat, anchor)] (or 'COLD_OPEN': jingle.COLD_OPEN_ANCHORS) become film seconds."""
    ev = []
    for a, ty, lv, ln, extra in IDENTITY:
        t = resolve(a, lines)
        e = {'t': round(t, 3), 'type': ty, 'level': lv}
        x = dict(extra)
        if 'until' in x:
            ln = max(0.5, resolve(x.pop('until'), lines) - t)
        if x.get('anchors') == 'COLD_OPEN':
            sys.path.insert(0, HERE)
            import jingle as JG
            x['anchors'] = [[float(b), float(s)] for b, s in JG.COLD_OPEN_ANCHORS]
            x['melody_anchors'] = [[float(b), float(s)] for b, s in JG.COLD_OPEN_MELODY]
        elif x.get('anchors'):
            x['anchors'] = [[float(b), round(resolve(s, lines), 3)] for b, s in x['anchors']]
        if x.get('counts'):                              # the pulse count: anchors -> film seconds
            x['counts'] = [round(resolve(c, lines), 3) for c in x['counts']]
        if 'phrases' in x:
            x['phrases'] = list(x['phrases'])
        if ln is not None:
            e['len'] = round(float(ln), 3)
        e.update(x)
        ev.append(e)
    return sorted(ev, key=lambda e: e['t'])


def music_cues(lines=None, duration=None):
    if lines is None:
        lines, d0 = load_lines()
        duration = duration or d0 + 2.5
    duration = float(duration or max(l['end'] for l in lines) + 2.5)
    idt = identity_events(lines)
    duration = max(duration, max(e['t'] + OUTRO_LEN if e.get('version') == 'outro' else e['t'] + float(e.get('len') or 0)
                                 for e in idt) + 0.6) if idt else duration
    return {'duration': round(duration, 2), 'intensity': intensity(lines, duration),
            'events': sorted(events(lines) + idt, key=lambda e: e['t']),
            'track_map': track_map(lines)}


OUTRO_LEN = 9.75        # (the Bunnyman's jingle outro; this film's last 'hold' warm event carries its own len: 11.5 s,
                        # the end card holds to about e455 + 11.7 s)


def table(lines):
    out = []
    tm = track_map(lines)
    for k, (x, (_a, _s, _o, why)) in enumerate(zip(tm, TRACK_MAP)):
        t1 = tm[k + 1]['t0'] if k + 1 < len(tm) else max(l['end'] for l in lines)
        out.append(f"{x['t0']:7.2f}-{t1:7.2f}  {x['slug']:40s} from {x['off']:5.1f}s  {why}")
    out.append('identity:')
    for e in identity_events(lines):
        ex = {k: v for k, v in e.items() if k not in ('t', 'type', 'level', 'len', 'anchors')}
        out.append(f"  {e['t']:7.2f}-{e['t'] + e.get('len', 0):7.2f}  {e['type']:6s} {e['level']:.2f}  {ex}")
    return '\n'.join(out)


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--timeline', default=TIMELINE)
    ap.add_argument('--out', default=os.path.join(W, 'cues', 'music_cues_plan.json'))
    ap.add_argument('--table', action='store_true')
    a = ap.parse_args()
    L, d = load_lines(a.timeline)
    mc = music_cues(L, d + 2.5)
    if a.table:
        print(table(L))
        from collections import Counter
        print(Counter(e['type'] for e in mc['events']))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(mc, open(a.out, 'w'), indent=0)
    print('wrote', a.out, len(mc['events']), 'events,', len(mc['intensity']), 'intensity points')
