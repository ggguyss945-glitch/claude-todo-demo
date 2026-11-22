"""characters_bus.py: the cast of "If The School Bus Stops At Midnight... DON'T GET ON" and its staging tools.

This file is not imported on its own: characters.py runs it in its own namespace at the end of the module (exec, after
characters_bunny.py and characters_doctor.py), so everything here is part of `characters` (import characters as CH;
CH.draw(...), CH.Acting(...)) and can use and extend every helper above (Ctx, HeadMap, Body, _ik, _tube, _v3cast, Acting,
PropTrack, PROPS3...). The older casts are unchanged. See BUS_API below and CAST.md for the beat map.
"""
# NOTE: runs inside characters.py's globals (math, np, skia, Ctx, Body, CAST, Pose, Acting, ... are defined).

BUS_API = """
Bus film cast ids:
  'whistle'      MISTER WHISTLESTOP (original): 8 ft, a forward predator's hunch, legs 55 %, arms to the knees (they stretch), a
                 big furry cat-mascot head (about 1/5 of his height, tilted): jagged cheek ruffs, tufted ears, tabby crown fading
                 into a matted off-white face, muzzle with whisker pads, cat nose and long (some bent) whiskers, painted almond
                 cat eyes that never blink (his left pupil higher), THE GRIN (a cat's mouth stretched up into the cheeks, dark
                 inside, a flat row of teeth; never moves), an off-white chest ruff, a ticket-punch hole in his left ear, a
                 far-too-tall dented stovepipe hat in faded school-bus yellow with two DIAGONAL black hazard bands leaning
                 12 deg to his left, a mustard driver jacket (short sleeves, tabby wrists, WHISTLESTOP patch), a black bow tie
                 with a red STOP pin, a silver whistle on an orange lanyard, white gloves with four segments per finger, a thin
                 tabby tail hanging straight. Never walks, never lip-syncs. 'whistle94': the 1994 TV host (clean, bright).
  'mina'         Mina, 13 (the narrator). 'mina_bare': barefoot for the chase.
  'sami'         Sami, 6 (dinosaur pajamas with hood and tail). 'sami_torn': half the tail ripped off.
  'della'        Grandma Della, 63 (knit cap, glasses on a cord, navy driver jacket with DELLA tape).
  'theo'         Theo, the boy in the yellow raincoat (1994), faded. 'theo_color': after three o'clock (adults see him).
  'new_girl'     the new girl (hair clip, backpack with no name).
  'kid94_a', 'kid94_b', 'kid94_c'   1994 studio kids holding up name cards.
Whistlestop acting (Acting('whistle', ...)): unfold(t0), tape_skip(keys), curl_door(t0, side, edge), walls_flat(t0, l, r),
  bend_double(t0, ceil_y), lean_to(t0, target, gap_cm), reach_far(t0, side, target), hold_child(t0, side, child, cside),
  grip_small(t0, side, other, oside), walkie_to_grin(t0, side), blow_whistle(t0, 'two'|'long'), snap_glove(t0, side,
  target), head_backwards(t0), clipboard(t0), punch(t0), write_line(t0, t1), host(t0, t1), say(intervals) (head bob, no
  lips), defeat(t0). Helpers: draw_whistle_hands, whistle_point, ws_tracking (VHS tear overlay).
"""

import bisect as _bisect4

# ====================================================================================================== MISTER WHISTLESTOP
# His own rig in centimetres, body frame: x = his left (+), y = down (floor 0, so heights are negative), z = his front.
# The origin is the floor point between his feet (a.place(x, floor_y)). 2.44 m to the crown; the hat adds ~0.9 m.
_WS_M = 2.44
_WSU = 1000.0 / (_WS_M * 100.0)                 # body units per cm
_WS_L = dict(thigh=64.5, shin=62.0, upper=50.0, fore=47.0)
_WS_HIP = 134.0                                 # hip joint height (55 % of 244)
_WS_HAT = 92.0                                  # hat height (cm)
_WS_PAL = dict(
    hat='#c49f3f', hat_sh='#8a6f28', hat_hi='#dcc06e', band='#1d1a16', scuff='#e6d7a8',
    fur='#7a6a55', fur_dk='#5a4c3d', fur_hi='#958670', mask='#ebe4d0', mask_edge='#c9b98a', mask_sh='#b9ae93',
    jacket='#a88a3a', jacket_sh='#77612a', jacket_hi='#c2a55c', trim='#5e4c22', trousers='#4a3f33', trousers_sh='#352d24',
    shoe='#221d19', glove='#e2ded2', glove_sh='#a9a495', glove_dirt='#8f8878', bow='#141212', pin='#b3241e',
    lanyard='#e07a1f', whistle='#c9ced5', line='#1b1512', teeth='#efe8d3', eye='#d4c35e', pupil='#0b0a09',
    ear_in='#a88c8a', mouth='#2a2018', pad='#f1ecdd', whisk='#ece6d4', patch='#e0d6b8', patch_rim='#6e4a22', button='#b4964c', nose='#7c5c50', grime=0.75, tv=0)
_WS_PAL94 = dict(_WS_PAL, hat='#dfb23a', hat_sh='#a8822a', hat_hi='#f2d47a', fur='#8a7a62', fur_dk='#665640',
                 mask='#f7f3e8', mask_edge='#e2d8bc', mask_sh='#cfc6ae', jacket='#c2a043', jacket_sh='#8f7530',
                 jacket_hi='#dcbe6a', glove='#f8f7f2', glove_sh='#c4c1b6', teeth='#fbf9f0', eye='#e6d86c', pad='#fbf9f2', grime=0.0, tv=1)

POSE_DEFAULTS.update(
    ws_unfold=1.0,      # 0 folded small (in the bus door) .. 1 standing: unfolds segment by segment like a ladder
    ws_bend=0.0,        # waist hinge forward: 1 = torso horizontal ("bent double"), more = "down, and down"
    ws_crouch=0.0,      # knees bend 0..1.45
    ws_ceil=0.0,        # a ceiling (cm above the floor): the hat crushes and folds under it, then he bends
    ws_hatfold=0.0,     # extra fold of the hat's upper half (computed from the ceiling; can be forced)
    ws_elev=0.03,       # camera elevation (rad): negative = the camera looks up at him
    ws_scale=1.0,       # tape-skip depth: the figure scales about its feet (a skip toward the lens)
    ws_glitch=0.0,      # VHS tracking tear across the figure (tape skip)
    ws_slip=0.0,        # the defeat: the grin slides out of register
    ws_rewind=0.0,      # the defeat: tracking lines tear him, he rewinds into the dark (fades)
    ws_whistle=0.0,     # the whistle lifted to the grin 0..1
    ws_blow=0.0,        # blowing: a little rise and head tilt back
    ws_bob=0.0,         # his talk bob (no jaw)
    ws_write=0.0,       # pencil stroke progress on the clipboard
    ws_px0=0.0, ws_py0=0.0, ws_ph=0.0,       # staging placement (set by Acting.place)
    ws_lw=0.0, ws_lx=0.0, ws_ly=0.0, ws_lz=0.0, ws_lroll=0.0,   # left hand world target
    ws_rw=0.0, ws_rx=0.0, ws_ry=0.0, ws_rz=0.0, ws_rroll=0.0,   # right hand world target
    ws_lcurl=0.0, ws_rcurl=0.0,              # extra finger curl
    ws_face_up=0.75,    # how much the head keeps facing forward when he bends
)
POSE_DISCRETE.update(ws_lrest='hang', ws_rrest='hang', ws_hands_front=0, ws_ticket='SAMI')


def _rx(v, a):
    """Rotate vector(s) about the x axis by a (forward lean: the top moves toward +z)."""
    v = np.asarray(v, float)
    ca, sa = math.cos(a), math.sin(a)
    return np.stack([v[..., 0], v[..., 1] * ca + v[..., 2] * sa, -v[..., 1] * sa + v[..., 2] * ca], -1)


def _rot3(yaw, pitch, roll):
    """Matrix: roll about z (+ = top toward his left), then pitch about x (+ = face down), then yaw about y (+ = face to
    his left / screen right)."""
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp_ = math.cos(pitch), math.sin(pitch)
    cy_, sy_ = math.cos(yaw), math.sin(yaw)
    Rz = np.array([[cr, -sr, 0], [sr, cr, 0], [0, 0, 1.0]])
    Rx = np.array([[1, 0, 0], [0, cp, sp_], [0, -sp_, cp]])
    Ry = np.array([[cy_, 0, sy_], [0, 1, 0], [-sy_, 0, cy_]])
    return Ry @ Rx @ Rz


def _u3(v):
    n = float(np.linalg.norm(v)); return v / n if n > 1e-9 else v


class _WSView:
    """His body frame (cm) -> the drawing frame (cm, x right, y down, feet at (0, 0)): yaw (pose.turn quarter turns,
    + faces screen right), a camera elevation, mild perspective, the figure's 2D tilt about the feet."""

    def __init__(self, P):
        self.th = P.turn * PI / 2
        self.ct, self.st = math.cos(self.th), math.sin(self.th)
        self.e = float(getattr(P, 'ws_elev', 0.03))
        self.ce, self.se = math.cos(self.e), math.sin(self.e)
        self.D = 900.0
        self.cy = -150.0
        self.tilt = math.radians(P.tilt)
        self.sway = P.sway * 0.1

    def pa(self, Q):
        Q = np.asarray(Q, float).reshape(-1, 3)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        xc = x * self.ct + z * self.st
        zc = -x * self.st + z * self.ct
        yv = y * self.ce + zc * self.se
        zd = zc * self.ce - y * self.se
        f = self.D / (self.D - np.minimum(zd, self.D * 0.8))
        X = xc * f + self.sway; Y = self.cy + (yv - self.cy) * f
        if self.tilt:
            c_, s_ = math.cos(self.tilt), math.sin(self.tilt)
            X, Y = X * c_ - Y * s_, X * s_ + Y * c_
        return X, Y, zd, f

    def p(self, q):
        X, Y, zd, f = self.pa(q)
        return float(X[0]), float(Y[0]), float(zd[0]), float(f[0])

    def p2(self, q):
        X, Y, _, _ = self.pa(q); return (float(X[0]), float(Y[0]))

    def unp(self, X, Y, zd):
        if self.tilt:
            c_, s_ = math.cos(-self.tilt), math.sin(-self.tilt)
            X, Y = X * c_ - Y * s_, X * s_ + Y * c_
        X -= self.sway
        f = self.D / (self.D - zd)
        xc = X / f; yv = self.cy + (Y - self.cy) / f
        y = yv * self.ce - zd * self.se
        zc = yv * self.se + zd * self.ce
        return np.array([xc * self.ct - zc * self.st, y, xc * self.st + zc * self.ct])

    def face(self, n):
        """Camera-facing component of direction(s) n (> 0 faces the lens)."""
        n = np.asarray(n, float).reshape(-1, 3)
        zc = -n[:, 0] * self.st + n[:, 2] * self.ct
        return zc * self.ce - n[:, 1] * self.se

    def depth(self, q):
        return float(self.face(q)[0])


def _ws_world_to_cm(P, wx, wy, zd=0.0):
    if P.ws_ph <= 0: return None
    s = P.ws_ph / 1000.0 * _WSU * max(P.ws_scale, 1e-3)
    X = (wx - (P.ws_px0 + P.dx)) / s; Y = (wy - (P.ws_py0 + P.dy)) / s
    return _WSView(P).unp(X, Y, zd)


# ---------------------------------------------------------------------------------------------------- hand geometry
_WS_FING = ((2.9, (4.3, 3.9, 3.4, 3.0)), (0.0, (4.7, 4.3, 3.7, 3.2)), (-2.9, (4.1, 3.7, 3.3, 2.8)))   # 3 fingers x 4 segments
_WS_CURL = {   # per-hinge curl (rad) for the 4 finger joints; thumb curl
    'hang': ((0.16, 0.26, 0.32, 0.30), 0.35),          # half-curled, hanging ready 'open': ((0.02, 0.04, 0.05, 0.05), 0.0), 'flat': ((0.0, -0.04, -0.04, -0.02), -0.1),
    'curl': ((0.55, 0.62, 0.62, 0.55), 0.35), 'grip': ((0.85, 0.95, 0.85, 0.7), 0.9), 'pinch': ((0.35, 0.45, 0.4, 0.3), 0.7),
    'claw': ((0.25, 0.55, 0.6, 0.55), 0.4), 'host': ((0.06, 0.1, 0.1, 0.08), 0.0), 'hold': ((0.7, 0.8, 0.7, 0.5), 0.8),
    'clip': ((0.75, 0.85, 0.75, 0.6), 0.6), 'pen': ((0.6, 0.7, 0.6, 0.5), 0.8), 'point': ((0.9, 0.9, 0.8, 0.6), 0.6),
    'snap': ((1.0, 1.05, 0.95, 0.8), 1.0), 'reach': ((0.05, 0.1, 0.12, 0.12), 0.1), 'mitt': ((0.10, 0.16, 0.22, 0.26), 0.25),
}


def _ws_hand3(R, s, P):
    """3D glove: wrist W, palm corners, the three fingers (4 segments each: one knuckle too many) and the thumb."""
    arm = R['arms'][s]
    W = arm['W']; E = arm['J'][-1]
    f = _u3(W - E)
    shape = (getattr(P, 'hl_shape' if s > 0 else 'hr_shape') or 'hang')
    if shape not in _WS_CURL: shape = 'hang'
    roll = math.radians(getattr(P, 'ws_lroll' if s > 0 else 'ws_rroll', 0.0) + arm.get('roll', 0.0))
    r0 = np.array([float(s), 0.0, 0.0])
    if abs(float(np.dot(r0, f))) > 0.92: r0 = np.array([0.0, -1.0, 0.0])
    nb = _u3(r0 - f * float(np.dot(r0, f)))
    if roll:                                            # roll the hand about the forearm
        lat = np.cross(f, nb)
        nb = _u3(nb * math.cos(roll) + lat * math.sin(roll))
    th = _u3(-s * np.cross(f, nb))                     # toward the thumb
    curls, tc = _WS_CURL[shape]
    extra = clamp(getattr(P, 'ws_lcurl' if s > 0 else 'ws_rcurl', 0.0))
    K = W + f * 11.0
    palm = [W + th * 4.0 + nb * 1.6, W - th * 4.0 + nb * 1.6, K + th * 4.6 + nb * 1.4, K - th * 4.6 + nb * 1.4,
            W + th * 4.0 - nb * 1.6, W - th * 4.0 - nb * 1.6, K + th * 4.6 - nb * 1.2, K - th * 4.6 - nb * 1.2]
    fingers = []
    for j, (off, lens) in enumerate(_WS_FING):
        if shape == 'point' and j == 0: cl = (0.02, 0.03, 0.03, 0.02)
        else: cl = curls
        splay = (0.10 * (1 - j) if shape in ('flat', 'open', 'host') else 0.04 * (1 - j))
        d = _u3(f + th * splay); n_ = nb.copy()
        p = K + th * off
        pts = [p]
        for k, L in enumerate(lens):
            c_ = cl[k] + extra * 0.5
            d, n_ = _u3(d * math.cos(c_) - n_ * math.sin(c_)), _u3(n_ * math.cos(c_) + d * math.sin(c_))
            p = p + d * L
            pts.append(p)
        fingers.append(pts)
    d = _u3(f * 0.45 + th * 0.85 - nb * 0.25); n_ = nb.copy()
    p = W + f * 3.5 + th * 3.8 - nb * 0.8
    tpts = [p]
    for k, L in enumerate((3.6, 3.2, 2.7)):
        c_ = tc * (0.5 + 0.25 * k) + extra * 0.4
        d = _u3(d * math.cos(c_) - nb * math.sin(c_) * 0.8 - th * math.sin(c_) * 0.4)
        p = p + d * L; tpts.append(p)
    return dict(W=W, f=f, nb=nb, th=th, K=K, palm=palm, fingers=fingers, thumb=tpts, shape=shape)


# ---------------------------------------------------------------------------------------------------- the rig
def _ws_arc_blend(A, B, u, s, lift=1.0):
    """Arm A (rest) -> arm B (settled) at u 0..1 through the joints: the upper arm and the forearm turn (normalised
    blends of their directions; a forearm turning from down to up swings out and forward, never through the body), the
    bone lengths blend. u 0 is exactly A and u 1 exactly B, so the arm meets both poses without a jump."""
    if u <= 0.0: return A
    if u >= 1.0: return B
    S = A['S']; E0, E1 = A['J'][0], B['J'][0]; W0, W1 = A['W'], B['W']
    bias = _u3(np.array([s * 0.4, -0.15, 0.9]))

    def turn(p, q, extra=None):
        p = _u3(p); q = _u3(q)
        d = float(np.dot(p, q))
        v = p * (1.0 - u) + q * u + bias * (math.sin(PI * u) * (1.0 - d) * 0.5)
        if extra is not None: v = v + extra * math.sin(PI * u)
        return _u3(v)
    lu = (1.0 - u) * float(np.linalg.norm(E0 - S)) + u * float(np.linalg.norm(E1 - S))
    lf = (1.0 - u) * float(np.linalg.norm(W0 - E0)) + u * float(np.linalg.norm(W1 - E1))
    # the elbow leads: it lifts out and up mid-move (a raise starts at the shoulder), and settles back into the end pose
    E = S + turn(E0 - S, E1 - S, np.array([s * 0.3, -0.5, 0.45]) * lift) * lu
    W = E + turn(W0 - E0, W1 - E1) * lf
    return dict(S=S, J=[E], W=W, k=(1.0 - u) * A['k'] + u * B['k'], rest=A['rest'])


_WS_HUNCH = 0.30      # rad: rounded shoulders, the neck pushed forward (the 1994 host stands straighter)
_WS_HUP = 12.0         # cm from the neck's top to the head's centre (the crown at 244 cm)


def _ws_headpos(R, a, npitch):
    """Neck top, head 'up' vector and head centre for a waist pitch a and a neck pitch."""
    jut = 0.55 * (1.0 if R.get('hunch', _WS_HUNCH) > 0.1 else 0.3)
    Nt = R['Nb'] + _rx(np.array([0.0, -4.0, 0.8]), a + npitch + jut)
    up = _rx(np.array([0.0, -1.0, 0.0]), a + npitch)
    if jut > 0.3:      # the predator: head pushed forward and down, the chin sunk over the collar
        return Nt, up, Nt + up * (_WS_HUP - 2.5) + _rx(np.array([0.0, 0.0, 8.0]), a)
    return Nt, up, Nt + up * _WS_HUP + _rx(np.array([0.0, 0.0, 2.0]), a)


def _ws_spine(P, crouch, bend):
    """Legs, hips and spine for a crouch and a waist bend."""
    R = {}
    c = clamp(crouch, 0.0, 1.5)
    hh = _WS_HIP - 66.0 * c
    hz = -15.0 * c
    Hc = np.array([0.0, -hh, hz])
    legs = {}
    st = float(getattr(P, 'stance', 0.0))
    for s in (-1, 1):
        A = np.array([s * (9.0 + 18.0 * st), -8.0, 2.0 + 6.0 * c])
        Hp = Hc + np.array([s * 8.0, 0.0, 0.0])
        K, Hp2 = _ik(A, Hp, _WS_L['shin'], _WS_L['thigh'], np.array([s * 0.18, 0.0, 1.0]))
        fd = _u3(np.array([s * 0.2, 0.0, 1.0]))
        legs[s] = (Hp2, K, A, fd)
    R['legs'] = legs
    Hc = (legs[1][0] + legs[-1][0]) / 2.0
    a = bend * PI / 2 + 0.3 * P.lean + 0.18 * c
    a1, a2 = 0.72 * a, 0.28 * a
    Wst = Hc + _rx(np.array([0.0, -16.0, 0.0]), a1)
    Ch = Wst + _rx(np.array([0.0, -30.0, 1.0]), a1 + a2)
    hunch = 0.07 if P.__dict__.get('_ws94') else _WS_HUNCH          # a predator's forward hunch inside the suit
    Sc = Ch + _rx(np.array([0.0, -24.0, -1.5]), a + hunch)
    Nb = Sc + _rx(np.array([0.0, -4.0, 0.5]), a + hunch * 1.5)
    R.update(Hc=Hc, Wst=Wst, Ch=Ch, Sc=Sc, Nb=Nb, a=a, a1=a1, a2=a2, hunch=hunch)
    return R


def _ws_rig(P, _depth=0):
    """The 3D joints (cm, body frame) of Mister Whistlestop for pose P."""
    u = clamp(P.ws_unfold)
    s1 = ease_in_out(prog(u, 0.0, 0.36)); s2 = ease_in_out(prog(u, 0.28, 0.64))
    s3 = ease_in_out(prog(u, 0.58, 0.82)); s4 = ease_out_back(prog(u, 0.78, 1.0)) if u < 1 else 1.0
    crouch = P.ws_crouch + (1.0 - s1) * 1.45
    bend = P.ws_bend + (1.0 - s2) * 1.7
    nfold = (1.0 - s3) * 1.25
    hat_ext = lerp(0.3, 1.0, s4)
    blow = clamp(P.ws_blow)
    R = _ws_spine(P, crouch, bend)
    # a ceiling: bend and crouch until the head (with the hat crushed to a hand's width) fits under it
    ceil = float(P.ws_ceil)
    if ceil > 0 and _depth == 0:
        for _ in range(48):
            a_ = R['a']; np_ = -0.55 * a_ * clamp(P.ws_face_up) + nfold - 0.25 * blow
            hd_ = _ws_headpos(R, a_, np_)[2]
            top = -hd_[1] + _WS_CROWN                                       # the crown's height
            if top < ceil - 22.0: break                                     # room for the crushed, folded hat
            bend += 0.045; crouch = min(crouch + 0.02, 1.0)
            R = _ws_spine(P, crouch, bend)
    a = R['a']
    Nb = R['Nb']
    npitch = -0.55 * a * clamp(P.ws_face_up) + nfold - 0.25 * blow
    Nt, up, Hd = _ws_headpos(R, a, npitch)
    bob = 0.06 * P.ws_bob
    R['neck'] = [Nb, Nt]
    R['head'] = Hd + np.array([P.h_dx * 0.06, P.h_dy * 0.06, 0.0])
    yaw = P.h_turn * PI / 2
    pitch = (a + npitch) * (1.0 - clamp(P.ws_face_up)) + 0.6 * P.h_nod + bob - 0.3 * blow + (0.0 if P.__dict__.get('_ws94') else 0.10)
    roll = math.radians(P.h_tilt - (2.0 if P.__dict__.get('_ws94') else 9.0) + 9.0 * nfold)     # the head tilts against the hat
    R['hrot'] = _rot3(yaw, pitch, roll)
    R['hat_ext'] = hat_ext
    R['crouch'], R['bend'] = crouch, bend
    # hat: base on the crown, leaning 12 deg to his left (3 deg on the 1994 tape), dented halfway, folding under a ceiling
    lean = math.radians(5.0 if P.__dict__.get('_ws94') else 21.0)      # 12 (3 on the tape) once the head's crook is added
    hb_l = np.array([0.0, -(_WS_CROWN - 1.0), -1.5])
    ax_l = np.array([math.sin(lean), -math.cos(lean), -0.06])
    M = R['hrot']
    hb = R['head'] + M @ hb_l
    ax = _u3(M @ ax_l)
    Hh = _WS_HAT * hat_ext
    fold = float(P.ws_hatfold)
    squash = 1.0
    if ceil > 0:
        avail = ceil + hb[1]                         # cm between the hat's base and the ceiling (y is negative up)
        upy = max(-ax[1], 0.2)
        need = Hh * upy
        if need > avail:
            half = Hh * 0.5 * upy
            if avail > half + 4.0:
                fold = max(fold, math.acos(clamp((avail - half - 3.0) / half, -1.0, 1.0)))
            else:
                fold = max(fold, 1.75)
                squash = clamp((avail - 3.0) / max(half, 1.0), 0.15, 1.0)
    R['hat'] = dict(base=hb, ax=ax, H=Hh, fold=fold, squash=squash, M=M, ceil=ceil)
    # arms
    Sc, Ch = R['Sc'], R['Ch']
    a12 = R['a1'] + R['a2']
    arms = {}
    afold = 1.0 - ease_in_out(prog(u, 0.5, 0.92))
    mouth = R['head'] + M @ (_ws_head_local(0.0, -0.47) + np.array([0.0, 0.0, 1.0]))
    R['mouth'] = mouth
    for s in (-1, 1):
        S = Sc + _rx(np.array([s * 19.0, 1.5 if P.__dict__.get('_ws94') else 5.5, -1.0]), a12)      # shoulders dropped
        rest = getattr(P, 'ws_lrest' if s > 0 else 'ws_rrest', 'hang')
        if rest == 'host':        # the 1994 presenter: hand out to the side, palm up
            W = S + np.array([s * 40.0, 58.0, 28.0])
        elif rest == 'clip':      # the clipboard held up against his chest
            W = Ch + _rx(np.array([s * 3.0, 12.0, 24.0]), a12)
        elif rest == 'chest':     # a hand flat on his own chest (the lure)
            W = Ch + _rx(np.array([s * 2.0, 2.0, 20.0]), a12)
        elif rest == 'fold':
            W = S + np.array([s * 3.0, 30.0, 10.0])
        elif rest == 'mouth':     # at the grin (whistle / walkie)
            W = mouth + np.array([s * 4.0, 13.0, 9.0])
        elif rest == 'hip':
            W = Ch + _rx(np.array([s * 17.0, 30.0, 4.0]), a12)
        else:                     # hanging straight down from the shoulder (gravity, even when he bends)
            W = S + (np.array([s * 7.0, 93.5, 7.0 + 3.0 * math.sin(a)]) if P.__dict__.get('_ws94')
                     else np.array([s * 2.5, 92.5, 12.5 + 3.0 * math.sin(a)]))      # elbows bent, gloves a little forward
        if P.ws_whistle > 0.01 and s == getattr(P, '_ws_wside', -1):
            W = W + ((mouth + np.array([s * 3.0, 12.0, 8.0])) - W) * ease_in_out(clamp(P.ws_whistle))
        if afold > 0.001:
            W = W + ((S + _rx(np.array([s * 2.0, 26.0, 12.0]), a12)) - W) * afold
        W_rest = W
        w = clamp(getattr(P, 'ws_lw' if s > 0 else 'ws_rw'))
        Tw_goal = Tw_full = None
        if w > 0.001:
            pre = 'ws_l' if s > 0 else 'ws_r'
            Tw = _ws_world_to_cm(P, getattr(P, pre + 'x'), getattr(P, pre + 'y'), getattr(P, pre + 'z'))
            if Tw is not None:
                Tw_goal = Tw.copy()
                shp = getattr(P, 'hl_shape' if s > 0 else 'hr_shape') or 'hang'
                off = {'flat': 18.0, 'curl': 14.0, 'grip': 9.0, 'snap': 9.0, 'hold': 8.0, 'pinch': 20.0, 'point': 22.0,
                       'reach': 22.0, 'claw': 18.0, 'open': 20.0}.get(shp, 16.0)
                Tw = Tw - _u3(Tw - S) * off
                Tw_full = Tw
                W = W + (Tw - W) * w
        Lu, Lf = _WS_L['upper'], _WS_L['fore']
        pole = _u3(np.array([s * 0.7, 0.1, -0.7]) if rest in ('hang', 'fold') else np.array([s * 0.75, 0.45, -0.45]))

        def solve(W, S=S, pole=pole):
            d = float(np.linalg.norm(W - S))
            k = d / ((Lu + Lf) * 0.985)
            if k > 1.0:             # the arm stretches: both bones lengthen, the elbow barely bent (a rubber reach)
                uu = _u3(W - S)
                perp = _u3(pole - uu * float(np.dot(pole, uu)))
                E = S + uu * d * 0.52 + perp * min(6.0, 0.05 * d)
                return dict(S=S, J=[E], W=W, k=k, rest=rest)
            E, Wr = _ik(S, W, Lu, Lf, pole)
            return dict(S=S, J=[E], W=Wr, k=1.0, rest=rest)
        arms[s] = solve(W)
        if Tw_goal is not None and P.__dict__.get('ws_arc_reach', 0.0) > 0.5:
            # opt-in (ice film L3 / L192 wave): the plain path blends the wrist in a straight line (the arm folds into an
            # inverted V) and switches the fingertip fix on at w 0.5 (the glove jumps a forearm's length in one frame).
            # Here the settled arm (full reach, fingertip on the goal) is solved every frame and the arm travels from its
            # rest pose to it by its joints (upper arm and forearm directions, forearm swinging out-and-forward) over the
            # w window ws_arc_w0..ws_arc_w1 (default 0.25..0.6: about 7 frames of the 0.9 s slow_wave ramp, eased).
            R['arms'] = arms
            arms[s] = solve(Tw_full)
            for _ in range(2):
                h3 = _ws_hand3(R, s, P)
                shp = h3['shape']
                tip = (h3['fingers'][0][-1] + h3['fingers'][1][-1]) / 2.0 if shp not in ('grip', 'snap', 'hold', 'clip', 'curl') \
                    else (h3['fingers'][1][2] if shp != 'curl' else h3['fingers'][1][3])
                arms[s] = solve(arms[s]['W'] + (Tw_goal - tip))
            wa0 = float(P.__dict__.get('ws_arc_w0', 0.25)); wa1 = float(P.__dict__.get('ws_arc_w1', 0.6))
            ua = ease_in_out(clamp((w - wa0) / max(wa1 - wa0, 1e-3)))
            # (ws_arc_lift, opt-in per shot, default 1: how far the elbow lifts out mid-raise; 0 keeps a raise whose glove
            #  ends near the frame edge inside the frame - ice film L387 close bust)
            arms[s] = _ws_arc_blend(solve(W_rest), arms[s], ua, s, lift=float(P.__dict__.get('ws_arc_lift', 1.0)))
        elif w > 0.5 and Tw_goal is not None:
            R['arms'] = arms
            for _ in range(2):
                h3 = _ws_hand3(R, s, P)
                shp = h3['shape']
                tip = (h3['fingers'][0][-1] + h3['fingers'][1][-1]) / 2.0 if shp not in ('grip', 'snap', 'hold', 'clip', 'curl') \
                    else (h3['fingers'][1][2] if shp != 'curl' else h3['fingers'][1][3])
                kw_ = min(1.0, w)
                if P.__dict__.get('ws_soft_reach', 0.0) > 0.5:      # opt-in (ice film L192 wave): the fingertip fix eases in
                    kw_ = clamp((w - 0.5) / 0.5)                    # from w 0.5, no one-frame jump of the hand
                Wn = arms[s]['W'] + (Tw_goal - tip) * kw_
                arms[s] = solve(Wn)
    R['arms'] = arms
    # tail: from the back of the hips, hanging straight down; never moves
    T0 = R['Hc'] + _rx(np.array([3.0, -6.0, -12.0]), R['a1'])
    yb = -14.0; ym = min(yb - 8.0, T0[1] + 0.55 * (yb - T0[1]))
    R['tail'] = [T0, np.array([T0[0] + 3.0, ym, T0[2] - 6.0]), np.array([T0[0] + 6.5, yb + 12.0, T0[2] - 9.5]),
                 np.array([T0[0] + 3.5, yb, T0[2] - 10.5])]
    return R


# ---------------------------------------------------------------------------------------------------- the head
# The mascot costume head: a big furry cat skull (about a fifth of his height): broad flaring cheek ruffs, a flat broad
# crown between pointed tufted ears, a muzzle with two puffy whisker pads and a small triangular nose, painted almond cat
# eyes, and THE GRIN: a cat's mouth stretched from the whisker pads up into the cheeks, dark inside, a flat row of teeth.
_WS_HR = (18.0, 24.5, 16.0)          # cranium radii (cm): x half-width, y up (crown), z depth
_WS_CHIN = 20.5                      # chin depth below the head centre (cm)


def _ws_head_local(lon, lat, grow=0.0):
    """Head surface points (cm, head frame: x his left, y down, z forward) at longitude/latitude arrays (lon 0 = the
    front, lat + up): a cat skull with wide cheek ruffs, a flat crown, a muzzle and whisker pads, a small chin."""
    lon = np.asarray(lon, float); lat = np.asarray(lat, float)
    cl = np.cos(lat); sl = np.sin(lat)
    rx0, ry0, rz0 = _WS_HR
    cheek = 1.0 + 0.30 * np.exp(-((lat + 0.30) / 0.42) ** 2)
    rx = (rx0 + grow) * cheek
    ry = np.where(lat > 0, ry0 * (1.0 - 0.10 * np.clip(lat - 0.5, 0.0, None)), _WS_CHIN) + grow
    rz = (rz0 + grow) * (1.0 + 0.03 * cheek)
    y = -ry * sl
    x = rx * cl * np.sin(lon)
    z = rz * cl * np.cos(lon)
    fr = np.clip(np.cos(lon), 0.0, None)
    z = z + fr * (4.6 * np.exp(-(lon / 0.40) ** 2 - ((lat + 0.28) / 0.24) ** 2)                       # the muzzle
                  + 1.6 * np.exp(-(lon / 0.12) ** 2 - ((lat + 0.15) / 0.09) ** 2)                     # the nose
                  + 1.4 * np.exp(-((np.abs(lon) - 0.17) / 0.12) ** 2 - ((lat + 0.31) / 0.11) ** 2)     # whisker pads
                  + 0.9 * np.exp(-((lat - 0.30) / 0.12) ** 2)                                         # brow ridge
                  - 2.2 * np.exp(-((lat + 0.95) / 0.22) ** 2))                                        # small chin
    return np.stack([x, y, z], -1)


_WS_CROWN = float(-_ws_head_local(0.0, PI / 2)[1])


def _ws_hp(R, lon, lat, out=0.0):
    """A point on his head (body frame) at lon/lat, pushed out by `out` cm along the radius."""
    L = _ws_head_local(lon, lat)
    if out: L = L + _u3(L) * out
    return R['head'] + R['hrot'] @ L


class _WSHead:
    """The head placed in the body frame and projected: grids of (lon, lat) surface points -> screen points + facing."""

    def __init__(self, R, view, P, pal):
        self.R, self.view, self.P, self.pal = R, view, P, pal
        self.M = R['hrot']; self.C = R['head']

    def body(self, L):
        return self.C + (self.M @ np.asarray(L, float).reshape(-1, 3).T).T

    def normal(self, L):
        rx, ry, rz = _WS_HR
        n = L / np.array([(rx * 1.15) ** 2, ry ** 2, rz ** 2])
        n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
        return (self.M @ n.T).T

    def proj(self, lon, lat, grow=0.0):
        L = _ws_head_local(lon, lat, grow).reshape(-1, 3)
        B = self.body(L)
        X, Y, zd, f = self.view.pa(B)
        return X, Y, self.view.face(self.normal(L)), zd

    def sil(self):
        lo, la = np.meshgrid(np.linspace(-PI, PI, 41), np.linspace(-1.55, 1.55, 19))
        X, Y, _, _ = self.proj(lo.ravel(), la.ravel())
        return poly(_hull(np.stack([X, Y], -1)), True)

    def region(self, lon0, lon1, lat_lo, lat_hi, nlon=18, nlat=8, grow=0.05, thr=0.0):
        """Visible quads of the surface patch between lon0..lon1 and lat_lo(lon)..lat_hi(lon) as one path (one fill
        = no seams). Returns the path (None if nothing faces the lens)."""
        lons = np.linspace(lon0, lon1, nlon + 1)
        lo = np.asarray(lat_lo(lons) if callable(lat_lo) else np.full_like(lons, lat_lo), float)
        hi = np.asarray(lat_hi(lons) if callable(lat_hi) else np.full_like(lons, lat_hi), float)
        g = np.linspace(0, 1, nlat + 1)
        LA = lo[:, None] + (hi - lo)[:, None] * g[None, :]
        LO = np.repeat(lons[:, None], nlat + 1, 1)
        X, Y, F, _ = self.proj(LO.ravel(), LA.ravel(), grow)
        X = X.reshape(LO.shape); Y = Y.reshape(LO.shape); F = F.reshape(LO.shape)
        p = skia.Path(); any_ = False
        for i in range(nlon):
            for j in range(nlat):
                fs = F[i, j] + F[i + 1, j] + F[i, j + 1] + F[i + 1, j + 1]
                if fs <= thr * 4: continue
                q = [(X[i, j], Y[i, j]), (X[i + 1, j], Y[i + 1, j]), (X[i + 1, j + 1], Y[i + 1, j + 1]), (X[i, j + 1], Y[i, j + 1])]
                ar = sum(q[k][0] * q[(k + 1) % 4][1] - q[(k + 1) % 4][0] * q[k][1] for k in range(4))
                if ar < 0: q = q[::-1]
                p.addPoly([skia.Point(*v) for v in q], True); any_ = True
        return p if any_ else None

    def curve(self, lons, lats, grow=0.12, thr=0.02):
        """Visible runs of a surface curve as a list of point lists."""
        X, Y, F, _ = self.proj(np.asarray(lons), np.asarray(lats), grow)
        runs, cur = [], []
        for x, y, fv in zip(X, Y, F):
            if fv > thr: cur.append((float(x), float(y)))
            else:
                if len(cur) > 1: runs.append(cur)
                cur = []
        if len(cur) > 1: runs.append(cur)
        return runs

    def disc(self, lon, lat, rl, rt, n=14, grow=0.15):
        """A painted disc on the surface: (path, facing)."""
        a = np.linspace(0, 2 * PI, n, endpoint=False)
        X, Y, F, _ = self.proj(lon + rl * np.cos(a) / max(math.cos(lat), 0.3), lat + rt * np.sin(a), grow)
        return smooth(list(zip(X.tolist(), Y.tolist())), True, 0.9), float(np.mean(F))

    def shape(self, lons, lats, grow=0.15, k=0.6):
        X, Y, F, _ = self.proj(np.asarray(lons, float), np.asarray(lats, float), grow)
        return smooth(list(zip(X.tolist(), Y.tolist())), True, k), float(np.mean(F))


def _ws_masky(lon, lat):
    """1 where the off-white face (mask and cheek ruffs) is, 0 on the tabby (lon/lat arrays)."""
    lon = np.abs(np.asarray(lon, float)); lat = np.asarray(lat, float)
    top = 0.50 - 0.26 * lon ** 2
    return (lon < 1.55) & (lat < top) & (lat > -1.45)


# the fur tufts round the head (lon, lat anchors; fixed in 3D so they never crawl when he turns)
def _u3n(v):
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-6)


def _ws_tuft_grid():
    out = []
    k = 0
    for la in np.arange(-1.42, 1.50, 0.13):
        n = max(8, int(round(52 * math.cos(la) + 6)))
        for i in range(n):
            lo = -PI + 2 * PI * (i + 0.5 * (k % 2)) / n
            out.append((lo, la + 0.035 * (hash01(k * 3 + i, 1301) - 0.5), hash01(k * 7 + i, 1302), hash01(k * 5 + i, 1303)))
        k += 1
    return np.array(out)


_WS_TUFTS = _ws_tuft_grid()


_WS_CLUMPS = (((1.00, -0.62), 0.8), ((1.20, -0.22), 0.8), ((0.68, -1.06), 0.7),
              ((1.34, 0.06), 0.4), ((0.88, -0.86), 0.4), ((1.12, -0.44), 0.35), ((0.42, -1.22), 0.4), ((1.40, -0.62), 0.35))


def _ws_tuft_len(lon, lat, r):
    """Tuft length (cm) by place: long flaring cheek ruffs gathered in matted clumps (3 large, 5 medium, many small),
    a shaggy ruff under the jaw, short fur on the crown."""
    alon = np.abs(lon)
    cheek = np.exp(-((lat + 0.35) / 0.46) ** 2) * np.clip((alon - 0.55) / 0.5, 0, 1) * np.clip((2.4 - alon) / 0.6, 0, 1)
    jaw = np.exp(-((lat + 1.15) / 0.3) ** 2)
    base = 1.3 + 0.6 * np.clip(-lat, 0, 1)
    sh = np.where(np.asarray(lon) < 0, 0.05, 0.0)          # the two sides do not mirror exactly
    cl = 1.0
    for (cl0, ca0), g in _WS_CLUMPS:
        cl = cl + g * np.exp(-((alon - cl0) / 0.11) ** 2 - ((lat - ca0 - sh) / 0.13) ** 2)
    return (base + 6.2 * cheek + 2.6 * jaw) * (0.40 + 0.75 * r ** 1.5) * cl


def _ws_fur_tufts(c, hd, pal, det, lw):
    """Jagged fur round the head's outline: tufts anchored in 3D, drawn only where they stand off the silhouette; the
    face-coloured cheek ruffs flare out and down, the tabby ones behind."""
    T = _WS_TUFTS
    lon, lat, r1, r2 = T[:, 0], T[:, 1], T[:, 2], T[:, 3]
    L = _ws_head_local(lon, lat)
    Bn = hd.normal(L)
    F = hd.view.face(Bn)
    keep = (F < 0.42) & (F > -0.62)
    if det < 1: keep &= (r1 > 0.45)
    if not keep.any(): return
    lon, lat, r1, r2, L, Bn = lon[keep], lat[keep], r1[keep], r2[keep], L[keep], Bn[keep]
    ln = _ws_tuft_len(lon, lat, r1) * (0.6 if pal.get('tv') else 1.0)
    nb = Bn / np.maximum(np.linalg.norm(Bn, axis=1, keepdims=True), 1e-6)
    down = (hd.M @ np.array([0.0, 1.0, 0.0]))
    back = (hd.M @ np.array([0.0, 0.0, -1.0]))
    drop = 0.25 + 0.5 * np.exp(-((lat + 0.3) / 0.5) ** 2)
    d = nb + down[None, :] * drop[:, None] + back[None, :] * 0.15 + (r2[:, None] - 0.5) * 0.4 * (hd.M @ np.array([1.0, 0.0, 0.0]))[None, :]
    d = d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-6)
    B0 = hd.body(L)
    B1 = B0 + d * ln[:, None]
    X0, Y0, _, _ = hd.view.pa(B0); X1, Y1, _, _ = hd.view.pa(B1)
    mk = _ws_masky(lon, lat)
    # the under-layer: the same clumps a little longer, swung down, in a darker tone
    B2 = B0 + _u3n(d + down[None, :] * 0.35) * (ln * 1.2)[:, None]
    X2, Y2, _, _ = hd.view.pa(B2)
    under = {True: skia.Path(), False: skia.Path()}
    for i in range(len(lon)):
        dx, dy = X2[i] - X0[i], Y2[i] - Y0[i]
        Ln = math.hypot(dx, dy)
        if Ln < 1.0 or ln[i] < 2.5: continue
        w = (1.8 + 1.1 * r2[i]) * (1.0 + 0.45 * min(ln[i] / 7.0, 1.4))
        nx, ny = -dy / Ln * w, dx / Ln * w
        under[bool(mk[i])].addPoly([skia.Point(X0[i] - nx, Y0[i] - ny), skia.Point(X0[i] + dx * 0.6 - nx * 0.4, Y0[i] + dy * 0.6 - ny * 0.4),
                                    skia.Point(X2[i], Y2[i]), skia.Point(X0[i] + dx * 0.5 + nx * 0.45, Y0[i] + dy * 0.5 + ny * 0.45),
                                    skia.Point(X0[i] + nx, Y0[i] + ny)], True)
    for m_, col in ((False, pal['fur_dk']), (True, '#8f8468' if not pal.get('tv') else pal['mask_sh'])):
        p = under[m_]
        if p.countPoints() == 0: continue
        c.line(p, lw * 1.3, pal['line'], 235)
        c.fill(p, col)
    paths = {True: skia.Path(), False: skia.Path()}
    for i in range(len(lon)):
        dx, dy = X1[i] - X0[i], Y1[i] - Y0[i]
        Ln = math.hypot(dx, dy)
        if Ln < 0.6: continue
        w = (1.5 + 0.9 * r2[i]) * (1.0 + 0.45 * min(ln[i] / 7.0, 1.4))
        nx, ny = -dy / Ln * w, dx / Ln * w
        bend = (r2[i] - 0.5) * 0.35
        tip = (X1[i] + ny * bend * 0, Y1[i] - nx * bend * 0)
        q = [(X0[i] - nx - dx * 0.15, Y0[i] - ny - dy * 0.15), (X0[i] + dx * 0.55 - nx * 0.45 + nx * bend, Y0[i] + dy * 0.55 - ny * 0.45 + ny * bend),
             tip, (X0[i] + dx * 0.5 + nx * 0.5 + nx * bend, Y0[i] + dy * 0.5 + ny * 0.5 + ny * bend), (X0[i] + nx - dx * 0.15, Y0[i] + ny - dy * 0.15)]
        paths[bool(mk[i])].addPoly([skia.Point(*v) for v in q], True)
    for m_, col, sh in ((False, pal['fur'], pal['fur_dk']), (True, pal['mask_edge'], pal['mask_sh'])):
        p = paths[m_]
        if p.countPoints() == 0: continue
        c.line(p, lw * 1.0, pal['line'], 200)
        if det >= 1:                 # a darker under-layer, the tuft itself nudged up-left over it (cheap shade, no path ops)
            c.fill(p, sh)
            q = skia.Path(p); q.offset(-0.45, -0.6); c.fill(q, col)
        else:
            c.fill(p, col)


def _ws_fur_strokes(c, hd, pal, det, lw, n=420):
    """Short fur strokes over the head (flowing out from the nose, back over the crown), a darker and a lighter set."""
    if det < 1: return
    n = n if det >= 2 else n // 2
    i = np.arange(n)
    lon = -PI + 2 * PI * np.array([hash01(k, 1311) for k in i])
    lat = -1.35 + 2.75 * np.array([hash01(k, 1312) for k in i])
    lat = np.where(np.abs(lon) > 2.2, lat, lat)
    sgn = np.sign(lon); sgn[sgn == 0] = 1
    mk = _ws_masky(lon, lat)
    dlo = 0.075 * np.sin(lon) * np.where(np.abs(lon) < 1.7, 1.0, 0.4)
    dla = np.where(lat > 0.45, 0.07, -0.05 - 0.03 * np.abs(np.sin(lon)))
    X0, Y0, F0, _ = hd.proj(lon, lat, 0.1)
    X1, Y1, F1, _ = hd.proj(lon + dlo, lat + dla, 0.1)
    sets = {('m', 0): skia.Path(), ('m', 1): skia.Path(), ('f', 0): skia.Path(), ('f', 1): skia.Path()}
    for k in range(n):
        if F0[k] < 0.12 or F1[k] < 0.05: continue
        key = ('m' if mk[k] else 'f', k % 2)
        p = sets[key]
        mx, my = (X0[k] + X1[k]) / 2 + (Y1[k] - Y0[k]) * 0.15, (Y0[k] + Y1[k]) / 2 - (X1[k] - X0[k]) * 0.15
        p.moveTo(X0[k], Y0[k]); p.quadTo(mx, my, X1[k], Y1[k])
    c.line(sets[('m', 0)], lw * 0.55, pal['mask_sh'], 150)
    c.line(sets[('m', 1)], lw * 0.45, '#fffbf0', 90 if pal['grime'] > 0 else 130)
    c.line(sets[('f', 0)], lw * 0.6, pal['fur_dk'], 190)
    c.line(sets[('f', 1)], lw * 0.5, pal['fur_hi'], 140)


def _grin_lat(lon, slip=0.0):
    """THE GRIN's upper and lower lip (lat) at lon: from under the whisker pads up into the cheeks (corners at +-1.12)."""
    a = np.clip(np.abs(np.asarray(lon, float)) / 1.12, 0.0, 1.0)
    up = -0.39 + 0.30 * a ** 1.6 + 0.035 * np.exp(-(np.asarray(lon, float) / 0.07) ** 2)
    lo = -0.72 + 0.63 * a ** 1.8
    return up, lo


def _ws_grin(c, hd, pal, det, lw, dlo, dla, colr=None, a=255, glow=0.0):
    """The mouth: dark inside, a flat row of white painted teeth along the upper lip, small pointed canines, a short lower
    row; thick painted lips; the corners pushed up into the cheeks with a crease."""
    def up_f(lon): return _grin_lat(lon - dlo)[0] + dla
    def lo_f(lon): return _grin_lat(lon - dlo)[1] + dla
    g = hd.region(-1.12 + dlo, 1.12 + dlo, lo_f, up_f, 32, 4, 0.2, 0.0)
    if g is None: return
    ghost = colr is not None
    if ghost:
        c.fill(g, colr, a); return
    c.fill(g, pal['mouth'])
    with c.clip(g):
        # upper teeth: a flat painted row, too many of them; small pointed canines
        tu = hd.region(-0.98 + dlo, 0.98 + dlo, lambda lon: up_f(lon) - 0.12, lambda lon: up_f(lon) + 0.02, 26, 1, 0.22, -0.05)
        tl = hd.region(-0.80 + dlo, 0.80 + dlo, lambda lon: lo_f(lon) - 0.02, lambda lon: lo_f(lon) + 0.06, 20, 1, 0.22, -0.05)
        tcol = pal['teeth'] if glow <= 0 else '#fffbe8'
        for tp in (tu, tl):
            if tp is not None: c.fill(tp, tcol)
        for s in (-1, 1):
            for lk, top, dd in ((0.40, True, 0.085), (0.52, False, 0.07)):
                lo_ = s * lk + dlo
                if top:
                    u0 = up_f(np.array([lo_ - 0.05, lo_ + 0.05]))
                    pth, fc = hd.shape([lo_ - 0.05, lo_ + 0.05, lo_ + 0.008 * s], [u0[0] - 0.115, u0[1] - 0.115, u0[0] - 0.115 - dd])
                else:
                    l0 = lo_f(np.array([lo_ - 0.045, lo_ + 0.045]))
                    pth, fc = hd.shape([lo_ - 0.045, lo_ + 0.045, lo_], [l0[0] + 0.055, l0[1] + 0.055, l0[0] + 0.055 + dd])
                if fc > 0.02:
                    c.fill(pth, tcol); c.line(pth, lw * 0.45, pal['line'], 200)
        if det >= 1:
            for k in range(-11, 12):          # tooth gaps
                lk = k * 0.085 + dlo
                if abs(k * 0.085) > 0.96: continue
                u_ = up_f(np.array([lk]))[0]
                for run in hd.curve(np.array([lk, lk]), np.array([u_ - 0.12, u_ + 0.01]), 0.25):
                    c.line(poly(run, False), lw * 0.55, pal['line'], 200)
                if abs(k * 0.085) < 0.78:
                    l_ = lo_f(np.array([lk]))[0]
                    for run in hd.curve(np.array([lk, lk]), np.array([l_ - 0.01, l_ + 0.06]), 0.25):
                        c.line(poly(run, False), lw * 0.5, pal['line'], 190)
            if pal['grime'] > 0:
                for k in range(6):            # old paint: chips and stains on the teeth
                    lo_ = -0.9 + 1.8 * hash01(k, 621)
                    d_, fd = hd.disc(lo_ + dlo, up_f(np.array([lo_ + dlo]))[0] - 0.05, 0.03, 0.025, 6, 0.3)
                    if fd > 0.05: c.fill(d_, '#a99a74', 170)
            if tu is not None: c.fill(_crescent(tu, 0, -1.0), '#5a4a3a', 90)
    lon = np.linspace(-1.12, 1.12, 61) + dlo
    up, lo_ = _grin_lat(lon - dlo)
    for run in hd.curve(lon, up + dla, 0.25) + hd.curve(lon, lo_ + dla, 0.25):
        c.line(smooth(run, False), lw * 1.5, pal['line'])
    for s in (-1, 1):                         # the corners dig up into the cheeks
        lo0 = s * 1.12 + dlo; la0 = _grin_lat(np.array([s * 1.12]))[0][0] + dla
        for run in hd.curve(np.array([lo0 - s * 0.06, lo0 + s * 0.02, lo0 + s * 0.04]), np.array([la0 - 0.06, la0, la0 + 0.09]), 0.25):
            c.line(smooth(run, False), lw * 1.1, pal['line'], 230)


def _ws_eyes(c, hd, pal, det, lw, glow=0.0):
    """Painted almond cat eyes (yellow, no lids, never blink): thick dark rims flicked up at the outer corner, tiny
    pinprick pupils (his left one higher), a hard glint that catches any light."""
    out = []
    tv = bool(pal.get('tv'))
    for s, la0, pdl in ((1, 0.165, 0.03), (-1, 0.13, -0.005)):
        lo0 = s * 0.37
        x = np.linspace(-1, 1, 15)
        if tv:                              # the 1994 tape: rounder, friendlier painted eyes (still wrong: no lids)
            upl = 0.11 * (1 - x ** 2) ** 0.7; lol = -0.09 * (1 - x ** 2) ** 0.7; tilt = 0.0 * x
        else:                               # flat almond, the inner corner pressed down (a scowl under the paint)
            upl = 0.075 * (1 - x ** 2) ** 0.85 - 0.035 * np.clip(-x, 0, 1) ** 2; lol = -0.06 * (1 - x ** 2) ** 0.9
            tilt = 0.045 * x
        if not tv and det >= 1 and glow <= 0:      # a thin dark shadow above the eye: it sits in shade under the brow
            sh_, fsh = hd.shape(np.concatenate([lo0 + s * 0.24 * x, lo0 + s * 0.24 * x[::-1]]),
                                np.concatenate([la0 + 0.02 + 0.10 * (1 - x ** 2) + 0.045 * x, (la0 + 0.075 * (1 - x ** 2) + 0.045 * x - 0.035 * np.clip(-x, 0, 1) ** 2)[::-1]]), 0.18, 0.4)
            if fsh > 0.02: c.fill(sh_, pal['mask_sh'], 140); c.fill(sh_, '#3a2c22', 60)
        lons = np.concatenate([lo0 + s * 0.19 * x, lo0 + s * 0.19 * x[::-1]])
        lats = np.concatenate([la0 + upl + tilt, la0 + (lol + tilt)[::-1]])
        e, fe = hd.shape(lons, lats, 0.2, 0.35)
        if fe <= 0.02: continue
        so, fso = hd.disc(lo0, la0 + 0.01, 0.26, 0.17, 16, 0.12)
        if glow <= 0 and det >= 1 and fso > 0.03: c.fill(so, pal['mask_sh'], 110)
        c.fill(e, pal['eye'] if glow <= 0 else '#f6ec9a')
        if glow <= 0: c.fill(_crescent(e, 0, 1.2), '#6a5a1a', 120)
        pu, fp = hd.shape([lo0 + s * pdl + 0.026 * math.cos(a_) for a_ in np.linspace(0, 2 * PI, 10, endpoint=False)],
                          [la0 + 0.015 + 0.036 * math.sin(a_) for a_ in np.linspace(0, 2 * PI, 10, endpoint=False)], 0.25, 0.8)
        if fp > 0.02: c.fill(pu, pal['pupil'])
        gl, fg = hd.disc(lo0 + s * 0.06, la0 + 0.06, 0.028, 0.022, 8, 0.3)
        if fg > 0.02: c.fill(gl, '#ffffff', 235)
        c.line(e, lw * (1.25 if glow <= 0 else 0.6), pal['line'])
        out.append(e)
    return out


def _ws_muzzle(c, hd, pal, det, lw):
    """The whisker pads (two puffy ovals over the top of the grin, follicle dots), the small dark triangular cat nose
    and the philtrum."""
    for s in (-1, 1):
        pd, fp = hd.disc(s * 0.16, -0.32, 0.165, 0.105, 18, 0.35)
        if fp <= 0.02: continue
        c.fill(pd, pal['pad'])
        c.fill(_crescent(pd, 0.0, -1.3), pal['mask_sh'], 170)
        if det >= 1:
            for r_ in range(3):
                for k in range(3):
                    d_, fd = hd.disc(s * (0.11 + 0.055 * k), -0.29 - 0.035 * r_ + 0.012 * k, 0.012, 0.010, 6, 0.4)
                    if fd > 0.05: c.fill(d_, '#5a4a3e', 200)
        for run in hd.curve(s * np.array([0.02, 0.10, 0.22, 0.31]), np.array([-0.28, -0.24, -0.25, -0.31]), 0.35):
            c.line(smooth(run, False), lw * 0.8, pal['line'], 200)
    nz, fn = hd.shape([-0.10, 0.10, 0.0], [-0.115, -0.115, -0.215], 0.45, 0.45)
    if fn > 0.02:
        c.fill(nz, pal['nose']); c.fill(_crescent(nz, 0, -0.8), '#000000', 90)
        hl, fh = hd.disc(-0.03, -0.14, 0.03, 0.015, 6, 0.5)
        if fh > 0.02: c.fill(hl, '#c9a8a0', 160)
        c.line(nz, lw * 0.8, pal['line'])
    for run in hd.curve(np.array([0.0, 0.0]), np.array([-0.215, -0.27]), 0.45):
        c.line(poly(run, False), lw * 0.9, pal['line'])


def _ws_whiskers(c, hd, pal, det, lw, near):
    """Long whiskers out of the pads, past the cheek ruffs: pale with a dark edge (they read on the face and on the
    dark); two bent, one snapped short. near: draw the side facing the lens (else the far side, behind the head)."""
    view = hd.view
    if getattr(hd, 'hpx', 999.0) < 40.0: return          # too small to read: they would only stick out like antennae
    for s in (-1, 1):
        root = hd.body(_ws_head_local(s * 0.31, -0.29))[0]
        fc = float(view.face(hd.normal(_ws_head_local(s * 0.6, -0.3)[None, :]))[0])
        if (fc > -0.15) != near: continue
        if not near and float(view.face(hd.normal(_ws_head_local(0.0, -0.3)[None, :]))[0]) < -0.3: continue
        spec = ((-0.42, 16.0, 0.0), (-0.20, 19.0, 0.6 if s > 0 else 0.0), (0.02, 15.0, -1.0 if s > 0 else 0.0))
        for k, (dy, ln, kink) in enumerate(spec):
            if det < 1 and k == 1: continue
            d = hd.M @ _u3(np.array([s * 1.0, dy, 0.22]))
            dn = hd.M @ np.array([0.0, 1.0, 0.0])
            p0 = root + hd.M @ np.array([0.0, (k - 1.0) * 1.1, 0.4])
            if kink < 0:                     # snapped: a short stub
                pts = [p0, p0 + d * 4.5 + dn * 0.8]
            elif kink > 0:                   # bent halfway, drooping
                pts = [p0, p0 + d * ln * 0.5 - dn * 0.4, p0 + d * ln * 0.5 + _u3(d * 0.6 + dn) * ln * 0.45]
            else:
                pts = [p0, p0 + d * ln * 0.5 - dn * 0.6, p0 + d * ln - dn * 0.2]
            p2 = [view.p2(q) for q in pts]
            _, _, _, ff = view.p(p0)
            w0 = lw * 0.5
            tp = _tube(p2, [w0, w0 * 0.55, 0.05 * w0][:len(p2)] if len(p2) == 3 else [w0, w0 * 0.6], 0.6)
            c.line(tp, lw * 0.35, pal['line'], 110)
            c.fill(tp, pal['whisk'], 245)


def _ws_head_draw(c, R, view, P, det, t, light, pal, tv=False):
    """The mascot head: ears behind, the jagged fur outline (cheek ruffs flaring out and down), the tabby crown with
    dark stripes fading into the off-white matted face, layered cheek fur, fur strokes, soft shading, the painted cat
    eyes, the muzzle and nose, THE GRIN (it never moves), whiskers; ears in front (a ticket-punch hole through the left
    one); under the VHS slip the grin slides out of register."""
    hd = _WSHead(R, view, P, pal)
    lw = c.lw
    m_ = c.cv.getTotalMatrix()
    hd.hpx = 41.0 * c.s * math.sqrt(abs(m_.getScaleX() * m_.getScaleY() - m_.getSkewX() * m_.getSkewY()))
    far = hd.hpx < 60.0                    # far LOD: bigger ears lifted clear of the brim, no whiskers
    sil = hd.sil()
    ears = []
    for s in (-1, 1):
        lift = np.array([[0.0, -3.0, 0.0]]) if far else np.zeros((1, 3))
        b1 = _ws_head_local(s * 0.42, 0.98)[None, :] + lift; b2 = _ws_head_local(s * 1.30, 0.42)[None, :] + lift
        mid = _ws_head_local(s * 0.86, 0.78)[None, :] + lift
        tip = mid[0] + np.array([s * 11.0, -15.0, -2.5]) * (1.3 if far else 1.0)
        b3 = _ws_head_local(s * 0.95, 0.95)[None, :] + np.array([[0.0, 0.0, -7.0]]) + lift
        pts_l = np.vstack([b1, tip[None, :], b2, b3])
        B = hd.body(pts_l)
        X, Y, zd, _ = view.pa(B)
        facing = float(view.face(hd.M @ _u3(np.array([s * 0.35, -0.15, 1.0])))[0])     # the inner side looks forward
        ears.append((float(np.mean(zd)), s, list(zip(X.tolist(), Y.tolist())), facing, B))
    hz = view.depth(hd.C)
    for z_, s, pts, fc, B in ears:
        if z_ < hz - 2.0: _ws_ear(c, view, pts, fc, s, pal, det, B)
    _ws_whiskers(c, hd, pal, det, lw, near=False)
    if det >= 1 and not pal.get('tv'):     # costume: a black gap between the chin ruff and the collar
        q = hd.body(np.array([[0.0, _WS_CHIN + 1.5, -4.0]]))[0]
        X_, Y_ = view.p2(q); _, _, _, f_ = view.p(q)
        c.fill(oval(X_, Y_ + 1.0 * f_, 13.0 * f_, 4.2 * f_), '#050404', 245)
    c.line(sil, lw * 2.2, pal['line'])
    _ws_fur_tufts(c, hd, pal, det, lw)
    c.fill(sil, pal['fur'])
    rim = light.get('rim') if light else None
    with c.clip(sil):
        if det >= 1:                           # tabby: tapered stripes running from the crown down the back of the skull
            for k, (d0, l_end, w_) in enumerate(((0.0, -0.45, 2.2), (-0.36, 0.25, 1.7), (0.33, -0.15, 1.8), (-0.74, -0.30, 1.4), (0.70, 0.40, 1.3),
                                                 (-0.18, -0.85, 1.0), (0.52, -0.80, 1.0))):
                l_beg = 1.38 if k < 5 else -0.25                  # two short broken bars low on the nape
                lats = np.linspace(l_beg, l_end, 5)
                lons = PI + d0 * (1.0 + 0.22 * (1.38 - lats)) + 0.05 * np.sin(2.3 * lats + 1.7 * k)
                _ws_paint_stroke(c, hd, list(zip(lons, lats)), w_, pal['fur_dk'], 195)
        # the face: a dirty yellowed edge, then the off-white matted mask (jagged where it meets the tabby)
        mk = hd.region(-1.50, 1.50, -1.5, lambda lo: 0.56 - 0.26 * lo ** 2 + 0.035 * np.abs(np.sin(13 * lo)), 30, 12, 0.06)
        if mk is not None:
            c.fill(mk, pal['mask_edge'])
            mk2 = hd.region(-1.42, 1.42, lambda lo: -1.40 + 0.5 * np.clip((np.abs(lo) - 1.0) / 0.42, 0, 1) ** 2,
                            lambda lo: 0.47 - 0.26 * lo ** 2 - 0.04 * np.abs(np.sin(11 * lo + 0.5)) - 0.12 * np.clip((np.abs(lo) - 1.0) / 0.42, 0, 1) ** 2,
                            28, 12, 0.07)
            if mk2 is not None: c.fill(mk2, pal['mask'])
            if det >= 1:
                # forehead: a tapered tabby M, three lines running back from it over the crown, two bars on each cheek
                strokes = [(((-0.31, 0.33), (-0.21, 0.57), (-0.09, 0.43), (0.0, 0.53), (0.09, 0.43), (0.21, 0.57), (0.31, 0.33)), 1.5),
                           (((-0.11, 0.66), (-0.12, 0.95), (-0.10, 1.30)), 1.3), (((0.0, 0.62), (0.0, 0.95), (0.0, 1.35)), 1.5),
                           (((0.11, 0.66), (0.12, 0.95), (0.10, 1.30)), 1.3)]
                for s in (-1, 1):
                    strokes += [(((s * 0.62, 0.10), (s * 0.82, 0.08), (s * 1.02, 0.12), (s * 1.20, 0.20)), 1.0),
                                (((s * 0.70, -0.06), (s * 0.90, -0.08), (s * 1.12, -0.03)), 0.9)]
                for pts_, w_ in strokes:
                    _ws_paint_stroke(c, hd, pts_, w_, pal['fur_dk'], 215)
                if pal['grime'] > 0:
                    for k in range(9):         # matted clumps and old stains
                        lo_ = -1.3 + 2.6 * hash01(k, 611); la_ = -1.1 + 1.4 * hash01(k, 612)
                        pth, fc = hd.disc(lo_, la_, 0.08 + 0.06 * hash01(k, 613), 0.05, 7, 0.08)
                        if fc > 0.05: c.fill(pth, '#8a7650', int(70 * pal['grime']))
                c.texture(mk, 'fabric', 0.12 * pal['grime'] + 0.04, 0.45)
        _ws_fur_strokes(c, hd, pal, det, lw)
        # soft shading: lit from the front-left, darker toward the outline and under the jaw
        c.radial(sil, *view.p2(hd.body(np.array([[-5.0, -6.0, 16.0]]))[0]), 34.0,
                 [(0, '#ffffff', 45), (0.55, '#000000', 0), (1, '#000000', 125)])
        cy_ = view.p2(hd.body(np.array([[0.0, 0.0, 0.0]]))[0])[1]
        c.grad(sil, 0, cy_ + 6.0, 0, cy_ + 24.0, [(0, '#000000', 0), (1, '#000000', 125)])      # shade under the jaw
        if det >= 1:                           # costume: one faint seam from the crown down to between the eyes
            for run in hd.curve(np.full(14, 0.015), np.linspace(1.5, 0.30, 14), 0.15, 0.1):
                c.line(smooth(run, False), lw * 0.55, pal['fur_dk'] if pal.get('tv') else '#4a3e30', 120)
                if det >= 2:
                    for i_ in range(1, len(run) - 1, 2):
                        x_, y_ = run[i_]; dx_, dy_ = run[i_ + 1][0] - run[i_ - 1][0], run[i_ + 1][1] - run[i_ - 1][1]
                        d_ = math.hypot(dx_, dy_) or 1.0
                        c.line(poly([(x_ - dy_ / d_ * 0.7, y_ + dx_ / d_ * 0.7), (x_ + dy_ / d_ * 0.7, y_ - dx_ / d_ * 0.7)], False), lw * 0.4, '#4a3e30', 100)
        if light and light.get('under'):     # lit from below (a phone, a dashboard, the sodium glow)
            ua = light.get('under_a', 150)
            c.grad(sil, 0, cy_ - 26.0, 0, cy_ + 24.0, [(0, '#000000', 0.75 * ua), (0.4, '#000000', 0.15 * ua), (0.7, light['under'], 0.35 * ua), (1, light['under'], 0.8 * ua)])
        if rim:
            c.fill(_crescent(sil, -light.get('side', 1) * 1.1, 0.25), rim, light.get('rim_a', 60) * 0.45)
    # the painted face
    _ws_eyes(c, hd, pal, det, lw)
    slip = clamp(P.ws_slip)
    dlo, dla = 0.45 * slip + 0.04 * slip * math.sin(t * 37.0), -0.24 * slip
    if slip > 0.02:
        _ws_grin(c, hd, pal, det, lw, dlo + 0.07, dla, '#ff2a3a', int(120 * slip))
        _ws_grin(c, hd, pal, det, lw, dlo - 0.07, dla + 0.02, '#2ae0ff', int(120 * slip))
    _ws_grin(c, hd, pal, det, lw, dlo, dla)
    _ws_muzzle(c, hd, pal, det, lw)
    if det >= 1 and not pal.get('tv'):
        bs, ds, ls = [], [], []
        for s in (-1, 1):
            for k, (lo_, la_) in enumerate(((1.14, -0.30), (1.20, -0.42), (1.06, -0.52), (0.96, -0.62), (1.24, -0.20))):
                if s < 0 and k == 4: continue
                q0 = hd.body(_ws_head_local(s * lo_ + dlo, la_ + dla)[None, :])
                q1 = hd.body(_ws_head_local(s * (lo_ + 0.10) + dlo, la_ - 0.10 + dla)[None, :])
                F_ = float(view.face(hd.normal(_ws_head_local(s * lo_, la_)[None, :]))[0])
                if F_ < 0.1: continue
                x0_, y0_ = view.p2(q0[0]); x1_, y1_ = view.p2(q1[0])
                bs.append((x0_, y0_)); ds.append((x1_ - x0_, y1_ - y0_)); ls.append(3.2 + 1.2 * hash01(k, 1371))
        if bs: _ws_tufts2d(c, bs, ds, ls, 0.9, '#c9b98a', pal, lw * 0.6, det)
    if light and light.get('under') and det >= 1:
        with c.clip(sil):
            cy_ = view.p2(hd.body(np.array([[0.0, 0.0, 0.0]]))[0])[1]
            c.grad(sil, 0, cy_ - 4.0, 0, cy_ + 24.0, [(0, light['under'], 0), (1, light['under'], 0.22 * light.get('under_a', 150))])
    _ws_whiskers(c, hd, pal, det, lw, near=True)
    if slip > 0.05:
        bx = [view.p2(hd.body(np.array([[x_, y_, 0.0]]))[0]) for x_, y_ in ((-26, -24), (26, 22))]
        with c.clip(sil):
            ws_tracking(c, min(bx[0][0], bx[1][0]) - 5, min(bx[0][1], bx[1][1]), abs(bx[1][0] - bx[0][0]) + 10, abs(bx[1][1] - bx[0][1]), slip, t, 7)
    for z_, s, pts, fc, B in ears:          # the hat (drawn next) tucks the ear bases under its brim
        if z_ >= hz - 2.0: _ws_ear(c, view, pts, fc, s, pal, det, B)
    R['_ears_late'] = None
    return hd


def _ws_paint_stroke(c, hd, pts, w, colr, a=215):
    """A tapered painted stroke on the head surface through (lon, lat) points, w = its widest (cm); only facing runs."""
    pts = np.asarray(pts, float)
    t_ = np.linspace(0, 1, len(pts)); tt = np.linspace(0, 1, 4 * len(pts))
    lons = np.interp(tt, t_, pts[:, 0]); lats = np.interp(tt, t_, pts[:, 1])
    X, Y, F, _ = hd.proj(lons, lats, 0.12)
    _, _, _, f = hd.view.pa(hd.body(_ws_head_local(lons, lats)))
    run, wl = [], []
    for i in range(len(tt)):
        if F[i] > 0.04:
            run.append((float(X[i]), float(Y[i]))); wl.append(w * float(f[i]) * (0.25 + 0.75 * math.sin(PI * tt[i]) ** 0.6))
    if len(run) > 2: c.fill(_tube(run, wl, 0.6), colr, a)


def _ws_glow_feats(c, R, view, P, det, t, pal, amount):
    """In near darkness only his painted eyes and the teeth catch the light."""
    hd = _WSHead(R, view, P, pal)
    lw = c.lw
    c.cv.saveLayer(None, skia.Paint(Alphaf=float(clamp(amount))))
    _ws_eyes(c, hd, pal, det, lw, glow=1.0)
    slip = clamp(P.ws_slip)
    dlo, dla = 0.45 * slip, -0.24 * slip
    mouth = hd.region(-1.12 + dlo, 1.12 + dlo, lambda lon: _grin_lat(lon - dlo)[1] + dla, lambda lon: _grin_lat(lon - dlo)[0] + dla, 32, 4, 0.2, 0.0)
    if mouth is not None:
        with c.clip(mouth):
            _ws_grin(c, hd, pal, det, lw, dlo, dla, glow=1.0)
    c.cv.restore()


def _ws_ear(c, view, pts, facing, s, pal, det, B):
    """A tall pointed cat ear: tabby outside, dusty pink-grey inside with pale fur tufts, a tuft at the tip, a worn
    notch; the ticket-punch hole through his left ear."""
    (x0, y0), (xt, yt), (x2, y2), (x3, y3) = pts
    pts = pts[:3]
    ext = (xt + (xt - (x0 + x2) / 2) * 0.16, yt + (yt - (y0 + y2) / 2) * 0.16)
    m1 = (x0 * 0.45 + xt * 0.55 - (y2 - y0) * 0.03, y0 * 0.45 + yt * 0.55)
    nt = 0.62
    n0 = (x2 * (1 - nt) + xt * nt, y2 * (1 - nt) + yt * nt)
    n1 = (x2 * (1 - nt + 0.06) + xt * (nt - 0.06), y2 * (1 - nt + 0.06) + yt * (nt - 0.06))
    nc = ((n0[0] + n1[0]) / 2 + ((x0 + x2) / 2 - xt) * 0.06, (n0[1] + n1[1]) / 2 + ((y0 + y2) / 2 - yt) * 0.06)
    outer = smooth([pts[0], m1, (xt, yt), ext, (xt, yt), n0, nc, n1, pts[2]], False, 0.15)
    tri = poly([pts[0], m1, (xt, yt), n0, nc, n1, pts[2]], True)
    try:
        tri = union(tri, poly(_hull([pts[0], (xt, yt), pts[2], (x3, y3)]), True))
    except Exception:
        pass
    hole = None
    if s > 0:                       # the ticket-punch hole: inside the ear, well up from the base toward the tip
        cpt = (B[0] + B[2]) * 0.5 * 0.42 + B[1] * 0.58 + (B[2] - B[0]) * 0.06     # well clear of the hat brim
        X, Y = view.p2(cpt)
        _, _, _, f = view.p(cpt)
        r = 1.7 * f
        hole = oval(X, Y, r, r * 0.92)
    ctxm = c.clip(hole, diff=True) if hole is not None else _noop()
    with ctxm:
        c.fill(tri, pal['fur'])
        if facing > 0.2:
            cx, cy = (x0 + x2 + xt) / 3, (y0 + y2 + yt) / 3
            inner = smooth([(x0 * 0.72 + cx * 0.28, y0 * 0.72 + cy * 0.28), (xt * 0.78 + cx * 0.22, yt * 0.78 + cy * 0.22),
                            (x2 * 0.72 + cx * 0.28, y2 * 0.72 + cy * 0.28)], True, 0.3)
            c.fill(inner, pal['ear_in'])
            c.fill(_crescent(inner, 0, 1.2), '#6e5655', 150)
            if det >= 1:                        # pale tufts sprouting from inside the ear
                bx, by = (x0 + x2) / 2, (y0 + y2) / 2
                for k in range(5):
                    u = (k + 0.5) / 5
                    sx, sy = x0 + (x2 - x0) * u, y0 + (y2 - y0) * u
                    ex, ey = sx + (xt - bx) * (0.42 + 0.15 * hash01(k, 1321)), sy + (yt - by) * (0.42 + 0.15 * hash01(k, 1321))
                    c.line(smooth([(sx, sy), ((sx + ex) / 2 + (cx - sx) * 0.15, (sy + ey) / 2), (ex, ey)], False), c.lw * 0.8, pal['mask'], 220)
        elif det >= 1:                      # the back of the ear: tabby fur with stripes
            bx, by = (x0 + x2) / 2, (y0 + y2) / 2
            for k in range(3):
                u = 0.25 + 0.22 * k
                sx, sy = bx + (xt - bx) * u, by + (yt - by) * u
                hw = (1.0 - u) * 0.42
                c.line(poly([(sx + (x0 - bx) * hw, sy + (y0 - by) * hw), (sx + (x2 - bx) * hw, sy + (y2 - by) * hw)], False),
                       c.lw * 1.2, pal['fur_dk'], 200)
        c.line(tri, c.lw * 1.05, pal['line'])
    # a lynx tuft at the tip: 3-5 tapered strokes
    bx, by = (x0 + x2) / 2, (y0 + y2) / 2
    ax_, ay_ = xt - bx, yt - by
    L = math.hypot(ax_, ay_) or 1.0
    ux, uy = ax_ / L, ay_ / L
    nt_ = 4 if det >= 1 else 3
    for k in range(nt_):
        sp = (k - (nt_ - 1) / 2) * 0.28 + 0.1 * (hash01(k, 1381) - 0.5)
        ln = L * (0.24 + 0.08 * hash01(k, 1382))
        dx_, dy_ = ux * math.cos(sp) - uy * math.sin(sp), ux * math.sin(sp) + uy * math.cos(sp)
        tp = _tube([(xt - ux * L * 0.04, yt - uy * L * 0.04), (xt + dx_ * ln * 0.5, yt + dy_ * ln * 0.5), (xt + dx_ * ln, yt + dy_ * ln)],
                   [L * 0.05, L * 0.03, 0.01], 0.6)
        c.fill(tp, pal['fur_hi'] if k % 2 else pal['fur'])
        c.line(tp, c.lw * 0.35, pal['line'], 150)
    if hole is not None:            # a torn pale rim: the background shows through
        c.line(hole, c.lw * 0.45, pal['mask'], 230)
        c.line(hole, c.lw * 0.25, pal['line'], 160)


# ---------------------------------------------------------------------------------------------------- the hat
def _ws_hat_ring(hat, s, phi, rad=1.0):
    """Points on the hat at axial fraction s (0 base .. 1 top) and angle phi (0 = the hat's front). Above the dent the
    upper half folds about a hinge toward his left by hat['fold'] and the lower half squashes under a ceiling."""
    M = hat['M']
    base, ax, H = hat['base'], hat['ax'], hat['H']
    fwd = _u3(M @ np.array([0.0, 0.0, 1.0])); fwd = _u3(fwd - ax * float(np.dot(fwd, ax)))
    side = _u3(np.cross(ax, fwd))                       # toward his left (+x) for an upright head
    if float(np.dot(side, M @ np.array([1.0, 0.0, 0.0]))) < 0: side = -side
    phi = np.asarray(phi, float)
    r = (11.6 + 1.3 * s) * rad * (1.0 - 0.12 * math.exp(-((s - 0.5) / 0.06) ** 2))       # pinched at the dent
    off = r * (np.cos(phi)[:, None] * fwd[None, :] + np.sin(phi)[:, None] * side[None, :])
    sq = hat['squash']
    if s <= 0.5:
        return base + ax * (H * s * sq) + off
    hinge = base + ax * (H * 0.5 * sq)
    a = hat['fold'] + math.radians(8.0)                 # the upper half kinks at the dent even unfolded
    ca, sa = math.cos(a), math.sin(a)
    ax2 = ax * ca + side * sa
    side2 = side * ca - ax * sa
    off2 = r * (np.cos(phi)[:, None] * fwd[None, :] + np.sin(phi)[:, None] * side2[None, :])
    return hinge + ax2 * (H * (s - 0.5) * (1.0 if hat['fold'] < 1.5 else 0.8)) + off2


def _ws_hat_draw(c, R, view, P, det, t, light, pal):
    hat = R['hat']; lw = c.lw
    M = hat['M']
    m_ = c.cv.getTotalMatrix()
    if 41.0 * c.s * math.sqrt(abs(m_.getScaleX() * m_.getScaleY() - m_.getSkewX() * m_.getSkewY())) < 60.0 and not pal.get('tv'):
        # far LOD (silhouettes): push the crooked lean and the dent's kink so the chimney still reads as crooked
        side = _u3(M @ np.array([1.0, 0.0, 0.0])); a_ = math.radians(6.0)
        hat = dict(hat, ax=_u3(hat['ax'] * math.cos(a_) + side * math.sin(a_)), fold=hat['fold'] + math.radians(7.0))
    phis = np.linspace(-PI, PI, 33)
    # brim: a ragged oval round the base, a little wider at the sides
    br = []
    for k, ph in enumerate(phis[:-1]):
        rr = 14.6 + 1.2 * math.cos(2 * ph) + 0.9 * (hash01(k, 641) - 0.5)
        q = _ws_hat_ring(hat, 0.0, np.array([ph]), rr / 10.4)[0]
        br.append(view.p2(q))
    brim = smooth(br, True, 0.6)
    # a solid brim 3.5 cm thick: its edge band hangs below the top oval, dark underneath, chewed along the lower edge
    dn_ = -hat['ax'] * 3.5
    lo = []
    for k, ph in enumerate(phis[:-1]):
        rr = 14.6 + 1.2 * math.cos(2 * ph) + 0.9 * (hash01(k, 641) - 0.5)
        q = _ws_hat_ring(hat, 0.0, np.array([ph]), rr / 10.4)[0] + dn_ * (1.0 + 0.35 * (hash01(k, 642) - 0.5))
        lo.append(view.p2(q))
    try:
        band = union(poly(_hull(br + lo), True), brim)
    except Exception:
        band = brim
    c.fill(band, pal['hat_sh']); c.fill(band, '#2a2010', 120)
    c.line(band, lw, pal['line'])
    c.fill(brim, pal['hat_sh']); c.fill(brim, pal['hat'], 110); c.line(brim, lw * 0.8, pal['line'])
    ss = [0.0, 0.12, 0.25, 0.38, 0.5, 0.62, 0.75, 0.88, 1.0]
    rings = [np.array(view.pa(_ws_hat_ring(hat, s, phis))[:2]).T for s in ss]
    body = None
    for i in range(len(ss) - 1):
        h = poly(_hull(np.vstack([rings[i], rings[i + 1]])), True)
        body = h if body is None else union(body, h)
    if body is None: return
    c.fill(body, pal['hat'])
    # bands: two hazard bands wound DIAGONALLY round the crown (helical: they slant from every side; the seams behind)
    with c.clip(body):
        c.grad(body, rings[4][:, 0].min(), 0, rings[4][:, 0].max(), 0, [(0, pal['hat_hi'], 120), (0.45, pal['hat'], 0), (1, pal['hat_sh'], 200)])
        for b0 in (0.14, 0.53):
            quads = skia.Path(); anyq = False
            n = 48
            wb = 0.55

            def bu(ph):
                phw = ph if ph >= -PI + wb else ph + 2 * PI
                return (phw + PI - wb) / (2 * PI - 2 * wb) if phw <= PI - wb else 1.0 - (phw - (PI - wb)) / (2 * wb)
            for i in range(n):
                ph0 = -PI + 2 * PI * i / n; ph1 = ph0 + 2 * PI / n
                cen = [view.face(_u3(_ws_hat_ring(hat, b0 + 0.17, np.array([ph]))[0] - _ws_hat_ring(hat, b0 + 0.17, np.array([ph]), 0.0)[0]))[0]
                       for ph in (ph0, ph1)]
                if cen[0] + cen[1] <= 0: continue
                cor = []
                for ph, dh in ((ph0, 0.0), (ph1, 0.0), (ph1, 0.085), (ph0, 0.085)):
                    sv = b0 + 0.30 * bu(ph) + dh
                    cor.append(view.p2(_ws_hat_ring(hat, sv, np.array([ph]), 1.004)[0]))
                ar = sum(cor[k][0] * cor[(k + 1) % 4][1] - cor[(k + 1) % 4][0] * cor[k][1] for k in range(4))
                if ar < 0: cor = cor[::-1]
                quads.addPoly([skia.Point(*v) for v in cor], True); anyq = True
            if anyq: c.fill(quads, pal['band'], 235)
        if det >= 1:
            for k in range(9):             # scuffs and chewed paint
                sv = 0.06 + 0.88 * hash01(k, 651); ph = -1.2 + 2.4 * hash01(k, 652)
                q = _ws_hat_ring(hat, sv, np.array([ph]), 1.01)[0]
                if view.face(_u3(q - _ws_hat_ring(hat, sv, np.array([ph]), 0.0)[0]))[0] > 0.1:
                    X, Y = view.p2(q); _, _, _, f = view.p(q)
                    c.fill(oval(X, Y, (1.2 + 1.2 * hash01(k, 653)) * f, (0.5 + 0.4 * hash01(k, 654)) * f), pal['scuff'], 60)
            c.texture(body, 'fabric', 0.12, 0.5)
        if light and light.get('rim'):
            c.fill(_crescent(body, -light.get('side', 1) * 1.4, 0), light['rim'], light.get('rim_a', 60))
    # the dent: a crease across the pinch; crushed: accordion folds
    dent = [view.p2(q) for q in _ws_hat_ring(hat, 0.5, np.linspace(-1.2, 1.2, 9), 1.0)]
    c.line(smooth(dent, False), lw * 0.9, pal['line'], 200)
    if hat['squash'] < 0.95 or hat['fold'] > 0.6:
        for s_ in (0.18, 0.3, 0.42):
            fl = [view.p2(q) for q in _ws_hat_ring(hat, s_, np.linspace(-1.3, 1.3, 7), 1.0)]
            c.line(smooth(fl, False), lw * 0.7, pal['line'], 170)
    # the top cap (only when it faces the lens)
    tring = _ws_hat_ring(hat, 1.0, phis[:-1])
    nrm = _u3(tring.mean(0) - _ws_hat_ring(hat, 0.95, phis[:-1]).mean(0))
    if view.face(nrm)[0] > 0.02:
        cap = poly([view.p2(q) for q in tring], True)
        c.fill(cap, pal['hat_sh']); c.line(cap, lw * 0.8, pal['line'])
    c.line(body, lw, pal['line'])
    # the brim's front lip over the crown's base
    front = [view.p2(_ws_hat_ring(hat, 0.0, np.array([ph]), (14.6 + 1.2 * math.cos(2 * ph)) / 10.4)[0]) for ph in np.linspace(-1.5, 1.5, 9)]
    if view.face(M @ np.array([0.0, 0.0, 1.0]))[0] > -0.3:
        c.line(smooth(front, False), lw * 1.1, pal['line'])


# ---------------------------------------------------------------------------------------------------- body parts
def _ws_tube3(c, view, pts, widths, colr, sh, lw, light=None, line=True):
    """A limb through 3D points with widths in cm (scaled by perspective): fill, a shade band, outline."""
    X, Y, zd, f = view.pa(np.asarray(pts))
    p2 = list(zip(X.tolist(), Y.tolist()))
    ws = [w * ff for w, ff in zip(widths, f.tolist())]
    tp = _tube(p2, ws, 0.8)
    c.fill(tp, colr)
    if sh: c.fill(_crescent(tp, 1.2, 0.5), sh, 150)
    if light and light.get('rim'): c.fill(_crescent(tp, -light.get('side', 1) * 1.0, 0), light['rim'], light.get('rim_a', 60) * 0.8)
    if line: c.line(tp, lw, _WS_PAL['line'])
    return tp, p2


def _ws_stripes(c, tp, p2, colr, n, w, a=200):
    """Tabby rings across a thin limb (2D: short strokes across the tube)."""
    with c.clip(tp):
        L = len(p2)
        for k in range(n):
            u = (k + 0.5) / n * (L - 1)
            i = min(int(u), L - 2); fr = u - i
            x = p2[i][0] + (p2[i + 1][0] - p2[i][0]) * fr; y = p2[i][1] + (p2[i + 1][1] - p2[i][1]) * fr
            dx, dy = p2[i + 1][0] - p2[i][0], p2[i + 1][1] - p2[i][1]; d = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / d * 8, dx / d * 8
            c.line(poly([(x - nx + dx / d * 0.6, y - ny + dy / d * 0.6), (x + nx - dx / d * 0.6, y + ny - dy / d * 0.6)], False), w, colr, a)


def _ws_leg(c, view, R, s, pal, det, light):
    Hp, K, A, fd = R['legs'][s]
    lw = c.lw
    hem = K + (A - K) * 0.80
    _ws_tube3(c, view, [Hp, (Hp + K) / 2, K], [10.0, 8.6, 7.6], pal['trousers'], pal['trousers_sh'], lw, light)
    _ws_tube3(c, view, [K, (K + hem) / 2, hem], [7.6, 7.0, 6.8], pal['trousers'], pal['trousers_sh'], lw, light)
    tp, p2 = _ws_tube3(c, view, [hem - (hem - K) * 0.04, (hem + A) / 2, A], [4.6, 4.2, 4.0], pal['fur'], pal['fur_dk'], lw, light)
    if det >= 1: _ws_stripes(c, tp, p2, pal['fur_dk'], 2, lw * 1.2)
    # the shoe: long, narrow, worn to a point
    heel = np.array([A[0], -3.0, A[2]]) - fd * 6.0
    ball = np.array([A[0], -3.6, A[2]]) + fd * 15.0
    toe = np.array([A[0], -2.0, A[2]]) + fd * 30.0
    sole = [np.array([q[0], -0.5, q[2]]) for q in (heel, ball, toe)]
    X, Y, zd, f = view.pa(np.array([heel, A + np.array([0.0, 2.0, 0.0]), ball, toe]))
    Xs, Ys, _, fs = view.pa(np.array(sole))
    top = list(zip(X.tolist(), Y.tolist()))
    bot = list(zip(Xs.tolist(), Ys.tolist()))
    sh = smooth([top[0], top[1], top[2], top[3], bot[2], bot[1], bot[0]], True, 0.6)
    try:
        hull = poly(_hull(top + bot), True)
        sh = union(sh, hull)
    except Exception:
        pass
    c.fill(sh, pal['shoe']); c.fill(_crescent(sh, 0, -1.2), '#5a4e44', 120); c.line(sh, lw, pal['line'])
    c.line(poly(bot, False), lw * 0.7, '#4a4038', 200)


def _ws_tail(c, view, R, pal, det, light):
    """A thick matted tabby tail hanging behind and off-centre from the legs (rigid: it never moves), an S-curl at the
    tip, ragged tufts along both edges, dark rings, a lighter edge on the lit side."""
    T = np.asarray(R['tail'], float)
    X, Y, _, f = view.pa(T)
    m = len(X) - 1
    bases, dirs, lens = [], [], []
    n = 40
    for i in range(n):
        u = (i + 0.5) / n
        k = min(int(u * m), m - 1); fr = u * m - k
        x = X[k] + (X[k + 1] - X[k]) * fr; y = Y[k] + (Y[k + 1] - Y[k]) * fr
        dx, dy = X[k + 1] - X[k], Y[k + 1] - Y[k]; d = math.hypot(dx, dy) or 1.0
        s_ = 1 if i % 2 else -1
        wv = 0.5 * (7.5 - 2.5 * u) * f[k]
        bases.append((x - dy / d * s_ * wv * 0.75, y + dx / d * s_ * wv * 0.75))
        dirs.append((-dy / d * s_ * 0.55 + dx / d * 1.0, dx / d * s_ * 0.55 + dy / d * 1.0))      # swept down along the tail
        lens.append((5.0 + 3.0 * hash01(i, 1351)) * f[k] * (0.6 + 0.4 * u))
    for j in range(3):          # a ragged brush at the tip
        bases.append((X[-1], Y[-1])); a_ = (j - 1) * 0.45
        dx, dy = X[-1] - X[-2], Y[-1] - Y[-2]
        dirs.append((dx * math.cos(a_) - dy * math.sin(a_), dx * math.sin(a_) + dy * math.cos(a_))); lens.append((6.0 + j) * f[-1])
    _ws_tufts2d(c, bases, dirs, lens, 1.6 * f[0], pal['fur'], pal, c.lw, det)
    ws_ = [7.5, 6.5, 5.6, 5.0][:len(T)]
    tp, p2 = _ws_tube3(c, view, T, ws_, pal['fur'], pal['fur_dk'], c.lw, light)
    if det >= 1:
        _ws_stripes(c, tp, p2, pal['fur_dk'], 6, c.lw * 2.6, 230)
        with c.clip(tp):
            c.fill(_crescent(tp, -1.1, -0.2), pal['fur_hi'], 150)


_WS_ROWS = ((-12.0, 15.5, 11.5), (0.0, 14.0, 10.0), (16.0, 12.0, 9.0), (46.0, 15.5, 10.5), (60.0, 18.5, 9.2), (68.0, 13.0, 8.0), (73.5, 7.5, 6.5))      # sloped, dropped shoulders


def _ws_spine_pt(R, h):
    """Point on the spine h cm above the hip centre (negative: below), with the local pitch."""
    Hc, Wst, Ch, Sc, Nb = R['Hc'], R['Wst'], R['Ch'], R['Sc'], R['Nb']
    a1, a = R['a1'], R['a']
    if h <= 16.0:
        return Hc + _rx(np.array([0.0, -h, 0.0]), a1), a1
    if h <= 46.0:
        k = (h - 16.0) / 30.0; return Wst + (Ch - Wst) * k, a1 + R['a2'] * k
    hn = R.get('hunch', 0.0)
    if h <= 70.0:
        k = (h - 46.0) / 24.0; return Ch + (Sc - Ch) * k, a + hn * k
    return Sc + _rx(np.array([0.0, -(h - 70.0), 0.0]), a + hn), a + hn


def _ws_surf(R, h, xr, out=1.0, front=True):
    """Point on the jacket's surface at height h, across fraction xr (-1 his right .. 1 his left), front or back."""
    rows = _WS_ROWS
    hs = [r[0] for r in rows]
    w = float(np.interp(h, hs, [r[1] for r in rows])); d = float(np.interp(h, hs, [r[2] for r in rows]))
    p, a = _ws_spine_pt(R, h)
    xr = clamp(xr, -1, 1)
    z = d * math.sqrt(max(0.0, 1 - xr * xr)) * (1 if front else -1)
    loc = np.array([xr * w, 0.0, z + (out if front else -out)])
    n = _u3(np.array([xr / max(w, 1), 0.0, (z / max(d * d, 1))]))
    return p + _rx(loc, a), _rx(n, a)


def _ws_torso(c, view, R, P, pal, det, t, light, tv=False):
    """The mustard driver jacket: narrow torso, hem over the hips, buttons, collar, the oval WHISTLESTOP patch, pockets;
    the black bow tie with the red STOP pin; the orange lanyard and silver whistle."""
    lw = c.lw
    rings = []
    for hrow, w, d in _WS_ROWS:
        p, a = _ws_spine_pt(R, hrow)
        ph = np.linspace(0, 2 * PI, 20, endpoint=False)
        loc = np.stack([w * np.cos(ph), np.zeros_like(ph), d * np.sin(ph)], -1)
        Q = p + _rx(loc, a)
        X, Y, _, _ = view.pa(Q)
        rings.append(np.stack([X, Y], -1))
    body = None
    for i in range(len(rings) - 1):
        h = poly(_hull(np.vstack([rings[i], rings[i + 1]])), True)
        body = h if body is None else union(body, h)
    c.fill(body, pal['jacket'])
    front_n = _rx(np.array([0.0, 0.0, 1.0]), R['a2'] + R['a1'])
    fz = float(view.face(front_n)[0])
    with c.clip(body):
        xs = np.concatenate([r[:, 0] for r in rings])
        c.grad(body, xs.min(), 0, xs.max(), 0, [(0, pal['jacket_hi'], 100), (0.4, pal['jacket'], 0), (1, pal['jacket_sh'], 210)])
        if det >= 1:
            c.texture(body, 'fabric', 0.10 + 0.08 * pal['grime'], 0.6)
            hem = [view.p2(_ws_surf(R, -8.0, x_)[0]) for x_ in np.linspace(-1, 1, 9)]
            c.line(smooth(hem, False), lw * 3.0, pal['jacket_sh'], 90)
        if light and light.get('rim'):
            c.fill(_crescent(body, -light.get('side', 1) * 1.5, 0), light['rim'], light.get('rim_a', 60))
        if fz > 0.05:
            # centre front, buttons, pockets, collar
            cf = [view.p2(_ws_surf(R, h_, 0.0)[0]) for h_ in (-12.0, 10.0, 30.0, 50.0, 62.0)]
            c.line(smooth(cf, False), lw * 0.8, pal['line'], 220)
            for h_ in (12.0, 30.0, 47.0):
                q, n = _ws_surf(R, h_, 0.05, 1.2)
                X, Y = view.p2(q); _, _, _, f = view.p(q)
                bt = oval(X, Y, 1.25 * f, 1.25 * f)
                c.fill(bt, pal['button']); c.line(bt, lw * 0.5, pal['line'])
            for s in (-1, 1):
                pk = [view.p2(_ws_surf(R, 4.0, s * x_)[0]) for x_ in (0.35, 0.82)]
                c.line(poly(pk, False), lw * 0.8, pal['line'], 200)
                lap = [view.p2(_ws_surf(R, h_, s * x_, 1.5)[0]) for h_, x_ in ((71.0, 0.55), (60.0, 0.42), (52.0, 0.06))]
                c.line(smooth(lap, False), lw * 0.9, pal['line'])
            # the oval patch on his left chest: WHISTLESTOP
            q, n = _ws_surf(R, 49.0, 0.60, 1.0)
            if view.face(n)[0] > 0.1:
                tx = _u3(_ws_surf(R, 49.0, 0.72, 1.0)[0] - _ws_surf(R, 49.0, 0.48, 1.0)[0])
                ty = _u3(_ws_surf(R, 46.0, 0.60, 1.0)[0] - _ws_surf(R, 52.0, 0.60, 1.0)[0])
                ang = np.linspace(0, 2 * PI, 18, endpoint=False)
                pts = [view.p2(q + tx * 6.0 * math.cos(a_) + ty * 2.6 * math.sin(a_)) for a_ in ang]
                pa = smooth(pts, True, 0.9)
                c.fill(pa, pal['patch']); c.line(pa, lw * 1.0, pal['patch_rim'])
                if det >= 2:
                    X0, Y0 = view.p2(q); X1, Y1 = view.p2(q + tx); X2, Y2 = view.p2(q + ty)
                    sx = math.hypot(X1 - X0, Y1 - Y0); sy = math.hypot(X2 - X0, Y2 - Y0)
                    rot = math.degrees(math.atan2(Y1 - Y0, X1 - X0))
                    pc = c.sub(X0, Y0, rot, sx, sy)
                    _block_text(pc, 'WHISTLESTOP', 0.0, 0.0, 0.95, pal['patch_rim'], 255, w=0.28)
    c.line(body, lw, pal['line'])
    return body, fz


def _ws_tufts2d(c, bases, dirs, lens, w, colr, pal, lw, det, a=255):
    """Jagged fur tufts (2D): from base points along directions; one path, a dark rim, a shade."""
    p = skia.Path()
    for (x, y), (dx, dy), L in zip(bases, dirs, lens):
        d = math.hypot(dx, dy) or 1.0; ux, uy = dx / d, dy / d
        nx, ny = -uy * w, ux * w
        p.addPoly([skia.Point(x - nx, y - ny), skia.Point(x + ux * L * 0.55 - nx * 0.35, y + uy * L * 0.55 - ny * 0.35),
                   skia.Point(x + ux * L, y + uy * L), skia.Point(x + ux * L * 0.5 + nx * 0.45, y + uy * L * 0.5 + ny * 0.45),
                   skia.Point(x + nx, y + ny)], True)
    if p.countPoints() == 0: return
    c.line(p, lw * 1.2, pal['line'], int(220 * a / 255))
    if det >= 1:
        c.fill(p, pal['fur_dk'] if colr == pal['fur'] else pal['mask_sh'], a)
        q = skia.Path(p); q.offset(-0.3, -0.45); c.fill(q, colr, a)
    else:
        c.fill(p, colr, a)


def _ws_chest_ruff(c, view, R, P, pal, det):
    """The off-white chest ruff spilling out of the jacket's neck under the bow tie: matted, jagged, a little dirty."""
    lw = c.lw
    side = []
    for s in (-1, 1):
        pts = []
        for i in range(15):
            u = i / 14.0
            h = 74.0 - 30.0 * u
            xb = 0.92 * (1.0 - u) ** 0.75
            if i % 2:   # a tuft tip hanging down and out
                xr, h = xb + 0.05, h - (3.0 + 2.5 * hash01(i + 20 * (s + 1), 1336))
            else:       # the valley between two tufts
                xr, h = xb - 0.10 * (1.0 - u) - 0.02, h + 1.5
            pts.append(view.p2(_ws_surf(R, h, clamp(s * xr, -0.99, 0.99), 1.4)[0]))
        side.append(pts)
    out = side[0] + side[1][::-1]
    rf = poly(out, True)
    c.line(rf, lw * 2.0, pal['line'])
    c.fill(rf, pal['mask_edge'])
    inner = poly([view.p2(_ws_surf(R, 74.0 - 25.0 * (i / 8.0), s * 0.62 * (1 - i / 8.0) ** 0.8 + (0.06 * s if i % 2 else 0.0), 1.6)[0])
                  for s, rng in ((-1, range(9)), (1, range(8, -1, -1))) for i in rng], True)
    c.fill(inner, pal['mask'])
    if det >= 1:
        for k in range(22):
            u = hash01(k, 1331); xr = (hash01(k, 1332) - 0.5) * 1.4 * (1 - u)
            a_ = view.p2(_ws_surf(R, 73.0 - 24.0 * u, xr, 1.7)[0]); b_ = view.p2(_ws_surf(R, 73.0 - 24.0 * u - 4.0, xr * 1.12, 1.7)[0])
            c.line(poly([a_, b_], False), lw * 0.55, pal['mask_sh'] if k % 3 else '#fffbf0', 200)
        c.fill(_crescent(rf, 0, -1.5), pal['mask_sh'], 150)
        if pal['grime'] > 0:
            c.texture(rf, 'fabric', 0.14, 0.45)
            d_ = view.p2(_ws_surf(R, 56.0, 0.25, 1.7)[0]); c.fill(oval(d_[0], d_[1], 2.6, 1.6), '#8a7650', 70)


def _ws_collar(c, view, R, P, pal, det, fz):
    """Bow tie (black, the red STOP-sign pin) and the lanyard with the whistle (drawn after the head is not needed: the
    tie sits under the chin)."""
    if fz < -0.05: return None
    lw = c.lw
    _ws_chest_ruff(c, view, R, P, pal, det)
    a = R['a'] + R.get('hunch', 0.0)
    B = R['Sc'] + _rx(np.array([0.0, 5.0, 10.5]), a)
    tx = _rx(np.array([1.0, 0.0, 0.0]), a); ty = _rx(np.array([0.0, 1.0, 0.0]), a)
    pr = lambda q: view.p2(q)                                          # noqa: E731
    for s in (-1, 1):
        wing = smooth([pr(B + tx * s * 1.2), pr(B + tx * s * 9.6 - ty * 4.6), pr(B + tx * s * 10.4 + ty * 0.2), pr(B + tx * s * 9.4 + ty * 4.8)], True, 0.25)
        c.fill(wing, pal['bow']); c.line(wing, lw * 0.7, '#000000')
        if det >= 1: c.line(poly([pr(B + tx * s * 2.0), pr(B + tx * s * 6.4 - ty * 1.0)], False), lw * 0.5, '#3a3634', 200)
    X, Y, _, f = view.p(B + _rx(np.array([0.0, 0.0, 0.6]), a))
    knot = oval(X, Y, 2.6 * f, 2.8 * f)
    c.fill(knot, pal['bow'])
    oc = [(X + 2.05 * f * math.cos(PI / 8 + k * PI / 4), Y + 2.05 * f * math.sin(PI / 8 + k * PI / 4)) for k in range(8)]
    c.fill(poly(oc, True), '#f2ede4')
    oc2 = [(X + 1.72 * f * math.cos(PI / 8 + k * PI / 4), Y + 1.72 * f * math.sin(PI / 8 + k * PI / 4)) for k in range(8)]
    c.fill(poly(oc2, True), pal['pin'])
    if det >= 2 and f * c.s > 6: _block_text(c, 'STOP', X, Y, 0.7 * f, '#ffffff', 255, w=0.14 * f)
    return B


def _ws_lanyard(c, view, R, P, pal, det):
    a = R['a']
    rest = R['Ch'] + _rx(np.array([1.0, -6.0, 13.5]), a)
    wh = rest
    side = getattr(P, '_ws_wside', -1)
    if P.ws_whistle > 0.01:
        target = R['mouth'] + np.array([side * 1.5, 1.5, 3.0])
        wh = rest + (target - rest) * ease_in_out(clamp(P.ws_whistle))
    pr = view.p2
    l1 = [pr(R['Nb'] + _rx(np.array([-6.0, 1.0, 5.0]), a)), pr((R['Nb'] + wh) / 2 + np.array([-3.0, 4.0, 3.0])), pr(wh)]
    l2 = [pr(R['Nb'] + _rx(np.array([6.0, 1.0, 5.0]), a)), pr((R['Nb'] + wh) / 2 + np.array([3.0, 4.0, 3.0])), pr(wh)]
    for l_ in (l1, l2):
        c.line(smooth(l_, False), c.lw * 2.3, pal['line']); c.line(smooth(l_, False), c.lw * 1.3, pal['lanyard'])
    X, Y, _, f = view.p(wh)
    ang = -25.0 if P.ws_whistle < 0.5 else -80.0 * side
    wc = c.sub(X, Y, ang, f)
    body = smooth([(-1.2, 0.0), (1.8, -0.2), (2.2, 1.4), (1.2, 2.6), (-1.2, 2.4), (-2.1, 1.2)], True, 0.8)
    wc.fill(rrect(-1.0, -2.6, 2.0, 2.8, 0.4), pal['whistle']); wc.line(rrect(-1.0, -2.6, 2.0, 2.8, 0.4), c.lw / f * 0.7, pal['line'])
    wc.fill(body, pal['whistle']); wc.fill(_crescent(body, 0.4, 0.5), '#7a8088', 200)
    wc.fill(oval(-0.4, 0.6, 0.6, 0.5), '#ffffff', 200)
    wc.line(body, c.lw / f * 0.8, pal['line'])
    return wh


def _ws_arm(c, view, R, P, s, pal, det, t, light, hands=True, arm_only=False):
    arm = R['arms'][s]
    lw = c.lw
    S, E, W = arm['S'], arm['J'][0], arm['W']
    cuff = E + (W - E) * 0.42
    if not arm_only or True:
        _ws_tube3(c, view, [S, (S + E) / 2, E], [10.0, 8.6, 8.0], pal['jacket'], pal['jacket_sh'], lw, light)
        tp, _ = _ws_tube3(c, view, [E, cuff], [8.0, 7.6], pal['jacket'], pal['jacket_sh'], lw, light)
        X, Y, _, f = view.p(cuff)
        Xe, Ye, _, _ = view.p(E)
        d = math.hypot(X - Xe, Y - Ye) or 1.0
        nx, ny = -(Y - Ye) / d * 4.0 * f, (X - Xe) / d * 4.0 * f
        c.line(poly([(X - nx, Y - ny), (X + nx, Y + ny)], False), lw * 2.2, pal['trim'])
        tw, p2 = _ws_tube3(c, view, [cuff, (cuff + W) / 2, W], [4.6, 4.0, 4.0], pal['fur'], pal['fur_dk'], lw, light)
        if det >= 1: _ws_stripes(c, tw, p2, pal['fur_dk'], max(2, int(3 * arm['k'])), lw * 1.3)
        Xw, Yw, _, fw = view.p(cuff + (W - cuff) * 0.08)
        Xk, Yk = view.p2(W)
        dx, dy = Xk - Xw, Yk - Yw; dd = math.hypot(dx, dy) or 1.0
        px, py = -dy / dd, dx / dd
        bases = [(Xw + px * k * 1.5 * fw, Yw + py * k * 1.5 * fw) for k in (-2, -1, 0, 1, 2)]
        dirs = [(dx / dd + px * k * 0.35, dy / dd + py * k * 0.35) for k in (-2, -1, 0, 1, 2)]
        lens = [(3.2 + 2.0 * hash01(k + 3 * (s + 1), 1341)) * fw for k in range(5)]
        _ws_tufts2d(c, bases, dirs, lens, 1.1 * fw, pal['fur'], pal, lw, det)
    if hands: _ws_glove(c, view, R, P, s, pal, det, t, light)


def _ws_glove(c, view, R, P, s, pal, det, t, light):
    h = _ws_hand3(R, s, P)
    lw = c.lw
    W, f_, nb = h['W'], h['f'], h['nb']
    pieces = []
    # glove cuff: a short flared tube
    cuff = [W - f_ * 4.0, W - f_ * 0.5]
    pieces.append((view.depth(W - f_ * 2.0) - 0.5, 'cuff', cuff))
    Xp, Yp, zp, fp = view.pa(np.array(h['palm']))
    pz = float(np.mean(zp))
    pieces.append((pz, 'palm', list(zip(Xp.tolist(), Yp.tolist()))))
    for j, fing in enumerate(h['fingers']):
        pieces.append((view.depth(np.mean(fing, 0)) + (0.3 if j == 1 else 0.0), 'finger', fing))
    pieces.append((view.depth(np.mean(h['thumb'], 0)), 'finger', h['thumb']))
    back = view.face(nb)[0] > 0
    pieces.sort(key=lambda q: q[0])
    prop = getattr(P, 'hl_prop' if s > 0 else 'hr_prop')
    drew_prop = False
    for z_, kind, g in pieces:
        if prop and not drew_prop and kind != 'cuff' and z_ >= pz - 0.5 and not back:
            _ws_held(c, view, h, P, s, prop, pal, det, t); drew_prop = True
        if kind == 'cuff':
            _ws_tube3(c, view, g, [9.6, 8.2], pal['glove'], pal['glove_sh'], lw, light)
        elif kind == 'palm':
            gc = np.mean(np.array(g), 0)
            hp = poly(_hull([tuple(gc + (np.array(q) - gc) * 1.25) for q in g]), True)     # a fat mascot palm
            c.fill(hp, pal['glove']); c.fill(_crescent(hp, 1.0, 1.0), pal['glove_sh'], 170)
            if back and det >= 1:                 # the three stitch lines on the back of the glove
                for k in (-1, 0, 1):
                    a_ = h['W'] + f_ * 3.0 + h['th'] * k * 2.4 + nb * 1.7
                    b_ = h['W'] + f_ * 9.0 + h['th'] * k * 2.8 + nb * 1.6
                    c.line(poly([view.p2(a_), view.p2(b_)], False), lw * 0.7, pal['glove_sh'])
            if back and det >= 1:                 # fuzz on the back of the old glove
                for k in range(3):
                    a_ = h['W'] + f_ * (5.0 + 2.2 * k) + h['th'] * (k - 1) * 2.0 + nb * 2.0
                    x_, y_ = view.p2(a_); _, _, _, ff = view.p(a_)
                    c.line(poly([(x_ - 0.8 * ff, y_ + 0.5 * ff), (x_ + 0.9 * ff, y_ - 0.6 * ff)], False), lw * 0.6, pal['glove_sh'], 170)
            c.line(hp, lw * 1.1, pal['line'])
        else:
            X, Y, zd, f = view.pa(np.array(g))
            p2 = list(zip(X.tolist(), Y.tolist()))
            n = len(p2)
            ws = [(4.4 - 0.6 * k / (n - 1)) * f[k] for k in range(n)]
            tp = _tube(p2, ws, 0.75)
            # round, padded fingertip: a disc over the last point
            tip = oval(p2[-1][0], p2[-1][1], ws[-1] * 0.52, ws[-1] * 0.52)
            try: tp = union(tp, tip)
            except Exception: pass
            c.fill(tp, pal['glove']); c.fill(_crescent(tp, 0.8, 0.8), pal['glove_sh'], 140)
            if det >= 1 and pal['grime'] > 0:           # grey grime gathering toward the fingertips
                c.grad(tp, p2[1][0], p2[1][1], p2[-1][0], p2[-1][1], [(0, pal['glove_dirt'], 0), (1, pal['glove_dirt'], 120)])
            c.line(tp, lw * 0.9, pal['line'])
            # every hinge: a soft knuckle bulge and a pale crease (four segments: one knuckle too many, read in the bends)
            for k in range(1, n - 1):
                dx, dy = p2[k + 1][0] - p2[k - 1][0], p2[k + 1][1] - p2[k - 1][1]; d = math.hypot(dx, dy) or 1.0
                nx, ny = -dy / d * ws[k] * 0.42, dx / d * ws[k] * 0.42
                c.line(smooth([(p2[k][0] - nx, p2[k][1] - ny), (p2[k][0] + dx / d * ws[k] * 0.18, p2[k][1] + dy / d * ws[k] * 0.18),
                               (p2[k][0] + nx, p2[k][1] + ny)], False), lw * 0.7, pal['glove_sh'], 120)
    if prop and not drew_prop:
        _ws_held(c, view, h, P, s, prop, pal, det, t)
    return h


def _ws_held(c, view, h, P, s, prop, pal, det, t):
    """His props in the glove (cm, drawn in the hand's own frame): the clipboard watchlist, the ticket punch, Mina's
    walkie-talkie, a yellow ticket, a pencil."""
    grip = h['K'] + h['f'] * 1.5 - h['nb'] * 3.0
    X, Y, zd, f = view.p(grip)
    if prop in ('ws_clipboard', 'ws_clipboard_new'):
        q = grip - h['nb'] * 1.0
        X, Y, _, f = view.p(q)
        pc = c.sub(X, Y, 0.0, f)
        pc.lw = c.lw / f
        _ws_clipboard(pc, det, t, P, new=(prop == 'ws_clipboard_new'))
        return
    if prop in PROPS3:
        fx, fy = view.p2(grip + h['f'] * 4.0)
        ang = math.degrees(math.atan2(fy - Y, fx - X)) - 90.0
        fn, how, _ = PROPS3[prop]
        pc = c.sub(X, Y, ang if how == 'grip' else 0.0, f)
        pc.lw = c.lw / f
        fn(pc, det, t, P)


def _ws_clipboard(c, det, t, P, new=False):
    """The roll call: a hardboard clipboard (24 x 32 cm), a chrome clip, a watchlist of names each ending 'Sat alone'
    (most crossed out), held up against his chest; ws_write draws the pencil line through a name."""
    board = rrect(-12.0, -6.0, 24.0, 32.0, 1.5)
    c.fill(board, '#8a6a44'); c.line(board, c.lw * 0.9)
    paper = rect(-10.5, -2.5, 21.0, 27.0)
    c.fill(paper, '#efe9d8' if new else '#ddd3ba'); c.line(paper, c.lw * 0.5, '#6a6050')
    if det >= 1:
        for k in range(8):
            y = 1.5 + k * 2.8
            c.line(poly([(-9.0, y), (2.0 + 2.0 * hash01(k, 671), y)], False), c.lw * 0.55, '#3a3a4a', 210)
            c.line(poly([(4.0, y), (8.6, y)], False), c.lw * 0.45, '#6a5a5a', 190)
            if not new and k < 7:
                c.line(poly([(-9.5, y - 0.2), (3.0, y + 0.2)], False), c.lw * 0.5, '#7a2a2a', 200)
        if new:
            w = clamp(getattr(P, 'ws_write', 0.0)) if P is not None else 0.0
            if w > 0: c.line(poly([(-9.5, 1.3), (-9.5 + 13.0 * w, 1.7)], False), c.lw * 0.6, '#2a2a3a')
    c.fill(rrect(-4.0, -7.0, 8.0, 3.6, 0.8), '#c9ced5'); c.line(rrect(-4.0, -7.0, 8.0, 3.6, 0.8), c.lw * 0.6)


# ---------------------------------------------------------------------------------------------------- the figure
def _ws_body_items(c, view, R, P, pal, det, t, light, upper_only=False, skip_hands=0):
    items = []
    tv = bool(P.__dict__.get('_ws94'))
    zt = view.depth(R['Ch'])
    if not upper_only:
        for s in (-1, 1):
            Hp, K, A, fd = R['legs'][s]
            zl = (view.depth(K) + view.depth(A)) / 2
            if view.depth(K) < zt + 8.0: zl = min(zl, zt - 6.0)
            items.append((zl + 0.01 * s, lambda cc, s=s: _ws_leg(cc, view, R, s, pal, det, light)))
        items.append((view.depth(R['tail'][1]), lambda cc: _ws_tail(cc, view, R, pal, det, light)))
    st = {}

    def torso(cc):
        body, fz = _ws_torso(cc, view, R, P, pal, det, t, light, tv)
        st['fz'] = fz
        if fz > -0.05: _ws_neck(cc, view, R, pal, det, light)
    items.append((zt, torso))
    zh = view.depth(R['head'])

    def head(cc):
        if st.get('fz', 1) <= -0.05: _ws_neck(cc, view, R, pal, det, light)
        _ws_head_draw(cc, R, view, P, det, t, light, pal, tv)
        if st.get('fz', 1) > -0.05:
            _ws_collar(cc, view, R, P, pal, det, st.get('fz', 1))
            _ws_lanyard(cc, view, R, P, pal, det)
        _ws_hat_draw(cc, R, view, P, det, t, light, pal)
        if R.get('_ears_late'): R['_ears_late'](cc)
    items.append((max(zh, zt + 1.0) if view.depth(_rx(np.array([0.0, 0.0, 1.0]), R['a'])) > -0.2 else zh - 2.0, head))
    for s in (-1, 1):
        arm = R['arms'][s]
        za = (view.depth(arm['S']) + view.depth(arm['J'][0]) + 2 * view.depth(arm['W'])) / 4
        hands = not (skip_hands in (2, s))
        items.append((za + 0.02 * s, lambda cc, s=s, hands=hands: _ws_arm(cc, view, R, P, s, pal, det, t, light, hands)))
    items.sort(key=lambda q: q[0])
    return items


def _ws_neck(c, view, R, pal, det, light):
    _ws_tube3(c, view, [R['neck'][0], R['neck'][1] + (R['head'] - R['neck'][1]) * 0.3], [8.0, 7.0], pal['fur'], pal['fur_dk'], c.lw, light)


def ws_tracking(pen_or_c, x0, y0, w, h, amount, t, seed=0, colr='#f4f4ff'):
    """VHS tracking lines: thin bright broken horizontal lines and a dark tear band (design px box)."""
    c = pen_or_c
    if amount <= 0.01: return
    k = int(t * 30.0)
    for i in range(int(3 + 6 * amount)):
        y = y0 + h * hash01(k * 7 + i, 900 + seed)
        xs = x0 + w * 0.3 * hash01(k * 5 + i, 901 + seed)
        ww = w * (0.3 + 0.7 * hash01(k * 3 + i, 902 + seed))
        a = int(90 + 140 * amount * hash01(i + k, 903))
        c.fill(rect(xs, y, ww, 1.2 + 2.5 * hash01(i, 904 + k)), colr, a)
    yb = y0 + h * hash01(k, 905 + seed)
    c.fill(rect(x0, yb, w, h * 0.04 * amount), '#000000', int(90 * amount))


def _whistle_figure(c, who, P, det, t, light=None, upper_only=False):
    """Mister Whistlestop in body units on Ctx c (feet at (0, 0)). Tape effects (ws_glitch / ws_rewind) draw him in
    torn, offset horizontal slices with chroma ghosts and tracking lines."""
    sp = CAST[who]
    pal = _WS_PAL94 if sp.get('tv') else _WS_PAL
    if sp.get('tv'): P.__dict__['_ws94'] = True
    sc = max(P.ws_scale, 1e-3)
    cc = c.sub(0.0, 0.0, 0.0, _WSU * sc)
    view = _WSView(P)
    R = _ws_rig(P)
    skip = int(getattr(P, 'ws_hands_front', 0) or 0)
    if skip == 3:                    # auto: leave out (for draw_whistle_hands) only the hands that have reached their target
        l_, r_ = P.ws_lw > 0.6, P.ws_rw > 0.6
        skip = 2 if (l_ and r_) else (1 if l_ else (-1 if r_ else 0))
    items = _ws_body_items(cc, view, R, P, pal, det, t, light, upper_only, skip)

    def draw_all(cx_):
        for z, fn in items: fn(cx_)
    g = clamp(P.ws_glitch); rw = clamp(P.ws_rewind)
    amt = max(g, rw)
    dark = clamp((light or {}).get('dark', 0.0))
    if amt < 0.01 and dark > 0.01:      # near darkness: the figure sinks into the dark; only his eyes and teeth catch light
        cv = cc.cv
        cv.saveLayer(None, None)
        draw_all(cc)
        if (light or {}).get('under'):  # lit from below in the dark: black above the chin, the light pooling under the grin
            M_ = R['hrot']
            ys = [cc.pt(*view.p2(q)) for q in (R['hat']['base'] + R['hat']['ax'] * R['hat']['H'] * 0.3, R['head'] + M_ @ _ws_head_local(0.0, 0.15),
                                                R['mouth'], R['head'] + M_ @ _ws_head_local(0.0, -1.3), R['Ch'])]
            pos = [p_[1] for p_ in ys]
            if pos[-1] > pos[0] + 1:
                al = [0.97, 0.93, 0.42, 0.40, dark]
                srt = sorted(zip(pos, al))
                p0_, p1_ = srt[0][0], srt[-1][0]
                cols = [skia.Color4f(0.02, 0.018, 0.03, float(a_)) for _, a_ in srt]
                offs = [float((p_ - p0_) / (p1_ - p0_)) for p_, _ in srt]
                sh_ = skia.GradientShader.MakeLinear([skia.Point(0, p0_), skia.Point(0, p1_)], [c_.toColor() for c_ in cols], offs)
                cv.drawPaint(skia.Paint(Shader=sh_, BlendMode=skia.BlendMode.kSrcATop))
            else:
                cv.drawPaint(skia.Paint(Color=skia.Color4f(0.02, 0.018, 0.03, float(dark)), BlendMode=skia.BlendMode.kSrcATop))
        else:
            cv.drawPaint(skia.Paint(Color=skia.Color4f(0.02, 0.018, 0.03, float(dark)), BlendMode=skia.BlendMode.kSrcATop))
        cv.restore()
        if not upper_only or True:
            _ws_glow_feats(cc, R, view, P, det, t, pal, 0.35 + 0.65 * dark)
        return R
    if amt < 0.01:
        draw_all(cc)
        return R
    # tape effects
    Xs, Ys = [], []
    for q in (R['head'], R['hat']['base'] + R['hat']['ax'] * R['hat']['H'], R['legs'][1][2], R['legs'][-1][2], R['arms'][1]['W'], R['arms'][-1]['W']):
        x_, y_ = view.p2(q); Xs.append(x_); Ys.append(y_)
    x0, x1 = min(Xs) - 40, max(Xs) + 40; y0, y1 = min(Ys) - 20, max(Ys) + 10
    k = int(t * 30.0)
    fade = 1.0 - 0.85 * ease_in_out(prog(rw, 0.55, 1.0))
    cv = cc.cv
    for ghost, gcol, dxg in (('r', (255, 40, 60), 3.5), ('c', (40, 220, 255), -3.5)):
        pnt = skia.Paint(Alphaf=float(0.45 * amt * fade),
                         ColorFilter=skia.ColorFilters.Blend(skia.Color(*gcol), skia.BlendMode.kModulate))
        cv.saveLayer(None, pnt)
        draw_all(cc.sub(dxg * (1 + 2 * amt), 0.0))
        cv.restore()
    nb = 7
    cv.saveLayer(None, skia.Paint(Alphaf=float(fade)))
    for i in range(nb):
        ya, yb = y0 + (y1 - y0) * i / nb, y0 + (y1 - y0) * (i + 1) / nb
        tear = (hash01(k * 11 + i, 911) - 0.5) * 2.0 * 26.0 * amt * (1.0 if hash01(k + i, 912) > 0.35 else 0.15)
        with cc.clip(rect(x0 - 400, ya, (x1 - x0) + 800, yb - ya + 0.5)):
            draw_all(cc.sub(tear, 0.0))
    cv.restore()
    ws_tracking(cc, x0 - 30, y0, (x1 - x0) + 60, (y1 - y0), amt, t, 3)
    return R


_figure_bus_prev = _figure


def _figure(c, who, P, det, t, light=None, upper_only=False):
    """Whole character in body units on Ctx c: Mister Whistlestop dispatches here; everyone else as before."""
    if CAST[who].get('whistle'): return _whistle_figure(c, who, P, det, t, light, upper_only)
    return _figure_bus_prev(c, who, P, det, t, light, upper_only)


CAST['whistle'] = dict(whistle=True, m=_WS_M, hh=200.0, blink_rate=0.0, lock=0.0, micro=0.12, talk=0.0,
                       breath=0.15, body=dict(sh=40, ch=40, wa=30, hip=30, arm=(20, 18), leg=(25, 20), neck=20, hand=1.0),
                       outfit='whistle', sex='m', ring=0, skin='#ebe4d0', skin_sh='#b9ae93', cloth={}, eye_y=0, mouth_y=60,
                       eye_dx=40)
CAST['whistle94'] = dict(CAST['whistle'], tv=True)


# ====================================================================================================== ACTING: WHISTLESTOP
# a = CH.Acting('whistle', seed, height=CH.height_px('whistle', ppm)).place(x, floor_y). World targets (reach, look) are
# design points, callables, (actor, part) or PropTracks, as for everyone. He never walks: tape_skip moves him.
_acting_place_prev_bus = Acting.place


def _acting_place_bus(self, x, y_feet, height=None):
    r = _acting_place_prev_bus(self, x, y_feet, height)
    if self.sp.get('whistle'):
        self.base.update(ws_px0=float(self.x0), ws_py0=float(self.y0), ws_ph=float(self.height))
        if not getattr(self, '_ws_init', False):
            self._ws_init = True
            self.life_k = 0.0                       # no idle fidgets: he is still unless he acts
            self.micro = 0.08
    return r


Acting.place = _acting_place_bus


def _ws_pts(P):
    """Named points of Mister Whistlestop in body units (as _body_point returns) for pose P."""
    view = _WSView(P); R = _ws_rig(P)
    k = _WSU * max(P.ws_scale, 1e-3)
    pr = lambda q: tuple(v * k for v in view.p2(q))            # noqa: E731
    M = R['hrot']
    out = {'head': pr(R['head']), 'eyes': pr(R['head'] + M @ _ws_head_local(0.0, 0.15)), 'mouth': pr(R['mouth']),
           'grin': pr(R['mouth']), 'chin': pr(R['head'] + M @ _ws_head_local(0.0, -1.2)),
           'crown': pr(R['head'] + M @ np.array([0.0, -_WS_CROWN, 0.0])),
           'hat_top': pr(_ws_hat_ring(R['hat'], 1.0, np.array([0.0]))[0]),
           'chest': pr(R['Ch'] + _rx(np.array([0.0, 0.0, 11.0]), R['a'])), 'neck': pr(R['Nb']), 'hip': pr(R['Hc']),
           'belly': pr(R['Wst'] + _rx(np.array([0.0, 0.0, 10.0]), R['a1']))}
    for s, nm in ((1, 'l'), (-1, 'r')):
        arm = R['arms'][s]
        h3 = _ws_hand3(R, s, P)
        out['wrist_' + nm] = pr(arm['W'])
        out['hand_' + nm] = pr(h3['K'] - h3['nb'] * 2.0)
        out['tips_' + nm] = pr((h3['fingers'][0][-1] + h3['fingers'][1][-1]) / 2)
        out['shoulder_' + nm] = pr(arm['S']); out['elbow_' + nm] = pr(arm['J'][0])
        Hp, K, A, fd = R['legs'][s]
        out['knee_' + nm] = pr(K); out['foot_' + nm] = pr(A + fd * 12.0 + np.array([0.0, 8.0, 0.0]))
    return out


_body_point_prev_bus = _body_point


def _body_point(self, P, part):
    if self.sp.get('whistle'):
        pts = _ws_pts(P)
        return pts.get(part, pts['head'])
    return _body_point_prev_bus(self, P, part)


_acting_look_at_prev_bus = Acting.look_at


def _acting_look_at_bus(self, t0, target, t1=None, dur=0.4, z=None, body=0.0, head=1.0, fade=0.35, eyes_lead=0.07, max_head=0.85,
                        snap=False):
    """Whistlestop: painted eyes never move, so the whole head turns to the target: slowly (>= 0.6 s), or with snap=True
    in one hard 2-frame tick (a tape skip of the head)."""
    if not self.sp.get('whistle'):
        return _acting_look_at_prev_bus(self, t0, target, t1, dur, z, body, head, fade, eyes_lead, max_head)
    dur = 0.035 if snap else max(dur, 0.6)

    def fn(P, t):
        w_h = _env(t, t0, t1, dur, fade * (0.3 if snap else 1.6)) * head
        if w_h <= 0.001: return
        tx, ty = _target_xy(target, t)
        ox, oy, s = _origin(self, P)
        hx, hy = _ws_pts(P)['head']
        dx = (tx - (ox + hx * s)) / s; dy = (ty - (oy + hy * s)) / s
        dz = (0.5 * abs(dx) + 120.0) if z is None else float(z)
        yaw = math.atan2(dx, dz) / (PI / 2)
        pitch = math.atan2(dy, math.hypot(dx, max(dz, 1.0)))
        if body > 0: P.turn += (yaw - P.turn) * body * w_h
        P.h_turn += (clamp(yaw - P.turn, -1.2, 1.2) - P.h_turn) * w_h
        P.h_nod += (clamp(pitch / 0.6 * 0.8, -0.7, 0.9) - P.h_nod) * w_h
    return _acting_post(self, t0 - dur, None if t1 is None else t1 + fade * 1.6, fn)


Acting.look_at = _acting_look_at_bus


def _ws_reach(self, t0, side, target, t1=None, dur=0.9, z=0.0, shape='reach', fade=0.7, arc=0.0, ease=None):
    """His glove goes to a world target by t0 + dur and stays until t1, then returns over fade. Past arm's length the arm
    stretches (both bones lengthen, rubbery and thin): down a bus aisle, across a room."""
    pre = 'ws_l' if side > 0 else 'ws_r'
    hp = 'hl_' if side > 0 else 'hr_'
    ef = ease or ease_in_out

    def fn(P, t):
        u = prog(t, t0, t0 + dur)
        if u <= 0: return
        w_out = 1.0 if t1 is None else 1.0 - ease_in_out(prog(t, t1, t1 + fade))
        if w_out <= 0: return
        tx, ty = _target_xy(target, t)
        e = ef(u)
        w = min(1.0, e * 1.0001) * w_out
        lift = arc * math.sin(PI * clamp(u)) * w_out
        setattr(P, pre + 'w', max(getattr(P, pre + 'w'), w))
        setattr(P, pre + 'x', tx); setattr(P, pre + 'y', ty - lift); setattr(P, pre + 'z', z)
        if shape is not None and w > 0.3: setattr(P, hp + 'shape', shape)
    return _acting_post(self, t0, None if t1 is None else t1 + fade, fn)


_acting_reach_to_prev_bus = Acting.reach_to


def _acting_reach_to_bus(self, t0, side, target, t1=None, dur=0.55, z=0.0, contact='palm', shape='grip', fade=0.45, antic_k=0.06,
                         prop=None, lean=True, press=None, rot=None):
    if self.sp.get('whistle'):
        return _ws_reach(self, t0, side, target, t1, max(dur, 0.3), z, shape, max(fade, 0.5))
    return _acting_reach_to_prev_bus(self, t0, side, target, t1, dur, z, contact, shape, fade, antic_k, prop, lean, press, rot)


Acting.reach_to = _acting_reach_to_bus
_acting_reach_far_prev_bus = Acting.reach_far


def _acting_reach_far_bus(self, t0, side, target, t1=None, dur=0.9, z=0.0, shape='reach', fade=0.7, arc=0.0, ease=None):
    if self.sp.get('whistle'): return _ws_reach(self, t0, side, target, t1, dur, z, shape, fade, arc, ease)
    return _acting_reach_far_prev_bus(self, t0, side, target, t1, dur, z, shape, fade, arc)


Acting.reach_far = _acting_reach_far_bus
_acting_foot_gap_prev_bus = Acting.foot_gap


def _acting_foot_gap_bus(self, t):
    if self.sp.get('whistle'):
        P = self.at(t)
        if P.ws_unfold < 0.999 and P.ws_unfold > 0: return 0.0
        R = _ws_rig(P)
        view = _WSView(P)
        low = max(view.p2(np.array([R['legs'][s][2][0], -0.5, R['legs'][s][2][2]]))[1] for s in (-1, 1))
        return max(0.0, -low) * self.height / 1000.0 * _WSU * max(P.ws_scale, 1e-3)
    return _acting_foot_gap_prev_bus(self, t)


Acting.foot_gap = _acting_foot_gap_bus
_grip_point_prev_bus = Acting.grip_point


def _grip_point_bus(self, t, side, prop, post=True):
    if self.sp.get('whistle'):
        P = self.at(t) if post else self._raw(t, False)
        ox, oy, s = _origin(self, P)
        X, Y = _ws_pts(P)['hand_l' if side > 0 else 'hand_r']
        return ox + X * s, oy + Y * s
    return _grip_point_prev_bus(self, t, side, prop, post)


Acting.grip_point = _grip_point_bus


def whistle_point(actor, t, part):
    """Design point of a named part of Mister Whistlestop (see _ws_pts)."""
    return actor.where(t, part)


def _ws_ppc(self):
    return self.height / (_WS_M * 100.0)


def _ws_unfold(self, t0, dur=2.6, t_before=-INF):
    """He unfolds out of the bus door like a ladder, one segment at a time: knees, then the waist, the neck and head, the
    hat telescoping up last. 'ws_unfold_clack' at each segment locking."""
    bounds = (0.0, 0.36, 0.64, 0.84, 1.0)
    step = dur / 4.0
    evs = []

    def fn(P, t):
        if t < t0: P.ws_unfold = 0.0; return
        k = (t - t0) / step
        i = int(k)
        if i >= 4: P.ws_unfold = 1.0; return
        f = ease_in_out(clamp((k - i) / 0.78))
        P.ws_unfold = bounds[i] + (bounds[i + 1] - bounds[i]) * f
    self._add(t_before, None, fn)
    for i in range(4):
        evs.append(self._ev(t0 + step * (i + 0.78), 'ws_unfold_clack', -3.0 + i, step=i))
    return evs


def _ws_tape_skip(self, keys, glitch=0.14):
    """He never walks: every flicker puts him closer. keys = [(t, dict(x=, y=, h=, turn=, pose...)), ...] (x, y = design
    feet point; h = drawn height there; any other entries are pose values held from that key). Each skip: a hard cut of
    position with a 3-frame stutter (new, old, new at 30 fps), a horizontal tracking tear, a 'tape_skip' event."""
    ks = sorted(keys, key=lambda q: q[0])
    ts = [k_[0] for k_ in ks]
    evs = []

    def state(i, P):
        d = ks[i][1]
        if 'x' in d: P.dx = d['x'] - self.x0
        if 'y' in d: P.dy = d['y'] - self.y0
        if 'h' in d: P.ws_scale = d['h'] / self.height
        for kk, vv in d.items():
            if kk in ('x', 'y', 'h'): continue
            if isinstance(vv, (int, float)) and kk in POSE_DEFAULTS: setattr(P, kk, vv)
            elif kk in POSE_DISCRETE: setattr(P, kk, vv)

    def fn(P, t):
        i = _bisect4.bisect_right(ts, t) - 1
        if i < 0: i = 0; state(0, P); return
        tau = t - ts[i]
        j = i
        if i > 0 and 1 / 30.0 <= tau < 2 / 30.0: j = i - 1            # the stutter frame: one tape frame of before
        state(j, P)
        if i > 0 and tau < glitch * 2.0:
            P.ws_glitch = max(P.ws_glitch, (1.0 - tau / (glitch * 2.0)) ** 1.5)
    self._add(-INF, None, fn)
    for i in range(1, len(ks)):
        evs.append(self._ev(ts[i], 'tape_skip', 0.0, step=i))
    return evs


def _ws_curl_door(self, t0, side, edge, t1=None, dur=0.7, z=-6.0):
    """White gloves curl around a doorframe: the fingers wrap the edge (shape 'curl'), one hinge at a time."""
    _ws_reach(self, t0, side, edge, t1, dur, z, 'curl', 0.7)

    def fn(P, t):
        c_ = clamp(prog(t, t0 + dur * 0.6, t0 + dur * 1.5))
        setattr(P, 'ws_lcurl' if side > 0 else 'ws_rcurl', 0.6 * ease_in_out(c_))
    return self._add(t0, t1, fn)


def _ws_walls_flat(self, t0, left_pt, right_pt, t1=None, dur=0.9):
    """Both gloves flat on the hallway's walls."""
    _ws_reach(self, t0, 1, left_pt, t1, dur, 0.0, 'flat', 0.7)
    _ws_reach(self, t0 + 0.12, -1, right_pt, t1, dur, 0.0, 'flat', 0.7)
    return self


def _ws_bend_double(self, t0, ceil_y, t1=None, fade=0.6, crouch=0.3, bend=0.85):
    """Indoors: the hat crushed and folded against the ceiling (design y ceil_y), bent double under it."""
    ppc = _ws_ppc(self)
    cm = max(60.0, (self.y0 - ceil_y) / ppc)

    def fn(P, t):
        w = _env(t, t0, t1, fade, fade)
        if w <= 0: return
        P.ws_ceil = cm if w > 0.5 else 0.0
        P.ws_crouch += crouch * w
        P.ws_bend += bend * w
    return self._add(t0, None if t1 is None else t1 + fade, fn)


def _ws_lean_to(self, t0, target, gap=30.0, dur=2.4, t1=None, beats=2, fade=0.8):
    """He bends down, and down, until the grin is `gap` cm from the target point (a face): a solved waist bend and knee
    crouch, reached in `beats` slow eased stages."""
    P0 = self._raw(t0, False) if hasattr(self, 'post') else self.at(t0)
    tx, ty = _target_xy(target, t0)
    ox, oy, s = _origin(self, P0)
    ppc = _ws_ppc(self) * max(P0.ws_scale, 1e-3)
    best = None
    for b in np.linspace(0.0, 1.9, 39):
        for cr in np.linspace(0.0, 1.0, 11):
            Q = P0.copy(); Q.ws_bend = b; Q.ws_crouch = cr; Q.ws_lw = Q.ws_rw = 0.0
            mx, my = _ws_pts(Q)['mouth']
            X, Y = ox + mx * s, oy + my * s
            side = 1.0 if X < tx else -1.0
            want = (tx - side * gap * ppc, ty)
            err = math.hypot(X - want[0], Y - want[1]) + 8.0 * cr * ppc
            if best is None or err < best[0]: best = (err, b, cr)
    _, b, cr = best

    def fn(P, t):
        u = prog(t, t0, t0 + dur)
        if u <= 0: return
        k = u * beats; i = min(int(k), beats - 1) if u < 1 else beats - 1
        f = (i + ease_in_out(clamp((k - i) / 0.8))) / beats if u < 1 else 1.0
        w = f * (1.0 if t1 is None else 1.0 - ease_in_out(prog(t, t1, t1 + fade)))
        P.ws_bend += (b - P.ws_bend) * w; P.ws_crouch += (cr - P.ws_crouch) * w
    self._add(t0, None if t1 is None else t1 + fade, fn)
    return b, cr


def _ws_hold_child(self, t0, side, child, cside, t1=None, dur=0.8):
    """Like a crossing guard: the child's hand up in his glove (the child reaches up, his glove comes down and closes)."""
    def meet(t):
        b = child.where(t, 'shoulder_l' if cside > 0 else 'shoulder_r', post=False)
        hh = child.height
        return (b[0] + side * 0.0 + (-cside) * 0.0, b[1] - 0.12 * hh)
    child.reach_to(t0, cside, meet, t1=t1, dur=dur, contact='palm', shape='grip', fade=0.5, lean=False)
    _ws_reach(self, t0, side, lambda t: child.where(t, 'hand_l' if cside > 0 else 'hand_r'), t1, dur * 1.1, 6.0, 'grip', 0.6)
    return self


def _ws_grip_small(self, t0, side, other, oside, t1=None, dur=0.5):
    """His glove folded small around someone's fingers, gripping too tight."""
    _ws_reach(self, t0, side, lambda t: other.where(t, 'hand_l' if oside > 0 else 'hand_r'), t1, dur, 4.0, 'grip', 0.4)

    def fn(P, t):
        w = _env(t, t0 + dur, t1, 0.4, 0.2)
        setattr(P, 'ws_lcurl' if side > 0 else 'ws_rcurl', 0.5 * w + 0.1 * w * math.sin(t * 9.0))
    return self._add(t0, t1, fn)


def _ws_hold_prop(self, t0, side, prop, t1=None, shape='hold'):
    def fn(P, t):
        if t < t0 or (t1 is not None and t > t1): return
        setattr(P, 'hl_prop' if side > 0 else 'hr_prop', prop)
        if shape: setattr(P, 'hl_shape' if side > 0 else 'hr_shape', shape)
    return self._add(t0, t1, fn)


def _ws_rest(self, t0, side, rest, t1=None, fade=0.6):
    """Move a hand to a rest ('hang', 'host', 'clip', 'chest', 'mouth', 'hip', 'fold') over fade."""
    key = 'ws_lrest' if side > 0 else 'ws_rrest'

    def fn(P, t):
        w = _env(t, t0, t1, fade, fade)
        if w <= 0: return
        if w >= 0.999:
            setattr(P, key, rest); return
        # blend the wrist from the old rest to the new: draw the rig both ways and mix the target through world coords
        Q = P.copy(); setattr(Q, key, rest)
        R1 = _ws_rig(Q)
        pre = 'ws_l' if side > 0 else 'ws_r'
        if getattr(P, pre + 'w') > 0.5: return
        view = _WSView(Q)
        X, Y, zd, _ = view.p(R1['arms'][side]['W'])
        s_ = P.ws_ph / 1000.0 * _WSU * max(P.ws_scale, 1e-3)
        wx, wy = P.ws_px0 + P.dx + X * s_, P.ws_py0 + P.dy + Y * s_
        setattr(P, pre + 'w', ease_in_out(w)); setattr(P, pre + 'x', wx); setattr(P, pre + 'y', wy); setattr(P, pre + 'z', zd)
    return self._add(t0, None if t1 is None else t1 + fade, fn)


def _ws_walkie(self, t0, side=-1, t1=None, dur=0.6):
    """Mina's walkie-talkie in his glove, pressed to the grin."""
    _ws_hold_prop(self, t0 - 10.0, side, 'walkie', t1, 'hold')
    return _ws_rest(self, t0, side, 'mouth', t1, dur)


def _ws_blow(self, t0, kind='two', side=-1, t1=None):
    """The whistle to the grin: 'two' = fweet-fweet (two short blasts), 'long' = one long blast to drown everyone out.
    The whistle rides up its lanyard in his glove; the body rises a little and the head tips back on each blast."""
    lift = 0.3
    blasts = [(t0 + lift, 0.16), (t0 + lift + 0.28, 0.16)] if kind == 'two' else [(t0 + lift, 1.8)]
    end = blasts[-1][0] + blasts[-1][1] + 0.35 if t1 is None else t1

    def fn(P, t):
        P.__dict__['_ws_wside'] = side
        P.ws_whistle = max(P.ws_whistle, ease_in_out(prog(t, t0, t0 + lift)) * (1.0 - ease_in_out(prog(t, end, end + 0.4))))
        for b0, bd in blasts:
            P.ws_blow = max(P.ws_blow, _env(t, b0, b0 + bd, 0.05, 0.12))
    self._add(t0, end + 0.5, fn)
    evs = [self._ev(blasts[0][0], 'whistle_two' if kind == 'two' else 'whistle_long', 0.0, dur=round(blasts[-1][0] + blasts[-1][1] - blasts[0][0], 3))]
    return evs


def _ws_snap_glove(self, t0, side, target, t1=None, dur=0.16, z=4.0):
    """A glove snaps shut on fabric: a fast reach (anticipation: the fingers open first) and a hard close."""
    _ws_reach(self, t0, side, target, t1, dur, z, 'open', 0.5, ease=ease_out_cubic)

    def fn(P, t):
        if t >= t0 + dur * 0.85: setattr(P, 'hl_shape' if side > 0 else 'hr_shape', 'snap')
    self._add(t0, t1, fn)
    return [self._ev(t0 + dur, 'glove_snap', 0.0)]


def _ws_head_back(self, t0, dur=1.4, to=2.0, ticks=3):
    """His head turns all the way round (180 deg), in a few hard ratchet ticks (a tape catching)."""
    def fn(P, t):
        u = prog(t, t0, t0 + dur)
        if u <= 0: return
        k = u * ticks; i = min(int(k), ticks - 1) if u < 1 else ticks - 1
        f = (i + ease_out_cubic(clamp((k - i) / 0.25))) / ticks if u < 1 else 1.0
        P.h_turn += (to - P.h_turn) * f
    self._add(t0, None, fn)
    return [self._ev(t0 + dur * (i + 0.1) / ticks, 'neck_ratchet', -4.0, step=i) for i in range(ticks)]


def _ws_clipboard_hold(self, t0=-INF, side=1, t1=None, new=False):
    _ws_hold_prop(self, t0, side, 'ws_clipboard_new' if new else 'ws_clipboard', t1, 'clip')
    return _ws_rest(self, t0 if t0 > -INF else -100.0, side, 'clip', t1, 0.01 if t0 == -INF else 0.6)


def _ws_punch(self, t0, side=-1):
    """The chrome ticket punch: click-clack."""
    _ws_hold_prop(self, -INF, side, 'punch', None, 'hold')

    def fn(P, t):
        for tt in (t0, t0 + 0.22):
            setattr(P, 'ws_lcurl' if side > 0 else 'ws_rcurl', max(getattr(P, 'ws_lcurl' if side > 0 else 'ws_rcurl'), _env(t, tt, tt + 0.06, 0.04, 0.08)))
    self._add(t0, t0 + 0.6, fn)
    return [self._ev(t0, 'punch_clack', 0.0)]


def _ws_write_line(self, t0, t1, side=-1, board_side=1):
    """The pencil draws a line through a name on the clipboard (then starts writing the next)."""
    _ws_hold_prop(self, -INF, side, 'pencil', None, 'pen')
    tgt = lambda t: self.where(t, 'hand_l' if board_side > 0 else 'hand_r', post=False)   # noqa: E731
    _ws_reach(self, t0 - 0.6, side, lambda t: (tgt(t)[0] + (-12 + 26 * clamp(prog(t, t0, t1))) * _ws_ppc(self), tgt(t)[1] - 6 * _ws_ppc(self)),
              t1 + 0.4, 0.6, 30.0, 'pen', 0.6)

    def fn(P, t):
        P.ws_write = max(P.ws_write, ease_in_out(prog(t, t0, t1)))
    self._add(t0, None, fn)
    return [self._ev(t0, 'pencil_line', -6.0)]


def _ws_host(self, t0, t1, beats=None):
    """The 1994 TV host: an open-palmed presenting gesture, head bobbing to the jingle; (still the frozen grin)."""
    _ws_rest(self, t0, 1, 'host', t1, 0.5)

    def fn(P, t):
        w = _env(t, t0, t1, 0.4, 0.4)
        P.h_tilt += 7.0 * w * math.sin(2 * PI * (t - t0) / 1.2)
        P.ws_bob += 0.6 * w * max(0.0, math.sin(2 * PI * (t - t0) / 0.6))
    return self._add(t0, t1 + 0.4, fn)


def _ws_say(self, intervals, amount=1.0):
    """His lines: the voice comes from behind the frozen grin (it never moves); only a jaw-free head bob per syllable."""
    for iv in intervals:
        t0, t1 = float(iv[0]), float(iv[1])
        txt = iv[2] if len(iv) > 2 else ''
        n = max(2, len(_re.findall(r'[aeiouy]+', txt.lower())) if txt else int((t1 - t0) * 4))

        def fn(P, t, t0=t0, t1=t1, n=n):
            if t < t0 or t > t1 + 0.3: return
            u = (t - t0) / max(t1 - t0, 0.1)
            P.ws_bob += amount * 0.55 * max(0.0, math.sin(PI * u * n)) * _env(t, t0, t1, 0.1, 0.25)
            P.h_tilt += amount * 3.0 * math.sin(PI * u * n * 0.5) * _env(t, t0, t1, 0.15, 0.3)
        self._add(t0, t1 + 0.3, fn)
    return self


def _ws_defeat(self, t0, slip_dur=1.2, rewind_dur=1.6, back_px=None):
    """Three o'clock: the grin doesn't fit his face; it slips out of register (chroma ghosts), tracking lines tear
    through him, and he rewinds into the dark in reversed jumps, fading."""
    back = (0.0, -0.2 * self.height) if back_px is None else back_px
    t1 = t0 + slip_dur

    def fn(P, t):
        P.ws_slip = max(P.ws_slip, ease_in_out(prog(t, t0, t1)))
        if t0 <= t < t1: P.ws_glitch = max(P.ws_glitch, 0.25 * (1 if int(t * 12) % 3 == 0 else 0))
        r = prog(t, t1, t1 + rewind_dur)
        if r > 0:
            P.ws_rewind = max(P.ws_rewind, r)
            st = math.floor(r * 6) / 6.0                      # reversed jumps backward
            P.dx += back[0] * st; P.dy += back[1] * st * 0.2
            P.ws_scale *= (1.0 - 0.35 * st)
    self._add(t0, None, fn)
    return [self._ev(t0, 'tape_warble', 0.0), self._ev(t1, 'tape_rewind', 0.0, dur=rewind_dur)]


Acting.unfold = _ws_unfold
Acting.tape_skip = _ws_tape_skip
Acting.curl_door = _ws_curl_door
Acting.walls_flat = _ws_walls_flat
Acting.bend_double = _ws_bend_double
Acting.lean_to = _ws_lean_to
Acting.hold_child = _ws_hold_child
Acting.grip_small = _ws_grip_small
Acting.ws_hold = _ws_hold_prop
Acting.ws_rest = _ws_rest
Acting.walkie_to_grin = _ws_walkie
Acting.blow_whistle = _ws_blow
Acting.snap_glove = _ws_snap_glove
Acting.head_backwards = _ws_head_back
Acting.clipboard = _ws_clipboard_hold
Acting.punch = _ws_punch
Acting.write_line = _ws_write_line
Acting.host = _ws_host
Acting.say = _ws_say
Acting.defeat = _ws_defeat
_acting_talk_prev_bus = Acting.talk


def _acting_talk_bus(self, intervals, text=None, intensity=1.0, env='auto', words='auto', lead=0.02, lag=None):
    if self.sp.get('whistle'):                         # never lip-syncs: the head bob only
        return _ws_say(self, intervals if len(intervals[0]) > 2 or text is None else [(intervals[0][0], intervals[0][1], text)])
    return _acting_talk_prev_bus(self, intervals, text, intensity, env, words, lead, lag)


Acting.talk = _acting_talk_bus


def draw_whistle_hands(pen, actor, t, sides=(1, -1), light=None, detail=None):
    """Draw only his gloves (and wrists) on top of the scenery (the doorframe he curls round, the walls), exactly where
    draw() puts them. Draw him first with pose.ws_hands_front = 2 (or the side) so the hands are not drawn twice."""
    P = actor.at(t)
    s = actor.height / 1000.0
    head_px = CAST[actor.who]['hh'] * s
    det = _auto_detail(pen, head_px) if detail is None else detail
    c = Ctx(pen, skia.Matrix(), _lw_for(head_px)).sub(actor.x0 + P.dx, actor.y0 + P.dy, 0.0, s)
    cc = c.sub(0.0, 0.0, 0.0, _WSU * max(P.ws_scale, 1e-3))
    sp = CAST[actor.who]
    pal = _WS_PAL94 if sp.get('tv') else _WS_PAL
    view = _WSView(P); R = _ws_rig(P)
    for sd in sides:
        if int(getattr(P, 'ws_hands_front', 0) or 0) == 3 and getattr(P, 'ws_lw' if sd > 0 else 'ws_rw') <= 0.6: continue
        _ws_glove(cc, view, R, P, sd, pal, det, t, light)


# ====================================================================================================== THE PEOPLE
# Faces, bodies and hands are the v3 cast system (characters_bunny.py / characters_doctor.py). New here: Grandma Della's
# knit cap and DELLA name tape, Sami's dinosaur hood and tail (torn half off at the last stop), Theo's yellow raincoat
# (faded until three o'clock), the new girl's hair clip, the 1994 studio kids, the props they handle, a step up onto a
# bus step, and the beats' expressions.

# ---------------------------------------------------------------------------------------------------- hair: Della's knit cap
_hair_region_doc_ = _hair_region


def _hair_region(c, hm, sp, P, det, sil, t):
    style = sp.get('hair')
    if style == 'della_cap':
        sp2 = dict(sp, hair='set_curls')
        _hair_region_doc_(c, hm, sp2, P, det, sil, t)            # short grey natural curls at the ears and nape
        X, Y = hm.arc_phi(lambda ph: -56.0 + 10.0 * np.abs(np.sin(ph)) ** 2, 120)
        if len(X) < 3: return
        cap = inter(_bumpy(hm, 9.0, 14, 2.2, -136.0, 40.0, spiky=False, seed=9), _region_above(X, Y))
        cc = sp['cloth'].get('cap', '#7a2f3a'); csh = mix(cc, '#000000', 0.3); chi = mix(cc, '#ffffff', 0.25)
        c.fill(cap, cc)
        with c.clip(cap):
            c.radial(None, -30, -100, 160, [(0, chi, 120), (0.5, cc, 0), (1, csh, 200)], clip=False)
            if det >= 1:
                rib = []
                for k in range(-9, 10):
                    Xr, Yr = [], []
                    for yy in (-140.0, -40.0):
                        x_, y_, v_ = hm.map1(k * 12.0, yy, 10.0)
                        Xr.append(x_); Yr.append(y_)
                    rib.append(poly(list(zip(Xr, Yr)), False))
                c.line(_multi(rib), c.lw * 0.45, csh, 150)
            X2, Y2 = hm.arc_phi(lambda ph: -70.0 + 10.0 * np.abs(np.sin(ph)) ** 2, 120)
            if len(X2) > 2: c.line(smooth(list(zip(X2.tolist(), Y2.tolist())), False), c.lw * 0.9, csh)
        c.line(cap, c.lw)
        return
    _hair_region_doc_(c, hm, sp, P, det, sil, t)
    if sp.get('clip') and not P.__dict__.get('_back_view'):            # the new girl's hair clip
        x_, y_, v_ = hm.map1(-52.0, -78.0, 14.0)
        if v_ > 0.1:
            cl_ = rrect(x_ - 16, y_ - 5, 32, 10, 4)
            c.fill(cl_, sp['clip']); c.line(cl_, c.lw * 0.6)


# ---------------------------------------------------------------------------------------------------- outfits
def _front_della(c, sp, B, rows, P, det, t):
    """Grandma Della's navy driver jacket (open over a cream sweater) with a white DELLA name tape."""
    _front_jacket3(c, sp, B, rows, P, det, t)
    X, Y, vv, s_ = B.surf(62, B.y_ch - 34, 6, False, rows)
    if vv > 0.15:
        w = 64 * s_ * max(0.35, vv); h = 18 * s_
        tp = rect(X - w / 2, Y - h / 2, w, h)
        c.fill(tp, '#f2efe6'); c.line(tp, c.lw * 0.5)
        if det >= 1: _block_text(c, 'DELLA', X, Y, h * 0.55, '#1e2a4a', 255, w=h * 0.11)


def _front_raincoat_kid(c, sp, B, rows, P, det, t):
    """Theo's yellow raincoat, closed: a placket of black toggle snaps, a collar, patch pockets; hood down behind."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    pl, v = _surf_poly(B, rows, [(6, yS - 24), (6, B.y_hip + 20)], dz=3)
    if v > -0.1: c.line(poly(pl, False), lw * 0.9)
    for k in range(4):
        X, Y, vv, s_ = B.surf(-6, yS + 8 + k * 46, 5, False, rows)
        if vv > 0.1:
            tg = rrect(X - 9 * s_, Y - 3.5 * s_, 18 * s_, 7 * s_, 3 * s_)
            c.fill(tg, '#1e1c1a')
    for sd in (-1, 1):
        col_, v = _surf_poly(B, rows, [(sd * 6, yS - 34), (sd * (b['neck'] + 26), yS - 40), (sd * (b['neck'] + 38), yS + 2), (sd * 8, yS + 20)], dz=7)
        if v > -0.2:
            cp = smooth(col_, True, 0.4); c.fill(cp, cl['top']); c.fill(_crescent(cp, sd * 4, 0), cl['top_sh'], 120); c.line(cp, lw * 0.7)
        pk, v = _surf_poly(B, rows, [(sd * 30, B.y_wa + 10), (sd * 80, B.y_wa + 10), (sd * 80, B.y_hip + 4), (sd * 30, B.y_hip + 4)], dz=3)
        if v > 0.05: c.line(poly(pk), lw * 0.6)
    if det >= 1:
        hem, v = _surf_poly(B, rows, [(-b['hip'] - 12, B.y_hip + 30), (b['hip'] + 12, B.y_hip + 30)], dz=2)
        if v > -0.2: c.line(poly(hem, False), lw * 0.5, LINE, 160)


_FRONTS3.update({'della': _front_della, 'raincoat_kid': _front_raincoat_kid})
_limb_cols3_doc_ = _limb_cols3


def _limb_cols3(sp):
    if sp.get('outfit') == 'della':
        cl = sp['cloth']
        return cl['top'], cl['top_sh'], cl['trousers'], cl['trousers_sh'], cl.get('shoes', '#222')
    return _limb_cols3_doc_(sp)


# ---------------------------------------------------------------------------------------------------- Sami's dinosaur hood and tail
def _dino_extras(c, sp, B, P, det, behind):
    """Sami's pajamas: the dinosaur hood lying behind his neck (orange spikes along its seam) and the tail from the back of
    the pajama bottoms to the floor behind him (sp['tail'] 1 whole, 0.5 torn half off with a frayed end)."""
    cl = sp['cloth']; lw = c.lw
    tl = sp.get('tail', 1.0)
    # tail
    hip = B.y_hip + 30
    pts3 = [(0, hip, -60), (0, hip + 90, -200), (0, hip + 200, -330), (0, -36, -440)]
    n_ = max(2, int(round(1 + (len(pts3) - 1) * tl)))
    seg = pts3[:n_]
    if tl < 0.99:                                        # torn: ends partway with a ragged edge
        a_, b_ = np.array(pts3[n_ - 1], float), np.array(pts3[min(n_, len(pts3) - 1)], float)
        seg = pts3[:n_ - 1] + [tuple(a_ + (b_ - a_) * 0.3)]
    p2 = [B.p3(x, y, z, upper=False)[:2] for x, y, z in seg]
    ws = [62.0, 46.0, 30.0, 16.0][:len(p2)]
    if tl < 0.99: ws[-1] = ws[-1] * 1.1
    tp = _tube(p2, [w * B.p3(0, hip, 0, upper=False)[2] for w in ws], 0.8)
    c.fill(tp, cl['top']); c.fill(_crescent(tp, 4, 6), cl['top_sh'], 160)
    if det >= 1:                                         # spikes along the tail's top
        sp_ = []
        for k in range(len(p2) - 1):
            x0, y0 = p2[k]; x1, y1 = p2[k + 1]
            for j in (0.3, 0.75):
                xm, ym = x0 + (x1 - x0) * j, y0 + (y1 - y0) * j
                d = math.hypot(x1 - x0, y1 - y0) or 1.0
                nx, ny = (y1 - y0) / d, -(x1 - x0) / d
                if ny > 0: nx, ny = -nx, -ny
                w_ = ws[k] * 0.45
                sp_.append(poly([(xm - (x1 - x0) / d * w_ * 0.5 + nx * w_ * 0.8, ym - (y1 - y0) / d * w_ * 0.5 + ny * w_ * 0.8),
                                 (xm + nx * w_ * 1.7, ym + ny * w_ * 1.7),
                                 (xm + (x1 - x0) / d * w_ * 0.5 + nx * w_ * 0.8, ym + (y1 - y0) / d * w_ * 0.5 + ny * w_ * 0.8)], True))
        if sp_: c.fill(_multi(sp_), cl.get('spike', '#e9a23b')); c.line(_multi(sp_), lw * 0.6)
    c.line(tp, lw)
    if tl < 0.99:                                        # the frayed tear
        xe, ye = p2[-1]
        fr = [poly([(xe + (k - 2) * 7, ye - 4), (xe + (k - 2) * 7 + 3, ye + 10 + 6 * hash01(k, 73))], False) for k in range(5)]
        c.line(_multi(fr), lw * 0.8, cl['top_sh']); c.fill(oval(xe, ye, ws[-1] * 0.45, ws[-1] * 0.3), '#f4f2ea', 220)
    # hood
    nb = B.p3(0, B.y_sh - 34, 0)
    nw = sp['body']['neck']
    hood = smooth([(nb[0] - (nw + 54) * nb[2], nb[1] + 14), (nb[0] - (nw + 40) * nb[2], nb[1] - 56), (nb[0], nb[1] - 74),
                   (nb[0] + (nw + 40) * nb[2], nb[1] - 56), (nb[0] + (nw + 54) * nb[2], nb[1] + 14)], True, 0.8)
    c.fill(hood, cl['top']); c.fill(_crescent(hood, 0, 10), cl['top_sh'], 160)
    if det >= 1:
        sk = []
        for k in range(4):
            x_ = nb[0] + (-30 + 20 * k) * nb[2]; y_ = nb[1] - 70 + abs(k - 1.5) * 8
            sk.append(poly([(x_ - 9, y_ + 6), (x_, y_ - 18), (x_ + 9, y_ + 6)], True))
        c.fill(_multi(sk), cl.get('spike', '#e9a23b')); c.line(_multi(sk), lw * 0.6)
    c.line(hood, lw)


_figure_bus_people_prev = _figure


def _figure(c, who, P, det, t, light=None, upper_only=False):
    sp = CAST[who]
    if sp.get('dino'):
        B = Body(sp, P)
        front = B.ct > -0.2
        if front: _dino_extras(c, sp, B, P, det, True)
        r = _figure_bus_people_prev(c, who, P, det, t, light, upper_only)
        if not front: _dino_extras(c, sp, B, P, det, False)
        return r
    return _figure_bus_people_prev(c, who, P, det, t, light, upper_only)


# ---------------------------------------------------------------------------------------------------- the cast
# Mina, 13 (the narrator): dark hair in a low ponytail, warm brown eyes, an oversized grey-green hoodie over plaid pajama
# bottoms, socks (barefoot for the chase). Protective, smart; guilt and resolve; kind at the end.
_MINA = dict(hair='pony', sex='f', hh=196.0, m=1.57, head_ws=[0, 51, 74, 90, 95, 94, 87, 72, 51, 27, 0],
             eye_dx=41, eye_y=-2, eye_r=20.0, iris_c='#5a3a24', lid_rest=0.1, brow_th=7.5, nose_len=18, mouth_w=18,
             skin='#d9a585', skin_sh='#ad7a60', skin_dp='#6e4a3e', blush='#d98a80', lip='#a86a60', lips=0.1,
             hair_c='#231812', brow_c='#1c130e', bags=0.15, age=0.02, lashes=0.6, part=0,
             body=dict(sh=100, ch=96, wa=88, hip=96, arm=(42, 34), leg=(46, 38), neck=35, hand=0.92))
_MINA_CLOTH = dict(top='#6f7a6a', top_sh='#4c5649', top_hi='#8e9a88', hood='#66715f', hood_sh='#454e40', string='#e9e4d8',
                   trousers='#5a4a6e', trousers_sh='#3c3150', socks='#d8d4cc', socks_sh='#aaa69c')
CAST['mina'] = _v3cast(outfit='hoodie3', feet='socks', **_MINA, cloth=dict(_MINA_CLOTH))
CAST['mina_bare'] = _v3cast(outfit='hoodie3', feet='socks', **_MINA, cloth=dict(_MINA_CLOTH, socks='#d9a585', socks_sh='#ad7a60'))
# Sami, 6: small, round face, a big gap-toothed proud grin, a dark-brown mop; green dinosaur pajamas with a hood and a
# tail (orange spikes); socks. 'sami_torn': half the tail ripped off.
_SAMI = dict(hair='cowlick', sex='m', hh=240.0, child=True, m=1.16, head_ws=[0, 58, 86, 100, 105, 105, 100, 88, 67, 37, 0],
             eye_dx=40, eye_y=8, eye_r=23.0, iris_c='#4a3020', iris_k=0.74, lid_rest=0.06, pupil=1.2, brow_th=6.5, nose_len=12,
             mouth_y=64, mouth_w=16, nose='button', ears=1.2, gap=True,
             skin='#dfaa88', skin_sh='#b47f64', skin_dp='#76503f', blush='#ec9a8a', lip='#c07a6c', lips=0.1,
             hair_c='#3a2416', brow_c='#2e1c10', bags=0.05, age=0.0, blink_rate=0.4, lashes=0.5, part=1,
             body=dict(sh=78, ch=76, wa=74, hip=76, arm=(32, 27), leg=(37, 31), neck=28, hand=0.74, arm_k=0.86))
_SAMI_CLOTH = dict(top='#6fae6a', top_sh='#4c8448', top_hi='#93cc8c', trim='#f4f7ee', print_c='#2f6a34', print_c2='#e9a23b',
                   trousers='#6fae6a', trousers_sh='#4c8448', socks='#e8e6e0', socks_sh='#bcb8ae', spike='#e9a23b')
CAST['sami'] = _v3cast(outfit='pj_dino', feet='socks', dino=True, tail=1.0, **_SAMI, cloth=dict(_SAMI_CLOTH))
CAST['sami_torn'] = dict(CAST['sami'], tail=0.5)
# Grandma Della, 63: warm brown skin, grey natural hair under a burgundy knit cap, reading glasses on a cord, a navy
# driver jacket over a cream sweater with a white DELLA name tape, dark trousers, sensible shoes. Warm, firm,
# frightened underneath; a school-bus driver for 32 years.
CAST['della'] = _v3cast(
    outfit='della', hair='della_cap', sex='f', hh=186.0, m=1.63, glasses=True, chain=True,
    head_ws=[0, 50, 73, 89, 95, 95, 89, 75, 55, 30, 0],
    eye_dx=41, eye_y=-4, eye_r=17.5, iris_c='#3a2418', lid_rest=0.24, brow_th=7.0, nose_len=22, mouth_w=21,
    skin='#8d5a3e', skin_sh='#6a412b', skin_dp='#43281a', blush='#a8614c', lip='#7a4436', lips=0.3,
    hair_c='#c9c4bc', brow_c='#8a847c', bags=0.55, age=0.62, lashes=0.4, part=0, feet='shoes',
    body=dict(sh=106, ch=110, wa=102, hip=112, arm=(44, 37), leg=(48, 40), neck=36, hand=0.96),
    cloth=dict(top='#24324f', top_sh='#151e33', top_hi='#3a4a6e', collar='#1a2540', shirt='#e8dfcc', shirt_sh='#bfb49c',
               trousers='#2b2a30', trousers_sh='#18171c', shoes='#2a221e', shoes_sh='#160f0c', button='#c9a24a', cap='#7a2f3a'))
# Theo, about 12 (forever): a 1994 boy in a yellow raincoat (hood down), a bowl-ish cut, big careful eyes; ordinary and
# lonely. 'theo' is faded and desaturated (nobody sees him); 'theo_color' full colour after three o'clock.
_THEO = dict(hair='side_short', sex='m', hh=214.0, child=True, m=1.38, head_ws=[0, 55, 80, 95, 100, 100, 94, 81, 60, 32, 0],
             eye_dx=41, eye_y=2, eye_r=21.0, iris_c='#5a4630', iris_k=0.7, lid_rest=0.14, pupil=1.05, brow_th=7.0, nose_len=15,
             mouth_y=62, mouth_w=16, nose='button', ears=1.1,
             skin='#eac2a6', skin_sh='#bf947c', skin_dp='#7d5a50', blush='#e2a296', lip='#b8807a', lips=0.05,
             hair_c='#7a5434', brow_c='#5e3e24', bags=0.3, age=0.0, blink_rate=0.25, lashes=0.3, part=-1,
             body=dict(sh=88, ch=86, wa=82, hip=84, arm=(36, 30), leg=(41, 34), neck=31, hand=0.82, arm_k=0.9))
_THEO_CLOTH = dict(top='#e7c23a', top_sh='#b8921e', top_hi='#f6dc78', hood='#d9b432', hood_sh='#a8851a', string='#e9e4d8',
                   trousers='#4a5a7a', trousers_sh='#2f3b54', shoes='#6a5040', shoes_sh='#43301f')
CAST['theo_color'] = _v3cast(outfit='raincoat_kid', feet='shoes', **_THEO, cloth=dict(_THEO_CLOTH))
_t_ = dict(CAST['theo_color'])
for _k in ('skin', 'skin_sh', 'skin_dp', 'blush', 'lip', 'hair_c', 'brow_c', 'iris_c'):
    _t_[_k] = _greyed(_t_[_k], 0.5, '#9aa4a8', 0.04)
# review r3: the raincoat must still read YELLOW under the bus's amber (it read beige at 0.55): the coat fades less
_t_['cloth'] = {k: _greyed(v, 0.22 if k in ('top', 'top_sh', 'top_hi', 'hood', 'hood_sh') else 0.55, '#9aa4a8', 0.05) for k, v in _THEO_CLOTH.items()}
_t_.update(lid_rest=0.2, micro=0.5)
CAST['theo'] = _t_
# The new girl, about 11: hair in a clip, an oversized plain backpack with no name on it, a mustard cardigan; looks down
# at her lap. Non-speaking.
CAST['new_girl'] = _v3cast(
    outfit='neat3', hair='chin', sex='f', hh=222.0, child=True, m=1.42, clip='#e46a8a',
    head_ws=[0, 55, 80, 95, 100, 100, 95, 82, 60, 32, 0],
    eye_dx=40, eye_y=2, eye_r=21.0, iris_c='#3a2a1e', iris_k=0.7, lid_rest=0.18, pupil=1.05, brow_th=6.5, nose_len=14,
    mouth_y=62, mouth_w=15, nose='button', skin='#c79470', skin_sh='#9c6b50', skin_dp='#5e3e30', blush='#d08a7a', lip='#a06a5e',
    hair_c='#1e1612', brow_c='#1a120c', bags=0.15, age=0.0, blink_rate=0.3, lashes=0.6, part=1, feet='shoes',
    body=dict(sh=86, ch=84, wa=80, hip=84, arm=(35, 29), leg=(40, 33), neck=30, hand=0.8, arm_k=0.88),
    cloth=dict(top='#c99a3e', top_sh='#9a7226', top_hi='#e2b860', collar='#f2eee4', collar_sh='#cfc9bc', button='#6a4a2a',
               trousers='#3a4a6a', trousers_sh='#263248', shoes='#4a3a34', shoes_sh='#2a201c'))
# The 1994 studio kids (holding up their name cards to the camera): bright early-90s colours.
for _i, (_hair, _sex, _sk, _hc, _top, _tsh, _trs) in enumerate((
        ('pigtails', 'f', '#efc6aa', '#8a5a2e', '#2fa39a', '#1f7a72', '#5a3a8a'),
        ('cowlick', 'm', '#b9805c', '#1e1410', '#8a3fa8', '#632a7a', '#2a3a5e'),
        ('chin', 'f', '#f0cbb2', '#c99a4a', '#e8573a', '#b23e26', '#2a4a7a'))):
    CAST['kid94_' + 'abc'[_i]] = _v3cast(
        outfit='hoodie3', hair=_hair, sex=_sex, hh=228.0, child=True, m=1.3, head_ws=[0, 57, 83, 97, 102, 102, 97, 85, 63, 34, 0],
        eye_dx=40, eye_y=6, eye_r=22.0, iris_c='#4a3424', iris_k=0.72, lid_rest=0.08, pupil=1.1, brow_th=6.5, nose_len=13,
        mouth_y=64, mouth_w=16, nose='button', skin=_sk, skin_sh=mix(_sk, '#5a3020', 0.25), skin_dp=mix(_sk, '#2a1008', 0.5),
        blush='#e9a093', lip='#c08074', lips=0.1, hair_c=_hc, brow_c=mix(_hc, '#000000', 0.2), bags=0.05, age=0.0,
        blink_rate=0.35, lashes=0.5 if _sex == 'f' else 0.3, part=1, feet='shoes',
        body=dict(sh=82, ch=80, wa=78, hip=80, arm=(34, 28), leg=(39, 33), neck=29, hand=0.78, arm_k=0.88),
        cloth=dict(top=_top, top_sh=_tsh, top_hi=mix(_top, '#ffffff', 0.25), hood=_tsh, hood_sh=mix(_tsh, '#000000', 0.25),
                   string='#f2f2f2', trousers=_trs, trousers_sh=mix(_trs, '#000000', 0.3), shoes='#f2f2f2', shoes_sh='#b8b8b8'))

BUS_CAST = ('whistle', 'whistle94', 'mina', 'mina_bare', 'sami', 'sami_torn', 'della', 'theo', 'theo_color', 'new_girl',
            'kid94_a', 'kid94_b', 'kid94_c')

# ---------------------------------------------------------------------------------------------------- expressions per beat
EXPR.update({
    'guilt': dict(brow_sad=0.85, brow_up=0.2, smile=-0.25, m_press=0.55, eye_open=0.85, look_y=0.45, h_nod=0.15, pupil=1.0),
    'resolve': dict(brow_angry=0.45, brow_sad=0.15, m_press=0.6, squint=0.15, pupil=0.9, smile=-0.1),
    'hush_fear': dict(wide=0.65, pupil=0.5, brow_sad=0.75, brow_up=0.55, m_press=0.85, tremble=0.35, smile=-0.25),
    'kind_ask': dict(smile=0.4, teeth=0.2, brow_up=0.3, brow_sad=0.15, pupil=1.05, m_open=0.08),
    'shout_here': dict(m_open=0.95, m_round=0.3, smile=0.45, teeth=0.6, brow_up=0.65, wide=0.3, pupil=0.9),
    'proud_grin': dict(smile=1.0, teeth=1.0, m_open=0.18, brow_up=0.4, squint=0.2, pupil=1.05),
    'lonely': dict(brow_sad=0.55, brow_up=0.2, smile=0.08, eye_open=0.86, pupil=1.0, h_nod=0.06),
    'tempted': dict(brow_sad=0.8, brow_up=0.35, eye_open=0.92, m_open=0.12, pupil=1.15, wet=0.6, smile=-0.1),
    'grim_drive': dict(brow_angry=0.55, squint=0.3, m_press=0.7, pupil=0.8),
    'tender': dict(smile=0.45, brow_sad=0.45, brow_up=0.25, eye_open=0.88, wet=0.7, pupil=1.05),
    'terrified_call': dict(m_open=0.9, m_round=0.45, brow_sad=0.9, brow_up=0.7, wide=0.7, pupil=0.45, tremble=0.4),
})
EXPR_BUS = ('fear', 'shock', 'scream', 'guilt', 'resolve', 'hush_fear', 'kind_ask', 'relief', 'shout_here', 'proud_grin',
            'lonely', 'tempted', 'grim_drive', 'tender', 'terrified_call', 'warm', 'calm_firm', 'stern_afraid', 'set_jaw',
            'brave', 'sleepy', 'sad', 'cry')


# ---------------------------------------------------------------------------------------------------- props
def _p_walkie(c, det, t, P=None):
    """A toy walkie-talkie (14 cm): blue body, yellow antenna, a grille, a red talk button."""
    c.fill(rrect(1.6, -11.5, 1.6, 6.0, 0.6), '#e9c23a'); c.line(rrect(1.6, -11.5, 1.6, 6.0, 0.6), c.lw * 0.5)
    b = rrect(-3.4, -6.0, 6.8, 13.0, 1.6)
    c.fill(b, '#3a6ab0'); c.fill(_crescent(b, 0.6, 0.6), '#264a80', 200); c.line(b, c.lw * 0.7)
    if det >= 1:
        for k in range(4): c.line(poly([(-2.2, -4.0 + k * 1.1), (2.2, -4.0 + k * 1.1)], False), c.lw * 0.4, '#1a2a4a')
    c.fill(oval(0.0, 2.6, 1.2, 1.2), '#d8433a'); c.line(oval(0.0, 2.6, 1.2, 1.2), c.lw * 0.4)


def _p_rex(c, det, t, P=None):
    """Rex, Sami's plush dinosaur (about 28 cm): green, a round belly, orange felt spikes, button eyes."""
    g, gsh = '#5f9e58', '#3f7038'
    body = smooth([(-8, 6), (-9, -2), (-6, -9), (0, -11), (6, -8), (9, 0), (8, 8), (2, 11), (-5, 10)], True, 0.9)
    tail = smooth([(6, 6), (13, 9), (17, 8), (12, 4), (8, 2)], True, 0.8)
    head = smooth([(-6, -9), (-10, -15), (-6, -21), (2, -21), (5, -16), (2, -11)], True, 0.9)
    for p_ in (tail, body, head):
        c.fill(p_, g); c.fill(_crescent(p_, 1.0, 1.0), gsh, 170); c.line(p_, c.lw * 0.7)
    c.fill(oval(0.5, 2.0, 5.0, 6.0), '#b9d89a'); c.line(oval(0.5, 2.0, 5.0, 6.0), c.lw * 0.4)
    sk = [poly([(x - 1.6, y + 1.0), (x + 0.3, y - 2.4), (x + 1.8, y + 1.2)], True) for x, y in ((3, -20), (6, -12), (9, -4), (11, 4))]
    c.fill(_multi(sk), '#e9a23b'); c.line(_multi(sk), c.lw * 0.5)
    c.fill(oval(-3.0, -17.0, 1.1, 1.1), '#141414'); c.fill(oval(-2.6, -17.4, 0.35, 0.35), '#ffffff')
    for x in (-7, 4):
        c.fill(oval(x, 10.5, 2.4, 1.6), g); c.line(oval(x, 10.5, 2.4, 1.6), c.lw * 0.5)


def _p_broom(c, det, t, P=None):
    """The porch broom (120 cm): a wooden handle, a straw head (drawn handle-first along the hand)."""
    c.fill(rrect(-1.1, -2.0, 2.2, 104.0, 1.0), '#a87a4a'); c.line(rrect(-1.1, -2.0, 2.2, 104.0, 1.0), c.lw * 0.5)
    hd = poly([(-5.0, 100.0), (5.0, 100.0), (13.0, 128.0), (-13.0, 128.0)], True)
    c.fill(hd, '#c9a85a'); c.line(hd, c.lw * 0.6)
    if det >= 1:
        c.line(_multi([poly([(-4.0 + k * 1.6, 104.0), (-11.0 + k * 3.7, 127.0)], False) for k in range(6)]), c.lw * 0.35, '#8a6a2a')
    c.fill(rect(-5.5, 101.0, 11.0, 3.0), '#c43a2a')


def _p_name_card(c, det, t, P=None):
    """A kid's name card (28 x 20 cm) held up to the camera: name, school, bus in marker."""
    txt = (getattr(P, 'card_text', None) if P is not None else None) or 'AMY|LARKFIELD EL|BUS 4'
    c.fill(rect(-14.0, -18.0, 28.0, 20.0), '#fbfaf4'); c.line(rect(-14.0, -18.0, 28.0, 20.0), c.lw * 0.6)
    if det >= 1:
        lines = txt.split('|')
        for k, s in enumerate(lines[:3]):
            _block_text(c, s, 0.0, -13.0 + k * 6.0, 3.6 if k == 0 else 2.2, '#1a1a2a' if k == 0 else '#3a3a6a', 255,
                        w=0.6 if k == 0 else 0.35, wobble=0.5, seed=k + len(s))


def _p_ticket_y(c, det, t, P=None):
    """His yellow ticket, punched through the middle: SAMI. SEAT 4. LAST STOP 3 A.M."""
    tk = rect(-6.0, -3.0, 12.0, 6.0)
    c.fill(tk, '#e9c440'); c.line(tk, c.lw * 0.5)
    c.fill(oval(0.0, 0.0, 0.7, 0.7), '#1a1612')
    if det >= 1:
        _block_text(c, 'SAMI', -3.0, -1.4, 1.0, '#3a2a10', 255, w=0.18)
        _block_text(c, 'SEAT 4', -3.0, 1.2, 0.7, '#3a2a10', 255, w=0.12)
        _block_text(c, '3 AM', 3.4, 1.2, 0.7, '#3a2a10', 255, w=0.12)


def _p_punch(c, det, t, P=None):
    """The chrome ticket punch (16 cm): two handles hinged at a punch head."""
    c.fill(poly([(-1.4, 0.0), (1.4, 0.0), (1.0, 12.0), (-1.0, 12.0)], True), '#b9bec6'); c.line(poly([(-1.4, 0.0), (1.4, 0.0), (1.0, 12.0), (-1.0, 12.0)], True), c.lw * 0.5)
    c.fill(poly([(1.0, 1.0), (3.4, 1.4), (3.0, 11.0), (1.0, 11.0)], True), '#9aa0a8'); c.line(poly([(1.0, 1.0), (3.4, 1.4), (3.0, 11.0), (1.0, 11.0)], True), c.lw * 0.5)
    hd = rrect(-2.4, 11.0, 5.0, 5.0, 1.2)
    c.fill(hd, '#d9dde2'); c.line(hd, c.lw * 0.6); c.fill(oval(0.1, 13.5, 0.8, 0.8), '#2a2a2a')


def _p_pencil(c, det, t, P=None):
    c.fill(rect(-0.4, -2.0, 0.8, 16.0), '#e9b83a'); c.line(rect(-0.4, -2.0, 0.8, 16.0), c.lw * 0.4)
    c.fill(poly([(-0.4, 14.0), (0.4, 14.0), (0.0, 16.5)], True), '#e8cfa0'); c.fill(rect(-0.4, -3.2, 0.8, 1.2), '#e88a9a')


def _p_backpack(c, det, t, P=None):
    """The new girl's oversized plain backpack (40 cm): no name on it anywhere."""
    b = rrect(-17.0, -22.0, 34.0, 42.0, 8.0)
    c.fill(b, '#5a7a8a'); c.fill(_crescent(b, 2.0, 2.0), '#3e5866', 200); c.line(b, c.lw * 0.8)
    pk = rrect(-12.0, 0.0, 24.0, 16.0, 4.0)
    c.fill(pk, '#4e6c7a'); c.line(pk, c.lw * 0.6)
    c.line(poly([(-12.0, 4.0), (12.0, 4.0)], False), c.lw * 0.5, '#2a3a44')
    c.fill(rrect(-4.0, -26.0, 8.0, 6.0, 3.0), '#3e5866'); c.line(rrect(-4.0, -26.0, 8.0, 6.0, 3.0), c.lw * 0.5)


def _p_dino_pack(c, det, t, P=None):
    """Sami's dinosaur backpack (30 cm): green with orange spikes and SAMI embroidered on it (turned to the wall later)."""
    b = rrect(-13.0, -16.0, 26.0, 32.0, 7.0)
    c.fill(b, '#6fae6a'); c.fill(_crescent(b, 1.5, 1.5), '#4c8448', 200); c.line(b, c.lw * 0.8)
    sk = [poly([(-11 + k * 6.0, -16.0), (-8 + k * 6.0, -21.0), (-5 + k * 6.0, -16.0)], True) for k in range(4)]
    c.fill(_multi(sk), '#e9a23b'); c.line(_multi(sk), c.lw * 0.5)
    c.fill(rrect(-9.0, 2.0, 18.0, 7.0, 2.0), '#f4f2ea'); c.line(rrect(-9.0, 2.0, 18.0, 7.0, 2.0), c.lw * 0.5)
    if det >= 1: _block_text(c, 'SAMI', 0.0, 5.5, 3.6, '#2f6a34', 255, w=0.6)


PROPS3.update({
    'walkie': (_p_walkie, 'upright', (0.0, 0.0)),
    'rex': (_p_rex, 'upright', (0.0, 0.0)),
    'broom': (_p_broom, 'grip', (0.0, 0.0)),
    'name_card': (_p_name_card, 'upright', (0.0, -8.0)),
    'ticket_y': (_p_ticket_y, 'upright', (0.0, 0.0)),
    'punch': (_p_punch, 'grip', (0.0, 0.0)),
    'pencil': (_p_pencil, 'grip', (0.0, 0.0)),
    'backpack': (_p_backpack, 'upright', (0.0, 0.0)),
    'dino_pack': (_p_dino_pack, 'upright', (0.0, 0.0)),
})
POSE_DISCRETE.update(card_text=None)


# ---------------------------------------------------------------------------------------------------- a foot up onto a step
POSE_DEFAULTS.update(step_l=0.0, step_r=0.0, step_h=110.0, step_f=170.0)
_leg_chain_bus_prev = _leg_chain


def _leg_chain(sp, B, P, side):
    """pose.step_l / step_r 0..1 lift that foot up onto a step (step_h body units up, step_f forward) and back down."""
    H, K, A, pitch = _leg_chain_bus_prev(sp, B, P, side)
    st = clamp(getattr(P, 'step_l' if side > 0 else 'step_r', 0.0))
    if st > 0.001:
        arc = math.sin(PI * min(st, 1.0) * 0.5)
        Ad = _v3(A[0], A[1] - P.step_h * arc - 30.0 * math.sin(PI * st), A[2] + P.step_f * st)
        K, A = _ik(H, Ad, _THIGH, _SHIN, _v3(0.06 * side, -0.2, 1.0))
    return H, K, A, pitch


def _acting_step_up(self, t0, side=1, up=0.9, hold=0.5, back=0.7, h=110.0, f=170.0):
    """One foot lifts onto the first step (up s), stays (hold s), and pulls back down (back s): Mina at his bus."""
    key = 'step_l' if side > 0 else 'step_r'

    def fn(P, t):
        u = ease_in_out(prog(t, t0, t0 + up)) * (1.0 - ease_in_out(prog(t, t0 + up + hold, t0 + up + hold + back)))
        if u <= 0: return
        setattr(P, key, u); P.step_h = h; P.step_f = f
        P.lean += 0.08 * u
    self._add(t0, t0 + up + hold + back + 0.1, fn)
    return [self._ev(t0 + up, 'step_touch', -6.0), self._ev(t0 + up + hold, 'step_off', -8.0)]


def _acting_hug_prop(self, t0, prop, t1=None, dur=0.6, z=90.0, part='chest'):
    """Both arms wrapped round a held thing at the chest (Rex, the backpack): the prop in the near hand, both hands meet."""
    self.hold_prop(prop, 1, t0, t1)
    tgt = lambda t: self.where(t, part, post=False)                # noqa: E731
    self.reach_to(t0, 1, lambda t: (tgt(t)[0] + 0.03 * self.height, tgt(t)[1] + 0.05 * self.height), t1=t1, dur=dur, z=z, contact='palm', shape='grip')
    self.reach_to(t0, -1, lambda t: (tgt(t)[0] - 0.03 * self.height, tgt(t)[1] + 0.07 * self.height), t1=t1, dur=dur, z=z * 0.9, contact='palm', shape='open')
    return self


Acting.step_up = _acting_step_up
Acting.hug_prop = _acting_hug_prop


def _p_tail_piece(c, det, t, P=None):
    """The torn-off half of Sami's dinosaur tail, hanging from his glove (24 cm, frayed at the top)."""
    tp = _tube([(0.0, 0.0), (1.5, 9.0), (0.5, 18.0), (-1.0, 24.0)], [7.0, 5.6, 3.6, 1.6], 0.8)
    c.fill(tp, '#6fae6a'); c.fill(_crescent(tp, 0.8, 0.8), '#4c8448', 170); c.line(tp, c.lw * 0.6)
    sk = [poly([(2.6 + 0.2 * k, 3.0 + 6.5 * k), (5.6 - 0.6 * k, 5.0 + 6.5 * k), (2.4 + 0.1 * k, 7.0 + 6.5 * k)], True) for k in range(3)]
    c.fill(_multi(sk), '#e9a23b'); c.line(_multi(sk), c.lw * 0.4)
    if det >= 1:
        c.line(_multi([poly([(-3.0 + 1.5 * k, -0.5), (-2.6 + 1.5 * k, -2.6 - hash01(k, 77))], False) for k in range(5)]), c.lw * 0.5, '#f4f2ea')


PROPS3['tail_piece'] = (_p_tail_piece, 'hang', (0.0, 0.0))


# ====================================================================================================== self-test
def _selftest_bus():
    """The bus film's checks (python3 characters.py --selftest runs them after the older films')."""
    out = []
    # every id draws in 6 views, full body and bust
    set_render_size(480, 270)
    surf = skia.Surface(CFG.rw, CFG.rh); pen = Pen(surf.getCanvas()); surf.getCanvas().scale(CFG.k, CFG.k)
    for who in BUS_CAST:
        for yaw in (0.0, 0.5, 1.0, 1.5, 2.0, -0.5):
            draw(pen, who, 960, 1000, 700, Pose(turn=yaw), t=0.3)
            draw_bust(pen, who, 960, 540, 0.6, Pose(h_turn=yaw), t=0.3)
    out.append('all %d bus ids draw in 6 views (full + bust)' % len(BUS_CAST))
    # his proportions
    P = Pose(); R = _ws_rig(P)
    hip = -R['Hc'][1]; crown = -(R['head'] + R['hrot'] @ np.array([0.0, -_WS_CROWN, 0.0]))[1]
    knee = -R['legs'][1][1][1]; tip = -_ws_hand3(R, 1, P)['fingers'][1][-1][1]
    hat = R['hat']; lean = math.degrees(math.atan2(hat['ax'][0], -hat['ax'][1]))
    assert 0.53 < hip / 244.0 < 0.57, ('legs', hip)
    assert abs(crown - 244.0) < 4.0, ('crown', crown)
    assert abs(tip - knee) < 16.0, ('arms to the knees', tip, knee)
    assert 0.34 < hat['H'] / 244.0 < 0.42 and 8.0 < lean < 16.0, ('hat', hat['H'], lean)
    out.append('Whistlestop: legs %.0f %%, crown %.0f cm, fingertips %.0f cm vs knee %.0f cm, hat %.0f cm leaning %.1f deg' %
               (100 * hip / 244.0, crown, tip, knee, hat['H'], lean))
    # never lip-syncs, never blinks; talks with a head bob
    a = Acting('whistle', seed=1, height=600.0).place(960, 1000)
    a.talk([(1.0, 3.0, 'I know your name That makes us friends')], env=None, words=None)
    mo = max(a.at(t_).m_open for t_ in np.arange(0.8, 3.2, 0.05)); bob = max(a.at(t_).ws_bob for t_ in np.arange(0.8, 3.2, 0.05))
    bl = max(a.at(t_).blink for t_ in np.arange(0.0, 20.0, 0.1))
    assert mo == 0.0 and bob > 0.2 and bl == 0.0, ('grin / blink', mo, bob, bl)
    out.append('no lip sync (m_open 0), head bob %.2f on his lines, never blinks' % bob)
    # the stretching reach lands on a far target
    a = Acting('whistle', seed=2, height=600.0).place(300, 1000)
    a.reach_far(0.0, 1, (1700, 560), dur=0.5, z=0.0, shape='reach')
    tx, ty = a.where(1.0, 'tips_l')
    miss = math.hypot(tx - 1700, ty - 560)
    assert miss < 12.0, ('reach_far', miss)
    out.append('stretching reach: fingertips %.1f px from a target 1400 px away' % miss)
    # the hat never goes through a ceiling; he bends under it
    for ceil in (235.0, 200.0, 160.0):
        R = _ws_rig(Pose(ws_ceil=ceil, ws_bend=0.0))
        top = max(-_ws_hat_ring(R['hat'], s_, np.linspace(-PI, PI, 12))[:, 1].min() for s_ in (0.5, 0.75, 1.0))
        assert top < ceil + 6.0, ('ceiling', ceil, top)
    out.append('ceilings 2.35 / 2.0 / 1.6 m: hat crushed and folded under them, he bends')
    # tape skip: cut, 3-frame stutter, events
    a = Acting('whistle', seed=3, height=600.0).place(500, 1000)
    ev = a.tape_skip([(0.0, dict(x=500)), (1.0, dict(x=900)), (2.0, dict(x=1300))])
    xs = [a.x0 + a.at(t_).dx for t_ in (0.99, 1.0, 1.0 + 1.5 / 30.0, 1.0 + 2.5 / 30.0)]
    assert abs(xs[0] - 500) < 1 and abs(xs[1] - 900) < 1 and abs(xs[2] - 500) < 1 and abs(xs[3] - 900) < 1 and len(ev) == 2, xs
    assert a.at(1.02).ws_glitch > 0.5 and a.at(1.6).ws_glitch < 0.01
    out.append('tape skip: hard cut, stutter frame back, tracking tear 0.28 s, %d tape_skip events' % len(ev))
    # feet on the floor standing, bent, crouched
    for d in (dict(), dict(ws_bend=1.0, ws_crouch=0.4), dict(ws_ceil=200.0)):
        a = Acting('whistle', seed=4, height=600.0).place(960, 1000); a.set(-1, None, 0.01, **d)
        assert a.foot_gap(1.0) < 1.0, ('feet', d, a.foot_gap(1.0))
    out.append('feet on the floor standing, bent double and under a ceiling')
    # lean_to brings the grin a foot from a face
    m = Acting('mina', seed=5, height=height_px('mina', 250.0)).place(700, 1000); m.face(0.6)
    a = Acting('whistle', seed=6, height=height_px('whistle', 250.0)).place(960, 1000); a.face(-0.6)
    a.lean_to(0.0, (m, 'eyes'), gap=30.0, dur=1.0, beats=1)
    mx, my = a.where(1.5, 'mouth'); ex, ey = m.where(1.5, 'eyes')
    d_cm = math.hypot(mx - ex, my - ey) / 2.5
    assert 15.0 < d_cm < 55.0, ('lean_to', d_cm)
    out.append('lean_to: the grin %.0f cm from Mina\'s eyes' % d_cm)
    # the crossing guard: his glove on Sami's raised hand
    s_ = Acting('sami', seed=7, height=height_px('sami', 250.0)).place(1000, 1000); s_.face(0.4)
    a = Acting('whistle', seed=8, height=height_px('whistle', 250.0)).place(760, 1000); a.face(0.4)
    a.hold_child(0.0, 1, s_, -1, dur=0.6)
    gx, gy = a.where(1.5, 'hand_l'); hx, hy = s_.where(1.5, 'hand_r')
    gap = math.hypot(gx - hx, gy - hy)
    assert gap < 30.0, ('hold_child', gap)
    out.append('crossing guard: glove %.0f px from Sami\'s hand' % gap)
    # no red-and-white: red pixels only from the STOP pin
    set_render_size(480, 270)
    surf = skia.Surface(CFG.rw, CFG.rh); cv_ = surf.getCanvas(); cv_.scale(CFG.k, CFG.k)
    reds = []
    for yaw in (0.0, 0.5, 1.0, 2.0):
        cv_.clear(skia.Color(26, 28, 36)); draw(Pen(cv_), 'whistle', 960, 1040, 900, Pose(turn=yaw), t=0.0, detail=2)
        im = surf.makeImageSnapshot().toarray()[:, :, :3].astype(int)          # BGRA -> first three are B, G, R
        b_, g_, r_ = im[:, :, 0], im[:, :, 1], im[:, :, 2]
        reds.append(float(((r_ > 140) & (g_ < 80) & (b_ < 80)).mean()))
    assert max(reds) < 0.001, reds
    out.append('red pixels %.4f %% max over 4 views (the STOP pin only)' % (100 * max(reds)))
    # Sami's torn tail, Mina's foot on the step
    m = Acting('mina', seed=9, height=400.0).place(960, 1000); m.face(1.0); m.step_up(0.0, 1, up=0.5, hold=0.5, back=0.5)
    fy0 = m.where(-1.0, 'foot_l')[1]; fy1 = m.where(0.75, 'foot_l')[1]
    assert fy0 - fy1 > 20.0, ('step_up', fy0, fy1)
    out.append('Mina\'s foot up %.0f px on the step and back' % (fy0 - fy1))
    for o_ in out: print(o_)
    print('bus self-test ok')


_selftest_doctor_full = _selftest


def _selftest():
    """python3 characters.py --selftest: the older films' checks, then the bus film's."""
    _selftest_doctor_full()
    _selftest_bus()
