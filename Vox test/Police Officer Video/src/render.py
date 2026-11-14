"""Renders the picture: shots from shots.py, post look, captions and header, encoded per slice.
    python3 render.py <timeline.json> <out dir> --workers 3 [--from s --to s] [--stills t1,t2,...] [--fps 60]
Slices are encoded with libx264 (identical settings) so they join with a stream copy.
"""
import argparse, json, math, os, subprocess, sys, time
import numpy as np, cv2, skia
from look import *
import shots as SH

ap = argparse.ArgumentParser()
ap.add_argument('timeline'); ap.add_argument('out')
ap.add_argument('--workers', type=int, default=3); ap.add_argument('--fps', type=int, default=60)
ap.add_argument('--from_', type=float, default=0.0, dest='t0'); ap.add_argument('--to', type=float, default=None)
ap.add_argument('--stills', default=None); ap.add_argument('--worker', type=int, default=-1)
ap.add_argument('--crf', default='16'); ap.add_argument('--preset', default='faster')
a = ap.parse_args()
tl = json.load(open(a.timeline))
FILM = SH.Film(tl)
os.makedirs(a.out, exist_ok=True)


def overlay_layer(t):
    """Captions + header as an RGBA layer (cached by content)."""
    key = FILM.overlay_key(t)
    if key in _ov: return _ov[key]
    s = skia.Surface(RW, RH); cv = s.getCanvas(); cv.clear(skia.ColorTRANSPARENT); cv.scale(K, K)
    FILM.overlay(cv, t)
    arr = s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
    rows = np.where(arr[..., 3].max(axis=1) > 0)[0]
    if len(_ov) > 40: _ov.clear()
    if not len(rows): _ov[key] = None; return None
    # composite only the bands that hold text (header strip, caption block)
    bands, start = [], rows[0]
    for a_, b_ in zip(rows[:-1], rows[1:]):
        if b_ - a_ > 40: bands.append((start, a_ + 1)); start = b_
    bands.append((start, rows[-1] + 1))
    out = []
    for y0, y1 in bands:
        sub = arr[y0:y1]
        al = sub[..., 3:4].astype(np.float32) / 255.0
        out.append((y0, y1, sub[..., :3].astype(np.float32), cv2.merge([1 - al[..., 0]] * 3)))
    _ov[key] = out
    return out


_ov = {}
surf = skia.Surface(RW, RH)


def frame(t, i):
    cv = surf.getCanvas(); cv.save(); cv.clear(col('#000000')); cv.scale(K, K)
    shot = FILM.at(t)
    look_ = shot.render(cv, t)
    cv.restore()
    rgb = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3]
    out = post(np.ascontiguousarray(rgb), i, **look_)
    layer = overlay_layer(t)
    if layer:
        for y0, y1, pm, inv in layer:   # skia gives premultiplied colour: out = out * (1 - a) + colour
            out[y0:y1] = cv2.convertScaleAbs(cv2.add(cv2.multiply(out[y0:y1].astype(np.float32), inv), pm))
    return out


if a.stills:
    for s in a.stills.split(','):
        t = float(s); t0 = time.time()
        img = frame(t, int(t * a.fps))
        p = os.path.join(a.out, f'still_{t:07.2f}.jpg')
        cv2.imwrite(p, cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92]); print(p, f'{time.time() - t0:.2f}s', flush=True)
    sys.exit(0)

end = a.to if a.to is not None else tl['duration_en'] + 2.0
N = int(round((end - a.t0) * a.fps))
if a.worker < 0:   # launcher: split the range into contiguous slices and run workers
    procs = []
    for w in range(a.workers):
        cmd = [sys.executable, __file__, a.timeline, a.out, '--fps', str(a.fps), '--from_', str(a.t0), '--to', str(end), '--worker', str(w),
               '--workers', str(a.workers), '--crf', a.crf, '--preset', a.preset]
        procs.append(subprocess.Popen(cmd))
    codes = [p.wait() for p in procs]
    print('workers done', codes); sys.exit(max(codes))

f0 = a.worker * N // a.workers; f1 = (a.worker + 1) * N // a.workers
seg = os.path.join(a.out, f'slice_{a.worker:02d}.mp4')
if os.path.exists(seg + '.done'): sys.exit(0)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{RW}x{RH}', '-r', str(a.fps), '-i', '-',
                        '-c:v', 'libx264', '-preset', a.preset, '-crf', a.crf, '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-threads', '2',
                        '-x264-params', 'keyint=120:min-keyint=120:scenecut=0', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', seg],
                       stdin=subprocess.PIPE)
t_start = time.time()
for k, fi in enumerate(range(f0, f1)):
    t = a.t0 + fi / a.fps
    enc.stdin.write(frame(t, fi).tobytes())
    if k % 300 == 0:
        el = time.time() - t_start; rate = (k + 1) / max(el, 1e-6)
        print(f'[w{a.worker}] {k}/{f1 - f0} frames  {rate:.2f} fps  eta {(f1 - f0 - k) / max(rate, 1e-6) / 60:.1f} min', flush=True)
        with open(os.path.join(a.out, f'progress_{a.worker:02d}.json'), 'w') as fh: json.dump({'done': k, 'total': f1 - f0, 'fps': rate}, fh)
enc.stdin.close(); enc.wait()
with open(os.path.join(a.out, f'progress_{a.worker:02d}.json'), 'w') as fh: json.dump({'done': f1 - f0, 'total': f1 - f0}, fh)
open(seg + '.done', 'w').write('ok')
print(f'[w{a.worker}] done in {(time.time() - t_start) / 60:.1f} min')
