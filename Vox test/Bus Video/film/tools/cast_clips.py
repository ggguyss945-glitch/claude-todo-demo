"""cast_clips.py: acting clips of the bus film's cast ("If The School Bus Stops At Midnight... DON'T GET ON",
characters_bus.py run by characters.py), one per scripted action, written to W/cast/clips/ (W = Bus Video/film/_work).

    cd "Vox test/Bus Video/film" && python3 tools/cast_clips.py [names...] [--fps 60] [--strip-only] [--review]

Each clip is 3-6 s at 960x540: <name>.mp4 plus <name>_strip.jpg (8 frames) and a line in clips.json with the actors'
sound events and the contact report (reach misses: frames where a hand did not reach its target; feet: the lowest
foot point vs the floor). The scenery here is a flat stand-in drawn only to check contact, eyelines and feet: the real
sets are in sets.py. Every clip stages its people with Acting.place() and world targets, the way film.py should.
"""
import os, sys, math, json, time, subprocess
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import numpy as np
import cv2
import skia
from engine.core import set_render_size, Pen, CFG, rect, rrect, oval, poly, smooth, text, mix
import characters as CH

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
WARM2 = dict(rim='#ffd9a0', rim_a=55, side=-1, key=0.1)


# ================================================================================================ bus film stand-ins
SODIUM = dict(rim='#ffb050', rim_a=75, side=1, key=-0.25)
AMBER = dict(rim='#ffa030', rim_a=95, side=1, key=-0.3)
PHONE = dict(rim='#dfeaff', rim_a=85, side=-1, key=-0.45)
STUDIO = dict(rim='#ffffff', rim_a=45, side=-1, key=0.3)
MORNING = dict(rim='#ffe2a8', rim_a=55, side=-1, key=0.2)
NIGHTB = dict(rim='#8fa6e8', rim_a=55, side=1, key=-0.3)


def ws(x, y, ppm, seed=1, who='whistle', h=None):
    a = CH.Acting(who, seed=seed, height=h or CH.height_px(who, ppm))
    a.place(x, y)
    return a


def night_yard(pen, hz=560, lamp=None):
    pen.linear(rect(0, 0, 1920, hz), 0, 0, 0, hz, [(0, '#06070c'), (1, '#1a1a22')])
    pen.fill(rect(0, hz, 1920, 1080 - hz), '#1d2a1c')
    pen.linear(rect(0, hz, 1920, 1080 - hz), 0, hz, 0, 1080, [(0, '#000000', 120), (1, '#000000', 0)])
    pen.fill(rect(0, hz - 8, 1920, 30), '#2a2a2e')
    if lamp is not None: pen.glow(lamp[0], lamp[1], 520, '#ffb050', 55 * lamp[2])


def streetlight(pen, x, y, h=520, flicker=1.0):
    pen.line(poly([(x, y), (x, y - h), (x + 60, y - h - 10)], False), 8, '#2a2c32')
    pen.fill(rrect(x + 40, y - h - 18, 50, 16, 5), '#3a3c44')
    if flicker > 0.05:
        pen.glow(x + 65, y - h, 220, '#cfe0ff', 120 * flicker)
        pen.linear(poly([(x + 45, y - h), (x + 85, y - h), (x + 200, y), (x - 70, y)]), x + 65, y - h, x + 65, y,
                   [(0, '#cfe0ff', 70 * flicker), (1, '#cfe0ff', 0)])
    return (x + 65, y - h)


def mailbox(pen, x, y, ppm, letters=1.0):
    h = 1.1 * ppm
    pen.fill(rect(x - 0.04 * ppm, y - h, 0.08 * ppm, h), '#3a3028'); pen.line(rect(x - 0.04 * ppm, y - h, 0.08 * ppm, h), 3)
    b = rrect(x - 0.24 * ppm, y - h - 0.22 * ppm, 0.48 * ppm, 0.24 * ppm, 0.1 * ppm)
    pen.fill(b, '#4a5058'); pen.line(b, 3)
    n = int(round(5 * letters))
    for k in range(n):
        pen.fill(rect(x - 0.2 * ppm + k * 0.08 * ppm, y - h - 0.17 * ppm, 0.06 * ppm, 0.12 * ppm), '#e8e2c8')


def bus_side(pen, x0, y_floor, ppm, door_x, door_open=1.0, glow='#ffa040', lit=True, color='#b89a3a', w=None):
    """An old rounded school bus seen side-on (stand-in): a folding door at door_x (open 0..1) with steps and an amber
    glow inside."""
    w = w or 9.0 * ppm
    h = 2.9 * ppm
    top = y_floor - 0.35 * ppm - h
    body = rrect(x0, top, w, h, 0.45 * ppm)
    pen.fill(body, color); pen.line(body, 4)
    pen.fill(rect(x0, top + h * 0.62, w, 0.12 * ppm), '#1a1a1a')
    for k in range(6):
        wx = x0 + 0.35 * ppm + k * 1.1 * ppm
        if abs(wx + 0.45 * ppm - door_x) < 0.9 * ppm: continue
        win = rrect(wx, top + 0.35 * ppm, 0.9 * ppm, 0.8 * ppm, 0.08 * ppm)
        pen.fill(win, '#2a1a0a' if lit else '#0c0d12')
        if lit: pen.fill(win, glow, 90)
        pen.line(win, 3)
    dw = 0.95 * ppm
    dr = rect(door_x - dw / 2, top + 0.2 * ppm, dw, y_floor - 0.25 * ppm - top - 0.2 * ppm)
    pen.fill(dr, '#140c06')
    if lit: pen.linear(dr, 0, top, 0, y_floor, [(0, glow, 140), (1, glow, 40)])
    for k in range(3):                                              # steps
        sy = y_floor - 0.25 * ppm - k * 0.28 * ppm
        pen.fill(rect(door_x - dw / 2, sy - 0.05 * ppm, dw, 0.05 * ppm), '#3a3028')
    pf = dw / 2 * (1.0 - 0.8 * door_open)
    for sd in (-1, 1):
        pnl = rect(door_x + sd * dw / 2 - (pf if sd > 0 else 0), top + 0.2 * ppm, pf, y_floor - 0.25 * ppm - top - 0.2 * ppm)
        pen.fill(pnl, '#2a2c30', 230); pen.line(pnl, 3)
    for wx in (x0 + 1.2 * ppm, x0 + w - 1.6 * ppm):
        pen.fill(oval(wx, y_floor - 0.45 * ppm, 0.48 * ppm, 0.48 * ppm), '#141414'); pen.fill(oval(wx, y_floor - 0.45 * ppm, 0.2 * ppm, 0.2 * ppm), '#6a6a6a')
    return dict(step_top=(door_x, y_floor - 0.25 * ppm - 2 * 0.28 * ppm), step_bot=(door_x, y_floor - 0.25 * ppm), door=dr, top=top)


def frame_vignette(pen, a=170):
    pen.radial(rect(0, 0, 1920, 1080), 960, 540, 1150, [(0, '#000000', 0), (0.7, '#000000', 40), (1, '#000000', a)])


def dark_over(pen, hole=None, a=235):
    cv = pen.cv
    cv.save()
    if hole is not None: cv.clipPath(hole, skia.ClipOp.kDifference, True)
    pen.fill(rect(0, 0, 1920, 1080), '#000000', a)
    cv.restore()


def blurred(pen, fn, sigma=14.0):
    cv = pen.cv
    cv.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(sigma, sigma)))
    fn()
    cv.restore()


def bus_aisle(pen, vp=(960, 430), lit=True):
    """The midnight bus seen down its aisle: dark seats both sides, an amber glow."""
    pen.fill(rect(0, 0, 1920, 1080), '#120b06')
    pen.fill(poly([(0, 1080), (1920, 1080), (vp[0] + 60, vp[1] + 60), (vp[0] - 60, vp[1] + 60)]), '#2a1e14')
    pen.fill(poly([(0, 0), (1920, 0), (vp[0] + 90, vp[1] - 90), (vp[0] - 90, vp[1] - 90)]), '#1e140c')
    pen.fill(rect(vp[0] - 90, vp[1] - 90, 180, 150), '#0a0604')
    for k in range(7):
        f = 1.0 / (1.0 + 0.55 * k)
        for sd in (-1, 1):
            x = vp[0] + sd * (130 + 760 * f); y = vp[1] + 60 + 560 * f
            seat = rrect(x - (0 if sd > 0 else 300 * f) - (300 * f if sd > 0 else 0) * 0, y - 300 * f, 300 * f, 300 * f, 20 * f)
            seat = rrect(x - 150 * f, y - 320 * f, 300 * f, 330 * f, 24 * f)
            pen.fill(seat, '#4a2a1c'); pen.line(seat, max(1.5, 4 * f))
    if lit: pen.radial(rect(0, 0, 1920, 1080), vp[0], vp[1], 900, [(0, '#ffa030', 70), (1, '#ffa030', 0)])


def clock_face(pen, x, y, r, hh=3, mm=0):
    pen.fill(oval(x, y, r, r), '#e9e2cc'); pen.line(oval(x, y, r, r), 5)
    for a, L, w in ((PI * 2 * (hh % 12 + mm / 60) / 12, 0.5, 7), (PI * 2 * mm / 60, 0.8, 4)):
        pen.line(poly([(x, y), (x + math.sin(a) * r * L, y - math.cos(a) * r * L)], False), w)


def cardboard_bus(pen, x, y, ppm):
    w, h = 3.6 * ppm, 1.9 * ppm
    b = rrect(x - w / 2, y - h, w, h, 0.3 * ppm)
    pen.fill(b, '#f2c43a'); pen.line(b, 4)
    for k in range(4):
        wr = rrect(x - w / 2 + 0.3 * ppm + k * 0.8 * ppm, y - h + 0.3 * ppm, 0.6 * ppm, 0.5 * ppm, 0.06 * ppm)
        pen.fill(wr, '#bfe0f2'); pen.line(wr, 3)
    pen.fill(rect(x - w / 2, y - h * 0.38, w, 0.1 * ppm), '#1a1a1a')
    for wx in (x - w * 0.3, x + w * 0.3):
        pen.fill(oval(wx, y - 0.1 * ppm, 0.32 * ppm, 0.32 * ppm), '#222222'); pen.line(oval(wx, y - 0.1 * ppm, 0.32 * ppm, 0.32 * ppm), 3)
    text(pen.cv, 'RIDE RIGHT', x, y - h * 0.5, 800, 0.32 * ppm, '#c43a2a', 255, 0.05)


def jump(a, t, ddx=0.0, ddy=0.0):
    """Cut an actor's position at t (a tape skip carries Sami along)."""
    a._add(t, None, lambda P, tt: (setattr(P, 'dx', P.dx + ddx), setattr(P, 'dy', P.dy + ddy)) if tt >= t else None)


# ------------------------------------------------------------------------------------------------ Mister Whistlestop
@clip('ws_tv_host_1994', 5.0, '1994, Channel 6: a cat taller than the cardboard bus behind him, crooked yellow hat, whistle, the grin that never moves: "Write your name, your school and your bus on your card! Hold it up to the camera! Ride right, kids!"')
def _c_ws_tv():
    ppm = 210.0
    a = ws(1080, 980, ppm, 1, 'whistle94')
    a.face(-0.15)
    a.host(0.2, 2.2)
    a.say([(0.3, 2.1, 'Write your name your school and your bus on your card'), (2.4, 3.4, 'Hold it up to the camera'),
           (3.8, 4.6, 'Ride right kids')])
    a.reach_far(2.3, -1, (760, 330), t1=3.5, dur=0.45, z=260.0, shape='point')
    a.ws_rest(3.6, 1, 'host', 4.9, 0.4); a.ws_rest(3.6, -1, 'host', 4.9, 0.4)
    def draw(pen, t):
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 1080, [(0, '#5ab0e0'), (1, '#2a78b8')])
        pen.fill(rect(0, 980, 1920, 100), '#3a8a4a')
        cardboard_bus(pen, 620, 980, ppm)
        fig(pen, a, t, STUDIO)
    return dict(draw=draw, actors=[a], grounded=[a])


@clip('kids94_cards', 4.0, 'The kids hold up their cards (name, school, bus) to the camera; at the end of the row, a small boy in a yellow raincoat, his card unreadable')
def _c_kids94():
    ppm = 330.0
    ks = []
    texts = ('AMY R.|LARKFIELD EL.|BUS 4', 'DEVON|LARKFIELD EL.|BUS 9', 'KATIE M.|LARKFIELD EL.|BUS 2', ' | | ')
    for i, w in enumerate(('kid94_a', 'kid94_b', 'kid94_c', 'theo_color')):
        k = actor(w, 420 + i * 380, FLOOR, ppm, seed=60 + i, expr='proud_grin' if i < 3 else 'lonely')
        k.face(0.0)
        k.base['card_text'] = texts[i]
        t0 = 0.3 + 0.35 * i if i < 3 else 1.6
        k.hold_prop('name_card', 1, -1.0, None)
        k.reach_to(t0, 1, lambda t, k=k: (k.where(t, 'chin', post=False)[0] + 0.03 * k.height, k.where(t, 'chin', post=False)[1] + 0.13 * k.height),
                   dur=0.5, contact='grip', shape='grip', z=150.0)
        k.reach_to(t0 + 0.05, -1, lambda t, k=k: (k.where(t, 'chin', post=False)[0] - 0.07 * k.height, k.where(t, 'chin', post=False)[1] + 0.19 * k.height),
                   dur=0.5, contact='palm', shape='grip', z=150.0)
        k.set(-1.0, None, 0.01, lock=1.0 if i < 3 else 0.0)
        if i == 3: k.look_at(0.0, (1300, 700), dur=0.4)
        ks.append(k)
    def draw(pen, t):
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 1080, [(0, '#4aa0d0'), (1, '#2a68a8')])
        pen.fill(rect(0, FLOOR, 1920, 140), '#3a8a4a')
        for k in ks: fig(pen, k, t, STUDIO)
    return dict(draw=draw, actors=ks, grounded=ks)


@clip('ws_unfold_door', 5.0, 'Through a gap in the curtains: his bus door folds open; something unfolds out of it, like a ladder: up, and up, and up')
def _c_ws_unfold():
    ppm = 165.0
    bus = dict(x0=900.0, door_x=1180.0)
    a = ws(1180, 1010, ppm, 2)
    a.face(-0.35)
    ev = a.unfold(0.6, 3.0)
    a.look_at(3.9, (300, 600), dur=0.9)
    def draw(pen, t):
        night_yard(pen, 640, (1500, 300, 1.0))
        bus_side(pen, 900, 1010, ppm, 1180, door_open=clamp(t / 0.5))
        fig(pen, a, t, AMBER)
        frame_vignette(pen, 200)
    return dict(draw=draw, actors=[a])


@clip('ws_skip_lawn', 5.0, 'The streetlight flickers: he\'s at our mailbox. Flicker: the middle of the lawn. Flicker: the porch steps. He never walks; he skips, like a tape')
def _c_ws_skip():
    a = ws(1400, 610, 0, 3, h=150.0)
    ks = [(0.0, dict(x=1400, y=610, h=150.0, turn=-0.4, h_turn=0.3)),
          (1.2, dict(x=560, y=700, h=215.0, turn=0.25, h_turn=0.15, ws_elev=0.0)),
          (2.5, dict(x=1080, y=840, h=345.0, turn=-0.15, h_turn=0.0, ws_elev=-0.03)),
          (3.7, dict(x=840, y=1110, h=600.0, turn=0.0, h_turn=0.0, ws_elev=-0.07))]
    ev = a.tape_skip(ks)
    a.reach_far(3.95, -1, (760, 600), t1=None, dur=0.8, z=330.0, shape='claw')
    flick = [k_[0] for k_ in ks[1:]]
    def draw(pen, t):
        fl = 0.0 if any(-0.08 < t - f < 0.05 for f in flick) else 1.0
        night_yard(pen, 560, (1650, 180, fl))
        streetlight(pen, 1600, 600, 420, fl)
        mailbox(pen, 470, 712, 200, 0.0)
        pen.fill(poly([(520, 1080), (1400, 1080), (1180, 940), (740, 940)]), '#2a2420')
        fig(pen, a, t, SODIUM)
        if fl < 0.5: pen.fill(rect(0, 0, 1920, 1080), '#000000', 150)
        for sd in (-1, 1):
            pen.fill(rect(960 + sd * 960 - (380 if sd > 0 else 0), 0, 380, 1080), '#3a1e22')
        frame_vignette(pen, 220)
    return dict(draw=draw, actors=[a])


@clip('ws_door_curl', 4.5, 'White gloves curl around our doorframe. Too many knuckles. (He peeks round the frame; every finger folds on four hinges)')
def _c_ws_curl():
    ppm = 700.0                                      # close: the head and gloves big in frame (mood ref 1)
    a = ws(930, 1180, ppm, 4)
    a.face(0.3)
    a.set(-1.0, None, 0.01, ws_hands_front=3, tilt=9.0, h_tilt=-14.0)
    hx0, hy0 = a.where(0.0, 'head')
    a.place(930 + (975 - hx0), 1180 + (440 - hy0))   # his body stays hidden behind the wall; only the head leans out
    a.set(0.4, None, 1.3, tilt=11.0)                 # ...and slides further round the frame
    hy0 = a.where(0.0, 'head')[1]
    a.curl_door(0.3, 1, (1010, hy0 - 150), dur=0.9, z=-8.0)
    a.curl_door(0.8, -1, (1010, hy0 + 300), dur=0.9, z=-8.0)
    a.look_at(1.8, (1500, 450), dur=0.9)
    a.look_at(3.2, (1250, 520), dur=0.05, snap=True)
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#2a2422')
        pen.fill(rect(1000, 0, 920, 1080), '#141418')
        pen.glow(1150, 420, 420, '#ffa040', 40)
        pen.fill(rect(0, FLOOR, 1920, 140), '#2a201a')
        hx, hy = a.where(t, 'head'); cx_, cy_ = a.where(t, 'chin')
        rr = 1.45 * max(cy_ - hy, 30.0)
        pen.cv.save()                                # nothing of him past the frame but the half face, an ear, the hat
        mask = union(rect(960, -10, max(1.0, hx + rr - 960), max(1.0, hy + 10)), oval(hx, hy, rr * 1.15, (cy_ - hy) * 1.45))
        pen.cv.clipPath(mask, skia.ClipOp.kIntersect, True)
        fig(pen, a, t, SODIUM)
        pen.cv.restore()
        pen.fill(rect(0, 0, 1000, 1080), '#5a4a3e'); pen.line(rect(0, -10, 1000, 1100), 4)
        pen.fill(rect(960, 0, 60, 1080), '#e2d8c4'); pen.line(rect(960, -10, 60, 1100), 4)
        CH.draw_whistle_hands(pen, a, t, (1, -1), SODIUM)
        frame_vignette(pen, 160)
    return dict(draw=draw, actors=[a])


@clip('ws_frosted_glass', 4.0, 'Through the frosted glass: a crooked hat, and that grin. He calls roll: "Della? Long time!" "Mina?" "Sami?"')
def _c_ws_frost():
    ppm = 260.0
    a = ws(960, 1190, ppm, 5)
    a.face(0.0)
    a.set(-1.0, None, 0.01, ws_bend=0.12)
    a.say([(0.4, 1.4, 'Della Long time'), (1.9, 2.4, 'Mina'), (3.0, 3.5, 'Sami')])
    a.set(1.8, 2.6, 0.2, h_tilt=-14.0); a.set(2.9, None, 0.2, h_tilt=12.0)
    glass = rrect(720, 160, 480, 640, 10)
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#3a2a20')
        pen.cv.save(); pen.cv.clipPath(glass, skia.ClipOp.kIntersect, True)
        pen.fill(glass, '#6a5a44')
        pen.glow(960, 300, 500, '#ffb050', 120)
        blurred(pen, lambda: fig(pen, a, t, SODIUM), 7.0)
        pen.fill(glass, '#e8e2d4', 70)
        pen.cv.restore()
        pen.line(glass, 8, '#1a1410')
        pen.fill(rect(660, 120, 600, 40), '#4a3424'); pen.fill(rect(660, 800, 600, 280), '#4a3424')
    return dict(draw=draw, actors=[a])


@clip('ws_peephole', 3.5, 'The peephole goes white. Fur. Grin. (The fisheye: he is pressed against the door, then eases back so the grin fills it)')
def _c_ws_peep():
    a = ws(0, 0, 300.0, 6)
    UNDER = dict(SODIUM, under='#c98a3a', under_a=180)
    # white fur pressed to the lens, then he is back on the porch; every tape skip puts him closer, the last one the
    # grin filling the lens (the barrel warp of the peephole bulges the middle: k ~ 0.35)
    stages = ((0.30, 'full', 900.0, 0.0, 6.0), (1.10, 'full', 1500.0, 0.0, -7.0), (1.85, 'bust', 0.95, 0.45, 9.0), (2.55, 'bust', 0.95, 1.0, -3.0))
    cache = {}

    def warp_maps(w, h, k1=0.35):
        if (w, h) not in cache:
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
            cx, cy, R = w / 2.0, h / 2.0, 470.0 * w / 1920.0
            dx, dy = xx - cx, yy - cy
            r2 = np.clip((dx * dx + dy * dy) / (R * R), 0, 1.0)
            s = (1.0 - k1) + k1 * r2
            cache[(w, h)] = ((cx + dx * s).astype(np.float32), (cy + dy * s).astype(np.float32))
        return cache[(w, h)]

    def draw(pen, t):
        W, H, kz = CFG.rw, CFG.rh, CFG.k
        surf = skia.Surface(W, H); c2 = surf.getCanvas(); c2.clear(skia.Color(14, 10, 6)); c2.scale(kz, kz)
        p2 = Pen(c2)
        p2.fill(rect(0, 640, 1920, 440), '#1e150c'); p2.glow(980, 260, 700, '#ffb050', 70)
        si = max([i for i, s in enumerate(stages) if t >= s[0]] or [0])
        t0, kind, sz, appr, tilt = stages[si]
        nxt = stages[si + 1][0] if si + 1 < len(stages) else 3.6
        creep = clamp((t - t0) / max(nxt - t0, 0.1))
        P = a.at(t); P.h_tilt += tilt
        if t - t0 < 0.05 and si > 0: P.ws_glitch = 0.85          # 3 frames of tape tear on every skip
        if kind == 'full':
            hpx = sz * (1.0 + 0.06 * creep)
            P.approach = 0.0
            CH.draw(p2, 'whistle', 960, 560 + 0.82 * hpx, hpx, P, light=UNDER, t=t)
        else:
            P.approach = min(1.0, appr + 0.08 * creep)
            kk = 1.0 + 1.1 * P.approach
            CH.draw_bust(p2, 'whistle', 960 + 18 * (1 - P.approach), 540 - 105 * kk - 150 * P.approach ** 2, sz * (1.0 + 0.04 * creep), P, light=UNDER, t=t)
        # the porch light is below him: the top of the lens falls off to black, an amber pool from under the chin
        p2.linear(rect(0, 0, 1920, 1080), 0, 60, 0, 620, [(0, '#000000', 200), (1, '#000000', 0)])
        p2.linear(rect(0, 0, 1920, 1080), 0, 700, 0, 1080, [(0, '#c98a3a', 0), (1, '#c98a3a', 70)])
        img = surf.makeImageSnapshot().toarray()
        mx, my = warp_maps(img.shape[1], img.shape[0])
        img = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        cv = pen.cv
        cv.save(); cv.resetMatrix()
        cv.drawImage(skia.Image.fromarray(np.ascontiguousarray(img[:, :, [2, 1, 0, 3]])), 0, 0)
        cv.restore()
        circ = oval(960, 540, 470, 470)
        if t < 0.30: pen.fill(circ, '#efe8d6', 255 * (1.0 - t / 0.30) ** 0.4 if t > 0.12 else 255)    # fur pressed to the glass
        if si > 0 and t - t0 < 0.05: CH.ws_tracking(pen, 490, 300, 940, 480, 0.9, t, si)
        pen.radial(circ, 960, 540, 470, [(0, '#000000', 0), (0.7, '#000000', 30), (1, '#000000', 230)])
        dark_over(pen, circ, 255)
    return dict(draw=draw, actors=[a])


@clip('ws_dark_grip', 5.5, 'Two ten, total black: a small hand slides into mine. Cold. I turn on my phone light: a white glove, one knuckle too many, folded small around my fingers; in his other glove, my walkie, pressed to the grin. I rip free')
def _c_ws_grip():
    ppm = 270.0
    seat = FLOOR - 0.45 * ppm
    m = actor('mina', 760, FLOOR, ppm, seed=7, expr='hush_fear')
    m.face(0.55); m.seated(seat, hands=None)
    m.reach_to(-1.0, -1, (930, seat - 10), t1=4.2, dur=0.01, contact='palm', shape='open', z=40.0)
    m.hold_prop('cell', 1, -1.0, None)
    m.reach(-1.0, None, 1, out=-30.0, down=120.0, fwd=200.0, shape='grip', up=0.0, fade=0.01)
    m.look_at(0.0, (1300, 400), t1=1.9, dur=0.3)
    m.look_at(2.3, (m, 'hand_r'), t1=3.9, dur=0.25)
    m.expr('shock', 2.5, 4.0, 0.15)
    m.reach_to(4.2, -1, (m, 'chest'), dur=0.25, contact='palm', shape='grip', z=60.0)
    m.expr('fear', 4.2, None, 0.2)
    a = ws(1230, FLOOR, ppm, 8)
    a.face(-0.55)
    a.set(-1.0, None, 0.01, ws_bend=0.35, ws_crouch=0.25)
    a.grip_small(0.4, 1, m, -1, t1=4.25, dur=0.9)
    a.walkie_to_grin(-1.0, -1, None, 0.01)
    a.say([(1.2, 2.0, 'heh heh')])
    def draw(pen, t):
        room(pen, '#2a2622', '#2a201a')
        couch(pen, 860, seat, 640)
        if t < 4.4: fig(pen, a, t, dict(PHONE, under='#dfe8ff', under_a=200, dark=0.6) if t > 2.1 else PHONE)
        fig(pen, m, t, PHONE)
        if t < 4.4:
            if t > 2.1:
                hx, hy = m.where(t, 'hand_r')
                gx, gy = a.where(t, 'mouth')
                pen.radial(rect(0, 0, 1920, 1080), (hx + gx) / 2, (hy + gy) / 2 + 60, 560,
                           [(0, '#000000', 0), (0.45, '#000000', 90), (1, '#000000', 238)], sy=0.85)
                pen.glow(hx, hy, 160, '#dfeaff', 60)
            else:
                dark_over(pen, None, 246)
    return dict(draw=draw, actors=[m, a], grounded=[m])


@clip('ws_walkie_grin', 4.0, 'In his other glove: my walkie-talkie, pressed to the grin (Sami\'s voice comes out of it); the grin never moves')
def _c_ws_walkie():
    ppm = 420.0
    a = ws(980, 1520, ppm, 9)
    a.face(-0.25)
    a.set(-1.0, None, 0.01, ws_bend=0.15)
    a.walkie_to_grin(0.3, -1, None, 0.7)
    a.say([(1.3, 3.4, 'say our word so I know it is really me')])
    a.set(1.0, None, 0.6, h_tilt=-10.0)
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#0c0c10')
        pen.glow(700, 900, 700, '#dfeaff', 60)
        fig(pen, a, t, PHONE)
    return dict(draw=draw, actors=[a])


@clip('ws_hallway_bent', 4.5, 'The hallway is full of him: bent double, hat crushed against the ceiling, gloves flat on both walls. "Sami?"')
def _c_ws_hall():
    ppm = 250.0
    ceil = FLOOR - 2.4 * ppm
    a = ws(960, FLOOR, ppm, 10)
    a.face(0.3)
    a.bend_double(-1.0, ceil, None, 0.01, crouch=0.4, bend=1.0)
    a.walls_flat(0.4, (690, 690), (1230, 690), dur=0.9)
    a.say([(2.4, 2.9, 'Sami')])
    a.set(2.2, None, 0.35, h_tilt=-18.0)
    a.look_at(3.3, (1300, 700), dur=0.05, snap=True)
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#2e2620')
        pen.fill(poly([(0, 0), (680, ceil), (1240, ceil), (1920, 0)]), '#3c322a')
        pen.fill(poly([(0, 0), (680, ceil), (680, FLOOR), (0, 1080)]), '#4a3c30')
        pen.fill(poly([(1920, 0), (1240, ceil), (1240, FLOOR), (1920, 1080)]), '#4a3c30')
        pen.fill(poly([(0, 1080), (680, FLOOR), (1240, FLOOR), (1920, 1080)]), '#3a2a1e')
        for p_ in ((680, ceil, 680, FLOOR), (1240, ceil, 1240, FLOOR), (680, ceil, 1240, ceil), (680, FLOOR, 1240, FLOOR)):
            pen.line(poly([(p_[0], p_[1]), (p_[2], p_[3])], False), 3)
        fig(pen, a, t, AMBER)
        frame_vignette(pen, 170)
    return dict(draw=draw, actors=[a], grounded=[a])


@clip('ws_crossing_guard', 5.0, 'He takes Sami\'s hand, like a crossing guard; I grab the other. The lights blink and we\'re on the stairs... Sami\'s hand slips out of mine')
def _c_ws_guard():
    ppm = 230.0
    a = ws(700, FLOOR, ppm, 11)
    s_ = actor('sami', 960, FLOOR, ppm, seed=12, expr='dazed')
    m = actor('mina', 1130, FLOOR, ppm, seed=13, expr='fear')
    a.face(0.45); s_.face(0.45); m.face(-0.45)
    a.hold_child(0.2, 1, s_, -1, dur=0.8)
    m.hold_hand(0.5, -1, s_, 1, t1=3.0, dur=0.5)
    s_.look_at(0.0, (a, 'head'), dur=0.4)
    m.look_at(0.0, (s_, 'eyes'), dur=0.3)
    m.expr('terrified_call', 3.1, None, 0.15)
    m.reach_to(3.4, -1, (930, 780), dur=0.3, contact='palm', shape='open', z=60.0)
    ev = a.tape_skip([(0.0, dict()), (3.3, dict(x=480))])
    jump(s_, 3.3, -220.0)
    def draw(pen, t):
        blink = any(-0.06 < t - b < 0.06 for b in (1.4, 2.2, 3.3))
        room(pen, '#3a3028', '#2a201a')
        fig(pen, a, t, AMBER); fig(pen, s_, t, AMBER); fig(pen, m, t, AMBER)
        if blink: pen.fill(rect(0, 0, 1920, 1080), '#000000', 235)
    return dict(draw=draw, actors=[a, s_, m], grounded=[a, s_, m])


@clip('ws_window_backwards', 4.0, 'His head comes out of the driver\'s window, and turns. Backwards. Grinning at us')
def _c_ws_back():
    ppm = 600.0
    a = ws(900, 1640, ppm, 14)
    a.face(1.0)
    a.set(-1.0, None, 0.01, ws_crouch=0.35, ws_bend=0.1)
    ev = a.head_backwards(1.0, 1.6)
    win_y = 600
    def draw(pen, t):
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 1080, [(0, '#05060a'), (1, '#12141a')])
        sh = 6 * math.sin(t * 13.0)
        pen.fill(rect(0, win_y + sh, 1920, 1080), '#7a6a30')
        pen.fill(rect(560, win_y - 480 + sh, 800, 480), '#1a0e06')
        pen.linear(rect(560, win_y - 480 + sh, 800, 480), 0, win_y - 480, 0, win_y, [(0, '#ffa030', 60), (1, '#ffa030', 20)])
        pen.cv.save(); pen.cv.clipPath(rect(0, -400, 1920, win_y + sh + 400), skia.ClipOp.kIntersect, True)
        fig(pen, a, t, AMBER, y=a.y0 + sh)
        pen.cv.restore()
        pen.line(rect(560, win_y - 480 + sh, 800, 480), 6)
        pen.fill(rect(0, win_y + sh, 1920, 16), '#3a3010')
    return dict(draw=draw, actors=[a])


@clip('ws_steps_clipboard', 4.5, 'Doors open. Amber light. He\'s at the top of the steps, with his clipboard: "Last stop! Everybody counted?"')
def _c_ws_steps():
    ppm = 250.0
    y_top = FLOOR - 0.25 * ppm - 2 * 0.28 * ppm
    a = ws(1180, y_top, ppm, 15)
    a.face(-0.35)
    a.clipboard(-INF, 1)
    top = FLOOR - 0.35 * ppm - 2.9 * ppm + 0.2 * ppm
    a.bend_double(-1.0, top, None, 0.01, crouch=0.15, bend=0.3)
    a.say([(0.8, 2.6, 'Last stop Everybody counted')])
    a.set(0.6, None, 1.2, ws_bend=0.25)
    m = actor('mina_bare', 860, FLOOR, ppm, seed=16, expr='fear')
    m.face(0.7)
    m.look_at(0.0, (a, 'head'), dur=0.3)
    a.look_at(0.4, (m, 'eyes'), dur=0.8)
    def draw(pen, t):
        night_yard(pen, 600)
        bus_side(pen, 860, FLOOR, ppm, 1180)
        fig(pen, a, t, AMBER); fig(pen, m, t, AMBER)
    return dict(draw=draw, actors=[a, m], grounded=[m])


@clip('ws_glove_snap', 4.5, 'Sami scrambles for the door; a glove snaps shut on his pajamas. Rip. He tumbles into my arms, half his dinosaur tail gone')
def _c_ws_snap():
    ppm = 200.0
    y_top = FLOOR - 0.25 * ppm - 2 * 0.28 * ppm
    a = ws(1380, y_top, ppm, 17)
    a.face(-0.5)
    s_ = actor('sami', 1180, FLOOR, ppm, seed=18, expr='shout_here')
    s_.face(-1.0)
    s_.run(0.2, 2.0, 0.0, -380.0, surface='porch')
    tail_pt = lambda t: (s_.where(t, 'hip', post=False)[0] + 0.25 * s_.height, s_.where(t, 'hip', post=False)[1] + 0.12 * s_.height)   # noqa: E731
    ev = a.snap_glove(0.55, -1, tail_pt, t1=1.0)
    a.ws_hold(1.0, -1, 'tail_piece', None, 'snap')
    a.reach_far(1.0, -1, (1260, 520), dur=0.6, z=40.0, shape='snap')
    m = actor('mina_bare', 640, FLOOR, ppm, seed=19, expr='terrified_call')
    m.face(0.6)
    m.look_at(0.0, (s_, 'eyes'), dur=0.3)
    m.crouch(1.6, 0.6, None, 0.5)
    m.reach_to(1.7, 1, (s_, 'chest'), t1=None, dur=0.4, contact='palm', shape='open', z=60.0)
    m.reach_to(1.75, -1, (s_, 'belly'), t1=None, dur=0.4, contact='palm', shape='open', z=70.0)
    m.expr('relief', 2.6, None, 0.5)
    s_.expr('cry', 1.4, None, 0.3)
    def draw(pen, t):
        night_yard(pen, 600)
        bus_side(pen, 1060, FLOOR, ppm, 1380)
        fig(pen, a, t, AMBER)
        CH.draw(pen, 'sami' if t < 1.0 else 'sami_torn', s_.x0, s_.y0, s_.height, s_.at(t), light=AMBER, t=t)
        fig(pen, m, t, AMBER)
    return dict(draw=draw, actors=[a, s_, m], grounded=[s_])


@clip('ws_aisle_reach', 5.0, 'At the back, seat twenty-two glows: the boy in the yellow raincoat. One impossibly long arm reaches down the aisle, and a glove settles on his shoulder')
def _c_ws_aisle():
    ppm_t = 150.0
    th = actor('theo', 1060, 640, ppm_t, seed=20, expr='lonely')
    th.face(-0.2); th.seated(640 - 0.42 * ppm_t, hands='lap')
    a = ws(470, 1330, 340.0, 21)
    a.face(0.55)
    a.set(-1.0, None, 0.01, ws_bend=0.1)
    a.reach_far(0.6, 1, lambda t: th.where(t, 'shoulder_r', post=False), t1=None, dur=2.4, z=-40.0, shape='hang', ease=ease_in_out)
    th.look_at(3.1, (th, 'shoulder_r'), dur=0.6)
    th.expr('hush_fear', 3.1, None, 0.6)
    def draw(pen, t):
        bus_aisle(pen, (960, 430))
        pen.glow(1060, 520, 160, '#ffd070', 120)
        fig(pen, th, t, AMBER)
        fig(pen, a, t, AMBER)
        frame_vignette(pen, 180)
    return dict(draw=draw, actors=[a, th])


@clip('ws_lean_to_mina', 5.0, 'He bends down, and down, until the grin is a foot from my face. Soft. Kind. "Trade seats with him, Mina... Hurry. Just you. Our secret."')
def _c_ws_lean():
    ppm = 230.0
    m = actor('mina_bare', 760, FLOOR, ppm, seed=22, expr='fear')
    m.face(0.55)
    a = ws(1010, FLOOR, ppm, 23)
    a.face(-0.55)
    a.lean_to(0.3, (m, 'eyes'), gap=32.0, dur=2.6, beats=2)
    a.ws_rest(0.6, 1, 'chest', None, 0.8)
    a.say([(3.0, 4.6, 'Hurry Just you Our secret')], amount=0.6)
    a.look_at(0.0, (m, 'eyes'), dur=0.8)
    m.look_at(0.0, (a, 'eyes'), dur=0.4)
    m.expr('tempted', 3.0, None, 0.8)
    m.set(1.6, None, 0.8, lean=-0.08)
    def draw(pen, t):
        night_yard(pen, 600)
        fig(pen, m, t, AMBER); fig(pen, a, t, AMBER)
    return dict(draw=draw, actors=[a, m], grounded=[m])


@clip('ws_whistle_two', 3.0, 'Fweet-fweet: the silver whistle rides up its orange lanyard to the grin, two short blasts')
def _c_ws_wh2():
    ppm = 300.0
    a = ws(960, 1240, ppm, 24)
    a.face(0.2)
    ev = a.blow_whistle(0.5, 'two', -1)
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#140c06'); pen.glow(960, 300, 800, '#ffa030', 70)
        fig(pen, a, t, AMBER)
    return dict(draw=draw, actors=[a])


@clip('ws_whistle_long_clock', 4.0, 'The grin swings to the school clock. He blows the whistle, long and loud, to drown us out')
def _c_ws_wh_long():
    ppm = 230.0
    a = ws(900, FLOOR, ppm, 25)
    a.face(-0.3)
    a.look_at(0.5, (1550, 220), dur=0.05, snap=True)
    ev = a.blow_whistle(1.0, 'long', 1)
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#14100c'); pen.fill(rect(1300, 0, 620, 520), '#2a2420')
        clock_face(pen, 1550, 220, 90, 2, 59 + clamp(t / 4.0))
        pen.fill(rect(0, FLOOR, 1920, 140), '#1a1a1c')
        fig(pen, a, t, AMBER)
    return dict(draw=draw, actors=[a], grounded=[a])


@clip('ws_defeat', 5.5, 'Three o\'clock. His bus is empty. The grin doesn\'t fit his face; it slips. Tracking lines tear through him, and the bus rewinds into the dark. His clipboard clatters onto the asphalt')
def _c_ws_defeat():
    ppm = 210.0
    a = ws(1000, FLOOR, ppm, 26)
    a.face(-0.2)
    a.clipboard(-INF, 1)
    drop = 1.6
    a._add(drop, None, lambda P, t: (setattr(P, 'hl_prop', None), setattr(P, 'hl_shape', 'open')) if t >= drop else None)
    ev = a.defeat(0.3, 1.4, 1.8)
    a._ev(drop + 0.42, 'clipboard_clatter', 0.0)
    st = {}
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#0a0a0e'); pen.fill(rect(0, FLOOR, 1920, 140), '#26262a')
        if 'hand' not in st and t >= drop: st['hand'] = a.where(drop - 1 / 60.0, 'hand_l')
        fig(pen, a, t, AMBER)
        if t >= drop:
            hx, hy = st['hand']
            u = clamp((t - drop) / 0.42)
            y = hy + (FLOOR - 8 - hy) * u * u
            ang = 80.0 * u
            c = CH.Ctx(pen, skia.Matrix(), 3.0).sub(hx + 30 * u, y, ang if u < 1 else 86.0, ppm / 100.0)
            c.lw = 3.0 / (ppm / 100.0)
            CH._ws_clipboard(c, 2, t, None)
    return dict(draw=draw, actors=[a])


@clip('ws_final_sting', 5.0, 'Out the back window, something very tall in a crooked yellow hat lifts a new clipboard; draws a line through one name, and starts writing the next')
def _c_ws_sting():
    a = ws(1100, 760, 0, 27, h=210.0)
    a.face(-0.1)
    a.clipboard(0.6, 1, new=True)
    ev = a.write_line(2.0, 3.0)
    def draw(pen, t):
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 760, [(0, '#c8d8e8'), (1, '#e8e0cc')])
        pen.fill(rect(0, 760, 1920, 320), '#8a8a84')
        fig(pen, a, t, MORNING)
        win = rrect(420, 160, 1080, 700, 60)
        pen.cv.save(); pen.cv.clipPath(win, skia.ClipOp.kDifference, True)
        pen.fill(rect(0, 0, 1920, 1080), '#c9a23a'); pen.fill(rect(0, 0, 1920, 1080), '#000000', 60)
        pen.cv.restore()
        pen.line(win, 10, '#1a1a1a')
    return dict(draw=draw, actors=[a])


@clip('ws_punch_ticket', 3.0, 'Click-clack: the chrome ticket punch bites through a yellow ticket (SAMI. SEAT 4. LAST STOP 3 A.M.)')
def _c_ws_punch():
    ppm = 420.0
    a = ws(960, 1500, ppm, 28)
    a.face(-0.1)
    a.ws_hold(-INF, 1, 'ticket_y', None, 'pinch')
    a.ws_rest(0.0, 1, 'clip', None, 0.01)
    ev = a.punch(1.0, -1)
    a.reach_far(0.3, -1, lambda t: a.where(t, 'hand_l', post=False), t1=None, dur=0.6, z=10.0, shape='hold')
    a.look_at(0.0, (900, 760), dur=0.6)
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#140c06'); pen.glow(960, 500, 700, '#ffa030', 60)
        fig(pen, a, t, AMBER)
    return dict(draw=draw, actors=[a])


# ------------------------------------------------------------------------------------------------ the people
@clip('della_brakes_names', 4.0, 'Grandma Della at bus 9, morning: "Brakes, mirrors, names," she says. "That\'s the job." A good morning, by name')
def _c_della_job():
    ppm = 300.0
    d = actor('della', 900, FLOOR, ppm, seed=30, expr='warm')
    d.face(0.4)
    d.talk([(0.3, 1.8, 'Brakes mirrors names'), (2.2, 3.0, "That's the job")], env=None, words=None)
    d.point_at(0.4, (1500, 380), t1=1.8, side=1)
    d.look_at(0.4, (1500, 380), t1=1.9, dur=0.3)
    d.look_at(2.1, (1300, 700), dur=0.3)
    d.wave(2.4, 3.8, side=-1, slow=True)
    def draw(pen, t):
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 1080, [(0, '#bcd6ef'), (1, '#e8e0cc')])
        bus_side(pen, 1150, FLOOR, ppm * 0.7, 1500, door_open=1.0, lit=False, color='#e2b43a', w=2000)
        pen.fill(rect(0, FLOOR, 1920, 140), '#8a8a84')
        fig(pen, d, t, MORNING)
    return dict(draw=draw, actors=[d], grounded=[d])


@clip('della_mailbox', 4.0, 'Grandma unscrews the letters off our mailbox')
def _c_della_mail():
    ppm = 340.0
    d = actor('della', 870, FLOOR, ppm, seed=31, expr='set_jaw')
    d.face(0.55)
    bx = (1080, FLOOR - 1.2 * ppm)
    for k in range(3):
        d.reach_to(0.2 + k * 1.1, 1, (bx[0] - 60 + 45 * k, bx[1] + 5), t1=0.9 + k * 1.1, dur=0.35, contact='grip', shape='grip', z=40.0)
    d.reach_to(0.2, -1, (bx[0] - 40, bx[1] + 30), dur=0.4, contact='palm', shape='flat', z=60.0)
    d.look_at(0.0, bx, dur=0.3)
    def draw(pen, t):
        night_yard(pen, 520, (300, 200, 0.6))
        mailbox(pen, 1080, FLOOR, ppm, letters=1.0 - clamp((t - 0.7) / 3.0))
        fig(pen, d, t, NIGHTB)
    return dict(draw=draw, actors=[d], grounded=[d])


@clip('della_rules_door', 4.5, 'The night before the first day, Grandma tapes seven rules inside the front door; this year she also whispers our family word')
def _c_della_rules():
    ppm = 330.0
    d = actor('della', 920, FLOOR, ppm, seed=32, expr='calm_firm')
    dp = door_pts(700, ppm)
    d.face(-0.6)
    sheet = (720, FLOOR - 1.3 * ppm)
    d.reach_to(0.2, 1, (sheet[0] + 60, sheet[1] - 70), t1=1.6, dur=0.5, contact='palm', shape='flat', z=-40.0)
    d.reach_to(0.3, -1, (sheet[0] - 50, sheet[1] - 70), t1=1.6, dur=0.5, contact='palm', shape='flat', z=-40.0)
    d.look_at(0.0, sheet, t1=1.8, dur=0.3)
    s_ = actor('sami', 1180, FLOOR, ppm, seed=33, expr='sleepy')
    s_.face(-0.4)
    d.turn(2.0, 0.5, 0.6)
    d.crouch(2.3, 0.45, None, 0.6)
    d.look_at(2.3, (s_, 'eyes'), dur=0.3)
    d.expr('whisper', 2.6, None, 0.3)
    d.talk([(2.9, 3.8, 'family word')], env=None, words=None, intensity=0.4)
    s_.look_at(2.5, (d, 'eyes'), dur=0.3)
    def draw(pen, t):
        room(pen, '#4a3a30', '#3a2a20')
        door(pen, 700, FLOOR, ppm=ppm)
        if t > 0.6: pen.fill(rect(sheet[0] - 70, sheet[1] - 100, 140, 190), '#f6f2e6'); pen.line(rect(sheet[0] - 70, sheet[1] - 100, 140, 190), 2.5)
        fig(pen, s_, t, WARM2); fig(pen, d, t, WARM2)
    return dict(draw=draw, actors=[d, s_], grounded=[d, s_])


@clip('della_keys_leave', 4.5, 'Grandma grabs her keys: "Bus 9 has a radio to the depot. Lock this behind me." She slips out the back, her flashlight on')
def _c_della_keys():
    ppm = 300.0
    d = actor('della', 1100, FLOOR, ppm, seed=34, expr='set_jaw')
    d.face(-0.4)
    hook = (990, FLOOR - 1.45 * ppm)
    d.hold_prop('maglite', -1, -1.0, None)
    d.reach_to(0.2, 1, hook, t1=0.8, dur=0.5, contact='grip', shape='grip', z=-30.0)
    d.hold_prop('keys', 1, 0.7, None)
    d.look_at(0.0, hook, t1=0.8, dur=0.3)
    d.look_at(1.0, (1500, 560), dur=0.3)
    d.talk([(1.0, 2.6, 'Bus 9 has a radio to the depot'), (2.8, 3.6, 'Lock this behind me')], env=None, words=None)
    d.walk(3.4, 4.5, 0.0, -420.0, facing=-1.0, surface='inside')
    def draw(pen, t):
        room(pen, '#3a3028', '#2a201a')
        pen.fill(rect(hook[0] - 30, hook[1] - 10, 60, 12), '#6a4a2a')
        if t < 0.7: CH.draw_prop3(pen, 'keys', hook[0], hook[1] + 10, ppm / 100.0)
        fig(pen, d, t, NIGHTB)
    return dict(draw=draw, actors=[d], grounded=[d])


@clip('della_trapped_pound', 4.0, 'Across the yard, the real Grandma is pounding on the glass of bus 9, trapped in her own cab, our porch broom wedged through her folding doors: "DON\'T OPEN THE DOOR!"')
def _c_della_pound():
    ppm = 330.0
    d = actor('della', 960, FLOOR, ppm, seed=35, expr='shout')
    d.face(0.0)
    glass_y = FLOOR - 1.3 * ppm
    ev = d.knock_pattern(0.2, (3,), side=1, beat=0.3, gap=0.5, target=(1060, glass_y), z=120.0, kind='glass')
    d.reach_to(0.2, -1, (840, glass_y - 40), t1=None, dur=0.4, contact='palm', shape='flat', z=120.0)
    d.talk([(1.8, 3.4, "DON'T OPEN THE DOOR")], env=None, words=None)
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#1a1a20'); pen.fill(rect(0, FLOOR - 0.2 * ppm, 1920, 400), '#2a2620')
        fig(pen, d, t, NIGHTB)
        g = rect(560, 220, 800, 860)
        pen.fill(g, '#9ab8d0', 40); pen.line(g, 10, '#2a2c30'); pen.line(poly([(960, 220), (960, 1080)], False), 8, '#2a2c30')
        pen.line(poly([(500, 820), (1420, 760)], False), 16, '#a87a4a'); pen.line(poly([(500, 820), (1420, 760)], False), 3)
    return dict(draw=draw, actors=[d])


@clip('della_drive_swerve', 4.5, 'Grandma hits the gas: "So are we." His brake lights flash; she swerves')
def _c_della_drive():
    ppm = 380.0
    seat = FLOOR - 0.3 * ppm
    d = actor('della', 900, FLOOR, ppm, seed=36, expr='grim_drive')
    d.face(0.0); d.seated(seat, hands=None)
    wc = (900, FLOOR - 0.78 * ppm)
    ang = lambda t: 38.0 * math.sin(PI * clamp((t - 2.4) / 1.0)) if t > 2.4 else 0.0     # noqa: E731
    def grip(sd):
        def f(t):
            a_ = math.radians(ang(t) + (-60 if sd < 0 else 60))
            return (wc[0] + 150 * math.sin(a_), wc[1] - 150 * math.cos(a_))
        return f
    d.drive(0.0, None, grip(-1), grip(1))
    d.talk([(0.4, 1.2, 'So are we')], env=None, words=None)
    d.expr('shock', 2.3, 3.4, 0.15)
    d.look_at(0.0, (960, 300), dur=0.3, z=300.0)
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#101218')
        if 2.2 < t < 2.6: pen.fill(rect(700, 100, 520, 200), '#ff2a20', 120)
        fig(pen, d, t, NIGHTB)
        CH.draw_steering_wheel(pen, wc[0], wc[1], 150, ang(t))
        for side in (1, -1): CH.draw_arm(pen, d.who, side, d.at(t), x=d.x0, y_feet=d.y0, height=d.height, light=NIGHTB, t=t)
    return dict(draw=draw, actors=[d])


@clip('della_broom_jam', 4.0, 'The doors start folding shut. Grandma jams our porch broom between them. The handle bends')
def _c_della_broom():
    ppm = 300.0
    d = actor('della', 960, FLOOR, ppm, seed=37, expr='set_jaw')
    d.face(0.8)
    d.hold_prop('broom', 1, -1.0, None)
    gap_x = 1260
    d.reach_to(0.3, 1, (gap_x - 90, FLOOR - 1.05 * ppm), t1=None, dur=0.45, contact='grip', shape='grip', z=30.0)
    d.reach_to(0.3, -1, (gap_x - 220, FLOOR - 0.95 * ppm), t1=None, dur=0.45, contact='grip', shape='grip', z=60.0)
    d.set(0.3, None, 0.4, lean=0.15)
    d.expr('shout', 1.0, 1.8, 0.2)
    def draw(pen, t):
        night_yard(pen, 560)
        u = clamp(t / 0.6)
        for sd in (-1, 1):
            pnl = rect(gap_x + sd * (30 + 160 * (1 - u)) - (0 if sd > 0 else 220), FLOOR - 2.2 * ppm, 220, 2.0 * ppm)
            pen.fill(pnl, '#2a2c30'); pen.fill(pnl, '#ffa030', 60); pen.line(pnl, 4)
        fig(pen, d, t, AMBER)
    return dict(draw=draw, actors=[d], grounded=[d])


@clip('della_kneel_theo', 5.0, 'Grandma gasps; now she can see Theo. She kneels: "Six mornings, you said thank you. And I never asked your name."')
def _c_della_kneel():
    ppm = 330.0
    d = actor('della', 820, FLOOR, ppm, seed=38, expr='shock')
    th = actor('theo_color', 1180, FLOOR, ppm, seed=39, expr='lonely')
    d.face(0.6); th.face(-0.6)
    d.kneel_down(0.6, 1.0, 0)
    d.look_at(0.0, (th, 'eyes'), dur=0.3)
    d.expr('tender', 1.4, None, 0.6)
    d.talk([(1.8, 3.0, 'Six mornings you said thank you'), (3.3, 4.6, 'And I never asked your name')], env=None, words=None)
    th.look_at(0.0, (d, 'eyes'), dur=0.4)
    th.expr('tender', 3.6, None, 0.6)
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#0e0e14'); pen.fill(rect(0, FLOOR, 1920, 140), '#26262a')
        pen.glow(300, 300, 500, '#3a6aff', 50 + 30 * math.sin(t * 6))
        fig(pen, th, t, NIGHTB); fig(pen, d, t, NIGHTB)
    return dict(draw=draw, actors=[d, th], grounded=[th])


@clip('della_hug_mina', 4.0, 'In the morning I delete the post and tell Grandma I\'m sorry. She hugs me: "Brakes, mirrors, names."')
def _c_della_hug():
    ppm = 330.0
    d = actor('della', 1020, FLOOR, ppm, seed=40, expr='tender')
    m = actor('mina', 760, FLOOR, ppm, seed=41, expr='guilt')
    d.face(-0.7); m.face(0.7)
    m.talk([(0.2, 1.0, "I'm sorry")], env=None, words=None, intensity=0.6)
    m.walk(1.0, 1.7, 0.0, 90.0, facing=0.7)
    d.reach_to(1.4, 1, lambda t: (m.where(t, 'shoulder_r', post=False)[0] - 10, m.where(t, 'shoulder_r', post=False)[1] + 20), dur=0.6, contact='palm', shape='open', z=-20.0)
    d.reach_to(1.5, -1, lambda t: (m.where(t, 'shoulder_l', post=False)[0] - 20, m.where(t, 'shoulder_l', post=False)[1] + 60), dur=0.6, contact='palm', shape='open', z=40.0)
    m.reach_to(1.6, -1, lambda t: (d.where(t, 'chest', post=False)[0] + 10, d.where(t, 'chest', post=False)[1] + 30), dur=0.5, contact='palm', shape='open', z=40.0)
    m.expr('relief', 1.8, None, 0.5)
    d.talk([(2.4, 3.6, 'Brakes mirrors names')], env=None, words=None, intensity=0.6)
    d.look_at(0.0, (m, 'eyes'), dur=0.3); m.look_at(0.0, (d, 'eyes'), t1=1.3, dur=0.3)
    def draw(pen, t):
        room(pen, '#d8c8a8', '#a8885a')
        fig(pen, d, t, MORNING); fig(pen, m, t, MORNING)
    return dict(draw=draw, actors=[d, m], grounded=[d, m])


@clip('mina_post_phone', 4.0, 'Today, I posted his first-day chalkboard (Sami, first grade, Larkfield Elementary, bus 9, Larch Street); forty-one likes; one comment')
def _c_mina_post():
    ppm = 360.0
    m = actor('mina', 900, FLOOR, ppm, seed=42, expr='kind_smile')
    m.face(0.3)
    m.hold_prop('cell', 1, -1.0, None)
    m.reach(-1.0, None, 1, out=-30.0, down=120.0, fwd=230.0, shape='grip', up=0.0, fade=0.01)
    m.tap(0.6, -1, lambda t: m.grip_point(t, 1, 'cell', post=False), n=3, gap=0.3)
    m.look_at(0.0, lambda t: m.grip_point(t, 1, 'cell'), dur=0.3)
    m.expr('suspicious', 2.6, None, 0.5)
    def draw(pen, t):
        room(pen, '#d8c8a8', '#a8885a')
        fig(pen, m, t, MORNING)
    return dict(draw=draw, actors=[m], grounded=[m])


@clip('mina_hush_sami', 3.5, 'Sami jolts awake, takes a breath: "He..." My hand slaps over his mouth. Silence')
def _c_mina_hush():
    ppm = 330.0
    seat = FLOOR - 0.42 * ppm
    s_ = actor('sami', 1000, FLOOR, ppm, seed=43, expr='sleepy')
    m = actor('mina', 760, FLOOR, ppm, seed=44, expr='hush_fear')
    s_.face(-0.5); s_.seated(seat, hands='lap')
    m.face(0.6); m.seated(seat, hands=None)
    s_.set(0.6, None, 0.15, h_dy=-6.0)
    s_.expr('shout_here', 0.8, None, 0.2)
    s_.talk([(0.9, 1.2, 'He')], env=None, words=None)
    m.hand_over(1.15, 1, s_, 'mouth', dur=0.15)
    s_.expr('shock', 1.3, None, 0.15)
    m.look_at(0.0, (1500, 400), t1=0.9, dur=0.3); m.look_at(1.0, (s_, 'eyes'), dur=0.15)
    s_.look_at(1.4, (m, 'eyes'), dur=0.3)
    def draw(pen, t):
        room(pen, '#2a2a34', '#2a201a')
        couch(pen, 880, seat, 640)
        fig(pen, s_, t, NIGHTB); fig(pen, m, t, NIGHTB)
    return dict(draw=draw, actors=[m, s_])


@clip('mina_911_nobars', 4.0, 'I dial 911. No bars. Not since his headlights came')
def _c_mina_911():
    ppm = 360.0
    m = actor('mina', 900, FLOOR, ppm, seed=45, expr='resolve')
    m.face(0.35)
    m.hold_prop('cell', -1, -1.0, None)
    m.reach(-1.0, None, -1, out=-40.0, down=100.0, fwd=230.0, shape='grip', up=0.0, fade=0.01)
    ev = m.dial(0.3, 1, lambda t: m.grip_point(t, -1, 'cell', post=False), n=3, gap=0.3)
    m.look_at(0.0, lambda t: m.grip_point(t, -1, 'cell'), dur=0.3)
    m.phone_to_ear(1.8, None, side=-1)
    m.expr('fear', 2.6, None, 0.3)
    m.look_at(2.2, (1500, 450), dur=0.4)
    def draw(pen, t):
        room(pen, '#2a2a34', '#2a201a')
        fig(pen, m, t, NIGHTB)
    return dict(draw=draw, actors=[m], grounded=[m])


@clip('mina_whats_the_word', 4.0, '"Mina, open up! It\'s Grandma!" Her voice, exactly. "What\'s the word, Grandma?" (my palm flat on the door, not opening it)')
def _c_mina_word():
    ppm = 360.0
    m = actor('mina', 920, FLOOR, ppm, seed=46, expr='fear')
    dp = door_pts(720, ppm)
    m.face(-1.6)
    m.reach_to(0.3, 1, (dp['knob'][0] + 40, dp['peep'][1] + 90), dur=0.6, contact='palm', shape='flat', z=-80.0)
    m.head_to(0.5, (dp['peep'][0] + 40, dp['peep'][1] + 60), 'mouth', dur=0.8, max_lean=0.15)
    m.expr('resolve', 1.0, None, 0.3)
    m.talk([(1.3, 2.4, "What's the word Grandma")], env=None, words=None)
    def draw(pen, t):
        room(pen, '#2a2a34', '#2a201a')
        door(pen, 720, FLOOR, ppm=ppm)
        fig(pen, m, t, NIGHTB)
    return dict(draw=draw, actors=[m], grounded=[m])


@clip('mina_deadbolt_floor', 4.0, 'Grandma\'s room has the only deadbolt. I sit with my back against it: "The word\'s dead, Sami. Nobody opens."')
def _c_mina_floor():
    ppm = 330.0
    m = actor('mina', 860, FLOOR, ppm, seed=47, expr='resolve')
    m.face(0.6)
    m.sit_floor(-1.0)
    m.talk([(0.8, 2.6, "The word's dead Sami Nobody opens")], env=None, words=None)
    m.look_at(0.0, (1400, 700), dur=0.3)
    def draw(pen, t):
        room(pen, '#2a2a34', '#2a201a')
        door(pen, 640, FLOOR, ppm=ppm)
        fig(pen, m, t, NIGHTB)
    return dict(draw=draw, actors=[m])


@clip('mina_step_scream', 5.0, 'Not even for Sami: my foot lifts onto the first step... I pull it back, and SCREAM his name: "SAMI!"')
def _c_mina_step():
    ppm = 280.0
    m = actor('mina_bare', 950, FLOOR, ppm, seed=48, expr='fear')
    m.face(0.9)
    ev = m.step_up(0.5, 1, up=0.8, hold=0.6, back=0.7, h=95.0, f=150.0)
    m.look_at(0.0, (1400, 300), dur=0.3)
    m.expr('resolve', 2.6, None, 0.3)
    m.expr('terrified_call', 3.0, None, 0.15)
    m.talk([(3.1, 4.3, 'SAMI')], env=None, words=None)
    def draw(pen, t):
        night_yard(pen, 600)
        b = bus_side(pen, 1000, FLOOR, ppm, 1080)
        fig(pen, m, t, AMBER)
    return dict(draw=draw, actors=[m], grounded=[m])


@clip('mina_asks_name', 3.5, 'From the bottom step, I call up the aisle: "What\'s your name?"')
def _c_mina_ask():
    ppm = 340.0
    m = actor('mina_bare', 900, FLOOR, ppm, seed=49, expr='brave')
    m.face(0.7)
    m.look_at(0.0, (1500, 260), dur=0.3)
    m.set(0.6, None, 0.5, lean=0.12)
    m.expr('kind_ask', 0.8, None, 0.4)
    m.talk([(1.0, 2.2, "What's your name")], env=None, words=None)
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#140c06'); pen.glow(1500, 300, 700, '#ffa030', 90)
        fig(pen, m, t, AMBER)
    return dict(draw=draw, actors=[m], grounded=[m])


@clip('mina_sits_new_girl', 6.0, 'In seat twenty-one, a new girl sits alone; no name on her backpack. I walk past my usual seat and sit down next to her: "Hi. I\'m Mina. What\'s your name?"')
def _c_mina_girl():
    ppm = 300.0
    seat = FLOOR - 0.42 * ppm
    g = actor('new_girl', 1400, FLOOR, ppm, seed=50, expr='lonely')
    g.face(-0.45); g.seated(seat, hands=None)
    g.hug_prop(-1.0, 'backpack', dur=0.01, part='lap')
    g.look_at(0.0, (g, 'lap'), t1=4.4, dur=0.3)
    m = actor('mina', 420, FLOOR, ppm, seed=51, expr='kind_smile')
    m.face(1.0)
    m.walk(0.2, 2.1, 0.0, 760.0, facing=1.0, surface='inside')
    m.sit_on(2.3, seat, dur=0.9)
    m.turn(2.4, 0.5, 0.7)
    m.look_at(3.0, (g, 'eyes'), dur=0.3)
    m.expr('kind_ask', 3.2, None, 0.4)
    m.talk([(3.4, 3.8, 'Hi'), (3.9, 4.6, "I'm Mina"), (4.8, 5.7, "What's your name")], env=None, words=None)
    g.look_at(4.6, (m, 'eyes'), dur=0.5)
    g.expr('kind_smile', 5.3, None, 0.6)
    def draw(pen, t):
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 1080, [(0, '#e8e0cc'), (1, '#c8b896')])
        for sx in (320, 1100):
            pen.fill(rrect(sx - 20, seat - 330, 40, 360, 12), '#7a3a2a'); pen.fill(rect(sx, seat - 10, 420, 26), '#8a4a34')
        fig(pen, g, t, MORNING); fig(pen, m, t, MORNING)
    return dict(draw=draw, actors=[m, g], grounded=[m])


@clip('sami_here', 3.0, 'Say his name, and he shouts "HERE!" (his hand up, proud)')
def _c_sami_here():
    ppm = 380.0
    s_ = actor('sami', 960, FLOOR, ppm, seed=52, expr='proud_grin')
    s_.face(0.25)
    s_.reach_to(0.6, 1, lambda t: (s_.where(t, 'head', post=False)[0] + 0.12 * s_.height, s_.where(t, 'head', post=False)[1] - 0.1 * s_.height),
                t1=2.4, dur=0.3, contact='palm', shape='open', z=20.0)
    s_.expr('shout_here', 0.6, 1.6, 0.15)
    s_.talk([(0.65, 1.3, 'HERE')], env=None, words=None)
    s_.set(0.6, 1.4, 0.2, bob=-12.0)
    def draw(pen, t):
        room(pen, '#d8c8a8', '#a8885a')
        fig(pen, s_, t, MORNING)
    return dict(draw=draw, actors=[s_], grounded=[s_])


@clip('sami_lighthouse', 4.0, 'Upstairs, Sami\'s hugging Rex, proud of himself: "You told me on the walkie to say our word... So I did! LIGHTHOUSE!"')
def _c_sami_rex():
    ppm = 380.0
    s_ = actor('sami', 960, FLOOR, ppm, seed=53, expr='proud_grin')
    s_.face(0.3)
    s_.hug_prop(-1.0, 'rex', dur=0.01)
    s_.talk([(0.4, 1.8, 'So I did'), (2.2, 3.2, 'LIGHTHOUSE')], env=None, words=None)
    s_.expr('shout_here', 2.2, 3.0, 0.15)
    s_.set(2.2, 3.0, 0.2, bob=-10.0)
    def draw(pen, t):
        room(pen, '#4a4a6a', '#3a2a20')
        fig(pen, s_, t, WARM2)
    return dict(draw=draw, actors=[s_], grounded=[s_])


@clip('sami_walkie', 3.5, 'From upstairs, Sami, laughing, talking to someone on his walkie')
def _c_sami_walkie():
    ppm = 380.0
    s_ = actor('sami', 960, FLOOR, ppm, seed=54, expr='proud_grin')
    s_.face(-0.3)
    s_.hold_prop('walkie', -1, -1.0, None)
    s_.radio_to_mouth(0.3, 3.4, side=-1)
    s_.talk([(0.6, 1.6, 'hee hee okay'), (2.0, 3.0, 'I know it')], env=None, words=None)
    def draw(pen, t):
        room(pen, '#4a4a6a', '#3a2a20')
        fig(pen, s_, t, WARM2)
    return dict(draw=draw, actors=[s_], grounded=[s_])


@clip('sami_palm_window', 3.5, 'Sami\'s palm presses against the window of seat four. Every other seat is dark')
def _c_sami_glass():
    s_ = actor('sami', 0, 0, 380.0, seed=55, expr='terrified_call')
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#7a6a30')
        win = rrect(560, 160, 800, 700, 30)
        pen.cv.save(); pen.cv.clipPath(win, skia.ClipOp.kIntersect, True)
        pen.fill(win, '#2a1a0a'); pen.glow(960, 400, 500, '#ffa030', 90)
        P = s_.at(t); P.h_turn = 0.0
        CH.draw_bust(pen, 'sami', 960, 520, 0.85, P, light=AMBER, t=t)
        pen.fill(win, '#c8d8e8', 30)
        pen.cv.restore()
        pen.line(win, 10, '#1a1a1a')
        CH.draw_palm_on_glass(pen, 'sami', 1250, 640, 300, press=clamp((t - 0.5) / 0.3), t=t)
    return dict(draw=draw, actors=[s_])


@clip('theo_hi_mina', 4.0, 'Seat twenty-two: a boy in a yellow raincoat, even in June. Every day he says, "Hi, Mina."')
def _c_theo_hi():
    ppm = 330.0
    seat = FLOOR - 0.42 * ppm
    th = actor('theo', 960, FLOOR, ppm, seed=56, expr='lonely')
    th.face(0.35); th.seated(seat, hands='lap')
    th.look_at(0.0, (th, 'lap'), t1=1.0, dur=0.3)
    th.look_at(1.1, (1500, 520), dur=0.4)
    th.expr('kind_smile', 1.3, None, 0.5)
    th.talk([(1.6, 2.4, 'Hi Mina')], env=None, words=None, intensity=0.6)
    th.wave(1.6, 3.0, side=1, slow=True, height=0.6)
    def draw(pen, t):
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 1080, [(0, '#e8e0cc'), (1, '#c8b896')])
        pen.fill(rrect(760, seat - 330, 40, 360, 12), '#7a3a2a'); pen.fill(rect(780, seat - 10, 420, 26), '#8a4a34')
        fig(pen, th, t, MORNING)
    return dict(draw=draw, actors=[th])


@clip('theo_twist_free', 4.5, 'The glove squeezes his shoulder. He looks at it. Then at me: "Theo." ... "HERE!" He twists out from under the glove, and through the gap')
def _c_theo_free():
    ppm = 300.0
    th = actor('theo', 1100, FLOOR, ppm, seed=57, expr='hush_fear')
    th.face(-0.4)
    a = ws(1450, FLOOR, ppm, 58)
    a.face(-0.6)
    a.set(-1.0, None, 0.01, ws_bend=0.25)
    a.reach_far(-1.0, 1, lambda t: th.where(t, 'shoulder_r', post=False), t1=2.3, dur=0.01, z=-10.0, shape='hang')
    th.look_at(0.0, (th, 'shoulder_r'), t1=0.8, dur=0.4)
    th.look_at(0.9, (500, 500), dur=0.3)
    th.expr('brave', 1.0, None, 0.4)
    th.talk([(1.1, 1.6, 'Theo'), (2.0, 2.5, 'HERE')], env=None, words=None)
    th.expr('shout_here', 2.0, 2.8, 0.15)
    th.run(2.3, 4.2, 0.0, -700.0, surface='porch')
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#140c06'); pen.glow(960, 400, 800, '#ffa030', 60)
        pen.fill(rect(0, FLOOR, 1920, 140), '#2a1e14')
        fig(pen, th, t, AMBER); fig(pen, a, t, AMBER)
    return dict(draw=draw, actors=[th, a], grounded=[th])


if __name__ == '__main__':
    main()
