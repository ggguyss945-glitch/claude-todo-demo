"""Parallel frame renderer + encoder.

Usage (from a version script):
    render.main(make_renderer, duration, fps, out_path, audio=...)

`make_renderer(out_w, out_h)` must return a callable `draw(canvas, t)` that
draws one frame at time t (seconds) onto a canvas already sized out_w x out_h.
Each worker renders a contiguous frame range into a lossless RGB segment; the
segments are then concatenated and encoded once with the audio.
"""
import argparse
import multiprocessing as mp
import os
import shutil
import subprocess
import sys
import time

import numpy as np
import skia


def _worker(args):
    (factory_mod, factory_name, out_w, out_h, fps, f0, f1, seg_path, wid) = args
    mod = __import__(factory_mod)
    draw = getattr(mod, factory_name)(out_w, out_h)
    surf = skia.Surface(out_w, out_h)
    canvas = surf.getCanvas()
    info = skia.ImageInfo.Make(out_w, out_h, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    buf = np.zeros((out_h, out_w, 4), np.uint8)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba",
           "-s", f"{out_w}x{out_h}", "-r", str(fps), "-i", "-",
           "-c:v", "libx264rgb", "-qp", "0", "-preset", "ultrafast", "-threads", "2", seg_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t_start = time.time()
    for fi in range(f0, f1):
        canvas.save()
        canvas.clear(skia.ColorBLACK)
        draw(canvas, fi / fps)
        canvas.restore()
        surf.readPixels(info, buf)
        proc.stdin.write(buf.tobytes())
        if wid == 0 and (fi - f0) % 30 == 0:
            el = time.time() - t_start
            done = fi - f0 + 1
            print(f"  worker0 {done}/{f1 - f0} frames  {el / done:.3f}s/frame", flush=True)
    proc.stdin.close()
    proc.wait()
    return seg_path


def render(factory_mod, factory_name, duration, fps, out_path, out_w, out_h, audio=None,
           workers=4, crf=12, codec="libx264", workdir=None, t0=0.0, t1=None, extra_v=None,
           keep_master=None):
    n_frames = int(round((t1 if t1 else duration) * fps))
    f_start = int(round(t0 * fps))
    workdir = workdir or (os.path.splitext(out_path)[0] + "_segments")
    os.makedirs(workdir, exist_ok=True)
    chunks = []
    total = n_frames - f_start
    per = (total + workers - 1) // workers
    for i in range(workers):
        a = f_start + i * per
        b = min(n_frames, a + per)
        if a < b:
            chunks.append((factory_mod, factory_name, out_w, out_h, fps, a, b,
                           os.path.join(workdir, f"seg{i:02d}.mkv"), i))
    t = time.time()
    ctx = mp.get_context("fork")
    with ctx.Pool(len(chunks)) as pool:
        segs = pool.map(_worker, chunks)
    print(f"rendered {total} frames in {time.time() - t:.1f}s", flush=True)
    lst = os.path.join(workdir, "list.txt")
    with open(lst, "w") as fh:
        for s in segs:
            fh.write(f"file '{os.path.abspath(s)}'\n")
    master = keep_master or os.path.join(workdir, "master.mkv")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", master], check=True)
    encode(master, out_path, fps, audio=audio, crf=crf, codec=codec, t0=t0, extra_v=extra_v)
    if not keep_master:
        shutil.rmtree(workdir, ignore_errors=True)
    else:
        for s in segs:
            os.remove(s)
    return out_path


def encode(master, out_path, fps, audio=None, crf=12, codec="libx264", t0=0.0, extra_v=None,
           maxrate=None):
    cmd = ["ffmpeg", "-v", "error", "-stats", "-y", "-i", master]
    if audio:
        cmd += ["-ss", str(t0), "-i", audio]
    vf = "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p"
    if extra_v:
        vf = extra_v + "," + vf
    cmd += ["-vf", vf, "-c:v", codec, "-preset", "slow", "-crf", str(crf),
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
            "-color_range", "tv", "-r", str(fps)]
    if maxrate:
        cmd += ["-maxrate", maxrate, "-bufsize", maxrate]
    if codec == "libx264":
        cmd += ["-profile:v", "high", "-tune", "animation", "-x264-params", "aq-mode=3"]
    elif codec == "libx265":
        cmd += ["-tag:v", "hvc1"]
    if audio:
        cmd += ["-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac", "-b:a", "320k", "-shortest"]
    cmd += ["-movflags", "+faststart", out_path]
    subprocess.run(cmd, check=True)


def cli(factory_mod, factory_name, duration, default_out, audio=None, fps=30, size=(1440, 2560)):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=default_out)
    ap.add_argument("--fps", type=int, default=fps)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--crf", type=float, default=12)
    ap.add_argument("--codec", default="libx264")
    ap.add_argument("--still", type=float, nargs="*", help="render stills at these times")
    ap.add_argument("--still-dir", default="stills")
    ap.add_argument("--t0", type=float, default=0.0)
    ap.add_argument("--t1", type=float, default=None)
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--keep-master", default=None)
    a = ap.parse_args()
    out_w, out_h = int(size[0] * a.scale), int(size[1] * a.scale)
    if a.still is not None:
        mod = __import__(factory_mod)
        draw = getattr(mod, factory_name)(out_w, out_h)
        os.makedirs(a.still_dir, exist_ok=True)
        surf = skia.Surface(out_w, out_h)
        for t in a.still:
            c = surf.getCanvas()
            c.save()
            c.clear(skia.ColorBLACK)
            draw(c, t)
            c.restore()
            p = os.path.join(a.still_dir, f"{factory_mod}_{t:06.2f}.png")
            surf.makeImageSnapshot().save(p)
            print(p)
        return
    render(factory_mod, factory_name, duration, a.fps, a.out, out_w, out_h, audio=audio,
           workers=a.workers, crf=a.crf, codec=a.codec, t0=a.t0, t1=a.t1,
           keep_master=a.keep_master)


if __name__ == "__main__":
    sys.exit("import this module from a version script")
