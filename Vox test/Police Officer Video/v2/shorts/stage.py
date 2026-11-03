"""shorts.stage: the vertical picture engine for the Shorts.

A Short is a list of VShots (vertical shots) over the re-timed voice, each with a picture SOURCE, a 9:16 crop that
follows the subject, push-ins and zoom punches, plus a list of overlay EVENTS (captions, HUD, slams, tags, UI inserts,
SUBSCRIBE, end card, REWIND). Sources re-use the long video's own machinery (film.py builders, characters, sets, engine):

    LongSrc(T)            the long film's own shot at long time T (its staging, acting, lights), running at speed 1
    CustomSrc(kind, T, p) a NEW shot built with film.BUILDERS[kind] and parameters p (film.plan conventions), starting at
                          long time T (so speakers' mouths follow the long video's line timing when T is a clip's source)
    SplitSrc(top, bot)    two sources stacked (vertical split screen), each cropped 1080 x 960
    BlackSrc()            black

The landscape frame is rendered at (H * 16/9) x H (3414 x 1920 for the 1080 x 1920 master, 1707 x 960 for the preview)
and a W-wide window is cut out (607.5 design px at zoom 1), so faces keep full resolution; punches up to 140 % are
digital zooms like the references'. Doorbell / peephole lenses work unchanged because they act on the landscape frame.
"""
import math, os, sys
import numpy as np
import cv2
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
if V2 not in sys.path: sys.path.insert(0, V2)
if HERE not in sys.path: sys.path.insert(0, HERE)

from engine.core import CFG, DW, DH, clamp, lerp, ease_out_back, ease_out_cubic, ease_in_out, noise1, surface_for  # noqa: E402
from engine.scene import render_frame, project, project_box  # noqa: E402
import vfx  # noqa: E402


# ==================================================================================================== sources
class FProxy:
    """Film stand-in for the builders: controls which lines move a character's mouth (talk=None: the long video's lines,
    False: nobody talks, list of dict(who, t, end, en): these synthetic lines)."""
    def __init__(self, F, talk=None):
        self._F, self._talk = F, talk

    def __getattr__(self, k): return getattr(self._F, k)

    def lines_in(self, t0, t1, codes):
        if self._talk is None: return self._F.lines_in(t0, t1, codes)
        if self._talk is False: return []
        return [l for l in self._talk if l['who'] in codes and l['end'] > t0 - 0.2 and l['t'] < t1 + 0.2]


class Src:
    kind = 'src'
    lens_kind = None

    def bind(self, vs): self.vs = vs


class LongSrc(Src):
    """The long film at long time T0 + (t - vshot.t0) * speed (re-using its shots as they are)."""
    def __init__(self, T0=None, speed=1.0, hold=False, anchor=None):
        self.T0, self.speed, self.hold, self.anchor = (None if T0 is None else float(T0)), speed, hold, anchor

    def bind(self, vs):
        self.vs = vs
        if self.anchor is not None:                    # sync: short time ta <-> long time Ta
            ta, Ta = self.anchor; self.T0 = Ta + (vs.t0 - ta) * self.speed

    def tmap(self, t):
        T = self.T0 + (t - self.vs.t0) * self.speed
        if self.hold:
            sh = self.vs.R.F.shot_at(self.T0 + 1e-3)
            T = min(T, sh.t1 - 1.0 / 60)
        return T

    def shot(self, T):
        return self.vs.R.F.shot_at(T)


class CustomSrc(Src):
    """A new shot built by film.BUILDERS[kind] with parameters p, living in the long video's time at T0.. (talk: see FProxy)."""
    _n = 0

    def __init__(self, kind, T0=None, p=None, talk=None, speed=1.0, anchor=None):
        self.kind_, self.T0, self.p, self.talk, self.speed, self.anchor = kind, T0, dict(p or {}), talk, speed, anchor
        CustomSrc._n += 1
        self.uid = 9000 + CustomSrc._n
        self._shot = None

    def bind(self, vs):
        self.vs = vs
        if self.anchor is not None:
            ta, Ta = self.anchor; self.T0 = Ta + (vs.t0 - ta) * self.speed
        if callable(self.p.get('_fix')): self.p = self.p.pop('_fix')(self, vs) or self.p

    def tmap(self, t):
        return self.T0 + (t - self.vs.t0) * self.speed

    def shot(self, T):
        if self._shot is None:
            import film
            sh = film.Shot(self.T0, self.kind_, self.p, self.uid)
            sh.t1 = self.T0 + (self.vs.t1 - self.vs.t0) * self.speed + 0.02
            sh._proxy = FProxy(self.vs.R.F, self.talk)
            self._shot = sh
        return self._shot


class SplitSrc(Src):
    def __init__(self, top, bot, z=(0.62, 0.62), cx=(None, None), cy=(None, None), glitch=None):
        self.top, self.bot, self.z, self.cx, self.cy, self.glitch = top, bot, z, cx, cy, glitch

    def bind(self, vs):
        self.vs = vs; self.top.bind(vs); self.bot.bind(vs)


class BlackSrc(Src):
    def tmap(self, t): return t


# ==================================================================================================== vertical shot
class VShot:
    def __init__(self, t0, src, cx=None, cy=None, z=None, push=0.035, punches=(), track=True, dy=0.0, fx=None, name='',
                 face=0.12, roll=0.0):
        self.t0, self.src = float(t0), src
        self.t1 = self.t0 + 1.0
        self.cx, self.cy, self.z, self.push = cx, cy, z, push
        self.punches = sorted(list(punches))           # [(t, level)] absolute zoom multipliers (step with overshoot)
        self.track, self.dy, self.fx, self.name, self.face, self.roll = track, dy, fx or {}, name, face, roll
        self.R = None
        self.cuts = []                                 # [(t, zoom multiplier, dx, dy)] hard re-frame (jump) cuts

    def cut_at(self, t):
        """(zoom multiplier, dx, dy) of the hard re-frame cut in force at t (instant: it reads as a cut). A tight re-frame
        on an already tight shot pulls back instead (no soft over-zoom)."""
        m, dx, dy = 1.0, 0.0, 0.0
        for (tc, zm, x, y) in self.cuts:
            if t >= tc: m, dx, dy = zm, x, y
        if m > 1.0 and (self.z or 1.0) >= 1.5: m = 1.0 / m
        return m, dx, dy

    def zoom(self, t):
        base = (self.z or 1.0) * (1.0 + self.push * max(0.0, t - self.t0)) * self.cut_at(t)[0]
        lev, prev, tp = 1.0, 1.0, None
        for (tt, l) in self.punches:
            if t >= tt: prev, lev, tp = lev, l, tt
        if tp is not None:
            u = (t - tp) / 0.067
            if u < 1.0:
                s = ease_out_back(clamp(u), 2.2)
                return base * (prev + (lev - prev) * s)
        return base * lev


KIND_Z = {'door': 1.4, 'peep': 1.1, 'mumext': 1.15, 'hall': 1.05, 'kitchen': 1.05, 'mumroom': 1.05}


# ==================================================================================================== renderer
class Renderer:
    """Renders vertical frames for one Short. F: film.Film built at the landscape render size."""
    def __init__(self, F, W, H, shots, overlay=None, post=None):
        self.F, self.W, self.H = F, W, H
        self.LW, self.LH = CFG.rw, CFG.rh
        self.k = self.LH / DH                         # landscape px per design px
        self.shots = sorted(shots, key=lambda s: s.t0)
        for j, s in enumerate(self.shots):
            s.t1 = self.shots[j + 1].t0 if j + 1 < len(self.shots) else max(s.t1, s.t0 + 0.05)
            s.R = self; s.idx = j
            s.src.bind(s)
            if s.z is None:                               # default framing per kind: doorbell footage is wide -> punch in
                kind = getattr(s.src, 'kind_', None)
                if kind is None and isinstance(s.src, LongSrc) and s.src.T0 is not None: kind = F.shot_at(s.src.T0 + 0.01).kind
                s.z = KIND_Z.get(kind, 1.0)
        self._starts = [s.t0 for s in self.shots]
        self._built = {}
        self.overlay, self.post = overlay, post

    def shot_at(self, t):
        import bisect
        k = max(0, bisect.bisect_right(self._starts, t) - 1)
        return self.shots[k]

    # ---------------------------------------------------------------- film specs
    def build(self, sh):
        key = id(sh)
        e = self._built.get(key)
        if e is not None: return e
        import film
        Fp = getattr(sh, '_proxy', None) or self.F
        sh.sfx, sh.music, sh.actors = [], [], []
        spec = film.BUILDERS[sh.kind](Fp, sh)
        film.shot_common(Fp, sh, spec)
        mv = (sh.p.get('cam') or {}).get('mv', 'push')
        if (spec.lens is None and isinstance(spec.cam, film.Cam) and not spec.cam.posts and mv != 'pull'
                and sh.kind not in ('rule', 'black') and not sh.p.get('no_ppush')):
            spec.cam.post_push(sh.t0, sh.t1, 1.0, (1.0 + film.GLOBAL_PPUSH) ** max(0.3, sh.d), ease='push')
        if len(self._built) > 6:
            self._built.clear()
        self._built[key] = spec
        return spec

    def render_long(self, src, t, i):
        """Landscape RGB frame of a film source at short time t + the subject's design point (x, y) or None."""
        import film
        T = src.tmap(t)
        sh = src.shot(T)
        spec = self.build(sh)
        fx = dict(spec.fx(T)) if spec.fx else {}
        film.glob_fx(self.F, sh, T, fx)
        fx.pop('fade', None)
        cs = spec.cam.at(T) if spec.cam is not None else None
        img = render_frame(spec.layers, cs, T, i, focus=spec.focus, dof=spec.dof, lens=spec.lens, grade=spec.grade, post=fx, hud=None)
        src.lens_kind = getattr(spec.lens, 'kind', spec.lens) if spec.lens is not None else None
        src.long_kind = sh.kind
        return img, self.subject(sh, spec, T, cs)

    def subject(self, sh, spec, T, cs):
        """Where the subject's head lands in the landscape frame (design coords), or None (centre)."""
        p = sh.p
        try:
            if sh.kind in ('bust',):
                fr = p.get('_frame')
                cx = p.get('cx', fr[0] if fr else 960); cy = p.get('cy', fr[1] if fr else 560)
                x, y = project(cx, cy - 40, 1.0, cs, None)
                return float(x), float(y)
            if sh.kind == 'car':
                x, y = project(p.get('cx', 985), p.get('cy', 455) - 20, 1.2, cs, None, 1.2)
                return float(x), float(y)
            people = [l for l in spec.layers if hasattr(l, '_box') and l.name.startswith('p')]
            if people:
                lay = people[0]
                bx, by, bw, bh = project_box(lay._box(T), lay.depth_at(T), cs, spec.lens, lay.ref_depth)
                return float(bx + bw / 2), float(by + bh * 0.13)
        except Exception:
            return None
        return None

    # ---------------------------------------------------------------- crop
    def crop(self, img, cx, cy, z, out_w, out_h, roll=0.0):
        """Cut an out_w x out_h window (at zoom z) centred on design (cx, cy) out of the landscape img; one resample."""
        k = self.k
        win_w, win_h = out_w / z, out_h / z                  # in landscape px (render height = output height scale)
        s = self.H / self.LH                                  # output px per landscape px at zoom 1
        win_w /= s; win_h /= s
        X = clamp(cx * k, win_w / 2, self.LW - win_w / 2) if win_w < self.LW else self.LW / 2
        Y = clamp(cy * k, win_h / 2, self.LH - win_h / 2) if win_h < self.LH else self.LH / 2
        sc = out_w / win_w
        if roll:
            M = cv2.getRotationMatrix2D((X, Y), roll, sc)
            M[0, 2] += out_w / 2 - X; M[1, 2] += out_h / 2 - Y
        else:
            M = np.float32([[sc, 0, out_w / 2 - X * sc], [0, sc, out_h / 2 - Y * sc]])
        flag = cv2.INTER_LINEAR if sc <= 1.02 else cv2.INTER_CUBIC
        return cv2.warpAffine(img, M, (int(out_w), int(out_h)), flags=flag, borderMode=cv2.BORDER_REFLECT101)

    def subj_at(self, src, t):
        T = src.tmap(t)
        sh = src.shot(T)
        spec = self.build(sh)
        cs = spec.cam.at(T) if spec.cam is not None else None
        return self.subject(sh, spec, T, cs)

    def framing(self, vs, src, t):
        """Crop centre (design) for a shot: explicit cx/cy, or the tracked subject (mean of 4 samples over the last
        0.24 s inside the shot: a smooth, deterministic follow), else the centre."""
        cx, cy = vs.cx, vs.cy
        if (cx is None or cy is None) and vs.track:
            pts = []
            for d in (0.0, 0.08, 0.16, 0.24):
                tt = max(vs.t0, t - d)
                q = self.subj_at(src, tt)
                if q is not None: pts.append(q)
            if pts:
                sx = sum(q[0] for q in pts) / len(pts); sy = sum(q[1] for q in pts) / len(pts)
                if cx is None: cx = sx
                if cy is None: cy = sy + 150               # head in the upper part of the 9:16 frame
        return (960 if cx is None else cx), (540 if cy is None else cy)

    def render_src(self, vs, src, t, i, out_w, out_h, z, cx=None, cy=None):
        if isinstance(src, BlackSrc):
            return np.zeros((int(out_h), int(out_w), 3), np.uint8)
        img, _ = self.render_long(src, t, i)
        fcx, fcy = self.framing(vs, src, t)
        cx = fcx if cx is None else cx
        cy = fcy if cy is None else cy
        sx, sy = self.post.shake(t) if self.post else (0.0, 0.0)
        if not isinstance(vs.src, SplitSrc):
            _m, cdx, cdy = vs.cut_at(t); sx += cdx; sy += cdy
        return self.crop(img, cx + sx, cy + sy + vs.dy, z, out_w, out_h, vs.roll)

    # ---------------------------------------------------------------- frame
    def frame(self, t, i):
        vs = self.shot_at(t)
        z = vs.zoom(t)
        if isinstance(vs.src, SplitSrc):
            sp = vs.src
            hh = self.H // 2
            zt = sp.z[0] * z; zb = sp.z[1] * z
            top = self.render_src(vs, sp.top, t, i, self.W, hh, zt, sp.cx[0], sp.cy[0])
            bot = self.render_src(vs, sp.bot, t, i, self.W, self.H - hh, zb, sp.cx[1], sp.cy[1])
            if sp.glitch and sp.glitch[0] <= t <= sp.glitch[1]:
                kk = 0.9 * (1 - abs((t - sp.glitch[0]) / (sp.glitch[1] - sp.glitch[0]) * 2 - 1))
                top = vfx.rewind_fx(top, kk, seed=i)
            img = np.concatenate([top, bot], axis=0)
            img[hh - 3:hh + 3] = (235, 235, 235)
        else:
            img = self.render_src(vs, vs.src, t, i, self.W, self.H, z)
        if self.post: img = self.post.apply(img, t, i, vs)
        if self.overlay:
            o4 = cv2.cvtColor(img, cv2.COLOR_RGB2BGRA)
            s = surface_for(o4); cv = s.getCanvas()
            cv.scale(self.W / vfx.VW, self.W / vfx.VW)
            self.overlay(cv, t, i, vs)
            del cv, s
            img = cv2.cvtColor(o4, cv2.COLOR_BGRA2RGB)
        if self.post and hasattr(self.post, 'final'): img = self.post.final(img, t, i, vs)
        return img
