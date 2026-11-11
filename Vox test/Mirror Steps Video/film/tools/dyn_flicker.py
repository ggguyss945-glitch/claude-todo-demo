"""tools/dyn_flicker.py [--fps 30] [ids...]: flicker scan of the travelling shots (cam3). For every shot (default: all cam3 shots)
the room layers of the per-frame view (sets_v2.MOVE) are drawn alone at 480x270 every 1/fps s and compared with the frame
before: a band whose mean change jumps over 4x its running median (and over 3 levels) is reported (a plane clipped wrong,
an item lost for a frame). Prints one line per shot and the suspicious times."""
import sys, os, argparse
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
ap = argparse.ArgumentParser(); ap.add_argument('ids', nargs='*'); ap.add_argument('--fps', type=float, default=30.0)
a = ap.parse_args()
from engine.core import set_render_size, Pen, surface_for
set_render_size(480, 270)
import numpy as np
import film as FM
F = FM.Film()
ids = a.ids or [s['id'] for s in F.shots if s.get('cam3')]
BANDS = ('near', 'mid', 'far', 'wall')


def draw(l, t):
    arr = np.zeros((270, 480, 4), np.uint8); arr[..., 3] = 255
    s = surface_for(arr); cv = s.getCanvas(); cv.scale(0.25, 0.25); l.draw(Pen(cv), t); del cv, s
    return arr[..., :3].astype(np.float32)


bad_all = []
for sid in ids:
    k = F.index[sid]; sh = F.shots[k]; B = F.built(k)
    ts = np.arange(sh['t0'] + 0.02, sh['t1'] - 0.02, 1.0 / a.fps)
    prev = {}; hist = {}; bad = []
    for t in ts:
        for l in F._dyn_layers(B, float(t)):
            if l.name not in BANDS: continue
            im = draw(l, float(t))
            if l.name in prev:
                d = float(np.abs(im - prev[l.name]).mean())
                h = hist.setdefault(l.name, [])
                med = float(np.median(h[-8:])) if h else d
                if len(h) >= 2 and d > max(3.0, 4.0 * med + 0.5): bad.append((round(float(t), 3), l.name, round(d, 1), round(med, 2)))
                h.append(d)
            prev[l.name] = im
    print('%s %.2f-%.2f %s/%s: %d frames, %d suspicious %s' % (sid, sh['t0'], sh['t1'], sh['set'], sh['view'], len(ts), len(bad), bad[:6]), flush=True)
    bad_all += [(sid,) + b for b in bad]
    while len(F._built) > 2: F._built.popitem(last=False)
print('TOTAL suspicious', len(bad_all))
