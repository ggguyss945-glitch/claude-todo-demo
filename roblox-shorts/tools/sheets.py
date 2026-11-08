# Frame sheets of a vertical short: one frame every STEP s, 8 per row, time-stamped; split into sheets of 40 frames.
# usage: python3 -I sheets.py <video> <out_prefix> [step=2]
import sys, subprocess, os, math
from PIL import Image, ImageDraw
v, out = sys.argv[1], sys.argv[2]; step = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
dur = float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',v],capture_output=True,text=True).stdout)
tmp = out + '_tmp'; os.makedirs(tmp, exist_ok=True)
subprocess.run(['ffmpeg','-v','error','-y','-i',v,'-vf',f'fps=1/{step},scale=200:-2',f'{tmp}/%04d.jpg'], check=True)
fs = sorted(os.listdir(tmp)); per = 40; W, H = 200, 356
for k in range(math.ceil(len(fs) / per)):
    part = fs[k*per:(k+1)*per]; rows = math.ceil(len(part) / 8)
    sh = Image.new('RGB', (8 * (W + 4), rows * (H + 22)), (16, 16, 20)); d = ImageDraw.Draw(sh)
    for i, f in enumerate(part):
        im = Image.open(f'{tmp}/{f}').convert('RGB').resize((W, H)); x, y = (i % 8) * (W + 4), (i // 8) * (H + 22)
        sh.paste(im, (x, y + 20)); t = (k * per + i) * step; d.text((x + 4, y + 4), f'{int(t//60)}:{t%60:05.2f}', fill=(255, 230, 80))
    sh.save(f'{out}_{k+1}.jpg', quality=82)
for f in fs: os.remove(f'{tmp}/{f}')
os.rmdir(tmp); print(out, len(fs), 'frames')
