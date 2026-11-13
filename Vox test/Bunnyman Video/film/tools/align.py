"""Find where every script line sits in the narrator's recording (English only).
    python3 align.py [narration.wav] [parakeet dir] [out dir]          (all optional; defaults below)
    python3 align.py --asr-only ...      transcribe only (writes asr_cache.json + transcript.txt, no lines.py needed)
    python3 align.py --write-pauses ...  also rewrite each L(...) row of lines.py with the measured pause / pace
Defaults: W/narration/narration_en.wav, the Parakeet TDT 0.6b v2 int8 dir ($PARAKEET_DIR or the scratchpad models dir),
W/align, with W = Bunnyman Video/film/_work. Script: Bunnyman Video/script/lines.py (the recording is the truth).
ASR: Silero VAD (vad.onnx beside the Parakeet dir) finds speech; neighbouring segments are merged into chunks of at most
~16 s, cut from the full recording with 0.3 s padding, and transcribed by Parakeet TDT with token timestamps. Words are
cached in asr_cache.json ('en_words': [[word, t], ...] as film.py reads them, 'en_chunks': [[t0, t1, text], ...]);
a rescue pass then decodes every stretch louder than -40 dB that no chunk covers (the VAD skips an isolated short word);
delete it to re-run the ASR (about 2 min on 2 threads). Neighbouring chunks share the padding, so a word straddling a
VAD cut can be heard by both: the copy that opens a chunk is dropped when it repeats the previous word < 0.45 s before.
Matching: script and ASR words are normalised (lower case; clock times, number words and to/two unified) and matched with
difflib; each line takes its first/last matched word. A line with no matched word (a word the recogniser spells its own
way, e.g. the drawn-out 'RETURN') takes the unclaimed ASR words between its neighbours ('gap-filled', printed); a line
whose first or last words went unmatched takes the unclaimed ASR words next to it ('stretched', printed). A line
the recogniser did not hear at all (a whispered word, a child's voice) takes the sound between its found neighbours
('energy-filled', printed: the edited narration has silence between lines).
Bounds on a narration with silent gaps (this film): each boundary is placed in the longest stretch below -70 dBFS between
the two lines' words, so t / end are the first / last sound of each line to the millisecond (silence_bounds).
Bounds: start = voice onset before the first word (at most 0.3 s back, never into the previous line's last word); end =
last sounding frame after the last word (-52 dB), stopped by the next word. The edited narration of this film
(tools/vo_edit.py) has digital silence between lines, paced by _work/narration/pacing_map.md (0.15-2.8 s).
Writes timeline.json ({'duration_en', 'lines': [{i, who, tag, fx, en, ru, pause, pace, t, end, found_en, match,
pause_rec, pace_rec, ...}], 'dub': []}), vo_en.wav (48 kHz, 24-bit), asr_cache.json, transcript.txt and lines_table.txt.
"""
import difflib, json, os, re, sys
import numpy as np, soundfile as sf, librosa

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))                               # .../Bunnyman Video
W = os.path.join(ROOT, 'film', '_work')
MODELS = '/tmp/claude-0/-home-user-claude-todo-demo/aa250ae7-a0b4-594f-9bc6-bd18b596cf27/scratchpad/models'
args = [a for a in sys.argv[1:] if not a.startswith('--')]
ASR_ONLY = '--asr-only' in sys.argv
EN = args[0] if len(args) > 0 else os.path.join(W, 'narration', 'narration_en.wav')
PK = args[1] if len(args) > 1 else os.environ.get('PARAKEET_DIR', os.path.join(MODELS, 'sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8'))
OUT = args[2] if len(args) > 2 else os.path.join(W, 'align')
VAD = os.path.join(os.path.dirname(PK.rstrip('/')), 'vad.onnx')
SR = 48000
os.makedirs(OUT, exist_ok=True)

en48, _ = librosa.load(EN, sr=SR, mono=True); en48 = en48.astype(np.float32)
en16 = librosa.resample(en48, orig_sr=SR, target_sr=16000).astype(np.float32)
DUR = len(en48) / SR

# ------------------------------------------------------------------ ASR: VAD chunks -> Parakeet word timestamps
CACHE = os.path.join(OUT, 'asr_cache.json')
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
if 'en_words' not in cache:
    import sherpa_onnx
    cfg = sherpa_onnx.VadModelConfig(); cfg.silero_vad.model = VAD
    cfg.silero_vad.threshold = 0.45; cfg.silero_vad.min_silence_duration = 0.25
    cfg.silero_vad.min_speech_duration = 0.15; cfg.silero_vad.max_speech_duration = 14; cfg.sample_rate = 16000
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=60)
    segs = []
    for i in range(0, len(en16), 512):
        vad.accept_waveform(en16[i:i + 512])
        while not vad.empty(): segs.append([vad.front.start / 16000, (vad.front.start + len(vad.front.samples)) / 16000]); vad.pop()
    vad.flush()
    while not vad.empty(): segs.append([vad.front.start / 16000, (vad.front.start + len(vad.front.samples)) / 16000]); vad.pop()
    chunks = []
    for a, b in segs:                                           # merge short gaps; keep chunks under ~16 s
        if chunks and a - chunks[-1][1] < 0.7 and b - chunks[-1][0] < 16: chunks[-1][1] = b
        else: chunks.append([a, b])
    pk = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f'{PK}/encoder.int8.onnx', decoder=f'{PK}/decoder.int8.onnx',
                                                       joiner=f'{PK}/joiner.int8.onnx', tokens=f'{PK}/tokens.txt',
                                                       model_type='nemo_transducer', num_threads=2)
    words, ctext = [], []
    for k, (a, b) in enumerate(chunks):
        lo = max(0.0, a - 0.3, chunks[k - 1][1] if k else 0.0)
        hi = min(DUR, b + 0.3, chunks[k + 1][0] if k + 1 < len(chunks) else DUR)
        seg = en16[int(lo * 16000):int(hi * 16000)]
        st = pk.create_stream(); st.accept_waveform(16000, seg); pk.decode_stream(st)
        cur, cw = None, []
        for tok, ts in zip(st.result.tokens, st.result.timestamps):
            if tok.startswith(' ') or cur is None: cur = [tok.strip(), round(float(ts) + lo, 3)]; cw.append(cur)
            else: cur[0] += tok
        cw = [w for w in cw if w[0]]
        nw = lambda x: re.sub(r'[^a-z0-9]', '', x.lower())
        if cw and words and nw(cw[0][0]) == nw(words[-1][0]) and cw[0][1] - words[-1][1] < 0.45:
            cw = cw[1:]                                         # a word straddling the VAD cut, heard by both chunks
        words += cw
        ctext.append([round(lo, 2), round(hi, 2), st.result.text.strip()])
    # rescue pass: sound the VAD skipped (an isolated short word after a long pause: "...count to seven... don't.",
    # the first "Hop, hop" of the jingle) is decoded on its own; a word the chunks already hold is not added twice
    w5 = 80
    e5 = np.sqrt(np.convolve(en16 ** 2, np.ones(w5) / w5, 'same'))[::w5]
    db5 = 20 * np.log10(e5 + 1e-9)
    covered = np.zeros(len(db5), bool)
    for lo_, hi_, _ in ctext: covered[int(lo_ * 200):int(hi_ * 200) + 1] = True
    loud = (db5 > -40) & ~covered
    k5 = 0
    while k5 < len(loud):
        if not loud[k5]: k5 += 1; continue
        j5 = k5
        while j5 < len(loud) and (loud[j5] or (j5 + 30 < len(loud) and loud[j5:j5 + 30].any())): j5 += 1
        a5, b5 = k5 * 0.005, j5 * 0.005; k5 = j5
        if b5 - a5 < 0.08: continue
        lo, hi = max(0.0, a5 - 0.25), min(DUR, b5 + 0.25)
        st = pk.create_stream(); st.accept_waveform(16000, en16[int(lo * 16000):int(hi * 16000)]); pk.decode_stream(st)
        cur, cw = None, []
        for tok, ts in zip(st.result.tokens, st.result.timestamps):
            if tok.startswith(' ') or cur is None: cur = [tok.strip(), round(float(ts) + lo, 3)]; cw.append(cur)
            else: cur[0] += tok
        cw = [w for w in cw if w[0] and a5 - 0.1 <= w[1] <= b5 + 0.05
              and not any(nw(v[0]) == nw(w[0]) and abs(v[1] - w[1]) < 0.4 for v in words)]
        if cw:
            words += cw; ctext.append([round(lo, 2), round(hi, 2), ' '.join(w[0] for w in cw)])
    words.sort(key=lambda w: w[1]); ctext.sort()
    cache = {'en_words': words, 'en_chunks': ctext}
    json.dump(cache, open(CACHE, 'w'), ensure_ascii=False)
words = cache['en_words']
with open(os.path.join(OUT, 'transcript.txt'), 'w') as f:
    for a, b, txt in cache.get('en_chunks', []):
        f.write('%7.2f %7.2f  %s\n' % (a, b, txt))
print(f'ASR: {len(words)} words, {len(cache.get("en_chunks", []))} chunks')
if ASR_ONLY: sys.exit(0)

# ------------------------------------------------------------------ match script words to ASR words
sys.path.insert(0, os.path.join(ROOT, 'script'))
from lines import LINES

NUM = {'zero': '0', 'oh': '0', 'one': '1', 'two': '2', 'to': '2', 'too': '2', 'three': '3', 'four': '4', 'five': '5',
       'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10', 'eleven': '11', 'twelve': '12', 'thirty': '30',
       'forty': '40', 'first': '1st', 'second': '2nd', 'fourth': '4th', 'twentyone': '21', 'fifteen': '15', 'sixty': '60',
       'seventies': '70s', 'mr': 'mister', 'thirteen': '13', 'fifty': '50', 'eighty': '80', 'nineteen': '19',
       'mamma': 'mama', 'lori': 'laurie', 'gray': 'grey', 'aged': 'age', 'pembertons': 'pemberton'}   # spellings of this film
JOIN = {('good', 'night'): 'goodnight', ('any', 'more'): 'anymore', ('head', 'stick'): 'headstick', ('t', 'v'): 'tv',
        ('arm', 'chair'): 'armchair', ('note', 'paper'): 'notepaper', ('tree', 'line'): 'treeline',
        ('bunny', 'man'): 'bunnyman', ('door', 'knob'): 'doorknob', ('grown', 'up'): 'grownup'}
# words the recogniser splits or joins its own way


def toks(s):
    """Normalised word tokens: lower case, letters/digits only; clock times split into hour and minute whatever way they
    are written ('3:07', '3.07', '307', 'three oh seven' -> 3 7); 'a.m.' -> am; number words and to/too/two -> digits;
    possessive 's dropped; Mr -> mister; 'good night' / 'T V' / 'head stick' ... joined (JOIN)."""
    s = s.lower().replace('a.m.', 'am').replace('p.m.', 'pm').replace('-', ' ').replace('—', ' ').replace('’', "'")
    s = re.sub(r'\b1987\b', 'nineteen eighty seven', s)              # the year as it is read
    s = re.sub(r"(\w)'ve\b", r'\1 have', s)
    s = re.sub(r"(\w)'s\b", r'\1', s); s = re.sub(r"s'(?=\W|$)", 's', s)   # possessives: Winks's / Winks' -> winks
    s = re.sub(r'(\d+)[:.](\d\d)', r'\1 \2', s)
    out = []
    for w in s.split():
        n = re.sub(r'[^a-z0-9]', '', w)
        if not n: continue
        n = NUM.get(n, n)
        m = re.fullmatch(r'(\d)(\d\d)', n)                       # '309' (ASR for 3:09) -> 3 9
        if m: out += [m.group(1), str(int(m.group(2)))]; continue
        if re.fullmatch(r'0\d', n): n = n[1]                     # '07' -> '7'
        out.append(n)
    k = []                                                      # '3 0 7' (three oh seven) -> 3 7
    for j, n in enumerate(out):
        if n == '0' and k and k[-1].isdigit() and j + 1 < len(out) and out[j + 1].isdigit(): continue
        if k and (k[-1], n) in JOIN: k[-1] = JOIN[(k[-1], n)]; continue
        k.append(n)
    return k


asr, aw = [], []                                                # normalised ASR tokens and their word index
for k, (w, _) in enumerate(words):
    for n in toks(w):
        if asr and (asr[-1], n) in JOIN: asr[-1] = JOIN[(asr[-1], n)]; continue   # 'Good' 'night,' -> goodnight
        asr.append(n); aw.append(k)
script, owner = [], []
for i, l in enumerate(LINES):
    for n in toks(l['en']): script.append(n); owner.append(i)
sm = difflib.SequenceMatcher(None, script, asr, autojunk=False)
fk, lk, nmatch = {}, {}, {}                                     # line -> first / last matched ASR word index, matched count
for blk in sm.get_matching_blocks():
    for k in range(blk.size):
        i = owner[blk.a + k]; wk = aw[blk.b + k]
        fk.setdefault(i, wk); lk[i] = wk; nmatch[i] = nmatch.get(i, 0) + 1
nwords = {i: sum(1 for o in owner if o == i) for i in range(len(LINES))}
score = {i: nmatch.get(i, 0) / max(1, nwords[i]) for i in range(len(LINES))}
print(f'English: {len(words)} words recognised, {len(fk)}/{len(LINES)} lines matched word by word, '
      f'{sum(nmatch.values())}/{len(script)} script words matched')

# a line whose first (last) script words went unmatched (the recogniser spelled them its own way, e.g. 'Clack. Copying'
# heard as 'Clack kying') takes the unclaimed ASR words just before (after) its first (last) matched word: at most as
# many as it has unmatched words there, within 1.2 s, never past a neighbouring line's matched words
mtok = set(b.a + k for b in sm.get_matching_blocks() for k in range(b.size))
tix = {}
for j, o in enumerate(owner): tix.setdefault(o, []).append(j)
stretched = []
srt = sorted(fk)
for n_, i in enumerate(srt):
    tj = tix.get(i, [])
    lead = next((c for c, j in enumerate(tj) if j in mtok), 0)
    trail = next((c for c, j in enumerate(reversed(tj)) if j in mtok), 0)
    lo = lk[srt[n_ - 1]] if n_ else -1
    hi = fk[srt[n_ + 1]] if n_ + 1 < len(srt) else len(words)
    k = fk[i]
    while lead and k - 1 > lo and words[fk[i]][1] - words[k - 1][1] < 1.2: k -= 1; lead -= 1
    k2 = lk[i]
    while trail and k2 + 1 < hi and words[k2 + 1][1] - words[lk[i]][1] < 1.2: k2 += 1; trail -= 1
    if (k, k2) != (fk[i], lk[i]):
        stretched.append((i, ' '.join(words[q][0] for q in range(k, fk[i])), ' '.join(words[q][0] for q in range(lk[i] + 1, k2 + 1))))
        fk[i], lk[i] = k, k2

# lines with no matched word (a word the recogniser spelled its own way, e.g. a drawn-out 'RETURN'): they take the
# unclaimed ASR words between their matched neighbours, shared by text length when several lines miss in a row
gapfill = []
i = 0
while i < len(LINES):
    if i in fk: i += 1; continue
    j = i
    while j < len(LINES) and j not in fk: j += 1                 # missing run i..j-1
    a = lk[max(k for k in fk if k < i)] + 1 if any(k < i for k in fk) else 0
    b = fk[j] if j < len(LINES) else len(words)
    if b > a:
        run = list(range(i, j)); size = [max(1, len(toks(LINES[r]['en']))) for r in run]
        cut, acc = [a], 0
        for sz in size: acc += sz; cut.append(a + round((b - a) * acc / sum(size)))
        for r, c0, c1 in zip(run, cut, cut[1:]):
            if c1 <= c0: continue
            fk[r], lk[r] = c0, c1 - 1
            heard = ''.join(re.sub(r'[^a-z]', '', words[q][0].lower()) for q in range(c0, c1))
            score[r] = difflib.SequenceMatcher(None, re.sub(r'[^a-z]', '', LINES[r]['en'].lower()), heard).ratio()
            gapfill.append((r, ' '.join(words[q][0] for q in range(c0, c1))))
    i = j
first = {i: words[k][1] for i, k in fk.items()}
last = {i: words[k][1] for i, k in lk.items()}
nxt_word = {i: (words[k + 1][1] if k + 1 < len(words) else DUR) for i, k in lk.items()}

# ------------------------------------------------------------------ line start / end from the word times and the level
env = librosa.feature.rms(y=en16, frame_length=400, hop_length=160)[0]
DB = 20 * np.log10(env + 1e-6)                                  # 10 ms frames
SIL = -52.0                                                     # below this the recording is silent (edited gaps sit at -60..-120 dB)

# lines the recogniser did not hear at all (a whispered word, a child's voice): with silence-separated lines, the
# sound between their found neighbours is theirs ('energy-filled', printed); several missing lines in one gap share
# its sound runs in order
energyfill = []
i = 0
while i < len(LINES):
    if i in first: i += 1; continue
    j = i
    while j < len(LINES) and j not in first: j += 1
    a = (last[max(k for k in first if k < i)] + 0.15) if any(k < i for k in first) else 0.0
    if any(k < i for k in first):                                # skip the previous line's own tail
        f_ = int(a * 100)
        while f_ < len(DB) and DB[f_] > SIL: f_ += 1
        a = f_ / 100
    b = (first[j] - 0.05) if j < len(LINES) else DUR
    act = DB[int(a * 100):int(b * 100)] > SIL
    runs, k0 = [], None
    for f_, on in enumerate(np.concatenate([act, [False]])):
        if on and k0 is None: k0 = f_
        if not on and k0 is not None:
            if f_ - k0 >= 5: runs.append([a + k0 / 100, a + f_ / 100])
            k0 = None
    merged = []
    for r in runs:                                              # runs closer than 0.15 s are one phrase
        if merged and r[0] - merged[-1][1] < 0.15: merged[-1][1] = r[1]
        else: merged.append(r)
    run = list(range(i, j))
    if merged:
        groups = [merged[round(q * len(merged) / len(run)):round((q + 1) * len(merged) / len(run))] or [merged[-1]]
                  for q in range(len(run))]
        for r_, g_ in zip(run, groups):
            first[r_] = g_[0][0] + 0.02; last[r_] = max(g_[0][0] + 0.02, g_[-1][1] - 0.15)
            nxt_word[r_] = b + 0.05
            score[r_] = 0.0
            energyfill.append((r_, round(g_[0][0], 2), round(g_[-1][1], 2)))
    i = j
found = sorted(first)


def line_bounds(n):
    """Start: the voice onset before the first word (walk back over sound, at most 0.3 s, never into the previous line's
    last word; continuous sound means the words run together, so keep the word time). End: the last sounding frame
    after the last word, stopped by the next word. Lines the recording lacks sit at the previous line's end, zero long."""
    st, en = [None] * n, [None] * n
    for i in range(n):
        if i not in first: continue
        t0 = first[i]; f = int(t0 * 100); f_min = int(max(t0 - 0.3, 0.0) * 100)
        prev_last = max((last[j] for j in range(i) if j in last), default=-1.0)
        f_min = max(f_min, int((prev_last + 0.12) * 100) + 1)
        while f > f_min and DB[f - 1] > SIL: f -= 1
        st[i] = (t0 - 0.06) if (f <= f_min and DB[f - 1] > SIL) else max(f / 100 - 0.02, f_min / 100)
    for i in range(n):
        if i not in first: continue
        nxt = next((st[j] for j in range(i + 1, n) if st[j] is not None), DUR)
        lim = min(nxt_word[i] - 0.03, last[i] + 1.8, nxt)
        f = int((last[i] + 0.12) * 100)
        while f < int(lim * 100) and f < len(DB) and DB[f] > SIL: f += 1
        en[i] = max(min(lim, f / 100 + 0.05), st[i] + 0.15)
    for i in range(n):
        if st[i] is None:
            prev = next((en[j] for j in range(i - 1, -1, -1) if en[j] is not None), 0.0); st[i] = en[i] = prev
    return st, en


en_st, en_en = line_bounds(len(LINES))


def silence_bounds(st, en, thr=-70.0, min_gap=0.12):
    """An edited narration with true silence between lines (this film's tools/vo_edit.py): every silent stretch (below
    thr dBFS, 5 ms RMS at 1 ms hops, at least min_gap long) is a candidate boundary; the boundary after line k is the
    longest one whose middle lies between the last word of line k and the first word of line k+1 (+0.15 s), or, when a
    word is badly timed and there is none, between the two lines' median word times; the line ends where that silence
    starts and the next line begins where it ends, to the millisecond.
    Boundaries without such a silence keep the level-based bounds. Returns (starts, ends, number placed)."""
    w = int(0.005 * SR); h = int(0.001 * SR)
    cs = np.concatenate([[0.0], np.cumsum(en48.astype(np.float64) ** 2)])
    idx = np.arange(0, len(en48) - w, h)
    d5 = 10 * np.log10((cs[idx + w] - cs[idx]) / w + 1e-20)
    quiet = d5 < thr
    q = np.concatenate([[False], quiet, [False]])
    dq = np.diff(q.astype(np.int8)); qa = np.where(dq == 1)[0]; qb = np.where(dq == -1)[0]
    gaps = [(a_ / 1000, b_ / 1000) for a_, b_ in zip(qa, qb) if (b_ - a_) / 1000 >= min_gap]
    mids = np.array([(a_ + b_) / 2 for a_, b_ in gaps])
    med = {}
    for i in range(len(LINES)):
        if i in fk and i in lk and lk[i] >= fk[i]: med[i] = float(np.median([words[k][1] for k in range(fk[i], lk[i] + 1)]))
        elif i in first: med[i] = (first[i] + last[i]) / 2
    st, en = list(st), list(en); placed = 0
    for k in range(len(LINES) - 1):
        if k not in med or k + 1 not in med or med[k + 1] <= med[k]: continue
        near = [g for g, m in zip(gaps, mids) if k in last and k + 1 in first and last[k] < m < first[k + 1] + 0.15]
        cand = near or [g for g, m in zip(gaps, mids) if med[k] < m < med[k + 1]]
        if not cand: continue
        a_, b_ = max(cand, key=lambda g: g[1] - g[0])
        en[k] = round(a_ + 0.004, 3); st[k + 1] = round(b_ + 0.001, 3); placed += 1
    if gaps and gaps[0][0] == 0.0: st[0] = round(gaps[0][1] + 0.001, 3)
    if gaps and gaps[-1][1] >= len(quiet) / 1000 - 0.002: en[-1] = round(gaps[-1][0] + 0.004, 3)
    return st, en, placed


en_st, en_en, n_sil = silence_bounds(en_st, en_en)
print(f'bounds: {n_sil}/{len(LINES) - 1} line boundaries placed in the silence between the lines')
order_bad = [k for k in range(1, len(LINES)) if en_st[k] < en_st[k - 1] - 1e-6]
pause_rec = [round(max(0.0, (en_st[k + 1] if k + 1 < len(LINES) else DUR) - en_en[k]), 2) for k in range(len(LINES))]
WORDS_N = {0: 'oh', 1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten',
           11: 'eleven', 12: 'twelve', 20: 'twenty', 30: 'thirty', 40: 'forty', 50: 'fifty'}


def spoken(s):
    """Clock times as they are read ('3:09' -> 'three oh nine', '3:41' -> 'three forty one'), for the speaking rate."""
    def mm(m):
        h, mi = int(m.group(1)), int(m.group(2))
        tail = ('oh ' + WORDS_N[mi]) if mi < 10 else WORDS_N.get(mi) or (WORDS_N[mi // 10 * 10] + ' ' + WORDS_N[mi % 10])
        return WORDS_N[h] + ' ' + tail
    return re.sub(r'(\d{1,2}):(\d\d)', mm, s)


rate = [len(re.sub(r'[^A-Za-z0-9]', '', spoken(l['en']))) / max(0.2, en_en[k] - en_st[k]) for k, l in enumerate(LINES)]
med = float(np.median([r for r, l in zip(rate, LINES) if len(l['en']) >= 20]))
pace_rec = [round(r / med, 2) for r in rate]                      # speaking rate vs the narrator's median (1.0)

sf.write(os.path.join(OUT, 'vo_en.wav'), en48, SR, subtype='PCM_24')
tl = {'duration_en': round(DUR, 3), 'lines': [], 'dub': []}
for k, l in enumerate(LINES):
    tl['lines'].append({'i': k, 'who': l['who'], 'tag': l['tag'], 'fx': l['fx'], 'en': l['en'], 'ru': l['ru'],
                        'pause': l['pause'], 'pace': l['pace'], 't': round(en_st[k], 3), 'end': round(en_en[k], 3),
                        'found_en': k in first, 'match': round(score[k], 2), 'pause_rec': pause_rec[k], 'pace_rec': pace_rec[k],
                        'ru_src': None, 'found_ru': False})
json.dump(tl, open(os.path.join(OUT, 'timeline.json'), 'w'), ensure_ascii=False, indent=1)
json.dump(cache, open(CACHE, 'w'), ensure_ascii=False)

with open(os.path.join(OUT, 'lines_table.txt'), 'w') as f:
    f.write(f'# {len(LINES)} lines, {len(found)} located, recording {DUR:.1f} s; t/end = line start/end (s), gap = silence '
            f'to the next line, pace = speaking rate vs the median, match = share of script words heard\n')
    f.write('#   i       t     end   dur   gap  pace who fx       tag             match  text\n')
    for d in tl['lines']:
        f.write('%5d %7.2f %7.2f %5.2f %5.2f %5.2f  %-2s %-8s %-15s %5.2f  %s\n' % (d['i'], d['t'], d['end'], d['end'] - d['t'],
                d['pause_rec'], d['pace_rec'], d['who'], d['fx'] or '-', d['tag'] or '-', d['match'], d['en']))

if '--write-pauses' in sys.argv:            # rewrite each L(...) row of lines.py with the measured pause and pace nudges
    src = os.path.join(ROOT, 'script', 'lines.py'); txt = open(src).read().split('\n'); k = 0
    for li, row in enumerate(txt):
        if not re.match(r"\s*L\('\w', ", row): continue
        l = LINES[k]; pc = round(pace_rec[k] * 20) / 20
        kw = ''.join([", fx=%r" % l['fx'] if l['fx'] else '',
                      ", pace=%.2f" % pc if len(l['en']) >= 18 and abs(pace_rec[k] - 1) >= 0.2 else '',
                      ", tag=%r" % l['tag'] if l['tag'] else ''])
        q = lambda x: '"%s"' % x.replace('\\', '\\\\').replace('"', '\\"') if x else "''"
        txt[li] = "%sL('%s', %s, %s, %.2f%s)," % (re.match(r'\s*', row).group(0), l['who'], q(l['en']), q(l['ru']), pause_rec[k], kw)
        k += 1
    assert k == len(LINES), (k, len(LINES))
    open(src, 'w').write('\n'.join(txt)); print(f'lines.py: pause/pace rewritten from the recording for {k} lines')

weak = [d for d in tl['lines'] if d['match'] < 0.8]
print(f'English only: {len(found)}/{len(LINES)} lines located; {len(weak)} lines under 80 % word match; '
      f'{len(order_bad)} starts out of order')
for r, heard in gapfill: print('   gap-filled %3d %6.2f  %-40s heard: %s' % (r, en_st[r], LINES[r]['en'], heard))
for r, a, b in energyfill: print('   energy-filled %3d %6.2f-%6.2f  %s (not heard: placed on the sound between its neighbours)'
                                % (r, a, b, LINES[r]['en']))
for r, pre, post in stretched: print('   stretched %3d %6.2f  %-40s took: [%s] ... [%s]' % (r, en_st[r], LINES[r]['en'], pre, post))
for d in weak: print('   weak %3d %.2f %6.2f  %s' % (d['i'], d['match'], d['t'], d['en']))
missing = [k for k in range(len(LINES)) if k not in first]
if missing: print('NOT FOUND:', missing)
