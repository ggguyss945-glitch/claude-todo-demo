"""characters_doctor.py: the cast of "If Your Doctor Calls At 3 AM... DON'T ASK WHAT THEY FOUND" and its staging tools.

This file is not imported on its own: characters.py runs it in its own namespace at the end of the module (exec, after
characters_bunny.py), so everything here is part of `characters` (import characters as CH; CH.draw(...), CH.Acting(...))
and can use and extend every helper above (Ctx, HeadMap, Body, _ik, _tube, _draw_hand, _v3cast, Acting, PropTrack...).
The older casts are unchanged. See DOCTOR_API below and CAST.md for the beat map.
"""
# NOTE: runs inside characters.py's globals (math, np, skia, Ctx, HeadMap, Body, CAST, Pose, Acting, ... are defined).

DOCTOR_API = """
Doctor film cast ids (this film's cast has its own ids; the Bunnyman film's 'mom', 'narrator', 'grandma'... are unchanged):
  'later'            Doctor Later, the Waiting Man: an impossibly thin black creature folded on a small chair, knees above
                     his head, a tall pointed head wrapped round and round in old yellow medical tape (one thin gap, two
                     pale patient eyes), a white coat gone grey, a clipboard with no paper, a click pen. Never lip-syncs.
  'ruth'             Grandma Ruth, 70s. 'ruth79': Ruth at 40, 1979 (housecoat). 'ruth_sick': Ruth at sunrise, pale.
  'grandpa79'        Grandpa, about 50, 1979, brown cardigan. 'grandpa_ghost': grey and still in the last row.
  'milo'             Milo, 7, dinosaur pajamas. 'milo_jeans': the dinosaur jeans (falling off him). 'milo22': Milo at 22.
  'narr14'           The narrator at 14 ("I", gender never said). 'narr29': the narrator at 29, a pediatrician on nights.
  'halverson'        Doctor Anna Halverson, pediatrician, 40s (coffee-stained blue scrubs, dinosaur stickers on her badge).
  'halverson_rain'   The same at 3:40 AM: a raincoat over the blue scrubs, hair soaked flat, badge crooked.
  'mom_rn'           Mom, 40s, night-shift nurse (scrubs, lanyard, watch).
  'er_nurse', 'er_doctor', 'chest_man', 'medic', 'medic2', 'cardio' (the cardiologist with a coffee)
  'ghost_chest', 'ghost_side', 'ghost_teen', 'ghost_girl'   the waiting room's grey, still people.
Doctor Later acting (Acting('later', ...)): perch(seat_y, kind), later_hands(t0, left, right), click_pen(times),
  write_scratch(t0, t1), tilt_head(t0, deg), look_at (slow), reach_far / reach_to(t0, side, target), tear_ticket(t0, side,
  slot, text, offer_to=), offer(t0, side, target), take_wrist(t0, side, other, other_side), count(t), loosen_tape(t0, t1,
  frm, to), faces(keys), flinch_light(t), bend_to_roof(roof_y). Helpers: draw_bust('later', ...), later_bust_place,
  draw_later_arm, draw_later_far, later_point, chair_rock(t, t0).
People acting added here: receiver_to_ear(t0, t1, side, tilt_out, toward=), tap, pull_cord, strike_match, slide_under_door,
  write_marker, dial, take_pulse, carry (+ draw_carry_child), drive, rock, breathe_fast, drink, gone, glasses, sag, hold_up,
  hand_on, ticket_hold. Helpers: receiver_cord_end, draw_coil_cord, draw_wheelchair, draw_steering_wheel, carry_anchor.
"""

import bisect as _bisect3

# ====================================================================================================== DOCTOR LATER
# The rig works in centimetres in his own body frame: x = his left (+), y = down (floor 0, so heights are negative),
# z = his front. The origin is the floor point under the middle of the seat he is folded on (a.place(chair_x, floor_y)).
# He is 2.9 m standing (he never stands while watched); the cone of his head adds about half a metre on top.
_DL_M = 2.9
_DLU = 1000.0 / (_DL_M * 100.0)              # body units per cm (draw() works in body units: 1000 = his standing height)
_DL_L = dict(thigh=90.0, shin=104.0, foot=26.0, upper=58.0, fore=56.0, palm=9.0)
_DL_D = 640.0                                # mild perspective (cm) about the middle of the figure
_DL_ELEV = 0.11                              # the camera looks a little down on him: hands flat on the carpet read
_DL_BLACK, _DL_BLACK_SH, _DL_BLACK_HI = '#17171c', '#0a0a0d', '#474b57'
_DL_COAT = dict(c='#8c8a82', sh='#5f5d57', dp='#42413c', hi='#adab a1'.replace(' ', ''), grime='#5a5242', line='#1a1b20')
_DL_TAPE = ('#e8ddb2', '#ddd09e', '#efe6c4', '#d4c48e', '#e4d7a8', '#d9ca96', '#cfbd84')
_DL_TAPE_EDGE = '#8c7a4e'

POSE_DEFAULTS.update(
    dl_seat=45.0,       # seat height above the floor (cm): plastic chair 45, armchair 42, bench 46, car seat 30
    dl_knee=0.75,       # 0: the reference photo's knees (shoulder height) .. 1: knees well above his head
    dl_spread=0.0,      # knees apart (front views)
    dl_tape=1.0,        # 1 wrapped round and round .. 0 every strip off (strip by strip in between)
    dl_face=0.0,        # the face under the tape: 0 his own (pale, sunken), 1 Grandpa, 2 a stranger, 3 a little girl, 4 Ruth,
                        # 5 the narrator (fractions crossfade)
    dl_flinch=0.0,      # recoil from a question as if from light
    dl_roof=0.0,        # a roof (cm above the floor) the head must bend under (the car); 0 = none
    dl_click=0.0,       # the thumb pressing the pen's plunger 0..1
    dl_neck=1.0,        # neck reach forward
    dl_rock=0.0,        # the chair rocking (deg), for him and the empty chair
    dl_px0=0.0, dl_py0=0.0, dl_ph=0.0,       # the staging placement of world targets (set by Acting.at)
    dl_lw=0.0, dl_lx=0.0, dl_ly=0.0, dl_lz=0.0, dl_lrot=0.0,   # left hand world target (weight, design x, y, depth cm)
    dl_rw=0.0, dl_rx=0.0, dl_ry=0.0, dl_rz=0.0, dl_rrot=0.0,   # right hand world target
    dl_lf=0.0, dl_rf=0.0,                    # extra finger curl 0..1 per hand (count: fingers press)
    dl_count=0.0,       # a count pulse: the head dips a little on each number
)
POSE_DISCRETE.update(dl_lrest='lap', dl_rrest='pen', dl_ticket='MILO')


def _dl_rot_x(p, a, cy=0.0, cz=0.0):
    """Rotate (x, y, z) about the x axis through (cy, cz) by a forward lean a (rad): the top moves forward and down."""
    y, z = p[1] - cy, p[2] - cz
    ca, sa = math.cos(a), math.sin(a)
    return np.array([p[0], cy + y * ca + z * sa, cz - y * sa + z * ca])


def _unit3(v):
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-9 else v


class _DLView:
    """Projection of his body frame (cm) to the drawing frame (cm, x right, y down, floor under the seat at (0, 0)):
    yaw (pose.turn, quarter turns, + faces screen right), a slight downward camera elevation, mild perspective."""

    def __init__(self, P):
        self.th = P.turn * PI / 2
        self.ct, self.st = math.cos(self.th), math.sin(self.th)
        self.e = _DL_ELEV
        self.ce, self.se = math.cos(self.e), math.sin(self.e)
        self.D = _DL_D
        self.cy = -100.0
        self.tilt = math.radians(getattr(P, 'tilt', 0.0) + getattr(P, 'dl_rock', 0.0))
        self.sway = getattr(P, 'sway', 0.0) * 0.1

    def p(self, q):
        x, y, z = float(q[0]), float(q[1]), float(q[2])
        xc = x * self.ct + z * self.st
        zc = -x * self.st + z * self.ct
        yv = y * self.ce + zc * self.se
        zd = zc * self.ce - y * self.se
        f = self.D / (self.D - zd)
        X, Y = xc * f + self.sway, self.cy + (yv - self.cy) * f
        if self.tilt:                                       # the whole figure (and its chair) rocks about the seat's feet
            ct, st = math.cos(self.tilt), math.sin(self.tilt)
            X, Y = X * ct - Y * st, X * st + Y * ct
        return X, Y, zd, f

    def unp(self, X, Y, zd):
        """Inverse of p for a point at camera depth zd (cm toward the camera)."""
        if self.tilt:
            ct, st = math.cos(-self.tilt), math.sin(-self.tilt)
            X, Y = X * ct - Y * st, X * st + Y * ct
        X -= self.sway
        f = self.D / (self.D - zd)
        xc = X / f; yv = self.cy + (Y - self.cy) / f
        y = yv * self.ce - zd * self.se
        zc = yv * self.se + zd * self.ce
        x = xc * self.ct - zc * self.st
        z = xc * self.st + zc * self.ct
        return np.array([x, y, z])

    def depth_of(self, q):
        x, y, z = float(q[0]), float(q[1]), float(q[2])
        zc = -x * self.st + z * self.ct
        return zc * self.ce - y * self.se


def _dl_world_to_cm(P, wx, wy, zd=0.0):
    """A design-space point (in the staging placement carried by the pose) at camera depth zd (cm) -> body-frame cm."""
    if P.dl_ph <= 0: return None
    s = P.dl_ph / 1000.0 * _DLU                          # design px per cm
    X = (wx - (P.dl_px0 + P.dx)) / s; Y = (wy - (P.dl_py0 + P.dy)) / s
    return _DLView(P).unp(X, Y, zd)


def _dl_rig(P):
    """The 3D joints (cm, body frame) of Doctor Later for pose P: spine, neck, head frame, legs, arms (with the stretch of an
    arm reaching across a room), and the chair seat. Returns a dict."""
    R = {}
    hs = float(P.dl_seat)
    kk = clamp(P.dl_knee, 0.0, 1.25)
    fl = clamp(P.dl_flinch)
    lean = 0.16 + 0.55 * P.lean - 0.32 * fl + 0.04 * (P.breath - 0.5)
    hunch = 1.0 + P.hunch - 0.4 * fl
    H0 = np.array([0.0, -(hs + 5.0), -7.0])
    # spine: up from the seat, bowed back, then forward over the top into the shoulders (the reference's hump)
    lean += 0.22 * kk
    rel = [(0, 0, 0), (0, -24, -6), (0, -46, -7), (0, -62, -1.5 * hunch), (0, -69, 8 * hunch), (0, -71, 15 * hunch)]
    spine = [_dl_rot_x(H0 + np.array(r, float), lean, H0[1], H0[2]) for r in rel]
    R['spine'] = spine
    top = spine[-1]
    R['shoulder_c'] = spine[-2]
    # neck: long, reaching forward almost level, a slight droop, ending under the back of the skull
    nk = P.dl_neck * (1.0 - 0.45 * fl)
    neck = [top + np.array([0.0, 3.0, 4.0])]
    drop = 11.0 * kk                                    # folded tight (knees above the head): the neck droops
    for (dy, dz, k_) in ((-3.0, 12.0, 0.3), (-6.0, 23.0, 0.65), (-8.5, 32.0, 1.0)):
        neck.append(top + _dl_rot_x(np.array([0.0, dy + drop * k_, dz * nk]), 0.4 * lean))
    R['neck'] = neck
    hc = neck[-1] + np.array([0.0, -2.5, 6.5]) + np.array([0.0, 2.0, -10.0]) * fl
    hc = hc + np.array([P.h_dx * 0.08, P.h_dy * 0.08, 0.0])
    R['head'] = hc
    # legs: folded up like a grasshopper's, knees high, shins dropping to long pointed feet on the floor
    sp_ = P.dl_spread
    legs = {}
    for s in (-1, 1):
        Hp = H0 + np.array([s * 8.0, 2.0, 3.0])
        near = -s                                          # the right leg (s = -1) sits a little higher and closer
        # the near (right) knee higher with its foot drawn back under it, the far knee lower with its foot reaching forward
        Kd = np.array([s * (15.0 + 13.0 * sp_ + 5.0 * kk), -lerp(88.0, 116.0, kk) - 7.0 * near * (1.0 - 0.6 * kk),
                       lerp(72.0, 36.0, kk) + 8.0 * s])
        K = Hp + _unit3(Kd - Hp) * _DL_L['thigh']
        # the knee may not rise past the shin's reach of the floor (feet always on it)
        maxh = _DL_L['shin'] + 6.0
        if -K[1] > maxh: K[1] = -maxh
        ax = K[0] * 0.92 + s * 3.0
        drop = -K[1] - 7.0
        rad = _DL_L['shin'] ** 2 - drop ** 2 - (ax - K[0]) ** 2
        fwd = math.sqrt(max(rad, 0.0))
        A = np.array([ax, -7.0, K[2] + fwd * (1.0 if s > 0 else 0.55 + 0.4 * kk)])
        if s < 0:                                          # foot pulled back: the knee stays put, the shin steeper
            dz = A[2] - K[2]
            A[1] = min(-7.0, K[1] + math.sqrt(max(_DL_L['shin'] ** 2 - dz ** 2 - (ax - K[0]) ** 2, 1.0)))
        if rad < 0: A[1] = K[1] + _DL_L['shin']
        # pointed foot along the ground, in the direction the shin leans (forward if it is upright)
        hd = np.array([A[0] - K[0], 0.0, A[2] - K[2]])
        hn = float(np.linalg.norm(hd))
        fd = hd / hn if hn > 8.0 else np.array([s * 0.12, 0.0, 1.0])
        fd = _unit3(fd + np.array([s * 0.18, 0.0, 0.25]))
        T = A + fd * _DL_L['foot'] + np.array([0.0, 6.0, 0.0])
        legs[s] = (Hp, K, A, T)
    R['legs'] = legs
    # arms
    arms = {}
    for s in (-1, 1):
        rest = getattr(P, 'dl_lrest' if s > 0 else 'dl_rrest', 'lap')
        Sh = _dl_rot_x(H0 + np.array([s * 12.0, -66.0, 7.0 * hunch]), lean, H0[1], H0[2])
        Hp, K, A, T = legs[s]
        if rest == 'floor':      # hands flat on the carpet between the feet
            W = np.array([s * 10.0, -4.0, 44.0 + 5.0 * s])
        elif rest == 'knee':     # draped over the top of the knee
            W = K + np.array([-s * 2.0, -5.0, 2.0])
        elif rest == 'lap':      # holding the clipboard upright in his lap
            W = np.array([s * 7.0, -(hs + 28.0), 30.0])
        elif rest == 'pen':      # the pen hand in front of his chest
            W = np.array([s * 4.0, -(hs + 36.0), 32.0])
        elif rest == 'arm':      # on the armchair's arm
            W = np.array([s * 26.0, -(hs + 20.0), 14.0])
        elif rest == 'flinch':   # up before the face, as if from a light
            W = hc + np.array([s * 6.0, 10.0, 14.0])
        else:
            W = np.array([s * 12.0, -(hs + 10.0), 20.0])
        w = clamp(getattr(P, 'dl_lw' if s > 0 else 'dl_rw'))
        Tw_goal = None
        if w > 0.001:
            pre = 'dl_l' if s > 0 else 'dl_r'
            Tw = _dl_world_to_cm(P, getattr(P, pre + 'x'), getattr(P, pre + 'y'), getattr(P, pre + 'z'))
            if Tw is not None:
                Tw_goal = Tw.copy()
                # the target is where the pinch / fingertips / palm land: the wrist stops that far short of it
                shp = getattr(P, 'hl_shape' if s > 0 else 'hr_shape') or 'relaxed'
                off = {'pinch': 24.0, 'offer': 24.0, 'point': 24.0, 'grip': 7.0, 'flat': 17.0, 'reach': 21.0, 'claw': 17.0}.get(shp, 16.0)
                Tw = Tw - _unit3(Tw - Sh) * off
                W = W + (Tw - W) * w
        if fl > 0.01 and rest != 'flinch':
            W = W + ((hc + np.array([s * 7.0, 12.0, 16.0])) - W) * (0.65 * fl)
        Lu, Lf = _DL_L['upper'], _DL_L['fore']
        # floor: elbows out and back like a spider's; lap / pen: the upper arm hangs and the forearm folds up (a mantis)
        pole = _unit3({'floor': np.array([s * 0.75, 0.55, -0.45]), 'lap': np.array([s * 0.3, 1.0, 0.05]),
                       'pen': np.array([s * 0.3, 1.0, 0.05])}.get(rest, np.array([s * 0.6, 0.6, -0.55])))

        def solve(W):
            d = float(np.linalg.norm(W - Sh))
            k = max(1.0, d / ((Lu + Lf) * 0.985))
            if k > 1.0:              # the arm unfolds unnaturally long: a second elbow opens like a folding rule
                L = (Lu + Lf) * k * 1.0
                u = _unit3(W - Sh)
                perp = _unit3(pole - u * float(np.dot(pole, u)))
                sl = min(0.12, 0.35 / k) * L * 0.25
                E1 = Sh + u * L * 0.34 + perp * sl
                E2 = Sh + u * L * 0.68 - perp * sl * 0.6
                return dict(S=Sh, J=[E1, E2], W=W, k=k, rest=rest)
            E, Wr = _ik(Sh, W, Lu, Lf, pole)
            return dict(S=Sh, J=[E], W=Wr, k=1.0, rest=rest)
        arms[s] = solve(W)
        if w > 0.5 and Tw_goal is not None:
            # correct for where the pinch / fingertips really land with this hand pose (two passes)
            R['arms'] = arms
            for _ in range(2):
                hd_ = _dl_hand3(R, None, s, P)
                tips = (hd_['fingers'][0][-1] + hd_['fingers'][1][-1]) / 2 if (getattr(P, 'hl_shape' if s > 0 else 'hr_shape') or '') != 'grip' \
                    else hd_['W'] + hd_['f'] * 6.0
                W = arms[s]['W'] + (Tw_goal - tips) * min(1.0, w)
                arms[s] = solve(W)
    R['arms'] = arms
    # head orientation (relative to the camera): body yaw + head yaw, pitch (nod), roll (h_tilt)
    R['h_yaw'] = (P.turn + P.h_turn) * PI / 2 - 0.55 * fl * (1 if P.turn >= 0 else -1)      # turns away (a stable side)
    R['h_pitch'] = 0.6 * P.h_nod + 0.12 + 0.06 * clamp(P.dl_count) - 0.35 * fl
    R['h_roll'] = P.h_tilt + 8.0 * fl
    if P.dl_roof > 0:
        # a roof over him (the car): the head sinks under it and tips over until the cone lies along it
        roof = -float(P.dl_roof)
        top_face = hc[1] - _DL_FACE[1]
        if top_face < roof + 2.0:
            d_ = (roof + 2.0) - top_face
            hc = hc + np.array([0.0, d_, 0.0]); R['head'] = hc
            nk_ = R['neck']
            for i in range(1, len(nk_)): nk_[i] = nk_[i] + np.array([0.0, d_ * i / (len(nk_) - 1), 0.0])
        L_ = _DL_CONE['L'] + abs(_DL_CONE['base_y'])
        room = (hc[1] - roof) - 1.0
        if room < L_:
            ang = math.degrees(math.acos(clamp(room / L_, -1.0, 1.0)))
            sg = 1.0 if getattr(P, 'dl_roof_side', 1.0) >= 0 else -1.0       # a fixed side: no flip when the idle tilt
            R['h_roll'] = sg * ang + 0.25 * R['h_roll']                     # crosses zero
            R['h_pitch'] += 0.1
    return R


def _dl_head_basis(R, view):
    """Orthonormal head axes in the camera frame (before roll): right, down, forward (toward where the face looks)."""
    yaw, pitch = R['h_yaw'], R['h_pitch']
    cy_, sy_ = math.cos(yaw), math.sin(yaw)
    cp, sp_ = math.cos(pitch), math.sin(pitch)
    # head local: x right, y down, z forward (face). Pitch about x (nod down: forward tips down), then yaw.
    def tf(v):
        x, y, z = v
        y1 = y * cp + z * sp_
        z1 = -y * sp_ + z * cp
        X = x * cy_ + z1 * sy_
        Z = -x * sy_ + z1 * cy_
        # camera elevation
        Y = y1 * view.ce + Z * view.se
        Zd = Z * view.ce - y1 * view.se
        return np.array([X, Y, Zd])
    return tf


# ------------------------------------------------------------------------------------------------- drawing helpers
def _dense_tube(pts, widths, step=None, k=0.75):
    """_tube through a polyline resampled every `step` units (default: the mean width), so long two-point limbs keep
    straight sides and round caps (the spline through two far points overshoots into spikes at the caps)."""
    pts = [tuple(map(float, p)) for p in pts]
    if len(pts) < 2: return None
    step = step or max(0.5, sum(widths) / len(widths) * 0.9)
    P2, W2 = [pts[0]], [widths[0]]
    for i in range(len(pts) - 1):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        L = math.hypot(bx - ax, by - ay)
        n = max(1, int(L / step))
        for j in range(1, n + 1):
            u = j / n
            P2.append((ax + (bx - ax) * u, ay + (by - ay) * u)); W2.append(widths[i] + (widths[i + 1] - widths[i]) * u)
    if len(P2) == 2: P2.insert(1, ((P2[0][0] + P2[1][0]) / 2, (P2[0][1] + P2[1][1]) / 2)); W2.insert(1, (W2[0] + W2[1]) / 2)
    return _tube(P2, W2, k)


def _dl_tube(c, pts, widths, det, light=None, fib=0, seed=0, col=None):
    """A black sinewy limb segment chain: fill, a cool sheen down one side, fibres, outline."""
    if len(pts) < 2: return None
    tp = _dense_tube(pts, widths)
    c.fill(tp, col or _DL_BLACK)
    c.fill(_crescent(tp, 0.9 * widths[0] * 0.35, 0.6 * widths[0] * 0.2), _DL_BLACK_SH, 200)
    c.fill(_crescent(tp, -widths[0] * 0.28, widths[0] * 0.1), _DL_BLACK_HI, 120)
    if light and light.get('rim'):
        rs = light.get('side', 1)
        c.fill(_crescent(tp, -rs * widths[0] * 0.3, 0), light['rim'], light.get('rim_a', 70) * 1.2)
    if det >= 1 and fib:
        ls = []
        for i in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            L = math.hypot(bx - ax, by - ay) or 1.0
            nx, ny = -(by - ay) / L, (bx - ax) / L
            for k in range(fib):
                o = (hash01(k + 7 * i, seed + 61) - 0.5) * widths[i] * 0.7
                u0 = 0.1 + 0.3 * hash01(k + 3 * i, seed + 62); u1 = u0 + 0.35 + 0.25 * hash01(k, seed + 63)
                ls.append(poly([(ax + (bx - ax) * u0 + nx * o, ay + (by - ay) * u0 + ny * o),
                                (ax + (bx - ax) * min(u1, 0.97) + nx * o * 0.8, ay + (by - ay) * min(u1, 0.97) + ny * o * 0.8)], False))
        if ls: c.line(_multi(ls), c.lw * 0.35, '#34363f', 150)
    c.line(tp, c.lw * 0.8, '#060608')
    return tp


def _dl_knob(c, x, y, r, det):
    """A knobbly joint (knee, elbow, knuckle) bulging past the limb."""
    o = oval(x, y, r * 1.05, r * 0.95)
    c.fill(o, _DL_BLACK)
    if det >= 1: c.glow(x - r * 0.35, y - r * 0.4, r * 0.55, r * 0.45, '#5a5e6a', 120)
    c.line(o, c.lw * 0.7, '#060608')


def _dl_hand3(R, view, s, P):
    """3D hand points (cm) for the hand on side s: palm quad, fingers (each a list of points), thumb, and the frame."""
    arm = R['arms'][s]
    W = arm['W']; prev = arm['J'][-1]
    rest = arm['rest']
    shape = getattr(P, 'hl_shape' if s > 0 else 'hr_shape') or 'relaxed'
    if shape in ('mitt',): shape = 'relaxed'
    fore = _unit3(W - prev)
    # finger direction and palm normal by rest / shape
    if shape == 'flat' or (rest == 'floor' and getattr(P, 'dl_lw' if s > 0 else 'dl_rw') < 0.5 and shape == 'relaxed'):
        shape = 'flat'
        f = _unit3(np.array([s * 0.25, 0.0, 1.0])); n = np.array([0.0, 1.0, 0.0])
    elif shape in ('pinch', 'offer'):
        f = _unit3(fore + np.array([0.0, -0.15, 0.0])); n = _unit3(np.cross(f, np.array([s * 1.0, 0.0, 0.0])) * -1.0)
        if float(np.linalg.norm(n)) < 0.5: n = np.array([0.0, 1.0, 0.0])
    elif shape == 'grip':                                   # wrapped round a wrist: palm toward it
        f = _unit3(fore + np.array([0.0, 0.25, 0.0])); n = _unit3(np.cross(np.array([s * 1.0, 0.0, 0.0]), f))
    elif shape == 'pen':
        f = _unit3(np.array([-s * 0.6, -0.55, 0.6])); n = _unit3(np.array([-s * 0.5, 0.4, -0.3]))
    elif shape == 'clip':
        f = _unit3(np.array([-s * 0.2, -0.6, 0.6])); n = _unit3(np.array([-s * 1.0, 0.0, 0.0]))
    else:
        f = _unit3(fore * 0.8 + np.array([0.0, 0.35, 0.15])); n = _unit3(np.cross(f, np.array([s * 1.0, 0.0, 0.0])))
    n = _unit3(n - f * float(np.dot(n, f)))
    a = np.cross(f, n)                                     # across the knuckles (thumb on the s side of +a)
    curl = {'flat': 0.07, 'relaxed': 0.42, 'pinch': 0.05, 'offer': 0.05, 'grip': 0.95, 'pen': 0.75, 'clip': 0.6, 'reach': 0.22,
            'point': 0.05, 'claw': 0.55}.get(shape, 0.4)
    extra = clamp(getattr(P, 'dl_lf' if s > 0 else 'dl_rf', 0.0))
    pal = _DL_L['palm']
    lens = (7.0, 5.2, 4.0)
    offs = (2.9, 1.0, -0.9, -2.7)
    fingers = []
    for i, o in enumerate(offs):
        cu = curl
        if shape in ('pinch', 'offer') and i >= 2: cu = 0.95
        if shape == 'point' and i >= 1: cu = 0.95
        if shape == 'pen' and i == 0: cu = 0.45
        cu = cu + (1.0 - cu) * 0.35 * extra * (1 if i < 3 else 0.5)
        splay = (0.16 if shape in ('flat', 'reach', 'claw') else 0.05) * (i - 1.5) * s
        if shape in ('pinch', 'offer') and i < 2: splay = (0.03 if i == 0 else -0.03) * s
        base = W + f * pal + a * (s * o * 0.95)
        d = _unit3(f + a * (s * splay))
        pts = [base]
        ang = 0.0
        q = base
        for j, ln in enumerate(lens):
            ang += cu * (0.6 if j == 0 else 0.75)
            dj = _unit3(d * math.cos(ang) + n * math.sin(ang))
            ln_ = ln * (0.86 if i == 3 else (1.05 if i == 1 else 1.0))
            q = q + dj * ln_
            pts.append(q)
        if shape == 'flat':
            for j in range(1, len(pts)): pts[j][1] = min(pts[j][1], -0.6)
        fingers.append(pts)
    # thumb
    tb = W + f * 1.6 + a * (s * 2.4)
    tcu = {'grip': 0.7, 'pen': 0.2, 'pinch': 0.55, 'offer': 0.55, 'flat': 0.1}.get(shape, 0.35)
    td = _unit3(f * 0.55 + a * s * 0.7 + n * 0.35)
    thumb = [tb]
    ang = 0.0; q = tb
    for ln in (4.4, 3.4):
        ang += tcu
        dj = _unit3(td * math.cos(ang) + (n - a * s * 0.3) * math.sin(ang))
        q = q + dj * ln; thumb.append(q)
    palm = [W + a * (s * 1.9), W + a * (-s * 1.6), W + f * pal + a * (-s * 3.4), W + f * pal + a * (s * 3.6)]
    return dict(W=W, f=f, n=n, a=a, fingers=fingers, thumb=thumb, palm=palm, shape=shape)


def _dl_draw_hand(c, R, view, s, P, det, light=None, t=0.0):
    hd = _dl_hand3(R, view, s, P)
    pr = lambda q: view.p(q)[:2]                     # noqa: E731
    # fingers behind the palm first (by depth), then the palm, then the rest
    items = []
    for i, fp in enumerate(hd['fingers']):
        z = sum(view.depth_of(q) for q in fp) / len(fp)
        items.append((z, 'f', fp, i))
    items.append((sum(view.depth_of(q) for q in hd['thumb']) / 3.0, 't', hd['thumb'], 9))
    zp = sum(view.depth_of(q) for q in hd['palm']) / 4.0
    items.append((zp, 'p', hd['palm'], -1))
    items.sort(key=lambda o: o[0])
    out = None
    for z, kind, pts3, i in items:
        if kind == 'p':
            pp = [pr(q) for q in pts3]
            pa = smooth(pp, True, 0.5)
            c.fill(pa, _DL_BLACK); c.fill(_crescent(pa, 1.2, 0.8), _DL_BLACK_SH, 180)
            if det >= 1: c.glow(sum(p[0] for p in pp) / 4 - 0.8, sum(p[1] for p in pp) / 4 - 0.8, 2.2, 1.6, '#4d515d', 90)
            c.line(pa, c.lw * 0.7, '#060608')
            continue
        pp = [pr(q) for q in pts3]
        w0 = 1.45 if kind == 'f' else 1.6
        ws = [w0, w0 * 0.9, w0 * 0.78, w0 * 0.5][:len(pp)]
        tp = _tube(pp, ws, 0.8)
        c.fill(tp, _DL_BLACK); c.fill(_crescent(tp, 0.35, 0.25), _DL_BLACK_SH, 200)
        if light and light.get('rim'): c.fill(_crescent(tp, -light.get('side', 1) * 0.4, 0), light['rim'], light.get('rim_a', 70))
        c.line(tp, c.lw * 0.55, '#060608')
        if det >= 1:                                   # knuckle bumps
            for q in pp[1:-1]:
                c.fill(oval(q[0], q[1], ws[0] * 0.42, ws[0] * 0.36), '#2a2c33', 220)
        if det >= 2 and kind == 'f':                   # a dull nail sheen at the tip
            q0, q1 = pp[-2], pp[-1]
            c.fill(oval(q1[0] - (q1[0] - q0[0]) * 0.25, q1[1] - (q1[1] - q0[1]) * 0.25, 0.45, 0.45), '#5c606b', 200)
    return hd


# ------------------------------------------------------------------------------------------------- coat and body
def _dl_rows(R, P):
    """Coat rows down the spine: (centre 3D, half width, half depth). The coat hangs off the narrow shoulders over the
    hunched back and drapes over the seat."""
    sp = R['spine']; hs = P.dl_seat
    rows = []
    neck0 = R['neck'][0]
    rows.append((sp[5] + np.array([0.0, -6.0, -8.0]), 10.0, 8.0))         # the hump of his back, above and behind the neck
    rows.append((neck0 + np.array([0.0, 3.0, -3.0]), 7.0, 6.5))           # collar round the neck's root
    rows.append((sp[5] + np.array([0.0, 3.0, -3.0]), 13.0, 9.0))          # shoulders (the coat hangs off them)
    rows.append((sp[4] + np.array([0.0, 6.0, -3.0]), 13.5, 9.0))
    rows.append((sp[3] + np.array([0.0, 4.0, 0.0]), 11.5, 9.5))           # chest
    rows.append((sp[2] + np.array([0.0, 0.0, 1.0]), 10.0, 9.0))           # waist
    rows.append((sp[1] + np.array([0.0, 0.0, 2.0]), 10.5, 9.5))
    rows.append((sp[0] + np.array([0.0, 0.0, 3.0]), 12.5, 11.5))          # seat
    rows.append((np.array([0.0, -(hs - 9.0), -5.0]), 14.0, 13.5))         # hem draped over the seat edge
    return rows


def _dl_tube_rows(view, rows):
    """Projected outline of a tube of horizontal elliptic rows: (path, centre line screen pts)."""
    L, Rr, C = [], [], []
    for (c3, w, d) in rows:
        X, Y, Z, f = view.p(c3)
        e = math.sqrt((w * view.ct) ** 2 + (d * view.st) ** 2) * f
        L.append((X - e, Y)); Rr.append((X + e, Y)); C.append((X, Y))
    pts = Rr + L[::-1]
    return smooth(pts, True, 0.55), C


def _dl_surf(view, row, xr, dz=0.0):
    """Screen point on the front surface of a coat row at fraction xr (-1..1) of its half width."""
    c3, w, d = row
    x = xr * w
    z = d * math.sqrt(max(0.0, 1.0 - xr * xr)) + dz
    return view.p(c3 + np.array([x, 0.0, z]))


def _dl_coat_path(R, P, view):
    """The coat's outline (with its front opening cut out when it faces us), as _dl_body draws it."""
    rows = _dl_rows(R, P)
    coat, C = _dl_tube_rows(view, rows)
    if view.ct > 0.3:
        op_l, op_r = [], []
        for i, row in enumerate(rows):
            g = [0.32, 0.31, 0.30, 0.22, 0.26, 0.32, 0.38, 0.42, 0.46][i] * (0.55 + 0.45 * view.ct)
            op_l.append(_dl_surf(view, row, -g, 0.8)[:2]); op_r.append(_dl_surf(view, row, g, 0.8)[:2])
        bot = view.p(rows[-1][0] + np.array([0.0, 4.0, rows[-1][2] + 2]))
        opening = smooth(op_r + [(bot[0], bot[1] + 6)] + op_l[::-1], True, 0.4)
        cut = minus(coat, opening)
        if cut is not None: coat = cut
    return coat


def _dl_body(c, R, P, view, det, light, t):
    """The thin black torso (seen in the coat's opening), the grey coat with its lapels, pocket and pens, grime and frayed
    hem; returns nothing."""
    rows = _dl_rows(R, P)
    # the black torso under the coat (only its front shows, between the coat's edges)
    sp_ = R['spine']
    trows = [(sp_[5] + np.array([0, 2, 0]), 8.0, 6.0), (sp_[4], 8.5, 7.0), (sp_[3], 7.0, 7.0), (sp_[2], 5.8, 6.5),
             (sp_[1], 6.4, 6.8), (sp_[0], 8.0, 8.0)]
    tb, _ = _dl_tube_rows(view, trows)
    c.fill(tb, _DL_BLACK)
    if det >= 1:                                         # ribs: thin pale arcs across the front
        rl = []
        for k in range(6):
            yy = 0.15 + 0.12 * k
            i0 = int(yy * (len(trows) - 1)); u = yy * (len(trows) - 1) - i0
            r0, r1 = trows[i0], trows[min(i0 + 1, len(trows) - 1)]
            cc = r0[0] + (r1[0] - r0[0]) * u; w = r0[1] + (r1[1] - r0[1]) * u; d = r0[2] + (r1[2] - r0[2]) * u
            pts = [view.p(cc + np.array([w * x, 1.5 * (1 - x * x), d * math.sqrt(max(0, 1 - x * x))]))[:2] for x in np.linspace(-0.8, 0.8, 7)]
            if view.ct > -0.2: rl.append(smooth(pts, False))
        if rl: c.line(_multi(rl), c.lw * 0.5, '#2e3038', 200)
    c.line(tb, c.lw * 0.8, '#060608')
    # the coat
    coat, C = _dl_tube_rows(view, rows)
    cl = _DL_COAT
    front = view.ct > 0.3
    if front:                                           # the coat hangs open: cut the opening out of the front
        op_l, op_r = [], []
        for i, row in enumerate(rows):
            g = [0.32, 0.31, 0.30, 0.22, 0.26, 0.32, 0.38, 0.42, 0.46][i] * (0.55 + 0.45 * view.ct)
            op_l.append(_dl_surf(view, row, -g, 0.8)[:2]); op_r.append(_dl_surf(view, row, g, 0.8)[:2])
        bot = view.p(rows[-1][0] + np.array([0.0, 4.0, rows[-1][2] + 2]))
        opening = smooth(op_r + [(bot[0], bot[1] + 6)] + op_l[::-1], True, 0.4)
        coat_cut = minus(coat, opening)
        if coat_cut is not None: coat = coat_cut
    R['coat_path'] = coat
    c.fill(coat, cl['c'])
    bb = coat.getBounds()
    lsd = (light or {}).get('side', 1)
    c.grad(coat, bb.left(), 0, bb.right(), 0, [(0, cl['hi'], 70 if lsd < 0 else 0), (0.45, cl['c'], 0), (1, cl['sh'], 190 if lsd < 0 else 120)])
    with c.clip(coat):
        c.grad(rect(bb.left() - 10, bb.top(), bb.width() + 20, bb.height() + 10), 0, bb.top() + bb.height() * 0.45, 0, bb.bottom(),
               [(0, cl['grime'], 0), (1, cl['grime'], 150)])
        if det >= 1:
            c.texture(coat, 'grunge', 0.22, 0.25)
            c.texture(coat, 'fabric', 0.12, 0.35)
            # stains: tea-brown blots (old coffee, dust)
            for k in range(4):
                u = hash01(k, 811); v = hash01(k, 812)
                X = bb.left() + bb.width() * (0.2 + 0.6 * u); Y = bb.top() + bb.height() * (0.35 + 0.55 * v)
                c.fill(_blob(X, Y, 2.2 + 2.0 * hash01(k, 813), 1.6 + 1.5 * hash01(k, 814), 9, k + 3, 0.4), cl['grime'], 90)
            # long drape folds down the back / sides
            fl = []
            for k in range(5):
                xr = -0.8 + 0.4 * k
                pts = [(_dl_surf(view, rows[i], xr * 0.9, -0.5)) for i in range(2, len(rows))]
                pts = [(p[0], p[1]) for p in pts if p[2] > -40]
                if len(pts) > 2: fl.append(smooth(pts, False))
            c.line(_multi(fl), c.lw * 0.45, cl['dp'], 120)
        if light and light.get('rim'):
            c.fill(_crescent(coat, -lsd * 2.4, 0), light['rim'], light.get('rim_a', 70) * 0.9)
    c.line(coat, c.lw, cl['line'])
    if front:
        # lapels: a notch either side of the opening, the collar standing round the neck
        for sd in (-1, 1):
            a0 = _dl_surf(view, rows[2], sd * 0.30, 1.0); a1 = _dl_surf(view, rows[3], sd * 0.62, 1.4)
            a2 = _dl_surf(view, rows[4], sd * 0.36, 1.2); a3 = _dl_surf(view, rows[5], sd * 0.42, 1.0)
            lp = smooth([a0[:2], a1[:2], a2[:2], a3[:2]], True, 0.4)
            c.fill(lp, cl['c']); c.fill(_crescent(lp, sd * 0.8, 0.4), cl['sh'], 160); c.line(lp, c.lw * 0.7, cl['line'])
        # breast pocket on his left, two old pens and a pencil
        if view.ct > 0.2:
            p0 = _dl_surf(view, rows[4], 0.48, 1.0); p1 = _dl_surf(view, rows[4], 0.86, 1.0)
            p2 = _dl_surf(view, rows[5], 0.88, 1.0); p3 = _dl_surf(view, rows[5], 0.50, 1.0)
            pk = poly([p0[:2], p1[:2], p2[:2], p3[:2]])
            c.line(pk, c.lw * 0.55, cl['dp'])
            for k, cc in enumerate(('#2b3a6a', '#1c1c22', '#b08a3a')):
                x_ = p0[0] + (p1[0] - p0[0]) * (0.2 + 0.25 * k); y_ = p0[1] + (p1[1] - p0[1]) * (0.2 + 0.25 * k)
                c.fill(rrect(x_ - 0.45, y_ - 4.5, 0.9, 5.5, 0.4), cc); c.line(rrect(x_ - 0.45, y_ - 4.5, 0.9, 5.5, 0.4), c.lw * 0.3)
            # a blank, cracked name badge on the other side (the name long rubbed off)
            b0 = _dl_surf(view, rows[4], -0.75, 1.2); b1 = _dl_surf(view, rows[4], -0.45, 1.2)
            bd = rrect(min(b0[0], b1[0]), b0[1] - 0.5, abs(b1[0] - b0[0]) + 0.1, 2.8, 0.4)
            c.fill(bd, '#d8d4c4'); c.line(bd, c.lw * 0.4)
            c.fill(rect(min(b0[0], b1[0]), b0[1] - 0.5, abs(b1[0] - b0[0]), 0.7), '#5a6a7a', 200)
    else:
        # a back view: the coat's back seam, the vent, the collar behind the neck
        pts = [_dl_surf(view, rows[i], 0.0, 0.5) for i in range(1, len(rows))]
        if view.ct < -0.2:
            back = [view.p(r[0] + np.array([0.0, 0.0, -r[2] - 0.5]))[:2] for r in rows[1:]]
            c.line(smooth(back, False), c.lw * 0.45, cl['dp'], 170)
    # frayed hem: a few loose threads
    if det >= 1:
        hr = rows[-1]
        th = []
        for k in range(6):
            xr = -0.9 + 0.36 * k
            X, Y, Z, f = view.p(hr[0] + np.array([xr * hr[1], 0.0, hr[2] * math.sqrt(max(0, 1 - xr * xr)) * (1 if view.ct >= 0 else -1)]))
            th.append(poly([(X, Y), (X + 0.5 * math.sin(t * 1.3 + k), Y + 2.0 + 1.5 * hash01(k, 821))], False))
        c.line(_multi(th), c.lw * 0.35, cl['dp'], 200)


def _dl_sleeve(c, R, view, s, det, light):
    """The coat's sleeve on the upper arm, far too short: it ends below the elbow, the long black forearm sticking out."""
    arm = R['arms'][s]
    S = arm['S']; J = arm['J']; W = arm['W']
    E = J[0]
    end = E + (J[1] - E) * 0.12 if len(J) > 1 else E + (W - E) * 0.28
    top = S + np.array([0.0, -3.0, 0.0])
    pts = [view.p(top)[:2], view.p(S)[:2], view.p(E)[:2], view.p(end)[:2]]
    ws = [8.6, 7.6, 6.6, 6.2]
    sl = _dense_tube(pts, ws)
    cl = _DL_COAT
    c.fill(sl, mix(cl['c'], cl['sh'], 0.35)); _cloth_shade(c, sl, cl['sh'], 190, 1.0, 3.0)
    if det >= 1: c.texture(sl, 'grunge', 0.2, 0.25)
    if light and light.get('rim'): c.fill(_crescent(sl, -light.get('side', 1) * 1.5, 0), light['rim'], light.get('rim_a', 70) * 0.8)
    c.line(sl, c.lw, cl['line'])
    # frayed cuff
    ex, ey = pts[-1]; px, py = pts[-2]
    ang = math.atan2(ey - py, ex - px)
    nx, ny = -math.sin(ang), math.cos(ang)
    cuff = poly([(ex + nx * 4.0, ey + ny * 4.0), (ex - nx * 4.0, ey - ny * 4.0)], False)
    c.line(cuff, c.lw * 1.4, cl['dp'], 220)
    if det >= 1:
        c.line(_multi([poly([(ex + nx * k, ey + ny * k), (ex + nx * k + math.cos(ang) * 1.8, ey + ny * k + math.sin(ang) * 1.8)], False)
                       for k in (-3, -1, 1.5, 3)]), c.lw * 0.3, cl['dp'], 200)


# ------------------------------------------------------------------------------------------------- the head
_DL_FACE = (8.2, 10.6, 8.0)              # his small face (half width, half height, half depth), cm
_DL_CONE = dict(base_y=-7.2, base_z=-1.6, rx=12.6, rz=11.4, L=62.0, lean=0.12)
_DL_FACES = (None, 'grandpa_ghost', 'stranger_face', 'ghost_girl', 'ruth', 'narr14')
POSE_DISCRETE.update(dl_layer='all')


def _dl_rings():
    """The rings the tape is wound on, chin to cone tip: (centre (x, y, z) head-local cm, axis, half width, half depth,
    part ('face' | 'cone'))."""
    fx, fy, fz = _DL_FACE
    rings = []
    ys = np.linspace(fy * 0.93, _DL_CONE['base_y'] + 0.4, 8)
    ys[1:-1] += np.array([(hash01(k, 871) - 0.5) * 0.8 for k in range(1, len(ys) - 1)])
    ys[4] = 0.25; ys[5] = -2.6                                          # the eye band (the gap) sits on the eye line
    for y in ys:
        k = math.sqrt(max(0.0, 1.0 - (y / fy) ** 2))
        rings.append((np.array([0.0, y, 0.6]), np.array([0.0, -1.0, 0.0]), fx * k + 0.25, fz * k + 0.25, 'face'))
    cn = _DL_CONE
    u = np.array([0.0, -math.cos(cn['lean']), math.sin(cn['lean'])])
    b = np.array([0.0, cn['base_y'], cn['base_z']])
    ss = np.linspace(0.0, cn['L'] * 0.985, 18)
    ss[1:-1] += np.array([(hash01(k, 873) - 0.5) * 1.6 for k in range(1, len(ss) - 1)])
    for s_ in ss:
        k = 1.0 - s_ / cn['L']
        rings.append((b + u * s_, u, cn['rx'] * k + 0.3, cn['rz'] * k + 0.3, 'cone'))
    return rings


_DL_RINGS = _dl_rings()
# the order the strips come off when he is asked questions: the gap's neighbours first, out over the face, then up the cone
_DL_EYE_BAND = 4                                                        # the band (between rings 4 and 5) holding the gap
_DL_PEEL = sorted(range(len(_DL_RINGS) - 1), key=lambda i: (abs(i - _DL_EYE_BAND) if i < 7 else 100 - i))


class _DLHead:
    """Head-local (cm) -> drawing frame for one frame: centre, orientation (yaw / pitch / camera elevation), roll, scale."""

    def __init__(self, R, view):
        self.tf = _dl_head_basis(R, view)
        X, Y, Z, f = view.p(R['head'])
        self.X, self.Y, self.Z, self.f = X, Y, Z, f
        self.roll = math.radians(R['h_roll']) + view.tilt
        self.cr, self.sr = math.cos(self.roll), math.sin(self.roll)

    def p(self, q):
        v = self.tf(q)
        x, y = v[0] * self.f, v[1] * self.f
        return (self.X + x * self.cr - y * self.sr, self.Y + x * self.sr + y * self.cr, v[2])

    def vis(self, d):
        """Depth (toward the camera) of a head-local direction."""
        return float(self.tf(d)[2])


def _dl_ring_pts(hd, ring, phis, tilt=0.0, phase=0.0, grow=0.0):
    c3, ax, rx, rz, part = ring
    # in-ring basis: ex = head x, ez = perpendicular to the axis toward the face
    ex = np.array([1.0, 0.0, 0.0])
    ez = _unit3(np.cross(ex, ax)) * -1.0
    if ez[2] < 0: ez = -ez
    pts = []
    for ph in phis:
        q = c3 + ex * (rx + grow) * math.cos(ph) + ez * (rz + grow) * math.sin(ph) + ax * (tilt * math.sin(ph + phase))
        pts.append(hd.p(q)[:2])
    return pts


def _dl_front_arc(hd, ring, n=17):
    """phi samples (silhouette to silhouette) over the half of a ring facing the camera."""
    c3, ax, rx, rz, part = ring
    ex = np.array([1.0, 0.0, 0.0])
    ez = _unit3(np.cross(ex, ax)) * -1.0
    if ez[2] < 0: ez = -ez
    A = hd.vis(ex); B = hd.vis(ez)
    ph0 = math.atan2(B, A)
    return np.linspace(ph0 - 1.53, ph0 + 1.53, n), ph0


def _dl_silhouettes(hd):
    """(face hull path, cone hull path) of the head."""
    face_pts, cone_pts = [], []
    phs = np.linspace(0, 2 * PI, 20, endpoint=False)
    for r in _DL_RINGS:
        pts = _dl_ring_pts(hd, r, phs)
        (face_pts if r[4] == 'face' else cone_pts).extend(pts)
    fx, fy, fz = _DL_FACE
    face_pts.append(hd.p(np.array([0.0, fy, 0.0]))[:2])
    cn = _DL_CONE
    u = np.array([0.0, -math.cos(cn['lean']), math.sin(cn['lean'])])
    tip = np.array([0.0, cn['base_y'], cn['base_z']]) + u * cn['L']
    cone_pts.append(hd.p(tip)[:2])
    return smooth(_hull(face_pts), True, 0.6), poly(_hull(cone_pts), True), hd.p(tip)[:2]


def _dl_own_face(c, hd, P, det, t):
    """His own face under the tape (the reference's): pale and bony, two deep dark sockets, two pale patient eyes in them
    (they follow look_x / look_y, half-lidded), the lower face darker."""
    fx, fy, fz = _DL_FACE
    face_hull = _dl_silhouettes(hd)[0]
    c.fill(face_hull, '#cfc7b5')
    bb = face_hull.getBounds()
    c.grad(face_hull, 0, bb.top(), 0, bb.bottom(), [(0, '#e0d9c8', 120), (0.45, '#cfc7b5', 0), (0.75, '#4a403a', 150), (1, '#1d1714', 230)])
    vis = hd.vis(np.array([0.0, 0.0, 1.0]))
    out = {}
    for sd in (-1, 1):
        ex, ey = sd * 3.3, -1.0
        ez = fz * math.sqrt(max(0.0, 1.0 - (ex / fx) ** 2 - (ey / fy) ** 2))
        X, Y, V = hd.p(np.array([ex, ey, ez]))
        n = hd.vis(_unit3(np.array([ex / fx ** 2, ey / fy ** 2, ez / fz ** 2])))
        if n < -0.15: continue
        k = clamp(0.35 + n, 0.25, 1.0)
        sock = oval(X, Y + 0.2, 2.5 * k * hd.f, 2.2 * hd.f)
        c.radial(sock, X, Y + 0.2, 3.0 * hd.f, [(0, '#060404', 255), (0.6, '#160f0d', 240), (1, '#3a302a', 0)])
        out[sd] = (X, Y, k)
    # the eyes: pale, half-lidded, patient
    lid = clamp(0.42 + 0.58 * P.blink + 0.25 * P.squint - 0.3 * P.wide)
    for sd, (X, Y, k) in out.items():
        rx, ry = 1.25 * k * hd.f, 0.75 * hd.f
        eye = oval(X, Y, rx, ry)
        lx = clamp(P.look_x, -1, 1) * 0.55 * rx; ly = clamp(P.look_y, -1, 1) * 0.35 * ry
        with c.clip(eye):
            c.fill(eye, '#c9ccbf')
            c.fill(oval(X + lx, Y + ly, 0.62 * hd.f * k, 0.62 * hd.f), '#aeb3a6')
            c.fill(oval(X + lx, Y + ly, 0.22 * hd.f * k, 0.22 * hd.f), '#141312')
            c.fill(oval(X + lx - 0.2 * hd.f, Y + ly - 0.22 * hd.f, 0.12 * hd.f, 0.1 * hd.f), '#ffffff', 220)
            c.fill(rect(X - rx - 1, Y - ry - 1, 2 * rx + 2, (2 * ry + 1) * lid + 0.2), '#2a221e')
        c.line(poly([(X - rx, Y - ry + (2 * ry) * lid), (X + rx, Y - ry + (2 * ry) * lid)], False), c.lw * 0.5, '#0a0807', 230)
    # nose holes and a thin dark mouth line (only on his own face, seen in close-ups once the tape is off)
    if det >= 1 and vis > 0.1:
        for sd in (-1, 1):
            X, Y, V = hd.p(np.array([sd * 0.55, 3.0, fz * 0.95]))
            c.fill(oval(X, Y, 0.32 * hd.f, 0.22 * hd.f), '#1d1512', 220)
        m = [hd.p(np.array([x, 5.6 + 0.15 * abs(x), fz * 0.86]))[:2] for x in np.linspace(-2.4, 2.4, 6)]
        c.line(smooth(m, False), c.lw * 0.6, '#140f0d', 230)
    return face_hull


def _grey_layer(c, a=1.0, tint=(0.80, 0.83, 0.82)):
    """Begin a layer whose content is drawn grey (low saturation, a cold tint): the faces under his tape."""
    r, g, b = tint
    lum = [0.299, 0.587, 0.114]
    sat = 0.12
    m = []
    for i, tv in enumerate((r, g, b)):
        row = [(lum[j] * (1 - sat) + (sat if j == i else 0.0)) * tv for j in range(3)]
        m += row + [0.0, 0.02]
    m += [0, 0, 0, 1, 0]
    p = skia.Paint(ColorFilter=skia.ColorFilters.Matrix(m), Alphaf=float(clamp(a)))
    c.cv.saveLayer(None, p)


def _dl_under_face(c, hd, R, P, det, t, light):
    """What is under the tape on the face: his own face (dl_face 0) or the faces of the people who said "it's probably
    nothing" (1 Grandpa, 2 a stranger, 3 a little girl, 4 Ruth, 5 the narrator), grey and patient, crossfading."""
    fhull, chull, tip = _dl_silhouettes(hd)
    v = clamp(P.dl_face, 0.0, len(_DL_FACES) - 1.0)
    i0 = int(math.floor(v)); u = v - i0
    i1 = min(i0 + 1, len(_DL_FACES) - 1)
    layers = [(i0, 1.0)] if u < 0.02 else ([(i1, 1.0)] if u > 0.98 else [(i0, 1.0), (i1, ease_in_out(u))])
    with c.clip(fhull):
        for idx, a in layers:
            who = _DL_FACES[idx]
            if who is None:
                if a < 0.999:
                    c.cv.saveLayer(None, skia.Paint(Alphaf=float(a)))
                    _dl_own_face(c, hd, P, det, t); c.cv.restore()
                else:
                    _dl_own_face(c, hd, P, det, t)
                continue
            sp = CAST[who]
            # their face (eyes to chin) fills his small face: about 0.073 cm per head unit
            k = 0.074 * (1.0 + 0.04 * math.sin(t * 2.0 + idx))
            yaw = R['h_yaw'] * 0.9
            Q = Pose('neutral')
            Q.lid_l = Q.lid_r = 0.0
            Q.eye_open = 0.82; Q.pupil = 0.9; Q.m_press = 0.35; Q.smile = 0.05; Q.brow_sad = 0.25
            Q.look_x = P.look_x * 0.6; Q.look_y = P.look_y * 0.6
            cx, cy, _ = hd.p(np.array([0.0, 0.6, _DL_FACE[2] * 0.4]))
            hc = c.sub(cx, cy, math.degrees(hd.roll), k * hd.f)
            _grey_layer(c, a)
            c.fill(fhull, mix(sp['skin'], '#9a9a9a', 0.4))
            draw_head_local(hc, who, Q, yaw, R['h_pitch'] * 0.8, det, t, None, sp)
            c.cv.restore()
        # the face sits in the hollow of the wrapping: shade its edge
        bb = fhull.getBounds()
        c.radial(fhull, bb.centerX(), bb.centerY(), max(bb.width(), bb.height()) * 0.62,
                 [(0, '#000000', 0), (0.7, '#000000', 40), (1, '#000000', 170)])


def _dl_cone_under(c, hd, det, light):
    """The cone under the tape: black like the reference, a dull sheen down one side."""
    fhull, chull, tip = _dl_silhouettes(hd)
    c.fill(chull, '#121216')
    bb = chull.getBounds()
    c.grad(chull, bb.left(), 0, bb.right(), 0, [(0, '#000000', 120), (0.35, '#3d404a', 150), (0.55, '#1b1c22', 0), (1, '#000000', 160)])
    if det >= 1: c.texture(chull, 'grunge', 0.18, 0.18)


def _dl_band_state(i, tape):
    """0 = the strip is wound on, 1 = it is off (peel progress in between)."""
    if tape >= 0.999: return 0.0
    n_off = (1.0 - clamp(tape)) * (len(_DL_RINGS) - 1)
    k = _DL_PEEL.index(i)
    return clamp(n_off - k)


def _dl_tape(c, hd, P, det, t, light):
    """The old yellow medical tape wound round and round the head: one band per pair of rings, each overlapping the one
    below, a slight spiral, darker edges and grime; the eye band has a thin gap in front. Peeling strips unwind and
    hang. Returns the list of hanging strips' anchor points."""
    nb = len(_DL_RINGS) - 1
    hang = []
    lsd = (light or {}).get('side', 1)
    n_off = (1.0 - clamp(P.dl_tape)) * nb
    for i in range(nb):
        u = _dl_band_state(i, P.dl_tape)
        v = n_off - _DL_PEEL.index(i)                      # > 1: fully off; the loose strip hangs on, then falls away
        if u >= 0.999 and v >= 2.5:
            continue
        r0, r1 = _DL_RINGS[i], _DL_RINGS[i + 1]
        phis, ph0 = _dl_front_arc(hd, r0 if r0[4] == r1[4] else r1)
        tilt = (0.45 if r0[4] == 'face' else 0.9) * (1.0 if i % 2 else -0.7)    # wraps criss-cross a little
        ph = 0.9 * i + 0.6
        lo = _dl_ring_pts(hd, r0, phis, tilt, ph, 0.18)
        hi = _dl_ring_pts(hd, r1, phis, tilt, ph, 0.18)
        if u >= 0.999:
            side = 1 if i % 2 else -1
            a0 = lo[1] if side > 0 else lo[-2]; b0 = hi[1] if side > 0 else hi[-2]
            hang.append(((a0[0] + b0[0]) / 2, (a0[1] + b0[1]) / 2, math.hypot(b0[0] - a0[0], b0[1] - a0[1]), 1.0, i, side,
                         clamp(1.0 - (v - 1.0) / 1.5)))
            continue
        if u > 0.001:
            # the strip unwinds from one side: only the part still on is drawn; the loose end hangs from where it lifts
            m = max(2, int(round(len(phis) * (1.0 - u))))
            side = 1 if i % 2 else -1
            if side > 0:
                lo, hi = lo[:m], hi[:m]
            else:
                lo, hi = lo[-m:], hi[-m:]
            ax_, ay_ = (lo[-1] if side > 0 else lo[0]); bx_, by_ = (hi[-1] if side > 0 else hi[0])
            hang.append(((ax_ + bx_) / 2, (ay_ + by_) / 2, math.hypot(bx_ - ax_, by_ - ay_), u, i, side, 1.0))
        band = poly(lo + hi[::-1], True)
        colr = _DL_TAPE[(i * 7 + 3) % len(_DL_TAPE)]
        if r0[4] == 'cone':
            colr = mix(colr, '#8f7a4c', clamp((i - 7) / 18.0) * 0.6)    # grimier toward the tip
        if i == _DL_EYE_BAND and P.dl_tape > 0.0:
            # the gap: in front only; tape on either side of it
            gap_w = 0.62
            keep = [k for k, p_ in enumerate(phis) if abs(((p_ - (PI / 2)) + PI) % (2 * PI) - PI) > gap_w]
            if keep and u < 0.001:
                runs, cur = [], [keep[0]]
                for k in keep[1:]:
                    if k == cur[-1] + 1: cur.append(k)
                    else: runs.append(cur); cur = [k]
                runs.append(cur)
                for run in runs:
                    if len(run) < 2: continue
                    seg = poly([lo[k] for k in run] + [hi[k] for k in run[::-1]], True)
                    c.fill(seg, colr); c.line(seg, c.lw * 0.45, _DL_TAPE_EDGE, 220)
                continue
        c.fill(band, colr)
        if det >= 1:
            c.texture(band, 'fabric', 0.22, 0.12)
            c.fill(_crescent(band, 0.0, 0.5 * hd.f), _DL_TAPE_EDGE, 90)
            if hash01(i, 851) > 0.55:                                    # a grimy smudge on some wraps
                j = int(hash01(i, 852) * (len(lo) - 2)) + 1 if len(lo) > 2 else 0
                if j < len(lo) and j < len(hi):
                    mx, my = (lo[j][0] + hi[j][0]) / 2, (lo[j][1] + hi[j][1]) / 2
                    c.fill(oval(mx, my, 1.4 * hd.f, 0.7 * hd.f), '#6f5e3a', 70)
        # the lower edge of each wrap casts a thin shadow onto the one below; the top edge catches light
        c.line(smooth(lo, False), c.lw * 0.55, _DL_TAPE_EDGE, 230)
        if det >= 1: c.line(smooth(hi, False), c.lw * 0.3, '#efe2b4', 120)
    # shading over the whole wrap: the head is round
    return hang


def _dl_hanging(c, hd, hang, t, det):
    """Loose strips of tape hanging from where they lifted, swaying."""
    for (x, y, w, u, i, side, al) in hang:
        if al <= 0.01: continue
        if al < 0.999: c.cv.saveLayer(None, skia.Paint(Alphaf=float(al)))
        L = (4.0 + 22.0 * u + 8.0 * (1.0 - al)) * hd.f
        sw = math.sin(t * 1.6 + i) * 2.0 * hd.f
        dx = side * (2.0 + 4.0 * u) * hd.f
        pts = [(x, y), (x + dx * 0.6 + sw * 0.2, y + L * 0.35), (x + dx + sw * 0.6, y + L * 0.7), (x + dx * 0.8 + sw, y + L)]
        wd = max(1.2, w * 0.85)
        rb = _tube(pts, [wd, wd * 0.95, wd * 0.9, wd * 0.8], 0.8)
        c.fill(rb, _DL_TAPE[i % len(_DL_TAPE)]); c.fill(_crescent(rb, side * 0.6, 0), '#a08a55', 160)
        c.line(rb, c.lw * 0.5, _DL_TAPE_EDGE, 230)
        if al < 0.999: c.cv.restore()


def _dl_head(c, R, P, view, det, t, light):
    hd = _DLHead(R, view)
    fhull, chull, tip = _dl_silhouettes(hd)
    # under the tape: the black cone, the face
    _dl_cone_under(c, hd, det, light)
    _dl_under_face(c, hd, R, P, det, t, light)
    hang = _dl_tape(c, hd, P, det, t, light)
    sil = union(fhull, chull) or chull
    # soft roundness over the wrapping: lit on one side
    lsd = (light or {}).get('side', 1)
    bb = sil.getBounds()
    with c.clip(sil):
        cx0, cy0 = hd.X, hd.Y
        ax_ = (tip[0] - cx0, tip[1] - cy0); al = math.hypot(*ax_) or 1.0
        nx_, ny_ = -ax_[1] / al, ax_[0] / al                       # across the head (perpendicular to the cone's axis)
        w_ = 16.0 * hd.f
        c.grad(rect(bb.left() - 2, bb.top() - 2, bb.width() + 4, bb.height() + 4), cx0 - nx_ * w_, cy0 - ny_ * w_, cx0 + nx_ * w_, cy0 + ny_ * w_,
               [(0, '#1a1408', 150 if lsd > 0 else 60), (0.35, '#1a1408', 0), (0.62, '#fff6d8', 40), (0.8, '#1a1408', 30), (1, '#1a1408', 190 if lsd < 0 else 110)])
        c.grad(rect(bb.left() - 2, bb.top() - 2, bb.width() + 4, bb.height() + 4), cx0, cy0, tip[0], tip[1],
               [(0, '#000000', 0), (0.7, '#3a2a10', 40), (1, '#3a2a10', 120)])
        if det >= 1: c.texture(sil, 'grunge', 0.16, 0.2)
        if light and light.get('rim'):
            c.fill(_crescent(sil, -lsd * 1.0 * hd.f, 0), light['rim'], light.get('rim_a', 70))
    c.line(sil, c.lw * 0.9, '#0c0b0a')
    _dl_hanging(c, hd, hang, t, det)
    return hd


# ------------------------------------------------------------------------------------------------- props in his hands
def _dl_pen(c, R, view, s, P, det):
    """His click pen, held like a dagger, the thumb on the plunger (dl_click presses it)."""
    hd = _dl_hand3(R, view, s, P)
    th = hd['thumb'][-1]
    ax = _unit3(hd['thumb'][-1] - hd['W'] + np.array([0.0, -2.0, 0.0]))
    clk = clamp(P.dl_click)
    top = th - ax * (0.2 + 0.5 * clk)
    bot = top - ax * 14.0
    a, b = view.p(top + ax * (1.3 - 0.8 * clk)), view.p(bot)
    t0 = view.p(top)
    bar = _tube([t0[:2], b[:2]], [1.25, 1.0], 0.8)
    c.fill(bar, '#e6e4dc'); c.fill(_crescent(bar, 0.3, 0.2), '#a9a69c', 200); c.line(bar, c.lw * 0.5)
    pl = _tube([a[:2], t0[:2]], [0.7, 0.7], 0.8)
    c.fill(pl, '#2a3a7a'); c.line(pl, c.lw * 0.4)
    # the clip down the side and the steel tip
    cm_ = view.p(top - ax * 4.0)
    c.line(poly([t0[:2], cm_[:2]], False), c.lw * 0.9, '#2a3a7a')
    tp = view.p(bot - ax * 1.2)
    c.line(poly([b[:2], tp[:2]], False), c.lw * 0.8, '#8a8f98')


def _dl_clipboard(c, R, view, s, P, det):
    """The clipboard with no paper, upright in his lap against the knees, held at the top by one hand."""
    W = R['arms'][s]['W']
    Hp = R['legs'][s][0]
    top = W + np.array([-s * 2.0, 3.0, 2.0])
    bot = np.array([0.0, Hp[1] - 6.0, Hp[2] + 22.0])
    up = _unit3(top - bot)
    across = np.array([1.0, 0.0, 0.0])
    across = _unit3(across - up * float(np.dot(across, up)))
    L = 31.0; Wd = 22.5
    c0 = top - up * 1.0
    corners = [c0 + across * Wd / 2, c0 - across * Wd / 2, c0 - up * L - across * Wd / 2, c0 - up * L + across * Wd / 2]
    pts = [view.p(q)[:2] for q in corners]
    nrm = np.cross(across, up)
    face = view.depth_of(np.array([0.0, 0.0, 0.0]) + nrm) - view.depth_of(np.array([0.0, 0.0, 0.0]))
    b = poly(pts, True)
    c.fill(b, '#8a6a44' if face > -0.05 else '#6d5234')
    if det >= 1: c.texture(b, 'grunge', 0.25, 0.3)
    c.line(b, c.lw * 0.7)
    if face > 0.1:
        # no paper: just a torn scrap left under the clip, and the metal clip
        q = [c0 - up * 1.5 + across * 5, c0 - up * 1.5 - across * 4, c0 - up * 4.5 - across * 2, c0 - up * 3.2 + across * 3]
        sc = poly([view.p(x)[:2] for x in q], True)
        c.fill(sc, '#e8e2d0'); c.line(sc, c.lw * 0.3)
    cl = [c0 + across * 4.0 + up * 0.8, c0 - across * 4.0 + up * 0.8, c0 - across * 3.4 - up * 2.4, c0 + across * 3.4 - up * 2.4]
    cp = poly([view.p(x)[:2] for x in cl], True)
    c.fill(cp, '#9aa0a8'); c.line(cp, c.lw * 0.5)


def _dl_ticket(c, x, y, ang, k, text_=None, det=2, ink=1.0, colr='#f0e6d8'):
    """A deli-counter take-a-number ticket (5 x 6.5 cm) at (x, y) rotated ang deg, k = px per cm in this frame: a red band
    with the number box, the name in black block letters (ink 0 = faded to nothing)."""
    tc = c.sub(x, y, ang, k)
    p = rrect(-2.5, -3.25, 5.0, 6.5, 0.25)
    tc.fill(p, colr)
    tc.fill(rect(-2.5, -3.25, 5.0, 1.1), '#c0392f', 220 * clamp(0.3 + 0.7 * ink))
    if det >= 1:                                    # perforated ends
        tc.line(_multi([oval(-2.2 + 0.55 * j, 3.2, 0.12, 0.12) for j in range(9)]), tc.lw * 0.3, '#9a8f80', 200)
    if text_ and ink > 0.02:
        _block_text(tc, text_, 0.0, 0.6, 1.25, '#151515', 255 * ink)
    tc.line(p, tc.lw * 0.5)


# a tiny block-letter font (strokes on a 4 x 6 grid) so ticket names and card words draw as vector paths at any size
_BLOCK = {
    'A': [[(0, 6), (0, 2), (2, 0), (4, 2), (4, 6)], [(0, 3.5), (4, 3.5)]], 'B': [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)], [(0, 0), (3, 0), (4, 1), (4, 2), (3, 3)]],
    'C': [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5)]], 'D': [[(0, 0), (0, 6), (2.5, 6), (4, 4.5), (4, 1.5), (2.5, 0), (0, 0)]],
    'E': [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (3, 3)]], 'F': [[(4, 0), (0, 0), (0, 6)], [(0, 3), (3, 3)]],
    'G': [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 3.5), (2.5, 3.5)]], 'H': [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    'I': [[(1, 0), (3, 0)], [(2, 0), (2, 6)], [(1, 6), (3, 6)]], 'J': [[(4, 0), (4, 5), (3, 6), (1, 6), (0, 5)]],
    'K': [[(0, 0), (0, 6)], [(4, 0), (0, 3.5)], [(1.4, 2.6), (4, 6)]], 'L': [[(0, 0), (0, 6), (4, 6)]],
    'M': [[(0, 6), (0, 0), (2, 3), (4, 0), (4, 6)]], 'N': [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    'O': [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]], 'P': [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)]],
    'R': [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)], [(2, 3), (4, 6)]], 'S': [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    'T': [[(0, 0), (4, 0)], [(2, 0), (2, 6)]], 'U': [[(0, 0), (0, 5), (1, 6), (3, 6), (4, 5), (4, 0)]], 'V': [[(0, 0), (2, 6), (4, 0)]],
    'W': [[(0, 0), (1, 6), (2, 3), (3, 6), (4, 0)]], 'Y': [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]], 'Z': [[(0, 0), (4, 0), (0, 6), (4, 6)]],
    '0': [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]], '1': [[(1, 1), (2, 0), (2, 6)], [(1, 6), (3, 6)]],
    '2': [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (0, 6), (4, 6)]], '3': [[(0, 0), (4, 0), (2, 2.5), (3, 2.5), (4, 3.5), (4, 5), (3, 6), (1, 6), (0, 5)]],
    '4': [[(3, 6), (3, 0), (0, 4), (4, 4)]], '5': [[(4, 0), (0, 0), (0, 2.5), (3, 2.5), (4, 3.5), (4, 5), (3, 6), (0, 6)]],
    '6': [[(3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)]], '7': [[(0, 0), (4, 0), (1.5, 6)]],
    '8': [[(1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (1, 3), (0, 4), (0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3)], [(1, 3), (0, 2), (0, 1), (1, 0)]],
    '9': [[(4, 3), (1, 3), (0, 2), (0, 1), (1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6)]], '-': [[(1, 3), (3, 3)]], '.': [[(2, 5.6), (2, 6)]],
    ':': [[(2, 1.6), (2, 2)], [(2, 4.6), (2, 5)]], "'": [[(2, 0), (2, 1.5)]], ',': [[(2, 5.4), (1.5, 6.6)]], '?': [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (2, 3.5), (2, 4.2)], [(2, 5.6), (2, 6)]],
}


def _block_text(c, s, cx, cy, h, colr, a=255, w=None, wobble=0.0, seed=0):
    """Draw s in the block font centred at (cx, cy), cap height h (frame units). wobble > 0 = hand-written (marker)."""
    s = s.upper()
    sc = h / 6.0
    adv = 5.4 * sc
    x0 = cx - (len(s) * adv - 1.4 * sc) / 2.0
    paths = []
    for i, ch in enumerate(s):
        for st in _BLOCK.get(ch, []):
            pts = []
            for j, (x, y) in enumerate(st):
                jx = (hash01(i * 13 + j, seed + 71) - 0.5) * wobble * sc
                jy = (hash01(i * 13 + j, seed + 72) - 0.5) * wobble * sc
                pts.append((x0 + i * adv + x * sc + jx, cy - h / 2 + y * sc + jy))
            if len(pts) == 2 and pts[0] == pts[1]: pts[1] = (pts[1][0] + 0.01, pts[1][1])
            paths.append(poly(pts, False) if wobble <= 0 else smooth(pts, False, 0.4))
    if paths: c.line(_multi(paths), (w if w is not None else h * 0.16), colr, a)


# ------------------------------------------------------------------------------------------------- the figure
def _later_figure(c, who, P, det, t, light=None, upper_only=False):
    """Doctor Later in body units on Ctx c (floor under the seat at (0, 0)): far limbs, the coat and body, near limbs,
    neck and head, sorted by depth; his props (pen, clipboard, ticket) in his hands. pose.dl_layer 'back' / 'front' draws
    only the parts behind / in front of his body's plane (sandwich an armchair's arm or a car seat between them)."""
    cc = c.sub(0.0, 0.0, 0.0, _DLU)
    view = _DLView(P)
    R = _dl_rig(P)
    pr = lambda q: view.p(q)[:2]                     # noqa: E731
    R['coat_path'] = _dl_coat_path(R, P, view)
    R0 = None                                        # his rest pose, when the hand holding the clipboard reaches away
    for s_ in (-1, 1):
        if getattr(P, ('hl_' if s_ > 0 else 'hr_') + 'prop') == 'clipboard' and getattr(P, 'dl_lw' if s_ > 0 else 'dl_rw') > 0.0:
            P0 = P.copy(); P0.dl_lw = 0.0; P0.dl_rw = 0.0
            R0 = _dl_rig(P0)
    items = []
    layer = getattr(P, 'dl_layer', 'all') or 'all'
    for s in (-1, 1):
        Hp, K, A, T = R['legs'][s]
        def leg(cx_, Hp=Hp, K=K, A=A, T=T, s=s):
            h2, k2, a2, t2 = pr(Hp), pr(K), pr(A), pr(T)
            # thigh thick at the hip, a bony knee (a little point on its outside), a thin shin with a slight calf
            kn = (K - Hp); ks = (A - K)
            kout = _unit3(_unit3(kn) - _unit3(ks)) * 2.2
            kp = pr(K + kout)
            calf = pr(K + ks * 0.3 + np.array([0.0, 0.0, -1.5]))
            m1 = pr(Hp + kn * 0.45)
            cp_ = R.get('coat_path')
            if cp_ is not None and view.depth_of(Hp) > view.depth_of(R['spine'][1]) - 30:
                with cx_.clip(cp_, diff=True): _dl_tube(cx_, [h2, m1, k2], [10.0, 7.0, 4.6], det, light, 3, 10 + s)
            else:
                _dl_tube(cx_, [h2, m1, k2], [10.0, 7.0, 4.6], det, light, 3, 10 + s)
            _dl_tube(cx_, [k2, calf, a2], [4.6, 4.4, 2.6], det, light, 3, 20 + s)
            kb = poly([(k2[0] + (k2[0] - kp[0]) * 0.2 - (kp[1] - k2[1]) * 0.8, k2[1] + (k2[1] - kp[1]) * 0.2 + (kp[0] - k2[0]) * 0.8), kp,
                       (k2[0] + (k2[0] - kp[0]) * 0.2 + (kp[1] - k2[1]) * 0.8, k2[1] + (k2[1] - kp[1]) * 0.2 - (kp[0] - k2[0]) * 0.8)], True)
            cx_.fill(kb, _DL_BLACK)
            if det >= 1: cx_.glow(kp[0], kp[1], 1.4, 1.1, '#6a6e7a', 120)
            ft = _dl_tube(cx_, [a2, pr((A + T) / 2 + np.array([0.0, -0.8, 0.0])), t2], [3.4, 2.8, 0.8], det, light, 0, 30 + s)
        items.append(((view.depth_of(Hp) + view.depth_of(K)) / 2 + 0.01 * s, 'leg', leg))
        arm = R['arms'][s]
        def armf(cx_, arm=arm, s=s):
            pts = [arm['S']] + arm['J'] + [arm['W']]
            p2 = [pr(q) for q in pts]
            ws = [6.4] + [4.6] * len(arm['J']) + [3.0]
            for j in range(len(p2) - 1):
                _dl_tube(cx_, [p2[j], p2[j + 1]], [ws[j], ws[j + 1]], det, light, 2, 40 + 5 * j + s)
            for j in range(1, len(p2) - 1):
                if det >= 1: cx_.glow(p2[j][0], p2[j][1], 1.6, 1.3, '#5a5e6a', 110)
            _dl_sleeve(cx_, R, view, s, det, light)
            pre = 'hl_' if s > 0 else 'hr_'
            prop = getattr(P, pre + 'prop')
            if prop == 'pen': _dl_pen(cx_, R, view, s, P, det)
            hd = _dl_draw_hand(cx_, R, view, s, P, det, light, t)
            if prop == 'clipboard' and R0 is None: _dl_clipboard(cx_, R, view, s, P, det); _dl_draw_hand(cx_, R, view, s, P, det, light, t)
            if prop == 'ticket':
                f1, f2 = hd['fingers'][0][-1], hd['fingers'][1][-1]
                mid = (f1 + f2) / 2 - hd['f'] * 1.2
                X, Y, Z, f = view.p(mid)
                d2 = view.p(mid + hd['f'])
                ang = math.degrees(math.atan2(d2[1] - Y, d2[0] - X)) - 90.0
                _dl_ticket(cx_, X, Y + 1.0, ang * 0.35, f, getattr(P, 'dl_ticket', 'MILO'), det)
                # the two long fingers pinch it: draw them again over the ticket
                for fp in hd['fingers'][:2]:
                    p2_ = [pr(q) for q in fp]
                    tp = _tube(p2_, [1.45, 1.3, 1.1, 0.7], 0.8)
                    cx_.fill(tp, _DL_BLACK); cx_.line(tp, cx_.lw * 0.55, '#060608')
        zarm = sum(view.depth_of(q) for q in [arm['S']] + arm['J'] + [arm['W']]) / (2 + len(arm['J']))
        items.append((zarm + 0.02 * s, 'arm', armf))
        if R0 is not None and getattr(P, ('hl_' if s > 0 else 'hr_') + 'prop') == 'clipboard':
            # the clipboard hand is reaching: the clipboard stays where it was, leaning upright against his knees
            items.append((view.depth_of(R0['arms'][s]['W']) + 0.015 * s, 'clip', lambda cx_, s=s: _dl_clipboard(cx_, R0, view, s, P, det)))
    zb = view.depth_of(R['spine'][3])
    items.append((zb, 'body', lambda cx_: _dl_body(cx_, R, P, view, det, light, t)))
    zh = view.depth_of(R['head'])
    def neckhead(cx_):
        p2 = [pr(q) for q in R['neck']] + [pr(R['head'])]
        tp = _dense_tube(p2[:-1], [8.0, 7.0, 6.4, 6.0])
        cx_.fill(tp, _DL_BLACK)
        cx_.fill(_crescent(tp, 0.0, 1.2), _DL_BLACK_SH, 200)
        if det >= 1:                                  # ribbed rings down the long neck
            rl = []
            for k in range(1, 9):
                u = k / 9.0
                q = R['neck'][0] + (R['neck'][-1] - R['neck'][0]) * u
                a_ = view.p(q + np.array([3.0, -3.0, 0.0]))[:2]; b_ = view.p(q + np.array([-3.0, 3.0, 0.0]))[:2]
                m_ = view.p(q)[:2]
                rl.append(smooth([a_, (m_[0] + 0.6, m_[1] + 0.6), b_], False))
            cx_.line(_multi(rl), cx_.lw * 0.45, '#383a43', 200)
        cx_.line(tp, cx_.lw * 0.8, '#060608')
        _dl_head(cx_, R, P, view, det, t, light)
    items.append((zh, 'head', neckhead))
    items.sort(key=lambda o: o[0])
    for z, kind, fn in items:
        if layer == 'back' and z >= zb and kind != 'body': continue
        if layer == 'front' and (z < zb or kind == 'body'): continue
        if layer == 'back' and kind == 'body': fn(cc); continue
        fn(cc)
    return R


_figure_doctor_prev = _figure


def _figure(c, who, P, det, t, light=None, upper_only=False):
    """Whole character in body units on Ctx c: Doctor Later dispatches here; everyone else as before."""
    if CAST[who].get('later'): return _later_figure(c, who, P, det, t, light, upper_only)
    return _figure_doctor_prev(c, who, P, det, t, light, upper_only)


CAST['later'] = dict(later=True, m=_DL_M, hh=150.0, blink_rate=0.025, lock=0.6, micro=0.3, talk=0.0,
                     breath=0.2, body=dict(sh=40, ch=40, wa=30, hip=30, arm=(20, 18), leg=(25, 20), neck=20, hand=1.0),
                     outfit='later', sex='m', ring=0, skin='#cfc7b5', skin_sh='#9a9384', cloth={})


# ====================================================================================================== THE PEOPLE
# Faces, bodies and hands are the v3 cast system (characters_bunny.py). New here: the outfits (Ruth's buttoned cardigan
# and glasses chain, the 1979 housecoat, Grandpa's brown cardigan, dinosaur pajamas, the dinosaur jeans that fall off,
# coffee-stained scrubs with a dinosaur-sticker badge, a raincoat over scrubs, white coats over scrubs, paramedics, a
# coat too small, running gear with a glucose sensor), Ruth's set curls, a watch on a wrist, a hospital gown with an IV
# line and monitor leads, grey "waiting" people, and the props they handle.

# ---------------------------------------------------------------------------------------------------- hair: set curls
_hairline_bunny_, _hair_region_bunny_ = _hairline, _hair_region


def _hairline(style, part):
    if style == 'set_curls':                 # Ruth: a short silver set, curled close to the head, the ears showing
        def yf(ph):
            a = np.abs(ph)
            return np.maximum(np.interp(a, [0, 0.55, 0.95, 1.25, 1.6, 2.2, PI], [-74, -70, -46, -18, 0, 40, 56]), _nape(ph))
        return yf, 14.0
    return _hairline_bunny_(style, part)


def _hair_region(c, hm, sp, P, det, sil, t):
    style = sp.get('hair')
    if style != 'set_curls': return _hair_region_bunny_(c, hm, sp, P, det, sil, t)
    hc = sp['hair_c']
    hsh = mix(hc, '#000000', 0.32); hhi = mix(hc, '#ffffff', 0.45)
    yf, grow = _hairline(style, sp['part'])
    X, Y = hm.arc_phi(yf, 140)
    if len(X) < 3: return
    region = _region_above(X, Y)
    vol = _bumpy(hm, grow, 15, 6.5, -126.0, 60.0, spiky=False, seed=4)
    hair = inter(union(vol, sil), region)
    c.fill(hair, hc)
    with c.clip(hair):
        c.radial(None, -30, -92, 170, [(0, hhi, 140), (0.5, hc, 0), (1, hsh, 190)], clip=False)
        if det >= 1: _curls(c, hm, det, hc, hsh, hhi)
    c.line(hair, c.lw)


# ---------------------------------------------------------------------------------------------------- palettes
def _greyed(colr, k=0.85, tint='#8a9294', dark=0.12):
    """A colour drained toward a cold grey (the waiting room's people: 'all of them gray')."""
    if not isinstance(colr, str) or not colr.startswith('#'): return colr
    r, g, b = [int(colr[i:i + 2], 16) for i in (1, 3, 5)]
    y = int(0.299 * r + 0.587 * g + 0.114 * b)
    gy = '#%02x%02x%02x' % (y, y, y)
    out = mix(colr, gy, k)
    out = mix(out, tint, 0.25)
    return mix(out, '#000000', dark)


def _ghost_of(sp):
    """A grey, still version of a cast entry: every colour drained, no blinks, no fidgets, a patient stillness."""
    d = dict(sp)
    for k in ('skin', 'skin_sh', 'skin_dp', 'blush', 'lip', 'hair_c', 'brow_c', 'iris_c', 'stubble', 'moustache'):
        if d.get(k): d[k] = _greyed(d[k], 0.9)
    d['cloth'] = {k: _greyed(v, 0.85) for k, v in sp['cloth'].items()}
    d.update(blink_rate=0.02, lock=0.0, micro=0.12, breath=0.15, ghost=True, lid_rest=max(sp.get('lid_rest', 0.2), 0.3), bags=0.7)
    return d


# ---------------------------------------------------------------------------------------------------- outfits
_DOC_ROWS = {   # torso rows: (neck add, shoulder k, sh add, ch add, ch2 add, waist add, belt add, hip add) as _rows3
    'cardi_ruth': (18, 0.88, 3, 6, 6, 6, 6, 6), 'housecoat': (16, 0.88, 4, 8, 8, 10, 10, 10), 'cardi_brown': (20, 0.9, 5, 8, 8, 10, 8, 6),
    'pj_dino': (14, 0.88, 2, 4, 6, 8, 8, 6), 'tee_jeans': (12, 0.88, 2, 4, 6, 8, 8, 6), 'runner': (10, 0.88, 0, 2, 0, -2, 0, 2),
    'scrubs_doc': (16, 0.88, 4, 8, 8, 10, 10, 8), 'raincoat': (28, 0.94, 10, 14, 14, 16, 16, 14), 'labscrubs': (26, 0.92, 8, 10, 10, 12, 12, 10),
    'medic': (20, 0.9, 6, 10, 10, 10, 10, 8), 'coat_small': (10, 0.86, 0, 2, 0, 0, 0, 2), 'gown_er': (12, 0.86, -2, 0, 2, 10, 10, 10),
}
_rows3_prev = _rows3


def _rows3(sp, B):
    o = sp['outfit']
    if o not in _DOC_ROWS: return _rows3_prev(sp, B)
    b = sp['body']; k = B.chest_k
    ys = [B.y_sh - 30, B.y_sh - 10, B.y_sh + 16, B.y_ch, B.y_ch + 80, B.y_wa, B.y_belt, B.y_hip]
    a = _DOC_ROWS[o]
    ws = [b['neck'] + a[0], b['sh'] * a[1], b['sh'] + a[2], b['ch'] * k + a[3], b['ch'] * 0.97 * k + a[4], b['wa'] + a[5],
          b['hip'] * 0.98 + a[6], b['hip'] + a[7]]
    if ys[4] >= ys[5] - 4: ys[4] = (ys[3] + ys[5]) * 0.5
    ds = [w * f for w, f in zip(ws, [0.55, 0.52, 0.5, 0.56, 0.6, 0.6, 0.62, 0.64])]
    return ys, ws, ds


_LEGS3.update({'cardi_ruth': 'skin', 'housecoat': 'skin', 'gown_er': 'skin'})
_SLEEVES3.update({'cardi_ruth': 'long', 'housecoat': 'long', 'cardi_brown': 'long', 'pj_dino': 'long', 'tee_jeans': 'short',
                  'runner': 'short', 'scrubs_doc': 'short', 'raincoat': 'long', 'labscrubs': 'long', 'medic': 'long',
                  'coat_small': 'pushed', 'gown_er': 'short'})


def _dino_shape(x, y, s, flip=1.0, kind=0):
    """A tiny dinosaur silhouette (0 long-neck, 1 T-rex, 2 triceratops) at (x, y), s = size (frame units)."""
    f = flip
    if kind == 0:
        pts = [(-1.0, 0.2), (-0.5, -0.2), (0.3, -0.25), (0.55, -0.9), (0.75, -1.05), (0.85, -0.9), (0.6, -0.2), (0.9, 0.3), (0.7, 0.35),
               (0.6, 0.0), (0.3, 0.1), (0.25, 0.4), (0.05, 0.4), (0.0, 0.15), (-0.4, 0.15), (-0.45, 0.4), (-0.62, 0.4), (-0.6, 0.15)]
    elif kind == 1:
        pts = [(-1.0, 0.1), (-0.3, -0.3), (0.2, -0.55), (0.45, -0.8), (0.85, -0.75), (0.85, -0.55), (0.5, -0.5), (0.45, -0.3), (0.55, -0.15),
               (0.35, -0.1), (0.25, 0.1), (0.3, 0.5), (0.1, 0.5), (0.05, 0.2), (-0.15, 0.2), (-0.2, 0.5), (-0.38, 0.5), (-0.35, 0.1)]
    else:
        pts = [(-0.9, 0.05), (-0.5, -0.35), (0.2, -0.4), (0.45, -0.7), (0.6, -0.35), (0.95, -0.2), (0.75, 0.05), (0.4, 0.05), (0.38, 0.4),
               (0.18, 0.4), (0.15, 0.15), (-0.35, 0.15), (-0.4, 0.4), (-0.6, 0.4), (-0.58, 0.1)]
    return smooth([(x + f * px * s, y + py * s) for px, py in pts], True, 0.5)


def _dino_print(c, B, rows, cl, back, n=14, size=9.0, seed=181, path=None):
    """Pajama / T-shirt print: a scatter of little dinosaurs on the torso surface."""
    ys, ws, ds = rows
    a_, b_ = [], []
    for k in range(n):
        x0 = (hash01(k, seed) * 2 - 1) * 0.84; y0 = ys[1] + (ys[-1] - ys[1]) * (0.06 + 0.88 * hash01(k, seed + 1))
        w = float(np.interp(y0, ys, ws))
        X, Y, v, s_ = B.surf(x0 * w, y0, 2, back, rows)
        if v < 0.1: continue
        (a_ if k % 2 else b_).append(_dino_shape(X, Y, size * s_ * max(0.45, abs(B.ct) ** 0.5), 1.0 if hash01(k, seed + 2) > 0.5 else -1.0, k % 3))
    if a_: c.fill(_multi(a_), cl.get('print_c', '#4f8a4a'), 230)
    if b_: c.fill(_multi(b_), cl.get('print_c2', '#e9a23b'), 230)


def _badge(c, X, Y, s_, cl, ang=0.0, stickers=True, det=2, name_c='#2a4a9a'):
    """A hospital ID badge (photo, name bar) at (X, Y), size s_; stickers: two little dinosaur stickers on it."""
    bc = c.sub(X, Y, ang, s_)
    card = rrect(-13, -17, 26, 34, 3)
    bc.fill(card, '#f6f6f2'); bc.fill(rect(-13, -17, 26, 7), name_c)
    bc.fill(rect(-9, -6, 9, 11), '#b9c6d2'); bc.fill(oval(-4.5, -2.5, 2.6, 3.0), '#8a98a8')
    if det >= 1:
        bc.line(_multi([poly([(2, -4 + 4 * k), (10, -4 + 4 * k)], False) for k in range(3)]), bc.lw * 0.35, '#5a6470')
    if stickers:
        bc.fill(_dino_shape(5.5, 11.0, 5.5, -1.0, 1), '#5fb04e'); bc.line(_dino_shape(5.5, 11.0, 5.5, -1.0, 1), bc.lw * 0.3)
        bc.fill(_dino_shape(-6.0, 12.0, 4.5, 1.0, 2), '#f08a3a'); bc.line(_dino_shape(-6.0, 12.0, 4.5, 1.0, 2), bc.lw * 0.3)
    bc.line(card, bc.lw * 0.5)
    bc.fill(rrect(-4, -21, 8, 5, 1.5), '#9aa0a8'); bc.line(rrect(-4, -21, 8, 5, 1.5), bc.lw * 0.4)


def _vneck(c, sp, B, rows, depth=40, colr=None):
    b = sp['body']; lw = c.lw
    vn, v = _surf_poly(B, rows, [(-b['neck'] - 4, B.y_sh - 30), (0, B.y_sh + depth), (b['neck'] + 4, B.y_sh - 30)], dz=3)
    if v > -0.2:
        c.fill(poly(vn, True), colr or sp['skin']); c.line(poly(vn, False), lw * 0.9)


def _front_cardi_ruth(c, sp, B, rows, P, det, t):
    """Ruth: a cardigan buttoned all the way up, a white blouse collar folded over it, the reading glasses on a chain."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    for sd in (-1, 1):                                    # the blouse's pointed collar over the cardigan's neckline
        cc, v = _surf_poly(B, rows, [(sd * 2, yS - 28), (sd * (b['neck'] + 10), yS - 34), (sd * (b['neck'] + 22), yS - 4),
                                     (sd * 10, yS + 14), (sd * 2, yS - 10)], dz=6)
        if v > -0.2:
            cp = smooth(cc, True, 0.5); c.fill(cp, cl['blouse']); c.fill(_crescent(cp, 0, -3), cl['blouse_sh'], 130); c.line(cp, lw * 0.55)
    ed, v = _surf_poly(B, rows, [(0, yS - 10), (0, B.y_hip - 18)], dz=3)
    if v > -0.2: c.line(poly(ed, False), lw * 1.6, cl['rib'])
    if v > -0.2: c.line(poly(ed, False), lw * 0.45)
    for k in range(6):
        X, Y, vv, s_ = B.surf(0, yS + 8 + k * (B.y_hip - 50 - yS) / 5.2, 6, False, rows)
        if vv > 0.12: c.shape(oval(X, Y, 4.6 * s_), cl['button'], lw * 0.4)
    if det >= 1:
        rb = []
        for k in range(-7, 8):
            pts, v = _surf_poly(B, rows, [(k * 15, B.y_hip - 40), (k * 15, B.y_hip - 16)], dz=1)
            if v > 0.1: rb.append(poly(pts, False))
        if rb: c.line(_multi(rb), lw * 0.3, cl['top_sh'], 170)
        # the cardigan's two small pockets
        for sd in (-1, 1):
            pk, v = _surf_poly(B, rows, [(sd * 22, B.y_hip - 96), (sd * (b['hip'] * 0.72), B.y_hip - 96),
                                         (sd * (b['hip'] * 0.72), B.y_hip - 54), (sd * 22, B.y_hip - 54)], dz=3)
            if v > 0.08: c.line(smooth(pk, True, 0.2), lw * 0.45, LINE, 190)
    _glasses_chain(c, sp, B, rows, P, det, t)


def _glasses_chain(c, sp, B, rows, P, det, t):
    """Reading glasses on a thin chain round the neck: on the face (pose.specs 1) the chain loops from behind the ears
    down onto the chest; off (specs 0) the glasses hang on the chest at the bottom of the loop."""
    if not sp.get('chain') or B.ct < -0.1: return
    b = sp['body']
    on = getattr(P, 'specs', 1.0) > 0.5
    yb = B.y_sh + (56 if on else 92)
    sw = 6.0 * getattr(P, 'sec_x', 0.0)
    pts, v = _surf_poly(B, rows, [(-(b['neck'] + 6), B.y_sh - 34), (-(b['neck'] + 2) * 0.8, B.y_sh + 6), (sw, yb),
                                  ((b['neck'] + 2) * 0.8, B.y_sh + 6), (b['neck'] + 6, B.y_sh - 34)], dz=8)
    if v < -0.1: return
    ch = smooth(pts, False, 0.8)
    c.line(ch, c.lw * 0.5, '#b8963e', 230)
    if det >= 1: c.line(ch, c.lw * 0.22, '#f0dc9a', 160)
    if not on:
        X, Y = pts[2]
        s_ = 1.0
        g = c.sub(X, Y + 14, 6.0 * math.sin(t * 0.9) + sw, s_)
        for sd in (-1, 1):
            lens = rrect(sd * 17 - 14, -10, 28, 20, 8)
            g.fill(lens, '#dfe9f2', 60); g.line(lens, g.lw * 0.8, '#3a2f2c')
        g.line(smooth([(-3, -4), (0, -7), (3, -4)], False), g.lw * 0.7, '#3a2f2c')


def _front_housecoat(c, sp, B, rows, P, det, t):
    """Ruth in 1979: a quilted housecoat, a round collar, snaps down the front, a little floral print."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    for sd in (-1, 1):
        cc, v = _surf_poly(B, rows, [(sd * 2, yS - 26), (sd * (b['neck'] + 10), yS - 32), (sd * (b['neck'] + 26), yS - 2),
                                     (sd * 18, yS + 22), (sd * 2, yS + 4)], dz=6)
        if v > -0.2:
            cp = smooth(cc, True, 0.8); c.fill(cp, cl['collar']); c.line(cp, lw * 0.6)
    ed, v = _surf_poly(B, rows, [(4, yS + 4), (4, B.y_hip)], dz=3)
    if v > -0.2: c.line(poly(ed, False), lw * 0.7)
    for k in range(5):
        X, Y, vv, s_ = B.surf(4, yS + 30 + k * (B.y_hip - 40 - yS) / 4.5, 6, False, rows)
        if vv > 0.12: c.fill(oval(X, Y, 3.2 * s_), cl['button'])
    if det >= 1:                                          # quilting: a diamond lattice
        ys, ws, ds = rows
        q = []
        for k in range(-6, 7):
            pts, v = _surf_poly(B, rows, [(k * 28 - 60, yC - 20), (k * 28 + 60, B.y_hip - 10)], dz=1)
            if v > 0.1: q.append(poly(pts, False))
            pts, v = _surf_poly(B, rows, [(k * 28 + 60, yC - 20), (k * 28 - 60, B.y_hip - 10)], dz=1)
            if v > 0.1: q.append(poly(pts, False))
        if q:
            torso, _L, _R = _torso_path(B, rows)
            with c.clip(torso): c.line(_multi(q), lw * 0.28, cl['top_sh'], 150)


def _front_cardi_brown(c, sp, B, rows, P, det, t):
    """Grandpa, 1979: a brown V-neck cardigan over a checked shirt collar, leather buttons, two patch pockets."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    vneck, v = _surf_poly(B, rows, [(-b['neck'] - 6, yS - 30), (b['neck'] + 6, yS - 30), (6, yC + 16), (-6, yC + 16)], dz=2)
    if v > 0.0:
        q = smooth(vneck, True, 0.2); c.fill(q, cl['shirt'])
        if det >= 1:
            with c.clip(q):
                bb = q.getBounds()
                c.line(_multi([poly([(bb.left() + k * 9, bb.top()), (bb.left() + k * 9, bb.bottom())], False) for k in range(20)]), lw * 0.3, cl['shirt_sh'], 140)
                c.line(_multi([poly([(bb.left(), bb.top() + k * 9), (bb.right(), bb.top() + k * 9)], False) for k in range(20)]), lw * 0.3, cl['shirt_sh'], 140)
        for sd in (-1, 1):
            cc, _ = _surf_poly(B, rows, [(sd * 2, yS - 26), (sd * (b['neck'] + 6), yS - 34), (sd * (b['neck'] + 18), yS - 2), (sd * 6, yS + 10)], dz=5)
            cp = poly(cc, True); c.fill(cp, cl['shirt']); c.line(cp, lw * 0.55)
        c.line(q, lw * 0.6)
    for sd in (-1, 1):
        ed, v = _surf_poly(B, rows, [(sd * (b['neck'] + 6), yS - 30), (sd * 6, yC + 16), (sd * 4, B.y_hip - 16)], dz=3)
        if v > -0.2: c.line(poly(ed, False), lw * 2.6, LINE); c.line(poly(ed, False), lw * 1.3, cl['rib'])
        pk, v = _surf_poly(B, rows, [(sd * 24, B.y_hip - 100), (sd * (b['hip'] * 0.78), B.y_hip - 100),
                                     (sd * (b['hip'] * 0.76), B.y_hip - 50), (sd * 24, B.y_hip - 50)], dz=3)
        if v > 0.08: c.shape(smooth(pk, True, 0.2), mix(cl['top'], cl['top_sh'], 0.3), lw * 0.5)
    for k in range(4):
        X, Y, vv, s_ = B.surf(0, yC + 30 + k * (B.y_hip - 60 - yC) / 3.5, 6, False, rows)
        if vv > 0.12: c.shape(oval(X, Y, 5.0 * s_), cl['button'], lw * 0.4)


def _front_pj_dino(c, sp, B, rows, P, det, t):
    """Milo's dinosaur pajamas: a piped collar, buttons, little dinosaurs all over."""
    _front_pj3(c, sp, B, rows, P, det, t)


def _front_tee_jeans(c, sp, B, rows, P, det, t):
    """Milo's T-shirt with a big dinosaur on the chest (the jeans are the legs)."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    nk, v = _surf_poly(B, rows, [(-b['neck'] - 2, B.y_sh - 30), (0, B.y_sh - 14), (b['neck'] + 2, B.y_sh - 30)], dz=3)
    if v > -0.2: c.line(smooth(nk, False), lw * 1.6, cl['trim'])
    X, Y, vv, s_ = B.surf(0, B.y_ch + 20, 3, False, rows)
    if vv > 0.15:
        d = _dino_shape(X, Y, 46 * s_ * max(0.4, abs(B.ct)), 1.0, 1)
        c.fill(d, cl['print_c']); c.line(d, lw * 0.5)
        c.fill(oval(X + 26 * s_ * B.ct, Y - 30 * s_, 2.5 * s_, 2.5 * s_), '#ffffff')


def _front_runner(c, sp, B, rows, P, det, t):
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    nk, v = _surf_poly(B, rows, [(-b['neck'] - 2, B.y_sh - 30), (0, B.y_sh - 12), (b['neck'] + 2, B.y_sh - 30)], dz=3)
    if v > -0.2: c.line(smooth(nk, False), lw * 1.4, cl['trim'])
    for sd in (-1, 1):                                    # side panels
        pp, v = _surf_poly(B, rows, [(sd * b['ch'] * 0.82, B.y_ch - 20), (sd * b['wa'] * 0.86, B.y_hip - 20)], dz=2)
        if v > 0.0: c.line(poly(pp, False), lw * 1.6, cl['trim'], 220)


def _front_scrubs_doc(c, sp, B, rows, P, det, t):
    """Doctor Halverson's scrubs: a V-neck, a chest pocket with pens and a penlight, an old coffee stain, and her ID badge
    clipped (crooked) to the pocket, two little dinosaur stickers on it."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    _vneck(c, sp, B, rows, 46, cl.get('under'))
    pk, v = _surf_poly(B, rows, [(-98, yC - 6), (-50, yC - 6), (-50, yC + 46), (-98, yC + 46)], dz=3)
    if v > 0.05:
        c.line(poly(pk), lw * 0.5)
        for k, cc in enumerate(('#1c1c22', '#d8d6d0', '#3a6ab0')):
            X, Y, vv, s_ = B.surf(-90 + 12 * k, yC - 18, 5, False, rows)
            if vv > 0.1: c.fill(rrect(X - 3 * s_, Y, 6 * s_, 28 * s_, 2), cc); c.line(rrect(X - 3 * s_, Y, 6 * s_, 28 * s_, 2), lw * 0.3)
    if sp.get('stain', True):
        X, Y, vv, s_ = B.surf(34, yC + 36, 3, False, rows)
        if vv > 0.1:
            c.fill(_blob(X, Y, 15 * s_, 11 * s_, 10, 3, 0.45), '#7a5a3a', 110)
            c.fill(_blob(X + 12 * s_, Y + 20 * s_, 5 * s_, 4 * s_, 8, 5, 0.4), '#7a5a3a', 100)
    X, Y, vv, s_ = B.surf(-74, yC + 34, 7, False, rows)
    if vv > 0.12: _badge(c, X, Y, s_ * 1.15, cl, ang=-14.0 if sp.get('crooked', True) else 0.0, stickers=True, det=det)


def _front_raincoat(c, sp, B, rows, P, det, t):
    """The raincoat thrown on over the blue scrubs: open, its collar up a little, a hood behind, wet streaks; the scrubs'
    V-neck and the crooked badge show between its edges."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    op, v = _surf_poly(B, rows, [(-32, yS - 30), (32, yS - 30), (40, B.y_hip), (-40, B.y_hip)], dz=2)
    if v > 0.05:
        q = smooth(op, True, 0.2); c.fill(q, cl['scrubs']); c.fill(_crescent(q, -6, 0), cl['scrubs_sh'], 120)
        vn, _ = _surf_poly(B, rows, [(-24, yS - 30), (0, yS + 30), (24, yS - 30)], dz=3)
        c.fill(poly(vn, True), sp['skin']); c.line(poly(vn, False), lw * 0.8)
        X, Y, vv, s_ = B.surf(-30, yC + 34, 7, False, rows)
        if vv > 0.12: _badge(c, X, Y, s_ * 1.15, cl, ang=-22.0, stickers=True, det=det)
        c.line(q, lw * 0.5)
    for sd in (-1, 1):
        col_, v = _surf_poly(B, rows, [(sd * 30, yS - 36), (sd * (b['neck'] + 30), yS - 44), (sd * (b['neck'] + 44), yS + 4), (sd * 40, yS + 58)], dz=7)
        if v > -0.2:
            cp = smooth(col_, True, 0.4); c.fill(cp, cl['top']); c.fill(_crescent(cp, sd * 4, 0), cl['top_sh'], 120); c.line(cp, lw * 0.7)
        ed, v = _surf_poly(B, rows, [(sd * 40, yS + 58), (sd * 42, B.y_hip)], dz=4)
        if v > -0.2: c.line(poly(ed, False), lw * 1.2)
        pk, v = _surf_poly(B, rows, [(sd * 60, B.y_wa + 10), (sd * 100, B.y_wa + 4)], dz=4)
        if v > 0.05: c.line(poly(pk, False), lw * 0.8)
    if det >= 1:                                         # rain: wet streaks and beads on the shoulders
        st = []
        for k in range(9):
            x0 = (hash01(k, 911) * 2 - 1) * b['sh'] * 0.9; y0 = yS + 10 + 200 * hash01(k, 912)
            pts, v = _surf_poly(B, rows, [(x0, y0), (x0 + 2, y0 + 40 + 30 * hash01(k, 913))], dz=4)
            if v > 0.1: st.append(poly(pts, False))
        if st: c.line(_multi(st), lw * 0.5, cl['top_hi'], 150)


def _front_labscrubs(c, sp, B, rows, P, det, t):
    """A white coat over scrubs (V-neck under it), a badge on the lapel, a stethoscope round the neck, pens in the pocket."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    op, v = _surf_poly(B, rows, [(-30, yS - 30), (30, yS - 30), (14, B.y_ch + 60), (-14, B.y_ch + 60)], dz=2)
    if v > 0.05:
        q = smooth(op, True, 0.2); c.fill(q, cl['scrubs']); c.line(q, lw * 0.5)
        vn, _ = _surf_poly(B, rows, [(-22, yS - 30), (0, yS + 26), (22, yS - 30)], dz=3)
        c.fill(poly(vn, True), sp['skin']); c.line(poly(vn, False), lw * 0.7)
    for sd in (-1, 1):
        lap, v = _surf_poly(B, rows, [(sd * 30, yS - 32), (sd * (b['neck'] + 26), yS - 38), (sd * (b['neck'] + 38), yS + 30), (sd * 14, yC + 60)], dz=6)
        if v > -0.2:
            lp = poly(lap, True); c.fill(lp, cl['top']); c.fill(_crescent(lp, sd * 4, 0), cl['top_sh'], 110); c.line(lp, lw * 0.7)
        ed, v = _surf_poly(B, rows, [(sd * 14, yC + 60), (sd * 16, B.y_hip - 4)], dz=4)
        if v > -0.2: c.line(poly(ed, False), lw * 1.1)
    pk, v = _surf_poly(B, rows, [(52, yC - 6), (100, yC - 6), (98, yC + 44), (54, yC + 44)], dz=3)
    if v > 0.05:
        c.line(poly(pk), lw * 0.5)
        for k, cc in enumerate(('#2a4a9a', '#1c1c22')):
            X, Y, vv, s_ = B.surf(64 + 12 * k, yC - 18, 5, False, rows)
            if vv > 0.1: c.fill(rrect(X - 3 * s_, Y, 6 * s_, 26 * s_, 2), cc)
    X, Y, vv, s_ = B.surf(-74, yC + 10, 7, False, rows)
    if vv > 0.12: _badge(c, X, Y, s_ * 1.05, cl, ang=0.0, stickers=bool(sp.get('stickers')), det=det)
    if sp.get('steth', True): _stethoscope(c, sp, B, rows, det)


def _front_medic(c, sp, B, rows, P, det, t):
    """A paramedic: a navy uniform shirt, reflective bands across the chest, a radio on the shoulder, a patch."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    ed, v = _surf_poly(B, rows, [(0, yS - 26), (0, B.y_hip - 10)], dz=3)
    if v > -0.2: c.line(poly(ed, False), lw * 0.6)
    for yy in (yC + 40, B.y_wa - 10):
        band, v = _surf_poly(B, rows, [(-b['ch'] * 0.97, yy), (b['ch'] * 0.97, yy), (b['ch'] * 0.97, yy + 18), (-b['ch'] * 0.97, yy + 18)], dz=2)
        if v > -0.2:
            q = poly(band, True); c.fill(q, '#c9cc66'); c.fill(rect(-400, yy + 6 + B.bob, 800, 5), '#e8ecee', 0)
            with c.clip(q): c.fill(rect(-400, yy + 6 + B.bob, 800, 6), '#dfe4e8', 220)
            c.line(q, lw * 0.5)
    X, Y, vv, s_ = B.surf(-60, yS + 10, 6, False, rows)
    if vv > 0.12:
        c.shape(rrect(X - 10 * s_, Y - 14 * s_, 20 * s_, 32 * s_, 4 * s_), '#1a1b20', lw * 0.5)
        c.line(poly([(X, Y - 14 * s_), (X + 2 * s_, Y - 30 * s_)], False), lw * 0.8)
    X, Y, vv, s_ = B.surf(70, yC - 6, 6, False, rows)
    if vv > 0.12:
        c.shape(oval(X, Y, 14 * s_, 14 * s_), '#2a5aa8', lw * 0.4)
        c.line(_multi([poly([(X - 7 * s_, Y), (X + 7 * s_, Y)], False), poly([(X, Y - 7 * s_), (X, Y + 7 * s_)], False)]), lw * 0.9, '#ffffff')


def _front_coat_small(c, sp, B, rows, P, det, t):
    """The little girl's coat, too small for her: buttons straining across the front, the sleeves halfway up her arms."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS = B.y_sh
    for sd in (-1, 1):
        cc, v = _surf_poly(B, rows, [(sd * 2, yS - 24), (sd * (b['neck'] + 8), yS - 30), (sd * (b['neck'] + 20), yS - 6), (sd * 22, yS + 18), (sd * 3, yS + 6)], dz=6)
        if v > -0.2: cp = smooth(cc, True, 0.8); c.fill(cp, cl['collar']); c.line(cp, lw * 0.6)
    ed, v = _surf_poly(B, rows, [(6, yS + 6), (6, B.y_hip - 6)], dz=3)
    if v > -0.2: c.line(poly(ed, False), lw * 0.8)
    for k in range(4):
        yy = yS + 30 + k * (B.y_hip - 50 - yS) / 3.5
        X, Y, vv, s_ = B.surf(0, yy, 6, False, rows)
        if vv > 0.12:
            c.shape(oval(X, Y, 5 * s_), cl['button'], lw * 0.4)
            if det >= 1:                                   # strained: little pull lines from each button
                c.line(_multi([poly([(X + 6 * s_ * sd, Y), (X + 22 * s_ * sd, Y - 5 * s_)], False) for sd in (-1, 1)]), lw * 0.35, cl['top_sh'], 180)


def _front_gown_er(c, sp, B, rows, P, det, t):
    """Milo in the ER: a hospital gown with a little print, monitor leads coming out at the collar."""
    _gown_front(c, sp, B, rows, P, det, t)
    if B.ct > -0.1:
        for k, colr in enumerate(('#e04a3a', '#3a8ae0', '#e0c23a')):
            pts, v = _surf_poly(B, rows, [(-20 + 18 * k, B.y_sh - 18), (-40 + 30 * k, B.y_sh - 70), (-90 + 40 * k, B.y_sh - 120)], dz=6)
            if v > -0.2: c.line(smooth(pts, False), c.lw * 0.6, colr, 230)


_FRONTS3.update({'cardi_ruth': _front_cardi_ruth, 'housecoat': _front_housecoat, 'cardi_brown': _front_cardi_brown,
                 'pj_dino': _front_pj_dino, 'tee_jeans': _front_tee_jeans, 'runner': _front_runner, 'scrubs_doc': _front_scrubs_doc,
                 'raincoat': _front_raincoat, 'labscrubs': _front_labscrubs, 'medic': _front_medic, 'coat_small': _front_coat_small,
                 'gown_er': _front_gown_er})
_skirts3_prev = _skirts3


def _skirts3(c, sp, B, P, det, t, rows):
    """Ruth's skirts (her cardigan over a mid-calf skirt; the 1979 housecoat to the calves), the raincoat's and the white
    coats' tails, the gown; seated they drape forward over the thighs."""
    o = sp['outfit']; cl = sp['cloth']; b = sp['body']
    st = clamp(B.sit + 0.8 * B.kneel)
    if o == 'cardi_ruth':
        _skirt(c, sp, B, det, B.y_wa + 10, -190 + 130 * st, b['hip'] * 1.0, b['hip'] * 1.16 + 40 * st, cl['skirt'], cl['skirt_sh'], t=t, P=P)
        return
    if o == 'housecoat':
        _skirt(c, sp, B, det, B.y_wa, -150 + 110 * st, b['hip'] * 1.06, b['hip'] * 1.3 + 44 * st, cl['top'], cl['top_sh'], t=t, P=P)
        return
    if o == 'gown_er':
        _skirt(c, sp, B, det, B.y_wa + 10, -300 + 130 * st, b['hip'] * 1.08, b['hip'] * 1.2 + 50 * st, cl['top'], cl['top_sh'], t=t, P=P)
        return
    if o in ('raincoat', 'labscrubs'):
        X0, Y0, _, _ = B.p3(0, B.y_wa, 0)
        hem = (-300.0 if o == 'raincoat' else -330.0) + 120 * st
        _skirt(c, sp, B, det, B.y_wa, hem, b['wa'] + 14, b['hip'] * 1.32 + 40 * st, cl['top'], cl['top_sh'], t=t, P=P)
        if B.ct > -0.15:
            X1, Y1, _, _ = B.p3(0, hem, 0, upper=False)
            gap = poly([(X0 - 16, Y0), (X0 + 16, Y0), (X1 + 34, Y1 + 8), (X1 - 34, Y1 + 8)])
            c.fill(gap, cl.get('scrubs', cl['trousers']))
            c.line(poly([(X0 - 16, Y0), (X1 - 34, Y1 + 6)], False), c.lw * 0.8); c.line(poly([(X0 + 16, Y0), (X1 + 34, Y1 + 6)], False), c.lw * 0.8)
        return
    return _skirts3_prev(c, sp, B, P, det, t, rows)


# jeans that fall off: pose.sag lowers the waistband (Milo holds them up)
POSE_DEFAULTS.update(sag=0.0, iv=0.0)
_pelvis_prev = _pelvis


def _pelvis(c, sp, B, rows, legc, legsh, det):
    if sp.get('outfit') == 'runner':
        legc, legsh = sp['cloth']['shorts'], sp['cloth']['shorts_sh']
    _pelvis_prev(c, sp, B, rows, legc, legsh, det)
    if sp.get('outfit') == 'tee_jeans':
        cl = sp['cloth']; b = sp['body']
        sag = clamp(getattr(B.P, 'sag', 0.0))
        yb = B.y_hip - 26 + 38 * sag
        band, v = _surf_poly(B, rows, [(-b['hip'] - 4, yb), (b['hip'] + 4, yb), (b['hip'] + 4, yb + 14), (-b['hip'] - 4, yb + 14)], dz=3)
        if v > -0.2:
            q = poly(band, True); c.fill(q, legc); c.line(q, c.lw * 0.6)
            X, Y, vv, s_ = B.surf(0, yb + 7, 5, False, rows)
            if vv > 0.1: c.shape(oval(X, Y, 3.5 * s_), '#c9a24a', c.lw * 0.3)


_draw_legs3_prev = _draw_legs3


def _draw_legs3(c, sp, B, P, det, t, legc, legsh, shoec, order_only=False):
    _draw_legs3_prev(c, sp, B, P, det, t, legc, legsh, shoec, order_only)
    if sp.get('outfit') in ('tee_jeans',) and det >= 1:
        # dinosaur patches on the jeans' knees
        cl = sp['cloth']
        for side in (-1, 1):
            H, K, A, pitch = _leg_chain(sp, B, P, side)
            X, Y, s_, Z = B.p3(K[0], K[1] - B.bob - 6, K[2] + 26, upper=False)
            if B.ct * 1.0 + 0.3 > 0:
                d = _dino_shape(X, Y, 15 * s_ * max(0.45, abs(B.ct)), side, 2 if side > 0 else 1)
                c.fill(d, cl['patch'] if side > 0 else cl['patch2']); c.line(d, c.lw * 0.4)
    if sp.get('outfit') == 'runner':                         # running shorts over the tops of the bare thighs
        cl = sp['cloth']; b = sp['body']
        for side in (-1, 1):
            H, K, A, pitch = _leg_chain(sp, B, P, side)
            h2 = B.p3(H[0], H[1] - B.bob, H[2], upper=False); k2 = B.p3(K[0], K[1] - B.bob, K[2], upper=False)
            m2 = (h2[0] + (k2[0] - h2[0]) * 0.42, h2[1] + (k2[1] - h2[1]) * 0.42)
            sh = _dense_tube([(h2[0], h2[1] - 10), m2], [b['leg'][0] * 1.25 * h2[2], b['leg'][0] * 1.18 * h2[2]])
            c.fill(sh, cl['shorts']); _cloth_shade(c, sh, cl['shorts_sh'], 150, 1.0, 8); c.line(sh, c.lw)


_draw_arm3_prev = _draw_arm3


def _draw_arm3(c, sp, B, P, side, det, t, skin, sh, sleeve, sleeve_sh, light):
    _draw_arm3_prev(c, sp, B, P, side, det, t, skin, sh, sleeve, sleeve_sh, light)
    S, E, Wr = _arm_data(sp, B, P, side)
    pts = [B.p3(*S), B.p3(*E), B.p3(*Wr)]
    P2 = [(p[0], p[1]) for p in pts]
    if sp.get('watch') == side:                              # a wristwatch on the wrist (the pulse beats)
        xw, yw = _arm_pt(P2, 0.955); xb, yb = _arm_pt(P2, 0.9)
        ang = math.degrees(math.atan2(yw - yb, xw - xb)) - 90
        wc = c.sub(xw, yw, ang, 1.0)
        aw = sp['body']['arm'][1] * pts[2][2] * 0.62
        wc.fill(rrect(-aw, -7, aw * 2, 9, 3), '#2b2b30'); wc.line(rrect(-aw, -7, aw * 2, 9, 3), c.lw * 0.5)
        fx = aw * (0.35 if B.ct >= 0 else -0.35)
        wc.shape(oval(fx, -2.5, 8.5, 8.5), '#d9dde2', c.lw * 0.5)
        if det >= 1: wc.line(poly([(fx, -2.5), (fx + 3.5, -5.5)], False), c.lw * 0.35)
    if sp.get('cgm') == side:                                # Milo at 22: a glucose sensor on the back of his upper arm
        xs, ys = _arm_pt(P2, 0.22)
        c.shape(oval(xs, ys, 10, 10), '#f2f2ee', c.lw * 0.5); c.fill(oval(xs, ys, 3.5, 3.5), '#9aa0a8')
    if getattr(P, 'iv', 0.0) > 0.5 and side == 1:            # the IV in the back of Milo's hand: tape, a line going up
        xw, yw = _arm_pt(P2, 0.98)
        c.shape(rrect(xw - 9, yw - 4, 18, 12, 2), '#f2efe6', c.lw * 0.4)
        c.line(smooth([(xw, yw), (xw + 20, yw - 60), (xw + 30, yw - 300), (xw + 26, yw - 900)], False), c.lw * 0.9, '#d8e4ea', 230)
        c.line(smooth([(xw, yw), (xw + 20, yw - 60), (xw + 30, yw - 300), (xw + 26, yw - 900)], False), c.lw * 0.3, '#7a8a94', 200)


def _front_pj_dino(c, sp, B, rows, P, det, t):
    """Milo's dinosaur pajamas: a piped collar, buttons, little dinosaurs all over."""
    if det >= 1:
        torso, L, R = _torso_path(B, rows)
        with c.clip(torso): _dino_print(c, B, rows, sp['cloth'], B.ct < -0.15, 16, 11.0)
    _front_pj3(c, sp, B, rows, P, det, t)


_FRONTS3['pj_dino'] = _front_pj_dino


# ---------------------------------------------------------------------------------------------------- the cast
# Ruth, 70s: stern, neat, frightened underneath. Short silver set curls, pale grey-blue eyes behind reading glasses on a
# gold chain, a thin mouth that presses shut, deep lines; a sage cardigan buttoned to the top over a white blouse collar,
# a charcoal skirt, thick stockings, sensible shoes.
CAST['ruth'] = _v3cast(
    outfit='cardi_ruth', hair='set_curls', sex='f', hh=188.0, m=1.60, glasses=True, chain=True,
    head_ws=[0, 52, 76, 92, 97, 96, 89, 74, 52, 27, 0],
    eye_dx=41, eye_y=-4, eye_r=16.5, iris_c='#7f93a6', lid_rest=0.34, brow_th=6.5, nose_len=25, mouth_w=19,
    skin='#ebc6b0', skin_sh='#c29985', skin_dp='#86605a', blush='#e2a19c', lip='#a97072', lips=0.25,
    hair_c='#dcdad6', brow_c='#9d9790', bags=0.8, age=1.25, lashes=0.3, feet='shoes', ring=1, part=1,
    body=dict(sh=100, ch=104, wa=100, hip=110, arm=(40, 32), leg=(38, 31), neck=33, hand=0.94),
    cloth=dict(top='#7f8f78', top_sh='#5a6855', top_hi='#9eae96', rib='#6c7c66', button='#e8e2d2', blouse='#f6f2ea',
               blouse_sh='#d0c8b8', skirt='#3e3e46', skirt_sh='#28282e', legs='#cfb3a6', legs_sh='#a68a80',
               trousers='#3e3e46', trousers_sh='#28282e', shoes='#3a2c24', shoes_sh='#22180f'))
# Ruth at sunrise in Grandpa's armchair: chest pains since midnight, said nothing (pale, grey lips, sweat at the temple)
CAST['ruth_sick'] = dict(CAST['ruth'], skin='#e2c8bc', skin_sh='#b89c92', lip='#a08a8c', blush='#d9b4b0', bags=1.1)
# Ruth at 40, 1979: dark brown hair in a soft flipped bob, the same eyes and mouth (younger), a quilted rose housecoat
CAST['ruth79'] = _v3cast(
    outfit='housecoat', hair='bob', sex='f', hh=184.0, m=1.62,
    head_ws=[0, 50, 73, 89, 94, 92, 84, 68, 47, 25, 0],
    eye_dx=41, eye_y=-5, eye_r=18.0, iris_c='#7f93a6', lid_rest=0.22, brow_th=7.0, nose_len=23, mouth_w=19,
    skin='#efcab4', skin_sh='#c69c88', skin_dp='#87605a', blush='#e6a29c', lip='#b4686c', lips=0.5,
    hair_c='#5a3826', brow_c='#43291c', bags=0.35, age=0.45, lashes=0.9, feet='flats', ring=1, part=-1,
    body=dict(sh=102, ch=104, wa=92, hip=108, arm=(42, 34), leg=(44, 36), neck=34, hand=0.95),
    cloth=dict(top='#c98f86', top_sh='#9a625c', top_hi='#e2b0a6', collar='#f4ece0', button='#f4ece0', legs='#e8c3ad',
               legs_sh='#c09a86', trousers='#c98f86', trousers_sh='#9a625c', shoes='#7a5a4a', shoes_sh='#4e382c'))
# Grandpa, about 50, 1979: brown hair greying at the temples, a moustache, kind tired eyes; a brown cardigan over a
# checked shirt, grey trousers, slippers. 'grandpa_ghost': grey and still in the waiting room's last row.
CAST['grandpa79'] = _v3cast(
    outfit='cardi_brown', hair='side_short', sex='m', hh=180.0, m=1.78, moustache='#5a4232',
    head_ws=[0, 52, 76, 92, 98, 97, 90, 76, 55, 29, 0],
    eye_dx=42, eye_y=-6, eye_r=17.5, iris_c='#6b5a44', lid_rest=0.3, brow_th=10.0, nose_len=27, mouth_w=21,
    skin='#dfb196', skin_sh='#b2846d', skin_dp='#714e45', blush='#d9958d', lip='#a06e66', stubble='#5a4232', stub=0.25,
    hair_c='#6a4c36', brow_c='#4e3828', bags=0.55, age=0.62, ring=1, part=-1, feet='socks',
    body=dict(sh=124, ch=124, wa=118, hip=112, arm=(52, 44), leg=(56, 46), neck=46, hand=1.04),
    cloth=dict(top='#7a5636', top_sh='#55391f', top_hi='#9a744e', rib='#6a4a2c', button='#3a2818', shirt='#c9c2a8', shirt_sh='#8f876a',
               trousers='#6a6a70', trousers_sh='#48484e', socks='#4e4236', socks_sh='#342c22'))
CAST['grandpa_ghost'] = _ghost_of(CAST['grandpa79'])
# Milo, 7: a light-brown mop that never lies flat, big brown eyes, a gap tooth; the dinosaur pajamas (green, little
# dinosaurs), or a T-shirt with a T-rex and his favourite dinosaur jeans (falling off him: pose.sag); in the ER a gown.
_MILO = dict(hair='cowlick', sex='m', hh=234.0, child=True, m=1.22,
             head_ws=[0, 58, 85, 99, 104, 104, 99, 87, 66, 36, 0],
             eye_dx=40, eye_y=6, eye_r=22.5, iris_c='#6b4a2e', iris_k=0.72, lid_rest=0.08, pupil=1.15, brow_th=6.5, nose_len=13,
             mouth_y=64, mouth_w=16, nose='button', ears=1.15,
             skin='#f1c8ae', skin_sh='#c99a84', skin_dp='#855d55', blush='#f0a097', lip='#c47e78', lips=0.1,
             hair_c='#a77a4c', brow_c='#7a5634', bags=0.12, age=0.0, blink_rate=0.35, lashes=0.4, part=1,
             body=dict(sh=80, ch=78, wa=74, hip=76, arm=(33, 27), leg=(38, 32), neck=29, hand=0.76, arm_k=0.86))
CAST['milo'] = _v3cast(outfit='pj_dino', feet='socks', **_MILO,
                       cloth=dict(top='#8fc79a', top_sh='#5f9a6c', top_hi='#b4e0bc', trim='#f4f7ee', print_c='#3f7a44', print_c2='#e9a23b',
                                  trousers='#8fc79a', trousers_sh='#5f9a6c', socks='#e8e6e0', socks_sh='#bcb8ae'))
CAST['milo_sick'] = dict(CAST['milo'], cracked=1.0, bags=0.6, skin='#ecc6b2', blush='#e0a8a0', lip='#b8858a')
CAST['milo_jeans'] = _v3cast(outfit='tee_jeans', feet='shoes', **_MILO,
                             cloth=dict(top='#e7d24e', top_sh='#b9a32a', top_hi='#f4e48a', trim='#c9b032', print_c='#3f8a4a',
                                        trousers='#4f6f9a', trousers_sh='#344d72', patch='#5fb04e', patch2='#f08a3a',
                                        shoes='#d84a3a', shoes_sh='#9a2e24', sole='#f2f2ee'))
CAST['milo_er'] = _v3cast(outfit='gown_er', feet='socks', **_MILO,
                          cloth=dict(top='#c2d6e2', top_sh='#93aabb', top_hi='#dbe8f0', print_c='#7a96b4', socks='#e8e6e0',
                                     socks_sh='#bcb8ae', band='#f2f2ee', trousers='#c2d6e2', trousers_sh='#93aabb', legs='#f1c8ae',
                                     legs_sh='#c99a84'))
# Milo at 22: the same brown eyes and mop (shorter), lean, a runner; a technical tee and shorts, running shoes, a
# glucose sensor on the back of his left arm, his phone in his hand.
CAST['milo22'] = _v3cast(
    outfit='runner', hair='side_short', sex='m', hh=180.0, m=1.80, cgm=1,
    head_ws=[0, 52, 76, 92, 97, 96, 89, 75, 54, 29, 0],
    eye_dx=41, eye_y=-5, eye_r=18.5, iris_c='#6b4a2e', lid_rest=0.14, brow_th=8.5, nose_len=24, mouth_w=21,
    skin='#e9bea2', skin_sh='#bd8f78', skin_dp='#7a544b', blush='#df9a90', lip='#ad7068', stubble='#6a4c36', stub=0.2,
    hair_c='#8a6038', brow_c='#6a4a2a', bags=0.15, age=0.12, part=1, feet='shoes',
    body=dict(sh=118, ch=110, wa=94, hip=100, arm=(46, 38), leg=(52, 42), neck=40, hand=1.0),
    cloth=dict(top='#2f8f8a', top_sh='#1f6662', top_hi='#4fb0aa', trim='#f2f2ee', trousers='#e9bea2', trousers_sh='#bd8f78',
               shorts='#2a2c34', shorts_sh='#1a1b20', shoes='#f2f2ee', shoes_sh='#b9bcc2', sole='#e05a3a'))
# The narrator at 14 ("I"; never said if boy or girl): dark brown hair, a shaggy cut with curtain bangs over the ears, a
# soft jaw, warm hazel eyes; an oversized burgundy zip hoodie, grey sweatpants, socks.
CAST['narr14'] = _v3cast(
    outfit='hoodie3', hair='shaggy', sex='n', hh=190.0, m=1.62,
    head_ws=[0, 51, 74, 90, 95, 94, 87, 72, 51, 27, 0],
    eye_dx=41, eye_y=-3, eye_r=19.5, iris_c='#7a6a3e', lid_rest=0.12, brow_th=8.0, nose_len=20, mouth_w=18,
    skin='#e2b294', skin_sh='#b7876f', skin_dp='#774f45', blush='#e0968c', lip='#b07468', lips=0.0,
    hair_c='#3a271e', brow_c='#2e1f18', bags=0.15, age=0.02, lashes=0.3, part=0, feet='socks',
    body=dict(sh=104, ch=98, wa=90, hip=96, arm=(43, 35), leg=(47, 39), neck=36, hand=0.95),
    cloth=dict(top='#7a2e3a', top_sh='#55202a', top_hi='#9a4a56', hood='#6d2834', hood_sh='#4c1c24', string='#e9e4d8',
               trousers='#8a8c94', trousers_sh='#64666e', socks='#3a3c44', socks_sh='#26282e'))
# ... at 29, a pediatrician on nights at Larkfield General: the same face (tired, kind), hair a little shorter, ceil blue
# scrubs under a white coat, a badge with a dinosaur sticker (Doctor Halverson's habit), a stethoscope.
CAST['narr29'] = _v3cast(
    outfit='labscrubs', hair='shaggy', sex='n', hh=184.0, m=1.70, stickers=True,
    head_ws=[0, 50, 73, 89, 94, 93, 86, 71, 50, 26, 0],
    eye_dx=41, eye_y=-4, eye_r=18.5, iris_c='#7a6a3e', lid_rest=0.24, brow_th=8.0, nose_len=22, mouth_w=19,
    skin='#e0b092', skin_sh='#b4856d', skin_dp='#744c43', blush='#d8928a', lip='#a87066', lips=0.0,
    hair_c='#3a271e', brow_c='#2e1f18', bags=0.65, age=0.25, lashes=0.3, part=0, feet='clogs', watch=-1,
    body=dict(sh=106, ch=100, wa=92, hip=98, arm=(44, 36), leg=(48, 40), neck=37, hand=0.96),
    cloth=dict(top='#f2f3f0', top_sh='#c6cac6', top_hi='#ffffff', scrubs='#7ea3c6', scrubs_sh='#5a7e9e',
               trousers='#7ea3c6', trousers_sh='#5a7e9e', shoes='#3a4a5e', shoes_sh='#26303e', badge='#ffffff'))
# Doctor Anna Halverson, pediatrician, 40s: kind, quick, tired; dark-blonde hair twisted up in a messy bun with strands
# escaping, warm brown eyes, freckles; blue scrubs with a coffee stain, pens in the pocket, a watch, her badge clipped
# crooked to the pocket with two dinosaur stickers on it. 'halverson_rain': a raincoat over the scrubs, hair soaked flat.
_HAL = dict(sex='f', hh=182.0, m=1.68, head_ws=[0, 50, 72, 88, 93, 91, 83, 67, 47, 25, 0],
            eye_dx=40, eye_y=-6, eye_r=18.5, iris_c='#7a5434', lid_rest=0.2, brow_th=7.5, nose_len=21, mouth_w=21,
            skin='#efc4a8', skin_sh='#c4957f', skin_dp='#835b52', blush='#e69e94', lip='#b87470', lips=0.35,
            brow_c='#7a5a36', bags=0.55, age=0.45, lashes=0.8, part=1, watch=1, freckles=0.6,
            body=dict(sh=106, ch=104, wa=92, hip=106, arm=(43, 35), leg=(47, 39), neck=35, hand=0.96))
_SCRUBS_BLUE = dict(top='#6f9cc8', top_sh='#4c78a2', top_hi='#93bce0', under='#e8e6e0', trousers='#6f9cc8', trousers_sh='#4c78a2',
                    shoes='#e9edf0', shoes_sh='#b6bec4', lanyard='#2d4a8a', badge='#ffffff', scrubs='#6f9cc8', scrubs_sh='#4c78a2')
CAST['halverson'] = _v3cast(outfit='scrubs_doc', hair='gran_bun', feet='clogs', hair_c='#a6804e', **_HAL, cloth=dict(_SCRUBS_BLUE))
CAST['halverson_rain'] = _v3cast(outfit='raincoat', hair='loose', feet='clogs', hair_c='#6a5232', wet=1.0, **_HAL,
                                 cloth=dict(_SCRUBS_BLUE, top='#3e4a3e', top_sh='#262e26', top_hi='#6f7f70'))
CAST['halverson_rain']['cloth'].update(trousers='#6f9cc8', trousers_sh='#4c78a2')
# Mom, 40s, a night-shift nurse at Larkfield General: warm, decisive; dark hair in a low ponytail, brown eyes; wine
# scrubs, a long-sleeved tee under them, a lanyard with her badge, a watch.
CAST['mom_rn'] = _v3cast(
    outfit='scrubs3', hair='pony', sex='f', hh=182.0, m=1.66, watch=1,
    head_ws=[0, 49, 71, 87, 92, 90, 82, 66, 46, 24, 0],
    eye_dx=40, eye_y=-6, eye_r=18.5, iris_c='#5a3e2a', lid_rest=0.2, brow_th=7.5, nose_len=21, mouth_w=20,
    skin='#e4b598', skin_sh='#b88770', skin_dp='#774f45', blush='#df9a90', lip='#a86866', lips=0.45,
    hair_c='#3a2a22', brow_c='#2e2018', bags=0.5, age=0.4, lashes=0.9, part=-1, feet='clogs',
    body=dict(sh=104, ch=104, wa=90, hip=106, arm=(42, 34), leg=(46, 38), neck=34, hand=0.95),
    cloth=dict(top='#8a3a56', top_sh='#62263c', top_hi='#a85a74', trousers='#8a3a56', trousers_sh='#62263c', shoes='#2b2b33',
               shoes_sh='#16161a', lanyard='#2d6a5a', badge='#ffffff'))
# the ER: a calm, firm nurse; a doctor in a white coat over green scrubs; the man holding his chest; two paramedics; the
# cardiologist with a coffee
CAST['er_nurse'] = _v3cast(
    outfit='scrubs3', hair='pony', sex='f', hh=182.0, m=1.70, watch=1,
    head_ws=[0, 50, 72, 88, 93, 91, 83, 67, 47, 25, 0], eye_dx=40, eye_y=-6, eye_r=18.0, iris_c='#2e2018', lid_rest=0.22,
    brow_th=8.5, nose_len=21, mouth_w=21, skin='#8e5f46', skin_sh='#6a4433', skin_dp='#40281f', blush='#b0685a', lip='#7a4a42',
    lips=0.45, hair_c='#1a1311', brow_c='#140f0d', bags=0.4, age=0.4, lashes=0.8, earrings=True, feet='clogs',
    body=dict(sh=112, ch=108, wa=94, hip=106, arm=(44, 36), leg=(50, 40), neck=38, hand=0.96),
    cloth=dict(top='#2c3e66', top_sh='#1c2a48', top_hi='#44588a', trousers='#2c3e66', trousers_sh='#1c2a48', shoes='#e8eef0',
               shoes_sh='#b5c0c4', lanyard='#c9423a', badge='#ffffff'))
CAST['er_doctor'] = _v3cast(
    outfit='labscrubs', hair='doc', sex='m', hh=180.0, m=1.80, glasses=True, watch=-1,
    head_ws=[0, 52, 76, 92, 97, 96, 88, 73, 52, 28, 0], eye_dx=41, eye_y=-6, eye_r=17.5, iris_c='#3a2a20', lid_rest=0.24,
    brow_th=9.0, nose_len=25, mouth_w=21, skin='#c6957a', skin_sh='#9a6c56', skin_dp='#5e4035', blush='#c98a7c', lip='#8f5f55',
    stubble='#2a2020', stub=0.35, hair_c='#2a2220', brow_c='#221a18', bags=0.5, age=0.45, feet='clogs',
    body=dict(sh=120, ch=114, wa=104, hip=104, arm=(48, 40), leg=(56, 46), neck=42, hand=1.0),
    cloth=dict(top='#f4f5f2', top_sh='#c9ccc8', top_hi='#ffffff', scrubs='#5f9a7c', scrubs_sh='#3f7a5c', trousers='#5f9a7c',
               trousers_sh='#3f7a5c', shoes='#2a2320', shoes_sh='#16110f', badge='#ffffff'))
CAST['chest_man'] = _v3cast(
    outfit='jacket3', hair='thin', sex='m', hh=180.0, m=1.78,
    head_ws=[0, 54, 79, 95, 101, 101, 95, 82, 61, 33, 0], eye_dx=42, eye_y=-6, eye_r=17.0, iris_c='#5a6a7a', lid_rest=0.3,
    brow_th=10.0, nose_len=27, mouth_w=21, skin='#e2b39a', skin_sh='#b48670', skin_dp='#744e45', blush='#e09088', lip='#a46c66',
    stubble='#7a7068', stub=0.4, hair_c='#8a8076', brow_c='#6a6058', bags=0.7, age=0.75, feet='boots',
    body=dict(sh=130, ch=134, wa=134, hip=124, arm=(54, 46), leg=(58, 48), neck=50, hand=1.04),
    cloth=dict(top='#5e6a4a', top_sh='#3e4830', top_hi='#7e8a66', collar='#3e2e22', shirt='#a8442e', shirt_sh='#7a2e1e',
               trousers='#3c4250', trousers_sh='#262a34', shoes='#3a2a1e', shoes_sh='#22180f', button='#2a2018'))
_MEDIC = dict(top='#1f2c4a', top_sh='#141d33', top_hi='#33446a', trousers='#1f2c4a', trousers_sh='#141d33', shoes='#121214',
              shoes_sh='#08080a')
CAST['medic'] = _v3cast(
    outfit='medic', hair='side_short', sex='m', hh=178.0, m=1.82,
    head_ws=[0, 53, 77, 91, 96, 95, 88, 74, 53, 29, 0], eye_dx=42, eye_y=-7, eye_r=18.0, iris_c='#4a6a8a', lid_rest=0.2,
    brow_th=9.5, nose_len=24, mouth_w=21, skin='#e8b89c', skin_sh='#bb8a72', skin_dp='#784f45', blush='#df938a', lip='#a46c66',
    stubble='#6a4a30', stub=0.3, hair_c='#7a5430', brow_c='#5a3e24', bags=0.35, age=0.3, feet='boots',
    body=dict(sh=126, ch=120, wa=106, hip=106, arm=(52, 42), leg=(60, 48), neck=46, hand=1.02), cloth=dict(_MEDIC))
CAST['medic2'] = _v3cast(
    outfit='medic', hair='pony', sex='f', hh=182.0, m=1.68,
    head_ws=[0, 50, 72, 88, 93, 91, 83, 67, 47, 25, 0], eye_dx=40, eye_y=-6, eye_r=18.5, iris_c='#3b2a1e', lid_rest=0.2,
    brow_th=7.5, nose_len=21, mouth_w=20, skin='#c99677', skin_sh='#9d6f57', skin_dp='#5e4035', blush='#d38a7d', lip='#a0605c',
    lips=0.4, hair_c='#2a1c16', brow_c='#22160f', bags=0.35, age=0.25, lashes=0.8, feet='boots',
    body=dict(sh=108, ch=106, wa=92, hip=106, arm=(44, 36), leg=(50, 40), neck=36, hand=0.95), cloth=dict(_MEDIC))
CAST['cardio'] = _v3cast(
    outfit='labscrubs', hair='bob', sex='f', hh=182.0, m=1.64, glasses=True, steth=True,
    head_ws=[0, 50, 72, 88, 93, 91, 83, 67, 47, 25, 0], eye_dx=40, eye_y=-6, eye_r=17.5, iris_c='#4a6a5a', lid_rest=0.26,
    brow_th=7.0, nose_len=22, mouth_w=21, skin='#f0c9b2', skin_sh='#c49d8a', skin_dp='#86605a', blush='#e6a29c', lip='#b06a6e',
    lips=0.4, hair_c='#c9c6c0', brow_c='#8a8680', bags=0.5, age=0.75, lashes=0.6, part=1, feet='flats',
    body=dict(sh=104, ch=104, wa=94, hip=106, arm=(42, 34), leg=(46, 38), neck=34, hand=0.95),
    cloth=dict(top='#f4f5f2', top_sh='#c9ccc8', top_hi='#ffffff', scrubs='#7a6a9a', scrubs_sh='#5a4a7a', trousers='#3c3f48',
               trousers_sh='#26282e', shoes='#3a2a24', shoes_sh='#22180f', badge='#ffffff'))
# the waiting room's people, grey and still, holding paper tickets: a man holding his chest (an old overcoat and tie),
# a woman holding her side, a teenager holding his arm in his lap, a little girl in a coat too small for her
CAST['ghost_chest'] = _ghost_of(_v3cast(
    outfit='labcoat3', hair='doc', sex='m', hh=180.0, m=1.76, head_ws=[0, 53, 78, 94, 100, 100, 94, 80, 58, 31, 0],
    eye_dx=42, eye_y=-6, eye_r=17.0, iris_c='#5a5a5a', lid_rest=0.3, brow_th=9.5, nose_len=27, mouth_w=21,
    skin='#e0b49c', skin_sh='#b48670', skin_dp='#744e45', blush='#d9908a', lip='#a06e66', stubble='#6a6460', stub=0.3,
    hair_c='#9a948c', brow_c='#7a746c', bags=0.8, age=0.85, feet='shoes',
    body=dict(sh=122, ch=124, wa=120, hip=114, arm=(50, 42), leg=(56, 46), neck=46, hand=1.02),
    cloth=dict(top='#5a5048', top_sh='#3e3630', top_hi='#7a7068', shirt='#d8d2c4', shirt_sh='#aaa496', tie='#6a2a2a',
               trousers='#3c3a3e', trousers_sh='#28262a', shoes='#2a2220', shoes_sh='#16110f', badge='#5a5048')))
CAST['ghost_side'] = _ghost_of(_v3cast(
    outfit='cardigan3', hair='bob', sex='f', hh=182.0, m=1.64, head_ws=[0, 49, 71, 87, 92, 90, 82, 66, 46, 24, 0],
    eye_dx=40, eye_y=-6, eye_r=18.0, iris_c='#5a5a5a', lid_rest=0.3, brow_th=7.0, nose_len=21, mouth_w=20,
    skin='#e8c0a8', skin_sh='#be927e', skin_dp='#80564f', blush='#e0a09a', lip='#a86a6e', lips=0.4,
    hair_c='#5a4436', brow_c='#45342a', bags=0.6, age=0.5, lashes=0.8, part=-1, feet='flats',
    body=dict(sh=104, ch=104, wa=90, hip=106, arm=(42, 34), leg=(46, 38), neck=34, hand=0.95),
    cloth=dict(top='#6a7a8a', top_sh='#4a5a6a', top_hi='#8a9aaa', rib='#5a6a7a', button='#e8e2d2', blouse='#e8e2d2',
               blouse_sh='#c0b8a8', trousers='#4a4650', trousers_sh='#322e38', shoes='#2a2220', shoes_sh='#16110f')))
CAST['ghost_teen'] = _ghost_of(_v3cast(
    outfit='hoodie3', hair='side_short', sex='m', hh=186.0, m=1.72, head_ws=[0, 51, 74, 90, 95, 94, 87, 72, 51, 27, 0],
    eye_dx=41, eye_y=-4, eye_r=19.0, iris_c='#5a5a5a', lid_rest=0.3, brow_th=8.5, nose_len=22, mouth_w=19,
    skin='#c99c80', skin_sh='#9a7260', skin_dp='#5f4442', blush='#d88f86', lip='#a16a62', hair_c='#2a2220', brow_c='#221a18',
    bags=0.5, age=0.05, part=1, feet='shoes',
    body=dict(sh=110, ch=104, wa=94, hip=98, arm=(46, 38), leg=(50, 42), neck=38, hand=0.98),
    cloth=dict(top='#3a5a7a', top_sh='#2a4058', top_hi='#5a7a9a', hood='#34506c', hood_sh='#243a50', string='#e9e4d8',
               trousers='#3a3c44', trousers_sh='#24262c', shoes='#e8e4dc', shoes_sh='#a8a39a')))
_GIRL = dict(CAST['june']); _GIRL.update(outfit='coat_small', feet='maryjane', hair='pigtails', hair_c='#4a3426', brow_c='#3a2818',
                                        iris_c='#5a5a5a', v3=True)
CAST['ghost_girl'] = _ghost_of(_GIRL)
CAST['ghost_girl']['cloth'] = {k: _greyed(v, 0.85) for k, v in dict(
    top='#b84a4a', top_sh='#8a3232', top_hi='#d86a6a', collar='#e8e2d2', button='#2a2220', trousers='#e8c8b8', trousers_sh='#c0a090',
    legs='#e8c8b8', legs_sh='#c0a090', socks='#e8e4dc', socks_sh='#b8b4ac', shoes='#1c1a1f', shoes_sh='#0c0b0e', tie='#8a3232').items()}
CAST['ghost_girl']['outfit'] = 'coat_small'
_LEGS3['coat_small'] = 'skin'

DOCTOR_CAST = ('later', 'ruth', 'ruth_sick', 'ruth79', 'grandpa79', 'grandpa_ghost', 'milo', 'milo_sick', 'milo_jeans', 'milo_er',
               'milo22', 'narr14', 'narr29', 'halverson', 'halverson_rain', 'mom_rn', 'er_nurse', 'er_doctor', 'chest_man',
               'medic', 'medic2', 'cardio', 'ghost_chest', 'ghost_side', 'ghost_teen', 'ghost_girl')
_DL_FACES = (None, 'grandpa_ghost', 'ghost_chest', 'ghost_girl', 'ruth', 'narr14')


# ====================================================================================================== PROPS
# (centimetres, origin = where the hand grips; see PROPS3 in characters_bunny.py)
def _p_receiver(c, det, t, P=None):
    """The kitchen wall phone's handset (cream plastic, 1980s): the earpiece toward -y, the mouthpiece toward +y, the
    coiled cord leaving the mouthpiece end (the scene draws the cord with draw_coil_cord between receiver_cord_end() and
    the base)."""
    o = 5.0                                      # the hand holds it nearer the earpiece end
    body = smooth([(-1.6, -7.5 + o), (1.6, -7.5 + o), (1.8, 7.5 + o), (-1.8, 7.5 + o)], True, 0.4)
    ear = smooth([(-3.4, -11.5 + o), (3.4, -11.5 + o), (3.8, -7.0 + o), (2.0, -5.6 + o), (-2.0, -5.6 + o), (-3.8, -7.0 + o)], True, 0.7)
    mouth = smooth([(-3.6, 5.8 + o), (3.6, 5.8 + o), (3.4, 11.0 + o), (0.0, 12.2 + o), (-3.4, 11.0 + o)], True, 0.7)
    for p_ in (body, ear, mouth):
        c.fill(p_, '#e9e0c8'); c.fill(_crescent(p_, 0.6, 0.4), '#bfb398', 200); c.line(p_, c.lw * 0.6)
    if det >= 1:
        c.line(_multi([oval(-1.2 + 1.2 * k, -9.2 + o, 0.35, 0.35) for k in range(3)]), c.lw * 0.3, '#7a7058')
        c.line(_multi([oval(-1.2 + 1.2 * k, 9.4 + o, 0.35, 0.35) for k in range(3)]), c.lw * 0.3, '#7a7058')


def _p_card(c, det, t, P=None, back=False):
    """Grandma's seven rules: a small card the colour of weak tea, typed on a typewriter (front), or its back: faded 1979
    ink, signed 'Doctor Later' (back)."""
    r = rrect(-5.0, -3.6, 10.0, 7.2, 0.25)
    c.fill(r, '#d9c38e')
    c.radial(r, 0, 0, 8.0, [(0, '#e6d4a4', 0), (0.7, '#b9a066', 60), (1, '#8a7240', 160)])
    if det >= 1: c.texture(r, 'grunge', 0.3, 0.06)
    if not back:
        if det >= 1:
            c.line(_multi([poly([(-4.2, -2.6 + 0.78 * k), (-4.2 + 7.6 * (0.55 + 0.45 * hash01(k, 951)), -2.6 + 0.78 * k)], False)
                           for k in range(8)]), c.lw * 0.45, '#2a241c', 200)
    else:
        _block_text(c, 'DOCTOR', 0.5, -0.4, 1.0, '#4a4060', 150, wobble=0.6, seed=3)
        _block_text(c, 'LATER', 0.8, 1.2, 1.0, '#4a4060', 150, wobble=0.6, seed=5)
        c.line(smooth([(-3.6, 2.4), (-1.0, 2.6), (2.4, 2.2), (3.6, 2.6)], False), c.lw * 0.4, '#4a4060', 140)
    # the old tape that held it inside the cabinet, torn
    c.fill(poly([(-5.4, -4.0), (-3.0, -3.8), (-3.2, -2.6), (-5.6, -2.9)]), '#e8dcb0', 170)
    c.line(r, c.lw * 0.45)


def _p_match(c, det, t, P=None, lit=True):
    """A kitchen match, pinched near its end; lit: a small flame that flickers."""
    c.line(poly([(0.0, 1.0), (0.0, -4.4)], False), c.lw * 1.8, '#3a2a1a')
    c.line(poly([(0.0, 1.0), (0.0, -4.4)], False), c.lw * 1.1, '#e0c68e')
    c.fill(oval(0.0, -4.7, 0.42, 0.55), '#a03020'); c.line(oval(0.0, -4.7, 0.42, 0.55), c.lw * 0.3)
    if lit:
        f = 1.0 + 0.12 * math.sin(t * 23.0) + 0.08 * math.sin(t * 37.0 + 1.0)
        c.glow(0.0, -5.6, 4.5 * f, 4.5 * f, '#ffb04a', 110)
        fl = smooth([(0.0, -4.6), (0.55 * f, -5.4), (0.2, -6.9 * f), (0.0, -7.6 * f), (-0.3, -6.6 * f), (-0.55 * f, -5.4)], True, 0.8)
        c.fill(fl, '#ffcf5a'); c.fill(oval(0.0, -5.1, 0.3, 0.45), '#ffffff', 220)


def _p_matchbox(c, det, t, P=None):
    b = rrect(-2.6, -1.8, 5.2, 3.6, 0.3)
    c.fill(b, '#c8452e'); c.fill(rect(-2.6, -0.4, 5.2, 0.8), '#e8d6a8'); c.line(b, c.lw * 0.5)


def _p_note(c, det, t, P=None):
    """Milo's lab results with Doctor Halverson's warning signs in marker at the bottom (folded once, held by an edge)."""
    r = poly([(-10.5, -2), (10.5, -2), (10.5, 25.7), (-10.5, 25.7)], True)
    c.fill(r, '#f7f6f0'); c.line(r, c.lw * 0.5)
    if det >= 1:
        c.line(_multi([poly([(-8.5, 1.5 + 1.1 * k), (-8.5 + 15 * (0.4 + 0.6 * hash01(k, 961)), 1.5 + 1.1 * k)], False) for k in range(7)]),
               c.lw * 0.3, '#6a7280', 200)
        c.line(_multi([poly([(-8.5, 11.5 + 2.0 * k), (-8.5 + 16 * (0.5 + 0.5 * hash01(k, 963)), 11.8 + 2.0 * k)], False) for k in range(6)]),
               c.lw * 0.9, '#1a1a22', 230)
    c.line(poly([(-10.5, 9.0), (10.5, 9.0)], False), c.lw * 0.25, '#c8c6be')


def _p_marker(c, det, t, P=None):
    b = rrect(-0.8, -6.5, 1.6, 12.0, 0.6)
    c.fill(b, '#1d1e24'); c.fill(rect(-0.8, -1.0, 1.6, 2.0), '#e8e8e4'); c.line(b, c.lw * 0.5)
    c.fill(poly([(-0.5, 5.5), (0.5, 5.5), (0.2, 7.0), (-0.2, 7.0)]), '#101014')


def _p_ticket(c, det, t, P=None):
    _dl_ticket(c, 0.0, 0.0, 0.0, 1.0, getattr(P, 'dl_ticket', 'MILO') if P is not None else 'MILO', det,
               ink=0.0 if (P is not None and getattr(P, 'dl_ticket', '') == '') else 1.0)


def _p_bottle(c, det, t, P=None):
    """Milo's water bottle (a kid's plastic bottle, blue cap), gripped round the middle."""
    b = smooth([(-3.2, -8.0), (3.2, -8.0), (3.4, 9.0), (2.4, 10.5), (-2.4, 10.5), (-3.4, 9.0)], True, 0.5)
    c.fill(b, '#cfe6f2', 210)
    c.fill(rect(-3.1, -2.0 + 4.0 * (1 - clamp(getattr(P, 'drink_lvl', 0.6) if P is not None else 0.6)), 6.2, 12.0), '#8ec4e6', 150)
    c.line(b, c.lw * 0.6)
    cap = rrect(-2.0, -11.2, 4.0, 3.4, 0.6)
    c.fill(cap, '#2f6ab0'); c.line(cap, c.lw * 0.5)


def _p_mug(c, det, t, P=None):
    """A coffee mug held by its body (Grandma at sunrise in 1979; a nurse's mug)."""
    m = rrect(-4.2, -4.8, 8.4, 9.6, 1.2)
    c.fill(m, '#efe8d8'); c.fill(_crescent(m, 1.0, 0), '#c8bfa8', 200); c.line(m, c.lw * 0.6)
    h = smooth([(4.0, -2.6), (6.4, -2.0), (6.6, 1.6), (4.0, 2.4)], False, 0.8)
    c.line(h, c.lw * 1.6, LINE); c.line(h, c.lw * 0.8, '#efe8d8')
    c.fill(oval(0.0, -4.6, 4.0, 0.9), '#4a2e1c')
    if det >= 1:
        for k in range(2):
            sx = -1.2 + 2.4 * k + 0.6 * math.sin(t * 1.4 + k)
            c.line(smooth([(sx, -5.6), (sx + 0.8, -8.0), (sx - 0.4, -10.5)], False), c.lw * 0.35, '#ffffff', 90)


def _p_cup(c, det, t, P=None):
    """A paper coffee cup with a lid (the cardiologist's)."""
    b = poly([(-3.6, -5.0), (3.6, -5.0), (2.8, 6.0), (-2.8, 6.0)], True)
    c.fill(b, '#f2efe8'); c.fill(poly([(-3.4, -1.5), (3.4, -1.5), (3.15, 2.0), (-3.15, 2.0)]), '#8a5a3a'); c.line(b, c.lw * 0.6)
    lid = rrect(-4.0, -6.6, 8.0, 1.8, 0.6)
    c.fill(lid, '#1d1e22'); c.line(lid, c.lw * 0.5)


def _p_vial(c, det, t, P=None):
    """A capped blood-test tube with a printed label (no blood shown: the label faces us)."""
    b = rrect(-0.7, -4.0, 1.4, 8.0, 0.6)
    c.fill(b, '#e8eef2'); c.fill(rect(-0.7, -1.6, 1.4, 4.5), '#f6f6f2'); c.line(b, c.lw * 0.4)
    c.fill(rrect(-0.85, -5.4, 1.7, 1.8, 0.3), '#a03a6a'); c.line(rrect(-0.85, -5.4, 1.7, 1.8, 0.3), c.lw * 0.4)
    if det >= 1: c.line(_multi([poly([(-0.5, -1.0 + 0.6 * k), (0.4, -1.0 + 0.6 * k)], False) for k in range(4)]), c.lw * 0.2, '#5a6470')


def _p_cell(c, det, t, P=None):
    """A smartphone held by its edges, screen toward the holder (the back faces us)."""
    r = rrect(-3.6, -7.4, 7.2, 14.8, 1.0)
    c.fill(r, '#1c1d22'); c.grad(r, -3.6, 0, 3.6, 0, [(0, '#3a3d47', 255), (0.4, '#1c1d22', 255), (1, '#0b0b0e', 255)])
    c.line(r, c.lw * 0.6)
    c.fill(rrect(-2.8, -6.6, 2.6, 3.6, 0.6), '#0d0d10')


def _p_glucose(c, det, t, P=None):
    """Milo at 22 checks his blood sugar on his phone: the screen toward us, a gentle green graph, the number."""
    r = rrect(-3.6, -7.4, 7.2, 14.8, 1.0)
    c.fill(r, '#1c1d22'); c.line(r, c.lw * 0.6)
    s = rrect(-3.1, -6.8, 6.2, 13.6, 0.7)
    c.fill(s, '#f4f6f4')
    c.fill(rect(-3.1, -1.0, 6.2, 2.6), '#d8f0d8')
    c.line(smooth([(-2.6, 0.8), (-1.4, 0.2), (-0.2, 0.6), (1.0, -0.2), (2.4, 0.2)], False), c.lw * 0.6, '#2e9a4a')
    _block_text(c, '104', 0.0, -3.6, 1.6, '#1d2a22', 255)


def _p_keys(c, det, t, P=None):
    for k, (x, y, a) in enumerate(((-0.6, 1.8, 10), (0.8, 2.2, -14))):
        kc = c.sub(x, y, a, 1.0)
        kc.fill(poly([(-0.3, -1.0), (0.3, -1.0), (0.3, 3.0), (0.9, 3.0), (0.9, 2.2), (0.3, 2.2), (0.3, 1.6), (-0.3, 1.6)]), '#c9a24a')
    c.shape(oval(0.0, -0.4, 1.4, 1.4), '#b0b4ba', c.lw * 0.4); c.fill(oval(0.0, -0.4, 0.8, 0.8), '#141418')


PROPS3.update({
    'receiver': (_p_receiver, 'grip', (0.0, 0.0)),
    'card': (_p_card, 'upright', (0.0, 0.0)),
    'card_back': (lambda c, d, t, P=None: _p_card(c, d, t, P, back=True), 'upright', (0.0, 0.0)),
    'match': (lambda c, d, t, P=None: _p_match(c, d, t, P, lit=False), 'upright', (0.0, 0.0)),
    'match_lit': (_p_match, 'upright', (0.0, 0.0)),
    'matchbox': (_p_matchbox, 'upright', (0.0, 0.0)),
    'note': (_p_note, 'upright', (0.0, 0.0)),
    'marker': (_p_marker, 'grip', (0.0, 0.0)),
    'ticket': (_p_ticket, 'upright', (0.0, 0.0)),
    'bottle': (_p_bottle, 'upright', (0.0, 0.0)),
    'mug': (_p_mug, 'upright', (0.0, 0.0)),
    'cup': (_p_cup, 'upright', (0.0, 0.0)),
    'vial': (_p_vial, 'upright', (0.0, 0.0)),
    'cell': (_p_cell, 'upright', (0.0, 0.0)),
    'cell_glucose': (_p_glucose, 'upright', (0.0, 0.0)),
    'keys': (_p_keys, 'hang', (0.0, 0.0)),
})


def draw_coil_cord(pen, x0, y0, x1, y1, px_per_cm, sag=0.35, t=0.0, colr='#d9cfb4', coils=None):
    """The phone's coiled cord between two design points (the handset's mouthpiece end and the base): a helix that hangs
    in a catenary-ish sag (sag 0..1 of the span) and sways a little."""
    L = math.hypot(x1 - x0, y1 - y0)
    n = coils or max(8, int(L / (px_per_cm * 1.6)))
    pts = []
    r = 0.9 * px_per_cm
    for i in range(n * 6 + 1):
        u = i / (n * 6.0)
        x = x0 + (x1 - x0) * u; y = y0 + (y1 - y0) * u + math.sin(PI * u) * L * sag * 0.5
        x += math.sin(t * 1.3) * 4.0 * math.sin(PI * u)
        a = 2 * PI * n * u
        pts.append((x + math.cos(a) * r * 0.3, y + math.sin(a) * r))
    p = poly(pts, False)
    pen.line(p, max(1.6, 0.55 * px_per_cm), '#3a3424')
    pen.line(p, max(0.8, 0.3 * px_per_cm), colr)


def draw_wheelchair(pen, x, y_floor, px_per_cm, facing=1.0, t=0.0, roll=0.0, detail=2):
    """A hospital wheelchair seen from the side (facing +1 = its seat faces screen right). Returns the handles' grip point
    (for the pusher's hands) and the seat point."""
    k = px_per_cm; f = 1.0 if facing >= 0 else -1.0
    X = lambda u: x + f * u * k                        # noqa: E731
    Y = lambda v: y_floor - v * k                      # noqa: E731
    big = oval(X(-8), Y(30), 30 * k, 30 * k)
    pen.line(big, 2.6 * k * 0.4 + 2, '#2a2c32')
    for j in range(6):
        a = roll / 30.0 + j * PI / 3
        pen.line(poly([(X(-8), Y(30)), (X(-8) + math.cos(a) * 28 * k, Y(30) + math.sin(a) * 28 * k)], False), 0.5 * k + 1, '#8a8e96')
    pen.fill(oval(X(30), Y(7), 7 * k, 7 * k), '#2a2c32')
    frame = [(X(-22), Y(95)), (X(-22), Y(48)), (X(26), Y(48)), (X(30), Y(10))]
    pen.line(poly(frame, False), 2.2 * k * 0.6 + 2, '#9aa0a8')
    pen.fill(rrect(min(X(-22), X(24)), Y(52), 46 * k, 6 * k, 2 * k), '#2d3e66')
    pen.fill(rrect(min(X(-25), X(-19)), Y(96), 6 * k, 46 * k, 2 * k), '#2d3e66')
    pen.line(poly([(X(-22), Y(95)), (X(-34), Y(97))], False), 2.0 * k + 1, '#1a1b20')
    return (X(-34), Y(97)), (X(2), Y(52))


def draw_steering_wheel(pen, cx, cy, r, angle=0.0, detail=2):
    """A car's steering wheel seen from the driver's seat (slightly from above): returns the 10 and 2 o'clock grip points."""
    a = math.radians(angle)
    rim = oval(cx, cy, r, r * 0.86)
    pen.line(rim, r * 0.16, '#1c1d22'); pen.line(rim, r * 0.06, '#3a3c44')
    for k in (0, 1, 2):
        aa = a + PI / 2 + k * 2 * PI / 3
        pen.line(poly([(cx, cy), (cx + math.cos(aa) * r * 0.92, cy + math.sin(aa) * r * 0.8)], False), r * 0.1, '#1c1d22')
    pen.fill(oval(cx, cy, r * 0.25, r * 0.22), '#24262c')
    g10 = (cx + math.cos(a + PI * 1.17) * r, cy + math.sin(a + PI * 1.17) * r * 0.86)
    g2 = (cx + math.cos(a - PI * 0.17) * r, cy + math.sin(a - PI * 0.17) * r * 0.86)
    return g10, g2


# ====================================================================================================== EXPRESSIONS
EXPR.update({
    'stern': dict(brow_angry=0.32, brow_sad=0.12, m_press=0.5, smile=-0.22, squint=0.14, pupil=0.9),
    'stern_afraid': dict(brow_angry=0.12, brow_sad=0.6, brow_up=0.25, m_press=0.6, smile=-0.28, wide=0.22, tremble=0.12),
    'careful_smile': dict(smile=0.3, m_press=0.25, brow_sad=0.32, brow_up=0.18, squint=0.08),
    'kind_smile': dict(smile=0.6, teeth=0.25, squint=0.2, brow_up=0.15),
    'exhausted': dict(eye_open=0.76, brow_sad=0.5, brow_up=0.1, smile=-0.1, h_nod=0.05),
    'pleading': dict(brow_sad=0.9, brow_up=0.6, wide=0.22, smile=-0.18),
    'set_jaw': dict(brow_angry=0.5, brow_sad=0.1, m_press=0.7, squint=0.16),
    'thirsty': dict(eye_open=0.8, brow_sad=0.55, brow_up=0.15, m_open=0.07, smile=-0.15),
    'sleepy': dict(eye_open=0.5, brow_sad=0.3, h_nod=0.12, m_open=0.03),
    'dazed': dict(eye_open=0.86, pupil=1.3, brow_sad=0.22, m_open=0.12, lock=0.0),
    'asking': dict(brow_up=0.5, brow_sad=0.35, wide=0.3),
    'asking_hard': dict(brow_angry=0.45, brow_up=0.3, brow_sad=0.2, wide=0.45, pupil=0.8),
    'tired_kind': dict(eye_open=0.84, smile=0.25, brow_sad=0.28),
    'pale_hidden': dict(smile=0.12, m_press=0.5, brow_sad=0.38, pale=0.5, sweat=0.15),
    'warm': dict(smile=0.45, squint=0.15, brow_up=0.1),
    'calm_firm': dict(brow_angry=0.18, m_press=0.32, smile=0.05),
    'grief_still': dict(eye_open=0.84, brow_sad=0.7, smile=-0.3, still=0.5, wet=0.6),
    'waiting': dict(eye_open=0.86, still=1.0, brow_sad=0.22, m_press=0.3, pupil=0.95),
    'brave': dict(m_press=0.6, brow_up=0.32, brow_sad=0.2, squint=0.22),
    'focused': dict(brow_angry=0.22, squint=0.15, m_press=0.25),
    'fierce_kind': dict(brow_angry=0.42, squint=0.12, m_press=0.4, smile=0.08),
    'relief': dict(smile=0.55, brow_sad=0.45, brow_up=0.3, wet=0.7, squint=0.12),
})
EXPR_DOCTOR = ('stern', 'stern_afraid', 'careful_smile', 'kind_smile', 'exhausted', 'pleading', 'set_jaw', 'thirsty', 'sleepy',
               'dazed', 'asking', 'asking_hard', 'tired_kind', 'pale_hidden', 'warm', 'calm_firm', 'grief_still', 'waiting',
               'brave', 'focused', 'fierce_kind', 'relief')


# ====================================================================================================== ACTING: DOCTOR LATER
# He is staged like everyone else: a = CH.Acting('later', seed, height=CH.height_px('later', ppm)).place(chair_x, floor_y),
# then a.perch(seat_y, 'plastic'). World targets (reach, look) are design points, (actor, part) or PropTracks.
_acting_place_prev = Acting.place


def _acting_place_doc(self, x, y_feet, height=None):
    r = _acting_place_prev(self, x, y_feet, height)
    if self.sp.get('later'):
        self.base.update(dl_px0=float(self.x0), dl_py0=float(self.y0), dl_ph=float(self.height))
    return r


Acting.place = _acting_place_doc


def _later_pts(P):
    """Named design-frame points (body units, as _body_point returns) of Doctor Later for pose P."""
    view = _DLView(P); R = _dl_rig(P)
    pr = lambda q: tuple(v * _DLU for v in view.p(q)[:2])      # noqa: E731
    hd = _DLHead(R, view)
    out = {'head': (hd.X * _DLU, hd.Y * _DLU)}
    ex, ey, _ = hd.p(np.array([0.0, -1.0, _DL_FACE[2]]))
    out['eyes'] = (ex * _DLU, ey * _DLU)
    cn = _DL_CONE
    u = np.array([0.0, -math.cos(cn['lean']), math.sin(cn['lean'])])
    tx, ty, _ = hd.p(np.array([0.0, cn['base_y'], cn['base_z']]) + u * cn['L'])
    out['cone_tip'] = (tx * _DLU, ty * _DLU)
    out['crown'] = out['cone_tip']
    out['mouth'] = tuple(v * _DLU for v in hd.p(np.array([0.0, 5.6, _DL_FACE[2] * 0.85]))[:2])
    out['chest'] = pr(R['spine'][3] + np.array([0.0, 0.0, 9.0])); out['neck'] = pr(R['neck'][1]); out['hip'] = pr(R['spine'][0])
    out['lap'] = pr((R['legs'][1][0] + R['legs'][-1][0]) / 2 + np.array([0.0, -8.0, 12.0]))
    for s, nm in ((1, 'l'), (-1, 'r')):
        arm = R['arms'][s]
        h3 = _dl_hand3(R, view, s, P)
        out['wrist_' + nm] = pr(arm['W'])
        out['hand_' + nm] = pr(arm['W'] + h3['f'] * 5.0)
        out['tips_' + nm] = pr((h3['fingers'][0][-1] + h3['fingers'][1][-1]) / 2)
        out['shoulder_' + nm] = pr(arm['S']); out['elbow_' + nm] = pr(arm['J'][0])
        Hp, K, A, T = R['legs'][s]
        out['knee_' + nm] = pr(K); out['foot_' + nm] = pr(T)
    return out


_body_point_prev = _body_point


def _body_point(self, P, part):
    if self.sp.get('later'):
        pts = _later_pts(P)
        return pts.get(part, pts['head'])
    return _body_point_prev(self, P, part)


def _later_place_P(P, s):
    """Placement for the pose's own staging (used when a pose is drawn in a bust or a different layout)."""
    return P.dl_px0 + P.dx, P.dl_py0 + P.dy, s


_acting_look_at_prev = _acting_look_at


def _acting_look_at(self, t0, target, t1=None, dur=0.4, z=None, body=0.0, head=1.0, fade=0.35, eyes_lead=0.07, max_head=0.85):
    if not self.sp.get('later'):
        return _acting_look_at_prev(self, t0, target, t1, dur, z, body, head, fade, eyes_lead, max_head)
    dur = max(dur, 0.6)                                         # his head never darts: it turns slowly, patiently
    def fn(P, t):
        w_e = _env(t, t0, t1, eyes_lead + 0.1, fade)
        w_h = _env(t, t0, t1, dur, fade * 1.6) * head
        if w_e <= 0.001 and w_h <= 0.001: return
        tx, ty = _target_xy(target, t)
        ox, oy, s = _origin(self, P)
        hx, hy = _later_pts(P)['head']
        dx = (tx - (ox + hx * s)) / s; dy = (ty - (oy + hy * s)) / s
        dz = (0.6 * abs(dx) + 60.0) if z is None else float(z)
        yaw = math.atan2(dx, dz) / (PI / 2)
        pitch = math.atan2(dy, math.hypot(dx, max(dz, 1.0)))
        if body > 0: P.turn += (yaw - P.turn) * body * w_h
        want_h = clamp(yaw - P.turn, -1.1, 1.1)
        P.h_turn += (want_h - P.h_turn) * w_h
        P.h_nod += (clamp(pitch / 0.6 * 0.8, -0.6, 0.8) - P.h_nod) * w_h
        P.look_x += (clamp((yaw - P.turn - P.h_turn) * 1.6, -1, 1) - P.look_x) * w_e
        P.look_y += (clamp((pitch - P.h_nod * 0.6) * 1.4, -1, 1) - P.look_y) * w_e
        P._gaze = max(getattr(P, '_gaze', 0.0), w_e)
    return _acting_post(self, t0 - dur, None if t1 is None else t1 + fade * 1.6, fn)


Acting.look_at = _acting_look_at


def _later_reach(self, t0, side, target, t1=None, dur=1.2, z=0.0, shape='reach', fade=0.8, arc=0.0):
    """His hand goes to a world target (design point, callable, (actor, part), PropTrack) by t0 + dur and stays there
    until t1, then returns over fade. Out of reach, the arm unfolds unnaturally long (a second elbow opening like a
    folding rule). arc lifts the path in the middle (design px) so a long reach rises over things."""
    pre = 'dl_l' if side > 0 else 'dl_r'
    hp = 'hl_' if side > 0 else 'hr_'
    def fn(P, t):
        u = prog(t, t0, t0 + dur)
        if u <= 0: return
        w_out = 1.0 if t1 is None else 1.0 - ease_in_out(prog(t, t1, t1 + fade))
        if w_out <= 0: return
        tx, ty = _target_xy(target, t)
        # start from where the hand is (the pose before this reach), travel on an eased arc
        e = ease_in_out(u)
        w = min(1.0, e * 1.0001) * w_out
        lift = arc * math.sin(PI * clamp(u)) * w_out
        setattr(P, pre + 'w', max(getattr(P, pre + 'w'), w))
        setattr(P, pre + 'x', tx); setattr(P, pre + 'y', ty - lift); setattr(P, pre + 'z', z)
        if shape is not None and w > 0.3: setattr(P, hp + 'shape', shape)
    return _acting_post(self, t0, None if t1 is None else t1 + fade, fn)


_acting_reach_to_prev = _acting_reach_to


def _acting_reach_to(self, t0, side, target, t1=None, dur=0.55, z=0.0, contact='palm', shape='grip', fade=0.45, antic_k=0.06,
                     prop=None, lean=True, press=None, rot=None):
    if self.sp.get('later'):
        return _later_reach(self, t0, side, target, t1, max(dur, 0.8), z, shape if shape != 'grip' else 'grip', max(fade, 0.6))
    return _acting_reach_to_prev(self, t0, side, target, t1, dur, z, contact, shape, fade, antic_k, prop, lean, press, rot)


Acting.reach_to = _acting_reach_to
_acting_foot_gap_prev = Acting.foot_gap


def _acting_foot_gap_doc(self, t):
    if self.sp.get('later'):
        R = _dl_rig(self.at(t))
        return max(0.0, min(-(R['legs'][s][3][1]) for s in (-1, 1)) - 1.5) * self.height / 1000.0 * _DLU
    return _acting_foot_gap_prev(self, t)


Acting.foot_gap = _acting_foot_gap_doc
_grip_point_prev = Acting.grip_point


def _grip_point_doc(self, t, side, prop, post=True):
    if self.sp.get('later'):
        P = self.at(t) if post else self._raw(t, False)
        ox, oy, s = _origin(self, P)
        X, Y = _later_pts(P)['tips_l' if side > 0 else 'tips_r']
        return ox + X * s, oy + Y * s
    return _grip_point_prev(self, t, side, prop, post)


Acting.grip_point = _grip_point_doc

_PERCH = {'plastic': (45.0, 0.85), 'armchair': (42.0, 1.0), 'bench': (46.0, 1.0), 'car': (30.0, 1.0), 'low': (34.0, 1.0)}


def _later_perch(self, seat_y=None, kind='plastic', t0=-INF, t1=None, knee=None, hands=('lap', 'pen'), props=True):
    """Fold him onto a seat whose top is at design y seat_y (None = the kind's usual height): plastic waiting-room chair,
    Grandpa's armchair, the bus-stop bench, the car's back seat ('car': pass seat_y = the cushion, place() at the car
    floor), 'low'. His knees fold up above his head; his hands rest (hands = (left, right): 'lap' holds the clipboard
    upright on his knees, 'pen' holds the pen at his chest, 'floor' flat on the carpet, 'knee', 'arm'); props gives him
    the clipboard (left) and the pen (right)."""
    hs0, kk0 = _PERCH.get(kind, _PERCH['plastic'])
    ppc = self.height / (_DL_M * 100.0)
    hs = hs0 if seat_y is None else max(20.0, (self.y0 - seat_y) / ppc)
    kk = kk0 if knee is None else knee
    lh, rh = hands
    def fn(P, t):
        P.dl_seat = hs; P.dl_knee = kk
        P.dl_lrest = lh; P.dl_rrest = rh
        if props:
            if lh == 'lap' and P.hl_prop is None: P.hl_prop = 'clipboard'; P.hl_shape = 'clip'
            if rh == 'pen' and P.hr_prop is None: P.hr_prop = 'pen'; P.hr_shape = 'pen'
            if lh == 'pen' and P.hl_prop is None: P.hl_prop = 'pen'; P.hl_shape = 'pen'
            if rh == 'lap' and P.hr_prop is None: P.hr_prop = 'clipboard'; P.hr_shape = 'clip'
        for sd, rest in ((1, lh), (-1, rh)):
            if rest == 'floor': setattr(P, ('hl_' if sd > 0 else 'hr_') + 'shape', 'flat')
    return self._add(t0, t1, fn)


def _later_hands(self, t0, left=None, right=None, t1=None):
    """Change where his hands rest from t0 (to t1): 'lap', 'pen', 'floor', 'knee', 'arm' (props follow: set them with
    hold_prop / set if they change hands)."""
    def fn(P, t):
        if t < t0 or (t1 is not None and t >= t1): return
        if left: P.dl_lrest = left
        if right: P.dl_rrest = right
    return self._add(t0, None if t1 is None else t1, fn, late=True)


def _later_click_pen(self, times, side=-1):
    """Click the pen (the thumb presses the plunger) at each time: 'pen_click' events."""
    times = sorted(times)
    def fn(P, t):
        v = 0.0
        for tc in times:
            d = t - tc
            if -0.06 < d < 0.0: v = max(v, 1.0 + d / 0.06)
            elif 0.0 <= d < 0.12: v = max(v, 1.0 - d / 0.12)
        if v > 0: P.dl_click = max(P.dl_click, v)
    self._add(times[0] - 0.2, times[-1] + 0.2, fn)
    return [self._ev(tc, 'pen_click', 0.0, pan=0.0) for tc in times]


def _later_write(self, t0, t1, rate=6.0):
    """The pen scratching on his empty clipboard (unseen in the hallway, heard): 'pen_scratch' events and a small writing
    jitter of the pen hand."""
    def fn(P, t):
        w = _env(t, t0, t1, 0.2, 0.2)
        if w <= 0: return
        P.dl_rw = max(P.dl_rw, 0.0)
        P.hr_rot += 6.0 * w * math.sin(t * rate * 2 * PI)
    self._add(t0, t1 + 0.3, fn)
    evs = []
    tt = t0
    while tt < t1:
        evs.append(self._ev(tt, 'pen_scratch', -3.0, pan=0.0, dur=min(0.5, t1 - tt)))
        tt += 0.55
    return evs


def _later_tilt(self, t0, deg=18.0, dur=1.4, t1=None, fade=1.2):
    """Tilt his head (slowly: he is very patient). 'He tilted his head.'"""
    def fn(P, t):
        w = ease_in_out(prog(t, t0, t0 + dur)) * (1.0 if t1 is None else 1.0 - ease_in_out(prog(t, t1, t1 + fade)))
        if w > 0: P.h_tilt += deg * w
    return self._add(t0, None if t1 is None else t1 + fade, fn)


def _later_tear_ticket(self, t0, side, slot, text_='MILO', dur=1.8, offer_to=None, offer_t=None, offer_dur=1.4):
    """Reach (without standing up) all the way across the room to the red ticket machine's slot, pinch the ticket, tug:
    it tears off ('ticket_tear') and is held between two long fingers; with offer_to (a target) the hand then brings it
    out toward that point and holds it there. Returns (tear time, events)."""
    tt = t0 + dur + 0.25
    hp = 'hl_' if side > 0 else 'hr_'
    tug = lambda t: (lambda p: (p[0], p[1] + 10.0 * math.sin(PI * clamp((t - tt + 0.12) / 0.24))))(_target_xy(slot, t))  # noqa: E731
    t_hold1 = tt + 0.25 if offer_to is not None else None
    _later_reach(self, t0, side, tug, t1=t_hold1, dur=dur, z=0.0, shape='pinch', fade=0.9, arc=60.0)
    def fn(P, t):
        if t >= tt:
            setattr(P, hp + 'prop', 'ticket'); setattr(P, hp + 'shape', 'offer'); P.dl_ticket = text_
    self._add(tt, None, fn, late=True)
    if offer_to is not None:
        to = tt + 0.2 if offer_t is None else offer_t
        _later_reach(self, to, side, offer_to, t1=None, dur=offer_dur, z=40.0, shape='offer', fade=0.9)
    return tt, [self._ev(tt, 'ticket_tear', 0.0, pan=0.0)]


def _later_offer(self, t0, side, target, t1=None, dur=1.4, z=40.0, text_=None):
    """Hold the ticket out between two long fingers toward a point (the narrator's hands)."""
    hp = 'hl_' if side > 0 else 'hr_'
    def fn(P, t):
        if t >= t0 and (t1 is None or t < t1 + 0.5):
            setattr(P, hp + 'prop', 'ticket'); setattr(P, hp + 'shape', 'offer')
            if text_ is not None: P.dl_ticket = text_
    self._add(t0, None, fn, late=True)
    return _later_reach(self, t0, side, target, t1, dur, z, 'offer', 0.9)


def _later_take_wrist(self, t0, side, other, other_side=1, t1=None, dur=1.1):
    """His long cold fingers close round the other actor's wrist (the inside of it) and stay; draw him AFTER the other
    actor (or draw_later_arm on top) so the fingers wrap over the wrist. Returns the contact time."""
    part = 'wrist_l' if other_side > 0 else 'wrist_r'
    _later_reach(self, t0, side, (other, part), t1, dur, 30.0, 'grip', 0.6)
    return t0 + dur


def _later_count(self, t, n=1):
    """One count of the pulse ('One...'): the head dips a little, the fingers press. A 'pulse_count' marker event (no
    sound of its own: the hold music and the clock slow down with it)."""
    def fn(P, tt):
        d = tt - t
        if d < -0.1 or d > 1.2: return
        k = math.exp(-max(d, 0.0) * 3.0) * clamp((d + 0.1) / 0.15)
        P.dl_count = max(P.dl_count, k)
        P.dl_lf = max(P.dl_lf, k); P.dl_rf = max(P.dl_rf, k)
    self._add(t - 0.2, t + 1.3, fn)
    return [self._ev(t, 'pulse_count', 0.0, pan=0.0, n=n)]


def _later_loosen_tape(self, t0, t1, frm=1.0, to=0.0, flinch=True):
    """With every question the tape comes looser, strip by strip: dl_tape steps from frm to to between t0 and t1 (each
    strip unwinds over 0.3 s); a 'tape_peel' event per strip and (flinch) a recoil on the first."""
    n = len(_DL_RINGS) - 1
    k0 = int(round((1.0 - frm) * n)); k1 = int(round((1.0 - to) * n))
    steps = max(1, k1 - k0)
    times = [t0 + (t1 - t0) * (i / max(1, steps - 1) if steps > 1 else 0.0) for i in range(steps)]
    def fn(P, t):
        if t < t0 - 0.01:
            return
        done = 0.0
        for i, tk in enumerate(times):
            done += ease_in_out(prog(t, tk, tk + 0.3))
        P.dl_tape = min(P.dl_tape, 1.0 - (k0 + done) / n)
    self._add(t0, None, fn)
    evs = [self._ev(tk, 'tape_peel', -2.0, pan=0.0, strip=i) for i, tk in enumerate(times)]
    if flinch: evs += _later_flinch(self, t0)
    return evs


def _later_faces(self, keys, fade=0.55):
    """The faces under the tape shift: keys [(t, index)] (0 his own, 1 Grandpa, 2 a stranger, 3 a little girl, 4 Ruth,
    5 the narrator), each a crossfade over fade s."""
    keys = sorted(keys)
    def fn(P, t):
        v = keys[0][1] if t >= keys[0][0] else P.dl_face
        for i in range(1, len(keys)):
            ta, a = keys[i - 1]; tb, b = keys[i]
            if t >= tb: v = b
            elif t >= tb - fade: v = a + (b - a) * ease_in_out((t - (tb - fade)) / fade)
        P.dl_face = v
    return self._add(keys[0][0] - fade, None, fn)


def _later_flinch(self, t, amp=1.0):
    """He flinches as if a question were a light: a fast recoil (head back and turned away, arms up toward the face),
    a slow return. A 'flinch' event (a dry cloth rustle)."""
    def fn(P, tt):
        d = tt - t
        if d < 0 or d > 2.5: return
        k = (1.0 - math.exp(-d * 18.0)) * math.exp(-d * 1.6) * amp
        P.dl_flinch = max(P.dl_flinch, clamp(k))
    self._add(t - 0.05, t + 2.6, fn, real=True)
    return [self._ev(t, 'flinch', -4.0, pan=0.0)]


def _later_roof(self, roof_y, t0=-INF, t1=None):
    """A roof over him (the car): roof_y in design px; his head bends over against it, the cone lying along it."""
    ppc = self.height / (_DL_M * 100.0)
    h = max(40.0, (self.y0 - roof_y) / ppc)
    return self._add(t0, t1, lambda P, t: setattr(P, 'dl_roof', h))


Acting.perch = _later_perch
Acting.later_hands = _later_hands
Acting.click_pen = _later_click_pen
Acting.write_scratch = _later_write
Acting.tilt_head = _later_tilt
Acting.reach_far = _later_reach
Acting.tear_ticket = _later_tear_ticket
Acting.offer = _later_offer
Acting.take_wrist = _later_take_wrist
Acting.count = _later_count
Acting.loosen_tape = _later_loosen_tape
Acting.faces = _later_faces
Acting.flinch_light = _later_flinch
Acting.bend_to_roof = _later_roof


def later_point(actor, t, part):
    """Design-space point of one of Doctor Later's parts at time t (head, eyes, mouth, cone_tip, chest, lap, hand_l/_r,
    tips_l/_r (the pinch), wrist_l/_r, elbow_l/_r, shoulder_l/_r, knee_l/_r, foot_l/_r)."""
    return actor.where(t, part)


def chair_rock(t, t0, amp=4.0, decay=1.4, freq=1.15):
    """Angle (deg) of a chair still rocking a little after something very tall got up from it at t0 (the set rotates the
    chair about its front feet; pass it as pose.dl_rock to draw him rocking in it)."""
    d = t - t0
    if d < 0: return 0.0
    return amp * math.exp(-d / decay) * math.sin(2 * PI * freq * d)


def draw_later_arm(pen, actor, t, side, light=None, detail=None):
    """Draw only one of Doctor Later's arms (with its hand and what it holds) where draw() puts it: lay his fingers over
    something drawn after him (the narrator's wrist)."""
    P = actor.at(t)
    ox, oy, s = _origin(actor, P)
    c = Ctx(pen, skia.Matrix(), _lw_for(CAST['later']['hh'] * s)).sub(ox, oy, 0.0, s).sub(0.0, 0.0, 0.0, _DLU)
    det = _auto_detail(pen, CAST['later']['hh'] * s) if detail is None else detail
    view = _DLView(P); R = _dl_rig(P)
    arm = R['arms'][side]
    pr = lambda q: view.p(q)[:2]                       # noqa: E731
    p2 = [pr(q) for q in [arm['S']] + arm['J'] + [arm['W']]]
    ws = [6.4] + [4.6] * len(arm['J']) + [3.0]
    for j in range(len(p2) - 1): _dl_tube(c, [p2[j], p2[j + 1]], [ws[j], ws[j + 1]], det, light, 2, 40 + 5 * j + side)
    _dl_sleeve(c, R, view, side, det, light)
    _dl_draw_hand(c, R, view, side, P, det, light, t)


def draw_later_far(pen, x, y_floor, height, pose, t=0.0, lamp=(0.0, 0.0), flicker=1.0, colr='#05060a'):
    """Doctor Later far off (the bus stop at the end of the street): a black folded silhouette with a thin cold rim from
    the flickering streetlight above (lamp = the light's design point; flicker 0..1 its brightness)."""
    side = 1 if lamp[0] >= x else -1
    draw_silhouette(pen, 'later', x, y_floor, height, pose, t=t, colr=colr, a=0.97, rim='#cfe0ff', rim_a=0.55 * clamp(flicker),
                    rim_side=side)


# ====================================================================================================== ACTING: PEOPLE
def _p_receiver_ear(self, t0, t1=None, side=1, tilt_out=0.0, fade=0.5, tilt=6.0, toward=None):
    """The wall phone's handset at the ear (prop 'receiver': earpiece at the ear, mouthpiece toward the mouth).
    tilt_out 0..1 tips it away from the ear; with toward=(other actor) the handset comes out to a point between her ear
    and theirs, so they can hear too (Ruth, rule 1: 'she tilted it so I could hear')."""
    pre = 'hl_' if side > 0 else 'hr_'
    def fn(P, t):
        w = _env(t, t0, t1, fade, fade, ease)
        if w <= 0: return
        k = clamp(tilt_out) if toward is None else 0.0
        self._arm(P, side, w, 30.0 * k, -20.0 + 30.0 * k, 40.0 + 60.0 * k, 'grip', up=1.0, prop='receiver')
        setattr(P, pre + 'ear', max(getattr(P, pre + 'ear'), w * (1.0 - 0.45 * k)))
        setattr(P, pre + 'rot', getattr(P, pre + 'rot') - side * 28.0 * k * w)
        P.h_tilt += tilt * side * w * (1.0 - k)
        P.shrug += 0.06 * w
    self._add(t0, None if t1 is None else t1 + fade, fn)
    if toward is not None and tilt_out > 0:
        def tgt(t):
            ax, ay = self.where(t, 'head', post=False); bx, by = toward.where(t, 'head', post=False)
            return ax + (bx - ax) * 0.38, ay + (by - ay) * 0.38 + 6.0 * self.height / 1000.0
        def fn2(P, t):
            w = _env(t, t0, t1, fade, fade, ease) * clamp(tilt_out)
            if w > 0: setattr(P, pre + 'ear', getattr(P, pre + 'ear') * (1.0 - w))
        self._add(t0, None if t1 is None else t1 + fade, fn2)
        self.reach_to(t0, side, tgt, t1=t1, dur=fade + 0.3, z=60.0, contact='grip', shape='grip', fade=fade, prop='receiver',
                      rot=-side * 70.0)
        self.look_at(t0 + 0.2, (toward, 'eyes'), t1=t1, dur=0.5)
    return self


def receiver_cord_end(actor, t, side=1):
    """Design point of the mouthpiece end of the handset held in a hand (draw_coil_cord from here to the phone base)."""
    gx, gy = actor.grip_point(t, side, 'receiver')
    wx, wy = actor.where(t, 'wrist_l' if side > 0 else 'wrist_r')
    d = math.hypot(gx - wx, gy - wy) or 1.0
    ppc = actor.height / (actor.sp.get('m', 1.7) * 100.0)
    return gx - (gx - wx) / d * 16.0 * ppc, gy - (gy - wy) / d * 16.0 * ppc


def _p_tap(self, t0, side, target, n=3, gap=0.3, z=0.0, kind='card_tap'):
    """Tap a target with the index finger n times (Grandma tapping the yellow card inside the medicine cabinet)."""
    t_in = t0 + 0.55
    times = [t_in + i * gap for i in range(n)]
    t_end = times[-1] + 0.35
    def tgt(t):
        x, y = _target_xy(target, t)
        v = 0.0
        for tk in times:
            d = t - tk
            if -0.14 < d < 0.0: v = max(v, 1.0 + d / 0.14)
            elif 0.0 <= d < 0.1: v = max(v, 1.0 - d / 0.1)
        return x, y - 8.0 * (1.0 - v) * (self.height / 700.0)
    self.reach_to(t0, side, tgt, t1=t_end, dur=0.55, z=z, contact='tips', shape='point', fade=0.5)
    return [self._ev(tk, kind, -2.0, pan=0.0) for tk in times]


def _p_pull_cord(self, t0, side, jack, dur=1.6, z=20.0):
    """Reach down to the phone jack low on the wall, grip the cord and yank it out ('cord_yank'), the hand flying back."""
    ty = t0 + 0.65 * dur
    ppc = self.height / (self.sp.get('m', 1.7) * 100.0)
    def tgt(t):
        x, y = _target_xy(jack, t)
        k = ease_out_cubic(prog(t, ty, ty + 0.18))
        return x - 28.0 * ppc * k * (1 if self.at(t0).turn >= 0 else -1), y - 6.0 * ppc * k     # back toward her body
    self.reach_to(t0, side, tgt, t1=ty + 0.35, dur=0.55 * dur, z=z, contact='grip', shape='grip', fade=0.6)
    return [self._ev(ty, 'cord_yank', 0.0, pan=0.0)]


def _p_strike_match(self, t0, side=1, dur=1.4):
    """Strike a kitchen match on its box in front of the chest: the box in one hand, the match in the other, one quick
    stroke and it lights ('match_strike'); the lit match stays in the hand (prop 'match_lit'). Returns the strike time."""
    ts = t0 + 0.6 * dur
    box_side = -side
    self.hold_prop('matchbox', box_side, t0, ts + 0.9)
    self.hold_prop('match', side, t0, ts)
    self.hold_prop('match_lit', side, ts, None)
    self.reach(t0, ts + 0.9, box_side, out=-40.0, down=150.0, fwd=170.0, shape='grip', up=0.0, fade=0.4)
    def fn(P, t):
        w = _env(t, t0, None, 0.4, 0.4)
        stroke = ease_in_out(prog(t, ts - 0.12, ts + 0.06))
        self._arm(P, side, w, -30.0 + 70.0 * stroke, 140.0 - 25.0 * stroke, 185.0, 'pinch', up=0.0)
    self._add(t0, None, fn)
    return ts, [self._ev(ts, 'match_strike', 0.0, pan=0.0)]


def _p_slide_under(self, t0, side, track, door_x, floor_y, dur=2.2):
    """Kneel at the door and slide a paper under it: the hand brings the held PropTrack down to the floor at the door and
    pushes it through; it is gone under the door at the end ('paper_slide'). Returns the time it is gone."""
    self.kneel_down(t0, 0.8, knees=0)
    ppc = self.height / (self.sp.get('m', 1.7) * 100.0)
    tg = t0 + dur
    def tgt(t):
        u = ease_in_out(prog(t, t0 + 0.9, tg))
        dirn = 1.0 if door_x >= self.x0 else -1.0
        return door_x - dirn * (18.0 - 26.0 * u) * ppc, floor_y - 3.0 * ppc
    self.reach_to(t0 + 0.3, side, tgt, t1=tg, dur=0.7, z=40.0, contact='grip', shape='flat', fade=0.6, prop=track.name)
    track.gone(tg)
    pre = 'hl_' if side > 0 else 'hr_'
    self._add(tg, None, lambda P, t: setattr(P, pre + 'prop', None) if t >= tg else None, late=True)
    return tg, [self._ev(t0 + 1.0, 'paper_slide', 0.0, pan=0.0)]


def _p_write_marker(self, t0, t1, side, paper, z=60.0):
    """Write on a paper (held against the door, a clipboard) with a marker: small, careful letter strokes, line by line;
    'marker_write' events."""
    ppc = self.height / (self.sp.get('m', 1.7) * 100.0)
    def tgt(t):
        x, y = _target_xy(paper, t)
        u = max(0.0, t - t0)
        line = int(u / 1.6)
        ph = (u % 1.6) / 1.6
        return x + (-6.0 + 12.0 * ph) * ppc + 0.8 * ppc * math.sin(u * 19.0), y + (line % 4) * 2.2 * ppc + 0.6 * ppc * math.sin(u * 23.0)
    self.reach_to(t0, side, tgt, t1=t1, dur=0.5, z=z, contact='tips', shape='grip', fade=0.5, prop='marker')
    self.hold_prop('marker', side, t0 - 0.5, t1 + 0.5)
    evs, tt = [], t0 + 0.5
    while tt < t1:
        evs.append(self._ev(tt, 'marker_write', -4.0, pan=0.0)); tt += 0.8
    return evs


def _p_take_pulse(self, t0, side, other, other_side=1, t1=None, dur=0.7):
    """Two fingers on the inside of the other's wrist, the other arm up in front with her watch, eyes on the watch
    (Doctor Halverson counting Milo's pulse)."""
    part = 'wrist_l' if other_side > 0 else 'wrist_r'
    self.reach_to(t0, side, (other, part), t1=t1, dur=dur, z=50.0, contact='tips', shape='point', fade=0.5)
    self.reach(t0 + 0.2, t1, -side, out=-30.0, down=140.0, fwd=190.0, shape='relaxed', up=0.0, fade=0.5)
    self.look_at(t0 + 0.5, (self, 'wrist_l' if -side > 0 else 'wrist_r'), t1=t1, dur=0.35)
    return self


def _p_carry(self, t0, child, t1=None, fade=0.6):
    """Carry a child in front: the near arm under the child's seat, the far arm round its back; the child's arms on the
    carrier's shoulders, legs dangling, head on the shoulder. Draw with draw_carry_child (it places the child)."""
    self._carry = child
    for side, part, sh in ((1, 'hip', 'grip'), (-1, 'chest', 'open')):
        self.reach_to(t0, side, (child, part), t1=t1, dur=fade, z=40.0, contact='palm', shape=sh, fade=fade, lean=False)
    child._carried_by = self
    def fn(P, t):
        w = _env(t, t0, t1, fade, fade)
        if w <= 0: return
        P.sit = max(P.sit, 0.85 * w); P.crouch = 0.0
        for side in (-1, 1): child._arm(P, side, w, 40.0, 90.0, 160.0, 'relaxed', up=0.0)
        P.h_tilt += 14.0 * w; P.h_nod += 0.2 * w
        P.lid_l = max(P.lid_l, 0.4 * w); P.lid_r = max(P.lid_r, 0.4 * w)
    child._add(t0, None if t1 is None else t1 + fade, fn)
    return self


def carry_anchor(carrier, t):
    """Design (x, y_feet) to draw a carried child so its seat sits in the carrier's arms against the chest."""
    cx, cy = carrier.where(t, 'chest', post=False)
    bx, by = carrier.where(t, 'belly', post=False)
    P = carrier._raw(t, False)
    face = math.sin(P.turn * PI / 2)
    s = carrier.height / 1000.0
    return cx + face * 120.0 * s, by + 40.0 * s


def draw_carry_child(pen, carrier, child, t, light=None, clight=None):
    """Draw a child carried in front (carrier.carry(t0, child)): the carrier with its far arm, the child sitting in its
    arms (child placed at carry_anchor), then the carrier's near arm over the child."""
    x, y = carry_anchor(carrier, t)
    ch_h = child.height
    # the child's figure: seated pose, its seat at the anchor
    child.place(x, y + 0.36 * ch_h * 0.0)
    Pc = child.at(t)
    Pcar = carrier.at(t)
    near = 1 if math.sin(Pcar.turn * PI / 2) <= 0 else -1
    Pa = Pcar.copy()
    draw(pen, carrier.who, carrier.x0, carrier.y0, carrier.height, Pa, light=light, t=t)
    draw(pen, child.who, x, y, ch_h, Pc, light=clight or light, t=t)
    draw_arm(pen, carrier.who, near, Pcar, x=carrier.x0, y_feet=carrier.y0, height=carrier.height, light=light, t=t)


def _p_drive(self, t0, t1, g10, g2, fade=0.5, steer=None):
    """Both hands on the steering wheel at ten and two (grip points from draw_steering_wheel; callables follow a turning
    wheel), small corrections, eyes ahead."""
    self.reach_to(t0, 1, g2, t1=t1, dur=fade, z=120.0, contact='grip', shape='grip', fade=fade)
    self.reach_to(t0, -1, g10, t1=t1, dur=fade, z=120.0, contact='grip', shape='grip', fade=fade)
    return self


def _p_rock(self, t0, t1=None, amount=1.0, rate=0.45, fade=0.8, hum=True):
    """Rock back and forth sitting on the floor with a child in the lap (Grandma on the kitchen floor), humming."""
    def fn(P, t):
        w = _env(t, t0, t1, fade, fade) * amount
        if w <= 0: return
        ph = math.sin(2 * PI * rate * (t - t0))
        P.lean += 0.12 * w * ph; P.h_nod += 0.06 * w * ph; P.h_tilt += 3.0 * w * ph
        P.sway += 4.0 * w * ph
    self._add(t0, None if t1 is None else t1 + fade, fn)
    if hum: self.hum(t0, t1, 0.8, fade, rate * 2.2)
    return self


def _p_breathe_fast(self, t0, t1=None, rate=0.9, fade=0.8):
    """Deep, fast breathing (like running in his sleep): the chest heaves, the shoulders lift on each breath, the mouth
    opens a little on the in-breath. 'breath_fast' events on each breath."""
    def fn(P, t):
        w = _env(t, t0, t1, fade, fade)
        if w <= 0: return
        ph = 0.5 + 0.5 * math.sin(2 * PI * (t - t0) / rate)
        P.breath = lerp(P.breath, 0.05 + 1.25 * ph, w)
        P.shrug += 0.22 * w * ph; P.m_open = max(P.m_open, 0.16 * w * ph); P.h_nod -= 0.04 * w * ph
    self._add(t0, None if t1 is None else t1 + fade, fn)
    evs, tt = [], t0
    end = t1 if t1 is not None else t0 + 8.0
    while tt < end:
        evs.append(self._ev(tt + rate * 0.25, 'breath_fast', -6.0, pan=0.0)); tt += rate
    return evs


POSE_DEFAULTS.update(bottle_tilt=0.0, drink_lvl=0.6)
_held_prop_prev = _held_prop


def _held_prop(c, sp, prop, wx, wy, hang, hs, side, det, t, P, front_part=False):
    if prop in ('cell', 'phone') and _ear_weight(P, side) > 0.5:
        if front_part: return
        k = 10.0 / sp.get('m', 1.7); hk = sp['body'].get('hand', 1.0)
        reach = 30.0 * hs * hk
        gx_, gy_ = wx + math.sin(math.radians(-hang)) * reach, wy + math.cos(math.radians(hang)) * reach
        pc = c.sub(gx_, gy_, -side * 12.0, k); pc.lw = c.lw / k
        r = rrect(-3.5, -9.5, 7.0, 15.0, 1.0)
        pc.fill(r, '#17181d'); pc.grad(r, -3.5, 0, 3.5, 0, [(0, '#3a3d47', 255), (0.4, '#1c1d23', 255), (1, '#0b0b0e', 255)])
        pc.line(r, pc.lw * 0.8)
        return
    if prop == 'bottle' and abs(getattr(P, 'bottle_tilt', 0.0)) > 0.5 and not front_part:
        k = 10.0 / sp.get('m', 1.7); hk = sp['body'].get('hand', 1.0)
        reach = 36.0 * hs * hk
        gx_, gy_ = wx + math.sin(math.radians(-hang)) * reach, wy + math.cos(math.radians(hang)) * reach
        pc = c.sub(gx_, gy_, P.bottle_tilt, k); pc.lw = c.lw / k
        _p_bottle(pc, det, t, P); return
    return _held_prop_prev(c, sp, prop, wx, wy, hang, hs, side, det, t, P, front_part)


def _p_drink(self, t0, t1, side=1, gulps=4):
    """Drink from the water bottle: it comes up to the mouth, tips up, the head tips back, gulps ('gulp' events)."""
    self.hold_prop('bottle', side, t0 - 1.0, None)
    self.reach_to(t0, side, (self, 'mouth'), t1=t1, dur=0.6, z=90.0, contact='grip', shape='grip', fade=0.6, prop='bottle')
    def fn(P, t):
        w = _env(t, t0 + 0.4, t1, 0.5, 0.5)
        if w <= 0: return
        P.h_nod -= 0.35 * w; P.bottle_tilt = -side * 110.0 * w
        P.drink_lvl = 0.6 - 0.5 * clamp((t - t0) / max(0.1, t1 - t0))
        P.m_open = max(P.m_open, 0.2 * w)
    self._add(t0, t1 + 0.6, fn)
    return [self._ev(t0 + 0.8 + i * 0.5, 'gulp', -6.0, pan=0.0) for i in range(gulps) if t0 + 0.8 + i * 0.5 < t1]


def _p_dial(self, t0, side, keypad, n=10, gap=0.32):
    """Dial a phone: the index finger presses a keypad target n times ('dial_beep' events)."""
    return _p_tap(self, t0, side, keypad, n, gap, z=80.0, kind='dial_beep')


def _p_gone(self, t0, fade=2.5, tilt=9.0):
    """Gently gone (Grandpa at sunrise, 1979): the eyes close, the head settles a little to one side, the breathing stops,
    nothing moves any more. Nothing frightening: he looks asleep in his chair."""
    def fn(P, t):
        w = ease_in_out(prog(t, t0, t0 + fade))
        if w <= 0: return
        P.lid_l = max(P.lid_l, w); P.lid_r = max(P.lid_r, w)
        P.still = max(P.still, w); P.life *= (1.0 - w); P._noblink = max(getattr(P, '_noblink', 0.0), w)
        P.h_tilt += tilt * w; P.h_nod += 0.14 * w; P.breath = lerp(P.breath, 0.5, w)
        P.m_open = lerp(P.m_open, 0.04, w); P.smile *= (1.0 - w); P.brow_sad *= (1.0 - w); P.brow_up *= (1.0 - w)
        P.tremble *= (1.0 - w)
    return self._add(t0, None, fn)


def _p_glasses(self, t0, on=True, side=1, dur=0.9):
    """Put the reading glasses on (on=True) or let them drop onto their chain: the hand goes to the temple, the glasses
    move at the middle of the gesture."""
    tm = t0 + dur * 0.5
    self.reach_to(t0, side, (self, 'eye_l' if side > 0 else 'eye_r'), t1=tm + 0.1, dur=dur * 0.45, z=60.0, contact='tips',
                  shape='pinch', fade=dur * 0.45)
    def fn(P, t):
        P.specs = (1.0 if t >= tm else 0.0) if on else (0.0 if t >= tm else 1.0)
    return self._add(t0 - 5.0, None, fn, late=True)


def _p_sag(self, t0, t1=None, amount=1.0, fade=0.6):
    """The jeans slip down (Milo has lost weight): pose.sag."""
    return self.set(t0, t1, fade, sag=amount)


def _p_hold_up(self, t0, t1=None, side=1, fade=0.4):
    """A hand grabs the waistband to hold the falling jeans up."""
    tg = lambda t: (lambda h: (h[0] + 18.0 * self.height / 1000.0 * side, h[1] - 10.0 * self.height / 1000.0))(self.where(t, 'hip', post=False))  # noqa: E731
    return self.reach_to(t0, side, tg, t1=t1, dur=0.4, z=70.0, contact='grip', shape='grip', fade=fade)


def _p_hand_on(self, t0, part='chest', t1=None, side=-1, dur=0.8, z=115.0, fade=0.6, shape='open'):
    """A hand pressed to the body: 'chest' (chest pain), 'belly' (my tummy hurts), 'side' (holding her side)."""
    def tg(t):
        if part == 'side':
            hx, hy = self.where(t, 'belly', post=False)
            return hx - side * 40.0 * self.height / 1000.0, hy - 20.0 * self.height / 1000.0
        return self.where(t, part, post=False)
    return self.reach_to(t0, side, tg, t1=t1, dur=dur, z=z, contact='palm', shape=shape, fade=fade)


def _p_ticket_hold(self, t0, text_='', t1=None, side=1, lap=True):
    """Hold a paper waiting-room ticket in the lap (text_ '' = the ink long gone: Grandpa's; 'RUTH' at sunrise)."""
    def fn(P, t):
        if t >= t0 and (t1 is None or t < t1): P.dl_ticket = text_
    self._add(t0, t1, fn, late=True)
    self.hold_prop('ticket', side, t0, t1)
    if lap: self.reach_to(t0, side, (self, 'lap'), t1=t1, dur=0.6, z=90.0, contact='grip', shape='grip', fade=0.5, prop='ticket')
    return self


Acting.receiver_to_ear = _p_receiver_ear
Acting.tap = _p_tap
Acting.pull_cord = _p_pull_cord
Acting.strike_match = _p_strike_match
Acting.slide_under_door = _p_slide_under
Acting.write_marker = _p_write_marker
Acting.take_pulse = _p_take_pulse
Acting.carry = _p_carry
Acting.drive = _p_drive
Acting.rock = _p_rock
Acting.breathe_fast = _p_breathe_fast
Acting.drink = _p_drink
Acting.dial = _p_dial
Acting.gone = _p_gone
Acting.glasses = _p_glasses
Acting.sag = _p_sag
Acting.hold_up = _p_hold_up
Acting.hand_on = _p_hand_on


_HAND_OVER_SHAPE = 'cover'
_COVERC = {}


def _cover_geom(side):
    """'cover': the relaxed hand with its fingers closed together (a hand laid over a mouth or eyes). The crevices
    between the fingers are filled in up to just short of the tips, so the outline runs round the outside only and the
    finger joins are thin skin-coloured lines: at film scale the spread-finger outline met in the gaps and read black."""
    if side not in _COVERC:
        G = dict(_hand_cached('relaxed', side, 0.0))
        th = -side
        cl = []                                     # the relaxed fingers' centre lines (as _hand_geom builds them)
        for off, lens, w, spl in _FING:
            cl.append(_finger_pts(th * off * 9.6, 31.0 - abs(off) * 2.0, th * spl * 0.4, lens, 0.0, -th * spl * 0.12))
        closed = G['union']
        for a_, b_ in zip(cl[:-1], cl[1:]):         # fill the gap between neighbours from the knuckles to the tips
            closed = union(closed, poly(list(a_) + list(reversed(b_)), True))
        G['closed'] = closed
        G['shade_c'] = _crescent(closed, -5, -2.5)
        _COVERC[side] = G
    return _COVERC[side]


_draw_hand_prev = _draw_hand


def _draw_hand(c, sp, shape, x, y, scale, angle, side, det, skin, sh, ring=False, press=0.0, t=0.0):
    if shape != 'cover':
        return _draw_hand_prev(c, sp, shape, x, y, scale, angle, side, det, skin, sh, ring, press, t)
    hc = c.sub(x, y, angle, scale * sp['body'].get('hand', 1.0))
    G = _cover_geom(side)
    u = G['closed']
    hc.fill(u, skin)
    hc.fill(G['shade_c'], sh, 150)
    if det >= 1:
        with hc.clip(u):
            hc.line(G['seps'], hc.lw * 0.32, sp['skin_dp'], 120)
        nailc = mix(skin, '#ffffff', 0.38)
        for p in G['nails']:
            hc.fill(p, nailc, 200); hc.line(p, hc.lw * 0.22, sp['skin_dp'], 170)
    hc.line(u, hc.lw * 0.9)
    if ring and G['ring'] is not None:
        _ring_band(hc, G['ring'], det, t)




def _p_hand_over(self, t0, side, other, part='eyes', t1=None, dur=0.7, z=60.0, fade=0.5):
    """Lay a hand over another actor's eyes / mouth / head, the fingers closed and cupped ('relaxed'): spread 'open' or
    'flat' fingers show the face through gaps narrower than their outlines, and at film scale read as a black glove."""
    return self.reach_to(t0, side, (other, part), t1=t1, dur=dur, z=z, contact='palm', shape=_HAND_OVER_SHAPE, fade=fade)


Acting.hand_over = _p_hand_over
Acting.ticket_hold = _p_ticket_hold


# ---------------------------------------------------------------------------------------------------- fixes after the clip review
_draw_bust_prev = draw_bust


def draw_bust(pen, who, cx, cy, scale=1.0, pose=None, detail=None, light=None, t=None):
    """Close-up. Doctor Later: scale 1 = his face (chin to the top of the face, 21 cm) 600 design px tall, its centre at
    (cx, cy); the cone rises above it and the rest of him is drawn too (the frame crops it). Everyone else as before."""
    if not CAST[who].get('later'): return _draw_bust_prev(pen, who, cx, cy, scale, pose, detail, light, t)
    P = _as_pose(pose); t = P.t if t is None else t
    s = 600.0 * scale / (2 * _DL_FACE[1] * _DLU)          # design px per body unit
    hx, hy = _later_pts(P)['head']
    c = Ctx(pen, skia.Matrix(), _lw_for(600.0 * scale)).sub(cx - hx * s, cy - hy * s, 0.0, s)
    det = _auto_detail(pen, 600.0 * scale) if detail is None else detail
    return _later_figure(c, who, P, det, t, light)


def later_bust_place(actor, t, cx, cy, scale=1.0):
    """(x, y_floor, height) that draw() would need to put Doctor Later's face where draw_bust(cx, cy, scale) puts it (use
    it to stage targets for a close-up in the same coordinates)."""
    P = actor.at(t)
    s = 600.0 * scale / (2 * _DL_FACE[1] * _DLU)
    hx, hy = _later_pts(P)['head']
    return cx - hx * s - P.dx, cy - hy * s - P.dy, 1000.0 * s


_skirts3_doc_prev = _skirts3


def _skirts3(c, sp, B, P, det, t, rows):
    """Seated in a skirt (Ruth in the armchair, at the cardiologist; 1979 Ruth): the skirt drapes over both thighs to
    the knees and hangs a little below them, so neither leg shows through beside it."""
    o = sp['outfit']
    st = clamp(B.sit + 0.8 * B.kneel)
    if o in ('cardi_ruth', 'housecoat') and st > 0.25:
        cl = sp['cloth']; b = sp['body']
        colr, colsh = (cl['skirt'], cl['skirt_sh']) if o == 'cardi_ruth' else (cl['top'], cl['top_sh'])
        pts = []
        for side in (-1, 1):
            X, Y, s_, _ = B.p3(side * b['wa'] * 1.02, B.y_wa + 10, 0)
            pts.append((X, Y))
            H, K, A, pitch = _leg_chain(sp, B, P, side)
            lw = b['leg'][0] * 0.9
            for dx, dy, dz in ((side * lw, 0.0, 0.0), (side * lw, -lw * 0.6, 0.0), (side * lw, 70.0, 0.0), (-side * lw * 0.5, 70.0, 0.0)):
                Q = K + np.array([dx, dy, dz])
                X, Y, _, _ = B.p3(Q[0], Q[1] - B.bob, Q[2], upper=False)
                pts.append((X, Y))
            X, Y, _, _ = B.p3(H[0] + side * lw, H[1] - B.bob, H[2], upper=False)
            pts.append((X, Y))
        sk = smooth(_hull(pts), True, 0.5)
        c.fill(sk, colr); _cloth_shade(c, sk, colsh, 150, 1.0, 20)
        if det >= 1: c.texture(sk, 'fabric', 0.12, 0.6)
        c.line(sk, c.lw)
        return
    return _skirts3_doc_prev(c, sp, B, P, det, t, rows)


def carry_anchor(carrier, t):
    """Design point where a carried child's hips sit: in the carrier's arms, against the front of the belly."""
    bx, by = carrier.where(t, 'belly', post=False)
    P = carrier._raw(t, False)
    face = math.sin(P.turn * PI / 2)
    s = carrier.height / 1000.0
    return bx + face * 95.0 * s, by + 25.0 * s


def draw_carry_child(pen, carrier, child, t, light=None, clight=None):
    """Draw a child carried in front (carrier.carry(t0, child)): the child's hips placed in the carrier's arms
    (carry_anchor), the carrier with its far arm, the child, then the carrier's near arm over the child."""
    ax, ay = carry_anchor(carrier, t)
    child.place(0.0, 0.0)
    hx, hy = child.where(t, 'hip', post=False)
    child.place(ax - hx, ay - hy)
    Pc = child.at(t)
    Pcar = carrier.at(t)
    near = 1 if math.sin(Pcar.turn * PI / 2) <= 0 else -1
    draw(pen, carrier.who, carrier.x0, carrier.y0, carrier.height, Pcar, light=light, t=t)
    draw(pen, child.who, child.x0, child.y0, child.height, Pc, light=clight or light, t=t)
    draw_arm(pen, carrier.who, near, Pcar, x=carrier.x0, y_feet=carrier.y0, height=carrier.height, light=light, t=t)


# ====================================================================================================== self-test
def _selftest_doctor():
    """The doctor film's checks: every new id draws in every view (full and close), Doctor Later in every perch, tape
    stage and face; his feet stay on the floor; his pinch lands on far targets (the arm unfolds) and his fingers close on a
    wrist; the ticket tears into his fingers; the tape comes off strip by strip; he never lip-syncs; the people's new
    contacts land (the handset, a hand over a mouth, two fingers on a wrist, a seat, a perch)."""
    out = []
    set_render_size(480, 270)
    surf = skia.Surface(CFG.rw, CFG.rh); pen = Pen(surf.getCanvas()); surf.getCanvas().scale(CFG.k, CFG.k)
    people = [w for w in DOCTOR_CAST if w != 'later']
    for who in people:
        for yaw in (0.0, 0.5, -0.5, 1.0, 1.5, 2.0):
            draw(pen, who, 960, 1000, 700, Pose(turn=yaw, sit=0.6 if yaw == 1.0 else 0.0, seat=250.0 if yaw == 1.0 else 0.0))
            draw_bust(pen, who, 960, 540, 0.6, Pose(h_turn=yaw))
    for kind in ('plastic', 'armchair', 'bench', 'car', 'low'):
        for yaw in (0.0, 0.5, -0.5, 1.0, 1.5, 2.0):
            a = Acting('later', seed=1, height=height_px('later', 300.0)).place(960, 1000)
            a.perch(None, kind); a.face(yaw)
            if kind == 'car': a.bend_to_roof(1000 - 1.15 * 300)
            draw(pen, 'later', 960, 1000, a.height, a.at(1.0), t=1.0)
            assert a.foot_gap(1.0) < 0.5, ('later feet', kind, yaw, a.foot_gap(1.0))
    for tp in (1.0, 0.7, 0.4, 0.0):
        for fc in range(6):
            draw_bust(pen, 'later', 960, 540, 0.3, Pose(dl_tape=tp, dl_face=float(fc)), t=1.0)
    for nm in ('receiver', 'card', 'card_back', 'match', 'match_lit', 'matchbox', 'note', 'marker', 'ticket', 'bottle', 'mug', 'cup', 'vial',
               'cell', 'cell_glucose', 'keys'):
        draw_prop3(pen, nm, 960, 540, 5.0)
    out.append('%d people draw in 6 views full and close; Doctor Later in 5 perches x 6 views (feet on the floor in every one), '
               '4 tape stages x 6 faces; 16 props' % len(people))
    # his pinch lands on targets near and far across the room (the arm unfolds)
    errs = []
    for tg in ((1300, 640), (1700, 700), (2200, 600), (1100, 900)):
        a = Acting('later', seed=2, height=height_px('later', 300.0)).place(800, 1000)
        a.perch(None, 'armchair', hands=('lap', 'floor')); a.face(0.5)
        a.reach_far(0.0, -1, tg, dur=0.3, shape='pinch')
        tx, ty = a.where(1.0, 'tips_r')
        errs.append(math.hypot(tx - tg[0], ty - tg[1]))
    assert max(errs) < 25.0, ('later reach', errs)
    out.append('reach_far: his pinch within %.1f px of 4 targets up to 1400 px away (the arm unfolds)' % max(errs))
    # the ticket tears into his fingers; the tape comes off strip by strip; he never moves his mouth
    a = Acting('later', seed=3, height=height_px('later', 300.0)).place(800, 1000)
    a.perch(None, 'armchair'); tt, ev = a.tear_ticket(0.0, -1, (1500, 640), 'MILO', dur=1.0)
    assert a.at(tt - 0.05).hr_prop != 'ticket' and a.at(tt + 0.05).hr_prop == 'ticket' and ev[0]['name'] == 'ticket_tear'
    ev = a.loosen_tape(3.0, 6.0, 1.0, 0.4)
    tps = [a.at(t).dl_tape for t in np.arange(2.5, 7.0, 0.25)]
    assert all(tps[i] >= tps[i + 1] - 1e-6 for i in range(len(tps) - 1)) and tps[0] > 0.99 and abs(tps[-1] - 0.4) < 0.05
    assert sum(1 for e in ev if e['name'] == 'tape_peel') >= 10
    a.talk([(7.0, 8.0, 'Take a seat. It can wait.')], env=None, words=None)
    assert max(a.at(t).m_open for t in np.arange(7.0, 8.0, 0.05)) < 0.02
    out.append('tear_ticket: the ticket appears in his fingers at the tear; loosen_tape: %d strips, monotonic; no lip sync' %
               sum(1 for e in ev if e['name'] == 'tape_peel'))
    # his fingers close on the narrator's wrist
    n = Acting('narr14', seed=4, height=height_px('narr14', 300.0)).place(1300, 1000); n.face(-0.6)
    n.reach(-1.0, None, 1, out=40.0, down=150.0, fwd=200.0, shape='open', up=0.0, fade=0.01)
    a = Acting('later', seed=5, height=height_px('later', 300.0)).place(800, 1000); a.perch(None, 'armchair'); a.face(0.5)
    a.take_wrist(0.0, -1, n, 1, dur=0.4)
    tx, ty = a.where(1.0, 'hand_r'); wx, wy = n.where(1.0, 'wrist_l')
    assert math.hypot(tx - wx, ty - wy) < 25.0, ('wrist', tx, ty, wx, wy)
    out.append('take_wrist: his palm %.1f px from the narrator\'s wrist, the fingers wrapped round it' % math.hypot(tx - wx, ty - wy))
    # look_at: his head turns slowly toward the target
    a = Acting('later', seed=6, height=height_px('later', 300.0)).place(800, 1000); a.perch(None, 'plastic'); a.face(0.0)
    a.look_at(0.0, (1600, 500), dur=0.6)
    assert a.at(2.0).h_turn > 0.25
    # people: the handset comes off the wall phone without a jump; Ruth's hand lands on Milo's mouth; two fingers on a wrist
    r = Acting('ruth', seed=7, height=height_px('ruth', 380.0)).place(900, 1000); r.face(0.5)
    rec = PropTrack('receiver', 1080, 1000 - 1.45 * 380 + 9 * 3.8, 3.8)
    tc = r.pick_up(rec, 0.3, side=1, dur=1.0)
    b0, b1 = rec.pos(tc - 1e-3), rec.pos(tc + 1e-3)
    assert math.hypot(b1[0] - b0[0], b1[1] - b0[1]) < 10.0, ('receiver jump', b0, b1)
    m = Acting('milo', seed=8, height=height_px('milo', 380.0)).place(1150, 1000); m.face(-0.5)
    r2 = Acting('ruth', seed=9, height=height_px('ruth', 380.0)).place(900, 1000); r2.face(0.6); r2.hand_over(0.0, 1, m, 'mouth', dur=0.3)
    hx, hy = r2.where(1.0, 'hand_l'); mx, my = m.where(1.0, 'mouth')
    assert math.hypot(hx - mx, hy - my) < 12.0, ('hand over mouth', hx, hy, mx, my)
    h = Acting('halverson', seed=10, height=height_px('halverson', 380.0)).place(850, 1000); h.face(0.55)
    m2 = Acting('milo_sick', seed=11, height=height_px('milo', 380.0)).place(1100, 1000); m2.face(-0.5)
    m2.reach(-1.0, None, 1, out=10.0, down=150.0, fwd=200.0, shape='relaxed', up=0.0, fade=0.01)
    h.take_pulse(0.0, -1, m2, 1)
    P = h.at(1.0); B = Body(h.sp, P); _, E, W = _arm_data(h.sp, B, P, -1)
    ox, oy, s = _origin(h, P); X, Y, _, _ = B.p3(*W)
    wx, wy = m2.where(1.0, 'wrist_l')
    assert math.hypot(ox + X * s - wx, oy + Y * s - wy) < 80.0
    out.append('people: handset pick-up jump %.1f px; Ruth\'s palm %.1f px from Milo\'s mouth; Halverson\'s fingers on his wrist'
               % (math.hypot(b1[0] - b0[0], b1[1] - b0[1]), math.hypot(hx - mx, hy - my)))
    # seats: Ruth in the armchair keeps her feet on the floor; a perched child's legs hang (no floor contact needed)
    a = Acting('ruth', seed=12, height=height_px('ruth', 380.0)).place(900, 1000); a.face(0.6); a.sit_on(0.0, 1000 - 0.43 * 380, dur=0.8)
    for t in np.arange(0.0, 2.0, 0.1): assert a.foot_gap(float(t)) < 0.5, ('ruth seat feet', t)
    out.append('sit_on: Ruth into the armchair, feet on the floor all the way down')
    for o_ in out: print(o_)
    print('doctor film self-test ok')


_selftest_bunny_full = _selftest


def _selftest():
    """python3 characters.py --selftest: the older films' checks, the Bunnyman film's checks, then the doctor film's."""
    _selftest_bunny_full()
    _selftest_doctor()
