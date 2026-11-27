"""Split narration_en.txt into clean per-voice line files for ElevenLabs (script/voices/).

Every quoted line goes to its speaker's file; the narrator keeps everything else, in order, in parts of at most
PART_MAX characters cut at paragraph ends (so the Eleven v4 copies with tags stay under 2,400).
Sounds are not read: the "Tik." and "Ping." beats are dropped from the narrator (we place them as sounds).
On-screen capitals are written out for speech (FRI. -> Friday, the board messages in normal case).
Owen (11) and his son (10) have no designed voice (ElevenLabs will not design child voices): their lines are one
adult take, read with the narrator's voice, and we re-voice them ourselves (as in the Walls film).
Run: python3 tools/split_voices.py   (from script/)  -> voices/*.txt and voices/index.json
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.dirname(HERE)
SRC = os.path.join(SCRIPT, 'narration_en.txt')
OUT = os.path.join(SCRIPT, 'voices')
PART_MAX = 1750

# quoted line (its start) -> speaker. 'N' = the narrator reads it inside his own sentence.
WHO = [
    ("Your mom doesn't even see you\"...", 'N'),          # cold open, read by the narrator
    ("Button up, sweetheart. We're going home.", 'blank'),
    ("Thank you for calling. I'm listening.", 'mom'),
    ("One minute.", 'mom'),
    ("I'm listening.\" I got", 'N'),                     # "Strangers got "I'm listening."": the narrator
    ("One for warm and two for snug", 'mom'),             # the song, sung warm (flashback)
    ("I wish I had a different mom.", 'owen'),
    ("Your mom doesn't even see you. I can be her.", 'blank'),
    ("What color are her eyes?", 'blank'),
    ("I don't know.", 'owen'),                            # first time; the son's is below (by order)
    ("That's okay. I'll see you for both of us.", 'blank'),
    ("You're so grown-up.", 'blank'),
    ("I see you.", 'blank'),
    ("Because she never even looked.", 'blank'),          # the card
    ("It says delivered. On the mat.", 'mom'),
    ("Get in, sweetheart. I got off early.", 'blank'),
    ("Baby? I'm at the table.", 'mom'),
    ("You did right. You checked.", 'dunn'),
    ("Silver car. Dented bumper. Now.", 'dunn'),
    ("Tell her about me", 'blank'),
    ("Come to the kitchen, baby.", 'blank'),
    ("Sit. Say something.", 'blank'),
    ("Or I tell her what you wished.", 'blank'),
    ("It's not a secret. It's a surprise.", 'blank'),
    ("Your mom finds out when we're gone\" is", 'N'),
    ("Watch. She doesn't even see you.", 'blank'),
    ("No... I can't see him anywhere.", 'mom'),
    ("Only I see you.", 'blank'),
    ("Only you.", 'owen'),
    ("He's eleven. Green coat.", 'mom'),
    ("Mom. I'm here. I feel invisible.", 'owen'),
    ("Happy birthday. She can't hear you.", 'blank'),
    ("One for warm... two for snug", 'blank'),            # the song, detuned, at the climax
    ("Top one's yours, sweetheart.", 'blank'),
    ("NO!", 'owen'),
    ("Tell me where you are.", 'blank'),
    ("Ma'am. The board.", 'mensah'),
    ("Tell me. I'm listening.", 'mom'),
    ("There you are.", 'mom'),
    ("Green.", 'owen'),
    ("My package. That was a surprise.", 'mom'),
    ("No more one finger.", 'mom'),
    ("None of this is your fault.", 'mom'),
    ("Mama sees you. Say goodnight.", 'mom'),             # sung, the real words, voice cracking
    ("I could be your dad.", 'blank'),
    ("I don't know.", 'son'),
    ("Look at me. How are you, really?", 'N'),            # the narrator, in the scene
    ("Brown. Your eyes are brown.", 'son'),
    ("your family doesn't care", 'N'),
    ("How are you, really?\" Kids", 'N'),
]

SPEECH = [(r'FRI\. O\'S BIRTHDAY\.', "Friday. O's birthday."),
          (r'Under FRI, I wrote: MOM IT\'S OWEN I\'M HERE\.', "Under Friday, I wrote: Mom, it's Owen. I'm here."),
          (r'THE CHAT\. THE PHOTO\. THE COAT\. THE CAR\. 2 A\.M\. I WISHED FOR A DIFFERENT MOM\.',
           'The chat. The photo. The coat. The car. Two a.m. I wished for a different mom.')]


def clean_narr(p):
    for a, b in SPEECH:
        p = re.sub(a, b, p)
    p = re.sub(r'(^|\s)(Tik\.|Ping\.)(?=\s|$)', ' ', p)          # sounds, not words
    p = re.sub(r'\s+', ' ', p).strip()
    return p


def main():
    text = open(SRC).read().strip()
    paras = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    files = {k: [] for k in ('narrator', 'mom', 'blank', 'owen', 'son', 'dunn', 'mensah')}
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
            wi = k + 1
            who = WHO[k][1]
            if who == 'N':
                continue
            said.append((who, body))
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
    os.makedirs(OUT, exist_ok=True)
    # narrator parts, cut at paragraph ends, preferring a cut just before "Rule number"
    parts, cur = [], []
    for p in files['narrator']:
        n = len('\n\n'.join(cur + [p]))
        if cur and n > PART_MAX:
            # step back to the last "Rule number" start in this part if it leaves a part of reasonable size
            cut = len(cur)
            for i in range(len(cur) - 1, 0, -1):
                if cur[i].startswith('Rule number') and len('\n\n'.join(cur[:i])) > PART_MAX * 0.55:
                    cut = i
                    break
            parts.append(cur[:cut])
            cur = cur[cut:]
        cur.append(p)
    parts.append(cur)
    idx = {'narrator_parts': []}
    for i, ps in enumerate(parts, 1):
        name = 'narrator_part%d.txt' % i
        open(os.path.join(OUT, name), 'w').write('\n\n'.join(ps) + '\n')
        idx['narrator_parts'].append({'file': name, 'chars': len('\n\n'.join(ps)), 'paragraphs': len(ps)})
    for who in ('mom', 'blank', 'dunn', 'mensah'):
        open(os.path.join(OUT, who + '.txt'), 'w').write('\n\n'.join(files[who]) + '\n')
        idx[who] = len(files[who])
    kids = files['owen'] + files['son']
    open(os.path.join(OUT, 'kids_adult_take.txt'), 'w').write('\n\n'.join(kids) + '\n')
    idx['kids_adult_take'] = {'owen': len(files['owen']), 'son': len(files['son']),
                              'note': 'Owen lines first, then the son; one adult take with the narrator voice'}
    idx['order'] = order
    json.dump(idx, open(os.path.join(OUT, 'index.json'), 'w'), indent=1, ensure_ascii=False)
    for k in idx['narrator_parts']:
        print(k)
    print({k: idx[k] for k in ('mom', 'blank', 'dunn', 'mensah', 'kids_adult_take')})
    # words check: every word of the script is in exactly one file (minus sounds and spoken-out capitals)
    allw = ' '.join(x for _, x in order)
    print('words in files', len(allw.split()), 'script words', len(text.split()))


main()
