"""characters_obsession.py: the family and helpers of "If a Girl Is OBSESSED With Being Your Only Friend... DON'T WRITE
YOUR NAME": Adam (12, and 7 on the tape), Mom, Lina (7), Danny (12, and 7 on the tape), Mrs. Rahman, and the silent
background (Kofi, Sam, the caretaker, Danny's mom at her window, grown Adam's hands), with their props and acting clips.

Not imported on its own: characters.py runs it in its own namespace at the end of the module (exec, after
characters_evie.py), so everything here is part of `characters` (import characters as CH). Every id is a v3 cast entry on
the existing people rig (faces, lip sync, poses, look_at, reach_to, hands, props, kneel, sit, walk, run, climb); new here
are designs, outfits (work shirt, Lina's star pyjamas, overalls), Mrs. Rahman's hijab, Danny's pen, the chalk-sleeve /
red-knuckle / bracelet / tired states, props and a few clips. See OBSESSION_API and CAST.md.
"""
# NOTE: runs inside characters.py's globals (math, np, skia, Ctx, HeadMap, Body, CAST, Pose, Acting, _figure3 ... exist).

OBSESSION_API = """
Obsession film family ids (this film takes the plain names; the older films' ones live on as 'adam_ice', 'lina_ice',
'mom_buttons', 'sam_walls'):
  'adam' (12, grey hoodie)  'adam_night' (navy long-sleeve pyjamas, in bed)  'adam7' (7, on the tape: yellow tee)
  'mom' (40s, tied-back hair, blue work shirt)  'lina' (7, pigtails, oversized lilac star pyjamas)
  'danny' (12, round glasses, mustard jumper, chewed blue pen behind his right ear, bare wrist)
  'danny7' (7, on the tape: sky tee, glasses, the green-and-gold bracelet on his left wrist)
  'rahman' Mrs. Rahman (50s, navy hijab, long grey jacket, lanyard)  'kofi', 'sam' (Danny's new friends)
  'caretaker' (overalls, squints)  'danny_mom' (only ever a silhouette: draw_silhouette)  'adam_grown' (hands only: draw_arm)
Pose fields: ob_chalk 0..1 (hoodie sleeves chalk-white to the elbow), ob_tips 0..1 (chalk-white fingertips),
  ob_knuck 0..1 (red raw knuckles), ob_tired 0..1 (shadows under the eyes), ob_glow 0..1 (phone light up the face).
Expressions: adam_guarded, adam_lonely, adam_scared, adam_ashamed, adam_steady | mom_warm, mom_watchful, mom_tired,
  mom_firm | lina_earnest, lina_sing | danny_kind, danny_shy | rahman_calm, rahman_kind | squint_up.
Clips: phone_type, phone_taps, hold_hoodie, scrub, roller (+ roller_state / draw_roller), nod, sing_sway, look_down_at,
  duck, not_meeting (eyes off the other person) | everything else is the rig's own (see CAST.md beat map).
Free functions: draw_bucket, draw_shoebox, draw_roller, draw_silhouette, draw_lina_drawing; props in PROPS3: phone_ob,
  phone_mom, scrub_brush, bucket, hoodie_held, crayon, rule_card, rule_card_back, bracelet_real, fork, lina_drawing.
"""

# ====================================================================================================== keep old ids
for _o, _n in (('adam', 'adam_ice'), ('lina', 'lina_ice'), ('mom', 'mom_buttons'), ('sam', 'sam_walls')):
    if _o in CAST and _n not in CAST: CAST[_n] = CAST[_o]

POSE_DEFAULTS.update(ob_chalk=0.0, ob_tips=0.0, ob_knuck=0.0, ob_tired=0.0, ob_glow=0.0)
OB_CHALK = '#f1efe8'

# ====================================================================================================== outfits
_DOC_ROWS.update({'workshirt': _DOC_ROWS.get('flannel3', (18, 0.88, 4, 6, 6, 6, 6, 6)),
                  'overalls': (22, 0.9, 6, 10, 12, 14, 14, 12), 'pj_lina': (22, 0.9, 8, 12, 14, 16, 16, 12)})
_SLEEVES3.update({'workshirt': 'long', 'overalls': 'long', 'pj_lina': 'over'})


def _ob_front_pj_lina(c, sp, B, rows, P, det, t):
    """Lina's oversized lilac pyjamas: the pj front, then a scatter of small soft-yellow stars."""
    _FRONTS3['pj3'](c, sp, B, rows, P, det, t)
    if det < 1: return
    cl = sp['cloth']; b = sp['body']; st = []
    for k in range(11):
        x0 = (hash01(k, 811) - 0.5) * 1.5 * b['ch']
        y0 = B.y_sh + 30 + hash01(k, 812) * (B.y_hip - B.y_sh - 50)
        pts, v = _surf_poly(B, rows, [(x0, y0)], dz=1)
        if v < 0.15: continue
        x, y = pts[0]; r = 7.0 * B.p3(0, y0, 0)[2]
        st.append(poly([(x + r * (1.0 if j % 2 == 0 else 0.45) * math.cos(-PI / 2 + j * PI / 5),
                         y + r * (1.0 if j % 2 == 0 else 0.45) * math.sin(-PI / 2 + j * PI / 5)) for j in range(10)], True))
    if st: c.fill(_multi(st), cl.get('print_c', '#f2d37a'), 230)


def _ob_front_overalls(c, sp, B, rows, P, det, t):
    """The caretaker: a grey work shirt under navy bib overalls (bib, straps, brass buttons, a bib pocket, a pencil)."""
    _FRONTS3['flannel3'](c, sp, B, rows, P, det, t)
    cl = sp['cloth']; b = sp['body']
    bw = b['ch'] * 0.56; yt = B.y_ch - 34
    bib, v = _surf_poly(B, rows, [(-bw, yt), (bw, yt), (bw * 1.12, B.y_belt + 6), (-bw * 1.12, B.y_belt + 6)], dz=2)
    if v < -0.1: return
    bp = poly(bib, True)
    c.fill(bp, cl['bib']); c.grad(bp, bib[0][0], 0, bib[1][0], 0, [(0, cl['bib_sh'], 120), (0.5, cl['bib'], 0), (1, cl['bib_sh'], 150)])
    if det >= 1: c.texture(bp, 'fabric', 0.08, 0.6)
    c.line(bp, c.lw)
    for sd in (-1, 1):                                        # straps over the shoulders, brass buttons
        st, v2 = _surf_poly(B, rows, [(sd * bw * 0.86, yt + 2), (sd * b['sh'] * 0.62, B.y_sh - 6), (sd * b['sh'] * 0.5, B.y_sh - 30)], dz=2)
        if v2 > -0.1:
            c.line(smooth(st, False), 16.0 * B.p3(0, yt, 0)[2], LINE); c.line(smooth(st, False), 12.0 * B.p3(0, yt, 0)[2], cl['bib'])
        bt, v3 = _surf_poly(B, rows, [(sd * bw * 0.8, yt + 10)], dz=3)
        if v3 > 0.05:
            r = 6.0 * B.p3(0, yt, 0)[2]; c.fill(oval(bt[0][0], bt[0][1], r, r), '#c9a44a'); c.line(oval(bt[0][0], bt[0][1], r, r), c.lw * 0.5)
    if det >= 1:
        pk, v4 = _surf_poly(B, rows, [(-bw * 0.5, yt + 34), (bw * 0.5, yt + 34), (bw * 0.5, yt + 96), (-bw * 0.5, yt + 96)], dz=3)
        if v4 > 0.1:
            c.line(poly(pk, True), c.lw * 0.5, cl['bib_sh'], 220)
            pc, _ = _surf_poly(B, rows, [(bw * 0.3, yt + 12), (bw * 0.36, yt + 44)], dz=4)
            c.line(poly(pc, False), 6.0 * B.p3(0, yt, 0)[2], '#d9a440')


_front_labcoat3_ob_prev = _FRONTS3['labcoat3']


def _ob_front_labcoat3(c, sp, B, rows, P, det, t):
    _front_labcoat3_ob_prev(c, sp, B, rows, P, det, t)
    if not sp.get('lanyard'): return
    b = sp['body']; s = B.p3(0, B.y_ch, 0)[2]
    cy = B.y_ch + 62                                           # the cord from under the hijab to an ID card at the waist
    for sd in (-1, 1):
        q, v = _surf_poly(B, rows, [(sd * b['neck'] * 0.9, B.y_sh - 18), (sd * 16, B.y_ch + 10), (sd * 5, cy - 22)], dz=3)
        if v > -0.1:
            c.line(smooth(q, False), 7.0 * s, LINE); c.line(smooth(q, False), 4.6 * s, sp['cloth']['cord'])
    cd, v = _surf_poly(B, rows, [(-17, cy - 22), (17, cy - 22), (17, cy + 24), (-17, cy + 24)], dz=4)
    if v > 0.0:
        cp = poly(cd, True); c.fill(cp, '#f4f2ec'); c.line(cp, c.lw * 0.6)
        if det >= 1:
            ph, _ = _surf_poly(B, rows, [(-12, cy - 14), (-1, cy - 14), (-1, cy + 2), (-12, cy + 2)], dz=4)
            c.fill(poly(ph, True), '#8aa0b8')
            bd, _ = _surf_poly(B, rows, [(-17, cy + 12), (17, cy + 12), (17, cy + 24), (-17, cy + 24)], dz=4)
            c.fill(poly(bd, True), sp['cloth']['cord'])


_FRONTS3.update({'workshirt': _FRONTS3['flannel3'], 'overalls': _ob_front_overalls, 'pj_lina': _ob_front_pj_lina,
                 'labcoat3': _ob_front_labcoat3})
_stethoscope_ob_prev = _stethoscope


def _stethoscope(c, sp, B, rows, det):
    if sp.get('rahman'): return None
    return _stethoscope_ob_prev(c, sp, B, rows, det)


# ====================================================================================================== the cast
# One family face: Adam, Lina and Mom share warm light-olive skin, near-black brown hair, brown eyes, straight dark brows.
_FAM = dict(skin='#e4b994', skin_sh='#ba8b6b', skin_dp='#76503f', blush='#dc957e', lip='#ad6f62', iris_c='#4a3020',
            hair_c='#2a1f1a', brow_c='#211710')
_TEEN_BODY = dict(sh=96, ch=94, wa=86, hip=86, arm=(38, 32), leg=(43, 36), neck=31, hand=0.86, arm_k=0.92)
_KID7_BODY = dict(sh=86, ch=88, wa=84, hip=82, arm=(35, 30), leg=(39, 33), neck=28, hand=0.78, arm_k=0.88)
# Adam, 12: thin, a little hunched; messy near-black hair that falls into his eyes, thick straight brows that do the
# acting, brown eyes with a guarded low lid, a long face for his age; an oversized grey hoodie (white strings, kangaroo
# pocket), dark joggers, scuffed white trainers. Phone always within reach.
_ADAM = dict(hair='shaggy', sex='m', hh=204.0, child=True, m=1.52, head_ws=[0, 53, 77, 92, 97, 97, 91, 78, 57, 30, 0],
             eye_dx=40, eye_y=2, eye_r=19.5, iris_k=0.72, lid_rest=0.24, pupil=1.0, brow_th=10.0, nose_len=18,
             mouth_y=62, mouth_w=17, nose='button', ears=1.08, lips=0.05, bags=0.3, age=0.05, blink_rate=0.3,
             lashes=0.35, part=-1, body=dict(_TEEN_BODY), **_FAM)
_ADAM_CL = dict(top='#8b9099', top_sh='#646973', top_hi='#b0b5bd', hood='#8b9099', hood_sh='#646973', string='#f2efe8',
                trousers='#2e3544', trousers_sh='#1d2230', shoes='#e7e4dc', shoes_sh='#aeaaa1', socks='#e8e4dc', socks_sh='#b8b4aa')
CAST['adam'] = _v3cast(outfit='hoodie3', feet='shoes', chalk_ok=True, cloth=dict(_ADAM_CL), **_ADAM)
CAST['adam_night'] = _v3cast(outfit='pj3', feet='socks', cloth=dict(_ADAM_CL, top='#3e4a66', top_sh='#2a3349', top_hi='#5a6888',
                             trim='#2a3349', collar='#4a5878', collar_sh='#2a3349', trousers='#46506a', trousers_sh='#2f3649', print_c='#3e4a66', print_c2='#3e4a66'), **_ADAM)
# Adam at 7 on the tape: rounder, a big gap-free grin, the same hair cut short, a sunny yellow tee, light trousers.
_ADAM7 = dict(_ADAM, m=1.22, hh=236.0, head_ws=[0, 56, 82, 97, 102, 101, 95, 82, 60, 32, 0], eye_r=21.5, lid_rest=0.1,
              brow_th=8.0, nose_len=14, mouth_w=16, ears=1.12, bags=0.0, body=dict(_KID7_BODY))
CAST['adam7'] = _v3cast(outfit='tee_w', feet='shoes', cloth=dict(top='#f2c445', top_sh='#c99a2a', top_hi='#f8dc82', trim='#f8e6a8',
                        trousers='#c9b48e', trousers_sh='#a08a66', shoes='#5d86b8', shoes_sh='#3d5f8a'), **_ADAM7)
# Danny, 12: a head shorter than Adam, soft and round-faced; sandy-brown hair combed to the side, round dark-rimmed glasses,
# grey-blue eyes, pink cheeks; a mustard crew-neck jumper over a white collar, navy trousers; a chewed blue pen behind his
# right ear; a bare left wrist (the bracelet is gone).
_DANNY = dict(hair='side_short', sex='m', hh=210.0, child=True, m=1.45, head_ws=[0, 57, 82, 97, 102, 102, 96, 83, 61, 33, 0],
              eye_dx=40, eye_y=3, eye_r=19.0, iris_c='#5c7a96', iris_k=0.7, lid_rest=0.14, pupil=1.05, brow_th=7.0,
              nose_len=15, mouth_y=63, mouth_w=16, nose='button', ears=1.05, skin='#f2d0b8', skin_sh='#cca28a',
              skin_dp='#86605a', blush='#eba08e', lip='#c27c74', hair_c='#a07a4c', brow_c='#7d5a36', bags=0.1, age=0.0,
              blink_rate=0.35, lashes=0.3, part=1, glasses=True, pen_ear=True, body=dict(_TEEN_BODY, sh=92, ch=94, wa=90, hip=88))
CAST['danny'] = _v3cast(outfit='neat3', feet='shoes', cloth=dict(top='#d6a43a', top_sh='#a97c22', top_hi='#e8c46a', trim='#c9962e', collar='#f3f0e8',
                        collar_sh='#c9c3b6', button='#a97c22', trousers='#2c3550', trousers_sh='#1c2236', shoes='#4a3a30',
                        shoes_sh='#2e241e'), **_DANNY)
CAST['danny7'] = _v3cast(outfit='tee_w', feet='shoes', bracelet=1, cloth=dict(top='#8cc4e6', top_sh='#5f9cc4', top_hi='#b6dcf2',
                         trim='#e8f2f8', trousers='#d8cdb0', trousers_sh='#b0a585', shoes='#e6e2da', shoes_sh='#aaa69e'),
                         **dict(_DANNY, m=1.17, hh=240.0, head_ws=[0, 58, 84, 99, 104, 104, 97, 84, 62, 33, 0], eye_r=21.0,
                                pen_ear=False, nose_len=13, body=dict(_KID7_BODY)))
# Mom, 40s: warm, tired, sharp. Near-black hair pulled straight back into a low ponytail with a few loose strands, brown
# eyes with tired lower lids, straight brows that go firm; a dusty-blue long-sleeved work shirt (collar, buttons, two
# pockets) over a cream tee, charcoal trousers, flat shoes. Red raw knuckles on the scrubbing mornings (ob_knuck).
_MOM = dict(hair='pony', sex='f', hh=182.0, m=1.66, head_ws=[0, 49, 71, 87, 92, 90, 82, 66, 46, 24, 0], eye_dx=40, eye_y=-6,
            eye_r=18.0, lid_rest=0.3, brow_th=8.0, nose_len=21, mouth_w=20, lips=0.35, bags=0.6, age=0.45, lashes=0.8, part=1,
            body=dict(sh=102, ch=100, wa=86, hip=102, arm=(40, 32), leg=(45, 37), neck=32, hand=0.98), **_FAM)
CAST['mom'] = _v3cast(outfit='workshirt', feet='flats', cloth=dict(top='#6f8ea8', top_sh='#506d88', top_hi='#93adc2', tee='#ece4d4',
                      check='#6f8ea8', check_hi='#6f8ea8', trousers='#3a3a42', trousers_sh='#24242a', shoes='#4a3a30',
                      shoes_sh='#2e241e', socks='#3a3a42', socks_sh='#24242a'), **_MOM)
# Lina, 7: Adam's eyes in a round little face, two low pigtails tied with yellow bobbles, a straight fringe; oversized lilac
# pyjamas with soft-yellow stars, the sleeves over her hands, the legs pooling on her socks. Crayons, drawings.
CAST['lina'] = _v3cast(outfit='pj_lina', feet='socks', hair='pigtails', sex='f', hh=238.0, child=True, m=1.17,
                       head_ws=[0, 57, 84, 99, 104, 103, 96, 83, 61, 33, 0], eye_dx=40, eye_y=4, eye_r=22.0, iris_k=0.72,
                       lid_rest=0.06, pupil=1.08, brow_th=6.5, nose_len=12, mouth_y=64, mouth_w=15, nose='button', ears=1.1,
                       lips=0.1, bags=0.0, age=0.0, blink_rate=0.35, lashes=0.8, part=-1, body=dict(_KID7_BODY, sh=80, ch=84, wa=82, hip=80),
                       cloth=dict(top='#b9a6d8', top_sh='#8f7bb2', top_hi='#d6c8ec', trim='#a08cc4', collar='#cbbce4', collar_sh='#a08cc4', print_c='#f4d77c',
                                  trousers='#b9a6d8', trousers_sh='#8f7bb2', socks='#f2ede4', socks_sh='#c2bdb4', tie='#f2c94c',
                                  scrunchie='#f2c94c'), **dict(_FAM, hair_c='#33241d'))
# Mrs. Rahman, 50s, the counsellor: calm and unshockable. Warm brown skin, kind dark eyes with smile lines, a navy hijab
# framing her face (a lighter under-cap edge at the brow, the drape over neck and chest), a long grey jacket over a cream
# blouse, navy trousers, flat shoes, a teal lanyard with her ID card.
CAST['rahman'] = _v3cast(outfit='labcoat3', feet='flats', hair='hijab', rahman=True, lanyard=True, sex='f', hh=180.0, m=1.62,
                         head_ws=[0, 50, 73, 89, 95, 94, 87, 72, 51, 27, 0], eye_dx=40, eye_y=-4, eye_r=17.5, iris_c='#3a2418',
                         lid_rest=0.26, brow_th=8.0, nose_len=22, mouth_w=21, skin='#b07a57', skin_sh='#875a3e', skin_dp='#52331f',
                         blush='#b86e5c', lip='#8a4f46', lips=0.3, hair_c='#26345e', brow_c='#2a1c16', bags=0.45, age=0.65,
                         lashes=0.6, body=dict(sh=102, ch=104, wa=94, hip=110, arm=(41, 34), leg=(46, 38), neck=33, hand=0.98),
                         cloth=dict(top='#80848c', top_sh='#5e6269', top_hi='#a4a8af', shirt='#ece4d4', shirt_sh='#c6bca8',
                                    shirt_hi='#f6f0e4', collar='#80848c', pocket='#6c7078', button='#4a4d54', cord='#3a93a8', tie='#ece4d4', badge='#f4f2ec',
                                    trousers='#2e3650', trousers_sh='#1e2438', shoes='#2b2b30', shoes_sh='#18181c'))
# Kofi and Sam, Danny's new friends (background, silent): Kofi tall with a close crop and a steel-blue zip jacket; Sam
# smaller, black curls, an orange tee.
CAST['kofi'] = _v3cast(outfit='jacket3', feet='shoes', hair='crop', sex='m', hh=204.0, child=True, m=1.56,
                       head_ws=[0, 52, 76, 91, 96, 96, 90, 77, 56, 30, 0], eye_dx=40, eye_y=2, eye_r=19.0, iris_c='#2a1a12',
                       lid_rest=0.16, brow_th=8.0, nose_len=17, mouth_w=18, nose='button', skin='#6e4632', skin_sh='#4f2f20',
                       skin_dp='#2e1a10', blush='#7e4a38', lip='#5a3428', hair_c='#14100c', brow_c='#120c08', lashes=0.3,
                       body=dict(_TEEN_BODY), cloth=dict(top='#3f6e90', top_sh='#2a5070', top_hi='#6a92b0', collar='#2a5070', button='#c9ccd2', shirt='#e8e4da',
                       shirt_sh='#bcb6aa', trousers='#33302e', trousers_sh='#1f1d1c', shoes='#e2ded6', shoes_sh='#a8a49c'))
CAST['sam'] = _v3cast(outfit='tee_w', feet='shoes', hair='curly', sex='m', hh=206.0, child=True, m=1.49,
                      head_ws=[0, 54, 79, 94, 99, 99, 93, 80, 58, 31, 0], eye_dx=40, eye_y=3, eye_r=19.5, iris_c='#3a2618',
                      lid_rest=0.14, brow_th=8.0, nose_len=16, mouth_w=17, nose='button', skin='#d8a47c', skin_sh='#ac7858',
                      skin_dp='#6a4434', blush='#d08a72', lip='#9e6456', hair_c='#1c1614', brow_c='#181210', lashes=0.3,
                      body=dict(_TEEN_BODY), cloth=dict(top='#e2893c', top_sh='#b8682a', top_hi='#f0a868', trim='#f4e2cc',
                      trousers='#3c4a5e', trousers_sh='#27303e', shoes='#3a3a40', shoes_sh='#222226'))
# The caretaker (60s): grey hair, grey moustache, weathered kind face that squints; navy bib overalls over a grey work
# shirt, work boots.
CAST['caretaker'] = _v3cast(outfit='overalls', feet='boots', hair='thin', sex='m', hh=176.0, m=1.76,
                            head_ws=[0, 51, 75, 91, 97, 96, 89, 75, 54, 29, 0], eye_dx=41, eye_y=-6, eye_r=16.5,
                            iris_c='#5d6e7e', lid_rest=0.26, brow_th=10.0, nose_len=26, mouth_w=21, skin='#d29f80',
                            skin_sh='#a67558', skin_dp='#68463a', blush='#d48a78', lip='#9e6a60', moustache='#cfcac2',
                            hair_c='#c9c4bc', brow_c='#b9b3aa', bags=0.7, age=1.0,
                            body=dict(sh=118, ch=118, wa=112, hip=108, arm=(48, 40), leg=(52, 43), neck=42, hand=1.06),
                            cloth=dict(top='#8d9196', top_sh='#676b70', top_hi='#aeb2b6', tee='#d9d5cc', check='#8d9196',
                                       check_hi='#8d9196', bib='#2f4766', bib_sh='#1e3048', trousers='#2f4766',
                                       trousers_sh='#1e3048', shoes='#3a2c22', shoes_sh='#221a14'))
# Danny's mom: only ever the silhouette at her upstairs window, phone to her ear (draw_silhouette).
CAST['danny_mom'] = _v3cast(outfit='cardigan3', feet='flats', hair='bob', sex='f', hh=182.0, m=1.65, part=1, body=dict(_MOM['body']),
                            skin='#f0cdb4', skin_sh='#c89e86', skin_dp='#86605a', blush='#e0a090', lip='#b07870', hair_c='#8a6440', brow_c='#6a4a2e',
                            cloth=dict(top='#7a6a8c', top_sh='#5a4c6a', top_hi='#9a8aac', rib='#6a5a7c', button='#e8e2d6',
                                       blouse='#e8e2d6', blouse_sh='#c0b8aa', trousers='#3a3640', trousers_sh='#24222a'))
# Grown Adam (the coda): hands and sleeves only, a charcoal hoodie (his old grey one, grown up).
CAST['adam_grown'] = _v3cast(outfit='hoodie3', feet='socks', hair='shaggy', sex='m', hh=176.0, m=1.80, chalk_ok=True,
                             body=dict(sh=124, ch=118, wa=104, hip=104, arm=(50, 41), leg=(56, 46), neck=44, hand=1.04),
                             cloth=dict(_ADAM_CL, top='#454a53', top_sh='#2c3037', top_hi='#626872', hood='#454a53',
                                        hood_sh='#2c3037'), **_FAM)
OBSESSION_CAST = ('adam', 'adam_night', 'adam7', 'mom', 'lina', 'danny', 'danny7', 'rahman', 'kofi', 'sam', 'caretaker',
                  'danny_mom', 'adam_grown')

EXPR.update({
    'adam_guarded': dict(brow_in=0.3, brow_angry=0.12, m_press=0.35, smile=-0.08, eye_open=0.9, look_y=0.2, pupil=1.0),
    'adam_lonely': dict(brow_sad=0.6, brow_up=0.25, smile=0.05, eye_open=0.84, look_y=0.35, h_nod=0.08),
    'adam_scared': dict(wide=0.5, pupil=0.7, brow_sad=0.7, brow_up=0.55, m_open=0.1, smile=-0.35, tremble=0.25),
    'adam_ashamed': dict(brow_sad=0.9, brow_up=0.3, smile=-0.3, m_press=0.5, eye_open=0.78, look_y=0.6, h_nod=0.2, wet=0.4),
    'adam_steady': dict(brow_sad=0.18, m_press=0.25, smile=0.06, eye_open=1.0, pupil=1.05, brow_up=0.08),
    'mom_warm': dict(smile=0.5, squint=0.18, brow_up=0.12, brow_sad=0.12),
    'mom_watchful': dict(brow_in=0.18, brow_sad=0.22, smile=0.04, squint=0.1, m_press=0.2, lock=0.6, pupil=1.0),
    'mom_tired': dict(eye_open=0.78, brow_sad=0.4, smile=0.1, h_nod=0.05),
    'mom_firm': dict(brow_angry=0.25, m_press=0.45, squint=0.12, smile=0.0, pupil=0.95, lock=0.8),
    'lina_earnest': dict(brow_up=0.4, brow_sad=0.3, eye_open=1.06, smile=0.1, pupil=1.12),
    'lina_sing': dict(smile=0.55, m_open=0.25, squint=0.25, brow_up=0.3, pupil=1.05),
    'danny_kind': dict(smile=0.3, brow_sad=0.35, brow_up=0.2, eye_open=0.95),
    'danny_shy': dict(smile=0.12, brow_sad=0.45, brow_up=0.15, look_y=0.28, eye_open=0.95, h_nod=0.1),
    'rahman_calm': dict(smile=0.22, squint=0.2, brow_up=0.05),
    'rahman_kind': dict(smile=0.5, squint=0.3, brow_up=0.15, brow_sad=0.15),
    'squint_up': dict(squint=0.4, brow_in=0.45, brow_angry=0.1, smile=-0.05, m_side=0.25, eye_open=0.88),
})


# ====================================================================================================== the hijab
_HAIR3 = _HAIR3 + ('hijab',)
_EARLESS = _EARLESS + ('hijab',)
_hairline_ob_prev = _hairline


def _hairline(style, part):
    if style != 'hijab': return _hairline_ob_prev(style, part)
    return (lambda ph: np.interp(np.abs(ph), [0, 0.5, 0.95, 1.15, PI], [-70, -64, -36, 200, 200])), 14.0


def _hijab_window(hm):
    """The face opening, traced on the head surface (forehead under the cap edge, cheeks, round under the chin) and
    clamped to the head outline on the far side. None when the face is turned away."""
    u = np.linspace(-PI, PI, 64)
    phi = 1.0 * np.sin(u); y = 26.0 - 96.0 * np.cos(u)
    X, Y, V = _sph(hm, phi, y, 1.0)
    if V.max() < 0.08: return None
    xl, xr = hm.extent(np.maximum(hm.W(np.clip(y, -119.9, 119.9)), 1.0))
    st = float(hm.st)
    X = np.clip(X, xl + 3.0, xr - 3.0)
    if abs(st) > 0.05:                                         # the hidden cheek lies behind the face's front line
        X = np.where(V < 0.0, (xr - 3.0) if st > 0 else (xl + 3.0), X)
    win = _pts_path(X, Y, True, 0.9)
    if abs(st) > 0.15:
        # turned: open the window outward past the face's front line (forehead to chin), so the grown outline of the
        # scarf never covers the nose, lips or chin in 3/4 and profile
        yb = np.linspace(-60.0, 118.0, 14)
        Xf, Yf, Vf = _sph(hm, np.zeros_like(yb), yb, 0.0)
        sh = 90.0 * np.sign(st) * min(1.0, abs(st) * 1.6)
        bulge = np.sin(np.linspace(0.0, PI, len(yb))) ** 0.6       # a lens: tapers to the face at brow and chin
        pts = [(float(x), float(y_)) for x, y_ in zip(Xf, Yf)] + \
              [(float(x) + sh * b_, float(y_)) for x, y_, b_ in zip(Xf[::-1], Yf[::-1], bulge[::-1])]
        win = union(win, smooth(pts, True, 0.6))
    return win


def _hijab_drape(hm, grow=16.0):
    s = hm.st
    dx = 34.0 * s
    pts = [(-104 + dx, 30), (-122 + dx * 1.2, 118), (-168 + dx * 1.4, 236), (-176 + dx * 1.5, 300), (-60 + dx * 1.5, 318),
           (60 + dx * 1.5, 318), (176 + dx * 1.5, 300), (168 + dx * 1.4, 236), (122 + dx * 1.2, 118), (104 + dx, 30)]
    return union(_offset_path(hm.silhouette(), grow), smooth(pts, True, 0.7))


def _hijab_back(c, hm, sp, P, det):
    col = sp['hair_c']; sh = mix(col, '#000000', 0.38)
    back = union(_offset_path(hm.silhouette(), 15.0), smooth([(-110, 20), (-150, 150), (-190, 280), (0, 300), (190, 280),
                                                               (150, 150), (110, 20)], True, 0.7))
    c.fill(back, sh); c.line(back, c.lw)


def _hijab_front(c, hm, sp, P, det, t):
    col = sp['hair_c']; sh = mix(col, '#000000', 0.38); hi = mix(col, '#ffffff', 0.22)
    cover = _hijab_drape(hm)
    win = _hijab_window(hm)
    if win is not None: cover = minus(cover, win)
    c.fill(cover, col)
    with c.clip(cover):
        c.radial(None, -40 + 30 * hm.st, -90, 260, [(0, hi, 110), (0.45, col, 0), (1, sh, 210)], clip=False)
        c.grad(rect(-300, 120, 600, 220), 0, 120, 0, 330, [(0, sh, 0), (1, sh, 150)])
        if det >= 1:
            c.texture(cover, 'fabric', 0.07, 0.6)
            for sd in (-1, 1):                                    # soft folds from the temples down over the chest
                x0 = sd * 92 + 30 * hm.st
                c.line(smooth([(x0, 40), (x0 + sd * 26, 150), (x0 + sd * 50, 270)], False), c.lw * 0.45, sh, 150)
            c.line(smooth([(-70 + 34 * hm.st, 180), (0 + 40 * hm.st, 214), (70 + 34 * hm.st, 180)], False), c.lw * 0.4, sh, 120)
    if win is not None:
        with c.clip(inter(win, hm.silhouette())):                  # the fabric's shadow on the face edge, the under-cap band
            c.line(win, c.lw * 4.0, sp.get('skin_dp', '#553322'), 55)
        u = np.linspace(-0.95, 0.95, 18)
        X, Y, V = _sph(hm, np.sin(u) * 1.0, 26.0 - 102.0 * np.cos(u), 3.0)
        m = V > 0.0
        if m.sum() > 2: c.line(_pts_path(X[m], Y[m], False, 0.8), c.lw * 1.6, hi, 230)
    c.line(cover, c.lw)


# ====================================================================================================== head hooks
_hair3_back_ob_prev = _hair3_back


def _hair3_back(c, hm, sp, P, det, t):
    if sp.get('hair') == 'hijab': return _hijab_back(c, hm, sp, P, det)
    return _hair3_back_ob_prev(c, hm, sp, P, det, t)


_hair_region_ob_prev = _hair_region


def _hair_region(c, hm, sp, P, det, sil, t):
    if sp.get('hair') == 'hijab':
        _hijab_front(c, hm, sp, P, det, t); return None
    r = _hair_region_ob_prev(c, hm, sp, P, det, sil, t)
    if sp.get('pen_ear'): _danny_pen(c, hm, det)
    if getattr(P, 'ob_tired', 0.0) > 0.01 and hm.map1(0, 0)[2] > 0.0:
        for sd in (-1, 1):
            x, y, v = hm.map1(sd * sp['eye_dx'], sp['eye_y'] + 24.0)
            if v > 0.1: c.glow(x, y, 26.0 * hm.sx(sd * 40, 30), 9.0, '#6a4a5a', 70 * P.ob_tired)
    return r


def _danny_pen(c, hm, det):
    """The chewed blue pen tucked behind his right ear (character's right), tip forward over the temple."""
    X, Y, V = _sph(hm, np.array([-1.05, -1.55, -2.05]), np.array([-46.0, -30.0, -14.0]), 9.0)
    if V[1] < -0.15: return                                   # behind his head (he faces the other way)
    q = _pts_path(X, Y, False, 0.8)
    c.line(q, 13.0, LINE); c.line(q, 9.0, '#3f6fc6')
    c.line(_pts_path(X[:2] + 0.0, Y[:2] - 2.2, False, 0.8), 2.4, '#8fb0ee', 200)
    c.fill(oval(float(X[0]), float(Y[0]), 6.2, 6.2), '#9cb6e0'); c.line(oval(float(X[0]), float(Y[0]), 6.2, 6.2), c.lw * 0.5)
    if det >= 1:
        for k in (-1, 1): c.line(poly([(float(X[0]) + 2 * k, float(Y[0]) - 5), (float(X[0]) + 3 * k, float(Y[0]) + 4)], False), 1.2, '#5a7ab0')


_nape_cut_ob_prev = _nape_cut


def _nape_cut(hm, sp):
    return None if sp.get('hair') == 'hijab' else _nape_cut_ob_prev(hm, sp)


# ====================================================================================================== arm states
_draw_arm3_ob_prev = _draw_arm3


def _draw_arm3(c, sp, B, P, side, det, t, skin, sh, sleeve, sleeve_sh, light):
    r = _draw_arm3_ob_prev(c, sp, B, P, side, det, t, skin, sh, sleeve, sleeve_sh, light)
    ch, tp, kn, br = P.ob_chalk, P.ob_tips, P.ob_knuck, sp.get('bracelet') and side > 0
    if ch < 0.01 and tp < 0.01 and kn < 0.01 and not br: return r
    S, E, Wr = _arm_data(sp, B, P, side)
    e2 = B.p3(*E); w2 = B.p3(*Wr)
    dx, dy = w2[0] - e2[0], w2[1] - e2[1]
    d = math.hypot(dx, dy) or 1.0; ux, uy = dx / d, dy / d
    hl = 74.0 * sp['body']['hand'] * w2[2]
    if ch > 0.01 and sp.get('chalk_ok'):
        # chalk to the elbow: dusty white over the forearm sleeve, densest at the cuff, ragged at the elbow
        aw = sp['body']['arm'][1] * (1.05 if _SLEEVES3.get(sp['outfit']) == 'over' else 0.95) * e2[2]
        a0 = (e2[0] + dx * 0.06, e2[1] + dy * 0.06); a1 = (e2[0] + dx * 0.86, e2[1] + dy * 0.86)   # stops short of the hand
        tube = _tube([a0, a1], [aw * 1.15, aw * 1.3])
        c.fill(tube, OB_CHALK, 165 * ch)
        c.grad(tube, a0[0], a0[1], a1[0], a1[1], [(0, sleeve, 200 * ch), (0.35, OB_CHALK, 0), (1, '#ffffff', 70 * ch)])
        if det >= 1: c.texture(tube, 'grunge', 0.35 * ch, 0.5)
        if det >= 1:
            st = []
            for k in range(5):
                f0 = 0.15 + 0.15 * k; off = (hash01(k, 77 + side) - 0.5) * aw * 1.4
                p0 = (a0[0] + (a1[0] - a0[0]) * f0 - uy * off, a0[1] + (a1[1] - a0[1]) * f0 + ux * off)
                st.append(poly([p0, (p0[0] + ux * 26 * e2[2], p0[1] + uy * 26 * e2[2])], False))
            c.line(_multi(st), c.lw * 0.5, sleeve_sh, 90 * ch)
        c.line(tube, c.lw * 0.35, '#c9c6be', 160 * ch)
    if tp > 0.01 or kn > 0.01:
        s_ = w2[2]
        if tp > 0.01:
            tx, ty = w2[0] + ux * hl, w2[1] + uy * hl
            c.glow(tx, ty, 16 * s_, 12 * s_, OB_CHALK, 140 * tp)
        if kn > 0.01:
            kx, ky = w2[0] + ux * hl * 0.55, w2[1] + uy * hl * 0.55
            c.glow(kx, ky, 15 * s_, 10 * s_, '#d0675c', 120 * kn)
            if det >= 1:
                for k in (-1, 0, 1):
                    c.fill(oval(kx - uy * k * 7 * s_, ky + ux * k * 7 * s_, 3.0 * s_, 2.4 * s_), '#c25a52', 150 * kn)
    if br:
        # the green-and-gold woven bracelet round his left wrist
        bx, by = w2[0] - ux * 6 * w2[2], w2[1] - uy * 6 * w2[2]
        rw = sp['body']['arm'][1] * 1.05 * w2[2]
        ang = math.degrees(math.atan2(uy, ux))
        k = c.sub(bx, by, ang, 1.0)
        band = rrect(-5 * w2[2], -rw, 10 * w2[2], 2 * rw, 4 * w2[2])
        k.fill(band, '#3f8a4a'); k.line(band, c.lw * 0.5)
        if det >= 1:
            k.line(_multi([poly([(-4 * w2[2], -rw + j * rw * 0.4), (4 * w2[2], -rw + j * rw * 0.4 + rw * 0.2)], False)
                           for j in range(5)]), 1.6 * w2[2], '#e0b84a')
    return r


# ====================================================================================================== silhouette
def draw_silhouette(pen, who, x, y_feet, height, pose=None, col='#121722', alpha=255, t=0.0, rim=None, rim_side=1):
    """Draw a cast member as one flat dark shape (Danny's mom at her lit window): the figure rendered into a layer and
    filled with `col`; rim (a colour) adds a thin light edge on rim_side."""
    cv = pen.cv
    c4 = skia.Color4f.FromColor(skia.Color(int(col[1:3], 16), int(col[3:5], 16), int(col[5:7], 16), alpha))
    paint = skia.Paint(ColorFilter=skia.ColorFilters.Blend(c4.toColor(), skia.BlendMode.kSrcIn))
    if rim:
        r4 = skia.Color(int(rim[1:3], 16), int(rim[3:5], 16), int(rim[5:7], 16), 200)
        cv.saveLayer(None, skia.Paint(ColorFilter=skia.ColorFilters.Blend(r4, skia.BlendMode.kSrcIn)))
        draw(pen, who, x + 3 * rim_side, y_feet, height, pose, detail=0, t=t)
        cv.restore()
    cv.saveLayer(None, paint)
    draw(pen, who, x, y_feet, height, pose, detail=0, t=t)
    cv.restore()


# ====================================================================================================== props (cm, grip at 0,0)
def _p_phone_ob(c, det, t, P=None, case='#2a2e36', lit=False):
    body = rrect(-3.6, -7.4, 7.2, 14.8, 1.1)
    if lit: c.glow(0, 0, 9.0, 12.5, '#cfe0ff', 110)
    c.fill(body, case); c.fill(rrect(-3.6, -7.4, 7.2, 14.8, 1.1), '#ffffff', 18)
    if det >= 1:
        c.fill(rrect(-2.6, -6.6, 2.4, 2.4, 0.7), mix(case, '#000000', 0.4)); c.fill(oval(-1.4, -5.4, 0.7, 0.7), '#101218')
    c.line(body, c.lw)


def _p_bucket(c, det, t, P=None):
    """A galvanised bucket held by its wire handle (grip at the handle's top): grey ribbed metal, a brush across the rim."""
    body = poly([(-14, 8), (14, 8), (11.5, 34), (-11.5, 34)], True)
    c.line(smooth([(-14, 9), (-10, -2), (0, -4), (10, -2), (14, 9)], False), 1.0, '#6a6e74'); c.line(smooth([(-14, 9), (-10, -2), (0, -4), (10, -2), (14, 9)], False), 0.5, '#b8bcc2')
    c.fill(body, '#a9aeb5'); c.grad(body, -14, 0, 14, 0, [(0, '#d6dade', 200), (0.4, '#a9aeb5', 0), (1, '#6e737a', 220)])
    if det >= 1:
        c.line(_multi([poly([(-13.2, y), (13.2, y)], False) for y in (15, 26)]), 0.5, '#7c8187', 220)
    c.fill(oval(0, 8, 14, 2.4), '#8e949b'); c.line(oval(0, 8, 14, 2.4), c.lw * 0.6)
    c.line(body, c.lw)


def draw_bucket(pen, x, y_base, px_per_cm, water=True, brush=True, wet=0.0):
    """The bucket standing on a surface (x, y_base = the middle of its bottom edge): water inside, the scrub brush leaning
    on the rim; wet > 0 = a dark wet ring on the ground round it."""
    c = Ctx(pen, skia.Matrix(), _lw_for(px_per_cm * 26.0)).sub(x, y_base - 34 * px_per_cm, 0, px_per_cm)
    if wet > 0: c.fill(oval(0, 34, 24, 4.5), '#000000', 60 * wet)
    _p_bucket(c, 2, 0.0)
    if water: c.fill(oval(0, 9.5, 12.4, 1.9), '#8fa7b4', 230)
    if brush:
        k = c.sub(9, 4, -32, 1.0); _p_scrub_brush(k, 2, 0.0)


def _p_scrub_brush(c, det, t, P=None):
    """A wooden scrub brush, the block in the palm, stiff pale bristles below."""
    blk = rrect(-8, -2.4, 16, 4.0, 1.6)
    br = rect(-7.2, 1.6, 14.4, 2.6)
    c.fill(br, '#e2d6b4'); c.line(br, c.lw * 0.5)
    if det >= 1: c.line(_multi([poly([(-6.5 + k * 1.3, 1.8), (-6.5 + k * 1.3, 4.1)], False) for k in range(11)]), 0.25, '#a89a76')
    c.fill(blk, '#a8743e'); c.grad(blk, 0, -2.4, 0, 1.6, [(0, '#c99258', 200), (1, '#7a5228', 200)]); c.line(blk, c.lw)


def _p_hoodie_held(c, det, t, P=None):
    """Adam's grey hoodie held up by the shoulder seam: hood, body, the kangaroo pocket, both sleeves hanging, white with
    chalk from the cuffs to the elbows."""
    g, gs, ch = '#8b9099', '#646973', OB_CHALK
    body = smooth([(-3, -1), (-20, 4), (-22, 30), (-19, 56), (19, 56), (22, 30), (20, 4), (3, -1)], True, 0.5)
    for sd in (-1, 1):
        sl = smooth([(sd * 19, 5), (sd * 27, 26), (sd * 26, 52), (sd * 20, 54), (sd * 18, 28)], True, 0.5)
        c.fill(sl, g); c.line(sl, c.lw)
        cuff = smooth([(sd * 27.5, 30), (sd * 26.5, 53), (sd * 19.5, 55), (sd * 18.5, 32)], True, 0.5)
        c.fill(cuff, ch, 235); c.line(cuff, c.lw * 0.4, '#c6c2b8')
    c.fill(body, g); c.grad(body, -22, 0, 22, 0, [(0, gs, 150), (0.5, g, 0), (1, gs, 170)])
    hood = smooth([(-9, 2), (-6, -6), (6, -6), (9, 2), (0, 6)], True, 0.5)
    c.fill(hood, gs); c.line(hood, c.lw)
    if det >= 1:
        c.line(smooth([(-11, 38), (-8, 30), (8, 30), (11, 38)], False), c.lw * 0.5, gs)
        for sd in (-1, 1): c.line(poly([(sd * 3, 5), (sd * 3.5, 18)], False), 0.6, '#f2efe8')
    c.line(body, c.lw)


def _p_crayon(c, det, t, P=None, col='#e0a63a'):
    b = rrect(-0.55, -4.5, 1.1, 8.0, 0.4)
    c.fill(b, col); c.fill(poly([(-0.55, -4.5), (0.55, -4.5), (0, -5.6)], True), col)
    c.fill(rect(-0.56, -1.5, 1.12, 3.2), '#ffffff', 120); c.line(b, c.lw * 0.6)


def _p_rule_card(c, det, t, P=None, back=False):
    """Danny's mom's card: cream, seven rules in purple handwriting, a name at the top scribbled out in blue pen."""
    cd = rrect(-5.2, -7.4, 10.4, 14.8, 0.5)
    c.fill(cd, '#f3ecdc'); c.line(cd, c.lw * 0.7)
    if back or det < 1: return
    sc = []
    for k in range(9):
        y = -3.8 + k * 1.35; w_ = 7.6 - 2.4 * hash01(k, 31)
        sc.append(smooth([(-4.2 + 0.4 * j * w_ / 4, y + 0.22 * math.sin(j * 2.1 + k)) for j in range(5)], False))
    c.line(_multi(sc), 0.32, '#6e4a9e', 230)
    c.line(smooth([(-2.6, -5.9), (-1.6, -6.4), (-0.6, -5.8), (0.6, -6.5), (1.6, -5.7), (2.6, -6.3), (1.9, -5.9), (-2.2, -6.1)], False), 0.55, '#2f5fb8', 240)


def _p_bracelet_real(c, det, t, P=None):
    """The real green-and-gold woven bracelet (no chalk)."""
    ring = oval(0, 3.4, 3.2, 3.6)
    c.line(ring, 1.5, LINE); c.line(ring, 1.1, '#3f8a4a')
    if det >= 1:
        d = [poly([(3.2 * math.cos(2 * PI * k / 14) - 0.35, 3.4 + 3.6 * math.sin(2 * PI * k / 14) - 0.35),
                   (3.2 * math.cos(2 * PI * k / 14) + 0.35, 3.4 + 3.6 * math.sin(2 * PI * k / 14) + 0.35)], False) for k in range(14)]
        c.line(_multi(d), 0.35, '#e0b84a', 255)


def _p_fork(c, det, t, P=None):
    c.line(poly([(0, 6), (0, -6)], False), 0.9, LINE); c.line(poly([(0, 6), (0, -6)], False), 0.6, '#c8ccd2')
    for k in (-0.6, -0.2, 0.2, 0.6): c.line(poly([(k, -6), (k, -9)], False), 0.3, '#9aa0a8')


def draw_lina_drawing(c, w=21.0):
    """Lina's crayon drawing of 'us' on paper (cm units at the centre of Ctx c): a tall boy in grey with a phone, a little
    girl with pigtails holding his hand, a yellow sun, green scribble grass, LINA in the corner."""
    h = w * 0.72
    pg = rect(-w / 2, -h / 2, w, h)
    c.fill(pg, '#fbf8f0'); c.line(pg, c.lw * 0.6)
    c.line(smooth([(-w / 2 + 0.5, h / 2 - 1.2 + 0.3 * math.sin(k)) for k in range(0)] or [(-w / 2 + 0.5, h / 2 - 1.4), (w / 2 - 0.5, h / 2 - 1.1)], False), 0.9, '#58a54a')
    c.fill(oval(w / 2 - 3, -h / 2 + 2.6, 1.6, 1.6), '#f2c94c')
    for k in range(8):
        a = 2 * PI * k / 8
        c.line(poly([(w / 2 - 3 + 2.1 * math.cos(a), -h / 2 + 2.6 + 2.1 * math.sin(a)), (w / 2 - 3 + 2.9 * math.cos(a), -h / 2 + 2.6 + 2.9 * math.sin(a))], False), 0.25, '#e0a63a')
    for x0, hh, col_, pig in ((-3.2, 8.0, '#8b9099', False), (1.6, 5.4, '#b9a6d8', True)):
        yb = h / 2 - 1.6
        c.line(oval(x0, yb - hh, 1.3, 1.4), 0.3, '#3a2a22')
        c.fill(poly([(x0 - 1.4, yb - hh + 1.6), (x0 + 1.4, yb - hh + 1.6), (x0 + 1.8, yb - hh * 0.4), (x0 - 1.8, yb - hh * 0.4)], True), col_, 220)
        c.line(_multi([poly([(x0 - 0.6, yb - hh * 0.4), (x0 - 0.9, yb)], False), poly([(x0 + 0.6, yb - hh * 0.4), (x0 + 0.9, yb)], False)]), 0.3, '#3a2a22')
        if pig: c.line(_multi([poly([(x0 - 1.3, yb - hh), (x0 - 2.2, yb - hh + 1.2)], False), poly([(x0 + 1.3, yb - hh), (x0 + 2.2, yb - hh + 1.2)], False)]), 0.35, '#3a2a22')
    c.line(smooth([(-1.4, h / 2 - 1.6 - 4.4), (-0.2, h / 2 - 1.6 - 4.0), (0.2, h / 2 - 1.6 - 3.2)], False), 0.3, '#3a2a22')
    text_ = 'LINA'
    for k, ch in enumerate(text_):
        x0 = -w / 2 + 1.2 + k * 1.1; y0 = -h / 2 + 1.0
        c.line(poly([(x0, y0), (x0 + 0.3, y0 + 1.2)], False), 0.3, '#6e4a9e')


def _p_lina_drawing(c, det, t, P=None):
    draw_lina_drawing(c.sub(0, -6.0, 0, 1.0))


PROPS3.update({
    'phone_ob': (_p_phone_ob, 'upright', (0.0, 0.0)),
    'phone_ob_lit': (lambda c, d, t, P=None: _p_phone_ob(c, d, t, P, lit=True), 'upright', (0.0, 0.0)),
    'phone_mom': (lambda c, d, t, P=None: _p_phone_ob(c, d, t, P, case='#3f6f74'), 'upright', (0.0, 0.0)),
    'scrub_brush': (_p_scrub_brush, 'upright', (0.0, 0.0)),
    'bucket': (_p_bucket, 'hang', (0.0, 0.0)),
    'hoodie_held': (_p_hoodie_held, 'hang', (0.0, 0.0)),
    'crayon': (_p_crayon, 'grip', (0.0, 0.0)),
    'rule_card': (_p_rule_card, 'upright', (0.0, 0.0)),
    'rule_card_back': (lambda c, d, t, P=None: _p_rule_card(c, d, t, P, True), 'upright', (0.0, 0.0)),
    'bracelet_real': (_p_bracelet_real, 'hang', (0.0, 0.0)),
    'fork': (_p_fork, 'grip', (0.0, 0.0)),
    'lina_drawing': (_p_lina_drawing, 'upright', (0.0, 0.0)),
})


def draw_shoebox(pen, x, y_base, px_per_cm, open_=0.0, gifts=True):
    """The shoebox Danny slides over (x, y_base = the middle of its bottom on the table), seen from a little above:
    pale blue card, lid on (open_ 0) or set back (1) showing the gifts and the real bracelet on top."""
    c = Ctx(pen, skia.Matrix(), _lw_for(px_per_cm * 30.0)).sub(x, y_base, 0, px_per_cm)
    w, d, h = 30.0, 9.0, 11.0
    front = rect(-w / 2, -h, w, h); top = poly([(-w / 2, -h), (w / 2, -h), (w / 2 - 3, -h - d), (-w / 2 + 3, -h - d)], True)
    c.fill(front, '#9cbad0'); c.line(front, c.lw)
    if open_ < 0.5:
        lid = rect(-w / 2 - 0.6, -h - 0.6, w + 1.2, 3.2); c.fill(top, '#b4cde0'); c.line(top, c.lw); c.fill(lid, '#86a6c0'); c.line(lid, c.lw)
    else:
        c.fill(top, '#5a4e46'); c.line(top, c.lw)
        if gifts:
            for k, (gx, gc) in enumerate(((-8, '#e7c96a'), (-1, '#c95f8a'), (6, '#6aa0d8'))):
                c.fill(rrect(gx - 3, -h - 5.5 + k * 0.6, 6, 3.4, 0.6), gc); c.line(rrect(gx - 3, -h - 5.5 + k * 0.6, 6, 3.4, 0.6), c.lw * 0.5)
            k2 = c.sub(2, -h - 6.2, 0, 1.0)
            k2.line(oval(0, 0, 3.6, 1.6), 1.6, LINE); k2.line(oval(0, 0, 3.6, 1.6), 1.1, '#3f8a4a')
            k2.line(_multi([poly([(3.6 * math.cos(a) - 0.3, 1.6 * math.sin(a)), (3.6 * math.cos(a) + 0.3, 1.6 * math.sin(a) + 0.3)], False)
                            for a in np.linspace(0, 2 * PI, 12, endpoint=False)]), 0.35, '#e0b84a')
        lid = poly([(w / 2 + 1, -h - d - 1), (w / 2 + 6, -h - d - 9), (-w / 2 + 6, -h - d - 9), (-w / 2 + 1, -h - d - 1)], True)
        c.fill(lid, '#86a6c0'); c.line(lid, c.lw)


# ====================================================================================================== clips
def _ob_face_dir(self, t):
    """+1 / -1: which screen side the body faces at t (0 = square to the lens)."""
    return math.sin(self.at(t).turn * PI / 2) if t > -1e8 else 0.0


def _ob_phone_point(self, t0, dist=24.0, drop=12.0):
    p = _ppc(self); fac = _ob_face_dir(self, t0 - 0.01)
    def ph(t):
        x, y = self.where(t, 'chest')
        return x + fac * dist * p, y + drop * p
    return ph


def _ob_phone_type(self, t0, t1, side=-1, rate=4.5, prop='phone_ob', glow=True, gain=-24.0, dist=22.0, drop=12.0, look=True):
    """Typing on the phone: held at chest height in front of him in one hand (side), the other hand's thumb tapping on
    the screen, head bowed to it; ob_glow lights the face (pair with light=dict(under='#cfe0ff', under_a=..) at night).
    'phone_tap' events. Works standing, seated (a.seated / sit_on first) and sitting up in bed."""
    p = _ppc(self); ph = _ob_phone_point(self, t0, dist, drop)
    self.reach_to(t0 - 0.3, side, ph, t1=t1, dur=0.45, z=30.0, contact='grip', shape='grip', prop=prop)
    self.hold_prop(prop, side, t0 - 0.3, t1 + 0.5)
    def tap(t):
        x, y = ph(t); k = max(0.0, math.sin(2 * PI * (t - t0) * rate * 0.5)) ** 2
        return x - side * 1.5 * p, y - 2.5 * p + 1.2 * p * k
    self.reach_to(t0, -side, tap, t1=t1, dur=0.4, z=34.0, contact='tips', shape='point', fade=0.35)
    if look: self.look_at(t0 - 0.3, ph, t1=t1, dur=0.35)
    if glow:
        def fn(P, t): P.ob_glow = max(P.ob_glow, 0.8 * _env(t, t0 - 0.3, t1, 0.3, 0.4))
        self._add(t0 - 0.3, t1 + 0.4, fn)
    evs, tt = [], t0 + 0.35
    while tt < t1:
        evs.append(self._ev(tt, 'phone_tap', gain + 3.0 * (hash01(int(tt * 100), 5) - 0.5))); tt += (1.0 + 0.5 * hash01(int(tt * 37), 6)) / rate
    return evs


def _ob_phone_taps(self, taps, side=1, t0=None, t1=None, prop='phone_mom', dist=20.0, drop=6.0, gain=-18.0):
    """Mom taps Save, then Block, then Report: the phone held up in the other hand, eyes on it; the index finger of `side`
    hovers and taps at each time in `taps`. 'phone_tap' events."""
    t0 = taps[0] - 0.8 if t0 is None else t0; t1 = taps[-1] + 0.8 if t1 is None else t1
    p = _ppc(self); ph = _ob_phone_point(self, t0, dist, drop)
    self.reach_to(t0, -side, ph, t1=t1, dur=0.45, z=30.0, contact='grip', shape='grip', prop=prop)
    self.hold_prop(prop, -side, t0, t1 + 0.5)
    def fin(t):
        x, y = ph(t); k = 0.0
        for tt in taps: k = max(k, 1.0 - min(1.0, abs(t - tt) / 0.16))
        return x + side * 1.0 * p, y - 1.5 * p - 3.0 * p * (1.0 - k)
    self.reach_to(t0 + 0.2, side, fin, t1=t1, dur=0.4, z=36.0, contact='tips', shape='point', fade=0.35)
    self.look_at(t0, ph, t1=t1, dur=0.35)
    return [self._ev(tt, 'phone_tap', gain) for tt in taps]


def _ob_hold_hoodie(self, t0, t1=None, side=1, dur=0.6):
    """'Mom held up my grey hoodie': one hand lifts it by the shoulder seam to head height out in front of her, the
    sleeves (chalk-white to the elbow) hanging toward him. Returns [cloth_rustle]."""
    p = _ppc(self); fac = _ob_face_dir(self, t0 - 0.01) or (1.0 if side > 0 else -1.0)
    def tg(t):
        x, y = self.where(t, 'shoulder_l' if side > 0 else 'shoulder_r')
        return x + fac * 42.0 * p, y - 14.0 * p
    self.reach_to(t0, side, tg, t1=t1, dur=dur, z=40.0, contact='grip', shape='grip', prop='hoodie_held')
    self.hold_prop('hoodie_held', side, t0, t1)
    return [self._ev(t0 + dur * 0.5, 'cloth_rustle', -20.0, kind='grab')]


def _ob_scrub(self, t0, t1, target, side=1, rate=1.6, amp=13.0, kneel=True, prop='scrub_brush', gain=-20.0, other=True):
    """Scrub the path / the hall floor at `target` (a ground point; callables work): kneel (knees=1), the brush in the
    `side` hand going back and forth along the ground, the other hand flat on the ground for support, head down on the
    work. 'brush_scrub' events, one per stroke."""
    p = _ppc(self)
    if kneel: self.kneel_down(t0 - 0.9, dur=0.9, knees=1, t1=t1 + 0.2)
    def tg(t):
        x, y = _target_xy(target, t); w = _env(t, t0, t1, 0.4, 0.4)
        return x + amp * p * w * math.sin(2 * PI * rate * (t - t0)), y - 2.0 * p
    self.reach_to(t0 - 0.4, side, tg, t1=t1, dur=0.45, z=20.0, contact='palm', shape='grip', prop=prop)
    self.hold_prop(prop, side, t0 - 0.4, t1)
    if other:
        def sup(t):
            x, y = _target_xy(target, t0)
            return x - (1 if side > 0 else -1) * _ob_face_dir(self, t0 - 0.01) * 0.0 - 16.0 * p * (1 if side > 0 else -1), y
        self.reach_to(t0 - 0.3, -side, sup, t1=t1, dur=0.5, z=10.0, contact='palm', shape='flat')
    self.look_at(t0 - 0.4, target, t1=t1, dur=0.4)
    evs, tt = [], t0 + 0.25 / rate
    while tt < t1 - 0.1:
        evs.append(self._ev(tt, 'brush_scrub', gain + 2.0 * (hash01(int(tt * 50), 3) - 0.5))); tt += 0.5 / rate
    return evs


def _ob_roller(self, t0, t1, ground, stroke=50.0, rate=0.4, pole=170.0, gain=-22.0):
    """The caretaker paints the square: both hands on the roller pole (top hand at its end, the other 40 cm down), the
    roller on the ground at `ground` running +-stroke/2 cm along x, a little lean into each push. a.roller_state(t) ->
    (roller centre, pole top) for draw_roller. 'paint_roll' events, one per pass."""
    p = _ppc(self)
    gx, gy = _target_xy(ground, t0)
    def head(t):
        w = _env(t, t0, t1, 0.5, 0.5)
        return gx + 0.5 * stroke * p * w * math.sin(2 * PI * rate * (t - t0)), gy
    def top(t):
        hx, hy = head(t); cx, cy = self.where(t, 'chest')
        dx, dy = cx - hx, cy - hy; d = math.hypot(dx, dy) or 1.0
        L = pole * p
        return hx + dx / d * L, hy + dy / d * L
    def lower(t):
        hx, hy = head(t); tx, ty = top(t); f = 1.0 - 40.0 / pole
        return hx + (tx - hx) * f, hy + (ty - hy) * f
    self._roller = (head, top)
    self.reach_to(t0 - 0.5, 1, top, t1=None, dur=0.5, z=30.0, contact='grip', shape='grip')     # he keeps hold of
    self.reach_to(t0 - 0.5, -1, lower, t1=None, dur=0.5, z=40.0, contact='grip', shape='grip')   # the pole after
    def fn(P, t):
        w = _env(t, t0, t1, 0.5, 0.5)
        P.lean += 0.04 * w * math.sin(2 * PI * rate * (t - t0)); P.h_nod += 0.18 * w
    self._add(t0 - 0.5, t1 + 0.5, fn)
    evs, tt = [], t0 + 0.25 / rate
    while tt < t1:
        evs.append(self._ev(tt, 'paint_roll', gain)); tt += 0.5 / rate
    return evs


def _ob_roller_state(self, t):
    head, top = self._roller
    return head(t), top(t)


def draw_roller(pen, a, t, px_per_cm, paint='#d9d4c6'):
    """The roller (a cream paint sleeve on a wire frame) and its long pole, from a.roller_state(t)."""
    (hx, hy), (tx, ty) = a.roller_state(t)
    c = Ctx(pen, skia.Matrix(), _lw_for(px_per_cm * 40.0))
    lw = 3.0 * px_per_cm
    c.line(poly([(hx, hy - 6 * px_per_cm), (tx, ty)], False), lw + 2.0, LINE); c.line(poly([(hx, hy - 6 * px_per_cm), (tx, ty)], False), lw, '#c9a46a')
    r = rrect(hx - 12 * px_per_cm, hy - 6 * px_per_cm, 24 * px_per_cm, 6 * px_per_cm, 3 * px_per_cm)
    c.fill(r, paint); c.line(r, c.lw)


def _ob_nod(self, t0, n=1, amount=1.0, dur=0.55):
    """A small, calm nod (Mrs. Rahman in her doorway, listening in her chair)."""
    def fn(P, t):
        for k in range(n):
            u = prog(t, t0 + k * dur, t0 + (k + 1) * dur)
            if 0 < u < 1: P.h_nod += amount * 0.2 * math.sin(PI * u)
    self._add(t0, t0 + n * dur + 0.01, fn)
    return self


def _ob_sing_sway(self, t0, t1, beat=0.42, amount=1.0, smile=0.5):
    """Singing (the tape, Lina at dawn): the head sways on the beat, a little bounce, a smile; pair with talk on the sung
    line for the mouth."""
    def fn(P, t):
        w = _env(t, t0, t1, 0.4, 0.4) * amount
        ph = 2 * PI * (t - t0) / (2 * beat)
        P.tilt += 4.5 * w * math.sin(ph); P.h_turn += 0.05 * w * math.sin(ph); P.dy += -3.0 * w * abs(math.sin(ph))
        P.smile = max(P.smile, smile * w)
    self._add(t0, t1 + 0.4, fn)
    return self


def _ob_look_down_at(self, t0, target, t1=None, lean=0.6, dur=0.5):
    """Look down from a window at `target` (a point below): head bowed, a lean toward the glass."""
    self.look_at(t0, target, t1=t1, dur=dur, body=0.15)
    def fn(P, t): P.lean += 0.1 * lean * _env(t, t0, t1, dur, 0.5)
    self._add(t0, (t1 if t1 is not None else t0 + 1e6) + 0.5, fn)
    return self


def _ob_duck(self, t0, t1=None, dur=0.25):
    """Duck away from the window: a fast drop into a crouch, head down, a flinch on the way."""
    self.crouch(t0, amount=1.7, t1=t1, dur=dur, fade=0.3)
    self.head_down(t0, t1, amount=0.8)
    return self


def _ob_not_meeting(self, t0, other, t1=None, side=1, dur=0.35):
    """Danny handing over the card: eyes off the other person (down and to one side of them), the head only half turned."""
    p = _ppc(self)
    def tg(t):
        x, y = _target_xy(other if not isinstance(other, Acting) else (other, 'chest'), t)
        return x + side * 30.0 * p, y + 60.0 * p
    self.look_at(t0, tg, t1=t1, dur=dur, head=0.6)
    return self


Acting.phone_type = _ob_phone_type
Acting.phone_taps = _ob_phone_taps
Acting.hold_hoodie = _ob_hold_hoodie
Acting.scrub = _ob_scrub
Acting.roller = _ob_roller
Acting.roller_state = _ob_roller_state
Acting.nod = _ob_nod
Acting.sing_sway = _ob_sing_sway
Acting.look_down_at = _ob_look_down_at
Acting.duck = _ob_duck
Acting.not_meeting = _ob_not_meeting
