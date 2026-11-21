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


def snow_holes(pen, a, t, ys, keep=None):
    """Needle holes left in the snow where his tips touched (from the actor's leg tips at ground level)."""
    pass


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
    a.lean_to(2.0, (980, 760), gap=10.0, dur=1.2)
    def draw(pen, t):
        snow_street(pen, 760)
        truck_back(pen, g, ppm)
        shiver_in_window(pen, a, t, g, lean=t > 2.0)
        truck_front(pen, g, ppm, win(t), t)
    return dict(draw=draw, actors=[a])


@clip('sh_lean_down_reach', 5.5, '"Mister Shiver leans down. Down. Further than a man can bend." His glove reaches down for Lina\'s bare hand; an inch from his fingers Adam yanks her into his arms. He keeps smiling, keeps waving.')
def _c_sh_down():
    ppm = 260.0
    g = truck(None, 760, 520, ppm)
    a = sh(760, g['floor'], ppm)
    lina = actor('lina', 1080, 1000, ppm, seed=3, expr='neutral')
    adam = actor('adam', 1500, 1000, ppm, seed=4, expr='fear')
    lina.face(-0.6); adam.face(-0.6)
    hand = lambda t: lina.where(t, 'tips_r')
    lina.reach_to(0.8, -1, (900, 600), t1=3.4, dur=1.0, z=60.0, shape='reach')
    a.lean_to(0.3, (1000, 760), gap=-10.0, dur=2.6, beats=2)
    a.reach_far(1.6, 1, lambda t: (lina.where(t, 'tips_r')[0] - 20, lina.where(t, 'tips_r')[1] - 30), t1=None, dur=1.6, z=40.0)
    adam.run(2.2, 3.0, 1500, 1170)
    adam.reach_to(2.9, -1, (lina, 'chest'), t1=None, dur=0.3, z=60.0)
    def ln(P, t):
        if t > 3.2: P.dx -= 0 
    lina.look_at(0.2, (a, 'eyes'), dur=0.5)
    adam.look_at(0.2, (lina, 'head'), dur=0.3)
    def lina_pull(P, t):
        u = ease_in_out(clamp((t - 3.25) / 0.35)); P.dx += 120 * u
    lina._add(3.25, None, lina_pull)
    a.slow_wave(3.8, 5.5, side=-1)
    def draw(pen, t):
        snow_street(pen, 700)
        truck_back(pen, g, ppm)
        shiver_in_window(pen, a, t, g, lean=True)
        truck_front(pen, g, ppm, 1.0, t)
        fig(pen, lina, t, PINKW); fig(pen, adam, t, PINKW)
    return dict(draw=draw, actors=[a, lina, adam], grounded=[lina, adam])


@clip('sh_glimpse_flicker', 3.0, 'The streetlight flickers. For one flicker, his face is long and white. Red eyes. Then the smile again.')
def _c_sh_glimpse():
    ppm = 520.0
    g = truck(None, 960, 780, ppm)
    a = sh(960, g['floor'], ppm)
    a.lean_to(0.0, (960, 700), gap=10.0, dur=0.01)
    a.face(0.0, -0.25)
    a.glimpse(1.30, 0.15)
    def draw(pen, t):
        on = 0.25 if 1.25 < t < 1.5 else 1.0
        pen.fill(rect(0, 0, 1920, 1080), '#0a0c16')
        truck_back(pen, g, ppm)
        shiver_in_window(pen, a, t, g, light=dict(PINKW, rim_a=int(90 * on)), lean=True)
        truck_front(pen, g, ppm, 1.0, t)
        if 1.3 <= t < 1.45: pen.fill(rect(0, 0, 1920, 1080), '#cfe0ff', 40)
        pen.fill(rect(0, 0, 1920, 1080), '#000000', int(150 * (1 - on)))
    return dict(draw=draw, actors=[a])


def _transform_times(t0=0.3, step=0.62):
    return [t0 + k * step for k in range(8)]


@clip('sh_transform_face', 5.0, 'THE TRANSFORMATION, close, at the window while he keeps waving: the smile keeps going past the cheeks; the skin pulls long, white, hard, a mask of bone; the little blue eyes sink into the dark... and come back red; the jaw drops to the chest: no throat, just dark, and icicle teeth.')
def _c_sh_transform_face():
    ppm = 900.0
    g = truck(None, 960, 1080, ppm)
    a = sh(980, g['floor'] - 0.12 * ppm, ppm)
    a.set(-1.0, None, 0.01, ws_bend=0.15)
    a.face(0.0, 0.08)
    a.slow_wave(0.0, 5.0, side=1)
    ts = [0.2, 1.0, 1.9, 2.6, 3.2, 4.2, 9.0, 9.5]
    a.transform(0.2, ts)
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#0a0c16')
        truck_back(pen, g, ppm)
        shiver_in_window(pen, a, t, g, lean=True)
    return dict(draw=draw, actors=[a])


@clip('sh_transform_legs', 4.5, 'Wide: behind him the striped uniform bulges and splits; a long brown leg punches out, jointed like a spider\'s. Click. Another. Click. Click. They plant on the truck roof beside the snowflake. The song keeps playing; the warm pink window behind him.')
def _c_sh_transform_legs():
    ppm = 300.0
    g = truck(None, 960, 700, ppm)
    a = sh(960, g['floor'], ppm)
    a.set(-1.0, None, 0.01, ws_bend=0.2)
    a.slow_wave(0.0, 4.5, side=1)
    ts = [-4.0, -3.5, -3.0, -2.5, -2.0, -0.2, 1.8, 3.6]
    a.transform(-4.0, ts)
    roof = g['roof']
    tg = {i: (960 + (1 if i % 2 == 0 else -1) * (380 + 95 * (i // 2)), roof + 4) for i in range(8)}
    a.legs_plant(-5.0, tg, stagger=0.0, dur=0.01)      # each leg unfolds straight onto its spot on the roof
    def draw(pen, t):
        snow_street(pen, 860)
        truck_back(pen, g, ppm)
        truck_front(pen, g, ppm, 1.0, t)
        pen.cv.save(); pen.cv.clipPath(rect(0, g['sill'] + 10, 1920, 2000), skia.ClipOp.kDifference, True)
        fig(pen, a, t, PINKW)
        pen.cv.restore()
    return dict(draw=draw, actors=[a])


@clip('sh_pour_out', 4.0, 'He pours out of the window. Head first. Legs last. Then the legs carry him over the edge into the snow.')
def _c_sh_pour():
    ppm = 200.0
    g = truck(None, 700, 560, ppm)
    a = sh(700, g['floor'], ppm)
    a.set(-1.0, None, 0.01, sh_m=1.0)
    a.face(0.5, 0.0)
    a.pour_out(0.3, 2.4, drop=420.0)
    def draw(pen, t):
        snow_street(pen, 760)
        truck_back(pen, g, ppm)
        truck_front(pen, g, ppm, 1.0, t)
        fig(pen, a, t, PINKW)
    return dict(draw=draw, actors=[a])


@clip('sh_scuttle_fence_car_roof', 5.0, 'He scuttles along our fence, over Dad\'s car, up onto our roof: low and fast, legs stabbing left and right, every plant a click.')
def _c_sh_scuttle():
    ppm = 150.0
    FY = 860.0
    def ground(x):
        if x < 700: return FY - 1.1 * ppm                          # the fence top
        if x < 1150: return FY - (1.45 * ppm) * math.sin(PI * clamp((x - 700) / 450))  # over the car
        return FY - 2.6 * ppm - (x - 1150) * 0.55                   # up the roof slope
    a = sh(150, FY, ppm)
    a.set(-1.0, None, 0.01, sh_m=1.0, sh_spread=0.7)
    a.face(0.75, 0.0)
    path = lambda u: (150 + 1500 * u, ground(150 + 1500 * u) + 0.2 * ppm)
    a.scuttle(0.2, 4.8, path, ground, stride=180.0, lift=70.0)
    def draw(pen, t):
        snow_street(pen, 700)
        pen.fill(rect(0, FY - 1.1 * ppm, 700, 18), '#5a4a3a')
        for k in range(14): pen.fill(rect(20 + k * 50, FY - 1.1 * ppm, 10, 1.1 * ppm), '#5a4a3a')
        pen.fill(smooth([(700, FY), (760, FY - 1.0 * ppm), (900, FY - 1.45 * ppm), (1000, FY - 1.45 * ppm), (1150, FY - 0.9 * ppm), (1150, FY)], True, 0.6), '#3a4a6a')
        pen.fill(poly([(1150, FY), (1150, FY - 2.6 * ppm), (1920, FY - 2.6 * ppm - 770 * 0.55), (1920, FY)], True), '#4a3a34')
        fig(pen, a, t, NIGHTI)
    return dict(draw=draw, actors=[a])


@clip('sh_drop_door', 3.5, 'And drops. Right in front of our door. Jaw hanging. (Adam ducks under him and slams the door.)')
def _c_sh_drop():
    ppm = 210.0
    a = sh(960, 1000, ppm)
    a.set(-1.0, None, 0.01, sh_m=1.0, sh_lift=80.0)
    a.face(0.0, 0.0)
    a.drop_to(0.6, 0.42, from_dy=-700.0)
    a.jaw_gape(1.2, 3.5)
    def draw(pen, t):
        snow_street(pen, 820)
        door(pen, 960, 1000, ppm=ppm)
        fig(pen, a, t, NIGHTI)
    return dict(draw=draw, actors=[a])


@clip('sh_legs_spear_coat', 4.5, 'Legs stab the snow round Adam as he runs with Lina in his arms; one spears his coat to the ground; he tears free; another pries at Lina (he never touches a child who is held).')
def _c_sh_spear():
    ppm = 210.0
    a = sh(300, 1000, ppm)
    a.set(-1.0, None, 0.01, sh_m=1.0, sh_lift=90.0)
    a.face(0.6, 0.0)
    adam = actor('adam_sock', 900, 1000, ppm, seed=5, expr='terrified_call')
    lina = actor('lina', 0, 0, ppm, seed=6, expr='fear')
    adam.carry(0.0, lina)
    adam.run(0.2, 4.4, 820, 1500)
    adam.face(0.6)
    lina.look_at(0.0, (a, 'eyes'), dur=0.3)
    a.leg_to(0.5, 0, lambda t: (adam.where(t, 'foot_l')[0] - 90, 1000), dur=0.18, hold=0.3, back=0.3)
    a.leg_to(1.0, 2, lambda t: (adam.where(t, 'hip')[0] - 40, adam.where(t, 'hip')[1] + 40), dur=0.2, hold=0.7, back=0.3, ev='leg_spear_coat')
    a.leg_to(2.2, 4, lambda t: (lina.where(t, 'hip')[0], lina.where(t, 'hip')[1] - 10), dur=0.3, hold=0.6, back=0.4, ev='leg_pry')
    a.leg_to(3.0, 6, lambda t: (adam.where(t, 'foot_r')[0] + 60, 1000), dur=0.18, hold=0.3, back=0.3)
    def draw(pen, t):
        snow_street(pen, 700)
        fig(pen, a, t, NIGHTI)
        CH.draw_carry_child(pen, adam, lina, t, NIGHTI, NIGHTI)
    return dict(draw=draw, actors=[a, adam, lina], grounded=[adam])


@clip('sh_face_glass', 3.5, 'At the door as "Mom": slowly, a face slides up the clear strip of glass. Long. White. Red eyes. The doorknob grows frost.')
def _c_sh_glass():
    ppm = 520.0
    a = sh(960, 1600, ppm)
    a.set(-1.0, None, 0.01, sh_long=1.0, sh_red=1.0, sh_sink=1.0, sh_smile=1.0)
    a.face(0.0, 0.0)
    def rise(P, t): P.dy -= 420 * ease_in_out(clamp((t - 0.4) / 2.4))
    a._add(-INF, None, rise)
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#3a2e26')
        strip = rect(760, 120, 400, 640)
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
    ppm = 240.0
    a = sh(960, 120, ppm)
    a.set(-1.0, None, 0.01, sh_m=1.0)
    a.face(0.0, 0.0)
    a.hang_hatch(0.4, 1.2, lower=0.62)
    adam = actor('adam_in', 760, 1040, ppm, seed=7, expr='fear'); lina = actor('lina_pj', 1160, 1040, ppm, seed=8, expr='fear')
    adam.face(0.35); lina.face(-0.35)
    adam.look_at(0.6, (a, 'eyes'), dur=0.3); lina.look_at(0.7, (a, 'eyes'), dur=0.3)
    adam.reach_to(2.3, 1, (lina, 'hand_l'), dur=0.3, z=40.0)
    a.leg_to(2.0, 1, (960, 900), dur=0.35, hold=1.2, back=0.4, ev='leg_pry')
    def draw(pen, t):
        room(pen, '#2e3446', '#4a3a30', 1040)
        pen.fill(rect(820, 0, 280, 40), '#111018')
        pen.cv.save(); pen.cv.clipPath(rect(0, 40, 1920, 1080), skia.ClipOp.kIntersect, True)
        fig(pen, a, t, NIGHTI)
        pen.cv.restore()
        fig(pen, adam, t, NIGHTI); fig(pen, lina, t, NIGHTI)
    return dict(draw=draw, actors=[a, adam, lina], grounded=[adam, lina])


@clip('sh_under_door', 3.5, 'Under the bathroom door, a needle-thin leg tip slides in, feeling for Lina\'s sock. Adam jams the towel down on it. It pulls back.')
def _c_sh_under_door():
    ppm = 700.0
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#cfd6dc')
        pen.fill(rect(0, 0, 1920, 760), '#e6e2da')
        pen.fill(rect(0, 740, 1920, 24), '#1a1418')
        u = ease_in_out(clamp((t - 0.3) / 1.2)) - ease_in_out(clamp((t - 2.5) / 0.4))
        tip = (300 + 520 * u, 770)
        pts = [(-20, 760), (tip[0] - 120, 765), tip]
        pen.line(smooth(pts, False), 10, '#6B4A32'); pen.line(poly([(tip[0] - 120, 765), tip], False), 4, '#e3e9ee')
        for k in range(6): pen.fill(oval(40 + 70 * k, 760, 6, 3), '#DCE8F2')
        pen.fill(rrect(1200, 760, 200, 110, 40), '#f2a8c4'); pen.line(rrect(1200, 760, 200, 110, 40), 4)
        if t > 1.9:
            k = ease_out_back(clamp((t - 1.9) / 0.25))
            pen.fill(rrect(380 + 300 * u, 620 + 140 * k, 380, 120, 30), '#5a8ac0'); pen.line(rrect(380 + 300 * u, 620 + 140 * k, 380, 120, 30), 4)
    return dict(draw=draw, actors=[])


@clip('sh_hook_blanket_cage', 5.0, 'Crossing the street under one blanket: legs stab the snow round them; one hooks the blanket and PULLS; then he swings round, jaw down, legs arched over them like a cage ("Inside, children. Rule seven.").')
def _c_sh_cage():
    ppm = 170.0
    a = sh(1100, 1000, ppm)
    a.set(-1.0, None, 0.01, sh_m=1.0)
    a.face(-0.3, 0.0)
    adam = actor('adam_sock', 880, 1000, ppm, seed=9, expr='fear'); lina = actor('lina', 990, 1000, ppm, seed=10, expr='fear')
    adam.face(0.4); lina.face(0.4)
    adam.hold_hand(0.0, 1, lina, -1)
    a.leg_to(0.5, 1, (760, 1000), dur=0.2, hold=0.3, back=0.3)
    a.leg_to(1.0, 3, lambda t: (lina.where(t, 'head')[0] - 10, lina.where(t, 'head')[1] - 20), dur=0.3, hold=0.9, back=0.4, ev='leg_hook_blanket')
    a.cage(2.6, 940, 520, 1000, dur=0.6, lift=200.0)
    a.jaw_gape(3.2, 5.0)
    adam.look_at(1.0, (a, 'eyes'), dur=0.3); lina.look_at(1.1, (a, 'eyes'), dur=0.3)
    def draw(pen, t):
        snow_street(pen, 620)
        fig(pen, adam, t, NIGHTI); fig(pen, lina, t, NIGHTI)
        pen.fill(smooth([(840, 640 + 8 * math.sin(t * 3)), (1050, 650), (1060, 820), (830, 830)], True, 0.5), '#8a5a7a', 180)
        fig(pen, a, t, PINKW)
    return dict(draw=draw, actors=[a, adam, lina], grounded=[adam, lina])


@clip('sh_pluck_mitten', 3.5, 'One leg plucks Lina\'s mitten from the snow and carries it back: cutaway, it hangs at the RIGHT end of his string, saving her a place. The red one at the left.')
def _c_sh_mitten():
    ppm = 330.0
    g = truck(None, 960, 700, ppm)
    def draw(pen, t):
        snow_street(pen, 820)
        truck_back(pen, g, ppm)
        truck_front(pen, g, ppm, 1.0, t, mitten_lina=ease_out_cubic(clamp((t - 1.0) / 1.2)))
        u = ease_in_out(clamp((t - 0.2) / 1.0))
        x1, y1 = g['x1'] - 20, g['top'] + 0.12 * ppm + (1 - u) * 300
        pen.line(poly([(1500, g['roof'] - 300), (1350, g['roof'] - 120), (x1, y1)], False), 16, '#6B4A32')
        pen.line(poly([(1500, g['roof'] - 300), (1350, g['roof'] - 120), (x1, y1)], False), 3, '#1a1418')
    return dict(draw=draw, actors=[])


@clip('sh_defeat_shrink', 4.5, 'Defeat: the song hangs on the empty beat; his jaw gapes for the last note and can\'t close; then the legs fold away and the skull shrinks back into the smile: "See you when it\'s this cold again!"')
def _c_sh_defeat():
    ppm = 250.0
    g = truck(None, 960, 640, ppm)
    a = sh(960, g['floor'], ppm)
    a.lean_to(0.0, (960, 600), gap=10.0, dur=0.01)
    a.set(-1.0, None, 0.01, sh_m=1.0)
    a.jaw_gape(0.2, 1.8)
    a.shrink_back(1.8, 1.8)
    a.slow_wave(3.6, 4.5, side=1)
    def draw(pen, t):
        snow_street(pen, 820)
        truck_back(pen, g, ppm)
        truck_front(pen, g, ppm, 1.0, t)
        pen.cv.save(); pen.cv.clipPath(rect(0, g['sill'] + 10, 1920, 2000), skia.ClipOp.kDifference, True)
        fig(pen, a, t, dict(PINKW, rim='#ffa040'))
        pen.cv.restore()
    return dict(draw=draw, actors=[a])


if __name__ == '__main__':
    main()
