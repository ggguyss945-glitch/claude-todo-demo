"""cast_clips.py: acting clips of the doctor film's cast ("If Your Doctor Calls At 3 AM... DON'T ASK WHAT THEY FOUND",
characters_doctor.py run by characters.py), one per scripted action, written to W/cast/clips/
(W = Doctor Video/film/_work).

    cd "Vox test/Doctor Video/film" && python3 tools/cast_clips.py [names...] [--fps 60] [--strip-only] [--review]

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
        r = render(nm, '--strip-only' in sys.argv)
        allr[nm] = r
        print('%-28s %4.1fs  %.3f s/frame  misses %d (worst %.1f)  feet %s' % (nm, r['dur'], r['sec_per_frame'], r['reach_misses'],
                                                                           r['worst_miss'], r['feet_off_floor_px']))
    json.dump(allr, open(rpath, 'w'), indent=1)
    if '--review' in sys.argv:
        for p in review(names): print('review', p)


# ================================================================================================ doctor film stand-ins
KITCHEN = ('#3a4038', '#4a3e34')        # night kitchen wall / floor
WAIT = ('#7d8a6a', '#5a5a4a')           # the waiting room: sickly fluorescent green-yellow
WARM2 = dict(rim='#ffd9a0', rim_a=55, side=-1, key=0.1)
NIGHT2 = dict(rim='#8fa6e8', rim_a=55, side=1, key=-0.3)
FLUO = dict(rim='#d8f0a0', rim_a=70, side=1, key=-0.1)
ER = dict(rim='#ffffff', rim_a=40, side=-1, key=0.2)


def wall_phone(pen, x, y, ppc, has_receiver=True):
    """A cream wall phone: the base on the wall at (x, y) (its top), the cradle hook; returns the cradle (receiver grip)
    point and the cord socket at the bottom of the base."""
    w, h = 9.0 * ppc, 20.0 * ppc
    b = rrect(x - w / 2, y, w, h, 1.5 * ppc)
    pen.fill(b, '#e3d9bf'); pen.line(b, 3)
    for r in range(4):
        for k in range(3):
            pen.fill(oval(x - 2.2 * ppc + k * 2.2 * ppc, y + 7 * ppc + r * 2.6 * ppc, 0.8 * ppc), '#cfc4a6')
    cradle = (x, y + 9.0 * ppc)
    if has_receiver:
        CH.draw_prop3(pen, 'receiver', cradle[0], cradle[1], ppc)
    return cradle, (x, y + h)


def phone_jack(pen, x, y, ppc, plugged=True):
    pen.fill(rrect(x - 3 * ppc, y - 3.5 * ppc, 6 * ppc, 7 * ppc, ppc * 0.6), '#e8e2d2'); pen.line(rrect(x - 3 * ppc, y - 3.5 * ppc, 6 * ppc, 7 * ppc, ppc * 0.6), 2.5)
    return (x, y)


def cabinet(pen, x, y, ppc, swing=0.0, card=True):
    """The bathroom medicine cabinet (top-left at (x, y)): the mirror door swings aside (swing 0..1), the little yellow card
    taped inside. Returns the card's centre."""
    w, h = 40.0 * ppc, 55.0 * ppc
    pen.fill(rect(x, y, w, h), '#d9d6ce'); pen.line(rect(x, y, w, h), 3)
    pen.fill(rect(x + 2 * ppc, y + 2 * ppc, w - 4 * ppc, h - 4 * ppc), '#a8a49a')
    for k in range(2): pen.line(poly([(x + 2 * ppc, y + (18 + 17 * k) * ppc), (x + w - 2 * ppc, y + (18 + 17 * k) * ppc)], False), 3, '#7a766e')
    cx, cy = x + w * 0.55, y + 10 * ppc
    if card: CH.draw_prop3(pen, 'card', cx, cy, ppc)
    dw = w * (1.0 - 0.92 * swing)
    m = rect(x - (w - dw) * 0.0 + (w - dw) * 0.0, y, dw, h)
    pen.fill(m, '#9fb4c0'); pen.linear(m, x, y, x + dw, y + h, [(0, '#c8d8e0', 255), (0.5, '#8fa4b0', 255), (1, '#6f8490', 255)])
    pen.line(m, 3)
    return (cx, cy)


def counter(pen, x, top, w=520, y=FLOOR, sink=True, c='#6a5a4a'):
    pen.fill(rect(x - w / 2, top, w, y - top), c); pen.line(rect(x - w / 2, top, w, y - top), 3)
    pen.fill(rect(x - w / 2 - 10, top - 14, w + 20, 18), '#cfc8b8'); pen.line(rect(x - w / 2 - 10, top - 14, w + 20, 18), 3)
    for k in range(3): pen.line(rect(x - w / 2 + 14 + k * (w - 28) / 3, top + 20, (w - 28) / 3 - 10, y - top - 40), 2.5, mix(c, '#000000', 0.3))
    if sink:
        pen.fill(rrect(x - 90, top - 12, 180, 14, 4), '#9aa2aa'); pen.line(rrect(x - 90, top - 12, 180, 14, 4), 2.5)
        return (x, top - 6)
    return (x, top - 14)


def plastic_chair(pen, x, y=FLOOR, ppm=380.0, facing=1.0, c='#3f6a8a', rock=0.0, front=False):
    """A molded plastic waiting-room chair (side view, facing +1 = screen right, or front=True), rocking by `rock` deg
    about its front feet. Returns the seat top y."""
    k = ppm / 100.0
    sy = y - 45 * k
    cv = pen.cv
    cv.save()
    if rock:
        fx = x + facing * 20 * k
        cv.translate(fx, y); cv.rotate(rock * facing); cv.translate(-fx, -y)
    if front:
        pen.line(poly([(x - 20 * k, y), (x - 18 * k, sy)], False), 4, '#2a2c32'); pen.line(poly([(x + 20 * k, y), (x + 18 * k, sy)], False), 4, '#2a2c32')
        pen.fill(rrect(x - 23 * k, sy - 4 * k, 46 * k, 7 * k, 2 * k), c); pen.line(rrect(x - 23 * k, sy - 4 * k, 46 * k, 7 * k, 2 * k), 3)
        pen.fill(rrect(x - 21 * k, sy - 44 * k, 42 * k, 30 * k, 6 * k), mix(c, '#000000', 0.15)); pen.line(rrect(x - 21 * k, sy - 44 * k, 42 * k, 30 * k, 6 * k), 3)
    else:
        f = facing
        for dx in (-18, 18): pen.line(poly([(x + f * dx * k, y), (x + f * dx * 0.9 * k, sy)], False), 4, '#2a2c32')
        seat = smooth([(x - f * 22 * k, sy - 2 * k), (x + f * 22 * k, sy - 3 * k), (x + f * 23 * k, sy + 3 * k), (x - f * 22 * k, sy + 3 * k)], True, 0.4)
        pen.fill(seat, c); pen.line(seat, 3)
        back = smooth([(x - f * 20 * k, sy - 2 * k), (x - f * 26 * k, sy - 40 * k), (x - f * 21 * k, sy - 42 * k), (x - f * 15 * k, sy - 4 * k)], True, 0.5)
        pen.fill(back, mix(c, '#000000', 0.15)); pen.line(back, 3)
    cv.restore()
    return sy


def ticket_machine(pen, x, y=FLOOR, ppm=380.0):
    """The red take-a-number machine on its pole (deli counter); returns the slot where the ticket comes out."""
    k = ppm / 100.0
    pen.line(poly([(x, y), (x, y - 110 * k)], False), 3 * k, '#6a6e76')
    pen.fill(oval(x, y, 14 * k, 3 * k), '#4a4e56')
    body = smooth([(x - 9 * k, y - 140 * k), (x + 9 * k, y - 140 * k), (x + 11 * k, y - 112 * k), (x - 11 * k, y - 112 * k)], True, 0.5)
    pen.fill(body, '#c0392f'); pen.line(body, 3)
    pen.fill(rect(x - 7 * k, y - 120 * k, 14 * k, 2 * k), '#2a1a18')
    return (x, y - 119 * k)


def armchair2(pen, x, seat_y, w=330, back_h=320, y=FLOOR, c='#6a4a32', front=True):
    armchair(pen, x, seat_y, w, back_h, y, c)


def streetlight(pen, x, y, h=520, flicker=1.0):
    pen.line(poly([(x, y), (x, y - h), (x + 60, y - h - 10)], False), 8, '#2a2c32')
    pen.fill(rrect(x + 40, y - h - 18, 50, 16, 5), '#3a3c44')
    if flicker > 0.05:
        pen.glow(x + 65, y - h, 220, '#cfe0ff', 120 * flicker)
        pen.linear(poly([(x + 45, y - h), (x + 85, y - h), (x + 200, y), (x - 70, y)]), x + 65, y - h, x + 65, y,
                   [(0, '#cfe0ff', 70 * flicker), (1, '#cfe0ff', 0)])
    return (x + 65, y - h)


def bench(pen, x, seat_y, w=300, y=FLOOR):
    pen.fill(rect(x - w / 2, seat_y - 6, w, 12), '#3a3226')
    for dx in (-w / 2 + 20, w / 2 - 20): pen.line(poly([(x + dx, seat_y), (x + dx, y)], False), 6, '#22201c')
    pen.fill(rect(x - w / 2, seat_y - 80, w, 10), '#3a3226')


def car_back(pen, x, floor, ppm, roof_y, seat_y, inside='#1a1c22'):
    """A car's back seat seen from the front (the rear-view mirror's view): the seat back, the cushion, the low roof."""
    k = ppm / 100.0
    pen.fill(rect(0, 0, 1920, 1080), inside)
    pen.fill(rect(0, 0, 1920, roof_y), '#2a2c34'); pen.line(poly([(0, roof_y), (1920, roof_y)], False), 4)
    pen.fill(rrect(x - 140 * k, seat_y - 75 * k, 280 * k, 80 * k, 10 * k), '#3a3a40'); pen.line(rrect(x - 140 * k, seat_y - 75 * k, 280 * k, 80 * k, 10 * k), 3)
    pen.fill(rrect(x - 140 * k, seat_y - 4, 280 * k, floor - seat_y, 8 * k), '#45454c'); pen.line(rrect(x - 140 * k, seat_y - 4, 280 * k, floor - seat_y, 8 * k), 3)
    pen.fill(rect(0, floor, 1920, 1080 - floor), '#121318')


def car_front_seat(pen, x, floor, ppm, seat_y):
    k = ppm / 100.0
    pen.fill(rrect(x - 30 * k, seat_y - 70 * k, 22 * k, 75 * k, 8 * k), '#3a3a40'); pen.line(rrect(x - 30 * k, seat_y - 70 * k, 22 * k, 75 * k, 8 * k), 3)
    pen.fill(rrect(x - 30 * k, seat_y - 4, 55 * k, 14 * k, 5 * k), '#45454c'); pen.line(rrect(x - 30 * k, seat_y - 4, 55 * k, 14 * k, 5 * k), 3)


def er_bed(pen, x, top, w=560, y=FLOOR):
    pen.fill(rect(x - w / 2, top, w, 30), '#e8eef0'); pen.line(rect(x - w / 2, top, w, 30), 3)
    pen.fill(rect(x - w / 2, top + 30, w, 24), '#9aa4ac'); pen.line(rect(x - w / 2, top + 30, w, 24), 3)
    for dx in (-w / 2 + 30, w / 2 - 30): pen.line(poly([(x + dx, top + 54), (x + dx, y - 20)], False), 6, '#8a929a'); pen.fill(oval(x + dx, y - 12, 12), '#2a2c32')
    pen.fill(rrect(x - w / 2 - 10, top - 90, 20, 140, 6), '#b9c2ca'); pen.line(rrect(x - w / 2 - 10, top - 90, 20, 140, 6), 3)


def monitor(pen, x, y, t=0.0):
    pen.fill(rrect(x - 90, y - 70, 180, 130, 10), '#2a2e36'); pen.line(rrect(x - 90, y - 70, 180, 130, 10), 3)
    pen.fill(rect(x - 75, y - 58, 150, 100), '#0d1a14')
    pts = []
    for i in range(60):
        u = i / 59.0; ph = (u * 3 + t * 1.5) % 1.0
        v = -30 if 0.48 < ph < 0.52 else (12 if 0.52 <= ph < 0.56 else 0)
        pts.append((x - 72 + 144 * u, y - 10 + v))
    pen.line(poly(pts, False), 3, '#4ae07a')


def desk(pen, x, top, w=520, y=FLOOR):
    pen.fill(rect(x - w / 2, top, w, 22), '#8a8478'); pen.line(rect(x - w / 2, top, w, 22), 3)
    for dx in (-w / 2 + 20, w / 2 - 30): pen.fill(rect(x + dx, top + 22, 12, y - top - 22), '#5a564e')
    for k in range(6): pen.fill(rect(x + 60 + k * 2, top - 6 - k * 5, 150, 5), '#f6f4ee'); pen.line(rect(x + 60 + k * 2, top - 6 - k * 5, 150, 5), 1.5)


def fluo_room(pen, t=0.0):
    room(pen, WAIT[0], WAIT[1])
    for k in range(4):
        on = 1.0 if k % 2 == 0 else (0.3 + 0.7 * (math.sin(t * 37.0 + k) > 0.6))
        pen.fill(rect(160 + k * 450, 40, 260, 18), '#f4ffd8' if on > 0.5 else '#6a7058'); pen.glow(290 + k * 450, 50, 260, '#e8ffb0', 50 * on)


def door_open_room(pen, x, y=FLOOR, ppm=380.0):
    pass


# ================================================================================================ the clips
def lat(x, y, ppm, seed=1, **kw):
    a = CH.Acting('later', seed=seed, height=CH.height_px('later', ppm), **kw)
    a.place(x, y)
    return a


@clip('later_wait_plastic', 5.0, 'Cold open: a very tall man folded into a little plastic chair, knees up past his shoulders, the clipboard with no paper, clicking his pen; he looks up at you and tilts his head: "Take a seat. It can wait."')
def _c_later_wait():
    ppm = 300.0
    a = lat(900, FLOOR, ppm, seed=1)
    a.perch(None, 'plastic')
    a.face(0.35, -0.2)
    a.set(-1, None, 0.01, h_nod=0.45, h_tilt=4.0)
    ev = a.click_pen([0.5, 0.9, 1.6, 2.0])
    a.look_at(2.3, (1400, 560), dur=1.2, z=300.0)             # looks up at "you" (the lens side)
    a.tilt_head(3.2, 20.0, 1.4)
    def draw(pen, t):
        fluo_room(pen, t)
        for i, xx in enumerate((520, 1280, 1500)): plastic_chair(pen, xx, FLOOR, ppm, front=True)
        plastic_chair(pen, 900, FLOOR, ppm, facing=1.0)
        fig(pen, a, t, FLUO)
    return dict(draw=draw, actors=[a], grounded=[a])


@clip('later_likeness_profile', 4.0, 'Reference pose (the owner\'s photo): folded on a small chair in profile, the long neck reaching forward, the face turned to us, the cone tipped, hands flat on the carpet')
def _c_later_profile():
    ppm = 300.0
    a = lat(700, FLOOR, ppm, seed=2)
    a.perch(None, 'plastic', knee=0.0, hands=('floor', 'floor'), props=False)
    a.face(1.0, -1.0)
    a.set(-1, None, 0.01, h_tilt=24.0)
    a.tilt_head(1.5, 6.0, 1.5)
    def draw(pen, t):
        room(pen, '#c6b4ac', '#3a3434')
        plastic_chair(pen, 700, FLOOR, ppm, facing=1.0, c='#2a2626')
        fig(pen, a, t)
    return dict(draw=draw, actors=[a], grounded=[a])


@clip('ruth79_phone_hold', 5.0, '1979, 3 AM: Grandma calls that place, a recording puts her on hold; she waits with the receiver at her ear, the cord coiling to the wall phone; then she listens: "It can wait until morning."')
def _c_ruth79_phone():
    ppm = 380.0; ppc = ppm / 100.0
    r = actor('ruth79', 860, FLOOR, ppm, seed=3, expr='stern_afraid')
    r.face(0.6)
    rec = CH.PropTrack('receiver', 1060, FLOOR - 1.45 * ppm + 9 * ppc, ppc)
    tc = r.pick_up(rec, 0.2, side=1, dur=1.0, carry=None)
    r.receiver_to_ear(tc + 0.2, None, side=1)
    r.look_at(0.0, rec, t1=tc, dur=0.3)
    r.look_at(tc + 0.6, (1300, 600), dur=0.6)                # eyes off into the dark while she waits
    r.expr('fear', 3.6, None, 0.6)                           # the calm voice: "It can wait until morning."
    def draw(pen, t):
        room(pen, '#2c2a36', '#3a3028')
        cr, sock = wall_phone(pen, 1060, FLOOR - 1.45 * ppm, ppc, has_receiver=False)
        rec.draw(pen, t)
        fig(pen, r, t, NIGHT2)
        if rec.holder(t):
            e = CH.receiver_cord_end(r, t, 1)
            CH.draw_coil_cord(pen, e[0], e[1], sock[0], sock[1], ppc, 0.35, t)
        else:
            CH.draw_coil_cord(pen, cr[0], cr[1] + 11 * ppc, sock[0], sock[1], ppc, 0.2, t)
    return dict(draw=draw, actors=[r], grounded=[r])


@clip('grandpa79_sits_armchair', 5.0, '1979: Grandpa, a hand on his chest, sits down in his armchair, the brown one by the window, to wait for the sun')
def _c_grandpa_sits():
    ppm = 380.0
    seat = FLOOR - 0.43 * ppm
    g = actor('grandpa79', 600, FLOOR, ppm, seed=4, expr='stern_afraid')
    g.face(1.0)
    g.walk(0.0, 1.4, -200.0, 160.0, surface='inside')
    g.hand_on(0.0, 'chest', t1=4.6, side=-1)
    g.turn(1.4, -0.5, 0.6)
    g.sit_on(1.9, seat, dur=1.2, hands=None)
    g.look_at(3.4, (1300, 380), dur=0.8)                     # out of the window, toward where the sun will come up
    def draw(pen, t):
        room(pen, '#2a2c3a', '#3a2e26')
        window(pen, 1250, 260, 360, 400, night=True)
        armchair(pen, 780, seat, 340, c='#6a4a30')
        fig(pen, g, t, NIGHT2)
    return dict(draw=draw, actors=[g], grounded=[g])


@clip('ruth79_coffee_sunrise', 6.0, 'At sunrise Grandma brings him a cup of coffee; he is still sitting there, still waiting (gently: eyes closed, as if asleep)')
def _c_ruth79_coffee():
    ppm = 380.0; ppc = ppm / 100.0
    seat = FLOOR - 0.43 * ppm
    g = actor('grandpa79', 1150, FLOOR, ppm, seed=5)
    g.face(-0.5); g.seated(seat, hands='arms'); g.gone(-5.0, 0.1)
    r = actor('ruth79', 420, FLOOR, ppm, seed=6, expr='warm')
    r.face(1.0)
    r.hold_prop('mug', -1, -1.0, None)
    r.reach(-1.0, None, -1, out=-30.0, down=130.0, fwd=170.0, shape='grip', up=0.0, fade=0.01)
    r.walk(0.4, 2.7, 0.0, 530.0, surface='inside')
    r.look_at(0.4, (g, 'head'), dur=0.5)
    r.expr('stern_afraid', 3.6, None, 0.8)                  # she stops: he has not moved
    r.reach_to(3.8, 1, (g, 'shoulder_l'), dur=0.9, z=60.0, contact='palm', shape='open')      # the free hand, the mug still in the other
    def draw(pen, t):
        room(pen, '#5a4a40', '#3a2e26')
        window(pen, 1500, 240, 360, 420, night=False)
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 1920, 0, [(0, '#ffb070', 0), (1, '#ffb070', 60)])
        armchair(pen, 1170, seat, 340, c='#6a4a30')
        fig(pen, g, t, WARM2); fig(pen, r, t, WARM2)
    return dict(draw=draw, actors=[g, r], grounded=[r])


@clip('milo_drink', 4.0, 'Milo is thirsty all the time: he drinks a whole bottle of water and asks for another')
def _c_milo_drink():
    ppm = 380.0
    m = actor('milo', 900, FLOOR, ppm, seed=7, expr='thirsty')
    m.face(0.45)
    ev = m.drink(0.4, 2.8, side=1)
    m.look_at(3.0, (1500, 400), dur=0.4)
    m.talk([(3.1, 3.8, 'Can I have another')], env=None, words=None)
    def draw(pen, t):
        room(pen, '#5a6a7a', '#6a5a4a')
        fig(pen, m, t, WARM)
    return dict(draw=draw, actors=[m], grounded=[m])


@clip('milo_jeans_sag', 4.0, 'His favorite dinosaur jeans started falling off him: they slip, he grabs the waistband and hitches them up')
def _c_milo_sag():
    ppm = 380.0
    m = actor('milo_jeans', 900, FLOOR, ppm, seed=8, expr='sleepy')
    m.face(0.3)
    m.sag(0.3, None, 1.0, 1.0)
    m.look_at(1.0, (m, 'hip'), t1=2.6, dur=0.3)
    m.hold_up(1.4, None, side=1)
    m.set(2.0, None, 0.4, sag=0.35)
    def draw(pen, t):
        room(pen, '#6a7a8a', '#6a5a4a')
        fig(pen, m, t, WARM)
    return dict(draw=draw, actors=[m], grounded=[m])


@clip('halverson_clinic_blood', 5.0, 'Doctor Halverson takes one look at Milo and her smile goes careful; she takes some blood (a capped tube), Milo brave on the exam table')
def _c_hal_clinic():
    ppm = 380.0
    top = FLOOR - 0.78 * ppm
    m = actor('milo', 1060, top, ppm, seed=9, expr='brave')
    m.face(-0.55); m.set(-1, None, 0.01, perch=1.0, sit=1.0)
    m.reach(-1.0, None, 1, out=-20.0, down=300.0, fwd=170.0, shape='relaxed', up=0.0, fade=0.01)
    m.reach(-1.0, None, -1, out=-20.0, down=300.0, fwd=170.0, shape='relaxed', up=0.0, fade=0.01)
    h = actor('halverson', 745, FLOOR, ppm, seed=10, expr='kind_smile')
    h.face(0.6)
    h.look_at(0.0, (m, 'eyes'), dur=0.3)
    m.look_at(0.0, (h, 'eyes'), dur=0.3)
    h.expr('careful_smile', 1.0, None, 0.6)
    m.reach(1.6, None, 1, out=20.0, down=200.0, fwd=230.0, shape='open', up=0.0, fade=0.6)     # holds out his arm
    h.reach_to(2.0, -1, (m, 'elbow_l'), dur=0.7, z=80.0, contact='palm', shape='grip')        # steadies it
    h.hold_prop('vial', 1, 2.0, None)
    h.reach(2.2, None, 1, out=-30.0, down=120.0, fwd=200.0, shape='grip', up=0.0, fade=0.6)
    h.look_at(2.0, (m, 'elbow_l'), dur=0.3)
    m.look_at(2.4, (1500, 380), dur=0.3)                       # looks away, being brave
    def draw(pen, t):
        room(pen, '#d8e6ee', '#b8c4cc')
        pen.fill(rect(920, top - 6, 380, 24), '#e8eef0'); pen.line(rect(920, top - 6, 380, 24), 3)
        for x_ in (940, 1280): pen.line(poly([(x_, top + 18), (x_, FLOOR)], False), 6, '#9aa2aa')
        fig(pen, m, t, ER); fig(pen, h, t, ER)
    return dict(draw=draw, actors=[m, h], grounded=[h])


@clip('ruth_cabinet_tap', 5.0, 'At sundown Grandma opens the medicine cabinet, swings the mirror aside and taps the little yellow card: "Nobody gets sick in this house after dark."')
def _c_ruth_cab():
    ppm = 380.0; ppc = ppm / 100.0
    cx0, cy0 = 960, FLOOR - 1.66 * ppm
    r = actor('ruth', 852, FLOOR, ppm, seed=11, expr='stern')
    r.face(0.55)
    sw = lambda t: min(1.0, max(0.0, (t - 0.9) / 0.9))       # noqa: E731
    edge = lambda t: (cx0 + 40 * ppc * (1.0 - 0.92 * sw(t)) - 2 * ppc, cy0 + 30 * ppc)     # noqa: E731
    r.reach_to(0.2, 1, edge, t1=1.8, dur=0.6, contact='grip', shape='grip', z=0.0)
    card = (cx0 + 40 * ppc * 0.55, cy0 + 10 * ppc)
    r.look_at(1.6, card, dur=0.4)
    ev = r.tap(2.2, 1, card, n=3)
    r.look_at(3.6, (1500, 520), dur=0.5)                     # to the kids: "Same as always."
    r.talk([(3.9, 4.8, 'Same as always')], env=None, words=None)
    def draw(pen, t):
        room(pen, '#8a7a6a', '#4a4038')
        cabinet(pen, cx0, cy0, ppc, swing=sw(t))
        fig(pen, r, t, WARM2)
    return dict(draw=draw, actors=[r], grounded=[r])


@clip('ruth_phone_tilt', 6.0, 'Rule 1, 3 AM: the landline rings; Grandma, already beside it, lets it ring, picks it up and tilts the receiver so I can hear; I lean in')
def _c_ruth_tilt():
    ppm = 380.0; ppc = ppm / 100.0
    r = actor('ruth', 880, FLOOR, ppm, seed=12, expr='stern')
    n = actor('narr14', 1200, FLOOR, ppm, seed=13, expr='fear')
    r.face(0.45); n.face(-0.55)
    rec = CH.PropTrack('receiver', 1080, FLOOR - 1.45 * ppm + 9 * ppc, ppc)
    r.look_at(0.0, rec, t1=1.2, dur=0.3)
    tc = r.pick_up(rec, 0.8, side=1, dur=1.0)
    r.receiver_to_ear(tc + 0.1, None, side=1, tilt_out=0.0)
    r.receiver_to_ear(2.6, None, side=1, tilt_out=1.0, fade=0.7, toward=n)
    n.look_at(0.0, rec, dur=0.3)
    n.set(3.0, None, 0.8, lean=0.18, h_tilt=-10.0)
    n.look_at(3.0, lambda t: r.grip_point(t, 1, 'receiver'), dur=0.3)
    n.set(3.0, None, 0.8, h_turn=-0.5)                       # turns an ear to it
    def draw(pen, t):
        room(pen, *KITCHEN)
        cr, sock = wall_phone(pen, 1080, FLOOR - 1.45 * ppm, ppc, has_receiver=False)
        rec.draw(pen, t)
        fig(pen, n, t, NIGHT2); fig(pen, r, t, NIGHT2)
        e = CH.receiver_cord_end(r, t, 1) if rec.holder(t) else (cr[0], cr[1] + 11 * ppc)
        CH.draw_coil_cord(pen, e[0], e[1], sock[0], sock[1], ppc, 0.3, t)
    return dict(draw=draw, actors=[r, n], grounded=[r, n])


@clip('ruth_hangup_cord', 6.0, '"Don\'t you dare tell me what you found." She hangs up; it rings again, nine times; she pulls the cord out of the wall and the house goes quiet')
def _c_ruth_cord():
    ppm = 380.0; ppc = ppm / 100.0
    r = actor('ruth', 985, FLOOR, ppm, seed=14, expr='stern')
    r.face(0.5)
    base_x, base_y = 1110, FLOOR - 1.45 * ppm
    rec = CH.PropTrack('receiver', 0, 0, ppc)
    rec.held(-1e9, r, 1)
    r.receiver_to_ear(-1.0, 0.6, side=1)
    r.talk([(0.0, 0.9, "Don't you dare tell me")], env=None, words=None)
    tc = r.put_down(rec, 1.0, 1, base_x, base_y + 9 * ppc, dur=1.0)
    r.look_at(1.0, (base_x, base_y + 9 * ppc), dur=0.3)
    jack = (base_x + 90, FLOOR - 1.02 * ppm)
    r.look_at(2.6, jack, dur=0.4)
    ev = r.pull_cord(2.8, 1, jack, dur=1.6)
    r.expr('set_jaw', 2.8, None, 0.4)
    def draw(pen, t):
        room(pen, *KITCHEN)
        cr, sock = wall_phone(pen, base_x, base_y, ppc, has_receiver=False)
        rec.draw(pen, t)
        yank = 2.8 + 0.65 * 1.6
        phone_jack(pen, jack[0], jack[1], ppc)
        fig(pen, r, t, NIGHT2)
        e = CH.receiver_cord_end(r, t, 1) if rec.holder(t) else (cr[0], cr[1] + 11 * ppc)
        CH.draw_coil_cord(pen, e[0], e[1], sock[0], sock[1], ppc, 0.3, t)
        # the wall cord from the base down to the jack, then (pulled) hanging from her hand
        if t < yank:
            pen.line(smooth([(sock[0], sock[1]), (sock[0] + 30, jack[1] - 120), (jack[0], jack[1])], False), 3, '#d9cfb4')
        else:
            hx, hy = r.where(t, 'hand_l')
            pen.line(smooth([(sock[0], sock[1]), (sock[0] + 20, (sock[1] + hy) / 2 + 60), (hx, hy)], False), 3, '#d9cfb4')
    return dict(draw=draw, actors=[r], grounded=[r])


@clip('halverson_office_phone', 4.0, '3 AM at Larkfield General: Doctor Halverson, rough and out of breath, nineteen hours awake, on the phone in a little office')
def _c_hal_office():
    ppm = 380.0
    seat = FLOOR - 0.47 * ppm
    h = actor('halverson', 900, FLOOR, ppm, seed=15, expr='exhausted')
    h.face(0.55); h.seated(seat, hands='lap')
    h.phone_to_ear(-1.0, None, side=-1)
    h.hold_prop('cell', -1, -1.0, None)
    h.talk([(0.6, 3.4, "This is Doctor Halverson. I'm so sorry about the hour")], env=None, words=None)
    h.reach(1.0, None, 1, out=10.0, down=230.0, fwd=230.0, shape='point', up=0.0, fade=0.6)
    def draw(pen, t):
        room(pen, '#c8d4dc', '#8a949c')
        desk(pen, 1240, FLOOR - 0.75 * ppm, 520)
        pen.fill(rect(820, seat - 8, 170, 20), '#4a5a6a')
        fig(pen, h, t, ER)
    return dict(draw=draw, actors=[h], grounded=[h])


@clip('ruth_receiver_counter', 4.0, 'Rule 2: no voice, just hold music; Grandma does not hang up: she sets the receiver down on the counter gently, like a sleeping baby')
def _c_ruth_counter():
    ppm = 380.0; ppc = ppm / 100.0
    top = FLOOR - 0.92 * ppm
    r = actor('ruth', 780, FLOOR, ppm, seed=16, expr='stern_afraid')
    r.face(0.55)
    rec = CH.PropTrack('receiver', 0, 0, ppc); rec.held(-1e9, r, 1)
    r.receiver_to_ear(-1.0, 1.0, side=1)
    r.look_at(0.8, (1040, top - 10), dur=0.4)
    tc = r.put_down(rec, 1.2, 1, 1040, top - 4 * ppc, dur=1.8, angle=-80.0)
    r.crouch(1.3, 0.12, 3.2, 0.8)
    def draw(pen, t):
        room(pen, *KITCHEN)
        counter(pen, 1100, top, 560, sink=False)
        rec.draw(pen, t)
        fig(pen, r, t, NIGHT2)
    return dict(draw=draw, actors=[r], grounded=[r])


@clip('milo_thirsty_mouth', 5.0, 'Rule 3: Milo in his dinosaur pajamas, lips cracked: "I\'m so thirsty. And my tummy hurts. Grandma, my tummy really..." Grandma claps her hand over his mouth')
def _c_milo_mouth():
    ppm = 380.0
    m = actor('milo_sick', 1000, FLOOR, ppm, seed=17, expr='thirsty')
    r = actor('ruth', 760, FLOOR, ppm, seed=18, expr='stern_afraid')
    m.face(-0.5); r.face(0.6)
    m.hand_on(0.1, 'belly', side=-1, t1=None)
    m.look_at(0.0, (r, 'eyes'), dur=0.3)
    m.talk([(0.4, 1.5, "I'm so thirsty"), (1.7, 3.0, 'And my tummy hurts Grandma my tummy really')], env=None, words=None)
    r.look_at(0.0, (m, 'eyes'), dur=0.3)
    r.hand_over(3.0, 1, m, 'mouth', dur=0.25)
    r.talk([(3.6, 4.5, 'Shh. Not after dark')], env=None, words=None)
    m.expr('fear', 3.1, None, 0.2)
    def draw(pen, t):
        room(pen, *KITCHEN)
        fig(pen, m, t, NIGHT2); fig(pen, r, t, NIGHT2)
    return dict(draw=draw, actors=[m, r], grounded=[m, r])


@clip('narr_peephole', 4.0, 'Rule 4, 3:40: someone knocks; through the peephole I see a woman on our porch (the narrator from behind, an eye to the peephole)')
def _c_narr_peep():
    ppm = 380.0
    n = actor('narr14', 860, FLOOR, ppm, seed=19, expr='fear')
    d_ = door_pts(760, ppm)
    n.face(-0.9)
    n.walk(0.0, 0.8, 260.0, 0.0, facing=-0.9)
    n.turn(0.8, -1.7, 0.5)
    n.head_to(1.1, (d_['peep'][0], d_['peep'][1]), 'eyes', dur=0.8, max_lean=0.2)
    n.reach_to(1.1, 1, (d_['peep'][0] - 60, d_['peep'][1] + 70), dur=0.7, contact='palm', shape='flat', z=-60.0)
    n.set(1.6, None, 0.2, lid_l=0.85)
    def draw(pen, t):
        room(pen, '#262c3a', '#3a2f2a')
        door(pen, 760, FLOOR, ppm=ppm)
        fig(pen, n, t)
    return dict(draw=draw, actors=[n], grounded=[n])


@clip('halverson_porch_plead', 5.0, 'Through the peephole: a raincoat over blue scrubs, hair soaked flat, badge crooked; she knocks on the door (the lens), then pleads: "Milo\'s blood sugar is six hundred and twelve..."')
def _c_hal_porch():
    ppm = 420.0
    h = actor('halverson_rain', 960, FLOOR + 40, ppm, seed=20, expr='pleading')
    h.face(0.0)
    ev = h.knock(0.3, n=3, spacing=0.34, side=0.0)
    h.look_at(0.0, (960, 380), dur=0.3, z=400.0)
    h.talk([(2.0, 4.6, "Milo's blood sugar is six hundred and twelve")], env=None, words=None)
    h.reach(1.9, None, 1, out=60.0, down=-40.0, fwd=280.0, shape='flat', up=0.6, fade=0.6)   # a hand flat on the door
    def draw(pen, t):
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 1080, [(0, '#1a2030'), (1, '#262a34')])
        for k in range(40):                                      # rain behind her
            x = (k * 97 + t * 900) % 1920; y = (k * 53 + t * 1700) % 1080
            pen.line(poly([(x, y), (x - 8, y + 40)], False), 2, '#9fb0d0', 90)
        fig(pen, h, t, dict(rim='#ffd9a0', rim_a=60, side=-1, key=-0.15))
    return dict(draw=draw, actors=[h])


@clip('halverson_write_slide', 6.5, 'She writes in marker, big careful letters, the paper against the door, kneels and slides it under the door')
def _c_hal_write():
    ppm = 380.0; ppc = ppm / 100.0
    h = actor('halverson_rain', 980, FLOOR, ppm, seed=21, expr='set_jaw')
    h.face(-0.9)
    d_ = door_pts(700, ppm)
    note = CH.PropTrack('note', 0, 0, ppc); note.held(-1e9, h, -1)
    h.hold_prop('note', -1, -1.0, 5.6)
    paper = (d_['knob'][0] + 110, FLOOR - 1.2 * ppm)
    h.reach_to(0.0, -1, (paper[0] - 10, paper[1] - 60), t1=3.0, dur=0.5, contact='grip', shape='grip', z=0.0, prop='note')
    ev = h.write_marker(0.4, 2.8, 1, (paper[0] - 5, paper[1] - 10), z=10.0)
    h.look_at(0.4, (paper[0], paper[1] + 20), t1=3.0, dur=0.3)
    tg, ev2 = h.slide_under_door(3.2, -1, note, 790, FLOOR, dur=2.4)
    h.look_at(3.2, (790, FLOOR), dur=0.4)
    def draw(pen, t):
        room(pen, '#1c2230', '#24262c')
        door(pen, 700, FLOOR, c='#4a3a2e', ppm=ppm)
        note.draw(pen, t)
        fig(pen, h, t, dict(rim='#ffd9a0', rim_a=60, side=-1, key=-0.25))
    return dict(draw=draw, actors=[h], grounded=[h])


@clip('ruth_burn_note', 5.0, 'Grandma puts the paper in the sink and lights it with a match')
def _c_ruth_burn():
    ppm = 380.0; ppc = ppm / 100.0
    top = FLOOR - 0.92 * ppm
    r = actor('ruth', 850, FLOOR, ppm, seed=22, expr='stern')
    r.face(0.55)
    ts, ev = r.strike_match(0.3, side=1, dur=1.4)
    r.look_at(0.3, lambda t: r.grip_point(t, 1, 'match'), t1=1.6, dur=0.3)
    r.reach_to(2.2, 1, (1060, top - 6), t1=None, dur=0.9, contact='grip', shape='pinch', z=80.0, prop='match_lit')
    r.look_at(2.2, (1060, top - 6), dur=0.4)
    def draw(pen, t):
        room(pen, *KITCHEN)
        sk = counter(pen, 1080, top, 560, sink=True)
        fire = max(0.0, min(1.0, (t - 3.1) / 0.5))
        if fire < 1.0:
            pen.fill(smooth([(1000, top - 8), (1030, top - 26), (1062, top - 20), (1090, top - 30), (1104, top - 8)], True, 0.6), '#f2efe6', 255 * (1 - fire))
            pen.line(smooth([(1000, top - 8), (1030, top - 26), (1062, top - 20), (1090, top - 30), (1104, top - 8)], True, 0.6), 2.5, '#1d1f26', 255 * (1 - fire))
        if fire > 0: pen.glow(1050, top - 20, 140 * fire, '#ffa040', 170 * fire); pen.fill(oval(1050, top - 26, 40 * fire, 30 * fire), '#ffcf5a', 200 * fire)
        fig(pen, r, t, dict(rim='#ffb060', rim_a=50 + 80 * fire, side=1, key=-0.2))
    return dict(draw=draw, actors=[r], grounded=[r])


@clip('narr_window', 4.0, 'But I went to the window: Doctor Halverson was still there, in her car in our driveway (the narrator at the window, from behind, a hand on the frame)')
def _c_narr_window():
    ppm = 380.0
    n = actor('narr14', 900, FLOOR, ppm, seed=23, expr='fear')
    n.face(-1.6)
    n.walk(0.0, 1.2, 300.0, 0.0, facing=-1.6)
    n.reach_to(1.4, -1, (760, 470), dur=0.6, contact='palm', shape='flat', z=-40.0)
    n.look_at(1.2, (900, 420), dur=0.5, z=-300.0)
    def draw(pen, t):
        room(pen, '#1c2030', '#2a2420')
        window(pen, 900, 260, 420, 420, night=True)
        pen.glow(1000, 600, 120, '#fff2c0', 120)
        fig(pen, n, t, NIGHT2)
    return dict(draw=draw, actors=[n], grounded=[n])


@clip('halverson_car_phone', 4.0, 'Sitting in her car in our driveway at four in the morning after a nineteen-hour shift, phone pressed to her ear, calling our house again and again')
def _c_hal_car():
    ppm = 380.0
    seat = FLOOR - 0.3 * ppm
    h = actor('halverson_rain', 900, FLOOR, ppm, seed=24, expr='exhausted')
    h.face(-0.4); h.seated(seat, hands='lap')
    h.phone_to_ear(-1.0, None, side=1)
    h.hold_prop('cell', 1, -1.0, None)
    h.look_at(0.0, (300, 380), dur=0.3, z=300.0)
    h.set(2.0, None, 0.5, h_nod=0.15)
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#141821')
        car_front_seat(pen, 900, FLOOR, ppm, seat)
        fig(pen, h, t, dict(rim='#9fb6ff', rim_a=60, side=1, key=-0.35))
        pen.fill(rect(0, FLOOR - 0.95 * ppm, 1920, 30), '#22252c')
    return dict(draw=draw, actors=[h], grounded=[])


@clip('later_bus_stop_far', 4.0, 'At the end of our street, at the bus stop under the flickering streetlight, someone sitting on the bench: very tall, folded up, knees above his head. Waiting.')
def _c_later_bus():
    ppm = 120.0
    a = lat(1100, 900, ppm, seed=25)
    a.perch(900 - 0.46 * ppm, 'bench', knee=1.1)
    a.face(-0.4, 0.3)
    a.set(-1, None, 0.01, h_tilt=-10.0)
    def draw(pen, t):
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 1080, [(0, '#05070e'), (1, '#121624')])
        fl = 0.35 + 0.65 * (1.0 if math.sin(t * 13.0) + math.sin(t * 7.1) > -0.6 else 0.15)
        lp = streetlight(pen, 980, 900, 420, fl)
        pen.fill(rect(0, 900, 1920, 180), '#0c0e14')
        bench(pen, 1100, 900 - 0.46 * ppm, 0.9 * ppm)
        CH.draw_later_far(pen, a.x0, a.y0, a.height, a.at(t), t=t, lamp=lp, flicker=fl)
    return dict(draw=draw, actors=[a], grounded=[a])


@clip('ruth_rock_milo', 6.0, 'Rule 5, by four: Milo breathing deep and fast; Grandma sits on the kitchen floor with him in her arms, rocking, humming along with the hold music: "It can wait. It can wait."')
def _c_ruth_rock():
    ppm = 380.0
    r = actor('ruth', 860, FLOOR, ppm, seed=26, expr='stern_afraid')
    m = actor('milo_sick', 1010, FLOOR, ppm, seed=27, expr='dazed')
    r.face(0.8); m.face(0.75)
    r.sit_floor(-1.0, None, 0.01)
    m.sit_floor(-1.0, None, 0.01)
    r.rock(0.2, None, 1.0, 0.45)
    m.rock(0.2, None, 0.8, 0.45, hum=False)
    ev = m.breathe_fast(0.0, 6.0, 0.95)
    m.set(-1, None, 0.01, lean=-0.18, h_tilt=-8.0)
    r.reach_to(0.0, 1, (m, 'chest'), dur=0.4, contact='palm', shape='open', z=110.0)
    r.reach_to(0.0, -1, (m, 'belly'), dur=0.4, contact='palm', shape='open', z=90.0)
    r.look_at(0.0, (m, 'head'), dur=0.3)
    r.talk([(3.6, 5.2, 'It can wait. It can wait.')], env=None, words=None, intensity=0.5)
    def draw(pen, t):
        room(pen, *KITCHEN)
        fig(pen, r, t, NIGHT2); fig(pen, m, t, NIGHT2)
        for sd in (1, -1): CH.draw_arm(pen, 'ruth', sd, r.at(t), x=r.x0, y_feet=r.y0, height=r.height, light=NIGHT2, t=t)
    return dict(draw=draw, actors=[r, m], grounded=[])


@clip('narr_tells_ruth', 5.0, '"Grandma, that\'s what the voice told you. In 1979." She stops rocking: "How do you know what the voice said?"')
def _c_narr_tells():
    ppm = 380.0
    r = actor('ruth', 1000, FLOOR, ppm, seed=28, expr='stern_afraid')
    n = actor('narr14', 640, FLOOR, ppm, seed=29, expr='asking')
    r.face(-0.75); n.face(0.6)
    r.sit_floor(-1.0, None, 0.01)
    r.rock(-1.0, 1.4, 1.0, 0.45, hum=True)
    n.kneel_down(-1.0, 0.01, knees=0)
    n.look_at(0.0, (r, 'eyes'), dur=0.3)
    n.talk([(0.2, 1.9, "Grandma. That's what the voice told you. In 1979.")], env=None, words=None)
    r.look_at(1.6, (n, 'eyes'), dur=0.8)
    r.expr('fear', 2.0, None, 0.6)
    r.talk([(2.8, 4.4, 'How do you know what the voice said')], env=None, words=None, intensity=0.7)
    def draw(pen, t):
        room(pen, *KITCHEN)
        fig(pen, n, t, NIGHT2); fig(pen, r, t, NIGHT2)
    return dict(draw=draw, actors=[r, n], grounded=[n])


@clip('later_armchair_front', 5.0, 'Rule 6: at the front of the room, in Grandpa\'s armchair, facing all of them: so tall the armchair looks like a toy, knees higher than his head, hands... the clipboard with no paper, clicking his pen')
def _c_later_arm():
    ppm = 260.0
    seat = FLOOR - 0.42 * ppm
    a = lat(960, FLOOR, ppm, seed=30)
    a.perch(seat, 'armchair')
    a.face(0.0, 0.0)
    a.set(-1, None, 0.01, h_tilt=8.0)
    ev = a.click_pen([0.6, 1.0, 2.2, 2.6, 3.8])
    a.tilt_head(1.4, 10.0, 1.6)
    def draw(pen, t):
        fluo_room(pen, t)
        armchair(pen, 960, seat, 0.95 * ppm, back_h=0.9 * ppm, c='#6a4a30')
        fig(pen, a, t, FLUO)
    return dict(draw=draw, actors=[a], grounded=[a])


@clip('ghosts_row', 4.0, 'Every chair taken: a man holding his chest, a woman holding her side, a teenager holding his arm in his lap, a little girl in a coat too small for her; all gray, all still, holding paper tickets; and in the last row, Grandpa, his ticket\'s ink long gone')
def _c_ghosts():
    ppm = 300.0
    seat = FLOOR - 0.45 * ppm
    xs = (330, 620, 910, 1200, 1560)
    who = ('ghost_chest', 'ghost_side', 'ghost_teen', 'ghost_girl', 'grandpa_ghost')
    acts = []
    for i, (x, w) in enumerate(zip(xs, who)):
        a = actor(w, x, FLOOR, ppm, seed=40 + i, expr='waiting')
        a.face(0.6 if i < 4 else 0.4)
        s_y = seat if w != 'ghost_girl' else FLOOR - 0.45 * ppm
        a.seated(s_y, hands=None)
        txt = '' if w == 'grandpa_ghost' else str(40 + 7 * i)
        if w == 'ghost_chest': a.hand_on(-1.0, 'chest', side=-1, dur=0.01)
        if w == 'ghost_side': a.hand_on(-1.0, 'side', side=1, dur=0.01)
        if w == 'ghost_teen': a.reach(-1.0, None, 1, out=-40.0, down=280.0, fwd=200.0, shape='relaxed', up=0.0, fade=0.01)
        a.ticket_hold(-1.0, txt, side=-1 if w != 'ghost_chest' else 1)
        acts.append(a)
    def draw(pen, t):
        fluo_room(pen, t)
        for x in xs: plastic_chair(pen, x, FLOOR, ppm, facing=1.0, c='#5a6a7a')
        for a in acts: fig(pen, a, t, FLUO)
    return dict(draw=draw, actors=acts, grounded=acts)


@clip('later_tear_ticket', 7.0, 'Without standing up he reaches all the way across the room, tears a ticket from the red machine and holds it out to me between two long fingers: MILO. I do not take it.')
def _c_later_ticket():
    ppm = 240.0
    seat = FLOOR - 0.42 * ppm
    a = lat(520, FLOOR, ppm, seed=31)
    a.perch(seat, 'armchair', hands=('lap', 'floor'))
    a.face(0.45, 0.0)
    n = actor('narr14', 1560, FLOOR, ppm, seed=32, expr='fear')
    n.face(-0.6)
    slot = (1220, FLOOR - 1.19 * ppm)
    a.look_at(0.0, (n, 'eyes'), dur=0.8)
    hands_of_n = lambda t: (lambda p: (p[0] - 80, p[1] - 30))(n.where(t, 'chest', post=False))   # noqa: E731
    tt, ev = a.tear_ticket(0.4, -1, slot, 'MILO', dur=1.8, offer_to=hands_of_n, offer_t=2.9, offer_dur=1.6)
    n.look_at(0.4, lambda t: a.where(t, 'tips_r'), dur=0.3)
    n.reach(4.8, None, 1, out=0.0, down=260.0, fwd=40.0, shape='fist', up=0.0, fade=0.5)   # hands stay down: I don't take it
    n.reach(4.8, None, -1, out=0.0, down=260.0, fwd=40.0, shape='fist', up=0.0, fade=0.5)
    n.lean_in(4.6, 0.6, None, -0.4)
    def draw(pen, t):
        fluo_room(pen, t)
        ticket_machine(pen, slot[0], FLOOR, ppm)
        armchair(pen, 520, seat, 0.95 * ppm, back_h=0.9 * ppm, c='#6a4a30')
        fig(pen, a, t, FLUO); fig(pen, n, t, FLUO)
    return dict(draw=draw, actors=[a, n], grounded=[n])


@clip('later_take_wrist_count', 6.0, 'Rule 7: I don\'t take the ticket, so he takes my wrist instead: cold, smooth fingers on the inside of my wrist; he counts. "One..." "Two..." "Three..."')
def _c_later_wrist():
    ppm = 260.0
    seat = FLOOR - 0.42 * ppm
    a = lat(700, FLOOR, ppm, seed=33)
    a.perch(seat, 'armchair', hands=('lap', 'pen'))
    a.face(0.5, 0.0)
    n = actor('narr14', 1230, FLOOR, ppm, seed=34, expr='fear')
    n.face(-0.55)
    n.reach(0.0, None, 1, out=40.0, down=150.0, fwd=200.0, shape='open', up=0.0, fade=0.5)     # the wrist, held out
    tc = a.take_wrist(0.6, -1, n, 1, dur=1.2)
    a.look_at(0.0, (n, 'eyes'), dur=0.8)
    ev = []
    for i, tt in enumerate((2.2, 3.5, 4.9)): ev += a.count(tt, i + 1)
    n.look_at(0.8, (n, 'wrist_l'), t1=2.0, dur=0.3)
    n.look_at(2.2, (a, 'eyes'), dur=0.4)
    n.lean_in(3.0, 2.5, None, -0.2)
    def draw(pen, t):
        fluo_room(pen, t)
        armchair(pen, 700, seat, 0.95 * ppm, back_h=0.9 * ppm, c='#6a4a30')
        fig(pen, a, t, FLUO); fig(pen, n, t, FLUO)
        CH.draw_later_arm(pen, a, t, -1, FLUO)
    return dict(draw=draw, actors=[a, n], grounded=[n])


@clip('narr_asks_tape', 7.0, 'I asked. "What did you find?" He stops counting. "What\'s wrong with my brother? What do we do? How long is too long? Who are you?" With every question the tape comes looser, one strip, then another; he flinches like the questions are light')
def _c_narr_asks():
    ppm = 300.0
    seat = FLOOR - 0.42 * ppm
    a = lat(760, FLOOR, ppm, seed=35)
    a.perch(seat, 'armchair', hands=('lap', 'pen'))
    a.face(0.45, 0.05)
    n = actor('narr14', 1360, FLOOR, ppm, seed=36, expr='asking')
    n.face(-0.55)
    n.look_at(0.0, (a, 'eyes'), dur=0.3)
    a.look_at(0.0, (n, 'eyes'), dur=0.8)
    qs = [(0.3, 1.2, 'What did you find'), (1.6, 2.7, "What's wrong with my brother"), (3.0, 3.8, 'What do we do'),
          (4.1, 5.0, 'How long is too long'), (5.3, 6.1, 'Who are you')]
    n.talk(qs, env=None, words=None)
    n.expr('asking_hard', 3.0, None, 1.5)
    n.lean_in(3.0, 3.0, None, 0.3)
    ev = []
    taped = [1.0, 0.86, 0.72, 0.58, 0.44, 0.3]
    for i, (q0, q1, _) in enumerate(qs):
        ev += a.loosen_tape(q1 - 0.1, q1 + 0.25, taped[i], taped[i + 1], flinch=True)
    def draw(pen, t):
        fluo_room(pen, t)
        armchair(pen, 760, seat, 0.95 * ppm, back_h=0.9 * ppm, c='#6a4a30')
        fig(pen, a, t, FLUO); fig(pen, n, t, FLUO)
    return dict(draw=draw, actors=[a, n], grounded=[n])


@clip('later_faces', 6.0, 'Under the tape there is no doctor: Grandpa\'s face, gray and patient; then a man I never saw; then a little girl; then my grandmother; then... me (close)')
def _c_later_faces():
    a = CH.Acting('later', seed=37, height=CH.height_px('later', 380.0))
    a.place(900, FLOOR)
    a.perch(None, 'plastic', hands=('lap', 'pen'))
    a.face(0.15, -0.1)
    a.set(-1, None, 0.01, dl_tape=0.45, h_tilt=8.0)
    a.faces([(0.0, 1.0), (1.1, 2.0), (2.2, 3.0), (3.3, 4.0), (4.6, 5.0)], fade=0.6)
    a.tilt_head(0.5, 10.0, 4.0)
    def draw(pen, t):
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 1080, [(0, '#5a6a4a'), (1, '#2a3024')])
        CH.draw_bust(pen, 'later', 960, 700, 0.62, a.at(t), t=t, light=FLUO)
    return dict(draw=draw, actors=[a])


@clip('narr_pull_free_card', 6.0, 'I pull my wrist free; on the way out I tear Grandma\'s rules out of the medicine cabinet: on the back of the card, in faded ink from 1979, someone signed it: Doctor Later')
def _c_narr_card():
    ppm = 380.0; ppc = ppm / 100.0
    cx0, cy0 = 940, FLOOR - 1.62 * ppm
    n = actor('narr14', 800, FLOOR, ppm, seed=38, expr='determined')
    n.face(0.55)
    card = CH.PropTrack('card', cx0 + 40 * ppc * 0.55, cy0 + 10 * ppc, ppc)
    n.look_at(0.0, card, dur=0.3)
    tc = n.pick_up(card, 0.3, side=1, dur=1.2, carry=None)
    ev = [n._ev(tc, 'card_tear', 0.0, pan=0.0)]
    n.reach(tc + 0.4, None, 1, out=-40.0, down=60.0, fwd=220.0, shape='grip', up=0.0, fade=0.6)
    n.set(tc + 1.4, None, 0.01, hl_prop='card_back')
    n.look_at(tc + 0.5, lambda t: n.grip_point(t, 1, 'card'), dur=0.3)
    n.expr('shock_shut', tc + 1.5, None, 0.4)
    def draw(pen, t):
        room(pen, '#8a7a6a', '#4a4038')
        cabinet(pen, cx0, cy0, ppc, swing=1.0, card=False)
        card.draw(pen, t)
        fig(pen, n, t, WARM2)
    return dict(draw=draw, actors=[n], grounded=[n])


@clip('narr_carry_milo', 5.0, 'I pick Milo up off the kitchen floor and carry him out; Grandma does not stop me')
def _c_carry():
    ppm = 380.0
    n = actor('narr14', 700, FLOOR, ppm, seed=39, expr='determined')
    m = actor('milo_sick', 0, 0, ppm, seed=40, expr='sleepy')
    n.face(1.0)
    n.carry(-1.0, m)
    n.walk(0.6, 4.4, 0.0, 600.0, surface='inside')
    m.face(-0.75)
    def draw(pen, t):
        room(pen, *KITCHEN)
        CH.draw_carry_child(pen, n, m, t, NIGHT2)
    return dict(draw=draw, actors=[n, m], grounded=[n])


@clip('halverson_run_steps', 3.0, 'Doctor Halverson is already out of her car and running up the steps, like that open door was all she\'d been waiting for')
def _c_hal_run():
    ppm = 380.0
    h = actor('halverson_rain', 300, FLOOR, ppm, seed=41, expr='set_jaw')
    h.face(1.0)
    ev = h.run(0.2, 2.6, 0.0, 1100.0, surface='porch')
    h.look_at(0.0, (1700, 420), dur=0.3)
    def draw(pen, t):
        room(pen, '#1c2230', '#24262c')
        fig(pen, h, t, dict(rim='#ffd9a0', rim_a=60, side=-1, key=-0.2))
    return dict(draw=draw, actors=[h], grounded=[h])


@clip('halverson_pulse_car', 5.0, 'In the car she reaches for Milo\'s wrist: two fingers on it, her watch up, counting: "One-forty. Fast. That\'s okay. He\'s fighting. We\'re going."')
def _c_hal_pulse():
    ppm = 380.0
    seat = FLOOR - 0.3 * ppm
    m = actor('milo_sick', 1020, FLOOR, ppm, seed=42, expr='sleepy')
    m.face(-0.4); m.seated(seat, hands=None)
    m.reach(-1.0, None, 1, out=10.0, down=220.0, fwd=150.0, shape='relaxed', up=0.0, fade=0.01)
    h = actor('halverson_rain', 760, FLOOR, ppm, seed=43, expr='focused')
    h.face(0.5); h.seated(seat, hands=None)
    h.take_pulse(0.3, -1, m, 1, t1=None)                     # the watch is on her left wrist
    h.talk([(2.6, 4.6, "One-forty. Fast. That's okay. He's fighting.")], env=None, words=None)
    h.look_at(2.5, (m, 'eyes'), dur=0.4)
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#141821')
        pen.fill(rect(600, seat - 8, 640, 26), '#45454c')
        fig(pen, h, t, NIGHT2); fig(pen, m, t, NIGHT2)
    return dict(draw=draw, actors=[h, m], grounded=[])


@clip('halverson_drive_mirror', 5.0, 'She drives and talks the whole way; she looks in the mirror, sees him, is not surprised; she sets her jaw: "Not tonight. Not on my shift." and drives faster')
def _c_hal_drive():
    ppm = 380.0
    seat = FLOOR - 0.3 * ppm
    h = actor('halverson_rain', 900, FLOOR, ppm, seed=44, expr='focused')
    h.face(0.0); h.seated(seat, hands=None)
    wc = (900, FLOOR - 0.78 * ppm)
    g10, g2 = (wc[0] - 120, wc[1] - 40), (wc[0] + 120, wc[1] - 40)
    h.drive(0.0, None, g10, g2)
    h.talk([(0.3, 1.6, 'Questions are good. Questions are how we win')], env=None, words=None)
    h.look_at(1.9, (960, 160), t1=3.3, dur=0.35, z=200.0)           # up to the rear-view mirror
    h.expr('set_jaw', 2.8, None, 0.4)
    h.talk([(3.5, 4.6, 'Not tonight. Not on my shift')], env=None, words=None)
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#141821')
        pen.fill(rrect(860, 120, 200, 60, 10), '#2a2c34'); pen.line(rrect(860, 120, 200, 60, 10), 3)
        fig(pen, h, t, NIGHT2)
        CH.draw_steering_wheel(pen, wc[0], wc[1], 150)
        for side in (1, -1): CH.draw_arm(pen, h.who, side, h.at(t), x=h.x0, y_feet=h.y0, height=h.height, light=NIGHT2, t=t)
    return dict(draw=draw, actors=[h])


@clip('later_car_backseat', 5.0, 'In the rear-view mirror: he is in the back seat, folded up beside Milo, his head bent against the roof, his clipboard in his lap, clicking his pen: "It can wait."')
def _c_later_car():
    ppm = 300.0
    floor = 980.0
    seat = floor - 0.30 * ppm
    roof = floor - 1.18 * ppm
    a = lat(1100, floor, ppm, seed=45)
    a.perch(seat, 'car')
    a.bend_to_roof(roof)
    a.face(0.0, 0.0)
    ev = a.click_pen([0.6, 1.0, 2.4, 2.8, 4.0])
    m = actor('milo_sick', 640, floor, ppm, seed=46, expr='sleepy')
    m.face(0.2); m.seated(seat, hands='lap'); m.set(-1, None, 0.01, h_tilt=-14.0, lid_l=0.6, lid_r=0.6)
    def draw(pen, t):
        car_back(pen, 860, floor, ppm, roof, seat)
        fig(pen, m, t, NIGHT2)
        fig(pen, a, t, NIGHT2)
    return dict(draw=draw, actors=[a, m])


@clip('mom_wheelchair_run', 4.0, 'The emergency doors open before we reach them: Mom in her scrubs, running, pushing a wheelchair')
def _c_mom_wc():
    ppm = 380.0; ppc = ppm / 100.0
    m = actor('mom_rn', 400, FLOOR, ppm, seed=47, expr='set_jaw')
    m.face(1.0)
    ev = m.run(0.2, 3.4, 0.0, 900.0, surface='inside')
    def wc_at(t):
        P = m._raw(t, False)
        return 400 + P.dx + 0.62 * ppm
    for side in (1, -1):
        m.reach_to(0.0, side, lambda t: (wc_at(t) - 34 * ppc, FLOOR - 97 * ppc), dur=0.3, contact='grip', shape='grip', z=-10.0 * side)
    def draw(pen, t):
        room(pen, '#dfe8ee', '#b8c4cc')
        fig(pen, m, t, ER)
        CH.draw_wheelchair(pen, wc_at(t), FLOOR, ppc, facing=1.0, t=t, roll=wc_at(t))
        CH.draw_arm(pen, m.who, -1, m.at(t), x=m.x0, y_feet=m.y0, height=m.height, light=ER, t=t)
    return dict(draw=draw, actors=[m], grounded=[m])


@clip('nurse_chest_man', 5.0, 'In the waiting room a man sits down holding his chest, and a nurse walks straight up to him: "Sir, you don\'t wait. You come with me, right now."')
def _c_nurse_man():
    ppm = 360.0
    seat = FLOOR - 0.45 * ppm
    c_ = actor('chest_man', 760, FLOOR, ppm, seed=48, expr='stern_afraid')
    c_.face(0.5); c_.sit_on(0.2, seat, dur=1.0, hands=None)
    c_.hand_on(0.0, 'chest', side=-1)
    nu = actor('er_nurse', 1500, FLOOR, ppm, seed=49, expr='calm_firm')
    nu.face(-1.0)
    nu.walk(1.0, 2.8, 0.0, -480.0, surface='inside')
    nu.look_at(1.0, (c_, 'eyes'), dur=0.3)
    nu.reach_to(3.0, 1, (c_, 'shoulder_l'), dur=0.5, contact='palm', shape='open', z=40.0)
    nu.talk([(3.0, 4.8, "Sir, you don't wait. You come with me, right now.")], env=None, words=None)
    c_.look_at(2.4, (nu, 'eyes'), dur=0.4)
    def draw(pen, t):
        room(pen, '#dfe8ee', '#b8c4cc')
        for x in (520, 760): plastic_chair(pen, x, FLOOR, ppm, facing=1.0, c='#5a7a9a')
        fig(pen, c_, t, ER); fig(pen, nu, t, ER)
    return dict(draw=draw, actors=[c_, nu], grounded=[c_, nu])


@clip('empty_chair_rocking', 3.0, 'The chair next to his is empty, still rocking a little, like something very tall had just gotten up and left')
def _c_empty():
    ppm = 380.0
    def draw(pen, t):
        room(pen, '#dfe8ee', '#b8c4cc')
        plastic_chair(pen, 760, FLOOR, ppm, facing=1.0, c='#5a7a9a')
        plastic_chair(pen, 1100, FLOOR, ppm, facing=1.0, c='#5a7a9a', rock=CH.chair_rock(t, -0.3, amp=5.0))
    return dict(draw=draw, actors=[])


@clip('milo_er_bed', 4.0, 'Bright lights, fluids, insulin, machines that beep like they are cheering: Milo on the bed with an IV and monitor leads; his eyes open; he smiles')
def _c_milo_er():
    ppm = 380.0
    top = FLOOR - 0.62 * ppm
    m = actor('milo_er', 900, top, ppm, seed=50, expr='sleepy')
    m.face(0.55); m.set(-1, None, 0.01, perch=1.0, sit=1.0)
    m.reach(-1.0, None, 1, out=-20.0, down=300.0, fwd=170.0, shape='relaxed', up=0.0, fade=0.01)
    m.reach(-1.0, None, -1, out=-20.0, down=300.0, fwd=170.0, shape='relaxed', up=0.0, fade=0.01)
    m.set(-1, None, 0.01, iv=1.0)
    m.expr('kid_grin', 2.2, None, 0.8)
    m.look_at(1.6, (1400, 420), dur=0.5)
    def draw(pen, t):
        room(pen, '#e8f0f4', '#c8d2d8')
        er_bed(pen, 900, top, 560)
        monitor(pen, 1450, 380, t)
        fig(pen, m, t, ER)
    return dict(draw=draw, actors=[m])


@clip('milo22_run_phone', 4.0, 'Milo is twenty-two now: he runs marathons, he checks his blood sugar on his phone (a sensor on his arm)')
def _c_milo22():
    ppm = 360.0
    m = actor('milo22', 400, FLOOR, ppm, seed=51, expr='kind_smile')
    m.face(1.0)
    ev = m.run(0.0, 1.8, 0.0, 700.0, surface='porch')
    m.hold_prop('cell_glucose', 1, 2.2, None)
    m.reach(2.2, None, 1, out=-40.0, down=60.0, fwd=230.0, shape='grip', up=0.0, fade=0.6)
    m.turn(2.0, 0.3, 0.6)
    m.look_at(2.5, lambda t: m.grip_point(t, 1, 'cell_glucose'), dur=0.3)
    def draw(pen, t):
        room(pen, '#bfe0f0', '#8aa070')
        fig(pen, m, t, dict(rim='#fff2c0', rim_a=60, side=-1, key=0.2))
    return dict(draw=draw, actors=[m], grounded=[m])


@clip('ruth_sick_ticket', 4.0, 'Sunrise: Grandma sitting in Grandpa\'s armchair, a paper ticket in her hand: RUTH. Chest pains since midnight; she hadn\'t said a word')
def _c_ruth_sick():
    ppm = 380.0
    seat = FLOOR - 0.43 * ppm
    r = actor('ruth_sick', 900, FLOOR, ppm, seed=52, expr='pale_hidden')
    r.face(0.45); r.seated(seat, hands=None)
    r.ticket_hold(-1.0, 'RUTH', side=1)
    r.hand_on(-1.0, 'chest', side=-1, dur=0.01)
    r.look_at(0.4, (r, 'lap'), t1=2.4, dur=0.6)
    r.look_at(2.6, (1500, 500), dur=0.6)
    def draw(pen, t):
        room(pen, '#8a7060', '#4a3a30')
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 1920, 0, [(0, '#ffb070', 0), (1, '#ffb070', 70)])
        armchair(pen, 920, seat, 340, c='#6a4a30')
        fig(pen, r, t, WARM2)
    return dict(draw=draw, actors=[r])


@clip('mom_dials', 4.0, 'My mom picks up the phone and dials: "You don\'t wait," she says. "You call."')
def _c_mom_dials():
    ppm = 380.0
    m = actor('mom_rn', 900, FLOOR, ppm, seed=53, expr='set_jaw')
    m.face(0.4)
    m.hold_prop('cell', -1, -1.0, None)
    m.reach(-1.0, None, -1, out=-40.0, down=70.0, fwd=220.0, shape='grip', up=0.0, fade=0.01)
    ev = m.dial(0.3, 1, lambda t: m.grip_point(t, -1, 'cell', post=False), n=3, gap=0.3)
    m.look_at(0.0, lambda t: m.grip_point(t, -1, 'cell'), t1=1.8, dur=0.3)
    m.phone_to_ear(2.0, None, side=-1)
    m.look_at(2.2, (1500, 520), dur=0.4)
    m.talk([(2.6, 3.8, "You don't wait. You call.")], env=None, words=None)
    def draw(pen, t):
        room(pen, '#8a7060', '#4a3a30')
        fig(pen, m, t, WARM2)
    return dict(draw=draw, actors=[m], grounded=[m])


@clip('ruth_cardio_coffee', 5.0, 'Grandma asks so many questions now that her cardiologist brings her coffee, just to keep up')
def _c_ruth_cardio():
    ppm = 380.0
    seat = FLOOR - 0.47 * ppm
    r = actor('ruth', 700, FLOOR, ppm, seed=54, expr='asking')
    r.face(0.5); r.seated(seat, hands=None)
    c_ = actor('cardio', 1180, FLOOR, ppm, seed=55, expr='kind_smile')
    c_.face(-0.5)
    c_.hold_prop('cup', 1, -1.0, None)
    c_.reach(-1.0, None, 1, out=-30.0, down=120.0, fwd=180.0, shape='grip', up=0.0, fade=0.01)
    r.look_at(0.0, (c_, 'eyes'), dur=0.3); c_.look_at(0.0, (r, 'eyes'), dur=0.3)
    r.talk([(0.3, 1.4, 'And what does that one do'), (1.8, 2.8, 'And how long')], env=None, words=None)
    r.reach(0.3, 2.8, 1, out=40.0, down=150.0, fwd=180.0, shape='point', up=0.0, fade=0.5)
    c_.talk([(3.0, 4.4, 'Here. You will need this.')], env=None, words=None)
    def draw(pen, t):
        room(pen, '#e8eef0', '#c8d0d4')
        pen.fill(rect(600, seat - 8, 220, 22), '#5a7a9a')
        fig(pen, r, t, ER); fig(pen, c_, t, ER)
    return dict(draw=draw, actors=[r, c_], grounded=[c_])


@clip('narr29_desk', 5.0, 'I\'m a pediatrician now; I work nights: three in the morning, a little office at Larkfield General, a stack of test results that came back late, the phone; nineteen hours awake')
def _c_narr29():
    ppm = 380.0
    seat = FLOOR - 0.47 * ppm
    n = actor('narr29', 760, FLOOR, ppm, seed=56, expr='tired_kind')
    n.face(0.55); n.seated(seat, hands=None)
    n.reach(-1.0, 1.6, 1, out=10.0, down=200.0, fwd=250.0, shape='point', up=0.0, fade=0.01)
    n.look_at(0.0, (1180, FLOOR - 0.8 * 380), t1=1.8, dur=0.3)
    n.hold_prop('cell', -1, 1.8, None)
    n.phone_to_ear(2.2, None, side=-1)
    n.look_at(2.6, (1500, 520), dur=0.5)
    def draw(pen, t):
        room(pen, '#c8d4dc', '#8a949c')
        desk(pen, 1180, FLOOR - 0.75 * ppm, 520)
        pen.fill(rect(680, seat - 8, 170, 20), '#4a5a6a')
        fig(pen, n, t, ER)
    return dict(draw=draw, actors=[n], grounded=[n])


@clip('hall_last_chair', 4.0, 'Some nights, when the hallways are empty, I hear a pen click; at the end of the hall, in the last plastic chair, something very tall is folded up, waiting')
def _c_hall():
    ppm = 110.0
    a = lat(1500, 760, ppm, seed=57)
    a.perch(None, 'plastic')
    a.face(-0.5, 0.3)
    ev = a.click_pen([1.0, 1.4])
    def draw(pen, t):
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 1080, [(0, '#c8d0d0'), (1, '#9aa4a4')])
        pen.fill(poly([(0, 1080), (1920, 1080), (1700, 760), (1250, 760)]), '#8a948c')
        for k in range(3): plastic_chair(pen, 1340 + k * 55, 760, ppm, facing=-1.0, c='#5a7a9a')
        plastic_chair(pen, 1500, 760, ppm, facing=-1.0, c='#5a7a9a')
        fig(pen, a, t, FLUO)
    return dict(draw=draw, actors=[a])


@clip('ruth_door_refuse', 4.0, '"Doctors don\'t make house calls," Grandma says through the door (her back to us, a hand flat on the door, not opening it)')
def _c_ruth_door():
    ppm = 380.0
    r = actor('ruth', 900, FLOOR, ppm, seed=58, expr='stern')
    d_ = door_pts(760, ppm)
    r.face(-1.75)
    r.reach_to(0.3, 1, (d_['knob'][0] + 40, d_['peep'][1] + 80), dur=0.7, contact='palm', shape='flat', z=-80.0)
    r.head_to(0.5, (d_['peep'][0] + 40, d_['peep'][1] + 60), 'mouth', dur=0.8, max_lean=0.15)
    r.talk([(1.2, 2.6, "Doctors don't make house calls")], env=None, words=None)
    def draw(pen, t):
        room(pen, '#262c3a', '#3a2f2a')
        door(pen, 760, FLOOR, ppm=ppm)
        fig(pen, r, t, NIGHT2)
    return dict(draw=draw, actors=[r], grounded=[r])


if __name__ == '__main__':
    main()
