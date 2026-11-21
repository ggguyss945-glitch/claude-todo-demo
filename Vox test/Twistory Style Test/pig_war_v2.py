"""The Pig War (1859) in the reference channel's cartoon style, three 1920x1080 frames.
    python3 pig_war_v2.py <fonts dir> <out dir>
"""
import math, os, random, sys
import skia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rock import *

FONTS, OUT = sys.argv[1], sys.argv[2]
W, H = 1920, 1080
CAP = os.path.join(FONTS, 'Fredoka-Bold.ttf')


def new(): s = skia.Surface(W, H); return s, s.getCanvas()


def landscape(pen, horizon=640, seed=1):
    """Painted backdrop: sky, the Olympic mountains across the strait, the sea, a meadow."""
    sky(pen, W, horizon, seed=seed, clouds=5)
    rnd = random.Random(seed)
    m = [(0, horizon - 40)]
    for i in range(1, 13):
        m.append((i * W / 12, horizon - 60 - rnd.uniform(20, 150) * (1 if i % 2 else 0.5)))
    m += [(W, horizon - 30), (W, horizon), (0, horizon)]
    mt = poly(m); pen.fill(mt, '#8aa6c8'); pen.cel(mt, poly([(0, horizon - 70), (W, horizon - 80), (W, horizon), (0, horizon)]), '#7894ba')
    pen.ink(mt, pen.lw * 0.6)
    pen.fill(poly([(0, horizon - 10), (W, horizon - 10), (W, horizon + 60), (0, horizon + 60)]), '#3d8fd0')
    for i in range(14):
        x = rnd.uniform(0, W); pen.brush([(x, horizon + 18 + i % 3 * 12), (x + 60, horizon + 18 + i % 3 * 12)], pen.lw * 0.4, (0.3, 0.3), '#d8f0ff')
    mead = smooth([(-60, horizon + 40), (500, horizon + 10), (1100, horizon + 30), (1980, horizon - 5), (1980, H + 60), (-60, H + 60)], True, 0.6)
    pen.fill(mead, '#86c64a'); pen.cel(mead, poly([(0, horizon + 140), (W, horizon + 120), (W, H), (0, H)]), '#74b33e'); pen.ink(mead, pen.lw * 0.8)
    for _ in range(140):
        x, y = rnd.uniform(0, W), rnd.uniform(horizon + 60, H)
        pen.brush([(x, y), (x + rnd.uniform(-4, 4), y - rnd.uniform(12, 26))], pen.lw * 0.35, (0.2, 0.6), '#5a9a34')


# ---------------------------------------------------------------- 1: close-up, Captain Pickett
def frame1():
    surf, cv = new(); pen = Pen(cv, 9)
    landscape(pen, 600, seed=4)
    bush(pen, 180, 820, 170, 21); bush(pen, 1820, 860, 150, 22)
    s = 520
    face = Face('light', 'angry', look=(0.35, 0.05), moustache='#4a2e1c', hair='#3a2414', hair_style='long',
                hat=Hat('#2d4479', 'kepi'))
    def coat(pen, P, s, flip, torso):
        for i in range(4): pen.shape(oval(*P([(0.05, 0.25 + i * 0.22)])[0], 0.035 * s, 0.035 * s), '#e5b63e', pen.lw * 0.6)
        for x in (-0.24, 0.26):  # shoulder straps
            st = poly(P([(x - 0.1, 0.02), (x + 0.1, 0.0), (x + 0.12, 0.09), (x - 0.1, 0.11)])); pen.shape(st, '#e5b63e', pen.lw * 0.7)
    figure(pen, 1240, 1080 + s * 0.95, s, face, '#2f4c88', flip=-1, collar='#2f4c88', details=coat, legs=False)
    caption(cv, 'CAPTAIN GEORGE PICKETT', 60, 1030, 70, CAP, align='left')
    return surf.makeImageSnapshot()


os.makedirs(OUT, exist_ok=True)
for name, fn in [('v2_01_pickett', frame1)]:
    fn().save(os.path.join(OUT, name + '.png'), skia.kPNG); print('wrote', name)
