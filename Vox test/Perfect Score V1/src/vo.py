"""Narration: Kokoro-82M (sherpa-onnx), custom blended male voice, phrase by phrase.

The voice is a new style vector (a blend of two stock male styles), generated line
by line so pacing, pauses and emphasis follow the script's direction, then
assembled with natural breaths and mastered like a close-mic studio read.
"""
import json, os, sys, shutil
import numpy as np, soundfile as sf, sherpa_onnx
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODEL = sys.argv[1]           # kokoro-multi-lang-v1_0 dir
OUT = sys.argv[2]             # output dir
BLEND = {"am_liam": 0.62, "am_fenrir": 0.38}
NAMES = ("af_alloy af_aoede af_bella af_heart af_jessica af_kore af_nicole af_nova af_river af_sarah af_sky "
         "am_adam am_echo am_eric am_fenrir am_liam am_michael am_onyx am_puck am_santa").split()
SLOT = NAMES.index("am_santa")  # overwritten in a private copy of the voice table

def make_voice_table():
    dst = os.path.join(OUT, "voices_blend.bin")
    v = np.fromfile(os.path.join(MODEL, "voices.bin"), dtype=np.float32).reshape(54, 510, 256)
    mix = sum(w * v[NAMES.index(n)] for n, w in BLEND.items())
    v[SLOT] = mix
    v.tofile(dst)
    return dst

def breath(sr, dur=0.28, level=0.012, seed=0):
    """Soft inhale: band-passed noise with a rounded envelope."""
    rng = np.random.default_rng(seed)
    n = int(sr * dur)
    x = rng.standard_normal(n)
    b, a = signal.butter(2, [900 / (sr / 2), 3800 / (sr / 2)], "band")
    x = signal.lfilter(b, a, x)
    env = np.sin(np.linspace(0, np.pi, n)) ** 1.6
    return x / np.abs(x).max() * env * level

def main():
    os.makedirs(OUT, exist_ok=True)
    table = make_voice_table()
    d = MODEL + "/"
    tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
        kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(model=d + "model.onnx", voices=table, tokens=d + "tokens.txt",
                                                       data_dir=d + "espeak-ng-data", dict_dir=d + "dict",
                                                       lexicon=d + "lexicon-us-en.txt," + d + "lexicon-zh.txt"),
        num_threads=4, provider="cpu")))
    sr = tts.sample_rate
    script = json.load(open(os.path.join(ROOT, "script", "script.json")))
    parts, lines, t = [np.zeros(int(sr * 0.05))], [], 0.05
    k = 0
    for beat in script["beats"]:
        for ln in beat["lines"]:
            a = tts.generate(ln["t"], sid=SLOT, speed=ln.get("speed", 1.0) * GLOBAL_SPEED)
            y = np.array(a.samples, dtype=np.float64)
            # trim model's own leading/trailing silence
            thr = np.abs(y).max() * 0.02
            idx = np.where(np.abs(y) > thr)[0]
            y = y[max(0, idx[0] - int(0.01 * sr)): idx[-1] + int(0.04 * sr)]
            lines.append({"beat": beat["beat"], "text": ln["t"], "start": round(t, 3), "end": round(t + len(y) / sr, 3)})
            parts.append(y); t += len(y) / sr
            gap = ln.get("pause", 0.25) * PAUSE_SCALE
            g = np.zeros(int(sr * gap))
            if 0.38 <= gap < 1.5:  # breathe before the next sentence on longer pauses
                br = breath(sr, dur=min(0.3, gap * 0.6), seed=k)
                g[len(g) - len(br) - int(0.04 * sr): len(g) - int(0.04 * sr)] += br
            parts.append(g); t += gap; k += 1
    y = np.concatenate(parts)
    sf.write(os.path.join(OUT, "vo_raw.wav"), y.astype(np.float32), sr)
    json.dump(lines, open(os.path.join(OUT, "vo_lines.json"), "w"), indent=1)
    print("duration", round(len(y) / sr, 2), "sr", sr, "lines", len(lines))

GLOBAL_SPEED = float(os.environ.get("VO_SPEED", "1.12"))
PAUSE_SCALE = float(os.environ.get("VO_PAUSE", "0.85"))
if __name__ == "__main__":
    main()
