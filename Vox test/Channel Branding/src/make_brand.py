#!/usr/bin/env python3
"""Finishing pass for the POLYWIT channel art.

    make_brand.py <logo render> <banner render> <banner clean plate> <out dir>

The renders come from the film's own renderer (Perfect Score V1/app/brand.js):
  node render.js --app app --gl egl --w 2048 --h 2048 --q brand=1 --stills 200.5          (logo)
  node render.js --app app --gl egl --w 2048 --h 1152 --q brand=1 --stills 210.5,211.5    (banner + clean plate)

Outputs: logo (2048 and 800 px), banner 2048x1152, and previews of how each device crops them.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage
from scipy.spatial import Delaunay

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', 'fonts')
TITLE_FONT = os.path.join(FONTS, 'LilitaOne.ttf')
LABEL_FONT = os.path.join(FONTS, 'Fredoka-Bold.ttf')

NAME = 'POLYWIT'
TAGLINE = 'SMART STORIES  •  HONEST WINS'
NAVY, NAVY_DEEP, INK_RED, PAPER = (24, 40, 86), (10, 18, 44), (226, 30, 38), (246, 240, 226)

# YouTube channel art at 2048x1152: everything shows on TV, a 2048x338 band on desktop,
# and only the centre 1235x338 on every device (phones included)
BW, BH = 2048, 1152
SAFE = (BW / 2 - 617.5, BH / 2 - 169, BW / 2 + 617.5, BH / 2 + 169)
DESKTOP = (0, BH / 2 - 169, BW, BH / 2 + 169)


def font(path, size):
    return ImageFont.truetype(path, size)


def faceted_fill(size, top, bottom, cell, seed, jitter=0.18):
    """A low-poly gradient: jittered Delaunay triangles, each flat-shaded from a vertical gradient."""
    w, h = size
    rng = np.random.default_rng(seed)
    xs, ys = np.meshgrid(np.arange(-cell, w + 2 * cell, cell), np.arange(-cell, h + 2 * cell, cell))
    pts = np.stack([xs.ravel(), ys.ravel()], 1).astype(float)
    pts += rng.uniform(-cell * 0.45, cell * 0.45, pts.shape)
    tri = Delaunay(pts)
    img = Image.new('RGB', size)
    d = ImageDraw.Draw(img)
    top, bottom = np.array(top, float), np.array(bottom, float)
    for s in tri.simplices:
        p = pts[s]
        k = np.clip(p[:, 1].mean() / h, 0, 1)
        col = top + (bottom - top) * k
        col = np.clip(col * (1 + rng.uniform(-jitter, jitter)), 0, 255)
        d.polygon([tuple(q) for q in p], fill=tuple(int(c) for c in col))
    return img


def pen_ellipse(draw, box, width, color, rot_deg=0, start=0, end=360, steps=240, wobble=0.0, seed=1):
    """A hand-drawn marker ellipse: slightly uneven radius and pressure, open at the ends."""
    rng = np.random.default_rng(seed)
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    rx, ry = (box[2] - box[0]) / 2, (box[3] - box[1]) / 2
    rot = np.radians(rot_deg)
    ph = rng.uniform(0, 6.28, 3)
    prev = None
    for i in range(steps + 1):
        a = np.radians(start + (end - start) * i / steps)
        r = 1 + wobble * (np.sin(a * 2 + ph[0]) * 0.6 + np.sin(a * 3 + ph[1]) * 0.4)
        x, y = rx * r * np.cos(a), ry * r * np.sin(a)
        p = (cx + x * np.cos(rot) - y * np.sin(rot), cy + x * np.sin(rot) + y * np.cos(rot))
        if prev is not None:
            t = i / steps
            wv = width * (0.55 + 0.45 * np.sin(np.pi * min(1, t * 1.15)))  # taper at both ends
            draw.line([prev, p], fill=color, width=max(2, int(wv)))
            draw.ellipse([p[0] - wv / 2, p[1] - wv / 2, p[0] + wv / 2, p[1] + wv / 2], fill=color)
        prev = p


def title_block(text, size, seed=3):
    """Faceted low-poly lettering with a white rim, a stepped navy extrusion and a soft shadow."""
    f = font(TITLE_FONT, size)
    pad = int(size * 0.35)
    l, t, r, b = f.getbbox(text)
    w, h = r - l + 2 * pad, b - t + 2 * pad
    org = (pad - l, pad - t)
    rim = int(size * 0.055)
    depth = int(size * 0.07)

    def mask(stroke=0, dx=0, dy=0):
        m = Image.new('L', (w, h), 0)
        ImageDraw.Draw(m).text((org[0] + dx, org[1] + dy), text, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
        return m

    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    # shadow
    sh = mask(rim + 4, depth + 6, depth + 10).filter(ImageFilter.GaussianBlur(size * 0.06))
    out.paste(Image.new('RGBA', (w, h), (0, 0, 0, 255)), (0, 0), sh.point(lambda v: int(v * 0.42)))
    # extrusion: the rimmed silhouette stepped down-right
    for i in range(depth, 0, -1):
        k = i / depth
        col = tuple(int(NAVY_DEEP[j] * (1 - 0.3 * k)) for j in range(3)) + (255,)
        out.paste(Image.new('RGBA', (w, h), col), (0, 0), mask(rim, i, i))
    # white rim, then the faceted face
    out.paste(Image.new('RGBA', (w, h), (255, 255, 255, 255)), (0, 0), mask(rim))
    face = faceted_fill((w, h), (70, 128, 236), (16, 34, 92), int(size * 0.16), seed).convert('RGBA')
    out.paste(face, (0, 0), mask())
    # a soft top highlight on the face, like the sun on a low-poly surface
    hl = Image.new('L', (w, h), 0)
    ImageDraw.Draw(hl).rectangle([0, 0, w, org[1] + (b - t) * 0.42 + t], fill=60)
    hl = ImageChops.multiply(hl.filter(ImageFilter.GaussianBlur(size * 0.05)), mask())
    out.paste(Image.new('RGBA', (w, h), (255, 255, 255, 255)), (0, 0), hl)
    # where each letter sits, for accents
    boxes, x = [], org[0]
    for ch in text:
        cb = f.getbbox(ch)
        boxes.append((x + cb[0], org[1] + cb[1], x + cb[2], org[1] + cb[3]))
        x += f.getlength(ch)
    ink = (pad, pad, pad + r - l, pad + b - t)
    return out, boxes, ink


def label_pill(text, size, fg, bg, pad=(26, 12)):
    f = font(LABEL_FONT, size)
    l, t, r, b = f.getbbox(text)
    w, h = r - l + 2 * pad[0], b - t + 2 * pad[1]
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=bg)
    d.text((pad[0] - l, pad[1] - t), text, font=f, fill=fg)
    return im


def subscribe_button(height):
    """Red-ink button with faceted shading, a white '100' badge and a paper tag."""
    H = height
    f = font(TITLE_FONT, int(H * 0.56))
    label = 'SUBSCRIBE'
    lw = f.getlength(label)
    badge = int(H * 0.74)
    W = int(H * 0.32 + badge + H * 0.24 + lw + H * 0.42)
    pad = int(H * 0.6)
    im = Image.new('RGBA', (W + 2 * pad, H + 2 * pad), (0, 0, 0, 0))
    x0, y0 = pad, pad
    # shadow and a darker base step for depth
    sh = Image.new('L', im.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle([x0 + 6, y0 + 12, x0 + W + 6, y0 + H + 12], radius=H // 2, fill=150)
    im.paste(Image.new('RGBA', im.size, (0, 0, 0, 255)), (0, 0), sh.filter(ImageFilter.GaussianBlur(H * 0.16)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x0, y0 + 7, x0 + W, y0 + H + 7], radius=H // 2, fill=(130, 10, 18, 255))
    body = Image.new('L', im.size, 0)
    ImageDraw.Draw(body).rounded_rectangle([x0, y0, x0 + W, y0 + H], radius=H // 2, fill=255)
    face = faceted_fill(im.size, (255, 92, 88), (196, 16, 26), int(H * 0.42), 11, jitter=0.08).convert('RGBA')
    im.paste(face, (0, 0), body)
    rim = Image.new('L', im.size, 0)
    ImageDraw.Draw(rim).rounded_rectangle([x0, y0, x0 + W, y0 + H], radius=H // 2, outline=255, width=max(3, H // 22))
    im.paste(Image.new('RGBA', im.size, (255, 255, 255, 200)), (0, 0), rim)
    # white badge with a red hand-circled 100
    bx, by = x0 + int(H * 0.16), y0 + (H - badge) // 2
    d.ellipse([bx, by, bx + badge, by + badge], fill=PAPER + (255,))
    bf = font(TITLE_FONT, int(badge * 0.42))
    tw = bf.getlength('100')
    d.text((bx + (badge - tw) / 2, by + badge * 0.27), '100', font=bf, fill=INK_RED + (255,))
    pen_ellipse(d, (bx + badge * 0.1, by + badge * 0.2, bx + badge * 0.92, by + badge * 0.8), max(3, badge // 16), INK_RED + (255,), -12, 20, 350, wobble=0.04, seed=4)
    # label
    lx = bx + badge + H * 0.24
    l, t, r, b = f.getbbox(label)
    ly = y0 + (H - (b - t)) / 2 - t
    d.text((lx + 3, ly + 4), label, font=f, fill=(110, 6, 14, 255))
    d.text((lx, ly), label, font=f, fill=(255, 255, 255, 255))
    return im, (x0, y0, x0 + W, y0 + H)


def paper_tag(text, size, rot):
    f = font(LABEL_FONT, size)
    l, t, r, b = f.getbbox(text)
    w, h = int(r - l + size * 1.1), int(b - t + size * 0.75)
    im = Image.new('RGBA', (w + 30, h + 30), (0, 0, 0, 0))
    sh = Image.new('L', im.size, 0)
    ImageDraw.Draw(sh).rectangle([18, 20, w + 14, h + 18], fill=120)
    im.paste(Image.new('RGBA', im.size, (0, 0, 0, 255)), (0, 0), sh.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(im)
    d.rectangle([12, 12, w + 12, h + 12], fill=PAPER + (255,))
    for yy in range(12 + int(h * 0.33), h + 12, max(6, int(h * 0.3))):  # faint ruled lines, like an exam sheet
        d.line([(16, yy), (w + 8, yy)], fill=(190, 206, 228, 255), width=2)
    d.line([(12 + int(size * 0.45), 12), (12 + int(size * 0.45), h + 12)], fill=(236, 150, 150, 255), width=2)
    d.text((12 + size * 0.6 - l, 12 + size * 0.36 - t), text, font=f, fill=NAVY + (255,))
    return im.rotate(rot, resample=Image.BICUBIC, expand=True)


def cursor(size):
    """A white arrow pointer with a dark outline, clicking."""
    s = size / 100
    pts = [(0, 0), (0, 74), (18, 58), (31, 88), (44, 82), (31, 53), (54, 53)]
    im = Image.new('RGBA', (int(70 * s) + 20, int(100 * s) + 20), (0, 0, 0, 0))
    P = [(10 + x * s, 10 + y * s) for x, y in pts]
    sh = Image.new('L', im.size, 0)
    ImageDraw.Draw(sh).polygon([(x + 5, y + 7) for x, y in P], fill=140)
    im.paste(Image.new('RGBA', im.size, (0, 0, 0, 255)), (0, 0), sh.filter(ImageFilter.GaussianBlur(4)))
    d = ImageDraw.Draw(im)
    d.polygon(P, fill=(255, 255, 255, 255), outline=(14, 20, 40, 255), width=max(3, int(5 * s)))
    return im


def depth_of_field(full, plate, radius):
    """Blur the set behind the cast: the cast mask is where the two renders differ."""
    a = np.asarray(full.convert('RGB'), np.float32)
    b = np.asarray(plate.convert('RGB'), np.float32)
    diff = ndimage.gaussian_filter(np.abs(a - b).max(2), 1.5)
    m = diff > 14
    m = ndimage.binary_closing(m, iterations=4)
    m = ndimage.binary_fill_holes(m)
    m = ndimage.binary_opening(m, iterations=2)
    mask = ndimage.gaussian_filter(m.astype(np.float32), 1.2)[..., None]
    bg = np.asarray(plate.convert('RGB').filter(ImageFilter.GaussianBlur(radius)), np.float32)
    out = a * mask + bg * (1 - mask)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)), mask[..., 0]


def make_banner(full_path, plate_path, out_dir):
    full, plate = Image.open(full_path), Image.open(plate_path)
    img, cast_mask = depth_of_field(full, plate, 5)
    img = img.convert('RGBA')
    cx = BW / 2
    # a soft light pool behind the name lifts it off the board
    glow = Image.new('L', (BW, BH), 0)
    ImageDraw.Draw(glow).ellipse([cx - 420, SAFE[1] + 10, cx + 420, SAFE[3] - 10], fill=120)
    img.paste(Image.new('RGBA', (BW, BH), (255, 255, 255, 255)), (0, 0), glow.filter(ImageFilter.GaussianBlur(70)))

    # vertical rhythm inside the 338 px band: name, tagline, button
    title, boxes, ink = title_block(NAME, 160)
    tx = int(cx - (ink[0] + ink[2]) / 2)
    ty = int(SAFE[1] + 26 - ink[1])
    img.alpha_composite(title, (tx, ty))
    # the O gets circled in red ink, like the 100 on the exam
    ob = boxes[1]
    d = ImageDraw.Draw(img)
    pen_ellipse(d, (tx + ob[0] - 20, ty + ob[1] - 12, tx + ob[2] + 20, ty + ob[3] + 14), 11, INK_RED + (255,), -8, -60, 300, wobble=0.035, seed=7)

    tag = label_pill(TAGLINE, 27, (255, 255, 255, 255), NAVY + (235,), pad=(24, 10))
    gy = ty + ink[3] + 22
    img.alpha_composite(tag, (int(cx - tag.size[0] / 2), gy))

    btn, inner = subscribe_button(70)
    bx = int(cx - (inner[0] + inner[2]) / 2)
    by = int(gy + tag.size[1] + 16 - inner[1])
    img.alpha_composite(btn, (bx, by))
    # a paper sticky note beside the button and a cursor about to click it
    note = paper_tag('JOIN THE CLASS!', 21, 6)
    img.alpha_composite(note, (bx + inner[2] - 6, by + inner[1] - int(note.size[1] * 0.18)))
    cur = cursor(56)
    img.alpha_composite(cur, (bx + inner[2] - 120, by + inner[3] - 30))

    out = img.convert('RGB')
    out.save(os.path.join(out_dir, 'POLYWIT_banner_2048x1152.png'), optimize=True)
    out.save(os.path.join(out_dir, 'POLYWIT_banner_2048x1152.jpg'), quality=95, subsampling=0)
    ring = (tx + ob[0] - 26, ty + ob[1] - 18, tx + ob[2] + 26, ty + ob[3] + 20)
    bounds = {'name': (tx + ink[0], ty + ink[1], tx + ink[2], ty + ink[3]), 'O ring': ring, 'tagline': (int(cx - tag.size[0] / 2), gy, int(cx + tag.size[0] / 2), gy + tag.size[1]),
              'button': (bx + inner[0], by + inner[1], bx + inner[2], by + inner[3] + 8),
              'note': (bx + inner[2] - 6, by + inner[1] - int(note.size[1] * 0.18), bx + inner[2] - 6 + note.size[0], by + inner[1] + int(note.size[1] * 0.82))}
    return out, bounds


def zone_preview(banner, out_dir):
    """The banner with the TV / desktop / all-devices crops marked, plus each crop on its own."""
    im = banner.convert('RGBA')
    dim = Image.new('RGBA', im.size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(dim)
    dd.rectangle([0, 0, BW, DESKTOP[1]], fill=(0, 0, 0, 120))
    dd.rectangle([0, DESKTOP[3], BW, BH], fill=(0, 0, 0, 120))
    im.alpha_composite(dim)
    d = ImageDraw.Draw(im)
    lf = font(LABEL_FONT, 30)
    d.rectangle(DESKTOP, outline=(255, 210, 0, 255), width=4)
    d.rectangle(SAFE, outline=(255, 60, 60, 255), width=5)
    d.text((24, 22), 'TV: whole image', font=lf, fill=(255, 255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0, 255))
    d.text((24, DESKTOP[1] + 12), 'DESKTOP: 2048 x 338', font=lf, fill=(255, 210, 0, 255), stroke_width=3, stroke_fill=(0, 0, 0, 255))
    d.text((SAFE[0] + 14, SAFE[3] - 44), 'ALL DEVICES / MOBILE: 1235 x 338', font=lf, fill=(255, 90, 90, 255), stroke_width=3, stroke_fill=(0, 0, 0, 255))
    im.convert('RGB').save(os.path.join(out_dir, 'preview_banner_device_zones.png'), optimize=True)
    banner.crop(tuple(int(v) for v in SAFE)).save(os.path.join(out_dir, 'preview_banner_mobile_crop.png'))
    banner.crop(tuple(int(v) for v in DESKTOP)).save(os.path.join(out_dir, 'preview_banner_desktop_crop.png'))


def make_logo(path, out_dir):
    im = Image.open(path).convert('RGBA')
    N = im.size[0]
    d = ImageDraw.Draw(im)
    # red-ink ring just inside the round crop, two quick passes like a teacher's mark
    m = N * 0.045
    pen_ellipse(d, (m, m, N - m, N - m), int(N * 0.028), INK_RED + (255,), -6, -80, 285, wobble=0.012, seed=21)
    pen_ellipse(d, (m + N * 0.012, m + N * 0.02, N - m - N * 0.004, N - m + N * 0.004), int(N * 0.012), INK_RED + (235,), 4, 200, 400, wobble=0.015, seed=22)
    sq = im.convert('RGB')
    sq.save(os.path.join(out_dir, 'POLYWIT_logo_2048.png'), optimize=True)
    sq.resize((800, 800), Image.LANCZOS).save(os.path.join(out_dir, 'POLYWIT_logo_800.png'), optimize=True)
    # how YouTube shows it: a circle, large and at comment size
    circ = Image.new('L', (N, N), 0)
    ImageDraw.Draw(circ).ellipse([0, 0, N - 1, N - 1], fill=255)
    prev = Image.new('RGB', (1400, 760), (249, 249, 249))
    big = Image.new('RGB', (N, N), (249, 249, 249)); big.paste(sq, (0, 0), circ)
    prev.paste(big.resize((640, 640), Image.LANCZOS), (40, 60))
    pd = ImageDraw.Draw(prev)
    lf = font(LABEL_FONT, 30)
    for i, s in enumerate([240, 98, 40]):
        small = big.resize((s, s), Image.LANCZOS)
        x = 760 + [0, 300, 450][i]
        prev.paste(small, (x, 60 + (240 - s) // 2))
        pd.text((x, 320), f'{s}px', font=lf, fill=(60, 60, 60))
    pd.text((760, 420), 'POLYWIT', font=font(TITLE_FONT, 64), fill=NAVY)
    pd.text((760, 500), 'how the round crop reads at\nchannel, video-page and comment size', font=font(LABEL_FONT, 28), fill=(90, 90, 90))
    prev.save(os.path.join(out_dir, 'preview_logo_round_crop.png'), optimize=True)


if __name__ == '__main__':
    logo, full, plate, out = sys.argv[1:5]
    os.makedirs(out, exist_ok=True)
    make_logo(logo, out)
    banner, b = make_banner(full, plate, out)
    zone_preview(banner, out)
    inside = lambda r: r[0] >= SAFE[0] and r[1] >= SAFE[1] and r[2] <= SAFE[2] and r[3] <= SAFE[3]
    for k, r in b.items():
        print(f'{k:7s} {tuple(int(v) for v in r)}  inside all-device safe area: {inside(r)}')
