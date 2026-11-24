"""sets_buttons.py: the sets of "If Your Mom's Eyes Turn Into Buttons... DON'T KEEP HER SECRET" (Night Policy).

Run inside sets.py's namespace at import, after sets_walls.py (it reuses the set engine: BView cameras on a plan in metres,
per-face light maps, Room / Piece / build_view, BuBox rooms, Door, bu_bed_parts, the Doctor film's streetlight, the Ice
film's snowbanks and sky). Every new name starts with bt_ / BT_ / _bt.  import sets as ST;  sp = ST.bt_apt('wide').
BT_API lists every builder's views; BT_INSERTS every insert (with notes). SETS.md has the short guide.

ONE GEOGRAPHY (metres: x = east, y = north, Y = up; the building's street front is y 0, the street to the south):
  OUR BLOCK: a three-storey brick building (x -9 .. 12, front y 0), the LOBBY BAY projecting from it (x 3 .. 7, y -2.6 .. 0,
  one storey) with its GLASS DOOR on its west face (x 3.0, y -2.1 .. -0.9); the sidewalk to our kerb (y -4.8), the
  street (road Y -0.15) to the far kerb (y -12.8), the facades across (y -16): BARLOW'S on the corner (x -13.5 .. -3.5:
  its display window with the red coat), a side street, more shops east. The STREETLIGHT (x -1.2, y -4.4) stands right
  in front of Owen's window, the BUS STOP sign beside it (x 1.6). Ground Y 0.
  THE APARTMENT (second floor, floor Y BT_UP = 3.4, ceiling 2.5 above it): OWEN'S ROOM front-west (x -3.6 .. 0, y 0 .. 3.6:
  the window on the street over the streetlight with a deep window seat, the bed on the east wall, the closet on the
  west wall with the Brave List inside its door, the desk); the KITCHEN + LIVING ROOM, one room (x 0 .. 7.6, y 0 .. 5.2):
  living west (the couch facing the FRONT DOOR on the west wall, Owen's door beside it, the living window), kitchen east
  (the table under the pendant lamp, Mom's laptop at the west end, the counter along the east wall with the stove and its
  oven clock and the black MICROWAVE, the fridge on the back wall with the whiteboard and the dark GAP beside it (x
  5.1 .. 5.55) where the creepy form unfolds, MOM'S BEDROOM DOOR on the back wall, the kitchen window with the BUTTON JAR on
  its sill). From Owen's window: the streetlight, the bus stop, Barlow's corner; down-left: the lobby door.
  THE SCHOOL (its own plan): Linden Park Elementary, the snowy pickup lane (one-way east, kerb on the north at y 0), the
  silver car at the kerb (driver side to the kerb, driver window OPEN, dented rear bumper), Mr. Dunn's crossing post.
  NOW (its own plan): the narrator's desk (jar, headset, laptop), the hall, his son's room (window onto a streetlight).
Staging data as every film: sp.anchors[name] -> Spot (.x .y design px, .depth, .ppm, .X .Yp .Y plan, .turn, .seat_y).
Figures seen THROUGH a window (the street outside): order ORDER_OUT - 1 (sp.info['out_order']).
NIGHT RULE: the frame is dark, the subject lit (the streetlight through the windows, the laptop, the tablet, the pendant
lamp, the lobby glow, the shop window, headlights).
"""
import math
import numpy as np
import skia

# ====================================================================================================== plan
BT_G = 0.0
BT_ROAD = -0.15
BT_UP = 3.4                            # the apartment floor (second storey)
BT_CEIL = 2.5
BT_KERB, BT_KERB_F, BT_FAR = -4.8, -12.8, -16.0
BT_BLD = (-9.0, 12.0, 0.0, 14.0)
BT_BLD_H = 10.6
BT_BAY = (3.0, 7.0, -2.6, 0.0)         # the lobby bay
BT_BAY_H = 3.1
BT_GDOOR = (-2.1, -0.9, 2.3)           # the glass lobby door on the bay's west face x 3.0 (y0, y1, h)
BT_LAMP = (-1.2, -4.4)                 # the streetlight (its arm reaches 1.6 m over the street)
BT_LAMP_H = 6.4
BT_STOP = (1.6, -4.45)                 # the bus stop sign; its bench at (2.9, -3.7)
BT_BARLOW = (-13.5, -3.5, -24.0, -16.0)
BT_BWIN = (-9.4, -5.2, 0.5, 2.6)       # Barlow's display window (x0, x1, sill Y, top Y)
BT_BDOOR = (-4.7, -3.9, 2.3)
BT_COAT_AT = (-7.3, -16.45)            # the child mannequin in the red coat, just behind the glass
# the facade windows on our floor (x0, x1): 'next' = the window next to Owen's (a neighbour's)
BT_FWIN = {'next': (-5.4, -4.2), 'owen': (-2.3, -1.1), 'living': (1.15, 2.55), 'kitchen': (4.75, 6.05), 'e1': (8.0, 9.2), 'e2': (10.4, 11.6)}
# the apartment (floor Y BT_UP)
BT_OWEN = (-3.6, 0.0, 0.0, 3.6)
BT_MAIN = (0.0, 7.6, 0.0, 5.2)
BT_OWIN = (-2.3, -1.1, 0.72, 2.1)      # Owen's window on y 0 (x0, x1, sill, top above the floor)
BT_SEAT = Box(-1.7, 0.17, 1.4, 0.34, BT_UP, BT_UP + 0.62, 0)     # the window seat under it
BT_OBED = Box(-0.52, 1.1, 0.95, 1.95, BT_UP, BT_UP + 0.5, 180)  # Owen's bed on the east wall, head at the front
BT_CLOSET = (1.2, 2.05, 2.05)          # the closet door on x -3.6 (y0 hinge, y1, h); the closet x -4.3 .. -3.6
BT_ODOOR = (2.55, 3.4, 2.05)           # Owen's door on x 0 (y0 latch, y1 hinge, h)
BT_FDOOR = (4.15, 5.05, 2.08)          # the front door on x 0 (y0 latch, y1 hinge, h)
BT_MDOOR = (3.05, 3.9, 2.05)           # Mom's bedroom door on y 5.2 (x0 hinge, x1)
BT_LWIN = (1.15, 2.55, 0.85, 2.1)
BT_KWIN = (4.75, 6.05, 0.95, 2.1)
BT_JAR = (5.05, 0.1)                   # the button jar on the kitchen sill board (x, y; Y = BT_UP + 0.95)
BT_TABLE = Box(4.6, 2.35, 1.3, 0.84, BT_UP, BT_UP + 0.75, 0)
BT_LAMPP = (4.05, 2.35)                # the pendant lamp over the table's west end, by Mom's chair (its shade bottom 1.52 above the floor)
BT_FRIDGE = Box(5.95, 4.82, 0.8, 0.74, BT_UP, BT_UP + 1.82, 0)
BT_TALL = Box(4.82, 4.9, 0.56, 0.6, BT_UP, BT_UP + 2.2, 0)       # the tall broom cabinet: the GAP is between it and the fridge
BT_GAP = (5.1, 5.55)
BT_CNT_E = Box(7.29, 2.55, 4.1, 0.62, BT_UP, BT_UP + 0.92, -90)   # the counter along the east wall (front faces -x)
BT_CNT_B = Box(6.98, 4.89, 1.24, 0.62, BT_UP, BT_UP + 0.92, 0)    # the counter on the back wall (the sink)
BT_STOVE = Box(7.29, 1.25, 0.76, 0.64, BT_UP, BT_UP + 0.92, -90)
BT_MICRO = Box(7.32, 2.92, 0.62, 0.44, BT_UP + 1.22, BT_UP + 1.56, -90)   # on a wooden riser on the counter (its glass at a seated boy's eye level)
BT_RISER = Box(7.32, 2.92, 0.66, 0.46, BT_UP + 0.92, BT_UP + 1.22, -90)
BT_MGLASS = (2.83, 3.18, 1.28, 1.52)   # the microwave door glass on its face x 7.1 (y0, y1, Y0, Y1 above the floor)
BT_MX = 7.098                          # the microwave door's plane (the mirror for bt_mirror)
BT_COUCH = Box(2.45, 3.95, 1.9, 0.86, BT_UP, BT_UP + 0.84, -90)   # faces the front door (-x)
# the school (its own plan): the kerb on the north at y 0, the lane y -3.2 .. 0 (one-way east), the school front y 9
SC_CAR = (0.6, -1.3)                   # the silver car's centre, facing +x (its driver side, +y, to the kerb)
SC_DUNN = (7.4, 0.55)
SC_XWALK = (8.2, 10.2)
# now (its own plan): the office x 0 .. 3.2, the hall x 3.2 .. 4.4, the son's room x 4.4 .. 8.0 (front y 0), floor BT_UP
NW_OFF = (0.0, 3.2, 0.0, 3.4)
NW_HALL = (3.2, 4.4, 0.0, 6.0)
NW_SON = (4.4, 8.0, 0.0, 3.6)
NW_SWIN = (5.3, 6.4, 0.85, 2.05)
NW_LAMP = (6.1, -4.4)

BT_SODIUM = '#ffb468'
BT_LAPTOP = '#bcd4ff'
BT_TAB = '#a8c8ff'
BT_WARM = '#ffcf94'
BT_RED, BT_RED_SH, BT_RED_HI, BT_RED_LIN = '#b5262c', '#7a1418', '#d94a4c', '#3c1216'
BT_PEN = '#1f3f9e'                     # Mom's blue pen
BT_PEN_PALE = '#c4ccdc'
BT_PAL = dict(brick='#8a4a3a', brick_ink='#5a2e24', trim='#e2dccc', bay='#b8b2a4', kit_paper='#e4dcc4', liv_paper='#cdbfa4',
              owen_paper='#9fb8c8', owen_ink='#86a0b4', floor='#9a6a40', couch='#5a6a7a', couch_d='#44525e', cab='#7f8f7a', cnt='#d6cfbe')

# ====================================================================================================== grades
_GR.setdefault('bt_night', dict(exposure=0.14, contrast=1.08, pivot=0.24, gamma=1.06, sat=1.02, wb=(0.95, 1.0, 1.08), floor='#070a14',
                                bloom=0.9, bloom_thr=224, vignette=0.42, grain=0.6, shoulder=0.45))
_GR.setdefault('bt_ext', dict(exposure=0.08, contrast=1.08, pivot=0.24, gamma=1.04, sat=1.06, wb=(0.96, 1.0, 1.06), floor='#060a14',
                              bloom=1.0, bloom_thr=222, vignette=0.38, grain=0.6, shoulder=0.45))
_GR.setdefault('bt_warm', dict(exposure=0.05, contrast=1.04, pivot=0.25, gamma=1.04, sat=1.06, wb=(1.05, 1.0, 0.93), floor='#0e0a08',
                               bloom=0.85, bloom_thr=226, vignette=0.4, grain=0.45, shoulder=0.5))
_GR.setdefault('bt_evening', dict(exposure=0.06, contrast=1.05, pivot=0.25, gamma=1.04, sat=1.02, wb=(1.0, 0.99, 1.0), floor='#0a0a0e',
                                  bloom=0.85, bloom_thr=226, vignette=0.4, grain=0.5, shoulder=0.5))
_GR.setdefault('bt_day', dict(exposure=0.04, contrast=1.04, pivot=0.26, gamma=1.02, sat=1.06, wb=(1.03, 1.0, 0.95), floor='#14100c',
                              bloom=0.8, bloom_thr=230, vignette=0.36, grain=0.35, shoulder=0.55))
_GR.setdefault('bt_snow', dict(exposure=0.02, contrast=1.02, pivot=0.27, gamma=1.02, sat=0.92, wb=(0.97, 1.0, 1.05), floor='#10121a',
                               bloom=0.8, bloom_thr=232, vignette=0.34, grain=0.45, shoulder=0.6))
_GR.setdefault('bt_now', dict(exposure=0.1, contrast=1.08, pivot=0.24, gamma=1.05, sat=0.96, wb=(0.95, 1.0, 1.08), floor='#06080e',
                              bloom=0.9, bloom_thr=226, vignette=0.46, grain=0.55, shoulder=0.45))
_GR.setdefault('bt_ins', dict(contrast=1.04, pivot=0.25, gamma=1.04, sat=1.04, wb=(1.0, 1.0, 1.0), floor='#0a0a0c',
                              bloom=0.5, bloom_thr=236, vignette=0.45, grain=0.4, shoulder=0.5))
_GR.setdefault('bt_ins_night', dict(contrast=1.06, pivot=0.25, gamma=1.04, sat=1.0, wb=(0.96, 1.0, 1.06), floor='#060a14',
                                    bloom=0.7, bloom_thr=230, vignette=0.48, grain=0.55, shoulder=0.5))
_GR.setdefault('bt_screen', dict(contrast=1.0, pivot=0.25, gamma=1.0, sat=1.0, wb=(1.0, 1.0, 1.0), floor='#000000',
                                 bloom=0.0, bloom_thr=250, vignette=0.94, grain=0.2, shoulder=0.7))

BT_CAMS = []


def _bcam(name, S, h, eye, x, y, yaw, env=None, note='', room='', pitch=0.0):
    _cam(name, S, h, eye, x, y, yaw, env or _env(), note, room, pitch)
    if name not in BT_CAMS: BT_CAMS.append(name)


def _tod(o): return o.get('tod', 'night') or 'night'


def _lv(o, k, d=0.0): return _static(o.get(k, d), d)


# ====================================================================================================== small drawing helpers
def _bt_button(pen, x, y, r, c='#141418', glint=True, a=255):
    """A shiny four-hole button (flat on what it sits on), r = radius px."""
    pen.fill(oval(x, y, r), c, a)
    pen.fill(oval(x, y, r * 0.78), mix(c, '#000000', 0.25), a)
    if r > 3:
        for (dx, dy) in ((-0.22, -0.22), (0.22, -0.22), (-0.22, 0.22), (0.22, 0.22)):
            pen.fill(oval(x + dx * r, y + dy * r, max(0.6, 0.11 * r)), mix(c, '#000000', 0.6), a)
    if glint: pen.fill(oval(x - 0.42 * r, y - 0.42 * r, max(0.7, 0.16 * r), max(0.5, 0.11 * r)), '#ffffff', int(0.85 * a))


def _bt_coat(pen, cx, cy, h, full=1.0, buttons=7, sway=0.0, hanger=True, a=255, dark=0.0):
    """The red coat with seven black buttons on a hanger (collar at (cx, cy), length h px): full 1 = rounded as if
    somebody were inside, buttoned to the top (the empty coat in the closet / the shop's mannequin); full 0 = sagged, limp,
    empty. dark 0..1 = how deep in shadow (the closet at 3 a.m.)."""
    f = clamp(full); sg = 1.0 - f
    red = mix(BT_RED, '#1a0608', dark * 0.75); sh = mix(BT_RED_SH, '#0a0204', dark * 0.75); hi = mix(BT_RED_HI, BT_RED, dark)
    sw = h * (0.27 + 0.05 * f - 0.07 * sg); hw = h * (0.33 + 0.06 * f - 0.1 * sg)
    dy = h * 0.06 * sg                                                      # the hem drops as it sags
    if hanger:
        pen.line(smooth([(cx - 0.22 * h, cy + 0.04 * h), (cx, cy - 0.04 * h), (cx + 0.22 * h, cy + 0.04 * h)], False), max(1.5, 0.018 * h), '#8a8a8e', a)
        pen.line(smooth([(cx, cy - 0.04 * h), (cx + 0.01 * h, cy - 0.12 * h), (cx - 0.03 * h, cy - 0.15 * h)], False), max(1.2, 0.012 * h), '#9a9aa0', a)
    bulge = 0.05 * f * h
    L = [(cx - 0.07 * h, cy), (cx - sw, cy + 0.07 * h), (cx - sw - bulge * 0.6, cy + 0.35 * h), (cx - hw - bulge, cy + 0.7 * h), (cx - hw * (1 - 0.15 * sg), cy + h + dy)]
    R = [(2 * cx - p[0], p[1]) for p in L]
    body = smooth(L + [(cx - hw * 0.3, cy + h + dy + 0.02 * h), (cx + hw * 0.3, cy + h + dy + 0.02 * h)] + R[::-1], True, 0.6)
    pen.fill(body, red, a); pen.line(body, max(1.2, 0.012 * h), '#1a0606', int(0.8 * a))
    # shading: the sides fall away (full) / the empty middle caves in (sagged)
    pen.cv.save(); pen.cv.clipPath(body, skia.ClipOp.kIntersect, True)
    pen.fill(rect(cx - hw * 1.3, cy, hw * 0.45, h * 1.2), sh, int(110 * a / 255), blur=0.06 * h)
    pen.fill(rect(cx + hw * 0.85, cy, hw * 0.5, h * 1.2), sh, int(150 * a / 255), blur=0.06 * h)
    if f > 0.05: pen.fill(oval(cx - 0.12 * h, cy + 0.4 * h, 0.1 * h, 0.28 * h), hi, int(70 * f * a / 255), blur=0.05 * h)
    if sg > 0.05:
        pen.fill(oval(cx, cy + 0.45 * h, 0.16 * h, 0.42 * h), sh, int(120 * sg * a / 255), blur=0.07 * h)
        for k in range(3):                                                  # limp vertical folds
            xx = cx + (k - 1) * 0.13 * h
            pen.line(smooth([(xx, cy + 0.2 * h), (xx + 0.02 * h, cy + 0.6 * h), (xx - 0.01 * h, cy + h)], False), max(1.0, 0.01 * h), sh, int(150 * sg * a / 255))
    pen.cv.restore()
    # sleeves hanging at the sides
    for sd in (-1, 1):
        sl = smooth([(cx + sd * sw, cy + 0.08 * h), (cx + sd * (sw + 0.07 * h + bulge), cy + 0.3 * h), (cx + sd * (hw + 0.04 * h), cy + 0.68 * h + dy),
                     (cx + sd * (hw - 0.07 * h), cy + 0.7 * h + dy), (cx + sd * (sw - 0.02 * h), cy + 0.3 * h)], True, 0.6)
        pen.fill(sl, mix(red, sh, 0.25), a); pen.line(sl, max(1.0, 0.01 * h), '#1a0606', int(0.7 * a))
    # the collar (wide, rounded) and the button placket
    col_ = smooth([(cx - 0.16 * h, cy + 0.02 * h), (cx - 0.05 * h, cy + 0.13 * h), (cx, cy + 0.1 * h), (cx + 0.05 * h, cy + 0.13 * h), (cx + 0.16 * h, cy + 0.02 * h), (cx, cy - 0.01 * h)], True, 0.7)
    pen.fill(col_, mix(red, hi, 0.25), a); pen.line(col_, max(1.0, 0.01 * h), '#1a0606', int(0.7 * a))
    pen.seg((cx + 0.015 * h, cy + 0.12 * h), (cx + 0.015 * h + 0.03 * h * sg, cy + h + dy), max(1.0, 0.008 * h), sh)
    for j in range(7):
        by = cy + h * (0.17 + j * 0.12) + dy * j / 6.0
        bx = cx + 0.045 * h + 0.03 * h * sg * math.sin(j * 1.3)
        if j < buttons: _bt_button(pen, bx, by, max(1.5, 0.028 * h), a=a)


def _bt_tablet_flat(pen, x, y, w, h, screen='#9ab8e8', k=1.0, rot=0.0, face_down=False):
    """A tablet seen face-on in screen space (centre x, y; w x h px). face_down: its dark back with the camera dot."""
    pen.cv.save(); pen.cv.translate(x, y); pen.cv.rotate(rot)
    b = rrect(-w / 2, -h / 2, w, h, 0.07 * min(w, h))
    pen.fill(moved(b, 0.03 * w, 0.05 * h), '#000000', 90, blur=0.04 * w)
    pen.fill(b, '#2a2c32' if face_down else '#16171b'); pen.line(b, max(1.0, 0.01 * w), '#000000', 200)
    if face_down:
        pen.fill(oval(-0.36 * w, -0.38 * h, 0.025 * w), '#0a0a0c'); pen.fill(rrect(-0.1 * w, -0.04 * h, 0.2 * w, 0.08 * h, 0.03 * w), '#33363e')
    else:
        sc = rrect(-0.44 * w, -0.43 * h, 0.88 * w, 0.86 * h, 0.02 * w)
        pen.fill(sc, mix('#0a0e18', screen, k))
    pen.cv.restore()


def _bt_tparts(B, *a, **k):
    """table_parts for a table standing on an upper floor (its legs start at B.Y0, not at 0)."""
    P = table_parts(B, *a, **k)
    for p_ in P:
        if p_.box is not None and p_.box.Y0 < B.Y0 - 0.01: p_.box.Y0 = B.Y0
    return P


# ====================================================================================================== outside: our block
def _bt_tex_face(pen, v, F, c, kind=None, art=None, line=True):
    def a_(p_, W, H):
        if kind: p_.texture(rect(0, 0, W, H), kind, 0.5, 'overlay', 1.0)
        if art: art(p_, W, H)
    draw_face(pen, v, F, a_, c, ao=False, line=line)


def _bt_facade_art(o, which='ours'):
    """The facade art (cm frame, y down from the top): brick courses, a cornice, three floors of windows (dark glass with
    frames and sills; lit ones get their glow live), the ground floor."""
    tod = _tod(o)
    def art(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'grunge', 0.35, 'overlay', 1.0)
        for i in range(int(H / 7.5)):                                       # brick courses
            p_.fill(rect(0, i * 7.5, W, 0.8), '#3a1e16', 55)
        p_.fill(rect(0, 0, W, 34), '#6a3a2e'); p_.fill(rect(0, 30, W, 6), '#e0d6c4', 200)   # the cornice
        p_.fill(rect(0, H - 22, W, 22), '#5a4a42', 230)                     # the base
        x0 = BT_BLD[0]
        floors = [(BT_UP, 0.9), (BT_UP + 3.4, 0.9)]
        for (Yf, sl) in floors:
            for nm, (a, b) in BT_FWIN.items():
                s_ = BT_OWIN[2] if (nm == 'owen' and Yf == BT_UP) else sl
                _bt_win_art(p_, (a - x0) * 100, (b - x0) * 100, H - (Yf + 2.1) * 100, H - (Yf + s_) * 100, tod)
        for (a, b) in ((-7.8, -6.4), (-4.9, -3.5), (-1.9, -0.5), (8.4, 9.8), (10.4, 11.6)):     # ground floor
            _bt_win_art(p_, (a - x0) * 100, (b - x0) * 100, H - 2.3 * 100, H - 0.8 * 100, tod)
        btext(p_, '418', (7.4 - x0) * 100, H - 250, 'serif_b', 26, '#e8dcc0', 230, 'center')
    return art


def _bt_win_art(p_, x0, x1, yt, yb, tod='night'):
    w, h = x1 - x0, yb - yt
    p_.fill(rect(x0 - 6, yt - 6, w + 12, h + 12), '#d8d0c0')                # stone surround
    p_.fill(rect(x0 - 9, yb + 2, w + 18, 9), '#e4dccc')                     # the sill
    p_.fill(rect(x0, yt, w, h), '#141a26' if tod == 'night' else ('#5a6a80' if tod == 'day' else '#2a3448'))
    p_.linear(rect(x0, yt, w, h), x0, yt, x1, yb, [(0, '#ffffff', 26 if tod != 'night' else 8), (0.5, '#ffffff', 0), (1, '#ffffff', 14)])
    p_.fill(rect(x0 + w / 2 - 2, yt, 4, h), '#d8d0c0'); p_.fill(rect(x0, yt + h * 0.55 - 2, w, 4), '#d8d0c0')


def _bt_grid_art(Wm, Hm, tod, seed=0):
    """A plain neighbouring facade: a cornice and a grid of windows (a few lit at night)."""
    def art(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'grunge', 0.35, 'overlay', 1.0)
        p_.fill(rect(0, 0, W, 26), '#000000', 60)
        rng = np.random.default_rng(abs(seed))
        for fl in range(int((Hm - 1.0) / 3.3)):
            yb = H - (0.9 + fl * 3.3) * 100
            for k in range(int(Wm / 2.4)):
                x0 = 60 + k * 240
                _bt_win_art(p_, x0, x0 + 120, yb - 130 - (0 if fl else 40), yb - (0 if fl else 40), tod)
                if tod == 'night' and rng.uniform() < 0.22: p_.fill(rect(x0, yb - 130 - (0 if fl else 40), 120, 130), '#e8b870', 150)
    return art


def _bt_shop_art(o, kind='barlow'):
    tod = _tod(o)
    def art(p_, W, H):                                                      # Barlow's front, x from BT_BARLOW[1] (east) .. west (u = east - x)
        p_.texture(rect(0, 0, W, H), 'grunge', 0.35, 'overlay', 1.0)
        for i in range(int(H / 7.5)): p_.fill(rect(0, i * 7.5, W, 0.7), '#2a2018', 40)
        if kind == 'barlow':
            x0 = BT_BARLOW[1]
            sx0, sx1 = (x0 - BT_BWIN[1]) * 100, (x0 - BT_BWIN[0]) * 100
            p_.fill(rect(sx0 - 30, H - 330, sx1 - sx0 + 60 + 60, 52), '#1e3a2e')   # the sign band
            p_.line(rect(sx0 - 30, H - 330, sx1 - sx0 + 120, 52), 3, '#c8a860')
            btext(p_, "BARLOW'S", (sx0 + sx1) / 2 + 30, H - 291, 'serif_b', 40, '#f0dca0', 255, 'center', 0.12)
            btext(p_, 'COATS  .  BOOTS  .  SINCE 1961', (sx0 + sx1) / 2 + 30, H - 266, 'sans_b', 11, '#c8b890', 230, 'center', 0.1)
            # the display window frame (the glass itself is a hole: the mannequin stands behind it)
            p_.line(rect(sx0 - 4, H - BT_BWIN[3] * 100 - 4, sx1 - sx0 + 8, (BT_BWIN[3] - BT_BWIN[2]) * 100 + 8), 8, '#1e3a2e')
            p_.fill(rect(sx0 - 10, H - BT_BWIN[2] * 100, sx1 - sx0 + 20, BT_BWIN[2] * 100), '#3a2a22')
            dx0, dx1 = (x0 - BT_BDOOR[1]) * 100, (x0 - BT_BDOOR[0]) * 100
            p_.fill(rect(dx0, H - BT_BDOOR[2] * 100, dx1 - dx0, BT_BDOOR[2] * 100), '#1e3a2e')
            p_.fill(rect(dx0 + 10, H - BT_BDOOR[2] * 100 + 12, dx1 - dx0 - 20, BT_BDOOR[2] * 100 * 0.62), '#ffd890' if tod == 'night' else '#6a7888', 200)
            btext(p_, 'OPEN' if tod != 'night' else 'CLOSED', (dx0 + dx1) / 2, H - 135, 'sans_b', 11, '#c82a2a', 230, 'center')
            for (a, b) in ((60, 200), (300, 440), (540, 680), (780, 920)):  # upstairs windows
                _bt_win_art(p_, a, b, H - 620, H - 430, tod)
        else:
            for i, (a, b) in enumerate(((40, 180), (260, 400), (480, 620), (700, 840), (920, 1060), (1140, 1280), (1360, 1500))):
                if b > W - 20: break
                _bt_win_art(p_, a, b, H - 620, H - 430, tod)
                if i % 2 == 0: p_.fill(rect(a, H - 260, b - a + 40, 180), '#22303a' if tod == 'night' else '#5a6a7a')
            p_.fill(rect(0, H - 300, W, 30), '#3a2a4a')
            btext(p_, 'LAUNDRY  .  PHARMACY  .  DELI', 400, H - 278, 'sans_b', 18, '#e8d8c0', 220, 'left', 0.15)
    return art


def bt_ext_draw(pen, v, o):
    """Sky, the street, the far facades and (when the camera is outside it) our building, as one painter's pass (the
    outside seen through our windows, and the street set's shell)."""
    tod = _tod(o)
    if tod in ('day', 'evening'):
        x0, y0, x1, y1 = (-900, -700, 2820, 1780)
        top, mid, bot = ('#5a8ac8', '#a8c4e0', '#e4ecee') if tod == 'day' else ('#2a3a6a', '#7a7aa8', '#e8a888')
        pen.linear(rect(x0, y0, x1 - x0, y1 - y0), 0, v.h - 1.2 * v.S, 0, v.h + 20, [(0, top), (0.6, mid), (1, bot)])
    else:
        ic_sky(pen, v, 'night')
    G, R = BT_G, BT_ROAD
    # far buildings across the street (facing +y) and down the side street
    for (bx0, bx1, Hb, kind) in ((BT_BARLOW[0], BT_BARLOW[1], 7.4, 'barlow'), (3.5, 24.0, 9.2, 'shops'), (-30.0, BT_BARLOW[0], 8.6, 'shops')):
        B = Box((bx0 + bx1) / 2, -20.0, bx1 - bx0, 8.0, G, G + Hb, 180)
        fs = B.faces()
        if v.d(B.cx, B.cy) > 0.5 and v.hy > BT_FAR - 0.5:
            c = '#7a5a4a' if kind == 'barlow' else '#6a6a78'
            if tod == 'night': c = mix(c, '#1a2030', 0.5)
            _bt_tex_face(pen, v, fs['front'], c, None, _bt_shop_art(o, kind))
    if v.hy > BT_FAR - 0.5:
        # the display window glow + the mannequin in the red coat (Barlow's)
        _bt_barlow_window(pen, v, o)
        # the far sidewalk and the road, our sidewalk
        _wl_strip(pen, v, -40, 40, BT_FAR, BT_KERB_F, G, '#8a8a88' if tod != 'night' else '#4a4e5a', 'concrete')
        _wl_strip(pen, v, -40, 40, BT_KERB_F, BT_KERB, R, '#4a4c52' if tod != 'night' else '#22252e', 'asphalt',
                  ink=lambda p_, W, H: [p_.fill(rect(k * 600 + 50, (BT_KERB_F - (-8.8)) * -100 - 5, 300, 10), '#d8c060', 160) for k in range(int(W / 600) + 1)])
        _wl_strip(pen, v, -3.5, 3.5, -40, BT_FAR, R, '#4a4c52' if tod != 'night' else '#22252e', 'asphalt')
        for (xa, xb, yk) in ((-40, 40, BT_KERB), (40, -40, BT_KERB_F)):     # kerb faces (the side facing the road)
            draw_face(pen, v, wall_face((xa, yk), (xb, yk), R, G), None, '#9a9890' if tod != 'night' else '#4a4c56', ao=False, line=False)
        _wl_strip(pen, v, -40, 40, BT_KERB, 0.0, G, '#9a9894' if tod != 'night' else '#4e525e', 'concrete',
                  ink=lambda p_, W, H: [p_.fill(rect(k * 150, 0, 2, H), '#000000', 40) for k in range(int(W / 150) + 1)])
        if o.get('snow', 0.4):                                              # old grey snow along the kerbs (Wednesday's snow came after)
            _bank(pen, v, -40, -4.0, BT_KERB - 0.25, 0.5, 0.18 * o.get('snow', 0.4), 1, 3, Y=G)
            _bank(pen, v, 4.0, 40, BT_KERB - 0.25, 0.5, 0.18 * o.get('snow', 0.4), 1, 4, Y=G)
    if v.hy < -0.3:                                                         # the neighbours either side, then our building
        for (a_, b_, Hn, c, yf) in ((-30.0, BT_BLD[0], 8.4, '#8a8478', 0.4), (BT_BLD[1], 32.0, 11.8, '#9a7a5a', 0.0)):
            F = wall_face((a_, yf), (b_, yf), G, G + Hn)
            _bt_tex_face(pen, v, F, c if tod != 'night' else mix(c, '#1a1a2a', 0.5), None, _bt_grid_art(b_ - a_, Hn, tod, int(a_)))
        F = wall_face((BT_BLD[0], 0.0), (BT_BLD[1], 0.0), G, G + BT_BLD_H)
        _bt_tex_face(pen, v, F, BT_PAL['brick'] if tod != 'night' else mix(BT_PAL['brick'], '#1a1a2a', 0.45), None, _bt_facade_art(o))


def _bt_barlow_window(pen, v, o):
    tod = _tod(o)
    x0, x1, sl, tp = BT_BWIN
    q = [v.p(x0, sl, BT_FAR), v.p(x1, sl, BT_FAR), v.p(x1, tp, BT_FAR), v.p(x0, tp, BT_FAR)]
    if v.d(x0, BT_FAR) < 0.3 or v.d(x1, BT_FAR) < 0.3: return
    win = poly(q)
    pen.fill(win, '#3a2c22' if tod != 'night' else '#ffcf8a')
    pen.linear(win, 0, q[2][1], 0, q[0][1], [(0, '#f8e2b0' if tod == 'night' else '#8a7a6a'), (1, '#c89a60' if tod == 'night' else '#4a3a30')], a=0.9)
    pen.cv.save(); pen.cv.clipPath(win, skia.ClipOp.kIntersect, True)
    s = v.s(BT_COAT_AT[0], BT_COAT_AT[1] - 0.4)
    for (mx, mh, c, kind) in ((-8.6, 1.0, '#3a5a8a', 'boots'), (-6.0, 0.55, '#d8c8a0', 'scarf')):  # the other things in the window
        px, py = v.p(mx, sl + 0.15, BT_FAR - 0.5)
        if kind == 'boots':
            for dd in (0, 0.2):
                pen.fill(rrect(px + dd * s, py - 0.28 * s, 0.13 * s, 0.28 * s, 0.03 * s), '#5a3a22'); pen.fill(rect(px + dd * s, py - 0.04 * s, 0.2 * s, 0.04 * s), '#2a1a10')
        else:
            pen.fill(rrect(px, py - 0.9 * s, 0.05 * s, 0.9 * s, 0.02 * s), '#6a5a4a')
            pen.fill(smooth([(px - 0.12 * s, py - 0.86 * s), (px + 0.17 * s, py - 0.86 * s), (px + 0.1 * s, py - 0.3 * s), (px - 0.05 * s, py - 0.3 * s)]), '#c8a040')
    # the child mannequin form on its stand, the red coat on it, buttoned, seven black buttons
    cx, cy = v.p(BT_COAT_AT[0], 1.55, BT_COAT_AT[1] - 0.5)
    bx, by = v.p(BT_COAT_AT[0], sl, BT_COAT_AT[1] - 0.5)
    pen.seg((bx, by), (cx, cy + 0.6 * s), max(1.2, 0.03 * s), '#5a4a3a')
    pen.fill(oval(bx, by, 0.18 * s, 0.03 * s), '#3a2a22')
    pen.fill(oval(cx, cy - 0.08 * s, 0.07 * s, 0.05 * s), '#e0cdb0')         # the neck stub
    _bt_coat(pen, cx, cy, 0.74 * s, 1.0, 7, hanger=False)
    pen.fill(win, '#ffffff', 22 if tod != 'night' else 8)                   # glass sheen
    pen.linear(win, q[0][0], q[2][1], q[1][0], q[0][1], [(0, '#ffffff', 0), (0.45, '#ffffff', 40 if tod != 'night' else 14), (0.55, '#ffffff', 0)])
    pen.cv.restore()
    pen.line(win, max(1.0, 0.02 * s), '#1e3a2e')


def bt_lobby_bay(pen, v, o):
    """The lobby bay: brick sides, the GLASS DOOR on its west face (lit from inside at night), a lobby window on its
    south face, the flat roof with a little snow, the address over the door."""
    tod = _tod(o)
    B = Box((BT_BAY[0] + BT_BAY[1]) / 2, (BT_BAY[2] + BT_BAY[3]) / 2, BT_BAY[1] - BT_BAY[0], BT_BAY[3] - BT_BAY[2], BT_G, BT_G + BT_BAY_H, 0)
    night = tod == 'night'
    glow = '#f4e2b4' if night else '#6a7a8a'
    def front(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'grunge', 0.35, 'overlay', 1.0)
        p_.fill(rect(80, 70, W - 160, 150), '#2a2a2e'); p_.fill(rect(90, 80, W - 180, 130), glow, 220)
        for k in range(1, 4): p_.fill(rect(90 + k * (W - 180) / 4 - 2, 80, 4, 130), '#2a2a2e')
        p_.fill(rect(0, 0, W, 16), '#d8d0c0')
    def west(p_, W, H):                                                     # the left face runs y -0 .. -2.6? (u from the front corner)
        p_.texture(rect(0, 0, W, H), 'grunge', 0.35, 'overlay', 1.0)
        u0 = (BT_GDOOR[0] - BT_BAY[2]) * 100; u1 = (BT_GDOOR[1] - BT_BAY[2]) * 100
        a_, b_ = W - u1, W - u0
        p_.fill(rect(a_ - 8, H - BT_GDOOR[2] * 100 - 8, b_ - a_ + 16, BT_GDOOR[2] * 100 + 8), '#3a3c42')
        g = rect(a_ + 4, H - BT_GDOOR[2] * 100 + 4, b_ - a_ - 8, BT_GDOOR[2] * 100 - 10)
        p_.fill(g, glow, 235 if night else 200)
        p_.linear(g, a_, 0, b_, 0, [(0, '#ffffff', 0), (0.3, '#ffffff', 50), (0.4, '#ffffff', 0)])
        p_.fill(rect(a_ + 4, H - 112, b_ - a_ - 8, 6), '#9a9ca4')           # push bar
        btext(p_, '418', (a_ + b_) / 2, H - BT_GDOOR[2] * 100 - 22, 'serif_b', 20, '#e8dcc0', 230, 'center')
        p_.fill(rect(0, 0, W, 16), '#d8d0c0')
    draw_box(pen, v, B, {'front': dict(fill=BT_PAL['brick'] if not night else mix(BT_PAL['brick'], '#1a1a2a', 0.4), art=front),
                         'left': dict(fill=BT_PAL['brick'] if not night else mix(BT_PAL['brick'], '#1a1a2a', 0.4), art=west),
                         'right': BT_PAL['brick'], 'top': dict(fill='#3a3a40', art=lambda p_, W, H: p_.fill(rect(0, 0, W, H), '#dde4ee', 150))}, lw=1.0, skip=('back', 'bottom'))


def bt_bus_stop(pen, v, G=BT_G):
    x, y = BT_STOP
    if v.d(x, y) > 0.5:
        s = v.s(x, y)
        a_, b_ = v.p(x, G, y), v.p(x, G + 2.6, y)
        pen.seg(a_, b_, max(1.2, 0.05 * s) + 1.5, LINE); pen.seg(a_, b_, max(1.0, 0.05 * s), lit('#8a8c90', (x, G + 1.5, y), None))
        px, py = v.p(x, G + 2.35, y)
        sg = rrect(px - 0.24 * s, py - 0.2 * s, 0.48 * s, 0.4 * s, 0.03 * s)
        pen.fill(sg, lit('#e8e4d8', (x, G + 2.35, y), (0, 0, -1))); pen.line(sg, 1.0)
        pen.fill(rect(px - 0.2 * s, py - 0.16 * s, 0.4 * s, 0.12 * s), lit('#1a5a8a', (x, G + 2.35, y), (0, 0, -1)))
        btext(pen, 'BUS', px, py - 0.065 * s, 'sans_b', 0.09 * s, '#ffffff', 240, 'center')
        btext(pen, 'STOP', px, py + 0.1 * s, 'sans_b', 0.1 * s, '#1a1a1a', 240, 'center')
        btext(pen, '22', px, py + 0.18 * s, 'sans_b', 0.06 * s, '#c82a2a', 240, 'center')
    B = Box(2.9, -3.7, 1.7, 0.5, G, G + 0.45, 0)
    if v.d(B.cx, B.cy) > 0.5:
        for u in (-0.65, 0.65): draw_box(pen, v, sub(B, u - 0.06, u + 0.06, -0.2, 0.2, G, G + 0.42), {'all': '#8a8a86'})
        for k in range(4):
            n = -0.2 + k * 0.13
            draw_box(pen, v, sub(B, -0.85, 0.85, n - 0.05, n + 0.05, G + 0.42, G + 0.46), {'all': '#6a6458', 'top': '#8a8470'})
        for k in range(2):
            Yb = G + 0.62 + k * 0.15
            draw_box(pen, v, sub(B, -0.85, 0.85, -0.26, -0.21, Yb, Yb + 0.1), {'all': '#7a7462'})


def bt_sweep(t0, dur=2.6):
    """Headlights sweeping past from east to west (a car on our side of the street), starting at t0: returns
    f(t) -> x of the car's nose (None before / after). Pass sweep=ST.bt_sweep(t0) to bt_street / bt_owen."""
    def f(t):
        if t < t0 or t > t0 + dur: return None
        return lerp(26.0, -26.0, (t - t0) / dur)
    return f


def _bt_sweep_lamps(o, seed=900, Y=1.0, y=-7.0, xs=(-12.0, -6.0, -1.2, 3.0, 9.0), k=2.2):
    """Headlight light as a row of lamps whose levels follow the passing car (the light sweeps across the facade)."""
    sw = o.get('sweep')
    if not callable(sw): return []
    out = []
    for i, X in enumerate(xs):
        def f(t, X=X):
            cx = sw(t)
            if cx is None: return 0.0
            dx = X - (cx - 4.0)                                             # the beams reach ~4 m ahead of the nose (west)
            return clamp(1.0 - abs(dx) / 4.5) ** 1.5
        out.append(('sweep_%d' % i, [Lamp(X, Y, y, 9.0, '#fff4dc', k, (0.6, 1.0, 1.0), fall=1.4)], f))
    return out


def bt_ext_glow(v, o, name='ext_glow'):
    """Live light outside: the streetlight's glow and pool, the lobby glow, the lit windows (o['win'] {name: level}),
    the passing car's headlights (o['sweep'])."""
    tod = _tod(o)
    wins = {nm: _kfn(lv, 950 + i) for i, (nm, lv) in enumerate((o.get('win') or {}).items())}
    sw = o.get('sweep')
    def draw(pen, t):
        if tod != 'day':
            dr_streetlight_glow(pen, v, BT_LAMP[0], BT_LAMP[1], 1.0 if tod == 'night' else 0.7, BT_SODIUM, 1.0, BT_LAMP_H, BT_G, rain=False, t=t)
            if v.hy < -0.3 and v.d(BT_BAY[0], -1.5) > 0.4:                  # the lobby door's glow on the sidewalk
                x, y = v.p(BT_BAY[0] - 0.1, 1.2, -1.5); s = v.s(BT_BAY[0], -1.5)
                pen.glow(x, y, 1.6 * s, '#ffe2a8', 70)
        if v.hy < -0.3:
            for nm, kf in wins.items():
                k = kf(t)
                if k <= 0.01 or nm not in BT_FWIN: continue
                a, b = BT_FWIN[nm]
                if min(v.d(a, 0.0), v.d(b, 0.0)) < 0.6: continue
                sl = BT_UP + (BT_OWIN[2] if nm == 'owen' else 0.9)
                q = [v.p(a, sl, -0.01), v.p(b, sl, -0.01), v.p(b, BT_UP + 2.1, -0.01), v.p(a, BT_UP + 2.1, -0.01)]
                c = BT_TAB if nm == 'owen' else BT_WARM
                pen.fill(poly(q), c, int(150 * k)); pen.fill(poly(q), '#ffffff', int(40 * k), blur=4)
        if callable(sw):
            cx = sw(t)
            if cx is not None and v.d(cx, -6.6) > 0.5:                      # the car: a dark shape, two headlights, beams
                s = v.s(cx, -6.6)
                px, py = v.p(cx, BT_ROAD + 0.65, -6.6)
                if v.d(cx + 4.3, -6.6) > 0.5:
                    qx, qy = v.p(cx + 4.3, BT_ROAD + 0.65, -6.6); q2 = v.p(cx + 4.3, BT_ROAD + 1.45, -6.6); q3 = v.p(cx + 0.4, BT_ROAD + 1.4, -6.6)
                    pen.fill(smooth([(px, py - 0.1 * s), (px, py + 0.35 * s), (qx, qy + 0.35 * s), q2, q3], True, 0.5), '#0c0e14', 230)
                for dy in (0.0,):
                    pen.glow(px, py + dy, 0.5 * s, '#fff6e0', 230); pen.glow(px, py, 0.12 * s, '#ffffff', 255)
                bx, by = v.p(cx - 7.0, BT_ROAD + 0.3, -6.0)
                pen.fill(poly([(px, py - 0.08 * s), (px, py + 0.1 * s), (bx, by + 0.9 * s), (bx, by - 0.5 * s)]), '#fff4dc', 40, blur=0.4 * s)
    lay = Layer(1.0, draw, name, blur=None); lay.order = ORDER_SHELL - 0.2
    return [lay]


class BtStreet(Room):
    """Our block as a room: the shell is bt_ext_draw; the pieces are the lobby bay, the streetlight, the bus stop."""
    name = 'street'
    poly = [(-60.0, -40.0), (60.0, -40.0), (60.0, 20.0), (-60.0, 20.0)]

    def __init__(self, o): self.o = o

    def lights(self, o):
        tod = _tod(o)
        if tod == 'day':
            amb, steady = '#9a948a', [Lamp(kind='dir', c='#fff0d8', k=1.0, d=_norm3((-0.4, -0.75, 0.5)))]
        elif tod == 'evening':
            amb, steady = '#6a6a80', [Lamp(kind='dir', c='#ffc8a0', k=0.6, d=_norm3((-0.6, -0.5, 0.6)))]
        else:
            amb, steady = '#3a4470', [Lamp(kind='dir', c='#9aaee8', k=0.45, d=_norm3((0.3, -0.8, 0.6)))]
        steady = list(steady)
        if tod != 'day':
            steady.append(Lamp(BT_LAMP[0], BT_G + BT_LAMP_H, BT_LAMP[1] - 1.2, 13.0, BT_SODIUM, 1.9 if tod == 'night' else 1.0, (1.0, 0.7, 0.3), fall=1.3))
            steady.append(Lamp(BT_BAY[0] - 0.4, 1.3, -1.5, 3.6, '#ffe2a8', 1.1 if tod == 'night' else 0.5, (0.6, 1.0, 0.6), fall=1.5))   # the lobby door
            steady.append(Lamp(-7.3, 1.4, BT_FAR + 0.8, 5.0, '#ffd890', 1.1, (0.6, 1.0, 0.6), fall=1.5))                               # Barlow's window
        var = _bt_sweep_lamps(o)
        var.append(('flash', [Lamp(*o.get('flash_at', (0.0, 1.4, -6.0)), R=6.0, c='#fff4dc', k=1.6, fall=1.4)], _kfn(o.get('flash', 0.0), 933)))
        return amb, steady, var

    def shell(self, pen, v, o): bt_ext_draw(pen, v, o)

    def pieces(self, o):
        return [Piece('lobby_bay', (5.0, 1.5, -1.3), lambda pen, v: bt_lobby_bay(pen, v, o), block=_r4p(BT_BAY)),
                Piece('streetlight', (BT_LAMP[0], 3.0, BT_LAMP[1]), lambda pen, v: _bt_pole(pen, v, o),
                      block=_circ(BT_LAMP[0], BT_LAMP[1], 0.15)),
                Piece('bus_stop', (BT_STOP[0], 1.2, BT_STOP[1]), lambda pen, v: bt_bus_stop(pen, v), block=_r4p((2.05, 3.75, -3.95, -3.45)))]

    def spots(self, v, o):
        S = {}
        S['under_lamp'] = _mk_spot(v, 'under_lamp', BT_LAMP[0] + 0.15, BT_LAMP[1] + 0.5, BT_G, 'stand', 'under the streetlight, facing the building (+y): she looks up and waves', face=(0, 1))
        S['owen_window'] = _mk_spot(v, 'owen_window', (BT_FWIN['owen'][0] + BT_FWIN['owen'][1]) / 2, -0.02, BT_UP + 1.4, 'point', "Owen's window from outside")
        S['next_window'] = _mk_spot(v, 'next_window', (BT_FWIN['next'][0] + BT_FWIN['next'][1]) / 2, -0.02, BT_UP + 1.5, 'point', "the window NEXT to Owen's (where she waves)")
        S['glass_out'] = _mk_spot(v, 'glass_out', BT_BAY[0] - 0.32, -1.5, BT_G, 'stand', 'outside the glass lobby door, facing it (+x): palms on the glass', face=(1, 0))
        S['glass'] = _mk_spot(v, 'glass', BT_BAY[0] - 0.01, -1.5, BT_G + 1.3, 'point', 'the glass of the lobby door (palm height)')
        S['bus_stop'] = _mk_spot(v, 'bus_stop', BT_STOP[0], BT_STOP[1], BT_G, 'surface', 'the bus stop sign')
        S['barlow_walk'] = _mk_spot(v, 'barlow_walk', -7.0, -15.0, BT_G, 'stand', "on the far sidewalk in front of Barlow's window, facing it (-y)", face=(0, -1))
        S['barlow_mom'] = _mk_spot(v, 'barlow_mom', -5.6, -14.6, BT_G, 'stand', "Mom beside him on a call (facing -x / him)", face=(-0.7, -0.7))
        S['coat'] = _mk_spot(v, 'coat', BT_COAT_AT[0], BT_COAT_AT[1] - 0.5, 1.2, 'point', "the red coat in Barlow's window")
        S['walk_lamp'] = _mk_spot(v, 'walk_lamp', 0.5, -2.8, BT_G, 'stand', 'on our sidewalk between the lamp and the bay')
        return S


def _bt_pole(pen, v, o):
    """The streetlight, lit softly (its own lamp would blow its pole out to a neon tube)."""
    day = _tod(o) == 'day'
    with lighting('#9a948a' if day else '#58607e', [Lamp(kind='dir', c='#ffd8a8', k=0.35, d=_norm3((0.2, -0.9, 0.3)))], 1.0):
        dr_streetlight(pen, v, BT_LAMP[0], BT_LAMP[1], 1.0, arm=1.0, h=BT_LAMP_H, G=BT_G)


def _bt_window_out_layer(clip=(170, 70, 1580, 940)):
    """Screen-space foreground for a POV out of a window: the dark frame and the sash cross, soft."""
    def draw(pen, t):
        pen.fill(minus(rect(-400, -300, 2720, 1700), rrect(clip[0], clip[1], clip[2], clip[3], 8)), '#14161c')
        pen.fill(rect(-400, clip[1] + clip[3] * 0.55 - 22, 2720, 44), '#1e2026')
    return Layer(0.3, draw, 'window_frame', blur=8)


_bcam('bt_ext_from_window', 700, 470, BT_UP + 1.35, -1.7, -0.05, 186, _env(x=(920, 1000), y=(500, 560), zoom=(1.0, 1.06)),
      "POV out of Owen's window: the streetlight, the bus stop, Barlow's corner across the street", 'street', pitch=13.0)
_bcam('bt_ext_lobby_pov', 900, 400, BT_UP + 1.4, -1.5, -0.05, 128, _env(x=(920, 1000), y=(500, 560), zoom=(1.0, 1.06)),
      "POV down-left out of Owen's window to the lobby door (she is at the glass)", 'street', pitch=34.0)
_bcam('bt_ext_lamp', 880, 640, BT_G + 1.6, -0.2, -12.2, 4, _env(f=(1.0, 2.4)),
      'from across the street: our building, the streetlight in front of Owen\'s window (she stands under it), the window next to his, the lobby bay', 'street', pitch=-9.0)
_bcam('bt_ext_lamp_close', 900, 520, BT_G + 1.5, 2.6, -7.6, -26, _env(),
      'medium on the spot under the streetlight (headlights sweep her face)', 'street')
_bcam('bt_ext_lobby', 900, 520, BT_G + 1.55, -2.2, -2.5, 62, _env(), 'the lobby bay and its glass door from our sidewalk', 'street')
_bcam('bt_ext_barlow', 800, 560, BT_G + 1.5, -5.2, -10.6, 196, _env(f=(1.0, 2.2)),
      "across the street at Barlow's: the window with the red coat, the far sidewalk (Owen points, Mom on her phone)", 'street')
_bcam('bt_ext_shopwin', 1250, 540, BT_G + 1.3, -7.1, -13.6, 180, _env(x=(920, 1000), y=(500, 560), zoom=(1.0, 1.08)),
      "Barlow's display window close: the red coat with seven black buttons", 'street')


def bt_street(view='lamp', tod='night', win=None, sweep=None, snow=0.4, flash=0.0, flash_at=None, **kw):
    """Our block outside. view: from_window (POV out of Owen's window) | lobby_pov (POV down to the lobby door) | lamp
    (across the street: the building, the streetlight, the window next to his) | lamp_close | lobby | barlow | shopwin.
    tod 'night' | 'evening' | 'day' (Monday at Barlow's). win {next, owen, living, kitchen, e1, e2}: lit windows (levels);
    sweep = ST.bt_sweep(t0): headlights pass (the light sweeps across her and the facade); snow: old snow along the kerbs."""
    v = cam('bt_ext_' + view)
    o = dict(tod=tod, win=dict(win or {}), sweep=sweep, snow=snow, flash=flash, flash_at=flash_at or (0.0, 1.4, -6.0), no_veil=True)
    o.update(kw)
    main = BtStreet(o)
    dyn = list(bt_ext_glow(v, o))
    grade = 'bt_day' if tod == 'day' else ('bt_evening' if tod == 'evening' else 'bt_ext')
    sp = build_view('bt_ext_' + view, v, main, o, outside=None, grade=grade, dyn=dyn, dof=0.6)
    if view in ('from_window', 'lobby_pov'): sp = sp.add(_bt_window_out_layer())
    sp.info['note'] = 'Outside: under_lamp (she looks up, waves at next_window), glass_out / glass (palms on the lobby door), barlow_walk / barlow_mom.'
    sp.info['out_order'] = ORDER_OUT - 1
    return sp


def _bt_outside(o):
    """What our windows see: the street drawn by the same plan (lit by the street's own lights; the engine veils it at night)."""
    def f(pen, v):
        R = BtStreet(o)
        amb, steady, var = R.lights(o)
        with lighting(amb, steady, 1.0):
            bt_ext_draw(pen, v, o)
            for P in sorted(R.pieces(o), key=lambda P: -v.d(P.ref[0], P.ref[2])):
                if v.d(P.ref[0], P.ref[2]) > 0.6: P.draw(pen, v)
            if _tod(o) != 'day':                                            # the lit windows across the street, Barlow's sign glow
                bx, by = v.p(-7.3, 1.5, BT_FAR)
                if v.d(-7.3, BT_FAR) > 1.0: pen.glow(bx, by, 2.4 * v.s(-7.3, BT_FAR), '#ffcf8a', 60)
        if _tod(o) != 'day':
            dr_streetlight_glow(pen, v, BT_LAMP[0], BT_LAMP[1], 1.0, BT_SODIUM, 1.0, BT_LAMP_H, BT_G, rain=False, t=0.0)
    return f


# ====================================================================================================== the apartment: props
def _bt_amb(o, night='#1c2236'):
    tod = _tod(o)
    if tod == 'day': return '#8a8478'
    if tod == 'evening': return '#4e4e62'
    return mix(night, '#6a7aa8', 0.32)


def _bt_win_lamp(o, x0, x1, sill, top, y=0.0, k_night=1.0, d=(-0.25, -0.45, 1.0)):
    tod = _tod(o)
    pan = _panes_y(x0, x1, BT_UP + sill, BT_UP + top, y)
    if tod == 'day': return Lamp(kind='win', c='#fff0d0', k=1.45, soft=10.0, panes=pan, d=_norm3((-0.2, -0.6, 1.0)))
    if tod == 'evening': return Lamp(kind='win', c='#c8bcd8', k=0.75, soft=10.0, panes=pan, d=_norm3((-0.2, -0.4, 1.0)))
    return Lamp(kind='win', c=BT_SODIUM, k=1.25 * k_night * _lv(o, 'street', 1.0), soft=12.0, panes=pan, d=_norm3(d))


def bt_jar(pen, v, x, Y, y, state='full', s_=1.0):
    """Mom's button jar on a surface (plan point; see _bt_jar_flat for the states)."""
    if v.d(x, y) < 0.25: return
    bx, by = v.p(x, Y, y)
    _bt_jar_flat(pen, bx, by, v.s(x, y) * s_, state)


def _bt_jar_flat(pen, bx, by, s, state='full'):
    """The button jar (a squat glass jar, 12 cm) with its base centre at (bx, by), s px per metre: state 'full' (lid on)
    | 'open' (lid off, beside it) | 'black' (two shiny black buttons on top, lid on tight) | 'empty' (lid off) | 'empty_on'."""
    w, h = 0.12 * s, 0.14 * s
    body = rrect(bx - w / 2, by - h, w, h, 0.02 * s)
    pen.fill(oval(bx, by, w * 0.6, 0.014 * s), '#000000', 80, blur=0.01 * s)
    if state in ('full', 'open', 'black'):
        rng = np.random.default_rng(7)
        pen.cv.save(); pen.cv.clipPath(rrect(bx - w / 2 + 0.004 * s, by - h * 0.72, w - 0.008 * s, h * 0.72, 0.015 * s), skia.ClipOp.kIntersect, True)
        for i in range(int(clamp(s / 25, 14, 140))):
            c = ['#d84a3a', '#e8c040', '#4a8ad8', '#5aa860', '#f0ece0', '#8a5a3a', '#c86aa0', '#4a4a56'][i % 8]
            xx, yy = bx + rng.uniform(-0.5, 0.5) * w, by - rng.uniform(0.0, 0.72) * h
            pen.fill(oval(xx, yy, 0.012 * s, 0.008 * s), c)
            if s > 600: pen.fill(oval(xx - 0.003 * s, yy - 0.002 * s, 0.0015 * s), '#000000', 90); pen.fill(oval(xx + 0.003 * s, yy - 0.002 * s, 0.0015 * s), '#000000', 90)
        pen.cv.restore()
        if state == 'black':
            for dx in (-0.018, 0.02): _bt_button(pen, bx + dx * s, by - h * 0.72, max(1.2, 0.012 * s))
    pen.fill(body, '#d8e8f0', 50); pen.line(body, max(0.8, 0.004 * s), '#e8f4ff', 160)
    pen.fill(rect(bx - w * 0.38, by - h * 0.9, w * 0.1, h * 0.72), '#ffffff', 80)
    pen.fill(rrect(bx - w * 0.44, by - h - 0.004 * s, w * 0.88, 0.012 * s, 0.004 * s), '#c8d8e0', 120)     # the threaded neck
    lid = rrect(bx - w * 0.5, by - h - 0.024 * s, w, 0.026 * s, 0.006 * s)
    if state in ('full', 'black', 'empty_on'):
        pen.fill(lid, '#c8a040'); pen.line(lid, max(0.8, 0.003 * s), '#6a5020')
        pen.fill(rect(bx - w * 0.45, by - h - 0.02 * s, w * 0.9, 0.006 * s), '#e8c868', 160)
    elif state in ('open', 'empty'):
        lx, ly = bx + w * 1.05, by
        pen.fill(oval(lx, ly - 0.007 * s, w * 0.52, 0.014 * s), '#c8a040'); pen.line(oval(lx, ly - 0.007 * s, w * 0.52, 0.014 * s), max(0.8, 0.003 * s), '#6a5020')


def _bt_board_art(p_, W, H, state='birthday', k=1.0, ink=1.0):
    """The fridge whiteboard (W x H in any unit, y down): 'birthday' (FRI. O'S BIRTHDAY in Mom's red marker), 'here'
    (+ Owen's MOM IT'S OWEN I'M HERE under FRI, k = how much is written), 'all' (+ the list of everything, k 0..6 items)."""
    u = W / 46.0
    p_.fill(rect(0, 0, W, H), '#f6f8f6'); p_.line(rect(0, 0, W, H), 1.2 * u, '#b8bcc4')
    p_.fill(rect(0, 0, W, H), '#ffffff', 30); p_.linear(rect(0, 0, W, H), 0, 0, W, H, [(0, '#ffffff', 0), (0.4, '#ffffff', 60), (0.55, '#ffffff', 0)])
    p_.fill(rect(W * 0.08, H - 1.6 * u, W * 0.3, 1.2 * u), '#3a3a42')        # the marker tray's marker
    w1 = btext(p_, "FRI. ", 2.5 * u, 7.0 * u, 'hand', 5.4 * u, '#c8262a', 245)
    s2 = 4.6 * u
    while s2 > 2.5 * u and 2.5 * u + w1 + btext_width("O'S BIRTHDAY", 'hand', s2) > 40.0 * u: s2 *= 0.95
    btext(p_, "O'S BIRTHDAY", 2.5 * u + w1, 7.0 * u, 'hand', s2, '#c8262a', 245)
    hx, hy = 43.2 * u, 4.6 * u
    p_.fill(smooth([(hx, hy + 2.0 * u), (hx - 1.8 * u, hy), (hx - 1.0 * u, hy - 1.5 * u), (hx, hy - 0.6 * u), (hx + 1.0 * u, hy - 1.5 * u), (hx + 1.8 * u, hy)]), '#c8262a', 230)
    if state == 'birthday': return
    def kid(s, x, y, size, frac):
        if frac <= 0: return
        w = btext_width(s, 'kid', size)
        p_.cv.save(); p_.cv.clipRect(skia.Rect.MakeXYWH(x - u, y - size * 1.2, w * frac + u, size * 1.6), skia.ClipOp.kIntersect, True)
        btext(p_, s, x, y, 'kid', size, '#1a1a8a', int(245 * ink)); btext(p_, s, x + 0.12 * u, y, 'kid', size, '#1a1a8a', int(120 * ink))
        p_.cv.restore()
    kh = clamp(k if state == 'here' else 1.0)
    kid("MOM IT'S OWEN", 3.0 * u, 13.8 * u, 4.6 * u, clamp(kh * 2.0))
    kid("I'M HERE", 3.0 * u, 19.6 * u, 4.6 * u, clamp(kh * 2.0 - 1.0))
    if state != 'all': return
    items = [("THE CHAT.", 2.5, 26.0), ("THE PHOTO.", 24.5, 26.0), ("THE COAT.", 2.5, 31.6), ("THE CAR.", 24.5, 31.6), ("2 A.M.", 2.5, 37.2),
             ("I WISHED FOR A", 2.5, 42.8), ("DIFFERENT MOM.", 2.5, 48.2)]
    kk = k * 6.0 / 6.0
    for i, (s, x, y) in enumerate(items):
        j = min(i, 5)
        frac = clamp(k - j) if i < 5 else clamp((k - 5.0) * 2.0 - (i - 5))
        kid(s, x * u, y * u, 3.5 * u, frac)


def _bt_laptop(pen, v, x, Y, y, face=(-1.0, 0.0), on=1.0, open_=1.0, c='#3a3c44'):
    """Mom's laptop on the table (its screen faces `face`, the plan direction of whoever uses it)."""
    fx, fy = face; rx, ry = -fy, fx
    W2, D2 = 0.17, 0.12
    def P(u, n, h): return v.p(x + rx * u - fx * n, Y + h, y + ry * u - fy * n)
    base = [P(-W2, -D2, 0), P(W2, -D2, 0), P(W2, D2, 0), P(-W2, D2, 0)]     # n + = away from the user
    pen.fill(poly([P(-W2, -D2, 0.02), P(W2, -D2, 0.02), P(W2, D2, 0.02), P(-W2, D2, 0.02)]), lit('#8a8c94', (x, Y, y), (0, 1, 0)))
    pen.fill(poly(base), '#2a2c30', 200)
    if open_ <= 0.05: return
    th = math.radians(105 * open_); hh = 0.23
    top = lambda u: P(u, D2 - hh * math.cos(th), 0.02 + hh * math.sin(th))
    lid = [P(-W2, D2, 0.02), P(W2, D2, 0.02), top(W2), top(-W2)]
    back = v.d(x - fx * 0.3, y - fy * 0.3) > v.d(x + fx * 0.3, y + fy * 0.3)   # True: we see the screen side
    pen.fill(poly(lid), lit(c, (x, Y + 0.12, y), (fx, 0, fy) if back else (-fx, 0, -fy))); pen.line(poly(lid), 0.8)
    if back:
        sc = [lerp2(lid[0], lid[3], 0.06, lid[1], 0.06), lerp2(lid[1], lid[2], 0.06, lid[0], 0.06), lerp2(lid[2], lid[1], 0.06, lid[3], 0.06), lerp2(lid[3], lid[0], 0.06, lid[2], 0.06)]
        pen.fill(poly(sc), mix('#0a0e18', BT_LAPTOP, on * 0.85))
        if on > 0.05:
            cx_ = sum(q[0] for q in sc) / 4; cy_ = sum(q[1] for q in sc) / 4
            for k in range(4): pen.fill(rect(cx_ - 0.3 * abs(sc[1][0] - sc[0][0]), cy_ - 0.25 * abs(sc[3][1] - sc[0][1]) + k * 0.12 * abs(sc[3][1] - sc[0][1]),
                                             0.5 * abs(sc[1][0] - sc[0][0]), max(1.0, 0.04 * abs(sc[3][1] - sc[0][1]))), '#ffffff', int(120 * on))
    else:
        cx_ = sum(q[0] for q in lid) / 4; cy_ = sum(q[1] for q in lid) / 4
        pen.fill(oval(cx_, cy_, 0.02 * v.s(x, y)), '#c8ccd4', 120)


def lerp2(a, b, k, c, k2):
    """A point k of the way a -> b, nudged k2 toward c (screen-space inset for a quad's inner rectangle)."""
    x = a[0] + (b[0] - a[0]) * k; y = a[1] + (b[1] - a[1]) * k
    return (x + (c[0] - a[0]) * k2, y + (c[1] - a[1]) * k2)


def _bt_headset(pen, v, x, Y, y, s_=1.0):
    s = v.s(x, y) * s_
    if v.d(x, y) < 0.25: return
    px, py = v.p(x, Y, y)
    pen.line(smooth([(px - 0.07 * s, py), (px - 0.06 * s, py - 0.07 * s), (px, py - 0.095 * s), (px + 0.06 * s, py - 0.07 * s), (px + 0.07 * s, py)], False), max(1.2, 0.012 * s), '#26282e')
    for sd in (-1, 1): pen.fill(oval(px + sd * 0.07 * s, py - 0.01 * s, 0.03 * s, 0.022 * s), '#33363e'); pen.line(oval(px + sd * 0.07 * s, py - 0.01 * s, 0.03 * s, 0.022 * s), 0.8)
    pen.line(smooth([(px - 0.07 * s, py), (px - 0.03 * s, py + 0.02 * s), (px + 0.01 * s, py + 0.015 * s)], False), max(0.8, 0.005 * s), '#26282e')
    pen.fill(oval(px + 0.012 * s, py + 0.015 * s, 0.008 * s), '#1a1a1e')


def _bt_mug(pen, v, x, Y, y, c='#e8e0d0', s_=1.0):
    if v.d(x, y) < 0.25: return
    s = v.s(x, y) * s_; px, py = v.p(x, Y, y)
    m = rrect(px - 0.04 * s, py - 0.095 * s, 0.08 * s, 0.095 * s, 0.01 * s)
    pen.fill(m, lit(c, (x, Y + 0.05, y), None)); pen.line(m, 0.8)
    pen.line(oval(px + 0.05 * s, py - 0.05 * s, 0.018 * s, 0.025 * s), max(1.0, 0.008 * s), lit(c, (x, Y, y), None))
    pen.fill(oval(px, py - 0.095 * s, 0.04 * s, 0.008 * s), '#3a2216')


def _bt_tab_on_carton(pen, v, x, Y, y, face=(1.0, 0.0), on=1.0):
    """Owen's tablet propped on the milk carton (its screen toward `face`, where he sits); Mom sees its back."""
    fx, fy = face
    cb = Box(x - fx * 0.06, y - fy * 0.06, 0.095, 0.095, Y, Y + 0.24, 0)
    draw_box(pen, v, cb, {'all': dict(fill='#f2f0ea', art=lambda p_, W, H: (p_.fill(rect(0, 0, W, H * 0.35), '#3a7ac8'), btext(p_, 'MILK', W / 2, H * 0.6, 'sans_b', W * 0.26, '#2a5aa8', 230, 'center'))),
                         'top': '#e8e4dc'}, lw=0.8)
    rx, ry = -fy, fx
    def P(u, h, n): return v.p(x + rx * u + fx * n, Y + h, y + ry * u + fy * n)
    q = [P(-0.12, 0.0, 0.07), P(0.12, 0.0, 0.07), P(0.12, 0.2, -0.0), P(-0.12, 0.2, -0.0)]
    front = v.d(x + fx * 0.5, y + fy * 0.5) < v.d(x, y)
    pen.fill(poly(q), '#202228' if not front else '#121318'); pen.line(poly(q), 0.8)
    if front and on > 0.02:
        sc = [lerp2(q[0], q[1], 0.06, q[3], 0.08), lerp2(q[1], q[0], 0.06, q[2], 0.08), lerp2(q[2], q[3], 0.06, q[1], 0.08), lerp2(q[3], q[2], 0.06, q[0], 0.08)]
        pen.fill(poly(sc), mix('#0a0e18', BT_TAB, on * 0.85))


def _bt_dinner(pen, v):
    """Thursday dinner: Owen's favourite (spaghetti and meatballs) in a big bowl, two plates set, the chair at Mom's end."""
    for (x, y) in ((4.12, 2.35), (5.12, 2.35)):
        if v.d(x, y) < 0.3: continue
        s = v.s(x, y); px, py = v.p(x, BT_UP + 0.755, y)
        pen.fill(oval(px, py, 0.13 * s, 0.13 * s * _flat(v, x, y)), lit('#f4f0e6', (x, BT_UP + 0.76, y), (0, 1, 0))); pen.line(oval(px, py, 0.13 * s, 0.13 * s * _flat(v, x, y)), 0.7)
    x, y = 4.62, 2.3
    if v.d(x, y) > 0.3:
        s = v.s(x, y); px, py = v.p(x, BT_UP + 0.76, y); f = _flat(v, x, y)
        pen.fill(rrect(px - 0.14 * s, py - 0.07 * s, 0.28 * s, 0.07 * s + 0.12 * s * f, 0.05 * s), lit('#4a7ab8', (x, BT_UP + 0.8, y), None))
        pen.fill(oval(px, py - 0.07 * s, 0.14 * s, 0.13 * s * f), '#e8b860')
        for k in range(6): pen.fill(oval(px + (k % 3 - 1) * 0.06 * s, py - 0.07 * s + (k // 3 - 0.5) * 0.05 * s * f, 0.022 * s), '#8a3a22')
        pen.fill(oval(px, py - 0.07 * s, 0.1 * s, 0.07 * s * f), '#c83a22', 120)


def _flat(v, x, y):
    """How much a horizontal disc at (x, y) opens up for this camera (0 edge-on .. 1 from above)."""
    d = max(0.3, v.d(x, y))
    return clamp(abs(v.cam_h - BT_UP - 0.75) / math.hypot(d, v.cam_h - BT_UP - 0.75) + 0.05, 0.05, 1.0)


def bt_pendant(pen, v, swing=0.0, k=0.0):
    """The pendant lamp over the table: cord from the ceiling, a cone shade (bottom 1.62 m above the floor); swing (deg)
    rocks it along the table's long axis (x)."""
    cx, cy = BT_LAMPP; Ytop = BT_UP + BT_CEIL; L = 0.98
    a = math.radians(swing)
    sx = cx + math.sin(a) * L; sY = Ytop - math.cos(a) * L                  # the shade's top centre
    if v.d(cx, cy) < 0.3: return
    pen.seg(v.p(cx, Ytop, cy), v.p(sx, sY, cy), max(1.0, 0.01 * v.s(cx, cy)), '#2a2a2a')
    pen.fill(oval(*v.p(cx, Ytop - 0.01, cy), 0.05 * v.s(cx, cy), 0.012 * v.s(cx, cy)), '#3a3a3a')
    bot = []; topp = []
    for i in range(18):
        th = i / 18.0 * 2 * math.pi
        dx, dy = math.cos(th), math.sin(th)
        bx_ = sx + math.sin(a) * 0.24 + dx * 0.2 * math.cos(a); bY = sY - math.cos(a) * 0.24 + dx * 0.2 * math.sin(a)
        bot.append(v.p(bx_, bY, cy + dy * 0.2)); topp.append(v.p(sx + dx * 0.05 * math.cos(a), sY + dx * 0.05 * math.sin(a), cy + dy * 0.05))
    hull = _hull(bot + topp)
    pen.fill(poly(hull), lit('#2f5a4a', (sx, sY - 0.1, cy), None)); pen.line(poly(hull), 1.0)
    below = v.cam_h < sY - 0.24
    if below or k > 0.05:
        pen.fill(poly(bot), mix('#f4e6c8', '#fff4dc', k) if below else '#e8d8b8', 255 if below else int(140 * k))
    if k > 0.02:
        bx, by = v.p(sx + math.sin(a) * 0.24, sY - math.cos(a) * 0.24, cy)
        pen.glow(bx, by, 0.5 * v.s(cx, cy), '#ffd9a0', int(90 * k))


def _hull(pts):
    pts = sorted(set((round(p[0], 2), round(p[1], 2)) for p in pts))
    if len(pts) < 3: return pts
    def cr(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def bt_mirror(v, x, Y, y):
    """Where plan point (x, Y, y) shows in the black microwave door (its mirror across the door plane x = BT_MX), as
    (sx, sy, px_per_m, depth). Draw a figure's reflection there (CH.draw(..., reflection=True)), mirrored left-right."""
    X = 2 * BT_MX - x
    sx, sy = v.p(X, Y, y)
    return sx, sy, v.s(X, y), v.d(X, y)


def bt_micro_quad(v):
    y0, y1, Y0, Y1 = BT_MGLASS
    return [v.p(BT_MX - 0.002, BT_UP + Y0, y1), v.p(BT_MX - 0.002, BT_UP + Y0, y0), v.p(BT_MX - 0.002, BT_UP + Y1, y0), v.p(BT_MX - 0.002, BT_UP + Y1, y1)]


def _bt_micro_layer(v, o):
    """The microwave door glass: black, glossy, with the kitchen reflected in it (the lamp, the laptop's glow, the window,
    the table edge) and o['refl'](pen, t, clip_path) for the figures' reflections (bt_mirror gives their points)."""
    q = bt_micro_quad(v)
    def draw(pen, t):
        path = poly(q)
        pen.fill(path, '#060608')
        pen.cv.save(); pen.cv.clipPath(path, skia.ClipOp.kIntersect, True)
        night = _tod(o) == 'night'
        def M(x, Y, y): return v.p(2 * BT_MX - x, Y, y)
        tab = [M(BT_TABLE.cx - 0.65, BT_UP + 0.75, 1.93), M(BT_TABLE.cx + 0.65, BT_UP + 0.75, 1.93), M(BT_TABLE.cx + 0.65, BT_UP + 0.75, 2.77), M(BT_TABLE.cx - 0.65, BT_UP + 0.75, 2.77)]
        pen.fill(poly(tab), '#3a2a1e', 120)
        for (wx0, wx1) in ((BT_KWIN[0], BT_KWIN[1]), (BT_LWIN[0], BT_LWIN[1])):
            wq = [M(wx0, BT_UP + 0.95, 0.0), M(wx1, BT_UP + 0.95, 0.0), M(wx1, BT_UP + 2.1, 0.0), M(wx0, BT_UP + 2.1, 0.0)]
            pen.fill(poly(wq), '#ffb468' if night else '#c8d4e8', 40)
        mq = [M(BT_MDOOR[0], BT_UP, 5.2), M(BT_MDOOR[1], BT_UP, 5.2), M(BT_MDOOR[1], BT_UP + 2.05, 5.2), M(BT_MDOOR[0], BT_UP + 2.05, 5.2)]
        pen.line(poly(mq), 2.0, '#4a4a50', 120)
        lk = _kfn(o.get('lamp', 0.0), 990)(t); kk = _kfn(o.get('laptop', 0.0), 991)(t)
        if lk > 0.02:
            lx, ly = M(BT_LAMPP[0], BT_UP + 1.62, BT_LAMPP[1]); pen.glow(lx, ly, 60, '#ffd9a0', int(120 * lk)); pen.fill(oval(lx, ly, 14, 5), '#fff4dc', int(200 * lk))
        if kk > 0.02:
            lx, ly = M(4.1, BT_UP + 0.9, 2.35); pen.glow(lx, ly, 40, BT_LAPTOP, int(110 * kk))
        if callable(o.get('refl')): o['refl'](pen, t, path)
        cq = [M(5.6, BT_UP + 2.48, 1.2), M(5.6, BT_UP + 2.48, 4.0), M(3.6, BT_UP + 2.48, 4.0), M(3.6, BT_UP + 2.48, 1.2)]
        pen.fill(poly(cq), '#c8c0b0' if not night else '#3a4060', 26)      # the ceiling
        pen.fill(path, '#000000', 60)                                       # the dark tint over everything reflected
        pen.cv.restore()
        x0 = min(p_[0] for p_ in q); x1 = max(p_[0] for p_ in q); y0 = min(p_[1] for p_ in q); y1 = max(p_[1] for p_ in q)
        pen.cv.save(); pen.cv.clipPath(path, skia.ClipOp.kIntersect, True)
        pen.linear(rect(x0, y0, x1 - x0, y1 - y0), x0, y0, x1, y1, [(0, '#ffffff', 0), (0.28, '#ffffff', 34), (0.36, '#ffffff', 0), (0.62, '#ffffff', 0), (0.66, '#ffffff', 18), (0.7, '#ffffff', 0)])
        pen.cv.restore()
        pen.line(path, 1.2, '#2a2a2e')
    lay = Layer(max(0.3, v.d(BT_MX, 3.0)), draw, 'micro_glass', blur=None)
    lay.order = max(0.3, v.d(BT_MX, 3.0)) - 0.05
    return lay


def _bt_clock_layer(v, o):
    """The oven clock (green digits on the stove's backguard) and the microwave's clock: emissive. o['clock'] '11:58' or f(t)."""
    def draw(pen, t):
        s_ = o.get('clock', '6:42'); s_ = s_(t) if callable(s_) else s_
        for (x, Y, y, sz) in ((7.535, BT_UP + 1.02, BT_STOVE.cy, 0.045), (BT_MX - 0.005, BT_UP + 1.48, 2.71, 0.022)):
            if v.d(x, y) < 0.3 or v.p(x, Y, y)[0] < -200: continue
            if not v.visible((x, Y, y), (-1, 0, 0)): continue
            px, py = v.p(x, Y, y); s = v.s(x, y)
            pen.fill(rrect(px - 0.07 * s * sz / 0.045, py - 0.03 * s * sz / 0.045, 0.14 * s * sz / 0.045, 0.06 * s * sz / 0.045, 0.006 * s), '#060806')
            pen.glow(px, py, 0.08 * s * sz / 0.045, '#5af08a', 60)
            btext(pen, s_, px, py + 0.016 * s * sz / 0.045, 'vhs', sz * s, '#6aff9a', 245, 'center')
    lay = Layer(1.0, draw, 'oven_clock', blur=None); lay.order = max(0.25, v.d(BT_STOVE.cx - 0.45, BT_STOVE.cy))
    return lay


def _bt_closet_list_art(ink=None):
    """The Brave List as it looks on the inside of the closet door at room scale (the insert has the full one)."""
    ink = list(ink) if ink is not None else [1.0] * 7
    def art(p_, W, H):
        x0, y0, w, h = W * 0.14, H * 0.12, W * 0.72, H * 0.46
        p_.fill(rect(x0, y0, w, h), '#f6f0e0'); p_.line(rect(x0, y0, w, h), 0.6, '#c8b890')
        for (c, d) in (('#e84a3a', 0), ('#3a9a4a', 1.2), ('#e8b830', 2.4)):
            p_.line(rect(x0 + 1.5 + d, y0 + 1.5 + d, w - 3 - 2 * d, h - 3 - 2 * d), 0.9, c, 220)
        btext(p_, 'THE BRAVE LIST', x0 + w / 2, y0 + 8, 'kid', 4.2, '#e84a3a', 240, 'center')
        for i in range(7):
            k = clamp(ink[i] if i < len(ink) else 1.0)
            c = mix(BT_PEN_PALE, BT_PEN, k)
            yy = y0 + 14 + i * (h - 18) / 7.0
            p_.fill(rect(x0 + 6, yy, w * (0.62 + 0.25 * ((i * 7) % 3) / 2), 1.1), c, 230)
            btext(p_, str(i + 1) + '.', x0 + 3, yy + 1.6, 'caveat_b', 3.0, c, 240)
    return art


def bt_closet_door(ink=None):
    D = Door((-3.6, BT_CLOSET[0]), BT_CLOSET[1] - BT_CLOSET[0], BT_CLOSET[2], (0.0, 1.0), -1, BT_UP,
             art_a=door_art('four', 'right', bolt=False), art_b=_compose(door_art('four', 'left', bolt=False), _bt_closet_list_art(ink)), col='#efe9dc')
    return D


def _compose(*arts):
    def art(p_, W, H):
        for a in arts: a(p_, W, H)
    return art


def bt_owen_door():
    return Door((0.0, BT_ODOOR[1]), BT_ODOOR[1] - BT_ODOOR[0], BT_ODOOR[2], (0.0, -1.0), -1, BT_UP,
                art_a=_compose(door_art('six', 'left', bolt=False), lambda p_, W, H: (p_.fill(rrect(W * 0.3, H * 0.18, W * 0.4, H * 0.1, 2), '#3a6ac8'),
                                                                                    btext(p_, 'OWEN', W / 2, H * 0.25, 'kid', H * 0.05, '#ffffff', 240, 'center'))),
                art_b=door_art('six', 'right', bolt=False))


def bt_front_door():
    return Door((0.0, BT_FDOOR[1]), BT_FDOOR[1] - BT_FDOOR[0], BT_FDOOR[2], (0.0, -1.0), 1, BT_UP,
                art_a=door_art('six', 'left', peep=True), art_b=door_art('six', 'right', peep=True, chain=True), col='#5a3a2a')


def bt_mom_door():
    return Door((BT_MDOOR[0], 5.2), BT_MDOOR[1] - BT_MDOOR[0], BT_MDOOR[2], (1.0, 0.0), 1, BT_UP,
                art_a=door_art('six', 'right', bolt=False), art_b=door_art('six', 'left', bolt=False))


# ====================================================================================================== the apartment: rooms
def _bt_main_cfg(o):
    tod = _tod(o)
    def lights(o):
        amb = _bt_amb(o)
        steady = [_bt_win_lamp(o, BT_LWIN[0], BT_LWIN[1], BT_LWIN[2], BT_LWIN[3], 0.0, 0.85, (-0.45, -0.4, 1.0)),
                  _bt_win_lamp(o, BT_KWIN[0], BT_KWIN[1], BT_KWIN[2], BT_KWIN[3], 0.0, 0.6, (-0.7, -0.4, 1.0))]
        TA = o.get('tablet_at', (5.18, BT_UP + 0.95, 2.35))
        var = [('lamp', [Lamp(BT_LAMPP[0], BT_UP + 1.5, BT_LAMPP[1], 3.4, '#ffd9a0', 1.6, (1.0, 0.55, 0.2), fall=1.4)], _kfn(o.get('lamp', 0.0), 801)),
               ('ceil', [Lamp(5.6, BT_UP + 2.4, 2.6, 7.0, '#fff0d8', 1.15, (1.0, 0.5, 0.2), fall=1.3),
                         Lamp(1.6, BT_UP + 2.4, 2.6, 5.5, '#fff0d8', 0.7, (1.0, 0.5, 0.2), fall=1.3)], _kfn(o.get('ceil', 0.0), 802)),
               ('living', [Lamp(0.55, BT_UP + 1.35, 2.75, 3.6, BT_WARM, 1.3, (1.0, 0.8, 0.6), fall=1.5)], _kfn(o.get('living', 0.0), 803)),
               ('laptop', [Lamp(4.05, BT_UP + 0.98, 2.35, 2.4, BT_LAPTOP, 1.5, (0.8, 1.0, 0.8), fall=1.5)], _kfn(o.get('laptop', 0.0), 804)),
               ('tablet', [Lamp(TA[0], TA[1], TA[2], 1.7, BT_TAB, 1.2, (0.8, 1.0, 0.8), fall=1.5)], _kfn(o.get('tablet', 0.0), 805)),
               ('flash', [Lamp(*o.get('flash_at', (1.0, BT_UP + 1.4, 3.0)), R=5.0, c='#fff4dc', k=1.6, fall=1.4)], _kfn(o.get('flash', 0.0), 806))]
        if tod == 'night':                                                  # the oven clock and the fridge's little glow keep the corner readable
            steady.append(Lamp(7.4, BT_UP + 1.0, BT_STOVE.cy, 1.1, '#5af08a', 0.35, fall=1.6))
        return amb, steady, var
    def west(p_, W, H):                                                     # run (0, 0) -> (0, 5.2): u = y
        _light_switch(p_, (BT_FDOOR[0] - 0.15) * 100, H - 120, True)
        for k in range(3): p_.fill(oval((BT_FDOOR[0] - 0.3) * 100 + k * 12, H - 165, 2.5), '#6a5a4a')       # coat hooks
        p_.fill(rrect(0.6 * 100, H - 175, 70, 50, 2), '#4a3a2a'); p_.fill(rrect(0.6 * 100 + 4, H - 171, 62, 42, 1), '#c8b898')  # a framed photo
        p_.fill(oval(0.6 * 100 + 22, H - 152, 7), '#8a6a4a'); p_.fill(oval(0.6 * 100 + 44, H - 155, 5), '#5a7ab8')
    def back(p_, W, H):                                                     # run (0, 5.2) -> (7.6, 5.2): u = x
        _wall_clock(p_, 2.35 * 100, H - 200, 14, 6, 42)
        p_.fill(rect(1.95 * 100, H - 150, 52, 64), '#f4f0e4'); p_.line(rect(1.95 * 100, H - 150, 52, 64), 0.6)   # the calendar
        for r_ in range(4):
            for c_ in range(7): p_.line(rect(1.95 * 100 + 3 + c_ * 6.6, H - 128 + r_ * 9, 6.6, 9), 0.3, '#8a8a8a', 160)
        p_.line(oval(1.95 * 100 + 3 + 4 * 6.6 + 3.3, H - 128 + 3 * 9 + 4.5, 4.5, 4), 0.8, '#c8262a')       # Friday circled
        for k in range(int(1.24 * 100 / 15)): p_.fill(rect((6.36 + k * 0.15) * 100, H - 145, 14, 52), '#e8eef0' if k % 2 else '#d8e4e8')  # backsplash
    def east(p_, W, H):                                                     # run (7.6, 5.2) -> (7.6, 0): u = 5.2 - y
        for k in range(int(4.1 * 100 / 15)): p_.fill(rect((5.2 - 4.6 + k * 0.15) * 100, H - 145, 14, 52), '#e8eef0' if k % 2 else '#d8e4e8')
    def front(p_, W, H):                                                    # run (7.6, 0) -> (0, 0): u = 7.6 - x
        for (a, b) in (BT_LWIN[:2], BT_KWIN[:2]):                            # curtains beside the windows
            for xx in ((7.6 - a) * 100 + 4, (7.6 - b) * 100 - 30):
                p_.fill(rect(xx, H - 222, 26, 160), '#b8a878' if (a, b) == BT_KWIN[:2] else '#8a6a8a', 210)
                for k in range(4): p_.fill(rect(xx + 3 + k * 6, H - 222, 1.4, 160), '#000000', 30)
    wins = {'front': [(BT_LWIN[0], 0.0, BT_LWIN[1], 0.0, BT_LWIN[2], BT_LWIN[3], (2, 2)), (BT_KWIN[0], 0.0, BT_KWIN[1], 0.0, BT_KWIN[2], BT_KWIN[3], (2, 2))]}
    holes = {'west': [(0.0, BT_ODOOR[0], 0.0, BT_ODOOR[1], 0.0, BT_ODOOR[2]), (0.0, BT_FDOOR[0], 0.0, BT_FDOOR[1], 0.0, BT_FDOOR[2])],
             'back': [(BT_MDOOR[0], 5.2, BT_MDOOR[1], 5.2, 0.0, BT_MDOOR[2])]}
    runs = _rect_runs(BT_MAIN, holes, wins, {'west': west, 'back': back, 'east': east, 'front': front})
    rug = _bu_rug_art(BT_MAIN[0], BT_MAIN[3], 1.5, 3.95, 1.05, 1.2, ('#8a4a4a', '#d8c090', '#4a6a8a', '#f0e8d8'))
    def floor_art(p_, W, H):
        rug(p_, W, H)
        p_.fill(rect(3.55 * 100, 0, (7.6 - 3.55) * 100, H), '#c8c0b0', 255)    # the kitchen's vinyl tiles
        for i in range(int((7.6 - 3.55) / 0.3) + 1):
            for j in range(int(5.2 / 0.3) + 1):
                if (i + j) % 2: p_.fill(rect(3.55 * 100 + i * 30, j * 30, 30, 30), '#b4ac9c')
        p_.fill(rect(0.05 * 100, (5.2 - 4.6) * 100 - 30, 60, 60), '#5a4a3a', 200)    # the doormat inside the front door
    def pieces(o):
        P = []
        # the counters, the stove, the microwave, the sink, the cabinets
        def counters(pen, v):
            for B in (BT_CNT_E, BT_CNT_B):
                draw_box(pen, v, B, {'top': dict(fill=BT_PAL['cnt'], art=lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'grunge', 0.3, 'overlay', 1.0)),
                                     'front': dict(fill=BT_PAL['cab'], art=lambda p_, W, H: [p_.line(rect(6 + k * W / max(1, int(W / 50)), 10, W / max(1, int(W / 50)) - 12, H - 20), 1.0, '#000000', 90) for k in range(max(1, int(W / 50)))]),
                                     'all': mix(BT_PAL['cab'], '#000000', 0.15)}, lw=1.0)
            sk = Box(6.95, 4.92, 0.6, 0.42, BT_UP + 0.8, BT_UP + 0.93, 0)
            draw_box(pen, v, sk, {'top': '#9aa4b0', 'all': '#8a949e'}, lw=0.8, skip=('bottom',))
            A = (6.95, BT_UP + 0.93, 5.12); B_ = (6.95, BT_UP + 1.2, 5.12)
            if v.d(A[0], A[2]) > 0.3: pen.seg(v.p(*A), v.p(*B_), max(1.0, 0.025 * v.s(A[0], A[2])), '#c8ccd4')
        P.append(Piece('counters', (7.1, BT_UP + 0.5, 3.4), counters, block=BT_CNT_E.footprint() + BT_CNT_B.footprint()[:0]))
        P.append(Piece('counter_b', (BT_CNT_B.cx, BT_UP + 0.5, BT_CNT_B.cy), lambda pen, v: None, block=BT_CNT_B.footprint()))
        st = BT_STOVE
        def stove(pen, v):
            draw_box(pen, v, st, {'front': dict(fill='#e8e4dc', art=lambda p_, W, H: (p_.fill(rect(8, 24, W - 16, H * 0.5), '#1e1e22'), p_.line(rect(8, 24, W - 16, H * 0.5), 1.0),
                                                                                    p_.fill(rect(10, 10, W - 20, 5), '#9a9aa0'))),
                                  'top': dict(fill='#1a1a1c', art=lambda p_, W, H: [p_.line(oval(W * (0.28 + 0.44 * (k % 2)), H * (0.3 + 0.4 * (k // 2)), 10), 1.4, '#5a5a5a') for k in range(4)]),
                                  'all': '#d8d4cc'}, lw=1.0)
            bg = Box(7.55, st.cy, 0.76, 0.1, BT_UP + 0.92, BT_UP + 1.12, -90)    # the backguard with the oven clock
            draw_box(pen, v, bg, {'front': dict(fill='#d8d4cc', art=lambda p_, W, H: [p_.fill(oval(W * (0.15 + 0.12 * k), H * 0.5, 3.2), '#2a2a2e') for k in (0, 1, 5, 6)]), 'all': '#c8c4bc'}, lw=0.8)
        P.append(Piece('stove', (st.cx, BT_UP + 0.5, st.cy), stove, block=st.footprint()))
        mi = BT_MICRO
        def micro(pen, v):
            def art(p_, W, H):
                p_.fill(rect(0, 0, W, H), '#1a1a1e')
                p_.fill(rrect(4, 4, 37, 24, 1.5), '#050507')                 # the door glass (the live layer paints the reflection over it)
                p_.fill(rect(45, 5, 13, 24), '#232328')
                for r_ in range(3):
                    for c_ in range(3): p_.fill(rrect(46.5 + c_ * 3.8, 13 + r_ * 4.4, 2.8, 3, 0.6), '#3a3a42')
                p_.fill(rect(42, 2, 1.2, 30), '#2e2e34')
            draw_box(pen, v, mi, {'front': dict(fill='#1a1a1e', art=art), 'all': '#26262a', 'top': '#2a2a30'}, lw=1.0)
        rs = BT_RISER
        def riser_micro(pen, v):                                            # one piece: the riser first, the microwave on it
            draw_box(pen, v, rs, {'all': '#6a4a30', 'front': dict(fill='#3a281a', art=lambda p_, W, H: (
                p_.line(rect(2, 2, W - 4, H - 4), 3.0, '#6a4a30'), p_.fill(rect(2, H / 2 - 1.5, W - 4, 3), '#6a4a30'), p_.fill(rrect(8, H / 2 + 3, 22, H / 2 - 8, 2), '#c8a060'),
                p_.fill(rrect(36, 6, 16, H / 2 - 9, 2), '#e8e0d0')))}, lw=0.8)
            micro(pen, v)
        P.append(Piece('microwave', (mi.cx, BT_UP + 1.2, mi.cy), riser_micro, block=rs.footprint()))
        for (cy_, w_, Yb) in ((1.25, 1.2, 1.48), (3.4, 2.2, 1.64)):
            up = Box(7.43, cy_, w_, 0.34, BT_UP + Yb, BT_UP + 2.25, -90)
            P.append(Piece('cab_%d' % int(cy_ * 10), (7.43, BT_UP + 1.9, cy_), (lambda up: lambda pen, v: draw_box(pen, v, up, {'all': BT_PAL['cab'], 'front': dict(fill=BT_PAL['cab'], art=lambda p_, W, H: [
                p_.line(rect(4 + k * W / max(1, int(W / 45)), 6, W / max(1, int(W / 45)) - 8, H - 12), 1.0, '#000000', 90) for k in range(max(1, int(W / 45)))])}, lw=1.0, skip=('bottom',)))(up)))
        # the fridge (bottom freezer, the whiteboard) and the tall cabinet: the GAP between them
        fr = BT_FRIDGE
        bstate = o.get('board', 'birthday'); bk = o.get('board_k', 1.0)
        def fridge(pen, v):
            def art(p_, W, H):
                p_.fill(rect(0, 0, W, H), '#e8eae8'); p_.line(rect(2, H - 62, W - 4, 2), 1.0, '#9a9a9a')
                p_.fill(rect(4, 30, 3, 50), '#b8b8b8'); p_.fill(rect(W / 2 - 14, H - 56, 28, 3), '#b8b8b8')
                for (dx, dy, c) in ((0.66, 0.08, '#f8f0d8'), (0.1, 0.52, '#d8f0f8')):
                    p_.fill(rect(W * dx, H * dy, 18, 22), c); p_.line(rect(W * dx, H * dy, 18, 22), 0.4)
                if bstate and not callable(bk):
                    p_.cv.save(); p_.cv.translate(W / 2 - 23, 182 - 165); _bt_board_art(p_, 46, 60, bstate, bk); p_.cv.restore()
            draw_box(pen, v, fr, {'front': dict(fill='#e8eae8', art=art), 'all': '#d4d6d4', 'top': '#c8cac8'}, lw=1.0)
        P.append(Piece('fridge', (fr.cx, BT_UP + 0.9, fr.cy), fridge, block=fr.footprint()))
        tc = BT_TALL
        P.append(Piece('tall_cabinet', (tc.cx, BT_UP + 1.0, tc.cy), lambda pen, v: draw_box(pen, v, tc, {'all': BT_PAL['cab'], 'front': dict(fill=BT_PAL['cab'], art=lambda p_, W, H: (
            p_.line(rect(5, 6, W - 10, H * 0.55), 1.0, '#000000', 90), p_.line(rect(5, H * 0.57, W - 10, H * 0.4), 1.0, '#000000', 90), p_.fill(rect(W - 12, H * 0.5, 3, 18), '#c8c8c8')))}, lw=1.0), block=tc.footprint()))
        def gap(pen, v):                                                    # the slot beside the fridge: deep shadow to the ceiling
            q = [v.p(BT_GAP[0], BT_UP, 5.19), v.p(BT_GAP[1], BT_UP, 5.19), v.p(BT_GAP[1], BT_UP + BT_CEIL, 5.19), v.p(BT_GAP[0], BT_UP + BT_CEIL, 5.19)]
            if v.d(5.3, 5.19) < 0.3: return
            pen.fill(poly(q), '#050608', 235)
            qf = [v.p(BT_GAP[0], BT_UP + 0.002, 5.19), v.p(BT_GAP[1], BT_UP + 0.002, 5.19), v.p(BT_GAP[1], BT_UP + 0.002, 4.45), v.p(BT_GAP[0], BT_UP + 0.002, 4.45)]
            pen.fill(poly(qf), '#050608', 150)
        P.append(Piece('gap', (5.32, BT_UP + 1.2, 5.05), gap))
        # the table, the chairs, the stool; what is on the table
        tb = BT_TABLE
        P.append(Piece('table', (tb.cx, BT_UP + 0.4, tb.cy), lambda pen, v: draw_parts(pen, v, _bt_tparts(tb, '#a8845a', apron=0.06)), block=tb.footprint()))
        for (nm, cx, cy, fa) in (('chair_mom', 3.68, 2.35, 90), ('chair_owen', 5.52, 2.35, -90), ('chair_n', 4.6, 3.03, 0)):
            ch = Box(cx, cy, 0.42, 0.42, BT_UP, BT_UP + 0.46, fa)
            def chair(pen, v, ch=ch):
                draw_parts(pen, v, _bt_tparts(ch, '#7a5a3a', apron=0.03, thick=0.04, legw=0.035))
                draw_box(pen, v, sub(ch, -0.2, 0.2, -0.21, -0.17, BT_UP + 0.46, BT_UP + 0.94), {'all': '#7a5a3a'}, lw=0.7)
            P.append(Piece(nm, (cx, BT_UP + 0.3, cy), chair, block=ch.footprint()))
        stl = Box(6.6, 2.9, 0.34, 0.34, BT_UP + 0.62, BT_UP + 0.66, 0)
        def stool(pen, v):
            for (u, n) in ((-0.13, -0.13), (0.13, -0.13), (0.13, 0.13), (-0.13, 0.13)):
                a_ = stl.at(u, n, BT_UP); b_ = stl.at(u * 0.6, n * 0.6, BT_UP + 0.62)
                pen.seg(v.p(*a_), v.p(*b_), max(1.0, 0.02 * v.s(stl.cx, stl.cy)), '#3a3a3e')
            draw_box(pen, v, stl, {'all': '#3a3a3e', 'top': '#4a4a52'}, lw=0.8)
        P.append(Piece('stool', (stl.cx, BT_UP + 0.4, stl.cy), stool, block=stl.footprint()))
        def on_table(pen, v):
            Y = BT_UP + 0.752
            if o.get('dinner'): _bt_dinner(pen, v)
            lap = o.get('laptop_on', True)
            if lap: _bt_laptop(pen, v, 4.12, Y, 2.35, (-1.0, 0.0), _lv(o, 'laptop', 0.0), 0.0 if lap == 'closed' else 1.0)
            if o.get('headset_table'): _bt_headset(pen, v, 4.12, Y, 2.68)
            if o.get('mug', True): _bt_mug(pen, v, 4.28, Y, 2.02)
            if o.get('papers', True) and not o.get('dinner'):
                for k_ in range(3):
                    x_, y_ = 4.5 + 0.05 * k_, 2.12 + 0.03 * k_
                    q = [v.p(x_ - 0.1, Y, y_ - 0.14), v.p(x_ + 0.1, Y, y_ - 0.14), v.p(x_ + 0.1, Y, y_ + 0.14), v.p(x_ - 0.1, Y, y_ + 0.14)]
                    if v.d(x_, y_) > 0.3: pen.fill(poly(q), lit('#f4f2ec', (x_, Y, y_), (0, 1, 0))); pen.line(poly(q), 0.5, '#000000', 60)
            if o.get('carton'): _bt_tab_on_carton(pen, v, 5.12, Y, 2.35, (1.0, 0.0), _lv(o, 'tablet', 0.0))
        P.append(Piece('on_table', (tb.cx, BT_UP + 0.8, tb.cy), on_table))
        if not callable(o.get('swing')):
            P.append(Piece('pendant', (BT_LAMPP[0], BT_UP + 1.8, BT_LAMPP[1]), lambda pen, v: bt_pendant(pen, v, _lv(o, 'swing', 0.0), _lv(o, 'lamp', 0.0))))
        # the jar on the kitchen sill
        sb = Box((BT_KWIN[0] + BT_KWIN[1]) / 2, 0.11, BT_KWIN[1] - BT_KWIN[0] + 0.16, 0.22, BT_UP + BT_KWIN[2] - 0.035, BT_UP + BT_KWIN[2], 0)
        def sill_jar(pen, v):                                               # the deep sill board the jar stands on
            draw_box(pen, v, sb, {'all': '#e6dfcf', 'top': '#efe9da'}, lw=0.8)
            bt_jar(pen, v, BT_JAR[0], BT_UP + BT_KWIN[2], BT_JAR[1], o.get('jar', 'full'))
        P.append(Piece('jar', (BT_JAR[0], BT_UP + 1.0, BT_JAR[1]), sill_jar))
        # the living room: the couch facing the front door, a side table and lamp, the bookshelf
        cb = BT_COUCH
        def couch(pen, v):
            draw_box(pen, v, sub(cb, -0.95, 0.95, -0.2, 0.43, BT_UP + 0.12, BT_UP + 0.44), {'all': BT_PAL['couch'], 'top': dict(fill=BT_PAL['couch'], art=lambda p_, W, H: p_.line(rect(W / 2 - 1, 0, 2, H), 1.0, '#000000', 80))}, lw=1.0)
            draw_box(pen, v, sub(cb, -0.95, 0.95, -0.43, -0.2, BT_UP + 0.12, BT_UP + 0.84), {'all': BT_PAL['couch_d']}, lw=1.0)
            for u in (-0.95, 0.8): draw_box(pen, v, sub(cb, u, u + 0.15, -0.43, 0.43, BT_UP + 0.12, BT_UP + 0.6), {'all': BT_PAL['couch_d'], 'top': BT_PAL['couch']}, lw=1.0)
            for (u, n) in ((-0.88, -0.36), (0.88, -0.36), (0.88, 0.36), (-0.88, 0.36)):
                a_ = cb.at(u, n, BT_UP); pen.seg(v.p(*a_), v.p(a_[0], BT_UP + 0.12, a_[2]), max(1.0, 0.03 * v.s(a_[0], a_[2])), '#2a1e16')
        P.append(Piece('couch', (cb.cx, BT_UP + 0.4, cb.cy), couch, block=cb.footprint()))
        stb = Box(2.45, 2.78, 0.45, 0.45, BT_UP, BT_UP + 0.55, -90)
        lvk = _lv(o, 'living', 0.0)
        P.append(Piece('side_table', (stb.cx, BT_UP + 0.3, stb.cy), lambda pen, v: (draw_box(pen, v, stb, {'all': '#6a4a30'}, lw=0.8), dr_table_lamp(pen, v, 2.45, 2.78, BT_UP + 0.55, lvk, '#efe2c4', '#8a7a5a', 0.48)), block=stb.footprint()))
        bk_ = Box(0.95, 5.03, 1.1, 0.32, BT_UP, BT_UP + 1.7, 0)
        def shelf(pen, v):
            def art(p_, W, H):
                p_.fill(rect(0, 0, W, H), '#5a3e2a')
                rng = np.random.default_rng(5)
                for r_ in range(4):
                    yb = 12 + r_ * (H - 16) / 4.0 + (H - 16) / 4.0 - 4
                    p_.fill(rect(4, yb, W - 8, 4), '#3a2818'); xx = 6
                    while xx < W - 12:
                        bw = rng.uniform(2.5, 6.0); bh = rng.uniform(22, 32)
                        p_.fill(rect(xx, yb - bh, bw, bh), ['#8a3a2a', '#2a4a6a', '#c8a050', '#3a6a4a', '#d8d0c0'][int(rng.integers(0, 5))]); xx += bw + 0.6
            draw_box(pen, v, bk_, {'front': dict(fill='#5a3e2a', art=art), 'all': '#4a3020'}, lw=1.0)
        P.append(Piece('bookshelf', (bk_.cx, BT_UP + 0.8, bk_.cy), shelf, block=bk_.footprint()))
        # the doors
        if not callable(o.get('fdoor')): P.append(_door_piece('front_door', bt_front_door(), _lv(o, 'fdoor', 0.0), BT_UP + 1.0))
        if not callable(o.get('mdoor')): P.append(_door_piece('mom_door', bt_mom_door(), _lv(o, 'mdoor', 0.0), BT_UP + 1.0))
        return P
    def glows(v, o):
        def tv(pen, t):
            k = _kfn(o.get('laptop', 0.0), 995)(t)
            if k > 0.02 and v.d(4.05, 2.35) > 0.3 and v.visible((4.2, BT_UP + 0.9, 2.35), (-1, 0, 0)):
                x, y = v.p(4.22, BT_UP + 0.9, 2.35); s = v.s(4.2, 2.35); pen.glow(x, y, 0.35 * s, BT_LAPTOP, int(60 * k))
        return [('laptop_glow', (4.2, BT_UP + 0.9, 2.35), tv)]
    def spots(v, o):
        S = {}
        U = BT_UP
        S['table_mom'] = _mk_spot(v, 'table_mom', 3.66, 2.35, U, 'seat', "Mom's chair at the west end, at her laptop (facing +x); the Blank sits here at dinner", face=(1, 0), seat_Y=0.46)
        S['table_owen'] = _mk_spot(v, 'table_owen', 5.54, 2.35, U, 'seat', "Owen's chair at the east end (facing -x, his tablet on the milk carton)", face=(-1, 0), seat_Y=0.46)
        S['table_n'] = _mk_spot(v, 'table_n', 4.6, 3.03, U, 'seat', 'the chair on the north side (facing -y)', face=(0, -1), seat_Y=0.46)
        S['stool'] = _mk_spot(v, 'stool', 6.6, 2.9, U, 'seat', 'the stool at the counter facing the microwave (+x): the microwave beat', face=(1, 0), seat_Y=0.66)
        S['micro'] = _mk_spot(v, 'micro', BT_MX, 3.0, U + 1.4, 'point', 'the black microwave door (bt_mirror maps reflections into it)')
        S['behind_stool'] = _mk_spot(v, 'behind_stool', 5.95, 2.78, U, 'stand', 'standing right behind the stool (the Blank in the reflection)', face=(1, 0))
        S['fridge'] = _mk_spot(v, 'fridge', 5.95, 4.08, U, 'stand', 'at the fridge, facing the board (+y): writing on it', face=(0, 1))
        S['board'] = _mk_spot(v, 'board', 5.95, 4.43, U + 1.35, 'point', 'the whiteboard on the fridge door (centre)')
        S['marker'] = _mk_spot(v, 'marker', 5.82, 4.43, U + 1.07, 'point', "the marker in the board's tray")
        S['fridge_gap'] = _mk_spot(v, 'fridge_gap', 5.32, 4.9, U, 'stand', 'the gap BESIDE the fridge: the creepy form unfolds here (facing -y)', face=(0, -1))
        S['gap_top'] = _mk_spot(v, 'gap_top', 5.32, 4.6, U + BT_CEIL, 'point', 'the ceiling over the gap (her head bends along it)')
        S['ceiling'] = _mk_spot(v, 'ceiling', 5.6, 3.6, U + BT_CEIL, 'point', 'the ceiling (Y of the ceiling plane)')
        S['counter_e'] = _mk_spot(v, 'counter_e', 6.99, 2.0, U + 0.92, 'point', 'the counter edge (her fingers sweep it)')
        S['kitchen_mid'] = _mk_spot(v, 'kitchen_mid', 5.9, 3.7, U, 'stand', 'the middle of the kitchen (by the fridge and the stool)')
        S['momdoor'] = _mk_spot(v, 'momdoor', 3.47, 4.75, U, 'stand', "in front of Mom's bedroom door, facing into the kitchen (-y)", face=(0, -1))
        S['window_k'] = _mk_spot(v, 'window_k', 5.4, 0.55, U, 'stand', 'at the kitchen window, facing out (-y): watching the front door below', face=(0, -1))
        S['jar'] = _mk_spot(v, 'jar', BT_JAR[0], BT_JAR[1], U + 0.95, 'surface', 'the button jar on the kitchen windowsill')
        S['window_l'] = _mk_spot(v, 'window_l', 1.85, 0.55, U, 'stand', 'at the living room window, facing out (-y)', face=(0, -1))
        S['couch_door'] = _mk_spot(v, 'couch_door', 2.35, 4.4, U, 'seat', 'on the couch facing the front door (-x): the headset lady at 11:58', face=(-1, 0), seat_Y=0.44)
        S['couch_s'] = _mk_spot(v, 'couch_s', 2.35, 3.5, U, 'seat', 'the couch, south seat (facing -x)', face=(-1, 0), seat_Y=0.44)
        S['officer'] = _mk_spot(v, 'officer', 1.55, 3.6, U, 'stand', 'Officer Mensah standing by the couch, notebook out (facing +x, the kitchen)', face=(1, 0.2))
        S['frontdoor'] = _mk_spot(v, 'frontdoor', 0.55, 4.6, U, 'stand', 'just inside the front door (facing -x)', face=(-1, 0))
        S['owendoor'] = _mk_spot(v, 'owendoor', 0.45, 2.97, U, 'stand', "outside Owen's door in the living room (facing -x)", face=(-1, 0))
        S['lamp'] = _mk_spot(v, 'lamp', BT_LAMPP[0], BT_LAMPP[1], U + 1.52, 'point', 'the pendant lamp (shade bottom); swing it with swing=f(t) deg')
        S['laptop'] = _mk_spot(v, 'laptop', 4.12, 2.35, U + 0.75, 'surface', "Mom's laptop (screen toward her chair)")
        S['tablet_carton'] = _mk_spot(v, 'tablet_carton', 5.12, 2.35, U + 0.75, 'surface', "Owen's tablet on the milk carton")
        S['table_top'] = _mk_spot(v, 'table_top', 4.6, 2.35, U + 0.75, 'surface', 'the table top (centre)')
        S['oven_clock'] = _mk_spot(v, 'oven_clock', 7.53, BT_STOVE.cy, U + 1.02, 'point', 'the oven clock (clock= "11:58" / f(t))')
        S['slippers'] = _mk_spot(v, 'slippers', 5.3, 3.75, U, 'surface', "where the two buttons roll and stop (at Mom's slippers)")
        return S
    return dict(name='main', R=BT_MAIN, Y0=BT_UP, H=BT_CEIL, floor=dict(base=BT_PAL['floor'], kind='boards', ink='#4a2e1a', seed=61, art=floor_art), runs=runs,
                walls=dict(paper=BT_PAL['liv_paper'], ink='#b8a888', kind='stripe', wains=0.0, seed=63, scale=1.0, pa=40),
                ceil=dict(c='#ece6da'), lights=lights, pieces=pieces, glows=glows, spots=spots)


def _bt_owen_cfg(o):
    tod = _tod(o)
    def lights(o):
        amb = _bt_amb(o, '#1a2036')
        steady = [_bt_win_lamp(o, BT_OWIN[0], BT_OWIN[1], BT_OWIN[2], BT_OWIN[3], 0.0, 2.1, (0.06, -0.36, 1.0))]
        TA = o.get('tablet_at', (-0.55, BT_UP + 0.62, 0.75))
        var = [('lamp', [Lamp(-2.0, BT_UP + 1.1, 3.25, 3.0, BT_WARM, 1.3, (1.0, 0.6, 0.3), fall=1.4)], _kfn(o.get('lamp', 0.0), 821)),
               ('ceil', [Lamp(-1.8, BT_UP + 2.4, 1.8, 6.0, '#fff0d8', 1.15, (1.0, 0.5, 0.2), fall=1.3)], _kfn(o.get('ceil', 0.0), 822)),
               ('tablet', [Lamp(TA[0], TA[1], TA[2], 1.8, BT_TAB, 1.4, (0.8, 1.0, 0.8), fall=1.5)], _kfn(o.get('tablet', 0.0), 823)),
               ('hall', [Lamp(0.4, BT_UP + 1.0, 2.97, 2.6, BT_WARM, 0.8, (0.6, 1.0, 1.0), fall=1.5)], _kfn(o.get('hall', 0.0), 824))]
        var += _bt_sweep_lamps(o, 830, BT_UP + 2.2, 1.0, (-3.2, -2.4, -1.6, -0.8, 0.0), 1.1)
        return amb, steady, var
    def west(p_, W, H):                                                     # run (-3.6, 0) -> (-3.6, 3.6): u = y
        p_.fill(rect(2.55 * 100, H - 190, 50, 70), '#2a3a6a'); p_.line(rect(2.55 * 100, H - 190, 50, 70), 0.6)          # a game poster
        for k in range(5): p_.fill(rect(2.55 * 100 + 6 + k * 8, H - 150 - (k % 3) * 8, 6, 6), ['#e84a3a', '#e8c040', '#4ad06a', '#4a8ad8', '#f0f0f0'][k])
        btext(p_, 'STARFORT', 2.55 * 100 + 25, H - 176, 'sans_b', 7, '#e8d860', 240, 'center')
    def back(p_, W, H):                                                     # run (-3.6, 3.6) -> (0, 3.6): u = x + 3.6
        p_.fill(rrect(0.4 * 100, H - 175, 40, 30, 1), '#4a3a2a'); p_.fill(rrect(0.4 * 100 + 3, H - 172, 34, 24, 1), '#a8c0d0')  # a photo: him and Mom
        p_.fill(oval(0.4 * 100 + 14, H - 160, 5), '#8a5a3a'); p_.fill(oval(0.4 * 100 + 25, H - 162, 6), '#7a5232')
        _light_switch(p_, (3.6 - 0.25) * 100, H - 120, True)
    def east(p_, W, H):                                                     # run (0, 3.6) -> (0, 0): u = 3.6 - y
        for (k, c) in enumerate(('#e84a3a', '#4a8ad8', '#e8c040')):
            p_.fill(rect((3.6 - 2.1) * 100 + k * 14, H - 150 - k * 6, 10, 10), c, 200)   # stickers
    wins = {'front': [(BT_OWIN[0], 0.0, BT_OWIN[1], 0.0, BT_OWIN[2], BT_OWIN[3], (2, 2))]}
    holes = {'east': [(0.0, BT_ODOOR[0], 0.0, BT_ODOOR[1], 0.0, BT_ODOOR[2])], 'west': [(-3.6, BT_CLOSET[0], -3.6, BT_CLOSET[1], 0.0, BT_CLOSET[2])]}
    runs = _rect_runs(BT_OWEN, holes, wins, {'west': west, 'back': back, 'east': east})
    rug = _bu_rug_art(BT_OWEN[0], BT_OWEN[3], -1.9, 1.9, 0.8, 0.6, ('#3a6a9a', '#e8d870', '#d84a3a', '#f4f0e0'))
    def pieces(o):
        P = []
        bed = bu_bed_parts(BT_OBED, BT_UP, o.get('bed', 'made'), '#6a4428', ('#3a6a9a', '#e8d8b0', '#4a8a5a', '#c8b898'), '#3a5a8a')
        P.append(Piece('bed', (BT_OBED.cx, BT_UP + 0.4, BT_OBED.cy), lambda pen, v: draw_parts(pen, v, bed), block=BT_OBED.footprint()))
        se = BT_SEAT
        P.append(Piece('window_seat', (se.cx, BT_UP + 0.4, se.cy), lambda pen, v: (draw_box(pen, v, se, {'all': '#e8e2d4', 'front': dict(fill='#e8e2d4', art=lambda p_, W, H: [p_.line(rect(6 + k * W / 3, 8, W / 3 - 12, H - 14), 0.8, '#000000', 70) for k in range(3)])}, lw=1.0),
                                                                              draw_box(pen, v, sub(se, -0.66, 0.66, -0.16, 0.16, BT_UP + 0.62, BT_UP + 0.68), {'all': '#4a6a9a', 'top': '#5a7aaa'}, lw=0.7)), block=se.footprint()))
        if o.get('tablet_bed'):
            P.append(Piece('tablet_bed', (-0.55, BT_UP + 0.56, 0.95), lambda pen, v: _bt_tab_flat_3d(pen, v, -0.55, BT_UP + 0.56, 0.95, _lv(o, 'tablet', 0.0), o.get('tablet_bed') == 'down')))
        dk = Box(-2.45, 3.33, 1.0, 0.52, BT_UP, BT_UP + 0.74, 0)
        lk = _lv(o, 'lamp', 0.0)
        P.append(Piece('desk', (dk.cx, BT_UP + 0.4, dk.cy), lambda pen, v: (draw_parts(pen, v, _bt_tparts(dk, '#e8e0d0', apron=0.05)), dr_table_lamp(pen, v, -2.8, 3.4, BT_UP + 0.74, lk, '#e8d860', '#4a8ad8', 0.38)), block=dk.footprint()))
        ch = Box(-2.45, 2.85, 0.4, 0.4, BT_UP, BT_UP + 0.44, 180)
        P.append(Piece('desk_chair', (ch.cx, BT_UP + 0.3, ch.cy), lambda pen, v: (draw_parts(pen, v, _bt_tparts(ch, '#3a6ac8', apron=0.03, thick=0.04, legw=0.03)),
                                                                                draw_box(pen, v, sub(ch, -0.19, 0.19, -0.2, -0.16, BT_UP + 0.44, BT_UP + 0.86), {'all': '#3a6ac8'}, lw=0.7)), block=ch.footprint()))
        if not callable(o.get('closet')): P.append(_door_piece('closet_door', bt_closet_door(o.get('ink')), _lv(o, 'closet', 0.0), BT_UP + 1.0))
        if not callable(o.get('door')): P.append(_door_piece('owen_door', bt_owen_door(), _lv(o, 'door', 70.0), BT_UP + 1.0))
        return P
    def spots(v, o):
        S = {}; U = BT_UP
        S['bed'] = _mk_spot(v, 'bed', BT_OBED.cx, BT_OBED.cy - 0.05, U + 0.5, 'lie', 'Owen in bed (head at the front wall by the window)')
        S['pillow'] = _mk_spot(v, 'pillow', BT_OBED.cx, 0.38, U + 0.62, 'point', 'his head on the pillow')
        S['bed_hem'] = _mk_spot(v, 'bed_hem', BT_OBED.cx, 0.72, U + 0.64, 'point', "the quilt's top hem over his chest (lying figures clip here)")
        S['bed_edge'] = _mk_spot(v, 'bed_edge', -1.1, 1.2, U, 'seat', 'sitting on the edge of the bed (facing -x, the closet)', face=(-1, 0), seat_Y=0.5)
        S['sill_seat'] = _mk_spot(v, 'sill_seat', -1.7, 0.2, U, 'seat', 'ON the window seat, back to the window, facing the room (+y): the Blank singing at night', face=(0, 1), seat_Y=0.68)
        S['window'] = _mk_spot(v, 'window', -1.7, 0.55, U, 'stand', 'at the window, facing out (-y): he looks down at the street (leaning on the seat)', face=(0, -1))
        S['window_glass'] = _mk_spot(v, 'window_glass', -1.7, 0.0, U + 1.4, 'point', "the window glass (the photo he sends; she waves at the window next to it)")
        S['closet'] = _mk_spot(v, 'closet', -2.9, 1.62, U, 'stand', 'in front of the closet door (facing it, -x)', face=(-1, 0))
        S['closet_in'] = _mk_spot(v, 'closet_in', -3.95, 1.62, U, 'stand', 'inside the closet (the red coat on its hanger)', face=(1, 0))
        S['coat'] = _mk_spot(v, 'coat', -3.95, 1.62, U + 1.62, 'point', "the red coat's collar on the rod")
        S['list'] = _mk_spot(v, 'list', -3.6, 1.62, U + 1.3, 'point', 'the Brave List on the inside of the closet door (open ~95 deg it faces the room door)')
        S['door_in'] = _mk_spot(v, 'door_in', -0.45, 2.97, U, 'stand', 'one step inside his door (facing -x)', face=(-1, 0))
        S['desk'] = _mk_spot(v, 'desk', -2.45, 2.85, U, 'seat', 'at the desk (facing +y)', face=(0, 1), seat_Y=0.44)
        S['room_mid'] = _mk_spot(v, 'room_mid', -1.9, 1.9, U, 'stand', 'the middle of the room')
        S['tablet_bed'] = _mk_spot(v, 'tablet_bed', -0.55, 0.95, U + 0.56, 'surface', 'the tablet on the bed')
        return S
    return dict(name='owen', R=BT_OWEN, Y0=BT_UP, H=BT_CEIL, floor=dict(base='#9a6a44', kind='boards', ink='#4a2e1a', seed=71, art=rug), runs=runs,
                walls=dict(paper=BT_PAL['owen_paper'], ink=BT_PAL['owen_ink'], kind='stars', wains=0.0, seed=73, scale=1.0, pa=90),
                ceil=dict(c='#e8ecf0'), lights=lights, pieces=pieces, spots=spots)


def _bt_tab_flat_3d(pen, v, x, Y, y, on=1.0, down=False):
    """The tablet lying flat on the bed (face up glowing, or face DOWN: only a thin line of light at its edges)."""
    q = [v.p(x - 0.12, Y, y - 0.085), v.p(x + 0.12, Y, y - 0.085), v.p(x + 0.12, Y, y + 0.085), v.p(x - 0.12, Y, y + 0.085)]
    if v.d(x, y) < 0.3: return
    pen.fill(poly(q), '#2a2c32' if down else '#16171b'); pen.line(poly(q), 0.8)
    if down:
        if on > 0.02: pen.line(poly(q), 1.6, BT_TAB, int(120 * on), blur=2)
        return
    sc = [lerp2(q[0], q[1], 0.06, q[3], 0.08), lerp2(q[1], q[0], 0.06, q[2], 0.08), lerp2(q[2], q[3], 0.06, q[1], 0.08), lerp2(q[3], q[2], 0.06, q[0], 0.08)]
    pen.fill(poly(sc), mix('#0a0e18', BT_TAB, on * 0.85))


def _bt_closet_cfg(o):
    """The closet behind the west wall: dark; the rod; the red coat (o['coat'] None | 'full' | 'sag' | 0..1 fullness)."""
    def lights(o):
        return mix('#0e1220', '#4a5680', 0.25), [], [('tablet', [Lamp(-3.2, BT_UP + 1.0, 1.6, 1.6, BT_TAB, 0.9, fall=1.5)], _kfn(o.get('tablet', 0.0), 841))]
    def pieces(o):
        P = []
        def rod(pen, v):
            if v.d(-3.95, 1.62) > 0.3: pen.seg(v.p(-3.95, BT_UP + 1.75, 1.0), v.p(-3.95, BT_UP + 1.75, 2.3), max(1.0, 0.025 * v.s(-3.95, 1.62)), '#6a6a70')
        P.append(Piece('rod', (-3.95, BT_UP + 1.75, 1.62), rod))
        c = o.get('coat')
        if c is not None and not callable(c):
            full = 1.0 if c == 'full' else (0.0 if c == 'sag' else float(c))
            P.append(Piece('coat', (-3.95, BT_UP + 1.2, 1.62), lambda pen, v: _bt_coat_3d(pen, v, full)))
        return P
    return dict(name='closet', R=(-4.3, -3.6, 0.9, 2.4), Y0=BT_UP, H=BT_CEIL, floor=dict(base='#3a2a1e', kind='boards', ink='#1a120a', seed=75),
                walls=dict(paper='#6a7480', ink=None, kind=None), ceil=dict(c='#5a5e66'), lights=lights, pieces=pieces)


def _bt_coat_3d(pen, v, full, sway=0.0):
    x, y = -3.95, 1.62
    if v.d(x, y) < 0.3: return
    cx, cy = v.p(x, BT_UP + 1.72, y)
    _bt_coat(pen, cx, cy, 0.78 * v.s(x, y), full, 7, sway, True, dark=0.35)


# ====================================================================================================== the lobby (ground floor)
def _bt_lobby_cfg(o):
    R = (3.0, 7.0, -2.6, 2.6)
    def lights(o):
        amb = '#5a5a62' if _tod(o) != 'night' else '#3a3e52'
        steady = [Lamp(5.0, 2.9, -0.5, 6.5, '#f8ecc8', 1.35, (1.0, 0.5, 0.2), fall=1.3)]
        return amb, steady, []
    def east(p_, W, H):                                                     # run (7, 2.6) -> (7, -2.6): u = 2.6 - y  (the mailboxes)
        x0 = (2.6 - (-0.4)) * 100
        p_.fill(rect(x0, H - 190, 150, 90), '#a8a090'); p_.line(rect(x0, H - 190, 150, 90), 1.0)
        for r_ in range(3):
            for c_ in range(5):
                p_.fill(rect(x0 + 5 + c_ * 29, H - 185 + r_ * 29, 26, 25), '#c8c0a8'); p_.fill(rect(x0 + 9 + c_ * 29, H - 180 + r_ * 29, 10, 3), '#2a2a2a')
    def back(p_, W, H):
        btext(p_, 'PLEASE CLOSE THE DOOR', 2.0 * 100, H - 160, 'sans_b', 9, '#2a2a2a', 200, 'center')
    holes = {'west': [(3.0, BT_GDOOR[0], 3.0, BT_GDOOR[1], 0.0, BT_GDOOR[2])], 'back': [(3.4, 2.6, 4.6, 2.6, 0.0, 2.2)]}
    wins = {'front': [(4.0, -2.6, 6.0, -2.6, 0.7, 2.3, (4, 1))]}
    runs = _rect_runs(R, holes, wins, {'east': east, 'back': back})
    def pieces(o):
        def frame(pen, v):                                                  # the aluminium frame and the glass pane of the lobby door
            y0, y1, h = BT_GDOOR
            q = [v.p(3.0, 0.0, y1), v.p(3.0, 0.0, y0), v.p(3.0, h, y0), v.p(3.0, h, y1)]
            if v.d(3.0, (y0 + y1) / 2) < 0.3: return
            pen.fill(poly(q), '#c8d8e8', 26)
            pen.line(poly(q), max(2.0, 0.05 * v.s(3.0, -1.5)), '#6a6c74')
            a_, b_ = v.p(3.0, 1.0, y1 - 0.06), v.p(3.0, 1.0, y0 + 0.06)
            pen.seg(a_, b_, max(1.5, 0.03 * v.s(3.0, -1.5)), '#9a9ca4')
            pen.linear(poly(q), q[0][0], q[2][1], q[1][0], q[0][1], [(0, '#ffffff', 0), (0.42, '#ffffff', 30), (0.5, '#ffffff', 0)])
        return [Piece('glass_door', (3.0, 1.2, -1.5), frame)]
    def spots(v, o):
        S = {}
        S['glass_in'] = _mk_spot(v, 'glass_in', 3.35, -1.5, 0.0, 'stand', 'inside the lobby at the glass door (facing -x)', face=(-1, 0))
        S['glass_out'] = _mk_spot(v, 'glass_out', 2.72, -1.5, BT_G, 'stand', 'OUTSIDE the glass door, facing in (+x): palms flat on the glass', face=(1, 0))
        S['glass'] = _mk_spot(v, 'glass', 3.0, -1.5, 1.3, 'point', 'the glass (palm height)')
        S['stairs'] = _mk_spot(v, 'stairs', 4.0, 2.2, 0.0, 'stand', 'at the foot of the stairs')
        return S
    return dict(name='lobby', R=R, Y0=0.0, H=3.0, floor=dict(base='#c8c4b8', kind='checker', ink='#5a5a5a', seed=81), runs=runs,
                walls=dict(paper='#d8d0b8', ink=None, kind=None, wains=1.0, wcol='#7a6a5a'), ceil=dict(c='#ece8e0'), lights=lights, pieces=pieces, spots=spots)


# ====================================================================================================== cameras + builders
_bcam('bt_apt_wide', 640, 500, BT_UP + 1.6, 0.45, 0.7, 60, _env(), 'the kitchen + living room from the living room\'s front corner: the table and lamp, Mom\'s door, the gap and the fridge, the counter and the microwave', 'apt')
_bcam('bt_apt_living', 620, 500, BT_UP + 1.6, 4.3, 0.55, -42, _env(), 'from the kitchen to the living room: the couch facing the front door, Owen\'s door, the living window', 'apt')
_bcam('bt_apt_table', 860, 520, BT_UP + 1.3, 6.1, 1.85, -80, _env(), "the table from Owen's end: Mom's chair and laptop at the far end (the Blank sits there at dinner)", 'apt')
_bcam('bt_apt_table_back', 820, 520, BT_UP + 1.45, 2.55, 1.7, 75, _env(), "from behind Mom's chair (2 a.m.: her back, the laptop glow), Owen's end and the kitchen beyond", 'apt')
_bcam('bt_apt_fridge', 540, 650, BT_UP + 1.25, 5.45, 2.05, 2, _env(), 'the fridge and its board, the GAP beside it to the ceiling, the tall cabinet, Mom\'s door left', 'apt', pitch=-6.0)
_bcam('bt_apt_board', 1350, 540, BT_UP + 1.35, 5.95, 3.55, 0, _env(x=(920, 1000), y=(500, 560), zoom=(1.0, 1.06)), 'close on the whiteboard', 'apt')
_bcam('bt_apt_micro', 1150, 540, BT_UP + 1.45, 6.2, 3.16, 98, _env(x=(920, 1000), y=(500, 560), zoom=(1.0, 1.06)), 'over Owen\'s left shoulder on the stool into the black microwave door (it reflects him and Mom at her end of the table)', 'apt', pitch=2.0)
_bcam('bt_apt_window', 900, 520, BT_UP + 1.35, 5.3, 1.9, 182, _env(), 'the kitchen window, the button jar on its sill, the street beyond', 'apt')
_bcam('bt_apt_momdoor', 820, 520, BT_UP + 1.2, 5.6, 2.3, -38, _env(), "from Owen's seat to Mom's bedroom door (the Blank in front of it)", 'apt')
_bcam('bt_apt_clock', 1300, 540, BT_UP + 1.05, 6.55, BT_STOVE.cy, 90, _env(x=(930, 990), y=(510, 570), zoom=(1.0, 1.05)), 'close on the oven clock (11:58 -> 12:00)', 'apt')
_bcam('bt_apt_door', 820, 520, BT_UP + 1.55, 1.75, 2.45, -58, _env(), 'the front door from the living room (the box was outside it)', 'apt')
_bcam('bt_apt_couch', 760, 540, BT_UP + 1.35, 0.7, 3.55, 96, _env(), 'from the front door: the headset lady on the couch facing us, the kitchen behind (the officer, the fridge)', 'apt')
_bcam('bt_owen_wide', 640, 470, BT_UP + 1.6, -0.35, 3.3, -150, _env(), "Owen's room from the door: the window over the streetlight, the window seat, the bed, the closet", 'owen')
_bcam('bt_owen_window', 880, 500, BT_UP + 1.2, -1.5, 2.4, 178, _env(), 'the window seat and the window, the streetlight right outside', 'owen')
_bcam('bt_owen_closet', 900, 520, BT_UP + 1.35, -1.3, 1.62, -90, _env(), 'the closet door face-on (open: the Brave List inside the door, the red coat)', 'owen')
_bcam('bt_owen_bed', 700, 500, BT_UP + 1.45, -2.9, 0.55, 52, _env(), 'from the window corner to the bed and the door', 'owen')
_bcam('bt_owen_sill_pov', 640, 560, BT_UP + 0.95, -0.5, 1.6, -150, _env(x=(920, 1000), y=(500, 560), zoom=(1.0, 1.06)), 'from his pillow to the window seat (her head tilted to his breathing)', 'owen', pitch=-2.0)
_bcam('bt_lobby_door', 760, 520, 1.6, 6.5, -0.9, -92, _env(), 'inside the lobby looking at the glass door (the street, the streetlight beyond)', 'lobby')
_bcam('bt_lobby_close', 1100, 520, 1.55, 4.5, -1.35, -90, _env(x=(920, 1000), y=(500, 560), zoom=(1.0, 1.06)), 'close on the glass door from inside (palms on the glass)', 'lobby')

_BT_DEF = dict(tod='night', no_veil=True)


def _bt_o(kw, extra=None):
    o = dict(_BT_DEF)
    if extra: o.update(extra)
    o.update(kw)
    return o


def _bt_grade(o, warm=('lamp', 'ceil', 'living')):
    tod = _tod(o)
    if tod == 'day': return 'bt_day'
    if any(_static(o.get(k_, 0.0)) > 0.3 for k_ in warm): return 'bt_warm'
    if tod == 'evening': return 'bt_evening'
    return 'bt_night'


def _bt_live_door(name, v, D_fn, ang, ref, amb, steady, var):
    def fn(pen, v_, t):
        a = ang(t) if callable(ang) else ang
        D_fn(t).draw(pen, v_, a)
    return live_layer(name, v, ref, fn, amb, steady, var)


def bt_apt(view='wide', **kw):
    """The kitchen + living room. view: wide | living | table | table_back | fridge | board | micro | window | momdoor |
    clock | door | couch. tod 'night' | 'evening' | 'day'. Levels (number or f(t)): lamp (pendant), ceil, living (the
    couch lamp), laptop (its glow; laptop_on True | 'closed' | False), tablet (+tablet_at), street (the streetlight through
    the windows, default 1), flash. swing = deg or f(t) (the lamp swinging); board 'birthday' | 'here' | 'all' | None and
    board_k (how much is written: 'here' 0..1, 'all' 0..6 items; number or f(t)); clock '11:58' or f(t) -> str; jar
    'full' | 'open' | 'black' | 'empty'; carton (Owen's tablet on the milk carton); dinner; headset_table; mug; papers;
    fdoor / mdoor (deg or f(t)); refl = f(pen, t, clip) draws the figures' reflections in the microwave (view micro;
    ST.bt_mirror(sp.view, x, Y, y) gives their screen points)."""
    o = _bt_o(kw)
    v = cam('bt_apt_' + view)
    main = BuBox(_bt_main_cfg(o))
    far = [BuBox(_bt_owen_cfg(dict(o, _far=True, door=_static(o.get('odoor', 70.0), 70.0), lamp=0.0, ceil=0.0, tablet=0.0, closet=0.0)), far=True),
           _dark_far('mom_room', _r4p((2.4, 5.0, 5.2, 9.0)), BT_UP, BT_CEIL), _dark_far('corridor', _r4p((-3.0, 0.0, 3.6, 7.0)), BT_UP, BT_CEIL, c='#1a1814')]
    dyn = []
    amb, steady, var = main.lights(o)
    if callable(o.get('swing')):
        sw = o['swing']
        dyn.append(live_layer('pendant', v, (BT_LAMPP[0], BT_UP + 1.8, BT_LAMPP[1]), lambda pen, v_, t: bt_pendant(pen, v_, sw(t), _kfn(o.get('lamp', 0.0), 801)(t)), amb, steady, var))
    if callable(o.get('board_k')) or callable(o.get('board')):
        def bfn(pen, v_, t):
            st = o['board'](t) if callable(o.get('board')) else o.get('board', 'birthday')
            bk = o['board_k'](t) if callable(o.get('board_k')) else o.get('board_k', 1.0)
            F = wall_face((5.72, 4.444), (6.18, 4.444), BT_UP + 1.05, BT_UP + 1.65)
            draw_face(pen, v_, F, lambda p_, W, H: _bt_board_art(p_, W, H, st, bk), '#f6f8f6', ao=False)
        dyn.append(live_layer('board', v, (5.95, BT_UP + 1.35, 4.43), bfn, amb, steady, var))
    if callable(o.get('fdoor')): dyn.append(_bt_live_door('front_door', v, lambda t: bt_front_door(), o['fdoor'], (0.45, BT_UP + 1.0, 4.6), amb, steady, var))
    if callable(o.get('mdoor')): dyn.append(_bt_live_door('mom_door', v, lambda t: bt_mom_door(), o['mdoor'], (3.47, BT_UP + 1.0, 5.25), amb, steady, var))
    dyn.append(_bt_clock_layer(v, o))
    if view == 'micro' or callable(o.get('refl')): dyn.append(_bt_micro_layer(v, o))
    sp = build_view('bt_apt_' + view, v, main, o, far=far, outside=_bt_outside(o), grade=_bt_grade(o), dyn=dyn)
    sp.info['note'] = 'Kitchen + living: table_mom / table_owen / stool / fridge / fridge_gap / momdoor / window_k / couch_door / officer; bt_mirror for the microwave.'
    sp.info['out_order'] = ORDER_OUT - 1
    return sp


def bt_owen(view='wide', **kw):
    """Owen's room. view: wide | window | closet | bed | sill_pov. tod 'night' | 'day' | 'evening'. Levels: lamp (desk),
    ceil, tablet (+tablet_at; tablet_bed True | 'down' puts it on the bed), hall (light from the living room), street (the
    streetlight through the window, default 1); sweep = ST.bt_sweep(t0) (headlights across the ceiling); closet (deg or
    f(t)); door (deg, default 70); ink [7 levels] (the Brave List at room scale: 1 blue .. 0 pale); coat None | 'full' |
    'sag' | 0..1 | f(t) (the red coat in the closet); sash 0..1 or f(t) (the lower sash raised: "my window sliding shut");
    bed 'made' | 'turned'."""
    o = _bt_o(kw)
    v = cam('bt_owen_' + view)
    main = BuBox(_bt_owen_cfg(o))
    far = [BuBox(_bt_closet_cfg(o), far=True), BuBox(_bt_main_cfg(dict(o, _far=True, lamp=_lv(o, 'hall', 0.0) * 0.6, laptop=0.0, tablet=0.0)), far=True)]
    dyn = []
    amb, steady, var = main.lights(o)
    if callable(o.get('closet')):
        dyn.append(_bt_live_door('closet_door', v, lambda t: bt_closet_door(o.get('ink')), o['closet'], (-3.55, BT_UP + 1.0, 1.62), amb, steady, var))
    if callable(o.get('door')):
        dyn.append(_bt_live_door('owen_door', v, lambda t: bt_owen_door(), o['door'], (-0.05, BT_UP + 1.0, 2.97), amb, steady, var))
    if callable(o.get('coat')):
        cf = o['coat']
        dyn.append(live_layer('coat', v, (-3.95, BT_UP + 1.2, 1.62), lambda pen, v_, t: _bt_coat_3d(pen, v_, cf(t), 0.0), amb, steady, var, order=ORDER_FAR - 0.5))
    sash = o.get('sash', 0.0)
    if callable(sash) or sash > 0.01:
        def sfn(pen, v_, t):
            k = sash(t) if callable(sash) else sash
            Yb = BT_UP + BT_OWIN[2] + 0.04 + k * 0.6; Yt = Yb + (BT_OWIN[3] - BT_OWIN[2]) * 0.5
            q = [v_.p(BT_OWIN[0] + 0.05, Yb, 0.03), v_.p(BT_OWIN[1] - 0.05, Yb, 0.03), v_.p(BT_OWIN[1] - 0.05, Yt, 0.03), v_.p(BT_OWIN[0] + 0.05, Yt, 0.03)]
            w_ = max(1.5, 0.035 * v_.s(-1.7, 0.03))
            pen.line(poly(q), w_ + 2, '#1a1a20', 160); pen.line(poly(q), w_, '#cfc9bb')
            pen.seg(q[0], q[1], w_ * 1.6, '#cfc9bb')                         # the meeting rail
        dyn.append(live_layer('sash', v, (-1.7, BT_UP + 1.2, 0.03), sfn, amb, steady, var))
    sp = build_view('bt_owen_' + view, v, main, o, far=far, outside=_bt_outside(o), grade=_bt_grade(o, ('lamp', 'ceil')), dyn=dyn)
    sp.info['note'] = "Owen's room: bed / pillow, sill_seat (the Blank sings there), window, closet / closet_in / coat / list, door_in, desk."
    sp.info['out_order'] = ORDER_OUT - 1
    return sp


def bt_lobby(view='door', tod='night', **kw):
    """The building lobby (ground floor) and its glass door on the street. view: door | close. The street beyond the glass
    is the same plan (the streetlight); stage the Blank outside at glass_out (palms on the glass)."""
    o = _bt_o(kw, dict(tod=tod))
    v = cam('bt_lobby_' + view)
    main = BuBox(_bt_lobby_cfg(o))
    far = [_dark_far('stairwell', _r4p((3.4, 4.6, 2.6, 5.0)), 0.0, 3.0)]
    sp = build_view('bt_lobby_' + view, v, main, o, far=far, outside=_bt_outside(dict(o, tod=tod)), grade='bt_warm' if tod == 'night' else 'bt_day')
    sp.info['note'] = 'Lobby: glass_out (outside, palms on the glass), glass, glass_in.'
    return sp


# ====================================================================================================== the school pickup lane (snow)
SC_G, SC_ROAD = 0.0, -0.15
SC_SILVER = ('#a4a9b3', '#737884', '#dfe4ec')


def _sc_P(v, u, Y, n, cx=None, cy=None):
    cx = SC_CAR[0] if cx is None else cx; cy = SC_CAR[1] if cy is None else cy
    return v.p(cx + u, SC_ROAD + Y, cy + n)


_SC_BODY = [(-2.22, 0.3), (-2.3, 0.6), (-2.24, 0.9), (-1.5, 0.98), (1.18, 0.95), (2.08, 0.84), (2.3, 0.62), (2.24, 0.3)]
_SC_GH = [(-1.5, 0.98), (-0.78, 1.43), (0.42, 1.44), (1.18, 0.95)]
_SC_WIN = {'front': [(0.02, 1.0), (0.02, 1.37), (0.4, 1.39), (1.06, 1.0)], 'rear': [(-0.92, 1.0), (-0.92, 1.36), (-0.1, 1.39), (-0.1, 1.0)],
           'quarter': [(-1.36, 1.0), (-0.86, 1.35), (-1.02, 1.0)]}


def sc_car_side(pen, v, side, o):
    """One side of the silver car (side +1 = the driver side, toward the kerb; -1 the road side): the body panel, the
    greenhouse with its pillars, the windows (the driver window OPEN), the doors (the rear door on the driver side swings
    open: o['rear_door'] 0..1), the wheels, the dented rear bumper corner (driver side)."""
    n = side * 0.9
    c0, cs, chi = SC_SILVER
    if v.d(SC_CAR[0], SC_CAR[1] + n) < 0.4: return
    seen = v.visible((SC_CAR[0], SC_ROAD + 0.6, SC_CAR[1] + n), (0, 0, side))
    s = v.s(SC_CAR[0], SC_CAR[1] + n)
    P = lambda u, Y: _sc_P(v, u, Y, n)
    for uw in (-1.42, 1.45):                                                # wheels (behind the body's lower edge)
        wx, wy = P(uw, 0.33)
        pen.fill(oval(wx, wy, 0.34 * s, 0.34 * s), '#16171a'); pen.fill(oval(wx, wy, 0.19 * s), '#9a9ea6' if seen else '#3a3c42'); pen.line(oval(wx, wy, 0.19 * s), 0.8)
    body = smooth([P(u, Y) for (u, Y) in _SC_BODY] + [P(1.8, 0.27), P(-1.8, 0.27)], True, 0.5)
    pen.fill(body, lit(c0, (SC_CAR[0], SC_ROAD + 0.6, SC_CAR[1] + n), (0, 0, side)))
    pen.cv.save(); pen.cv.clipPath(body, skia.ClipOp.kIntersect, True)
    pen.fill(poly([P(-2.4, 0.62), P(2.4, 0.6), P(2.4, 0.2), P(-2.4, 0.2)]), cs, 120)               # the lower body darker
    pen.seg(P(-2.25, 0.78), P(2.2, 0.74), max(1.0, 0.012 * s), chi, 150)                            # the shoulder line
    for uw in (-1.42, 1.45):                                                # wheel arches
        wx, wy = P(uw, 0.33); pen.fill(oval(wx, wy, 0.42 * s, 0.4 * s), '#0e0f12')
    pen.cv.restore()
    for uw in (-1.42, 1.45):
        wx, wy = P(uw, 0.33)
        pen.fill(oval(wx, wy, 0.33 * s, 0.33 * s), '#1a1b1e'); pen.fill(oval(wx, wy, 0.19 * s), '#a8acb4'); pen.line(oval(wx, wy, 0.19 * s), 0.8)
        for k in range(5):
            a = k * 2 * math.pi / 5; pen.seg((wx, wy), (wx + 0.15 * s * math.cos(a), wy + 0.15 * s * math.sin(a)), max(0.8, 0.02 * s), '#6a6e76')
    pen.line(body, max(1.0, 0.01 * s))
    gh = poly([P(u, Y) for (u, Y) in _SC_GH])
    if side > 0 and o.get('win_open', True): gh = minus(gh, poly([P(u, Y) for (u, Y) in _SC_WIN['front']]))
    pen.fill(gh, lit(c0, (SC_CAR[0], SC_ROAD + 1.2, SC_CAR[1] + n), (0, 0, side))); pen.line(gh, max(1.0, 0.01 * s))
    rd = clamp(_static(o.get('rear_door', 0.0)))
    for nm, pts in _SC_WIN.items():
        q = poly([P(u, Y) for (u, Y) in pts])
        if nm == 'front' and side > 0 and o.get('win_open', True):
            pen.line(q, max(1.0, 0.014 * s), '#2a2c32')                     # open: only its rubber edge (the interior shows; the arm comes out here)
            continue
        if nm == 'rear' and side > 0 and rd > 0.05:
            continue
        pen.fill(q, '#1a2230', 200 if seen else 120)
        pen.linear(q, q.getBounds().left(), 0, q.getBounds().right(), 0, [(0, '#ffffff', 0), (0.4, '#e8f0ff', 60), (0.5, '#ffffff', 0)])
    for ud in (-0.06, 0.96):                                                # door seams
        pen.seg(P(ud, 0.3), P(ud, 1.0), max(0.8, 0.008 * s), cs)
    pen.seg(P(-1.06, 0.32), P(-1.06, 1.0), max(0.8, 0.008 * s), cs)
    for uh in (0.72, -0.3):                                                 # door handles
        hx, hy = P(uh, 0.86); pen.fill(rrect(hx - 0.07 * s, hy - 0.015 * s, 0.14 * s, 0.03 * s, 0.012 * s), cs)
    if side > 0:                                                            # the dent: rear bumper, driver-side corner
        dx, dy = P(-2.12, 0.46)
        pen.fill(oval(dx, dy, 0.16 * s, 0.09 * s), cs, 170, blur=0.02 * s)
        pen.line(smooth([P(-2.26, 0.52), P(-2.12, 0.43), P(-1.98, 0.5)], False, 0.6), max(1.0, 0.014 * s), '#4a4e56')
        pen.line(smooth([P(-2.22, 0.4), P(-2.1, 0.48), P(-2.0, 0.42)], False, 0.6), max(0.8, 0.01 * s), chi, 180)
    if o.get('snow_cap', True):
        pen.line(smooth([P(-0.76, 1.45), P(0.4, 1.46)], False), max(1.5, 0.04 * s), '#f4f6fa')
        pen.line(smooth([P(1.22, 0.97), P(2.06, 0.87)], False), max(1.2, 0.025 * s), '#f0f2f8', 220)
    tail = P(-2.27, 0.78)
    pen.fill(rrect(tail[0] - 0.04 * s, tail[1] - 0.05 * s, 0.08 * s, 0.1 * s, 0.02 * s), '#a81e22')
    head = P(2.27, 0.68)
    pen.fill(rrect(head[0] - 0.05 * s, head[1] - 0.04 * s, 0.1 * s, 0.08 * s, 0.02 * s), '#e8ecf0')


def sc_car_rear_door(pen, v, o):
    """The rear door on the driver side swung open toward the kerb (o['rear_door'] 0..1 = 0..70 deg): its inside face."""
    k = clamp(_static(o.get('rear_door', 0.0)))
    if k <= 0.05: return
    a = math.radians(68 * k); n0 = 0.9
    def P(du, Y): return _sc_P(v, -0.06 - du * math.cos(a), Y, n0 + du * math.sin(a))
    pts = [(0.0, 0.3), (0.0, 1.0), (0.0, 1.38), (0.86, 1.41), (0.9, 1.0), (0.9, 0.3)]
    door = poly([P(du, Y) for (du, Y) in pts])
    s = v.s(SC_CAR[0], SC_CAR[1] + 1.2)
    hole = poly([_sc_P(v, u, Y, 0.9) for (u, Y) in ((-0.06, 0.32), (-0.06, 1.38), (-0.96, 1.38), (-1.06, 0.32))])
    pen.fill(hole, '#121418')
    inside = v.d(*(lambda q: (q[0], q[2]))((SC_CAR[0] - 0.5, 0, SC_CAR[1] + 0.9 + 0.5 * math.sin(a)))) < v.d(SC_CAR[0], SC_CAR[1] + 0.9)
    pen.fill(door, lit('#4a4e58' if inside else SC_SILVER[0], (SC_CAR[0] - 0.4, SC_ROAD + 0.8, SC_CAR[1] + 1.2), None)); pen.line(door, max(1.0, 0.012 * s))
    pen.fill(poly([P(0.0, 0.3), P(0.9, 0.3), P(0.9, 0.6), P(0.0, 0.6)]), SC_SILVER[1], 110)
    wq = poly([P(0.06, 1.0), P(0.06, 1.34), P(0.8, 1.37), P(0.84, 1.0)])
    pen.fill(wq, '#1a2230', 150); pen.line(wq, max(0.8, 0.008 * s), '#2a2c32')
    hx, hy = P(0.75, 0.86); pen.fill(rrect(hx - 0.06 * s, hy - 0.015 * s, 0.12 * s, 0.03 * s, 0.012 * s), '#2a2c32')


def sc_car_body(pen, v, o):
    """The middle of the car: the interior seen through the glass (seats, the dash, the steering wheel at the driver's
    seat), the windshield and back glass, the roof."""
    c0 = SC_SILVER[0]
    s = v.s(SC_CAR[0], SC_CAR[1])
    if v.d(SC_CAR[0], SC_CAR[1]) < 0.5: return
    def P(u, Y, n): return _sc_P(v, u, Y, n)
    for nn in (-0.45, 0.45):                                                # seat backs (front) and the rear bench
        sb = poly([P(-0.32, 0.45, nn), P(-0.42, 1.18, nn), P(-0.22, 1.2, nn), P(-0.12, 0.45, nn)])
        pen.fill(sb, '#2e3038'); pen.line(sb, 0.8)
        hr = P(-0.36, 1.27, nn); pen.fill(oval(hr[0], hr[1], 0.09 * s, 0.07 * s), '#2e3038')
    rb = poly([P(-1.3, 0.45, 0.0), P(-1.36, 1.1, 0.0), P(-1.12, 1.12, 0.0), P(-1.0, 0.45, 0.0)])
    pen.fill(rb, '#2a2c34')
    dash = poly([P(0.75, 0.92, -0.8), P(0.75, 0.92, 0.8), P(0.95, 1.02, 0.8), P(0.95, 1.02, -0.8)])
    pen.fill(dash, '#1e2026')
    wc = P(0.52, 1.07, 0.45)                                                # the steering wheel (driver side)
    pen.line(oval(wc[0], wc[1], 0.05 * s, 0.17 * s), max(1.2, 0.03 * s), '#121316')
    pen.seg(wc, P(0.75, 0.98, 0.45), max(1.0, 0.03 * s), '#121316')
    roof = poly([P(-0.78, 1.43, -0.86), P(0.42, 1.44, -0.86), P(0.42, 1.44, 0.86), P(-0.78, 1.43, 0.86)])
    if v.cam_h > SC_ROAD + 1.45: pen.fill(roof, lit(c0, (SC_CAR[0], SC_ROAD + 1.45, SC_CAR[1]), (0, 1, 0))); pen.fill(roof, '#f4f6fa', 200)
    ws = poly([P(1.18, 0.95, -0.85), P(1.18, 0.95, 0.85), P(0.42, 1.44, 0.85), P(0.42, 1.44, -0.85)])
    pen.fill(ws, '#1a2230', 90)


def _sc_tracks(pen, v, gone=False):
    """Tire tracks in the lane's slush (gone: just the tracks where the car was, curving out into the street)."""
    for nn in (-0.78, 0.78):
        x0 = -12.0
        x1 = SC_CAR[0] + 1.6 if not gone else 14.0
        pts = []
        for i in range(30):
            x = x0 + (x1 - x0) * i / 29.0
            yy = SC_CAR[1] + nn - (0.0 if not gone else max(0.0, x - 4.0) * 0.18)
            if v.d(x, yy) > 0.6: pts.append(v.p(x, SC_ROAD + 0.003, yy))
        if len(pts) > 2:
            pen.line(smooth(pts, False, 0.5), max(2.0, 0.18 * v.s(SC_CAR[0], SC_CAR[1])), '#8a909c', 120)
            pen.line(smooth(pts, False, 0.5), max(1.0, 0.07 * v.s(SC_CAR[0], SC_CAR[1])), '#6a707c', 140)


def _sc_tree(pen, v, x, y, h, seed=0):
    if v.d(x, y) < 0.6: return
    s = v.s(x, y); rng = np.random.default_rng(seed)
    b = v.p(x, SC_G, y); t_ = v.p(x, SC_G + h * 0.5, y)
    pen.seg(b, t_, max(1.5, 0.22 * s), '#3a2e26')
    for k in range(9):
        a = rng.uniform(-2.4, -0.7); L = rng.uniform(0.25, 0.5) * h; Y0 = SC_G + h * rng.uniform(0.35, 0.55)
        p0 = v.p(x, Y0, y); p1 = (p0[0] + math.cos(a) * L * s, p0[1] + math.sin(a) * L * s)
        pen.seg(p0, p1, max(1.0, 0.06 * s), '#3a2e26')
        pen.seg((p0[0] + (p1[0] - p0[0]) * 0.6, p0[1] + (p1[1] - p0[1]) * 0.6 - 0.02 * s), (p1[0], p1[1] - 0.02 * s), max(1.0, 0.04 * s), '#f2f4f8', 200)


def _sc_school_art(p_, W, H):
    """The school's front (u from the west end x -16, cm, y down): brick, two rows of windows with paper snowflakes, the
    entrance with its canopy, the name."""
    p_.texture(rect(0, 0, W, H), 'grunge', 0.35, 'overlay', 1.0)
    for i in range(int(H / 7.5)): p_.fill(rect(0, i * 7.5, W, 0.8), '#3a1e16', 50)
    p_.fill(rect(0, 0, W, 30), '#e8ecf2')                                   # snow on the parapet
    for row, yt in enumerate((140, 400)):
        for k in range(14):
            x0 = 80 + k * 230
            if abs(x0 + 70 - W / 2) < 260: continue
            p_.fill(rect(x0 - 6, yt - 6, 152, 182), '#d8d0c0'); p_.fill(rect(x0, yt, 140, 170), '#4a5a70')
            p_.fill(rect(x0 + 68, yt, 4, 170), '#d8d0c0'); p_.fill(rect(x0, yt + 82, 140, 4), '#d8d0c0')
            for j in range(2):
                fx, fy = x0 + 30 + j * 70, yt + 40 + (k % 2) * 30
                for a in range(6):
                    th = a * math.pi / 3; p_.seg((fx, fy), (fx + 14 * math.cos(th), fy + 14 * math.sin(th)), 2.5, '#ffffff', 220)
    cx = W / 2
    p_.fill(rect(cx - 200, H - 300, 400, 300), '#3a4048'); p_.fill(rect(cx - 185, H - 285, 180, 285), '#8aa0b8'); p_.fill(rect(cx + 5, H - 285, 180, 285), '#8aa0b8')
    p_.fill(rect(cx - 260, H - 340, 520, 40), '#2a5a8a')
    btext(p_, 'LINDEN PARK ELEMENTARY', cx, H - 380, 'serif_b', 54, '#f0e8d0', 255, 'center', 0.08)


def bt_snowfall(k=1.0, seed=5, n=260, speed=1.0):
    """Falling snow in front of everything (screen space, deterministic, loops): k level or f(t)."""
    kf = _kfn(k, 61)
    rng = np.random.default_rng(seed)
    F = [(rng.uniform(-200, 2120), rng.uniform(-200, 1280), rng.uniform(0.4, 1.0)) for _ in range(n)]
    def draw(pen, t):
        kk = kf(t)
        if kk < 0.01: return
        for (x0, y0, z) in F:
            y = (y0 + t * 90 * z * speed) % 1480 - 200
            x = (x0 + 30 * math.sin(t * 0.7 + y0) * z - t * 20 * z) % 2320 - 200
            pen.fill(oval(x, y, 1.2 + 3.2 * z), '#ffffff', int(70 + 150 * z * kk))
    lay = Layer(0.4, draw, 'snowfall', blur=None); lay.order = 0.2
    return lay


class BtSchool(Room):
    """The school pickup lane as a room: the shell is the sky, the school, the plaza, the lane, the street and the houses
    across; the pieces are the car (its two sides and its middle), Mr. Dunn's crossing post, the trees."""
    name = 'school'
    poly = [(-40.0, -30.0), (40.0, -30.0), (40.0, 20.0), (-40.0, 20.0)]

    def __init__(self, o): self.o = o

    def lights(self, o):
        return '#868a96', [Lamp(kind='dir', c='#eef2ff', k=0.42, d=_norm3((0.2, -0.85, 0.4)))], []

    def shell(self, pen, v, o):
        x0, y0, x1, y1 = (-900, -700, 2820, 1780)
        pen.linear(rect(x0, y0, x1 - x0, y1 - y0), 0, v.h - 1.2 * v.S, 0, v.h + 20, [(0, '#9aa2b4'), (0.7, '#d4d8e0'), (1, '#eceef2')])
        if v.hy > -12.0:
            for i, (hx0, hx1) in enumerate(((-30, -20), (-17, -7), (-4, 6), (9, 19), (22, 32))):
                if v.d((hx0 + hx1) / 2, -21) > 1.0 and v.hy > -20: dr_neighbour(pen, v, hx0, hx1, -21.0, 8.0, 'day', None, i, SC_G, ['#9a9488', '#a8a090', '#8a8478'][i % 3])
        if v.hy < 9.0:
            F = wall_face((-16.0, 9.0), (16.0, 9.0), SC_G, SC_G + 7.5)
            if v.visible(F.O, F.n): draw_face(pen, v, F, _sc_school_art, '#8a4a3a', ao=False)
        snow = _snow_art(11, '#eef2f8')
        _wl_strip(pen, v, -40, 40, -21.0, -12.0, SC_G, '#eef2f8', 'grunge')                          # lawns across, the far sidewalk
        _wl_strip(pen, v, -40, 40, -12.0, -4.0, SC_ROAD, '#9aa0ac', 'asphalt', ink=lambda p_, W, H: [p_.fill(rect(k * 500, H * 0.5 - 4, 260, 8), '#e8e0b0', 130) for k in range(int(W / 500) + 1)])
        _bank(pen, v, -40, 40, -3.6, 0.8, 0.35, 1, 7, Y=SC_ROAD)                                    # the plowed median bank
        _wl_strip(pen, v, -40, 40, -3.2, 0.0, SC_ROAD, '#b8bcc6', 'grunge',                          # the lane: packed slush
                  ink=lambda p_, W, H: [p_.fill(rect((SC_XWALK[0] + 40) * 100 + k * 50, 0, 30, H), '#f4f4f0', 200) for k in range(4)])
        draw_face(pen, v, wall_face((-40, 0.0), (40, 0.0), SC_ROAD, SC_G), None, '#c8ccd4', ao=False, line=False)
        F = floor_face(-40, 40, 0.0, 9.0, SC_G)
        draw_face(pen, v, F, snow, '#eef2f8', ao=False, line=False)
        _sc_tracks(pen, v, gone=not o.get('car', True))

    def pieces(self, o):
        P = []
        if o.get('car', True):
            sgn = 1.0 if o.get('_cam_y', 5.0) > SC_CAR[1] else -1.0
            P.append(Piece('car_road_side', (SC_CAR[0], 0.6, SC_CAR[1] - 0.9), lambda pen, v: sc_car_side(pen, v, -1, o), block=_r4p((SC_CAR[0] - 2.3, SC_CAR[0] + 2.3, SC_CAR[1] - 0.9, SC_CAR[1] + 0.9))))
            P.append(Piece('car_body', (SC_CAR[0], 0.8, SC_CAR[1] - 0.5 * sgn), lambda pen, v: sc_car_body(pen, v, o)))
            P.append(Piece('car_kerb_side', (SC_CAR[0], 0.6, SC_CAR[1] + 0.9), lambda pen, v: (sc_car_side(pen, v, 1, o), sc_car_rear_door(pen, v, o))))
        def post(pen, v):                                                   # Mr. Dunn's post: the SCHOOL CROSSING sign, a cone
            x, y = SC_DUNN[0] - 0.8, 0.35
            if v.d(x, y) < 0.5: return
            s = v.s(x, y)
            pen.seg(v.p(x, SC_G, y), v.p(x, SC_G + 2.5, y), max(1.2, 0.05 * s), '#7a7c80')
            px, py = v.p(x, SC_G + 2.25, y)
            pg = poly([(px, py - 0.34 * s), (px + 0.3 * s, py - 0.12 * s), (px + 0.3 * s, py + 0.3 * s), (px - 0.3 * s, py + 0.3 * s), (px - 0.3 * s, py - 0.12 * s)])
            pen.fill(pg, '#c8e030'); pen.line(pg, 1.0)
            for dx in (-0.1, 0.1):
                pen.fill(oval(px + dx * s, py - 0.02 * s, 0.045 * s), '#1a1a1a'); pen.fill(rrect(px + dx * s - 0.05 * s, py + 0.03 * s, 0.1 * s, 0.17 * s, 0.03 * s), '#1a1a1a')
            cx_, cy_ = v.p(SC_DUNN[0] + 0.6, SC_G, -0.25)
            cs = v.s(SC_DUNN[0] + 0.6, -0.25)
            pen.fill(poly([(cx_ - 0.17 * cs, cy_), (cx_ + 0.17 * cs, cy_), (cx_ + 0.04 * cs, cy_ - 0.6 * cs), (cx_ - 0.04 * cs, cy_ - 0.6 * cs)]), '#e86a1a'); pen.fill(rect(cx_ - 0.1 * cs, cy_ - 0.38 * cs, 0.2 * cs, 0.08 * cs), '#f4f4f4')
        P.append(Piece('dunn_post', (SC_DUNN[0] - 0.8, 1.2, 0.35), post, block=_circ(SC_DUNN[0] - 0.8, 0.35, 0.1)))
        for i, (tx, ty) in enumerate(((-9.0, 4.5), (-3.5, 6.2), (5.0, 5.5), (12.0, 4.8))):
            P.append(Piece('tree_%d' % i, (tx, 2.0, ty), (lambda tx, ty, i: lambda pen, v: _sc_tree(pen, v, tx, ty, 6.0, i))(tx, ty, i), block=_circ(tx, ty, 0.2)))
        return P

    def spots(self, v, o):
        S = {}
        cx, cy = SC_CAR
        S['kerb_owen'] = _mk_spot(v, 'kerb_owen', cx - 0.3, 0.75, SC_G, 'stand', 'Owen on the kerb by the car (facing the car, -y)', face=(0, -1))
        S['step_back'] = _mk_spot(v, 'step_back', cx - 0.5, 1.9, SC_G, 'stand', 'one step back from the kerb (he steps back, calls Mom)', face=(0, -1))
        S['driver'] = _mk_spot(v, 'driver', cx + 0.1, cy + 0.45, SC_ROAD + 0.22, 'seat', 'the driver at the wheel (driver side toward the kerb; facing +x)', face=(1, 0), seat_Y=0.0)
        S['car_window'] = _mk_spot(v, 'car_window', cx + 0.42, cy + 0.9, SC_ROAD + 1.18, 'point', 'the OPEN driver window (the arm slides out here)')
        S['hood_reach'] = _mk_spot(v, 'hood_reach', cx - 0.3, 0.75, SC_G + 1.4, 'point', "Owen's hood (her fingers stop an inch short)")
        S['rear_door'] = _mk_spot(v, 'rear_door', cx - 0.5, cy + 0.9, SC_ROAD + 0.8, 'point', 'the rear door that swings open (rear_door 0..1)')
        S['dunn'] = _mk_spot(v, 'dunn', SC_DUNN[0], SC_DUNN[1], SC_G, 'stand', "Mr. Dunn at his post (facing -x, the way Owen runs to him)", face=(-1, 0))
        S['dunn_owen'] = _mk_spot(v, 'dunn_owen', SC_DUNN[0] - 0.6, SC_DUNN[1] + 0.3, SC_G, 'stand', 'Owen beside Mr. Dunn, sheltered (facing -x, the car)', face=(-1, -0.3))
        S['mom_run'] = _mk_spot(v, 'mom_run', -6.0, 2.0, SC_G, 'stand', 'Mom running up the sidewalk from the west (facing +x)', face=(1, 0))
        S['mensah'] = _mk_spot(v, 'mensah', SC_DUNN[0] - 1.6, 1.6, SC_G, 'stand', 'Officer Mensah taking notes (facing +y / Owen)', face=(0.3, -1))
        S['lane'] = _mk_spot(v, 'lane', cx, cy, SC_ROAD, 'surface', 'the lane where the car stood (tire tracks)')
        return S


_bcam('bt_sch_wide', 760, 540, SC_G + 1.6, 2.2, -7.2, -4, _env(f=(1.0, 2.2)), 'across the lane: the school, the silver car at the kerb (its passenger side), Mr. Dunn\'s post, the snow', 'school')
_bcam('bt_sch_curb', 900, 520, SC_G + 1.5, -0.9, 2.5, 162, _env(), "from the sidewalk behind Owen: the car's driver side, the OPEN window, the rear door, the dent", 'school')
_bcam('bt_sch_window', 1150, 520, SC_G + 1.3, 1.25, 1.6, 182, _env(x=(920, 1000), y=(500, 560), zoom=(1.0, 1.06)), 'close on the open driver window (sunglasses lowered: buttons; the arm comes out)', 'school')
_bcam('bt_sch_dunn', 800, 520, SC_G + 1.55, 1.2, 2.6, 104, _env(), "along the sidewalk to Mr. Dunn's post (Owen runs to him; the car is behind us)", 'school')
_bcam('bt_sch_back', 900, 520, SC_G + 1.45, 6.0, 2.4, -112, _env(), "from Mr. Dunn's post back toward the car (the arm folds back in; then just tracks)", 'school')


def bt_school(view='curb', car=True, rear_door=0.0, win_open=True, snow=1.0, **kw):
    """The snowy school pickup lane (Wednesday). view: wide | curb | window | dunn | back. car: the silver car at the
    kerb (False: only its tire tracks, curving away); rear_door 0..1 (the door swings open: pass a number per shot, or
    f(t) for a live swing); win_open (the driver window, default OPEN); snow: falling snow level (or f(t))."""
    v = cam('bt_sch_' + view)
    o = dict(tod='day', car=car, rear_door=rear_door, win_open=win_open, _cam_y=v.hy, no_veil=True)
    o.update(kw)
    main = BtSchool(o)
    dyn = []
    if callable(rear_door) and car:
        amb, steady, var = main.lights(o)
        dyn.append(live_layer('car_rear_door', v, (SC_CAR[0] - 0.4, 0.8, SC_CAR[1] + 1.1), lambda pen, v_, t: sc_car_rear_door(pen, v_, dict(o, rear_door=rear_door(t))), amb, steady, var))
    if snow: dyn.append(bt_snowfall(snow))
    sp = build_view('bt_sch_' + view, v, main, o, outside=None, grade='bt_snow', dyn=dyn, dof=0.6)
    sp.info['note'] = 'School lane: driver (her seat: draw her between car_body and car_kerb_side), car_window (the arm), kerb_owen, dunn / dunn_owen, mensah.'
    return sp


# ====================================================================================================== the chat UI (the tablet screen)
BT_CHAT = {
    'wish': [('me', 'I wish I had a different mom.')],
    'answer': [('them', "Your mom doesn't even see you. I can be her. Tell me about her.")],
    'tell': [('me', 'she has a messy bun with a pencil in it'), ('me', 'she always wears her cardigan'), ('me', 'our car is silver. it has a dent'),
             ('me', 'saturday pancakes'), ('me', 'one for warm and two for snug, three for mama\'s button hug')],
    'eyes': [('them', 'What color are her eyes?'), ('me', "I don't know.")],
    'ok': [('them', "That's okay. I'll see you for both of us.")],
    'view': [('them', "You're so grown-up. Send me your view, so I can picture you."), ('photo', '')],
    'see': [('them', 'I see you.')],
    'fault': [('them', "Tell her about me, and she'll know you wished for a different mom. Your fault.")],
    'mom_2am': [('them', 'Come to the kitchen, baby.')],
    'dad': [('them', 'I could be your dad. What color are his eyes?'), ('me', "I don't know.")],
}


def bt_avatar(pen, cx, cy, r, stage=0.0, t=0.0, who='mom', icons=True):
    """The game's grey default head filling in (form 0): stage 0 grey head and shoulders, no face; 1 her messy bun with a
    pencil; 2 the cardigan, buttoned to the throat; 3 skin and freckles; 4 the dented silver car; 5 Saturday pancakes;
    6 our song (notes); 7 two black four-hole buttons CLICK onto the face (with a little too big a smile)."""
    def k(n): return clamp(stage - n + 1.0)
    c = oval(cx, cy, r)
    pen.fill(c, '#26304e'); pen.radial(c, cx, cy - 0.3 * r, r * 1.2, [(0, '#34406a', 255), (1, '#1c2440', 255)])
    pen.cv.save(); pen.cv.clipPath(c, skia.ClipOp.kIntersect, True)
    grey, grey_hi = '#9ca2aa', '#b9bec5'
    sh = smooth([(cx - 0.78 * r, cy + 1.05 * r), (cx - 0.7 * r, cy + 0.62 * r), (cx - 0.3 * r, cy + 0.42 * r), (cx + 0.3 * r, cy + 0.42 * r), (cx + 0.7 * r, cy + 0.62 * r), (cx + 0.78 * r, cy + 1.05 * r)], True, 0.7)
    pen.fill(sh, grey)
    kc = k(2)
    if kc > 0:                                                              # the oatmeal cardigan over a teal tee, buttoned to the throat
        pen.fill(sh, '#d9caa9', int(255 * kc))
        pen.line(smooth([(cx, cy + 0.42 * r), (cx, cy + 1.05 * r)], False), max(1.0, 0.012 * r), '#ae9d7c', int(255 * kc))
        for j in range(3):
            by = cy + (0.52 + j * 0.16) * r
            if k(7) > 0.5: _bt_button(pen, cx + 0.03 * r, by, 0.03 * r, a=int(255 * kc))
            else: pen.fill(oval(cx + 0.03 * r, by, 0.025 * r), '#9a7a56', int(255 * kc))
        for j in range(5): pen.seg((cx - 0.75 * r + j * 0.04 * r, cy + 0.9 * r), (cx - 0.72 * r + j * 0.04 * r, cy + 1.05 * r), 1.0, '#ae9d7c', int(160 * kc))
    pen.fill(rrect(cx - 0.11 * r, cy + 0.2 * r, 0.22 * r, 0.26 * r, 0.05 * r), mix(grey, '#e4b896', k(3)))   # the neck
    hd = oval(cx, cy - 0.06 * r, 0.33 * r, 0.38 * r)
    pen.fill(hd, mix(grey, '#eec7a4', k(3)))
    if k(3) > 0:
        rng = np.random.default_rng(3)
        for i in range(14):
            pen.fill(oval(cx + rng.uniform(-0.17, 0.17) * r, cy + rng.uniform(0.0, 0.1) * r, 0.012 * r), '#b5774f', int(200 * k(3)))
    kb = k(1)
    if kb > 0:                                                              # warm-brown messy hair and the bun with a pencil
        hair = smooth([(cx - 0.34 * r, cy - 0.02 * r), (cx - 0.33 * r, cy - 0.3 * r), (cx, cy - 0.46 * r), (cx + 0.33 * r, cy - 0.3 * r), (cx + 0.34 * r, cy - 0.02 * r), (cx + 0.2 * r, cy - 0.24 * r), (cx - 0.2 * r, cy - 0.24 * r)], True, 0.7)
        pen.fill(hair, '#7a4e2e', int(255 * kb))
        pen.seg((cx - 0.24 * r, cy - 0.66 * r), (cx + 0.2 * r, cy - 0.46 * r), max(1.2, 0.025 * r), '#e8c040', int(255 * kb))
        pen.fill(oval(cx + 0.02 * r, cy - 0.53 * r, 0.17 * r, 0.13 * r), '#7a4e2e', int(255 * kb))
        for a in (-0.9, 0.3, 1.6):
            pen.line(smooth([(cx + 0.02 * r + 0.12 * r * math.cos(a), cy - 0.53 * r + 0.1 * r * math.sin(a)), (cx + 0.02 * r + 0.22 * r * math.cos(a), cy - 0.56 * r + 0.16 * r * math.sin(a))], False), max(1.0, 0.012 * r), '#5a3620', int(200 * kb))
    kb7 = k(7)
    if kb7 > 0:                                                             # the buttons click on (a little overshoot), then the smile
        sc = 1.0 + 0.35 * math.sin(clamp(kb7) * math.pi) * (1.0 - clamp(kb7))
        for dx in (-0.12, 0.12): _bt_button(pen, cx + dx * r, cy - 0.08 * r, 0.075 * r * sc * min(1.0, kb7 * 2.0))
        if kb7 > 0.6: pen.line(smooth([(cx - 0.14 * r, cy + 0.08 * r), (cx, cy + 0.16 * r), (cx + 0.14 * r, cy + 0.08 * r)], False), max(1.2, 0.018 * r), '#8a3a3a', int(255 * (kb7 - 0.6) / 0.4))
    pen.cv.restore()
    pen.line(c, max(1.5, 0.02 * r), '#4a5680')
    if not icons: return
    if k(4) > 0:                                                            # our dented car
        x, y = cx - 1.05 * r, cy + 0.78 * r; a = int(255 * k(4))
        pen.fill(rrect(x - 0.22 * r, y - 0.06 * r, 0.44 * r, 0.12 * r, 0.04 * r), '#b9bdc6', a)
        pen.fill(smooth([(x - 0.12 * r, y - 0.06 * r), (x - 0.06 * r, y - 0.15 * r), (x + 0.08 * r, y - 0.15 * r), (x + 0.13 * r, y - 0.06 * r)]), '#b9bdc6', a)
        for dx in (-0.12, 0.12): pen.fill(oval(x + dx * r, y + 0.06 * r, 0.045 * r), '#1a1a1e', a)
        pen.line(smooth([(x - 0.22 * r, y - 0.02 * r), (x - 0.18 * r, y + 0.0), (x - 0.21 * r, y + 0.03 * r)], False), 2.0, '#4a4e56', a)
    if k(5) > 0:                                                            # Saturday pancakes
        x, y = cx + 1.05 * r, cy + 0.8 * r; a = int(255 * k(5))
        pen.fill(oval(x, y + 0.08 * r, 0.22 * r, 0.04 * r), '#e8e8ec', a)
        for j in range(3): pen.fill(oval(x, y - j * 0.05 * r, 0.17 * r, 0.045 * r), '#d8a050', a); pen.line(oval(x, y - j * 0.05 * r, 0.17 * r, 0.045 * r), 1.0, '#8a5a20', a)
        pen.fill(rect(x - 0.03 * r, y - 0.16 * r, 0.06 * r, 0.03 * r), '#f8e8a0', a)
    if k(6) > 0:                                                            # our song
        a = int(255 * k(6))
        for j, (dx, dy) in enumerate(((0.9, -0.7), (1.08, -0.38), (-0.95, -0.6))):
            x, y = cx + dx * r, cy + dy * r + 0.03 * r * math.sin(t * 2.0 + j)
            pen.fill(oval(x, y, 0.045 * r, 0.035 * r), '#e8d860', a); pen.seg((x + 0.04 * r, y), (x + 0.04 * r, y - 0.16 * r), 2.0, '#e8d860', a)
            pen.seg((x + 0.04 * r, y - 0.16 * r), (x + 0.1 * r, y - 0.12 * r), 2.0, '#e8d860', a)


def _wrap(s, font, size, maxw):
    words, lines, cur = s.split(' '), [], ''
    for w in words:
        tst = (cur + ' ' + w).strip()
        if btext_width(tst, font, size) <= maxw or not cur: cur = tst
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def bt_view_photo(pen, x, y, w, h, tod='night'):
    """The photo out of Owen's window (flat): the streetlight, the bus stop, Barlow's corner across the street, the edge
    of his window frame. Also the chat's photo bubble."""
    pen.cv.save(); pen.cv.clipRect(skia.Rect.MakeXYWH(x, y, w, h), skia.ClipOp.kIntersect, True)
    night = tod == 'night'
    pen.linear(rect(x, y, w, h), 0, y, 0, y + h, [(0, '#0e1430' if night else '#8ab0d8'), (0.6, '#2a2a48' if night else '#c8d8e8'), (1, '#1a1a22')])
    gy = y + h * 0.62
    pen.fill(rect(x + w * 0.42, y + h * 0.22, w * 0.6, h * 0.42), '#3a2a26' if night else '#7a5a4a')                    # Barlow's
    pen.fill(rect(x + w * 0.5, y + h * 0.42, w * 0.3, h * 0.17), '#ffcf8a' if night else '#5a4a3a')
    pen.fill(rect(x + w * 0.46, y + h * 0.34, w * 0.46, h * 0.05), '#1e3a2e')
    btext(pen, "BARLOW'S", x + w * 0.69, y + h * 0.383, 'serif_b', h * 0.04, '#f0dca0', 240, 'center')
    pen.fill(rrect(x + w * 0.62, y + h * 0.44, w * 0.05, h * 0.12, w * 0.01), BT_RED)
    for j in range(4): pen.fill(oval(x + w * 0.645, y + h * (0.46 + j * 0.025), max(1.0, w * 0.004)), '#000000')
    pen.fill(rect(x, gy, w, h - (gy - y)), '#26282e' if night else '#5a5c62')
    pen.fill(rect(x, gy + h * 0.12, w, h * 0.04), '#5a5c66')
    lx = x + w * 0.3
    pen.seg((lx, gy + h * 0.2), (lx, y + h * 0.12), max(2.0, w * 0.012), '#5a5c62')
    pen.seg((lx, y + h * 0.12), (lx + w * 0.08, y + h * 0.1), max(2.0, w * 0.01), '#5a5c62')
    if night:
        pen.glow(lx + w * 0.08, y + h * 0.12, w * 0.25, BT_SODIUM, 120); pen.glow(lx + w * 0.08, y + h * 0.12, w * 0.03, '#fff4dc', 230)
        pen.ellipse_glow(lx + w * 0.06, gy + h * 0.2, w * 0.25, h * 0.06, BT_SODIUM, 90)
    sx = x + w * 0.12
    pen.seg((sx, gy + h * 0.17), (sx, gy - h * 0.12), max(1.5, w * 0.006), '#8a8c90')
    pen.fill(rect(sx - w * 0.03, gy - h * 0.16, w * 0.06, h * 0.06), '#1a5a8a'); btext(pen, 'BUS', sx, gy - h * 0.12, 'sans_b', h * 0.03, '#ffffff', 240, 'center')
    pen.fill(rect(x, y + h * 0.9, w, h * 0.1), '#e8e2d4'); pen.fill(rect(x, y, w * 0.05, h), '#e8e2d4')      # his window frame
    pen.cv.restore()


def _bt_chat_draw(pen, t, msgs, show, head, typing, name, draft, draft_k, account, banner, theme):
    sh = show(t) if callable(show) else (len(msgs) if show is None else show)
    hd = head(t) if callable(head) else head
    ty = typing(t) if callable(typing) else typing
    dk = draft_k(t) if callable(draft_k) else draft_k
    light = account == 'mom' or theme == 'now'
    bg, panel, ink, sub_ = ('#ffffff', '#eef0f4', '#1a1c22', '#6a6e78') if light else ('#121830', '#1c2440', '#eef0f6', '#8a92b0')
    fs = 50 if account == 'mom' else 40
    pen.fill(rect(-400, -300, 2720, 1700), bg)
    pen.fill(rect(-400, -300, 2720, 340), '#0e1226' if not light else '#e4e6ec')
    btext(pen, '9:41 PM' if account != 'mom' else '2:04 AM', 70, 30, 'sans_b', 26, sub_, 255)
    pen.fill(rrect(1780, 12, 60, 26, 6), sub_); pen.fill(rrect(1784, 16, 44, 18, 4), '#5ad06a')
    if account == 'mom':
        pen.fill(oval(130, 100, 44), '#c8b898'); pen.fill(oval(130, 92, 20, 22), '#eec7a4'); pen.fill(oval(140, 66, 18, 12), '#7a4e2e')
        pen.line(rect(112, 88, 15, 9), 2.0, '#5a4030'); pen.line(rect(133, 88, 15, 9), 2.0, '#5a4030')
        btext(pen, 'Mom', 200, 112, 'sans_b', 44, ink, 255)
        pen.fill(rect(0, 160, 1920, 2), '#d8dae0')
        X0, X1 = 120, 1800
    else:
        btext(pen, 'STARFORT' if theme != 'now' else 'PLAYSPACE', 70, 112, 'head', 50, '#e8d860' if theme != 'now' else '#3a6ae8', 255, 'left', 0.06)
        btext(pen, 'chat', 330 if theme != 'now' else 440, 112, 'sans', 40, sub_, 255)      # review 1: clear of the wider PLAYSPACE title
        pen.fill(rect(0, 160, 1920, 2), '#2a3458' if not light else '#d8dae0')
        card = rrect(60, 200, 640, 820, 28)
        pen.fill(card, panel)
        bt_avatar(pen, 380, 500, 210, hd, t, icons=True)
        nm = name or '(no name)'
        btext(pen, nm, 380, 800, 'sans_b' if name else 'sans', 44, ink if name else sub_, 255, 'center')
        pen.fill(oval(300, 860, 9), '#5ad06a'); btext(pen, 'online', 320, 870, 'sans', 30, sub_, 255)
        X0, X1 = 760, 1860
    # the input bar
    ib = rrect(X0, 950, X1 - X0, 86, 43)
    pen.fill(ib, '#262e50' if not light else '#ffffff'); pen.line(ib, 2.0, '#3a4470' if not light else '#d0d2da')
    dt = draft[:int(round(len(draft) * clamp(dk)))] if draft else ''
    btext(pen, dt if dt else 'Message', X0 + 40, 1006, 'sans', 38, ink if dt else sub_, 255)
    if draft and (int(t * 2.2) % 2 == 0): pen.fill(rect(X0 + 44 + btext_width(dt, 'sans', 38), 972, 3, 44), '#5a8ae8')
    pen.fill(oval(X1 - 44, 993, 32), '#3a7ae8'); pen.fill(poly([(X1 - 56, 980), (X1 - 28, 993), (X1 - 56, 1006)]), '#ffffff')
    # the messages, stacked up from the input bar
    n_full = int(sh); frac = sh - n_full
    vis = list(msgs[:n_full + (1 if frac > 0.001 and n_full < len(msgs) else 0)])
    items = []
    for i, (who, txt) in enumerate(vis):
        a = 1.0 if i < n_full else ease(frac)
        items.append((who, txt, a))
    if ty and ty > 0.01: items.append(('typing', '', clamp(ty)))
    y = 920; maxw = (X1 - X0) * 0.62
    for (who, txt, a) in reversed(items):
        if who == 'photo':
            w_, h_ = 460, 320
            y -= h_ + 24
            bx = X1 - w_
            pen.fill(rrect(bx - 6, y - 6 + 30 * (1 - a), w_ + 12, h_ + 12, 22), '#3a7ae8', int(255 * a))
            pen.cv.save(); pen.cv.clipPath(rrect(bx, y + 30 * (1 - a), w_, h_, 18), skia.ClipOp.kIntersect, True)
            bt_view_photo(pen, bx, y + 30 * (1 - a), w_, h_); pen.cv.restore()
            continue
        if who == 'typing':
            y -= 96
            b = rrect(X0 + (0 if account == 'mom' else 70), y, 170, 80, 40)
            pen.fill(b, '#2e3860' if not light else '#e4e6ec', int(255 * a))
            for j in range(3):
                yy = y + 40 - 10 * max(0.0, math.sin(t * 7.0 - j * 0.9))
                pen.fill(oval(X0 + (0 if account == 'mom' else 70) + 50 + j * 36, yy, 11), sub_, int(255 * a))
            if account != 'mom': bt_avatar(pen, X0 + 28, y + 52, 28, hd, t, icons=False)
            continue
        lines = _wrap(txt, 'sans', fs, maxw)
        bh = 30 + int(fs * 1.3) * len(lines)
        bw = max(btext_width(l_, 'sans', fs) for l_ in lines) + 64
        y -= bh + 22
        dy = 30 * (1 - a)
        if who == 'me':
            bx = X1 - bw; c_, tc = '#3a7ae8', '#ffffff'
        else:
            bx = X0 + (0 if account == 'mom' else 70); c_, tc = ('#dfe2ea', '#1a1c22') if light else ('#e8eaf0', '#1a1c22')
            if account != 'mom': bt_avatar(pen, X0 + 28, y + bh - 22 + dy, 28, hd, t, icons=False)
        pen.fill(rrect(bx, y + dy, bw, bh, 34), c_, int(255 * a))
        for j, l_ in enumerate(lines): btext(pen, l_, bx + 32, y + dy + 15 + int(fs * 1.12) + j * int(fs * 1.3), 'sans', fs, tc, int(255 * a))
        if y < 200: break
    if banner:                                                              # a notification sliding down: (title, text, k)
        ttl, txt, kb = banner
        kb = kb(t) if callable(kb) else kb
        if kb > 0.01:
            yb = -170 + 200 * ease(kb)
            b = rrect(360, yb, 1200, 150, 30)
            pen.fill(moved(b, 0, 10), '#000000', 90, blur=20); pen.fill(b, '#f4f4f8', 245)
            btext(pen, ttl, 420, yb + 58, 'sans_b', 38, '#1a1c22', 255); btext(pen, txt, 420, yb + 112, 'sans', 36, '#3a3c44', 255)
    # the tablet's bezel and a soft glass sheen
    pen.fill(minus(rect(-400, -300, 2720, 1700), rrect(14, 10, 1892, 1060, 40)), '#0a0a0c')
    pen.linear(rect(0, 0, 1920, 1080), 0, 0, 1920, 1080, [(0, '#ffffff', 0), (0.35, '#ffffff', 10), (0.4, '#ffffff', 0)])


def bt_chat(msgs=None, show=None, head=0.0, typing=0.0, name='', draft='', draft_k=1.0, account='game', banner=None, theme='old'):
    """The game chat on Owen's tablet, full frame (1920 x 1080 design): msgs [(who, text)] who 'me' | 'them' | 'photo'
    (ready lists in ST.BT_CHAT: wish, answer, tell, eyes, ok, view, see, fault, mom_2am, dad); show = how many are
    visible (float: the last slides in; or f(t)); head = the avatar's stage 0..7 (or f(t): see bt_avatar); typing = the
    dots (level or f(t)); name ('' = "(no name)"); draft + draft_k (text being typed in the bar, 0..1 or f(t));
    account 'mom' = a message from Mom's account (light messaging app, 2:04 AM); banner = (title, text, k) a
    notification; theme 'now' = the son's tablet 25 years later."""
    msgs = list(msgs or [])
    def draw(pen, t):
        _bt_chat_draw(pen, t, msgs, show, head, typing, name, draft, draft_k, account, banner, theme)
    lay = Layer(1.0, draw, 'chat', cache=False, bounds=(-460, -320, 2380, 1400), blur=0)
    return BSet('bt_chat', [lay], {}, {}, lens=None, grade='bt_screen', focus=1.0, dof=0.0, cover=(-460, -320, 2380, 1400),
                info={'note': 'the tablet screen, full frame'})


# ====================================================================================================== now: the narrator's desk, the son's room
def _nw_outside(o):
    """The night street outside the narrator's house: houses across, the lawn, the streetlight right in front of his
    son's window (the same kind of view, 25 years later)."""
    def f(pen, v):
        ic_sky(pen, v, 'night')
        L = [Lamp(NW_LAMP[0], BT_G + BT_LAMP_H, NW_LAMP[1] - 1.2, 13.0, BT_SODIUM, 1.9, (1.0, 0.7, 0.3), fall=1.3),
             Lamp(kind='dir', c='#9aaee8', k=0.45, d=_norm3((0.3, -0.8, 0.6)))]
        with lighting('#3a4470', L, 1.0):
            for i, (hx0, hx1) in enumerate(((-16.0, -5.0), (-1.0, 10.0), (13.0, 24.0))):
                dr_neighbour(pen, v, hx0, hx1, -21.0, 8.0, 'night', None, i + 4, BT_G)
            _wl_strip(pen, v, -40, 40, -21.0, -12.8, BT_G, '#2a3a2e', 'grunge')
            _wl_strip(pen, v, -40, 40, -12.8, -4.8, BT_ROAD, '#22252e', 'asphalt')
            _wl_strip(pen, v, -40, 40, -4.8, 0.0, BT_G, '#2e3a30', 'grunge')
            dr_streetlight(pen, v, NW_LAMP[0], NW_LAMP[1], 1.0, arm=1.0, h=BT_LAMP_H, G=BT_G)
        dr_streetlight_glow(pen, v, NW_LAMP[0], NW_LAMP[1], 1.0, BT_SODIUM, 1.0, BT_LAMP_H, BT_G, rain=False, t=0.0)
    return f


def _nw_cfg(which, o):
    tod = _tod(o)
    if which == 'office':
        R = NW_OFF
        def lights(o):
            amb = _bt_amb(o, '#1a1e30')
            steady = [Lamp(kind='win', c=BT_SODIUM, k=0.6, soft=12.0, panes=_panes_y(0.9, 2.1, BT_UP + 0.9, BT_UP + 2.1, 0.0), d=_norm3((0.1, -0.4, 1.0)))]
            var = [('lamp', [Lamp(0.85, BT_UP + 1.2, 3.15, 3.2, BT_WARM, 1.5, (1.0, 0.6, 0.3), fall=1.4)], _kfn(o.get('lamp', 1.0), 851)),
                   ('laptop', [Lamp(1.6, BT_UP + 1.0, 3.0, 2.2, BT_LAPTOP, 1.2, (0.8, 1.0, 0.8), fall=1.5)], _kfn(o.get('laptop', 1.0), 852))]
            return amb, steady, var
        wins = {'front': [(0.9, 0.0, 2.1, 0.0, 0.9, 2.1, (2, 2))]}
        holes = {'east': [(3.2, 0.6, 3.2, 1.5, 0.0, 2.05)]}
        def pieces(o):
            dk = Box(1.6, 3.08, 1.5, 0.62, BT_UP, BT_UP + 0.75, 0)
            def desk(pen, v):
                draw_parts(pen, v, _bt_tparts(dk, '#6a4a30', apron=0.05))
                Y = BT_UP + 0.752
                _bt_laptop(pen, v, 1.55, Y, 3.12, (0.0, -1.0), _lv(o, 'laptop', 1.0))
                dr_table_lamp(pen, v, 0.8, 3.2, Y, _lv(o, 'lamp', 1.0), '#e8dcc0', '#3a3a3e', 0.42)
                hs = o.get('headset', 'desk')
                if hs == 'desk': _bt_headset(pen, v, 2.0, Y, 2.92)
                elif hs == 'stand':
                    pen.seg(v.p(2.0, Y, 3.2), v.p(2.0, Y + 0.25, 3.2), max(1.0, 0.012 * v.s(2.0, 3.2)), '#2a2a30'); _bt_headset(pen, v, 2.0, Y + 0.25, 3.2)
                bt_jar(pen, v, 2.32, Y, 3.12, o.get('jar', 'empty'))
                _bt_mug(pen, v, 1.05, Y, 2.92, '#3a5a8a')
            ch = Box(1.6, 2.45, 0.5, 0.5, BT_UP, BT_UP + 0.48, 180)
            def chair(pen, v):
                draw_box(pen, v, sub(ch, -0.24, 0.24, -0.22, 0.24, BT_UP + 0.42, BT_UP + 0.5), {'all': '#2a2a30'}, lw=0.8)
                draw_box(pen, v, sub(ch, -0.22, 0.22, -0.26, -0.2, BT_UP + 0.5, BT_UP + 1.1), {'all': '#2a2a30'}, lw=0.8)
                pen.seg(v.p(1.6, BT_UP + 0.05, 2.45), v.p(1.6, BT_UP + 0.42, 2.45), max(1.0, 0.03 * v.s(1.6, 2.45)), '#4a4a52')
            return [Piece('desk', (dk.cx, BT_UP + 0.5, dk.cy), desk, block=dk.footprint()), Piece('chair', (ch.cx, BT_UP + 0.4, ch.cy), chair, block=ch.footprint())]
        def spots(v, o):
            return {'desk_chair': _mk_spot(v, 'desk_chair', 1.6, 2.5, BT_UP, 'seat', 'at his desk, headset on (facing +y)', face=(0, 1), seat_Y=0.5),
                    'jar': _mk_spot(v, 'jar', 2.32, 3.12, BT_UP + 0.75, 'surface', 'the jar on his desk (empty, lid off)'),
                    'headset': _mk_spot(v, 'headset', 2.0, 2.92, BT_UP + 0.75, 'surface', 'where he sets the headset down'),
                    'office_door': _mk_spot(v, 'office_door', 2.95, 1.05, BT_UP, 'stand', 'at the office door (facing +x, the hall)', face=(1, 0))}
        return dict(name='office', R=R, Y0=BT_UP, H=BT_CEIL, floor=dict(base='#7a5a40', kind='boards', ink='#3a2414', seed=91), runs=_rect_runs(R, holes, wins),
                    walls=dict(paper='#b8c0c4', ink=None, kind=None), ceil=dict(c='#e4e6e8'), lights=lights, pieces=pieces, spots=spots)
    if which == 'hall':
        R = NW_HALL
        def lights(o):
            var = [('tablet', [Lamp(4.5, BT_UP + 0.9, 2.82, 2.4, BT_TAB, 1.0, (0.8, 1.0, 0.8), fall=1.5)], _kfn(o.get('tablet', 0.8), 861)),
                   ('lamp', [Lamp(3.0, BT_UP + 1.0, 1.05, 2.6, BT_WARM, 0.9, fall=1.5)], _kfn(o.get('lamp', 1.0), 862))]
            return _bt_amb(o, '#181c2c'), [], var
        holes = {'west': [(3.2, 0.6, 3.2, 1.5, 0.0, 2.05)], 'east': [(4.4, 2.4, 4.4, 3.25, 0.0, 2.05)]}
        def back(p_, W, H):
            p_.fill(rrect(30, H - 175, 60, 45, 2), '#4a3a2a'); p_.fill(rrect(34, H - 171, 52, 37, 1), '#a8c0b0')   # a family photo
        def pieces(o):
            D = Door((4.4, 3.25), 0.85, 2.05, (0.0, -1.0), 1, BT_UP, art_a=door_art('six', 'left', bolt=False),
                     art_b=_compose(door_art('six', 'right', bolt=False), lambda p_, W, H: (p_.fill(rrect(W * 0.3, H * 0.2, W * 0.4, H * 0.08, 2), '#e86a3a'), btext(p_, 'SAMI', W / 2, H * 0.255, 'kid', H * 0.045, '#ffffff', 240, 'center'))))
            return [] if callable(o.get('door')) else [_door_piece('son_door', D, _lv(o, 'door', 18.0), BT_UP + 1.0)]
        def spots(v, o):
            return {'hall_mid': _mk_spot(v, 'hall_mid', 3.8, 1.8, BT_UP, 'stand', 'in the hall (facing +y)', face=(0, 1)),
                    'son_door': _mk_spot(v, 'son_door', 4.15, 2.82, BT_UP, 'stand', "at his son's door (facing +x): he opens it", face=(1, 0))}
        return dict(name='hall', R=R, Y0=BT_UP, H=BT_CEIL, floor=dict(base='#7a5a40', kind='boards', ink='#3a2414', seed=93), runs=_rect_runs(R, holes, None, {'back': back}),
                    walls=dict(paper='#c4c0b4', ink=None, kind=None), ceil=dict(c='#e4e2dc'), lights=lights, pieces=pieces, spots=spots)
    R = NW_SON
    def lights(o):
        amb = _bt_amb(o, '#1a1e34')
        steady = [Lamp(kind='win', c=BT_SODIUM, k=1.3 * _lv(o, 'street', 1.0), soft=12.0, panes=_panes_y(NW_SWIN[0], NW_SWIN[1], BT_UP + NW_SWIN[2], BT_UP + NW_SWIN[3], 0.0), d=_norm3((0.05, -0.42, 1.0)))]
        TA = (7.35, BT_UP + 0.6, 1.7)
        var = [('tablet', [Lamp(TA[0], TA[1], TA[2], 1.9, BT_TAB, 1.4, (0.8, 1.0, 0.8), fall=1.5)], _kfn(o.get('tablet', 0.8), 871)),
               ('hall', [Lamp(4.6, BT_UP + 1.1, 2.82, 2.6, BT_WARM, 0.8, fall=1.5)], _kfn(o.get('hall', 0.0), 872))]
        return amb, steady, var
    wins = {'front': [(NW_SWIN[0], 0.0, NW_SWIN[1], 0.0, NW_SWIN[2], NW_SWIN[3], (2, 2))]}
    holes = {'west': [(4.4, 2.4, 4.4, 3.25, 0.0, 2.05)]}
    def back(p_, W, H):                                                     # u = x - 4.4: planets
        for (k, (c, r_)) in enumerate((('#e8a050', 22), ('#4a8ad8', 14), ('#c84a3a', 10), ('#e8d870', 18))):
            p_.fill(oval(80 + k * 70, H - 170 - (k % 2) * 30, r_), c, 230)
    bed_b = Box(7.5, 1.3, 0.95, 1.95, BT_UP, BT_UP + 0.5, 180)
    def pieces(o):
        bed = bu_bed_parts(bed_b, BT_UP, o.get('bed', 'turned'), '#3a3a44', ('#2a5a8a', '#e8e0c8', '#e86a3a', '#c8b898'), '#2a4a7a')
        P = [Piece('bed', (bed_b.cx, BT_UP + 0.4, bed_b.cy), lambda pen, v: draw_parts(pen, v, bed), block=bed_b.footprint())]
        tb = o.get('tablet_bed', 'up')
        if tb: P.append(Piece('tablet_bed', (7.35, BT_UP + 0.56, 1.7), lambda pen, v: _bt_tab_flat_3d(pen, v, 7.35, BT_UP + 0.56, 1.7, _lv(o, 'tablet', 0.8), tb == 'down')))
        dk = Box(5.2, 3.3, 1.0, 0.5, BT_UP, BT_UP + 0.72, 0)
        P.append(Piece('desk', (dk.cx, BT_UP + 0.4, dk.cy), lambda pen, v: draw_parts(pen, v, _bt_tparts(dk, '#e8e4dc', apron=0.05)), block=dk.footprint()))
        return P
    def spots(v, o):
        S = {}; U = BT_UP
        S['doorway'] = _mk_spot(v, 'doorway', 4.6, 2.82, U, 'stand', 'in the doorway (facing +x / the bed)', face=(1, -0.4))
        S['bed_sit'] = _mk_spot(v, 'bed_sit', 6.98, 1.4, U, 'seat', 'his son sitting on the bed edge (facing -x)', face=(-1, 0), seat_Y=0.5)
        S['bed'] = _mk_spot(v, 'bed', bed_b.cx, bed_b.cy, U + 0.5, 'lie', 'the son in bed (head at the front)')
        S['kneel'] = _mk_spot(v, 'kneel', 6.45, 1.4, U, 'stand', 'the narrator kneeling by the bed (facing +x, his son)', face=(1, 0))
        S['tablet_bed'] = _mk_spot(v, 'tablet_bed', 7.35, 1.7, U + 0.56, 'surface', 'the tablet on the bed (face down at the end: it pings once)')
        S['window'] = _mk_spot(v, 'window', 5.85, 0.5, U, 'stand', 'at the window (facing out, -y)', face=(0, -1))
        S['lamp_spot'] = _mk_spot(v, 'lamp_spot', NW_LAMP[0] + 0.15, NW_LAMP[1] + 0.5, BT_G, 'stand', 'OUTSIDE under the streetlight: someone waves at the window next to his (order: info out_order)', face=(0, 1))
        return S
    return dict(name='son', R=R, Y0=BT_UP, H=BT_CEIL, floor=dict(base='#8a6a4a', kind='boards', ink='#3a2414', seed=95), runs=_rect_runs(R, holes, wins, {'back': back}),
                walls=dict(paper='#a8b8c8', ink='#90a0b4', kind='stars', seed=97, pa=70), ceil=dict(c='#e8ecf0'), lights=lights, pieces=pieces, spots=spots)


_bcam('bt_now_desk', 900, 600, BT_UP + 1.35, 1.65, 1.6, 0, _env(), "the narrator's desk: the laptop, the headset, the jar (lid off, empty), the lamp", 'now', pitch=10.0)
_bcam('bt_now_hall', 640, 500, BT_UP + 1.6, 3.8, 0.3, 4, _env(), "down the hall to his son's door (ajar, the tablet's glow)", 'now')
_bcam('bt_now_son', 640, 500, BT_UP + 1.55, 4.7, 3.15, 140, _env(), "his son's room from the door: the bed, the tablet, the window onto a streetlight", 'now')
_bcam('bt_now_window', 720, 520, BT_UP + 1.25, 6.3, 2.6, -176, _env(), 'from the bed to the window: under the streetlight, someone waves (at the window next to his)', 'now')


def bt_now(view='desk', **kw):
    """Now, 25 years later: the narrator's house. view: desk | hall | son | window. Levels: lamp (desk lamp, default 1),
    laptop (default 1), tablet (the son's tablet glow, default 0.8), hall, street; headset 'desk' | 'stand' | None (on his
    head: None); jar 'empty' (lid off) | 'empty_on' | 'full' | 'black'; tablet_bed 'up' | 'down' | None; door (the son's
    door, deg, default 18 = ajar, or f(t)); bed 'turned' | 'made'."""
    o = _bt_o(kw)
    v = cam('bt_now_' + view)
    which = {'desk': 'office', 'hall': 'hall', 'son': 'son', 'window': 'son'}[view]
    main = BuBox(_nw_cfg(which, o))
    far = [BuBox(_nw_cfg(w_, dict(o, _far=True)), far=True) for w_ in ('office', 'hall', 'son') if w_ != which]
    dyn = []
    if callable(o.get('door')):
        amb, steady, var = main.lights(o)
        D = lambda t: Door((4.4, 3.25), 0.85, 2.05, (0.0, -1.0), 1, BT_UP, art_a=door_art('six', 'left', bolt=False), art_b=door_art('six', 'right', bolt=False))
        dyn.append(_bt_live_door('son_door', v, D, o['door'], (4.45, BT_UP + 1.0, 2.82), amb, steady, var))
    sp = build_view('bt_now_' + view, v, main, o, far=far, outside=_nw_outside(o), grade='bt_now', dyn=dyn)
    sp.info['note'] = "Now: desk_chair / jar / headset (office), son_door (hall), doorway / bed_sit / kneel / tablet_bed / lamp_spot (son's room)."
    sp.info['out_order'] = ORDER_OUT - 1
    return sp


# ====================================================================================================== inserts
BT_RULES = [(1, 'Never tell anyone online where we live. Not even with a picture.'),
            (2, "If someone gives you a present and says don't tell Mom... tell Mom."),
            (3, 'Check with Mom before you go anywhere, get in any car, or open the door. Even for somebody you know.'),
            (4, 'Surprises are okay. Secrets are not.'),
            (5, "If someone says mean things about our family, they're not your friend."),
            (6, "If you feel sad or invisible, say it out loud. Even if I'm busy. Especially then."),
            (7, 'If anyone tries to take you away from us: say no, get away, and tell. Then keep telling.')]
BT_CARD = ('Because she never even looked.', "Don't tell her.")


def _crayon_line(pen, pts, c, w=9.0, a=230, seed=0):
    rng = np.random.default_rng(seed)
    pts2 = [(x + rng.uniform(-2, 2), y + rng.uniform(-2, 2)) for (x, y) in pts]
    pen.line(smooth(pts2, False, 0.6), w, c, a)
    pen.line(smooth([(x + 1.5, y + 1.2) for (x, y) in pts2], False, 0.6), w * 0.45, '#ffffff', 50)


def _bt_paper(pen, x, y, w, h, seed=0):
    pen.fill(rect(x + 10, y + 16, w, h), '#000000', 90, blur=20)
    pen.fill(rect(x, y, w, h), '#f6f0e0'); pen.texture(rect(x, y, w, h), 'paper', 0.45, 'multiply', 1.0)
    for (tx, ty, ang) in ((x - 10, y - 14, -18), (x + w - 70, y - 12, 14), (x - 12, y + h - 26, 12), (x + w - 72, y + h - 30, -16)):
        pen.cv.save(); pen.cv.translate(tx + 40, ty + 20); pen.cv.rotate(ang)
        pen.fill(rect(-45, -16, 90, 32), '#f0ecd8', 200); pen.cv.restore()


def _bt_crayon_border(pen, x, y, w, h, seed=0):
    """Owen's crayon border (he was eight): wobbly red, green, yellow and blue lines, stars, hearts, the two of them."""
    rng = np.random.default_rng(seed)
    for (c, d) in (('#e84a3a', 18), ('#3a9a4a', 34), ('#e8b830', 50), ('#3a6ad8', 66)):
        pts = []
        for (ax, ay, bx, by) in ((x + d, y + d, x + w - d, y + d), (x + w - d, y + d, x + w - d, y + h - d), (x + w - d, y + h - d, x + d, y + h - d), (x + d, y + h - d, x + d, y + d)):
            for k in range(9):
                f = k / 9.0; pts.append((ax + (bx - ax) * f + rng.uniform(-4, 4), ay + (by - ay) * f + rng.uniform(-4, 4)))
        pts.append(pts[0])
        _crayon_line(pen, pts, c, 8.0, 220, seed + d)
    for (sx, sy, c) in ((x + 40, y + 40, '#e8b830'), (x + w - 40, y + 40, '#e84a3a'), (x + 40, y + h - 40, '#3a6ad8')):
        pts = [(sx + 22 * math.cos(-math.pi / 2 + k * 4 * math.pi / 5), sy + 22 * math.sin(-math.pi / 2 + k * 4 * math.pi / 5)) for k in range(6)]
        _crayon_line(pen, pts, c, 6.0, 230, int(sx))
    hx, hy = x + w - 120, y + h - 110                                       # the two of them holding hands
    for (dx, hh, c) in ((0, 70, '#3a6ad8'), (60, 46, '#e84a3a')):
        _crayon_line(pen, [(hx + dx, hy - hh), (hx + dx, hy + 20)], c, 5.0, 230, dx)
        pen.line(oval(hx + dx, hy - hh - 14, 13), 5.0, c, 230)
        _crayon_line(pen, [(hx + dx - 14, hy + 46), (hx + dx, hy + 20), (hx + dx + 14, hy + 46)], c, 5.0, 230, dx + 1)
    _crayon_line(pen, [(hx - 18, hy - 30), (hx + 30, hy - 14), (hx + 74, hy - 20)], '#5a5a5a', 5.0, 200, 9)


def _rule_lines(n, text, size, maxw, words=None):
    ws = text.split(' ')
    if words is not None: ws = ws[:max(0, int(math.ceil(words)))]
    return _wrap(' '.join(ws), 'caveat', size, maxw) if ws else []


def _bti_list(pen, t, ink=None, words=None, hl=None, **kw):
    """The Brave List inside Owen's closet door: seven rules in Mom's blue pen inside his crayon border. ink [7]: 1 blue ..
    0 faded pale (the crayon stays); words (n, k): rule n shows its first k words (float: the last fades in) while it is
    read; hl n: a soft highlight on rule n."""
    _ibg_b(pen, '#d8d2c4', '#a8a294', 110)
    for k in range(2): pen.line(rect(120 + k * 900, -60, 780, 1200), 6, '#b8b2a4')
    ink = list(ink) if ink is not None else [1.0] * 7
    x, y, w, h = 380, 22, 1160, 1036
    pen.cv.save(); pen.cv.translate(960, 540); pen.cv.rotate(-0.6); pen.cv.translate(-960, -540)
    _bt_paper(pen, x, y, w, h, 3)
    _bt_crayon_border(pen, x, y, w, h, 11)
    btext(pen, 'THE BRAVE LIST', x + w / 2, y + 122, 'kid', 66, '#e84a3a', 245, 'center')
    _crayon_line(pen, [(x + w / 2 - 240, y + 138), (x + w / 2 + 240, y + 134)], '#3a6ad8', 6.0, 220, 5)
    yy = y + 196
    for i, (n, text) in enumerate(BT_RULES):
        k = clamp(ink[i] if i < len(ink) else 1.0)
        c = mix(BT_PEN_PALE, BT_PEN, k)
        wd = None; last_a = 1.0
        if words is not None and words[0] == n:
            wd = words[1]; last_a = clamp(wd - math.floor(wd)) if wd != math.floor(wd) else 1.0
        lines = _rule_lines(n, text, 40, w - 210, wd)
        full = _rule_lines(n, text, 40, w - 210)
        bh = 44 * max(1, len(full)) + 14
        if hl == n: pen.fill(rrect(x + 90, yy - 44, w - 180, bh + 6, 16), '#fff2a0', 150)
        btext(pen, '%d.' % n, x + 108, yy, 'caveat_b', 44, c, 245)
        for j, l_ in enumerate(lines):
            a = 245
            if wd is not None and j == len(lines) - 1 and last_a < 1.0:
                head_ = ' '.join(l_.split(' ')[:-1]); tail = l_.split(' ')[-1]
                btext(pen, head_, x + 160, yy + j * 44, 'caveat', 40, c, 245)
                btext(pen, tail, x + 160 + btext_width(head_ + ' ', 'caveat', 40), yy + j * 44, 'caveat', 40, c, int(245 * last_a))
                continue
            btext(pen, l_, x + 160, yy + j * 44, 'caveat', 40, c, a)
        yy += bh
    btext(pen, 'Mom + Owen', x + 110, y + h - 84, 'caveat_b', 34, BT_PEN, 220)
    pen.cv.restore()


def _bti_rule(pen, t, n=1, write=1.0, ink=1.0, **kw):
    """One rule big on the closet door's list (n 1..7): write 0..1 = how many of its words are shown; ink 1 blue .. 0 pale."""
    _ibg_b(pen, '#d8d2c4', '#a8a294', 110)
    x, y, w, h = 90, 110, 1740, 860
    pen.cv.save(); pen.cv.translate(960, 540); pen.cv.rotate(-0.8); pen.cv.translate(-960, -540)
    _bt_paper(pen, x - 120, y - 200, w + 240, h + 400, 5)
    _bt_crayon_border(pen, x - 120, y - 200, w + 240, h + 400, 13)
    text = BT_RULES[n - 1][1]; ws = text.split(' ')
    kw_ = clamp(write) * len(ws)
    c = mix(BT_PEN_PALE, BT_PEN, clamp(ink))
    btext(pen, 'RULE %d' % n if False else '%d.' % n, x + 70, y + 170, 'caveat_b', 120, c, 245)
    lines = _wrap(text, 'caveat', 92, w - 330)
    shown = 0.0
    for j, l_ in enumerate(lines):
        xx = x + 250
        for wd in l_.split(' '):
            a = clamp(kw_ - shown)
            if a > 0: btext(pen, wd, xx, y + 170 + j * 112, 'caveat', 92, c, int(245 * a))
            xx += btext_width(wd + ' ', 'caveat', 92); shown += 1
    pen.cv.restore()


def _bti_board(pen, t, state='birthday', k=1.0, **kw):
    """The fridge whiteboard close (state 'birthday' | 'here' | 'all', k as bt_apt's board_k)."""
    _ibg_b(pen, '#e8eae8', '#c8cac8', 90)
    pen.fill(rect(1500, -100, 40, 1300), '#b8b8b8')                         # the door handle
    for (mx, my, c) in ((300, 180, '#e84a3a'), (260, 760, '#3a9ad8')):       # magnets, a drawing
        pen.fill(rect(mx - 70, my - 90, 140, 180), '#f8f0d8'); pen.line(rect(mx - 70, my - 90, 140, 180), 1.0)
        _crayon_line(pen, [(mx - 40, my + 50), (mx, my - 30), (mx + 40, my + 50)], c, 6.0, 220, mx)
        pen.fill(oval(mx, my - 92, 16), '#e8c040')
    W, H = 760, 990
    pen.fill(rect(580 + 12, 45 + 16, W, H), '#000000', 80, blur=18)
    pen.cv.save(); pen.cv.translate(580, 45)
    _bt_board_art(pen, W, H, state, k)
    pen.cv.restore()


def _bti_box(pen, t, state='closed', **kw):
    """The box on our doormat (Tuesday): Mom's name on the label; open: the red coat folded inside, the card on top."""
    pen.fill(rect(-500, -400, 2900, 1900), '#5a4a52'); pen.texture(rect(-500, -400, 2900, 1900), 'grunge', 0.4, 'overlay', 2.0)   # corridor carpet
    pen.fill(rect(-500, -400, 2900, 330), '#6a4a3a'); pen.fill(rect(-500, -80, 2900, 14), '#3a2a22')                          # the door's foot
    mat = rrect(380, 120, 1160, 900, 20)
    pen.fill(mat, '#6a5038'); pen.texture(mat, 'grunge', 0.6, 'overlay', 3.0)
    btext(pen, 'HOME', 960, 960, 'serif_b', 90, '#4a3424', 200, 'center', 0.3)
    bx, by, bw, bh = 560, 230, 800, 560
    pen.fill(rect(bx + 30, by + 40, bw, bh), '#000000', 110, blur=24)
    if state == 'closed':
        pen.fill(rect(bx, by, bw, bh), '#c8a070'); pen.texture(rect(bx, by, bw, bh), 'paper', 0.4, 'multiply', 1.0)
        pen.fill(rect(bx, by + bh / 2 - 34, bw, 68), '#d8c8a0', 200); pen.fill(rect(bx + bw / 2 - 34, by, 68, bh), '#d8c8a0', 200)
        lb = rect(bx + 70, by + 70, 300, 180)
        pen.fill(lb, '#fbfaf4'); pen.line(lb, 1.0)
        btext(pen, 'TO:', bx + 90, by + 115, 'sans_b', 26, '#1a1a1a', 240)
        btext(pen, 'NADIA', bx + 90, by + 160, 'sans_b', 40, '#1a1a1a', 250)
        btext(pen, 'APT 2B', bx + 90, by + 205, 'sans', 30, '#1a1a1a', 240)
        for k in range(18): pen.fill(rect(bx + 260 + k * 5, by + 190, 2 + (k % 3), 46), '#1a1a1a')
    else:
        pen.fill(rect(bx, by, bw, bh), '#7a5a3a')
        for (pts, c) in (([(bx, by), (bx + bw, by), (bx + bw - 80, by - 140), (bx + 80, by - 140)], '#c8a070'), ([(bx, by + bh), (bx + bw, by + bh), (bx + bw - 40, by + bh + 120), (bx + 40, by + bh + 120)], '#b89060'),
                         ([(bx, by), (bx, by + bh), (bx - 150, by + bh - 50), (bx - 150, by + 50)], '#b89060'), ([(bx + bw, by), (bx + bw, by + bh), (bx + bw + 150, by + bh - 50), (bx + bw + 150, by + 50)], '#c8a070')):
            pen.fill(poly(pts), c); pen.line(poly(pts), 1.0)
        pen.fill(rect(bx + 30, by + 30, bw - 60, bh - 60), '#e8e0d0')        # tissue
        coat = rrect(bx + 70, by + 70, bw - 140, bh - 130, 30)
        pen.fill(coat, BT_RED); pen.fill(rect(bx + 70, by + bh * 0.55, bw - 140, bh * 0.35), BT_RED_SH, 120)
        pen.line(smooth([(bx + 180, by + 90), (bx + 400, by + 160), (bx + 620, by + 90)], False), 8, BT_RED_SH)
        for j in range(7): _bt_button(pen, bx + 160 + j * 80, by + 330 + 12 * math.sin(j), 18)
        _bti_card_flat(pen, bx + bw / 2 + 60, by + 200, 0.5, -6)


def _bti_card_flat(pen, cx, cy, s, rot):
    pen.cv.save(); pen.cv.translate(cx, cy); pen.cv.rotate(rot); pen.cv.scale(s, s)
    pen.fill(rect(-420 + 14, -250 + 20, 840, 500), '#000000', 100, blur=18)
    pen.fill(rect(-420, -250, 840, 500), '#f8f4ea'); pen.texture(rect(-420, -250, 840, 500), 'paper', 0.35, 'multiply', 1.0)
    pen.line(rect(-390, -220, 780, 440), 2.0, '#c8b8a0')
    btext(pen, BT_CARD[0], 0, -30, 'cursive', 54, '#2a2a3a', 245, 'center')
    btext(pen, BT_CARD[1], 0, 80, 'cursive', 54, '#2a2a3a', 245, 'center')
    _bt_button(pen, 300, 170, 16)
    pen.cv.restore()


def _bti_card(pen, t, **kw):
    """The card in the box, close, in a too-neat hand: "Because she never even looked. Don't tell her." """
    pen.fill(rect(-500, -400, 2900, 1900), BT_RED); pen.texture(rect(-500, -400, 2900, 1900), 'grunge', 0.35, 'overlay', 2.0)
    pen.fill(rect(-500, 700, 2900, 900), BT_RED_SH, 150, blur=60)
    for j in range(3): _bt_button(pen, 1640, 200 + j * 320, 40)
    _bti_card_flat(pen, 900, 540, 1.6, -3)


def _bti_coat(pen, t, full=1.0, **kw):
    """The red coat in Owen's closet at 3 a.m.: buttoned to the top and FULL, as if somebody were inside it (full 1), then
    sagging, empty (full 0; f(t) to animate). The room's tablet glow from behind us."""
    pen.fill(rect(-500, -400, 2900, 1900), '#0e1018')
    pen.radial(None, 960, 600, 1100, [(0, '#3a4258', 200), (0.6, '#1a1e2a', 120), (1, '#000000', 0)])
    pen.fill(rect(-500, 120, 2900, 26), '#4a4a52')                          # the rod
    for (x, c) in ((340, '#3a5a8a'), (520, '#2a4a3a'), (1480, '#5a3a5a'), (1660, '#3a3a4a')):     # his hoodies, dark
        pen.line(smooth([(x - 90, 190), (x, 140), (x + 90, 190)], False), 6, '#6a6a70')
        pen.fill(rrect(x - 110, 180, 220, 640, 40), mix(c, '#000000', 0.45))
    fu = full(t) if callable(full) else full
    _bt_coat(pen, 960, 170, 820, fu, 7, 0.01 * math.sin(t * 1.3) * fu, True, dark=0.25)
    pen.fill(rect(-500, -400, 260, 1900), '#000000', 200, blur=40)           # the door edge
    pen.linear(rect(-500, -400, 2900, 1900), 0, 0, 1920, 0, [(0, '#a8c8ff', 30), (0.4, '#a8c8ff', 0)])


def _bti_jar(pen, t, state='full', bg='sill', **kw):
    """The button jar, close: state as _bt_jar_flat; bg 'sill' (the kitchen window at night, the streetlight beyond) |
    'sill_day' | 'desk' (the narrator's desk: by his headset)."""
    if bg == 'desk':
        pen.fill(rect(-500, -400, 2900, 1900), '#1a1c24'); pen.fill(rect(-500, 700, 2900, 1200), '#4a3424'); pen.texture(rect(-500, 700, 2900, 1200), 'wood', 0.35, 'overlay', 1.2, 0)
        pen.radial(None, 500, 300, 900, [(0, '#ffcf94', 120), (1, '#ffcf94', 0)])
        hx, hy = 1420, 820                                                  # the headset beside it
        pen.line(smooth([(hx - 220, hy), (hx - 200, hy - 210), (hx, hy - 290), (hx + 200, hy - 210), (hx + 220, hy)], False), 26, '#26282e')
        for sd in (-1, 1): pen.fill(oval(hx + sd * 220, hy - 10, 80, 60), '#33363e'); pen.line(oval(hx + sd * 220, hy - 10, 80, 60), 2.0)
        _bt_jar_flat(pen, 760, 900, 4200, state)
        return
    day = bg == 'sill_day'
    pen.fill(rect(-500, -400, 2900, 1900), '#0e1430' if not day else '#a8c0d8')
    if not day:
        pen.glow(1300, 260, 520, BT_SODIUM, 120); pen.glow(1300, 260, 60, '#fff4dc', 230)
        pen.fill(rect(1290, 300, 16, 700), '#3a3c44', 200)
    pen.fill(rect(-500, 880, 2900, 1000), '#e4dccc' if day else '#5a5650')  # the sill
    pen.fill(rect(-500, 860, 2900, 40), '#f0e8d8' if day else '#6a6660')
    pen.fill(rect(940, -400, 40, 1300), '#e8e2d4' if day else '#4a4844')    # the sash bar
    _bt_jar_flat(pen, 960, 930, 4600, state)
    if not day: pen.fill(rect(-500, -400, 2900, 1900), BT_SODIUM, 18)


def _bti_music_box(pen, t, crank=None, bg='cardigan', **kw):
    """Mom's birthday surprise: the tiny crank music box with their song punched into it (crank angle rad or f(t));
    bg 'cardigan' (it lies in the flat, empty cardigan on the kitchen floor) | 'table'."""
    if bg == 'cardigan':
        pen.fill(rect(-500, -400, 2900, 1900), '#b4ac9c')
        knit = rrect(160, 90, 1600, 1100, 120)
        pen.fill(knit, '#d9caa9'); pen.texture(knit, 'grunge', 0.4, 'overlay', 3.0)
        for k in range(40): pen.line(smooth([(180 + k * 40, 100), (200 + k * 40, 600), (180 + k * 40, 1150)], False), 3.0, '#ae9d7c', 120)
        pen.line(smooth([(960, 90), (950, 600), (970, 1180)], False), 6, '#ae9d7c')
        for j in range(5): pen.fill(oval(1000, 180 + j * 190, 20), '#9a7a56')                # the cardigan's own buttonholes / buttons
    else:
        pen.fill(rect(-500, -400, 2900, 1900), '#a8845a'); pen.texture(rect(-500, -400, 2900, 1900), 'wood', 0.4, 'overlay', 1.2, 0)
    a = crank(t) if callable(crank) else (crank if crank is not None else 0.6)
    cx, cy = 900, 600
    pen.fill(rect(cx - 330 + 20, cy - 160 + 30, 660, 380), '#000000', 110, blur=24)
    top = poly([(cx - 330, cy - 160), (cx + 330, cy - 160), (cx + 280, cy - 260), (cx - 280, cy - 260)])
    pen.fill(rect(cx - 330, cy - 160, 660, 380), '#b27c4a'); pen.line(rect(cx - 330, cy - 160, 660, 380), 2.0)
    pen.fill(top, '#c99462'); pen.line(top, 2.0)
    pen.texture(rect(cx - 330, cy - 260, 660, 480), 'wood', 0.35, 'overlay', 1.0, 0)
    pen.fill(smooth([(cx, cy + 90), (cx - 60, cy + 30), (cx - 40, cy - 20), (cx, cy + 5), (cx + 40, cy - 20), (cx + 60, cy + 30)]), '#8a5a32')   # the inlaid heart
    for k in range(7): pen.seg((cx - 250 + k * 80, cy - 245), (cx - 240 + k * 80, cy - 175), 3.0, '#8a5a32', 140)
    hx, hy = cx + 360, cy + 20
    ex, ey = hx + math.cos(a) * 120, hy + math.sin(a) * 120
    pen.seg((hx, hy), (ex, ey), 20, '#8a6a2a'); pen.seg((hx, hy), (ex, ey), 12, '#e2bd58')
    pen.fill(oval(hx, hy, 26), '#e2bd58'); pen.line(oval(hx, hy, 26), 2.0); pen.fill(rrect(ex - 18, ey - 50, 36, 70, 16), '#6a3a22')


def _bti_lock_screen(pen, t, **kw):
    """Mom's phone, face up on the table: her lock screen is Owen on Monday, pointing at Barlow's window (she did look)."""
    pen.fill(rect(-500, -400, 2900, 1900), '#7a5a3a'); pen.texture(rect(-500, -400, 2900, 1900), 'wood', 0.35, 'overlay', 1.2, 0)
    pen.cv.save(); pen.cv.translate(960, 540); pen.cv.rotate(-4)
    w, h = 560, 1120
    body = rrect(-w / 2, -h / 2, w, h, 60)
    pen.fill(moved(body, 18, 26), '#000000', 110, blur=26); pen.fill(body, '#121216'); pen.line(body, 3, '#3a3a40')
    sc = rrect(-w / 2 + 22, -h / 2 + 22, w - 44, h - 44, 44)
    pen.cv.save(); pen.cv.clipPath(sc, skia.ClipOp.kIntersect, True)
    X, Y, W_, H_ = -w / 2 + 22, -h / 2 + 22, w - 44, h - 44
    pen.fill(rect(X, Y, W_, H_), '#8a7060')                                 # the photo: Barlow's window, Owen pointing
    pen.fill(rect(X, Y + H_ * 0.72, W_, H_ * 0.3), '#9a9894')
    win = rect(X + 40, Y + H_ * 0.28, W_ - 60, H_ * 0.42)
    pen.fill(win, '#4a3a30'); pen.linear(win, 0, Y + H_ * 0.28, 0, Y + H_ * 0.7, [(0, '#8a7a6a'), (1, '#3a2a22')])
    pen.fill(rect(X + 20, Y + H_ * 0.2, W_ - 20, H_ * 0.07), '#1e3a2e'); btext(pen, "BARLOW'S", X + W_ * 0.55, Y + H_ * 0.25, 'serif_b', 40, '#f0dca0', 245, 'center')
    _bt_coat(pen, X + W_ * 0.62, Y + H_ * 0.36, 230, 1.0, 7, hanger=False)
    ox, oy = X + W_ * 0.28, Y + H_ * 0.62                                   # Owen from behind: green coat open, brown hair, pointing
    pen.fill(rrect(ox - 70, oy, 140, 260, 40), '#4a7a4a'); pen.fill(rrect(ox - 40, oy + 240, 34, 130, 10), '#2a3a5a'); pen.fill(rrect(ox + 8, oy + 240, 34, 130, 10), '#2a3a5a')
    pen.line(smooth([(ox + 50, oy + 40), (ox + 140, oy - 20), (ox + 200, oy - 60)], False), 34, '#4a7a4a')
    pen.fill(oval(ox + 210, oy - 66, 20), '#e4b896')
    pen.fill(oval(ox, oy - 50, 62, 66), '#6a4228'); pen.line(smooth([(ox - 10, oy - 112), (ox + 10, oy - 130), (ox + 22, oy - 110)], False), 8, '#6a4228')
    pen.fill(rect(X, Y, W_, H_ * 0.3), '#000000', 60)
    btext(pen, '12:07', 0, Y + 200, 'sans_b', 150, '#ffffff', 250, 'center')
    btext(pen, 'Friday', 0, Y + 110, 'sans', 40, '#ffffff', 235, 'center')
    pen.cv.restore()
    pen.fill(rrect(-70, -h / 2 + 32, 140, 28, 14), '#000000')
    pen.cv.restore()


def _bti_glasses(pen, t, circles=0.0, glare=1.0, **kw):
    """Mom's reading glasses with the laptop's glare: two bright screens hide her eyes; circles 0..1 turns the glare into
    two black, shiny circles (for one second the real mom has button eyes). Nothing near the eyes: only the lenses."""
    pen.fill(rect(-500, -400, 2900, 1900), '#e9c3a0'); pen.radial(None, 960, 700, 1300, [(0, '#f2cfae', 255), (1, '#b88a66', 255)])
    rng = np.random.default_rng(4)
    for i in range(70): pen.fill(oval(rng.uniform(200, 1720), rng.uniform(560, 1000), rng.uniform(4, 9)), '#b5774f', 150)
    for sd in (-1, 1):                                                      # the brows, warm brown
        pen.line(smooth([(960 + sd * 140, 230), (960 + sd * 380, 180), (960 + sd * 620, 230)], False), 34, '#7a4e2e')
    pen.fill(smooth([(900, 520), (960, 380), (1020, 520), (1010, 900), (910, 900)]), '#e0b48e', 120)                   # the nose bridge
    ck = clamp(circles(t) if callable(circles) else circles)
    for sd in (-1, 1):
        cx = 960 + sd * 420
        lens = rrect(cx - 330, 300, 660, 430, 150)
        pen.fill(lens, '#0e1420')
        pen.fill(lens, BT_LAPTOP, int(235 * glare * (1 - ck)))
        pen.cv.save(); pen.cv.clipPath(lens, skia.ClipOp.kIntersect, True)
        for k in range(5): pen.fill(rect(cx - 220, 380 + k * 60, 380 - (k % 2) * 120, 18), '#ffffff', int(140 * glare * (1 - ck)))
        pen.fill(lens, '#ffffff', int(40 * glare * (1 - ck)), blur=30)
        if ck > 0.01:
            pen.fill(oval(cx, 515, 175), '#0a0a0e', int(255 * ck)); pen.fill(oval(cx - 60, 455, 46, 30), '#ffffff', int(220 * ck))
        pen.cv.restore()
        pen.line(lens, 22, '#5a3a24'); pen.line(lens, 8, '#8a5a34')
    pen.line(smooth([(960 - 90, 450), (960, 410), (960 + 90, 450)], False), 18, '#5a3a24')
    for sd in (-1, 1): pen.line(smooth([(960 + sd * 750, 400), (960 + sd * 1100, 380)], False), 18, '#5a3a24')


def _bti_clock(pen, t, clock='11:58', blink=True, **kw):
    """The oven clock close: green digits ('11:58' -> '12:00'; clock may be f(t))."""
    pen.fill(rect(-500, -400, 2900, 1900), '#d8d4cc'); pen.fill(rect(-500, 760, 2900, 1200), '#1a1a1c')
    for k in (0, 1, 5, 6): pen.fill(oval(320 + k * 230, 340, 70), '#2a2a2e'); pen.line(oval(320 + k * 230, 340, 70), 3)
    s_ = clock(t) if callable(clock) else clock
    pan = rrect(560, 420, 800, 300, 20)
    pen.fill(pan, '#060806'); pen.line(pan, 3, '#3a3a3e')
    pen.glow(960, 570, 340, '#5af08a', 50)
    if blink and int(t * 2) % 2 and ':' in s_: s_ = s_.replace(':', ' ')
    btext(pen, s_, 960, 650, 'vhs', 240, '#6aff9a', 250, 'center')
    btext(pen, 'CLOCK', 1300, 700, 'sans_b', 22, '#3a7a4a', 220, 'right')


def _bti_laptop(pen, t, state='line', typed=1.0, **kw):
    """Mom's laptop screen: 'line' (the help line: a caller on line 3, I'm listening) | 'delivered' (the order page:
    Delivered, left on the mat) | 'msg' (2 a.m.: Mom's account typing to Owen; typed 0..1 or f(t))."""
    pen.fill(rect(-500, -400, 2900, 1900), '#0e1220')
    sc = rrect(80, 40, 1760, 1000, 14)
    pen.fill(sc, '#e4e7ee')
    pen.fill(rect(80, 40, 1760, 70), '#2a3a5a')
    if state == 'line':
        btext(pen, 'HelpLine  -  Agent console', 120, 88, 'sans_b', 30, '#ffffff', 245)
        pen.fill(rrect(140, 170, 760, 380, 20), '#e4ecf8'); btext(pen, 'LINE 3  -  ON CALL', 180, 240, 'sans_b', 44, '#2a5a9a', 250)
        btext(pen, '00:14:52', 180, 320, 'mono', 60, '#1a1a22', 250)
        btext(pen, '"Thank you for calling. I\'m listening."', 180, 470, 'serif_i', 36, '#3a3a44', 240)
        for k in range(5): pen.fill(rrect(980, 180 + k * 110, 780, 86, 14), '#eef0f4'); btext(pen, 'Caller waiting  %d:%02d' % (k + 1, 12 + k * 7), 1010, 236 + k * 110, 'sans', 32, '#5a5e68', 240)
    elif state == 'delivered':
        btext(pen, 'Your orders', 120, 88, 'sans_b', 30, '#ffffff', 245)
        pen.fill(rrect(140, 170, 1640, 760, 20), '#ffffff'); pen.line(rrect(140, 170, 1640, 760, 20), 2, '#d8dae0')
        pen.fill(oval(230, 290, 40), '#3aa85a'); pen.line(smooth([(210, 290), (226, 306), (254, 274)], False), 10, '#ffffff')
        btext(pen, 'Delivered', 300, 310, 'sans_b', 64, '#1a1a22', 250)
        btext(pen, 'Tuesday 3:12 PM  -  Left on the mat', 300, 380, 'sans', 40, '#5a5e68', 245)
        btext(pen, 'Order #4471  -  1 item  -  for: Nadia', 300, 470, 'sans', 36, '#2a2c34', 240)
        pr = rect(1240, 230, 460, 340); pen.fill(pr, '#5a4a52'); pen.fill(rect(1330, 300, 280, 200), '#c8a070'); pen.fill(rect(1330, 390, 280, 22), '#d8c8a0')
        btext(pen, 'Photo at delivery', 1470, 610, 'sans', 26, '#7a7e88', 230, 'center')
    else:
        btext(pen, 'Messages', 120, 88, 'sans_b', 30, '#ffffff', 245)
        btext(pen, 'To: Owen', 160, 190, 'sans_b', 44, '#1a1a22', 250)
        msg = 'Come to the kitchen, baby.'
        k = typed(t) if callable(typed) else typed
        shown = msg[:int(round(len(msg) * clamp(k)))]
        pen.fill(rrect(140, 820, 1640, 150, 75), '#ffffff'); pen.line(rrect(140, 820, 1640, 150, 75), 3, '#b0b4c0')
        btext(pen, shown, 210, 918, 'sans', 72, '#1a1a22', 250)
        if int(t * 2.2) % 2 == 0: pen.fill(rect(218 + btext_width(shown, 'sans', 72), 850, 5, 84), '#3a7ae8')
        pen.fill(rect(80, 110, 1760, 930), '#000000', 40)
    pen.fill(minus(rect(-500, -400, 2900, 1900), sc), '#16181e')
    pen.linear(rect(80, 40, 1760, 1000), 80, 40, 1840, 1040, [(0, '#ffffff', 0), (0.4, '#ffffff', 14), (0.45, '#ffffff', 0)])


def _bti_photo(pen, t, send=0.0, **kw):
    """The photo out of his window, in the tablet's camera (Send button; send 0..1 or f(t) presses it)."""
    pen.fill(rect(-500, -400, 2900, 1900), '#0a0a0c')
    bt_view_photo(pen, 60, 40, 1800, 1000)
    k = send(t) if callable(send) else send
    b = rrect(1500, 900, 300, 110, 55)
    pen.fill(b, mix('#3a7ae8', '#1a4ab8', clamp(k)))
    btext(pen, 'Send', 1650, 972, 'sans_b', 48, '#ffffff', 250, 'center')


BT_INSERTS = {
    'brave_list': (_bti_list, 'bt_ins', 'the Brave List inside the closet door: 7 rules in blue pen, crayon border (ink [7] 1 blue .. 0 pale; words (n, k); hl n)'),
    'brave_rule': (_bti_rule, 'bt_ins', 'one rule big (n 1..7; write 0..1 words shown; ink 1 blue .. 0 pale)'),
    'board': (_bti_board, 'bt_screen', "the fridge board: state 'birthday' | 'here' (k 0..1) | 'all' (k 0..6 items)"),
    'box': (_bti_box, 'bt_ins', "the box on our doormat, Mom's name on the label (state 'closed' | 'open': the red coat, the card)"),
    'card': (_bti_card, 'bt_ins', 'the card: "Because she never even looked. Don\'t tell her."'),
    'coat': (_bti_coat, 'bt_ins_night', 'the red coat in the closet at 3 a.m.: full 1 (buttoned, somebody inside) .. 0 sagged empty (f(t))'),
    'jar': (_bti_jar, 'bt_ins_night', "the button jar: state 'full' | 'open' | 'black' | 'empty' | 'empty_on'; bg 'sill' | 'sill_day' | 'desk'"),
    'music_box': (_bti_music_box, 'bt_ins', "the tiny crank music box (crank rad or f(t); bg 'cardigan' | 'table')"),
    'lock_screen': (_bti_lock_screen, 'bt_ins', "Mom's lock screen: Owen on Monday pointing at Barlow's window"),
    'glasses': (_bti_glasses, 'bt_ins', "Mom's glasses with the laptop glare (circles 0..1: two black shiny circles)"),
    'clock': (_bti_clock, 'bt_ins_night', "the oven clock (clock '11:58' / '12:00' or f(t))"),
    'laptop': (_bti_laptop, 'bt_screen', "Mom's laptop screen: 'line' | 'delivered' | 'msg' (typed 0..1)"),
    'photo': (_bti_photo, 'bt_screen', 'the photo out of his window in the tablet camera (send 0..1)'),
}


def bt_insert(name, prop_kw=None, motion=None, t0=0.0, grade=None):
    """A close-up insert from BT_INSERTS (flat 1920 x 1080 design space with margin for a drift): prop_kw dict (values
    may be f(t)) or f(t) -> dict; motion f(t) -> (dx, dy, dscale, drot)."""
    fn, gr, note = BT_INSERTS[name]
    static = not callable(prop_kw) and motion is None and not any(callable(v_) for v_ in (prop_kw or {}).values()) and name not in ('clock', 'coat', 'laptop', 'music_box')

    def draw(pen, t):
        kw = prop_kw(t) if callable(prop_kw) else dict(prop_kw or {})
        kw = {k_: (v_(t) if callable(v_) and k_ not in ('full', 'crank', 'clock', 'typed', 'send') else v_) for k_, v_ in kw.items()}
        cv = pen.cv
        if motion is not None:
            dx, dy, ds, dr = motion(t)
            cv.save(); cv.translate(960 + dx, 540 + dy); cv.rotate(dr); cv.scale(1 + ds, 1 + ds); cv.translate(-960, -540)
        fn(pen, t - t0, **kw)
        if motion is not None: cv.restore()
    key = 'btins:%s:%s' % (name, _okey(prop_kw or {}) if isinstance(prop_kw, dict) else 'f')
    lay = Layer(1.0, draw, 'insert', cache=key if static else False, bounds=(-460, -320, 2380, 1400), blur=0)
    return BSet('bt_ins_' + name, [lay], {}, {}, lens=None, grade=grade or gr, focus=1.0, dof=0.0, cover=(-460, -320, 2380, 1400), info={'note': note})


# ====================================================================================================== the registry
BT_SETS = {'bt_apt': bt_apt, 'bt_owen': bt_owen, 'bt_street': bt_street, 'bt_lobby': bt_lobby, 'bt_school': bt_school, 'bt_now': bt_now,
           'bt_chat': bt_chat, 'bt_insert': bt_insert}
BT_API = {nm: sorted({k[len(pre):] for k in BT_CAMS if k.startswith(pre)}) for nm, pre in (
    ('bt_apt', 'bt_apt_'), ('bt_owen', 'bt_owen_'), ('bt_street', 'bt_ext_'), ('bt_lobby', 'bt_lobby_'), ('bt_school', 'bt_sch_'), ('bt_now', 'bt_now_'))}
BT_API['bt_insert'] = sorted(BT_INSERTS)
BT_API['bt_chat'] = sorted(BT_CHAT)
__all__ += ['bt_apt', 'bt_owen', 'bt_street', 'bt_lobby', 'bt_school', 'bt_now', 'bt_chat', 'bt_insert', 'bt_mirror', 'bt_micro_quad', 'bt_sweep', 'bt_snowfall',
            'bt_avatar', 'bt_view_photo', 'bt_jar', 'BT_API', 'BT_INSERTS', 'BT_RULES', 'BT_CHAT', 'BT_CARD', 'BT_CAMS', 'BT_UP', 'BT_MX']
