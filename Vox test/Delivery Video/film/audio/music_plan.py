"""music_plan.py: the delivery film's music map, built the police film's way (film.py INTENSITY / polish_cues / score.py).

The police score: one Epidemic track section per film section (sections start at the rule cards), gain automation
following a piecewise-linear intensity curve (Q1 > Q2 calmest < Q3 < Q4, climax in the last minute), 13 s swells
into hits and rule cards, risers into reveals, true music drop-outs (1.7 s, under the line) before the scares, hits
and stingers on the reveal lines, a rule-card sting on every "Rule number N", a music-box motif on the memories, a
heartbeat pulse in the two chases, and the end cadence. This module holds that plan for this film, anchored to the
script lines (so a re-alignment moves the events with the words), and writes music_cues.json for score.py.

Public API
    TRACK_MAP        [(anchor, slug, off, why)]   one track section per film section; off = seconds into the
                     varispeed track (score.TRACKS shift), chosen from the catalogue's loudness / brightness curves
    INTENSITY        [(anchor, value)]            0..1 tension curve (score.py: bed level, layer thresholds)
    EVENTS           [(anchor, type, level, len)] music events (ARCHITECTURE.md music_cues types)
    resolve(anchor, lines) -> t                   'sN' = start of line N, 'eN' = end of line N, 'sN+0.3' offsets,
                                                  or a number (film seconds)
    track_map(lines), intensity(lines, duration), events(lines), music_cues(lines, duration) -> dict
                     music_cues adds 'track_map' (score.py pins the arrangement with it)
    load_lines(timeline_path=None) -> (lines, duration)

For film.py (the director owns the picture-derived cues): use these as the base and merge the picture's own events,
e.g. in Film.cues():  import audio.music_plan as MP;  mus = MP.events(F.L) + picture events;
music = {'duration': F.duration, 'intensity': MP.intensity(F.L, F.duration), 'events': mus,
'track_map': MP.track_map(F.L)}. polish_cues() then retimes hits to the cuts as in the police film.

CLI: python3 music_plan.py [--timeline T] [--out W/cues/music_cues_plan.json] [--table]   (--table prints the map)
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.normpath(os.path.join(HERE, '..', '_work'))
TIMELINE = os.path.join(W, 'align', 'timeline.json')

# ---------------------------------------------------------------------------------------------------- arrangement
# section start, track, offset (s, in the varispeed track), why. Tracks: score.TRACKS (shifts there).
TRACK_MAP = [
    ('s0', 'are_you_alone_victor_lundberg', 0.0,
     'cold open: a dark D sub drone (67-92 % < 250 Hz) that swells into its one spike at 93.5-100 s, which lands on '
     '"Something that belongs to this house is coming back / the exchange"; falls back for "seven rules"'),
    ('s49', 'the_logic_of_tyrants_hampus_naeselius', 0.0,
     'rule 1 (the tablet, your initial on the line, the late mouth, 3:09 3:08): low dark pulse building -26 -> -15 LU'),
    ('s75', 'dark_forebodings_ethan_sloan', 4.0,
     'rule 2 (the blank label, "anyone asleep upstairs?"): the police film\'s flat dark drone, the calm second quarter'),
    ('s98', 'haunted_mind_etienne_roussel', 25.0,
     'rule 3 (the photo from behind, the keys in the bowl, "Hey, buddy"): slow mid-register build, no drums'),
    ('s123', 'goth_christmas_par', 10.0,
     'rule 4 (mom, the same van, the night dad left): the bell / lullaby track slowed 4 semitones: the memory theme'),
    ('s148', 'code_of_violence_dian_shuai', 75.0,
     'the driver leans in ("Ma\'am", the chain, the eyes): dark pulsing D-minor bass building -15 -> -12 into the knock'),
    ('s165', 'turning_stones_stefan_ekstrom', 75.0,
     'rule 5 (the box knocks, "Mar?", "Buddy?", faster): a pure dark drone (99 % < 250 Hz), no pulse to fight the knocks'),
    ('s204', 'afterthoughts_beyza', 0.0,
     'rule 6 (the box left at the door, the night, 3:40, the empty seat): slow, sad, no drums'),
    ('s227', 'one_step_away_dian_shuai', 45.0,
     'rule 7 (the run, Lily\'s room, the 3:41 photo, "Lily.", the van leaves): percussive build to the climax at '
     '93-132 s; its drop at 132.5 s lands on the sunrise (598 s)'),
    ('s263', 'goth_christmas_par', 148.0,
     'sunrise, the cut tape, dad\'s rusted keys: the memory theme returns (its warm middle, not the fade-out)'),
    ('s274', 'are_you_alone_victor_lundberg', 72.0,
     'the sting ("Tonight, at 3:07..."): the opening track again, so its spike lands on "And one more."'),
]

# ---------------------------------------------------------------------------------------------------- intensity
INTENSITY = [
    ('s0', 0.46), ('s5', 0.5), ('s6', 0.56), ('s7', 0.38), ('s9', 0.44), ('s10', 0.4), ('s13', 0.52), ('s15', 0.48),
    ('s19', 0.56), ('s20', 0.5), ('s23', 0.52), ('s26', 0.6), ('s28', 0.62), ('s37', 0.66), ('s39', 0.62),
    ('s42', 0.76), ('e43', 0.8), ('s46', 0.62), ('s47', 0.55),
    ('s49', 0.7), ('s51', 0.48), ('s54', 0.52), ('s55', 0.6), ('s56', 0.66), ('s58', 0.62), ('s62', 0.66),
    ('s66', 0.72), ('s67', 0.58), ('s71', 0.55), ('e74', 0.6),
    ('s75', 0.5), ('s77', 0.34), ('s80', 0.38), ('s83', 0.44), ('s85', 0.48), ('s86', 0.38), ('s91', 0.46),
    ('s94', 0.5), ('s96', 0.4),
    ('s98', 0.5), ('s100', 0.4), ('s102', 0.48), ('s105', 0.44), ('s106', 0.52), ('s107', 0.55), ('e109', 0.6),
    ('s110', 0.64), ('s113', 0.45), ('s115', 0.4), ('s117', 0.42), ('s119', 0.3), ('s122', 0.4),
    ('s123', 0.46), ('s125', 0.3), ('s130', 0.36), ('s131', 0.42), ('s134', 0.3), ('s136', 0.34), ('s138', 0.4),
    ('s139', 0.44), ('s143', 0.46), ('s144', 0.5), ('s145', 0.42), ('s147', 0.38),
    ('s148', 0.5), ('s150', 0.56), ('s155', 0.6), ('s156', 0.64), ('s159', 0.62), ('s162', 0.66), ('s163', 0.72),
    ('e163', 0.82), ('s164', 0.85),
    ('s165', 0.8), ('s167', 0.62), ('s170', 0.6), ('s171', 0.66), ('e173', 0.62), ('s174', 0.7), ('s177', 0.74),
    ('s180', 0.6), ('s183', 0.64), ('s186', 0.68), ('s187', 0.74), ('s191', 0.78), ('s194', 0.82), ('s196', 0.86),
    ('s197', 0.6), ('s198', 0.66), ('s199', 0.78), ('s200', 0.72), ('e203', 0.66),
    ('s204', 0.6), ('s206', 0.48), ('s207', 0.52), ('s208', 0.5), ('s210', 0.44), ('s214', 0.42), ('s217', 0.5),
    ('s219', 0.44), ('s220', 0.4), ('s221', 0.3), ('s222', 0.45), ('s224', 0.52), ('s226', 0.62),
    ('s227', 0.72), ('s229', 0.62), ('s231', 0.74), ('s235', 0.78), ('s237', 0.8), ('s239', 0.7), ('s241', 0.76),
    ('s242', 0.86), ('s244', 0.82), ('s245', 0.78), ('s246', 0.84), ('s249', 0.86), ('s250', 0.9), ('s252', 0.94),
    ('e253', 0.96), ('s254', 1.0), ('s255', 0.8), ('s258', 0.74), ('s259', 0.66), ('s261', 0.7), ('s262', 0.76),
    ('s263', 0.48), ('s267', 0.5), ('s268', 0.56), ('s270', 0.44), ('e273', 0.38),
    ('s274', 0.62), ('s275', 0.66), ('s279', 0.72), ('s280', 0.82), ('s281', 0.86), ('s282', 0.9), ('s283', 0.95),
    ('s284', 0.9), ('s285', 1.0), ('e285', 0.95),
]

# ---------------------------------------------------------------------------------------------------- events
# (anchor, type, level, len). Silences sit under the line before the scare and end on it (polish_cues keeps a hit
# right after a drop); rule stings on every "Rule number N"; risers end on their anchor.
EVENTS = [
    # cold open
    ('s6', 'hit', 0.55, None),                     # "It's asking to get in."
    ('s9', 'riser', 0.5, 4.0), ('s9', 'stinger', 0.55, None),   # "Last night, someone tried to deliver him back."
    ('s10', 'motif', 0.35, 4.0),                   # 3:07, the phone lights up: the music box, very soft
    ('s12+0.2', 'silence', 0.5, 1.5),              # "You haven't ordered anything." ... the doorbell (SFX) rings
    ('s19', 'hit', 0.55, None),                    # "He's looking straight into the lens"
    ('s26', 'stinger', 0.5, None),                 # "The driver smiles at the camera."
    ('s36+1.0', 'silence', 0.5, 1.5), ('s37', 'hit', 0.7, None),          # RETURN.
    ('e43', 'swell', 0.75, 12.0), ('s44', 'braam', 0.75, 3.5),            # "...sign for the exchange." / Exchange.
    ('s49', 'rule', 0.7, None),
    # rule 1
    ('s55', 'pulse_on', 0.5, None),
    ('s54+1.0', 'silence', 0.5, 1.6), ('s55', 'hit', 0.7, None),          # "The signature line isn't empty."
    ('s56', 'swell', 0.6, 8.0),
    ('s62', 'stinger', 0.45, None),                # "his mouth moves a little too late"
    ('s66+1.6', 'sub_drop', 0.5, None),            # "3:09. 3:09. 3:08."
    ('s67', 'pulse_off', 0.5, None),
    ('s75', 'rule', 0.65, None),
    # rule 2 (the calm quarter)
    ('s85+1.1', 'hit', 0.5, None),                 # "Anyone else asleep upstairs?"
    ('s91', 'stinger', 0.5, None),                 # "His smile is wider now"
    ('e95', 'braam', 0.55, 3.0),                   # "They always do."
    ('s98', 'rule', 0.65, None),
    # rule 3
    ('s100+0.6', 'silence', 0.5, 1.5), ('s102', 'hit', 0.75, None),       # "From behind."
    ('s106', 'hit', 0.6, None),                    # "It's 3:11 now."
    ('s109', 'motif', 0.4, 4.0),                   # dad used to drop his keys in that bowl
    ('e109-0.35', 'silence', 0.6, 1.0), ('s110', 'hit', 0.85, None),      # "Hey, buddy,"
    ('s110', 'swell', 0.7, 2.0),
    ('s119', 'silence', 0.4, 1.9),                 # "The hallway goes quiet."
    ('s123', 'riser', 0.55, 5.0),                  # footsteps on the stairs -> rule 4
    ('s123', 'rule', 0.7, None),
    # rule 4: mom, the van, the night dad left
    ('s131', 'hit', 0.6, None),                    # "That's the van,"
    ('s136', 'motif', 0.45, 8.0),                  # twenty-one years ago
    ('s139', 'braam', 0.6, 3.0),                   # "It had his own father's voice."
    ('s144+1.2', 'hit', 0.6, None),                # the van door slides shut
    ('s145', 'silence', 0.35, 1.7),                # the box was empty, father gone
    ('s148', 'swell', 0.6, 5.0),
    ('s150', 'hit', 0.65, None),                   # "Ma'am,"
    ('s155', 'swell', 0.6, 8.0),                   # the chain / you catch her wrist
    ('s163+3.6', 'stinger', 0.6, None),            # the eyes shine white (the picture's eye_flash may move it)
    ('e163-1.3', 'silence', 0.6, 1.3), ('s164', 'hit', 0.85, None),       # "Then the box knocks."
    ('s165', 'rule', 0.75, None),
    # rule 5: the box
    ('s171', 'swell', 0.6, 6.0),                   # "That was your father's knock."
    ('e173-1.1', 'silence', 0.5, 1.4), ('s174', 'sub_drop', 0.6, None),   # "Mar?"
    ('e186-0.6', 'silence', 0.5, 1.3),             # "Buddy?" (the voice alone after the drop)
    ('s194', 'riser', 0.65, 4.8),                  # the knocking gets faster -> the driver stops smiling
    ('s196', 'hit', 0.8, None),
    ('s197', 'silence', 0.6, 1.9),                 # "His face is perfectly still."
    ('s199', 'stinger', 0.7, None),                # smiles again, wider
    ('s204', 'rule', 0.7, None),
    # rule 6: the night
    ('s207', 'sub_drop', 0.4, None),               # it scrapes across the welcome mat
    ('s214', 'motif', 0.35, 4.0),                  # sunrise is at 6:12
    ('s221', 'silence', 0.5, 2.0),                 # "At 3:40, the knocking stops."
    ('s226', 'riser', 0.6, 5.0), ('s226', 'hit', 0.8, None),   # "And the driver's seat is empty."
    ('s227', 'rule', 0.8, None),
    # rule 7: the windows, Lily
    ('s231', 'pulse_on', 0.6, None),               # you run through the house
    ('s237', 'stinger', 0.55, None),               # the door at the end of the hall is open a crack
    ('s239', 'motif', 0.4, 4.0),                   # Lily is eight
    ('s242', 'hit', 0.8, None),                    # "The window is wide open."
    ('e244', 'braam', 0.7, 3.0),                   # the blankets are still warm
    ('s246', 'hit', 0.75, None),                   # "Return complete."
    ('e253', 'swell', 0.9, 14.0),
    ('e253-1.5', 'silence', 0.7, 1.4), ('s254', 'hit', 1.0, None),        # "Lily."
    ('s254', 'pulse_off', 0.5, None),
    ('s259', 'motif', 0.45, 4.0),                  # she never even knew him
    ('s262', 'braam', 0.7, 3.5),                   # the van pulls away
    ('s263', 'scene', 0.0, None),                  # sunrise
    ('s267-0.2', 'silence', 0.4, 1.4), ('s268', 'hit', 0.55, None),       # "except for a ring of keys"
    ('s269', 'motif', 0.4, 4.0),                   # the keychain you made him in second grade
    ('s274', 'scene', 0.0, None), ('s274', 'sub_drop', 0.7, None),        # "Tonight, at 3:07..."
    ('e280-0.4', 'hit', 0.8, None),                # "...it says: Lily."
    ('s281', 'swell', 0.85, 8.0),
    ('s282', 'riser', 0.7, 5.0),                   # small knuckles on cardboard -> two knocks
    ('s284', 'silence', 0.7, 0.7),                 # "A pause."
    ('s285', 'hit', 1.0, None),                    # "And one more."
    ('e285+0.2', 'end', 0.9, 6.0),
]


# ---------------------------------------------------------------------------------------------------- resolve
_A = re.compile(r'^([se])(\d+)([+-][0-9.]+)?$')


def resolve(anchor, lines):
    if isinstance(anchor, (int, float)):
        return float(anchor)
    m = _A.match(str(anchor).strip())
    if not m:
        raise ValueError(f'bad anchor {anchor!r}')
    i = int(m.group(2))
    l = lines[i] if i < len(lines) and lines[i].get('i', i) == i else next(x for x in lines if x.get('i') == i)
    t = float(l['t'] if m.group(1) == 's' else l['end'])
    return t + (float(m.group(3)) if m.group(3) else 0.0)


def load_lines(timeline_path=None):
    tl = json.load(open(timeline_path or TIMELINE))
    return tl['lines'], float(tl.get('duration_en') or max(l['end'] for l in tl['lines']))


FLATTEN = {}          # slug -> share of the track's own dynamics evened out (score.FLATTEN 0.3 otherwise)


def track_map(lines):
    out = []
    for a, s, o, _w in TRACK_MAP:
        x = {'t0': round(resolve(a, lines), 3), 'slug': s, 'off': float(o)}
        if s in FLATTEN:
            x['flatten'] = FLATTEN[s]
        out.append(x)
    return out


def intensity(lines, duration=None):
    pts = sorted((round(resolve(a, lines), 3), float(v)) for a, v in INTENSITY)
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
    for a, ty, lv, ln in EVENTS:
        e = {'t': round(resolve(a, lines), 3), 'type': ty, 'level': lv}
        if ln is not None:
            e['len'] = ln
        ev.append(e)
    return sorted(ev, key=lambda e: e['t'])


def music_cues(lines=None, duration=None):
    if lines is None:
        lines, d0 = load_lines()
        duration = duration or d0 + 2.5
    duration = float(duration or max(l['end'] for l in lines) + 2.5)
    return {'duration': round(duration, 2), 'intensity': intensity(lines, duration), 'events': events(lines),
            'track_map': track_map(lines)}


def table(lines):
    out = []
    tm = track_map(lines)
    for k, (x, (_a, _s, _o, why)) in enumerate(zip(tm, TRACK_MAP)):
        t1 = tm[k + 1]['t0'] if k + 1 < len(tm) else max(l['end'] for l in lines)
        out.append(f"{x['t0']:7.2f}-{t1:7.2f}  {x['slug']:40s} from {x['off']:5.1f}s  {why}")
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
