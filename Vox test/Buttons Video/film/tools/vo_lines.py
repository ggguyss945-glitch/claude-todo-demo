"""The line map of "If Your Mom's Eyes Turn Into Buttons... DON'T KEEP HER SECRET" (Night Policy): writes
F/script/lines.py from the full script (script/narration_en.txt) and the exact interleaving of the takes
(script/voices/index.json "order": every narrator paragraph and character line, in script order, with who speaks).
    python3 tools/vo_lines.py          -> film/script/lines.py (prints the narrator-vs-order word check)
Every quote of the script that is the next character line of the order is that character's line (cut later from its
own take); any other quote ("Your mom doesn't even see you"... don't answer.) is the narrator's.
Narration is split into sentences (an ellipsis before a lower-case word stays inside its sentence); a character's
quote is one line. en = the caption (the script's words, with the on-screen capitals); say = what the take says when
it differs (FRI. read as "Friday", the board messages in normal case): the edit and the aligner match 'say'.
The "Tik." and "Ping." beats are SOUNDS (not in any take): each becomes a beat after the line before it
(beats=['tik'] ...); the edit leaves room for it and writes its time to W/align/beats.json.
PACE / FX below are the hand-set columns (by the caption text); the gap rules are in gap_after().
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
SCRIPT = os.path.join(os.path.dirname(FILM), 'script')
OUT = os.path.join(FILM, 'script', 'lines.py')
CHARS = ['mom', 'blank', 'owen', 'son', 'dunn', 'mensah']

# lines kept whole (the sentence split would break them at FRI. / A.M.); caption -> spoken (the take's words)
SAY = {
    "On the fridge: FRI. O'S BIRTHDAY.": "On the fridge: Friday. O's birthday.",
    "Under FRI, I wrote: MOM IT'S OWEN I'M HERE.": "Under Friday, I wrote: Mom, it's Owen. I'm here.",
    "THE CHAT. THE PHOTO. THE COAT. THE CAR. 2 A.M. I WISHED FOR A DIFFERENT MOM.":
        "The chat. The photo. The coat. The car. Two a.m. I wished for a different mom.",
}

# voice FX by staging (the Blank's lines by text; Mom's phone line). Everything else is dry (None).
WHISPER = ["Your mom doesn't even see you. I can be her. Tell me about her.", "What color are her eyes?",
           "That's okay. I'll see you for both of us.", "You're so grown-up. Send me your view, so I can picture you.",
           "I see you.", "Because she never even looked. Don't tell her.",
           "Tell her about me, and she'll know you wished for a different mom. Your fault.",
           "Come to the kitchen, baby.", "I could be your dad. What color are his eyes?"]
DOUBLE = ["Sit. Say something. I like to hear where you are.", "Or I tell her what you wished.",
          "It's not a secret. It's a surprise. Your mom finds out when we're gone. On your birthday, you button up... and I take you home.",
          "Watch. She doesn't even see you.", "Only I see you."]
TALL = ["Button up, sweetheart. We're going home.",
        "Happy birthday. She can't hear you. Only me. Button up. We're going home.",
        "One for warm... two for snug... three for Mama's button hug...",
        "Top one's yours, sweetheart. Mama keeps you. Say goodbye.", "Tell me where you are."]
FX = dict([(k, 'whisper') for k in WHISPER] + [(k, 'double') for k in DOUBLE] + [(k, 'tall') for k in TALL] +
          [("Get in, sweetheart. I got off early. Pancakes?", 'car'), ("Baby? I'm at the table. Where are you?", 'phone')])

# gap after the line (s), set by hand for its moment (overrides gap_after's rules): the scare beats sit just after
# their key word; the holds are the few dread beats the picture needs. Tight and energetic, like the Walls edit.
PACE = {
    "And if your mom holds your coat open at midnight, with two shiny black buttons where her eyes should be...": 0.35,
    "Button up, sweetheart. We're going home.": 0.45,
    "...don't.": 0.45,
    "Talking to the police.": 0.85,                     # the hook lands: title sting
    "The Brave List.": 0.40,
    "At eleven, I broke four of them in one week.": 0.45,
    "By midnight on my birthday, a police officer stood in our kitchen, my mom was crying my name... and I was standing right next to her.": 0.60,
    "In a jar by my headset.": 0.70,
    "One minute.": 0.40,
    "She didn't even look.": 0.45,
    "She hadn't sung it in years.": 0.45,
    "I wish I had a different mom.": 0.65,             # + the ping
    "Our song.": 0.35,
    "I don't know.": 0.40,
    "So I named her.": 0.15, "The Blank.": 0.45,
    "Her kind hunt one thing: a kid who feels invisible... and tells strangers instead of home.": 0.60,
    "Send.": 0.40,
    "On my closet door, rule one went pale.": 0.45,
    "Two black buttons flashed.": 0.45,
    "I see you.": 0.40,
    "Gone.": 0.45,
    "And she was outside... wearing my mom.": 0.65,
    "Buttons, or Mom?": 0.65,
    "I hid it in my closet.": 0.40,
    "Like a photo left in the sun.": 0.45,
    "I opened the closet.": 0.35,
    "Like somebody was inside it.": 0.40,
    "Then, slowly, it sagged.": 0.20,
    "And I'd typed that.": 0.45,
    "Buttons.": 0.45,
    "And kept coming.": 0.25,
    "Fingers tapping the air, reaching for my hood.": 0.45,
    "Then, just tire tracks.": 0.50,
    "Half a secret is still a secret.": 0.45,
    "She turned, and took the glasses off.": 0.20,
    "The Blank was in front of it.": 0.45,
    "Rule four faded.": 0.45,
    "Standing behind me.": 0.50,
    "She didn't even sit down.": 0.50,
    "Her bun brushed the lamp.": 0.40,
    "For one second, I couldn't tell my mothers apart.": 0.45,
    "Only you.": 0.45,
    "Her head set the lamp swinging.": 0.45,
    "The headset lady was still on the phone.": 0.65,
    "I couldn't see me.": 0.60,
    "I was standing in my own kitchen.": 0.50,
    "Like she'd heard a whisper.": 0.50,
    "My birthday.": 0.45,
    "Holding open... the red coat.": 0.40,
    "Happy birthday. She can't hear you. Only me. Button up. We're going home.": 0.60,
    "One for warm... two for snug... three for Mama's button hug...": 0.30,
    "The song stopped.": 0.45,
    "Top one's yours, sweetheart. Mama keeps you. Say goodbye.": 0.45,
    "NO!": 0.40,
    "She was left holding a red coat with nobody in it.": 0.50,
    "Tell me where you are.": 0.50,
    "And I told my mom.": 0.50,
    "The marker squeaked.": 0.20,
    "Tell me. I'm listening.": 0.45,
    "The long fingers were an inch from my hood.": 0.40,
    "And my mom's eyes found me.": 0.35,
    "There you are.": 0.45,
    "Mid-reach.": 0.45,
    "Green.": 0.60,
    "Now I was looking.": 0.50,
    "She did look.": 0.45,
    "Mama sees you. Say goodnight.": 0.95,              # the story ends
    "Just like her.": 0.50,
    "The jar was empty.": 0.65,
    "At the window next to his.": 0.50,
    "Brown. Your eyes are brown.": 0.45,
    "Still waiting.": 0.85,
    "Breathe.": 0.30,
    "You should know what color they are.": 0.00,
}
BEAT_LEAD, BEAT_STEP, BEAT_AFTER = 0.15, 0.35, 0.42   # beat: sound at line end + lead (+ step per extra tik), then room


def strip_tags(s):
    return re.sub(r'\[[^\]]*\]\s*', '', s)


def toks(s):
    return re.findall(r"[a-z0-9]+", s.lower().replace("'", '').replace('-', ' '))


SENT = re.compile(r'(?<=[.?!])\s+(?=["A-Z])')
ABBR = re.compile(r'(?:\bMrs?|\bL)\.$')
BEAT = re.compile(r'(?:(?<=^)|(?<=\s))(Tik|Ping)\.(?=\s|$)')


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
                if chars and chars[0][1] == q:
                    lines.append(dict(who=chars.pop(0)[0], en=q, para=pi, beats=[])); continue
                if lines and lines[-1]['who'] == 'narrator' and lines[-1]['para'] == pi and not re.search(r'[.?!]$', lines[-1]['en']):
                    lines[-1]['en'] += ' ' + seg; lines[-1]['glue'] = True; continue
                lines.append(dict(who='narrator', en=seg, para=pi, beats=[], glue=True)); continue
            pos = 0
            for m in list(BEAT.finditer(seg)) + [None]:  # text, beat, text, ...
                txt = seg[pos:m.start() if m else len(seg)]
                for sn in sentences(txt): add_narr(sn, pi)
                if m:
                    lines[-1]['beats'].append(m.group(1).lower()); pos = m.end()
        if lines and lines[-1].get('glue'): lines[-1].pop('glue')
    assert not chars, chars
    for l in lines:
        if l['en'] in SAY: l['say'] = SAY[l['en']]
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
    elif n['en'].startswith('Rule number'): g = 0.70
    elif l['en'].startswith('Rule number'): g = 0.30
    elif l['who'] != n['who']:                         # narrator action -> character line, and back
        g = 0.22 if l['who'] == 'narrator' else 0.28
    elif l['who'] != 'narrator': g = 0.30
    elif n['para'] != l['para']: g = 0.32
    elif len(toks(l['en'])) <= 3 or len(toks(n['en'])) <= 3: g = 0.18   # staccato fragments
    else: g = 0.20
    if l['beats']:                                     # room for the tik / ping, then a breath before the next line
        g = max(g, BEAT_LEAD + BEAT_STEP * (len(l['beats']) - 1) + BEAT_AFTER + (0.05 if n['who'] != 'narrator' else 0))
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
        ex = (', say=%r' % l['say'] if 'say' in l else '') + (', beats=%r' % l['beats'] if l['beats'] else '') + (', fixed=True' if fixed(L, i) else '')
        rows.append('    L(%r, %r, %r, %.2f, tag=%r, para=%d%s),' % (l['who'], l['en'], fx, gap_after(L, i), l['tag'], l['para'], ex))
    head = ('"""Every spoken line of "If Your Mom\'s Eyes Turn Into Buttons... DON\'T KEEP HER SECRET" (Night Policy), in\n'
            'script order. GENERATED by film/tools/vo_lines.py from script/narration_en.txt and script/voices/index.json\n'
            '(edit the tables there and re-run, not this file).\n'
            'who: narrator (the grown-up Owen; also his own quoted words), mom, blank, owen, son, dunn, mensah. A character\n'
            '     line is cut from that character\'s own take (W/narration/raw/index.json); Owen (11) and his son (10) are\n'
            '     re-voiced from the adult take into child voices (tools/vo_voices.py).\n'
            'en: the caption (the script\'s words, on-screen capitals kept); say: what the take says, when it differs.\n'
            'fx: how the line is heard, BAKED into W/narration/narration_en.wav by tools/vo_fx.py (the mix must not add it\n'
            '    again): whisper (the Blank\'s chat messages, the card, "I see you.", the sting: close whisper, faint cold\n'
            '    digital sheen), car (her car line: as dry as the real Mom), double (2 a.m. and dinner: a subtle too-smooth\n'
            '    double), tall (cold open, midnight, climax and her song: the tall form, a lower detuned double and size),\n'
            '    phone (Mom on Owen\'s phone speaker); None = in the room, dry.\n'
            'pause: the silence after the line (s) in the edit (fixed: exactly; else a ceiling, see vo_edit.py). beats: the Tik / Ping sounds (not in any take) placed in\n'
            '    that pause (W/align/beats.json has their times). para: the script paragraph. tag: unique.\n"""\n')
    src = head + ('def L(who, en, fx, pause, tag, para, say=None, beats=(), fixed=False):\n'
                  '    return dict(who=who, en=en, say=say or en, fx=fx, pause=pause, tag=tag, para=para, beats=list(beats), fixed=fixed)\n\n\n'
                  'LINES = [\n' + '\n'.join(rows) + '\n]\n')
    open(OUT, 'w').write(src)
    from collections import Counter
    print('%d lines -> %s' % (len(L), OUT), dict(Counter(l['who'] for l in L)))
    print('fx:', dict(Counter(FX[l['en']] for l in L if l['en'] in FX and l['who'] != 'narrator')))
    ens = {l['en'] for l in L}
    print('table keys not found:', [k for k in list(FX) + list(PACE) + list(SAY) if k not in ens])


if __name__ == '__main__':
    main()
