"""characters_ice.py: the cast of "If The Ice Cream Truck Plays Its Song In Winter... DON'T GO OUTSIDE" and its staging.

Not imported on its own: characters.py runs it in its own namespace at the end of the module (exec, after
characters_bus.py), so everything here is part of `characters` (import characters as CH). Mister Shiver reuses the bus
film's 3D cm rig (_ws_rig: spine, arms with world-target IK, knitted gloves through _ws_glove) with his own egg head,
striped uniform, transformation and eight spider legs. See ICE_API below and CAST.md.
"""
# NOTE: runs inside characters.py's globals (math, np, skia, Ctx, CAST, Pose, Acting, _ws_rig, _WSView ... are defined).

ICE_API = """
Ice cream film cast ids:
  'shiver'      MISTER SHIVER (original): 6 ft 4, narrow, slightly hunched, long neck, a bald chalk-white egg head a little
                too big, tiny bright blue eyes in shadowed sockets, no eyebrows, frost flecks on the brow, a too-wide smile with
                two big buck teeth, a pink-and-white VERTICALLY striped vendor jacket buttoned to the throat, round white
                collar, pink bow tie with a silver snowflake pin, snowflake SHIVER badge, white knitted wool gloves. No breath.
                Pose sh_m 0..1 = the transformation (see SH_STEPS); sh_legs 0..8 legs out; sh_lift (cm) body raised on legs.
  'shiver_mom'  his copy of Mom at the door glass (hospital coat and scarf; no breath).
  'adam', 'adam_sock' (one boot, one sock), 'lina', 'lina_mitt' (mittens on), 'dad', 'kessler', 'kessler_out'
  (undershirt + slippers), 'kessler_wrap' (in the blanket), 'kessler_am' (scarf, morning), 'walter58', 'benny',
  'medic_a', 'medic_b', 'mom_photo'.
Shiver acting: transform(t0, times=None) / shrink_back(t0, dur), glimpse(t0, dur), slow_wave(t0, t1, side),
  lean_down(t0, target), leg_to(t0, i, target, dur, hold), legs_plant(t0, targets), scuttle(t0, t1, path, ground),
  drop_to(t0, dur, y_from_px), cage(t0, center_px, width_px), pour_out(t0, dur, sill_px), hang_hatch(t0, ...),
  jaw_gape(t0, t1). Points: where(t, 'eyes'|'mouth'|'chin'|'crown'|'leg0'..'leg7'|'hand_l'...).
"""

# ====================================================================================================== MISTER SHIVER
_SH_M = 1.93
_SH_PAL = dict(
    skin='#E9E4DC', skin_sh='#B9C3CF', skin_dk='#8593a6', skin_hi='#fbf9f5', eye='#4FB3FF', eye_dk='#1f6fb8', teeth='#F3EEDC',
    teeth_sh='#c9c0a6', lip='#D9C6C6', lip_dk='#a88f93', mouth='#3a1620', mouth_m='#120A10', socket='#6f7f96',
    pink='#E58FB4', pink_sh='#b0607f', pink_hi='#f4b4cf', white='#F7F2F4', white_sh='#c9bec8', bow='#e0709e', bow_sh='#a84a72',
    pin='#C9D6E3', badge='#eef3f8', badge_rim='#7f93a8', bone='#EFE9DD', bone_sh='#aeb3b8', crack='#9FB4C8', crack_dk='#5d7690',
    red='#FF2A2A', icicle='#DDEFFF', icicle_rim='#9fd0ff', leg='#6B4A32', leg_dk='#3E2A1C', leg_hi='#8f6a4a', rime='#DCE8F2',
    tip='#e3e9ee', line='#1a1418', frost='#e8f4ff')
# the reused whistle-rig pieces (sleeves, gloves, trousers) read these keys
_SH_WSPAL = dict(_WS_PAL, jacket=_SH_PAL['pink'], jacket_sh=_SH_PAL['pink_sh'], jacket_hi=_SH_PAL['pink_hi'],
                 trim=_SH_PAL['white'], fur='#e9e9e6', fur_dk='#b6b9c0', fur_hi='#ffffff', glove='#EDEDED', glove_sh='#b3b8c2',
                 glove_dirt='#b3b8c2', grime=0.0, trousers='#efe9ec', trousers_sh='#bfb3bc', shoe='#3b3337', line='#1a1418')
_SH_WSPAL['glove_sh'] = '#cdd2da'

POSE_DEFAULTS.update(
    sh_m=0.0,        # the transformation 0..1 (drives the stages below through SH_STAGES)
    sh_smile=0.0,    # the smile stretches past the cheeks
    sh_long=0.0,     # the face pulls long, white, hard (bone mask, frost cracks)
    sh_sink=0.0,     # the blue eyes sink into the dark
    sh_red=0.0,      # the red eyes ignite
    sh_jaw=0.0,      # the jaw drops to the chest
    sh_gape=0.0,     # extra jaw strain (the hung last note)
    sh_split=0.0,    # the uniform bulges and splits
    sh_legs=0.0,     # number of spider legs out (continuous 0..8, one after another)
    sh_lift=0.0,     # cm: the body raised on its legs (the human feet hang)
    sh_spread=1.0,   # default leg stance width
    sh_neck=7.0,     # cm of extra neck (his long neck)
    sh_glim=0.0,     # glimpse: the long white face with red eyes for a flicker (head only)
    sh_wave=0.0,     # wave phase helper (set by slow_wave)
    sh_legcap=8.0,   # at most this many legs drawn (pour_out: the legs come last)
    sh_nolegs=0.0,   # 1: his human legs not drawn (inside the truck below the window, during the pour)
)
for _i in range(8):
    POSE_DEFAULTS.update({'sh_t%dw' % _i: 0.0, 'sh_t%dx' % _i: 0.0, 'sh_t%dy' % _i: 0.0, 'sh_t%dz' % _i: 0.0,
                          'sh_t%dlift' % _i: 0.0})

# transformation stages: name -> (m start, m end). SH_STEPS: the 8 bible steps as sh_m values (the TRANSFORMATION strip)
SH_STAGES = dict(smile=(0.02, 0.20), long=(0.18, 0.38), sink=(0.38, 0.47), red=(0.50, 0.56), jaw=(0.56, 0.70),
                 split=(0.68, 0.78), legs=(0.76, 1.0))
SH_STEPS = (0.0, 0.20, 0.38, 0.48, 0.56, 0.70, 0.84, 1.0)
SH_STEP_NAMES = ('waving', 'the smile keeps going', 'skin pulls long, bone', 'eyes sink into the dark', '...come back red',
                 'the jaw drops to the chest', 'uniform splits, legs punch out', 'legs planted: full monster')


def _sh_state(P):
    """Effective stage values (each 0..1; legs 0..8) from sh_m and the direct overrides."""
    m = float(P.sh_m)
    st = {k: ease_in_out(prog(m, a, b)) for k, (a, b) in SH_STAGES.items()}
    out = dict(smile=max(st['smile'], P.sh_smile), long=max(st['long'], P.sh_long), sink=max(st['sink'], P.sh_sink),
               red=max(st['red'], P.sh_red), jaw=max(st['jaw'], P.sh_jaw), split=max(st['split'], P.sh_split),
               legs=min(max(prog(m, *SH_STAGES['legs']) * 8.0, P.sh_legs), P.sh_legcap))
    g = clamp(P.sh_glim)
    if g > 0:
        out['smile'] = max(out['smile'], g); out['long'] = max(out['long'], g); out['red'] = max(out['red'], g)
        out['sink'] = max(out['sink'], g)
    out['jaw'] = clamp(out['jaw'] + 0.12 * P.sh_gape)
    return out


# ---------------------------------------------------------------------------------------------------- the head
_SH_HR = (13.0, 17.8, 14.2)       # cm: half width, crown up, depth (an egg: the dome taller than the jaw)
_SH_CHIN = 14.2
_SH_HS = 1.2                      # the head a little too big for the neck


def _sh_mouth(W, L, sm):
    """Lip latitudes for the smile: upper(lon), lower(lon) and the corner latitude."""
    def up(lon):
        q = np.clip(np.abs(np.asarray(lon, float)) / W, 0, 1)
        return -0.37 + (0.19 + 0.16 * sm) * q ** 2 - 0.05 * L

    def lo(lon):
        q = np.clip(np.abs(np.asarray(lon, float)) / W, 0, 1)
        return up(lon) - (0.25 + 0.10 * sm) * (1.0 - q ** 2) ** 0.75
    return up, lo


def _sh_head_local(lon, lat, grow=0.0, L=0.0):
    lon = np.asarray(lon, float); lat = np.asarray(lat, float)
    cl, sl = np.cos(lat), np.sin(lat)
    dn = np.clip(-sl, 0.0, 1.0)
    rx = (_SH_HR[0] + grow) * (1.0 - 0.15 * dn - 0.16 * L * dn) * (1.0 - 0.03 * L)
    ry = np.where(lat > 0, _SH_HR[1] * (1.0 + 0.05 * L), _SH_CHIN * (1.0 + 1.25 * L)) + grow
    rz = (_SH_HR[2] + grow) * (1.0 - 0.06 * L * dn)
    x = rx * cl * np.sin(lon)
    y = -ry * sl
    z = rz * cl * np.cos(lon)
    fr = np.clip(np.cos(lon), 0.0, None)
    z = z + fr * (3.8 * (1.0 - 0.85 * L) * np.exp(-(lon / 0.10) ** 2 - ((lat + 0.08) / 0.13) ** 2)          # the nose
                  + 1.2 * np.exp(-(lon / 0.35) ** 2 - ((lat + 0.95) / 0.20) ** 2)                               # chin
                  + (1.1 + 0.8 * L) * np.exp(-((np.abs(lon) - 0.52) / 0.24) ** 2 - ((lat + 0.06) / 0.13) ** 2)  # cheekbones
                  + (0.9 + 0.6 * L) * np.exp(-((lat - 0.31) / 0.10) ** 2) * np.exp(-(lon / 0.6) ** 2)        # brow ridge
                  - (1.3 + 2.2 * L) * np.exp(-((np.abs(lon) - 0.27) / 0.13) ** 2 - ((lat - 0.13) / 0.11) ** 2)  # sockets
                  - (0.9 + 1.4 * L) * np.exp(-((np.abs(lon) - 0.66) / 0.20) ** 2 - ((lat + 0.36) / 0.17) ** 2))  # hollows
    x = x - np.sign(lon) * (0.9 + 0.6 * L) * np.exp(-((np.abs(lon) - 1.25) / 0.30) ** 2 - ((lat - 0.22) / 0.22) ** 2)  # temples
    return np.stack([x, y, z], -1) * _SH_HS


_SH_CROWN = float(-_sh_head_local(0.0, PI / 2)[1])


class _SHHead:
    """His head in the body frame, projected. The jaw (below the lower lip and its line back toward the ears) drops."""

    def __init__(self, R, view, P, st):
        self.R, self.view, self.P, self.st = R, view, P, st
        self.M = R['hrot']; self.C = R['head']
        self.L = st['long']; self.J = st['jaw']; self.sm = st['smile']
        self.W = 0.98 + 0.95 * self.sm + 0.10 * self.L
        self.up, self.lo = _sh_mouth(self.W, self.L, self.sm)

    def jaw_w(self, lon, lat):
        lon = np.asarray(lon, float); lat = np.asarray(lat, float)
        a = np.abs(lon)
        cut = np.where(a <= self.W, self.lo(np.minimum(a, self.W)), self.lo(self.W) - (a - self.W) * 0.55)
        w = (lat <= cut + 1e-6).astype(float) * np.clip((2.25 - a) / 0.35, 0.0, 1.0)
        return w

    def local(self, lon, lat, grow=0.0, jaw=None):
        L_ = _sh_head_local(lon, lat, grow, self.L).reshape(-1, 3)
        if self.J > 1e-3:
            w = self.jaw_w(np.ravel(lon), np.ravel(lat)) if jaw is None else np.full(L_.shape[0], float(jaw))
            drop = self.J * (24.0 + 6.0 * self.L)
            L_ = L_ + np.stack([np.zeros_like(w), w * drop, w * (3.0 * self.J)], -1)
        return L_

    def body(self, L):
        return self.C + (self.M @ np.asarray(L, float).reshape(-1, 3).T).T

    def normal(self, L):
        n = L / np.array([_SH_HR[0] ** 2, (_SH_HR[1] * 0.9) ** 2, _SH_HR[2] ** 2])
        n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
        return (self.M @ n.T).T

    def proj(self, lon, lat, grow=0.0, jaw=None):
        L_ = self.local(lon, lat, grow, jaw)
        X, Y, zd, f = self.view.pa(self.body(L_))
        return X, Y, self.view.face(self.normal(_sh_head_local(lon, lat, 0.0, self.L).reshape(-1, 3))), zd

    def p3(self, lon, lat, grow=0.0, jaw=None):
        return self.body(self.local(np.atleast_1d(lon), np.atleast_1d(lat), grow, jaw))[0]

    def sils(self):
        lo, la = np.meshgrid(np.linspace(-PI, PI, 49), np.linspace(-1.56, 1.56, 25))
        lo, la = lo.ravel(), la.ravel()
        X, Y, _, _ = self.proj(lo, la)
        P2 = np.stack([X, Y], -1)
        if self.J < 0.02:
            return [poly(_hull(P2), True)]
        w = self.jaw_w(lo, la)
        out = []
        for m in (w < 0.5, w >= 0.5):
            if m.sum() > 3: out.append(poly(_hull(P2[m]), True))
        return out

    def region(self, lon0, lon1, lat_lo, lat_hi, nlon=16, nlat=6, grow=0.05, thr=0.0, jaw=None):
        lons = np.linspace(lon0, lon1, nlon + 1)
        lo = np.asarray(lat_lo(lons) if callable(lat_lo) else np.full_like(lons, lat_lo), float)
        hi = np.asarray(lat_hi(lons) if callable(lat_hi) else np.full_like(lons, lat_hi), float)
        g = np.linspace(0, 1, nlat + 1)
        LA = lo[:, None] + (hi - lo)[:, None] * g[None, :]
        LO = np.repeat(lons[:, None], nlat + 1, 1)
        X, Y, F, _ = self.proj(LO.ravel(), LA.ravel(), grow, jaw)
        X = X.reshape(LO.shape); Y = Y.reshape(LO.shape); F = F.reshape(LO.shape)
        p = skia.Path(); any_ = False
        for i in range(nlon):
            for j in range(nlat):
                if F[i, j] + F[i + 1, j] + F[i, j + 1] + F[i + 1, j + 1] <= thr * 4: continue
                q = [(X[i, j], Y[i, j]), (X[i + 1, j], Y[i + 1, j]), (X[i + 1, j + 1], Y[i + 1, j + 1]), (X[i, j + 1], Y[i, j + 1])]
                ar = sum(q[k][0] * q[(k + 1) % 4][1] - q[(k + 1) % 4][0] * q[k][1] for k in range(4))
                if ar < 0: q = q[::-1]
                p.addPoly([skia.Point(*v) for v in q], True); any_ = True
        return p if any_ else None

    def curve(self, lons, lats, grow=0.12, thr=0.02, jaw=None):
        X, Y, F, _ = self.proj(np.asarray(lons, float), np.asarray(lats, float), grow, jaw)
        runs, cur = [], []
        for x, y, fv in zip(X, Y, F):
            if fv > thr: cur.append((float(x), float(y)))
            else:
                if len(cur) > 1: runs.append(cur)
                cur = []
        if len(cur) > 1: runs.append(cur)
        return runs

    def disc(self, lon, lat, rl, rt, n=16, grow=0.15):
        a = np.linspace(0, 2 * PI, n, endpoint=False)
        X, Y, F, _ = self.proj(lon + rl * np.cos(a) / max(math.cos(lat), 0.3), lat + rt * np.sin(a), grow)
        return smooth(list(zip(X.tolist(), Y.tolist())), True, 0.9), float(np.mean(F))

    def facing(self, lon, lat):
        return float(self.proj(np.atleast_1d(lon), np.atleast_1d(lat))[2][0])


def _sh_cracks():
    """Frost-crack polylines in (lon, lat) on the mask: branching like ice on a pond (fixed, seeded)."""
    out = []
    seeds = ((0.0, 0.62), (0.42, 0.45), (-0.45, 0.50), (0.62, 0.05), (-0.66, -0.02), (0.30, -0.55), (-0.28, -0.70),
             (0.85, 0.40), (-0.88, 0.32), (0.0, 0.95), (0.55, -0.95), (-0.50, -1.05))
    for k, (lo, la) in enumerate(seeds):
        for br in range(2 + (k % 2)):
            pts = [(lo, la)]
            ang = hash01(k * 7 + br, 3101) * 2 * PI
            cur = (lo, la)
            for st in range(5 + int(hash01(k + br, 3102) * 4)):
                ang += (hash01(k * 31 + br * 7 + st, 3103) - 0.5) * 1.3
                ln = 0.05 + 0.05 * hash01(k * 13 + st, 3104)
                cur = (cur[0] + ln * math.cos(ang), cur[1] + ln * math.sin(ang) * 0.9)
                pts.append(cur)
            out.append(pts)
    return out


_SH_CRACKS = _sh_cracks()


def _sh_tooth(c, view, hd, root, d_down, tang, wid, ln, colr, rim, lw, icy, a=255):
    """One tooth from a 3D root: d_down = unit growth direction (3D), tang = unit along the lip. icy: long tapered."""
    tip = root + d_down * ln
    if icy > 0.5:
        pts3 = [root - tang * wid * 0.5, root - tang * wid * 0.25 + d_down * ln * 0.55, tip,
                root + tang * wid * 0.25 + d_down * ln * 0.55, root + tang * wid * 0.5]
    else:
        pts3 = [root - tang * wid * 0.48, root - tang * wid * 0.50 + d_down * ln * 0.8, root - tang * wid * 0.25 + d_down * ln,
                root + tang * wid * 0.25 + d_down * ln, root + tang * wid * 0.50 + d_down * ln * 0.8, root + tang * wid * 0.48]
    pp = [view.p2(q) for q in pts3]
    path = poly(pp, True)
    c.fill(path, colr, a)
    if icy > 0.5:
        X0, Y0 = view.p2(root); X1, Y1 = view.p2(tip)
        c.line(poly([(X0 * 0.7 + X1 * 0.3, Y0 * 0.7 + Y1 * 0.3), (X0 * 0.15 + X1 * 0.85, Y0 * 0.15 + Y1 * 0.85)], False),
               lw * 0.9, '#ffffff', int(180 * a / 255))
        c.line(path, lw * 0.8, rim, int(230 * a / 255))
    else:
        c.line(path, lw * 0.8, _SH_PAL['line'], int(220 * a / 255))
    return path


def _sh_head_draw(c, R, view, P, det, t, light, st):
    pal = _SH_PAL
    hd = _SHHead(R, view, P, st)
    lw = c.lw
    L, J, sm = st['long'], st['jaw'], st['smile']
    skin = mix(pal['skin'], pal['bone'], L); skin_sh = mix(pal['skin_sh'], pal['bone_sh'], L)
    # ears (small, flat, human), behind first
    ears = []
    for s in (-1, 1):
        Ec = hd.body(_sh_head_local(s * 1.50, -0.02, 0.4, L)[None, :])[0]
        M = R['hrot']
        out_ = M @ np.array([s * 1.0, 0.0, 0.0]); upv = M @ np.array([0.0, -1.0, 0.0]); bk = M @ np.array([0.0, 0.0, -1.0])
        bk = _u3(bk * 0.75 + out_ * 0.65)
        ring = [Ec + upv * (3.7 * math.cos(a_) - 0.5) * (1.0 if math.cos(a_) > 0 else 0.8) + bk * (2.3 * math.sin(a_) + 0.6) + out_ * 0.4
                for a_ in np.linspace(0, 2 * PI, 12, endpoint=False)]
        pts = [view.p2(q) for q in ring]
        ears.append((view.depth(out_), s, smooth(pts, True, 0.8), pts))
    for dz, s, ep, pts in ears:
        if dz < 0.45:
            c.line(ep, lw * 2.2, pal['line']); c.fill(ep, skin); c.fill(_crescent(ep, -s * 0.8, 0.3), skin_sh, 170)
    sils = hd.sils()
    # mouth hole (behind the skin when the jaw drops: the dark between skull and jaw)
    W = hd.W
    lons = np.linspace(-W, W, 31)
    up_lat, lo_lat = hd.up(lons), hd.lo(lons)
    Xu, Yu, Fu, _ = hd.proj(lons, up_lat, 0.1, jaw=0.0)
    Xl, Yl, Fl, _ = hd.proj(lons, lo_lat, 0.1, jaw=1.0)
    mouth_pts = list(zip(Xu.tolist(), Yu.tolist())) + list(zip(Xl[::-1].tolist(), Yl[::-1].tolist()))
    mouth = smooth(mouth_pts, True, 0.5)
    for sp_ in sils:
        c.line(sp_, lw * 2.2, pal['line'])
    if J > 0.02:
        c.fill(mouth, pal['mouth_m'])      # under the skin silhouettes: shows in the gap between skull and jaw
    for sp_ in sils:
        c.fill(sp_, skin)
    sil_all = sils[0]
    for sp_ in sils[1:]: sil_all = union(sil_all, sp_)
    Xc, Yc = view.p2(hd.C)
    Xt, Yt = view.p2(hd.p3(0.0, 1.4))
    r_ = math.hypot(Xt - Xc, Yt - Yc)
    _, _, _, fh = view.p(hd.C)
    cm = r_ / (_SH_HR[1] * _SH_HS * 0.98)          # px per cm at the head

    def P2(lo_, la_, g=0.0, jaw=None):
        X_, Y_, F_, _ = hd.proj(np.array([lo_]), np.array([la_]), g, jaw)
        return float(X_[0]), float(Y_[0]), float(F_[0])
    sink, red = st['sink'], st['red']
    with c.clip(sil_all):
        # cold modelling: lit from the upper left; blue-grey turning away; a cold shadow under the dome and the jaw
        c.grad(sil_all, Xc - r_ * 0.9, Yc - r_ * 0.5, Xc + r_ * 0.9, Yc + r_ * 0.6,
               [(0, pal['skin_hi'], 120), (0.42, skin, 0), (1.0, skin_sh, 240)])
        c.radial(sil_all, Xc - r_ * 0.12, Yc - r_ * 0.25 + r_ * 0.35 * L, r_ * (1.25 + 0.45 * L),
                 [(0, skin, 0), (0.62, skin, 0), (0.86, skin_sh, 150 - 50 * L), (1.0, pal['skin_dk'], 230 - 60 * L)], sy=1.15 + 0.4 * L)
        c.glow(Xc - r_ * 0.32, Yc - r_ * 0.62, r_ * 0.42, r_ * 0.30, '#ffffff', 110)
        # cheek hollows under the cheekbones, temples, the brow shadow over the sockets
        for s in (-1, 1):
            x_, y_, f_ = P2(s * 0.70, -0.42 - 0.05 * L)
            if f_ > -0.2: c.glow(x_, y_, 4.2 * cm, 6.0 * cm * (1 + 0.5 * L), pal['skin_dk'], 70 + int(90 * L))
            x_, y_, f_ = P2(s * 1.15, 0.25)
            if f_ > -0.2: c.glow(x_, y_, 3.5 * cm, 5.0 * cm, pal['skin_dk'], 70)
            x_, y_, f_ = P2(s * 0.52, -0.08)
            if f_ > 0: c.glow(x_, y_ - 1.0 * cm, 3.0 * cm, 1.6 * cm, '#ffffff', 90)          # cheekbone highlight
            # the socket: a heavy dark hollow, darkest under the brow (the owner's reference)
            x_, y_, f_ = P2(s * 0.27, 0.14)
            if f_ > -0.1:
                c.glow(x_, y_ - 0.4 * cm, 4.6 * cm * (1 + 0.25 * L), 3.4 * cm * (1 + 0.4 * L), '#3c4a63', 150 + int(100 * max(L, sink)))
                c.glow(x_, y_ - 0.2 * cm, 2.6 * cm * (1 + 0.3 * L), 2.0 * cm * (1 + 0.5 * L), '#1a2133', 140 + int(115 * max(L, sink)))
        x_, y_, f_ = P2(0.0, 0.30)
        if f_ > 0: c.glow(x_, y_ - 1.5 * cm, 7.5 * cm, 1.8 * cm, '#ffffff', 70)                  # brow ridge catches the light
        if det >= 1:
            c.texture(sil_all, 'skin', 0.04, 0.5)
        # faint blue veins at the temples (cold)
        if det >= 1 and L < 0.6:
            for s in (-1, 1):
                for run in hd.curve(s * np.linspace(0.92, 1.25, 7), 0.30 + 0.06 * np.sin(np.linspace(0, 5, 7))):
                    c.line(smooth(run, False), lw * 0.45, '#7f9bc4', int(110 * (1 - L)))
        # forehead creases (age, not a doll)
        if det >= 1:
            for la_ in (0.52, 0.62):
                for run in hd.curve(np.linspace(-0.40, 0.40, 11), la_ + 0.025 * np.cos(np.linspace(-1.5, 1.5, 11))):
                    c.line(smooth(run, False), lw * 0.45, pal['skin_dk'], int(120 * (1 - L)))
    # sockets turning to bone holes as the mask forms; lower lid bags
    for s in (-1, 1):
        lon_e = s * 0.27
        if L > 0.05 or sink > 0.05:
            so2, fso = hd.disc(lon_e, 0.13, 0.12 + 0.06 * L, 0.07 + 0.06 * L, grow=0.12)
            if fso > -0.1:
                c.fill(so2, '#050407', int(255 * clamp(max(sink, 0.8 * L))))
                c.line(so2, lw * 0.9, pal['line'], int(220 * L))
        if det >= 1 and L < 0.9:
            for run in hd.curve(lon_e + s * np.linspace(-0.12, 0.11, 7), 0.045 - 0.02 * np.sin(np.linspace(0, PI, 7))):
                c.line(smooth(run, False), lw * 0.6, pal['skin_dk'], int(190 * (1 - L)))
            for run in hd.curve(lon_e + s * np.linspace(-0.09, 0.09, 6), 0.205 + 0.015 * np.sin(np.linspace(0, PI, 6))):
                c.line(smooth(run, False), lw * 0.7, '#2a3346', int(200 * (1 - L)))      # the upper lid crease (no brows)
    # the nose: narrow and sharp, pale; it fades into a dark nasal cavity as the mask forms
    fn_ = hd.facing(0.0, -0.05)
    if fn_ > 0:
        if L < 0.7:
            a_ = int(255 * (1 - L / 0.7))
            sd = 1 if view.depth(R['hrot'] @ np.array([1.0, 0.0, 0.0])) < 0 else -1      # the side turned away gets the shadow
            for run in hd.curve(np.array([sd * 0.05, sd * 0.065, sd * 0.08, sd * 0.10]), np.array([0.10, 0.0, -0.08, -0.15]), 1.0):
                c.line(smooth(run, False), lw * 0.8, pal['skin_dk'], a_)
            for s in (-1, 1):
                x_, y_, f_ = P2(s * 0.055, -0.175, 0.6)
                if f_ > 0: c.fill(oval(x_, y_, 0.75 * cm, 0.42 * cm), '#3a3440', int(a_ * 0.85))
                for run in hd.curve(s * np.array([0.05, 0.10, 0.11, 0.085]), np.array([-0.12, -0.14, -0.18, -0.20]), 0.8):
                    c.line(smooth(run, False), lw * 0.7, pal['skin_dk'], a_)
            x_, y_, f_ = P2(0.0, -0.10, 2.0)
            if f_ > 0: c.fill(oval(x_ - 0.3 * cm, y_ - 0.4 * cm, 0.7 * cm, 0.5 * cm), '#ffffff', int(a_ * 0.7))
        if L > 0.3:
            k = prog(L, 0.3, 1.0)
            for s in (-1, 1):
                pts = [hd.proj(np.array([lo_]), np.array([la_]), 0.3)[:2] for lo_, la_ in
                       ((s * 0.015, -0.02), (s * 0.12, -0.15), (s * 0.06, -0.22), (s * 0.01, -0.20))]
                pp = smooth([(float(x[0]), float(y[0])) for x, y in pts], True, 0.5)
                c.fill(pp, '#0b0910', int(235 * k))
    # smile creases: cheeks pushed up by the too-wide smile
    if det >= 1:
        for s in (-1, 1):
            lc = s * (W + 0.05)
            for run in hd.curve(np.array([s * 0.14, s * 0.30, s * (0.45 + 0.45 * W), lc]),
                                np.array([-0.10, -0.20, -0.30, float(hd.up(W)) + 0.02]), 0.3):
                c.line(smooth(run, False), lw * 0.9, pal['skin_dk'], int(200 * (1 - 0.6 * L)))
            for run in hd.curve(np.array([lc + s * 0.05, lc + s * 0.10, lc + s * 0.06]),
                                np.array([float(hd.up(W)) + 0.08, float(hd.up(W)), float(hd.up(W)) - 0.07]), 0.3):
                c.line(smooth(run, False), lw * 0.8, pal['skin_dk'], int(180 * (1 - 0.5 * L)))
    # the mouth: interior, teeth (buck teeth -> icicles), pale lips
    vis = float(np.mean(np.concatenate([Fu, Fl])))
    if vis > -0.2:
        icy = max(prog(J, 0.05, 0.5), prog(L, 0.5, 1.0) * 0.6)
        c.fill(mouth, mix(pal['mouth'], pal['mouth_m'], max(L, J)))
        with c.clip(mouth):
            M = R['hrot']
            dn = M @ _u3(np.array([0.0, 1.0, 0.12])); upd = M @ _u3(np.array([0.0, -1.0, 0.12]))
            if J > 0.25:   # no throat: the dark deepens into the middle
                Xm, Ym = view.p2((hd.p3(0.0, float(hd.up(0.0)), 0.0, 0.0) + hd.p3(0.0, float(hd.lo(0.0)), 0.0, 1.0)) / 2)
                c.glow(Xm, Ym, 14.0 * cm * J, 18.0 * cm * J, '#000000', 230)
            elif icy < 0.5:   # the gum line behind the teeth
                for run in hd.curve(lons * 0.9, hd.up(lons * 0.9) - 0.03, 0.0, -1.0):
                    c.line(smooth(run, False), lw * 2.0, '#6e2a3a', 200)
            # upper teeth
            n_up = 12 if icy < 0.5 else 15
            for i in range(n_up):
                u = (i + 0.5) / n_up * 2 - 1
                lon_ = u * W * (0.86 if icy < 0.5 else 0.95)
                if icy < 0.5 and abs(lon_) < 0.16: continue           # the buck teeth go in last
                root = hd.p3(lon_, float(hd.up(lon_)) + 0.02, 0.0, jaw=0.0)
                tg = _u3(hd.p3(lon_ + 0.02, float(hd.up(lon_ + 0.02)), 0.0, 0.0) - hd.p3(lon_ - 0.02, float(hd.up(lon_ - 0.02)), 0.0, 0.0))
                if hd.facing(lon_, float(hd.up(lon_))) < -0.05: continue
                dl_ = W * (0.86 if icy < 0.5 else 0.95) / n_up
                spc = float(np.linalg.norm(hd.p3(lon_ + dl_, float(hd.up(lon_ + dl_)), 0.0, 0.0) - hd.p3(lon_ - dl_, float(hd.up(lon_ - dl_)), 0.0, 0.0)))
                if icy < 0.5:
                    wid = spc * 0.86; ln = 2.1 * (1 - 0.45 * abs(u))
                else:
                    wid = 2.0 + 0.8 * hash01(i, 3201); ln = (6.0 + 9.0 * hash01(i, 3202)) * (1 - 0.35 * abs(u)) * (0.5 + 0.9 * J)
                _sh_tooth(c, view, hd, root, dn, tg, wid, ln, pal['icicle'] if icy >= 0.5 else pal['teeth'], pal['icicle_rim'], lw, icy)
            # lower teeth (gap-toothed in the vendor grin)
            n_lo = 8 if icy < 0.5 else 13
            for i in range(n_lo):
                u = (i + 0.5) / n_lo * 2 - 1
                if icy < 0.5 and (hash01(i, 3203) < 0.4 or abs(u) < 0.2): continue
                lon_ = u * W * 0.8
                if hd.facing(lon_, float(hd.lo(lon_))) < -0.05: continue
                root = hd.p3(lon_, float(hd.lo(lon_)) - 0.015, 0.0, jaw=1.0)
                tg = _u3(hd.p3(lon_ + 0.02, float(hd.lo(lon_ + 0.02)), 0.0, 1.0) - hd.p3(lon_ - 0.02, float(hd.lo(lon_ - 0.02)), 0.0, 1.0))
                if icy < 0.5:
                    dl_ = W * 0.8 / n_lo
                    wid = 0.9 * float(np.linalg.norm(hd.p3(lon_ + dl_, float(hd.lo(lon_ + dl_)), 0.0, 1.0) - hd.p3(lon_ - dl_, float(hd.lo(lon_ - dl_)), 0.0, 1.0)))
                    ln = 1.3 * (1 - 0.4 * abs(u))
                else:
                    wid = 1.8 + 0.6 * hash01(i, 3204); ln = (4.0 + 7.0 * hash01(i, 3205)) * (0.5 + 0.8 * J)
                _sh_tooth(c, view, hd, root, upd, tg, wid, ln, pal['icicle'] if icy >= 0.5 else pal['teeth'], pal['icicle_rim'], lw, icy)
        # the two big buck teeth with a gap between them, resting over the lower lip (fade as the mouth turns to icicles)
        if icy < 0.9:
            a_ = int(255 * (1 - icy / 0.9))
            for s in (-1, 1):
                lon_ = s * 0.085
                root = hd.p3(lon_, float(hd.up(lon_)) + 0.02, 0.0, jaw=0.0)
                tipy = hd.p3(lon_, float(hd.lo(lon_)) - 0.035, 0.0, jaw=1.0)
                tg = _u3(hd.p3(lon_ + 0.02, float(hd.up(lon_)), 0.0, 0.0) - hd.p3(lon_ - 0.02, float(hd.up(lon_)), 0.0, 0.0))
                ln_ = min(float(np.linalg.norm(tipy - root)), 6.5)
                _sh_tooth(c, view, hd, root + tg * s * 0.5, _u3(tipy - root), tg, 3.6, ln_, pal['teeth'], pal['icicle_rim'], lw, 0.0, a_)
        # lips: pale, thin; the upper lip over the teeth roots, the lower under them
        if L < 0.85:
            a_ = int(255 * (1 - L / 0.85))
            up_run = [(float(x), float(y)) for x, y, f in zip(Xu, Yu, Fu) if f > -0.05]
            lo_run = [(float(x), float(y)) for x, y, f in zip(Xl, Yl, Fl) if f > -0.05]
            if len(up_run) > 1: c.line(smooth(up_run, False), lw * 1.3, pal['lip'], a_)
            if len(lo_run) > 1: c.line(smooth(lo_run, False), lw * 1.8, pal['lip'], a_)
        c.line(mouth, lw * 1.1, pal['line'])
    # frost: flecks on the brow (normal), frost cracks across the mask (monster)
    if det >= 1:
        for i in range(34):
            lo_ = (hash01(i, 3301) - 0.5) * 1.3; la_ = 0.30 + hash01(i, 3302) * 0.50
            X_, Y_, F_, _ = hd.proj(np.array([lo_]), np.array([la_]), 0.3)
            if F_[0] < 0.15: continue
            r0 = (0.12 + 0.22 * hash01(i, 3303)) * cm
            x0, y0 = float(X_[0]), float(Y_[0])
            c.fill(oval(x0, y0, r0, r0), pal['frost'], 200)
            if hash01(i, 3304) > 0.75:
                for k in range(3):
                    a_ = k * PI / 3
                    c.line(poly([(x0 - math.cos(a_) * r0 * 2.2, y0 - math.sin(a_) * r0 * 2.2),
                                 (x0 + math.cos(a_) * r0 * 2.2, y0 + math.sin(a_) * r0 * 2.2)], False), lw * 0.25, '#ffffff', 170)
    if L > 0.15:
      ka = prog(L, 0.15, 0.9)
      with c.clip(mouth, diff=True):
        for k, pts in enumerate(_SH_CRACKS):
            n_ = max(2, int(len(pts) * ka + 0.5))
            lo_ = [p_[0] for p_ in pts[:n_]]; la_ = [p_[1] * (0.85 + 0.0) for p_ in pts[:n_]]
            for run in hd.curve(lo_, la_, 0.25):
                c.line(poly(run, False), lw * 0.75, pal['crack_dk'], int(230 * ka))
                c.line(poly(run, False), lw * 0.3, '#dbe8f5', int(200 * ka))
    # eyes: tiny bright blue with a pinpoint highlight; they sink, a beat of black, then red
    for s in (-1, 1):
        lon_e = s * 0.25
        X_, Y_, F_, zd_ = hd.proj(np.array([lon_e]), np.array([0.13]), -0.5 - 2.0 * sink)
        if F_[0] < 0.05: continue
        x0, y0 = float(X_[0]), float(Y_[0])
        _, _, _, f_ = view.p(hd.p3(lon_e, 0.13))
        rr = 0.88 * f_
        kb = 1.0 - prog(sink, 0.0, 0.9)
        if kb > 0.02 and red < 0.5:
            c.fill(oval(x0, y0, rr * (0.55 + 0.45 * kb) * 1.15, rr * (0.55 + 0.45 * kb)), '#0d1b2a', int(255 * kb))
            c.fill(oval(x0, y0, rr * 0.8 * kb, rr * 0.75 * kb), pal['eye'], int(255 * kb))
            c.fill(oval(x0 + 0.1 * rr, y0 + 0.1 * rr, rr * 0.38 * kb, rr * 0.38 * kb), pal['eye_dk'], int(255 * kb))
            c.fill(oval(x0 - 0.25 * rr, y0 - 0.25 * rr, rr * 0.16, rr * 0.16), '#ffffff', int(255 * kb))
        if red > 0.02:
            g = red
            c.glow(x0, y0, rr * 5.0, rr * 4.0, pal['red'], int(120 * g))
            c.fill(oval(x0, y0, rr * 0.95, rr * 0.85), '#5a0000', int(255 * g))
            c.fill(oval(x0, y0, rr * 0.75, rr * 0.65), pal['red'], int(255 * g))
            c.fill(oval(x0 - 0.15 * rr, y0 - 0.15 * rr, rr * 0.3, rr * 0.25), '#ffd0c8', int(230 * g))
    # rim light from the window / streetlight
    if light and light.get('rim'):
        with c.clip(sil_all):
            c.fill(_crescent(sil_all, -light.get('side', 1) * 1.6, 0), light['rim'], light.get('rim_a', 60))
    with c.clip(mouth, diff=True):
        for sp_ in sils:
            c.line(sp_, lw * 1.2, pal['line'])
    for dz, s, ep, pts in ears:
        if dz >= 0.45:
            c.fill(ep, skin); c.fill(_crescent(ep, s * 0.8, 0.4), skin_sh, 160); c.line(ep, lw, pal['line'])
            ce = smooth([(pts[i][0] * 0.55 + pts[(i + 6) % 12][0] * 0.45, pts[i][1] * 0.55 + pts[(i + 6) % 12][1] * 0.45) for i in (1, 2, 3, 4)], False)
            c.line(ce, lw * 0.6, pal['skin_dk'], 200)
    return hd, sil_all


# ---------------------------------------------------------------------------------------------------- the body
def _sh_torso(c, view, R, P, det, t, light, st):
    """The vendor jacket: pink and white VERTICAL stripes, buttoned to the throat, a round white collar; when he
    transforms the back bulges and splits along the stripes."""
    pal = _SH_PAL
    lw = c.lw
    bul = st['split']
    rings = []
    for hrow, w, d in _WS_ROWS:
        p, a = _ws_spine_pt(R, hrow)
        ph = np.linspace(0, 2 * PI, 24, endpoint=False)
        k = 1.0 + 0.16 * bul * math.exp(-((hrow - 50.0) / 18.0) ** 2)
        back = np.where(np.sin(ph) < 0, k + 0.1 * bul * np.cos(ph * 3) ** 2, 1.0)
        loc = np.stack([w * np.cos(ph) * (1 + 0.06 * bul), np.zeros_like(ph), d * np.sin(ph) * back], -1)
        Q = p + _rx(loc, a)
        X, Y, _, _ = view.pa(Q)
        rings.append(np.stack([X, Y], -1))
    body = None
    for i in range(len(rings) - 1):
        h = poly(_hull(np.vstack([rings[i], rings[i + 1]])), True)
        body = h if body is None else union(body, h)
    c.line(body, lw * 2.0, pal['line'])
    c.fill(body, pal['white'])
    front_n = _rx(np.array([0.0, 0.0, 1.0]), R['a2'] + R['a1'])
    fz = float(view.face(front_n)[0])
    front = fz >= 0.0
    with c.clip(body):
        # stripes: even in angle round the body so they wrap like real vertical stripes
        hs = np.linspace(-12.0, 72.0, 14)
        nst = 9
        for side_ in (False, True):          # both halves; a stripe is drawn where its surface faces the lens
            for i in range(nst):
                a0 = -PI / 2 + (i + 0.25) * PI / nst; a1 = -PI / 2 + (i + 0.75) * PI / nst
                nrm = _ws_surf(R, 40.0, math.sin((a0 + a1) / 2), 0.3, side_)[1]
                if view.face(nrm)[0] < -0.02: continue
                e0 = [view.p2(_ws_surf(R, h_, math.sin(a0), 0.3, side_)[0]) for h_ in hs]
                e1 = [view.p2(_ws_surf(R, h_, math.sin(a1), 0.3, side_)[0]) for h_ in hs[::-1]]
                c.fill(poly(e0 + e1, True), pal['pink'])
        xs = np.concatenate([r[:, 0] for r in rings])
        c.grad(body, xs.min(), 0, xs.max(), 0, [(0, '#ffffff', 60), (0.45, pal['white'], 0), (1, pal['pink_sh'], 150)])
        if det >= 1: c.texture(body, 'fabric', 0.10, 0.6)
        hem = [view.p2(_ws_surf(R, -8.0, x_)[0]) for x_ in np.linspace(-1, 1, 9)]
        c.line(smooth(hem, False), lw * 3.0, pal['white_sh'], 120)
        if light and light.get('rim'):
            c.fill(_crescent(body, -light.get('side', 1) * 1.5, 0), light['rim'], light.get('rim_a', 60))
        if front and fz > 0.05:
            cf = [view.p2(_ws_surf(R, h_, 0.0)[0]) for h_ in (-12.0, 10.0, 30.0, 50.0, 66.0)]
            c.line(smooth(cf, False), lw * 0.8, pal['line'], 200)
            for h_ in (4.0, 18.0, 32.0, 46.0, 60.0):
                q, n = _ws_surf(R, h_, 0.07, 1.2)
                X, Y = view.p2(q); _, _, _, f = view.p(q)
                bt = oval(X, Y, 1.2 * f, 1.2 * f)
                c.fill(bt, '#fdfbfc'); c.line(bt, lw * 0.5, pal['line'])
            # the snowflake SHIVER badge on his left chest
            q, n = _ws_surf(R, 50.0, 0.55, 1.2)
            if view.face(n)[0] > 0.1:
                X0, Y0, _, f = view.p(q)
                r0 = 4.2 * f
                pts = []
                for k in range(12):
                    a_ = -PI / 2 + k * PI / 6
                    rr = r0 if k % 2 == 0 else r0 * 0.62
                    pts.append((X0 + rr * math.cos(a_), Y0 + rr * math.sin(a_)))
                sf = poly(pts, True)
                c.fill(sf, pal['badge']); c.line(sf, lw * 0.7, pal['badge_rim'])
                if det >= 2 and f * c.s * r0 > 6:
                    _block_text(c, 'SHIVER', X0, Y0 + 0.1 * r0, 0.32 * r0, '#3d5671', 255, w=0.06 * r0)
        if not front and bul > 0.02:
            # the back splits along a stripe seam: torn edges, a dark gap where the legs come out
            gap_w = 0.05 + 0.30 * bul
            e0 = [view.p2(_ws_surf(R, h_, -gap_w * (0.6 + 0.4 * hash01(int(h_), 3401)), 0.5, False)[0]) for h_ in np.linspace(14, 68, 9)]
            e1 = [view.p2(_ws_surf(R, h_, gap_w * (0.6 + 0.4 * hash01(int(h_), 3402)), 0.5, False)[0]) for h_ in np.linspace(68, 14, 9)]
            gp = poly(e0 + e1, True)
            c.fill(gp, '#140c10', int(255 * clamp(bul * 1.6)))
            c.line(gp, lw * 0.8, pal['white_sh'], int(255 * bul))
    c.line(body, lw, pal['line'])
    if bul > 0.02 and front:
        # seen from the front: the shoulders bulge, torn stripe ends lift behind the collar line
        for s in (-1, 1):
            q = _ws_surf(R, 66.0, s * 0.75, 0.0, False)[0] + _rx(np.array([0.0, -6.0 * bul, -2.0]), R['a'])
            X, Y, _, f = view.p(q)
            for k in range(3):
                ang = -PI / 2 + s * (0.4 + 0.25 * k)
                L_ = (5 + 4 * k) * f * bul
                tri = poly([(X - 2 * f, Y), (X + 2 * f, Y), (X + math.cos(ang) * L_, Y + math.sin(ang) * L_)], True)
                c.fill(tri, pal['pink'] if k % 2 == 0 else pal['white']); c.line(tri, lw * 0.6, pal['line'])
    return body, fz


def _sh_collar(c, view, R, P, det, fz):
    """Round white collar, the pink bow tie and its silver snowflake pin."""
    if fz < -0.05: return
    pal = _SH_PAL
    lw = c.lw
    a = R['a'] + R.get('hunch', 0.0)
    B = R['Sc'] + _rx(np.array([0.0, 3.5, 9.5]), a)
    tx = _rx(np.array([1.0, 0.0, 0.0]), a); ty = _rx(np.array([0.0, 1.0, 0.0]), a); tz = _rx(np.array([0.0, 0.0, 1.0]), a)
    pr = view.p2
    for s in (-1, 1):   # Peter Pan collar: two rounded white flaps
        fl = smooth([pr(B + tx * s * 0.5 - ty * 2.5), pr(B + tx * s * 7.5 - ty * 3.0 - tz * 2.0), pr(B + tx * s * 9.0 + ty * 1.0 - tz * 1.0),
                     pr(B + tx * s * 6.0 + ty * 4.2), pr(B + tx * s * 1.0 + ty * 3.0)], True, 0.6)
        c.fill(fl, '#fbf8f9'); c.fill(_crescent(fl, 0, -1.0), pal['white_sh'], 140); c.line(fl, lw * 0.8, pal['line'])
    Bb = B + ty * 1.0 + tz * 1.0
    for s in (-1, 1):
        wing = smooth([pr(Bb + tx * s * 1.0), pr(Bb + tx * s * 6.4 - ty * 3.2), pr(Bb + tx * s * 7.0 + ty * 0.2), pr(Bb + tx * s * 6.2 + ty * 3.4)], True, 0.3)
        c.fill(wing, pal['bow']); c.fill(_crescent(wing, 0, 0.8), pal['bow_sh'], 150); c.line(wing, lw * 0.7, pal['line'])
    X, Y, _, f = view.p(Bb + tz * 0.6)
    knot = oval(X, Y, 1.8 * f, 2.1 * f)
    c.fill(knot, pal['bow']); c.line(knot, lw * 0.6, pal['line'])
    # snowflake pin
    r0 = 1.9 * f
    for k in range(3):
        a_ = PI / 2 + k * PI / 3
        dx, dy = math.cos(a_) * r0, math.sin(a_) * r0
        c.line(poly([(X - dx, Y - dy), (X + dx, Y + dy)], False), lw * 0.9, pal['pin'])
        for sgn in (-1, 1):
            bx, by = X + sgn * dx * 0.65, Y + sgn * dy * 0.65
            for b in (-1, 1):
                a2 = a_ + b * 0.7
                c.line(poly([(bx, by), (bx + sgn * math.cos(a2) * r0 * 0.35, by + sgn * math.sin(a2) * r0 * 0.35)], False), lw * 0.5, '#ffffff')


def _sh_neck(c, view, R, st):
    skin = mix(_SH_PAL['skin'], _SH_PAL['bone'], st['long'])
    _ws_tube3(c, view, [R['neck'][0], R['neck'][1], R['head'] + (R['neck'][1] - R['head']) * 0.35], [8.6, 7.8, 8.0], skin,
              _SH_PAL['skin_sh'], c.lw, None)


def _sh_stripe_tube(c, view, pts, widths, light, n=2):
    """A striped sleeve / trouser tube: pink with white lengthwise stripes that follow the limb."""
    pal = _SH_PAL
    tp, p2 = _ws_tube3(c, view, pts, widths, pal['white'], None, c.lw, None, line=False)
    X, Y, zd, f = view.pa(np.asarray(pts))
    with c.clip(tp):
        for off in (-0.62, 0.0, 0.62):
            q = []
            for i in range(len(pts)):
                j0, j1 = max(0, i - 1), min(len(pts) - 1, i + 1)
                dx, dy = X[j1] - X[j0], Y[j1] - Y[j0]; d = math.hypot(dx, dy) or 1.0
                q.append((X[i] - dy / d * off * widths[i] * f[i], Y[i] + dx / d * off * widths[i] * f[i]))
            c.line(smooth(q, False), widths[0] * float(f[0]) * 0.42, pal['pink'])
        c.fill(_crescent(tp, 1.2, 0.5), pal['pink_sh'], 120)
        if light and light.get('rim'): c.fill(_crescent(tp, -light.get('side', 1) * 1.0, 0), light['rim'], light.get('rim_a', 60) * 0.8)
    c.line(tp, c.lw, pal['line'])
    return tp, p2


def _sh_arm(c, view, R, P, s, det, t, light, hands=True):
    """Long striped sleeve to the wrist, a white cuff, the ribbed cuff of a white knitted wool glove, the glove."""
    pal = _SH_PAL
    arm = R['arms'][s]
    S, E, W = arm['S'], arm['J'][0], arm['W']
    cuff = E + (W - E) * 0.80
    _sh_stripe_tube(c, view, [S, (S + E) / 2, E], [10.5, 9.4, 8.4], light)
    _sh_stripe_tube(c, view, [E, (E + cuff) / 2, cuff], [8.4, 7.8, 7.4], light)
    X, Y, _, f = view.p(cuff)
    Xe, Ye, _, _ = view.p(E)
    d = math.hypot(X - Xe, Y - Ye) or 1.0
    ux, uy = (X - Xe) / d, (Y - Ye) / d
    nx, ny = -uy * 4.0 * f, ux * 4.0 * f
    c.line(poly([(X - nx, Y - ny), (X + nx, Y + ny)], False), c.lw * 2.4, '#fbf8f9')
    # knitted rib cuff
    tw, p2 = _ws_tube3(c, view, [cuff, W], [4.6, 4.4], _SH_WSPAL['glove'], _SH_WSPAL['glove_sh'], c.lw, light)
    if det >= 1:
        with c.clip(tw):
            for k in range(-3, 4):
                ox, oy = -uy * k * 1.1 * f, ux * k * 1.1 * f
                c.line(poly([(X + ox, Y + oy), (p2[-1][0] + ox, p2[-1][1] + oy)], False), c.lw * 0.5, '#b9bec8', 200)
    if hands: _ws_glove(c, view, R, P, s, _SH_WSPAL, det, t, light)


def _sh_leg_h(c, view, R, s, det, light):
    """His human legs: pink-striped vendor trousers to the shoe, plain dark shoes."""
    Hp, K, A, fd = R['legs'][s]
    tr, tr_sh = '#d9d0d6', '#a89aa4'
    _ws_tube3(c, view, [Hp, (Hp + K) / 2, K], [15.0, 13.5, 12.0], tr, tr_sh, c.lw, light)
    _ws_tube3(c, view, [K, (K + A) / 2, A + np.array([0.0, 3.0, 0.0])], [12.0, 11.2, 10.8], tr, tr_sh, c.lw, light)
    X, Y, _, f = view.p(A + np.array([0.0, 6.0, 0.0]))
    Xt, Yt, _, _ = view.p(A + fd * 26.0 + np.array([0.0, 7.0, 0.0]))
    if math.hypot(Xt - X, Yt - Y) < 4 * f: sh = oval((X + Xt) / 2, (Y + Yt) / 2, 6 * f, 3.5 * f)
    else: sh = _tube([(X, Y), ((X + Xt) / 2, (Y + Yt) / 2 - 0.5 * f), (Xt, Yt)], [7.0 * f, 6.5 * f, 5.0 * f], 0.9)
    c.fill(sh, '#2e2629'); c.fill(_crescent(sh, 0, -1.2), '#5a4c52', 120); c.line(sh, c.lw, _SH_PAL['line'])


# ---------------------------------------------------------------------------------------------------- spider legs
_SH_LEG_L = (34.0, 185.0, 200.0, 125.0)       # coxa, femur, tibia, tarsus (cm, rig units): ~2.8x his height stretched
_SH_LEG_ORDER = (1, 0, 3, 2, 5, 4, 7, 6)       # the order they punch out (his right top first)


def _sh_leg_root(R, i):
    s = 1 if i % 2 == 0 else -1
    k = i // 2
    h = 66.0 - 9.0 * k
    q, n = _ws_surf(R, h, s * 0.42, -1.0, False)
    return q, s, k


def _sh_leg_rest(R, P, i):
    """Default tip (body frame, cm) for leg i: a wide stance on the ground (y = 0), knees high."""
    s = 1 if i % 2 == 0 else -1
    k = i // 2
    sp = float(P.sh_spread)
    zz = (120.0, 45.0, -40.0, -120.0)[k]
    xx = s * (170.0 + 45.0 * (1.5 - abs(k - 1.5))) * sp
    return np.array([xx, 0.0, zz]) + np.array([0.0, 0.0, R['Hc'][2]])


def _sh_leg_chain(R, P, i, e):
    """Joints (root, coxa end, knee, ankle, tip) for leg i, emerged e (0 folded in the back .. 1 planted)."""
    Rt, s, k = _sh_leg_root(R, i)
    w = float(getattr(P, 'sh_t%dw' % i))
    rest = _sh_leg_rest(R, P, i)
    if w > 0:
        tgt = np.array([getattr(P, 'sh_t%dx' % i), getattr(P, 'sh_t%dy' % i), getattr(P, 'sh_t%dz' % i)])
        T = rest + (tgt - rest) * clamp(w)
    else:
        T = rest
    lift = float(getattr(P, 'sh_t%dlift' % i))
    if lift: T = T + np.array([0.0, -lift, 0.0])
    a = R['a']
    upv = np.array([0.0, -1.0, 0.0])
    hor = T - Rt; hor[1] = 0.0
    out = _u3(hor + np.array([s * 30.0, 0.0, 0.0])) if np.linalg.norm(hor) > 1 else np.array([float(s), 0.0, 0.0])
    C1 = Rt + _u3(out * 0.6 + upv * 0.8 + _rx(np.array([0.0, 0.0, -0.5]), a)) * _SH_LEG_L[0]
    a_, b_ = _SH_LEG_L[1], _SH_LEG_L[2] + _SH_LEG_L[3] * 0.85
    # harvestman knee: always up and out over its own side (never crossing over his head), then down to the tip
    hd = T - C1; hd[1] = 0.0
    hdl = float(np.linalg.norm(hd))
    oh = hd / hdl if hdl > 1e-6 else out
    kh = 0.80 + 0.35 * hash01(i, 3601)                 # every knee at its own height: never a neat row
    x_ = min(0.42 * hdl + 25.0, a_ * 0.92)
    y_ = math.sqrt(max(a_ * a_ - x_ * x_, 0.0)) * kh
    K = C1 + oh * x_ + upv * y_
    if K[1] > min(C1[1], T[1]) - 40.0:                 # keep the knee the highest point
        K[1] = min(C1[1], T[1]) - 40.0
    # the ankle joint between the knee and the needle tip, bent a little outward so all three joints read
    A = K + (T - K) * 0.58 + _u3(out + upv * 0.5) * 24.0
    full = [Rt, C1, K, A, T]
    if e >= 0.999: return full
    # folded: the leg pressed up the back, the knee over the shoulder (punching out = unfolding fast)
    e1 = ease_out_cubic(prog(e, 0.0, 0.35)); e2 = ease_in_out(prog(e, 0.3, 1.0))
    Kf = Rt + _u3(upv * 1.0 + out * 0.25 + _rx(np.array([0.0, 0.0, -0.35]), a)) * 120.0
    Af = Kf + _u3(out * 1.0 - upv * 0.2) * 70.0
    Tf = Af + _u3(-upv * 1.0 + out * 0.3) * 60.0
    fold = [Rt, C1, Kf, Af, Tf]
    out_l = []
    for q_f, q_p in zip(fold, full):
        qf = Rt + (q_f - Rt) * e1
        out_l.append(qf + (q_p - qf) * e2)
    return out_l


def _sh_leg_items(view, R, P, st, det, light, zt):
    """Depth-sorted draw items for the legs (each segment its own item)."""
    pal = _SH_PAL
    n = st['legs']
    items = []
    for j, i in enumerate(_SH_LEG_ORDER):
        e = clamp(n - j)
        if e <= 0.01: continue
        ch = _sh_leg_chain(R, P, i, e)
        widths = ((13.0, 11.5), (11.5, 8.5), (8.0, 5.0), (4.6, 0.6))
        for sgi in range(4):
            a3, b3 = ch[sgi], ch[sgi + 1]
            z = (view.depth(a3) + view.depth(b3)) / 2
            if sgi == 0: z = min(z, zt - 3.0)
            items.append((z + 0.001 * i, lambda cc, a3=a3, b3=b3, sgi=sgi, ch=ch, i=i: _sh_leg_seg(cc, view, a3, b3, sgi, widths[sgi], det, light, i)))
    return items


def _sh_leg_seg(c, view, a3, b3, sgi, wd, det, light, i):
    pal = _SH_PAL
    lw = c.lw
    mid = (a3 + b3) / 2
    if sgi == 3:
        # tarsus: brown into a pale needle tip
        q = a3 + (b3 - a3) * 0.62
        tp, p2 = _ws_tube3(c, view, [a3, q], [wd[0], wd[0] * 0.55], pal['leg'], pal['leg_dk'], lw, light)
        X, Y, _, f = view.pa(np.array([q, b3]))
        tp2 = _tube([(float(X[0]), float(Y[0])), (float(X[1]), float(Y[1]))], [wd[0] * 0.55 * float(f[0]), 0.25], 0.8)
        c.fill(tp2, pal['tip']); c.line(tp2, lw * 0.7, pal['line'])
    else:
        bend = (b3 - a3)
        tp, p2 = _ws_tube3(c, view, [a3, mid + _u3(np.cross(bend, np.array([0.0, 0.0, 1.0])) + 1e-9) * wd[0] * 0.25, b3],
                           [wd[0], (wd[0] + wd[1]) / 2 * 0.92, wd[1]], pal['leg'], pal['leg_dk'], lw, light)
        if det >= 1:
            with c.clip(tp):
                c.line(poly(p2, False), lw * 0.8, pal['leg_hi'], 120)
                # bristles / chitin bands
                for k in range(3):
                    u = (k + 1) / 4.0
                    X, Y = view.p2(a3 + (b3 - a3) * u)
                    c.fill(oval(X, Y, wd[0] * 0.9, wd[0] * 0.35), pal['leg_dk'], 70)
    # the joint at the start of this segment: a dark knuckle with frost rime
    if sgi >= 1:
        X, Y, _, f = view.p(a3)
        r = wd[0] * 0.58 * f
        c.fill(oval(X, Y, r, r * 0.9), pal['leg_dk']); c.line(oval(X, Y, r, r * 0.9), lw * 0.7, pal['line'])
        if det >= 1:
            for k in range(6):
                ang = hash01(i * 17 + sgi * 5 + k, 3501) * 2 * PI
                rr = r * (0.6 + 0.6 * hash01(i * 17 + sgi * 5 + k, 3502))
                cx_, cy_ = X + math.cos(ang) * r * 0.55, Y + math.sin(ang) * r * 0.55 - r * 0.25
                c.fill(poly([(cx_ - rr * 0.28, cy_ + rr * 0.1), (cx_, cy_ - rr * 0.3), (cx_ + rr * 0.24, cy_ + rr * 0.12)], True), pal['rime'], 215)
            for k in range(3):
                ang = -PI / 2 + (k - 1) * 0.6
                c.line(poly([(X + math.cos(ang) * r * 0.6, Y + math.sin(ang) * r * 0.6),
                             (X + math.cos(ang) * r * 1.15, Y + math.sin(ang) * r * 1.15)], False), lw * 0.4, '#ffffff', 140)


# ---------------------------------------------------------------------------------------------------- the figure
def _sh_rig(P, st):
    if P.sh_lift > 1.0:     # slung in the cage of legs: knees folded up, the body pitched forward, the head hanging
        k = clamp(P.sh_lift / 80.0)
        P = P.copy(); P.ws_crouch = max(P.ws_crouch, 1.25 * k); P.ws_bend = max(P.ws_bend, 0.38 * k)
        P.ws_face_up = min(P.ws_face_up, 0.75 - 0.45 * k)
    R = _ws_rig(P)
    # his long neck: the head rides up the neck line
    Nb = R['Nb']; d = _u3(R['head'] - Nb)
    ext = d * float(P.sh_neck)
    R['head'] = R['head'] + ext
    R['neck'] = [R['neck'][0], R['neck'][1] + ext]
    R['mouth'] = R['mouth'] + ext
    lift = float(P.sh_lift)
    if lift:
        sh = np.array([0.0, -lift, 0.0])

        def mv(o):
            if isinstance(o, np.ndarray) and o.shape == (3,): return o + sh
            if isinstance(o, dict): return {k: (v if k in ('M', 'H', 'fold', 'squash', 'ceil', 'k', 'rest', 'ax') else mv(v)) for k, v in o.items()}
            if isinstance(o, (list, tuple)):
                r_ = [mv(v) for v in o]; return tuple(r_) if isinstance(o, tuple) else r_
            return o
        keep = {k: R[k] for k in ('hrot', 'a', 'a1', 'a2', 'hunch', 'crouch', 'bend', 'hat_ext')}
        legs = {s_: (mv(v[0]), mv(v[1]), mv(v[2]), v[3]) for s_, v in R['legs'].items()}     # fd is a direction
        R = {k: mv(v) for k, v in R.items()}
        R.update(keep); R['legs'] = legs
        # the human legs hang limp: feet dangle, toes down
    return R


def _shiver_figure(c, who, P, det, t, light=None, upper_only=False):
    sp = CAST[who]
    st = _sh_state(P)
    sc = max(P.ws_scale, 1e-3)
    cc = c.sub(0.0, 0.0, 0.0, _WSU * sc)
    view = _WSView(P)
    R = _sh_rig(P, st)
    pal = _SH_WSPAL
    skip = int(getattr(P, 'ws_hands_front', 0) or 0)
    if skip == 3:
        l_, r_ = P.ws_lw > 0.6, P.ws_rw > 0.6
        skip = 2 if (l_ and r_) else (1 if l_ else (-1 if r_ else 0))
    items = []
    zt = view.depth(R['Ch'])
    if not upper_only and P.sh_nolegs < 0.5:
        for s in (-1, 1):
            Hp, K, A, fd = R['legs'][s]
            zl = (view.depth(K) + view.depth(A)) / 2
            if view.depth(K) < zt + 8.0: zl = min(zl, zt - 6.0)
            items.append((zl + 0.01 * s, lambda cc_, s=s: _sh_leg_h(cc_, view, R, s, det, light)))
    stt = {}

    def torso(cc_):
        body, fz = _sh_torso(cc_, view, R, P, det, t, light, st)
        stt['fz'] = fz
        if fz > -0.05: _sh_neck(cc_, view, R, st)
    items.append((zt, torso))
    zh = view.depth(R['head'])

    def head(cc_):
        if stt.get('fz', 1) <= -0.05: _sh_neck(cc_, view, R, st)
        if stt.get('fz', 1) > -0.05: _sh_collar(cc_, view, R, P, det, stt.get('fz', 1))
        _sh_head_draw(cc_, R, view, P, det, t, light, st)
    items.append((max(zh, zt + 1.0) if view.depth(_rx(np.array([0.0, 0.0, 1.0]), R['a'])) > -0.2 else zh - 2.0, head))
    for s in (-1, 1):
        arm = R['arms'][s]
        za = (view.depth(arm['S']) + view.depth(arm['J'][0]) + 2 * view.depth(arm['W'])) / 4
        hands = not (skip in (2, s))
        items.append((za + 0.02 * s, lambda cc_, s=s, hands=hands: _sh_arm(cc_, view, R, P, s, det, t, light, hands)))
    if st['legs'] > 0.01:
        items += _sh_leg_items(view, R, P, st, det, light, zt)
    items.sort(key=lambda q: q[0])
    dark = clamp((light or {}).get('dark', 0.0))
    if dark > 0.01:
        cv = cc.cv
        cv.saveLayer(None, None)
        for z, fn in items: fn(cc)
        cv.drawPaint(skia.Paint(Color=skia.Color4f(0.02, 0.018, 0.03, float(dark)), BlendMode=skia.BlendMode.kSrcATop))
        cv.restore()
        _sh_glow_feats(cc, R, view, P, st, 0.4 + 0.6 * dark)
        return R
    for z, fn in items: fn(cc)
    return R


def _sh_glow_feats(c, R, view, P, st, amount):
    """In the dark only the eyes (blue pinpoints, or red) and the teeth catch light."""
    hd = _SHHead(R, view, P, st)
    for s in (-1, 1):
        X_, Y_, F_, _ = hd.proj(np.array([s * 0.25]), np.array([0.13]), -0.5)
        if F_[0] < 0.05: continue
        _, _, _, f_ = view.p(hd.p3(s * 0.25, 0.13))
        x0, y0 = float(X_[0]), float(Y_[0])
        if st['red'] > 0.3:
            c.glow(x0, y0, 6.0 * f_, 5.0 * f_, _SH_PAL['red'], int(160 * amount))
            c.fill(oval(x0, y0, 0.9 * f_, 0.8 * f_), _SH_PAL['red'], int(255 * amount))
        elif st['sink'] < 0.5:
            c.glow(x0, y0, 3.0 * f_, 3.0 * f_, _SH_PAL['eye'], int(110 * amount))
            c.fill(oval(x0, y0, 0.7 * f_, 0.7 * f_), '#bfe6ff', int(255 * amount))
    W = hd.W
    for lon_ in np.linspace(-0.6 * W, 0.6 * W, 7):
        X_, Y_, F_, _ = hd.proj(np.array([lon_]), np.array([float(hd.up(lon_)) - 0.03]), 0.2, jaw=0.0)
        if F_[0] > 0.1:
            _, _, _, f_ = view.p(hd.p3(lon_, float(hd.up(lon_))))
            c.fill(oval(float(X_[0]), float(Y_[0]), 1.0 * f_, 0.8 * f_), '#d9dde6', int(150 * amount))


_figure_ice_prev = _figure


def _figure(c, who, P, det, t, light=None, upper_only=False):
    if CAST[who].get('shiver'): return _shiver_figure(c, who, P, det, t, light, upper_only)
    return _figure_ice_prev(c, who, P, det, t, light, upper_only)


CAST['shiver'] = dict(CAST['whistle'], shiver=True, m=_SH_M, hh=170.0, breath=0.0, tv=False)


def _sh_pts(P):
    st = _sh_state(P)
    view = _WSView(P); R = _sh_rig(P, st)
    k = _WSU * max(P.ws_scale, 1e-3)
    pr = lambda q: tuple(v * k for v in view.p2(q))            # noqa: E731
    hd = _SHHead(R, view, P, st)
    out = _ws_pts(P)       # arms, hands, knees, feet (no lift); head points from his own head below
    out = {kk: v for kk, v in out.items()}
    mid_m = (hd.p3(0.0, float(hd.up(0.0)), 0.0, 0.0) + hd.p3(0.0, float(hd.lo(0.0)), 0.0, 1.0)) / 2
    out.update(head=pr(hd.C), eyes=pr(hd.p3(0.0, 0.13)), mouth=pr(mid_m), grin=pr(mid_m), chin=pr(hd.p3(0.0, -1.4)),
               crown=pr(hd.p3(0.0, 1.5)), neck=pr(R['Nb']), chest=pr(R['Ch'] + _rx(np.array([0.0, 0.0, 11.0]), R['a'])),
               hip=pr(R['Hc']), eye_l=pr(hd.p3(0.25, 0.13)), eye_r=pr(hd.p3(-0.25, 0.13)))
    if P.sh_lift:
        for kk in list(out):
            if kk.startswith(('hand', 'tips', 'wrist', 'elbow', 'shoulder', 'knee', 'foot')):
                out[kk] = (out[kk][0], out[kk][1] - P.sh_lift * k)
    n = st['legs']
    for j, i in enumerate(_SH_LEG_ORDER):
        ch = _sh_leg_chain(R, P, i, clamp(n - j) if n > j else 1.0)
        out['leg%d' % i] = pr(ch[-1]); out['knee%d' % i] = pr(ch[2])
    return out


_body_point_prev_ice = _body_point


def _body_point(self, P, part):
    if self.sp.get('shiver'):
        pts = _sh_pts(P)
        return pts.get(part, pts['head'])
    return _body_point_prev_ice(self, P, part)


# ====================================================================================================== PEOPLE
# All built on the v3 human rig (faces, hands, look_at, reach IK, walk/run, carry, kneel, seats): see CAST.md.
# Adam, 12 (the narrator): dark hair under a red knitted hat, a puffy navy coat, snow boots. Careful, then brave.
_ADAM = dict(hair='della_cap', sex='m', hh=212.0, child=True, m=1.50, head_ws=[0, 55, 80, 95, 100, 100, 94, 81, 60, 32, 0],
             eye_dx=41, eye_y=2, eye_r=20.5, iris_c='#4a3424', iris_k=0.7, lid_rest=0.12, pupil=1.05, brow_th=7.5, nose_len=15,
             mouth_y=62, mouth_w=16, nose='button', ears=1.1,
             skin='#efc8ac', skin_sh='#c4987f', skin_dp='#80594c', blush='#e8a096', lip='#bf827a', lips=0.05,
             hair_c='#2a1c14', brow_c='#22160e', bags=0.2, age=0.0, blink_rate=0.3, lashes=0.3, part=-1,
             body=dict(sh=94, ch=94, wa=90, hip=88, arm=(39, 33), leg=(43, 36), neck=32, hand=0.84, arm_k=0.9))
_ADAM_CLOTH = dict(top='#263a66', top_sh='#16244a', top_hi='#3c5590', hood='#22355e', hood_sh='#14213f', string='#d9d4c8',
                   trousers='#3a3f4c', trousers_sh='#23262e', shoes='#5a4636', shoes_sh='#36281e', cap='#c8322f', cap_sh='#8e1f1f',
                   socks='#e4e1da', socks_sh='#b5b1a8')
CAST['adam'] = _v3cast(outfit='raincoat_kid', feet='boots', **_ADAM, cloth=dict(_ADAM_CLOTH))
CAST['adam_in'] = _v3cast(outfit='hoodie3', feet='socks', **dict(_ADAM, hair='side_short'),        # indoors, no hat
                          cloth=dict(_ADAM_CLOTH, top='#4b6a8c', top_sh='#324c6a', top_hi='#6a8aac'))
CAST['adam_sock'] = _v3cast(outfit='raincoat_kid', feet='socks', **_ADAM, cloth=dict(_ADAM_CLOTH))   # lost a boot (see CAST.md)

# Lina, 6: big gap-toothed smile, pink pyjamas with snowflakes, an open puffy yellow coat, a pom-pom hat, bare hands.
_LINA = dict(_JUNE, hair='della_cap', hair_c='#3a2418', brow_c='#2c1a10', iris_c='#4a3020', gap=True, m=1.15, hh=242.0,
             skin='#f1c9ae', skin_sh='#c89a84', blush='#f2a198')
_LINA_PJ = dict(top='#f2a8c4', top_sh='#c97898', top_hi='#f9cadb', trim='#fbf4f7', print_c='#ffffff', print_c2='#bfe3ff',
                trousers='#f2a8c4', trousers_sh='#c97898', socks='#f4f2ee', socks_sh='#c9c5bc', sock_toe='#f2a8c4', tie='#e87aa4',
                cap='#f4c742', cap_sh='#c99a24')
CAST['lina_pj'] = _v3cast(outfit='pj3', feet='socks', **dict(_LINA, hair='pigtails'), cloth=dict(_LINA_PJ))
CAST['lina'] = _v3cast(outfit='coat_small', feet='boots', **_LINA,
                       cloth=dict(_LINA_PJ, top='#f4c742', top_sh='#c99a24', top_hi='#fbe08a', collar='#fbfaf4', button='#c98a2a',
                                  legs='#f2a8c4', legs_sh='#c97898', trousers='#f2a8c4', trousers_sh='#c97898', shoes='#e85a7a',
                                  shoes_sh='#a83a52', cap='#e87aa4', cap_sh='#b0507a'))

# Dad: big, a hi-vis orange plow jacket, a brown trapper hat, stubble; warm and steady.
CAST['dad'] = _v3cast(
    outfit='jacket3', hair='della_cap', sex='m', hh=180.0, m=1.88, head_ws=[0, 53, 77, 92, 97, 96, 89, 75, 54, 30, 0],
    eye_dx=42, eye_y=-6, eye_r=17.5, iris_c='#4a3424', lid_rest=0.22, brow_th=10.0, nose_len=24, mouth_w=22,
    skin='#e2b293', skin_sh='#b5846c', skin_dp='#744c40', blush='#d98d80', lip='#a46a60', stubble='#4a3424', stub=0.55,
    hair_c='#3a2a1e', brow_c='#2e2016', bags=0.45, age=0.35, feet='boots',
    body=dict(sh=134, ch=132, wa=124, hip=116, arm=(56, 45), leg=(62, 50), neck=50, hand=1.08),
    cloth=dict(top='#f07a1e', top_sh='#b85412', top_hi='#ffa24a', collar='#3a3430', shirt='#4a4440', shirt_sh='#2e2a26',
               trousers='#3a3a40', trousers_sh='#232328', shoes='#3a2c22', shoes_sh='#22180f', button='#dfe2e6', cap='#6a4a30',
               cap_sh='#3e2a1a', stripe='#e6eaee'))

# Mr. Walter Kessler, about 80: thin, stooped, white stubble, large ears, thick glasses, a grey cardigan. Grumpy, kind.
_KES = dict(_GRANDPA)
_KES.update(glasses=True, ears=1.4, stubble='#e8e4dc', stub=0.45, hair_c='#ece8e0', brow_c='#dcd8d0', m=1.72, lock=0.2)
CAST['kessler'] = dict(_KES, outfit='cardi_m', feet='slippers',
                       cloth=dict(top='#7d7f86', top_sh='#55575e', top_hi='#9a9ca3', shirt='#e7dcc4', shirt_sh='#bfb196',
                                  check='#b49a7a', trousers='#5a5048', trousers_sh='#3a332c', shoes='#6a4a3a', shoes_sh='#43301f',
                                  button='#3a3430'))
CAST['kessler_out'] = dict(_KES, outfit='tee_jeans', feet='slippers',            # undershirt, no coat (severe cold)
                           cloth=dict(top='#c9c7c0', top_sh='#9a988f', top_hi='#e2e0da', trousers='#5a5048', trousers_sh='#3a332c',
                                      shoes='#6a4a3a', shoes_sh='#43301f', jeans='#5a5048', jeans_sh='#3a332c'))
CAST['kessler_am'] = dict(CAST['kessler'])

# 1958 (sepia, from behind, far): Walter at twelve (Adam's rig, flat cap read by a dark crown) and little Benny, 6,
# in striped pyjamas.
CAST['walter58'] = _v3cast(outfit='raincoat_kid', feet='boots', **dict(_ADAM, hair='della_cap'),
                           cloth={k: _greyed(v, 0.7, '#a08a6a', 0.05) for k, v in dict(_ADAM_CLOTH, cap='#4a3a2a', cap_sh='#2a2018').items()})
CAST['benny'] = _v3cast(outfit='pj3', feet='socks', **dict(_JUNE, hair='cowlick', sex='m', hair_c='#6a4a2a'),
                        cloth={k: _greyed(v, 0.6, '#a08a6a', 0.05) for k, v in dict(_LINA_PJ, top='#d9d2c4', print_c='#7a8aa0').items()})
CAST['medic_a'] = dict(CAST['medic']) if 'medic' in CAST else dict(CAST['medic2'])
CAST['medic_b'] = dict(CAST['medic2'])
# "Mom" at the door is HIS copy: a hospital coat and scarf; the real Mom only in a photo (labcoat over a sweater).
CAST['mom_photo'] = _v3cast(
    outfit='labcoat3', hair='lowbun', sex='f', hh=184.0, m=1.66, eye_dx=40, eye_y=-6, eye_r=18.5, iris_c='#4a3424', lid_rest=0.2,
    brow_th=7.0, nose_len=21, mouth_w=20, skin='#e8bea4', skin_sh='#bd917b', skin_dp='#7d564b', blush='#e19c94', lip='#b06a6c',
    lips=0.5, hair_c='#3a2418', brow_c='#2c1a10', bags=0.45, age=0.3, lashes=1.0, feet='shoes',
    body=dict(sh=104, ch=104, wa=90, hip=106, arm=(42, 34), leg=(46, 38), neck=34, hand=0.98),
    cloth=dict(top='#eef0f2', top_sh='#bcc2c8', top_hi='#ffffff', shirt='#7a9ac0', shirt_sh='#5a7aa0', trousers='#3a4a6a',
               trousers_sh='#263248', shoes='#2a2a30', shoes_sh='#141418', pocket='#dfe3e8', button='#dfe3e8', scarf='#b0485e'))
CAST['shiver_mom'] = dict(CAST['mom_photo'], breath=0.0, blink_rate=0.0, lock=1.0, micro=0.0)

ICE_CAST = ('shiver', 'adam', 'adam_in', 'adam_sock', 'lina', 'lina_pj', 'dad', 'kessler', 'kessler_out', 'kessler_am',
            'walter58', 'benny', 'medic_a', 'medic_b', 'mom_photo', 'shiver_mom')
# every outfit finds the cloth keys it reads (missing ones fall back to the costume's own colours)
for _w in ICE_CAST:
    if _w == 'shiver': continue
    _c = CAST[_w].setdefault('cloth', {})
    _top, _tsh = _c.get('top', '#888888'), _c.get('top_sh', '#555555')
    for _k, _v in dict(top_hi=mix(_top, '#ffffff', 0.25), tie=_tsh, tie_hi=_top, collar=mix(_top, '#ffffff', 0.5), collar_sh=_tsh,
                       button='#e8e4dc', shirt='#e8e2d4', shirt_sh='#bdb5a4', shirt_hi='#f6f2ea', trim=mix(_top, '#ffffff', 0.6),
                       hood=_top, hood_sh=_tsh, string='#e9e4d8', trousers='#3a3f4c', trousers_sh='#23262e', legs=_c.get('trousers', '#3a3f4c'),
                       legs_sh=_c.get('trousers_sh', '#23262e'), socks='#e4e1da', socks_sh='#b5b1a8', sock_toe=_top, shoes='#3a2c22',
                       shoes_sh='#22180f', print_c='#ffffff', print_c2=_tsh, cap=_tsh, cap_sh=mix(_tsh, '#000000', 0.3),
                       scarf='#b0485e', scarf_sh='#7a2e40', scarf_hi='#d0687e', pocket=_tsh, check=_tsh, rib=_tsh, tee=_top,
                       sweater=_top, coat=_top, coat_sh=_tsh, coat_hi=mix(_top, '#ffffff', 0.25), lace='#ffffff', sash='#ffffff',
                       stitch=_tsh, belt='#2a2420', buckle='#c9b27a', badge='#e8e4dc').items():
        _c.setdefault(_k, _v)


# ====================================================================================================== ACTING: SHIVER
# a = CH.Acting('shiver', seed=1, height=CH.height_px('shiver', ppm)).place(x, floor_y)  (floor_y = where his feet would
# stand: in the truck, below the window sill; the set masks him to the window). Every whistle-rig tool works too:
# reach_to / reach_far (gloves, world targets), lean_to (down, and down), look_at (the whole head turns), say (no lips).
def _sh_m_curve(times):
    """times: 8 times for SH_STEPS -> (fn(t) -> sh_m, inverse(m) -> t)."""
    ts = list(times); ms = list(SH_STEPS)

    def m_at(t):
        if t <= ts[0]: return ms[0]
        for k in range(len(ts) - 1):
            if t < ts[k + 1]:
                return ms[k] + (ms[k + 1] - ms[k]) * ease_in_out(clamp((t - ts[k]) / max(ts[k + 1] - ts[k], 1e-6) / 0.85))
        return ms[-1]

    def t_at(m):
        for k in range(len(ms) - 1):
            if ms[k] <= m <= ms[k + 1]:
                return ts[k] + (ts[k + 1] - ts[k]) * 0.85 * (m - ms[k]) / max(ms[k + 1] - ms[k], 1e-6)
        return ts[-1]
    return m_at, t_at


def _sh_transform(self, t0, times=None, step=1.4):
    """THE TRANSFORMATION, one parameter through the bible's steps. times: 8 times (one per SH_STEPS: waving, smile,
    long bone face, eyes sink, red, jaw, split + legs punching out, planted) keyed to the narration's words; default
    every `step` s from t0. Events: 'sh_smile_creak', 'sh_bone_crack', 'sh_eyes_sink', 'sh_eyes_red', 'sh_jaw_drop',
    'sh_uniform_split', 'leg_click' x8 (each leg planting)."""
    times = list(times) if times is not None else [t0 + k * step for k in range(8)]
    m_at, t_at = _sh_m_curve(times)

    def fn(P, t):
        P.sh_m = max(P.sh_m, m_at(t))
    self._add(times[0], None, fn)
    evs = [self._ev(times[1], 'sh_smile_creak', -6.0), self._ev(times[2], 'sh_bone_crack', -3.0),
           self._ev(times[3], 'sh_eyes_sink', -8.0), self._ev(t_at(SH_STAGES['red'][0]), 'sh_eyes_red', -4.0),
           self._ev(times[5] - 0.3, 'sh_jaw_drop', 0.0), self._ev(t_at(SH_STAGES['split'][0]), 'sh_uniform_split', -2.0)]
    a, b = SH_STAGES['legs']
    for j in range(8):
        evs.append(self._ev(t_at(a + (b - a) * (j + 1) / 8.0), 'leg_click', -2.0 + (2.0 if j < 3 else 0.0), leg=_SH_LEG_ORDER[j]))
    return evs


def _sh_shrink_back(self, t0, dur=1.6, frm=1.0):
    """The defeat: the legs fold away, the jaw closes, the skull shrinks back into the smile (sh_m frm -> 0)."""
    def fn(P, t):
        u = ease_in_out(prog(t, t0, t0 + dur))
        if t >= t0: P.sh_m = frm * (1.0 - u)
    self._add(t0, None, fn)
    return [self._ev(t0, 'legs_fold', -3.0), self._ev(t0 + dur * 0.7, 'sh_jaw_close', -6.0)]


def _sh_glimpse(self, t0, dur=0.13):
    """One flicker: the long white face with red eyes, then the smile again (head only)."""
    def fn(P, t):
        if t0 <= t < t0 + dur: P.sh_glim = 1.0
    self._add(t0, t0 + dur, fn)
    return [self._ev(t0, 'flicker_sting', 0.0)]


def _sh_slow_wave(self, t0, t1, side=1, period=2.2, lift=0.0):
    """His slow, over-long wave: the glove up beside the head, swinging in a slow arc (keeps going through the change)."""
    def tgt(t, s=side):
        sx, sy = self.where(t, 'shoulder_' + ('l' if s > 0 else 'r'))
        hx, hy = self.where(t, 'head')
        ppc = _ws_ppc(self)
        ph = math.sin(2 * PI * (t - t0) / period)
        out = 1.0 if sx >= hx else -1.0
        return (hx + out * (44.0 + 10.0 * ph) * ppc, hy - (16.0 + lift) * ppc + abs(ph) * 3.0 * ppc)
    return self.reach_to(t0, side, tgt, t1=t1, dur=0.9, shape='host', z=25.0)


def _sh_world_cm(self, P, wx, wy, zd=0.0):
    q = _ws_world_to_cm(P, wx, wy, zd)
    return q if q is not None else np.zeros(3)


def _sh_leg_to(self, t0, i, target, dur=0.35, hold=0.8, back=0.5, arc=70.0, zd=40.0, ev='leg_stab'):
    """Leg i's needle tip goes to a world target (x, y) / callable / (actor, part): a fast stab (snow, a coat, a
    blanket, under a door), holds, and goes back (back=None: stays). 'leg_stab' at contact."""
    t1 = t0 + dur; t2 = t1 + hold

    def fn(P, t):
        if t < t0: return
        tx, ty = _target_xy(target, t)
        q = _sh_world_cm(self, P, tx, ty, zd)
        u = ease_in_out(prog(t, t0, t1))
        if back is not None and t > t2: u = 1.0 - ease_in_out(prog(t, t2, t2 + back))
        setattr(P, 'sh_t%dw' % i, u); setattr(P, 'sh_t%dx' % i, q[0]); setattr(P, 'sh_t%dy' % i, q[1]); setattr(P, 'sh_t%dz' % i, q[2])
        setattr(P, 'sh_t%dlift' % i, arc * math.sin(PI * clamp(prog(t, t0, t1))) if t < t1 else 0.0)
    self._add(t0, None if back is None else t2 + back, fn)
    return [self._ev(t1, ev, 0.0, leg=i)]


def _sh_legs_plant(self, t0, targets, stagger=0.07, dur=0.22, zd=40.0):
    """Plant several legs on world points {i: (x, y)} (a roof, the snow round the kids), one click each."""
    evs = []
    for k, (i, tg) in enumerate(sorted(targets.items())):
        evs += _sh_leg_to(self, t0 + k * stagger, i, tg, dur=dur, hold=1e6, back=None, arc=50.0, zd=zd, ev='leg_click')
    return evs


def _sh_scuttle(self, t0, t1, path, ground=None, stride=None, swing=0.16, lift=0.0, ease=0.25):
    """He scuttles: path(u) -> world (x, y) of his feet origin for u 0..1 (eased in/out), ground(x) -> world y of the
    surface under a leg tip (a fence top, a car, a roof; default: the path's y). Each leg steps in a staggered gait,
    needle tips planted between steps. 'leg_click' on every landing (pan follows)."""
    phases = [((j * 3) % 8) / 8.0 for j in range(8)]
    S_ = stride if stride is not None else self.height * 0.55
    dur = t1 - t0

    def body_xy(t):
        u = clamp((t - t0) / dur)
        k = ease
        if u < k: uu = u * u / (2 * k * (1 - k))
        elif u > 1 - k: uu = 1 - (1 - u) ** 2 / (2 * k * (1 - k))
        else: uu = (u - k / 2) / (1 - k)
        return path(clamp(uu)), clamp(uu)

    def fn(P, t):
        if t < t0: return
        (bx, by), uu = body_xy(t)
        P.dx += bx - self.x0; P.dy += by - self.y0
        P.sh_lift = max(P.sh_lift, lift)
        view = _WSView(P)
        R = _sh_rig(P, _sh_state(P))
        sc = self.height / 1000.0 * _WSU * max(P.ws_scale, 1e-3)
        for j, i in enumerate(_SH_LEG_ORDER):
            rc = _sh_leg_rest(R, P, i)
            rx_, ry_ = view.p2(rc)
            ox = rx_ * sc
            xb = bx - self.x0
            ph = phases[j] * S_
            n = math.floor((xb + ph) / S_)
            fr = (xb + ph) / S_ - n
            spot0 = n * S_ - ph; spot1 = spot0 + S_
            sw = clamp((fr - (1 - swing)) / swing)
            tipx = self.x0 + ox + spot0 + (spot1 - spot0) * ease_in_out(sw)
            gy = ground(tipx) if ground is not None else by
            q = _sh_world_cm(self, P, tipx, gy, rc[2])
            setattr(P, 'sh_t%dw' % i, 1.0); setattr(P, 'sh_t%dx' % i, q[0]); setattr(P, 'sh_t%dy' % i, q[1]); setattr(P, 'sh_t%dz' % i, q[2])
            setattr(P, 'sh_t%dlift' % i, 45.0 * math.sin(PI * sw))
    self._add(t0, None, fn)
    evs = []
    n_ev = int(dur / 0.11)
    for k in range(n_ev):
        evs.append(self._ev(t0 + 0.11 * k + 0.05 * hash01(k, 3701), 'leg_click', -6.0 - 3.0 * hash01(k, 3702), leg=k % 8))
    return evs


def _sh_drop_to(self, t0, dur=0.45, from_dy=-400.0, land=None):
    """Drops from above (a roof edge) to the feet point: falls with the legs folded high, lands, the legs slam out round
    him ('sh_land' + clicks). from_dy: start offset (px, negative = above)."""
    def fn(P, t):
        if t < t0: P.dy += from_dy; P.sh_spread = 0.35; return
        u = prog(t, t0, t0 + dur)
        P.dy += from_dy * (1.0 - u * u)
        P.sh_spread = 0.35 + 0.65 * ease_out_back(prog(t, t0 + dur * 0.85, t0 + dur + 0.25))
    self._add(-INF, None, fn)
    return [self._ev(t0 + dur, 'sh_land', 2.0)] + [self._ev(t0 + dur + 0.04 * k, 'leg_click', -3.0, leg=k) for k in range(4)]


def _sh_cage(self, t0, center, width, ground_y, dur=0.5, lift=150.0):
    """Legs arched over people like a cage: tips planted in a ring round `center` (world x) on ground_y; he hangs above."""
    def fl(P, t):
        if t >= t0: P.sh_lift = max(P.sh_lift, lift * ease_in_out(prog(t, t0, t0 + dur)))
    self._add(t0, None, fl)
    tg = {}
    for j, i in enumerate(_SH_LEG_ORDER):
        s = 1 if i % 2 == 0 else -1
        k = i // 2
        tg[i] = (center + s * width * (0.55 + 0.17 * k), ground_y)
    return _sh_legs_plant(self, t0, tg, stagger=0.06, dur=dur * 0.5)


def _sh_pour_out(self, t0, dur=2.4, sill_dy=-300.0, ground_dy=200.0, forward=1.0, lift=110.0):
    """He pours out of the serving window head first, legs last: the body rises to the sill and tips over it head first
    (rotating about his hips at the sill), slides down the side of the truck to the snow, and only then the legs come out
    (sh_legcap 0 -> 8), plant, and lift him upright into the cage of legs. sill_dy: px from his feet origin up to the sill;
    ground_dy: px from the origin down to the snow. His human legs stay hidden (inside the truck) throughout."""
    def fn(P, t):
        P.sh_nolegs = 1.0
        if t < t0: P.sh_legcap = 0.0; return
        u = prog(t, t0, t0 + dur)
        a = ease_in_out(prog(u, 0.0, 0.40))           # up onto the sill and over, head first
        b = ease_in_out(prog(u, 0.30, 0.70))          # sliding down the side, head down
        c = ease_in_out(prog(u, 0.62, 1.00))          # legs out, plant, rights itself
        P.tilt += forward * ((95.0 * a + 45.0 * b) * (1.0 - c))      # head first, down the side of the truck
        P.dy += sill_dy * a * (1.0 - c) + ground_dy * c
        P.dx += forward * self.height * (0.18 * a + 0.10 * b + 0.25 * c)
        P.sh_legcap = 8.0 * ease_out_cubic(prog(u, 0.58, 0.95))
        P.sh_lift = max(P.sh_lift, lift * c)
    self._add(-INF, None, fn)
    return [self._ev(t0, 'sh_pour', 0.0), self._ev(t0 + dur * 0.7, 'leg_click', -2.0), self._ev(t0 + dur * 0.85, 'leg_click', -2.0)]


def _sh_hang(self, t0, dur=0.9, lower=0.4):
    """The attic hatch: upside down (the only one in the film), the head lowering through the hatch."""
    def fn(P, t):
        P.tilt += 180.0
        P.dy -= self.height * (1.0 - lower * ease_in_out(prog(t, t0, t0 + dur)))
    self._add(-INF, None, fn)
    return [self._ev(t0, 'hatch_drop', 0.0)]


def _sh_jaw_gape(self, t0, t1):
    """The hung last note: the jaw strains open for the note and can't close (a slow tremor)."""
    def fn(P, t):
        if t0 <= t: P.sh_gape = max(P.sh_gape, ease_in_out(prog(t, t0, t0 + 0.5)) * (0.8 + 0.2 * math.sin(t * 23.0)))
    self._add(t0, t1, fn)
    return [self._ev(t0, 'sh_jaw_strain', -4.0)]


Acting.transform = _sh_transform
Acting.shrink_back = _sh_shrink_back
Acting.glimpse = _sh_glimpse
Acting.slow_wave = _sh_slow_wave
Acting.leg_to = _sh_leg_to
Acting.legs_plant = _sh_legs_plant
Acting.scuttle = _sh_scuttle
Acting.drop_to = _sh_drop_to
Acting.cage = _sh_cage
Acting.pour_out = _sh_pour_out
Acting.hang_hatch = _sh_hang
Acting.jaw_gape = _sh_jaw_gape
