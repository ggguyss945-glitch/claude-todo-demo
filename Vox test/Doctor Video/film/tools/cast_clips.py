"""cast_clips.py: acting clips of the Bunnyman film's cast (characters.py), one per scripted action, written to W/cast/clips/.

    cd "Vox test/Bunnyman Video/film" && python3 tools/cast_clips.py [names...] [--fps 60] [--strip-only]

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


# ================================================================================================ the clips
@clip('mom_sit_stand', 5.0, 'Mom walks to the armchair, turns, sits (feet stay on the floor), then stands up with the weight forward first')
def _c_mom_sit_stand():
    ppm = 380.0
    seat = FLOOR - 0.45 * ppm
    m = actor('mom', 700, FLOOR, ppm, seed=2, expr='too_still')
    m.face(1.0)
    m.walk(0.0, 1.3, -260.0, 120.0, surface='inside')
    m.turn(1.3, -0.45, 0.5)
    m.sit_on(1.7, seat, dur=1.0, t1=3.5, hands='lap')
    m.look_at(0.2, (1500, 520), t1=1.2, dur=0.3)
    def draw(pen, t):
        room(pen)
        armchair(pen, 820, seat, 330)
        fig(pen, m, t, WARM)
    return dict(draw=draw, actors=[m], grounded=[m])


@clip('mom_takes_ring_pockets', 6.0, '"You opened it." Mom takes the ring from the narrator\'s hand, stares at it a long time, pockets it')
def _c_mom_ring():
    ppm = 380.0
    n = actor('narrator', 1130, FLOOR, ppm, seed=3, expr='fear')
    m = actor('mom', 800, FLOOR, ppm, seed=2, expr='too_still')
    n.face(-0.45); m.face(0.5)
    ring = CH.PropTrack('ring', 0, 0, ppm / 100.0)
    ring.held(-1e9, n, 1)
    n.hold_prop('ring', 1, -1e9, 1.25)
    n.reach(-1.0, 1.0, 1, out=40.0, down=150.0, fwd=210.0, shape='grip', up=0.0, fade=0.6)
    n.look_at(0.0, (m, 'eyes'), dur=0.3)
    m.look_at(0.0, (n, 'hand_l'), t1=1.6, dur=0.4)
    tc = n.give(ring, 0.6, 1, m, -1, dur=1.3)
    # Mom holds it up and stares at it
    m.reach_to(tc + 0.5, -1, (900, 560), t1=4.3, dur=0.7, contact='grip', prop='ring', z=160.0, fade=0.6)
    m.look_at(1.9, (900, 560), t1=4.4, dur=0.5)
    m.expr('dead_stare', 2.0, 4.3, 0.6)
    # pocket: the hand goes to the cardigan pocket at the hip and comes back empty
    pk = lambda t: (m.where(t, 'hip', post=False)[0] + 24, m.where(t, 'hip', post=False)[1] + 6)
    m.reach_to(4.4, -1, pk, t1=5.2, dur=0.5, contact='tips', z=90.0, fade=0.5)
    ring.gone(4.85)
    m.set(4.85, None, 0.01, hr_prop=None)
    m.look_at(4.9, (n, 'eyes'), dur=0.4)
    def draw(pen, t):
        room(pen)
        fig(pen, m, t, WARM); fig(pen, n, t, WARM)
    return dict(draw=draw, actors=[m, n], grounded=[m, n])


@clip('bunny_treeline_wave_point', 6.0, 'At the treeline under the moon: the slow wave, the arm lowers, he lifts a paw and points past us')
def _c_bunny_tree():
    ppm = 300.0
    b = actor('bunny', 960, 900, ppm, seed=4)
    b.wave(0.2, 2.6, side=1, slow=True)
    b.point_at(3.3, (300, 380), t1=None, side=-1, dur=0.8, z=500.0)
    b.set(3.0, None, 0.6, h_tilt=-8.0)
    def draw(pen, t):
        treeline(pen, 780, t)
        fig(pen, b, t, dict(rim='#9fb6ff', rim_a=80, side=1, key=-0.35))
    return dict(draw=draw, actors=[b], grounded=[b], floor=900.0)



def doorway(pen, x, y=FLOOR, w=230, h=560, inside='#141824', c='#d9d2c4'):
    pen.fill(rect(x - w / 2, y - h, w, h), inside)
    pen.line(rect(x - w / 2, y - h, w, h), 4)
    pen.fill(rect(x - w / 2 - 22, y - h - 22, 22, h + 22), c); pen.fill(rect(x + w / 2, y - h - 22, 22, h + 22), c)
    pen.fill(rect(x - w / 2 - 22, y - h - 22, w + 44, 22), c)
    pen.line(rect(x - w / 2 - 22, y - h - 22, w + 44, h + 22), 3)


def frame_over(pen, x, y=FLOOR, w=230, h=560, c='#d9d2c4'):
    """The near jamb of a doorway drawn over a figure standing in it."""
    pen.fill(rect(x + w / 2, y - h - 22, 22, h + 22), c); pen.line(rect(x + w / 2, y - h - 22, 22, h + 22), 3)


@clip('bunny87_parade_wave', 4.0, '1987 parade: the clean mascot on the last float, basket of plastic eggs in one paw, waving with the other')
def _c_parade():
    ppm = 330.0
    b = actor('bunny87', 960, 900, ppm, seed=5)
    b.face(0.2)
    b.hold_prop('basket', -1)
    b.reach(-1.0, None, -1, out=40.0, down=230.0, fwd=150.0, shape='grip', up=0.0, fade=0.01)
    b.wave(0.3, 3.6, side=1, speed=0.8)
    b.set(0.0, None, 0.5, h_tilt=6.0)
    def draw(pen, t):
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 1080, [(0, '#bfe0f6'), (1, '#eef6fb')])
        pen.fill(rect(0, 900, 1920, 180), '#e8d6b0'); pen.fill(rect(0, 900, 1920, 34), '#f2a5b5'); pen.line(rect(0, 900, 1920, 34), 3)
        for k in range(14): pen.fill(oval(70 + k * 140, 950, 40, 18), ['#f6d978', '#9fd3f0', '#b9e0a5', '#d9b3f0'][k % 4])
        fig(pen, b, t)
    return dict(draw=draw, actors=[b], grounded=[b], floor=900.0)


@clip('bunny87_kneel_egg', 5.0, 'The mascot kneels to little Laurie and hands her a plastic egg; she takes it with both eyes on him')
def _c_kneel_egg():
    ppm = 330.0
    b = actor('bunny87', 1080, FLOOR, ppm, seed=6)
    l = actor('laurie87', 780, FLOOR, ppm, seed=7, expr='warm_smile')
    b.face(-0.55); l.face(0.55)
    egg = CH.PropTrack('egg', 0, 0, ppm / 100.0)
    egg.held(-1e9, b, -1)
    b.hold_prop('egg', -1, -1e9, None)
    b.reach(-1.0, None, -1, out=40.0, down=170.0, fwd=140.0, shape='grip', up=0.0, fade=0.01)
    b.kneel_down(0.2, 1.0, knees=0)
    tc = b.give(egg, 1.6, -1, l, 1, dur=1.4)
    l.look_at(0.0, (b, 'eyes'), t1=1.8, dur=0.3)
    l.look_at(2.6, (l, 'hand_l'), t1=3.6, dur=0.3)
    l.look_at(3.8, (b, 'eyes'), dur=0.3)
    b.look_at(0.4, (l, 'eyes'), dur=0.5)
    l.expr('kid_grin', 2.4, None, 0.4)
    def draw(pen, t):
        room(pen, '#9cc4dc', '#7aa86a')
        fig(pen, l, t); fig(pen, b, t)
    return dict(draw=draw, actors=[b, l], grounded=[b, l])


@clip('bunny87_walk_hand', 5.0, 'The newspaper photo pose (Laurie holding his paw), then they walk off toward the woods hand in paw')
def _c_walk_hand():
    ppm = 300.0
    b = actor('bunny87', 980, FLOOR, ppm, seed=6)
    l = actor('laurie87', 880, FLOOR + 14, ppm, seed=7, expr='warm_smile')     # side by side, a step nearer the camera
    b.face(-0.15); l.face(0.15)
    b.hold_prop('basket', 1)
    b.reach(-1.0, None, 1, out=40.0, down=230.0, fwd=150.0, shape='grip', up=0.0, fade=0.01)
    b.hold_hand(-1.0, -1, l, 1, t1=None, dur=0.3)
    b.walk(1.8, 5.0, 0.0, 520.0, facing=1.0, surface='porch')
    l.walk(1.8, 5.0, 0.0, 520.0, facing=1.0, surface='porch')
    l.look_at(2.2, (b, 'eyes'), t1=3.4, dur=0.4)
    l.look_at(0.0, (b, 'eyes'), t1=1.6, dur=0.3)
    def draw(pen, t):
        room(pen, '#9cc4dc', '#7aa86a')
        fig(pen, b, t); fig(pen, l, t)
    return dict(draw=draw, actors=[b, l], grounded=[l])


@clip('laurie87_sunrise', 5.0, 'Three days later at sunrise: Laurie walks out of the trees alone, dress spotless, a golden egg, humming')
def _c_sunrise():
    ppm = 320.0
    l = actor('laurie87', 600, 900, ppm, seed=8, expr='too_still')
    l.face(0.3)
    l.hold_prop('egg_gold', 1)
    l.reach(-1.0, None, 1, out=0.0, down=160.0, fwd=130.0, shape='grip', up=0.0, fade=0.01)
    l.walk(0.3, 4.4, 0.0, 600.0, facing=0.35, surface='porch')
    l.hum(0.5, None)
    def draw(pen, t):
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 1080, [(0, '#f2b27a'), (0.55, '#f6d6a0'), (1, '#c9b48a')])
        pen.glow(1500, 700, 420, '#fff2c0', 200)
        for k in range(26):
            x = k * 80 - 20; h = 420 + 140 * CH.hash01(k, 3)
            pen.fill(poly([(x - 70, 920), (x, 920 - h), (x + 70, 920)]), '#3a2a2a')
        pen.fill(rect(0, 900, 1920, 180), '#6a7a4a')
        fig(pen, l, t, dict(rim='#ffd9a0', rim_a=90, side=1, key=0.15))
    return dict(draw=draw, actors=[l], grounded=[l], floor=900.0)


@clip('bunny_mail_slot', 4.0, 'Outside the front door at 1:40: the Bunnyman crouched at the brass mail slot, a paw pushing the flap')
def _c_slot():
    ppm = 300.0
    b = actor('bunny', 900, FLOOR, ppm, seed=9)
    b.face(-1.45)
    d_ = door_pts(760, ppm)
    b.crouch(0.0, 0.8, None, 1.0)
    b.reach_to(0.6, -1, (d_['slot'][0] + 10, d_['slot'][1]), dur=0.9, contact='tips', shape='paw_flat', z=0.0)
    b.set(1.6, None, 0.8, h_tilt=-10.0, h_nod=0.25)
    def draw(pen, t):
        room(pen, '#1b2233', '#2a2a2e')
        door(pen, 760, FLOOR, ppm=ppm)
        fig(pen, b, t, dict(rim='#ffcf8f', rim_a=70, side=-1, key=-0.2))
    return dict(draw=draw, actors=[b], grounded=[b])


@clip('bunny_stairs_hatchet', 6.0, 'Footsteps on the stairs, slow; the old hatchet hanging from his paw knocks against every step (hatchet_thunk)')
def _c_stairs():
    ppm = 260.0
    rise, run = 52.0, 90.0
    b = actor('bunny', 520, FLOOR, ppm, seed=10)
    b.face(1.0)
    b.drag_hatchet(-1.0, None, side=-1)
    b.climb(0.4, 5.6, 0.0, rise, 6, run, hatchet=-1)
    def draw(pen, t):
        room(pen, '#1e2433', '#2a2420')
        stairs(pen, 560, 7, rise, run, FLOOR, 1200, 1)
        fig(pen, b, t, dict(rim='#9fb6ff', rim_a=60, side=1, key=-0.3))
    return dict(draw=draw, actors=[b], grounded=[])


@clip('bunny_dead_wide', 4.0, 'Sunrise: at the bottom of the stairs the Bunnyman lies on his back, not moving, the head of the suit half off')
def _c_dead_wide():
    ppm = 400.0
    b = actor('bunny', 820, FLOOR - 30, ppm, seed=11, expr='little_girl')
    b.face(1.0)
    b.lie(-1.0, 'up', arms='out')
    b.unmask(-1.0, 0.01)
    b.mama(1.2, 0.9)
    b.dead(2.4, 0.8)
    def draw(pen, t):
        room(pen, '#2a2a33', '#3a2f2a')
        fig(pen, b, t, dict(rim='#ffd9a0', rim_a=60, side=-1, key=0.05))
    return dict(draw=draw, actors=[b], grounded=[])


@clip('bunny_dead_face', 5.0, 'Close: the foam head tipped back, Dale (55, skin and bone) with the eyes of a terrified little girl: "Mama." Then still')
def _c_dead_face():
    b = CH.Acting('bunny', seed=11, height=700, expr='little_girl')
    b.set(-1.0, None, 0.01, unmask=1.0, h_turn=0.12)
    b.set(-1.0, None, 0.01, look_x=0.35, look_y=-0.6, _gaze=1.0)
    b.mama(1.4, 1.0)
    b.dead(3.0, 1.0)
    def draw(pen, t):
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 1080, [(0, '#3a3030'), (1, '#1d1a1c')])
        CH.draw_bust(pen, 'bunny', 960, 640, 0.75, b.at(t), t=t, light=dict(rim='#ffd9a0', rim_a=70, side=-1, key=0.05))
    return dict(draw=draw, actors=[b])


@clip('mom_doorway_smile', 4.5, 'Mom in the doorway: I don\'t know how long she\'s been there; she\'s smiling: "I told you not to look at the treeline."')
def _c_doorway():
    ppm = 360.0
    m = actor('mom', 960, FLOOR, ppm, seed=12, expr='too_still')
    m.face(0.0)
    m.talk([(1.6, 4.0, 'I told you not to look at the treeline')], env=None, words=None)
    m.head_tilt(0.4, 8.0, 1.6)
    def draw(pen, t):
        room(pen, '#2b3040', '#3a2f2a')
        doorway(pen, 960, FLOOR, 260, 640)
        fig(pen, m, t, dict(rim='#ffcf8f', rim_a=40, side=-1, key=-0.1))
        frame_over(pen, 960, FLOOR, 260, 640)
    return dict(draw=draw, actors=[m], grounded=[m])


@clip('mom_egg_mitts_barrel', 5.0, 'Every Easter: Mom carries the egg in oven mitts to the burn barrel and drops it in, unopened')
def _c_mitts():
    ppm = 330.0
    m = actor('mom', 560, 900, ppm, seed=13, expr='too_still')
    m.face(1.0)
    egg = CH.PropTrack('egg', 0, 0, ppm / 100.0)
    egg.held(-1e9, m, -1)
    m.hold_prop('egg', -1, -1e9, 3.4)
    m.set(-1.0, None, 0.01, hl_shape='oven', hr_shape='oven')
    m.reach(-1.0, None, -1, out=-34.0, down=180.0, fwd=210.0, shape='oven', up=0.0, fade=0.01)
    m.reach(-1.0, None, 1, out=-34.0, down=180.0, fwd=210.0, shape='oven', up=0.0, fade=0.01)
    m.walk(0.2, 2.4, 0.0, 640.0, facing=1.0, surface='porch')
    m.reach(2.6, None, -1, out=60.0, down=60.0, fwd=240.0, shape='oven', up=0.0, fade=0.6)
    egg.gone(3.4)
    def draw(pen, t):
        treeline(pen, 760)
        pen.fill(rect(0, 900, 1920, 180), '#1a2230')
        barrel(pen, 1420, 900, fire=0.8, t=t)
        fig(pen, m, t, dict(rim='#ff9a3a', rim_a=70, side=1, key=0.0))
    return dict(draw=draw, actors=[m], grounded=[m], floor=900.0)


@clip('mom_slot_hair_hum', 6.0, 'Mom closes the mail slot, smooths June\'s hair: "Bedtime, bunny." She\'s humming')
def _c_slot_hair():
    ppm = 360.0
    j = actor('june', 860, FLOOR, ppm, seed=14, expr='sad')
    m = actor('mom', 1240, FLOOR, ppm, seed=15, expr='too_still')
    j.face(-0.85); m.face(-0.9)
    j.kneel_down(-1.0, 0.01, knees=2)
    slot = door_pts(700, ppm)['slot']
    m.walk(0.0, 0.9, 0.0, -300.0, facing=-0.9, surface='inside')
    m.reach_to(1.0, -1, (slot[0] + 20, slot[1]), t1=2.0, dur=0.7, contact='tips', shape='flat', z=0.0, fade=0.6)
    m.smooth_hair(2.4, -1, j, n=2, stroke=0.8)
    j.look_at(2.4, (m, 'eyes'), dur=0.4)
    m.look_at(2.0, (j, 'eyes'), dur=0.4)
    m.talk([(3.6, 4.4, 'Bedtime, bunny')], env=None, words=None)
    m.hum(4.5, None)
    def draw(pen, t):
        room(pen, '#262c3a', '#3a2f2a')
        door(pen, 700, FLOOR, ppm=ppm)
        fig(pen, m, t); fig(pen, j, t)
        if 2.3 < t < 5.2:                                    # Mom's hand comes over June's hair (drawn in front of her)
            CH.draw_arm(pen, 'mom', -1, m.at(t), x=m.x0, y_feet=m.y0, height=m.height, t=t)
    return dict(draw=draw, actors=[m, j], grounded=[m])


@clip('mom_armchair_backdoor', 4.0, 'June and I sleep on the couch, with Mom in the armchair facing the back door: still, the smile, a slow blink')
def _c_armchair():
    ppm = 380.0
    seat = FLOOR - 0.44 * ppm
    m = actor('mom', 960, FLOOR, ppm, seed=16, expr='too_still', blink=0.05)
    m.face(-0.6)
    m.seated(seat, hands='arms')
    m.look_at(-1.0, (120, 560), dur=0.01, z=300.0)
    def draw(pen, t):
        room(pen, '#1d2230', '#2e2622')
        armchair(pen, 990, seat, 340)
        fig(pen, m, t, dict(rim='#9fb6ff', rim_a=50, side=-1, key=-0.3))
    return dict(draw=draw, actors=[m], grounded=[m])


@clip('mom_attic_corner', 4.0, 'From the dark corner of the attic, behind the boxes: "Back to bed, you two." I never saw her sitting there')
def _c_attic_corner():
    ppm = 340.0
    seat = FLOOR - 0.42 * ppm
    m = actor('mom', 1180, FLOOR, ppm, seed=17, expr='too_still', blink=0.03)
    m.face(-0.4)
    m.seated(seat, hands='knees')
    m.look_at(-1.0, (300, 620), dur=0.01, z=200.0)
    m.talk([(1.4, 2.8, 'Back to bed, you two')], env=None, words=None)
    def draw(pen, t):
        room(pen, '#141418', '#241e1a')
        pen.fill(rect(1050, seat, 260, FLOOR - seat), '#5a4630'); pen.line(rect(1050, seat, 260, FLOOR - seat), 3)
        fig(pen, m, t, dict(rim='#ffcf8f', rim_a=30, side=-1, key=-0.55))
        pen.fill(rect(0, 0, 1920, 1080), '#000000', 90)
    return dict(draw=draw, actors=[m], grounded=[m])


@clip('mom_scratched_smile', 4.0, 'The hallway is wrecked. Mom\'s arms are scratched to ribbons, and she\'s smiling: "It\'s sunrise, babies."')
def _c_scratched():
    ppm = 380.0
    m = actor('mom', 960, FLOOR, ppm, seed=18, expr='proud')
    m.face(-0.2)
    m.set(-1.0, None, 0.01, scratch=1.0, mess=0.6)
    m.hold_prop('key', 1, -1.0, None)
    m.reach(-1.0, None, 1, out=30.0, down=200.0, fwd=150.0, shape='grip', up=0.0, fade=0.01)
    m.talk([(1.0, 2.6, "It's sunrise, babies")], env=None, words=None)
    def draw(pen, t):
        room(pen, '#3a3330', '#3a2f2a')
        fig(pen, m, t, dict(rim='#ffd9a0', rim_a=80, side=-1, key=0.1))
    return dict(draw=draw, actors=[m], grounded=[m])


@clip('mom_kneel_dress_eyes', 6.0, 'Mom kneels in front of June with the little yellow dress and gently puts one hand over June\'s eyes; June counts')
def _c_kneel_eyes():
    ppm = 380.0
    j = actor('june_dress', 820, FLOOR, ppm, seed=19, expr='neutral')
    m = actor('mom', 1060, FLOOR, ppm, seed=20, expr='proud')
    j.face(0.5); m.face(-0.6)
    m.set(-1.0, None, 0.01, scratch=1.0, mess=0.5)
    m.kneel_down(-1.0, 0.01, knees=0)
    m.hold_prop('dress_tiny', 1, -1.0, None)
    m.reach(-1.0, None, 1, out=20.0, down=120.0, fwd=180.0, shape='grip', up=0.0, fade=0.01)
    m.look_at(-1.0, (j, 'eyes'), dur=0.01)
    m.hand_over(1.2, -1, j, 'eyes', dur=0.9)
    m.talk([(0.2, 1.1, 'Happy Easter, bunny')], env=None, words=None)
    j.look_at(-1.0, (m, 'eyes'), dur=0.01)
    j.eyes_shut(2.0, None, squeeze=0.0)
    j.talk([(3.0, 3.4, 'One'), (3.8, 4.2, 'Two'), (4.6, 5.0, 'Three')], env=None, words=None, intensity=0.6)
    def draw(pen, t):
        room(pen, '#3a3330', '#3a2f2a')
        fig(pen, j, t); fig(pen, m, t, dict(rim='#ffd9a0', rim_a=60, side=-1, key=0.1))
    return dict(draw=draw, actors=[m, j], grounded=[j])


@clip('narrator_swap', 5.0, 'I pull June\'s face out from under that hand and push my own face into it, eyes squeezed shut. "Six. Seven."')
def _c_swap():
    ppm = 380.0
    j = actor('june_dress', 820, FLOOR, ppm, seed=19)
    m = actor('mom', 1060, FLOOR, ppm, seed=20, expr='too_still')
    n = actor('narrator', 600, FLOOR, ppm, seed=21, expr='determined')
    j.face(0.5); m.face(-0.6); n.face(0.6)
    m.set(-1.0, None, 0.01, scratch=1.0, mess=0.5)
    m.kneel_down(-1.0, 0.01, knees=0)
    hand_pt = j.where(0.0, 'eyes')
    hand_pt = (hand_pt[0] + 6, hand_pt[1])
    m.reach_to(-1.0, -1, hand_pt, dur=0.01, contact='palm', shape='open', z=60.0)
    j.eyes_shut(-1.0, 1.4, squeeze=0.0)
    # the narrator grabs June's shoulder and pulls her back, June stumbles out of frame left
    n.reach_to(0.3, 1, (j, 'neck'), t1=1.4, dur=0.5, contact='palm', shape='grip', z=40.0)
    j.set(0.9, None, 0.5, dx=-330.0, turn=0.2, lean=-0.18)
    j.expr('fear', 1.2, None, 0.3)
    n.walk(1.2, 1.9, 0.0, 110.0, facing=0.6)
    n.head_to(1.6, hand_pt, 'eyes', dur=0.6, max_lean=0.3)
    n.eyes_shut(2.1, None, squeeze=1.0)
    n.talk([(3.0, 3.5, 'Six'), (3.9, 4.5, 'Seven')], env=None, words=None, intensity=0.7)
    def draw(pen, t):
        room(pen, '#3a3330', '#3a2f2a')
        fig(pen, j, t); fig(pen, n, t); fig(pen, m, t, dict(rim='#ffd9a0', rim_a=60, side=-1, key=0.1))
    return dict(draw=draw, actors=[m, j, n], grounded=[m])


@clip('narrator_new_holds_june', 5.0, 'I\'m on my knees in the hallway, looking at myself: sixteen, holding June\'s hand, smiling. My own face hums')
def _c_new():
    ppm = 380.0
    m = actor('mom', 700, FLOOR, ppm, seed=22, expr='terror')
    n = actor('narrator_new', 1100, FLOOR, ppm, seed=23, expr='wrong_smile')
    j = actor('june_dress', 1320, FLOOR, ppm, seed=24, expr='neutral')
    m.face(0.6); n.face(-0.4); j.face(-0.4)
    m.set(-1.0, None, 0.01, scratch=1.0, mess=0.7)
    m.kneel_down(-1.0, 0.01, knees=1)
    m.look_at(-1.0, (n, 'eyes'), dur=0.01)
    n.hold_hand(-1.0, 1, j, -1, dur=0.01)
    n.look_at(-1.0, (m, 'eyes'), dur=0.01)
    n.hum(0.8, None)
    j.look_at(-1.0, (m, 'eyes'), dur=0.01)
    def draw(pen, t):
        room(pen, '#3a3330', '#3a2f2a')
        fig(pen, m, t); fig(pen, j, t); fig(pen, n, t)
    return dict(draw=draw, actors=[m, n, j], grounded=[n, j])


@clip('mom_hosp_lap_whisper', 6.0, 'Holloway State Hospital: June climbs into my lap, puts her mouth against my ear and whispers, "I know it\'s you."')
def _c_hosp():
    ppm = 380.0
    seat = FLOOR - 0.46 * ppm
    m = actor('mom_hosp', 1000, FLOOR, ppm, seed=25, expr='haunted')
    j = actor('june', 700, FLOOR, ppm, seed=26, expr='neutral')
    m.face(-0.45); j.face(0.6)
    m.seated(seat, hands='lap')
    j.walk(0.0, 1.2, 0.0, 170.0, facing=0.6)
    j.set(1.3, None, 0.8, dy=-0.41 * ppm * 1.0, dx=270.0, sit=1.0, seat=60.0, turn=-0.1)
    j.head_to(2.6, (m, 'eye_l'), 'mouth', t1=5.6, dur=0.7, max_lean=0.3)
    j.talk([(3.4, 4.6, "I know it's you")], env=None, words=None, intensity=0.5)
    m.look_at(1.0, (j, 'eyes'), t1=3.0, dur=0.5)
    m.expr('fear', 3.6, None, 0.6)
    def draw(pen, t):
        room(pen, '#c9d6d4', '#8a9590')
        armchair(pen, 1030, seat, 330, c='#7a8a9a')
        fig(pen, m, t, dict(rim='#ffffff', rim_a=40, side=1, key=0.0)); fig(pen, j, t)
    return dict(draw=draw, actors=[m, j], grounded=[m])


@clip('june_window_wave', 4.0, 'June is at her window in her pajamas, waving at the treeline')
def _c_june_window():
    ppm = 380.0
    j = actor('june', 960, FLOOR, ppm, seed=27, expr='warm_smile')
    j.face(2.0)
    j.wave(0.4, 3.8, side=1, speed=0.9, height=1.1)
    def draw(pen, t):
        room(pen, '#5a4a6a', '#4a3a3a')
        window(pen, 960, 300, 380, 380, True, 0.0)
        fig(pen, j, t, dict(rim='#9fb6ff', rim_a=80, side=1, key=-0.2))
    return dict(draw=draw, actors=[j], grounded=[j])


@clip('june_whisper', 4.0, '"That\'s Mister Bunny," June whispers. "He waves at me every year. He\'s sad."')
def _c_june_whisper():
    j = CH.Acting('june', seed=28, height=700, expr='whisper')
    j.set(-1.0, None, 0.01, h_turn=0.25)
    j.talk([(0.3, 1.4, "That's Mister Bunny"), (1.7, 3.0, 'He waves at me every year'), (3.2, 3.8, "He's sad")], env=None, words=None, intensity=0.5)
    j.expr('sad', 3.1, None, 0.5)
    def draw(pen, t):
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 1080, [(0, '#1c2440'), (1, '#0e1220')])
        CH.draw_bust(pen, 'june', 960, 560, 0.8, j.at(t), t=t, light=dict(rim='#9fb6ff', rim_a=90, side=1, key=-0.2))
    return dict(draw=draw, actors=[j])


@clip('june_kneel_slot', 5.0, 'June kneels at the mail slot in her socks: "Laurie\'s my mom. She\'s right here."')
def _c_june_slot():
    ppm = 360.0
    j = actor('june', 760, FLOOR, ppm, seed=29, expr='neutral')
    j.face(-1.55)
    j.kneel_down(0.2, 0.9, knees=1)
    slot = door_pts(700, ppm)['slot']
    j.head_to(1.1, (slot[0] + 20, slot[1] + 8), 'mouth', dur=0.8, max_lean=0.3)
    j.reach_to(1.1, 1, (slot[0] - 30, slot[1]), dur=0.8, contact='tips', shape='flat', z=-60.0)
    j.talk([(2.2, 3.3, "Laurie's my mom"), (3.5, 4.6, "She's right here")], env=None, words=None, intensity=0.6)
    def draw(pen, t):
        room(pen, '#262c3a', '#3a2f2a')
        door(pen, 700, FLOOR, ppm=ppm)
        fig(pen, j, t)
    return dict(draw=draw, actors=[j], grounded=[j])


@clip('june_attic_diary', 5.0, 'June on the attic floor at the toy chest: the tiny dress, the diary in her lap; she smiles up at me')
def _c_attic():
    ppm = 380.0
    j = actor('june', 900, FLOOR, ppm, seed=30, expr='neutral')
    j.face(0.62)
    j.sit_floor(-1.0, None, 0.01)
    j.hold_prop('diary_open', -1, -1.0, None)
    j.reach(-1.0, None, -1, out=-30.0, down=230.0, fwd=210.0, shape='grip', up=0.0, fade=0.01)
    j.hold_prop('dress_tiny', 1, -1.0, None)
    j.reach(-1.0, None, 1, out=60.0, down=60.0, fwd=170.0, shape='grip', up=0.0, fade=0.01)
    j.look_at(-1.0, (900, 900), t1=1.6, dur=0.01)
    j.look_at(1.8, (1500, 300), dur=0.5, z=300.0)
    j.expr('warm_smile', 2.0, None, 0.5)
    j.talk([(2.8, 4.6, 'Mom says I can wear the yellow dress tomorrow')], env=None, words=None, intensity=0.6)
    def draw(pen, t):
        room(pen, '#3a2e26', '#4a3a2a')
        chest(pen, 600, FLOOR, 320, 190, lid=0.6)
        pen.glow(900, 500, 520, '#ffcf8f', 70)
        fig(pen, j, t, dict(rim='#ffcf8f', rim_a=70, side=-1, key=0.1))
    return dict(draw=draw, actors=[j], grounded=[])


@clip('narr_close_curtains', 4.0, 'If you hear the song, close all the curtains: the narrator pulls both curtains shut')
def _c_curtains():
    ppm = 380.0
    n = actor('narrator', 960, FLOOR, ppm, seed=31, expr='fear')
    n.face(2.0)
    L = lambda t: (960 - 200 + 170 * min(1.0, max(0.0, (t - 1.0) / 1.2)), 470)
    R = lambda t: (960 + 200 - 170 * min(1.0, max(0.0, (t - 1.0) / 1.2)), 470)
    n.reach_to(0.3, 1, L, t1=2.8, dur=0.7, contact='palm', shape='grip', z=-100.0)
    n.reach_to(0.35, -1, R, t1=2.8, dur=0.7, contact='palm', shape='grip', z=-100.0)
    def draw(pen, t):
        room(pen, '#2b3040', '#3a2f2a')
        window(pen, 960, 300, 330, 360, True, min(1.0, max(0.0, (t - 1.0) / 1.2)))
        fig(pen, n, t)
    return dict(draw=draw, actors=[n], grounded=[n])


@clip('narr_run', 3.0, 'I close the curtains downstairs, then run up to June\'s room: a real run (flight phase, pumping arms)')
def _c_run():
    ppm = 300.0
    n = actor('narrator', 260, FLOOR, ppm, seed=32, expr='fear')
    ev = n.run(0.3, 2.7, 0.0, 1400.0, surface='inside')
    def draw(pen, t):
        room(pen, '#2b3040', '#3a2f2a')
        fig(pen, n, t)
    return dict(draw=draw, actors=[n], grounded=[])


@clip('narr_peephole', 4.0, 'Through the peephole: the eye goes to the brass peephole, the other eye squeezed shut')
def _c_peep():
    ppm = 380.0
    n = actor('narrator', 800, FLOOR, ppm, seed=33, expr='nervous')
    n.face(-0.9)
    d_ = door_pts(760, ppm)
    n.walk(0.0, 0.8, 260.0, 0.0, facing=-0.9)
    n.turn(0.8, -1.7, 0.5)                                   # a door that faces the camera: look through it from behind
    n.head_to(1.1, (d_['peep'][0], d_['peep'][1]), 'eyes', dur=0.8, max_lean=0.2)
    n.reach_to(1.1, 1, (d_['peep'][0] - 60, d_['peep'][1] + 70), dur=0.7, contact='palm', shape='flat', z=-60.0)
    n.set(1.6, None, 0.2, lid_l=0.85)
    def draw(pen, t):
        room(pen, '#262c3a', '#3a2f2a')
        door(pen, 760, FLOOR, ppm=ppm)
        fig(pen, n, t)
    return dict(draw=draw, actors=[n], grounded=[n])


@clip('narr_egg_open', 6.5, 'I open the door, just a crack, pick the egg up off the doormat and open it: inside, rolling around, a gold ring')
def _c_egg_open():
    ppm = 380.0
    n = actor('narrator', 1060, FLOOR, ppm, seed=34, expr='nervous')
    n.face(-0.7)
    d_ = door_pts(760, ppm)
    egg = CH.PropTrack('egg', 900, FLOOR - 18, ppm / 100.0)
    n.reach_to(0.2, -1, d_['knob'], t1=1.0, dur=0.5, contact='palm', shape='grip', z=0.0)
    n.crouch(1.2, 1.0, 3.0, 0.7)
    n.look_at(1.0, egg, t1=4.0, dur=0.4)
    tc = n.pick_up(egg, 1.4, side=-1, dur=1.3, carry=None)
    n.turn(2.8, -0.12, 0.6)                                  # turn to us so the egg (and the ring) read
    ts, ev = n.open_egg(3.4, dur=1.8)
    n.look_at(4.2, lambda t: n.grip_point(t, -1, 'egg_bot_ring', post=False), dur=0.4)
    n.expr('shock', 4.6, None, 0.4)
    def draw(pen, t):
        room(pen, '#262c3a', '#3a2f2a')
        door(pen, 760, FLOOR, open_=0.12 * min(1.0, max(0.0, (t - 0.5) / 0.5)), ppm=ppm)
        pen.fill(rrect(760, FLOOR - 8, 260, 16, 4), '#6a4a3a')
        egg.draw(pen, t)
        fig(pen, n, t)
    return dict(draw=draw, actors=[n], grounded=[n])


@clip('narr_ring_stare', 4.0, 'My dad\'s wedding ring. Engraved on the inside: M and L, forever. (close: holding it up, staring)')
def _c_ring_stare():
    n = CH.Acting('narrator', seed=35, height=700, expr='shock')
    n.hold_prop('ring', 1, -1.0, None)
    # the ring pinched at the fingertips beside the face (never over it), the eyes on it; it drifts a little closer
    n.reach(-1.0, None, 1, out=55.0, down=-80.0, fwd=220.0, shape='grip', up=0.0, fade=0.01)
    n.reach(0.4, None, 1, out=45.0, down=-92.0, fwd=235.0, shape='grip', up=0.0, fade=2.4)
    n.set(-1.0, None, 0.01, h_nod=0.05, h_turn=-0.1, look_x=-0.42, look_y=0.05, _gaze=1.0)
    n.expr('cry', 2.4, None, 1.2)
    def draw(pen, t):
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 1080, [(0, '#2a2e3c'), (1, '#14161e')])
        CH.draw_bust(pen, 'narrator', 960, 520, 0.8, n.at(t), t=t, light=dict(rim='#ffcf8f', rim_a=60, side=-1, key=0.0))
    return dict(draw=draw, actors=[n])


@clip('narr_couch_wake', 5.0, 'At 2:47 I wake up on the couch; June\'s blanket is still warm; June is gone; Mom\'s chair is empty')
def _c_wake():
    ppm = 380.0
    seat = FLOOR - 0.42 * ppm
    n = actor('narrator', 900, FLOOR, ppm, seed=36, expr='sleep')
    n.face(0.35)
    n.seated(seat, hands='lap')
    n.set(-1.0, 1.0, 0.25, h_tilt=-16.0, lean=-0.1)
    n.expr('fear', 1.0, None, 0.25)
    n.set(1.0, None, 0.2, lid_l=0.0, lid_r=0.0)
    n.look_at(1.4, (1500, 700), t1=2.4, dur=0.3)
    n.look_at(2.6, (300, 700), t1=3.6, dur=0.35)
    n.look_at(3.8, (1100, 820), dur=0.3)
    def draw(pen, t):
        room(pen, '#1d2230', '#2e2622')
        couch(pen, 960, seat, 760)
        fig(pen, n, t, dict(rim='#9fb6ff', rim_a=50, side=1, key=-0.3))
    return dict(draw=draw, actors=[n], grounded=[n])


@clip('narr_tub_june', 5.0, 'We sit in the dark, in the empty bathtub, my hand over her mouth, staring at the door')
def _c_tub():
    ppm = 380.0
    tub_floor = FLOOR - 60
    n = actor('narrator', 1050, tub_floor, ppm, seed=37, expr='terror')
    j = actor('june', 880, tub_floor, ppm, seed=38, expr='fear')
    n.face(-0.4); j.face(-0.3)
    n.sit_floor(-1.0, None, 0.01); j.sit_floor(-1.0, None, 0.01)
    n.hand_over(0.2, -1, j, 'mouth', dur=0.6)
    n.reach_to(0.3, 1, (j, 'chest'), dur=0.6, contact='palm', shape='relaxed', z=80.0)
    n.look_at(-1.0, (200, 520), dur=0.01, z=200.0); j.look_at(-1.0, (200, 520), dur=0.01, z=200.0)
    def draw(pen, t):
        room(pen, '#141824', '#1c1f26')
        fig(pen, n, t, dict(rim='#ffd9a0', rim_a=40, side=-1, key=-0.5)); fig(pen, j, t, dict(rim='#ffd9a0', rim_a=40, side=-1, key=-0.5))
        tub(pen, 960, FLOOR + 90, 780, 340)
    return dict(draw=draw, actors=[n, j], grounded=[])


@clip('grandma_knock', 5.0, 'Grandma teaches the family knock with her knuckles on the kitchen table: two, three, two')
def _c_gran_knock():
    ppm = 380.0
    top = FLOOR - 0.74 * ppm
    g = actor('grandma', 760, FLOOR, ppm, seed=39, expr='warm_smile')
    k = actor('narrator_kid', 1150, FLOOR, ppm, seed=40, expr='neutral')
    g.face(0.5); k.face(-0.5)
    ev = g.knock_pattern(0.4, (2, 3, 2), side=-1, target=(900, top - 4), z=120.0, kind='table')
    g.look_at(-1.0, (k, 'eyes'), dur=0.01)
    k.look_at(-1.0, (900, top), t1=3.6, dur=0.01)
    k.look_at(3.8, (g, 'eyes'), dur=0.3)
    def draw(pen, t):
        room(pen, '#d8c8a8', '#8a6a4a')
        table(pen, 955, top, 300)
        fig(pen, g, t, WARM); fig(pen, k, t, WARM)
    return dict(draw=draw, actors=[g, k], grounded=[g, k])


@clip('grandma_porch_light', 3.0, 'Every Easter, Grandma left the porch light on all night: she reaches up and flips the switch')
def _c_gran_light():
    ppm = 380.0
    g = actor('grandma', 1000, FLOOR, ppm, seed=41, expr='warm_smile')
    g.face(-0.6)
    sw = (820, FLOOR - 0.95 * ppm * 1.0)
    g.reach_to(0.4, -1, sw, t1=1.8, dur=0.7, contact='tips', shape='point', z=0.0)
    def draw(pen, t):
        on = t > 1.15
        room(pen, '#c9b898' if on else '#5a5040', '#5a4a3a')
        pen.fill(rrect(sw[0] - 22, sw[1] - 36, 44, 72, 6), '#f2ecdc'); pen.line(rrect(sw[0] - 22, sw[1] - 36, 44, 72, 6), 3)
        pen.fill(rrect(sw[0] - 7, sw[1] - (18 if on else 4), 14, 22, 4), '#d8d0bc'); pen.line(rrect(sw[0] - 7, sw[1] - (18 if on else 4), 14, 22, 4), 2)
        fig(pen, g, t, WARM if on else None)
    return dict(draw=draw, actors=[g], grounded=[g])


@clip('dad_flashlight_treeline', 5.0, 'Last Easter, Dad walked out to the treeline with a flashlight, to talk to it')
def _c_dad():
    ppm = 300.0
    d = actor('dad', 500, 900, ppm, seed=42, expr='determined')
    d.face(1.0)
    d.hold_prop('maglite', 1, -1.0, None)
    d.reach(-1.0, None, 1, out=40.0, down=180.0, fwd=200.0, shape='grip', up=0.0, fade=0.01)
    d.set(-1.0, None, 0.01, torch_ang=96.0)
    d.walk(0.3, 4.6, 0.0, 700.0, facing=1.0, surface='porch')
    def draw(pen, t):
        treeline(pen, 760)
        pen.fill(rect(0, 900, 1920, 180), '#101624')
        fig(pen, d, t, dict(rim='#9fb6ff', rim_a=60, side=1, key=-0.3))
        lx, ly, ang = CH.torch_pos3(d, t, 1)
        CH.draw_torch_beam(pen, lx, ly, ang, 700.0, 11.0, 0.9, t)
    return dict(draw=draw, actors=[d], grounded=[d], floor=900.0)


@clip('cops_notes', 4.0, 'When the police came: one officer writes in his notebook, the other looks up at the house')
def _c_cops():
    ppm = 360.0
    c1 = actor('cop', 820, FLOOR, ppm, seed=43, expr='neutral')
    c2 = actor('cop2', 1120, FLOOR, ppm, seed=44, expr='sad')
    c1.face(0.4); c2.face(-0.3)
    c1.hold_prop('notebook', -1, -1.0, None); c1.reach(-1.0, None, -1, out=20.0, down=170.0, fwd=200.0, shape='grip', up=0.0, fade=0.01)
    c1.reach_to(-1.0, 1, lambda t: c1.grip_point(t, -1, 'notebook', post=False), dur=0.01, contact='tips', shape='point', z=200.0)
    c1.look_at(-1.0, lambda t: c1.grip_point(t, -1, 'notebook', post=False), dur=0.01)
    c2.look_at(0.5, (1500, 200), dur=0.6, z=400.0)
    def draw(pen, t):
        room(pen, '#2a3040', '#3a2f2a')
        fig(pen, c1, t, dict(rim='#ff3040', rim_a=70, side=-1)); fig(pen, c2, t, dict(rim='#4a7aff', rim_a=70, side=1))
    return dict(draw=draw, actors=[c1, c2], grounded=[c1, c2])


@clip('doctor_nurse', 4.0, 'The doctors here are very kind: the doctor with his clipboard, the nurse beside him')
def _c_doc():
    ppm = 360.0
    d = actor('doctor', 840, FLOOR, ppm, seed=45, expr='warm_smile')
    nr = actor('nurse', 1120, FLOOR, ppm, seed=46, expr='polite')
    d.face(0.3); nr.face(-0.3)
    d.hold_prop('clipboard', -1, -1.0, None); d.reach(-1.0, None, -1, out=10.0, down=160.0, fwd=190.0, shape='grip', up=0.0, fade=0.01)
    d.talk([(1.0, 2.4, 'How are we today, Laurie')], env=None, words=None, intensity=0.6)
    nr.look_at(-1.0, (d, 'eyes'), t1=2.6, dur=0.01)
    nr.look_at(2.8, (600, 600), dur=0.4)
    def draw(pen, t):
        room(pen, '#d6e2e0', '#9aa6a2')
        fig(pen, d, t); fig(pen, nr, t)
    return dict(draw=draw, actors=[d, nr], grounded=[d, nr])


@clip('mom_hum_bust', 4.0, 'All week, Mom\'s been humming that jingle (close: closed-mouth hum, the head sways on the beat)')
def _c_hum():
    m = CH.Acting('mom', seed=47, height=700, expr='too_still')
    m.set(-1.0, None, 0.01, h_turn=0.3)
    m.hum(0.2, None)
    def draw(pen, t):
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 1080, [(0, '#e8d6b8'), (1, '#b89a78')])
        CH.draw_bust(pen, 'mom', 960, 560, 0.8, m.at(t), t=t, light=WARM)
    return dict(draw=draw, actors=[m])


@clip('bunny_head_tilt_bust', 4.0, 'Black glass eyes that don\'t reflect anything: a slow head tilt under the moon')
def _c_bunny_bust():
    b = CH.Acting('bunny', seed=48, height=700)
    b.set(-1.0, None, 0.01, h_turn=0.1)
    b.head_tilt(0.6, -14.0, 2.4)
    def draw(pen, t):
        pen.linear(rect(0, 0, 1920, 1080), 0, 0, 0, 1080, [(0, '#0b1230'), (1, '#05070d')])
        CH.draw_bust(pen, 'bunny', 960, 600, 0.75, b.at(t), t=t, light=dict(rim='#9fb6ff', rim_a=110, side=1, key=-0.35))
    return dict(draw=draw, actors=[b])


@clip('crayon_drawing', 3.0, 'Something slides under the door: the crayon drawing (insert)')
def _c_crayon():
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#2a2420')
        u = min(1.0, t / 1.6); e = 1 - (1 - u) ** 3
        CH.draw_crayon_drawing(pen, 960 - 900 * (1 - e), 560, 520, t, angle=-6 + 4 * e)
        pen.fill(rect(0, 0, 1920, 120), '#5a3f2e')
    return dict(draw=draw, actors=[])


if __name__ == '__main__':
    main()
