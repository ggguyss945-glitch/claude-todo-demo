#!/usr/bin/env python3
"""Contact sheet / side-by-side comparison helper for look-dev.

usage:
  sheet.py OUT.jpg H img1 img2 ...      # every image scaled to height H, one row, labelled
  sheet.py OUT.jpg H --cols N img...    # grid with N columns
Labels are the file basenames. Images are opened with PIL only (no code from the image dirs).
"""
import sys, os
from PIL import Image, ImageDraw, ImageFont

def main():
    a = sys.argv[1:]
    out, h = a[0], int(a[1]); a = a[2:]
    cols = None
    if a and a[0] == '--cols':
        cols = int(a[1]); a = a[2:]
    ims = []
    for p in a:
        im = Image.open(p).convert('RGB')
        w = round(im.width * h / im.height)
        ims.append((os.path.basename(p), im.resize((w, h), Image.LANCZOS)))
    if cols is None:
        cols = len(ims)
    rows = (len(ims) + cols - 1) // cols
    cw = max(i.width for _, i in ims)
    pad = 6
    W = cols * cw + (cols + 1) * pad
    H = rows * (h + 22) + (rows + 1) * pad
    sh = Image.new('RGB', (W, H), (24, 24, 24))
    d = ImageDraw.Draw(sh)
    try:
        f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
    except Exception:
        f = ImageFont.load_default()
    for k, (n, im) in enumerate(ims):
        r, c = divmod(k, cols)
        x = pad + c * (cw + pad); y = pad + r * (h + 22 + pad)
        d.text((x + 2, y + 2), n, fill=(230, 230, 230), font=f)
        sh.paste(im, (x, y + 22))
    sh.save(out, quality=88)

if __name__ == '__main__':
    main()
