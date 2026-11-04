"""Find where every script line sits in the narrator's recordings, then (optionally) fit a Russian dub into the English timeline.
    python3 align.py <en.wav> <ru.mp3 | -> <parakeet dir> <whisper dir | -> <out dir>   ('-' for RU: English timeline only)
The script is ../../script/lines.py (the project's script/ folder, two levels above this file).
English: Parakeet word timestamps, matched word-by-word to the script. The recording is decoded in ~20 s windows that are
cut at the quietest point near each boundary and padded with 1.5 s of context on both sides; each window only keeps the
words that start inside its own span, so no word is lost or doubled at a window edge.
Russian: the recording is cut at pauses, each piece is transcribed with Whisper and matched to the Russian script text,
and line starts inside a piece are placed by character position.
Writes timeline.json (lines with t/end, per-line match quality and word times), lines_table.txt, vo_en.wav (48 kHz) and
asr_cache.json ('en_words': [[word, start], ...] straight from the recogniser). Delete asr_cache.json to re-run the ASR.
"""
import difflib, json, os, re, subprocess, sys
import numpy as np, soundfile as sf, librosa, sherpa_onnx

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'script'))
from lines import LINES

EN, RU, PK, WH, OUT = sys.argv[1:6]
SR = 48000
os.makedirs(OUT, exist_ok=True)


def load(path, sr):
    y, _ = librosa.load(path, sr=sr, mono=True); return y.astype(np.float32)


en48, ru48 = load(EN, SR), (load(RU, SR) if RU != '-' else None)
en16, ru16 = load(EN, 16000), (load(RU, 16000) if RU != '-' else None)
env16 = librosa.feature.rms(y=en16, frame_length=400, hop_length=160)[0]          # 10 ms frames
DB = 20 * np.log10(env16 + 1e-6); FLOOR = float(np.percentile(DB, 20))

# ------------------------------------------------------------------ English: word timestamps
CACHE = os.path.join(OUT, 'asr_cache.json')
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def silence_cuts(db, total_s, every=20.0, search=4.0):
    """Window boundaries at the quietest 200 ms stretch within +-search s of every `every` s."""
    sm = np.convolve(db, np.ones(20) / 20, mode='same')
    cuts, c = [0.0], every
    while c < total_s - 8:
        a, b = int((c - search) * 100), int((c + search) * 100)
        k = a + int(np.argmin(sm[a:b]))
        cuts.append(k / 100); c = k / 100 + every
    cuts.append(total_s)
    return cuts


if 'en_words' in cache:
    words = cache['en_words']
else:
    pk = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f'{PK}/encoder.int8.onnx', decoder=f'{PK}/decoder.int8.onnx', joiner=f'{PK}/joiner.int8.onnx',
                                                       tokens=f'{PK}/tokens.txt', model_type='nemo_transducer', num_threads=3)
    total = len(en16) / 16000
    cuts = silence_cuts(DB, total)
    words, PAD = [], 1.5
    for k in range(len(cuts) - 1):
        c0, c1 = cuts[k], cuts[k + 1]
        a = max(0, int((c0 - PAD) * 16000)); b = min(len(en16), int((c1 + PAD) * 16000))
        st = pk.create_stream(); st.accept_waveform(16000, en16[a:b]); pk.decode_stream(st)
        cur = None
        for t, ts in zip(st.result.tokens, st.result.timestamps):
            T = ts + a / 16000
            new = t.startswith(' ') or t.startswith('▁') or cur is None
            if new:
                cur = [t.strip().lstrip('▁'), round(T, 3)]
                if c0 <= T < c1 or (k == 0 and T < c0): words.append(cur)
                else: cur = ['', T]                                # owned by the neighbouring window: decode, but drop
            else:
                cur[0] += t
        words = [w for w in words if w[0]]
    words.sort(key=lambda w: w[1])
_n = lambda s: re.sub(r"[^a-z0-9]", '', s.lower())
_d = []
for w in words:                                    # a word heard by both windows right at a cut: keep it once
    if _d and _n(w[0]) == _n(_d[-1][0]) and w[1] - _d[-1][1] < 0.3: continue
    _d.append(w)
if len(_d) != len(words) or 'en_words' not in cache:
    words = _d; cache['en_words'] = words
    json.dump(cache, open(CACHE, 'w'), ensure_ascii=False)

NUM = {'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
       'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14', 'fifteen': '15', 'sixteen': '16',
       'seventeen': '17', 'eighteen': '18', 'nineteen': '19', 'twenty': '20', 'thirty': '30', 'forty': '40', 'fortyfive': '45',
       'fifty': '50', 'sixty': '60', 'hundred': '100', 'gonna': 'goingto', 'mom': 'mom', 'mum': 'mom', 'okay': 'ok'}
SPLIT = {'barefoot': ['bare', 'foot'], 'grownup': ['grown', 'up']}       # the recogniser joins / splits these inconsistently


def toks(w):
    n = re.sub(r"[^a-z0-9]", '', w.lower())
    if not n: return []
    n = NUM.get(n, n)
    return SPLIT.get(n, [n])


asr, asr_t = [], []
for w, t in words:
    for n in toks(w): asr.append(n); asr_t.append(t)
script, owner, sword = [], [], []
for i, l in enumerate(LINES):
    for w in l['en'].split():
        for n in toks(w): script.append(n); owner.append(i); sword.append(w)
sm = difflib.SequenceMatcher(None, script, asr, autojunk=False)
wt = [None] * len(script)                          # time of every script word (exact match, or placed inside a small replace)
exact = [False] * len(script)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == 'equal':
        for k in range(i2 - i1): wt[i1 + k] = asr_t[j1 + k]; exact[i1 + k] = True
    elif tag == 'replace' and (i2 - i1) <= 4 and (j2 - j1) <= 4:
        for k in range(i2 - i1): wt[i1 + k] = asr_t[j1 + min(j2 - j1 - 1, int(k * (j2 - j1) / (i2 - i1)))]
first, last, nwords, nexact, lwords = {}, {}, {}, {}, {}
for k, i in enumerate(owner):
    nwords[i] = nwords.get(i, 0) + 1; nexact[i] = nexact.get(i, 0) + exact[k]
    lwords.setdefault(i, []).append([sword[k], None if wt[k] is None else round(wt[k], 3), exact[k]])
    if wt[k] is not None:
        first.setdefault(i, wt[k]); last[i] = wt[k]
QUAL = {i: nexact.get(i, 0) / max(1, nwords.get(i, 1)) for i in range(len(LINES))}
found = sorted(first)
print(f'English: {len(words)} words recognised, {len(script)} script words, {sum(exact)} matched exactly, {len(found)}/{len(LINES)} lines located')


def line_bounds(times_first, times_last, y16, n, db=None):
    """Start/end per line; missing lines borrow neighbours; starts snap back to the onset before the first word,
    ends run forward to the last loud frame of the last word (never into the next line)."""
    if db is None:
        env = librosa.feature.rms(y=y16, frame_length=400, hop_length=160)[0]; db = 20 * np.log10(env + 1e-6)
    thr = np.percentile(db, 90) - 30        # speech vs pause: sentence-final words fall to -30 dB below the voice, pauses lie under it
    thr_end = thr + 4                        # ends: breaths in the pauses sit at -26..-32 dB below the voice, final syllables above
    st, en, lw = [None] * n, [None] * n, [None] * n
    for i in range(n):
        if i in times_first: st[i], lw[i] = times_first[i] - 0.06, times_last[i]
    for i in range(n):
        if st[i] is None:
            prev = next((lw[j] + 0.5 for j in range(i - 1, -1, -1) if lw[j] is not None), 0.0)
            nxt = next((st[j] for j in range(i + 1, n) if st[j] is not None), None)
            if nxt is not None and nxt - prev > 1.0:      # spoken but missed by the recogniser: it fills the gap
                st[i], lw[i] = prev + 0.3 * (nxt - prev), nxt - 0.6
            else:                                          # not in the recording at all
                st[i] = lw[i] = prev
    total = len(y16) / 16000
    for i in range(n):  # Parakeet word starts sit on the onset (median error ~10 ms): start 20 ms before the first word and walk
        f0 = int(round((st[i] + 0.04) * 100))                    # back to a quiet frame if there is one within 120 ms; in run-on
        lo = max(int(round(((lw[i - 1] + 0.12) if i else 0) * 100)), f0 - 12)   # speech (no quiet frame) keep the word start
        f = f0                                                    # (picking energy dips there cut "voicemail", "softer", "coffee")
        while f > lo and db[f - 1] > thr: f -= 1
        if f == f0 and db[f0] <= thr:                             # the word start is quantised to 80 ms: if it lands in the
            hi = f0 + 12                                          # silence before the word, step forward to the first loud frame
            while f < hi and db[f] <= thr: f += 1
            if f == hi: f = f0
        st[i] = (f if (f > lo or db[max(0, f - 1)] <= thr) else f0) / 100
    for i in range(n):  # end: from the last word's start, past its quiet onset, to the last loud frame before a 150 ms silence
        nxt = st[i + 1] if i + 1 < n else total
        lim = min(int((nxt - 0.02) * 100), int((lw[i] + 1.3) * 100), len(db) - 1)
        f = int(lw[i] * 100)
        g = f
        while g < min(lim, f + 30) and db[g] <= thr_end: g += 1   # a soft first consonant (f, h, s) is not the end
        lastloud, quiet, f = g, 0, g
        while f < lim:
            if db[f] > thr_end: lastloud = f; quiet = 0
            else:
                quiet += 1
                if quiet >= 15: break                            # 150 ms: longer than a stop closure (the p in "spoon")
            f += 1
        en[i] = round(min(nxt, max(st[i] + 0.2, (lastloud + 1) / 100 + 0.05)), 3)
    return st, en


en_st, en_en = line_bounds(first, last, en16, len(LINES), DB)


def write_table(path):
    with open(path, 'w') as fh:
        fh.write(f"{'i':>3}  {'t':>8}  {'end':>8}  who  {'tag':<11} {'q':>4}  text\n")
        for k, l in enumerate(LINES):
            fh.write(f"{k:>3}  {en_st[k]:8.2f}  {en_en[k]:8.2f}  {l['who']:<3}  {(l['tag'] or ''):<11} {QUAL[k]:4.2f}  {l['en']}\n")


def line_entry(k, l):
    return {'i': k, 'who': l['who'], 'tag': l['tag'], 'fx': l['fx'], 'en': l['en'], 'ru': l['ru'],
            't': round(en_st[k], 3), 'end': round(en_en[k], 3), 'found_en': k in first, 'match': round(QUAL[k], 3),
            'words': [[w, t] for w, t, _ in lwords.get(k, [])]}


def report():
    low = [k for k in range(len(LINES)) if QUAL[k] < 0.75 or k not in first]
    print(f'lines below 75% exact word match: {len(low)}')
    for k in low:
        print(f"  {k:>3} {en_st[k]:7.2f} q={QUAL[k]:.2f}  {LINES[k]['en']}")
        print('       heard:', ' '.join(w for w, t in words if en_st[k] - 0.1 <= t <= en_en[k] + 0.05))


if RU == '-':                                                  # English only (no Russian recording): timeline + vo_en, no dub
    sf.write(os.path.join(OUT, 'vo_en.wav'), en48, SR, subtype='PCM_24')
    tl = {'duration_en': round(len(en48) / SR, 3), 'lines': [], 'dub': []}
    for k, l in enumerate(LINES):
        e = line_entry(k, l); e.update({'ru_src': None, 'found_ru': False}); tl['lines'].append(e)
    json.dump(tl, open(os.path.join(OUT, 'timeline.json'), 'w'), ensure_ascii=False, indent=1)
    write_table(os.path.join(OUT, 'lines_table.txt'))
    report()
    print(f'English only: {sum(k in first for k in range(len(LINES)))}/{len(LINES)} lines located'); sys.exit(0)

# ------------------------------------------------------------------ Russian: pause-split pieces, Whisper, character alignment
wh = None if 'ru_texts' in cache else sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f'{WH}/small-encoder.int8.onnx', decoder=f'{WH}/small-decoder.int8.onnx',
                                                tokens=f'{WH}/small-tokens.txt', language='ru', task='transcribe', num_threads=3)
iv = librosa.effects.split(ru16, top_db=38, frame_length=800, hop_length=160)
pieces = []
for a, b in iv:                                               # merge tiny gaps, keep pieces under ~25 s
    if pieces and a - pieces[-1][1] < 0.22 * 16000 and b - pieces[-1][0] < 25 * 16000: pieces[-1][1] = b
    else: pieces.append([a, b])
rnorm = lambda s: re.sub(r'[^а-яa-z0-9]', '', s.lower().replace('ё', 'е'))
full, chowner = [], []
for i, l in enumerate(LINES):
    for ch in rnorm(l['ru']): full.append(ch); chowner.append(i)
full = ''.join(full)
cursor, ru_first = 0, {}
texts = cache.get('ru_texts', [])
for pi, (a, b) in enumerate(pieces):
    if wh is not None:
        st = wh.create_stream(); st.accept_waveform(16000, ru16[a:b]); wh.decode_stream(st); texts.append(st.result.text)
    txt = rnorm(texts[pi])
    if not txt: continue
    win = full[cursor:cursor + len(txt) * 2 + 120]
    m = difflib.SequenceMatcher(None, win, txt, autojunk=False)
    blocks = [bk for bk in m.get_matching_blocks() if bk.size >= 3]
    if not blocks: continue
    s0 = cursor + blocks[0].a; s1 = cursor + blocks[-1].a + blocks[-1].size
    span = max(1, s1 - s0)
    for c in range(s0, s1):                                   # place each line that starts inside this piece by its character position
        i = chowner[c]
        if i not in ru_first and (c == 0 or chowner[c - 1] != i):
            ru_first[i] = (a + (b - a) * (c - s0) / span) / 16000
    if chowner[s0] not in ru_first: ru_first[chowner[s0]] = a / 16000
    cursor = s1
cache['ru_texts'] = texts
json.dump(cache, open(CACHE, 'w'), ensure_ascii=False)
print(f'Russian: {len(pieces)} pieces, {len(ru_first)}/{len(LINES)} line starts located')
ru_last = {}
ks = sorted(ru_first)
for k, i in enumerate(ks): ru_last[i] = (ru_first[ks[k + 1]] - 0.35) if k + 1 < len(ks) else len(ru16) / 16000 - 0.4
ru_st, ru_en = line_bounds(ru_first, ru_last, ru16, len(LINES))

# ------------------------------------------------------------------ the dub: each Russian line starts with its English line
def rubber(x, tempo):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-af', f'rubberband=tempo={tempo:.4f}:pitchq=quality',
                        '-f', 'f32le', '-'], input=x.astype(np.float32).tobytes(), capture_output=True)
    return np.frombuffer(p.stdout, np.float32).copy()


dub = np.zeros(len(en48) + SR * 4, np.float32)
groups, i, n = [], 0, len(LINES)
while i < n:                                                   # lines with no Russian start of their own ride with the previous one
    j = i + 1
    while j < n and j not in ru_first: j += 1
    groups.append((i, j)); i = j
log, t_free = [], 0.0
for gi, (i, j) in enumerate(groups):
    src = ru48[int(ru_st[i] * SR):int(ru_en[j - 1] * SR)].copy()
    slot0 = max(en_st[i], t_free)
    slot1 = en_st[j] - 0.08 if j < n else len(en48) / SR
    need = len(src) / SR
    room = max(0.3, slot1 - slot0)
    tempo = 1.0
    if need > room:
        tempo = min(1.3, need / room)                          # compress up to 30%, the rest spills into the next pause
        src = rubber(src, tempo)
    a = int(slot0 * SR)
    f = min(len(src), int(0.008 * SR))
    if f: src[:f] *= np.linspace(0, 1, f); src[-f:] *= np.linspace(1, 0, f)
    dub[a:a + len(src)] += src
    t_free = slot0 + len(src) / SR + 0.05
    log.append({'lines': [i, j], 'en_start': round(en_st[i], 3), 'ru_start': round(slot0, 3), 'drift': round(slot0 - en_st[i], 3), 'tempo': round(tempo, 3)})
dub = dub[:len(en48) + int(1.0 * SR)]
sf.write(os.path.join(OUT, 'vo_en.wav'), en48, SR, subtype='PCM_24')
sf.write(os.path.join(OUT, 'vo_ru_dub.wav'), dub, SR, subtype='PCM_24')
tl = {'duration_en': round(len(en48) / SR, 3), 'lines': []}
for k, l in enumerate(LINES):
    e = line_entry(k, l); e.update({'ru_src': [round(ru_st[k], 3), round(ru_en[k], 3)], 'found_ru': k in ru_first}); tl['lines'].append(e)
tl['dub'] = log
json.dump(tl, open(os.path.join(OUT, 'timeline.json'), 'w'), ensure_ascii=False, indent=1)
write_table(os.path.join(OUT, 'lines_table.txt'))
report()
dr = np.array([g['drift'] for g in log]); tp = np.array([g['tempo'] for g in log])
print(f'dub: {len(groups)} groups, median tempo {np.median(tp):.2f}, max {tp.max():.2f}, drift p95 {np.percentile(dr, 95):.2f}s max {dr.max():.2f}s')
