"""Locations, drawn flat in the reference look. Every function draws a full 1920x1080 design frame (or a layer of one).
Night palette: navy sky, cold street light, warm windows and porch lamp; interiors in dim warm browns with a blue cast.
"""
import math, random
from look import *
import people as P

NIGHT_TOP, NIGHT_LOW = '#0b1224', '#1d2b48'


def sky(pen, horizon, moon=(1580, 150), stars=60, seed=1):
    pen.grad(0, 0, DW, horizon, NIGHT_TOP, NIGHT_LOW)
    rnd = random.Random(seed)
    for _ in range(stars): pen.fill(oval(rnd.uniform(0, DW), rnd.uniform(0, horizon * 0.55), 1.3), '#d8e0ff', rnd.uniform(60, 170))
    if moon:
        pen.glow(*moon, 110, '#dfe7ff', 90); pen.fill(oval(*moon, 34), '#e7ecf6')
        pen.fill(oval(moon[0] + 9, moon[1] - 6, 8), '#cfd6e6'); pen.fill(oval(moon[0] - 10, moon[1] + 9, 5), '#d3d9e8')


def bare_tree(pen, x, y, h, seed=3, c='#0c111c'):
    rnd = random.Random(seed)
    def branch(x0, y0, ang, L, w, d):
        x1, y1 = x0 + math.sin(ang) * L, y0 - math.cos(ang) * L
        pen.seg((x0, y0), (x1, y1), w, c)
        if d == 0: return
        for k in (-1, 1):
            branch(x1, y1, ang + k * rnd.uniform(0.3, 0.6), L * rnd.uniform(0.6, 0.78), w * 0.65, d - 1)
    branch(x, y, 0, h * 0.4, h * 0.035, 5)


def house(pen, x, y, w, h, wall='#2a3550', roof='#161d2e', door='#5a3a28', lit=(True, False, True), porch_lamp=True, door_open=0.0, number=None, upstairs=True):
    """A front-facing house, x = left edge, y = ground."""
    lw = 3
    body = rect(x, y - h, w, h)
    pen.shape(body, wall, lw)
    for i in range(int(h / 22)):  # siding lines
        pen.seg((x, y - h + 18 + i * 22), (x + w, y - h + 18 + i * 22), 1.6, mix(wall, '#000000', 0.25), 160)
    pen.shape(poly([(x - 30, y - h), (x + w / 2, y - h - w * 0.32), (x + w + 30, y - h)]), roof, lw)
    if upstairs:
        uw = w * 0.16
        pen.shape(rect(x + w / 2 - uw / 2, y - h - w * 0.2, uw, uw * 0.9), '#f0c46c' if lit[1] else '#121a2c', lw)
        pen.seg((x + w / 2, y - h - w * 0.2), (x + w / 2, y - h - w * 0.2 + uw * 0.9), 3)
        if lit[1]: pen.glow(x + w / 2, y - h - w * 0.15, 140, '#ffb84a', 50)
    dw, dh = w * 0.15, h * 0.62
    dx = x + w / 2 - dw / 2
    pen.shape(rect(dx - 8, y - dh - 8, dw + 16, dh + 8), '#d8d2c4', lw)
    pen.shape(rect(dx, y - dh, dw, dh), door, lw)
    if door_open > 0: pen.fill(rect(dx, y - dh, dw * door_open, dh), '#f4cf86')
    pen.fill(oval(dx + dw * 0.82, y - dh * 0.48, 4), '#d9b24a')
    for k, wx in enumerate((x + w * 0.1, x + w * 0.68)):
        ww, wh = w * 0.22, h * 0.36
        on = lit[0] if k == 0 else lit[2]
        pen.shape(rect(wx, y - h * 0.72, ww, wh), '#f2c46b' if on else '#121a2b', lw)
        pen.seg((wx + ww / 2, y - h * 0.72), (wx + ww / 2, y - h * 0.72 + wh), 3); pen.seg((wx, y - h * 0.72 + wh / 2), (wx + ww, y - h * 0.72 + wh / 2), 3)
        if on: pen.glow(wx + ww / 2, y - h * 0.55, 180, '#ffb84a', 55)
    if porch_lamp:
        lx, ly = dx + dw + 22, y - dh * 0.8
        pen.glow(lx, ly, 300, '#ffd38a', 120); pen.shape(rrect(lx - 7, ly - 12, 14, 22, 3), '#ffe6b0', 2)
    if number: text(pen.cv, number, dx + dw / 2, y - dh - 22, 700, 18, '#d9b24a', 230, 0.05)
    return (dx, y - dh, dw, dh)


def patrol_car(pen, x, y, s=1.0, facing=1, lights=0.0, t=0.0, driver=None, backseat=None, glass='#0e1626'):
    """Side view; x = centre, y = ground. lights: 0 off, 1 flashing. driver/backseat: callables drawing the occupants inside the windows."""
    W_, H_ = 620 * s, 190 * s
    X = lambda u: x + u * W_ / 2 * facing
    body = smooth([(X(-1), y - H_ * 0.18), (X(-0.98), y - H_ * 0.5), (X(-0.62), y - H_ * 0.58), (X(-0.4), y - H_ * 0.95), (X(0.38), y - H_ * 0.95),
                   (X(0.6), y - H_ * 0.58), (X(0.97), y - H_ * 0.5), (X(1.0), y - H_ * 0.18)], True, 0.35)
    pen.fill(body, '#e9ecf1')
    pen.shade(body, rect(x - W_, y - H_ * 0.45, W_ * 2, H_), '#15181f')            # black lower half (black & white livery)
    pen.shade(body, rect(x - W_, y - H_ * 0.62, W_ * 2, H_ * 0.06), '#2a3a7a')
    pen.line(body, 3)
    win = [(X(-0.55), y - H_ * 0.6), (X(-0.37), y - H_ * 0.9), (X(0.34), y - H_ * 0.9), (X(0.52), y - H_ * 0.6)]
    wp = poly(win); pen.fill(wp, glass)
    pen.cv.save(); pen.cv.clipPath(wp, doAntiAlias=True)
    if backseat: backseat(X(-0.18), y - H_ * 0.55)
    if driver: driver(X(0.26), y - H_ * 0.55)
    pen.fill(poly([(X(-0.4), y - H_ * 0.9), (X(-0.2), y - H_ * 0.9), (X(-0.5), y - H_ * 0.6), (X(-0.62), y - H_ * 0.6)]), '#ffffff', 22)
    pen.cv.restore()
    pen.line(wp, 3); pen.seg((X(0.05), y - H_ * 0.9), (X(0.05), y - H_ * 0.45), 4)
    for u in (-0.62, 0.62):
        pen.shape(oval(X(u), y - H_ * 0.1, H_ * 0.2), '#0b0c10', 3); pen.fill(oval(X(u), y - H_ * 0.1, H_ * 0.09), '#6a6e78')
    text(pen.cv, 'POLICE', X(-0.1), y - H_ * 0.3, 800, int(30 * s), '#e9ecf1', 230, 0.12)
    bar = rrect(X(-0.18) - 60 * s, y - H_ * 1.03, 140 * s, 16 * s, 5); pen.shape(bar, '#2a2d36', 2)
    if lights > 0:
        red, blue = 0.5 + 0.5 * math.sin(t * 9), 0.5 - 0.5 * math.sin(t * 9)
        pen.fill(rrect(X(-0.18) - 58 * s, y - H_ * 1.03, 68 * s, 16 * s, 5), '#ff2a2a', 120 + 135 * red)
        pen.fill(rrect(X(-0.18) + 12 * s, y - H_ * 1.03, 68 * s, 16 * s, 5), '#2a5cff', 120 + 135 * blue)
        pen.glow(X(-0.18), y - H_, 500 * s, '#ff1e2a', 90 * red * lights); pen.glow(X(-0.18), y - H_, 500 * s, '#2a5cff', 90 * blue * lights)


def street(pen, horizon=560, houses=True, car=None, seed=2, trees=True):
    """Across the street: houses, a lamp post, the kerb. car: dict for patrol_car or None."""
    sky(pen, horizon, seed=seed)
    if trees:
        bare_tree(pen, 120, horizon, 520, 5); bare_tree(pen, 1830, horizon + 10, 460, 9)
    if houses:
        for i, (x, w, c, lit) in enumerate([(-80, 470, '#253049', (True, False, False)), (480, 430, '#2c3045', (False, True, True)), (1010, 470, '#212a40', (True, False, True)),
                                            (1560, 440, '#2b3550', (False, False, True))]):
            house(pen, x, horizon, w, 230, c, '#131a2a', '#3a2a20', lit, porch_lamp=(i == 2), upstairs=i % 2 == 0)
    pen.fill(rect(0, horizon, DW, 70), '#252d3c')                           # far pavement
    pen.fill(rect(0, horizon + 70, DW, 200), '#1a202b')                     # road
    for i in range(8): pen.fill(rect(i * 280 + 40, horizon + 160, 140, 8), '#6a6450', 160)
    pen.fill(rect(0, horizon + 270, DW, 30), '#3a404c')                     # kerb
    pen.line(poly([(0, horizon + 270), (DW, horizon + 270)], False), 3)
    lx = 300
    pen.seg((lx, horizon + 70), (lx, horizon - 330), 10, '#0e121b'); pen.seg((lx, horizon - 330), (lx + 70, horizon - 345), 8, '#0e121b')
    pen.glow(lx + 72, horizon - 330, 300, '#ffcf7a', 80); pen.fill(oval(lx + 72, horizon - 334, 22, 10), '#ffe2a2')
    if car: patrol_car(pen, **car)


def porch_frame(pen, light=1.0, floor_y=900):
    """What surrounds a figure on your porch, seen from the door: boards, posts, rail, the lamp above."""
    pen.fill(rect(0, floor_y, DW, DH - floor_y), '#3b2b21')
    for i in range(10): pen.seg((0, floor_y + 10 + i * 20), (DW, floor_y + 10 + i * 20), 2.5, '#2a1d16', 170)
    for x in (70, 1790):
        post = rect(x, 0, 60, floor_y); pen.shape(post, '#d6cfc0', 3); pen.shade(post, rect(x + 36, 0, 30, floor_y), '#aaa293')
    pen.shape(rect(0, floor_y - 170, DW, 22), '#cfc8b8', 3)
    for x in range(160, 1790, 64): pen.shape(rect(x, floor_y - 148, 13, 148), '#c6bfaf', 2.5)
    if light: pen.glow(DW / 2, -80, 820, '#ffd38a', 110 * light)


def hallway(pen, coat=True, lamp=True, door_light=0.6, photo=True, red=0.0, blue=0.0):
    """Inside, facing the front door: deadbolt, peephole, mail slot, coat hook to the left, framed photo to the right."""
    pen.grad(0, 0, DW, DH, '#2a2622', '#1a1715')
    pen.fill(rect(0, 0, DW, 120), '#1d1a18')
    pen.fill(rect(0, 840, DW, 240), '#2a1f19')
    for i in range(6): pen.seg((0, 860 + i * 38), (DW, 860 + i * 38), 2, '#20170f', 160)
    pen.shape(poly([(560, 1080), (700, 860), (1220, 860), (1360, 1080)]), '#4a2a26', 3)     # runner rug
    # door and frame
    pen.shape(rect(700, 160, 520, 700), '#d4ccbd', 4)
    door = rect(740, 200, 440, 660); pen.shape(door, '#5d3c28', 4)
    for (x, y, w, h) in ((790, 250, 150, 250), (980, 250, 150, 250), (790, 560, 150, 250), (980, 560, 150, 250)):
        pen.line(rect(x, y, w, h), 3, '#3e2718')
    pen.shade(door, rect(1100, 200, 100, 660), '#4d3020')
    pen.fill(oval(960, 330, 9), '#0d0d0f'); pen.line(oval(960, 330, 14), 3, '#c9a24a')                 # peephole
    pen.shape(rrect(1110, 470, 36, 70, 6), '#c9a24a', 3); pen.fill(oval(1128, 505, 8), '#3a2a10')       # deadbolt
    pen.shape(oval(1120, 575, 16), '#c9a24a', 3)                                                        # knob
    pen.shape(rrect(880, 640, 160, 34, 4), '#b8933e', 3); pen.fill(rect(892, 652, 136, 10), '#2a1a0c')  # mail slot
    if door_light: pen.fill(rect(740, 856, 440, 6), '#ffd38a', 200 * door_light); pen.glow(960, 870, 260, '#ffd38a', 80 * door_light)
    # coat hook (left)
    pen.shape(rrect(470, 300, 140, 26, 4), '#3a2a1e', 3); pen.shape(smooth([(540, 326), (540, 352), (556, 362)], False), '#c9a24a', 4)
    if coat:
        c = smooth([(500, 345), (580, 345), (618, 450), (630, 700), (450, 700), (462, 450)], True, 0.5)
        pen.shape(c, '#8a8d93', 3); pen.shade(c, rect(560, 300, 100, 420), '#74777e')
        pen.seg((540, 350), (540, 690), 2, '#5a5d63')
    # framed photograph (right)
    if photo:
        pen.shape(rect(1340, 330, 190, 150), '#3a2a1e', 4); pen.fill(rect(1356, 346, 158, 118), '#b7a58a')
        pen.fill(oval(1410, 400, 20), '#7a5a46'); pen.fill(rect(1394, 418, 32, 46), '#5a6a8a'); pen.fill(oval(1460, 392, 26), '#8a6a52'); pen.fill(rect(1440, 416, 40, 48), '#7a4a4a')
    # side table and lamp
    pen.shape(rect(1300, 620, 260, 24), '#3a2a1e', 3); pen.shape(rect(1320, 644, 14, 200), '#2c2017', 3); pen.shape(rect(1526, 644, 14, 200), '#2c2017', 3)
    if lamp:
        pen.shape(poly([(1390, 520), (1470, 520), (1490, 600), (1370, 600)]), '#e8d6b0', 3); pen.shape(rect(1424, 600, 12, 22), '#2c2017', 3)
        pen.glow(1430, 560, 520, '#ffcb7a', 70)
    if red: pen.wash('#ff1e2a', 60 * red)
    if blue: pen.wash('#2a5cff', 60 * blue)
    pen.wash('#0a1430', 40)


def lock_close(pen, hand=0.0, key=0.0):
    """Close on the deadbolt; your hand drifts toward it (hand 0..1)."""
    pen.fill(rect(0, 0, DW, DH), '#5d3c28')
    for i in range(14): pen.seg((0, 30 + i * 80), (DW, 30 + i * 80 + 6), 2, '#4e3222', 120)
    pen.shape(rrect(820, 300, 280, 480, 30), '#c9a24a', 6); pen.fill(oval(960, 450, 70), '#a8822e'); pen.shape(oval(960, 450, 48), '#d9b24a', 4)
    pen.shape(rrect(935, 410, 50, 140, 12), '#b8933e', 4)
    pen.fill(oval(960, 660, 50), '#3a2a10'); pen.fill(rect(948, 660, 24, 60), '#3a2a10')
    if hand:   # your hand comes in from the right: sleeve, palm, four fingers curling toward the bolt
        x = lerp(2000, 1150, ease(hand))
        pen.shape(rect(x + 230, 500, 900, 360), '#30333b', 4)
        palm = rrect(x + 40, 520, 230, 300, 90); pen.shape(palm, '#d9ab8c', 4)
        for k in range(4): pen.shape(rrect(x - 90 + k * 8, 540 + k * 64, 170, 52, 26), '#d9ab8c', 4)
        pen.shape(rrect(x + 60, 440, 70, 150, 34), '#cf9f82', 4)
    if key:
        kx = lerp(-300, 640, ease(key))
        pen.shape(rrect(kx, 640, 260, 40, 10), '#b9bcc4', 4); pen.shape(oval(kx - 30, 660, 60), '#b9bcc4', 4); pen.fill(oval(kx - 30, 660, 24), '#5d3c28')


def car_window(pen, man='lowered', t=0.0, card=0.0, hand=0.0, look_up=0.0, lips=0.0):
    """Close on the patrol car's rear window at night; the man in the back seat in your clothes."""
    pen.grad(0, 0, DW, DH, '#0c1324', '#141c2e')
    body = rect(-50, 760, DW + 100, 400); pen.shape(body, '#15181f', 4)
    pen.shape(rect(-50, 700, DW + 100, 60), '#e9ecf1', 4)
    frame = poly([(160, 700), (380, 140), (1560, 140), (1780, 700)]); pen.shape(frame, '#e9ecf1', 5)
    glass = poly([(210, 690), (410, 175), (1520, 175), (1730, 690)]); pen.fill(glass, '#0e1626')
    pen.cv.save(); pen.cv.clipPath(glass, doAntiAlias=True)
    pen.fill(rect(0, 0, DW, DH), '#101a2c')
    pen.shape(rrect(500, 330, 920, 520, 60), '#1b2230', 3)                  # seat back
    y = 940 if man == 'lowered' else 900
    lift = look_up * 40
    P.draw(pen, P.DOUBLE, 960, 1500 - lift, 1350, P.pose(head=(0, 0.3 * (1 - look_up)), look=(0, 1.0 * (1 - look_up) - 0.3 * look_up), expr='tired' if (man == 'lowered' and look_up < 0.5) else 'neutral',
                                                         talk=lips, arms=('down', 'down')))
    if card:
        cx, cy = 1180, lerp(1100, 470, ease(card))
        pen.shape(rrect(cx - 170, cy - 105, 340, 210, 14), '#e8edf2', 4)
        pen.fill(poly([(cx + 170, cy - 105), (cx + 120, cy - 105), (cx + 170, cy - 60)]), '#101a2c')      # the broken corner
        pen.fill(rect(cx - 150, cy - 85, 300, 30), '#3a5a9a'); pen.fill(rect(cx - 150, cy - 40, 110, 120), '#c8ccd4')
        for i in range(4): pen.fill(rect(cx - 25, cy - 35 + i * 28, 160, 10), '#a0a6b2')
    if hand:
        hx, hy = 1250, lerp(1100, 420, ease(hand))
        palm = oval(hx, hy, 90, 110); pen.shape(palm, '#e2b89a', 4)
        for k, a in enumerate((-0.55, -0.2, 0.12, 0.42)):
            pen.shape(rrect(hx + math.sin(a) * 120 - 22, hy - 150 - abs(a) * 10, 44, 130, 22), '#e2b89a', 4)
        pen.shape(rrect(hx - 150, hy - 10, 90, 44, 20), '#e2b89a', 4)
        pen.fill(oval(hx, hy, 80, 100), '#ffffff', 30)                     # pressed against the glass
    pen.fill(poly([(410, 175), (700, 175), (420, 690), (210, 690)]), '#ffffff', 18)
    pen.cv.restore(); pen.line(glass, 4)
    pen.glow(1900, 0, 900, '#ffcf7a', 50)


def hands_lap(pen, t):
    """The back-seat man's hands in his lap; his right thumb keeps rubbing the base of his ring finger."""
    pen.grad(0, 0, DW, DH, '#151b2a', '#0e121c')
    pen.shape(rect(-20, 520, DW + 40, 600), '#2b2e36', 4)                         # trousers
    for sx in (-1, 1):                                                           # coat fronts falling either side
        pen.shape(poly([(960 + sx * 260, 300), (960 + sx * 1100, 300), (960 + sx * 1100, 1100), (960 + sx * 380, 1100)]), '#8a8d93', 4)
    sk, sks = '#d9ab8c', '#c29274'
    # left hand lying flat, fingers to the right
    pen.shape(rrect(620, 560, 330, 230, 90), sk, 4)
    for k in range(4):
        y = 575 + k * 52
        pen.shape(rrect(900, y, 230 - abs(k - 1.5) * 26, 46, 23), sk if k != 2 else sks, 4)
    pen.fill(rrect(930, 575 + 2 * 52 + 4, 24, 38, 6), '#d9b24a'); pen.line(rrect(930, 579 + 2 * 52, 24, 38, 6), 2.5, '#8a6a1a')   # ring
    # right hand resting on top, thumb sliding back and forth over the ring finger
    rub = 26 * math.sin(t * 6.0)
    pen.shape(rrect(700, 760, 360, 220, 100), sks, 4)
    for k in range(4): pen.shape(rrect(1010, 770 + k * 48, 170 - abs(k - 1.5) * 20, 44, 22), sks, 4)
    thumb = smooth([(860, 780), (930 + rub, 700), (985 + rub, 690), (995 + rub, 730), (930 + rub, 790)], True, 0.7)
    pen.shape(thumb, sk, 4)
    pen.shape(rect(260, 600, 380, 220), '#7a7d84', 4); pen.shape(rect(330, 800, 400, 220), '#74777e', 4)   # cuffs
    pen.glow(1500, -100, 900, '#ffcf7a', 50)


def license_card(pen, x, y, s=1.0, broken=True, name='', tilt=0.0):
    pen.cv.save(); pen.cv.translate(x, y); pen.cv.rotate(tilt); pen.cv.scale(s, s)
    card = poly([(-300, -190), (300, -190), (300, 190), (-300, 190)])
    if broken: card = poly([(-300, -190), (215, -190), (300, -118), (300, 190), (-300, 190)])
    pen.shape(card, '#eef1f4', 5)
    pen.fill(inter(card, rect(-300, -190, 600, 70)), '#3a5a9a')
    text(pen.cv, 'DRIVER LICENSE', -270, -140, 800, 30, '#ffffff', 240, 0.08, 'left')
    pen.shape(rrect(-270, -95, 190, 240, 8), '#c8ccd4', 3); pen.fill(oval(-175, -10, 50), '#9aa0ac'); pen.fill(rrect(-240, 50, 130, 90, 30), '#9aa0ac')
    for i in range(5): pen.fill(rrect(-50, -90 + i * 45, 300 - i * 30, 14, 6), '#a7adb8')
    if name: text(pen.cv, name, -50, 150, 700, 26, '#2a3550', 230, 0.04, 'left')
    pen.cv.restore()


def holding_card(pen, t, hand_y=780):
    pen.grad(0, 0, DW, DH, '#2a2622', '#16130f')
    pen.wash('#0a1430', 40)
    license_card(pen, 980, 470, 1.25, True, 'YOU', -0.04)
    hand = smooth([(520, 1120), (560, 700), (700, 640), (820, 700), (840, 1120)], True, 0.6); pen.shape(hand, '#d9ab8c', 4)
    pen.shape(rrect(700, 560, 90, 170, 40), '#d9ab8c', 4)                  # thumb over the card
    pen.shape(rect(450, 900, 520, 300), '#30333b', 4)                      # sleeve


def kitchen(pen):
    pen.fill(rect(0, 0, DW, DH), '#20263a')
    for r in range(9):
        for c in range(17):
            x, y = c * 118 - (r % 2) * 59, r * 82
            pen.shape(rrect(x + 4, y + 4, 110, 74, 6), '#2f6ab0' if (r + c) % 5 else '#2a5fa0', 2.5, '#16243a')
    pen.shape(rect(0, 760, DW, 60), '#c9c2b2', 4); pen.shape(rect(0, 820, DW, 260), '#5a4636', 4)
    for x in range(120, DW, 420): pen.shape(rect(x, 860, 360, 190), '#6a5442', 3); pen.fill(rrect(x + 160, 940, 40, 12, 5), '#c9a24a')
    pen.glow(960, 200, 900, '#ffd8a0', 50); pen.wash('#0a1430', 50)


def photograph(pen, t):
    """The framed photo in your hallway: a child and a woman, taken by your father."""
    pen.grad(0, 0, DW, DH, '#2a2622', '#1d1916')
    for i in range(10): pen.seg((i * 200, 0), (i * 200, DH), 2, '#24201c', 120)
    fr = rect(560, 170, 800, 640); pen.shape(fr, '#3a2a1e', 6); pen.fill(rect(600, 210, 720, 560), '#e8dcc4')
    pic = rect(640, 250, 640, 480)
    pen.grad(640, 250, 1280, 730, '#9ab4c8', '#c8b48a', path=pic)
    pen.cv.save(); pen.cv.clipPath(pic, doAntiAlias=True)
    pen.fill(rect(640, 600, 640, 140), '#7a9a5a')
    P.draw(pen, P.MUM | {'hair': ('curly', '#5a3a26')}, 820, 760, 520, P.pose(expr='neutral'))
    P.draw(pen, P.YOU | {'outfit': 'hoodie'}, 1060, 760, 330, P.pose(expr='neutral'))
    pen.cv.restore(); pen.line(pic, 3)
    pen.glow(960, 480, 700, '#ffcb7a', 40); pen.wash('#0a1430', 45)


def table_grip(pen, t):
    pen.grad(0, 0, DW, DH, '#1f1b18', '#14110f')
    pen.shape(rect(0, 600, DW, 120), '#4a3424', 5); pen.shape(rect(0, 720, DW, 360), '#2a1d14', 4)
    squeeze = 0.5 + 0.5 * math.sin(t * 3)
    hand = smooth([(800, 480), (1120, 460), (1180, 640), (1160, 760), (820, 780), (760, 620)], True, 0.7); pen.shape(hand, '#d9ab8c', 4)
    for k in range(4):
        x = 860 + k * 80
        pen.shape(rrect(x, 640 + squeeze * 6, 64, 130, 30), '#cf9f82', 4)
    pen.shape(rect(500, 380, 420, 260), '#30333b', 4)
    pen.wash('#0a1430', 40)


def coat_hook(pen, empty=True):
    pen.grad(0, 0, DW, DH, '#2a2622', '#1a1715')
    pen.shape(rect(600, 260, 720, 60), '#3a2a1e', 5)
    for x in (760, 960, 1160): pen.shape(smooth([(x, 320), (x, 380), (x + 30, 400)], False), '#c9a24a', 8)
    if not empty:
        c = smooth([(900, 380), (1020, 380), (1080, 560), (1100, 980), (820, 980), (840, 560)], True, 0.5); pen.shape(c, '#8a8d93', 4)
    pen.shape(rect(1340, 160, 60, 900), '#d4ccbd', 4)                    # the door frame at the edge
    pen.glow(1600, 500, 700, '#ffd38a', 40); pen.wash('#0a1430', 45)


def mother_exterior(pen, t, knock=False, people=True, curtain=0.0):
    sky(pen, 600, moon=(300, 130), seed=7)
    bare_tree(pen, 1650, 600, 560, 12)
    pen.fill(rect(0, 600, DW, 480), '#16202a')
    d = house(pen, 460, 860, 1000, 380, '#3a3044', '#1c1622', '#4a2a2a', (False, False, True), porch_lamp=True, upstairs=False)
    pen.fill(poly([(860, 1080), (920, 860), (1000, 860), (1060, 1080)]), '#3a404c')
    if curtain:   # the curtain on the right window is pulled aside: her face in the gap
        wx, wy = 460 + 1000 * 0.68, 860 - 380 * 0.72
        pen.fill(rect(wx + 10, wy + 10, 60 * curtain, 116), '#3a2a20')
        P.draw(pen, P.MUM, wx + 70, wy + 300, 280, P.pose(expr='scared', look=(-0.5, 0.2)))
    if people:
        P.draw(pen, P.COP, d[0] - 120, 870, 300, P.pose(arms=('down', 'down'), look=(0.5, 0)))
        P.draw(pen, P.DOUBLE, d[0] + d[2] / 2, 870, 290, P.pose(expr='sad', arms=('up' if knock and int(t * 3) % 2 else 'down', 'down')))
    pen.wash('#0a1430', 30)


def mother_room(pen, t, tv=True, curtain=0.0, phone_up=True, expr='worried', tears=0.0, look=(0.6, 0)):
    pen.grad(0, 0, DW, DH, '#2e2630', '#1c171d')
    pen.fill(rect(0, 820, DW, 260), '#3a2c26')
    win = rect(1200, 180, 520, 480); pen.shape(win, '#141c30', 6)
    pen.seg((1460, 180), (1460, 660), 6); pen.seg((1200, 420), (1720, 420), 6)
    pen.shape(rect(1160, 150, 600, 20), '#8a7a62', 4)
    for k in range(9): pen.line(oval(1180 + k * 70 + curtain * 60, 160, 10), 3, '#c9a24a')
    pen.shape(rect(1160 + curtain * 250, 165, 300 - curtain * 120, 560), '#7a3a3a', 4)
    pen.shape(rect(1460 + curtain * 120, 165, 300, 560), '#7a3a3a', 4)
    pen.shape(rect(160, 420, 420, 260), '#0c0d12', 6)
    if tv: pen.fill(rect(176, 436, 388, 228), '#4a6a9a'); pen.glow(370, 550, 500, '#8aa8ff', 60)
    pen.shape(rect(200, 680, 340, 140), '#3a2a1e', 4)
    P.draw(pen, P.MUM, 860, 1220, 1050, P.pose(expr=expr, tears=tears, look=look, arms=('down', 'chest' if phone_up else 'down')))
    if phone_up: pen.shape(rrect(950, 360, 46, 100, 8), '#16181e', 3)
    pen.glow(960, 300, 800, '#ffcb7a', 40); pen.wash('#0a1430', 35)
