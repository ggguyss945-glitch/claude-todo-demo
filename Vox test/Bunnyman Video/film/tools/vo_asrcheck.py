"""Every line of the edited narration against what the recogniser hears in it (fix round 1, from critic 3's asrcheck).
    python3 tools/vo_asrcheck.py [--quiet]          exit 1 on any mismatch that is not in ALLOW
Reads W/narration/edit_list.json (each line's output span) and W/align/asr_cache.json (Parakeet on narration_en.wav,
written by align.py: run align.py after every vo_edit.py build, then this). A recognised word belongs to the line whose
sound holds its start (out span - 40 ms .. + 20 ms); a word that starts in a gap goes to the next line when that line
starts within 0.35 s (Parakeet puts the first word after a silence up to ~0.3 s early: "It has a zipper"), else to the
line before. A line fails when its first or last word is wrong, when it reads under 80 % of its script, when it is not
heard at all, or when a word is split across a line boundary ("wood" | "pile", "door at" | "At six"): exactly the
fragments a mis-placed cut leaves.
"""
import difflib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(os.path.dirname(HERE), '_work')
sys.path.insert(0, HERE)
from vo_edit import toks                                           # noqa: E402  (the edit's own word normaliser)

# what the recogniser cannot help hearing its own way (homophones and spellings: not edit faults)
SAME = {'lori': 'laurie', 'gray': 'grey', 'mamma': 'mama', 'stockboy': 'stock', 'pembertons': 'pemberton',
        'mr': 'mister', 'aged': 'age', 'oh': '0'}
# lines that may fail, with the reason (checked by ear on the spectrogram, not an edit fault)
ALLOW = {
}


def norm(s):
    out = []
    for t in toks(s):
        t = SAME.get(t, t)
        if t == '0': continue
        if out and re.fullmatch(r'[2-9]0', out[-1]) and re.fullmatch(r'[1-9]', t):    # "forty seven" = 47
            out[-1] = out[-1][0] + t; continue
        out.append(t)
    return out


def main(quiet=False):
    el = json.load(open(os.path.join(W, 'narration', 'edit_list.json')))['lines']
    words = json.load(open(os.path.join(W, 'align', 'asr_cache.json')))['en_words']
    heard = {e['i']: [] for e in el}
    for w, t in words:
        k = next((k for k, e in enumerate(el) if e['out'][0] - 0.04 <= t <= e['out'][1] + 0.02), None)
        if k is None:
            nxt = next((k for k, e in enumerate(el) if e['out'][0] > t), None)
            if nxt is None: k = len(el) - 1
            elif nxt > 0 and el[nxt]['out'][0] - t > 0.35: k = nxt - 1
            else: k = nxt
        heard[el[k]['i']].append(w)
    sim = lambda x, y: x == y or difflib.SequenceMatcher(None, x, y).ratio() >= 0.67
    bad = []
    H = {i: norm(' '.join(v)) for i, v in heard.items()}
    for n, e in enumerate(el):
        i = e['i']; hs = H[i]; sc = norm(e['en'])
        why = []
        if not hs: why.append('nothing heard')
        else:
            if not sim(hs[0], sc[0]): why.append('first word')
            if not sim(hs[-1], sc[-1]): why.append('last word')
            r = difflib.SequenceMatcher(None, hs, sc).ratio()
            if r < 0.8 and len(sc) >= 3: why.append('reads %.2f' % r)
        if n + 1 < len(el) and hs and H[el[n + 1]['i']]:
            a, b = hs[-1], H[el[n + 1]['i']][0]
            joined = a + b
            if joined in sc or joined in norm(el[n + 1]['en']) or (a == b and len(a) > 1 and a in norm(el[n + 1]['en'])[:1]):
                why.append('word split across the boundary: "%s" | "%s"' % (a, b))
        if why:
            bad.append((i, ', '.join(why), e['en'], ' '.join(heard[i])))
    fails = [b for b in bad if b[0] not in ALLOW]
    for i, why, s, h in bad:
        tag = 'ALLOWED (%s)' % ALLOW[i] if i in ALLOW else 'FAIL'
        print('L%-3d %-7s %-28s script: %-50s | heard: %s' % (i, tag, why, s[:50], h[:70]))
    print('asrcheck: %d lines, %d mismatches, %d allowed, %d failures' % (len(el), len(bad), len(bad) - len(fails), len(fails)))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main('--quiet' in sys.argv))
