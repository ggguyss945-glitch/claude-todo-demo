"""Twistory brand kit: lettering and finishing on the rendered stills.
    python3 make_twistory.py <logo render> <banner render> <thumbnail render> <fonts dir> <out dir>
"""
import sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
logo_p, banner_p, thumb_p, F, OUT = sys.argv[1:6]
YEL, TEAL, INK, WHITE = (255, 210, 63), (22, 163, 154), (18, 11, 7), (255, 255, 255)
font = lambda n, s: ImageFont.truetype(os.path.join(F, n), s)

def outlined(img, xy, text, f, fill, stroke, sw, anchor='mm', shadow=True):
    d = ImageDraw.Draw(img)
    if shadow:
        sh = Image.new('RGBA', img.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text((xy[0] + sw * 0.5, xy[1] + sw * 0.9), text, font=f, fill=(0, 0, 0, 150), anchor=anchor, stroke_width=sw, stroke_fill=(0, 0, 0, 150))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(sw * 0.6)))
    d.text(xy, text, font=f, fill=fill, anchor=anchor, stroke_width=sw, stroke_fill=stroke)

def wordmark(img, cx, cy, size, tilt=-3):
    """TWIST in yellow + ORY in white, one chunky inked word, tilted a little."""
    f = font('LilitaOne.ttf', size); sw = max(6, size // 11)
    a, b = 'TWIST', 'ORY'
    wa, wb = f.getlength(a), f.getlength(b)
    layer = Image.new('RGBA', (int(wa + wb + sw * 6), int(size * 1.6)), (0, 0, 0, 0))
    y = layer.height // 2
    outlined(layer, (sw * 3, y), a, f, YEL, INK, sw, anchor='lm')
    outlined(layer, (sw * 3 + wa, y), b, f, WHITE, INK, sw, anchor='lm')
    layer = layer.rotate(-tilt, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))
    return layer.size

# ---- logo: the render in a teal ring (YouTube crops it round)
lg = Image.open(logo_p).convert('RGBA'); N = lg.width
d = ImageDraw.Draw(lg); r = N * 0.485
d.ellipse([N / 2 - r, N / 2 - r, N / 2 + r, N / 2 + r], outline=TEAL, width=int(N * 0.035))
d.ellipse([N / 2 - r - N * 0.006, N / 2 - r - N * 0.006, N / 2 + r + N * 0.006, N / 2 + r + N * 0.006], outline=INK, width=int(N * 0.008))
lg.convert('RGB').save(os.path.join(OUT, 'Twistory_logo_2048.png'))
lg.convert('RGB').resize((800, 800), Image.LANCZOS).save(os.path.join(OUT, 'Twistory_logo_800.png'))

# ---- banner 2560x1440: name and tagline in the middle of the 1546x423 safe area
bn = Image.open(banner_p).convert('RGBA'); W, H = bn.size
wordmark(bn, W / 2, H / 2 - 40, 210)
outlined(bn, (W / 2, H / 2 + 120), 'History, with a twist.', font('Baloo2-ExtraBold.ttf', 72), WHITE, INK, 9)
bn.convert('RGB').save(os.path.join(OUT, 'Twistory_banner_2560x1440.png'))
bn.convert('RGB').save(os.path.join(OUT, 'Twistory_banner_2560x1440.jpg'), quality=92)
# phone crop preview: the centre 1546x423 every device shows
bn.crop(((W - 1546) // 2, (H - 423) // 2, (W + 1546) // 2, (H + 423) // 2)).convert('RGB').save(os.path.join(OUT, 'preview_banner_safe_area.png'))

# ---- thumbnail 2160x3840: two lines of inked text, top and bottom thirds, inside the centre crop
th = Image.open(thumb_p).convert('RGBA'); W, H = th.size
outlined(th, (W / 2, H * 0.12), 'HE GAVE AWAY', font('LilitaOne.ttf', 250), WHITE, INK, 24)
outlined(th, (W / 2, H * 0.19), 'SO MUCH GOLD...', font('LilitaOne.ttf', 250), YEL, INK, 24)
outlined(th, (W / 2, H * 0.80), 'IT BECAME', font('LilitaOne.ttf', 270), WHITE, INK, 26)
outlined(th, (W / 2, H * 0.875), 'WORTHLESS', font('LilitaOne.ttf', 330), YEL, INK, 30)
th.convert('RGB').save(os.path.join(OUT, 'Too_Much_Gold_thumbnail_2160x3840.png'))
th.convert('RGB').resize((1080, 1920), Image.LANCZOS).save(os.path.join(OUT, 'Too_Much_Gold_thumbnail_1080x1920.jpg'), quality=92)
print('ok')
