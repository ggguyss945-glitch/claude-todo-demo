# Word-timed transcript of a reference short with the local Parakeet model (sherpa-onnx), split on pauses by Silero VAD.
# usage: python3 -I transcribe.py <audio_16k.wav> <out_prefix>   ->  <out>.json (words with times) and <out>.txt (lines with times)
import sys, json, numpy as np, soundfile as sf, sherpa_onnx

M = '/tmp/claude-0/-home-user-claude-todo-demo/353ac1d9-152b-55bb-bdf1-0625e0fc6a83/scratchpad/models'
P = f'{M}/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8'
wav, out = sys.argv[1], sys.argv[2]
x, sr = sf.read(wav, dtype='float32')
assert sr == 16000

rec = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f'{P}/encoder.int8.onnx', decoder=f'{P}/decoder.int8.onnx', joiner=f'{P}/joiner.int8.onnx',
                                                    tokens=f'{P}/tokens.txt', num_threads=4, model_type='nemo_transducer')
cfg = sherpa_onnx.VadModelConfig()
cfg.silero_vad.model = f'{M}/silero_vad.onnx'
cfg.silero_vad.min_silence_duration = 0.25
cfg.silero_vad.min_speech_duration = 0.15
cfg.silero_vad.max_speech_duration = 18
cfg.silero_vad.threshold = 0.4
cfg.sample_rate = 16000
vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=200)
win = cfg.silero_vad.window_size
segs = []
for i in range(0, len(x), win):
    vad.accept_waveform(x[i:i + win])
    while not vad.empty():
        segs.append((vad.front.start, np.array(vad.front.samples, dtype='float32'))); vad.pop()
vad.flush()
while not vad.empty():
    segs.append((vad.front.start, np.array(vad.front.samples, dtype='float32'))); vad.pop()

words, lines = [], []
for start, s in segs:
    pad = np.zeros(int(0.2 * sr), dtype='float32')
    st = rec.create_stream(); st.accept_waveform(sr, np.concatenate([pad, s, pad])); rec.decode_stream(st)
    r = st.result; t0 = start / sr - 0.2
    toks, ts = r.tokens, r.timestamps
    cur = None
    for tok, tt in zip(toks, ts):
        if tok.startswith(' ') or cur is None:
            if cur: words.append(cur)
            cur = {'w': tok.strip(), 't': round(t0 + tt, 2)}
        else:
            cur['w'] += tok
    if cur: words.append(cur)
    if r.text.strip(): lines.append({'t0': round(start / sr, 2), 't1': round((start + len(s)) / sr, 2), 'text': r.text.strip()})

json.dump({'words': words, 'lines': lines}, open(out + '.json', 'w'), indent=1)
with open(out + '.txt', 'w') as f:
    for l in lines: f.write(f"[{l['t0']:6.2f}-{l['t1']:6.2f}] {l['text']}\n")
print(out, len(words), 'words', len(lines), 'segments')
