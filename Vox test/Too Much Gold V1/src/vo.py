"""Narration and character lines: Kokoro-82M (sherpa-onnx), line by line.

    vo.py <kokoro-multi-lang-v1_0 dir> <out dir>

Each voice in script.json is a blend of stock Kokoro styles (a new synthetic voice, not a clone of anyone),
lifted by a few semitones the clean way: the line is generated slower by the same ratio and then resampled,
so pitch and formants rise together with no phase-vocoder artefacts and the pace comes out as directed.
Writes vo_raw.wav (24 kHz mono) and vo_lines.json (start/end of every line).
"""
import json, os, sys
from fractions import Fraction
import numpy as np, soundfile as sf, sherpa_onnx
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODEL, OUT = sys.argv[1], sys.argv[2]
NAMES = ("af_alloy af_aoede af_bella af_heart af_jessica af_kore af_nicole af_nova af_river af_sarah af_sky "
         "am_adam am_echo am_eric am_fenrir am_liam am_michael am_onyx am_puck am_santa").split()
GLOBAL_SPEED = float(os.environ.get("VO_SPEED", "1.10"))
GAP_SCALE = float(os.environ.get("VO_GAP", "1.0"))


def voice_table(voices):
    """Write a private voices.bin where slots 0.. hold the script's blended voices."""
    v = np.fromfile(os.path.join(MODEL, "voices.bin"), dtype=np.float32).reshape(54, 510, 256)
    slots = {}
    for i, (name, spec) in enumerate(voices.items()):
        v[i] = sum(w * v[NAMES.index(n)] for n, w in spec["blend"].items())
        slots[name] = i
    path = os.path.join(OUT, "voices_blend.bin")
    v.tofile(path)
    return path, slots


def breath(sr, dur, seed):
    rng = np.random.default_rng(seed)
    n = int(sr * dur)
    b, a = signal.butter(2, [900 / (sr / 2), 3800 / (sr / 2)], "band")
    x = signal.lfilter(b, a, rng.standard_normal(n))
    return x / np.abs(x).max() * np.sin(np.linspace(0, np.pi, n)) ** 1.6 * 0.01


def trim(y, sr):
    thr = np.abs(y).max() * 0.02
    idx = np.where(np.abs(y) > thr)[0]
    return y[max(0, idx[0] - int(0.012 * sr)): idx[-1] + int(0.05 * sr)]


def main():
    os.makedirs(OUT, exist_ok=True)
    script = json.load(open(os.path.join(ROOT, "script", "script.json")))
    table, slots = voice_table(script["voices"])
    d = MODEL + "/"
    tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
        kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(model=d + "model.onnx", voices=table, tokens=d + "tokens.txt",
                                                       data_dir=d + "espeak-ng-data", dict_dir=d + "dict",
                                                       lexicon=d + "lexicon-us-en.txt," + d + "lexicon-zh.txt"),
        num_threads=4, provider="cpu")))
    sr = tts.sample_rate
    parts, lines, t = [np.zeros(int(sr * 0.02))], [], 0.02
    for k, ln in enumerate(script["lines"]):
        spec = script["voices"][ln["who"]]
        ratio = 2 ** (spec.get("semitones", 0) / 12)
        a = tts.generate(ln["t"], sid=slots[ln["who"]], speed=ln.get("speed", 1.0) * GLOBAL_SPEED / ratio)
        y = np.array(a.samples, dtype=np.float64)
        if ratio != 1:
            fr = Fraction(1 / ratio).limit_denominator(200)
            y = signal.resample_poly(y, fr.numerator, fr.denominator)
        y = trim(y, sr)
        lines.append({"i": k, "beat": ln["beat"], "who": ln["who"], "text": ln["t"], "start": round(t, 3), "end": round(t + len(y) / sr, 3)})
        parts.append(y)
        t += len(y) / sr
        gap = ln.get("gap", 0.25) * GAP_SCALE
        g = np.zeros(int(sr * gap))
        if gap >= 0.28:  # a soft inhale before the next sentence on the longer gaps
            br = breath(sr, min(0.24, gap * 0.6), k)
            g[len(g) - len(br) - int(0.03 * sr): len(g) - int(0.03 * sr)] += br
        parts.append(g)
        t += gap
    y = np.concatenate(parts + [np.zeros(int(sr * 0.25))])
    sf.write(os.path.join(OUT, "vo_raw.wav"), y.astype(np.float32), sr)
    json.dump(lines, open(os.path.join(OUT, "vo_lines.json"), "w"), indent=1)
    words = sum(len(l["text"].split()) for l in lines)
    print("duration", round(len(y) / sr, 2), "s | words", words, "| wps", round(words / lines[-1]["end"], 2))


if __name__ == "__main__":
    main()
