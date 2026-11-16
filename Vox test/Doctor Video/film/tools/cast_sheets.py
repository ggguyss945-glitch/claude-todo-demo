"""cast_sheets.py: model sheets of the doctor film's cast (characters.py + characters_doctor.py), written to W/cast/.

    cd "Vox test/Doctor Video/film" && python3 tools/cast_sheets.py [names...]     (default: all sheets)

Sheets (1920x1080 JPEG): later_likeness (Doctor Later beside the owner's reference photo and the fan drawing),
later_turn (turnaround), later_states (every state the script needs), later_tape (the tape loosening strip by strip and
the faces under it), lineup, lineup2 (everyone to scale), turn_family, faces_ruth, faces_milo, faces_narrator,
faces_halverson, faces_others (expressions per beat), mouths (lip-sync shapes), props, staging. The Bunnyman film's
sheets live in the Bunnyman Video project.
"""
import os, sys, math
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import numpy as np
import cv2
import skia
from engine.core import set_render_size, Pen, CFG, rect, rrect, oval, poly, smooth, text, mix
import characters as CH

OUT = os.path.join(HERE, '_work', 'cast')
BG = (26, 28, 36)
NIGHT = dict(rim='#9fb6ff', rim_a=70, side=1, key=-0.25)
WARM = dict(rim='#ffcf8f', rim_a=55, side=-1, key=0.1)


def canvas(w=1920, h=1080, bg=BG):
    set_render_size(w, h)
    surf = skia.Surface(CFG.rw, CFG.rh)
    cv = surf.getCanvas(); cv.clear(skia.Color(*bg)); cv.scale(CFG.k, CFG.k)
    return surf, cv, Pen(cv)


def floor(pen, y, c='#1f222b'):
    pen.linear(rect(0, y, 1920, 1080 - y), 0, y, 0, 1080, [(0, c), (1, '#121319')])


def title(cv, s, sub=''):
    text(cv, s, 40, 52, 900, 34, '#ffffff', 255, 0.04, 'left')
    if sub: text(cv, sub, 40, 86, 700, 19, '#9aa3b8', 255, 0.02, 'left')


def label(cv, s, x, y, size=17, c='#d8dbe4'):
    text(cv, s, x, y, 800, size, c, 255, 0.02, 'center')


def save(surf, name):
    os.makedirs(OUT, exist_ok=True)
    img = surf.makeImageSnapshot().toarray()[:, :, :3]
    p = os.path.join(OUT, name + '.jpg')
    cv2.imwrite(p, img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print('wrote', p)


def _turn(name, rows, ttl, sub, ppm=330.0):
    surf, cv, pen = canvas()
    title(cv, ttl, sub)
    views = [(0.0, 'FRONT'), (0.5, '3/4 RIGHT'), (1.0, 'PROFILE'), (1.5, '3/4 BACK'), (2.0, 'BACK'), (-0.5, '3/4 LEFT')]
    nrow = len(rows)
    for r, (who, light) in enumerate(rows):
        y = 140 + (r + 1) * (900 / nrow) - 20
        floor(pen, y) if r == nrow - 1 else None
        h = CH.height_px(who, ppm) * (0.95 if nrow == 1 else min(1.0, (900 / nrow - 40) / CH.height_px(who, ppm) / 1.15))
        for i, (yw, lb) in enumerate(views):
            x = 170 + i * 316
            CH.draw(pen, who, x, y, h, CH.Pose(turn=yw), t=0.4, light=light, detail=2)
            if r == 0: label(cv, lb, x, 128, 15, '#9aa3b8')
    save(surf, name)


def _faces(name, items, ttl, sub, light=None, cols=6, bg=None):
    surf, cv, pen = canvas()
    title(cv, ttl, sub)
    n = len(items)
    rows = int(math.ceil(n / cols))
    cw = 1920 / cols; ch = (1080 - 120) / rows
    for i, it in enumerate(items):
        who, pose, lb = it[0], it[1], it[2]
        lt = it[3] if len(it) > 3 else light
        c, r = i % cols, i // cols
        x0, y0 = c * cw, 120 + r * ch
        pen.fill(rect(x0 + 4, y0 + 4, cw - 8, ch - 8), '#232633')
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x0 + 4, y0 + 4, cw - 8, ch - 8))
        P = pose if isinstance(pose, CH.Pose) else CH.Pose(**pose) if isinstance(pose, dict) else CH.Pose(pose)
        CH.draw_bust(pen, who, x0 + cw / 2, y0 + ch * 0.48, ch / 600.0 * 0.62, P, t=0.6, light=lt, detail=2)
        cv.restore()
        pen.fill(rect(x0 + 4, y0 + ch - 34, cw - 8, 30), '#000000', 140)
        label(cv, lb, x0 + cw / 2, y0 + ch - 13, 15)
    save(surf, name)


def P_(expr=None, **kw):
    p = CH.Pose(expr) if expr else CH.Pose()
    for k, v in kw.items(): setattr(p, k, v)
    return p


FLOOR = 940.0
REF = os.path.join(HERE, '_work', 'ref')
FLUO = dict(rim='#d8f0a0', rim_a=70, side=1, key=-0.1)


def _later(x, y, ppm, seat='plastic', knee=None, hands=('lap', 'pen'), props=True, seed=1, **kw):
    a = CH.Acting('later', seed=seed, height=CH.height_px('later', ppm)).place(x, y)
    a.perch(None if seat in ('plastic', 'armchair', 'bench', 'low') else seat, seat if isinstance(seat, str) else 'plastic', knee=knee,
            hands=hands, props=props)
    if kw: a.set(-1, None, 0.01, **kw)
    return a


def _chair(pen, x, y, ppm, kind='plastic', facing=1.0, front=False, rock=0.0, c='#3f6a8a'):
    k = ppm / 100.0
    if kind == 'armchair':
        seat = y - 42 * k
        w = 95 * k
        pen.fill(rrect(x - w / 2 + 6 * k, seat - 55 * k, w - 12 * k, 62 * k, 8 * k), '#5a3e28'); pen.line(rrect(x - w / 2 + 6 * k, seat - 55 * k, w - 12 * k, 62 * k, 8 * k), 3)
        pen.fill(rrect(x - w / 2, seat - 3 * k, w, y - seat - 4 * k, 6 * k), '#6a4a30'); pen.line(rrect(x - w / 2, seat - 3 * k, w, y - seat - 4 * k, 6 * k), 3)
        for sd in (-1, 1):
            pen.fill(rrect(x + sd * (w / 2 - 8 * k) - 9 * k, seat - 22 * k, 18 * k, y - seat + 18 * k, 6 * k), '#74523a')
            pen.line(rrect(x + sd * (w / 2 - 8 * k) - 9 * k, seat - 22 * k, 18 * k, y - seat + 18 * k, 6 * k), 3)
        return seat
    sy = y - 45 * k
    cv = pen.cv; cv.save()
    if rock: fx = x + facing * 20 * k; cv.translate(fx, y); cv.rotate(rock * facing); cv.translate(-fx, -y)
    if front:
        for sd in (-1, 1): pen.line(poly([(x + sd * 20 * k, y), (x + sd * 18 * k, sy)], False), 4, '#2a2c32')
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


def sheet_later_likeness():
    """Doctor Later beside the owner's reference photo (and the fan drawing of the same creature): the same pose (folded on
    a small chair in profile, the long neck reaching forward, the face turned to us, the cone tipped, hands flat on the
    carpet), then the narration's adaptations (tape, coat, clipboard and pen) in the waiting room."""
    surf, cv, pen = canvas(bg=(198, 182, 176))
    img = surf.makeImageSnapshot().toarray()[:, :, :3]
    title(cv, 'DOCTOR LATER: LIKENESS TO THE REFERENCE', 'Left: the owner\'s photo and the fan drawing. Right: our creature in the photo\'s pose and in the film (tape, grey coat, clipboard, pen)')
    # our creature in the photo's pose, same scale as the photo panel
    y = 1040
    pen.fill(rect(640, y, 1280, 40), '#3a3434')
    ppm = 420.0
    x = 980
    k = ppm / 100.0
    _chair(pen, x, y, ppm, 'plastic', facing=1.0, c='#2a2626')
    a = _later(x, y, ppm, 'plastic', knee=0.0, hands=('floor', 'floor'), props=False, turn=1.0, h_turn=-1.0, h_tilt=24.0)
    CH.draw(pen, 'later', x, y, a.height, a.at(1.0), t=1.0, detail=2)
    label(cv, 'the reference pose', x + 120, 140, 17, '#3a3434')
    # the film version: waiting-room chair, tape, coat, clipboard and pen, looking up at you
    pen.fill(rect(1460, 120, 460, 920), '#7d8a6a')
    pen.fill(rect(1460, 900, 460, 140), '#5a5a4a')
    x2, y2, ppm2 = 1680, 900, 230.0
    _chair(pen, x2, y2, ppm2, 'plastic', facing=1.0)
    b = _later(x2, y2, ppm2, 'plastic', turn=0.45, h_turn=-0.25, h_tilt=14.0)
    CH.draw(pen, 'later', x2, y2, b.height, b.at(1.0), t=1.0, detail=2, light=FLUO)
    label(cv, 'in the film (waiting room)', x2, 150, 17, '#1d1f26')
    out = surf.makeImageSnapshot().toarray()[:, :, :3].copy()
    ref = cv2.imread(os.path.join(REF, 'doctor_later_reference_photo.jpg'))
    r = cv2.resize(ref, (int(236 * 600 / 251), 600), interpolation=cv2.INTER_CUBIC)
    out[110:110 + 600, 30:30 + r.shape[1]] = r
    dr = cv2.imread(os.path.join(REF, 'doctor_later_reference_drawing.jpg'))
    d2 = cv2.resize(dr, (330, 330), interpolation=cv2.INTER_AREA)
    out[730:730 + 330, 30:30 + 330] = d2
    cv2.putText(out, 'owner reference photo', (40, 735 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (40, 40, 40), 2, cv2.LINE_AA)
    cv2.putText(out, 'fan drawing', (370, 1050), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (40, 40, 40), 2, cv2.LINE_AA)
    os.makedirs(OUT, exist_ok=True)
    cv2.imwrite(os.path.join(OUT, 'later_likeness.jpg'), out, [cv2.IMWRITE_JPEG_QUALITY, 90]); print('wrote later_likeness')


def sheet_later_turn():
    surf, cv, pen = canvas(bg=(125, 138, 106))
    title(cv, 'DOCTOR LATER: TURNAROUND (FOLDED ON A WAITING-ROOM CHAIR)',
          '2.9 m standing (he never stands while watched); folded, the cone tip is about 2 m up. Same pose in every view: knees above the face, the neck reaching forward')
    y = 980; floor(pen, y - 95, '#5a5a4a')   # the floor plane reaches back: feet behind the chair land on it too
    ppm = 250.0
    views = [(0.0, 'FRONT'), (0.5, '3/4 RIGHT'), (1.0, 'PROFILE'), (1.5, '3/4 BACK'), (2.0, 'BACK'), (-0.5, '3/4 LEFT')]
    for i, (yw, lb) in enumerate(views):
        x = 170 + i * 316
        _chair(pen, x, y, ppm, 'plastic', facing=1.0 if math.sin(yw * math.pi / 2) >= 0 else -1.0, front=abs(math.sin(yw * math.pi / 2)) < 0.3)
        a = _later(x, y, ppm, 'plastic', turn=yw, h_tilt=10.0)
        CH.draw(pen, 'later', x, y, a.height, a.at(1.0), t=1.0, detail=2, light=FLUO)
        label(cv, lb, x, 128, 15, '#1d1f26')
    save(surf, 'later_turn')


def sheet_later_states():
    surf, cv, pen = canvas(bg=(40, 44, 40))
    title(cv, 'DOCTOR LATER: STATES', 'Every state the narration needs. He never stands, never lip-syncs; his arm unfolds unnaturally long when he reaches')
    cw, ch = 1920 / 4, (1080 - 120) / 2
    def panel(i, bg, fn, lb):
        c, r = i % 4, i // 4
        x0, y0 = c * cw, 120 + r * ch
        pen.fill(rect(x0 + 4, y0 + 4, cw - 8, ch - 8), bg)
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x0 + 4, y0 + 4, cw - 8, ch - 8))
        fn(x0, y0)
        cv.restore()
        pen.fill(rect(x0 + 4, y0 + ch - 34, cw - 8, 30), '#000000', 150)
        label(cv, lb, x0 + cw / 2, y0 + ch - 13, 14)
    def p0(x0, y0):
        y = y0 + ch - 40; ppm = 150.0
        pen.fill(rect(x0, y, cw, 40), '#5a5a4a')
        _chair(pen, x0 + 240, y, ppm, front=True)
        a = _later(x0 + 240, y, ppm, 'plastic', turn=0.2, h_tilt=12.0)
        CH.draw(pen, 'later', x0 + 240, y, a.height, a.at(1.0), t=1.0, light=FLUO)
    def p1(x0, y0):
        y = y0 + ch - 40; ppm = 140.0
        pen.fill(rect(x0, y, cw, 40), '#5a5a4a')
        seat = _chair(pen, x0 + 240, y, ppm, 'armchair')
        a = _later(x0 + 240, y, ppm, 'armchair', turn=0.0, h_tilt=8.0)
        CH.draw(pen, 'later', x0 + 240, y, a.height, a.at(1.0), t=1.0, light=FLUO)
    def p2(x0, y0):
        y = y0 + ch - 60; ppm = 95.0
        pen.linear(rect(x0, y0, cw, ch), 0, y0, 0, y0 + ch, [(0, '#05070e'), (1, '#121624')])
        lx = x0 + 180
        pen.line(poly([(lx, y), (lx, y - 300), (lx + 40, y - 306)], False), 5, '#2a2c32')
        pen.glow(lx + 50, y - 300, 160, '#cfe0ff', 110)
        pen.fill(rect(x0 + 230, y - 0.46 * ppm - 4, 150, 8), '#3a3226')
        a = _later(x0 + 300, y, ppm, 'bench', knee=1.1, turn=-0.4, h_turn=0.3, h_tilt=-10.0)
        CH.draw_later_far(pen, x0 + 300, y, a.height, a.at(1.0), t=1.0, lamp=(lx + 50, y - 300), flicker=1.0)
    def p3(x0, y0):
        y = y0 + ch - 40; ppm = 150.0
        roof = y - 1.18 * ppm
        pen.fill(rect(x0, y0, cw, ch), '#1a1c22'); pen.fill(rect(x0, y0, cw, roof - y0), '#2a2c34')
        pen.fill(rrect(x0 + 120, y - 0.30 * ppm - 4, 260, y - (y - 0.30 * ppm), 8), '#45454c')
        a = CH.Acting('later', seed=4, height=CH.height_px('later', ppm)).place(x0 + 240, y)
        a.perch(y - 0.30 * ppm, 'car'); a.bend_to_roof(roof); a.face(0.0, 0.0)
        CH.draw(pen, 'later', x0 + 240, y, a.height, a.at(1.0), t=1.0, light=NIGHT)
    def p4(x0, y0):
        y = y0 + ch - 40; ppm = 110.0
        pen.fill(rect(x0, y, cw, 40), '#5a5a4a')
        _chair(pen, x0 + 90, y, ppm, 'armchair')
        mx = x0 + 400
        pen.line(poly([(mx, y), (mx, y - 1.1 * ppm)], False), 4, '#6a6e76'); pen.fill(rrect(mx - 12, y - 1.4 * ppm, 24, 0.3 * ppm, 4), '#c0392f')
        a = _later(x0 + 90, y, ppm, 'armchair', hands=('lap', 'floor'), turn=0.6, h_turn=-0.1)
        a.reach_far(0.0, -1, (mx, y - 1.19 * ppm), dur=0.5, shape='pinch', arc=0.0)
        CH.draw(pen, 'later', x0 + 90, y, a.height, a.at(1.0), t=1.0, light=FLUO)
    def p5(x0, y0):
        y = y0 + ch - 40; ppm = 120.0
        pen.fill(rect(x0, y, cw, 40), '#4a5640')
        a = _later(x0 + 110, y, ppm, 'plastic', hands=('lap', 'floor'), turn=0.5, h_turn=-0.2, h_tilt=12.0)
        a.offer(-1.0, -1, (x0 + 400, y - 1.15 * ppm), dur=0.1, text_='MILO')
        _chair(pen, x0 + 110, y, ppm)
        CH.draw(pen, 'later', x0 + 110, y, a.height, a.at(1.0), t=1.0, light=FLUO)
        m = CH.Ctx(pen, skia.Matrix(), 3.0)
        tx, ty = a.where(1.0, 'tips_r')
        # close-up callout: a ring round his fingertips, a framed inset of the ticket they hold
        pen.fill(rrect(x0 + 286, y0 + 36, 142, 160, 10), '#2c3326')
        pen.line(rrect(x0 + 286, y0 + 36, 142, 160, 10), 2, '#ffd479', 220)
        CH._dl_ticket(m, x0 + 360, y0 + 120, -8.0, 16.0, 'MILO', 2)
        pen.line(oval(tx, ty, 22), 2, '#ffd479', 220)
        pen.line(poly([(tx - 8, ty - 22), (x0 + 330, y0 + 196)], False), 2, '#ffd479', 220)
        text(cv, 'close-up', x0 + 357, y0 + 214, 700, 13, '#ffd479', 230, 0.02, 'center')
    def p6(x0, y0):
        a = CH.Acting('later', seed=6, height=CH.height_px('later', 380.0)).place(900, FLOOR)
        a.perch(None, 'plastic'); a.face(0.3, -0.2)
        P = a.at(1.0); P.dl_flinch = 0.9
        CH.draw_bust(pen, 'later', x0 + 240, y0 + 260, 0.34, P, t=1.0, light=FLUO)
    def p7(x0, y0):
        y = y0 + ch - 40; ppm = 230.0
        pen.fill(rect(x0, y, cw, 40), '#c8d0d4'); pen.fill(rect(x0, y0, cw, y - y0), '#dfe8ee')
        for i, xx in enumerate((x0 + 140, x0 + 330)):
            _chair(pen, xx, y, ppm, facing=1.0, rock=CH.chair_rock(0.45, 0.0, 5.0) if i else 0.0, c='#5a7a9a')
    for i, (bg, fn, lb) in enumerate((('#7d8a6a', p0, 'folded in a plastic waiting-room chair'), ('#7d8a6a', p1, 'in Grandpa\'s armchair: knees above his head'),
                                       ('#0a0c12', p2, 'far: the bus-stop bench, the flickering light'), ('#1a1c22', p3, 'the back seat: head bent against the roof'),
                                       ('#7d8a6a', p4, 'reaching across the room (the arm unfolds)'), ('#5a6a4a', p5, 'the ticket between two long fingers'),
                                       ('#5a6a4a', p6, 'flinching from a question, as if from light'), ('#dfe8ee', p7, 'gone: the empty chair still rocking (chair_rock)'))):
        panel(i, bg, fn, lb)
    save(surf, 'later_states')


def sheet_later_tape():
    surf, cv, pen = canvas(bg=(60, 70, 52))
    title(cv, 'DOCTOR LATER: THE TAPE AND THE FACES UNDER IT',
          'Top: old yellow medical tape wound round and round, a thin gap, two pale patient eyes; each question loosens a strip (pose.dl_tape 1 -> 0). Bottom: faces under it (pose.dl_face 0..5)')
    a = CH.Acting('later', seed=7, height=CH.height_px('later', 380.0)).place(900, FLOOR)
    a.perch(None, 'plastic'); a.face(0.12, -0.08); a.set(-1, None, 0.01, h_tilt=6.0)
    P0 = a.at(1.0)
    tapes = (1.0, 0.86, 0.72, 0.58, 0.4, 0.0)
    cw = 1920 / 6
    for i, tp in enumerate(tapes):
        P = P0.copy(); P.dl_tape = tp
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(i * cw + 4, 110, cw - 8, 470))
        pen.fill(rect(i * cw + 4, 110, cw - 8, 470), '#4a5640')
        CH.draw_bust(pen, 'later', i * cw + cw / 2, 470, 0.27, P, t=1.0, light=FLUO)
        cv.restore()
        label(cv, 'dl_tape %.2f' % tp, i * cw + cw / 2, 600, 14)
    names = ('his own face', 'Grandpa, gray and patient', 'a man I never saw', 'a little girl', 'my grandmother', '...me')
    for i in range(6):
        P = P0.copy(); P.dl_tape = 0.42; P.dl_face = float(i)
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(i * cw + 4, 620, cw - 8, 420))
        pen.fill(rect(i * cw + 4, 620, cw - 8, 420), '#4a5640')
        CH.draw_bust(pen, 'later', i * cw + cw / 2, 900, 0.36, P, t=1.0, light=FLUO)
        cv.restore()
        label(cv, names[i], i * cw + cw / 2, 1062, 14)
    save(surf, 'later_tape')


def sheet_lineup():
    surf, cv, pen = canvas()
    title(cv, 'THE DOCTOR FILM CAST: TO SCALE', 'Draw each one with height = CH.height_px(who, px_per_m) at the same depth; Doctor Later is 2.9 m standing (folded here on a 45 cm chair)')
    y = 960; floor(pen, y)
    ppm = 330.0
    whos = [('later', 'DOCTOR LATER'), ('ruth', 'RUTH (70s)'), ('narr14', 'THE NARRATOR (14)'), ('milo', 'MILO (7)'), ('mom_rn', 'MOM (NURSE)'),
            ('halverson', 'DR ANNA HALVERSON'), ('halverson_rain', '...AT 3:40 AM'), ('grandpa79', 'GRANDPA, 1979'), ('ruth79', 'RUTH, 1979')]
    for i, (who, lb) in enumerate(whos):
        x = 1920 / (len(whos) + 1) * (i + 1) + (-2 if i == 0 else 30 + 25 * (len(whos) - i) / len(whos))
        if who == 'later':
            _chair(pen, x, y, ppm, front=True)
            a = _later(x, y, ppm, 'plastic', turn=0.25, h_tilt=8.0)
            CH.draw(pen, 'later', x, y, a.height, a.at(1.0), t=1.0, detail=2)
            label(cv, lb, x, y + 40); label(cv, '2.90 m standing', x, y + 64, 14, '#9aa3b8')
            continue
        CH.draw(pen, who, x, y, CH.height_px(who, ppm), CH.Pose(turn=0.12 if i % 2 else -0.12), t=0.4, detail=2)
        label(cv, lb, x, y + 40)
        label(cv, '%.2f m' % CH.CAST[who]['m'], x, y + 64, 14, '#9aa3b8')
    save(surf, 'lineup')


def sheet_lineup2():
    surf, cv, pen = canvas()
    title(cv, 'THE HOSPITAL, THE WAITING ROOM, LATER: TO SCALE', 'The ER (warm, competent, kind); the waiting room\'s people (grey, still); Milo in the ER and at 22; the narrator at 29')
    y = 960; floor(pen, y)
    ppm = 330.0
    whos = [('er_nurse', 'ER NURSE'), ('er_doctor', 'ER DOCTOR'), ('medic', 'PARAMEDIC'), ('medic2', 'PARAMEDIC 2'), ('cardio', 'CARDIOLOGIST'),
            ('chest_man', 'MAN, CHEST PAIN'), ('milo_er', 'MILO, ER'), ('milo_jeans', 'MILO, DINO JEANS'), ('milo22', 'MILO AT 22'), ('narr29', 'ME AT 29'),
            ('ghost_chest', 'WAITING: CHEST'), ('ghost_side', 'WAITING: SIDE'), ('ghost_teen', 'WAITING: ARM'), ('ghost_girl', 'WAITING: GIRL'), ('grandpa_ghost', 'GRANDPA, LAST ROW')]
    for i, (who, lb) in enumerate(whos):
        x = 1920 / (len(whos) + 1) * (i + 1)
        CH.draw(pen, who, x, y, CH.height_px(who, ppm * 0.92), CH.Pose(turn=0.12 if i % 2 else -0.12, **({'eye_open': 0.86, 'still': 1.0} if 'ghost' in who else {})), t=0.4, detail=2)
        label(cv, lb, x, y + 40, 12)
    save(surf, 'lineup2')


def sheet_turn_family():
    _turn('turn_family', [('ruth', None), ('narr14', None), ('milo', None)], 'RUTH, THE NARRATOR (14), MILO: TURNAROUNDS',
          'Ruth: set silver curls, reading glasses on a chain, buttoned cardigan; the narrator: neither clearly a boy nor a girl; Milo: dinosaur pajamas')
    _turn('turn_doctors', [('halverson', None), ('halverson_rain', None), ('mom_rn', None)], 'DOCTOR HALVERSON, MOM: TURNAROUNDS',
          'Halverson: coffee-stained blue scrubs, dinosaur stickers on her badge, a watch; at 3:40 AM a raincoat, hair soaked flat; Mom: night-shift nurse')


def sheet_faces_ruth():
    _faces('faces_ruth', [
        ('ruth', P_('stern'), 'stern (as always)'), ('ruth', P_('stern', h_turn=0.3, look_x=0.4), 'tapping the yellow card'),
        ('ruth', P_('stern_afraid', h_turn=-0.2), 'by the phone, already waiting'), ('ruth', P_('angry', h_turn=0.2, m_open=0.3), '"Don\'t you dare tell me"'),
        ('ruth', P_('set_jaw', h_turn=0.3), 'pulling the cord out'), ('ruth', P_('stern_afraid', h_nod=0.15), 'the receiver down, like a baby'),
        ('ruth', P_('stern', h_turn=-0.35, m_open=0.2), '"Doctors don\'t make house calls"'), ('ruth', P_('stern_afraid', hum=1.0, m_press=0.5, h_tilt=7), 'rocking Milo, humming'),
        ('ruth', P_('stern_afraid', wide=0.6, m_open=0.3, h_turn=0.2), '"How do you know what the voice said?"'), ('ruth', P_('grief_still', h_nod=0.25), 'staring at the burned paper'),
        ('ruth_sick', P_('pale_hidden', h_turn=0.25, specs=0.0), 'sunrise: chest pains, says nothing'), ('ruth', P_('asking', h_turn=0.3, smile=0.3), 'asking her cardiologist everything'),
    ], 'GRANDMA RUTH (70s): FACES', 'Stern and neat, frightened underneath; the reading glasses go on and off their chain (pose.specs)', WARM)


def sheet_faces_milo():
    _faces('faces_milo', [
        ('milo', P_(None), 'Milo'), ('milo', P_('kid_grin', h_turn=0.3), 'his favourite dinosaur'), ('milo', P_('thirsty'), 'thirsty all the time'),
        ('milo', P_('sleepy', h_tilt=-10), 'falling asleep everywhere'), ('milo', P_('brave', h_turn=0.4), 'brave (the blood test)'),
        ('milo_sick', P_('thirsty', m_open=0.3), '"I\'m so thirsty" (cracked lips)'), ('milo_sick', P_('fear', h_turn=0.2), 'the hand over his mouth'),
        ('milo_sick', P_('dazed', m_open=0.25, breath=1.2), 'breathing deep and fast'), ('milo_sick', P_('dazed', look_x=0.3), '"Who are you?"'),
        ('milo_er', P_('sleepy'), 'the ER: fluids, insulin'), ('milo_er', P_('kid_grin'), 'he smiles'), ('milo22', P_('kind_smile', h_turn=0.3), 'Milo at 22'),
    ], 'MILO (7) AND MILO AT 22: FACES', 'A seven-year-old with a light-brown mop and big brown eyes; sick: cracked lips, the eyes too big for his face')


def sheet_faces_narrator():
    _faces('faces_narrator', [
        ('narr14', P_(None), 'neutral'), ('narr14', P_('fear', h_turn=0.3), 'listening at the receiver'), ('narr14', P_('shock_shut', h_turn=-0.2), 'the pen click in the hall'),
        ('narr14', P_('fear', h_turn=-1.6), 'at the peephole (from behind)'), ('narr14', P_('asking', m_open=0.4), '"Grandma, that\'s what the voice told you"'),
        ('narr14', P_('terror'), 'the waiting room'), ('narr14', P_('asking', m_open=0.5, m_round=0.3), '"What did you find?"'),
        ('narr14', P_('asking_hard', m_open=0.55), '"Who are you?" (growing force)'), ('narr14', P_('determined', h_turn=0.25), 'pulling free'),
        ('narr14', P_('relief', h_turn=0.2), 'he lived'), ('narr29', P_('tired_kind', h_turn=0.3), 'at 29: nineteen hours awake'),
        ('narr29', P_('kind_smile', h_turn=-0.2), '"Ask what we found."'),
    ], 'THE NARRATOR (14, AND 29): FACES', 'Neither clearly a boy nor a girl: a shaggy cut with curtain bangs, a soft jaw, warm hazel eyes; at 29 the same face, tired and kind')


def sheet_faces_halverson():
    _faces('faces_halverson', [
        ('halverson', P_('kind_smile'), 'knows every kid\'s favourite dinosaur'), ('halverson', P_('careful_smile', h_turn=0.3), 'her smile goes careful'),
        ('halverson', P_('kind_smile', h_turn=-0.3, m_open=0.3), '"Day or night. I mean it."'), ('halverson', P_('exhausted', h_turn=0.2), '3 AM, nineteen hours awake'),
        ('halverson_rain', P_('pleading'), 'at the door, pleading'), ('halverson_rain', P_('pleading', m_open=0.35), '"This can\'t wait."'),
        ('halverson_rain', P_('set_jaw', h_nod=0.2), 'writing in marker'), ('halverson_rain', P_('exhausted', h_turn=0.4), 'in her car, calling again'),
        ('halverson_rain', P_('focused', h_turn=0.3), '"One-forty. Fast. That\'s okay."'), ('halverson_rain', P_('kind_smile', m_open=0.3), '"Questions are how we win."'),
        ('halverson_rain', P_('set_jaw', look_y=-0.5), 'she sees him in the mirror'), ('halverson_rain', P_('fierce_kind', m_open=0.25), '"Not tonight. Not on my shift."'),
    ], 'DOCTOR ANNA HALVERSON: FACES', 'Kind, quick, tired; freckles, a messy bun (soaked flat in the rain); the heroes of this film are drawn warm and competent', WARM)


def sheet_faces_others():
    _faces('faces_others', [
        ('mom_rn', P_('warm'), 'Mom, night shift'), ('mom_rn', P_('set_jaw', h_turn=0.3), 'running with the wheelchair'), ('mom_rn', P_('calm_firm', m_open=0.3), '"You don\'t wait. You call."'),
        ('er_nurse', P_('calm_firm', h_turn=0.3, m_open=0.3), '"Sir, you don\'t wait."'), ('er_doctor', P_('kind_smile', h_turn=-0.2), 'ER doctor'),
        ('cardio', P_('kind_smile', h_turn=0.3), 'the cardiologist (coffee)'), ('chest_man', P_('stern_afraid', h_turn=0.3), 'the man holding his chest'),
        ('ruth79', P_('stern_afraid'), 'Ruth, 1979: on hold'), ('ruth79', P_('warm', h_turn=0.3), 'bringing the coffee'),
        ('grandpa79', P_('stern_afraid', h_turn=-0.3), 'Grandpa, chest pain'), ('grandpa79', P_(None, lid_l=1, lid_r=1, still=1, h_tilt=9, h_nod=0.14), 'at sunrise (gently gone)'),
        ('grandpa_ghost', P_('waiting'), 'the last row, gray and patient'),
    ], 'MOM, THE ER, 1979, THE WAITING ROOM: FACES', 'The people who answer at three in the morning; 1979; the grey, still people who decided it could wait')


def sheet_mouths():
    surf, cv, pen = canvas()
    title(cv, 'MOUTH SHAPES (LIP SYNC ON CHARACTER LINES ONLY)', 'a.talk([(t0, t1, text)]) maps letters to these shapes; nobody\'s lips move on the narrator\'s lines; Doctor Later never lip-syncs (his mouth is under the tape)')
    vis = ['rest', 'M', 'F', 'L', 'E', 'I', 'A', 'O', 'U']
    whos = ['ruth', 'halverson_rain', 'narr14', 'milo']
    cw = 1920 / len(vis); ch = 230
    for r, who in enumerate(whos):
        for i, v in enumerate(vis):
            o, wd, rd, te, pr = CH.VISEMES[v]
            P = CH.Pose(m_open=o, m_wide=wd, m_round=rd, teeth=te, m_press=pr)
            x = cw * i + cw / 2; y = 150 + r * ch + 95
            CH.draw_head(pen, who, x, y, 170, P, detail=2, t=0.5)
            if r == 0: label(cv, v, x, 128, 18, '#ffd479')
        label(cv, who.upper(), 70, 150 + r * ch + 200, 15, '#9aa3b8')
    save(surf, 'mouths')


def sheet_props():
    surf, cv, pen = canvas()
    title(cv, 'PROPS (ONE SCALE, IN CENTIMETRES)', 'Held props sit in the gripping hand (PROPS3); on a surface draw_prop3(pen, name, x, y, px_per_cm) draws the same size; the coiled cord, wheelchair and steering wheel are helpers')
    ppc = 9.0
    items = ['receiver', 'card', 'card_back', 'match', 'match_lit', 'matchbox', 'marker', 'ticket', 'bottle', 'mug', 'cup', 'vial', 'cell', 'cell_glucose', 'keys']
    for i, nm in enumerate(items):
        x = 90 + i * 125; y = 400
        P = CH.Pose(); P.dl_ticket = 'MILO'
        CH.draw_prop3(pen, nm, x, y, ppc, 0.0, 2, 0.4, pose=P)
        label(cv, nm, x, 590, 14, '#9aa3b8')
    CH.draw_prop3(pen, 'note', 160, 640, 9.0 * 0.8, 0.0, 2, 0.4); label(cv, 'note (results + marker)', 160, 1000, 14, '#9aa3b8')
    CH.draw_coil_cord(pen, 420, 700, 760, 820, 9.0, 0.3, 0.0); label(cv, 'draw_coil_cord', 590, 900, 14, '#9aa3b8')
    h, s = CH.draw_wheelchair(pen, 1050, 1000, 4.0, 1.0); label(cv, 'draw_wheelchair (returns the handles)', 1050, 1040, 14, '#9aa3b8')
    pen.fill(oval(h[0], h[1], 6), '#ffd479')
    g10, g2 = CH.draw_steering_wheel(pen, 1440, 800, 130); label(cv, 'draw_steering_wheel (hands at 10 and 2)', 1440, 1000, 14, '#9aa3b8')
    for g in (g10, g2): pen.fill(oval(g[0], g[1], 6), '#ffd479')
    for i, (txt, ink) in enumerate((('MILO', 1.0), ('RUTH', 1.0), ('', 0.0))):
        m = CH.Ctx(pen, skia.Matrix(), 3.0)
        CH._dl_ticket(m, 1760 + 0 * i, 640 + i * 120, -6 + 6 * i, 13.0, txt, 2, ink=ink)
    label(cv, 'tickets: MILO, RUTH,', 1770, 985, 13, '#9aa3b8'); label(cv, 'Grandpa\'s (ink gone)', 1770, 1005, 13, '#9aa3b8')
    save(surf, 'props')


def sheet_staging():
    surf, cv, pen = canvas()
    title(cv, 'STAGING TOOLS: FEET ON THE FLOOR, HANDS ON TARGET, EYES ON TARGET',
          'sit_on / seated keep the feet on the floor; perch (a high table: legs dangle); reach_to and look_at on world points; carry; take_pulse; receiver_to_ear(toward=); Doctor Later\'s reach')
    y = 520; floor(pen, y, '#1f222b')
    ppm = 200.0
    # 1 Ruth sits in the armchair, feet on the floor
    seat = y - 0.43 * ppm
    pen.fill(rrect(160 - 70, seat - 4, 140, y - seat, 8), '#6a4a30'); pen.line(rrect(160 - 70, seat - 4, 140, y - seat, 8), 3)
    a = CH.Acting('ruth', seed=1, height=CH.height_px('ruth', ppm)).place(160, y); a.face(0.6); a.seated(seat, hands='lap')
    CH.draw(pen, 'ruth', 160, y, a.height, a.at(1.0), t=1.0); label(cv, 'seated (skirt drapes the knees)', 160, y + 30, 13, '#9aa3b8')
    # 2 Milo perched on the exam table
    top = y - 0.78 * ppm
    pen.fill(rect(330, top - 4, 170, 14), '#e8eef0'); pen.line(rect(330, top - 4, 170, 14), 2)
    m = CH.Acting('milo', seed=2, height=CH.height_px('milo', ppm)).place(410, top); m.face(0.5); m.set(-1, None, 0.01, perch=1.0, sit=1.0)
    CH.draw(pen, 'milo', 410, top, m.height, m.at(1.0), t=1.0); label(cv, 'perch: legs dangle', 410, y + 30, 13, '#9aa3b8')
    # 3 carry
    n = CH.Acting('narr14', seed=3, height=CH.height_px('narr14', ppm)).place(640, y); n.face(1.0)
    k = CH.Acting('milo_sick', seed=4, height=CH.height_px('milo', ppm)); k.face(-0.75)
    n.carry(-1.0, k)
    CH.draw_carry_child(pen, n, k, 1.0); label(cv, 'carry + draw_carry_child', 640, y + 30, 13, '#9aa3b8')
    # 4 take_pulse
    m2 = CH.Acting('milo_sick', seed=5, height=CH.height_px('milo', ppm)).place(980, y); m2.face(-0.5)
    m2.reach(-1.0, None, 1, out=10.0, down=150.0, fwd=200.0, shape='relaxed', up=0.0, fade=0.01)
    h = CH.Acting('halverson', seed=6, height=CH.height_px('halverson', ppm)).place(860, y); h.face(0.55)
    h.take_pulse(-1.0, -1, m2, 1)
    CH.draw(pen, 'milo_sick', 980, y, m2.height, m2.at(1.0), t=1.0); CH.draw(pen, 'halverson', 860, y, h.height, h.at(1.0), t=1.0)
    label(cv, 'take_pulse (two fingers, the watch)', 920, y + 30, 13, '#9aa3b8')
    # 5 receiver tilted toward the narrator
    r = CH.Acting('ruth', seed=7, height=CH.height_px('ruth', ppm)).place(1180, y); r.face(0.5)
    n2 = CH.Acting('narr14', seed=8, height=CH.height_px('narr14', ppm)).place(1360, y); n2.face(-0.55)
    r.receiver_to_ear(-1.0, None, 1, tilt_out=1.0, toward=n2)
    n2.look_at(-1.0, lambda t: r.grip_point(t, 1, 'receiver'), dur=0.1)
    CH.draw(pen, 'narr14', 1360, y, n2.height, n2.at(1.0), t=1.0); CH.draw(pen, 'ruth', 1180, y, r.height, r.at(1.0), t=1.0)
    label(cv, 'receiver_to_ear(toward=)', 1270, y + 30, 13, '#9aa3b8')
    # 6 hand over mouth
    m3 = CH.Acting('milo_sick', seed=9, height=CH.height_px('milo', ppm)).place(1700, y); m3.face(-0.5); m3.expr('fear', -1.0)
    r2 = CH.Acting('ruth', seed=10, height=CH.height_px('ruth', ppm)).place(1580, y); r2.face(0.6); r2.hand_over(-1.0, 1, m3, 'mouth', dur=0.1)
    CH.draw(pen, 'milo_sick', 1700, y, m3.height, m3.at(1.0), t=1.0); CH.draw(pen, 'ruth', 1580, y, r2.height, r2.at(1.0), t=1.0)
    label(cv, 'hand_over(\'mouth\')', 1640, y + 30, 13, '#9aa3b8')
    # bottom: Doctor Later reaches across the room and takes a wrist
    y2 = 1010; floor(pen, y2, '#1b1e26')
    ppm2 = 150.0
    L = CH.Acting('later', seed=11, height=CH.height_px('later', ppm2)).place(220, y2); L.perch(None, 'armchair', hands=('lap', 'floor')); L.face(0.5)
    N = CH.Acting('narr14', seed=12, height=CH.height_px('narr14', ppm2)).place(980, y2); N.face(-0.6)
    N.reach(-1.0, None, 1, out=40.0, down=150.0, fwd=200.0, shape='open', up=0.0, fade=0.01)
    L.take_wrist(-2.0, -1, N, 1, dur=0.5)
    _chair(pen, 220, y2, ppm2, 'armchair')
    CH.draw(pen, 'later', 220, y2, L.height, L.at(1.0), t=1.0); CH.draw(pen, 'narr14', 980, y2, N.height, N.at(1.0), t=1.0)
    CH.draw_later_arm(pen, L, 1.0, -1)
    wx, wy = N.where(1.0, 'wrist_l'); pen.fill(oval(wx, wy, 5), '#ffd479')
    label(cv, 'Doctor Later: take_wrist (the arm unfolds to reach; draw_later_arm on top)', 600, y2 + 34, 13, '#9aa3b8')
    L2 = CH.Acting('later', seed=13, height=CH.height_px('later', ppm2)).place(1330, y2); L2.perch(None, 'plastic'); L2.face(0.45)
    tg = (1800, y2 - 1.2 * ppm2); L2.reach_far(-1.0, -1 if False else 1, tg, dur=0.1, shape='pinch')
    _chair(pen, 1330, y2, ppm2, 'plastic', facing=1.0)
    CH.draw(pen, 'later', 1330, y2, L2.height, L2.at(1.0), t=1.0)
    pen.fill(oval(tg[0], tg[1], 7), '#ff5a6a', 220)
    tp = L2.where(1.0, 'tips_l'); pen.fill(oval(tp[0], tp[1], 4), '#ffd479')
    label(cv, 'reach_far: the pinch (yellow) on the target (red)', 1560, y2 + 34, 13, '#9aa3b8')
    save(surf, 'staging')


SHEETS = dict(later_likeness=sheet_later_likeness, later_turn=sheet_later_turn, later_states=sheet_later_states, later_tape=sheet_later_tape,
              lineup=sheet_lineup, lineup2=sheet_lineup2, turn_family=sheet_turn_family, faces_ruth=sheet_faces_ruth,
              faces_milo=sheet_faces_milo, faces_narrator=sheet_faces_narrator, faces_halverson=sheet_faces_halverson,
              faces_others=sheet_faces_others, mouths=sheet_mouths, props=sheet_props, staging=sheet_staging)

if __name__ == '__main__':
    names = sys.argv[1:] or list(SHEETS)
    for n in names: SHEETS[n]()
