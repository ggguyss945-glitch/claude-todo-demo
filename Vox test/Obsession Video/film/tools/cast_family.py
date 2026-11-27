"""cast_family.py: the Obsession film's family sheet, 640-px faces and acting strips (characters_obsession.py), to
W/cast/family_*.

    cd "Vox test/Obsession Video/film" && python3 tools/cast_family.py [sheet] [faces] [strips [group ...]]

sheet  -> _work/cast/family_sheet.png: everyone to scale side by side (Evie for scale, the tape kids, the silhouette),
          face busts with each one's key expressions, the states (chalk sleeves, red knuckles, bracelet, tired) and props.
faces  -> _work/cast/family_faces_640.jpg: four 640x360 frames (the size faces must read at).
strips -> _work/cast/family_strips_<group>.jpg: 8 frames (320x180 each) per scripted action, 3 actions per image, on flat
          stand-in sets, plus a printed contact report (reach misses, foot gaps).
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
PHONE = dict(under='#cfe0ff', under_a=150, key=-0.3)


def _surface(w, h):
    set_render_size(w, h)
    s = skia.Surface(CFG.rw, CFG.rh)
    return s, s.getCanvas()


def _grab(surf):
    return surf.makeImageSnapshot().toarray()[:, :, :3].copy()


def lbl(pen, s, x, y, c='#d8dce6', size=14):
    text(pen.cv, s, x, y, 600, size, c)


# ------------------------------------------------------------------------------------------------ the sheet
LINE_UP = [('adam', {}, 'adam'), ('adam', dict(ob_chalk=1.0), 'chalk sleeves'), ('adam_night', {}, 'adam_night'),
           ('danny', {}, 'danny'), ('evie', {}, 'evie (scale)'), ('lina', {}, 'lina'), ('mom', dict(ob_knuck=1.0), 'mom'),
           ('rahman', {}, 'rahman'), ('kofi', {}, 'kofi'), ('sam', {}, 'sam'), ('caretaker', {}, 'caretaker'),
           ('danny_mom', {}, 'danny_mom'), ('adam7', {}, 'adam7 (tape)'), ('danny7', {}, 'danny7 (tape)')]
BUSTS = [('adam', 'adam_guarded', {}), ('adam', 'adam_lonely', {}), ('adam', 'adam_scared', {}), ('adam', 'adam_ashamed', {}),
         ('adam', 'adam_steady', {}), ('mom', 'mom_warm', {}), ('mom', 'mom_watchful', {}), ('mom', 'mom_tired', dict(ob_tired=1.0)),
         ('mom', 'mom_firm', {}), ('lina', 'lina_earnest', {}), ('lina', 'lina_sing', {}), ('danny', 'danny_kind', {}),
         ('danny', 'danny_shy', {}), ('rahman', 'rahman_calm', {}), ('rahman', 'rahman_kind', {}), ('caretaker', 'squint_up', {}),
         ('adam7', 'kid_grin', {}), ('danny7', 'kid_grin', {})]


def sheet():
    W, H = 1920, 1440
    surf, cv = _surface(W, H)
    cv.clear(skia.Color(32, 34, 44)); cv.save(); cv.scale(CFG.k, CFG.k)
    pen = Pen(cv)
    pen.fill(rect(0, 0, W, 560), '#3a3f4e'); pen.fill(rect(0, 545, W, 15), '#2a2d38')
    ppm = 290.0; fl = 545.0
    for k, (who, kw, lab) in enumerate(LINE_UP):
        x = 70 + k * 134
        a = CH.Acting(who, seed=k + 1, height=CH.height_px(who, ppm), expr='neutral').place(x, fl)
        P = a.at(1.3); P.turn = 0.25 if k % 2 else -0.25
        for kk, v in kw.items(): setattr(P, kk, v)
        if who == 'danny_mom': CH.draw_silhouette(pen, who, x, fl, a.height, P, t=1.3, rim='#e8c88a')
        else: CH.draw(pen, who, x, fl, a.height, P, t=1.3, light=WARM)
        lbl(pen, lab, x, fl - 2 if False else 556, '#d8dce6', 12)
    for y_m in (1.0, 1.5):
        pen.line(poly([(10, fl - y_m * ppm), (1910, fl - y_m * ppm)], False), 1.0, '#6a7080')
        lbl(pen, '%.1f m' % y_m, 22, fl - y_m * ppm - 6, '#8a90a0', 11)
    # busts
    pen.fill(rect(0, 575, W, 560), '#2a2d38')
    for k, (who, ex, kw) in enumerate(BUSTS):
        col_, row = k % 9, k // 9
        a = CH.Acting(who, seed=k + 3, height=600, expr=ex)
        P = a.at(2.0); P.h_turn = 0.25 if k % 2 else -0.2
        for kk, v in kw.items(): setattr(P, kk, v)
        cx, cy = 106 + col_ * 213, 690 + row * 280
        cv.save(); cv.clipRect(skia.Rect(cx - 106, cy - 140, cx + 106, cy + 150))
        CH.draw_bust(pen, who, cx, cy, 0.22, P, t=2.0); cv.restore()
        lbl(pen, ex, cx, cy + 150, '#d8dce6', 12)
    # states and props
    pen.fill(rect(0, 1140, W, 300), '#3a3f4e')
    sc = 9.0
    for k, (nm, x, y) in enumerate((('phone_ob', 90, 1260), ('phone_ob_lit', 170, 1260), ('phone_mom', 250, 1260),
                                    ('scrub_brush', 350, 1250), ('hoodie_held', 520, 1170), ('crayon', 680, 1250),
                                    ('rule_card', 780, 1260), ('bracelet_real', 880, 1240), ('fork', 960, 1260),
                                    ('lina_drawing', 1120, 1290))):
        CH.draw_prop3(pen, nm, x, y, sc if nm not in ('hoodie_held', 'lina_drawing') else 4.5)
        lbl(pen, nm, x, 1420, '#d8dce6', 11)
    CH.draw_bucket(pen, 1320, 1400, 5.0, wet=1.0); lbl(pen, 'bucket', 1320, 1420, '#d8dce6', 11)
    CH.draw_shoebox(pen, 1500, 1370, 5.0, open_=0.0); CH.draw_shoebox(pen, 1700, 1370, 5.0, open_=1.0)
    lbl(pen, 'shoebox', 1600, 1420, '#d8dce6', 11)
    # Danny at 7's wrist close (the bracelet) and Mom's knuckles
    a = CH.Acting('danny7', seed=2, height=600, expr='kid_grin'); P = a.at(1.0); P.hl_out = 30; P.hl_fwd = 120; P.hl_down = 60
    CH.draw_bust(pen, 'danny7', 1850, 1250, 0.25, P, t=1.0)
    cv.restore()
    os.makedirs(OUT, exist_ok=True)
    img = _grab(surf)
    cv2.imwrite(os.path.join(OUT, 'family_sheet.png'), img)
    return img


def faces640():
    shots = [[('adam', 320, 205, 0.42, dict(h_turn=0.25), 'adam_lonely', None, '#4a5060')],
             [('mom', 320, 205, 0.42, dict(h_turn=-0.2), 'mom_watchful', WARM, '#5a4e46')],
             [('rahman', 320, 205, 0.42, dict(h_turn=0.2), 'rahman_kind', WARM, '#5e6a62')],
             [('danny', 180, 215, 0.36, dict(h_turn=0.25), 'danny_shy', None, '#46505e'),
              ('lina', 470, 225, 0.33, dict(h_turn=-0.2), 'lina_earnest', None, None)]]
    tiles = []
    for shot in shots:
        surf, cv = _surface(640, 360)
        cv.save(); cv.scale(CFG.k, CFG.k); pen = Pen(cv)
        for who, x, y, sc, kw, ex, lt, bg in shot:
            if bg: pen.fill(rect(0, 0, 1920, 1080), bg)
            a = CH.Acting(who, seed=5, height=600, expr=ex)
            P = a.at(2.0)
            for k, v in kw.items(): setattr(P, k, v)
            CH.draw_bust(pen, who, x * 3, y * 3, sc * 3, P, t=2.0, light=lt)
        cv.restore()
        tiles.append(_grab(surf))
    img = np.vstack([np.hstack(tiles[:2]), np.hstack(tiles[2:])])
    cv2.imwrite(os.path.join(OUT, 'family_faces_640.jpg'), img, [cv2.IMWRITE_JPEG_QUALITY, 90])


def selftest():
    """Every family id in 5 views at 3 detail levels, every clip once; prints the time per full body."""
    import time
    surf, cv = _surface(960, 540); cv.save(); cv.scale(CFG.k, CFG.k); pen = Pen(cv)
    n, t0 = 0, time.time()
    for who in CH.OBSESSION_CAST:
        for turn in (0.0, 0.5, -0.5, 1.0, 2.0):
            for det in (0, 1, 2):
                a = CH.Acting(who, seed=1, height=600, expr='neutral'); P = a.at(1.0); P.turn = turn
                P.ob_chalk = P.ob_tips = P.ob_knuck = P.ob_tired = 1.0
                CH.draw(pen, who, 960, 1000, 600, P, detail=det, t=1.0); n += 1
        CH.draw_bust(pen, who, 960, 500, 0.8, CH.Acting(who, seed=1, height=600).at(1.0), t=1.0)
    print('selftest: %d full bodies, %.1f ms each' % (n, (time.time() - t0) * 1000.0 / n))
    cv.restore()


if __name__ == '__main__':
    args = sys.argv[1:] or ['sheet', 'faces']
    os.makedirs(OUT, exist_ok=True)
    if 'sheet' in args: sheet(); print('sheet ->', os.path.join(OUT, 'family_sheet.png'))
    if 'selftest' in args: selftest()
    if 'faces' in args: faces640(); print('faces ->', os.path.join(OUT, 'family_faces_640.jpg'))
    if 'strips' in args:
        import cast_family_strips as S
        for g in [a for a in args if a in S.GROUPS] or list(S.GROUPS): S.render_group(g)
