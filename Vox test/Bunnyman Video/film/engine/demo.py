"""engine.demo: a placeholder porch scene rendered through every lens, plus the HUD gallery and the speed benchmark.

    python3 -m engine.demo [--out DIR] [--bench] [--clip] [--sheets]      (run from v2/)
DemoFilm(timeline=None).frame(t, i) is the 6 s test film render.py falls back to before film.py exists.
"""
import argparse, math, os, sys, time, subprocess
import numpy as np
import cv2
from .core import *                                                      # noqa: F403
from .core import CFG, set_render_size
from .camera import Cam, hold, push_in, drift, handheld
from .scene import Layer, render_frame, STATS, clear_cache, project_box
from .lens import Lens, get_lens
from .post import Grade, police_flash
from . import hud

S = '/home/user/claude-todo-demo/Vox test/Police Officer Video/v2/_work'
OUT = os.path.join(S, 'pov2', 'tests', 'engine')
X0, X1, Y0, Y1 = -1000, 2920, -560, 1640           # wide enough for the doorbell source rect plus camera moves
WIDE = (X0, Y0, X1, Y1)


# ------------------------------------------------------------------ placeholder set (several depths)
def draw_sky(pen, t):
    pen.linear(rect(X0, Y0, X1 - X0, Y1 - Y0), 0, -300, 0, 640, [(0, '#05070f'), (0.55, '#0c1630'), (1, '#1b2442')])
    rng = np.random.default_rng(3)
    for _ in range(260):
        x, y = rng.uniform(X0, X1), rng.uniform(Y0, 420); r = rng.uniform(0.8, 2.2)
        pen.fill(oval(x, y, r), '#dfe6ff', rng.uniform(60, 200))
    pen.glow(1460, 150, 160, '#9fb4e8', 60)
    pen.fill(oval(1460, 150, 46), '#e9eef8'); pen.fill(oval(1476, 140, 40), '#c9d2e6', 90)


def draw_houses(pen, t):
    base = 486
    pen.fill(rect(X0, base - 6, X1 - X0, 40), '#0b0e17')
    xs = list(range(-900, 2900, 330))
    for k, x in enumerate(xs):
        w = 250 + (k * 37) % 70; h = 150 + (k * 53) % 90
        body = rect(x, base - h, w, h)
        roof = poly([(x - 18, base - h), (x + w / 2, base - h - 90 - (k % 3) * 15), (x + w + 18, base - h)])
        pen.fill(union(body, roof), '#121726'); pen.line(union(body, roof), 2.5, '#070910')
        for j in range(2):
            wx = x + 40 + j * (w - 120); wy = base - h + 40
            lit = (k + j) % 3 != 0
            pen.fill(rect(wx, wy, 42, 50), '#d9b47c' if lit else '#1c2233')
            if lit: pen.glow(wx + 21, wy + 25, 70, '#e2a95c', 70)
    for k in range(-2, 9):                          # trees
        x = k * 360 + 150
        pen.fill(smooth([(x - 70, base), (x - 90, base - 120), (x - 30, base - 210), (x + 40, base - 200), (x + 90, base - 110), (x + 70, base)]), '#0a0f14')
    pen.fill(rect(1180, 250, 9, 240), '#0d1018')       # streetlight
    pen.glow(1184, 252, 120, '#ffcf8a', 110); pen.fill(oval(1184, 252, 10), '#fff2d6')


def draw_street(pen, t):
    road = rect(X0, 500, X1 - X0, 150)
    pen.linear(road, 0, 500, 0, 650, ['#171a22', '#0e1016'])
    pen.texture(road, 'asphalt', 0.35, 'overlay', 1.0)
    pen.fill(rect(X0, 648, X1 - X0, 16), '#262a33')
    for k in range(-6, 14): pen.fill(rect(k * 260, 572, 120, 7), '#4a4b44', 160)


def draw_lawn(pen, t):
    pen.linear(rect(X0, 662, X1 - X0, 300), 0, 662, 0, 900, ['#0c1312', '#121a17'])
    pen.fill(poly([(900, 662), (1020, 662), (1170, 900), (750, 900)]), '#2b2c2f')
    pen.texture(poly([(900, 662), (1020, 662), (1170, 900), (750, 900)]), 'plaster', 0.4)
    for k in range(-4, 10):
        x = k * 230
        pen.fill(smooth([(x, 720), (x + 60, 660), (x + 150, 690), (x + 170, 730)]), '#0d1a16')


def draw_porch(pen, t):
    floor = poly([(X0, 860), (X1, 860), (X1, Y1), (X0, Y1)])
    pen.linear(floor, 0, 860, 0, 1300, ['#3a2d23', '#1b1511'])
    pen.texture(floor, 'wood', 0.5, 'overlay', 1.6)
    for k in range(-14, 30): pen.seg((k * 120, 860), (k * 210 - 1100, 1640), 3, '#130e0b', 140)
    for x in (280, 1640):                                   # railing posts
        pen.shape(rect(x - 22, 560, 44, 310), '#4a3a2e', 5)
    pen.shape(rect(-900, 600, 1200, 26), '#4a3a2e', 5); pen.shape(rect(1620, 600, 1300, 26), '#4a3a2e', 5)
    for x in list(range(-860, 280, 70)) + list(range(1700, 2900, 70)):
        pen.shape(rect(x, 626, 16, 234), '#3d3027', 3)


def draw_frame_near(pen, t):
    """Door frame / wall edge right next to the camera (very near)."""
    for (x, w) in ((X0, 170 - X0), (1750, X1 - 1750)):
        r = rect(x, Y0, w, Y1 - Y0)
        pen.linear(r, x, 0, x + w, 0, ['#17110e', '#2a1f19'] if x < 0 else ['#2a1f19', '#17110e'])
        pen.texture(r, 'grunge', 0.4, 'overlay', 1.4)
    pen.shape(rect(160, 330, 50, 74), '#2c2a2a', 4)              # porch lamp on the wall
    pen.glow(185, 370, 260, '#ffcf8f', 120); pen.fill(oval(185, 368, 18), '#fff6e0')
    pen.cone(185, 400, 60, 700, 700, '#ffd9a0', 45, 40)


def draw_figure(pen, t):
    """Placeholder officer: navy uniform, pale face with huge eye whites and tiny pupils, cap."""
    sway = 3 * noise1(t * 0.5, 9)
    cx, feet = 960 + sway, 905
    body = smooth([(cx - 170, feet), (cx - 150, 520), (cx - 90, 460), (cx + 90, 460), (cx + 150, 520), (cx + 170, feet)], True, 0.5)
    pen.shadow(body, 0, 10, 20, '#000000', 120)
    pen.shape(body, '#1c2740', 7)
    pen.shade(body, moved(body, 60, 0), '#141c30', 255)
    pen.fill(oval(cx + 70, 560, 16), '#c9a64a'); pen.line(oval(cx + 70, 560, 16), 4)
    pen.shape(rrect(cx - 70, 545, 46, 60, 8), '#202020', 5)          # bodycam
    pen.fill(oval(cx - 47, 565, 8), '#d02020')
    head = oval(cx, 340, 112, 128)
    pen.shape(head, '#c0aa9e', 7)
    pen.shade(head, oval(cx + 60, 360, 110, 140), '#a99083', 255)
    for ex in (-44, 44):
        pen.shape(oval(cx + ex, 330, 26), '#f3f1ee', 5)
        pen.fill(oval(cx + ex, 333, 8), '#111111'); pen.fill(oval(cx + ex - 3, 330, 2), '#ffffff')
        pen.fill(oval(cx + ex, 362, 22, 7), '#6d5a5c', 90)
    grin = smooth([(cx - 68, 400), (cx, 414), (cx + 68, 400), (cx + 50, 432), (cx, 444), (cx - 50, 432)], True, 0.6)
    pen.shape(grin, '#f2efe6', 5)
    for k in range(-4, 5): pen.seg((cx + k * 13, 404 + abs(k) * 0.8), (cx + k * 12, 438 - abs(k) * 1.2), 2.5)
    cap = union(smooth([(cx - 118, 262), (cx - 100, 200), (cx, 176), (cx + 100, 200), (cx + 118, 262)], True, 0.7), rect(cx - 118, 248, 236, 20))
    pen.shape(cap, '#151d30', 7)
    pen.shape(rrect(cx - 130, 258, 260, 22, 10), '#0d1220', 6)
    pen.fill(oval(cx, 220, 15), '#c9a64a')


def draw_car(pen, t):
    """Patrol car placeholder driving through at the street depth, light bar strobing."""
    x = -700 + ((t * 420) % 3400)
    y = 600
    body = rrect(x - 230, y - 70, 460, 90, 26)
    cab = smooth([(x - 120, y - 70), (x - 80, y - 135), (x + 90, y - 135), (x + 140, y - 70)], True, 0.4)
    pen.shape(union(body, cab), '#11141b', 4)
    pen.fill(rect(x - 228, y - 40, 456, 22), '#d8dbe0', 200)
    for wx in (x - 140, x + 140): pen.shape(oval(wx, y + 20, 38), '#07080a', 4)
    on_r = math.sin(t * 2 * math.pi * 2.2) > 0
    pen.fill(rrect(x - 50, y - 152, 48, 16, 5), '#ff2020' if on_r else '#400808')
    pen.fill(rrect(x + 2, y - 152, 48, 16, 5), '#2040ff' if not on_r else '#081040')
    pen.glow(x - 26 if on_r else x + 26, y - 145, 160, '#ff3030' if on_r else '#3050ff', 140)
    pen.fill(oval(x + 225, y - 30, 12), '#fff3c0'); pen.glow(x + 225, y - 30, 90, '#fff0b0', 110)


def make_layers(approach=None, car=True, blur_bg=True):
    """6+ layers: sky 40, houses 9, street 4.5 (+car), lawn 2.2, porch 1.4, figure 1.0 (or approaching), near frame 0.6."""
    fig_depth = approach if approach is not None else 1.0
    L = [Layer(40, draw_sky, 'sky', cache='demo_sky', bounds=WIDE, blur=0),
         Layer(9, draw_houses, 'houses', cache='demo_houses', bounds=WIDE),
         Layer(4.5, draw_street, 'street', cache='demo_street', bounds=WIDE),
         Layer(2.2, draw_lawn, 'lawn', cache='demo_lawn', bounds=WIDE),
         Layer(1.4, draw_porch, 'porch', cache='demo_porch', bounds=WIDE),
         Layer(fig_depth, draw_figure, 'officer', ref_depth=1.0),
         Layer(0.6, draw_frame_near, 'frame', cache='demo_frame', bounds=WIDE)]
    if car: L.insert(3, Layer(4.3, draw_car, 'car'))
    return L


# ------------------------------------------------------------------ shots
def approach_depth(t, t0=0.0, dur=6.0, d0=1.0, d1=0.42):
    return d0 + (d1 - d0) * ease_in_out((t - t0) / dur)


MOVES = {
    'push': lambda: (push_in(0, 6, 960, 470, 1.0, rate=0.03, shake=1.5), None),
    'drift': lambda: (drift(0, 6, 880, 520, 1060, 500, zoom=1.06, shake=1.5), None),
    'approach': lambda: (handheld(Cam([(0, 960, 500, 1.0), (6, 960, 480, 1.04, 0, 'push')]), 1.2), lambda t: approach_depth(t)),
}
LOOKS = {
    'none': dict(lens=None, grade='night_blue', dof=0.0),
    'lens': dict(lens='lens', grade='night_blue', dof=6.75),
    'doorbell': dict(lens='doorbell', grade='night_blue', dof=0.0),
    'doorbell_ir': dict(lens='doorbell_ir', grade='ir_night', dof=0.0),
    'peephole': dict(lens='peephole', grade='porch_warm', dof=0.0),
}


def officer_box(t, cs, depth, lens):
    """Frame box of the placeholder officer through camera + lens (for the doorbell motion HUD)."""
    return project_box((780, 200, 360, 705), depth, cs, lens, ref_depth=1.0)


def shot_frame(look, move, t, i, hud_on=True):
    cam, dep = MOVES[move]()
    lk = LOOKS[look]
    depth = dep(t) if dep else 1.0
    layers = make_layers(approach=(lambda tt: dep(tt)) if dep else None)
    cs = cam.at(t)
    fx = {}
    if look in ('none', 'lens'): fx['flash'] = police_flash(t, 0.55)
    def h(cv, tt):
        if not hud_on: return
        if look.startswith('doorbell'):
            hud.doorbell_hud(cv, tt, ir=look.endswith('ir'), motion=officer_box(tt, cs, depth, lk['lens']) if move == 'approach' else None)
        elif look in ('none', 'lens'):
            hud.header(cv, 'RULE 1 OF 7'); hud.caption(cv, 'Through the peephole, you see a police officer standing under your porch light.')
    return render_frame(layers, cs, t, i, focus=1.0, dof=lk['dof'], lens=lk['lens'], grade=lk['grade'], post=fx, hud=h)


class DemoFilm:
    """6 s test film: lens/push + police flash, doorbell approach, peephole approach, static flash, IR doorbell drift."""
    duration = 6.0

    def __init__(self, timeline=None):
        self.timeline = timeline

    def frame(self, t, i):
        t = t % 6.0
        if t < 1.5: return shot_frame('lens', 'push', t + 2.0, i)
        if t < 3.0: return shot_frame('doorbell', 'approach', (t - 1.5) * 2.4 + 1.5, i)
        if t < 4.5:
            img = shot_frame('peephole', 'approach', (t - 3.0) * 2.4 + 1.0, i)
            return img
        if t < 4.5 + 4 / 60:
            cam, _ = MOVES['drift']()
            return render_frame(make_layers(), cam.at(t), t, i, lens='doorbell_ir', grade='ir_night', post={'static': 0.85})
        return shot_frame('doorbell_ir', 'drift', t, i)


# ------------------------------------------------------------------ outputs
def _sheet(imgs, labels, cols, tile_w):
    tiles = []
    for im, lb in zip(imgs, labels):
        h, w = im.shape[:2]; th = int(h * tile_w / w)
        tl = cv2.resize(cv2.cvtColor(im, cv2.COLOR_RGB2BGR), (tile_w, th), interpolation=cv2.INTER_AREA)
        cv2.putText(tl, lb, (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
        tiles.append(tl)
    while len(tiles) % cols: tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[k:k + cols]) for k in range(0, len(tiles), cols)]
    return np.vstack(rows)


def sheets(out):
    set_render_size(960, 540)
    imgs, labels = [], []
    for look in ('none', 'lens', 'doorbell', 'doorbell_ir', 'peephole'):
        for move, t in (('push', 5.5), ('drift', 5.5), ('approach', 5.5)):
            imgs.append(shot_frame(look, move, t, int(t * 60))); labels.append(f'{look} / {move} t={t}')
    p = os.path.join(out, 'sheet_lenses.jpg'); cv2.imwrite(p, _sheet(imgs, labels, 3, 480), [cv2.IMWRITE_JPEG_QUALITY, 88]); print(p)
    # approach sequence through the doorbell and peephole
    imgs, labels = [], []
    for look in ('doorbell', 'peephole'):
        for t in (0.0, 2.5, 4.0, 6.0):
            imgs.append(shot_frame(look, 'approach', t, int(t * 60), hud_on=(look == 'doorbell'))); labels.append(f'{look} approach t={t}')
    p = os.path.join(out, 'sheet_approach.jpg'); cv2.imwrite(p, _sheet(imgs, labels, 4, 400), [cv2.IMWRITE_JPEG_QUALITY, 88]); print(p)
    # full-size single doorbell frame (to judge the camera look)
    img = shot_frame('doorbell', 'approach', 3.6, 216)
    p = os.path.join(out, 'doorbell_960.jpg'); cv2.imwrite(p, cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90]); print(p)


def hud_gallery(out):
    set_render_size(960, 540)
    bgl = [Layer(40, draw_sky, 'sky', cache='demo_sky', bounds=WIDE), Layer(9, draw_houses, 'houses', cache='demo_houses', bounds=WIDE),
           Layer(1.4, draw_porch, 'porch', cache='demo_porch', bounds=WIDE)]
    cs = hold().at(0)
    items = []
    rtext = 'If you hear someone *calling* from the patrol car, *do not answer*.'
    tm = hud.rule_times(rtext)
    for tt in (0.03, 0.07, 1.6, tm['end'] - 0.1):
        items.append((f'rule card t={tt:.2f}', {'blur': 6, 'dim': 0.35}, lambda cv, _t, tt=tt: hud.rule_card(cv, 5, rtext, tt)))
    items.append(('alert + pill + red/white tags', {}, lambda cv, t: (hud.tag(cv, 'NEVER OPEN UP', 960, 150, 'alert'),
                                                                    hud.tag(cv, 'NO SMOKE', 360, 420, 'pill', 2.0),
                                                                    hud.tag(cv, 'MICROPHONE', 960, 600, 'red', 0.5),
                                                                    hud.tag(cv, 'BADGE *4471*', 1500, 420, 'white', 0.5),
                                                                    hud.caption(cv, 'Never open up.'))))
    items.append(('speech bubble + waveform panel', {}, lambda cv, t: (hud.speech_bubble(cv, ["You haven't gotten", '*yours yet, have you?*'], 1300, 220, 2.0),
                                                                       hud.waveform_panel(cv, 120, 420, 760, 420, 'SHOULDER RADIO', [
                                                                           {'label': 'PLAY 1', 'color': 'blue', 'seed': 1},
                                                                           {'label': 'PLAY 2', 'color': 'red', 'seed': 2},
                                                                           {'label': 'PLAY 3', 'color': 'red', 'seed': 2, 'progress': 0.55}], 1.3, 0.55))))
    for st in ('calling', 'busy', 'incoming', 'connected', 'voicemail', 'emergency'):
        items.append((f'phone {st}', {}, lambda cv, t, st=st: (hud.phone(cv, st, 3.4, 'MUM' if st != 'voicemail' else 'Unknown', 760, 560, 0.95),
                                                              hud.dispatch_panel(cv, 1120, 300, 'DISPATCH  -  CALL 24-1187',
                                                                                 ['Address: 144 Elm St', 'Units: *2 en route*'], 3.0) if st == 'emergency' else None)))
    items.append(('doorbell hud', {}, lambda cv, t: hud.doorbell_hud(cv, 12.3, motion=(700, 260, 520, 700), talk=True)))
    items.append(('bodycam hud', {}, lambda cv, t: hud.bodycam_hud(cv, 12.3)))
    imgs, labels = [], []
    for lb, fx, fn in items:
        fx2 = dict(fx); fx2.setdefault('dim', 0.25)
        imgs.append(render_frame(bgl, cs, 0.0, 0, lens=None, grade='night_blue', post=fx2, hud=fn)); labels.append(lb)
    p = os.path.join(out, 'sheet_hud.jpg'); cv2.imwrite(p, _sheet(imgs, labels, 4, 400), [cv2.IMWRITE_JPEG_QUALITY, 88]); print(p)


def clip(out, size=(960, 540), fps=60):
    set_render_size(*size)
    film = DemoFilm()
    p = os.path.join(out, 'demo_clip.mp4')
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % size, '-r', str(fps), '-i', '-',
                            '-c:v', 'libx264', '-preset', 'faster', '-crf', '18', '-pix_fmt', 'yuv420p', p], stdin=subprocess.PIPE)
    t0 = time.time()
    for i in range(int(6 * fps)):
        enc.stdin.write(film.frame(i / fps, i).tobytes())
    enc.stdin.close(); enc.wait()
    print(p, '%.1fs' % (time.time() - t0))


def spec_layers():
    """The speed-budget scene: 6 layers, 2 of them DOF-blurred (houses, street), 4 cached + the dynamic figure."""
    return [Layer(40, draw_sky, 'sky', cache='demo_sky', bounds=WIDE, blur=0),
            Layer(9, draw_houses, 'houses', cache='demo_houses', bounds=WIDE),
            Layer(4.5, draw_street, 'street', cache='demo_street', bounds=WIDE),
            Layer(1.4, draw_porch, 'porch', cache='demo_porch', bounds=WIDE, blur=0),
            Layer(1.0, draw_figure, 'officer'),
            Layer(0.6, draw_frame_near, 'frame', cache='demo_frame', bounds=WIDE, blur=0)]


def bench(n=30, threads=None, which=('spec', 'full')):
    """Engine time per frame at 2560x1440 for each lens. 'spec': 6 layers / 2 blurred (+ grade, flash, HUD).
    'full': the 8-layer demo scene with DOF on every layer and a dynamic patrol car."""
    if threads is not None: cv2.setNumThreads(threads)
    set_render_size(2560, 1440)
    res = {}
    for cfg in which:
        for look in ('none', 'lens', 'doorbell', 'doorbell_ir', 'peephole'):
            lk = LOOKS[look]
            cam, _ = MOVES['push']()
            layers = spec_layers() if cfg == 'spec' else make_layers()
            dof = 6.75 if (cfg == 'spec' or look in ('none', 'lens')) else 0.0
            hudf = (lambda cv, t: (hud.doorbell_hud(cv, t), hud.caption(cv, 'You tell him you live here.'))) if look.startswith('doorbell') else \
                (lambda cv, t: (hud.header(cv, 'RULE 1 OF 7'), hud.caption(cv, 'You tell him you live here.')))
            fxf = (lambda t: {'flash': police_flash(t)}) if look in ('none', 'lens') else (lambda t: None)
            for w in range(3):                                         # warm caches
                render_frame(layers, cam.at(w * 0.1), w * 0.1, w, focus=1.0, dof=dof, lens=lk['lens'], grade=lk['grade'], post=fxf(w * 0.1), hud=hudf)
            STATS.clear()
            t0 = time.perf_counter()
            for i in range(n):
                t = 1.0 + i / 60.0
                render_frame(layers, cam.at(t), t, i, focus=1.0, dof=dof, lens=lk['lens'], grade=lk['grade'], post=fxf(t), hud=hudf)
            dt = (time.perf_counter() - t0) / n
            res[(cfg, look)] = (dt, {k: round(v / n * 1000, 1) for k, v in STATS.items() if k != 'frames'})
            print('%-5s %-12s %.3f s/frame' % (cfg, look, dt), res[(cfg, look)][1], flush=True)
    return res


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=OUT); ap.add_argument('--bench', action='store_true'); ap.add_argument('--clip', action='store_true')
    ap.add_argument('--sheets', action='store_true'); ap.add_argument('--hud', action='store_true'); ap.add_argument('--threads', type=int, default=None)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.sheets: sheets(a.out)
    if a.hud: hud_gallery(a.out)
    if a.clip: clip(a.out)
    if a.bench: bench(threads=a.threads)
