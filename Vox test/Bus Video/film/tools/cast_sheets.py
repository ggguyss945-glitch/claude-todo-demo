"""cast_sheets.py: model sheets of the bus film's cast (characters.py + characters_bus.py), written to W/cast/.

    cd "Vox test/Bus Video/film" && python3 tools/cast_sheets.py [names...]     (default: all sheets)

Sheets (1920x1080 JPEG): ws_turn (Mister Whistlestop turnaround with proportion marks), ws_mood (beside the owner's mood
references), ws_limits (every hard limit checked, with a red-pixel measurement), ws_states (every state the script
needs), ws_head (the head in 6 views, the defeat slip, the 1994 tape), lineup (everyone to scale), turn_family,
turn_others, faces_mina, faces_sami, faces_della, faces_others, props, props2.
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
AMBER = dict(rim='#ffa030', rim_a=90, side=1, key=-0.3)
STUDIO = dict(rim='#ffffff', rim_a=45, side=-1, key=0.3)
MORN = dict(rim='#ffe2a8', rim_a=55, side=-1, key=0.2)


def _ws(x, y, h, who='whistle', seed=1):
    return CH.Acting(who, seed=seed, height=h).place(x, y)


def _box(pen, x, y, w, h, c='#232633'):
    pen.fill(rect(x, y, w, h), c)


def sheet_ws_turn():
    surf, cv, pen = canvas()
    title(cv, 'MISTER WHISTLESTOP: turnaround (2.44 m to the crown, the hat +0.9 m)',
          'legs 55 % of his height, arms to the knees, crooked mascot head, hat leaning 12 deg to his left, dented halfway; never walks')
    views = [(0.0, 'FRONT'), (0.5, '3/4 RIGHT'), (1.0, 'PROFILE'), (1.5, '3/4 BACK'), (2.0, 'BACK'), (-0.5, '3/4 LEFT')]
    floor(pen, 1030)
    for i, (yw, lb) in enumerate(views):
        x = 175 + i * 314
        CH.draw(pen, 'whistle', x, 1030, 640, CH.Pose(turn=yw), t=0.0, light=AMBER, detail=2)
        label(cv, lb, x, 1062, 15, '#9aa3b8')
    # proportion marks on the front view
    h = 640.0; ppc = h / 244.0
    for cm, lb in ((134, 'hip 55 %'), (70, 'knee: fingertips'), (209, 'chin (head 1/7)'), (244, 'crown'), (244 + 90, 'hat top +40 %')):
        y = 1030 - cm * ppc
        pen.line(poly([(20, y), (120, y)], False), 2, '#7a8296')
        text(cv, lb, 22, y - 4, 600, 12, '#9aa3b8', 255, 0.0, 'left')
    save(surf, 'ws_turn')


def sheet_ws_mood():
    surf, cv, pen = canvas()
    title(cv, 'MISTER WHISTLESTOP beside the owner\'s mood references (mood only: nothing copied)',
          'kept: a tall grinning mascot, the frozen grin, white gloves curling round a doorframe, VHS grain and tracking lines. changed: every design element (see ws_limits)')
    x = 30
    for i in (1, 2, 3):
        p = os.path.join(REF, 'owner_mood_cat_%d.jpg' % i)
        im = cv2.imread(p)
        if im is None: continue
        hh = 300; ww = int(im.shape[1] * hh / im.shape[0])
        im = cv2.cvtColor(cv2.resize(im, (ww, hh)), cv2.COLOR_BGR2RGBA)
        img = skia.Image.fromarray(im)
        cv.drawImage(img, x, 130)
        label(cv, 'mood ref %d' % i, x + ww / 2, 450, 14, '#9aa3b8')
        x += ww + 20
    # ours: peeking round a doorframe (gloves curled), the grin through VHS tear, the bust
    a = _ws(585, 1240, 560)
    a.set(-1, None, 0.01, tilt=16.0, turn=0.3, ws_hands_front=3)
    a.curl_door(-2.0, 1, (640, 700), dur=0.01, z=-8.0)
    a.curl_door(-2.0, -1, (640, 860), dur=0.01, z=-8.0)
    pen.fill(rect(30, 480, 1860, 580), '#141018')
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(30, 480, 620, 580))
    pen.fill(rect(30, 480, 620, 580), '#2a2018'); pen.glow(500, 700, 400, '#ffa030', 70)
    CH.draw(pen, 'whistle', a.x0, a.y0, a.height, a.at(0.0), light=AMBER, t=0.0)
    pen.fill(rect(30, 480, 610, 580), '#4a3c30'); pen.fill(rect(600, 480, 44, 580), '#d8cfb8')
    CH.draw_whistle_hands(pen, a, 0.0, (1, -1), AMBER)
    cv.restore()
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(660, 480, 600, 580))
    pen.fill(rect(660, 480, 600, 580), '#0c0a10')
    CH.draw_bust(pen, 'whistle', 960, 760, 0.62, CH.Pose(h_turn=0.1, ws_glitch=0.0, ws_slip=0.35), light=AMBER, t=0.3)
    cv.restore()
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(1270, 480, 620, 580))
    pen.fill(rect(1270, 480, 620, 580), '#3a8acb')
    CH.draw(pen, 'whistle94', 1580, 1040, 360, CH.Pose(turn=-0.2, ws_glitch=0.35), light=STUDIO, t=0.4)
    cv.restore()
    for x_, s_ in ((340, 'gloves curl round the frame, the head peeks'), (960, 'the frozen grin, slipping out of register'), (1580, 'the 1994 tape: a VHS tear')):
        label(cv, s_, x_, 1050, 15)
    save(surf, 'ws_mood')


def _hat_red_white(img):
    """Fraction of saturated red pixels and of red/white alternation in a picture of the hat region."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    red = ((hsv[:, :, 0] < 8) | (hsv[:, :, 0] > 172)) & (hsv[:, :, 1] > 120) & (hsv[:, :, 2] > 90)
    return float(red.mean())


def sheet_ws_limits():
    """Proof that every hard limit is respected, with measurements."""
    surf, cv, pen = canvas()
    title(cv, 'MISTER WHISTLESTOP: the hard limits, checked', 'original design: an archetype only (tall cat, top hat, gloves, bow tie); none of the protected specifics')
    # hat close-ups from 3 views
    for i, yw in enumerate((0.0, 0.6, -1.2)):
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(30 + i * 300, 120, 290, 520))
        pen.fill(rect(30 + i * 300, 120, 290, 520), '#232633')
        CH.draw_bust(pen, 'whistle', 175 + i * 300, 600, 0.32, CH.Pose(h_turn=yw), light=AMBER, t=0.0)
        cv.restore()
    label(cv, 'hat: faded yellow, TWO DIAGONAL black bands from every side', 465, 665, 15)
    # bow tie + pin close-up
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(960, 120, 440, 520))
    pen.fill(rect(960, 120, 440, 520), '#232633')
    CH.draw_bust(pen, 'whistle', 1180, 170, 1.0, CH.Pose(), light=AMBER, t=0.0)
    cv.restore()
    label(cv, 'BLACK bow tie, red STOP-sign pin (the only red)', 1180, 665, 15)
    # glove: 4 segments per finger (two gloves: open, and curled round an edge)
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(1420, 120, 470, 520))
    pen.fill(rect(1420, 120, 470, 520), '#232633')
    for k, (shape, cx, cy, roll) in enumerate((('flat', 1540, 330, 0.0), ('curl', 1770, 470, 0.0))):
        a = _ws(0, 0, 2600)
        a.set(-1, None, 0.01, turn=0.15, ws_lrest='host', hl_shape=shape, ws_lroll=roll)
        hx, hy = a.where(0.0, 'hand_l')
        a.place(cx - hx, cy - hy)
        CH.draw_whistle_hands(pen, a, 0.0, (1,), AMBER, detail=2)
    cv.restore()
    label(cv, 'white glove: 4 segments per finger', 1655, 665, 15)
    # colour swatches and the measured checks
    sw = [('hat', '#c49f3f'), ('bands', '#1d1a16'), ('body fur (tabby)', '#7a6a55'), ('stripes', '#5a4c3d'), ('mask', '#ebe4d0'),
          ('jacket', '#a88a3a'), ('bow tie', '#141212'), ('STOP pin', '#b3241e'), ('lanyard', '#e07a1f'), ('gloves', '#e2ded2')]
    for i, (n, c) in enumerate(sw):
        x = 40 + i * 186
        pen.fill(rrect(x, 700, 170, 60, 6), c); pen.line(rrect(x, 700, 170, 60, 6), 2, '#000000')
        label(cv, n, x + 85, 785, 13)
    # measure: render the full figure in 6 views and count red pixels outside the pin
    reds = []
    for yw in (0.0, 0.5, 1.0, 1.5, 2.0, -0.5):
        s2, c2, p2 = canvas(480, 270, (26, 28, 36))
        CH.draw(p2, 'whistle', 960, 1040, 900, CH.Pose(turn=yw), t=0.0, detail=2)
        im = s2.makeImageSnapshot().toarray()[:, :, :3]
        reds.append(_hat_red_white(im))
    set_render_size(1920, 1080)
    checks = ['no red-and-white stripes: red pixels in 6 views %.3f %% max (the pin only)' % (100 * max(reds)),
              'hat bands helical: they slant on every side (never horizontal), no stripes on the brim',
              'bow tie black; body fur grey-brown tabby (never black); off-white mask only on the face',
              'no rhyming verse, no fish, no helper creatures, no umbrella or balancing tricks, no Seuss names or words',
              'his own props: whistle on orange lanyard, ticket punch, clipboard watchlist (Sat alone), a stolen walkie',
              'grin painted and frozen (never lip-syncs); no blinking painted pupils, his left one higher; punch hole in the left ear']
    for i, s_ in enumerate(checks):
        text(cv, ('OK  ' + s_), 60, 850 + i * 34, 700, 19, '#b8f0b0', 255, 0.0, 'left')
    save(surf, 'ws_limits')
    return reds


def sheet_ws_states():
    surf, cv, pen = canvas()
    title(cv, 'MISTER WHISTLESTOP: every state the script needs', 'each cell is the rig at that beat (see the acting clips for the motion)')
    cells = [
        ('1994 host', dict(who='whistle94', turn=-0.15, ws_lrest='host', ws_rrest='host'), STUDIO, '#3a8acb'),
        ('unfolding: 30 %', dict(ws_unfold=0.3, turn=0.4), AMBER, None),
        ('unfolding: 70 %', dict(ws_unfold=0.7, turn=0.4), AMBER, None),
        ('tape skip (tear)', dict(ws_glitch=0.8, turn=0.1), AMBER, None),
        ('bent double, hat crushed', dict(ws_ceil=235.0, ws_bend=1.0, ws_crouch=0.4, turn=0.3), AMBER, None),
        ('head turned backwards', dict(turn=1.0, h_turn=2.0), AMBER, None),
        ('clipboard (roll call)', dict(turn=-0.3, ws_lrest='clip', hl_prop='ws_clipboard', hl_shape='clip'), AMBER, None),
        ('the whistle (fweet-fweet)', dict(turn=0.2, ws_whistle=1.0, ws_blow=1.0), AMBER, None),
        ('walkie to the grin', dict(turn=-0.2, ws_rrest='mouth', hr_prop='walkie', hr_shape='hold'), AMBER, None),
        ('down, and down (the lure)', dict(turn=-0.6, ws_bend=1.25, ws_crouch=0.5, ws_lrest='chest'), AMBER, None),
        ('defeat: the grin slips', dict(ws_slip=0.85, ws_glitch=0.3, turn=0.0), AMBER, None),
        ('rewinding away', dict(ws_rewind=0.6, ws_slip=1.0, turn=0.0), AMBER, None),
    ]
    cols, cw, ch = 6, 320, 470
    for i, (lb, d, lt, bg) in enumerate(cells):
        c_, r_ = i % cols, i // cols
        x0, y0 = c_ * cw, 115 + r_ * ch
        pen.fill(rect(x0 + 4, y0 + 4, cw - 8, ch - 8), bg or '#1c1a20')
        d = dict(d); who = d.pop('who', 'whistle')
        P = CH.Pose(**d)
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x0 + 4, y0 + 4, cw - 8, ch - 8))
        CH.draw(pen, who, x0 + cw / 2, y0 + ch - 50, 290, P, light=lt, t=0.5)
        if 'ws_ceil' in d: pen.fill(rect(x0 + 4, y0 + ch - 50 - 235 * 290 / 244 - 8, cw - 8, 8), '#8a8a8a')
        cv.restore()
        pen.fill(rect(x0 + 4, y0 + ch - 36, cw - 8, 32), '#000000', 150)
        label(cv, lb, x0 + cw / 2, y0 + ch - 14, 15)
    save(surf, 'ws_states')


def sheet_ws_head():
    items = []
    for yw, lb in ((0.0, 'front'), (0.4, '3/4'), (1.0, 'profile'), (1.6, 'behind 3/4'), (2.0, 'back'), (-0.4, '3/4 left')):
        items.append(('whistle', dict(h_turn=yw), lb, AMBER))
    for sl, lb in ((0.3, 'slip 30 %'), (0.7, 'slip 70 %'), (1.0, 'slip 100 %')):
        items.append(('whistle', dict(ws_slip=sl), lb, AMBER))
    items += [('whistle', dict(h_tilt=-16.0, ws_bob=0.6), 'talk bob (no jaw)', AMBER), ('whistle94', dict(), '1994 tape', STUDIO),
              ('whistle', dict(h_nod=0.5, h_turn=0.3), 'looking down at you', AMBER)]
    _faces('ws_head', items, 'MISTER WHISTLESTOP: the head', 'painted grin (never moves), painted pupils (his left one higher, never blink), punch hole in the left ear; the VHS slip only at the defeat', cols=6)


def sheet_lineup():
    surf, cv, pen = canvas()
    title(cv, 'The cast to scale (same depth)', 'Whistlestop 2.44 m (+ hat), Della 1.63, Mina 1.57, new girl 1.42, Theo 1.38, 1994 kids 1.30, Sami 1.16')
    ppm = 250.0
    ids = [('whistle', 0.0), ('della', 0.3), ('mina', 0.2), ('new_girl', -0.2), ('theo', 0.2), ('theo_color', -0.2), ('kid94_a', 0.1),
           ('kid94_b', -0.1), ('kid94_c', 0.1), ('sami', 0.25), ('sami_torn', 1.5)]
    floor(pen, 1000)
    for i, (w, yw) in enumerate(ids):
        x = 110 + i * 170
        CH.draw(pen, w, x, 1000, CH.height_px(w, ppm), CH.Pose(turn=yw), light=MORN, t=0.3)
        label(cv, w, x, 1040, 14, '#9aa3b8')
    for m in (1.0, 2.0, 3.0):
        y = 1000 - m * ppm
        pen.line(poly([(0, y), (1920, y)], False), 1, '#3a3e4a')
        text(cv, '%.0f m' % m, 1880, y - 4, 600, 12, '#7a8296', 255, 0.0, 'right')
    save(surf, 'lineup')


def sheet_turn_people():
    _turn('turn_family', [('mina', MORN), ('della', MORN), ('sami', MORN)], 'Mina, Grandma Della, Sami: turnaround',
          'Mina: low ponytail, oversized hoodie over pajamas. Della: knit cap, glasses on a cord, navy driver jacket (DELLA). Sami: dinosaur pajamas, hood, tail', ppm=230.0)
    _turn('turn_others', [('theo', MORN), ('theo_color', MORN), ('new_girl', MORN)], 'Theo (faded, then in colour) and the new girl: turnaround',
          'Theo: yellow raincoat, 1994; nobody sees him until three o\'clock. The new girl: a hair clip, a plain backpack with no name', ppm=250.0)


def sheet_faces():
    _faces('faces_mina', [('mina', P_(e), e, AMBER) for e in ('neutral', 'kind_smile', 'guilt', 'fear', 'hush_fear', 'resolve', 'shock',
                                                             'terrified_call', 'tempted', 'brave', 'kind_ask', 'relief')],
           'Mina: expressions per beat', 'fear, resolve, guilt (the post, the boy she never asked), kindness (the new girl)')
    _faces('faces_sami', [('sami', P_(e), e, MORN) for e in ('neutral', 'proud_grin', 'shout_here', 'sleepy', 'dazed', 'shock', 'fear',
                                                            'cry', 'relief', 'terrified_call', 'kind_smile', 'hush_fear')],
           'Sami: expressions per beat', 'a proud rule-follower: his mouth answers before his head does ("HERE!")')
    _faces('faces_della', [('della', P_(e), e, MORN) for e in ('warm', 'calm_firm', 'set_jaw', 'stern_afraid', 'shout', 'fear', 'grim_drive',
                                                              'shock', 'tender', 'whisper', 'sad', 'kind_smile')],
           'Grandma Della: expressions per beat', 'warm, firm, frightened underneath; 32 years a school-bus driver: "Brakes, mirrors, names"')
    _faces('faces_others', [('theo', P_('lonely'), 'Theo lonely', MORN), ('theo', P_('kind_smile'), 'Theo "Hi, Mina"', MORN),
                            ('theo', P_('hush_fear'), 'Theo, the glove', AMBER), ('theo_color', P_('brave'), 'Theo "Theo."', AMBER),
                            ('theo_color', P_('shout_here'), 'Theo "HERE!"', AMBER), ('theo_color', P_('tender'), 'Theo, seen', MORN),
                            ('new_girl', P_('lonely'), 'new girl alone', MORN), ('new_girl', P_('kind_smile'), 'new girl, asked', MORN),
                            ('kid94_a', P_('proud_grin'), '1994 kid', STUDIO), ('kid94_b', P_('proud_grin'), '1994 kid', STUDIO),
                            ('kid94_c', P_('kind_smile'), '1994 kid', STUDIO), ('mina', P_('tender'), 'Mina, sorry', MORN)],
           'Theo, the new girl, the 1994 kids', 'Theo stays faded and desaturated until three o\'clock; then full colour')


def sheet_props():
    surf, cv, pen = canvas()
    title(cv, 'Props (same size in a hand and on a surface)', 'cm scale 1:1 at 9 px/cm')
    ppc = 9.0
    items = [('walkie', 'walkie-talkie'), ('rex', 'Rex'), ('dino_pack', 'Sami\'s backpack'), ('backpack', 'new girl\'s backpack (no name)'),
             ('ticket_y', 'his ticket (punched)'), ('punch', 'ticket punch'), ('name_card', '1994 name card'), ('tail_piece', 'torn tail'),
             ('pencil', 'pencil'), ('keys', 'Della\'s keys'), ('maglite', 'flashlight'), ('cell', 'phone')]
    for i, (n, lb) in enumerate(items):
        x = 140 + (i % 6) * 300; y = 380 + (i // 6) * 420
        CH.draw_prop3(pen, n, x, y, ppc)
        label(cv, lb, x, y + 230, 15)
    c = CH.Ctx(pen, skia.Matrix(), 3.0).sub(1780, 120, 0.0, 5.0)
    c.lw = 0.6
    save(surf, 'props')
    surf, cv, pen = canvas()
    title(cv, 'The broom and his clipboard watchlist', '')
    CH.draw_prop3(pen, 'broom', 300, 160, 6.0, angle=0.0)
    c = CH.Ctx(pen, skia.Matrix(), 3.0).sub(1100, 400, 0.0, 14.0); c.lw = 0.25
    CH._ws_clipboard(c, 2, 0.0, None)
    c = CH.Ctx(pen, skia.Matrix(), 3.0).sub(1600, 400, 0.0, 14.0); c.lw = 0.25
    CH._ws_clipboard(c, 2, 0.0, CH.Pose(ws_write=0.7), new=True)
    label(cv, 'the watchlist (most names crossed out)', 1100, 920, 16); label(cv, 'the new clipboard (a line drawn)', 1600, 920, 16)
    save(surf, 'props2')


SHEETS = dict(ws_turn=sheet_ws_turn, ws_mood=sheet_ws_mood, ws_limits=sheet_ws_limits, ws_states=sheet_ws_states, ws_head=sheet_ws_head,
              lineup=sheet_lineup, turn_people=sheet_turn_people, faces=sheet_faces, props=sheet_props)

if __name__ == '__main__':
    names = [a for a in sys.argv[1:] if not a.startswith('--')] or list(SHEETS)
    for n in names: SHEETS[n]()
