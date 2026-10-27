# Can the final mix be understood? Run ASR over the master and compare with the script.
import sys, json, re, numpy as np, soundfile as sf, librosa, sherpa_onnx, warnings
warnings.filterwarnings('ignore')
S, A, TL = sys.argv[1:4]
T = json.load(open(TL)); y, sr = sf.read(f'{A}/mix.wav'); y = librosa.resample(y.mean(1).astype(np.float32), orig_sr=sr, target_sr=16000)
M = S + '/models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8'
rec = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=M + '/encoder.int8.onnx', decoder=M + '/decoder.int8.onnx', joiner=M + '/joiner.int8.onnx', tokens=M + '/tokens.txt', num_threads=4, model_type='nemo_transducer')
def hear(a, b):
    s = rec.create_stream(); s.accept_waveform(16000, y[int(a * 16000):int(b * 16000)]); rec.decode_stream(s); return s.result.text
print('PA   ', hear(T['events']['pa_start'] - 0.2, T['events']['pa_cut'] + 0.3))
for L in T['voice']['lines']:
    print(f"{L['id']:4s} ", hear(L['start'] - 0.1, L['start'] + L['dur'] + 0.1))
