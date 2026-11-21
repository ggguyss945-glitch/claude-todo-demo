"""Classify hard cuts as punch-ins / punch-outs (same shot, scaled) vs new shots.
Usage: python3 -I punchins.py <data_dir> <name>
For each cut, the frame 2 before is scaled by s in 1.08..2.4 around a searched centre and compared (edge NCC)
with the frame 2 after; also the reverse (punch-out). Match if NCC >= 0.6 and it beats scale 1.0 by 0.15."""
import sys, json, numpy as np, cv2
d, name = sys.argv[1], sys.argv[2]
fr = np.fromfile(f"{d}/{name}/gray30.raw", np.uint8).reshape(-1, 90, 160)[:, :77]
C = json.load(open(f"{d}/cuts30_{name}.json"))
def em(g):
    g = cv2.GaussianBlur(g.astype(np.float32), (0, 0), 1.0)
    e = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)); return e
def ncc(a, b):
    a = a - a.mean(); b = b - b.mean(); return float((a * b).sum() / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-6))
def best_scale(A, B):
    h, w = A.shape; best = (-1, 1.0, 0, 0)
    for s in (1.08, 1.15, 1.25, 1.35, 1.5, 1.7, 2.0, 2.4):
        cw, ch = w / s, h / s
        for cx in np.linspace(cw / 2, w - cw / 2, 7):
            for cy in np.linspace(ch / 2, h - ch / 2, 5):
                M = np.float32([[s, 0, w / 2 - s * cx], [0, s, h / 2 - s * cy]])
                Aw = cv2.warpAffine(A, M, (w, h), flags=cv2.INTER_LINEAR)
                v = ncc(Aw, B)
                if v > best[0]: best = (v, s, cx / w, cy / h)
    return best
out = []
for c in C["cuts"]:
    if c["kind"] != "hard": continue
    i = int(round(c["t"] * 30))
    if i < 3 or i + 3 >= len(fr): continue
    A, B = em(fr[i - 2]), em(fr[i + 2]); base = ncc(A, B)
    vi = best_scale(A, B); vo = best_scale(B, A)
    if vi[0] >= 0.6 and vi[0] > base + 0.15 and vi[0] >= vo[0]: out.append({"t": c["t"], "kind": "punch-in", "scale": vi[1], "ncc": round(vi[0], 2), "cx": round(vi[2], 2), "cy": round(vi[3], 2)})
    elif vo[0] >= 0.6 and vo[0] > base + 0.15: out.append({"t": c["t"], "kind": "punch-out", "scale": vo[1], "ncc": round(vo[0], 2)})
nh = sum(1 for c in C["cuts"] if c["kind"] == "hard")
pi = [o for o in out if o["kind"] == "punch-in"]; po = [o for o in out if o["kind"] == "punch-out"]
print(name, "hard cuts", nh, "punch-ins", len(pi), "(%.0f%%)" % (100 * len(pi) / nh), "punch-outs", len(po),
      "| punch-in scale median", np.median([o["scale"] for o in pi]) if pi else None, "per min %.1f" % (len(pi) / (C["duration"] / 60)))
print("  ", [(o["t"], o["scale"]) for o in out][:40])
json.dump(out, open(f"{d}/punch_{name}.json", "w"), indent=0)
