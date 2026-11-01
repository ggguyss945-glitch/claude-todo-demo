"""UI in/out timing at 30 fps: per-frame metric in a region. Args: ref_dir"""
import numpy as np, cv2, subprocess, sys
ref = sys.argv[1]
def dec(name, a, b):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(a), '-to', str(b), '-i', f'{ref}/{name}.mp4', '-pix_fmt', 'bgr24', '-f', 'rawvideo', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, 720, 1280, 3)
def red(f):
    h = cv2.cvtColor(f, cv2.COLOR_BGR2HSV); return (h[..., 2] > 140) & ((h[..., 0] < 8) | (h[..., 0] > 170)) & (h[..., 1] > 110)
def report(label, vals, a):
    v = np.array(vals, float); mx = v.max() + 1e-9; n = v / mx
    on = np.where(n > 0.05)[0]
    if not len(on): print(label, 'none'); return
    s = on[0]; full = s + np.argmax(n[s:] > 0.95); e = on[-1]
    print(f'{label}: appears {a + s/30:.2f}s, reaches 95% in {(full - s)/30:.2f}s, last visible {a + e/30:.2f}s; curve(every 2f from start)={np.round(n[s:s+16:2],2).tolist()}')
fr = dec('fire', 7.5, 10.5)
report('NEVER OPEN UP red px', [red(f[:300]).sum() for f in fr], 7.5)
ws = []
for f in fr:
    ys, xs = np.where(red(f[:300])); ws.append(xs.max() - xs.min() if len(xs) > 50 else 0)
print('   box width over time (every 2f):', ws[::2][:40])
fr = dec('fire', 292, 300.5)
g = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in fr]
report('rule number white px', [(x[240:340, 520:760] > 200).sum() for x in g], 292)
report('rule text white px (typing)', [(x[430:500, 300:980] > 180).sum() for x in g], 292)
tw = [(x[430:500, 300:980] > 180).sum() for x in g]; print('   text px every 0.5s:', tw[::15])
fr = dec('hotel', 50, 55)
report('hotel tags red px', [red(f[:600]).sum() for f in fr], 50)
fr = dec('fire', 129, 134)
report('MICROPHONE tag red px', [red(f[:500, 640:]).sum() for f in fr], 129)
