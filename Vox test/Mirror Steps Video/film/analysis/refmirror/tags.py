"""Find red alert tags ("RUN FAST", "DON'T WAIT"...) at 6 fps: solid red rectangles (fill >= 0.6, aspect >= 2.2)
with bright text inside. Usage: python3 -I tags.py <data_dir> <name>. Prints events (start, duration, box x/y/w/h as
fractions of the frame) and writes <data_dir>/tags_<name>.json."""
import sys, json, numpy as np, cv2
d, name = sys.argv[1], sys.argv[2]
fr = np.fromfile(f"{d}/{name}/small6.rgb", np.uint8).reshape(-1, 180, 320, 3)
hits = []
for i, f in enumerate(fr):
    r, g, b = [f[..., k].astype(np.int16) for k in range(3)]
    m = ((r > 140) & (g < 90) & (b < 100) & (r - g > 80)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    k, lab, st, c = cv2.connectedComponentsWithStats(m)
    best = None
    for j in range(1, k):
        x, y, w, h, a = st[j]
        if w < 30 or h < 7 or y > 150: continue
        if w / h < 2.2 or a / (w * h) < 0.6: continue
        inner = f[y + 2:y + h - 2, x + 2:x + w - 2]
        txt = (inner.min(2) > 200).mean() if inner.size else 0
        if txt < 0.04: continue
        if best is None or w * h > best[2] * best[3]: best = (x, y, w, h)
    hits.append(best)
ev = []; i = 0
while i < len(hits):
    if hits[i] is None: i += 1; continue
    j = i
    while j + 1 < len(hits) and (hits[j + 1] is not None or (j + 2 < len(hits) and hits[j + 2] is not None)): j += 1
    boxes = [h for h in hits[i:j + 1] if h]
    x, y, w, h = np.median(np.array(boxes), 0)
    if j - i + 1 >= 2:
        ev.append({"t": round(i / 6, 2), "dur": round((j - i + 1) / 6, 2), "x": round(x / 320, 2), "y": round(y / 180, 2),
                   "w": round(w / 320, 2), "h": round(h / 180, 3)})
    i = j + 1
json.dump(ev, open(f"{d}/tags_{name}.json", "w"), indent=0)
print(name, len(ev), "tag events")
for e in ev: print(" ", e)
