"""cast_sheets.py: model sheets of the Bunnyman film's cast (characters.py + characters_bunny.py), written to W/cast/.

    cd "Vox test/Bunnyman Video/film" && python3 tools/cast_sheets.py [names...]     (default: all sheets)

Sheets (1920x1080 JPEG): lineup, lineup2 (everyone to scale), turn_bunny, turn_family (turnarounds), faces_mom,
faces_june, faces_narrator, faces_others (expressions), mouths (lip-sync shapes), bunny_states (1987 / now / paws / the
mask half off / the crayon drawing), props (every prop at one scale), staging (seat anchor, kneels, reach precision,
look-at, the planted walk and the run). The dummy film's sheets live in the Dummy Video project.
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


def _lineup(name, whos, labels, ppm, sub):
    surf, cv, pen = canvas()
    title(cv, 'THE BUNNYMAN FILM CAST: TO SCALE' if name == 'lineup' else 'SUPPORTING CAST AND STATES: TO SCALE', sub)
    y = 960
    floor(pen, y)
    n = len(whos)
    for i, (who, lb) in enumerate(zip(whos, labels)):
        x = 1920 / (n + 1) * (i + 1)
        CH.draw(pen, who, x, y, CH.height_px(who, ppm), CH.Pose(turn=0.12 if i % 2 else -0.12), t=0.4, detail=2)
        label(cv, lb, x, y + 40)
        label(cv, '%.2f m' % CH.CAST[who]['m'], x, y + 64, 14, '#9aa3b8')
    save(surf, name)


def sheet_lineup():
    _lineup('lineup', ['bunny', 'bunny87', 'dad', 'mom', 'narrator', 'june', 'laurie87', 'grandma'],
            ['THE BUNNYMAN (NOW)', 'THE BUNNYMAN, 1987', 'DAD', 'MOM (LAURIE, 43)', 'THE NARRATOR (16)', 'JUNE (7)', 'LAURIE, 1987 (7)', 'GRANDMA'],
            335.0, 'Heights to the crown (the Bunnyman\'s ears above): draw each one with height = CH.height_px(who, px_per_m) at the same depth')


def sheet_lineup2():
    _lineup('lineup2', ['cop', 'cop2', 'doctor', 'nurse', 'mom_hosp', 'narrator_new', 'narrator_neat', 'june_dress', 'narrator_kid', 'dale'],
            ['OFFICER', 'OFFICER 2', 'DOCTOR', 'NURSE', 'MOM\'S BODY, HOSPITAL', 'THE THING IN ME', '...AT THE VISITS', 'JUNE, YELLOW DRESS',
             'ME AT SIX', 'DALE (55)'],
            360.0, 'mom_hosp = the narrator inside Mom\'s body; narrator_new / narrator_neat = the thing inside the narrator\'s body (never blinks)')


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


def sheet_turn_bunny():
    _turn('turn_bunny', [('bunny', None)], 'THE BUNNYMAN: TURNAROUND',
          'Grey plush mascot suit worn by a tall man: one ear snapped, matted dark fur, rust-brown belly, rips, dead matte glass eyes; zipper in the back',
          380.0)
    _turn('turn_bunny87', [('bunny87', None)], 'THE BUNNYMAN, 1987: TURNAROUND',
          'The clean department-store mascot: fluffy light grey, white belly, both ears up, glossy black eyes, pink nose and inner ears', 380.0)


def sheet_turn_family():
    _turn('turn_family', [('mom', None), ('narrator', None), ('june', None)], 'MOM, THE NARRATOR, JUNE: TURNAROUNDS',
          'Faces keep their features in 3/4 (the muzzle / nose and eyes stay inside the head), hair frames the face and hangs behind it in profile')


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


def sheet_faces_mom():
    _faces('faces_mom', [
        ('mom', P_(None), 'neutral'), ('mom', P_('warm_smile', h_turn=0.25), 'warm smile (as people see her)'),
        ('mom', P_('too_still', h_turn=-0.2), 'too still: the eyes do not smile'), ('mom', P_('too_still', m_press=0.6, h_tilt=8, hum=1.0), 'humming the jingle'),
        ('mom', P_('proud', h_turn=0.3), '"I\'m so proud of you"'), ('mom', P_('dead_stare', h_nod=0.2), 'staring at the ring'),
        ('mom', P_('shout', h_turn=0.2), '"GET OUT OF MY HOUSE"'), ('mom', P_('proud', scratch=1.0, mess=0.7), 'scratched to ribbons, smiling'),
        ('mom', P_('too_still', h_nod=0.25, look_y=0.5, _gaze=1.0), 'looking down at June'),
        ('mom_hosp', P_('haunted'), 'the narrator in her body'), ('mom_hosp', P_('terror', h_turn=0.2), 'screaming my own name'),
        ('mom_hosp', P_('cry', h_turn=-0.2), 'June whispers "I know it\'s you"'),
    ], 'MOM (LAURIE, 43): FACES', 'A pretty, warm face whose smile is a little too still; the hospital rows are the narrator inside her body', WARM)


def sheet_faces_june():
    _faces('faces_june', [
        ('june', P_(None), 'neutral'), ('june', P_('warm_smile', h_turn=0.3), 'waving at Mister Bunny'),
        ('june', P_('whisper', h_turn=0.2), '"He\'s sad." (whisper)'), ('june', P_('sad'), 'sad'), ('june', P_('fear'), 'fear'),
        ('june', P_('kid_grin'), 'grin'), ('june', P_(None, lid_l=1.0, lid_r=1.0, m_open=0.2), 'eyes shut, counting'),
        ('june', P_('cry'), 'crying'), ('june_dress', P_('warm_smile', h_turn=-0.3), 'the yellow dress'),
        ('laurie87', P_('kid_grin'), 'Laurie, 1987: the photo'), ('laurie87', P_('too_still'), 'Laurie at sunrise (humming)'),
        ('narrator_kid', P_('neutral', h_turn=0.3), 'me at six'),
    ], 'JUNE (7), LAURIE (1987), ME AT SIX: FACES', 'Children: big irises, rounder heads, the lids rest open; June\'s pigtails and Laurie\'s ribbon bows')


def sheet_faces_narrator():
    _faces('faces_narrator', [
        ('narrator', P_(None), 'neutral'), ('narrator', P_('nervous', h_turn=0.3), 'nervous'), ('narrator', P_('fear', h_turn=-0.2), 'fear'),
        ('narrator', P_('terror'), 'terror'), ('narrator', P_('shock'), 'the ring'), ('narrator', P_('determined', h_turn=0.25), 'not her: me'),
        ('narrator', P_(None, lid_l=1, lid_r=1, squint=0.6, brow_angry=0.3, brow_sad=0.4, m_press=0.5), 'eyes squeezed: "Six. Seven."'),
        ('narrator', P_('sleep', h_tilt=-14), 'asleep on the couch'), ('narrator', P_('cry'), 'crying'),
        ('narrator_new', P_('wrong_smile', h_turn=-0.2), 'the thing in me: smiling'), ('narrator_new', P_('wrong_smile', hum=1, m_press=0.5), 'it hums'),
        ('narrator_neat', P_('wrong_smile', h_turn=0.25), 'straight A\'s, never late'),
    ], 'THE NARRATOR (16): FACES', 'Neither clearly a boy nor a girl: chin-length hair, a soft jaw, no make-up; the bottom row is the thing wearing that body')


def sheet_faces_others():
    _faces('faces_others', [
        ('bunny', P_(None), 'the Bunnyman (now)', NIGHT), ('bunny', P_(None, h_turn=0.5, h_tilt=-12), 'the head tilt', NIGHT),
        ('bunny87', P_(None, h_turn=0.3), '1987 mascot'), ('bunny', P_('little_girl', unmask=1.0), 'Dale, the mask half off'),
        ('bunny', P_('little_girl', unmask=1.0, m_open=0.5, m_round=0.2), '"Mama."'), ('bunny', P_('little_girl', unmask=1.0, eye_open=0.45, still=1.0, tears=0.4), 'then still'),
        ('grandma', P_('warm_smile'), 'Grandma'), ('grandma', P_('sad', h_turn=0.2), '"Not after the woods."'),
        ('dad', P_(None, h_turn=0.3), 'Dad'), ('dad', P_('determined'), '"to talk to it"'),
        ('cop', P_('sad', h_turn=0.3), 'officer'), ('nurse', P_('polite', h_turn=-0.3), 'nurse'),
    ], 'THE BUNNYMAN, DALE, GRANDMA, DAD, POLICE, HOSPITAL: FACES', 'The mask never lip-syncs (the voice is inside it); Dale\'s face has the wide wet eyes of a terrified little girl')


def sheet_mouths():
    surf, cv, pen = canvas()
    title(cv, 'MOUTH SHAPES (LIP SYNC ON CHARACTER LINES ONLY)', 'a.talk([(t0, t1, text)]) maps letters to these shapes; nobody\'s lips move on the narrator\'s lines; the Bunnyman\'s mask never moves')
    vis = ['rest', 'M', 'F', 'L', 'E', 'I', 'A', 'O', 'U']
    whos = ['mom', 'june', 'narrator', 'dale']
    cw = 1920 / len(vis); ch = 230
    for r, who in enumerate(whos):
        for i, v in enumerate(vis):
            o, wd, rd, te, pr = CH.VISEMES[v]
            P = CH.Pose(m_open=o, m_wide=wd, m_round=rd, teeth=te, m_press=pr)
            x = cw * i + cw / 2; y = 150 + r * ch + 95
            CH.draw_head(pen, who if who != 'dale' else 'dale', x, y, 170, P, detail=2, t=0.5)
            if r == 0: label(cv, v, x, 128, 18, '#ffd479')
        label(cv, who.upper(), 60, 150 + r * ch + 200, 15, '#9aa3b8')
    save(surf, 'mouths')


def sheet_bunny_states():
    surf, cv, pen = canvas()
    title(cv, 'THE BUNNYMAN: STATES', '1987 parade mascot; now at the treeline; paws; the mask coming off at the bottom of the stairs; the crayon drawing')
    floor(pen, 700)
    a = CH.Acting('bunny87', seed=2, height=CH.height_px('bunny87', 225)); a.hold_prop('basket', -1)
    a.reach(-1, None, -1, out=40.0, down=230.0, fwd=150.0, shape='grip', up=0.0, fade=0.01); a.wave(0.0, 5.0, 1)
    CH.draw(pen, 'bunny87', 170, 700, a.height, a.at(0.9), t=0.9); label(cv, '1987: basket, waving', 170, 730)
    b = CH.Acting('bunny', seed=3, height=CH.height_px('bunny', 225)); b.wave(0.0, 5.0, 1, slow=True)
    CH.draw(pen, 'bunny', 430, 700, b.height, b.at(1.2), t=1.2, light=NIGHT); label(cv, 'now: the slow wave', 430, 730)
    c = CH.Acting('bunny', seed=4, height=CH.height_px('bunny', 225)).place(720, 700)
    c.point_at(0.0, (1100, 330), side=1, dur=0.3, z=500.0); c.set(0, None, 0.3, h_tilt=-10)
    CH.draw(pen, 'bunny', 720, 700, c.height, c.at(1.0), t=1.0, light=NIGHT); label(cv, 'the point (past us)', 720, 730)
    d = CH.Acting('bunny', seed=5, height=CH.height_px('bunny', 225)); d.drag_hatchet(-1, None, -1)
    CH.draw(pen, 'bunny', 990, 700, d.height, d.at(1.0), t=1.0, light=NIGHT); label(cv, 'the hatchet', 990, 730)
    for i, sh in enumerate(['paw', 'paw_open', 'paw_point', 'paw_grip', 'paw_flat']):
        x = 1160 + i * 150
        CH._draw_paw(CH.Ctx(pen, skia.Matrix(), 4.0), CH.CAST['bunny'], sh, x, 300, 1.5, 180.0 if sh != 'paw_grip' else 0.0, 1, 2)
        label(cv, sh, x, 430, 14, '#9aa3b8')
    for i, u in enumerate((0.0, 0.6, 1.0)):
        x = 1200 + i * 230
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x - 112, 470, 224, 300))
        CH.draw_bust(pen, 'bunny', x, 660, 0.3, CH.Pose('little_girl', unmask=u), t=0.5)
        cv.restore()
        label(cv, 'unmask %.1f' % u, x, 790, 14, '#9aa3b8')
    e = CH.Acting('bunny', seed=6, height=CH.height_px('bunny', 250), expr='little_girl').place(470, 1010)
    e.lie(-1.0, 'up'); e.unmask(-1.0, 0.01)
    CH.draw(pen, 'bunny', 470, 1010, e.height, e.at(1.0), t=1.0); label(cv, 'dead at the bottom of the stairs', 470, 1050)
    CH.draw_crayon_drawing(pen, 1110, 930, 200, 0.0, -5)
    label(cv, 'the drawing', 1110, 1066, 14, '#9aa3b8')
    save(surf, 'bunny_states')


def sheet_props():
    surf, cv, pen = canvas()
    title(cv, 'PROPS (ONE SCALE, IN CENTIMETRES)', 'Held props sit in the gripping hand (PROPS3); on a surface draw_prop3(pen, name, x, y, px_per_cm) draws the same size: no pops on pick-up')
    ppc = 7.0
    items = [('egg', 0), ('egg_gold', 0), ('egg_top', 0), ('egg_bot_ring', 0), ('ring', 0), ('key', 0), ('diary', 0), ('diary_open', 0),
             ('dress_tiny', 0), ('hatchet', 0), ('maglite', 90), ('basket', 0), ('clipboard', 0), ('drawing', 0)]
    xs = [120, 230, 340, 450, 560, 660, 800, 990, 1180, 1370, 1520, 1690, 1840, 120]
    for i, (nm, ang) in enumerate(items[:-1]):
        x = xs[i]; y = 480
        s = ppc if nm not in ('hatchet', 'basket', 'clipboard', 'dress_tiny') else ppc * 0.75
        CH.draw_prop3(pen, nm, x, y, s, ang, 2, 0.4)
        label(cv, nm, x, 820 if nm in ('dress_tiny', 'hatchet') else 640, 14, '#9aa3b8')
    m = CH.Ctx(pen, skia.Matrix(), 4.0)
    CH._draw_oven_mitt(m, CH.CAST['mom'], 400, 860, 1.5, 0.0, 1, 2); label(cv, 'oven mitt (hand shape \'oven\')', 400, 1000, 14, '#9aa3b8')
    CH.draw_torch_beam(pen, 1600, 820, 90.0, 300, 11, 0.9, 0.0); CH.draw_prop3(pen, 'maglite', 1560, 820, ppc * 0.7, 90.0)
    label(cv, 'torch_pos3 + draw_torch_beam', 1640, 900, 14, '#9aa3b8')
    save(surf, 'props')


def sheet_staging():
    surf, cv, pen = canvas()
    title(cv, 'STAGING TOOLS: FEET ON THE FLOOR, HANDS ON TARGET, EYES ON TARGET',
          'a.place(x, y_floor); sit_on(seat_y) keeps the feet on the floor; kneel_down(knees 0/1/2); reach_to / look_at world points; planted walk; run')
    y = 540
    floor(pen, y, '#1f222b')
    ppm = 230.0
    for i, (seat_m, lb) in enumerate(((0.47, 'chair 0.47 m'), (0.40, 'couch 0.40 m'), (0.25, 'low stool 0.25 m'))):
        x = 120 + i * 170
        seat = y - seat_m * ppm
        pen.fill(rect(x - 60, seat, 120, y - seat), '#4f5a6e'); pen.line(rect(x - 60, seat, 120, y - seat), 3)
        a = CH.Acting('mom', seed=1, height=CH.height_px('mom', ppm)).place(x, y); a.face(0.6); a.seated(seat)
        CH.draw(pen, 'mom', x, y, a.height, a.at(1.0), t=1.0)
        label(cv, lb, x, y + 34, 14, '#9aa3b8')
    for i, (k, lb) in enumerate(((0, 'one knee'), (1, 'both knees'), (2, 'on the heels'))):
        x = 650 + i * 150
        a = CH.Acting('narrator', seed=2, height=CH.height_px('narrator', ppm)).place(x, y); a.face(0.6); a.kneel_down(-1.0, 0.01, knees=k)
        CH.draw(pen, 'narrator', x, y, a.height, a.at(1.0), t=1.0)
        label(cv, lb, x, y + 34, 14, '#9aa3b8')
    # reach precision: targets round the figure inside its reach, plus one out of reach (reported in a.misses)
    x0 = 1430
    who = 'mom'
    a0 = CH.Acting(who, seed=3, height=CH.height_px(who, ppm)).place(x0, y)
    sh = a0.where(1.0, 'shoulder_l'); shr = a0.where(1.0, 'shoulder_r')
    R = CH._arm_len(CH.CAST[who]) * a0.height / 1000.0
    tgts = [(sh[0] + R * 0.75 * math.cos(q), sh[1] + R * 0.75 * math.sin(q)) for q in (-0.9, -0.2, 0.5, 1.1)]
    tgts += [(shr[0] - R * 0.7 * math.cos(q), shr[1] + R * 0.7 * math.sin(q)) for q in (-0.5, 0.4)]
    tgts += [(sh[0] + R * 1.5, sh[1] + 20)]
    for i, tg in enumerate(tgts):
        a = CH.Acting(who, seed=3, height=a0.height).place(x0, y)
        sd = 1 if tg[0] > x0 else -1
        a.reach_to(0.0, sd, tg, dur=0.2, contact='palm', shape='open', lean=False)
        hp = a.where(1.0, 'hand_l' if sd > 0 else 'hand_r')
        if i == 1: CH.draw(pen, who, x0, y, a.height, a.at(1.0), t=1.0)
        miss = math.hypot(hp[0] - tg[0], hp[1] - tg[1])
        pen.fill(oval(tg[0], tg[1], 8), '#ff5a6a', 210)
        pen.line(poly([tg, hp], False), 2, '#ffd479'); pen.fill(oval(hp[0], hp[1], 4), '#ffd479')
        text(cv, '%.0f px' % miss, tg[0], tg[1] - 14, 700, 12, '#ffd479' if miss < 6 else '#ff8a8a', 255, 0.0, 'center')
    label(cv, 'reach_to: palm (yellow) on target (red); the far one is out of reach -> a.misses', x0 + 60, y + 34, 13, '#9aa3b8')
    # look-at: the head follows a target round the figure
    y2 = 990
    floor(pen, y2, '#1b1e26')
    ppm2 = 230.0
    tg = [(130, 640), (470, 960), (820, 660)]
    for i, t_ in enumerate(tg):
        x = 300 + i * 170
        a = CH.Acting('narrator', seed=4, height=CH.height_px('narrator', ppm2)).place(x, y2); a.look_at(0.0, t_, dur=0.1)
        CH.draw(pen, 'narrator', x, y2, a.height, a.at(1.0), t=1.0)
        pen.fill(oval(t_[0], t_[1], 10), '#7ad0ff', 220)
        e = a.where(1.0, 'eyes'); pen.line(poly([e, t_], False), 1.5, '#7ad0ff', 150)
    label(cv, 'look_at: head + eyes on the blue targets', 470, y2 + 34, 14, '#9aa3b8')
    # planted walk: ghost frames, the stance foot stays put
    a = CH.Acting('mom', seed=5, height=CH.height_px('mom', ppm2)).place(940, y2)
    a.walk(0.0, 2.4, 0.0, 380.0, facing=1.0, surface='inside')
    for k in range(4):
        t = 0.5 + k * 0.42
        cv.saveLayer(None, skia.Paint(Alphaf=0.35 + 0.15 * (k == 3)))
        CH.draw(pen, 'mom', 940, y2, a.height, a.at(t), t=t)
        cv.restore()
    label(cv, 'walk: ghosts every 0.42 s (stance feet planted)', 1130, y2 + 34, 14, '#9aa3b8')
    r = CH.Acting('narrator', seed=6, height=CH.height_px('narrator', ppm2)).place(1480, y2)
    r.run(0.0, 2.0, 0.0, 330.0)
    for k in range(4):
        t = 0.35 + k * 0.17
        cv.saveLayer(None, skia.Paint(Alphaf=0.35 + 0.15 * (k == 3)))
        CH.draw(pen, 'narrator', 1480, y2, r.height, r.at(t), t=t)
        cv.restore()
    label(cv, 'run: flight phase, pumping arms', 1650, y2 + 34, 14, '#9aa3b8')
    save(surf, 'staging')


SHEETS = dict(lineup=sheet_lineup, lineup2=sheet_lineup2, turn_bunny=sheet_turn_bunny, turn_family=sheet_turn_family,
              faces_mom=sheet_faces_mom, faces_june=sheet_faces_june, faces_narrator=sheet_faces_narrator,
              faces_others=sheet_faces_others, mouths=sheet_mouths, bunny_states=sheet_bunny_states, props=sheet_props,
              staging=sheet_staging)

if __name__ == '__main__':
    names = sys.argv[1:] or list(SHEETS)
    for n in names: SHEETS[n]()
