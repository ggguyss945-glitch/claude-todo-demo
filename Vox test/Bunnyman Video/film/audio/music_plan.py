"""music_plan.py: the music map of "If The Bunnyman Asks You To Close Your Eyes... DON'T COUNT TO SEVEN", built the
police film's way (film.py intensity / polish_cues / score.py), anchored to the script lines and their words.

Two things live here:
1. The tension arc (the police way, AUDIO_SPEC): one dark Epidemic track section per film section (sections start at
   the rule cards and the turns of the story; varispeeded to D / A in score.TRACKS), gain automation following an
   intensity curve (the cold open strong, the second quarter the calmest, the climax around the count), swells into
   the reveals, risers, true music drop-outs under the line before a scare, hits and stingers on the reveals, a rule
   sting on every "Rule number N", the heartbeat pulse in the chases, the bed thickening rule by rule. The owner's new
   tracks carry the new colours: The Haunted (the woods, 1987), Sleep Forever (Mom with the yellow dress), The Cursed
   Path of Everlasting Loneliness (the real Laurie's thirty-six years), Mermaid's Story (the outro); the children's
   tunes are identity layers (below), never wallpaper. Silence where silence is stronger: the comment prompt (the
   tape is paused), "Then nothing.", the cut on "Seven".
2. The film's own sound (IDENTITY, score.py stem `show`): the ORIGINAL Pemberton's jingle (audio/jingle.py) coming
   back again and again, each time worse: the 1987 VHS commercial under the narrator's own "Hop, hop, hop along" in
   the cold open (every word on its note), the float's PA at the 1987 parade on a camcorder, the seven-year-old body
   humming it coming out of the woods, Mom humming it all week, the dying portable speaker in the woods at 11:07,
   Grandma's music box behind her memory, the real Laurie trying to sing it through the mail slot and breaking into
   tears, Mom humming it after "Bedtime, bunny.", the slow minor music box on "Close your eyes. And count to seven.",
   June's count on the same scale (One D, Two E, Three F ... Six Bb, Seven C#: it never reaches home, cut to
   silence), the old body humming it, and the cheerful outro that ends on a soft hum. Plus two of the owner's
   children's tunes: Mary Had a Little Lamb on the real Laurie's crayon diary (dragged to a halt when the handwriting
   changes) and Mr. Otter's Rainy Day for June turning seven.

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
# section start, track, offset (s, in the varispeed track), why. Tracks: score.TRACKS (shifts there).
TRACK_MAP = [
    ('s0', 'afterthoughts_beyza', 0.0,
     'cold open ("don\'t wave at him... don\'t open it... don\'t."), the jingle\'s story, "humming it ever since", the '
     'seven rules, the hospital: a slow, unpulsed F minor -> D minor dread (no drums), stepping right back under the '
     'VHS jingle'),
    ('s19', 'annihilated_blue_saga', 24.1,
     '1987: the Easter parade on a camcorder (the jingle from the float\'s PA, the crowd): a pale, quiet D-major pad '
     'under the PA tune (the jingle\'s own key)'),
    ('s29', 'the_haunted_luella_gren', 6.6,
     '"Then he walked off into Holloway Woods. And she followed him.": the owner\'s new dark track (G# -> A minor), '
     'sparse piano over a thin high drone: the dogs, the bridge, the girl walking out humming, the sightings ("fur '
     'matted dark... watching the houses")'),
    ('s45', 'dark_tunnels_ethan_sloan', 2.4,
     'the house at the end of Orchard Road, the porch light, Dad and the flashlight under the bridge, "Mom told them a '
     'lot of things": a flat sub drone (centroid 125 Hz) that leaves the voice alone'),
    ('s54', 'end_of_rain_beyza', 85.6,
     'June turns seven (Mr. Otter\'s Rainy Day, A), Mom humming all week (the jingle hummed in A), the yellow dress: a '
     'very quiet A-major pad (false calm) under them'),
    ('s61', 'a_massive_mist_ethan_sloan', 0.0,
     'rule 1 (11:07: the song from the woods, June at the window, he waves back, he points, Mom in the doorway): a very '
     'low drone (centroid 112 Hz) under the dying speaker\'s jingle, which carries the scene'),
    ('s92', 'dark_forebodings_ethan_sloan', 0.0,
     'the comment prompt: the tape is paused (a 20 s drop-out: the VHS pause hum alone); the drone is only there to '
     'come back on "Rule number two"'),
    ('s100', 'midnight_wanderer_luella_gren', 10.1,
     'rule 2 (the tap at midnight, the egg, the burn barrel, the rattle, the ring, "You opened it.", the pocket): '
     'E minor -> D minor, building to its loudest around the ring'),
    ('s130', 'turning_stones_stefan_ekstrom', 14.2,
     'rule 3 (the knocks, Grandma\'s family knock, "Not after the woods.", the secret knock): a pure dark drone that '
     'leaves the knocks and the memory clear'),
    ('s160', 'escalation_jon_bjork', 6.9,
     'rule 4 (the brass slot, "Mama?", Grandma dead six years, Mom calm, June at the slot, "Is she humming?", the girl '
     'crying, Mom humming): C minor -> D minor, a steady escalation'),
    ('s196', 'in_continuum_dream_cave', 0.0,
     'rule 5 (June gone, the attic light, the toy chest, the dress, the diary, "It is so nice to be small again", Mom in '
     'the dark corner): D minor, louder from its 50 s on the cursive pages'),
    ('s232', 'one_hampus_naeselius', 28.0,
     'rule 6 (the window explodes, the door crashes in, the bathtub, the hatchet on the stairs, the girl under the door, '
     'the drawing, GET OUT OF MY HOUSE, the fight): G minor, percussive, its dip landing on the drawing'),
    ('s282', 'tefu_sayuri_hayashi_egnell', 0.0,
     'rule 7 (we don\'t close our eyes; 6:12, the light turns gold, Mom so proud): the police film\'s D major false '
     'relief'),
    ('s294', 'are_you_alone_victor_lundberg', 60.0,
     '"Before sunrise. That\'s what the rule said." -> the key, the wrecked hall, the Bunnyman unmasked: the D drone '
     'whose one spike (its 93.5 s) lands on "...with the eyes of a terrified little girl."'),
    ('s313', 'sleep_forever_luella_gren', 14.1,
     'Mom kneels with the little yellow dress: the owner\'s sinister lullaby (G# -> A) under "Happy Easter, bunny. Want '
     'to see a magic trick?" and the first three counts'),
    ('s322', 'the_cursed_path_of_everlasting_loneliness_polar_nights', 6.2,
     'the reveal: the trade, the real Laurie under the bridge for thirty-six years, the recap of the rules, "Four. '
     'Five.", the swap, "Six. Seven." -> cut to silence: the owner\'s aching G-major build, the loudest music of the film'),
    ('s360', 'dark_forebodings_ethan_sloan', 30.0,
     'I open my eyes and see myself; it hums; I scream; the police; Holloway State Hospital: a flat G-minor drone'),
    ('s376', 'goth_christmas_par', 5.6,
     'Every Sunday, June visits; "I know it\'s you"; "Want to see a magic trick?"; Easter is in nine days: bells and a '
     'lullaby gone wrong (F# minor -> D minor)'),
    ('s386', 'mermaid_s_story_jerry_lacey', 0.0,
     'the outro ("Okay. Breathe."): the owner\'s calm harp lullaby (C -> D major), the jingle\'s outro after it in key'),
]

# slug -> share of the track's own dynamics evened out (score.FLATTEN 0.3 otherwise)
FLATTEN = {'afterthoughts_beyza': 0.5, 'the_haunted_luella_gren': 0.45, 'end_of_rain_beyza': 0.6,
           'annihilated_blue_saga': 0.55, 'midnight_wanderer_luella_gren': 0.4, 'mermaid_s_story_jerry_lacey': 0.6,
           'sleep_forever_luella_gren': 0.45, 'are_you_alone_victor_lundberg': 0.55}
# slug -> level trim (dB) of the track in its sections: the sub drones read quiet (dark_tunnels 125 Hz, a_massive_mist
# 112 Hz, dark_forebodings 174 Hz centroids: the delivery and dummy films measured +3 dB needed); the near-silent pads
# need lifting; the new melodic tracks (The Haunted, Sleep Forever, Cursed Path, Mermaid) are mid-band and loud: down
GAIN = {'dark_tunnels_ethan_sloan': 3.0, 'a_massive_mist_ethan_sloan': 2.0, 'dark_forebodings_ethan_sloan': 2.5,
        'end_of_rain_beyza': 3.0, 'annihilated_blue_saga': 3.0, 'are_you_alone_victor_lundberg': 4.0,
        'turning_stones_stefan_ekstrom': 3.0, 'the_haunted_luella_gren': -1.0, 'sleep_forever_luella_gren': -2.0,
        'the_cursed_path_of_everlasting_loneliness_polar_nights': -2.0, 'mermaid_s_story_jerry_lacey': -3.0,
        'midnight_wanderer_luella_gren': -1.0, 'tefu_sayuri_hayashi_egnell': -1.0}

# ---------------------------------------------------------------------------------------------------- intensity
INTENSITY = [
    # cold open: the woods, the warnings, then the bright jingle (the bed steps back), the jingle's story
    ('s0', 0.55), ('s1', 0.6), ('s2', 0.68), ('e2', 0.72), ('s3', 0.3), ('e6', 0.32), ('s7', 0.45), ('s8', 0.55),
    ('s10', 0.6), ('s11', 0.62), ('s12', 0.5), ('s14', 0.58), ('s15', 0.66), ('s16', 0.48), ('e18', 0.56),
    # 1987: the parade (bright), the woods, the sightings
    ('s19', 0.22), ('s24', 0.25), ('s28', 0.3), ('s29', 0.5), ('s31', 0.58), ('s32', 0.5), ('s35', 0.45),
    ('s36', 0.55), ('s37', 0.62), ('s39', 0.62), ('s40', 0.68), ('s42', 0.72), ('s44', 0.76),
    # the house, Dad
    ('s45', 0.42), ('s46', 0.4), ('s48', 0.52), ('s50', 0.62), ('s51', 0.6), ('s53', 0.66),
    # June turns seven, the hum, the dress (the calm quarter)
    ('s54', 0.32), ('s56', 0.36), ('s58', 0.42), ('s59', 0.48), ('s60', 0.52),
    # rule 1
    ('s61', 0.55), ('s65', 0.45), ('s69', 0.5), ('s71', 0.62), ('s73', 0.66), ('s76', 0.56), ('s80', 0.6),
    ('s82', 0.66), ('s86', 0.78), ('s87', 0.72), ('s88', 0.86), ('s90', 0.82), ('e91', 0.84),
    # the comment prompt (paused)
    ('s92', 0.15), ('e99', 0.18),
    # rule 2
    ('s100', 0.5), ('s104', 0.46), ('s106', 0.52), ('s109', 0.48), ('s112', 0.55), ('s114', 0.6), ('s116', 0.66),
    ('s119', 0.74), ('s124', 0.78), ('s125', 0.82), ('s127', 0.66), ('s129', 0.62),
    # rule 3
    ('s130', 0.55), ('s135', 0.42), ('e141', 0.45), ('s145', 0.6), ('s147', 0.4), ('s152', 0.5), ('e154', 0.56),
    ('s155', 0.6), ('s158', 0.72), ('s159', 0.78),
    # rule 4
    ('s160', 0.6), ('s164', 0.58), ('s167', 0.66), ('s168', 0.74), ('s172', 0.6), ('s176', 0.68), ('s177', 0.6),
    ('s180', 0.68), ('s184', 0.62), ('s186', 0.72), ('s189', 0.58), ('s192', 0.6), ('s195', 0.66),
    # rule 5
    ('s196', 0.64), ('s200', 0.62), ('s202', 0.76), ('s204', 0.78), ('s205', 0.66), ('s206', 0.56), ('s210', 0.46),
    ('s215', 0.6), ('s217', 0.7), ('e223', 0.8), ('s224', 0.82), ('s225', 0.86), ('s226', 0.72), ('s229', 0.86),
    ('s230', 0.92), ('s231', 0.86),
    # rule 6
    ('s232', 0.8), ('s236', 0.96), ('s241', 0.94), ('s244', 0.84), ('s245', 0.88), ('s251', 0.86), ('s253', 0.8),
    ('s257', 0.72), ('s260', 0.74), ('s264', 0.84), ('s265', 0.86), ('s267', 0.98), ('s270', 1.0), ('e273', 1.0),
    ('s274', 0.1), ('s275', 0.4), ('s279', 0.6), ('s281', 0.66),
    # rule 7
    ('s282', 0.62), ('s284', 0.5), ('s286', 0.38), ('s289', 0.42), ('s294', 0.66), ('s296', 0.76), ('s297', 0.8),
    ('s299', 0.86), ('s300', 0.8), ('s302', 0.86), ('s305', 0.9), ('s309', 0.96), ('s311', 0.6), ('s312', 0.62),
    ('s313', 0.7), ('s315', 0.8), ('s317', 0.86), ('s318', 0.88),
    # the reveal and the climax
    ('s322', 0.64), ('s324', 0.72), ('s326', 0.76), ('s333', 0.7), ('s337', 0.8), ('s340', 0.84), ('s342', 0.86),
    ('s346', 0.9), ('s350', 0.94), ('s351', 0.96), ('s354', 0.98), ('s355', 1.0), ('e359', 1.0),
    # after: myself, the scream, the police, the hospital, June's visits
    ('s360', 0.42), ('s364', 0.56), ('s365', 0.62), ('s367', 0.7), ('s370', 0.58), ('s371', 0.46), ('s376', 0.5),
    ('s381', 0.6), ('s383', 0.7), ('s384', 0.82), ('e385', 0.86),
    # the outro (calm, a little shadow on "Next time")
    ('s386', 0.25), ('s396', 0.28), ('s406', 0.3), ('s409', 0.42), ('s410', 0.3), ('e411', 0.3),
]

# ---------------------------------------------------------------------------------------------------- events
# (anchor, type, level, len[, extra]). Silences sit under the line before the scare and end on it; rule stings on every
# "Rule number N"; risers end on their anchor; 'nosnap' keeps a word's time when the picture has a hit nearby.
EVENTS = [
    # cold open
    ('e2-0.35', 'sub_drop', 0.55, None, {'nosnap': True}),            # "...count to seven... don't."
    ('e2', 'silence', 0.7, 0.45),                                      # a breath of nothing before the VHS jingle
    ('s8', 'swell', 0.5, 4.0),                                         # "...the last thing my mother heard before she disappeared."
    ('s9', 'stinger', 0.5, None),                                      # "She was seven years old."
    ('w15:him', 'hit', 0.6, None, {'nosnap': True}),                   # "...to protect us from him."
    ('s16', 'silence', 0.45, 0.8),                                     # "I'm telling you this from a hospital."
    ('e18', 'sub_drop', 0.5, None),                                    # "They just don't believe a word I say."
    # 1987
    ('s29', 'braam', 0.55, 3.0),                                       # "Then he walked off into Holloway Woods."
    ('e30', 'silence', 0.5, 0.75),                                     # "And she followed him." ->
    ('s31', 'riser', 0.45, 3.0),                                       # the dogs, the bridge
    ('e33', 'stinger', 0.45, None),                                    # "Her dress was spotless."
    ('s35', 'silence', 0.45, 1.2),                                     # "And she was humming." (the child's hum alone)
    ('s37', 'hit', 0.55, None),                                        # "Dale Whitlock was never found."
    ('e38', 'stinger', 0.55, None),                                    # "Neither was the suit."
    ('s39', 'swell', 0.6, 12.8),                                       # the sightings -> "Watching the houses."
    ('w44:houses', 'hit', 0.65, None),
    # the house, Dad
    ('s48', 'swell', 0.5, 6.5),                                        # Dad walks to the treeline -> "He never came back."
    ('s50', 'hit', 0.65, None),
    ('e51', 'sub_drop', 0.5, None),                                    # "...under the railroad bridge, still on."
    ('s53-0.15', 'silence', 0.55, 0.9), ('e53', 'stinger', 0.6, None),     # "Mom told them a lot of things."
    ('s55', 'stinger', 0.4, None),                                     # "The same age Mom was."
    ('s59', 'hit', 0.45, None),                                        # "Exactly like the one in the photo."
    ('s61-0.1', 'rule', 0.7, None, {'nosnap': True}),
    # rule 1
    ('s66', 'sub_drop', 0.45, None),                                   # "From the woods."
    ('w71:there', 'riser', 0.5, 3.0), ('w71:there', 'hit', 0.65, None), # "there he is."
    ('s73', 'stinger', 0.55, None),                                    # "Black glass eyes that don't reflect anything."
    ('s75-0.2', 'silence', 0.5, 0.9),                                  # "Slowly."
    ('s82', 'silence', 0.6, 1.4),                                      # the song dies; "Then the Bunnyman stops waving."
    ('s83', 'riser', 0.55, 3.2), ('e86+0.05', 'hit', 0.7, None),       # "...points. Not at June. Not at me. Past us."
    ('s87-0.1', 'silence', 0.7, 1.3),                                  # "I turn around."
    ('s88', 'hit', 0.85, None, {'boost': 3.0}),                        # "Mom is standing in the doorway."
    ('s90', 'swell', 0.5, 3.5), ('e91+0.05', 'stinger', 0.65, None),   # "She's smiling." / "I told you not to look..."
    # the comment prompt: the tape is paused
    ('s92-0.05', 'silence', 0.5, 21.2),
    ('s100-0.1', 'rule', 0.7, None, {'nosnap': True}),
    # rule 2
    ('w104:tap-0.6', 'silence', 0.5, 0.6),                             # "...one soft tap on the front door."
    ('s106', 'hit', 0.45, None),                                       # "Except for an egg on the doormat."
    ('s108', 'stinger', 0.45, None),                                   # "Stamped on the side: Pemberton's."
    ('s112', 'braam', 0.45, 2.5),                                      # "They smell sweet when they melt."
    ('s114-0.1', 'silence', 0.5, 1.1),                                 # "...the egg rattles."
    ('s118', 'riser', 0.55, 3.0), ('w119:gold', 'hit', 0.75, None),     # "...is a gold ring."
    ('s124', 'braam', 0.6, 3.0),                                       # "The Bunnyman has my father's wedding ring."
    ('s125-0.05', 'hit', 0.8, None, {'nosnap': True}),                 # "You opened it."
    ('s128+0.6', 'silence', 0.55, 1.5), ('s129', 'sub_drop', 0.55, None),   # "She puts it in her pocket."
    ('s130-0.1', 'rule', 0.7, None, {'nosnap': True}),
    # rule 3
    ('s135+1.2', 'silence', 0.4, 6.2),                                 # the knocks alone (2-3-2) and "Seven."
    ('e141+0.05', 'sub_drop', 0.5, None),
    ('w145:drops', 'sub_drop', 0.55, None),                            # "But my stomach drops..."
    ('s154-0.1', 'silence', 0.45, 1.6),                                # "Not after the woods."
    ('e158', 'hit', 0.7, None),                                        # "...knows my grandmother's secret knock."
    ('s159', 'swell', 0.55, 4.6), ('e159', 'stinger', 0.6, None),      # "...doesn't recognize it at all."
    ('s160-0.1', 'rule', 0.75, None, {'nosnap': True}),
    # rule 4
    ('s164-0.2', 'silence', 0.5, 1.0),                                 # "...the mail slot creaks open"
    ('w167:mama+0.5', 'stinger', 0.45, None, {'nosnap': True}),        # "Mama?"
    ('s168', 'braam', 0.65, 2.8),                                      # "Grandma has been dead for six years."
    ('s176', 'swell', 0.5, 3.8),                                       # "...to make children open doors."
    ('s180', 'riser', 0.45, 3.0),                                      # June crept down the stairs
    ('s184-0.05', 'silence', 0.6, 1.4),                                # "Silence."
    ('e186+0.1', 'stinger', 0.5, None, {'nosnap': True}),              # "Is she humming?"
    ('s192', 'sub_drop', 0.45, None),                                  # "Mom closes the mail slot."
    ('s196-0.1', 'rule', 0.75, None, {'nosnap': True}),
    # rule 5
    ('s202', 'hit', 0.7, None),                                        # "June is gone."
    ('s203', 'stinger', 0.5, None), ('s204', 'braam', 0.55, 2.5),      # "Mom's chair is empty." / "...locked from the inside."
    ('s205', 'riser', 0.45, 3.0),                                      # "There's a light under the attic door."
    ('s215-0.1', 'silence', 0.5, 0.8),                                 # "Then Easter, 1987." (the nursery drags to a halt)
    ('s217', 'swell', 0.55, 7.0),                                      # the cursive -> "I am Laurie..."
    ('s225-0.6', 'silence', 0.75, 1.5), ('e225+0.1', 'hit', 0.75, None),    # "It is so nice to be small again."
    ('s229', 'riser', 0.6, 3.5), ('s230', 'hit', 0.9, None, {'boost': 3.0}), # "...Mom says," / "Back to bed, you two."
    ('s231', 'stinger', 0.6, None),                                    # "I never saw her sitting there."
    ('s232-0.1', 'rule', 0.8, None, {'nosnap': True}),
    # rule 6
    ('w236:explodes-0.55', 'silence', 0.8, 0.5),
    ('w236:explodes', 'hit', 1.0, None, {'boost': 4.0}),               # "the kitchen window explodes."
    ('w237:crashes', 'hit', 0.75, None),                               # "The back door crashes open."
    ('s241', 'pulse_on', 0.6, None), ('s243', 'hit', 0.5, None),       # "I grab June and run." / "Lock."
    ('s245', 'pulse_off', 0.5, None),
    ('s251-0.2', 'silence', 0.6, 2.4),                                 # "The doorknob turns. Gently."
    ('s253', 'swell', 0.45, 6.0),                                      # the girl's voice under the door
    ('s257', 'sub_drop', 0.45, None),                                  # "Something slides under the door."
    ('s264', 'stinger', 0.6, None),                                    # "I TRIED TO HELP HIM."
    ('w267:get', 'hit', 0.85, None, {'boost': 3.0}),                   # "GET OUT OF MY HOUSE."
    ('w269:house', 'hit', 0.85, None), ('w269:house', 'braam', 0.7, 2.5),   # "IT'S MY HOUSE!"
    ('s270', 'pulse_on', 0.7, None),                                   # the hallway shakes
    ('w273:crack', 'hit', 0.8, None),                                  # "A wet, heavy crack."
    ('s273', 'pulse_off', 0.5, None),
    ('e273+0.1', 'silence', 1.0, 3.2),                                 # "Then nothing."
    ('s280', 'sub_drop', 0.5, None),                                   # "Not even me."
    ('s282-0.1', 'rule', 0.8, None, {'nosnap': True}),
    # rule 7
    ('s294-0.2', 'silence', 0.55, 0.9),                                # "Before sunrise."
    ('s296', 'hit', 0.65, None),                                       # "And it isn't before sunrise anymore."
    ('s297', 'riser', 0.55, 3.0), ('w299:key', 'hit', 0.75, None),     # "...From the outside. Mom has a key."
    ('s302', 'braam', 0.65, 3.0),                                      # the Bunnyman at the bottom of the stairs
    # the face reveal (final mix: one of the two hardest hits of the film, with the swap)
    # (on the cut to Dale's face, out of the 2.2 s silence, just before "It's a man.": on "man" it masked the word)
    ('s304-0.1', 'silence', 0.6, 2.2), ('s305-0.06', 'hit', 0.95, None, {'boost': 3.5}),   # "Inside, there's no monster. It's a man."
    ('e309', 'stinger', 0.7, None),                                    # "...the eyes of a terrified little girl."
    ('s311-0.4', 'silence', 0.85, 2.0),                                # "Mama."
    ('s312', 'sub_drop', 0.55, None),                                  # "Then he's still."
    ('s315', 'swell', 0.45, 4.2),                                      # "Want to see a magic trick?"
    # the reveal, the climax
    ('s322', 'riser', 0.55, 2.5), ('w324:traded', 'hit', 0.8, None),   # "He traded with her."
    ('s327', 'stinger', 0.6, None),                                    # "In someone else."
    ('s333', 'swell', 0.55, 10.0),                                     # the real Laurie under the bridge
    ('w338:daughter', 'hit', 0.7, None),                               # "Her daughter."
    ('s341', 'braam', 0.65, 3.0),                                      # "...followed him there."
    ('s342', 'pulse_on', 0.6, None),                                   # the recap, rule by rule
    ('s347', 'swell', 0.6, 8.0),
    ('w350:mom', 'hit', 0.85, None),                                   # "...it would be for Mom."
    ('s354', 'riser', 0.75, 4.3),                                      # "...it wasn't going to be her."
    ('s355', 'hit', 0.9, None, {'boost': 3.0}),                        # the swap
    ('s356', 'swell', 0.75, 4.6),
    ('w359:seven', 'hit', 1.0, None, {'boost': 4.0}),                  # "Seven.": the swap itself, the hardest hit
    ('w359:seven+0.3', 'silence', 1.0, 1.25),                          # "Seven." -> nothing
    ('s360', 'pulse_off', 0.5, None),
    # after
    ('s360+0.05', 'sub_drop', 0.5, None),                              # "When I open my eyes..."
    ('w365:hums+0.5', 'stinger', 0.5, None, {'nosnap': True}),         # "And it hums."
    ('s367', 'hit', 0.6, None),                                        # "I screamed."
    ('s372-0.15', 'silence', 0.45, 0.8),                               # "Holloway State Hospital."
    ('s374', 'stinger', 0.45, None),                                   # "They call me Laurie."
    ('s382-0.3', 'silence', 0.7, 1.6),                                 # "I know it's you."
    ('e382+0.1', 'sub_drop', 0.5, None),
    # the ending is near silence (final mix): the score drops out under "Want to see a magic trick?" and stays out
    # under "Easter is in nine days." (the line alone, clear); a low drop after it, then only the music box winding
    # down (IDENTITY), then "Okay. Breathe." (was: a riser under the line and a boosted hit after it)
    ('s384-0.2', 'silence', 0.85, 5.3),                                # "Want to see a magic trick?" .. "nine days."
    ('e385+0.05', 'sub_drop', 0.45, None),                              # "Easter is in nine days."
    ('e385+0.4', 'silence', 0.8, 2.3),                                 # into "Okay. Breathe." (the music box alone)
    # the outro
    ('e409', 'sub_drop', 0.35, None),                                  # "...don't ask what they found."
]

# ---------------------------------------------------------------------------------------------------- identity
# (anchor, type, level, len, extra). 'jingle': an audio/jingle.py version (version, tempo, loops, phrases, who, anchors
# [(beat, anchor)], space, stop, fade, off ...; 'until' (an anchor) sets len). 'show': a children's tune clean
# (slug, space 'clean', stop).
IDENTITY = [
    # the 1987 commercial under the narrator's "Hop, hop, hop along...", every word on its note
    (17.32, 'jingle', 0.78, None, dict(version='vhs', until='s7+1.6', anchors='COLD_OPEN', stop='fade', fade=0.02)),
    # "And she has been humming it ever since." (Mom)
    ('w11:humming+0.55', 'jingle', 0.4, 3.4, dict(version='hum', phrases=(0,), stop='fade')),
    # 1987: the float's PA on a camcorder, round and round, dragged to a halt as he walks into the woods
    ('s19-0.4', 'jingle', 0.55, None, dict(version='parade', loops=4, pass_at=11.0, until='s29+0.9', stop='drag')),
    # "And she was humming." -- the seven-year-old body coming out of the trees (a child's hum)
    ('s35-0.1', 'jingle', 0.36, 3.2, dict(version='hum', who='J', phrases=(0,), transpose=0.0, stop='fade')),
    # June turns seven (Mr. Otter's Rainy Day, soft), then Mom humming the jingle all week
    ('s54', 'show', 0.3, None, dict(slug='mr_otter_s_rainy_day_lil_y', space='clean', until='w56:humming-0.3',
                                    stop='fade', fade=1.0)),
    ('w56:humming+0.35', 'jingle', 0.42, None, dict(version='hum', phrases=(0, 1), until='s59+0.6', stop='fade')),
    # 11:07: the song from the woods on a dying speaker, until he stops waving
    ('w65:starts', 'jingle', 0.55, None, dict(version='speaker', loops=4, until='s82+0.5', stop='drag')),
    # Grandma remembered: her music box behind her words
    ('s147-0.4', 'jingle', 0.3, None, dict(version='musicbox', tempo=92.0, until='e154+0.4', stop='fade')),
    # "Yeah." -> the real Laurie tries to sing it through the slot and breaks into tears; the slot snaps shut on her
    # final mix: only her broken "Hop... hop... hop along..." (5 s, its sob at the end); her crying then takes over
    # (the picture's girl_cry, sfx_plan PICTURE) as the narrator says "...starts to cry", until Mom shuts the slot
    ('e188+0.12', 'jingle', 0.6, 5.0, dict(version='girl', space='slot', stop='fade')),
    # "Bedtime, bunny." / "She's humming."
    ('e194+0.15', 'jingle', 0.45, 4.6, dict(version='hum', phrases=(0, 1), stop='fade')),
    # the crayon diary (the real Laurie at six): Mary Had a Little Lamb on a music box, dragged to a halt on 1987
    ('s210-0.3', 'show', 0.32, None, dict(slug='mary_had_a_little_lamb_lil_y', space='clean', until='s215+0.5',
                                          stop='drag')),
    # "Mom says I can wear the yellow dress tomorrow. For the magic trick." -- the count phrase, slow, minor
    ('s227+0.3', 'jingle', 0.3, None, dict(version='climax', tempo=58.0, until='s229+0.4', stop='cut')),
    # "Close your eyes. And count to seven." -- Mom's words on the notes (D minor, detuned music box, low piano)
    ('w316:close-0.6', 'jingle', 0.55, None, dict(version='climax', until='w318:one-0.05', stop='fade',
                                                   anchors=[(8, 'w316:close'), (9, 'w316:eyes'), (9.5, 'w317:and'),
                                                            (10, 'w317:count'), (10.5, 'w317:to'), (11, 'w317:seven'),
                                                            (11.5, 'w317:seven+0.28'), (12, 'w317:seven+0.6')])),
    # the count: One D, Two E, Three F ... Six Bb, Seven C# (never home)
    ('w318:one', 'jingle', 0.6, 4.0, dict(version='count', n=1)),
    ('w320:two', 'jingle', 0.62, 4.0, dict(version='count', n=2)),
    ('w321:three', 'jingle', 0.64, 4.0, dict(version='count', n=3)),
    ('w351:four', 'jingle', 0.7, 4.0, dict(version='count', n=4)),
    ('w353:five', 'jingle', 0.72, 4.0, dict(version='count', n=5)),
    ('w358:six', 'jingle', 0.8, 4.0, dict(version='count', n=6)),
    ('w359:seven', 'jingle', 0.85, 0.4, dict(version='count', n=7, stop='cut')),
    # "And it hums." / "Hums all the time." (the thing in my old body: my own voice)
    ('w365:hums+0.4', 'jingle', 0.42, 3.6, dict(version='hum_x', phrases=(0,), stop='fade')),
    ('w380:hums+0.3', 'jingle', 0.3, 3.0, dict(version='hum_x', phrases=(2,), stop='fade')),
    # "Easter is in nine days." -- the first phrase on the music box, minor, winding down
    ('e385+0.5', 'jingle', 0.4, 3.2, dict(version='musicbox', minor=True, tempo=76.0, wind_down=True, stop='drag')),
    # "...if you hear a little song tonight... that's just the outro." -- and the song IS the outro: cheerful, from
    # the moment the line ends, its last phrase given to a soft hum (9.7 s: the picture must hold its end card to
    # about 1088.5 s; music_cues() extends the score's duration to the end of the last identity event)
    ('e411+0.1', 'jingle', 0.6, None, dict(version='outro', stop='fade')),
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
ARC = [('s130', 's160', 0.02), ('s160', 's196', 0.04), ('s196', 's232', 0.05), ('s232', 's282', 0.06),
       ('s322', 's360', 0.05)]


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
                                 for e in idt) + 0.6)
    return {'duration': round(duration, 2), 'intensity': intensity(lines, duration),
            'events': sorted(events(lines) + idt, key=lambda e: e['t']),
            'track_map': track_map(lines)}


OUTRO_LEN = 9.75                                          # jingle.render('outro') length (s): the end card holds for it


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
