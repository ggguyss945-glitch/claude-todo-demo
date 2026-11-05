"""Thumbnail for "If An Eighth Step Appears On Your Mirror... WIPE THE GLASS CLEAN", in the channel's layout (the police
thumbnail's red panel, two-line command and arrow) with a framed mirror: the film's Queen of Spades grinning out of the
glass, the seven lipstick steps behind her, the glowing eighth step, the 11:57 PM pill.
    python3 tools/thumbnail_mirror.py <out dir> [LINE1 LINE2 TAG] -> thumbnail_4k.png (3840x2160), thumbnail_1280.jpg
Drawn in a 1280x720 design space at 3x.
"""
import os, sys
import numpy as np, cv2, skia
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import characters as C
from engine.core import set_render_size, Pen
from thumbnail import S, INK, BLACK, XBOLD, col, paint, P, rr, text, fit, glow, font
from cast_sheets import _queen_build


def stairs_world(cv, x, y, w, h):
    """The film's stairs world: near-black glass with red step edges receding up into the dark."""
    cv.drawRect(skia.Rect.MakeXYWH(x, y, w, h), skia.Paint(Shader=skia.GradientShader.MakeLinear(
        [(0, y), (0, y + h)], [col('#07070c'), col('#140a12'), col('#2a0c16')], [0, 0.6, 1])))
    vx, vy = x + w * 0.5, y + h * 0.18
    for k in range(16):
        f = (k / 15.0) ** 1.7
        yy = vy + (y + h - vy) * f
        hw = 30 + (w * 0.62) * f
        a = int(40 + 180 * f)
        cv.drawLine(vx - hw, yy, vx + hw, yy, paint('#ff2340', a, stroke=1.2 + 3.5 * f))
        glow(cv, vx, yy, hw * 0.9, '#ff1030', int(14 * f))
    glow(cv, vx, vy + 30, 120, '#ffd9e0', 40)                                   # cold light at the top of the stairs


def lipstick_steps(cv, x0, y0, step_w, step_h, n, a=255, lw=9.0):
    """n lipstick steps climbing up and right from (x0, y0) (bottom-left corner), drawn as one smeary red stroke."""
    pts = [(x0, y0)]
    for k in range(n):
        x, yv = pts[-1]
        pts.append((x, yv - step_h)); pts.append((x + step_w, yv - step_h))
    p = P(pts, False)
    cv.drawPath(p, paint('#ff2a44', int(a * 0.35), stroke=lw * 2.4, blur=6))
    cv.drawPath(p, paint('#c8102e', a, stroke=lw))
    cv.drawPath(p, paint('#ff6a7c', int(a * 0.55), stroke=lw * 0.28))           # waxy highlight
    return pts


def queen(cv, cx, cy, sc, t=1.0):
    def build(a):
        _queen_build(3)(a); a.expr('queen_grin', 0); a.head_tilt(0, 10, 0.01)
    a = C.Acting('queen', seed=3, height=700.0, expr='queen_grin'); a._at = (cx, cy, sc)
    build(a)
    Pz = a.at(t); Pz.t = t
    C.draw_mode(Pen(cv), 'queen', 'bust', [cx, cy, sc], Pz, light=dict(rim='#ff4060', rim_a=150, side=-1, key=-0.2), main='r')


def main(out, line1='WIPE', line2='IT', tag='STEP 8'):
    os.makedirs(out, exist_ok=True)
    set_render_size(1280 * S, 720 * S)
    surf = skia.Surface(1280 * S, 720 * S); cv = surf.getCanvas(); cv.scale(S, S)
    cv.drawRect(skia.Rect.MakeWH(1280, 720), paint('#ff1f2d'))
    # the command
    cx = 336
    s1 = fit(line1, BLACK, 190, 600); s2 = fit(line2, BLACK, 190, 600)
    y1, y2 = 262, 430
    text(cv, line1, cx + 4, y1 + 6, s1, '#7a0a14', blur=4, a=120)
    text(cv, line1, cx, y1, s1, '#ffffff', blur=12, a=95)
    text(cv, line1, cx, y1, s1, '#ffffff')
    text(cv, line2, cx + 4, y2 + 6, s2, '#8a0a14', blur=5, a=110)
    text(cv, line2, cx, y2, s2, INK)
    # the mirror: dark wood frame with a bevel
    fx, fy, fw, fh = 676, 10, 592, 700
    cv.drawPath(rr(fx, fy, fw, fh, 26), paint(INK))
    cv.drawPath(rr(fx + 5, fy + 5, fw - 10, fh - 10, 22), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(fx, fy), (fx + fw, fy + fh)], [col('#6b4428'), col('#3a2414'), col('#5a381f'), col('#2a190d')], [0, 0.4, 0.7, 1])))
    for k in range(9):                                                             # wood grain
        yy = fy + 30 + k * 78
        cv.drawPath(P([(fx + 8, yy), (fx + fw / 2, yy + 14, fx + fw - 8, yy - 6)], False), paint('#1e1209', 70, stroke=2))
    ix, iy, iw, ih = fx + 30, fy + 30, fw - 60, fh - 60
    inner = rr(ix, iy, iw, ih, 10)
    # glass content: stairs world blurred behind, steps on the glass, the queen in focus
    bgs = skia.Surface(1280 * S, 720 * S); bc = bgs.getCanvas(); bc.scale(S, S)
    stairs_world(bc, ix, iy, iw, ih)
    bga = bgs.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
    bga = cv2.GaussianBlur(bga, (0, 0), 1.6 * S)
    bgi = skia.Image.fromarray(np.ascontiguousarray(bga), colorType=skia.kRGBA_8888_ColorType)
    cv.save(); cv.clipPath(inner, doAntiAlias=True)
    cv.save(); cv.resetMatrix(); cv.drawImage(bgi, 0, 0); cv.restore()
    queen(cv, ix + iw * 0.60, iy + 330, 0.62)
    # the seven lipstick steps on the glass (over her, lower left, climbing toward her face)
    sx0, sy0 = 772, 600
    pts = lipstick_steps(cv, sx0, sy0, 18, 38, 7, a=240, lw=8)
    # the eighth step: a clean glowing line below the bottom step (behind the glass)
    e8 = P([(sx0 - 6, sy0 + 44), (sx0 + 44, sy0 + 44)], False)
    cv.drawPath(e8, paint('#ff1030', 230, stroke=34, blur=12))
    cv.drawPath(e8, paint('#ff3a52', 255, stroke=11))
    cv.drawPath(e8, paint('#ffe4e8', 255, stroke=3.5))
    # glass sheen + vignette
    cv.drawPath(P([(ix + iw * 0.62, iy), (ix + iw * 0.80, iy), (ix + iw * 0.30, iy + ih), (ix + iw * 0.12, iy + ih)]),
                paint('#ffffff', 16))
    cv.drawPath(P([(ix + iw * 0.86, iy), (ix + iw * 0.90, iy), (ix + iw * 0.40, iy + ih), (ix + iw * 0.36, iy + ih)]),
                paint('#ffffff', 12))
    cv.drawRect(skia.Rect.MakeXYWH(ix, iy, iw, ih), skia.Paint(Shader=skia.GradientShader.MakeRadial(
        (ix + iw / 2, iy + ih * 0.45), ih * 0.82, [col('#000000', 0), col('#000000', 0), col('#000000', 150)], [0, 0.6, 1])))
    # time pill, top left of the glass
    tsw = font(XBOLD, 27).measureText('11:57 PM')
    cv.drawPath(rr(ix + 14, iy + 14, tsw + 52, 44, 10), paint('#05060c', 210))
    cv.drawCircle(ix + 34, iy + 36, 8, paint('#ff2b2b')); glow(cv, ix + 34, iy + 36, 18, '#ff2b2b', 120)
    text(cv, '11:57 PM', ix + 50, iy + 46, 27, '#ffffff', XBOLD, 'left')
    cv.restore()
    cv.drawPath(inner, paint(INK, stroke=4))
    # tag on the eighth step
    tw = font(BLACK, 25).measureText(tag)
    tx, ty = sx0 + 58, sy0 + 24
    cv.drawPath(rr(tx, ty, tw + 24, 40, 6), paint('#ffffff'))
    cv.drawPath(rr(tx, ty, tw + 24, 40, 6), paint(INK, stroke=3))
    text(cv, tag, tx + 12, ty + 30, 25, '#c8102e', BLACK, 'left')
    # the arrow: from under the text, sweeping right into the eighth step
    arrow = P([(318, 482), (318, 650, 470, 662), (600, 670, 684, 646)], False)
    cv.drawPath(arrow, paint(INK, stroke=46)); cv.drawPath(arrow, paint('#ffffff', stroke=30))
    head = P([(752, 644), (670, 600), (678, 690)])
    cv.drawPath(head, paint(INK, stroke=16)); cv.drawPath(head, paint('#ffffff'))
    arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3]
    bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    cv2.imwrite(os.path.join(out, 'thumbnail_4k.png'), bgr)
    cv2.imwrite(os.path.join(out, 'thumbnail_1280.jpg'), cv2.resize(bgr, (1280, 720), interpolation=cv2.INTER_AREA),
                [cv2.IMWRITE_JPEG_QUALITY, 95])
    print('written', out)


if __name__ == '__main__':
    main(sys.argv[1], *sys.argv[2:5])
