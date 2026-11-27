"""Channel logo and banner: a white keyhole-in-a-ring mark on solid red, and the wordmark NAME1 [mark] NAME2.
    python3 brand.py <out dir> [NAME1 NAME2 TAGLINE]
-> logo_800.png (profile picture; centred so the circle crop never cuts it),
   banner_2560x1440.png (everything inside YouTube's 1546x423 safe area, so it shows on phone, desktop and TV),
   banner_device_preview.png (the banner with the TV / desktop / phone crops outlined).
"""
import os, sys
import numpy as np, cv2, skia

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'fonts')
BLACK, XBOLD = os.path.join(FONTS, 'MontserratLC-900.ttf'), os.path.join(FONTS, 'MontserratLC-800.ttf')
RED, RED_DK, WHITE = '#ff0d1f', '#c4000f', '#ffffff'


def col(h, a=255):
    h = h.lstrip('#'); return skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(a))


def paint(c, a=255, stroke=0.0):
    p = skia.Paint(Color=col(c, a), AntiAlias=True)
    if stroke: p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
    return p


def mark(cv, cx, cy, size, c=WHITE, a=255):
    """Keyhole inside a bold ring; size = outer diameter."""
    s = size / 1000.0
    cv.save(); cv.translate(cx, cy); cv.scale(s, s)
    cv.drawCircle(0, 0, 465, paint(c, a, stroke=70))
    key = skia.Path()
    key.addCircle(0, -70, 118)
    key.moveTo(-62, -20); key.lineTo(62, -20); key.lineTo(112, 250); key.quadTo(114, 268, 96, 268)
    key.lineTo(-96, 268); key.quadTo(-114, 268, -112, 250); key.close()
    key.setFillType(skia.PathFillType.kWinding)
    cv.drawPath(key, paint(c, a))
    cv.restore()


def background(cv, w, h):
    cv.drawRect(skia.Rect.MakeWH(w, h), paint(RED))
    cv.drawRect(skia.Rect.MakeWH(w, h), skia.Paint(Shader=skia.GradientShader.MakeRadial(
        (w / 2, h / 2), max(w, h) * 0.62, [col(RED, 0), col(RED, 0), col(RED_DK, 200)], [0, 0.45, 1])))


def save(surf, path):
    arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3]
    cv2.imwrite(path, cv2.cvtColor(arr, cv2.COLOR_RGB2BGR))
    return arr


def main(out, name1='RULES', name2='AFTER DARK', tagline='FOLLOW THE RULES. SURVIVE THE NIGHT.'):
    os.makedirs(out, exist_ok=True)
    # ---------------------------------------------------------------- logo (800x800)
    s = skia.Surface(800, 800); cv = s.getCanvas()
    background(cv, 800, 800)
    mark(cv, 400, 400, 470)
    save(s, os.path.join(out, 'logo_800.png'))
    # ---------------------------------------------------------------- banner (2560x1440, safe area 1546x423)
    W, H = 2560, 1440
    s = skia.Surface(W, H); cv = s.getCanvas()
    background(cv, W, H)
    for k, (x, y, d) in enumerate(((330, 260, 900), (2260, 1180, 1000), (2380, 220, 520), (180, 1240, 560))):
        mark(cv, x, y, d, '#ffffff', 16)                                 # faint watermarks, outside the safe area
    f = skia.Font(skia.Typeface.MakeFromFile(BLACK), 100)
    gap, msize_k = 0.30, 1.36                                            # space round the mark, mark height vs cap
    def widths(size):
        f.setSize(size)
        cap = size * 0.70
        return f.measureText(name1), f.measureText(name2), cap * msize_k * 1.18, cap
    size = 100
    while True:
        a, b, m, cap = widths(size)
        total = a + b + m + 2 * cap * gap
        if total > 1420 or size > 220: break
        size += 2
    size -= 2; a, b, m, cap = widths(size); total = a + b + m + 2 * cap * gap
    tag_h = 0 if not tagline else 30
    block_h = cap + (tag_h + 34 if tagline else 0)
    top = H / 2 - block_h / 2
    base = top + cap
    x = W / 2 - total / 2
    shadow = skia.Paint(Color=col('#7a0009', 110), AntiAlias=True, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10))
    for dx, p in ((6, shadow), (0, paint(WHITE))):
        f.setSize(size)
        cv.drawString(name1, x + dx, base + dx, f, p)
        cv.drawString(name2, x + a + m + 2 * cap * gap + dx, base + dx, f, p)
    mark(cv, x + a + cap * gap + m / 2 + 3, base - cap / 2 + 3, m, '#7a0009', 90)
    mark(cv, x + a + cap * gap + m / 2, base - cap / 2, m)
    if tagline:
        ft = skia.Font(skia.Typeface.MakeFromFile(XBOLD), tag_h)
        sp_ = 0.22 * tag_h
        glyphs = ft.textToGlyphs(tagline); ws = ft.getWidths(glyphs)
        tw = sum(ws) + sp_ * (len(ws) - 1)
        pos, cx_ = [], W / 2 - tw / 2
        for wv in ws: pos.append(skia.Point(cx_, base + 34 + tag_h)); cx_ += wv + sp_
        cv.drawTextBlob(skia.TextBlob.MakeFromPosText(tagline, pos, ft), 0, 0, paint(WHITE, 225))
    arr = save(s, os.path.join(out, 'banner_2560x1440.png'))
    # ---------------------------------------------------------------- device preview with crop guides
    prev = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR).copy()
    guides = (('TV: full 2560x1440', (0, 0, 2560, 1440), (255, 255, 255)),
              ('Desktop: 2560x423', (0, 508, 2560, 931), (0, 220, 255)),
              ('Phone / safe area: 1546x423', (507, 508, 2053, 931), (80, 255, 80)))
    label_at = {0: (24, 60), 1: (24, 931 + 64), 2: (507 + 24, 931 - 30)}
    for k, (label, (x0, y0, x1, y1), c) in enumerate(guides):
        cv2.rectangle(prev, (x0 + 4, y0 + 4), (x1 - 4, y1 - 4), c, 6)
        cv2.putText(prev, label, label_at[k], cv2.FONT_HERSHEY_SIMPLEX, 1.8, c, 4, cv2.LINE_AA)
    cv2.imwrite(os.path.join(out, 'banner_device_preview.png'), cv2.resize(prev, (1280, 720), interpolation=cv2.INTER_AREA))
    print('written', out, 'wordmark size', size, 'width', round(total))


if __name__ == '__main__':
    main(sys.argv[1], *sys.argv[2:5])
