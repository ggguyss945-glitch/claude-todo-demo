"""The line map of "If a Girl Is OBSESSED With Being Your Only Friend... DON'T WRITE YOUR NAME" (Night Policy): writes
F/script/lines.py from the full script (script/narration_en.txt) and the exact interleaving of the takes
(script/voices/index.json "order": every narrator paragraph and character line, in script order, with who speaks).
    python3 tools/vo_lines.py          -> film/script/lines.py (prints the narrator-vs-order word check)
Every quote of the script that is the next character line of the order is that character's line (cut later from its
own take); any other quote (the cold open's "I can see your light's still on") is the narrator's.
Narration is split into sentences (an ellipsis before a lower-case word stays inside its sentence); a character's
quote is one line. en = the caption (the script's words, with the on-screen capitals: ONLY ME, DANNY, ADAM); say =
what the take says when it differs (Evie's "Under ONLY ME." is read "Under only me."): the edit and aligner match 'say'.
The "Ping." and "Clank." paragraphs are SOUNDS (not in any take): each becomes a beat after the line before it
(beats=['ping', ...], beat_t = each sound's offset after that line's end); the edit leaves room for them and writes
their times to W/align/beats.json.
PACE / FX below are the hand-set columns (by the caption text); the gap rules are in gap_after().
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
SCRIPT = os.path.join(os.path.dirname(FILM), 'script')
OUT = os.path.join(FILM, 'script', 'lines.py')
CHARS = ['evie', 'lina', 'mom', 'rahman', 'adam', 'adam7', 'danny']

# narrator lines kept whole (the sentence split would break them at each letter), caption -> spoken
SAY = {"O. N. L. Y.": "O. N. L. Y.", "Chalk fingers wrote M... E... toward the kitchen.":
       "Chalk fingers wrote M... E... toward the kitchen."}

# voice FX by staging (story bible registers). Everything else is dry (None); the narrator is never processed.
MESSAGE = ["Are you awake?", "Why aren't you answering?", "There. Now it's only me.",
           "Your mom's always on the phone about you. She thinks something's wrong with you.",
           "Your sister's a baby. Only I get you.",
           "Please stop. You're scaring me."]          # Danny's old message, read off Adam's phone
LETTERBOX = ["After everything I gave you.", "If you leave, it's your fault. I'll stand here forever.",
             "Write your name. Under ONLY ME."]
FX = dict([(k, 'message') for k in MESSAGE] + [(k, 'letterbox') for k in LETTERBOX] +
          [("Only me. I'm here, I'm he-", 'thin'),
           ("Me and you, and you and me, stick like glue, and you will see. Everywhere you go, I'm near. Only me. I'm here, I'm here.", 'tape')])

# gap after the line (s), set by hand for its moment (overrides gap_after's rules): the scare beats sit just after
# their key word; the holds are the few dread beats the picture needs. Tight and energetic, like the Buttons edit.
PACE = {
    "Especially if she doesn't blink.": 0.85,           # trailer wave 1 hit (cold open widened +2.5 s total)
    "If your phone is off... and it still lights up: \"I can see your light's still on\"... don't look out the window.": 0.85,                 # trailer wave 2 hit
    "And if you look down at midnight... and someone at your blue front door is smiling up, two words chalked at their feet...": 0.80,   # wave 3: counter to 47, the blue door
    "Wake a grown-up.": 1.25,                           # hard stop, a beat of black, the one silence
    "I know who it is.": 0.85,                          # the hook lands: title sting
    "At the top, one name, scribbled out in blue pen.": 0.33,
    "By Saturday midnight, she was on our doormat, my sister was reading a name under the landing light... and I was halfway down the stairs to let her in.": 0.45,
    "I ate alone.": 0.33,
    "Nobody else knows it.": 0.29,
    "The green-and-gold bracelet I wove him in third grade... gone.": 0.33,
    "She looked a beat too long.": 0.33,
    "The Keeping Square.": 0.33,
    "That person will never leave you.": 0.29,
    "Nobody was cruel enough to try it.": 0.37,
    "A smile that didn't stop.": 0.37,
    "Somebody waiting for me, for once.": 0.29,
    "We'd met on Monday.": 0.33,
    "Sleep.": 0.33,
    "Forty-seven.": 0.29,
    "I can see your light's still on.": 0.33,
    "ONLY ME.": 0.33,
    "She didn't blink.": 0.33,
    "Evie lay down flat, like a chalk drawing... and slid away.": 0.33,
    "Must have rained.": 0.29,
    "Good.": 0.29,
    "Pointing in.": 0.37,
    "If someone did that for you... would you feel Special, or Trapped?": 0.41,
    "Chalk dust on it.": 0.29,
    "It was Danny's bracelet.": 0.37,
    "Now I owed her.": 0.33,
    "Just past the corners.": 0.33,
    "Then in my room.": 0.29,
    "Nobody.": 0.28,
    "Just one white chalk fingerprint... on the inside of my window.": 0.33,
    "Outside, ONLY ME had reached the foot of our step.": 0.33,
    "There. Now it's only me.": 0.37,
    "There.": 0.29,
    "She never ran.": 0.33,
    "In my seven-year-old voice.": 0.41,
    "I was.": 0.65,                                     # the first reveal
    "The chalk slid out, flat across the playground... and stood up.": 0.33,
    "I ran.": 0.33,
    "Waiting for a name.": 0.37,
    "You're my only friend.": 0.37,
    "Right against our green front door.": 0.33,
    "There's a girl at our door. She's smiling up at your window.": 0.33,
    "Her chalk smile almost touched her ears.": 0.41,
    "Midnight.": 0.29,
    "O. N. L. Y.": 0.33,
    "Write your name. Under ONLY ME.": 0.37,
    "Halfway.": 0.33,
    "It says your name.": 0.33,
    "ADAM.": 0.65,
    "From me.": 0.75,                                   # whose rules they were
    "The letters crept across the tiles... and stopped at her chair.": 0.33,
    "And she'd kept asking, until I let her in.": 0.37,
    "Sent by me.": 0.33,
    "Please stop. You're scaring me.": 0.37,
    "That blue front door was Danny's.": 0.33,
    "It was me.": 0.90,                                 # the truth lands
    "He woke his mom.": 0.33,
    "Only me. I'm here, I'm he-": 0.70,                 # silence after the cut
    "Her colour drained to chalk-white, and the wind carried her off like dust.": 0.49,
    "Me and you, and others too, friends for me and friends for you. Go wherever, near or far. I'll still care, wherever you are.": 0.37,
    "That had to be okay.": 0.37,
    "The caretaker painted over the Keeping Square.": 0.37,
    "He's one of my best.": 0.41,
    "ONLY.": 0.33,
    "I only call once.": 0.95,                          # the story ends
    "You can turn a light on now.": 0.33,
    "Special, or Trapped?": 0.33,
}
# the sounds: offset of each from the line's end (s): the first after LEAD, the next in its paragraph STEP later, a new
# paragraph of sounds GAP later; then AFTER of room before the next line (each paragraph of sounds is a 0.5-0.9 s beat)
BEAT_LEAD, BEAT_STEP, BEAT_GAP, BEAT_AFTER = 0.12, 0.30, 0.55, 0.45


def strip_tags(s):
    return re.sub(r'\[[^\]]*\]\s*', '', s)


def toks(s):
    return re.findall(r"[a-z0-9]+", s.lower().replace("'", '').replace('-', ' '))


SENT = re.compile(r'(?<=[.?!])\s+(?=["A-Z])')
ABBR = re.compile(r'(?:\bMrs?|\bL)\.$')
BEAT = re.compile(r'(?:(?<=^)|(?<=\s))(Ping|Clank)\.(?=\s|$)')


def sentences(s):
    keep = {}
    for k, v in enumerate(SAY):                        # protect the lines kept whole
        if v in s: s = s.replace(v, 'QZ%dQZ' % k); keep['QZ%dQZ' % k] = v
    out = []
    for p in SENT.split(s.strip()):
        if out and ABBR.search(out[-1]): out[-1] += ' ' + p
        else: out.append(p)
    res = []
    for p in out:
        for k, v in keep.items(): p = p.replace(k, v)
        if p.strip(): res.append(p.strip())
    return res


def build():
    paras = [p.strip() for p in open(os.path.join(SCRIPT, 'narration_en.txt')).read().split('\n\n') if p.strip()]
    order = json.load(open(os.path.join(SCRIPT, 'voices', 'index.json')))['order']
    chars = [(w, t) for w, t in order if w != 'narrator']
    lines = []

    def add_narr(sn, pi):
        if lines and lines[-1].get('glue') and lines[-1]['para'] == pi and not re.search(r'[.?!]"?$', lines[-1]['en']):
            lines[-1]['en'] += ('' if re.match(r'[.?!,]', sn) else ' ') + sn; lines[-1].pop('glue'); return
        if lines and lines[-1].get('glue'): lines[-1].pop('glue')
        if sn[0].islower(): sn = sn[0].upper() + sn[1:]
        lines.append(dict(who='narrator', en=sn, para=pi, beats=[]))

    for pi, p in enumerate(paras):
        for seg in re.split(r'("[^"]*")', p):
            if not seg.strip(): continue
            if seg.startswith('"'):
                q = seg[1:-1].strip()
                if chars and toks(chars[0][1]) == toks(q):
                    w_, t_ = chars.pop(0)
                    lines.append(dict(who=w_, en=q, para=pi, beats=[]))
                    if t_ != q: lines[-1]['say'] = t_
                    continue
                if lines and lines[-1]['who'] == 'narrator' and lines[-1]['para'] == pi and not re.search(r'[.?!]$', lines[-1]['en']):
                    lines[-1]['en'] += ' ' + seg; lines[-1]['glue'] = True; continue
                lines.append(dict(who='narrator', en=seg, para=pi, beats=[], glue=True)); continue
            pos = 0
            for m in list(BEAT.finditer(seg)) + [None]:  # text, beat, text, ...
                txt = seg[pos:m.start() if m else len(seg)]
                for sn in sentences(txt): add_narr(sn, pi)
                if m:
                    lines[-1]['beats'].append(m.group(1).lower()); lines[-1].setdefault('bpara', []).append(pi); pos = m.end()
        if lines and lines[-1].get('glue'): lines[-1].pop('glue')
    assert not chars, chars
    for l in lines:
        if l['en'] in SAY: l['say'] = SAY[l['en']]
        if l['beats']:                                 # each sound's offset after the line's end
            bt, t = [], BEAT_LEAD
            for k, bp in enumerate(l['bpara']):
                if k: t += BEAT_STEP if bp == l['bpara'][k - 1] else BEAT_GAP
                bt.append(round(t, 2))
            l['beat_t'] = bt
    return lines, paras, order


def fixed(L, i):
    """The gap is set for its moment (a hold, a beat, a rule card): the edit keeps it exactly. Any other narrator gap
    is a ceiling: the edit keeps the take's own pause when that is shorter (tools/vo_edit.py)."""
    l = L[i]; n = L[i + 1] if i + 1 < len(L) else l
    return bool(l['en'] in PACE or l['beats'] or n['en'].startswith('Rule number') or l['en'].startswith('Rule number'))


def gap_after(L, i):
    l = L[i]
    if i == len(L) - 1: return 0.0
    n = L[i + 1]
    if l['en'] in PACE: g = PACE[l['en']]
    elif n['en'].startswith('Rule number'): g = 0.55
    elif l['en'].startswith('Rule number'): g = 0.22
    elif l['who'] != n['who']:                         # narrator action -> character line, and back
        g = 0.16 if l['who'] == 'narrator' else 0.20
    elif l['who'] != 'narrator': g = 0.22
    elif n['para'] != l['para']: g = 0.20
    elif len(toks(l['en'])) <= 3 or len(toks(n['en'])) <= 3: g = 0.12   # staccato fragments
    else: g = 0.14
    if l['beats']:                                     # room for the pings / clank, then a breath before the next line
        g = max(g, l['beat_t'][-1] + BEAT_AFTER + (0.05 if n['who'] != 'narrator' else 0))
    return g


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


def check(L, order):
    import difflib
    for who in ['narrator'] + CHARS:
        a = [w for l in L if l['who'] == who for w in toks(l.get('say', l['en']))]
        b = [w for ww, t in order if ww == who for w in toks(t)]
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        bad = [(op, a[i1:i2], b[j1:j2]) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != 'equal']
        print('%-8s words: lines %d, order %d, differences: %s' % (who, len(a), len(b), bad or 'none'))
    nb = sum(len(l['beats']) for l in L)
    print('beats: %d (%s)' % (nb, ', '.join('%s:%s' % (l['tag'], '+'.join(l['beats'])) for l in L if l['beats'])))


def main():
    L, paras, order = build()
    tags(L)
    check(L, order)
    rows = []
    for i, l in enumerate(L):
        fx = FX.get(l['en']) if l['who'] != 'narrator' else None
        ex = (', say=%r' % l['say'] if 'say' in l else '') + (', beats=%r, beat_t=%r' % (l['beats'], l['beat_t']) if l['beats'] else '') + (', fixed=True' if fixed(L, i) else '')
        rows.append('    L(%r, %r, %r, %.2f, tag=%r, para=%d%s),' % (l['who'], l['en'], fx, gap_after(L, i), l['tag'], l['para'], ex))
    head = ('"""Every spoken line of "If a Girl Is OBSESSED With Being Your Only Friend... DON\'T WRITE YOUR NAME" (Night\n'
            'Policy), in script order. GENERATED by film/tools/vo_lines.py from script/narration_en.txt and\n'
            'script/voices/index.json (edit the tables there and re-run, not this file).\n'
            'who: narrator (the grown-up Adam; also the cold open\'s quoted words), evie, lina (7), mom, rahman, adam (12),\n'
            '     adam7 (his song at seven, on the old camcorder tape), danny (12). A character line is cut from its own take\n'
            '     (W/narration/raw/index.json); Adam, little Adam and Danny are re-voiced from the narrator-voice kids takes,\n'
            '     Evie (about 12) and Lina (7) from Evie\'s young-adult takes (tools/vo_voices.py).\n'
            'en: the caption (the script\'s words, on-screen capitals kept); say: what the take says, when it differs.\n'
            'fx: how the line is heard, BAKED into W/narration/narration_en.wav by tools/vo_fx.py (the mix must not add it\n'
            '    again): message (Evie\'s messages and Danny\'s old one: close, a faint digital sheen), letterbox (through the\n'
            '    slot: close, flat, a little muffled), thin (her last sung line: stretched thin, cut off on "he-"), tape (little\n'
            '    Adam\'s song on the old VHS camcorder tape: warm, band-limited, wow and flutter); None = in the room, dry.\n'
            'pause: the silence after the line (s) in the edit (fixed: exactly; else a ceiling, see vo_edit.py). beats: the\n'
            '    Ping / Clank sounds (not in any take) placed in that pause, beat_t their offsets after the line\'s end\n'
            '    (W/align/beats.json has their times). para: the script paragraph. tag: unique.\n"""\n')
    src = head + ('def L(who, en, fx, pause, tag, para, say=None, beats=(), beat_t=(), fixed=False):\n'
                  '    return dict(who=who, en=en, say=say or en, fx=fx, pause=pause, tag=tag, para=para, beats=list(beats), beat_t=list(beat_t), fixed=fixed)\n\n\n'
                  'LINES = [\n' + '\n'.join(rows) + '\n]\n')
    open(OUT, 'w').write(src)
    from collections import Counter
    print('%d lines -> %s' % (len(L), OUT), dict(Counter(l['who'] for l in L)))
    print('fx:', dict(Counter(FX[l['en']] for l in L if l['en'] in FX and l['who'] != 'narrator')))
    ens = {l['en'] for l in L}
    print('table keys not found:', [k for k in list(FX) + list(PACE) + list(SAY) if k not in ens])


if __name__ == '__main__':
    main()
