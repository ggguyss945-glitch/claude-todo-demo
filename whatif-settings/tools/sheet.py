#!/usr/bin/env python3
"""Contact sheet for an engine v3 timeline: first / middle / last frame of every shot, labelled with shot name and time.

  python3 -I tools/sheet.py <timeline.json> <video.mp4 | frames_dir | render> <out.jpg> [--times t1,t2,...] [--cols 3]
          [--width 640] [--shots name1,name2] [--scale 0.5] [--fps 60]

Sources:
  video.mp4    frames are decoded with ffmpeg at the exact frame times (the video's t = 0 is timeline t = from, see --offset)
  frames_dir   a folder of f_<frame:06d>.jpg|png (render.js stills or kept frames); the nearest frame on disk is used
  render       draws just the needed frames with tools/render.js (times= mode, --scale, default 0.5) into a temp dir
--times replaces the per-shot picks with a free list of times (one row per --cols frames).
"""
import json, os, subprocess, sys, tempfile, shutil, argparse, glob, re
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONT = os.path.join(ROOT, 'assets', 'fonts', 'nunito900.ttf')


def picks(T, fps, only=None):
    out = []
    for sh in T.get('shots', []):
        if only and sh['name'] not in only:
            continue
        a, b = sh['start'], sh['end']
        f0, f1 = round(a * fps), max(round(a * fps), round(b * fps) - 1)
        fm = (f0 + f1) // 2
        out.append((sh['name'], [f0, fm, f1]))
    return out


def grab_video(video, frames, fps, tmp, offset=0.0):
    paths = {}
    for f in sorted(set(frames)):
        p = os.path.join(tmp, f'v_{f:06d}.jpg')
        t = max(0.0, f / fps - offset - 0.25 / fps)
        # accurate input seek: decodes from the previous keyframe and returns the first frame with pts >= t, i.e.
        # exactly frame f (the quarter-frame margin absorbs rounding; seeking past f/fps would return frame f + 1)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-accurate_seek', '-ss', f'{t:.5f}', '-i', video, '-frames:v', '1', '-q:v', '2', p], check=True)
        if os.path.exists(p):
            paths[f] = p
    return paths


def grab_dir(d, frames):
    have = {}
    for p in glob.glob(os.path.join(d, '**', 'f_*.*'), recursive=True):
        m = re.search(r'f_(\d+)\.(jpg|png)$', p)
        if m:
            have[int(m.group(1))] = p
    keys = sorted(have)
    out = {}
    for f in frames:
        if not keys:
            break
        k = min(keys, key=lambda x: abs(x - f))
        out[f] = have[k]
    return out


def grab_render(tl, frames, fps, scale, tmp):
    times = ','.join(f'{f / fps:.6f}' for f in sorted(set(frames)))
    env = dict(os.environ, NODE_PATH=os.environ.get('NODE_PATH', '/opt/node-tools/node_modules'))
    subprocess.run(['node', os.path.join(HERE, 'render.js'), tl, tmp, f'times={times}', f'scale={scale}', f'fps={fps}', 'workers=3'], check=True, env=env)
    return grab_dir(tmp, frames)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('timeline'); ap.add_argument('source'); ap.add_argument('out')
    ap.add_argument('--times', default=None); ap.add_argument('--cols', type=int, default=3)
    ap.add_argument('--width', type=int, default=640); ap.add_argument('--shots', default=None)
    ap.add_argument('--scale', type=float, default=0.5); ap.add_argument('--fps', type=float, default=None)
    ap.add_argument('--offset', type=float, default=0.0, help='timeline time of the first video frame')
    a = ap.parse_args()
    T = json.load(open(a.timeline))
    fps = a.fps or T.get('fps', 60)
    if a.times:
        ts = [float(x) for x in a.times.split(',') if x.strip()]
        fr = [round(t * fps) for t in ts]
        rows = [(None, fr[i:i + a.cols]) for i in range(0, len(fr), a.cols)]
    else:
        rows = picks(T, fps, set(a.shots.split(',')) if a.shots else None)
    allf = [f for _, fs in rows for f in fs]
    tmp = tempfile.mkdtemp(prefix='.sheet_', dir=os.path.dirname(os.path.abspath(a.out)))
    try:
        if a.source == 'render':
            src = grab_render(a.timeline, allf, fps, a.scale, tmp)
        elif os.path.isdir(a.source):
            src = grab_dir(a.source, allf)
        else:
            src = grab_video(a.source, allf, fps, tmp, a.offset)
        tw = a.width
        th = round(tw * 9 / 16)
        lab = 34
        cols = max(len(fs) for _, fs in rows) if rows else 1
        W, H = cols * tw + (cols + 1) * 8, len(rows) * (th + lab + 8) + 8
        sheet = Image.new('RGB', (W, H), (24, 22, 34))
        dr = ImageDraw.Draw(sheet)
        try:
            font = ImageFont.truetype(FONT, 20)
        except Exception:
            font = ImageFont.load_default()
        for r, (name, fs) in enumerate(rows):
            y = 8 + r * (th + lab + 8)
            for c, f in enumerate(fs):
                x = 8 + c * (tw + 8)
                p = src.get(f)
                if p and os.path.exists(p):
                    im = Image.open(p).convert('RGB').resize((tw, th), Image.LANCZOS)
                    sheet.paste(im, (x, y + lab))
                else:
                    dr.rectangle([x, y + lab, x + tw, y + lab + th], fill=(90, 0, 60))
                which = ['first', 'mid', 'last'][c] if name and len(fs) == 3 else ''
                text = f'{name}  {which}  t={f / fps:.3f}s  f{f}' if name else f't={f / fps:.3f}s  f{f}'
                dr.text((x + 4, y + 6), text, fill=(235, 235, 245), font=font)
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        sheet.save(a.out, quality=90)
        print('wrote', a.out, f'{W}x{H}', len(rows), 'rows')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
