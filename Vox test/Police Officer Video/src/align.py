"""Find where every script line sits in the narrator's recordings, then fit the Russian dub into the English timeline.
    python3 align.py <en.mp3> <ru.mp3> <parakeet dir> <whisper dir> <out dir>
English: Parakeet word timestamps, matched word-by-word to the script.
Russian: the recording is cut at pauses, each piece is transcribed with Whisper and matched to the Russian script text,
and line starts inside a piece are placed by character position.
Writes timeline.json (English line times + Russian source times), vo_en.wav (48 kHz) and vo_ru_dub.wav (Russian, re-timed so
each line starts with its English line; lines that run long are time-compressed with rubberband, pitch unchanged).
"""
import difflib, json, os, re, subprocess, sys
import numpy as np, soundfile as sf, librosa, sherpa_onnx

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'script'))
from lines import LINES

EN, RU, PK, WH, OUT = sys.argv[1:6]
SR = 48000
os.makedirs(OUT, exist_ok=True)


def load(path, sr):
    y, _ = librosa.load(path, sr=sr, mono=True); return y.astype(np.float32)


en48, ru48 = load(EN, SR), load(RU, SR)
en16, ru16 = load(EN, 16000), load(RU, 16000)

# ------------------------------------------------------------------ English: word timestamps
CACHE = os.path.join(OUT, 'asr_cache.json')
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
pk = None if 'en_words' in cache else sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f'{PK}/encoder.int8.onnx', decoder=f'{PK}/decoder.int8.onnx', joiner=f'{PK}/joiner.int8.onnx',
                                                   tokens=f'{PK}/tokens.txt', model_type='nemo_transducer', num_threads=3)
words = []
step = 16000 * 20
for a in ([] if pk is None else range(0, len(en16), step - 16000 * 2)):            # 20 s windows with 2 s overlap
    seg = en16[a:a + step]
    if len(seg) < 1600: break
    st = pk.create_stream(); st.accept_waveform(16000, seg); pk.decode_stream(st)
    cur = None
    for t, ts in zip(st.result.tokens, st.result.timestamps):
        T = ts + a / 16000
        if t.startswith(' ') or cur is None: cur = [t.strip(), T]; words.append(cur)
        else: cur[0] += t
words.sort(key=lambda w: w[1])
dedup = []                                                   # drop words repeated by the overlapping windows
for w in words:
    if dedup and abs(w[1] - dedup[-1][1]) < 0.12 and w[0].lower() == dedup[-1][0].lower(): continue
    if dedup and w[1] < dedup[-1][1] - 0.05: continue
    dedup.append(w)
words = dedup if pk is not None else cache['en_words']
cache['en_words'] = words
norm = lambda s: re.sub(r"[^a-z0-9]", '', s.lower())
asr = [norm(w) for w, _ in words]
script, owner = [], []
for i, l in enumerate(LINES):
    for w in l['en'].replace('12:36', 'twelve thirty six').split():
        n = norm(w)
        if n: script.append(n); owner.append(i)
sm = difflib.SequenceMatcher(None, script, asr, autojunk=False)
first, last = {}, {}
for blk in sm.get_matching_blocks():
    for k in range(blk.size):
        i = owner[blk.a + k]; t = words[blk.b + k][1]
        first.setdefault(i, t); last[i] = t
found = sorted(first)
print(f'English: {len(words)} words recognised, {len(found)}/{len(LINES)} lines located')


def line_bounds(times_first, times_last, y16, n):
    """Start/end per line; missing lines borrow neighbours; snap starts back to the onset before the first word."""
    st, en = [None] * n, [None] * n
    for i in range(n):
        if i in times_first: st[i], en[i] = times_first[i] - 0.06, times_last[i] + 0.35
    for i in range(n):
        if st[i] is None:
            prev = next((en[j] for j in range(i - 1, -1, -1) if en[j] is not None), 0.0)
            nxt = next((st[j] for j in range(i + 1, n) if st[j] is not None), None)
            if nxt is not None and nxt - prev > 1.0:      # spoken but missed by the recogniser: it fills the gap
                st[i], en[i] = prev + 0.3 * (nxt - prev), nxt - 0.25
            else:                                          # not in the recording at all
                st[i] = en[i] = prev
    env = librosa.feature.rms(y=y16, frame_length=400, hop_length=160)[0]
    db = 20 * np.log10(env + 1e-6); floor = np.percentile(db, 20)
    for i in range(n):  # walk back to the first loud frame of the word, never past the previous line
        f = int(st[i] * 100)
        lo = int((en[i - 1] if i else 0) * 100)
        while f > lo + 1 and db[f - 1] > floor + 8: f -= 1
        st[i] = f / 100
    for i in range(n):  # end: last loud frame before the next line starts
        nxt = st[i + 1] if i + 1 < n else len(y16) / 16000
        f = int(min(en[i], nxt) * 100)
        while f > int(st[i] * 100) + 5 and db[min(f, len(db) - 1)] < floor + 6: f -= 1
        en[i] = min(nxt, f / 100 + 0.08)
    return st, en


en_st, en_en = line_bounds(first, last, en16, len(LINES))

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
    tl['lines'].append({'i': k, 'who': l['who'], 'tag': l['tag'], 'fx': l['fx'], 'en': l['en'], 'ru': l['ru'],
                        't': round(en_st[k], 3), 'end': round(en_en[k], 3), 'found_en': k in first,
                        'ru_src': [round(ru_st[k], 3), round(ru_en[k], 3)], 'found_ru': k in ru_first})
tl['dub'] = log
json.dump(tl, open(os.path.join(OUT, 'timeline.json'), 'w'), ensure_ascii=False, indent=1)
dr = np.array([g['drift'] for g in log]); tp = np.array([g['tempo'] for g in log])
print(f'dub: {len(groups)} groups, median tempo {np.median(tp):.2f}, max {tp.max():.2f}, drift p95 {np.percentile(dr, 95):.2f}s max {dr.max():.2f}s')
