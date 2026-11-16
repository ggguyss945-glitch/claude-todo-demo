"""Frame strips for the polish pass: every selected shot rendered at --fps (default 12) at a small size, checked for pops
(frame-to-frame jumps inside a shot) and tiled into review sheets with the cut neighbours.

    python3 tools/strips.py --shots 0-40 [--fps 12] [--size 480x270] [--cols 8] [--per 6] [--out _work/tests/polish/strips]
    python3 tools/strips.py --times 290.5-296 [--fps 15]          # a time range instead of shots (one row per shot it crosses)
    python3 tools/strips.py --shots 105 --tag before              # file names carry the tag (before / after strips)

Each row of a sheet is one shot: [the previous shot's last frame] | K frames spread over the shot | [the next shot's first
frame], the shot's index / kind / times and the lines it covers under it. The pop check renders EVERY frame at --fps and
flags a frame whose mean absolute change is > 3.5x the shot's median change and > 6 grey levels (a prop or a limb that
teleports, a layer that pops in): the flags are listed in <out>/<tag>pops.json and marked red on the sheet.
"""
import argparse, json, os, sys, time
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
os.chdir(HERE)
import numpy as np
import cv2

ap = argparse.ArgumentParser()
ap.add_argument('--shots', default=None, help='a-b,c,... shot indices')
ap.add_argument('--times', default=None, help='t0-t1 film seconds')
ap.add_argument('--fps', type=float, default=12.0)
ap.add_argument('--size', default='480x270')
ap.add_argument('--tile', default='320x180')
ap.add_argument('--cols', type=int, default=6)
ap.add_argument('--per', type=int, default=6, help='shots per sheet')
ap.add_argument('--out', default=os.path.join(HERE, '_work', 'tests', 'polish', 'strips'))
ap.add_argument('--tag', default='')
ap.add_argument('--no-pops', action='store_true')
ap.add_argument('--threads', type=int, default=1)
a = ap.parse_args()
cv2.setNumThreads(a.threads)
from engine.core import set_render_size
RW, RH = (int(v) for v in a.size.split('x'))
TW, TH = (int(v) for v in a.tile.split('x'))
set_render_size(RW, RH)
import film as FM

F = FM.Film(json.load(open(os.path.join(FM.ALIGN, 'timeline.json'))))
FPS = FM.FPS


def sel():
    if a.shots:
        out = []
        for part in a.shots.split(','):
            if '-' in part:
                x, y = part.split('-'); out += list(range(int(x), int(y) + 1))
            else: out.append(int(part))
        return [k for k in out if 0 <= k < len(F.shots)]
    t0, t1 = (float(v) for v in a.times.split('-'))
    return [s.idx for s in F.shots if s.t1 > t0 and s.t0 < t1]


def render(t):
    img = F.frame(t, int(round(t * FPS)))
    return img


def label(im, txt, col=(0, 255, 255)):
    cv2.putText(im, txt, (3, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(im, txt, (3, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.36, col, 1, cv2.LINE_AA)
    return im


def tile(img, txt, col=(0, 255, 255), border=None):
    im = cv2.resize(cv2.cvtColor(img, cv2.COLOR_RGB2BGR), (TW, TH), interpolation=cv2.INTER_AREA)
    label(im, txt, col)
    if border is not None: cv2.rectangle(im, (0, 0), (TW - 1, TH - 1), border, 3)
    return im


def wrap(s, n):
    out, cur = [], ''
    for w_ in s.split():
        if len(cur) + len(w_) + 1 > n and cur: out.append(cur); cur = w_
        else: cur = (cur + ' ' + w_).strip()
    if cur: out.append(cur)
    return out


os.makedirs(a.out, exist_ok=True)
ks = sel()
rows, pops_all = [], []
t_start = time.time()
for k in ks:
    sh = F.shots[k]
    step = 1.0 / a.fps
    ts = list(np.arange(sh.t0 + 0.5 / FPS, sh.t1 - 0.5 / FPS, step))
    if not ts: ts = [sh.t0 + 0.5 / FPS]
    if ts[-1] < sh.t1 - 1.5 / FPS: ts.append(sh.t1 - 1.0 / FPS)
    frames = []
    if a.no_pops:
        pick = np.linspace(0, len(ts) - 1, min(a.cols, len(ts))).round().astype(int)
        for j in pick: frames.append((ts[j], render(ts[j])))
        diffs = []
    else:
        prev = None; diffs = []
        for tt in ts:
            img = render(tt)
            small = cv2.resize(img, (160, 90), interpolation=cv2.INTER_AREA).astype(np.float32)
            if prev is not None: diffs.append(float(np.mean(np.abs(small - prev))))
            prev = small
            frames.append((tt, img))
    pops = []
    if len(diffs) >= 4:
        med = float(np.median(diffs)) + 0.4
        for j, d in enumerate(diffs):
            if d > 3.5 * med and d > 6.0:
                pops.append(dict(shot=k, t=round(ts[j + 1], 3), diff=round(d, 2), median=round(med, 2)))
    pops_all += pops
    pop_ts = set(p['t'] for p in pops)
    if a.no_pops:
        chosen = frames
    else:
        pick = set(np.linspace(0, len(frames) - 1, min(a.cols, len(frames))).round().astype(int).tolist())
        for p in pops:                                    # always show a flagged frame
            j = ts.index(min(ts, key=lambda x: abs(x - p['t']))); pick.add(j)
        chosen = [frames[j] for j in sorted(pick)][:a.cols + 3]
    tiles = []
    if k > 0:
        tp = sh.t0 - 1.0 / FPS
        tiles.append(tile(render(tp), '<%d %.2f' % (k - 1, tp), (160, 160, 160)))
        tiles.append(np.full((TH, 6, 3), 255, np.uint8))
    for tt, img in chosen:
        hot = round(tt, 3) in pop_ts
        tiles.append(tile(img, '%.2f' % tt, (60, 60, 255) if hot else (0, 255, 255), (0, 0, 255) if hot else None))
    if k + 1 < len(F.shots):
        tiles.append(np.full((TH, 6, 3), 255, np.uint8))
        tn = F.shots[k + 1].t0 + 0.5 / FPS
        tiles.append(tile(render(tn), '%d> %.2f' % (k + 1, tn), (160, 160, 160)))
    row = np.hstack(tiles)
    ls = [l for l in F.L if l['end'] > sh.t0 + 0.05 and l['t'] < sh.t1 - 0.05]
    txt = ' / '.join('[%d%s] %s' % (l['i'], '' if l['who'] == 'N' else ' ' + l['who'], l['en']) for l in ls) or '(no line)'
    p = sh.p
    hdr = '#%d %s %s %s  %.2f-%.2f (%.2fs)%s' % (k, sh.kind, p.get('room') or p.get('name') or p.get('who') or p.get('mode') or '', p.get('view', ''),
                                              sh.t0, sh.t1, sh.d, ('   POPS: ' + ', '.join('%.2f' % q['t'] for q in pops)) if pops else '')
    tl = [hdr] + wrap(txt, int(row.shape[1] / 7.2))[:3]
    band = np.full((16 * len(tl) + 6, row.shape[1], 3), 24, np.uint8)
    for j, s_ in enumerate(tl):
        cv2.putText(band, s_, (5, 14 + 16 * j), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (120, 230, 255) if j == 0 else (235, 235, 235), 1, cv2.LINE_AA)
    rows.append((k, np.vstack([row, band, np.full((4, row.shape[1], 3), 70, np.uint8)])))
    F._built.clear()
    print('shot %d done (%d frames, %d pops) %.0fs' % (k, len(frames), len(pops), time.time() - t_start), flush=True)

paths = []
for s0 in range(0, len(rows), a.per):
    grp = rows[s0:s0 + a.per]
    wmax = max(r.shape[1] for _, r in grp)
    grp_im = [np.pad(r, ((0, 0), (0, wmax - r.shape[1]), (0, 0))) for _, r in grp]
    pth = os.path.join(a.out, '%sstrip_%03d.jpg' % (a.tag + '_' if a.tag else '', grp[0][0]))
    cv2.imwrite(pth, np.vstack(grp_im), [cv2.IMWRITE_JPEG_QUALITY, 85]); paths.append(pth)
pj = os.path.join(a.out, '%spops.json' % (a.tag + '_' if a.tag else ''))
old = json.load(open(pj)) if os.path.exists(pj) else []
old = [q for q in old if q['shot'] not in ks] + pops_all
json.dump(sorted(old, key=lambda q: q['t']), open(pj, 'w'), indent=0)
print('\n'.join(paths))
print('pops:', len(pops_all), pops_all[:40])
