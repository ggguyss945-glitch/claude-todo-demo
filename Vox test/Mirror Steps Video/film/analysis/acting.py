"""Eye-white area time series (blinks) and face-centre motion in close-up segments at 30 fps. Args: ref_dir"""
import numpy as np, cv2, subprocess, sys
ref = sys.argv[1]
SEG = [('hotel', 44, 64), ('hotel', 84, 92), ('hotel', 160, 172), ('class', 190, 200), ('class', 452, 460), ('class', 88, 96), ('fire', 66, 76), ('fire', 348, 353), ('fire', 438, 446)]
for name, a, b in SEG:
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(a), '-to', str(b), '-i', f'{ref}/{name}.mp4', '-vf', 'scale=640:360', '-pix_fmt', 'bgr24', '-f', 'rawvideo', '-'], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 360, 640, 3)
    area = []; cen = []
    for f in fr:
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY); s = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)[..., 1]
        wm = ((g > 195) & (s < 45)).astype(np.uint8); wm[320:] = 0
        k, lab, st, c = cv2.connectedComponentsWithStats(wm)
        e = [i for i in range(1, k) if 40 < st[i, 4] < 6000 and 0.5 < st[i, 2] / st[i, 3] < 2.2 and 150 < c[i][0] < 490]
        e = sorted(e, key=lambda i: -st[i, 4])[:2]
        area.append(sum(st[i, 4] for i in e)); cen.append(np.mean([c[i] for i in e], 0) if len(e) == 2 else (np.nan, np.nan))
    area = np.array(area, float); cen = np.array(cen)
    med = np.median(area[area > 0]) if (area > 0).any() else 0
    closed = area < 0.35 * med
    # blink = run of closed frames length 1..8 (<=0.27 s) bounded by open
    blinks = []; i = 0
    while i < len(closed):
        if closed[i]:
            j = i
            while j < len(closed) and closed[j]: j += 1
            if i > 0 and j < len(closed) and j - i <= 8: blinks.append((round(a + i / 30, 2), j - i))
            i = j
        else: i += 1
    v = np.nanmedian(np.hypot(*np.diff(cen, axis=0).T)) * 30 * 2  # px/s @1280
    vmax = np.nanpercentile(np.hypot(*np.diff(cen, axis=0).T), 95) * 30 * 2
    # eye-white growth (expression widen): ratio last/first second
    sz = [np.median(area[k:k + 30]) for k in range(0, len(area) - 29, 30)]
    print(f'{name} {a}-{b}s blinks {len(blinks)} {blinks[:6]} | eye-centre speed med {v:.0f} p95 {vmax:.0f} px/s@1280 | eye-white area per s: {[int(x) for x in sz]}')
