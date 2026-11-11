"""Frame-accurate (30 fps) timing of tags and rule cards.

Usage: python3 -I ui_timing_ref.py <ref_dir> <out.json>
For each window: per-frame red-text px (top 45 % of frame for tags), card coverage (white board for diver,
yellow sign for hazmat) and ink inside the card. Reports appear / 95 % / last-visible times and ink growth.
"""
import sys, json, subprocess, numpy as np, cv2
ref, out = sys.argv[1], sys.argv[2]
TAGS = [("diver", 4.5, 8.5, "RUN FAST"), ("diver", 186.5, 192.5, "DON'T WAIT / MOVE AWAY"), ("diver", 274.5, 278.5, "DON'T STOP"),
        ("diver", 348.5, 352.5, "DON'T TURN AROUND"), ("diver", 410.5, 416.5, "STOP / DON'T MOVE"), ("diver", 492.5, 496.5, "DON'T FOLLOW HIM"),
        ("hazmat", 6.0, 9.0, "ESCAPE NOW"), ("hazmat", 9.0, 12.5, "DON'T WAIT"), ("hazmat", 148.5, 152.5, "DON'T FOLLOW")]
CARDS = [("diver", 115, 125, 1), ("diver", 196, 205, 2), ("diver", 288, 298, 3), ("diver", 360, 369, 4), ("diver", 452, 461, 5),
         ("diver", 552, 561, 6), ("diver", 678, 685, 7),
         ("hazmat", 80, 89, 1), ("hazmat", 131, 140, 2), ("hazmat", 192, 200, 3), ("hazmat", 250, 259, 4), ("hazmat", 312, 321, 5),
         ("hazmat", 382, 391, 6), ("hazmat", 456, 465, 7)]

def dec(name, a, b):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a), "-to", str(b), "-i", f"{ref}/{name}.mp4", "-an",
                          "-pix_fmt", "bgr24", "-f", "rawvideo", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, 480, 854, 3)

def timing(v, a, thr=0.06):
    v = np.asarray(v, float); mx = v.max() + 1e-9; n = v / mx
    on = np.where(n > thr)[0]
    if not len(on): return None
    s = on[0]; full = s + int(np.argmax(n[s:] > 0.95)); e = on[-1]
    return {"appear": round(a + s / 30, 2), "rise_s": round((full - s) / 30, 2), "last": round(a + e / 30, 2),
            "visible_s": round((e - s + 1) / 30, 2), "curve_2f": np.round(n[s:s + 14:2], 2).tolist()}

R = {"tags": [], "cards": []}
for name, a, b, lab in TAGS:
    fr = dec(name, a, b); vals = []
    for f in fr:
        h = cv2.cvtColor(f[: int(480 * 0.6)], cv2.COLOR_BGR2HSV)
        vals.append(int((((h[..., 0] < 8) | (h[..., 0] > 168)) & (h[..., 1] > 130) & (h[..., 2] > 150)).sum()))
    t = timing(vals, a); t["label"] = name + " " + lab; R["tags"].append(t); print("TAG", t)
for name, a, b, num in CARDS:
    fr = dec(name, a, b); cov, ink, red = [], [], []
    for f in fr:
        h = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
        if name == "diver":
            card = (h[..., 2] > 200) & (h[..., 1] < 40)
        else:
            card = (h[..., 0] > 18) & (h[..., 0] < 36) & (h[..., 1] > 150) & (h[..., 2] > 150)
        cov.append(float(card[: int(480 * 0.86)].mean()))
        ys, xs = np.where(card[: int(480 * 0.86)])
        if len(xs) > 2000:
            x0, x1 = np.percentile(xs, [2, 98]).astype(int); y0, y1 = np.percentile(ys, [2, 98]).astype(int)
            box = f[y0:y1, x0:x1]; hb = h[y0:y1, x0:x1]
            rd = ((hb[..., 0] < 8) | (hb[..., 0] > 168)) & (hb[..., 1] > 100) & (hb[..., 2] > 120)
            if name == "diver":
                dk = (hb[..., 2] < 150) & (hb[..., 1] < 60)
            else:
                dk = ((hb[..., 2] < 90) | ((hb[..., 1] < 50) & (hb[..., 2] > 220)))  # black or white letters on yellow
            ink.append(int(dk.sum())); red.append(int(rd.sum()))
        else:
            ink.append(0); red.append(0)
    tc = timing(cov, a, 0.3); ti = timing(ink, a, 0.1); tr = timing(red, a, 0.1)
    ink = np.array(ink, float)
    rec = {"label": f"{name} rule {num}", "card": tc, "ink": ti, "red": tr,
           "ink_every_0.5s": np.round(ink[::15] / (ink.max() + 1e-9), 2).tolist(), "card_cov_max": round(max(cov), 3)}
    R["cards"].append(rec); print("CARD", rec)
json.dump(R, open(out, "w"), indent=1)
