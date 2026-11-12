"""cast_sheets.py: model and acting sheets for the dummy film's cast (characters.py), written to W/cast/.

    cd "Vox test/Dummy Video/film" && python3 tools/cast_sheets.py [names...]     (default: all sheets)
    python3 tools/cast_sheets.py sync          # the 4 s jaw / lip sync clips at 960x540 with the voice + the sync plot

Sheets (1920x1080 JPEG): lineup, winks_turnaround, winks_faces (close-up / medium / wide), winks_arc, winks_acting,
winks_acting2, family_faces, family_acting (mom), family_acting2 (Owen), family_acting3 (you, Grandpa), laps (the
hospital, the 1974 show, Owen in the den, in your arms), props. The scenery on the sheets (chairs, stairs, bed...) is
sheet-only stand-ins: the real sets are in sets.py.
"""
import os, sys, math, time, json, subprocess
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import numpy as np
import cv2
import skia
from engine.core import set_render_size, Pen, CFG, rect, rrect, oval, poly, smooth, text, mix, col
import characters as CH

OUT = os.path.join(HERE, '_work', 'cast')
BG = (26, 28, 36)


def canvas(w=1920, h=1080, bg=BG):
    set_render_size(w, h)
    surf = skia.Surface(CFG.rw, CFG.rh)
    cv = surf.getCanvas(); cv.clear(skia.Color(*bg)); cv.scale(CFG.k, CFG.k)
    return surf, cv, Pen(cv)


def floor(pen, y, x0=0, x1=1920, c='#1f222b'):
    pen.linear(rect(x0, y, x1 - x0, 1080 - y), 0, y, 0, 1080, [(0, c), (1, '#121319')])


def title(cv, s, sub=''):
    text(cv, s, 40, 52, 900, 34, '#ffffff', 255, 0.04, 'left')
    if sub: text(cv, sub, 40, 86, 700, 19, '#9aa3b8', 255, 0.02, 'left')


def label(cv, s, x, y, size=18, c='#d8dbe4', align='center'):
    text(cv, s, x, y, 800, size, c, 255, 0.02, align)


def save(surf, name):
    os.makedirs(OUT, exist_ok=True)
    img = surf.makeImageSnapshot().toarray()[:, :, :3]
    p = os.path.join(OUT, name + '.jpg')
    cv2.imwrite(p, img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print('wrote', p)


LAMP = dict(rim='#ffcf8f', rim_a=60, side=-1, key=0.12)            # a warm table lamp
NIGHT = dict(rim='#9fb6ff', rim_a=55, side=1)                        # the dark house
TORCH = dict(under='#fff1c8', under_a=210)                           # the usher's flashlight under the chin
TV = dict(rim='#a9d4ff', rim_a=110, side=1, key=-0.15)               # the TV's blue flicker
HOSP = dict(rim='#d8f0ea', rim_a=60, side=1, key=0.05)               # hospital strip light


# ------------------------------------------------------------------------------------------------ sheet-only scenery
def chair(pen, x, seat, h, c='#6a4630'):
    pen.fill(rect(x - h * 0.28, seat - h * 0.95, h * 0.56, h * 0.95), mix(c, '#000000', 0.15)); pen.line(rect(x - h * 0.28, seat - h * 0.95, h * 0.56, h * 0.95), 4)
    pen.fill(rect(x - h * 0.32, seat, h * 0.64, h * 0.07), c); pen.line(rect(x - h * 0.32, seat, h * 0.64, h * 0.07), 4)
    for sx in (-1, 1): pen.fill(rect(x + sx * h * 0.27 - 6, seat + h * 0.07, 12, h * 0.9), mix(c, '#000000', 0.3))


def table(pen, x, top, w, h=200):
    pen.fill(rect(x - w / 2, top, w, 22), '#7a5236'); pen.line(rect(x - w / 2, top, w, 22), 4)
    pen.fill(rect(x - w / 2 + 10, top + 22, 18, h), '#4a2f20'); pen.fill(rect(x + w / 2 - 28, top + 22, 18, h), '#4a2f20')


def armchair(pen, x, seat, h, c='#5b3a4a'):
    pen.fill(rrect(x - h * 0.42, seat - h * 0.95, h * 0.84, h * 1.0, 28), mix(c, '#000000', 0.2)); pen.line(rrect(x - h * 0.42, seat - h * 0.95, h * 0.84, h * 1.0, 28), 4)
    pen.fill(rrect(x - h * 0.5, seat - h * 0.05, h * 1.0, h * 0.42, 20), c); pen.line(rrect(x - h * 0.5, seat - h * 0.05, h * 1.0, h * 0.42, 20), 4)
    for sx in (-1, 1):
        pen.fill(rrect(x + sx * h * 0.45 - h * 0.1, seat - h * 0.38, h * 0.2, h * 0.5, 14), mix(c, '#ffffff', 0.08)); pen.line(rrect(x + sx * h * 0.45 - h * 0.1, seat - h * 0.38, h * 0.2, h * 0.5, 14), 4)


def stairs(pen, x, base, w=480, rise=70, n=4):
    for k in range(n):
        pen.fill(rect(x - w / 2, base - (k + 1) * rise, w, rise), '#4a3426' if k % 2 else '#553c2c'); pen.line(rect(x - w / 2, base - (k + 1) * rise, w, rise), 3)


def bed(pen, x, y, w, h, t=0.0):
    pen.fill(rect(x - w / 2, y - h * 0.62, w * 0.18, h * 0.7), '#8d98a4'); pen.line(rect(x - w / 2, y - h * 0.62, w * 0.18, h * 0.7), 4)
    pen.fill(rrect(x - w / 2 + 10, y - h * 0.58, w * 0.32, h * 0.32, 24), '#eef2f4'); pen.line(rrect(x - w / 2 + 10, y - h * 0.58, w * 0.32, h * 0.32, 24), 4)


def blanket(pen, x, y, w, h):
    b = smooth([(x - w * 0.36, y - h * 0.22), (x + w * 0.5, y - h * 0.2), (x + w * 0.52, y + 10), (x - w * 0.38, y + 10)], True, 0.3)
    pen.fill(b, '#cfd9e2'); pen.line(b, 4)
    pen.line(poly([(x - w * 0.36, y - h * 0.16), (x + w * 0.5, y - h * 0.14)], False), 3, '#9aa8b6')


def bookcase(pen, x, top, w=380, h=320):
    pen.fill(rect(x - w / 2, top, w, h), '#3a2a20'); pen.line(rect(x - w / 2, top, w, h), 4)
    for k in range(1, 3): pen.line(poly([(x - w / 2, top + k * h / 3), (x + w / 2, top + k * h / 3)], False), 4)
    for k in range(9):
        bx = x - w / 2 + 14 + k * (w - 28) / 9
        pen.fill(rect(bx, top + 14, (w - 28) / 9 - 4, h / 3 - 18), ['#6a2a2a', '#2a4a6a', '#6a5a2a', '#3a5a3a'][k % 4])


def rug(pen, x, y, w=460):
    pen.fill(rrect(x - w / 2, y - 30, w, 52, 8), '#6a2a2a'); pen.line(rrect(x - w / 2, y - 30, w, 52, 8), 3, '#3a1414')


def case(pen, x, y, w=300, h=110, open_=0.0):
    pen.fill(rrect(x - w / 2, y - h, w, h, 10), '#15161a'); pen.line(rrect(x - w / 2, y - h, w, h, 10), 4)
    for sx in (-1, 1):
        pen.fill(rrect(x + sx * w * 0.28 - 12, y - h + 6, 24, 16, 3), '#c9a24a'); pen.line(rrect(x + sx * w * 0.28 - 12, y - h + 6, 24, 16, 3), 2)


def kitchen(pen, x, yf, hh, with_table=False, tx=0.0):
    """A real-scale kitchen chair (seat 0.45 m) for the 0.85 m dummy of height hh px standing on yf; with_table: the
    table top (0.75 m) in front. Returns the seat y."""
    seat = yf - 0.53 * hh
    chair(pen, x, seat, 0.53 * hh / 0.97)
    if with_table: table(pen, x + tx, yf - 0.88 * hh, hh * 1.1, 0.86 * hh)
    return seat


# ------------------------------------------------------------------------------------------------ strip helper
def strip(cv, pen, who, act, times, y0, rh, lab, paint=None, light=None, h=None, bg=('#232633', '#171920'), events=True):
    """One row of frames: act(a) builds the Acting (returns sound events), paint(pen, a, tt, x, yf, hh) draws the frame
    (default: the figure alone)."""
    a = CH.Acting(who, seed=3)
    ev = act(a)
    n = len(times); cw = 1920.0 / n
    for i, tt in enumerate(times):
        x = cw * i + cw * 0.5
        yf = y0 + rh - 16
        hh = h or rh * 0.8
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(cw * i + 2, y0 + 2, cw - 4, rh - 4))
        pen.linear(rect(cw * i, y0, cw, rh), 0, y0, 0, y0 + rh, [(0, bg[0]), (1, bg[1])])
        if paint: paint(pen, a, tt, x, yf, hh)
        else: CH.draw(pen, who, x, yf, hh, a.at(tt), light=light)
        cv.restore()
        label(cv, '%.2f' % tt, cw * i + 34, y0 + 24, 14, '#9aa3b8')
    label(cv, lab, 14, y0 + rh - 30 if not events else y0 + 46, 17, '#ffffff', 'left')

    def flat(x):
        if isinstance(x, dict): return [x]
        if isinstance(x, (list, tuple)): return [e for y in x for e in flat(y)]
        return []
    evs = flat(ev)
    if evs and events:
        label(cv, 'sfx: ' + ', '.join('%s %.2f' % (e['name'], e['t']) for e in evs[:5]), 14, y0 + rh - 10, 13, '#8fd4a8', 'left')
    return a


def _bg(pen, x0, y0, w, h, c0='#2c3242', c1='#111318', cx=None, cy=None):
    pen.radial(rect(x0, y0, w, h), cx if cx is not None else x0 + w / 2, cy if cy is not None else y0 + h * 0.35, max(w, h) * 0.8, [(0, c0), (1, c1)])


# ------------------------------------------------------------------------------------------------ sheets
def sheet_lineup():
    surf, cv, pen = canvas()
    floor(pen, 940)
    title(cv, 'THE DUMMY FILM CAST: LINEUP TO SCALE', 'Mister Winks 0.85 m  /  Grandpa 1.72 m (86)  /  young Walter 1.78 m (1974)  /  Mom 1.65 m  /  you 1.74 m (16)  /  Owen 1.32 m (9)')
    H = 780.0 / 1.85
    items = [('winks', 0.85, 'MISTER WINKS', None), ('grandpa', 1.72, 'GRANDPA', None), ('grandpa_bed', 1.72, 'IN HOSPITAL', None),
             ('walter74', 1.78, 'WALTER, 1974', None), ('mom', 1.65, 'MOM', None), ('you', 1.74, 'YOU', None), ('owen', 1.32, 'OWEN, 9', None)]
    xs = [150, 400, 640, 900, 1150, 1420, 1700]
    for (who, m, lab, _), x in zip(items, xs):
        a = CH.Acting(who, seed=4)
        if who == 'winks': a.torch_on(-5.0, 120.0, 1, hold='side')
        if who == 'grandpa': a.set(-9, None, 0.1, hunch=0.35, smile=0.3, m_press=0.3)
        if who == 'grandpa_bed': a.set(-9, None, 0.1, hunch=0.45)
        if who == 'walter74': a.showman(-9, 99)
        if who == 'mom': a.expr('sad', 0)
        if who == 'you': a.expr('nervous', 0)
        P = a.at(2.0)
        CH.draw(pen, who, x, 940, m * H, P, light=LAMP)
        label(cv, lab, x, 985, 20)
    save(surf, 'lineup')


def sheet_winks_turnaround():
    surf, cv, pen = canvas()
    floor(pen, 930)
    title(cv, 'MISTER WINKS: TURNAROUND', 'painted red hair, hard side part, freckles, glass eyes under wooden lids, the jaw block on two slot lines, '
          'burgundy usher\'s jacket, pillbox cap, white gloves')
    views = [(0.0, 'FRONT'), (-0.5, '3/4 LEFT'), (0.5, '3/4 RIGHT'), (1.0, 'PROFILE'), (2.0, 'BACK (the slot)')]
    for i, (yaw, lab) in enumerate(views):
        a = CH.Acting('winks', seed=2); a.set(-10, None, 0.1, turn=yaw)
        x = 170 + i * 330
        CH.draw(pen, 'winks', x, 930, 760, a.at(30.0), light=LAMP)
        label(cv, lab, x, 975, 20)
    a = CH.Acting('winks', seed=2); a.sit_dummy(hands='knees'); a.set(-10, None, 0.1, turn=0.35)
    seat = kitchen(pen, 1790, 930, 560)
    CH.draw(pen, 'winks', 1790, seat, 560, a.at(30.0), light=LAMP)
    label(cv, 'SEATED (perch)', 1790, 975, 20)
    save(surf, 'winks_turnaround')


def sheet_winks_faces():
    """The dummy's face in close-up, medium and wide (the framings the film uses), with the jaw, lids and lighting."""
    surf, cv, pen = canvas()
    # close-up (left): S2, the jaw half open, warm lamp
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(0, 0, 900, 1080))
    _bg(pen, 0, 0, 900, 1080, '#3a3040', '#121016')
    a = CH.Acting('winks', seed=1); a.jaw_hang(250.0, 0.55)
    CH.draw_bust(pen, 'winks', 450, 560, 1.05, a.at(252.0), light=LAMP)
    cv.restore()
    pen.fill(rect(0, 1030, 900, 50), '#000000', 150)
    label(cv, 'CLOSE-UP  draw_bust scale 1.05  (S2, the jaw hanging open, the black hollow behind the painted teeth)', 450, 1062, 16)
    # medium (right top): 2 x 3 busts
    cells = [('jaw shut (S0)', lambda a: None, 30.0, LAMP), ('jaw dropped: jaw_drop', lambda a: a.jaw_drop(29.5, 1.0), 30.0, LAMP),
             ('wink: his left lid clicks', lambda a: a.wink(29.8, 1, 0.5), 30.0, LAMP), ('both lids: blink_click', lambda a: a.blink_click(29.8, 0.5), 30.0, LAMP),
             ('torch under the chin (S4)', lambda a: (a.torch_on(399.0, 0.0, 1, hold='chin'), a.jaw_hang(399.5, 0.4)), 425.0, TORCH),
             ('the TV glow, head turned 3/4', lambda a: a.set(0, None, 0.1, h_turn=0.55), 300.0, TV)]
    for i, (lab, act, tt, lt) in enumerate(cells):
        cx = 900 + 170 + (i % 3) * 340; cy = 150 + (i // 3) * 330
        a = CH.Acting('winks', seed=1); act(a)
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(cx - 168, cy - 148, 336, 322))
        _bg(pen, cx - 170, cy - 150, 340, 330, '#3a3040' if lt is not TORCH else '#2a2018', '#121016')
        CH.draw_bust(pen, 'winks', cx, cy + 20, 0.36, a.at(tt), light=lt)
        cv.restore()
        pen.fill(rect(cx - 168, cy + 146, 336, 28), '#000000', 150)
        label(cv, lab, cx, cy + 166, 14)
    # wide (right bottom): seated in Grandpa's kitchen chair at the table; standing on the chair
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(902, 700, 1018, 380))
    _bg(pen, 900, 700, 1020, 380, '#2c2a26', '#111014')
    a = CH.Acting('winks', seed=1); a.sit_dummy(hands='table'); a.torch_on(170.0, 0.0, 1, hold='up')
    chair(pen, 1130, 960, 170); table(pen, 1130, 900, 300, 160)
    P = a.at(180.0); CH.draw(pen, 'winks', 1130, 960, 210, P, light=LAMP)
    lx, ly, ang = CH.torch_pos('winks', P, 1, x=1130, y_feet=960, height=210); CH.draw_torch_beam(pen, lx, ly, ang, 300, a=0.8)
    b = CH.Acting('winks', seed=1); b.sit_dummy(-1e9, 314.0, hands='table'); b.stand_on_chair(314.7)
    chair(pen, 1600, 980, 170)
    CH.draw(pen, 'winks', 1600, 980, 210, b.at(317.0), light=LAMP)
    cv.restore()
    label(cv, 'WIDE: in Grandpa\'s chair, the torch at the ceiling (2:58)            stands up on the chair (5:17)', 1410, 1062, 15)
    title(cv, '', '')
    save(surf, 'winks_faces')


def sheet_winks_arc():
    surf, cv, pen = canvas()
    title(cv, 'MISTER WINKS: THE GRIN THAT WIDENS (WINKS_ARC, film time)',
          'the painted grin widens, the stare hardens (pupils shrink, brows pinch, the varnish cracks); on the tape and at the end the one inside looks out')
    a = CH.Acting('winks', seed=1)
    tp = CH.Acting('winks', seed=1, arc=CH.WINKS_TAPE_ARC)
    cells = [(a, 100.0, 'S0  1:40  the hospital, the case'), (a, 178.0, 'S1  2:58  in Grandpa\'s chair'), (a, 252.0, 'S2  4:10  the head has turned'),
             (a, 318.0, 'S3  5:18  stands on the chair'), (a, 404.0, 'S4  6:44  "smiles up at me"'), (a, 530.0, 'S5  8:50  Owen\'s lap'),
             (tp, 455.0, 'TAPE  7:35  "Please. Somebody help me."'), (a, 658.0, 'OWEN INSIDE  10:58  he opens his eyes')]
    for i, (ac, tt, lab) in enumerate(cells):
        cx = 240 + (i % 4) * 480; cy = 350 + (i // 4) * 470
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(cx - 236, cy - 228, 472, 460))
        _bg(pen, cx - 240, cy - 240, 480, 480, '#3a3040' if i < 6 else '#28323e', '#121016')
        CH.draw_bust(pen, 'winks', cx, cy + 10, 0.5, ac.at(tt), light=LAMP if i != 6 else TV)
        cv.restore()
        pen.fill(rect(cx - 236, cy + 196, 472, 36), '#000000', 150)
        label(cv, lab, cx, cy + 221, 17)
    save(surf, 'winks_arc')


def sheet_winks_acting():
    surf, cv, pen = canvas()
    rh = 1080 / 4.0

    def seated(pen, a, tt, x, yf, hh, light=LAMP):
        seat = kitchen(pen, x, yf, hh)
        CH.draw(pen, 'winks', x, seat, hh, a.at(tt), light=light)
    strip(cv, pen, 'winks', lambda a: (a.sit_dummy(), a.doll_turn(0.2, 0.9, 1.2, 4)), [0.1, 0.5, 0.85, 1.2, 1.6], 0, rh,
          'doll_turn: the head ratchets in 4 hard snaps', paint=seated, h=rh * 0.68)

    def back_turn(pen, a, tt, x, yf, hh):
        seat = kitchen(pen, x, yf, hh)
        CH.draw(pen, 'winks', x, seat, hh, a.at(tt), light=LAMP)
    strip(cv, pen, 'winks', lambda a: (a.sit_dummy(), a.set(-9, None, 0.1, turn=2.0, h_turn=0.0), a.head_turn_180(0.3, 2.6, 0.0, -2.0)),
          [0.2, 1.0, 1.6, 2.2, 3.1], rh, rh, 'head_turn_180: back to us, the head comes all the way round', paint=back_turn, h=rh * 0.68)

    def face(pen, a, tt, x, yf, hh):
        _bg(pen, x - 200, yf - rh, 400, rh, '#3a3040', '#121016')
        CH.draw_bust(pen, 'winks', x, yf - rh * 0.42, 0.26, a.at(tt), light=LAMP)
    strip(cv, pen, 'winks', lambda a: (a.jaw_drop(0.3, 1.0), a.clack(2.6, 1.6)), [0.2, 0.45, 1.2, 2.2, 2.7], 2 * rh, rh,
          'jaw_drop, then "it closes, very slowly. Clack."', paint=face)

    def tablepaint(pen, a, tt, x, yf, hh):
        seat = kitchen(pen, x, yf, hh)
        CH.draw(pen, 'winks', x, seat, hh, a.at(tt), light=LAMP)
        table(pen, x, yf - 0.88 * hh, hh * 1.1, 0.86 * hh)
        CH.draw_arm(pen, 'winks', 1, a.at(tt), x=x, y_feet=seat, height=hh, light=LAMP)
        CH.draw_arm(pen, 'winks', -1, a.at(tt), x=x, y_feet=seat, height=hh, light=LAMP)
    strip(cv, pen, 'winks', lambda a: (a.sit_dummy(hands='table'), a.glove_lift(0.3, 1, 0.35, 1.2), a.fingers_curl(1.8, -1), a.elbow_bend(2.4, -1)),
          [0.2, 0.8, 1.5, 2.1, 2.7], 3 * rh, rh, 'glove_lift, fingers_curl, elbow_bend (the laughter waves)', paint=tablepaint, h=rh * 0.68)
    save(surf, 'winks_acting')


def sheet_winks_acting2():
    surf, cv, pen = canvas()
    rh = 1080 / 4.0

    def standp(pen, a, tt, x, yf, hh):
        seat = kitchen(pen, x, yf, hh)
        CH.draw(pen, 'winks', x, seat, hh, a.at(tt), light=LAMP)
        table(pen, x, yf - 0.88 * hh, hh * 1.1, 0.86 * hh)
        for sd in (-1, 1): CH.draw_arm(pen, 'winks', sd, a.at(tt), x=x, y_feet=seat, height=hh, light=LAMP)
    strip(cv, pen, 'winks', lambda a: (a.sit_dummy(-1e9, 0.0, hands='table'), a.stand_on_chair(0.3, 1.6)), [0.2, 0.8, 1.3, 1.8, 2.3], 0, rh,
          'stand_on_chair (hands flat on the table, jerky)', paint=standp, h=rh * 0.5)

    def torchp(pen, a, tt, x, yf, hh, lens=False):
        if lens: stairs(pen, x, yf, 380, rh * 0.18, 4)
        y_ = yf - (rh * 0.54 if lens else 0)
        P = a.at(tt)
        if lens: base = y_
        else: base = kitchen(pen, x, yf, hh)
        CH.draw(pen, 'winks', x, base, hh, P, light=NIGHT)
        side = -1 if lens else 1
        lx, ly, ang = CH.torch_pos('winks', P, side, x=x, y_feet=base, height=hh)
        CH.draw_torch_beam(pen, lx, ly, ang, 300, a=P.torch, lens=P.torch_lens, t=tt)
    strip(cv, pen, 'winks', lambda a: (a.sit_dummy(), a.torch_on(0.6, 0.0, 1, hold='up'), a.torch_sweep(1.4, 2.4, 0.0, -40.0)), [0.2, 0.55, 0.8, 1.8, 2.6], rh, rh,
          'torch_on + torch_sweep (a knee-high beam in the dark)', paint=torchp, h=rh * 0.68)
    strip(cv, pen, 'winks', lambda a: (a.sit_dummy(), a.torch_on(0.5, 0.0, -1, hold='lens')), [0.1, 0.45, 0.6, 1.2, 2.0], 2 * rh, rh,
          'on the stairs, three steps up: the torch in your face', paint=lambda pen, a, tt, x, yf, hh: torchp(pen, a, tt, x, yf, hh, True), h=rh * 0.62)

    def floorp(pen, a, tt, x, yf, hh):
        rug(pen, x, yf - 6, 320)
        CH.draw(pen, 'winks', x - 20, yf - 10, hh, a.at(tt), light=LAMP)
    strip(cv, pen, 'winks', lambda a: a.fall_face_down(0.4, 0.45), [0.2, 0.5, 0.7, 0.85, 1.4], 3 * rh, rh,
          'fall_face_down: on the rug, silent', paint=floorp, h=rh * 0.75)
    save(surf, 'winks_acting2')


def sheet_winks_acting3():
    surf, cv, pen = canvas()
    rh = 1080 / 3.0

    def shelf(pen, a, tt, x, yf, hh):
        bookcase(pen, x, yf - rh * 0.4, 320, rh * 0.4)
        P = a.at(tt)
        CH.draw(pen, 'winks', x, yf - rh * 0.4, hh, P, light=TORCH)
    strip(cv, pen, 'winks', lambda a: (a.sit_dummy(hands='limp'), a.torch_on(0.0, 0.0, 1, hold='chin'),
                                       a.talk([(417.85, 418.69, "We're leaving"), (419.45, 420.38, 'Get your shoes')])),
          [417.9, 418.1, 418.3, 419.6, 419.9], 0, rh, 'on top of the bookcase, flashlight under his chin, jaw going (Mom\'s voice, 6:57)', paint=shelf, h=rh * 0.6)

    def arms(pen, a, tt, x, yf, hh):
        y = CH.Acting('you', seed=2); y.hold_dummy(); y.expr('fear', 0)
        CH.draw_carry(pen, 'you', x - hh * 0.1, yf + hh * 0.9, hh * 1.9, y.at(tt), a.at(tt), m=1.74, light=LAMP)
    strip(cv, pen, 'winks', lambda a: (a.carried(), a.smile_arc(None), a.smile_stage(-9, 'owen'), a.lids(-9, 655.6, 1.0, 0.05), a.eyes_open(655.6, 1.8),
                                       a.try_wink(659.2, 0.7, 1.2)),
          [655.0, 656.4, 657.6, 659.3, 660.4], rh, rh, 'in your arms: he opens his eyes, tries to wink - both lids close (Owen inside)', paint=arms, h=rh * 0.95)

    def show(pen, a, tt, x, yf, hh):
        w = CH.Acting('walter74', seed=2); w.vent_pose(side=1); w.showman(270, 280); w.set(-9, None, 0.1, turn=0.15)
        pen.fill(rect(x - 70, yf - hh * 0.34, 60, hh * 0.34), '#c9a24a')
        CH.draw_lap(pen, 'walter74', x - 60, yf, hh * 1.05, w.at(tt), a.at(tt), side=1, m=1.78, light=TV)
    strip(cv, pen, 'winks', lambda a: (a.smile_arc(CH.WINKS_TAPE_ARC), a.sit_dummy(), a.puppet(270.0, 280.0, look=-1),
                                       a.talk([(271.29, 274.38, "Why does a dummy always sit on the ventriloquist's knee"), (277.45, 278.77, "Because he can't stand him")])),
          [271.5, 272.2, 273.0, 277.6, 278.2], 2 * rh, rh, 'the 1974 tape: worked on Walter\'s knee (puppet), the jaw talks, Walter\'s lips never move', paint=show, h=rh * 0.85)
    save(surf, 'winks_acting3')


def sheet_family_faces():
    surf, cv, pen = canvas()
    title(cv, 'GRANDPA, WALTER, MOM, YOU, OWEN: FACES AND BEATS', 'Grandpa\'s smile is a little too still and his lips barely move; the real Walter is lucid and terrified; '
          'young Walter\'s lips never move')
    busts = [
        ('grandpa', lambda a: a.expr('still_smile', 0), 2.0, 'Grandpa: the too-still smile (memory)', LAMP),
        ('grandpa_bed', lambda a: (a.in_bed(), a.set(0, None, 0.1, smile=0.2, m_press=0.4, pupil=0.7, still=0.8)), 2.0, 'Grandpa in the hospital bed', HOSP),
        ('walter', lambda a: (a.expr('lucid', 0), a.talk([(1.8, 3.2, 'It was never me')], env=None, words=None, intensity=0.5)), 2.6, 'the real Walter: "It was never me."', HOSP),
        ('walter74', lambda a: a.showman(-9, 99), 2.0, 'young Walter, 1974: the showman smile', TV),
        ('mom', lambda a: (a.laugh_soft(1.0)), 1.6, 'Mom laughs at the letter', LAMP),
        ('mom', lambda a: (a.smell_mug(0.0, None, -1, 1.0)), 2.6, 'Mom: the colour leaves her face', LAMP),
        ('you', lambda a: a.expr('fear', 0), 2.0, 'you: fear', NIGHT),
        ('owen', lambda a: a.expr('kid_grin', 0), 2.0, 'Owen grinning (the gap tooth)', LAMP),
        ('owen', lambda a: a.try_wink_kid(1.9, 0.6), 2.1, 'Owen tries to wink: both eyes close', LAMP),
        ('owen', lambda a: (a.cry(0), a.expr('scream', 0.5, None)), 2.0, 'Owen: his hand won\'t come out', NIGHT),
        ('owen_new', lambda a: a.doorway_smile(0.0, 2.0), 3.0, 'the new Owen: the doorway smile', NIGHT),
        ('owen_new', lambda a: a.hold_mug(sip=[1.0]), 1.9, 'two sugars', LAMP),
    ]
    for i, (who, act, tt, lab, lt) in enumerate(busts):
        cx = 160 + (i % 6) * 320; cy = 330 + (i // 6) * 430
        a = CH.Acting(who, seed=6); act(a)
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(cx - 156, cy - 210, 312, 420))
        _bg(pen, cx - 160, cy - 220, 320, 440)
        CH.draw_bust(pen, who, cx, cy - 10, 0.36 if who not in ('owen', 'owen_new') else 0.32, a.at(tt), light=lt)
        cv.restore()
        pen.fill(rect(cx - 156, cy + 180, 312, 30), '#000000', 150)
        label(cv, lab, cx, cy + 201, 14)
    save(surf, 'family_faces')


def sheet_family_acting():
    surf, cv, pen = canvas()
    rh = 1080 / 4.0

    def latch(pen, a, tt, x, yf, hh):
        P = a.at(tt)
        CH.draw(pen, 'mom', x, yf, hh, P, light=LAMP)
        case(pen, x, yf - hh * 0.4, hh * 0.55, hh * 0.12)
        for sd in (-1, 1): CH.draw_arm(pen, 'mom', sd, P, x=x, y_feet=yf, height=hh, light=LAMP)
    strip(cv, pen, 'mom', lambda a: (a.set(-9, None, 0.1, turn=0.0), a.open_latches(0.6)), [0.0, 0.4, 0.62, 0.85, 1.6], 0, rh,
          'Mom: open_latches (two brass pops)', paint=latch, light=LAMP, h=rh * 0.85)
    strip(cv, pen, 'mom', lambda a: (a.set(-9, None, 0.1, turn=0.3), a.smell_mug(0.3, 3.0, -1, 1.7), a.hand_to_mouth(3.0, None, side=1)),
          [0.1, 0.9, 1.6, 2.4, 3.6], rh, rh, 'Mom: smell_mug -> pale -> hand_to_mouth', light=LAMP, h=rh * 0.85)

    def pullp(pen, a, tt, x, yf, hh):
        o = CH.Acting('owen', seed=2); o.vent_pose(side=-1); o.cry(0.0); o.expr('scream', 0.4, None); o.set(-9, None, 0.1, turn=-0.2)
        d = CH.Acting('winks', seed=3); d.sit_dummy(); d.smile_stage(-9, 5)
        P = a.at(tt)
        jerk = max(0.0, -P.lean - 0.08) * 0.6
        armchair(pen, x + hh * 0.3, yf - hh * 0.18, hh * 0.55)
        dx_, dy_, dh_ = CH.draw_lap(pen, 'owen', x + hh * 0.3, yf, hh * 0.78, o.at(tt), d.at(tt), side=-1, m=1.32, light=LAMP, dx=-jerk * hh * 0.12)
        Pg = a.at(1.0)                                   # place her once, from the grab pose
        (w1, _), (w2, _) = CH.hand_pos('mom', Pg, 1, x=0, y_feet=yf, height=hh), CH.hand_pos('mom', Pg, -1, x=0, y_feet=yf, height=hh)
        mx = dx_ - max(w1[0], w2[0]) + dh_ * 0.08
        CH.draw(pen, 'mom', mx, yf, hh, P, light=LAMP)
    strip(cv, pen, 'mom', lambda a: (a.set(-9, None, 0.1, turn=0.6), a.pull_dummy(0.3, 2.6, 3), a.scream(0.3, 2.6)), [0.1, 0.75, 1.3, 1.85, 2.4], 2 * rh, rh,
          'Mom: pull_dummy + scream (Owen\'s hand won\'t come out)', paint=pullp, h=rh * 0.85)
    strip(cv, pen, 'mom', lambda a: (a.set(-9, None, 0.1, turn=-0.2), a.grab_keys(0.3, side=1), a.expr('fear', 1.2)), [0.1, 0.5, 0.8, 1.2, 1.8], 3 * rh, rh,
          'Mom: grab_keys ("We\'re leaving.")', light=LAMP, h=rh * 0.85)
    save(surf, 'family_acting')


def sheet_family_acting2():
    surf, cv, pen = canvas()
    rh = 1080 / 4.0

    def couch(pen, a, tt, x, yf, hh):
        armchair(pen, x, yf - hh * 0.3, hh * 0.62, '#4a5a6a')
        CH.draw(pen, 'owen', x, yf, hh, a.at(tt), light=LAMP)
    strip(cv, pen, 'owen', lambda a: (a.sit(-9), a.set(-9, None, 0.1, turn=0.4), a.snort(0.5)), [0.2, 0.52, 0.7, 1.0, 1.8], 0, rh,
          'Owen: snort (he can\'t help it, he\'s nine)', paint=couch, h=rh * 0.85)

    def shush(pen, a, tt, x, yf, hh):
        y = CH.Acting('you', seed=2); y.set(-9, None, 0.1, turn=0.5); y.clamp_mouth(0.4, None, side=1, reach_x=0.75); y.expr('fear', 0)
        CH.draw(pen, 'you', x - hh * 0.28, yf, hh * 1.32, y.at(tt), light=LAMP)
        CH.draw(pen, 'owen', x + hh * 0.12, yf, hh, a.at(tt), light=LAMP)
        if tt > 0.5: CH.draw_arm(pen, 'you', 1, y.at(tt), x=x - hh * 0.28, y_feet=yf, height=hh * 1.32, light=LAMP)
    strip(cv, pen, 'owen', lambda a: (a.set(-9, None, 0.1, turn=-0.3), a.expr('fear', 0.4), a.set(0.4, None, 0.2, still=0.8, wide=0.8)), [0.1, 0.5, 0.8, 1.4, 2.0], rh, rh,
          'you clamp_mouth over Owen\'s mouth: nobody laughs, nobody breathes', paint=shush, h=rh * 0.6)
    strip(cv, pen, 'owen', lambda a: (a.set(-9, None, 0.1, turn=0.3, sit=1.0), a.jump_hug(0.4)), [0.2, 0.45, 0.6, 0.8, 1.3], 2 * rh, rh,
          'Owen: jump_hug ("It worked! He\'s asleep!")', light=LAMP, h=rh * 0.85)
    strip(cv, pen, 'owen_new', lambda a: (a.set(-9, None, 0.1, turn=-0.25), a.wave(0.3, 3.0, side=1)), [0.1, 0.5, 0.8, 1.1, 1.4], 3 * rh, rh,
          'the new Owen at the window: wave as the van pulls away', light=dict(rim='#ffe6b0', rim_a=80, side=1, key=0.2), h=rh * 0.85)
    save(surf, 'family_acting2')


def sheet_family_acting3():
    surf, cv, pen = canvas()
    rh = 1080 / 4.0

    def stairs_grab(pen, a, tt, x, yf, hh):
        d = CH.Acting('winks', seed=3); d.sit_dummy(); d.smile_stage(-9, 3)
        stairs(pen, x + hh * 0.18, yf, 260, hh * 0.1, 4)
        CH.draw(pen, 'winks', x + hh * 0.18, yf - hh * 0.2, hh * 0.47, d.at(tt), light=NIGHT)
        CH.draw(pen, 'you', x - hh * 0.12, yf, hh, a.at(tt), light=NIGHT)
    strip(cv, pen, 'you', lambda a: (a.set(-9, None, 0.1, turn=0.6), a.expr('fear', 0), a.grab_dummy(0.4)), [0.1, 0.45, 0.65, 1.0, 1.6], 0, rh,
          'you: grab_dummy (on the stairs)', paint=stairs_grab, h=rh * 0.85)

    def slot(pen, a, tt, x, yf, hh):
        d = CH.Acting('winks', seed=3); d.sit_dummy(); d.set(-9, None, 0.1, turn=0.3)
        CH.draw(pen, 'you', x - hh * 0.05, yf, hh, a.at(tt), light=NIGHT)
        stairs(pen, x + hh * 0.2, yf, 200, hh * 0.1, 3)
        CH.draw(pen, 'winks', x + hh * 0.2, yf - hh * 0.3, hh * 0.47, d.at(tt), light=NIGHT)
    strip(cv, pen, 'you', lambda a: (a.set(-9, None, 0.1, turn=0.6), a.expr('fear', 0), a.hand_inside(0.3, None, side=1), a.squeezed([1.6, 2.0, 2.4])),
          [0.1, 0.6, 1.2, 1.65, 2.45], rh, rh, 'you: hand_inside the slot, squeezed x3 ("I love you")', paint=slot, h=rh * 0.85)

    def kneelp(pen, a, tt, x, yf, hh):
        armchair(pen, x + hh * 0.35, yf - hh * 0.2, hh * 0.5)
        CH.draw(pen, 'you', x - hh * 0.15, yf, hh, a.at(tt), light=LAMP)
    strip(cv, pen, 'you', lambda a: (a.set(-9, None, 0.1, turn=0.6), a.expr('nervous', 0), a.kneel(0.3)), [0.1, 0.5, 0.8, 1.2, 1.8], 2 * rh, rh,
          'you: kneel in front of Owen\'s chair', paint=kneelp, h=rh * 0.85)

    def tuck(pen, a, tt, x, yf, hh):
        CH.draw(pen, 'grandpa', x, yf, hh, a.at(tt), light=LAMP)
    strip(cv, pen, 'grandpa', lambda a: (a.set(-9, None, 0.1, turn=0.45, smile=0.35, m_press=0.3), a.tuck_in(0.3), a.squeeze_hand(1.4, 3, 0.42, 1),
                                          a.talk([(2.8, 4.4, 'See you in the morning, kiddo')], env=None, words=None)),
          [0.1, 0.8, 1.45, 2.3, 3.4], 3 * rh, rh, 'Grandpa (memory): tuck_in, squeeze_hand x3, "See you in the morning, kiddo" (lips barely move)',
          paint=tuck, h=rh * 0.85)
    save(surf, 'family_acting3')


def sheet_laps():
    """The composites: the hospital (Grandpa in bed, the dummy on his lap, his hand inside; the real Walter grabs your
    wrist), the 1974 show, Owen in Grandpa's armchair with his hand inside, you holding him."""
    surf, cv, pen = canvas()
    title(cv, 'LAPS AND ARMS: draw_lap / draw_carry', 'the operator\'s hand goes in at the back (hidden by the figure), the free arm is drawn over him')
    # hospital
    x0, y0, w, h = 0, 110, 960, 480
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x0 + 4, y0, w - 8, h - 4)); _bg(pen, x0, y0, w, h, '#2e3a3a', '#101616')
    g = CH.Acting('grandpa_bed', seed=1); g.in_bed(); g.vent_pose(side=1); g.set(-9, None, 0.1, turn=0.15, lean=-0.18, smile=0.25, m_press=0.4)
    d = CH.Acting('winks', seed=2); d.sit_dummy(); d.puppet(0, 9, look=-1)
    bed(pen, 260, 560, 460, 300)
    CH.draw_lap(pen, 'grandpa_bed', 250, 600, 400, g.at(2.0), d.at(2.0), side=1, m=1.72, light=HOSP, between=lambda pen: blanket(pen, 300, 590, 460, 140))
    wl = CH.Acting('walter', seed=1); wl.in_bed(); wl.set(-9, None, 0.1, turn=0.35, lean=-0.1); wl.expr('fear', 0); wl.grab_wrist(0.5, None, side=-1)
    yu = CH.Acting('you', seed=2); yu.set(-9, None, 0.1, turn=-0.5); yu.expr('fear', 0)
    bed(pen, 700, 560, 360, 300)
    CH.draw(pen, 'walter', 690, 600, 400, wl.at(1.0), light=HOSP)
    blanket(pen, 720, 590, 360, 140)
    CH.draw(pen, 'you', 900, 660, 540, yu.at(1.0), light=HOSP)
    CH.draw_arm(pen, 'walter', -1, wl.at(1.0), x=690, y_feet=600, height=400, light=HOSP)
    cv.restore()
    pen.fill(rect(x0 + 4, y0 + h - 40, w - 8, 36), '#000000', 160)
    label(cv, 'the hospital: Grandpa works him one last time  /  the real Walter grabs your wrist', x0 + w / 2, y0 + h - 14, 16)
    # 1974
    x0 = 960
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x0 + 4, y0, w - 8, h - 4)); _bg(pen, x0, y0, w, h, '#2c3a4e', '#0f141c')
    w74 = CH.Acting('walter74', seed=2); w74.vent_pose(side=1); w74.showman(0, 9); w74.set(-9, None, 0.1, turn=0.15)
    d2 = CH.Acting('winks', seed=3, arc=CH.WINKS_TAPE_ARC); d2.sit_dummy(); d2.puppet(0, 9, look=-1); d2.jaw_hang(1.0, 0.7)
    pen.fill(rect(x0 + 380, 440, 70, 160), '#c9a24a'); pen.line(rect(x0 + 380, 440, 70, 160), 4)
    CH.draw_lap(pen, 'walter74', x0 + 400, 600, 470, w74.at(2.0), d2.at(2.0), side=1, m=1.78, light=TV)
    cv.restore()
    label(cv, 'Saturday Morning with Walter Kemp, 1974: the jaw talks, Walter\'s lips stay shut', x0 + w / 2, y0 + h - 14, 16)
    # Owen in the den
    x0, y0 = 0, 590
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x0 + 4, y0 + 4, w - 8, h - 8)); _bg(pen, x0, y0, w, h, '#33282a', '#120e10')
    o = CH.Acting('owen', seed=2); o.vent_pose(side=1); o.expr('talk_smile', 0); o.set(-9, None, 0.1, turn=0.15)
    d3 = CH.Acting('winks', seed=3); d3.sit_dummy(); d3.smile_stage(-9, 5); d3.set(-9, None, 0.1, h_turn=-0.35)
    armchair(pen, 440, 900, 330)
    CH.draw_lap(pen, 'owen', 420, 1060, 450, o.at(2.0), d3.at(2.0), side=1, m=1.32, light=LAMP)
    cv.restore()
    label(cv, 'Owen in Grandpa\'s armchair: "Look! I\'m doing it!"', x0 + w / 2, y0 + h - 18, 16)
    # in your arms
    x0 = 960
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x0 + 4, y0 + 4, w - 8, h - 8)); _bg(pen, x0, y0, w, h, '#2a2e3a', '#101218')
    yu = CH.Acting('you', seed=2); yu.hold_dummy(); yu.expr('fear', 0)
    d4 = CH.Acting('winks', seed=3); d4.carried(); d4.smile_stage(-9, 'owen')
    CH.draw_carry(pen, 'you', x0 + 380, 1240, 760, yu.at(1.0), d4.at(1.0), m=1.74, light=LAMP)
    d5 = CH.Acting('winks', seed=3); d5.face_down()
    rug(pen, x0 + 760, 1020, 300)
    CH.draw(pen, 'winks', x0 + 740, 1010, 200, d5.at(1.0), light=LAMP)
    cv.restore()
    label(cv, 'in your arms (draw_carry)   /   face down on the rug', x0 + w / 2, y0 + h - 18, 16)
    save(surf, 'laps')


def sheet_props():
    surf, cv, pen = canvas()
    title(cv, 'PROPS: THE FLASHLIGHT, THE MUG, THE KEYS', 'draw_prop / torch_pos / draw_torch_beam (the beam lives on a light layer)')
    CH.draw_prop(pen, 'flashlight', 200, 400, 300, pose=CH.Pose(torch=0.0))
    label(cv, 'torch off', 200, 600, 18)
    CH.draw_prop(pen, 'flashlight', 420, 400, 300, pose=CH.Pose(torch=1.0))
    CH.draw_torch_beam(pen, 420, 270, 0.0, 300, a=0.9)
    label(cv, 'on (beam up)', 420, 600, 18)
    CH.draw_torch_beam(pen, 680, 400, 0.0, 0, a=1.0, lens=1.0)
    label(cv, 'pointed at the lens', 680, 600, 18)
    for i, st in enumerate((1.0, 0.4)):
        CH.draw_prop(pen, 'mug', 950 + i * 260, 400, 240, pose=CH.Pose(steam=st), t=1.0 + i)
        label(cv, 'the mug, steam %.1f' % st, 950 + i * 260, 600, 18)
    CH.draw_prop(pen, 'key', 1550, 400, 220)
    label(cv, 'Mom\'s keys', 1550, 600, 18)
    a = CH.Acting('winks', seed=1); a.set(-9, None, 0.1, turn=2.0); a.paper_out(0.0, 1.0)
    CH.draw(pen, 'winks', 400, 1040, 330, a.at(2.0), light=LAMP)
    label(cv, 'the P.S. slides out of the slot (slot_paper)', 400, 1068, 16)
    b = CH.Acting('winks', seed=1); b.face_down()
    rug(pen, 1000, 1000, 420)
    CH.draw(pen, 'winks', 980, 990, 330, b.at(1.0), light=LAMP)
    label(cv, 'face down on the rug (lie 1)', 1000, 1068, 16)
    save(surf, 'props')


# ------------------------------------------------------------------------------------------------ the sync clips
def sync_clips():
    """Two 4 s clips at 960x540, 60 fps, with the voice: Mister Winks's joke (the jaw, 271.0-275.0) and Owen's line
    (534.5-538.5). Also writes sync.json (correlation of the jaw / mouth opening with the voice envelope and the best
    lag) and sync_plot.jpg."""
    env = CH.voice_envelope()
    res = {}
    specs = [('jaw_sync_winks', 'winks', 271.0, 275.0, [(271.29, 274.38, "Why does a dummy always sit on the ventriloquist's knee")], 'jaw', 'K'),
             ('lip_sync_owen', 'owen', 534.5, 538.5, [(534.69, 535.09, 'Look'), (535.09, 535.86, "I'm doing it"), (536.05, 537.94, 'Grandpa said his mouth was stuck')], 'm_open', 'O')]
    plot = np.full((540, 960, 3), 28, np.uint8)
    for k, (name, who, t0, t1, iv, key, code) in enumerate(specs):
        a = CH.Acting(who, seed=5)
        if who == 'winks': a.sit_dummy(); a.puppet(t0, t1, look=-1, rate=0.6)
        else: a.expr('talk_smile', t0 - 1); a.set(-9, None, 0.1, turn=0.15)
        a.talk(iv)
        fr = []
        set_render_size(960, 540)
        ts = np.arange(t0, t1, 1 / 60.0)
        for i, tt in enumerate(ts):
            surf = skia.Surface(CFG.rw, CFG.rh); cv = surf.getCanvas(); cv.clear(skia.Color(*BG)); cv.scale(CFG.k, CFG.k); pen = Pen(cv)
            _bg(pen, 0, 0, 1920, 1080, '#3a3040' if who == 'winks' else '#33302a', '#121016')
            CH.draw_bust(pen, who, 960, 600, 0.95 if who == 'winks' else 0.85, a.at(float(tt)), light=LAMP)
            text(cv, '%s  %.2f s' % (name, tt), 40, 60, 800, 30, '#ffffff', 255, 0.02, 'left')
            fr.append(surf.makeImageSnapshot().toarray()[:, :, :3].copy())
        p = os.path.join(OUT, name + '.mp4')
        raw = os.path.join(OUT, name + '_raw.mp4')
        h_, w_ = fr[0].shape[:2]
        vw = cv2.VideoWriter(raw, cv2.VideoWriter_fourcc(*'mp4v'), 60, (w_, h_))
        for f in fr: vw.write(f)
        vw.release()
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', raw, '-ss', '%.3f' % t0, '-t', '%.3f' % (t1 - t0), '-i', CH.VOICE_WAV,
                        '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                        '-shortest', p], check=True)
        os.remove(raw)
        print('wrote', p)
        tq = np.arange(t0, t1, 0.01)
        mo = np.array([getattr(a.at(float(x)), key) for x in tq])
        ev = np.array([10 ** (CH._env_db(env, float(x)) / 20.0) for x in tq])
        r0 = float(np.corrcoef(mo, ev)[0, 1])
        lags = list(range(-12, 13))
        rs = [float(np.corrcoef(mo[max(0, l):len(mo) + min(0, l)], ev[max(0, -l):len(ev) - max(0, l)])[0, 1]) for l in lags]
        best = lags[int(np.argmax(rs))]
        clacks = [e['t'] for e in a.events if e['name'] == 'dummy_clack']
        res[name] = dict(r=round(r0, 3), best_lag_s=best * 0.01, r_best=round(max(rs), 3), clacks=len(clacks))
        # plot: envelope (green) and the opening (orange)
        y0 = 40 + k * 250
        cv2.putText(plot, '%s  r=%.2f  best lag %+.2f s  clacks %d' % (name, r0, best * 0.01, len(clacks)), (20, y0 + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (230, 230, 230), 1)
        evn = ev / max(ev.max(), 1e-6); mon = mo / max(mo.max(), 1e-6)
        xs = np.linspace(20, 940, len(tq)).astype(int)
        for arr, c_ in ((evn, (120, 210, 140)), (mon, (60, 160, 240))):
            pts = np.stack([xs, (y0 + 220 - arr * 190).astype(int)], 1)
            cv2.polylines(plot, [pts], False, c_, 2)
        for tc in clacks:
            xc = int(20 + (tc - t0) / (t1 - t0) * 920)
            cv2.line(plot, (xc, y0 + 25), (xc, y0 + 225), (90, 90, 255), 1)
    cv2.imwrite(os.path.join(OUT, 'sync_plot.jpg'), plot, [cv2.IMWRITE_JPEG_QUALITY, 90])
    json.dump(res, open(os.path.join(OUT, 'sync.json'), 'w'), indent=1)
    print(json.dumps(res))


SHEETS = dict(lineup=sheet_lineup, winks_turnaround=sheet_winks_turnaround, winks_faces=sheet_winks_faces, winks_arc=sheet_winks_arc,
              winks_acting=sheet_winks_acting, winks_acting2=sheet_winks_acting2, winks_acting3=sheet_winks_acting3,
              family_faces=sheet_family_faces, family_acting=sheet_family_acting, family_acting2=sheet_family_acting2,
              family_acting3=sheet_family_acting3, laps=sheet_laps, props=sheet_props)

if __name__ == '__main__':
    names = sys.argv[1:] or list(SHEETS)
    for n in names:
        t0 = time.time()
        if n == 'sync': sync_clips()
        else: SHEETS[n]()
        print('  %s %.1f s' % (n, time.time() - t0))
