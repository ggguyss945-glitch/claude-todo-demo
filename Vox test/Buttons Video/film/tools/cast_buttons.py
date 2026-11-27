"""cast_buttons.py: the buttons film's cast sheet, 640-px faces and acting strips (characters_buttons.py), to W/cast/.

    cd "Vox test/Buttons Video/film" && python3 tools/cast_buttons.py [sheet] [faces] [strips [names...]]

sheet  -> _work/cast/cast_sheet.png: the line-up to scale; the three forms of the Blank side by side (with Mom); form 3
          under a ceiling (full, unfolding, collapsing, the flat cardigan); Owen faded; Mom pencil grey; the red coat;
          the car-window arm; face busts (glare, green eyes, two black circles, sunglasses lowered, default head).
faces  -> _work/cast/faces_640.jpg: four 640x360 close-ups (the size faces must read at).
strips -> _work/cast/strips_<group>.jpg: 8 frames (320x180 each) per scripted action, 3 actions per image, on flat
          stand-in sets (the real ones are sets_buttons'), plus a printed contact report (reach misses, foot gaps).
"""
import os, sys, math
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'tools'))
import numpy as np
import cv2
import skia
from engine.core import set_render_size, Pen, CFG, rect, rrect, oval, poly, smooth, text, mix
import characters as CH
from cast_clips import room, actor, fig

OUT = os.path.join(HERE, '_work', 'cast')
FLOOR = 940.0
NIGHT = dict(rim='#8fa6e8', rim_a=70, side=1, key=-0.35)
WARM = dict(rim='#ffcf8f', rim_a=55, side=-1, key=0.12)
LAP = dict(under='#bcd2ff', under_a=90)


def _surface(w, h):
    set_render_size(w, h)
    s = skia.Surface(CFG.rw, CFG.rh)
    return s, s.getCanvas()


def _grab(surf):
    return surf.makeImageSnapshot().toarray()[:, :, :3].copy()


def lbl(pen, s, x, y, c='#d8dce6', size=14):
    text(pen.cv, s, x, y, 600, size, c)


# ------------------------------------------------------------------------------------------------ the sheet
def sheet():
    W, H = 1920, 1440
    surf, cv = _surface(W, H)
    cv.clear(skia.Color(32, 34, 44)); cv.save(); cv.scale(CFG.k, CFG.k)
    pen = Pen(cv)
    pen.fill(rect(0, 0, W, 520), '#3a3f4e'); pen.fill(rect(0, 505, W, 15), '#2a2d38')
    ppm = 230.0
    ids = [('owen', 0), ('owen_coat', 0), ('owen_pj', 0), ('son', 0), ('mom', 0), ('blank1', 0), ('blank1_shades', 0),
           ('blank2', 0.0), ('blank2', 0.12), ('dunn', 0), ('mensah', 0), ('narrator_b', 0)]
    for k, (who, tall) in enumerate(ids):
        x = 75 + k * 148
        a = CH.Acting(who, seed=k + 1, height=CH.height_px(who, ppm, tall=tall), expr='too_sweet' if who == 'blank2' else 'neutral').place(x, 505)
        if who == 'dunn': a.hold_sign(-1e9, None, side=-1)
        if who == 'mensah': a.take_notes(0.0, 9.0)
        if who == 'owen': a.typing(0.0, 9.0, lambda t: (x, 505 - a.height * 0.52))
        P = a.at(1.3); P.turn += -0.25 if k % 2 else 0.25
        if who == 'owen': P.turn = 0.0
        CH.draw(pen, who, x, 505, a.height, P, t=1.3, light=WARM)
        if who == 'owen': CH.draw_prop3(pen, 'tab_back', x, 505 - a.height * 0.5, a.height / 145.0)
        lbl(pen, who + (' +12%%' if tall else ''), x, 500, '#d8dce6', 13)
    # row 2: Mom and the three forms, form 3 under a ceiling; looks
    fl2 = 1060.0; ppm2 = 175.0; ceil = fl2 - 2.45 * ppm2
    pen.fill(rect(0, 520, 1210, 560), '#2e3240'); pen.fill(rect(0, ceil - 14, 1210, 14), '#565c6c')
    for k, (who, lab) in enumerate((('mom', 'Mom (real)'), ('blank1', 'form 1'), ('blank2', 'form 2'))):
        x = 90 + k * 150
        a = CH.Acting(who, seed=4, height=CH.height_px(who, ppm2, tall=0.1 if k == 2 else 0.0),
                      expr='too_sweet' if k == 2 else ('polite' if k == 1 else 'busy')).place(x, fl2)
        P = a.at(2.0); P.turn = 0.3
        CH.draw(pen, who, x, fl2, a.height, P, t=2.0, light=WARM)
        lbl(pen, lab, x, fl2 + 14)
    b = CH.Acting('blank3', seed=5, height=fl2 - ceil, expr='too_wide').place(560, fl2)
    CH.draw(pen, 'blank3', 560, fl2, b.height, b.at(2.0), t=2.0, light=NIGHT); lbl(pen, 'form 3', 560, fl2 + 14)
    for k, (un, co, lab) in enumerate(((0.45, 0.0, 'unfold 0.45'), (0.8, 0.0, 'unfold 0.8'), (1.0, 0.55, 'collapse 0.55'))):
        x = 800 + k * 150
        b2 = CH.Acting('blank3', seed=5, height=fl2 - ceil, expr='too_wide').place(x, fl2)
        P = b2.at(2.0); P.b3_unfold = un; P.b3_collapse = co
        CH.draw(pen, 'blank3', x, fl2, b2.height, P, t=2.0, light=NIGHT); lbl(pen, lab, x, fl2 + 14)
    CH.draw_flat_cardigan(pen, 1140, fl2, 120); lbl(pen, 'empty', 1140, fl2 + 14)
    # looks: Owen faded / normal, Mom pencil grey
    pen.fill(rect(1210, 520, 710, 560), '#3a3f4e')
    for k, (who, kw, lab) in enumerate((('owen', {}, 'Owen'), ('owen', dict(faded=1.0), 'faded 1.0'),
                                         ('mom', dict(pgrey=1.0), 'pencil grey'))):
        x = 1270 + k * 110
        a = CH.Acting(who, seed=6, height=CH.height_px(who, ppm2)).place(x, fl2)
        P = a.at(2.0); P.turn = 0.2
        for kk, v in kw.items(): setattr(P, kk, v)
        CH.draw(pen, who, x, fl2, a.height, P, t=2.0, light=WARM); lbl(pen, lab, x, fl2 + 14)
    # the coat (held open, empty; six closed, top held out) and the car-window arm
    CH.draw_red_coat(pen, 1640, 600, 150, buttons=0, open_=1.0, full=0.0); lbl(pen, 'coat held open', 1640, 770)
    CH.draw_red_coat(pen, 1820, 600, 150, buttons=6, open_=0.4, full=0.0, top_out=1.0, top_to=(1860, 650)); lbl(pen, 'six closed', 1820, 770)
    pen.fill(rrect(1560, 820, 200, 120, 14), '#8d949e'); pen.fill(rrect(1580, 835, 120, 60, 8), '#22262e')
    CH.draw_long_arm(pen, (1650, 880), (1880, 1000), 1.0, 1.0, 1.0)
    lbl(pen, 'car-window arm', 1700, 1050)
    # busts
    pen.fill(rect(0, 1080, W, 360), '#2a2d38')
    busts = [('owen', {}, 'owen'), ('owen', dict(faded=1.0), 'faded'), ('son', {}, 'son'), ('mom', {}, 'glare'),
             ('mom', dict(specs=0.0, hs_off=1.0), 'green'), ('mom', dict(circles=1.0), 'circles'),
             ('blank1_shades', dict(shades_dn=1.0), 'shades down'), ('blank2', {}, 'form 2'),
             ('blank2', dict(default_head=1.0), 'default head'), ('blank3', {}, 'form 3 face')]
    for k, (who, kw, lab) in enumerate(busts):
        a = CH.Acting(who, seed=k, height=600, expr='too_sweet' if who == 'blank2' else ('too_wide' if who == 'blank3' else 'neutral'))
        P = a.at(3.0); P.h_turn = 0.22 if k % 2 else -0.22
        for kk, v in kw.items(): setattr(P, kk, v)
        CH.draw_bust(pen, who, 100 + k * 192, 1225, 0.16, P, t=3.0)
        lbl(pen, lab, 100 + k * 192, 1425)
    for k, (nm, sz) in enumerate((('music_box', 9.0), ('headset', 5.0), ('tab', 4.0), ('button', 14.0))):
        CH.draw_prop3(pen, nm, 1260 + k * 95, 600 if nm != 'headset' else 545, sz)
    cv.restore()
    os.makedirs(OUT, exist_ok=True)
    img = _grab(surf)
    cv2.imwrite(os.path.join(OUT, 'cast_sheet.png'), img)
    return img


def faces640():
    shots = [[('mom', 320, 250, 0.42, dict(h_turn=0.25), 'busy', None, '#5a4e46')],
             [('mom', 320, 250, 0.42, dict(h_turn=-0.15, specs=0.0, hs_off=1.0), 'listening_soft', None, '#5a4e46')],
             [('blank2', 320, 250, 0.42, dict(h_turn=0.2), 'too_sweet', NIGHT, '#1e2230')],
             [('owen', 180, 260, 0.36, dict(h_turn=0.2), 'quiet_sure', None, '#46505e'),
              ('son', 470, 260, 0.36, dict(h_turn=-0.2), 'neutral', None, None)]]
    tiles = []
    for shot in shots:
        surf, cv = _surface(640, 360)
        cv.save(); cv.scale(CFG.k, CFG.k); pen = Pen(cv)
        for who, x, y, sc, kw, ex, lt, bg in shot:
            if bg: pen.fill(rect(0, 0, 1920, 1080), bg)
            a = CH.Acting(who, seed=5, height=600, expr=ex)
            P = a.at(2.0)
            for k, v in kw.items(): setattr(P, k, v)
            CH.draw_bust(pen, who, x * 3, y * 3, sc * 3 / 3.0 * 3, P, t=2.0, light=lt)
        cv.restore()
        tiles.append(_grab(surf))
    img = np.vstack([np.hstack(tiles[:2]), np.hstack(tiles[2:])])
    cv2.imwrite(os.path.join(OUT, 'faces_640.jpg'), img, [cv2.IMWRITE_JPEG_QUALITY, 90])


# ------------------------------------------------------------------------------------------------ strips
STRIPS = {}
GROUPS = {'mom': ['mom_type_finger', 'mom_photo_run', 'mom_climax'], 'owen': ['owen_tablet', 'owen_board_rise', 'dunn_owen'],
          'blank_a': ['blank2_street', 'blank3_unfold', 'blank3_coat'], 'blank_b': ['blank3_lunge', 'car_arm', 'son_mensah'],
          'misc': ['mom_wind_box', 'blank1_laptop', 'blank2_sill', 'sting_hands']}


def strip(name, dur):
    def deco(f):
        STRIPS[name] = (f, dur); return f
    return deco


def table(pen, x0, x1, top, c='#7a5a40'):
    pen.fill(rect(x0, top, x1 - x0, 18), c); pen.line(rect(x0, top, x1 - x0, 18), 2)
    for x in (x0 + 20, x1 - 40): pen.fill(rect(x, top + 18, 20, FLOOR - top - 18), mix(c, '#000000', 0.3))


def laptop(pen, x, top, face=1):
    pen.fill(poly([(x - 70, top), (x + 70, top), (x + 64, top - 8), (x - 64, top - 8)]), '#9aa0aa'); pen.line(rect(x - 70, top - 8, 140, 8), 2)
    sx = x + face * 60
    pen.fill(poly([(sx, top - 8), (sx + face * 14, top - 118), (sx + face * 4, top - 120), (sx - face * 10, top - 8)]), '#2a2e36')


@strip('mom_type_finger', 5.0)
def _s_type():
    ppm = 330.0; seat = FLOOR - 0.46 * ppm; top = FLOOR - 0.76 * ppm
    m = actor('mom', 700, FLOOR, ppm, seed=3, expr='busy'); m.set(-1e9, None, 0.0, turn=0.55)
    m.seated(seat)
    kb = (930, top - 10)
    m.typing(0.2, 2.1, kb)
    m.one_finger(2.3, 3.6, side=-1); m.typing(2.3, 3.6, kb, side=1)
    m.typing(3.8, 5.0, kb)
    m.look_at(0.0, (1010, top - 70), dur=0.3)
    m.expr('puzzled', 3.9, None); m.lean_in(3.9, dur=1.0, amount=0.5)
    def draw(pen, t):
        room(pen, '#4a4038', '#5a4a3a')
        pen.fill(rect(560, seat, 180, 22), '#6a4a34'); pen.fill(rect(560, seat - 260, 24, 260), '#6a4a34')
        table(pen, 820, 1300, top); laptop(pen, 960, top, 1)
        fig(pen, m, t, LAP)
    return dict(draw=draw, actors=[m], grounded=[m])


@strip('mom_photo_run', 5.0)
def _s_photo():
    ppm = 330.0
    m = actor('mom', 760, FLOOR, ppm, seed=4, expr='busy'); m.set(-1e9, None, 0.0, turn=-0.3)
    m.talk([(0.1, 0.9), (1.3, 2.2)])
    m.look_at(0.0, (380, 520), t1=2.8, dur=0.3)
    ts, ev = m.snap_photo(0.5, (1500, 560), side=1, dur=1.8)
    m.run(3.0, 4.9, 0, 700)
    def draw(pen, t):
        room(pen, '#3e4654', '#4a4a50')
        pen.fill(rect(1400, 300, 420, 360), '#2a3a4a'); pen.line(rect(1400, 300, 420, 360), 3)
        fig(pen, m, t, WARM)
        if abs(t - ts) < 0.1: pen.fill(rect(0, 0, 1920, 1080), '#ffffff', 60)
    return dict(draw=draw, actors=[m], grounded=[m])


@strip('mom_climax', 6.5)
def _s_climax():
    ppm = 300.0
    o = actor('owen', 860, FLOOR, ppm, seed=5, expr='quiet_sure'); o.set(-1e9, None, 0.0, turn=0.45)
    b = CH.Acting('blank3', seed=6, height=2.45 * ppm, expr='too_wide').place(1560, FLOOR); b.set(-1e9, None, 0, b3_face=-1.0)
    b.b3_hand(-1.0, 1, lambda t: (o.where(t, 'neck')[0] + 0.03 * ppm, o.where(t, 'neck')[1] - 0.04 * ppm), dur=0.5)
    b.freeze(0.0, 6.5)
    m = actor('mom', 560, FLOOR, ppm, seed=7, expr='terrified_call'); m.set(-1e9, None, 0.0, turn=0.45)
    m.headset_off(0.3, side=1); m.glasses_off(1.2, side=-1)
    m.expr('listening_soft', 1.6, None)
    m.walk(2.3, 3.5, 0, 450, facing=1)
    m.turn(3.5, -0.5, dur=0.45)
    m.hug(4.1, o)
    o.look_at(0.0, (m, 'eyes'), dur=0.4)
    def draw(pen, t):
        room(pen, '#3a3630', '#4a4038')
        pen.fill(rect(0, 0, 1920, FLOOR - 2.45 * ppm), '#2a2622')
        CH.draw(pen, 'blank3', b.x0, b.y0, b.height, b.at(t), t=t, light=NIGHT)
        fig(pen, o, t, WARM); fig(pen, m, t, WARM)
    return dict(draw=draw, actors=[o, m], grounded=[o])


@strip('owen_tablet', 6.0)
def _s_tablet():
    ppm = 380.0
    o = actor('owen', 860, FLOOR, ppm, seed=8, expr='neutral'); o.set(-1e9, None, 0.0, turn=0.3)
    tab = lambda t: (o.where(0.0, 'chest')[0] + 0.12 * ppm, o.where(0.0, 'chest')[1] + 0.1 * ppm)
    o.reach_to(0.0, -1, tab, t1=1.7, dur=0.4, z=60.0, contact='palm', shape='grip', prop='tab_back')
    o.typing(0.2, 1.6, tab, side=1); o.hold_prop('tab_back', -1, 0.0, 1.7)
    o.look_at(0.0, tab, t1=1.7, dur=0.3)
    o.point_at(2.0, (1600, 260), t1=3.0, side=1)
    o.crouch(3.3, amount=1.6, t1=4.0, dur=0.25); o.expr('fear', 3.2, 4.3)
    o.look_at(3.3, (1600, 260), t1=None, dur=0.3)
    o.wave(4.5, 5.9, side=1)
    def draw(pen, t):
        room(pen, '#3a4256', '#40384a'); pen.fill(rect(1450, 120, 320, 300), '#1a2236'); pen.line(rect(1450, 120, 320, 300), 4)
        fig(pen, o, t, WARM)
    return dict(draw=draw, actors=[o], grounded=[o])


@strip('owen_board_rise', 6.0)
def _s_board():
    ppm = 380.0
    o = actor('owen', 1060, FLOOR, ppm, seed=9, expr='quiet_sure'); o.set(-1e9, None, 0.0, turn=0.65)
    ev = o.write_marker(0.3, 3.0, 1, (1250, 470))
    o.look_at(0.3, (1250, 470), t1=3.0, dur=0.3)
    o.rise_to(3.5, (1180, 600), side=-1, dur=2.0)
    o.look_at(3.4, (1180, 600), dur=0.4)
    def draw(pen, t):
        room(pen, '#4a4a44', '#5a4a3a')
        pen.fill(rect(1150, 200, 360, 740), '#d8dad6'); pen.line(rect(1150, 200, 360, 740), 3)
        pen.fill(rect(1190, 360, 280, 220), '#f6f6f2'); pen.line(rect(1190, 360, 280, 220), 2)
        pen.fill(oval(1180, 600, 7), '#121216')
        fig(pen, o, t, WARM)
    return dict(draw=draw, actors=[o], grounded=[o])


@strip('dunn_owen', 6.0)
def _s_dunn():
    ppm = 300.0
    d = actor('dunn', 1150, FLOOR, ppm, seed=10, expr='calm_firm'); d.set(-1e9, None, 0.0, turn=-0.3)
    d.hold_sign(-1e9, None, side=-1)
    d.radio_up(0.4, 2.2, side=1); d.talk([(0.8, 1.9)])
    o = actor('owen_coat', 0, FLOOR, ppm, seed=11, expr='fear'); o.run(0.2, 1.5, 300, 960)
    o.set(1.5, None, 0.3, turn=0.3)
    d.shelter(2.6, o, t1=5.8, side=1, toward=-1)
    d.look_at(0.0, (200, 600), t1=2.4, dur=0.3); d.look_at(2.4, (o, 'eyes'), dur=0.4)
    def draw(pen, t):
        room(pen, '#c8ccd4', '#e8ecf0')
        fig(pen, o, t, None); fig(pen, d, t, None)
    return dict(draw=draw, actors=[d, o], grounded=[d, o])


@strip('blank2_street', 6.0)
def _s_street():
    ppm = 300.0
    b = actor('blank2', 760, FLOOR, ppm, seed=12, expr='too_sweet')
    b.height = CH.height_px('blank2', ppm, tall=CH.BLANK_TALL['r1'])
    b.look_at(0.0, (1500, 120), t1=2.4, dur=0.3); b.wave(0.3, 2.2, side=1, slow=True)
    b.hand_on_glass(2.8, 6.0, side=1); b.hand_on_glass(2.9, 6.0, side=-1)
    b.listen_tilt(4.0, None, side=1, angle=24.0)
    def draw(pen, t):
        if t < 2.5:
            room(pen, '#141a2a', '#22242c')
            pen.fill(rect(560, 120, 20, 820), '#3a3e48'); pen.fill(oval(570, 120, 60, 22), '#ffe9b0')
            pen.fill(poly([(530, 130), (610, 130), (900, 940), (240, 940)]), '#ffe9b0', 40)
            fig(pen, b, t, NIGHT)
        else:
            room(pen, '#141a2a', '#22242c')
            fig(pen, b, t, NIGHT, x=960)
            pen.fill(rect(560, 100, 800, 840), '#a8c4e0', 40); pen.line(rect(560, 100, 800, 840), 8, '#5a5e66')
    return dict(draw=draw, actors=[b], grounded=[b])


@strip('blank3_unfold', 6.0)
def _s_unfold():
    ppm = 240.0; ceil = FLOOR - 2.45 * ppm
    b = CH.Acting('blank3', seed=13, height=2.45 * ppm, expr='too_wide').place(1110, FLOOR); b.set(-1e9, None, 0, b3_face=-1.0)
    b.b3_unfold(0.3, dur=4.4)
    b.b3_hand(5.0, 1, (620, 640), dur=1.2)
    def draw(pen, t):
        room(pen, '#3a3630', '#4a4038'); pen.fill(rect(0, 0, 1920, ceil), '#2a2622'); pen.line(poly([(0, ceil), (1920, ceil)], False), 3)
        CH.draw(pen, 'blank3', b.x0, b.y0, b.height, b.at(t), t=t, light=NIGHT)
        pen.fill(rect(760, FLOOR - 1.8 * ppm, 300, 1.8 * ppm), '#d6d8d4'); pen.line(rect(760, FLOOR - 1.8 * ppm, 300, 1.8 * ppm), 3)
    return dict(draw=draw, actors=[], grounded=[])


@strip('blank3_coat', 8.0)
def _s_coat():
    ppm = 260.0; ceil = FLOOR - 2.45 * ppm
    o = actor('owen', 860, FLOOR, ppm, seed=14, expr='fear'); o.set(-1e9, None, 0.0, turn=0.5)
    b = CH.Acting('blank3', seed=15, height=2.45 * ppm, expr='too_wide').place(1180, FLOOR); b.set(-1e9, None, 0, b3_face=-1.0)
    on0 = CH.coat_on(o, 0.0)
    held = (1040, on0[1] - 20, on0[2])
    def coat(t):
        k = CH.ease_in_out(CH.prog(t, 1.6, 3.0))
        on = CH.coat_on(o, min(t, 6.1))
        return held[0] + (on[0] - held[0]) * k, held[1] + (on[1] - held[1]) * k, held[2]
    b.b3_hold_coat(-1.0, coat, dur=0.6, face=-1)
    b.talk([(3.0, 4.9), (5.4, 6.1)])
    top_to = lambda t: (coat(t)[0] - 0.18 * ppm, coat(t)[1] + 0.2 * ppm)
    o.rise_to(5.2, lambda t: top_to(t), side=1, dur=0.9)
    o.drop_out(6.2, 380, run_dur=1.4)
    def draw(pen, t):
        room(pen, '#3a3630', '#4a4038'); pen.fill(rect(0, 0, 1920, ceil), '#2a2622')
        cx, cy, h = coat(t)
        btn = 6.0 * CH.prog(t, 3.0, 5.0); op = 1.0 - 0.4 * CH.prog(t, 1.6, 3.0)
        full = CH.prog(t, 2.6, 3.0) * (1.0 - CH.prog(t, 6.2, 6.5))
        tout = CH.prog(t, 5.0, 5.6)
        CH.draw(pen, 'blank3', b.x0, b.y0, b.height, b.at(t), t=t, light=NIGHT)
        if t < 2.8 or t > 6.4:
            CH.draw_red_coat(pen, cx, cy, h, btn, op, full, top_out=tout, top_to=top_to(t))
            fig(pen, o, t, WARM)
        else:
            CH.draw_red_coat(pen, cx, cy, h, btn, op, full, part='back')
            fig(pen, o, t, WARM)
            CH.draw_red_coat(pen, cx, cy, h, btn, op, full, part='front', top_out=tout, top_to=top_to(t))
    return dict(draw=draw, actors=[o], grounded=[o])


@strip('blank3_lunge', 6.0)
def _s_lunge():
    ppm = 260.0; ceil = FLOOR - 2.45 * ppm; ctop = FLOOR - 0.9 * ppm
    o = actor('owen', 880, FLOOR, ppm, seed=16, expr='fear'); o.set(-1e9, None, 0.0, turn=-0.5)
    b = CH.Acting('blank3', seed=17, height=2.45 * ppm, expr='too_wide').place(1480, FLOOR); b.set(-1e9, None, 0, b3_face=-1.0)
    b.b3_lunge(0.3, (1250, ctop - 4), (1000, ctop - 4), dur=1.6, t1=2.0)
    hood = lambda t: (o.where(t, 'neck')[0] + 0.035 * ppm, o.where(t, 'neck')[1] - 0.05 * ppm)
    b.b3_hand(2.2, 1, hood, dur=1.0)
    b.freeze(3.3, 4.6)
    b.b3_collapse(4.6, 1.3)
    def draw(pen, t):
        room(pen, '#3a3630', '#4a4038'); pen.fill(rect(0, 0, 1920, ceil), '#2a2622')
        pen.fill(rect(980, ctop, 300, FLOOR - ctop), '#8a7a66'); pen.fill(rect(970, ctop - 10, 320, 14), '#d8d2c6')
        CH.draw(pen, 'blank3', b.x0, b.y0, b.height, b.at(t), t=t, light=NIGHT)
        fig(pen, o, t, WARM)
    return dict(draw=draw, actors=[o], grounded=[o])


@strip('car_arm', 5.0)
def _s_car():
    ppm = 300.0
    o = actor('owen_coat', 1350, FLOOR, ppm, seed=18, expr='fear'); o.set(-1e9, None, 0.0, turn=-0.55)
    o.walk(2.0, 3.0, 0, 170, facing=-1)
    def ext(t): return CH.ease_in_out(CH.prog(t, 0.3, 2.6)) * (1.0 - CH.ease_in_out(CH.prog(t, 3.4, 4.8)))
    def draw(pen, t):
        room(pen, '#9aa6b6', '#e6eaf0')
        pen.fill(rrect(300, 560, 760, 300, 40), '#b8bcc4'); pen.fill(rrect(420, 470, 500, 140, 30), '#b8bcc4')
        pen.fill(rrect(640, 500, 240, 110, 12), '#1c2028')
        nx, ny = o.where(t, 'neck')
        CH.draw_long_arm(pen, (860, 590), (nx + 0.02 * ppm, ny + 0.09 * ppm), ext(t), t, ppm / 100.0)
        pen.line(rrect(300, 560, 760, 300, 40), 3)
        fig(pen, o, t, None)
    return dict(draw=draw, actors=[o], grounded=[o])


@strip('son_mensah', 6.0)
def _s_son():
    ppm = 300.0; btop = FLOOR - 0.48 * ppm
    s_ = actor('son', 540, FLOOR, ppm, seed=19, expr='neutral'); s_.set(-1e9, None, 0.0, turn=0.35)
    s_.seated(btop)
    tc = s_.tablet_down(1.2, (700, btop), side=1)
    s_.look_at(0.0, (s_, 'lap'), t1=2.2, dur=0.3); s_.look_at(2.4, (360, 180), dur=0.5); s_.expr('kind_smile', 3.0, None)
    k = actor('mensah', 1300, FLOOR, ppm, seed=20, expr='calm_firm'); k.set(-1e9, None, 0.0, turn=0.4)
    k.take_notes(0.0, 3.0)
    k.read_board(3.3, (1720, 470), then=(1000, 380), side=1)
    def draw(pen, t):
        room(pen, '#3a4256', '#40384a')
        pen.fill(rect(260, btop, 560, FLOOR - btop), '#6a7aa0'); pen.fill(rect(250, btop - 14, 580, 28), '#e0e4ee')
        pen.fill(rect(1620, 300, 220, 300), '#f2f2ee'); pen.line(rect(1620, 300, 220, 300), 3)
        if t >= tc: pen.fill(rect(650, btop - 22, 110, 8), '#5a5f6a')
        fig(pen, s_, t, None); fig(pen, k, t, None)
    return dict(draw=draw, actors=[s_, k], grounded=[s_, k])


@strip('sting_hands', 3.0)
def _s_sting():
    n = CH.Acting('narrator_b', seed=24, height=1500.0).place(960, 2050)
    tr = n.set_down(0.3, 'headset', 1, (1060, 760), dur=1.6)
    n.reach_to(0.0, -1, (820, 770), dur=0.5, z=40.0, contact='palm', shape='relaxed')
    def draw(pen, t):
        room(pen, '#262a36', '#3a3030', y=780)
        pen.fill(rect(300, 770, 1320, 40), '#6a4e3a'); pen.fill(rect(300, 810, 1320, 270), '#4a3628')
        pen.fill(rrect(560, 640, 90, 130, 18), '#b8d0e0', 90); pen.line(rrect(560, 640, 90, 130, 18), 3)
        if t >= tr: CH.draw_prop3(pen, 'headset', 1060, 740, 1500.0 / 180.0)
        for sd in (-1, 1): CH.draw_arm(pen, 'narrator_b', sd, n.at(t), x=n.x0, y_feet=n.y0, height=n.height, t=t)
    return dict(draw=draw, actors=[n], grounded=[])


@strip('mom_wind_box', 5.0)
def _s_wind():
    ppm = 400.0
    m = actor('mom', 900, FLOOR, ppm, seed=21, expr='listening_soft'); m.set(-1e9, None, 0.0, turn=0.2, specs=0.0, hs_off=1.0)
    m.wind_box(0.4, 4.6)
    m.talk([(1.0, 1.8), (2.0, 2.8), (3.0, 4.3)]); m.cry(0.6, None, smile=True)
    def draw(pen, t):
        room(pen, '#4a4038', '#5a4a3a'); fig(pen, m, t, WARM)
    return dict(draw=draw, actors=[m], grounded=[m])


@strip('blank1_laptop', 5.0)
def _s_b1():
    ppm = 330.0; seat = FLOOR - 0.46 * ppm; top = FLOOR - 0.76 * ppm
    b = actor('blank1', 960, FLOOR, ppm, seed=22, expr='polite'); b.set(-1e9, None, 0.0, turn=2.0)
    b.seated(seat)
    b.typing(0.2, 2.3, (960, top - 10))
    b.turn(2.6, 0.55, dur=0.6)
    b.glasses_off(3.3, side=1)
    b.expr('too_sweet', 3.6, None)
    def draw(pen, t):
        room(pen, '#1e2230', '#2a2a30')
        table(pen, 700, 1220, top); laptop(pen, 960, top, -1)
        fig(pen, b, t, LAP)
    return dict(draw=draw, actors=[b], grounded=[b])


@strip('blank2_sill', 5.0)
def _s_sill():
    ppm = 330.0; sill = FLOOR - 0.85 * ppm
    b = actor('blank2', 960, FLOOR, ppm, seed=23, expr='too_sweet'); b.set(-1e9, None, 0.0, turn=0.3)
    b.height = CH.height_px('blank2', ppm, tall=CH.BLANK_TALL['sill'])
    b.seated(sill, hands='lap')
    b.listen_tilt(0.6, None, side=1, angle=26.0)
    b.talk([(0.3, 1.5), (1.8, 3.0), (3.3, 4.6)])
    def draw(pen, t):
        room(pen, '#141a2a', '#22242c')
        pen.fill(rect(700, 160, 520, sill - 160), '#26324a'); pen.line(rect(700, 160, 520, sill - 160), 6, '#8a8e96')
        pen.fill(rect(680, sill - 4, 560, 26), '#c8c4bc')
        fig(pen, b, t, NIGHT)
    return dict(draw=draw, actors=[b], grounded=[])


def render_group(g):
    rows = []
    for name in GROUPS[g]:
        f, dur = STRIPS[name]
        S = f()
        ts = list(np.linspace(0.0, dur - 1.0 / 60, 8))
        tiles = []
        for t in ts:
            surf, cv = _surface(640, 360)
            cv.save(); cv.clear(skia.Color(20, 22, 30)); cv.scale(CFG.k, CFG.k)
            S['draw'](Pen(cv), t); cv.restore()
            tl = cv2.resize(_grab(surf), (320, 180), interpolation=cv2.INTER_AREA)
            cv2.putText(tl, '%s %.1f' % (name if t == 0 else '', t), (5, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
            tiles.append(tl)
        rows.append(np.vstack([np.hstack(tiles[:4]), np.hstack(tiles[4:])]))
        miss = max([m[-1] for a in S.get('actors', []) for m in getattr(a, 'misses', [])], default=0.0)
        feet = [round(max(a.foot_gap(t) for t in ts), 1) for a in S.get('grounded', [])]
        print('%-16s reach miss max %.1f px, foot gaps %s' % (name, miss, feet))
    cv2.imwrite(os.path.join(OUT, 'strips_%s.jpg' % g), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])



DETAILS = [('mom_type_finger', 3.0, (480, 300, 640, 360)), ('owen_tablet', 1.0, (600, 380, 560, 315)),
           ('blank3_coat', 5.7, (650, 330, 640, 360)), ('dunn_owen', 4.0, (800, 420, 600, 338)),
           ('sting_hands', 1.2, (480, 400, 960, 540)), ('car_arm', 2.4, (700, 380, 960, 540))]


def details(out=None):
    """Close crops of key contacts (one finger, tablet, top button, shelter arm, folded start, car arm) at 640x360."""
    tiles = []
    for name, t, (x, y, w, h) in DETAILS:
        S = STRIPS[name][0]()
        surf, cv = _surface(1920, 1080)
        cv.save(); cv.clear(skia.Color(20, 22, 30)); cv.scale(CFG.k, CFG.k)
        S['draw'](Pen(cv), t); cv.restore()
        tiles.append(cv2.resize(_grab(surf)[int(y):int(y + h), int(x):int(x + w)], (640, 360), interpolation=cv2.INTER_AREA))
    img = np.vstack([np.hstack(tiles[k:k + 2]) for k in range(0, len(tiles), 2)])
    cv2.imwrite(out or os.path.join(OUT, 'details.jpg'), img, [cv2.IMWRITE_JPEG_QUALITY, 85])

if __name__ == '__main__':
    args = sys.argv[1:] or ['sheet', 'faces']
    os.makedirs(OUT, exist_ok=True)
    if 'sheet' in args: sheet(); print('sheet ->', os.path.join(OUT, 'cast_sheet.png'))
    if 'faces' in args: faces640(); print('faces ->', os.path.join(OUT, 'faces_640.jpg'))
    if 'details' in args: details(); print('details ->', os.path.join(OUT, 'details.jpg'))
    if 'strips' in args:
        for g in [a for a in args if a in GROUPS] or list(GROUPS): render_group(g)
