"""music_plan.py: the music map of "If Your Little Brother Says Someone Lives In The Walls... DON'T LAUGH" (Night
Policy), built the earlier films' way (intensity curve, tension events, score.py), anchored to the script's WORDS:
every anchor names a phrase of script/narration_en.txt and is found in the timeline's line texts at run time
(W/align/timeline.json; word onsets from each line's own 'words'), so a re-paced voice edit needs no change here.
Nothing is a hard-coded film time. The dialogue tags are cut from the voice track, so no anchor uses one.

Anchors (resolve(anchor, lines)):
    'Rule number one'              the start of the line holding that phrase (case and punctuation ignored)
    'end:Human teeth'              the end of the line holding the phrase's LAST word
    'whispered, Off#Off'           the onset of the word 'Off' inside the line that holds it (timeline words)
    ... +0.4 / ... -1.2            an offset in seconds (a space, then the signed number, at the very end)
    'sN' / 'eN' / 'wN:word'        a line index form (kept for tools), or plain seconds
An anchor that is not found is skipped with a warning (the row drops out; the mix never fails on the plan).

The arc: quiet unease in the move-in (a pale pad), the first doorway and Hushabye on horror strings and a sinister
lullaby; then rule by rule the bed thickens (ARC): the locks on a low pulse, the pantry wall (the eye), the warm
armchair on a sparse sad piano, the attic switch ("Off."), the address song and the voice in the wall repeating the
note, the 3 a.m. doorway building on Irene to the snore, the mask and the tuck-in; the closet slide and the walk down
the hall on a dark pulse, a low drone under the calm 911 call, the CLIMAX (scratching around the room, the vent) at
intensity 1.0; then the police relief (a warm pad under the sirens and boots), the dead space and the unmasked old
man on a sad piano, one last chill at the fresh pencil mark, rule seven warm and pale, and a warm outro.
Silences sit before the big scares; boosted hits (+6..+10 LU momentary, smooth releases) land in the voice edit's
scare beats just after their words: "Your dad is asleep.", the eye, "Off.", the snore, "Human teeth.", the vent,
"Dated last week."

The film's own sound (IDENTITY, score.py 'jingle' events = JINGLE_MODULE 'motif_walls' on the stem `show`): THEO'S
ADDRESS SONG (audio/motif_walls.py), an ORIGINAL child's tune, returning: a warped music-box phrase under the hook,
sweet under "My little brother Theo", the hush-a-bye lullaby after Theo names Hushabye, the toy piano after Theo sings
it (rule 5), a man humming it inside the wall (slow, low, wrong) before Pell's own line, the lullaby hummed in the room
at the tuck-in, the wall hum at its most warped (dragged down) while he scratches around the bedroom, the music box
warped under the pencil marks (it was HIS address too), and the motif warm after "Believe me." and at the very end,
resolving on the hush-a-bye lullaby. The motif never plays over a sung voice line (the voice track carries those).

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
MOTIF_MODULE = 'motif_walls'                               # the identity's renderer (score.JINGLE_MODULE)

# ---------------------------------------------------------------------------------------------------- arrangement
# (anchor, track slug, offset s in the varispeed track, why). Tracks and shifts: score.TRACKS (this film's table).
TRACK_MAP = [
    ('If your little brother says someone lives', 'are_you_alone_victor_lundberg', 0.0,
     'the hook: a dark sub drone that swells to one spike under the three "If... don\'t" lines'),
    ('My little brother Theo had seven rules', 'haunted_mind_etienne_roussel', 0.0,
     'the setup of the rules, every explanation wrong, three police cars to come: a slow mid build'),
    ('We moved into fourteen Larkspur Lane', 'afterthoughts_beyza', 0.0,
     'the move-in: heat wave, Pell\'s things, the frog, the note: quiet unease, no drums'),
    ('That first night, I woke up at three', 'come_closer_belladonna_strings', 0.0,
     'the first doorway: Dad who is not Dad, backing away'),
    ('The next night, Theo told us about Hushabye', 'sleep_forever_luella_gren', 0.0,
     'Hushabye and the hound mask taped into GONE FOREVER: a sinister lullaby'),
    ('Okay. Before rule two', 'turning_stones_stefan_ekstrom', 0.0,
     'the comment prompt: a pure low drone, room for the question'),
    ('Rule number one', 'the_logic_of_tyrants_hampus_naeselius', 0.0,
     'rule 1: the locks, the same door every morning, the deadbolt turning by itself: a dark low pulse'),
    ('Rule number two', 'dark_tunnels_ethan_sloan', 0.0,
     'rule 2: the food, the twisted bread bag, chewing in the pantry wall, the eye, the crawl'),
    ('Rule number three', 'the_haunted_luella_gren', 0.0,
     'rule 3: the warm armchair and the hidden drawings: sparse piano over a thin drone'),
    ('Rule number four', 'don_t_look_belladonna_strings', 0.0,
     'rule 4: Mrs. Dabrowski, the switch that does nothing, the light, "Off."'),
    ('Rule number five', 'midnight_wanderer_luella_gren', 0.0,
     'rule 5: the address song (the toy piano carries it), the man humming it in the wall'),
    ('Then the knocking started', 'escalation_jon_bjork', 0.0,
     'the voice in the wall repeats the note\'s excuses: a steady escalation to rule 6'),
    ('Rule number six', 'irene_kevin_dailey', 0.0,
     'rule 6 and 3 a.m.: near silent, building through the snore, the mask, the tuck-in'),
    ('He stood up, and he went into my closet', 'code_of_violence_dian_shuai', 0.0,
     'the closet slide, the walk down the hall past the open crack, the locked door, waking Dad'),
    ('Mom grabbed her phone and dialed', 'turning_stones_stefan_ekstrom', 40.0,
     'the 911 call: a low drone under the calm dispatcher and Theo\'s address'),
    ('So we stayed', 'one_step_away_dian_shuai', 0.0,
     'THE CLIMAX: the man in the walls looking for them, scratching around the room, the vent'),
    ('Then sirens', 'when_the_sun_sets_anna_landstrom', 0.0,
     'the police relief: a quiet warm pad under the sirens, the boots, the dead space and the empty box'),
    ('When Officer Reyes pulled the mask off', 'the_forgotten_memories_luella_gren', 0.0,
     'the unmasked tired old man, he never walked away, "That was my room": sparse sad piano'),
    ('The next morning, I found the pencil marks', 'dark_forebodings_ethan_sloan', 0.0,
     'the last chill: L age four, eight, twelve... and a fresh one, dated last week'),
    ('Rule number seven', 'end_of_rain_beyza', 0.0, 'rule 7: the blank line, "Believe me.": a pale warm pad'),
    ('Okay. Breathe', 'at_first_light_gavin_luke', 0.0, 'the outro: lights on, none of this happened, the real list'),
    ('Now. Go back to the word', 'in_those_hazel_eyes_tall_oak_town', 0.0,
     'the comment payoff ("Person."), like, subscribe, "Believe him." (the motif resolves on top)'),
]

# slug -> share of the track's own dynamics evened out (score.FLATTEN 0.3 otherwise)
FLATTEN = {'are_you_alone_victor_lundberg': 0.3, 'haunted_mind_etienne_roussel': 0.45, 'afterthoughts_beyza': 0.5,
           'come_closer_belladonna_strings': 0.4, 'sleep_forever_luella_gren': 0.45,
           'turning_stones_stefan_ekstrom': 0.5, 'the_logic_of_tyrants_hampus_naeselius': 0.4,
           'dark_tunnels_ethan_sloan': 0.4, 'the_haunted_luella_gren': 0.45, 'don_t_look_belladonna_strings': 0.4,
           'midnight_wanderer_luella_gren': 0.5, 'irene_kevin_dailey': 0.3, 'when_the_sun_sets_anna_landstrom': 0.6,
           'the_forgotten_memories_luella_gren': 0.45, 'end_of_rain_beyza': 0.6, 'at_first_light_gavin_luke': 0.55,
           'in_those_hazel_eyes_tall_oak_town': 0.55}
# slug -> level trim (dB): the sub drones and very quiet pads read quiet (catalogue LUFS: end of rain -20.7, sun sets
# -20.9, afterthoughts -14.8 with long near-silent stretches); the loud warm ones down (hazel eyes -9.3)
GAIN = {'are_you_alone_victor_lundberg': 2.0, 'turning_stones_stefan_ekstrom': 4.5, 'afterthoughts_beyza': 1.5,
        'end_of_rain_beyza': 3.0, 'when_the_sun_sets_anna_landstrom': 3.0, 'irene_kevin_dailey': 1.0,
        'don_t_look_belladonna_strings': 2.5, 'come_closer_belladonna_strings': 3.0, 'sleep_forever_luella_gren': 2.5,
        'dark_forebodings_ethan_sloan': 2.5, 'one_step_away_dian_shuai': -1.0, 'escalation_jon_bjork': 3.0,
        'in_those_hazel_eyes_tall_oak_town': -3.0, 'at_first_light_gavin_luke': -1.0}

# ---------------------------------------------------------------------------------------------------- intensity
INTENSITY = [
    # the hook, then the setup of the rules
    ('If your little brother says', 0.55), ('And if your dad stands in your bedroom doorway', 0.65),
    ('Your dad is asleep', 0.75), ('My little brother Theo had seven rules', 0.3), ('Every explanation was wrong', 0.38),
    ('By morning, there would be three police cars', 0.45),
    # the move-in (the calmest stretch), the first doorway, Hushabye
    ('We moved into fourteen Larkspur Lane', 0.18), ('The old owner, Mr. Pell', 0.22), ('On the kitchen counter', 0.25),
    ('Dad read it out loud', 0.22), ('That first night, I woke up at three', 0.45), ('Just watching us sleep', 0.55),
    ('He just backed away', 0.5), ("In the morning, Dad couldn't find", 0.3),
    ('The next night, Theo told us about Hushabye', 0.35), ("Dad's old Halloween mask", 0.42), ('Nobody checked', 0.5),
    ("That's when Theo made his rules", 0.4), ('Okay. Before rule two', 0.25),
    # rule 1: the deadbolt
    ('Rule number one', 0.35), ('And every morning, one door was unlocked', 0.4),
    ('On the fifth night, I went down for water', 0.48), ('And I watched the deadbolt', 0.58), ('From the kitchen side', 0.6),
    ('There was nobody in the kitchen', 0.5),
    # rule 2: the pantry wall, the eye
    ('Rule number two', 0.38), ('Things went missing', 0.35), ("Because that's what we found, every time", 0.42),
    ('That night, I heard chewing', 0.55), ('There was a crack in the plaster', 0.6), ('An eye leaned in', 0.75),
    ('And then it was gone', 0.72), ('I told Dad. Dad said I was dreaming', 0.45),
    # rule 3: the armchair, the drawings
    ('Rule number three', 0.4), ("Mr. Pell's green armchair", 0.42), ('It was August', 0.45),
    ('I lifted the seat cushion', 0.5), ('Every drawing was the same', 0.58), ('Somebody had been taking them down', 0.55),
    # rule 4: the attic light
    ('Rule number four', 0.45), ('On Saturday, Mrs. Dabrowski', 0.35), ('That night at two, I stood', 0.55),
    ('Somewhere above me', 0.65), ('And a voice in the ceiling', 0.7), ('I wanted to open that closet', 0.55),
    ('Old wiring, Sam', 0.45),
    # rule 5: the song in the wall, the note's words
    ('Rule number five', 0.45), ('Theo had a song', 0.35), ('That night, I heard it through the wall', 0.55),
    ("In a man's voice", 0.62), ('Then the knocking started', 0.62), ("It wasn't Dad's voice", 0.66),
    ("They were the note's words", 0.68),
    # rule 6: 3 a.m.
    ('Rule number six', 0.5), ('That night, at three, I woke up', 0.55), ('And then, from down the hall', 0.7),
    ('The man in the doorway stepped', 0.78), ('The moonlight hit his face', 0.8), ('He knelt down beside', 0.75),
    ('Then the dog face turned', 0.82), ('He stood up, and he went into my closet', 0.75), ('I did not scream', 0.7),
    ('I picked Theo up', 0.78), ("Mom and Dad's door", 0.72), ('My dad looked at my face', 0.6),
    # the call, THE CLIMAX
    ('Mom grabbed her phone', 0.62), ('And my mom, in a brand new house', 0.66), ('Theo could', 0.55),
    ('Stay in that room', 0.6), ('So we stayed', 0.8), ('Scratching, inside the bedroom wall', 0.88),
    ('Behind the headboard', 0.95), ('Then the vent by the floor rattled', 1.0),
    # the police relief, the dead space, the pencil marks
    ('Then sirens', 0.55), ('Heavy boots on the stairs', 0.5), ('The officers found him', 0.4),
    ('He was wearing the mask', 0.45), ('When Officer Reyes pulled the mask off', 0.38), ('He never walked away', 0.42),
    ('He had lived in our walls', 0.5), ('On the way to the car', 0.4),
    ('The next morning, I found the pencil marks', 0.4), ('And one more, higher', 0.55), ('Dated last week', 0.62),
    # rule 7 and the warm outro
    ('Rule number seven', 0.35), ('Rule seven was two words', 0.3), ('Okay. Breathe', 0.18),
    ("So here's the real list", 0.25), ('Now. Go back to the word', 0.3), ('There was a third word', 0.4),
    ('If this story made you go check', 0.3), ('Sleep well', 0.25),
]

# the bed thickens rule by rule (the move-in the calmest, the climax the loudest): (from, to, + intensity)
ARC = [('Rule number two', 'Rule number three', 0.02), ('Rule number three', 'Rule number four', 0.04),
       ('Rule number four', 'Rule number five', 0.05), ('Rule number five', 'Rule number six', 0.07),
       ('Rule number six', 'Then sirens', 0.08)]

# ---------------------------------------------------------------------------------------------------- events
# (anchor, type, level, len, extra). Hits: 'boost' (>= 3.5 -> +10 LU momentary over the voice, >= 2.5 -> +9, else
# +8) only on the biggest scares, each in the voice edit's scare beat just after its word (the gaps measured on the
# timeline: 0.5-1.1 s). Silences sit under the line before the scare and end on it ('level' >= 0.95 would also mute
# the SFX: never used here, the deadbolt, the snore and the vent must stay). 'nosnap' keeps a word's time.
EVENTS = [
    # the hook
    ('Your dad is asleep -1.1', 'silence', 0.85, 1.05),
    ('end:Your dad is asleep +0.06', 'hit', 0.8, None, {'boost': 2.5, 'nosnap': True}),
    ('Every explanation was wrong', 'sub_drop', 0.4, None),
    ('Nobody checked', 'sub_drop', 0.45, None),
    # rule 1: the deadbolt turns by itself (the bed dips while it turns; the SFX carries the click)
    ('Rule number one -0.1', 'rule', 0.6, None, {'nosnap': True}),
    ('Slowly. All by itself', 'silence', 0.7, 2.3),
    ('From the kitchen side', 'sub_drop', 0.5, None),
    # rule 2: the eye in the plaster crack
    ('Rule number two -0.1', 'rule', 0.6, None, {'nosnap': True}),
    ('That night, I heard chewing', 'pulse_on', 0.4, None),
    ('An eye leaned in on the other side -1.0', 'silence', 0.8, 0.95),
    ('end:An eye leaned in on the other side +0.05', 'hit', 0.9, None, {'boost': 3.0, 'nosnap': True}),
    ('It blinked', 'sub_drop', 0.5, None),
    ('And then it was gone', 'swell', 0.6, 5.0),                          # the crawl away inside the wall
    ('I told Dad. Dad said I was dreaming', 'pulse_off', 0.4, None),
    # rule 3: the drawings
    ('Rule number three -0.1', 'rule', 0.6, None, {'nosnap': True}),
    ('Every drawing was the same', 'swell', 0.45, 5.0),
    ('In a red shirt', 'sub_drop', 0.45, None),
    # rule 4: the switch that does nothing, the light, "Off."
    ('Rule number four -0.1', 'rule', 0.6, None, {'nosnap': True}),
    ('Somewhere above me, in a place that was sealed#light', 'hit', 0.55, None),
    ('whispered, Off#Off -1.45', 'silence', 0.9, 1.4),
    ('end:whispered, Off +0.05', 'hit', 0.85, None, {'boost': 2.5, 'nosnap': True}),
    # rule 5: the address song in a man's voice, the note's words
    ('Rule number five -0.1', 'rule', 0.6, None, {'nosnap': True}),
    ("In a man's voice", 'sub_drop', 0.5, None),
    ('Then the knocking started', 'pulse_on', 0.5, None),
    ("They were the note's words", 'sub_drop', 0.5, None),
    # rule 6: 3 a.m. -- the snore, the mask, the tuck-in, the closet
    ('Rule number six -0.1', 'rule', 0.65, None, {'nosnap': True}),
    ('And then, from down the hall -0.2', 'silence', 0.85, 3.6),           # the house holds its breath for the snore
    ('end:I heard my dad snore +0.1', 'hit', 0.95, None, {'boost': 3.5, 'nosnap': True}),
    ('The man in the doorway stepped', 'pulse_on', 0.6, None),
    ('end:Human teeth +0.05', 'hit', 0.85, None, {'boost': 2.5, 'nosnap': True}),
    ('end:Shhh. Just the pipes +0.05', 'sub_drop', 0.55, None),
    ('Then nothing -0.05', 'silence', 0.85, 1.6),
    ('I picked Theo up', 'pulse_on', 0.6, None),
    ('Mom grabbed her phone', 'pulse_off', 0.45, None),
    # THE CLIMAX: scratching around the room, the vent
    ('Scratching, inside the bedroom wall', 'swell', 0.75, 8.0),
    ("end:Hush-a-bye. That's my house +0.1", 'hit', 0.9, None, {'boost': 3.0, 'nosnap': True}),
    # the dead space, the unmasking, the pencil marks
    ('Empty', 'sub_drop', 0.4, None),
    ('Lawrence Pell', 'sub_drop', 0.35, None),
    ('Fresh pencil -0.15', 'silence', 0.75, 1.3),
    ('end:Dated last week +0.08', 'hit', 0.8, None, {'boost': 2.5, 'nosnap': True}),
    ('Rule number seven -0.1', 'rule', 0.55, None, {'nosnap': True}),
]

# ---------------------------------------------------------------------------------------------------- identity
# THEO'S ADDRESS SONG (audio/motif_walls.py; score.py 'jingle' events). (anchor, type, level, len, extra): 'version',
# 'until' (an anchor: sets len), stop ('fade' | 'cut' | 'drag'), fade (fade-in s), loops, phrases, amount, inst,
# tempo, anchors [(beat, anchor)], 'gap_at' (an anchor: the event starts so that the version's LAST note lands there).
IDENTITY = [
    # the hook: the first phrase on a warped music box, before anyone explains anything
    ('If your little brother says -0.2', 'jingle', 0.4, None,
     dict(version='first', amount=0.6, until='If the armchair is warm -0.2', stop='fade', fade=0.05)),
    # Theo, six: the same phrase sweet
    ('My little brother Theo had seven rules -0.3', 'jingle', 0.35, None,
     dict(version='first', amount=0.0, until='I was twelve -0.2', stop='fade', fade=0.05)),
    # "He sings hush-a-bye, hush-a-bye.": the lullaby, faint, as the parents look at each other
    ('Mom and Dad looked at each other -0.3', 'jingle', 0.35, None,
     dict(version='hush', inst='box', amount=0.3, until="Dad's old Halloween mask -0.2", stop='fade', fade=0.4)),
    # rule 5: after Theo sings it, the toy piano keeps singing it "fifty times a day"
    ('He sang it fifty times a day -0.25', 'jingle', 0.45, None,
     dict(version='toy', tempo=112.0, until='That night, I heard it through the wall -0.4', stop='fade', fade=0.05)),
    # "...through the wall by my bed. But not in Theo's voice. In a man's voice. Slow. Low. Wrong.": he hums it
    # inside the wall ("Fourteen Larkspur Lane..."), and stops before his own line
    ('That night, I heard it through the wall +1.6', 'jingle', 0.5, None,
     dict(version='wall', amount=0.7, phrases='A', until="Fourteen Larkspur Lane... that's my house -0.35",
          stop='fade', fade=0.8)),
    # the tuck-in: after his whispered "Hush-a-bye," the lullaby hummed in the room, until "Shhh."
    ('Then the dog face turned -0.2', 'jingle', 0.4, None,
     dict(version='hush', inst='hum_room', amount=0.5, until='Shhh. Just the pipes -0.3', stop='fade', fade=0.5)),
    # the climax: the man in the walls, humming it at its most warped while he scratches around the room; dragged
    # down before the vent
    ('And the man in the walls came looking for us', 'jingle', 0.5, None,
     dict(version='wall', amount=1.0, phrases='ABCD', tempo=62.0, until='Then the vent by the floor rattled -0.1', stop='drag',
          fade=1.0)),
    # the pencil marks: it was HIS address too: the music box, warped
    ('The next morning, I found the pencil marks -0.2', 'jingle', 0.42, None,
     dict(version='box', amount=0.5, until='Fresh pencil -0.25', stop='fade', fade=0.3)),
    # "Believe me.": the motif warm (That's my house / That's my name / mm)
    ('end:Believe me +0.25', 'jingle', 0.42, None,
     dict(version='warm', short=True, until="So here's the real list -0.3", stop='fade', fade=0.3)),
    # the very end: warm, resolving on the hush-a-bye lullaby; its home note just after "Believe him."
    ('If this story made you go check', 'jingle', 0.4, None,
     dict(version='warm', phrases='CDH1H2H3', gap_at='end:Believe him +0.7', stop='fade', fade=1.0)),
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
