"""Motion / pacing measurements of the reference videos.

Usage: python3 measure_motion.py <va_dir> <name> <out_json>
Reads <va_dir>/<name>/small6.rgb (320x180 rgb24 at 6 fps).
Per frame pair: Farneback flow, fitted global model (tx, ty, zoom) by least squares,
residual (subject) motion, plus luma / saturation / red share and a histogram cut score.
"""
import sys, json
import numpy as np, cv2

va, name, out = sys.argv[1], sys.argv[2], sys.argv[3]
W, H, FPS = 320, 180, 6.0
raw = np.fromfile(f"{va}/{name}/small6.rgb", np.uint8)
fr = raw.reshape(-1, H, W, 3)
n = len(fr)
ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
xc, yc = xs - W / 2, ys - H / 2
rows = []
prevg = None
prevh = None
for i in range(n):
    rgb = fr[i]
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    h = cv2.calcHist([hsv], [0, 1], None, [16, 8], [0, 180, 0, 256]).ravel()
    h /= h.sum() + 1e-9
    r, gg, b = [rgb[..., k].astype(np.int16) for k in range(3)]
    red = ((r > 90) & (r > gg + 40) & (r > b + 40)).mean()
    blue = ((b > 90) & (b > r + 40)).mean()
    row = dict(t=i / FPS, luma=float(g.mean()), sat=float(hsv[..., 1].mean()), red=float(red), blue=float(blue))
    if prevg is not None:
        f = cv2.calcOpticalFlowFarneback(prevg, g, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        u, v = f[..., 0], f[..., 1]
        # mask out flat areas (flow unreliable)
        gx = cv2.Sobel(g, cv2.CV_32F, 1, 0); gy = cv2.Sobel(g, cv2.CV_32F, 0, 1)
        m = (gx * gx + gy * gy) > 400
        if m.sum() > 200:
            # model: u = tx + s*xc ; v = ty + s*yc  (s = zoom rate per frame)
            A = np.zeros((2 * m.sum(), 3), np.float32)
            A[0::2, 0] = 1; A[0::2, 2] = xc[m]
            A[1::2, 1] = 1; A[1::2, 2] = yc[m]
            bb = np.empty(2 * m.sum(), np.float32); bb[0::2] = u[m]; bb[1::2] = v[m]
            p, *_ = np.linalg.lstsq(A, bb, rcond=None)
            res = bb - A @ p
            resm = np.hypot(res[0::2], res[1::2])
            row.update(tx=float(p[0]), ty=float(p[1]), zoom=float(p[2]),
                       resid=float(np.median(resm)), resid90=float(np.percentile(resm, 90)),
                       mag=float(np.median(np.hypot(u[m], v[m]))))
        hd = 0.5 * np.abs(h - prevh).sum()
        row["hdiff"] = float(hd)
        row["gdiff"] = float(np.abs(g.astype(np.int16) - prevg).mean())
    prevg, prevh = g, h
    rows.append(row)
json.dump(rows, open(out, "w"))
print(name, n)
