"""engine.lens: real lens models applied to the composited 2.5D scene.

The scene is composited into a SOURCE canvas that is a rectilinear (pinhole) image of the layers, wider than the frame when
the lens needs it. The lens then maps every output pixel to a source pixel with a physical projection, so camera moves,
parallax and people walking toward the lens distort exactly as through a real fisheye.

Lens(kind, **params)            get_lens('doorbell' | 'peephole' | 'lens' | Lens | None) -> cached Lens
  kind='doorbell'  equidistant fisheye (mapping='equidistant' | 'stereographic' | 'equisolid'), fov=150 (diagonal degrees,
                   ~130 deg horizontal), zoom=1.15 (centre magnification vs the 1920x1080 composition: bobble-head),
                   res=0.75 (camera resolution vs output: 1920x1080 at 2560 out), ca=0.0016 (lateral colour at the edges),
                   noise=1.0 (low-light sensor noise), codec=55 (JPEG quality of the stream; 0 = off), sharpen=0.35,
                   ir=False (IR night mode: monochrome, IR illuminator falls off with depth, heavier noise), fps=None
                   (e.g. 15 -> the scene itself steps at 15 fps like a real doorbell stream; post moves stay smooth).
  kind='peephole'  circular fisheye in a dark ring: disc diameter 0.98 H, black outside, fov=105 (barrel k1 ~0.4 at the rim),
                   zoom=1.15, radial falloff to ~0.45 at r=0.8 (with centred subjects this measures ~0.3 like the reference),
                   ring='#2a2018'.
  kind='lens'      mild cinematic barrel: k=0.05 (r_src = r(1 + k r^2), r normalised to the half diagonal), no CA.
Doorbell scenes need content beyond the frame: Lens.src_rect() gives the design-space rectangle the set must cover
(about x -540..2460, y -320..1400 for the default doorbell). Peephole needs about x 300..1620, y -120..1200.

Used by scene.render_frame (callers normally only pass lens='doorbell' etc.):
  L.geometry() -> (hx, hy, sd): source half extents (design px, around the frame centre) and source density (px per design px)
  L.work_size() -> (w, h) of the lens output;  L.optics(src_bgra) -> BGR work image;  L.mask() -> u8 3ch mask (unity 200)
  L.sensor(bgr, frame_i) -> BGR (doorbell noise, sharpening, codec);  L.ring_add() -> additive peephole rim image
  L.ir_gain(depth_cam) -> brightness of a layer at camera distance d under the IR illuminator.
"""
import math
import numpy as np
import cv2
import skia
from . import core
from .core import DW, DH, CFG, col

R_DIAG = math.hypot(DW / 2, DH / 2)


def _theta(r_norm, mapping):
    """Fisheye: normalised image radius (r / f) -> field angle."""
    if mapping == 'stereographic': return 2 * np.arctan(r_norm / 2)
    if mapping == 'equisolid': return 2 * np.arcsin(np.clip(r_norm / 2, -1, 1))
    return r_norm                                    # equidistant


def _rmap(theta_max, mapping):
    """Inverse: field angle -> r / f."""
    if mapping == 'stereographic': return 2 * math.tan(theta_max / 2)
    if mapping == 'equisolid': return 2 * math.sin(theta_max / 2)
    return theta_max


def _rmap_np(theta, mapping):
    if mapping == 'stereographic': return 2 * np.tan(theta / 2)
    if mapping == 'equisolid': return 2 * np.sin(theta / 2)
    return theta


class Lens:
    DEFAULTS = {
        'doorbell': dict(fov=150.0, zoom=1.15, mapping='equidistant', res=0.75, ca=0.0016, noise=1.0, codec=55, sharpen=0.35,
                         ir=False, fps=None, cover=0.9, src_density=None),
        'peephole': dict(fov=105.0, zoom=1.15, mapping='equidistant', disc=0.98, ring='#2a2018', ring_w=6.0, src_density=None),
        'lens': dict(k=0.05, src_density=None),
    }

    def __init__(self, kind='doorbell', **kw):
        if kind not in self.DEFAULTS: raise ValueError('unknown lens ' + kind)
        self.kind = kind
        self.p = dict(self.DEFAULTS[kind]); self.p.update(kw)
        self._c = {}
        self.fps = self.p.get('fps')
        self.ir = bool(self.p.get('ir'))
        self.own_vignette = kind == 'peephole'
        core.on_size_change(self._c.clear)

    def __repr__(self): return 'Lens(%r, %r)' % (self.kind, self.p)

    # ------------------------------------------------------------ geometry
    def _f(self):
        """(f_out, f_src) in design px for the fisheyes."""
        p = self.p
        if self.kind == 'doorbell':
            f_o = R_DIAG / _rmap(math.radians(p['fov'] / 2), p['mapping'])
        else:
            rd = p['disc'] * DH / 2
            f_o = rd / _rmap(math.radians(p['fov'] / 2), p['mapping'])
        return f_o, f_o / p['zoom']

    def _design_to_src(self, qx, qy):
        """Output design offsets from centre -> source design offsets (vectorised), plus validity."""
        p = self.p
        r = np.sqrt(qx * qx + qy * qy) + 1e-9
        if self.kind == 'lens':
            rn = r / R_DIAG; s = 1 + p['k'] * rn * rn
            return qx * s, qy * s, np.ones_like(r, bool)
        f_o, f_s = self._f()
        th = _theta(r / f_o, p['mapping'])
        ok = th < math.radians(86)
        rs = f_s * np.tan(np.minimum(th, math.radians(86)))
        k = rs / r
        return qx * k, qy * k, ok

    def to_output(self, sx, sy):
        """Inverse mapping: source (undistorted) design offsets from the centre -> output design offsets (vectorised)."""
        sx = np.asarray(sx, np.float64); sy = np.asarray(sy, np.float64)
        rs = np.sqrt(sx * sx + sy * sy) + 1e-9
        if self.kind == 'lens':
            r = rs.copy()
            for _ in range(6):                                           # Newton on r (1 + k r^2 / R^2) = rs
                f = r * (1 + self.p['k'] * (r / R_DIAG) ** 2) - rs
                df = 1 + 3 * self.p['k'] * (r / R_DIAG) ** 2
                r = r - f / df
        else:
            f_o, f_s = self._f()
            r = f_o * _rmap_np(np.arctan(rs / f_s), self.p['mapping'])
        k = r / rs
        return sx * k, sy * k

    def src_rect(self):
        hx, hy, _ = self.geometry()
        return (DW / 2 - hx, DH / 2 - hy, DW / 2 + hx, DH / 2 + hy)

    def geometry(self):
        if 'geo' in self._c: return self._c['geo']
        p = self.p; K = CFG.k
        if self.kind == 'lens':
            s = 1 + p['k']
            hx, hy = DW / 2 * s + 4, DH / 2 * s + 4; sd = p['src_density'] or K
        elif self.kind == 'peephole':
            rd = p['disc'] * DH / 2
            sx, _, _ = self._design_to_src(np.array([rd]), np.array([0.0]))
            hx = hy = float(sx[0]) + 6
            sd = p['src_density'] or K * p['zoom'] * 0.9
        else:
            # bounding box of the source needed by the frame edges and by the diagonal up to `cover`
            n = 64
            ex = np.concatenate([np.linspace(-DW / 2, DW / 2, n), np.full(n, DW / 2), np.linspace(-DW / 2, DW / 2, n), np.full(n, -DW / 2)])
            ey = np.concatenate([np.full(n, -DH / 2), np.linspace(-DH / 2, DH / 2, n), np.full(n, DH / 2), np.linspace(-DH / 2, DH / 2, n)])
            rr = np.sqrt(ex * ex + ey * ey); lim = p['cover'] * R_DIAG
            sc = np.minimum(1.0, lim / rr)
            sx, sy, _ = self._design_to_src(ex * sc, ey * sc)
            hx, hy = float(np.abs(sx).max()) + 8, float(np.abs(sy).max()) + 8
            sd = p['src_density'] or K * p['res'] * p['zoom'] * 0.82
        self._c['geo'] = (hx, hy, sd)
        return self._c['geo']

    def work_size(self):
        if self.kind == 'doorbell':
            r = self.p['res']; return int(round(CFG.rw * r / 2) * 2), int(round(CFG.rh * r / 2) * 2)
        return CFG.rw, CFG.rh

    def _roi(self):
        """Region of the work image the lens writes (peephole: the disc's bounding square)."""
        ww, wh = self.work_size()
        if self.kind == 'peephole':
            rd = self.p['disc'] * DH / 2 * ww / DW + 3
            x0 = max(0, int(ww / 2 - rd)); y0 = max(0, int(wh / 2 - rd))
            return x0, y0, min(ww, int(math.ceil(ww / 2 + rd))), min(wh, int(math.ceil(wh / 2 + rd)))
        return 0, 0, ww, wh

    def _maps(self):
        if 'maps' in self._c: return self._c['maps']
        ww, wh = self.work_size(); x0, y0, x1, y1 = self._roi()
        hx, hy, sd = self.geometry()
        wd = ww / DW
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float64)
        qx = (xx + 0.5) / wd - DW / 2; qy = (yy + 0.5) / wd - DH / 2
        sx, sy, ok = self._design_to_src(qx, qy)
        mx = ((sx + hx) * sd - 0.5).astype(np.float32); my = ((sy + hy) * sd - 0.5).astype(np.float32)
        mx[~ok] = -10; my[~ok] = -10
        m1, m2 = cv2.convertMaps(mx, my, cv2.CV_16SC2)
        # coverage: fade to black where the source canvas ends (doorbell extreme corners)
        cov = np.minimum(np.clip((hx - np.abs(sx)) * sd / 6.0, 0, 1), np.clip((hy - np.abs(sy)) * sd / 6.0, 0, 1)) * ok
        self._c['maps'] = (m1, m2, cov.astype(np.float32), (x0, y0, x1, y1))
        return self._c['maps']

    # ------------------------------------------------------------ masks
    def mask(self):
        """u8 3-channel multiplicative mask at work size (200 = unity) or None."""
        if 'mask' in self._c: return self._c['mask']
        ww, wh = self.work_size()
        _, _, cov, (x0, y0, x1, y1) = self._maps()
        m = np.zeros((wh, ww), np.float32)
        m[y0:y1, x0:x1] = cov
        if self.kind == 'peephole':
            rd = self.p['disc'] * DH / 2 * ww / DW
            yy, xx = np.mgrid[0:wh, 0:ww].astype(np.float32)
            rho = np.sqrt((xx + 0.5 - ww / 2) ** 2 + (yy + 0.5 - wh / 2) ** 2) / rd
            prof_r = [0.0, 0.25, 0.5, 0.65, 0.8, 0.9, 0.97, 1.0]
            prof_v = [1.0, 0.97, 0.76, 0.56, 0.38, 0.24, 0.12, 0.06]
            fall = np.interp(rho, prof_r, prof_v).astype(np.float32)
            edge = np.clip((1.0 - rho) * rd / 1.5, 0, 1)                    # 1.5 px antialiased rim
            ring, glint = self._ring(ww, wh)
            m = m * fall * edge * (1 - ring)
        if self.ir:                                                          # IR illuminator hot spot
            yy, xx = np.mgrid[0:wh, 0:ww].astype(np.float32)
            rr = np.sqrt(((xx - ww / 2) / (ww / 2)) ** 2 + ((yy - wh / 2) / (ww / 2)) ** 2)
            m = m * (1.18 - 0.35 * np.clip(rr, 0, 1.2) ** 1.6)
        if self.kind == 'lens' or (m.min() > 0.999 and m.max() < 1.001):
            self._c['mask'] = None
        else:
            mm = np.clip(m * 200, 0, 255).astype(np.uint8)
            self._c['mask'] = cv2.merge([mm, mm, mm])
        return self._c['mask']

    def _ring(self, ww, wh):
        """Peephole rim: (coverage, glint) float maps at work size."""
        key = ('ring', ww, wh)
        if key not in self._c:
            k = ww / DW; rd = self.p['disc'] * DH / 2 * k; w = self.p['ring_w'] * k
            yy, xx = np.mgrid[0:wh, 0:ww].astype(np.float32)
            dx, dy = xx + 0.5 - ww / 2, yy + 0.5 - wh / 2
            rr = np.sqrt(dx * dx + dy * dy)
            ring = np.clip(w / 2 - np.abs(rr - (rd + w * 0.35)) + 0.5, 0, 1)
            ang = (np.degrees(np.arctan2(dy, dx)) + 360) % 360
            arc = np.clip(1 - np.abs(ang - 227.5) / 27.5, 0, 1) ** 0.7
            glint = np.clip(1.1 * k - np.abs(rr - (rd + 1 * k)) + 0.5, 0, 1) * arc * (70 / 255.0)
            self._c[key] = (ring.astype(np.float32), glint.astype(np.float32))
        return self._c[key]

    def ring_add(self):
        """Additive BGR u8 image for the peephole rim (None for other lenses)."""
        if self.kind != 'peephole': return None
        if 'ring_add' not in self._c:
            ww, wh = self.work_size()
            ring, glint = self._ring(ww, wh)
            rc = np.array(core.rgb(self.p['ring'])[::-1], np.float32); gc = np.array(core.rgb('#8a7058')[::-1], np.float32)
            add = ring[..., None] * rc + glint[..., None] * gc
            self._c['ring_add'] = np.clip(add + 0.5, 0, 255).astype(np.uint8)
        return self._c['ring_add']

    def ir_gain(self, d):
        """IR illuminator brightness for a layer at depth d (subject ~1): inverse-square-ish falloff, clipped."""
        return float(np.clip((0.95 / max(0.05, d)) ** 1.5, 0.1, 1.45))

    # ------------------------------------------------------------ processing
    def optics(self, src):
        """src: BGRA source canvas (premultiplied, opaque) -> BGR work image (distorted, CA)."""
        ww, wh = self.work_size()
        m1, m2, _, (x0, y0, x1, y1) = self._maps()
        if (x0, y0, x1, y1) == (0, 0, ww, wh):
            out = cv2.remap(src, m1, m2, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 255))
            out = cv2.cvtColor(out, cv2.COLOR_BGRA2BGR)
        else:
            out = np.zeros((wh, ww, 3), np.uint8)
            part = cv2.remap(src, m1, m2, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 255))
            out[y0:y1, x0:x1] = cv2.cvtColor(part, cv2.COLOR_BGRA2BGR)
        ca = self.p.get('ca', 0.0)
        if ca:
            b, g, r = cv2.split(out)
            cx, cy = ww / 2, wh / 2
            def sc(ch, s):
                A = np.float32([[s, 0, cx * (1 - s)], [0, s, cy * (1 - s)]])
                return cv2.warpAffine(ch, A, (ww, wh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            out = cv2.merge([sc(b, 1 - ca), g, sc(r, 1 + ca)])
        return out

    def _noise_tex(self, ww, wh):
        key = ('noise', ww, wh, self.ir)
        if key not in self._c:
            rng = np.random.default_rng(7)
            H2, W2 = wh + 96, ww + 96
            lum = cv2.GaussianBlur(rng.normal(0, 1, (H2, W2)).astype(np.float32), (0, 0), 0.7) * (5.5 if self.ir else 3.6)
            ch = []
            for c in range(3):
                small = rng.normal(0, 1, (H2 // 3 + 1, W2 // 3 + 1)).astype(np.float32)
                ch.append(cv2.resize(cv2.GaussianBlur(small, (0, 0), 0.8), (W2, H2), interpolation=cv2.INTER_LINEAR) * (0.0 if self.ir else 3.4))
            n = np.dstack([lum + ch[0], lum + ch[1] * 0.6, lum + ch[2]])
            self._c[key] = np.clip(128 + n, 0, 255).astype(np.uint8)
        return self._c[key]

    def sensor(self, img, frame_i):
        """In-camera processing for the doorbell: IR monochrome, sharpening, low-light noise, stream compression."""
        if self.kind != 'doorbell': return img
        p = self.p; wh, ww = img.shape[:2]
        if self.ir:
            g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.merge([g, g, g])
        if p.get('sharpen'):
            bl = cv2.GaussianBlur(img, (0, 0), 1.6)
            img = cv2.addWeighted(img, 1 + p['sharpen'], bl, -p['sharpen'], 0)
        amt = p.get('noise', 0.0)
        if amt:
            tex = self._noise_tex(ww, wh)
            rng = np.random.default_rng(frame_i * 7919 + 13)
            ox, oy = int(rng.integers(0, 96)), int(rng.integers(0, 96))
            img = cv2.addWeighted(img, 1.0, tex[oy:oy + wh, ox:ox + ww], amt, -128.0 * amt)
        q = p.get('codec')
        if q:
            ok, buf = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, int(q), cv2.IMWRITE_JPEG_OPTIMIZE, 0])
            img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        return img

    def overlay(self, cv):
        """Kept for API compatibility: the peephole rim is baked into mask() / ring_add()."""
        return

_lenses = {}


def get_lens(lens):
    if lens is None or isinstance(lens, Lens): return lens
    if lens not in _lenses:
        if lens == 'doorbell_ir': _lenses[lens] = Lens('doorbell', ir=True, noise=1.4)
        else: _lenses[lens] = Lens(lens)
    return _lenses[lens]
