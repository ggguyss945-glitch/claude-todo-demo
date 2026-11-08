#!/usr/bin/env python3
"""Colour statistics in the same terms as the reference analyses.

usage: stats.py img1 [img2 ...]
Prints per image: mean colour, hi (mean of top 8% by luma) / lo (bottom 8%), luma p1/p50/p99,
luma std, mean HSV saturation, R-B (mean), share of crushed pixels (L<4) and clipped (L>250).
The caption band (y 1290-1420 on a 1920-high frame) is masked out, like the analyses did.
"""
import sys
import numpy as np
from PIL import Image

def stats(p):
    im = np.asarray(Image.open(p).convert('RGB')).astype(np.float32)
    h, w, _ = im.shape
    m = np.ones((h, w), bool)
    if h >= 1900:
        m[int(h * 0.672):int(h * 0.74), :] = False
    px = im[m]
    L = 0.299 * px[:, 0] + 0.587 * px[:, 1] + 0.114 * px[:, 2]
    o = np.argsort(L)
    n = len(L); k = max(1, int(n * 0.08))
    hi = px[o[-k:]].mean(0); lo = px[o[:k]].mean(0); mean = px.mean(0)
    mx = px.max(1); mn = px.min(1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0).mean()
    hx = lambda c: '#%02x%02x%02x' % tuple(int(round(v)) for v in c)
    p1, p50, p99 = np.percentile(L, [1, 50, 99])
    return (f"mean {hx(mean)} hi {hx(hi)} lo {hx(lo)} L p1/p50/p99 {p1:.0f}/{p50:.0f}/{p99:.0f} "
            f"std {L.std():.0f} sat {sat:.2f} R-B {mean[0]-mean[2]:+.0f} "
            f"crush {100*(L<4).mean():.1f}% clip {100*(L>250).mean():.2f}%")

if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(f"{p.split('/')[-1]:34s} {stats(p)}")
