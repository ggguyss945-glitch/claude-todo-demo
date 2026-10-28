# Render a long episode in chunks. Each chunk of frames is rendered, then encoded to a video-only H.264 segment in the
# background while the next chunk renders, then deleted, so the whole episode's frames never sit on disk at once.
# Finished segments are kept, so a stopped job resumes where it left off.
# usage: python3 -I tools/render_ep.py <timeline.json> <work_dir> <first_frame> <end_frame> [fps=60] [scale=1.3333333] [chunk=3000] [page=engine/ep.html]
# status: <work_dir>/status.json  {done, total, rate, chunk, chunks, last, segments, finished}
import sys, os, json, time, shutil, subprocess, threading, datetime

TL, WORK = sys.argv[1], sys.argv[2]
FIRST, END = int(sys.argv[3]), int(sys.argv[4])
FPS = int(sys.argv[5]) if len(sys.argv) > 5 else 60
SCALE = sys.argv[6] if len(sys.argv) > 6 else '1.3333333'
CHUNK = int(sys.argv[7]) if len(sys.argv) > 7 else 3000
PAGE = sys.argv[8] if len(sys.argv) > 8 else 'engine/ep.html'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(WORK, exist_ok=True)
chunks = [(a, min(a + CHUNK, END)) for a in range(FIRST, END, CHUNK)]
seg = lambda a: f'{WORK}/seg_{a:05d}.mp4'
now = lambda: datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
state = dict(total=END - FIRST, done=0, rate=0.0, chunk=0, chunks=len(chunks), last='', segments=0, finished=False,
             started_at=now(), updated_at=now(), errors=[])
done_before = 0

def save():
    state['updated_at'] = now()
    tmp = f'{WORK}/status.json.tmp'; json.dump(state, open(tmp, 'w')); os.replace(tmp, f'{WORK}/status.json')

def encode(a, b, frames):
    out = seg(a)
    cmd = ['nice', '-n', '15', 'ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-start_number', str(a), '-i', f'{frames}/f_%05d.jpg',
           '-frames:v', str(b - a), '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
           '-g', str(FPS * 2), '-threads', '2', '-an', out + '.part.mp4']
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0: state['errors'].append(f'encode {a}: {r.stderr[-300:]}'); save(); return
    os.replace(out + '.part.mp4', out)
    shutil.copy(f'{frames}/f_{b - 1:05d}.jpg', f'{WORK}/latest_{a:05d}.jpg')
    shutil.rmtree(frames, ignore_errors=True)
    state['segments'] += 1; save()

enc = None
for k, (a, b) in enumerate(chunks):
    state['chunk'] = k + 1
    if os.path.exists(seg(a)): state['segments'] += 1; state['done'] += b - a; done_before += b - a; save(); continue
    frames = f'{WORK}/frames_{a:05d}'
    have = len([f for f in os.listdir(frames) if f.endswith('.jpg')]) if os.path.isdir(frames) else 0
    if have < b - a:
        shutil.rmtree(frames, ignore_errors=True)
        p = subprocess.Popen(['node', f'{ROOT}/tools/render_anim.js', TL, frames, str(FPS), '4', '-', SCALE, f'page={PAGE}', f'frames={a}:{b}', 'warm=1'],
                             cwd=ROOT, stdout=open(f'{WORK}/render_{a:05d}.log', 'w'), stderr=subprocess.STDOUT)
        t_chunk = time.time()
        while p.poll() is None:
            time.sleep(5)
            try: pr = json.load(open(f'{frames}/progress.json'))
            except Exception: continue
            state['done'] = done_before + pr['done']; state['last'] = f"{frames}/{pr['last']}" if pr['last'] else state['last']
            state['rate'] = round(pr['done'] / max(1, time.time() - t_chunk), 2)   # this chunk's pace, bakes included
            save()
        have = len([f for f in os.listdir(frames) if f.endswith('.jpg')]) if os.path.isdir(frames) else 0
        if p.returncode != 0 or have < b - a:
            state['errors'].append(f'render {a}:{b} exit {p.returncode}, {have} frames'); save(); sys.exit(1)
    done_before += b - a; state['done'] = done_before; save()
    if enc: enc.join()   # one encode at a time; it runs while the next chunk renders
    enc = threading.Thread(target=encode, args=(a, b, frames)); enc.start()
if enc: enc.join()
state['finished'] = not state['errors']; save()
print('finished', state['segments'], 'segments', state['errors'])
