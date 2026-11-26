"""The walls film's sets (14 Larkspur Lane): stills of every set / view / state / insert, a contact sheet, the floor plan, the framing
check at each view's widest camera move and the draw-time bench (one timing).

    python3 tools/sets_sheet_walls.py                 # every variant (1280x720) -> W/sets/wl_*.jpg, sets_sheet.png, index.json, floorplan.jpg
    python3 tools/sets_sheet_walls.py --only ext_,liv_
    python3 tools/sets_sheet_walls.py --frame         # + framing check (magenta holes at the widest camera envelope) -> frame_check.json/.jpg
    python3 tools/sets_sheet_walls.py --bench         # + one 2560x1440 timing per variant -> bench_2560.json
    python3 tools/sets_sheet_walls.py --stage         # cast placed only from Spots (needs characters_ice) -> stage_*.jpg
Stills are graded through the engine exactly like the film (lens, grade, set fx). W = film/_work.
"""
import argparse, json, math, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
sys.path.insert(0, FILM)
import numpy as np
import cv2

ap = argparse.ArgumentParser()
ap.add_argument('--out', default=os.path.join(FILM, '_work', 'sets'))
ap.add_argument('--size', default='1280x720')
ap.add_argument('--only', default=None)
ap.add_argument('--bench', action='store_true')
ap.add_argument('--bench_only', default=None)
ap.add_argument('--frame', action='store_true')
ap.add_argument('--stage', action='store_true')
ap.add_argument('--no_sheet', action='store_true')
ap.add_argument('--no_stills', action='store_true')
ap.add_argument('--keep', default=None, help='comma list of variant names whose full still is kept (wl_<name>.jpg); others only go on the sheet')
a = ap.parse_args()
cv2.setNumThreads(1)

from engine import *                                                     # noqa
from engine.core import set_render_size                                  # noqa
W0, H0 = (int(v) for v in a.size.split('x'))
set_render_size(W0, H0)
import sets as ST                                                        # noqa


def G(fn, grade=None, **opt):
    def build():
        sp = fn()
        if grade: sp.grade = grade
        return sp, opt
    return build


def II(name, **kw):
    return G((lambda n_, kw_: lambda: ST.wl_insert(n_, **kw_))(name, kw))


exec(open(os.path.join(HERE, 'sets_sheet_walls_list.py')).read()) if os.path.exists(os.path.join(HERE, 'sets_sheet_walls_list.py')) else None


def render(sp, opt, t, cam=None, i=0, bg=None):
    kw = sp.render_kw()
    post = dict(sp.fx(t)); post.update(opt.get('post', {}))
    if bg is not None: post.pop('vhs', None)
    return render_frame(list(sp), (cam or hold()).at(t), t, i, **kw, post=post, **({'bg': bg} if bg else {}))


def label(img, s):
    cv2.rectangle(img, (0, img.shape[0] - 24), (img.shape[1], img.shape[0]), (0, 0, 0), -1)
    cv2.putText(img, s, (4, img.shape[0] - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (235, 235, 235), 1, cv2.LINE_AA)
    return img


def sheet(tiles, path, cols):
    rows = [np.hstack(tiles[i:i + cols] + [np.zeros_like(tiles[0])] * (cols - len(tiles[i:i + cols]))) for i in range(0, len(tiles), cols)]
    cv2.imwrite(path, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85] if path.endswith('.jpg') else [cv2.IMWRITE_PNG_COMPRESSION, 6])


def main():
    os.makedirs(a.out, exist_ok=True)
    vs = WALLS
    if a.only: vs = [v for v in vs if any(k in v[0] for k in a.only.split(','))]
    if a.stage:
        stage_run(); return
    thumbs, index = [], []
    if not a.no_stills:
        for name, build, t, note in vs:
            t0 = time.time()
            try:
                sp, opt = build()
                img = render(sp, opt, t)
            except Exception as e:
                import traceback; traceback.print_exc()
                print('FAIL %s: %r' % (name, e), flush=True); continue
            if a.keep and name in a.keep.split(','): cv2.imwrite(os.path.join(a.out, 'wl_' + name + '.jpg'), img[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
            thumbs.append(label(cv2.resize(img[:, :, ::-1], (256, 144), interpolation=cv2.INTER_AREA).copy(), name))
            anchors = {k_: dict(kind=v_.kind, x=round(v_.x, 1), y=round(v_.y, 1), depth=round(v_.depth, 3), ppm=round(v_.ppm, 1),
                                plan=(round(v_.X, 2), round(v_.Yp, 2), round(v_.Y, 2)), turn=None if v_.turn is None else round(v_.turn, 2),
                                seat_y=None if v_.seat_y is None else round(v_.seat_y, 1), note=v_.note)
                       for k_, v_ in sorted(sp.anchors.items()) if isinstance(v_, ST.Spot)}
            index.append(dict(name=name, set=sp.name, t=t, note=note, lens=str(sp.lens), grade=str(sp.grade), anchors=anchors))
            print('%-26s %5.2fs  %s' % (name, time.time() - t0, note), flush=True)
        if thumbs and not a.no_sheet:
            sheet(thumbs, os.path.join(a.out, 'sets_sheet.png' if not a.only else 'sets_partial.png'), 5)
            if not a.only:
                json.dump(index, open(os.path.join(a.out, 'index.json'), 'w'), indent=1)
                ST.wl_plan_map(os.path.join(a.out, 'floorplan.jpg'))
    if a.frame: frame_check(vs)
    if a.bench: bench(vs)


def stage_run():
    tiles = []
    for name, build, figs, note in STAGE_WALLS:
        sp = build(); lays = []
        for who, spot, kw in figs:
            try: lays.append(ST.stage_figure(sp, who, spot, **kw)[0])
            except Exception as e: print('  STAGE FAIL %s %s at %s: %r' % (name, who, spot, e), flush=True)
        sp2 = sp.add(*lays)
        img = render_frame(list(sp2), None, 0.5, 0, **sp2.render_kw(), post=sp2.fx(0.5))
        cv2.imwrite(os.path.join(a.out, 'stage_' + name + '.jpg'), img[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
        tiles.append(label(cv2.resize(img[:, :, ::-1], (640, 360), interpolation=cv2.INTER_AREA).copy(), 'stage_' + name))
        print('stage_%s  %s' % (name, note), flush=True)
    if tiles: sheet(tiles, os.path.join(a.out, 'stage_sheet.jpg'), 3)


def frame_check(vs):
    set_render_size(480, 270)
    res, tiles, seen = [], [], set()
    for name, build, t, note in vs:
        sp, opt = build()
        if sp.name in seen: continue
        seen.add(sp.name)
        env = sp.info.get('cam_env') or dict(x=(920, 1000), y=(500, 580), zoom=(1.0, 1.1), f=(1.0, 1.0))
        x0, x1 = env['x']; y0, y1 = env['y']; z1 = env.get('zoom', (1.0, 1.0))[1]; f1 = env.get('f', (1.0, 1.0))[1]
        cams = [('%s%s' % (cxn, cyn), Cam([(0.0, cx + dx, cy + dy, 1.0)])) for (cxn, cx, dx) in (('L', x0, -8), ('R', x1, 8)) for (cyn, cy, dy) in (('T', y0, -8), ('B', y1, 8))]
        cams.append(('deep', Cam([(0.0, (x0 + x1) / 2, (y0 + y1) / 2, z1)]).snap(-1.0, f1, 0.001)))
        worst, wimg, wn = -1.0, None, ''
        for cn, cm in cams:
            img = render(sp, opt, t, cm, bg='#ff00ff')
            r_, g_, b_ = (img[..., k].astype(np.int16) for k in range(3))
            mag = float(np.mean((r_ > 150) & (b_ > 150) & (g_ * 20 < np.minimum(r_, b_) * 9)))
            if mag > worst: worst, wimg, wn = mag, img, cn
        res.append(dict(name=name, set=sp.name, worst_hole=round(worst, 5), at=wn, env=env))
        tiles.append(label(wimg[:, :, ::-1].copy(), '%s %s %.3f%%' % (name, wn, worst * 100)))
        print('frame %-24s worst %.4f%% (%s)' % (name, worst * 100, wn), flush=True)
    sheet(tiles, os.path.join(a.out, 'frame_check.jpg'), 6)
    json.dump(res, open(os.path.join(a.out, 'frame_check.json'), 'w'), indent=1)
    bad = [r for r in res if r['worst_hole'] > 0.0002]
    print('frame check: %d views, %d with holes > 0.02%%: %s' % (len(res), len(bad), ', '.join(r['name'] for r in bad)))
    set_render_size(W0, H0)


def bench(vs):
    """One steady-state timing per variant at 2560x1440 (caches warm), camera pushing in 2.5 %/s."""
    set_render_size(2560, 1440)
    res = []
    for name, build, t, note in vs:
        if a.bench_only and not any(k in name for k in a.bench_only.split(',')): continue
        sp, opt = build()
        base = hold().at(t)
        cm = push_in(t, t + 10, base.x, base.y, base.zoom, rate=0.025)
        render(sp, opt, t, cm)
        t0 = time.perf_counter(); render(sp, opt, t + 1 / 60.0, cm, 1); dt = time.perf_counter() - t0
        res.append(dict(name=name, s=round(dt, 3)))
        print('bench %-26s %.3f s' % (name, dt), flush=True)
    json.dump(res, open(os.path.join(a.out, 'bench_2560.json'), 'w'), indent=1)
    ms = [r['s'] for r in res]
    if ms: print('bench: %d variants, mean %.3f s/frame, worst %.3f s (%s)' % (len(ms), float(np.mean(ms)), max(ms), res[int(np.argmax(ms))]['name']))


if __name__ == '__main__':
    main()
