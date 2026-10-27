import sys, numpy as np, soundfile as sf, librosa, warnings
warnings.filterwarnings('ignore')
from kokoro_onnx import Kokoro
S = sys.argv[1]
k = Kokoro(f'{S}/tts/kokoro-v1.0.onnx', f'{S}/tts/voices-v1.0.bin')
text = "They don't see you. They hear you. And the store radio just told every one of them where you are."
blends = {'puck': {'am_puck': 1}, 'puck60_fenrir40': {'am_puck': .6, 'am_fenrir': .4}, 'puck50_michael50': {'am_puck': .5, 'am_michael': .5},
          'fenrir50_michael50': {'am_fenrir': .5, 'am_michael': .5}, 'puck40_fenrir30_michael30': {'am_puck': .4, 'am_fenrir': .3, 'am_michael': .3}}
for name, mix in blends.items():
    style = sum(w * k.get_voice_style(v) for v, w in mix.items())
    a, sr = k.create(text, voice=style, speed=0.95, lang='en-us')
    sf.write(f'{S}/tts/blend_{name}.wav', a, sr)
    y = librosa.resample(a, orig_sr=sr, target_sr=16000)
    f0, vf, _ = librosa.pyin(y, fmin=60, fmax=400, sr=16000, frame_length=1024); f = f0[~np.isnan(f0)]
    # roughness proxy: frame-to-frame F0 jumps > 2 semitones within voiced runs
    st = 12 * np.log2(f0 / np.nanmedian(f0)); d = np.abs(np.diff(st)); jumps = np.nansum(d > 2) / np.sum(~np.isnan(d))
    flat = librosa.feature.spectral_flatness(y=y)[0]
    print(f'{name:28s} dur {len(a)/sr:.1f}s F0 {np.median(f):.0f} Hz pitch std {np.std(st[~np.isnan(st)]):.1f} st | F0 jumps {jumps*100:.1f}% | flatness p95 {np.percentile(flat,95):.3f}')
