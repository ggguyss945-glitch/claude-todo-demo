"""Set test harness: render shots (sets only, or with cast) at 960x540 -> contact sheet.
usage: sh.py OUT.jpg [--chars] [--size WxH] SHOTID[@t] ... | --combos [set] """
import sys, os, json, time, math
F = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, F); os.chdir(F)
import numpy as np, cv2
from engine import set_render_size
from engine.camera import Cam
from engine.scene import render_frame
args = sys.argv[1:]
out = args.pop(0)
chars = '--chars' in args; args = [a for a in args if a != '--chars']
size = (960, 540)
if '--size' in args:
    i = args.index('--size'); size = tuple(int(v) for v in args[i + 1].split('x')); del args[i:i + 2]
cols = 4
stills_dir = None
if '--stills' in args:
    i = args.index('--stills'); stills_dir = args[i + 1]; del args[i:i + 2]; os.makedirs(stills_dir, exist_ok=True)
per = 10 ** 9
if '--per' in args:
    i = args.index('--per'); per = int(args[i + 1]); del args[i:i + 2]
if '--cols' in args:
    i = args.index('--cols'); cols = int(args[i + 1]); del args[i:i + 2]
set_render_size(*size)
import sets
D = json.load(open('plan/shots.json')); S = {s['id']: s for s in D['shots']}
if args and args[0] == '--combos':
    want = args[1:]
    seen = {}; ids = []
    for s in D['shots']:
        k = (s['set'], s['view'], s['var'])
        if want and s['set'] not in want: continue
        if k not in seen: seen[k] = 1; ids.append(s['id'])
    args = ids
tiles = []
for a in args:
    sid, _, tt = a.partition('@')
    s = S[sid]
    t = float(tt) if tt else round((s['t0'] + s['t1']) / 2, 3)
    t0 = time.perf_counter()
    try:
        sp = sets.build_shot(s)
    except KeyError as e:
        print('MISSING', sid, e); continue
    tb = time.perf_counter() - t0
    layers = list(sp)
    if chars and s['chars']:
        import characters as C
        for spec in s['chars']:
            spec = dict(spec); at = sets.resolve_at(sp, spec); spec['at'] = at
            try:
                rig = C.CharRig(spec, s)
            except Exception as e:
                print('  char fail', spec['who'], e); continue
            d = at[3] if (isinstance(at, list) and len(at) > 3 and spec.get('mode') in ('body', 'legs', 'silhouette')) else 1.0
            def drw(r):
                def f(pen, tt):
                    try: r.draw(pen, tt)
                    except Exception as e: pass
                return f
            L_ = sets.Layer(d, drw(rig), 'char_' + spec['who'])
            if s['view'] == 'phone_screen' and spec['who'] == 'queen': sets.clip_layer(L_, sp.info['screen'])
            layers.append(L_)
    k = s['cam']['keys']
    cam = Cam([tuple(x) for x in k], ease=s['cam'].get('ease', 'lin'), shake=s['cam'].get('shake', 2) * 0.0)
    t1 = time.perf_counter()
    img = render_frame(layers, cam.at(t), t, int(t * 60), **sp.render_kw(), post=sp.fx(t))
    tr = time.perf_counter() - t1
    img = np.ascontiguousarray(img[..., ::-1]) if img.shape[2] == 3 else img
    lab = '%s %s/%s/%s t=%.2f %.0fms' % (sid, s['set'], s['view'], s['var'], t, tr * 1000)
    th = cv2.resize(img, (400, 225), interpolation=cv2.INTER_AREA) if cols > 1 else img
    cv2.putText(th, lab, (4, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(th, lab, (4, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (255, 255, 0), 1, cv2.LINE_AA)
    luma = float(np.median(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)))
    print(lab, 'build %.0fms' % (tb * 1000), 'luma_p50 %.0f' % luma, flush=True)
    tiles.append(th)
    if stills_dir: cv2.imwrite(os.path.join(stills_dir, '%s__%s__%s__%s.jpg' % (s['set'], s['view'], s['var'], sid)), img, [cv2.IMWRITE_JPEG_QUALITY, 88])
    if cols == 1: cv2.imwrite(out.replace('.jpg', '_%s.jpg' % sid), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
if cols > 1 and tiles:
    for pg in range(0, len(tiles), per):
        tl = tiles[pg:pg + per]
        rows = int(math.ceil(len(tl) / cols)); H, W = tl[0].shape[:2]
        sheet = np.zeros((rows * H, cols * W, 3), np.uint8)
        for i, t_ in enumerate(tl): sheet[(i // cols) * H:(i // cols + 1) * H, (i % cols) * W:(i % cols + 1) * W] = t_
        o = out if per >= len(tiles) else out.replace('.jpg', '_%d.jpg' % (pg // per + 1))
        cv2.imwrite(o, sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
