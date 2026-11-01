"""YouTube thumbnail in the channel's reference layout (crisp flat vector, like the firefighter/hotel/class thumbnails):
flat red panel with a centred two-line command (white with a soft glow over black), a thick curved arrow, and a framed
doorbell-camera close-up of a grinning officer with red glowing eyes, two more behind him, HUD and a face box.
    python3 thumbnail.py <out dir> [LINE1 LINE2 TAG]  -> thumbnail_4k.png (3840x2160), thumbnail_1280.jpg (upload)
Drawn in a 1280x720 design space and rendered at 3x.
"""
import os, sys, math
import numpy as np, cv2, skia

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
    # ears and head
    for s in (-1, 1):
        shp(cv, ov(s * 148, 28, 24, 38), skin, lw)
        cv.drawPath(ov(s * 148, 30, 10, 20), paint(shade))
    head = P([(-146, -40), (-152, 70, -128, 140), (-96, 196, 0, 200), (96, 196, 128, 140), (152, 70, 146, -40),
              (140, -150, 0, -158), (-140, -150, -146, -40)])
    shp(cv, head, skin, lw)
    clipped(cv, head, lambda: (cv.drawPath(P([(152, -60), (120, 80, 70, 210), (200, 210), (200, -60)]), paint(shade)),
                               cv.drawPath(ov(0, 230, 150, 40), paint(shade))))
    # dark sunken sockets
    for s in (-1, 1):
        cv.drawPath(ov(s * 62, 4, 66, 50), paint('#5a2a46', 150, blur=14))
        cv.drawPath(ov(s * 62, 26, 50, 18), paint('#5a2a46', 120, blur=8))
    # eyes: pink whites, glowing red irises
    for s in (-1, 1):
        ex, ey = s * 60, 0
        glow(cv, ex, ey, 78, '#ff1a2a', 90)
        eye = ov(ex, ey, 44, 33)
        shp(cv, eye, '#ffe3e6', 5.5)
        def inside(ex=ex, ey=ey):
            cv.drawPath(ov(ex, ey, 44, 33), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
                (ex, ey), 46, [col('#ffffff', 0), col('#ff6a78', 150)])))
            cv.drawPath(ov(ex, ey + 1, 22), paint('#ff1d2c'))
            cv.drawPath(ov(ex, ey + 1, 22), paint('#8a0011', stroke=3))
            cv.drawPath(ov(ex, ey + 1, 9), paint('#1a0205'))
            cv.drawPath(ov(ex - 8, ey - 7, 5.5, 4.5), paint('#ffffff'))
        clipped(cv, eye, inside)
        cv.drawPath(P([(ex - 46, ey - 4), (ex, ey - 40, ex + 46, ey - 4)], False), paint(INK, stroke=7))
    # brows: thick, angry
    for s in (-1, 1):
        shp(cv, P([(s * 116, -62), (s * 70, -66, s * 22, -36), (s * 26, -22), (s * 70, -46, s * 114, -44)]), INK, 2)
    # nose
    cv.drawPath(P([(-6, 46), (-16, 70, 0, 76)], False), paint(INK, stroke=4.5))
    cv.drawPath(ov(-12, 80, 6, 4.5), paint(INK)); cv.drawPath(ov(12, 80, 6, 4.5), paint(INK))
    # the grin: a crescent across the whole face, big even teeth, red gums
    mouth = P([(-130, 104), (-66, 132, 0, 134), (66, 132, 130, 104), (112, 196, 0, 204), (-112, 196, -130, 104)])
    cv.drawPath(mouth, paint('#3a0610'))
    def teeth():
        cv.drawPath(P([(-140, 96), (0, 140, 140, 96), (140, 152), (0, 162, -140, 152)]), paint('#c42638'))      # upper gum
        up = P([(-124, 108), (0, 146, 124, 108), (116, 158), (0, 170, -116, 158)])
        lo = P([(-104, 166), (0, 178, 104, 166), (92, 190), (0, 206, -92, 190)])
        for t in (up, lo):
            cv.drawPath(t, paint('#ffffff'))
        for k in range(-5, 6):
            x = k * 22.5
            cv.drawPath(P([(x, 132 - 0.0016 * x * x * 6), (x * 0.97, 166)], False), paint('#b9b4b8', stroke=2.6))
            if abs(k) <= 4: cv.drawPath(P([(x * 0.86, 168), (x * 0.86, 204)], False), paint('#b9b4b8', stroke=2.6))
        cv.drawPath(P([(-124, 160), (0, 172, 124, 160)], False), paint('#7a0e1c', stroke=4))
    clipped(cv, mouth, teeth)
    cv.drawPath(mouth, paint(INK, stroke=6))
    for s in (-1, 1):
        cv.drawPath(P([(s * 132, 78), (s * 162, 110, s * 140, 150)], False), paint(INK, stroke=5))
        cv.drawPath(ov(s * 100, 66, 30, 13), paint('#ff7b86', 80, blur=8))
    cv.drawPath(P([(-30, 226), (0, 232, 30, 226)], False), paint('#b3a497', stroke=4))
    # police cap
    crown = P([(-168, -104), (-188, -226, -70, -250), (70, -266, 188, -232), (170, -104)])
    shp(cv, crown, navy, lw)
    clipped(cv, crown, lambda: cv.drawPath(P([(-150, -120), (-170, -220, -60, -236), (-10, -150)]), paint('#2b3d75')))
    shp(cv, rr(-172, -128, 344, 34, 9), '#0f1426', lw)
    cv.drawPath(P([(-160, -111), (160, -111)], False), paint('#e7bf55', stroke=5))
    shp(cv, P([(-170, -96), (0, -38, 170, -96), (158, -70), (0, -14, -158, -70)]), '#0a0c14', lw)
    cv.drawPath(P([(-120, -80), (0, -40, 120, -80)], False), paint('#ffffff', 60, stroke=4))
    shp(cv, star(0, -192, 40, 17), '#f2c14e', 4.5)
    shp(cv, ov(0, -192, 13), '#c9952a', 3)
    if dim:
        cv.drawRect(skia.Rect.MakeLTRB(-400, -300, 400, 500), paint('#050814', int(255 * dim)))
        for s in (-1, 1):                                                                    # eyes still glow in the dark
            glow(cv, s * 60, 0, 60, '#ff1a2a', 150)
            cv.drawPath(ov(s * 60, 1, 22), paint('#ff1d2c')); cv.drawPath(ov(s * 60, 1, 9), paint('#1a0205'))
    cv.restore()


def scene(cv, x, y, w, h):
    """The doorbell picture inside the frame."""
    cv.drawRect(skia.Rect.MakeXYWH(x, y, w, h), skia.Paint(Shader=skia.GradientShader.MakeLinear(
        [(0, y), (0, y + h)], [col('#0a1230'), col('#1a2350'), col('#141a36')], [0, 0.55, 1])))
    for k in range(40):                                                                      # stars
        sx, sy = x + (k * 137.5) % w, y + 20 + (k * 71.3) % 160
        cv.drawCircle(sx, sy, 1.6 if k % 3 else 2.4, paint('#c9d4ff', 170))
    # house roofs across the street
    cv.drawPath(P([(x, y + 290), (x + 120, y + 200), (x + 240, y + 290), (x + 330, y + 230), (x + 440, y + 300),
                   (x + 540, y + 210), (x + w, y + 270), (x + w, y + h), (x, y + h)]), paint('#0c1128'))
    for wx, wy in ((x + 70, y + 300), (x + 170, y + 310), (x + 470, y + 320)):
        cv.drawRect(skia.Rect.MakeXYWH(wx, wy, 28, 22), paint('#ffc86a', 220)); glow(cv, wx + 14, wy + 11, 40, '#ffc86a', 70)
    # police lights behind them
    glow(cv, x + 40, y + 360, 260, '#ff1830', 150)
    glow(cv, x + w - 40, y + 360, 260, '#2a5cff', 160)
    # two more officers behind, in the dark
    officer(cv, x + 60, y + 300, 0.56, dim=0.42)
    officer(cv, x + w - 60, y + 300, 0.56, dim=0.42)
    # the one at the door
    officer(cv, x + w / 2, y + 318, 0.84)
    # lens vignette
    cv.drawRect(skia.Rect.MakeXYWH(x, y, w, h), skia.Paint(Shader=skia.GradientShader.MakeRadial(
        (x + w / 2, y + h / 2), h * 0.78, [col('#000000', 0), col('#000000', 0), col('#000000', 150)], [0, 0.6, 1])))


def main(out, line1='STAY', line2='INSIDE', tag='NOT POLICE'):
    os.makedirs(out, exist_ok=True)
    surf = skia.Surface(1280 * S, 720 * S); cv = surf.getCanvas(); cv.scale(S, S)
    cv.drawRect(skia.Rect.MakeWH(1280, 720), paint('#ff1f2d'))
    # the command, centred over the red panel
    cx = 336
    s1 = fit(line1, BLACK, 168, 600); s2 = fit(line2, BLACK, 168, 600)
    y1, y2 = 248, 400
    text(cv, line1, cx + 5, y1 + 7, s1, '#8a0a14', blur=5, a=150)                         # soft drop shadow
    text(cv, line1, cx, y1, s1, '#ffffff', blur=22, a=200)                                 # glow
    text(cv, line1, cx, y1, s1, '#ffffff', blur=8, a=170)
    text(cv, line1, cx, y1, s1, '#ffffff')
    text(cv, line2, cx + 4, y2 + 6, s2, '#8a0a14', blur=5, a=110)
    text(cv, line2, cx, y2, s2, INK)
    # the framed doorbell view (rounded like a phone / doorbell screen)
    fx, fy, fw, fh = 684, 10, 584, 700
    cv.drawPath(rr(fx, fy, fw, fh, 36), paint(INK))
    cv.drawPath(rr(fx + 6, fy + 6, fw - 12, fh - 12, 31), paint('#ffffff'))
    ix, iy, iw, ih = fx + 20, fy + 20, fw - 40, fh - 40
    inner = rr(ix, iy, iw, ih, 22)
    cv.save(); cv.clipPath(inner, doAntiAlias=True)
    scene(cv, ix, iy, iw, ih)
    # face box with tag
    bx, by, bw, bh = ix + iw / 2 - 138, iy + 252, 276, 254
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
    text(cv, '12:36:14 AM', ix + 26, iy + ih - 28, 27, '#ffffff', XBOLD, 'left')
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
