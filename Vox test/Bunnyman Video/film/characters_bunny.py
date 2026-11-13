"""characters_bunny.py: the Bunnyman film's cast and staging tools ("If The Bunnyman Asks You To Close Your Eyes... DON'T
COUNT TO SEVEN"). This file is not imported on its own: characters.py runs it in its own namespace at the end of the module
(exec), so everything here is part of `characters` (import characters as CH; CH.draw(...), CH.Acting(...)) and can use
and extend every helper above (Ctx, HeadMap, Body, _ik, _tube, _draw_hand, Acting...). The older casts are unchanged.

See CAST.md for the beat map. The public API added here is listed in BUNNY_API below and in characters.py's docstring.
"""
# NOTE: runs inside characters.py's globals (math, np, skia, Ctx, HeadMap, Body, CAST, Pose, Acting, ... are defined).
import bisect as _bisect2

BUNNY_API = """
Bunnyman film additions (this film's cast takes the plain names; the dummy film's mom / delivery dad live on as
'mom_dummy' / 'dad_delivery').
  Cast ids: 'bunny' (now: matted dark grey, one ear snapped, rust-brown belly, torn, dead matte eyes), 'bunny87' (the clean
  1987 mascot with glossy eyes and a basket), 'mom' (Laurie, 43), 'mom_hosp' (the narrator in Mom's body at the hospital),
  'june' (7, pajamas), 'june_dress' (7, the yellow dress), 'narrator' (16), 'narrator_new' (the thing in the narrator's
  body), 'narrator_neat' (the same at the hospital visits), 'laurie87' (Laurie at 7, 1987), 'grandma', 'dad', 'dale'
  (Dale at 55: the face inside the suit), 'cop', 'cop2', 'doctor', 'nurse'.
"""

# ====================================================================================================== helpers
def antic(u, a=0.12, k=0.35):
    """Anticipation ease 0..1: dips back by about `a` (fraction) over the first k of the move, then eases to 1 with a soft
    landing. Use for any motion that starts with intent (reach, stand up, turn the head to a sound)."""
    u = clamp(u)
    if u < k:
        x = u / k
        return -a * math.sin(PI * x) * (1.0 - x) * 1.6
    x = (u - k) / (1.0 - k)
    return ease_in_out(x) * 1.0 + (-a * 0.0)


def settle(u, over=0.06):
    """Ease to 1 with a small overshoot and settle (for arrivals: a hand landing on a door, a head snapping round)."""
    u = clamp(u)
    return 1.0 - (1.0 - u) ** 3 + over * math.sin(PI * u) * (1.0 - u) * 2.0


def _v3(x, y, z): return np.array([float(x), float(y), float(z)])


def _unit(v):
    n = float(np.linalg.norm(v));
    return v / n if n > 1e-9 else v


def _rot_head(hm, x, y, z):
    """Head-local 3D points (x right, y down, z toward the viewer) through the head's pitch then yaw (as HeadMap.map does).
    Returns screen X, Y and depth Z (toward the camera)."""
    x = np.asarray(x, float); y = np.asarray(y, float); z = np.asarray(z, float)
    y1 = y * hm.cp + z * hm.spi
    z1 = z * hm.cp - y * hm.spi
    X = x * hm.ct + z1 * hm.st
    Z = -x * hm.st + z1 * hm.ct
    return X, y1, Z


def _fluff_ring(xs, ys, amp, n, seed=0, spiky=0.0):
    """Displace a closed outline (point arrays) along its outward normal by a soft fur fluff (amp head units, about n tufts
    round the loop). spiky 0..1 makes the tufts pointed (matted clumps)."""
    xs = np.asarray(xs, float); ys = np.asarray(ys, float)
    m = len(xs)
    cx, cy = xs.mean(), ys.mean()
    d = np.hypot(xs - cx, ys - cy) + 1e-6
    ang = np.arctan2(ys - cy, xs - cx)
    ph = np.linspace(0, 2 * PI, m, endpoint=False)
    w = 0.5 + 0.5 * np.sin(ph * n + seed * 1.37)
    w = w ** (1.0 + 3.0 * spiky)
    w = w + 0.25 * (0.5 + 0.5 * np.sin(ph * n * 2.3 + seed * 2.1))
    k = amp * w
    return xs + (xs - cx) / d * k, ys + (ys - cy) / d * k


# ====================================================================================================== the Bunnyman
# One tall man (Dale Whitlock, 1.85 m) in a mascot suit: the foam head with its ears makes him about 1.98 m to the crown
# and 2.45 m to the ear tips. Body units as everyone else (feet 0 .. crown -1000); the head is drawn by _bunny_head.
_BUNNY_FUR = dict(
    clean=dict(fur='#a7abb5', fur_sh='#7a7f8b', fur_dp='#565a66', fur_hi='#ced2da', belly='#f1efe9', belly_sh='#c9c5bc',
               pad='#f2f0ea', pad_sh='#cdc8be', inner='#eaa3b2', inner_sh='#c47c8d', nose='#e98b9f', nose_sh='#b85f74',
               teeth='#fbf8ef', teeth_sh='#d8d1c0', eye='#08090c', stitch='#3a3036', whisk='#2b2a30', sole='#e0a6b1'),
    dirty=dict(fur='#5d5f66', fur_sh='#3f4148', fur_dp='#26272d', fur_hi='#7e8189', belly='#a99f8c', belly_sh='#7f7563',
               pad='#b9b09d', pad_sh='#8d8370', inner='#a6727a', inner_sh='#7a4e57', nose='#a46a70', nose_sh='#7a4850',
               teeth='#d9c995', teeth_sh='#a8955e', eye='#050506', stitch='#231b1c', whisk='#1d1b1e', sole='#7e5f5d',
               rust='#7b3a20', rust_dk='#4e2212', mud='#3b2f24', hole='#120d0c', stuffing='#cfc6b2'))
_BUNNY_HEAD_YS = [-120, -117, -108, -86, -50, -10, 34, 66, 92, 110, 120]
_BUNNY_HEAD_WS = [0, 38, 64, 87, 98, 105, 110, 108, 96, 68, 0]


def _bunny_cast(state):
    f = _BUNNY_FUR['clean' if state == 'clean' else 'dirty']
    return dict(
        outfit='bunny', hat=None, hair=None, sex='m', hh=232.0, bunny=state, m=1.98, v3=True,
        head_ys=_BUNNY_HEAD_YS, head_ws=_BUNNY_HEAD_WS,
        eye_dx=43, eye_y=-16, eye_r=25.0, pupil=1.0, brow_th=0, nose_len=10, mouth_y=66, mouth_w=40,
        skin=f['fur'], skin_sh=f['fur_sh'], skin_dp=f['fur_dp'], blush='#e3a0aa', lip=f['nose'], stubble=None, stub=0,
        hair_c=f['fur'], brow_c=f['fur_dp'], bags=0.0, age=0.0, blink_rate=0.0, lock=0.0, micro=0.35, breath=0.55,
        scar=0, ring=0, part=0, lashes=0.0, talk=0.0, feet='bunny',
        dirt=0.0 if state == 'clean' else 1.0, ear_snap=0.0 if state == 'clean' else 1.0, shine=1.0 if state == 'clean' else 0.0,
        body=dict(sh=126, ch=142, wa=150, hip=138, arm=(76, 64), leg=(98, 78), neck=70, hand=1.34, arm_k=0.98),
        cloth=dict(f, top=f['fur'], top_sh=f['fur_sh'], top_hi=f['fur_hi'], trousers=f['fur'], trousers_sh=f['fur_sh'],
                   shoes=f['fur'], shoes_sh=f['fur_sh']))


CAST['bunny'] = _bunny_cast('dirty')
CAST['bunny87'] = _bunny_cast('clean')


class BunnyMap(HeadMap):
    """The foam mascot head: rounder in depth than a person's (the muzzle sits proud of a nearly spherical head)."""
    DF, DB = 0.84, 1.02


def _bunny_ear_pts(L=240.0, wmax=56.0, n=13):
    """Outline of one ear in its own plane: v along the ear (0 base .. 1 tip), u across (half widths). Returns the outer
    loop and the inner pink panel loop as (v, u) lists."""
    vs = np.linspace(0.0, 1.0, n)
    hw = wmax / 2 * np.sin(np.clip(vs, 0, 1) * PI * 0.92 + 0.25) ** 0.75
    hw[0] = wmax * 0.30; hw[-1] = 0.0
    outer = [(v, h) for v, h in zip(vs, hw)] + [(v, -h) for v, h in zip(vs[::-1], hw[::-1])]
    vi = np.linspace(0.12, 0.9, n)
    hi = wmax / 2 * 0.52 * np.sin((vi - 0.12) / 0.78 * PI * 0.95 + 0.12) ** 0.8
    inner = [(v, h) for v, h in zip(vi, hi)] + [(v, -h) for v, h in zip(vi[::-1], hi[::-1])]
    return outer, inner


_BEAR_OUT, _BEAR_IN = _bunny_ear_pts()


def _stub_pts():
    """The standing stump of the snapped ear (v 0..1 over its 40 %): straight sides, a ragged torn top."""
    vs = np.linspace(0.0, 1.0, 7)
    hw = np.interp(vs, [0, 1], [56 * 0.30, 56 * 0.47])
    top = [(1.0 + 0.05 * math.sin(k * 2.7), (k / 4.0 - 0.5) * 2 * 56 * 0.47) for k in range(5)]
    outer = [(v, h) for v, h in zip(vs, hw)] + [(1.0 - 0.06 * hash01(k, 13), u) for k, (_, u) in enumerate(top[::-1])] + \
            [(v, -h) for v, h in zip(vs[::-1], hw[::-1])]
    vi = np.linspace(0.3, 0.95, 5)
    inner = [(v, 9.0 + 4 * v) for v in vi] + [(v, -9.0 - 4 * v) for v in vi[::-1]]
    return outer, inner


def _flap_pts():
    """The hanging flap of the snapped ear in its own frame (v 0 at the break .. 1 at the tip, u across)."""
    vs = np.linspace(0.0, 1.0, 9)
    hw = 26.0 * np.sin(np.clip(vs, 0, 1) * PI * 0.8 + 0.6) ** 0.7
    hw[-1] = 0.0
    return [(v, h) for v, h in zip(vs, hw)] + [(v, -h) for v, h in zip(vs[::-1], hw[::-1])]


_STUB_OUT, _STUB_IN = _stub_pts()
_FLAP_OUT = _flap_pts()


def _ear_frame(hm, side, P, t, base_y=-98.0):
    """3D frame of one ear: base point, up, across and normal vectors (head-local)."""
    phi = side * 0.40
    w0 = float(hm.W(base_y))
    base = _v3(w0 * math.sin(phi), base_y, hm.DF * w0 * math.cos(phi) * 0.92)
    sway = 4.0 * P.sec_x + 2.0 * math.sin(t * 1.3 + side)
    splay = math.radians(11.0) * side + math.radians(sway * 0.6)
    up = _unit(_v3(math.sin(splay), -math.cos(splay), -0.16))
    nrm = _unit(_v3(side * 0.30, -0.05, 1.0))
    acr = _unit(np.cross(up, nrm))
    nrm = _unit(np.cross(acr, up))
    return base, up, acr, nrm


def _ear_poly(hm, base, up, acr, L, pts, v0=0.0, v1=1.0):
    """Project ear-plane points (v, u) with v remapped from 0..1 to v0..v1 of the ear length."""
    P3 = np.array([base + up * ((v0 + (v1 - v0) * v) * L) + acr * u for v, u in pts])
    return _rot_head(hm, P3[:, 0], P3[:, 1], P3[:, 2])


def _bunny_ears(c, hm, sp, P, det, t, phase):
    """Both ears. phase 'back': ears whose base is behind the dome (drawn before the head); 'front': the others. The
    character's RIGHT ear (screen left in a front view) is the snapped one when sp ear_snap > 0: it breaks 38 % up and the
    top hangs down over the side of the head, swinging with the head's motion (pose.sec_x)."""
    cl = sp['cloth']
    dirt = sp.get('dirt', 0.0)
    L = 236.0
    snap = sp.get('ear_snap', 0.0)
    for side in (-1, 1):
        base, up, acr, nrm = _ear_frame(hm, side, P, t)
        _, _, BZ = _rot_head(hm, base[0], base[1], base[2])
        is_front = float(BZ) > -18.0
        if (phase == 'front') != is_front: continue
        n_s = _rot_head(hm, nrm[0], nrm[1], nrm[2]); face = float(n_s[2])
        fur = mix(cl['fur'], '#000000', 0.06 if side > 0 else 0.0)
        broken = snap > 0.5 and side < 0
        segs = [(0.0, 1.0)] if not broken else [(0.0, 0.40)]
        for (v0, v1) in segs:
            X, Y, Z = _ear_poly(hm, base, up, acr, L, _BEAR_OUT if not broken else _STUB_OUT, 0.0, 1.0 if not broken else 0.40)
            path = _pts_path(X, Y, True, 0.8)
            c.fill(path, fur)
            c.radial(path, float(X.mean()) - 10, float(Y.min()) + 20, 160, [(0, cl['fur_hi'], 90), (0.6, fur, 0), (1, cl['fur_sh'], 160)])
            if face > 0.12:
                Xi, Yi, _ = _ear_poly(hm, base, up, acr, L, _BEAR_IN if not broken else _STUB_IN, 0.0, 1.0 if not broken else 0.40)
                inner = _pts_path(Xi, Yi, True, 0.8)
                fa = clamp((face - 0.12) / 0.3)
                c.fill(inner, cl['inner'], 255 * fa)
                c.fill(_crescent(inner, 4 * side, 3), cl['inner_sh'], 150 * fa)
            if dirt > 0.1 and det >= 1:
                with c.clip(path):
                    c.grad(path, 0, float(Y.min()), 0, float(Y.max()), [(0, cl.get('mud', '#3b2f24'), 150 * dirt), (0.5, cl['fur'], 0)])
            c.line(path, c.lw)
            if face > 0.0 and det >= 1:                               # base fold where the ear is sewn on
                Xs, Ys, _ = _ear_poly(hm, base, up, acr, L, [(0.05, -16.0), (0.07, 0.0), (0.05, 16.0)])
                c.line(_pts_path(Xs, Ys, False, 0.8), c.lw * 0.6, cl['fur_dp'], 170)
        if broken:
            # the flap hangs from the break, its fur side out, over the side of the head
            pb = base + up * (0.40 * L)
            sw = 0.07 * math.sin(t * 1.05 + 0.5) + 0.08 * P.sec_x
            hang = _unit(_v3(side * 0.36 + sw, 1.0, 0.42))
            a2 = _unit(np.cross(hang, _v3(0.0, 0.0, 1.0)))
            P3 = np.array([pb + hang * (v * L * 0.64) + a2 * u * (0.92 + 0.1 * v) for v, u in _FLAP_OUT])
            X, Y, Z = _rot_head(hm, P3[:, 0], P3[:, 1], P3[:, 2])
            flap = _pts_path(X, Y, True, 0.8)
            c.fill(flap, mix(cl['fur'], '#000000', 0.12))
            c.radial(flap, float(X.mean()) + 8 * side, float(Y.min()), 150, [(0, cl['fur_hi'], 60), (0.6, cl['fur'], 0), (1, cl['fur_dp'], 170)])
            if det >= 1:
                with c.clip(flap):
                    c.grad(flap, 0, float(Y.min()), 0, float(Y.max()), [(0, cl['fur'], 0), (1, cl.get('mud', '#3b2f24'), 190 * dirt)])
                    # a sliver of the pink lining showing along the fold
                    Pl = np.array([pb + hang * (v * L * 0.64) + a2 * (-u - 2.0) for v, u in ((0.05, 22), (0.5, 24), (0.9, 12), (0.9, 6), (0.5, 15), (0.05, 14))])
                    Xl, Yl, _ = _rot_head(hm, Pl[:, 0], Pl[:, 1], Pl[:, 2])
                    c.fill(_pts_path(Xl, Yl, True, 0.8), cl['inner_sh'], 160)
            c.line(flap, c.lw)
            # the break: a crease and frayed fabric / stuffing
            Xs, Ys, _ = _ear_poly(hm, base, up, acr, L, [(0.40, -24.0), (0.42, 0.0), (0.40, 24.0)])
            c.line(_pts_path(Xs, Ys, False, 0.8), c.lw * 1.2, cl['fur_dp'])
            if det >= 1:
                fr = []
                for k in range(6):
                    q = base + up * (0.41 * L) + acr * (-20 + 8 * k)
                    qx, qy, _ = _rot_head(hm, q[0], q[1], q[2])
                    a_ = -PI / 2 + (hash01(k, 91) - 0.5) * 2.0
                    fr.append(poly([(float(qx), float(qy)), (float(qx) + 8 * math.cos(a_), float(qy) + 8 * math.sin(a_))], False))
                c.line(_multi(fr), c.lw * 0.5, cl.get('stuffing', '#cfc6b2'), 230)

def _bunny_sil(hm, sp, det, seed=3):
    """The head outline with a soft fur fluff (clean) or matted clumps (dirty)."""
    ys = np.linspace(-120, 120, 34)
    w = hm.W(ys)
    xl, xr = hm.extent(w)
    yy = hm.J(ys) * hm.cp + hm.DF * w * hm.spi * 0.25
    xs = np.concatenate([xr, xl[::-1]]); yv = np.concatenate([yy, yy[::-1]])
    dirt = sp.get('dirt', 0.0)
    if det >= 1:
        xs, yv = _fluff_ring(xs, yv, 1.4 + 2.2 * dirt, 16 if dirt > 0.5 else 26, seed, spiky=0.75 * dirt)
    return _pts_path(xs, yv, True, 0.85)


_ELL_U = np.linspace(0, 2 * PI, 18, endpoint=False)
_ELL_V = np.linspace(0.05, PI / 2, 6)


def _ellipsoid_hull(hm, cx, cy, cz, rx, ry, rz):
    """Projected outline (convex hull) of the front half of a 3D ellipsoid on the head (head-local centre and radii)."""
    uu, vv = np.meshgrid(_ELL_U, _ELL_V)
    x = cx + rx * np.cos(uu) * np.sin(vv); y = cy + ry * np.sin(uu) * np.sin(vv); z = cz + rz * np.cos(vv) - rz * 0.35
    X, Y, Z = _rot_head(hm, x.ravel(), y.ravel(), z.ravel())
    pts = _hull(np.stack([X, Y], 1))
    return smooth(pts, True, 0.7), float(np.mean(Z))


def _bunny_muzzle(hm):
    """The two puffy muzzle pads as 3D ellipsoids: [(side, outline path, depth)]."""
    out = []
    for side in (-1, 1):
        x0, y0 = side * 22.0, 46.0
        w = float(hm.W(y0)); s_ = clamp(x0 / w, -1, 1)
        z0 = hm.DF * w * math.sqrt(1 - s_ * s_) + 2.0
        path, zm = _ellipsoid_hull(hm, x0, y0, z0 + 6.0, 28.0, 23.0, 30.0)
        out.append((side, path, zm))
    return out


def _bunny_eye(c, hm, sp, P, side, det, t):
    """A big black glass eye set in a dirty felt ring. Clean (1987): glossy, a hard highlight and a window gleam. Now:
    matte, they reflect nothing (just a dull rim so the ball still reads)."""
    cl = sp['cloth']
    ex0, ey0, r = side * sp['eye_dx'], sp['eye_y'], sp['eye_r']
    X, Y, V = hm.map1(ex0, ey0, 7.0)
    if V < 0.02: return None
    fs = hm.sx(ex0, ey0)
    rx = r * (0.40 + 0.60 * fs)
    ring = oval(X, Y + 1.0, rx * 1.2, r * 1.2)
    c.fill(oval(X, Y + 3.0, rx * 1.32, r * 1.3), cl['fur_dp'], 120)
    c.fill(ring, cl['pad']); c.fill(_crescent(ring, 2, -3), cl['pad_sh'], 170)
    c.line(ring, c.lw * 0.6)
    eye = oval(X, Y, rx, r)
    c.fill(eye, cl['eye'])
    sh = sp.get('shine', 0.0)
    ls = -1.0
    if sh > 0.01:
        c.radial(eye, X - ls * rx * 0.1, Y + r * 0.45, r * 1.05, [(0, '#3a4150', 0), (0.7, '#2a303c', 60), (1, '#5a6578', 160)], sy=1.0)
        c.fill(oval(X + ls * rx * 0.36, Y - r * 0.4, rx * 0.26, r * 0.2), '#ffffff', 235 * sh)
        c.fill(oval(X - ls * rx * 0.3, Y + r * 0.42, rx * 0.12, r * 0.08), '#ffffff', 150 * sh)
        if det >= 2:
            c.line(smooth([(X + ls * rx * 0.66, Y - r * 0.1), (X + ls * rx * 0.52, Y - r * 0.55), (X + ls * rx * 0.12, Y - r * 0.78)], False),
                   c.lw * 0.6, '#c9d6ea', 110 * sh)
    else:
        c.radial(eye, X, Y + r * 0.6, r * 0.95, [(0, '#16181d', 0), (0.78, '#121419', 20), (1, '#24272e', 110)], sy=1.0)
        if det >= 2 and sp.get('dirt', 0) > 0.5 and side < 0:       # a scuff across the dead right eye
            c.line(poly([(X - rx * 0.5, Y - r * 0.15), (X + rx * 0.3, Y + r * 0.35)], False), c.lw * 0.3, '#3a3d44', 150)
    c.line(eye, c.lw * 0.95)
    return (X, Y, r, fs)


_FUR_PTS = [(hash01(k, 301) * 2 - 1, -110 + 220 * hash01(k, 302), hash01(k, 303)) for k in range(40)]


def _fur_marks(c, hm, sp, sil, n):
    """Short fur strokes over the head surface: soft light tufts on the clean suit, dark matted clumps on the dirty one."""
    dirt = sp.get('dirt', 0.0); cl = sp['cloth']
    dk, lt_ = [], []
    for k, (u, y, r) in enumerate(_FUR_PTS[:n]):
        w = float(hm.W(y)); x = u * w * 0.85
        if -30 < y < 100 and abs(x) < 70: continue                   # keep the face clear
        X, Y, V = hm.map1(x, y, 1.0)
        if V < 0.15: continue
        fs = hm.sx(x, y); L_ = (7.0 + 6.0 * r) * (1.0 + 0.4 * dirt)
        a = PI / 2 + (u * 0.9) + (r - 0.5) * 0.8
        p = smooth([(X - 3 * fs, Y - L_ * 0.3), (X + math.cos(a) * L_ * 0.3 * fs, Y + L_ * 0.25), (X + 3 * fs, Y - L_ * 0.2)], False)
        (dk if (dirt > 0.5 or k % 3) else lt_).append(p)
    with c.clip(sil):
        if dk: c.line(_multi(dk), c.lw * (0.45 + 0.25 * dirt), cl['fur_dp'], 110 + 70 * dirt)
        if lt_: c.line(_multi(lt_), c.lw * 0.4, cl['fur_hi'], 120)


_SMILE = [(-84, 22), (-80, 34), (-66, 52), (-46, 66), (-24, 74), (0, 77), (24, 74), (46, 66), (66, 52), (80, 34), (84, 22)]


def _bunny_head(c, who, P, yaw, pitch, det, t, light=None, sp=None):
    """The Bunnyman's foam head on Ctx c (origin = head centre, head units). Long ears (one snapped when sp ear_snap), big
    black glass eyes in felt rings, a pink nose on two puffy muzzle pads, whiskers, two big flat buck teeth and a long
    stitched smile. The mask never lip-syncs: speech (pose.m_open from talk) only nods it a little (the voice is inside)."""
    sp = sp or CAST[who]
    cl = sp['cloth']
    dirt = sp.get('dirt', 0.0)
    pitch = pitch + 0.05 * clamp(P.m_open)
    hm = BunnyMap(sp, yaw, pitch, 0.0, 0.0)
    _bunny_ears(c, hm, sp, P, det, t, 'back')
    sil0 = _bunny_sil(hm, sp, det)
    face_v = hm.map1(0, 0)[2]
    pads = _bunny_muzzle(hm) if face_v > -0.3 else []
    sil = sil0
    for _, q, _ in pads: sil = union(sil, q)
    fur, fsh, fdp, fhi = cl['fur'], cl['fur_sh'], cl['fur_dp'], cl['fur_hi']
    lt = light or {}
    lsd = lt.get('side', 1)
    k_ = lt.get('key', 0.0)
    if k_ < 0: fur = mix(fur, '#58607a', -0.4 * k_); fsh = mix(fsh, '#30364a', -0.4 * k_)
    c.fill(sil, fur)
    c.radial(sil, -32.0 * lsd + hm.st * 22, -46, 172, [(0, fhi, 110), (0.45, fur, 0), (0.8, fsh, 110), (1.0, fdp, 200)], sy=1.08)
    c.fill(_crescent(sil, -lsd * 22, 8), fsh, 70)
    if det >= 1: c.texture(sil, 'fabric', 0.10, 0.5)
    if det >= 2 and dirt > 0.3: c.texture(sil, 'grunge', 0.07 * dirt, 0.9)
    if det >= 1:                                                     # fur: tufts (clean) / matted clumps (dirty)
        _fur_marks(c, hm, sp, sil0, 26 if det >= 2 else 14)
    if det >= 1:                                                     # the centre seam over the crown
        Xs, Ys, Vs = _sph(hm, np.zeros(9), np.linspace(-118, -50, 9), 0.5)
        m = Vs > 0.05
        if m.sum() > 2: c.line(_pts_path(Xs[m], Ys[m], False), c.lw * 0.45, fdp, 150)
    if dirt > 0.4 and det >= 1 and face_v > -0.6:                    # matted dark clumps
        blots = [(-70, -60, 20), (54, -84, 15), (-30, -98, 11), (84, 30, 15), (-88, 34, 17), (40, 96, 18), (-50, 100, 14)]
        bl = []
        for (x_, y_, r_) in blots:
            a_, b_, v_ = hm.map1(x_, y_, 1.0)
            if v_ > 0.1: bl.append(oval(a_, b_, r_ * hm.sx(x_, y_), r_ * 0.8))
        if bl:
            with c.clip(sil0): c.fill(_multi(bl), fdp, 85 * dirt)
    if lt.get('rim'):
        c.fill(_crescent(sil, -lsd * 8, 3), lt['rim'], lt.get('rim_a', 70))
    if lt.get('under'):
        ua = lt.get('under_a', 120)
        c.grad(sil, 0, -125, 0, 40, [(0, '#07080d', 0.5 * ua), (1, '#07080d', 0)])
        c.radial(sil, hm.st * 20, 150, 220, [(0, lt['under'], ua), (0.55, lt['under'], 0.45 * ua), (1, lt['under'], 0)], sy=0.8)
    c.line(sil0, c.lw)
    eyes = {}
    if face_v > -0.3:
        # the mouth: a dark crescent under the pads, mostly hidden by the teeth
        mo = [(-34, 58), (-18, 72), (0, 78), (18, 72), (34, 58), (18, 64), (0, 66), (-18, 64)]
        mq, mv = _fpath(hm, mo, 18.0, True, 0.85)
        if float(np.max(mv)) > 0.05: c.fill(mq, '#1d1015'); c.line(mq, c.lw * 0.7)
        # the long stitched smile from cheek to cheek
        sx_, sy_, sv_ = hm.map([p[0] for p in _SMILE], [p[1] for p in _SMILE], 4.0)
        m = sv_ > 0.0
        if m.sum() > 2:
            c.line(_pts_path(sx_[m], sy_[m], False, 0.9), c.lw * 1.35, cl['stitch'])
            if det >= 1:
                st = []
                n_ = len(_SMILE) - 1
                for u in np.linspace(0.04, 0.96, 17):
                    i = u * n_; i0 = int(i); f = i - i0
                    x0 = _SMILE[i0][0] + (_SMILE[min(i0 + 1, n_)][0] - _SMILE[i0][0]) * f
                    y0 = _SMILE[i0][1] + (_SMILE[min(i0 + 1, n_)][1] - _SMILE[i0][1]) * f
                    a_, b_, v_ = hm.map1(x0 - 2.5, y0 - 6, 4.0); a2, b2, v2 = hm.map1(x0 + 2.5, y0 + 6, 4.0)
                    if v_ > 0.0 and v2 > 0.0: st.append(poly([(a_, b_), (a2, b2)], False))
                if st: c.line(_multi(st), c.lw * 0.55, cl['stitch'], 235)
        # buck teeth (they hang from under the pads)
        for side in (-1, 1):
            x0, x1 = (1.5, 17.0) if side > 0 else (-17.0, -1.5)
            chip = (dirt > 0.5 and side > 0)
            tp = [(x0, 54), (x1, 54), (x1, 88), (x1 - 3 * side, 92), (x0 + 2 * side, 92), (x0, 88)]
            if chip: tp = [(x0, 54), (x1, 54), (x1, 80), (x1 - 5 * side, 85), (x0 + 6 * side, 84), (x0 + 2 * side, 92), (x0, 88)]
            q, V = _fpath(hm, tp, 24.0, True, 0.35)
            if float(np.max(V)) > -0.1:
                c.fill(q, cl['teeth'])
                c.fill(_crescent(q, -3 * side, -3), cl['teeth_sh'], 160)
                if dirt > 0.3:
                    c.grad(q, 0, 60, 0, 92, [(0, cl['teeth_sh'], 110 * dirt), (1, cl.get('rust', '#7b3a20'), 110 * dirt)])
                c.line(q, c.lw * 0.85)
        # muzzle pads over the top of the teeth (far pad first)
        for side, q, zm in sorted(pads, key=lambda e: e[2]):
            c.fill(q, cl['pad'])
            bb = q.getBounds()
            c.radial(q, bb.centerX() - 6 * lsd, bb.top() + 6, max(bb.width(), 30) * 0.9,
                     [(0, '#ffffff', 80), (0.55, cl['pad'], 0), (1, cl['pad_sh'], 200)], sy=0.85)
            if dirt > 0.2 and det >= 1: c.texture(q, 'grunge', 0.25 * dirt, 0.6)
            if det >= 1:
                dts = []
                for (dx_, dy_) in ((14, 40), (24, 46), (14, 52), (27, 36)):
                    a_, b_, v_ = hm.map1(side * (dx_ + 6), dy_, 34.0)
                    if v_ > 0.15: dts.append(oval(a_, b_, 2.0, 2.0))
                if dts: c.fill(_multi(dts), cl['fur_dp'], 200)
            c.line(q, c.lw * 0.9)
        if dirt > 0.3 and det >= 1:                                  # dried rust-brown dribble from the mouth corner
            dr = [(30, 64), (33, 78), (30, 92), (34, 104)]
            X_, Y_, V_ = hm.map([p[0] for p in dr], [p[1] for p in dr], 6.0)
            if V_.min() > 0.0: c.line(_pts_path(X_, Y_, False), c.lw * 1.3, cl.get('rust', '#7b3a20'), 170 * dirt)
        # nose on top of the pads
        nz = [(-18, 18), (0, 14), (18, 18), (12, 29), (0, 35), (-12, 29)]
        q, V = _fpath(hm, nz, 32.0, True, 0.7)
        if float(np.max(V)) > -0.1:
            c.fill(q, cl['nose']); c.fill(_crescent(q, 3, -4), cl['nose_sh'], 170)
            bb = q.getBounds()
            if sp.get('shine', 0) > 0.5: c.fill(oval(bb.centerX() - 4, bb.top() + 5, 5, 2.6), '#ffffff', 170)
            c.line(q, c.lw * 0.85)
        X_, Y_, V_ = hm.map([0, 0], [35, 50], 28.0)
        if V_.min() > 0.0: c.line(_pts_path(X_, Y_, False), c.lw * 0.6, cl['stitch'], 200)
        with (c.clip(sil0) if abs(hm.st) > 0.12 else _noop()):
            for side in (-1, 1):
                eyes[side] = _bunny_eye(c, hm, sp, P, side, det, t)
            if dirt > 0.4 and det >= 1:                              # a ragged tear low on the left jowl, stuffing
                hx, hy, hv = hm.map1(74, 88, 3.0)                       # bulging out (well clear of the eye: by the
                if hv > 0.15:                                            # eye ring it read as a third eye)
                    fs_ = hm.sx(74, 88)
                    hole = poly([(hx - 13 * fs_, hy - 2), (hx - 7 * fs_, hy - 6), (hx - 2 * fs_, hy - 3), (hx + 4 * fs_, hy - 7),
                                 (hx + 12 * fs_, hy - 1), (hx + 7 * fs_, hy + 4), (hx + 1 * fs_, hy + 3), (hx - 7 * fs_, hy + 5)], True)
                    c.fill(hole, cl['hole'])
                    stf = union(union(oval(hx - 5 * fs_, hy + 1.5, 4.0 * fs_, 3.0), oval(hx + 0.5 * fs_, hy + 0.5, 4.6 * fs_, 3.6)),
                                oval(hx + 6 * fs_, hy + 1.0, 3.6 * fs_, 2.8))
                    c.fill(stf, cl['stuffing'], 235); c.line(stf, c.lw * 0.35, '#8d8574', 200)
                    c.line(hole, c.lw * 0.5)
    if face_v > -0.3:                                               # whiskers over the outline (dirty: bent, one broken)
        wk = []
        for side in (-1, 1):
            for j, (y0, y1) in enumerate(((40, 24), (46, 46), (52, 68))):
                x0 = side * 44
                pts = [(x0, y0), (side * 84, (y0 + y1) / 2 + 2), (side * 132, y1)]
                if dirt > 0.5:
                    kk = hash01(j + 3 * (side + 1), 17)
                    pts = [(x0, y0), (side * (72 + 10 * kk), (y0 + y1) / 2 + 6), (side * (100 + 12 * kk), y1 + 20 * (kk - 0.3))]
                    if j == 1 and side < 0: pts = pts[:2]
                X_, Y_, V_ = hm.map([p[0] for p in pts], [p[1] for p in pts], np.array([24.0, 14.0, 6.0][:len(pts)]))
                if V_[0] > 0.12: wk.append(_pts_path(X_, Y_, False, 0.6 if dirt > 0.5 else 1.0))
        if wk: c.line(_multi(wk), c.lw * 0.42, cl['whisk'], 235)
    _bunny_ears(c, hm, sp, P, det, t, 'front')
    return hm


# ====================================================================================================== dispatch hooks
_draw_head_local_v2 = draw_head_local


def draw_head_local(c, who, P, yaw, pitch, det, t, light=None, sp=None):
    """Head in head units on Ctx c (see the v2 version). The Bunnyman's foam head and the v3 cast's faces dispatch here."""
    sp = sp or CAST[who]
    if sp.get('bunny'): return _bunny_head(c, who, P, yaw, pitch, det, t, light, sp)
    return _draw_head_local_v2(c, who, P, yaw, pitch, det, t, light, sp)


# ====================================================================================================== v3 body rig
# New pose fields (all 0 by default, so older casts are unchanged):
#   seat     body units above the floor of the seat a sitting figure's hips rest on (with sit > 0); 0 = the old sit (hips
#            dropped 170). draw() keeps y_feet = the FLOOR: the feet stay on the floor whatever the seat height.
#   knees    kneel style for pose.kneel: 0 = one knee down (the character's left knee up, foot forward), 1 = both knees down
#            (upright), 2 = both knees down sitting back on the heels.
#   run      0..1 turns the walk cycle into a run (longer stride, flight phase, forward lean, bent pumping arms).
POSE_DEFAULTS.update(seat=0.0, knees=0.0, run=0.0, unmask=0.0, hum=0.0, scratch=0.0, mess=0.0, head_off=0.0)
_THIGH, _SHIN = 206.0, 180.0


class Body3(Body):
    """Body with a seat anchor, two kneeling styles and (v3 cast) a walk whose stance foot is planted (it moves back at the
    body's speed instead of on a cosine, so feet do not slide)."""

    def __init__(self, sp, P):
        _Body_v2.__init__(self, sp, P)
        self.v3 = bool(sp.get('v3'))
        seat = float(getattr(P, 'seat', 0.0) or 0.0)
        kn = self.kneel
        knees = float(getattr(P, 'knees', 0.0) or 0.0)
        self.knees = knees
        self.runk = clamp(getattr(P, 'run', 0.0)) * self.walk
        if self.v3 or seat > 0 or (kn > 0 and knees > 0):
            hd = 0.0
            if self.sit > 0 and seat > 0 and self.floor < 0.5:
                hd += (422.0 - (seat + 40.0)) * self.sit
            else:
                hd += 170.0 * self.sit * (1.0 - self.floor)
            hd += 330.0 * self.floor + P.crouch * 120 - 34.0 * self.tip
            if kn > 0:
                # hip height when kneeling: one knee ~ shin + 40, upright on both knees ~ thigh + 30, on the heels ~ 150
                hk = 236.0 if knees < 1.5 else lerp(236.0, 150.0, clamp(knees - 1.0))
                hd += (422.0 - hk) * kn
            self.hip_drop = hd
            drop = 0.0
            if self.walk > 0:
                for sd in (-1, 1):
                    f = self.foot_fwd(sd)
                    if self.foot_lift(sd) < 1: drop = max(drop, math.sqrt(384.0 ** 2 + f * f) - 384.0)
            run_bob = 22.0 * self.runk * max(0.0, math.sin(2 * self.ph))
            self.bob = P.bob + drop * (1.0 - 0.6 * self.runk) + 5.0 * self.walk * math.cos(2 * self.ph) - run_bob + self.hip_drop
            if self.runk > 0: self.stride = 230.0 * self.walk * (1.0 + 0.7 * self.runk)

    def _stance(self, side):
        """(phase in 0..1 of this leg's cycle, in stance?) for the v3 walk: 60 % stance (run: 40 %)."""
        ph = ((self.leg_phase(side) / (2 * PI)) % 1.0)
        return ph, ph < (0.6 - 0.2 * self.runk)

    def foot_fwd(self, side):
        if not getattr(self, 'v3', False): return _Body_v2.foot_fwd(self, side)
        ph, st = self._stance(side)
        sf = 0.6 - 0.2 * self.runk
        S = self.stride
        if st:                                      # planted: moves back linearly from +S/2 to -S/2
            return S / 2 - S * (ph / sf)
        u = (ph - sf) / (1 - sf)                    # swing: eases forward from -S/2 to +S/2
        return -S / 2 + S * ease_in_out(u)

    def foot_lift(self, side):
        if not getattr(self, 'v3', False): return _Body_v2.foot_lift(self, side)
        ph, st = self._stance(side)
        if st: return 0.0
        sf = 0.6 - 0.2 * self.runk
        u = (ph - sf) / (1 - sf)
        return math.sin(PI * u) ** 0.8 * (62.0 + 70.0 * self.runk) * self.walk


_Body_v2 = Body
Body = Body3


def _foot_box(kind):
    """3D foot box in foot coords (x across, y up = negative, z forward from the ankle): (points, sole y)."""
    if kind == 'bunny':      # long plush rabbit feet with round toes
        return [(-34, 0, -30), (34, 0, -30), (-38, 0, 60), (38, 0, 60), (-30, 0, 118), (30, 0, 118), (0, 0, 128),
                (-30, -46, -26), (30, -46, -26), (-32, -40, 60), (32, -40, 60), (-24, -30, 108), (24, -30, 108)]
    if kind == 'maryjane':
        return [(-19, 0, -20), (19, 0, -20), (-21, 0, 52), (21, 0, 52), (-15, 0, 66), (15, 0, 66),
                (-17, -22, -18), (17, -22, -18), (-19, -16, 44), (19, -16, 44)]
    if kind == 'flats':
        return [(-19, 0, -20), (19, 0, -20), (-21, 0, 54), (21, 0, 54), (-14, 0, 70), (14, 0, 70),
                (-17, -20, -18), (17, -20, -18), (-18, -12, 48), (18, -12, 48)]
    if kind == 'socks':
        return [(-19, 0, -20), (19, 0, -20), (-21, 0, 54), (21, 0, 54), (-15, 0, 66), (15, 0, 66),
                (-18, -30, -18), (18, -30, -18), (-19, -16, 46), (19, -16, 46)]
    if kind == 'boots':
        return [(-23, 0, -24), (23, 0, -24), (-25, 0, 60), (25, 0, 60), (-19, 0, 74), (19, 0, 74),
                (-22, -48, -22), (22, -48, -22), (-23, -26, 52), (23, -26, 52)]
    if kind == 'clogs':
        return [(-22, 0, -22), (22, 0, -22), (-24, 0, 58), (24, 0, 58), (-18, 0, 72), (18, 0, 72),
                (-21, -30, -20), (21, -30, -20), (-22, -24, 50), (22, -24, 50)]
    return [(-22, 0, -24), (22, 0, -24), (-24, 0, 58), (24, 0, 58), (-18, 0, 72), (18, 0, 72),
            (-21, -26, -22), (21, -26, -22), (-22, -20, 50), (22, -20, 50)]


def _leg_chain(sp, B, P, side):
    """3D hip, knee, ankle (body units, upright frame) and the foot pitch (rad, 0 = flat, + = toes down) of one leg for the
    v3 rig: standing / walking / running, seated on pose.seat, one-knee or two-knee kneels, floor sitting."""
    b = sp['body']
    hipx = side * b['hip'] * 0.46
    H = _v3(hipx, B.y_hip + 8 + B.bob, 0.0)
    kn = B.kneel; knees = B.knees
    fl = B.floor
    pitch = 0.0
    fwd = B.foot_fwd(side) + fl * (262.0 + 22.0 * side)
    lift = B.foot_lift(side)
    seat = float(getattr(P, 'seat', 0.0) or 0.0)
    if B.sit > 0:
        # seated: ankles forward under the knees (feet flat on the floor); a low seat lifts the knees
        hy = -(H[1])                                        # hip height above the floor
        tf = math.sqrt(max(_THIGH ** 2 - max(0.0, hy - 38.0 - _SHIN) ** 2, 0.0)) if seat > 0 else 210.0
        fwd += min(tf, 200.0) * B.sit * (1.0 - fl)
    A = _v3(side * (b['hip'] * 0.46 + 6 + 30 * P.stance + 24 * fl), -38.0 - lift - 34.0 * B.tip, fwd)
    pole = _v3(0.08 * side + 0.3 * side * fl, -0.15 - 0.85 * fl, 1.0)
    if kn > 0.01:
        up_leg = side > 0 and knees < 0.5               # one-knee kneel: the character's left knee stays up
        if up_leg:
            Ak = _v3(A[0], -38.0, 150.0)
            A = A + (Ak - A) * kn
            K, A = _ik(H, A, _THIGH, _SHIN, pole)
            return H, K, A, 0.0
        # knee on the floor: the knee goes down and a little forward, the shin lies back along the floor; on the way down
        # the foot stays on the floor (it slides back onto its toes) while the knee bends down to meet the floor
        Kk = _v3(hipx * 1.05, -30.0, 30.0 if knees < 1.5 else 70.0)
        Af = Kk + _v3(0.0, -8.0, -_SHIN)
        A = A + (Af - A) * kn
        A[1] = -38.0 - lift
        Ks, _ = _ik(H, A, _THIGH, _SHIN, _v3(0.08 * side, 0.35, 1.0))
        K = Ks + (Kk - Ks) * (kn ** 2)
        pitch = 1.25 * kn                               # toes down behind
        return H, K, A, pitch
    K, A = _ik(H, A, _THIGH, _SHIN, pole)
    if lift > 1.0:
        pitch = -0.35 * math.sin(PI * clamp(lift / (62.0 + 70.0 * B.runk))) if B.foot_fwd(side) > 0 else 0.5 * clamp(lift / 60.0)
    return H, K, A, pitch


def _draw_legs3(c, sp, B, P, det, t, legc, legsh, shoec, order_only=False):
    """v3 legs: tube through hip-knee-ankle, foot boxes (shoes, socks, plush rabbit feet) pitched for walking / kneeling."""
    b = sp['body']
    kind = sp.get('feet', 'shoes')
    cl = sp['cloth']
    legs = []
    for side in (-1, 1):
        H, K, A, pitch = _leg_chain(sp, B, P, side)
        h2 = B.p3(H[0], H[1] - B.bob, H[2], upper=False); k2 = B.p3(K[0], K[1] - B.bob, K[2], upper=False)
        a2 = B.p3(A[0], A[1] - B.bob, A[2], upper=False)
        legs.append((h2, k2, a2, side, A, pitch))
    legs.sort(key=lambda o: o[0][3] + o[2][3])
    lw0, lw1 = b['leg']
    for hp, kp, ap, side, A, pitch in legs:
        P2 = [(hp[0], hp[1]), (kp[0], kp[1]), (ap[0], ap[1])]
        widths = [lw0 * hp[2], (lw0 + lw1) / 2 * kp[2], lw1 * ap[2]]
        tp = _tube(P2, widths)
        # foot
        pts = []
        cp, spp = math.cos(pitch), math.sin(pitch)
        for (fx, fy, fz) in _foot_box(kind):
            yy = fy * cp - fz * spp; zz = fz * cp + fy * spp
            X, Y, s_, Z = B.p3(A[0] + fx * (1.0 + 0.0 * side), A[1] + 38.0 + yy - B.bob, A[2] + zz, upper=False)
            pts.append((X, Y))
        foot = smooth(_hull(pts), True, 0.6)
        # the foot behind the leg when it points away (back view / kneeling: toes behind)
        foot_back = (B.ct * math.cos(pitch) < -0.1)
        if foot_back: _foot_fill(c, sp, kind, foot, cl, det, P, B, side)
        if sp.get('outfit') == 'bunny':
            _bunny_limb(c, sp, tp, P2, widths, det, 'leg')
        else:
            c.fill(tp, legc); _cloth_shade(c, tp, legsh, 160, 1.0, 10)
            if det >= 1 and sp.get('legs_tex', True): c.texture(tp, 'fabric', 0.08, 0.6)
            _leg_extra(c, sp, P2, widths, det, side, B)
            c.line(tp, c.lw)
        if not foot_back: _foot_fill(c, sp, kind, foot, cl, det, P, B, side)


def _leg_extra(c, sp, P2, widths, det, side, B):
    """Per-outfit leg details (socks bands over bare legs, knee creases)."""
    if det >= 1:
        c.line(smooth([((P2[0][0] + P2[1][0]) / 2, (P2[0][1] + P2[1][1]) / 2), P2[1],
                       ((P2[1][0] + P2[2][0]) / 2, (P2[1][1] + P2[2][1]) / 2 + 10)], False), c.lw * 0.32, LINE, 110)


def _foot_fill(c, sp, kind, foot, cl, det, P, B, side):
    bb = foot.getBounds()
    if kind == 'bunny':
        fur = cl['fur']
        c.fill(foot, fur); c.fill(_crescent(foot, 0, -7), cl['fur_sh'], 150)
        dirt = sp.get('dirt', 0.0)
        if dirt > 0.2: c.grad(foot, 0, bb.top(), 0, bb.bottom(), [(0, cl.get('mud', '#3b2f24'), 0), (1, cl.get('mud', '#3b2f24'), 220 * dirt)])
        if det >= 1:                                           # three toe grooves at the front
            tx = bb.centerX(); w_ = bb.width()
            front = B.ct >= -0.2
            if front and abs(B.st) < 0.85:
                c.line(_multi([poly([(tx + k * w_ * 0.16, bb.bottom() - 4), (tx + k * w_ * 0.13, bb.bottom() - bb.height() * 0.42)], False)
                               for k in (-1, 1)]), c.lw * 0.45, cl['fur_dp'], 200)
        c.line(foot, c.lw)
        return
    if kind in ('socks',):
        sc = cl.get('socks', '#c9c6c0'); ssh = cl.get('socks_sh', mix(sc, '#000000', 0.3))
        c.fill(foot, sc); c.fill(_crescent(foot, 6, -4), ssh, 150)
        if det >= 1: c.texture(foot, 'fabric', 0.18, 0.5)
        if cl.get('sock_toe'):
            with c.clip(foot): c.fill(rect(bb.left() - 4, bb.bottom() - bb.height() * 0.3, bb.width() + 8, bb.height()), cl['sock_toe'], 220)
        c.line(foot, c.lw)
        return
    sc = shoe = cl.get('shoes', '#2a2420'); ssh = cl.get('shoes_sh', mix(sc, '#000000', 0.35))
    c.fill(foot, sc); c.fill(_crescent(foot, 6, -5), ssh, 160)
    if kind == 'maryjane':
        c.glow(bb.centerX() - bb.width() * 0.2, bb.top() + bb.height() * 0.3, bb.width() * 0.28, bb.height() * 0.14, '#ffffff', 90)
        if det >= 1 and B.ct > -0.2:
            c.line(poly([(bb.left() + 3, bb.top() + bb.height() * 0.35), (bb.right() - 3, bb.top() + bb.height() * 0.3)], False), c.lw * 0.9, mix(sc, '#000000', 0.5))
            c.fill(oval(bb.centerX() + side * bb.width() * 0.28, bb.top() + bb.height() * 0.33, 2.6, 2.6), '#d8d2c4')
    elif kind == 'flats':
        c.glow(bb.centerX() - bb.width() * 0.2, bb.top() + bb.height() * 0.4, bb.width() * 0.3, bb.height() * 0.12, '#ffffff', 50)
    elif kind == 'boots':
        c.fill(rect(bb.left() - 2, bb.bottom() - 8, bb.width() + 4, 8), mix(sc, '#000000', 0.45))
    elif kind == 'clogs':
        c.line(_crescent(foot, 0, -6), c.lw * 0.5, mix(sc, '#000000', 0.25), 200)
    else:
        if cl.get('sole'): c.fill(rect(bb.left() - 2, bb.bottom() - 8, bb.width() + 4, 8), cl['sole'])
        c.glow(bb.centerX() - bb.width() * 0.18, bb.top() + bb.height() * 0.32, bb.width() * 0.3, bb.height() * 0.13, '#ffffff', 40)
    c.line(foot, c.lw)


# ====================================================================================================== the suit's body
def _bunny_limb(c, sp, tp, P2, widths, det, kind):
    """A plush limb: fur fill, soft shade, a fluffy edge, grime toward the end (dirty suit)."""
    cl = sp['cloth']; dirt = sp.get('dirt', 0.0)
    c.fill(tp, cl['fur'])
    _cloth_shade(c, tp, cl['fur_sh'], 150, 1.0, 12)
    if det >= 1:
        c.texture(tp, 'fabric', 0.10, 0.5)
        if dirt > 0.2:
            (x0, y0), (x1, y1) = P2[0], P2[-1]
            c.grad(tp, x0, y0, x1, y1, [(0, cl.get('mud', '#3b2f24'), 0), (0.55, cl.get('mud', '#3b2f24'), 40 * dirt),
                                        (1, cl.get('mud', '#3b2f24'), 150 * dirt)])
            c.texture(tp, 'grunge', 0.10 * dirt, 0.8)
        # fur tufts along the outline
        tu = []
        for i in range(len(P2) - 1):
            (ax, ay), (bx, by) = P2[i], P2[i + 1]
            L = math.hypot(bx - ax, by - ay) or 1.0
            nx, ny = -(by - ay) / L, (bx - ax) / L
            for k in range(3):
                u = (k + 0.5) / 3.0
                w = (widths[i] + (widths[i + 1] - widths[i]) * u) / 2
                for sd in (-1, 1):
                    px, py = ax + (bx - ax) * u + sd * nx * w, ay + (by - ay) * u + sd * ny * w
                    tu.append(poly([(px - sd * nx * 5, py - sd * ny * 5), (px + sd * nx * 2 + (bx - ax) / L * 5, py + sd * ny * 2 + (by - ay) / L * 5)], False))
        c.line(_multi(tu), c.lw * 0.45, cl['fur_dp'], 120 + 60 * dirt)
    c.line(tp, c.lw)


def _paw_geom(shape, side):
    """Paw outline + grooves in hand coords (wrist (0, 0), fingers toward +y, thumb toward -side * x)."""
    th = -side
    if shape in ('paw_open', 'paw_wave'):
        body = smooth([(-24, 0), (24, 0), (29, 26), (26, 44), (-26, 44), (-29, 26)], True, 0.7)
        u = body
        for k, (x, ln) in enumerate(((-15, 22), (-5, 27), (5, 27), (15, 22))):
            u = union(u, rrect(x + th * 0 - 6.5, 30, 13, ln + 12, 6.5))
        u = union(u, smooth([(th * 18, 8), (th * 40, 18), (th * 38, 30), (th * 22, 26)], True, 0.8))
        grooves = [poly([(x, 46), (x, 58)], False) for x in (-10, 0, 10)]
        return u, grooves, oval(0, 22, 14, 11)
    if shape == 'paw_point':
        blk = smooth([(-24, 0), (24, 0), (28, 24), (24, 48), (0, 54), (-24, 48), (-28, 24)], True, 0.75)
        fin = rrect(th * 12 - 7, 34, 14, 46, 7)
        u = union(blk, fin)
        return u, [poly([(x, 40), (x, 50)], False) for x in (-th * 4, -th * 13)], oval(0, 20, 13, 10)
    if shape == 'paw_grip':
        blk = smooth([(-24, -2), (24, -2), (28, 20), (25, 42), (-25, 42), (-28, 20)], True, 0.75)
        return blk, [poly([(-22, 18 + 8 * k), (22, 18 + 8 * k)], False) for k in range(3)], None
    if shape == 'paw_flat':
        u = smooth([(-25, 0), (25, 0), (30, 30), (26, 58), (12, 70), (-12, 70), (-26, 58), (-30, 30)], True, 0.75)
        u = union(u, smooth([(th * 20, 8), (th * 40, 20), (th * 36, 34), (th * 20, 28)], True, 0.8))
        return u, [], 'pads'
    # relaxed paw: a soft mitten, three finger grooves at the end
    u = smooth([(-23, 0), (23, 0), (27, 26), (25, 50), (14, 64), (0, 67), (-14, 64), (-25, 50), (-27, 26)], True, 0.75)
    u = union(u, smooth([(th * 18, 10), (th * 33, 22), (th * 30, 36), (th * 18, 32)], True, 0.8))
    return u, [poly([(x, 50), (x * 1.1, 64)], False) for x in (-9, 0, 9)], None


def _draw_paw(c, sp, shape, x, y, scale, angle, side, det):
    cl = sp['cloth']; dirt = sp.get('dirt', 0.0)
    hc = c.sub(x, y, angle, scale * sp['body'].get('hand', 1.0))
    u, grooves, pad = _paw_geom(shape if shape and shape.startswith('paw') else 'paw', side)
    hc.fill(u, cl['fur'])
    hc.fill(_crescent(u, -5, -3), cl['fur_sh'], 160)
    if dirt > 0.2:
        bb = u.getBounds()
        hc.grad(u, 0, bb.top(), 0, bb.bottom(), [(0, cl.get('mud', '#3b2f24'), 50 * dirt), (1, cl.get('mud', '#3b2f24'), 190 * dirt)])
    if pad == 'pads':                                  # the palm: a big pink pad and four toe pads
        pc = cl['inner'] if dirt < 0.5 else mix(cl['inner'], '#5a4040', 0.45)
        hc.shape(oval(0, 26, 15, 12), pc, hc.lw * 0.45)
        for k, (px, py) in enumerate(((-15, 50), (-5, 57), (6, 57), (16, 50))):
            hc.shape(oval(px, py, 5.5, 6.5), pc, hc.lw * 0.35)
    if det >= 1 and grooves: hc.line(_multi(grooves), hc.lw * 0.55, cl['fur_dp'], 210)
    hc.line(u, hc.lw * 0.95)


def _bunny_rows(sp, B):
    """Rows of the round plush body: sloped shoulders, a full round belly, tapering into the crotch."""
    b = sp['body']; k = B.chest_k
    ys = [B.y_sh - 44, B.y_sh - 22, B.y_sh + 4, B.y_sh + 40, B.y_ch + 30, B.y_ch + 100, B.y_wa + 10, B.y_belt + 10, B.y_hip,
          B.y_cr + 14]
    ws = [b['neck'] + 26, b['sh'] * 0.70, b['sh'] * 0.94, b['ch'] * 0.98 * k, b['ch'] * 1.06 * k, b['wa'] * 1.10, b['wa'] * 1.11,
          b['hip'] * 1.06, b['hip'] * 0.96, b['hip'] * 0.66]
    ds = [w * f for w, f in zip(ws, [0.62, 0.64, 0.68, 0.76, 0.84, 0.9, 0.9, 0.86, 0.8, 0.62])]
    return ys, ws, ds


def _blob(cx, cy, rx, ry, n=11, seed=0, rough=0.35):
    """An irregular soft blob (stains, matted patches) as a closed smooth path."""
    pts = []
    for k in range(n):
        a = 2 * PI * k / n
        r = 1.0 + rough * (hash01(k + seed * 31 + 7, 211) - 0.5) * 2.0
        pts.append((cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r))
    return smooth(pts, True, 0.85)


def _rip(cx, cy, w, h, ang, seed=0):
    """A torn rip in the suit: a jagged almond slit (points)."""
    pts = []
    n = 14
    for k in range(n):
        a = 2 * PI * k / n
        jag = 1.0 + (0.45 if k % 2 else -0.1) * hash01(k + seed * 17, 233)
        ux, uy = math.cos(a) * w * 0.5 * jag, math.sin(a) * h * 0.5 * (0.6 + 0.4 * jag)
        pts.append((cx + ux * math.cos(ang) - uy * math.sin(ang), cy + ux * math.sin(ang) + uy * math.cos(ang)))
    return pts


def _bunny_belly(c, sp, B, rows, P, det, t):
    """The white belly panel (front), and on the dirty suit: the rust-brown stain soaked into it with a dried tide line and
    runs, torn rips with stuffing bulging out, and dark matted patches over the fur."""
    cl = sp['cloth']; dirt = sp.get('dirt', 0.0); b = sp['body']
    yt, yb = B.y_ch - 10, B.y_cr + 2
    pts = []
    for a in np.linspace(0, 2 * PI, 30, endpoint=False):
        x0 = math.sin(a) * b['ch'] * 0.66 * (1.0 - 0.12 * max(0.0, -math.cos(a)))
        y0 = (yt + yb) / 2 - math.cos(a) * (yb - yt) / 2
        pts.append((x0, y0))
    vis = [B.surf(x0, y0, 2, False, rows)[2] for x0, y0 in pts]
    if max(vis) < 0.05: return
    pp = [B.surf(x0, y0, 2, False, rows)[:2] for x0, y0 in pts]
    belly = smooth(pp, True, 0.9)
    c.fill(belly, cl['belly'])
    bb = belly.getBounds()
    c.radial(belly, bb.centerX() - bb.width() * 0.2, bb.top() + bb.height() * 0.3, bb.height() * 0.7,
             [(0, '#ffffff', 60), (0.5, cl['belly'], 0), (1, cl['belly_sh'], 210)], sy=1.0)
    if det >= 1: c.texture(belly, 'fabric', 0.12, 0.5)
    if dirt > 0.2:
        with c.clip(belly):
            c.texture(belly, 'grunge', 0.22 * dirt, 0.7)
            # one big soaked stain spreading from the upper belly, darkest at its heart, a dried tide line at the edge
            X, Y, vv, s_ = B.surf(-0.08 * b['ch'], yt + (yb - yt) * 0.42, 3, False, rows)
            fx = max(0.35, abs(B.ct))
            stain = _blob(X, Y, 86 * s_ * fx, 104 * s_, 13, 3, 0.55)
            c.radial(stain, X + 10 * s_, Y - 20 * s_, 130 * s_, [(0, cl['rust_dk'], 235 * dirt), (0.5, cl['rust'], 210 * dirt),
                                                             (0.85, cl['rust'], 130 * dirt), (1, cl['rust'], 70 * dirt)], sy=1.15)
            c.line(stain, c.lw * 1.2, cl['rust_dk'], 120 * dirt)
            sec = _blob(X + 70 * s_ * fx, Y + 130 * s_, 34 * s_ * fx, 40 * s_, 9, 5, 0.5)
            c.fill(sec, cl['rust'], 150 * dirt); c.line(sec, c.lw * 0.8, cl['rust_dk'], 90 * dirt)
            runs, drops = [], []
            for k in range(6):
                x0 = X + (-60 + 24 * k) * s_ * fx
                y0 = Y + (70 + 25 * hash01(k, 41)) * s_
                ln = (50 + 90 * hash01(k, 43)) * s_
                runs.append(smooth([(x0, y0), (x0 + 3 * s_, y0 + ln * 0.5), (x0 + 1 * s_, y0 + ln)], False))
                drops.append(oval(x0 + 1 * s_, y0 + ln + 4 * s_, 5 * s_, 6 * s_))
            c.line(_multi(runs), c.lw * 1.5, cl['rust'], 190 * dirt)
            c.fill(_multi(drops), cl['rust_dk'], 180 * dirt)
            sp_ = [oval(X + (hash01(k, 61) - 0.5) * 300 * s_ * fx, Y + (hash01(k, 62) - 0.6) * 300 * s_, (2 + 4 * hash01(k, 63)) * s_)
                   for k in range(14)]
            c.fill(_multi(sp_), cl['rust_dk'], 150 * dirt)
    c.line(belly, c.lw * 0.9)
    if dirt > 0.4:
        for (x0, y0, w0, h0, rot, sd) in ((-0.30, 0.22, 26, 70, 0.5, 1), (0.36, 0.70, 30, 40, -0.4, 2)):
            X, Y, vv, s_ = B.surf(x0 * b['ch'], yt + (yb - yt) * y0, 3, False, rows)
            if vv < 0.25: continue
            fx = max(0.4, abs(B.ct))
            rp = _rip(X, Y, w0 * s_ * fx, h0 * s_, rot, sd)
            hole = poly(rp, True)
            c.fill(hole, cl['hole'])
            if det >= 1:
                # stuffing bulging from the lower lip of the rip, frayed threads round the edge
                k0 = len(rp) // 4
                st = _blob(rp[k0][0] - 4 * s_, rp[k0][1], 13 * s_ * fx, 10 * s_, 7, sd + 9, 0.3)
                c.fill(st, cl['stuffing']); c.fill(_crescent(st, 3, -3), '#9e9684', 150); c.line(st, c.lw * 0.45)
                fr = [poly([(px, py), (px + (px - X) * 0.35 + 2, py + (py - Y) * 0.2)], False) for px, py in rp[::2]]
                c.line(_multi(fr), c.lw * 0.45, cl['belly_sh'], 230)
            c.line(hole, c.lw * 0.55, cl['fur_dp'])


def _bunny_matting(c, sp, B, rows, det, back=False):
    """Dark matted, wet-looking clumps of fur over the body (dirty suit)."""
    cl = sp['cloth']; b = sp['body']
    ys_, ws_, ds_ = rows
    bl = []
    for k in range(9):
        u = (hash01(k, 71) * 2 - 1) * 0.85
        y0 = ys_[1] + (ys_[-1] - ys_[1]) * hash01(k, 72)
        w = float(np.interp(y0, ys_, ws_))
        X, Y, vv, s_ = B.surf(u * w, y0, 2, back, rows)
        if vv < 0.15: continue
        bl.append(_blob(X, Y, (26 + 30 * hash01(k, 73)) * s_ * max(0.4, abs(B.ct) if not back else 1.0), (22 + 26 * hash01(k, 74)) * s_, 8, k, 0.5))
    if bl: c.fill(_multi(bl), cl['fur_dp'], 95)


def _bunny_figure(c, who, P, det, t, light=None, upper_only=False):
    """The Bunnyman's whole body in body units on Ctx c (feet at y=0): plush legs and long rabbit feet, a round suit body
    with the white belly panel, a ruff collar under the foam head, thick arms ending in paws (pose hand shapes 'paw',
    'paw_open' (wave), 'paw_point', 'paw_grip' (holding a prop), 'paw_flat' (pads to camera)), a cotton tail and the back
    zipper. The dirty suit adds mud, grime, the rust-brown belly stain and torn holes."""
    sp = CAST[who]
    B = Body(sp, P)
    cl = sp['cloth']
    dirt = sp.get('dirt', 0.0)
    rows = _bunny_rows(sp, B)
    arm_z = {}
    for side in (-1, 1):
        S, E, Wr = _arm_data(sp, B, P, side)
        arm_z[side] = (B.p3(*S)[3], B.p3(*Wr)[3])
    behind = [s_ for s_ in (-1, 1) if arm_z[s_][0] < -20 and arm_z[s_][1] < 40]
    front = sorted([s_ for s_ in (-1, 1) if s_ not in behind], key=lambda s_: arm_z[s_][1])
    back_view = B.ct < -0.15
    tail_front = B.ct < -0.3
    for side in behind: _bunny_arm(c, sp, B, P, side, det, t, light)
    if not tail_front and not upper_only: _bunny_tail(c, sp, B, rows, det)
    if not upper_only: _draw_legs3(c, sp, B, P, det, t, cl['fur'], cl['fur_sh'], cl['fur'])
    torso, L, R = _torso_path(B, rows)
    if det >= 1:
        bb = torso.getBounds()
        # fluffy outline
        ys_, ws_, ds_ = rows
        Lp, Rp = B.rows(ys_, ws_, ds_)
        xs = np.array([p[0] for p in Rp] + [p[0] for p in Lp[::-1]]); yv = np.array([p[1] for p in Rp] + [p[1] for p in Lp[::-1]])
        xs, yv = _densify_xy(xs, yv, 3)
        xs, yv = _fluff_ring(xs, yv, 3.0 + 3.0 * dirt, 30, 5, spiky=0.6 * dirt)
        torso = _pts_path(xs, yv, True, 0.85)
    c.fill(torso, cl['fur'])
    lsd = (light or {}).get('side', 1)
    c.grad(torso, L[3][0] - 10, 0, R[3][0] + 10, 0, [(0, cl['fur_hi'], 80), (0.35, cl['fur'], 0), (0.72, cl['fur_sh'], 70), (1, cl['fur_sh'], 210)])
    with c.clip(torso):
        c.grad(rect(-500, B.y_wa - 10 + B.bob, 1000, 600), 0, B.y_wa + B.bob, 0, B.y_cr + B.bob, [(0, cl['fur_sh'], 0), (1, cl['fur_sh'], 150)])
        if det >= 1: c.texture(torso, 'fabric', 0.12, 0.55)
        if dirt > 0.2:
            c.texture(torso, 'grunge', 0.16 * dirt, 0.8)
            c.grad(rect(-500, B.y_belt + B.bob, 1000, 600), 0, B.y_belt + B.bob, 0, B.y_cr + 40 + B.bob,
                   [(0, cl['mud'], 0), (1, cl['mud'], 120 * dirt)])
        if dirt > 0.4 and det >= 1: _bunny_matting(c, sp, B, rows, det, back_view)
        if light and light.get('rim'):
            c.fill(_crescent(torso, -lsd * 10, 0), light['rim'], light.get('rim_a', 70) * 0.8)
    c.line(torso, c.lw)
    if not back_view: _bunny_belly(c, sp, B, rows, P, det, t)
    else: _bunny_zipper(c, sp, B, rows, det)
    if tail_front and not upper_only: _bunny_tail(c, sp, B, rows, det)
    # ruff collar where the foam head sits on the suit
    nb = B.p3(0, B.y_sh - 30, 0)
    rw = (sp['body']['neck'] + 52) * nb[2]
    ruff_pts = [(nb[0] + math.cos(a) * rw * math.sqrt((B.ct) ** 2 + (0.85 * B.st) ** 2), nb[1] + 12 + math.sin(a) * 34) for a in np.linspace(0, 2 * PI, 30, endpoint=False)]
    rx_, ry_ = _fluff_ring(np.array([p[0] for p in ruff_pts]), np.array([p[1] for p in ruff_pts]), 6.0 + 3.0 * dirt, 15, 2, spiky=0.6)
    ruff = _pts_path(rx_, ry_, True, 0.9)
    c.fill(ruff, mix(cl['fur'], cl['fur_hi'], 0.25)); c.fill(_crescent(ruff, 0, -8), cl['fur_sh'], 140); c.line(ruff, c.lw * 0.9)
    # head (the foam head is not driven by the jaw / mouth)
    pv = B.p3(0, B.yc - 22 + P.h_dy, 0)
    hs = sp['hh'] / 240.0 * pv[2] * P.h_scale
    head_rot = P.tilt + P.h_tilt
    arm_ = (sp['hh'] / 2 - 30) * pv[2] * P.h_scale
    ra = math.radians(head_rot)
    hx = pv[0] + P.h_dx + math.sin(ra) * arm_
    hy = pv[1] - math.cos(ra) * arm_ + 18.0
    hc = c.sub(hx, hy, head_rot, hs)
    yaw = (P.turn + P.h_turn) * PI / 2
    if clamp(getattr(P, 'unmask', 0.0)) > 0.01:
        _bunny_unmasked_head(hc, who, P, yaw, P.h_nod * 0.6, det, t, light, sp)
    else:
        draw_head_local(hc, who, P, yaw, P.h_nod * 0.6, det, t, light, sp)
    for side in front: _bunny_arm(c, sp, B, P, side, det, t, light)
    return B


def _densify_xy(xs, ys, n=3):
    xs = np.asarray(xs, float); ys = np.asarray(ys, float)
    m = len(xs); out_x, out_y = [], []
    for i in range(m):
        j = (i + 1) % m
        for k in range(n):
            u = k / n
            out_x.append(xs[i] + (xs[j] - xs[i]) * u); out_y.append(ys[i] + (ys[j] - ys[i]) * u)
    return np.array(out_x), np.array(out_y)


def _bunny_tail(c, sp, B, rows, det):
    cl = sp['cloth']
    X, Y, s_, Z = B.p3(0, B.y_hip + 10, -sp['body']['hip'] * 0.8, upper=False)
    r = 34 * s_
    pts = [(X + math.cos(a) * r, Y + math.sin(a) * r * 0.92) for a in np.linspace(0, 2 * PI, 20, endpoint=False)]
    xs, ys = _fluff_ring(np.array([p[0] for p in pts]), np.array([p[1] for p in pts]), 6.0, 9, 4, spiky=0.4)
    tail = _pts_path(xs, ys, True, 0.9)
    c.fill(tail, cl['belly']); c.fill(_crescent(tail, -6, -5), cl['belly_sh'], 170)
    if sp.get('dirt', 0) > 0.3: c.fill(tail, cl['mud'], 90)
    c.line(tail, c.lw)


def _bunny_zipper(c, sp, B, rows, det):
    """'It has a zipper in the back, where zippers go.' A zipper from the collar to the small of the back."""
    cl = sp['cloth']
    pts, v = _surf_poly(B, rows, [(0, B.y_sh - 26), (0, B.y_wa + 30)], back=True, dz=2)
    if v < 0.05: return
    c.line(poly(pts, False), c.lw * 2.2, cl['fur_dp'])
    c.line(poly(pts, False), c.lw * 0.9, '#9a958a')
    if det >= 1:
        (x0, y0), (x1, y1) = pts
        teeth = [poly([(x0 + (x1 - x0) * u - 4, y0 + (y1 - y0) * u), (x0 + (x1 - x0) * u + 4, y0 + (y1 - y0) * u)], False)
                 for u in np.linspace(0.03, 0.97, 22)]
        c.line(_multi(teeth), c.lw * 0.35, '#5a5650', 220)
        c.shape(rrect(x0 - 6, y0 + 6, 12, 24, 4), '#a8a39a', c.lw * 0.5)


def _bunny_arm(c, sp, B, P, side, det, t, light):
    S, E, Wr = _arm_data(sp, B, P, side)
    b = sp['body']
    pts = [B.p3(*S), B.p3(*E), B.p3(*Wr)]
    P2 = [(p[0], p[1]) for p in pts]
    cl = sp['cloth']
    # a round plush shoulder cap so the arm grows out of a soft shoulder, not a box corner
    cx_, cy_ = P2[0][0] - side * 4 * B.ct, P2[0][1] - 10
    cap = _blob(cx_, cy_, b['arm'][0] * 0.62 * pts[0][2], b['arm'][0] * 0.55 * pts[0][2], 9, 3 + side, 0.12)
    c.fill(cap, cl['fur']); c.fill(_crescent(cap, -side * 8, 4), cl['fur_sh'], 110); c.line(cap, c.lw)
    aw0, aw1 = b['arm']
    hz = clamp(900.0 / (900.0 - pts[2][3]), 0.6, 3.0)
    widths = [aw0 * pts[0][2], (aw0 + aw1) / 2 * max(pts[1][2], hz ** 0.5), aw1 * hz]
    tp = _tube([(P2[0][0] - side * 6, P2[0][1] - 18)] + P2, [widths[0] * 1.1] + widths)
    _bunny_limb(c, sp, tp, [(P2[0][0] - side * 6, P2[0][1] - 18)] + P2, [widths[0] * 1.1] + widths, det, 'arm')
    wx, wy = P2[2]
    ang = math.degrees(math.atan2(P2[2][1] - P2[1][1], P2[2][0] - P2[1][0])) - 90
    pre = 'hl_' if side > 0 else 'hr_'
    shape = getattr(P, pre + 'shape'); prop = getattr(P, pre + 'prop')
    up = getattr(P, pre + 'up'); rot = getattr(P, pre + 'rot')
    hang = ang * (1 - up) + 180.0 * up + rot
    hs = hz * getattr(P, pre + 'scale', 1.0)
    if shape in (None, 'mitt', 'relaxed', 'open'): shape = 'paw'
    elif shape == 'point': shape = 'paw_point'
    elif shape in ('grip', 'fist'): shape = 'paw_grip'
    elif shape == 'flat': shape = 'paw_flat'
    elif shape == 'wave': shape = 'paw_open'
    if prop:
        _held_prop(c, sp, prop, wx, wy, hang, hs, side, det, t, P)
        shape = 'paw_grip'
    _draw_paw(c, sp, shape, wx, wy, hs, hang, side, det)
    if prop: _held_prop(c, sp, prop, wx, wy, hang, hs, side, det, t, P, front_part=True)


def _held_prop(c, sp, prop, wx, wy, hang, hs, side, det, t, P, front_part=False):
    """Placeholder until the prop system below is defined (it replaces this)."""
    return None


def _bunny_unmasked_head(c, who, P, yaw, pitch, det, t, light, sp):
    """Placeholder until the unmask composite below is defined (it replaces this)."""
    return draw_head_local(c, who, P, yaw, pitch, det, t, light, sp)


_figure_v2 = _figure


def _figure(c, who, P, det, t, light=None, upper_only=False):
    """Whole character in body units on Ctx c (feet at y=0). The Bunnyman's suit and the v3 cast dispatch here."""
    sp = CAST[who]
    if sp.get('bunny'): return _bunny_figure(c, who, P, det, t, light, upper_only)
    if sp.get('v3') and '_figure3' in globals(): return _figure3(c, who, P, det, t, light, upper_only)
    return _figure_v2(c, who, P, det, t, light, upper_only)


# ====================================================================================================== the family + cast
# The dummy film's Mom and the delivery film's Dad keep their designs under new ids; this film takes the plain names.
CAST['mom_dummy'] = CAST['mom']
CAST['dad_delivery'] = CAST['dad']
_F11 = [-120, -114, -100, -70, -30, 10, 50, 82, 104, 116, 120]


def _v3cast(**kw):
    """A v3 cast entry: defaults shared by the whole new cast (natural iris eyes with resting lids, expressive brows,
    v3 hands and garments)."""
    d = dict(hat=None, sex='f', hh=184.0, v3=True, head_ys=_F11, head_ws=[0, 50, 72, 88, 93, 92, 85, 69, 49, 25, 0],
             eye_dx=40, eye_y=-6, eye_r=19.0, eye_ry=0.86, iris_k=0.66, lid_rest=0.16, pupil=1.0, brow_th=8.5, nose_len=20,
             mouth_y=60, mouth_w=20, stubble=None, stub=0, lips=0.0, bags=0.25, age=0.2, blink_rate=0.3, lock=0.0, micro=1.0,
             breath=1.0, scar=0, ring=0, part=0, lashes=0.0, feet='shoes', m=1.70, hand_k=1.18)
    d.update(kw)
    return d


# Laurie Price, 43 ("Mom"): pretty, neat, warm; a too-still smile. Auburn bob with a side part, green eyes (the body's own:
# the real Laurie's), a dusty-rose cardigan over a cream blouse with a round collar, taupe trousers, ballet flats, pearl
# studs, her own gold wedding ring. pose.scratch 0..1: sleeves pushed up, forearms scratched to ribbons; pose.mess: hair
# coming loose.
CAST['mom'] = _v3cast(
    outfit='cardigan3', hair='bob', sex='f', hh=182.0, m=1.66,
    head_ws=[0, 49, 71, 87, 92, 90, 82, 66, 46, 24, 0],
    eye_dx=40, eye_y=-6, eye_r=18.5, iris_c='#5f7f58', lid_rest=0.2, brow_th=7.0, nose_len=21, mouth_w=20,
    skin='#ebc3aa', skin_sh='#c4927d', skin_dp='#80564f', blush='#e6a29c', lip='#b66a70', lips=0.55,
    hair_c='#7c3d26', brow_c='#5a2c1c', bags=0.3, age=0.42, lashes=1.0, earrings='pearl', ring=1, part=1,
    body=dict(sh=104, ch=104, wa=88, hip=106, arm=(42, 34), leg=(46, 38), neck=34, hand=1.0),
    feet='flats',
    cloth=dict(top='#c98d94', top_sh='#9c6470', top_hi='#e2aab0', rib='#b07880', button='#f3ece0', blouse='#f2e9da',
               blouse_sh='#cbbfa8', trousers='#5f5660', trousers_sh='#3f3842', shoes='#3b2b2d', shoes_sh='#22191a'))
# the narrator in Mom's body at Holloway State Hospital: the same face, hair loose and unkempt, dark circles, a hospital
# gown, the narrator's mannerisms (scared cast: blinks, glances, hugs their knees)
CAST['mom_hosp'] = dict(CAST['mom'], outfit='gown3', hair='loose', bags=0.95, lid_rest=0.1, blink_rate=0.4, feet='socks',
                        cloth=dict(top='#b9cbd8', top_sh='#8aa0b2', top_hi='#d6e3ec', print_c='#6f8aa4', socks='#d9d4c8',
                                   socks_sh='#aaa496', band='#f2f2ee', trousers='#b9cbd8', trousers_sh='#8aa0b2'))
CAST['mom_hosp']['skin'] = '#e2bea8'; CAST['mom_hosp']['skin_sh'] = '#b98f80'
# June, 7: honey-brown hair in two low pigtails with pink scrunchies and a side fringe, brown eyes, mint pajamas with a
# tiny Easter-egg print, white socks with pink toes. 'june_dress': the yellow Easter dress (exactly like the photo).
_JUNE = dict(hair='pigtails', sex='f', hh=236.0, child=True, m=1.22,
             head_ys=_F11, head_ws=[0, 58, 84, 98, 102, 102, 97, 85, 63, 34, 0],
             eye_dx=40, eye_y=6, eye_r=22.0, iris_c='#6e4a2c', iris_k=0.72, lid_rest=0.06, pupil=1.15, brow_th=6.0, nose_len=12,
             mouth_y=64, mouth_w=15, nose='button',
             skin='#f2cbb3', skin_sh='#c99c88', skin_dp='#85605a', blush='#f2a39b', lip='#c4807a', lips=0.25,
             hair_c='#a06c3c', brow_c='#7a4e2a', bags=0.05, age=0.0, blink_rate=0.35, lashes=0.8, part=-1,
             body=dict(sh=80, ch=80, wa=78, hip=80, arm=(34, 28), leg=(40, 34), neck=30, hand=0.78, arm_k=0.86))
CAST['june'] = _v3cast(outfit='pj3', feet='socks', **_JUNE,
                       cloth=dict(top='#a6d8c6', top_sh='#76ad99', top_hi='#c6ecde', trim='#f4f7f2', print_c='#f2a5b5',
                                  print_c2='#f6d978', trousers='#a6d8c6', trousers_sh='#76ad99', socks='#f4f2ee', socks_sh='#c9c5bc',
                                  sock_toe='#f2a5b5', tie='#f08aa0'))
_DRESS = dict(top='#f2c84b', top_sh='#c99a24', top_hi='#fbe08a', collar='#fbfaf4', collar_sh='#d9d4c4', sash='#fbfaf4',
              lace='#fbfaf4', legs='#f2cbb3', legs_sh='#c99c88', socks='#fbfaf4', socks_sh='#d6d1c4', shoes='#1c1a1f',
              shoes_sh='#0c0b0e', tie='#f7d34a', trousers='#f2cbb3', trousers_sh='#c99c88')
CAST['june_dress'] = _v3cast(outfit='dress3', feet='maryjane', **_JUNE, cloth=dict(_DRESS, tie='#f08aa0'))
# Laurie Price at 7, Easter 1987: strawberry-blonde high pigtails with big yellow ribbon bows, straight bangs, green eyes,
# the yellow Easter dress, white frilly socks, black Mary Janes. Walks out of the trees at sunrise with a golden egg.
CAST['laurie87'] = _v3cast(outfit='dress3', feet='maryjane', **dict(_JUNE, hair='pigtails_hi', hair_c='#d99258', brow_c='#b9773f',
                                                                       iris_c='#5f8a5a', skin='#f4d0ba', part=0),
                           cloth=dict(_DRESS))
# The narrator, 16 ("I"; never said if boy or girl): chin-length dark auburn-brown hair, slightly messy, a soft jaw,
# hazel-green eyes, no make-up; an oversized sage-green hoodie with the sleeves half over the hands, charcoal joggers,
# grey socks. 'narrator_new' = the thing in that body (never blinks, a calm wrong smile, hums); 'narrator_neat' = the
# same thing at the hospital visits (hair combed and tucked, a pressed cream cardigan over a white collar).
CAST['narrator'] = _v3cast(
    outfit='hoodie3', hair='chin', sex='n', hh=184.0, m=1.68,
    head_ws=[0, 50, 72, 88, 93, 92, 85, 70, 50, 26, 0],
    eye_dx=41, eye_y=-5, eye_r=19.0, iris_c='#7a7a4c', lid_rest=0.14, brow_th=8.5, nose_len=22, mouth_w=19,
    skin='#e5b99f', skin_sh='#bb8d78', skin_dp='#7a524a', blush='#e09a92', lip='#b07870', lips=0.0,
    hair_c='#4a2a1f', brow_c='#3a2118', bags=0.45, age=0.12, lashes=0.25, part=1, feet='socks',
    body=dict(sh=108, ch=102, wa=94, hip=100, arm=(46, 38), leg=(50, 42), neck=38, hand=0.98),
    cloth=dict(top='#7f957a', top_sh='#596c55', top_hi='#9eb299', hood='#73896e', hood_sh='#4f604b', string='#e9e4d8',
               trousers='#3a3c44', trousers_sh='#24262c', socks='#a8a8ae', socks_sh='#7b7b82'))
CAST['narrator_new'] = dict(CAST['narrator'], lock=0.9, blink_rate=0.0, micro=0.25, talk=0.35, pupil=0.85, lid_rest=0.22)
CAST['narrator_neat'] = dict(CAST['narrator_new'], outfit='neat3', hair='chin_neat', feet='flats',
                             cloth=dict(top='#e9dfc9', top_sh='#bfb299', top_hi='#f6efe0', collar='#ffffff', collar_sh='#d8d6d0',
                                        button='#8a7a5a', trousers='#3d4256', trousers_sh='#272b39', shoes='#2b2522', shoes_sh='#171311'))
# Grandma (memory): kind, old; silver hair in a soft bun, glasses, a lavender cardigan over a flowered blouse, a brooch,
# a plum skirt. Teaches the family knock with her knuckles.
CAST['grandma'] = _v3cast(
    outfit='gran3', hair='gran_bun', sex='f', hh=188.0, m=1.58, glasses=True,
    head_ws=[0, 52, 77, 94, 100, 99, 91, 76, 54, 28, 0],
    eye_dx=41, eye_y=-4, eye_r=17.0, iris_c='#6f8299', lid_rest=0.3, brow_th=6.0, nose_len=24, mouth_w=20,
    skin='#ecc7b2', skin_sh='#c39985', skin_dp='#87615a', blush='#e8a3a0', lip='#b3757a', lips=0.4,
    hair_c='#d9d6d1', brow_c='#a39d96', bags=0.7, age=1.1, lashes=0.4, feet='shoes', ring=1,
    body=dict(sh=100, ch=108, wa=104, hip=112, arm=(42, 34), leg=(40, 33), neck=34, hand=0.95),
    cloth=dict(top='#a296bb', top_sh='#776c90', top_hi='#bdb3d3', blouse='#f3ebe0', blouse_sh='#cfc4b2', flower='#e48ea0',
               flower2='#9ab878', brooch='#d8b04c', skirt='#5d4763', skirt_sh='#3e2e44', legs='#e3c2b0', trousers='#5d4763',
               trousers_sh='#3e2e44', shoes='#5a3d2e', shoes_sh='#3a271d'))
# Dad (memory, last Easter): mid 40s, short brown hair greying at the temples, stubble, blue-grey eyes, a tan canvas work
# jacket over a charcoal henley, jeans, boots, a gold wedding ring ("M and L, forever"); a big black flashlight.
CAST['dad'] = _v3cast(
    outfit='jacket3', hair='side_short', sex='m', hh=176.0, m=1.83,
    head_ws=[0, 51, 75, 92, 98, 97, 90, 75, 54, 29, 0],
    eye_dx=42, eye_y=-7, eye_r=18.0, iris_c='#5d7489', lid_rest=0.22, brow_th=10.5, nose_len=25, mouth_w=21,
    skin='#ddab8e', skin_sh='#b07f68', skin_dp='#6e4c44', blush='#d99690', lip='#a06e66', stubble='#4e3a2e', stub=0.6,
    hair_c='#4b3424', brow_c='#3a281c', bags=0.4, age=0.5, ring=-1, part=-1, feet='boots',
    body=dict(sh=130, ch=124, wa=112, hip=110, arm=(56, 46), leg=(60, 50), neck=50, hand=1.05),
    cloth=dict(top='#a8875a', top_sh='#7a5f3c', top_hi='#c4a676', collar='#5a3e26', shirt='#3c3f46', shirt_sh='#26282d',
               trousers='#3e5470', trousers_sh='#28374b', shoes='#4a3424', shoes_sh='#2e2017', button='#3a2a1c'))
# Dale Whitlock at 55: the man inside the suit. Only his face is ever seen (the suit's head half off): gaunt, skin and
# bone, grey stubble, thin grey hair, and the wide wet eyes of a terrified little girl. His lips form "Mama".
CAST['dale'] = _v3cast(
    outfit='gown3', hair='thin', sex='m', hh=180.0, m=1.85, gaunt=1.3,
    head_ws=[0, 50, 72, 86, 90, 87, 77, 64, 47, 26, 0],
    eye_dx=40, eye_y=-6, eye_r=19.5, iris_c='#6a5a44', lid_rest=0.0, pupil=1.25, brow_th=7.0, nose_len=28, mouth_w=20,
    skin='#cdb3a3', skin_sh='#9a8073', skin_dp='#5e4a48', blush='#c9928f', lip='#9a706c', stubble='#9a958e', stub=0.9,
    hair_c='#8e8a84', brow_c='#6e6a64', bags=1.2, age=0.9, lock=0.0, lashes=0.3, wet_k=1.0,
    body=dict(sh=118, ch=104, wa=92, hip=98, arm=(44, 36), leg=(50, 42), neck=40, hand=1.0),
    cloth=dict(top='#5d5f66', top_sh='#3f4148', top_hi='#7e8189', print_c='#5d5f66', trousers='#5d5f66', trousers_sh='#3f4148',
               socks='#5d5f66', socks_sh='#3f4148', band='#5d5f66'))
# The police (freshened from the police film's officers: ordinary, kind people this time) and the hospital staff
CAST['cop'] = _v3cast(
    outfit='police', hat='cap', hair='short', sex='m', hh=178.0, m=1.80,
    head_ws=[0, 53, 77, 91, 96, 95, 88, 74, 53, 29, 0], eye_dx=42, eye_y=-9, eye_r=18.0, iris_c='#3a2a20', lid_rest=0.22,
    brow_th=10.0, nose_len=25, mouth_w=21, skin='#b4876c', skin_sh='#8a634f', skin_dp='#54392f', blush='#c98a7c', lip='#8f5f55',
    stubble='#3a2c26', stub=0.4, hair_c='#211a17', brow_c='#1b1513', bags=0.45, age=0.5, feet='shoes',
    body=dict(sh=130, ch=124, wa=108, hip=110, arm=(52, 42), leg=(66, 52), neck=50, hand=1.0), cloth=dict(_POLICE))
CAST['cop2'] = _v3cast(
    outfit='police', hat='cap', hair='bun', sex='f', hh=180.0, m=1.70,
    head_ws=[0, 50, 72, 87, 92, 90, 81, 64, 43, 22, 0], eye_dx=41, eye_y=-8, eye_r=18.5, iris_c='#2e2018', lid_rest=0.18,
    brow_th=8.0, nose_len=21, mouth_w=20, skin='#8e5f46', skin_sh='#6a4433', skin_dp='#40281f', blush='#b0685a', lip='#7a4a42',
    lips=0.5, hair_c='#1a1311', brow_c='#140f0d', bags=0.35, age=0.35, lashes=1.0, earrings=True, feet='shoes',
    body=dict(sh=114, ch=110, wa=90, hip=104, arm=(44, 36), leg=(58, 46), neck=41, hand=0.9), cloth=dict(_POLICE, shirt='#22304d'))
CAST['doctor'] = _v3cast(
    outfit='labcoat3', hair='doc', sex='m', hh=180.0, m=1.78, glasses=True,
    head_ws=[0, 52, 76, 92, 97, 96, 88, 73, 52, 28, 0], eye_dx=41, eye_y=-6, eye_r=17.5, iris_c='#4d6680', lid_rest=0.26,
    brow_th=9.0, nose_len=26, mouth_w=21, skin='#e4bba2', skin_sh='#b88f7a', skin_dp='#76534b', blush='#dc9c94', lip='#a36f69',
    stubble='#8a8580', stub=0.25, hair_c='#9d9a96', brow_c='#6e6a66', bags=0.55, age=0.8, feet='shoes',
    body=dict(sh=118, ch=114, wa=108, hip=106, arm=(48, 40), leg=(56, 46), neck=42, hand=1.0),
    cloth=dict(top='#f4f5f2', top_sh='#c9ccc8', top_hi='#ffffff', shirt='#a9c1db', shirt_sh='#7e98b4', tie='#5a3d55',
               trousers='#3c3f48', trousers_sh='#26282e', shoes='#2a2320', shoes_sh='#16110f', badge='#ffffff'))
CAST['nurse'] = _v3cast(
    outfit='scrubs3', hair='pony', sex='f', hh=182.0, m=1.64,
    head_ws=[0, 49, 71, 87, 92, 90, 82, 66, 46, 24, 0], eye_dx=40, eye_y=-6, eye_r=18.5, iris_c='#3b2a1e', lid_rest=0.2,
    brow_th=7.5, nose_len=20, mouth_w=20, skin='#c99677', skin_sh='#9d6f57', skin_dp='#5e4035', blush='#d38a7d', lip='#a0605c',
    lips=0.5, hair_c='#2a1c16', brow_c='#22160f', bags=0.4, age=0.3, lashes=0.9, feet='clogs',
    body=dict(sh=104, ch=104, wa=90, hip=106, arm=(42, 34), leg=(46, 38), neck=34, hand=0.92),
    cloth=dict(top='#5fa8a4', top_sh='#3f7d7a', top_hi='#80c4c0', trousers='#5fa8a4', trousers_sh='#3f7d7a', shoes='#e8eef0',
               shoes_sh='#b5c0c4', lanyard='#2d4a8a', badge='#ffffff'))

BUNNY_CAST = ('bunny', 'bunny87', 'mom', 'mom_hosp', 'june', 'june_dress', 'laurie87', 'narrator', 'narrator_new',
              'narrator_neat', 'grandma', 'dad', 'dale', 'cop', 'cop2', 'doctor', 'nurse')


def height_px(who, px_per_m):
    """Design-px figure height (feet to crown) of a cast member at a scene scale of px_per_m (the same for everyone at that
    depth): keeps everybody to scale (June 1.22 m, Mom 1.66 m, the Bunnyman 1.98 m to the crown, ears above)."""
    return CAST[who].get('m', 1.7) * px_per_m


# ====================================================================================================== v3 faces
_eye_v2, _brow_v2 = _eye, _brow


def _eye(c, hm, sp, P, side, det, t, skin, sh):
    """One eye. The v3 cast (sp iris_c): an almond eye with a coloured iris (darker limbal ring, lighter lower half, the
    pupil inside, two catchlights), an upper lid that rests a little over the iris (sp lid_rest; wide opens it, blink /
    squint / lid_l / lid_r close it), a dark lash line with a crease above, and optional lashes. Older casts: v2 eye."""
    if not sp.get('iris_c'): return _eye_v2(c, hm, sp, P, side, det, t, skin, sh)
    ex0 = side * sp['eye_dx']; ey0 = sp['eye_y']
    X, Y, V = hm.map1(ex0, ey0, 2.0)
    if V < 0.12: return None
    fs = hm.sx(ex0, ey0)
    r = sp['eye_r'] * (1.0 + 0.10 * P.wide) * (1.0 + 0.03 * P.brow_up)
    ry = r * sp.get('eye_ry', 0.86)
    rx = r * 1.08 * fs
    bl_ = max(P.blink, P.lid_l if side > 0 else P.lid_r)
    # lid cover (0 = top of the white, 1 = shut): rest + squint, opened by wide / brow_up, closed by blinks
    rest = sp.get('lid_rest', 0.15) * (1.0 - clamp(P.wide * 1.4)) * (1.0 - 0.5 * clamp(P.brow_up)) + 0.1 * clamp(P.brow_angry)
    cover = clamp(rest + 0.32 * P.squint + (1.0 - P.eye_open) * 0.9 + 0.12 * clamp(P.smile) * (1 - sp['lock']), 0.0, 1.0)
    cover = cover + (1.0 - cover) * clamp(bl_)
    lift_w = 0.18 * clamp(P.wide - 0.3) / 0.7              # terror: white shows above the iris
    # sockets: a soft shadow round the eye (darker on tired faces)
    c.glow(X, Y + 2, rx * 1.75, ry * 1.8, sp['skin_dp'], 30 + 40 * sp['bags'] + 30 * P.wide)
    bags = sp['bags']
    if bags > 0.2 and det >= 1:
        fold = smooth([(X - rx * 0.75, Y + ry * 1.05), (X, Y + ry * 1.5 + 2 * bags), (X + rx * 0.75, Y + ry * 1.05)], False)
        c.line(fold, c.lw * 0.38, sp['skin_dp'], 120 * min(1.0, bags))
        if bags > 0.7:
            c.fill(smooth([(X - rx * 0.9, Y + ry * 0.7), (X, Y + ry * 1.45 + 3 * bags), (X + rx * 0.9, Y + ry * 0.7), (X, Y + ry * 1.0)], True, 0.9),
                   mix(sh, sp['skin_dp'], 0.5), 70 * min(1.3, bags))
    tilt = 0.10 * side                                     # outer corners a touch higher
    if cover > 0.93:                                       # shut: a curved lid line with lashes
        k_ = 1.0 if (P.squint > 0.3 or P.smile > 0.4) else -1.0
        lid = smooth([(X - rx * 1.05, Y + ry * 0.05 - tilt * side * ry * 0.2), (X, Y + ry * (0.32 if k_ < 0 else -0.1)),
                      (X + rx * 1.05, Y + ry * 0.05 + tilt * side * ry * 0.2)], False)
        c.line(lid, c.lw * 1.1)
        if sp['lashes'] > 0:
            ls = []
            for k in (0.55, 0.85):
                x1 = X + side * rx * k
                ls.append(poly([(x1, Y + ry * 0.2), (x1 + side * 6, Y + ry * 0.5)], False))
            c.line(_multi(ls), c.lw * 0.5)
        return (X, Y, r, fs)
    pts = []
    for a in np.linspace(0, 2 * PI, 28, endpoint=False):
        ca, sa = math.cos(a), math.sin(a)
        yy = sa * (ry * (1.0 + lift_w) if sa < 0 else ry * 0.82)
        pts.append((X + ca * rx, Y + yy - ca * side * tilt * ry))
    white = smooth(pts, True, 0.9)
    wc = '#f1eee8' if P.pale < 0.5 else '#e6e6e4'
    c.fill(white, wc)
    if det >= 1:
        c.radial(white, X, Y + ry * 0.2, max(rx, ry) * 1.1, [(0, wc, 0), (0.65, wc, 0), (1, sp.get('eye_edge', '#c4b6ae'), 230)], sy=ry / max(rx, ry))
    lock = clamp(P.lock)
    lx = lerp(P.look_x, -math.sin(hm.yaw) * 0.85, lock)
    ly = lerp(P.look_y, -math.sin(hm.pitch) * 1.1 - 0.05, lock)
    ir = ry * sp.get('iris_k', 0.66) * (1.0 - 0.08 * clamp(P.wide))
    reach_x = max(0.0, rx - ir * 0.72 * fs); reach_y = max(0.0, ry - ir * 0.75)
    px = X + lx * reach_x; py = Y + ly * reach_y
    pr = max(ir * 0.42 * sp['pupil'] * P.pupil, 1.6)
    ic = sp['iris_c']
    lid_y = Y - ry * (1.0 + lift_w) + cover * ry * 1.85
    with c.clip(white):
        if det >= 1 and P.bloodshot > 0.02:
            vs = []
            for k in range(5):
                ang = (hash01(k, 7 + side) * 2 - 1) * PI
                x1, y1 = X + math.cos(ang) * rx * 1.02, Y + math.sin(ang) * ry * 1.02
                x2, y2 = X + math.cos(ang - 0.15) * rx * 0.55, Y + math.sin(ang - 0.15) * ry * 0.55
                vs.append(smooth([(x1, y1), ((x1 + x2) / 2 + 2, (y1 + y2) / 2), (x2, y2)], False))
            c.line(_multi(vs), c.lw * 0.2, '#c0505a', 140 * clamp(P.bloodshot))
        iris = oval(px, py, ir * fs, ir)
        c.fill(iris, ic)
        c.radial(iris, px, py + ir * 0.35, ir * 1.05, [(0, mix(ic, '#ffffff', 0.35), 200), (0.55, ic, 0), (1, mix(ic, '#000000', 0.55), 255)], sy=1.0)
        if det >= 1:
            sp_ = [poly([(px + math.cos(a) * pr * 1.25 * fs, py + math.sin(a) * pr * 1.25), (px + math.cos(a) * ir * 0.86 * fs, py + math.sin(a) * ir * 0.86)], False)
                   for a in np.linspace(0, 2 * PI, 14, endpoint=False)]
            c.line(_multi(sp_), c.lw * 0.18, mix(ic, '#000000', 0.4), 110)
        c.line(iris, c.lw * 0.32, mix(ic, '#000000', 0.7), 230)
        c.fill(oval(px, py, pr * fs, pr), '#0b0b0e')
        # the shadow the upper lid casts on the eye
        c.fill(rect(X - rx * 2, lid_y - ry * 2, rx * 4, ry * 2 + ry * 0.32), '#3a2a2a', 55)
        cl_ = max(ir * 0.26, 1.6)
        c.fill(oval(px - ir * 0.38 * fs, py - ir * 0.36, cl_ * fs, cl_), '#ffffff', 245)
        if det >= 1: c.fill(oval(px + ir * 0.34 * fs, py + ir * 0.34, cl_ * 0.42 * fs, cl_ * 0.42), '#ffffff', 190)
        if P.wet > 0 and det >= 1:
            c.fill(smooth([(X - rx, Y + ry * 0.55), (X, Y + ry * 0.8), (X + rx, Y + ry * 0.55), (X, Y + ry * 1.0)], True), '#b8d4f2', 140 * clamp(P.wet))
            c.fill(oval(px + ir * 0.1 * fs, py + ir * 0.62, ir * 0.5 * fs, ir * 0.12), '#ffffff', 120 * clamp(P.wet))
        # upper lid skin over the eye
        lidp = smooth([(X - rx * 1.4, Y - ry * 2.2), (X + rx * 1.4, Y - ry * 2.2), (X + rx * 1.4, lid_y + side * tilt * ry * 0.3),
                       (X, lid_y - ry * 0.12 * (1 - cover)), (X - rx * 1.4, lid_y - side * tilt * ry * 0.3)], True, 0.6)
        c.fill(lidp, mix(skin, sh, 0.18))
        # lower lid push (squint / genuine smile)
        sq = P.squint * 0.6 + max(0.0, P.smile) * 0.16 * (1 - P.wide) * (0.0 if sp['lock'] >= 0.5 else 1.0)
        if sq > 0.03:
            ly2 = Y + ry * 0.82 - sq * ry * 1.0
            low = smooth([(X - rx * 1.4, Y + ry * 2.0), (X - rx * 1.4, ly2 + ry * 0.25), (X, ly2), (X + rx * 1.4, ly2 + ry * 0.25),
                          (X + rx * 1.4, Y + ry * 2.0)], True, 0.6)
            c.fill(low, skin)
    # outline: the lower edge thin, the lash line along the lid thick
    c.line(white, c.lw * 0.45, sp['skin_dp'], 160)
    span = rx * (1.0 - 0.25 * cover)
    lash = smooth([(X - rx * 1.06, Y - side * tilt * ry * 0.9 + ry * 0.1), (X - rx * 0.55, lid_y + ry * 0.02 - ry * 0.06 * (1 - cover)),
                   (X, lid_y - ry * 0.12 * (1 - cover)), (X + rx * 0.55, lid_y + ry * 0.02 - ry * 0.06 * (1 - cover)),
                   (X + rx * 1.06, Y + side * tilt * ry * 0.9 + ry * 0.1)], False)
    c.line(lash, c.lw * (1.05 + 0.35 * sp.get('lashes', 0.0)))
    if det >= 1:                                            # lid crease above
        cy_ = min(lid_y, Y - ry * 0.85) - ry * 0.42 - ry * 0.25 * clamp(P.wide)
        c.line(smooth([(X - rx * 0.8, cy_ + ry * 0.25), (X, cy_), (X + rx * 0.85, cy_ + ry * 0.2)], False), c.lw * 0.4, sp['skin_dp'], 150)
        if sp.get('lashes', 0.0) > 0.3:                     # a few lashes flicking out at the outer corner
            ox_ = X + side * rx * 1.02; oy_ = Y + side * tilt * ry * 0.9 + ry * 0.05
            ls = [poly([(ox_ - side * rx * 0.1 * k, oy_ - ry * 0.25 * k), (ox_ + side * rx * (0.25 - 0.05 * k), oy_ - ry * (0.38 + 0.2 * k))], False)
                  for k in range(3)]
            c.line(_multi(ls), c.lw * 0.42 * sp['lashes'])
    return (X, Y, r, fs, px, py, 1.0 - cover)


def _brow(c, hm, sp, P, side, eyeinfo):
    """Brows. v3 cast: a tapered brush stroke (full at the inner end, a fine tail), arched; up / angry / sad / asym move the
    inner and outer ends independently so worry, fear and the too-still smile all read. Older casts: v2 brow."""
    if not sp.get('iris_c'): return _brow_v2(c, hm, sp, P, side, eyeinfo)
    ex0 = side * sp['eye_dx']; ey0 = sp['eye_y']; r = sp['eye_r'] * sp.get('eye_ry', 0.86)
    up = P.brow_up + P.brow_asym * 0.5 * side
    base = ey0 - r - 16 - 13 * up
    inner_dy = 12 * P.brow_angry - 15 * P.brow_sad
    outer_dy = -4 * P.brow_angry + 9 * P.brow_sad
    th = sp['brow_th']
    xi, xo = ex0 - side * 22, ex0 + side * 30
    n = 7
    top, bot = [], []
    for k in range(n):
        u = k / (n - 1)
        x = xi + (xo - xi) * u
        arch = -7.0 * math.sin(PI * min(1.0, u * 1.15)) * (1.0 - 0.4 * P.brow_sad)
        y = base + inner_dy * (1 - u) + outer_dy * u + arch
        w = th * (1.05 - 0.75 * u ** 1.3)
        top.append((x, y - w * 0.55)); bot.append((x, y + w * 0.45))
    allp = top + bot[::-1]
    X, Y, V = hm.map([p[0] for p in allp], [p[1] for p in allp], 3.0)
    if V.mean() < 0.1: return
    path = _pts_path(X, Y, True, 0.7)
    c.fill(path, sp['brow_c'])
    c.line(path, c.lw * 0.25, sp['brow_c'])



# ====================================================================================================== v3 hair
# Styles: 'bob' (Mom: neat chin-length auburn bob, side part, swept fringe), 'loose' (Mom's body at the hospital: longer,
# unkempt, strands across the face), 'pigtails' (June: two low pigtails with scrunchies, side fringe), 'pigtails_hi'
# (Laurie in 1987: high pigtails with yellow ribbon bows, straight bangs), 'chin' (the narrator: chin length, a little
# messy, off-centre part), 'chin_neat' (the same, combed and tucked behind the ears), 'gran_bun' (Grandma), 'side_short'
# (Dad), 'thin' (Dale, receded and grey), 'pony' (the nurse), 'doc' (the doctor).
_HAIR3 = ('bob', 'loose', 'pigtails', 'pigtails_hi', 'chin', 'chin_neat', 'gran_bun', 'side_short', 'thin', 'pony', 'doc')
_HANG3 = {'bob': 118.0, 'loose': 176.0, 'chin': 100.0}            # hair hanging past the jaw (bottom y, head units)
_EARLESS = _EARLESS + ('bob', 'loose', 'chin')
_hairline_v2, _hair_region_v2 = _hairline, _hair_region


def _hairline(style, part):
    """(yf(phi) -> hairline height round the head, grow) for a hair style (v3 styles here, older ones as before)."""
    if style not in _HAIR3: return _hairline_v2(style, part)
    pp = 1.0 if part >= 0 else -1.0
    if style in ('bob', 'loose'):
        def yf(ph):
            q = ph * pp                                     # the part on the character's +part side
            return np.interp(q, [-PI, -1.3, -1.06, -0.72, -0.25, 0.32, 0.75, 1.02, 1.3, PI],
                             [90, 90, 40, -44, -60, -90, -72, -30, 90, 90])
        return yf, 13.0 if style == 'bob' else 15.0
    if style == 'chin':
        def yf(ph):
            q = ph * pp
            return np.interp(q, [-PI, -1.3, -1.06, -0.62, -0.1, 0.22, 0.65, 1.02, 1.3, PI],
                             [90, 90, 36, -40, -58, -88, -66, -22, 90, 90])
        return yf, 12.0
    if style == 'chin_neat':
        def yf(ph):
            q = ph * pp
            y = np.interp(q, [-PI, -2.2, -1.75, -1.25, -0.9, -0.1, 0.22, 0.7, 1.0, 1.25, 1.75, 2.2, PI],
                          [94, 94, 40, -20, -38, -62, -90, -70, -40, -20, 40, 94, 94])
            return y
        return yf, 9.0
    if style == 'pigtails':
        def yf(ph):
            q = ph * pp
            return np.maximum(np.interp(q, [-PI, -1.9, -1.4, -1.0, -0.62, -0.1, 0.25, 0.7, 1.0, 1.4, 1.9, PI],
                                        [86, 60, -6, -28, -38, -48, -84, -64, -32, -6, 60, 86]), _nape(ph))
        return yf, 8.0
    if style == 'pigtails_hi':
        def yf(ph):
            a = np.abs(ph)
            return np.maximum(np.interp(a, [0, 0.78, 0.98, 1.3, 1.75, 2.2, PI], [-44, -44, -36, -12, 14, 72, 86]), _nape(ph))
        return yf, 8.0
    if style == 'gran_bun':
        def yf(ph):
            a = np.abs(ph)
            return np.maximum(np.interp(a, [0, 0.5, 0.95, 1.3, 1.7, 2.3, PI], [-80, -76, -52, -10, 0, 30, 46]), _nape(ph))
        return yf, 11.0
    if style == 'side_short':
        def yf(ph):
            a = np.abs(ph)
            return np.maximum(np.interp(a, [0, 0.9, 1.15, 1.4, 1.7, 2.3, PI], [-78, -72, -40, -22, -6, 54, 72]), _nape(ph))
        return yf, 8.0
    if style == 'thin':
        def yf(ph):
            a = np.abs(ph)
            return np.maximum(np.interp(a, [0, 0.55, 0.9, 1.25, 1.6, 2.2, PI], [-96, -92, -66, -24, -4, 50, 70]), _nape(ph))
        return yf, 3.5
    if style == 'pony':
        def yf(ph):
            a = np.abs(ph)
            return np.maximum(np.interp(a, [0, 0.6, 0.95, 1.3, 1.7, 2.2, PI], [-80, -74, -48, -12, -2, 40, 62]), _nape(ph))
        return yf, 6.0
    # 'doc'
    def yf(ph):
        a = np.abs(ph)
        return np.maximum(np.interp(a, [0, 0.7, 1.0, 1.3, 1.65, 2.2, PI], [-70, -66, -44, -18, -4, 50, 70]), _nape(ph))
    return yf, 7.0


def _hang_shape(hm, grow, y_bot, flare=8.0, seed=0, mess=0.0):
    """Hair hanging beside the face and behind the jaw down to y_bot: a slab between the head's extents, flared, with an
    uneven (mess) or neat, slightly turned-under hem."""
    w0 = float(hm.W(10.0)) + grow
    xl, xr = hm.extent(w0)
    xl2, xr2 = hm.extent(w0 + flare)
    mid = (xl2 + xr2) * 0.5
    jag = lambda k: (hash01(k + seed, 401) - 0.5) * 18.0 * mess   # noqa: E731
    pts = [(xl, -30.0), (xr, -30.0), (xr2 + 2, y_bot - 18), (xr2 - 4 + jag(1), y_bot + jag(2) * 0.6), (mid + (xr2 - mid) * 0.45, y_bot + 4 + jag(3)),
           (mid, y_bot + 2 + jag(4)), (mid - (mid - xl2) * 0.45, y_bot + 4 + jag(5)), (xl2 + 4 + jag(6), y_bot + jag(7) * 0.6), (xl2 - 2, y_bot - 18)]
    return smooth(pts, True, 0.6)


def _offset_path(path, d):
    """The path grown outward by d (a true offset with round joins: hair caps get a round dome, not a flat top)."""
    if d <= 0: return path
    pt = skia.Paint(Style=skia.Paint.kStroke_Style, StrokeWidth=2.0 * d, StrokeJoin=skia.Paint.kRound_Join, AntiAlias=True)
    out = skia.Path()
    try:
        pt.getFillPath(path, out)
    except TypeError:
        out = pt.getFillPath(path)
    u = union(path, out)
    return u if u is not None else path


def _curtain(hm, grow, y_top, y_bot, phi0=1.0, mess=0.0, seed=0, flare=8.0):
    """Hair hanging round the SIDES and BACK of the head (phi from +phi0 round the back to -phi0), from y_top down to
    y_bot: the projected outline of that curtain (so in profile it hangs behind the face, never in front of it)."""
    ys = np.linspace(y_top, y_bot, 9)
    phis = np.linspace(phi0, 2 * PI - phi0, 25)
    L, R = [], []
    for j, y in enumerate(ys):
        yh = min(y, 60.0)
        w = float(hm.W(yh)) + grow * (0.6 + 0.4 * clamp((y - y_top) / 40.0)) + flare * clamp((y - 40.0) / max(1.0, y_bot - 40.0))
        c_, s_ = np.cos(phis), np.sin(phis)
        d = np.where(c_ > 0, hm.DF, hm.DB)
        px = w * s_; pz = d * w * c_
        y1 = y * hm.cp + pz * hm.spi
        z1 = pz * hm.cp - y * hm.spi
        X = px * hm.ct + z1 * hm.st
        jag = (hash01(j + seed, 409) - 0.5) * 14.0 * mess if j == len(ys) - 1 else 0.0
        i0, i1 = int(np.argmin(X)), int(np.argmax(X))
        L.append((float(X[i0]), float(y1[i0]) + jag)); R.append((float(X[i1]), float(y1[i1]) - jag))
    hem = []
    xl, yl = L[-1]; xr, yr = R[-1]
    for k in range(1, 4):
        u = k / 4.0
        hem.append((xr + (xl - xr) * u, yr + (yl - yr) * u + 5.0 * math.sin(PI * u) + (hash01(k + seed, 413) - 0.5) * 16.0 * mess))
    return smooth(R + hem + L[::-1], True, 0.6)


def _hair3_back(c, hm, sp, P, det, t):
    """Hair behind the skull: the back mass of long styles, pigtails / ponytail / bun when they are behind the head."""
    style = sp['hair']; hc = sp['hair_c']
    hsh = mix(hc, '#000000', 0.42)
    sw = 5.0 * P.sec_x
    mess = clamp(getattr(P, 'mess', 0.0) + (0.6 if style == 'loose' else 0.0))
    if style in _HANG3:
        yb = _HANG3[style] + 4.0 * abs(P.sec_x)
        back = union(_offset_path(hm.silhouette(), _hairline(style, sp['part'])[1] + 1.0), _curtain(hm, 14.0, -70.0, yb, 0.9, mess, 3, 10.0))
        if sw: back = moved_path(back, sw * 0.5, 0)
        c.fill(back, hsh)
        if det >= 1: c.radial(back, 0, 40, 160, [(0, '#000000', 0), (0.7, '#000000', 40), (1, '#000000', 110)], sy=1.2)
        c.line(back, c.lw)
    if style in ('pigtails', 'pigtails_hi'):
        _pigtails(c, hm, sp, P, det, t, behind=True)
    if style == 'pony':
        _ponytail(c, hm, sp, P, det, t, behind=True)
    if style == 'gran_bun':
        _gran_bun(c, hm, sp, det, behind=True)


def _pigtails(c, hm, sp, P, det, t, behind):
    """Two pigtails. 'pigtails' (June): low, behind the ears, hanging down past the shoulders, pink scrunchies.
    'pigtails_hi' (Laurie 1987): high on the sides, sticking out and curling down, big yellow ribbon bows."""
    style = sp['hair']; hc = sp['hair_c']; cl = sp['cloth']
    hsh = mix(hc, '#000000', 0.38); hhi = mix(hc, '#ffffff', 0.3)
    hi = style == 'pigtails_hi'
    for side in (-1, 1):
        phi = side * (1.42 if hi else 1.95)
        y0 = -72.0 if hi else 30.0
        X0, Y0, V0 = _sph(hm, np.array([phi]), np.array([y0]), 6.0)
        X0, Y0, V0 = float(X0[0]), float(Y0[0]), float(V0[0])
        if (V0 < -0.05) != behind: continue
        out = side * (1.0 if hm.ct >= 0 else -1.0)
        # screen direction of "outward" for this side (follows the head's turn)
        ox_, _, oz_ = _rot_head(hm, side * 1.0, 0.0, 0.0)
        ox_ = float(ox_)
        sw = 6.0 * P.sec_x + 3.0 * math.sin(t * 1.7 + side)
        if hi:
            ctrl = [(X0, Y0), (X0 + ox_ * 46 + sw * 0.3, Y0 + 6), (X0 + ox_ * 70 + sw * 0.6, Y0 + 52), (X0 + ox_ * 62 + sw, Y0 + 104)]
            w = [30, 34, 26, 8]
        else:
            ctrl = [(X0, Y0), (X0 + ox_ * 18 + sw * 0.3, Y0 + 40), (X0 + ox_ * 24 + sw * 0.7, Y0 + 96), (X0 + ox_ * 18 + sw, Y0 + 140)]
            w = [24, 30, 24, 6]
        tail = _tube(ctrl, w, 0.9)
        c.fill(tail, hc)
        c.fill(_crescent(tail, ox_ * 6, -4), hsh, 140)
        if det >= 1:
            st = [smooth([(ctrl[0][0] + k * 4, ctrl[0][1] + 6), (ctrl[1][0] + k * 5, ctrl[1][1]), (ctrl[2][0] + k * 4, ctrl[2][1]),
                          (ctrl[3][0] + k * 2, ctrl[3][1] - 8)], False) for k in (-1, 1)]
            c.line(_multi(st), c.lw * 0.35, hsh, 170)
            c.line(smooth([(ctrl[0][0] - ox_ * 4, ctrl[0][1] + 10), (ctrl[1][0] - ox_ * 6, ctrl[1][1] + 4)], False), c.lw * 0.6, hhi, 120)
        c.line(tail, c.lw)
        # the tie: a scrunchie (June) or a big ribbon bow (Laurie)
        tx, ty = X0 + ox_ * (8 if hi else 4), Y0 + (4 if hi else 8)
        tie = cl.get('tie', '#f08aa0')
        if hi:
            for sd in (-1, 1):
                lp = smooth([(tx, ty), (tx + 20 * sd - ox_ * 4, ty - 22), (tx + 30 * sd, ty - 6), (tx + 12 * sd, ty + 6)], True, 0.7)
                c.fill(lp, tie); c.fill(_crescent(lp, 3, 3), mix(tie, '#000000', 0.25), 150); c.line(lp, c.lw * 0.8)
            for sd in (-1, 1):
                rb = poly([(tx + 3 * sd, ty + 4), (tx + 16 * sd + ox_ * 6, ty + 34), (tx + 8 * sd + ox_ * 6, ty + 36), (tx, ty + 8)])
                c.fill(rb, tie); c.line(rb, c.lw * 0.7)
            c.shape(oval(tx, ty, 8, 7), mix(tie, '#ffffff', 0.15), c.lw * 0.7)
        else:
            sc = _blob(tx, ty, 15, 11, 9, side + 2, 0.25)
            c.fill(sc, tie); c.fill(_crescent(sc, 0, -4), mix(tie, '#000000', 0.25), 140); c.line(sc, c.lw * 0.8)


def _ponytail(c, hm, sp, P, det, t, behind):
    hc = sp['hair_c']; hsh = mix(hc, '#000000', 0.4)
    X0, Y0, V0 = _sph(hm, np.array([PI]), np.array([-30.0]), 6.0)
    X0, Y0, V0 = float(X0[0]), float(Y0[0]), float(V0[0])
    if (V0 < 0.1) != behind and abs(hm.st) < 0.3: return
    if not behind and V0 < -0.2 and abs(hm.st) >= 0.3: return
    sw = 8.0 * P.sec_x + 2.0 * math.sin(t * 1.5)
    bx = -hm.st * 18.0
    ctrl = [(X0, Y0), (X0 + bx * 0.6 + sw * 0.3, Y0 + 50), (X0 + bx + sw * 0.7, Y0 + 120), (X0 + bx * 0.8 + sw, Y0 + 190)]
    tail = _tube(ctrl, [30, 34, 24, 6], 0.9)
    c.fill(tail, hc); c.fill(_crescent(tail, 5, -4), hsh, 140)
    c.line(tail, c.lw)
    c.shape(oval(X0, Y0 + 4, 12, 7), '#2b2b33', c.lw * 0.5)


def _gran_bun(c, hm, sp, det, behind):
    X, Y, V = _sph(hm, np.array([PI * 0.92]), np.array([-78.0]), 16.0)
    X, Y, V = float(X[0]), float(Y[0]), float(V[0])
    if (V < 0.25) != behind: return
    hc = sp['hair_c']; hsh = mix(hc, '#000000', 0.3); hhi = mix(hc, '#ffffff', 0.4)
    bun = oval(X, Y - 10, 38 * (0.7 + 0.3 * abs(hm.st)), 32)
    c.fill(bun, hc); c.radial(bun, X - 8, Y - 20, 50, [(0, hhi, 160), (0.6, hc, 0), (1, hsh, 220)])
    if det >= 1:
        c.line(_multi([smooth([(X - 26, Y - 18 + k * 10), (X, Y - 28 + k * 10), (X + 26, Y - 16 + k * 10)], False) for k in range(3)]),
               c.lw * 0.35, hsh, 170)
    c.line(bun, c.lw)


def _hair_region(c, hm, sp, P, det, sil, t):
    style = sp['hair']
    if style not in _HAIR3: return _hair_region_v2(c, hm, sp, P, det, sil, t)
    hc = sp['hair_c']
    hsh = mix(hc, '#000000', 0.36); hhi = mix(hc, '#ffffff', 0.28)
    yf, grow = _hairline(style, sp['part'])
    mess = clamp(getattr(P, 'mess', 0.0) + (0.7 if style == 'loose' else 0.0) + (0.45 if style == 'chin' else 0.0))
    if style in _HANG3:
        # face-framing styles: the hair volume minus a face window cut along the FRONT of the hairline (|phi| < 1.3),
        # extended straight down, so the hair frames the face in a U and hangs past the jaw at the sides
        phis = np.linspace(-1.3, 1.3, 60)
        ys0 = yf(phis)
        Xw, Yw, Vw = _sph(hm, phis, ys0, 0.0)
        m = Vw > -0.02
        vol = union(_offset_path(hm.silhouette(), grow), _curtain(hm, grow, -70.0, _HANG3[style] + 4.0 * abs(P.sec_x), 0.95, mess, 1, 8.0))
        if mess > 0.05: vol = union(vol, _bumpy(hm, grow, 9, 6.0 * mess, -128.0, 60.0, spiky=True, seed=sp['part'] + 3))
        if m.sum() >= 3:
            Xw, Yw = Xw[m], Yw[m]
            if Xw[0] > Xw[-1]: Xw, Yw = Xw[::-1], Yw[::-1]
            win = poly([(float(Xw[0]), 420.0)] + [(float(x), float(y)) for x, y in zip(Xw, Yw)] + [(float(Xw[-1]), 420.0)], True)
            hair = minus(vol, win)
        else:
            hair = vol
    else:
        X, Y = hm.arc_phi(yf, 140)
        if len(X) < 3: return
        region = _region_above(X, Y)
        if style in ('side_short', 'doc', 'thin'):
            vol = _bumpy(hm, grow, 12, 3.0 if style != 'thin' else 1.5, -124.0, 90.0, spiky=False)
        else:
            vol = _offset_path(hm.silhouette(), grow)
        hair = inter(union(vol, sil), region)
    c.fill(hair, hc)
    with c.clip(hair):
        c.radial(None, -30, -92, 180, [(0, hhi, 125), (0.5, hc, 0), (1, hsh, 205)], clip=False)
        if style in ('bob', 'loose', 'chin', 'chin_neat') and det >= 1:      # a soft sheen on the crown
            gx, gy, gv = hm.map1(-30.0, -96.0, grow)
            if gv > 0.0: c.glow(gx, gy, 46, 16, '#ffffff', 34)
        if style == 'side_short' or style == 'doc':
            # grey at the temples
            for sd in (-1, 1):
                gx, gy, gv = hm.map1(sd * 88, -24, grow)
                if gv > -0.2: c.glow(gx, gy, 26, 36, '#cfc9c2', 110 if style == 'side_short' else 60)
        if det >= 1:
            pp = 1.0 if sp['part'] >= 0 else -1.0
            L = []
            if style in ('bob', 'loose', 'chin', 'chin_neat'):
                for k in range(6):                            # strands sweeping from the part over to the fringe side
                    ph = pp * np.linspace(0.3 - 0.02 * k, -0.25 - 0.14 * k, 8)
                    L.append((ph, np.linspace(-118.0, -66.0 + 6 * k, 8)))
                for k in range(4):
                    ph = pp * np.linspace(0.34, 0.65 + 0.12 * k, 6)
                    L.append((ph, np.linspace(-118.0, -70.0 + 6 * k, 6)))
            elif style in ('pigtails', 'pigtails_hi', 'pony', 'gran_bun'):
                for k in range(-4, 5):                        # combed back toward the ties
                    L.append((np.linspace(0.12 * k, 0.4 * k + (0.6 if k > 0 else -0.6), 7), np.linspace(-118.0, -70.0, 7)))
            elif style in ('side_short', 'doc'):
                for k in range(6):
                    ph = np.linspace(-0.5 + 0.18 * k, -0.2 + 0.2 * k, 5)
                    L.append((ph, np.linspace(-122.0, -82.0, 5)))
            elif style == 'thin':
                for k in range(5):
                    L.append((np.linspace(-0.6 + 0.3 * k, -0.4 + 0.3 * k, 5), np.linspace(-118.0, -80.0, 5)))
            _strands(c, hm, L, grow * 0.5, c.lw * 0.32, hsh, 165)
        if style in _HANG3 and det >= 1:                      # long strands down the hanging part
            for sd in (-1, 1):
                xl_, xr_ = hm.extent(float(hm.W(20.0)) + grow * 0.6)
                xe = xr_ if sd > 0 else xl_
                yb = _HANG3[style]
                c.line(smooth([(xe - sd * 6, -10), (xe - sd * 3, yb * 0.45), (xe - sd * 10, yb - 6)], False), c.lw * 0.32, hsh, 160)
                c.line(smooth([(xe - sd * 18, 10), (xe - sd * 14, yb * 0.55), (xe - sd * 20, yb - 2)], False), c.lw * 0.3, hsh, 120)
        if style == 'thin':                                   # greasy grey: a sallow sheen and scalp showing through
            c.fill(hair, '#cdb3a3', 70)
    c.line(hair, c.lw)
    if style in ('pigtails', 'pigtails_hi', 'pony', 'gran_bun'):
        if style == 'pony': _ponytail(c, hm, sp, P, det, t, behind=False)
        elif style == 'gran_bun': _gran_bun(c, hm, sp, det, behind=False)
        else: _pigtails(c, hm, sp, P, det, t, behind=False)
    if style in ('chin', 'loose') and det >= 1 and hm.map1(0, 0)[2] > 0.2:      # a loose strand or two over the face
        pp = 1.0 if sp['part'] >= 0 else -1.0
        n_ = 1 if style == 'chin' else 2
        for k in range(n_):
            ph = -pp * np.linspace(0.42 + 0.14 * k, 0.78 + 0.1 * k, 6)
            ys = np.linspace(-84.0, -10.0 + 22 * k + 30 * mess, 6)
            X_, Y_, V_ = _sph(hm, ph, ys, grow * 0.7)
            m = V_ > 0.0
            if m.sum() > 2:
                q = _pts_path(X_[m], Y_[m], False)
                c.line(q, c.lw * 0.55, mix(hc, '#000000', 0.45), 220); c.line(q, c.lw * 0.28, hc)
    # brows over the fringe so worry / fear always read
    if style in ('bob', 'loose', 'chin', 'pigtails', 'pigtails_hi') and hm.map1(0, 0)[2] > -0.3:
        for side in (-1, 1): _brow(c, hm, sp, P, side, None)


def _nape_cut_v3(hm, sp):
    return None if sp.get('hair') in _HANG3 or sp.get('hair') in ('pigtails', 'pigtails_hi') else _nape_cut_v2(hm, sp)


_nape_cut_v2 = _nape_cut
_nape_cut = _nape_cut_v3


def draw_head_local(c, who, P, yaw, pitch, det, t, light=None, sp=None):
    """Head in head units on Ctx c (see the v2 version). The Bunnyman's foam head and the v3 cast's faces dispatch here:
    v3 heads get their back hair (long styles, pigtails, ponytail, bun) behind the skull, then the v2 head with the v3
    eyes / brows / hair, then earrings."""
    sp = sp or CAST[who]
    if sp.get('bunny'): return _bunny_head(c, who, P, yaw, pitch, det, t, light, sp)
    if sp.get('v3') and sp.get('hair') in _HAIR3 and not getattr(P, '_back_done', False):
        hm = HeadMap(sp, yaw, pitch, jaw=26.0 * clamp(P.m_open) + 5.0 * clamp(P.grin), cheek=clamp(P.grin + 0.4 * max(P.smile, 0.0)))
        _hair3_back(c, hm, sp, P, det, t)
    return _draw_head_local_v2(c, who, P, yaw, pitch, det, t, light, sp)


# ====================================================================================================== v3 bodies
def _rows3(sp, B):
    """Torso rows (y, half width, half depth) for the v3 outfits."""
    o = sp['outfit']
    if o == 'police': return _torso_rows(sp, B)
    b = sp['body']; k = B.chest_k
    ys = [B.y_sh - 30, B.y_sh - 10, B.y_sh + 16, B.y_ch, B.y_ch + 80, B.y_wa, B.y_belt, B.y_hip]
    add = {'cardigan3': (18, 0.88, 3, 4, 4, 4, 4, 4), 'hoodie3': (26, 0.92, 10, 14, 16, 18, 16, 12),
           'pj3': (14, 0.88, 2, 4, 6, 8, 8, 6), 'dress3': (12, 0.86, 0, 0, -2, -6, -2, 0), 'gran3': (20, 0.88, 2, 6, 6, 6, 6, 6),
           'jacket3': (26, 0.92, 8, 10, 8, 10, 10, 8), 'labcoat3': (26, 0.92, 8, 10, 10, 12, 12, 10),
           'scrubs3': (16, 0.88, 4, 8, 8, 10, 10, 8), 'gown3': (12, 0.86, -2, 0, 2, 10, 10, 10), 'neat3': (18, 0.88, 2, 4, 2, 2, 4, 4)}
    a = add.get(o, (16, 0.84, 0, 0, 0, 0, 0, 0))
    ws = [b['neck'] + a[0], b['sh'] * a[1], b['sh'] + a[2], b['ch'] * k + a[3], b['ch'] * 0.97 * k + a[4], b['wa'] + a[5],
          b['hip'] * 0.98 + a[6], b['hip'] + a[7]]
    if ys[4] >= ys[5] - 4: ys[4] = (ys[3] + ys[5]) * 0.5
    ds = [w * f for w, f in zip(ws, [0.55, 0.52, 0.5, 0.56, 0.6, 0.6, 0.62, 0.64])]
    return ys, ws, ds


_LEGS3 = {'dress3': 'skin', 'gown3': 'skin', 'gran3': 'skin'}


def _limb_cols3(sp):
    cl = sp['cloth']; o = sp['outfit']
    sleeve, sleeve_sh = cl.get('top', '#777'), cl.get('top_sh', '#555')
    if o == 'police': sleeve, sleeve_sh = cl['shirt'], cl['shirt_sh']
    if o == 'jacket3': sleeve, sleeve_sh = cl['top'], cl['top_sh']
    if _LEGS3.get(o) == 'skin':
        legc, legsh = cl.get('legs', sp['skin']), cl.get('legs_sh', sp['skin_sh'])
    else:
        legc, legsh = cl.get('trousers', '#333'), cl.get('trousers_sh', '#222')
    return sleeve, sleeve_sh, legc, legsh, cl.get('shoes', '#222')


def _neck3(c, sp, B, skin, skin_sh):
    nb = B.p3(0, B.y_sh - 34, 0); nt = B.p3(0, B.yc - 30, 0)
    nw = sp['body']['neck']
    neck = _tube([(nb[0], nb[1]), (nt[0], nt[1])], [nw * 2 * nb[2], nw * 1.9 * nt[2]])
    c.fill(neck, skin)
    c.grad(neck, 0, nt[1] - 10, 0, nb[1], [(0, mix(skin_sh, '#000000', 0.2), 255), (0.6, skin_sh, 160), (1, skin, 0)])
    c.line(neck, c.lw)
    return nb, nt


def _head_xf(sp, B, P):
    """(x, y, rotation, scale) of the head frame (as v2 _figure places it)."""
    pv = B.p3(0, B.yc - 22 + P.h_dy, 0)
    hs = sp['hh'] / 240.0 * pv[2] * P.h_scale
    head_rot = P.tilt + P.h_tilt
    arm_ = (sp['hh'] / 2 - 22) * pv[2] * P.h_scale
    ra = math.radians(head_rot)
    return pv[0] + P.h_dx + math.sin(ra) * arm_, pv[1] - math.cos(ra) * arm_, head_rot, hs


def _figure3(c, who, P, det, t, light=None, upper_only=False):
    """A v3 cast member in body units on Ctx c (feet at y=0, crown at y=-1000): back hair (behind the neck), arms behind,
    legs (Body3: seat anchor, kneels, planted walk), skirts / coat tails, neck, torso with the outfit's front, head, arms
    in front. Outfits: cardigan3, hoodie3, pj3, dress3, gran3, jacket3, labcoat3, scrubs3, gown3, neat3, police."""
    sp = CAST[who]
    B = Body(sp, P)
    skin, skin_sh, _ = _skin_cols(sp, P, light)
    sleeve, sleeve_sh, legc, legsh, shoec = _limb_cols3(sp)
    rows = _rows3(sp, B)
    cl = sp['cloth']; o = sp['outfit']
    arm_z = {}
    for side in (-1, 1):
        S, E, Wr = _arm_data(sp, B, P, side)
        arm_z[side] = (B.p3(*S)[3], B.p3(*Wr)[3])
    behind = [s_ for s_ in (-1, 1) if arm_z[s_][0] < -20 and arm_z[s_][1] < 40]
    front = sorted([s_ for s_ in (-1, 1) if s_ not in behind], key=lambda s_: arm_z[s_][1])
    back_view = B.ct < -0.15
    hx, hy, hrot, hs = _head_xf(sp, B, P)
    yaw = (P.turn + P.h_turn) * PI / 2
    hc = c.sub(hx, hy, hrot, hs)
    # back hair behind neck and shoulders (long styles, pigtails, ponytail, bun)
    if sp.get('hair') in _HAIR3:
        hm0 = HeadMap(sp, yaw, P.h_nod * 0.6, jaw=26.0 * clamp(P.m_open) + 5.0 * clamp(P.grin), cheek=clamp(P.grin + 0.4 * max(P.smile, 0.0)))
        _hair3_back(hc, hm0, sp, P, det, t)
    for side in behind: _draw_arm3(c, sp, B, P, side, det, t, skin, skin_sh, sleeve, sleeve_sh, light)
    if not upper_only:
        _draw_legs3(c, sp, B, P, det, t, legc, legsh, shoec)
        if _LEGS3.get(o) != 'skin': _pelvis(c, sp, B, rows, legc, legsh, det)
        _skirts3(c, sp, B, P, det, t, rows)
    elif o not in ('gown3', 'dress3', 'labcoat3'):
        _pelvis(c, sp, B, rows, legc, legsh, det)
    if o == 'hoodie3': _hood_back(c, sp, B, det)
    _neck3(c, sp, B, skin, skin_sh)
    torso, L, R = _torso_path(B, rows)
    top, topsh, tophi = cl.get('top'), cl.get('top_sh'), cl.get('top_hi')
    if o == 'police': top, topsh, tophi = cl['shirt'], cl['shirt_sh'], cl['shirt_hi']
    c.fill(torso, top)
    c.grad(torso, L[3][0] - 10, 0, R[3][0] + 10, 0, [(0, tophi, 90), (0.35, top, 0), (0.7, topsh, 60), (1, topsh, 200)])
    with c.clip(torso):
        c.grad(rect(-400, B.y_wa - 10 + B.bob, 800, 300), 0, B.y_wa - 60 + B.bob, 0, B.y_hip + B.bob, [(0, topsh, 0), (1, topsh, 130)])
        if det >= 1: c.texture(torso, 'fabric', 0.09 if o in ('cardigan3', 'gran3', 'hoodie3', 'neat3') else 0.06, 0.6)
        if o == 'pj3' and det >= 1: _egg_print(c, B, rows, cl, back_view)
        if o == 'gown3': _gown_print(c, B, rows, cl, det, torso)
        if det >= 1:                                          # armpit creases
            for side in (-1, 1):
                p0 = B.surf(side * (sp['body']['ch'] * 0.78), B.y_ch - 10, 1, back_view, rows)
                p1 = B.surf(side * (sp['body']['ch'] * 0.5), B.y_ch + 34, 1, back_view, rows)
                c.line(smooth([(p0[0], p0[1]), ((p0[0] + p1[0]) / 2 + side * 4, (p0[1] + p1[1]) / 2), (p1[0], p1[1])], False), c.lw * 0.4, LINE, 120)
        if light and light.get('rim'):
            rs = light.get('side', 1)
            c.fill(_crescent(torso, -rs * 9, 0), light['rim'], light.get('rim_a', 70) * 0.8)
    c.line(torso, c.lw)
    if not back_view:
        f = _FRONTS3.get(o)
        if f: f(c, sp, B, rows, P, det, t)
    else:
        yy = B.y_sh + 30
        sm, v = _surf_poly(B, rows, [(-sp['body']['sh'] * 0.8, yy), (0, yy + 12), (sp['body']['sh'] * 0.8, yy)], back=True, dz=1)
        c.line(smooth(sm, False), c.lw * 0.4, LINE, 140)
        if o == 'dress3': _dress_back_bow(c, sp, B, rows, det, t)
    if o == 'police':
        _police_belt(c, sp, B, rows, P, det, back_view)
    if o == 'hoodie3' and not back_view: _hood_front(c, sp, B, det)
    # head (its back hair is already drawn)
    Pq = P
    try:
        Pq._back_done = True
        draw_head_local(hc, who, Pq, yaw, P.h_nod * 0.6, det, t, light, sp)
    finally:
        Pq.__dict__.pop('_back_done', None)
    if o == 'labcoat3' and not back_view: _stethoscope(c, sp, B, rows, det)
    for side in front: _draw_arm3(c, sp, B, P, side, det, t, skin, skin_sh, sleeve, sleeve_sh, light)
    return B


def _egg_print(c, B, rows, cl, back):
    """June's pajamas: a scatter of tiny pastel Easter eggs."""
    ys, ws, ds = rows
    a_, b_ = [], []
    for k in range(18):
        x0 = (hash01(k, 151) * 2 - 1) * 0.86; y0 = ys[1] + (ys[-1] - ys[1]) * (0.06 + 0.88 * hash01(k, 152))
        w = float(np.interp(y0, ys, ws))
        X, Y, v, s_ = B.surf(x0 * w, y0, 2, back, rows)
        if v < 0.1: continue
        e = oval(X, Y, 5.0 * s_ * max(0.4, abs(B.ct)), 7.0 * s_)
        (a_ if k % 2 else b_).append(e)
    if a_: c.fill(_multi(a_), cl.get('print_c', '#f2a5b5'), 230)
    if b_: c.fill(_multi(b_), cl.get('print_c2', '#f6d978'), 230)


def _hood_back(c, sp, B, det):
    """The narrator's hood lying behind the neck (drawn before the neck)."""
    cl = sp['cloth']
    nb = B.p3(0, B.y_sh - 34, 0)
    nw = sp['body']['neck']
    hood = smooth([(nb[0] - (nw + 50) * nb[2], nb[1] + 10), (nb[0] - (nw + 36) * nb[2], nb[1] - 50), (nb[0], nb[1] - 66 - 10 * (B.ct < 0)),
                   (nb[0] + (nw + 36) * nb[2], nb[1] - 50), (nb[0] + (nw + 50) * nb[2], nb[1] + 10)], True, 0.8)
    c.fill(hood, cl['hood']); c.fill(_crescent(hood, 0, 10), cl['hood_sh'], 160); c.line(hood, c.lw)


def _hood_front(c, sp, B, det):
    """The hood's rim round the neck in front and the drawstrings."""
    cl = sp['cloth']; b = sp['body']
    nb = B.p3(0, B.y_sh - 30, 0)
    w = (b['neck'] + 30) * nb[2] * math.sqrt(B.ct ** 2 + 0.5 * B.st ** 2)
    rim = smooth([(nb[0] - w, nb[1] - 14), (nb[0] - w * 0.6, nb[1] + 22), (nb[0], nb[1] + 34), (nb[0] + w * 0.6, nb[1] + 22), (nb[0] + w, nb[1] - 14),
                  (nb[0] + w * 0.55, nb[1] + 6), (nb[0], nb[1] + 14), (nb[0] - w * 0.55, nb[1] + 6)], True, 0.7)
    c.fill(rim, cl['hood']); c.fill(_crescent(rim, 0, -5), cl['hood_sh'], 140); c.line(rim, c.lw * 0.9)
    if B.ct > 0.2:
        for sd in (-1, 1):
            x0 = nb[0] + sd * 14 * B.ct
            sw = 4.0 * sd + 6.0 * getattr(B.P, 'sec_x', 0.0)
            pts = [(x0, nb[1] + 24), (x0 + sw * 0.5, nb[1] + 80), (x0 + sw, nb[1] + 130)]
            c.line(smooth(pts, False), c.lw * 1.9, LINE); c.line(smooth(pts, False), c.lw * 1.0, cl['string'])
            c.fill(rrect(pts[-1][0] - 4, pts[-1][1], 8, 14, 3), '#b8b2a4'); c.line(rrect(pts[-1][0] - 4, pts[-1][1], 8, 14, 3), c.lw * 0.5)


def _front_hoodie3(c, sp, B, rows, P, det, t):
    cl = sp['cloth']; b = sp['body']
    pk, v = _surf_poly(B, rows, [(-b['wa'] * 0.62, B.y_wa - 20), (b['wa'] * 0.62, B.y_wa - 20), (b['wa'] * 0.74, B.y_hip - 24),
                                 (-b['wa'] * 0.74, B.y_hip - 24)], dz=4)
    if v > 0.05:
        q = smooth(pk, True, 0.25); c.fill(q, mix(cl['top'], '#000000', 0.06)); c.line(q, c.lw * 0.6)
        if det >= 1:
            for sd in (-1, 1):
                a_, _ = _surf_poly(B, rows, [(sd * b['wa'] * 0.62, B.y_wa - 20), (sd * b['wa'] * 0.7, B.y_hip - 26)], dz=5)
                c.line(poly(a_, False), c.lw * 0.5, cl['top_sh'])
    hem, v = _surf_poly(B, rows, [(-b['hip'] - 14, B.y_hip - 20), (b['hip'] + 14, B.y_hip - 20)], dz=2)
    if v > -0.2 and det >= 1: c.line(poly(hem, False), c.lw * 0.5, LINE, 180)


def _front_cardigan3(c, sp, B, rows, P, det, t):
    """Mom's cardigan: a narrow V opening on the cream blouse with its round collar, five pearl buttons, ribbed hem."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    vneck, v = _surf_poly(B, rows, [(-b['neck'] - 8, yS - 30), (b['neck'] + 8, yS - 30), (6, yC - 4), (-6, yC - 4)], dz=2)
    if v > 0.0:
        q = smooth(vneck, True, 0.2); c.fill(q, cl['blouse']); c.fill(_crescent(q, -6, 0), cl['blouse_sh'], 120)
        for sd in (-1, 1):                                    # round collar flaps
            cc, _ = _surf_poly(B, rows, [(0, yS - 24), (sd * (b['neck'] + 8), yS - 30), (sd * (b['neck'] + 16), yS - 10),
                                         (sd * 18, yS + 6), (sd * 2, yS - 6)], dz=5)
            cp = smooth(cc, True, 0.8); c.fill(cp, cl['blouse']); c.line(cp, lw * 0.55)
        c.line(q, lw * 0.6)
    for sd in (-1, 1):
        ed, v = _surf_poly(B, rows, [(sd * (b['neck'] + 8), yS - 30), (sd * 6, yC - 4), (sd * 3, B.y_hip - 22)], dz=3)
        if v > -0.2:
            c.line(poly(ed, False), lw * 2.4, LINE); c.line(poly(ed, False), lw * 1.2, cl['rib'])
    for k in range(5):
        X, Y, vv, s_ = B.surf(0, yC + 6 + k * (B.y_hip - 40 - yC) / 4.5, 6, False, rows)
        if vv > 0.12: c.shape(oval(X, Y, 5.0 * s_), cl['button'], lw * 0.4)
    if det >= 1:
        rb = []
        for k in range(-7, 8):
            pts, v = _surf_poly(B, rows, [(k * 15, B.y_hip - 44), (k * 15, B.y_hip - 18)], dz=1)
            if v > 0.1: rb.append(poly(pts, False))
        if rb: c.line(_multi(rb), lw * 0.3, cl['top_sh'], 170)
        hem, v = _surf_poly(B, rows, [(-b['hip'] - 6, B.y_hip - 44), (b['hip'] + 6, B.y_hip - 44)], dz=1)
        if v > -0.2: c.line(poly(hem, False), lw * 0.4, LINE, 190)


def _front_neat3(c, sp, B, rows, P, det, t):
    """The thing in the narrator's body at the hospital: a pressed cream cardigan buttoned over a white collar."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    vneck, v = _surf_poly(B, rows, [(-b['neck'] - 4, yS - 30), (b['neck'] + 4, yS - 30), (4, yS + 40), (-4, yS + 40)], dz=2)
    if v > 0.0:
        q = smooth(vneck, True, 0.2); c.fill(q, cl['collar'])
        for sd in (-1, 1):
            cc, _ = _surf_poly(B, rows, [(sd * 2, yS - 26), (sd * (b['neck'] + 6), yS - 34), (sd * (b['neck'] + 10), yS - 8), (sd * 6, yS + 10)], dz=5)
            cp = poly(cc, True); c.fill(cp, cl['collar']); c.line(cp, lw * 0.55)
        c.line(q, lw * 0.5)
    ed, v = _surf_poly(B, rows, [(0, yS + 40), (0, B.y_hip - 20)], dz=3)
    if v > -0.2: c.line(poly(ed, False), lw * 0.6)
    for k in range(5):
        X, Y, vv, s_ = B.surf(0, yS + 54 + k * (B.y_hip - 70 - yS) / 4.5, 6, False, rows)
        if vv > 0.12: c.shape(oval(X, Y, 4.5 * s_), cl['button'], lw * 0.35)


def _front_pj3(c, sp, B, rows, P, det, t):
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    for side in (-1, 1):
        cc, v = _surf_poly(B, rows, [(side * 2, yS - 22), (side * (b['neck'] + 10), yS - 30), (side * (b['neck'] + 16), yS - 6),
                                     (side * 26, yS + 18), (side * 4, yS + 6)], dz=5)
        if v > -0.2:
            cp = smooth(cc, True, 0.7); c.fill(cp, cl['top_hi']); c.line(cp, lw * 1.1, cl['trim']); c.line(cp, lw * 0.5)
    pts, v = _surf_poly(B, rows, [(0, yS + 8), (0, B.y_hip - 20)])
    if v > 0.05:
        c.line(poly(pts, False), lw * 1.3, cl['trim'], 220)
        for k in range(4):
            X, Y, vv, s_ = B.surf(0, yC - 20 + k * 52, 3, False, rows)
            if vv > 0.1: c.fill(oval(X, Y, 5 * s_), '#ffffff'); c.line(oval(X, Y, 5 * s_), lw * 0.35)


def _front_dress3(c, sp, B, rows, P, det, t):
    """The yellow Easter dress: a white round collar, three tiny buttons, a white sash at the waist."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS = B.y_sh
    for side in (-1, 1):
        cc, v = _surf_poly(B, rows, [(side * 1, yS - 24), (side * (b['neck'] + 8), yS - 32), (side * (b['neck'] + 24), yS - 6),
                                     (side * 30, yS + 24), (side * 4, yS + 8)], dz=6)
        if v > -0.2:
            cp = smooth(cc, True, 0.85); c.fill(cp, cl['collar']); c.fill(_crescent(cp, 0, -4), cl['collar_sh'], 140); c.line(cp, lw * 0.6)
    for k in range(3):
        X, Y, vv, s_ = B.surf(0, yS + 26 + k * 26, 4, False, rows)
        if vv > 0.12: c.shape(oval(X, Y, 3.6 * s_), cl['collar'], lw * 0.35)
    sash, v = _surf_poly(B, rows, [(-b['wa'] - 6, B.y_wa - 14), (b['wa'] + 6, B.y_wa - 14), (b['wa'] + 6, B.y_wa + 16), (-b['wa'] - 6, B.y_wa + 16)], dz=3)
    if v > -0.2:
        q = smooth(sash, True, 0.2); c.fill(q, cl['sash']); c.fill(_crescent(q, 0, -4), cl['collar_sh'], 120); c.line(q, lw * 0.6)
    if det >= 1:                                         # a few soft gathers on the bodice
        g = []
        for k in (-2, -1, 1, 2):
            pts, v = _surf_poly(B, rows, [(k * 16, B.y_ch + 20), (k * 18, B.y_wa - 16)], dz=1)
            if v > 0.1: g.append(poly(pts, False))
        if g: c.line(_multi(g), lw * 0.3, cl['top_sh'], 150)


def _dress_back_bow(c, sp, B, rows, det, t):
    cl = sp['cloth']; b = sp['body']
    X, Y, vv, s_ = B.surf(0, B.y_wa, 6, True, rows)
    if vv < 0.1: return
    for sd in (-1, 1):
        lp = smooth([(X, Y), (X + sd * 30 * s_, Y - 18 * s_), (X + sd * 36 * s_, Y + 8 * s_), (X + sd * 8 * s_, Y + 4 * s_)], True, 0.7)
        c.fill(lp, cl['sash']); c.line(lp, c.lw * 0.6)
        tl = poly([(X + sd * 4 * s_, Y + 4 * s_), (X + sd * 18 * s_, Y + 54 * s_), (X + sd * 8 * s_, Y + 56 * s_), (X, Y + 6 * s_)])
        c.fill(tl, cl['sash']); c.line(tl, c.lw * 0.5)


def _front_gran3(c, sp, B, rows, P, det, t):
    """Grandma: a lavender cardigan open on a flowered cream blouse, a gold brooch at the collar."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    op, v = _surf_poly(B, rows, [(-26, yS - 28), (26, yS - 28), (20, B.y_hip - 18), (-20, B.y_hip - 18)], dz=2)
    if v > 0.05:
        q = smooth(op, True, 0.2); c.fill(q, cl['blouse'])
        if det >= 1:
            fl, f2 = [], []
            bb = q.getBounds()
            for k in range(14):
                x_ = bb.left() + bb.width() * hash01(k, 171); y_ = bb.top() + bb.height() * hash01(k, 172)
                (fl if k % 3 else f2).append(oval(x_, y_, 3.6, 3.6))
            with c.clip(q):
                c.fill(_multi(fl), cl['flower'], 220); c.fill(_multi(f2), cl['flower2'], 220)
        c.line(q, lw * 0.5)
        X, Y, vv, s_ = B.surf(0, yS - 10, 7, False, rows)
        if vv > 0.1:
            c.shape(oval(X, Y, 8 * s_, 7 * s_), cl['brooch'], lw * 0.45)
            if det >= 1: c.fill(oval(X - 2 * s_, Y - 2 * s_, 2.5 * s_), '#fff2c0')
    for sd in (-1, 1):
        ed, v = _surf_poly(B, rows, [(sd * 26, yS - 28), (sd * 20, B.y_hip - 18)], dz=4)
        if v > -0.2: c.line(poly(ed, False), lw * 2.4, LINE); c.line(poly(ed, False), lw * 1.2, cl['top_hi'])


def _front_jacket3(c, sp, B, rows, P, det, t):
    """Dad's canvas work jacket hanging open on a charcoal henley; corduroy collar, chest pockets with flaps."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    op, v = _surf_poly(B, rows, [(-34, yS - 30), (34, yS - 30), (40, B.y_hip - 10), (-40, B.y_hip - 10)], dz=2)
    if v > 0.05:
        q = smooth(op, True, 0.2); c.fill(q, cl['shirt']); c.fill(_crescent(q, -8, 0), cl['shirt_sh'], 140); c.line(q, lw * 0.5)
        pl, _ = _surf_poly(B, rows, [(0, yS - 26), (0, yS + 40)], dz=3)
        c.line(poly(pl, False), lw * 0.5)
        for k in range(3):
            X, Y, vv, s_ = B.surf(0, yS - 10 + k * 18, 4, False, rows)
            if vv > 0.1: c.fill(oval(X, Y, 3 * s_), '#8a8478')
    for sd in (-1, 1):
        col_, v = _surf_poly(B, rows, [(sd * 30, yS - 34), (sd * (b['neck'] + 30), yS - 40), (sd * (b['neck'] + 40), yS + 6), (sd * 40, yS + 54)], dz=7)
        if v > -0.2:
            cp = smooth(col_, True, 0.4); c.fill(cp, cl['collar']); c.line(cp, lw * 0.7)
        ed, v = _surf_poly(B, rows, [(sd * 40, yS + 54), (sd * 42, B.y_hip - 10)], dz=4)
        if v > -0.2: c.line(poly(ed, False), lw * 1.3)
        pk, v = _surf_poly(B, rows, [(sd * 58, yC - 14), (sd * 104, yC - 14), (sd * 104, yC + 46), (sd * 58, yC + 46)], dz=3)
        if v > 0.05:
            c.line(poly(pk), lw * 0.5)
            fl, _ = _surf_poly(B, rows, [(sd * 56, yC - 16), (sd * 106, yC - 16), (sd * 106, yC + 6), (sd * 56, yC + 6)], dz=4)
            c.shape(poly(fl), cl['top_sh'], lw * 0.5)
            X, Y, vv, s_ = B.surf(sd * 81, yC + 2, 5, False, rows)
            if vv > 0.1: c.fill(oval(X, Y, 3.5 * s_), cl['button'])
    if det >= 1:
        hem, v = _surf_poly(B, rows, [(-b['hip'] - 10, B.y_hip - 14), (b['hip'] + 10, B.y_hip - 14)], dz=2)
        if v > -0.2: c.line(poly(hem, False), lw * 0.4, LINE, 180)


def _front_labcoat3(c, sp, B, rows, P, det, t):
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    op, v = _surf_poly(B, rows, [(-30, yS - 30), (30, yS - 30), (14, B.y_ch + 60), (-14, B.y_ch + 60)], dz=2)
    if v > 0.05:
        q = smooth(op, True, 0.2); c.fill(q, cl['shirt']); c.line(q, lw * 0.5)
        tie, _ = _surf_poly(B, rows, [(-7, yS - 22), (7, yS - 22), (11, yC + 40), (0, yC + 56), (-11, yC + 40)], dz=4)
        c.shape(poly(tie), cl['tie'], lw * 0.5)
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
    bd, v = _surf_poly(B, rows, [(-96, yC - 10), (-58, yC - 10), (-58, yC + 16), (-96, yC + 16)], dz=4)
    if v > 0.05: c.shape(poly(bd), cl['badge'], lw * 0.4); c.fill(poly(bd[:2] + [(bd[1][0], bd[1][1] + 6), (bd[0][0], bd[0][1] + 6)]), '#2a4a9a', 200)


def _stethoscope(c, sp, B, rows, det):
    pts, v = _surf_poly(B, rows, [(-40, B.y_sh - 26), (-58, B.y_sh + 30), (-46, B.y_ch + 70)], dz=10)
    pts2, v2 = _surf_poly(B, rows, [(40, B.y_sh - 26), (58, B.y_sh + 30), (44, B.y_ch + 50)], dz=10)
    if min(v, v2) < 0.05: return
    for p_ in (pts, pts2):
        c.line(smooth(p_, False), c.lw * 2.0, LINE); c.line(smooth(p_, False), c.lw * 1.1, '#2b2d33')
    x_, y_ = pts[-1]
    c.shape(oval(x_, y_ + 8, 11, 11), '#b9bec6', c.lw * 0.6)


def _front_scrubs3(c, sp, B, rows, P, det, t):
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    vn, v = _surf_poly(B, rows, [(-b['neck'] - 4, yS - 30), (0, yS + 40), (b['neck'] + 4, yS - 30)], dz=3)
    if v > -0.2:
        c.fill(poly(vn, True), sp['skin']); c.line(poly(vn, False), lw * 0.9)
    pk, v = _surf_poly(B, rows, [(-96, yC), (-56, yC), (-56, yC + 46), (-96, yC + 46)], dz=3)
    if v > 0.05: c.line(poly(pk), lw * 0.5)
    ly, v = _surf_poly(B, rows, [(-b['neck'] + 2, yS - 28), (-10, yC + 30), (b['neck'] - 2, yS - 28)], dz=8)
    if v > 0.05:
        c.line(poly(ly, False), lw * 1.2, cl['lanyard'])
        x_, y_ = ly[1]
        c.shape(rrect(x_ - 14, y_, 28, 38, 4), cl['badge'], lw * 0.5)
        c.fill(rect(x_ - 14, y_, 28, 9), cl['lanyard'])


def _front_gown3(c, sp, B, rows, P, det, t):
    _gown_front(c, sp, B, rows, P, det, t)


def _front_police(c, sp, B, rows, P, det, t):
    _police_front(c, sp, B, rows, P, det, t)


_FRONTS3 = {'hoodie3': _front_hoodie3, 'cardigan3': _front_cardigan3, 'neat3': _front_neat3, 'pj3': _front_pj3,
            'dress3': _front_dress3, 'gran3': _front_gran3, 'jacket3': _front_jacket3, 'labcoat3': _front_labcoat3,
            'scrubs3': _front_scrubs3, 'gown3': _front_gown3, 'police': _front_police}


def _skirts3(c, sp, B, P, det, t, rows):
    """Skirts, the dress's full skirt (white lace hem), the gown, the lab coat's tails; seated / kneeling they drape forward
    over the thighs."""
    o = sp['outfit']; cl = sp['cloth']; b = sp['body']
    st = clamp(B.sit + 0.8 * B.kneel)
    if o == 'dress3':
        hem = -262.0 + 150.0 * st
        p = _skirt(c, sp, B, det, B.y_wa + 8, hem, b['wa'] * 1.02, b['hip'] * 1.62 + 30 * st, cl['top'], cl['top_sh'], t=t, P=P)
        bb = p.getBounds()
        X1, Y1, s1, _ = B.p3(0, hem, 0, upper=False)
        hw = math.sqrt((b['hip'] * 1.62 * B.ct) ** 2 + (b['hip'] * 1.62 * 0.66 * B.st) ** 2) * s1 + 30 * st
        sw = (P.sec_x * 10) - B.st * 8 * B.walk
        lace = []
        n = 9
        for k in range(n + 1):
            u = k / n
            x_ = X1 - hw + 2 * hw * u + sw
            lace.append(oval(x_, Y1 + 4, hw / n * 1.05, 9))
        lp = _multi(lace)
        c.fill(lp, cl['lace']); c.line(lp, c.lw * 0.35, LINE, 160)
        return
    if o == 'gran3':
        _skirt(c, sp, B, det, B.y_wa + 10, -170 + 120 * st, b['hip'] * 1.0, b['hip'] * 1.2 + 40 * st, cl['skirt'], cl['skirt_sh'], t=t, P=P)
        return
    if o == 'gown3':
        g = _skirt(c, sp, B, det, B.y_wa + 10, -300 + 130 * st, b['hip'] * 1.08, b['hip'] * 1.2 + 50 * st, cl['top'], cl['top_sh'], t=t, P=P)
        _gown_print(c, B, rows, cl, det, g)
        return
    if o == 'labcoat3':
        X0, Y0, _, _ = B.p3(0, B.y_wa, 0)
        cs = _skirt(c, sp, B, det, B.y_wa, -330 + 120 * st, b['wa'] + 12, b['hip'] * 1.3 + 40 * st, cl['top'], cl['top_sh'], t=t, P=P)
        if B.ct > -0.15:
            X1, Y1, _, _ = B.p3(0, -330 + 120 * st, 0, upper=False)
            gap = poly([(X0 - 14, Y0), (X0 + 14, Y0), (X1 + 30, Y1 + 8), (X1 - 30, Y1 + 8)])
            c.fill(gap, cl['trousers'])
            c.line(poly([(X0 - 14, Y0), (X1 - 30, Y1 + 6)], False), c.lw * 0.8); c.line(poly([(X0 + 14, Y0), (X1 + 30, Y1 + 6)], False), c.lw * 0.8)



# ====================================================================================================== v3 arms
_arm_data_v2 = _arm_data


def _arm_data(sp, B, P, side):
    """v3 cast and the Bunnyman: as _arm_data_v2, but a hand held out in front of the body (an egg, a cup, a notebook, a
    knob) drops its elbow: the IK pole swings from out-and-back to down-and-a-little-out instead of winging the elbow
    out sideways. Raised hands and the phone at the ear keep their own elbows; older casts are unchanged."""
    if not (sp.get('v3') or sp.get('bunny')): return _arm_data_v2(sp, B, P, side)
    b = sp['body']
    pre = 'hl_' if side > 0 else 'hr_'
    g = lambda k: getattr(P, pre + k)   # noqa: E731
    sx = side * (b['sh'] - 17)
    S = np.array([sx, B.y_sh + 20, 0.0])
    swing = 0.0
    if B.walk > 0:
        swing = -60.0 * B.walk * math.cos(B.leg_phase(-side))
    H = S + np.array([side * g('out'), g('down'), g('fwd') + swing])
    shk = getattr(P, pre + 'shake', 0.0)
    if shk > 0.01:
        tt_ = P.t
        H = H + np.array([5.0 * shk * math.sin(tt_ * 61.0) + 3.0 * shk * noise1(tt_ * 13.0, 5 + side),
                          4.0 * shk * math.sin(tt_ * 73.0 + 1.3), 3.0 * shk * noise1(tt_ * 11.0, 9 + side)])
    pole = np.array([side * 0.75, 0.25, -0.65])
    kup = clamp((S[1] - H[1] - 10.0) / 60.0)
    kf = clamp((H[2] - S[2] - 50.0) / 110.0) * (1.0 - kup)          # hand forward of the shoulder: elbow down
    if kf > 0: pole = pole + (np.array([side * 0.32, 1.0, -0.38]) - pole) * kf
    if kup > 0: pole = pole + (np.array([side * 0.7, 1.0, 0.25]) - pole) * kup
    ear = _ear_weight(P, side)
    if ear > 0:
        hh = sp['hh']
        hw = float(np.interp(4.0, sp['head_ys'], sp['head_ws'])) * hh / 240.0
        hy = P.h_turn * PI / 2
        ex = side * (hw * 1.0 + 9.0) * math.cos(hy) + P.h_dx
        ey = B.yc - hh / 2 + 3.0 * hh / 240.0 + P.h_dy
        He = np.array([ex + side * 4.0, ey + 0.31 * hh, 26.0 - side * hw * 0.9 * math.sin(hy)])
        H = H + (He - H) * ear
        pole = pole + (np.array([side * 0.2, 1.0, 0.75]) - pole) * ear
    ak = b.get('arm_k', 1.0) * (1.0 + max(0.0, getattr(P, pre + 'stretch', 0.0)))
    E, Wp = _ik(S, H, 182.0 * ak, 166.0 * ak, pole)
    return S, E, Wp


_SLEEVES3 = {'cardigan3': 'long', 'hoodie3': 'over', 'pj3': 'long', 'dress3': 'puff', 'gran3': 'long', 'jacket3': 'long',
             'labcoat3': 'long', 'scrubs3': 'short', 'gown3': 'short', 'neat3': 'long', 'police': 'long'}


def _arm_pt(P2, u):
    """Point (x, y) at fraction u (0 shoulder .. 1 wrist, > 1 past the wrist along the forearm) of a 2D arm polyline."""
    (sx, sy), (ex, ey), (wx, wy) = P2[-3], P2[-2], P2[-1]
    L1 = math.hypot(ex - sx, ey - sy); L2 = math.hypot(wx - ex, wy - ey) or 1.0
    d = u * (L1 + L2)
    if d <= L1:
        k = d / (L1 or 1.0); return sx + (ex - sx) * k, sy + (ey - sy) * k
    k = (d - L1) / L2
    return ex + (wx - ex) * k, ey + (wy - ey) * k


def _scratches(c, P2, widths, u0, det, amt, seed=0):
    """Mom's forearms scratched to ribbons: thin raw red lines (some beaded) across the bare forearm from u0 to the wrist."""
    if amt <= 0.01: return
    ls, beads = [], []
    n = int(5 + 9 * amt)
    for k in range(n):
        u = u0 + (0.97 - u0) * (k + 0.5) / n
        x, y = _arm_pt(P2, u)
        x2, y2 = _arm_pt(P2, min(0.99, u + 0.04))
        dx, dy = x2 - x, y2 - y; L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        w = widths[2] * 0.42
        j = (hash01(k + seed, 431) - 0.5) * 2
        a = (x - nx * w * 0.9 + dx / L * 6 * j, y - ny * w * 0.9 + dy / L * 6 * j)
        b = (x + nx * w * 0.8 - dx / L * 10 * j, y + ny * w * 0.8 - dy / L * 10 * j)
        ls.append(poly([a, b], False))
        if det >= 1 and k % 2 == 0: beads.append(oval((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 2, 1.6, 2.2))
    c.line(_multi(ls), c.lw * 0.75, '#9a2a2a', 210 * amt)
    c.line(_multi(ls), c.lw * 0.3, '#e06a62', 200 * amt)
    if beads: c.fill(_multi(beads), '#8a1e1e', 220 * amt)


def _draw_arm3(c, sp, B, P, side, det, t, skin, sh, sleeve, sleeve_sh, light):
    S, E, Wr = _arm_data(sp, B, P, side)
    b = sp['body']; o = sp['outfit']; cl = sp['cloth']
    pts = [B.p3(*S), B.p3(*E), B.p3(*Wr)]
    P2 = [(p[0], p[1]) for p in pts]
    aw0, aw1 = b['arm']
    hz = clamp(900.0 / (900.0 - pts[2][3]), 0.6, 3.0)
    widths = [aw0 * pts[0][2], (aw0 + aw1) / 2 * max(pts[1][2], hz ** 0.5), aw1 * hz]
    kind = _SLEEVES3.get(o, 'long')
    scr = clamp(getattr(P, 'scratch', 0.0)) if o == 'cardigan3' else 0.0
    if scr > 0.3: kind = 'pushed'
    top = (P2[0][0] - side * 4, P2[0][1] - 14)
    full = [top] + P2
    fw = [widths[0] * 1.05] + widths
    ends = {'long': 1.0, 'over': 1.0, 'short': 0.4, 'puff': 0.3, 'pushed': 0.58}
    ue = ends[kind]
    if kind != 'long' and kind != 'over':                  # bare arm under a short / pushed sleeve
        tp = _tube(full, [w * 0.92 for w in fw])
        c.fill(tp, skin); _cloth_shade(c, tp, sh, 110, 1.0, 8 * pts[0][2]); c.line(tp, c.lw)
        if det >= 1:
            ex_, ey_ = P2[1]
            c.line(smooth([(ex_ - 7, ey_ - 4), (ex_, ey_ + 2), (ex_ + 6, ey_ - 3)], False), c.lw * 0.35, sp['skin_dp'], 150)
        if scr > 0.01: _scratches(c, P2, widths, 0.62, det, scr, 7 + side)
    # sleeve tube from the shoulder to ue
    if ue >= 0.999:
        sl_pts, sl_w = full, [w * (1.06 if kind == 'over' else 1.0) for w in fw]
    else:
        xe, ye = _arm_pt(P2, ue)
        if ue <= 0.5:
            sl_pts = [top, P2[0], (xe, ye)]
            sl_w = [fw[0] * 1.1, fw[1] * 1.12, (fw[1] + (fw[2] - fw[1]) * ue * 2) * (1.25 if kind == 'puff' else 1.12)]
        else:
            sl_pts = [top, P2[0], P2[1], (xe, ye)]
            sl_w = [fw[0] * 1.06, fw[1] * 1.06, fw[2] * 1.18, fw[3] * 1.3]
    sl = _tube(sl_pts, sl_w)
    if kind == 'puff':
        px_, py_ = _arm_pt(P2, 0.14)
        sl = union(sl, _blob(px_, py_ + 2, widths[0] * 0.95, widths[0] * 0.8, 9, side + 4, 0.08))
    c.fill(sl, sleeve)
    _cloth_shade(c, sl, sleeve_sh, 165, 1.0, 12 * pts[0][2])
    if det >= 1:
        c.texture(sl, 'fabric', 0.09, 0.6)
    c.line(sl, c.lw)
    if det >= 1 and ue > 0.55:
        ex, ey = P2[1]
        c.line(smooth([(ex - 10, ey - 6), (ex, ey + 2), (ex + 9, ey - 4)], False), c.lw * 0.4, LINE, 140)
    if kind == 'pushed' and det >= 1:                      # bunched folds where the sleeve is shoved up
        xe, ye = _arm_pt(P2, ue)
        xm, ym = _arm_pt(P2, ue - 0.08)
        c.line(_multi([smooth([(xm - 8, ym - 2 + 6 * k), (xm, ym + 4 + 6 * k), (xm + 8, ym - 1 + 6 * k)], False) for k in range(2)]),
               c.lw * 0.45, LINE, 170)
    wx, wy = P2[2]
    ang = math.degrees(math.atan2(P2[2][1] - P2[1][1], P2[2][0] - P2[1][0])) - 90
    # cuff
    if kind in ('long', 'pushed', 'short', 'puff'):
        xe, ye = _arm_pt(P2, ue)
        xb, yb = _arm_pt(P2, max(0.0, ue - 0.05))
        ca = math.degrees(math.atan2(ye - yb, xe - xb)) - 90
        cw = (widths[2] if ue > 0.5 else widths[1]) * (0.62 if kind != 'puff' else 0.7)
        cc = c.sub(xe, ye, ca, 1.0)
        cuffc = {'cardigan3': cl.get('rib', sleeve_sh), 'pj3': cl.get('trim', sleeve_sh), 'dress3': cl.get('collar', '#fff'),
                 'labcoat3': sleeve, 'police': sleeve_sh}.get(o, mix(sleeve, '#000000', 0.12))
        ch_ = 16 if kind != 'puff' else 9
        cp = rrect(-cw, -ch_, cw * 2, ch_, 5)
        cc.fill(cp, cuffc); cc.line(cp, c.lw * 0.7)
        if det >= 1 and o in ('cardigan3', 'neat3', 'gran3'):
            cc.line(_multi([poly([(k * cw / 4, -ch_ + 2), (k * cw / 4, -2)], False) for k in range(-3, 4)]), c.lw * 0.3, LINE, 130)
    # hand (+ prop)
    pre = 'hl_' if side > 0 else 'hr_'
    shape = getattr(P, pre + 'shape'); prop = getattr(P, pre + 'prop')
    up = getattr(P, pre + 'up'); rot = getattr(P, pre + 'rot'); press = getattr(P, pre + 'press')
    hang = ang * (1 - up) + 180.0 * up + rot
    hs = hz * getattr(P, pre + 'scale', 1.0) * sp.get('hand_k', 1.0)
    ring = (sp['ring'] == side)
    if shape == 'mitt' and det >= 1: shape = 'relaxed'
    if prop:
        _held_prop(c, sp, prop, wx, wy, hang, hs, side, det, t, P)
        if shape not in ('oven', 'pinch', 'flat', 'open'): shape = 'grip'
    if shape == 'oven':
        _draw_oven_mitt(c, sp, wx, wy, hs, hang, side, det)
    else:
        _draw_hand(c, sp, shape, wx, wy, hs, hang, side, det, skin, sh, ring, press, t)
    if prop: _held_prop(c, sp, prop, wx, wy, hang, hs, side, det, t, P, front_part=True)
    if kind == 'over' and shape != 'oven':                  # the oversized hoodie sleeve slides half over the hand
        xb, yb = _arm_pt(P2, 0.93); xe, ye = _arm_pt(P2, 1.06)
        ov = _tube([(xb, yb), (xe, ye)], [widths[2] * 1.2, widths[2] * 1.26])
        c.fill(ov, sleeve); _cloth_shade(c, ov, sleeve_sh, 150, 1.0, 6)
        c.line(ov, c.lw)
        if det >= 1:
            ca = math.degrees(math.atan2(ye - yb, xe - xb)) - 90
            cc = c.sub(xe, ye, ca, 1.0); cw = widths[2] * 0.66
            cc.line(_multi([poly([(k * cw / 3, -14), (k * cw / 3, -3)], False) for k in range(-2, 3)]), c.lw * 0.3, LINE, 140)


def _draw_oven_mitt(c, sp, x, y, scale, angle, side, det):
    """A quilted oven mitt (Mom carries the egg to the burn barrel in them)."""
    hc = c.sub(x, y, angle, scale * sp['body'].get('hand', 1.0) * 1.15)
    th = -side
    m = smooth([(-24, -16), (24, -16), (28, 20), (26, 56), (14, 74), (-8, 76), (-24, 60), (-28, 24)], True, 0.75)
    m = union(m, smooth([(th * 20, 4), (th * 42, 18), (th * 40, 36), (th * 22, 34)], True, 0.8))
    cuff = rrect(-26, -24, 52, 18, 6)
    hc.fill(m, '#c8473a'); hc.fill(_crescent(m, -5, -4), '#8e2c24', 160)
    if det >= 1:
        with hc.clip(m):
            q = [poly([(-40 + k * 14, -20), (-40 + k * 14 + 60, 80)], False) for k in range(-3, 8)]
            q += [poly([(40 - k * 14, -20), (40 - k * 14 - 60, 80)], False) for k in range(-3, 8)]
            hc.line(_multi(q), hc.lw * 0.3, '#f2d6c8', 120)
    hc.line(m, hc.lw * 0.9)
    hc.fill(cuff, '#f2e6d6'); hc.line(cuff, hc.lw * 0.7)


# ====================================================================================================== props
# Props are drawn in CENTIMETRES with their origin at the point a hand grips them (y down). In a hand they scale with the
# holder's real size (sp m); on a surface draw_prop3(pen, name, x, y, px_per_cm) uses the scene scale, so a prop keeps
# exactly the same size when it is picked up (no pops). PROPS3[name] = (draw fn, how it is held: 'grip' = along the hand
# (handles), 'upright' = stays upright in the fingers, 'hang' = hangs down from the hand).
def _p_egg(c, det, t, P=None, kind='pink'):
    col = {'pink': ('#e9a8b6', '#b9788a', '#f6cdd6'), 'gold': ('#e8bd3c', '#a8801c', '#fff0a0')}[kind]
    e = smooth([(0, -4.6), (2.6, -3.4), (3.2, -0.4), (2.6, 2.4), (0, 3.6), (-2.6, 2.4), (-3.2, -0.4), (-2.6, -3.4)], True, 0.9)
    c.fill(e, col[0]); c.radial(e, -1.0, -1.6, 4.8, [(0, col[2], 200), (0.5, col[0], 0), (1, col[1], 230)])
    c.line(smooth([(-3.15, -0.2), (0, 0.5), (3.15, -0.2)], False), c.lw * 0.45, col[1], 230)
    if kind == 'pink' and det >= 1:
        c.fill(rrect(-1.8, 0.9, 3.6, 1.1, 0.3), '#7a4a58', 150)
        c.fill(rect(-1.4, 1.3, 2.8, 0.25), '#f6dde3', 200)
    if kind == 'gold':
        c.fill(oval(-1.2, -2.2, 0.7, 1.1), '#ffffff', 220)
    c.line(e, c.lw * 0.8)


def _p_egg_half(c, det, t, P=None, part='top', ring=False):
    col = ('#e9a8b6', '#b9788a', '#f6cdd6')
    if part == 'top':
        h = smooth([(-3.2, 0.0), (-2.6, -3.0), (0, -4.6), (2.6, -3.0), (3.2, 0.0)], False, 0.9)
        shell = poly([(-3.2, 0.0), (-2.6, -3.0), (0, -4.6), (2.6, -3.0), (3.2, 0.0), (0, 0.9)], True)
        shell = smooth([(-3.2, 0.0), (-2.6, -3.0), (0, -4.6), (2.6, -3.0), (3.2, 0.0), (0, 0.9)], True, 0.9)
        c.fill(shell, col[0]); c.radial(shell, -1.0, -2.0, 4.6, [(0, col[2], 200), (0.5, col[0], 0), (1, col[1], 230)])
        c.fill(oval(0, 0.1, 3.1, 0.8), '#7a4a58'); c.line(shell, c.lw * 0.8)
    else:
        cup = smooth([(-3.2, 0.0), (3.2, 0.0), (2.6, 2.4), (0, 3.6), (-2.6, 2.4)], True, 0.9)
        c.fill(cup, col[0]); c.radial(cup, -1.0, 1.0, 4.4, [(0, col[2], 160), (0.5, col[0], 0), (1, col[1], 230)])
        c.fill(oval(0, 0.0, 3.1, 0.9), '#5e3542')
        if ring:
            c.fill(oval(0.4, -0.1, 1.25, 0.55), '#d8b04c'); c.line(oval(0.4, -0.1, 1.25, 0.55), c.lw * 0.35)
            c.fill(oval(0.4, -0.05, 0.8, 0.28), '#5e3542'); c.fill(oval(-0.3, -0.35, 0.3, 0.14), '#fffbe8')
        c.line(cup, c.lw * 0.8)
        if det >= 1: c.fill(rrect(-1.8, 1.1, 3.6, 1.0, 0.3), '#7a4a58', 150)


def _p_ring(c, det, t, P=None):
    """Dad's gold wedding ring (drawn a little over life size so it reads)."""
    o = oval(0, 0, 1.45, 1.45); i = oval(0, 0, 1.0, 1.0)
    band = minus(o, i)
    c.fill(band, '#d8b04c')
    c.radial(band, -0.5, -0.6, 1.6, [(0, '#fff0b8', 255), (0.6, '#d8b04c', 0), (1, '#7a5a1c', 255)])
    c.line(o, c.lw * 0.35); c.line(i, c.lw * 0.3)
    g = 0.5 + 0.5 * math.sin(t * 3.1)
    c.fill(oval(-0.75, -0.8, 0.28 + 0.15 * g, 0.18), '#ffffff', 200 + 55 * g)


def _p_hatchet(c, det, t, P=None):
    """The old hatchet from the woodpile: grip at the end of a worn handle, a rusty head 38 cm away."""
    h = smooth([(-1.4, 4), (1.4, 4), (1.6, -20), (1.3, -36), (-1.3, -36), (-1.6, -20)], True, 0.6)
    c.fill(h, '#8a6440'); c.fill(_crescent(h, 0.6, 0), '#5e4128', 170)
    if det >= 1: c.line(poly([(-0.4, 0), (0.2, -30)], False), c.lw * 0.25, '#5e4128', 160)
    c.line(h, c.lw * 0.8)
    hd = poly([(-2.6, -40), (3.2, -40.5), (9.5, -44), (10.5, -36), (9.5, -27.5), (3.2, -31), (-2.6, -31.5)], True)
    c.fill(hd, '#5f6268'); c.fill(poly([(7.8, -43), (9.5, -44), (10.5, -36), (9.5, -27.5), (7.8, -29)]), '#9ea3aa')
    if det >= 1: c.fill(oval(1.5, -37, 2.2, 2.6), '#7b3a20', 150)
    c.line(hd, c.lw * 0.8)


def _p_maglite(c, det, t, P=None):
    """Dad's big black flashlight: the beam end at the top (pose.torch_ang turns the whole light)."""
    body = rrect(-1.6, -14, 3.2, 26, 1.2)
    head = smooth([(-2.4, -14), (2.4, -14), (2.4, -20), (-2.4, -20)], True, 0.3)
    c.fill(body, '#1d1e22'); c.fill(head, '#26272c')
    if det >= 1:
        c.line(_multi([poly([(-1.6, k), (1.6, k)], False) for k in np.arange(-4, 8, 1.2)]), c.lw * 0.2, '#3a3b42', 200)
    c.fill(rect(-2.2, -20.6, 4.4, 1.0), '#e8e2c8')
    c.line(body, c.lw * 0.6); c.line(head, c.lw * 0.6)


def _p_diary(c, det, t, P=None, open_=False):
    if open_:
        for sd in (-1, 1):
            pg = poly([(0, -8), (sd * 11, -8.6), (sd * 11, 8.6), (0, 8)], True)
            c.fill(pg, '#f5eedc'); c.line(pg, c.lw * 0.5)
            if det >= 1:
                ls = [poly([(sd * 1.5, -6 + k * 1.6), (sd * 9.5, -6.2 + k * 1.6)], False) for k in range(8)]
                c.line(_multi(ls), c.lw * 0.22, '#9ab0c8', 160)
        return
    cv = rrect(-6, -8, 12, 16, 0.8)
    c.fill(cv, '#e58fae'); c.fill(_crescent(cv, -0.8, 0), '#b8607e', 160)
    c.fill(rect(4.6, -1.2, 2.4, 2.6), '#f6c2d4'); c.line(rect(4.6, -1.2, 2.4, 2.6), c.lw * 0.4)
    c.shape(oval(5.8, 0.1, 0.6, 0.6), '#d8b04c', c.lw * 0.25)
    if det >= 1:
        c.fill(rrect(-4.4, -5.5, 8, 3.2, 0.4), '#fbf3e8'); c.line(rrect(-4.4, -5.5, 8, 3.2, 0.4), c.lw * 0.3)
        c.line(poly([(-3.6, -3.9), (2.6, -3.9)], False), c.lw * 0.3, '#6a4a5a', 200)
    c.line(cv, c.lw * 0.7)


def _p_dress_tiny(c, det, t, P=None, age=1.0):
    """Laurie's tiny yellow Easter dress from the toy chest, grey with age; held by the collar it hangs down: puff
    sleeves, a round white collar, a sash, a full gathered skirt with a lace hem (about 60 cm long)."""
    y = mix('#f2c84b', '#b9b4a2', 0.72 * age); ysh = mix('#c99a24', '#8a8676', 0.72 * age)
    wc = mix('#fbfaf4', '#c9c4b2', 0.6 * age)
    sw = 1.4 * math.sin(t * 1.3)
    bod = smooth([(-8, 1), (8, 1), (10, 10), (9, 22), (-9, 22), (-10, 10)], True, 0.5)
    sk = smooth([(-9, 22), (9, 22), (19 + sw, 52), (10 + sw, 56), (0 + sw, 57), (-10 + sw, 56), (-19 + sw, 52)], True, 0.55)
    for sd in (-1, 1):
        sl = _blob(sd * 11.5, 6.0, 5.5, 5.0, 8, 2 + sd, 0.1)
        c.fill(sl, y); c.fill(_crescent(sl, sd * 1.5, 0), ysh, 150); c.line(sl, c.lw * 0.6)
    c.fill(sk, y); c.fill(_crescent(sk, 3, 0), ysh, 160)
    c.fill(bod, y); c.fill(_crescent(bod, 2, 0), ysh, 150)
    if det >= 1:
        c.line(_multi([poly([(k * 3.5, 24), (k * 5.0 + sw, 54)], False) for k in (-3, -2, -1, 0, 1, 2, 3)]), c.lw * 0.3, ysh, 170)
        lace = _multi([oval(-17 + k * 4.2 + sw, 56.5, 2.3, 1.6) for k in range(9)])
        c.fill(lace, wc); c.line(lace, c.lw * 0.3, '#8a8676', 160)
        c.texture(sk, 'grunge', 0.25 * age, 0.4)
    c.fill(rect(-9.5, 20, 19, 3.2), wc); c.line(rect(-9.5, 20, 19, 3.2), c.lw * 0.4)
    c.line(sk, c.lw * 0.8); c.line(bod, c.lw * 0.8)
    for sd in (-1, 1):
        cp = smooth([(0, 1.0), (sd * 7.5, 0.4), (sd * 8.5, 4.6), (sd * 1.5, 4.0)], True, 0.8); c.fill(cp, wc); c.line(cp, c.lw * 0.45)


def _p_drawing(c, det, t, P=None):
    """The crayon drawing slid under the bathroom door (A4 paper held at a corner): see draw_crayon_drawing."""
    _crayon_page(c, 0.0, 0.0, 21.0, 29.7, det, t, corner=True)


def _p_basket(c, det, t, P=None):
    """The 1987 Bunnyman's Easter basket of plastic eggs (held by its handle)."""
    hdl = smooth([(-11, 14), (-10, 0), (0, -3), (10, 0), (11, 14)], False, 0.9)
    c.line(hdl, c.lw * 2.6, LINE); c.line(hdl, c.lw * 1.6, '#c79a5a')
    for k, (x, col) in enumerate(((-8, '#f2a5b5'), (-3, '#f6d978'), (2, '#9fd3f0'), (7, '#b9e0a5'), (-5, '#d9b3f0'), (5, '#f6d978'))):
        yy = 13 if k < 4 else 11
        c.shape(oval(x, yy, 2.6, 3.4), col, c.lw * 0.4)
    c.fill(poly([(-12, 14), (12, 14), (12, 15.5), (-12, 15.5)]), '#7fc36a')
    b = poly([(-13, 14), (13, 14), (10.5, 26), (-10.5, 26)], True)
    c.fill(b, '#c79a5a'); c.fill(_crescent(b, 1.5, 0), '#8e6a36', 160)
    if det >= 1:
        with c.clip(b):
            c.line(_multi([poly([(-14 + k * 3, 13), (-14 + k * 3 + 4, 27)], False) for k in range(10)]), c.lw * 0.35, '#8e6a36', 200)
            c.line(_multi([poly([(-14, 17 + k * 3), (14, 17 + k * 3)], False) for k in range(4)]), c.lw * 0.35, '#8e6a36', 200)
    c.line(b, c.lw * 0.8)


def _p_key(c, det, t, P=None):
    c.shape(oval(0, -2.2, 1.4, 1.4), '#c9a24a', c.lw * 0.4)
    c.fill(oval(0, -2.2, 0.55, 0.55), '#3a2a1a')
    k = poly([(-0.35, -0.9), (0.35, -0.9), (0.35, 3.4), (1.0, 3.4), (1.0, 2.6), (0.35, 2.6), (0.35, 2.2), (-0.35, 2.2)], True)
    c.fill(k, '#c9a24a'); c.line(k, c.lw * 0.35)


def _p_clipboard(c, det, t, P=None):
    b = rrect(-11, -2, 22, 31, 1.2)
    c.fill(b, '#a07a4e'); c.line(b, c.lw * 0.7)
    c.fill(rect(-9, 2, 18, 25), '#f6f4ee'); c.line(rect(-9, 2, 18, 25), c.lw * 0.4)
    c.shape(rrect(-4, -3.5, 8, 4, 1), '#b9bec6', c.lw * 0.5)
    if det >= 1: c.line(_multi([poly([(-7, 7 + k * 2.4), (7 - 3 * (k % 2), 7 + k * 2.4)], False) for k in range(7)]), c.lw * 0.25, '#7a8090', 180)


PROPS3 = {
    'egg': (lambda c, d, t, P=None: _p_egg(c, d, t, P, 'pink'), 'upright', (0.0, -1.0)),
    'egg_gold': (lambda c, d, t, P=None: _p_egg(c, d, t, P, 'gold'), 'upright', (0.0, -1.0)),
    'egg_top': (lambda c, d, t, P=None: _p_egg_half(c, d, t, P, 'top'), 'upright', (0.0, -1.0)),
    'egg_bot': (lambda c, d, t, P=None: _p_egg_half(c, d, t, P, 'bot'), 'upright', (0.0, 0.0)),
    'egg_bot_ring': (lambda c, d, t, P=None: _p_egg_half(c, d, t, P, 'bot', True), 'upright', (0.0, 0.0)),
    'ring': (_p_ring, 'upright', (0.0, 0.0)),
    'hatchet': (_p_hatchet, 'grip', (0.0, 0.0)),
    'maglite': (_p_maglite, 'torch', (0.0, 0.0)),
    'diary': (_p_diary, 'upright', (0.0, 0.0)),
    'diary_open': (lambda c, d, t, P=None: _p_diary(c, d, t, P, True), 'upright', (0.0, 0.0)),
    'dress_tiny': (_p_dress_tiny, 'hang', (0.0, 0.0)),
    'drawing': (_p_drawing, 'upright', (0.0, 0.0)),
    'basket': (_p_basket, 'hang', (0.0, 0.0)),
    'key': (_p_key, 'upright', (0.0, 0.0)),
    'clipboard': (_p_clipboard, 'upright', (0.0, 0.0)),
}


def _held_prop(c, sp, prop, wx, wy, hang, hs, side, det, t, P, front_part=False):
    """Draw a held prop in the hand at wrist (wx, wy) with hand angle `hang` (0 = fingers down): its grip point sits in
    the palm, about 0.45 of a hand length from the wrist. Older props (v2 _prop names) still work."""
    if prop not in PROPS3:
        if front_part: return
        pc = c.sub(wx + math.sin(math.radians(-hang)) * 30 * hs, wy + math.cos(math.radians(hang)) * 30 * hs, 0, hs * 1.15)
        _prop(pc, prop, det, t)
        return
    if front_part and prop not in ('ring',): return
    if not front_part and prop == 'ring': return
    fn, how, (gx, gy) = PROPS3[prop]
    k = 10.0 / sp.get('m', 1.7)                              # body units per cm for this holder
    hk = sp['body'].get('hand', 1.0)                         # hs already carries the cast's hand_k
    reach = (36.0 if how != 'hang' else 52.0) * hs * hk
    if prop in ('egg', 'egg_gold', 'egg_top', 'egg_bot', 'egg_bot_ring', 'key'): reach = 50.0 * hs * hk
    if prop == 'ring': reach = 40.0 * hs * hk                # pinched at the fingertips
    gx_, gy_ = wx + math.sin(math.radians(-hang)) * reach, wy + math.cos(math.radians(hang)) * reach
    if how == 'grip':
        rot = hang + 180.0                                    # handle along the hand, the head beyond the fingers
    elif how == 'torch':
        rot = getattr(P, 'torch_ang', 0.0)
    else:
        rot = 0.0
    pc = c.sub(gx_, gy_, rot, k)
    pc.lw = c.lw / k
    fn(pc, det, t, P)


def draw_prop3(pen, name, x, y, px_per_cm, angle=0.0, detail=2, t=0.0, pose=None, lw=None):
    """Draw a v3 prop on a surface: (x, y) = its grip point in design px, px_per_cm = scene scale (a figure of real height
    m drawn h px tall has px_per_cm = h / (m * 100)). The same prop in a hand has exactly the same size."""
    fn, how, _ = PROPS3[name]
    c = Ctx(pen, skia.Matrix(), (lw or _lw_for(px_per_cm * 22.0)) / px_per_cm)
    c = Ctx(pen, skia.Matrix(), lw or _lw_for(px_per_cm * 22.0)).sub(x, y, angle, px_per_cm)
    fn(c, detail, t, pose)


def _crayon_page(c, x, y, w, h, det, t, corner=False):
    """Placeholder: replaced by the crayon drawing below."""
    c.shape(rect(x - w / 2, y - h / 2, w, h), '#f6f1e4', c.lw * 0.5)



# ====================================================================================================== staging tools
# World-space acting: an Acting that knows where its figure stands (a.place) can look at, reach to and touch points in
# the same design coordinates its draw() call uses, so eyelines, contacts and props always line up with the set.
# Targets: (x, y) | callable t -> (x, y) | (other_acting, part) | PropTrack. Parts (Acting.where): 'head', 'eyes',
# 'eye_l', 'eye_r', 'mouth', 'nose', 'chin', 'crown', 'neck', 'chest', 'belly', 'hip', 'lap', 'knee_l', 'knee_r',
# 'foot_l', 'foot_r', 'hand_l', 'hand_r' (palm centre), 'wrist_l', 'wrist_r', 'shoulder_l', 'shoulder_r'.
# Solves run in a post pass, after every clip, the idle life and the breathing, so contact holds on the final pose.

def _acting_raw3(self, t, post=True):
    tf = self._tmap(t)
    P = Pose()
    P.t = t
    P.mix(self.base); P.mix(EXPR[self.expr0])
    if self._arc: P.mix(stage_at(tf, self._arc, self.sp.get('stages'), self.sp.get('stage_keys')), 1.0)
    sd = self.seed * 7 + 3
    P.breath = 0.5 + 0.45 * math.sin(2 * PI * tf / 3.9 + sd) + 0.08 * noise1(tf * 0.4, sd)
    for (t0, t1, fn, real) in (self.clips + self.late if self.late else self.clips):
        tt = t if real else tf
        if (t0 == -INF or t0 - 1.5 <= tt) and tt <= t1 + 1.5: fn(P, tt)
    m = self.micro * (1.0 - clamp(P.still))
    P.h_tilt += 1.7 * m * noise1(tf * 0.21, sd + 1)
    P.h_turn += 0.035 * m * noise1(tf * 0.16, sd + 2)
    P.h_nod += 0.03 * m * noise1(tf * 0.19, sd + 3)
    P.sway += 3.0 * m * noise1(tf * 0.3, sd + 4)
    P.tilt += 0.5 * m * noise1(tf * 0.13, sd + 5)
    lf = self.life_k * clamp(P.life)
    if P.still > 0: P.breath = lerp(P.breath, 0.5 + (0.15 + 0.17 * lf) * math.sin(2 * PI * tf / 4.6 + sd), clamp(P.still))
    if lf > 0.01: self._life(P, tf, lf, sd)
    sx, sy = self._saccade(tf)
    un = (1.0 - clamp(P.lock)) * (1.0 - clamp(P.still)) * (1.0 - clamp(getattr(P, '_gaze', 0.0)))
    P.look_x += sx * un; P.look_y += sy * un
    b = self._blink_amt(tf) * (1.0 - clamp(P.still)) * (1.0 - clamp(getattr(P, '_noblink', 0.0)))
    P.blink = max(P.blink, b)
    if post and getattr(self, 'post', None) and not getattr(self, '_in_post', False):
        # contact solves; a nested look-up of this same actor from inside them (a look at a prop it holds) gets the pose
        # before the solves instead of recursing
        self._in_post = True
        try:
            for (t0, t1, fn) in self.post:
                if t0 - 1.5 <= tf <= t1 + 1.5: fn(P, tf)
        finally:
            self._in_post = False
    return P


Acting._raw = _acting_raw3
POSE_DEFAULTS.update(_gaze=0.0)


def _acting_place(self, x, y_feet, height=None):
    """Tell the actor where its figure is drawn (the same x, y_feet, height as the draw() call; pose.dx / dy still move it).
    Needed by look_at / reach_to / where / the prop and contact clips. Returns self."""
    self.x0, self.y0 = float(x), float(y_feet)
    if height is not None: self.height = float(height)
    return self


def _acting_post(self, t0, t1, fn):
    if not hasattr(self, 'post'): self.post = []
    self.post.append((t0, INF if t1 is None else t1, fn))
    return self


def _origin(self, P):
    """(ox, oy, s): design-space origin of the figure's body frame and px per body unit (as draw() places it)."""
    if not hasattr(self, 'x0'): raise ValueError('Acting.place(x, y_feet, height) first: %s' % self.who)
    return _place(self.who, P, self.x0, self.y0, self.height)


def _head_point(sp, B, P, fx, fy, dz=2.0):
    """Body-frame 2D point of a face point (front coords fx, fy in head units) as the figure draws its head."""
    hx, hy, hrot, hs = _head_xf(sp, B, P)
    yaw = (P.turn + P.h_turn) * PI / 2
    hm = HeadMap(sp, yaw, P.h_nod * 0.6) if not sp.get('bunny') else BunnyMap(sp, yaw, P.h_nod * 0.6)
    X, Y, V = hm.map1(fx, fy, dz)
    a = math.radians(hrot)
    if sp.get('bunny'): hy += 18.0
    return hx + (X * math.cos(a) - Y * math.sin(a)) * hs, hy + (X * math.sin(a) + Y * math.cos(a)) * hs


def _body_point(self, P, part):
    """Body-frame 2D point of a named part for pose P."""
    sp = self.sp; B = Body(sp, P); b = sp['body']
    if part in ('head', 'eyes', 'eye_l', 'eye_r', 'mouth', 'nose', 'chin', 'crown', 'forehead'):
        ey = sp['eye_y']
        fp = {'head': (0, 0), 'eyes': (0, ey), 'eye_l': (sp['eye_dx'], ey), 'eye_r': (-sp['eye_dx'], ey),
              'mouth': (0, sp['mouth_y']), 'nose': (0, (ey + sp['mouth_y']) * 0.5), 'chin': (0, 112), 'crown': (0, -118),
              'forehead': (0, -60)}[part]
        return _head_point(sp, B, P, fp[0], fp[1], 6.0 if part != 'head' else 0.0)
    if part in ('hand_l', 'hand_r', 'wrist_l', 'wrist_r', 'shoulder_l', 'shoulder_r', 'elbow_l', 'elbow_r'):
        side = 1 if part.endswith('_l') else -1
        S, E, W = _arm_data(sp, B, P, side)
        if part.startswith('shoulder'): X, Y, _, _ = B.p3(*S); return X, Y
        if part.startswith('elbow'): X, Y, _, _ = B.p3(*E); return X, Y
        wx, wy, ws, _ = B.p3(*W); ex, ey, _, _ = B.p3(*E)
        if part.startswith('wrist'): return wx, wy
        L = math.hypot(wx - ex, wy - ey) or 1.0
        k = 34.0 * ws * sp['body'].get('hand', 1.0) * sp.get('hand_k', 1.0)
        return wx + (wx - ex) / L * k, wy + (wy - ey) / L * k
    if part in ('knee_l', 'knee_r', 'foot_l', 'foot_r'):
        side = 1 if part.endswith('_l') else -1
        H, K, A, _ = _leg_chain(sp, B, P, side)
        Q = K if part.startswith('knee') else A
        X, Y, _, _ = B.p3(Q[0], Q[1] - B.bob, Q[2], upper=False)
        return X, Y
    if part == 'lap':
        Hl, Kl, _, _ = _leg_chain(sp, B, P, 1); Hr, Kr, _, _ = _leg_chain(sp, B, P, -1)
        m_ = (Hl + Kl + Hr + Kr) / 4.0
        X, Y, _, _ = B.p3(m_[0], m_[1] - B.bob - b['leg'][0] * 0.5, m_[2], upper=False)
        return X, Y
    y = {'neck': B.y_sh - 30, 'chest': B.y_ch, 'belly': B.y_wa, 'hip': B.y_hip}[part]
    X, Y, _, _ = B.p3(0, y, b['ch'] * 0.6 if part in ('chest', 'belly') else 0.0, upper=part != 'hip')
    return X, Y


def _acting_where(self, t, part='head', post=True):
    """Design-space (x, y) of a body part at time t (see the part names above). post=False uses the pose before the
    contact solves (two actors that reach for each other use it to avoid chasing each other)."""
    P = self._raw(t, post) if not post else self.at(t)
    ox, oy, s = _origin(self, P)
    X, Y = _body_point(self, P, part)
    return ox + X * s, oy + Y * s


def _target_xy(target, t):
    """Resolve a target at time t: (x, y) | callable | (Acting, part) | PropTrack."""
    if isinstance(target, PropTrack): return target.pos(t)
    if callable(target): return target(t)
    if isinstance(target, tuple) and len(target) == 2 and isinstance(target[0], Acting):
        return target[0].where(t, target[1], post=False)
    return target


def _world_to_body(self, P, B, wx, wy, z=0.0):
    """Inverse of the body projection: a design-space point (wx, wy) at camera depth z (body units toward the camera,
    relative to the body's centre plane) -> body-frame (x, y_in, z) as _arm_data's targets use (y_in without the bob)."""
    ox, oy, s = _origin(self, P)
    X = (wx - ox) / s; Y = (wy - oy) / s
    # undo the 2D tilt and sway about the hips
    hx, hy = 0.0, B.y_hip + B.bob
    X -= P.sway
    dx, dy = X - hx, Y - hy
    X = hx + dx * B.ctl + dy * B.stl; Y = hy - dx * B.stl + dy * B.ctl
    sc = B.D / (B.D - z)
    xc = X / sc; y1 = B.y0c + (Y - B.y0c) / sc
    x = xc * B.ct - z * B.st; z1 = xc * B.st + z * B.ct
    yp = B.y_hip + B.bob
    y1p = y1 - yp
    dyb = y1p * B.cL - z1 * B.sL; zb = y1p * B.sL + z1 * B.cL
    return x, yp + dyb - B.bob, zb


def _arm_len(sp):
    ak = sp['body'].get('arm_k', 1.0)
    return (182.0 + 166.0) * ak


def _solve_reach(self, P, side, wx, wy, z, contact, w, lean_ok=True, prop=None):
    """Blend the arm (side) of pose P toward a design-space target by weight w: the palm centre (contact 'palm'), the
    fingertips ('tips') or the held prop's grip point ('grip') lands on (wx, wy). Leans the body a little toward targets
    just out of reach; records misses in self.misses."""
    if w <= 0.001: return
    sp = self.sp; pre = 'hl_' if side > 0 else 'hr_'
    hk = sp['body'].get('hand', 1.0) * sp.get('hand_k', 1.0)
    off = {'palm': 34.0, 'tips': 62.0, 'wrist': 0.0}.get(contact, 34.0) * hk
    if contact == 'grip' and prop:
        how = PROPS3.get(prop, (None, 'upright'))[1]
        off = (52.0 if how == 'hang' else 36.0) * hk
        if prop in ('egg', 'egg_gold', 'egg_top', 'egg_bot', 'egg_bot_ring', 'key'): off = 50.0 * hk
        if prop == 'ring': off = 64.0 * hk
    L = _arm_len(sp)
    for it in range(5):
        B = Body(sp, P)
        x, y, zz = _world_to_body(self, P, B, wx, wy, z)
        S = np.array([side * (sp['body']['sh'] - 17), B.y_sh + 20, 0.0])
        Tgt = np.array([x, y, zz])
        # direction of the hand: from the current elbow (or the shoulder) toward the target
        _, E, Wc = _arm_data(sp, B, P, side)
        d = Tgt - E if it > 0 else Tgt - S
        n = float(np.linalg.norm(d)) or 1.0
        Wt = Tgt - d / n * off
        dist = float(np.linalg.norm(Wt - S))
        if lean_ok and dist > L * 0.97 and it < 4:
            k = clamp((dist - L * 0.97) / 200.0)
            low = Tgt[1] > B.y_hip - 40.0                # below the waist: squat and bend (a pick-up from the floor)
            if low:
                P.lean = min(1.5, P.lean + 0.55 * k * w); P.crouch = min(2.2, P.crouch + 0.9 * k * w)
            else:
                P.lean = min(0.9, P.lean + 0.32 * k * w * (1.0 if (Tgt[2] > 0 or abs(Tgt[0]) < 60) else 0.4))
                P.tilt += -side * 6.0 * k * w * (1.0 if abs(Tgt[0]) > 120 else 0.0) * (1 if B.ct >= 0 else -1)
            continue
        rel = Wt - S
        if B.walk > 0:                                  # _arm_data adds the walk's arm swing: take it back out
            rel = rel + np.array([0.0, 0.0, 60.0 * B.walk * math.cos(B.leg_phase(-side))])
        cur = np.array([side * getattr(P, pre + 'out'), getattr(P, pre + 'down'), getattr(P, pre + 'fwd')])
        tgt = np.array([side * rel[0], rel[1], rel[2]])
        new = cur + (tgt - cur) * w
        setattr(P, pre + 'out', float(new[0])); setattr(P, pre + 'down', float(new[1])); setattr(P, pre + 'fwd', float(new[2]))
        setattr(P, pre + 'up', getattr(P, pre + 'up') * (1.0 - w))
    if w > 0.98:
        B = Body(sp, P)
        _, E, Wr = _arm_data(sp, B, P, side)
        if float(np.linalg.norm(Wr - Wt)) > 12.0:
            ms = getattr(self, 'misses', None)
            if ms is None: self.misses = ms = []
            if len(ms) < 200: ms.append((round(P.t, 3), side, round(float(np.linalg.norm(Wr - Wt)), 1)))


def _acting_look_at(self, t0, target, t1=None, dur=0.4, z=None, body=0.0, head=1.0, fade=0.35, eyes_lead=0.07, max_head=0.85):
    """Head and eyes look at a target (design point, callable, (actor, part) or PropTrack) from t0 (to t1, None = hold).
    The eyes get there first (a saccade in eyes_lead s), the head follows with an eased turn over dur, the body turns by
    `body` (0..1) of the yaw. z = the target's depth toward the camera in body units (None: a little in front of the
    figure, the usual 2D cheat that keeps both faces in 3/4). Pitch follows the height difference (looking down at a
    child, up at the stairs)."""
    def fn(P, t):
        w_e = _env(t, t0, t1, eyes_lead, fade)
        w_h = _env(t, t0, t1, dur, fade * 1.4) * head
        if w_e <= 0.001 and w_h <= 0.001: return
        tx, ty = _target_xy(target, t)
        sp = self.sp
        ox, oy, s = _origin(self, P)
        B = Body(sp, P)
        hx, hy, _, _ = _head_xf(sp, B, P)
        dx = (tx - (ox + hx * s)) / s; dy = (ty - (oy + hy * s)) / s
        dz = (0.6 * abs(dx) + 60.0) if z is None else float(z)
        yaw = math.atan2(dx, dz) / (PI / 2)                # quarter turns
        pitch = math.atan2(dy, math.hypot(dx, max(dz, 1.0)))
        tot0 = P.turn + P.h_turn
        if body > 0:
            P.turn += (yaw - P.turn) * body * w_h
        want_h = clamp(yaw - P.turn, -max_head, max_head)
        P.h_turn += (want_h - P.h_turn) * w_h
        P.h_nod += (clamp(pitch / 0.6 * 0.85, -0.7, 0.8) - P.h_nod) * w_h
        # eyes: the rest of the angle (they lead, then stay on target while the head arrives)
        rem_yaw = yaw - (P.turn + P.h_turn)
        rem_pitch = pitch - P.h_nod * 0.6
        P.look_x += (clamp(rem_yaw * 1.6, -1.0, 1.0) - P.look_x) * w_e
        P.look_y += (clamp(rem_pitch * 1.4, -1.0, 1.0) - P.look_y) * w_e
        P.lock *= (1.0 - w_e)
        P._gaze = max(getattr(P, '_gaze', 0.0), w_e)
    return _acting_post(self, t0 - dur, None if t1 is None else t1 + fade * 1.5, fn)


def _acting_reach_to(self, t0, side, target, t1=None, dur=0.55, z=0.0, contact='palm', shape='grip', fade=0.45,
                     antic_k=0.06, prop=None, lean=True, press=None, rot=None):
    """The hand (side +1 = character's left) reaches a target (design point, callable, (actor, part), PropTrack) by
    t0 + dur with anticipation and an eased arrival, holds until t1 (None = for good), then returns over fade. contact:
    'palm' (palm centre on the target), 'tips' (fingertips), 'grip' (the held prop's grip point), 'wrist'. z: the
    target's depth toward the camera in body units (0 = the figure's own plane; + = in front of it)."""
    def fn(P, t):
        u = prog(t, t0, t0 + dur)
        w_in = settle(u, 0.03) if u > 0 else 0.0
        if u > 0 and u < 0.3: w_in += antic(u, antic_k) * 0.5 * 0.0
        w_out = 1.0 if t1 is None else 1.0 - ease_in_out(prog(t, t1, t1 + fade))
        w = clamp(min(w_in, w_out), 0.0, 1.05)
        if w <= 0.001: return
        tx, ty = _target_xy(target, t)
        pr_ = prop if prop is not None else getattr(P, ('hl_' if side > 0 else 'hr_') + 'prop')
        _solve_reach(self, P, side, tx, ty, z, contact, min(w, 1.0), lean, pr_)
        pre = 'hl_' if side > 0 else 'hr_'
        if shape is not None and w > 0.5: setattr(P, pre + 'shape', shape)
        if press is not None: setattr(P, pre + 'press', press * min(w, 1.0))
        if rot is not None: setattr(P, pre + 'rot', getattr(P, pre + 'rot') + rot * min(w, 1.0))
    return _acting_post(self, t0, None if t1 is None else t1 + fade, fn)


Acting.place = _acting_place
Acting.where = _acting_where
Acting.look_at = _acting_look_at
Acting.reach_to = _acting_reach_to


class PropTrack:
    """One prop's single source of truth over a shot: it rests somewhere (drawn by track.draw) or is held by an actor
    (drawn in that hand by the figure); never both, never teleporting. Keys are added by the actors' clips (pick_up,
    put_down, give) or by hand: track.rest(t, x, y, angle), track.held(t, actor, side).
        egg = PropTrack('egg', 980, 905, px_per_cm)    # px_per_cm: the scene scale at the prop's depth
        a.pick_up(egg, 2.0, side=-1)                   # reach, grip at contact, lift
        Layer(d, lambda pen, t: egg.draw(pen, t))      # draws it only while it rests
    """

    def __init__(self, name, x, y, px_per_cm, angle=0.0):
        self.name, self.ppc = name, float(px_per_cm)
        self.keys = [(-INF, ('rest', float(x), float(y), float(angle)))]

    def _key(self, t, st):
        self.keys.append((float(t), st)); self.keys.sort(key=lambda k: k[0]); return self

    def rest(self, t, x, y, angle=0.0): return self._key(t, ('rest', float(x), float(y), float(angle)))

    def held(self, t, actor, side): return self._key(t, ('held', actor, side))

    def gone(self, t): return self._key(t, ('gone',))

    def state(self, t):
        st = self.keys[0][1]
        for tk, s_ in self.keys:
            if tk <= t: st = s_
            else: break
        return st

    def holder(self, t):
        st = self.state(t)
        return (st[1], st[2]) if st[0] == 'held' else None

    def pos(self, t):
        """Design-space grip point at time t (the hand's grip point while held)."""
        st = self.state(t)
        if st[0] == 'rest': return st[1], st[2]
        if st[0] == 'held':
            a, side = st[1], st[2]
            return a.grip_point(t, side, self.name)
        return (-1e6, -1e6)

    def draw(self, pen, t, detail=2, pose=None):
        st = self.state(t)
        if st[0] == 'rest': draw_prop3(pen, self.name, st[1], st[2], self.ppc, st[3], detail, t, pose)


def _grip_point(self, t, side, prop, post=True):
    """Design-space grip point of a prop held in a hand (where draw puts it). post=False: before the contact solves (use
    it inside this actor's own clips)."""
    P = self.at(t) if post else self._raw(t, False); sp = self.sp
    B = Body(sp, P)
    S, E, W = _arm_data(sp, B, P, side)
    pts = [B.p3(*S), B.p3(*E), B.p3(*W)]
    wx, wy = pts[2][0], pts[2][1]
    ang = math.degrees(math.atan2(pts[2][1] - pts[1][1], pts[2][0] - pts[1][0])) - 90
    pre = 'hl_' if side > 0 else 'hr_'
    up = getattr(P, pre + 'up'); rot = getattr(P, pre + 'rot')
    hang = ang * (1 - up) + 180.0 * up + rot
    hz = clamp(900.0 / (900.0 - pts[2][3]), 0.6, 3.0)
    hs = hz * getattr(P, pre + 'scale', 1.0) * sp.get('hand_k', 1.0)
    how = PROPS3.get(prop, (None, 'upright'))[1]
    hk = sp['body'].get('hand', 1.0) * sp.get('hand_k', 1.0)
    reach = (36.0 if how != 'hang' else 52.0) * hs * sp['body'].get('hand', 1.0)
    if prop in ('egg', 'egg_gold', 'egg_top', 'egg_bot', 'egg_bot_ring', 'key'): reach = 50.0 * hs * sp['body'].get('hand', 1.0)
    if prop == 'ring': reach = 40.0 * hs * sp['body'].get('hand', 1.0)
    gx, gy = wx + math.sin(math.radians(-hang)) * reach, wy + math.cos(math.radians(hang)) * reach
    ox, oy, s = _origin(self, P)
    return ox + gx * s, oy + gy * s


def _set_prop(self, side, t0, t1, name):
    pre = 'hl_' if side > 0 else 'hr_'
    def fn(P, t):
        if t0 <= t < (INF if t1 is None else t1): setattr(P, pre + 'prop', name)
    return self._add(t0, t1, fn, late=True)


def _acting_hold_prop(self, name, side, t0=-INF, t1=None):
    """The hand holds prop `name` from t0 to t1 (a prop the actor already has: the hatchet, the basket, the flashlight)."""
    return _set_prop(self, side, t0, t1, name)


def _acting_pick_up(self, track, t0, side=1, dur=1.0, carry=None, z=0.0, shape='grip'):
    """Reach for a resting PropTrack, take it at contact (t0 + 0.55 dur: the track switches to this hand, the prop is in
    the hand from that frame), then carry it to `carry` (design point / target; None = up in front of the chest) by t0 +
    dur. Returns the contact time."""
    tc = t0 + 0.55 * dur
    x, y = track.pos(t0)
    self.reach_to(t0, side, (x, y), t1=tc, dur=0.55 * dur, z=z, contact='grip', shape=shape, fade=0.45 * dur, prop=track.name)
    track.held(tc, self, side)
    _set_prop(self, side, tc, None, track.name)
    if carry is not None:
        self.reach_to(tc, side, carry, t1=None, dur=0.45 * dur, z=z, contact='grip', shape=shape, fade=0.4, prop=track.name)
    else:
        self.reach(tc, None, side, out=-30.0, down=105.0, fwd=165.0, shape='grip', up=0.0, fade=0.45 * dur)
    return tc


def _acting_put_down(self, track, t0, side, x, y, dur=1.0, z=0.0, angle=0.0, release_t1=None):
    """Carry the held prop to (x, y), let go at contact (t0 + 0.55 dur: it rests there from that frame), the hand
    returns. Returns the contact time."""
    tc = t0 + 0.55 * dur
    self.reach_to(t0, side, (x, y), t1=tc, dur=0.55 * dur, z=z, contact='grip', fade=0.45 * dur, prop=track.name)
    track.rest(tc, x, y, angle)
    pre = 'hl_' if side > 0 else 'hr_'
    def fn(P, t):
        if t >= tc and getattr(P, pre + 'prop') == track.name: setattr(P, pre + 'prop', None)
    self._add(tc, release_t1, fn, late=True)
    return tc


def _acting_give(self, track, t0, side, other, other_side, dur=1.2, meet=None, z=0.0):
    """Hand a held prop to another actor: both hands meet at `meet` (None = halfway between the two hands), the prop
    changes hands at contact (t0 + 0.5 dur), both arms settle. Returns the contact time."""
    tc = t0 + 0.5 * dur
    if meet is None:                                      # between the two chests, a little below: both arms reach it
        a0 = self.where(t0, 'chest', post=False); b0 = other.where(t0, 'chest', post=False)
        a1 = self.where(t0, 'belly', post=False); b1 = other.where(t0, 'belly', post=False)
        meet = ((a0[0] + b0[0]) / 2, ((a0[1] + b0[1]) / 2 + (a1[1] + b1[1]) / 2) / 2)
    self.reach_to(t0, side, meet, t1=tc + 0.1, dur=0.5 * dur, z=z, contact='grip', fade=0.5 * dur, prop=track.name)
    other.reach_to(t0 + 0.1 * dur, other_side, meet, t1=tc + 0.15, dur=0.4 * dur, z=z, contact='grip', fade=0.45 * dur, prop=track.name)
    track.held(tc, other, other_side)
    pre = 'hl_' if side > 0 else 'hr_'
    def fn(P, t):
        if t >= tc and getattr(P, pre + 'prop') == track.name: setattr(P, pre + 'prop', None)
    self._add(tc, None, fn, late=True)
    _set_prop(other, other_side, tc, None, track.name)
    return tc


Acting.grip_point = _grip_point
Acting.hold_prop = _acting_hold_prop
Acting.pick_up = _acting_pick_up
Acting.put_down = _acting_put_down
Acting.give = _acting_give


# ------------------------------------------------------------------------------------------- body clips (v3 staging)
def _acting_sit_on(self, t0, seat_y, dur=1.0, t1=None, hands='lap', floor_y=None, lean_back=0.0):
    """Sit down onto a seat whose top is at design y seat_y (the figure's y_feet stays the FLOOR, the feet stay on it):
    a small lean forward and bend (anticipation), the hips lower onto the seat (pose.seat, pose.sit), the back straightens.
    t1: start of standing back up (stand_up). hands 'lap' | 'knees' | 'arms' (on armrests) | None."""
    fy = self.y0 if floor_y is None else floor_y
    s = self.height / 1000.0
    seat_u = max(60.0, (fy - seat_y) / s)
    def fn(P, t):
        u = prog(t, t0, t0 + dur)
        if t < t0: return
        k = ease_in_out(clamp((u - 0.15) / 0.8))
        lean = 0.22 * math.sin(PI * clamp(u / 0.9)) * (1.0 - k * 0.3)
        if t1 is not None and t >= t1:
            return
        P.seat = seat_u; P.sit = max(P.sit, k)
        P.lean += lean + 0.05 * k - lean_back * k
        if hands and k > 0.01:
            for side in (-1, 1):
                if hands == 'lap': self._arm(P, side, k, -28.0, 300.0, 170.0, 'relaxed', up=0.0)
                elif hands == 'knees': self._arm(P, side, k, -10.0, 300.0, 230.0, 'relaxed', up=0.0)
                elif hands == 'arms': self._arm(P, side, k, 40.0, 250.0, 110.0, 'relaxed', up=0.0)
    self._add(t0, None, fn)
    if t1 is not None: self.stand_up(t1, seat_y=seat_y, floor_y=floor_y, hands=hands)
    return self


def _acting_seated(self, seat_y, t0=-INF, t1=None, hands='lap', floor_y=None):
    """Already sitting on the seat at design y seat_y (no sit-down move)."""
    fy = self.y0 if floor_y is None else floor_y
    seat_u = max(60.0, (fy - seat_y) / (self.height / 1000.0))
    def fn(P, t):
        P.seat = seat_u; P.sit = 1.0; P.lean += 0.05
        if hands:
            for side in (-1, 1):
                if hands == 'lap': self._arm(P, side, 1.0, -28.0, 300.0, 170.0, 'relaxed', up=0.0)
                elif hands == 'knees': self._arm(P, side, 1.0, -10.0, 300.0, 230.0, 'relaxed', up=0.0)
                elif hands == 'arms': self._arm(P, side, 1.0, 40.0, 250.0, 110.0, 'relaxed', up=0.0)
    return self._add(t0, t1, fn)


def _acting_stand_up(self, t0, dur=1.1, seat_y=None, floor_y=None, hands='lap'):
    """Stand up from a seat: lean the weight forward over the feet first (anticipation), push up, straighten."""
    fy = self.y0 if floor_y is None else floor_y
    seat_u = max(60.0, (fy - seat_y) / (self.height / 1000.0)) if seat_y is not None else None
    def fn(P, t):
        if t < t0: return
        u = prog(t, t0, t0 + dur)
        k = 1.0 - ease_in_out(clamp((u - 0.25) / 0.75))
        if seat_u is not None: P.seat = seat_u
        P.sit = min(1.0, k) if P.sit <= 1.0 else P.sit
        P.sit = k
        P.lean += 0.32 * math.sin(PI * clamp(u / 0.85)) * (1.0 if u < 0.85 else 0.0)
        if hands and k > 0.01:
            for side in (-1, 1):
                self._arm(P, side, k * 0.8 + 0.2 * math.sin(PI * u), -10.0, 290.0, 220.0, 'relaxed', up=0.0)
    return self._add(t0, None, fn)


def _acting_kneel_down(self, t0, dur=1.0, knees=0, t1=None, up_dur=1.0):
    """Kneel: one knee (knees 0: the character's right knee down, left foot forward), both knees (1) or sitting back on
    the heels (2). A small step and lean forward on the way down; t1 = start of getting back up."""
    def fn(P, t):
        if t < t0: return
        u = prog(t, t0, t0 + dur)
        k = ease_in_out(u)
        if t1 is not None and t >= t1:
            k *= 1.0 - ease_in_out(prog(t, t1, t1 + up_dur))
            P.lean += 0.25 * math.sin(PI * prog(t, t1, t1 + up_dur))
        P.kneel = max(P.kneel, k); P.knees = float(knees)
        P.lean += 0.18 * math.sin(PI * u) + (0.06 if knees < 1.5 else 0.12) * k
    return self._add(t0, None, fn)


def _acting_run(self, t0, t1, x_from, x_to, surface='inside', facing=None):
    """Run from x_from to x_to (pose.dx): a running cycle (longer stride, a flight phase, forward lean, bent arms pumping)
    with footstep events (louder) at each foot strike."""
    d = x_to - x_from
    units = abs(d) / (self.height / 1000.0)
    cycles = units / 760.0
    face = facing if facing is not None else (1.0 if d >= 0 else -1.0)
    dur = t1 - t0
    def fn(P, t):
        u = ease_in_out(prog(t, t0, t1)) * 0.25 + prog(t, t0, t1) * 0.75
        w = _env(t, t0 - 0.25, t1, 0.3, 0.35, ease)
        P.dx = x_from + d * u
        P.walk_amt = max(P.walk_amt, _env(t, t0, t1, 0.2, 0.3))
        P.run = max(P.run, _env(t, t0, t1, 0.25, 0.3))
        P.walk_ph = cycles * u
        P.turn = lerp(P.turn, face, w)
        P.lean += 0.16 * P.run
        sw = math.sin(cycles * u * 2 * PI)
        for side in (-1, 1):
            self._arm(P, side, 0.9 * P.run, 26.0, 150.0 + 40.0 * side * sw, 120.0 - 150.0 * side * sw, 'fist', up=0.0)
    if not getattr(self, '_walked', False):
        self._walked = True
        self.clips.append((-INF, t0 - 0.3, lambda P, t: setattr(P, 'dx', x_from), False))
    self._add(t0 - 0.3, None, fn)
    evs = []
    n = int(math.floor(cycles * 2.0))
    for k in range(1, n + 1):
        uu = k / (cycles * 2.0)
        evs.append(self._ev(t0 + dur * uu, 'footsteps_wood_inside' if surface == 'inside' else 'footsteps_porch', 1.0, pan=0.0,
                            n=1, kind='run', foot='L' if k % 2 else 'R'))
    return evs


def _acting_wave(self, t0, t1, side=1, speed=1.0, height=1.0, slow=False):
    """Wave (side +1 = the character's left hand): the arm comes up, the hand sways from the elbow; slow=True is the
    Bunnyman's slow, heavy wave (about one sway every 1.6 s, no wrist flick)."""
    per = 1.6 if slow else 0.55 / speed
    def fn(P, t):
        w = _env(t, t0, t1, 0.5 if slow else 0.3, 0.6 if slow else 0.35)
        if w <= 0: return
        ph = math.sin(2 * PI * max(0.0, t - t0 - (0.5 if slow else 0.3)) / per)
        self._arm(P, side, w, 150.0 + 40.0 * ph, -150.0 * height - 20.0 * abs(ph), 60.0, 'wave' if not self.sp.get('bunny') else 'paw_open',
                  up=1.0, rot=-side * 18.0 * ph)
        P.tilt += -side * 1.2 * w * ph
    return self._add(t0, t1 + 0.8, fn)


def _acting_point_at(self, t0, target, t1=None, side=1, dur=0.6, z=200.0, fade=0.5):
    """Lift an arm and point at a target (design point / actor part): the arm extends straight along the line from the
    shoulder to the target, the head looks along it."""
    def fn(P, t):
        w = _env(t, t0, t1, dur, fade)
        if w <= 0.001: return
        tx, ty = _target_xy(target, t)
        sp = self.sp
        B = Body(sp, P)
        x, y, zz = _world_to_body(self, P, B, tx, ty, z)
        S = np.array([side * (sp['body']['sh'] - 17), B.y_sh + 20, 0.0])
        d = np.array([x, y, zz]) - S; n = float(np.linalg.norm(d)) or 1.0
        Wt = S + d / n * _arm_len(sp) * 0.93
        rel = Wt - S
        pre = 'hl_' if side > 0 else 'hr_'
        self._arm(P, side, w, side * rel[0], rel[1], rel[2], 'point' if not sp.get('bunny') else 'paw_point', up=0.0)
    return _acting_post(self, t0, None if t1 is None else t1 + fade, fn)


def _acting_hum(self, t0, t1=None, amount=1.0, fade=0.5, rate=1.0):
    """Closed-mouth humming (the Pemberton's jingle): lips pressed in a soft smile, a slow sway of the head on the beat
    (about 2 beats a second), the brows a touch lifted and calm. No lip sync (it is not speech)."""
    def fn(P, t):
        w = _env(t, t0, t1, fade, fade) * amount
        if w <= 0: return
        beat = math.sin(2 * PI * 1.05 * rate * (t - t0))
        P.m_press += 0.45 * w; P.smile += 0.32 * w; P.m_open *= (1.0 - w)
        P.h_tilt += 4.0 * w * beat; P.sway += 3.0 * w * beat
        P.brow_up += 0.12 * w
        P.hum = max(getattr(P, 'hum', 0.0), w)
    return self._add(t0, None if t1 is None else t1 + fade, fn)


def _acting_knock_pattern(self, t0, pattern=(2, 3, 2), side=1, beat=0.28, gap=0.62, target=None, z=0.0, kind='door'):
    """Knock a pattern (Grandma's family knock 2-3-2; seven knocks): the fist comes to the door (target design point,
    or out in front), a forearm snap per knock. Returns knock_door events (one per hit, params n and group)."""
    evs = []
    tt = t0 + 0.45
    hits = []
    for g, n in enumerate(pattern):
        for k in range(n):
            hits.append((tt, g)); tt += beat
        tt += gap - beat
    t_end = hits[-1][0] + 0.5
    def pulse(t):
        v = 0.0
        for (th, _) in hits:
            dt = t - th
            if -0.12 < dt < 0.0: v = max(v, 1.0 - (-dt) / 0.12)
            elif 0.0 <= dt < 0.16: v = max(v, 1.0 - dt / 0.16)
        return v
    if target is not None:
        self.reach_to(t0, side, target, t1=t_end, dur=0.4, z=z, contact='tips', shape='fist', fade=0.5)
        def fn(P, t):
            if t0 + 0.3 < t < t_end:
                pre = 'hl_' if side > 0 else 'hr_'
                p = pulse(t)
                setattr(P, pre + 'fwd', getattr(P, pre + 'fwd') - 26.0 * (1.0 - p))
                setattr(P, pre + 'shape', 'fist')
        _acting_post(self, t0, t_end, fn)
    else:
        def fn(P, t):
            w = _env(t, t0, t_end, 0.4, 0.5)
            if w <= 0: return
            self._arm(P, side, w, 30.0, -10.0 - 10.0 * pulse(t), 170.0 + 30.0 * pulse(t), 'fist', up=0.0)
        self._add(t0, t_end + 0.5, fn)
    for i, (th, g) in enumerate(hits):
        evs.append(self._ev(th, 'knock_door', -2.0 if kind == 'table' else 0.0, pan=0.0, n=1, group=g, index=i, kind=kind))
    return evs


def _acting_eyes_shut(self, t0, t1=None, squeeze=1.0, fade=0.15):
    """Eyes shut (squeezed when squeeze > 0.5: brows pinched down, the face scrunched)."""
    def fn(P, t):
        w = _env(t, t0, t1, fade, 0.25)
        if w <= 0: return
        P.lid_l = max(P.lid_l, w); P.lid_r = max(P.lid_r, w)
        if squeeze > 0.3:
            P.squint += 0.6 * w * squeeze; P.brow_angry += 0.3 * w * squeeze; P.brow_sad += 0.4 * w * squeeze
            P.m_press += 0.5 * w * squeeze
    return self._add(t0, None if t1 is None else t1 + 0.3, fn)


Acting.sit_on = _acting_sit_on
Acting.seated = _acting_seated
Acting.stand_up = _acting_stand_up
Acting.kneel_down = _acting_kneel_down
Acting.run = _acting_run
Acting.wave = _acting_wave
Acting.point_at = _acting_point_at
Acting.hum = _acting_hum
Acting.knock_pattern = _acting_knock_pattern
Acting.eyes_shut = _acting_eyes_shut


# ------------------------------------------------------------------------------------------- contact clips (v3 staging)
def _acting_face(self, turn, h_turn=0.0, t0=-INF, t1=None):
    """Base facing from t0 (quarter turns: + faces screen right). Use it to stage the opening pose of a shot."""
    return self.set(t0, t1, 0.001 if t0 == -INF else 0.4, turn=turn, h_turn=h_turn)


def _acting_hand_over(self, t0, side, other, part='eyes', t1=None, dur=0.7, z=60.0, fade=0.5):
    """Lay a hand over another actor's eyes / mouth / head (palm on the part, the back of the hand to camera)."""
    return self.reach_to(t0, side, (other, part), t1=t1, dur=dur, z=z, contact='palm', shape='open', fade=fade)


def _acting_hold_hand(self, t0, side, other, other_side, t1=None, dur=0.6, fade=0.5, lift=None):
    """Hold hands with another actor: the hands meet near the taller one's hanging hand, a little above it (lift px;
    None = 5 % of the taller figure: a hanging arm is already almost straight, so a meeting point below it is out of
    reach), the shorter one reaching up. Solved before either reach, so the two never chase each other."""
    if lift is None: lift = 0.05 * max(self.height, other.height)
    def meet(t):
        a = self.where(t, 'hand_l' if side > 0 else 'hand_r', post=False)
        b = other.where(t, 'hand_l' if other_side > 0 else 'hand_r', post=False)
        # the taller one's arm hangs naturally and the shorter one reaches up to it (weighted by real height)
        ha, hb = self.sp.get('m', 1.7), other.sp.get('m', 1.7)
        k = clamp(0.5 + 2.0 * (ha - hb) / (ha + hb), 0.15, 0.85)     # 0.5 = equal heights; -> 0.85 for the much taller
        return ((a[0] + b[0]) * 0.5, b[1] + (a[1] - b[1]) * k - lift)
    self.reach_to(t0, side, meet, t1=t1, dur=dur, contact='palm', shape='grip', fade=fade)
    other.reach_to(t0, other_side, meet, t1=t1, dur=dur, contact='palm', shape='grip', fade=fade)
    return self


def _acting_smooth_hair(self, t0, side, other, n=2, stroke=0.9, t1=None):
    """Smooth another actor's hair: the palm lands on the crown and strokes back over the head n times."""
    def tgt(t):
        cx, cy = other.where(t, 'crown', post=False)
        hx, hy = other.where(t, 'head', post=False)
        ph = max(0.0, t - t0 - 0.5) / stroke
        k = 0.5 - 0.5 * math.cos(2 * PI * min(ph, n))
        sgn = 1.0 if other._raw(t, False).turn >= 0 else -1.0
        return cx + (hx - cx) * 0.1 - 22.0 * k * sgn, cy + (hy - cy) * 0.12 + 6.0 * k
    t_end = t0 + 0.5 + n * stroke
    return self.reach_to(t0, side, tgt, t1=t1 if t1 is not None else t_end, dur=0.5, z=40.0, contact='palm', shape='relaxed', fade=0.5)


def _acting_head_to(self, t0, target, part='eyes', t1=None, dur=0.8, fade=0.6, max_lean=0.55):
    """Bring a face part (the eye to a peephole, the face into a hand, the mouth to an ear) to a target point by bending
    at the hips and shifting the body (pose.lean, dx, dy, crouch) in the post pass."""
    def fn(P, t):
        w = _env(t, t0, t1, dur, fade)
        if w <= 0.001: return
        tx, ty = _target_xy(target, t)
        for it in range(3):
            ox, oy, s = _origin(self, P)
            X, Y = _body_point(self, P, part)
            ex, ey = ox + X * s, oy + Y * s
            dx, dy = (tx - ex) / s, (ty - ey) / s
            # lower the head by leaning forward (toward the side the figure faces) and crouching, then slide the rest
            if dy > 0:
                need = clamp(dy / 520.0, 0.0, max_lean)
                P.lean += need * w * 0.5
                P.crouch += clamp((dy - 260.0 * max_lean) / 200.0, 0.0, 1.2) * w * 0.5 if dy > 260 * max_lean else 0.0
            elif dy < 0:
                P.tiptoe = max(getattr(P, 'tiptoe', 0.0), clamp(-dy / 40.0) * w)
            ox, oy, s = _origin(self, P)
            X, Y = _body_point(self, P, part)
            ex, ey = ox + X * s, oy + Y * s
            P.dx += (tx - ex) * w * 0.85
            if abs(ty - ey) < 60 and dy > 0: P.dy += (ty - ey) * 0.0
    return _acting_post(self, t0, None if t1 is None else t1 + fade, fn)


def _acting_crouch(self, t0, amount=1.0, t1=None, dur=0.7, fade=0.6):
    """Crouch down (knees bent, hips lowered, a forward lean), e.g. to the doormat or a mail slot."""
    def fn(P, t):
        w = _env(t, t0, t1, dur, fade) * amount
        if w <= 0: return
        P.crouch += 1.4 * w; P.lean += 0.18 * w; P.stance += 0.35 * w
    return self._add(t0, None if t1 is None else t1 + fade, fn)


def _acting_lie(self, t0, face='up', dur=0.01, t1=None, arms='out', knees=0.15):
    """Lie on the floor (face 'up' or 'down'): for a lying figure draw() takes y_feet = the surface it lies on. arms 'out'
    flung out, 'side' along the body; knees a little bent."""
    def fn(P, t):
        w = ease_in_out(prog(t, t0, t0 + dur)) if dur > 0.02 else float(t >= t0)
        if t1 is not None: w *= 1.0 - ease_in_out(prog(t, t1, t1 + 0.8))
        if w <= 0: return
        P.lie = (-1.0 if face == 'up' else 1.0) * w
        if arms == 'out':
            for side in (-1, 1): self._arm(P, side, w, 150.0, 240.0, -40.0 + 30 * side, 'relaxed', up=0.0)
        P.crouch += knees * w
        P.still = max(P.still, 0.0)
    return self._add(t0, None if t1 is None else t1 + 0.8, fn)


def _acting_dead(self, t0, fade=0.6):
    """Life leaves the face: lids sink half shut, the eyes go still, the mouth falls slack, no breath, no blinks."""
    def fn(P, t):
        w = ease_in_out(prog(t, t0, t0 + fade))
        if w <= 0: return
        P.still = max(P.still, w); P.life *= (1.0 - w); P._noblink = max(getattr(P, '_noblink', 0.0), w)
        P.eye_open = lerp(P.eye_open, 0.45, w); P.pupil = lerp(P.pupil, 1.25, w); P.m_open = lerp(P.m_open, 0.12, w)
        P.brow_sad *= (1.0 - 0.6 * w); P.brow_up *= (1.0 - 0.6 * w); P.breath = lerp(P.breath, 0.5, w)
        P.look_x *= (1.0 - w); P.look_y *= (1.0 - w); P.tremble *= (1.0 - w)
    return self._add(t0, None, fn)


def _acting_unmask(self, t0, dur=1.2, amount=1.0):
    """The Bunnyman's foam head slides half off (pose.unmask), uncovering Dale's face beneath."""
    def fn(P, t):
        P.unmask = max(getattr(P, 'unmask', 0.0), amount * ease_in_out(prog(t, t0, t0 + dur)))
    return self._add(t0, None, fn)


def _acting_drag_hatchet(self, t0, t1=None, side=-1):
    """Carry the old hatchet hanging from one paw / hand, its head down by the feet (it knocks on each step)."""
    self.hold_prop('hatchet', side, t0, t1)
    def fn(P, t):
        w = _env(t, t0, t1, 0.4, 0.4)
        self._arm(P, side, w, 22.0, 352.0, -30.0, 'grip', up=0.0, rot=0.0)
    return self._add(t0, None if t1 is None else t1 + 0.4, fn)


def _acting_climb(self, t0, t1, x_from, y_rise, n_steps, run_px, surface='stairs', hatchet=None):
    """Climb n_steps stairs from t0 to t1: a slow walk cycle in profile (dx += run_px per step) with the body rising
    y_rise px per step (pose.dy), one foot per step. Returns footstep events and, with hatchet=side, a 'hatchet_thunk'
    after each step (the head knocking against the stair)."""
    dur = (t1 - t0) / n_steps
    evs = []
    face = 1.0 if run_px >= 0 else -1.0
    def fn(P, t):
        u = clamp((t - t0) / (t1 - t0))
        k = u * n_steps
        i = min(int(k), n_steps - 1) if u < 1 else n_steps
        f = k - int(k) if u < 1 else 0.0
        e = ease_in_out(clamp(f / 0.7))
        P.dx = x_from + run_px * (min(i, n_steps) + (e if u < 1 else 0.0))
        P.dy = -y_rise * (min(i, n_steps) + (e if u < 1 else 0.0))
        P.walk_amt = max(P.walk_amt, 0.75 * _env(t, t0, t1, 0.3, 0.3))
        P.walk_ph = 0.5 * k
        P.turn = lerp(P.turn, face, _env(t, t0 - 0.3, t1, 0.3, 0.3))
        P.lean += 0.12 * _env(t, t0, t1, 0.4, 0.4)
    if not getattr(self, '_walked', False):
        self._walked = True
        self.clips.append((-INF, t0 - 0.3, lambda P, t: (setattr(P, 'dx', x_from)), False))
    self._add(t0 - 0.3, None, fn)
    for k in range(n_steps):
        tt = t0 + (k + 0.7) * dur
        evs.append(self._ev(tt, 'footsteps_wood_inside', -1.0, pan=0.0, n=1, kind='stair', step=k))
        if hatchet is not None:
            evs.append(self._ev(tt + 0.22, 'hatchet_thunk', 0.0, pan=0.0, step=k))
    return evs


def _acting_mama(self, t0, dur=0.9):
    """Dale's lips form "Mama" (two M closures, two A openings): a whisper."""
    return self.talk([(t0, t0 + dur, 'Mama')], env=None, words=None, intensity=0.7)


def _acting_open_egg(self, t0, egg_track=None, dur=1.6, ring=True):
    """Open the plastic egg held in both hands: the right hand holds it (prop 'egg'), the left comes to it, a twist, and
    it splits: the left hand lifts the top half, the right keeps the bottom half (with Dad's ring in it). Returns the
    split time and a 'egg_open' event."""
    ts = t0 + 0.55 * dur
    self.hold_prop('egg', -1, -INF, ts)
    self.hold_prop('egg_bot_ring' if ring else 'egg_bot', -1, ts, None)
    self.hold_prop('egg_top', 1, ts, None)
    # the egg comes up in front of the lower chest, near the centre line, elbow bent: close enough to look into, and it
    # reads in any view (front, 3/4 or profile)
    self.reach(t0 - 0.4, None, -1, out=-50.0, down=100.0, fwd=170.0, shape='grip', up=0.0, fade=0.4)
    tgt = lambda t: self.grip_point(t, -1, 'egg', post=False)    # noqa: E731
    self.reach_to(t0, 1, tgt, t1=ts, dur=0.5 * dur, contact='palm', shape='grip', z=170.0, fade=0.3)
    def fn(P, t):
        u = prog(t, ts, ts + 0.45 * dur)
        if t < ts: P.hr_rot += -14.0 * math.sin(PI * prog(t, t0 + 0.35 * dur, ts))
        w1 = ease_in_out(prog(t, t0, t0 + 0.5 * dur))        # under the reach_to: the arm is already at the egg when the
        if w1 > 0:                                            # contact solve lets go, so the hand never drops
            e = ease_in_out(u)
            self._arm(P, 1, w1, -100.0 + 145.0 * e, 95.0 - 40.0 * e, 175.0 - 15.0 * e, 'grip', up=0.0)  # lid up and away
            if e > 0:
                self._arm(P, -1, e, -50.0, 100.0 - 25.0 * e, 160.0, 'grip', up=0.0)    # the cup comes up to the eyes
            P.hl_rot += -30.0 * e
    self._add(t0, None, fn)
    return ts, self._ev(ts, 'egg_open', 0.0, pan=0.0)


Acting.face = _acting_face
Acting.hand_over = _acting_hand_over
Acting.hold_hand = _acting_hold_hand
Acting.smooth_hair = _acting_smooth_hair
Acting.head_to = _acting_head_to
Acting.crouch = _acting_crouch
Acting.lie = _acting_lie
Acting.dead = _acting_dead
Acting.unmask = _acting_unmask
Acting.drag_hatchet = _acting_drag_hatchet
Acting.climb = _acting_climb
Acting.mama = _acting_mama
Acting.open_egg = _acting_open_egg



# ------------------------------------------------------------------------------------------- expressions (this film)
EXPR.update({
    'warm_smile': dict(smile=0.55, teeth=0.2, squint=0.15, brow_up=0.12),                       # Mom as people see her
    'too_still': dict(smile=0.4, m_press=0.32, still=0.55, pupil=0.78, lock=0.55, brow_up=0.05),  # the smile that never moves
    'proud': dict(smile=0.72, teeth=0.35, brow_up=0.32, squint=0.1, pupil=0.85),
    'little_girl': dict(wide=0.6, brow_sad=1.0, brow_up=0.55, wet=1.0, tears=0.55, pupil=1.25, m_open=0.08, m_round=0.3,
                        tremble=0.5, smile=-0.3),                                                # Dale's face: Laurie inside
    'terror': dict(wide=0.9, pupil=0.45, brow_sad=0.9, brow_up=0.7, m_open=0.32, m_round=0.35, smile=-0.45, tremble=0.7, sweat=0.4),
    'haunted': dict(eye_open=0.88, pupil=0.95, brow_sad=0.6, brow_up=0.15, smile=-0.15, wet=0.4),
    'wrong_smile': dict(smile=0.62, grin=0.08, teeth=0.25, pupil=0.72, lock=0.8, still=0.4, brow_up=0.08),
    'sleep': dict(lid_l=1.0, lid_r=1.0, m_open=0.05, h_nod=0.18, still=0.3),
    'determined': dict(brow_angry=0.55, brow_sad=0.25, m_press=0.6, squint=0.15, wide=0.15),
})


def _bunny_unmasked_head(c, who, P, yaw, pitch, det, t, light, sp):
    """The suit's head half off (pose.unmask 0..1): Dale's face (55, gaunt, grey stubble) with the wide wet eyes of a
    terrified little girl, his lips free to move ("Mama"); the foam head tipped back off his crown, its dark neck opening
    showing, the ears splayed."""
    u = clamp(getattr(P, 'unmask', 0.0))
    ds = CAST['dale']
    fsz = ds['hh'] / sp['hh'] * 1.02                       # Dale's head inside the big foam head
    fc = c.sub(0.0, 26.0 * u, 0.0, fsz)
    draw_head_local(fc, 'dale', P, yaw, pitch, det, t, light, ds)
    # the foam head, tipped back off the crown: pushed up past the forehead, foreshortened as it tips away, a little
    # to one side; the dark inside of its neck opening shows as a band along its lower rim
    sgn = 1.0 if math.sin(yaw) >= 0 else -1.0
    mc = c.sub(-sgn * 14.0 * u, -104.0 * u, -sgn * 14.0 * u, 1.0, 1.0 - 0.3 * u)
    Pm = P.copy(); Pm.m_open = 0.0
    hm = draw_head_local(mc, who, Pm, yaw, pitch - 0.45 * u, det, t, light, sp)
    if u > 0.05:
        ys = np.linspace(-1.0, 1.0, 13)
        w_ = 88.0
        lower = [(x * w_, 112.0 - 10.0 * (1 - x * x)) for x in ys]
        upper = [(x * w_ * 0.86, 112.0 - (10.0 + 26.0 * u) * (1 - x * x) ** 0.7) for x in ys[::-1]]
        band = smooth(lower + upper, True, 0.8)
        mc.fill(band, '#140e0d', 235 * clamp(u * 2.0))
        mc.line(smooth(lower, False, 0.8), mc.lw * 0.9)


EXPR_BUNNY = ('warm_smile', 'too_still', 'proud', 'little_girl', 'terror', 'haunted', 'wrong_smile', 'sleep', 'determined')



# ====================================================================================================== the crayon drawing
# Slid under the bathroom door: a bridge, a tall man lying on the ground, a lady over him holding a rock with a big wide
# smile, and a grey bunny with blue crayon tears; "I TRIED TO HELP HIM" in shaky letters in the corner.
_STROKE_FONT = {
    'I': [[(0.5, 0), (0.5, 1)], [(0.2, 0), (0.8, 0)], [(0.2, 1), (0.8, 1)]],
    'T': [[(0, 0), (1, 0)], [(0.5, 0), (0.5, 1)]],
    'R': [[(0, 1), (0, 0), (0.8, 0.05), (0.85, 0.4), (0, 0.5)], [(0.3, 0.5), (0.95, 1)]],
    'E': [[(0.9, 0), (0, 0), (0, 1), (0.9, 1)], [(0, 0.5), (0.7, 0.5)]],
    'D': [[(0, 0), (0, 1), (0.6, 0.95), (0.9, 0.5), (0.6, 0.05), (0, 0)]],
    'O': [[(0.5, 0), (0.95, 0.3), (0.9, 0.8), (0.5, 1), (0.1, 0.8), (0.05, 0.3), (0.5, 0)]],
    'H': [[(0, 0), (0, 1)], [(0.9, 0), (0.9, 1)], [(0, 0.5), (0.9, 0.5)]],
    'L': [[(0, 0), (0, 1), (0.85, 1)]],
    'P': [[(0, 1), (0, 0), (0.8, 0.05), (0.85, 0.4), (0, 0.5)]],
    'M': [[(0, 1), (0, 0), (0.45, 0.6), (0.9, 0), (0.9, 1)]],
}


def _crayon(c, pts, colr, w, seed=0, a=230, passes=3, jit=1.0, closed=False):
    """A waxy crayon stroke: a few jittery passes over the same line with gaps where the wax skips."""
    for p_ in range(passes):
        q = []
        for i, (x, y) in enumerate(pts):
            q.append((x + (hash01(i + 31 * p_ + seed * 7, 501) - 0.5) * 0.42 * jit, y + (hash01(i + 31 * p_ + seed * 7, 502) - 0.5) * 0.42 * jit))
        path = smooth(q, closed, 0.6) if len(q) > 2 else poly(q, closed)
        c.line(path, w * (1.0 - 0.18 * p_), colr, a * (0.85 if p_ else 1.0))


def _crayon_fill(c, path, colr, seed=0, a=170, ang=0.6, gap=2.2, w=1.4):
    """Scribble-fill a shape with crayon hatching (clipped)."""
    bb = path.getBounds()
    ls = []
    L = max(bb.width(), bb.height()) * 1.5
    n = int(L / gap) + 2
    for k in range(-n, n):
        x0 = bb.centerX() + k * gap; y0 = bb.centerY()
        dx, dy = math.cos(ang) * L, math.sin(ang) * L
        j = (hash01(k + 4000 + seed * 13, 503) - 0.5) * 0.25
        ls.append(poly([(x0 - dx + j, y0 - dy), (x0 + dx + j, y0 + dy)], False))
    with c.clip(path):
        c.line(_multi(ls), w, colr, a)


def _crayon_page(c, x, y, w, h, det, t, corner=False):
    """The drawing on a sheet w x h (local units) centred at (x, y) (corner=True: held at its top-left corner)."""
    if corner: x, y = x + w * 0.5 - 1.0, y + h * 0.5 - 1.0
    k = w / 21.0                                            # drawn on a 21 x 29.7 unit page
    pc = c.sub(x - w / 2, y - h / 2, 0.0, k)
    pc.lw = c.lw / k
    page = poly([(0, 0.3), (21, 0), (20.8, 29.7), (0.2, 29.5)], True)
    pc.fill(page, '#f4efe2')
    if det >= 1: pc.texture(page, 'paper', 0.25, 0.08)
    pc.line(poly([(0.3, 14.6), (20.7, 14.9)], False), pc.lw * 0.25, '#c9c0aa', 160)          # the fold
    lw = 0.3
    # night sky scribble and a yellow moon
    sky = poly([(1, 1), (20, 1), (20, 7), (1, 7.5)], True)
    if det >= 1: _crayon_fill(pc, sky, '#2b3f8a', 1, 90, 0.25, 0.42, 0.2)
    _crayon(pc, [(17.6 + 1.4 * math.cos(a), 5.4 + 1.4 * math.sin(a)) for a in np.linspace(0, 2 * PI, 12)], '#e8b820', lw * 1.2, 2, closed=True)
    if det >= 1: _crayon_fill(pc, oval(17.6, 5.4, 1.3), '#f2c830', 3, 200, 0.9, 0.3, 0.22)
    # the railroad bridge: a deck with X trestles
    _crayon(pc, [(1.0, 10.5), (13.5, 10.0)], '#4a2e1c', lw * 1.3, 4)
    _crayon(pc, [(1.0, 11.3), (13.5, 10.8)], '#4a2e1c', lw * 1.0, 5)
    for k in range(4):
        x0 = 1.8 + k * 3.2
        _crayon(pc, [(x0, 11.2), (x0 + 2.8, 15.5)], '#4a2e1c', lw * 0.9, 6 + k)
        _crayon(pc, [(x0 + 2.8, 11.1), (x0, 15.5)], '#4a2e1c', lw * 0.9, 9 + k)
    # grass
    _crayon(pc, [(0.8 + 0.5 * k + (0.25 if k % 2 else 0), 27.6 - (0.9 if k % 2 else 0)) for k in range(40)], '#3f8a3a', lw * 0.9, 11, passes=2)
    # the tall man lying on the ground (Dad), X eyes, not moving
    _crayon(pc, [(2.0, 24.4), (9.6, 24.0)], '#3a2a20', lw * 1.1, 12)              # body
    _crayon(pc, [(9.6, 24.0), (11.6, 23.0)], '#3a2a20', lw, 13); _crayon(pc, [(9.6, 24.0), (11.8, 25.0)], '#3a2a20', lw, 14)
    _crayon(pc, [(4.0, 24.3), (5.0, 22.6)], '#3a2a20', lw, 15); _crayon(pc, [(4.0, 24.3), (5.4, 25.8)], '#3a2a20', lw, 16)
    _crayon(pc, [(0.6 + 1.1 * math.cos(a), 24.3 + 1.1 * math.sin(a)) for a in np.linspace(0, 2 * PI, 10)], '#3a2a20', lw, 17, closed=True)
    _crayon(pc, [(0.2, 23.9), (0.7, 24.4)], '#3a2a20', lw * 0.7, 18); _crayon(pc, [(0.7, 23.9), (0.2, 24.4)], '#3a2a20', lw * 0.7, 19)
    _crayon(pc, [(1.6, 23.2), (3.4, 23.3)], '#e8c840', lw * 0.8, 20)              # the flashlight still on beside him
    # the lady over him: pink triangle dress, red hair, a big wide smile, a grey rock held up
    _crayon(pc, [(10.6, 23.6), (12.4, 17.6), (14.2, 23.6), (10.6, 23.6)], '#d97a8a', lw * 1.1, 21, closed=True)
    if det >= 1: _crayon_fill(pc, poly([(10.6, 23.6), (12.4, 17.6), (14.2, 23.6)]), '#e88a9a', 22, 170, 0.8, 0.3, 0.22)
    _crayon(pc, [(11.6, 23.6), (11.4, 25.6)], '#3a2a20', lw, 23); _crayon(pc, [(13.2, 23.6), (13.4, 25.6)], '#3a2a20', lw, 24)
    _crayon(pc, [(12.4 + 1.25 * math.cos(a), 16.2 + 1.25 * math.sin(a)) for a in np.linspace(0, 2 * PI, 10)], '#3a2a20', lw, 25, closed=True)
    _crayon(pc, [(11.0, 15.4), (11.2, 14.4), (12.4, 14.0), (13.6, 14.4), (13.9, 15.6)], '#b8442a', lw * 1.4, 26)
    _crayon(pc, [(11.25, 16.0), (11.6, 16.9), (12.4, 17.25), (13.2, 16.9), (13.55, 16.0)], '#c0283a', lw * 1.0, 27)   # the big wide smile
    _crayon(pc, [(11.25, 16.0), (12.4, 16.35), (13.55, 16.0)], '#c0283a', lw * 0.8, 47)
    _crayon(pc, [(12.9, 18.6), (14.6, 15.2)], '#3a2a20', lw, 28)
    _crayon(pc, [(14.9 + 1.0 * math.cos(a), 14.4 + 0.8 * math.sin(a)) for a in np.linspace(0, 2 * PI, 9)], '#6f6f74', lw * 1.1, 29, closed=True)
    if det >= 1: _crayon_fill(pc, oval(14.9, 14.4, 0.9, 0.7), '#7a7a80', 30, 210, 0.5, 0.25, 0.2)
    # the grey bunny beside them, one ear bent, blue crayon tears running down
    bx, by = 17.4, 21.6
    _crayon(pc, [(bx + 1.6 * math.cos(a), by + 2.2 * math.sin(a)) for a in np.linspace(0, 2 * PI, 12)], '#6f6f74', lw * 1.1, 31, closed=True)
    if det >= 1: _crayon_fill(pc, oval(bx, by, 1.5, 2.1), '#8a8a90', 32, 160, 0.9, 0.3, 0.22)
    _crayon(pc, [(bx + 1.2 * math.cos(a), by - 3.4 + 1.2 * math.sin(a)) for a in np.linspace(0, 2 * PI, 10)], '#6f6f74', lw * 1.1, 33, closed=True)
    _crayon(pc, [(bx + 0.5, by - 4.4), (bx + 0.9, by - 7.6)], '#6f6f74', lw * 1.2, 34)
    _crayon(pc, [(bx - 0.5, by - 4.4), (bx - 0.9, by - 5.6), (bx - 2.2, by - 5.0)], '#6f6f74', lw * 1.2, 35)
    pc.fill(oval(bx - 0.45, by - 3.6, 0.22), '#1a1a1a'); pc.fill(oval(bx + 0.45, by - 3.6, 0.22), '#1a1a1a')
    _crayon(pc, [(bx - 0.4, by - 2.7), (bx, by - 2.95), (bx + 0.4, by - 2.7)], '#3a3a40', lw * 0.7, 46)
    for sd in (-1, 1):
        _crayon(pc, [(bx + sd * 0.45, by - 3.2), (bx + sd * 0.6, by - 1.6), (bx + sd * 0.5, by + 0.4)], '#2f6fd8', lw * 0.9, 36 + sd, passes=2)
    # I TRIED TO HELP HIM, shaky, in the corner
    txt = 'I TRIED TO HELP HIM'
    x0, y0, ch = 1.4, 1.9, 0.9
    xx = x0
    lines = []
    for i, chh in enumerate(txt):
        if chh == ' ':
            xx += ch * 0.55; continue
        for stroke in _STROKE_FONT.get(chh, []):
            pts = [(xx + u * ch * 0.7 + (hash01(i * 7 + j, 511) - 0.5) * 0.12, y0 + v * ch * 1.15 + (hash01(i * 7 + j, 512) - 0.5) * 0.12 + 0.12 * math.sin(i * 1.7))
                   for j, (u, v) in enumerate(stroke)]
            lines.append(pts)
        xx += ch * 0.92
    sc = min(1.0, 14.0 / max(1.0, xx - x0))
    for j, pts in enumerate(lines):
        _crayon(pc, [(x0 + (x - x0) * sc, y0 + (y - y0) * sc) for x, y in pts], '#14182e', lw * 0.75, 40 + j, passes=2, jit=0.4)
    pc.line(page, pc.lw * 0.45, '#9a917e')


def draw_crayon_drawing(pen, cx, cy, w, t=0.0, angle=0.0, detail=2):
    """The crayon drawing as an insert: a sheet w design px wide (A4 proportions) centred at (cx, cy), turned by angle."""
    c = Ctx(pen, skia.Matrix(), _lw_for(w * 0.35)).sub(cx, cy, angle, 1.0)
    _crayon_page(c, 0.0, 0.0, w, w * 29.7 / 21.0, detail, t)


# the narrator at six (Grandma teaches the family knock): the same hair and eyes, child proportions, striped pajamas
CAST['narrator_kid'] = _v3cast(outfit='pj3', feet='socks', **dict(_JUNE, hair='chin', hair_c='#4a2a1f', brow_c='#3a2118',
                                                                   iris_c='#7a7a4c', part=1, sex='n', m=1.15, lashes=0.2),
                               cloth=dict(top='#c9b07a', top_sh='#9a8350', top_hi='#e2cc98', trim='#f4f0e2', print_c='#8a6a3a',
                                          print_c2='#f4f0e2', trousers='#c9b07a', trousers_sh='#9a8350', socks='#c9c6c0',
                                          socks_sh='#9a978f'))
BUNNY_CAST = BUNNY_CAST + ('narrator_kid',)



def torch_pos3(actor, t, side=1):
    """Design-space (x, y, angle deg) of the lens of the 'maglite' (Dad's flashlight) held in a hand, for
    draw_torch_beam(pen, x, y, angle, ...). pose.torch_ang aims it (0 = up, 90 = screen right)."""
    gx, gy = actor.grip_point(t, side, 'maglite')
    P = actor.at(t)
    a = math.radians(getattr(P, 'torch_ang', 0.0))
    k = actor.height / (actor.sp.get('m', 1.7) * 100.0)          # px per cm
    return gx + math.sin(a) * 20.5 * k, gy - math.cos(a) * 20.5 * k, P.torch_ang


def _acting_foot_gap(self, t):
    """Height in design px of the lower planted sole above the floor plane (0 = a foot on the floor); a figure lying,
    kneeling or sitting on the floor reports its lowest contact. Used by the clip checks."""
    P = self.at(t); sp = self.sp
    if abs(getattr(P, 'lie', 0.0)) > 0.5: return 0.0
    B = Body(sp, P)
    lows = []
    for side in (-1, 1):
        H, K, A, pitch = _leg_chain(sp, B, P, side)
        lows.append(max(0.0, -(A[1] + 38.0)))
        if B.kneel > 0.5 and not (side > 0 and B.knees < 0.5): lows.append(max(0.0, -(K[1] + 30.0)))
    return min(lows) * self.height / 1000.0


Acting.foot_gap = _acting_foot_gap


_draw_arm_public_v2 = draw_arm


def draw_arm(pen, who, side=1, pose=None, x=None, y_feet=None, height=None, cx=None, cy=None, scale=None, light=None,
             detail=None, t=None):
    """Draw ONE arm (sleeve, hand, held prop) exactly where draw() / draw_bust() puts it: use it to bring a hand in front
    of another figure (Mom's hand smoothing June's hair from behind her, a hand on a shoulder). v3 cast and the
    Bunnyman's paws included."""
    sp = CAST[who]
    if not (sp.get('v3') or sp.get('bunny')):
        return _draw_arm_public_v2(pen, who, side, pose, x, y_feet, height, cx, cy, scale, light, detail, t)
    P = _as_pose(pose); t = P.t if t is None else t
    if cx is not None:
        k = 1.0 + 1.1 * clamp(P.approach)
        head_px = 600.0 * (scale or 1.0) * k
        s_ = head_px / sp['hh']
        c = Ctx(pen, skia.Matrix(), _lw_for(head_px)).sub(cx, cy + 60.0 * (scale or 1.0) * clamp(P.approach) - (-1000 + sp['hh'] / 2) * s_, 0.0, s_)
    else:
        s_ = height / 1000.0; head_px = sp['hh'] * s_
        py = clamp(getattr(P, 'perch', 0.0)) * clamp(P.sit) * 222.0 * s_
        c = Ctx(pen, skia.Matrix(), _lw_for(head_px)).sub(x + P.dx, y_feet + P.dy + py, 0.0, s_)
    det = _auto_detail(pen, head_px) if detail is None else detail
    B = Body(sp, P)
    if sp.get('bunny'):
        _bunny_arm(c, sp, B, P, side, det, t, light); return
    skin, skin_sh, _ = _skin_cols(sp, P, light)
    sleeve, sleeve_sh = _limb_cols3(sp)[:2]
    _draw_arm3(c, sp, B, P, side, det, t, skin, skin_sh, sleeve, sleeve_sh, light)


# ------------------------------------------------------------------------------------------- small heads (wide shots)
def _feat_k(c):
    """Line-weight factor for facial features from the head's size on the render target: features stay crisp and the
    eyes stay open on wide shots (a 40 px head would otherwise get outlines as wide as its eyes)."""
    m = c.cv.getTotalMatrix()
    sc = math.sqrt(abs(m.getScaleX() * m.getScaleY() - m.getSkewX() * m.getSkewY()))
    head_px = 240.0 * c.s * sc
    return clamp(head_px / 260.0, 0.32, 1.0), head_px


def _wrap_feature(fn):
    def w(c, hm, sp, P, *a, **kw):
        if not sp.get('v3') or sp.get('bunny'): return fn(c, hm, sp, P, *a, **kw)
        k, hpx = _feat_k(c)
        if k >= 0.999: return fn(c, hm, sp, P, *a, **kw)
        lw0 = c.lw
        c.lw = lw0 * k
        try:
            return fn(c, hm, sp, P, *a, **kw)
        finally:
            c.lw = lw0
    return w


_eye_v3_full = _eye
_eye = _wrap_feature(_eye_v3_full)
_brow = _wrap_feature(_brow)
_mouth = _wrap_feature(_mouth)
_nose = _wrap_feature(_nose)


# ====================================================================================================== self-test
_REF_VOICE = os.path.join(_HERE, '..', '..', 'Dummy Video', 'film', '_work', 'align')


def _selftest_bunny():
    """The Bunnyman film's checks: every new id draws in every view and state; reach_to lands the palm on reachable
    targets; sitting keeps the feet on the floor and the hips on the seat; kneeling keeps the feet down; the planted
    walk does not slide; a prop picked up does not jump; look_at turns toward the target; hands held while walking meet."""
    out = []
    set_render_size(480, 270)
    surf = skia.Surface(CFG.rw, CFG.rh); pen = Pen(surf.getCanvas()); surf.getCanvas().scale(CFG.k, CFG.k)
    for who in BUNNY_CAST:
        for yaw in (0.0, 0.5, -0.5, 1.0, 1.5, 2.0):
            draw(pen, who, 960, 1000, 700, Pose(turn=yaw, kneel=0.5 if yaw == 1.5 else 0.0, sit=0.6 if yaw == 1.0 else 0.0,
                                                seat=250.0 if yaw == 1.0 else 0.0))
            draw_bust(pen, who, 960, 540, 0.6, Pose(h_turn=yaw, unmask=1.0 if who == 'bunny' and yaw == 0.5 else 0.0))
        draw(pen, who, 960, 1000, 600, Pose(lie=-1.0, turn=1.0))
    draw_crayon_drawing(pen, 960, 540, 300)
    for nm in PROPS3: draw_prop3(pen, nm, 960, 540, 5.0)
    out.append('%d cast ids draw in 6 views, kneeling, seated, lying and as busts; %d props; the crayon drawing' % (len(BUNNY_CAST), len(PROPS3)))
    # reach precision
    errs = []
    for who in ('mom', 'narrator', 'june', 'bunny', 'dad'):
        a0 = Acting(who, seed=1, height=height_px(who, 380)).place(900, 1000)
        sh = a0.where(1.0, 'shoulder_l'); R = _arm_len(CAST[who]) * a0.height / 1000.0
        for q in (-0.8, 0.0, 0.7):
            tg = (sh[0] + 0.72 * R * math.cos(q), sh[1] + 0.72 * R * math.sin(q))
            a = Acting(who, seed=1, height=a0.height).place(900, 1000); a.reach_to(0.0, 1, tg, dur=0.2, lean=False)
            h = a.where(1.0, 'hand_l'); errs.append(math.hypot(h[0] - tg[0], h[1] - tg[1]))
    assert max(errs) < 8.0, ('reach_to', max(errs))
    out.append('reach_to: palm within %.1f px of 15 reachable targets (5 cast members)' % max(errs))
    # seat anchor: hips on the seat, feet on the floor
    for who, seat_m in (('mom', 0.46), ('narrator', 0.40), ('june', 0.30)):
        ppm = 380.0; fl = 1000.0; seat_y = fl - seat_m * ppm
        a = Acting(who, seed=2, height=height_px(who, ppm)).place(900, fl); a.face(0.6); a.sit_on(0.0, seat_y, dur=0.8)
        P = a.at(2.0); hy = a.where(2.0, 'hip')[1]
        assert a.foot_gap(2.0) < 0.5 and abs(hy - (seat_y - 40.0 * a.height / 1000.0)) < 0.06 * a.height, (who, hy, seat_y)
        for t in np.arange(0.0, 1.0, 0.1): assert a.foot_gap(float(t)) < 0.5, ('sit feet', who, t)
    out.append('sit_on: hips on the seat (chair / couch / low), feet on the floor all the way down')
    for k in (0, 1, 2):
        a = Acting('mom', seed=3, height=600).place(900, 1000); a.kneel_down(0.0, 1.0, knees=k)
        gaps = [a.foot_gap(float(t)) for t in np.arange(0.0, 1.4, 0.05)]
        assert max(gaps) < 0.5, ('kneel feet', k, max(gaps))
    out.append('kneel_down (one knee, both knees, on the heels): a foot or a knee on the floor every frame')
    # planted walk: the stance foot stays put
    a = Acting('mom', seed=4, height=600).place(500, 1000); a.walk(0.0, 3.0, 0.0, 600.0, facing=1.0)
    slide = 0.0; prev = None
    for t in np.arange(0.8, 2.2, 1 / 60.0):
        P = a.at(float(t)); B = Body(a.sp, P)
        sd = min((-1, 1), key=lambda s_: B.foot_lift(s_))
        fx = a.where(float(t), 'foot_l' if sd > 0 else 'foot_r')[0]
        if prev is not None and prev[0] == sd and B.foot_lift(sd) < 0.5: slide = max(slide, abs(fx - prev[1]))
        prev = (sd, fx)
    assert slide < 2.5, ('walk slide px/frame', slide)
    out.append('walk: the planted foot moves at most %.2f px per frame (no skating)' % slide)
    # props: picked up without a jump, never in two places
    a = Acting('narrator', seed=5, height=600).place(900, 1000)
    egg = PropTrack('egg', 830, 990, 600 / 168.0)
    tc = a.pick_up(egg, 0.5, side=-1, dur=1.2)
    before = egg.pos(tc - 1e-3); after = egg.pos(tc + 1e-3)
    assert math.hypot(after[0] - before[0], after[1] - before[1]) < 8.0, ('pick-up jump', before, after)
    assert egg.state(tc - 0.01)[0] == 'rest' and egg.state(tc + 0.01)[0] == 'held' and a.at(tc + 0.05).hr_prop == 'egg'
    out.append('pick_up: the egg changes from the doormat to the hand with a %.1f px jump' % math.hypot(after[0] - before[0], after[1] - before[1]))
    # look_at: the head turns toward the target side; eyes follow
    a = Acting('mom', seed=6, height=600).place(900, 1000); a.look_at(0.0, (1500, 500), dur=0.2)
    b = Acting('mom', seed=6, height=600).place(900, 1000); b.look_at(0.0, (300, 500), dur=0.2)
    pa, pb = a.at(1.0), b.at(1.0)
    assert pa.turn + pa.h_turn > 0.3 and pb.turn + pb.h_turn < -0.3 and pa.look_x > -0.05 and pb.look_x < 0.05
    out.append('look_at: yaw %+.2f / %+.2f toward targets right / left' % (pa.turn + pa.h_turn, pb.turn + pb.h_turn))
    # hand in paw while walking
    bb = Acting('bunny87', seed=6, height=height_px('bunny87', 300)).place(980, 940)
    ll = Acting('laurie87', seed=7, height=height_px('laurie87', 300)).place(880, 954)
    bb.face(-0.15); ll.face(0.15); bb.hold_hand(-1.0, -1, ll, 1)
    bb.walk(1.8, 5.0, 0.0, 520.0, facing=1.0); ll.walk(1.8, 5.0, 0.0, 520.0, facing=1.0)
    for t in np.arange(0.0, 5.0, 0.1): bb.at(float(t)); ll.at(float(t))
    assert not getattr(bb, 'misses', None) and not getattr(ll, 'misses', None), 'hand in paw'
    out.append('hold_hand: the Bunnyman and little Laurie keep hold all through the walk')
    # character lines move lips; the foam head never does
    m = Acting('mom', seed=7); m.talk([(0.2, 1.4, 'I told you not to look at the treeline')], env=None, words=None)
    mo = [m.at(float(t)).m_open for t in np.arange(0.2, 1.4, 0.02)]
    assert max(mo) > 0.25 and min(mo) < 0.1, 'mom lip sync'
    out.append('lip sync from text: mouth open %.2f..%.2f on Mom\'s line' % (min(mo), max(mo)))
    for o_ in out: print(o_)
    print('bunnyman film self-test ok')


_selftest_v2 = _selftest


def _selftest():
    """python3 characters.py --selftest: the older films' checks (their lip sync against the dummy film's recording when
    it is there, so this film's new narration cannot break them) and the Bunnyman film's checks."""
    global VOICE_WAV, VOICE_WORDS
    ref_w, ref_j = os.path.join(_REF_VOICE, 'vo_en.wav'), os.path.join(_REF_VOICE, 'asr_cache.json')
    keep = (VOICE_WAV, VOICE_WORDS)
    if os.path.exists(ref_w):
        VOICE_WAV, VOICE_WORDS = ref_w, ref_j
    try:
        _selftest_v2()
    finally:
        VOICE_WAV, VOICE_WORDS = keep
    _selftest_bunny()


from engine.core import rgb  # noqa: E402


def draw_silhouette(pen, who, x, y_feet, height, pose=None, t=None, colr='#05070d', a=0.94, rim='#9fb6ff', rim_a=0.55,
                    rim_side=1, eyes=0.0):
    """A figure as a dark silhouette against a brighter sky (the Bunnyman far off at the treeline under the moon): the
    figure flattened to colr, a thin moonlight rim on one side, and with eyes > 0 the Bunnyman's felt eye rings catching
    a little light (two pale dots)."""
    P = _as_pose(pose); t = P.t if t is None else t
    cv = pen.cv
    cv.saveLayer(None, None)
    draw(pen, who, x, y_feet, height, P, detail=0, t=t)
    cv.drawPaint(skia.Paint(Color=skia.Color4f(*[v / 255.0 for v in rgb(colr)[:3]], a), BlendMode=skia.BlendMode.kSrcATop))
    cv.restore()
    if rim_a > 0:
        cv.saveLayer(None, None)
        draw(pen, who, x + rim_side * max(1.5, height * 0.004), y_feet, height, P, detail=0, t=t)
        cv.drawPaint(skia.Paint(Color=skia.Color4f(*[v / 255.0 for v in rgb(rim)[:3]], rim_a), BlendMode=skia.BlendMode.kSrcATop))
        cv.saveLayer(None, skia.Paint(BlendMode=skia.BlendMode.kDstOut))
        draw(pen, who, x, y_feet, height, P, detail=0, t=t)
        cv.restore()
        cv.restore()
    if eyes > 0 and CAST[who].get('bunny'):
        sp = CAST[who]
        s = height / 1000.0
        B = Body(sp, P)
        hx, hy, hrot, hs = _head_xf(sp, B, P)
        for side in (-1, 1):
            ex = x + P.dx + (hx + side * sp['eye_dx'] * hs * math.cos((P.turn + P.h_turn) * PI / 2)) * s
            ey = y_feet + P.dy + (hy + 18.0 + sp['eye_y'] * hs) * s
            pen.glow(ex, ey, max(2.0, sp['eye_r'] * hs * s * 1.6), '#c9d2e6', 140 * eyes)
            pen.fill(oval(ex, ey, max(0.8, sp['eye_r'] * hs * s * 0.6)), '#05070d', 255 * eyes)
