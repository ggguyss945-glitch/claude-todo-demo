"""music_plan.py: the music map of "If Your Mom's Eyes Turn Into Buttons... DON'T KEEP HER SECRET" (Night Policy),
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
MOTIF_MODULE = 'motif_buttons'                             # the identity's renderer (score.JINGLE_MODULE)

# ---------------------------------------------------------------------------------------------------- arrangement
# (anchor, track slug, offset s in the varispeed track, why). Tracks and shifts: score.TRACKS (this film's table:
# every track on A or D, the Button Song's A major and its relative / subdominant minors).
TRACK_MAP = [
    ('If someone online says', 'are_you_alone_victor_lundberg', 0.0,
     'the hook: a dark sub drone that swells under the three "If... don\'t" lines and the Blank\'s "Button up"'),
    ('At eight, my mom and I wrote seven rules', 'the_haunted_luella_gren', 0.0,
     'the Brave List, a police officer in the kitchen at midnight: sparse piano, a thin high drone'),
    ('Mom worked twelve-hour help-line shifts', 'unvaried_elin_piel', 0.0,
     'the kitchen table, one finger, the jar, the coat in Barlow\'s window, her song: quiet unease, very low'),
    ('That night, in a game chat', 'sleep_forever_luella_gren', 0.0,
     'the wish, the grey head filling in, the buttons clicking on: a sinister lullaby in A'),
    ('Rule number one', 'haunted_mind_etienne_roussel', 0.0,
     'the photo out the window, the woman under the streetlight, the lobby door: a slow mid build'),
    ('Before rule two: one word, in the comments', 'turning_stones_stefan_ekstrom', 0.0,
     'the comment prompt: a pure low drone, room for the question'),
    ('Rule number two', 'come_closer_belladonna_strings', 0.0,
     'the box on the mat, the coat, the card, Mom going grey, the closet at 3 a.m.: horror strings'),
    ('Rule number three', 'i_m_the_villain_dream_cave', 0.0,
     'the snow-day pickup, the car, the sunglasses, the arm out of the window: a slow villain pulse'),
    ("But locks don't stop something in your pocket", 'dark_forebodings_ethan_sloan', 0.0,
     'half a secret: the flat dark drone under the ping and the tik'),
    ('Rule number four', 'don_t_look_belladonna_strings', 0.0,
     '2 a.m. at Mom\'s laptop, "Buttons.", the microwave door up / down: horror strings'),
    ('Rule number five', 'midnight_wanderer_luella_gren', 0.0,
     'Thursday dinner, the Blank in Mom\'s chair, "Only you.", the lamp, the windowsill'),
    ('Rule number six', 'irene_kevin_dailey', 0.0,
     'two minutes to midnight, Officer Mensah, "I couldn\'t see me.": near silent, then builds'),
    ('Behind the fridge, something unfolded', 'code_of_violence_dian_shuai', 0.0,
     'midnight: the creepy form unfolds, holding open the red coat: a dark pulsing build'),
    ('Rule number seven', 'one_step_away_dian_shuai', 0.0,
     'THE CLIMAX: the coat, the buttons, NO, the run, the marker, the long fingers an inch away'),
    ("She'd put buttons where I'd never looked -0.4", 'when_the_sun_sets_anna_landstrom', 0.0,
     'the relief after "Green.": a quiet warm pad; the Blank folds into an empty cardigan, Tik. Tik.'),
    ('Mom pulled out a tiny music box', 'end_of_rain_beyza', 0.0,
     'the real music box, the lock screen, "She did look.", the real words: a very quiet warm pad under the box'),
    ('My son is ten now', 'the_forgotten_memories_luella_gren', 0.0,
     'twenty-five years later, the empty jar, the chime down the hall: a sparse sad piano'),
    ('Under the streetlight, someone waved', 'are_you_alone_victor_lundberg', 30.0,
     'the sting: the wave at the window next to his, the grey head, "I don\'t know."'),
    ('Okay. Breathe', 'at_first_light_gavin_luke', 0.0,
     'the outro checklist: a calm bed, low, every word clear; no "next time" teaser'),
]

# slug -> share of the track's own dynamics evened out (score.FLATTEN 0.3 otherwise)
FLATTEN = {'are_you_alone_victor_lundberg': 0.3, 'the_haunted_luella_gren': 0.45, 'unvaried_elin_piel': 0.5,
           'sleep_forever_luella_gren': 0.45, 'haunted_mind_etienne_roussel': 0.45,
           'turning_stones_stefan_ekstrom': 0.5, 'come_closer_belladonna_strings': 0.4,
           'i_m_the_villain_dream_cave': 0.4, 'dark_forebodings_ethan_sloan': 0.4,
           'don_t_look_belladonna_strings': 0.4, 'midnight_wanderer_luella_gren': 0.5, 'irene_kevin_dailey': 0.3,
           'code_of_violence_dian_shuai': 0.4, 'one_step_away_dian_shuai': 0.35,
           'when_the_sun_sets_anna_landstrom': 0.6, 'end_of_rain_beyza': 0.6,
           'the_forgotten_memories_luella_gren': 0.45, 'at_first_light_gavin_luke': 0.6}
# slug -> level trim (dB): quiet pads up (end of rain -20.7, sun sets -20.9 LUFS), the outro bed down (low under the
# checklist: every word clear)
GAIN = {'are_you_alone_victor_lundberg': 2.0, 'turning_stones_stefan_ekstrom': 4.5, 'unvaried_elin_piel': 1.0,
        'end_of_rain_beyza': 3.0, 'when_the_sun_sets_anna_landstrom': 3.0, 'irene_kevin_dailey': 1.0,
        'don_t_look_belladonna_strings': 2.5, 'come_closer_belladonna_strings': 3.0, 'sleep_forever_luella_gren': 2.0,
        'dark_forebodings_ethan_sloan': 2.5, 'one_step_away_dian_shuai': -1.0, 'at_first_light_gavin_luke': -4.0}

# ---------------------------------------------------------------------------------------------------- intensity
INTENSITY = [
    # the hook, then the setup (the Brave List, the police at midnight)
    ('If someone online says', 0.55), ('If a present says', 0.62), ('And if your mom holds your coat open', 0.7),
    ('Your real mom is in the kitchen', 0.6), ('At eight, my mom and I wrote', 0.3), ('At eleven, I broke four', 0.35),
    ('By midnight on my birthday', 0.45), ('I kept the buttons', 0.35),
    # the kitchen (the calmest stretch), her song, the chat
    ('Mom worked twelve-hour help-line shifts', 0.18), ('When I was little, she buttoned', 0.15),
    ('She hadn\'t sung it in years', 0.2), ('That night, in a game chat', 0.32), ('With every word, the grey head', 0.4),
    ('Two black buttons clicked onto the face', 0.55), ('So I named her', 0.45), ('Her kind hunt one thing', 0.4),
    # rule 1: the streetlight
    ('Rule number one', 0.35), ('A photo out my window', 0.4), ('That night, a woman stood', 0.55),
    ('Two black buttons flashed', 0.68), ('She was waving at the window next to mine', 0.6), ('I ducked', 0.66),
    ('She was at our lobby door', 0.7), ('I looked again. Gone', 0.55), ("She wasn't far away", 0.5),
    ('Before rule two: one word', 0.25),
    # rule 2: the box, the coat, 3 a.m.
    ('Rule number two', 0.38), ('Tuesday, a box on our doormat', 0.4), ('I hid it in my closet', 0.45),
    ('That night, rule two faded', 0.45), ('Three a.m. Inside my closet', 0.55), ('I opened the closet', 0.62),
    ('Full. Like somebody was inside it', 0.72), ('Then, slowly, it sagged', 0.6),
    # rule 3: the car
    ('Rule number three', 0.42), ('Wednesday pickup', 0.45), ('The door swung open', 0.55),
    ('Mom never got off early', 0.58), ('First ring', 0.6), ('She lowered the sunglasses', 0.75),
    ('Her arm slid out of the window', 0.82), ('I ran to Mr. Dunn', 0.7), ('You did right', 0.5),
    ('The arm folded back in', 0.45), ('Mom came running', 0.35), ('Rule three stayed blue', 0.3),
    ("But locks don't stop something", 0.4), ('Half a secret is still a secret', 0.48),
    # rule 4: 2 a.m., the microwave door
    ('Rule number four', 0.45), ('Two in the morning', 0.5), ('She sat at her laptop', 0.55),
    ('She turned, and took the glasses off', 0.75), ('I glanced at Mom\'s door', 0.66),
    ("It's not a secret. It's a surprise", 0.6), ('With a surprise, everyone finds out soon', 0.45),
    ('After school, Mom sat behind me', 0.55), ('And the Blank. Standing behind me', 0.68), ('Mom looked down', 0.74),
    ("The Blank's chin was almost on my shoulder", 0.8),
    # rule 5: dinner, the lamp, the windowsill
    ('Rule number five', 0.5), ('Thursday dinner', 0.45), ('In Mom\'s chair sat the Blank', 0.62),
    ('I waved at my mom', 0.62), ("For one second, I couldn't tell", 0.66), ('The Blank leaned in', 0.7),
    ('I heard myself', 0.7), ('On my closet door, every line but rule three', 0.6), ('The Blank stood', 0.72),
    ('That night, Mom sat on my windowsill', 0.6), ('The headset lady was still on the phone', 0.55),
    # rule 6: midnight
    ('Rule number six', 0.52), ('Two minutes to midnight', 0.55), ("I couldn't see me", 0.75),
    ("She wasn't ignoring me", 0.6), ('So I kept rule six', 0.55), ('Midnight. My birthday', 0.75),
    ('Behind the fridge, something unfolded', 0.85), ('Happy birthday. She can\'t hear you', 0.85),
    # rule 7: THE CLIMAX
    ('Rule number seven', 0.6), ('She wrapped the coat around me', 0.78), ('Six closed', 0.8),
    ('The top one waited', 0.82), ('My fingers rose', 0.85), ('As loud as I could', 0.9),
    ('She was left holding a red coat', 0.85), ('Those buttons were blind', 0.75), ('And I told my mom', 0.72),
    ('I grabbed the fridge marker', 0.85), ('The marker squeaked', 0.92), ('Officer Mensah read it first', 0.85),
    ('So I wrote everything', 0.85), ('With every word, I came back', 0.9), ('The long fingers were an inch', 1.0),
    ('And my mom\'s eyes found me', 0.9), ('The Blank froze', 0.8), ('Mom stepped between us', 0.65),
    ('And I looked into my mother\'s eyes', 0.55),
    # "Green." the relief, the empty cardigan, the real music box
    ("She'd put buttons where I'd never looked -0.4", 0.3), ('The Blank folded in on herself', 0.4),
    ('She dropped them in her jar', 0.3), ('From the empty cardigan', 0.22), ('Mom pulled out a tiny music box', 0.2),
    ('She did look', 0.18), ('None of this is your fault', 0.18), ('She wound the music box', 0.15),
    # the sting
    ('My son is ten now', 0.25), ('Tonight, the lid was off the jar', 0.4), ('The jar was empty', 0.48),
    ('Down the hall, my son\'s tablet chimed', 0.5), ('Under the streetlight, someone waved', 0.62),
    ('On his screen, a grey default head', 0.66), ('Look at me. How are you, really', 0.4),
    ('Brown. Your eyes are brown', 0.3), ('Face down on the bed', 0.45),
    # the outro: calm, low, every word clear
    ('Okay. Breathe', 0.15), ('Now. Buttons, or Mom', 0.18), ('Sleep well', 0.15),
]

# the bed thickens rule by rule (the kitchen the calmest, the climax the loudest): (from, to, + intensity)
ARC = [('Rule number two', 'Rule number three', 0.02), ('Rule number three', 'Rule number four', 0.04),
       ('Rule number four', 'Rule number five', 0.05), ('Rule number five', 'Rule number six', 0.06),
       ('Rule number six', "She'd put buttons where I'd never looked", 0.08)]

# ---------------------------------------------------------------------------------------------------- events
# (anchor, type, level, len, extra). Hits: 'boost' (>= 3.5 -> +10 LU momentary over the voice, >= 2.5 -> +9, else
# +8) only on the planned scares, each just after its word ('nosnap' keeps the word's time). Silences sit under the
# line before a scare and end on it. The bed dips (silence 0.6) under Mom's sung song: nothing doubles her voice.
EVENTS = [
    # the hook
    ("end:Button up, sweetheart. We're going home +0.05", 'hit', 0.85, None, {'boost': 2.5, 'nosnap': True}),
    ('Your real mom is in the kitchen', 'sub_drop', 0.45, None),
    ('By midnight on my birthday', 'sub_drop', 0.4, None),
    # her song (the voice carries it): the bed steps back
    ('One for warm and two for snug -0.3', 'silence', 0.6, 10.8),
    # the chat
    ('Two black buttons clicked onto the face', 'hit', 0.6, None),
    ('So I named her. The Blank', 'sub_drop', 0.45, None),
    # rule 1: the streetlight
    ('Rule number one -0.1', 'rule', 0.6, None, {'nosnap': True}),
    ('Headlights swept her face -0.2', 'silence', 0.7, 1.5),
    ('end:Two black buttons flashed +0.05', 'hit', 0.85, None, {'boost': 2.5, 'nosnap': True}),
    ('She was at our lobby door', 'pulse_on', 0.45, None),
    ('I looked again. Gone', 'pulse_off', 0.4, None),
    ('wearing my mom', 'sub_drop', 0.5, None),
    # rule 2: the coat in the closet
    ('Rule number two -0.1', 'rule', 0.6, None, {'nosnap': True}),
    ('Like a photo left in the sun', 'sub_drop', 0.4, None),
    ('Three a.m. Inside my closet', 'silence', 0.6, 3.0),
    ('The red coat hung there -0.1', 'silence', 0.8, 2.6),
    ('end:Like somebody was inside it +0.05', 'hit', 0.85, None, {'boost': 2.5, 'nosnap': True}),
    # rule 3: the car
    ('Rule number three -0.1', 'rule', 0.6, None, {'nosnap': True}),
    ('Pancakes were Saturdays', 'pulse_on', 0.5, None),
    ('She lowered the sunglasses -0.1', 'silence', 0.8, 1.3),
    ('end:She lowered the sunglasses. Buttons +0.05', 'hit', 0.9, None, {'boost': 3.0, 'nosnap': True}),
    ('Her arm slid out of the window', 'swell', 0.65, 5.0),
    ('You did right', 'pulse_off', 0.45, None),
    ('Half a secret is still a secret', 'sub_drop', 0.5, None),
    # rule 4: 2 a.m., the microwave door
    ('Rule number four -0.1', 'rule', 0.6, None, {'nosnap': True}),
    ('She turned, and took the glasses off -0.1', 'silence', 0.8, 1.6),
    ('end:She turned, and took the glasses off. Buttons +0.05', 'hit', 0.9, None, {'boost': 3.0, 'nosnap': True}),
    ('is a secret wearing a bow', 'sub_drop', 0.45, None),
    ('And the Blank. Standing behind me', 'pulse_on', 0.55, None),
    ("The Blank's chin was almost on my shoulder -0.1", 'silence', 0.75, 1.4),
    ("end:The Blank's chin was almost on my shoulder +0.08", 'hit', 0.85, None, {'boost': 2.5, 'nosnap': True}),
    # rule 5: dinner, the lamp
    ('Rule number five -0.1', 'rule', 0.6, None, {'nosnap': True}),
    ('Two black, shiny circles', 'sub_drop', 0.5, None),
    ('Only you', 'sub_drop', 0.55, None),
    ('Her head set the lamp swinging', 'hit', 0.7, None),
    # rule 6: midnight, the unfolding
    ('Rule number six -0.1', 'rule', 0.65, None, {'nosnap': True}),
    ("I couldn't see me -0.1", 'silence', 0.8, 1.0),
    ("end:I couldn't see me +0.05", 'hit', 0.9, None, {'boost': 3.0, 'nosnap': True}),
    ('Midnight. My birthday', 'pulse_on', 0.6, None),
    ('Behind the fridge, something unfolded', 'swell', 0.8, 8.0),
    ('Holding open -0.1', 'silence', 0.8, 1.6),
    ('end:Holding open... the red coat +0.05', 'hit', 0.95, None, {'boost': 3.5, 'nosnap': True}),
    # rule 7: THE CLIMAX
    ('Rule number seven -0.1', 'rule', 0.65, None, {'nosnap': True}),
    ('Six closed. -0.05', 'silence', 0.85, 2.4),                  # the song stops: the bed holds its breath
    ('As loud as I could -0.3', 'hit', 0.85, None, {'nosnap': True}),          # just after "NO!"
    ('I dropped down out of the coat and ran', 'pulse_on', 0.7, None),
    ('The marker squeaked. The Blank lunged', 'hit', 0.8, None),
    ('The long fingers were an inch from my hood', 'swell', 0.9, 4.0),
    ('The Blank froze. Mid-reach -0.05', 'silence', 0.9, 1.4),
    ("She'd put buttons where I'd never looked -0.4", 'pulse_off', 0.5, None),
    # the sting
    ('The jar was empty', 'sub_drop', 0.45, None),
    ('Under the streetlight, someone waved', 'hit', 0.65, None),
    ('On his screen, a grey default head', 'sub_drop', 0.5, None),
]

# ---------------------------------------------------------------------------------------------------- identity
# THE BUTTON SONG (audio/motif_buttons.py; score.py 'jingle' events). (anchor, type, level, len, extra): 'version',
# 'until' (an anchor: sets len), stop ('fade' | 'cut' | 'drag'), fade (fade-in s), loops, phrases (bars '1234'), n
# (notes played), amount, tempo, anchors [(beat, anchor)], 'gap_at'. It never doubles a sung line: Mom's song (line
# 'mom_one_for_warm') has no motif; the climax box is bent onto the Blank's own sung words and stops one note short;
# the real box under Mom's last line is bent onto her words so they agree. 'wN:word' anchors name timeline line N
# (316 = 'mom_mama_sees_you', whose words also open line 32: a phrase would find line 32).
IDENTITY = [
    # 2. the chat: Owen types "Our song." and a clean music box plays, quietly
    ('Our song -0.25', 'jingle', 0.3, None,
     dict(version='box', until='Two black buttons clicked onto the face -0.3', stop='fade', fade=0.2)),
    # 3. R2, 3 a.m.: inside the closet, the stolen music box winding down, too slow; it drags to a halt as he opens
    ('Then our song, slow -0.15', 'jingle', 0.42, None,
     dict(version='winddown', n=10, until='The red coat hung there -0.2', stop='drag', fade=0.15)),
    # 4. R3: hummed, slowed, through the car's open window
    ('Mom at the wheel in sunglasses -0.3', 'jingle', 0.42, None,
     dict(version='hum', until='Get in, sweetheart -0.25', stop='fade', fade=0.4)),
    # 5. R5: the windowsill: sung perfectly, like a recording, again and again (bars 3-4 looped, sample-exact)
    ('That night, Mom sat on my windowsill -0.2', 'jingle', 0.38, None,
     dict(version='sill', phrases='34', loops=3, tempo=78.0, until='Rule number six -0.35', stop='fade', fade=0.6)),
    # 6. R7: detuned, one button per beat, bent onto the Blank's sung words; STOPS with one note left (no "hug")
    ('warm two for snug#One -0.05', 'jingle', 0.45, None,
     dict(version='detuned', n=13, until='Six closed +0.4', stop='fade', fade=0.05,
          anchors=[(0.0, 'warm two for snug#One'), (0.75, 'warm two for snug#warm'), (1.5, 'warm two for snug#two'),
                   (2.0, 'warm two for snug#snug'), (3.0, 'warm two for snug#three'),
                   (3.75, "warm two for snug#mamma's"), (4.5, 'warm two for snug#button')])),
    # 7. aftermath: four notes from the empty cardigan (the real music box)
    ('From the empty cardigan#four -0.1', 'jingle', 0.35, None,
     dict(version='cardigan', until='Mom pulled out a tiny music box -0.1', stop='fade', fade=0.02)),
    #    Mom winds it and sings the real words: the real box, bar 4 on her "Mama sees you. Say goodnight."
    ('end:She wound the music box and sang along +0.1', 'jingle', 0.4, None,
     dict(version='real', phrases='34', until='My son is ten now +0.8', stop='fade', fade=0.05,
          anchors=[(3.0, 'w316:Mama'), (3.75, 'w316:sees'), (4.0, 'w316:you'), (4.5, 'w316:Say'),
                   (4.75, 'w316:goodnight')])),
    # 8. the sting: the son's tablet chimes the first four notes, down the hall, in the gap before the narrator names it
    ('Down the hall -0.6', 'jingle', 0.35, None,
     dict(version='chime', space='inside', until="end:Down the hall, my son's tablet chimed +1.0", stop='fade', fade=0.0)),
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
