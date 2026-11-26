"""music_plan.py: the music map of "If a Girl Is OBSESSED With Being Your Only Friend... DON'T WRITE YOUR NAME" (Night
Policy). THIS film: the trailer cold open (score 'trailer'), the hook on a dark pad, unease rising rule by rule (ARC),
the reveals ("I was.", "From me.", "It was me.") on silence or on the tape song dragging to a halt, the relief and
Lina's healed song at dawn, a calm low bed under the outro checklist, no "next time" teaser. THE TAPE SONG ('show',
space 'tape' / 'far') and its rotted form as Evie's theme ('winks': the sweet tune plays while she moves), and STICK
LIKE GLUE (MOTIF_MODULE 'motif_obsession'). Anchors are script phrases, 'tag#word' and 'end:tag' forms also work
when a phrase is a line's tag (see resolve). The earlier film's notes follow.

(Buttons) the music map of "If Your Mom's Eyes Turn Into Buttons... DON'T KEEP HER SECRET" (Night Policy),
built the earlier films' way (intensity curve, tension events, score.py), anchored to the script's WORDS: every anchor
names a phrase of script/narration_en.txt and is found in the timeline's line texts at run time
(W/align/timeline.json; word onsets from each line's own 'words'), so a re-paced voice edit needs no change here.
Nothing is a hard-coded film time (two 'wN:word' anchors name Mom's last sung line by index, see IDENTITY).

Anchors (resolve(anchor, lines)):
    'Rule number one'              the start of the line holding that phrase (case and punctuation ignored)
    'end:Two black buttons flashed' the end of the line holding the phrase's LAST word
    'Mom at the wheel#humming'     the onset of the word 'humming' inside the line that holds the phrase
    ... +0.4 / ... -1.2            an offset in seconds (a space, then the signed number, at the very end)
    'sN' / 'eN' / 'wN:word'        a line index form, or plain seconds
An anchor that is not found is skipped with a warning (the row drops out; the mix never fails on the plan).

The arc (keyed to the timeline's lines): quiet unease at the kitchen table (the calmest stretch; the bed steps back
under Mom's sung song), the chat on a sinister lullaby, then rule by rule the bed rises (ARC): the streetlight woman,
the coat in the closet, the car, 2 a.m. and the microwave door, dinner and the lamp, midnight; THE CLIMAX in rule
seven (the coat, NO, the marker, the fingers an inch away) at intensity 1.0; the relief after "Green." on a warm pad,
the warm music-box ending (Mom's real box under her real words), the sting (the empty jar, the chime, the wave), and a
calm low bed under the outro checklist (every word clear; no "next time" teaser). Silences sit before the big scares;
boosted hits (+6..+10 LU momentary, smooth releases) land just after their words: "We're going home.", "Two black
buttons flashed.", "Like somebody was inside it.", the two "Buttons.", the chin on his shoulder, "I couldn't see me.",
"Holding open... the red coat."

The film's own sound (IDENTITY, score.py 'jingle' events = MOTIF_MODULE 'motif_buttons' on the stem `show`): THE
BUTTON SONG (audio/motif_buttons.py), our original four-bar waltz measured from Mom's sung take, returning in order:
the clean music box in the chat, the stolen box winding down in the closet at 3 a.m., hummed slowed through the car
window, the perfect looped "recording" at the windowsill, detuned at the climax (bent onto the Blank's sung words,
stopping one note short: "Six closed. The song stopped."), four notes from the empty cardigan, Mom's real box under
her "Mama sees you. Say goodnight.", and the son's tablet chime (the first four notes). It never doubles a sung line.

How it reaches the mix: mix.py --plan full (audio/final_mix.sh) takes this module's track map, intensity, events and
identity (snapping hits within 0.35 s to the picture's hit frames); --plan auto adds the track map and, when the
picture's sheet has no identity events of its own, IDENTITY.

Public API (unchanged): TRACK_MAP, FLATTEN, GAIN, INTENSITY, EVENTS, IDENTITY, ARC; resolve(anchor, lines),
line_index(anchor, lines), track_map(lines), intensity(lines, duration), events(lines), identity_events(lines),
music_cues(lines, duration), load_lines(timeline_path=None), table(lines).

CLI: python3 music_plan.py [--timeline T] [--out W/cues/music_cues_plan.json] [--table]
"""
import importlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.normpath(os.path.join(HERE, '..', '_work'))
TIMELINE = os.path.join(W, 'align', 'timeline.json')
WORDS = os.path.join(W, 'align', 'asr_cache.json')        # fallback only: the timeline's own line words come first
MOTIF_MODULE = 'motif_obsession'                           # the identity's renderer (score.JINGLE_MODULE)

# ---------------------------------------------------------------------------------------------------- arrangement
# THIS film ("If a Girl Is OBSESSED With Being Your Only Friend... DON'T WRITE YOUR NAME"). (anchor, track slug, offset
# s in the varispeed track, why). Tracks and shifts: score.TRACKS (this film's table: every track on A-flat major / F
# minor / D-flat, +0.4 semitone: the chant's tuning). The cold open (the trailer) has no track: render_trailer is its
# bed; the first section starts on the hook.
TRACK_MAP = [
    ('When I was twelve, my best friend handed me', 'borders_beyza', 0.0,
     'the hook: a dark quiet pad under the card, the new girl, "halfway down the stairs"'),
    ('Danny had been my best friend since we were seven', 'rylee_s_tears_franz_gordon', 0.0,
     'lonely: Danny with Kofi and Sam, "I ate alone."; the tape song takes over at "At seven, on the swings"'),
    ('Behind our school: an old hopscotch', 'for_all_time_megan_wofford', 0.0,
     'the Keeping Square legend, the chalk girl in the square: slow, mysterious'),
    ('That day, a new girl sat behind me', 'sleep_forever_luella_gren', 0.0,
     'Evie arrives, the locker, "favourite person": a sinister lullaby, sweet on top'),
    ('Then Danny crossed the hall', 'borders_beyza', 40.0, 'the card: quiet'),
    ('Rule number one', 'the_deal_ruiqi_zhao', 0.0, 'rule 1: the pings, the dark screen, the streetlight, the porch light'),
    ('Thursday morning, our path was wet and clean', 'borders_beyza', 80.0,
     'the wet path, Mom on the phone, the sneaker print, the comment prompt: quiet'),
    ('Rule number two', 'tears_of_a_shadow_eva_hummingbird', 0.0, 'rule 2: the bracelet, "Only me?", halfway up the path'),
    ('Rule number three', 'on_the_other_hand_franz_gordon', 0.0, 'rule 3: the password, the dots, 2 a.m., the fingerprint'),
    ('Rule number four', 'ancestors_without_peace_ludvig_moulin', 0.0,
     'rule 4: the red lights, the swings, the square at sunset: a driving build'),
    ('The chalk slid out, flat across the playground', 'annihilated_blue_saga', 0.0,
     'the chalk stands up, "Here I am.", the clank, "I ran."'),
    ('Rule number five', 'you_are_not_alone_luella_gren', 0.0, 'rule 5: dinner, the window, the doorstep, the neck'),
    ('Rule number six', 'they_come_at_night_etienne_roussel', 0.0, 'rule 6: midnight, the letterbox, O-N-L-Y, the stub'),
    ('Rule number seven', 'pulse_pressure_max_anson', 60.0,
     'rule 7: the kitchen, M-E creeping, the pings, Block: the climax pulse (the trailer\'s, later in the track)'),
    ('Danny didn\'t go down. He woke his mom', 'annihilated_blue_saga', 50.0, 'after "It was me.": low, then the door'),
    ('At dawn, we scrubbed the path together', 'when_the_sun_sets_anna_landstrom', 0.0,
     'relief: the scrub at dawn; Lina\'s healed song (the bed steps back under her)'),
    ('Monday, I told Mrs. Rahman too', 'movement_william_claeson', 0.0, 'Mrs. Rahman, Danny\'s message, the lunch table'),
    ('Last week, Danny didn\'t answer all day', 'rylee_s_tears_franz_gordon', 60.0, 'the coda: the old pull, ONLY.'),
    ('Okay. Breathe', 'sentient_gavin_luke', 0.0, 'the outro checklist: calm and LOW, every word clear'),
]
FLATTEN = {'borders_beyza': 0.5, 'rylee_s_tears_franz_gordon': 0.45, 'for_all_time_megan_wofford': 0.45,
           'sleep_forever_luella_gren': 0.45, 'the_deal_ruiqi_zhao': 0.4, 'tears_of_a_shadow_eva_hummingbird': 0.4,
           'on_the_other_hand_franz_gordon': 0.4, 'ancestors_without_peace_ludvig_moulin': 0.35,
           'annihilated_blue_saga': 0.4, 'you_are_not_alone_luella_gren': 0.4,
           'they_come_at_night_etienne_roussel': 0.3, 'pulse_pressure_max_anson': 0.35,
           'when_the_sun_sets_anna_landstrom': 0.6, 'movement_william_claeson': 0.55, 'sentient_gavin_luke': 0.6}
# slug -> level trim (dB): quiet pads up (borders -17.9, sun sets -20.9, annihilated -18.6 LUFS), the loud pulses and
# the outro bed down (low under the checklist: every word clear)
GAIN = {'borders_beyza': 2.5, 'when_the_sun_sets_anna_landstrom': 3.0, 'annihilated_blue_saga': 2.5,
        'pulse_pressure_max_anson': -2.0, 'they_come_at_night_etienne_roussel': -1.0, 'sentient_gavin_luke': -5.0,
        'movement_william_claeson': -1.0}

# ---------------------------------------------------------------------------------------------------- intensity
INTENSITY = [
    ('If someone you met three days ago', 0.75), ('I know who it is', 0.5),          # the trailer, then the hook
    ('When I was twelve, my best friend handed me', 0.4), ('Danny had been my best friend', 0.2), ('I ate alone', 0.15),
    ('Behind our school: an old hopscotch', 0.3), ('In the square, someone had chalked a little girl', 0.4),
    ('That day, a new girl sat behind me', 0.25), ('By Tuesday, she was waiting', 0.25),
    ("Wednesday, at my shoulder... she didn't blink", 0.45), ('Then Danny crossed the hall', 0.3),
    # rule 1
    ('Rule number one', 0.35), ('Every ping, one note of my song', 0.5), ('The dark screen lit up anyway', 0.6),
    ('Under the streetlight, Evie smiled up', 0.66), ('I switched off my light', 0.6),
    ('Thursday morning, our path was wet', 0.22), ('Forty-seven messages, in one night. Before rule two', 0.18),
    # rule 2 .. 4: unease rising rule by rule (ARC adds to each)
    ('Rule number two', 0.38), ('Suddenly Evie was one inch from my shoulder', 0.55), ('That night, ONLY ME was halfway', 0.58),
    ('Rule number three', 0.4), ('Two a.m. Her dot was on our house', 0.62), ('Just one white chalk fingerprint', 0.68),
    ('Friday. Mrs. Rahman', 0.35), ('There. Now it\'s only me', 0.55),
    ('Rule number four', 0.45), ('At break, on the swings, she sang my song', 0.5), ('At sunset, I went to sort it out', 0.62),
    ('It was covered in chalk', 0.7), ('From the square, slowed down', 0.72), ('I was. Last Sunday', 0.5),
    ('The chalk slid out', 0.78), ('Floodlight. The caretaker', 0.6), ('That night, ONLY ME was on our step', 0.55),
    ('Rule number five', 0.5), ('Behind Mom, outside the dark window', 0.66), ("ONLY ME moved onto our doorstep", 0.7),
    ("Evie's neck was bending", 0.8),
    ('Rule number six', 0.55), ('From the landing, I heard our letterbox lift', 0.75), ('Chalk-white fingers slid through', 0.85),
    ('A chalk stub dropped through', 0.88), ('My feet moved. One step down', 0.92), ('It says your name', 0.6),
    ('From me.', 0.5),
    ('Rule number seven', 0.6), ('Behind me, the letterbox rattled', 0.9), ('Thank you for telling me', 0.55),
    ('It never rained', 0.35), ('Mom saved every message from Evie', 0.6), ('The same words. Word for word', 0.7),
    ('It was me.', 0.5), ("Danny didn't go down", 0.35), ('Evie was on our doormat', 0.75), ("Write your name? No. I'm not", 0.8),
    ('I hope you find lots of people', 0.6), ('Her colour drained to chalk-white', 0.55),
    ('At dawn, we scrubbed the path', 0.15), ('Monday, I told Mrs. Rahman too', 0.15), ('Weeks later, Danny stopped', 0.15),
    ('Last week, Danny didn\'t answer all day', 0.3), ('Next morning, one chalk word', 0.45), ('Then I called Danny', 0.15),
    # the outro: calm, low, every word clear
    ('Okay. Breathe', 0.12), ('Now. Special, or Trapped', 0.15), ('Sleep well', 0.12),
]
# the bed thickens rule by rule: (from, to, + intensity)
ARC = [('Rule number two', 'Rule number three', 0.02), ('Rule number three', 'Rule number four', 0.04),
       ('Rule number four', 'Rule number five', 0.05), ('Rule number five', 'Rule number six', 0.06),
       ('Rule number six', 'Rule number seven', 0.08), ('Rule number seven', 'At dawn, we scrubbed', 0.08)]

# ---------------------------------------------------------------------------------------------------- events
# (anchor, type, level, len, extra). Hits: 'boost' only on the planned scares, each just after its word ('nosnap'
# keeps the word's time). The reveals ("I was.", "From me.", "It was me.") land on SILENCE (or on the tape song
# dragging to a halt, IDENTITY). Rule stings on every "Rule number N". No "next time" teaser: the end cue at the outro.
EVENTS = [
    ('When I was twelve, my best friend handed me', 'sub_drop', 0.45, None),
    ('Rule number one -0.1', 'rule', 0.6, None, {'nosnap': True}),
    ('The dark screen lit up anyway -0.15', 'silence', 0.7, 1.4),
    ('end:lit up anyway. I can see your light\'s still on +0.05', 'hit', 0.8, None, {'boost': 2.5, 'nosnap': True}),
    ('end:ONLY ME. +0.05', 'sub_drop', 0.5, None),
    ('Rule number two -0.1', 'rule', 0.6, None, {'nosnap': True}),
    ('end:Suddenly Evie was one inch from my shoulder +0.05', 'hit', 0.75, None, {'boost': 2.0, 'nosnap': True}),
    ('Rule number three -0.1', 'rule', 0.6, None, {'nosnap': True}),
    ('Then in my room -0.1', 'silence', 0.7, 1.2),
    ('end:on the inside of my window +0.05', 'hit', 0.8, None, {'boost': 2.5, 'nosnap': True}),
    ('Rule number four -0.1', 'rule', 0.6, None, {'nosnap': True}),
    ('Next red light. There -0.1', 'sub_drop', 0.45, None),
    ('It was covered in chalk', 'pulse_on', 0.5, None),
    ('I was. Last Sunday -0.25', 'silence', 1.0, 1.6),                       # REVEAL 1 on silence (the tape song drags out first)
    ('end:and stood up +0.05', 'hit', 0.9, None, {'boost': 3.0, 'nosnap': True}),
    ('Floodlight. The caretaker -0.1', 'pulse_off', 0.4, None),
    ('Rule number five -0.1', 'rule', 0.6, None, {'nosnap': True}),
    ('end:toward my window +0.05', 'hit', 0.85, None, {'boost': 2.5, 'nosnap': True}),
    ('Rule number six -0.1', 'rule', 0.6, None, {'nosnap': True}),
    ('From the landing, I heard our letterbox lift -0.2', 'silence', 0.6, 2.0),
    ('end:Chalk-white fingers slid through +0.05', 'hit', 0.85, None, {'boost': 3.0, 'nosnap': True}),
    ('Behind me, the landing light clicked on -0.1', 'sub_drop', 0.5, None),
    ('From me. -0.3', 'silence', 1.0, 1.7),                      # REVEAL 2 on silence
    ('Rule number seven -0.1', 'rule', 0.6, None, {'nosnap': True}),
    ('Behind me, the letterbox rattled', 'pulse_on', 0.6, None),
    ('Thank you for telling me -0.2', 'pulse_off', 0.4, None),
    ('That blue front door was Danny\'s', 'riser', 0.6, 3.0),
    ('It was me. -0.3', 'silence', 1.0, 2.0),                    # REVEAL 3 on silence
    ("No. I'm not your only -0.25", 'sub_drop', 0.55, None),
    ('Her colour drained to chalk-white', 'swell', 0.5, 6.0),
    ('Next morning, one chalk word on my path', 'sub_drop', 0.4, None),
    ('Okay. Breathe -0.2', 'end', 0.3, None),
]

# ---------------------------------------------------------------------------------------------------- identity
# (anchor, type, level, len, extra). 'show': THE TAPE SONG from Mom's camcorder tape (score.render_show: space 'tape'
# = the camcorder speaker, 'far'; warp up to 9 semitones, stop 'drag' / 'cut'); 'winks': the same tune ROTTED as
# EVIE's theme (score.render_winks: slowed, detuned, seasick; stop 'drag' on the reveals); 'jingle': STICK LIKE GLUE
# (audio/motif_obsession.py versions); 'trailer': the cold open (score.render_trailer). The sweet tune plays while she
# moves. 'until' (an anchor) sets len; anchors inside 'warp_at', 'stop', 'stop_at', 'waves', 'hits', 'silence' are
# resolved to film seconds ('warp_at' to seconds after the event).
IDENTITY = [
    # THE TRAILER: three waves (the three "If..." lines), a hard stop after "Wake a grown-up.", ONE silence, the last
    # line "I know who it is.", then the hook. film.py's own 'trailer' event (picture hit times, silence) wins.
    ('s0', 'trailer', 0.85, None,
     dict(stop='end:Wake a grown-up +0.12', waves=['s0', 'If your phone is off -0.25', 'And if you look down at midnight -0.25'],
          hits=['If your phone is off#lights', 'And if you look down at midnight#smiling', '...don\'t go down -0.05',
                'end:Wake a grown-up +0.1'],
          silence=['end:Wake a grown-up +0.12', 'I know who it is -0.05'])),
    # the tape at seven, on the swings: THE TAPE SONG from the camcorder, little Adam's chant on top (voice track)
    ('At seven, on the swings -0.4', 'show', 0.42, None, dict(until='end:I made it up. Nobody else knows it +0.6',
                                                            space='tape', stop='fade', fade=0.4)),
    # Evie arrives: the tune rotted, far, as she sits behind him
    ('That day, a new girl sat behind me', 'winks', 0.3, 6.0, dict(depth=0.5)),
    # Wednesday: she doesn't blink
    ("Wednesday, at my shoulder", 'winks', 0.36, None, dict(until='We\'d met on Monday +0.5', depth=0.8)),
    # rule 1: the pings, one note each: the looped run under "Every ping, one note of my song."
    ('Every ping, one note of my song -0.1', 'jingle', 0.45, None,
     dict(version='pings', loops=2, accel=0.6, until='"Are you awake?" -0.1', stop='fade', fade=0.02)),
    # the streetlight: she lies flat and slides away (she moves: the sweet tune, rotted)
    ('Under the streetlight, Evie smiled up', 'winks', 0.42, None, dict(until='Thursday morning, our path -0.3',
                                                                       stop='fade', depth=1.0)),
    # rule 2 / rule 3 nights
    ('That night, ONLY ME was halfway up our path', 'winks', 0.45, 7.0, dict(depth=1.1)),
    ('Two a.m. Her dot was on our house', 'winks', 0.5, None, dict(until='I swung my torch -0.1', stop='drag', depth=1.2)),
    # rule 4: the swings: her perfect bright version (music box + glockenspiel), then the car
    ('At break, on the swings, she sang my song -0.2', 'jingle', 0.4, None,
     dict(version='swings', until='I found Danny -0.2', stop='fade', fade=0.05)),
    # the square: my song from the square, slowed, in my seven-year-old voice: THE TAPE, warping, dragging to a halt
    #   on "I was." (reveal 1)
    ('From the square, slowed down, came my song -0.2', 'show', 0.5, None,
     dict(until='I was. Last Sunday -0.3', space='far', warp=0.9, warp_at='I told you nobody was cruel enough', stop='drag',
          fade=0.6, off=50.0)),
    # the chalk stands up: Evie, washed in red (she moves)
    ('The chalk slid out', 'winks', 0.6, None, dict(until='Floodlight. The caretaker -0.15', stop='cut', depth=1.3)),
    # rule 5: the neck stretching up toward his window
    ("Evie's neck was bending", 'winks', 0.62, None, dict(until='Rule number six -0.4', stop='drag', depth=1.4)),
    # rule 6: hummed through the letterbox, slow and a semitone flat, a chalk scrape on every beat
    ('Through the slot, a smile, ear to ear -0.1', 'jingle', 0.5, None,
     dict(version='letterbox', until='"After everything I gave you." -0.15', stop='fade', fade=0.1)),
    # "It says your name." ... "From me." (reveal 2): the rotted tune drags to a halt into the silence
    ('Lina, under the bare bulb', 'winks', 0.45, None, dict(until='From me. -0.3', stop='drag', depth=1.2)),
    # rule 7: the pings again, slower and lower, under Mom saving; they STOP DEAD on Block
    ('Mom saved every message from Evie -0.1', 'jingle', 0.42, None,
     dict(version='block', phrases='12', until='Then I scrolled to Danny -0.1', stop_at='Then I scrolled to Danny -0.35',
          stop='fade', fade=0.02)),
    # the replay at Danny's blue door ("It was me.", reveal 3): the tape rewinds (rule-7 cold-open replay), drags to a halt
    ('Sunday. Midnight. Chalk-white sleeves', 'show', 0.45, None,
     dict(until='It was me. -0.3', space='tape', warp=0.6, warp_at='Smiling up at his dark window', stop='drag',
          off=60.0, fade=0.3)),
    # the doormat: "Write your name?" sweet again: the tune, rotted, then her own song stretched thin (voice) and cut
    ('Evie was on our doormat', 'winks', 0.5, None, dict(until="Write your name? No. I'm not -0.1", stop='drag', depth=1.0)),
    # dawn: Lina's healed song in a major key under her (her key, D-flat): bent onto her bars
    ('Me and you, and others too#Me -0.05', 'jingle', 0.38, None,
     dict(version='healed', until="end:I'll still care, wherever you are +2.5", stop='fade', fade=0.05,
          anchors=[(0.0, 'Me and you, and others too#Me'), (4.0, 'friends for me and friends for you#Friends'),
                   (8.0, 'Go wherever, near or far#Go'), (12.0, "I'll still care, wherever you are#I'll"),
                   (16.0, "end:I'll still care, wherever you are")])),
    # the coda: ONLY. on the path: the tape song far away, once, dragging out
    ('Next morning, one chalk word on my path', 'show', 0.28, None,
     dict(until='I scrubbed it off -0.2', space='far', stop='drag', off=70.0, fade=0.5)),
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
        try:                                            # the timeline's own per-line words (the edited voice)
            _WORDS = sorted((_norm(w), float(t)) for l in json.load(open(TIMELINE))['lines'] for w, t in l.get('words') or [])
            _WORDS = [(w, t) for w, t in sorted(_WORDS, key=lambda x: x[1])]
        except Exception:
            _WORDS = []
        if not _WORDS:
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
    """THEO'S ADDRESS SONG's versions (score.py 'jingle', MOTIF_MODULE). 'until' sets len; 'anchors' [(beat, anchor)]
    become film seconds; 'gap_at' moves the start so the version's LAST note lands on that anchor."""
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
                    CH = importlib.import_module(MOTIF_MODULE)
                    kw = {k: x[k] for k in ('phrases', 'amount', 'inst', 'tempo', 'hush') if k in x}
                    t = g - CH.gap_time(x.get('version'), loops=int(x.get('loops') or 1), short=bool(x.get('short')), **kw)
                except Exception as e:
                    print(f'[music_plan] WARNING: motif gap time failed ({repr(e)[:60]})', flush=True)
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
        if isinstance(x.get('warp_at'), str):                # Obsession: anchors inside the extras
            wa = _try(x['warp_at'], lines, 'identity warp')
            x['warp_at'] = round(max(0.0, wa - t), 3) if wa is not None else None
            if x['warp_at'] is None:
                x.pop('warp_at')
        for k_ in ('stop_at', 'stop'):
            if isinstance(x.get(k_), str) and x[k_] not in ('fade', 'cut', 'drag'):
                v_ = _try(x[k_], lines, 'identity ' + k_)
                if v_ is None:
                    x.pop(k_)
                else:
                    x[k_] = round(v_, 3)
        for k_ in ('waves', 'hits', 'silence'):
            if isinstance(x.get(k_), list):
                vs = [_try(q, lines, 'identity ' + k_) if isinstance(q, str) else q for q in x[k_]]
                x[k_] = [round(v, 3) for v in vs if v is not None]
                if k_ == 'silence' and len(x[k_]) != 2:
                    x.pop(k_)
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
