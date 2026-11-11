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

__all__ = ['Cam3', 'Scene3', 'Xf', 'v3', 'norm', 'ID', 'CamPath3', 'TexCache', 'glide', 'mono_cubic']

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

    def _dists(self, cam, xf):
        """(dist, band_dist) of every item for this camera, memoised per camera object (a moving shot asks once per band)."""
        memo = getattr(self, '_dmemo', None)
        if memo is not None and memo[0] is cam and memo[1] is xf and memo[2] == len(self.items): return memo[3]
        D = [(self._dist(it, cam, xf), self._band_dist(it, cam, xf)) for it in self.items]
        self._dmemo = (cam, xf, len(self.items), D)
        return D

    def render(self, pen, cam, xf=ID, band=None, tags=None, skip=None, clip_poly=None, tex=None):
        """Draw the items (optionally only those with band[0] <= dist < band[1], or whose tag is in `tags`). tex: a
        TexCache: planes and box faces are drawn from baked textures (moving cameras) unless they come close."""
        cv = pen.cv
        L = []
        D = self._dists(cam, xf)
        for it, (d, db) in zip(self.items, D):
            if tags is not None and it.tag not in tags: continue
            if skip is not None and it.tag in skip: continue
            if band is not None:
                if not ((band[0] <= db or band[0] <= -1e8) and db < band[1]): continue
            L.append((d - it.order, it))
        L.sort(key=lambda x: -x[0])
        if clip_poly is not None:
            cv.save(); cv.clipPath(poly(clip_poly), skia.ClipOp.kIntersect, True)
        for _, it in L:
            self._draw(pen, cam, xf, it, tex)
        if clip_poly is not None: cv.restore()

    def _draw(self, pen, cam, xf, it, tex=None):
        k = it.kind
        if k == 'plane':
            O, U, V, w, h, draw, two, unit, readable = it.data
            draw_plane(pen, cam, xf, O, U, V, w, h, draw, two, unit, self.lights, readable, tex=tex, tkey=(id(it),))
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
                    draw_plane(pen, cam, xf, O, U, V, w, h, f, True, 0.01, self.lights, False, tex=tex, tkey=(id(it), side))
                else:
                    def fl(p, ww, hh, f=f):
                        r = rect(0, 0, ww, hh); p.fill(r, f)
                        if line: p.line(r, lw or 1.2, line)
                    draw_plane(pen, cam, xf, O, U, V, w, h, fl, True, 0.01, self.lights, False, tex=tex, tkey=(id(it), side),
                               smooth=not line)

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


    def live_bands(self, cam, d0, bands, xf=ID, tags=None, skip=None, blur=None, tex=None, depths=None):
        """Uncached band Layers for ONE frame's camera (a camera that travels through the room rebuilds its view every
        frame): planes and box faces come from the baked textures in `tex` (a TexCache kept with the scene for the shot),
        so a frame costs about one textured fill per surface. depths: fixed layer depths per band (stable draw order and
        focus while the camera moves); default near 0.6, mid 1.0, far 2.0."""
        if tex is None:
            tex = getattr(self, 'tex', None)
            if tex is None: tex = self.tex = TexCache()
        out = []
        dd = depths or {0: 0.6, 1: 1.0, 2: 2.0}
        from .core import CFG, surface_for, image_from
        k = LIVE_BAND_RES if CFG.rw > 1500 else 1.0

        def draw_band(pen, t, dmin, dmax):
            if k >= 0.999:
                self.render(pen, cam, xf, (dmin, dmax), tags, skip, tex=tex); return
            # full-size renders: the band is rasterised at LIVE_BAND_RES of the frame and scaled up (its surfaces are
            # textured and soft anyway; the fill rate of six full-frame textured planes per frame was the cost)
            cv = pen.cv
            sz = cv.getBaseLayerSize(); W_, H_ = sz.width(), sz.height()
            w2, h2 = max(2, int(W_ * k)), max(2, int(H_ * k))
            arr = np.zeros((h2, w2, 4), np.uint8)
            srf = surface_for(arr); c2 = srf.getCanvas()
            c2.scale(w2 / W_, h2 / H_); c2.concat(cv.getTotalMatrix())
            p2 = Pen(c2)
            p2.lw = getattr(pen, 'lw', 1.0)
            self.render(p2, cam, xf, (dmin, dmax), tags, skip, tex=tex)
            del c2, srf
            img = image_from(arr)
            cv.save(); cv.resetMatrix()
            cv.drawImageRect(img, skia.Rect.MakeWH(w2, h2), skia.Rect.MakeWH(W_, H_), skia.SamplingOptions(skia.FilterMode.kLinear), None,
                             skia.Canvas.kFast_SrcRectConstraint)
            cv.restore()
        for j, b in enumerate(bands):
            dmin, dmax, name = b[0], b[1], b[2]
            ld = float(b[3]) if len(b) > 3 else float(dd.get(j, 1.0 + j))

            def draw(pen, t, dmin=dmin, dmax=dmax):
                draw_band(pen, t, dmin, dmax)
            out.append(Layer(ld, draw, name, blur=blur))
        return out

    def moving_layers(self, camfn, d0, bands, key, xf=ID, tags=None, skip=None, blur=None, span=None):
        """Live (uncached) Layers for a camera that moves: camfn(t) -> Cam3. One layer per band (dmin, dmax, name, depth):
        each frame every item goes to the band its distance from the camera of that frame falls in, and the planes are
        drawn from baked textures (Scene3.tex) so a dolly, crane or track through the room costs about one textured fill
        per surface. The 2.5D engine camera stays home on these shots: the move is the Cam3's. span=(t0, t1): the textures
        are baked once at the largest density the move asks of each surface (no re-bake, so no sharpness pops)."""
        if getattr(self, 'tex', None) is None: self.tex = TexCache()
        if span is not None and not self.tex.need:
            self.tex.prescan(self, camfn, xf, span)
        out = []
        for b in bands:
            dmin, dmax, name = b[0], b[1], b[2]
            ld = float(b[3]) if len(b) > 3 else float(max(0.55, (max(dmin, 0.0) + min(dmax, max(dmin, 0.0) * 2 + 1)) / 2 / d0))

            def draw(pen, t, dmin=dmin, dmax=dmax):
                self.render(pen, camfn(t), xf, (dmin, dmax), tags, skip, tex=self.tex)
            out.append(Layer(ld, draw, name, blur=blur))
        return out


class TexCache(dict):
    """Baked plane textures for moving cameras: key -> (skia.Image with mipmaps, texels per plane unit). The content of
    a plane (and the light washes on it) does not depend on the camera, so it is drawn once and mapped through the
    plane's homography every frame. TEX_PX: texels per cm at 2560 wide (scaled to the render size); planes that come
    closer than TEX_NEAR x that density are drawn as vectors instead (crisp near surfaces)."""
    TEX_PX = 4.0
    TEX_NEAR = 8.0
    MAX_SIDE = 6000
    MAX_PIX = 6e6

    def __init__(self):
        super().__init__()
        self.need = {}                 # tkey -> largest render px per plane unit over the move (prescan)

    def prescan(self, scene, camfn, xf, span, n=14):
        """Sample the move: the largest density every plane / box face is seen at (render px per plane unit)."""
        from .core import CFG
        t0, t1 = span
        for j in range(n):
            cam = camfn(t0 + (t1 - t0) * j / (n - 1))
            for it in scene.items:
                if it.kind == 'plane':
                    O, U, V, w, h, draw, two, unit, readable = it.data
                    g = plane_geom(cam, xf, O, U, V, w, h, two, unit, readable)
                    if g is not None:
                        k_ = (id(it),)
                        self.need[k_] = max(self.need.get(k_, 0.0), _px_per_unit(g[0], g[1]) * CFG.k)
                elif it.kind == 'box':
                    spec, faces, allc, line, lw = it.data
                    for side, (O, U, V, w, h, nrm) in spec.items():
                        f = faces.get(side, allc)
                        if f is None or w <= 0 or h <= 0: continue
                        g = plane_geom(cam, xf, O, U, V, w, h, True, 0.01, False)
                        if g is not None:
                            k_ = (id(it), side)
                            self.need[k_] = max(self.need.get(k_, 0.0), _px_per_unit(g[0], g[1]) * CFG.k)
        self.need['_scanned'] = 1.0

    def get(self, key, w, h, unit, paint_fn, smooth=False):
        e = dict.get(self, key)
        if e is not None: return e
        from .core import CFG, surface_for, image_from
        k = self.TEX_PX * (unit / 0.01) * CFG.rw / 2560.0
        nd = self.need.get(key[:-2])
        if nd is not None: k = max(0.5 * (unit / 0.01) * CFG.rw / 2560.0, min(nd * 1.05, 4 * k))   # what the move asks, up to 4x
        if smooth: k = min(k, 0.9 * (unit / 0.01))        # flat colour + light washes: smooth gradients
        k = min(k, self.MAX_SIDE / max(w, 1e-3), self.MAX_SIDE / max(h, 1e-3), math.sqrt(self.MAX_PIX / max(1e-3, w * h)))
        tw, th = max(2, int(math.ceil(w * k))), max(2, int(math.ceil(h * k)))
        arr = np.zeros((th, tw, 4), np.uint8)
        srf = surface_for(arr); cv = srf.getCanvas()
        cv.scale(tw / max(w, 1e-6), th / max(h, 1e-6))
        paint_fn(Pen(cv))
        del cv, srf
        img = image_from(arr, copy=True).withDefaultMipmaps()
        e = (img, k)
        self[key] = e
        return e


_TEX_SAMPLING = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)


def _px_per_unit(Hm, pts):
    """Largest local scale (design px per plane unit) of homography Hm over the plane points pts."""
    best = 0.0
    for s, t in pts:
        p = Hm @ np.array([s, t, 1.0])
        w = p[2]
        if abs(w) < 1e-9: continue
        J = (Hm[:2, :2] * w - np.outer(p[:2], Hm[2, :2])) / (w * w)
        best = max(best, math.sqrt(abs(J[0, 0] * J[1, 1] - J[0, 1] * J[1, 0])))
    return best


class CamPath3:
    """A Cam3 that moves: keys [(t, pos, look, fov, roll)] (look a point; fov / roll may be None to keep the last).
    Positions, yaw / pitch (from look), fov and roll are interpolated per channel with a monotone cubic through the keys
    (no overshoot, continuous speed) under `warp` (a function film time -> path time, e.g. an eased glide). at(t) caches
    the last Cam3."""

    def __init__(self, keys, warp=None, shift=(0.0, 0.0)):
        ks = sorted(keys, key=lambda k: k[0])
        self.ts = [float(k[0]) for k in ks]
        rows = []
        prev_yaw = None
        last_fov, last_roll = 70.0, 0.0
        for k in ks:
            pos = v3(k[1]); look = v3(k[2])
            d = look - pos
            yaw = math.degrees(math.atan2(d[0], d[2])); pitch = math.degrees(math.atan2(d[1], math.hypot(d[0], d[2])))
            if prev_yaw is not None:                                    # unwrap: turn the short way
                while yaw - prev_yaw > 180: yaw -= 360
                while yaw - prev_yaw < -180: yaw += 360
            prev_yaw = yaw
            fov = float(k[3]) if len(k) > 3 and k[3] is not None else last_fov
            roll = float(k[4]) if len(k) > 4 and k[4] is not None else last_roll
            last_fov, last_roll = fov, roll
            rows.append([pos[0], pos[1], pos[2], yaw, pitch, fov, roll])
        self.vals = np.array(rows, np.float64)
        self.warp = warp or (lambda t: t)
        self.shift = shift
        self._last = (None, None)

    def _raw(self, u):
        return np.array([mono_cubic(self.ts, self.vals[:, j], u) for j in range(self.vals.shape[1])])

    def state(self, t):
        u = self.warp(t)
        if len(self.ts) > 2 and self.ts[0] < u < self.ts[-1]:
            if not hasattr(self, '_arc'):
                self._arc = ArcBlend(self.ts, self._raw, (1.0, 1.0, 1.0, 1 / 35.0, 1 / 35.0, 1 / 30.0, 1 / 20.0))
            u = self._arc(u)
        return self._raw(u)

    def at(self, t):
        if self._last[0] == t: return self._last[1]
        v = self.state(t)
        c = Cam3((v[0], v[1], v[2]), yaw=v[3], pitch=v[4], roll=v[6], fov=v[5], shift=self.shift)
        self._last = (t, c)
        return c

    __call__ = at


class ArcBlend:
    """Review round 2 (M20): no stop at a key. A per-channel monotone cubic has a zero tangent wherever a channel turns
    (the camera passes the swimsuits and swings back: every channel slows at once and the move nearly stops). This
    re-times the path: the path time u is moved so the travelled distance (metres of position, degrees of turn, fov ...
    weighted into one measure) is a blend of the keyed timing and an even pace along the path. The camera still passes
    through every key, near its time, but its speed never drops to zero inside the move (the eased ends stay the warp's)."""

    def __init__(self, ts, fn, weights, lam=0.6, n=480):
        self.t0, self.t1 = float(ts[0]), float(ts[-1])
        us = np.linspace(self.t0, self.t1, n)
        V = np.array([fn(u) for u in us])
        w = np.asarray(weights, np.float64)[:V.shape[1]]
        d = np.sqrt((((V[1:] - V[:-1]) * w) ** 2).sum(1))
        S = np.concatenate([[0.0], np.cumsum(d)])
        self.us, self.S, self.lam = us, S, float(lam)
        self.ok = S[-1] > 1e-6

    def __call__(self, u):
        if not self.ok or u <= self.t0 or u >= self.t1: return u
        Sk = float(np.interp(u, self.us, self.S))
        Su = self.S[-1] * (u - self.t0) / (self.t1 - self.t0)
        St = (1.0 - self.lam) * Sk + self.lam * Su
        return float(np.interp(St, self.S, self.us))


def mono_cubic(xs, ys, x):
    """Monotone cubic Hermite (Fritsch-Carlson) through (xs, ys) evaluated at x; holds outside the range."""
    n = len(xs)
    if n == 1 or x <= xs[0]: return float(ys[0])
    if x >= xs[-1]: return float(ys[-1])
    i = max(0, min(n - 2, int(np.searchsorted(xs, x, side='right')) - 1))
    h = [xs[j + 1] - xs[j] for j in range(n - 1)]
    dl = [(ys[j + 1] - ys[j]) / max(1e-9, h[j]) for j in range(n - 1)]
    def tan(j):
        if j == 0: return dl[0] if n == 2 else _end_tan(h[0], h[1], dl[0], dl[1])
        if j == n - 1: return dl[-1] if n == 2 else _end_tan(h[-1], h[-2], dl[-1], dl[-2])
        if dl[j - 1] * dl[j] <= 0: return 0.0
        w1, w2 = 2 * h[j] + h[j - 1], h[j] + 2 * h[j - 1]
        return (w1 + w2) / (w1 / dl[j - 1] + w2 / dl[j])
    m0, m1 = tan(i), tan(i + 1)
    s = (x - xs[i]) / max(1e-9, h[i])
    h00 = (1 + 2 * s) * (1 - s) ** 2; h10 = s * (1 - s) ** 2; h01 = s * s * (3 - 2 * s); h11 = s * s * (s - 1)
    return float(h00 * ys[i] + h10 * h[i] * m0 + h01 * ys[i + 1] + h11 * h[i] * m1)


def _end_tan(h0, h1, d0, d1):
    m = ((2 * h0 + h1) * d0 - h0 * d1) / (h0 + h1)
    if m * d0 <= 0: return 0.0
    if d0 * d1 <= 0 and abs(m) > abs(3 * d0): return 3 * d0
    return m


def glide(t0, t1, v0=0.4, v1=0.4, ramp=0.7):
    """Time warp for a move from t0 to t1 (returns path time): the speed starts at v0 of the cruise speed, eases up over
    `ramp` s, cruises, and eases down to v1 at the end (v = 1: no ease at that end). A camera that is alive at the cut
    and never snaps from rest; the eases are cosine ramps (no jerk)."""
    D = max(1e-6, t1 - t0)
    r = min(ramp, D / 3.0)

    def area(x):            # integral of the unscaled speed from 0 to x
        if x <= 0: return 0.0
        a = 0.0
        if r > 0:
            xa = min(x, r)
            a += v0 * xa + (1 - v0) * (xa / 2 - r / (2 * math.pi) * math.sin(math.pi * xa / r))
        if x > r: a += min(x, D - r) - r
        if x > D - r and r > 0:
            xb = min(x, D) - (D - r)
            # speed from 1 down to v1: 1 - (1 - v1) (1 - cos(pi xb / r)) / 2
            a += xb - (1 - v1) * (xb / 2 - r / (2 * math.pi) * math.sin(math.pi * xb / r))
        return a
    A = area(D)
    vend0, vend1 = v0 * D / A, v1 * D / A

    def warp(t):
        x = t - t0
        if x < 0: return t0 + vend0 * x                 # extrapolate with the end speeds (dissolves render outside)
        if x > D: return t1 + vend1 * (x - D)
        return t0 + area(x) * D / A
    return warp


LIVE_BAND_RES = 0.5          # travelling shots at full size: the room bands rasterise at half resolution (Scene3.live_bands)

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


def plane_geom(cam, xf, O, U, V, w, h, two_sided=True, unit=0.01, readable=True):
    """(Hm, visible polygon in plane units) of a plane for this camera, or None when it is culled or out of view."""
    O = v3(O); U = v3(U); V = v3(V)
    Ow, Uw, Vw = xf.p(O), xf.d(U), xf.d(V)
    if xf.layout_flip and xf.mirrors and readable:
        if abs(Uw[0]) > 0.5 or (abs(Uw[0]) <= 0.5 and abs(Vw[0]) <= 0.5):
            Ow = Ow + Uw * (w * unit); Uw = -Uw
        else:
            Ow = Ow + Vw * (h * unit); Vw = -Vw
    n = np.cross(Uw, Vw)
    if not two_sided and np.dot(n, cam.C - Ow) <= 0: return None
    Hm, (a, b, c) = cam.H(Ow, Uw, Vw, unit)
    vis = [(0.0, 0.0), (w, 0.0), (w, h), (0.0, h)]
    for fn in _frustum_fns(cam, a, b, c, cam.near):
        vis = _clip_halfplane(vis, fn)
        if len(vis) < 3: return None
    pr = [Hm @ np.array([s, t, 1.0]) for s, t in vis]
    xs = [p[0] / p[2] for p in pr]; ys = [p[1] / p[2] for p in pr]
    if max(xs) < -400 or min(xs) > 2320 or max(ys) < -300 or min(ys) > 1380: return None
    return Hm, vis


def draw_plane(pen, cam, xf, O, U, V, w, h, draw, two_sided=True, unit=0.01, lights=None, readable=True, tex=None, tkey=None,
               smooth=False):
    """Draw a w x h plane (plane units, default cm) through its homography; content clipped to the part in front of the
    camera. With a layout-flipping transform the plane's U axis is turned back so text stays readable. `lights` (model
    space) are washed over the content. tex (a TexCache) + tkey: draw the plane from its baked texture when it is not
    close to the camera."""
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
    if tex is not None and tkey is not None:
        from .core import CFG
        need = _px_per_unit(Hm, vis) * CFG.k
        flip_r = bool(xf.layout_flip and xf.mirrors and readable)
        side = 1
        if lights:
            n0 = norm(np.cross(U0 if not flip_r else Uw, V0 if not flip_r else Vw))
            vp = xf_inv_point(xf, cam.C) if not flip_r else cam.C
            side = 1 if np.dot(vp - (O0 if not flip_r else Ow), n0) >= 0 else -1
        key = tuple(tkey) + (side, flip_r)
        ent = dict.get(tex, key)
        k_est = ent[1] if ent is not None else TexCache.TEX_PX * (unit / 0.01) * CFG.rw / 2560.0
        if ent is None and tex.need.get(tuple(tkey)) is not None:
            k_est = min(tex.need[tuple(tkey)] * 1.05, 4 * k_est)
        vec = tex.__dict__.setdefault('vec', set())             # sticky: a plane that came close stays vector drawn
        if not smooth and need > TexCache.TEX_NEAR * k_est: vec.add(key)   # (flipping texture / vector flickered)
        # a plane that reaches behind the lens (the floor under a travelling camera) is always filled from its texture
        # through the visible polygon: vector content drawn through a perspective matrix that crosses the camera plane
        # came out black or missing for single frames
        behind = any((Hm @ np.array([s_, t_, 1.0]))[2] <= 1e-6 for s_, t_ in ((0.0, 0.0), (w, 0.0), (w, h), (0.0, h)))
        if smooth or behind or key not in vec:
            def paint_fn(p):
                lw_ = p.lw
                if lights: p.cv.saveLayer(None, None)
                draw(p, w, h)
                if lights:
                    p.cv.saveLayer(None, skia.Paint(BlendMode=skia.BlendMode.kSrcATop))
                    if flip_r:
                        Lm = [(xf.p(P), c, a, r, b, nm) for (P, c, a, r, b, nm) in lights]
                        _apply_lights(p, Ow, Uw, Vw, w, h, Lm, unit, cam.C)
                    else:
                        _apply_lights(p, O0, U0, V0, w, h, lights, unit, xf_inv_point(xf, cam.C))
                    p.cv.restore(); p.cv.restore()
                p.lw = lw_
            img, kk = tex.get(key, w, h, unit, paint_fn, smooth)
            # the texture fills only the visible polygon (all of it in front of the lens): drawing the whole image rect
            # through a perspective matrix whose far part lies behind the camera dropped or blackened near floor strips
            sh_ = img.makeShader(skia.TileMode.kClamp, skia.TileMode.kClamp, _TEX_SAMPLING,
                                 skia.Matrix.Scale(w / max(1, img.width()), h / max(1, img.height())))
            cv.save()
            cv.concat(_skmat(Hm))
            cv.drawPath(poly(vis), skia.Paint(Shader=sh_, AntiAlias=True))
            cv.restore()
            return
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
