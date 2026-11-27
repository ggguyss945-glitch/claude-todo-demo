"""tools/motion_metrics.py VIDEO T0 [--fps 60] [--json OUT]: the critic's 60 fps motion measures on a clip of the film that starts at
film time T0 (review round 1, _work/review/v2_r1/tools/decode_metrics.py + analyze.py): per frame the mean absolute difference at
480x270 gray and the global motion (Farneback flow fitted to tx, ty, scale, rot); inside every plan shot (3 frames clear of
each cut) a SPIKE is a frame whose difference exceeds max(6 x the local median, 1.5) and a JERK a frame-to-frame change of the
camera velocity over 0.6 px/frame (tx, ty) or 0.25 %/frame (scale) and over 8 x its median. Transition windows (the flow /
dissolve / paper blends) are measured like the rest of the shot."""
import sys, json, subprocess, argparse, os
import numpy as np, cv2
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument('video'); ap.add_argument('t0', type=float); ap.add_argument('--fps', type=int, default=60)
ap.add_argument('--json', default=None)
a = ap.parse_args()
cv2.setNumThreads(1)
W, H = 480, 270
cmd = ['ffmpeg', '-v', 'error', '-i', a.video, '-vf', f'scale={W}:{H}:flags=area,format=gray', '-f', 'rawvideo', 'pipe:1']
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 8)
w2, h2 = 240, 135
ys, xs = np.mgrid[0:h2, 0:w2].astype(np.float32)
xc = (xs - w2 / 2).ravel(); yc = (ys - h2 / 2).ravel(); one = np.ones_like(xc); zero = np.zeros_like(xc)
A = np.concatenate([np.stack([one, zero, xc, -yc], 1), np.stack([zero, one, yc, xc], 1)], 0); pinv = np.linalg.pinv(A)
mad, gm = [], []
prev = prev2 = None
while True:
    buf = p.stdout.read(W * H)
    if len(buf) < W * H: break
    f = np.frombuffer(buf, np.uint8).reshape(H, W); s2 = cv2.resize(f, (w2, h2), interpolation=cv2.INTER_AREA)
    if prev is None: mad.append(0.0); gm.append(np.zeros(4, np.float32))
    else:
        mad.append(float(cv2.absdiff(f, prev).mean()))
        fl = cv2.calcOpticalFlowFarneback(prev2, s2, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        gm.append((pinv @ np.concatenate([fl[..., 0].ravel(), fl[..., 1].ravel()])).astype(np.float32))
    prev, prev2 = f, s2
p.wait()
mad = np.array(mad); gm = np.array(gm); N = len(mad); fps = a.fps
shots = json.load(open(os.path.join(HERE, 'plan', 'shots.json')))['shots']
spikes, jerks = [], []
t_end = a.t0 + N / fps
for s in shots:
    if s['t1'] <= a.t0 or s['t0'] >= t_end: continue
    i0 = max(0, int(round((s['t0'] - a.t0) * fps))); i1 = min(N, int(round((s['t1'] - a.t0) * fps)))
    seg = np.arange(i0 + 3, i1 - 2)
    if len(seg) < 4: continue
    for i in seg:
        lo, hi = max(i0 + 3, i - 15), min(i1 - 2, i + 15)
        loc = np.median(mad[lo:hi]) + 0.05
        if mad[i] > max(6 * loc, 1.5): spikes.append([round(a.t0 + i / fps, 3), s['id'], round(float(mad[i]), 1), round(float(loc), 2)])
    v = gm[seg]
    for arr, name, thr in ((v[:, 0], 'tx', 0.6), (v[:, 1], 'ty', 0.6), (v[:, 2] * 100, 'scale', 0.25)):
        dv = np.abs(np.diff(arr)); locm = np.median(dv) + 1e-3
        for k in np.where((dv > thr) & (dv > 8 * locm))[0]:
            jerks.append([round(a.t0 + seg[k + 1] / fps, 3), s['id'], name, round(float(arr[k]), 2), round(float(arr[k + 1]), 2)])
out = dict(video=a.video, t0=a.t0, frames=N, spikes=spikes, jerks=jerks)
if a.json: json.dump(out, open(a.json, 'w'), indent=0)
print('%s: %d frames, %d spikes, %d jerks' % (os.path.basename(a.video), N, len(spikes), len(jerks)))
for x in spikes[:30]: print('  spike', x)
