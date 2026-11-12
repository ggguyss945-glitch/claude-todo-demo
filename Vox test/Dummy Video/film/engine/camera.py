"""engine.camera: keyframed 2.5D camera with eases, handheld noise, hits and punch-ins.

Cam(keys, ease='in_out', shake=0.0, shake_hz=0.6, seed=0, roll_shake=0.0)
    keys: [(t, x, y, zoom), (t, x, y, zoom, roll), (t, x, y, zoom, roll, ease)] or dicts {t, x, y, zoom, roll, ease}.
      x, y  = design point (on the depth-1 plane) at the frame centre; (960, 540) is the home framing.
      zoom  = magnification of the depth-1 plane, realised as a DOLLY (near layers grow faster: real parallax).
      roll  = degrees (applied to the final image, like rolling a real camera; auto-zooms to hide corners).
      ease  = ease of the segment ARRIVING at this key (core.EASES name or function); default `ease`.
    Zoom is interpolated geometrically. Before the first key / after the last key the camera holds.
    shake: handheld amplitude in design px (3 = gentle, 8 = nervous); shake_hz: its speed; roll_shake: degrees.
  Chainable extras (return self):
    .hit(t, amp=8, dur=0.35, hz=13)        impact shake (knocks, slams)
    .snap(t, factor=1.25, dur=0.1, until=None, back=0.15)   punch-in: optical zoom (no parallax) with a slight overshoot
    .post_push(t0, t1, z0=1.0, z1=1.06, ease='push', x=0, y=0)  zoom into the FINISHED image (after the lens): a push into
        doorbell footage keeps the fisheye geometry attached to the picture
    .focus_pull(...) is not here: pass focus to scene.render_frame.
  cam.at(t) -> CamState(x, y, zoom, roll, fz, pz, px, py, vx, vy)
    fz = optical zoom (pre-lens, all depths alike); pz/px/py = post-lens zoom and offset (design px);
    vx, vy = screen velocity of depth-1 content (design px/s) used for automatic motion blur on whips.

Shot helpers (all return a Cam; every one accepts shake=, seed=):
    hold(x, y, zoom, roll)                                  static (add shake for life)
    push_in(t0, t1, x, y, z0=1.0, z1=None, rate=0.025)      default 2.5 %/s, reference ease (moving at the cut, slight ease-out)
    pull_out(t0, t1, x, y, z0=1.12, z1=1.0)                 fast reveal
    drift(t0, t1, x0, y0, x1, y1, zoom=1.04)                lateral float
    pan(t0, t1, x0, x1, y=540, zoom=1.0)                    eased pan
    whip(t, x0, x1, y=540, zoom=1.0, dur=0.22)              fast whip pan centred on t (motion-blurred by the renderer)
    snap_zoom(t, x, y, z0=1.0, factor=1.3, dur=0.1)         punch-in at t
    handheld(cam=None, amount=3.0, hz=0.6, roll=0.0)        add handheld noise to a cam (roll>0 costs one extra warp per frame)
"""
import math
from .core import ease_fn, noise1, lerp, clamp, ease_out_back, ease_push, ease_out_cubic, ease_in_out, DW, DH


class CamState:
    __slots__ = ('x', 'y', 'zoom', 'roll', 'fz', 'pz', 'px', 'py', 'vx', 'vy')

    def __init__(self, x=DW / 2, y=DH / 2, zoom=1.0, roll=0.0, fz=1.0, pz=1.0, px=0.0, py=0.0, vx=0.0, vy=0.0):
        self.x, self.y, self.zoom, self.roll, self.fz, self.pz, self.px, self.py, self.vx, self.vy = x, y, zoom, roll, fz, pz, px, py, vx, vy

    def __repr__(self):
        return 'CamState(x=%.1f y=%.1f zoom=%.4f roll=%.2f fz=%.3f pz=%.3f v=(%.0f,%.0f))' % (
            self.x, self.y, self.zoom, self.roll, self.fz, self.pz, self.vx, self.vy)


HOME = CamState()


def _key(k):
    if isinstance(k, dict):
        return (float(k['t']), float(k.get('x', DW / 2)), float(k.get('y', DH / 2)), float(k.get('zoom', 1.0)),
                float(k.get('roll', 0.0)), k.get('ease'))
    k = tuple(k)
    return (float(k[0]), float(k[1]), float(k[2]), float(k[3]) if len(k) > 3 else 1.0,
            float(k[4]) if len(k) > 4 else 0.0, k[5] if len(k) > 5 else None)


class Cam:
    def __init__(self, keys=None, ease='in_out', shake=0.0, shake_hz=0.6, seed=0, roll_shake=0.0):
        keys = keys or [(0.0, DW / 2, DH / 2, 1.0)]
        self.keys = sorted((_key(k) for k in keys), key=lambda k: k[0])
        self.ease = ease
        self.shake, self.shake_hz, self.seed, self.roll_shake = shake, shake_hz, seed, roll_shake
        self.hits, self.snaps, self.posts = [], [], []
        self.snap_back = True            # snap(): overshooting punch-in; False = a plain eased push over `dur`

    # ---- chainable extras
    def hit(self, t, amp=8.0, dur=0.35, hz=13.0):
        self.hits.append((t, amp, dur, hz)); return self

    def snap(self, t, factor=1.25, dur=0.1, until=None, back=0.15):
        self.snaps.append((t, factor, dur, until, back)); return self

    def post_push(self, t0, t1, z0=1.0, z1=1.06, ease='push', x=0.0, y=0.0):
        self.posts.append((t0, t1, z0, z1, ease, x, y)); return self

    # ---- evaluation
    def _base(self, t):
        ks = self.keys
        if t <= ks[0][0] or len(ks) == 1: k = ks[0]; return k[1], k[2], k[3], k[4]
        if t >= ks[-1][0]: k = ks[-1]; return k[1], k[2], k[3], k[4]
        for i in range(len(ks) - 1):
            a, b = ks[i], ks[i + 1]
            if a[0] <= t <= b[0]:
                u = (t - a[0]) / max(1e-9, b[0] - a[0])
                e = ease_fn(b[5] or self.ease)(u)
                z = math.exp(lerp(math.log(a[3]), math.log(b[3]), e))
                return lerp(a[1], b[1], e), lerp(a[2], b[2], e), z, lerp(a[4], b[4], e)
        k = ks[-1]; return k[1], k[2], k[3], k[4]

    def _offsets(self, t):
        dx = dy = dr = 0.0
        if self.shake:
            f = t * self.shake_hz
            dx += self.shake * noise1(f, self.seed * 7 + 1)
            dy += self.shake * 0.8 * noise1(f * 1.13, self.seed * 7 + 2)
        if self.roll_shake:
            dr += self.roll_shake * noise1(t * self.shake_hz * 0.7, self.seed * 7 + 3)
        for (th, amp, dur, hz) in self.hits:
            u = t - th
            if 0 <= u < dur * 2.5:
                env = amp * math.exp(-u / max(1e-3, dur) * 2.2)
                dx += env * math.sin(2 * math.pi * hz * u) * 0.6
                dy += env * math.sin(2 * math.pi * hz * 0.83 * u + 1.3)
        return dx, dy, dr

    def _fz(self, t):
        fz = 1.0
        for (ts, factor, dur, until, back) in self.snaps:
            if t < ts: continue
            u = (t - ts) / max(1e-3, dur)
            k = ease_out_back(min(1.0, u), 1.4) if self.snap_back else ease_in_out(min(1.0, u))
            z = lerp(1.0, factor, k)
            if until is not None and t > until:
                z = lerp(factor, 1.0, ease_out_cubic((t - until) / max(1e-3, back)))
            fz *= z
        return fz

    def _post(self, t):
        pz, px, py = 1.0, 0.0, 0.0
        for (t0, t1, z0, z1, e, x, y) in self.posts:
            if t < t0: continue
            u = ease_fn(e)((t - t0) / max(1e-6, t1 - t0))
            pz *= math.exp(lerp(math.log(z0), math.log(z1), u)); px += x * u; py += y * u
        return pz, px, py

    def at(self, t):
        x, y, z, r = self._base(t)
        dx, dy, dr = self._offsets(t)
        h = 1 / 120.0
        xa, ya, za, _ = self._base(t - h); xb, yb, zb, _ = self._base(t + h)
        oxa, oya, _ = self._offsets(t - h); oxb, oyb, _ = self._offsets(t + h)
        vx = -((xb + oxb) - (xa + oxa)) / (2 * h) * z
        vy = -((yb + oyb) - (ya + oya)) / (2 * h) * z
        pz, px, py = self._post(t)
        return CamState(x + dx, y + dy, z, r + dr, self._fz(t), pz, px, py, vx, vy)

    __call__ = at


# ------------------------------------------------------------------ shot helpers
def hold(x=DW / 2, y=DH / 2, zoom=1.0, roll=0.0, shake=0.0, seed=0, **kw):
    return Cam([(0.0, x, y, zoom, roll)], shake=shake, seed=seed, **kw)


def push_in(t0, t1, x=DW / 2, y=DH / 2, z0=1.0, z1=None, rate=0.025, ease='push', drift=(0.0, 0.0), roll=0.0, shake=1.5, seed=0, **kw):
    """Push in about design point (x, y). Default 2.5 %/s (reference median), reference ease profile."""
    if z1 is None: z1 = z0 * (1 + rate) ** max(0.0, t1 - t0)
    return Cam([(t0, x, y, z0, roll), (t1, x + drift[0], y + drift[1], z1, roll, ease)], shake=shake, seed=seed, **kw)


def pull_out(t0, t1, x=DW / 2, y=DH / 2, z0=1.12, z1=1.0, ease='out', shake=1.0, seed=0, **kw):
    return Cam([(t0, x, y, z0), (t1, x, y, z1, 0.0, ease)], shake=shake, seed=seed, **kw)


def drift(t0, t1, x0, y0, x1, y1, zoom=1.04, z1=None, ease='lin', shake=1.5, seed=0, **kw):
    return Cam([(t0, x0, y0, zoom), (t1, x1, y1, z1 or zoom, 0.0, ease)], shake=shake, seed=seed, **kw)


def pan(t0, t1, x0, x1, y=DH / 2, zoom=1.0, ease='in_out', shake=0.0, seed=0, **kw):
    return Cam([(t0, x0, y, zoom), (t1, x1, y, zoom, 0.0, ease)], shake=shake, seed=seed, **kw)


def whip(t, x0, x1, y=DH / 2, zoom=1.0, dur=0.22, shake=0.0, seed=0, **kw):
    return Cam([(t - dur / 2, x0, y, zoom), (t + dur / 2, x1, y, zoom, 0.0, 'in_out')], shake=shake, seed=seed, **kw)


def snap_zoom(t, x=DW / 2, y=DH / 2, z0=1.0, factor=1.3, dur=0.1, until=None, shake=0.0, seed=0, **kw):
    return Cam([(0.0, x, y, z0)], shake=shake, seed=seed, **kw).snap(t, factor, dur, until)


def handheld(cam=None, amount=3.0, hz=0.6, roll=0.0, seed=0):
    cam = cam or hold()
    cam.shake, cam.shake_hz, cam.roll_shake, cam.seed = amount, hz, roll, seed
    return cam
