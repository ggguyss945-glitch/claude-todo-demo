#!/usr/bin/env python3
"""Thumbnail v2 for "Perfect Score", modelled on the Loaded Dice channel's top Shorts.

    make_thumbnail_v2.py <frame render> <plate render> <out dir>

Renders: node render.js --app app --gl egl --w 2160 --h 3840 --q brand=1 --stills 230.5,231.5

What the channel's best performers share (Eye in the Sky 37M, Unluckiest win 18M, Cheating or smart 12M):
a plain frame from the video, one centred subject in a medium shot showing the story's prop to camera,
context behind, and the video's own small caption burned in as a curiosity fragment. Their newest adds a
single flat label with a hand-drawn arrow ("BAD IDEA"). So:
  A: the frame and caption only
  B: the same with one flat label and arrow pointing at the 100
YouTube's desktop grid crops Shorts to about 2:3 (8% off the top and bottom); everything that matters
sits inside that.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_thumbnail import vignette  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CAPTION_FONT = os.path.join(HERE, '..', '..', 'Perfect Score V1', 'app', 'fonts', 'LiberationSans-Bold.ttf')
CAPTION = 'to accuse you of cheating.'  # the film's own caption at 5.0-6.6 s
LABEL = 'TOO PERFECT?'
SCORE = (1300, 1715)  # centre of the circled 100 in the 2160x3840 frame
W, H = 2160, 3840


def film_caption(img, text):
    """Same look as overlay.js drawCaption: white bold sans, black outline, soft drop shadow, at 71.65% height."""
    size = int(0.0432 * W)
    f = ImageFont.truetype(CAPTION_FONT, size)
    x, y = W / 2, 0.7165 * H
    sh = Image.new('L', img.size, 0)
    ImageDraw.Draw(sh).text((x, y + size * 0.04), text, font=f, fill=217, anchor='ms', stroke_width=int(size * 0.08), stroke_fill=217)
    img.paste(Image.new('RGBA', img.size, (0, 0, 0, 255)), (0, 0), sh.filter(ImageFilter.GaussianBlur(size * 0.09)))
    ImageDraw.Draw(img).text((x, y), text, font=f, fill=(255, 255, 255, 255), anchor='ms', stroke_width=int(size * 0.08), stroke_fill=(0, 0, 0, 255))


def flat_label(img, text, cx, cy):
    """The channel's flat label: a solid blue box, white bold caps, no gradients."""
    f = ImageFont.truetype(CAPTION_FONT, 104)
    l, t, r, b = f.getbbox(text)
    px, py = 46, 30
    box = [cx - (r - l) / 2 - px, cy - (b - t) / 2 - py, cx + (r - l) / 2 + px, cy + (b - t) / 2 + py]
    d = ImageDraw.Draw(img)
    d.rectangle(box, fill=(26, 104, 186, 255))
    d.text((box[0] + px - l, box[1] + py - t), text, font=f, fill=(255, 255, 255, 255))
    return box


def hand_arrow(img, start, ctrl, end, width=26, head=74):
    """A white hand-drawn arrow with a thin dark edge, like the channel's."""
    p0, p1, p2 = (np.array(p, float) for p in (start, ctrl, end))
    ts = np.linspace(0, 1, 120)
    pts = [(1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2 for t in ts]
    tang = pts[-1] - pts[-5]
    tang /= np.linalg.norm(tang)
    nrm = np.array([-tang[1], tang[0]])
    tip = pts[-1]
    wings = [tip - tang * head + nrm * head * 0.7, tip, tip - tang * head - nrm * head * 0.7]
    d = ImageDraw.Draw(img)
    for col, extra in [((20, 24, 36, 200), 8), ((255, 255, 255, 255), 0)]:
        w = width + extra
        for a, b in zip(pts[:-3], pts[1:-2]):
            d.line([tuple(a), tuple(b)], fill=col, width=w)
            d.ellipse([b[0] - w / 2, b[1] - w / 2, b[0] + w / 2, b[1] + w / 2], fill=col)
        for q in (wings[0], wings[2]):
            d.line([tuple(q), tuple(tip)], fill=col, width=w)
            d.ellipse([q[0] - w / 2, q[1] - w / 2, q[0] + w / 2, q[1] + w / 2], fill=col)
        d.ellipse([tip[0] - w / 2, tip[1] - w / 2, tip[0] + w / 2, tip[1] + w / 2], fill=col)


def base_frame(render, plate):
    # a clean frame like the channel's (their thumbnails barely use depth of field); the plate is kept for
    # reference only, since the paper and the whiteboard are too close in tone to separate cleanly
    img = Image.open(render).convert('RGB')
    img = ImageEnhance.Contrast(img).enhance(1.08)
    img = ImageEnhance.Color(img).enhance(1.1)
    return vignette(img, 0.32).convert('RGBA')


def grid_preview(a, b, out_dir):
    """Both variants as the desktop grid shows them (2:3 centre crop) and as a phone shows them (9:16)."""
    def crop23(im):
        h = int(W * 1.5)
        y0 = (H - h) // 2
        return im.crop((0, y0, W, y0 + h))
    tw = 360
    prev = Image.new('RGB', (4 * tw + 5 * 30, int(tw * 16 / 9) + 150), (255, 255, 255))
    d = ImageDraw.Draw(prev)
    f = ImageFont.truetype(CAPTION_FONT, 26)
    x = 30
    for im, lab in [(crop23(a), 'A: desktop grid (2:3)'), (crop23(b), 'B: desktop grid (2:3)'), (a, 'A: phone (9:16)'), (b, 'B: phone (9:16)')]:
        t = im.resize((tw, int(tw * im.size[1] / im.size[0])), Image.LANCZOS)
        m = Image.new('L', t.size, 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, t.size[0] - 1, t.size[1] - 1], radius=18, fill=255)
        prev.paste(t, (x, 30), m)
        d.text((x, 40 + t.size[1]), lab, font=f, fill=(30, 30, 30))
        x += tw + 30
    prev.save(os.path.join(out_dir, 'preview_thumbnail_v2_grid.png'), optimize=True)


def save(img, out_dir, name):
    rgb = img.convert('RGB')
    rgb.save(os.path.join(out_dir, f'{name}_2160x3840.png'), optimize=True)
    rgb.save(os.path.join(out_dir, f'{name}_2160x3840.jpg'), quality=91, subsampling=0, optimize=True)  # under YouTube's 2 MB
    return rgb


if __name__ == '__main__':
    render, plate, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    frame = base_frame(render, plate)
    a = frame.copy()
    film_caption(a, CAPTION)
    b = frame.copy()
    box = flat_label(b, LABEL, 1640, 2300)
    hand_arrow(b, (box[0] + 120, box[1] - 20), (1250, 2060), (SCORE[0] + 40, SCORE[1] + 130))
    film_caption(b, CAPTION)
    a, b = save(a, out, 'Perfect_Score_thumbnail_v2A'), save(b, out, 'Perfect_Score_thumbnail_v2B')
    grid_preview(a, b, out)
    for n in ('A', 'B'):
        p = os.path.join(out, f'Perfect_Score_thumbnail_v2{n}_2160x3840.jpg')
        print(n, os.path.getsize(p) // 1024, 'KB')
