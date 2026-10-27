import sys, json, re, numpy as np, soundfile as sf, librosa, sherpa_onnx, warnings
warnings.filterwarnings('ignore')
from kokoro_onnx import Kokoro
S = sys.argv[1]
k = Kokoro(f'{S}/tts/kokoro-v1.0.onnx', f'{S}/tts/voices-v1.0.bin')
print('voices:', ' '.join(v for v in k.get_voices() if v[:2] in ('am', 'bm', 'af', 'bf')))
lines = ["They don't see you. They hear you. And the store radio just told every one of them where you are.",
         "Your manager promised the night shift would be quiet. Gary has never been more right."]
M = S + '/models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8'
rec = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=M + '/encoder.int8.onnx', decoder=M + '/decoder.int8.onnx', joiner=M + '/joiner.int8.onnx', tokens=M + '/tokens.txt', num_threads=4, model_type='nemo_transducer')
def norm(t): return re.sub(r"[^a-z' ]", ' ', t.lower()).split()
def wer(ref, hyp):
    r, h = norm(ref), norm(hyp); d = np.arange(len(h) + 1)
    for i in range(1, len(r) + 1):
        prev, d[0] = d.copy(), i
        for j in range(1, len(h) + 1): d[j] = min(prev[j] + 1, d[j - 1] + 1, prev[j - 1] + (r[i - 1] != h[j - 1]))
    return d[len(h)] / len(r)
for v in sys.argv[2:]:
    res = []
    for li, text in enumerate(lines):
        a, sr = k.create(text, voice=v, speed=0.95, lang='en-us' if v[0] == 'a' else 'en-gb')
        sf.write(f'{S}/tts/test_{v}_{li}.wav', a, sr)
        y = librosa.resample(a, orig_sr=sr, target_sr=16000)
        st = rec.create_stream(); st.accept_waveform(16000, y); rec.decode_stream(st)
        f0, vf, _ = librosa.pyin(y, fmin=60, fmax=400, sr=16000, frame_length=1024); f0 = f0[~np.isnan(f0)]
        res.append((len(a) / sr, wer(text, st.result.text), np.median(f0), np.std(12 * np.log2(f0 / np.median(f0)))))
    d = np.mean([r[0] for r in res[:1]])
    print(f'{v:12s} dur L1 {res[0][0]:.1f}s L2 {res[1][0]:.1f}s | WER {np.mean([r[1] for r in res]) * 100:.0f}% | F0 {np.mean([r[2] for r in res]):.0f} Hz | pitch std {np.mean([r[3] for r in res]):.1f} st')
