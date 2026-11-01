"""YouTube thumbnail in the channel's reference layout: red panel with a two-line command, a curved arrow, and a framed
doorbell-camera close-up of the grinning officer (red glowing eyes) with the double and the second officer behind him.
    python3 thumbnail.py <out dir>   -> thumbnail_4k.png (3840x2160) and thumbnail_1280.jpg (YouTube upload, < 2 MB)
Drawn in a 1280x720 design space and rendered at 3x.
"""
import os, sys, math
import numpy as np, cv2, skia

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'fonts', 'MontserratLC-900.ttf')
FONT8 = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'fonts', 'MontserratLC-800.ttf')
S = 3
W, H = 1280 * S, 720 * S
INK = '#111114'


def col(h, a=255):
    h = h.lstrip('#'); return skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def paint(c, a=255, stroke=0.0, blur=0.0):
    p = skia.Paint(Color=col(c, a), AntiAlias=True)
    if stroke: p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke); p.setStrokeJoin(skia.Paint.kRound_Join); p.setStrokeCap(skia.Paint.kRound_Cap)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def path(pts, close=True):
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:]:
        if len(q) == 4: p.quadTo(*q)
        elif len(q) == 6: p.cubicTo(*q)
        else: p.lineTo(*q)
    if close: p.close()
    return p


def shape(cv, p, fill, lw=4.0, line=INK):
    cv.drawPath(p, paint(fill)); cv.drawPath(p, paint(line, stroke=lw))


def oval(cx, cy, rx, ry):
    p = skia.Path(); p.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry)); return p


def rrect(x, y, w, h, r):
    p = skia.Path(); p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)); return p


def glow(cv, cx, cy, r, c, a):
    cv.drawCircle(cx, cy, r, skia.Paint(Shader=skia.GradientShader.MakeRadial((cx, cy), r, [col(c, a), col(c, 0)])))


def text(cv, s, x, y, size, c, font=FONT, align='left', blur=0.0, a=255):
    f = skia.Font(skia.Typeface.MakeFromFile(font), size)
    w = f.measureText(s)
    x0 = x - w / 2 if align == 'center' else (x - w if align == 'right' else x)
    cv.drawString(s, x0, y, f, paint(c, a, blur=blur))
    return w


# ------------------------------------------------------------------ one face, thumbnail style
def face(cv, cx, cy, sc, skin, hair=None, cap=False, bun=False, dim=0.0):
    """A grinning head centred at (cx, cy); sc = 1 means a 300 x 330 head."""
    cv.save(); cv.translate(cx, cy); cv.scale(sc, sc)
    lw = 5.0
    if hair == 'bun':
        shape(cv, oval(0, -190, 52, 44), '#3a2a22', lw)
    head = path([(-140, -60), (-150, 60, -120, 150), (-90, 200, 0, 205), (90, 200, 120, 150), (150, 60, 140, -60),
                 (130, -160, 0, -170), (-130, -160, -140, -60)])
    # ears
    for s in (-1, 1):
        shape(cv, oval(s * 146, 20, 22, 36), skin, lw)
    shape(cv, head, skin, lw)
    cv.save(); cv.clipPath(head, doAntiAlias=True)
    cv.drawPath(oval(-150, 80, 80, 170), paint('#000000', 26, blur=18))         # side shade
    cv.drawPath(oval(0, 230, 160, 60), paint('#000000', 30, blur=18))
    cv.restore()
    if hair and hair not in ('bun',):
        shape(cv, path([(-142, -40), (-150, -150, -40, -175), (60, -190, 140, -120), (152, -60, 142, -30), (110, -95, 40, -110),
                        (-60, -120, -142, -40)]), hair, lw)
    if hair == 'bun':
        shape(cv, path([(-142, -40), (-150, -160, 0, -170), (150, -160, 142, -40), (90, -110, 0, -118), (-90, -110, -142, -40)]), '#3a2a22', lw)
    # eye sockets: dark, sunken
    for s in (-1, 1):
        cv.drawPath(oval(s * 62, -10, 62, 44), paint('#3b2230', 150, blur=10))
    # brows, angled down to the centre
    for s in (-1, 1):
        cv.drawPath(path([(s * 110, -78), (s * 60, -70, s * 20, -46), (s * 22, -36), (s * 62, -58, s * 112, -62)]), paint(INK))
    # eyes: white, red glowing iris, small pupil
    for s in (-1, 1):
        ex, ey = s * 60, -8
        shape(cv, oval(ex, ey, 40, 30), '#f7f2ec', lw)
        cv.save(); cv.clipPath(oval(ex, ey, 40, 30), doAntiAlias=True)
        for k in range(4):                                                   # bloodshot veins
            a = (k * 1.7 + (0.4 if s > 0 else 1.1))
            cv.drawPath(path([(ex + 40 * math.cos(a), ey + 30 * math.sin(a)), (ex + 18 * math.cos(a + 0.3), ey + 14 * math.sin(a + 0.3))], False),
                        paint('#d23a3a', 150, stroke=1.6))
        glow(cv, ex, ey + 2, 34, '#ff2a2a', 150)
        cv.drawPath(oval(ex, ey + 2, 19, 19), paint('#e01020'))
        cv.drawPath(oval(ex, ey + 2, 19, 19), paint('#7a0008', stroke=2.4))
        cv.drawPath(oval(ex, ey + 2, 8, 8), paint('#170306'))
        cv.drawPath(oval(ex - 6, ey - 5, 4.5, 4), paint('#ffffff', 230))
        cv.restore()
        cv.drawPath(path([(ex - 40, ey - 6), (ex, ey - 34, ex + 40, ey - 6)], False), paint(INK, stroke=lw + 1))
        glow(cv, ex, ey + 2, 70, '#ff2020', 60)
    # nose
    cv.drawPath(path([(-4, 30), (-14, 62, -6, 70)], False), paint(INK, stroke=4))
    cv.drawPath(oval(-12, 72, 6, 4), paint(INK)); cv.drawPath(oval(12, 72, 6, 4), paint(INK))
    # the grin: far too wide, two rows of teeth over dark red gums
    mouth = path([(-122, 96), (-60, 128, 0, 128), (60, 128, 122, 96), (110, 176, 0, 190), (-110, 176, -122, 96)])
    shape(cv, mouth, '#5a0d14', lw + 1)
    cv.save(); cv.clipPath(mouth, doAntiAlias=True)
    cv.drawPath(path([(-130, 92), (0, 132, 130, 92), (130, 150), (0, 166, -130, 150)]), paint('#a01c28'))   # gums
    top = path([(-118, 100), (0, 140, 118, 100), (112, 146), (0, 160, -112, 146)])
    bot = path([(-108, 152), (0, 166, 108, 152), (96, 178), (0, 196, -96, 178)])
    for tp in (top, bot):
        cv.drawPath(tp, paint('#fbf8f1')); cv.drawPath(tp, paint('#2a1a1a', stroke=2.5))
    for k in range(-5, 6):                                                    # tooth gaps
        x = k * 21
        cv.drawPath(path([(x, 104 + abs(k) * -2 + 22), (x, 158)], False), paint('#3a2626', 210, stroke=2.4))
        cv.drawPath(path([(x * 0.9, 152), (x * 0.9, 190)], False), paint('#3a2626', 210, stroke=2.4))
    cv.drawPath(path([(-130, 150), (0, 160, 130, 150)], False), paint('#5a0d14', stroke=3))
    cv.restore()
    cv.drawPath(mouth, paint(INK, stroke=lw + 1))
    for s in (-1, 1):                                                         # smile folds pushed into the cheeks
        cv.drawPath(path([(s * 118, 70), (s * 146, 104, s * 128, 140)], False), paint(INK, 200, stroke=4))
        cv.drawPath(oval(s * 92, 52, 26, 12), paint('#d26a6a', 70, blur=8))
    if cap:
        crown = path([(-160, -118), (-176, -228, -60, -250), (60, -262, 176, -230), (162, -118)])
        shape(cv, crown, '#1d2a4a', lw)
        cv.save(); cv.clipPath(crown, doAntiAlias=True); cv.drawPath(oval(-60, -210, 80, 30), paint('#ffffff', 22, blur=12)); cv.restore()
        shape(cv, rrect(-164, -136, 328, 30, 8), '#0f1220', lw)
        cv.drawPath(path([(-150, -122), (150, -122)], False), paint('#d9b45a', stroke=4))
        shape(cv, path([(-160, -108), (0, -58, 160, -108), (150, -86), (0, -40, -150, -86)]), '#0b0d16', lw)
        # cap badge
        star = [(0, -232)]
        for k in range(1, 12):
            r = 36 if k % 2 == 0 else 15
            a = -math.pi / 2 + k * math.pi / 6
            star.append((r * math.cos(a), -196 + r * math.sin(a)))
        shape(cv, path(star), '#e2b84c', 3.5)
        shape(cv, oval(0, -196, 12, 12), '#b88a26', 2.5)
    if dim:
        cv.drawPath(oval(0, 0, 240, 290), paint('#000000', int(255 * dim), blur=60))
    cv.restore()


def body(cv, cx, top, sc, kind):
    cv.save(); cv.translate(cx, top); cv.scale(sc, sc)
    lw = 5.0
    if kind == 'police':
        torso = path([(-300, 400), (-290, 120, -150, 40), (-60, 10), (60, 10), (150, 40, 290, 120), (300, 400)])
        shape(cv, torso, '#1f2c4f', lw)
        cv.drawPath(path([(-60, 10), (0, 120), (60, 10)]), paint('#e9e7e2')); cv.drawPath(path([(-60, 10), (0, 120), (60, 10)], False), paint(INK, stroke=lw))
        shape(cv, path([(-16, 40), (16, 40), (26, 330), (0, 360), (-26, 330)]), '#0d0f18', lw)
        for s in (-1, 1):
            shape(cv, path([(s * 60, 10), (s * 130, 60), (s * 96, 130), (s * 20, 70)]), '#25335c', lw)
        star = []
        for k in range(12):
            r = 34 if k % 2 == 0 else 15
            a = -math.pi / 2 + k * math.pi / 6
            star.append((-150 + r * math.cos(a), 170 + r * math.sin(a)))
        shape(cv, path(star), '#e2b84c', 3.5)
        shape(cv, rrect(90, 150, 120, 34, 6), '#d9c27a', 3.5)
        text(cv, 'POLICE', 150, 176, 22, '#2a2416', FONT8, 'center')
        shape(cv, rrect(170, 70, 56, 90, 10), '#121318', lw)                 # shoulder radio
        cv.drawPath(oval(198, 96, 10, 10), paint('#ff3030')); glow(cv, 198, 96, 26, '#ff3030', 160)
    else:
        torso = path([(-260, 400), (-250, 130, -130, 40), (-50, 14), (50, 14), (130, 40, 250, 130), (260, 400)])
        shape(cv, torso, '#8c8f96' if kind == 'coat' else '#24314f', lw)
        cv.drawPath(path([(-50, 14), (0, 100), (50, 14)]), paint('#2a2a30'))
    cv.restore()


def doorbell_scene(w, h):
    """The framed picture: drawn flat, then bent through a doorbell fisheye."""
    s = skia.Surface(w, h); cv = s.getCanvas(); k = w / 560.0
    cv.scale(k, k)
    cv.drawRect(skia.Rect.MakeWH(560, 700), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 0), (0, 700)], [col('#0b1226'), col('#1a1d33')])))
    # porch: siding, door frame, lamp
    for y in range(60, 520, 26):
        cv.drawLine(0, y, 560, y, paint('#2a3150', 120, stroke=2))
    shape(cv, rrect(20, 40, 120, 480, 6), '#3a2a26', 4)
    glow(cv, 60, 110, 120, '#ffc46a', 110); shape(cv, rrect(48, 86, 24, 44, 5), '#ffd78e', 3)
    cv.drawRect(skia.Rect.MakeXYWH(0, 520, 560, 180), paint('#151826'))
    for x in range(0, 560, 40):
        cv.drawLine(x, 520, x - 30, 700, paint('#0e1020', 255, stroke=3))
    # police lights washing the edges
    cv.drawRect(skia.Rect.MakeWH(560, 700), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 0), (210, 0)], [col('#ff1830', 150), col('#ff1830', 0)])))
    cv.drawRect(skia.Rect.MakeWH(560, 700), skia.Paint(Shader=skia.GradientShader.MakeLinear([(560, 0), (350, 0)], [col('#2a62ff', 160), col('#2a62ff', 0)])))
    # the double (left) and the second officer (right), behind
    body(cv, 92, 395, 0.62, 'coat'); face(cv, 92, 300, 0.55, '#d9cbbc', hair='#5a3a28', dim=0.32)
    body(cv, 470, 395, 0.62, 'police2'); face(cv, 470, 300, 0.55, '#dfcfc2', hair='bun', cap=False, dim=0.32)
    # the officer, close to the lens
    body(cv, 280, 520, 1.0, 'police'); face(cv, 280, 330, 1.02, '#ece0d0', cap=True)
    img = s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3].copy()
    # fisheye: the centre swells toward the lens
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx, ny = (xx - w / 2) / (w / 2), (yy - h / 2) / (w / 2)
    r2 = nx * nx + ny * ny
    f = (1 + 0.16 * r2) / 1.06
    img = cv2.remap(img, nx * f * (w / 2) + w / 2, ny * f * (w / 2) + h / 2, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    vig = np.clip(1 - 0.55 * np.clip(np.sqrt(r2) - 0.25, 0, 1) ** 1.4, 0, 1)[..., None]
    return (img * vig).astype(np.uint8)


def main(out):
    os.makedirs(out, exist_ok=True)
    surf = skia.Surface(W, H); cv = surf.getCanvas(); cv.scale(S, S)
    cv.drawRect(skia.Rect.MakeWH(1280, 720), paint('#ff1f2e'))
    cv.drawRect(skia.Rect.MakeWH(1280, 720), skia.Paint(Shader=skia.GradientShader.MakeRadial((300, 330), 700, [col('#ff3a46'), col('#e3101f')])))
    # the command: white with a soft glow, black underneath
    for blur, a in ((26, 150), (10, 120)):
        text(cv, 'STAY', 62, 262, 196, '#ffffff', blur=blur, a=a)
    text(cv, 'STAY', 66, 270, 196, '#7a0010', a=110)
    text(cv, 'STAY', 62, 262, 196, '#ffffff')
    text(cv, 'INSIDE', 46, 418, 158, INK)
    # the framed doorbell view
    fx, fy, fw, fh = 686, 8, 584, 704
    cv.drawPath(rrect(fx, fy, fw, fh, 34), paint(INK))
    cv.drawPath(rrect(fx + 7, fy + 7, fw - 14, fh - 14, 28), paint('#ffffff'))
    ix, iy, iw, ih = fx + 19, fy + 19, fw - 38, fh - 38
    pic = doorbell_scene(iw * S, ih * S)
    img = skia.Image.fromarray(np.dstack([pic, np.full(pic.shape[:2], 255, np.uint8)]).copy(), colorType=skia.kRGBA_8888_ColorType)
    cv.save(); cv.clipPath(rrect(ix, iy, iw, ih, 22), doAntiAlias=True)
    cv.drawImageRect(img, skia.Rect.MakeXYWH(ix, iy, iw, ih), skia.SamplingOptions(skia.FilterMode.kLinear))
    # doorbell HUD
    cv.drawCircle(ix + 30, iy + 34, 10, paint('#ff2a2a')); glow(cv, ix + 30, iy + 34, 22, '#ff2a2a', 120)
    text(cv, 'LIVE', ix + 50, iy + 45, 30, '#ffffff', FONT8)
    text(cv, 'FRONT DOOR', ix + iw - 22, iy + 45, 26, '#ffffff', FONT8, 'right')
    text(cv, '12:36:14 AM', ix + 24, iy + ih - 26, 26, '#ffffff', FONT8)
    # face box with the identity tag
    bx, by, bw, bh = ix + 150, iy + 170, 250, 310
    g = '#39f06a'
    for (x0, y0, dx, dy) in ((bx, by, 1, 1), (bx + bw, by, -1, 1), (bx, by + bh, 1, -1), (bx + bw, by + bh, -1, -1)):
        cv.drawPath(path([(x0, y0 + dy * 34), (x0, y0), (x0 + dx * 34, y0)], False), paint(g, stroke=6))
    cv.drawRect(skia.Rect.MakeXYWH(bx, by, bw, bh), paint(g, 120, stroke=2))
    tw = text(cv, 'ID: NOT VERIFIED', 0, -100, 22, '#000000', FONT)
    cv.drawRect(skia.Rect.MakeXYWH(bx, by - 36, tw + 20, 34), paint(g))
    text(cv, 'ID: NOT VERIFIED', bx + 10, by - 11, 22, '#06240f', FONT)
    cv.restore()
    cv.drawPath(rrect(ix, iy, iw, ih, 22), paint(INK, stroke=4))
    # the arrow: thick white hook from under the text to the officer's face
    arrow = path([(330, 470), (300, 640, 470, 640), (640, 640, 750, 470)], False)
    cv.drawPath(arrow, paint(INK, stroke=50)); cv.drawPath(arrow, paint('#ffffff', stroke=32))
    head = path([(805, 395), (700, 438), (770, 520)])
    cv.drawPath(head, paint(INK, stroke=18)); cv.drawPath(head, paint('#ffffff'))
    cv.drawCircle(330, 470, 25, paint(INK)); cv.drawCircle(330, 470, 16, paint('#ffffff'))
    arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3]
    bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    cv2.imwrite(os.path.join(out, 'thumbnail_4k.png'), bgr)
    small = cv2.resize(bgr, (1280, 720), interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(out, 'thumbnail_1280.jpg'), small, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print('written', out)


if __name__ == '__main__':
    main(sys.argv[1])
