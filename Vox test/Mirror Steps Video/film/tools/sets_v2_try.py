"""Quick renders of v2 set views (sets only, or --chars with the cast) at 960x540.
usage: python3 tools/sets_v2_try.py OUTDIR [--chars] [--size WxH] SPEC ...
  SPEC = shot id (S055, S055@72.8) or set/view/var@t[:k=v,k=v] (a synthetic shot at film time t with the props of the plan's
         shot nearest t, overridden by k=v)."""
import sys, os, json, time
F = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, F); os.chdir(F)
import numpy as np, cv2
from engine import set_render_size
from engine.camera import Cam
from engine.scene import render_frame, STATS
args = sys.argv[1:]
out = args.pop(0); os.makedirs(out, exist_ok=True)
chars = '--chars' in args; args = [a for a in args if a != '--chars']
size = (960, 540)
if '--size' in args:
    i = args.index('--size'); size = tuple(int(v) for v in args[i + 1].split('x')); del args[i:i + 2]
set_render_size(*size)
import sets
D = json.load(open('plan/shots.json')); SH = D['shots']; S = {s['id']: s for s in SH}


def shot_at(t):
    best = SH[0]
    for s in SH:
        if s['t0'] <= t: best = s
    return best


def synth(spec):
    sv, _, rest = spec.partition('@')
    tt, _, kv = rest.partition(':')
    st_, vw, var = sv.split('/')
    t = float(tt) if tt else 100.0
    base = shot_at(t)
    s = dict(base); s['id'] = 'X'; s['set'], s['view'], s['var'] = st_, vw, var
    s['t0'], s['t1'] = t - 0.5, t + 1.5
    s['props'] = dict(base['props']); s['props'].pop('changes_in_shot', None)
    s['chars'] = []; s['hud'] = []
    s['cam'] = {'keys': [[t - 0.5, 960, 540, 1.0, 0.0], [t + 1.5, 960, 540, 1.0, 0.0]], 'ease': 'lin'}
    s['grade'] = None; s['dof'] = None
    for p in kv.split(',') if kv else []:
        k, v = p.split('=')
        if k in ('grade',): s[k] = v
        else: s['props'][k] = v
    return s, t


for a in args:
    if '/' in a:
        s, t = synth(a)
    else:
        sid, _, tt = a.partition('@'); s = S[sid]; t = float(tt) if tt else round((s['t0'] + s['t1']) / 2, 3)
    t0 = time.perf_counter()
    sp = sets.build_shot(s)
    tb = time.perf_counter() - t0
    layers = list(sp)
    if chars and s.get('chars'):
        import characters as C
        for spec in s['chars']:
            spec = dict(spec); at = sets.resolve_at(sp, spec); spec['at'] = at
            try: rig = C.CharRig(spec, s)
            except Exception as e: print('  char fail', spec['who'], e); continue
            d = at[3] if (isinstance(at, list) and len(at) > 3 and spec.get('mode') in ('body', 'legs', 'silhouette')) else 1.0
            layers.append(sets.Layer(d, (lambda r: (lambda pen, tt: r.draw(pen, tt)))(rig), 'char_' + spec['who']))
    k = s['cam']['keys']
    cam = Cam([tuple(x) for x in k], ease=s['cam'].get('ease', 'lin'))
    t1 = time.perf_counter()
    img = render_frame(layers, cam.at(t), t, int(t * 60), **sp.render_kw(), post=sp.fx(t))
    t2 = time.perf_counter()
    img2 = render_frame(layers, cam.at(t + 1 / 60), t + 1 / 60, int(t * 60) + 1, **sp.render_kw(), post=sp.fx(t + 1 / 60))
    t3 = time.perf_counter()
    bgr = np.ascontiguousarray(img[..., ::-1])
    name = '%s__%s__%s__%s@%.2f.jpg' % (s['set'], s['view'], s['var'], s['id'], t)
    cv2.imwrite(os.path.join(out, name), bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    print('%-52s build %4.0fms first %5.0fms warm %4.0fms  luma p50 %3.0f p95 %3.0f sat %3.0f grade %s' % (
        name, tb * 1000, (t2 - t1) * 1000, (t3 - t2) * 1000, np.median(g), np.percentile(g, 95), hsv[..., 1].mean(), sp.grade), flush=True)
