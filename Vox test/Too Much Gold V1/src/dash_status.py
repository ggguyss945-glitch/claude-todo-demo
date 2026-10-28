#!/usr/bin/env python3
"""Collects the render's state into one JSON file of rows for the live render dashboard:
a summary row, the latest finished frame (as a small JPEG data URL), one row per second
of video (done / rendering / queued), the production stages, and a history of frames done.
    python3 dash_status.py <scratch dir> <out.json>
"""
import base64, glob, json, os, re, subprocess, sys, time
from datetime import datetime, timezone

S, OUT = sys.argv[1], sys.argv[2]
SEG = os.path.join(S, 'TMG_full_seg')
FPS, TOTAL_S = 60, 51
TOTAL = FPS * TOTAL_S
iso = lambda t: datetime.fromtimestamp(t, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

SHOTS = [(0, 'Хук: король бросает золото'), (1.5, 'Золото как мусор'), (3.3, 'Караван у пирамид'), (5.4, 'Король под зонтом'),
         (7.0, 'Шестьдесят тысяч человек'), (8.42, 'Верблюд с золотом'), (10.12, 'Кошель за рулон ткани'), (12.15, 'Золото всем'),
         (13.84, 'Купцы'), (14.6, 'Нищие'), (15.32, 'Дети'), (15.98, 'Погонщик верблюда'), (17.56, 'Каир тонет в золоте'),
         (19.7, 'Хлеб: 1 → 3 монеты'), (22.82, 'Пекарь пожимает плечами'), (24.12, '«У всех теперь золото!»'), (26.2, 'Меняла'),
         (28.98, 'Человек в куче золота'), (30.34, 'Монета в пыли'), (31.6, 'Одна монета: редкость'), (33.84, 'Потоп из золота'),
         (35.86, 'Двенадцать лет спустя'), (38.62, 'Закат: путь домой'), (39.94, 'Лагерь: сундук'), (41.92, 'Сундук пуст'),
         (43.2, 'Назад к купцам'), (45.76, '«Эй. Помнишь меня?»'), (47.08, 'Заём'), (48.3, 'Теперь золото у них')]
def shot_at(t):
    name = SHOTS[0][1]
    for t0, n in SHOTS:
        if t >= t0: name = n
    return name

now = time.time()
done = {int(os.path.basename(f)[1:7]) // FPS for f in glob.glob(os.path.join(SEG, '*.done'))}
claims = {int(os.path.basename(f)[1:7]) // FPS: os.path.getmtime(f) for f in glob.glob(os.path.join(SEG, '*.claim'))}
running = sorted(set(claims) - done)
alive = int(subprocess.run(['bash', '-c', 'pgrep -fc "[r]ender.js --app app --version tmg"'], capture_output=True, text=True).stdout.strip() or 0)
start = min(claims.values()) if claims else now

# frames inside chunks still being rendered: each slot's log counts frames since that process started,
# and a process always starts on a fresh chunk, so its count modulo 60 is how far into the current chunk it is
partial = 0
for i in range(3):
    try:
        lines = open(os.path.join(S, f'tmg_slot{i}.log')).read().splitlines()
        nums = [int(m.group(1)) for l in lines for m in [re.match(r'frames (\d+)/', l)] if m]
        if nums: partial += nums[-1] % FPS
    except FileNotFoundError:
        pass
frames = min(TOTAL, len(done) * FPS + (partial if running else 0))

# history and speed
HIST = os.path.join(S, 'tmg_dash_history.json')
hist = json.load(open(HIST)) if os.path.exists(HIST) else []
if not hist or frames != hist[-1][1] or now - hist[-1][0] > 600: hist.append([now, frames])
hist = hist[-200:]
json.dump(hist, open(HIST, 'w'))
win = [h for h in hist if now - h[0] <= 1500] or hist
fps = (hist[-1][1] - win[0][1]) / max(1, hist[-1][0] - win[0][0]) if len(win) > 1 else 0.0
if fps <= 0 and frames > 0: fps = frames / max(1, now - start)
state = 'done' if len(done) >= TOTAL_S else ('rendering' if alive else 'stopped')
eta = (TOTAL - frames) / fps / 60 if fps > 0 and state != 'done' else 0

rows = [{'id': 'summary', 'kind': 'summary', 'updated': iso(now), 'state': state, 'frames_done': frames, 'frames_total': TOTAL,
         'chunks_done': len(done), 'chunks_total': TOTAL_S, 'fps': round(fps, 3), 'elapsed_min': round((now - start) / 60, 1),
         'eta_min': round(eta, 1), 'workers': alive}]

# the latest finished frame: middle of the most recently finished second, or a preview still before any is done
def jpeg_b64(cmd):
    r = subprocess.run(cmd, capture_output=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(r.stdout).decode() if r.returncode == 0 and r.stdout else None
img, t_img = None, None
if done:
    last = max(done, key=lambda s: os.path.getmtime(os.path.join(SEG, f'c{s * FPS:06d}.mkv.done')))
    img = jpeg_b64(['ffmpeg', '-v', 'error', '-ss', '0.5', '-i', os.path.join(SEG, f'c{last * FPS:06d}.mkv'), '-frames:v', '1',
                    '-vf', 'scale=405:720', '-q:v', '5', '-f', 'mjpeg', '-'])
    t_img = last + 0.5
if not img:
    still = os.path.join(S, 'mm/preview8/r8_0.93.png')
    img = jpeg_b64(['ffmpeg', '-v', 'error', '-i', still, '-vf', 'scale=405:720', '-q:v', '5', '-f', 'mjpeg', '-'])
    t_img = 0.93
rows.append({'id': 'preview', 'kind': 'preview', 'image': img, 'time_s': t_img, 'shot': shot_at(t_img),
             'timecode': f'00:{int(t_img):02d}:{int((t_img % 1) * FPS):02d}', 'from_render': bool(done)})

# one row per second of video
for s in range(TOTAL_S):
    st = 'done' if s in done else ('rendering' if s in running else 'queued')
    rows.append({'id': f'sec-{s:02d}', 'kind': 'second', 'second': s, 'shot': shot_at(s + 0.5), 'status': st})

# production stages (kept by hand in tmg_stages.json as the work moves on)
for k, st in enumerate(json.load(open(os.path.join(S, 'tmg_stages.json')))):
    rows.append({'id': f'stage-{k + 1}', 'kind': 'stage', 'order': k + 1, 'step': st['step'], 'status': st['status'], 'detail': st['detail']})

# frames over time
for k, (t, f) in enumerate(hist):
    rows.append({'id': f'hist-{k:03d}', 'kind': 'history', 'at': iso(t), 'frames': f})

json.dump(rows, open(OUT, 'w'), ensure_ascii=False)
print(f'{frames}/{TOTAL} frames, {len(done)}/{TOTAL_S} seconds, {fps:.2f} fps, eta {eta:.0f} min, state {state}, {os.path.getsize(OUT) // 1024} KB')
