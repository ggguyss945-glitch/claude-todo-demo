"""tools/at_times.py OUT.jpg T [T ...] [--size 640x360] [--cols 3] [--nohud]: frames of the film at exact times in a labelled grid
(review fix round 2: quick checks of staging and continuity at the moments a finding names). A token A:B:N expands to N
times from A to B."""
import sys, os, time, argparse
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
ap = argparse.ArgumentParser()
ap.add_argument('out'); ap.add_argument('times', nargs='+'); ap.add_argument('--size', default='640x360')
ap.add_argument('--cols', type=int, default=3)
a = ap.parse_args()
from engine.core import set_render_size
W, H = (int(v) for v in a.size.split('x'))
set_render_size(W, H)
import numpy as np, cv2
import film as FM
F = FM.Film()
ts = []
for tok in a.times:
    if tok.count(':') == 2:
        x, y, n = tok.split(':'); x, y, n = float(x), float(y), int(n)
        ts += [x + (y - x) * j / max(1, n - 1) for j in range(n)]
    else: ts.append(float(tok))
tiles = []
for t in ts:
    c = time.perf_counter()
    try: img = F.frame(t)
    except Exception:
        import traceback; traceback.print_exc(); img = np.zeros((H, W, 3), np.uint8)
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    sh = F.shot_at(t)
    lab = '%.3f %s %s/%s' % (t, sh['id'], sh['set'], sh['view'])
    cv2.putText(bgr, lab, (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(bgr, lab, (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (80, 255, 255), 1, cv2.LINE_AA)
    tiles.append(bgr)
    print('%s %.2fs' % (lab, time.perf_counter() - c), flush=True)
    while len(F._built) > 3: F._built.popitem(last=False)
cols = min(a.cols, len(tiles)); rows = (len(tiles) + cols - 1) // cols
sheet = np.zeros((rows * H, cols * W, 3), np.uint8)
for j, im in enumerate(tiles): sheet[(j // cols) * H:(j // cols + 1) * H, (j % cols) * W:(j % cols + 1) * W] = im
cv2.imwrite(a.out, sheet, [cv2.IMWRITE_JPEG_QUALITY, 85]); print(a.out)
