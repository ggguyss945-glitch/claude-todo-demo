"""The voice edit of "If a Girl Is OBSESSED With Being Your Only Friend... DON'T WRITE YOUR NAME" (Night Policy;
adapted from the Buttons film's tool): the owner's 13 ElevenLabs takes -> one clean, paced voice track (English).
    python3 tools/vo_edit.py analyze     line -> take mapping, recogniser vs script per line, dropped islands (prints)
    python3 tools/vo_edit.py build       -> W/narration/narration_en.wav (48 kHz mono, 24-bit) + edit_list.json
    python3 tools/vo_edit.py check       scans of the built file (gaps vs plan, residual breaths, clicks at cuts,
                                         levels per voice, peaks); then run tools/align.py and tools/vo_asrcheck.py --every
Sources: W/narration/raw/index.json (7 narrator parts in order, one take per character; Adam's 9 lines (the song at
seven first) and Danny's 5 share one narrator-voice take ('kids'); 'danny2' is a second Danny take: DANNY_SRC picks
the better reading per line, and the unused reading stays in the cut plan as a ghost so no cut lands inside it), words from tools/vo_asr.py (W/narration/asr/<take>.json: Parakeet TDT word start/end times, used as anchors),
lines from film/script/lines.py (tools/vo_lines.py: who, fx, pause per line, in script order).
How it works
  1. Map: per source (the narrator's six parts as one word stream; each character take), the lines' words are matched
     to the recogniser's (difflib on normalised words); every recognised word belongs to one line.
  2. Cut: between two lines of one take the cut sits in the silence between them (the longest stretch under -60 dBFS
     near the expected boundary; the takes have digital silence between phrases), or, if they run together, in the
     deepest 10 ms dip (8 ms fades). Inside a line every sound island (> -60 dBFS, 5 ms RMS, gaps < 15 ms merged) is
     kept when it is speech: voiced, or a consonant touching voiced speech (a coda burst or fricative within 150 ms
     after it, an s/sh/f onset within 100 ms before it, a consonant between two voiced islands). Breaths (unvoiced,
     apart from the speech), clicks and lip noises are dropped, at line edges and inside lines.
  3. Pace: the silence after each line is its lines.py pause (the end of one line's last sound to the next line's
     first sound). Pauses inside a line keep the take's timing, clamped by their punctuation (comma 0.10-0.30 s,
     colon 0.20-0.35, ellipsis 0.22-0.45, mid-line full stop 0.15-0.30, none <= 0.25; character lines may hold x1.5).
     Pauses inside words (< 120 ms) are never touched. Nothing is stretched. A narrator gap that is not 'fixed' in
     lines.py (a hold, a Tik / Ping beat, a rule card) is a ceiling: the take's own pause is kept when shorter (>= 0.14 s).
     The beats' times go to W/align/beats.json.
  4. Level: one gain per line, never inside a phrase: a narrator line moves 60 % of its distance to the narrator's
     median speech level (+-6 dB, nothing inside 1.5 dB: his whispers stay whispers, only softer than the rest by
     less); a character line goes the whole way to the narrator's median (+ VOICE_LU), so every voice sits at the
     narrator's level. The narrator's voice is otherwise untouched.
  5. Voices and places: Adam, little Adam and Danny (from the narrator-voice takes), Evie and Lina (from Evie's takes) are
     re-voiced (tools/vo_voices.py); the staged lines get their place (tools/vo_fx.py: message, letterbox, thin, tape),
     each loudness-matched to the dry line + its offset; an fx decay runs into the gap after its line (ending 0.1 s
     before the next). The lines with an fx and their times go to W/align/voice_fx.json (the picture shows the tape).
  6. Finish: (each take is 70 Hz high-passed on loading, before any level is measured), the gaps gated to digital
     silence, one gain puts the true peak at -1 dBTP.
"""
import json, os, re, sys, difflib
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
W = os.path.join(FILM, '_work')
N = os.path.join(W, 'narration')
RAWDIR = os.path.join(N, 'raw')
ASRDIR = os.path.join(N, 'asr')
OUT = os.path.join(N, 'narration_en.wav')
EDL = os.path.join(N, 'edit_list.json')
sys.path.insert(0, os.path.join(FILM, 'script'))
sys.path.insert(0, HERE)
SR = 48000
NARR = ['narrator_part%d' % k for k in range(1, 8)]
TAKE = {'evie': 'evie', 'lina': 'lina', 'mom': 'mom', 'rahman': 'rahman', 'adam': 'kids', 'adam7': 'kids',
        'danny': 'danny2'}
# Danny's better reading per line (default danny2, the second take: slower, softer, each full stop a real stop, which
# suits "soft, slightly hesitant"; the kids take has the real question on "Can we sit here? All of us?")
DANNY_SRC = {'danny_can_we_sit': 'kids'}
VOICE_LU = {'evie': 0.0, 'lina': -0.5, 'mom': 0.0, 'rahman': 0.0, 'adam': 0.0, 'adam7': 0.0, 'danny': -0.5}   # dB vs the narrator's median speech level (before any fx offset)
THR = -60.0                                        # island threshold (dBFS, 5 ms RMS)
LEAD, TAIL = 0.30, 0.60
NAT_MIN = 0.12                                     # shortest gap between two narrator sentences (s)
CLAMP = {',': (0.07, 0.17), ';': (0.14, 0.24), ':': (0.14, 0.24), '...': (0.16, 0.30), '.': (0.10, 0.19),
         '?': (0.10, 0.19), '!': (0.10, 0.19), '': (0.0, 0.18)}
LINE_LU = {}                                       # dB on top of the voice level, per tag
HOLD = {'adam7': 1.0, 'lina': 1.0}                 # x the clamp's upper bound for character lines (default 1.3); the
                                                   # songs keep their own phrasing (their rests are short anyway)
# hand fixes (raw take seconds), checked by measurement: CUTS {tag: start cut}; ENDS {tag: end of the line} (Evie's
# last sung line is cut off inside the second "here": the take sings it whole, the script stops on "he-")
# CUTS: a float is one cut (end of the line before = start of this one, forced: 8 ms fades); a pair (end of the line
# before, start of this one) is two cuts in silence. "I scrubbed it off": part 6 sings a stray, drawn-out "I." (34.62-
# 35.28 s, a glitch of the take) between "Only." and "I scrubbed"; both cuts sit in its -86 dB silences
CUTS = {'i_scrubbed_it': (34.40, 35.31)}
# (tried: "I didn't open." ends in the -72 dB dip before the take's "it" at 34.425 s, but alone it then read "I didn't
# know": the take's "open it" is one gesture, so the line keeps its faint "it", which both passes read as "I didn't open.")
ENDS = {}
# a line built from hand-picked pieces of its take: [(a or None = the line's start cut, b, gain dB, fade out ms)]. Evie's
# take sings "I'm here. I'm h" (the take stops on a breathy h, no vowel), so "he-" is the h + the first 105 ms of the
# "ee" of her first "here" (47.925-48.175 s; F3 starts falling into the r at 48.19 s), after her own second "I'm" (lifted
# 4 dB: the take sang it 10 dB under the first; the split at 48.95 s sits in -88 dB silence); the cut is a 10 ms fade
SPLICE = {'evie_only_me_im': [(None, 48.95, 0.0, 3), (48.95, 49.215, 4.0, 6), (47.925, 48.175, 0.0, 10)]}
# words the first transcript missed (take key -> [(word, t0, t1)]), placed by the take's energy: the narrator's "Adam."
# after Lina's line is a lone word between two silences (-86 dB), 84.25-84.80 s of part 4
ASR_ADD = {'narrator_part4': [('Adam', 84.25, 84.80)]}

NUM = {'zero': '0', 'one': '1', 'two': '2', 'to': '2', 'too': '2', 'three': '3', 'four': '4', 'five': '5', 'six': '6',
       'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10', 'twelve': '12', 'fourteen': '14', 'fifty': '50',
       'sixty': '60', 'thirty': '30', 'forty': '40', 'hundred': '100', 'first': '1st', 'fifth': '5th'}
SAME = {'larksburg': 'larkspur', 'larkspurs': 'larkspur', 'markspur': 'larkspur', 'pel': 'pell', 'pells': 'pell',
        'grey': 'gray', 'shh': 'shhh', 'sh': 'shhh', 'mr': 'mister', 'mrs': 'missus', 'hushabai': 'hushabye',
        'hushaby': 'hushabye', 'hushabi': 'hushabye', 'okay': 'ok', 'goodnight': 'good night', 'dabrowskis': 'dabrowski',
        'misses': 'missus', 'dubrowski': 'dabrowski', 'grill': 'grille', 'larksbury': 'larkspur', 'larksburgh': 'larkspur',
        'larksford': 'larkspur', 'hashabai': 'hushabye', 'hashaby': 'hushabye', 'hushabuy': 'hushabye',
        'mamma': 'mama', 'mammas': 'mamas', 'favorite': 'favourite', 'color': 'colour', 'flashlight': 'torch'}
PAIRS = {('larks', 'per'): 'larkspur', ('larks', 'for'): 'larkspur', ('arm', 'chair'): 'armchair', ('door', 'frame'): 'doorframe', ('2', 'night'): 'tonight', ('dead', 'bolt'): 'deadbolt',
         ('grown', 'up'): 'grownup', ('grown', 'ups'): 'grownups', ('flash', 'light'): 'flashlight', ('head', 'board'): 'headboard'}
HUSH = [('hush', 'a', 'bye'), ('hush', 'a', 'by'), ('hush', 'a', 'bi'), ('hush', 'a', 'bai'), ('hush', 'abye'),
        ('hush', 'aby'), ('hush', 'a', 'buy'), ('husha', 'bai'), ('husha', 'bye'), ('husha', 'by')]


def log(*a):
    print('[vo]', *a, flush=True)


# ============================================================================ words
def _raw_toks(s):
    out = []
    for w in re.findall(r"[a-z0-9]+", s.lower().replace("'", '').replace('’', '').replace('-', ' ')):
        w = SAME.get(w, w); w = NUM.get(w, w)
        if w.isdigit() and len(w) >= 3 and w not in ('100',): out += list(w)
        else: out += w.split()
    return out


def _join(ts, key=lambda t: t):
    out, k = [], 0
    while k < len(ts):
        for h in HUSH:
            if tuple(key(t) for t in ts[k:k + len(h)]) == h:
                out.append(('hushabye', ts[k], ts[k + len(h) - 1])); k += len(h); break
        else:
            pr = tuple(key(t) for t in ts[k:k + 2])
            if pr in PAIRS:
                out.append((PAIRS[pr], ts[k], ts[k + 1])); k += 2; continue
            out.append((key(ts[k]), ts[k], ts[k])); k += 1
    return out


def toks(s):
    """Normalised word tokens (vo_asrcheck.py uses the same)."""
    return [t for t, _, _ in _join(_raw_toks(s))]


def text_punct(s):
    """Per token of toks(s): the punctuation after it in the text ('' inside a word group)."""
    out = []
    for w in s.split():
        n = len(toks(w))
        if not n: continue
        m = re.search(r'([.,;:?!]+)["\')]*$', w)
        p = m.group(1) if m else ''
        p = '...' if p.startswith('...') else (p[-1] if p else '')
        out += [''] * (n - 1) + [p]
    return out


def rawfile(key):
    """Take key -> file name in W/narration/raw (index.json 'files': {file: label})."""
    ix = json.load(open(os.path.join(RAWDIR, 'index.json')))['files']
    for f, lab in ix.items():
        k = lab.split()[0]
        k = {'kids_adult_take': 'kids'}.get(k, k)
        if lab.startswith('danny (second'): k = 'danny2'
        if k == key: return f
    raise KeyError(key)


def asr_tokens(key, part=0):
    d = json.load(open(os.path.join(ASRDIR, os.path.splitext(rawfile(key))[0] + '.json')))
    flat = []
    for w, t0, t1 in sorted(d['words'] + [list(a) for a in ASR_ADD.get(key, [])], key=lambda r: float(r[1])):
        for t in _raw_toks(w): flat.append((t, float(t0), float(t1)))
    return [dict(tok=t, src=key, t0=a[1], t1=b[2]) for t, a, b in _join(flat, key=lambda x: x[0])]


def load_lines():
    from lines import LINES
    return [dict(l, i=i) for i, l in enumerate(LINES)]


def take_of(l):
    if l.get('take'): return l['take']
    if l['who'] == 'danny': return DANNY_SRC.get(l['tag'], TAKE['danny'])
    return 'narrator' if l['who'] == 'narrator' else TAKE[l['who']]


def map_lines(L):
    """Every line -> its recognised words in its take: l['asr'] = [token dicts with 'li' (line token index)];
    l['diff'] = the mismatches (op, script words, heard words)."""
    groups = {}
    ghosts = []                                        # Danny's unused reading: mapped and cut around, never output
    for l in L:
        if l['who'] == 'danny':
            g = dict(l, ghost=True); g['take'] = 'kids' if take_of(l) == 'danny2' else 'danny2'; ghosts.append(g)
    for l in L + ghosts: groups.setdefault(take_of(l), []).append(l)
    for g, ls in groups.items():
        if g == 'narrator': A = [t for k in NARR for t in asr_tokens(k)]
        else:
            A = asr_tokens(g)
            if g == 'kids': ls = sorted(ls, key=lambda l: (l['who'] == 'danny', l['i']))
            else: ls = sorted(ls, key=lambda l: l['i'])
        S = [(l['i'], k, t) for l in ls for k, t in enumerate(toks(l['say']))]
        by = {l['i']: l for l in ls}
        for l in ls: l['asr'], l['diff'] = [], []
        sm = difflib.SequenceMatcher(None, [s[2] for s in S], [a['tok'] for a in A], autojunk=False)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == 'equal':
                for d in range(i2 - i1): by[S[i1 + d][0]]['asr'].append(dict(A[j1 + d], li=S[i1 + d][1]))
                continue
            if op == 'replace':                            # (an 'insert' is a word the script does not have: the
                for j in range(j1, j2):                    # recogniser's double of a word at a chunk edge, "I looked I
                    si = i1 + (j - j1) * (i2 - i1) // (j2 - j1)   # kept": it anchors no line and moves no cut)
                    by[S[si][0]]['asr'].append(dict(A[j], li=S[si][1]))
            owner = S[i1][0] if i1 < len(S) else S[-1][0]
            by[owner]['diff'].append((op, [s[2] for s in S[i1:i2]], [a['tok'] for a in A[j1:j2]]))
        for l in ls:
            l['asr'].sort(key=lambda a: (NARR.index(a['src']) if a['src'] in NARR else 0, a['t0']))
            l['head_unmatched'] = any(op == 'delete' and sw and sw[0] == toks(l['say'])[0] for op, sw, _ in l['diff'][:1])
    return L + ghosts


# ============================================================================ audio analysis
_TAKES = {}


def take(key):
    if key not in _TAKES:
        x, sr = sf.read(os.path.join(RAWDIR, rawfile(key)), dtype='float64')
        assert sr == SR, (key, sr)
        x = highpass(x)                                # 70 Hz first: levels are measured on what is heard (a whisper
        e = envelope(x)                                # line's sub-bass rumble read 5 dB of "speech")
        import parselmouth
        p = parselmouth.Sound(x, sampling_frequency=SR).to_pitch_ac(time_step=0.005, pitch_floor=65, pitch_ceiling=600,
                                                                     voicing_threshold=0.45)
        v = np.zeros(len(e), bool)
        for t, f in zip(p.xs(), p.selected_array['frequency']):
            if f > 0: k = int(t * 1000); v[max(0, k - 3):k + 3] = True
        _TAKES[key] = dict(x=x, e=e, v=v, isl=islands(e))
    return _TAKES[key]


def envelope(x, sr=SR, win=0.005, hop=0.001):
    w, h = int(win * sr), int(hop * sr)
    cs = np.concatenate([[0.0], np.cumsum(x * x)])
    idx = np.arange(0, len(x) - w, h)
    return 10 * np.log10((cs[idx + w] - cs[idx]) / w + 1e-20)


def islands(db, thr=THR, merge=15):
    act = db > thr
    d = np.diff(np.concatenate([[0], act.astype(np.int8), [0]]))
    out = []
    for a, b in zip(np.where(d == 1)[0], np.where(d == -1)[0]):
        if out and a - out[-1][1] < merge: out[-1][1] = b
        else: out.append([int(a), int(b)])
    return [(a / 1000.0, (b - 1) / 1000.0 + 0.005) for a, b in out]


def runs_below(e, a, b, thr=THR, min_len=0.03):
    """Silent runs [(s0, s1)] inside [a, b] (seconds)."""
    i0, i1 = max(0, int(a * 1000)), min(len(e), int(b * 1000))
    if i1 <= i0: return []
    q = e[i0:i1] < thr
    d = np.diff(np.concatenate([[0], q.astype(np.int8), [0]]))
    out = []
    for s, t in zip(np.where(d == 1)[0], np.where(d == -1)[0]):
        if (t - s) / 1000.0 >= min_len: out.append(((i0 + s) / 1000.0 + 0.005, (i0 + t) / 1000.0))
    return out


def centroid(x):
    if len(x) < 64: return 0.0
    s = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = (f > 100) & (f < 12000)
    return float((s[m] * f[m]).sum() / (s[m].sum() + 1e-20))


# ============================================================================ cuts
def line_spans(L):
    """l['span'] = (take, a, b, forced_head, forced_tail): the line's stretch of its take, cut in silence."""
    byt = {}
    for l in L:
        if not l['asr']: raise SystemExit('line %d has no recognised words: %s' % (l['i'], l['en']))
        src = l['asr'][0]['src']
        if any(a['src'] != src for a in l['asr']):        # a line across two narrator parts: keep its main part
            from collections import Counter
            src = Counter(a['src'] for a in l['asr']).most_common(1)[0][0]
            l['asr'] = [a for a in l['asr'] if a['src'] == src]
        byt.setdefault(src, []).append(l)
    for src, ls in byt.items():
        T = take(src); e = T['e']; dur = len(T['x']) / SR
        ls.sort(key=lambda l: l['asr'][0]['t0'])
        cut = [None] * (len(ls) + 1)                   # cut[k] = (end of line k-1, start of line k, forced)
        first = ls[0]['asr'][0]
        rs = runs_below(e, 0, first['t1'])
        cut[0] = (None, rs[0][1] if rs and rs[0][0] < 0.02 else 0.0, False)
        for k in range(1, len(ls)):
            A, B = ls[k - 1]['asr'][-1], ls[k]['asr'][0]
            if ls[k]['tag'] in CUTS:
                c = CUTS[ls[k]['tag']]
                cut[k] = (c, c, True) if isinstance(c, float) else (c[0], c[1], False); continue
            exp = 0.5 * (A['t1'] + B['t0'])
            rs = runs_below(e, A['t0'] + 0.03, max(B['t1'], A['t0'] + 0.1))
            if rs:
                best = max(rs, key=lambda r: (r[1] - r[0]) - 0.5 * abs(0.5 * (r[0] + r[1]) - exp))
                if best[1] - best[0] >= 0.06 or len(rs) == 1:
                    cut[k] = (best[0], best[1], False); continue
            lo, hi = int((A['t1'] - 0.08) * 1000), int((B['t0'] + 0.08) * 1000)
            lo = max(lo, int((A['t0'] + 0.05) * 1000)); hi = max(hi, lo + 10)
            sm = np.convolve(10 ** (e[lo:hi] / 10), np.ones(10) / 10, mode='same')
            c = (lo + int(np.argmin(sm))) / 1000.0
            cut[k] = (c, c, True)
        last = ls[-1]['asr'][-1]
        rs = runs_below(e, last['t0'] + 0.03, dur, min_len=0.25)
        cut[-1] = (rs[0][0] if rs else dur, None, False)
        for k, l in enumerate(ls):
            l['span'] = (src, cut[k][1], cut[k + 1][0], cut[k][2], cut[k + 1][2])
            if l['tag'] in ENDS: l['span'] = (src, cut[k][1], ENDS[l['tag']], cut[k][2], True)
    return L


def line_islands(l):
    """The kept and dropped islands of a line: ([(a, b)], [(a, b, why)])."""
    src, a, b, fh, ft = l['span']
    T = take(src)
    isl = [(max(s, a), min(t, b)) for s, t in T['isl'] if t > a and s < b]
    isl = [(s, t) for s, t in isl if t - s > 0.002]
    feats = []
    for s, t in isl:
        i0, i1 = int(s * 1000), int(t * 1000) + 1
        vf = float(T['v'][i0:i1].mean()) if i1 > i0 else 0.0
        pk = float(T['e'][i0:i1].max()) if i1 > i0 else -99
        feats.append(dict(s=s, t=t, vf=vf, vms=float(T['v'][i0:i1].sum()), pk=pk,
                          c=centroid(T['x'][int(s * SR):int(t * SR)])))
    ref = max([f['pk'] for f in feats] or [-30])
    voiced = [f for f in feats if (f['vf'] >= 0.2 or f['vms'] >= 25) and f['pk'] > ref - 32]
    keep, drop = [], []
    words = [(w['t0'], w['t1']) for w in l['asr']]
    v0 = min([v['s'] for v in voiced] or [9e9]); v1 = max([v['t'] for v in voiced] or [-9e9])
    ov = lambda f, a_, b_: max(0.0, min(f['t'], b_) - max(f['s'], a_))
    for f in feats:
        if f in voiced: keep.append((f['s'], f['t'])); continue
        gp = min([f['s'] - v['t'] for v in voiced if v['t'] <= f['s'] + 0.001] or [9])
        gn = min([v['s'] - f['t'] for v in voiced if v['s'] >= f['t'] - 0.001] or [9])
        dur = f['t'] - f['s']
        inword = sum(ov(f, w0, w1 + 0.05) for w0, w1 in words) >= min(0.04, 0.5 * dur)
        quiet = f['pk'] < ref - 20 and dur >= 0.12 and f['c'] < 3000
        if (fh and f['s'] <= a + 0.001) or (ft and f['t'] >= b - 0.001): why = None      # a forced cut's edge: speech
        elif not voiced: why = None if inword else 'breath'                              # a whispered line
        elif f['t'] <= v0 + 0.001:                                                       # before the first voiced sound
            ok = gn <= 0.10 and (f['c'] >= 3000 or f['pk'] > ref - 15)                   # an s / sh / f onset, a loud
            ok = ok or (l.get('head_unmatched') and dur >= 0.08) or (inword and f['pk'] > ref - 18)   # whispered
            # word; an unheard
            why = None if ok else ('breath' if dur >= 0.08 else 'click')                 # first word ("Shhh.")
        elif f['s'] >= v1 - 0.001:                                                       # after the last voiced sound
            wl = words[:-1] + [(words[-1][0], min(words[-1][1], words[-1][0] + 0.5))] if words else []
            inw = sum(ov(f, w0, w1 + 0.05) for w0, w1 in wl) >= min(0.04, 0.5 * dur)
            q2 = f['pk'] < ref - 18 and f['c'] < 3500 and dur >= 0.08
            ok = (gp <= 0.15 or inw or not q2) and not quiet                             # a coda, a devoiced end,
            # a whispered word (loud, bright); a breath after the line is soft and dull
            why = None if ok else ('breath' if dur >= 0.08 else 'click')
        else:                                                                            # between voiced sounds
            q2 = f['pk'] < ref - 18 and f['c'] < 3500 and dur >= 0.08                  # breath-like: soft, dull
            ok = (not q2) or ((inword or (gp <= 0.15 and gn <= 0.15)) and not quiet)   # (a whispered word is not)
            why = None if ok else ('breath' if dur >= 0.08 else 'click')
        if why: drop.append((f['s'], f['t'], why, round(f['c']), round(f['pk'], 1)))
        else: keep.append((f['s'], f['t']))
    return sorted(keep), drop


def pause_clamp(l, gap_start):
    """(lo, hi) for a pause inside line l that starts at gap_start (take seconds)."""
    pun = text_punct(l['say'])
    before = [w for w in l['asr'] if w['t0'] < gap_start - 0.02]
    p = pun[before[-1]['li']] if before and before[-1]['li'] < len(pun) else ''
    lo, hi = CLAMP.get(p, CLAMP[''])
    if l['who'] != 'narrator': hi *= HOLD.get(l['who'], 1.3)
    return lo, hi, p


def line_audio(l):
    """The cleaned line (dry, take level) and its piece list."""
    src, a, b, fh, ft = l['span']
    x = take(src)['x']
    if l['tag'] in SPLICE:                             # hand-built from its pieces (see SPLICE)
        out, pieces = [], []
        for k, (p0, p1, g, fo) in enumerate(SPLICE[l['tag']]):
            p0 = a if p0 is None else p0
            y = x[int(round(p0 * SR)):int(round(p1 * SR))] * 10 ** (g / 20)
            fi, fo = int(0.003 * SR), int(fo / 1000.0 * SR)
            y[:fi] *= np.sin(np.linspace(0, np.pi / 2, fi)) ** 2
            y[-fo:] *= np.cos(np.linspace(0, np.pi / 2, fo)) ** 2
            out.append(y); pieces.append(dict(src=src, a=round(p0, 3), b=round(p1, 3), gain_db=g))
        l['dropped'] = []
        return np.concatenate(out), pieces
    keep, drop = line_islands(l)
    l['dropped'] = drop
    groups = []
    for s, t in keep:
        if groups and s - groups[-1][1] < 0.12: groups[-1][1] = t
        else: groups.append([s, t])
    out, pieces = [], []
    for k, (s, t) in enumerate(groups):
        if k:
            g = s - groups[k - 1][1]
            lo, hi, p = pause_clamp(l, groups[k - 1][1])
            g2 = min(max(g, lo), hi)
            out.append(np.zeros(int(round(g2 * SR))))
            pieces.append(dict(pause=round(g, 3), kept=round(g2, 3), punct=p))
        y = x[int(round(s * SR)):int(round(t * SR))].copy()
        fi = int((0.008 if (fh and k == 0) else 0.002) * SR)
        fo = int((0.008 if (ft and k == len(groups) - 1) else 0.003) * SR)
        if len(y) > fi + fo:
            y[:fi] *= np.sin(np.linspace(0, np.pi / 2, fi)) ** 2
            y[-fo:] *= np.cos(np.linspace(0, np.pi / 2, fo)) ** 2
        out.append(y); pieces.append(dict(src=src, a=round(s, 3), b=round(t, 3)))
    return np.concatenate(out), pieces


def speech_level(y):
    w = int(0.02 * SR); n = len(y) // w
    if n < 1: return -99.0
    p = 10 * np.log10((y[:n * w].reshape(n, w) ** 2).mean(1) + 1e-20)
    return float(np.median(p[p > p.max() - 20]))


def highpass(y, fc=70.0):
    from scipy import signal
    return signal.sosfiltfilt(signal.butter(2, fc, 'highpass', fs=SR, output='sos'), y)


def true_peak(y):
    import soxr
    return float(np.abs(soxr.resample(y, SR, SR * 4)).max())


# ============================================================================ commands
def prepared():
    L = map_lines(load_lines())
    return [l for l in line_spans(L) if not l.get('ghost')]


def cmd_analyze():
    L = prepared()
    for l in L:
        flag = [d for d in l['diff']]
        audio, pcs = line_audio(l)
        big = [d for d in l['dropped'] if d[1] - d[0] > 0.25 or d[4] > -35]
        if flag or big or l['span'][3] or l['span'][4]:
            print('L%-3d %-9s %s | diff %s | forced %s%s | big drops %s' % (
                l['i'], l['who'], l['en'][:50], flag, 'H' if l['span'][3] else '', 'T' if l['span'][4] else '', big))
    nd = sum(len(l['dropped']) for l in L)
    log('%d lines; %d islands dropped (%d breath, %d click)' % (len(L), nd, sum(1 for l in L for d in l['dropped'] if d[2] == 'breath'),
                                                               sum(1 for l in L for d in l['dropped'] if d[2] == 'click')))


def cmd_build():
    import vo_voices, vo_fx
    L = prepared()
    dry = []
    for l in L:
        y, pcs = line_audio(l); l['pieces'] = pcs; l['lvl'] = speech_level(y); dry.append(y)
    nar_med = float(np.median([l['lvl'] for l in L if l['who'] == 'narrator']))
    for a, b in zip(L, L[1:]):                     # an ordinary narrator gap (not 'fixed' for its moment) keeps the
        if a['who'] == b['who'] == 'narrator' and not a.get('fixed') and a['span'][0] == b['span'][0]:   # take's own
            nat = b['pieces'][0]['a'] - a['pieces'][-1]['b']                                              # pause when
            if nat > 0: a['pause'] = round(min(float(a['pause']), max(nat, NAT_MIN)), 3)                 # shorter
    take_med = {}
    for l in L:
        if l['who'] != 'narrator': take_med.setdefault(l['who'], []).append(l['lvl'])
    take_med = {k: float(np.median(v)) for k, v in take_med.items()}
    parts, t, el, beats = [np.zeros(int(LEAD * SR))], LEAD, [], []
    for l, y in zip(L, dry):
        if l.get('drop'):                              # owner: no dialogue tags; keep the longer of the two pauses
            if el:
                want = float(l['pause'])
                nxt = next((m for m in L[L.index(l) + 1:] if not m.get('drop')), None)
                if nxt is not None and nxt['who'] == el[-1]['who'] != 'narrator':   # one speaker's two quotes now meet:
                    want = max(want, 0.40)        # a natural phrase pause between them
                extra = max(0.0, want - el[-1]['pause'])
                if extra > 0:
                    parts.append(np.zeros(int(round(extra * SR)))); t += extra
                    el[-1]['pause'] = round(el[-1]['pause'] + extra, 3)
            continue
        ref = nar_med if l['who'] == 'narrator' else take_med[l['who']]
        if l['who'] == 'narrator':                     # 60 % of the way to the median, +-6 dB, nothing inside 1.5 dB
            d = nar_med - l['lvl']
            g = 0.0 if abs(d) < 1.5 else float(np.clip(0.6 * d, -6, 6))
        else:                                          # a character line: the whole way (one level per voice)
            g = nar_med - l['lvl'] + VOICE_LU.get(l['who'], 0.0)
        g += LINE_LU.get(l['tag'], 0.0)
        y = y * 10 ** (g / 20)
        vst = None
        if l['who'] in vo_voices.VOICES:          # the re-voiced characters (tools/vo_voices.py)
            y, vst = vo_voices.voice_line(y, l)
        if l.get('fx'):
            y = vo_fx.apply(y, l['fx'])
        gap = float(l['pause']) if l['i'] < len(L) - 1 else TAIL
        tail = vo_fx.TAIL.get(l.get('fx'), 0.0) if l.get('fx') else 0.0   # an fx's decay runs into the gap (never past
        n0 = len(y) - int(tail * SR)                  # it: cut there with a 60 ms fade)
        z = np.zeros(int(round(gap * SR)))
        if n0 < len(y):
            tl = y[n0:n0 + max(0, len(z) - int(0.10 * SR))].copy(); f = min(len(tl), int(0.06 * SR))   # 0.1 s clear
            if f: tl[-f:] *= np.linspace(1, 0, f)
            z[:len(tl)] += tl
        parts.append(y[:n0]); parts.append(z)
        el.append(dict(i=l['i'], tag=l['tag'], who=l['who'], fx=l.get('fx'), en=l['en'], say=l['say'], out=[round(t, 3), round(t + n0 / SR, 3)],
                       pause=round(gap, 3), gain_db=round(g, 2), level_dry=round(l['lvl'], 1), src=l['span'][0],
                       src_span=[round(l['span'][1], 3), round(l['span'][2], 3)], forced=[l['span'][3], l['span'][4]],
                       pieces=l['pieces'], dropped=l['dropped'], voice=vst, fx_tail=tail))
        for k, b in enumerate(l.get('beats') or []):   # the Ping / Clank sounds of the script, placed in this gap
            beats.append(dict(kind=b, t=round(t + n0 / SR + l['beat_t'][k], 3), line=l['i'], tag=l['tag']))
        t += n0 / SR + gap
    y = np.concatenate(parts)
    mask = np.zeros(len(y))                            # the gaps gated to digital silence (fx tails kept)
    for e in el:
        a = int((e['out'][0] - 0.004) * SR); b = int((e['out'][1] + e['fx_tail'] + 0.03) * SR)
        mask[max(0, a):b] = 1.0
    from scipy.ndimage import uniform_filter1d
    mask = np.minimum(1.0, uniform_filter1d(mask, int(0.004 * SR)) * 1.0)
    y = y * mask
    tp = true_peak(y)
    gain = 10 ** (-1.0 / 20) / tp
    y = y * gain
    sf.write(OUT, y.astype(np.float32), SR, subtype='PCM_24')
    json.dump(dict(sr=SR, duration=round(len(y) / SR, 3), final_gain_db=round(20 * np.log10(gain), 2),
                   narrator_median_db=round(nar_med, 2), take_median_db={k: round(v, 2) for k, v in take_med.items()},
                   lines=el), open(EDL, 'w'), indent=1)
    os.makedirs(os.path.join(W, 'align'), exist_ok=True)
    json.dump(dict(note='Ping / Clank beats of the script (sounds, not in the voice track): t = where the sound starts (s, '
                        'narration_en.wav time); line = the timeline line it follows', beats=beats),
              open(os.path.join(W, 'align', 'beats.json'), 'w'), indent=1)
    json.dump(dict(note='voice fx baked into narration_en.wav (tools/vo_fx.py): t0/t1 = the line, tail_end = where its fx '
                        'decay ends; tape = little Adam\'s song off the old VHS camcorder tape (the picture shows the tape)',
                   lines=[dict(i=e['i'], tag=e['tag'], who=e['who'], fx=e['fx'], t0=e['out'][0], t1=e['out'][1],
                               tail_end=round(e['out'][1] + e['fx_tail'], 3), en=e['en']) for e in el if e['fx']]),
              open(os.path.join(W, 'align', 'voice_fx.json'), 'w'), indent=1)
    m, s = divmod(len(y) / SR, 60)
    log('narration_en.wav %d:%05.2f (%d lines), final gain %+.2f dB -> %s' % (m, s, len(el), 20 * np.log10(gain), OUT))


def cmd_check():
    import vo_check
    sys.exit(vo_check.main())


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'analyze'
    {'analyze': cmd_analyze, 'build': cmd_build, 'check': cmd_check}[cmd]()
