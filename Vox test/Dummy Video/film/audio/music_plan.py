"""music_plan.py: the dummy film's music map ("If Your Grandpa's Ventriloquist Dummy Tells You A Joke... DON'T LAUGH"),
built the police film's way (film.py INTENSITY / polish_cues / score.py), anchored to the script lines and words.

Two things live here:
1. The tension arc (the police way): one dark Epidemic track section per film section (sections start at the rule
   cards; the delivery, police and mirror sets, varispeeded to D / A in score.TRACKS), gain automation following an
   intensity curve (the cold open strong, the second quarter the calmest, climax in the last minute), swells into the
   reveals, risers, true music drop-outs under the line before a scare, hits and stingers on the reveals, a rule-card
   sting on every "Rule number N", the heartbeat pulse in the chases, the end cadence.
2. The film's own sound (IDENTITY, score.py stem `show`): the cheerful 1970s kids-show theme ("Saturday Morning with
   Walter Kemp" = the owner's Balloon Twister) heard from Grandpa's old TV (band-limited, wow, hiss) when the tape
   plays, the same tune rotted (slowed 9 semitones, detuned, seasick) as Mister Winks's theme when he is near, the
   1962 first show (Ye Olde Piano Roll on a kinescope), and the music-box lullaby for Grandpa's love (the three
   squeezes, "Kiddo", the museum glass).

Public API
    TRACK_MAP        [(anchor, slug, off, why)]   one dark track section per film section; off = seconds into the
                     varispeed track (score.TRACKS shift), chosen from the catalogue's 2 s loudness curves
    FLATTEN, GAIN    per-track dynamics flattening and level trim (dB) passed to score.py in the track map
    INTENSITY        [(anchor, value)]            0..1 tension curve (score.py: bed level, layer thresholds)
    EVENTS           [(anchor, type, level, len)] the tension events (ARCHITECTURE.md music_cues types)
    IDENTITY         [(anchor, type, level, len, extra)]   the show / winks / motif events (extra: score.py keys,
                     anchors inside extra ('warp_at') are resolved to seconds after the event)
    resolve(anchor, lines) -> t   'sN' / 'eN' = start / end of line N, 'wN:word' = that word's onset inside line N
                                  (the aligner's words, W/align/asr_cache.json), each with an optional +/-offset,
                                  or a number (film seconds)
    track_map(lines), intensity(lines, duration), events(lines), identity_events(lines),
    music_cues(lines, duration) -> dict (events = EVENTS + IDENTITY; adds 'track_map')
    load_lines(timeline_path=None) -> (lines, duration)

How it reaches the mix: film.py writes W/cues/music_cues.json from the picture (intensity curve, hits on the reveal
cuts, silences, swells, rule stings) but no track_map. mix.py (--plan auto, the default) adds track_map(lines) from
this module, and IDENTITY when the sheet has no 'show' / 'winks' events of its own (the film's sound must be there
whatever the picture cues say); a sheet with no events at all also gets EVENTS and INTENSITY. Windowed mixes (--t0)
shift the map with the window. film.py may instead write 'track_map': MP.track_map(F.L) and
MP.identity_events(F.L) itself (mix.py then leaves them alone).

CLI: python3 music_plan.py [--timeline T] [--out W/cues/music_cues_plan.json] [--table]   (--table prints the map)
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.normpath(os.path.join(HERE, '..', '_work'))
TIMELINE = os.path.join(W, 'align', 'timeline.json')
WORDS = os.path.join(W, 'align', 'asr_cache.json')

# ---------------------------------------------------------------------------------------------------- arrangement
# section start, track, offset (s, in the varispeed track), why. Tracks: score.TRACKS (shifts there).
TRACK_MAP = [
    ('s0', 'are_you_alone_victor_lundberg', 63.0,
     'cold open ("don\'t laugh... never tell it goodnight", two seats, Grandpa, "we buried him"): the dark D sub drone '
     'swelling into its one spike (93.5-100 s of the track) on "Last night, I found out why his lips never moved"'),
    ('s12', 'when_the_sun_sets_anna_landstrom', 0.0,
     'Walter Kemp, Saturday mornings, Mister Winks, Owen\'s wink, the tuck-in: a quiet warm pad (C# -> D major) under '
     'the show theme on the old TV and the music box; the calm before the hospital'),
    ('s28', 'haunted_mind_etienne_roussel', 44.0,
     'the hospital (the heart monitor, Winks on his lap, "It wasn\'t me. It was never me."): the slow mid-register '
     'build peaking (its 74 s) on the whisper'),
    ('s41', 'turning_stones_stefan_ekstrom', 0.0,
     'the drive, the house, the black leather case, the envelope, "one of the seven was a lie": a pure dark drone'),
    ('s52', 'the_logic_of_tyrants_hampus_naeselius', 62.0,
     'rule 1 (the empty case, the warm velvet, the spoon, the clinks, Winks in Grandpa\'s chair, two sugars): from '
     'the track\'s quiet dip (62 s), a low pulse building to "like he\'s lived here a lot longer than any of us"'),
    ('s77', 'from_hell_christoffer_moe_ditlevsen', 4.0,
     'rule 2 (the voices upstairs, "See you in the morning, kiddo", the head turned all the way, the slow clack): the '
     'police set\'s unpulsed, mid-register dread (Bb -> A minor, centroid 1.5 kHz: it reads on a phone, where the sub '
     'drones vanish; tests: the police drone left the music present 32 % of this window), quiet at first, building '
     'from its 46 s to the clack'),
    ('s115', 'a_massive_mist_ethan_sloan', 0.0,
     'rule 3 (the joke, the snort, the clack, the TV turns on, the laughter, he stands, the lamp): a very low drone '
     '(centroid 112 Hz) that leaves the whole mid band to the show theme on the TV and the studio audience'),
    ('s148', 'come_closer_belladonna_strings', 0.0,
     'rule 4 (3 AM, the flashlight on the stairs, the hand in the slot, the warm hand, the squeezes, "Kiddo, it\'s '
     'me"): horror strings (D# -> D minor), the section\'s peak around the hand, a dip into the rule 5 card'),
    ('s190', 'don_t_look_belladonna_strings', 0.0,
     'rule 5 (Mom\'s voice from the bookcase, the jaw going up and down, the TV, young Grandpa\'s lips): horror strings '
     'until the tape stops'),
    ('w209:stops+0.4', 'irene_kevin_dailey', 0.0,
     'the twist (the dummy on the tape looks into the camera and cries "My name is Walter Kemp"; the audience laughs; '
     'sixty years; the only grandpa I ever had): switches inside the drop-out where the tape stops; starts near silent '
     'and builds slowly'),
    ('s234', 'code_of_violence_dian_shuai', 60.0,
     'rule 6 (Owen in the armchair with the dummy on his knee, Mom screams, "Pull, and his hand comes with me", '
     '"Say goodnight, Mister Winks", "Goodnight, Owen.", the lamp out): dark pulsing D-minor bass at its loudest '
     'around the scream'),
    ('s272', 'tefu_sayuri_hayashi_egnell', 0.0,
     'false relief ("It worked! He\'s asleep!", the dummy face down on the rug): the police film\'s D major, quiet'),
    ('s279', 'one_step_away_dian_shuai', 25.0,
     'rule 7 (rules six and seven side by side, the P.S., 1962, "a young one", the eyelids: "Click, click."): the '
     'percussive build to the climax (its loud 86-130 s on film 643-677: the last minute is the loudest, AUDIO_SPEC; '
     'the full-film check had its peak at 631 s with offset 40)'),
    ('s325', 'are_you_alone_victor_lundberg', 67.6,
     'the museum glass, "Wink back", the sting ("The boy who came home with us doesn\'t laugh anymore", two sugars, the '
     'doorway): the opening track again, its spike on "See you in the morning, kiddo."'),
]

# slug -> share of the track's own dynamics evened out (score.FLATTEN 0.3 otherwise)
FLATTEN = {'are_you_alone_victor_lundberg': 0.6, 'haunted_mind_etienne_roussel': 0.55,
           'when_the_sun_sets_anna_landstrom': 0.55, 'irene_kevin_dailey': 0.6, 'come_closer_belladonna_strings': 0.5,
           'the_logic_of_tyrants_hampus_naeselius': 0.45, 'tefu_sayuri_hayashi_egnell': 0.4}
# slug -> level trim (dB) of the track in its sections: sub drones read quiet (a_massive_mist centroid 112 Hz,
# dark_forebodings 174 Hz: the delivery film measured +3 dB needed), the two near-silent pads need lifting
# Full-film checks (film.py's cue sheets, measure_mix.py): music by quarter -17.0 / -14.4 / -14.2 / -14.3 LU rel voice
# with the first gains: the first quarter was the quietest (AUDIO_SPEC: Q2 the calmest, the cold open strong), so the
# Q1 tracks come up 2.5-3 dB and the Q2 tracks go down 1.5 dB.
# Final mix (music by quarter -17.3 / -17.8 / -16.3 / -14.2 LU rel voice with the full plan): rules 4 and 5 sat at -18.6
# and -18.0 while the job asks for the bed "thicker and louder by rule 5": come_closer +2, don't_look +3.
GAIN = {'come_closer_belladonna_strings': 2.0, 'don_t_look_belladonna_strings': 3.0,   # (and irene 2 -> 0.5: the
        # twist section measured the loudest music of the film, -11 LU, its swell 5 LU over the line)
        'a_massive_mist_ethan_sloan': 1.5, 'dark_forebodings_ethan_sloan': 3.0, 'from_hell_christoffer_moe_ditlevsen': -2.5,
        'when_the_sun_sets_anna_landstrom': 7.0,
        'haunted_mind_etienne_roussel': 4.0, 'are_you_alone_victor_lundberg': 5.0, 'irene_kevin_dailey': 0.5,
        'turning_stones_stefan_ekstrom': 4.5, 'the_logic_of_tyrants_hampus_naeselius': -1.0,
        'tefu_sayuri_hayashi_egnell': -1.0}

# ---------------------------------------------------------------------------------------------------- intensity
INTENSITY = [
    # cold open
    ('s0', 0.6), ('s2', 0.66), ('s3', 0.52), ('s6', 0.6), ('s7', 0.5), ('s10', 0.58), ('s11', 0.72), ('e11', 0.76),
    # Walter, the show, Owen, the habit, the tuck-in
    ('s12', 0.42), ('s14', 0.4), ('s17', 0.44), ('s18', 0.4), ('s23', 0.44), ('s24', 0.5), ('s26', 0.44),
    ('s27', 0.46),
    # the hospital
    ('s28', 0.5), ('s32', 0.58), ('s35', 0.64), ('s36', 0.7), ('s37', 0.78), ('s38', 0.8), ('s39', 0.58),
    # the drive, the house, the case
    ('s41', 0.48), ('s43', 0.52), ('s46', 0.56), ('s48', 0.62), ('s50', 0.7), ('e51', 0.72),
    # rule 1
    ('s52', 0.62), ('s56', 0.42), ('s59', 0.46), ('s60', 0.64), ('s62', 0.6), ('s63', 0.5), ('s64', 0.54),
    ('s67', 0.55), ('s68', 0.62), ('s69', 0.57), ('s71', 0.57), ('s72', 0.63), ('s75', 0.67), ('e76', 0.69),
    # rule 2 (the calm quarter)
    ('s77', 0.5), ('s82', 0.36), ('s83', 0.3), ('s86', 0.38), ('s89', 0.36), ('s91', 0.44), ('s92', 0.5),
    ('s96', 0.4), ('s99', 0.5), ('s103', 0.6), ('s104', 0.52), ('s108', 0.58), ('s109', 0.64), ('s110', 0.68),
    ('s111', 0.74), ('s112', 0.54), ('s113', 0.58), ('e114', 0.56),
    # rule 3 (the joke, the TV, the laughter)
    ('s115', 0.5), ('s118', 0.26), ('s122', 0.3), ('s124', 0.34), ('s127', 0.54), ('s128', 0.58), ('s130', 0.4),
    ('s131', 0.34), ('s132', 0.46), ('s135', 0.46), ('s137', 0.56), ('s140', 0.68), ('s141', 0.6), ('s142', 0.66),
    ('s143', 0.44), ('s144', 0.6), ('s145', 0.58), ('s147', 0.62),
    # rule 4 (the stairs, the hand)
    ('s148', 0.6), ('s150', 0.46), ('s152', 0.4), ('s153', 0.44), ('s156', 0.62), ('s157', 0.74), ('s158', 0.78),
    ('s159', 0.72), ('s161', 0.8), ('s162', 0.62), ('s164', 0.42), ('s168', 0.44), ('s169', 0.56), ('s172', 0.52),
    ('s175', 0.54), ('s179', 0.62), ('s181', 0.72), ('s182', 0.78), ('s184', 0.68), ('s185', 0.76), ('s186', 0.62),
    ('s189', 0.68),
    # rule 5 (the bookcase, the tape, the twist)
    ('s190', 0.64), ('s192', 0.52), ('s193', 0.66), ('s196', 0.76), ('s197', 0.82), ('s198', 0.86), ('s199', 0.68),
    ('s202', 0.6), ('s203', 0.5), ('s204', 0.46), ('s206', 0.56), ('s208', 0.62), ('s209', 0.56), ('s210', 0.66),
    ('s211', 0.6), ('s214', 0.5), ('s218', 0.84), ('s219', 0.76), ('s220', 0.72), ('s221', 0.74), ('s222', 0.66),
    ('s224', 0.76), ('s225', 0.84), ('s226', 0.88), ('s227', 0.68), ('s229', 0.62), ('s232', 0.58), ('s233', 0.52),
    # rule 6 (Owen in the den, the scream, the goodnight, the lamp)
    ('s234', 0.68), ('s242', 0.76), ('s243', 0.72), ('s246', 0.78), ('s247', 0.72), ('s251', 0.82), ('s254', 0.94),
    ('s257', 0.92), ('s260', 0.86), ('s261', 0.8), ('s263', 0.72), ('s264', 0.5), ('s265', 0.4), ('s266', 0.3),
    ('s268', 0.24), ('s269', 0.28), ('s271', 0.12), ('s272', 0.34), ('s273', 0.4), ('s276', 0.48), ('s277', 0.5),
    # rule 7 (the realisation, the P.S., 1962, the eyelids)
    ('s279', 0.64), ('s283', 0.62), ('s284', 0.68), ('s285', 0.74), ('s286', 0.8), ('s287', 0.86), ('s289', 0.9),
    ('s290', 0.68), ('s292', 0.64), ('s293', 0.72), ('s295', 0.78), ('s297', 0.86), ('s298', 0.82), ('s299', 0.68),
    ('s300', 0.68), ('s301', 0.72), ('s305', 0.8), ('s306', 0.76), ('s308', 0.82), ('s309', 0.86), ('s310', 0.9),
    ('s311', 0.88), ('s312', 0.82), ('s314', 0.9), ('s315', 0.94), ('s316', 1.0), ('s317', 0.96), ('s318', 0.92),
    # the ending (the van, the museum, the sting)
    ('s319', 0.68), ('s321', 0.76), ('s322', 0.62), ('s324', 0.66), ('s325', 0.58), ('s326', 0.62), ('s328', 0.68),
    ('s329', 0.74), ('s330', 0.92), ('s331', 0.9), ('s333', 0.94), ('s335', 0.98), ('s336', 1.0), ('s337', 1.0),
    ('e338', 0.96),
]

# ---------------------------------------------------------------------------------------------------- events
# (anchor, type, level, len). Silences sit under the line before the scare and end on it; rule stings on every
# "Rule number N"; risers end on their anchor; hits never sit on a line the dummy speaks (they land just after it).
EVENTS = [
    # (anchor, type, level, len[, extra]). extra: 'boost' (dB over the level-1 size: score.py; the three hardest scares
    # of the film: the tape cry, the goodnight, the both-eyelids blink), 'nosnap' (mix.py --plan full moves hits within
    # 0.35 s of a picture hit onto the picture's frame; nosnap keeps the word's time, e.g. the music hit 40 ms after a
    # wooden clack). Final-mix revisions (the full-length checks) are marked "final:".
    # cold open
    ('w2:goodnight+0.3', 'stinger', 0.5, None, {'nosnap': True}),   # v2: after the lamp's pop            # "...never, ever tell it goodnight."
    ('e11+0.06', 'riser', 0.45, 3.0), ('e11+0.06', 'hit', 0.7, None),     # final: on the picture's cut after "...why
    #   his lips never moved." (was on "lips", 1.15 s before the picture's impact: two hits)
    # Walter, the habit, the tuck-in
    ('s24', 'silence', 0.45, 1.2),                     # "He never said goodnight."
    # the hospital
    ('w35:grabbed', 'hit', 0.65, None),                # "Grandpa grabbed my wrist so hard it hurt."
    ('w36:whispered', 'silence', 0.55, 2.9),           # final: the whisper alone through "It was never me." (2.4 -> 2.9)
    ('e38', 'braam', 0.6, 3.0),                        # "It was never me." -> "An hour later, he was gone."
    #   final: the sub drop on "An hour later" (0.23 s after the braam) removed
    # the house, the case, the letter
    ('s48', 'swell', 0.55, 6.0),                       # seven rules -> "one of the seven was a lie"
    ('s50', 'stinger', 0.55, None),
    ('s52-0.1', 'rule', 0.7, None, {'nosnap': True}),
    # rule 1
    ('e59-0.5', 'silence', 0.5, 0.5), ('s60', 'hit', 0.7, None),          # "The case is empty."
    ('s63', 'silence', 0.6, 1.8),                      # "From the kitchen, there's a sound." (the spoon alone)
    ('s68', 'swell', 0.38, 9.4),                       # Mister Winks in Grandpa's chair (final: peaks in the gap
    #   after "In front of him is a mug of coffee.", not on it)
    ('s68', 'hit', 0.6, None),                         # final: the reveal cut (the picture's impact) gets the score too
    ('s72', 'silence', 0.5, 1.0),                      # "Two sugars." (v2: its sub drop removed: too many hits)
    ('s77', 'riser', 0.55, 4.0), ('s77-0.1', 'rule', 0.7, None, {'nosnap': True}),
    # rule 2: the voices
    ('s92', 'stinger', 0.55, None),                    # "Your voice."
    ('s103-0.5', 'silence', 0.7, 2.1), ('e103+0.14', 'hit', 0.7, None, {'nosnap': True}),       # "See you in the morning, kiddo." alone, then
    ('s108', 'swell', 0.6, 5.2),                       # the head has turned all the way -> the jaw hanging
    ('s108-0.12', 'hit', 0.75, None, {'nosnap': True}),                       # final: the head-turn reveal cut (the picture's impact)
    ('s110', 'silence', 0.7, 2.05), ('e110+0.06', 'sub_drop', 0.55, None, {'nosnap': True}),   # v2: sub only (m8)   # "slowly. / Clack."
    #   (the music hits on the clacks land 40 ms after the wooden clack and smaller: tests 2-4 measured the full-size
    #   hit 0.3-4 LU over the clack itself, burying the film's signature sound)
    ('s115-0.1', 'rule', 0.7, None, {'nosnap': True}),
    # rule 3: the joke, the TV
    ('s118-0.3', 'silence', 0.55, 2.4),                # the joke hangs in the dark
    ('s124', 'silence', 0.5, 1.2),                     # "Owen snorts."
    ('w127:clack+0.04', 'hit', 0.6, None, {'nosnap': True}),             # "Clack."
    ('s130', 'silence', 0.5, 2.0),                     # "Nobody laughs. Nobody breathes."
    ('s132', 'hit', 0.55, None),                       # "Then the TV turns on by itself."
    ('s137', 'swell', 0.6, 13.3),                      # with every wave he moves -> "his own audience"
    ('s143', 'silence', 0.75, 1.25),                   # the lamp flickers: everything drops
    ('w144:empty', 'stinger', 0.7, None),              # "...the chair is empty."
    ('s148-0.1', 'rule', 0.75, None, {'nosnap': True}),
    # rule 4: the stairs, the hand
    ('s156', 'pulse_on', 0.55, None),                  # "At three in the morning, the flashlight comes back."
    ('s157-0.12', 'hit', 0.7, None, {'nosnap': True}),                        # on the stairs, pointing it at my face
    ('s158', 'hit', 0.55, None),                       # "I grab him."
    ('s159', 'swell', 0.6, 7.6),                       # the hand through the slot -> "But there's a hand in there."
    ('s161-0.75', 'silence', 0.6, 0.7), ('s161', 'hit', 0.75, None),
    ('s162', 'pulse_off', 0.5, None),
    ('s164-0.2', 'silence', 0.4, 1.0),                 # "And it squeezes." (the music box takes over)
    ('e182', 'braam', 0.55, 2.5),                      # "It's rule two." -> "When you hear my voice, it's me."
    ('w185:clacks+0.04', 'hit', 0.55, None, {'nosnap': True}),           # "His jaw clacks shut"
    ('s190-0.1', 'rule', 0.75, None, {'nosnap': True}),
    # rule 5: the bookcase, the tape
    ('s196', 'hit', 0.8, None),                        # final: "Her lips didn't move." on the picture's cut (was on
    #   "move", 1 s after the picture's impact)
    ('s198', 'braam', 0.8, 3.0),                       # Mister Winks on top of the bookcase, the flashlight under his chin
    ('s208', 'stinger', 0.55, None),                   # "Because he isn't doing the voice."
    ('s209+0.3', 'silence', 0.6, 3.0),                 # final: the tape stops mid-joke (the picture stops at the line's
    #   start, the show theme drags to a halt with it): the drop-out runs to the camera look
    ('w210:turns', 'hit', 0.8, None),                  # final: he turns and looks straight into the camera (the
    #   picture's impact): silence -> hit
    ('s211', 'swell', 0.55, 3.0),                      # an old man's voice, cracked, crying -> (final: 4.6 -> 3.0 s,
    #   peaking into the drop-out)
    ('s214-0.2', 'silence', 0.5, 4.7),                 # final: "Please. Somebody help me. My name is Walter Kemp. That
    #   isn't me in the chair." all of it in the drop-out (was 3.5 s: the music came back under "That isn't me")
    ('e217', 'hit', 1.0, None, {'boost': 6.0}),        # final: the hardest hit of the film, with the audience laughing
    ('e217', 'braam', 1.0, 3.0),       #   (the hit is the punch; the braam's body stays lower: at +6 it
    #   sat 5 LU over "And the studio audience laughs.")
    ('s225', 'swell', 0.42, 6.3),                      # the real Walter on his knee, begging -> (final: peaks in the
    #   gap after "...in front of millions.", 0.75 -> 0.65)
    ('w226:laughed', 'stinger', 0.7, None),            # "And everyone laughed."
    ('s234-0.1', 'rule', 0.75, None, {'nosnap': True}),
    # rule 6: Owen in the den
    ('e242-0.05', 'sub_drop', 0.5, None, {'nosnap': True}),   # v2.1: a sub drop (the hit sat -8 LU on the end of "gone.")   # final: "...Owen is gone." lands as the word ends (on the word
    #   "gone" and the picture's cut it sat 11-12 LU over it; the picture's impact there is at -8 dB)
    ('w254:grabs', 'hit', 0.5, None, {'nosnap': True}), ('w254:screams', 'pulse_on', 0.7, None),   # v2 (M4): the scream first   # final: on the scream (was 0.5 s early)
    ('e259+0.14', 'braam', 0.75, 2.5, {'nosnap': True}),                      # "...and his hand comes with me." -> I catch Mom's wrist
    ('s260', 'pulse_off', 0.5, None),
    ('s264-0.4', 'silence', 0.6, 2.0),                 # "Say goodnight, Mister Winks." (Owen, crying)
    ('s266-0.15', 'silence', 0.7, 0.75),               # "Click."
    ('s268-0.5', 'silence', 0.8, 1.56),                # final: "Goodnight, Owen." all of it in near silence (0.5 -> 1.56 s)
    ('e268+0.05', 'hit', 1.0, None, {'boost': 5.0}),   # v2: 8 -> 5 (B1). final: it lands as Owen's eyes close (the cut): one of the three
    ('e268+0.05', 'sub_drop', 0.8, None),              #   hardest hits (with the SFX goodnight thump just before)
    ('s271', 'silence', 0.9, 1.15),                    # "The lamp goes out."
    ('s279-0.1', 'rule', 0.8, None, {'nosnap': True}),
    # rule 7: the realisation, the P.S., 1962, the eyelids
    ('s285', 'pulse_on', 0.55, None),                  # rule six and rule seven side by side
    ('s287', 'riser', 0.65, 3.0), ('s287', 'hit', 0.8, None),             # "Owen said goodnight to him."
    ('s289', 'stinger', 0.6, None),                    # "With his hand inside."
    ('s290', 'pulse_off', 0.5, None),
    ('s293', 'swell', 0.65, 6.7),                      # -> "Walter."
    ('s297', 'hit', 0.75, None),
    ('s305', 'braam', 0.75, 3.5),                      # "And they traded places."
    ('s306', 'pulse_on', 0.65, None),                  # "Sixty years later..."
    ('s310', 'sub_drop', 0.75, None, {'nosnap': True}),   # "A young one." (final: a sub drop on the line; the hit on the
    #   picture's cut sat on "...a new one")
    ('s311', 'pulse_off', 0.5, None),
    ('s315-0.1', 'silence', 0.8, 3.78),                # final: "Both of his eyelids close." (the two dry clicks) "Click,
    #   click." all in the drop-out (2.3 -> 3.0 s) -> v3: and "Owen can't wink." too (3.0 -> 3.78 s): the twist line is
    #   spoken into the silence ->
    ('w317:wink+0.1', 'stinger', 1.0, None, {'boost': 5.0}),   # v2: 8 -> 5 (B1). v3: the twist's hit lands after "Owen
    #   can't wink." as his eyes squeeze shut on screen, under "He never could." (on the cut, 663.13, it sat on the tail of
    #   "click." and 0.12 s before "Owen": the line only cleared the stinger by 1-3 dB in the 1-4 kHz band)
    # v2 (m13): the classic riser into the reveal word (film.py's reveal list, kept by the full plan now)
    ('s60', 'riser', 0.5, 3.0), ('s68', 'riser', 0.5, 3.0), ('w108:turned', 'riser', 0.5, 3.0), ('w132:turns', 'riser', 0.5, 3.0),
    ('w144:empty', 'riser', 0.55, 3.0), ('s157-0.12', 'riser', 0.4, 3.0, {'nosnap': True}), ('w161:hand', 'riser', 0.55, 3.0),
    ('s196', 'riser', 0.55, 3.0), ('w210:camera', 'riser', 0.55, 3.0),   # (w242:gone dropped, v2.1: it masked "gone.")
    ('w311:actually', 'riser', 0.55, 3.0),
    # the ending
    ('s321', 'stinger', 0.55, None),                   # "I scream it."
    ('s328-0.2', 'silence', 0.5, 0.9),                 # "Wink back."
    ('s330', 'sub_drop', 0.8, None),                   # "The boy who came home with us doesn't laugh anymore."
    ('s331', 'swell', 0.65, 9.6),                      # two sugars, the doorway, the smile -> (final: peaks into the cut;
    #   0.85 -> 0.65: it rose 6 LU over "He looked at me for a long time.")
    ('s336-0.4', 'silence', 0.6, 4.66),                # final: near silence from "See you in the morning, kiddo." through
    #   "He didn't say goodnight. He never will." (the SFX goodnight thump after "kiddo"; was a full hit 1.0 there)
    ('e338+0.25', 'end', 0.9, 4.0),                    # the cut to black (the picture's end hit)
]

# ---------------------------------------------------------------------------------------------------- identity
# (anchor, type, level, len, extra). 'show': the show theme from the old TV (score.render_show keys); 'winks': the same
# tune rotting, when he is near (score.render_winks); 'motif': the music-box lullaby (Grandpa's love). An extra value
# that is an anchor string under 'warp_at' is resolved to seconds after the event's start.
IDENTITY = [
    # Walter Kemp on Saturday mornings: the theme from an old TV, then it drags and rots on "...when he winked."
    ('s13', 'show', 0.42, None, dict(until='w17:winked+0.25', space='tv', off=0.0, warp=0.55, warp_at='w17:eyelids',
                                     stop='drag', fade=1.2)),
    ('s26', 'motif', 0.35, 7.0, dict(inst='musicbox')),                   # the tuck-in: three squeezes, I love you, "See you in the morning"
    ('w32:lap', 'winks', 0.32, 7.5, dict(depth=0.7)),  # Mister Winks on Grandpa's lap, his hand inside: one last show
    ('s68', 'winks', 0.38, 13.0, {}),                  # in Grandpa's chair at the kitchen table
    ('s108', 'winks', 0.5, None, dict(until='w111:clack-0.25', stop='cut', depth=1.2)),   # the head turned, the jaw, cut
    ('e121+0.1', 'winks', 0.8, 2.2, dict(stop='drag', off=14.0)),        # after the punchline: a rotten rimshot
    ('w132:turns-0.08', 'show', 0.5, None, dict(until='s143+0.05', space='tv', off=58.0, warp=0.4, warp_at='s140',
                                                stop='cut', fade=0.02, blast=7.0)),   # v2: on the turn, blaring  # the TV on by itself -> the lamp flickers
    ('s144+0.3', 'show', 0.3, 7.4, dict(space='far', off=36.0, stop='fade')),   # the TV still playing, far away
    ('s145', 'winks', 0.42, 5.5, {}),                  # a little flashlight clicks on; down the hall
    ('s156', 'winks', 0.58, 5.0, dict(depth=1.2)),     # 3 AM, the flashlight comes back
    ('s164', 'motif', 0.4, 6.5, dict(inst='musicbox')),                   # the three squeezes: I love you
    ('s172', 'motif', 0.45, 12.0, {}),                 # "Kiddo, it's me." (the wrong phrase)
    ('s198', 'winks', 0.45, 5.4, dict(depth=1.3)),     # on the bookcase, the jaw going up and down
    ('s203+0.5', 'show', 0.45, None, dict(until='s209+0.3', space='tv', off=40.0, stop='drag')),  # the tape (final:
    #   drags to a halt with the picture's stop and the warble, into the drop-out; was on the word "stops", 1.3 s later)
    ('s218+1.2', 'show', 0.4, None, dict(until='s221', space='tv', off=52.0, stop='fade', fade=1.0)),   # "part of the act"
    ('s232', 'motif', 0.45, 8.0, dict(inst='musicbox')),                  # the hand that squeezed mine; the only grandpa I ever had
    ('s243', 'winks', 0.62, None, dict(until='s254', stop='cut', depth=0.9, off=20.0)),   # Owen doing the act
    ('s300', 'show', 0.36, None, dict(until='e304', space='old', slug='ye_olde_piano_roll_the_fly_guy_five',
                                      off=2.0, stop='drag')),             # 1962, his very first show
    ('s312', 'winks', 0.5, None, dict(until='s315', stop='cut', depth=1.4)),   # in my arms he opens his eyes
    ('s325', 'motif', 0.4, 10.0, dict(inst='musicbox')),                  # behind glass, three states away
    ('e338+0.15', 'show', 0.3, 3.6, dict(space='far', off=52.0, stop='fade', fade=0.6)),   # a TV somewhere, after
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


# final mix: the arc the job asks for (quiet dread early, thicker and louder by rule 5): (from, to, + intensity)
ARC = [('s148', 's190', 0.03), ('s190', 's234', 0.06), ('s234', 's264', 0.04), ('s331', 's336', -0.1)]


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
    """The film's own sound: the show theme on the TV, Mister Winks's theme, the music box (score.py 'show' / 'winks' /
    'motif'). 'until' (an anchor) sets len; 'warp_at' (an anchor) becomes seconds after the start."""
    ev = []
    for a, ty, lv, ln, extra in IDENTITY:
        t = resolve(a, lines)
        e = {'t': round(t, 3), 'type': ty, 'level': lv}
        x = dict(extra)
        if 'until' in x:
            ln = max(0.5, resolve(x.pop('until'), lines) - t)
        if 'warp_at' in x and isinstance(x['warp_at'], str):
            x['warp_at'] = round(max(0.0, resolve(x['warp_at'], lines) - t), 3)
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
    return {'duration': round(duration, 2), 'intensity': intensity(lines, duration),
            'events': sorted(events(lines) + identity_events(lines), key=lambda e: e['t']),
            'track_map': track_map(lines)}


def table(lines):
    out = []
    tm = track_map(lines)
    for k, (x, (_a, _s, _o, why)) in enumerate(zip(tm, TRACK_MAP)):
        t1 = tm[k + 1]['t0'] if k + 1 < len(tm) else max(l['end'] for l in lines)
        out.append(f"{x['t0']:7.2f}-{t1:7.2f}  {x['slug']:40s} from {x['off']:5.1f}s  {why}")
    out.append('identity:')
    for e in identity_events(lines):
        ex = {k: v for k, v in e.items() if k not in ('t', 'type', 'level', 'len')}
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
