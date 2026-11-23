"""The voice edit of "If Your Little Brother Says Someone Lives In The Walls... DON'T LAUGH" (Night Policy; adapted
from the Ice Cream film's tool): the owner's 13 ElevenLabs takes -> one clean, paced voice track (English).
    python3 tools/vo_edit.py analyze     line -> take mapping, recogniser vs script per line, dropped islands (prints)
    python3 tools/vo_edit.py build       -> W/narration/narration_en.wav (48 kHz mono, 24-bit) + edit_list.json
    python3 tools/vo_edit.py check       scans of the built file (gaps vs plan, residual breaths, clicks at cuts,
                                         levels per voice, peaks); then run tools/align.py and tools/vo_asrcheck.py --every
Sources: W/narration/raw/index.json (6 narrator parts in order, one take per character; Theo and Sam share one adult
take), words from tools/vo_asr.py (W/narration/asr/<take>.json: Parakeet TDT word start/end times, used as anchors),
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
     colon 0.20-0.35, ellipsis 0.30-0.50, mid-line full stop 0.15-0.30, none <= 0.25; character lines may hold x1.5,
     Mr. Pell x2: his slow, hushed delivery). Pauses inside words (< 120 ms) are never touched. Nothing is stretched.
  4. Level: one gain per line, never inside a phrase: a narrator line moves 60 % of its distance to the narrator's
     median speech level (+-6 dB, nothing inside 1.5 dB: his whispers stay whispers, only softer than the rest by
     less); a character line goes the whole way to the narrator's median (+ VOICE_LU), so every voice sits at the
     narrator's level. The narrator's voice is otherwise untouched.
  5. Voices and places: Theo and Sam are re-voiced into child voices (tools/vo_voices.py); the staged lines get their
     place (tools/vo_fx.py: ceiling, wall, mask, vent, phone), each loudness-matched to the dry line + its offset.
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
NARR = ['narrator_part%d' % k for k in range(1, 7)]
TAKE = {'dad': 'dad', 'mom': 'mom', 'theo': 'theo_and_sam_adult_take', 'sam': 'theo_and_sam_adult_take',
        'dabrowski': 'dabrowski', 'pell': 'pell', 'dispatcher': 'dispatcher', 'officer': 'officer'}
VOICE_LU = {'pell': -1.0, 'officer': 0.0, 'dispatcher': 0.0, 'dad': 0.0, 'mom': 0.0, 'dabrowski': 0.0,
            'theo': -0.5, 'sam': -0.5}            # dB vs the narrator's median speech level (before any fx offset)
THR = -60.0                                        # island threshold (dBFS, 5 ms RMS)
LEAD, TAIL = 0.30, 0.60
CLAMP = {',': (0.10, 0.30), ';': (0.20, 0.35), ':': (0.20, 0.35), '...': (0.30, 0.50), '.': (0.15, 0.30),
         '?': (0.15, 0.30), '!': (0.15, 0.30), '': (0.0, 0.25)}
HOLD = {'pell': 2.0}                               # x the clamp's upper bound for character lines (default 1.5)
# hand fixes (raw take seconds), checked by ear-free measurement: {tag: {...}} (none needed so far)
CUTS = {}

NUM = {'zero': '0', 'one': '1', 'two': '2', 'to': '2', 'too': '2', 'three': '3', 'four': '4', 'five': '5', 'six': '6',
       'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10', 'twelve': '12', 'fourteen': '14', 'fifty': '50',
       'sixty': '60', 'hundred': '100', 'first': '1st', 'fifth': '5th'}
SAME = {'larksburg': 'larkspur', 'larkspurs': 'larkspur', 'markspur': 'larkspur', 'pel': 'pell', 'pells': 'pell',
        'grey': 'gray', 'shh': 'shhh', 'sh': 'shhh', 'mr': 'mister', 'mrs': 'missus', 'hushabai': 'hushabye',
        'hushaby': 'hushabye', 'hushabi': 'hushabye', 'okay': 'ok', 'goodnight': 'good night', 'dabrowskis': 'dabrowski',
        'misses': 'missus', 'dubrowski': 'dabrowski', 'grill': 'grille', 'larksbury': 'larkspur', 'larksburgh': 'larkspur',
        'larksford': 'larkspur', 'hashabai': 'hushabye', 'hashaby': 'hushabye', 'hushabuy': 'hushabye'}
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


def asr_tokens(key, part=0):
    d = json.load(open(os.path.join(ASRDIR, key + '.json')))
    flat = []
    for w, t0, t1 in d['words']:
        for t in _raw_toks(w): flat.append((t, float(t0), float(t1)))
    return [dict(tok=t, src=key, t0=a[1], t1=b[2]) for t, a, b in _join(flat, key=lambda x: x[0])]


def load_lines():
    from lines import LINES
    return [dict(l, i=i) for i, l in enumerate(LINES)]


def take_of(l):
    return 'narrator' if l['who'] == 'narrator' else TAKE[l['who']]


def map_lines(L):
    """Every line -> its recognised words in its take: l['asr'] = [token dicts with 'li' (line token index)];
    l['diff'] = the mismatches (op, script words, heard words)."""
    groups = {}
    for l in L: groups.setdefault(take_of(l), []).append(l)
    for g, ls in groups.items():
        if g == 'narrator': A = [t for k in NARR for t in asr_tokens(k)]
        else:
            A = asr_tokens(g)
            if g == TAKE['theo']: ls = sorted(ls, key=lambda l: (l['who'] != 'theo', l['i']))
        S = [(l['i'], k, t) for l in ls for k, t in enumerate(toks(l['en']))]
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
            l['head_unmatched'] = any(op == 'delete' and sw and sw[0] == toks(l['en'])[0] for op, sw, _ in l['diff'][:1])
    return L


# ============================================================================ audio analysis
_TAKES = {}


def take(key):
    if key not in _TAKES:
        ix = json.load(open(os.path.join(RAWDIR, 'index.json')))
        x, sr = sf.read(os.path.join(RAWDIR, ix[key]), dtype='float64')
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
            if ls[k]['tag'] in CUTS: c = CUTS[ls[k]['tag']]; cut[k] = (c, c, True); continue
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
    pun = text_punct(l['en'])
    before = [w for w in l['asr'] if w['t0'] < gap_start - 0.02]
    p = pun[before[-1]['li']] if before and before[-1]['li'] < len(pun) else ''
    lo, hi = CLAMP.get(p, CLAMP[''])
    if l['who'] != 'narrator': hi *= HOLD.get(l['who'], 1.5)
    return lo, hi, p


def line_audio(l):
    """The cleaned line (dry, take level) and its piece list."""
    src, a, b, fh, ft = l['span']
    x = take(src)['x']
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
    return line_spans(L)


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
    take_med = {}
    for l in L:
        if l['who'] != 'narrator': take_med.setdefault(l['who'], []).append(l['lvl'])
    take_med = {k: float(np.median(v)) for k, v in take_med.items()}
    parts, t, el = [np.zeros(int(LEAD * SR))], LEAD, []
    for l, y in zip(L, dry):
        if l.get('drop'):                              # owner: no dialogue tags; keep the longer of the two pauses
            if el:
                want = float(l['pause'])
                nxt = next((m for m in L[L.index(l) + 1:] if not m.get('drop')), None)
                if nxt is not None and nxt['who'] == el[-1]['who'] != 'narrator':   # one speaker's two quotes now meet:
                    want = max(want, 0.55 if nxt['who'] == 'pell' else 0.40)        # a natural phrase pause between them
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
        y = y * 10 ** (g / 20)
        vst = None
        if l['who'] in ('theo', 'sam'):
            y, vst = vo_voices.voice_line(y, l)
        if l.get('fx'):
            y = vo_fx.apply(y, l['fx'])
        n0 = len(y)
        parts.append(y)
        gap = float(l['pause']) if l['i'] < len(L) - 1 else TAIL
        tail = vo_fx.TAIL.get(l.get('fx'), 0.0)       # an fx's decay runs into the gap (never past it)
        parts.append(np.zeros(int(round(gap * SR))))
        el.append(dict(i=l['i'], tag=l['tag'], who=l['who'], fx=l.get('fx'), en=l['en'], out=[round(t, 3), round(t + n0 / SR, 3)],
                       pause=round(gap, 3), gain_db=round(g, 2), level_dry=round(l['lvl'], 1), src=l['span'][0],
                       src_span=[round(l['span'][1], 3), round(l['span'][2], 3)], forced=[l['span'][3], l['span'][4]],
                       pieces=l['pieces'], dropped=l['dropped'], voice=vst, fx_tail=tail))
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
    m, s = divmod(len(y) / SR, 60)
    log('narration_en.wav %d:%05.2f (%d lines), final gain %+.2f dB -> %s' % (m, s, len(el), 20 * np.log10(gain), OUT))


def cmd_check():
    import vo_check
    sys.exit(vo_check.main())


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'analyze'
    {'analyze': cmd_analyze, 'build': cmd_build, 'check': cmd_check}[cmd]()
