"""Bench: per-frame set cost at 2560x1440 (sets only, grade + post, no cast/HUD): first frame (cache bake) and warm frames."""
import sys, os, json, time
F = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, F); os.chdir(F)
from engine import set_render_size
from engine.camera import Cam
from engine import scene
set_render_size(2560, 1440)
import sets
D = json.load(open('plan/shots.json')); S = {s['id']: s for s in D['shots']}
ids = sys.argv[1:]
if ids and ids[0] == '--combos':
    seen = set(); ids = []
    for s in D['shots']:
        k = (s['set'], s['view'], s['var'])
        if k not in seen: seen.add(k); ids.append(s['id'])
res = []
for sid in ids:
    s = S[sid]
    sp = sets.build_shot(s)
    cam = Cam([tuple(x) for x in s['cam']['keys']], ease=s['cam'].get('ease', 'lin'), shake=s['cam'].get('shake', 2))
    n = 6; ts = [s['t0'] + (s['t1'] - s['t0']) * (i + 0.5) / n for i in range(n)]
    tt = []
    for i, t in enumerate(ts):
        a = time.perf_counter()
        scene.render_frame(list(sp), cam.at(t), t, int(t * 60), **sp.render_kw(), post=sp.fx(t))
        tt.append(time.perf_counter() - a)
    warm = sorted(tt[1:])
    res.append((sid, s['set'] + '/' + s['view'] + '/' + s['var'], tt[0], warm[len(warm) // 2], warm[-1]))
    print('%s %-40s first %.2fs  warm median %.3fs  max %.3fs' % res[-1], flush=True)
res.sort(key=lambda r: -r[3])
print('HEAVIEST:', ['%s %.3f' % (r[1], r[3]) for r in res[:8]])
