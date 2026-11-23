"""cast_walls.py: the walls film's cast sheet and acting strips (characters_walls.py), written to W/cast/.

    cd "Vox test/Walls Video/film" && python3 tools/cast_walls.py [sheet] [strips [names...]]

sheet  -> _work/cast/cast_sheet.png: the line-up (to scale), Mr. Pell in five views, the doorway silhouettes (Dad / the
          figure, same build and tilt), face busts, the crack-eye insert, the empty mask in Reyes' hand.
strips -> _work/cast/strip_<name>.jpg: 8 frames (960x540 each, shown at 480x270) of one scripted action on a flat
          stand-in set (the real sets are sets_walls.py's), plus a printed contact report (reach misses, feet).
"""
import os, sys, math
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'tools'))
import numpy as np
import cv2
import skia
from engine.core import set_render_size, Pen, CFG, rect, rrect, oval, poly, smooth, text, mix
import characters as CH
from cast_clips import room, door, ppm_for, actor, fig, _strip

OUT = os.path.join(HERE, '_work', 'cast')
FLOOR = 940.0
NIGHT = dict(rim='#8fa6e8', rim_a=70, side=1, key=-0.35)
WARM = dict(rim='#ffcf8f', rim_a=55, side=-1, key=0.12)


def _surface(w, h):
    set_render_size(w, h)
    s = skia.Surface(CFG.rw, CFG.rh)
    return s, s.getCanvas()


def _grab(surf):
    return surf.makeImageSnapshot().toarray()[:, :, :3].copy()


def bed(pen, x0, x1, top, c='#5a6a8a', y=FLOOR):
    pen.fill(rect(x0, top, x1 - x0, y - top), mix(c, '#000000', 0.45)); pen.line(rect(x0, top, x1 - x0, y - top), 2)
    pen.fill(rrect(x0 - 10, top - 18, x1 - x0 + 20, 36, 12), '#d8d4cc'); pen.line(rrect(x0 - 10, top - 18, x1 - x0 + 20, 36, 12), 2)


# ------------------------------------------------------------------------------------------------ the sheet
def sheet():
    W, H = 1920, 1440
    surf, cv = _surface(W, H)
    cv.clear(skia.Color(32, 34, 44)); cv.save(); cv.scale(CFG.k, CFG.k)
    pen = Pen(cv)
    pen.fill(rect(0, 0, W, 520), '#3a3f4e'); pen.fill(rect(0, 520, W, 6), '#22242c')
    # line-up to scale (ppm 230: Dad / Pell 1.87 m = 430 px), 3/4 left
    ppm = 230.0
    ids = ['sam', 'theo', 'mom', 'dad', 'pell', 'pell_bare', 'dabrowski', 'reyes', 'officer_w', 'sam_pj', 'mom_pj', 'dad_pj']
    for k, who in enumerate(ids):
        a = CH.Acting(who, seed=k + 1, height=CH.height_px(who, ppm)).place(80 + k * 150, 505)
        if who == 'dabrowski': a.offer_pie(-1e9, facing=1)
        P = a.at(1.3); P.turn += -0.28 if k % 2 else 0.28
        CH.draw(pen, who, 80 + k * 150, 505, a.height, P, t=1.3, light=WARM)
        text(pen.cv, who, 80 + k * 150, 530, 600, 15, '#d8dce6')
    # Pell in five views (front, 3/4, profile, 3/4 back, back) at night
    for k, yaw in enumerate((0.0, 0.5, 1.0, 1.5, 2.0)):
        a = CH.Acting('pell', seed=7, height=440); P = a.at(2.0); P.turn = yaw
        CH.draw(pen, 'pell', 90 + k * 120, 1040, 440, P, t=2.0, light=NIGHT)
    # doorway silhouettes: Dad (bare-headed) and the figure, both with WALLS_TILT, backlit
    for k, who in enumerate(('dad_pj', 'pell')):
        x = 760 + k * 210
        pen.fill(rect(x - 95, 560, 190, 480), '#c9b98e')
        a = CH.Acting(who, seed=3, height=CH.height_px(who, 230.0)); a.doorway(0.0)
        P = a.at(2.0)
        sc = skia.Surface(CFG.rw, CFG.rh); c2 = sc.getCanvas(); c2.clear(skia.Color(0, 0, 0, 0)); c2.scale(CFG.k, CFG.k)
        CH.draw(Pen(c2), who, x, 1040, a.height, P, t=2.0)
        img = sc.makeImageSnapshot()
        p = skia.Paint(ColorFilter=skia.ColorFilters.Blend(skia.Color(14, 12, 16), skia.BlendMode.kSrcIn))
        cv.restore(); cv.drawImage(img, 0, 0, skia.SamplingOptions(), p); cv.save(); cv.scale(CFG.k, CFG.k)
        text(pen.cv, ('Dad' if k == 0 else 'the figure'), x, 1066, 600, 15, '#d8dce6')
    # busts row (y 1080..1440): Pell masked (3/4, tilted + whisper), Pell bare, Sam, Theo, Mom, Dad, Mrs. D, Reyes
    pen.fill(rect(0, 1080, W, 360), '#2a2d38')
    busts = [('pell', 0.25, NIGHT, 0.0), ('pell', -0.55, NIGHT, 1.0), ('pell_bare', 0.3, None, 0.0), ('sam', 0.25, None, 0.0),
             ('theo', -0.25, None, 0.0), ('mom', 0.25, None, 0.0), ('dad', -0.2, None, 0.0), ('dabrowski', 0.2, None, 0.0),
             ('reyes', -0.25, None, 0.0)]
    for k, (who, yaw, lt, tl) in enumerate(busts):
        a = CH.Acting(who, seed=k, height=600); P = a.at(3.0); P.h_turn = yaw
        if tl: P.h_tilt = 21.0; P.m_open = 0.5
        CH.draw_bust(pen, who, 110 + k * 212, 1230, 0.17, P, t=3.0, light=lt)
    # the crack-eye insert (clipped to the crack) and the empty mask as Reyes holds it
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(1180 * CFG.k / CFG.k, 600, 560, 70)); cv.clear(skia.Color(18, 14, 12))
    P = CH.Pose(); P.h_turn = 0.2
    CH.draw_head_at(pen, 'pell', P, 1450, 635, 2.4, 'eye_l', t=0.0, light=NIGHT)
    cv.restore()
    text(pen.cv, 'eye at the crack (insert)', 1460, 700, 600, 15, '#d8dce6')
    CH.draw_prop3(pen, 'hound_mask', 1820, 760, 6.0)
    text(pen.cv, 'mask in her hand', 1820, 1050, 600, 15, '#d8dce6')
    cv.restore()
    os.makedirs(OUT, exist_ok=True)
    img = _grab(surf)
    cv2.imwrite(os.path.join(OUT, 'cast_sheet.png'), img)
    return img


# ------------------------------------------------------------------------------------------------ strips
STRIPS = {}


def strip(name, dur):
    def deco(f):
        STRIPS[name] = (f, dur); return f
    return deco


@strip('doorway_back', 5.0)
def _s_doorway():
    a = actor('pell', 960, FLOOR, 330.0, seed=2); a.doorway(0.2, None)
    a.back_away(2.0, 4.8, steps=4)
    def draw(pen, t):
        room(pen, '#1c2232', '#2a2630')
        pen.fill(rect(820, 300, 280, 640), '#0e1018')
        u = CH.ease_in_out(CH.prog(t, 2.0, 4.8))
        h = a.height * (1 - 0.42 * u); y = FLOOR - 120 * u
        CH.draw(pen, 'pell', 960, y, h, a.at(t), light=NIGHT, t=t)
        pen.fill(rect(800, 280, 20, 660), '#5a4a3a'); pen.fill(rect(1100, 280, 20, 660), '#5a4a3a'); pen.fill(rect(800, 280, 320, 22), '#5a4a3a')
    return dict(draw=draw, actors=[a])


@strip('tuck_shush', 6.0)
def _s_tuck():
    ppm = 300.0
    th = actor('theo', 1240, 742, ppm, seed=3, expr='sleep'); th.lie(-1e9, face='up', arms='side')
    p = actor('pell', 640, FLOOR, ppm, seed=4); p.set(-1e9, None, 0.1, turn=0.55)
    p.tuck_blanket(0.2, (830, 735), (1010, 735), dur=2.6, t1=3.6)
    p.look_at(3.2, (120, 470), dur=0.7)
    p.shush(3.9, None, side=1)
    p.look_at(0.4, (th, 'eyes'), t1=3.0, dur=0.6)
    def draw(pen, t):
        room(pen, '#1c2232', '#2a2630')
        bed(pen, 780, 1560, 760)
        fig(pen, th, t, NIGHT)
        pen.fill(rect(790, 735, 760, 26), '#5a7ab0'); pen.line(rect(790, 735, 760, 26), 2)
        fig(pen, p, t, NIGHT)
    return dict(draw=draw, actors=[p, th], grounded=[])


@strip('crawl', 4.0)
def _s_crawl():
    a = actor('pell', 0, 900, 300.0, seed=5); a.crawl(0.3, 3.7, 250, 1500)
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#2c2420')
        pen.fill(rect(0, 560, 1920, 340), '#14100e')
        for x in range(60, 1920, 240): pen.fill(rect(x, 560, 30, 340), '#3a2e24')
        pen.fill(rect(0, 900, 1920, 180), '#3a2e24')
        fig(pen, a, t, NIGHT)
    return dict(draw=draw, actors=[a])


@strip('closet_panel', 3.2)
def _s_panel():
    a = actor('pell', 880, FLOOR, 330.0, seed=6); a.set(-1e9, None, 0.1, turn=1.55)
    pdx = a.slide_panel(0.4, 1, (1190, 560), -170.0, dur=1.8)
    def draw(pen, t):
        room(pen, '#1c2232', '#2a2630')
        pen.fill(rect(1080, 260, 500, 680), '#0a0a0e')
        pen.fill(rect(1080 + pdx(t), 260, 500, 680), '#6a5a48'); pen.line(rect(1080 + pdx(t), 260, 500, 680), 3)
        fig(pen, a, t, NIGHT)
    return dict(draw=draw, actors=[a])


@strip('carry_hush', 4.0)
def _s_carry():
    ppm = 330.0
    s = actor('sam_pj', 0, FLOOR, ppm, seed=7, expr='hush_fear'); th = actor('theo', 0, FLOOR, ppm, seed=8, expr='sleepy')
    s.walk(0.3, 3.8, 500, 1300); s.carry_hush(0.0, th)
    def draw(pen, t):
        room(pen, '#1c2232', '#2a2630')
        CH.draw_carry_walls(pen, s, th, t, light=NIGHT)
    return dict(draw=draw, actors=[s, th], grounded=[s])


@strip('shake_awake', 4.0)
def _s_shake():
    ppm = 300.0
    d = actor('dad_pj', 1150, 745, ppm, seed=9, expr='sleep'); d.lie(-1e9, face='up', arms='side')
    d.expr('shock', 2.4, None, 0.3)
    s = actor('sam_pj', 640, FLOOR, ppm, seed=10, expr='hush_fear'); s.set(-1e9, None, 0.1, turn=0.6)
    s.shake_awake(0.4, 2.4, d)
    s.look_at(0.2, (d, 'eyes'), dur=0.4)
    def draw(pen, t):
        room(pen, '#1c2232', '#2a2630')
        bed(pen, 760, 1700, 770)
        fig(pen, d, t, NIGHT)
        pen.fill(rect(770, 760, 900, 26), '#6a5a8a'); pen.line(rect(770, 760, 900, 26), 2)
        fig(pen, s, t, NIGHT)
    return dict(draw=draw, actors=[s, d], grounded=[s])


@strip('phone_sing', 5.0)
def _s_phone():
    ppm = 330.0
    m = actor('mom_pj', 760, FLOOR, ppm, seed=11, expr='terrified_call'); m.set(-1e9, None, 0.1, turn=0.35)
    th = actor('theo', 1120, FLOOR, ppm, seed=12); th.set(-1e9, None, 0.1, turn=-0.4)
    m.phone_to_ear(0.2, 2.2, side=1)
    m.reach_to(2.6, 1, (th, 'mouth'), dur=0.6, z=120.0, contact='grip', shape='grip', prop='cell')
    m.hold_prop('cell', 1, 2.3, None)
    th.look_at(2.6, (m, 'hand_l'), dur=0.4)
    th.sing([(3.1, 4.9, 'Fourteen Larkspur Lane Maple Falls')], env=None)
    m.look_at(2.4, (th, 'eyes'), dur=0.5)
    def draw(pen, t):
        room(pen, '#262a3a', '#2a2630')
        fig(pen, th, t, NIGHT); fig(pen, m, t, NIGHT)
    return dict(draw=draw, actors=[m, th], grounded=[m, th])


@strip('note_laugh_sigh', 5.6)
def _s_note():
    d = actor('dad', 960, FLOOR, 330.0, seed=13); d.set(-1e9, None, 0.1, turn=0.3)
    d.read_note(0.2, 3.4, side=-1)
    d.laugh(2.0, 1.4)
    d.sigh(3.8, 1.7)
    d.walls_tilt(0.6, 1.8, 0.5)
    def draw(pen, t):
        room(pen, '#6a6050', '#4a3a2e')
        fig(pen, d, t, WARM)
    return dict(draw=draw, actors=[d], grounded=[d])


@strip('pie', 3.0)
def _s_pie():
    m = actor('dabrowski', 820, FLOOR, 330.0, seed=14, expr='kind_smile'); m.set(-1e9, None, 0.1, turn=0.35)
    m.offer_pie(0.5, 1.0, facing=1)
    m.talk([(1.6, 2.8, 'Your attic light is on every night')], env=None)
    mo = actor('mom', 1260, FLOOR, 330.0, seed=15, expr='polite'); mo.set(-1e9, None, 0.1, turn=-0.4)
    def draw(pen, t):
        room(pen, '#7a8a96', '#5a5048')
        fig(pen, mo, t, WARM); fig(pen, m, t, WARM)
    return dict(draw=draw, actors=[m, mo], grounded=[m, mo])


@strip('unmask', 3.6)
def _s_unmask():
    p = actor('pell', 1040, FLOOR, 330.0, seed=16); p.set(-1e9, None, 0.1, turn=-0.45)
    r = actor('reyes', 760, FLOOR, 330.0, seed=17, expr='calm_firm'); r.set(-1e9, None, 0.1, turn=0.5)
    r.lift_mask(0.4, p, dur=1.6)
    r.look_at(0.0, (p, 'eyes'), dur=0.4)
    p.expr('exhausted', 2.0, None, 0.4)
    def draw(pen, t):
        room(pen, '#2a3040', '#2a2630')
        fig(pen, p, t, NIGHT); fig(pen, r, t, NIGHT)
    return dict(draw=draw, actors=[p, r], grounded=[p, r])


@strip('curb_cuffs', 3.0)
def _s_curb():
    p = actor('pell', 960, FLOOR, 330.0, seed=18, expr='lonely'); p.set(-1e9, None, 0.1, turn=0.3)
    p.seated(FLOOR - 50, hands=None)
    p.cuffed()
    p.look_at(1.0, (400, 120), dur=1.0)
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, FLOOR - 50), '#1c2232'); pen.fill(rect(0, FLOOR - 50, 1920, 50), '#8a8a86')
        pen.fill(rect(0, FLOOR, 1920, 140), '#2e2e32')
        fig(pen, p, t, NIGHT)
    return dict(draw=draw, actors=[p])


@strip('switch', 2.4)
def _s_switch():
    s = actor('sam_pj', 900, FLOOR, 330.0, seed=19, expr='hush_fear'); s.set(-1e9, None, 0.1, turn=0.6)
    tf = s.flip_switch(0.4, 1, (1150, 560))
    s.look_at(0.2, (1150, 560), t1=1.3, dur=0.4); s.look_at(1.4, (900, 120), dur=0.5)
    def draw(pen, t):
        room(pen, '#262a3a', '#2a2630')
        pen.fill(rrect(1135, 530, 30, 56, 4), '#e8e4da'); pen.line(rrect(1135, 530, 30, 56, 4), 2)
        pen.fill(rect(1144, 548 if t < tf else 556, 12, 12), '#9a968e')
        fig(pen, s, t, NIGHT)
    return dict(draw=draw, actors=[s], grounded=[s])


def render_strip(name):
    f, dur = STRIPS[name]
    S = f()
    surf, cv = _surface(960, 540)
    ts = list(np.linspace(0.0, dur - 1.0 / 60, 8))
    frames = []
    for t in ts:
        cv.save(); cv.clear(skia.Color(20, 22, 30)); cv.scale(CFG.k, CFG.k)
        S['draw'](Pen(cv), t)
        cv.restore()
        frames.append(_grab(surf))
    _strip(frames, os.path.join(OUT, 'strip_%s.jpg' % name), times=ts)
    miss = max([m[-1] for a in S.get('actors', []) for m in getattr(a, 'misses', [])], default=0.0)
    feet = [round(max(a.foot_gap(t) for t in ts), 1) for a in S.get('grounded', [])]
    print('%-16s reach miss max %.1f px, foot gaps %s' % (name, miss, feet))


if __name__ == '__main__':
    args = sys.argv[1:] or ['sheet', 'strips']
    os.makedirs(OUT, exist_ok=True)
    if 'sheet' in args: sheet(); print('sheet ->', os.path.join(OUT, 'cast_sheet.png'))
    if 'strips' in args:
        names = [a for a in args if a in STRIPS] or list(STRIPS)
        for n in names: render_strip(n)
