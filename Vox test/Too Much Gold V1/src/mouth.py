"""Mouth-flap curves for the characters who speak (everyone but the narrator), from the voice track.

    mouth.py <vo_raw.wav> <vo_lines.json> <out mouth.json>
Writes {who: [{t0, t1, fps, v:[0..1 per frame]}]}: loudness per 1/30 s, smoothed, with the
syllable peaks kept so the mouth opens and closes on the words.
"""
import json, sys, numpy as np, soundfile as sf
from scipy import signal
wav, lines_p, out = sys.argv[1:4]
y, sr = sf.read(wav)
lines = json.load(open(lines_p))
res = {}
for ln in lines:
    if ln["who"] == "narrator":
        continue
    a, b = int(ln["start"] * sr), int(ln["end"] * sr)
    seg = y[a:b]
    hop = sr // 30
    rms = np.array([np.sqrt(np.mean(seg[i:i + hop] ** 2)) for i in range(0, len(seg) - hop, hop)])
    rms = signal.savgol_filter(rms, 5, 2) if len(rms) > 6 else rms
    v = np.clip(rms / (np.percentile(rms, 92) + 1e-9), 0, 1) ** 0.8
    v[v < 0.12] = 0
    res.setdefault(ln["who"], []).append({"t0": ln["start"], "t1": ln["end"], "fps": 30, "v": [round(float(x), 2) for x in v]})
json.dump(res, open(out, "w"))
print({k: len(v) for k, v in res.items()})
