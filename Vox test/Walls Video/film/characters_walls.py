"""characters_walls.py: the cast of "If Your Little Brother Says Someone Lives In The Walls... DON'T LAUGH" and its staging.

Not imported on its own: characters.py runs it in its own namespace at the end of the module (exec, after
characters_ice.py), so everything here is part of `characters` (import characters as CH). The family, the neighbour and
the police are v3 cast entries (outfits, proportions, props) on the existing people rig; Mr. Pell is the same rig in
Dad's buffalo-check flannel with an original rubber hound MASK drawn over his own head (his eyes and teeth show through
it). See WALLS_API below and CAST.md.
"""
# NOTE: runs inside characters.py's globals (math, np, skia, Ctx, HeadMap, Body, CAST, Pose, Acting, _figure3 ... exist).

WALLS_API = """
Walls film cast ids (this film takes the plain names; the older films' ones live on as 'mom_bunny', 'dad_ice', 'theo94'):
  'sam' (12, day tee) / 'sam_pj'          'theo' (6, dinosaur pyjamas)
  'mom' (day) / 'mom_pj'                  'dad' (day one: the red buffalo-check flannel) / 'dad_tee' / 'dad_pj'
  'pell'       MR. PELL masked: Dad's flannel (loose), grey trousers, grey socks, long pale dusty fingers, the rubber
               hound mask (pose.mask_lift 0..1 pulls it up and off: his own face underneath; >= 1 no mask)
  'pell_bare'  Pell unmasked (grey stubble, tired, lonely)   'dabrowski' (late 60s, glasses, teal cardigan)
  'reyes'      Officer Reyes        'officer_w' a generic officer
Shared: WALLS_TILT (the head tilt Dad and the doorway figure share), Acting.walls_tilt(t0, t1, dur).
Pell: doorway(t0, t1), back_away(t0, t1, steps), tuck_blanket(t0, a, b, dur), shush(t0, t1, side), crawl(t0, t1, x0, x1,
  facing), slide_panel(t0, side, grip, dx, dur) -> panel_dx(t), cuffed(t0, t1), eye to a crack = head_to(t0, pt,
  'eye_l'); insert: draw_head_at(pen, 'pell', P, x, y, px_per_unit, part='eye_l').
Family: carry_hush(t0, child, t1) + draw_carry_walls(pen, sam, theo, t, blanket=True); shake_awake(t0, t1, other);
  flip_switch(t0, side, xy) -> flip time; read_note(t0, t1); laugh(t0, dur); sigh(t0, dur); sing = talk;
  Mom on the phone: phone_to_ear(t0, t1, side) + expr 'terrified_call'; phone_to_mouth(t0, t1) (Theo sings into it).
Mrs. Dabrowski: offer_pie(t0, dur, facing).  Reyes: lift_mask(t0, pell, dur) (the mask goes to her hand, 'hound_mask').
Props: 'pie' / 'pie_r', 'hound_mask' (limp, held by the crown).  Parts: where(t, 'mouth') is the MASK's mouth when on.
"""

# ====================================================================================================== keep old ids
for _o, _n in (('mom', 'mom_bunny'), ('dad', 'dad_ice'), ('theo', 'theo94')):
    if _o in CAST and _n not in CAST: CAST[_n] = CAST[_o]

POSE_DEFAULTS.update(mask_lift=0.0, ear_sw=0.0, crawl=0.0, crawl_ph=0.0, cuffs=0.0)
WALLS_TILT = dict(h_tilt=21.0, h_nod=0.12, tilt=-2.0)      # Dad's habit and the doorway figure's: the SAME every time

# ====================================================================================================== outfits
_DOC_ROWS.update({'flannel3': (24, 0.93, 8, 12, 14, 16, 16, 12), 'tee_w': (12, 0.88, 2, 4, 6, 8, 8, 6)})
_SLEEVES3.update({'flannel3': 'long', 'tee_w': 'short'})


def _front_tee_w(c, sp, B, rows, P, det, t):
    """A plain T-shirt: a ribbed round neck (a ringer collar in cl['trim'])."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    nk, v = _surf_poly(B, rows, [(-b['neck'] - 4, B.y_sh - 30), (-b['neck'] * 0.6, B.y_sh - 18), (0, B.y_sh - 13),
                                 (b['neck'] * 0.6, B.y_sh - 18), (b['neck'] + 4, B.y_sh - 30)], dz=3)
    if v > -0.2:
        c.line(smooth(nk, False), lw * 2.4, LINE); c.line(smooth(nk, False), lw * 1.5, cl.get('trim', cl['top_sh']))


def _front_flannel3(c, sp, B, rows, P, det, t):
    """Dad's red-and-black buffalo-check flannel, worn open at the neck over a T-shirt: collar, placket, buttons, two flap
    pockets (the check itself is laid on the torso and sleeves by the texture hook below)."""
    _flannel_front(c, sp, B, rows, P, det, t)


_FRONTS3.update({'tee_w': _front_tee_w, 'flannel3': _front_flannel3})
_PLAID_OUT = ('flannel3',)
_W_PLAID = {'on': None}


def _buffalo(c, path, cl, ang, ax, ay, sx=1.0, per=58.0):
    """Buffalo check: equal dark bands both ways over the red (single = dark red, crossed = black), anchored to a body
    point (ax, ay) so it never swims, rotated by ang (a sleeve's angle), squeezed by sx (a torso turned away)."""
    bb = path.getBounds()
    R = max(bb.width(), bb.height()) + per * 2
    cc = c.sub(ax, ay, ang, 1.0)
    n = int(R / per) + 2
    h = per * 0.5
    v_ = [rect((k * per - h * 0.5) * sx, -R, h * sx, 2 * R) for k in range(-n, n + 1)]
    hz = [rect(-R, k * per - h * 0.5, 2 * R, h) for k in range(-n, n + 1)]
    with c.clip(path):
        cc.fill(_multi(v_), cl['check'], 140)
        cc.fill(_multi(hz), cl['check'], 140)


_ctx_texture_w_prev = Ctx.texture


def _ctx_texture_w(self, path, name, alpha=0.2, scale=1.0, dx=0.0, dy=0.0):
    f = _W_PLAID['on']
    if f is not None and name == 'fabric':
        _W_PLAID['on'] = None
        _buffalo(self, path, *f)
    return _ctx_texture_w_prev(self, path, name, alpha, scale, dx, dy)


Ctx.texture = _ctx_texture_w
_neck3_w_prev = _neck3


def _neck3(c, sp, B, skin, skin_sh):
    r = _neck3_w_prev(c, sp, B, skin, skin_sh)
    if sp.get('outfit') in _PLAID_OUT:                       # the next fabric pass is the torso: lay the check on it
        X, Y, _, _ = B.p3(0, B.y_ch, 0)
        _W_PLAID['on'] = (sp['cloth'], 0.0, X, Y, max(0.4, abs(B.ct)))
    return r


_draw_arm3_w_prev = _draw_arm3


def _draw_arm3(c, sp, B, P, side, det, t, skin, sh, sleeve, sleeve_sh, light):
    S, E, Wr = _arm_data(sp, B, P, side)
    if sp.get('outfit') in _PLAID_OUT:
        s3, e3 = B.p3(*S), B.p3(*E)
        ang = math.degrees(math.atan2(e3[1] - s3[1], e3[0] - s3[0])) - 90.0
        _W_PLAID['on'] = (sp['cloth'], ang, s3[0], s3[1], 1.0)
    try:
        r = _draw_arm3_w_prev(c, sp, B, P, side, det, t, skin, sh, sleeve, sleeve_sh, light)
    finally:
        _W_PLAID['on'] = None
    if getattr(P, 'cuffs', 0.0) > 0.5:
        _cuff(c, sp, B, P, side, E, Wr)
    return r


def _cuff(c, sp, B, P, side, E, Wr):
    """A steel handcuff ring on this wrist; the chain to the other wrist is drawn with the second (front) arm."""
    w3, e3 = B.p3(*Wr), B.p3(*E)
    k = 0.86
    x, y = e3[0] + (w3[0] - e3[0]) * k, e3[1] + (w3[1] - e3[1]) * k
    a = math.degrees(math.atan2(w3[1] - e3[1], w3[0] - e3[0])) - 90.0
    r = sp['body']['arm'][1] * w3[2] * 0.62
    cc = c.sub(x, y, a, 1.0)
    ring = minus(oval(0, 0, r * 1.18, r * 0.42), oval(0, 0.0, r * 0.98, r * 0.24))
    cc.fill(ring, '#aeb4bd'); cc.line(ring, c.lw * 0.55)
    cc.line(poly([(-r * 0.7, -r * 0.3), (r * 0.2, -r * 0.4)], False), c.lw * 0.5, '#eef2f6', 200)
    prev = getattr(P, '_cuff_pt', None)
    if prev is None:
        try: P._cuff_pt = (x, y)
        except AttributeError: pass
        return
    mx, my = (prev[0] + x) / 2, (prev[1] + y) / 2 + r * 0.5
    ch = smooth([prev, (mx, my), (x, y)], False)
    c.line(ch, c.lw * 2.2, LINE); c.line(ch, c.lw * 1.2, '#9aa1aa')
    try: del P._cuff_pt
    except AttributeError: pass


_draw_hand_w_prev = _draw_hand


def _draw_hand(c, sp, shape, x, y, scale, angle, side, det, skin, sh, ring=False, press=0.0, t=0.0):
    r = _draw_hand_w_prev(c, sp, shape, x, y, scale, angle, side, det, skin, sh, ring, press, t)
    if sp.get('dust') and det >= 1:                          # plaster dust on the fingertips (pale chalky ends + specks)
        try: G = _hand_cached(shape, side, round(press, 1))
        except Exception: return r
        hc = c.sub(x, y, angle, scale * sp['body'].get('hand', 1.0))
        u = G['union']; bb = u.getBounds()
        with hc.clip(u):
            hc.grad(rect(bb.left() - 2, bb.bottom() - 16, bb.width() + 4, 18), 0, bb.bottom() - 16, 0, bb.bottom(),
                    [(0, '#ece6d8', 0), (0.6, '#ece6d8', 150), (1, '#f4f0e6', 210)])
            hc.fill(_multi([oval(bb.left() + bb.width() * hash01(k, 71), bb.bottom() - 4 - 22 * hash01(k, 72), 1.3) for k in range(9)]),
                    '#f6f2ea', 200)
    return r


# ====================================================================================================== the cast
# Sam, 12: the narrator as a boy. Dark brown hair, hazel eyes, a few freckles' worth of blush; a green ringer tee.
_SAM = dict(hair='side_short', sex='m', hh=210.0, child=True, m=1.50, head_ws=[0, 55, 80, 95, 100, 100, 94, 81, 60, 32, 0],
            eye_dx=41, eye_y=2, eye_r=20.5, iris_c='#6b5a34', iris_k=0.7, lid_rest=0.12, pupil=1.05, brow_th=7.5, nose_len=15,
            mouth_y=62, mouth_w=16, nose='button', ears=1.1, skin='#e9bf9f', skin_sh='#be9178', skin_dp='#7c564a',
            blush='#e49c8e', lip='#b97a70', lips=0.05, hair_c='#3a2618', brow_c='#2e1d12', bags=0.2, age=0.0, blink_rate=0.3,
            lashes=0.3, part=1, body=dict(sh=92, ch=92, wa=86, hip=86, arm=(38, 32), leg=(42, 35), neck=31, hand=0.84, arm_k=0.9))
_SAM_CL = dict(top='#5f8f6a', top_sh='#3f6a4a', top_hi='#80b08a', trim='#e8e2d2', trousers='#3c4c6a', trousers_sh='#263248',
               shoes='#d8d4cc', shoes_sh='#9a968e', socks='#e8e4dc', socks_sh='#b8b4aa')
CAST['sam'] = _v3cast(outfit='tee_w', feet='shoes', **_SAM, cloth=dict(_SAM_CL))
CAST['sam_pj'] = _v3cast(outfit='tee_w', feet='socks', **_SAM,
                         cloth=dict(_SAM_CL, top='#9aa3ad', top_sh='#6e7782', top_hi='#b8c0c8', trim='#7d8692', trousers='#2f3e5c',
                                    trousers_sh='#1d2840'))
# Theo, 6: a blond-brown mop, big brown eyes, a gap tooth; blue dinosaur pyjamas (orange and green dinosaurs).
_THEO_W = dict(hair='cowlick', sex='m', hh=238.0, child=True, m=1.16, head_ws=[0, 58, 85, 99, 104, 104, 99, 87, 66, 36, 0],
               eye_dx=40, eye_y=7, eye_r=23.0, iris_c='#6b4a2e', iris_k=0.72, lid_rest=0.08, pupil=1.15, brow_th=6.5, nose_len=12,
               mouth_y=64, mouth_w=15, nose='button', ears=1.15, skin='#f2caaf', skin_sh='#ca9c86', skin_dp='#865e55',
               blush='#f0a097', lip='#c47e78', lips=0.1, hair_c='#b08a58', brow_c='#8a6a40', bags=0.1, age=0.0, blink_rate=0.35,
               lashes=0.5, part=1, gap=True,
               body=dict(sh=78, ch=77, wa=73, hip=75, arm=(32, 26), leg=(37, 31), neck=28, hand=0.74, arm_k=0.86))
CAST['theo'] = _v3cast(outfit='pj_dino', feet='socks', **_THEO_W,
                       cloth=dict(top='#86a9d6', top_sh='#5a7cab', top_hi='#aac6ea', trim='#f2f4f8', print_c='#ec8a3a',
                                  print_c2='#5fae5a', trousers='#86a9d6', trousers_sh='#5a7cab', socks='#eceae4', socks_sh='#bdb9b0'))
# Mom, about 40: dark brown hair to the shoulders, brown eyes, warm; a coral tee, jeans / lavender pyjamas at night.
_MOM_W = dict(hair='loose', sex='f', hh=182.0, m=1.66, head_ws=[0, 49, 71, 87, 92, 90, 82, 66, 46, 24, 0],
              eye_dx=40, eye_y=-6, eye_r=18.5, iris_c='#5a3e2a', lid_rest=0.2, brow_th=7.0, nose_len=21, mouth_w=20,
              skin='#e4b799', skin_sh='#b98b72', skin_dp='#7a5446', blush='#e09a8e', lip='#b4686a', lips=0.6,
              hair_c='#3b2a22', brow_c='#2e2018', bags=0.3, age=0.35, lashes=1.2, ring=1, part=1,
              body=dict(sh=102, ch=102, wa=86, hip=104, arm=(41, 33), leg=(46, 38), neck=33, hand=0.98))
CAST['mom'] = _v3cast(outfit='tee_w', feet='flats', **_MOM_W,
                      cloth=dict(top='#d9806e', top_sh='#a85a4c', top_hi='#eea28e', trim='#c46a5a', trousers='#4a5f84',
                                 trousers_sh='#2f3f5c', shoes='#6a4a3a', shoes_sh='#43301f'))
CAST['mom_pj'] = _v3cast(outfit='pj3', feet='socks', **_MOM_W,
                         cloth=dict(top='#a99ac8', top_sh='#7c6c9e', top_hi='#c6badf', trim='#efeaf6', print_c='#a99ac8',
                                    print_c2='#a99ac8', trousers='#a99ac8', trousers_sh='#7c6c9e', socks='#eeeae4', socks_sh='#bcb8b0'))
# Dad, mid 40s: tall and lean (1.87 m: his build is how the doorway silhouette reads), short dark hair, light stubble.
# Day one he wears THE red buffalo-check flannel; later a blue tee; in bed a grey tee.
_DAD_W = dict(hair='side_short', sex='m', hh=176.0, m=1.87, head_ws=[0, 51, 75, 92, 98, 97, 90, 75, 54, 29, 0],
              eye_dx=42, eye_y=-7, eye_r=17.5, iris_c='#5d6e80', lid_rest=0.24, brow_th=10.0, nose_len=25, mouth_w=21,
              skin='#dfae90', skin_sh='#b2816a', skin_dp='#704c42', blush='#d8948a', lip='#a26c62', stubble='#4a3a2e', stub=0.45,
              hair_c='#3e2c20', brow_c='#33241a', bags=0.4, age=0.45, ring=-1, part=-1,
              body=dict(sh=126, ch=118, wa=104, hip=104, arm=(50, 41), leg=(56, 46), neck=44, hand=1.06))
_FLANNEL = dict(top='#b8262a', top_sh='#7e1418', top_hi='#d8484a', check='#120c0c', check_hi='#d8484a', tee='#d9d6ce',
                trousers='#4a5262', trousers_sh='#2e3440', shoes='#4a3628', shoes_sh='#2c1f16', socks='#8e9094', socks_sh='#626468')
CAST['dad'] = _v3cast(outfit='flannel3', feet='shoes', **_DAD_W, cloth=dict(_FLANNEL))
CAST['dad_tee'] = _v3cast(outfit='tee_w', feet='shoes', **_DAD_W,
                          cloth=dict(_FLANNEL, top='#5d6f8a', top_sh='#3e4c64', top_hi='#7d90aa', trim='#4a5a74'))
CAST['dad_pj'] = _v3cast(outfit='tee_w', feet='socks', **_DAD_W,
                         cloth=dict(_FLANNEL, top='#8a8f96', top_sh='#62676e', top_hi='#a6abb2', trim='#71767d',
                                    trousers='#3a4250', trousers_sh='#242a34'))
# Mr. Lawrence Pell, late 60s: tall, thin, slightly stooped, long pale hands (plaster dust on the fingertips), grey stubble,
# thin grey hair; Dad's flannel loose on him, grey work trousers, grey socks. 'pell' wears the hound mask.
_PELL = dict(hair='thin', sex='m', hh=168.0, m=1.88, head_ws=[0, 50, 72, 86, 90, 86, 76, 62, 46, 25, 0],
             eye_dx=40, eye_y=-6, eye_r=17.5, iris_c='#7a8a8c', lid_rest=0.34, pupil=0.95, brow_th=7.0, nose_len=28, mouth_w=20,
             skin='#dcc4b2', skin_sh='#ad9283', skin_dp='#6c5650', blush='#cf9e98', lip='#a07a74', stubble='#a8a49e', stub=0.85,
             stub_dots=1.0, gaunt=1.2, hair_c='#a9a6a0', brow_c='#8a8680', bags=1.0, age=1.0, lashes=0.2, blink_rate=0.22,
             hand_k=1.32, dust=True, stoop=0.28,
             body=dict(sh=116, ch=104, wa=92, hip=96, arm=(40, 33), leg=(46, 38), neck=36, hand=1.12))
_PELL_CL = dict(_FLANNEL, trousers='#7d7f82', trousers_sh='#55575a', socks='#8f9195', socks_sh='#636569', tee='#cfc9bc')
CAST['pell_bare'] = _v3cast(outfit='flannel3', feet='socks', **_PELL, cloth=dict(_PELL_CL))
CAST['pell'] = dict(CAST['pell_bare'], hound=True, blink_rate=0.12)
# Mrs. Dabrowski, late 60s, across the street: set ash-blond curls, glasses on a chain, coral lipstick, a teal cardigan over
# a flowered blouse; nice, nosy. Holds out a pie.
CAST['dabrowski'] = _v3cast(
    outfit='gran3', hair='set_curls', sex='f', hh=188.0, m=1.60, glasses=True, chain=True,
    head_ws=[0, 52, 77, 94, 100, 99, 91, 76, 54, 28, 0], eye_dx=41, eye_y=-4, eye_r=17.0, iris_c='#6a8aa0', lid_rest=0.26,
    brow_th=6.0, nose_len=23, mouth_w=21, skin='#efc9b4', skin_sh='#c49a87', skin_dp='#87615a', blush='#ec9c98', lip='#d0606a',
    lips=0.8, hair_c='#d8c9a8', brow_c='#a89a80', bags=0.6, age=1.0, lashes=0.6, feet='shoes', ring=1, earrings='pearl',
    body=dict(sh=100, ch=110, wa=106, hip=114, arm=(42, 34), leg=(40, 33), neck=33, hand=0.95),
    cloth=dict(top='#3f8a8a', top_sh='#2a6464', top_hi='#62a8a6', blouse='#f4ece0', blouse_sh='#d0c4b0', flower='#e47a8a',
               flower2='#8ab870', brooch='#d8b04c', skirt='#6a5a4a', skirt_sh='#4a3e32', legs='#e9c6b2', trousers='#6a5a4a',
               trousers_sh='#4a3e32', shoes='#5a3d2e', shoes_sh='#3a271d'))
# Officer Reyes (calm, kind, competent): dark hair in a low bun, warm brown skin; a generic male officer beside her.
CAST['reyes'] = _v3cast(
    outfit='police', hat=None, hair='bun', sex='f', hh=182.0, m=1.68,
    head_ws=[0, 50, 72, 87, 92, 90, 81, 64, 43, 22, 0], eye_dx=41, eye_y=-7, eye_r=18.5, iris_c='#3a2618', lid_rest=0.2,
    brow_th=8.5, nose_len=21, mouth_w=20, skin='#c68c68', skin_sh='#9a6448', skin_dp='#5e3a2c', blush='#c87a6a', lip='#94584e',
    lips=0.45, hair_c='#1e1512', brow_c='#1a1210', bags=0.35, age=0.35, lashes=1.0, earrings=True, feet='shoes',
    body=dict(sh=114, ch=110, wa=92, hip=104, arm=(44, 36), leg=(58, 46), neck=40, hand=0.92), cloth=dict(_POLICE, shirt='#22304d'))
CAST['officer_w'] = dict(CAST['cop'], skin='#e0b294', skin_sh='#b3826a', skin_dp='#704a3e', blush='#d8948a', lip='#a06a60',
                         hair_c='#6a4a2e', brow_c='#5a3e26', stubble='#6a4a2e', stub=0.3, hat=None)
WALLS_CAST = ('sam', 'sam_pj', 'theo', 'mom', 'mom_pj', 'dad', 'dad_tee', 'dad_pj', 'pell', 'pell_bare', 'dabrowski', 'reyes',
              'officer_w')

# ====================================================================================================== the hound mask
# Head units (crown -120, chin +120). An original cheap latex Halloween hound: a pale fawn dome a little bigger than his
# head, a long heavy muzzle with low flews, a wet black nose, sad half-closed sculpted lids over dark eye holes (HIS eyes
# show in them, they blink), red droopy lower lids, worried brow folds, long ears hanging close (a beat late), grey tape
# round the left ear, a loose wrinkled rubber hem round his neck. His own teeth show in the mouth slit.
_HD = dict(rub='#c9a37c', rub_sh='#8c6848', rub_dk='#5a3f2c', rub_hi='#e6c9a4', muz='#d9bd9a', muz_sh='#a5845f',
           ear='#8a5d3b', ear_sh='#5c3c25', ear_in='#b07a58', nose='#141012', hole='#120907', haw='#ad4a50', haw_dk='#6e2830',
           tape='#a4a7aa', tape_hi='#d3d6d8', teeth='#e8dfc6', teeth_sh='#b8ab88', gum='#9c5a58', lip='#a8706a')
_HM_MASK = dict(head_ys=[-120, -114, -100, -70, -30, 10, 50, 82, 104, 116, 120],
                head_ws=[0, 40, 70, 94, 103, 102, 97, 88, 76, 58, 0])


def _hd_cols(light):
    k = (light or {}).get('key', 0.0)
    if k >= -0.01: return _HD
    return {n: mix(v, '#6f7890', min(0.5, -0.4 * k)) for n, v in _HD.items()}


def _muz_w(y): return float(np.interp(y, [-6, 20, 50, 85, 104, 118], [13, 24, 37, 47, 50, 38]))
def _muz_d(y): return float(np.interp(y, [-6, 10, 36, 60, 95, 118], [4, 18, 40, 42, 36, 26]))


def _hd_ear(c, hm, side, ang, cols, det, tape):
    """One long ear hanging from the side of the dome; ang = swing (deg) in the head frame."""
    y0 = -52.0
    w = float(hm.W(y0)) * 0.93
    X, Y, V = hm.map1(side * w, y0, -2.0)
    ec = c.sub(X, Y, ang, 1.0)
    s = side
    pts = [(-s * 4, -10), (s * 14, 20), (s * 25, 80), (s * 24, 132), (s * 10, 166), (-s * 8, 170), (-s * 20, 150), (-s * 21, 92),
           (-s * 14, 30), (-s * 10, 0)]
    e = smooth(pts, True, 0.9)
    ec.fill(e, cols['ear'])
    ec.grad(e, -s * 22, 0, s * 27, 0, [(0, cols['ear_sh'], 200), (0.45, cols['ear'], 0), (1, cols['ear_sh'], 120)])
    ec.grad(e, 0, -6, 0, 60, [(0, cols['ear_sh'], 170), (1, cols['ear_sh'], 0)])
    if det >= 1:
        ec.line(smooth([(s * 3, 18), (s * 8, 80), (s * 6, 140), (-s * 2, 176)], False), c.lw * 0.45, cols['ear_sh'], 200)
        ec.line(smooth([(s * 18, 60), (s * 22, 120)], False), c.lw * 0.6, cols['rub_hi'], 70)
    if tape:
        tp = poly([(-s * 26, 88), (s * 31, 78), (s * 33, 102), (-s * 24, 112)], True)
        with ec.clip(e):
            ec.fill(tp, cols['tape']); ec.line(tp, c.lw * 0.35, '#6e7174', 200)
            if det >= 1:
                ec.line(_multi([poly([(s * (-14 + 11 * k), 86 - 1.6 * k), (s * (-12 + 11 * k), 107 - 1.6 * k)], False) for k in range(4)]),
                        c.lw * 0.3, '#7d8083', 150)
                ec.line(poly([(-s * 20, 90), (s * 26, 81)], False), c.lw * 0.5, cols['tape_hi'], 150)
        tab = poly([(s * 27, 80), (s * 36, 76), (s * 37, 90), (s * 28, 94)], True)
        ec.fill(tab, cols['tape']); ec.line(tab, c.lw * 0.45)
    ec.line(e, c.lw)
    return V


def _hd_head(c, sp, P, yaw, pitch, det, t, light, empty=False):
    """The mask on head-unit Ctx c. empty: dark holes (pulled up off his face, or in Reyes' hand)."""
    cols = _hd_cols(light)
    hm = HeadMap(_HM_MASK, yaw, pitch)
    hmh = HeadMap(sp, yaw, pitch, jaw=10.0 * clamp(P.m_open))
    fm = hmh                                                   # face features ride HIS face (eyes and teeth line up)
    R = P.tilt + P.h_tilt
    ears = []
    for side in (-1, 1):
        w = float(hm.W(-52.0)) * 0.93
        V = hm.map1(side * w, -52.0, -2.0)[2]
        a = -0.72 * R + getattr(P, 'ear_sw', 0.0) + side * 3.0 - 10.0 * math.sin(yaw) * 0.4
        ears.append((V, side, a))
    for V, side, a in ears:
        if V < -0.06: _hd_ear(c, hm, side, a, cols, det, side > 0)
    # the loose rubber hem round his neck (under the jowls)
    hem_y = 146.0
    wav = [(-56 + 112 * k / 10.0, hem_y + 4.0 * math.sin(k * 2.1 + 0.7) + 3.0 * hash01(k, 33)) for k in range(11)]
    neck = smooth([(-46, 92), (46, 92), (57, hem_y - 6)] + wav[::-1] + [(-57, hem_y - 6)], True, 0.6)
    c.fill(neck, cols['rub_sh']); c.grad(neck, 0, 90, 0, hem_y, [(0, cols['rub_dk'], 200), (1, cols['rub_sh'], 60)])
    if det >= 1:
        c.line(_multi([smooth([(-46 + 3 * k, 112 + 10 * k), (-8, 117 + 11 * k), (24, 113 + 10 * k), (48 - 3 * k, 118 + 9 * k)], False)
                           for k in range(3)]), c.lw * 0.4, cols['rub_dk'], 170)
    c.line(smooth(wav, False), c.lw * 1.6, cols['rub_hi'], 160)
    c.line(neck, c.lw)
    # the dome
    sil = hm.silhouette()
    c.fill(sil, cols['rub'])
    fz = hm.map1(0, 0)[2]
    c.grad(sil, -110, 0, 110, 0, [(0, cols['rub_sh'], 150), (0.35, cols['rub'], 0), (0.75, cols['rub'], 0), (1, cols['rub_sh'], 170)])
    c.grad(sil, 0, -120, 0, 120, [(0, cols['rub_hi'], 90), (0.4, cols['rub'], 0), (1, cols['rub_sh'], 140)])
    if det >= 1:
        with c.clip(sil): c.texture(sil, 'grunge', 0.12, 0.8)
        c.fill(_blob(*hm.map1(-28, -78)[:2], 26, 9, 9, 3, 0.2), '#fff6e6', 55)          # rubber sheen
    if light and light.get('rim'):
        c.fill(_crescent(sil, -light.get('side', 1) * 8, 0), light['rim'], light.get('rim_a', 70))
    c.line(sil, c.lw)
    if fz > -0.3:
        # worried brow folds (inner ends high) and forehead wrinkles
        if det >= 0:
            fl = []
            for side in (-1, 1):
                fl.append([hm.map1(side * x, y, 3)[:2] for x, y in ((10, -46), (28, -52), (50, -42), (64, -26))])
            for k, yy in enumerate((-70, -86)):
                fl.append([hm.map1(x, yy + 0.004 * x * x, 2)[:2] for x in (-46, -18, 0, 18, 46)])
            c.line(_multi([smooth(p_, False) for p_ in fl]), c.lw * 0.7, cols['rub_dk'], 190)
            c.line(_multi([smooth([(x_, y_ + 3) for x_, y_ in p_], False) for p_ in fl[:2]]), c.lw * 0.7, cols['rub_hi'], 90)
        # eyes: dark holes with HIS eyes in them, heavy sculpted lids, red droopy lower lids
        sk, ssh, _ = _skin_cols(sp, P, light)
        for side in (-1, 1):
            ex, ey = side * sp['eye_dx'], sp['eye_y'] + 2.0
            if fm.map1(ex, ey, 2)[2] < 0.1: continue
            hole_f = [(ex - side * 22, ey - 3), (ex - side * 8, ey - 15), (ex + side * 12, ey - 14), (ex + side * 28, ey + 5),
                      (ex + side * 19, ey + 13), (ex, ey + 14), (ex - side * 17, ey + 7)]
            hole = smooth([fm.map1(x, y, 3)[:2] for x, y in hole_f], True, 0.9)
            sock = smooth([fm.map1(x, y, 2)[:2] for x, y in
                           [(ex - side * 30, ey - 6), (ex - side * 10, ey - 26), (ex + side * 22, ey - 22), (ex + side * 38, ey + 8),
                            (ex + side * 22, ey + 30), (ex - side * 6, ey + 28), (ex - side * 28, ey + 14)]], True, 0.9)
            c.fill(sock, cols['rub_dk'], 150)
            c.fill(sock, cols['rub_sh'], 90)
            c.fill(hole, cols['hole'])
            if not empty:
                with c.clip(hole):
                    _eye(c, hmh, sp, P, side, det, t, sk, ssh)
                    c.fill(_multi([oval(*fm.map1(ex + side * 4, ey - 2, 3)[:2], 34, 9)]), cols['hole'], 120)   # the lid's shadow
            # heavy upper lid (rubber, half closed, sagging at the outer corner)
            op = clamp(1.0 - 0.6 * P.blink if empty else 1.0)
            lid_f = [(ex - side * 26, ey - 6), (ex - side * 8, ey - 20), (ex + side * 16, ey - 18), (ex + side * 33, ey + 2),
                     (ex + side * 24, ey + 6), (ex + side * 6, ey - 1), (ex - side * 12, ey - 1), (ex - side * 24, ey - 1)]
            lid = smooth([fm.map1(x, y, 5)[:2] for x, y in lid_f], True, 0.85)
            c.fill(lid, cols['rub']); c.grad(lid, 0, *fm.map1(ex, ey - 18, 5)[1:2], 0, fm.map1(ex, ey, 5)[1],
                                             [(0, cols['rub_hi'], 120), (1, cols['rub_sh'], 200)])
            c.line(lid, c.lw * 0.8)
            rim = smooth([fm.map1(x, y, 5)[:2] for x, y in lid_f[4:]], False)
            c.line(rim, c.lw * 2.0, cols['rub_dk'], 230)
            # the red droopy lower lid (haw) and the bag under it
            haw = smooth([fm.map1(x, y, 4)[:2] for x, y in
                          [(ex - side * 18, ey + 7), (ex, ey + 12), (ex + side * 20, ey + 10), (ex + side * 25, ey + 12),
                           (ex + side * 10, ey + 22), (ex - side * 8, ey + 18)]], True, 0.9)
            c.fill(haw, cols['haw']); c.line(haw, c.lw * 0.6)
            c.line(smooth([fm.map1(x, y, 4)[:2] for x, y in [(ex - side * 14, ey + 9), (ex + side * 4, ey + 13), (ex + side * 20, ey + 11)]], False),
                   c.lw * 0.9, cols['haw_dk'], 220)
            c.line(smooth([fm.map1(x, y, 3)[:2] for x, y in [(ex - side * 22, ey + 22), (ex, ey + 32), (ex + side * 30, ey + 24)]], False),
                   c.lw * 0.7, cols['rub_dk'], 170)
        # the muzzle (projects forward: dz), its flews, the mouth slit with his teeth, the wet nose
        ys = np.linspace(-6, 118, 14)
        L = [fm.map1(-_muz_w(y), y, _muz_d(y) * 0.45)[:2] for y in ys]
        C = [fm.map1(0, y, _muz_d(y))[:2] for y in ys]
        Rr = [fm.map1(_muz_w(y), y, _muz_d(y) * 0.45)[:2] for y in ys]
        muz = union(smooth(L + C[::-1], True, 0.7), smooth(C + Rr[::-1], True, 0.7))
        c.fill(muz, cols['muz'])
        c.grad(muz, 0, C[0][1], 0, C[-1][1], [(0, cols['rub'], 120), (0.35, cols['muz'], 0), (0.8, cols['muz_sh'], 120), (1, cols['rub_sh'], 210)])
        sd = 1 if math.sin(yaw) > 0 else -1
        c.grad(muz, C[6][0] - sd * 10, 0, C[6][0] + sd * 90, 0, [(0, cols['muz'], 0), (1, cols['muz_sh'], 150)])
        if det >= 1:
            with c.clip(muz): c.texture(muz, 'grunge', 0.1, 0.7)
            for side in (-1, 1):                                  # muzzle dots and the flew fold
                c.fill(_multi([oval(*fm.map1(side * (14 + 7 * (k % 3)), 62 + 6 * (k // 3), _muz_d(62) * 0.8)[:2], 1.4) for k in range(6)]),
                       cols['muz_sh'], 200)
            c.line(_multi([smooth([fm.map1(side * x, y, _muz_d(y) * 0.6)[:2] for x, y in ((22, 58), (36, 80), (46, 102), (42, 116))], False)
                           for side in (-1, 1)]), c.lw * 0.8, cols['rub_dk'], 200)
        k0 = 4
        c.line(smooth(L[k0:] + [C[-1]] + Rr[k0:][::-1], False, 0.7), c.lw)
        c.line(smooth(L[1:k0 + 1], False), c.lw * 0.5, cols['rub_dk'], 150); c.line(smooth(Rr[1:k0 + 1], False), c.lw * 0.5, cols['rub_dk'], 150)
        c.line(smooth(C[1:5], False), c.lw * 2.2, cols['rub_hi'], 80)
        # mouth slit: dark, his upper teeth, his lower lip (drops with his jaw when he whispers)
        mo = clamp(P.m_open)
        my0, my1 = 84.0, 96.0 + 10.0 * mo
        mf = [(-30, my0 + 3), (-14, my0 - 1), (0, my0), (14, my0 - 1), (30, my0 + 3), (20, my1), (0, my1 + 3), (-20, my1)]
        mouth = smooth([fm.map1(x, y, _muz_d(y) * 0.92)[:2] for x, y in mf], True, 0.9)
        c.fill(mouth, '#1e0c0c')
        if not empty:
            with c.clip(mouth):
                tl = []
                for k in range(-3, 3):
                    x0 = k * 8.0 + 0.6
                    tl.append(rrect(*fm.map1(x0, my0 - 2, _muz_d(my0) * 0.95)[:2], 7.2, 8.5, 2.2))
                c.fill(poly([fm.map1(x, my0 - 4, _muz_d(my0))[:2] for x in (-34, 34)] + [fm.map1(x, my0 + 1, _muz_d(my0))[:2] for x in (34, -34)], True),
                       cols['gum'])
                tt = _multi(tl)
                c.fill(tt, cols['teeth']); c.line(tt, c.lw * 0.35, cols['teeth_sh'])
                if mo > 0.15:
                    c.fill(_multi([rrect(*fm.map1(k * 8.0 + 0.6, my1 - 6.0, _muz_d(my1) * 0.9)[:2], 7.0, 5.0, 2.0) for k in range(-2, 2)]),
                           cols['teeth'], 230)
                lp = smooth([fm.map1(x, y, _muz_d(y) * 0.92)[:2] for x, y in ((-30, my1 + 2), (-12, my1 - 3), (12, my1 - 3), (30, my1 + 2), (0, my1 + 8))], True)
                c.fill(lp, cols['lip'])
        c.line(mouth, c.lw * 0.9)
        # nose: big, wet, black
        nd = _muz_d(42) + 7.0
        nose = smooth([fm.map1(x, y, nd - 0.012 * (x * x))[:2] for x, y in
                       ((-27, 40), (-20, 31), (0, 28), (20, 31), (27, 40), (18, 54), (5, 57), (-5, 57), (-18, 54))], True, 0.9)
        c.fill(nose, cols['nose'])
        nx, ny = fm.map1(0, 40, nd)[:2]
        c.radial(nose, nx - 8, ny - 8, 30, [(0, '#5a5050', 255), (0.5, '#221c1c', 160), (1, '#000000', 0)])
        if det >= 0:
            c.fill(_multi([_blob(*fm.map1(sx_, 48, nd)[:2], 6.0, 3.6, 7, 4, 0.15) for sx_ in (-11, 11)]), '#000000', 255)
            hx, hy = fm.map1(-9, 34, nd)[:2]
            c.fill(oval(hx, hy, 7.0, 3.6), '#ffffff', 215); c.fill(oval(hx + 13, hy + 1, 2.6, 1.8), '#ffffff', 190)
            c.fill(oval(*fm.map1(10, 50, nd)[:2], 4.0, 1.6), '#ffffff', 110)
        c.line(nose, c.lw)
        c.line(smooth([fm.map1(0, y, _muz_d(y))[:2] for y in (57, 70, 84)], False), c.lw * 0.7, cols['rub_dk'], 200)
    for V, side, a in ears:
        if V >= -0.06: _hd_ear(c, hm, side, a, cols, det, side > 0)


_dhl_walls_prev = draw_head_local


def draw_head_local(c, who, P, yaw, pitch, det, t, light=None, sp=None):
    """WALLS: Mr. Pell's rubber hound mask over his own head ('pell'). pose.mask_lift 0..1 pulls it up and off (his face
    underneath); 1 = no mask."""
    sp = sp or CAST[who]
    if not sp.get('hound'): return _dhl_walls_prev(c, who, P, yaw, pitch, det, t, light, sp)
    lift = clamp(getattr(P, 'mask_lift', 0.0))
    bare = CAST['pell_bare']
    if lift > 0.002:
        _dhl_walls_prev(c, 'pell_bare', P, yaw, pitch, det, t, light, bare)
    if lift >= 0.999: return None
    if lift > 0.002:
        mc = c.sub(0.0, -235.0 * ease_in_out(lift), -6.0 * lift, 1.0, 1.0 + 0.22 * math.sin(PI * lift))
        _hd_head(mc, bare, P, yaw, pitch, det, t, light, empty=True)
    else:
        _hd_head(c, bare, P, yaw, pitch, det, t, light)
    return None


def _p_hound_mask(c, det, t, P=None):
    """The empty mask held by the crown, hanging (about 34 cm): Officer Reyes after she pulls it off."""
    Q = Pose(); Q.m_open = 0.3
    hc = c.sub(0.0, 16.0, 4.0, 0.13, 0.12)
    _hd_head(hc, CAST['pell_bare'], Q, 0.15, 0.25, det, t, None, empty=True)


def _p_pie(c, det, t, P=None, flip=1):
    """Mrs. Dabrowski's pie in a glass dish, lattice top, a tea towel under it; the grip is the near rim (x = 0)."""
    s = flip
    dish = poly([(0, -2), (s * 26, -2), (s * 24, 4), (s * 2, 4)], True)
    top = oval(s * 13, -3, 13.5, 3.6)
    tow = poly([(-s * 1.5, 2), (s * 27.5, 2), (s * 25, 8.5), (s * 18, 6), (s * 9, 9.5), (s * 1, 6)], True)
    c.fill(tow, '#e8e2d4'); c.line(tow, c.lw * 0.4)
    if det >= 1: c.line(_multi([poly([(s * x, 2.5), (s * (x - 1), 7)], False) for x in (6, 12, 18, 24)]), c.lw * 0.6, '#c0504a', 200)
    c.fill(dish, '#c9d6d8'); c.line(dish, c.lw * 0.5)
    c.fill(top, '#d9a35a'); c.grad(top, 0, -6, 0, 0, [(0, '#f0c27a', 255), (1, '#b07a38', 255)])
    if det >= 0:
        with c.clip(top):
            c.line(_multi([poly([(s * (x - 4), -7), (s * (x + 4), 1)], False) for x in range(2, 26, 5)] +
                          [poly([(s * (x + 4), -7), (s * (x - 4), 1)], False) for x in range(2, 26, 5)]), c.lw * 1.2, '#a8682e', 230)
        c.fill(_multi([oval(s * x, -3.5 + 0.3 * (x % 3), 1.1, 0.5) for x in (7, 13, 19)]), '#7a2a3a', 230)
    c.line(top, c.lw * 0.6)


PROPS3.update({'hound_mask': (_p_hound_mask, 'hang', (0.0, 0.0)), 'pie': (_p_pie, 'upright', (0.0, 0.0)),
               'pie_r': (lambda c, d, t, P=None: _p_pie(c, d, t, P, -1), 'upright', (0.0, 0.0))})


def draw_head_at(pen, who, P, x, y, px_per_unit, part='eye_l', t=0.0, light=None, detail=2, yaw=None, pitch=None):
    """Draw only a head, huge, with a face part ('eye_l' / 'eye_r' / 'mouth' / 'nose' / 'center') at design (x, y):
    inserts (the eye at the pantry crack, the mask's mouth behind his finger). px_per_unit = design px per head unit
    (the head is 240 units tall)."""
    sp = CAST[who]
    yaw = (P.turn + P.h_turn) * PI / 2 if yaw is None else yaw
    pitch = P.h_nod * 0.6 if pitch is None else pitch
    hm = HeadMap(sp, yaw, pitch)
    fx, fy, dz = {'eye_l': (sp['eye_dx'], sp['eye_y'], 2), 'eye_r': (-sp['eye_dx'], sp['eye_y'], 2), 'mouth': (0, 88, 40),
                  'nose': (0, 42, 48), 'center': (0, 0, 0)}[part]
    X, Y, _ = hm.map1(fx, fy, dz)
    rot = P.tilt + P.h_tilt
    a = math.radians(rot)
    ox = (X * math.cos(a) - Y * math.sin(a)) * px_per_unit; oy = (X * math.sin(a) + Y * math.cos(a)) * px_per_unit
    c = Ctx(pen, skia.Matrix(), _lw_for(240 * px_per_unit)).sub(x - ox, y - oy, rot, px_per_unit)
    draw_head_local(c, who, P, yaw, pitch, detail, t, light, sp)


# ====================================================================================================== rig hooks
_body_point_prev_walls = _body_point


def _body_point(self, P, part):
    sp = self.sp
    if sp.get('hound') and getattr(P, 'mask_lift', 0.0) < 0.5 and part in ('mouth', 'nose', 'snout', 'crown'):
        B = Body(sp, P)
        fx, fy, dz = {'mouth': (0, 88, 40), 'nose': (0, 42, 48), 'snout': (0, 60, 44), 'crown': (0, -120, 0)}[part]
        return _head_point(sp, B, P, fx, fy, dz)
    return _body_point_prev_walls(self, P, part)


_at_prev_walls = Acting.at


def _walls_at(self, t):
    P = _at_prev_walls(self, t)
    sp = self.sp
    if sp.get('stoop'): P.hunch += sp['stoop']
    if sp.get('hound'):
        # the ears swing a beat late: the head's roll from 0.1 s and 0.26 s ago (with a small overshoot) + sideways moves
        a = self._raw(t - 0.1, False); b = self._raw(t - 0.26, False)
        R = P.tilt + P.h_tilt; Ra = a.tilt + a.h_tilt; Rb = b.tilt + b.h_tilt
        P.ear_sw = clamp(0.95 * (Ra - R) - 0.45 * (Rb - Ra) + 9.0 * P.sec_x, -40.0, 40.0)
    return P


Acting.at = _walls_at
Acting.__call__ = _walls_at
_leg_chain_prev_walls = _leg_chain


def _leg_chain(sp, B, P, side):
    H, K, A, pitch = _leg_chain_prev_walls(sp, B, P, side)
    cr = getattr(P, 'crawl', 0.0)
    if cr > 0.01 and B.kneel > 0.3:                         # crawling: the knees step forward in turn, lifting as they swing
        ph = P.crawl_ph * 2 * PI + (0.0 if side > 0 else PI)
        d = 55.0 * math.sin(ph) * cr; lift = max(0.0, math.cos(ph)) * 22.0 * cr
        off = _v3(0.0, -lift, d)
        K = K + off; A = A + off * 0.7
    return H, K, A, pitch


# ====================================================================================================== acting
def _w_tilt(self, t0, t1=None, dur=0.8, amount=1.0):
    """THE head tilt (WALLS_TILT): Dad's habit when he listens; the doorway figure's every time."""
    def fn(P, t):
        w = _env(t, t0, t1, dur, dur) * amount
        if w <= 0: return
        for k, v in WALLS_TILT.items(): setattr(P, k, getattr(P, k) + v * w)
    return self._add(t0, None if t1 is None else t1 + dur, fn)


def _w_doorway(self, t0, t1=None, fade=0.5):
    """Standing in a doorway at night, watching: arms hanging long and still, the tilt, very slow breathing, no fidgets."""
    self.walls_tilt(t0, t1, 1.1)
    L = self._alen()
    def fn(P, t):
        w = _env(t, t0, t1, fade, fade)
        if w <= 0: return
        for sd in (-1, 1): self._arm(P, sd, w, 4.0, 0.98 * L, 0.06 * L, 'relaxed', up=0.0)
        P.lock = lerp(P.lock, 1.0, w); P.still = lerp(P.still, 1.0, w)
    return self._add(t0, None if t1 is None else t1 + fade, fn)


def _w_back_away(self, t0, t1, steps=4, fade=0.4):
    """Back away facing the room (slow steps backwards, the tilt held, no turn). The film moves him into depth (shrink
    the drawn height / raise y_feet along the hall); this only animates the legs and the body."""
    def fn(P, t):
        w = _env(t, t0, t1, fade, fade)
        if w <= 0: return
        u = prog(t, t0, t1)
        P.walk_amt = max(P.walk_amt, 0.55 * w)
        P.walk_ph = -0.5 * steps * u
        P.lean -= 0.05 * w
    return self._add(t0, t1 + fade, fn)


def _w_tuck(self, t0, a, b, dur=2.6, knees=0, t1=None):
    """Kneel beside a bed and tuck the blanket in: both hands come to the blanket's top edge between design points a and
    b, smooth it outwards and press it down at the sides. Returns the press time (blanket settles)."""
    self.kneel_down(t0, 0.9, knees=knees, t1=t1)
    tc = t0 + 0.9
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    end = t0 + dur
    def tgt(p0, p1):
        return lambda t: (lerp(p0[0], p1[0], ease_in_out(prog(t, tc + 0.35, end - 0.25))),
                          lerp(p0[1], p1[1], ease_in_out(prog(t, tc + 0.35, end - 0.25))))
    near_a = (lerp(mid[0], a[0], 0.25), lerp(mid[1], a[1], 0.25)); near_b = (lerp(mid[0], b[0], 0.25), lerp(mid[1], b[1], 0.25))
    sa = -1 if a[0] < b[0] else 1
    self.reach_to(tc - 0.3, sa, tgt(near_a, a), t1=t1 if t1 is not None else end + 0.6, dur=0.6, contact='palm', shape='flat', lean=False)
    self.reach_to(tc - 0.2, -sa, tgt(near_b, b), t1=t1 if t1 is not None else end + 0.6, dur=0.6, contact='palm', shape='flat', lean=False)
    self._ev(end - 0.2, 'blanket', -10.0, 0.0)
    return end - 0.2


def _w_shush(self, t0, t1=None, side=1, dur=0.8, fade=0.6):
    """One finger lifted to where his lips should be (the mask's mouth): the index across the slit, slow."""
    s = self.height / 1000.0
    def tgt(t):
        x, y = self.where(t, 'mouth', post=False)
        return x, y - 18.0 * s
    self.reach_to(t0, side, tgt, t1=t1, dur=dur, z=150.0, contact='tips', shape='point', fade=fade, lean=False)
    return self


def _w_crawl(self, t0, t1, x_from, x_to, facing=None, fade=0.35, stride=300.0):
    """On hands and knees, fast and quiet (inside the wall, under a bed): the knees step in turn (pose.crawl), the palms
    plant on the floor (the figure's y_feet) and lift as they swing, the head up looking ahead. Side view."""
    d = x_to - x_from
    face = facing if facing is not None else (1.0 if d >= 0 else -1.0)
    s = self.height / 1000.0
    cycles = max(1.0, abs(d) / (s * stride))
    def u_of(t): return ease_in_out(prog(t, t0, t1)) * 0.2 + prog(t, t0, t1) * 0.8
    def fn(P, t):
        w = _env(t, t0 - fade, t1, fade, fade)
        P.dx = x_from + d * u_of(t)
        if w <= 0: return
        P.turn = lerp(P.turn, face, w)
        P.kneel = max(P.kneel, w); P.knees = 1.0
        P.lean += 2.25 * w; P.h_nod -= 0.95 * w
        P.crawl = w; P.crawl_ph = cycles * u_of(t)
        P.bob += 7.0 * math.sin(4 * PI * cycles * u_of(t)) * w
    self._add(t0 - fade, None, fn)
    def hand(side):
        def f(t):
            u = u_of(t)
            ph = cycles * u * 2 * PI + (PI if side > 0 else 0.0)
            sx, sy = self.where(t, 'shoulder_l' if side > 0 else 'shoulder_r', post=False)
            return sx + face * (0.05 + 0.07 * math.sin(ph)) * self.height, self.y0 - max(0.0, math.cos(ph)) * 0.025 * self.height
        return f
    for sd in (-1, 1):
        self.reach_to(t0 - fade * 0.5, sd, hand(sd), t1=t1, dur=fade, contact='palm', shape='flat', lean=False, fade=fade)
    for k in range(int(cycles * 2)):
        self._ev(t0 + (t1 - t0) * (k + 0.5) / (cycles * 2), 'crawl_thump', -18.0, 0.0)
    return self


def _w_slide_panel(self, t0, side, grip, dx, dur=1.4):
    """Hand to the closet's back panel at design point `grip`, then slide it sideways by dx px (the hand stays on it).
    Returns panel_dx(t) for the set: 0 before the push, dx at the end."""
    tc = t0 + 0.55
    def pdx(t): return dx * ease_in_out(prog(t, tc, t0 + dur))
    self.reach_to(t0, side, lambda t: (grip[0] + pdx(t), grip[1]), t1=t0 + dur + 0.15, dur=0.55, contact='palm', shape='flat', fade=0.5)
    self._ev(tc, 'panel_slide', -8.0, 0.0)
    return pdx


def _w_cuffed(self, t0=-1e9, t1=None, fade=0.4):
    """Hands cuffed in front, resting together in the lap (seated on the curb) or at the belt: steel cuffs and a chain."""
    s = self.height / 1000.0
    for sd in (-1, 1):
        self.reach_to(t0, sd, lambda t, sd=sd: (self.where(t, 'lap', post=False)[0] + sd * 34.0 * s, self.where(t, 'lap', post=False)[1] - 30.0 * s),
                      t1=t1, dur=fade, z=90.0, contact='wrist', shape='relaxed', fade=fade, lean=False)
    def fn(P, t):
        P.cuffs = 1.0 if _env(t, t0, t1, fade, fade) > 0.5 else 0.0
    return self._add(t0, None if t1 is None else t1 + fade, fn)


def _w_carry_hush(self, t0, child, t1=None, fade=0.5):
    """Carry the little one on the hip (carry) with the free hand over his mouth (shhh): draw with draw_carry_walls."""
    self.carry(t0, child, t1=t1, fade=fade)
    near = 1 if math.sin(self._raw(t0 + 0.01, False).turn * PI / 2) <= 0 else -1
    self.reach_to(t0 + 0.05, -near, (child, 'mouth'), t1=t1, dur=fade, z=40.0, contact='palm', shape='relaxed', fade=fade, lean=False)
    return self


def _w_shake_awake(self, t0, t1, other, side=None, rate=4.2):
    """Both hands on the sleeper's shoulder, shaking it; the sleeper's body rocks with it (other: an Acting)."""
    s = self.height / 1000.0
    part = 'shoulder_l' if (other.x0 > self.x0) == (other._raw(t0, False).turn >= 0) else 'shoulder_r'
    def osc(t): return math.sin(2 * PI * rate * (t - t0)) * _env(t, t0, t1, 0.3, 0.3)
    for k, sd in enumerate((-1, 1)):
        self.reach_to(t0, sd, lambda t, k=k: (other.where(t, part, post=False)[0] + (k - 0.5) * 60 * s + 14 * s * osc(t),
                                             other.where(t, part, post=False)[1] + (k - 0.5) * 24 * s),
                      t1=t1, dur=0.45, contact='palm', shape='flat', fade=0.5)
    other._add(t0, t1 + 0.3, lambda P, t: setattr(P, 'dx', P.dx + 10.0 * s * osc(t)))
    self.set(t0, t1, 0.3, lean=0.3)
    return self


def _w_flip_switch(self, t0, side, xy, dur=0.5):
    """Reach the wall switch with the fingertips and flick it (the set's switch flips at the returned time)."""
    tf = t0 + dur
    self.reach_to(t0, side, lambda t: (xy[0], xy[1] - 10.0 * self.height / 1000.0 * ease_in_out(prog(t, tf - 0.06, tf + 0.05))),
                  t1=tf + 0.35, dur=dur, contact='tips', shape='point', fade=0.45)
    self._ev(tf, 'switch_click', -6.0, 0.0)
    return tf


def _w_read_note(self, t0, t1, side=-1):
    """Hold the note up in front (read it), the eyes on it."""
    self.hold_up('note', t0, t1, side)
    self.set(t0, t1, 0.5, h_nod=0.22, look_y=0.35)
    return self


def _w_laugh(self, t0, dur=1.6):
    """A warm, easy laugh: head back, shoulders bouncing, eyes squeezed (Dad: 'that's every noise explained')."""
    self.expr('talk_smile', t0, t0 + dur, 0.3)
    def fn(P, t):
        u = prog(t, t0, t0 + dur)
        if u <= 0 or u >= 1: return
        e = math.sin(PI * u)
        P.h_nod -= 0.16 * e; P.shrug += 0.06 * e * (0.5 + 0.5 * math.sin(2 * PI * 5.0 * (t - t0)))
        P.m_open = max(P.m_open, 0.35 * e * (0.6 + 0.4 * math.sin(2 * PI * 4.5 * (t - t0)))); P.squint = max(P.squint, 0.6 * e)
    self._ev(t0 + 0.05, 'laugh', -6.0, 0.0)
    return self._add(t0, t0 + dur, fn)


def _w_sigh(self, t0, dur=1.8):
    """A long tired sigh: the chest fills, the shoulders drop, the head dips, the eyes close a moment."""
    def fn(P, t):
        u = prog(t, t0, t0 + dur)
        if u <= 0 or u >= 1: return
        up = math.sin(PI * clamp(u / 0.4)) if u < 0.4 else 0.0
        dn = math.sin(PI * clamp((u - 0.3) / 0.7))
        P.shrug += 0.22 * up - 0.12 * dn; P.breath += 0.8 * up
        P.h_nod += 0.18 * dn; P.blink = max(P.blink, 0.85 * math.sin(PI * clamp((u - 0.35) / 0.4)) if 0.35 < u < 0.75 else 0.0)
        P.m_open = max(P.m_open, 0.12 * dn)
    self._ev(t0 + 0.3, 'sigh', -10.0, 0.0)
    return self._add(t0, t0 + dur, fn)


def _w_phone_to_mouth(self, t0, t1=None, fade=0.5):
    """Both hands hold the phone just under the chin (Theo sings the address into it)."""
    s = self.height / 1000.0
    def tgt(t):
        x, y = self.where(t, 'chin', post=False)
        return x, y + 40.0 * s
    self.hold_prop('cell', -1, t0 - fade, t1)
    self.reach_to(t0, -1, tgt, t1=t1, dur=fade, z=120.0, contact='grip', shape='grip', fade=fade, prop='cell', lean=False)
    self.reach_to(t0, 1, lambda t: (tgt(t)[0] + 26.0 * s, tgt(t)[1] + 26.0 * s), t1=t1, dur=fade, z=110.0, contact='palm',
                  shape='relaxed', fade=fade, lean=False)
    self.set(t0, t1, fade, h_nod=0.14)
    return self


def _w_offer_pie(self, t0=-1e9, dur=0.9, facing=1, t1=None):
    """Hold the pie in both hands and offer it forward (facing +1: toward screen right)."""
    s = self.height / 1000.0
    side = -1 if facing > 0 else 1
    name = 'pie' if facing > 0 else 'pie_r'
    ppc = self.height / (self.sp['m'] * 100.0)
    L = self._alen()
    self.hold_prop(name, side, -1e9, t1)
    def fn(P, t):
        u = ease_in_out(prog(t, t0, t0 + dur)) if t0 > -1e8 else 1.0
        w = 1.0 if t1 is None else 1.0 - ease_in_out(prog(t, t1, t1 + 0.5))
        self._arm(P, side, w, -18.0, lerp(0.62, 0.5, u) * L, lerp(0.42, 0.75, u) * L, 'grip', up=0.0, prop=name)
        P.lean += 0.06 * u * w
    self._add(-1e9, None, fn)
    self.reach_to(-1e9, -side, lambda t: (self.grip_point(t, side, name, False)[0] + facing * 25.0 * ppc, self.grip_point(t, side, name, False)[1] + 3 * ppc),
                  t1=t1, dur=0.01, contact='palm', shape='flat', lean=False)
    return self


def _w_lift_mask(self, t0, pell, dur=1.6, side=1):
    """Officer Reyes takes the mask by the crown and pulls it up and off (pell.mask_lift 0 -> 1); from then on it hangs
    from her hand ('hound_mask'). Returns the time the face is clear."""
    tg = t0 + 0.6; tc = t0 + dur
    hp = pell.height / 1000.0 * pell.sp['hh'] / 240.0
    pell._add(tg, None, lambda P, t: setattr(P, 'mask_lift', max(getattr(P, 'mask_lift', 0.0), ease_in_out(prog(t, tg, tc)))))
    def tgt(t):
        x, y = pell.where(t, 'crown', post=False)
        u = ease_in_out(prog(t, tg, tc))
        return x, y - 235.0 * hp * u + 18.0 * hp
    self.reach_to(t0, side, tgt, t1=tc, dur=0.6, z=40.0, contact='palm', shape='grip', fade=0.8, lean=True)
    self.hold_prop('hound_mask', side, tc, None)
    pell.set(tg, tc + 0.8, 0.3, h_nod=-0.12)
    self._ev(tg, 'rubber_peel', -6.0, 0.0)
    return tc


for _n, _f in (('walls_tilt', _w_tilt), ('doorway', _w_doorway), ('back_away', _w_back_away), ('tuck_blanket', _w_tuck),
               ('shush', _w_shush), ('crawl', _w_crawl), ('slide_panel', _w_slide_panel), ('cuffed', _w_cuffed),
               ('carry_hush', _w_carry_hush), ('shake_awake', _w_shake_awake), ('flip_switch', _w_flip_switch),
               ('read_note', _w_read_note), ('laugh', _w_laugh), ('sigh', _w_sigh), ('phone_to_mouth', _w_phone_to_mouth),
               ('offer_pie', _w_offer_pie), ('lift_mask', _w_lift_mask)):
    setattr(Acting, _n, _f)
Acting.sing = Acting.talk


def draw_carry_walls(pen, carrier, child, t, light=None, clight=None, blanket=True, bc='#7e9cc8'):
    """draw_carry_child plus the blanket he was wrapped in ('blanket and all'): it hangs from the child's waist over the
    carrier's arm, below the feet."""
    ax, ay = carry_anchor(carrier, t)
    child.place(0.0, 0.0)
    hx, hy = child.where(t, 'hip', post=False)
    child.place(ax - hx, ay - hy)
    Pc = child.at(t); Pcar = carrier.at(t)
    near = 1 if math.sin(Pcar.turn * PI / 2) <= 0 else -1
    draw(pen, carrier.who, carrier.x0, carrier.y0, carrier.height, Pcar, light=light, t=t)
    draw(pen, child.who, child.x0, child.y0, child.height, Pc, light=clight or light, t=t)
    if blanket:
        s = child.height / 1000.0
        bx, by = child.where(t, 'belly', post=False)
        f1 = child.where(t, 'foot_l', post=False); f2 = child.where(t, 'foot_r', post=False)
        fx, fy = (f1[0] + f2[0]) / 2, max(f1[1], f2[1])
        sw = 1 if fx > bx else -1
        pts = [(bx - sw * 150 * s, by - 20 * s), (bx + sw * 170 * s, by - 40 * s), (fx + sw * 150 * s, fy + 60 * s),
               (fx + sw * 40 * s, fy + 190 * s), (fx - sw * 60 * s, fy + 110 * s), (bx - sw * 190 * s, by + 260 * s)]
        bl = smooth(pts, True, 0.8)
        c = Ctx(pen, skia.Matrix(), _lw_for(child.height * 0.24))
        c.fill(bl, bc)
        c.grad(bl, bx, by, fx, fy + 150 * s, [(0, mix(bc, '#ffffff', 0.15), 255), (1, mix(bc, '#000000', 0.35), 255)])
        with c.clip(bl):
            c.line(_multi([poly([(bx - 400 * s + k * 90 * s, by - 100 * s), (bx - 200 * s + k * 90 * s, fy + 300 * s)], False) for k in range(10)]),
                   c.lw * 0.5, mix(bc, '#ffffff', 0.35), 120)
        c.line(smooth([(fx + sw * 150 * s, fy + 60 * s), (fx + sw * 60 * s, fy + 130 * s), (fx - sw * 20 * s, fy + 120 * s)], False),
               c.lw * 0.5, LINE, 150)
        c.line(bl, c.lw)
    draw_arm(pen, carrier.who, near, Pcar, x=carrier.x0, y_feet=carrier.y0, height=carrier.height, light=light, t=t)


# ====================================================================================================== self-test
def _selftest_walls():
    """The walls film's checks (python3 characters.py --selftest runs them after the older films')."""
    out = []
    set_render_size(480, 270)
    surf = skia.Surface(CFG.rw, CFG.rh); pen = Pen(surf.getCanvas()); surf.getCanvas().scale(CFG.k, CFG.k)
    for who in WALLS_CAST:
        for yaw in (0.0, 0.5, 1.0, 1.5, 2.0, -0.5):
            draw(pen, who, 960, 1000, 700, Pose(turn=yaw), t=0.3)
            draw_bust(pen, who, 960, 540, 0.6, Pose(h_turn=yaw), t=0.3)
    out.append('all %d walls ids draw in 6 views (full + bust)' % len(WALLS_CAST))
    # Dad and the doorway figure: the same height and (nearly) the same shoulder line
    assert abs(CAST['dad']['m'] - CAST['pell']['m']) < 0.03
    # the mask's mouth: the shush fingertip lands on it
    a = Acting('pell', seed=1, height=700).place(900, 1000); a.shush(0.0, None, side=1)
    mx, my = a.where(1.5, 'mouth'); tx, ty = a.where(1.5, 'hand_l')
    assert math.hypot(tx - mx, ty - my) < 90, ('shush', tx - mx, ty - my)
    out.append('shush: fingers %.0f px from the mask mouth' % math.hypot(tx - mx, ty - my))
    # the ears lag: a fast tilt leaves them behind, then they settle
    a = Acting('pell', seed=2, height=700).place(900, 1000); a.walls_tilt(1.0, None, 0.35)
    sw = [a.at(1.0 + k * 0.05).ear_sw for k in range(30)]
    assert min(sw) < -2.0 and abs(sw[-1]) < 1.0, ('ears', min(sw), sw[-1])
    out.append('ears swing %.1f deg behind a tilt and settle (%.2f)' % (min(sw), sw[-1]))
    # mask off: lift 1 draws his own face (no exception), the mask in Reyes' hand
    r = Acting('reyes', seed=3, height=640).place(700, 1000); p = Acting('pell', seed=4, height=700).place(900, 1000)
    tc = r.lift_mask(0.5, p)
    assert p.at(tc + 0.1).mask_lift > 0.99 and r.at(tc + 0.3).hl_prop == 'hound_mask'
    draw(pen, 'pell', 900, 1000, 700, p.at(tc - 0.5), t=tc - 0.5); draw(pen, 'reyes', 700, 1000, 640, r.at(tc + 0.4), t=tc + 0.4)
    out.append('lift_mask: off at %.2f s, in her hand after' % tc)
    # feet / knees on the floor while crawling
    a = Acting('pell', seed=5, height=700).place(400, 1000); a.crawl(0.5, 3.0, 0.0, 700.0)
    lows = []
    for t_ in np.arange(0.8, 2.9, 0.15):
        kl = a.where(t_, 'knee_l'); kr = a.where(t_, 'knee_r'); hl = a.where(t_, 'hand_l'); hr = a.where(t_, 'hand_r')
        lows.append(max(kl[1], kr[1])); lows.append(max(hl[1], hr[1]))
    assert max(abs(y - 1000) for y in lows) < 45, ('crawl contact', max(abs(y - 1000) for y in lows))
    out.append('crawl: a knee and a palm within %.0f px of the floor every sample' % max(abs(y - 1000) for y in lows))
    for o_ in out: print(o_)
    print('walls self-test ok')


_selftest_before_walls = _selftest


def _selftest():
    """python3 characters.py --selftest: the older films' checks, then the walls film's."""
    _selftest_before_walls()
    _selftest_walls()
