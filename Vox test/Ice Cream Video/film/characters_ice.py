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
    sh_hang=0.55,    # how far the head hangs (h_nod added) when he is slung in the legs (sh_lift)
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
    rx = (_SH_HR[0] + grow) * (1.0 - 0.15 * dn - 0.34 * L * dn ** 1.3) * (1.0 - 0.03 * L)
    ry = np.where(lat > 0, _SH_HR[1] * (1.0 + 0.05 * L), _SH_CHIN * (1.0 + 1.25 * L)) + grow
    rz = (_SH_HR[2] + grow) * (1.0 - 0.06 * L * dn)
    x = rx * cl * np.sin(lon)
    y = -ry * sl
    z = rz * cl * np.cos(lon)
    fr = np.clip(np.cos(lon), 0.0, None)
    z = z + fr * (4.8 * (1.0 - 0.85 * L) * np.exp(-(lon / 0.10) ** 2 - ((lat + 0.08) / 0.13) ** 2)          # the nose
                  + 2.8 * np.exp(-(lon / 0.35) ** 2 - ((lat + 0.95) / 0.20) ** 2)                               # chin
                  + 0.7 * (1.0 - L) * np.exp(-(lon / 0.30) ** 2 - ((lat + 0.33) / 0.08) ** 2)                   # upper lip
                  - 0.8 * np.exp(-(lon / 0.18) ** 2 - ((lat - 0.14) / 0.06) ** 2)                               # nasal bridge
                  + (1.1 + 0.8 * L) * np.exp(-((np.abs(lon) - 0.52) / 0.24) ** 2 - ((lat + 0.06) / 0.13) ** 2)  # cheekbones
                  + (1.9 + 0.9 * L) * np.exp(-((lat - 0.29) / 0.09) ** 2) * np.exp(-(lon / 0.6) ** 2)        # brow ridge
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
            drop = self.J * (20.0 + 5.0 * self.L)
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
            side = abs(self.facing(0.0, 0.0))
            if side >= 0.75:
                return [poly(_hull(P2), True)]
            # turned: the face's profile shows on the silhouette (brow, nasal bridge, nose, lip, chin)
            keep = ~((np.abs(lo) < 0.78) & (la < 0.62))
            sil = poly(_hull(P2[keep]), True)
            if True:
                Xc, Yc = self.view.p2(self.C)
                las = np.linspace(0.80, -1.54, 44)
                for lo_ in np.linspace(-0.80, 0.80, 13):
                    Xf, Yf, _, _ = self.proj(np.full_like(las, lo_), las)
                    try: sil = union(sil, poly([(Xc, Yc)] + list(zip(Xf.tolist(), Yf.tolist())), True))
                    except Exception: pass
            return [sil]
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
        ek = 1.0 - 0.5 * L
        Ec = hd.body(_sh_head_local(s * 1.66, -0.04, 0.15, L)[None, :])[0]
        M = R['hrot']
        out_ = M @ np.array([s * 1.0, 0.0, 0.0]); up0 = M @ np.array([0.0, -1.0, 0.0]); bk0 = M @ np.array([0.0, 0.0, -1.0])
        c15, s15 = math.cos(0.26), math.sin(0.26)
        upv = _u3(up0 * c15 + bk0 * s15)                 # tilted back 15 degrees
        bk = _u3(bk0 * c15 - up0 * s15 + out_ * 0.22)    # nearly flat to the skull
        ring = [Ec + upv * (3.2 * ek * math.cos(a_) - 0.3) * (1.0 if math.cos(a_) > 0 else 0.80)
                + bk * (1.9 * ek * math.sin(a_) * (1.0 if math.sin(a_) > 0 else 0.35) + 0.6) + out_ * 0.6
                for a_ in np.linspace(0, 2 * PI, 12, endpoint=False)]
        pts = [view.p2(q) for q in ring]
        ears.append((view.depth(out_), s, smooth(pts, True, 0.8), pts))
    for dz, s, ep, pts in ears:
        if dz < 0.45:
            c.line(ep, lw * 2.2, pal['line']); c.fill(ep, skin); c.fill(_crescent(ep, -s * 0.8, 0.3), skin_sh, 200)
    sils = hd.sils()
    # mouth hole (behind the skin when the jaw drops: the dark between skull and jaw)
    W = hd.W
    lons = np.linspace(-W, W, 31)
    up_lat, lo_lat = hd.up(lons), hd.lo(lons)
    Xu, Yu, Fu, _ = hd.proj(lons, up_lat, 0.1, jaw=0.0)
    Xl, Yl, Fl, _ = hd.proj(lons, lo_lat, 0.1, jaw=1.0)
    vm = np.maximum(Fu, Fl) > -0.10
    if J < 0.05 and 3 < vm.sum() < len(vm):       # turned: only the visible run (a crescent back toward the ear)
        idx = np.where(vm)[0]
        i0, i1 = int(idx.min()), int(idx.max()) + 1
        Xu, Yu, Fu, Xl, Yl, Fl = Xu[i0:i1], Yu[i0:i1], Fu[i0:i1], Xl[i0:i1], Yl[i0:i1], Fl[i0:i1]
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
        if L > 0.05:
            # the hard skull under the mask: zygoma planes under the sockets, deep temple hollows, the cheek cut-in
            for s in (-1, 1):
                q = [P2(s * a_, b_)[:2] for a_, b_ in ((0.16, -0.06), (0.56, -0.01), (0.80, -0.26), (0.62, -0.46), (0.30, -0.30))]
                c.fill(smooth(q, True, 0.4), pal['bone_sh'], int(130 * L))
                q2 = [P2(s * a_, b_)[:2] for a_, b_ in ((0.58, -0.30), (0.86, -0.28), (0.80, -0.62), (0.52, -0.58))]
                c.fill(smooth(q2, True, 0.5), '#6f7a88', int(110 * L))
                x_, y_, f_ = P2(s * 0.98, 0.36)
                if f_ > -0.3: c.glow(x_, y_, 4.5 * cm, 6.5 * cm, '#5d6876', int(150 * L))
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
            so2, fso = hd.disc(lon_e, 0.13 - 0.01 * L, 0.12 + 0.09 * L, 0.07 + 0.10 * L, grow=0.12)
            if fso > -0.1:
                c.fill(so2, '#050407', int(255 * clamp(max(sink, 0.8 * L))))
                c.line(so2, lw * 0.9, pal['line'], int(220 * L))
                if L > 0.3:
                    c.line(so2, lw * 0.5, pal['frost'], int(210 * prog(L, 0.3, 1.0)))
                    for run in hd.curve(lon_e + s * np.linspace(-0.20, 0.20, 9), 0.32 + 0.05 * np.sin(np.linspace(0, PI, 9)), 0.2):
                        c.line(smooth(run, False), lw * 1.4, pal['bone_sh'], int(200 * L))
                    for run in hd.curve(lon_e + s * np.linspace(-0.17, 0.17, 7), 0.36 + 0.05 * np.sin(np.linspace(0, PI, 7)), 0.3):
                        c.line(smooth(run, False), lw * 0.9, '#ffffff', int(170 * L))
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
            if f_ > 0.6: c.fill(oval(x_ - 0.3 * cm, y_ - 0.4 * cm, 0.7 * cm, 0.5 * cm), '#ffffff', int(a_ * 0.7))
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
            for run in hd.curve(np.array([s * 0.16, s * 0.30, s * (0.42 + 0.40 * W)]),
                                np.array([-0.12, -0.21, -0.29]), 0.3):
                c.line(smooth(run, False), lw * 1.6, pal['skin_sh'], int(90 * (1 - 0.6 * L)))
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
                # the mouth's side walls: pale stretched sinews and frost strands from the skull to the dropped jaw
                ks = prog(J, 0.25, 0.8)
                for sg in (-1, 1):
                    for k in range(5):
                        u0 = 0.62 + 0.08 * k + 0.03 * hash01(k, 3611); u1 = 0.55 + 0.09 * k
                        a0 = hd.p3(sg * W * u0, float(hd.up(W * u0)) - 0.01, 0.0, 0.0)
                        b0 = hd.p3(sg * W * u1, float(hd.lo(W * u1)) + 0.01, 0.0, 1.0)
                        mid = (a0 + b0) / 2 + R['hrot'] @ np.array([-sg * (1.5 + 1.2 * hash01(k, 3612)), 0.0, -2.0])
                        pp = [view.p2(a0), view.p2(mid), view.p2(b0)]
                        if hd.facing(sg * W * u0, float(hd.up(W * u0))) < -0.15: continue
                        c.line(smooth(pp, False), lw * (0.7 + 0.8 * hash01(k, 3613)), '#b9c3cf', int(120 * ks))
            elif icy < 0.5:   # the gum line behind the teeth
                for run in hd.curve(lons * 0.9, hd.up(lons * 0.9) - 0.03, 0.0, -1.0):
                    c.line(smooth(run, False), lw * 2.0, '#6e2a3a', 200)
            # upper teeth
            n_up = 12 if icy < 0.5 else 9
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
                    fang = i in (1, 4, 7)
                    wid = (2.9 if fang else 2.0 + 0.6 * hash01(i, 3201))
                    ln = ((15.0 + 3.0 * hash01(i, 3202)) if fang else (4.5 + 3.5 * hash01(i, 3202))) * (1 - 0.30 * abs(u)) * (0.5 + 0.9 * J)
                _sh_tooth(c, view, hd, root, dn, tg, wid, ln, pal['icicle'] if icy >= 0.5 else pal['teeth'], pal['icicle_rim'], lw, icy)
            # lower teeth (gap-toothed in the vendor grin)
            n_lo = 7
            for i in range(n_lo):
                u = (i + 0.5) / n_lo * 2 - 1
                if icy < 0.5 and i in (2, 4): continue            # the gaps in his lower row
                lon_ = u * W * 0.8
                if hd.facing(lon_, float(hd.lo(lon_))) < -0.05: continue
                root = hd.p3(lon_, float(hd.lo(lon_)) - 0.015, 0.0, jaw=1.0)
                tg = _u3(hd.p3(lon_ + 0.02, float(hd.lo(lon_ + 0.02)), 0.0, 1.0) - hd.p3(lon_ - 0.02, float(hd.lo(lon_ - 0.02)), 0.0, 1.0))
                if icy < 0.5:
                    dl_ = W * 0.8 / n_lo
                    wid = 0.9 * float(np.linalg.norm(hd.p3(lon_ + dl_, float(hd.lo(lon_ + dl_)), 0.0, 1.0) - hd.p3(lon_ - dl_, float(hd.lo(lon_ - dl_)), 0.0, 1.0)))
                    ln = 2.1 * (1 - 0.4 * abs(u))
                else:
                    fang = i in (1, 5)
                    wid = (2.6 if fang else 1.8 + 0.5 * hash01(i, 3204))
                    ln = ((11.0 + 2.0 * hash01(i, 3205)) if fang else (3.5 + 3.0 * hash01(i, 3205))) * (0.5 + 0.8 * J)
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
        if J > 0.3:
            # the dropped jaw ends in a bone mandible: a U band under the lower teeth, cracked, its own shading
            kj = prog(J, 0.3, 0.7)
            Wm = W * 0.98
            band = hd.region(-Wm, Wm, lambda lo_: hd.lo(np.abs(lo_)) - 0.40 - 0.16 * (1 - (np.abs(lo_) / Wm) ** 2),
                             lambda lo_: hd.lo(np.abs(lo_)) - 0.01, nlon=18, nlat=3, grow=0.2, thr=-0.3, jaw=1.0)
            if band is not None:
                c.fill(band, pal['bone'], int(255 * kj))
                bbj = band.getBounds()
                c.grad(band, 0, bbj.top(), 0, bbj.bottom(), [(0, '#ffffff', 0), (0.55, pal['bone'], 0), (1, pal['bone_sh'], int(230 * kj))])
                if det >= 1:
                    for k in range(4):
                        lo0 = (k - 1.5) * 0.45 * Wm
                        run_l = np.array([lo0, lo0 + 0.06, lo0 + 0.02, lo0 + 0.09]); run_a = hd.lo(np.abs(run_l)) - np.array([0.04, 0.12, 0.20, 0.28])
                        for run in hd.curve(run_l, run_a, 0.3, -0.3, jaw=1.0):
                            c.line(poly(run, False), lw * 0.6, pal['crack_dk'], int(220 * kj))
                c.line(band, lw * 1.1, pal['line'], int(255 * kj))
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
            c.fill(ep, skin); c.fill(_crescent(ep, s * 0.6, 0.4), skin_sh, 200); c.line(ep, lw * 0.75, pal['skin_dk'], 230)
            # the helix: a thick C rolled over the back rim (opens toward the face), the concha bowl inside it
            ce = smooth([(pts[i][0] * 0.80 + pts[(i + 6) % 12][0] * 0.20, pts[i][1] * 0.80 + pts[(i + 6) % 12][1] * 0.20) for i in (10, 11, 0, 1, 2, 3, 4, 5)], False)
            c.line(ce, lw * 1.3, pal['line'], 210)
            ci = smooth([(pts[i][0] * 0.55 + pts[(i + 6) % 12][0] * 0.45, pts[i][1] * 0.55 + pts[(i + 6) % 12][1] * 0.45) for i in (11, 0, 1, 2, 3)], False)
            c.line(ci, lw * 0.6, pal['skin_dk'], 200)
            if abs(hd.facing(0.0, 0.0)) < 0.45 and L < 0.5:       # near profile: the jaw line from under the ear to the chin
                for run in hd.curve(s * np.array([1.42, 1.15, 0.85, 0.55, 0.30]), np.array([-0.30, -0.55, -0.74, -0.86, -0.92]), 0.1):
                    c.line(smooth(run, False), lw * 0.9, pal['skin_dk'], int(150 * (1 - 2 * L)))
            cx_ = sum(q[0] for q in pts) / 12; cy_ = sum(q[1] for q in pts) / 12
            ex_ = math.hypot(pts[0][0] - pts[6][0], pts[0][1] - pts[6][1])
            c.fill(oval(cx_, cy_ + ex_ * 0.08, ex_ * 0.10, ex_ * 0.13), pal['skin_dk'], 200)
    return hd, sil_all


# ---------------------------------------------------------------------------------------------------- the body
# his vendor coat: shoulders squared and widened, a waist, the hem flared to mid-thigh (h in cm above the hip centre)
_SH_ROWS = ((-25.0, 17.2, 12.6), (-12.0, 15.6, 11.4), (0.0, 14.2, 10.1), (16.0, 12.4, 9.1), (46.0, 15.6, 10.6), (60.0, 18.9, 9.6),
            (68.0, 16.25, 8.6), (73.5, 8.2, 6.8))


def _sh_surf(R, h, xr, out=1.0, front=True):
    """Point + normal on the coat's surface at height h, across fraction xr (-1 his right .. 1 his left)."""
    rows = _SH_ROWS
    hs = [r[0] for r in rows]
    w = float(np.interp(h, hs, [r[1] for r in rows])); d = float(np.interp(h, hs, [r[2] for r in rows]))
    p, a = _ws_spine_pt(R, h)
    xr = clamp(xr, -1, 1)
    z = d * math.sqrt(max(0.0, 1 - xr * xr)) * (1 if front else -1)
    loc = np.array([xr * w, 0.0, z + (out if front else -out)])
    n = _u3(np.array([xr / max(w, 1), 0.0, (z / max(d * d, 1))]))
    return p + _rx(loc, a), _rx(n, a)


def _sh_torso(c, view, R, P, det, t, light, st):
    """The vendor jacket: pink and white VERTICAL stripes, buttoned to the throat, a round white collar; when he
    transforms the back bulges and splits along the stripes."""
    pal = _SH_PAL
    lw = c.lw
    bul = st['split']
    rings = []
    for hrow, w, d in _SH_ROWS:
        p, a = _ws_spine_pt(R, hrow)
        ph = np.linspace(0, 2 * PI, 24, endpoint=False)
        sw_ = 0.16 + 0.19 * clamp(bul * 1.6) + 0.035 * math.sin(t * 47.0) * bul * (1.0 - clamp(st['legs'] / 2.0))
        k = 1.0 + sw_ * bul * math.exp(-((hrow - 50.0) / 18.0) ** 2)
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
        hs = np.linspace(-25.0, 72.0, 16)
        nst = 9
        for side_ in (False, True):          # both halves; a stripe is drawn where its surface faces the lens
            for i in range(nst):
                a0 = -PI / 2 + (i + 0.25) * PI / nst; a1 = -PI / 2 + (i + 0.75) * PI / nst
                nrm = _sh_surf(R, 40.0, math.sin((a0 + a1) / 2), 0.3, side_)[1]
                if view.face(nrm)[0] < -0.02: continue
                e0 = [view.p2(_sh_surf(R, h_, math.sin(a0), 0.3, side_)[0]) for h_ in hs]
                e1 = [view.p2(_sh_surf(R, h_, math.sin(a1), 0.3, side_)[0]) for h_ in hs[::-1]]
                c.fill(poly(e0 + e1, True), pal['pink'])
        xs = np.concatenate([r[:, 0] for r in rings])
        c.grad(body, xs.min(), 0, xs.max(), 0, [(0, '#ffffff', 60), (0.45, pal['white'], 0), (1, pal['pink_sh'], 150)])
        if det >= 1: c.texture(body, 'fabric', 0.10, 0.6)
        # volume: the coat turns away at both sides, a cold shadow under the chest and in the waist
        c.fill(_crescent(body, 0.0, -6.0), pal['pink_sh'], 70)
        for h_, a_ in ((40.0, 70), (16.0, 60)):
            q0 = view.p2(_sh_surf(R, h_, 0.0)[0]); _, _, _, f0 = view.p(_sh_surf(R, h_, 0.0)[0])
            c.glow(q0[0], q0[1], 16.0 * f0, 3.0 * f0, pal['pink_sh'], a_)
        if front and fz > 0.05 and det >= 1:
            # tension folds pulling from the buttons at the waist, two lower patch pockets with flaps, the hem turned up
            for h_ in (4.0, 18.0, 32.0):
                for sg in (-1, 1):
                    e = [view.p2(_sh_surf(R, h_ + dh, sg * xr_, 1.0)[0]) for dh, xr_ in ((0.0, 0.08), (3.5, 0.30), (6.0, 0.55))]
                    c.line(smooth(e, False), lw * 0.8, pal['pink_sh'], 150)
            for sg in (-1, 1):
                pk = [view.p2(_sh_surf(R, h_, sg * xr_, 1.4)[0]) for h_, xr_ in ((-6.0, 0.25), (-6.0, 0.78), (-20.0, 0.80), (-20.0, 0.27))]
                c.fill(poly(pk, True), '#ffffff', 60); c.line(poly(pk, True), lw * 0.8, pal['pink_sh'], 230)
                fl = [view.p2(_sh_surf(R, -9.0, sg * xr_, 1.5)[0]) for xr_ in (0.25, 0.52, 0.79)]
                c.line(smooth(fl, False), lw * 0.8, pal['pink_sh'], 230)
        hem = [view.p2(_sh_surf(R, -22.5, x_)[0]) for x_ in np.linspace(-1, 1, 11)]
        c.line(smooth(hem, False), lw * 0.8, pal['white_sh'], 200)
        for sg in (-1, 1):                       # side vents
            v = [view.p2(_sh_surf(R, h_, sg * 0.97, 0.3, front)[0]) for h_ in (-25.0, -14.0)]
            c.line(poly(v, False), lw * 1.2, pal['line'], 200)
        if light and light.get('rim'):
            c.fill(_crescent(body, -light.get('side', 1) * 1.5, 0), light['rim'], light.get('rim_a', 60))
        if front and fz > 0.05:
            cf = [view.p2(_sh_surf(R, h_, 0.0)[0]) for h_ in (-25.0, -8.0, 10.0, 30.0, 50.0, 66.0)]
            c.line(smooth(cf, False), lw * 0.8, pal['line'], 200)
            for h_ in (4.0, 18.0, 32.0, 46.0, 60.0):
                q, n = _sh_surf(R, h_, 0.07, 1.2)
                X, Y = view.p2(q); _, _, _, f = view.p(q)
                bt = oval(X, Y, 1.2 * f, 1.2 * f)
                c.fill(bt, '#fdfbfc'); c.line(bt, lw * 0.5, pal['line'])
            # the snowflake SHIVER badge on his left chest
            q, n = _sh_surf(R, 50.0, 0.55, 1.2)
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
            e0 = [view.p2(_sh_surf(R, h_, -gap_w * (0.6 + 0.4 * hash01(int(h_), 3401)), 0.5, False)[0]) for h_ in np.linspace(14, 68, 9)]
            e1 = [view.p2(_sh_surf(R, h_, gap_w * (0.6 + 0.4 * hash01(int(h_), 3402)), 0.5, False)[0]) for h_ in np.linspace(68, 14, 9)]
            gp = poly(e0 + e1, True)
            c.fill(gp, '#140c10', int(255 * clamp(bul * 1.6)))
            c.line(gp, lw * 0.8, pal['white_sh'], int(255 * bul))
    c.line(body, lw, pal['line'])
    if bul > 0.02 and front:
        # seen from the front: the shoulders bulge, torn stripe ends lift behind the collar line
        for s in (-1, 1):
            q = _sh_surf(R, 66.0, s * 0.75, 0.0, False)[0] + _rx(np.array([0.0, -6.0 * bul, -2.0]), R['a'])
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
    """A full set-in sleeve (rounded shoulder cap, seam), creases at the inner elbow, a wide white turned-back cuff, the
    ribbed cuff of a white knitted wool glove, the glove."""
    pal = _SH_PAL
    arm = R['arms'][s]
    S, E, W = arm['S'], arm['J'][0], arm['W']
    a = R['a'] + R.get('hunch', 0.0)
    upv = _rx(np.array([0.0, -1.0, 0.0]), a)
    Sc = S + upv * 2.5 + _rx(np.array([s * 1.5, 0.0, 0.0]), a)          # the shoulder cap sits a little up and out
    cuff = E + (W - E) * 0.80
    _sh_stripe_tube(c, view, [Sc, (S + E) / 2, E, (E + cuff) / 2, cuff], [13.0, 11.6, 10.4, 9.6, 9.0], light)
    X, Y, _, f = view.p(cuff)
    Xe, Ye, _, fe = view.p(E)
    d = math.hypot(X - Xe, Y - Ye) or 1.0
    ux, uy = (X - Xe) / d, (Y - Ye) / d
    if det >= 1:
        # the set-in sleeve seam round the shoulder cap and the creases bunched at the inner elbow
        Xs, Ys, _, fs = view.p(Sc + (E - Sc) * 0.10)
        dxs, dys = Xe - Xs, Ye - Ys; ds = math.hypot(dxs, dys) or 1.0
        nx, ny = -dys / ds, dxs / ds
        w_ = 6.3 * fs
        c.line(smooth([(Xs - nx * w_, Ys - ny * w_), (Xs - dxs / ds * 2.2 * fs, Ys - dys / ds * 2.2 * fs), (Xs + nx * w_, Ys + ny * w_)], False),
               c.lw * 0.8, pal['pink_sh'], 220)
        inner = -s if True else s
        for k in range(3):
            o = (k - 1) * 1.7 * fe
            cx_, cy_ = Xe + ux * o, Ye + uy * o
            nx2, ny2 = -uy, ux
            sg = 1.0 if (nx2 * (view.p2(R['Ch'])[0] - Xe) + ny2 * (view.p2(R['Ch'])[1] - Ye)) > 0 else -1.0
            p0 = (cx_ + nx2 * sg * 1.0 * fe, cy_ + ny2 * sg * 1.0 * fe)
            p1 = (cx_ + nx2 * sg * 3.6 * fe + ux * 0.9 * fe, cy_ + ny2 * sg * 3.6 * fe + uy * 0.9 * fe)
            p3 = (cx_ + nx2 * sg * 5.0 * fe, cy_ + ny2 * sg * 5.0 * fe)
            c.line(smooth([p0, p1, p3], False), c.lw * 0.7, pal['pink_sh'], 200)
    # the turned-back cuff: a wide white band at the sleeve end
    c0 = cuff - (cuff - E) * 0.16
    tc, _ = _ws_tube3(c, view, [c0, cuff], [10.0, 10.4], '#fbf8f9', pal['white_sh'], c.lw, light)
    if det >= 1:
        Xa, Ya = view.p2(c0)
        c.line(poly([(Xa - uy * 4.8 * f, Ya + ux * 4.8 * f), (Xa + uy * 4.8 * f, Ya - ux * 4.8 * f)], False), c.lw * 0.6, pal['white_sh'], 220)
    if hands: _sh_glove(c, view, R, P, s, det, t, light)


def _sh_glove(c, view, R, P, s, det, t, light):
    """His white KNITTED WOOL glove (a child's winter glove on a long hand): plump fingers with round tips, separated by
    soft grey shading (never dark gaps), knuckle bumps, a soft thumb pad, a V-stitch knit texture and a two-row ribbed
    cuff. Only the outer silhouette gets the dark line."""
    pal = _SH_WSPAL
    h = _ws_hand3(R, s, P)
    lw = c.lw
    W, f_, nb = h['W'], h['f'], h['nb']
    g, gsh = '#EDEDED', '#cdd2da'
    back = view.face(nb)[0] > 0
    paths = []
    # ribbed cuff (2 rows)
    cA, cB = W - f_ * 6.5, W - f_ * 0.3
    Xc, Yc, _, fc = view.pa(np.array([cA, (cA + cB) / 2, cB]))
    cuff = _tube(list(zip(Xc.tolist(), Yc.tolist())), [8.6 * fc[0], 8.2 * fc[1], 7.6 * fc[2]], 0.8)
    paths.append((view.depth(W - f_ * 3.0) - 0.5, 'cuff', cuff, None))
    Xp, Yp, zp, fp = view.pa(np.array(h['palm']))
    gc = np.array([float(np.mean(Xp)), float(np.mean(Yp))])
    palm = smooth(_hull([tuple(gc + (np.array(q) - gc) * 1.22) for q in zip(Xp.tolist(), Yp.tolist())]), True, 0.6)
    pz = float(np.mean(zp))
    paths.append((pz, 'palm', palm, None))
    for j, fing in enumerate(list(h['fingers']) + [h['thumb']]):
        X, Y, zd, f = view.pa(np.array(fing))
        p2 = list(zip(X.tolist(), Y.tolist()))
        n = len(p2)
        ws = [(4.4 - 0.5 * k / (n - 1)) * 1.35 * f[k] for k in range(n)]
        tp = _tube(p2, ws, 0.75)
        try: tp = union(tp, oval(p2[-1][0], p2[-1][1], ws[-1] * 0.55, ws[-1] * 0.55))
        except Exception: pass
        paths.append((view.depth(np.mean(fing, 0)) + (0.3 if j == 1 else 0.0), 'thumb' if j == len(h['fingers']) else 'finger', tp, (p2, ws)))
    paths.sort(key=lambda q: q[0])
    # one dark outline round the whole glove (under the fills: only the silhouette edge stays dark)
    for _, kind, pth, _ in paths:
        c.line(pth, lw * 2.0, pal['line'])
    prop = getattr(P, 'hl_prop' if s > 0 else 'hr_prop')
    drew = False
    for z_, kind, pth, extra in paths:
        if prop and not drew and kind != 'cuff' and z_ >= pz - 0.5 and not back:
            _ws_held(c, view, h, P, s, prop, pal, det, t); drew = True
        c.fill(pth, g)
        c.fill(_crescent(pth, 0.9, 0.9), gsh, 190)
        if light and light.get('rim'): c.fill(_crescent(pth, -light.get('side', 1) * 0.8, 0), light['rim'], light.get('rim_a', 60) * 0.6)
        if kind == 'cuff':
            if det >= 1:
                with c.clip(pth):
                    dx, dy = Xc[2] - Xc[0], Yc[2] - Yc[0]; d = math.hypot(dx, dy) or 1.0
                    ux, uy = dx / d, dy / d
                    for k in range(-4, 5):
                        ox, oy = -uy * k * 1.0 * fc[1], ux * k * 1.0 * fc[1]
                        c.line(poly([(Xc[0] + ox, Yc[0] + oy), (Xc[2] + ox, Yc[2] + oy)], False), lw * 0.45, gsh, 230)
                    c.line(poly([(Xc[1] - uy * 6 * fc[1], Yc[1] + ux * 6 * fc[1]), (Xc[1] + uy * 6 * fc[1], Yc[1] - ux * 6 * fc[1])], False), lw * 0.6, gsh, 255)
            c.line(pth, lw * 0.5, gsh, 200)
        elif kind == 'palm':
            if det >= 1:
                with c.clip(pth):      # V-stitch knit texture
                    bb = pth.getBounds()
                    st_ = max(bb.width(), bb.height()) / 7.0
                    for iy in range(9):
                        for ix in range(9):
                            x0 = bb.left() + (ix + 0.5 * (iy % 2)) * st_ * 0.9; y0 = bb.top() + iy * st_ * 0.8
                            c.line(poly([(x0 - st_ * 0.25, y0 - st_ * 0.2), (x0, y0 + st_ * 0.15), (x0 + st_ * 0.25, y0 - st_ * 0.2)], False), lw * 0.35, '#9aa2ae', 60)
                if back:                  # knuckle bumps across the back of the hand
                    for fing in h['fingers']:
                        x_, y_ = view.p2(fing[0]); _, _, _, ff = view.p(fing[0])
                        c.line(smooth([(x_ - 2.2 * ff, y_ + 0.6 * ff), (x_, y_ - 0.9 * ff), (x_ + 2.2 * ff, y_ + 0.6 * ff)], False), lw * 0.6, gsh, 230)
                else:                     # the soft thumb pad
                    tx_, ty_ = view.p2(h['W'] + h['th'] * 2.8 + f_ * 3.5); _, _, _, ff = view.p(h['W'])
                    c.glow(tx_, ty_, 3.2 * ff, 2.4 * ff, gsh, 150)
        else:
            p2, ws = extra
            if det >= 1:
                for k in range(1, len(p2) - 1):          # soft creases at the bends (grey, not dark)
                    dx, dy = p2[k + 1][0] - p2[k - 1][0], p2[k + 1][1] - p2[k - 1][1]; d = math.hypot(dx, dy) or 1.0
                    nx, ny = -dy / d * ws[k] * 0.40, dx / d * ws[k] * 0.40
                    c.line(smooth([(p2[k][0] - nx, p2[k][1] - ny), (p2[k][0] + dx / d * ws[k] * 0.16, p2[k][1] + dy / d * ws[k] * 0.16),
                                   (p2[k][0] + nx, p2[k][1] + ny)], False), lw * 0.55, gsh, 200)
                with c.clip(pth):
                    for k in range(len(p2) - 1):
                        mx, my = (p2[k][0] + p2[k + 1][0]) / 2, (p2[k][1] + p2[k + 1][1]) / 2
                        w_ = ws[k] * 0.22
                        c.line(poly([(mx - w_, my - w_ * 0.6), (mx, my + w_ * 0.4), (mx + w_, my - w_ * 0.6)], False), lw * 0.35, '#9aa2ae', 60)
            c.line(pth, lw * 0.6, gsh, 230)               # finger separation: soft grey, the wool between
    if prop and not drew:
        _ws_held(c, view, h, P, s, prop, pal, det, t)
    return h


def _sh_leg_h(c, view, R, s, det, light):
    """His human legs: charcoal vendor trousers with a pressed front crease, long black shoes (about 30 cm) with a shine."""
    Hp, K, A, fd = R['legs'][s]
    tr, tr_sh = '#3a3540', '#24212a'
    t1, p1 = _ws_tube3(c, view, [Hp, (Hp + K) / 2, K], [15.0, 13.5, 12.0], tr, tr_sh, c.lw, light)
    t2, p2 = _ws_tube3(c, view, [K, (K + A) / 2, A + np.array([0.0, 3.0, 0.0])], [12.0, 11.4, 11.2], tr, tr_sh, c.lw, light)
    if det >= 1:
        for pp, tp in ((p1, t1), (p2, t2)):
            with c.clip(tp):
                c.line(smooth(pp, False), c.lw * 0.6, '#5a5462', 200)          # the pressed crease
    heel = A + np.array([0.0, 7.0, 0.0]) - fd * 5.0
    toe = A + fd * 27.0 + np.array([0.0, 7.5, 0.0])
    top = A + np.array([0.0, 2.5, 0.0]) + fd * 3.0
    X, Y, _, f = view.pa(np.array([heel, top, A + fd * 15.0 + np.array([0.0, 4.0, 0.0]), toe, A + fd * 16.0 + np.array([0.0, 9.0, 0.0])]))
    pts = list(zip(X.tolist(), Y.tolist()))
    if math.hypot(pts[3][0] - pts[0][0], pts[3][1] - pts[0][1]) < 8 * float(f[0]):
        sh = oval((pts[0][0] + pts[3][0]) / 2, (pts[0][1] + pts[3][1]) / 2, 6.5 * f[0], 4.0 * f[0])
    else:
        hull = poly(_hull(pts + [(x_ + 2.6 * f[0], y_) for x_, y_ in pts[:1]]), True)
        sh = _tube([pts[0], pts[2], pts[3]], [8.5 * f[0], 7.8 * f[0], 5.5 * f[0]], 0.9)
        try: sh = union(sh, hull)
        except Exception: pass
    c.fill(sh, '#141216'); c.fill(_crescent(sh, 0, 1.4), '#2c2830', 160)
    bb = sh.getBounds()
    c.glow(bb.centerX() + (pts[3][0] - pts[0][0]) * 0.18, bb.top() + bb.height() * 0.35, bb.width() * 0.16, bb.height() * 0.12, '#ffffff', 90)
    c.line(sh, c.lw, _SH_PAL['line'])


# ---------------------------------------------------------------------------------------------------- spider legs
_SH_LEG_L = (34.0, 255.0, 270.0, 150.0)       # coxa, femur, tibia, tarsus (cm, rig units; the rig is 244 tall): ~2.9x his height
_SH_LEG_ORDER = (1, 0, 3, 2, 5, 4, 7, 6)       # the order they punch out (his right top first)


def _sh_leg_root(R, i):
    s = 1 if i % 2 == 0 else -1
    k = i // 2
    h = 66.0 - 9.0 * k
    q, n = _sh_surf(R, h, s * 0.42, -1.0, False)
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


_SH_LEG_W = ((16.0, 13.0), (13.0, 7.5), (8.5, 4.2), (4.2, 0.35))     # coxa, femur, tibia, tarsus: thick to a needle


def _sh_leg_e(n, j):
    """How far leg j (in _SH_LEG_ORDER) is out when n legs are out: they punch out one PAIR at a time."""
    return clamp((n - 2 * (j // 2)) / 2.0)


def _sh_leg_items(view, R, P, st, det, light, zt):
    """Depth-sorted draw items for the legs: the coxa (always behind the torso: it comes out of the split back) and the
    rest of each leg (femur, tibia, tarsus and their joints) as one item, so the joints overlap in the right order."""
    n = st['legs']
    items = []
    Bx, By = view.p2(R['Ch'])
    for j, i in enumerate(_SH_LEG_ORDER):
        e = _sh_leg_e(n, j)
        if e <= 0.01: continue
        ch = _sh_leg_chain(R, P, i, e)
        zc = min((view.depth(ch[0]) + view.depth(ch[1])) / 2, zt - 3.0)
        items.append((zc + 0.001 * i, lambda cc, ch=ch, i=i: _sh_leg_draw(cc, view, ch, det, light, i, (Bx, By), (0,))))
        zr = (view.depth(ch[1]) + view.depth(ch[2]) + view.depth(ch[3])) / 3
        items.append((zr + 0.001 * i, lambda cc, ch=ch, i=i: _sh_leg_draw(cc, view, ch, det, light, i, (Bx, By), (3, 2, 1))))
    return items


def _sh_seg2d(view, a3, b3, sgi, Bc, wd):
    """The segment in screen space: a bowed spindle centre line (femur bows outward, tibia inward: an organic S) and
    its widths (thickest at 30%)."""
    X, Y, _, f = view.pa(np.array([a3, b3]))
    ax, ay, bx, by = float(X[0]), float(Y[0]), float(X[1]), float(Y[1])
    fa, fb = float(f[0]), float(f[1])
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / L, dx / L
    mx, my = (ax + bx) / 2, (ay + by) / 2
    away = (mx - Bc[0]) * nx + (my - Bc[1]) * ny
    sg = 1.0 if away >= 0 else -1.0
    if sgi == 2: sg = -sg                                   # the tibia bows back in
    bow = 0.0 if sgi in (0, 3) else sg * (0.6 * wd[0] * (fa + fb) / 2 + (0.075 if sgi == 1 else 0.05) * L)
    us = (0.0, 0.3, 0.6, 0.85, 1.0)
    w0, w1 = wd[0] * fa, wd[1] * fb
    pts, ws = [], []
    for u in us:
        b = bow * math.sin(PI * u)
        pts.append((ax + dx * u + nx * b, ay + dy * u + ny * b))
        if u <= 0.3: w = w0 * (1.0 + 0.1 * u / 0.3)
        else: w = w0 * 1.1 + (w1 - w0 * 1.1) * ((u - 0.3) / 0.7) ** 1.15
        ws.append(max(w, 0.05))
    return pts, ws, (nx * sg, ny * sg), L


def _sh_leg_draw(c, view, ch, det, light, i, Bc, segs):
    """One spider leg: dark-brown chitin spindles with lit and shadow edges, telescoping rings, bristles on the outer
    edge, dark ball joints under flared segment ends, frost rime crusted on the top of every joint (icicles hanging),
    and a needle tip that fades from dark to pale."""
    pal = _SH_PAL
    lw = c.lw
    side = (light or {}).get('side', 1)
    px = 1.0 / max(getattr(c, 's', 1.0), 1e-6)            # one screen pixel in these units
    joints = []
    for sgi in segs:                                       # drawn distal first: each proximal end flares over its joint
        a3, b3 = ch[sgi], ch[sgi + 1]
        wd = _SH_LEG_W[sgi]
        pts, ws, (ox, oy), L = _sh_seg2d(view, a3, b3, sgi, Bc, wd)
        _, _, _, fa = view.p(a3)
        if sgi == 3:
            # tarsus: half brown chitin, half a pale needle (dark into pale)
            mid = len(pts) // 2
            q = (pts[0][0] + (pts[-1][0] - pts[0][0]) * 0.5, pts[0][1] + (pts[-1][1] - pts[0][1]) * 0.5)
            wq = ws[0] * 0.55
            tp = _tube([pts[0], ((pts[0][0] + q[0]) / 2, (pts[0][1] + q[1]) / 2), q], [ws[0], ws[0] * 0.78, wq], 0.8)
            c.fill(tp, pal['leg'])
            c.fill(_crescent(tp, side * 0.2 * ws[0], 0.25 * ws[0]), pal['leg_dk'], 170)
            if light and light.get('rim'): c.fill(_crescent(tp, -side * 0.3 * ws[0], 0.0), light['rim'], int(light.get('rim_a', 60) * 1.3))
            c.line(tp, lw * 0.8, pal['line'])
            nd = _tube([q, ((q[0] + pts[-1][0]) / 2, (q[1] + pts[-1][1]) / 2), pts[-1]], [wq, wq * 0.45, max(ws[-1], 0.05)], 0.8)
            c.grad(nd, q[0], q[1], pts[-1][0], pts[-1][1], [(0, pal['leg_dk'], 255), (0.45, '#9a8f86', 255), (1, pal['tip'], 255)])
            c.line(nd, lw * 0.6, pal['line'], 220)
            continue
        tp = _tube(pts, ws, 0.85)
        c.fill(tp, pal['leg'])
        with c.clip(tp):
            c.fill(_crescent(tp, side * 0.22 * ws[1], 0.30 * ws[1]), pal['leg_hi'], 160)       # the lit edge
            c.fill(_crescent(tp, -side * 0.20 * ws[1], -0.26 * ws[1]), pal['leg_dk'], 170)     # the shadow edge
            if light and light.get('rim'):                                                      # moon / window rim: reads on the night
                c.fill(_crescent(tp, -side * 0.30 * ws[1], 0.0), light['rim'], int(light.get('rim_a', 60) * 1.3))
            if det >= 1:
                dx, dy = pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1]
                Ld = math.hypot(dx, dy) or 1.0
                tx, ty = dx / Ld, dy / Ld
                for u in (0.88, 0.96):                    # telescoping rings near the far end
                    k = int(u * (len(pts) - 1)); fr = u * (len(pts) - 1) - k
                    k = min(k, len(pts) - 2)
                    cx_ = pts[k][0] + (pts[k + 1][0] - pts[k][0]) * fr; cy_ = pts[k][1] + (pts[k + 1][1] - pts[k][1]) * fr
                    w_ = ws[k] + (ws[k + 1] - ws[k]) * fr
                    c.line(smooth([(cx_ - ty * w_ * 0.6 - tx * w_ * 0.08, cy_ + tx * w_ * 0.6 - ty * w_ * 0.08), (cx_ + tx * w_ * 0.12, cy_ + ty * w_ * 0.12),
                                   (cx_ + ty * w_ * 0.6 - tx * w_ * 0.08, cy_ - tx * w_ * 0.6 - ty * w_ * 0.08)], False), lw * 0.55, pal['leg_dk'], 230)
        c.line(tp, lw * (0.9 if sgi < 2 else 0.65), pal['line'])
        if det >= 1:                                       # short dark bristles along the outer edge, raked toward the tip
            nb = 6 + int(4 * hash01(i * 5 + sgi, 3511))
            dx, dy = pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1]
            Ld = math.hypot(dx, dy) or 1.0
            tx, ty = dx / Ld, dy / Ld
            ca, sa = math.cos(0.52), math.sin(0.52)
            for k in range(nb):
                u = 0.12 + 0.76 * (k + 0.5 * hash01(i * 13 + sgi * 7 + k, 3512)) / nb
                kk = min(int(u * (len(pts) - 1)), len(pts) - 2); fr = u * (len(pts) - 1) - kk
                bx_ = pts[kk][0] + (pts[kk + 1][0] - pts[kk][0]) * fr; by_ = pts[kk][1] + (pts[kk + 1][1] - pts[kk][1]) * fr
                w_ = (ws[kk] + (ws[kk + 1] - ws[kk]) * fr) * 0.5
                sx_, sy_ = bx_ + ox * w_ * 0.9, by_ + oy * w_ * 0.9
                ln = w_ * (0.55 + 0.4 * hash01(i * 3 + k, 3513)) + 2.0 * px
                vx, vy = ox * sa + tx * ca, oy * sa + ty * ca
                c.line(poly([(sx_, sy_), (sx_ + vx * ln, sy_ + vy * ln)], False), max(lw * 0.45, 0.8 * px), pal['leg_dk'], 230)
        # the flared end cap over the joint at this segment's far end (the next segment's ball sits under it)
        if 0 < sgi < 3:
            ex, ey = pts[-1]
            rr = ws[-1] * 0.5 * 1.15
            cap = oval(ex, ey, rr, rr)
            c.fill(cap, pal['leg']); c.fill(_crescent(cap, -side * rr * 0.35, -rr * 0.3), pal['leg_dk'], 150)
            c.line(cap, lw * 0.8, pal['line'])
            joints.append((ex, ey, wd[1], sgi + 1))
        # the dark ball joint at the start of this segment, under the previous segment's flare
        if sgi >= 1:
            X, Y = view.p2(a3)
            rb = (0.30 if sgi == 1 else 0.42) * wd[0] * fa
            ball = oval(X, Y, rb, rb)
            c.fill(ball, pal['leg_dk']); c.line(ball, lw * 0.7, pal['line'])
    if 0 in segs:
        Xr, Yr, _, fr_ = view.p(ch[0])
        Xq, Yq = view.p2(ch[1])
        ang0 = math.atan2(Yq - Yr, Xq - Xr)
        for k in range(4):
            a_ = ang0 + (k - 1.5) * 0.85 + (hash01(i * 7 + k, 3531) - 0.5) * 0.4
            ln = (8.0 + 6.0 * hash01(i * 5 + k, 3532)) * fr_
            wb = (3.0 + 1.5 * hash01(i + k, 3533)) * fr_
            px_, py_ = -math.sin(a_), math.cos(a_)
            bx_, by_ = Xr + math.cos(a_) * 5.0 * fr_, Yr + math.sin(a_) * 5.0 * fr_
            tipx, tipy = bx_ + math.cos(a_) * ln, by_ + math.sin(a_) * ln
            jag = [(bx_ - px_ * wb, by_ - py_ * wb), (bx_ + math.cos(a_) * ln * 0.55 - px_ * wb * 0.9, by_ + math.sin(a_) * ln * 0.55 - py_ * wb * 0.9),
                   (tipx - px_ * wb * 0.3, tipy - py_ * wb * 0.3), (bx_ + math.cos(a_) * ln * 0.75 + px_ * wb * 0.1, by_ + math.sin(a_) * ln * 0.75 + py_ * wb * 0.1),
                   (tipx + px_ * wb * 0.5, tipy + py_ * wb * 0.5), (bx_ + px_ * wb, by_ + py_ * wb)]
            fl = poly(jag, True)
            c.fill(fl, _SH_PAL['pink'] if k % 2 == 0 else _SH_PAL['white'])
            c.fill(_crescent(fl, 0, -wb * 0.3), _SH_PAL['pink_sh'], 140)
            c.line(fl, lw * 0.7, pal['line'])
    if det >= 1:
        for ex, ey, w_cm, jn in joints:
            _sh_rime(c, ex, ey, w_cm * view.p(ch[jn])[3] * 0.62, i * 11 + jn, px, lw)


def _sh_rime(c, X, Y, r, seed, px, lw):
    """Frost rime crusted on the top half of a joint: an irregular crust of small blobs, a soft cold glow, and two or
    three tiny icicles hanging from its lower edge."""
    pal = _SH_PAL
    c.glow(X, Y - r * 0.2, r * 1.6, r * 1.3, '#e8f4ff', 40)
    crust = None
    nbl = 5 + int(4 * hash01(seed, 3521))
    for k in range(nbl):
        a_ = PI + PI * (k + 0.5) / nbl + (hash01(seed * 7 + k, 3522) - 0.5) * 0.4      # over the top half
        rr = r * (0.30 + 0.22 * hash01(seed * 5 + k, 3523))
        b = oval(X + math.cos(a_) * r * 0.78, Y + math.sin(a_) * r * 0.70 - r * 0.08, rr, rr * 0.85)
        crust = b if crust is None else union(crust, b)
    cap = oval(X, Y - r * 0.35, r * 0.75, r * 0.45)
    crust = union(crust, cap)
    c.fill(crust, pal['rime'], 230)
    c.fill(_crescent(crust, 0, -r * 0.18), '#9fb4c8', 150)
    c.line(crust, max(lw * 0.45, 0.7 * px), '#7f93a8', 200)
    for k in range(2 + int(hash01(seed, 3524) * 2)):
        u = (k + 0.5) / 3.0 - 0.5
        x0 = X + u * r * 1.3
        y0 = Y - r * 0.05 + abs(u) * r * 0.35
        ln = max(r * (0.35 + 0.35 * hash01(seed * 3 + k, 3525)), 2.0 * px)
        ln = min(ln, 4.0 * px) if r < 8 * px else ln
        w_ = max(ln * 0.32, 0.9 * px)
        ic = poly([(x0 - w_, y0), (x0 + w_, y0), (x0 + 0.1 * w_, y0 + ln)], True)
        c.fill(ic, '#eef6ff', 240); c.line(ic, max(lw * 0.3, 0.5 * px), '#7f93a8', 180)


# ---------------------------------------------------------------------------------------------------- the figure
def _sh_rig(P, st):
    if P.sh_lift > 1.0:     # slung in the cage of legs: knees folded up, the body pitched forward, the head hanging
        k = clamp(P.sh_lift / 80.0)
        P = P.copy(); P.ws_crouch = max(P.ws_crouch, 1.25 * k); P.ws_bend = max(P.ws_bend, 0.38 * k)
        P.ws_face_up = min(P.ws_face_up, 0.75 - 0.45 * k)
        P.h_nod = P.h_nod + float(P.sh_hang) * k      # the long pale head hangs down (the bible's read test)
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
        ch = _sh_leg_chain(R, P, i, _sh_leg_e(n, j) if n > j else 1.0)
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

# ---------------------------------------------------------------------------------------------- one boot, one sock
# adam_sock after 6:45: the LEFT boot still on, the RIGHT foot in a grey sock caked with snow (feet_lr: side -> kind).
_draw_legs3_ice_prev = _draw_legs3


def _draw_legs3(c, sp, B, P, det, t, legc, legsh, shoec, order_only=False):
    lr = sp.get('feet_lr')
    if not lr:
        return _draw_legs3_ice_prev(c, sp, B, P, det, t, legc, legsh, shoec, order_only)
    b = sp['body']
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
        kind = lr.get(side, sp.get('feet', 'shoes'))
        P2 = [(hp[0], hp[1]), (kp[0], kp[1]), (ap[0], ap[1])]
        widths = [lw0 * hp[2], (lw0 + lw1) / 2 * kp[2], lw1 * ap[2]]
        tp = _tube(P2, widths)
        pts = []
        cp, spp = math.cos(pitch), math.sin(pitch)
        for (fx, fy, fz) in _foot_box(kind):
            yy = fy * cp - fz * spp; zz = fz * cp + fy * spp
            X, Y, s_, Z = B.p3(A[0] + fx, A[1] + 38.0 + yy - B.bob, A[2] + zz, upper=False)
            pts.append((X, Y))
        foot = smooth(_hull(pts), True, 0.6)
        foot_back = (B.ct * math.cos(pitch) < -0.1)
        if foot_back: _foot_fill(c, sp, kind, foot, cl, det, P, B, side)
        c.fill(tp, legc); _cloth_shade(c, tp, legsh, 160, 1.0, 10)
        if det >= 1 and sp.get('legs_tex', True): c.texture(tp, 'fabric', 0.08, 0.6)
        _leg_extra(c, sp, P2, widths, det, side, B)
        c.line(tp, c.lw)
        if not foot_back: _foot_fill(c, sp, kind, foot, cl, det, P, B, side)


_foot_fill_ice_prev = _foot_fill


def _foot_fill(c, sp, kind, foot, cl, det, P, B, side):
    _foot_fill_ice_prev(c, sp, kind, foot, cl, det, P, B, side)
    if kind == 'socks' and cl.get('sock_snow') and det >= 1:      # wet wool caked with snow clumps
        bb = foot.getBounds()
        with c.clip(foot):
            for k in range(6):
                x_ = bb.left() + bb.width() * (0.12 + 0.76 * hash01(k, 3801)); y_ = bb.top() + bb.height() * (0.35 + 0.6 * hash01(k, 3802))
                r_ = bb.height() * (0.10 + 0.08 * hash01(k, 3803))
                c.fill(oval(x_, y_, r_ * 1.3, r_), '#ffffff', 235); c.fill(oval(x_ + r_ * 0.3, y_ + r_ * 0.3, r_ * 0.8, r_ * 0.5), '#c9d6ea', 200)
            c.fill(rect(bb.left() - 4, bb.bottom() - bb.height() * 0.22, bb.width() + 8, bb.height()), '#9aa6b8', 120)   # soaked sole
        c.line(foot, c.lw)


CAST['adam_sock'] = _v3cast(outfit='raincoat_kid', feet='boots', **_ADAM,
                            cloth=dict(_ADAM_CLOTH, socks='#d8d8e0', socks_sh='#9fa3b0', sock_toe=None, sock_snow=True))
CAST['adam_sock']['feet_lr'] = {1: 'boots', -1: 'socks'}


# ---------------------------------------------------------------------------------------------- carrying Lina
def _ice_carry(self, t0, child, t1=None, fade=0.5, face_lens=0.55):
    """Carry a small child on the hip and chest (Adam with Lina): her seat on his near forearm, her thighs round his
    waist with the knees bent, her arms locked round his neck, her cheek on his shoulder and her face turned to the lens;
    his near arm under her seat, his far arm across her back. Draw with draw_carry_child (it places her)."""
    self._carry = child
    child._carried_by = self
    near = lambda t: (1 if math.sin(self._raw(t, False).turn * PI / 2) <= 0 else -1)
    s_near = near(t0 + 0.01)
    self.reach_to(t0, s_near, (child, 'hip'), t1=t1, dur=fade, z=30.0, contact='palm', shape='grip', fade=fade, lean=False)
    self.reach_to(t0, -s_near, (child, 'chest'), t1=t1, dur=fade, z=-6.0, contact='palm', shape='open', fade=fade, lean=False)

    def fn(P, t):
        w = _env(t, t0, t1, fade, fade)
        if w <= 0: return
        Pc = self._raw(t, False)
        P.turn = lerp(P.turn, -Pc.turn, w)                     # chest to chest
        P.sit = max(P.sit, 0.95 * w); P.seat = max(getattr(P, 'seat', 0.0) or 0.0, 1.0 * w); P.crouch = 0.0
        P.h_turn += face_lens * (1 if Pc.turn > 0 else -1) * w   # her face turned out to the lens, cheek on his shoulder
        P.h_tilt += 12.0 * w; P.h_nod += 0.10 * w
        for side in (-1, 1): child._arm(P, side, w, 30.0, 40.0, 170.0, 'fist', up=0.0)
    child._add(t0, None if t1 is None else t1 + fade, fn)
    for side in (-1, 1):                                      # arms locked round his neck
        child.reach_to(t0, side, (self, 'neck'), t1=t1, dur=fade, z=(-8.0 if side == s_near else 8.0), contact='palm', shape='grip',
                       fade=fade, lean=False)
    return self


Acting.carry = _ice_carry


def carry_anchor(carrier, t):
    """Design point where a carried child's hips sit: on the carrier's forearm at the hip, against the front of the body."""
    bx, by = carrier.where(t, 'belly', post=False)
    hx, hy = carrier.where(t, 'hip', post=False)
    P = carrier._raw(t, False)
    face = math.sin(P.turn * PI / 2)
    s = carrier.height / 1000.0
    return bx + face * 92.0 * s, (by + hy) / 2 + 95.0 * s


def draw_carry_child(pen, carrier, child, t, light=None, clight=None):
    """Draw a child carried on the hip (carrier.carry(t0, child)): the carrier with its far arm, the child placed at
    carry_anchor (her hips on his forearm), then the carrier's near arm over her seat."""
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


def draw_breath(pen, actor, t, period=1.1, k=1.0, c='#ffffff', phase=0.0):
    """A white breath puff from the mouth in the cold (people only: never Mister Shiver), one per `period` s, drifting
    up and forward and fading. k: size (1 = a calm breath; 1.5 = panting)."""
    if CAST[actor.who].get('shiver') or CAST[actor.who].get('breath', 1.0) <= 0: return
    mx, my = actor.where(t, 'mouth')
    P = actor._raw(t, False)
    face = math.sin(P.turn * PI / 2) or 0.3
    s = actor.height / 1000.0
    for n in range(2):
        u = ((t + phase) / period - n) % 1.0 if n == 0 else ((t + phase) / period + 0.5) % 1.0
        if n == 1 and k < 1.3: continue
        a = int(150 * (1.0 - u) ** 1.5 * min(1.0, u * 8.0))
        if a <= 2: continue
        x = mx + face * (30.0 + 90.0 * u) * s * k; y = my - 25.0 * u * s
        r = (14.0 + 40.0 * u) * s * k
        pen.glow(x, y, r, c, a)


# ---------------------------------------------------------------------------------------------- the kids' coats
# Lina's puffy yellow coat hangs OPEN over her pink snowflake pyjamas; Adam's navy coat is quilted in puffy baffles.
_front_coat_small_ice_prev = _FRONTS3['coat_small']
_front_raincoat_kid_ice_prev = _FRONTS3['raincoat_kid']


def _ice_snowflake(c, X, Y, r, colr, a=255):
    for k in range(3):
        a_ = PI / 2 + k * PI / 3
        dx, dy = math.cos(a_) * r, math.sin(a_) * r
        c.line(poly([(X - dx, Y - dy), (X + dx, Y + dy)], False), max(r * 0.28, 0.6), colr, a)


def _front_coat_open(c, sp, B, rows, P, det, t):
    if not sp.get('open_coat'):
        return _front_coat_small_ice_prev(c, sp, B, rows, P, det, t)
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yH = B.y_sh, B.y_hip
    gap, v = _surf_poly(B, rows, [(-15, yS + 2), (15, yS + 2), (34, yH + 4), (-34, yH + 4)], dz=2)
    if v > -0.2:
        gp = smooth(gap, True, 0.35)
        c.fill(gp, cl.get('pj', '#f2a8c4')); c.fill(_crescent(gp, 0, -5), cl.get('pj_sh', '#c97898'), 120)
        if det >= 1:
            for k, (xx, yy) in enumerate(((-6, 0.30), (8, 0.52), (-10, 0.74), (4, 0.92))):
                X, Y, vv, s_ = B.surf(xx, yS + (yH - yS) * yy, 3, False, rows)
                if vv > 0.1: _ice_snowflake(c, X, Y, 9.0 * s_, '#ffffff', 250)
        c.line(gp, lw * 0.9)
        for sd in (-1, 1):                         # the coat's open front edges: thick, padded
            ed, v2 = _surf_poly(B, rows, [(sd * 15, yS + 2), (sd * 34, yH + 4)], dz=5)
            if v2 > -0.2: c.line(poly(ed, False), lw * 2.2, cl.get('top_sh', '#c99a24'), 200)
    for sd in (-1, 1):                             # collar
        cc, v3 = _surf_poly(B, rows, [(sd * 2, yS - 24), (sd * (b['neck'] + 8), yS - 30), (sd * (b['neck'] + 20), yS - 6), (sd * 22, yS + 18), (sd * 9, yS + 6)], dz=6)
        if v3 > -0.2: cp = smooth(cc, True, 0.8); c.fill(cp, cl['collar']); c.line(cp, lw * 0.6)
    if det >= 1:                                   # puffy baffles across each front panel
        for k in range(1, 4):
            yy = yS + k * (yH - yS) / 4.0
            for sd in (-1, 1):
                x0 = 11 + 14 * k / 4.0
                pts, v4 = _surf_poly(B, rows, [(sd * x0, yy), (sd * (x0 + 20), yy + 3), (sd * (b['ch'] * 0.95), yy)], dz=4)
                if v4 > -0.2: c.line(smooth(pts, False), lw * 0.8, cl.get('top_sh', '#c99a24'), 210)


def _front_raincoat_quilt(c, sp, B, rows, P, det, t):
    _front_raincoat_kid_ice_prev(c, sp, B, rows, P, det, t)
    if sp.get('quilt') and det >= 1:              # three horizontal quilting baffles on the puffy navy coat
        cl = sp['cloth']; b = sp['body']
        yS, yH = B.y_sh, B.y_hip
        for k in range(1, 4):
            yy = yS + 18 + k * (yH - yS - 18) / 4.0
            pts, v = _surf_poly(B, rows, [(-b['ch'] * 0.98, yy), (-b['ch'] * 0.5, yy + 4), (0, yy + 5), (b['ch'] * 0.5, yy + 4), (b['ch'] * 0.98, yy)], dz=4)
            if v > -0.2:
                c.line(smooth(pts, False), c.lw * 1.0, cl.get('top_sh', '#16244a'), 230)
                c.line(smooth([(x_, y_ - 4.0) for x_, y_ in pts], False), c.lw * 1.4, cl.get('top_hi', '#3c5590'), 90)


_FRONTS3['coat_small'] = _front_coat_open
_FRONTS3['raincoat_kid'] = _front_raincoat_quilt
for _w in ('adam', 'adam_sock', 'walter58'):
    CAST[_w]['quilt'] = True
CAST['lina']['open_coat'] = True
CAST['lina']['cloth'].update(pj='#f2a8c4', pj_sh='#c97898')
CAST['lina'].update(eye_r=CAST['lina']['eye_r'] * 1.10, eye_y=CAST['lina'].get('eye_y', 0) + 5)
CAST['lina_pj'].update(eye_r=CAST['lina_pj']['eye_r'] * 1.10, eye_y=CAST['lina_pj'].get('eye_y', 0) + 5)
# Mr. Kessler: the large ears (the bible); out in the snow with no coat: the blue-grey skin of severe cold
for _w in ('kessler', 'kessler_out', 'kessler_am'):
    CAST[_w]['ears'] = 1.6
CAST['kessler_out'].update(skin=mix(CAST['kessler_out']['skin'], '#B9C3CF', 0.38), skin_sh=mix(CAST['kessler_out'].get('skin_sh', '#a88a7c'), '#8593a6', 0.4),
                           blush=mix(CAST['kessler_out'].get('blush', '#d98d80'), '#B9C3CF', 0.6))
# Dad: heavier stubble
CAST['dad']['stub'] = 0.85


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
    for p_ in range(4):                     # one pair per click ("Click. Another. Click. Click.")
        tc = t_at(a + (b - a) * (2 * p_ + 2) / 8.0)
        evs.append(self._ev(tc, 'leg_click', -2.0 + (2.0 if p_ < 2 else 0.0), leg=_SH_LEG_ORDER[2 * p_]))
        evs.append(self._ev(tc + 0.06, 'leg_click', -6.0, leg=_SH_LEG_ORDER[2 * p_ + 1]))
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


def _sh_scuttle(self, t0, t1, path, ground=None, stride=None, swing=0.42, lift=60.0, ease=0.25, spread=1.6, pitch=12.0):
    """He scuttles like a harvestman: a wide arch of legs (sh_spread `spread`) with the small body slung low under it,
    pitched forward along the path, the long head hanging down. path(u) -> world (x, y) of his feet origin for u 0..1
    (eased in/out); ground(x) -> world y of the surface under a tip (a fence top rail, a car roof, a roof slope; default:
    the path's y): every tip is planted ON it. Alternating tetrapod gait (legs 0,3,4,7 against 1,2,5,6); a 'leg_click'
    for every tip that lands (pan follows)."""
    grp = {i: (0.0 if i in (0, 3, 4, 7) else 0.5) for i in range(8)}
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
        (bx2, by2), _ = body_xy(min(t + 0.05, t1 + 0.05))
        P.dx += bx - self.x0; P.dy += by - self.y0
        P.sh_lift = max(P.sh_lift, lift)
        P.sh_spread = spread
        P.sh_hang = max(P.sh_hang, 0.95)                      # the long pale head hanging down
        dirx = 1.0 if bx2 >= bx else -1.0
        slope = math.degrees(math.atan2(by2 - by, abs(bx2 - bx) + 1e-6)) if abs(bx2 - bx) > 0.5 else 0.0
        P.ws_bend = max(P.ws_bend, pitch / 40.0)              # the body pitched down under the arch (no 2D tilt: tips stay planted)
        view = _WSView(P)
        R = _sh_rig(P, _sh_state(P))
        sc = self.height / 1000.0 * _WSU * max(P.ws_scale, 1e-3)
        xb = bx - self.x0
        for i in range(8):
            rc = _sh_leg_rest(R, P, i)
            rx_, ry_ = view.p2(rc)
            ox = rx_ * sc
            ph = grp[i] * S_
            n = math.floor((xb * dirx + ph) / S_)
            fr = (xb * dirx + ph) / S_ - n
            spot0 = (n * S_ - ph) * dirx; spot1 = spot0 + S_ * dirx
            sw = clamp((fr - (1 - swing)) / swing)
            tipx = self.x0 + ox + spot0 + (spot1 - spot0) * ease_in_out(sw)
            gy = ground(tipx) if ground is not None else by
            q = _sh_world_cm(self, P, tipx, gy, rc[2])
            setattr(P, 'sh_t%dw' % i, 1.0); setattr(P, 'sh_t%dx' % i, q[0]); setattr(P, 'sh_t%dy' % i, q[1]); setattr(P, 'sh_t%dz' % i, q[2])
            setattr(P, 'sh_t%dlift' % i, 55.0 * math.sin(PI * sw))
    self._add(t0, None, fn)
    # a click for every landing: sample the body path, count stride crossings per group
    evs = []
    last = {}
    k = 0
    for m in range(int(dur * 120) + 1):
        t = t0 + m / 120.0
        (bx, by), _ = body_xy(t)
        (bx2, _), _ = body_xy(min(t + 0.05, t1 + 0.05))
        dirx = 1.0 if bx2 >= bx else -1.0
        xb = (bx - self.x0) * dirx
        for gph in (0.0, 0.5):
            n = math.floor((xb + gph * S_) / S_)
            if gph in last and n != last[gph]:
                for j, i in enumerate([i_ for i_ in range(8) if grp[i_] == gph]):
                    evs.append(self._ev(t + 0.025 * j, 'leg_click', -4.0 - 3.0 * hash01(k + j, 3702), leg=i))
                k += 4
            last[gph] = n
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


def _sh_pour_out(self, t0, dur=2.4, sill_dy=-300.0, ground_dy=0.0, forward=1.0, lift=110.0, roof_dy=None, frame_w=None, ground=None):
    """He pours out of the serving window HEAD FIRST, LEGS LAST, always held by his spider legs (never floating):
      0.00-0.30  four legs already grip the roof edge and the window frame; he rises to the sill and curls over it neck
                 first (ws_bend 0 -> 1.25), the long head hanging toward the snow; both gloves reach down and plant in
                 the snow below the window;
      0.30-0.62  the roof legs haul his hips up and out over the sill (the human legs fold under, coming out last);
      0.62-1.00  the other four legs unfold out of the window one by one and step over the roof edge to the snow, the
                 roof legs step down after them, and he is lowered into the cage of legs on the snow (lift cm).
    sill_dy: px from his feet origin up to the sill; ground_dy: px from the origin down to the snow; roof_dy: px from the
    origin up to the roof edge (default sill_dy - 1.4 m); frame_w: window width px (default 1.25 m); ground(x) -> snow y
    (tips are clamped to it). Draw him in two passes (see CAST.md): through the window hole, then in front of the wall;
    sh_nolegs is set here (human legs hidden until the hips are over the sill)."""
    ppm = self.height / _SH_M
    roof_dy = (sill_dy - 1.4 * ppm) if roof_dy is None else roof_dy
    fw = (1.25 * ppm) if frame_w is None else frame_w
    hip_px = 0.50 * self.height
    rise = min(0.0, sill_dy + hip_px - 0.06 * ppm)                       # the origin up so the hips reach the sill
    x0, y0 = self.x0, self.y0
    gy = (lambda x: y0 + ground_dy) if ground is None else ground
    plant = {0: (x0 + 0.95 * fw, y0 + roof_dy), 1: (x0 - 0.95 * fw, y0 + roof_dy),
             2: (x0 + 0.52 * fw, y0 + sill_dy - 0.95 * ppm), 3: (x0 - 0.52 * fw, y0 + sill_dy - 0.95 * ppm)}

    def fn(P, t):
        u = prog(t, t0, t0 + dur) if t >= t0 else 0.0
        a = ease_in_out(prog(u, 0.0, 0.30))
        b = ease_in_out(prog(u, 0.30, 0.62))
        c = ease_in_out(prog(u, 0.62, 1.00))
        P.sh_legs = 8.0
        P.sh_legcap = 4.0 + 4.0 * prog(u, 0.62, 0.92)                    # the last four unfold out of the window
        P.sh_nolegs = 0.0 if b > 0.55 else 1.0
        P.ws_bend = max(P.ws_bend, 1.25 * ease_in_out(prog(u, 0.08, 0.30)) * (1.0 - c) + 0.38 * c)
        P.__dict__['_sh_pour_u'] = u                                      # for the set's mask (hips behind the wall: u < 0.1)
        P.ws_face_up = min(P.ws_face_up, 0.75 - 0.6 * a * (1.0 - c))      # neck first: the head hangs toward the snow
        P.h_nod += 0.35 * a * (1.0 - c)
        P.dy += rise * ease_in_out(prog(u, 0.0, 0.12)) * (1.0 - c) + ground_dy * c
        P.dx += forward * self.height * (0.10 * b + 0.22 * c)
        P.sh_lift = max(P.sh_lift, 55.0 * b * (1.0 - c) + lift * c)
        # the four gripping legs: on the roof edge and the window frame, then (0.70-0.95) each steps down to the snow
        for k, (i, (tx, ty)) in enumerate(sorted(plant.items())):
            s0 = 0.70 + 0.06 * k
            w = 1.0 - ease_in_out(prog(u, s0, s0 + 0.12))
            q = _sh_world_cm(self, P, tx, min(ty, gy(tx)), 40.0)
            setattr(P, 'sh_t%dw' % i, w); setattr(P, 'sh_t%dx' % i, q[0]); setattr(P, 'sh_t%dy' % i, q[1]); setattr(P, 'sh_t%dz' % i, q[2])
            setattr(P, 'sh_t%dlift' % i, 60.0 * math.sin(PI * prog(u, s0, s0 + 0.12)))
    self._add(-INF, None, fn)
    # the gloves go down first and plant in the snow below the window, released as the legs take him
    for side, dxk in ((1, 0.22), (-1, -0.22)):
        self.reach_far(t0 + dur * 0.06, side, (x0 + dxk * fw, gy(x0 + dxk * fw) - 0.02 * ppm), t1=t0 + dur * 0.66,
                       dur=dur * 0.24, z=55.0, shape='flat')
    evs = [self._ev(t0, 'sh_pour', 0.0), self._ev(t0 + dur * 0.30, 'glove_snow', -6.0)]
    evs += [self._ev(t0 + dur * (0.62 + 0.30 * k / 4.0), 'leg_click', -2.0, leg=_SH_LEG_ORDER[4 + k]) for k in range(4)]
    evs += [self._ev(t0 + dur * (0.82 + 0.06 * k), 'leg_click', -3.0, leg=k) for k in range(4)]
    return evs


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
