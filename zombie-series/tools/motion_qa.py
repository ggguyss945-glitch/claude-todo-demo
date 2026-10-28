# Find animation pops: frame-to-frame jumps inside a shot that stand out from the shot's own motion.
# Run on a low-res proxy render (e.g. 15 fps, scale 0.25). Cuts are skipped; each flagged step is drawn as a
# before / after / difference strip so it can be judged by eye.
# usage: python3 -I tools/motion_qa.py <frames_dir> <timeline.json> <fps> <out_dir> [ratio=4.0] [floor=6.0]
import sys, os, json, glob
import numpy as np
from PIL import Image, ImageDraw

FR, TL, FPS, OUT = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
RATIO = float(sys.argv[5]) if len(sys.argv) > 5 else 4.0
FLOOR = float(sys.argv[6]) if len(sys.argv) > 6 else 6.0
os.makedirs(OUT, exist_ok=True)
T = json.load(open(TL))
files = sorted(glob.glob(f'{FR}/f_*.jpg'))
idx = [int(os.path.basename(f)[2:7]) for f in files]
shot_of = lambda t: next((i for i, s in enumerate(T['shots']) if s['start'] <= t < s['end']), len(T['shots']) - 1)
prev, diffs = None, []
for f, i in zip(files, idx):
    a = np.asarray(Image.open(f).convert('L').resize((240, 135)), np.float32)
    if prev is not None:
        t0, t1 = (i - 1) / FPS, i / FPS
        same = shot_of(t0) == shot_of(t1) and shot_of(t1) == shot_of(t1 + 0.05) and shot_of(t0 - 0.05) == shot_of(t0)
        d = np.abs(a - prev)
        diffs.append((i, t1, float(d.mean()), float(np.percentile(d, 99.5)), same))
    prev = a
flag = []
by_shot = {}
for i, t, m, p99, same in diffs:
    if same: by_shot.setdefault(shot_of(t), []).append((i, t, m, p99))
for k, rows in by_shot.items():
    ms = np.array([r[2] for r in rows]); med = float(np.median(ms)) if len(ms) else 0
    for j, (i, t, m, p99) in enumerate(rows):
        nb = [rows[q][2] for q in (j - 1, j + 1) if 0 <= q < len(rows)]
        if m > FLOOR and m > RATIO * max(med, 0.3) and m > 2.5 * max(nb or [0]):
            flag.append({'frame': i, 't': round(t, 3), 'mean': round(m, 2), 'shot_median': round(med, 2), 'shot': T['shots'][k]['name'], 'p': T['shots'][k].get('p', {})})
json.dump(flag, open(f'{OUT}/flags.json', 'w'), indent=1)
print(len(diffs), 'steps |', len(flag), 'flagged')
# strips: before | after | |difference| x4
for n, fl in enumerate(flag[:60]):
    i = fl['frame']; a = Image.open(f'{FR}/f_{i - 1:05d}.jpg').convert('RGB'); b = Image.open(f'{FR}/f_{i:05d}.jpg').convert('RGB')
    d = Image.fromarray(np.clip(np.abs(np.asarray(a, np.float32) - np.asarray(b, np.float32)) * 4, 0, 255).astype(np.uint8))
    w, h = a.size; strip = Image.new('RGB', (w * 3, h + 22), (0, 0, 0)); strip.paste(a, (0, 22)); strip.paste(b, (w, 22)); strip.paste(d, (w * 2, 22))
    ImageDraw.Draw(strip).text((4, 4), f"{fl['t']}s  {fl['shot']} {json.dumps(fl['p'])[:80]}  step {fl['mean']} vs median {fl['shot_median']}", fill=(255, 230, 120))
    strip.save(f'{OUT}/flag_{n:02d}.jpg', quality=85)
for fl in flag: print(f"  {fl['t']:8.3f}s  {fl['shot']:12s} step {fl['mean']:6.2f}  median {fl['shot_median']:5.2f}  {json.dumps(fl['p'])[:70]}")
