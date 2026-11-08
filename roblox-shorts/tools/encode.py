#!/usr/bin/env python3
"""Post-render helpers for the 3D engine output (run with python3 -I).

  encode.py mux    <video.mp4> <audio.wav> <out.mp4> [offset=0] [abr=256k] [pad=1]
        Copy the video stream, encode audio to AAC 48 kHz. offset (s) delays (+) or advances (-) the audio.
        pad=1 pads/trims the audio to the exact video length (no -shortest truncation surprises).
  encode.py sheet  <video.mp4> <out.jpg> [cols=6] [rows=3] [width=270]
        Contact sheet of evenly spaced frames, each stamped with its time.
  encode.py stills <video.mp4> <outdir> <t1,t2,...>
        Full-resolution JPEG stills at the given times (s).
  encode.py concat <out.mp4> <seg1.mp4> <seg2.mp4> ...
        Lossless concatenation of segments with identical encoding parameters.
  encode.py check  <video.mp4>
        Stream summary + QC: duplicate-frame share (true 60 fps?), black/frozen runs, luma range, colour tags.
"""
import json, os, subprocess, sys, tempfile

# Decode our BT.709 limited-range video to full-range RGB exactly (a plain ffmpeg -> jpg keeps the 709 matrix and
# gets read as 601: a visible green/brightness shift). Append to any frame-extraction filter chain.
RGB709 = 'in_color_matrix=bt709:in_range=tv:out_range=pc:flags=bicubic+accurate_rnd+full_chroma_int'


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        sys.exit('command failed: ' + ' '.join(cmd) + '\n' + r.stderr[-2000:])
    return r.stdout


def kv(args):
    out, pos = {}, []
    for a in args:
        if '=' in a and not a.startswith('/'):
            k, v = a.split('=', 1); out[k] = v
        else:
            pos.append(a)
    return pos, out


def probe(path):
    return json.loads(run(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_streams', '-show_format', path]))


def duration(path):
    return float(probe(path)['format']['duration'])


def mux(video, audio, out, offset='0', abr='256k', pad='1'):
    vdur = duration(video); off = float(offset)
    af = []
    if off > 0: af.append(f'adelay={int(off * 1000)}:all=1')
    if pad == '1': af.append(f'apad,atrim=0:{vdur:.6f}')
    cmd = ['ffmpeg', '-y', '-v', 'error', '-i', video]
    if off < 0: cmd += ['-ss', f'{-off:.6f}']
    cmd += ['-i', audio, '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', abr, '-ar', '48000']
    if af: cmd += ['-af', ','.join(af)]
    cmd += ['-movflags', '+faststart', out]
    run(cmd); print(out, f'{duration(out):.3f}s')


def sheet(video, out, cols='6', rows='3', width='270'):
    cols, rows, width = int(cols), int(rows), int(width); n = cols * rows; d = duration(video)
    from PIL import Image, ImageDraw
    with tempfile.TemporaryDirectory() as tmp:
        tiles = []
        for k in range(n):
            t = (k + 0.5) * d / n; f = os.path.join(tmp, f'{k}.jpg')
            run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.3f}', '-i', video, '-frames:v', '1', '-vf', f'scale={width}:-2:{RGB709},format=rgb24', f]); tiles.append((t, f))
        im0 = Image.open(tiles[0][1]); w, h = im0.size
        S = Image.new('RGB', (cols * (w + 4), rows * (h + 4)), (16, 16, 20)); dr = ImageDraw.Draw(S)
        for k, (t, f) in enumerate(tiles):
            x, y = (k % cols) * (w + 4), (k // cols) * (h + 4); S.paste(Image.open(f).convert('RGB'), (x, y)); dr.text((x + 4, y + 4), f'{t:.2f}s', fill=(255, 230, 80))
        S.save(out, quality=85)
    print(out)


def stills(video, outdir, times):
    os.makedirs(outdir, exist_ok=True)
    for t in [float(x) for x in times.split(',')]:
        f = os.path.join(outdir, f'still_{t:07.3f}.jpg')
        run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.4f}', '-i', video, '-frames:v', '1', '-vf', f'scale={RGB709},format=rgb24', '-q:v', '2', f]); print(f)


def concat(out, *segs):
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as fh:
        for s in segs: fh.write("file '%s'\n" % os.path.abspath(s).replace("'", "'\\''"))
        lst = fh.name
    run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', '-movflags', '+faststart', out]); os.unlink(lst); print(out)


def check(video):
    import numpy as np
    p = probe(video); v = [s for s in p['streams'] if s['codec_type'] == 'video'][0]; a = [s for s in p['streams'] if s['codec_type'] == 'audio']
    info = {k: v.get(k) for k in ['width', 'height', 'r_frame_rate', 'nb_frames', 'pix_fmt', 'color_range', 'color_space', 'color_transfer', 'color_primaries', 'profile']}
    info['duration'] = float(p['format']['duration']); info['audio'] = [{k: s.get(k) for k in ['codec_name', 'sample_rate', 'channels']} for s in a]
    w, h = 135, 240
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', video, '-vf', f'scale={w}:{h}', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
    d = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2)); dup = d < 0.05
    runs, cur = [], 0
    for x in dup:
        cur = cur + 1 if x else 0
        if cur == 5: runs.append(len(runs))
    lum = f.mean(axis=(1, 2))
    info['qc'] = {'frames_decoded': int(len(f)), 'duplicate_frame_share': round(float(dup.mean()), 4), 'frozen_runs_ge5': len(runs),
                  'black_frames': int((lum < 3).sum()), 'luma_mean_min_max': [round(float(lum.mean()), 1), round(float(lum.min()), 1), round(float(lum.max()), 1)],
                  'biggest_jumps(frame,diff)': [[int(i), round(float(d[i]), 1)] for i in np.argsort(d)[::-1][:5]]}
    print(json.dumps(info, indent=1))


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in ('mux', 'sheet', 'stills', 'concat', 'check'):
        sys.exit(__doc__)
    cmd = sys.argv[1]; pos, opt = kv(sys.argv[2:])
    {'mux': mux, 'sheet': sheet, 'stills': stills, 'concat': concat, 'check': check}[cmd](*pos, **opt)
