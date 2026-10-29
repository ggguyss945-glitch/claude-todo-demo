# The edit itself, for tools/shorts_edit.py make: sound (voice + effects stems cut on the clips and sped up, a new
# music bed across the cuts, whooshes / risers / booms), picture (clean frames with punch-ins, shakes, flashes,
# captions, the hook title, the call to action), then one H.264 + AAC mp4 at 1440x2560 60 fps.
import os, sys, json, math, subprocess, re
import numpy as np, soundfile as sf, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pedalboard import Pedalboard, Compressor, time_stretch
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, f'{ROOT}/audio')
import sfx as X
from ep_music import render_cue, GAIN
import shorts_edit as SE
SR, FPS, OW, OH = X.SR, SE.FPS, SE.OW, SE.OH
SCR = SE.SCR
SF2 = '/tmp/claude-0/-home-user-claude-todo-demo/353ac1d9-152b-55bb-bdf1-0625e0fc6a83/scratchpad/sf/GeneralUser-GS.sf2'
FONT = lambda name, size: ImageFont.truetype(f'{ROOT}/assets/fonts/{name}.ttf', size)
db = lambda d: 10 ** (d / 20)
INK = (43, 29, 33)
WHO = {'DALE': ('DALE · RADIO', (242, 167, 59)), 'NORA': ('NORA', (127, 216, 204)), 'HERO': ('YOU', (255, 255, 255)), 'PA': ('STORE SPEAKER', (242, 194, 48))}

# ---------------------------------------------------------------- sound
def place(track, sig, t, gain=0.0):
    i = int(round(t * SR)); sig = sig * db(gain)
    if i < 0: sig = sig[-i:]; i = 0
    m = min(len(sig), len(track) - i)
    if m > 0: track[i:i + m] += sig[:m]

def cut(stem, E0, c):
    span = c['n'] * c['speed'] / FPS
    a = int(round((c['t0'] - E0) * SR)); b = a + int(round(span * SR))
    x, _ = sf.read(stem, start=max(0, a), stop=max(0, b), dtype='float32', always_2d=True)
    if a < 0: x = np.concatenate([np.zeros((-a, 2), np.float32), x])
    if abs(c['speed'] - 1) > 1e-3: x = time_stretch(x.T.copy(), SR, stretch_factor=c['speed']).T
    n = int(round(c['n'] / FPS * SR)); x = x[:n] if len(x) >= n else np.concatenate([x, np.zeros((n - len(x), 2), np.float32)])
    k = int(0.006 * SR); e = np.ones(n, np.float32); e[:k] = np.linspace(0, 1, k); e[-k:] = np.linspace(1, 0, k)
    return x * e[:, None]

def lufs(path):
    r = subprocess.run(['ffmpeg', '-nostats', '-hide_banner', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1])

def limit(x, ceil=-1.0):
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    n = int(0.012 * SR) | 1
    g = np.minimum(1.0, db(ceil) / np.maximum(np.abs(x).max(1), 1e-9)).astype(np.float32)
    g = uniform_filter1d(minimum_filter1d(g, 2 * n + 1), n)
    return (x * g[:, None]).astype(np.float32)

def sound(E, clips, dur, out):
    T = json.load(open(SE.TL[E['ep']])); E0 = T['ep_start']
    stems = f'{SCR}/stems/ep{E["ep"]}'
    N = int(round(dur * SR)) + SR
    voice, fx, music, hits = (np.zeros((N, 2), np.float32) for _ in range(4))
    for c in clips:
        place(voice, cut(f'{stems}/stemfull_voice.wav', E0, c), c['out0'])
        place(fx, cut(f'{stems}/stemfull_fx.wav', E0, c), c['out0'], -2.5)
    # music: one bed per section, hard in on a switch, a short overlap out
    beat_t = {}
    for c in clips: beat_t.setdefault(c['beat'], c['out0'])
    secs = sorted((beat_t[b], cue) for b, cue in E['music'] if b in beat_t) + [(dur, None)]
    for (t0, cue), (t1, _) in zip(secs, secs[1:]):
        if not cue or cue == '-': continue
        y = render_cue(SF2, cue, t1 - t0 + 0.6, {})[:int((t1 - t0 + 0.6) * SR)]
        env = np.ones(len(y), np.float32); k0, k1 = int(0.04 * SR), int(0.6 * SR)
        env[:k0] = np.linspace(0, 1, k0); env[-k1:] = np.linspace(1, 0, k1)
        place(music, y * env[:, None], t0, GAIN.get(cue, 0) - 5)
    # duck the music under the voice: fast in, quick out, so it surges in the gaps
    hop = SR // 100; v = np.abs(voice).mean(1); nf = len(v) // hop
    fr = np.sqrt((v[:nf * hop].reshape(nf, hop) ** 2).mean(1)); on = (fr > 0.004).astype(np.float32)
    on = np.maximum(on, np.convolve(on, np.ones(8), 'same') > 0)
    sm = np.zeros(nf, np.float32); cur = 0.0
    for i in range(nf): cur += (on[i] - cur) * ((1 - np.exp(-1 / 4)) if on[i] > cur else (1 - np.exp(-1 / 25))); sm[i] = cur
    act = np.interp(np.arange(N), np.arange(nf) * hop + hop / 2, sm).astype(np.float32)
    music *= (1 - act * (1 - db(-10)))[:, None]
    # hits: the hook, the punches and the twists; whooshes on every change of shot; a riser into each music switch
    place(hits, X.boom(1.0, 2.0), 0.0, -6); place(hits, X.whoosh(0.5, 1.0), 0.0, -14)
    prev = None
    for c in clips:
        if c['out0'] > 0.05 and prev is not None and c['shot'] != prev['shot'] and c['k'] == 0: place(hits, X.whoosh(0.32, 1.0), c['out0'] - 0.16, -17)
        if c['fx'] == 'hit' and c['out0'] > 0.05: place(hits, X.boom(1.0, 1.6), c['out0'], -9); place(hits, X.slam(0.6), c['out0'], -16)
        if c['fx'] == 'punch': place(hits, X.whoosh(0.28, 1.0, up=False), c['out0'] - 0.12, -15)
        prev = c
    for b, cue in E['music'][1:]:
        if b not in beat_t: continue
        t = beat_t[b]
        if cue != '-' and t > 2: place(hits, X.riser(1.3, 1.0), t - 1.3, -17)
    mix = voice + fx + music + hits
    mix = Pedalboard([Compressor(threshold_db=-18, ratio=2.5, attack_ms=8, release_ms=120)])(mix, SR)
    mix = limit(mix[:int(round(dur * SR))], -2.0)
    tmp = f'{out}/pre.wav'; sf.write(tmp, mix, SR, subtype='PCM_24')
    g = -13.0 - lufs(tmp)
    for _ in range(4):
        fin = limit(mix * db(g), -1.0); sf.write(f'{out}/audio.wav', fin, SR, subtype='PCM_24')
        L = lufs(f'{out}/audio.wav')
        if abs(L + 13) < 0.15: break
        g += -13.0 - L
    print('audio', round(L, 2), 'LUFS', flush=True)

# ---------------------------------------------------------------- text
def text_img(parts, font, stroke=12, shadow=True):
    """parts: [(text, rgb)], drawn left to right; returns an RGBA PIL image, tight with padding"""
    pad = stroke + 18
    widths = [font.getlength(t) for t, _ in parts]; W = int(sum(widths)) + 2 * pad
    asc, desc = font.getmetrics(); H = asc + desc + 2 * pad
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if shadow:
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(sh); x = pad
        for (t, _), w in zip(parts, widths): d.text((x, pad + 8), t, font=font, fill=(0, 0, 0, 150), stroke_width=stroke, stroke_fill=(0, 0, 0, 150)); x += w
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(im); x = pad
    for (t, col), w in zip(parts, widths): d.text((x, pad), t, font=font, fill=col + (255,), stroke_width=stroke, stroke_fill=INK + (255,)); x += w
    return im

def rich(s):
    """'ONE [[STORM]].' -> parts with the bracketed word red"""
    out = []
    for i, p in enumerate(re.split(r'\[\[(.+?)\]\]', s)):
        if p: out.append((p, (255, 74, 58) if i % 2 else (255, 255, 255)))
    return out

def pill(text, font, fg, bg, padx=26, pady=12):
    w = int(font.getlength(text)); asc, desc = font.getmetrics(); h = asc + desc
    im = Image.new('RGBA', (w + 2 * padx, h + 2 * pady), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=im.height // 2, fill=bg)
    d.text((padx, pady), text, font=font, fill=fg); return im

def to_np(im):
    a = np.asarray(im, np.float32); return a[..., :3][..., ::-1].copy(), a[..., 3:4] / 255.0   # BGR, alpha

def blit(frame, img, cx, cy, scale=1.0, alpha=1.0):
    rgb, al = img
    if abs(scale - 1) > 1e-3:
        h, w = rgb.shape[:2]; nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        rgb = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_LINEAR); al = cv2.resize(al, (nw, nh), interpolation=cv2.INTER_LINEAR)[..., None]
    h, w = rgb.shape[:2]; x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(OW, x0 + w), min(OH, y0 + h)
    if xb <= xa or yb <= ya: return
    r = rgb[ya - y0:yb - y0, xa - x0:xb - x0]; a = al[ya - y0:yb - y0, xa - x0:xb - x0] * alpha
    roi = frame[ya:yb, xa:xb].astype(np.float32); frame[ya:yb, xa:xb] = (roi * (1 - a) + r * a).astype(np.uint8)

# ---------------------------------------------------------------- picture plan
ease = lambda k: 0 if k <= 0 else 1 if k >= 1 else k * k * (3 - 2 * k)
def camera_plan(E, clips):
    """per clip: zoom at start and end, a shake window, flash times (output seconds)"""
    plan, flashes, shakes = [], [], []
    cycle = [(1.00, 1.04), (1.10, 1.13), (1.03, 1.07), (1.14, 1.16)]
    for i, c in enumerate(clips):
        z0, z1 = cycle[i % len(cycle)]
        if c['act']: z0, z1 = 1.0, 1.06
        if c['fx'] == 'punch': z0, z1 = 1.17, 1.19
        if c['fx'] == 'hit' or i == 0:
            z0, z1 = 1.24, 1.08; shakes.append((c['out0'], 0.35, 26)); flashes.append((c['out0'], 0.10))
        if c.get('flash_word') is not None and c['words']:
            w = c['words'][min(c['flash_word'], len(c['words']) - 1)]
            ft = c['out0'] + (w['t'] - c['t0']) / c['speed']; flashes.append((ft, 0.12)); shakes.append((ft, 0.3, 22))
        plan.append((z0, z1))
    return plan, flashes, shakes

def caption_groups(clips):
    groups = []
    for ci, c in enumerate(clips):
        ws = [dict(w, o=c['out0'] + (w['t'] - c['t0']) / c['speed']) for w in c['words']]
        cur = []
        for w in ws:
            txt = re.sub(r'[.,!?]+$', '', w['w']).upper()
            if cur and (len(cur) >= 3 or sum(len(x['txt']) + 1 for x in cur) + len(txt) > 15): groups.append(dict(words=cur, who=c['who'], clip=ci)); cur = []
            cur.append(dict(txt=txt, o=max(c['out0'], w['o'] - 0.04)))
        if cur: groups.append(dict(words=cur, who=c['who'], clip=ci))
    for i, gr in enumerate(groups):
        gr['t0'] = gr['words'][0]['o']
        nxt = groups[i + 1]['words'][0]['o'] if i + 1 < len(groups) else gr['t0'] + 1.5
        gr['t1'] = min(nxt, clips[gr['clip']]['out1'] + 0.25) if i + 1 < len(groups) else clips[gr['clip']]['out1']
        if i + 1 < len(groups) and groups[i + 1]['clip'] != gr['clip']: gr['t1'] = min(nxt, clips[gr['clip']]['out1'])
    return groups

# ---------------------------------------------------------------- picture
def picture(E, clips, dur, out):
    cache = SE.CACHE(E['ep'])
    zplan, flashes, shakes = camera_plan(E, clips)
    groups = caption_groups(clips)
    fcap = FONT('bangers', 150); flab = FONT('rubik800', 34); ftag = FONT('rubik800', 30)
    hook_big = [to_np(text_img(rich(l), FONT('lilita', 132), 14)) for l in E['hook']]
    hook_small = [to_np(text_img(rich(l), FONT('lilita', 76), 9)) for l in E['hook']]
    tag = to_np(pill(E['tag'], ftag, (242, 194, 48, 255), (0, 0, 0, 150)))
    cta = to_np(pill(E['cta'], FONT('lilita', 52), (255, 255, 255, 255), (216, 38, 26, 235), 40, 18))
    labels = {k: to_np(pill(v[0], flab, (20, 16, 18, 255), v[1] + (240,))) for k, v in WHO.items()}
    grad = np.linspace(0.62, 0, 620, dtype=np.float32)[:, None, None]
    cap_cache = {}
    def cap_img(gi, active):
        key = (gi, active)
        if key not in cap_cache:
            gr = groups[gi]; parts = []
            for j, w in enumerate(gr['words']):
                col = (255, 210, 63) if j == active else (255, 255, 255)
                parts.append((w['txt'] + (' ' if j < len(gr['words']) - 1 else ''), col))
            im = text_img(parts, fcap, 13)
            if im.width > OW - 120: im = im.resize((OW - 120, int(im.height * (OW - 120) / im.width)), Image.LANCZOS)
            cap_cache[key] = to_np(im)
        return cap_cache[key]
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{OW}x{OH}', '-r', str(FPS), '-i', '-',
                            '-i', f'{out}/audio.wav', '-c:v', 'libx264', '-preset', 'fast', '-crf', '17', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
                            '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', f'{out}/{E["id"]}_1440x2560_60fps.mp4'], stdin=subprocess.PIPE)
    rng = np.random.default_rng(7); last = None; gi = 0
    HOOK = 2.2
    for ci, c in enumerate(clips):
        z0, z1 = zplan[ci]
        for j, f in enumerate(c['src']):
            t = c['out0'] + j / FPS; k = j / max(1, c['n'] - 1)
            img = cv2.imread(f'{cache}/f_{f:06d}.jpg')
            if img is None: img = last if last is not None else np.zeros((OH, OW, 3), np.uint8)
            else: img = img[:OH, :OW]
            last = img
            # camera: zoom (fast settle on hits), shake, flash
            z = z0 + (z1 - z0) * (ease(min(1, j / (0.4 * FPS))) if z0 > z1 else k)
            dx = dy = 0.0
            for (st, d, a) in shakes:
                if st <= t < st + d: q = 1 - (t - st) / d; dx += a * q * rng.uniform(-1, 1); dy += a * q * rng.uniform(-1, 1)
            if z > 1.001 or dx or dy:
                w, h = OW / z, OH / z; cx, cy = OW / 2 + dx, OH / 2 + dy
                x0 = min(max(0, cx - w / 2), OW - w); y0 = min(max(0, cy - h / 2), OH - h)
                M = np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]])
                frame = cv2.warpAffine(img, M, (OW, OH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
            else: frame = img.copy()
            for (st, d) in flashes:
                if st <= t < st + d:
                    a = 0.85 * (1 - (t - st) / d); frame = (frame.astype(np.float32) * (1 - a) + 255 * a).astype(np.uint8)
            # top shade so the title always reads
            frame[:620] = (frame[:620].astype(np.float32) * (1 - grad)).astype(np.uint8)
            # title: big for the hook, then small at the top with the series tag
            if t < HOOK:
                pop = 1 + 0.14 * (1 - ease(t / 0.2))
                for i, hb in enumerate(hook_big): blit(frame, hb, OW / 2, 470 + i * 150 - (len(hook_big) - 1) * 75, pop)
            else:
                kk = ease((t - HOOK) / 0.25)
                for i, (hb, hs) in enumerate(zip(hook_big, hook_small)):
                    if kk < 1: blit(frame, hb, OW / 2, (470 + i * 150 - (len(hook_big) - 1) * 75) * (1 - kk) + (215 + i * 86) * kk, 1 - 0.42 * kk)
                    else: blit(frame, hs, OW / 2, 215 + i * 86)
                blit(frame, tag, OW / 2, 215 + len(hook_small) * 86 + 6, 1.0, kk)
            # captions: the group being spoken, its current word in yellow, popping in
            while gi + 1 < len(groups) and groups[gi + 1]['t0'] <= t: gi += 1
            gr = groups[gi] if groups else None
            if gr and gr['t0'] <= t < gr['t1']:
                act = max([i for i, w in enumerate(gr['words']) if w['o'] <= t] or [0])
                sc = 1 + 0.16 * (1 - ease((t - gr['t0']) / 0.09))
                cy = 1930 if clips[gr['clip']].get('fit') else 1640
                blit(frame, cap_img(gi, act), OW / 2, cy, sc)
                if gr['who'] in labels: blit(frame, labels[gr['who']], OW / 2, cy - 120, 1.0)
            # the call to action over the last 2.5 seconds
            if t > dur - 2.5: blit(frame, cta, OW / 2, 470, 1.0, ease((t - (dur - 2.5)) / 0.3))
            enc.stdin.write(frame.tobytes())
    enc.stdin.close(); enc.wait()
    print('picture done', flush=True)

def make(E, out):
    os.makedirs(out, exist_ok=True)
    T, clips, dur = SE.plan(E)
    sound(E, clips, dur, out)
    picture(E, clips, dur, out)
    json.dump(dict(id=E['id'], dur=dur, clips=len(clips)), open(f'{out}/done.json', 'w'))
