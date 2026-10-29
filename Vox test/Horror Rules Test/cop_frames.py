"""Test frames for "If A Police Officer Knocks At 3 AM... NEVER OPEN THE DOOR" in the reference look.
    python3 cop_frames.py <out dir>
"""
import math, os, random, sys
import numpy as np
import skia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from horror import *

OUT = sys.argv[1]
SKIN, SKIN_SH = '#d6a07a', '#bd8763'
NAVY, NAVY_SH = '#22304f', '#18233b'


def surface(w=W, h=H):
    s = skia.Surface(w, h); return s, s.getCanvas()


# ------------------------------------------------------------------ the officer
def cop(pen, cx, cy, s, creepy=False, look=(0, 0), lw=None, light=None):
    """Head s px tall, centred at (cx, cy); draws cap, face and uniform down to mid-chest (or lower)."""
    lw = lw or max(3.0, s * 0.012)
    P = lambda x, y: (cx + x * s, cy + y * s)
    # uniform: shoulders, collar, tie, badge, radio
    body = smooth([P(-1.25, 1.9), P(-1.18, 0.95), P(-0.75, 0.7), P(-0.2, 0.55), P(0.2, 0.55), P(0.75, 0.7), P(1.18, 0.95), P(1.25, 1.9)], True, 0.55)
    pen.shape(body, NAVY, lw)
    pen.shade(body, smooth([P(0.35, 0.5), P(1.4, 0.8), P(1.4, 2.0), P(0.6, 2.0)]), NAVY_SH)
    for sx in (-1, 1):  # shoulder patches and epaulette lines
        patch = smooth([P(sx * 0.98, 0.9), P(sx * 1.14, 0.98), P(sx * 1.12, 1.24), P(sx * 0.98, 1.3), P(sx * 0.9, 1.1)])
        pen.shape(patch, '#c9a23a', lw * 0.7)
        pen.fill(oval(*P(sx * 1.02, 1.1), s * 0.05, s * 0.07), '#1d2a4a')
        pen.line(poly([P(sx * 0.55, 0.68), P(sx * 1.0, 0.86)], False), lw * 1.6, '#141c30')
    neck = poly([P(-0.2, 0.3), P(0.2, 0.3), P(0.22, 0.66), P(-0.22, 0.66)])
    pen.shape(neck, SKIN_SH, lw)
    for sx in (-1, 1):  # collar points
        pen.shape(poly([P(0, 0.62), P(sx * 0.32, 0.5), P(sx * 0.36, 0.82)]), '#2b3b60', lw * 0.8)
    tie = poly([P(-0.06, 0.66), P(0.06, 0.66), P(0.09, 1.9), P(-0.09, 1.9)]); pen.shape(tie, '#10141f', lw * 0.8)
    pen.shape(poly([P(-0.08, 0.6), P(0.08, 0.6), P(0.06, 0.7), P(-0.06, 0.7)]), '#10141f', lw * 0.8)
    # star badge on the left chest, name tag on the right
    bx, by = P(-0.58, 1.18)
    star = [(bx + math.cos(-math.pi / 2 + i * math.pi / 5) * s * (0.16 if i % 2 == 0 else 0.075),
             by + math.sin(-math.pi / 2 + i * math.pi / 5) * s * (0.16 if i % 2 == 0 else 0.075)) for i in range(10)]
    pen.shape(poly(star), '#e2c25a', lw * 0.7); pen.fill(oval(bx, by, s * 0.045, s * 0.045), '#b08a2a')
    pen.shape(rrect(*P(0.4, 1.12), s * 0.32, s * 0.08, s * 0.015), '#d8d8dc', lw * 0.6)
    # radio on the right shoulder, coiled cord down the chest
    rx, ry = P(0.66, 0.86)
    pen.shape(rrect(rx, ry, s * 0.17, s * 0.27, s * 0.03), '#1b1b1f', lw * 0.8)
    pen.line(poly([(rx + s * 0.05, ry), (rx + s * 0.05, ry - s * 0.12)], False), lw * 1.2, '#1b1b1f')
    for i in range(7):
        y0 = ry + s * (0.27 + i * 0.06)
        pen.line(smooth([(rx + s * 0.08, y0), (rx + s * 0.14, y0 + s * 0.03), (rx + s * 0.08, y0 + s * 0.06)], False), lw * 0.9, '#1b1b1f')
    # ears
    for sx in (-1, 1): pen.shape(oval(*P(sx * 0.4, 0.02), s * 0.08, s * 0.13), SKIN_SH, lw)
    # face: a long rounded box, a bit wider at the jaw
    face = smooth([P(-0.36, -0.42), P(0.0, -0.46), P(0.36, -0.42), P(0.4, -0.1), P(0.4, 0.22), P(0.3, 0.42), P(0.0, 0.5), P(-0.3, 0.42), P(-0.4, 0.22), P(-0.4, -0.1)], True, 0.75)
    pen.fill(face, SKIN)
    pen.shade(face, smooth([P(0.18, -0.6), P(0.6, -0.6), P(0.6, 0.6), P(0.12, 0.6), P(0.26, 0.1)]), SKIN_SH)
    if light: pen.shade(face, oval(*P(-0.1, -0.2), s * 0.35, s * 0.3), light, 60)
    pen.line(face, lw)
    ex = 0.165
    if creepy:  # sunken, bruised sockets
        for sx in (-1, 1):
            pen.fill(oval(*P(sx * ex, -0.05), s * 0.17, s * 0.15), '#8a5a5a', 120)
            pen.line(smooth([P(sx * (ex - 0.13), 0.06), P(sx * ex, 0.12), P(sx * (ex + 0.13), 0.06)], False), lw * 0.8, '#5a3434', 200)
    for sx in (-1, 1):
        X, Y = P(sx * ex, -0.05)
        r = s * (0.115 if creepy else 0.1)
        pen.shape(oval(X, Y, r, r), '#f4f1ea', lw)
        px, py = X + look[0] * r * 0.4, Y + look[1] * r * 0.4
        if creepy:
            pen.glow(px, py, r * 1.4, '#ff2a1a', 90)
            pen.fill(oval(px, py, r * 0.62, r * 0.62), '#c8141a'); pen.fill(oval(px, py, r * 0.45, r * 0.45), '#ee2a22')
            pen.fill(oval(px, py, r * 0.2, r * 0.2), '#14090a')
            pen.fill(oval(px - r * 0.22, py - r * 0.25, r * 0.12, r * 0.12), '#ffffff')
        else:
            pen.fill(oval(px, py, r * 0.38, r * 0.38), '#14100e')
            pen.fill(oval(px - r * 0.14, py - r * 0.16, r * 0.11, r * 0.11), '#ffffff')
    # eyebrows: thick and arched (too happy) when creepy, flat when calm
    for sx in (-1, 1):
        if creepy:
            b = smooth([P(sx * 0.05, -0.2), P(sx * 0.14, -0.29), P(sx * 0.27, -0.27)], False)
        else:
            b = smooth([P(sx * 0.06, -0.2), P(sx * 0.16, -0.22), P(sx * 0.27, -0.2)], False)
        pen.line(b, s * 0.045, '#2a1a12')
    # nose: an L
    pen.line(poly([P(0.0, 0.0), P(0.04, 0.12), P(-0.03, 0.13)], False), lw * 1.1, '#5a3a28')
    if creepy:
        # far too wide grin: dark outline crescent, two rows of teeth with dividers, creases and flushed cheeks
        for sx in (-1, 1): pen.fill(oval(*P(sx * 0.27, 0.12), s * 0.08, s * 0.05), '#e07070', 110)
        m = smooth([P(-0.34, 0.15), P(-0.2, 0.2), P(0.0, 0.215), P(0.2, 0.2), P(0.34, 0.15), P(0.3, 0.3), P(0.15, 0.39), P(0.0, 0.41), P(-0.15, 0.39), P(-0.3, 0.3)], True, 0.8)
        pen.fill(m, '#1a0c0c')
        pen.cv.save(); pen.cv.clipPath(m, doAntiAlias=True)
        upper = smooth([P(-0.4, 0.1), P(0.4, 0.1), P(0.4, 0.29), P(0.0, 0.31), P(-0.4, 0.29)], True, 0.6)
        lower = smooth([P(-0.4, 0.315), P(0.0, 0.335), P(0.4, 0.315), P(0.4, 0.5), P(-0.4, 0.5)], True, 0.6)
        pen.fill(upper, '#f2efe6'); pen.fill(lower, '#e6e1d4')
        for i in range(-6, 7):
            x = i * 0.05
            pen.line(poly([P(x, 0.1), P(x * 1.02, 0.3)], False), lw * 0.55, '#8c8478')
            pen.line(poly([P(x + 0.025, 0.32), P(x * 1.02 + 0.025, 0.45)], False), lw * 0.55, '#8c8478')
        pen.cv.restore()
        pen.line(m, lw * 1.2)
        for sx in (-1, 1):
            pen.line(smooth([P(sx * 0.33, 0.08), P(sx * 0.39, 0.16), P(sx * 0.35, 0.27)], False), lw * 0.9, '#6a4030')
    else:
        pen.line(smooth([P(-0.1, 0.27), P(0.0, 0.285), P(0.1, 0.27)], False), lw * 1.2, '#3a2418')
    # peaked cap
    crown = smooth([P(-0.62, -0.62), P(-0.3, -0.92), P(0.3, -0.92), P(0.62, -0.62), P(0.48, -0.42), P(-0.48, -0.42)], True, 0.7)
    pen.shape(crown, '#1d2945', lw)
    pen.shade(crown, smooth([P(0.1, -1.0), P(0.8, -1.0), P(0.8, -0.3), P(0.3, -0.4)]), '#151e34')
    band = poly([P(-0.47, -0.52), P(0.47, -0.52), P(0.44, -0.4), P(-0.44, -0.4)]); pen.shape(band, '#0f1422', lw)
    for i in range(10):  # chequered band
        x = -0.43 + i * 0.087
        if i % 2 == 0: pen.fill(poly([P(x, -0.5), P(x + 0.087, -0.5), P(x + 0.085, -0.43), P(x, -0.43)]), '#e8e8ea', 220)
    visor = smooth([P(-0.46, -0.4), P(0.46, -0.4), P(0.38, -0.3), P(0.0, -0.27), P(-0.38, -0.3)], True, 0.7)
    pen.shape(visor, '#0c0d11', lw)
    pen.line(smooth([P(-0.25, -0.36), P(0.0, -0.345), P(0.22, -0.36)], False), lw * 0.8, '#5a5e6e', 180)
    bx, by = P(0.0, -0.66)
    pen.shape(poly([(bx, by - s * 0.11), (bx + s * 0.09, by - s * 0.03), (bx + s * 0.06, by + s * 0.09), (bx - s * 0.06, by + s * 0.09), (bx - s * 0.09, by - s * 0.03)]), '#e2c25a', lw * 0.7)


# ------------------------------------------------------------------ set pieces
def street_night(pen, horizon=640, police_lights=True, t_phase=0.0, seed=2):
    rnd = random.Random(seed)
    pen.grad_rect(0, 0, W, horizon, '#0a1226', '#1c2c4c')
    for _ in range(70): pen.fill(oval(rnd.uniform(0, W), rnd.uniform(0, horizon * 0.6), 1.4, 1.4), '#d8e0ff', int(rnd.uniform(60, 180)))
    pen.glow(1600, 150, 90, '#e8eeff', 110); pen.fill(oval(1600, 150, 34, 34), '#e9eef8')
    # houses across the street
    for i, x in enumerate((-60, 420, 980, 1450)):
        w, h = 430, 240
        roof = poly([(x - 20, horizon - h), (x + w / 2, horizon - h - 120), (x + w + 20, horizon - h)])
        pen.shape(roof, '#151d2e', 3)
        pen.shape(poly([(x, horizon - h), (x + w, horizon - h), (x + w, horizon), (x, horizon)]), ['#253049', '#2a2f45', '#20293f', '#2b3550'][i], 3)
        for j, wx in enumerate((x + 50, x + 290)):
            lit = (i + j) % 3 != 0
            pen.shape(rrect(wx, horizon - h + 60, 90, 80, 4), '#f2c46b' if lit else '#121a2b', 3)
            if lit: pen.glow(wx + 45, horizon - h + 100, 120, '#ffb84a', 60)
        pen.shape(rrect(x + 175, horizon - 130, 70, 130, 3), '#3a2a20', 3)
    pen.fill(poly([(0, horizon), (W, horizon), (W, horizon + 90), (0, horizon + 90)]), '#202838')
    pen.fill(poly([(0, horizon + 90), (W, horizon + 90), (W, H), (0, H)]), '#141a26')
    # street lamp
    pen.line(poly([(260, horizon + 80), (260, horizon - 300), (330, horizon - 320)], False), 10, '#0e121b')
    pen.glow(335, horizon - 300, 260, '#ffcf7a', 90); pen.fill(oval(335, horizon - 304, 24, 12), '#ffe2a2')
    if police_lights:
        # a cruiser at the kerb, its light bar flashing red and blue
        cx, cy = 1180, horizon + 70
        body = smooth([(cx - 300, cy + 40), (cx - 290, cy - 30), (cx - 160, cy - 60), (cx - 90, cy - 125), (cx + 110, cy - 125), (cx + 190, cy - 60),
                       (cx + 300, cy - 45), (cx + 310, cy + 40)], True, 0.4)
        pen.shape(body, '#e9ecf0', 4)
        pen.shade(body, poly([(cx - 320, cy - 40), (cx + 330, cy - 40), (cx + 330, cy + 60), (cx - 320, cy + 60)]), '#15171d')
        pen.shape(poly([(cx - 70, cy - 115), (cx + 95, cy - 115), (cx + 160, cy - 62), (cx - 140, cy - 62)]), '#0f141f', 3)
        for wx in (cx - 200, cx + 200):
            pen.shape(oval(wx, cy + 40, 52, 52), '#0b0c10', 4); pen.fill(oval(wx, cy + 40, 22, 22), '#6a6e78')
        pen.shape(rrect(cx - 60, cy - 145, 60, 20, 6), '#ff2a2a', 3); pen.shape(rrect(cx + 0, cy - 145, 60, 20, 6), '#2a5aff', 3)
        red, blue = (0.5 + 0.5 * math.sin(t_phase * 6)), (0.5 - 0.5 * math.sin(t_phase * 6))
        pen.glow(cx - 30, cy - 135, 520, '#ff1e2a', int(40 + 120 * red)); pen.glow(cx + 30, cy - 135, 520, '#2a5cff', int(40 + 120 * blue))


def porch(pen, light=True):
    """Front porch seen from the door: posts, rail, floor boards, overhead lamp."""
    pen.fill(poly([(0, 860), (W, 860), (W, H), (0, H)]), '#3a2a20')
    for i in range(12): pen.line(poly([(0, 870 + i * 22), (W, 870 + i * 22)], False), 3, '#2a1d16', 160)
    for x in (120, 1740):
        pen.shape(poly([(x, 0), (x + 60, 0), (x + 60, 870), (x, 870)]), '#d9d2c4', 4)
        pen.shade(poly([(x, 0), (x + 60, 0), (x + 60, 870), (x, 870)]), poly([(x + 36, 0), (x + 60, 0), (x + 60, 870), (x + 36, 870)]), '#b0a898')
    pen.shape(poly([(0, 700), (W, 700), (W, 726), (0, 726)]), '#cfc8b8', 4)
    for x in range(200, 1740, 70):
        pen.shape(poly([(x, 726), (x + 14, 726), (x + 14, 860), (x, 860)]), '#c6bfaf', 3)
    if light: pen.glow(W / 2, -60, 760, '#ffd38a', 120)


# ------------------------------------------------------------------ frames
def f_doorbell(creepy=True, ui=True):
    """Doorbell camera: the officer leans in close, porch lamp above, cruiser behind."""
    surf, cv = surface(); pen = Pen(cv)
    street_night(pen, 600, t_phase=0.3)
    porch(pen)
    cop(pen, 960, 500, 380, creepy=creepy, look=(0, 0.1), light='#ffd38a')
    pen.glow(960, 120, 600, '#ffd38a', 50)
    a = to_np(surf.makeImageSnapshot())
    a = fisheye(a, 0.42, 1.12)
    a = a * np.array([0.92, 0.98, 1.06])  # cool camera sensor
    a = finish(a, vignette=0.85, grain=9, soft=0.8, seed=3)
    img = from_np(a)
    if not ui: return img
    s2 = skia.Surface(W, H); c2 = s2.getCanvas(); c2.drawImage(img, 0, 0); p2 = Pen(c2)
    p2.fill(oval(66, 62, 11, 11), '#ff2a2a')
    text(c2, 'LIVE', 88, 72, 700, 28, '#ffffff', 235, 0.06, 'left')
    text(c2, 'FRONT DOOR', W - 50, 72, 700, 28, '#ffffff', 235, 0.08, 'right')
    text(c2, '03:00:17 AM', 54, H - 52, 600, 26, '#ffffff', 220, 0.05, 'left')
    p2.line(rrect(770, 245, 380, 440, 10), 5, '#4bff7a', 220)  # face detection box
    p2.fill(rrect(770, 208, 190, 38, 4), '#4bff7a', 225)
    text(c2, 'HUMAN 2%', 865, 236, 700, 22, '#0c1f12', 255, 0.04, 'center', False)
    p2.fill(oval(W - 72, H - 64, 24, 24), '#ffffff', 40); text(c2, 'REC', W - 110, H - 54, 700, 22, '#ff4a4a', 230, 0.08, 'right')
    return s2.makeImageSnapshot()


def f_peephole():
    surf, cv = surface(); pen = Pen(cv)
    street_night(pen, 640, t_phase=1.1)
    cop(pen, 960, 420, 300, creepy=False, look=(0, 0.05))
    pen.fill(poly([(0, 860), (W, 860), (W, H), (0, H)]), '#2a2018')
    a = peephole(to_np(surf.makeImageSnapshot()))
    a = finish(a, 0.35, 8, 0.7, 5)
    s2 = skia.Surface(W, H); c2 = s2.getCanvas(); c2.drawImage(from_np(a), 0, 0)
    header(c2, 'HOUSE RULES', 'INTRODUCTION'); caption(c2, 'You see a police officer in full uniform.')
    return s2.makeImageSnapshot()


def f_rule():
    """Rule card over the dark, dimmed hallway."""
    surf, cv = surface(); pen = Pen(cv)
    pen.grad_rect(0, 0, W, H, '#14161e', '#0c0d12')
    door = rrect(800, 220, 320, 640, 8); pen.shape(door, '#3a2c22', 5)
    pen.glow(960, 860, 300, '#ff3a2a', 50)
    for x in (880, 1040): pen.fill(rrect(x, 860, 40, 12, 3), '#ffe0b0', 120)  # light under the door, broken by two feet
    pen.fill(poly([(0, 860), (W, 860), (W, H), (0, H)]), '#0f0f14')
    # red icon on the wall: a door with a cross
    ix, iy = 210, 300
    pen.line(rrect(ix, iy, 230, 300, 6), 4, '#8a1c1c', 200)
    pen.line(rrect(ix + 70, iy + 60, 90, 180, 4), 4, '#8a1c1c', 200)
    pen.line(poly([(ix + 20, iy + 30), (ix + 210, iy + 270)], False), 6, '#c42424', 210)
    pen.line(poly([(ix + 210, iy + 30), (ix + 20, iy + 270)], False), 6, '#c42424', 210)
    text(cv, '1', ix + 205, iy + 48, 500, 54, '#8a1c1c', 200, 0, 'center', False)
    a = finish(to_np(surf.makeImageSnapshot()) * 0.55, 0.6, 6, 2.0, 7)
    s2 = skia.Surface(W, H); c2 = s2.getCanvas(); c2.drawImage(from_np(a), 0, 0); p2 = Pen(c2)
    text(c2, 'RULE', 960, 300, 600, 26, '#d8d8de', 230, 0.6)
    text(c2, '01', 960, 470, 800, 190, '#ffffff', 255, 0.0)
    p2.fill(rrect(760, 510, 400, 5, 2), '#e3202a')
    text(c2, 'DO NOT OPEN THE DOOR', 960, 580, 700, 38, '#ffffff', 245, 0.05)
    text(c2, 'FOR AN OFFICER YOU DIDN\'T CALL.', 960, 632, 700, 38, '#ffffff', 245, 0.05)
    for i in range(7): p2.fill(rrect(760 + i * 58, 700, 46, 5, 2), '#e3202a' if i == 0 else '#5a5a64', 255 if i == 0 else 160)
    header(c2, 'HOUSE RULES', 'RULE 1 OF 7')
    return s2.makeImageSnapshot()


def f_phone():
    """Living room in the dark, red and blue washing the ceiling; you dial 911."""
    surf, cv = surface(); pen = Pen(cv)
    pen.grad_rect(0, 0, W, H, '#151a26', '#0d1018')
    win = rrect(1200, 200, 460, 420, 6); pen.shape(win, '#1b2a48', 6)
    pen.line(poly([(1430, 200), (1430, 620)], False), 8, '#2a2a32'); pen.line(poly([(1200, 410), (1660, 410)], False), 8, '#2a2a32')
    pen.glow(1430, 420, 700, '#ff1e2a', 70); pen.glow(1600, 120, 800, '#2a5cff', 70)
    tv = rrect(380, 380, 560, 320, 8); pen.shape(tv, '#0a0c12', 6); pen.fill(rrect(400, 398, 520, 284, 4), '#2b3f6a'); pen.glow(660, 540, 420, '#7a9aff', 45)
    pen.fill(oval(560, 520, 50, 50), '#dfe6f4', 200); pen.fill(rrect(700, 470, 150, 120, 4), '#9aaccc', 160)
    pen.fill(poly([(0, 800), (W, 800), (W, H), (0, H)]), '#0b0d13')
    a = finish(to_np(surf.makeImageSnapshot()) * 0.75, 0.6, 6, 2.2, 9)
    s2 = skia.Surface(W, H); c2 = s2.getCanvas(); c2.drawImage(from_np(a), 0, 0); p2 = Pen(c2)
    # hand holding the phone: palm from below, thumb on the left edge, fingertips on the right edge
    ox, oy, k = 110, 300, 0.92
    Q = lambda x, y: (ox + x * k, oy + y * k)
    palm = smooth([Q(70, 900), Q(40, 640), Q(110, 560), Q(380, 560), Q(420, 700), Q(400, 900)], True, 0.6)
    p2.shape(palm, '#b9805c', 4)
    ph = rrect(*Q(110, 120), 290 * k, 560 * k, 40 * k); p2.shape(ph, '#0e1220', 6)
    p2.fill(rrect(*Q(126, 136), 258 * k, 528 * k, 30 * k), '#16203a')
    cxp = ox + 255 * k
    text(c2, 'EMERGENCY CALL', cxp, oy + 240 * k, 600, 21, '#d9e0f2', 230, 0.06)
    text(c2, '911', cxp, oy + 310 * k, 800, 60, '#ffffff', 255, 0.02)
    text(c2, '00:07', cxp, oy + 356 * k, 600, 24, '#d9e0f2', 220, 0.08)
    rnd = random.Random(4)
    for i in range(17):
        h = 6 + abs(math.sin(i * 1.7)) * 26 * rnd.uniform(0.5, 1)
        p2.fill(rrect(ox + (158 + i * 12.5) * k, oy + 420 * k - h / 2, 7, h, 3), '#7aa0ff', 230)
    for x in (190, 255, 320): p2.fill(oval(ox + x * k, oy + 500 * k, 22, 22), '#2a3554')
    p2.fill(oval(cxp, oy + 590 * k, 32, 32), '#e3202a'); p2.line(smooth([(cxp - 13, oy + 598 * k), (cxp, oy + 582 * k), (cxp + 14, oy + 594 * k)], False), 5, '#ffffff')
    p2.shape(smooth([Q(92, 600), Q(70, 480), Q(98, 420), Q(122, 470), Q(124, 600)], True, 0.6), '#b9805c', 4)  # thumb
    for y in (300, 380, 460, 540):
        p2.shape(rrect(*Q(384, y), 52 * k, 50 * k, 22 * k), '#b9805c', 4)  # fingertips
    # dispatcher chat panel
    pnl = rrect(820, 300, 600, 260, 14); p2.fill(pnl, '#0c1222', 225); p2.line(pnl, 2, '#3a4a72', 200)
    text(c2, 'DISPATCH  —  CALL 24-1187', 850, 345, 700, 20, '#8fa6d8', 230, 0.12, 'left', False)
    p2.fill(rrect(850, 365, 540, 1.5, 0), '#3a4a72')
    text(c2, 'ADDRESS:  144 ELM ST', 850, 410, 600, 26, '#ffffff', 235, 0.04, 'left', False)
    text(c2, 'UNITS NEAR YOU:  NONE', 850, 460, 700, 26, '#ff5a5a', 245, 0.04, 'left', False)
    text(c2, 'NO OFFICER WAS SENT.', 850, 510, 600, 26, '#ffffff', 220, 0.04, 'left', False)
    header(c2, 'HOUSE RULES', 'RULE 2 OF 7')
    caption(c2, '"Ma\'am, there are no officers on your street."')
    return s2.makeImageSnapshot()


def f_thumbnail(face_img):
    """Red panel with two words, white arrow, the doorbell frame boxed on the right."""
    TW, TH = 1920, 1080
    s = skia.Surface(TW, TH); cv = s.getCanvas(); pen = Pen(cv)
    cv.clear(col('#ff1f2b'))
    pen.grad_rect(0, 0, TW, TH, '#ff2a35', '#e01422')
    # right panel: crop of the doorbell frame, white border, rounded corners
    px, py, pw, ph = 1020, 0, 900, 1080
    src = skia.Rect.MakeXYWH(575, 100, 770, 930)
    clip = rrect(px + 10, py + 10, pw - 20, ph - 20, 26)
    cv.save(); cv.clipPath(clip, doAntiAlias=True)
    cv.drawImageRect(face_img, src, skia.Rect.MakeXYWH(px + 10, py + 10, pw - 20, ph - 20), skia.SamplingOptions(skia.FilterMode.kLinear))
    cv.restore()
    pen.line(clip, 14, '#ffffff')
    # words
    def big(s_, y, c, size, sh=True):
        f = font(900, size); w = f.measureText(s_)
        blob = skia.TextBlob.MakeFromString(s_, f)
        if sh: cv.drawTextBlob(blob, 500 - w / 2 + 8, y + 10, skia.Paint(Color=col('#7a0008', 150), AntiAlias=True, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10)))
        cv.drawTextBlob(blob, 500 - w / 2, y, skia.Paint(Color=col(c), AntiAlias=True))
    big('NEVER', 330, '#ffffff', 250)
    big('OPEN', 560, '#111111', 250, False)
    # the arrow: a thick white curve with a black edge, sweeping right into the face
    arrow = smooth([(300, 690), (360, 900), (620, 960), (930, 780)], False)
    for w_, c in ((64, '#111111'), (42, '#ffffff')):
        pen.line(arrow, w_, c)
    head = poly([(1010, 700), (900, 712), (958, 822)])
    pen.cv.drawPath(head, skia.Paint(Color=col('#111111'), AntiAlias=True, Style=skia.Paint.kStrokeAndFill_Style, StrokeWidth=22, StrokeJoin=skia.Paint.kRound_Join))
    pen.cv.drawPath(head, skia.Paint(Color=col('#ffffff'), AntiAlias=True))
    return s.makeImageSnapshot()


os.makedirs(OUT, exist_ok=True)
bell = f_doorbell(True)
outs = {'01_peephole': f_peephole(), '02_rule_card': f_rule(), '03_phone_911': f_phone(), '04_doorbell_cop': bell,
        '05_thumbnail': f_thumbnail(f_doorbell(True, ui=True))}
for k, im in outs.items():
    im.save(os.path.join(OUT, f'cop_{k}.png'), skia.kPNG); print('wrote', k)
