"""tools/view_try.py OUT.jpg SHOT_ID T set/view[/var] [set/view ...] [--size 640x360]: render a shot's moment with its set swapped
for other views (review fix round 2: picking set-ups for new continuous moves)."""
import sys, os, json, argparse
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
ap = argparse.ArgumentParser()
ap.add_argument('out'); ap.add_argument('sid'); ap.add_argument('t', type=float); ap.add_argument('views', nargs='+')
ap.add_argument('--size', default='640x360'); ap.add_argument('--nochars', action='store_true')
a = ap.parse_args()
from engine.core import set_render_size
W, H = (int(v) for v in a.size.split('x')); set_render_size(W, H)
import numpy as np, cv2
import film as FM
F = FM.Film()
k = F.index[a.sid]; base = F.shots[k]
tiles = []
for v in a.views:
    p = v.split('/')
    sh = json.loads(json.dumps(base)); sh['set'], sh['view'] = p[0], p[1]
    if len(p) > 2: sh['var'] = p[2]
    sh.pop('cam3', None)
    if a.nochars: sh['chars'] = []
    sh['cam'] = dict(move='push', keys=[[sh['t0'], 960, 540, 1.0, 0.0], [sh['t1'], 960, 540, 1.0, 0.0]], ease='lin')
    F.shots[k] = sh
    F._built.clear()
    img = F._render(k, a.t, int(a.t * 60), hud=False)
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    cv2.putText(bgr, v, (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (80, 255, 255), 1, cv2.LINE_AA)
    tiles.append(bgr)
F.shots[k] = base
cols = min(3, len(tiles)); rows = (len(tiles) + cols - 1) // cols
sheet = np.zeros((rows * H, cols * W, 3), np.uint8)
for j, im in enumerate(tiles): sheet[(j // cols) * H:(j // cols + 1) * H, (j % cols) * W:(j % cols + 1) * W] = im
cv2.imwrite(a.out, sheet); print(a.out)
