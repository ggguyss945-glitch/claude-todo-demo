"""Intensity curves: bed loudness over the whole video and aligned on rule cards.

Usage: python3 -I curves.py <data_dir> <name> <out.png>
Prints the median bed momentary (0.4 s) LU rel voice integrated around rule-card appear times (-8..+6 s, 0.5 s steps)
and draws a chart: bed short-term (3 s) LU rel voice (blue), voice 3 s (grey), mean luma (yellow), rule cards (red lines).
"""
import sys, os, json, numpy as np, soundfile as sf, pyloudnorm as pyln, cv2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from measure import kweight, momentary, HOP
d, name, out = sys.argv[1:4]
bed, sr = sf.read(f"{d}/{name}/bed.wav", dtype="float32", always_2d=True)
voice, _ = sf.read(f"{d}/{name}/voice.wav", dtype="float32", always_2d=True)
Iv = pyln.Meter(sr).integrated_loudness(voice)
bk = kweight(bed, sr); vk = kweight(voice, sr)
bm = momentary(bk, sr, 0.4) - Iv; bst = momentary(bk, sr, 3.0) - Iv; vst = momentary(vk, sr, 3.0) - Iv
UI = json.load(open(f"{d}/ui_timing.json"))
cards = [c["card"]["appear"] for c in UI["cards"] if c["label"].startswith(name)]
offs = np.arange(-8, 6.01, 0.5)
M = np.array([[bm[min(len(bm) - 1, int((c + o) / HOP))] for o in offs] for c in cards])
print(name, "bed LU rel voice around rule cards (median of", len(cards), "):")
print("  ", " ".join(f"{o:+.1f}:{v:.0f}" for o, v in zip(offs, np.median(M, 0))))
dur = len(bed) / sr; W, H = 1600, 360
img = np.full((H, W, 3), 255, np.uint8)
def y(v, lo=-40, hi=5): return int(H - 20 - (np.clip(v, lo, hi) - lo) / (hi - lo) * (H - 40))
for lv in (-30, -20, -10, 0):
    cv2.line(img, (0, y(lv)), (W, y(lv)), (220, 220, 220), 1); cv2.putText(img, f"{lv} LU", (2, y(lv) - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (120, 120, 120), 1)
for c in cards:
    x = int(c / dur * W); cv2.line(img, (x, 10), (x, H - 20), (60, 60, 230), 1)
xs = (np.arange(len(bst)) * HOP / dur * W).astype(int)
step = max(1, len(bst) // W)
pts_v = np.array([[xs[i], y(vst[i])] for i in range(0, len(vst), step)], np.int32)
pts_b = np.array([[xs[i], y(bst[i])] for i in range(0, len(bst), step)], np.int32)
cv2.polylines(img, [pts_v], False, (170, 170, 170), 1, cv2.LINE_AA)
cv2.polylines(img, [pts_b], False, (200, 90, 20), 2, cv2.LINE_AA)
R = json.load(open(f"{d}/motion_{name}.json"))
lum = np.array([r["luma"] for r in R]); lum = np.convolve(lum, np.ones(30) / 30, "same")
pts_l = np.array([[int(i / 6 / dur * W), int(H - 20 - lum[i] / 255 * (H - 40))] for i in range(0, len(lum), 3)], np.int32)
cv2.polylines(img, [pts_l], False, (0, 190, 230), 1, cv2.LINE_AA)
for m in range(0, int(dur) + 1, 60):
    x = int(m / dur * W); cv2.putText(img, f"{m//60}:00", (x + 2, H - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
cv2.putText(img, f"{name}: bed 3s LU rel voice (blue), voice (grey), mean luma (yellow, 0-255), rule cards (red)", (60, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
cv2.imwrite(out, img)
