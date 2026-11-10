"""Render one still per plan shot (or per set/view/var combo) for the v2 sets, measure the look (the REF_V2 lookstats
method: 640x360, caption band y > 0.86 H dropped) and make contact sheets.

usage: python3 tools/sets_v2_stills.py OUTDIR [--size WxH] [--chars] [--combos] [--ids S001,S002] [--every N]
writes OUTDIR/stills/<id>__<set>__<view>__<var>.jpg, OUTDIR/looks.json (per still: luma, p5, p50, p95, sat, colorful,
edges, red, world, t) and prints per-world and per-tenth summaries."""
import sys, os, json, time, math
F = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, F); os.chdir(F)
import numpy as np, cv2
from engine import set_render_size
from engine.camera import Cam
from engine.scene import render_frame
args = sys.argv[1:]
out = args.pop(0)
size = (640, 360)
if '--size' in args:
    i = args.index('--size'); size = tuple(int(v) for v in args[i + 1].split('x')); del args[i:i + 2]
chars = '--chars' in args
combos = '--combos' in args
ids = None
if '--ids' in args:
    i = args.index('--ids'); ids = args[i + 1].split(','); del args[i:i + 2]
every = 1
if '--every' in args:
    i = args.index('--every'); every = int(args[i + 1]); del args[i:i + 2]
set_render_size(*size)
import sets
D = json.load(open('plan/shots.json')); SH = D['shots']
os.makedirs(os.path.join(out, 'stills'), exist_ok=True)


def look(bgr):
    im = cv2.resize(bgr, (640, 360), interpolation=cv2.INTER_AREA)[:310]
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    b, gg, r = [im[..., k].astype(np.float32) for k in range(3)]
    rg = r - gg; yb = 0.5 * (r + gg) - b
    colorful = float(np.hypot(rg.std(), yb.std()) + 0.3 * np.hypot(rg.mean(), yb.mean()))
    e = cv2.Canny(im, 60, 160)
    red = float(((r > 110) & (r > gg + 50) & (r > b + 40)).mean())
    sat = hsv[..., 1]; hue = hsv[..., 0][sat > 80]
    hm = float(np.degrees(np.angle(np.mean(np.exp(1j * np.radians(hue.astype(float) * 2)))))) % 360 if len(hue) else -1
    return dict(luma=float(g.mean()), p5=float(np.percentile(g, 5)), p50=float(np.median(g)), p95=float(np.percentile(g, 95)),
                std=float(g.std()), sat=float(sat.mean()), colorful=colorful, edges=float((e > 0).mean()), red=red, hue=hm)


todo = []
seen = set()
for s in SH[::every]:
    if ids and s['id'] not in ids: continue
    k = (s['set'], s['view'], s['var'])
    if combos and k in seen: continue
    seen.add(k); todo.append(s)
res = []
t_start = time.time()
for s in todo:
    t = round((s['t0'] + s['t1']) / 2, 3)
    try:
        sp = sets.build_shot(s)
    except Exception as e:
        print('FAIL build', s['id'], e); continue
    layers = list(sp)
    if chars and s.get('chars'):
        import characters as C
        for spec in s['chars']:
            spec = dict(spec)
            try:
                at = sets.resolve_at(sp, spec); spec['at'] = at
                rig = C.CharRig(spec, s)
            except Exception as e:
                continue
            d = at[3] if (isinstance(at, list) and len(at) > 3 and spec.get('mode') in ('body', 'legs', 'silhouette')) else 1.0
            layers.append(sets.Layer(d, (lambda r: (lambda pen, tt: r.draw(pen, tt)))(rig), 'char_' + spec['who']))
    cam = Cam([tuple(x) for x in s['cam']['keys']], ease=s['cam'].get('ease', 'lin'))
    try:
        img = render_frame(layers, cam.at(t), t, int(t * 60), **sp.render_kw(), post=sp.fx(t))
    except Exception as e:
        print('FAIL render', s['id'], e); continue
    bgr = np.ascontiguousarray(img[..., ::-1])
    name = '%s__%s__%s__%s.jpg' % (s['id'], s['set'], s['view'], s['var'])
    cv2.imwrite(os.path.join(out, 'stills', name), bgr, [cv2.IMWRITE_JPEG_QUALITY, 88])
    m = look(bgr); m.update(id=s['id'], t=t, set=s['set'], view=s['view'], var=s['var'], world=s.get('world'), cls=s.get('cls'),
                            type=s.get('type'), file=name, grade=sp.grade)
    res.append(m)
    if len(res) % 25 == 0: print(len(res), '/', len(todo), '%.0fs' % (time.time() - t_start), flush=True)
json.dump(res, open(os.path.join(out, 'looks.json'), 'w'), indent=0)
# summaries
import collections
W = collections.defaultdict(list)
for m in res: W[m['world']].append(m)
print('%-13s %4s %6s %6s %6s %6s %6s %6s %6s %6s' % ('world', 'n', 'p50', 'p95', 'sat', 'colorf', 'p95-p5', 'std', 'edges', 'red%'))
for w, L in sorted(W.items()):
    a = lambda k: np.median([x[k] for x in L])
    print('%-13s %4d %6.0f %6.0f %6.0f %6.0f %6.0f %6.0f %6.3f %6.1f' % (w, len(L), a('p50'), a('p95'), a('sat'), a('colorful'),
                                                                     np.median([x['p95'] - x['p5'] for x in L]), a('std'), a('edges'), 100 * np.mean([x['red'] for x in L])))
if not combos and every == 1 and not ids:
    print('tenth  luma_p50(median of shots)  mean-luma  red%  (weighted by shot duration)')
    dur = {s['id']: s['dur'] for s in SH}
    for k in range(10):
        L = [m for m in res if k * 70 <= m['t'] < (k + 1) * 70]
        if not L: continue
        w = np.array([dur[m['id']] for m in L])
        print('%3d-%3d  %5.0f  %5.0f  %5.2f' % (k * 70, k * 70 + 70, np.median([m['p50'] for m in L]), np.average([m['luma'] for m in L], weights=w),
                                         100 * np.average([m['red'] for m in L], weights=w)))
    w = np.array([dur[m['id']] for m in res])
    lum = np.array([m['luma'] for m in res])
    print('whole film (duration-weighted): luma<60 %.1f%%  luma<40 %.1f%%  colourfulness p50 %.0f  contrast p95-p5 p50 %.0f  std p50 %.0f  edges p50 %.3f' % (
        100 * w[lum < 60].sum() / w.sum(), 100 * w[lum < 40].sum() / w.sum(), np.median([m['colorful'] for m in res]),
        np.median([m['p95'] - m['p5'] for m in res]), np.median([m['std'] for m in res]), np.median([m['edges'] for m in res])))
