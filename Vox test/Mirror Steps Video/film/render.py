"""Picture renderer for the mirror film (film.py): stills, test clips and the full worker/slice render.

    python3 render.py --stills 12.5,40,61.2 [--size 960x540]          -> <out>/still_0012.50.jpg ...
    python3 render.py --clip 30 36 --size 960x540 [--audio mix.wav]   -> <out>/clip_0030.00_0036.00.mp4
    python3 render.py [--workers 3] [--from_ 0 --to T] [--audio mix_en.wav]
        full render at 2560x1440 / 60 fps: contiguous slices per worker process, libx264 crf 16 preset faster (identical
        settings, so they join with a stream copy) -> <out>/picture.mp4 (+ <out>/film.mp4 with the audio muxed in).
Options: --timeline (default _work/align/timeline.json), --out (default _work/picture for full, _work/tests/render
otherwise), --fps 60, --film film|demo (default: film.py if it exists, else engine/demo.py's DemoFilm), --crf, --preset,
--threads (OpenCV threads per process; full-mode workers default to 1), --name (muxed file name, default film.mp4).
Low-res preview: python3 render.py --size 640x360 --fps 30 --workers 2 --crf 23 --out _work/preview
                 --audio _work/mix/draft/mix.wav --name preview.mp4
Workers write <out>/progress_NN.json ({done, total, fps}) for tools/progress_page.py; finished slices get a .done marker and
are skipped on a re-run, so an interrupted render resumes.
The film contract: Film(timeline_dict).frame(t, i) -> uint8 RGB at the engine render size (set before Film is built);
optional Film.duration (seconds) else timeline['duration_en'] + 2.
"""
import argparse, json, os, subprocess, sys, time
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
S = os.path.join(HERE, '_work')

ap = argparse.ArgumentParser()
ap.add_argument('--timeline', default=os.path.join(S, 'align', 'timeline.json'))
ap.add_argument('--out', default=None)
ap.add_argument('--size', default='2560x1440')
ap.add_argument('--fps', type=int, default=60)
ap.add_argument('--film', default=None, choices=[None, 'film', 'demo'])
ap.add_argument('--stills', default=None)
ap.add_argument('--clip', nargs=2, type=float, default=None)
ap.add_argument('--audio', default=None)
ap.add_argument('--workers', type=int, default=3)
ap.add_argument('--worker', type=int, default=-1)
ap.add_argument('--from_', type=float, default=0.0, dest='t0')
ap.add_argument('--to', type=float, default=None)
ap.add_argument('--crf', default='16')
ap.add_argument('--preset', default='faster')
ap.add_argument('--threads', type=int, default=None)
ap.add_argument('--name', default='film.mp4')
a = ap.parse_args()

W, H = (int(v) for v in a.size.lower().split('x'))
full_mode = a.stills is None and a.clip is None
out = a.out or os.path.join(S, 'picture' if full_mode else os.path.join('tests', 'render'))
os.makedirs(out, exist_ok=True)
threads = a.threads if a.threads is not None else (1 if (full_mode and a.worker >= 0) else None)
if threads is not None: cv2.setNumThreads(threads)

from engine.core import set_render_size                                   # noqa: E402
set_render_size(W, H)


def load_film():
    tl = json.load(open(a.timeline)) if os.path.exists(a.timeline) else {'duration_en': 6.0, 'lines': []}
    use = a.film or ('film' if os.path.exists(os.path.join(HERE, 'film.py')) else 'demo')
    if use == 'film':
        from film import Film
    else:
        from engine.demo import DemoFilm as Film
        print('[render] film.py not found or --film demo: rendering engine/demo.py DemoFilm', flush=True)
    film = Film(tl)
    dur = getattr(film, 'duration', None) or (tl.get('duration_en', 6.0) + 2.0)
    return film, float(dur)


def encoder(path, w, h, fps, crf, preset, x264_threads=2):
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(fps), '-i', '-',
                             '-c:v', 'libx264', '-preset', preset, '-crf', str(crf), '-pix_fmt', 'yuv420p', '-profile:v', 'high',
                             '-threads', str(x264_threads), '-x264-params', f'keyint={2 * fps}:min-keyint={2 * fps}:scenecut=0',
                             '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-movflags', '+faststart', path],
                            stdin=subprocess.PIPE)


def mux(video, audio, dst, t0=0.0, dur=None):
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', video]
    cmd += ['-ss', '%.3f' % t0] + (['-t', '%.3f' % dur] if dur else []) + ['-i', audio]
    cmd += ['-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '320k', '-shortest', '-movflags', '+faststart', dst]
    subprocess.run(cmd, check=True)


# ------------------------------------------------------------------ stills
if a.stills:
    film, dur = load_film()
    for s in a.stills.split(','):
        t = float(s); t0 = time.time()
        img = film.frame(t, int(round(t * a.fps)))
        p = os.path.join(out, f'still_{t:07.2f}.jpg')
        cv2.imwrite(p, cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
        print(p, f'{time.time() - t0:.2f}s', flush=True)
    sys.exit(0)

# ------------------------------------------------------------------ clip (single process)
if a.clip:
    film, dur = load_film()
    c0, c1 = a.clip
    p = os.path.join(out, f'clip_{c0:07.2f}_{c1:07.2f}.mp4')
    tmp = p + '.video.mp4' if a.audio else p
    enc = encoder(tmp, W, H, a.fps, 18 if W < 2000 else a.crf, a.preset, 4)
    f0, f1 = int(round(c0 * a.fps)), int(round(c1 * a.fps))
    ts = time.time()
    for fi in range(f0, f1):
        enc.stdin.write(np.ascontiguousarray(film.frame(fi / a.fps, fi)).tobytes())
    enc.stdin.close(); enc.wait()
    if a.audio:
        mux(tmp, a.audio, p, c0, c1 - c0); os.remove(tmp)
    n = f1 - f0
    print(p, f'{n} frames in {time.time() - ts:.1f}s ({(time.time() - ts) / max(1, n):.3f} s/frame)', flush=True)
    sys.exit(0)

# ------------------------------------------------------------------ full: launcher
if a.worker < 0:
    film_dur = None
    if a.to is None:
        film, film_dur = load_film(); del film
    end = a.to if a.to is not None else film_dur
    procs = []
    for w in range(a.workers):
        cmd = [sys.executable, os.path.abspath(__file__), '--timeline', a.timeline, '--out', out, '--size', a.size, '--fps', str(a.fps),
               '--from_', str(a.t0), '--to', str(end), '--worker', str(w), '--workers', str(a.workers), '--crf', a.crf, '--preset', a.preset]
        if a.film: cmd += ['--film', a.film]
        if a.threads is not None: cmd += ['--threads', str(a.threads)]
        procs.append(subprocess.Popen(cmd))
    codes = [p.wait() for p in procs]
    print('[render] workers done', codes, flush=True)
    if max(codes) != 0: sys.exit(max(codes))
    lst = os.path.join(out, 'slices.txt')
    with open(lst, 'w') as fh:
        for w in range(a.workers): fh.write(f"file '{os.path.abspath(os.path.join(out, f'slice_{w:02d}.mp4'))}'\n")
    pic = os.path.join(out, 'picture.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', '-movflags', '+faststart', pic], check=True)
    print('[render]', pic, flush=True)
    if a.audio:
        mux(pic, a.audio, os.path.join(out, a.name), a.t0, (end - a.t0) if (a.t0 > 0 or a.to is not None) else None)
        print('[render]', os.path.join(out, a.name), flush=True)
    sys.exit(0)

# ------------------------------------------------------------------ full: one worker = one contiguous slice
film, _ = load_film()
N = int(round((a.to - a.t0) * a.fps))
f0 = a.worker * N // a.workers; f1 = (a.worker + 1) * N // a.workers
seg = os.path.join(out, f'slice_{a.worker:02d}.mp4')
prog = os.path.join(out, f'progress_{a.worker:02d}.json')
if os.path.exists(seg + '.done'): sys.exit(0)
enc = encoder(seg, W, H, a.fps, a.crf, a.preset, 2)
t_start = time.time()
for k, fi in enumerate(range(f0, f1)):
    t = a.t0 + fi / a.fps
    enc.stdin.write(np.ascontiguousarray(film.frame(t, fi)).tobytes())
    if k % 120 == 0:
        el = time.time() - t_start; rate = (k + 1) / max(el, 1e-6)
        print(f'[w{a.worker}] {k}/{f1 - f0} frames  {rate:.2f} fps  eta {(f1 - f0 - k) / max(rate, 1e-6) / 60:.1f} min', flush=True)
        with open(prog, 'w') as fh: json.dump({'done': k, 'total': f1 - f0, 'fps': rate}, fh)
enc.stdin.close(); enc.wait()
with open(prog, 'w') as fh: json.dump({'done': f1 - f0, 'total': f1 - f0, 'fps': (f1 - f0) / max(1e-6, time.time() - t_start)}, fh)
open(seg + '.done', 'w').write('ok')
print(f'[w{a.worker}] done in {(time.time() - t_start) / 60:.1f} min', flush=True)
