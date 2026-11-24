"""characters_buttons.py: the cast of "If Your Mom's Eyes Turn Into Buttons... DON'T KEEP HER SECRET" and its staging.

Not imported on its own: characters.py runs it in its own namespace at the end of the module (exec, after
characters_walls.py), so everything here is part of `characters` (import characters as CH). Owen, Mom (Nadia), forms 1
and 2 of the Blank, Mr. Dunn, Officer Mensah, the son and the grown narrator are v3 cast entries (outfits, proportions,
props) on the existing people rig; form 3 of the Blank is a thin long-limbed figure drawn here on the same head, hand
and cloth language (see _b3_geom). See BUTTONS_API below and CAST.md.
"""
# NOTE: runs inside characters.py's globals (math, np, skia, Ctx, HeadMap, Body, CAST, Pose, Acting, _figure3 ... exist).

BUTTONS_API = """
Buttons film cast ids (this film takes the plain names; the older films' ones live on as 'mom_walls', 'owen_dummy'):
  'owen' (11, blue hoodie) / 'owen_coat' (the green coat, broken zip, hanging open) / 'owen_pj'
  'mom'  Nadia: open oatmeal cardigan (pens in the pockets) on a teal tee, messy warm-brown bun with a pencil, freckles,
         reading glasses (laptop glare hides her green eyes), headset, slippers
  'blank1' form 1: Mom's exact look, cardigan buttoned to the throat, reading glasses on (button eyes behind them);
         'blank1_shades' the same in sunglasses (the car)
  'blank2' form 2: Mom made too neat (glossy bun, smooth grey-tinged skin, shiny black buttons to the throat), flat
         black four-hole button eyes with a white glint, never blinks, a smile a little too big
  'blank3' form 3: ceiling height, very thin (custom figure: see _b3_geom); 'blank3' in draw_bust = her face
  'dunn' crossing guard (late 60s, hi-vis vest, stop sign, radio)   'mensah' Officer Mensah (40s, uniform, notepad)
  'son' (10)   'narrator_b' the grown narrator (hands only: draw_arm)
Pose fields: faded 0..1 (Owen's fade: rubbed out: cool, translucent, still clearly read), refl_hide 0..1 (with
  draw(..., reflection=True): gone from the microwave door), pgrey 0..1 (pencil grey), glare / circles 0..1 (Mom's
  lenses), specs 0/1 (glasses on), hs_off 0/1 (headset off), shades / shades_dn 0..1 (sunglasses on / lowered),
  default_head 0/1 (one-frame grey default head), crank (music box), b3_* (form 3, set by the methods below).
Heights: height_px(who, ppm, tall=0.0); blank2 grows with BLANK_TALL[scene] ('r1' 0 ... 'sill' 0.12).
"""

# ====================================================================================================== keep old ids
_BTN_OLD = {}
for _o, _n in (('mom', 'mom_walls'), ('owen', 'owen_dummy'), ('son', 'son_old')):
    if _o in CAST:
        _BTN_OLD[_o] = CAST[_o]
        if _n not in CAST: CAST[_n] = CAST[_o]

POSE_DEFAULTS.update(faded=0.0, refl_hide=0.0, pgrey=0.0, glare=0.0, circles=0.0, hs_off=0.0, shades=0.0, shades_dn=0.0,
                     default_head=0.0, crank=0.0, b3_unfold=1.0, b3_collapse=0.0, b3_face=1.0, b3_lean=0.0, b3_look=0.0,
                     b3_tap=0.0, b3_lx=0.0, b3_ly=0.0, b3_lw=0.0, b3_rx=0.0, b3_ry=0.0, b3_rw=0.0)
BLANK_TALL = {'r1': 0.0, 'r3': 0.03, 'r4': 0.05, 'r4_micro': 0.07, 'r5': 0.10, 'sill': 0.12}
_BTN_BLACK = '#121216'


def _button_disc(c, x, y, rx, ry=None, det=2, col=_BTN_BLACK, glint=True, holes=True):
    """A shiny four-hole button, flat on whatever it sits on: a dark disc, a raised rim, a dished centre, four holes, a
    white glint (top left: the room light, never the camera)."""
    ry = rx if ry is None else ry
    d = oval(x, y, rx, ry)
    c.fill(d, col)
    c.radial(d, x - rx * 0.3, y - ry * 0.35, max(rx, ry) * 1.25, [(0, mix(col, '#ffffff', 0.32), 255), (0.55, col, 0),
                                                                    (1, mix(col, '#000000', 0.5), 200)])
    if det >= 1:
        c.line(oval(x, y, rx * 0.72, ry * 0.72), c.lw * 0.45, mix(col, '#ffffff', 0.25), 200)
        if holes:
            hs = [oval(x + sx * rx * 0.24, y + sy * ry * 0.24, rx * 0.11, ry * 0.11) for sx in (-1, 1) for sy in (-1, 1)]
            c.fill(_multi(hs), mix(col, '#ffffff', 0.38), 230)
    if glint:
        c.line(smooth([(x - rx * 0.62, y - ry * 0.05), (x - rx * 0.5, y - ry * 0.5), (x - rx * 0.08, y - ry * 0.68)], False),
               max(c.lw * 0.7, rx * 0.12), '#ffffff', 215)
        c.fill(oval(x + rx * 0.38, y - ry * 0.42, rx * 0.11, ry * 0.11), '#ffffff', 235)
    c.line(d, c.lw * 0.6)


# ====================================================================================================== outfits
_BTN_CARDI = ('cardi_open', 'cardi_throat')
_DOC_ROWS.update({'cardi_open': (18, 0.88, 3, 5, 6, 6, 6, 6), 'cardi_throat': (16, 0.88, 2, 4, 4, 4, 4, 4),
                  'hivis': (24, 0.92, 8, 12, 12, 12, 12, 10), 'parka': (28, 0.93, 10, 12, 12, 14, 14, 12)})
_SLEEVES3.update({'cardi_open': 'long', 'cardi_throat': 'long', 'hivis': 'long', 'parka': 'long'})


def _cardi_hem(c, sp, B, rows, det):
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    if det < 1: return
    rb = []
    for k in range(-7, 8):
        pts, v = _surf_poly(B, rows, [(k * 15, B.y_hip - 40), (k * 15, B.y_hip - 18)], dz=1)
        if v > 0.1: rb.append(poly(pts, False))
    if rb: c.line(_multi(rb), lw * 0.3, cl['top_sh'], 170)
    hem, v = _surf_poly(B, rows, [(-b['hip'] - 6, B.y_hip - 40), (b['hip'] + 6, B.y_hip - 40)], dz=1)
    if v > -0.2: c.line(poly(hem, False), lw * 0.4, LINE, 190)


def _cardi_pockets(c, sp, B, rows, P, det, pens=False):
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    for sd in (-1, 1):
        x0_, x1_ = sd * 22, sd * (b['hip'] * 0.8)
        yt, yb = B.y_hip - 96, B.y_hip - 46
        if pens and sd == 1 and det >= 1:                    # two pens in her left pocket: a blue ballpoint and a pencil
            for (xp, col_, top_) in ((0.45, '#2f4f9a', 30), (0.62, '#e2b23a', 24)):
                X0, Y0, v0, s0 = B.surf(sd * (b['hip'] * xp), yt + 4, 5, False, rows)
                if v0 < 0.1: continue
                pn = rrect(X0 - 3.6 * s0, Y0 - top_ * s0, 7.2 * s0, (top_ + 6) * s0, 2.5 * s0)
                c.shape(pn, col_, lw * 0.5)
                if col_ == '#2f4f9a': c.fill(rect(X0 + 1.2 * s0, Y0 - top_ * s0, 1.8 * s0, 15 * s0), '#c9ccd3')
                else: c.fill(rrect(X0 - 3.6 * s0, Y0 - top_ * s0, 7.2 * s0, 5 * s0, 2 * s0), '#e48a9a')
        pk, v = _surf_poly(B, rows, [(x0_, yt), (x1_, yt), (x1_ * 0.98, yb), (x0_, yb)], dz=3)
        if v > 0.08:
            pp = smooth(pk, True, 0.25)
            c.fill(pp, mix(cl['top'], cl['top_sh'], 0.22)); c.line(pp, lw * 0.5, LINE, 200)
            band, _ = _surf_poly(B, rows, [(x0_, yt + 9), (x1_, yt + 9)], dz=3)
            c.line(poly(band, False), lw * 0.45, cl['top_sh'], 200)


def _front_cardi_open(c, sp, B, rows, P, det, t):
    """Mom's oatmeal cardigan worn OPEN on a teal tee: the tee in a wide opening, ribbed front bands, plain buttons on
    one band and buttonholes on the other (never done up), patch pockets with her pens, a ribbed hem."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC, yH = B.y_sh, B.y_ch, B.y_hip
    edge = [(b['neck'] + 4, yS - 30), (b['neck'] * 0.5 + 22, yC - 10), (b['wa'] * 0.36, B.y_wa), (b['hip'] * 0.42, yH - 16)]
    pts = [(-x, y) for (x, y) in edge] + [(x, y) for (x, y) in edge[::-1]]
    panel, v = _surf_poly(B, rows, pts, dz=2)
    if v > 0.0:
        q = smooth(panel, True, 0.15)
        c.fill(q, cl['tee']); c.fill(_crescent(q, -7, 0), cl['tee_sh'], 130)
        nk, v2 = _surf_poly(B, rows, [(-b['neck'] - 2, yS - 30), (0, yS - 8), (b['neck'] + 2, yS - 30)], dz=3)
        if v2 > 0: c.line(smooth(nk, False), lw * 0.7, cl['tee_sh'])
    for sd in (-1, 1):
        ed, v = _surf_poly(B, rows, [(sd * x, y) for (x, y) in edge], dz=3)
        if v > -0.2:
            pe = smooth(ed, False)
            c.line(pe, lw * 3.6, LINE); c.line(pe, lw * 2.4, cl['rib'])
        if det >= 1:
            for k in range(5):
                yy = yC - 4 + k * (yH - 52 - yC) / 4.0
                xx = float(np.interp(yy, [e[1] for e in edge], [e[0] for e in edge])) + 4
                X, Y, vv, s_ = B.surf(sd * xx, yy, 6, False, rows)
                if vv < 0.12: continue
                if sd < 0: c.shape(oval(X, Y, 4.6 * s_), cl['button'], lw * 0.4)
                else: c.line(poly([(X - 4 * s_, Y), (X + 4 * s_, Y)], False), lw * 0.5, cl['top_sh'])
    _cardi_pockets(c, sp, B, rows, P, det, pens=True)
    _cardi_hem(c, sp, B, rows, det)


def _front_cardi_throat(c, sp, B, rows, P, det, t):
    """The Blank's version: the same cardigan buttoned all the way to the throat (a high ribbed neckband, a placket and a
    row of buttons from the throat to the hem; shiny black four-hole buttons on form 2), empty pockets."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yH = B.y_sh, B.y_hip
    nb, v = _surf_poly(B, rows, [(-b['neck'] - 8, yS - 34), (0, yS - 24), (b['neck'] + 8, yS - 34), (b['neck'] + 12, yS - 20),
                                 (0, yS - 8), (-b['neck'] - 12, yS - 20)], dz=4)
    if v > 0.0:
        q = smooth(nb, True, 0.4); c.fill(q, cl['rib']); c.line(q, lw * 0.6)
    for sd in (-1, 1):
        pl, v = _surf_poly(B, rows, [(sd * 7, yS - 12), (sd * 7, yH - 18)], dz=3)
        if v > -0.2: c.line(poly(pl, False), lw * 0.5, cl['top_sh'], 220)
    n = 7
    for k in range(n):
        yy = yS - 16 + k * (yH - 40 - (yS - 16)) / (n - 1)
        X, Y, vv, s_ = B.surf(0, yy, 6, False, rows)
        if vv < 0.12: continue
        if cl.get('btn_shiny'): _button_disc(c, X, Y, 6.4 * s_ * max(0.45, abs(B.ct)), 6.4 * s_, det, cl['button'])
        else: c.shape(oval(X, Y, 4.8 * s_ * max(0.45, abs(B.ct)), 4.8 * s_), cl['button'], lw * 0.4)
    _cardi_pockets(c, sp, B, rows, P, det, pens=False)
    _cardi_hem(c, sp, B, rows, det)


def _front_hivis(c, sp, B, rows, P, det, t):
    """Mr. Dunn: a fluorescent yellow-green safety vest over a navy jacket: the jacket's zip and collar in the V, two
    silver reflective bands round the body and two up over the shoulders."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC, yH = B.y_sh, B.y_ch, B.y_hip
    vv_, v = _surf_poly(B, rows, [(-b['neck'] - 14, yS - 30), (b['neck'] + 14, yS - 30), (16, yC + 30), (-16, yC + 30)], dz=2)
    if v > 0:
        q = smooth(vv_, True, 0.2); c.fill(q, cl['jacket']); c.line(q, lw * 0.6)
        zp, _ = _surf_poly(B, rows, [(0, yS - 26), (0, yC + 28)], dz=3)
        c.line(poly(zp, False), lw * 0.6, '#8d96a8')
        for sd in (-1, 1):
            col_, _ = _surf_poly(B, rows, [(sd * 2, yS - 30), (sd * (b['neck'] + 10), yS - 36), (sd * (b['neck'] + 20), yS - 18),
                                           (sd * 8, yS - 14)], dz=5)
            cp = smooth(col_, True, 0.6); c.fill(cp, cl['jacket']); c.line(cp, lw * 0.5)
    bands = []
    for y_ in (yC + 52, yC + 122):
        bd, v = _surf_poly(B, rows, [(-b['wa'] - 20, y_), (-b['wa'] * 0.3, y_ + 1), (b['wa'] * 0.3, y_ + 1), (b['wa'] + 20, y_)], dz=2)
        if v > -0.1: bands.append(poly(bd, False))
    for sd in (-1, 1):
        bd, v = _surf_poly(B, rows, [(sd * (b['neck'] + 24), yS - 28), (sd * (b['neck'] + 22), yC), (sd * (b['neck'] + 18), yC + 52)], dz=2)
        if v > -0.1: bands.append(poly(bd, False))
    if bands:
        m_ = _multi(bands)
        c.line(m_, lw * 4.6, '#7d838c'); c.line(m_, lw * 3.4, cl['stripe'])
        if det >= 1: c.line(m_, lw * 0.8, '#ffffff', 150)


def _front_parka(c, sp, B, rows, P, det, t):
    """Owen's green coat hanging open (the broken zip): the jacket front, zip teeth down both edges, the pull dangling
    from one side at the hem."""
    _front_jacket3(c, sp, B, rows, P, det, t)
    if det < 1: return
    for sd in (-1, 1):
        ed, v = _surf_poly(B, rows, [(sd * 38, B.y_sh - 26), (sd * 41, B.y_hip - 14)], dz=4)
        if v < 0.05: continue
        (x0, y0), (x1, y1) = ed[0], ed[-1]
        tk = []
        for k in range(16):
            u = (k + 0.5) / 16.0
            x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
            tk.append(poly([(x - 3.5 * sd, y), (x + 1.5 * sd, y)], False))
        c.line(_multi(tk), c.lw * 0.45, '#2a2f2a', 220)
        if sd > 0:
            pull = rrect(x1 - 3, y1 - 2, 7, 15, 2.5); c.shape(pull, '#a9adb3', c.lw * 0.45)


_FRONTS3.update({'cardi_open': _front_cardi_open, 'cardi_throat': _front_cardi_throat, 'hivis': _front_hivis,
                 'parka': _front_parka})
_limb_cols3_btn_prev = _limb_cols3


def _limb_cols3(sp):
    if sp.get('outfit') == 'hivis':
        cl = sp['cloth']
        return cl['jacket'], cl['jacket_sh'], cl['trousers'], cl['trousers_sh'], cl.get('shoes', '#222')
    return _limb_cols3_btn_prev(sp)


# ====================================================================================================== the cast
_KID_BODY = dict(sh=90, ch=90, wa=84, hip=84, arm=(37, 31), leg=(41, 34), neck=30, hand=0.82, arm_k=0.9)
# Owen, 11: warm-brown hair like his mom's (a messy cowlick), brown eyes (the narrator's are brown), small, honest.
_OWEN = dict(hair='cowlick', sex='m', hh=208.0, child=True, m=1.45, head_ws=[0, 55, 80, 95, 100, 100, 94, 81, 60, 32, 0],
             eye_dx=41, eye_y=3, eye_r=21.0, iris_c='#5a3a24', iris_k=0.72, lid_rest=0.14, pupil=1.08, brow_th=7.5,
             nose_len=15, mouth_y=62, mouth_w=16, nose='button', ears=1.1, skin='#ecc4a4', skin_sh='#c29478',
             skin_dp='#80584a', blush='#e8a090', lip='#bd7c72', lips=0.05, hair_c='#6b4128', brow_c='#4e2e1c', bags=0.3,
             age=0.0, blink_rate=0.3, lashes=0.3, part=1, fades=True, body=dict(_KID_BODY))
_OWEN_CL = dict(top='#5d7fb0', top_sh='#3f5c88', top_hi='#84a2cc', hood='#5d7fb0', hood_sh='#3f5c88', string='#e8e4da',
                trousers='#3b4254', trousers_sh='#262b38', shoes='#d6d0c4', shoes_sh='#9a948a', socks='#e8e4dc', socks_sh='#b8b4aa')
CAST['owen'] = _v3cast(outfit='hoodie3', feet='shoes', **_OWEN, cloth=dict(_OWEN_CL))
CAST['owen_coat'] = _v3cast(outfit='parka', feet='shoes', **_OWEN,
                            cloth=dict(_OWEN_CL, top='#4d7a4a', top_sh='#335532', top_hi='#6f9c68', collar='#3a5a38',
                                       shirt='#5d7fb0', shirt_sh='#3f5c88', button='#5d7fb0'))
CAST['owen_pj'] = _v3cast(outfit='tee_w', feet='socks', **_OWEN,
                          cloth=dict(_OWEN_CL, top='#8fa6bf', top_sh='#667d96', top_hi='#b0c3d6', trim='#6a7f98',
                                     trousers='#46597a', trousers_sh='#2f3d56'))
# The son, 10 (now): darker straight hair, brown eyes, a teal pyjama tee; a little flat, then warm.
CAST['son'] = _v3cast(outfit='tee_w', feet='socks', hair='side_short', sex='m', hh=212.0, child=True, m=1.40,
                      head_ws=[0, 56, 81, 96, 101, 100, 93, 79, 58, 31, 0], eye_dx=41, eye_y=3, eye_r=20.5, iris_c='#4a3020',
                      iris_k=0.72, lid_rest=0.18, pupil=1.05, brow_th=7.0, nose_len=15, mouth_y=63, mouth_w=16, nose='button',
                      ears=1.05, skin='#d9a682', skin_sh='#ad7a5c', skin_dp='#6e4636', blush='#d88a76', lip='#a8685c',
                      hair_c='#2a1d16', brow_c='#22170f', bags=0.15, blink_rate=0.3, lashes=0.4, part=-1, body=dict(_KID_BODY),
                      cloth=dict(top='#3f8a86', top_sh='#2a6460', top_hi='#62aaa4', trim='#e8e2d2', trousers='#34405c',
                                 trousers_sh='#222a3e', socks='#e2ddd2', socks_sh='#b2ada2'))
# Nadia ("Mom"), late 30s: warm, tired, loving. Messy warm-brown bun with a pencil through it, freckles, green eyes
# (hidden by glare), an open oatmeal cardigan with pens in the pockets over a teal tee, reading glasses, headset, slippers.
_NADIA = dict(hair='gran_bun', bun='messy', pencil=True, sex='f', hh=182.0, m=1.65, head_ws=[0, 49, 71, 87, 92, 90, 82, 66, 46, 24, 0],
              eye_dx=40, eye_y=-6, eye_r=18.5, iris_c='#5f8c4c', lid_rest=0.26, brow_th=7.0, nose_len=21, mouth_w=20,
              skin='#e9c09e', skin_sh='#bd9176', skin_dp='#7c5648', blush='#e49e8e', lip='#b87472', lips=0.45,
              hair_c='#7c4c2e', brow_c='#5a3622', bags=0.55, age=0.35, lashes=0.9, part=0, glasses=True, specs='reading',
              freckles=1.0, headset=True, btn=True, body=dict(sh=100, ch=100, wa=86, hip=102, arm=(40, 32), leg=(45, 37), neck=32, hand=0.96))
_OAT = dict(top='#d9caa9', top_sh='#ae9d7c', top_hi='#eee2c8', rib='#cbb994', button='#9a7a56', tee='#4f8c88',
            tee_sh='#33645f', trousers='#5a5560', trousers_sh='#3b3842', shoes='#c99a9c', shoes_sh='#94686c',
            socks='#e8e2d8', socks_sh='#b8b2a8')
CAST['mom'] = _v3cast(outfit='cardi_open', feet='slippers', **_NADIA, cloth=dict(_OAT))
# Form 1: Mom exactly, the cardigan buttoned to the throat (her own tan buttons), glasses over button eyes, no headset.
CAST['blank1'] = dict(CAST['mom'], outfit='cardi_throat', headset=False, button_eyes=True, blink_rate=0.0, blank=True)
CAST['blank1_shades'] = dict(CAST['blank1'], shades=True)
# Form 2: Mom made too neat: glossy perfect bun, smooth grey-tinged skin (no freckles, no tired bags), shiny black buttons
# to the throat, button eyes, never blinks, the smile a little too big, very still.
CAST['blank2'] = dict(CAST['blank1'], bun='neat', freckles=0.0, glasses=False, skin='#dfc8b8', skin_sh='#b09c90',
                      skin_dp='#6e625e', blush='#d2aaa2', lip='#a87878', lips=0.55, hair_c='#6e452c', bags=0.0, age=0.1,
                      mouth_w=28, micro=0.25, breath=0.4, lock=0.6,
                      cloth=dict(_OAT, button=_BTN_BLACK, btn_shiny=True, top='#dccfb2', top_hi='#f2e8d2'))
# Form 3 (drawn by _draw_blank3; this entry is her head and the Acting bookkeeping): paler, a far too wide smile.
CAST['blank3'] = dict(CAST['blank2'], blank3=True, m=2.45, mouth_w=31, skin='#d9cbc2', skin_sh='#a89c96', skin_dp='#686060',
                      blush='#c8aaa6', head_ws=[0, 46, 68, 84, 88, 86, 80, 66, 47, 25, 0])
# Mr. Dunn, late 60s, crossing guard: white hair and moustache, kind weathered face, navy jacket under a hi-vis vest.
CAST['dunn'] = _v3cast(outfit='hivis', feet='shoes', hair='thin', sex='m', hh=176.0, m=1.74,
                       head_ws=[0, 51, 75, 91, 97, 96, 89, 75, 54, 29, 0], eye_dx=41, eye_y=-6, eye_r=17.0, iris_c='#5d7488',
                       lid_rest=0.3, brow_th=9.0, nose_len=26, mouth_w=21, skin='#dba98a', skin_sh='#ae7d66', skin_dp='#6c4a40',
                       blush='#d88a7e', lip='#a26c62', moustache='#e6e2da', hair_c='#e4e0d8', brow_c='#cfcac0', bags=0.7,
                       age=1.0, ring=1, body=dict(sh=118, ch=116, wa=110, hip=106, arm=(48, 40), leg=(52, 43), neck=42, hand=1.05),
                       cloth=dict(top='#cfe33a', top_sh='#9fb328', top_hi='#e4f27a', stripe='#d9dde3', jacket='#27344e',
                                  jacket_sh='#18213a', trousers='#2c3342', trousers_sh='#1b202b', shoes='#2a2420', shoes_sh='#171310'))
# Officer Mensah, 40s: calm, professional; close-cropped hair, a neat beard line; uniform, a notepad and pencil.
CAST['mensah'] = _v3cast(outfit='police', hat=None, hair='side_short', sex='m', hh=176.0, m=1.83,
                         head_ws=[0, 52, 76, 93, 99, 98, 91, 76, 55, 30, 0], eye_dx=42, eye_y=-7, eye_r=17.5, iris_c='#2e1d14',
                         lid_rest=0.24, brow_th=10.0, nose_len=24, mouth_w=22, skin='#8a5a3e', skin_sh='#673f2a', skin_dp='#3e2418',
                         blush='#a0604c', lip='#6e3e32', stubble='#1e1410', stub=0.55, hair_c='#1a1210', brow_c='#140e0a',
                         bags=0.35, age=0.45, body=dict(sh=126, ch=120, wa=104, hip=106, arm=(50, 42), leg=(58, 47), neck=44, hand=1.04),
                         cloth=dict(_POLICE))
# The grown narrator (the sting): hands and sleeves only (a charcoal hoodie, a wedding ring).
CAST['narrator_b'] = _v3cast(outfit='hoodie3', feet='socks', hair='side_short', sex='m', hh=176.0, m=1.80,
                             skin='#e2b898', skin_sh='#b68a70', skin_dp='#74503f', blush='#d8947e', lip='#a8705e', hair_c='#5e3b24', brow_c='#4a2c1a',
                             iris_c='#5a3a24', ring=1, body=dict(sh=124, ch=118, wa=104, hip=104, arm=(50, 41), leg=(56, 46), neck=44, hand=1.04),
                             cloth=dict(top='#3c4048', top_sh='#262a30', top_hi='#565b64', hood='#3c4048', hood_sh='#262a30',
                                        string='#cfc9bb', trousers='#2e3442', trousers_sh='#1d2230'))
BUTTONS_CAST = ('owen', 'owen_coat', 'owen_pj', 'mom', 'blank1', 'blank1_shades', 'blank2', 'blank3', 'dunn', 'mensah', 'son',
                'narrator_b')
_BTN_NEW = {k: CAST[k] for k in ('mom', 'owen', 'son')}
EXPR.update({
    'puzzled': dict(brow_in=0.35, brow_up=0.25, brow_asym=0.55, m_side=0.45, smile=-0.12, squint=0.18),
    'too_sweet': dict(smile=1.0, teeth=0.7, grin=0.3, brow_up=0.35, lock=1.0),
    'too_wide': dict(smile=1.0, grin=0.75, teeth=0.85, brow_up=0.5, m_open=0.06, lock=1.0),
    'quiet_sure': dict(smile=0.08, m_press=0.3, brow_sad=0.25, brow_up=0.12, pupil=1.05),
    'listening_soft': dict(brow_sad=0.6, brow_up=0.35, smile=0.12, wide=0.12),
    'busy': dict(brow_in=0.2, brow_angry=0.08, m_press=0.25, eye_open=0.9, h_nod=0.12),
})


def height_px(who, px_per_m, tall=0.0, _prev=height_px):
    """Feet-to-crown px at px_per_m; tall > 0 = the Blank's growth (BLANK_TALL[scene]); 'blank3' = floor to ceiling."""
    return _prev(who, px_per_m) * (1.0 + tall)


# ====================================================================================================== faces
_eye_btn_prev = _eye


def _eye(c, hm, sp, P, side, det, t, skin, sh):
    """Button eyes (the Blank): a flat shiny black four-hole button where the eye is, a white glint; never blinks."""
    if not sp.get('button_eyes'): return _eye_btn_prev(c, hm, sp, P, side, det, t, skin, sh)
    ex0 = side * sp['eye_dx']; ey0 = sp['eye_y']
    X, Y, V = hm.map1(ex0, ey0, 2.0)
    if V < 0.12: return None
    fs = hm.sx(ex0, ey0)
    r = sp['eye_r'] * 1.16
    c.fill(oval(X, Y + 2, r * 1.1 * fs, r * 1.08), sh, 70)          # the faint socket shadow it sits in
    _button_disc(c, X, Y, r * fs, r, det)
    return (X, Y, r, fs, X, Y, 1.0)


_glasses_btn_prev = _glasses


def _glasses(c, hm, sp, P, det, eyes, t):
    """Mom's reading glasses (thin tortoiseshell ovals; laptop glare hides her eyes unless pose.glare < 0 ... see below),
    the 'two black circles' state (pose.circles), and the Blank's sunglasses (sp shades / pose.shades, pose.shades_dn
    slides them down the nose: buttons above the frame)."""
    if not sp.get('specs'): return _glasses_btn_prev(c, hm, sp, P, det, eyes, t)
    shades = sp.get('shades') or P.__dict__.get('shades', 0.0) > 0.5
    dn = clamp(P.__dict__.get('shades_dn', 0.0)) if shades else 0.0
    circ = clamp(P.__dict__.get('circles', 0.0))
    glare = 0.0 if sp.get('button_eyes') else clamp(1.0 - P.__dict__.get('glare', 0.0))   # glare=1 turns it OFF
    fr = '#1d1c20' if shades else '#6b4428'
    pts_c = []
    for side in (-1, 1):
        ex0 = side * sp['eye_dx']; ey0 = sp['eye_y'] + 2 + 34.0 * ease_in_out(dn)
        X, Y, V = hm.map1(ex0, ey0, 18.0)
        if V < 0.05: continue
        fs = hm.sx(ex0, ey0, 18.0)
        rx, ry = (33 if shades else 30) * fs, (25 if shades else 26) * (1.0 - 0.25 * dn)
        lens = oval(X, Y, rx, ry)
        if shades:
            c.fill(lens, '#15161b', 248)
            with c.clip(lens):
                c.fill(poly([(X - rx, Y - ry * 0.2), (X - rx * 0.2, Y - ry), (X + rx * 0.1, Y - ry), (X - rx, Y + ry * 0.3)]), '#8a92a8', 90)
        else:
            c.fill(lens, '#dfe9f4', 40)
            if glare > 0.01:                                # the laptop's glare: a cool white sheen that hides the eye
                c.grad(lens, X - rx, Y - ry, X + rx, Y + ry, [(0, '#f4f8ff', 236 * glare), (0.55, '#d6e4f6', 214 * glare),
                                                              (1, '#b8cbe6', 190 * glare)])
                with c.clip(lens):
                    for k, w_ in ((-0.5, 0.18), (0.15, 0.1)):
                        c.fill(poly([(X + rx * (k - 0.1), Y + ry), (X + rx * (k + w_ + 0.1), Y + ry), (X + rx * (k + w_ + 0.6), Y - ry),
                                     (X + rx * (k + 0.4), Y - ry)]), '#ffffff', 150 * glare)
            if circ > 0.01:                                 # the glasses catch the laptop: two black, shiny circles
                c.fill(lens, _BTN_BLACK, 250 * circ)
                c.radial(lens, X - rx * 0.3, Y - ry * 0.35, max(rx, ry) * 1.2, [(0, '#5a5e6a', 230 * circ), (0.6, _BTN_BLACK, 0)])
                c.fill(oval(X - rx * 0.35, Y - ry * 0.4, rx * 0.16, ry * 0.16), '#ffffff', 240 * circ)
        c.line(lens, c.lw * (0.95 if shades else 0.7), fr)
        pts_c.append((side, X, Y, rx))
    if len(pts_c) == 2:
        (s0, x0, y0, r0), (s1, x1, y1, r1) = sorted(pts_c, key=lambda p: p[1])
        c.line(smooth([(x0 + r0, y0 - 6), ((x0 + x1) / 2, y0 - 12), (x1 - r1, y1 - 6)], False), c.lw * 0.7, fr)
    for side, X, Y, rx in pts_c:
        ear_x, ear_y, ev = hm.map1(side * float(hm.W(0)), -2, -6)
        if ev > -0.6 and abs(ear_x - X) > rx:
            c.line(poly([(X + (rx if ear_x > X else -rx), Y - 8), (ear_x, ear_y - 4)], False), c.lw * 0.6, fr)


_nose_btn_prev = _nose


def _nose(c, hm, sp, P, det, skin, sh):
    fk = sp.get('freckles', 0.0)
    if fk and det >= 1:                                       # freckles over the nose and cheeks
        dots = []
        for k in range(26):
            sd = -1 if k % 2 else 1
            x0 = sd * (8 + 62 * hash01(k, 301)); y0 = 14 + 26 * hash01(k, 302) - 0.08 * abs(x0)
            X, Y, V = hm.map1(x0, y0, 1.0)
            if V < 0.2: continue
            r_ = (1.7 + 1.3 * hash01(k, 303)) * hm.sx(x0, y0)
            dots.append(oval(X, Y, r_, r_ * 0.9))
        if dots: c.fill(_multi(dots), mix(sp['skin_dp'], skin, 0.3), 120 * fk)
    return _nose_btn_prev(c, hm, sp, P, det, skin, sh)


_gran_bun_btn_prev = _gran_bun
_BTN_CUR = {'P': None}


def _gran_bun(c, hm, sp, det, behind):
    """Mom's messy warm-brown bun high at the back of the head with a pencil through it (loops and loose ends); the
    Blank's form 2 / 3 bun is glossy and perfect (one clean spiral, a hard highlight), the pencil dead straight."""
    st = sp.get('bun')
    if not st: return _gran_bun_btn_prev(c, hm, sp, det, behind)
    X, Y, V = _sph(hm, np.array([PI * 0.86]), np.array([-108.0]), 30.0)
    X, Y, V = float(X[0]), float(Y[0]), float(V[0])
    if (V < 0.25) != behind: return
    hc = sp['hair_c']; hsh = mix(hc, '#000000', 0.32); hhi = mix(hc, '#ffffff', 0.38)
    neat = st == 'neat'
    r = 36.0 if neat else 40.0
    by = Y - 8
    if sp.get('pencil') and not neat:
        a = math.radians(-22.0 if hm.st >= 0 else 202.0)
        dx, dy = math.cos(a), math.sin(a)
        p0, p1 = (X - dx * 66, by - dy * 66), (X + dx * 60, by + dy * 60)
        c.line(poly([p0, p1], False), 13.0, LINE); c.line(poly([p0, p1], False), 9.0, '#e8b432')
        c.fill(oval(p0[0], p0[1], 6.0, 6.0), '#e48a9a'); c.line(oval(p0[0], p0[1], 6.0, 6.0), c.lw * 0.5)
        tip = poly([(p1[0] - dy * 5, p1[1] + dx * 5), (p1[0] + dx * 14, p1[1] + dy * 14), (p1[0] + dy * 5, p1[1] - dx * 5)])
        c.shape(tip, '#e9cf9e', c.lw * 0.5)
        c.fill(oval(p1[0] + dx * 12, p1[1] + dy * 12, 2.4, 2.4), '#2a2a2a')
    bun = oval(X, by, r * (0.78 + 0.22 * abs(hm.st)), r * 0.9) if neat else \
        smooth([(X + r * math.cos(k * PI / 5) * (1 + 0.12 * math.sin(k * 2.3)), by + r * 0.88 * math.sin(k * PI / 5) * (1 + 0.1 * math.cos(k * 1.7)))
                for k in range(10)], True, 0.9)
    c.fill(bun, hc)
    c.radial(bun, X - 10, by - 18, r * 1.3, [(0, hhi, 200 if neat else 140), (0.55, hc, 0), (1, hsh, 220)])
    if neat:
        c.fill(oval(X - r * 0.3, by - r * 0.42, r * 0.34, r * 0.12), '#ffffff', 120)
        if det >= 1: c.line(smooth([(X - r * 0.55, by + r * 0.1), (X - r * 0.1, by - r * 0.5), (X + r * 0.5, by - r * 0.1),
                                    (X + r * 0.1, by + r * 0.45), (X - r * 0.2, by + r * 0.05)], False), c.lw * 0.4, hsh, 190)
    elif det >= 1:
        c.line(_multi([smooth([(X - r * 0.8, by + 4 + k * 9), (X - r * 0.1, by - r * 0.6 + k * 12), (X + r * 0.75, by - 6 + k * 10)], False)
                       for k in range(3)]), c.lw * 0.4, hsh, 180)
        c.line(_multi([smooth([(X + r * 0.6, by - r * 0.5), (X + r * 1.05, by - r * 0.85), (X + r * 1.2, by - r * 0.45)], False),
                       smooth([(X - r * 0.7, by - r * 0.4), (X - r * 1.0, by - r * 0.95), (X - r * 0.75, by - r * 1.1)], False)]),
               c.lw * 0.9, hc)
    c.line(bun, c.lw)


_hair3_back_btn_prev = _hair3_back


def _hair3_back(c, hm, sp, P, det, t):
    if sp.get('btn') and P.__dict__.get('default_head', 0.0) > 0.5: return
    return _hair3_back_btn_prev(c, hm, sp, P, det, t)


def _default_head(c, sp, P, yaw, det):
    """The chat app's grey default head (form 0): a flat UI-grey circle head, no face. One frame of it on a fast turn."""
    h = oval(4.0 * math.sin(yaw), -4, 90, 106)
    c.fill(h, '#9ca2aa'); c.fill(oval(-26 + 10 * math.sin(yaw), -50, 34, 22), '#b9bec5', 150); c.line(h, c.lw)
    return HeadMap(sp, yaw, 0.0)


def _headset(c, hm, sp, P, det):
    """Mom's call headset: a band over the crown, padded ear cups, the mic boom curving to her mouth."""
    ys = np.linspace(-4.0, -118.0, 9)
    band = []
    for side in (-1, 1):
        X, Y, V = _sph(hm, np.full(9, side * PI * 0.5), ys, 9.0)
        band.append(list(zip(X.tolist(), Y.tolist())))
    pts = band[0] + band[1][::-1]
    bp = smooth(pts, False, 0.8)
    c.line(bp, c.lw * 2.7, LINE); c.line(bp, c.lw * 1.5, '#3a3d46')
    if det >= 1: c.line(bp, c.lw * 0.6, '#6a6f7c', 200)
    for side in (-1, 1):
        X, Y, V = _sph(hm, np.array([side * PI * 0.5]), np.array([-2.0]), 10.0)
        X, Y, V = float(X[0]), float(Y[0]), float(V[0])
        cup = oval(X, Y, 15 + 9 * max(0.0, V), 22)
        c.shape(cup, '#2b2d34', c.lw * 0.8); c.fill(oval(X, Y, 7 + 5 * max(0.0, V), 12), '#4b4f5a')
        if side == 1 and V > -0.55:
            mx, my, mv = hm.map1(sp['mouth_w'] + 16, sp['mouth_y'] - 4, 12.0)
            cx_, cy_, _ = hm.map1(sp['mouth_w'] + 52, sp['mouth_y'] - 34, 8.0)
            boom = smooth([(X, Y + 10), (cx_ * 0.6 + X * 0.4, cy_), (mx, my)], False, 0.8)
            c.line(boom, c.lw * 2.0, LINE); c.line(boom, c.lw * 1.1, '#2b2d34')
            c.shape(oval(mx, my, 7.5, 6.5), '#1f2026', c.lw * 0.5)


_dhl_btn_prev = draw_head_local


def draw_head_local(c, who, P, yaw, pitch, det, t, light=None, sp=None):
    sp = sp or CAST[who]
    if not sp.get('btn'): return _dhl_btn_prev(c, who, P, yaw, pitch, det, t, light, sp)
    if P.__dict__.get('default_head', 0.0) > 0.5: return _default_head(c, sp, P, yaw, det)
    hm = _dhl_btn_prev(c, who, P, yaw, pitch, det, t, light, sp)
    if sp.get('headset') and P.__dict__.get('hs_off', 0.0) < 0.5 and hm is not None:
        _headset(c, hm, sp, P, det)
    return hm


# ====================================================================================================== fade / grey / growth
def _btn_matrix(fade, grey):
    """Colour matrix: fade = Owen rubbed out (desaturated, cooled, lifted); grey = pencil grey (graphite, a little light)."""
    s = 1.0 - 0.55 * fade - 0.97 * grey
    lr, lg, lb = 0.2126, 0.7152, 0.0722
    m = [lr * (1 - s) + s, lg * (1 - s), lb * (1 - s), 0, 0,
         lr * (1 - s), lg * (1 - s) + s, lb * (1 - s), 0, 0,
         lr * (1 - s), lg * (1 - s), lb * (1 - s) + s, 0, 0,
         0, 0, 0, 1, 0]
    tint = (0.84, 0.93, 1.06)
    k = 0.85 * grey + 0.0
    for r_ in range(3):
        g = 1.0 + (tint[r_] - 1.0) * fade
        g *= 1.0 - 0.12 * grey
        for j in range(3): m[r_ * 5 + j] *= g
        m[r_ * 5 + 4] = (0.05 + 0.04 * r_) * fade + 0.10 * k
    return m


def _btn_layer(pen, P, sp, refl):
    f = clamp(P.__dict__.get('faded', 0.0)) if sp.get('fades') else 0.0
    g = clamp(P.__dict__.get('pgrey', 0.0))
    hide = clamp(P.__dict__.get('refl_hide', 0.0)) if refl else 0.0
    if f < 0.005 and g < 0.005 and hide < 0.005: return None
    paint = skia.Paint(ColorFilter=skia.ColorFilters.Matrix(_btn_matrix(f, g)), Alphaf=(1.0 - 0.42 * f) * (1.0 - hide))
    pen.cv.saveLayer(None, paint)
    return True


_draw_btn_prev = draw


def draw(pen, who, *a, **k):
    """draw() with the Buttons film's looks: pose.faded (Owen), pose.pgrey, reflection=True (+ pose.refl_hide), and form 3."""
    refl = k.pop('reflection', False)
    sp = CAST.get(who, {})
    if not sp.get('btn') and not sp.get('fades'): return _draw_btn_prev(pen, who, *a, **k)
    names = ('x', 'y_feet', 'height', 'pose', 'detail', 'light', 't', 'aim')
    kw = dict(zip(names, a)); kw.update(k)
    P = _as_pose(kw.get('pose'))
    if refl and P.__dict__.get('refl_hide', 0.0) > 0.995 and sp.get('fades'): return None
    lay = _btn_layer(pen, P, sp, refl)
    try:
        if sp.get('blank3'):
            return _draw_blank3(pen, kw['x'], kw['y_feet'], kw['height'], P, P.t if kw.get('t') is None else kw['t'],
                                kw.get('light'), kw.get('detail'))
        return _draw_btn_prev(pen, who, *a, **k)
    finally:
        if lay: pen.cv.restore()


_draw_bust_btn_prev = draw_bust


def draw_bust(pen, who, cx, cy, scale=1.0, pose=None, detail=None, light=None, t=None):
    sp = CAST.get(who, {})
    lay = _btn_layer(pen, _as_pose(pose), sp, False) if (sp.get('btn') or sp.get('fades')) else None
    try:
        return _draw_bust_btn_prev(pen, who, cx, cy, scale, pose, detail, light, t)
    finally:
        if lay: pen.cv.restore()


# ====================================================================================================== form 3 + long arms
_B3_SLEEVE, _B3_SLEEVE_SH = '#dccfb2', '#ab9e80'


def _button_hand(c, x, y, ang, s, det, t, skin, sh, tap=0.0, spread=0.5, seed=0):
    """A long thin hand (ang 0 = fingers pointing down +y, degrees), four long fingers and a thumb, each ending in a flat
    round button disc (no points, no claws). tap > 0: the fingers tap the air one after another."""
    hc = c.sub(x, y, ang, s)
    palm = smooth([(-13, 0), (13, 0), (15, 22), (11, 34), (-11, 34), (-15, 22)], True, 0.8)
    segs = []
    for j, (fx, fa) in enumerate(((-10.5, -15), (-3.5, -5), (3.5, 5), (10.5, 15))):
        a_ = math.radians(fa * (0.4 + spread) + 9.0 * tap * max(0.0, math.sin(t * 7.0 - j * 0.9 + seed)))
        L = 74 - abs(j - 1.5) * 7
        bend = 0.18 + 0.25 * tap * max(0.0, math.sin(t * 7.0 - j * 0.9 + seed))
        p0 = (fx, 31.0)
        p1 = (fx + math.sin(a_) * L * 0.5, 31 + math.cos(a_) * L * 0.5)
        p2 = (p1[0] + math.sin(a_ - bend) * L * 0.5, p1[1] + math.cos(a_ - bend) * L * 0.5)
        segs.append((p0, p1, p2))
    th = ((13.0, 10.0), (26.0, 30.0), (30.0, 52.0))
    segs.append(th)
    for sg in segs: c_ = hc.line(smooth(list(sg), False), 9.6 + hc.lw * 2.0, LINE)
    hc.fill(palm, skin); hc.line(palm, hc.lw)
    for sg in segs: hc.line(smooth(list(sg), False), 7.4, skin)
    hc.fill(palm, skin)
    if det >= 1:
        hc.line(_multi([smooth(list(sg), False) for sg in segs]), 2.6, sh, 70)
    for sg in segs:
        ex, ey = sg[-1]
        _button_disc(hc, ex, ey + 2, 7.2, 6.4, det, _BTN_BLACK)
    return hc


def _chain(root, tip, L, n, sign, t=0.0, wob=0.0):
    """Points of an n-segment chain of total length L from root toward tip, bending alternately (sign = side of the
    first bend): if L reaches past the tip the bends deepen so the end lands on it; otherwise it points along the line."""
    dx, dy = tip[0] - root[0], tip[1] - root[1]
    D = math.hypot(dx, dy) or 1e-6
    ux, uy = dx / D, dy / D
    nx, ny = -uy, ux
    if L <= D * 1.001:
        Dd, h = L, L * 0.06
    else:
        Dd = D
        lo, hi = 0.0, L
        for _ in range(28):
            h = (lo + hi) * 0.5
            offs = [0.0] + [h * (1 if k % 2 == 0 else -1) for k in range(n - 1)] + [0.0]
            ln = sum(math.hypot(Dd / n, offs[k + 1] - offs[k]) for k in range(n))
            lo, hi = (h, hi) if ln < L else (lo, h)
    offs = [0.0] + [h * (1 if k % 2 == 0 else -1) * sign * (1.0 + wob * math.sin(t * 0.9 + k)) for k in range(n - 1)] + [0.0]
    return [(root[0] + ux * Dd * k / n + nx * offs[k], root[1] + uy * Dd * k / n + ny * offs[k]) for k in range(n + 1)]


def _draw_limb(c, pts, w_sleeve, w_skin, sleeve_k, skin, sh, cuff=True):
    """A long arm along a chain of points: the cardigan sleeve for the first sleeve_k of its length (a ribbed cuff), then
    thin grey-pale skin; rounded joints (no points)."""
    Ls = [math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1]) for k in range(len(pts) - 1)]
    tot = sum(Ls) or 1.0
    cut = tot * sleeve_k; acc = 0.0; sl = [pts[0]]; sk = []
    for k, L in enumerate(Ls):
        if acc + L <= cut: sl.append(pts[k + 1])
        else:
            u = (cut - acc) / L if acc < cut else 0.0
            m = (pts[k][0] + (pts[k + 1][0] - pts[k][0]) * u, pts[k][1] + (pts[k + 1][1] - pts[k][1]) * u)
            if acc < cut: sl.append(m)
            sk = [m] + pts[k + 1:] if not sk else sk
            break
        acc += L
    if not sk: sk = [sl[-1], sl[-1]]
    sk_p = poly(sk, False); sl_p = poly(sl, False)
    c.line(sk_p, w_skin + c.lw * 2.0, LINE); c.line(sk_p, w_skin, skin)
    c.line(sk_p, w_skin * 0.35, sh, 90)
    c.line(sl_p, w_sleeve + c.lw * 2.0, LINE); c.line(sl_p, w_sleeve, _B3_SLEEVE)
    c.line(sl_p, w_sleeve * 0.4, _B3_SLEEVE_SH, 110)
    if cuff and len(sl) >= 2:
        (x0, y0), (x1, y1) = sl[-2], sl[-1]
        a = math.degrees(math.atan2(y1 - y0, x1 - x0))
        cc = c.sub(x1, y1, a, 1.0)
        r_ = rrect(-w_sleeve * 0.45, -w_sleeve * 0.62, w_sleeve * 0.5, w_sleeve * 1.24, w_sleeve * 0.2)
        cc.shape(r_, '#cbbd9a', c.lw * 0.8)
    return sk[-1], math.degrees(math.atan2(sk[-1][1] - sk[-2][1], sk[-1][0] - sk[-2][0])) if len(sk) > 1 else 90.0


def draw_long_arm(pen, root, target, ext, t, px_per_cm, light=None, n=4, sign=1, max_cm=260.0, tap=1.0, detail=2, stop_cm=3.0):
    """The car-window arm (R3): from root (the open window) toward target, ext 0..1 of its full length max_cm: it comes
    out, keeps coming, bends where arms don't bend (n segments, alternating), fingers tapping the air; ext back to 0
    folds it in. The fingertips never get closer than stop_cm to the target (kid-safe: it reaches, never touches).
    Returns the fingertips' point."""
    s = px_per_cm
    L = max(1.0, ext * max_cm * s)
    dx_, dy_ = target[0] - root[0], target[1] - root[1]; d_ = math.hypot(dx_, dy_) or 1.0
    back = (16.5 + stop_cm) * s
    target = (target[0] - dx_ / d_ * back, target[1] - dy_ / d_ * back)
    pts = _chain(root, target, L, n, sign, t, wob=0.08)
    c = Ctx(pen, skia.Matrix(), _lw_for(s * 22.0))
    sp = CAST['blank3']
    end, ang = _draw_limb(c, pts, 8.5 * s, 5.6 * s, 0.32, sp['skin'], sp['skin_sh'])
    hc = _button_hand(c, end[0], end[1], ang - 90.0, 0.16 * s, detail, t, sp['skin'], sp['skin_sh'], tap=tap)
    a = math.radians(ang)
    return end[0] + math.cos(a) * 16.5 * s, end[1] + math.sin(a) * 16.5 * s


def _b3_geom(x, y, H, P, t):
    """Form 3's skeleton in design px (feet at (x, y), ceiling at y - H): legs with backward knees, the long cardigan
    tube, the neck rising and bending along the ceiling, the head under it, long arms with backward elbows toward the
    pose's hand targets (b3_lx/ly/lw, b3_rx/ry/rw). b3_unfold 0..1 straightens it joint by joint."""
    u = H / 1000.0
    f = 1.0 if P.__dict__.get('b3_face', 1.0) >= 0 else -1.0
    un = clamp(P.__dict__.get('b3_unfold', 1.0))
    uL = ease_in_out(prog(un, 0.0, 0.42)); uT = ease_in_out(prog(un, 0.18, 0.68)); uN = ease_in_out(prog(un, 0.5, 1.0))
    sway = math.sin(t * 0.55) * 4.0 * u
    kb = math.radians(158.0 - 146.0 * uL)
    leg = 262.0 * u
    hh = 2 * leg * math.cos(kb / 2)
    kx = -f * leg * math.sin(kb / 2)
    hip = (x + sway * 0.3, y - hh)
    feet = [(x - f * 16 * u, y), (x + f * 20 * u, y)]
    knees = [((fx + hip[0]) / 2 + kx, y - hh / 2) for fx, _ in feet]
    lean = P.__dict__.get('b3_lean', 0.0)
    at = math.radians(f * (40.0 * (1 - uT) + 6.0 * lean) + sway * 0.05)    # folded: bent over the crouched legs
    T = 335.0 * u
    sh = (hip[0] + math.sin(at) * T, hip[1] - math.cos(at) * T)
    hem = (hip[0] - math.sin(at) * 70 * u, hip[1] + math.cos(at) * 70 * u)
    head_h = 0.142 * H
    ceil = y - H
    yb = ceil + 14 * u + 42 * u
    vert = max(0.0, sh[1] - yb)
    Lfull = max(0.0, (y - 0.83 * H) - yb) + PI / 2 * 42 * u + 150 * u
    Ln = 28 * u + (Lfull - 28 * u) * uN
    neck = [sh]
    look = P.__dict__.get('b3_look', 0.0)
    if Ln <= vert:
        end = (sh[0], sh[1] - Ln); neck.append(end)
        kbend = 0.0
    else:
        neck.append((sh[0], yb))
        rest = Ln - vert
        arc = min(rest, PI / 2 * 42 * u)
        cxa, cya = sh[0] + f * 42 * u, yb
        for k in range(1, 5):
            a_ = arc / (42 * u) * k / 4
            neck.append((cxa - f * 42 * u * math.cos(a_), cya - 42 * u * math.sin(a_)))
        run = max(0.0, rest - arc)
        end = (neck[-1][0] + f * run, neck[-1][1]) if run > 0 else neck[-1]
        if run > 0: neck.append(end)
        kbend = clamp((rest) / (110 * u))
    if kbend <= 0:
        hc = (end[0] + f * 6 * u, end[1] - head_h * 0.42); hrot = f * 8.0
    else:
        up = (end[0] + f * 6 * u, end[1] - head_h * 0.42)
        dn = (end[0] + f * head_h * 0.34, ceil + head_h * 0.5 + 2 * u)
        hc = (up[0] + (dn[0] - up[0]) * kbend, up[1] + (dn[1] - up[1]) * kbend); hrot = f * 8.0 - f * 30.0 * kbend
    hc = (hc[0] + look * 10 * u, hc[1])
    arms = {}
    for side in (1, -1):                                       # +1 near arm (in front), -1 far
        S = (sh[0] - f * side * 5 * u, sh[1] + (10 - 4 * side) * u)
        rest_t = (S[0] + f * (40 + 24 * side) * u, min(y - 14 * u, S[1] + 440 * u * (0.55 + 0.45 * uT)))
        pre = 'b3_l' if side > 0 else 'b3_r'
        w = clamp(P.__dict__.get(pre + 'w', 0.0))
        A = B_ = 252.0 * u
        TL = _B3_TIP * u
        def ik(tg):
            dx, dy = tg[0] - S[0], tg[1] - S[1]
            D = min(math.hypot(dx, dy), (A + B_) * 0.999) or 1e-6
            a0 = math.atan2(dy, dx)
            al = math.acos(clamp((A * A + D * D - B_ * B_) / (2 * A * D), -1.0, 1.0))
            ea = a0 - al * f * side_k                         # elbows bend the WRONG way (forward / up)
            return (S[0] + math.cos(ea) * A, S[1] + math.sin(ea) * A), (S[0] + math.cos(a0) * D, S[1] + math.sin(a0) * D)
        side_k = 1.0
        if w > 0.001:                                          # the target is the FINGERTIPS: solve the wrist behind them
            tx, ty = P.__dict__.get(pre + 'x', 0.0) / max(w, 1e-3), P.__dict__.get(pre + 'y', 0.0) / max(w, 1e-3)
            E, W = ik((tx, ty))
            for _ in range(3):
                d_ = math.hypot(W[0] - E[0], W[1] - E[1]) or 1.0
                E, W = ik((tx - (W[0] - E[0]) / d_ * TL, ty - (W[1] - E[1]) / d_ * TL))
            tgt = (rest_t[0] + (W[0] - rest_t[0]) * w, rest_t[1] + (W[1] - rest_t[1]) * w)
        else:
            tgt = rest_t
        E, W = ik(tgt)
        arms[side] = (S, E, W)
    return dict(u=u, f=f, feet=feet, knees=knees, hip=hip, hem=hem, sh=sh, neck=neck, head=hc, hrot=hrot, head_h=head_h,
                arms=arms, ceil=ceil, kbend=kbend)


_B3_TIP = 112.0                                              # wrist to fingertip (body units)


def b3_point(actor, t, part='head'):
    """Design point of a form 3 part at t: head, mouth, eyes, hand_l / hand_r (wrists), tips_l / tips_r (fingertips),
    shoulder, hip, foot."""
    P = actor.at(t)
    G = _b3_geom(actor.x0 + P.dx, actor.y0, actor.height, P, t)
    if part in ('head', 'eyes', 'mouth'):
        hx, hy = G['head']
        return hx, hy + {'head': 0.0, 'eyes': -0.03, 'mouth': 0.25}[part] * G['head_h']
    if part in ('hand_l', 'hand_r', 'tips_l', 'tips_r'):
        S, E, W = G['arms'][1 if part.endswith('_l') else -1]
        if part.startswith('hand'): return W
        a = math.atan2(W[1] - E[1], W[0] - E[0])
        return W[0] + math.cos(a) * _B3_TIP * G['u'], W[1] + math.sin(a) * _B3_TIP * G['u']
    return {'shoulder': G['sh'], 'hip': G['hip'], 'foot': G['feet'][1]}[part]


def _draw_blank3(pen, x, y, H, P, t, light=None, detail=None):
    sp = CAST['blank3']
    t = 0.0 if t is None else t
    G = _b3_geom(x + P.dx, y, H, P, t)
    u, f = G['u'], G['f']
    head_px = G['head_h']
    det = _auto_detail(pen, head_px) if detail is None else detail
    cl_ = clamp(P.__dict__.get('b3_collapse', 0.0))
    c = Ctx(pen, skia.Matrix(), _lw_for(head_px * 1.2))
    skin, skin_sh = sp['skin'], sp['skin_sh']
    tr = sp['cloth']['trousers']; tr_sh = sp['cloth']['trousers_sh']
    if cl_ > 0.001:
        pen.cv.save()
        m = skia.Matrix(); m.setScale(1.0 + 0.35 * cl_, max(0.04, 1.0 - 0.96 * ease_in_out(cl_)), x + P.dx, y)
        pen.cv.concat(m)
        pen.cv.saveLayer(None, skia.Paint(Alphaf=clamp(1.0 - ease_in_out(prog(cl_, 0.35, 0.95)))))
    tap = clamp(P.__dict__.get('b3_tap', 0.0))
    # far arm, far leg
    S, E, W = G['arms'][-1]
    end, ang = _draw_limb(c, [S, E, W], 30 * u, 19 * u, 0.84, mix(skin, '#000000', 0.12), skin_sh)
    _button_hand(c, end[0], end[1], ang - 90.0, 1.02 * u, det, t, mix(skin, '#000000', 0.12), skin_sh, tap=tap, seed=2)
    for k, col_ in ((0, mix(tr, '#000000', 0.25)), (1, tr)):
        fx, fy = G['feet'][k]; kx_, ky_ = G['knees'][k]
        lp = poly([G['hip'], (kx_, ky_), (fx, fy - 18 * u)], False)
        c.line(lp, 24 * u + c.lw * 2, LINE); c.line(lp, 24 * u, col_)
        c.fill(oval(kx_, ky_, 15 * u, 15 * u), col_); c.line(oval(kx_, ky_, 15 * u, 15 * u), c.lw * 0.5, tr_sh)
        sl = smooth([(fx - f * 26 * u, fy), (fx - f * 24 * u, fy - 22 * u), (fx + f * 30 * u, fy - 20 * u), (fx + f * 46 * u, fy - 4 * u),
                     (fx + f * 40 * u, fy)], True, 0.7)
        c.shape(sl, mix(sp['cloth']['shoes'], '#000000', 0.15 * (1 - k)), c.lw)
    # the long cardigan tube with its longer row of buttons
    hip, sh, hem = G['hip'], G['sh'], G['hem']
    axd = (sh[0] - hem[0], sh[1] - hem[1]); Lt = math.hypot(*axd) or 1.0
    nx, ny = -axd[1] / Lt, axd[0] / Lt
    mid = ((hip[0] + sh[0]) / 2 - nx * f * 9 * u, (hip[1] + sh[1]) / 2 - ny * f * 9 * u)
    torso = _tube([hem, hip, mid, sh], [70 * u, 64 * u, 54 * u, 58 * u])
    c.fill(torso, _B3_SLEEVE)
    c.grad(torso, hip[0] - f * 40 * u, 0, hip[0] + f * 40 * u, 0, [(0, _B3_SLEEVE_SH, 200), (0.5, _B3_SLEEVE, 0), (1, '#f2e8d2', 90)])
    if det >= 1: c.texture(torso, 'fabric', 0.08, 0.6)
    c.line(torso, c.lw)
    pl = [(hem[0] + axd[0] * k / 12 + nx * f * 9 * u, hem[1] + axd[1] * k / 12 + ny * f * 9 * u) for k in range(13)]
    c.line(poly(pl, False), c.lw * 0.6, _B3_SLEEVE_SH)
    for k in range(1, 12):
        bx, by = pl[k]
        _button_disc(c, bx + nx * f * 9 * u, by + ny * f * 9 * u, 7.5 * u, 7.5 * u, det)
    for k_ in (0.025, 0.05):                                  # the ribbed hem: two lines round the tube
        p_ = (hem[0] + axd[0] * k_, hem[1] + axd[1] * k_)
        c.line(poly([(p_[0] - nx * 33 * u, p_[1] - ny * 33 * u), (p_[0] + nx * 33 * u, p_[1] + ny * 33 * u)], False), c.lw * 0.6, _B3_SLEEVE_SH)
    # neck along the ceiling, then the head under it
    nk = smooth(G['neck'], False, 0.6) if len(G['neck']) > 2 else poly(G['neck'], False)
    c.line(nk, 15 * u + c.lw * 2, LINE); c.line(nk, 15 * u, skin); c.line(nk, 5 * u, skin_sh, 80)
    col = _tube([(sh[0], sh[1] + 6 * u), (sh[0], sh[1] - 16 * u)], [36 * u, 28 * u])
    c.fill(col, '#cbbd9a'); c.line(col, c.lw * 0.7)
    hx, hy = G['head']
    hc = c.sub(hx, hy, G['hrot'], head_px / 240.0)
    hc.lw = c.lw * 240.0 / head_px
    yaw = f * 0.42 * PI / 2 + P.h_turn * PI / 2
    draw_head_local(hc, 'blank3', P, yaw, P.h_nod * 0.6 + 0.18 * G['kbend'], det, t, light, sp)
    # near arm (a rounded shoulder first, so the sleeve grows out of the body)
    S, E, W = G['arms'][1]
    c.shape(oval(S[0], S[1] + 6 * u, 22 * u, 26 * u), _B3_SLEEVE, c.lw * 0.8)
    end, ang = _draw_limb(c, [S, E, W], 32 * u, 20 * u, 0.84, skin, skin_sh)
    _button_hand(c, end[0], end[1], ang - 90.0, 1.06 * u, det, t, skin, skin_sh, tap=tap)
    if cl_ > 0.001:
        pen.cv.restore(); pen.cv.restore()
        a_ = ease_in_out(prog(cl_, 0.3, 0.9))
        if a_ > 0.01: draw_flat_cardigan(pen, x + P.dx + f * 30 * u, y, 330 * u, alpha=a_, buttons=11)
    return G


def draw_flat_cardigan(pen, cx, y_floor, w, alpha=1.0, buttons=7, t=0.0):
    """The empty cardigan lying flat on the floor (what the Blank folds down to): a flat oatmeal heap, the sleeves
    splayed, the collar folded over, a row of buttons; nobody in it."""
    c = Ctx(pen, skia.Matrix(), _lw_for(w * 0.25))
    if alpha < 0.999: pen.cv.saveLayer(None, skia.Paint(Alphaf=clamp(alpha)))
    h = w * 0.13
    body = smooth([(cx - w * 0.42, y_floor), (cx - w * 0.36, y_floor - h * 0.8), (cx - w * 0.1, y_floor - h), (cx + w * 0.2, y_floor - h * 0.9),
                   (cx + w * 0.4, y_floor - h * 0.55), (cx + w * 0.46, y_floor)], True, 0.7)
    for sd in (-1, 1):
        sl = smooth([(cx + sd * w * 0.3, y_floor - h * 0.3), (cx + sd * w * 0.55, y_floor - h * 0.25), (cx + sd * w * 0.68, y_floor - h * 0.08),
                     (cx + sd * w * 0.66, y_floor), (cx + sd * w * 0.32, y_floor)], True, 0.7)
        c.fill(sl, _B3_SLEEVE_SH); c.line(sl, c.lw)
    c.fill(body, _B3_SLEEVE)
    c.grad(body, 0, y_floor - h, 0, y_floor, [(0, '#f2e8d2', 120), (1, _B3_SLEEVE_SH, 200)])
    c.line(body, c.lw)
    c.line(smooth([(cx - w * 0.3, y_floor - h * 0.55), (cx, y_floor - h * 0.75), (cx + w * 0.3, y_floor - h * 0.5)], False), c.lw * 0.6, _B3_SLEEVE_SH)
    for k in range(buttons):
        bx = cx - w * 0.34 + k * w * 0.68 / max(1, buttons - 1)
        _button_disc(c, bx, y_floor - h * 0.35 - 0.12 * h * math.sin(k), w * 0.016, w * 0.012, 2)
    if alpha < 0.999: pen.cv.restore()


# ====================================================================================================== the red coat
def coat_pts(cx, cy, h):
    """Points of the red coat drawn at collar (cx, cy), length h: its shoulders (where hands hold it) and the top button."""
    return dict(shoulder_l=(cx - 0.3 * h, cy + 0.05 * h), shoulder_r=(cx + 0.3 * h, cy + 0.05 * h),
                top_button=(cx + 0.07 * h, cy + 0.15 * h), hem=(cx, cy + h))


def coat_on(actor, t):
    """(cx, cy, h) to draw the red coat round a child actor's shoulders at t (collar at his neck, hem to mid thigh)."""
    nx, ny = actor.where(t, 'neck'); hx, hy = actor.where(t, 'hip')
    return nx, ny - 0.03 * actor.height, (hy - ny) * 1.55


def draw_red_coat(pen, cx, cy, h, buttons=0.0, open_=0.6, full=1.0, part='all', top_out=0.0, top_to=None, sway=0.0,
                  light=None, detail=2, t=0.0):
    """The red coat with seven shiny black buttons. Collar centre (cx, cy), length h. buttons 0..7 = how many are closed,
    from the bottom (fractional = the next one closing); open_ 0..1 how far the fronts hang apart; full 1 = someone in
    it (rounded), 0 = empty and limp (held at the shoulders). part 'back' (lining behind a wearer) / 'front' / 'all'.
    top_out 0..1 pulls the top button's corner out toward top_to (held out to him, never touching). Kid-safe: the
    collar stays open and loose; the top button is never closed by this drawing (buttons is capped at 6.99)."""
    buttons = min(buttons, 6.99)
    c = Ctx(pen, skia.Matrix(), _lw_for(h * 0.32))
    red, red_sh, red_hi, lin = '#b5262c', '#7a1418', '#d94a4c', '#3c1216'
    sag = 1.0 - clamp(full)
    sw = (0.29 - 0.04 * sag) * h; hw = (0.35 - 0.08 * sag) * h
    ys = [0.0, 0.08, 0.3, 0.55, 0.8, 1.0]
    def side_x(sd, k):
        return cx + sd * (sw + (hw - sw) * ys[k] ** 0.8) * (1.0 + 0.06 * full * math.sin(ys[k] * PI)) + sway * h * ys[k]
    by = [cy + h * (0.88 - j * 0.12) for j in range(7)]
    def gap(y_):                                              # half opening at height y_
        k = (y_ - cy) / h
        g = open_ * h * (0.05 + 0.16 * k)
        closed = 0.0
        for j in range(7):
            cj = clamp(buttons - j)
            if cj > 0: closed = max(closed, cj * clamp(1.0 - abs(y_ - by[j]) / (0.14 * h)) if j < int(buttons) + 1 else 0)
        if y_ > by[min(6, int(buttons))] - 0.02 * h and buttons >= 1: closed = max(closed, clamp(buttons - int(buttons)) if y_ < by[int(buttons)] + 0.07 * h else 1.0)
        return g * (1.0 - closed) - 0.035 * h * closed
    shell = smooth([(cx, cy - 0.02 * h), (side_x(1, 0), cy + 0.02 * h), (side_x(1, 2), cy + 0.3 * h), (side_x(1, 5), cy + h),
                    (side_x(-1, 5), cy + h), (side_x(-1, 2), cy + 0.3 * h), (side_x(-1, 0), cy + 0.02 * h)], True, 0.5)
    if part in ('back', 'all'):
        c.fill(shell, lin); c.line(shell, c.lw)
        if part == 'back': return
    yk = np.linspace(cy + 0.1 * h, cy + h, 10)
    for sd in (-1, 1):
        edge = [(cx + sd * gap(float(yy)) + (0.035 * h if sd > 0 else 0), float(yy)) for yy in yk]
        if sd > 0 and top_out > 0.01 and top_to is not None:
            k_ = ease_in_out(clamp(top_out))
            edge[0] = (edge[0][0] + (top_to[0] - edge[0][0]) * k_ * 0.85, edge[0][1] + (top_to[1] - edge[0][1]) * k_ * 0.85)
        outer = [(side_x(sd, 5), cy + h), (side_x(sd, 3), cy + 0.55 * h), (side_x(sd, 1), cy + 0.08 * h), (cx + sd * 0.12 * h, cy + 0.02 * h)]
        pnl = smooth([(cx + sd * 0.12 * h, cy + 0.02 * h)] + edge + outer[:-1], True, 0.45)
        c.fill(pnl, red)
        c.grad(pnl, cx - sd * 0.1 * h, 0, side_x(sd, 3), 0, [(0, red_hi, 60), (0.5, red, 0), (1, red_sh, 170)])
        if detail >= 1: c.texture(pnl, 'fabric', 0.1, 0.7)
        c.line(pnl, c.lw)
        if sd < 0 and detail >= 1:                            # buttonholes on the left front
            c.line(_multi([poly([(cx - gap(y_) + 0.03 * h, y_), (cx - gap(y_) + 0.075 * h, y_)], False) for y_ in by]), c.lw * 0.6, red_sh)
        if sd > 0:
            for j in range(7):
                ex = cx + gap(by[j]) + 0.035 * h
                bx, byy = ex - 0.012 * h, by[j]
                if j == 6 and top_out > 0.01 and top_to is not None:
                    k_ = ease_in_out(clamp(top_out)) * 0.85
                    bx, byy = bx + (top_to[0] - bx) * k_, byy + (top_to[1] - byy) * k_
                _button_disc(c, bx, byy, 0.028 * h, 0.028 * h, detail)
        pk = rrect(cx + sd * 0.14 * h - (0.13 * h if sd < 0 else 0), cy + 0.62 * h, 0.13 * h, 0.1 * h, 0.02 * h)
        c.line(pk, c.lw * 0.6, red_sh)
    for sd in (-1, 1):                                        # the open collar, loose, folded down
        cl = smooth([(cx + sd * 0.02 * h, cy + 0.0), (cx + sd * 0.2 * h, cy - 0.04 * h), (cx + sd * 0.3 * h, cy + 0.04 * h),
                     (cx + sd * (gap(cy + 0.12 * h) + 0.06 * h), cy + 0.2 * h), (cx + sd * 0.08 * h, cy + 0.08 * h)], True, 0.7)
        c.fill(cl, red_sh if sd < 0 else red); c.line(cl, c.lw * 0.9)
    for sd in (-1, 1):                                        # empty sleeves hanging at the sides (his hands stay free)
        sx0 = side_x(sd, 1)
        sv = smooth([(sx0 - sd * 0.02 * h, cy + 0.06 * h), (sx0 + sd * 0.07 * h, cy + 0.1 * h), (sx0 + sd * 0.09 * h + sway * h * 0.6, cy + 0.72 * h),
                     (sx0 - sd * 0.02 * h + sway * h * 0.6, cy + 0.74 * h), (sx0 - sd * 0.05 * h, cy + 0.3 * h)], True, 0.6)
        c.fill(sv, red_sh if sag > 0.5 else red); c.grad(sv, 0, cy, 0, cy + 0.74 * h, [(0, red, 0), (1, red_sh, 160)]); c.line(sv, c.lw * 0.9)


# ====================================================================================================== props (cm)
def _p_headset(c, det, t, P=None):
    band = smooth([(-8.5, 9.0), (-8.0, 1.0), (0.0, -1.5), (8.0, 1.0), (8.5, 9.0)], False, 0.8)
    c.line(band, 2.2, LINE); c.line(band, 1.4, '#3a3d46')
    for sd in (-1, 1):
        cp = oval(sd * 8.6, 11.0, 2.6, 3.6); c.shape(cp, '#2b2d34', c.lw * 0.6)
    boom = smooth([(8.6, 13.5), (7.0, 18.0), (2.5, 20.5)], False)
    c.line(boom, 1.3, LINE); c.line(boom, 0.7, '#2b2d34'); c.shape(oval(2.0, 20.6, 1.3, 1.1), '#1f2026', c.lw * 0.4)


def _p_music_box(c, det, t, P=None):
    """Mom's birthday surprise: a tiny wooden crank music box (8 x 5.5 cm) with a brass crank on its side."""
    ang = getattr(P, 'crank', 0.0) if P is not None else 0.0
    bx = rrect(-4.0, -5.5, 8.0, 5.5, 0.8)
    c.shape(bx, '#b27c4a', c.lw * 0.8); c.fill(rect(-4.0, -5.5, 8.0, 1.4), '#c99462'); c.line(poly([(-4, -4.1), (4, -4.1)], False), c.lw * 0.5)
    if det >= 1:
        c.line(_multi([poly([(-3.4 + k * 1.1, -3.6), (-3.4 + k * 1.1, -0.4)], False) for k in range(7)]), c.lw * 0.25, '#8a5a32', 150)
    hx, hy = 4.4, -2.8
    ex, ey = hx + math.cos(ang) * 2.4, hy + math.sin(ang) * 2.4
    c.line(poly([(hx, hy), (ex, ey)], False), 0.7, '#8a6a2a'); c.line(poly([(hx, hy), (ex, ey)], False), 0.45, '#e2bd58')
    c.shape(oval(hx, hy, 0.6, 0.6), '#e2bd58', c.lw * 0.4); c.shape(rrect(ex - 0.4, ey - 1.2, 0.8, 1.4, 0.35), '#6a3a22', c.lw * 0.4)


def _p_stop_sign(c, det, t, P=None):
    """Mr. Dunn's hand-held STOP paddle: red octagon (45 cm) with a white rim on its pole; grip just under the sign."""
    c.shape(rrect(-1.4, -14.0, 2.8, 92.0, 1.2), '#d8d8d2', c.lw * 0.7)
    oc = poly([(22.5 * math.cos(PI / 8 + k * PI / 4), -36.0 + 22.5 * math.sin(PI / 8 + k * PI / 4)) for k in range(8)])
    c.shape(oc, '#f2f0ea', c.lw); c.fill(poly([(19.5 * math.cos(PI / 8 + k * PI / 4), -36.0 + 19.5 * math.sin(PI / 8 + k * PI / 4)) for k in range(8)]), '#c8262a')
    if det >= 1:
        x_, y_ = c.pt(0.0, -36.0)
        text(c.cv, 'STOP', x_, y_ + 3.4 * c.s, 900, 10.5 * c.s, '#ffffff')


def _p_notepad(c, det, t, P=None):
    """Officer Mensah's flip notepad (10 x 14 cm), open, a few written lines."""
    pg = rrect(-5.0, -7.0, 10.0, 14.0, 0.6)
    c.shape(pg, '#f4f1e8', c.lw * 0.7); c.fill(rect(-5.0, -7.6, 10.0, 1.3), '#2a2f3a')
    if det >= 1:
        c.line(_multi([poly([(-3.6, -4.2 + k * 1.9), (2.6 - 1.4 * (k % 2), -4.2 + k * 1.9)], False) for k in range(5)]), c.lw * 0.3, '#3a4a8a', 200)


def _p_tab(c, det, t, P=None, back=False):
    """Owen's / the son's tablet (24 x 17 cm, landscape): the screen's glow (chat bubbles) or its plain back."""
    r = rrect(-12.0, -8.5, 24.0, 17.0, 1.6)
    if back:
        c.shape(r, '#5a5f6a', c.lw * 0.8); c.fill(oval(8.5, -5.5, 1.1, 1.1), '#2a2d33'); return
    c.shape(r, '#1c1e24', c.lw * 0.8)
    sc = rrect(-10.8, -7.3, 21.6, 14.6, 0.8)
    c.fill(sc, '#d9e4f2')
    if det >= 1:
        c.fill(oval(-8.4, -4.6, 1.6, 1.6), '#9ca2aa')
        for k, (x0, w_) in enumerate(((-6.2, 9.0), (-2.0, 10.0), (-6.2, 6.5))):
            c.fill(rrect(x0, -5.8 + k * 3.6, w_, 2.4, 1.1), '#ffffff' if k != 1 else '#7ea2d8', 240)


def _p_button1(c, det, t, P=None):
    _button_disc(c, 0.0, 0.0, 1.0, 1.0, det)


PROPS3.update({
    'headset': (_p_headset, 'hang', (0.0, 0.0)),
    'music_box': (_p_music_box, 'upright', (0.0, 0.0)),
    'stop_sign': (_p_stop_sign, 'upright', (0.0, 0.0)),
    'notepad': (_p_notepad, 'upright', (0.0, 0.0)),
    'tab': (_p_tab, 'upright', (0.0, 0.0)),
    'tab_back': (lambda c, d, t, P=None: _p_tab(c, d, t, P, True), 'upright', (0.0, 0.0)),
    'button': (_p_button1, 'upright', (0.0, 0.0)),
})


# ====================================================================================================== acting
def _ppc(self):
    return self.height / (self.sp.get('m', 1.7) * 100.0)


def _sx(self, t, side):
    """+1 / -1: which way (screen x) the arm on `side` lies from the body at t (front, back or 3/4 views alike)."""
    a = self.where(t, 'shoulder_l' if side > 0 else 'shoulder_r')[0] - self.where(t, 'chest')[0]
    return 1.0 if a > 0 else -1.0


def _bt_typing(self, t0, t1, kb, side=0, rate=6.0, z=40.0):
    """Type at a keyboard / tablet: both hands (or one: side) on the keys at kb (design point), fingers bobbing
    alternately; 'key_tap' events."""
    p = _ppc(self)
    sides = (1, -1) if not side else (side,)
    for s_ in sides:
        def tgt(t, s_=s_):
            x, y = _target_xy(kb, t)
            return x + _sx(self, t0, s_) * 7.0 * p, y + 0.9 * p * max(0.0, math.sin(t * rate * PI + (0 if s_ > 0 else 1.7)))
        self.reach_to(t0, s_, tgt, t1=t1, dur=0.5, z=z, contact='tips', shape='relaxed', fade=0.45)
    evs, tt = [], t0 + 0.5
    while tt < t1:
        evs.append(self._ev(tt, 'key_tap', -14.0)); tt += 1.0 / rate * (1.0 + 0.4 * hash01(int(tt * 10), 7))
    return evs


def _bt_one_finger(self, t0, t1, side=1, dur=0.35, toward=None):
    """"One minute.": the hand comes up at head height, out toward whoever is asking (toward = screen x direction;
    None = behind her, away from where she faces), index finger up, palm out; eyes stay on the screen."""
    p = _ppc(self)
    tw = toward if toward is not None else (-1.0 if self.at(t0 - 0.01).turn > 0 else 1.0)
    def tgt(t):
        x, y = self.where(t0, 'shoulder_l' if side > 0 else 'shoulder_r')
        return x + tw * 9.0 * p, y - 25.0 * p
    self.reach_to(t0, side, tgt, t1=t1, dur=dur, z=30.0, contact='palm', shape='point', fade=0.35)
    return self


def _bt_snap_photo(self, t0, aim, side=1, dur=1.6):
    """Mom lifts her phone (eyes and call on the laptop) and takes a photo of aim without looking at it: the phone comes
    up in front of her chest, tilts to aim, a shutter at the middle. Returns the shutter time."""
    p = _ppc(self)
    def tgt(t):
        cx, cy = self.where(t0, 'chest')
        ax, ay = _target_xy(aim, t)
        d = math.hypot(ax - cx, ay - cy) or 1.0
        return cx + (ax - cx) / d * 30.0 * p, cy - 8.0 * p + (ay - cy) / d * 10.0 * p
    self.reach_to(t0, side, tgt, t1=t0 + dur, dur=0.45, z=50.0, contact='palm', shape='grip', fade=0.45, prop='cell')
    self.hold_prop('cell', side, t0 + 0.1, t0 + dur + 0.3)
    ts = t0 + dur * 0.55
    return ts, [self._ev(ts, 'phone_shutter', -10.0)]


def _bt_headset_off(self, t0, side=1, t1=None, dur=0.9):
    """Pull the headset off: the hand to the ear cup, the headset comes away at t0 + 0.55 dur and stays in that hand
    (t1: until then; the film then puts it down)."""
    tm = t0 + dur * 0.55
    self.reach_to(t0, side, (self, 'eye_l' if side > 0 else 'eye_r'), t1=tm + 0.05, dur=dur * 0.5, z=-10.0, contact='tips',
                  shape='pinch', fade=dur * 0.45)
    self._add(t0 - 5.0, None, lambda P, t: P.__dict__.__setitem__('hs_off', 1.0 if t >= tm else 0.0), late=True)
    self.hold_prop('headset', side, tm, t1)
    return tm


def _bt_press_headset(self, t0, t1=None, side=1, dur=0.4):
    """"No... I can't see him anywhere.": her palm presses the headset's ear cup to her ear."""
    self.reach_to(t0, side, (self, 'eye_l' if side > 0 else 'eye_r'), t1=t1, dur=dur, z=-25.0, contact='palm', shape='open', fade=0.4)
    return self


def _bt_set_down(self, t0, prop, side, xy, dur=1.0, t1=None):
    """Carry a held prop (the headset, the phone) to xy and let go at t0 + 0.6 dur (the film draws it resting there
    from then). Returns the release time."""
    tr = t0 + dur * 0.6
    self.reach_to(t0, side, xy, t1=tr, dur=dur * 0.6, z=10.0, contact='grip', shape='grip', fade=0.4, prop=prop)
    self.hold_prop(prop, side, t0 - 1e6, tr)
    return tr


def _bt_hug(self, t0, child, t1=None, dur=0.9, kneel=True):
    """Kneel and hold him: both hands round his back at the shoulder blades (palms on his hoodie, never his face)."""
    if kneel: self.kneel_down(t0, dur=dur, knees=0, t1=t1)
    for s_, part in ((1, 'shoulder_r'), (-1, 'shoulder_l')):
        self.reach_to(t0 + 0.25, s_, (child, part), t1=t1, dur=dur * 0.7, z=-30.0, contact='palm', shape='open', fade=0.5)
    self.look_at(t0, (child, 'eyes'), t1=t1, dur=0.5)
    return self


def _bt_wind_box(self, t0, t1, side=-1, rate=1.4):
    """Hold the music box in front of the chest and wind it: one hand holds it, the other turns the crank (pose.crank)."""
    p = _ppc(self)
    def box(t):
        x, y = self.where(t0, 'chest')
        return x + 2.0 * p, y + 14.0 * p
    self.reach_to(t0, side, box, t1=t1, dur=0.5, z=60.0, contact='palm', shape='grip', fade=0.5, prop='music_box')
    self.hold_prop('music_box', side, t0, t1)
    def crank(t):
        bx, by = box(t); a = (t - t0) * rate * 2 * PI
        return bx + (4.4 + 2.4 * math.cos(a)) * p * -side, by - (2.8 - 2.4 * math.sin(a)) * p
    self.reach_to(t0 + 0.4, -side, crank, t1=t1, dur=0.5, z=60.0, contact='tips', shape='pinch', fade=0.5)
    self._add(t0, t1, lambda P, t: P.__dict__.__setitem__('crank', (t - t0) * rate * 2 * PI), real=True)
    self.look_at(t0, box, t1=t1, dur=0.5)
    return self


def _bt_rise_to(self, t0, target, side=1, dur=2.2, short_cm=2.5):
    """His fingers rise slowly toward a point (the top button) and stop short_cm before it ('tik' at the start)."""
    p = _ppc(self)
    def tgt(t):
        x, y = _target_xy(target, t); hx, hy = self.where(t0, 'chest')
        d = math.hypot(x - hx, y - hy) or 1.0
        return x - (x - hx) / d * short_cm * p, y - (y - hy) / d * short_cm * p
    self.reach_to(t0, side, tgt, t1=t0 + dur + 0.6, dur=dur, z=40.0, contact='tips', shape='pinch', fade=0.4)
    return [self._ev(t0, 'tik', -6.0)]


def _bt_drop_out(self, t0, x_to, run_dur=1.2, surface='inside'):
    """Drop straight down out of a loosely held coat (a fast crouch), then run to design x x_to (the coat stays in her
    hands). Returns the time he starts running."""
    self.crouch(t0, amount=1.0, t1=t0 + 0.35, dur=0.22, fade=0.25)
    self.run(t0 + 0.45, t0 + 0.45 + run_dur, 0.0, x_to - self.x0, surface=surface)
    return t0 + 0.45


def _bt_radio_up(self, t0, t1, side=1):
    """Mr. Dunn's hand radio up at his mouth ('already up'): eyes stay on the car."""
    p = _ppc(self)
    def tgt(t):
        x, y = self.where(t0, 'mouth')
        return x + _sx(self, t0, side) * 6.0 * p, y + 4.0 * p
    self.reach_to(t0, side, tgt, t1=t1, dur=0.35, z=30.0, contact='palm', shape='grip', fade=0.35, prop='walkie')
    self.hold_prop('walkie', side, t0 - 0.5, t1 + 0.5)
    return [self._ev(t0 + 0.3, 'radio_key', -10.0)]


def _bt_hold_sign(self, t0=-1e9, t1=None, side=-1):
    """Mr. Dunn's STOP paddle held upright a little out from his side (the sign beside him, never over his face)."""
    p = _ppc(self)
    def tgt(t):
        x, y = self.where(t0 if t0 > -1e8 else 0.0, 'hip')
        return x + _sx(self, t0 if t0 > -1e8 else 0.0, side) * 30.0 * p, y + 6.0 * p
    self.reach_to(t0, side, tgt, t1=t1, dur=0.5, z=10.0, contact='palm', shape='grip', fade=0.4, prop='stop_sign')
    self.hold_prop('stop_sign', side, t0, t1)
    return self


def _bt_shelter(self, t0, child, t1=None, side=-1, toward=1):
    """An arm out across in front of the child at his chest (palm open, toward the danger side `toward`), not touching."""
    p = _ppc(self)
    def tgt(t):
        x, y = child.where(t, 'chest')
        return x + toward * 5.0 * p, y + 2.0 * p
    self.reach_to(t0, side, tgt, t1=t1, dur=0.4, z=70.0, contact='palm', shape='open', fade=0.45)
    return self


def _bt_take_notes(self, t0, t1, pad_side=1):
    """Officer Mensah takes notes: the notepad held at his chest, the pencil writing small lines, eyes on the pad."""
    p = _ppc(self)
    def pad(t):
        x, y = self.where(t0, 'chest')
        return x + 3.0 * p, y + 8.0 * p
    self.reach_to(t0, pad_side, pad, t1=t1, dur=0.5, z=55.0, contact='palm', shape='grip', fade=0.5, prop='notepad')
    self.hold_prop('notepad', pad_side, t0, t1); self.hold_prop('pencil', -pad_side, t0, t1)
    def pen_(t):
        x, y = pad(t); u = (t - t0) % 1.4
        return x - pad_side * (3.0 - 4.0 * u / 1.4) * p, y + (-3.0 + 1.9 * int((t - t0) / 1.4) % 4) * p + 0.4 * p * math.sin(t * 21)
    self.reach_to(t0 + 0.3, -pad_side, pen_, t1=t1, dur=0.5, z=60.0, contact='tips', shape='grip', fade=0.5, prop='pencil')
    self.look_at(t0, pad, t1=t1, dur=0.4)
    return self


def _bt_read_board(self, t0, board, t1=None, then=None, side=1):
    """Read the fridge board (lean a little, eyes on it), then (then = (actor, 'eyes')) turn to her and point at it."""
    self.look_at(t0, board, t1=None if then is None else t0 + 1.4, dur=0.45)
    self.lean_in(t0, dur=1.2, amount=0.4)
    if then is not None:
        self.look_at(t0 + 1.4, then, t1=t1, dur=0.4)
        self.point_at(t0 + 1.5, board, t1=t1, side=side, dur=0.5)
    return self


def _bt_tablet_down(self, t0, surface, side=1, dur=1.0):
    """The son turns his tablet face down on the bed: the hand carries it there and lets go at t0 + 0.6 dur (the film
    draws it resting face down from then: prop 'tab_back'). Returns the contact time."""
    tc = t0 + dur * 0.6
    self.reach_to(t0 - 0.6, side, (self, 'chest'), t1=t0, dur=0.4, z=60.0, contact='palm', shape='grip', fade=0.3, prop='tab')
    self.reach_to(t0, side, surface, t1=tc, dur=dur * 0.6, z=10.0, contact='palm', shape='flat', fade=0.4, prop='tab_back')
    self.hold_prop('tab', side, t0 - 1e6, t0 + dur * 0.3); self.hold_prop('tab_back', side, t0 + dur * 0.3, tc)
    return tc


def _bt_flicker(self, t):
    """One frame of the grey default head (a fast turn)."""
    return self._add(t, t + 1.0 / 60.0, lambda P, tt: P.__dict__.__setitem__('default_head', 1.0), real=True)


# ---- form 3
def _b3_set_hand(self, t0, side, target, t1=None, dur=1.6, fade=None, tap=None):
    """Form 3's FINGERTIPS to a design point / callable / (actor, part) (her joints move slowly: dur >= 1.2 s reads
    right). Returns a 'tik' event as the hand arrives."""
    pre = 'b3_l' if side > 0 else 'b3_r'
    fade = dur if fade is None else fade
    def fn(P, t):
        w = _env(t, t0, t1, dur, fade)
        if w <= 0: return
        x, y = _target_xy(target, t)
        cw = P.__dict__.get(pre + 'w', 0.0)
        P.__dict__[pre + 'x'] = P.__dict__.get(pre + 'x', 0.0) * (1 - w) + x * w
        P.__dict__[pre + 'y'] = P.__dict__.get(pre + 'y', 0.0) * (1 - w) + y * w
        P.__dict__[pre + 'w'] = cw + (1.0 - cw) * w
        if tap is not None: P.__dict__['b3_tap'] = max(P.__dict__.get('b3_tap', 0.0), tap * w)
    self._add(t0, None if t1 is None else t1 + fade, fn)
    return [self._ev(t0 + dur * 0.8, 'tik', -8.0)]


def _b3_unfold(self, t0, dur=4.0, frm=0.0):
    """Unfold from the gap beside the fridge: legs, then the long body, then the neck rising until her head bends along
    the ceiling (slowly, joint by joint). 'b3_unfold' events: start, the head touching the ceiling."""
    self._add(t0 - 1e6, None, lambda P, t: P.__dict__.__setitem__('b3_unfold', frm + (1 - frm) * clamp((t - t0) / dur)))
    return [self._ev(t0, 'b3_unfold', -6.0), self._ev(t0 + dur * 0.86, 'b3_ceiling', -8.0)]


def _b3_collapse(self, t0, dur=1.6):
    """Fold in on herself down to a flat, empty cardigan (cloth folding flat)."""
    self._add(t0 - 1e6, None, lambda P, t: P.__dict__.__setitem__('b3_collapse', clamp((t - t0) / dur)))
    return [self._ev(t0, 'b3_collapse', -4.0)]


def _b3_hold_coat(self, t0, coat_fn, t1=None, dur=1.6, face=1):
    """Both hands at the coat's shoulders: coat_fn(t) -> (cx, cy, h) of the coat she holds (open toward him, or wrapped
    round him); the coat is drawn there by draw_red_coat. face = her b3_face."""
    self.b3_hand(t0, 1, lambda t: coat_pts(*coat_fn(t))['shoulder_r' if face > 0 else 'shoulder_l'], t1, dur)
    self.b3_hand(t0, -1, lambda t: coat_pts(*coat_fn(t))['shoulder_l' if face > 0 else 'shoulder_r'], t1, dur)
    return self


def _b3_lunge(self, t0, sweep_from, sweep_to, dur=1.4, t1=None, side=1):
    """Lunge at a sound: lean in, the near hand sweeps along a line (the counter) with the fingers tapping."""
    self.set(t0, t1, 0.5, b3_lean=1.0, b3_look=1.0)
    def tgt(t):
        k = ease_in_out(clamp((t - t0) / dur))
        a, b = _target_xy(sweep_from, t), _target_xy(sweep_to, t)
        return a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
    return self.b3_hand(t0, side, tgt, t1, dur=0.8, tap=1.0)


Acting.typing = _bt_typing
Acting.one_finger = _bt_one_finger
Acting.snap_photo = _bt_snap_photo
Acting.headset_off = _bt_headset_off
Acting.hug = _bt_hug
Acting.press_headset = _bt_press_headset
Acting.set_down = _bt_set_down
Acting.wind_box = _bt_wind_box
Acting.rise_to = _bt_rise_to
Acting.drop_out = _bt_drop_out
Acting.radio_up = _bt_radio_up
Acting.shelter = _bt_shelter
Acting.hold_sign = _bt_hold_sign
Acting.take_notes = _bt_take_notes
Acting.read_board = _bt_read_board
Acting.tablet_down = _bt_tablet_down
Acting.flicker = _bt_flicker
Acting.b3_hand = _b3_set_hand
Acting.b3_unfold = _b3_unfold
Acting.b3_collapse = _b3_collapse
Acting.b3_hold_coat = _b3_hold_coat
Acting.b3_lunge = _b3_lunge


# ====================================================================================================== self-test
def _selftest_buttons():
    out = []
    surf = skia.Surface(640, 360); pen = Pen(surf.getCanvas())
    for who in BUTTONS_CAST:
        a = Acting(who, seed=3, height=300).place(320, 340)
        P = a.at(1.0)
        draw(pen, who, 320, 340, 300, P, t=1.0)
        if who != 'blank3': draw_bust(pen, who, 320, 180, 0.4, P, t=1.0)
    out.append('%d buttons cast ids draw (full + bust)' % len(BUTTONS_CAST))
    o = Acting('owen', seed=1, height=300).place(300, 340); o.set(0, None, 0.0, faded=1.0, refl_hide=1.0)
    assert draw(pen, 'owen', 300, 340, 300, o.at(1.0), reflection=True) is None
    b = Acting('blank3', seed=2, height=320).place(300, 340)
    b.b3_unfold(0.0, 4.0); b.b3_hand(4.0, 1, (380, 170), dur=1.5); b.b3_collapse(8.0, 1.5)
    g0 = _b3_geom(300, 340, 320, b.at(0.0), 0.0); g1 = _b3_geom(300, 340, 320, b.at(5.0), 5.0)
    top = min(p[1] for p in g1['neck'])
    assert abs(top - (340 - 320)) < 0.12 * 320 and g1['kbend'] > 0.5, ('neck along the ceiling', top, g1['kbend'])
    assert g0['sh'][1] > g1['sh'][1] + 60, 'unfold rises'
    hx, hy = b3_point(b, 6.0, 'tips_l')
    assert math.hypot(hx - 380, hy - 170) < 4.0, ('b3 fingertip reach', hx, hy)
    for t_ in (0.0, 2.0, 5.0, 9.6): draw(pen, 'blank3', 300, 340, 320, b.at(t_), t=t_)
    out.append('blank3: unfold rises to the ceiling, the neck bends along it, hand reach < 4 px, collapse draws')
    draw_red_coat(pen, 300, 120, 160, buttons=6, open_=0.5, full=0.0, top_out=1.0, top_to=(360, 150))
    draw_long_arm(pen, (100, 200), (400, 250), 1.0, 1.0, 1.2)
    out.append('coat / long arm / flat cardigan draw')
    for o_ in out: print(o_)
    print('buttons self-test ok')


_selftest_before_buttons = _selftest


def _selftest():
    """python3 characters.py --selftest: the older films' checks (with their own 'mom' / 'owen' / 'son'), then these."""
    try:
        CAST.update(_BTN_OLD)
        _selftest_before_buttons()
    finally:
        CAST.update(_BTN_NEW)
    _selftest_buttons()
