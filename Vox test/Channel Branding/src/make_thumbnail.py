#!/usr/bin/env python3
"""Thumbnail for the first POLYWIT video, "Perfect Score" (2160x3840, 9:16).

    make_thumbnail.py <thumbnail render> <clean plate> <out dir>

The renders come from Perfect Score V1/app/brand.js:
  node render.js --app app --gl egl --w 2160 --h 3840 --q brand=1 --stills 220.5,221.5

The cast stays sharp, the classroom drops into soft focus, and the graphics tell the story in three beats:
EVERY. SINGLE. EXAM. -> a red marker arrow to the circled 100 -> a rubber-stamped CHEATER? across the paper.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_brand import INK_RED, NAVY_DEEP, TITLE_FONT, depth_of_field, faceted_fill, font  # noqa: E402

TW, TH = 2160, 3840


def subject_glow(img, mask, color=(255, 255, 255), strength=0.5, grow=12, blur=30):
    """A soft halo just outside the cast so they lift off the blurred room."""
    m = mask > 0.5
    ring = ndimage.binary_dilation(m, iterations=grow) & ~m
    g = ndimage.gaussian_filter(ring.astype(np.float32), blur)
    g = np.clip(g / max(g.max(), 1e-6), 0, 1) * (1 - mask) * strength
    a = np.asarray(img, np.float32)
    a = a * (1 - g[..., None]) + np.array(color, np.float32) * g[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def vignette(img, amount=0.28):
    w, h = img.size
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h * 0.48) / (h / 2)) ** 2)
    v = 1 - amount * np.clip(r - 0.55, 0, 1) ** 1.6
    a = np.asarray(img, np.float32) * v[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def heavy_word(text, size, top, bottom, seed):
    """Faceted fill, thick navy outline and a stepped extrusion: reads on light or busy backgrounds."""
    f = font(TITLE_FONT, size)
    pad = int(size * 0.3)
    l, t, r, b = f.getbbox(text)
    w, h = r - l + 2 * pad, b - t + 2 * pad
    org = (pad - l, pad - t)
    stroke, depth = int(size * 0.075), int(size * 0.085)

    def mask(s=0, dx=0, dy=0):
        m = Image.new('L', (w, h), 0)
        ImageDraw.Draw(m).text((org[0] + dx, org[1] + dy), text, font=f, fill=255, stroke_width=s, stroke_fill=255)
        return m

    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    sh = mask(stroke + 6, depth + 8, depth + 14).filter(ImageFilter.GaussianBlur(size * 0.07))
    out.paste(Image.new('RGBA', (w, h), (0, 0, 0, 255)), (0, 0), sh.point(lambda v: int(v * 0.5)))
    for i in range(depth, 0, -1):
        out.paste(Image.new('RGBA', (w, h), NAVY_DEEP + (255,)), (0, 0), mask(stroke, i, i))
    out.paste(Image.new('RGBA', (w, h), (16, 28, 64, 255)), (0, 0), mask(stroke))
    face = faceted_fill((w, h), top, bottom, int(size * 0.2), seed).convert('RGBA')
    out.paste(face, (0, 0), mask())
    return out, (pad, pad, pad + r - l, pad + b - t)


def marker_arrow(img, pts, width, head):
    """A hand-drawn arrow along a quadratic curve, red ink over a white edge, tapered at the tail."""
    p0, p1, p2 = [np.array(p, float) for p in pts]
    ts = np.linspace(0, 1, 160)
    curve = [(1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2 for t in ts]
    tip = curve[-1]
    tang = curve[-1] - curve[-6]
    tang /= np.linalg.norm(tang)
    nrm = np.array([-tang[1], tang[0]])
    wing = [tip - tang * head + nrm * head * 0.62, tip, tip - tang * head - nrm * head * 0.62]
    d = ImageDraw.Draw(img)
    for col, extra in [((255, 255, 255, 255), width * 0.55), (INK_RED + (255,), 0)]:
        for i in range(1, len(curve) - 4):
            wv = (width * (0.45 + 0.55 * min(1, ts[i] * 2.2))) + extra
            a, b = curve[i - 1], curve[i]
            d.line([tuple(a), tuple(b)], fill=col, width=int(wv))
            d.ellipse([b[0] - wv / 2, b[1] - wv / 2, b[0] + wv / 2, b[1] + wv / 2], fill=col)
        lw = int(width * 0.95 + extra)
        d.line([tuple(wing[0]), tuple(wing[1])], fill=col, width=lw)
        d.line([tuple(wing[2]), tuple(wing[1])], fill=col, width=lw)
        for q in wing:
            d.ellipse([q[0] - lw / 2, q[1] - lw / 2, q[0] + lw / 2, q[1] + lw / 2], fill=col)


def rubber_stamp(text, size, rot, seed=5):
    """Red rubber-stamp ink: double border, bold letters, worn patches, slight rotation."""
    f = font(TITLE_FONT, size)
    l, t, r, b = f.getbbox(text)
    tw, th = r - l, b - t
    bx, by = int(size * 0.36), int(size * 0.26)
    w, h = tw + 2 * bx, th + 2 * by
    m = Image.new('L', (w + 40, h + 40), 0)
    d = ImageDraw.Draw(m)
    lw = int(size * 0.075)
    d.rounded_rectangle([20, 20, 20 + w, 20 + h], radius=int(size * 0.12), outline=255, width=lw)
    d.rounded_rectangle([20 + lw * 1.9, 20 + lw * 1.9, 20 + w - lw * 1.9, 20 + h - lw * 1.9], radius=int(size * 0.07), outline=255, width=max(3, lw // 3))
    d.text((20 + bx - l, 20 + by - t), text, font=f, fill=255)
    # worn ink: speckles and a few dry streaks, kept light so it still reads at thumbnail size
    rng = np.random.default_rng(seed)
    a = np.asarray(m, np.float32) / 255
    noise = ndimage.gaussian_filter(rng.random(a.shape), 2.2)
    noise = (noise - noise.min()) / (noise.max() - noise.min())
    streak = ndimage.gaussian_filter(rng.random((a.shape[0], 1)) * np.ones((1, a.shape[1])), (1.5, 0))
    wear = np.clip((noise - 0.66) * 4, 0, 1) * 0.85 + np.clip((streak - 0.8) * 5, 0, 1) * 0.35
    a = np.clip(a * (1 - wear), 0, 1)
    ink = Image.new('RGBA', m.size, INK_RED + (0,))
    ink.putalpha(Image.fromarray((a * 238).astype(np.uint8)))
    return ink.rotate(rot, resample=Image.BICUBIC, expand=True)


def make_thumbnail(render, plate, out_dir):
    img, mask = depth_of_field(Image.open(render), Image.open(plate), 16)
    img = subject_glow(img, mask, strength=0.42)
    img = ImageEnhance.Contrast(img).enhance(1.07)
    img = ImageEnhance.Color(img).enhance(1.12)
    img = vignette(img).convert('RGBA')

    # EVERY. SINGLE. EXAM. stacked in the empty ceiling, right-aligned, yellow for attention
    x_right, y = TW - 70, 120
    words = [('EVERY.', 250), ('SINGLE.', 250), ('EXAM.', 300)]
    bottoms = []
    for i, (wd, sz) in enumerate(words):
        im, ink = heavy_word(wd, sz, (255, 226, 92), (246, 160, 0), 30 + i)
        img.alpha_composite(im, (x_right - ink[2], y - ink[1]))
        bottoms.append((x_right - ink[2] + ink[0], y + ink[3] - ink[1]))
        y += ink[3] - ink[1] + int(sz * 0.2)

    # red marker arrow from the words down to the circled 100
    score = (1622, 2378)
    marker_arrow(img, [(1830, y + 10), (2075, 1720), (score[0] + 140, score[1] - 150)], 46, 120)

    # CHEATER? stamped across the lower half of the paper
    stamp = rubber_stamp('CHEATER?', 300, 9)
    cx, cy = 1360, 2720  # on the white of the paper, above his hands
    img.alpha_composite(stamp, (int(cx - stamp.size[0] / 2), int(cy - stamp.size[1] / 2)))

    out = img.convert('RGB')
    out.save(os.path.join(out_dir, 'Perfect_Score_thumbnail_2160x3840.png'), optimize=True)
    out.save(os.path.join(out_dir, 'Perfect_Score_thumbnail_2160x3840.jpg'), quality=94, subsampling=0)
    out.resize((1080, 1920), Image.LANCZOS).save(os.path.join(out_dir, 'Perfect_Score_thumbnail_1080x1920.jpg'), quality=92)
    return out


def phone_preview(thumb, out_dir):
    """How it reads in a Shorts shelf on a phone: two tiles side by side at real size."""
    W, H = 1080, 1100
    prev = Image.new('RGB', (W, H), (15, 15, 15))
    d = ImageDraw.Draw(prev)
    tile_w = 500
    tile = thumb.resize((tile_w, int(tile_w * 16 / 9)), Image.LANCZOS)
    m = Image.new('L', tile.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, tile.size[0] - 1, tile.size[1] - 1], radius=24, fill=255)
    prev.paste(tile, (26, 60), m)
    small = thumb.resize((180, 320), Image.LANCZOS)
    ms = Image.new('L', small.size, 0)
    ImageDraw.Draw(ms).rounded_rectangle([0, 0, 179, 319], radius=14, fill=255)
    prev.paste(small, (600, 60), ms)
    f = font(TITLE_FONT, 34)
    d.text((26, 970), 'Shorts shelf tile', font=f, fill=(230, 230, 230))
    d.text((600, 400), 'small grid\n(180 px wide)', font=f, fill=(230, 230, 230))
    prev.save(os.path.join(out_dir, 'preview_thumbnail_phone.png'), optimize=True)


if __name__ == '__main__':
    render, plate, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    t = make_thumbnail(render, plate, out)
    phone_preview(t, out)
