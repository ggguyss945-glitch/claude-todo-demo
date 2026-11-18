"""music_plan.py: the music map of "If The School Bus Stops At Midnight... DON'T GET ON", built the police film's
way (intensity curve, tension events, score.py), anchored to the script lines and their words (W/align/timeline.json,
W/align/asr_cache.json): nothing is a hard-coded film time.

Two things live here:
1. The arc (AUDIO_SPEC): one track section per stretch of the story, varispeeded to D / A / G in score.TRACKS. Dread
   from the hook (Through the Portal); the tape and Della step back; the bed thickens rule by rule (ARC adds
   intensity from rule 2 to rule 7: Terra Firma, Come Closer, Can They See Us, Don't Look, Midnight Wanderer,
   Escalation); the chase (rule 6) drives (All Exits Closed, then Irene under the backstory and Code of Violence on
   the road); rule 7 is a ticking build to 3:00 (Chronometer); true drop-outs before the biggest scares ("He read it
   off my phone.", "Silence.", "...Clever.", the lights dying, "I'm still holding a hand.", "LIGHTHOUSE!", the
   deadbolt -> "The hallway is full of him.", seat 22 empty for thirty-two years, "He's behind us.", the broom ->
   "Theo.", the 3:00 bell alone); hard hits on the twists; a rule sting on every "Rule number N". From the bell on the
   owner's WARM tracks take over (The Last Horizon for Theo going home and the porch light, At First Light for the
   morning, A Sky Unveiled under rule eight, Wait for Me on the Other Side under the tips, Just a Little Sunshine for
   the SHORT outro); "Next time..." gets one shadow. Grandma Della and the real adults are never scored as threats.
2. The film's own sound (IDENTITY, score.py 'jingle' events on the stem `show`): the ORIGINAL "Ride Right with
   Mister Whistlestop!" PSA jingle (audio/jingle_bus.py) coming back, each time worse: the whistle's hook under "That's
   Mister Whistlestop", the 1994 tape on the TV cart dragged to a halt on "pulled", his PA at midnight, the slow
   detuned music box while he unfolds and tape-skips across the lawn, the PA going off down the street with Sami, the
   music box again under the lure, the tape stopping dead on "It slips." and rewinding with his bus, then redeemed
   (warm) when the porch light comes on for Theo and on the rule-eight card.

Public API (unchanged): TRACK_MAP, FLATTEN, GAIN, INTENSITY, EVENTS, IDENTITY, ARC; resolve(anchor, lines) ('sN' /
'eN' = start / end of line N, 'wN:word' = that word's onset in line N (W/align/asr_cache.json), +- offset, or seconds);
track_map(lines), intensity(lines, duration), events(lines), identity_events(lines), music_cues(lines, duration),
load_lines(timeline_path=None), table(lines).

How it reaches the mix: mix.py --plan full (audio/final_mix.sh) takes this module's track map, intensity, events and
identity (snapping hits within 0.35 s to the picture's hit frames); --plan auto adds the track map and, when the
picture's sheet has no identity events of its own, IDENTITY. IDENTITY 'jingle' events render audio/jingle_bus.py
versions in score.py (render_jingle, score.JINGLE_MODULE).

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
    ('s0', 'through_the_portal_anthony_earls', 3.0,
     'the hook ("If the school bus stops outside your house at midnight..."): dread from the first line, his TV '
     'voice at 0:14, "And I gave it to him."'),
    ('s9', 'afterthoughts_beyza', 0.0,
     'the 1994 tape: the TV cart, the jingle on the CRT (identity tv1994) over a slow D-minor bed that steps back'),
    ('s22', 'end_of_rain_beyza', 0.0,
     'Grandma Della and bus 9 ("Brakes, mirrors, names."), the boy in seat 22: a quiet A-major pad, respect and an '
     'ordinary loneliness, never a threat'),
    ('s36', 'the_haunted_luella_gren', 6.6,
     'Sami, roll call, the walkies, the post, "Great smile!": sparse dark piano, unease creeping in'),
    ('s56', 'dark_tunnels_ethan_sloan', 2.0,
     'the seven rules taped inside the door, the family word: a flat sub drone that leaves the voice alone'),
    ('s59', 'terra_firma_dream_cave', 0.0,
     'rule 1: the mailbox letters, lights off, midnight, the air brakes, the PA reading the post (D minor pulse)'),
    ('s79', 'annihilated_blue_saga', 0.0, 'the comment beat: a pale pad, almost nothing'),
    ('s83', 'come_closer_belladonna_strings', 10.0,
     'rule 2: the door unfolds, the tape-skips across the lawn, the gloves, the roll call, "Here!" / "Almost."'),
    ('s122', 'can_they_see_us_experia', 1.0,
     'rule 3: no bars, Grandma out the back, the three knocks, "What\'s the word?", "...Clever.", the peephole'),
    ('s154', 'don_t_look_belladonna_strings', 0.0,
     'rule 4: Sami upstairs, 2:10, the lights die, the hand in the dark, the walkie, "LIGHTHOUSE!"'),
    ('s190', 'midnight_wanderer_luella_gren', 0.0,
     'rule 5: the deadbolt, 2:31, the flashlight, the window, "It\'s me, sweetheart."'),
    ('s210', 'escalation_jon_bjork', 20.0,
     'the deadbolt slides: the hallway full of him, "HERE!", the blink-cut run to his bus, "Seat\'s saved"'),
    ('s239', 'dark_forebodings_ethan_sloan', 0.0, 'rule 6 card and "don\'t chase him on foot": a held breath'),
    ('s243', 'all_exits_closed_guy_copeland', 32.0,
     'THE CHASE: Mina runs to bus 9, the broom out of the doors, 911 works, "So are we.": driving D pulse'),
    ('s254', 'irene_kevin_dailey', 16.0,
     'the backstory on the road (seat 22 empty for 32 years, 1994, the rule of his last stop), hijacked by the dash '
     'radio: starts near silent and builds'),
    ('s272', 'code_of_violence_dian_shuai', 0.0,
     'his bus ahead, the backwards head, the brake check, the mirror ripped off, his amber windows behind them'),
    ('s286', 'can_they_see_us_experia', 64.0,
     'rule 7: 2:57, the school, his bus already waiting, the two Minas, the foot on the step, the rip'),
    ('s317', 'chronometer_guy_copeland', 0.0,
     '2:58 -> 3:00: the ticking build (E minor -> D minor): seat 22, the lure, the taunt, 2:59, the doors and the '
     'broom, "Theo.", the long whistle against the clock'),
    ('s371', 'the_last_horizon_aerian', 34.0,
     'THE WARM TURN: Grandma sees Theo, kneels, "Six mornings...", his porch light comes on (its swell lands on "it '
     'does"), the clipboard of "Sat alone"'),
    ('s386', 'at_first_light_gavin_luke', 0.0,
     'the morning: the apology, the hug, the new girl in seat 21, "Hi. I\'m Mina. What\'s your name?"'),
    ('s395', 'dark_forebodings_ethan_sloan', 30.0, 'the sting: far back through the rear window, a new clipboard'),
    ('s397', 'a_sky_unveiled_megan_wofford', 0.0,
     'that night: rule eight written under Grandma\'s seven, the warm jingle on the card (F -> D)'),
    ('s401', 'wait_for_me_on_the_other_side_instrumental_version_clngr', 10.0,
     'the outro tips (code word, no ride without a yes, "that\'s when you tell", parents, thank your driver)'),
    ('s413', 'just_a_little_sunshine_instrumental_version_staffan_carlen', 0.0,
     'the SHORT warm outro: the comment payoff, like / subscribe for Theo; "Next time..." darkens it'),
]

# slug -> share of the track's own dynamics evened out (score.FLATTEN 0.3 otherwise)
FLATTEN = {'end_of_rain_beyza': 0.6, 'the_haunted_luella_gren': 0.45, 'through_the_portal_anthony_earls': 0.4,
           'the_last_horizon_aerian': 0.35, 'at_first_light_gavin_luke': 0.55, 'a_sky_unveiled_megan_wofford': 0.55,
           'wait_for_me_on_the_other_side_instrumental_version_clngr': 0.6,
           'just_a_little_sunshine_instrumental_version_staffan_carlen': 0.6, 'chronometer_guy_copeland': 0.3,
           'all_exits_closed_guy_copeland': 0.35, 'irene_kevin_dailey': 0.3}
# slug -> level trim (dB): the sub drones read quiet (+2.5..+4.5, measured in the earlier films); the owner's bright
# new tracks are mid-band and loud (Just a Little Sunshine -9 LUFS, centroid 2.3 kHz; Wait for Me -9.5, 2.4 kHz;
# both clip on decode): down so they never sit on the voice
GAIN = {'dark_tunnels_ethan_sloan': 3.0, 'dark_forebodings_ethan_sloan': 2.5, 'end_of_rain_beyza': 3.0,
        'escalation_jon_bjork': 3.5, 'irene_kevin_dailey': 1.0, 'the_haunted_luella_gren': 0.5,
        'come_closer_belladonna_strings': 0.0, 'don_t_look_belladonna_strings': 3.0, 'terra_firma_dream_cave': 3.5,
        'chronometer_guy_copeland': 0.5, 'can_they_see_us_experia': -1.5, 'through_the_portal_anthony_earls': -1.5,
        'all_exits_closed_guy_copeland': -1.0, 'the_last_horizon_aerian': -1.0, 'at_first_light_gavin_luke': 1.0,
        'a_sky_unveiled_megan_wofford': -2.0, 'wait_for_me_on_the_other_side_instrumental_version_clngr': -6.0,
        'just_a_little_sunshine_instrumental_version_staffan_carlen': -7.0, 'afterthoughts_beyza': 1.0}

# ---------------------------------------------------------------------------------------------------- intensity
INTENSITY = [
    # the hook (strong), the tape (steps back under the jingle), Della (calm), Sami and the post (creeping)
    ('s0', 0.6), ('s3', 0.72), ('s4', 0.55), ('s6', 0.62), ('s8', 0.68), ('s9', 0.3), ('s12', 0.35), ('s17', 0.4),
    ('s20', 0.45), ('s22', 0.22), ('s29', 0.28), ('s33', 0.3), ('s36', 0.3), ('s42', 0.38), ('s49', 0.45),
    ('s52', 0.55), ('s53', 0.5), ('s56', 0.38),
    # rule 1
    ('s59', 0.5), ('s63', 0.45), ('s66', 0.55), ('s67', 0.62), ('s70', 0.66), ('s72', 0.6), ('s75', 0.72),
    ('s77', 0.78), ('e78', 0.7),
    # the comment beat
    ('s79', 0.2), ('e82', 0.22),
    # rule 2
    ('s83', 0.5), ('s88', 0.58), ('s92', 0.68), ('s98', 0.72), ('s100', 0.78), ('s104', 0.7), ('s108', 0.62),
    ('s113', 0.8), ('s117', 0.72), ('e121', 0.7),
    # rule 3
    ('s122', 0.55), ('s126', 0.6), ('s131', 0.58), ('s134', 0.68), ('s138', 0.72), ('s141', 0.6), ('s143', 0.82),
    ('s147', 0.72), ('s152', 0.78), ('e153', 0.75),
    # rule 4 (the dark)
    ('s154', 0.55), ('s157', 0.45), ('s161', 0.62), ('s164', 0.5), ('s168', 0.62), ('s171', 0.8), ('s173', 0.88),
    ('s179', 0.85), ('s183', 0.55), ('s187', 0.9), ('e189', 0.7),
    # rule 5
    ('s190', 0.6), ('s196', 0.62), ('s200', 0.7), ('s202', 0.76), ('s208', 0.82), ('s212', 1.0), ('s216', 0.9),
    ('s223', 0.95), ('s230', 0.9), ('s232', 0.75), ('s238', 0.8), ('e238', 0.7),
    # rule 6: the chase, the backstory, the road
    ('s239', 0.5), ('s243', 0.78), ('s249', 0.82), ('s252', 0.86), ('s254', 0.5), ('s256', 0.62), ('s260', 0.55),
    ('s263', 0.7), ('s265', 0.85), ('s266', 0.6), ('s272', 0.75), ('s275', 0.88), ('s279', 0.95), ('s280', 0.6),
    ('s281', 0.85), ('s283', 0.95), ('e285', 0.85),
    # rule 7: the school, the clock (thickest of the film), the lure (it pulls back), the doors, Theo, the whistle
    ('s286', 0.62), ('s290', 0.66), ('s297', 0.75), ('s302', 0.85), ('s305', 0.9), ('s308', 0.6), ('s309', 0.95),
    ('s313', 0.92), ('s317', 0.7), ('s320', 0.8), ('s324', 0.6), ('s328', 0.55), ('s331', 0.72), ('s335', 0.8),
    ('s336', 0.85), ('s341', 0.7), ('s343', 0.9), ('s347', 0.95), ('s352', 0.7), ('s354', 0.95), ('s358', 1.0),
    ('s361', 1.0), ('e363', 0.95),
    # 3:00, the grin slips, the warm turn, the watchlist
    ('s364', 0.35), ('s366', 0.55), ('s370', 0.5), ('s371', 0.35), ('s374', 0.42), ('s377', 0.6), ('s378', 0.42),
    ('s383', 0.5), ('e385', 0.48),
    # the morning, the sting, rule eight
    ('s386', 0.3), ('s389', 0.35), ('s392', 0.42), ('s394', 0.6), ('s395', 0.62), ('s397', 0.3), ('s398', 0.42),
    ('e400', 0.4),
    # the outro (calm, warm, bright for the call to action, a shadow on "Next time")
    ('s401', 0.28), ('s408', 0.32), ('s413', 0.42), ('s416', 0.45), ('s417', 0.3), ('e418', 0.25),
]

# ---------------------------------------------------------------------------------------------------- events
# (anchor, type, level, len[, extra]). Silences sit under the line before the scare and end on it; rule stings on every
# "Rule number N"; risers end on their anchor; 'nosnap' keeps a word's time when the picture has a hit nearby.
EVENTS = [
    # the hook
    ('s3-0.05', 'hit', 0.6, None),                                    # his TV voice: "I know your name!"
    ('s8', 'sub_drop', 0.55, None),                                   # "And I gave it to him."
    ('s15+1.0', 'swell', 0.4, 4.0),                                   # "...a grin too wide... that never moves."
    ('s53', 'sub_drop', 0.4, None),                                   # "Grandma's face went grey."
    ('s62', 'sub_drop', 0.4, None),                                   # "He can only call the names he can read."
    # rule 1
    ('s59-0.1', 'rule', 0.7, None, {'nosnap': True}),
    ('s66-0.4', 'silence', 0.7, 1.2), ('s67', 'hit', 0.55, None),     # "Midnight." -> the air brakes
    ('e75-0.2', 'silence', 0.85, 1.4), ('s76', 'hit', 0.85, None),    # "He read it off my phone."
    ('s77', 'stinger', 0.6, None),
    # rule 2
    ('s83-0.1', 'rule', 0.7, None, {'nosnap': True}),
    ('s92', 'riser', 0.5, 8.0),                                       # unfolding ... "The streetlight flickers."
    ('s100', 'hit', 0.6, None),                                       # white gloves curl around our doorframe
    ('s111', 'hit', 0.5, None),                                       # my hand slaps over his mouth
    ('s112', 'silence', 0.9, 2.0),                                    # "Silence."
    ('s114', 'stinger', 0.75, None),                                  # "Here!" in Sami's voice
    ('s116', 'hit', 0.6, None),                                       # "Almost."
    ('s121', 'sub_drop', 0.55, None),                                 # "Last stop, three a.m."
    # rule 3
    ('s122-0.1', 'rule', 0.7, None, {'nosnap': True}),
    ('s133', 'sub_drop', 0.5, None),                                  # the flashlight goes out
    ('s141-0.2', 'silence', 0.8, 1.4), ('s143', 'hit', 0.75, None),   # "...Clever."
    ('s144', 'stinger', 0.7, None),                                   # the peephole goes white
    ('s149', 'hit', 0.5, None),                                       # "DON'T OPEN THE DOOR!"
    # rule 4
    ('s154-0.1', 'rule', 0.7, None, {'nosnap': True}),
    ('s162', 'silence', 1.0, 2.6),                                    # "Every light dies. Total black."
    ('s171-0.4', 'silence', 0.85, 1.2), ('s171+0.3', 'hit', 0.85, None),   # "I'm still holding a hand."
    ('s173', 'stinger', 0.8, None),                                   # "A white glove."
    ('s179', 'hit', 0.7, None),                                       # "I rip free."
    ('e186', 'silence', 0.85, 1.0), ('s187', 'hit', 0.9, None),       # "LIGHTHOUSE!"
    # rule 5
    ('s190-0.1', 'rule', 0.7, None, {'nosnap': True}),
    ('s202', 'hit', 0.45, None),                                      # "Knock, knock."
    ('s211', 'riser', 0.55, 6.0),                                     # ... "The deadbolt slides."
    ('s211', 'silence', 0.95, 1.7), ('s212', 'hit', 1.0, None),       # "The hallway is full of him."
    ('s219', 'stinger', 0.75, None),                                  # "HERE!"
    ('s231', 'hit', 0.7, None),                                       # the doors slap shut an inch from my fingers
    ('s232', 'swell', 0.5, 6.0),                                      # Sami's palm on the window of seat four
    ('s237', 'sub_drop', 0.5, None),                                  # "Seat's saved, Mina."
    # rule 6
    ('s239-0.1', 'rule', 0.7, None, {'nosnap': True}),
    ('s256-0.6', 'silence', 0.8, 1.2), ('w256:empty', 'hit', 0.85, None),   # seat 22 empty for thirty-two years
    ('s263-0.3', 'silence', 0.7, 1.0), ('s265', 'stinger', 0.75, None),     # the radio, in Grandma's voice
    ('s275', 'hit', 0.7, None),                                       # "Backwards."
    ('s279', 'hit', 0.65, None),                                      # the mirror ripped off
    ('s280', 'silence', 0.7, 1.4), ('s283', 'stinger', 0.85, None),   # "He's behind us."
    ('s285', 'sub_drop', 0.5, None),                                  # "Two forty-one."
    # rule 7
    ('s286-0.1', 'rule', 0.75, None, {'nosnap': True}),
    ('s294', 'sub_drop', 0.5, None),                                  # his bus is already parked at the doors
    ('s305', 'hit', 0.75, None),                                      # "Two of me."
    ('s308', 'silence', 0.8, 1.6), ('s309', 'riser', 0.5, 2.5),       # "Not even for Sami." -> the SCREAM
    ('s314', 'hit', 0.65, None),                                      # a glove snaps shut on his pajamas
    ('s320', 'swell', 0.55, 6.0),                                     # one impossibly long arm
    ('s332', 'sub_drop', 0.45, None),                                 # "Hurry. Just you. Our secret."
    ('s336', 'sub_drop', 0.5, None),                                  # "Two fifty-nine."
    ('s352', 'riser', 0.55, 4.5), ('s353', 'silence', 0.9, 1.4),      # the broom cracks ...
    ('s354', 'hit', 0.9, None),                                       # "Theo."
    ('s358', 'stinger', 0.8, None),                                   # "THEO!"
    ('s364-0.3', 'silence', 1.0, 1.6),                                # "Three o'clock." (the bell, alone)
    ('s370', 'hit', 0.6, None),                                       # his clipboard clatters
    ('s384', 'sub_drop', 0.45, None),                                 # "One name. Nobody I know."
    ('s394', 'stinger', 0.7, None),                                   # the name on his last page
    ('s417', 'sub_drop', 0.3, None),                                  # "Next time..."
]

# ---------------------------------------------------------------------------------------------------- identity
# The RIDE RIGHT JINGLE (audio/jingle_bus.py, score.py 'jingle'): an ORIGINAL 1994 PSA tune that keeps coming back,
# warped, until it is redeemed. (anchor, type, level, len, extra): 'version', 'until' (an anchor: sets len),
# stop ('fade' | 'cut' | 'drag'), fade (fade-in s), off, loops, stop_beat, wind_down, space.
IDENTITY = [
    # the hook: "That's Mister Whistlestop." -- the whistle's hook, once, clean
    ('s4-0.15', 'jingle', 0.45, None, dict(version='sting', until='s4+2.0', stop='fade', fade=0.01)),
    # 1994: the tape on the TV cart, from "Ride Right with Mister Whistlestop", dragged to a halt on "pulled"
    ('s10-0.4', 'jingle', 0.55, None, dict(version='tv1994', loops=2, until='w20:pulled+0.3', stop='drag', fade=0.05)),
    # rule 1: the loudspeaker crackles -> the first bars on his PA, cut by his reading voice
    ('s70+0.7', 'jingle', 0.55, None, dict(version='pa', until='s72-0.05', stop='cut', fade=0.05)),
    # rule 2: the door unfolds, the tape-skips across the lawn (the slow, warped music box), until the roll call
    ('s88', 'jingle', 0.5, None, dict(version='musicbox', until='s104', stop='fade', fade=1.0)),
    # rule 5: the bus pulls away with no lights on, the tune on his PA going off down the street
    ('s238', 'jingle', 0.5, None, dict(version='pa', until='s239-0.2', stop='fade', fade=0.2, space='street')),
    # rule 7: the lure ("Soft. Kind.") -- the music box, slow, under the kind voice
    ('s324', 'jingle', 0.45, None, dict(version='musicbox', until='s328+1.0', stop='fade', fade=1.5)),
    # 3:00: the grin slips -- the tape plays, stops dead on "It slips." and REWINDS under "the bus rewinds"
    ('s368-3.64', 'jingle', 0.6, None, dict(version='tapestop', stop_beat=8.0, until='s369+3.0', stop='fade',
                                             fade=0.05)),
    # the porch light comes on for Theo: the tune redeemed, warm, once
    ('s376', 'jingle', 0.5, None, dict(version='warm', until='s378+0.5', stop='fade', fade=1.0)),
    # rule eight: the warm arrangement on the card
    ('s397+0.5', 'jingle', 0.55, None, dict(version='warm', until='s401+0.5', stop='fade', fade=1.5)),
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
ARC = [('s83', 's122', 0.02), ('s122', 's154', 0.04), ('s154', 's190', 0.06), ('s190', 's239', 0.08),
       ('s239', 's286', 0.09), ('s286', 's364', 0.1)]


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


OUTRO_LEN = 9.75        # (the Bunnyman's jingle outro; unused here: every Bus film identity event carries its own len)


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
