"""Shorts assembler: shorts_spec.json + the owner's narration -> a finished vertical Short (picture), its voice track and
the cue lists for the mixer.

    python3 shorts/assemble.py --short 1|2|3 [--preview] [--out DIR] [--workers 3] [--with-new-lines]
            [--stills 0.5,12,30] [--sheet] [--no-render] [--from_ T0 --to T1]

Outputs (DIR defaults to $S/pov2/shorts/S<n>[_preview]):
    voice.wav        the owner's narration cut and re-timed (48 kHz 24-bit mono, dry; radio / phone voicing is marked per
                     clip in timing.json for the mixer)
    timing.json      beats (t0, t1, voice clips with source and destination times), words, caption chunks, shots
    cues_sfx.json    every cut, punch, slam, UI pop, knock, click... {t, name (audio/sfx.py NAMES), gain_db, pan, space?,
                     params?, kind: 'hit' | 'transient' | 'bed' | 'diegetic', why}
    cues_music.json  {duration, track, start_in_track, intensity [[t, 0..1]], events [{t, type, level, len?}], tension_gap}
    picture.mp4      1080x1920 / 60 fps (or 540x960 / 30 fps with --preview), libx264
    short.mp4        picture + the raw voice track
--with-new-lines: if $S/pov2/shorts_vo/<ID>.wav exist (S1-N2, S1-N3, S2-N1, S2-N2, S3-N1, S3-N2) they are inserted as the
spoken subscribe and end calls (the re-timing makes room for them).
Speed: 3 worker processes, each one contiguous slice; the landscape film frame is rendered at H*16/9 x H and cropped.
"""
import argparse, importlib, json, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
sys.path.insert(0, V2); sys.path.insert(0, HERE)
import numpy as np
import cv2

S = '/home/user/claude-todo-demo/Vox test/Police Officer Video/v2/_work'
SPEC = os.path.join(HERE, 'shorts_spec.json')
NEWVO = os.environ.get('SHORTS_VO', os.path.join(S, 'pov2', 'shorts_vo'))

ap = argparse.ArgumentParser()
ap.add_argument('--short', type=int, required=True, choices=[1, 2, 3])
ap.add_argument('--preview', action='store_true')
ap.add_argument('--out', default=None)
ap.add_argument('--workers', type=int, default=3)
ap.add_argument('--worker', type=int, default=-1)
ap.add_argument('--with-new-lines', action='store_true', dest='new_lines')
ap.add_argument('--stills', default=None)
ap.add_argument('--sheet', action='store_true', help='contact sheet: one still per shot (mid-shot)')
ap.add_argument('--no-render', action='store_true', dest='no_render')
ap.add_argument('--from_', type=float, default=None, dest='t0')
ap.add_argument('--to', type=float, default=None)
ap.add_argument('--crf', default=None)
a = ap.parse_args()

if a.preview: W, H, FPS = 540, 960, 30
else: W, H, FPS = 1080, 1920, 60
LW = int(round(H * 16 / 9)); LW += LW % 2
SID = 'S%d' % a.short
OUT = a.out or os.path.join(S, 'pov2', 'shorts', SID + ('_preview' if a.preview else ''))
os.makedirs(OUT, exist_ok=True)
if a.worker >= 0: cv2.setNumThreads(1)

from engine.core import set_render_size  # noqa: E402
set_render_size(LW, H)

import timing as TM  # noqa: E402
from edit import Edit  # noqa: E402
from stage import Renderer  # noqa: E402
from overlay import Overlay, Post  # noqa: E402


def build():
    spec = json.load(open(SPEC))
    sp = [s for s in spec['shorts'] if s['id'] == SID][0]
    V = TM.Voice()
    E = Edit(sp, V)
    E.new_lines = {}
    E.new_texts = {k: v['text'] for k, v in spec['new_lines'].items()}
    if a.new_lines:
        for k in spec['new_lines']:
            p = os.path.join(NEWVO, k + '.wav')
            if k.startswith(SID + '-') and os.path.exists(p): E.new_lines[k] = p
    mod = importlib.import_module('s%d' % a.short)
    mod.voice(E)
    E.retime()
    mod.stage(E)
    E.finish()
    return sp, V, E


def write_meta(sp, V, E):
    T = E.T
    V.write(T, os.path.join(OUT, 'voice.wav'), dur=E.dur)
    shots = [dict(t0=round(s.t0, 3), t1=round(s.t1, 3), beat=s.beat, src=type(s.src).__name__,
                  T0=round(getattr(s.src, 'T0', 0) or 0, 3), kind=getattr(s.src, 'kind_', None), punches=[(round(x, 3), y) for x, y in s.punches])
             for s in E.shots]
    tj = dict(short=SID, title=sp['title'], duration=round(E.dur, 3), fps=FPS, size=[W, H], beats=T['beats'], clips=T['clips'],
              words=E.words, chunks=E.chunks, shots=shots, events=[{k: v for k, v in e.items() if not callable(v)} for e in E.events],
              hud=[(round(t, 3), s) for t, s in E.huds])
    json.dump(tj, open(os.path.join(OUT, 'timing.json'), 'w'), indent=0, default=float)
    import cues as CU
    sfx, mus = CU.build(E, sp, make_renderer(E))
    st = CU.stats(sfx, E.dur)
    print('[assemble] per 10 s (start, hits, transients):', st, flush=True)
    json.dump(sfx, open(os.path.join(OUT, 'cues_sfx.json'), 'w'), indent=0)
    json.dump(mus, open(os.path.join(OUT, 'cues_music.json'), 'w'), indent=0)
    return sfx, mus


def make_renderer(E):
    from film import Film
    tl = json.load(open(os.path.join(S, 'pov2', 'align', 'timeline.json')))
    F = Film(tl)
    return Renderer(F, W, H, E.shots, overlay=Overlay(E), post=Post(E))


def encoder(path, w, h, fps, crf, threads=2):
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(fps), '-i', '-',
                             '-c:v', 'libx264', '-preset', 'faster' if not a.preview else 'veryfast', '-crf', str(crf), '-pix_fmt', 'yuv420p',
                             '-profile:v', 'high', '-threads', str(threads), '-x264-params', f'keyint={fps}:min-keyint={fps}:scenecut=0',
                             '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-movflags', '+faststart', path],
                            stdin=subprocess.PIPE)


def main():
    sp, V, E = build()
    crf = a.crf or ('20' if a.preview else '16')
    if a.worker < 0:
        sfx, mus = write_meta(sp, V, E)
        print('[assemble] %s %.2f s, %d words, %d shots, %d events, %d sfx cues' % (SID, E.dur, len(E.words), len(E.shots), len(E.events),
                                                                                  len(sfx)), flush=True)
        if a.no_render: return
    if a.stills or a.sheet:
        R = make_renderer(E)
        if a.sheet:
            ts = [min(s.t1 - 0.05, s.t0 + 0.45 * (s.t1 - s.t0)) for s in E.shots]
        else:
            ts = [float(x) for x in a.stills.split(',')]
        tiles = []
        for t in ts:
            t0 = time.time()
            img = R.frame(t, int(round(t * FPS)))
            tiles.append((t, img))
            if not a.sheet:
                p = os.path.join(OUT, 'still_%06.2f.jpg' % t)
                cv2.imwrite(p, cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
                print(p, '%.2fs' % (time.time() - t0), flush=True)
        if a.sheet: contact_sheet(tiles, os.path.join(OUT, 'sheet'))
        return
    N = int(round(E.dur * FPS))
    f_lo = int(round((a.t0 or 0.0) * FPS)); f_hi = int(round(a.to * FPS)) if a.to else N
    if a.worker < 0:
        procs = []
        for w in range(a.workers):
            cmd = [sys.executable, os.path.abspath(__file__), '--short', str(a.short), '--out', OUT, '--worker', str(w),
                   '--workers', str(a.workers), '--crf', crf]
            if a.preview: cmd.append('--preview')
            if a.new_lines: cmd.append('--with-new-lines')
            if a.t0 is not None: cmd += ['--from_', str(a.t0)]
            if a.to is not None: cmd += ['--to', str(a.to)]
            procs.append(subprocess.Popen(cmd))
        t_start = time.time()
        codes = [p.wait() for p in procs]
        if max(codes) != 0: sys.exit('[assemble] worker failed %s' % codes)
        lst = os.path.join(OUT, 'slices.txt')
        with open(lst, 'w') as fh:
            for w in range(a.workers): fh.write("file '%s'\n" % os.path.join(OUT, 'slice_%02d.mp4' % w))
        pic = os.path.join(OUT, 'picture.mp4')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', '-movflags', '+faststart', pic], check=True)
        dst = os.path.join(OUT, 'short.mp4')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', pic, '-ss', '%.3f' % (f_lo / FPS), '-i', os.path.join(OUT, 'voice.wav'),
                        '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', dst],
                       check=True)
        for w in range(a.workers):
            for ext in ('', '.done'):
                try: os.remove(os.path.join(OUT, 'slice_%02d.mp4%s' % (w, ext)))
                except OSError: pass
        print('[assemble] %s  (%.1f min)' % (dst, (time.time() - t_start) / 60), flush=True)
        return
    # ---- worker
    R = make_renderer(E)
    n = f_hi - f_lo
    f0 = f_lo + a.worker * n // a.workers; f1 = f_lo + (a.worker + 1) * n // a.workers
    seg = os.path.join(OUT, 'slice_%02d.mp4' % a.worker)
    enc = encoder(seg, W, H, FPS, crf)
    ts = time.time()
    for k, fi in enumerate(range(f0, f1)):
        t = fi / FPS
        enc.stdin.write(np.ascontiguousarray(R.frame(t, fi)).tobytes())
        if k % (4 * FPS) == 0:
            el = time.time() - ts; r = (k + 1) / max(1e-6, el)
            print('[w%d] %d/%d  %.2f fps  eta %.1f min' % (a.worker, k, f1 - f0, r, (f1 - f0 - k) / max(r, 1e-6) / 60), flush=True)
    enc.stdin.close(); enc.wait()
    print('[w%d] done %.1f min (%.3f s/frame)' % (a.worker, (time.time() - ts) / 60, (time.time() - ts) / max(1, f1 - f0)), flush=True)


def contact_sheet(tiles, prefix, cols=8, tw=180):
    th = int(tw * 16 / 9)
    rows = (len(tiles) + cols - 1) // cols
    sheet = np.zeros((rows * (th + 4), cols * (tw + 4), 3), np.uint8)
    for k, (t, img) in enumerate(tiles):
        r, c = divmod(k, cols)
        im = cv2.resize(img, (tw, th), interpolation=cv2.INTER_AREA)
        cv2.putText(im, '%.1f' % t, (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1, cv2.LINE_AA)
        sheet[r * (th + 4):r * (th + 4) + th, c * (tw + 4):c * (tw + 4) + tw] = im
    p = prefix + '.jpg'
    cv2.imwrite(p, cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 80])
    print(p, flush=True)


if __name__ == '__main__':
    main()
