"""tools/shot_frames.py OUT.jpg [--size 640x360] [--n 4] ID|T0-T1 ...: n frames across each shot (or time span), one row each,
labelled with the time (checks of continuous moves: the start, the middle and the end of a merged or travelling shot)."""
import sys, os, json, time, argparse
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
ap = argparse.ArgumentParser()
ap.add_argument('out'); ap.add_argument('items', nargs='+'); ap.add_argument('--size', default='640x360'); ap.add_argument('--n', type=int, default=4)
a = ap.parse_args()
from engine.core import set_render_size
W, H = (int(v) for v in a.size.split('x'))
set_render_size(W, H)
import numpy as np, cv2
import film as FM
F = FM.Film()
rows = []
for it in a.items:
    if '-' in it and not it.startswith('S'):
        t0, t1 = (float(v) for v in it.split('-')); lab = it
    else:
        sh = F.shots[F.index[it]]; t0, t1 = sh['t0'], sh['t1']; lab = '%s %s/%s' % (it, sh['set'], sh['view'])
    ts = [t0 + 0.03 + (t1 - t0 - 0.06) * j / max(1, a.n - 1) for j in range(a.n)]
    row = []
    for t in ts:
        c = time.perf_counter()
        try:
            img = F.frame(t)
        except Exception as e:
            import traceback; traceback.print_exc(); img = np.zeros((H, W, 3), np.uint8)
        bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        cv2.putText(bgr, '%s %.2f' % (lab, t), (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(bgr, '%s %.2f' % (lab, t), (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (80, 255, 255), 1, cv2.LINE_AA)
        row.append(bgr)
        print('%s %.2f %.2fs' % (lab, t, time.perf_counter() - c), flush=True)
    rows.append(np.hstack(row))
    while len(F._built) > 2: F._built.popitem(last=False)
cv2.imwrite(a.out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
print(a.out)
