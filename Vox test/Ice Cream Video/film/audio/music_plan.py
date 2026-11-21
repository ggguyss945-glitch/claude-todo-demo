"""music_plan.py: the music map of "If The Ice Cream Truck Plays Its Song In Winter... DON'T GO OUTSIDE", built the
police film's way (intensity curve, tension events, score.py), anchored to the script's WORDS: every anchor names a
phrase of script/narration_en.txt and is found in the timeline's line texts at run time (W/align/timeline.json), so a
re-paced or re-cut voice edit and any line split or tag scheme in script/lines.py need no change here. Nothing is a
hard-coded film time and nothing from the Bus film is left in.

Anchors (resolve(anchor, lines)):
    'Rule number one'            the start of the line holding that phrase (case and punctuation ignored)
    'end:Head first. Legs last'  the end of the line holding the phrase's LAST word
    'Sweet. Too slow#gap'        the onset of the word 'gap' inside that line (W/align/asr_cache.json words when
                                 present, else interpolated by character position inside the line)
    ... +0.4 / ... -1.2          an offset in seconds (a space, then the signed number, at the very end)
    'sN' / 'eN' / 'wN:word'      a line index form (kept for tools), or plain seconds
An anchor that is not found is skipped with a warning (the row drops out; the mix never fails on the plan).

The arc (AUDIO_SPEC): one track section per stretch of the story, varispeeded to D / A in score.TRACKS. Icy dread
from the hook (Throbbing Anxiety); the setup and 1958 on The Haunted's thin piano; rule by rule the bed thickens
(ARC adds intensity from rule 2 to the climax); silence before the biggest scares ("The song stops.", "Click.", the TV,
"Silence.", "No cloud.", the hatch, "was across the street."); hard hits on the three glimpses, the transformation
and the twists; a DRIVING chase from "I run." to the slammed door (I'm the Villain); the attic dread (Don't Look);
the twist's turn on a sparse sad piano (The Forgotten Memories); rule 7's slow swell (Irene); a pulsing build across
the street (Impossible Theory) to the empty note; then the warm turn: Redeemed under the plow's horn and the porch
lights, Lullaby before Christmas for "Bye, Benny", With the Dawn for the morning and the cocoa, A Heart Full of Spring
under rule eight, Peaceful Melody under the tips, and a SHORT warm outro (the chime redeemed).

The film's own sound (IDENTITY, score.py 'chime' events = JINGLE_MODULE 'chime_ice' on the stem `show`): HIS CHIME
(audio/chime_ice.py), an ORIGINAL music-box tune that always ends on a GAP where the last note should be, returning
as the night gets worse: the burst under "Who's cold?", three slow notes in the radio static, far away and coming
closer street by street (its gap lands on "a gap where the last note should be"), full outside until it stops dead,
the lullaby, warped as it moves to Kessler's, cheerful through the whole transformation, hanging on the empty beat at
the climax and falling apart, the stinger across town, and redeemed (the last note PLAYED) in the morning and the
outro. His bells under the copied voices are mix.py's 'mimic' line FX; the bells in the static are sfx.py's
'radio_bells' / 'radio_static' (bells=) cues.

How it reaches the mix: mix.py --plan full (audio/final_mix.sh) takes this module's track map, intensity, events and
identity (snapping hits within 0.35 s to the picture's hit frames); --plan auto adds the track map and, when the
picture's sheet has no identity events of its own, IDENTITY.

Public API (unchanged): TRACK_MAP, FLATTEN, GAIN, INTENSITY, EVENTS, IDENTITY, ARC; resolve(anchor, lines),
line_index(anchor, lines), track_map(lines), intensity(lines, duration), events(lines), identity_events(lines),
music_cues(lines, duration), load_lines(timeline_path=None), table(lines).

CLI: python3 music_plan.py [--timeline T] [--out W/cues/music_cues_plan.json] [--table]
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.normpath(os.path.join(HERE, '..', '_work'))
TIMELINE = os.path.join(W, 'align', 'timeline.json')
WORDS = os.path.join(W, 'align', 'asr_cache.json')

# ---------------------------------------------------------------------------------------------------- arrangement
# (anchor, track slug, offset s in the varispeed track, why). Tracks and shifts: score.TRACKS (this film's table).
TRACK_MAP = [
    ('If the ice cream truck plays its song', 'throbbing_anxiety_dream_cave', 0.0,
     'the hook: icy dread under the three "If... don\'t" lines; steps back under the chime burst ("Who\'s cold?")'),
    ('Larkfield. Minus thirty-one', 'the_haunted_luella_gren', 4.0,
     'the setup: the absent adults, the radio, the shovel, 1958 and the red mitten on a thin piano and a high drone'),
    ('Rule number one', 'turning_stones_stefan_ekstrom', 0.0,
     'rule 1: a pure low drone, so the far chime is the only melody coming street by street'),
    ('The truck glides down Birch Lane', 'i_m_the_villain_dream_cave', 6.0,
     'the drive-by: his slow pulse under the chime; glimpse 1; drops to nothing when the song stops'),
    ('Stop. His song is playing outside', 'are_you_alone_victor_lundberg', 0.0,
     'the comment beat: only a sub drone and the idling engine'),
    ('Rule number two', 'unvaried_elin_piel', 10.0,
     'rule 2: a steady creeping bed (the tap, the doormat, the windowsill, the open window)'),
    ("Lina's on the couch, holding the cone", 'impossible_theory_rachel_sandy', 0.0,
     'the near miss: a heavy build to the slap; cut by "Click." (the furnace, the lights, the TV skull)'),
    ('Rule number three', 'sleep_forever_luella_gren', 0.0,
     'rule 3: the cold coming in (frost inside, breath clouds); steps back under the chime lullaby'),
    ('The radio crackles', 'come_closer_belladonna_strings', 0.0,
     'the fake Dad: a trusted voice twisting the rules; the leg shadow; twist 1 and the jammed radio (Tears of a '
     'Shadow was planned here: the recogniser hears voice-like fragments in it, so it never plays under narration)'),
    ('Rule number four', 'escalation_jon_bjork', 0.0,
     'rule 4: two-ten, the blanket cold, the door swinging open, Lina walking to the window'),
    ('I run. Knee-deep snow', 'all_exits_closed_guy_copeland', 30.0,
     'the run to the window: the driving part of the pulse (from 30 s: -16..-11 LUFS short-term)'),
    ('He keeps smiling. Keeps waving', 'are_you_alone_victor_lundberg', 20.0,
     'the transformation: only a sub drone under it, so the chime plays on cheerful and alone; hits on every step'),
    ('I rip my foot out of the boot', 'i_m_the_villain_dream_cave', 123.0,
     'THE CHASE home: its loudest driving stretch (from 110 s of the original: -16..-11 LUFS short-term), from the '
     'one-sock run to the slammed door and the stolen mitten'),
    ('Her fingertips are white', 'when_the_sun_sets_anna_landstrom', 0.0,
     'first aid: a quiet warm pad (care, not threat); "Shivering means you\'re fighting."'),
    ('Rule number five', 'can_they_see_us_experia', 0.0,
     'rule 5: Mom at the door, the breath test, the face up the glass, the frosting knob'),
    ('Rule number six', 'don_t_look_belladonna_strings', 0.0,
     'rule 6: the attic dread: clicks across the ceiling, the hatch, the leg under the door'),
    ('Then the song moves', 'the_forgotten_memories_luella_gren', 0.0,
     'the twist\'s turn: the truck at Kessler\'s door; every clue clicking into place on a sparse sad piano'),
    ('Rule number seven', 'irene_kevin_dailey', 0.0,
     'rule 7 and the reread: near silence building ("everybody inside means somebody alone")'),
    ("Mr. Kessler is halfway to the window", 'impossible_theory_rachel_sandy', 40.0,
     'the climax: a pulsing build across the street, the cage, the copied boy, to the empty note'),
    ("Dad's plow roars onto Birch Lane", 'redeemed_blue_saga', 0.0,
     'the warm turn: the horn, the porch lights, "Cold. Alone. He needs both."; the song falls apart over it'),
    ('Mr. Kessler whispers', 'lullaby_before_christmas_franz_gordon', 0.0,
     '"Bye, Benny." and the paramedics: tender'),
    ('In the morning, Dad, Lina and I shovel', 'with_the_dawn_megan_wofford', 0.0,
     'the morning: three shovels, the chimney smoking, the cocoa, "First time anyone knocked on mine."'),
    ('Two nights later, across town', 'dark_forebodings_ethan_sloan', 0.0,
     'the stinger: a flat dark drone under the far chime; a house with no chimney smoke'),
    ('Rule number eight', 'a_heart_full_of_spring_franz_gordon', 0.0,
     'rule eight: warm, together, with a grown-up'),
    ("There's no Mister Shiver", 'peaceful_melody_megan_wofford', 0.0,
     'the tips (cold signs, frostbite, no oven, the lures, knock on a door): gentle, low, never on the voice'),
    ("Like if you'd have crossed the street", 'a_heart_full_of_spring_franz_gordon', 60.0,
     'the SHORT outro under the chime redeemed; "Next time..." gets one shadow'),
]

# slug -> share of the track's own dynamics evened out (score.FLATTEN 0.3 otherwise)
FLATTEN = {'throbbing_anxiety_dream_cave': 0.35, 'the_haunted_luella_gren': 0.45, 'turning_stones_stefan_ekstrom': 0.5,
           'unvaried_elin_piel': 0.5, 'sleep_forever_luella_gren': 0.45, 'come_closer_belladonna_strings': 0.4,
           'when_the_sun_sets_anna_landstrom': 0.6, 'the_forgotten_memories_luella_gren': 0.45,
           'irene_kevin_dailey': 0.3, 'redeemed_blue_saga': 0.4, 'lullaby_before_christmas_franz_gordon': 0.5,
           'with_the_dawn_megan_wofford': 0.55, 'a_heart_full_of_spring_franz_gordon': 0.55,
           'peaceful_melody_megan_wofford': 0.6, 'all_exits_closed_guy_copeland': 0.35}
# slug -> level trim (dB). The owner's new tracks measured in W/mix/sfx_review.md: Impossible Theory -12 LUFS with
# 1404 clipped samples, Peaceful Melody -11 LUFS / 218 clipped: down; the sub drones read quiet: up
GAIN = {'turning_stones_stefan_ekstrom': 4.5, 'are_you_alone_victor_lundberg': 2.0, 'dark_forebodings_ethan_sloan': 2.5,
        'escalation_jon_bjork': 3.0, 'irene_kevin_dailey': 1.0, 'the_haunted_luella_gren': 0.5,
        'don_t_look_belladonna_strings': 2.5, 'impossible_theory_rachel_sandy': -3.0, 'i_m_the_villain_dream_cave': -1.0,
        'peaceful_melody_megan_wofford': -6.0, 'redeemed_blue_saga': -1.0, 'with_the_dawn_megan_wofford': -1.5,
        'a_heart_full_of_spring_franz_gordon': -1.0, 'throbbing_anxiety_dream_cave': -1.0,
        'can_they_see_us_experia': 1.0, 'all_exits_closed_guy_copeland': -1.0,
        # first mix: the tension curve dipped in rule 3 (lullaby -22.8, fake Dad -21.1 LU in speech) under rule 2
        'sleep_forever_luella_gren': 3.0, 'come_closer_belladonna_strings': 3.5}

# ---------------------------------------------------------------------------------------------------- intensity
INTENSITY = [
    # cold open: strong, steps back under the catchphrase, the mystery line
    ('If the ice cream truck plays its song', 0.62), ("And if Mom knocks", 0.7), ("Who's cold? Who wants", 0.5),
    ("That's Mister Shiver", 0.62), ('That was the problem', 0.72),
    # setup (the calmest stretch) and 1958
    ('Larkfield. Minus thirty-one', 0.25), ("Mom's on night shift", 0.22), ('My sister Lina is six', 0.22),
    ('Every morning at six', 0.25), ('In 1958, twelve-year-old', 0.4), ('Just one red mitten', 0.5),
    ('Walter never told anyone', 0.42), ('This morning, no scrape', 0.45), ('The plow pulled away', 0.5),
    # rule 1: the song coming street by street
    ('Rule number one', 0.5), ('Eleven-oh-two', 0.35), ('Far away... a chime', 0.4), ('Maple. Cedar. Closer', 0.5),
    ('I close every curtain', 0.45), ('A hand lifts. Slowly', 0.55), ('And a small cloud of breath', 0.62),
    ('Old people like it cold', 0.4), ('Lina sneaks back', 0.48),
    # the drive-by
    ('The truck glides down Birch Lane', 0.55), ('He leans out. Bald', 0.6), ('He looks across at Kessler', 0.62),
    ('The streetlight flickers', 0.72), ('The song stops. Right outside', 0.2), ('And that smile breathes', 0.6),
    ('Stop. His song is playing', 0.3),
    # rule 2 and the couch
    ('Rule number two', 0.42), ("I look across at Kessler's dark window", 0.4), ('On the doormat', 0.45),
    ("I don't open the door", 0.42), ('Five minutes later', 0.5), ('I check every lock', 0.5),
    ('When I come back, the kitchen window', 0.58), ("Lina's on the couch", 0.68), ('I slap it', 0.75),
    ('It was inside. Brought in', 0.6), ('The furnace stops', 0.55), ('In the black TV screen', 0.6),
    ('I spin around', 0.75), ('I yank the curtain shut', 0.55),
    # rule 3, the lullaby, the fake Dad
    ('Rule number three', 0.45), ('Frost creeps across the windows', 0.5), ('Coats. Hats. Two pairs', 0.35),
    ('The song comes back. Softer', 0.3), ('Dad said if we needed a grown-up', 0.4), ('The radio crackles', 0.55),
    ('I almost go', 0.5), ('Lina grabs my coat', 0.45), ('Then keep her warm, kiddo', 0.62),
    ('Pink light sweeps the curtain', 0.7), ('Then an orange light sweeps', 0.45),
    ('You just told me not to go', 0.6), ('Told you what', 0.8), ('Static. Bells', 0.85), ('The orange light fades', 0.6),
    ("The pink one doesn't", 0.7),
    # rule 4, the window, the transformation, the chase
    ('Rule number four', 0.55), ('Two-ten. Minus thirty-eight', 0.4), ('I wake up. The blanket', 0.55),
    ('The front door is swinging open', 0.65), ('Lina is walking toward the pink window', 0.7), ('I run. Knee-deep', 0.8),
    ('The serving window slides open', 0.7), ('Mister Shiver leans down', 0.78), ('An inch from his fingers', 0.85),
    ('I step back. My boot', 0.6), ('He keeps smiling. Keeps waving', 0.55), ('And the smile keeps going', 0.65),
    ('His jaw drops', 0.85), ('Behind him, the striped uniform', 0.9), ('And the song keeps playing', 0.6),
    ('He pours out of the window', 0.9), ('I rip my foot out', 0.92), ('He scuttles along our fence', 0.95),
    ('And drops. Right in front', 0.98), ('I duck under him', 0.9), ('One leg plucks', 0.55), ('I grab the radio', 0.5),
    ('Her fingertips are white', 0.3), ('Then she shivers. Hard', 0.3),
    # rule 5 and rule 6
    ('Rule number five', 0.55), ('Pounding on the door', 0.7), ('No cloud. Not a wisp', 0.75), ('Breathe, Mom', 0.6),
    ('Slowly, a face slides up', 0.85), ('The doorknob grows frost', 0.7),
    ('Rule number six', 0.65), ('The house is as cold as the street', 0.6), ('Click. Click. Click', 0.72),
    ('The hallway hatch drops open', 0.92), ('We dive into the bathroom', 0.85), ('Under the door, a needle-thin', 0.8),
    ('I jam the towel', 0.9), ('The clicking stops', 0.4),
    # the twist
    ('Then the song moves', 0.45), ('The truck has rolled across', 0.5), ('His door opens', 0.55),
    ('Walter! Look who', 0.65), ("The town never shoveled", 0.55), ('Every night, he broke', 0.6),
    ("Whoever's coldest... was across", 0.85), ('Rule number seven', 0.6), ('Sixty-eight years', 0.5),
    ('Because everybody inside', 0.75), ('Mr. Kessler is halfway', 0.8),
    # the climax
    ('I grab the radio. No bells', 0.6), ('Two minutes out', 0.72), ('Every layer. The big blanket', 0.82),
    ('Legs stab the snow around us', 0.92), ('He swings around, jaw down', 0.98), ('I lock my arm', 0.9),
    ('We pull Mr. Kessler into his doorway', 0.75), ('From the window, a little boy', 0.85), ('Lina holds on tighter', 0.7),
    ('And the old man starts to shiver', 0.62), ('The song reaches the empty beat', 0.35),
    ("Dad's plow roars", 0.72), ('Porch lights click on', 0.65), ('Cold. Alone. He needs both', 0.6),
    ('The song falls apart', 0.5), ('The truck glides into the white', 0.35), ("Lina's mitten drops", 0.3),
    # resolution, stinger, outro
    ('Mr. Kessler whispers', 0.25), ('Paramedics said twenty more', 0.3), ('In the morning, Dad, Lina', 0.3),
    ('Sixty-eight years I taped', 0.32), ('Two nights later', 0.45), ('The truck slows at a house', 0.55),
    ("That's why I wrote one more", 0.35), ('Rule number eight', 0.42), ("There's no Mister Shiver", 0.3),
    ("Like if you'd have crossed", 0.38), ('Next time... if a snowman', 0.45),
]

# the bed thickens rule by rule (AUDIO_SPEC: Q2 the calmest, the last part the loudest): (from, to, + intensity)
ARC = [('Rule number two', 'Rule number three', 0.02), ('Rule number three', 'Rule number four', 0.04),
       ('Rule number four', 'Rule number five', 0.06), ('Rule number five', 'Rule number six', 0.08),
       ('Rule number six', 'Then the song moves', 0.1), ('Rule number seven', "Dad's plow roars", 0.1)]

# ---------------------------------------------------------------------------------------------------- events
# (anchor, type, level, len, extra). Hits: 'boost' (>= 3.5 -> +10 LU momentary over the voice, >= 2.5 -> +9, else
# +8) only on the biggest scares. Silences sit under the line before the scare and end on it ('level' >= 0.95: a TRUE
# silence that also mutes the SFX events). 'nosnap' keeps a word's time when the picture has a hit nearby.
EVENTS = [
    # cold open
    ("And her breath doesn't show -0.1", 'sub_drop', 0.45, None),
    ('That was the problem -1.4', 'silence', 0.8, 1.3), ('That was the problem', 'sub_drop', 0.6, None),
    # setup
    ('Just one red mitten', 'sub_drop', 0.4, None),
    ('end:three slow notes -2.0', 'silence', 0.9, 2.0),                   # the notes in the static alone
    # rule 1
    ('Rule number one -0.1', 'rule', 0.7, None, {'nosnap': True}),
    ('From the inside', 'hit', 0.6, None),                                 # the breath on Kessler's glass (a fair clue)
    ('The truck glides down Birch Lane', 'swell', 0.45, 4.0),
    ('For one flicker, his face is long#white +0.1', 'silence', 0.75, 1.25),   # the dip under 'white. Red eyes.', up to the hit
    # sound fix (critic B1): the boosted hits land in the voice edit's SCARE BEATS just after their words (the 0.40-0.45 s
    # gaps left for them), never on the words; the reveal frame keeps the picture's own sound, the riser peaks on the hit
    ('end:his face is long and white. Red eyes', 'riser', 0.55, 2.5),
    ('end:his face is long and white. Red eyes', 'hit', 0.85, None, {'boost': 3.0, 'nosnap': True}),   # glimpse 1: after "Red eyes."
    ('The song stops. Right outside#stops', 'silence', 0.95, 1.6),        # the song stops dead: only the idle
    ('And that smile breathes', 'sub_drop', 0.6, None),
    # rule 2
    ('Rule number two -0.1', 'rule', 0.7, None, {'nosnap': True}),
    ("Then... a soft tap -0.9", 'silence', 0.8, 1.0),
    ('Five minutes later', 'sub_drop', 0.4, None),
    ("Lina's step-stool under it", 'riser', 0.55, 3.0),
    ('end:I slap it', 'hit', 0.8, None, {'boost': 2.5, 'nosnap': True}),   # after "I slap it." (the slap itself is the picture's foley)
    ('Click. -0.9', 'silence', 0.9, 1.0),                                 # the furnace relay alone (sound fix: 0.95 muted the relay itself)
    ('The furnace stops', 'sub_drop', 0.6, None),
    ('end:Every light in the house goes out', 'hit', 0.9, None, {'boost': 2.5, 'nosnap': True}),   # just after 'out.'   # the power dies (picture power_cut)
    ('in the curtain crack... a long white skull#skull -0.2', 'silence', 0.8, 1.4),   # under 'skull. Red eyes.', up to the hit
    ('end:a long white skull. Red eyes', 'riser', 0.45, 3.0),
    ('end:a long white skull. Red eyes', 'hit', 1.0, None, {'boost': 3.5, 'nosnap': True}),   # glimpse 2: after "Red eyes."
    # ('I spin around', 'stinger'): dropped (sound fix: 0.45 s after the moved glimpse-2 hit it doubled it)
    # rule 3, the fake Dad, twist 1
    ('Rule number three -0.1', 'rule', 0.7, None, {'nosnap': True}),
    ('Frost creeps across the windows', 'swell', 0.45, 5.0),
    ('The radio crackles -0.8', 'silence', 0.8, 0.9),
    ('Silence. -0.3', 'silence', 0.95, 1.6),
    ('Sleep is warm', 'sub_drop', 0.55, None),
    ('Long, jointed legs', 'silence', 0.8, 1.4),                          # minor 14: the dip before glimpse 3
    ('end:Long, jointed legs', 'hit', 0.8, None, {'boost': 2.5, 'nosnap': True}),     # glimpse 3: after "Long, jointed legs."
    ('Told you what', 'hit', 0.65, None),                                  # twist 1 (a sting on the line, no boost)
    ("end:Dad, there's a truck outsi +0.05", 'hit', 0.9, None, {'boost': 3.0, 'nosnap': True}),   # the bells cut Adam off: on the cut, before "Static."
    ("The pink one doesn't", 'sub_drop', 0.6, None),
    # rule 4, the window, the transformation
    ('Rule number four -0.1', 'rule', 0.75, None, {'nosnap': True}),
    ('I wake up. The blanket beside me is cold', 'sub_drop', 0.5, None),
    ('The front door is swinging open', 'hit', 0.7, None),
    ('end:An inch from his fingers, I yank her into my arms', 'riser', 0.65, 4.0),
    ('end:An inch from his fingers, I yank her into my arms', 'hit', 0.85, None, {'boost': 2.5, 'nosnap': True}),   # after "into my arms."
    ('Frozen to the snow', 'sub_drop', 0.55, None),
    ('Like a mask made of bone#bone +0.35', 'riser', 0.6, 6.0),
    ('Like a mask made of bone#bone +0.35', 'hit', 0.85, None, {'boost': 2.5, 'nosnap': True}),
    ('and come back red#red', 'hit', 0.8, None),
    ('His jaw drops#drops -0.15', 'silence', 0.8, 0.6, {'keep_show': True}),   # minor 2: the chime plays on through it
    ('end:His jaw drops', 'hit', 1.0, None, {'boost': 3.5, 'nosnap': True}),   # just after 'drops.'
    ("end:A long brown leg punches out, jointed like a spider's", 'hit', 0.95, None, {'boost': 3.0, 'nosnap': True}),
    ('He pours out of the window', 'braam', 0.8, None),
    # the chase
    ('I rip my foot out', 'pulse_on', 0.8, None),
    ('One spears my coat', 'hit', 0.75, None),
    ('And drops#drops -0.85', 'silence', 0.95, 0.55),                    # minor 14: a true drop-out (the scuttle stops); it
                                                                          # ends 0.65 s before the hit (its 0.5 s release)
    ('end:Up onto our roof. And drops', 'hit', 0.95, None, {'boost': 3.0, 'nosnap': True}),   # after "And drops."
    ('and slam the door', 'hit', 0.8, None),
    ('One leg plucks', 'pulse_off', 0.5, None),
    ('Saving her a place', 'sub_drop', 0.45, None),
    ('Static. And bells', 'stinger', 0.55, None),
    # rule 5
    ('Rule number five -0.1', 'rule', 0.75, None, {'nosnap': True}),
    ('No cloud. Not a wisp -0.7', 'silence', 0.8, 0.8), ('No cloud. Not a wisp#cloud +0.55', 'hit', 0.85, None, {'boost': 2.5, 'nosnap': True}),   # just after 'No cloud.'
    ('Let me in, baby -1.4', 'silence', 0.95, 1.4),
    ('end:Long. White. Red eyes', 'riser', 0.6, 4.5),                     # the face slides up the glass ...
    ('end:Long. White. Red eyes', 'hit', 1.0, None, {'boost': 3.5, 'nosnap': True}),   # ... pressed to it: after "Red eyes."
    ('The doorknob grows frost', 'sub_drop', 0.55, None),
    # rule 6
    ('Rule number six -0.1', 'rule', 0.8, None, {'nosnap': True}),
    ('Click. Click. Click -0.8', 'silence', 0.8, 0.9),
    ('The hallway hatch drops open', 'silence', 0.8, 1.45),               # minor 14: the dip before the hatch
    ('end:The hallway hatch drops open', 'hit', 1.0, None, {'boost': 3.5, 'nosnap': True}),   # after "drops open."
    ('end:A leg reaches between us', 'hit', 0.85, None, {'boost': 2.5, 'nosnap': True}),
    ("end:leg tip slides in. Feeling for Lina's sock", 'riser', 0.55, 3.0),
    ("end:leg tip slides in. Feeling for Lina's sock", 'hit', 0.8, None, {'boost': 2.5, 'nosnap': True}),   # after "...Lina's sock." (0.28 s)
    ('end:I jam the towel down on it. Hard', 'hit', 0.7, None, {'nosnap': True}),   # after "Hard.": Adam's blow, not a scare
    # (sound fix: no longer boosted: 2.3 s after the leg-tip scare, in a 0.17 s gap it could not reach +6 LU)
    ('The clicking stops', 'silence', 0.8, 1.5),
    # the twist
    ("To Kessler's door +0.1", 'silence', 0.8, 0.95),
    ("end:To Kessler's door", 'hit', 0.9, None, {'boost': 3.0, 'nosnap': True}),       # the big twist: the truck at HIS door
    ('Not shivering. Smiling', 'hit', 0.65, None),
    ('end:And nobody checked', 'sub_drop', 0.6, None),          # after the line (it sat on "And nobody checked.")
    ("Whoever's coldest... was across -1.0", 'silence', 0.85, 1.1),
    ("end:Whoever's coldest... was across the street", 'hit', 0.95, None, {'boost': 3.0, 'nosnap': True}),   # into the 0.85 s hold
    ('Rule number seven -0.1', 'rule', 0.8, None, {'nosnap': True}),
    ("When it's my turn", 'swell', 0.5, 5.0),
    ('Because everybody inside', 'hit', 0.8, None),
    # the climax
    ('Every layer. The big blanket', 'pulse_on', 0.85, None),
    ('One hooks the blanket#pulls', 'hit', 0.8, None),
    ('end:legs arched over us like a cage', 'hit', 0.95, None, {'boost': 3.0, 'nosnap': True}),   # the cage, after its line
    ('Inside, children. Rule seven', 'sub_drop', 0.6, None),
    ('We pull Mr. Kessler', 'pulse_off', 0.5, None),
    ('And the old man starts to shiver', 'swell', 0.55, 4.0),
    ("Dad's plow roars", 'swell', 0.8, 4.0),
    ("His jaw gapes for the last note... and can't close#and -0.3", 'silence', 0.6, 1.4, {'keep_show': True}),   # minor 14: a dip (the hung chime stays)
    ("end:His jaw gapes for the last note... and can't close", 'hit', 0.85, None, {'boost': 2.5, 'nosnap': True}),   # after "can't close.": it rolls into the plow's roar
    ('end:The song falls apart', 'hit', 0.8, None, {'boost': 2.5, 'nosnap': True}),     # his defeat
    ('The red one stays', 'sub_drop', 0.35, None),
    # stinger and the teaser
    ('The truck slows at a house', 'hit', 0.7, None),
    ('Rule number eight -0.1', 'rule', 0.55, None, {'nosnap': True}),
    ('Next time... if a snowman', 'sub_drop', 0.45, None),
]

# ---------------------------------------------------------------------------------------------------- identity
# HIS CHIME (audio/chime_ice.py; score.py 'chime' events). (anchor, type, level, len, extra): 'version', 'until'
# (an anchor: sets len), stop ('fade' | 'cut' | 'drag'), fade (fade-in s), loops, anchors [(beat, anchor)] (the tune
# bends so those beats land on the words), 'gap_at' (an anchor: the event starts so that the version's gap (or the
# warm version's played last note) lands there), 'hang_until' (climax: the hang lasts until that anchor), wind,
# amount, short.
IDENTITY = [
    # 0:15 the cold open: a bright burst under the catchphrase, from the window's speaker
    ("Who's cold? Who wants -0.6", 'jingle', 0.55, None, dict(version='burst', until="That's Mister Shiver -0.2",
                                                             stop='fade', fade=0.05)),
    # 1:33 three slow notes under the radio static as the plow leaves, straight into the rule 1 card
    ('end:three slow notes -1.9', 'jingle', 0.5, None, dict(version='three', until='Rule number one +1.2', stop='fade',
                                                          fade=0.02)),
    # 1:45 far away, coming closer street by street (one pass at its own too-slow 72 bpm: its gap falls just after
    # "...a gap where the last note should be.")
    ('Far away... a chime -0.2', 'jingle', 0.5, None, dict(version='closer', loops=1,
                                                          until='Far away... a chime +20.0', stop='fade', fade=0.5)),
    # then near (the speaker, quieter) while the curtains close and Kessler's glass fogs ...
    ('Far away... a chime +19.8', 'jingle', 0.32, None,
     dict(version='outside', loops=2, until='The truck glides down Birch Lane +1.0', stop='fade', fade=1.0)),
    # 2:15 ... and right outside: full, the speaker horn, until it stops DEAD on "stops"
    ('The truck glides down Birch Lane', 'jingle', 0.45, None,
     dict(version='outside', loops=3, until='The song stops. Right outside#stops', stop='cut', fade=1.0)),
    # 4:20 the lullaby; Lina's eyes droop; it fades when Adam pulls on his boots
    ('The song comes back. Softer', 'jingle', 0.45, None, dict(version='lullaby', loops=2,
                                                              until='The radio crackles -0.3', stop='fade', fade=1.0)),
    # 5:44 M2 (sound fix): "Humming his song.": the tune soft and close, a lullaby only she hears, under L179-L182
    ('Humming his song -0.2', 'jingle', 0.3, None, dict(version='lullaby', loops=1, until='she calls back +0.25',
                                                        stop='fade', fade=0.6)),
    # 5:45 the serving window: cheerful and undistorted through the whole transformation, until he pours out
    ('The serving window slides open +0.3', 'jingle', 0.5, None,
     dict(version='outside', loops=5, until='end:Head first. Legs last +0.6', stop='fade', fade=0.4)),
    # 8:45 the song moves to Kessler's: warped, the night at its worst; dragged down as Kessler steps out
    ('Then the song moves', 'jingle', 0.45, None, dict(version='warped', amount=0.6, loops=2,
                                                      until='Rule number seven -0.6', stop='drag', fade=0.6)),
    # 11:00 the climax: the tune plays, reaches the empty beat on "empty", HANGS until "The song falls apart." and
    # falls apart there
    ('The song reaches the empty beat#empty', 'jingle', 0.65, None,
     dict(version='climax', gap_at='The song reaches the empty beat#empty', hang_until='The song falls apart',
          fall=3.0, stop='fade')),
    # 11:45 the stinger across town: the last phrase, far, ending on the note that isn't there
    ('Two nights later#chime', 'jingle', 0.45, None, dict(version='stinger', until='end:The truck slows at a house +2.5',
                                                        stop='fade')),
    # the morning: the motif redeemed, the last note finally PLAYED after "First time anyone knocked on mine."
    ('Lina brings him cocoa', 'jingle', 0.4, None, dict(version='warm', gap_at='end:anyone knocked on mine -0.3',
                                                       until='Two nights later +0.8', stop='fade', fade=1.5)),
    # the SHORT outro: bars 5-8 and the resolution, warm
    ("Like if you'd have crossed the street", 'jingle', 0.4, None,
     dict(version='warm', short=True, until='Next time... if a snowman -0.2', stop='fade', fade=0.8)),
]


# ---------------------------------------------------------------------------------------------------- resolve
_A = re.compile(r'^([se])(\d+)([+-][0-9.]+)?$')
_WA = re.compile(r'^w(\d+):([^+\-]+)([+-][0-9.]+)?$')
_OFF = re.compile(r'^(.*?)\s([+-][0-9.]+)$')
_WORDS = None
_WARNED = set()


def _norm(w):
    return re.sub(r"[^a-z0-9']", '', str(w).lower().replace('mr.', 'mister'))


def _ntext(s):
    s = str(s).lower().replace('mr.', 'mister').replace('’', "'")
    return re.sub(r'\s+', ' ', re.sub(r"[^a-z0-9' ]", ' ', s)).strip()


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


def _text(l):
    return l.get('en') or l.get('text') or ''


_CAT = {}


def _concat(lines):
    """One normalised string of every line's text, and the line index of each character."""
    k = id(lines)
    if k not in _CAT:
        s, owner = [], []
        for j, l in enumerate(lines):
            t = _ntext(_text(l)) + ' '
            s.append(t); owner += [j] * len(t)
        _CAT.clear(); _CAT[k] = (''.join(s), owner)
    return _CAT[k]


def _find(phrase, lines):
    """(first line index, last line index, char span inside the joined text) of a script phrase, or None."""
    txt, owner = _concat(lines)
    p = _ntext(phrase)
    if not p:
        return None
    i = txt.find(p)
    if i < 0:                                            # a TTS slip or a re-cut: try the first 4 words, then 2
        w = p.split()
        for k in (4, 2):
            if len(w) > k:
                i = txt.find(' '.join(w[:k]))
                if i >= 0:
                    p = ' '.join(w[:k]); break
    if i < 0:
        return None
    return owner[i], owner[min(len(owner) - 1, i + len(p) - 1)], (i, i + len(p))


def line_index(anchor, lines):
    """The line index an anchor names (its first line), or None."""
    a = str(anchor)
    m = _A.match(a)
    if m:
        return int(m.group(2))
    a = re.sub(r'^end:', '', _OFF.sub(r'\1', a)).split('#')[0]
    f = _find(a, lines)
    return f[0] if f else None


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
    if m:
        l = _line(int(m.group(2)), lines)
        t = float(l['t'] if m.group(1) == 's' else l['end'])
        return t + (float(m.group(3)) if m.group(3) else 0.0)
    off = 0.0
    mo = _OFF.match(a)
    if mo:
        a, off = mo.group(1).strip(), float(mo.group(2))
    end = a.startswith('end:')
    if end:
        a = a[4:]
    word = None
    if '#' in a:
        a, word = a.split('#', 1)
    f = _find(a, lines)
    if f is None:
        raise KeyError(f'anchor not found in the timeline: {anchor!r}')
    j0, j1, _ = f
    if word:                                            # the word's onset inside the line that holds the phrase
        want = _norm(word)
        l = lines[j0]                                    # the phrase's line, else its last line, else the next 4
        for jj in [j0, j1] + list(range(j1 + 1, min(len(lines), j1 + 5))):
            if any(_norm(x).startswith(want) for x in _text(lines[jj]).split()):
                l = lines[jj]; break
        cand = [t for w, t in _words() if l['t'] - 0.35 <= t <= l['end'] + 0.05 and w.startswith(want)]
        if cand:
            return cand[0] + off
        tx = _ntext(_text(l)); k = tx.find(_ntext(word))            # no word timings: by character position
        frac = (k / max(1, len(tx))) if k >= 0 else 0.0
        return float(l['t']) + frac * (float(l['end']) - float(l['t'])) + off
    l = lines[j1] if end else lines[j0]
    return float(l['end'] if end else l['t']) + off


def _try(anchor, lines, what=''):
    try:
        return resolve(anchor, lines)
    except (KeyError, ValueError, StopIteration, IndexError) as e:
        if anchor not in _WARNED:
            _WARNED.add(anchor)
            print(f'[music_plan] WARNING: {what} anchor {anchor!r} not found ({repr(e)[:60]}): row skipped', flush=True)
        return None


def load_lines(timeline_path=None):
    tl = json.load(open(timeline_path or TIMELINE))
    return tl['lines'], float(tl.get('duration_en') or max(l['end'] for l in tl['lines']))


def track_map(lines):
    out = []
    for a, s, o, _w in TRACK_MAP:
        t = _try(a, lines, 'track')
        if t is None:
            continue
        x = {'t0': round(t, 3), 'slug': s, 'off': float(o)}
        if s in FLATTEN:
            x['flatten'] = FLATTEN[s]
        if GAIN.get(s):
            x['gain_db'] = GAIN[s]
        out.append(x)
    out.sort(key=lambda x: x['t0'])
    if out:
        out[0]['t0'] = 0.0                               # the first section starts the film
    return out


def intensity(lines, duration=None):
    arc = [(x, y, d) for x, y, d in ((_try(a, lines, 'arc'), _try(b, lines, 'arc'), d) for a, b, d in ARC)
           if x is not None and y is not None]
    pts = []
    for a, v in INTENSITY:
        t = _try(a, lines, 'intensity')
        if t is None:
            continue
        pts.append((round(t, 3), float(min(1.0, v + sum(d for x, y, d in arc if x <= t < y)))))
    pts.sort()
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
        t = _try(a, lines, 'event')
        if t is None:
            continue
        e = {'t': round(t, 3), 'type': ty, 'level': lv}
        if ln is not None:
            e['len'] = ln
        if len(row) > 4 and row[4]:
            e.update(row[4])
        ev.append(e)
    return sorted(ev, key=lambda e: e['t'])


def identity_events(lines):
    """HIS CHIME's versions (score.py 'chime'). 'until' sets len; 'anchors' [(beat, anchor)] become film seconds;
    'gap_at' moves the start so the version's gap (warm: the played last note) lands on that anchor; 'hang_until'
    sets the climax's hang."""
    ev = []
    sys.path.insert(0, HERE)
    for a, ty, lv, ln, extra in IDENTITY:
        t = _try(a, lines, 'identity')
        if t is None:
            continue
        x = dict(extra)
        if x.get('gap_at'):
            g = _try(x.pop('gap_at'), lines, 'identity gap')
            if g is not None:
                try:
                    import chime_ice as CH
                    t = g - CH.gap_time(x.get('version'), loops=int(x.get('loops') or 1), short=bool(x.get('short')))
                except Exception as e:
                    print(f'[music_plan] WARNING: chime gap time failed ({repr(e)[:60]})', flush=True)
        if x.get('hang_until'):
            hu = _try(x.pop('hang_until'), lines, 'identity hang')
            g = _try(a, lines, 'identity')
            if hu is not None and g is not None:
                x['hang'] = round(max(1.5, hu - g), 3)
        e = {'t': round(t, 3), 'type': ty, 'level': lv}
        if 'until' in x:
            u = _try(x.pop('until'), lines, 'identity until')
            if u is not None:
                ln = max(0.5, u - t)
        if x.get('version') == 'climax' and 'hang' in x and ln is None:
            import chime_ice as CH
            ln = CH.gap_time('climax') + float(x['hang']) + float(x.get('fall', 3.0)) + 1.5
        if x.get('anchors'):
            an = [(float(b), _try(s, lines, 'identity beat')) for b, s in x['anchors']]
            x['anchors'] = [[b, round(s, 3)] for b, s in an if s is not None]
            if len(x['anchors']) < 2:
                x.pop('anchors')
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
    if idt:
        duration = max(duration, max(e['t'] + float(e.get('len') or 0) for e in idt) + 0.6)
    return {'duration': round(duration, 2), 'intensity': intensity(lines, duration),
            'events': sorted(events(lines) + idt, key=lambda e: e['t']),
            'track_map': track_map(lines)}


def table(lines):
    out = []
    tm = track_map(lines)
    why = {(s, o): w for _a, s, o, w in TRACK_MAP}
    for k, x in enumerate(tm):
        t1 = tm[k + 1]['t0'] if k + 1 < len(tm) else max(l['end'] for l in lines)
        out.append(f"{x['t0']:7.2f}-{t1:7.2f}  {x['slug']:40s} from {x['off']:5.1f}s  {why.get((x['slug'], x['off']), '')}")
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
