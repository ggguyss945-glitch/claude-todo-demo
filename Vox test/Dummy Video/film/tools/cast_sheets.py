"""cast_sheets.py: model and acting sheets for the delivery film's cast (characters.py), written to W/cast/.

    cd "Vox test/Delivery Video/film" && python3 tools/cast_sheets.py [names...]     (default: all sheets)

Sheets (1920x1080 JPEG): lineup, driver_turnaround, driver_smile_arc, driver_doorbell (through the engine's doorbell
lens on the engine demo porch, IR included), driver_acting, family_acting, lily_window, props.
"""
import os, sys, math, time
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


def paste(cv, arr, x, y, w, h):
    """Draw an RGB / BGR uint8 array into the design-space rect."""
    a = np.ascontiguousarray(np.dstack([arr, np.full(arr.shape[:2], 255, np.uint8)]))
    im = skia.Image.fromarray(a, skia.kBGRA_8888_ColorType)
    cv.drawImageRect(im, skia.Rect.MakeXYWH(x, y, w, h), skia.SamplingOptions(skia.FilterMode.kLinear))


PORCH = dict(rim='#ffcf8f', rim_a=70, side=-1, key=0.2)
NIGHT = dict(rim='#9fb6ff', rim_a=60, side=1)


# ------------------------------------------------------------------------------------------------ sheets
def sheet_lineup():
    surf, cv, pen = canvas()
    floor(pen, 930)
    title(cv, 'DELIVERY CAST: LINEUP TO SCALE', 'driver 1.85 m  /  dad 1.82 m (21 years ago)  /  you 1.80 m  /  mom 1.62 m  /  Lily 8, 1.28 m')
    H = 760.0 / 1.85
    items = [('driver', 1.85, 'driver', 'THE DRIVER'), ('dad', 1.82, 'dad', 'DAD (MEMORY)'), ('you', 1.80, 'you', 'YOU (SOCKS)'),
             ('mom', 1.62, 'mom', 'MOM (ROBE)'), ('lily', 1.28, 'lily', 'LILY, 8')]
    xs = [260, 610, 960, 1310, 1640]
    for (who, m, _, lab), x in zip(items, xs):
        a = CH.Acting(who, seed=4)
        if who == 'driver': a.carry_tablet()
        if who == 'mom': a.expr('nervous', 0)
        if who == 'you': a.expr('nervous', 0)
        if who == 'lily': a.sleepy(0)
        tt = 120.0 if who == 'driver' else 2.0
        CH.draw(pen, who, x, 930, m * H, a.at(tt), light=PORCH if who == 'driver' else NIGHT)
        label(cv, lab, x, 975, 22)
    save(surf, 'lineup')


def sheet_turnaround():
    surf, cv, pen = canvas()
    floor(pen, 960)
    title(cv, 'THE DRIVER: TURNAROUND', 'Nightline courier: brown shirt, NIGHTLINE crescent patch, name tag NO. 307, brown cap with a crescent, work boots, '
          'a ring of keys on a carabiner, the handheld on a coiled tether')
    views = [(0.0, 'FRONT'), (-0.5, '3/4 LEFT'), (0.5, '3/4 RIGHT'), (1.0, 'PROFILE'), (2.0, 'BACK')]
    for i, (yaw, lab) in enumerate(views):
        a = CH.Acting('driver', seed=2); a.carry_tablet(); a.set(-10, None, 0.1, turn=yaw)
        x = 200 + i * 380
        CH.draw(pen, 'driver', x, 960, 800, a.at(120.0), light=PORCH)
        label(cv, lab, x, 1010, 22)
    save(surf, 'driver_turnaround')


def sheet_smile_arc():
    surf, cv, pen = canvas()
    title(cv, 'THE DRIVER: THE SMILE THAT KEEPS WIDENING (DRIVER_ARC, film time)',
          'never blinks; the eyes never smile; pupils shrink and whites grow with every stage; mouth lags the voice by 0.2 s')
    a = CH.Acting('driver', seed=1)
    a.eye_flash(371.0, 0.6)
    cells = [(30, 'S0  0:30  arrives'), (100, 'S1  1:06  "doesn\'t stop smiling"'), (160, 'S2  2:19  "just finish it"'),
             (200, 'S3  3:05  "wider now"'), (345, 'S4  5:41  leans close, "Ma\'am"'), (371.25, 'S4 + EYESHINE  6:11'),
             (441, 'OFF  7:16  "perfectly still"'), (465, 'S5  7:26  "wider than before"')]
    for i, (tt, lab) in enumerate(cells):
        cx = 240 + (i % 4) * 480; cy = 360 + (i // 4) * 480
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(cx - 236, cy - 238, 472, 470))
        pen.radial(rect(cx - 240, cy - 240, 480, 480), cx - 60, cy - 120, 420, [(0, '#3a2c22'), (1, '#121014')])
        CH.draw_bust(pen, 'driver', cx, cy, 0.52, a.at(tt), light=dict(PORCH, rim_a=80))
        cv.restore()
        pen.fill(rect(cx - 236, cy + 196, 472, 36), '#000000', 150)
        label(cv, lab, cx, cy + 221, 18)
    save(surf, 'driver_smile_arc')


def _doorbell_frames(part=1):
    """Six 960x540 frames through the engine doorbell lens on the engine demo porch, the driver at the door."""
    from engine import demo as D
    from engine.scene import Layer, render_frame
    from engine.camera import hold, push_in
    from engine import hud
    set_render_size(960, 540)
    frames = []
    specs = [
        ('S1, tablet in one hand', 100.0, lambda a: a.carry_tablet(), False, 'doorbell'),
        ('rings: his fingertip comes up at the lens', 100.0, lambda a: (a.carry_tablet(-1e9, 99.0), a.ring_bell(99.5)), False, 'doorbell'),
        ('holds the tablet up to the lens', 120.0, lambda a: a.hold_tablet_up(118.5, 125.0), False, 'doorbell'),
        ('S4 leans close: fisheye bulge', 345.0, lambda a: a.lean_close(341.0, 2.4, tilt=8), True, 'doorbell'),
        ('eyeshine (6:11)', 371.2, lambda a: (a.lean_close(341.0, 2.4, tilt=8, amount=0.6), a.eye_flash(371.0, 0.6)), True, 'doorbell'),
        ('OFF: head turns to the side yard', 441.0, lambda a: (a.carry_tablet(), a.slow_look_side(437.5, 3.0, side=-1)), False, 'doorbell'),
    ] if part == 1 else [
        ('IR night mode, S1', 100.0, lambda a: a.carry_tablet(), False, 'doorbell_ir'),
        ('IR + eyeshine', 371.2, lambda a: (a.carry_tablet(), a.eye_flash(371.0, 0.6)), False, 'doorbell_ir'),
        ('listens (4:20)', 262.0, lambda a: (a.carry_tablet(), a.listen_tilt(260.0, None, side=1)), False, 'doorbell'),
        ('S5 "wider than before" (7:26)', 450.0, lambda a: (a.carry_tablet(), a.lean_in(447.0, 2.0, amount=0.45)), True, 'doorbell'),
        ('takes a photo of the box: flash (7:45)', 466.5, lambda a: a.take_photo(465.6, side=1), False, 'doorbell'),
        ('walks back to the van (7:48)', 469.5, lambda a: (a.carry_tablet(), a.walk_away(468.6, 472.0)), False, 'doorbell'),
    ]
    for lab, tt, act, lean, lens in specs:
        a = CH.Acting('driver', seed=5)
        act(a)
        m = a.at

        def drv(pen, t, a=a):
            CH.draw(pen, 'driver', 960, 905, 700, a.at(t), light=PORCH, aim=(960, 470))
        box_lay = Layer(1.02, lambda pen, t: CH.draw_box(pen, 1290, 905, 600, None, t=t, view=-0.35), 'box', ref_depth=1.02)
        L = D.make_layers(car=False)
        L = [l for l in L if l.name != 'officer'] + [box_lay, Layer(a.depth(1.0) if lean else 1.0, drv, 'driver', ref_depth=1.0)]
        cam = push_in(tt - 1.0, tt + 3.0, 960, 500, 1.0, rate=0.02)
        img = render_frame(L, cam.at(tt), tt, int(tt * 60), lens=lens, grade='ir_night' if lens.endswith('ir') else 'doorbell_night',
                           hud=lambda cv_, t_: hud.doorbell_hud(cv_, t_, clock=(3, 9, 12), date='NOV 12', ir=lens.endswith('ir')))
        frames.append((lab, np.ascontiguousarray(img[:, :, ::-1])))          # render_frame returns RGB; the sheet is BGR
    return frames


def sheet_doorbell(part=1):
    frames = _doorbell_frames(part)
    surf, cv, pen = canvas()
    for i, (lab, img) in enumerate(frames):
        x = (i % 3) * 640; y = 110 + (i // 3) * 480
        paste(cv, img, x + 4, y + 4, 632, 356 * 632 / 632)
        label(cv, lab, x + 320, y + 392, 20)
    title(cv, 'THE DRIVER THROUGH THE DOORBELL LENS', 'engine doorbell fisheye + doorbell_night grade (the police film\'s doorbell look) on the engine demo porch')
    save(surf, 'driver_doorbell' if part == 1 else 'driver_doorbell2')


def _strip(cv, pen, who, act, times, y0, rh, lab, box=None, light=None, h=None, xs=None, stage=None, draw_extra=None):
    a = CH.Acting(who, seed=3)
    ev = act(a)
    n = len(times)
    cw = 1920.0 / n
    for i, tt in enumerate(times):
        x = cw * i + cw * 0.5 + (xs or 0)
        yf = y0 + rh - 14
        hh = h or rh * 0.8
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(cw * i + 2, y0 + 2, cw - 4, rh - 4))
        pen.linear(rect(cw * i, y0, cw, rh), 0, y0, 0, y0 + rh, [(0, '#232633'), (1, '#171920')])
        if box: CH.draw_box(pen, x + box[0], yf, hh * box[1], box[2](tt) if len(box) > 2 else None, t=tt, view=0.3)
        if draw_extra: draw_extra(pen, tt, x, yf, hh)
        CH.draw(pen, who, x, yf, hh, a.at(tt), light=light)
        cv.restore()
        label(cv, '%.1f' % tt, cw * i + 30, y0 + 24, 14, '#9aa3b8')
    label(cv, lab, 14, y0 + 24, 17, '#ffffff', 'left')
    def flat(x):
        if isinstance(x, dict): return [x]
        if isinstance(x, (list, tuple)): return [e for y in x for e in flat(y)]
        return []
    evs = flat(ev)
    if evs:
        label(cv, 'sfx: ' + ', '.join('%s %.2f' % (e['name'], e['t']) for e in evs[:4]), 14, y0 + rh - 8, 13, '#8fd4a8', 'left')
    return a


def sheet_driver_acting():
    surf, cv, pen = canvas()
    rh = 1080 / 4.0
    b = CH.BoxActing(2); b.tilt(0.4, 3.0, angle=-8, turn=0.7)
    _strip(cv, pen, 'driver', lambda a: a.tap_label(0.3, 2, side=1), [0.1, 0.75, 0.85, 1.2, 1.7], 0, rh,
           'tap_label (box beside him)', box=(rh * 0.42, 0.84), light=PORCH)
    _strip(cv, pen, 'driver', lambda a: (a.tilt_box(0.2, 2.5, side=1), a.look_at_box(1.6, 2.4, side=1)), [0.1, 0.8, 1.4, 2.0, 2.9], rh, rh,
           'tilt_box + look_at_box', box=(rh * 0.42, 0.84, lambda tt: b.at(tt)), light=PORCH)
    _strip(cv, pen, 'driver', lambda a: (a.carry_tablet(-1e9, 0.1), a.take_photo(0.3, side=1)), [0.1, 0.6, 1.18, 1.5, 2.2], 2 * rh, rh,
           'take_photo (flash at the door)', light=PORCH)
    _strip(cv, pen, 'driver', lambda a: (a.carry_tablet(), a.walk_away(0.6, 3.0), a.climb_in(3.1, 1.2)), [0.2, 0.7, 1.4, 2.4, 3.8], 3 * rh, rh,
           'walk_away + climb_in (van)', light=PORCH)
    title(cv, '', '')
    save(surf, 'driver_acting')


def sheet_driver_acting2():
    surf, cv, pen = canvas()
    rh = 1080 / 3.0
    _strip(cv, pen, 'driver', lambda a: (a.carry_tablet(), a.listen_tilt(0.3, 2.6, side=1)), [0.1, 0.8, 1.5, 2.4, 3.2], 0, rh,
           'listen_tilt ("like he\'s listening")', light=PORCH)
    _strip(cv, pen, 'driver', lambda a: (a.carry_tablet(), a.set_box_down(0.2, 1.8, side=1)), [0.1, 0.7, 1.15, 1.5, 2.3], rh, rh,
           'set_box_down', box=(rh * 0.42, 0.84), light=PORCH)

    def wall(pen, tt, x, yf, hh):
        pen.fill(rect(x - 200, yf - hh * 2.2, 400, hh * 2.2), '#2b3040')
        pen.fill(rect(x - 30, yf - hh * 1.85, 150, 110), '#f0c27a', 230)
        pen.line(rect(x - 30, yf - hh * 1.85, 150, 110), 4)
    _strip(cv, pen, 'driver', lambda a: a.reach_up(0.2, None, side=1, stretch=1.1, grow=2.2), [0.1, 0.7, 1.4, 2.1, 3.0], 2 * rh, rh,
           'reach_up(stretch=1.1): the too-long arm', light=PORCH, h=rh * 0.5)
    save(surf, 'driver_acting2')


def sheet_family():
    surf, cv, pen = canvas()
    title(cv, 'MOM, YOU, LILY, DAD: FACES AND BEATS', 'mom: the police mum in a robe, no glasses (she came down squinting)')
    busts = [
        ('mom', lambda a: a.squint_light(0), 2.0, 'mom: squint_light (stairs)'),
        ('mom', lambda a: a.expr('fear', 0), 2.0, 'mom: fear ("that\'s the van")'),
        ('mom', lambda a: (a.expr('cry', 0), a.hands_over_mouth(0.3)), 2.4, 'mom: hands_over_mouth + cry'),
        ('mom', lambda a: (a.expr('nervous', 0), a.reach_chain(0.2, None, side=1, reach=(60.0, -40.0, 250.0))), 1.4, 'mom: reach_chain, shaking'),
        ('you', lambda a: (a.expr('fear', 0), a.look_at_phone(0.2)), 1.2, 'you: look_at_phone (screen glow)'),
        ('lily', lambda a: a.sleepy(0), 2.0, 'Lily: sleepy'),
        ('lily', lambda a: a.expr('neutral', 0), 2.0, 'Lily'),
        ('dad', lambda a: a.expr('polite', 0), 2.0, 'dad, 21 years ago'),
    ]
    for i, (who, act, tt, lab) in enumerate(busts):
        cx = 240 + (i % 4) * 480; cy = 330 + (i // 4) * 470
        a = CH.Acting(who, seed=6); act(a)
        lt = dict(NIGHT)
        if lab.startswith('you'): lt = dict(under='#bcd2ff', under_a=120, rim='#9fb6ff', rim_a=50)
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(cx - 236, cy - 220, 472, 455))
        pen.radial(rect(cx - 240, cy - 240, 480, 480), cx, cy - 80, 420, [(0, '#2c3242'), (1, '#111318')])
        CH.draw_bust(pen, who, cx, cy, 0.5 if who != 'lily' else 0.46, a.at(tt), light=lt)
        cv.restore()
        pen.fill(rect(cx - 236, cy + 200, 472, 34), '#000000', 150)
        label(cv, lab, cx, cy + 224, 17)
    save(surf, 'family_faces')


def sheet_family_acting():
    surf, cv, pen = canvas()
    rh = 1080 / 4.0
    _strip(cv, pen, 'mom', lambda a: (a.expr('fear', 0), a.reach_chain(0.3, 2.2, side=1)), [0.1, 0.9, 1.6, 2.4, 3.0], 0, rh,
           'mom: reach_chain -> let go (shaking hand)', light=NIGHT)
    _strip(cv, pen, 'mom', lambda a: (a.expr('sad', 0), a.set(-1, None, 0.1, turn=0.6), a.sit_floor(0.3)), [0.1, 0.6, 1.0, 1.6, 2.4], rh, rh,
           'mom: sit_floor (3/4 view; back to the wall)', light=NIGHT)
    _strip(cv, pen, 'dad', lambda a: a.sign(0.3, 2.4), [0.1, 0.8, 1.3, 1.9, 2.9], 2 * rh, rh, 'dad: sign (21 years ago)', light=PORCH)
    _strip(cv, pen, 'you', lambda a: (a.expr('fear', 0), a.catch_wrist(0.3, 2.0, side=1)), [0.1, 0.45, 0.9, 1.6, 2.6], 3 * rh, rh,
           'you: catch_wrist', light=NIGHT)
    save(surf, 'family_acting')


def _window_wall(pen, x0, y0, w, h, win, t, scale=1.0):
    """Side of the house with Lily's open window: siding, the moon nightlight glow inside, curtains blowing out."""
    pen.linear(rect(x0, y0, w, h), 0, y0, 0, y0 + h, [(0, '#0b1020'), (1, '#1a2238')])
    k = 0
    while y0 + k * 80 * scale < y0 + h:
        yy = y0 + k * 80 * scale
        pen.fill(rect(x0, yy, w, 78 * scale), '#2c3446' if k % 2 else '#283042')
        pen.line(poly([(x0, yy + 78 * scale), (x0 + w, yy + 78 * scale)], False), 3 * scale, '#1a1f2b'); k += 1
    wx, wy, ww, wh = win
    pen.fill(rect(wx, wy, ww, wh), '#3a2f4a')
    pen.radial(rect(wx, wy, ww, wh), wx + ww * 0.5, wy + wh * 0.35, max(ww, wh) * 0.8, [(0, '#c9b8f0'), (0.5, '#6a5a8f'), (1, '#2a2238')])
    pen.fill(oval(wx + ww * 0.82, wy + wh * 0.22, 30 * scale), '#fff4c8'); pen.glow(wx + ww * 0.82, wy + wh * 0.22, 120 * scale, '#fff0c0', 120)


def _curtains(pen, win, t, scale=1.0):
    wx, wy, ww, wh = win
    sw = 18 * scale * math.sin(t * 1.3)
    for s_ in (-1, 1):
        x0 = wx if s_ < 0 else wx + ww
        cur = smooth([(x0, wy), (x0 - s_ * 0.17 * ww + sw, wy), (x0 - s_ * 0.14 * ww + sw * 1.4, wy + wh * 0.5),
                      (x0 - s_ * 0.22 * ww + sw * 2, wy + wh * 1.05), (x0, wy + wh)], True, 0.7)
        pen.fill(cur, '#d8cdea'); pen.line(cur, 5 * scale)


def sheet_lily_window():
    """The delivery photo (3:41): from below, Lily leaning out of her window, the driver's tablet held up to her, her small
    finger on the screen; and the wide: the driver under the window with the too-long arm. Recipe: Lily drawn clipped
    above the sill, the sill, the tablet, then characters.draw_arm for her reaching arm over the sill."""
    surf, cv, pen = canvas()
    t = 2.6
    win = (330, 70, 460, 400); sill_y = 470
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(0, 0, 1100, 1080))
    _window_wall(pen, 0, 0, 1100, 1080, win, t)
    a = CH.Acting('lily', seed=9); a.lean_out(0.0, None, side=-1, reach_t=2.0)
    P = a.at(t)
    LB = dict(cx=560, cy=250, scale=0.4)
    cv.save(); cv.clipRect(skia.Rect.MakeLTRB(win[0], win[1], win[0] + win[2], sill_y))
    CH.draw_bust(pen, 'lily', LB['cx'], LB['cy'], LB['scale'], P, light=dict(rim='#c9b8f0', rim_a=90, side=1))
    cv.restore()
    _curtains(pen, win, t)
    pen.fill(rect(300, sill_y - 8, 520, 40), '#d9d4c8'); pen.line(rect(300, sill_y - 8, 520, 40), 6)          # the sill
    pen.line(rect(*win), 8)
    wr, tip = CH.hand_pos('lily', P, -1, **LB)
    tx, ty = tip[0] - 26, tip[1] + 26                                                                           # her fingertip on the signature box
    CH.draw_hand(pen, 'driver', tx + 30, ty + 150, 150, 'grip', 180.0, 1)                                       # his hand from below
    CH.draw_tablet(pen, tx, ty, 280, screen='sign', sig='lily', ink=0.8, ts='3:41 AM', t=t, angle=-6)
    CH.draw_arm(pen, 'lily', -1, P, light=dict(rim='#c9b8f0', rim_a=90, side=1), **LB)                          # her arm, over the sill
    cv.restore()
    label(cv, 'the delivery photo, 3:41 (from below)', 550, 1050, 22)
    # right: the wide
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(1110, 0, 810, 1080))
    H = 420.0; sill2 = 1000 - 3.2 / 1.85 * H                                       # a real second-floor sill (3.2 m)
    win2 = (1425, sill2 - 150, 180, 150)
    _window_wall(pen, 1110, 0, 810, 980, win2, 3.0, 0.4)
    pen.fill(rect(1110, 980, 810, 100), '#121a16')
    l2 = CH.Acting('lily', seed=9); l2.lean_out(0.0, None, side=-1, reach_t=2.0)
    P2 = l2.at(3.0); LB2 = dict(cx=1515, cy=sill2 - 95, scale=0.14)
    cv.save(); cv.clipRect(skia.Rect.MakeLTRB(win2[0], win2[1], win2[0] + win2[2], sill2))
    CH.draw_bust(pen, 'lily', LB2['cx'], LB2['cy'], LB2['scale'], P2)
    cv.restore()
    _curtains(pen, win2, 3.0, 0.3)
    pen.fill(rect(1410, sill2 - 4, 210, 14), '#d9d4c8'); pen.line(rect(1410, sill2 - 4, 210, 14), 3)
    pen.line(rect(*win2), 4)
    _, tip2 = CH.hand_pos('lily', P2, -1, **LB2)
    k = H / 1000.0; sh_y = 1000 + (-1000 + 178 + 64) * k                          # the driver's shoulder joint (px)
    stretch = max(0.0, (sh_y - (tip2[1] + 46)) / (0.97 * 348.0 * k) - 1.0)
    dx = tip2[0] + 8 - (124 - 17 + 40) * k
    d = CH.Acting('driver', seed=4); d.reach_up(0.0, None, side=1, stretch=stretch, grow=1.0, screen='lily')
    CH.draw(pen, 'driver', dx, 1000, H, d.at(3.0), light=dict(rim='#a998d0', rim_a=80, side=1))
    CH.draw_arm(pen, 'lily', -1, P2, **LB2)
    cv.restore()
    label(cv, 'reach_up(stretch=%.2f): up to her second-floor window' % stretch, 1515, 1050, 20)
    save(surf, 'lily_window')


def sheet_props():
    surf, cv, pen = canvas()
    title(cv, 'PROPS: THE BOX, THE TABLET, THE KEYS', 'BoxActing.knock: two knocks, a pause, one more (dad\'s knock)')
    b = CH.BoxActing(1); kv = b.knock(1.0); b.cut(30.0)
    seq = [(0.95, 'before'), (1.02, 'knock 1'), (1.32, 'knock 2'), (1.70, 'pause'), (2.04, 'knock 3'), (31.0, 'tape cut (6:12)')]
    for i, (tt, lab) in enumerate(seq):
        x = 105 + i * 205
        CH.draw_box(pen, x, 640, 460, b.at(tt), t=tt, view=0.3)
        label(cv, lab, x, 680, 18)
    CH.draw_tablet(pen, 1460, 380, 560, screen='sign', sig='initial', ink=1.0, ts='3:08 AM', t=1.0)
    label(cv, 'your initial, stopped halfway', 1460, 700, 18)
    CH.draw_tablet(pen, 1790, 300, 330, screen='sign', sig='lily', t=1.0, ts='3:41 AM')
    label(cv, '"Lily."', 1790, 500, 18)
    CH.draw_tablet(pen, 1790, 610, 200, screen='camera', flash=0.0, t=1.0)
    CH.draw_box_inside(pen, 250, 900, 300, t=1.0)
    label(cv, 'sunrise: empty, the rusted keys', 250, 1070, 17)
    for i, d in enumerate([-0.2, 0.12, 0.3, 0.6, None]):
        CH.draw_keys_bowl(pen, 620 + i * 210, 1030, 180, drop=d, t=2.0, hand=(i == 1))
        label(cv, 'drop %s' % ('rest' if d is None else '%.2f' % d), 620 + i * 210, 1070, 15)
    CH.draw_keyring(pen, 1660, 820, 210, rust=0.0)
    CH.draw_keyring(pen, 1820, 820, 210, rust=1.0)
    label(cv, 'keys + keychain (new / rusted)', 1740, 1070, 17)
    save(surf, 'props')


SHEETS = dict(lineup=sheet_lineup, driver_turnaround=sheet_turnaround, driver_smile_arc=sheet_smile_arc, driver_doorbell=sheet_doorbell,
              driver_doorbell2=lambda: sheet_doorbell(2),
              driver_acting=sheet_driver_acting, driver_acting2=sheet_driver_acting2, family_faces=sheet_family,
              family_acting=sheet_family_acting, lily_window=sheet_lily_window, props=sheet_props)

if __name__ == '__main__':
    names = sys.argv[1:] or list(SHEETS)
    for n in names:
        t0 = time.time(); SHEETS[n](); print('  %s %.1f s' % (n, time.time() - t0))
