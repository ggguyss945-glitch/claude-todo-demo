"""engine.room3d: a small projection kit for perspective sets (DIRECTION_V2 section 4).

Rooms are built in METRES (X right, Y up, Z away from the camera's usual side: in Cabin 7, from the door to the back wall)
as flat-shaded planes, boxes and props. A pinhole `Cam3` projects them into the engine's 1920x1080 design space; every
plane is drawn in its own 2D coordinates (centimetres) through a perspective homography, so wood grain, signs, gradients
and light pools on a wall or the floor come out perspective-correct with the ordinary Pen calls.

One model gives every angle, the mirror's reflection (`Xf.reflect_z`) and the flipped other side (`Xf.flip_x`, which flips
the layout but keeps text readable). Characters stay 2D: `Cam3.anchor(P, height_m)` gives the design point, the design height
and the layer depth of a person standing at P.

    cam = Cam3((2.8, 1.65, 0.4), look=(2.6, 0.9, 6.4), fov=72)
    sc = Scene3()
    sc.plane(O, U, V, w_cm, h_cm, draw)           # draw(pen) in plane cm: s along U, t along V
    sc.box(x0, y0, z0, x1, y1, z1, faces)         # faces: {'top': c | fn, 'front': ...} (visible faces only)
    sc.quad([P0, P1, P2, P3], c)                  # flat polygon
    sc.render(pen, cam, bands=(0, 3.0))           # painter's order, only items whose distance falls in the band
    layers = sc.layers(cam, d0, [(0, 2.5, 'near'), (2.5, 99, 'far')], key='c7:master')   # cached engine Layers per band

Item distance is the camera-space depth of the item's centre (`dist`), which the painter sorts on; `order` breaks ties
(walls first). `Scene3.layers` turns bands into cached `engine.scene.Layer`s at layer depth = band distance / d0, so a camera
dolly in the 2.5D engine gives real parallax between them.
"""
import math
import numpy as np
import skia
from .core import Pen, col, mix, poly, rect, clamp, lerp
from .scene import Layer

__all__ = ['Cam3', 'Scene3', 'Xf', 'v3', 'norm', 'ID']

DW, DH = 1920.0, 1080.0


def v3(x, y=None, z=None):
    if y is None: return np.asarray(x, np.float64)
    return np.array([x, y, z], np.float64)


def norm(v):
    v = np.asarray(v, np.float64); n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


# ====================================================================== transforms of the model
class Xf:
    """Affine transform applied to the model before projection: P' = M P + o. `layout_flip` keeps plane content readable
    (a flipped plane draws its content un-mirrored at the flipped place)."""

    def __init__(self, M=None, o=None, layout_flip=False):
        self.M = np.eye(3) if M is None else np.asarray(M, np.float64)
        self.o = np.zeros(3) if o is None else np.asarray(o, np.float64)
        self.layout_flip = layout_flip

    def p(self, P): return self.M @ np.asarray(P, np.float64) + self.o

    def d(self, D): return self.M @ np.asarray(D, np.float64)

    @property
    def mirrors(self): return np.linalg.det(self.M) < 0

    @staticmethod
    def flip_x(W):
        """The other side: x -> W - x (Cabin 7 flipped left-right), content kept readable."""
        return Xf(np.diag([-1.0, 1.0, 1.0]), [W, 0.0, 0.0], layout_flip=True)

    @staticmethod
    def reflect_z(z0):
        """A mirror on the plane z = z0 (true reflection: content reversed, as in a glass)."""
        return Xf(np.diag([1.0, 1.0, -1.0]), [0.0, 0.0, 2.0 * z0])

    @staticmethod
    def reflect_plane(P0, n):
        """True reflection in the plane through P0 with normal n."""
        n = norm(n); M = np.eye(3) - 2.0 * np.outer(n, n)
        return Xf(M, 2.0 * np.dot(P0, n) * n)

    def then(self, other):
        return Xf(other.M @ self.M, other.M @ self.o + other.o, self.layout_flip or other.layout_flip)


ID = Xf()


# ====================================================================== camera
class Cam3:
    """Pinhole camera. pos (m); yaw (deg, 0 = looking +Z, positive turns right toward +X); pitch (deg, positive up); roll (deg);
    fov = horizontal field of view over the 1920 design width; shift = lens shift of the principal point (design px; a
    shifted lens frames up/down without converging verticals). look=(x, y, z) sets yaw and pitch."""

    def __init__(self, pos, yaw=0.0, pitch=0.0, roll=0.0, fov=70.0, look=None, shift=(0.0, 0.0), near=0.05):
        self.C = v3(pos)
        if look is not None:
            d = v3(look) - self.C
            yaw = math.degrees(math.atan2(d[0], d[2]))
            pitch = math.degrees(math.atan2(d[1], math.hypot(d[0], d[2])))
        self.yaw, self.pitch, self.roll, self.fov = yaw, pitch, roll, fov
        self.shift = (float(shift[0]), float(shift[1]))
        self.near = near
        self.f = (DW / 2) / math.tan(math.radians(fov) / 2)
        cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
        fwd = np.array([sy * cp, sp, cy * cp])
        right = norm(np.cross([0.0, 1.0, 0.0], fwd))
        up = np.cross(fwd, right)
        if roll:
            cr, sr = math.cos(math.radians(roll)), math.sin(math.radians(roll))
            right, up = right * cr + up * sr, -right * sr + up * cr
        self.R = np.vstack([right, up, fwd])
        self.cx, self.cy = DW / 2 + self.shift[0], DH / 2 + self.shift[1]
        self.K = np.array([[self.f, 0.0, self.cx], [0.0, -self.f, self.cy], [0.0, 0.0, 1.0]])

    def cam(self, P):
        return self.R @ (np.asarray(P, np.float64) - self.C)

    def dist(self, P):
        return float(self.cam(P)[2])

    def proj(self, P):
        """-> (x, y, z_cam) in design px (z_cam <= near means behind the camera)."""
        q = self.cam(P)
        z = q[2] if q[2] > 1e-6 else 1e-6
        return (self.cx + self.f * q[0] / z, self.cy - self.f * q[1] / z, float(q[2]))

    def pt(self, P):
        x, y, _ = self.proj(P); return (x, y)

    def px_per_m(self, P):
        """Design px per metre at point P (for sizes of things standing there)."""
        return self.f / max(1e-3, self.dist(P))

    def anchor(self, P, height_m=1.7, d0=None):
        """A person (or prop) standing at floor point P: (x, y_feet, height_px, layer_depth) with layer depth = distance/d0."""
        x, y, z = self.proj(P)
        h = height_m * self.f / max(1e-3, z)
        return (x, y, h, (z / d0) if d0 else 1.0)

    def H(self, O, U, V, unit=0.01):
        """3x3 homography: plane coords (s, t) in `unit` metres (default cm) -> design px."""
        a = self.R @ (np.asarray(U, np.float64) * unit)
        b = self.R @ (np.asarray(V, np.float64) * unit)
        c = self.R @ (np.asarray(O, np.float64) - self.C)
        return self.K @ np.column_stack([a, b, c]), (a, b, c)


def _skmat(H):
    # scale by a POSITIVE factor only: skia culls points with w <= 0, so the sign of w (= camera depth) must be kept
    k = abs(H[2, 2]) if abs(H[2, 2]) > 1e-9 else (np.linalg.norm(H[2]) or 1.0)
    H = H / k
    return skia.Matrix.MakeAll(float(H[0, 0]), float(H[0, 1]), float(H[0, 2]),
                               float(H[1, 0]), float(H[1, 1]), float(H[1, 2]),
                               float(H[2, 0]), float(H[2, 1]), float(H[2, 2]))


def _clip_halfplane(pts, f):
    """Sutherland-Hodgman: keep the part of polygon pts (list of (s, t)) where f(s, t) >= 0 (f linear)."""
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        fa, fb = f(*a), f(*b)
        if fa >= 0: out.append(a)
        if (fa >= 0) != (fb >= 0):
            u = fa / (fa - fb)
            out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
    return out


# ====================================================================== items
class Item:
    __slots__ = ('kind', 'data', 'order', 'name', 'centre', 'tag', 'force_dist')

    def __init__(self, kind, data, centre, order=0, name='', tag=None, force_dist=None):
        self.kind, self.data, self.centre, self.order, self.name, self.tag = kind, data, centre, order, name, tag
        self.force_dist = force_dist


class Scene3:
    """A list of 3D items drawn in painter's order (far to near by camera depth of the item centre). `order` is a bias in
    metres: the sort key is dist - order, so negative orders draw earlier (walls -100, the floor -120 are always behind
    props) and small positive orders put decals on top of what they sit on."""

    def __init__(self):
        self.items = []
        self.lights = []          # [Light]: applied to every plane and box face after its own drawing

    def light(self, P, c, a=120, r=1.5, blend='screen', name=''):
        """A point light: P (m), colour, peak alpha, radius r (m): a surface at distance d from P gets
        a r^2 / (r^2 + d^2) of it, spread over sqrt(r^2 + d^2) along the surface (screen-blended wash)."""
        self.lights.append((v3(P), c, float(a), float(r), blend, name))
        return self

    # ---- building
    def plane(self, O, U, V, w, h, draw, order=0, name='', tag=None, two_sided=True, unit=0.01, centre=None, dist=None,
              readable=True):
        """A rectangle w x h (in `unit` m, default cm) at origin O spanned by unit axes U (s) and V (t); draw(pen, w, h)
        paints it in plane coords. two_sided=False culls it when seen from behind (normal = U x V). readable=False: under
        a layout flip the content is mirrored with the room (walls with holes, floors with pools); True keeps text readable."""
        O, U, V = v3(O), norm(U), norm(V)
        c = O + U * (w * unit / 2) + V * (h * unit / 2) if centre is None else v3(centre)
        self.items.append(Item('plane', (O, U, V, w, h, draw, two_sided, unit, readable), c, order, name, tag, dist))
        return self

    def quad(self, pts, c, a=255, line=None, lw=None, order=0, name='', tag=None, two_sided=True, dist=None):
        pts = [v3(p) for p in pts]
        self.items.append(Item('quad', (pts, c, a, line, lw, two_sided), sum(pts) / len(pts), order, name, tag, dist))
        return self

    def poly3(self, pts, draw, order=0, name='', tag=None, dist=None):
        """A screen-space custom draw of a 3D polyline/polygon: draw(pen, pts2d, cam)."""
        pts = [v3(p) for p in pts]
        self.items.append(Item('poly', (pts, draw), sum(pts) / len(pts), order, name, tag, dist))
        return self

    def custom(self, centre, draw, order=0, name='', tag=None, dist=None):
        """draw(pen, cam, xf) for anything else (sprites at projected points, glows)."""
        self.items.append(Item('custom', draw, v3(centre), order, name, tag, dist))
        return self

    def box(self, x0, y0, z0, x1, y1, z1, faces, order=0, name='', tag=None, line=None, lw=None, dist=None):
        """Axis-aligned box. faces: dict side -> colour or draw(pen, w, h) for 'top', 'bottom', 'front' (z0), 'back' (z1),
        'left' (x0), 'right' (x1); a colour under key 'all' fills the rest. Only faces turned to the camera draw."""
        x0, x1 = min(x0, x1), max(x0, x1); y0, y1 = min(y0, y1), max(y0, y1); z0, z1 = min(z0, z1), max(z0, z1)
        allc = faces.get('all')
        W, Hh, D = (x1 - x0) * 100, (y1 - y0) * 100, (z1 - z0) * 100
        spec = {
            # name: origin (top-left of the face as seen from outside), U, V, w, h, outward normal
            'front': ((x0, y1, z0), (1, 0, 0), (0, -1, 0), W, Hh, (0, 0, -1)),
            'back': ((x1, y1, z1), (-1, 0, 0), (0, -1, 0), W, Hh, (0, 0, 1)),
            'left': ((x0, y1, z1), (0, 0, -1), (0, -1, 0), D, Hh, (-1, 0, 0)),
            'right': ((x1, y1, z0), (0, 0, 1), (0, -1, 0), D, Hh, (1, 0, 0)),
            'top': ((x0, y1, z1), (1, 0, 0), (0, 0, -1), W, D, (0, 1, 0)),
            'bottom': ((x0, y0, z0), (1, 0, 0), (0, 0, 1), W, D, (0, -1, 0)),
        }
        cen = v3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        self.items.append(Item('box', (spec, faces, allc, line, lw), cen, order, name, tag, dist))
        return self

    def extend(self, other):
        self.items.extend(other.items); return self

    # ---- drawing
    def _dist(self, it, cam, xf):
        if it.force_dist is not None: return it.force_dist
        return cam.dist(xf.p(it.centre))

    def _band_dist(self, it, cam, xf):
        """Distance used to pick an item's band: planes go by their FARTHEST corner (a wall or floor strip belongs with
        what stands in front of it, never in front of it), everything else by its centre."""
        if it.force_dist is not None: return it.force_dist
        if it.kind == 'plane':
            O, U, V, w, h, draw, two, unit, _r = it.data
            cs = [O, O + U * (w * unit), O + V * (h * unit), O + U * (w * unit) + V * (h * unit)]
            return max(cam.dist(xf.p(c)) for c in cs)
        return cam.dist(xf.p(it.centre))

    def render(self, pen, cam, xf=ID, band=None, tags=None, skip=None, clip_poly=None):
        """Draw the items (optionally only those with band[0] <= dist < band[1], or whose tag is in `tags`)."""
        cv = pen.cv
        L = []
        for it in self.items:
            if tags is not None and it.tag not in tags: continue
            if skip is not None and it.tag in skip: continue
            d = self._dist(it, cam, xf)
            if band is not None:
                db = self._band_dist(it, cam, xf)
                if not ((band[0] <= db or band[0] <= -1e8) and db < band[1]): continue
            L.append((d - it.order, it))
        L.sort(key=lambda x: -x[0])
        if clip_poly is not None:
            cv.save(); cv.clipPath(poly(clip_poly), skia.ClipOp.kIntersect, True)
        for _, it in L:
            self._draw(pen, cam, xf, it)
        if clip_poly is not None: cv.restore()

    def _draw(self, pen, cam, xf, it):
        k = it.kind
        if k == 'plane':
            O, U, V, w, h, draw, two, unit, readable = it.data
            draw_plane(pen, cam, xf, O, U, V, w, h, draw, two, unit, self.lights, readable)
        elif k == 'quad':
            pts, c, a, line, lw, two = it.data
            P = [xf.p(p) for p in pts]
            if not two:
                n = np.cross(P[1] - P[0], P[2] - P[0])
                if xf.mirrors: n = -n
                if np.dot(n, cam.C - P[0]) <= 0: return
            q = clip_poly_near(cam, P)
            if len(q) < 3: return
            path = poly(q)
            if c is not None: pen.fill(path, c, a)
            if line: pen.line(path, lw or 2.0, line)
        elif k == 'poly':
            pts, draw = it.data
            P = [xf.p(p) for p in pts]
            if any(cam.dist(p) < cam.near for p in P): return
            draw(pen, [cam.pt(p) for p in P], cam)
        elif k == 'custom':
            it.data(pen, cam, xf)
        elif k == 'box':
            spec, faces, allc, line, lw = it.data
            for side, (O, U, V, w, h, nrm) in spec.items():
                f = faces.get(side, allc)
                if f is None or w <= 0 or h <= 0: continue
                Ow = xf.p(O); n = xf.d(nrm)
                cen = Ow + xf.d(U) * w / 200 + xf.d(V) * h / 200
                if np.dot(n, cam.C - cen) <= 1e-9: continue
                if callable(f):
                    draw_plane(pen, cam, xf, O, U, V, w, h, f, True, 0.01, self.lights, False)
                else:
                    def fl(p, ww, hh, f=f):
                        r = rect(0, 0, ww, hh); p.fill(r, f)
                        if line: p.line(r, lw or 1.2, line)
                    draw_plane(pen, cam, xf, O, U, V, w, h, fl, True, 0.01, self.lights, False)

    def layers(self, cam, d0, bands, key, xf=ID, bounds=None, dims=None, tags=None, skip=None, blur=None, cache_res=1.0):
        """Cached engine Layers, one per band (dmin, dmax, name[, layer_depth]): layer depth = band mid distance / d0 unless
        given. bounds default to the engine FRAME margins (wider for near bands)."""
        out = []
        for b in bands:
            dmin, dmax, name = b[0], b[1], b[2]
            ld = b[3] if len(b) > 3 else None
            if ld is None:
                ds = [self._band_dist(it, cam, xf) for it in self.items if dmin <= self._band_dist(it, cam, xf) < dmax
                      and (tags is None or it.tag in tags)]
                ld = (np.median(ds) / d0) if ds else max(0.3, (dmin + min(dmax, dmin * 2 + 1)) / 2 / d0)
            ld = float(max(0.55, ld))          # near bands never below 0.55: a plan dolly (zoom 1.1-1.3) must not blow them up
            bb = bounds or ((-420, -280, 2340, 1360) if ld >= 0.95 else (-900, -560, 2820, 1640))

            def draw(pen, t, dmin=dmin, dmax=dmax):
                self.render(pen, cam, xf, (dmin, dmax), tags, skip)
            out.append(Layer(ld, draw, name, cache='%s:%s' % (key, name), bounds=bb, blur=blur, cache_res=cache_res))
        return out


# projected coordinates are kept inside this design-px window (skia's rasteriser misbehaves past ~32k px)
XLIM, YLIM = (-3200.0, 5120.0), (-2600.0, 3680.0)


def _frustum_fns(cam, a, b, c, near):
    """Linear functions f(s, t) >= 0 for the clip window, for a plane with camera-space point c + s a + t b."""
    f, cx, cy = cam.f, cam.cx, cam.cy
    fns = [lambda s, t: c[2] + s * a[2] + t * b[2] - near]
    # x_img = cx + f xc / zc <= X1  <=>  (X1 - cx) zc - f xc >= 0 ; >= X0  <=>  f xc - (X0 - cx) zc >= 0
    X0, X1 = XLIM; Y0, Y1 = YLIM
    def lin(kz, kx, ky):
        return lambda s, t: (kz * (c[2] + s * a[2] + t * b[2]) + kx * (c[0] + s * a[0] + t * b[0]) + ky * (c[1] + s * a[1] + t * b[1]))
    fns.append(lin(X1 - cx, -f, 0.0)); fns.append(lin(-(X0 - cx), f, 0.0))
    # y_img = cy - f yc / zc <= Y1 <=> (Y1 - cy) zc + f yc >= 0 ; >= Y0 <=> -(Y0 - cy) zc - f yc >= 0
    fns.append(lin(Y1 - cy, 0.0, f)); fns.append(lin(-(Y0 - cy), 0.0, -f))
    return fns


def clip_poly_near(cam, P, near=None):
    """Project a 3D polygon after clipping it to the camera's near plane and the projection window -> design points."""
    near = cam.near if near is None else near
    Q = [cam.cam(p) for p in P]
    # clip in camera space against the same 5 planes (as functions of a camera-space point)
    f, cx, cy = cam.f, cam.cx, cam.cy
    X0, X1 = XLIM; Y0, Y1 = YLIM
    planes = [lambda q: q[2] - near, lambda q: (X1 - cx) * q[2] - f * q[0], lambda q: f * q[0] - (X0 - cx) * q[2],
              lambda q: (Y1 - cy) * q[2] + f * q[1], lambda q: -(Y0 - cy) * q[2] - f * q[1]]
    for fn in planes:
        out = []
        n = len(Q)
        for i in range(n):
            a, b = Q[i], Q[(i + 1) % n]
            fa, fb = fn(a), fn(b)
            if fa >= 0: out.append(a)
            if (fa >= 0) != (fb >= 0):
                u = fa / (fa - fb)
                out.append(a + (b - a) * u)
        Q = out
        if len(Q) < 3: return []
    return [(cx + f * q[0] / q[2], cy - f * q[1] / q[2]) for q in Q]


def _apply_lights(pen, O, U, V, w, h, lights, unit, viewer):
    """Light washes on a plane (in plane units) from model-space point lights on the viewer's side of it."""
    n = norm(np.cross(U, V))
    sv = np.dot(viewer - O, n)
    for (P, c, a, r, blend, _) in lights:
        d = float(np.dot(P - O, n))
        if d * sv <= 0 and abs(d) > 0.02: continue          # the light is behind this face
        d = abs(d)
        Q = P - n * np.dot(P - O, n)
        s_ = float(np.dot(Q - O, U)) / unit; t_ = float(np.dot(Q - O, V)) / unit
        wid = math.sqrt(r * r + d * d) / unit
        aa = a * r * r / (r * r + d * d)
        if aa < 3: continue
        R = wid * 3.0
        if s_ + R < 0 or s_ - R > w or t_ + R < 0 or t_ - R > h: continue
        stops = [(0.0, c, aa), (0.12, c, aa * 0.86), (0.33, c, aa * 0.5), (0.6, c, aa * 0.18), (1.0, c, 0)]
        pen.radial(rect(0, 0, w, h), s_, t_, R, stops, blend='normal' if blend == 'screen' else blend, clip=True)


def draw_plane(pen, cam, xf, O, U, V, w, h, draw, two_sided=True, unit=0.01, lights=None, readable=True):
    """Draw a w x h plane (plane units, default cm) through its homography; content clipped to the part in front of the
    camera. With a layout-flipping transform the plane's U axis is turned back so text stays readable. `lights` (model
    space) are washed over the content."""
    O = v3(O); U = v3(U); V = v3(V)
    O0, U0, V0 = O, U, V
    Ow, Uw, Vw = xf.p(O), xf.d(U), xf.d(V)
    if xf.layout_flip and xf.mirrors and readable:
        # keep content readable: draw from the other end along the flipped axis
        if abs(Uw[0]) > 0.5 or (abs(Uw[0]) <= 0.5 and abs(Vw[0]) <= 0.5):
            Ow = Ow + Uw * (w * unit); Uw = -Uw
        else:
            Ow = Ow + Vw * (h * unit); Vw = -Vw
    n = np.cross(Uw, Vw)
    if not two_sided and np.dot(n, cam.C - Ow) <= 0: return
    Hm, (a, b, c) = cam.H(Ow, Uw, Vw, unit)
    near = cam.near
    # visible part: z_cam(s, t) = c_z + s a_z + t b_z >= near
    vis = [(0.0, 0.0), (w, 0.0), (w, h), (0.0, h)]
    for fn in _frustum_fns(cam, a, b, c, near):
        vis = _clip_halfplane(vis, fn)
        if len(vis) < 3: return
    # cheap frustum reject: all projected points far outside the drawing region
    pr = [Hm @ np.array([s, t, 1.0]) for s, t in vis]
    xs = [p[0] / p[2] for p in pr]; ys = [p[1] / p[2] for p in pr]
    if max(xs) < -4000 or min(xs) > 6000 or max(ys) < -3000 or min(ys) > 4500:
        return
    cv = pen.cv
    cv.save()
    cv.concat(_skmat(Hm))
    cv.clipPath(poly(vis), skia.ClipOp.kIntersect, True)
    lw = pen.lw
    if lights:
        # the light washes must only touch what this plane drew (a frame plane must not wash the glass inside it):
        # content in its own layer, the washes composited onto it with src-atop
        cv.saveLayer(None, None)
    draw(pen, w, h)
    if lights:
        cv.saveLayer(None, skia.Paint(BlendMode=skia.BlendMode.kSrcATop))
        # lights live in model space: express them in this plane's (model) frame before the layout flip
        Lm = lights
        if xf.layout_flip and xf.mirrors and readable:
            Om, Um, Vm = Ow, Uw, Vw
            Lm = [(xf.p(P), c, a, r, b, nm) for (P, c, a, r, b, nm) in lights]
            _apply_lights(pen, Om, Um, Vm, w, h, Lm, unit, cam.C)
        else:
            _apply_lights(pen, O0, U0, V0, w, h, lights, unit, xf_inv_point(xf, cam.C))
        cv.restore(); cv.restore()
    pen.lw = lw
    cv.restore()


def xf_inv_point(xf, P):
    """Model-space point that xf maps to P."""
    return np.linalg.solve(xf.M, np.asarray(P, np.float64) - xf.o)
