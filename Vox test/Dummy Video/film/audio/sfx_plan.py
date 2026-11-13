"""sfx_plan.py: the final mix's sound-design pass over the picture's SFX cue sheet (the dummy film).

film.py writes W/cues/sfx_cues.json from the picture: every drawn action (jaw snaps, eyelid clicks, the head ticks,
the squeezes, the lamp, the TV, the laughter waves, the impacts on the reveal cuts) at its frame. That sheet stays
the source and its timings are never moved (they are the picture's sync). This pass, applied by mix.py with
`--plan full` (audio/final_mix.sh), only
  1. re-levels picture cues that measured buried or too busy in the full-length checks (EDIT),
  2. thins the per-syllable jaw ticks under his speech (THIN: dense ticks at -8 dB read as a rattle, not a dummy),
  3. adds the sounds the picture does not draw: off-screen sounds (the footsteps upstairs, the spoon heard from the
     kitchen, the slow creak of his jaw closing, the little steps), the touch / grab / slot foley of close-up actions
     the cast does not emit, the goodnight thump, the house settling (ADD).
Every added cue is anchored to the narration (music_plan.resolve: 'sN' / 'eN' / 'wN:word' +- s), so it follows the
recording, not a shot list, and survives picture changes.

    apply(cues, lines) -> (cues, log)      cues: the picture's list (not modified); log: what changed, one line each
    python3 sfx_plan.py [--cues W/cues] [--table]     prints the pass (dry run)
"""
import copy, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import music_plan as MP                                   # noqa: E402

# --------------------------------------------------------------------------------------------- EDIT (picture cues)
# (name, t0, t1, match params (subset), change, why). t0 / t1: anchors or seconds (the window the cue's t falls in).
# change: {'add_db': x} | {'gain_db': x} | {'min_db': x} (raise to at least x) | {'params': {...}} | {'drop': True}
EDIT = [
    ('wood_creak', 0, 9999, {'kind': 'tick'}, {'add_db': 4.0},
     'his small wooden ticks (a finger, an elbow, the head): the picture sends -14..-11 dB, measured 18-25 LU under the '
     'voice + music (inaudible); +4 dB keeps them small but there'),
    ('bulb_buzz', 0, 9999, {}, {'add_db': 4.0}, 'the kitchen bulb hum / the lamp coming back: -14 dB was buried'),
    ('footsteps_wood_inside', 's145', 's148', {'kind': 'tiny'}, {'gain_db': -6.0},
     '"Moving slowly down the hall": the knee-high steps were sent at -16 dB (measured masked)'),
    ('spoon_clink', 'w63:sound', 's64+1.0', {'kind': 'stir'}, {'drop': True},
     'the stir started on "A spoon, stirring"; the narration hears it first ("there\'s a sound"): ADD puts it inside '
     'the drop-out before the words, where it is heard alone'),
    ('wood_creak', 's104', 's108', {'kind': 'grind'}, {'gain_db': -5.0},
     'the 180-degree head turn heard from the couch (off screen): -12 dB was a whisper; it is the scare\'s set-up'),
    ('wood_creak', 's265', 's266', {'kind': 'tick'}, {'gain_db': -5.0},
     '"The dummy turns his head toward Owen": three jerky ticks, close (after the +4 rule: set, not added)'),
    ('hand_squeeze', 's164', 's169', {}, {'gain_db': 3.0},
     '"Once. Twice. Three times.": the squeezes sit on the words (the picture\'s pulses); -6 dB measured 13 LU under '
     'the narration'),
    ('hand_squeeze', 's26', 's28', {}, {'add_db': 4.0}, 'the bedtime squeezes (memory), same reason'),
    ('hand_squeeze', 's232', 's234', {}, {'add_db': 4.0}, 'the squeezes recalled ("the hand that squeezed mine")'),
    ('eyelid_click', 's315', 's317', {'kind': 'shut'}, {'gain_db': 4.0},
     '"Both of his eyelids close." The two dry clicks in the drop-out are the twist: the loudest small sound of the film'),
    ('eyelid_click', 's266-0.5', 's268', {'kind': 'shut'}, {'gain_db': 1.0}, '"Click." (his wink at Owen), in a drop-out'),
    ('tape_stop', 's209-0.5', 's210', {}, {'gain_db': -2.0},
     'the dummy on the tape stops mid-joke: the warble was -8 dB, under the show theme dragging to a halt'),
    ('studio_laughter', 'e217-0.3', 's219', {}, {'gain_db': 5.0, 'params': {'level': 1.0, 'roar': True}},
     '"And the studio audience laughs." at the crying man: the biggest wave of the film, on the hit (v2: +4 dB, the braam '
     'unboosted: it sat at -12 LU under the braam body)'),
    ('studio_laughter', 's135', 's142', {}, {'add_db': 6.0},
     'v2: the laughter waves he moves on peaked only -11..-16 LU rel the voice: +6 dB (the TV band keeps them off the words)'),
    ('studio_laughter', 's226-0.5', 'w226:laughed+0.2', {}, {'add_db': 8.0}, '"And everyone laughed." (was -24 under the stinger)'),
    ('scream', 'e253-0.2', 's255', {}, {'gain_db': 6.0},
     'Mom\'s scream (measured -6.9 LU rel the narration at -2 dB: it is the loudest human sound of the film)'),
    ('impact_hit', 'w242:gone-0.3', 'e242+0.2', {}, {'gain_db': -8.0},
     'the cut on "...Owen is gone." lands on the word: at -2 dB it sat 12 LU over "gone"'),
    ('impact_hit', 'e223-0.3', 'e223+0.2', {}, {'gain_db': -10.0},
     'the cut at the end of "...squeezed my hand three times." lands on "times" (10 LU over it at -2 dB)'),
    ('bulb_flicker', 's55', 'e55', {}, {'gain_db': -5.0}, '"...stay in the light.": the lamp flickers on "light"'),
    ('footsteps_wood_inside', 's41', 's42', {}, {'add_db': 4.0}, 'the family walking in (masked at -6 dB)'),
    ('cloth_rustle', 's90', 'e90+0.5', {'kind': 'touch'}, {'gain_db': -6.0},
     '"Her hand finds yours." (sent at -14 dB: masked 20 LU under the voice and music)'),
    ('eyelid_click', 's266', 'e267', {'kind': 'open'}, {'gain_db': -4.0},
     '"His eyelid winks." the lid opening again after the "Click." (masked at -8 dB)'),
    ('van_pull_away', 's324', 's325', {}, {'gain_db': 11.0},
     'the museum van taking him away (measured masked at 0 dB under the swell)'),
    ('light_switch', 's338-1.0', 'e338+0.2', {}, {'gain_db': 1.0}, 'the last light going off on "He never will." (v2: +6, it was lost)'),
    # v2 (review M2 / m7): the named action sounds, now placed just before their words, +4..+6 dB
    ('dummy_clack', 'e110-0.1', 'e110+0.1', {'kind': 'snap'}, {'add_db': 5.0}, '"Clack." (the slow close)'),
    ('dummy_clack', 'w127:clack-0.2', 'w127:clack+0.1', {'kind': 'snap'}, {'add_db': 5.0}, '"Clack." (the joke)'),
    ('eyelid_click', 'e17-0.1', 'e17+0.3', {}, {'add_db': 5.0}, 'the wink after "...when he winked."'),
    ('keys_drop', 'e192-0.3', 'e192+0.5', {}, {'add_db': 6.0}, 'Mom grabs her keys'),
    ('snort', 'e124-0.3', 'e124+0.2', {}, {'add_db': 4.0}, 'Owen\'s snort, after the word'),
    ('sip', 's331', 's333', {}, {'add_db': 6.0}, 'the new Owen sips the coffee (a callback)'),
    ('sip', 's73', 'e73+0.5', {}, {'add_db': 6.0}, 'Grandpa\'s sip (memory)'),
    ('lamp_out', 's2', 'e2+0.5', {}, {'add_db': 4.0}, 'the cold-open lamp dying under his flashlight'),
    ('breath', 's262', 's265', {'kind': 'sob'}, {'add_db': 2.0}, 'Owen crying before "Say goodnight, Mister Winks"'),
    ('dummy_clack', 's198', 's200', {'kind': 'snap'}, {'add_db': -2.0},
     'the bookcase jaw going up and down: ten snaps at 0 dB under three lines; -2 dB keeps the rhythm, frees the words'),
]

# --------------------------------------------------------------------------------------------- THIN (speech ticks)
# film.py emits one dummy_clack kind='speech' per syllable (every 0.15-0.3 s at -8 dB). Keep one every MIN_GAP s,
# at -10 dB in the room, -13 dB through the TV, -15 dB under the tape's crying man (the voice must stay pristine).
THIN_MIN_GAP = 0.26
THIN_GAIN = {'tv': -13.0, None: -10.0}
THIN_QUIET = [('s214', 'e217', -15.0)]          # "Please. Somebody help me. My name is Walter Kemp. That isn't me..."

# --------------------------------------------------------------------------------------------- ADD (new cues)
# (anchor, name, gain_db, space, params, why)
ADD = [
    # the house: settling timbers under the whole night (bed bus: ducked under the voice, cut in the drop-outs)
    ('s41+1.5', 'house_creaks', -3.0, None, {'dur': 'until:s319', 'density': 0.08},
     'the old house settling, the whole night in it (room tone so the house feels real)'),
    # rule 1: the case, the velvet, the spoon, the mug
    ('s62+0.15', 'velvet', -2.0, 'tight', {'dur': 1.0}, '"And the velvet is still warm." (fingers in the lining)'),
    ('w63:sound-0.7', 'spoon_stir', 1.0, 'next_room', {'dur': 3.4},
     '"From the kitchen, there\'s a sound." The spoon starts in the drop-out, alone, before the words name it'),
    ('w71:picks+0.1', 'mug_set', -4.0, 'next_room', {'kind': 'pickup'}, 'Mom picks the mug up'),
    # rule 2: the voices upstairs (someone walking overhead), Mom's hand, the jaw closing
    ('s86+1.45', 'footsteps_hall', 6.0, 'upstairs', {'n': 3, 'rate': 1.6},
     'someone walking overhead before "Honey?" (nobody is up there)'),
    ('s91+0.75', 'footsteps_hall', 5.0, 'upstairs', {'n': 2, 'rate': 1.4}, 'again, before "Mom? I\'m up here."'),
    ('w104:mouth-0.45', 'cloth_rustle', -6.0, None, {'kind': 'grab'}, '"Mom\'s hand flies to her mouth."'),
    ('w104:mouth-0.3', 'breath', -8.0, 'close', {'kind': 'gasp', 'who': 'mom'}, 'her gasp'),
    ('s106+0.35', 'cloth_rustle', -8.0, None, {'kind': 'rustle'}, '"She starts to stand up."'),
    ('s107+0.3', 'cloth_rustle', -5.0, None, {'kind': 'grab'}, '"You pull her back down."'),
    ('s110+0.2', 'wood_creak', -6.0, 'next_room', {'kind': 'creak', 'dur': 1.7},
     '"It closes, very slowly." The jaw\'s long creak in the drop-out, then "Clack."'),
    # rule 3: his hands on the table, standing on the chair, the steps down the hall
    ('w140:hands+0.15', 'wood_knock', 1.0, 'next_room', {'n': 2, 'spacing': 0.12},
     '"puts both hands flat on the table"'),
    ('w140:stands-0.15', 'wood_creak', 2.0, 'next_room', {'kind': 'creak', 'dur': 0.8},
     '"and stands up on the chair" (the chair seat under his weight)'),
    # v2 (review M3): the laughter swells exactly as he moves: a crest in each narration gap, on his ticks
    (305.0, 'studio_laughter', 2.0, 'tv', {'dur': 1.6, 'level': 0.85}, 'a crest before "A huge, roaring wave"'),
    (308.6, 'studio_laughter', 2.0, 'tv', {'dur': 1.4, 'level': 0.85}, 'the gap before "And with every wave"'),
    (311.8, 'studio_laughter', 3.0, 'tv', {'dur': 1.6, 'level': 0.9}, 'the gap before "His fingers curl."'),
    (320.55, 'studio_laughter', 3.0, 'tv', {'dur': 1.4, 'level': 1.0, 'roar': True}, 'he is standing on the chair'),
    ('e141+0.05', 'studio_laughter', 1.0, 'tv', {'dur': 1.6, 'level': 0.85}, 'after "He didn\'t need us to laugh." (v2.1: was mid-line)'),
    # v2 (review M6): his jaw snaps shut after each of his lines, close and dry (the hit after waits for it)
    ('e103+0.03', 'dummy_clack', 0.0, None, {'kind': 'snap'}, '"...kiddo." snap'),
    ('e118+0.03', 'dummy_clack', 0.0, None, {'kind': 'snap'}, 'the joke'),
    ('e121+0.03', 'dummy_clack', 0.0, None, {'kind': 'snap'}, 'the punchline'),
    ('e172+0.03', 'dummy_clack', 0.0, None, {'kind': 'snap'}, '"Kiddo"'),
    ('e183+0.03', 'dummy_clack', 0.0, None, {'kind': 'snap'}, 'the stairs'),
    ('e251+0.03', 'dummy_clack', 0.0, None, {'kind': 'snap'}, '"He\'s a natural, kiddo,"'),
    ('e253+0.03', 'dummy_clack', 0.0, None, {'kind': 'snap'}, '"Just like me."'),
    ('e257+0.03', 'dummy_clack', 0.0, None, {'kind': 'snap'}, '"Pull,"'),
    ('e259+0.03', 'dummy_clack', 0.0, None, {'kind': 'snap'}, '"...and his hand comes with me."'),
    ('e268+0.02', 'dummy_clack', 0.0, None, {'kind': 'snap'}, '"Goodnight, Owen."'),
    # rule 4: 3 AM, the flashlight on the stairs, the grab, the slot, the hand
    ('s157-0.05', 'flashlight_click', -6.0, 'inside', {'kind': 'on'}, 'the flashlight comes back: he is on the stairs'),
    ('s157', 'flashlight_hum', -6.0, None, {'dur': 'until:s158+0.3'}, 'the little bulb\'s hum while it points at you'),
    ('s158+0.05', 'cloth_rustle', -3.0, None, {'kind': 'grab'}, '"I grab him."'),
    ('s158+0.12', 'wood_knock', -6.0, 'close', {'n': 1}, 'his wooden body in my hands'),
    ('w159:slot-0.1', 'hand_slot', 2.0, 'tight', {'dur': 1.3}, '"I push my hand through the slot in his back"'),
    ('w163:lets+0.25', 'wood_creak', -3.0, 'tight', {'kind': 'tick', 'dur': 0.12}, '"It lets go of the stick"'),
    ('w163:takes+0.25', 'hand_squeeze', -4.0, 'tight', {}, '"and it takes hold of my hand instead"'),
    ('w169:fingertips-0.25', 'paper', 6.0, 'tight', {'dur': 0.6}, '"my fingertips brush against something folded" (v2: before the word, +8)'),
    # rule 5: the tape, the camera look
    ('w210:turns+0.3', 'tape_glitch', -6.0, 'tv', {'kind': 'tracking', 'dur': 0.5},
     'the dummy on the tape turns to the camera: the picture tears'),
    # rule 6: the goodnight, Owen's hand out, the hugs
    ('e268+0.05', 'goodnight_hit', -2.0, None, {'swell': 0.5}, '"Goodnight, Owen." in near silence: a short swell into the deep thump with the score\'s hit as his eyes '
     'close (the swell under the word "Owen" took 2 LU off it)'),
    ('w272:slides+0.1', 'hand_slot', -8.0, 'tight', {'dur': 0.9}, '"Owen slides his hand out like it\'s nothing"'),
    ('w272:throws+0.25', 'cloth_rustle', -2.0, None, {'kind': 'grab'}, '"throws his arms around Mom"'),
    ('s275+0.2', 'cloth_rustle', -6.0, None, {'kind': 'grab'}, '"He hugs me too."'),
    # rule 7: picking him up, his eyes opening
    ('w290:pick+0.2', 'wood_knock', -8.0, 'close', {'n': 1}, '"I pick the dummy up off the rug"'),
    ('w312:opens+0.35', 'eyelid_click', -6.0, 'tight', {'kind': 'open'}, '"In my arms, Mister Winks opens his eyes."'),
    # the ending: the museum man, the new Owen's "kiddo" echoing the goodnight
    ('e319+0.1', 'car_pass', 9.0, 'outside', {'kind': 'arrive', 'dur': 5.0}, 'the museum van draws up at eight (v2: after "comes.", +6)'),
    ('e336+0.02', 'goodnight_hit', -4.0, None, {'swell': 0.7},
     'after the new Owen\'s "See you in the morning, kiddo." the same low thump as Owen\'s goodnight, in the silence'),
]


def _t(a, lines):
    return float(a) if isinstance(a, (int, float)) else MP.resolve(a, lines)


def _match(c, name, a, b, sub):
    if c.get('name') != name:
        return False
    try:
        t = float(c['t'])
    except (KeyError, TypeError, ValueError):
        return False
    if not (a - 1e-3 <= t <= b + 1e-3):
        return False
    p = c.get('params') if isinstance(c.get('params'), dict) else {}
    return all(p.get(k) == v for k, v in sub.items())


def apply(cues, lines):
    """The picture's cue list -> the mixed cue list (a new list) and a log of every change."""
    out = [copy.deepcopy(c) for c in cues if isinstance(c, dict)]
    log = []
    # EDIT
    for name, a, b, sub, ch, why in EDIT:
        try:
            ta, tb = _t(a, lines), _t(b, lines)
        except Exception as e:
            log.append(f'EDIT {name} {a}..{b}: bad anchor ({e!r}): skipped'); continue
        hit = [c for c in out if _match(c, name, ta, tb, sub)]
        for c in hit:
            g0 = float(c.get('gain_db', 0.0) or 0.0)
            if ch.get('drop'):
                c['_drop'] = True
            if 'add_db' in ch:
                c['gain_db'] = round(g0 + ch['add_db'], 2)
            if 'gain_db' in ch:
                c['gain_db'] = ch['gain_db']
            if 'min_db' in ch:
                c['gain_db'] = max(g0, ch['min_db'])
            if 'params' in ch:
                c['params'] = dict(c.get('params') or {}, **ch['params'])
        log.append(f'EDIT {name:18s} {ta:7.2f}-{tb:7.2f} {sub or ""} {ch}: {len(hit)} cue(s)  ({why[:70]})')
    out = [c for c in out if not c.get('_drop')]
    # THIN the speech ticks
    quiet = []
    for a, b, g in THIN_QUIET:
        try:
            quiet.append((_t(a, lines), _t(b, lines) + 0.3, g))
        except Exception:
            pass
    sp = sorted([c for c in out if c.get('name') == 'dummy_clack' and (c.get('params') or {}).get('kind') == 'speech'],
                key=lambda c: float(c['t']))
    keep, last, n0 = [], -9.0, len(sp)
    for c in sp:
        t = float(c['t'])
        if t - last < THIN_MIN_GAP:
            c['_drop'] = True; continue
        last = t
        g = THIN_GAIN.get(c.get('space') if c.get('space') == 'tv' else None)
        for a, b, gq in quiet:
            if a <= t <= b:
                g = gq
        c['gain_db'] = min(float(c.get('gain_db', 0.0) or 0.0), g)
        keep.append(c)
    out = [c for c in out if not c.get('_drop')]
    log.append(f'THIN dummy_clack speech: {n0} -> {len(keep)} ticks (>= {THIN_MIN_GAP} s apart, -10 room / -13 TV / '
               f'-15 under the tape cry)')
    # ADD
    for a, name, g, space, params, why in ADD:
        try:
            t = _t(a, lines)
            p = dict(params)
            if isinstance(p.get('dur'), str) and p['dur'].startswith('until:'):
                p['dur'] = round(max(0.3, _t(p['dur'][6:], lines) - t), 2)
        except Exception as e:
            log.append(f'ADD {name} at {a}: bad anchor ({e!r}): skipped'); continue
        c = {'t': round(t, 3), 'name': name, 'gain_db': g, 'pan': 0.0, 'params': p, 'plan': 'sfx_plan'}
        if space:
            c['space'] = space
        out.append(c)
        log.append(f'ADD  {name:18s} {t:7.2f} {g:+5.1f} dB {space or "-":9s} {p}  ({why[:70]})')
    out.sort(key=lambda c: float(c.get('t', 0.0)) if isinstance(c.get('t'), (int, float)) else 1e9)
    return out, log


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--cues', default=os.path.join(MP.W, 'cues'))
    A = ap.parse_args()
    L, _d = MP.load_lines()
    sc = json.load(open(os.path.join(A.cues, 'sfx_cues.json')))
    new, lg = apply(sc, L)
    print('\n'.join(lg))
    print(f'{len(sc)} picture cues -> {len(new)} mixed cues')
