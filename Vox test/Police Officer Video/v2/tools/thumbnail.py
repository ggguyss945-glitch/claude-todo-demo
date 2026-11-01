"""YouTube thumbnail in the channel's reference layout (crisp flat vector, like the firefighter/hotel/class thumbnails):
flat red panel with a centred two-line command (white with a soft glow over black), a thick curved arrow, and a framed
doorbell-camera close-up of a grinning officer with red glowing eyes, two more behind him, HUD and a face box.
    python3 thumbnail.py <out dir> [LINE1 LINE2 TAG]  -> thumbnail_4k.png (3840x2160), thumbnail_1280.jpg (upload)
Drawn in a 1280x720 design space and rendered at 3x.
"""
import os, sys, math
import numpy as np, cv2, skia
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import characters as C
from engine.core import set_render_size, Pen

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'fonts')
BLACK, XBOLD = os.path.join(FONTS, 'MontserratLC-900.ttf'), os.path.join(FONTS, 'MontserratLC-800.ttf')
S = 3
INK = '#0d0d10'
_tf = {}


def col(h, a=255):
    h = h.lstrip('#'); return skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(a))


def paint(c, a=255, stroke=0.0, blur=0.0):
    p = skia.Paint(Color=col(c, a), AntiAlias=True)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
        p.setStrokeJoin(skia.Paint.kRound_Join); p.setStrokeCap(skia.Paint.kRound_Cap)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def P(pts, close=True):
    """Path from points: (x, y) line, (cx, cy, x, y) quad, (c1x, c1y, c2x, c2y, x, y) cubic."""
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:]:
        {2: p.lineTo, 4: p.quadTo, 6: p.cubicTo}[len(q)](*q)
    if close: p.close()
    return p


def ov(cx, cy, rx, ry=None):
    p = skia.Path(); ry = rx if ry is None else ry
    p.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry)); return p


def minus(a, b): return skia.Op(a, b, skia.PathOp.kDifference_PathOp)


def rr(x, y, w, h, r):
    p = skia.Path(); p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)); return p


def shp(cv, p, fill, lw=5.0):
    cv.drawPath(p, paint(fill)); cv.drawPath(p, paint(INK, stroke=lw))


def glow(cv, cx, cy, r, c, a):
    cv.drawCircle(cx, cy, r, skia.Paint(Shader=skia.GradientShader.MakeRadial((cx, cy), r, [col(c, a), col(c, 0)])))


def clipped(cv, clip, fn):
    cv.save(); cv.clipPath(clip, doAntiAlias=True); fn(); cv.restore()


def font(path_, size):
    if path_ not in _tf: _tf[path_] = skia.Typeface.MakeFromFile(path_)
    return skia.Font(_tf[path_], size)


def text(cv, s, x, y, size, c, fp=BLACK, align='center', blur=0.0, a=255):
    f = font(fp, size); w = f.measureText(s)
    x0 = x - w / 2 if align == 'center' else (x - w if align == 'right' else x)
    cv.drawString(s, x0, y, f, paint(c, a, blur=blur))
    return w


def fit(s, fp, size, maxw):
    w = font(fp, size).measureText(s)
    return size if w <= maxw else size * maxw / w


def star(cx, cy, r1, r2, n=6):
    pts = []
    for k in range(2 * n):
        r = r1 if k % 2 == 0 else r2; a = -math.pi / 2 + k * math.pi / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return P(pts)


# ---------------------------------------------------------------------------------------------------- the officer
def officer(cv, cx, cy, sc, dim=0.0):
    """Head-and-shoulders, head centre at (cx, cy); sc = 1 -> head 300 wide."""
    cv.save(); cv.translate(cx, cy); cv.scale(sc, sc)
    lw = 6.0
    skin, shade, navy, navy2 = '#f1e9df', '#d8cabd', '#1c2b57', '#14204a'
    # shoulders / uniform
    torso = P([(-330, 470), (-322, 300, -230, 232), (-120, 196), (120, 196), (230, 232, 322, 300), (330, 470)])
    shp(cv, torso, navy, lw)
    clipped(cv, torso, lambda: cv.drawPath(P([(-330, 470), (-300, 300, -200, 240), (-120, 210), (-170, 470)]), paint(navy2)))
    shp(cv, P([(-62, 178), (62, 178), (70, 236), (0, 300), (-70, 236)]), skin, lw)           # neck
    shp(cv, P([(-70, 214), (0, 300), (-36, 330), (-118, 232)]), '#e8ecf4', lw)                # collar
    shp(cv, P([(70, 214), (0, 300), (36, 330), (118, 232)]), '#e8ecf4', lw)
    shp(cv, P([(-18, 300), (18, 300), (30, 470), (-30, 470)]), '#121320', lw)                 # tie
    shp(cv, star(-176, 330, 40, 18), '#f2c14e', 4.5)                                          # badge
    cv.drawPath(ov(-176, 330, 12), paint('#c9952a'))
    shp(cv, rr(206, 236, 52, 82, 12), '#17181e', lw)                                          # shoulder radio
    cv.drawPath(ov(232, 258, 8), paint('#ff2b2b')); glow(cv, 232, 258, 26, '#ff2b2b', 170)
    # head: smooth, pale, cool grey-white (the reference girl's skin), soft shading only at the edges
    skin_l, skin_e = '#f3f2f1', '#cfcbcd'
    for s in (-1, 1):
        shp(cv, ov(s * 150, 26, 22, 36), '#e2dfdf', lw)
        cv.drawPath(ov(s * 150, 28, 9, 19), paint('#c4bfc1'))
    head = P([(-148, -50), (-154, 80, -122, 160), (-84, 214, 0, 218), (84, 214, 122, 160), (154, 80, 148, -50),
              (142, -160, 0, -168), (-142, -160, -148, -50)])
    cv.drawPath(head, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((0, 10), 210, [col(skin_l), col(skin_l), col(skin_e)], [0, 0.55, 1])))
    clipped(cv, head, lambda: (cv.drawPath(ov(0, 250, 170, 60), paint('#b9b4b8', 120, blur=20)),
                               cv.drawPath(P([(-150, -140), (-150, -60, -100, -56), (-40, -64), (-20, -150)]), paint('#2a2321')),
                               cv.drawPath(P([(150, -140), (150, -60, 100, -56), (40, -64), (20, -150)]), paint('#2a2321'))))
    cv.drawPath(head, paint(INK, stroke=lw))
    # sunken, shadowed sockets with a red glow on the skin around the eyes
    for s in (-1, 1):
        ex, ey = s * 60, 0
        cv.drawPath(ov(ex, ey + 6, 58, 50), paint('#4a2a3c', 110, blur=12))
        cv.drawCircle(ex, ey, 66, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
            (ex, ey), 66, [col('#ff2c3c', 200), col('#ff3a4a', 120), col('#ff3a4a', 0)], [0, 0.6, 1])))
        cv.drawPath(P([(ex - 40, ey + 30), (ex, ey + 50, ex + 40, ey + 30)], False), paint('#3e1e2e', 170, stroke=5, blur=1.5))
    # eyes: staring too wide, white all round the iris, pinpoint pupils, a glowing red ring
    for s in (-1, 1):
        ex, ey = s * 60, 0
        eye = P([(ex - 38, ey + 4), (ex - 34, ey - 32, ex, ey - 33), (ex + 34, ey - 32, ex + 38, ey + 4),
                 (ex + 30, ey + 33, ex, ey + 33), (ex - 30, ey + 33, ex - 38, ey + 4)])
        cv.drawPath(eye, paint('#ff4a5c', 220, stroke=13, blur=2.5))
        cv.drawPath(eye, paint('#ffffff'))
        def inside(ex=ex, ey=ey, eye=eye):
            cv.drawPath(eye, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
                (ex, ey), 40, [col('#ffffff', 0), col('#ffffff', 0), col('#ff9aa6', 220)], [0, 0.5, 1])))
            for k in range(5):                                                   # veins
                a_ = k * 1.25 + (0.3 if s > 0 else 1.0)
                cv.drawPath(P([(ex + 40 * math.cos(a_), ey + 34 * math.sin(a_)), (ex + 24 * math.cos(a_ + 0.25), ey + 20 * math.sin(a_ + 0.25))], False),
                            paint('#d8344a', 150, stroke=1.8))
            cv.drawPath(ov(ex, ey + 1, 18), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
                (ex, ey + 1), 19, [col('#ff4a5a'), col('#d4102a'), col('#86061a')], [0, 0.65, 1])))
            cv.drawPath(ov(ex, ey + 1, 18), paint('#3a0208', stroke=2.5))
            cv.drawPath(ov(ex, ey + 1, 4.5), paint('#0a0002'))
            cv.drawPath(ov(ex - 5, ey - 5, 2.4), paint('#ffffff', 230))
        clipped(cv, eye, inside)
        cv.drawPath(eye, paint('#2a0a12', stroke=4))
        cv.drawPath(P([(ex - 40, ey + 2), (ex - 34, ey - 36, ex, ey - 36), (ex + 34, ey - 36, ex + 40, ey + 2)], False), paint(INK, stroke=6.5))
    # brows: thin, high, the inner ends pulled down a touch
    for s in (-1, 1):
        cv.drawPath(P([(s * 24, -58), (s * 60, -80, s * 102, -66)], False), paint('#231c1b', stroke=7))
    # nose: a short bridge, the tip and nostrils, close above the mouth
    cv.drawPath(P([(-4, 18), (-8, 40, -14, 52)], False), paint('#b5aaaf', stroke=3))
    cv.drawPath(P([(-16, 56), (0, 66, 16, 56)], False), paint('#6e6268', stroke=3.5))
    cv.drawPath(ov(-10, 58, 4.5, 3.5), paint('#2a2224')); cv.drawPath(ov(10, 58, 4.5, 3.5), paint('#2a2224'))
    for s in (-1, 1):                                                          # folds from the nose to the mouth corners
        cv.drawPath(P([(s * 26, 52), (s * 70, 58, s * 112, 72)], False), paint('#a89aa2', stroke=3.5))
    # the smile: starts right under the nose, far too wide, two even rows of teeth, thin pink lips
    mouth = P([(-138, 72), (-70, 92, 0, 92), (70, 92, 138, 72), (118, 152, 0, 162), (-118, 152, -138, 72)])
    cv.drawPath(mouth, paint('#d96474', stroke=10))
    cv.drawPath(mouth, paint('#3e0610'))
    def teeth():
        up = P([(-146, 64), (0, 104, 146, 64), (142, 116), (0, 132, -142, 116)])
        lo = P([(-128, 124), (0, 138, 128, 124), (116, 152), (0, 172, -116, 152)])
        for t in (up, lo):
            cv.drawPath(t, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 80), (0, 170)], [col('#ffffff'), col('#e9e4e8')])))
        for k in range(-7, 8):
            x = k * 18
            cv.drawPath(P([(x, 80), (x * 0.985, 124)], False), paint('#b3acb3', stroke=2.2))
            if abs(k) <= 6: cv.drawPath(P([(x * 0.9, 126), (x * 0.9, 170)], False), paint('#b3acb3', stroke=2.2))
        cv.drawPath(P([(-142, 121), (0, 136, 142, 121)], False), paint('#3e0610', stroke=5))
    clipped(cv, mouth, teeth)
    cv.drawPath(mouth, paint('#4e0a16', stroke=4.5))
    for s in (-1, 1):                                                          # corners dug into the cheeks
        cv.drawPath(P([(s * 136, 58), (s * 154, 74, s * 146, 98)], False), paint('#9a8c95', stroke=3.5))
    cv.drawPath(P([(-26, 196), (0, 202, 26, 196)], False), paint('#b8b0b4', stroke=3.5))
    # police cap
    crown = P([(-168, -104), (-188, -226, -70, -250), (70, -266, 188, -232), (170, -104)])
    cv.drawPath(crown, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -260), (0, -104)], [col('#2c4182'), col(navy)])))
    cv.drawPath(crown, paint(INK, stroke=lw))
    shp(cv, rr(-172, -128, 344, 34, 9), '#0f1426', lw)
    cv.drawPath(P([(-160, -111), (160, -111)], False), paint('#e7bf55', stroke=5))
    shp(cv, P([(-170, -96), (0, -38, 170, -96), (158, -70), (0, -14, -158, -70)]), '#0a0c14', lw)
    cv.drawPath(P([(-120, -80), (0, -40, 120, -80)], False), paint('#ffffff', 60, stroke=4))
    shp(cv, star(0, -192, 40, 17), '#f2c14e', 4.5)
    shp(cv, ov(0, -192, 13), '#c9952a', 3)
    if dim:
        cv.drawRect(skia.Rect.MakeLTRB(-400, -300, 400, 500), paint('#060a1c', int(255 * dim)))
        for s in (-1, 1):                                                       # the eyes still burn in the dark
            cv.drawCircle(s * 62, 4, 62, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
                (s * 62, 4), 62, [col('#ff2c3c', 170), col('#ff2c3c', 0)])))
            cv.drawPath(ov(s * 62, 6, 24), paint('#ff2234')); cv.drawPath(ov(s * 62, 6, 8.5), paint('#120104'))
            cv.drawPath(ov(s * 62 - 8, -3, 5, 4), paint('#ffffff', 220))
    cv.restore()


def scene(cv, x, y, w, h):
    """The doorbell picture inside the frame."""
    cv.drawRect(skia.Rect.MakeXYWH(x, y, w, h), skia.Paint(Shader=skia.GradientShader.MakeLinear(
        [(0, y), (0, y + h)], [col('#0a1230'), col('#1a2350'), col('#141a36')], [0, 0.55, 1])))
    rng = np.random.default_rng(7)
    for k in range(26):                                                                      # stars
        sx, sy = x + rng.uniform(10, w - 10), y + rng.uniform(70, 170)
        cv.drawCircle(sx, sy, 1.6 if k % 3 else 2.4, paint('#c9d4ff', 170))
    # moon
    glow(cv, x + w - 90, y + 110, 90, '#ffe08a', 120)
    cv.drawPath(minus(ov(x + w - 90, y + 110, 30), ov(x + w - 76, y + 100, 27)), paint('#ffd75e'))
    # houses across the street, lit windows, bare trees, a street lamp
    def house(hx, hy, hw, hh, roof, wall):
        body_ = rr(hx, hy, hw, hh, 2)
        cv.drawPath(P([(hx - 12, hy + 2), (hx + hw / 2, hy - roof), (hx + hw + 12, hy + 2)]), paint('#0a0e22'))
        cv.drawPath(P([(hx - 12, hy + 2), (hx + hw / 2, hy - roof), (hx + hw + 12, hy + 2)]), paint('#20284c', stroke=3))
        cv.drawPath(body_, paint(wall))
        for wx in (hx + hw * 0.18, hx + hw * 0.62):
            win = rr(wx, hy + hh * 0.28, hw * 0.2, hh * 0.3, 2)
            cv.drawPath(win, paint('#ffc864')); cv.drawPath(win, paint('#0a0e22', stroke=2.5))
            cv.drawPath(P([(wx + hw * 0.1, hy + hh * 0.28), (wx + hw * 0.1, hy + hh * 0.58)], False), paint('#0a0e22', stroke=2))
            glow(cv, wx + hw * 0.1, hy + hh * 0.43, hw * 0.3, '#ffc864', 70)
    for k, (tx, th) in enumerate(((x + 180, 190), (x + 372, 170))):
        cv.drawPath(P([(tx, y + 300), (tx, y + 300 - th)], False), paint('#0b0f24', stroke=7))
        for b_ in range(4):
            a_ = -math.pi / 2 + (b_ - 1.5) * 0.45
            cv.drawPath(P([(tx, y + 300 - th * (0.4 + 0.15 * b_)), (tx + 44 * math.cos(a_), y + 300 - th * (0.4 + 0.15 * b_) + 44 * math.sin(a_))], False),
                        paint('#0b0f24', stroke=4))
    house(x - 10, y + 170, 150, 110, 64, '#1b2347')
    house(x + 205, y + 196, 130, 90, 54, '#18203f')
    house(x + 400, y + 166, 160, 116, 66, '#1c2449')
    cv.drawPath(P([(x + w - 30, y + 330), (x + w - 30, y + 200)], False), paint('#0b0f24', stroke=6))
    glow(cv, x + w - 30, y + 204, 70, '#ffd27a', 120); cv.drawCircle(x + w - 30, y + 204, 8, paint('#fff2c8'))
    cv.drawRect(skia.Rect.MakeXYWH(x, y + 322, w, h), paint('#121733'))
    # patrol car light bar behind them, washing everything red and blue
    glow(cv, x + 30, y + 330, 280, '#ff1830', 170)
    glow(cv, x + w - 30, y + 330, 280, '#2a5cff', 180)
    # (the cast is drawn by cast_bg / cast_fg so the background can be blurred)



def cast_bg(cv, x, y, w, h):
    """The double and the second officer behind: drawn on the background layer, which is blurred."""
    pen = Pen(cv)
    C.draw_bust(pen, 'double', x + 64, y + 300, 0.36, C.Pose('wide_grin', t=2.0, turn=0.25, bloodshot=0.8), detail=2,
                light=dict(rim='#ff3048', rim_a=130, side=-1))
    C.draw_bust(pen, 'officer2', x + w - 64, y + 300, 0.36, C.Pose('creep_smile', t=3.1, turn=-0.25, bloodshot=0.8), detail=2,
                light=dict(rim='#5a86ff', rim_a=140, side=1))


def cast_fg(cv, x, y, w, h):
    """The officer at the door: the film's officer and grin, closer to the lens, whiter skin, redder eyes."""
    sp = C.CAST['officer']
    keep = dict(sp)
    sp.update(skin='#e6dcd6', skin_sh='#bfb0ac', skin_dp='#6a5258', blush='#e3a2a8', eye_edge='#d9707c',
              eye_glow='#ff2a3e', eye_glow_a=110, veins=1.34, vein_a=1.45, vein_w=1.15, vein_even=True, vein_in=0.62)
    try:
        cv.save(); cv.rotate(-4, x + w / 2, y + 336)
        C.draw_bust(Pen(cv), 'officer', x + w / 2, y + 336, 0.64, C.Pose('wide_grin', t=1.4, bloodshot=1.0), detail=2,
                    light=dict(rim='#5a86ff', rim_a=120, side=1))
        cv.restore()
    finally:
        sp.clear(); sp.update(keep)


def main(out, line1='STAY', line2='INSIDE', tag='NOT POLICE'):
    os.makedirs(out, exist_ok=True)
    set_render_size(1280 * S, 720 * S)
    surf = skia.Surface(1280 * S, 720 * S); cv = surf.getCanvas(); cv.scale(S, S)
    cv.drawRect(skia.Rect.MakeWH(1280, 720), paint('#ff1f2d'))
    # the command, centred over the red panel
    cx = 336
    s1 = fit(line1, BLACK, 168, 600); s2 = fit(line2, BLACK, 168, 600)
    y1, y2 = 248, 400
    text(cv, line1, cx + 4, y1 + 6, s1, '#7a0a14', blur=4, a=120)                         # soft drop shadow
    text(cv, line1, cx, y1, s1, '#ffffff', blur=12, a=95)                                  # light glow
    text(cv, line1, cx, y1, s1, '#ffffff')
    text(cv, line2, cx + 4, y2 + 6, s2, '#8a0a14', blur=5, a=110)
    text(cv, line2, cx, y2, s2, INK)
    # the framed doorbell view (rounded like a phone / doorbell screen)
    fx, fy, fw, fh = 684, 10, 584, 700
    cv.drawPath(rr(fx, fy, fw, fh, 36), paint(INK))
    cv.drawPath(rr(fx + 6, fy + 6, fw - 12, fh - 12, 31), paint('#ffffff'))
    ix, iy, iw, ih = fx + 20, fy + 20, fw - 40, fh - 40
    inner = rr(ix, iy, iw, ih, 22)
    bgs = skia.Surface(1280 * S, 720 * S); bc = bgs.getCanvas(); bc.scale(S, S)
    scene(bc, ix, iy, iw, ih); cast_bg(bc, ix, iy, iw, ih)
    bga = bgs.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
    bga = cv2.GaussianBlur(bga, (0, 0), 2.4 * S)
    bga[..., :3] = (bga[..., :3].astype(np.float32) * 0.78).astype(np.uint8)
    bgi = skia.Image.fromarray(np.ascontiguousarray(bga), colorType=skia.kRGBA_8888_ColorType)
    cv.save(); cv.clipPath(inner, doAntiAlias=True)
    cv.save(); cv.resetMatrix(); cv.drawImage(bgi, 0, 0); cv.restore()
    cast_fg(cv, ix, iy, iw, ih)
    cv.drawRect(skia.Rect.MakeXYWH(ix, iy, iw, ih), skia.Paint(Shader=skia.GradientShader.MakeRadial(
        (ix + iw / 2, iy + ih / 2), ih * 0.8, [col('#000000', 0), col('#000000', 0), col('#000000', 120)], [0, 0.62, 1])))
    # face box with tag
    bx, by, bw, bh = ix + iw / 2 - 160, iy + 262, 320, 300
    g = '#3cf26a'
    cv.drawRect(skia.Rect.MakeXYWH(bx, by, bw, bh), paint(g, 140, stroke=2.5))
    for (x0, y0, dx, dy) in ((bx, by, 1, 1), (bx + bw, by, -1, 1), (bx, by + bh, 1, -1), (bx + bw, by + bh, -1, -1)):
        cv.drawPath(P([(x0, y0 + dy * 40), (x0, y0), (x0 + dx * 40, y0)], False), paint(g, stroke=7))
    tw = font(BLACK, 25).measureText(tag)
    cv.drawRect(skia.Rect.MakeXYWH(bx - 3.5, by - 40, tw + 22, 40), paint(g))
    text(cv, tag, bx + 8, by - 11, 25, '#062a12', align='left')
    # HUD
    cv.drawCircle(ix + 32, iy + 38, 11, paint('#ff2b2b')); glow(cv, ix + 32, iy + 38, 24, '#ff2b2b', 130)
    text(cv, 'LIVE', ix + 52, iy + 49, 31, '#ffffff', XBOLD, 'left')
    text(cv, 'FRONT DOOR', ix + iw - 24, iy + 49, 27, '#ffffff', XBOLD, 'right')
    tsw = font(XBOLD, 27).measureText('12:36:14 AM')
    cv.drawPath(rr(ix + 14, iy + ih - 64, tsw + 26, 44, 10), paint('#05060c', 205))
    text(cv, '12:36:14 AM', ix + 27, iy + ih - 32, 27, '#ffffff', XBOLD, 'left')
    cv.restore()
    cv.drawPath(inner, paint(INK, stroke=4))
    # police shield, bottom right (like the fire-dept emblem in the reference)
    sx, sy = ix + iw - 58, iy + ih - 74
    shield = P([(sx - 36, sy - 36), (sx, sy - 48), (sx + 36, sy - 36), (sx + 33, sy + 15, sx, sy + 46), (sx - 33, sy + 15, sx - 36, sy - 36)])
    shp(cv, shield, '#151a2e', 4); cv.drawPath(shield, paint('#ffffff', stroke=2.5))
    shp(cv, star(sx, sy - 6, 18, 8), '#f2c14e', 3)
    text(cv, 'POLICE', sx, sy + 26, 11.5, '#ffffff', XBOLD)
    # the arrow: round tail under the text, sweeping right and up into the face
    arrow = P([(318, 452), (322, 600, 450, 606), (590, 612, 718, 492)], False)
    cv.drawPath(arrow, paint(INK, stroke=46)); cv.drawPath(arrow, paint('#ffffff', stroke=30))
    head = P([(828, 404), (694, 440), (770, 538)])
    cv.drawPath(head, paint(INK, stroke=16)); cv.drawPath(head, paint('#ffffff'))
    arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3]
    bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    cv2.imwrite(os.path.join(out, 'thumbnail_4k.png'), bgr)
    cv2.imwrite(os.path.join(out, 'thumbnail_1280.jpg'), cv2.resize(bgr, (1280, 720), interpolation=cv2.INTER_AREA),
                [cv2.IMWRITE_JPEG_QUALITY, 95])
    print('written', out)


if __name__ == '__main__':
    main(sys.argv[1], *sys.argv[2:5])
