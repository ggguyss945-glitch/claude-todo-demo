"""Robust cut detection: structural (edge-map NCC) change + hist change. Args: va_dir. Writes cuts2_<name>.txt, prints shot stats."""
import sys, numpy as np, cv2, json
va = sys.argv[1]
def emap(f):
    g = cv2.cvtColor(cv2.resize(f, (160, 90), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY).astype(np.float32)
    g = cv2.GaussianBlur(g, (0, 0), 1.0)
    e = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
    e = e - e.mean(); return e / (np.linalg.norm(e) + 1e-6)
for name in ['fire', 'hotel', 'class']:
    fr = np.fromfile(f'{va}/{name}/small6.rgb', np.uint8).reshape(-1, 180, 320, 3)
    E = [emap(f) for f in fr]
    R = json.load(open(f'{va}/motion_{name}.json'))
    ncc = np.array([1.0] + [float((E[i] * E[i - 1]).sum()) for i in range(1, len(E))])
    # compare i vs i-2 too, to tolerate 1-frame dissolves
    ncc2 = np.array([1.0, 1.0] + [float((E[i] * E[i - 2]).sum()) for i in range(2, len(E))])
    cut = (ncc < 0.45) | ((ncc2 < 0.3) & (ncc < 0.65))
    idx = np.where(cut)[0]; t = idx / 6.0
    merged = []
    for c in t:
        if not merged or c - merged[-1] > 0.5: merged.append(c)
    merged = np.array(merged); dur = len(fr) / 6
    sl = np.diff(np.concatenate([[0], merged, [dur]]))
    np.savetxt(f'{va}/cuts2_{name}.txt', merged, fmt='%.2f')
    print(name, 'cuts', len(merged), 'shot len p10/25/50/75/90', np.round(np.percentile(sl, [10, 25, 50, 75, 90]), 2), 'mean %.2f' % sl.mean(),
          '| per-minute by tenth:', [int(((merged >= a) & (merged < a + dur / 10)).sum() * 600 / dur) for a in np.arange(10) * dur / 10])
