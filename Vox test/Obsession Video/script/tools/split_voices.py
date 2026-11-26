"""Split narration_en.txt into clean per-voice line files for ElevenLabs (script/voices/).

Every quoted line goes to its speaker's file; the narrator keeps everything else, in order, in parts of at most
PART_MAX characters cut at paragraph ends (preferring a cut just before "Rule number" or the outro).
Sounds are not read: the "Ping." and "Clank." beats are dropped from the narrator (we place them as sounds).
On-screen capitals are written out for speech (ONLY ME -> only me, or Only me at a sentence start; DANNY -> Danny).
Adam (12, and 7 in the song) has no designed voice (ElevenLabs will not design child voices): his lines are one
adult take, read with the narrator's voice and pitched up by us. Evie keeps all her registers in one file
(story order); index.json says which line is sweet, too sweet or wrong.
Run: python3 tools/split_voices.py   (from script/)  -> voices/*.txt and voices/index.json
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.dirname(HERE)
SRC = os.path.join(SCRIPT, 'narration_en.txt')
OUT = os.path.join(SCRIPT, 'voices')
PART_MAX = 1750

# quoted line (its start) -> speaker, in script order. 'N' = the narrator reads it inside his own sentence.
WHO = [
    ("I can see your light's still on\"...", 'N'),       # cold open, read by the narrator
    ("Me and you, and you and me", 'adam7'),              # the song, age 7, sung (flashback)
    ("Anything you want to tell me?", 'mom'),             # Monday, the hoodie
    ("Art.", 'adam'),
    ("Hi! I'm Evie. Like forever.", 'evie'),
    ("You're my favourite person in the whole world.", 'evie'),
    ("My mom wrote these.", 'danny'),
    ("Are you awake?", 'evie'),
    ("Why aren't you answering?", 'evie'),
    ("I can see your light's still on.", 'evie'),
    ("I know. I'll talk to him.", 'mom'),
    ("I made it myself. For you. Only me?", 'evie'),
    ("Best friends share passwords.", 'evie'),
    ("Just checking in, Adam.", 'rahman'),
    ("There. Now it's only me.", 'evie'),
    ("You told her our song?", 'adam'),
    ("What song?", 'danny'),
    ("You asked for someone who'd never leave.", 'evie'),
    ("Your mom's always on the phone about you.", 'evie'),
    ("Your sister's a baby.", 'evie'),
    ("Anything you want to tell me?", 'mom'),             # Saturday dinner, fork down
    ("You're my only friend.", 'adam'),
    ("There's a girl at our door.", 'lina'),
    ("After everything I gave you.", 'evie'),
    ("If you leave, it's your fault.", 'evie'),
    ("Write your name. Under ONLY ME.", 'evie'),
    ("It says your name.", 'lina'),
    ("Thank you for telling me.", 'mom'),                 # to Adam, in the kitchen
    ("Please stop. You're scaring me.", 'danny'),         # his old message
    ("Danny was right to say no.", 'mom'),
    ("Write your name?", 'evie'),
    ("No. I'm not your only.", 'adam'),
    ("I hope you find lots of people.", 'adam'),
    ("He said no.", 'mom'),
    ("Only me. I'm here, I'm he-", 'evie'),               # sung, stretched, cut off
    ("Me and you, and others too", 'lina'),               # the healed song, sung
    ("I think I'm the one who couldn't let go.", 'adam'),
    ("That was brave. Caring isn't owning.", 'rahman'),
    ("Sorry. I'll give you space.", 'adam'),              # the message he types
    ("Can we sit here? All of us?", 'danny'),
    ("Yeah. All of you.", 'adam'),
    ("I crossed it out.", 'danny'),
    ("It's your fault\" is never true", 'N'),             # outro checklist, read by the narrator
]

# Evie's register per line, in story order (sweet -> too sweet -> wrong); checked against her file
EVIE_REGISTER = [
    'sweet', 'too sweet (does not blink)', 'too sweet (message, whispered)', 'too sweet (message, a little hurt)',
    'too sweet (dark screen, delighted)', 'too sweet', 'too sweet (wounded)', 'wrong (message, content)',
    'wrong (flat delight)', 'wrong (mouthed at the window, message voice)', 'wrong (same)',
    'wrong (letterbox, close and flat)', 'wrong (letterbox, then a clipped giggle)', 'wrong (whisper)',
    'sweet again on the doormat (bright, hopeful: the trap)', 'wrong (sung, stretched thin, cut off)',
]

SPEECH = [(r'(^|[.!?] )ONLY ME\b', r'\1Only me'), (r'\bONLY ME\b', 'only me'),
          (r'\bONLY\b', 'Only'), (r'\bDANNY\b', 'Danny'), (r'\bADAM\b', 'Adam')]
CUT_BEFORE = ('Rule number', 'Okay. Breathe.')   # preferred narrator part starts
SOUNDS = ('Ping.', 'Clank.')
SOUND_RE = r'(^|\s)(' + '|'.join(re.escape(s) for s in SOUNDS) + r')(?=\s|$)'


def speech(p):
    for a, b in SPEECH:
        p = re.sub(a, b, p)
    return p


def clean_narr(p):
    p = speech(p)
    p = re.sub(SOUND_RE, ' ', p)          # sounds, not words
    p = re.sub(r'\s+', ' ', p).strip()
    return p


def main():
    text = open(SRC).read().strip()
    paras = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    keys = ('narrator', 'adam7', 'adam', 'evie', 'danny', 'lina', 'mom', 'rahman')
    files = {k: [] for k in keys}
    order, wi = [], 0
    for p in paras:
        q = list(re.finditer(r'"([^"]*)"', p))
        narr, said = p, []
        for m in q:
            body = m.group(1)
            rest = p[m.start() + 1:]
            k = None
            for j in range(wi, len(WHO)):
                if rest.startswith(WHO[j][0]) or body.startswith(WHO[j][0]):
                    k = j
                    break
            if k is None:
                raise SystemExit('no speaker for quote: %r' % body)
            if k != wi:
                raise SystemExit('quote %r matched WHO entry %d, expected %d (%r)' % (body, k, wi, WHO[wi][0]))
            wi = k + 1
            who = WHO[k][1]
            if who == 'N':
                continue
            said.append((who, speech(body)))
            narr = narr.replace(m.group(0), ' ', 1)
        narr = clean_narr(narr)
        # a paragraph's narrator words come before its quote (action, then the line)
        if narr and not re.fullmatch(r'[.…\s]*', narr):
            files['narrator'].append(narr)
            order.append(('narrator', narr))
        for who, body in said:
            files[who].append(body)
            order.append((who, body))
    if wi != len(WHO):
        raise SystemExit('unused speaker entries from %r' % (WHO[wi][0],))
    if len(files['evie']) != len(EVIE_REGISTER):
        raise SystemExit('Evie has %d lines but %d register notes' % (len(files['evie']), len(EVIE_REGISTER)))
    os.makedirs(OUT, exist_ok=True)
    for old in os.listdir(OUT):
        if old.endswith('.txt') or old == 'index.json':
            os.remove(os.path.join(OUT, old))
    # narrator parts, cut at paragraph ends, preferring a cut just before "Rule number"
    parts, cur = [], []
    for p in files['narrator']:
        n = len('\n\n'.join(cur + [p]))
        if cur and n > PART_MAX:
            # step back to the last "Rule number" start in this part if it leaves a part of reasonable size
            cut = len(cur)
            for i in range(len(cur) - 1, 0, -1):
                if cur[i].startswith(CUT_BEFORE) and len('\n\n'.join(cur[:i])) > PART_MAX * 0.55:
                    cut = i
                    break
            parts.append(cur[:cut])
            cur = cur[cut:]
        cur.append(p)
    parts.append(cur)
    # no tiny last part: re-cut the last two parts, at a preferred start if one keeps both under PART_MAX,
    # else at the paragraph end nearest the middle
    if len(parts) > 1 and len('\n\n'.join(parts[-1])) < PART_MAX * 0.35:
        both = parts[-2] + parts[-1]
        fits = [i for i in range(1, len(both)) if len('\n\n'.join(both[:i])) <= PART_MAX
                and len('\n\n'.join(both[i:])) <= PART_MAX]
        half = len('\n\n'.join(both)) / 2
        pref = [i for i in fits if both[i].startswith(CUT_BEFORE)]
        cut = min(pref or fits, key=lambda i: abs(len('\n\n'.join(both[:i])) - half))
        parts[-2:] = [both[:cut], both[cut:]]
    idx = {'narrator_parts': []}
    for i, ps in enumerate(parts, 1):
        name = 'narrator_part%d.txt' % i
        body = '\n\n'.join(ps)
        assert len(body) <= PART_MAX, (name, len(body))
        open(os.path.join(OUT, name), 'w').write(body + '\n')
        idx['narrator_parts'].append({'file': name, 'chars': len(body), 'paragraphs': len(ps),
                                      'starts': ps[0][:40]})
    for who in ('evie', 'danny', 'lina', 'mom', 'rahman'):
        open(os.path.join(OUT, who + '.txt'), 'w').write('\n\n'.join(files[who]) + '\n')
        idx[who] = len(files[who])
    idx['evie'] = {'lines': len(files['evie']),
                   'note': 'One file, story order. Designed young-adult woman voice, shifted younger. '
                           'Registers: sweet -> too sweet -> wrong; see registers.',
                   'registers': [{'line': i + 1, 'register': r, 'text': t}
                                 for i, (r, t) in enumerate(zip(EVIE_REGISTER, files['evie']))]}
    kids = files['adam7'] + files['adam']
    open(os.path.join(OUT, 'kids_adult_take.txt'), 'w').write('\n\n'.join(kids) + '\n')
    idx['kids_adult_take'] = {'adam_age7': len(files['adam7']), 'adam_age12': len(files['adam']),
                              'note': 'Line 1 is Adam at 7 (the song, sung sweetly, pitched higher); lines 2 on '
                                      'are Adam at 12, in story order. One adult take with the narrator voice, '
                                      'pitched up by us.'}
    idx['order'] = order
    json.dump(idx, open(os.path.join(OUT, 'index.json'), 'w'), indent=1, ensure_ascii=False)
    for k in idx['narrator_parts']:
        print(k)
    print({'evie': idx['evie']['lines'], 'danny': idx['danny'], 'lina': idx['lina'], 'mom': idx['mom'],
           'rahman': idx['rahman'], 'kids_adult_take': {k: v for k, v in idx['kids_adult_take'].items()
                                                         if k != 'note'}})
    # words check: every word of the script is in exactly one file, minus the dropped sounds
    # (spoken-out capitals keep the word count)
    allw = ' '.join(x for _, x in order)
    sounds = len(re.findall(SOUND_RE, text))
    got, want = len(allw.split()), len(text.split()) - sounds
    print('words in files', got, '| script words', len(text.split()), '- sounds', sounds, '=', want)
    if got != want:
        raise SystemExit('word check failed')


main()
