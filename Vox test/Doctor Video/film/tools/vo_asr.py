"""Transcribe a narration recording with Parakeet TDT (sherpa-onnx) and keep word START and END times.
    python3 vo_asr.py <in.wav> <out.json> [parakeet dir]
Like align.py's ASR (Silero VAD chunks of at most ~16 s, 0.3 s padding), but every word also carries the TDT token
durations, so a word has [text, start, end] (80 ms encoder resolution: use them as anchors, not as cut points).
A rescue pass then decodes every stretch louder than -40 dB that no VAD chunk covered (the VAD skips an isolated short
word or a quiet line: "don't" and the first "hop" of the cold open, the little girl's "Can I come home now?").
Writes {'words': [[w, t0, t1], ...], 'chunks': [[lo, hi, text], ...], 'sr_in': ..., 'duration': ...}.
"""
import json, os, re, sys
import numpy as np, soundfile as sf, soxr

MODELS = '/tmp/claude-0/-home-user-claude-todo-demo/aa250ae7-a0b4-594f-9bc6-bd18b596cf27/scratchpad/models'
IN, OUT = sys.argv[1], sys.argv[2]
PK = sys.argv[3] if len(sys.argv) > 3 else os.environ.get('PARAKEET_DIR', os.path.join(MODELS, 'sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8'))
VAD = os.path.join(os.path.dirname(PK.rstrip('/')), 'vad.onnx')

import sherpa_onnx
x, sr = sf.read(IN, dtype='float32', always_2d=True); x = x.mean(axis=1)
x16 = soxr.resample(x, sr, 16000, quality='VHQ').astype(np.float32)
DUR = len(x16) / 16000
cfg = sherpa_onnx.VadModelConfig(); cfg.silero_vad.model = VAD
cfg.silero_vad.threshold = 0.45; cfg.silero_vad.min_silence_duration = 0.25
cfg.silero_vad.min_speech_duration = 0.15; cfg.silero_vad.max_speech_duration = 14; cfg.sample_rate = 16000
vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=60)
segs = []
for i in range(0, len(x16), 512):
    vad.accept_waveform(x16[i:i + 512])
    while not vad.empty(): segs.append([vad.front.start / 16000, (vad.front.start + len(vad.front.samples)) / 16000]); vad.pop()
vad.flush()
while not vad.empty(): segs.append([vad.front.start / 16000, (vad.front.start + len(vad.front.samples)) / 16000]); vad.pop()
chunks = []
for a, b in segs:
    if chunks and a - chunks[-1][1] < 0.7 and b - chunks[-1][0] < 16: chunks[-1][1] = b
    else: chunks.append([a, b])
pk = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f'{PK}/encoder.int8.onnx', decoder=f'{PK}/decoder.int8.onnx',
                                                   joiner=f'{PK}/joiner.int8.onnx', tokens=f'{PK}/tokens.txt',
                                                   model_type='nemo_transducer', num_threads=2)
words, ctext = [], []
nw = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
for k, (a, b) in enumerate(chunks):
    lo = max(0.0, a - 0.3, chunks[k - 1][1] if k else 0.0)
    hi = min(DUR, b + 0.3, chunks[k + 1][0] if k + 1 < len(chunks) else DUR)
    seg = x16[int(lo * 16000):int(hi * 16000)]
    st = pk.create_stream(); st.accept_waveform(16000, seg); pk.decode_stream(st)
    r = st.result
    durs = list(r.durations) if len(r.durations) == len(r.tokens) else [0.08] * len(r.tokens)
    cur, cw = None, []
    for tok, ts, du in zip(r.tokens, r.timestamps, durs):
        if tok.startswith(' ') or cur is None:
            cur = [tok.strip(), round(float(ts) + lo, 3), round(float(ts) + float(du) + lo, 3)]; cw.append(cur)
        else:
            cur[0] += tok; cur[2] = round(float(ts) + float(du) + lo, 3)
    cw = [w for w in cw if w[0]]
    if cw and words and nw(cw[0][0]) == nw(words[-1][0]) and cw[0][1] - words[-1][1] < 0.45:
        cw = cw[1:]
    words += cw
    ctext.append([round(lo, 2), round(hi, 2), r.text.strip()])
    print('%7.2f %7.2f  %s' % (lo, hi, r.text.strip()), flush=True)
# rescue pass: sound the VAD skipped (an isolated short word, a quiet line between chunks) is decoded on its own
w5 = 80                                                           # 5 ms frames at 16 kHz
e = np.sqrt(np.convolve(x16 ** 2, np.ones(w5) / w5, 'same'))[::w5]
db5 = 20 * np.log10(e + 1e-9)
covered = np.zeros(len(db5), bool)
for lo, hi, _ in ctext: covered[int(lo * 200):int(hi * 200) + 1] = True
loud = (db5 > -40) & ~covered
regions, i = [], 0
while i < len(loud):
    if loud[i]:
        j = i
        while j < len(loud) and (loud[j] or (j + 30 < len(loud) and loud[j:j + 30].any())): j += 1
        if (j - i) * 0.005 >= 0.08: regions.append([i * 0.005, j * 0.005])
        i = j
    else: i += 1
rescued = []
for a, b in regions:
    lo, hi = max(0.0, a - 0.25), min(DUR, b + 0.25)
    st = pk.create_stream(); st.accept_waveform(16000, x16[int(lo * 16000):int(hi * 16000)]); pk.decode_stream(st)
    r = st.result
    durs = list(r.durations) if len(r.durations) == len(r.tokens) else [0.08] * len(r.tokens)
    cur, cw = None, []
    for tok, ts, du in zip(r.tokens, r.timestamps, durs):
        if tok.startswith(' ') or cur is None:
            cur = [tok.strip(), round(float(ts) + lo, 3), round(float(ts) + float(du) + lo, 3)]; cw.append(cur)
        else:
            cur[0] += tok; cur[2] = round(float(ts) + float(du) + lo, 3)
    cw = [w for w in cw if w[0] and a - 0.1 <= w[1] <= b + 0.05
          and not any(nw(v[0]) == nw(w[0]) and abs(v[1] - w[1]) < 0.4 for v in words)]   # the window reaches into a chunk
    if cw:
        rescued += cw; ctext.append([round(lo, 2), round(hi, 2), ' '.join(w[0] for w in cw)])
        print('rescued %7.2f %7.2f  %s' % (lo, hi, ' '.join(w[0] for w in cw)), flush=True)
words = sorted(words + rescued, key=lambda w: w[1]); ctext.sort()
json.dump({'words': words, 'chunks': ctext, 'sr_in': sr, 'duration': round(DUR, 3)}, open(OUT, 'w'), ensure_ascii=False)
print(f'{len(words)} words, {len(ctext)} chunks -> {OUT}')
