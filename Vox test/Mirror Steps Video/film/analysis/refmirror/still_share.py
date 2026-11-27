"""How often is the picture (caption band excluded) completely still? 30 fps 160x90 gray.

Usage: python3 -I still_share.py <data_dir> <name> [...]
frame energy = mean |f[i] - f[i-1]| (levels). 'frozen' = mean |f[i] - f[i-15]| < 0.25 levels (nothing moved over 0.5 s; cut-adjacent frames excluded).
Prints frozen share, frozen runs >= 0.5 s, and per-shot median energy percentiles.
"""
import sys, json, numpy as np
d = sys.argv[1]
for name in sys.argv[2:]:
    fr = np.fromfile(f"{d}/{name}/gray30.raw", np.uint8).reshape(-1, 90, 160)[:, :77].astype(np.int16)
    e = np.r_[0, np.abs(np.diff(fr, axis=0)).mean((1, 2))]
    C = json.load(open(f"{d}/cuts30_{name}.json")); cuts = np.array([c["t"] for c in C["cuts"]])
    cf = (cuts * 30).round().astype(int)
    mask = np.ones(len(e), bool)
    for c in cf: mask[max(0, c - 1):c + 2] = False
    # 0.5 s apart difference catches slow drifts that per-frame skip blocks hide
    e15 = np.r_[np.full(15, 99.0), np.abs(fr[15:] - fr[:-15]).mean((1, 2))]
    for c in cf: mask[max(0, c - 1):c + 16] = False
    fz = (e15 < 0.25) & mask
    runs = np.flatnonzero(np.diff(np.r_[0, fz.astype(int), 0])).reshape(-1, 2)
    long = [(round(a / 30, 1), round((b - a) / 30, 1)) for a, b in runs if b - a >= 15]
    edges = np.r_[0, cf, len(e)]
    shot_e = [float(np.median(e[a + 2:b - 1])) for a, b in zip(edges[:-1], edges[1:]) if b - a > 8]
    print(name, "frozen-frame share %.3f" % fz[mask].mean(), "| frozen runs>=0.5s:", len(long), "total %.1fs" % sum(l for _, l in long),
          "| per-shot median frame energy p10/50/90:", np.round(np.percentile(shot_e, [10, 50, 90]), 2),
          "| shots with median energy <0.15: %d of %d" % (sum(1 for s in shot_e if s < 0.15), len(shot_e)))
    print("   longest frozen runs:", sorted(long, key=lambda x: -x[1])[:8])
