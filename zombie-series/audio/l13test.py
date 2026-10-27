import sys, numpy as np, librosa, warnings, sherpa_onnx
warnings.filterwarnings('ignore')
from kokoro_onnx import Kokoro
S = sys.argv[1]
k = Kokoro(f'{S}/tts/kokoro-v1.0.onnx', f'{S}/tts/voices-v1.0.bin')
st = 0.5 * k.get_voice_style('am_puck') + 0.5 * k.get_voice_style('am_michael')
M = S + '/models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8'
rec = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=M + '/encoder.int8.onnx', decoder=M + '/decoder.int8.onnx', joiner=M + '/joiner.int8.onnx', tokens=M + '/tokens.txt', num_threads=4, model_type='nemo_transducer')
for text in ['Nobody here set it.', 'Nobody in here set it.', 'Nobody here set that alarm.', 'Nobody here set an alarm.', 'And nobody here set it.']:
    for sp in (0.84, 0.9):
        a, sr = k.create(text, voice=st, speed=sp, lang='en-us')
        y = librosa.resample(a, orig_sr=sr, target_sr=16000); s = rec.create_stream(); s.accept_waveform(16000, y); rec.decode_stream(s)
        print(f'{sp} {text:32s} -> {s.result.text}')
