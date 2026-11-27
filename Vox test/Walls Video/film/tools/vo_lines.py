"""The line map of "If Your Little Brother Says Someone Lives In The Walls... DON'T LAUGH" (Night Policy): writes
F/script/lines.py from the full script (script/narration_en.txt) and the per-voice texts the takes were made from
(script/voices_v4/*.txt, audio tags stripped; the same words as script/voices/).
    python3 tools/vo_lines.py          -> film/script/lines.py (prints the narrator-vs-take word check)
Every quoted stretch of the script that opens the next unread words of a character's take is that character's line
(cut later from its own take); any other quote ("Night, Dad," I almost said; Change it to "person.") is the narrator's.
Narration is split into sentences (an ellipsis before a lower-case word stays inside its sentence); a character's
quote is one line (it is cut from its take as one utterance). The take is the truth for the words: the narrator reads
'"Mice," said Dad.' as "Dad said." (voices_v4/narrator_part2.txt).
PACE / FX / HOLD below are the hand-set columns (by the line's text); the gap rules are in gap_after().
"""
import os, re, json

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
SCRIPT = os.path.join(os.path.dirname(FILM), 'script')
OUT = os.path.join(FILM, 'script', 'lines.py')
CHARS = ['dad', 'mom', 'theo', 'sam', 'dabrowski', 'pell', 'dispatcher', 'officer']
# where each character take sits (index.json key); Theo and Sam share the adult take (Theo first)
TAKE = {'dad': 'dad', 'mom': 'mom', 'theo': 'theo_and_sam_adult_take', 'sam': 'theo_and_sam_adult_take',
        'dabrowski': 'dabrowski', 'pell': 'pell', 'dispatcher': 'dispatcher', 'officer': 'officer'}

# voice FX by staging (line text -> fx). Everything else is dry (None).
FX = {
    'Off.': 'ceiling',                                        # from inside the sealed attic, right above Sam's head
    "Fourteen Larkspur Lane... that's my house.": 'wall',      # inside the wall by Sam's bed
    "Just the pipes. Old houses settle. It's only mice. Go back to sleep.": 'wall',
    'Hush-a-bye,': 'mask',                                     # in the room, through the rubber mask
    'Shhh. Just the pipes.': 'mask',
    "Hush-a-bye. That's my house.": 'vent',                    # through the floor vent's grille
    'That was my room,': 'outdoor',                            # unmasked, outdoors: dry
    'When I was a boy.': 'outdoor',
    "What's the address of your emergency?": 'phone',          # the dispatcher through Mom's phone speaker
    'Stay in that room,': 'phone',
    'Keep the door locked. Officers are two minutes away. Stay on the line with me.': 'phone',
}
# gap after the line (s), set by hand for its moment (overrides gap_after's rules); the scare beats sit just after
# their key word, the holds are the few dread beats the picture needs. Tight like the Ice Cream edit.
PACE = {
    "If your little brother says someone lives in the walls... don't laugh.": 0.45,
    "If the armchair is warm in the morning, and nobody sat in it... don't say it's the heater.": 0.45,
    "Your dad is asleep.": 1.10,                     # the hook lands: title sting
    "Every explanation was wrong.": 0.60,
    "By morning, there would be three police cars on our lawn, a hole in my closet wall, and a man with a dog's face sitting on our curb in handcuffs, telling the officers that we were the ones living in his house.": 0.80,
    'Just watching us sleep.': 0.50,
    'Dad read it out loud, and laughed.': 0.15,
    "Because they knew where a sad dog face came from.": 0.40,
    "Nobody checked.": 0.80,
    "That's when Theo made his rules.": 0.55,
    "When something knocks inside your wall at night, what is it?": 0.40,
    "Ghost, or pipes?": 0.45,
    "Slowly.": 0.20, "All by itself.": 0.45,
    "Click.": 0.40, "Unlocked.": 0.30, "From the kitchen side.": 0.50,
    "Nobody I could see.": 0.75,
    "Like someone polite had been eating our food.": 0.50,
    "I leaned in.": 0.30,
    "An eye leaned in on the other side.": 0.50,
    "In a face made of rubber.": 0.40,
    "It blinked.": 0.55,
    "It was August.": 0.20, "The heat had been off since June.": 0.50,
    "In a red shirt.": 0.50,
    "So that we would never see all of them together.": 0.75,
    "Remember the hall switch that does nothing?": 0.45,
    "And a voice in the ceiling, right above my head, whispered,": 0.30,
    "Off.": 0.75,
    "I didn't open it.": 0.40,
    "In a man's voice.": 0.20, "Slow.": 0.18, "Low.": 0.18, "Wrong.": 0.40,
    "Fourteen Larkspur Lane... that's my house.": 0.70,
    "It wasn't Dad's voice.": 0.30,
    "They were Dad's words.": 0.50,
    "By the man who wanted us to have an excuse for every sign he left.": 0.75,
    "I heard my dad snore.": 0.80,
    "Human teeth.": 0.55,
    "Like he'd done it a hundred times.": 0.35,
    "Hush-a-bye,": 0.40,
    "Shhh. Just the pipes.": 0.45,
    "Then nothing.": 0.70,
    "Just enough to watch me go.": 0.45,
    "Your shirt is upstairs. He's wearing it.": 0.45,
    "My dad looked at my face.": 0.20,
    "And for the first time all summer, he didn't explain anything.": 0.50,
    "And my mom, in a brand new house, at three in the morning... couldn't remember it.": 0.45,
    "Theo could.": 0.40,
    "So we stayed.": 0.20,
    "Hush-a-bye. That's my house.": 0.80,
    "Empty.": 0.70,
    "Just a tired old man with grey stubble, blinking in the flashlight.": 0.35,
    "Lawrence Pell,": 0.15,
    "He had lived in our walls for four months.": 0.70,
    "When I was a boy.": 0.70,
    "Fresh pencil.": 0.30,
    "Dated last week.": 0.90,
    "There was no rule seven.": 0.45,
    "Rule seven was two words.": 0.50,
    "Believe me.": 1.30,                              # the story ends
    "Okay.": 0.30, "Breathe.": 0.30,
    "Feeling silly is fine.": 0.40,
    "So here's the real list.": 0.40,
    "Person.": 0.55,
    "Sleep well.": 0.20,
    "And if your little brother tells you something tonight...": 0.55,
}


# Owner, 23 Nov: the narrator's dialogue tags are cut (every character speaks in their own voice). drop=True lines stay
# in the map (the take's words must still be matched to a line) but vo_edit.py leaves them out of the track and
# align.py out of the timeline. W/narration/drop_tags.json lists the same 17.
DROP = {'dad_said_and', 'i_said', 'theo_said', 'dad_said', 'dad_told_mom', 'dad_said_2', 'i_said_2', 'dad_said_3',
        'she_said', 'mom_said', 'dad_sighed', 'he_whispered', 'i_said_3', 'he_sang_into', 'the_dispatcher_said',
        'she_said_2', 'he_said'}


def strip_tags(s):
    return re.sub(r'\[[^\]]*\]\s*', '', s)


def toks(s):
    return [w for w in re.findall(r"[a-z0-9]+", s.lower().replace("'", '').replace('-', ' '))]


SENT = re.compile(r'(?<=[.?!])\s+(?=["A-Z])')
ABBR = re.compile(r'(?:\bMrs?|\bL)\.$')


def sentences(s):
    out = []
    for p in SENT.split(s.strip()):
        if out and ABBR.search(out[-1]): out[-1] += ' ' + p
        else: out.append(p)
    return [p for p in out if p.strip()]


def build():
    paras = [p.strip() for p in open(os.path.join(SCRIPT, 'narration_en.txt')).read().split('\n\n') if p.strip()]
    queue = {c: toks(strip_tags(open(os.path.join(SCRIPT, 'voices_v4', c + '.txt')).read())) for c in CHARS}
    lines = []
    for pi, p in enumerate(paras):
        p = p.replace('"Mice," said Dad.', '"Mice," Dad said.')
        parts = re.split(r'("[^"]*")', p)
        for seg in parts:
            if not seg.strip(): continue
            if seg.startswith('"'):
                q = seg[1:-1].strip(); qt = toks(q)
                who = next((c for c in CHARS if queue[c][:len(qt)] == qt), None)
                if who:
                    queue[who] = queue[who][len(qt):]
                    lines.append(dict(who=who, en=q, para=pi)); continue
                # a quote the narrator says himself: glue it to the narration around it
                if lines and lines[-1]['who'] == 'narrator' and lines[-1]['para'] == pi and not re.search(r'[.?!]$', lines[-1]['en']):
                    lines[-1]['en'] += ' ' + seg; continue
                lines.append(dict(who='narrator', en=seg, para=pi, glue=True)); continue
            s = seg.strip()
            if lines and lines[-1].get('glue') and lines[-1]['para'] == pi:
                ss = sentences(s)
                if lines[-1]['en'].endswith(',"'): lines[-1]['en'] += ' ' + ss.pop(0)   # "Night, Dad," I almost said.
                lines[-1].pop('glue')
            else:
                ss = sentences(s)
            for k, sn in enumerate(ss):
                sn = sn.strip()
                if sn[0].islower() and not sn.startswith('couldn'): sn = sn[0].upper() + sn[1:]
                lines.append(dict(who='narrator', en=sn, para=pi))
        if lines and lines[-1].get('glue'): lines[-1].pop('glue')
    left = {c: q for c, q in queue.items() if q}
    assert not left, left
    return lines, paras


def gap_after(L, i):
    l = L[i]
    if i == len(L) - 1: return 0.0
    n = L[i + 1]
    if l['en'] in PACE: return PACE[l['en']]
    if n['en'].startswith('Rule number'): return 0.70
    if l['en'].startswith('Rule number'): return 0.30
    same = n['para'] == l['para']
    if l['who'] != n['who']:                       # a quote and its dialogue tag flow into each other
        return 0.12 if same else 0.30
    if l['who'] != 'narrator': return 0.30
    if not same: return 0.32
    if len(toks(l['en'])) <= 3 or len(toks(n['en'])) <= 3: return 0.18   # staccato fragments
    return 0.20


def tags(L):
    seen, rule = {}, None
    for i, l in enumerate(L):
        m = re.match(r'Rule number (\w+)\.', l['en'])
        if m: rule = m.group(1); t = 'rule_' + rule
        elif rule and i > 0 and L[i - 1]['en'].startswith('Rule number'): t = 'rule_%s_text' % rule
        else:
            w = toks(l['en'])[:3]
            t = ('' if l['who'] == 'narrator' else l['who'] + '_') + '_'.join(w)
        k = seen.get(t, 0); seen[t] = k + 1
        l['tag'] = t if k == 0 else '%s_%d' % (t, k + 1)


def check_narrator(L):
    import difflib
    a = [w for l in L if l['who'] == 'narrator' for w in toks(l['en'])]
    b = []
    for k in range(1, 7): b += toks(strip_tags(open(os.path.join(SCRIPT, 'voices_v4', 'narrator_part%d.txt' % k)).read()))
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    bad = [(op, a[i1:i2], b[j1:j2]) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != 'equal']
    print('narrator words: lines %d, takes %d, differences: %s' % (len(a), len(b), bad or 'none'))


def main():
    L, paras = build()
    tags(L)
    check_narrator(L)
    rows = []
    for i, l in enumerate(L):
        fx = FX.get(l['en']) if l['who'] != 'narrator' else None
        rows.append('    L(%r, %r, %r, %.2f, tag=%r, para=%d%s),' % (l['who'], l['en'], fx, gap_after(L, i), l['tag'], l['para'],
                                                                     ', drop=True' if l['tag'] in DROP else ''))
    head = ('"""Every spoken line of "If Your Little Brother Says Someone Lives In The Walls... DON\'T LAUGH" (Night Policy),\n'
            'in script order. GENERATED by film/tools/vo_lines.py from script/narration_en.txt and script/voices_v4/*.txt (edit\n'
            'the tables there and re-run, not this file).\n'
            'who: narrator (the grown-up Sam; also his own quoted words), dad, mom, theo, sam, dabrowski, pell, dispatcher,\n'
            '     officer. A character line is cut from that character\'s own take (W/narration/raw/index.json); Theo and Sam\n'
            '     are re-voiced from the adult take into child voices (tools/vo_voices.py).\n'
            'fx: where the line is heard, BAKED into W/narration/narration_en.wav by tools/vo_fx.py (the mix must not add it\n'
            '    again): ceiling (Pell in the sealed attic), wall (inside the wall by Sam\'s bed), mask (in the room, through\n'
            '    the rubber mask), vent (through the floor vent), phone (the dispatcher on the phone speaker), outdoor\n'
            '    (unmasked at the curb: dry); None = in the room, dry.\n'
            'pause: the silence after the line (s) in the edit. para: the script paragraph. tag: unique.\n"""\n')
    src = head + ('def L(who, en, fx, pause, tag, para, drop=False):\n'
                  '    return dict(who=who, en=en, fx=fx, pause=pause, tag=tag, para=para, drop=drop)\n\n\nLINES = [\n' + '\n'.join(rows) + '\n]\n')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'w').write(src)
    from collections import Counter
    print('%d lines -> %s' % (len(L), OUT), dict(Counter(l['who'] for l in L)))
    print('fx:', {l['en']: FX[l['en']] for l in L if l['en'] in FX})
    miss = [k for k in list(FX) + list(PACE) if k not in {l['en'] for l in L}]
    print('table keys not found:', miss)


if __name__ == '__main__':
    main()
