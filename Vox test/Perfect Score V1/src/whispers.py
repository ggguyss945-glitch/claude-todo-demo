"""Hallway whispers: short phrases spoken by several stock voices, then turned into
real whispers (spectral envelope kept, harmonics removed, noise excitation).
    python3 whispers.py <kokoro dir> <outdir>"""
import os, sys, numpy as np, soundfile as sf, sherpa_onnx
from scipy import signal
MODEL, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
NAMES = ("af_alloy af_aoede af_bella af_heart af_jessica af_kore af_nicole af_nova af_river af_sarah af_sky "
         "am_adam am_echo am_eric am_fenrir am_liam am_michael am_onyx am_puck am_santa").split()
d = MODEL + "/"
tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
    kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(model=d + "model.onnx", voices=d + "voices.bin", tokens=d + "tokens.txt",
                                                   data_dir=d + "espeak-ng-data", dict_dir=d + "dict",
                                                   lexicon=d + "lexicon-us-en.txt," + d + "lexicon-zh.txt"),
    num_threads=2, provider="cpu")))
sr = tts.sample_rate
def whisperize(y, seed):
    f, t, Z = signal.stft(y, sr, nperseg=512, noverlap=384)
    mag = np.abs(Z)
    # cepstral liftering: keep the spectral envelope, drop the harmonic fine structure
    logm = np.log(mag + 1e-6)
    cep = np.fft.irfft(logm, axis=0)
    cep[30:-30] = 0
    env = np.exp(np.fft.rfft(cep, axis=0).real)[: mag.shape[0]]
    rng = np.random.default_rng(seed)
    ph = np.exp(1j * rng.uniform(0, 2 * np.pi, mag.shape))
    tilt = np.clip((f / 1500.0), 0.25, 1.6)[:, None]  # whispers lose the low end
    _, x = signal.istft(env * tilt * ph, sr, nperseg=512, noverlap=384)
    x = x[: len(y)]
    # follow the loudness of the original
    e = np.abs(signal.hilbert(y)); e = signal.filtfilt(*signal.butter(2, 30 / (sr / 2)), e)
    ex = np.abs(signal.hilbert(x)) + 1e-6; ex = signal.filtfilt(*signal.butter(2, 30 / (sr / 2)), ex)
    x = x * np.clip(e / np.maximum(ex, 1e-4), 0, 8)
    return x / (np.abs(x).max() + 1e-9) * 0.8
phrases = [("Cheater.", "af_nicole", 0.95), ("Cheater.", "am_puck", 1.0), ("Cheater...", "af_sky", 0.9), ("He cheated.", "af_bella", 1.05),
           ("No way he got a hundred.", "am_echo", 1.15), ("Cheater.", "af_river", 0.92), ("He copied it.", "af_kore", 1.1), ("Cheater.", "am_eric", 0.95),
           ("Did you hear?", "af_jessica", 1.1), ("Cheater.", "am_michael", 0.9)]
for i, (text, voice, sp) in enumerate(phrases):
    a = tts.generate(text, sid=NAMES.index(voice), speed=sp)
    y = np.array(a.samples, dtype=np.float64)
    thr = np.abs(y).max() * 0.02; idx = np.where(np.abs(y) > thr)[0]; y = y[idx[0]: idx[-1] + int(0.05 * sr)]
    w = whisperize(y, i)
    w = signal.resample_poly(w, 2, 1)  # 24k -> 48k
    sf.write(os.path.join(OUT, f"w{i:02d}.wav"), w.astype(np.float32), 48000)
    print(i, text, voice, round(len(w) / 48000, 2))
