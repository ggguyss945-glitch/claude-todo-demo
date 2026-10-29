# Vertical shorts cut from an episode, rendered fresh at 1440x2560 60 fps through engine/short.html.
#   python3 -I tools/shorts.py resolve <plan.json>            -> shorts/<id>.json (segments on the frame grid) + times
#   python3 -I tools/shorts.py sheet   <plan.json> <out.jpg>  -> contact sheet from the finished episode, 9:16 windows drawn
#   python3 -I tools/shorts.py render  <plan.json> <work>     -> frames, H.264 video, audio cut from the episode, final mp4
# A plan: {id, ep, timeline, source (episode mp4 with the final mix), tag, hook: {lines, dur}, cta,
#          segments: [{from: line id, to: line id, word?: n (start at that word of `from`), pre, post, x, x1?, z?, mode?}
#                     | {t0, t1, ...}]}
import sys, os, json, subprocess, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 60
SCALE = 2560 / 1080

def resolve(plan_path):
    P = json.load(open(plan_path)); T = json.load(open(P['timeline']))
    L = {l['id']: l for l in T['voice']['lines']}
    segs = []
    for sg in P['segments']:
        sg = dict(sg)
        if 'from' in sg:
            a = L[sg['from']]; b = L[sg.get('to', sg['from'])]
            t0 = a['start'] + (a['words'][sg['word']]['t'] - 0.05 if 'word' in sg else 0) - sg.get('pre', 0.25)
            t1 = b['start'] + b['dur'] + sg.get('post', 0.35)
        else: t0, t1 = sg['t0'], sg['t1']
        f0, f1 = round(t0 * FPS), round(t1 * FPS)
        for sh in T['shots']:
            b = round(sh['start'] * FPS)
            if f0 < b < f0 + 0.45 * FPS: f0 = b
            if f1 - 0.45 * FPS < b < f1: f1 = b
        sg.update(t0=f0 / FPS, t1=f1 / FPS, f0=f0, f1=f1); segs.append(sg)
    for a, b in zip(segs, segs[1:]):   # padding of neighbouring lines may overlap: the later segment starts where the earlier ends
        if a['f0'] < b['f0'] < a['f1']: b['f0'] = a['f1']; b['t0'] = b['f0'] / FPS
    # camera pieces: every segment split at shot boundaries; each shot's framing comes from shorts/framing_ep<n>.json
    fr_path = f'{ROOT}/shorts/framing_ep{P["ep"]}.json'
    FR = json.load(open(fr_path)) if os.path.exists(fr_path) else {}
    pieces = []
    for sg in segs:
        for sh in T['shots']:
            a, b = max(sg['f0'], round(sh['start'] * FPS)), min(sg['f1'], round(sh['end'] * FPS))
            if b <= a: continue
            key = f"{sh['start']:.2f}"
            d = FR.get(key) or ({'mode': 'fit'} if sh['name'] in ('card', 'card2', 'map', 'map2') else {'x': 960})
            pieces.append(dict(d, t0=a / FPS, t1=b / FPS, shot=key, name=sh['name']))
    out = dict(P, segments=segs, pieces=pieces)
    os.makedirs(f'{ROOT}/shorts', exist_ok=True)
    json.dump(out, open(f'{ROOT}/shorts/{P["id"]}.json', 'w'), indent=1)
    times = [f / FPS for sg in segs for f in range(sg['f0'], sg['f1'])]
    return out, times

def sheet(plan_path, out):
    # one cell per camera piece: its first and last frame from the finished episode, the 9:16 window in red
    from PIL import Image, ImageDraw
    P, _ = resolve(plan_path)
    tmp = f'/tmp/shsheet_{P["id"]}'; os.makedirs(tmp, exist_ok=True)
    cw, chh, s = 320, 180, 320 / 1920
    cells = []
    for i, sg in enumerate(P['pieces']):
        cell = Image.new('RGB', (cw * 2 + 6, chh + 22), (24, 24, 24))
        for k, t in enumerate([sg['t0'] + 0.1, sg['t1'] - 0.1]):
            f = f'{tmp}/{i}_{k}.jpg'
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.3f}', '-i', P['source'], '-frames:v', '1', '-vf', f'scale={cw}:{chh}', f], check=True)
            im = Image.open(f).convert('RGB'); d = ImageDraw.Draw(im)
            for gx in range(0, 1921, 320): d.line([(gx * s, 0), (gx * s, 6)], fill=(255, 255, 0)); d.text((gx * s + 1, 6), str(gx // 10), fill=(255, 255, 0))
            if sg.get('mode') != 'fit':
                z = sg.get('z', 1); w = 607.5 / z; x0 = sg.get('x', 960)
                cx = min(1920 - w / 2, max(w / 2, x0 + (sg.get('x1', x0) - x0) * k))
                d.rectangle([(cx - w / 2) * s, 0, (cx + w / 2) * s, chh - 1], outline=(255, 50, 50), width=2)
            cell.paste(im, (k * (cw + 6), 22))
        ImageDraw.Draw(cell).text((3, 4), f"#{i} {sg['shot']} {sg['name']} {sg['t1'] - sg['t0']:.1f}s x={sg.get('x')}{' x1=' + str(sg['x1']) if 'x1' in sg else ''}{' z=' + str(sg['z']) if 'z' in sg else ''} {sg.get('mode', '')}", fill=(255, 255, 255))
        cells.append(cell)
    per = 3; rows = math.ceil(len(cells) / per)
    sh = Image.new('RGB', (per * (cells[0].width + 8), rows * (cells[0].height + 8)), (0, 0, 0))
    for i, c in enumerate(cells): sh.paste(c, ((i % per) * (c.width + 8), (i // per) * (c.height + 8)))
    sh.save(out, quality=88); print('wrote', out, len(cells), 'pieces', round(sum(sg['t1'] - sg['t0'] for sg in P['segments']), 2), 's')

def render(plan_path, work):
    P, times = resolve(plan_path); os.makedirs(work, exist_ok=True)
    json.dump(times, open(f'{work}/times.json', 'w'))
    frames = f'{work}/frames'; n = len(times)
    have = len([f for f in os.listdir(frames) if f.endswith('.jpg')]) if os.path.isdir(frames) else 0
    if have < n:
        page = f'engine/short.html?ep={P["ep"]}&plan=/shorts/{P["id"]}.json'
        r = subprocess.run(['node', f'{ROOT}/tools/render_anim.js', P['timeline'], frames, str(FPS), '4', '-', f'{SCALE:.7f}', f'page={page}', f'times={work}/times.json', 'warm=1'],
                           cwd=ROOT, stdout=open(f'{work}/render.log', 'w'), stderr=subprocess.STDOUT)
        if r.returncode != 0: sys.exit(f'render failed, see {work}/render.log')
    vid = f'{work}/video.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', f'{frames}/f_%05d.jpg', '-frames:v', str(n),
                    '-vf', 'crop=1440:2560:0:0', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p',
                    '-profile:v', 'high', '-g', '120', '-an', vid], check=True)
    # audio: the episode's final mix, cut on the same frames, 25 ms fades at every join so no cut clicks
    parts, flt = [], []
    for i, sg in enumerate(P['segments']):
        d = (sg['f1'] - sg['f0']) / FPS
        fi = 0.05 if i == 0 else 0.025; fo = 0.8 if i == len(P['segments']) - 1 else 0.025
        flt.append(f"[0:a]atrim=start={sg['t0']:.6f}:duration={d:.6f},asetpts=PTS-STARTPTS,afade=t=in:d={fi},afade=t=out:st={max(0, d - fo):.6f}:d={fo}[a{i}]")
        parts.append(f'[a{i}]')
    flt.append(''.join(parts) + f'concat=n={len(parts)}:v=0:a=1[aout]')
    aud = f'{work}/audio.m4a'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', P['source'], '-filter_complex', ';'.join(flt), '-map', '[aout]', '-c:a', 'aac', '-b:a', '320k', aud], check=True)
    out = f'{work}/{P["id"]}_1440x2560_60fps.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', vid, '-i', aud, '-c:v', 'copy', '-c:a', 'copy', '-shortest', '-movflags', '+faststart', out], check=True)
    print('wrote', out, round(n / FPS, 2), 's')

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'resolve': P, times = resolve(sys.argv[2]); print(P['id'], len(times), 'frames', round(len(times) / FPS, 2), 's')
    elif cmd == 'sheet': sheet(sys.argv[2], sys.argv[3])
    elif cmd == 'render': render(sys.argv[2], sys.argv[3])
