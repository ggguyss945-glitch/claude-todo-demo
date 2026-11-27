"""cast_clips.py: acting clips of the ice cream truck film's cast ("If The Ice Cream Truck Plays Its Song In Winter...
DON'T GO OUTSIDE", characters_ice.py), one per scripted action, written to W/cast/clips/ (W = Ice Cream Video/film/_work).

    cd "Vox test/Ice Cream Video/film" && python3 tools/cast_clips.py [names...] [--fps 60] [--strip-only] [--review]

Each clip is 3-6 s at 960x540: <name>.mp4 plus <name>_strip.jpg (8 frames) and a line in clips.json with the actors'
sound events and the contact report (reach misses; feet: the lowest foot point vs the floor). The scenery is a flat
stand-in drawn only to check contact, eyelines and feet: the real sets are in sets.py / sets_ice.py. Every clip stages
its people with Acting.place() and world targets, the way film.py should.
"""
import os, sys, math, json, time, subprocess
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import numpy as np
import cv2
import skia
from engine.core import set_render_size, Pen, CFG, rect, rrect, oval, poly, smooth, text, mix
import characters as CH
if not hasattr(CH, 'ICE_API'):          # until characters.py runs characters_ice.py itself (see CAST.md)
    _ICE = os.path.join(HERE, 'characters_ice.py'); exec(compile(open(_ICE).read(), _ICE, 'exec'), CH.__dict__)

OUT = os.path.join(HERE, '_work', 'cast', 'clips')
FLOOR = 940.0                     # design y of the floor line in most clips
NIGHT = dict(rim='#8fa6e8', rim_a=60, side=1, key=-0.25)
WARM = dict(rim='#ffcf8f', rim_a=55, side=-1, key=0.12)


# ------------------------------------------------------------------------------------------------ stand-in scenery
def room(pen, wall='#2b3040', floor_c='#3a2f2a', y=FLOOR, base=True):
    pen.fill(rect(0, 0, 1920, y), wall)
    pen.linear(rect(0, 0, 1920, y), 0, 0, 0, y, [(0, '#000000', 60), (1, '#000000', 0)])
    pen.fill(rect(0, y, 1920, 1080 - y), floor_c)
    pen.linear(rect(0, y, 1920, 1080 - y), 0, y, 0, 1080, [(0, '#000000', 0), (1, '#000000', 90)])
    if base: pen.fill(rect(0, y - 26, 1920, 26), mix(wall, '#000000', 0.3))
    pen.line(poly([(0, y), (1920, y)], False), 3, '#15161c')


def door(pen, x, y=FLOOR, w=250, h=560, open_=0.0, slot=True, peep=True, c='#5a3f2e', ppm=None):
    """A front door (ppm given: real size 0.9 x 2.03 m, mail slot at 0.95 m, peephole at 1.52 m)."""
    if ppm: w, h = 0.9 * ppm, 2.03 * ppm
    pen.fill(rect(x - w / 2 - 18, y - h - 18, w + 36, h + 18), '#2a2420')
    if open_ > 0.01:
        pen.fill(rect(x - w / 2, y - h, w, h), '#0d0f16')
    dw = w * (1.0 - 0.85 * open_)
    pen.fill(rect(x - w / 2, y - h, dw, h), c)
    pen.line(rect(x - w / 2, y - h, dw, h), 4)
    for k in range(2):
        pen.line(rrect(x - w / 2 + 22, y - h + 30 + k * 270, dw - 44, 230, 6), 3, mix(c, '#000000', 0.35))
    if open_ < 0.3:
        pen.fill(oval(x - w / 2 + dw - 30, y - h * 0.48, 9), '#c9a24a'); pen.line(oval(x - w / 2 + dw - 30, y - h * 0.48, 9), 2.5)
        sy_ = y - h * 0.468; py_ = y - h * 0.75
        if slot:
            pen.fill(rrect(x - w * 0.2, sy_ - 11, w * 0.4, 22, 4), '#c9a24a'); pen.line(rrect(x - w * 0.2, sy_ - 11, w * 0.4, 22, 4), 2.5)
        if peep:
            pen.fill(oval(x, py_, 7), '#c9a24a'); pen.fill(oval(x, py_, 3.5), '#0a0a0a')
    return dict(slot=(x, y - h * 0.468), peep=(x, y - h * 0.75), knob=(x - w / 2 + dw - 30, y - h * 0.48), face=(x, y - h * 0.6))


def door_pts(x, ppm, y=FLOOR):
    """The same points without drawing (for staging the actors before the draw)."""
    h, w = 2.03 * ppm, 0.9 * ppm
    return dict(slot=(x, y - h * 0.468), peep=(x, y - h * 0.75), knob=(x - w / 2 + w - 30, y - h * 0.48))


def window(pen, x, y, w=330, h=360, night=True, curtains=0.0):
    pen.fill(rect(x - w / 2 - 14, y - 14, w + 28, h + 28), '#d9d2c4')
    pen.linear(rect(x - w / 2, y, w, h), 0, y, 0, y + h, [(0, '#0b1230'), (1, '#1d2a4a')] if night else [(0, '#bcd6ef'), (1, '#e8f0f6')])
    pen.line(poly([(x, y), (x, y + h)], False), 8, '#d9d2c4'); pen.line(poly([(x - w / 2, y + h / 2), (x + w / 2, y + h / 2)], False), 8, '#d9d2c4')
    pen.line(rect(x - w / 2 - 14, y - 14, w + 28, h + 28), 3)
    for sd in (-1, 1):
        cw = 40 + (w / 2 - 20) * curtains
        cx = x + sd * (w / 2 + 30) - sd * cw / 2
        pen.fill(rect(cx - cw / 2 - 20 * (1 - curtains), y - 30, cw + 40 * (1 - curtains), h + 70), '#6d3b48')
        pen.line(rect(cx - cw / 2 - 20 * (1 - curtains), y - 30, cw + 40 * (1 - curtains), h + 70), 3)


def armchair(pen, x, seat_y, w=300, back_h=300, y=FLOOR, c='#4f5a6e'):
    pen.fill(rrect(x - w / 2 + 20, seat_y - back_h, w - 40, back_h + 20, 30), mix(c, '#000000', 0.2)); pen.line(rrect(x - w / 2 + 20, seat_y - back_h, w - 40, back_h + 20, 30), 3)
    pen.fill(rrect(x - w / 2, seat_y - 6, w, y - seat_y - 20, 18), c); pen.line(rrect(x - w / 2, seat_y - 6, w, y - seat_y - 20, 18), 3)
    for sd in (-1, 1):
        pen.fill(rrect(x + sd * (w / 2 - 30) - 30, seat_y - 90, 60, y - seat_y + 70, 20), mix(c, '#ffffff', 0.08))
        pen.line(rrect(x + sd * (w / 2 - 30) - 30, seat_y - 90, 60, y - seat_y + 70, 20), 3)


def couch(pen, x, seat_y, w=760, y=FLOOR, c='#6b5a4a'):
    pen.fill(rrect(x - w / 2 + 30, seat_y - 260, w - 60, 280, 30), mix(c, '#000000', 0.2)); pen.line(rrect(x - w / 2 + 30, seat_y - 260, w - 60, 280, 30), 3)
    pen.fill(rrect(x - w / 2, seat_y - 6, w, y - seat_y - 16, 16), c); pen.line(rrect(x - w / 2, seat_y - 6, w, y - seat_y - 16, 16), 3)
    for sd in (-1, 1):
        pen.fill(rrect(x + sd * (w / 2 - 40) - 40, seat_y - 110, 80, y - seat_y + 92, 24), mix(c, '#ffffff', 0.08))
        pen.line(rrect(x + sd * (w / 2 - 40) - 40, seat_y - 110, 80, y - seat_y + 92, 24), 3)


def table(pen, x, top, w=360, y=FLOOR, c='#7a5236', depth=26):
    """A kitchen table seen a little from above: back legs, the top surface, the edge and apron, front legs."""
    dk = mix(c, '#000000', 0.35)
    for sd in (-1, 1):                                                  # back legs (set in, darker)
        pen.fill(rect(x + sd * (w / 2 - 40) - 8, top - depth + 20, 16, y - top - 24), mix(c, '#000000', 0.5))
    surf = poly([(x - w / 2 + 18, top - depth), (x + w / 2 - 18, top - depth), (x + w / 2, top), (x - w / 2, top)], True)
    pen.fill(surf, mix(c, '#ffffff', 0.12)); pen.line(surf, 3)
    pen.fill(rect(x - w / 2, top, w, 18), c); pen.line(rect(x - w / 2, top, w, 18), 3)
    pen.fill(rect(x - w / 2 + 14, top + 18, w - 28, 22), dk); pen.line(rect(x - w / 2 + 14, top + 18, w - 28, 22), 2.5)
    for sd in (-1, 1):                                                  # front legs
        lg = rect(x + sd * (w / 2 - 26) - 10, top + 18, 20, y - top - 18)
        pen.fill(lg, mix(c, '#000000', 0.22)); pen.line(lg, 2.5)


def stairs(pen, x, n=6, rise=62, run=90, y=FLOOR, w=520, dirn=1):
    for k in range(n):
        x0 = x + dirn * k * run
        pen.fill(rect(min(x0, x0 + dirn * w), y - (k + 1) * rise, w, rise), '#4a3426' if k % 2 else '#553c2c')
        pen.line(rect(min(x0, x0 + dirn * w), y - (k + 1) * rise, w, rise), 2.5)


def tub(pen, x, y, w=620, h=230, front=True):
    p = rrect(x - w / 2, y - h, w, h, 40)
    pen.fill(p, '#e9ebee'); pen.linear(p, 0, y - h, 0, y, [(0, '#ffffff', 0), (1, '#9aa4b0', 140)]); pen.line(p, 4)
    pen.fill(rrect(x - w / 2 + 24, y - h + 18, w - 48, 30, 14), '#8a94a2')


def chest(pen, x, y, w=300, h=170, lid=0.0):
    pen.fill(rect(x - w / 2, y - h, w, h), '#8a5a3a'); pen.line(rect(x - w / 2, y - h, w, h), 3)
    for k in range(3): pen.line(poly([(x - w / 2, y - h + 40 + k * 44), (x + w / 2, y - h + 40 + k * 44)], False), 2, '#5a3a22')
    pen.fill(rect(x - w / 2 - 6, y - h - 22 - 120 * lid, w + 12, 26), '#7a4a2e'); pen.line(rect(x - w / 2 - 6, y - h - 22 - 120 * lid, w + 12, 26), 3)


def barrel(pen, x, y, fire=0.0, t=0.0):
    pen.fill(rrect(x - 90, y - 230, 180, 230, 14), '#5a5e66'); pen.line(rrect(x - 90, y - 230, 180, 230, 14), 3)
    for k in range(3): pen.line(poly([(x - 90, y - 60 - k * 60), (x + 90, y - 60 - k * 60)], False), 3, '#3a3d44')
    if fire > 0: pen.glow(x, y - 250, 140, '#ff9a3a', 160 * fire)


def treeline(pen, y=760, t=0.0):
    pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 1080, [(0, '#060a18'), (0.6, '#0e1730'), (1, '#121a28')])
    pen.fill(oval(1500, 190, 70), '#e8ecf2'); pen.glow(1500, 190, 260, '#9fb6ff', 70)
    for k in range(26):
        x = k * 80 - 20; h = 420 + 140 * CH.hash01(k, 3)
        pen.fill(poly([(x - 70, y + 40), (x, y - h), (x + 70, y + 40)]), '#05070d')
    pen.fill(rect(0, y + 20, 1920, 1080 - y - 20), '#0b1220')


# ------------------------------------------------------------------------------------------------ clip registry
CLIPS = {}


def clip(name, dur, desc):
    def deco(f):
        CLIPS[name] = (f, dur, desc); return f
    return deco


def ppm_for(h_px, who):
    return h_px / CH.CAST[who]['m']


def actor(who, x, y, ppm, seed=1, expr='neutral', **kw):
    a = CH.Acting(who, seed=seed, height=CH.height_px(who, ppm), expr=expr, **kw)
    a.place(x, y)
    return a


def fig(pen, a, t, light=None, x=None, y=None):
    CH.draw(pen, a.who, a.x0 if x is None else x, a.y0 if y is None else y, a.height, a.at(t), light=light, t=t)


# ------------------------------------------------------------------------------------------------ rendering
def _strip(frames, path, n=8, times=None):
    idx = np.linspace(0, len(frames) - 1, n).astype(int)
    tiles = [cv2.resize(frames[i], (480, 270), interpolation=cv2.INTER_AREA) for i in idx]
    rows = [np.hstack(tiles[k:k + 4]) for k in range(0, n, 4)]
    img = np.vstack(rows)
    for j, i in enumerate(idx):
        cv2.putText(img, '%.2fs' % (times[i] if times else i / FPS), (8 + 480 * (j % 4), 20 + 270 * (j // 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, 86])


FPS = 60


def render(name, strip_only=False):
    f, dur, desc = CLIPS[name]
    set_render_size(960, 540)
    S = f()
    draw = S['draw']
    os.makedirs(OUT, exist_ok=True)
    n = int(round(dur * FPS))
    ts = [i / FPS for i in range(n)]
    if strip_only: ts = [ts[i] for i in np.linspace(0, n - 1, 8).astype(int)]
    frames = []
    surf = skia.Surface(CFG.rw, CFG.rh)
    cv = surf.getCanvas()
    proc = None
    if not strip_only:
        proc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '960x540', '-r', str(FPS),
                                 '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
                                 os.path.join(OUT, name + '.mp4')], stdin=subprocess.PIPE)
    t_r = time.time()
    feet = []
    for t in ts:
        cv.save(); cv.clear(skia.Color(20, 22, 30)); cv.scale(CFG.k, CFG.k)
        draw(Pen(cv), t)
        cv.restore()
        img = surf.makeImageSnapshot().toarray()[:, :, :3]
        rgb = img[:, :, ::-1].copy()
        if proc: proc.stdin.write(rgb.tobytes())
        frames.append(img)
        for a in S.get('grounded', []):                     # feet on the floor: the lower planted sole's gap (px)
            feet.append(a.foot_gap(t))
    if proc:
        proc.stdin.close(); proc.wait()
    _strip(frames, os.path.join(OUT, name + '_strip.jpg'), times=ts)
    misses = []
    evs = []
    for a in S.get('actors', []):
        misses += [(a.who,) + m for m in getattr(a, 'misses', [])]
        evs += [dict(e, who=a.who) for e in a.events]
    rep = dict(name=name, desc=desc, dur=dur, frames=len(ts), sec_per_frame=round((time.time() - t_r) / max(1, len(ts)), 4),
               reach_misses=len(misses), worst_miss=max([m[-1] for m in misses], default=0.0),
               feet_off_floor_px=round(max(feet), 2) if feet else None, events=sorted(evs, key=lambda e: e['t']))
    return rep


def review(names, per=3, tag='review'):
    """Stack clip strips into review sheets (per strips each) for checking by eye: W/cast/clips/<tag>_NN.jpg."""
    out = []
    for i in range(0, len(names), per):
        ims = []
        for nm in names[i:i + per]:
            p = os.path.join(OUT, nm + '_strip.jpg')
            if not os.path.exists(p): continue
            im = cv2.imread(p)
            im = cv2.resize(im, (1920, 540))
            cv2.putText(im, nm, (1500, 528), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (120, 230, 255), 2, cv2.LINE_AA)
            ims.append(im)
        if ims:
            path = os.path.join(OUT, '%s_%02d.jpg' % (tag, i // per))
            cv2.imwrite(path, np.vstack(ims), [cv2.IMWRITE_JPEG_QUALITY, 80]); out.append(path)
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    global FPS
    if '--fps' in sys.argv: FPS = int(sys.argv[sys.argv.index('--fps') + 1]); args = [a for a in args if a != str(FPS)]
    names = args or list(CLIPS)
    rpath = os.environ.get('CLIPS_JSON') or os.path.join(OUT, 'clips.json')
    allr = {}
    if os.path.exists(rpath):
        try: allr = json.load(open(rpath))
        except Exception: allr = {}
    for nm in names:
        try:
            r = render(nm, '--strip-only' in sys.argv)
        except Exception:
            import traceback; print('FAILED', nm); traceback.print_exc(limit=-3); continue
        allr[nm] = r
        print('%-28s %4.1fs  %.3f s/frame  misses %d (worst %.1f)  feet %s' % (nm, r['dur'], r['sec_per_frame'], r['reach_misses'],
                                                                           r['worst_miss'], r['feet_off_floor_px']))
    json.dump(allr, open(rpath, 'w'), indent=1)
    if '--review' in sys.argv:
        for p in review(names): print('review', p)


from engine.core import clamp, ease_out_cubic, ease_in_out, union      # noqa: E402
PI = math.pi
INF = float('inf')
from engine.core import ease_out_back, hash01      # noqa: E402

NIGHTI = dict(rim='#9fb8ff', rim_a=70, side=1, key=-0.25)            # frost-blue moonlight
PINKW = dict(rim='#ff9ccc', rim_a=90, side=-1, key=-0.2)             # his warm pink window
BEACON = dict(rim='#ffa040', rim_a=80, side=1, key=-0.2)             # the plow's orange light
MORNING = dict(rim='#ffe2a8', rim_a=55, side=-1, key=0.2)


# ------------------------------------------------------------------------------------------------ winter stand-ins
def snow_street(pen, hz=600, glow=None):
    pen.linear(rect(0, 0, 1920, hz), 0, 0, 0, hz, [(0, '#05070f'), (1, '#16203a')])
    pen.fill(rect(0, hz, 1920, 1080 - hz), '#c9d6ea')
    pen.linear(rect(0, hz, 1920, 1080 - hz), 0, hz, 0, 1080, [(0, '#5a6a8c', 255), (1, '#8a9cbc', 255)])
    if glow: pen.glow(glow[0], glow[1], glow[2], '#ff8cc0', glow[3])


def truck(pen, x, sill_y, ppm, win=1.0, lit=True, bunting=True, mitten_lina=0.0, red_only=False):
    """The step van's side round the serving window (stand-in): pink-and-white stripes, a warm pink window (nothing of
    the interior beyond it), mitten bunting across the top of the window (the oldest, small and RED, at the left), the
    frosted snowflake on the roof. win = how far the window has slid open (0 shut .. 1 open). Returns geometry."""
    W, H = 1.25 * ppm, 0.95 * ppm
    x0, x1 = x - W / 2, x + W / 2
    top = sill_y - H
    roof = top - 0.45 * ppm
    body = rect(x - 2.3 * ppm, roof, 4.6 * ppm, sill_y + 1.25 * ppm - roof)
    hole = rect(x0, top, W, H)
    g = dict(x0=x0, x1=x1, top=top, sill=sill_y, roof=roof, hole=hole, body=body, floor=sill_y + 1.25 * ppm)
    return g


def truck_back(pen, g, ppm, lit=True):
    """What is seen through the open window: only warm pink light (never the interior)."""
    pen.fill(g['hole'], '#ff9fca' if lit else '#3a2030')
    pen.linear(g['hole'], 0, g['top'], 0, g['sill'], [(0, '#ffd2e6', 200), (1, '#d8588e', 220)])


def truck_front(pen, g, ppm, win=1.0, t=0.0, bunting=True, mitten_lina=0.0, red_only=False, legs_holes=False):
    hole = g['hole']
    from engine.core import minus
    wall = minus(g['body'], hole)
    pen.fill(wall, '#f4eef1')
    n = 22
    bx0 = g['body'].getBounds().left(); bw = g['body'].getBounds().width()
    for k in range(n):
        if k % 2 == 0: continue
        pen.fill(minus(rect(bx0 + k * bw / n, g['roof'], bw / n, g['floor'] - g['roof']), hole), '#e58fb4')
    pen.linear(wall, 0, g['roof'], 0, g['floor'], [(0, '#000000', 0), (1, '#000000', 110)])
    pen.line(wall, 4, '#1a1418')
    # the sliding pane: slides LEFT to open
    Wd = g['x1'] - g['x0']
    pane = rect(g['x0'] + Wd * (1 - win) * 0.0 - Wd * win * 0.0, g['top'], Wd * (1 - win) + 2, g['sill'] - g['top'])
    pane = rect(g['x1'] - Wd * (1 - win), g['top'], Wd * (1 - win), g['sill'] - g['top'])
    if win < 0.99:
        pen.fill(pane, '#ffc9df', 120); pen.line(pane, 4, '#c9c9d4')
    pen.fill(rect(g['x0'] - 20, g['sill'] - 6, Wd + 40, 22), '#d9dde4'); pen.line(rect(g['x0'] - 20, g['sill'] - 6, Wd + 40, 22), 3, '#1a1418')
    # snowflake on the roof (chrome horn at its centre)
    cx, cy = (g['x0'] + g['x1']) / 2, g['roof'] - 0.35 * ppm
    for k in range(3):
        a = PI / 2 + k * PI / 3
        pen.line(poly([(cx - math.cos(a) * 0.4 * ppm, cy - math.sin(a) * 0.4 * ppm), (cx + math.cos(a) * 0.4 * ppm, cy + math.sin(a) * 0.4 * ppm)], False), 0.07 * ppm, '#e8f2ff')
    pen.fill(oval(cx, cy, 0.08 * ppm, 0.08 * ppm), '#c9d1dc')
    if bunting:
        y_s = g['top'] + 0.08 * ppm
        pts = [(g['x0'] + Wd * u, y_s + math.sin(PI * u) * 0.07 * ppm) for u in np.linspace(0, 1, 12)]
        pen.line(smooth(pts, False), 2.5, '#efe7d8')
        cols = ['#c8322f'] + ['#6a8ac0', '#7aa86a', '#c9a24a', '#8a6aa8', '#4aa0a0', '#c07a5a', '#5a7aa0']
        for k in range(8 if not red_only else 1):
            u = 0.06 + k * 0.115
            px, py = g['x0'] + Wd * u, y_s + math.sin(PI * u) * 0.07 * ppm
            sw = math.sin(t * 1.3 + k) * 4
            m = rrect(px - 0.045 * ppm + sw, py + 2, 0.09 * ppm, (0.10 if k else 0.08) * ppm, 0.03 * ppm)
            pen.fill(m, cols[k]); pen.line(m, 2, '#1a1418')
        if mitten_lina > 0.01:
            u = 0.97; px, py = g['x0'] + Wd * u, y_s + 0.01 * ppm
            m = rrect(px - 0.045 * ppm, py + 2 - (1 - mitten_lina) * 0.4 * ppm, 0.09 * ppm, 0.1 * ppm, 0.03 * ppm)
            pen.fill(m, '#e87aa4'); pen.line(m, 2, '#1a1418')


def shiver_in_window(pen, a, t, g, light=PINKW, lean=False):
    """Draw him behind the window: hidden by the wall below the sill (and beside the window unless he leans out)."""
    from engine.core import minus
    hidden = rect(g['body'].getBounds().left(), g['sill'] + 10, g['body'].getBounds().width(), 2000)
    if not lean: hidden = union(hidden, minus(g['body'], g['hole']))
    pen.cv.save(); pen.cv.clipPath(hidden, skia.ClipOp.kDifference, True)
    fig(pen, a, t, light)
    pen.cv.restore()


def snow_holes(pen, a, t, ys, keep=None, t0=0.0, tol=8.0, r=5.0):
    """Needle holes left in the snow where his tips touched (from the actor's leg tips at ground level). ys: the snow y
    (a number or a function of x)."""
    gy = ys if callable(ys) else (lambda x, v=float(ys): v)
    seen = []
    for tt in np.arange(t0, t + 1e-6, 1.0 / 15.0):
        for i in range(8):
            x, y = a.where(float(tt), 'leg%d' % i)
            if abs(y - gy(x)) < tol and all(abs(x - q) > 2 * r for q in seen):
                seen.append(x)
                pen.fill(oval(x, gy(x) + 1.5, r * 1.6, r * 0.55), '#2a3550', 200)
                pen.fill(oval(x, gy(x) + 0.5, r * 0.8, r * 0.3), '#0e1322', 230)


def _taper(pts, w0, w1):
    """A tapered spindle between two points (w0 at the first, w1 at the second), rounded ends."""
    (x0, y0), (x1, y1) = pts
    d = math.hypot(x1 - x0, y1 - y0) or 1.0
    nx, ny = -(y1 - y0) / d, (x1 - x0) / d
    q = [(x0 + nx * w0 / 2, y0 + ny * w0 / 2), ((x0 + x1) / 2 + nx * (w0 + w1) / 4 * 1.08, (y0 + y1) / 2 + ny * (w0 + w1) / 4 * 1.08),
         (x1 + nx * w1 / 2, y1 + ny * w1 / 2), (x1 + (x1 - x0) / d * w1 * 0.6, y1 + (y1 - y0) / d * w1 * 0.6), (x1 - nx * w1 / 2, y1 - ny * w1 / 2),
         ((x0 + x1) / 2 - nx * (w0 + w1) / 4 * 1.08, (y0 + y1) / 2 - ny * (w0 + w1) / 4 * 1.08), (x0 - nx * w0 / 2, y0 - ny * w0 / 2)]
    return poly(q, True)


def sh(x, y, ppm, seed=1):
    a = CH.Acting('shiver', seed=seed, height=CH.height_px('shiver', ppm))
    a.place(x, y)
    return a


# ================================================================================================ MISTER SHIVER
@clip('sh_drive_by_lean', 5.0, 'The truck parked: he leans out of the warm pink window, bald, chalk-white, tiny blue eyes, the too-wide smile; a slow over-long wave; he looks across at Kessler\'s window like an old friend, then at Lina through the crack, and the smile gets wider. No breath.')
def _c_sh_drive_by():
    ppm = 520.0
    g = truck(None, 960, 760, ppm)
    a = sh(960, g['floor'], ppm)
    a.set(-1.0, None, 0.01, ws_bend=0.22)
    a.face(0.0, 0.0)
    a.slow_wave(0.4, 4.6, side=1)
    a.look_at(1.4, (-600, 420), dur=0.9)
    a.look_at(3.0, (2600, 700), dur=0.9)
    a.set(3.4, None, 0.8, sh_smile=0.25)
    def draw(pen, t):
        snow_street(pen, 900)
        truck_back(pen, g, ppm)
        shiver_in_window(pen, a, t, g, lean=True)
        truck_front(pen, g, ppm, 1.0, t)
    return dict(draw=draw, actors=[a])


@clip('sh_slide_window', 3.5, 'The serving window slides open: his glove on the pane pushes it aside; warm pink light; he leans into the gap, smiling down.')
def _c_sh_slide():
    ppm = 330.0
    g = truck(None, 980, 640, ppm)
    a = sh(1010, g['floor'], ppm)
    Wd = g['x1'] - g['x0']
    def win(t): return ease_in_out(clamp((t - 0.6) / 1.2))
    def handle(t): return (g['x1'] - Wd * (1 - win(t)) + 30, (g['top'] + g['sill']) / 2)
    a.reach_to(0.2, -1, handle, t1=2.1, dur=0.4, z=30.0)
    a.set(2.0, None, 0.9, ws_bend=0.28)
    a.look_at(2.2, (980, 1400), dur=0.8)
    def draw(pen, t):
        snow_street(pen, 760)
        truck_back(pen, g, ppm)
        shiver_in_window(pen, a, t, g, lean=t > 2.0)
        truck_front(pen, g, ppm, win(t), t)
    return dict(draw=draw, actors=[a])


@clip('sh_lean_down_reach', 5.5, '"Mister Shiver leans down. Down. Further than a man can bend." His glove reaches down for Lina\'s bare hand; an inch from his fingers Adam yanks her into his arms. He keeps smiling, keeps waving.')
def _c_sh_down():
    ppm = 300.0
    g = truck(None, 700, 470, ppm)
    a = sh(700, g['floor'], ppm)
    a.set(-1.0, None, 0.01, sh_nolegs=1.0)
    lina = actor('lina', 1010, 1010, ppm, seed=3, expr='dazed')
    adam = actor('adam', 0, 1010, ppm, seed=4, expr='fear')
    lina.face(-0.6)
    lina.look_at(0.0, (a, 'eyes'), dur=0.4)
    lina.reach_to(0.6, -1, (860, 720), t1=3.0, dur=1.0, z=60.0, shape='reach')
    def bend(P, t):                       # down... and down: two slow beats, past a man's waist
        u1 = ease_in_out(clamp((t - 0.3) / 1.0)); u2 = ease_in_out(clamp((t - 1.6) / 1.1))
        P.ws_bend = max(P.ws_bend, min(0.75, 0.45 * u1 + 0.30 * u2)); P.ws_face_up = 0.95   # a HINGE over the sill, never flipped
        P.sh_neck += 60.0 * u2                                                         # the second 'Down.' is the neck
    a._add(-INF, None, bend)
    def tgt(t):                                       # palm down, fingers open, ~55 px short of her hand: every frame
        hx, hy = lina.where(min(t, 3.0), 'hand_r'); return (hx - 55, hy - 30)
    def tgt2(t):                                      # she is pulled away: the glove follows ~40 cm more and closes on air
        hx, hy = lina.where(min(t, 3.0), 'hand_r'); return (hx - 55 + 120 * ease_in_out(clamp((t - 3.0) / 0.5)), hy - 30 + 40 * ease_in_out(clamp((t - 3.0) / 0.5)))
    a.reach_far(1.8, 1, tgt2, t1=4.6, dur=1.2, z=30.0, fade=0.9)
    a.reach_to(1.0, -1, (g['x0'] + 60, g['sill'] - 4), dur=0.5, z=10.0)     # the other glove braces on the sill, fingers splayed
    a.look_at(0.4, (lina, 'head'), dur=0.6)
    a.look_at(3.25, (adam, 'head'), dur=0.15)                                  # the head snaps to Adam
    a.menace(0.0, 5.5)
    adam.look_at(0.4, (lina, 'head'), dur=0.3)
    adam.set(1.55, 1.9, 0.12, crouch=0.06)                                     # anticipation before the run
    adam.run(1.9, 2.9, 1600, 1150, surface='snow')
    adam.face(-0.6)
    adam.fear_body(0.0, 1.8, k=0.7)
    adam.reach_to(2.8, -1, (lina, 'chest'), dur=0.25, z=60.0)
    def lina_pull(P, t):
        u = ease_in_out(clamp((t - 3.0) / 0.3)); P.dx += 90 * u
    lina._add(3.0, None, lina_pull)
    lina.expr('fear', 3.0)
    # wide (establishing, <= 1.5 s), then CUT to a medium (ppm 300 -> 700) on the glove, her hand and her face
    hx_, hy_ = lina.where(2.4, 'head'); gx_, gy_ = tgt(2.4); sx_, sy_ = a.where(2.4, 'eyes')
    span_ = abs(hy_ - sy_) + 0.55 * ppm                 # his face (top) to her face (bottom) both in the frame
    zm = min(700.0 / 300.0, 1080.0 * 0.92 / span_)
    mcx, mcy = (hx_ + gx_ + sx_) / 3.0 + 40.0, (hy_ + sy_) / 2.0 + 0.05 * ppm

    def draw(pen, t):
        med = t >= 1.5
        if med:
            pen.cv.save(); pen.cv.translate(960, 540); pen.cv.scale(zm, zm); pen.cv.translate(-mcx, -mcy)
        snow_street(pen, 700)
        truck_back(pen, g, ppm)
        truck_front(pen, g, ppm, 1.0, t)
        fig(pen, a, t, PINKW)
        fig(pen, lina, t, PINKW); fig(pen, adam, t, PINKW)
        if med: pen.cv.restore()
    return dict(draw=draw, actors=[a, lina, adam], grounded=[lina, adam])


@clip('sh_glimpse_flicker', 3.0, 'The streetlight flickers. For one flicker, his face is long and white. Red eyes. Then the smile again.')
def _c_sh_glimpse():
    ppm = 520.0
    g = truck(None, 960, 780, ppm)
    a = sh(960, g['floor'], ppm)
    a.lean_to(0.0, (960, 700), gap=10.0, dur=0.01)
    a.face(0.0, -0.25)
    a.set(1.25, 1.5, 0.04, h_nod=0.0)
    a.glimpse(1.30, 0.15)
    def draw(pen, t):
        on = 0.25 if 1.25 < t < 1.5 else 1.0
        gl = 1.3 <= t < 1.45
        pen.fill(rect(0, 0, 1920, 1080), '#0a0c16')
        if gl: pen.cv.save(); pen.cv.translate(960, 420); pen.cv.scale(1.1, 1.1); pen.cv.translate(-960, -420)
        truck_back(pen, g, ppm)
        shiver_in_window(pen, a, t, g, light=dict(PINKW, rim_a=int(90 * on)), lean=True)
        truck_front(pen, g, ppm, 1.0, t)
        if 1.3 <= t < 1.45: pen.fill(rect(0, 0, 1920, 1080), '#cfe0ff', 40)
        pen.fill(rect(0, 0, 1920, 1080), '#000000', int(150 * (1 - on)))
        if gl:                                        # the red eyes stay at full strength over the dark
            for p_ in ('eye_l', 'eye_r'):
                ex, ey = a.where(t, p_)
                pen.glow(ex, ey, 26, '#ff2a2a', 200); pen.fill(oval(ex, ey, 7, 6), '#ff2a2a'); pen.fill(oval(ex - 2, ey - 2, 2.5, 2.2), '#ffd0c8')
            pen.cv.restore()
    return dict(draw=draw, actors=[a])


def _transform_times(t0=0.3, step=0.62):
    return [t0 + k * step for k in range(8)]


@clip('sh_transform_face', 5.0, 'THE TRANSFORMATION, close, at the window while he keeps waving: the smile keeps going past the cheeks; the skin pulls long, white, hard, a mask of bone; the little blue eyes sink into the dark... and come back red; the jaw drops to the chest: no throat, just dark, and icicle teeth.')
def _c_sh_transform_face():
    # over Adam's shoulder (his red hat and shoulder in the left fifth): the window frame and the ends of the mitten
    # bunting at the edges; the head pushes from ~30% to ~55% of the frame across steps 1-5, the eyes a third down; the
    # body is cut by the REAL sill and truck wall (never a half body floating on pink)
    ppm = 1000.0
    a = sh(1000, 3000, ppm)
    a.set(-1.0, None, 0.01, ws_bend=0.12)
    a.face(-0.14, 0.05)                                  # toward Adam (frame left)
    a.slow_wave(0.0, 5.0, side=1)
    ts = [0.2, 1.0, 1.9, 2.6, 3.2, 4.2, 9.0, 9.5]
    a.transform(0.2, ts)

    tt_ = np.linspace(0.0, 5.0, 201)
    # the framing is measured on the UPPER mask only (crown to the mouth's upper rim), never the dropping jaw; three
    # cuts IN (medium -> close -> close-up), each tighter, and inside each shot the camera only pushes in
    ml_ = np.array([max(a.where(x, 'mouth')[1] - a.where(x, 'crown')[1], 1.0) for x in tt_])
    def frac(x):
        if x < 1.0: return 0.28
        if x < 2.6: return 0.36 + 0.06 * ease_in_out(clamp((x - 1.0) / 1.4))
        if x < 3.2: return 0.46
        return 0.50 + 0.04 * ease_in_out(clamp((x - 3.2) / 1.6))
    zz_ = np.maximum.accumulate(np.array([frac(x) for x in tt_]) * 1080.0 / ml_)
    z0_ = float(zz_[0])

    def zf(t):           # monotonic: the head never shrinks in the frame; the jaw drops off the bottom at step 5
        return float(np.interp(t, tt_, zz_))
    ex0 = a.where(0.5, 'eyes')[0]
    zend = zf(4.9)
    sill = a.where(4.9, 'chin')[1] + 70.0 / zend
    g = truck(None, ex0 + 60, sill, ppm)
    Hh = 1700.0
    adam = actor('adam', 150, 640 + Hh, Hh / 1.5 * 1.0, seed=4, expr='fear')
    adam.set(-1.0, None, 0.01, turn=1.62)
    adam.fear_body(0.0)
    lina = actor('lina', 150, 640 + Hh, Hh / 1.5 * 1.0, seed=5, expr='fear')
    adam.carry(0.0, lina)                               # Lina held to his chest: her pom-pom hat and cheek at his shoulder
    lina.look_at(0.0, lambda t: a.where(t, 'eyes'))

    def flinch(P, t):    # the flinch on the red eyes: the head pulls back 25 px, the shoulders rise 6 deg
        k = math.sin(PI * clamp((t - 3.25) / 0.5)) if t < 3.5 else max(0.0, 1.0 - (t - 3.5) / 1.2) * 0.6
        k = max(0.0, k) if t >= 3.25 else 0.0
        P.dx -= 25.0 * k; P.tilt -= 6.0 * k; P.hunch = max(P.hunch, 0.5 * k)
    CH._acting_post(adam, 3.25, None, flinch)

    def draw(pen, t):
        z = zf(t)
        ey = a.where(t, 'eyes')[1]
        pen.fill(rect(0, 0, 1920, 1080), '#0a0c16')
        pen.cv.save(); pen.cv.translate(1060, 360); pen.cv.scale(z, z); pen.cv.translate(-ex0, -ey)
        pen.linear(rect(ex0 - 4000, ey - 4000, 8000, 8000), 0, ey - 2000, 0, ey + 2000, [(0, '#05070f'), (1, '#16203a')])
        truck_back(pen, g, ppm)
        truck_front(pen, g, ppm, 1.0, t)                  # the bunting behind his head: the face is never crossed
        pen.cv.save(); pen.cv.clipPath(g['hole'], skia.ClipOp.kIntersect, True)
        pen.cv.clipPath(rect(g['x0'] - 50, g['sill'] - 6, 6000, 4000), skia.ClipOp.kDifference, True)
        fig(pen, a, t, PINKW)
        pen.cv.restore()
        pen.cv.restore()
        ka = 1.0 + 0.35 * (z / z0_ - 1.0)                 # Adam in the same world: a parallax of 0.35 (near the lens)
        pen.cv.save(); pen.cv.translate(150, 1080); pen.cv.scale(ka, ka); pen.cv.translate(-150 - 60 * (ka - 1), -1080)
        CH.draw_carry_child(pen, adam, lina, t, PINKW)   # foreground: Adam's hat and shoulder with Lina, lit pink
        pen.cv.restore()
    return dict(draw=draw, actors=[a])


@clip('sh_transform_legs', 5.0, 'Behind him the striped uniform bulges (it swells and quivers), splits along the stripes, and a long brown leg punches out, jointed like a spider\'s, one PAIR per click (a 3/4 medium on the split, then the wide): Click. Another. Click. Click. They plant on the truck roof beside the snowflake, the knees high over the roof. The song keeps playing; the warm pink window behind him.')
def _c_sh_transform_legs():
    ts = [-6.0, -5.5, -5.0, -4.5, -4.0, 0.0, 1.4, 3.6]
    # shot A (0 - 1.5 s): a 3/4 medium on his shoulders and back: the swell, the quiver, the split, the first pair
    ppm_a = 900.0
    am = sh(900, 1080 + 1.05 * ppm_a, ppm_a)
    am.set(-1.0, None, 0.01, ws_bend=0.30, turn=0.80)           # his shoulder and back to us: we watch the back swell and split
    am.face(-0.55, 0.05)                                         # the mask still turned to us (no wave here: he goes rigid)
    am.transform(-6.0, ts)
    # shot B (1.4 - 4.0 s): the MEDIUM-WIDE (bible step 6, "hold on the full monster"): window + head, the mask >= 22% of the
    # frame, the femurs and knees bracketing the face, legs out of the frame edges; shot C (4.0 - 5.0 s): a tight wide
    # (truck ~70% of the frame) for "they plant on the truck roof"
    def setup(ppm, cx, sill):
        g = truck(None, cx, sill, ppm)
        a = sh(cx, g['floor'] - 0.40 * ppm, ppm)         # risen in the window: the dropped jaw clears the sill
        a.set(-1.0, None, 0.01, ws_bend=0.2)
        a.slow_wave(0.0, 5.0, side=1)
        a.transform(-6.0, ts)
        tg = {i: (cx + (1 if i % 2 == 0 else -1) * (0.55 + 0.48 * (i // 2)) * ppm, g['roof'] + 4) for i in range(8)}   # all ON the roof span
        a.legs_plant(-7.0, tg, stagger=0.0, dur=0.01)
        return g, a
    g0, a0 = setup(215.0, 960, 860)                      # measure the mask at a reference scale
    hx, hy = a0.where(3.0, 'crown'); cx_, cy_ = a0.where(3.0, 'chin')
    mask0 = abs(cy_ - hy)
    ppm_b = 635.0                                       # the mask >= 25% of the frame, the legs out of the frame edges
    gb, ab = setup(ppm_b, 960, 860)
    hx, hy = ab.where(3.0, 'crown')
    gb, ab = setup(ppm_b, 960, 860 + (150 - hy))         # the crown high: the dropped jaw and the maw show over the sill
    ppm_c = 400.0                                       # the tight wide (<= 0.8 s): roof, tips beside the snowflake, mask >= 15%
    gc, ac = setup(ppm_c, 960, 1000)
    hx, hy = ac.where(4.6, 'crown')
    gc, ac = setup(ppm_c, 960, 1000 + (330 - hy))
    ga = truck(None, 1100, 1125, ppm_a)                  # shot A: the window frame edge, bunting end and striped wall behind him
    def draw(pen, t):
        if t < 1.4:
            pen.fill(rect(0, 0, 1920, 1080), '#0a0c16')
            truck_back(pen, ga, ppm_a)
            truck_front(pen, ga, ppm_a, 1.0, t)
            pen.glow(1000, 500, 800, '#ff9fca', 70)         # the pink window spill on the wall and his shoulder
            fig(pen, am, t, PINKW)
            return
        g, a, ppm = (gb, ab, ppm_b) if t < 4.2 else (gc, ac, ppm_c)
        snow_street(pen, 960)
        truck_back(pen, g, ppm)
        truck_front(pen, g, ppm, 1.0, t)
        pen.cv.save(); pen.cv.clipPath(rect(0, g['sill'] + 10, 1920, 2000), skia.ClipOp.kDifference, True)
        fig(pen, a, t, PINKW)
        pen.cv.restore()
    return dict(draw=draw, actors=[ab])


@clip('sh_pour_out', 4.0, 'He pours out of the window. Head first. Legs last. Four legs grip the roof and the window frame; he curls over the sill neck first, the gloves plant in the snow, the legs haul his hips out, the last four legs unfold out of the window and everything steps down into the snow.')
def _c_sh_pour():
    ppm = 290.0                                   # the window ~26% of the frame, the snow line at 78%: everything lands ON snow
    GY = 840.0
    g = truck(None, 960, GY - 0.30 * ppm - 1.25 * ppm, ppm)
    a = sh(960, g['floor'], ppm)
    a.set(-1.0, None, 0.01, sh_m=1.0)
    a.face(0.1, 0.0)
    a.pour_out(0.3, 3.4, sill_dy=g['sill'] - g['floor'], ground_dy=GY - g['floor'], forward=0.6, roof_dy=g['roof'] - g['floor'],
               frame_w=g['x1'] - g['x0'], ground=lambda x: GY)
    hx0, hy0 = a.where(3.4, 'eyes')

    def draw(pen, t):
        zk = 1.0 + 0.25 * ease_in_out(clamp((t - 2.8) / 1.2))       # he comes at the lens: a short push over the last 1.2 s
        pen.cv.save(); pen.cv.translate(hx0, hy0); pen.cv.scale(zk, zk); pen.cv.translate(-hx0, -hy0)
        snow_street(pen, GY)
        for wx in (960 - 1.55 * ppm, 960 + 1.45 * ppm):             # the truck's lower body: shadow, wheels on the snow
            pen.fill(oval(wx, GY - 0.02 * ppm, 0.42 * ppm, 0.07 * ppm), '#1a2236', 160)
        pen.fill(rect(960 - 2.3 * ppm, g['floor'] - 4, 4.6 * ppm, GY - g['floor'] - 0.08 * ppm), '#2a2230')
        for wx in (960 - 1.55 * ppm, 960 + 1.45 * ppm):
            pen.fill(oval(wx, GY - 0.27 * ppm, 0.27 * ppm, 0.27 * ppm), '#15151c'); pen.fill(oval(wx, GY - 0.27 * ppm, 0.12 * ppm, 0.12 * ppm), '#8a8f9c')
        snow_holes(pen, a, t, GY, t0=0.3)
        truck_back(pen, g, ppm)
        pen.cv.save(); pen.cv.clipPath(g['hole'], skia.ClipOp.kIntersect, True)       # pass 1: seen through the window
        P = a.at(t); P.sh_nolegs = 0.0
        CH.draw(pen, a.who, a.x0, a.y0, a.height, P, light=PINKW, t=t)
        pen.cv.restore()
        truck_front(pen, g, ppm, 1.0, t)
        hide = a.at(t).__dict__.get('_sh_pour_u', 0.0) < 0.10                          # still standing inside: wall hides him
        if hide:
            pen.cv.save(); pen.cv.clipPath(rect(0, g['sill'] + 10, 1920, 2000), skia.ClipOp.kDifference, True)
        fig(pen, a, t, PINKW)                                                          # pass 2: out in front of the wall
        if hide: pen.cv.restore()
        if a.at(t).sh_nolegs > 0.5:                                                    # the sill ledge over his hips
            Wd = g['x1'] - g['x0']
            pen.fill(rect(g['x0'] - 20, g['sill'] - 6, Wd + 40, 22), '#d9dde4'); pen.line(rect(g['x0'] - 20, g['sill'] - 6, Wd + 40, 22), 3, '#1a1418')
        pen.cv.restore()
    return dict(draw=draw, actors=[a])


@clip('sh_scuttle_fence_car_roof', 5.0, 'He scuttles along our fence, over Dad\'s car, up onto our roof: low and fast, legs stabbing left and right, every plant a click.')
def _c_sh_scuttle():
    # a 3/4 tracking shot at snow level, much closer: the camera pans with him (world x -> screen x - cam(t)), his big
    # pale head leading low and forward (>= 8% of the frame), the legs stabbing round it
    ppm = 300.0
    FY = 1010.0
    CARX = [1100, 1135, 1310, 1420, 1650, 1780, 1880, 1900]           # Dad's car: the SAME profile is drawn and walked on
    CARH = [0.0, 0.72, 0.82, 1.40, 1.45, 0.92, 0.84, 0.0]

    def ground(x):
        if x < 1100: return FY - 1.1 * ppm                          # the fence top
        if x < 1900: return FY - float(np.interp(x, CARX, CARH)) * ppm   # hood, windscreen, roof, trunk
        return FY - 1.6 * ppm - (x - 1900) * 0.16                   # up the roof slope
    a = sh(300, FY, ppm)
    a.set(-1.0, None, 0.01, sh_m=1.0)
    a.face(0.35, 0.0)                                  # 3/4 toward the lens
    X0, X1 = 300.0, 2900.0
    path = lambda u: (X0 + (X1 - X0) * u, ground(X0 + (X1 - X0) * u) + 0.15 * ppm)
    a.scuttle(0.0, 4.8, path, ground, stride=300.0, lift=55.0, spread=1.25)
    def cam(t):                                        # lags him by 0.25 s: he moves INSIDE the frame (never a sprite on a scrolling plate)
        hx, hy = a.where(max(t - 0.25, 0.0), 'head')
        return hx - 960 - 220, min(0.0, hy - 430)
    def draw(pen, t):
        cx, cy = cam(t)
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 1080, [(0, '#05070f'), (1, '#16203a')])
        pen.cv.save(); pen.cv.translate(-cx, -cy)
        pen.linear(rect(cx - 50, FY - 380, 2100, 2000), 0, FY - 380, 0, FY + 200, [(0, '#5a6a8c', 255), (1, '#8a9cbc', 255)])
        pen.fill(rect(-400, FY - 1.1 * ppm, 1500, 22), '#6a5846')
        for k in range(30): pen.fill(rect(-380 + k * 50, FY - 1.1 * ppm, 12, 1.1 * ppm), '#6a5846')
        carp = poly([(x_, FY - h_ * ppm) for x_, h_ in zip(CARX, CARH)], True)
        pen.fill(carp, '#3a4a6a'); pen.line(carp, 4, '#141824')
        for wp in ([(1330, 0.80), (1425, 1.32), (1520, 1.36), (1520, 0.80)], [(1545, 0.80), (1545, 1.36), (1640, 1.38), (1750, 0.86)]):
            pen.fill(poly([(x_, FY - h_ * ppm) for x_, h_ in wp], True), '#1c2638'); pen.line(poly([(x_, FY - h_ * ppm) for x_, h_ in wp], True), 3, '#141824')
        pen.fill(rect(1100, FY - 0.30 * ppm, 800, 0.30 * ppm), '#2c3852')
        for wx in (1250, 1760):
            pen.fill(oval(wx, FY - 0.17 * ppm, 0.19 * ppm, 0.19 * ppm), '#111318'); pen.fill(oval(wx, FY - 0.17 * ppm, 0.08 * ppm, 0.08 * ppm), '#7d8596')
        pen.fill(oval(1890, FY - 0.55 * ppm, 10, 7), '#c0392b', 220)
        pen.fill(poly([(1900, FY), (1900, FY - 1.6 * ppm), (4200, FY - 1.6 * ppm - 2300 * 0.16), (4200, FY)], True), '#4a3a34')
        fig(pen, a, t, NIGHTI)
        pen.cv.restore()
    return dict(draw=draw, actors=[a])


@clip('sh_drop_door', 3.5, 'And drops. Right in front of our door. Jaw hanging. (Adam ducks under him and slams the door.)')
def _c_sh_drop():
    # closer; the fall reads (0.35 - 0.90 s, legs folded high), a squash on landing, the legs slam out, then the jaw hangs
    ppm = 330.0
    a = sh(960, 1050, ppm)
    a.set(-1.0, None, 0.01, sh_m=1.0, sh_lift=80.0)
    a.face(0.0, 0.0)
    a.drop_to(0.35, 0.55, from_dy=-900.0)
    a.jaw_gape(1.05, 3.5)
    a.leg_to(1.6, 0, (960 + 330, 1075), dur=0.22, hold=9.0, back=None, ev='leg_click')
    a.leg_to(2.2, 1, (960 - 330, 1075), dur=0.22, hold=9.0, back=None, ev='leg_click')
    a.set(1.6, None, 1.2, sh_neck=30.0, h_scale=1.15)                     # the mask pushes ~15% closer
    a.menace(0.0, 3.5)
    def draw(pen, t):
        snow_street(pen, 860)
        door(pen, 960, 1050, ppm=ppm)
        fig(pen, a, t, NIGHTI)
    return dict(draw=draw, actors=[a])


@clip('sh_legs_spear_coat', 4.5, 'Legs stab the snow round Adam as he runs with Lina in his arms; one spears his coat to the ground; he tears free; another pries at Lina (he never touches a child who is held).')
def _c_sh_spear():
    # a tracking shot at ppm 330: he is FASTER than Adam (the gap closes ~600 -> ~150 px by 2.5 s), the mask at the lens and
    # at Adam; leg 2 spears the coat HEM to the snow (it stretches, Adam is jerked back 0.15 s and tears free, a flap stays
    # pinned); leg 4 pries between Adam's arm and Lina's back; Adam turns his shoulder away
    ppm = 330.0
    GY = 1000.0
    a = sh(0, GY, ppm)
    a.set(-1.0, None, 0.01, sh_m=1.0, sh_spread=0.75)
    a.face(-0.4, 0.0)
    adam = actor('adam_sock', 0, GY, ppm, seed=5, expr='terrified_call')
    lina = actor('lina', 0, 0, ppm, seed=6, expr='fear')
    adam.run(0.0, 4.5, 900, 3420, surface='snow')          # a real run (~1.7 m/s): the fence scrolls ~9 px a frame
    adam.carry(0.0, lina)
    adam.face(0.55)
    lina.look_at(0.0, (a, 'eyes'), dur=0.3)
    a.look_at(0.2, (adam, 'head'), dur=0.3)
    sp = (3420 - 900) / 4.5

    def stall(P, t):                                       # pinned 0.45 s: jerked BACK 35 px, leaning back ~12 deg, then tears free
        P.dx -= sp * clamp(t - 1.25, 0.0, 0.45) + 35.0 * math.sin(PI * clamp((t - 1.25) / 0.45))
        P.lean -= 0.10 * math.sin(PI * clamp((t - 1.25) / 0.6))
    adam._add(1.25, None, stall, real=True)

    def bx(t):
        if t < 2.5: return 300 + (900 + sp * 2.5 - 300 - 300) * t / 2.5
        return 900 + sp * 2.5 - 300 + (sp - 10) * (t - 2.5)
    a.scuttle(0.0, 4.5, lambda u: (bx(u * 4.5), GY), None, stride=170.0, lift=90.0, ease=0.02)
    hem0 = [None]

    def hem(t):
        if hem0[0] is None:
            hx, hy = adam.where(1.2, 'hip'); hem0[0] = (hx - 30, GY - 4)        # the needle stops IN the snow, through the hem
        return hem0[0]
    a.leg_to(1.0, 2, hem, dur=0.2, hold=0.7, back=0.35, ev='leg_spear_coat')
    a.leg_to(0.45, 0, lambda t: (adam.where(t, 'foot_l')[0] - 110, GY), dur=0.18, hold=0.3, back=0.3)
    a.leg_to(2.4, 4, lambda t: ((adam.where(t, 'hand_r')[0] + lina.where(t, 'chest')[0]) / 2, (adam.where(t, 'hand_r')[1] + lina.where(t, 'chest')[1]) / 2 - 10),
             dur=0.25, hold=0.6, back=0.4, ev='leg_pry', zd=-10.0)
    adam.set(2.55, 3.3, 0.2, h_turn=0.25, turn=0.15)        # the shoulder turned away from the needle
    adam.flinch(2.6, 0.7)
    a.leg_to(3.3, 6, lambda t: (adam.where(t, 'foot_r')[0] + 70, GY), dur=0.18, hold=0.3, back=0.3)
    a.menace(0.0, 4.5)

    def cam(t):
        return (a.where(t, 'head')[0] * 0.45 + adam.where(t, 'head')[0] * 0.55) - 960

    def draw(pen, t):
        cx = cam(t)
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 640, [(0, '#05070f'), (1, '#16203a')])
        pen.cv.save(); pen.cv.translate(-cx, 0)
        pen.fill(rect(cx - 100, 640, 2200, 600), '#c9d6ea')
        pen.linear(rect(cx - 100, 640, 2200, 600), 0, 640, 0, 1080, [(0, '#5a6a8c', 255), (1, '#8a9cbc', 255)])
        for k in range(-2, 40):
            x = k * 260.0
            pen.fill(rect(x, 560, 16, 120), '#3a3040')                # fence posts far back (parallax read)
        fig(pen, a, t, NIGHTI)
        CH.draw_carry_child(pen, adam, lina, t, NIGHTI, NIGHTI)
        if 1.2 <= t:                                               # the coat hem pinned under the needle (over Adam)
            tx, ty = hem(t)
            if t < 1.7:                                            # the coat stretched from his hip to the needle
                hx, hy = adam.where(t, 'hip')
                p = smooth([(hx - 10, hy + 20), (tx + 10, ty - 10), (tx - 8, ty + 2), (hx - 45, hy + 75)], True, 0.4)
                pen.fill(p, '#263a66'); pen.line(p, 3, '#1a1418')
            pen.fill(poly([(tx - 18, ty - 6), (tx + 14, ty - 12), (tx + 8, ty + 8), (tx - 12, ty + 6)], True), '#263a66')
            pen.line(poly([(tx - 18, ty - 6), (tx + 14, ty - 12), (tx + 8, ty + 8), (tx - 12, ty + 6)], True), 2.5, '#1a1418')
        pen.cv.restore()
    return dict(draw=draw, actors=[a, adam, lina], grounded=[adam])


@clip('sh_face_glass', 3.5, 'At the door as "Mom": slowly, a face slides up the clear strip of glass. Long. White. Red eyes. The doorknob grows frost.')
def _c_sh_glass():
    ppm = 520.0
    a = sh(960, 2900, ppm * 1.9)
    a.set(-1.0, None, 0.01, sh_long=1.0, sh_red=1.0, sh_sink=1.0, sh_smile=1.0)
    a.face(0.0, 0.0)
    def rise(P, t): P.dy -= 860 * ease_in_out(clamp((t - 0.4) / 2.4))      # the long face slides UP into the clear strip
    a._add(-INF, None, rise)
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#3a2e26')
        strip = rect(760, 140, 400, 300)
        pen.fill(strip, '#0a0e1a')
        pen.cv.save(); pen.cv.clipPath(strip, skia.ClipOp.kIntersect, True)
        fig(pen, a, t, dict(NIGHTI, dark=0.15))
        pen.fill(strip, '#bcd0f0', 70)
        pen.cv.restore()
        pen.line(strip, 10, '#5a4a3a')
        k = clamp((t - 2.2) / 1.2)
        pen.fill(oval(1240, 860, 34, 34), mix('#c9a24a', '#e8f4ff', k)); pen.line(oval(1240, 860, 34, 34), 3)
    return dict(draw=draw, actors=[a])


@clip('sh_hatch_upside_down', 4.0, 'The hallway hatch drops open. His face lowers, upside down. A leg reaches between the kids, prying.')
def _c_sh_hatch():
    # a low angle from the kids: they fill the bottom of the frame (waist up), he hangs upside down out of the hatch
    # above them, his inverted face >= 20% of the frame; one leg stabs down BETWEEN them; Adam pulls Lina behind him
    ppm = 520.0
    a = sh(960, 30, ppm)
    a.set(-1.0, None, 0.01, sh_m=1.0, sh_legcap=2.0, sh_nolegs=1.0)
    a.face(0.0, 0.0)
    a.hang_hatch(0.3, 1.0, lower=0.22)
    kp = 560.0
    adam = actor('adam_in', 660, 1250, kp, seed=7, expr='fear'); lina = actor('lina_pj', 1250, 1250, kp, seed=8, expr='fear')
    adam.face(0.45); lina.face(-0.45)
    adam.look_at(0.5, (a, 'eyes'), dur=0.25); lina.look_at(0.55, (a, 'eyes'), dur=0.25)
    a.leg_to(1.6, 1, (960, 1240), dur=0.30, hold=2.0, back=0.4, ev='leg_pry')
    a.menace(0.0, 4.0)
    adam.flinch(0.45, 1.0); lina.flinch(0.5, 1.0)
    adam.fear_body(0.5); lina.fear_body(0.55)
    adam.hold_hand(2.4, -1, lina, 1)
    def pull(P, t):                       # round the stabbed leg and in behind his back
        u = ease_in_out(clamp((t - 2.5) / 0.6)); P.dx -= 420 * u
    lina._add(2.5, None, pull)
    def shield(P, t):
        u = ease_in_out(clamp((t - 2.5) / 0.5)); P.dx += 50 * u
    adam._add(2.6, None, shield)
    lina.look_at(2.6, (adam, 'head'), dur=0.2); lina.look_at(3.3, (a, 'eyes'), dur=0.3)
    def draw(pen, t):
        room(pen, '#2e3446', '#4a3a30', 1300)
        pen.fill(rect(720, 0, 480, 40), '#111018')
        pen.cv.save(); pen.cv.clipPath(rect(0, 40, 1920, 1080), skia.ClipOp.kIntersect, True)
        fig(pen, a, t, NIGHTI)
        pen.cv.restore()
        behind = t >= 2.45                                # pulled in behind him: drawn behind for the whole pull
        if behind: fig(pen, lina, t, NIGHTI); fig(pen, adam, t, NIGHTI)
        else: fig(pen, adam, t, NIGHTI); fig(pen, lina, t, NIGHTI)
    return dict(draw=draw, actors=[a, adam, lina])


@clip('sh_under_door', 3.5, 'Under the bathroom door, a needle-thin leg tip slides in, feeling for Lina\'s sock. Adam jams the towel down on it. It pulls back.')
def _c_sh_under_door():
    # side-on at the gap under the bathroom door: the needle (tapered 26 -> 4 px, a rime band, one ankle joint in frame)
    # slides in feeling for Lina's sock with two probing sweeps; her foot (ankle + pyjama hem) pulls back when it gets
    # close; Adam's hand and hoodie cuff bring the towel down 0.25 s before contact, press it (10% squash), the tip
    # retracts under it
    FL = 780.0

    def tip_x(t):
        u = ease_in_out(clamp((t - 0.3) / 1.3))
        sw = 40.0 * math.sin(2 * PI * clamp((t - 1.0) / 0.6)) * (1.0 if 1.0 < t < 1.6 else 0.0)
        back = ease_in_out(clamp((t - 2.15) / 0.45))
        return (300 + 840 * u + sw) * (1 - back) + (-200) * back

    def foot_x(t):
        d = 1250 - tip_x(t)
        return 1250 + 120 * ease_in_out(clamp((t - 1.35) / 0.3)) if t > 1.35 else 1250 + (120 if d < 60 else 0)

    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#cfd6dc')
        pen.cv.save(); pen.cv.translate(960, 640); pen.cv.scale(1.7, 1.7); pen.cv.translate(-1010, -FL)   # close on the gap
        pen.fill(rect(-600, -400, 3200, 2000), '#cfd6dc')
        pen.fill(rect(0, 0, 1920, FL - 40), '#e6e2da')                    # the door's bottom rail and the gap
        pen.fill(rect(0, FL - 64, 1920, 24), '#bdb4a6'); pen.line(rect(0, FL - 64, 1920, 24), 3, '#1a1418')
        pen.fill(rect(0, FL, 1920, 300), '#9fb0bf')                         # bathroom tiles
        for k in range(12): pen.line(poly([(k * 180, FL), (k * 180 - 60, 1080)], False), 2, '#7f90a0', 160)
        tx = tip_x(t)
        ax_ = tx - 230                                                      # the ankle joint
        pts = [(-60, FL - 26), (ax_, FL - 20), (tx, FL - 4)]
        pen.fill(_taper([pts[0], pts[1]], 30, 22), '#6B4A32'); pen.line(_taper([pts[0], pts[1]], 30, 22), 3, '#1a1418')
        pen.fill(_taper([pts[1], pts[2]], 22, 4), '#6B4A32'); pen.line(_taper([pts[1], pts[2]], 22, 4), 3, '#1a1418')
        pen.fill(_taper([((ax_ + tx) / 2 + 60, FL - 9), pts[2]], 9, 2), '#e3e9ee')
        pen.fill(oval(ax_, FL - 21, 17, 15), '#3E2A1C'); pen.line(oval(ax_, FL - 21, 17, 15), 3, '#1a1418')
        pen.fill(oval(ax_ - 2, FL - 31, 16, 8), '#c4d3e0', 200)                 # the rime band
        for k in range(5): pen.fill(oval(ax_ - 150 - 60 * k, FL - 34, 9, 4), '#DCE8F2', 200)
        fx = foot_x(t)                                                       # Lina's foot: sock, ankle, pyjama hem
        pen.fill(rrect(fx, FL - 70, 200, 72, 34), '#f2a8c4'); pen.line(rrect(fx, FL - 70, 200, 72, 34), 4)
        pen.fill(rect(fx + 120, FL - 300, 70, 240), '#e9c9b5'); pen.line(rect(fx + 120, FL - 300, 70, 240), 4)
        pen.fill(rrect(fx + 95, FL - 420, 120, 150, 20), '#f2a8c4'); pen.line(rrect(fx + 95, FL - 420, 120, 150, 20), 4)
        for k in range(3): pen.fill(oval(fx + 120 + 35 * k, FL - 360 + 25 * (k % 2), 7, 7), '#ffffff')
        if t > 1.55:                                                         # Adam's hand brings the towel down
            d = ease_in_out(clamp((t - 1.55) / 0.3))
            sq = 1.0 - 0.10 * math.sin(PI * clamp((t - 1.85) / 0.3))
            ty = -200 + (FL - 120 + 200) * d
            tx0 = 300 + 840 * ease_in_out(clamp((1.85 - 0.3) / 1.3)) - 200
            h = 120 * sq
            towel = rrect(tx0, ty + (120 - h), 420, h, 30)
            pen.fill(towel, '#5a8ac0'); pen.line(towel, 4)
            for k in range(4): pen.line(poly([(tx0 + 40 + 100 * k, ty + (120 - h) + 10), (tx0 + 40 + 100 * k, ty + 110)], False), 3, '#3f6a98', 160)
            hx = tx0 + 210
            pen.fill(rect(hx - 70, -400, 140, ty + 400 + 10), '#3c5590'); pen.line(rect(hx - 70, -400, 140, ty + 400 + 10), 4)   # the hoodie sleeve
            pen.fill(rrect(hx - 78, ty - 40, 156, 50, 14), '#2c4070'); pen.line(rrect(hx - 78, ty - 40, 156, 50, 14), 4)          # the cuff
            hand = smooth([(hx - 70, ty + 8), (hx + 75, ty + 6), (hx + 85, ty + 50), (hx - 75, ty + 52)], True, 0.5)
            pen.fill(hand, '#e2b293'); pen.line(hand, 4)
            for k in range(3): pen.line(poly([(hx - 40 + 40 * k, ty + 14), (hx - 40 + 40 * k, ty + 46)], False), 2, '#a87a62')
        pen.cv.restore()
    return dict(draw=draw, actors=[])


@clip('sh_hook_blanket_cage', 5.0, 'Crossing the street under one blanket: legs stab the snow round them; one hooks the blanket and PULLS; then he swings round, jaw down, legs arched over them like a cage ("Inside, children. Rule seven.").')
def _c_sh_cage():
    # the climax, at the kids' eye line: three people under one opaque blanket (Kessler, Lina, Adam); he scuttles in slung
    # low in his legs (human legs tucked), hooks the blanket corner and PULLS (they lean back, Adam grips the hem), it snaps
    # back; then the legs arch OVER them, planted outside the huddle, his head brought down to theirs, the jaw gapes and
    # the head creeps closer. Drawn BEHIND the people, then only the legs again in front once he cages them.
    ppm = 360.0
    GY = 960.0
    kes = actor('kessler_out', 740, GY - 12, ppm, seed=11, expr='hypo')     # staggered in depth, angled 3/4 to him
    lina = actor('lina', 885, GY + 22, ppm, seed=10, expr='fear')            # pressed into Adam
    adam = actor('adam_sock', 1005, GY + 6, ppm, seed=9, expr='fear')
    adam.face(0.55); lina.face(0.45); kes.face(0.35)
    adam.fear_body(0.0); lina.fear_body(0.0, k=0.8); kes.fear_body(0.0, k=0.8)
    a = sh(1750, GY, ppm)
    a.set(-1.0, None, 0.01, sh_m=1.0, sh_lift=85.0, sh_nolegs=1.0)
    a.face(-0.22, 0.0)                                    # mostly to the lens: the thrust head stays over his own body
    a.scuttle(0.0, 0.75, lambda u: (1780 - 300 * u, GY), None, stride=150.0, lift=85.0, spread=0.85, pitch=28.0, ease=0.3)
    hx0, hy0 = adam.where(1.0, 'head')
    C0 = (hx0 + 50.0, hy0 - 62.0)                         # the blanket's corner lies FLAT on Adam's head until the leg hooks it

    def corner_pull(t):
        return (C0[0] + 140.0 * ease_in_out(clamp((t - 1.2) / 0.6)), C0[1] - 25.0 * ease_in_out(clamp((t - 1.2) / 0.6)))
    a.leg_to(1.0, 3, corner_pull, dur=0.2, hold=0.7, back=0.35, ev='leg_hook_blanket')

    def corner(t):
        if t < 1.2: return C0
        if t < 1.9:
            return a.where(t, 'leg3')
        p = a.where(1.9, 'leg3'); u = clamp((t - 1.9) / 0.35)
        k = math.exp(-u * 5.0) * math.cos(u * 9.0)       # it snaps back with a little overshoot
        return (C0[0] + (p[0] - C0[0]) * k, C0[1] + (p[1] - C0[1]) * k)
    for who_, kk in ((adam, 1.0), (lina, 0.8), (kes, 1.0)):
        who_.set(1.2, 1.95, 0.18, lean=-0.07 * kk)              # they lean back against the pull (Kessler ~8 deg)
    adam.set(1.2, None, 0.3, dx=-45.0)                           # Adam steps half in front of Lina
    for who_ in (adam, lina, kes):
        who_.set(2.6, None, 0.3, crouch=0.08)                    # all hunch as the cage lands, eyes up
    adam.reach_to(1.05, 1, lambda t: (C0[0] - 40, C0[1] + 150), t1=2.3, dur=0.25, z=40.0)
    kes.reach_to(0.4, 1, lambda t: (kes.where(t, 'head')[0] + 70, kes.where(t, 'head')[1] + 190), dur=0.4, z=40.0)   # Kessler grips
    kes.reach_to(0.4, -1, lambda t: (kes.where(t, 'head')[0] - 60, kes.where(t, 'head')[1] + 200), dur=0.4, z=40.0)  # both edges
    adam.look_at(0.3, (a, 'eyes'), dur=0.3); lina.look_at(0.8, (a, 'eyes'), dur=0.3); kes.look_at(2.6, (a, 'eyes'), dur=0.6)
    lina.look_at(1.7, (adam, 'chest'), dur=0.35)                 # then she turns her face into Adam's coat
    lina.reach_to(1.7, 1, (adam, 'chest'), dur=0.35, z=30.0)
    lina.flinch(1.25, 0.8); adam.flinch(2.45, 0.6)
    a.cage(2.4, 860, 560, GY, dur=0.6)
    a.jaw_gape(3.0, 5.0)
    a.set(3.2, None, 1.8, sh_neck=24.0)                   # the head creeps ~20 cm toward them
    a.look_at(0.8, (adam, 'head'), dur=0.3)
    a.menace(0.0, 5.0)

    def blanket(pen, t, front):
        kx, ky = kes.where(t, 'head'); lx, ly = lina.where(t, 'head'); ax, ay = adam.where(t, 'head')
        cx, cy = corner(t)
        wool, dk, edge = '#7a4e66', '#4e3042', '#cdb9a6'
        if not front:                     # the back of the blanket behind their backs and shoulders
            pts = [(kx - 120, ky + 230), (kx - 110, ky), (ax + 100, ay), (ax + 95, ay + 230)]
            pen.fill(smooth(pts, True, 0.3), dk)
            return
        # OVER their heads: the top arcs over the three crowns to the hooked corner; the front edge runs just above their
        # brows (faces clear) and the sides hang down over the outer shoulders
        top = [(kx - 125, ky + 215), (kx - 120, ky - 10), (kx - 70, ky - 95), (kx + 10, ky - 115), (lx, ly - 100),
               (ax - 30, ay - 112), (cx, cy), (ax + 105, ay + 10), (ax + 100, ay + 225)]
        front_ = [(ax + 62, ay + 225), (ax + 66, ay + 5), (ax + 30, ay - 36), (ax - 20, ay - 40), (ax - 52, ay - 26), (lx + 40, ly - 30),
                  (lx, ly - 38), (lx - 40, ly - 26), (kx + 50, ky - 38), (kx, ky - 46), (kx - 55, ky - 30), (kx - 80, ky + 10), (kx - 82, ky + 220)]
        p = smooth(top + front_, True, 0.45)
        pen.fill(p, wool); pen.line(p, 4, '#1a1418')
        for k in range(5):               # folds pulled toward the hooked corner
            u = (k + 0.5) / 5.0
            pen.line(smooth([(cx - 25, cy + 12), (cx - 90 - 200 * u, cy + 25 + 30 * u), (kx - 40 + 330 * u, ky - 50 + 10 * u)], False), 3, dk, 170)
        pen.line(smooth(front_[1:-1], False), 8, edge, 235)       # the knit edge over their brows
        pen.line(smooth(front_[1:-1], False), 2, '#1a1418', 200)
        # wrapped ACROSS the fronts of their shoulders and torsos (under each chin), the hem gripped at the front
        hb = max(ay, ly, ky) + 290
        wrap = [(kx - 82, ky + 120), (kx - 20, ky + 112), (kx + 50, ky + 120), (lx - 30, ly + 88), (lx + 35, ly + 86),
                (ax - 40, ay + 112), (ax + 30, ay + 104), (ax + 66, ay + 120), (ax + 62, hb - 20), (ax, hb), (lx, hb + 12), (kx, hb), (kx - 82, hb - 30)]
        pw = smooth(wrap, True, 0.35)
        pen.fill(pw, wool); pen.fill(_crescent_rect(pw), dk, 120) if False else None
        for k in range(4):
            u = (k + 1) / 5.0
            pen.line(smooth([(kx - 40 + 30 * u, ky + 150 + 30 * u), (lx, ly + 150 + 60 * u), (ax + 20 - 20 * u, ay + 170 + 40 * u)], False), 3, dk, 150)
        pen.line(pw, 4, '#1a1418')
        pen.line(smooth([(kx - 82, hb - 30), (kx, hb), (lx, hb + 12), (ax, hb), (ax + 62, hb - 20)], False), 8, edge, 230)

    def draw(pen, t):
        snow_street(pen, 520)
        P = a.at(t)
        CH.draw(pen, a.who, a.x0, a.y0, a.height, P, light=dict(NIGHTI, rim='#ff9ccc', rim_a=80), t=t)
        blanket(pen, t, False)
        for who_ in (kes, lina, adam): fig(pen, who_, t, NIGHTI)
        blanket(pen, t, True)
        for who_, sd in ((adam, 1), (kes, 1), (kes, -1)):          # the gripping hands over the hem / edges
            CH.draw_arm(pen, who_.who, sd, who_.at(t), x=who_.x0, y_feet=who_.y0, height=who_.height, light=NIGHTI, t=t)
        if t >= 2.4:
            Q = a.at(t); Q.sh_legs_only = 1.0
            CH.draw(pen, a.who, a.x0, a.y0, a.height, Q, light=dict(NIGHTI, rim='#ff9ccc', rim_a=80), t=t)
    return dict(draw=draw, actors=[a, adam, lina, kes], grounded=[adam, lina, kes])


@clip('sh_pluck_mitten', 3.5, 'One leg plucks Lina\'s mitten from the snow and carries it back: cutaway, it hangs at the RIGHT end of his string, saving her a place. The red one at the left.')
def _c_sh_mitten():
    # the cutaway at the serving window: a REAL jointed leg (tapered, knee ball, rime) comes over the roof with Lina's
    # mitten hooked on its needle and hangs it on the RIGHT end of the string in the same frame (no fade); it withdraws
    ppm = 640.0                                         # a close cutaway: the window fills the frame
    g = truck(None, 900, 1010, ppm)
    Wd = g['x1'] - g['x0']
    y_s = g['top'] + 0.08 * ppm
    slot = (g['x0'] + Wd * 0.97, y_s + 0.01 * ppm + 4)
    start = (1650.0, 20.0)

    def tip(t):
        u = ease_in_out(clamp((t - 0.2) / 1.0)); v = ease_in_out(clamp((t - 1.35) / 0.4))
        p = (start[0] + (slot[0] - start[0]) * u, start[1] + (slot[1] - start[1]) * u + 60 * math.sin(PI * u) * -1)
        return (p[0] + (start[0] - p[0]) * v, p[1] + (start[1] - p[1]) * v)

    def draw(pen, t):
        snow_street(pen, 820)
        truck_back(pen, g, ppm)
        hung = t >= 1.2
        truck_front(pen, g, ppm, 1.0, t, mitten_lina=1.0 if hung else 0.0)
        tx, ty = tip(t)
        root = (2050.0, -60.0)
        knee = ((root[0] + tx) / 2 + 80, min(root[1], ty) + 150)
        ank = (tx + (knee[0] - tx) * 0.35 + 30, ty + (knee[1] - ty) * 0.35)
        for a_, b_, w0, w1 in ((root, knee, 54, 40), (knee, ank, 38, 20), (ank, (tx, ty), 18, 4)):
            p = _taper([a_, b_], w0, w1)
            pen.fill(p, '#6B4A32' if w1 > 3 else '#8a6a50'); pen.line(p, 3, '#1a1418')
        for j, r in ((knee, 30), (ank, 20)):
            pen.fill(oval(j[0], j[1], r, r * 0.9), '#3E2A1C'); pen.line(oval(j[0], j[1], r, r * 0.9), 3, '#1a1418')
            pen.fill(oval(j[0], j[1] - r * 0.6, r * 0.9, r * 0.45), '#c4d3e0', 190)
        if not hung:                                       # the mitten hooked on the needle, hanging from it
            m = rrect(tx - 0.045 * ppm, ty - 2, 0.09 * ppm, 0.1 * ppm, 0.03 * ppm)
            pen.fill(m, '#e87aa4'); pen.line(m, 2, '#1a1418')
    return dict(draw=draw, actors=[])


@clip('sh_defeat_shrink', 4.5, 'Defeat: the song hangs on the empty beat; his jaw gapes for the last note and can\'t close; then the legs fold away and the skull shrinks back into the smile: "See you when it\'s this cold again!"')
def _c_sh_defeat():
    # the gape that cannot close, CLOSE (ppm 450, the head ~13% of the frame), then a cut wide for the fold
    def setup(ppm, sill_y):
        g = truck(None, 960, sill_y, ppm)
        a = sh(960, g['floor'], ppm)
        a.lean_to(0.0, (960, sill_y - 60), gap=10.0, dur=0.01)
        a.set(-1.0, None, 0.01, sh_m=1.0)
        a.jaw_gape(0.2, 1.8)
        a.shrink_back(1.8, 1.8)
        a.slow_wave(3.6, 4.5, side=1)
        return g, a
    gc, ac = setup(450.0, 900)
    gw, aw = setup(250.0, 640)

    def draw(pen, t):
        g, a, ppm = (gc, ac, 450.0) if t < 1.8 else (gw, aw, 250.0)
        snow_street(pen, 820 if t >= 1.8 else 1000)
        truck_back(pen, g, ppm)
        truck_front(pen, g, ppm, 1.0, t)
        pen.cv.save(); pen.cv.clipPath(rect(0, g['sill'] + 10, 1920, 2000), skia.ClipOp.kDifference, True)
        fig(pen, a, t, dict(PINKW, rim='#ffa040'))
        pen.cv.restore()
    return dict(draw=draw, actors=[aw])


# ================================================================================================ PEOPLE
def house_window(pen, x, y, w=420, h=440, lit=False, curtains=0.0, frost=0.0):
    window(pen, x, y, w, h, night=True, curtains=curtains)
    if lit: pen.fill(rect(x - w / 2, y, w, h), '#ffd9a0', 90)
    if frost > 0: pen.fill(rect(x - w / 2, y, w, h), '#e8f4ff', int(110 * frost))


@clip('adam_radio_over', 4.0, 'Dad hands Adam the radio; Adam keys it and talks: "Channel three... Over." (eyes on the radio, then out the window)')
def _c_adam_radio():
    ppm = 520.0
    a = actor('adam_in', 900, 1060, ppm, seed=21, expr='focused')
    a.face(0.3)
    a.hold_prop('walkie', 1, -1.0, None)
    a.radio_to_mouth(0.6, 3.6, side=1)
    a.look_at(0.0, (1150, 700), dur=0.4); a.look_at(2.2, (1700, 420), dur=0.5)
    a.talk([(0.9, 2.0)], text='Dad over')
    def draw(pen, t):
        room(pen, '#3a3446', '#4a3a30', 1060)
        house_window(pen, 1600, 300, frost=0.3)
        fig(pen, a, t, WARM)
    return dict(draw=draw, actors=[a], grounded=[a])


@clip('lina_wave_kessler', 4.0, 'At the last curtain, Lina waves at Kessler\'s dark window across the street, like every night (gap-toothed smile, on tiptoe).')
def _c_lina_wave():
    ppm = 560.0
    l = actor('lina_pj', 860, 1060, ppm, seed=22, expr='lina_grin')
    l.face(0.55)
    l.look_at(0.0, (1500, 500), dur=0.3)
    l.wave(0.6, 3.5, side=1, speed=0.8, height=1.1)
    def draw(pen, t):
        room(pen, '#3a3446', '#4a3a30', 1060)
        house_window(pen, 1420, 260, curtains=0.15)
        pen.fill(rect(1440, 380, 60, 70), '#20263a')
        fig(pen, l, t, NIGHTI)
    return dict(draw=draw, actors=[l], grounded=[l])


@clip('kessler_window_hand', 4.0, 'Across the street, in his dark window: Mr. Kessler. A hand lifts. Slowly. A small cloud of breath fogs his glass, from the inside.')
def _c_kessler_window():
    ppm = 700.0
    k = actor('kessler', 960, 1500, ppm, seed=23, expr='lonely')
    k.face(0.0)
    k.wave(1.0, 3.8, side=-1, speed=0.35, height=0.72, slow=True)       # the elbow keeps a bend
    k.look_at(0.0, (900, 1300), dur=0.3)
    win = rect(560, 120, 800, 900)

    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#0c1020')
        pen.fill(win, '#080a12')
        pen.cv.save(); pen.cv.clipPath(win, skia.ClipOp.kIntersect, True)    # only inside his window (no legs on the wall)
        fig(pen, k, t, dict(NIGHTI, dark=0.55))
        f = clamp((t - 2.2) / 0.8) * (1 - clamp((t - 3.4) / 0.6))
        pen.glow(960, 500, 160, '#dfe8f4', 120 * f)
        pen.cv.restore()
        pen.fill(rect(530, 990, 860, 40), '#3a3a44'); pen.line(rect(530, 990, 860, 40), 4, '#16161c')   # the sill
        pen.line(win, 22, '#2a2a30')
    return dict(draw=draw, actors=[k])


@clip('lina_walk_humming', 5.0, '"Lina is walking toward the pink window. Pyjamas, open coat, bare hands. Humming his song. Smiling." (sleepy, dreamy, a mitten dropped behind her)')
def _c_lina_walk():
    ppm = 300.0
    l = actor('lina', 0, 980, ppm, seed=24, expr='dazed')
    l.walk(0.2, 4.8, 400, 1300, facing=0.6, surface='snow')
    l.hum(0.3, 4.8)
    l.look_at(0.0, (1800, 600), dur=0.3)
    def draw(pen, t):
        snow_street(pen, 640, glow=(1800, 560, 700, 120))
        pen.fill(rrect(380, 985, 40, 26, 10), '#e87aa4')
        fig(pen, l, t, PINKW)
    return dict(draw=draw, actors=[l], grounded=[l])


@clip('adam_run_carry_lina', 4.0, 'Adam runs with Lina in his arms through knee-deep snow, one sock, breath hurting (she clings, head on his shoulder).')
def _c_adam_carry():
    ppm = 300.0
    a = actor('adam_sock', 0, 980, ppm, seed=25, expr='fear')
    l = actor('lina', 0, 0, ppm, seed=26, expr='fear')
    a.run(0.2, 3.8, 1500, 500)
    a.carry(-1.0, l)                                   # after run(): the arms hold her, they don't pump (already up at t=0)
    def pant(P, t):
        P.m_open = max(P.m_open, 0.42 + 0.14 * math.sin(t * 9.0)); P.lean += 0.06
        P.h_turn -= 0.35 * (1 if P.turn > 0 else -1)   # his face half to the lens (fear), eyes on where he runs
    a._add(-INF, None, pant)
    def draw(pen, t):
        snow_street(pen, 640)
        CH.draw_carry_child(pen, a, l, t, NIGHTI, NIGHTI)
        CH.draw_breath(pen, a, t, period=0.55, k=1.5)
        CH.draw_breath(pen, l, t, period=0.9, k=0.9, phase=0.3)
    return dict(draw=draw, actors=[a, l], grounded=[a])


@clip('dad_plow_cab', 4.0, 'Dad in the plow cab, hands on the wheel, the orange beacon sweeping; he keys the radio: "Adam? Passing our street. All good? Over."')
def _c_dad_cab():
    ppm = 560.0
    d = actor('dad', 900, 1500, ppm, seed=27, expr='grim_drive')
    d.face(0.0)
    g = CH.draw_steering_wheel.__doc__
    d.drive(0.0, 4.0, (700, 980), (1100, 980))
    d.talk([(1.4, 3.2)], text='Adam passing our street all good over')
    d.look_at(0.0, (900, 600), dur=0.3)
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#14161c')
        b = 0.5 + 0.5 * math.sin(t * 5.0)
        pen.glow(960, -100, 900, '#ffa040', 120 * b)
        fig(pen, d, t, dict(BEACON, rim_a=int(40 + 70 * b)))
        CH.draw_steering_wheel(pen, 900, 1000, 260)
    return dict(draw=draw, actors=[d])


@clip('kessler_shuffle_out', 5.0, 'His door opens. Mr. Kessler shuffles out. Slippers. Undershirt. No coat. Not shivering. Smiling. One step off his porch. Another step.')
def _c_kessler_out():
    ppm = 330.0
    k = actor('kessler_out', 0, 940, ppm, seed=28, expr='dazed')
    k.walk(0.6, 4.8, 700, 1150, facing=0.5, surface='snow')
    k.look_at(0.0, (1900, 500), dur=0.3)
    def draw(pen, t):
        snow_street(pen, 600, glow=(1900, 520, 700, 130))
        door(pen, 520, 940, ppm=ppm, open_=1.0)
        fig(pen, k, t, PINKW)
    return dict(draw=draw, actors=[k], grounded=[k])


@clip('lina_hug_kessler', 4.5, 'In his doorway, the blanket round all three; Lina hugs him: "I\'m Lina. You\'re not by yourself." And the old man starts to shiver.')
def _c_hug():
    ppm = 400.0
    k = actor('kessler_out', 1060, 1000, ppm, seed=29, expr='dazed')
    l = actor('lina', 975, 1000, ppm, seed=30, expr='kind_smile')     # pressed against him: a real hug
    k.face(-0.45); l.face(0.40)                                       # her cheek turned OUT: her face reads
    l.reach_to(0.4, 1, (k, 'hip'), dur=0.6, z=30.0, shape='grip'); l.reach_to(0.5, -1, (k, 'hip'), dur=0.6, z=-40.0, shape='grip')
    k.look_at(0.4, (l, 'head'), dur=0.5)                              # he looks DOWN at her head (it reaches him)
    l.look_at(0.0, (k, 'eyes'), dur=0.3)
    k.set(0.4, None, 0.5, h_nod=0.35)                                 # head tilted down ~20 deg
    k.reach_to(1.2, 1, lambda t: (l.where(t, 'head')[0] - 25, l.where(t, 'head')[1] + 95), dur=0.6, z=-20.0, contact='palm', shape='flat')  # his hand settles on her back
    l.talk([(1.0, 2.8)], text='Im Lina youre not by yourself')
    k.expr('tender', 1.8)

    def settle(P, t):                                                 # 1.8 s: the shoulders drop 10 px, a long breath, eyes closed
        u = ease_in_out(clamp((t - 1.8) / 0.8)); P.dy += 10.0 * u; P.hunch = max(P.hunch, 0.25 * u)
        if t > 2.0: P.blink = max(getattr(P, 'blink', 0.0), clamp((t - 2.0) / 0.25) * (1 - clamp((t - 3.6) / 0.25)))
    k._add(1.8, None, settle)

    def shiver(P, t):
        if t > 3.2: P.dx += 2.2 * math.sin(t * 60.0) * clamp((t - 3.2) / 0.4)
    k._add(3.2, None, shiver)
    def draw(pen, t):
        snow_street(pen, 600)
        door(pen, 1000, 1000, ppm=ppm, open_=1.0)
        fig(pen, k, t, WARM); fig(pen, l, t, WARM)
        if t > 1.9: CH.draw_breath(pen, k, t, period=2.4, k=1.3)
    return dict(draw=draw, actors=[k, l], grounded=[k, l])


@clip('kessler_cocoa_morning', 4.5, 'Morning, warm: Lina brings him cocoa; he takes the mug in both hands: "Sixty-eight years... First time anyone knocked on mine."')
def _c_cocoa():
    ppm = 420.0
    k = actor('kessler_am', 1120, 1000, ppm, seed=31, expr='tender')
    l = actor('lina', 905, 1000, ppm, seed=32, expr='kid_grin')
    k.face(-0.5); l.face(0.55)
    M = (k.where(0.0, 'chest')[0] - 0.20 * ppm, k.where(0.0, 'chest')[1] + 0.34 * ppm)      # within her reach, at his belly
    l.hold_prop('mug', 1, -1.0, 1.9)
    l.reach_to(0.3, 1, M, t1=1.9, dur=0.9, z=60.0, shape='grip', prop='mug')
    k.reach_to(1.1, -1, (M[0] + 8, M[1]), t1=None, dur=0.6, z=60.0, shape='grip')
    k.reach_to(1.2, 1, (M[0] + 30, M[1] + 4), t1=None, dur=0.6, z=60.0, shape='grip')
    k.hold_prop('mug', -1, 1.9, None)
    k.look_at(0.0, (l, 'eyes'), dur=0.4); l.look_at(0.0, (k, 'eyes'), dur=0.3)
    k.talk([(2.2, 4.3)], text='first time anyone knocked on mine')
    def draw(pen, t):
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 1080, [(0, '#ffe6c0'), (1, '#f2c89a')])
        pen.fill(rect(0, 1000, 1920, 80), '#e8eef4')
        door(pen, 1350, 1000, ppm=ppm, open_=1.0)
        fig(pen, k, t, MORNING); fig(pen, l, t, MORNING)
    return dict(draw=draw, actors=[k, l], grounded=[k, l])


@clip('benny_1958', 4.0, '1958, sepia: little Benny, from behind, walks alone toward the pink window at the curb; small footprints; one red mitten.')
def _c_benny():
    ppm = 240.0
    b = actor('benny', 0, 960, ppm, seed=33, expr='neutral')
    b.walk(0.2, 3.8, 900, 1250, facing=1.85, surface='snow')        # from BEHIND, toward the pink window
    def draw(pen, t):
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 1080, [(0, '#2a2218'), (1, '#6a5a44')])
        pen.fill(rect(0, 960, 1920, 120), '#b8a888')
        pen.fill(rect(1380, 420, 380, 270), '#e0a0b0'); pen.glow(1570, 560, 420, '#ffb8c8', 60)   # the pink window ~25% of the frame
        fig(pen, b, t, dict(rim='#f0d0a0', rim_a=50, side=-1, key=0.0))
        # ONE red mitten, on his right hand while he walks; it slips off at the curb only at the end of the walk
        td = 3.55
        hx, hy = b.where(min(t, td), 'hand_r')
        if t < td:
            m_ = rrect(hx - 13, hy - 6, 26, 30, 9); pen.fill(m_, '#c8322f'); pen.line(m_, 2.5, '#1a1418')
            pen.fill(rrect(hx - 13, hy - 8, 26, 7, 3), '#e8d8c8')
        else:
            u = clamp((t - td) / 0.35); gy = 975.0
            y_ = hy + (gy - hy) * u * u; x_ = hx + 30 * u
            m_ = rrect(x_ - 15, y_ - 9, 30, 18, 7); pen.fill(m_, '#c8322f'); pen.line(m_, 2.5, '#1a1418')
    return dict(draw=draw, actors=[b], grounded=[b])


def _medium(name, idx, t_cut=1.5, k=2.6, fy=0.36, sepia=False):
    """Wide (<= t_cut, establishing) then CUT to a medium on actor idx (face >= 10% of the frame), the camera on the head."""
    f, dur, desc = CLIPS[name]

    def g():
        S = f(); d = S['draw']; act = S['actors'][idx]

        def draw(pen, t):
            if t >= t_cut:
                hx, hy = act.where(t, 'head')
                pen.cv.save(); pen.cv.translate(960, 1080 * fy); pen.cv.scale(k, k); pen.cv.translate(-hx, -hy)
                d(pen, t); pen.cv.restore()
            else:
                d(pen, t)
            if sepia:                                                 # the 1958 grade at shot level
                pen.cv.drawPaint(skia.Paint(Color=skia.Color(112, 82, 48, 150), BlendMode=skia.BlendMode.kColor))
        S['draw'] = draw
        return S
    CLIPS[name] = (g, dur, desc)


_medium('benny_1958', 0, t_cut=1.4, k=2.0, fy=0.45, sepia=True)
_medium('lina_walk_humming', 0, k=2.6)
_medium('adam_run_carry_lina', 0, k=2.2, fy=0.40)
_medium('kessler_shuffle_out', 0, k=2.2)
_medium('kessler_cocoa_morning', 0, k=1.8, fy=0.46)
_medium('lina_hug_kessler', 0, t_cut=1.0, k=1.7, fy=0.32)

if __name__ == '__main__':
    main()
