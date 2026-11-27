"""Burned-in caption timing: decode the caption band (y 418-440 of 480) at 15 fps, binarize white text,
split into caption segments where the text mask changes. Usage: python3 -I captions.py <ref_dir> <name>
Prints captions per minute, duration percentiles, on-screen share, width percentiles, gap between captions.
Writes <ref_dir>/data/captions_<name>.json."""
import sys, json, subprocess, numpy as np
ref, name = sys.argv[1], sys.argv[2]
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{ref}/{name}.mp4", "-an", "-vf", "fps=15,crop=854:22:0:418,format=gray",
                      "-f", "rawvideo", "-"], capture_output=True).stdout
b = np.frombuffer(raw, np.uint8).reshape(-1, 22, 854)
m = b > 215
cnt = m.reshape(len(m), -1).sum(1)
has = cnt > 40
segs = []; cur = None
for i in range(len(m)):
    if not has[i]:
        if cur: segs.append(cur); cur = None
        continue
    if cur is None: cur = [i, i, m[i]]; continue
    a = cur[2]; inter = (a & m[i]).sum(); uni = (a | m[i]).sum()
    if inter / max(uni, 1) < 0.5: segs.append(cur); cur = [i, i, m[i]]
    else: cur[1] = i
if cur: segs.append(cur)
dur = len(m) / 15
S = []
for a, e, mk in segs:
    cols = np.where(mk.any(0))[0]
    if e - a < 2: continue
    S.append({"t": round(a / 15, 2), "dur": round((e - a + 1) / 15, 2), "w": round((cols[-1] - cols[0]) / 854, 3)})
d = np.array([s["dur"] for s in S]); w = np.array([s["w"] for s in S])
gaps = np.array([S[i + 1]["t"] - (S[i]["t"] + S[i]["dur"]) for i in range(len(S) - 1)])
print(name, "captions", len(S), "per min %.1f" % (len(S) / dur * 60), "on-screen share %.2f" % has.mean(),
      "| dur p10/50/90", np.round(np.percentile(d, [10, 50, 90]), 2), "| width p10/50/90", np.round(np.percentile(w, [10, 50, 90]), 2),
      "| gaps >0.2s: %d, median gap %.2f" % ((gaps > 0.2).sum(), np.median(gaps[gaps > 0.2]) if (gaps > 0.2).any() else 0))
json.dump(S, open(f"{ref}/data/captions_{name}.json", "w"))
