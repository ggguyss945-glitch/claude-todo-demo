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
               legs=max(prog(m, *SH_STAGES['legs']) * 8.0, P.sh_legs))
    g = clamp(P.sh_glim)
    if g > 0:
        out['smile'] = max(out['smile'], g); out['long'] = max(out['long'], g); out['red'] = max(out['red'], g)
        out['sink'] = max(out['sink'], g)
    out['jaw'] = clamp(out['jaw'] + 0.12 * P.sh_gape)
    return out


# ---------------------------------------------------------------------------------------------------- the head
_SH_HR = (13.0, 17.8, 14.2)       # cm: half width, crown up, depth (an egg: the dome taller than the jaw)
_SH_CHIN = 14.2


def _sh_mouth(W, L, sm):
    """Lip latitudes for the smile: upper(lon), lower(lon) and the corner latitude."""
    def up(lon):
        q = np.clip(np.abs(np.asarray(lon, float)) / W, 0, 1)
        return -0.37 + 0.19 * q ** 2 - 0.05 * L

    def lo(lon):
        q = np.clip(np.abs(np.asarray(lon, float)) / W, 0, 1)
        return up(lon) - (0.12 + 0.05 * sm) * (1.0 - q ** 2) ** 0.8
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
    z = z + fr * (2.7 * (1.0 - 0.85 * L) * np.exp(-(lon / 0.12) ** 2 - ((lat + 0.06) / 0.15) ** 2)          # the nose
                  + (1.1 + 0.8 * L) * np.exp(-((np.abs(lon) - 0.52) / 0.24) ** 2 - ((lat + 0.06) / 0.13) ** 2)  # cheekbones
                  + (0.9 + 0.6 * L) * np.exp(-((lat - 0.31) / 0.10) ** 2) * np.exp(-(lon / 0.6) ** 2)        # brow ridge
                  - (1.3 + 2.2 * L) * np.exp(-((np.abs(lon) - 0.27) / 0.13) ** 2 - ((lat - 0.13) / 0.11) ** 2)  # sockets
                  - (0.9 + 1.4 * L) * np.exp(-((np.abs(lon) - 0.66) / 0.20) ** 2 - ((lat + 0.36) / 0.17) ** 2))  # hollows
    x = x - np.sign(lon) * (0.9 + 0.6 * L) * np.exp(-((np.abs(lon) - 1.25) / 0.30) ** 2 - ((lat - 0.22) / 0.22) ** 2)  # temples
    return np.stack([x, y, z], -1)


_SH_CROWN = float(-_sh_head_local(0.0, PI / 2)[1])


class _SHHead:
    """His head in the body frame, projected. The jaw (below the lower lip and its line back toward the ears) drops."""

    def __init__(self, R, view, P, st):
        self.R, self.view, self.P, self.st = R, view, P, st
        self.M = R['hrot']; self.C = R['head']
        self.L = st['long']; self.J = st['jaw']; self.sm = st['smile']
        self.W = 0.98 + 0.72 * self.sm + 0.10 * self.L
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
            drop = self.J * (30.0 + 8.0 * self.L)
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
    path = smooth(pp, True, 0.35 if icy <= 0.5 else 0.15)
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
        Ec = hd.body(_sh_head_local(s * 1.52, 0.02, 0.6, L)[None, :])[0]
        M = R['hrot']
        out_ = M @ np.array([s * 1.0, 0.0, 0.0]); upv = M @ np.array([0.0, -1.0, 0.0]); bk = M @ np.array([0.0, 0.0, -1.0])
        ring = [Ec + upv * (3.6 * math.cos(a_)) * (1.0 if math.cos(a_) > 0 else 0.85) + bk * (2.4 * math.sin(a_) + 0.6) + out_ * (1.4 + 0.6 * math.sin(a_))
                for a_ in np.linspace(0, 2 * PI, 12, endpoint=False)]
        pts = [view.p2(q) for q in ring]
        ears.append((view.depth(out_), s, smooth(pts, True, 0.8), pts))
    for dz, s, ep, pts in ears:
        if dz < -0.15:
            c.fill(ep, skin); c.line(ep, lw, pal['line'])
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
    with c.clip(sil_all):
        # cold shading: lit from upper left, blue-grey into the shadow side and under the chin
        c.grad(sil_all, Xc - r_ * 0.9, Yc - r_ * 0.5, Xc + r_ * 0.9, Yc + r_ * 0.6,
               [(0, pal['skin_hi'], 150), (0.45, skin, 0), (1.0, skin_sh, 235)])
        c.glow(Xc - r_ * 0.35, Yc - r_ * 0.62, r_ * 0.55, r_ * 0.4, '#ffffff', 90)
        # cheek hollows and temples
        for s in (-1, 1):
            hp = hd.region(s * 0.46, s * 0.95, lambda q: -0.62 - 0.1 * L + 0 * q, lambda q: -0.28 + 0 * q, 8, 4)
            if hp is not None: c.fill(hp, skin_sh, 70 + int(80 * L))
            tp_ = hd.region(s * 1.0, s * 1.45, 0.05, 0.42, 6, 4)
            if tp_ is not None: c.fill(tp_, skin_sh, 60)
        if det >= 1:
            c.texture(sil_all, 'skin', 0.08, 0.5)
        # faint blue veins at the temples (cold)
        if det >= 1 and L < 0.6:
            for s in (-1, 1):
                for run in hd.curve(s * np.linspace(0.92, 1.25, 7), 0.30 + 0.06 * np.sin(np.linspace(0, 5, 7))):
                    c.line(smooth(run, False), lw * 0.45, '#8aa3c4', int(90 * (1 - L)))
        # forehead creases (age, not a doll) and under-eye bags
        if det >= 1:
            for la_ in (0.50, 0.60):
                for run in hd.curve(np.linspace(-0.45, 0.45, 11), la_ + 0.025 * np.cos(np.linspace(-1.5, 1.5, 11))):
                    c.line(smooth(run, False), lw * 0.5, skin_sh, int(150 * (1 - L)))
    # eye sockets: shadowed hollows (the owner's reference: dark sockets around tiny eyes)
    sink, red = st['sink'], st['red']
    for s in (-1, 1):
        lon_e = s * 0.27
        so, fso = hd.disc(lon_e, 0.13, 0.17 + 0.05 * L, 0.10 + 0.05 * L, grow=0.1)
        if fso > -0.1:
            c.fill(so, pal['socket'], int(120 + 135 * max(L, sink)))
            if L > 0.05 or sink > 0.05:
                so2, _ = hd.disc(lon_e, 0.13, 0.13 + 0.05 * L, 0.075 + 0.05 * L, grow=0.12)
                c.fill(so2, '#07060a', int(255 * max(sink, 0.6 * L)))
                c.line(so2, lw * 0.9, pal['line'], int(220 * L))
            if det >= 1:   # lower lid bag line
                for run in hd.curve(lon_e + s * np.linspace(-0.13, 0.12, 7), 0.035 - 0.015 * np.sin(np.linspace(0, PI, 7))):
                    c.line(smooth(run, False), lw * 0.7, pal['skin_dk'], int(170 * (1 - L)))
    # the nose: a small sharp pale nose (fades into a dark nasal cavity as the mask forms)
    fn_ = hd.facing(0.0, -0.05)
    if fn_ > 0:
        if L < 0.7:
            a_ = int(255 * (1 - L / 0.7))
            for s in (-1, 1):
                for run in hd.curve(s * np.array([0.03, 0.08, 0.12, 0.10, 0.05]), np.array([0.02, -0.07, -0.14, -0.18, -0.19]), 0.6):
                    c.line(smooth(run, False), lw * 0.9, pal['skin_dk'], a_)
            nost, _ = hd.disc(0.0, -0.17, 0.10, 0.025, grow=0.7)
            c.fill(nost, pal['skin_sh'], int(a_ * 0.6))
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
        icy = max(prog(J, 0.15, 0.6), prog(L, 0.6, 1.0) * 0.6)
        c.fill(mouth, mix(pal['mouth'], pal['mouth_m'], max(L, J)))
        with c.clip(mouth):
            M = R['hrot']
            dn = M @ _u3(np.array([0.0, 1.0, 0.12])); upd = M @ _u3(np.array([0.0, -1.0, 0.12]))
            # upper teeth
            n_up = 9 if icy < 0.5 else 15
            for i in range(n_up):
                u = (i + 0.5) / n_up * 2 - 1
                lon_ = u * W * (0.86 if icy < 0.5 else 0.95)
                if icy < 0.5 and abs(lon_) < 0.13 * W: continue           # the buck teeth go in last
                root = hd.p3(lon_, float(hd.up(lon_)) + 0.02, 0.0, jaw=0.0)
                tg = _u3(hd.p3(lon_ + 0.02, float(hd.up(lon_ + 0.02)), 0.0, 0.0) - hd.p3(lon_ - 0.02, float(hd.up(lon_ - 0.02)), 0.0, 0.0))
                if hd.facing(lon_, float(hd.up(lon_))) < -0.05: continue
                if icy < 0.5:
                    wid = 2.2 * (1 - 0.4 * abs(u)); ln = 1.9 * (1 - 0.3 * abs(u))
                else:
                    wid = 1.5 + 0.6 * hash01(i, 3201); ln = (6.0 + 9.0 * hash01(i, 3202)) * (1 - 0.35 * abs(u)) * (0.4 + 0.6 * J)
                _sh_tooth(c, view, hd, root, dn, tg, wid, ln, pal['icicle'] if icy >= 0.5 else pal['teeth'], pal['icicle_rim'], lw, icy)
            # lower teeth (gap-toothed in the vendor grin)
            n_lo = 8 if icy < 0.5 else 13
            for i in range(n_lo):
                u = (i + 0.5) / n_lo * 2 - 1
                if icy < 0.5 and hash01(i, 3203) < 0.3: continue
                lon_ = u * W * 0.8
                if hd.facing(lon_, float(hd.lo(lon_))) < -0.05: continue
                root = hd.p3(lon_, float(hd.lo(lon_)) - 0.015, 0.0, jaw=1.0)
                tg = _u3(hd.p3(lon_ + 0.02, float(hd.lo(lon_ + 0.02)), 0.0, 1.0) - hd.p3(lon_ - 0.02, float(hd.lo(lon_ - 0.02)), 0.0, 1.0))
                if icy < 0.5:
                    wid = 1.7; ln = 1.3
                else:
                    wid = 1.3 + 0.5 * hash01(i, 3204); ln = (4.0 + 7.0 * hash01(i, 3205)) * (0.4 + 0.6 * J)
                _sh_tooth(c, view, hd, root, upd, tg, wid, ln, pal['icicle'] if icy >= 0.5 else pal['teeth'], pal['icicle_rim'], lw, icy)
            # the two big buck teeth with a gap between them (fade as the mouth turns to icicles)
            if icy < 0.9:
                a_ = int(255 * (1 - icy / 0.9))
                for s in (-1, 1):
                    lon_ = s * 0.075
                    root = hd.p3(lon_, float(hd.up(lon_)) + 0.025, 0.0, jaw=0.0)
                    tg = _u3(hd.p3(lon_ + 0.02, float(hd.up(lon_)), 0.0, 0.0) - hd.p3(lon_ - 0.02, float(hd.up(lon_)), 0.0, 0.0))
                    _sh_tooth(c, view, hd, root + tg * s * 0.25, dn, tg, 3.0, 4.3, pal['teeth'], pal['icicle_rim'], lw, 0.0, a_)
            if J > 0.25:   # no throat: the dark deepens into the middle
                Xm, Ym = view.p2((hd.p3(0.0, float(hd.up(0.0)), 0.0, 0.0) + hd.p3(0.0, float(hd.lo(0.0)), 0.0, 1.0)) / 2)
                c.glow(Xm, Ym, 60.0 * J, 90.0 * J, '#000000', 230)
        # lips: pale, thin; the upper lip over the teeth roots, the lower under them
        if L < 0.85:
            a_ = int(255 * (1 - L / 0.85))
            up_run = [(float(x), float(y)) for x, y, f in zip(Xu, Yu, Fu) if f > -0.05]
            lo_run = [(float(x), float(y)) for x, y, f in zip(Xl, Yl, Fl) if f > -0.05]
            if len(up_run) > 1: c.line(smooth(up_run, False), lw * 2.6, pal['lip'], a_)
            if len(lo_run) > 1: c.line(smooth(lo_run, False), lw * 3.2, pal['lip'], a_)
        c.line(mouth, lw * 1.1, pal['line'])
    # frost: flecks on the brow (normal), frost cracks across the mask (monster)
    if det >= 1:
        for i in range(26):
            lo_ = (hash01(i, 3301) - 0.5) * 1.5; la_ = 0.30 + hash01(i, 3302) * 0.55
            X_, Y_, F_, _ = hd.proj(np.array([lo_]), np.array([la_]), 0.3)
            if F_[0] < 0.15: continue
            r0 = (0.25 + 0.35 * hash01(i, 3303)) * c.lw * 2.0
            x0, y0 = float(X_[0]), float(Y_[0])
            c.fill(oval(x0, y0, r0, r0), pal['frost'], 230)
            if hash01(i, 3304) > 0.6:
                for k in range(3):
                    a_ = k * PI / 3
                    c.line(poly([(x0 - math.cos(a_) * r0 * 2.2, y0 - math.sin(a_) * r0 * 2.2),
                                 (x0 + math.cos(a_) * r0 * 2.2, y0 + math.sin(a_) * r0 * 2.2)], False), lw * 0.35, '#ffffff', 200)
    if L > 0.15:
        ka = prog(L, 0.15, 0.9)
        for k, pts in enumerate(_SH_CRACKS):
            n_ = max(2, int(len(pts) * ka + 0.5))
            lo_ = [p_[0] for p_ in pts[:n_]]; la_ = [p_[1] * (0.85 + 0.0) for p_ in pts[:n_]]
            for run in hd.curve(lo_, la_, 0.25):
                c.line(poly(run, False), lw * 1.0, pal['crack_dk'], int(220 * ka))
                c.line(poly(run, False), lw * 0.45, pal['crack'], int(255 * ka))
    # eyes: tiny bright blue with a pinpoint highlight; they sink, a beat of black, then red
    for s in (-1, 1):
        lon_e = s * 0.25
        X_, Y_, F_, zd_ = hd.proj(np.array([lon_e]), np.array([0.13]), -0.5 - 2.0 * sink)
        if F_[0] < 0.05: continue
        x0, y0 = float(X_[0]), float(Y_[0])
        _, _, _, f_ = view.p(hd.p3(lon_e, 0.13))
        rr = 1.15 * f_
        kb = 1.0 - prog(sink, 0.0, 0.9)
        if kb > 0.02 and red < 0.5:
            c.fill(oval(x0, y0, rr * (0.55 + 0.45 * kb) * 1.15, rr * (0.55 + 0.45 * kb)), '#0d1b2a', int(255 * kb))
            c.fill(oval(x0, y0, rr * 0.8 * kb, rr * 0.75 * kb), pal['eye'], int(255 * kb))
            c.fill(oval(x0 + 0.1 * rr, y0 + 0.1 * rr, rr * 0.38 * kb, rr * 0.38 * kb), pal['eye_dk'], int(255 * kb))
            c.fill(oval(x0 - 0.3 * rr, y0 - 0.3 * rr, rr * 0.2, rr * 0.2), '#ffffff', int(255 * kb))
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
    for sp_ in sils:
        c.line(sp_, lw * 1.2, pal['line'])
    for dz, s, ep, pts in ears:
        if dz >= -0.15:
            c.fill(ep, skin); c.fill(_crescent(ep, s * 0.8, 0.4), skin_sh, 160); c.line(ep, lw, pal['line'])
            ce = smooth([(pts[i][0] * 0.55 + pts[(i + 6) % 12][0] * 0.45, pts[i][1] * 0.55 + pts[(i + 6) % 12][1] * 0.45) for i in (1, 2, 3, 4)], False)
            c.line(ce, lw * 0.6, pal['skin_dk'], 200)
    return hd, sil_all
