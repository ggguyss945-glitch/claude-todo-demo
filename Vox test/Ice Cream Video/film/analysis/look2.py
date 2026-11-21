"""Vignette (mean-frame radial profile), DOF (edge rise in background strips of close-ups), bloom halo, chromatic aberration. Arg: va_dir"""
import numpy as np, cv2, glob, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from look import rise_width
va = sys.argv[1]
yy, xx = np.mgrid[:640, :1280]; rr = np.hypot((xx - 640) / 640, (yy - 320) / 640 * 1.0) / np.hypot(1, 0.5)
for name in ['fire', 'hotel', 'class']:
    fs = sorted(glob.glob(f'{va}/{name}/f*.jpg'))[::3]; acc = np.zeros((640, 1280)); n = 0
    for f in fs:
        g = cv2.imread(f, 0)[:640].astype(np.float32)
        if g[:, :150].mean() < 8 and g[:, -150:].mean() < 8: continue  # skip peephole/black-surround
        acc += g; n += 1
    m = acc / n; c = m[rr < 0.2].mean()
    print(name, 'vignette mean-frame luma ratio at r(norm to corner)=.4/.6/.8/.95:', [round(m[(rr >= a - .03) & (rr < a + .03)].mean() / c, 2) for a in (.4, .6, .8, .95)])
# DOF: close-ups; background strips vs centre
for name, t in [('class', 194), ('class', 91), ('class', 182), ('class', 456), ('hotel', 88), ('hotel', 166), ('hotel', 293), ('class', 205), ('fire', 441)]:
    g = cv2.imread(f'{va}/{name}/f{t+1:04d}.jpg', 0)[:640]
    print('DOF', name, t, 'rise L-strip %.2f R-strip %.2f centre %.2f' % tuple((rise_width(x, 0.01) or -1) for x in (g[:420, :260], g[:420, -260:], g[100:600, 440:840])))
# bloom: halos around small bright blobs
for name, t in [('fire', 27), ('fire', 45), ('fire', 234), ('fire', 486), ('hotel', 9), ('class', 353), ('fire', 171)]:
    im = cv2.imread(f'{va}/{name}/f{t+1:04d}.jpg')[:640]; g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)
    b = (g > 215).astype(np.uint8); nlab, lab, st, cen = cv2.connectedComponentsWithStats(b)
    profs = []
    for i in range(1, nlab):
        if not (6 < st[i, 4] < 4000): continue
        cx, cy = cen[i]; r0 = np.sqrt(st[i, 4] / np.pi)
        d = np.hypot(xx - cx, yy - cy) - r0
        bg = np.median(g[(d > 40) & (d < 60)])
        pk = 230
        profs.append([(g[(d >= a) & (d < a + 3)].mean() - bg) / (pk - bg + 1e-6) for a in (2, 6, 12, 20, 30)])
    if profs: print('bloom', name, t, 'n', len(profs), 'halo excess (fraction of peak) at 2/6/12/20/30 px:', np.round(np.median(profs, 0), 2))
# chromatic aberration: R vs B shift in peripheral patches
for name, t in [('fire', 72), ('fire', 351), ('fire', 27), ('hotel', 283), ('class', 22)]:
    im = cv2.imread(f'{va}/{name}/f{t+1:04d}.jpg').astype(np.float32)
    out = []
    for (x0, y0) in [(80, 80), (1000, 80), (80, 420), (1000, 420), (560, 260)]:
        pr = im[y0:y0 + 200, x0:x0 + 200, 2]; pb = im[y0:y0 + 200, x0:x0 + 200, 0]
        if pr.std() < 5 or pb.std() < 5: out.append(None); continue
        (dx, dy), resp = cv2.phaseCorrelate(cv2.Sobel(pb, cv2.CV_32F, 1, 1), cv2.Sobel(pr, cv2.CV_32F, 1, 1))
        out.append((round(dx, 2), round(dy, 2)))
    print('CA', name, t, 'R-vs-B shift (TL,TR,BL,BR,centre):', out)
