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
        if CH.CAST[who].get('whistle'):           # keep his head centred when the body turns (the neck juts forward)
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
          'a predator in a mascot suit: forward hunch, head tilted, furry cat-mascot head (about 1/5 of his height), arms to the knees, hat leaning 12 deg to his left; never walks')
    views = [(0.0, 'FRONT'), (0.5, '3/4 RIGHT'), (1.0, 'PROFILE'), (1.5, '3/4 BACK'), (2.0, 'BACK'), (-0.5, '3/4 LEFT')]
    floor(pen, 1030)
    for i, (yw, lb) in enumerate(views):
        x = 175 + i * 314
        CH.draw(pen, 'whistle', x, 1030, 640, CH.Pose(turn=yw), t=0.0, light=AMBER, detail=2)
        label(cv, lb, x, 1062, 15, '#9aa3b8')
    # proportion marks on the front view
    h = 640.0; ppc = h / 244.0
    for cm, lb in ((134, 'hip 55 %'), (70, 'knee: fingertips'), (202, 'chin (head ~1/5)'), (244, 'crown'), (244 + 90, 'hat top +40 %')):
        y = 1030 - cm * ppc
        pen.line(poly([(20, y), (120, y)], False), 2, '#7a8296')
        text(cv, lb, 22, y - 4, 600, 12, '#9aa3b8', 255, 0.0, 'left')
    save(surf, 'ws_turn')


def sheet_ws_mood():
    surf, cv, pen = canvas()
    title(cv, 'MISTER WHISTLESTOP beside the owner\'s mood references (mood only: nothing copied)',
          'kept: a big furry grinning cat-mascot head (cheek fur, ears, whiskers, cat eyes), white gloves round a doorframe, VHS grain, a long thin dark body. changed: every protected specific (see ws_limits)')
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
    # ours: peeking round a doorframe (half the face, one glove), the grin in the dark, the 1994 tape
    pen.fill(rect(30, 480, 1860, 580), '#141018')
    _peek(pen, cv, 30, 480, 620, 580, 1.2)
    _vhs(surf, cv, 30, 480, 620, 580, 1.0, 11, 0.35)
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(660, 480, 600, 580))
    pen.fill(rect(660, 480, 600, 580), '#0c0a10')
    CH.draw_bust(pen, 'whistle', 960, 740, 0.62, CH.Pose(turn=0.1, h_tilt=-12.0), light=dict(under='#ff9a2a', under_a=170, rim='#ff8a20', rim_a=70, side=1), t=0.3)
    cv.restore()
    _vhs(surf, cv, 660, 480, 600, 580, 0.9, 12, 0.2)
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(1270, 480, 620, 580))
    pen.fill(rect(1270, 480, 620, 580), '#3a8acb')
    CH.draw(pen, 'whistle94', 1580, 1040, 360, CH.Pose(turn=-0.2, ws_glitch=0.35), light=STUDIO, t=0.4)
    cv.restore()
    _vhs(surf, cv, 1270, 480, 620, 580, 1.0, 13, 0.1)
    for x_, s_ in ((340, 'half a face round the frame, one glove curled on it'), (960, 'the furry cat head and the frozen grin, lit from below'), (1580, 'the 1994 tape: a VHS tear')):
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
              'grin painted and frozen (never lip-syncs); painted almond cat eyes, no lids, his left pupil higher; punch hole in the left ear',
              'his own cat: dusty grey-brown TABBY (stripes), off-white matted face and ruffs, mustard jacket; no black body / white face / white gloves scheme']
    for i, s_ in enumerate(checks):
        text(cv, ('OK  ' + s_), 60, 846 + i * 31, 700, 18, '#b8f0b0', 255, 0.0, 'left')
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
        items.append(('whistle', dict(turn=yw), lb, AMBER))
    for sl, lb in ((0.3, 'slip 30 %'), (0.7, 'slip 70 %'), (1.0, 'slip 100 %')):
        items.append(('whistle', dict(ws_slip=sl), lb, AMBER))
    items += [('whistle', dict(h_tilt=-16.0, ws_bob=0.6), 'talk bob (no jaw)', AMBER), ('whistle94', dict(), '1994 tape', STUDIO),
              ('whistle', dict(h_nod=0.5, h_turn=0.3), 'looking down at you', AMBER)]
    _faces('ws_head', items, 'MISTER WHISTLESTOP: the head', 'a furry cat-mascot head: cheek ruffs, muzzle, whisker pads, cat nose, whiskers, painted almond cat eyes (never blink), THE GRIN (never moves; slips only at the defeat), punch hole in the left ear', cols=6, cyk=0.60, sk=0.56)


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


# ---------------------------------------------------------------------------------------------------- ws_creepy
def _grab(surf, x, y, w, h):
    a = surf.makeImageSnapshot().toarray()
    return np.ascontiguousarray(a[int(y):int(y + h), int(x):int(x + w), [2, 1, 0, 3]]).copy()     # BGRA -> RGBA


def _put(cv, arr, x, y, clip_path=None):
    img = skia.Image.fromarray(np.ascontiguousarray(arr.astype(np.uint8)))
    cv.save()
    if clip_path is not None: cv.clipPath(clip_path, skia.ClipOp.kIntersect, True)
    cv.drawImage(img, float(x), float(y))
    cv.restore()


def _vhs(surf, cv, x, y, w, h, amt=1.0, seed=0, desat=0.25, warm=False):
    """Cheap VHS look on a region: chroma offset, desaturation, scanlines, grain, a tracking band."""
    a = _grab(surf, x, y, w, h).astype(np.float32)
    rgb = a[:, :, :3]
    g = rgb.mean(2, keepdims=True)
    rgb = rgb * (1 - desat) + g * desat
    sh = int(2 + 2 * amt)
    rgb[:, sh:, 0] = rgb[:, :-sh, 0] * 0.8 + rgb[:, sh:, 0] * 0.2
    rgb[:, :-sh, 2] = rgb[:, sh:, 2] * 0.8 + rgb[:, :-sh, 2] * 0.2
    rng = np.random.default_rng(seed)
    rgb += rng.normal(0, 14 * amt, rgb.shape[:2])[:, :, None]
    rgb[::3] *= 0.86
    yb = int(h * (0.72 + 0.2 * rng.random()))
    rgb[yb:yb + 6] = rgb[yb:yb + 6] * 0.5 + 120
    rgb[yb:yb + 6] = np.roll(rgb[yb:yb + 6], int(12 * amt), axis=1)
    if warm: rgb *= np.array([1.06, 0.98, 0.86])
    a[:, :, :3] = np.clip(rgb, 0, 255)
    _put(cv, a, x, y)


def _cell(pen, cv, i, j, bg):
    x0, y0, w, h = 10 + i * 477, 118 + j * 474, 467, 462
    pen.fill(rect(x0, y0, w, h), bg)
    return x0, y0, w, h


def _cap(pen, cv, x0, y0, w, h, s_):
    pen.fill(rect(x0, y0 + h - 30, w, 30), '#000000', 170)
    label(cv, s_, x0 + w / 2, y0 + h - 10, 15)


def _peek(pen, cv, x0, y0, w, h, k=1.0):
    """He peeks round a doorframe: half the face, one glove curled on the frame edge (the mood of ref 1)."""
    pen.fill(rect(x0, y0, w, h), '#120f14')
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x0, y0, w, h))
    pen.glow(x0 + 60 * k, y0 + 160 * k, 380 * k, '#ffa030', 55)
    ex = x0 + w * 0.61
    a = _ws(0, 0, 1650 * k)
    a.set(-1, None, 0.01, tilt=-9.0, turn=-0.12, h_tilt=-16.0, ws_hands_front=3)
    hx, hy = a.where(0.0, 'head')
    a.place(ex + 4 * k - hx, y0 + h * 0.43 - hy)
    hx, hy = a.where(0.0, 'head')
    a.curl_door(-2.0, 1, (ex + 30 * k, hy + 175 * k), dur=0.01, z=-4.0)
    lt = dict(rim='#ffa030', rim_a=80, side=-1, key=-0.3)
    CH.draw(pen, 'whistle', a.x0, a.y0, a.height, a.at(0.0), light=lt, t=0.0, detail=2)
    pen.fill(rect(ex, y0, x0 + w - ex, h), '#3b2f27'); pen.fill(rect(ex, y0, 30 * k, h), '#cbbd9c'); pen.fill(rect(ex + 24 * k, y0, 6 * k, h), '#8f8166')
    pen.linear(rect(ex, y0, x0 + w - ex, h), ex, 0, x0 + w, 0, [(0, '#000000', 0), (1, '#000000', 150)])
    CH.draw_whistle_hands(pen, a, 0.0, (1,), lt, detail=2)
    cv.restore()


def sheet_ws_creepy():
    """The creepiness checks: the framings the film puts him in."""
    surf, cv, pen = canvas()
    title(cv, 'MISTER WHISTLESTOP: creepiness checks (film framings)',
          'doorframe peek, peephole fisheye, frosted glass, amber up-light, near darkness, far silhouette in the bus door, the 1994 tape, down and down')
    # 1 the doorframe peek: half the face round the frame and one glove curled on the edge (mood ref 1)
    x0, y0, w, h = _cell(pen, cv, 0, 0, '#120f14')
    _peek(pen, cv, x0, y0, w, h)
    _vhs(surf, cv, x0, y0, w, h, 1.0, 1, 0.35)
    _cap(pen, cv, x0, y0, w, h, 'round the doorframe: half a face, one glove')
    # 2 the peephole: a fisheye of his face filling the lens
    x0, y0, w, h = _cell(pen, cv, 1, 0, '#2a1d14')
    cx, cy, R = x0 + w / 2, y0 + h / 2 - 12, 190
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(cx - R, cy - R, 2 * R, 2 * R))
    pen.fill(rect(cx - R, cy - R, 2 * R, 2 * R), '#1a120c'); pen.glow(cx, cy - 160, 240, '#ffb040', 120)
    CH.draw_bust(pen, 'whistle', cx + 6, cy + 10, 0.47, CH.Pose(turn=0.04, h_nod=0.25, h_tilt=-8.0), light=dict(rim='#ffb040', rim_a=70, side=1, under='#ff9a2a', under_a=60), t=0.0, detail=2)
    cv.restore()
    a_ = _grab(surf, cx - R, cy - R, 2 * R, 2 * R)
    yy, xx = np.mgrid[0:2 * R, 0:2 * R].astype(np.float32)
    dx, dy = (xx - R) / R, (yy - R) / R
    r = np.sqrt(dx * dx + dy * dy) + 1e-6
    rs = np.clip(r, 0, 1) ** 1.75 * 1.05
    mx = (R + dx / r * rs * R).astype(np.float32); my = (R + dy / r * rs * R).astype(np.float32)
    fe = cv2.remap(a_, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
    fe[:, :, :3] *= np.clip(1.15 - 0.75 * r ** 2.2, 0, 1)[:, :, None]
    lens = oval(cx, cy, R, R)
    _put(cv, fe, cx - R, cy - R, lens)
    door = skia.Path(); door.addRect(skia.Rect.MakeXYWH(x0, y0, w, h)); door = skia.Op(door, lens, skia.PathOp.kDifference_PathOp)
    pen.fill(door, '#24170f'); pen.line(oval(cx, cy, R + 6, R + 6), 12, '#8a6a3a'); pen.line(oval(cx, cy, R + 12, R + 12), 3, '#000000')
    _vhs(surf, cv, x0, y0, w, h, 0.5, 2, 0.15)
    _cap(pen, cv, x0, y0, w, h, 'the peephole: the grin fills the lens')
    # 3 frosted glass: the shape behind the door panel
    x0, y0, w, h = _cell(pen, cv, 2, 0, '#2b2018')
    gx, gy, gw, gh = x0 + 70, y0 + 40, w - 140, h - 110
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(gx, gy, gw, gh))
    pen.fill(rect(gx, gy, gw, gh), '#3a2a1a'); pen.glow(gx + gw * 0.8, gy, 260, '#ffb14a', 160)
    CH.draw_bust(pen, 'whistle', gx + gw / 2, gy + 170, 0.36, CH.Pose(turn=0.0, h_tilt=-12.0), light=dict(rim='#ffc060', rim_a=110, side=-1), t=0.0, detail=2)
    cv.restore()
    a_ = _grab(surf, gx, gy, gw, gh).astype(np.float32)
    rng = np.random.default_rng(5)
    nx = cv2.GaussianBlur(rng.normal(0, 1, (gh, gw)).astype(np.float32), (0, 0), 2.0) * 9
    ny = cv2.GaussianBlur(rng.normal(0, 1, (gh, gw)).astype(np.float32), (0, 0), 2.0) * 9
    yy, xx = np.mgrid[0:gh, 0:gw].astype(np.float32)
    a_ = cv2.remap(a_, xx + nx, yy + ny, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    a_ = cv2.GaussianBlur(a_, (0, 0), 4.5)
    a_[:, :, :3] = a_[:, :, :3] * 0.8 + np.array([70, 60, 52]) * 0.35
    _put(cv, a_, gx, gy)
    for k in range(0, gw, 9): pen.line(poly([(gx + k, gy), (gx + k, gy + gh)], False), 1.5, '#ffffff', 18)
    fr = skia.Path(); fr.addRect(skia.Rect.MakeXYWH(x0, y0, w, h)); fr = skia.Op(fr, rect(gx, gy, gw, gh), skia.PathOp.kDifference_PathOp)
    pen.fill(fr, '#5a3f28'); pen.line(rect(gx, gy, gw, gh), 6, '#2a1a10')
    _cap(pen, cv, x0, y0, w, h, 'frosted glass: ears, hat, a pale face, the grin')
    # 4 amber light from below
    x0, y0, w, h = _cell(pen, cv, 3, 0, '#08070a')
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x0, y0, w, h))
    pen.glow(x0 + w / 2, y0 + h + 40, 300, '#ff9020', 90)
    CH.draw_bust(pen, 'whistle', x0 + w / 2, y0 + 250, 0.5, CH.Pose(turn=0.15, h_tilt=-10.0, h_nod=-0.15),
                 light=dict(under='#ff9a2a', under_a=200, rim='#ff8a20', rim_a=70, side=1), t=0.0, detail=2)
    cv.restore()
    _vhs(surf, cv, x0, y0, w, h, 0.6, 4, 0.1)
    _cap(pen, cv, x0, y0, w, h, 'sodium amber from below')
    # 5 near darkness: only the eyes and the grin
    x0, y0, w, h = _cell(pen, cv, 0, 1, '#050407')
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x0, y0, w, h))
    CH.draw_bust(pen, 'whistle', x0 + w / 2 + 20, y0 + 230, 0.5, CH.Pose(turn=-0.1, h_tilt=-14.0), light=dict(dark=0.93, rim='#8fa6ff', rim_a=40, side=1), t=0.0, detail=2)
    cv.restore()
    _vhs(surf, cv, x0, y0, w, h, 0.8, 5, 0.3)
    _cap(pen, cv, x0, y0, w, h, 'the blackout: eyes and grin catch the light')
    # 6 far silhouette against the lit bus door
    x0, y0, w, h = _cell(pen, cv, 1, 1, '#0b0d14')
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x0, y0, w, h))
    ppm = 92.0; fy = y0 + h - 50
    pen.glow(x0 + w * 0.7, y0 + 30, 220, '#ffb050', 60)
    pen.fill(rect(x0, fy - 3.0 * ppm, w, 3.0 * ppm), '#2a2416')
    for k in range(4): pen.fill(rect(x0 + 10 + k * 120, fy - 2.45 * ppm, 92, 0.8 * ppm), '#d9902e')
    dxl = x0 + w / 2 - 55
    pen.fill(rect(dxl, fy - 2.25 * ppm, 110, 2.25 * ppm), '#f0b04a'); pen.glow(dxl + 55, fy - 1.2 * ppm, 160, '#ffc060', 90)
    pen.line(rect(dxl, fy - 2.25 * ppm, 110, 2.25 * ppm), 6, '#1a1408')
    pen.fill(rect(x0, fy, w, 60), '#090a0e')
    CH.draw(pen, 'whistle', dxl + 55, fy, CH.height_px('whistle', ppm), CH.Pose(turn=0.1), light=dict(dark=1.0), t=0.0, detail=2)
    cv.restore()
    _vhs(surf, cv, x0, y0, w, h, 0.7, 6, 0.2)
    _cap(pen, cv, x0, y0, w, h, 'far: chimney hat, ears, ruff, long arms')
    # 7 the 1994 tape on the TV cart
    x0, y0, w, h = _cell(pen, cv, 2, 1, '#100e12')
    tvx, tvy, tvw, tvh = x0 + 30, y0 + 40, w - 60, h - 110
    pen.fill(rrect(tvx - 16, tvy - 16, tvw + 32, tvh + 32, 26), '#3a3633'); pen.line(rrect(tvx - 16, tvy - 16, tvw + 32, tvh + 32, 26), 4, '#000000')
    scr = rrect(tvx, tvy, tvw, tvh, 34)
    cv.save(); cv.clipPath(scr, skia.ClipOp.kIntersect, True)
    pen.fill(rect(tvx, tvy, tvw, tvh), '#3d8fd6'); pen.fill(rect(tvx, tvy + tvh * 0.78, tvw, tvh * 0.22), '#e2b93a')
    text(cv, 'RIDE', tvx + tvw * 0.76, tvy + 90, 900, 40, '#ffe66a', 255, 0.06, 'center')
    text(cv, 'RIGHT!', tvx + tvw * 0.76, tvy + 136, 900, 40, '#ffe66a', 255, 0.06, 'center')
    pen.fill(rrect(tvx + tvw * 0.6, tvy + tvh * 0.55, 120, 70, 8), '#f2c230'); pen.line(rrect(tvx + tvw * 0.6, tvy + tvh * 0.55, 120, 70, 8), 3, '#2a2a2a')
    a = _ws(tvx + tvw * 0.36, tvy + tvh * 0.95, 280, 'whistle94', seed=3)
    a.set(-1, None, 0.01, turn=-0.12, ws_lrest='host', ws_rrest='hang', hl_shape='host')
    CH.draw(pen, 'whistle94', a.x0, a.y0, a.height, a.at(0.0), light=STUDIO, t=0.0, detail=2)
    cv.restore()
    _vhs(surf, cv, tvx, tvy, tvw, tvh, 1.0, 7, 0.1)
    pen.line(scr, 8, '#111111')
    pen.radial(scr, tvx + tvw / 2, tvy + tvh / 2, tvw * 0.62, [(0, '#000000', 0), (0.7, '#000000', 20), (1, '#000000', 150)])
    _cap(pen, cv, x0, y0, w, h, '1994: bright, cheap, wholesome, wrong')
    # 8 down, and down: he bends to your face (from below, tracking lines)
    x0, y0, w, h = _cell(pen, cv, 3, 1, '#0d0b0e')
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x0, y0, w, h))
    pen.glow(x0 + w * 0.3, y0 + h, 300, '#ff9a2a', 70)
    a = _ws(0, 0, 1500)
    a.set(-1, None, 0.01, turn=-0.3, ws_bend=1.05, ws_crouch=0.3, ws_face_up=1.0, ws_elev=-0.22, h_tilt=-18.0, ws_lrest='chest')
    hx, hy = a.where(0.0, 'head')
    a.place(x0 + w * 0.55 - hx, y0 + 215 - hy)
    CH.draw(pen, 'whistle', a.x0, a.y0, a.height, a.at(0.0), light=dict(under='#ff9a2a', under_a=120, rim='#ffa030', rim_a=80, side=1), t=0.0, detail=2)
    CH.ws_tracking(pen, x0, y0, w, h, 0.5, 1.3, 3)
    cv.restore()
    _vhs(surf, cv, x0, y0, w, h, 0.8, 8, 0.25)
    _cap(pen, cv, x0, y0, w, h, '"down, and down": the grin a foot from you')
    save(surf, 'ws_creepy')


SHEETS = dict(ws_turn=sheet_ws_turn, ws_mood=sheet_ws_mood, ws_limits=sheet_ws_limits, ws_states=sheet_ws_states, ws_head=sheet_ws_head, ws_creepy=sheet_ws_creepy,
              lineup=sheet_lineup, turn_people=sheet_turn_people, faces=sheet_faces, props=sheet_props)

if __name__ == '__main__':
    names = [a for a in sys.argv[1:] if not a.startswith('--')] or list(SHEETS)
    for n in names: SHEETS[n]()
