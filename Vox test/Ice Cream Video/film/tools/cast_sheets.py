"""cast_sheets.py: model sheets of the ice cream truck film's cast (characters_ice.py), written to W/cast/.

    cd "Vox test/Ice Cream Video/film" && python3 tools/cast_sheets.py [names...]     (default: all sheets)

Sheets (1920x1080 JPEG): sh_turn (Mister Shiver turnaround), sh_head (head states), sh_transform (THE TRANSFORMATION in
8 steps), sh_monster (monster form, views + silhouette read test), sh_mood (beside the owner's references, at film
size), sh_limits (the bible's hard limits), lineup (everyone to scale), faces_kids, faces_adults.
"""
import os, sys, math
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import numpy as np
import cv2
import skia
from engine.core import set_render_size, Pen, CFG, rect, rrect, oval, poly, smooth, text, mix
import characters as CH
if not hasattr(CH, 'ICE_API'):          # until characters.py runs characters_ice.py itself (see CAST.md)
    _ICE = os.path.join(HERE, 'characters_ice.py'); exec(compile(open(_ICE).read(), _ICE, 'exec'), CH.__dict__)

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


def _faces(name, items, ttl, sub, light=None, cols=6, bg=None, cyk=0.48, sk=0.62):
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
        dxh = 0.0
        if CH.CAST[who].get('whistle') and not CH.CAST[who].get('shiver'):           # keep his head centred when the body turns (the neck juts forward)
            hx = CH._WSView(P).p2(CH._ws_rig(P)['head'])[0]
            dxh = hx * CH._WSU * (600.0 * ch / 600.0 * sk) / CH.CAST[who]['hh']
        CH.draw_bust(pen, who, x0 + cw / 2 - dxh, y0 + ch * cyk, ch / 600.0 * sk, P, t=0.6, light=lt, detail=2)
        cv.restore()
        pen.fill(rect(x0 + 4, y0 + ch - 34, cw - 8, 30), '#000000', 140)
        label(cv, lb, x0 + cw / 2, y0 + ch - 13, 15)
    save(surf, name)




def P_(expr=None, **kw):
    p = CH.Pose(expr) if expr else CH.Pose()
    for k, v in kw.items(): setattr(p, k, v)
    return p


NIGHTI = dict(rim='#9fb8ff', rim_a=70, side=1, key=-0.25)
PINKW = dict(rim='#ff9ccc', rim_a=90, side=-1, key=-0.2)
REFD = os.path.join(os.path.dirname(HERE), 'ref')


def _sh_bust(pen, x, y, scale, **kw):
    P = P_(**kw)
    CH.draw_bust(pen, 'shiver', x, y, scale, P, t=0.6, light=kw.pop('light', PINKW) if False else PINKW, detail=2)


def sheet_sh_turn():
    surf, cv, pen = canvas()
    title(cv, 'MISTER SHIVER: normal form turnaround', '6 ft 4, narrow, slightly hunched, long neck; bald chalk-white egg head a little too big; tiny blue eyes in dark sockets; buck-toothed too-wide smile; pink-and-white vertical stripes, pink bow tie + snowflake pin, SHIVER badge, white knitted gloves; no breath cloud')
    floor(pen, 980)
    ppm = 430
    for i, (turn, lb) in enumerate(((0.0, 'front'), (0.3, '3/4'), (0.5, 'three-quarter'), (1.0, 'profile'), (1.6, '3/4 back'), (2.0, 'back'))):
        P = P_(); P.turn = turn
        CH.draw(pen, 'shiver', 170 + i * 316, 980, CH.height_px('shiver', ppm), P, light=NIGHTI, t=0.6, detail=2)
        label(cv, lb, 170 + i * 316, 1030)
    for k, (m, lb) in enumerate(((1.0, '1 m'), (1.93, '1.93 m (crown)'))):
        y = 980 - m * ppm
        pen.line(poly([(20, y), (1900, y)], False), 1.5, '#ffffff', 40); label(cv, lb, 60, y - 6, 14)
    save(surf, 'sh_turn')


def sheet_sh_head():
    items = [('shiver', dict(h_turn=0.0), 'front: the vendor'), ('shiver', dict(h_turn=0.3), '3/4'),
             ('shiver', dict(h_turn=0.85), 'profile'), ('shiver', dict(h_turn=-0.25, h_nod=-0.3), 'looking down at Lina'),
             ('shiver', dict(h_turn=0.1, sh_smile=0.6), 'the smile widens'), ('shiver', dict(h_turn=0.1, sh_glim=1.0), 'GLIMPSE (one flicker)'),
             ('shiver', dict(h_turn=0.0, sh_m=0.56), 'red eyes, long bone mask'), ('shiver', dict(h_turn=0.25, sh_m=0.72), 'jaw to the chest, 3/4'),
             ('shiver', dict(h_turn=0.0, sh_m=1.0, sh_gape=1.0), 'the hung note: jaw gapes'), ('shiver', dict(h_turn=-0.3, sh_m=0.72), 'icicle teeth, 3/4'),
             ('shiver', dict(h_turn=0.0, sh_m=0.30), 'halfway back (shrinking)'), ('shiver', dict(h_turn=0.15), 'back to the smile')]
    items = [(w, P_(**kw), lb) for w, kw, lb in items]
    _faces('sh_head', items, 'MISTER SHIVER: head states', 'never blinks, never lip-syncs; frost flecks on the brow; cracks like ice on a pond on the mask', light=PINKW, cols=6, cyk=0.36, sk=0.62)


def sheet_sh_transform():
    surf, cv, pen = canvas()
    title(cv, 'THE TRANSFORMATION: one parameter (pose.sh_m), the bible\'s steps', 'Acting.transform(t0, times) keys these 8 states to the narration; he keeps waving; the chime keeps playing')
    cw = 1920 / 4; ch = 470
    for k, (m, nm) in enumerate(zip(CH.SH_STEPS, CH.SH_STEP_NAMES)):
        c_, r_ = k % 4, k // 4
        x0, y0 = c_ * cw, 120 + r_ * ch
        pen.fill(rect(x0 + 4, y0 + 4, cw - 8, ch - 8), '#2a1c26')
        pen.linear(rect(x0 + 4, y0 + 4, cw - 8, ch - 8), 0, y0, 0, y0 + ch, [(0, '#ffb3d2', 255), (1, '#c8487e', 255)])
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x0 + 4, y0 + 4, cw - 8, ch - 8))
        P = P_(); P.sh_m = m; P.h_turn = 0.08; P.ws_bend = 0.1
        legs = m >= 0.7
        if legs:
            sc = 0.17
            P.turn = 0.12
            CH.draw(pen, 'shiver', x0 + cw / 2, y0 + ch * 1.02, 0.85 * ch, P, light=PINKW, t=0.6, detail=2)
        else:
            CH.draw_bust(pen, 'shiver', x0 + cw / 2, y0 + ch * 0.36, ch / 600.0 * 0.62, P, t=0.6, light=PINKW, detail=2)
        cv.restore()
        pen.fill(rect(x0 + 4, y0 + ch - 34, cw - 8, 30), '#000000', 150)
        label(cv, '%d. %s  (sh_m %.2f)' % (k, nm, m), x0 + cw / 2, y0 + ch - 13, 15)
    save(surf, 'sh_transform')


def sheet_sh_monster():
    surf, cv, pen = canvas()
    title(cv, 'MISTER SHIVER: monster form', 'eight brown jointed legs out of the split back (frost rime on every joint, pale needle tips); the small striped body slung under a high arch; long bone mask, red eyes, jaw to the chest, icicle teeth')
    pen.fill(rect(0, 120, 1920, 960), '#101420')
    pen.fill(rect(0, 900, 1280, 180), '#c9d6ea')
    for i, (turn, lift, ht) in enumerate(((0.0, 150, 0.0), (0.6, 150, 0.2))):
        P = P_(); P.turn = turn; P.sh_m = 1.0; P.sh_lift = lift; P.h_turn = ht
        CH.draw(pen, 'shiver', 330 + i * 620, 900, CH.height_px('shiver', 220), P, light=NIGHTI, t=0.6, detail=2)
    # silhouette read test (bible): black against the snow
    pen.fill(rect(1290, 120, 630, 960), '#dfe8f4')
    surf2 = skia.Surface(CFG.rw, CFG.rh); cv2_ = surf2.getCanvas(); cv2_.clear(skia.Color(0, 0, 0, 0)); cv2_.scale(CFG.k, CFG.k)
    P = P_(); P.turn = 0.15; P.sh_m = 1.0; P.sh_lift = 150
    CH.draw(Pen(cv2_), 'shiver', 1605, 900, CH.height_px('shiver', 150), P, t=0.6, detail=1)
    img = surf2.makeImageSnapshot()
    p = skia.Paint(ColorFilter=skia.ColorFilters.Blend(skia.Color(10, 10, 14), skia.BlendMode.kSrcIn))
    cv.save(); cv.resetMatrix(); cv.clipRect(skia.Rect.MakeXYWH(1290 * CFG.k, 120 * CFG.k, 630 * CFG.k, 960 * CFG.k)); cv.drawImage(img, 0, 0, skia.SamplingOptions(), p); cv.restore()
    label(cv, 'silhouette read test: arch of legs, slung body, hanging head', 1605, 1060, 15, '#20242c')
    save(surf, 'sh_monster')


def sheet_sh_mood():
    surf, cv, pen = canvas()
    title(cv, 'MISTER SHIVER beside the owner\'s mood references (archetype only; ours is original)', 'left: references. right: our two forms at film size (a 1/2-screen close-up and a full-frame wide, shown at 1/2 scale)')
    for k, fn in enumerate(('owner_mood_normal.jpg', 'owner_mood_monster.jpg')):
        im = cv2.imread(os.path.join(REFD, fn))
        if im is None: continue
        h = 440; w = int(im.shape[1] * h / im.shape[0])
        im = cv2.resize(im, (w, h))
        rgba = cv2.cvtColor(im, cv2.COLOR_BGR2RGBA)
        sk = skia.Image.fromarray(rgba)
        cv.drawImageRect(sk, skia.Rect.MakeXYWH(30, 130 + k * 470, min(w, 560), h))
    # film-size panels: 960x540 each (a half-scale view of a 1920x1080 frame)
    for k, m in enumerate((0.0, 1.0)):
        x0, y0 = 640, 130 + k * 470
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x0, y0, 1240, 440))
        pen.linear(rect(x0, y0, 1240, 440), 0, y0, 0, y0 + 440, [(0, '#05070f'), (1, '#1d2a4a')])
        pen.fill(rect(x0, y0 + 360, 1240, 80), '#c9d6ea')
        if m == 0:
            pen.fill(rect(x0 + 380, y0 + 60, 480, 330), '#ff9fca')
            P = P_(); P.ws_bend = 0.15
            CH.draw_bust(pen, 'shiver', x0 + 620, y0 + 190, 0.33, P, t=0.6, light=PINKW, detail=2)
        else:
            P = P_(); P.sh_m = 1.0; P.sh_lift = 150; P.turn = 0.1
            CH.draw(pen, 'shiver', x0 + 620, y0 + 420, 330, P, t=0.6, light=NIGHTI, detail=2)
        cv.restore()
    save(surf, 'sh_mood')


def sheet_sh_limits():
    surf, cv, pen = canvas()
    title(cv, 'Hard limits (story bible), checked', 'each cell is drawn by the cast code itself')
    cells = [('NO breath cloud, ever (CAST breath=0)', dict()), ('SHIVER badge + snowflake pin (no other name)', dict()),
             ('white KNITTED gloves; nothing in his hands (no ray, no weapon)', dict()), ('icicle teeth, no tongue, no blood', dict(sh_m=0.72))]
    cw = 1920 / 4
    for i, (lb, kw) in enumerate(cells):
        x0 = i * cw
        pen.fill(rect(x0 + 4, 124, cw - 8, 520), '#232633')
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x0 + 4, 124, cw - 8, 520))
        P = P_(**kw); P.h_turn = 0.1
        CH.draw_bust(pen, 'shiver', x0 + cw / 2, 330, 0.42, P, t=0.6, light=NIGHTI, detail=2)
        cv.restore()
        label(cv, lb, x0 + cw / 2, 630, 14)
    lines = ['no "Rod", no game name or pun anywhere in the cast code or sheets (grep-checked)',
             'the truck stand-in: a frosted SNOWFLAKE on the roof (never a cone); no plate; interior beyond the window never drawn (pink light only)',
             'mitten bunting: single mittens, the oldest small and RED at the LEFT; Lina\'s added at the RIGHT (truck_front mitten_lina)',
             'nobody inside the truck; taking is never shown; legs touch snow, coats and blankets only (leg_to targets in the clips)',
             'he never lip-syncs: say() only bobs the head (the whistle-rig rule); no blinks (blink_rate 0)',
             'our chime is the audio team\'s; the cast emits sound events only (clips.json)']
    for k, s in enumerate(lines):
        text(cv, '- ' + s, 60, 700 + k * 52, 1800, 21, '#d8dbe4', 255, 0.02, 'left')
    save(surf, 'sh_limits')


def sheet_lineup():
    surf, cv, pen = canvas()
    title(cv, 'Ice cream film cast to scale', 'draw height = CH.height_px(id, px_per_m)')
    floor(pen, 980)
    ppm = 400
    ids = ['shiver', 'dad', 'kessler', 'kessler_out', 'mom_photo', 'adam', 'adam_in', 'lina', 'lina_pj', 'walter58', 'benny']
    for i, w in enumerate(ids):
        P = P_(); P.turn = 0.2 if w != 'shiver' else 0.05
        CH.draw(pen, w, 95 + i * 174, 980, CH.height_px(w, ppm), P, light=NIGHTI, t=0.6, detail=2)
        label(cv, w, 95 + i * 174, 1030, 15)
    save(surf, 'lineup')


def sheet_faces():
    kids = [('adam', 'neutral', 'Adam: neutral'), ('adam', 'fear', 'fear'), ('adam', 'resolve', 'resolve'), ('adam', 'terrified_call', '"Dad!"'),
            ('adam', 'tender', '"Good. Shivering..."'), ('adam_in', 'guilt', '"Old people like it cold"'),
            ('lina', 'kid_grin', 'Lina: gap-toothed grin'), ('lina', 'sleepy', 'sleepy (cold)'), ('lina', 'dazed', '"I\'m warm, Adam"'),
            ('lina', 'fear', 'fear'), ('lina', 'pleading', '"Don\'t leave me"'), ('lina_pj', 'kind_smile', '"You\'re not by yourself"')]
    _faces('faces_kids', [(w, P_(e), lb) for w, e, lb in kids], 'Adam and Lina: expressions', 'v3 faces: brows, lids, eyes lock on what the line is about', light=NIGHTI, cols=6)
    ads = [('dad', 'warm', 'Dad: warm ("Over.")'), ('dad', 'grim_drive', 'in the cab'), ('dad', 'shout', 'horn, again and again'),
           ('kessler', 'stern', 'Kessler: grumpy'), ('kessler', 'lonely', 'at his dark window'), ('kessler_out', 'dazed', 'out in the snow: not shivering'),
           ('kessler_out', 'sad', '"Bye, Benny."'), ('kessler', 'tender', 'cocoa: "First time anyone knocked"'), ('mom_photo', 'warm_smile', 'Mom (photo)'),
           ('shiver_mom', 'still_smile', 'HIS copy at the glass: no breath'), ('medic_a', 'focused', 'paramedic'), ('medic_b', 'calm_firm', 'paramedic')]
    _faces('faces_adults', [(w, P_(e), lb) for w, e, lb in ads], 'Dad, Mr. Kessler, Mom, paramedics', '', light=NIGHTI, cols=6)


SHEETS = dict(sh_turn=sheet_sh_turn, sh_head=sheet_sh_head, sh_transform=sheet_sh_transform, sh_monster=sheet_sh_monster,
              sh_mood=sheet_sh_mood, sh_limits=sheet_sh_limits, lineup=sheet_lineup, faces=sheet_faces)

if __name__ == '__main__':
    names = sys.argv[1:] or list(SHEETS)
    for n in names: SHEETS[n]()
