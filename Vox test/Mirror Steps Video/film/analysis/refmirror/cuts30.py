"""Cut and transition detection on 30 fps 160x90 gray frames.

Usage: python3 -I cuts30.py <data_dir> <name>
Reads <data_dir>/<name>/gray30.raw. Writes <data_dir>/cuts30_<name>.json:
  {"cuts": [{"t": s, "kind": "hard|soft|flash"}], "per_frame": {...summary arrays...}}
Hard cut: edge-map NCC between consecutive frames drops (< 0.55) and is a local dip.
Soft (dissolve / fast wipe): consecutive NCC stays high but NCC over 8 frames < 0.35 with a
monotonic structural change. Flash: mean luma jumps >= 40 levels for <= 8 frames and returns.
The caption band (bottom 14 %) is masked so burned-in subtitle changes do not count as cuts.
"""
import sys, json
import numpy as np, cv2

d, name = sys.argv[1], sys.argv[2]
W, H = 160, 90
fr = np.fromfile(f"{d}/{name}/gray30.raw", np.uint8).reshape(-1, H, W)
fr = fr[:, : int(H * 0.86)]  # drop caption band
n = len(fr)

def emap(g):
    g = cv2.GaussianBlur(g.astype(np.float32), (0, 0), 1.0)
    e = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
    e = e - e.mean(); return e / (np.linalg.norm(e) + 1e-6)

E = np.stack([emap(f) for f in fr]).reshape(n, -1)
luma = fr.reshape(n, -1).mean(1)
hist = np.stack([np.bincount((f >> 4).ravel(), minlength=16) / f.size for f in fr])
ncc1 = np.r_[1.0, (E[1:] * E[:-1]).sum(1)]
ncc8 = np.r_[np.ones(8), (E[8:] * E[:-8]).sum(1)]
hd1 = np.r_[0.0, 0.5 * np.abs(hist[1:] - hist[:-1]).sum(1)]
cuts = []
# hard cuts
for i in range(1, n):
    lo = max(1, i - 3); hi = min(n, i + 4)
    nb = np.r_[ncc1[lo:i], ncc1[i + 1:hi]]
    if ncc1[i] < 0.55 and (len(nb) == 0 or ncc1[i] < nb.min() - 0.15 or ncc1[i] < 0.3):
        # skip near-black frames where edges are meaningless unless luma/hist jumps
        if luma[i] < 4 and luma[i - 1] < 4: continue
        cuts.append([i / 30.0, "hard", float(ncc1[i]), float(hd1[i])])
# flashes (white or bright frames that return)
fl = []
for i in range(1, n - 9):
    if luma[i] - luma[i - 1] >= 40:
        back = np.where(luma[i + 1:i + 9] < luma[i - 1] + 25)[0]
        if len(back): fl.append([i / 30.0, "flash", float(luma[i] - luma[i - 1]), int(back[0] + 1)])
# soft transitions: long-range change without any hard cut nearby
hard_t = np.array([c[0] for c in cuts])
soft = []
i = 8
while i < n:
    if ncc8[i] < 0.35 and ncc1[i - 7:i + 1].min() > 0.6:
        t = (i - 4) / 30.0
        if len(hard_t) == 0 or np.min(np.abs(hard_t - t)) > 0.6:
            soft.append([t, "soft", float(ncc8[i]), 0.0]); i += 15; continue
    i += 1
allc = sorted(cuts + soft, key=lambda c: c[0])
merged = []
for c in allc:
    if merged and c[0] - merged[-1][0] < 0.25: continue
    merged.append(c)
dur = n / 30.0
t = np.array([c[0] for c in merged])
sl = np.diff(np.r_[0, t, dur])
out = {"name": name, "duration": dur, "n_frames": n,
       "cuts": [{"t": round(c[0], 3), "kind": c[1], "score": round(c[2], 3)} for c in merged],
       "flashes": [{"t": round(f[0], 3), "jump": round(f[2], 1), "frames": f[3]} for f in fl],
       "luma30": [round(float(v), 1) for v in luma],
       "ncc1": [round(float(v), 3) for v in ncc1]}
json.dump(out, open(f"{d}/cuts30_{name}.json", "w"))
kinds = [c[1] for c in merged]
print(name, "cuts", len(merged), "hard", kinds.count("hard"), "soft", kinds.count("soft"), "flashes", len(fl),
      "| per min %.1f" % (len(merged) / dur * 60),
      "| shot len p10/25/50/75/90", np.round(np.percentile(sl, [10, 25, 50, 75, 90]), 2), "mean %.2f max %.1f" % (sl.mean(), sl.max()))
