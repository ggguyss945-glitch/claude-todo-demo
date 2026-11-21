"""Bed loudness and transients around picture events (rule cards, tags, red X, flashes, punch-ins).

Usage: python3 -I audio_at_events.py <data_dir> <name>
Uses <name>/bed.wav, <name>/voice.wav, ui_timing.json, tags/X lists given below, cuts30_<name>.json, punch_<name>.json.
For each event: bed momentary (0.4 s) LU rel voice integrated, mean over [-1.5,-0.3] s before vs peak in [-0.05,+0.4] s,
and whether a >=8 dB transient (50 ms window vs 1 s median before) starts within -0.1..+0.15 s.
"""
import sys, os, json, numpy as np, soundfile as sf, pyloudnorm as pyln
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from measure import kweight, momentary, HOP

d, name = sys.argv[1], sys.argv[2]
bed, sr = sf.read(f"{d}/{name}/bed.wav", dtype="float32", always_2d=True)
voice, _ = sf.read(f"{d}/{name}/voice.wav", dtype="float32", always_2d=True)
Iv = pyln.Meter(sr).integrated_loudness(voice)
bk = kweight(bed, sr); bm = momentary(bk, sr, 0.4); bf = momentary(bk, sr, 0.05)
UI = json.load(open(f"{d}/ui_timing.json"))
ev = {"rule_card": [c["card"]["appear"] for c in UI["cards"] if c["label"].startswith(name)],
      "rule_title_red": [c["red"]["appear"] for c in UI["cards"] if c["label"].startswith(name) and c["red"]],
      "tag": [t["appear"] for t in UI["tags"] if t["label"].startswith(name)]}
X = {"diver": [276.5, 348.3, 463.8, 494.8, 536.3, 538.0], "hazmat": [9.8, 15.5, 85.8, 149.8]}
ev["red_x"] = X[name]
C = json.load(open(f"{d}/cuts30_{name}.json"))
ev["flash"] = [f["t"] for f in C["flashes"]]
ev["punch_in"] = [p["t"] for p in json.load(open(f"{d}/punch_{name}.json")) if p["kind"] == "punch-in"]
rng = np.random.default_rng(1)
ev["random_cut(baseline)"] = list(rng.choice([c["t"] for c in C["cuts"]], 40, replace=False))
def at(t):
    i = int(t / HOP)
    pre = float(np.mean(bm[max(0, i - 75):max(1, i - 15)])) - Iv
    pk = float(np.max(bm[max(0, i - 2):i + 20])) - Iv
    base = np.median(bf[max(0, i - 50):max(1, i - 5)])
    tr = bool(np.max(bf[max(0, i - 5):i + 8]) - base >= 8)
    return pre, pk, tr
out = {}
for k, ts in ev.items():
    if not ts: continue
    r = np.array([at(t) for t in ts], float)
    out[k] = {"n": len(ts), "bed_before_LU": round(float(np.median(r[:, 0])), 1), "bed_peak_after_LU": round(float(np.median(r[:, 1])), 1),
              "jump_median_dB": round(float(np.median(r[:, 1] - r[:, 0])), 1), "with_transient_share": round(float(r[:, 2].mean()), 2)}
    print(name, k, out[k])
json.dump(out, open(f"{d}/audio_events_{name}.json", "w"), indent=1)
