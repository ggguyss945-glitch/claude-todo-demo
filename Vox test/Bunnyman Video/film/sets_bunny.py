"""sets_bunny.py: the sets of "If The Bunnyman Asks You To Close Your Eyes... DON'T COUNT TO SEVEN".

Run inside sets.py's namespace at import (like characters_bunny.py inside characters.py), so everything here is part of
`sets`:  import sets as ST;  sp = ST.ob_living('couch').  The older films' builders are unchanged. See SETS.md.

THE HOUSE: one floor plan in metres (x right when facing the back of the house, y from the front wall (Orchard Road) back
toward the woods, Y up; ground floor Y 0, upstairs floor UP_Y, attic floor ATTIC_Y). Every interior and exterior view is a
camera (BView: any yaw, a shift-lens horizon, eye height) placed in that plan, so a cut keeps every wall, door, lamp and
chair where the last shot had it. PLAN_MAP draws the plan with every camera (tools/sets_sheet.py -> floorplan.jpg).

STAGING DATA (the owner's notes: nothing floats, nobody stands on furniture, props stay on surfaces):
  sp.spot(x, y, Y=0, note) -> Spot      a plan point -> screen x, y, layer depth, ppm (px per metre there) and the
                                       height of a 1.85 m adult; characters: height = CH.height_px(who, spot.ppm),
                                       Acting.place(spot.x, spot.y), Layer(spot.depth, ...). Spot iterates like Anchor.
  sp.anchors[name]                     named Spots: kind 'stand' (feet on the floor), 'seat' (+ seat_y: sit_on(seat_y)),
                                       'kneel', 'lie' (y = the surface under the body), 'surface' (a prop resting there:
                                       px_per_cm = ppm / 100), 'point' (peephole, mail slot, knob, switch: head_to / reach_to
                                       targets). Each has .turn: the cast `turn` for the way the set expects them to face.
  sp.ppm_at(x, y), sp.floor_y(x, y)    depth-to-scale rule: ppm = S / depth (depth = distance along the view axis);
                                       a figure of real height m is m * ppm design px tall where its feet are.
  sp.pick(sx, sy, Y=0)                 screen point -> (x, y) on the plan plane Y (click a still, get the plan point).
  sp.turn_for(x, y, fx, fy)            the cast `turn` of a figure at (x, y) facing plan direction (fx, fy).
  sp.walkable(x, y)                    (ok, why): inside the room's floor and outside every furniture footprint.
  sp.shadow(x, y, r, k)                a contact-shadow Layer on the floor (perspective-correct ellipse, drawn over the floor).
  sp.light_kw(x, y, Y=1.2, floor=0.45) Layer(tint=..., dim=...) so a figure takes the room's light at that point.
  sp.info['view'], ['cam_env'], ['plan'], ['occluders'] (which furniture layers sit in front of what).
LIGHT is modelled per face: every wall, floor, box face is drawn as albedo in its own frame and multiplied by the exact
light of each lamp on that plane (radial falloff about the lamp's foot point, Lambert term), moonlight patches projected
through window panes and soft ambient occlusion in the seams. A lamp that changes in the shot is its own 'plus' layer
(level spec as the dummy film: number | f(t) | dict(flick=, out=, on=, off=)).
"""
import math
import numpy as np
import skia

_BUNNY_FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fonts')
_BTF = {}


def bfont(name):
    """Typefaces: 'hand' (Mom's neat print), 'cursive' (the diary's perfect hand), 'cursive_b', 'kid' (crayon letters),
    'masthead' (the Courier's blackletter), 'script' (Pemberton's sign), 'vhs' (camcorder stamp), 'formal', 'caveat',
    'caveat_b', 'head' / 'head_r' (condensed headline), 'serif', 'serif_b', 'serif_i', 'sans', 'sans_b', 'mono'; or a
    Montserrat weight (600..900)."""
    if isinstance(name, int): return typeface(name)
    if name in _BTF: return _BTF[name]
    ex = os.path.join(_BUNNY_FONTS, 'extra')
    f = {'hand': os.path.join(ex, 'PatrickHand-Regular.ttf'), 'cursive': os.path.join(ex, 'DancingScript-Regular.ttf'),
         'cursive_b': os.path.join(ex, 'DancingScript-Bold.ttf'), 'kid': os.path.join(ex, 'Schoolbell-Regular.ttf'),
         'masthead': os.path.join(ex, 'UnifrakturMaguntia-Book.ttf'), 'script': os.path.join(ex, 'Lobster-Regular.ttf'),
         'vhs': os.path.join(ex, 'VT323-Regular.ttf'), 'formal': os.path.join(ex, 'Parisienne-Regular.ttf'),
         'caveat': os.path.join(ex, 'Caveat-Regular.ttf'), 'caveat_b': os.path.join(ex, 'Caveat-Bold.ttf'),
         'head': os.path.join(ex, 'Oswald-Bold.ttf'), 'head_r': os.path.join(ex, 'Oswald-Regular.ttf'),
         'serif': '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf',
         'serif_b': '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf',
         'serif_i': '/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf',
         'sans': '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
         'sans_b': '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
         'mono': '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf'}[name]
    tf = skia.Typeface.MakeFromFile(f)
    if tf is None: tf = typeface(700)
    _BTF[name] = tf
    return tf


def btext(pen, s, x, y, font='hand', size=30, c='#222222', a=255, align='left', spacing=0.0, skew=0.0, sx=1.0):
    """Draw text with one of the bfont() faces (x, y = baseline start / centre / end by align). Returns the width."""
    f = skia.Font(bfont(font), size)
    f.setSubpixel(True); f.setEdging(skia.Font.Edging.kAntiAlias)
    if skew: f.setSkewX(skew)
    if sx != 1.0: f.setScaleX(sx)
    g = f.textToGlyphs(s); ws = f.getWidths(g)
    w = sum(ws) + spacing * size * max(0, len(g) - 1)
    x0 = x - (w / 2 if align == 'center' else (w if align == 'right' else 0.0))
    p = skia.Paint(Color=col(c, a), AntiAlias=True)
    if spacing == 0.0:
        pen.cv.drawString(s, x0, y, f, p)
    else:
        xx = x0
        for ch_, wd in zip(s, ws):
            pen.cv.drawString(ch_, xx, y, f, p); xx += wd + spacing * size
    return w


def btext_width(s, font='hand', size=30, spacing=0.0, sx=1.0):
    f = skia.Font(bfont(font), size)
    if sx != 1.0: f.setScaleX(sx)
    g = f.textToGlyphs(s)
    return sum(f.getWidths(g)) + spacing * size * max(0, len(g) - 1)


def btext_path(s, x, y, font='hand', size=30, align='left'):
    """Text as a skia path (for crayon strokes / clipping / warping)."""
    f = skia.Font(bfont(font), size)
    w = btext_width(s, font, size)
    x0 = x - (w / 2 if align == 'center' else (w if align == 'right' else 0.0))
    blob = skia.TextBlob.MakeFromString(s, f)
    path = skia.Path()
    g = f.textToGlyphs(s); ws = f.getWidths(g); xx = x0
    for gid, wd in zip(g, ws):
        gp = f.getPath(gid)
        if gp is not None:
            gp.offset(xx, y); path.addPath(gp)
        xx += wd
    return path


# ====================================================================================================== the camera
class BView:
    """A camera on the house plan with any yaw. Plan coordinates (metres): x, y on the floor plan, Y up. yaw (degrees):
    0 faces +y (toward the back of the house / the woods), 90 faces +x, 180 faces the front (-y), -90 faces -x. S = design
    px per metre at depth 1, horizon = design y of eye level (a shift lens: verticals stay vertical), cam_h = eye height
    (absolute Y). Methods take PLAN coordinates: p(x, Y, y) -> design (sx, sy); d(x, y) = depth along the view axis;
    s(x, y) = px per metre there; spot(x, y, Y) -> Spot; pick(sx, sy, Y) -> plan (x, y)."""

    def __init__(self, S, horizon, cam_h, cam_x, cam_y, yaw=0.0, cx=960.0, near=0.12, name=''):
        self.S, self.h, self.cam_h, self.cx = float(S), float(horizon), float(cam_h), float(cx)
        self.hx, self.hy, self.yaw, self.near, self.name = float(cam_x), float(cam_y), float(yaw), float(near), name
        th = math.radians(yaw)
        self.fx, self.fy = math.sin(th), math.cos(th)            # forward (plan)
        self.rx, self.ry = math.cos(th), -math.sin(th)           # screen right (plan)

    def __repr__(self): return 'BView(%s: S=%.0f h=%.0f eye=%.2f at (%.2f, %.2f) yaw %.0f)' % (self.name, self.S, self.h, self.cam_h, self.hx, self.hy, self.yaw)

    def d(self, x, y): return (x - self.hx) * self.fx + (y - self.hy) * self.fy

    def u(self, x, y): return (x - self.hx) * self.rx + (y - self.hy) * self.ry

    def p(self, x, Y, y):
        D = max(self.near, self.d(x, y)); k = self.S / D
        return (self.cx + self.u(x, y) * k, self.h - (Y - self.cam_h) * k)

    def s(self, x, y): return self.S / max(self.near, self.d(x, y))

    def poly3(self, pts, closed=True):
        """[(x, Y, y), ...] -> skia path, clipped to the near plane."""
        q = _clip_near3(self, pts) if closed else pts
        if len(q) < 2: return skia.Path()
        return poly([self.p(*a) for a in q], closed)

    def visible(self, P, n):
        """Is a surface at P (x, Y, y) with normal n (nx, nY, ny) facing the camera?"""
        return (self.hx - P[0]) * n[0] + (self.cam_h - P[1]) * n[1] + (self.hy - P[2]) * n[2] > 1e-6

    def pick(self, sx, sy, Y=0.0):
        """Screen design point -> plan (x, y) on the horizontal plane at height Y (None if that plane is not there)."""
        dy = sy - self.h
        if abs(dy) < 1e-6 or (self.cam_h - Y) / dy <= 0: return None
        D = (self.cam_h - Y) * self.S / dy
        U = (sx - self.cx) * D / self.S
        return (self.hx + U * self.rx + D * self.fx, self.hy + U * self.ry + D * self.fy)

    def turn_for(self, x, y, fx, fy):
        """The cast's `turn` (0 front, +1 profile to screen right, -1 to screen left, 2 back) for a figure standing at
        plan (x, y) facing plan direction (fx, fy), seen from this camera (uses the real line of sight)."""
        vx, vy = x - self.hx, y - self.hy
        n = math.hypot(vx, vy) or 1.0; vx, vy = vx / n, vy / n
        m = math.hypot(fx, fy) or 1.0; fx, fy = fx / m, fy / m
        toward = -(fx * vx + fy * vy)
        lateral = fx * vy - fy * vx                      # dot with (vy, -vx): the screen-right direction at that spot
        return math.atan2(lateral, toward) / (math.pi / 2)

    def spot(self, x, y, Y=0.0, note='', kind='stand', **kw):
        px, py = self.p(x, Y, y); D = self.d(x, y)
        return Spot(px, py, D, self.S / max(self.near, D), x, y, Y, kind, note, **kw)

    anchor = spot

    def frame_pts(self, pts):
        return [self.p(*q) for q in pts]


def _clip_near3(v, pts, near=None):
    """Sutherland-Hodgman clip of a 3D polygon [(x, Y, y)] to depth >= near."""
    nr = (near if near is not None else v.near) + 1e-4
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        da, db = v.d(a[0], a[2]) - nr, v.d(b[0], b[2]) - nr
        if da >= 0: out.append(a)
        if (da >= 0) != (db >= 0):
            t = da / (da - db)
            out.append(tuple(a[k] + (b[k] - a[k]) * t for k in range(3)))
    return out


class Spot:
    """A staging point: x, y = design px (feet / point) at the home camera, depth = layer depth, ppm = design px per metre
    there, height = design px of a 1.85 m adult standing there (Anchor compatible: iterates as (x, y, depth, height)),
    X, Yp = plan position, Y = height above the ground floor, kind ('stand' | 'seat' | 'kneel' | 'lie' | 'surface' |
    'point'), turn = the cast turn the set expects, seat_y (seats) = design y of the seat top above (x, y), note."""
    __slots__ = ('x', 'y', 'depth', 'ppm', 'height', 'X', 'Yp', 'Y', 'kind', 'note', 'turn', 'seat_y', 'extra')

    def __init__(self, x, y, depth, ppm, X=0.0, Yp=0.0, Y=0.0, kind='stand', note='', turn=None, seat_y=None, **extra):
        self.x, self.y, self.depth, self.ppm = float(x), float(y), float(depth), float(ppm)
        self.height = 1.85 * self.ppm
        self.X, self.Yp, self.Y, self.kind, self.note, self.turn, self.seat_y = X, Yp, Y, kind, note, turn, seat_y
        self.extra = extra

    def __iter__(self): return iter((self.x, self.y, self.depth, self.height))

    def h_px(self, metres): return metres * self.ppm

    def __repr__(self):
        s = 'Spot(%s x=%.0f y=%.0f depth=%.2f ppm=%.1f plan=(%.2f, %.2f, %.2f)' % (self.kind, self.x, self.y, self.depth, self.ppm, self.X, self.Yp, self.Y)
        if self.seat_y is not None: s += ' seat_y=%.0f' % self.seat_y
        if self.turn is not None: s += ' turn=%.2f' % self.turn
        return s + (', ' + self.note if self.note else '') + ')'


# ====================================================================================================== lights
class Lamp:
    """A light for the per-face light maps. kind 'point': position (x, Y, y), reach R (m), colour c, strength k; w = (down,
    side, up) emission weights (a shaded lamp throws most light down); only = face kinds lit ('floor', 'wall', 'ceil',
    'top', 'side', ...) or None for all; sxy = (along face width, along face height) stretch of the pool (gap fans).
    kind 'win': moonlight / sunlight through window panes: panes = [[4 x (x, Y, y)], ...], d = travel direction (x, Y, y),
    soft = penumbra (cm); only lit faces in front of the panes along d. name: for variable lights (layers)."""
    __slots__ = ('kind', 'x', 'Y', 'y', 'R', 'c', 'k', 'w', 'only', 'sxy', 'panes', 'd', 'soft', 'name', 'fall')

    def __init__(self, x=0.0, Y=0.0, y=0.0, R=3.0, c='#ffd8a0', k=1.0, w=(1.0, 1.0, 1.0), only=None, sxy=(1.0, 1.0), kind='point',
                 panes=None, d=None, soft=6.0, name='', fall=2.0):
        self.kind, self.x, self.Y, self.y, self.R, self.c, self.k = kind, float(x), float(Y), float(y), float(R), c, float(k)
        self.w, self.only, self.sxy, self.panes, self.d, self.soft, self.name, self.fall = w, only, sxy, panes, d, soft, name, fall

    def scaled(self, k):
        L = Lamp.__new__(Lamp)
        for a in Lamp.__slots__: setattr(L, a, getattr(self, a))
        L.k = self.k * k
        return L

    def at(self, P, n=None):
        """Light (r, g, b) 0..~2 this lamp gives point P (x, Y, y) with normal n (None: no Lambert term)."""
        if self.kind != 'point': return (0.0, 0.0, 0.0)
        dx, dY, dy = P[0] - self.x, P[1] - self.Y, P[2] - self.y
        dist = math.sqrt(dx * dx + dY * dY + dy * dy) + 1e-6
        if dist >= self.R: return (0.0, 0.0, 0.0)
        g = max(0.0, 1.0 - dist / self.R) ** self.fall
        lam = 1.0
        if n is not None:
            lam = max(0.0, -(dx * n[0] + dY * n[1] + dy * n[2]) / dist)
        dw = self.w[0] if dY < -0.3 * dist else (self.w[2] if dY > 0.3 * dist else self.w[1])
        r, gg, b = rgb(self.c)
        k = self.k * g * lam * dw / 255.0
        return (r * k, gg * k, b * k)


class _LightCtx:
    """The lighting faces use while a layer's art is drawn: ambient hex (None = unlit albedo), lights [Lamp], ao (0..1)."""
    amb = None
    lights = ()
    ao = 1.0
    gain = 1.0


_LC = _LightCtx()


class lighting:
    """with lighting(amb, lights, ao=1.0): ...   sets the light context for the faces drawn inside."""

    def __init__(self, amb, lights=(), ao=1.0):
        self.v = (amb, list(lights), ao)

    def __enter__(self):
        self.old = (_LC.amb, _LC.lights, _LC.ao)
        _LC.amb, _LC.lights, _LC.ao = self.v
        return self

    def __exit__(self, *a):
        _LC.amb, _LC.lights, _LC.ao = self.old


def light_at(P, n=None, amb=None, lights=None):
    """(r, g, b) multiplier (1 = the albedo as drawn) at point P with normal n under the current (or given) lighting."""
    amb = _LC.amb if amb is None else amb
    lights = _LC.lights if lights is None else lights
    if amb is None: return (1.0, 1.0, 1.0)
    r, g, b = (q / 255.0 for q in rgb(amb))
    for L in lights:
        if L.kind != 'point': continue
        lr, lg, lb = L.at(P, n)
        r += lr; g += lg; b += lb
    return (r, g, b)


def lit(c, P, n=None, k=1.0):
    """A colour as it looks lit at P (vertex lighting for small props drawn outside faces)."""
    m = light_at(P, n)
    r, g, b = rgb(c)
    return '#%02x%02x%02x' % tuple(int(clamp(q * mm * k, 0, 255)) for q, mm in zip((r, g, b), m))


# ====================================================================================================== faces
def fmat(v, O, U, V):
    """Perspective matrix mapping a face frame (a, b) -> design px, where the 3D point is O + a U + b V (U, V = metres
    per frame unit)."""
    def comps(P, pt):
        if pt: dx, dy, up = P[0] - v.hx, P[2] - v.hy, P[1] - v.cam_h
        else: dx, dy, up = P[0], P[2], P[1]
        return dx * v.rx + dy * v.ry, up, dx * v.fx + dy * v.fy
    Ro, Uo, Do = comps(O, True); Ru, Uu, Du = comps(U, False); Rv, Uv, Dv = comps(V, False)
    S, cx, h = v.S, v.cx, v.h
    k = 1.0 / max(1e-6, max(abs(Do), 1e-3))
    m = skia.Matrix()
    m.setAll((cx * Du + S * Ru) * k, (cx * Dv + S * Rv) * k, (cx * Do + S * Ro) * k,
             (h * Du - S * Uu) * k, (h * Dv - S * Uv) * k, (h * Do - S * Uo) * k,
             Du * k, Dv * k, Do * k)
    return m, (Do, Du, Dv)


def _sub3(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add3(a, b, k=1.0): return (a[0] + b[0] * k, a[1] + b[1] * k, a[2] + b[2] * k)


def _dot3(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm3(a):
    n = math.sqrt(_dot3(a, a)) or 1.0
    return (a[0] / n, a[1] / n, a[2] / n)


class Face:
    """A planar rectangle: O = top-left corner (x, Y, y) in metres, Uu / Vu = unit vectors along its width (art x) and
    down its height (art y), W, H in cm (art frame), n = outward normal, kind for the light filters ('wall', 'floor',
    'ceil', 'top', 'side', 'bottom', 'front', 'back')."""
    __slots__ = ('O', 'Uu', 'Vu', 'W', 'H', 'n', 'kind')

    def __init__(self, O, Uu, Vu, W, H, n, kind='wall'):
        self.O, self.Uu, self.Vu, self.W, self.H, self.n, self.kind = O, _norm3(Uu), _norm3(Vu), float(W), float(H), _norm3(n), kind

    def pt(self, a, b):
        """Frame (cm) -> 3D."""
        return _add3(_add3(self.O, self.Uu, a / 100.0), self.Vu, b / 100.0)

    def uv(self, P):
        """3D point (on the plane) -> frame (cm)."""
        d = _sub3(P, self.O)
        return _dot3(d, self.Uu) * 100.0, _dot3(d, self.Vu) * 100.0

    def corners(self):
        return [self.pt(0, 0), self.pt(self.W, 0), self.pt(self.W, self.H), self.pt(0, self.H)]

    def centre(self): return self.pt(self.W / 2, self.H / 2)


def _near_clip_uv(Ddat, W, H, near):
    """The part of the face frame rectangle with depth >= near, as a list of (a, b) or None if all of it, [] if none."""
    Do, Du, Dv = Ddat
    pts = [(0.0, 0.0), (W, 0.0), (W, H), (0.0, H)]
    ds = [Do + a * Du + b * Dv - near for (a, b) in pts]
    if min(ds) >= 0: return None
    if max(ds) < 0: return []
    out = []
    for i in range(4):
        a, b = pts[i], pts[(i + 1) % 4]; da, db = ds[i], ds[(i + 1) % 4]
        if da >= 0: out.append(a)
        if (da >= 0) != (db >= 0):
            t = da / (da - db); out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


_BLEND_MOD = skia.BlendMode.kModulate
_BLEND_PLUS = skia.BlendMode.kPlus


def draw_face(pen, v, F, art=None, fill='#808080', holes=None, ao=None, line=True, lw=None, unlit=False, two_sided=False,
              outline=None, shape=None):
    """Draw face F if it faces the camera: fill (albedo), art(pen, W, H) in the cm frame (y down), cut holes (cm paths in
    the frame), multiply by the current light context (per-face light map: ambient + every Lamp on this plane + window
    patches), soft ambient occlusion along the edges in `ao` ({'top': cm, 'bottom': cm, 'left': cm, 'right': cm} or a
    number = all edges), and an outline in screen space. shape = a cm path: the face's silhouette instead of the full
    rectangle (rounded cushions, a wingback). Returns True if drawn."""
    if not two_sided and not v.visible(F.O, F.n):
        return False
    m, Dd = fmat(v, F.O, _scale3(F.Uu, 0.01), _scale3(F.Vu, 0.01))
    clip_uv = _near_clip_uv(Dd, F.W, F.H, v.near)
    if clip_uv is not None and len(clip_uv) < 3: return False
    cv = pen.cv
    cv.save()
    cv.concat(m)
    base = shape if shape is not None else rect(0, 0, F.W, F.H)
    region = base if clip_uv is None else inter(base, poly(clip_uv))
    if holes:
        for hp in holes: region = minus(region, hp)
    cv.clipPath(region, skia.ClipOp.kIntersect, True)
    if fill is not None: pen.fill(rect(-2, -2, F.W + 4, F.H + 4), fill)
    if art is not None: art(pen, F.W, F.H)
    if not unlit and _LC.amb is not None:
        _light_map(pen, v, F)
    if ao is None: ao = _LC.ao and _AO_DEFAULT.get(F.kind)
    if ao:
        _ao_edges(pen, F.W, F.H, ao, _LC.ao)
    cv.restore()
    if line:
        outl = region if shape is not None or holes else None
        if outl is None:
            q = _clip_near3(v, F.corners())
            path = poly([v.p(*a) for a in q]) if len(q) >= 3 else None
        else:
            path = skia.Path(outl); path.transform(m)
        if path is not None:
            c = F.centre(); D = max(v.near, v.d(c[0], c[2]))
            w = lw if lw is not None else clamp(0.011 * v.S / D, 0.7, 3.2)
            pen.line(path, w, outline or LINE, 200)
    return True


def _scale3(a, k): return (a[0] * k, a[1] * k, a[2] * k)


_AMB_K = {'top': 1.18, 'floor': 1.05, 'ceil': 0.78, 'bottom': 0.5, 'wall': 0.95, 'side': 0.82, 'front': 0.95, 'back': 0.8}


def _amb_scaled(c, k):
    r, g, b = rgb(c)
    return '#%02x%02x%02x' % (int(clamp(r * k, 0, 255)), int(clamp(g * k, 0, 255)), int(clamp(b * k, 0, 255)))


_AO_DEFAULT = {'wall': {'bottom': 26, 'top': 16, 'left': 14, 'right': 14}, 'floor': 22, 'ceil': 18}


def _ao_edges(pen, W, H, ao, k=1.0):
    if not isinstance(ao, dict): ao = {'top': ao, 'bottom': ao, 'left': ao, 'right': ao}
    a0 = 120 * k
    for side, wd in ao.items():
        if not wd: continue
        wd = min(wd, (H if side in ('top', 'bottom') else W) * 0.45)
        if side == 'top': pen.linear(rect(0, 0, W, wd), 0, 0, 0, wd, [(0, '#000000', a0), (1, '#000000', 0)])
        elif side == 'bottom': pen.linear(rect(0, H - wd, W, wd), 0, H, 0, H - wd, [(0, '#000000', a0 * 1.15), (1, '#000000', 0)])
        elif side == 'left': pen.linear(rect(0, 0, wd, H), 0, 0, wd, 0, [(0, '#000000', a0 * 0.8), (1, '#000000', 0)])
        elif side == 'right': pen.linear(rect(W - wd, 0, wd, H), W, 0, W - wd, 0, [(0, '#000000', a0 * 0.8), (1, '#000000', 0)])


_FALL_N = 9


def _light_map(pen, v, F):
    """Multiply what is drawn in the face frame by the light reaching that plane (inside the face clip)."""
    cv = pen.cv
    cv.saveLayer(None, skia.Paint(BlendMode=_BLEND_MOD))
    ak = _AMB_K.get(F.kind, 1.0)
    cv.drawColor(col(_amb_scaled(_LC.amb, ak)))
    n = F.n
    for L in _LC.lights:
        if L.only is not None and F.kind not in L.only: continue
        if L.kind == 'point':
            h = (L.x - F.O[0]) * n[0] + (L.Y - F.O[1]) * n[1] + (L.y - F.O[2]) * n[2]
            if h <= 0.005 or h >= L.R: continue
            rho = math.sqrt(L.R * L.R - h * h)
            a, b = F.uv((L.x - h * n[0], L.Y - h * n[1], L.y - h * n[2]))
            dw = L.w[0] if n[1] > 0.7 else (L.w[2] if n[1] < -0.7 else L.w[1])
            r0, g0, b0 = rgb(L.c)
            cs, ps = [], []
            for i in range(_FALL_N + 1):
                u = i / _FALL_N
                r_ = u * rho; dist = math.sqrt(r_ * r_ + h * h)
                I = L.k * dw * max(0.0, 1.0 - dist / L.R) ** L.fall * (h / dist)
                cs.append(skia.Color(int(min(255, r0 * I)), int(min(255, g0 * I)), int(min(255, b0 * I)), 255)); ps.append(u)
            R = rho * 100.0
            mm = skia.Matrix(); mm.setScale(L.sxy[0], L.sxy[1], a, b)
            sh = skia.GradientShader.MakeRadial(skia.Point(a, b), R, cs, ps, skia.TileMode.kClamp, 0, mm)
            cv.drawRect(skia.Rect.MakeLTRB(a - R * L.sxy[0], b - R * L.sxy[1], a + R * L.sxy[0], b + R * L.sxy[1]),
                        skia.Paint(Shader=sh, BlendMode=_BLEND_PLUS))
        elif L.kind == 'win' and L.panes:
            d = L.d
            nd = _dot3(n, d)
            if nd >= -0.02: continue
            r0, g0, b0 = rgb(L.c)
            I = L.k * min(1.0, -nd)
            paint = skia.Paint(Color=skia.Color(int(min(255, r0 * I)), int(min(255, g0 * I)), int(min(255, b0 * I)), 255),
                               BlendMode=_BLEND_PLUS, AntiAlias=True)
            if L.soft: paint.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, L.soft))
            for pane in L.panes:
                q = []
                ok = True
                for P in pane:
                    t = _dot3(n, _sub3(F.O, P)) / nd
                    if t < -1e-3: ok = False; break
                    q.append(F.uv(_add3(P, d, t)))
                if ok and len(q) >= 3:
                    cv.drawPath(poly(q), paint)
    cv.restore()


def wall_face(a, b, Y0, Y1, kind='wall'):
    """The inside face of a wall from plan point a to b (the visible side is on the RIGHT walking a -> b)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    fx, fy = dx / L, dy / L
    return Face((a[0], Y1, a[1]), (fx, 0.0, fy), (0.0, -1.0, 0.0), L * 100.0, (Y1 - Y0) * 100.0, (fy, 0.0, -fx), kind)


def floor_face(x0, x1, y0, y1, Y=0.0, kind='floor'):
    """A floor rectangle (art frame: a = (x - x0) cm, b = (y1 - y) cm: the far edge (y1) at the top)."""
    return Face((x0, Y, y1), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (x1 - x0) * 100.0, (y1 - y0) * 100.0, (0.0, 1.0, 0.0), kind)


def ceil_face(x0, x1, y0, y1, Y, kind='ceil'):
    """A ceiling rectangle seen from below (art: a = (x - x0) cm, b = (y - y0) cm)."""
    return Face((x0, Y, y0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (x1 - x0) * 100.0, (y1 - y0) * 100.0, (0.0, -1.0, 0.0), kind)


def floor_uv(x0, y1, x, y):
    """Plan point -> floor_face art coordinates (cm)."""
    return (x - x0) * 100.0, (y1 - y) * 100.0


# ---------------------------------------------------------------------------------------------- oriented boxes
class Box:
    """An oriented box on the plan: centre (cx, cy), width w (along its front), depth d, heights Y0..Y1, facing angle fa
    (degrees: 0 = its front faces -y (the front of the house), 90 = faces +x, 180 = +y, -90 = -x)."""
    __slots__ = ('cx', 'cy', 'w', 'd', 'Y0', 'Y1', 'fa', 'U', 'N')

    def __init__(self, cx, cy, w, d, Y0, Y1, fa=0.0):
        self.cx, self.cy, self.w, self.d, self.Y0, self.Y1, self.fa = cx, cy, w, d, Y0, Y1, fa
        th = math.radians(fa)
        self.N = (math.sin(th), -math.cos(th))           # front normal (plan)
        self.U = (math.cos(th), math.sin(th))            # left -> right across the front, seen from the front

    def at(self, u, n, Y):
        """Local (u across from the centre, n toward the front from the centre, Y) -> plan (x, Y, y)."""
        return (self.cx + self.U[0] * u + self.N[0] * n, Y, self.cy + self.U[1] * u + self.N[1] * n)

    def faces(self):
        w2, d2 = self.w / 2, self.d / 2
        U3 = (self.U[0], 0.0, self.U[1]); N3 = (self.N[0], 0.0, self.N[1]); dn = (0.0, -1.0, 0.0)
        H = (self.Y1 - self.Y0) * 100.0
        f = {}
        f['front'] = Face(self.at(-w2, d2, self.Y1), U3, dn, self.w * 100, H, N3, 'front')
        f['back'] = Face(self.at(w2, -d2, self.Y1), _scale3(U3, -1), dn, self.w * 100, H, _scale3(N3, -1), 'back')
        f['left'] = Face(self.at(-w2, -d2, self.Y1), N3, dn, self.d * 100, H, _scale3(U3, -1), 'side')
        f['right'] = Face(self.at(w2, d2, self.Y1), _scale3(N3, -1), dn, self.d * 100, H, U3, 'side')
        f['top'] = Face(self.at(-w2, -d2, self.Y1), U3, N3, self.w * 100, self.d * 100, (0.0, 1.0, 0.0), 'top')
        f['bottom'] = Face(self.at(-w2, d2, self.Y0), U3, _scale3(N3, -1), self.w * 100, self.d * 100, (0.0, -1.0, 0.0), 'bottom')
        return f

    def footprint(self, pad=0.0):
        w2, d2 = self.w / 2 + pad, self.d / 2 + pad
        return [(self.at(u, n, 0)[0], self.at(u, n, 0)[2]) for (u, n) in ((-w2, -d2), (w2, -d2), (w2, d2), (-w2, d2))]

    def depth_from(self, v, which='near'):
        ds = [v.d(x, y) for (x, y) in self.footprint()]
        return min(ds) if which == 'near' else (max(ds) if which == 'far' else sum(ds) / 4)


def draw_box(pen, v, B, mats, line=True, lw=None, skip=()):
    """Draw an oriented Box's visible faces. mats: {face: colour | (colour, art) | dict(fill, art, ao)} with face in
    front/back/left/right/top/bottom; 'all' = default; 'sides' = left/right/back default."""
    fs = B.faces()
    order = sorted(fs.items(), key=lambda kv: -v.d(kv[1].centre()[0], kv[1].centre()[2]))
    for name, F in order:
        if name in skip: continue
        m = mats.get(name) or (mats.get('sides') if name in ('left', 'right', 'back') else None) or mats.get('all')
        if m is None: continue
        if isinstance(m, str): fill, art, ao = m, None, False
        elif isinstance(m, tuple): fill, art, ao = m[0], m[1], False
        else: fill, art, ao = m.get('fill', '#808080'), m.get('art'), m.get('ao', False)
        draw_face(pen, v, F, art, fill, ao=ao, line=line, lw=lw)


def shadow_on_floor(pen, v, pts, Y=0.0, blur_m=0.12, a=150, c='#000000'):
    """A soft shadow polygon on a floor plane (plan points [(x, y)]), drawn in screen space (call inside a floor layer
    after the floor)."""
    q = _clip_near3(v, [(x, Y, y) for (x, y) in pts])
    if len(q) < 3: return
    cx = sum(p_[0] for p_ in q) / len(q); cy = sum(p_[2] for p_ in q) / len(q)
    pen.fill(poly([v.p(*p_) for p_ in q]), c, a, blur=max(1.0, blur_m * v.s(cx, cy)))


def ellipse3(v, x, y, rx, ry, Y=0.0, n=24):
    """A horizontal ellipse on the plan (radii along x / y) as a screen path."""
    pts = [(x + rx * math.cos(2 * math.pi * i / n), Y, y + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]
    q = _clip_near3(v, pts)
    if len(q) < 3: return skia.Path()
    return smooth([v.p(*p_) for p_ in q], True, 0.6)


# ====================================================================================================== layers
def blit(depth, art, name, key, bounds, amb, lights=(), var=(), ao=1.0, order=None, **kw):
    """Static lit layer(s) for one piece of a set (the bunny-film _lit): art(pen) draws faces under the light context.
    Base = albedo x (ambient + steady lights); each variable light (vname, [Lamp], f(t)) is a 'plus' layer = albedo x that
    light alone with alpha = its level (cached; costs nothing at level 0). Steady levels are baked into the base.
    order: draw-order depth (Layer.order) when it must differ from the projection depth."""
    lights = list(lights); dyn = []
    for (vn, vl, kf) in var:
        if not vl: continue
        c = getattr(kf, 'const', None)
        if c is None: dyn.append((vn, vl, kf)); continue
        key = key + ':%s=%.3f' % (vn, c)
        if c > 0.001: lights += [L_.scaled(c) for L_ in vl]

    def base(pen, t):
        with lighting(amb, lights, ao): art(pen)
    L = [Layer(depth, base, name, cache=key, bounds=bounds, **kw)]
    for (vn, vl, kf) in dyn:
        def add(pen, t, vl=vl):
            with lighting('#000000', vl, 0.0): art(pen)
        L.append(Layer(depth, add, name + ':' + vn, cache=key + ':' + vn, bounds=bounds, alpha=kf, blend='plus', **kw))
    if order is not None:
        for l_ in L: l_.order = order
    return L


class BSet(SetPiece):
    """A bunny-film set: SetPiece + the staging API (see the module docstring)."""

    def __init__(self, name, layers, anchors=None, paths=None, lens=None, grade=None, focus=1.0, dof=0.0, cover=None, fx=None,
                 info=None, view=None, room=None):
        SetPiece.__init__(self, name, layers, anchors, paths, lens, grade, focus, dof, cover or FRAME, fx, info)
        self.view = view if view is not None else (info or {}).get('view')
        self.room = room
        if self.view is not None: self.info.setdefault('view', self.view)

    def add(self, *layers):
        s = BSet(self.name, list(self) + [l for l in layers if l is not None], self.anchors, self.paths, self.lens, self.grade,
                 self.focus, self.dof, self.cover, self._fx, self.info, self.view, self.room)
        return s

    def without(self, *names):
        return BSet(self.name, [l for l in self if l.name not in names], self.anchors, self.paths, self.lens, self.grade,
                    self.focus, self.dof, self.cover, self._fx, self.info, self.view, self.room)

    # ---- staging
    def spot(self, x, y, Y=0.0, note='', kind='stand', **kw):
        return self.view.spot(x, y, Y, note, kind, **kw)

    def ppm_at(self, x, y): return self.view.s(x, y)

    def floor_y(self, x, y, Y=0.0): return self.view.p(x, Y, y)[1]

    def pick(self, sx, sy, Y=0.0): return self.view.pick(sx, sy, Y)

    def turn_for(self, x, y, fx, fy): return self.view.turn_for(x, y, fx, fy)

    def walkable(self, x, y):
        """(ok, why) for a figure's feet at plan (x, y): inside one of the room floors in info['floors'] and clear of every
        furniture footprint in info['blocks'] (name -> plan polygon)."""
        fl = self.info.get('floors') or []
        if fl and not any(_in_poly((x, y), q) for q in fl): return False, 'off the floor (outside the room)'
        for nm, q in (self.info.get('blocks') or {}).items():
            if _in_poly((x, y), q): return False, 'inside the footprint of ' + nm
        return True, 'ok'

    def light_kw(self, x, y, Y=1.2, floor=0.45, t_fn=None):
        """Layer kwargs (tint, dim) so a figure at plan (x, y) takes the room's light (steady + variable lamps at their level
        at time t); `floor` keeps faces readable (minimum brightness)."""
        info = self.info
        amb, steady, var = info.get('amb', '#30384c'), info.get('lights', []), info.get('var_lights', [])
        P = (x, Y, y)
        base = light_at(P, None, amb, steady)

        def gains(t):
            r, g, b = base
            for (vn, vl, kf) in var:
                k = kf(t)
                if k <= 0.001: continue
                for L_ in vl:
                    q = L_.at(P, None); r += q[0] * k; g += q[1] * k; b += q[2] * k
            m = max(r, g, b, 1e-3)
            lum = max(floor, min(1.0, m))
            return r / m * lum, g / m * lum, b / m * lum

        def tint(t):
            r, g, b = gains(t); m = max(r, g, b, 1e-3)
            return ('#%02x%02x%02x' % (int(clamp(r / m * 255, 0, 255)), int(clamp(g / m * 255, 0, 255)), int(clamp(b / m * 255, 0, 255))), 1.0)

        def dim(t):
            r, g, b = gains(t); m = max(r, g, b, 1e-3)
            return clamp(1.0 - m / 1.6, 0.0, 0.95)
        return dict(tint=tint, dim=dim)

    def shadow(self, x, y, r=0.32, k=0.5, Y=0.0, name='shadow', rx=None, ry=None, x_fn=None):
        """A soft contact-shadow Layer under a figure standing at plan (x, y) (or x_fn(t) -> (x, y) for a walk): drawn just
        over the floor (Layer.order = the floor's), sized in metres, perspective-correct."""
        v = self.view
        fo = self.info.get('floor_order', 50.0)

        def pos(t): return x_fn(t) if x_fn is not None else (x, y)

        def depth(t):
            px, py = pos(t); return max(0.2, v.d(px, py))

        def draw(pen, t):
            px, py = pos(t)
            D = max(0.2, v.d(px, py)); g = D / 4.0
            pen.cv.save(); pen.cv.translate(960, 540); pen.cv.scale(g, g); pen.cv.translate(-960, -540)
            try:
                path = ellipse3(v, px, py, rx or r, ry or r * 0.75, Y)
                pen.fill(path, '#000000', 255 * k, blur=max(1.0, 0.12 * v.s(px, py)))
            finally:
                pen.cv.restore()
        lay = Layer(depth, draw, name, blur=None, ref_depth=4.0)
        lay.order = lambda t: fo - 0.01
        return lay


def _in_poly(pt, q):
    x, y = pt; ins = False; n = len(q)
    for i in range(n):
        x1, y1 = q[i]; x2, y2 = q[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xx = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xx > x: ins = not ins
    return ins


# ====================================================================================================== the house plan
# Orchard Road: the last house. Ground floor Y 0 (ceiling CEIL0), upstairs floor UP_Y (ceiling CEIL1), attic floor ATTIC_Y.
# +y runs from the front wall (y 0, the road) to the back wall (y 10, the yard and the woods); +x is east (the sunrise).
HX0, HX1, HY0, HY1 = -5.0, 5.0, 0.0, 10.0
CEIL0 = 2.6
UP_Y = 2.85
CEIL1 = UP_Y + 2.45
ATTIC_Y = 5.45
RIDGE = ATTIC_Y + 2.7
WT = 0.14                                                    # wall thickness (the reveals of doors and windows)

# ground floor rooms (x0, x1, y0, y1)
HALL = (-1.4, 1.3, 0.0, 5.8)
LIV = (-5.0, -1.4, 0.0, 5.8)
KIT = (-5.0, 1.3, 5.8, 10.0)
# openings: doors are (x0, x1) along their wall + height; windows (u0, u1, sill, top)
FDOOR = (-0.85, 0.05, 2.03)                                  # front door on y 0 (hinge at x -0.85, opens into the hall)
FD_CX = (FDOOR[0] + FDOOR[1]) / 2
PEEP_Y, SLOT_Y, KNOB_Y = 1.52, 0.95, 0.97                    # the cast's door: peephole, mail slot, knob heights
STAIR_X = (0.35, 1.3); ST_Y0 = 0.9; ST_RISE = 0.19; ST_RUN = 0.26; ST_N = 15     # 15 risers to UP_Y (2.85)
ST_TOP = ST_Y0 + (ST_N - 1) * ST_RUN                         # y of the top riser (the corridor's front edge) = 4.54
LH_OPEN = (1.5, 3.1, 2.1)                                    # living room <-> hall: on x -1.4 (y0, y1, height)
LK_OPEN = (-4.25, -2.35, 2.1)                                # living room <-> kitchen: on y 5.8
HK_DOOR = (-1.2, -0.3, 2.05)                                 # hall -> kitchen doorway on y 5.8
BDOOR = (-3.75, -2.85, 2.03)                                 # the back door on y 10 (hinge at x -3.75, opens in)
KWIN = (-1.95, -0.75, 1.02, 2.05)                            # the window over the sink on y 10
LWIN_F = (-4.15, -2.45, 0.95, 2.15)                          # living room front window (over the couch) on y 0
LWIN_S = (4.25, 5.25, 0.9, 2.1)                              # living room side window on x -5 (y range)
CLOSET = (3.55, 4.25, 1.85)                                  # under-stair closet door on the stair side x 0.35 (y range, height)
# living room furniture (plan)
COUCH = Box(-3.3, 1.22, 2.05, 0.92, 0.0, 0.86, 180)         # pulled 0.76 m off the front window (room to close the curtains), facing +y
COUCH_SEAT, COUCH_ARM = 0.45, 0.64
ARMCHAIR = Box(-3.3, 4.55, 0.86, 0.86, 0.0, 1.08, 180)      # Mom's wingback: back to the couch, facing the back door
CHAIR_SEAT = 0.44
COFFEE = Box(-3.3, 2.42, 1.1, 0.55, 0.0, 0.42, 180)
ENDTAB = Box(-1.92, 1.22, 0.46, 0.46, 0.0, 0.58, 180)
SIDETAB = (-4.18, 4.62, 0.24, 0.62)                          # round side table by the armchair, on its fireplace side (x, y, r, h)
FLAMP = (-4.62, 1.12, 1.3, 1.6)                              # floor lamp by the couch: x, y, shade bottom, shade top
CHIMNEY = (-5.0, -4.58, 2.1, 3.9)                            # chimney breast on the left wall (x0, x1, y0, y1)
MANTEL_Y = 1.22
BOOKCASE = Box(-1.58, 4.5, 1.25, 0.34, 0.0, 1.95, -90)      # on the right wall, facing -x
RUG_LIV = (-3.3, 2.65, 1.5, 1.1)                           # braided oval (x, y, rx, ry)
# kitchen (plan)
FRIDGE = Box(-4.6, 7.75, 0.78, 0.72, 0.0, 1.72, 90)         # harvest-gold fridge on the left wall, facing +x
KTABLE = Box(-0.75, 7.75, 1.2, 0.86, 0.0, 0.76, 0)
STOVE = Box(0.32, 9.66, 0.76, 0.66, 0.0, 0.92, 180)
COUNTER_Y = 0.92
SINK_X = -1.35
KCLOCK = (-1.78, 2.05, 5.8)                                  # the kitchen wall clock (x, Y, y) on the front wall
KSWITCH = (-4.05, 1.2, 10.0)                                 # the back porch light switch, by the back door
# upstairs
UPH = (-3.8, 5.0, ST_TOP, 5.8)                               # the corridor (x0, x1, y0, y1)
JUNE = (-0.4, 2.6, 5.8, 10.0)
BATH = (-2.9, -0.4, 5.8, 8.6)
D_NARR = (-2.6, -1.85); D_MOM = (2.3, 3.05)                  # doors on the corridor's front wall (y ST_TOP)
D_BATH = (-2.0, -1.25); D_JUNE = (0.4, 1.2); D_BACK = (3.5, 4.25)   # doors on the corridor's back wall (y 5.8)
D_ATTIC = (4.8, 5.55)                                        # attic door on the corridor's west end wall (x -3.8), y range
DOOR_H = 2.03
UWIN = (4.85, 5.5, 0.85, 2.05)                               # the corridor's east window on x 5.0 (y range, sill, top)
JWIN = (0.55, 1.65, 0.75, 2.05)                              # June's window on y 10 (x range, sill, top above UP_Y)
JBED = Box(2.08, 7.9, 0.98, 1.98, 0.0, 0.52, -90)           # June's bed along the right wall (head toward the window)
TUB = Box(-2.0, 8.22, 1.7, 0.74, 0.0, 0.56, 0)              # the bathtub along the bathroom's back wall
# attic
ATT = (-5.0, 5.0, 0.0, 10.0)
KNEE = 0.95                                                  # knee wall height; knee walls at y KNEE_Y0 / KNEE_Y1
KNEE_Y0, KNEE_Y1 = 1.45, 8.55
TOYCHEST = Box(0.6, 8.12, 0.92, 0.46, 0.0, 0.52, 0)          # Mom's old toy chest against the north knee wall, facing -y
BULB = (0.55, ATTIC_Y + 2.05, 5.0)                           # the bare bulb (x, Y, y)
ATT_STAIR = (-4.95, -3.85, 4.6, 5.8)                         # the stair opening in the attic floor
ROCKER = (-4.3, 8.0)                                         # Grandma's rocking chair in the dark corner (faces +x / -y)
# exterior
PORCH_B = (-4.7, -2.0, 10.0, 12.1, 0.45)                     # back porch (x0, x1, y0, y1, floor Y)
PORCH_F = (-3.1, 1.9, -2.4, 0.0, 0.55)                       # front porch
BACK_LIGHT = (-4.05, 1.95, 10.06)                            # Grandma's porch light (by the back door)
FRONT_LIGHT = (0.32, 1.92, -0.06)
TREELINE_Y = 40.0
SHED = Box(-11.3, 25.5, 3.4, 3.0, 0.0, 2.3, 90)
BARREL = (-7.6, 26.3)                                        # the burn barrel by the shed
CHOP = (-8.4, 23.4)                                          # the chopping block (the hatchet stuck in it)
SWING = (6.8, 27.5)


# ---------------------------------------------------------------------------------------------- palette (albedo)
P_ = dict(
    trim='#efe7d6', trim_d='#cfc4ac', ceil='#e4ddd0', floor0='#a8754a', floor1='#7f5434',
    liv_paper='#c99d9a', liv_ink='#f1e2d4', liv_ink2='#7f9a7c', wains='#ebe3d0',
    hall_paper='#a6b6c6', hall_ink='#f4f0e6', hall_ink2='#7d8fa6',
    kit_wall='#efe0b6', kit_ink='#d24a3a', pine='#c88e4e', pine_d='#8e5a2c', counter='#efe6cc', tile='#e9cf68',
    lino0='#b84a3e', lino1='#e8dcc2', fridge='#d1a136', stove='#8d9a3c',
    up_wall='#a9b89a', june_wall='#ecb8c0', june_ink='#fff4f2', bath_tile='#e8a6b2', bath_wall='#f2d6da',
    attic_wood='#8f6c48', attic_rafter='#6e4b2e', attic_floor='#7c5a3a',
    couch='#4f7f7c', couch_d='#2f5554', chair='#c99430', chair_d='#8e6418', brick='#9a4a34', mortar='#cdbda4',
    drape='#a35a60', siding='#e6e2d6', shutter='#2f4a3c', roof='#4b4e56', door_w='#f1ece0', door_wood='#8a5a34')
NIGHT_AMB = '#2e3760'                # moonlit navy (inside, lamps off)
LAMP_C = '#ffc98a'                   # tungsten
MOON_C = '#8aa2e6'
DAWN_C = '#ffb560'


# ---------------------------------------------------------------------------------------------- patterns (cm frames)
def pat(pen, W, H, kind, ink, a=150, seed=0, ink2=None, scale=1.0):
    """Surface patterns in a cm frame: 'roses' (small cabbage roses with leaves), 'ditsy' (tiny flowers), 'stripe',
    'beadboard', 'boards' (floor planks), 'lino' (brick-pattern linoleum), 'checker', 'hex' (mosaic), 'tile' (square
    tiles), 'brick', 'clapboard', 'shingle', 'bunnies' (June's frieze), 'gingham', 'stars', 'knotty' (pine)."""
    cv = pen.cv
    rng = np.random.default_rng(seed)
    if kind == 'roses':
        dx, dy = 34.0 * scale, 30.0 * scale
        j = 0; y = 10.0 * scale
        while y < H + dy:
            x = (dx / 2 if j % 2 else 0.0) + 8.0 * scale
            while x < W + dx:
                r = 4.2 * scale
                pen.fill(oval(x, y, r * 1.05, r), ink, a)
                pen.line(smooth([(x - r * 0.5, y - r * 0.1), (x, y - r * 0.55), (x + r * 0.55, y), (x, y + r * 0.45), (x - r * 0.3, y + r * 0.1)], False, 1.0),
                         0.9 * scale, _darken(ink, 0.35), a * 0.8)
                for s_ in (-1, 1):
                    lf = smooth([(x + s_ * r * 0.9, y + r * 0.4), (x + s_ * r * 2.0, y + r * 0.2), (x + s_ * r * 2.4, y + r * 0.9), (x + s_ * r * 1.3, y + r * 1.1)], True, 0.8)
                    pen.fill(lf, ink2 or '#6f8a6a', a * 0.85)
                pen.fill(oval(x + dx * 0.5, y + dy * 0.5, 1.1 * scale), ink2 or '#6f8a6a', a * 0.6)
                x += dx
            y += dy; j += 1
    elif kind == 'ditsy':
        dx, dy = 16.0 * scale, 14.0 * scale
        j = 0; y = 4.0
        while y < H + dy:
            x = (dx / 2 if j % 2 else 0.0) + 3.0
            while x < W + dx:
                for q in range(5):
                    ang = q * 2 * math.pi / 5 + j
                    pen.fill(oval(x + math.cos(ang) * 1.5 * scale, y + math.sin(ang) * 1.5 * scale, 1.05 * scale), ink, a)
                pen.fill(oval(x, y, 0.8 * scale), ink2 or '#e8c860', a)
                x += dx
            y += dy; j += 1
    elif kind == 'stripe':
        x = 0.0; k = 0
        while x < W:
            pen.fill(rect(x, 0, 4.0 * scale, H), ink, a * (0.5 if k % 2 else 1.0)); x += 12.0 * scale; k += 1
    elif kind == 'beadboard':
        x = 0.0
        while x < W:
            pen.fill(rect(x, 0, 0.7, H), '#000000', a * 0.55); pen.fill(rect(x + 0.7, 0, 0.6, H), '#ffffff', a * 0.35)
            x += 8.0
    elif kind == 'boards':
        u = 0.0; i = 0
        bw = 11.0 * scale
        while u < W:
            pen.fill(rect(u, 0, bw, H), ink, 50 + 80 * _h(i, seed))
            pen.fill(rect(u, 0, 0.8, H), '#140c06', 190)
            jj = _h(i, seed + 3) * 160
            while jj < H:
                pen.fill(rect(u, jj, bw, 0.7), '#140c06', 160); jj += 110 + 150 * _h(int(jj) + i, seed + 5)
            u += bw; i += 1
    elif kind == 'lino':                                      # 1970s brick-pattern linoleum: red bricks, cream grout
        bw, bh = 20.0, 10.0
        j = 0; y = 0.0
        while y < H:
            x = -(bw / 2 if j % 2 else 0.0)
            while x < W:
                c_ = mix(ink, '#000000', 0.12 * _h(int(x * 7 + y * 3), seed)) if ink2 is None else mix(ink, ink2, 0.12 * _h(int(x * 7 + y * 3), seed))
                pen.fill(rect(x + 0.7, y + 0.7, bw - 1.4, bh - 1.4), c_, a)
                pen.fill(rect(x + 0.7, y + 0.7, bw - 1.4, 1.2), '#ffffff', 26)
                x += bw
            y += bh; j += 1
    elif kind == 'checker':
        s_ = 30.0 * scale
        for i in range(int(W / s_) + 1):
            for j in range(int(H / s_) + 1):
                if (i + j) % 2: pen.fill(rect(i * s_, j * s_, s_, s_), ink, a)
    elif kind == 'hex':                                       # tiny hex mosaic with a flower every so often
        r = 2.4
        j = 0; y = 0.0
        while y < H + r * 2:
            x = (r * 0.866 if j % 2 else 0.0)
            while x < W + r * 2:
                pts = [(x + r * math.cos(math.pi / 6 + q * math.pi / 3), y + r * math.sin(math.pi / 6 + q * math.pi / 3)) for q in range(6)]
                fl = (int(x / (r * 1.732)) % 7 == 3 and j % 6 == 2) or (int(x / (r * 1.732)) % 7 in (2, 4) and j % 6 == 2) or \
                     (int(x / (r * 1.732)) % 7 == 3 and j % 6 in (1, 3))
                pen.fill(poly(pts), ink if fl else (ink2 or '#f2efe6'), a)
                x += r * 1.732
            y += r * 1.5; j += 1
        pen.fill(rect(0, 0, W, H), '#000000', 0)
    elif kind == 'tile':
        s_ = 15.0 * scale
        x = 0.0
        while x <= W:
            pen.fill(rect(x - 0.35, 0, 0.7, H), ink, a); x += s_
        y = 0.0
        while y <= H:
            pen.fill(rect(0, y - 0.35, W, 0.7), ink, a); y += s_
    elif kind == 'brick':
        bw, bh = 21.0, 6.5
        j = 0; y = 0.0
        while y < H:
            x = -(bw / 2 if j % 2 else 0.0)
            while x < W:
                c_ = mix(ink2 or '#9a4a34', '#000000', 0.25 * _h(int(x * 3 + y * 7), seed)) if ink2 else None
                if c_: pen.fill(rect(x + 0.6, y + 0.6, bw - 1.2, bh - 1.2), c_)
                x += bw
            pen.fill(rect(0, y, W, 0.9), ink, a)
            y += bh; j += 1
    elif kind == 'clapboard':
        y = 0.0
        while y < H:
            pen.linear(rect(0, y, W, 11.5), 0, y, 0, y + 11.5, [(0, '#000000', a * 0.45), (0.2, '#000000', 0), (1, '#ffffff', a * 0.12)])
            pen.fill(rect(0, y + 11.0, W, 1.2), '#000000', a * 0.55)
            y += 12.0
    elif kind == 'shingle':
        y = 0.0; j = 0
        while y < H:
            x = -(9.0 if j % 2 else 0.0)
            while x < W:
                pen.fill(rect(x + 0.5, y, 17.0, 14.0), ink, a * (0.2 + 0.5 * _h(int(x) + j * 31, seed)))
                pen.fill(rect(x, y, 0.9, 14.0), '#000000', a * 0.6)
                x += 18.0
            pen.fill(rect(0, y + 13.0, W, 1.4), '#000000', a * 0.7)
            y += 14.0; j += 1
    elif kind == 'bunnies':                                   # a frieze of small white bunnies + pastel eggs
        x = 6.0; k = 0
        while x < W:
            yb = H * 0.62
            if k % 2 == 0:
                b = union(oval(x, yb, 3.4, 2.6), oval(x + 2.8, yb - 2.2, 1.7, 1.5))
                b = union(b, oval(x + 2.4, yb - 4.6, 0.55, 1.8)); b = union(b, oval(x + 3.4, yb - 4.4, 0.55, 1.8))
                pen.fill(b, ink, a); pen.fill(oval(x - 3.1, yb - 0.5, 0.9), ink, a)
                pen.fill(oval(x + 3.4, yb - 2.4, 0.3), '#5a3a3a', a)
            else:
                pen.fill(oval(x, yb, 1.9, 2.5), [ink2 or '#f6d978', '#9fd3f0', '#b9e0a5', '#f2a5b5'][k // 2 % 4], a)
            x += 12.0; k += 1
    elif kind == 'gingham':
        s_ = 3.0 * scale
        x = 0.0
        while x < W:
            pen.fill(rect(x, 0, s_, H), ink, a * 0.5); x += s_ * 2
        y = 0.0
        while y < H:
            pen.fill(rect(0, y, W, s_), ink, a * 0.5); y += s_ * 2
    elif kind == 'stars':
        for i in range(int(W * H / 900)):
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            r = rng.uniform(1.2, 2.6)
            pts = [(x + math.cos(-math.pi / 2 + q * math.pi / 5) * (r if q % 2 == 0 else r * 0.45),
                    y + math.sin(-math.pi / 2 + q * math.pi / 5) * (r if q % 2 == 0 else r * 0.45)) for q in range(10)]
            pen.fill(poly(pts), ink, a)
    elif kind == 'knotty':
        for i in range(int(W * H / 2600) + 1):
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            r = rng.uniform(1.0, 2.6)
            pen.fill(oval(x, y, r * 1.3, r), ink, a); pen.line(oval(x, y, r * 2.2, r * 1.6), 0.6, ink, a * 0.5)
            pen.line(oval(x, y, r * 3.3, r * 2.4), 0.5, ink, a * 0.3)


# ---------------------------------------------------------------------------------------------- walls
def hole_path(h, H):
    """A wall hole (u0, v0, u1, v1[, 'arch']) in metres (u along the wall, v up from the wall's foot) -> cm path in the
    wall's art frame (y down from the top, H = wall height in cm)."""
    u0, v0, u1, v1 = h[:4]
    r = rect(u0 * 100, H - v1 * 100, (u1 - u0) * 100, (v1 - v0) * 100)
    if len(h) > 4 and h[4] == 'arch':
        rr = (u1 - u0) * 50
        r = union(rect(u0 * 100, H - v1 * 100 + rr, (u1 - u0) * 100, (v1 - v0) * 100 - rr), oval((u0 + u1) * 50, H - v1 * 100 + rr, rr, rr * 0.75))
    return r


def wall(pen, v, a, b, Y0, Y1, paper='#c8c0b0', ink=None, kind=None, holes=(), wains=0.0, wcol=None, art=None, trim=None,
         base_h=0.13, crown=0.06, rail=None, seed=0, pa=150, ink2=None, scale=1.0, casing=0.075, thick=WT, back='#3a3430',
         line=True, ao=None):
    """A wall from plan point a (x, y) to b with its visible side on the right of a -> b, from height Y0 to Y1.
    holes: [(u0, v0, u1, v1[, 'arch'])] in metres along the wall from a and up from Y0 (doorways, windows), cased with
    `trim` (casing width in m) and with reveals of depth `thick` drawn when visible. wains = wainscot height (beadboard
    in wcol), rail = chair-rail height, art(pen, W, H) draws frames / switches in the cm frame (y down from the top)."""
    trim = trim or P_['trim']
    F = wall_face(a, b, Y0, Y1)
    W, H = F.W, F.H
    hp = [hole_path(h, H) for h in holes]

    def fn(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'plaster', 0.28, 'overlay', 0.5)
        if ink and kind: pat(p_, W, H, kind, ink, pa, seed, ink2, scale)
        if wains:
            wy = H - wains * 100
            wc = wcol or P_['wains']
            p_.fill(rect(0, wy, W, H - wy), wc)
            pat(p_, W, H - wy, 'beadboard', '#000000', 160) if False else None
            p_.cv.save(); p_.cv.translate(0, wy); pat(p_, W, H - wy, 'beadboard', '#000000', 150); p_.cv.restore()
            p_.fill(rect(0, wy - 3.5, W, 5.0), _lighten(trim, 0.04)); p_.fill(rect(0, wy - 3.5, W, 1.2), '#ffffff', 90)
            p_.fill(rect(0, wy + 1.5, W, 0.8), '#000000', 70)
        if rail:
            ry = H - rail * 100
            p_.fill(rect(0, ry - 2.5, W, 5.0), trim); p_.fill(rect(0, ry - 2.5, W, 1.0), '#ffffff', 80); p_.fill(rect(0, ry + 2.5, W, 0.8), '#000000', 60)
        if base_h:
            p_.fill(rect(0, H - base_h * 100, W, base_h * 100), trim); p_.fill(rect(0, H - base_h * 100, W, 1.4), '#ffffff', 70)
            p_.fill(rect(0, H - base_h * 100 - 0.9, W, 0.9), '#000000', 60)
        if crown:
            p_.fill(rect(0, 0, W, crown * 100), trim); p_.fill(rect(0, crown * 100 - 1.0, W, 1.0), '#000000', 70)
        if art: art(p_, W, H)
        for h, q in zip(holes, hp):                                         # casings round the openings
            if len(h) > 5 and h[5] == 'nocase': continue
            cw = casing * 100
            u0, v0, u1, v1 = h[:4]
            x0, x1, yt, yb = u0 * 100, u1 * 100, H - v1 * 100, H - v0 * 100
            outer = rect(x0 - cw, yt - cw, (x1 - x0) + 2 * cw, (yb - yt) + cw + (cw if v0 > 0.05 else 0))
            if len(h) > 4 and h[4] == 'arch':
                outer = minus(hole_path((u0 - casing, v0 - (casing if v0 > 0.05 else 0), u1 + casing, v1 + casing, 'arch'), H), q)
                p_.fill(outer, trim)
            else:
                p_.fill(minus(outer, q), trim)
                p_.line(minus(outer, q), 0.7, '#000000', 80)
            if v0 > 0.05:                                                   # a window stool (sill)
                p_.fill(rect(x0 - cw - 3, yb, (x1 - x0) + 2 * cw + 6, 3.5), _lighten(trim, 0.05)); p_.fill(rect(x0 - cw - 3, yb + 3.5, (x1 - x0) + 2 * cw + 6, 1.0), '#000000', 90)
    ok = draw_face(pen, v, F, fn, paper, holes=hp, ao=ao, line=line)
    if not ok: return False
    # reveals: the wall's thickness inside each opening (only the jambs the camera can see)
    nx, ny = F.n[0], F.n[2]
    fx, fy = F.Uu[0], F.Uu[2]
    for h in holes:
        if not thick: break
        u0, v0, u1, v1 = h[:4]
        for (u, sgn) in ((u0, 1), (u1, -1)):                               # jamb faces looking into the opening
            px, py = a[0] + fx * u, a[1] + fy * u
            Fj = Face((px, Y0 + v1, py), (-nx, 0, -ny), (0, -1, 0), thick * 100, (v1 - v0) * 100, (fx * sgn, 0, fy * sgn), 'side')
            draw_face(pen, v, Fj, None, _darken(trim, 0.08), ao={'right': 4}, line=True, lw=0.8)
        if v1 < Y1 - Y0 - 0.02:                                            # head (soffit)
            px, py = a[0] + fx * u0, a[1] + fy * u0
            Fh = Face((px, Y0 + v1, py), (fx, 0, fy), (-nx, 0, -ny), (u1 - u0) * 100, thick * 100, (0, -1, 0), 'bottom')
            draw_face(pen, v, Fh, None, _darken(trim, 0.15), ao=False, line=False)
        if v0 > 0.05:                                                       # sill (top face)
            px, py = a[0] + fx * u0, a[1] + fy * u0
            Fs = Face((px + (-nx) * thick, Y0 + v0, py + (-ny) * thick), (fx, 0, fy), (nx, 0, ny), (u1 - u0) * 100, thick * 100, (0, 1, 0), 'top')
            draw_face(pen, v, Fs, None, _lighten(trim, 0.02), ao=False, line=False)
    return True


def wall_point(a, b, u, Y, off=0.0):
    """A plan point on a wall: u metres along a -> b, height Y, `off` metres out of the visible face (toward the room)."""
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy); fx, fy = dx / L, dy / L
    return (a[0] + fx * u + fy * off, Y, a[1] + fy * u - fx * off)


def floor_rect(pen, v, x0, x1, y0, y1, Y=0.0, base='#a8754a', kind='boards', ink='#6a4428', ink2=None, seed=0, art=None, ao=22,
               scale=1.0, line=False):
    """A floor (plan rectangle) with a pattern; art(pen, W, H) draws rugs etc. in floor-art coordinates (floor_uv)."""
    F = floor_face(x0, x1, y0, y1, Y)

    def fn(p_, W, H):
        if kind == 'boards':
            p_.texture(rect(0, 0, W, H), 'wood', 0.55, 'overlay', 0.9, 90)
            pat(p_, W, H, 'boards', ink, 150, seed, scale=scale)
        elif kind:
            pat(p_, W, H, kind, ink, 255, seed, ink2, scale)
            p_.texture(rect(0, 0, W, H), 'grunge', 0.3, 'overlay', 0.7)
        if art: art(p_, W, H)
    return draw_face(pen, v, F, fn, base, ao=ao, line=line)


def ceil_rect(pen, v, x0, x1, y0, y1, Y, c=None, art=None, ao=18):
    F = ceil_face(x0, x1, y0, y1, Y)

    def fn(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'plaster', 0.35, 'overlay', 0.6)
        if art: art(p_, W, H)
    return draw_face(pen, v, F, fn, c or P_['ceil'], ao=ao, line=False)


# ====================================================================================================== furniture
def sub(B, u0, u1, n0, n1, Y0, Y1):
    """A box inside box B in B's local frame (u across, n toward its front)."""
    c = B.at((u0 + u1) / 2, (n0 + n1) / 2, 0)
    return Box(c[0], c[2], u1 - u0, n1 - n0, Y0, Y1, B.fa)


class Part:
    """One drawable piece of a furniture model: a Box with materials, or a custom draw fn with a reference point.
    tag: free label used to split pieces into layers ('front', 'arm_l', ...)."""
    __slots__ = ('box', 'mats', 'fn', 'ref', 'tag', 'skip')

    def __init__(self, box=None, mats=None, fn=None, ref=None, tag='', skip=()):
        self.box, self.mats, self.fn, self.ref, self.tag, self.skip = box, mats, fn, ref, tag, skip

    def depth(self, v):
        if self.ref is not None: return v.d(self.ref[0], self.ref[2])
        return v.d(self.box.cx, self.box.cy)


def draw_parts(pen, v, parts, select=None):
    """Draw furniture parts far -> near (painter's order by their reference depth). select(part) -> bool filters."""
    ps = [p_ for p_ in parts if select is None or select(p_)]
    ps.sort(key=lambda p_: -p_.depth(v))
    for p_ in ps:
        if p_.fn is not None: p_.fn(pen, v)
        else: draw_box(pen, v, p_.box, p_.mats, skip=p_.skip)


def _round_top(W, H, r):
    """cm silhouette: a rectangle with its top corners rounded (radius r cm)."""
    return rrect(0, 0, W, H + r, r) if r > 0 else rect(0, 0, W, H)


def _cushion_art(c, piping=None):
    def art(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'fabric', 0.5, 'overlay', 0.6)
        p_.linear(rect(0, 0, W, H), 0, 0, 0, H, [(0, '#ffffff', 40), (0.35, '#ffffff', 0), (1, '#000000', 50)])
        if piping: p_.line(rrect(1.2, 1.2, W - 2.4, H - 2.4, min(W, H) * 0.25), 1.2, piping, 150)
    return art


def couch_parts(B=None, c=None, cd=None, afghan=True, blanket=False):
    """The living-room couch (faded teal, three puffy seat cushions, rolled arms, three back pillows, Grandma's granny-
    square afghan over the back). Seats: couch_seats(). blanket: June's blanket left on the middle seat (she is gone)."""
    B = B or COUCH; c = c or P_['couch']; cd = cd or P_['couch_d']
    w2, d2 = B.w / 2, B.d / 2
    cus = _lighten(c, 0.08)
    P = []
    for (u, n) in ((-w2 + 0.07, -d2 + 0.07), (w2 - 0.07, -d2 + 0.07), (-w2 + 0.07, d2 - 0.07), (w2 - 0.07, d2 - 0.07)):
        P.append(Part(sub(B, u - 0.025, u + 0.025, n - 0.025, n + 0.025, 0.0, 0.09), {'all': '#3a2414'}))
    P.append(Part(sub(B, -w2 + 0.02, w2 - 0.02, -d2 + 0.02, d2 - 0.03, 0.09, 0.31), {'all': dict(fill=cd, art=_cushion_art(cd)),
                                                                                    'front': dict(fill=c, art=_skirt_art(c))}))
    # the back frame: a tall rounded slab behind the pillows
    P.append(Part(fn=lambda pen, v: box_extrude(pen, v, B, -w2 + 0.03, w2 - 0.03, -d2, -d2 + 0.2, 0.31, B.Y1,
                                                 lambda W, H: rounded_rect_pts(W, H, 9.0, 1.0), c, _darken(c, 0.12), _cushion_art(c)),
                  ref=B.at(0, -d2 + 0.1, 0.6), tag='back'))
    iw = (B.w - 0.46) / 3
    for i in range(3):
        u0 = -w2 + 0.23 + i * iw
        P.append(Part(fn=(lambda u0_: lambda pen, v: box_extrude(pen, v, B, -d2 + 0.19, -d2 + 0.41, 0, 0, 0.42, 0.8,
                                                                    lambda W, H: _pillow_side(W, H), cus, _darken(cus, 0.1), None, axis='u_' and 'u'
                                                                    ) if False else _pillow(pen, v, B, u0_, iw, cus, cd))(u0),
                      ref=B.at(u0 + iw / 2, -d2 + 0.3, 0.6), tag='pillow'))
        P.append(Part(fn=(lambda u0_: lambda pen, v: box_extrude(pen, v, B, u0_ + 0.006, u0_ + iw - 0.006, -d2 + 0.2, d2 - 0.005, 0.31, COUCH_SEAT,
                                                                    lambda W, H: rounded_rect_pts(W, H, 5.0, 2.0, bulge=1.6), cus, _darken(cus, 0.12),
                                                                    _cushion_art(cus, cd)))(u0),
                      ref=B.at(u0 + iw / 2, 0.05, 0.38), tag='seat'))
    for s_ in (-1, 1):
        u0, u1 = (-w2, -w2 + 0.24) if s_ < 0 else (w2 - 0.24, w2)
        P.append(Part(fn=(lambda u0_, u1_: lambda pen, v: box_extrude(pen, v, B, u0_, u1_, -d2, d2, 0.09, COUCH_ARM,
                                                                         lambda W, H: _arm_profile(W, H), c, _darken(c, 0.1), _arm_roll_art(c, cd)))(u0, u1),
                      ref=B.at((u0 + u1) / 2, 0.0, 0.4), tag='arm_l' if s_ < 0 else 'arm_r'))
    if afghan:
        P.append(Part(fn=lambda pen, v: _afghan_drape(pen, v, B), ref=B.at(0, -d2 + 0.05, 0.8), tag='back'))
    if blanket:
        P.append(Part(fn=lambda pen, v: _blanket(pen, v, B), ref=B.at(0.0, 0.1, COUCH_SEAT), tag='seat'))
    return P


def _arm_profile(W, H):
    """A rolled arm seen from the front: a column with a rounded roll overhanging outward at the top."""
    r = W * 0.48
    pts = [(W * 0.1, H), (W * 0.1, r * 1.6)]
    for k in range(0, 13):
        a = math.radians(180 + 180 * k / 12)
        pts.append((W / 2 + r * math.cos(a), r + r * 0.92 * math.sin(a)))
    pts += [(W * 0.95, r * 1.6), (W * 0.9, H)]
    return pts


def _pillow(pen, v, B, u0, iw, c, cd):
    """A back pillow leaning on the couch back: a puffy slab tilted back."""
    d2 = B.d / 2
    O = B.at(u0 + 0.012, -d2 + 0.42, 0.82)
    U3 = (B.U[0], 0.0, B.U[1]); N3 = (B.N[0], 0.0, B.N[1])
    tilt = 0.24
    V3 = _norm3((-N3[0] * tilt, -1.0, -N3[2] * tilt))
    W, H = (iw - 0.024) * 100, 40.0
    extrude(pen, v, O, U3, V3, rounded_rect_pts(W, H, 9.0, 6.0, bulge=1.5), _scale3(N3, -0.17), c, _darken(c, 0.12), _cushion_art(c, cd))


def _pillow_side(W, H):
    return rounded_rect_pts(W, H, 6.0)


def _skirt_art(c):
    def art(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'fabric', 0.5, 'overlay', 0.6)
        x = 6.0
        while x < W:
            p_.linear(rect(x - 3, 0, 6, H), x - 3, 0, x + 3, 0, [(0, '#000000', 0), (0.5, '#000000', 45), (1, '#000000', 0)]); x += 12.0
    return art


def _arm_roll_art(c, cd):
    def art(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'fabric', 0.5, 'overlay', 0.6)
        r = W * 0.42
        p_.fill(oval(W / 2, r * 0.9, r, r * 0.8), _lighten(c, 0.08)); p_.line(oval(W / 2, r * 0.9, r * 0.72, r * 0.55), 1.0, cd, 140)
        p_.line(oval(W / 2, r * 0.9, r, r * 0.8), 1.2, cd, 170)
    return art


_GRANNY = ['#d8584a', '#e8b84a', '#5a9a7a', '#4a6aa8', '#c86a9a', '#f0e6d0', '#8a5aa8', '#e88a3a']


def _afghan_art(p_, W, H):
    s_ = 9.0
    for i in range(int(W / s_) + 1):
        for j in range(int(H / s_) + 1):
            x, y = i * s_, j * s_
            k = (i * 7 + j * 3) % len(_GRANNY)
            p_.fill(rect(x, y, s_, s_), '#2a1e1a')
            p_.fill(rect(x + 1.0, y + 1.0, s_ - 2, s_ - 2), _GRANNY[k])
            p_.fill(rect(x + 2.6, y + 2.6, s_ - 5.2, s_ - 5.2), _GRANNY[(k + 3) % len(_GRANNY)])
            p_.fill(rect(x + 3.8, y + 3.8, s_ - 7.6, s_ - 7.6), '#f0e6d0')


def _afghan_drape(pen, v, B):
    """The afghan hanging down the front of the back cushions (a drape face with a zigzag hem)."""
    d2 = B.d / 2
    F = Face(B.at(-B.w / 2 + 0.35, -d2 + 0.225, B.Y1 + 0.005), (B.U[0], 0, B.U[1]), (0, -1, 0), 95.0, 34.0, (B.N[0], 0, B.N[1]), 'front')
    shape = poly([(0, 0), (95, 0), (95, 22), (87, 34), (79, 22), (71, 34), (63, 22), (55, 34), (47, 22), (39, 34), (31, 22), (23, 34), (15, 22), (7, 34), (0, 24)])
    draw_face(pen, v, F, _afghan_art, '#2a1e1a', shape=shape, ao=False, lw=1.0)


def _blanket(pen, v, B):
    """June's crumpled fleece blanket on the couch seat (pink with white stars)."""
    F = Face(B.at(-0.55, 0.32, COUCH_SEAT + 0.07), (B.U[0], 0, B.U[1]), (-B.N[0], 0, -B.N[1]), 95.0, 55.0, (0, 1, 0), 'top')
    shape = smooth([(0, 8), (20, 0), (48, 5), (80, 0), (95, 10), (92, 32), (96, 52), (70, 55), (40, 49), (12, 55), (2, 40), (6, 22)], True, 0.8)

    def art(p_, W, H):
        pat(p_, W, H, 'stars', '#fff6f8', 210, 3)
        for k in range(4):
            p_.line(smooth([(5 + k * 22, 4), (12 + k * 22, 25), (8 + k * 22, 50)], False, 1.0), 1.6, '#b86a80', 110)
    draw_face(pen, v, F, art, '#e8a2b4', shape=shape, ao=False, lw=1.0)


def couch_seats(B=None):
    """Plan points of the couch's three seats: [(name, x, y)] at the hip position (seat top COUCH_SEAT)."""
    B = B or COUCH
    out = []
    iw = (B.w - 0.46) / 3
    for i, nm in enumerate(('left', 'mid', 'right')):
        u = -B.w / 2 + 0.23 + (i + 0.5) * iw
        p_ = B.at(u, -B.d / 2 + 0.42, 0)
        out.append((nm, p_[0], p_[2]))
    return out


def wingback_parts(B=None, c=None, cd=None, doilies=True):
    """Mom's mustard wingback armchair (Grandma's): cabriole legs, a deep seat cushion, rolled arms, the tall back with
    flared wings and a curved crest (one shaped slab, so it reads from the front, the back and the side), crocheted
    doilies on the arms and the headrest."""
    B = B or ARMCHAIR; c = c or P_['chair']; cd = cd or P_['chair_d']
    w2, d2 = B.w / 2, B.d / 2
    P = []
    for (u, n) in ((-w2 + 0.08, -d2 + 0.08), (w2 - 0.08, -d2 + 0.08), (-w2 + 0.08, d2 - 0.08), (w2 - 0.08, d2 - 0.08)):
        P.append(Part(sub(B, u - 0.025, u + 0.025, n - 0.025, n + 0.025, 0.0, 0.13), {'all': '#4a2a14'}))
    P.append(Part(sub(B, -w2 + 0.05, w2 - 0.05, -d2 + 0.06, d2 - 0.03, 0.13, 0.33), {'all': dict(fill=cd, art=_cushion_art(cd)),
                                                                                    'front': dict(fill=c, art=_skirt_art(c))}))
    P.append(Part(fn=lambda pen, v: box_extrude(pen, v, B, -w2 + 0.17, w2 - 0.17, -d2 + 0.17, d2 - 0.01, 0.33, CHAIR_SEAT,
                                                 lambda W, H: rounded_rect_pts(W, H, 4.0, 2.0, bulge=1.5), _lighten(c, 0.07), _darken(c, 0.05),
                                                 _cushion_art(c, cd)), ref=B.at(0, 0.08, 0.38), tag='seat'))
    def back(pen, v):
        U3 = (B.U[0], 0.0, B.U[1]); N3 = (B.N[0], 0.0, B.N[1])
        W, H = B.w * 100, (B.Y1 - 0.33) * 100
        O = B.at(-w2, -d2 + 0.19, B.Y1)
        art = _cushion_art(c, cd)
        if doilies:
            art = lambda p_, W_, H_, a0=_cushion_art(c, cd): (a0(p_, W_, H_), _doily_shape(p_, W_ * 0.5, 15, 14, 9))
        extrude(pen, v, O, U3, (0.0, -1.0, 0.0), _wing_profile(W, H), _scale3(N3, -0.19), c, _darken(c, 0.15), art,
                art_back=_cushion_art(_darken(c, 0.05), cd))
    P.append(Part(fn=back, ref=B.at(0, -d2 + 0.09, 0.7), tag='back'))
    for s_ in (-1, 1):
        u0, u1 = (-w2, -w2 + 0.17) if s_ < 0 else (w2 - 0.17, w2)
        P.append(Part(fn=(lambda u0_, u1_: lambda pen, v: box_extrude(pen, v, B, u0_, u1_, -d2 + 0.17, d2, 0.13, 0.64,
                                                                         lambda W, H: _arm_profile(W, H), c, _darken(c, 0.1),
                                                                         lambda p_, W, H: (_arm_roll_art(c, cd)(p_, W, H),
                                                                                           _doily_shape(p_, W / 2, 9, W * 0.4, 6) if doilies else None)))(u0, u1),
                      ref=B.at((u0 + u1) / 2, 0.1, 0.4), tag='arm_l' if s_ < 0 else 'arm_r'))
    return P


def _wing_profile(W, H):
    """The wingback's back seen from the front (cm, y down): narrow at the seat, flaring out into the wings at shoulder
    height, rounding over into a raised crest."""
    pts = [(W * 0.2, H), (W * 0.17, H * 0.55), (W * 0.06, H * 0.42), (0, H * 0.3), (W * 0.02, H * 0.17), (W * 0.1, H * 0.08),
           (W * 0.28, H * 0.035), (W * 0.5, 0.0), (W * 0.72, H * 0.035), (W * 0.9, H * 0.08), (W * 0.98, H * 0.17), (W, H * 0.3),
           (W * 0.94, H * 0.42), (W * 0.83, H * 0.55), (W * 0.8, H)]
    out = []
    n = len(pts)
    for i in range(n - 1):                                    # densify with a Catmull-Rom pass for a soft outline
        p0, p1, p2, p3 = pts[max(0, i - 1)], pts[i], pts[i + 1], pts[min(n - 1, i + 2)]
        for k in range(4):
            t = k / 4
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)
                             for j in range(2)))
    out.append(pts[-1])
    return out


def _doily_shape(p_, cx, cy, rx, ry):
    sh = skia.Path()
    for k in range(18):
        a = 2 * math.pi * k / 18
        sh = union(sh, oval(cx + math.cos(a) * rx, cy + math.sin(a) * ry, rx * 0.22, ry * 0.22))
    sh = union(sh, oval(cx, cy, rx * 0.95, ry * 0.95))
    p_.fill(sh, '#f4efe2', 235)
    for r in (0.3, 0.55, 0.78):
        p_.line(oval(cx, cy, rx * r, ry * r), 0.7, '#cfc6b0', 200)


def _doily_art(p_, W, H):
    p_.texture(rect(0, 0, W, H), 'fabric', 0.5, 'overlay', 0.6)
    _doily_shape(p_, W / 2, H * 0.45, W * 0.42, H * 0.3)


def chair_seat(B=None, seat=CHAIR_SEAT):
    B = B or ARMCHAIR
    p_ = B.at(0, -B.d / 2 + 0.38, 0)
    return (p_[0], p_[2])


def table_parts(B, top='#7a4a2a', leg=None, apron=0.07, thick=0.035, inset=0.05, legw=0.05, cloth=None, tag='table'):
    """A wooden table: top slab, apron, four legs."""
    leg = leg or _darken(top, 0.18)
    w2, d2 = B.w / 2, B.d / 2
    P = []
    for (u, n) in ((-w2 + inset, -d2 + inset), (w2 - inset, -d2 + inset), (-w2 + inset, d2 - inset), (w2 - inset, d2 - inset)):
        P.append(Part(sub(B, u - legw / 2, u + legw / 2, n - legw / 2, n + legw / 2, 0.0, B.Y1 - thick), {'all': leg}, tag=tag))
    if apron:
        P.append(Part(sub(B, -w2 + inset, w2 - inset, -d2 + inset, d2 - inset, B.Y1 - thick - apron, B.Y1 - thick), {'all': dict(fill=_darken(top, 0.08), art=_wood_art)}, tag=tag))
    mt = {'all': dict(fill=top, art=_wood_art), 'top': dict(fill=_lighten(top, 0.06), art=_wood_art)}
    if cloth:
        mt = {'all': dict(fill=cloth[0], art=cloth[1]), 'top': dict(fill=cloth[0], art=cloth[1])}
    P.append(Part(sub(B, -w2, w2, -d2, d2, B.Y1 - thick, B.Y1), mt, tag=tag))
    return P


def _wood_art(p_, W, H):
    p_.texture(rect(0, 0, W, H), 'wood', 0.55, 'overlay', 0.8, 90)


def lamp_floor(pen, v, x, y, Yb, Yt, k=0.0, shade='#efe2c4', metal='#b08a4a', rb=0.2, rt=0.15):
    """A floor lamp: weighted base, brass pole, pleated drum shade (bottom Yb, top Yt). k = how lit the shade looks (the
    'plus' glow layer adds the light; the base layer draws k=0)."""
    s = v.s(x, y)
    bx, by = v.p(x, 0.0, y)
    base = ellipse3(v, x, y, 0.16, 0.16, 0.0)
    pen.fill(base, lit('#5a4a30', (x, 0.05, y), (0, 1, 0))); pen.line(base, 1.2)
    pen.fill(ellipse3(v, x, y, 0.13, 0.13, 0.035), lit(metal, (x, 0.05, y), (0, 1, 0)))
    tx, ty = v.p(x, Yb + 0.02, y)
    w = max(1.5, 0.022 * s)
    pen.seg((bx, by - 0.03 * s), (tx, ty), w + 2.4, LINE, 230); pen.seg((bx, by - 0.03 * s), (tx, ty), w, lit(metal, (x, 1.0, y), (1, 0, 0)))
    _shade(pen, v, x, y, Yb, Yt, rb, rt, shade, k)


def _shade(pen, v, x, y, Yb, Yt, rb, rt, c, k=0.0, pleat=True):
    """A lampshade (truncated cone) at plan (x, y): bottom radius rb at Yb, top rt at Yt."""
    bot = [v.p(x + rb * math.cos(2 * math.pi * i / 28), Yb, y + rb * math.sin(2 * math.pi * i / 28)) for i in range(28)]
    top = [v.p(x + rt * math.cos(2 * math.pi * i / 28), Yt, y + rt * math.sin(2 * math.pi * i / 28)) for i in range(28)]
    xs = [p_[0] for p_ in bot + top]
    lb, rbx = min(range(28), key=lambda i: bot[i][0]), max(range(28), key=lambda i: bot[i][0])
    lt, rtx = min(range(28), key=lambda i: top[i][0]), max(range(28), key=lambda i: top[i][0])
    # silhouette: left edge, the near half of the bottom ellipse, right edge, the far half of the top ellipse
    cyb = sum(p_[1] for p_ in bot) / 28; cyt = sum(p_[1] for p_ in top) / 28
    near_b = [p_ for p_ in bot if p_[1] >= cyb - 1e-6]; far_t = [p_ for p_ in top if p_[1] <= cyt + 1e-6]
    near_b.sort(key=lambda q: q[0]); far_t.sort(key=lambda q: -q[0])
    sil = poly([top[lt], bot[lb]] + near_b + [bot[rbx], top[rtx]] + far_t)
    m_ = light_at((x, (Yb + Yt) / 2, y), None, None, [])
    r_, g_, b_ = rgb(c)
    body = '#%02x%02x%02x' % tuple(int(clamp(q * mm * 1.1, 0, 255)) for q, mm in zip((r_, g_, b_), m_))
    glow = mix('#fff1d6', '#ffd9a0', 0.3)
    fillc = mix(body, glow, clamp(k))
    pen.fill(sil, fillc)
    if pleat:
        for i in range(0, 28, 2):
            a_, b_ = bot[i], top[i]
            if a_[1] >= cyb - 2:
                pen.seg(a_, b_, 0.8, '#000000', 30 if k < 0.5 else 18)
    pen.linear(sil, min(xs), 0, max(xs), 0, [(0, '#000000', 60 * (1 - k)), (0.5, '#000000', 0), (1, '#000000', 70 * (1 - k))])
    if v.cam_h < Yb:                                              # seen from below: the bright opening under the shade
        pen.fill(poly(bot), mix(_darken(c, 0.3), '#fff6e0', k))
    pen.line(sil, 1.4)


def fireplace(pen, v, part='all', fire=0.0):
    """The chimney breast on the living room's left wall: red brick surround, the firebox (old ashes, an iron grate), the
    white mantel shelf (Easter decorations on top: pastel egg garland, ceramic bunnies, a photo of Laurie at seven in the
    yellow dress, a clock), the brick hearth. Faces +x."""
    x0, x1, y0, y1 = CHIMNEY
    # breast sides + front (wallpapered above the mantel)
    def front_art(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'plaster', 0.28, 'overlay', 0.5)
        pat(p_, W, H, 'roses', P_['liv_ink'], 120, 4, P_['liv_ink2'])
        # brick surround
        bx0, bx1 = 25.0, W - 25.0
        by0 = H - 112.0
        br = rect(bx0, by0, bx1 - bx0, H - by0)
        p_.fill(br, P_['mortar'])
        p_.cv.save(); p_.cv.clipPath(br, skia.ClipOp.kIntersect, True)
        p_.cv.translate(bx0, by0); pat(p_, bx1 - bx0, H - by0, 'brick', P_['mortar'], 255, 3, P_['brick']); p_.cv.restore()
        p_.texture(br, 'grunge', 0.4, 'overlay', 0.6)
        # firebox
        fx0, fx1, fy0 = bx0 + 30.0, bx1 - 30.0, H - 75.0
        fb = rrect(fx0, fy0, fx1 - fx0, H - fy0 + 8, 6)
        p_.fill(fb, '#120c0a'); p_.linear(fb, 0, fy0, 0, H, [(0, '#000000', 0), (1, '#3a2a22', 160)])
        for k in range(5):                                                    # grate bars
            gx = fx0 + 12 + k * (fx1 - fx0 - 24) / 4
            p_.seg((gx, H - 22), (gx, H - 8), 2.4, '#2a2622')
        p_.seg((fx0 + 8, H - 20), (fx1 - 8, H - 20), 2.6, '#2a2622')
        p_.fill(smooth([(fx0 + 14, H - 6), (fx0 + 40, H - 14), (fx1 - 30, H - 12), (fx1 - 12, H - 5)], True, 0.8), '#4a4440', 220)  # ashes
        p_.line(fb, 1.2, '#000000', 160)
    F = wall_face((x1, y0), (x1, y1), 0.0, CEIL0)
    draw_face(pen, v, F, front_art, P_['liv_paper'], ao={'bottom': 18, 'top': 14})
    if part == 'front': return
    for (a, b) in (((x0, y0), (x1, y0)), ((x1, y1), (x0, y1))):
        F2 = wall_face(a, b, 0.0, CEIL0)
        draw_face(pen, v, F2, lambda p_, W, H: pat(p_, W, H, 'roses', P_['liv_ink'], 120, 6, P_['liv_ink2']), P_['liv_paper'],
                  ao={'bottom': 18, 'right': 10, 'left': 10})
    hearth = Box((x1 + x1 + 0.42) / 2, (y0 + y1) / 2, 1.5, 0.42, 0.0, 0.06, 90)
    draw_box(pen, v, hearth, {'all': dict(fill=P_['brick'], art=lambda p_, W, H: pat(p_, W, H, 'brick', P_['mortar'], 200, 9, P_['brick']))})
    mant = Box(x1 + 0.1, (y0 + y1) / 2, 1.62, 0.2, MANTEL_Y, MANTEL_Y + 0.06, 90)
    draw_box(pen, v, mant, {'all': P_['trim'], 'top': _lighten(P_['trim'], 0.04)})
    for yy in (y0 + 0.12, y1 - 0.12):                                      # pilasters
        pil = Box(x1 + 0.03, yy, 0.14, 0.06, 0.0, MANTEL_Y, 90)
        draw_box(pen, v, pil, {'all': P_['trim']})
    _mantel_things(pen, v, x1 + 0.1, (y0 + y1) / 2)


def _mantel_things(pen, v, x, yc):
    """Pastel egg garland, two ceramic bunnies, the framed photo of Laurie (1987, the yellow dress), a small clock."""
    Y = MANTEL_Y + 0.06
    # framed photo (stands, leaning)
    F = Face((x - 0.02, Y + 0.3, yc + 0.17), (0, 0, -1), (0, -1, 0), 24.0, 30.0, (1, 0, 0), 'front')
    def ph(p_, W, H):
        p_.fill(rect(0, 0, W, H), '#c8a24a'); p_.fill(rect(2.5, 2.5, W - 5, H - 5), '#f2e8c8')
        _photo_laurie(p_, 4, 4, W - 8, H - 8)
    draw_face(pen, v, F, ph, '#c8a24a', ao=False, lw=1.0)
    # clock
    cx_, cy_ = v.p(x - 0.01, Y + 0.12, yc - 0.32)
    r = 0.09 * v.s(x, yc - 0.32)
    pen.fill(oval(cx_, cy_, r * 0.45, r), lit('#6a4a2a', (x, Y, yc), (1, 0, 0))); pen.fill(oval(cx_ + r * 0.04, cy_, r * 0.33, r * 0.78), lit('#f2ead6', (x, Y, yc), (1, 0, 0)))
    pen.line(oval(cx_, cy_, r * 0.45, r), 1.2)
    # ceramic bunnies
    for yy, sc in ((yc - 0.6, 1.0), (yc + 0.55, 0.85)):
        _ceramic_bunny(pen, v, x - 0.02, Y, yy, 0.16 * sc)
    # the egg garland: pastel eggs on a string swagged along the mantel front
    pts = []
    n = 13
    for i in range(n):
        u = i / (n - 1)
        yy = (yc - 0.78) + 1.56 * u
        sag = 0.11 * math.sin(math.pi * ((u * 3) % 1.0))
        pts.append((x + 0.11, Y - 0.04 - sag, yy))
    sp = [v.p(*q) for q in pts]
    pen.line(smooth(sp, False, 0.8), 1.0, '#e8e0c8', 220)
    cols = ['#f2a5b5', '#f6d978', '#9fd3f0', '#b9e0a5', '#d9b3f0']
    for i, q in enumerate(pts[1:-1:1]):
        if i % 1: continue
        px, py = v.p(q[0], q[1] - 0.035, q[2]); s = v.s(q[0], q[2])
        e = oval(px, py, 0.028 * s, 0.038 * s)
        pen.fill(e, lit(cols[i % 5], q, (1, 0, 0), 1.15)); pen.line(e, 0.9)


def _ceramic_bunny(pen, v, x, Y, y, h):
    """A small white ceramic bunny figurine sitting at plan (x, y) on a surface at height Y, h metres tall (faces +x)."""
    px, py = v.p(x, Y, y); s = v.s(x, y) * h
    c = lit('#f2eee6', (x, Y + h / 2, y), (1, 0, 0), 1.05)
    body = union(oval(px, py - s * 0.32, s * 0.3, s * 0.32), oval(px + s * 0.05, py - s * 0.72, s * 0.17, s * 0.16))
    body = union(body, oval(px - s * 0.0, py - s * 1.02, s * 0.05, s * 0.2)); body = union(body, oval(px + s * 0.1, py - s * 1.0, s * 0.05, s * 0.2))
    pen.fill(body, c); pen.line(body, 1.0)
    pen.fill(oval(px + s * 0.1, py - s * 0.74, s * 0.025), '#3a2a2a')
    pen.fill(oval(px + s * 0.2, py - s * 0.7, s * 0.02), '#e89aa8')


def _photo_laurie(p_, x, y, w, h, age=0.0):
    """A small 1987 snapshot: Laurie, 7, in the yellow Easter dress with strawberry-blonde pigtails, against a pale sky."""
    p_.linear(rect(x, y, w, h), 0, y, 0, y + h, ['#a8c8e0', '#d8e4c8', '#8aa86a'])
    cx = x + w * 0.5
    hy = y + h * 0.3
    dress = poly([(cx - w * 0.14, y + h * 0.48), (cx + w * 0.14, y + h * 0.48), (cx + w * 0.26, y + h * 0.88), (cx - w * 0.26, y + h * 0.88)])
    p_.fill(dress, '#f2c84b'); p_.fill(rect(cx - w * 0.15, y + h * 0.42, w * 0.3, h * 0.1), '#f2c84b')
    p_.fill(rect(cx - w * 0.13, y + h * 0.88, w * 0.04, h * 0.1), '#e8c8a8'); p_.fill(rect(cx + w * 0.09, y + h * 0.88, w * 0.04, h * 0.1), '#e8c8a8')
    p_.fill(oval(cx, hy, w * 0.14, h * 0.11), '#f0cdb0')
    p_.fill(oval(cx, hy - h * 0.06, w * 0.15, h * 0.06), '#e0884a')
    for s_ in (-1, 1):
        p_.fill(oval(cx + s_ * w * 0.2, hy - h * 0.02, w * 0.06, h * 0.07), '#e0884a')
        p_.fill(oval(cx + s_ * w * 0.2, hy - h * 0.1, w * 0.05, h * 0.03), '#f6d84a')
    p_.fill(rect(cx - w * 0.07, y + h * 0.44, w * 0.14, h * 0.035), '#ffffff')
    if age: p_.fill(rect(x, y, w, h), '#d8b880', 80 * age)


def bookcase(pen, v, B=None):
    """A painted bookcase (books, a photo of Grandma, a sewing tin, a bunny figurine). Faces B.fa."""
    B = B or BOOKCASE
    fs = B.faces()
    for nm in ('left', 'right', 'top'):
        draw_face(pen, v, fs[nm], None, P_['trim'], ao=False)

    def art(p_, W, H):
        p_.fill(rect(0, 0, W, H), P_['trim'])
        n = 5
        sh = (H - 14) / n
        rng = np.random.default_rng(11)
        for i in range(n):
            y0 = 7 + i * sh
            p_.fill(rect(5, y0, W - 10, sh - 3), '#4a3a32')
            p_.linear(rect(5, y0, W - 10, sh - 3), 0, y0, 0, y0 + sh, [(0, '#000000', 120), (0.4, '#000000', 0)])
            x = 7.0
            while x < W - 12:
                if i == 1 and 40 < x < 70:
                    p_.fill(rect(x, y0 + sh - 26, 18, 22), '#c8a24a'); p_.fill(rect(x + 2, y0 + sh - 24, 14, 18), '#d8c8b0')
                    p_.fill(oval(x + 9, y0 + sh - 17, 3.5, 4.5), '#8a8a90'); x += 22; continue
                bw = rng.uniform(2.5, 5.0); bh = rng.uniform(sh * 0.55, sh * 0.85)
                c_ = ['#8a2a2a', '#2a4a6a', '#5a6a3a', '#c8a24a', '#6a3a5a', '#e8e0c8', '#3a3a3a', '#b86a3a'][int(rng.integers(0, 8))]
                p_.fill(rect(x, y0 + sh - 3 - bh, bw, bh), c_); p_.fill(rect(x, y0 + sh - 3 - bh * 0.8, bw, 1.2), '#e8d8a0', 120)
                x += bw + 0.4
                if rng.uniform() < 0.08: x += rng.uniform(4, 10)
            p_.fill(rect(3, y0 + sh - 3, W - 6, 3.5), P_['trim']); p_.fill(rect(3, y0 + sh + 0.5, W - 6, 0.8), '#000000', 80)
    draw_face(pen, v, fs['front'], art, P_['trim'], ao=False)


def rug_oval(p_, cx, cy, rx, ry, cols=('#6e3a2c', '#9a7a52', '#4a5a4a', '#b8a888', '#7a4a34', '#5a4a3a', '#8a6a4a')):
    """A braided oval rug in floor-art cm coordinates (centre, radii in cm)."""
    n = 22
    for i in range(n):
        k = 1.0 - i / n
        p_.fill(oval(cx, cy, rx * k, ry * k), cols[(i * 3 + i // 4) % len(cols)])
        p_.line(oval(cx, cy, rx * k, ry * k), 0.7, '#000000', 45)
    p_.texture(oval(cx, cy, rx, ry), 'fabric', 0.6, 'overlay', 0.4)
    p_.line(oval(cx, cy, rx, ry), 1.4, '#1a1010', 150)


# ====================================================================================================== windows, doors, curtains
def window_unit(pen, v, a, b, u0, u1, sill, top, Y0=0.0, lites=(2, 2), frame='#f1ece0', inset=0.07, sash_open=0.0, broken=0.0,
                seed=0):
    """A double-hung window in the wall a -> b (holes at u0..u1, sill..top above Y0): the sashes and muntins drawn in
    the window plane (inset into the wall), the glass left open so the layer behind (the night outside) shows through.
    broken 0..1: the lower sash's glass smashed (jagged hole, shards left in the frame)."""
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy); fx, fy = dx / L, dy / L
    nx, ny = fy, -fx
    O = (a[0] + fx * u0 - nx * inset, Y0 + top, a[1] + fy * u0 - ny * inset)
    W, H = (u1 - u0) * 100, (top - sill) * 100
    F = Face(O, (fx, 0, fy), (0, -1, 0), W, H, (nx, 0, ny), 'front')
    fw = 4.5                                                # frame / sash width (cm)
    mid = H / 2 + 1.5
    panes = []
    cols, rows = lites
    for half, (y0_, y1_) in enumerate(((fw, mid - fw * 0.5), (mid + fw * 0.5, H - fw))):
        pw = (W - 2 * fw - (cols - 1) * 1.6) / cols; ph = (y1_ - y0_ - (rows - 1) * 1.6) / rows
        for i in range(cols):
            for j in range(rows):
                panes.append((fw + i * (pw + 1.6), y0_ + j * (ph + 1.6), pw, ph, half))
    holes = [rect(x, y, w, h) for (x, y, w, h, _) in panes]
    if broken > 0:
        holes = [q for q, pn in zip(holes, panes) if pn[4] == 0]
        holes.append(_smash_hole(fw, mid + fw * 0.5, W - 2 * fw, H - fw - (mid + fw * 0.5), broken, seed))

    def art(p_, W, H):
        p_.fill(rect(0, 0, W, H), frame)
        p_.fill(rect(0, mid - fw * 0.6, W, fw * 1.2), _darken(frame, 0.12))                    # meeting rail
        for (x, y, w, h, _) in panes:
            p_.line(rect(x - 0.4, y - 0.4, w + 0.8, h + 0.8), 0.8, '#000000', 90)
        p_.fill(rect(W * 0.5 - 2.5, mid - 2.0, 5, 1.6), '#b8a070')                           # sash lock
    draw_face(pen, v, F, art, frame, holes=holes, ao=False, lw=1.0)
    return F, panes


def _smash_hole(x, y, w, h, k, seed=0):
    """A jagged smashed-glass hole in a pane area (cm): k 0..1 grows it."""
    rng = np.random.default_rng(seed + 5)
    cx, cy = x + w * 0.52, y + h * 0.45
    pts = []
    n = 22
    for i in range(n):
        a = 2 * math.pi * i / n
        r = (0.55 + 0.45 * rng.uniform()) * (0.35 + 0.65 * k)
        pts.append((cx + math.cos(a) * w * 0.55 * r, cy + math.sin(a) * h * 0.55 * r))
    return inter(poly(pts), rect(x, y, w, h))


def glass_sheen(pen, v, F, panes, k=1.0, c='#b8c8ff', moon=True):
    """Glass reflections over the panes of a window face (unlit, semi-transparent): a diagonal sheen + a faint
    reflection of the room."""
    m, _ = fmat(v, F.O, _scale3(F.Uu, 0.01), _scale3(F.Vu, 0.01))
    cv = pen.cv; cv.save(); cv.concat(m)
    for (x, y, w, h, _) in panes:
        r = rect(x, y, w, h)
        pen.linear(r, x, y, x + w, y + h, [(0, c, 0), (0.35, c, 26 * k), (0.42, c, 6 * k), (0.6, c, 0), (0.7, c, 18 * k), (1, c, 0)])
    cv.restore()


DOOR_PANEL = '#f1ece0'


def door_art(kind='six', latch='right', peep=False, slot=False, flap=0.0, knob=True, bolt=True, chain=False, chain_on=True,
             window=False, curtain=True, broken=0.0, col=None, keyhole=False, turn=0.0, knob_turn=0.0, scuff=0.0, stain=0.0):
    """Door face art in a cm frame (W x H, y down): kind 'six' (six raised panels) | 'four' | 'plank' | 'glass' (a
    nine-lite window in the upper half: the back door). latch 'left'/'right' = where the knob is in this frame. peep, slot
    (+ flap 0..1: the inner brass flap lifted), bolt (deadbolt thumb turn, turn 0 = unlocked, 1 = locked), chain (chain
    lock, chain_on = hooked), keyhole (an old mortise lock under the knob), knob_turn (degrees, the knob rose shows it)."""
    c = col or DOOR_PANEL

    def art(p_, W, H):
        p_.fill(rect(0, 0, W, H), c)
        p_.texture(rect(0, 0, W, H), 'wood', 0.25, 'overlay', 0.6, 90)
        sw = 11.0
        if kind in ('six', 'four'):
            rows = ([(sw, 0.0, 0.2), (0.2, 0.25, 0.55), (0.55, 0.6, 0.97)] if kind == 'six' else [(sw, 0.0, 0.45), (0.45, 0.5, 0.97)])
            ys = [(sw, H * 0.22), (H * 0.27, H * 0.58), (H * 0.63, H - 12)] if kind == 'six' else [(sw, H * 0.45), (H * 0.5, H - 12)]
            for (y0, y1) in ys:
                for (x0, x1) in ((sw, W / 2 - 3.5), (W / 2 + 3.5, W - sw)):
                    pr = rect(x0, y0, x1 - x0, y1 - y0)
                    p_.fill(pr, _darken(c, 0.04))
                    p_.fill(rect(x0 + 3, y0 + 3, x1 - x0 - 6, y1 - y0 - 6), _lighten(c, 0.03))
                    p_.line(pr, 0.9, '#000000', 90); p_.fill(rect(x0, y0, x1 - x0, 1.0), '#000000', 70)
                    p_.fill(rect(x0, y1 - 1.2, x1 - x0, 1.2), '#ffffff', 90)
        elif kind == 'glass':
            gx0, gx1, gy0, gy1 = sw, W - sw, sw, H * 0.48
            p_.fill(rect(gx0 - 1, gy0 - 1, gx1 - gx0 + 2, gy1 - gy0 + 2), _darken(c, 0.1))
            for y0, y1 in ((H * 0.55, H - 12),):
                pr = rect(sw, y0, W - 2 * sw, y1 - y0)
                p_.fill(pr, _darken(c, 0.04)); p_.line(pr, 0.9, '#000000', 90)
                p_.fill(rect(sw + 3, y0 + 3, W - 2 * sw - 6, y1 - y0 - 6), _lighten(c, 0.03))
        elif kind == 'plank':
            x = 0.0
            while x < W:
                p_.fill(rect(x, 0, 0.8, H), '#000000', 80); x += 15.0
            p_.fill(rect(0, H * 0.18, W, 9), _darken(c, 0.08)); p_.fill(rect(0, H * 0.75, W, 9), _darken(c, 0.08))
        kx = 7.5 if latch == 'left' else W - 7.5
        if scuff: p_.fill(oval(W * 0.5, H - 10, W * 0.4, 8), '#3a2a20', 60 * scuff)
        if stain: _stain(p_, W * 0.45, H * 0.4, 30, 50, stain)
        if knob:
            ky = H - KNOB_Y * 100
            p_.fill(rrect(kx - 3.2, ky - 9, 6.4, 18, 2.6), '#a8843a'); p_.line(rrect(kx - 3.2, ky - 9, 6.4, 18, 2.6), 0.7, '#3a2a10', 200)
            p_.fill(oval(kx, ky, 3.4), '#c9a24a'); p_.fill(oval(kx - 1.0, ky - 1.2, 1.3), '#fff0c0', 200)
            a_ = math.radians(knob_turn)
            p_.seg((kx - math.cos(a_) * 2.2, ky - math.sin(a_) * 2.2), (kx + math.cos(a_) * 2.2, ky + math.sin(a_) * 2.2), 0.5, '#6a4a1a', 200)
            p_.line(oval(kx, ky, 3.4), 0.7, '#3a2a10', 220)
            if keyhole:
                p_.fill(rrect(kx - 2.6, ky + 8, 5.2, 10, 2.4), '#a8843a'); p_.line(rrect(kx - 2.6, ky + 8, 5.2, 10, 2.4), 0.6, '#3a2a10', 200)
                p_.fill(oval(kx, ky + 11.6, 0.9), '#140c06'); p_.fill(poly([(kx - 0.5, ky + 12), (kx + 0.5, ky + 12), (kx + 0.8, ky + 15), (kx - 0.8, ky + 15)]), '#140c06')
        if bolt:
            by = H - (KNOB_Y + 0.17) * 100
            p_.fill(oval(kx, by, 3.0), '#b8944a'); p_.line(oval(kx, by, 3.0), 0.7, '#3a2a10', 220)
            a_ = math.radians(90 * (1 - turn))
            p_.seg((kx - math.cos(a_) * 2.2, by - math.sin(a_) * 2.2), (kx + math.cos(a_) * 2.2, by + math.sin(a_) * 2.2), 1.6, '#6a4a1a')
        if chain:
            cy_ = H - 1.42 * 100
            tx = (0.0 if latch == 'left' else W)
            p_.fill(rrect(kx - 7 if latch == 'right' else kx - 1, cy_ - 1.5, 9, 3, 1.2), '#b8944a')
            if chain_on:
                for q in range(6):
                    xx = (kx + 2 - q * 1.9) if latch == 'right' else (kx - 2 + q * 1.9)
                    p_.line(oval(xx, cy_ + 0.4 * math.sin(q), 1.1, 0.7), 0.5, '#8a6a2a')
            else:
                for q in range(9):
                    p_.line(oval(W - 5 if latch == 'right' else 5, cy_ + q * 1.6, 0.7, 1.0), 0.5, '#8a6a2a')
        if peep:
            py_ = H - PEEP_Y * 100
            p_.fill(oval(W / 2, py_, 2.2), '#b8944a'); p_.fill(oval(W / 2, py_, 1.1), '#1a1c22'); p_.fill(oval(W / 2 - 0.4, py_ - 0.4, 0.4), '#c8d0e8', 220)
            p_.line(oval(W / 2, py_, 2.2), 0.6, '#3a2a10', 220)
        if slot:
            sy_ = H - SLOT_Y * 100
            plate = rrect(W / 2 - 16, sy_ - 5, 32, 10, 1.6)
            p_.fill(plate, '#b8944a'); p_.line(plate, 0.7, '#3a2a10', 220)
            p_.fill(rect(W / 2 - 13, sy_ - 2.4, 26, 4.8), '#0a0806')
            if flap > 0.01:                                      # the inner flap lifts (hinged at the top)
                fh = 4.6 * math.cos(flap * 1.35)
                p_.fill(rect(W / 2 - 13.2, sy_ - 2.6, 26.4, max(0.3, fh)), '#d8b45a'); p_.fill(rect(W / 2 - 13.2, sy_ - 2.6 + max(0.3, fh) - 0.6, 26.4, 0.6), '#3a2a10')
                p_.fill(rect(W / 2 - 13, sy_ - 2.4 + fh, 26, 4.8 - fh), '#020202')
            else:
                p_.fill(rect(W / 2 - 13.2, sy_ - 2.6, 26.4, 5.2), '#c9a24a'); p_.fill(rect(W / 2 - 13.2, sy_ - 2.6, 26.4, 1.0), '#fff0c0', 140)
                p_.line(rect(W / 2 - 13.2, sy_ - 2.6, 26.4, 5.2), 0.5, '#3a2a10', 200)
            p_.fill(oval(W / 2 - 14.6, sy_, 0.7), '#5a4a2a'); p_.fill(oval(W / 2 + 14.6, sy_, 0.7), '#5a4a2a')
        p_.line(rect(0, 0, W, H), 1.0, '#000000', 120)
    return art


def _stain(p_, x, y, w, h, k, c='#5a1e14'):
    rng = np.random.default_rng(int(x * 7 + y))
    for i in range(7):
        p_.fill(_blob(x + rng.uniform(-w, w) * 0.4, y + rng.uniform(-h, h) * 0.4, w * rng.uniform(0.2, 0.5), h * rng.uniform(0.15, 0.4), 9, i, 0.4), c, 120 * k)
    for i in range(4):
        xx = x + rng.uniform(-w, w) * 0.4
        p_.line(poly([(xx, y), (xx + rng.uniform(-2, 2), y + h * rng.uniform(0.6, 1.4))], False), rng.uniform(1.0, 2.2), c, 140 * k)


class Door:
    """A door leaf in an opening: hinge (x, y) plan point, width, height, closed_dir (unit plan vector hinge -> latch),
    swing +1/-1 (which way it rotates open: +1 = counter-clockwise seen from above), Y0 floor height, art_a (face on the
    side of n = (cd.y, -cd.x), i.e. the right of hinge -> latch) / art_b (the other face), thick."""

    def __init__(self, hinge, width, height, closed_dir, swing, Y0=0.0, art_a=None, art_b=None, thick=0.045, col=DOOR_PANEL):
        self.hinge, self.w, self.h, self.cd, self.swing, self.Y0 = hinge, width, height, closed_dir, swing, Y0
        self.art_a, self.art_b, self.thick, self.col = art_a, art_b, thick, col

    def dir(self, ang):
        a = math.radians(ang) * self.swing
        c_, s_ = math.cos(a), math.sin(a)
        return (self.cd[0] * c_ - self.cd[1] * s_, self.cd[0] * s_ + self.cd[1] * c_)

    def box(self, ang):
        d = self.dir(ang)
        cx, cy = self.hinge[0] + d[0] * self.w / 2, self.hinge[1] + d[1] * self.w / 2
        fa = math.degrees(math.atan2(d[1], d[0]))
        return Box(cx, cy, self.w, self.thick, self.Y0, self.Y0 + self.h, fa)

    def knob(self, ang, side='a', Y=KNOB_Y):
        d = self.dir(ang); n = (d[1], -d[0])
        k = 1.0 if side == 'a' else -1.0
        u = self.w - 0.075
        return (self.hinge[0] + d[0] * u + n[0] * (self.thick / 2 + 0.05) * k, self.Y0 + Y, self.hinge[1] + d[1] * u + n[1] * (self.thick / 2 + 0.05) * k)

    def point(self, ang, u, Y, side='a', off=0.0):
        """A point on the leaf: u metres from the hinge along it, height Y above the door's floor, on face a / b."""
        d = self.dir(ang); n = (d[1], -d[0]); k = 1.0 if side == 'a' else -1.0
        return (self.hinge[0] + d[0] * u + n[0] * (self.thick / 2 + off) * k, self.Y0 + Y, self.hinge[1] + d[1] * u + n[1] * (self.thick / 2 + off) * k)

    def draw(self, pen, v, ang=0.0):
        B = self.box(ang)
        # box 'front' normal = N = (sin fa, -cos fa) = (d.y, -d.x): face a
        mats = {'front': dict(fill=self.col, art=_flip_art(self.art_a)) if self.art_a else self.col,
                'back': dict(fill=self.col, art=self.art_b) if self.art_b else self.col,
                'left': _darken(self.col, 0.1), 'right': _darken(self.col, 0.1), 'top': _darken(self.col, 0.2)}
        draw_box(pen, v, B, mats, lw=1.0)


def _flip_art(art):
    return art


def curtain_pair(pen, v, a, b, u0, u1, top, drop, Y0=0.0, open_=1.0, c='#a35a60', off=0.09, lining=None, sheer=True, t=0.0,
                 sway=0.0, seed=0, ruffle=True):
    """Drapes on a rod in front of a window in the wall a -> b (window across u0..u1, rod at `top` above Y0, hanging
    `drop` m): two panels; open_ 1 = drawn back to the sides, 0 = closed (meeting in the middle). Sheer lace behind them
    over the glass. sway: a slow breath of air."""
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy); fx, fy = dx / L, dy / L
    nx, ny = fy, -fx
    width = (u1 - u0) + 0.3
    uc = (u0 + u1) / 2
    rod_y = Y0 + top + 0.08
    # rod
    p0 = (a[0] + fx * (uc - width / 2 - 0.1) + nx * off, rod_y, a[1] + fy * (uc - width / 2 - 0.1) + ny * off)
    p1 = (a[0] + fx * (uc + width / 2 + 0.1) + nx * off, rod_y, a[1] + fy * (uc + width / 2 + 0.1) + ny * off)
    s0 = v.p(*p0); s1 = v.p(*p1)
    sw = max(1.2, 0.018 * v.s(p0[0], p0[2]))
    if sheer:
        O = (a[0] + fx * (u0 - 0.05) + nx * (off - 0.03), Y0 + top + 0.06, a[1] + fy * (u0 - 0.05) + ny * (off - 0.03))
        F = Face(O, (fx, 0, fy), (0, -1, 0), (u1 - u0 + 0.1) * 100, (drop - 0.05) * 100, (nx, 0, ny), 'front')
        if v.visible(F.O, F.n):
            m, _ = fmat(v, F.O, _scale3(F.Uu, 0.01), _scale3(F.Vu, 0.01))
            cv = pen.cv; cv.save(); cv.concat(m)
            W_, H_ = F.W, F.H
            sc = lit('#f2eee6', F.centre(), F.n, 1.0)
            hem = smooth([(x, H_ + 2 * math.sin(x * 0.3)) for x in np.linspace(0, W_, 16)], False, 1.0)
            sh = poly([(0, 0), (W_, 0)] + [(x, H_ - 2 + 2 * math.sin(x * 0.4)) for x in np.linspace(W_, 0, 16)])
            pen.fill(sh, sc, 34)
            x = 2.0
            while x < W_:
                pen.seg((x, 0), (x + 0.5 * math.sin(x), H_), 0.8, sc, 34); x += 5.0
            for yy in np.arange(8, H_, 14):
                for xx in np.arange(4, W_, 10):
                    pen.line(oval(xx + (5 if int(yy / 14) % 2 else 0), yy, 2.2, 1.6), 0.5, sc, 40)
            cv.restore()
    for side in (-1, 1):
        # each panel: from its outer edge inward; closed width = half the window + overlap, open = bunched 0.32 m
        wclosed = width / 2 + 0.06
        wopen = 0.34
        pw = lerp(wopen, wclosed, 1.0 - clamp(open_))
        if side < 0: ua, ub = uc - width / 2, uc - width / 2 + pw
        else: ua, ub = uc + width / 2 - pw, uc + width / 2
        O = (a[0] + fx * ua + nx * off, Y0 + top + 0.06, a[1] + fy * ua + ny * off)
        F = Face(O, (fx, 0, fy), (0, -1, 0), (ub - ua) * 100, drop * 100, (nx, 0, ny), 'front')
        W_, H_ = F.W, F.H
        nf = max(3, int(W_ / (7.0 + 9.0 * clamp(1 - open_ + 0.2))))
        tb = 0.0 if not ruffle else 1.0
        hem = [(x, H_ - 3 * abs(math.sin(math.pi * x / (W_ / nf) * 0.5 + seed))) for x in np.linspace(W_, 0, nf * 4 + 1)]
        sway_dx = sway * 4.0 * math.sin(t * 0.7 + side)
        shape = poly([(0, 0), (W_, 0)] + [(x + sway_dx * (1 - (0.0)), y) for (x, y) in hem])

        def art(p_, W, H, nf=nf):
            fwid = W / nf
            for i in range(nf):
                x0 = i * fwid
                p_.linear(rect(x0, 0, fwid, H), x0, 0, x0 + fwid, 0, [(0, '#000000', 70), (0.35, '#ffffff', 30), (0.6, '#ffffff', 10), (1, '#000000', 80)])
            p_.texture(rect(0, 0, W, H), 'fabric', 0.6, 'overlay', 0.7)
            p_.fill(rect(0, 0, W, 6), _darken(c, 0.15))
            if open_ > 0.6:                                     # a tie-back
                p_.fill(rect(0, H * 0.58, W, 4), _darken(c, 0.3))
        draw_face(pen, v, F, art, c, shape=shape, ao=False, lw=1.2)
    pen.seg(s0, s1, sw + 2, LINE); pen.seg(s0, s1, sw, '#8a6a3a')
    for q in (s0, s1): pen.fill(oval(q[0], q[1], sw * 1.4), '#8a6a3a')


def gap_glow(pen, v, door_a, door_b, Y=0.0, k=1.0, c='#ffd9a0', reach=0.9, feet=(), side_n=1.0, line_only=False):
    """The line of light under a closed door (between plan points door_a -> door_b at floor height Y) and its fan on this
    side's floor. side_n: +1 = the fan spreads toward the normal of a -> b (right-hand side). feet: [(u0, u1)] fractions
    along the door shadowed by feet standing on the far side."""
    if k <= 0.002: return
    dx, dy = door_b[0] - door_a[0], door_b[1] - door_a[1]; L = math.hypot(dx, dy); fx, fy = dx / L, dy / L
    nx, ny = fy * side_n, -fx * side_n
    segs = [(0.0, 1.0)]
    for (f0, f1) in sorted(feet):
        new = []
        for (s0, s1) in segs:
            if f1 <= s0 or f0 >= s1: new.append((s0, s1)); continue
            if f0 > s0: new.append((s0, f0))
            if f1 < s1: new.append((f1, s1))
        segs = new
    for (s0, s1) in segs:
        ua, ub = s0 * L, s1 * L
        pa = (door_a[0] + fx * ua, Y, door_a[1] + fy * ua); pb = (door_a[0] + fx * ub, Y, door_a[1] + fy * ub)
        pa2 = _add3(pa, (0, 0.012, 0)); pb2 = _add3(pb, (0, 0.012, 0))
        line = v.poly3([pa, pb, pb2, pa2])
        pen.fill(line, mix(c, '#ffffff', 0.5), 255 * k)
        pen.line(line, max(1.0, 0.006 * v.s(pa[0], pa[2])), mix(c, '#ffffff', 0.3), 200 * k)
        if line_only: continue
        # the fan on the floor: a soft quad widening into the room
        q = [pa, pb, (pb[0] + nx * reach + fx * reach * 0.35, Y, pb[2] + ny * reach + fy * reach * 0.35),
             (pa[0] + nx * reach - fx * reach * 0.35, Y, pa[2] + ny * reach - fy * reach * 0.35)]
        path = v.poly3(q)
        if path.isEmpty(): continue
        b = _rb(path)
        mx_, my_ = v.p((pa[0] + pb[0]) / 2, Y, (pa[2] + pb[2]) / 2)
        far = v.p((pa[0] + pb[0]) / 2 + nx * reach, Y, (pa[2] + pb[2]) / 2 + ny * reach)
        pen.linear(path, mx_, my_, far[0], far[1], [(0, c, 150 * k), (0.25, c, 70 * k), (1, c, 0)])


# ====================================================================================================== the outside world
# The moon hangs over the woods (azimuth from +y toward +x, elevation), so every view that sees the sky puts it in the
# same place: the treeline from the yard, from June's window and from the porch all agree.
MOON_AZ, MOON_EL = 12.0, 21.0
SUN_AZ, SUN_EL = 78.0, 4.0                                   # sunrise: low in the east (+x)
SKY = {'night': ('#0a1028', '#1b2a5a', '#3a4f8a'), 'dawn': ('#2a2a58', '#a86a8a', '#ffb070'), 'day87': ('#6aa0d8', '#9cc4e8', '#e8eef0'),
       'sunrise87': ('#5a6aa0', '#e8a07a', '#ffd8a0'), 'blue': ('#121a3a', '#3a3a6a', '#8a6a8a')}


def sky_dir(v, az, el):
    """Screen position of a world direction (azimuth degrees from +y toward +x, elevation) or None if behind."""
    a, e = math.radians(az), math.radians(el)
    dx, dY, dy = math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e)
    u = dx * v.rx + dy * v.ry; d = dx * v.fx + dy * v.fy
    if d <= 0.05: return None
    return (v.cx + v.S * u / d, v.h - v.S * dY / d)


def sky_dome(pen, v, tod='night', moon=True, stars=True, clouds=True, box=None, seed=3, moon_r=None, glow=1.0):
    """The sky as seen by camera v: a gradient tied to the horizon, stars and the moon at fixed world directions, a few
    soft clouds drifting nowhere."""
    x0, y0, x1, y1 = box or (-700, -500, 2620, 1600)
    top, mid, hor = SKY.get(tod, SKY['night'])
    H = v.h
    r = rect(x0, y0, x1 - x0, y1 - y0)
    pen.linear(r, 0, H - 1.1 * v.S, 0, H + 40, [(0, top), (0.62, mid), (1, hor)])
    if tod in ('dawn', 'sunrise87'):
        sp = sky_dir(v, SUN_AZ, SUN_EL)
        if sp: pen.radial(None, sp[0], sp[1], 1.2 * v.S, [(0, '#ffd8a0', 200), (0.3, '#ff9a6a', 90), (1, '#ff9a6a', 0)], sy=0.45, clip=False)
    if stars and tod in ('night', 'blue'):
        rng = np.random.default_rng(seed)
        for i in range(260):
            az = rng.uniform(-180, 180); el = rng.uniform(4, 70) ** 1.0
            q = sky_dir(v, az, el)
            if q is None or not (x0 < q[0] < x1 and y0 < q[1] < y1): continue
            rr = rng.uniform(0.6, 1.8) * (v.S / 900.0) ** 0.3
            a = rng.uniform(60, 220) * clamp((el - 3) / 12)
            pen.fill(oval(q[0], q[1], rr), '#e4eaff', a)
            if rr > 1.6: pen.glow(q[0], q[1], rr * 5, '#c8d4ff', 50)
    if clouds:
        rng = np.random.default_rng(seed + 9)
        for i in range(7):
            az = rng.uniform(-80, 100); el = rng.uniform(9, 30)
            q = sky_dir(v, az, el)
            if q is None: continue
            w = rng.uniform(0.35, 0.7) * v.S; h = w * 0.12
            if tod in ('night', 'blue'): _cloud(pen, q[0], q[1], w, h, int(rng.integers(0, 999)), '#16204a', '#3a4a86', 170)
            else: _cloud(pen, q[0], q[1], w, h, int(rng.integers(0, 999)), mix(mid, '#ffffff', 0.25), '#ffe0c0', 150)
    if moon and tod in ('night', 'blue'):
        q = sky_dir(v, MOON_AZ, MOON_EL)
        if q is not None:
            rr = moon_r or 0.048 * v.S
            pen.glow(q[0], q[1], rr * 9, '#4f64b0', 60 * glow)
            _moon(pen, q[0], q[1], rr)


def _pine(pen, x, y, h, w, c='#060a12', rim=None, seed=0, a=255):
    """A tall pine silhouette from its base (x, y), h tall, w wide (design px), ragged tiers."""
    rng = np.random.default_rng(seed)
    pts = [(x - w * 0.06, y)]
    tiers = 9
    for i in range(tiers):
        u = i / tiers
        yy = y - h * (0.12 + 0.86 * u)
        ww = w * (1 - u) ** 0.9 * rng.uniform(0.8, 1.1) * 0.5
        pts.append((x - ww, yy + h * 0.03)); pts.append((x - ww * 0.45, yy - h * 0.02))
    pts.append((x, y - h))
    right = []
    for i in range(tiers - 1, -1, -1):
        u = i / tiers
        yy = y - h * (0.12 + 0.86 * u)
        ww = w * (1 - u) ** 0.9 * rng.uniform(0.8, 1.1) * 0.5
        right.append((x + ww * 0.45, yy - h * 0.02)); right.append((x + ww, yy + h * 0.03))
    pts += right + [(x + w * 0.06, y)]
    path = poly(pts)
    pen.fill(path, c, a)
    if rim: pen.shade(path, moved(path, -w * 0.06, h * 0.01), rim[0], rim[1])


def woods(pen, v, y_edge=TREELINE_Y, xr=(-70, 70), depth=40.0, seed=7, tod='night', near_y=None, mist=True, edge_detail=True,
          c_far='#0b1226', c_near='#05070e', rim='#5a6ea8', clearing=None):
    """Holloway Woods behind the yard: a dense band of bare oaks and pines from y_edge back `depth` metres, drawn far ->
    near from camera v, moonlit rims on the near trunks, mist pooling at the treeline. clearing = (x0, x1): a gap in the
    first row (where the Bunnyman stands)."""
    rng = np.random.default_rng(seed)
    trees = []
    for k in range(int((xr[1] - xr[0]) * depth / 9)):
        x = rng.uniform(*xr); y = y_edge + depth * rng.uniform(0, 1) ** 1.6
        trees.append((x, y, rng.uniform(0, 1), int(rng.integers(0, 99999))))
    for k in range(int((xr[1] - xr[0]) * 0.9)):                               # the first row: the treeline itself
        x = rng.uniform(*xr); y = y_edge + rng.uniform(-1.5, 2.5)
        if clearing and clearing[0] < x < clearing[1]: continue
        trees.append((x, y, rng.uniform(0, 1), int(rng.integers(0, 99999))))
    trees.sort(key=lambda q: -v.d(q[0], q[1]))
    fc = {'night': (c_far, c_near), 'dawn': ('#3a3048', '#1a1420'), 'sunrise87': ('#5a4a58', '#2a2028'), 'day87': ('#4a5a48', '#2a3428'),
          'blue': ('#1a1e36', '#0a0c18')}.get(tod, (c_far, c_near))
    # the dark mass of the far woods (a band with a ragged top)
    pts = []
    for i in range(80):
        x = xr[0] + (xr[1] - xr[0]) * i / 79
        hh = 15.0 + 6.0 * (0.5 + 0.5 * math.sin(i * 1.7 + seed)) + 4 * rng.uniform()
        pts.append(v.p(x, hh, y_edge + depth * 0.9))
    far_band = poly(pts + [v.p(xr[1], -1, y_edge + depth * 0.9), v.p(xr[0], -1, y_edge + depth * 0.9)])
    if v.d(0, y_edge + depth) > 0.5:
        pen.fill(far_band, fc[0])
    for (x, y, r, sd) in trees:
        D = v.d(x, y)
        if D < 0.6: continue
        s = v.S / D
        bx, by = v.p(x, 0, y)
        if bx < -900 or bx > 2800: continue
        far_k = clamp((D - 6) / 40.0)
        c = mix(fc[1], fc[0], far_k)
        if r < 0.38:
            hh = (13 + 9 * _h(sd, 1)) * s
            _pine(pen, bx, by, hh, (3.2 + 2.0 * _h(sd, 2)) * s, c, (rim, 40 * (1 - far_k)) if (edge_detail and tod == 'night' and D < 25) else None, sd)
        else:
            hh = (5.5 + 3.5 * _h(sd, 3)) * s
            lit_ = (rim, int(150 * (1 - far_k))) if (edge_detail and D < 30) else None
            draw_tree(pen, bx, by, hh, 0.0, sd, 0.0, c, lit_, 5 if D < 25 else 4, 1.0 + 0.3 * _h(sd, 4), (_h(sd, 5) - 0.5) * 0.15)
    if mist:
        for i, (yy, hh, a) in enumerate(((y_edge - 1.0, 1.2, 70), (y_edge + 2.0, 2.2, 60), (y_edge + 6, 3.5, 45))):
            if v.d(0, yy) < 0.5: continue
            ya, yb = v.p(0, hh, yy)[1], v.p(0, 0, yy)[1]
            mc = {'night': '#6a7ab0', 'dawn': '#e8b8b0', 'sunrise87': '#ffe0c0', 'day87': '#e0e8e8', 'blue': '#8a8ab0'}.get(tod, '#6a7ab0')
            pen.linear(rect(-900, ya, 3700, yb - ya + 20), 0, ya, 0, yb + 10, [(0, mc, 0), (0.7, mc, a), (1, mc, a * 0.6)])


def ground(pen, v, y0, y1, x0=-80.0, x1=80.0, Y=0.0, tod='night', c=None, worn=None, seed=2):
    """The yard: grass from y0 to y1 (plan), mown dark, with a worn path (worn = [(x, y), ...] polyline in plan) and
    clumps of longer grass near the treeline."""
    cc = c or {'night': '#22342c', 'dawn': '#4a5a3a', 'day87': '#5a8a42', 'sunrise87': '#6a7a48', 'blue': '#26302c'}.get(tod, '#22342c')
    F = floor_face(x0, x1, y0, y1, Y)

    def art(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'grunge', 0.55, 'overlay', 6.0)
        p_.texture(rect(0, 0, W, H), 'fabric', 0.35, 'overlay', 0.8)
        if worn:
            pts = [floor_uv(x0, y1, x, y) for (x, y) in worn]
            p_.line(smooth(pts, False, 0.8), 70.0, _darken(cc, 0.25), 150)
            p_.line(smooth(pts, False, 0.8), 40.0, mix(cc, '#6a5a40', 0.35), 120)
    draw_face(pen, v, F, art, cc, ao=False, line=False)


def grass_tufts(pen, v, xr, yr, n=200, seed=4, c='#1a2a22', hi='#4a6a58', Y=0.0):
    """Tufts of long grass standing up from the ground (near ones show blades)."""
    rng = np.random.default_rng(seed)
    pts = [(rng.uniform(*xr), rng.uniform(*yr)) for _ in range(n)]
    pts.sort(key=lambda q: -v.d(q[0], q[1]))
    for (x, y) in pts:
        D = v.d(x, y)
        if D < 1.0: continue
        s = v.S / D
        bx, by = v.p(x, Y, y)
        if not (-600 < bx < 2500 and -200 < by < 1500): continue
        h = (0.18 + 0.2 * rng.uniform()) * s
        for k in range(5):
            dx = (k - 2) * 0.03 * s
            tip = (bx + dx + (k - 2) * 0.05 * s + rng.uniform(-0.03, 0.03) * s, by - h * rng.uniform(0.7, 1.0))
            pen.line(poly([(bx + dx, by), ((bx + dx + tip[0]) / 2, (by + tip[1]) / 2 - 0.01 * s), tip], False), max(0.8, 0.012 * s), c, 230)
        if D < 12: pen.line(poly([(bx, by), (bx + 0.04 * s, by - h * 0.9)], False), max(0.6, 0.006 * s), hi, 120)


# ====================================================================================================== rooms
# A Room draws its shell (floor, walls with openings, ceiling, fixtures that nobody stands behind) and lists its pieces
# (furniture a person can stand behind / sit in: each piece becomes its own layer so people sort against it). Rooms are
# drawn from any BView. Far rooms (seen through an opening) and the outside (seen through a window) are drawn into layers
# behind the main room's shell: see build_view() and BSet.order_at().
ORDER_SHELL, ORDER_FAR, ORDER_OUT = 50.0, 80.0, 900.0


class Piece:
    """A furniture piece: name, plan reference point (x, Y, y) used for its layer depth, draw(pen, v, o), front(v) ->
    optional draw of the parts that sit IN FRONT of an occupant (near arm, chair back seen from behind, the tub's near
    wall, the quilt) with the occupant point (x, y) they are in front of."""

    def __init__(self, name, ref, draw, occupant=None, front=None, block=None, rooms=None):
        self.name, self.ref, self.draw, self.occupant, self.front, self.block = name, ref, draw, occupant, front, block


def _parts_split(parts, v, occ, margin=0.12):
    """Split furniture parts into (behind, in_front) of an occupant at plan point occ = (x, y)."""
    do = v.d(occ[0], occ[1])
    front = [p_ for p_ in parts if p_.depth(v) < do - margin]
    back = [p_ for p_ in parts if p_.depth(v) >= do - margin]
    return back, front


class Room:
    name = 'room'
    poly = []
    Y = 0.0

    def shell(self, pen, v, o): pass

    def pieces(self, o): return []

    def lights(self, o):
        """-> (ambient hex, steady [Lamp], variable [(name, [Lamp], f(t))])."""
        return NIGHT_AMB, [], []

    def spots(self, v, o): return {}

    def glows(self, v, o): return []


def _mk_spot(v, name, x, y, Y=0.0, kind='stand', note='', face=None, seat_Y=None, **kw):
    """A named staging Spot: face = plan direction (fx, fy) the figure faces (gives .turn); seat_Y = seat height (gives
    .seat_y, the design y of the seat top above the spot)."""
    sp_ = v.spot(x, y, Y, note, kind)
    if face is not None: sp_.turn = v.turn_for(x, y, face[0], face[1])
    if seat_Y is not None: sp_.seat_y = v.p(x, Y + seat_Y, y)[1]
    for k_, val in kw.items(): sp_.extra[k_] = val
    return sp_


# ---------------------------------------------------------------------------------------------- living room
class LivingRoom(Room):
    name = 'living'
    poly = [(LIV[0], LIV[2]), (LIV[1], LIV[2]), (LIV[1], LIV[3]), (LIV[0], LIV[3])]

    def lights(self, o):
        amb = o.get('amb', NIGHT_AMB)
        moon = Lamp(kind='win', c=MOON_C, k=0.85 * o.get('moon', 1.0), soft=9.0,
                    panes=_panes_y(LWIN_F[0], LWIN_F[1], LWIN_F[2], LWIN_F[3], 0.0), d=_norm3((0.25, -0.55, 1.0)),
                    only={'floor', 'wall', 'top', 'front', 'side'})
        side = Lamp(kind='win', c=MOON_C, k=0.6 * o.get('moon', 1.0), soft=9.0,
                    panes=_panes_x(LWIN_S[0], LWIN_S[1], LWIN_S[2], LWIN_S[3], -5.0), d=_norm3((1.0, -0.5, 0.25)),
                    only={'floor', 'wall', 'top', 'front', 'side'})
        steady = [moon, side] if o.get('curtains', 1.0) > 0.5 else []
        lampL = [Lamp(FLAMP[0], (FLAMP[2] + FLAMP[3]) / 2, FLAMP[1], 5.2, LAMP_C, 2.1, (1.0, 0.8, 0.9), fall=1.7),
                 Lamp(FLAMP[0] + 0.8, 1.3, FLAMP[1] + 1.2, 7.5, '#ffb070', 0.32, fall=1.2)]
        chairL = [Lamp(SIDETAB[0], SIDETAB[3] + 0.37, SIDETAB[1], 3.6, LAMP_C, 1.6, (1.0, 0.75, 0.8), fall=1.7)]
        hallL = [Lamp(-1.3, 1.9, 2.3, 3.0, LAMP_C, 0.55, (1.0, 1.0, 1.0))]
        kitL = [Lamp(-3.3, 1.5, 5.9, 2.6, '#cfe0ff', 0.25)]
        var = [('lamp', lampL, _kfn(o.get('lamp', 1.0), 51)), ('chair_lamp', chairL, _kfn(o.get('chair_lamp', 0.0), 52)),
               ('hall', hallL, _kfn(o.get('hall', 0.0), 53)), ('kitchen', kitL, _kfn(o.get('kitchen', 0.0), 54))]
        if o.get('tod') == 'dawn':
            amb = '#5a5868'
            steady = [Lamp(kind='win', c=DAWN_C, k=0.9, soft=12.0, panes=_panes_y(LWIN_F[0], LWIN_F[1], LWIN_F[2], LWIN_F[3], 0.0),
                           d=_norm3((-0.6, -0.35, 1.0)))]
        return amb, steady, var

    def shell(self, pen, v, o):
        x0, x1, y0, y1 = LIV
        floor_rect(pen, v, x0, x1, y0, y1, 0.0, P_['floor0'], 'boards', '#5a3a22', seed=11,
                   art=lambda p_, W, H: rug_oval(p_, *floor_uv(x0, y1, RUG_LIV[0], RUG_LIV[1]), RUG_LIV[2] * 100, RUG_LIV[3] * 100))
        for (a, b, holes) in self.walls():
            wall(pen, v, a, b, 0.0, CEIL0, P_['liv_paper'], P_['liv_ink'], 'roses', holes, wains=0.92, rail=None, seed=len(holes),
                 ink2=P_['liv_ink2'], art=self.wall_art(a, b))
        ceil_rect(pen, v, x0, x1, y0, y1, CEIL0)
        fireplace(pen, v)
        bookcase(pen, v)
        for (a, b, (u0, u1, s0, s1)) in ((((-1.4, 0.0), (-5.0, 0.0)), (-1.4 - LWIN_F[1], -1.4 - LWIN_F[0], LWIN_F[2], LWIN_F[3]))[0:1] + (None,)) if False else ():
            pass
        F, panes = window_unit(pen, v, (-1.4, 0.0), (-5.0, 0.0), -1.4 - LWIN_F[1], -1.4 - LWIN_F[0], LWIN_F[2], LWIN_F[3], lites=(2, 2))
        F2, panes2 = window_unit(pen, v, (-5.0, 0.0), (-5.0, 5.8), LWIN_S[0], LWIN_S[1], LWIN_S[2], LWIN_S[3], lites=(2, 2))
        self._win = ((F, panes), (F2, panes2))

    def walls(self):
        return [((-1.4, 0.0), (-5.0, 0.0), [(-1.4 - LWIN_F[1], LWIN_F[2], -1.4 - LWIN_F[0], LWIN_F[3])]),
                ((-5.0, 0.0), (-5.0, 5.8), [(LWIN_S[0], LWIN_S[2], LWIN_S[1], LWIN_S[3])]),
                ((-5.0, 5.8), (-1.4, 5.8), [(LK_OPEN[0] + 5.0, 0.0, LK_OPEN[1] + 5.0, LK_OPEN[2])]),
                ((-1.4, 5.8), (-1.4, 0.0), [(5.8 - LH_OPEN[1], 0.0, 5.8 - LH_OPEN[0], LH_OPEN[2])])]

    def wall_art(self, a, b):
        if a == (-5.0, 5.8):                                  # back wall: Grandma's portrait right of the opening, a clock
            def art(p_, W, H):
                _frame_photo(p_, W, H, 312, H - 205, 46, 58, 'grandma')
                _wall_clock(p_, 30, H - 222, 13)
            return art
        if a == (-1.4, 0.0):                                  # front wall: a small framed sampler 'HOME' left of the window
            def art(p_, W, H):
                _frame_photo(p_, W, H, 18, H - 190, 40, 48, 'sampler')
                _light_switch(p_, 300, H - 120)
            return art
        return None

    def pieces(self, o):
        cp = couch_parts(blanket=o.get('blanket', False))
        wp = wingback_parts()
        seats = couch_seats()
        P = [Piece('couch', (COUCH.cx, 0.45, COUCH.cy), lambda pen, v, parts=cp: draw_parts(pen, v, parts),
                   occupant=[(s[1], s[2]) for s in seats], front=cp, block=COUCH.footprint()),
             Piece('armchair', (ARMCHAIR.cx, 0.5, ARMCHAIR.cy), lambda pen, v, parts=wp: draw_parts(pen, v, parts),
                   occupant=[chair_seat()], front=wp, block=ARMCHAIR.footprint()),
             Piece('coffee', (COFFEE.cx, 0.3, COFFEE.cy), lambda pen, v: (draw_parts(pen, v, table_parts(COFFEE, '#6a3e22', apron=0.06)),
                                                                          _egg_bowl(pen, v, COFFEE.cx + 0.18, COFFEE.Y1, COFFEE.cy)),
                   block=COFFEE.footprint()),
             Piece('endtable', (ENDTAB.cx, 0.3, ENDTAB.cy), lambda pen, v: (draw_parts(pen, v, table_parts(ENDTAB, '#6a3e22', apron=0.05)),
                                                                           _phone(pen, v, ENDTAB.cx, ENDTAB.Y1, ENDTAB.cy)),
                   block=ENDTAB.footprint()),
             Piece('lamp', (FLAMP[0], 1.0, FLAMP[1]), lambda pen, v: lamp_floor(pen, v, FLAMP[0], FLAMP[1], FLAMP[2], FLAMP[3]),
                   block=[(FLAMP[0] - 0.17, FLAMP[1] - 0.17), (FLAMP[0] + 0.17, FLAMP[1] - 0.17), (FLAMP[0] + 0.17, FLAMP[1] + 0.17), (FLAMP[0] - 0.17, FLAMP[1] + 0.17)]),
             Piece('sidetable', (SIDETAB[0], 0.4, SIDETAB[1]), lambda pen, v: _side_table(pen, v), block=_circ(SIDETAB[0], SIDETAB[1], SIDETAB[2] + 0.05)),
             Piece('curtains_front', (-3.3, 1.5, 0.12), lambda pen, v: curtain_pair(pen, v, (-1.4, 0.0), (-5.0, 0.0), -1.4 - LWIN_F[1], -1.4 - LWIN_F[0],
                                                                                     LWIN_F[3], 2.0, 0.0, o.get('curtains', 1.0), P_['drape'], seed=1)),
             Piece('curtains_side', (-4.88, 1.5, 4.75), lambda pen, v: curtain_pair(pen, v, (-5.0, 0.0), (-5.0, 5.8), LWIN_S[0], LWIN_S[1], LWIN_S[3], 1.95, 0.0,
                                                                                     o.get('curtains_side', o.get('curtains', 1.0)), P_['drape'], seed=2))]
        return P

    def glows(self, v, o):
        """Emissive bits that follow a lamp's level: the floor lamp's shade, the chair lamp."""
        kf = _kfn(o.get('lamp', 1.0), 51)
        kc = _kfn(o.get('chair_lamp', 0.0), 52)

        def lamp_glow(pen, t):
            k = kf(t)
            if k <= 0.01: return
            x, y, Yb, Yt = FLAMP
            _shade(pen, v, x, y, Yb, Yt, 0.2, 0.15, '#efe2c4', k)
            gx, gy = v.p(x, (Yb + Yt) / 2, y); s = v.s(x, y)
            pen.glow(gx, gy, 0.9 * s, '#ffd9a0', 70 * k)
            bx, by = v.p(x, Yb - 0.02, y)
            pen.radial(None, bx, by + 0.05 * s, 0.55 * s, [(0, '#fff2d8', 120 * k), (1, '#fff2d8', 0)], sy=0.35, clip=False)

        def chair_glow(pen, t):
            k = kc(t)
            if k <= 0.01: return
            x, y = SIDETAB[0], SIDETAB[1]
            _shade(pen, v, x, y, SIDETAB[3] + 0.28, SIDETAB[3] + 0.46, 0.13, 0.09, '#f2e4c8', k)
            gx, gy = v.p(x, SIDETAB[3] + 0.37, y)
            pen.glow(gx, gy, 0.7 * v.s(x, y), '#ffd9a0', 60 * k)
        return [('lamp_glow', (FLAMP[0], 1.4, FLAMP[1]), lamp_glow), ('chair_glow', (SIDETAB[0], 1.0, SIDETAB[1]), chair_glow)]

    def spots(self, v, o):
        S = {}
        for (nm, x, y) in couch_seats():
            S['couch_' + nm] = _mk_spot(v, 'couch_' + nm, x, y, 0.0, 'seat', 'on the couch (%s seat), facing the back door' % nm,
                                        face=(0, 1), seat_Y=COUCH_SEAT)
        S['couch_lie'] = _mk_spot(v, 'couch_lie', COUCH.cx, COUCH.cy + 0.05, COUCH_SEAT, 'lie', 'lying along the couch seat (head at the lamp end: -x)',
                                  face=(-1, 0))
        cx, cy = chair_seat()
        S['armchair'] = _mk_spot(v, 'armchair', cx, cy, 0.0, 'seat', "Mom's wingback, facing the back door through the kitchen opening",
                                 face=(0, 1), seat_Y=CHAIR_SEAT)
        S['window_front'] = _mk_spot(v, 'window_front', -3.3, 0.42, 0.0, 'stand', 'behind the couch at the front window (closing the curtains)', face=(0, -1))
        S['curtain_front_l'] = _mk_spot(v, 'curtain_front_l', -2.42, 0.12, 1.3, 'point', 'the front curtains: left panel edge (reach target)')
        S['curtain_front_r'] = _mk_spot(v, 'curtain_front_r', -4.18, 0.12, 1.3, 'point', 'the front curtains: right panel edge')
        S['window_side'] = _mk_spot(v, 'window_side', -4.55, 4.75, 0.0, 'stand', 'at the side window', face=(-1, 0))
        S['coffee_top'] = _mk_spot(v, 'coffee_top', COFFEE.cx, COFFEE.cy, COFFEE.Y1, 'surface', 'the coffee table top (the bowl of eggs at +0.18 m)')
        S['endtable_top'] = _mk_spot(v, 'endtable_top', ENDTAB.cx, ENDTAB.cy, ENDTAB.Y1, 'surface', 'the end table (the phone)')
        S['sidetable_top'] = _mk_spot(v, 'sidetable_top', SIDETAB[0], SIDETAB[1], SIDETAB[3], 'surface', "the side table by Mom's chair")
        S['mantel'] = _mk_spot(v, 'mantel', CHIMNEY[1] + 0.1, (CHIMNEY[2] + CHIMNEY[3]) / 2, MANTEL_Y + 0.06, 'surface', 'the mantel shelf')
        S['room_mid'] = _mk_spot(v, 'room_mid', -3.3, 3.4, 0.0, 'stand', 'between the coffee table and the armchair')
        S['hall_open'] = _mk_spot(v, 'hall_open', -1.55, 2.3, 0.0, 'stand', 'in the opening to the front hall')
        S['kitchen_open'] = _mk_spot(v, 'kitchen_open', -3.3, 5.75, 0.0, 'stand', 'in the opening to the kitchen')
        S['fireplace'] = _mk_spot(v, 'fireplace', -4.1, 3.0, 0.0, 'stand', 'in front of the fireplace', face=(-1, 0))
        return S


def _panes_y(x0, x1, sill, top, y, Y0=0.0):
    """Window glass rectangles on a wall at constant y (for the moonlight patches)."""
    xs = sorted((x0, x1)); mid = (sill + top) / 2
    out = []
    for (Ya, Yb) in ((sill + 0.05, mid - 0.03), (mid + 0.03, top - 0.05)):
        for (xa, xb) in ((xs[0] + 0.05, (xs[0] + xs[1]) / 2 - 0.01), ((xs[0] + xs[1]) / 2 + 0.01, xs[1] - 0.05)):
            out.append([(xa, Y0 + Yb, y), (xb, Y0 + Yb, y), (xb, Y0 + Ya, y), (xa, Y0 + Ya, y)])
    return out


def _panes_x(y0, y1, sill, top, x, Y0=0.0):
    ys = sorted((y0, y1)); mid = (sill + top) / 2
    out = []
    for (Ya, Yb) in ((sill + 0.05, mid - 0.03), (mid + 0.03, top - 0.05)):
        for (ya, yb) in ((ys[0] + 0.05, (ys[0] + ys[1]) / 2 - 0.01), ((ys[0] + ys[1]) / 2 + 0.01, ys[1] - 0.05)):
            out.append([(x, Y0 + Yb, ya), (x, Y0 + Yb, yb), (x, Y0 + Ya, yb), (x, Y0 + Ya, ya)])
    return out


def _circ(x, y, r, n=12):
    return [(x + r * math.cos(2 * math.pi * i / n), y + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _frame_photo(p_, W, H, x, y, w, h, kind='grandma', frame='#5a3a20'):
    """A framed picture in a wall's cm frame: 'grandma' (her portrait: silver bun, glasses, lavender), 'wedding' (Mom and
    Dad), 'june' (school photo), 'laurie' (1987, the yellow dress), 'sampler' (cross-stitch HOME), 'woods' (a print)."""
    def fn(q, w_, h_):
        if kind == 'grandma': _portrait(q, w_, h_, 'grandma')
        elif kind == 'wedding': _portrait(q, w_, h_, 'wedding')
        elif kind == 'june': _portrait(q, w_, h_, 'june')
        elif kind == 'laurie': _photo_laurie(q, 0, 0, w_, h_)
        elif kind == 'sampler':
            q.fill(rect(0, 0, w_, h_), '#efe6d0'); q.texture(rect(0, 0, w_, h_), 'fabric', 0.6, 'overlay', 0.4)
            btext(q, 'HOME', w_ / 2, h_ * 0.55, 'kid', h_ * 0.28, '#a83a3a', 230, 'center')
            for k in range(5): q.fill(oval(w_ * (0.2 + 0.15 * k), h_ * 0.8, 1.6), ['#e8a0b0', '#f2d07a', '#9fd3f0', '#b9e0a5', '#d9b3f0'][k])
        elif kind == 'woods':
            q.linear(rect(0, 0, w_, h_), 0, 0, 0, h_, ['#4a5a7a', '#8a9a8a', '#3a4a3a'])
            for k in range(7): q.fill(poly([(k * w_ / 6, h_), (k * w_ / 6 + w_ * 0.06, h_ * 0.2), (k * w_ / 6 + w_ * 0.12, h_)]), '#1a2a22')
    _hframe(p_, W, H, x, y, w, h, 'poster', frame=frame, fn=fn)


def _portrait(q, w, h, kind):
    q.linear(rect(0, 0, w, h), 0, 0, 0, h, ['#b8a890', '#8a7a68'] if kind != 'june' else ['#6a8ab8', '#3a5a88'])
    cx = w / 2
    if kind == 'grandma':
        q.fill(smooth([(cx - w * 0.36, h), (cx - w * 0.32, h * 0.66), (cx, h * 0.6), (cx + w * 0.32, h * 0.66), (cx + w * 0.36, h)], True, 0.6), '#9a86b8')
        q.fill(oval(cx, h * 0.42, w * 0.2, h * 0.17), '#e6c8b0')
        q.fill(oval(cx, h * 0.27, w * 0.22, h * 0.09), '#d8d8dc'); q.fill(oval(cx, h * 0.2, w * 0.1, h * 0.05), '#d8d8dc')
        for s_ in (-1, 1): q.line(oval(cx + s_ * w * 0.08, h * 0.42, w * 0.06, h * 0.035), 0.8, '#5a4a3a')
        q.line(smooth([(cx - w * 0.07, h * 0.51), (cx, h * 0.53), (cx + w * 0.07, h * 0.51)], False), 0.7, '#8a5a50')
        q.fill(oval(cx, h * 0.66, w * 0.03), '#d8b04c')
    elif kind == 'wedding':
        for s_, hc, bc in ((-1, '#5a3a24', '#2a2a32'), (1, '#b8562a', '#f2efe6')):
            x = cx + s_ * w * 0.2
            q.fill(smooth([(x - w * 0.18, h), (x - w * 0.15, h * 0.62), (x, h * 0.56), (x + w * 0.15, h * 0.62), (x + w * 0.18, h)], True, 0.6), bc)
            q.fill(oval(x, h * 0.42, w * 0.11, h * 0.12), '#e6c8b0'); q.fill(oval(x, h * 0.33, w * 0.12, h * 0.06), hc)
        q.fill(oval(cx + w * 0.2, h * 0.3, w * 0.16, h * 0.05), '#ffffff', 160)
    else:
        q.fill(smooth([(cx - w * 0.3, h), (cx - w * 0.26, h * 0.7), (cx, h * 0.64), (cx + w * 0.26, h * 0.7), (cx + w * 0.3, h)], True, 0.6), '#a8e0d0')
        q.fill(oval(cx, h * 0.46, w * 0.17, h * 0.16), '#f0cdb0')
        q.fill(oval(cx, h * 0.33, w * 0.19, h * 0.08), '#a8743a')
        for s_ in (-1, 1): q.fill(oval(cx + s_ * w * 0.23, h * 0.52, w * 0.06, h * 0.12), '#a8743a')


def _wall_clock(p_, x, y, r, hh=11, mm=7):
    p_.fill(oval(x + 1.5, y + 2.5, r), '#000000', 80)
    p_.fill(oval(x, y, r), '#7a4a2a'); p_.fill(oval(x, y, r * 0.84), '#f4eedc'); p_.line(oval(x, y, r), 0.8, '#000000', 180)
    for k in range(12):
        a = 2 * math.pi * k / 12
        p_.seg((x + math.sin(a) * r * 0.7, y - math.cos(a) * r * 0.7), (x + math.sin(a) * r * 0.8, y - math.cos(a) * r * 0.8), 0.8, '#2a2a2a')
    am = 2 * math.pi * mm / 60; ah = 2 * math.pi * ((hh % 12) + mm / 60) / 12
    p_.seg((x, y), (x + math.sin(ah) * r * 0.45, y - math.cos(ah) * r * 0.45), 1.4, '#1a1a1a')
    p_.seg((x, y), (x + math.sin(am) * r * 0.68, y - math.cos(am) * r * 0.68), 0.9, '#1a1a1a')
    p_.fill(oval(x, y, 0.9), '#a8262a')


def _light_switch(p_, x, y, on=True, label=None):
    p_.fill(rrect(x - 4, y - 6.5, 8, 13, 0.8), '#efe6d0'); p_.line(rrect(x - 4, y - 6.5, 8, 13, 0.8), 0.6, '#000000', 120)
    p_.fill(rrect(x - 1.1, y - (3.2 if on else 0.4), 2.2, 3.6, 0.6), '#f8f2e4'); p_.line(rrect(x - 1.1, y - (3.2 if on else 0.4), 2.2, 3.6, 0.6), 0.5, '#000000', 140)
    if label:
        p_.fill(rect(x - 6, y + 8, 12, 4), '#e8dca0'); btext(p_, label, x, y + 11.2, 'hand', 3.2, '#2a2a6a', 230, 'center')


def _egg_bowl(pen, v, x, Y, y):
    """A wooden bowl of pastel plastic eggs (vertex-lit)."""
    s = v.s(x, y)
    bx, by = v.p(x, Y, y)
    bowl = ellipse3(v, x, y, 0.14, 0.14, Y + 0.07)
    b = _rb(bowl)
    body = union(bowl, poly([(b[0], (b[1] + b[3]) / 2), (b[2], (b[1] + b[3]) / 2), (bx + 0.08 * s, by), (bx - 0.08 * s, by)]))
    pen.fill(body, lit('#8a5a30', (x, Y, y), None)); pen.line(body, 1.0)
    cols = ['#f2a5b5', '#f6d978', '#9fd3f0', '#b9e0a5', '#d9b3f0', '#f2a5b5', '#f6d978']
    for i, (dx, dy) in enumerate(((-0.06, 0.02), (0.0, -0.03), (0.06, 0.01), (-0.02, 0.05), (0.04, 0.06), (-0.07, -0.04), (0.08, -0.05))):
        ex, ey = v.p(x + dx, Y + 0.1, y + dy)
        e = oval(ex, ey, 0.03 * s, 0.04 * s)
        pen.fill(e, lit(cols[i], (x, Y + 0.1, y), (0, 1, 0), 1.2)); pen.line(e, 0.8)
    pen.fill(ellipse3(v, x, y, 0.13, 0.13, Y + 0.075), '#000000', 0)


def _phone(pen, v, x, Y, y):
    """A cream rotary telephone on the end table."""
    s = v.s(x, y)
    px, py = v.p(x, Y, y)
    base = smooth([(px - 0.1 * s, py), (px - 0.08 * s, py - 0.07 * s), (px + 0.08 * s, py - 0.07 * s), (px + 0.1 * s, py)], True, 0.6)
    pen.fill(base, lit('#e8dcc0', (x, Y, y), None)); pen.line(base, 1.0)
    pen.fill(oval(px, py - 0.045 * s, 0.045 * s, 0.02 * s), lit('#cfc2a4', (x, Y, y), None))
    hs = smooth([(px - 0.11 * s, py - 0.08 * s), (px - 0.09 * s, py - 0.11 * s), (px + 0.09 * s, py - 0.11 * s), (px + 0.11 * s, py - 0.08 * s),
                 (px + 0.07 * s, py - 0.085 * s), (px - 0.07 * s, py - 0.085 * s)], True, 0.7)
    pen.fill(hs, lit('#efe4c8', (x, Y, y), None)); pen.line(hs, 1.0)


def _side_table(pen, v):
    x, y, r, h = SIDETAB
    top = ellipse3(v, x, y, r, r, h)
    pen.fill(ellipse3(v, x, y, r, r, h - 0.03), lit('#5a3420', (x, h, y), None))
    tx, ty = v.p(x, h - 0.03, y); bx, by = v.p(x, 0.0, y); s = v.s(x, y)
    pen.seg((tx, ty), (bx, by - 0.05 * s), max(2.0, 0.05 * s), LINE); pen.seg((tx, ty), (bx, by - 0.05 * s), max(1.4, 0.035 * s), lit('#6a4028', (x, 0.3, y), None))
    pen.fill(ellipse3(v, x, y, 0.16, 0.16, 0.0), lit('#5a3420', (x, 0.0, y), None)); pen.line(ellipse3(v, x, y, 0.16, 0.16, 0.0), 1.0)
    pen.fill(top, lit('#7a4a2a', (x, h, y), (0, 1, 0))); pen.line(top, 1.2)
    # the little lamp and a ceramic bunny
    lx, ly = v.p(x - 0.06, h, y + 0.05)
    pen.seg((lx, ly), v.p(x - 0.06, h + 0.3, y + 0.05), max(1.2, 0.012 * s), lit('#b08a4a', (x, h, y), None))
    pen.fill(ellipse3(v, x - 0.06, y + 0.05, 0.06, 0.06, h + 0.01), lit('#8a6a3a', (x, h, y), None))
    _shade(pen, v, x - 0.06, y + 0.05, h + 0.28, h + 0.46, 0.13, 0.09, '#f2e4c8', 0.0)
    _ceramic_bunny(pen, v, x + 0.09, h, y - 0.08, 0.13)


# ====================================================================================================== views
_epost.GRADES.setdefault('ob_night', dict(contrast=1.08, pivot=0.24, gamma=1.0, sat=1.14, wb=(1.02, 1.0, 0.98), floor='#080a16',
                                          bloom=0.8, bloom_thr=226, vignette=0.38, grain=0.7, shoulder=0.45))
_epost.GRADES.setdefault('ob_dark', dict(contrast=1.06, pivot=0.24, gamma=0.98, sat=1.08, wb=(0.95, 0.99, 1.08), floor='#05070f',
                                         bloom=0.85, bloom_thr=224, vignette=0.34, grain=0.8, shoulder=0.45))
_epost.GRADES.setdefault('ob_dawn', dict(exposure=0.12, contrast=1.04, pivot=0.25, gamma=1.03, sat=1.05, wb=(1.08, 1.0, 0.9),
                                         floor='#120c10', bloom=0.9, bloom_thr=222, vignette=0.4, grain=0.6, shoulder=0.5))
_epost.GRADES.setdefault('ob_memory', dict(exposure=0.1, contrast=0.95, pivot=0.26, gamma=1.04, sat=0.72, wb=(1.08, 1.0, 0.86),
                                           floor='#1a120c', bloom=0.7, bloom_thr=226, vignette=0.5, grain=1.0, soft=0.5, shoulder=0.5))
_epost.GRADES.setdefault('ob_ext', dict(contrast=1.1, pivot=0.22, gamma=0.98, sat=1.12, wb=(0.96, 1.0, 1.06), floor='#04060e',
                                        bloom=0.9, bloom_thr=228, vignette=0.36, grain=0.8, shoulder=0.45))
_epost.GRADES.setdefault('ob_vhs87', dict(exposure=0.12, contrast=0.96, pivot=0.3, gamma=1.03, sat=1.08, wb=(1.06, 1.0, 0.9), floor='#14100e',
                                          bloom=0.8, bloom_thr=222, vignette=0.55, grain=0.0, soft=0.4, shoulder=0.55))
_epost.GRADES.setdefault('ob_sunrise87', dict(exposure=0.15, contrast=1.0, pivot=0.26, gamma=1.04, sat=0.95, wb=(1.1, 1.0, 0.86),
                                              floor='#18100c', bloom=1.0, bloom_thr=220, vignette=0.42, grain=1.0, soft=0.4, shoulder=0.55))
_epost.GRADES.setdefault('ob_hospital', dict(exposure=0.1, contrast=1.0, pivot=0.25, gamma=1.03, sat=0.7, wb=(0.95, 1.02, 1.04),
                                             floor='#0c1214', bloom=0.6, bloom_thr=232, vignette=0.42, grain=0.8, shoulder=0.5))

CAMS = {}


def cam(name, **over):
    """The named camera (a BView) from the CAMS table (every view's camera on the plan: PLAN_MAP draws them)."""
    c = dict(CAMS[name]); c.update(over)
    env = c.pop('env', None); c.pop('note', None); c.pop('room', None)
    v = BView(c.pop('S'), c.pop('h'), c.pop('eye'), c.pop('x'), c.pop('y'), c.pop('yaw'), name=name, **c)
    v.env = env
    return v


def _cam(name, S, h, eye, x, y, yaw, env=None, note='', room=''):
    CAMS[name] = dict(S=S, h=h, eye=eye, x=x, y=y, yaw=yaw, env=env or dict(x=(900, 1020), y=(500, 580), zoom=(1.0, 1.12), f=(1.0, 1.4)),
                      note=note, room=room)


def _okey(o):
    """A cache-key string for a view's options (only the values that change static art / light)."""
    parts = []
    for k_ in sorted(o):
        val = o[k_]
        if callable(val) or isinstance(val, dict): parts.append('%s=f' % k_); continue
        parts.append('%s=%s' % (k_, round(val, 3) if isinstance(val, float) else val))
    return ','.join(parts)


def _art_parts(R, parts_fn):
    return lambda pen: parts_fn(pen)


def build_view(vname, v, main, o, far=(), outside=None, lens='lens', grade='ob_night', focus=None, dof=0.8, cover=None, extra=None,
               dyn=None, info_extra=None):
    """Assemble a set from rooms seen by camera v: the outside (seen through windows, drawn first), far rooms (seen through
    openings: their shell at ORDER_FAR, their pieces at ORDER_SHELL + 0.1 depth), the main room's shell (ORDER_SHELL) and
    each main piece as its own layer at its real depth (seats split into the parts behind / in front of the occupant).
    extra: [(name, ref (x, Y, y), draw(pen, v) static, room)] extra static pieces; dyn: [Layer] animated layers."""
    cover = cover or FRAME
    key = 'ob:%s:%s' % (vname, _okey(o))
    L = []
    amb, steady, var = main.lights(o)
    info = {'view': v, 'amb': amb, 'lights': steady, 'var_lights': var, 'floors': [main.poly], 'blocks': {}, 'rooms': {main.name: main.poly},
            'cam_env': getattr(v, 'env', None), 'floor_order': ORDER_SHELL, 'orders': {}, 'room': main.name}
    if outside is not None:
        L.append(Layer(30.0, lambda pen, t: outside(pen, v), 'outside', cache=key + ':out', bounds=cover))
        L[-1].order = ORDER_OUT
    for i, R in enumerate(far):
        famb, fst, fvar = R.lights(o)
        dctr = max(1.0, v.d(sum(p_[0] for p_ in R.poly) / len(R.poly), sum(p_[1] for p_ in R.poly) / len(R.poly)))
        L += blit(dctr, (lambda R_: lambda pen: R_.shell(pen, v, o))(R), 'far_' + R.name, key + ':far:' + R.name, cover, famb, fst, fvar,
                  order=ORDER_FAR + i)
        for P in R.pieces(o):
            d = v.d(P.ref[0], P.ref[2])
            if d < v.near + 0.2: continue
            L += blit(max(0.3, d), (lambda P_: lambda pen: P_.draw(pen, v))(P), 'far_%s_%s' % (R.name, P.name),
                      key + ':farp:%s:%s' % (R.name, P.name), cover, famb, fst, fvar, order=ORDER_SHELL + 0.1 * d)
            if P.block: info['blocks'][P.name] = P.block
        info['floors'].append(R.poly); info['rooms'][R.name] = R.poly
        for g in R.glows(v, o):
            nm, ref, fn = g
            d = v.d(ref[0], ref[2])
            if d < v.near + 0.2: continue
            lay = Layer(max(0.3, d), (lambda f_: lambda pen, t: f_(pen, t))(fn), 'far_' + nm, blur=None); lay.order = ORDER_SHELL + 0.1 * d - 0.001
            L.append(lay)
    cx = sum(p_[0] for p_ in main.poly) / len(main.poly); cy = sum(p_[1] for p_ in main.poly) / len(main.poly)
    dmain = max(1.0, v.d(cx, cy))
    L += blit(dmain, lambda pen: main.shell(pen, v, o), 'shell', key + ':shell', cover, amb, steady, var, order=ORDER_SHELL)
    pieces = list(main.pieces(o))
    for P in pieces:
        d = v.d(P.ref[0], P.ref[2])
        if P.block: info['blocks'][P.name] = P.block
        if d < v.near + 0.15: continue
        if P.occupant and P.front:
            occ = [q for q in P.occupant if v.d(q[0], q[1]) > v.near]
            if occ:
                dmin = min(v.d(q[0], q[1]) for q in occ); dmax = max(v.d(q[0], q[1]) for q in occ)
                front = [p_ for p_ in P.front if p_.depth(v) < dmin - 0.14]
                back = [p_ for p_ in P.front if p_.depth(v) >= dmin - 0.14]
                L += blit(max(0.3, d), (lambda ps: lambda pen: draw_parts(pen, v, ps))(back), P.name, key + ':p:' + P.name, cover, amb, steady, var,
                          order=dmax + 0.06)
                info['orders'][P.name] = dmax + 0.06
                if front:
                    L += blit(max(0.3, dmin - 0.2), (lambda ps: lambda pen: draw_parts(pen, v, ps))(front), P.name + '_front', key + ':pf:' + P.name,
                              cover, amb, steady, var, order=dmin - 0.06)
                    info['orders'][P.name + '_front'] = dmin - 0.06
                continue
        L += blit(max(0.3, d), (lambda P_: lambda pen: P_.draw(pen, v))(P), P.name, key + ':p:' + P.name, cover, amb, steady, var, order=d)
        info['orders'][P.name] = d
    for (nm, ref, fn) in (extra or []):
        d = v.d(ref[0], ref[2])
        if d < v.near + 0.15: continue
        L += blit(max(0.3, d), (lambda f_: lambda pen: f_(pen, v))(fn), nm, key + ':x:' + nm, cover, amb, steady, var, order=d)
        info['orders'][nm] = d
    for g in main.glows(v, o):
        nm, ref, fn = g
        d = v.d(ref[0], ref[2])
        if d < v.near + 0.15: continue
        lay = Layer(max(0.3, d), (lambda f_: lambda pen, t: f_(pen, t))(fn), nm, blur=None)
        lay.order = info['orders'].get(nm.replace('_glow', ''), d) - 0.001
        L.append(lay)
    for lay in (dyn or []):
        L.append(lay)
    anchors = main.spots(v, o)
    for R in far:
        for k_, s_ in R.spots(v, o).items():
            anchors.setdefault(k_, s_)
    if info_extra: info.update(info_extra)
    sp = BSet(vname, L, anchors, {}, lens=lens, grade=grade, focus=focus or dmain, dof=dof, cover=cover, info=info, view=v, room=main.name)
    sp.far = list(far)
    return sp


def _order_at(self, x, y):
    """Draw order for a figure standing at plan (x, y): its depth in the main room; ORDER_SHELL + 0.1 depth in a room seen
    through an opening (so the main room's walls hide what is outside the opening); ORDER_SHELL + 20 + 0.1 depth outside."""
    v = self.view
    d = v.d(x, y)
    rooms = self.info.get('rooms', {})
    main = rooms.get(self.room)
    if main and _in_poly((x, y), main): return d
    for nm, q in rooms.items():
        if nm != self.room and _in_poly((x, y), q): return ORDER_SHELL + 0.1 * d
    return ORDER_SHELL + 20.0 + 0.1 * d


BSet.order_at = _order_at


def _figure_kw(self, x, y, Y=1.2, floor=0.45):
    """Everything a figure layer at plan (x, y) needs from the set: dict(depth, order, ppm, x, y (design feet), tint, dim)."""
    s_ = self.view.spot(x, y)
    kw = self.light_kw(x, y, Y, floor)
    return dict(depth=s_.depth, order=self.order_at(x, y), ppm=s_.ppm, x=s_.x, y=s_.y, **kw)


BSet.figure_kw = _figure_kw


# ---------------------------------------------------------------------------------------------- living room views
_cam('liv_wide', 860, 470, 1.5, -1.72, 5.5, -146, dict(x=(880, 1060), y=(450, 600), zoom=(1.0, 1.15), f=(1.0, 1.6)),
     'from the back-right corner: the couch (kids) under the lamp, the curtained front window, the fireplace; Mom\'s wingback in the right foreground facing camera-right (the back door)', 'living')
_cam('liv_back', 980, 455, 1.5, -3.3, 9.55, 180, dict(x=(880, 1040), y=(440, 600), zoom=(1.0, 1.15), f=(1.0, 2.0)),
     'the back door\'s point of view: through the kitchen opening, Mom in the wingback facing the lens, the couch with the kids behind her', 'living')
_cam('liv_chair', 900, 520, 1.2, -2.95, 1.95, 6, dict(x=(880, 1040), y=(470, 600), zoom=(1.0, 1.12), f=(1.0, 1.8)),
     'from the couch: the back of Mom\'s wingback, the opening, the dark kitchen, the back door', 'living')
_cam('liv_couch', 1000, 520, 1.25, -2.05, 3.85, -150, dict(x=(860, 1060), y=(470, 620), zoom=(1.0, 1.12), f=(1.0, 1.6)),
     'medium on the couch from the front-right: the lamp, the seats, the curtains behind', 'living')
_cam('liv_window', 900, 470, 1.55, -3.3, 3.3, 180, dict(x=(880, 1040), y=(440, 600), zoom=(1.0, 1.12), f=(1.0, 1.6)),
     'the front window over the back of the couch: the curtains (open / closing / closed)', 'living')
_cam('liv_hall', 860, 470, 1.55, 0.35, 2.3, -90, dict(x=(880, 1040), y=(440, 600), zoom=(1.0, 1.12), f=(1.0, 1.6)),
     'from the front hall into the living room through the opening: the fireplace wall facing us', 'living')


def ob_living(view='wide', lamp=1.0, chair_lamp=0.0, hall=0.0, kitchen=0.0, curtains=1.0, curtains_side=None, blanket=False, moon=1.0,
              tod='night', back_door=0.0, **kw):
    """The living room (one floor plan with the hall and the kitchen). view:
      'wide'   from the back-right corner: the couch under the floor lamp, the front window, the fireplace; Mom's wingback in
               the right foreground (anchors armchair, couch_left/mid/right, couch_lie)
      'back'   the back door's point of view: through the kitchen opening, the wingback facing the lens, the couch behind
      'chair'  from the couch: the back of the wingback, the opening, the dark kitchen and the back door
      'couch'  medium on the couch      'window'  the front window (curtains 1 = open, 0 = closed, or f(t))      'hall'
    Lights (level specs): lamp (the floor lamp), chair_lamp (the little lamp by the wingback), hall (the hall light through
    the opening), kitchen. blanket: June's blanket left on the couch. Grade ob_night / ob_dark (all off)."""
    v = cam('liv_' + view)
    o = dict(lamp=lamp, chair_lamp=chair_lamp, hall=hall, kitchen=kitchen, curtains=curtains if not callable(curtains) else 0.5,
             blanket=blanket, moon=moon, tod=tod, back_door=back_door)
    if curtains_side is not None: o['curtains_side'] = curtains_side
    dynl = []
    if callable(curtains):                                     # animated curtains: draw them live instead of cached
        o['curtains'] = 'live'
    main = LivingRoom()
    far = [KitchenRoom(), HallRoom()] if view in ('wide', 'chair', 'couch', 'hall', 'window', 'back') else []
    if view == 'back':
        main = LivingRoom(); far = [HallRoom()]
        sp = build_view('ob_living_back', v, KitchenRoom(), o, far=[LivingRoom(), HallRoom()], outside=lambda pen, v_: _outside_back(pen, v_, tod),
                        grade='ob_night' if (lamp or hall) else 'ob_dark')
        return sp
    out = (lambda pen, v_: _outside_front(pen, v_, tod)) if view in ('wide', 'couch', 'window', 'hall') else (lambda pen, v_: _outside_back(pen, v_, tod))
    sp = build_view('ob_living_' + view, v, main, o, far=far, outside=out, grade='ob_night', dyn=dynl)
    return sp


# ---------------------------------------------------------------------------------------------- kitchen
KCOUNTER = (-2.62, 1.3, 9.38, 10.0)                          # counter run along the back wall (x0, x1, y0, y1)
KSINK = (-1.78, -0.92)                                       # the sink bowl x range (under the window)


def back_door(swing_ang=0.0, broken=0.0, latch_turn=1.0, chain_on=True):
    """The kitchen's back door: white, a nine-lite window with a gingham curtain in its upper half, deadbolt + chain."""
    art = door_art('glass', 'right', bolt=True, chain=True, chain_on=chain_on, turn=latch_turn, scuff=0.4)
    return Door((BDOOR[0], 10.04), BDOOR[1] - BDOOR[0], BDOOR[2], (1.0, 0.0), -1, 0.0, art_a=art, art_b=door_art('glass', 'left', knob=True, bolt=False))


def _bdoor_glass(pen, v, D, ang=0.0, curtain=True, broken=0.0):
    """The back door's window: the night through the nine lites, the gingham half-curtain (drawn on face a)."""
    d = D.dir(ang); n = (d[1], -d[0])
    O = (D.hinge[0] + d[0] * 0.11 + n[0] * (D.thick / 2 + 0.002), DOOR_H - 0.11, D.hinge[1] + d[1] * 0.11 + n[1] * (D.thick / 2 + 0.002))
    F = Face(O, (d[0], 0, d[1]), (0, -1, 0), (D.w - 0.22) * 100, (DOOR_H * 0.52 - 0.11) * 100, (n[0], 0, n[1]), 'front')
    W, H = F.W, F.H
    lites = [rect(i * W / 3 + 1.2, j * H / 3 + 1.2, W / 3 - 2.4, H / 3 - 2.4) for i in range(3) for j in range(3)]

    def art(p_, W, H):
        p_.fill(rect(0, 0, W, H), DOOR_PANEL)
        if curtain:
            ct = poly([(0, H * 0.3), (W, H * 0.3)] + [(x, H + 1.5 * math.sin(x * 0.5)) for x in np.linspace(W, 0, 18)])
            p_.fill(ct, '#e8dcc8'); pat(p_, W, H, 'gingham', '#c84a4a', 170) if False else None
            p_.cv.save(); p_.cv.clipPath(ct, skia.ClipOp.kIntersect, True); pat(p_, W, H, 'gingham', '#c84a4a', 190); p_.cv.restore()
            p_.fill(rect(0, H * 0.3 - 1.2, W, 1.8), '#b8a070')
    holes = lites if not curtain else [rect(i * W / 3 + 1.2, j * H / 3 + 1.2, W / 3 - 2.4, min(H / 3 - 2.4, H * 0.3 - j * H / 3 - 2.4))
                                       for i in range(3) for j in range(3) if j * H / 3 + 1.2 < H * 0.3 - 2.4]
    draw_face(pen, v, F, art, DOOR_PANEL, holes=holes, ao=False, lw=0.9)


class KitchenRoom(Room):
    name = 'kitchen'
    poly = [(KIT[0], KIT[2]), (KIT[1], KIT[2]), (KIT[1], KIT[3]), (KIT[0], KIT[3])]

    def lights(self, o):
        amb = o.get('amb_k', '#283050')
        win = Lamp(kind='win', c=MOON_C, k=0.9 * o.get('moon', 1.0), soft=8.0, panes=_panes_y(KWIN[0], KWIN[1], KWIN[2], KWIN[3], 10.0),
                   d=_norm3((-0.15, -0.5, -1.0)), only={'floor', 'top', 'front', 'side', 'wall'})
        bd = Lamp(kind='win', c=MOON_C, k=0.6 * o.get('moon', 1.0), soft=8.0, panes=[[(BDOOR[0] + 0.12, 2.0, 10.0), (BDOOR[1] - 0.12, 2.0, 10.0),
                                                                                       (BDOOR[1] - 0.12, 1.45, 10.0), (BDOOR[0] + 0.12, 1.45, 10.0)]],
                  d=_norm3((0.1, -0.55, -1.0)), only={'floor', 'top', 'front', 'side'})
        steady = [win, bd]
        pend = [Lamp(KTABLE.cx, 1.75, KTABLE.cy, 3.8, '#ffd59a', 1.25, (1.0, 0.7, 0.9))]
        porch = [Lamp(BACK_LIGHT[0], 1.9, 10.4, 2.2, '#ffcf8a', 0.5, only={'floor', 'top', 'front'})]
        var = [('kitchen', pend, _kfn(o.get('kitchen', 0.0), 61)), ('porch', porch, _kfn(o.get('porch', 0.0), 62))]
        if o.get('tod') == 'memory':
            amb = '#9a8a78'
            steady = [Lamp(kind='win', c='#fff0d0', k=1.1, soft=14.0, panes=_panes_y(KWIN[0], KWIN[1], KWIN[2], KWIN[3], 10.0), d=_norm3((-0.3, -0.45, -1.0)))]
        if o.get('tod') == 'dawn':
            amb = '#5a5468'
        return amb, steady, var

    def shell(self, pen, v, o):
        x0, x1, y0, y1 = KIT
        floor_rect(pen, v, x0, x1, y0, y1, 0.0, P_['lino1'], 'lino', P_['lino0'], P_['lino1'], seed=5,
                   art=(lambda p_, W, H: _mud_trail(p_, W, H, o.get('mud', 0.0))) if o.get('mud') else None)
        holes_front = [(1.3 - HK_DOOR[1], 0.0, 1.3 - HK_DOOR[0], HK_DOOR[2]), (1.3 - LK_OPEN[1], 0.0, 1.3 - LK_OPEN[0], LK_OPEN[2])]
        bd_open = o.get('back_door', 0.0)
        for (a, b, holes) in (((1.3, 5.8), (-5.0, 5.8), holes_front), ((-5.0, 5.8), (-5.0, 10.0), []),
                              ((-5.0, 10.0), (1.3, 10.0), [(BDOOR[0] + 5.0, 0.0, BDOOR[1] + 5.0, BDOOR[2]), (KWIN[0] + 5.0, KWIN[2], KWIN[1] + 5.0, KWIN[3])]),
                              ((1.3, 10.0), (1.3, 5.8), [(10.0 - 9.25, 0.0, 10.0 - 8.45, 2.03)])):
            wall(pen, v, a, b, 0.0, CEIL0, P_['kit_wall'], '#d9a84a', 'ditsy', holes, wains=0.0, seed=7, ink2='#e46a5a', scale=1.2,
                 art=self.wall_art(a, b, o))
        ceil_rect(pen, v, x0, x1, y0, y1, CEIL0)
        # the window over the sink (smashed at 4:30) and its gingham cafe curtains
        F, panes = window_unit(pen, v, (-5.0, 10.0), (1.3, 10.0), KWIN[0] + 5.0, KWIN[1] + 5.0, KWIN[2], KWIN[3], lites=(2, 2),
                               broken=o.get('smash', 0.0), seed=3)
        self._win = (F, panes)
        _cafe_curtain(pen, v, o.get('smash', 0.0))
        # counters + upper cabinets along the back wall, the stove
        _counters(pen, v, o)
        # the mudroom door (closed) on the right wall
        md = Door((1.3 + 0.03, 9.25), 0.8, 2.03, (0.0, -1.0), 1, 0.0, art_a=door_art('four', 'right', bolt=False), art_b=door_art('four', 'left', bolt=False))
        md.draw(pen, v, 0.0)

    def wall_art(self, a, b, o):
        if a == (1.3, 5.8):                                       # front wall: the clock (11:07), the calendar, the phone
            def art(p_, W, H):
                hh, mm = o.get('clock', (11, 7))
                _wall_clock(p_, (1.3 - KCLOCK[0]) * 100, H - KCLOCK[1] * 100, 15, hh, mm)
                _calendar(p_, (1.3 - (-2.12)) * 100 - 14, H - 175, 28, 38)
                _wall_phone(p_, (1.3 - 0.35) * 100, H - 150)
            return art
        if a == (-5.0, 10.0):                                     # back wall: the porch light switch by the back door
            def art(p_, W, H):
                _light_switch(p_, (KSWITCH[0] + 5.0) * 100, H - KSWITCH[1] * 100, o.get('porch_switch', 0.0) > 0.5, 'PORCH')
            return art
        if a == (-5.0, 5.8):                                      # left wall: a bunny cookie-jar shelf + a framed recipe
            def art(p_, W, H):
                _hframe(p_, W, H, 290, H - 205, 30, 40, 'poster', frame='#8a5a30', fn=lambda q, w, h: (q.fill(rect(0, 0, w, h), '#f2ead6'),
                        [q.seg((3, 6 + k * 4), (w - 3, 6 + k * 4), 0.6, '#6a5a8a', 160) for k in range(7)]))
            return art
        return None

    def pieces(self, o):
        bd = back_door(latch_turn=o.get('locked', 1.0))
        ang = o.get('back_door', 0.0)
        ang = ang if not callable(ang) else 0.0
        P = [Piece('fridge', (FRIDGE.cx, 0.9, FRIDGE.cy), lambda pen, v: fridge(pen, v, o), block=FRIDGE.footprint()),
             Piece('table', (KTABLE.cx, 0.4, KTABLE.cy), lambda pen, v: draw_parts(pen, v, table_parts(KTABLE, '#d9c49a', cloth=('#e8dcc8', _check_cloth))),
                   block=KTABLE.footprint())]
        for i, (u, n, fa) in enumerate(((-0.32, 0.62, 180), (0.32, 0.62, 180), (-0.32, -0.62, 0), (0.32, -0.62, 0))):
            c = KTABLE.at(u, n, 0)
            P.append(Piece('kchair%d' % i, (c[0], 0.45, c[2]), (lambda c_, fa_: lambda pen, v: _kchair(pen, v, c_[0], c_[2], fa_))(c, fa),
                           block=_circ(c[0], c[2], 0.24)))
        if not callable(o.get('back_door', 0.0)) and o.get('back_door_live') is not True:
            P.append(Piece('back_door', (-3.3, 1.0, 9.95 - 0.45 * math.sin(math.radians(ang))),
                           lambda pen, v: (bd.draw(pen, v, ang), _bdoor_glass(pen, v, bd, ang))))
        return P

    def spots(self, v, o):
        S = {}
        S['fridge'] = _mk_spot(v, 'fridge', FRIDGE.cx + 0.75, FRIDGE.cy, 0.0, 'stand', 'facing the fridge (the rules at eye level)', face=(-1, 0))
        S['fridge_rules'] = _mk_spot(v, 'fridge_rules', FRIDGE.cx + FRIDGE.d / 2 + 0.01, FRIDGE.cy + 0.05, 1.42, 'point', 'the laminated rules under the bunny magnet')
        S['back_door'] = _mk_spot(v, 'back_door', -3.3, 9.45, 0.0, 'stand', 'at the back door (inside)', face=(0, 1))
        S['back_door_knob'] = _mk_spot(v, 'back_door_knob', BDOOR[1] - 0.075, KNOB_Y, 9.99, 'point', 'the back door knob (inside)')
        S['back_door_bolt'] = _mk_spot(v, 'back_door_bolt', BDOOR[1] - 0.075, KNOB_Y + 0.17, 9.99, 'point', 'the back door deadbolt (locked from the inside)')
        S['back_door_out'] = _mk_spot(v, 'back_door_out', -3.3, 10.6, 0.45, 'stand', 'on the back porch, outside the door')
        S['sink'] = _mk_spot(v, 'sink', -1.35, 9.0, 0.0, 'stand', 'at the sink under the window', face=(0, 1))
        S['counter'] = _mk_spot(v, 'counter', -0.45, 9.69, COUNTER_Y, 'surface', 'the counter top right of the sink')
        S['table_top'] = _mk_spot(v, 'table_top', KTABLE.cx, KTABLE.cy, KTABLE.Y1, 'surface', 'the kitchen table top')
        for i, (u, n, f) in enumerate(((-0.32, 0.62, (0, -1)), (0.32, 0.62, (0, -1)), (-0.32, -0.62, (0, 1)), (0.32, -0.62, (0, 1)))):
            c = KTABLE.at(u, n * 1.0, 0)
            S['kchair%d' % i] = _mk_spot(v, 'kchair%d' % i, c[0], c[2], 0.0, 'seat', 'kitchen chair %d at the table' % i, face=f, seat_Y=0.46)
        S['switch'] = _mk_spot(v, 'switch', KSWITCH[0], KSWITCH[1], 9.99, 'point', 'the back porch light switch')
        S['kitchen_mid'] = _mk_spot(v, 'kitchen_mid', -2.6, 7.8, 0.0, 'stand', 'the middle of the kitchen')
        S['window'] = _mk_spot(v, 'window', -1.35, 9.98, 1.5, 'point', 'the window over the sink (centre of the glass)')
        return S


def _check_cloth(p_, W, H):
    pat(p_, W, H, 'gingham', '#c84a4a', 170, scale=2.0)
    p_.texture(rect(0, 0, W, H), 'fabric', 0.4, 'overlay', 0.5)


def _mud_trail(p_, W, H, k):
    """Wet, dark drag marks across the kitchen floor from the back door (floor-art coordinates of the kitchen)."""
    if k <= 0: return
    x0, y1 = KIT[0], KIT[3]
    pts = [floor_uv(x0, y1, -3.3, 9.95), floor_uv(x0, y1, -3.1, 8.6), floor_uv(x0, y1, -2.2, 7.0), floor_uv(x0, y1, -1.0, 6.0)]
    n = int(len(pts) * 0 + 4 * k) + 1
    p_.line(smooth(pts, False, 0.9), 26.0, '#2a1a14', 150 * k)
    p_.line(smooth(pts, False, 0.9), 12.0, '#4a2018', 120 * k)
    rng = np.random.default_rng(8)
    for i in range(int(18 * k)):
        u = rng.uniform(0, 1)
        q = pts[min(3, int(u * 3))]
        p_.fill(_blob(q[0] + rng.uniform(-40, 40), q[1] + rng.uniform(-30, 30), rng.uniform(4, 12), rng.uniform(3, 8), 8, i, 0.4), '#2a1a14', 130 * k)


def _calendar(p_, x, y, w, h, month='APRIL', circle=None):
    p_.fill(rect(x + 1, y + 1.5, w, h), '#000000', 70)
    p_.fill(rect(x, y, w, h), '#f4efe2'); p_.fill(rect(x, y, w, h * 0.45), '#9fc8a8')
    p_.fill(oval(x + w * 0.5, y + h * 0.22, w * 0.18, h * 0.13), '#f2f2ee')                           # a bunny picture
    p_.fill(oval(x + w * 0.45, y + h * 0.1, w * 0.04, h * 0.08), '#f2f2ee'); p_.fill(oval(x + w * 0.55, y + h * 0.1, w * 0.04, h * 0.08), '#f2f2ee')
    btext(p_, month, x + w / 2, y + h * 0.53, 'sans_b', h * 0.07, '#3a3a3a', 230, 'center')
    for r in range(5):
        for c in range(7):
            p_.fill(rect(x + 2 + c * (w - 4) / 7, y + h * 0.58 + r * h * 0.08, (w - 4) / 7 - 0.6, h * 0.07), '#e8e2d2')
    if circle:
        r_, c_ = circle
        p_.line(oval(x + 2 + (c_ + 0.5) * (w - 4) / 7, y + h * 0.615 + r_ * h * 0.08, w * 0.08, h * 0.05), 0.8, '#c82a2a')


def _wall_phone(p_, x, y):
    p_.fill(rrect(x - 5, y, 10, 20, 1.5), '#e8dcc0'); p_.line(rrect(x - 5, y, 10, 20, 1.5), 0.6, '#000000', 140)
    p_.fill(rrect(x - 3.6, y - 2, 7.2, 22, 2.4), '#efe6cc'); p_.line(rrect(x - 3.6, y - 2, 7.2, 22, 2.4), 0.6, '#000000', 140)
    p_.line(smooth([(x, y + 20), (x - 2, y + 30), (x + 2, y + 38), (x - 1, y + 46)], False, 0.8), 0.8, '#d8ccb0', 220)


def _cafe_curtain(pen, v, smash=0.0):
    """Gingham cafe curtains on a tension rod across the lower half of the sink window (torn and hanging when smashed)."""
    a, b = (-5.0, 10.0), (1.3, 10.0)
    u0, u1 = KWIN[0] + 5.0, KWIN[1] + 5.0
    rodY = (KWIN[2] + KWIN[3]) / 2 + 0.02
    O = (KWIN[0] - 0.02, rodY, 10.0 - 0.07)
    F = Face(O, (1, 0, 0), (0, -1, 0), (KWIN[1] - KWIN[0] + 0.04) * 100, (rodY - KWIN[2] + 0.02) * 100, (0, 0, -1), 'front')
    W, H = F.W, F.H
    if smash > 0.3:
        shape = poly([(0, 0), (W * 0.4, 0), (W * 0.32, H * 0.6), (W * 0.1, H), (0, H)])
    else:
        shape = poly([(0, 0), (W, 0)] + [(x, H - 1.2 * abs(math.sin(x * 0.25))) for x in np.linspace(W, 0, 24)])

    def art(p_, W, H):
        p_.fill(rect(0, 0, W, H), '#efe6d6')
        pat(p_, W, H, 'gingham', '#c84a4a', 200, scale=1.0)
        for k in range(int(W / 6)):
            p_.linear(rect(k * 6, 0, 6, H), k * 6, 0, k * 6 + 6, 0, [(0, '#000000', 40), (0.5, '#ffffff', 20), (1, '#000000', 40)])
        p_.fill(rect(0, 0, W, 1.4), '#b8a070')
    draw_face(pen, v, F, art, '#efe6d6', shape=shape, ao=False, lw=0.9)


def _counters(pen, v, o):
    x0, x1, y0, y1 = KCOUNTER
    smash = o.get('smash', 0.0)
    pine = P_['pine']

    def door_row(n, inset=0.0):
        def art(p_, W, H):
            p_.texture(rect(0, 0, W, H), 'wood', 0.6, 'overlay', 0.9, 90)
            pat(p_, W, H, 'knotty', '#6a3a1a', 120, 4)
            dw = W / n
            for i in range(n):
                r = rect(i * dw + 2, 4 + inset, dw - 4, H - 8 - inset)
                p_.line(r, 1.0, '#3a200a', 170); p_.line(rect(i * dw + 5, 7 + inset, dw - 10, H - 14 - inset), 0.8, '#3a200a', 110)
                kx = i * dw + (dw - 8 if i % 2 == 0 else 8)
                p_.fill(oval(kx, 14 + inset, 1.6), '#c8b070'); p_.line(oval(kx, 14 + inset, 1.6), 0.5, '#3a2a10', 200)
        return art
    # base cabinets left of the sink, the sink cabinet, right of the stove
    segs = [(x0, -1.95), (-1.95, -0.75), (-0.75, -0.06), (0.7, x1)]
    for (a_, b_) in segs:
        B = Box((a_ + b_) / 2, (y0 + y1) / 2, b_ - a_, y1 - y0, 0.1, COUNTER_Y - 0.04, 0)
        draw_box(pen, v, B, {'front': dict(fill=pine, art=door_row(max(1, int(round((b_ - a_) / 0.45))))), 'all': _darken(pine, 0.2)})
        kick = Box((a_ + b_) / 2, (y0 + y1) / 2 + 0.04, b_ - a_, y1 - y0 - 0.08, 0.0, 0.1, 0)
        draw_box(pen, v, kick, {'all': '#2a1a10'})
        top = Box((a_ + b_) / 2, (y0 + y1) / 2 - 0.01, b_ - a_, y1 - y0 + 0.03, COUNTER_Y - 0.04, COUNTER_Y, 0)
        draw_box(pen, v, top, {'all': '#b8a888', 'top': dict(fill=P_['counter'], art=_boomerang)})
    # backsplash tiles (a face on the back wall between the counter and the upper cabinets)
    F = Face((x0, 1.5, 9.998), (1, 0, 0), (0, -1, 0), (x1 - x0) * 100, (1.5 - COUNTER_Y) * 100, (0, 0, -1), 'wall')
    holes = [rect((KWIN[0] - x0) * 100, 0, (KWIN[1] - KWIN[0]) * 100, (1.5 - KWIN[2]) * 100)]
    draw_face(pen, v, F, lambda p_, W, H: (pat(p_, W, H, 'tile', '#f6efd8', 255), p_.texture(rect(0, 0, W, H), 'grunge', 0.25, 'overlay', 0.5)),
              P_['tile'], holes=holes, ao={'bottom': 8}, line=False)
    # the sink bowl (a dark inset in the counter top) with the faucet
    q = [(KSINK[0], COUNTER_Y + 0.001, 9.48), (KSINK[1], COUNTER_Y + 0.001, 9.48), (KSINK[1], COUNTER_Y + 0.001, 9.88), (KSINK[0], COUNTER_Y + 0.001, 9.88)]
    if v.cam_h > COUNTER_Y:
        pen.fill(v.poly3(q), lit('#9aa0a8', (-1.35, COUNTER_Y, 9.7), (0, 1, 0)))
        q2 = [(KSINK[0] + 0.03, COUNTER_Y + 0.002, 9.51), (KSINK[1] - 0.03, COUNTER_Y + 0.002, 9.51), (KSINK[1] - 0.03, COUNTER_Y + 0.002, 9.85), (KSINK[0] + 0.03, COUNTER_Y + 0.002, 9.85)]
        pen.fill(v.poly3(q2), lit('#3a4048', (-1.35, COUNTER_Y, 9.7), (0, 1, 0))); pen.line(v.poly3(q), 1.0)
    fx_, fy_ = v.p(-1.35, COUNTER_Y, 9.92); s = v.s(-1.35, 9.92)
    tip = v.p(-1.35, COUNTER_Y + 0.3, 9.78)
    pen.line(smooth([(fx_, fy_), v.p(-1.35, COUNTER_Y + 0.33, 9.92), tip], False, 1.0), max(2.0, 0.025 * s) + 2, LINE)
    pen.line(smooth([(fx_, fy_), v.p(-1.35, COUNTER_Y + 0.33, 9.92), tip], False, 1.0), max(1.5, 0.025 * s), lit('#c8ccd4', (-1.35, 1.1, 9.9), None))
    # upper cabinets (left of the window, right of the window over the stove: a hood)
    for (a_, b_) in ((x0, -2.08), (-0.62, -0.1), (0.75, x1)):
        B = Box((a_ + b_) / 2, 9.82, b_ - a_, 0.34, 1.5, 2.25, 0)
        draw_box(pen, v, B, {'front': dict(fill=pine, art=door_row(max(1, int(round((b_ - a_) / 0.42))))), 'all': _darken(pine, 0.25),
                             'bottom': _darken(pine, 0.4)})
    hood = Box(0.32, 9.78, 0.8, 0.42, 1.62, 1.9, 0)
    draw_box(pen, v, hood, {'all': '#7a8a34', 'bottom': '#3a3a2a'})
    stove(pen, v)
    # things on the counter: a dish rack by the sink, a bunny cookie jar, a radio
    _ceramic_bunny(pen, v, -2.35, COUNTER_Y, 9.7, 0.26)
    if smash > 0: _glass_shards(pen, v, smash)


def _boomerang(p_, W, H):
    p_.texture(rect(0, 0, W, H), 'grunge', 0.2, 'overlay', 0.6)
    rng = np.random.default_rng(12)
    for i in range(int(W * H / 140)):
        x, y = rng.uniform(0, W), rng.uniform(0, H); a = rng.uniform(0, 6.28)
        p_.line(poly([(x - 3 * math.cos(a), y - 3 * math.sin(a)), (x, y), (x + 3 * math.cos(a + 0.8), y + 3 * math.sin(a + 0.8))], False), 0.7,
                ['#d8a04a', '#8ab0c8', '#c86a5a'][i % 3], 150)


def stove(pen, v):
    B = STOVE
    B2 = Box(B.cx, B.cy, B.w, B.d, B.Y0, B.Y1, 0)

    def front(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'grunge', 0.2, 'overlay', 0.5)
        p_.fill(rrect(8, 18, W - 16, H - 34, 2), _darken(P_['stove'], 0.08)); p_.line(rrect(8, 18, W - 16, H - 34, 2), 1.0, '#2a2a10', 180)
        p_.fill(rect(14, 24, W - 28, 20), '#1a1a14', 200)                                         # oven window
        p_.fill(rect(10, 10, W - 20, 4), '#e8e8e0')                                               # handle
        for k in range(4): p_.fill(oval(12 + k * (W - 24) / 3, 4.5, 2.6), '#efeee6')
        p_.fill(rect(0, H - 9, W, 9), '#2a2a1e')

    def top(p_, W, H):
        for (cx_, cy_) in ((W * 0.27, H * 0.3), (W * 0.73, H * 0.3), (W * 0.27, H * 0.72), (W * 0.73, H * 0.72)):
            p_.fill(oval(cx_, cy_, 9.5), '#1a1a18'); p_.line(oval(cx_, cy_, 6), 0.8, '#5a5a50'); p_.line(oval(cx_, cy_, 3), 0.8, '#5a5a50')
    draw_box(pen, v, B2, {'front': dict(fill=P_['stove'], art=front), 'top': dict(fill='#d8d8ce', art=top), 'all': _darken(P_['stove'], 0.2)})
    bs = Box(B.cx, B.cy + 0.3, B.w, 0.08, B.Y1, B.Y1 + 0.18, 0)
    draw_box(pen, v, bs, {'all': P_['stove']})


def fridge(pen, v, o):
    """Grandma's harvest-gold fridge on the kitchen's left wall: two doors, chrome handles, magnets, June's drawings, the
    laminated RULES sheet under a bunny magnet (rules=0..1: there from sundown)."""
    B = FRIDGE
    rules = o.get('rules', 1.0)

    def front(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'grunge', 0.22, 'overlay', 0.5)
        p_.linear(rect(0, 0, W, H), 0, 0, W, 0, [(0, '#ffffff', 30), (0.3, '#ffffff', 0), (1, '#000000', 40)])
        p_.fill(rect(0, H * 0.31, W, 1.4), '#5a4010')                                            # freezer split
        for (y0_, y1_) in ((H * 0.06, H * 0.26), (H * 0.36, H * 0.62)):
            p_.fill(rrect(W - 9, y0_, 3.4, y1_ - y0_, 1.6), '#d8dce0'); p_.line(rrect(W - 9, y0_, 3.4, y1_ - y0_, 1.6), 0.6, '#3a3a3a', 200)
        # June's crayon drawings and magnets
        for (x, y, w, h, kind) in ((6, H * 0.08, 20, 15, 'house'), (32, H * 0.11, 16, 20, 'bunny'), (8, H * 0.72, 22, 16, 'sun')):
            p_.fill(rect(x + 0.6, y + 0.8, w, h), '#000000', 50)
            p_.fill(rect(x, y, w, h), '#fbf7ee'); _tiny_drawing(p_, x, y, w, h, kind)
            p_.fill(oval(x + w / 2, y + 1.2, 1.4), ['#e84a5a', '#4aa8e8', '#f2c84a'][int(x) % 3])
        if rules > 0:
            rx, ry, rw, rh = W * 0.12, H * 0.36, W * 0.62, H * 0.3
            p_.fill(rect(rx + 1.0, ry + 1.4, rw, rh), '#000000', 80 * rules)
            p_.fill(rect(rx, ry, rw, rh), '#fbf8f0', 255 * rules)
            p_.linear(rect(rx, ry, rw, rh), rx, ry, rx + rw, ry + rh, [(0, '#ffffff', 90 * rules), (0.3, '#ffffff', 0), (0.65, '#ffffff', 40 * rules), (1, '#ffffff', 0)])
            btext(p_, 'RULES', rx + rw / 2, ry + 5.5, 'hand', 4.2, '#24306a', 240 * rules, 'center')
            for k in range(7):
                ly = ry + 9.0 + k * (rh - 11) / 7
                btext(p_, '%d.' % (k + 1), rx + 2.2, ly + 1.6, 'hand', 2.6, '#24306a', 230 * rules)
                p_.seg((rx + 5.5, ly + 0.8), (rx + rw - 2.5 - 4 * ((k * 37) % 5) / 5, ly + 0.8), 0.55, '#3a4a8a', 170 * rules)
            _bunny_magnet(p_, rx + rw / 2, ry + 0.5, 5.0)
        p_.fill(rect(0, H - 7, W, 7), '#2a2418')
    fs = B.faces()
    draw_face(pen, v, fs['front'], front, P_['fridge'], ao=False)
    for nm in ('left', 'right', 'top'):
        draw_face(pen, v, fs[nm], None, _darken(P_['fridge'], 0.12) if nm != 'top' else _lighten(P_['fridge'], 0.05), ao=False)


def _bunny_magnet(p_, x, y, s):
    """A white bunny-head fridge magnet with pink ears (holds the rules)."""
    head = union(oval(x, y, s * 0.55, s * 0.45), union(oval(x - s * 0.22, y - s * 0.6, s * 0.14, s * 0.42), oval(x + s * 0.22, y - s * 0.6, s * 0.14, s * 0.42)))
    p_.fill(moved(head, 0.3, 0.6), '#000000', 90)
    p_.fill(head, '#fbfaf6'); p_.line(head, 0.35, '#3a3a3a', 220)
    for sd in (-1, 1): p_.fill(oval(x + sd * s * 0.22, y - s * 0.6, s * 0.06, s * 0.28), '#f2a5b5')
    for sd in (-1, 1): p_.fill(oval(x + sd * s * 0.18, y - s * 0.05, s * 0.05), '#1a1a1a')
    p_.fill(oval(x, y + s * 0.08, s * 0.06, s * 0.045), '#e8889a')


def _tiny_drawing(p_, x, y, w, h, kind):
    if kind == 'house':
        p_.line(poly([(x + w * 0.25, y + h * 0.85), (x + w * 0.25, y + h * 0.45), (x + w * 0.5, y + h * 0.2), (x + w * 0.75, y + h * 0.45),
                      (x + w * 0.75, y + h * 0.85)], False), 0.7, '#d84a3a', 230)
        p_.fill(oval(x + w * 0.85, y + h * 0.2, w * 0.07), '#f2c84a')
        p_.line(poly([(x + w * 0.05, y + h * 0.86), (x + w * 0.95, y + h * 0.86)], False), 0.7, '#4aa84a', 230)
    elif kind == 'bunny':
        p_.line(oval(x + w * 0.5, y + h * 0.6, w * 0.22, h * 0.2), 0.7, '#8a8a9a', 230)
        p_.line(oval(x + w * 0.5, y + h * 0.35, w * 0.15, h * 0.12), 0.7, '#8a8a9a', 230)
        for sd in (-1, 1): p_.line(oval(x + w * (0.5 + sd * 0.07), y + h * 0.16, w * 0.04, h * 0.1), 0.6, '#8a8a9a', 230)
        btext(p_, 'MR BUNNY', x + w / 2, y + h * 0.95, 'kid', h * 0.12, '#3a3aa8', 220, 'center')
    else:
        p_.fill(oval(x + w * 0.5, y + h * 0.45, w * 0.16), '#f2c84a')
        for k in range(8):
            a = k * math.pi / 4
            p_.seg((x + w * 0.5 + math.cos(a) * w * 0.2, y + h * 0.45 + math.sin(a) * w * 0.2), (x + w * 0.5 + math.cos(a) * w * 0.3, y + h * 0.45 + math.sin(a) * w * 0.3), 0.6, '#f2a84a', 230)


def _kchair(pen, v, x, y, fa):
    """A kitchen chair: vinyl seat, chrome-ish legs, a ladder back."""
    B = Box(x, y, 0.42, 0.42, 0.0, 0.46, fa)
    parts = []
    w2 = 0.19
    for (u, n) in ((-w2, -w2), (w2, -w2), (-w2, w2), (w2, w2)):
        parts.append(Part(sub(B, u - 0.015, u + 0.015, n - 0.015, n + 0.015, 0.0, 0.43), {'all': '#a8a8a0'}))
    parts.append(Part(sub(B, -0.21, 0.21, -0.21, 0.21, 0.42, 0.47), {'all': '#a8382e', 'top': dict(fill='#c8463a', art=lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'fabric', 0.4, 'overlay', 0.5))}))
    for (u0, u1) in ((-0.21, -0.17), (0.17, 0.21)):
        parts.append(Part(sub(B, u0, u1, -0.21, -0.17, 0.47, 0.92), {'all': '#a8a8a0'}))
    parts.append(Part(sub(B, -0.21, 0.21, -0.215, -0.18, 0.74, 0.9), {'all': '#a8382e'}))
    draw_parts(pen, v, parts)


def _glass_shards(pen, v, k):
    """Broken glass on the counter and the floor under the smashed sink window."""
    rng = np.random.default_rng(31)
    for i in range(int(40 * k)):
        if i % 2: x, Y, y = rng.uniform(-2.0, -0.6), COUNTER_Y + 0.002, rng.uniform(9.45, 9.95)
        else: x, Y, y = rng.uniform(-2.4, 0.2), 0.002, rng.uniform(7.6, 9.3)
        if v.d(x, y) < 0.4: continue
        px, py = v.p(x, Y, y); s = v.s(x, y) * rng.uniform(0.02, 0.06)
        a = rng.uniform(0, 6.28)
        sh = poly([(px + math.cos(a) * s, py + math.sin(a) * s * 0.4), (px + math.cos(a + 2.1) * s * 0.7, py + math.sin(a + 2.1) * s * 0.3),
                   (px + math.cos(a + 4.0) * s, py + math.sin(a + 4.0) * s * 0.35)])
        pen.fill(sh, '#c8d8f0', 200); pen.line(sh, 0.6, '#ffffff', 160)


# ---------------------------------------------------------------------------------------------- the front hall + the stairs
ST_RAIL_END = ST_Y0 + (CEIL0 - (ST_RISE + 0.9)) / (ST_RISE / ST_RUN)     # where the handrail meets the hall ceiling (y ~2.97)
STAIRWELL = (STAIR_X[0], STAIR_X[1], 1.4, ST_TOP)                         # the opening in the upstairs floor over the flight


def nosing_Y(y):
    """Height of the tread nosing line at plan y along the flight."""
    return ST_RISE + (y - ST_Y0) * ST_RISE / ST_RUN


def front_door(ang=0.0, flap=0.0, bolt=1.0, chain=True, knob_turn=0.0):
    """The front door: white inside (six panels, brass peephole at 1.52 m, the brass mail slot at 0.95 m, deadbolt,
    chain), dark red outside with an Easter wreath and a brass knocker. Hinge at x -0.85 (opens into the hall)."""
    inside = door_art('six', 'left', peep=True, slot=True, flap=flap, bolt=True, chain=chain, chain_on=chain, turn=bolt, knob_turn=knob_turn)
    outside = door_art('six', 'right', peep=True, slot=True, bolt=False, col='#7a2a2c')
    return Door((FDOOR[0], -0.05), FDOOR[1] - FDOOR[0], FDOOR[2], (1.0, 0.0), 1, 0.0, art_a=_wreath_art(outside), art_b=inside, col='#f1ece0')


def _wreath_art(base):
    def art(p_, W, H):
        base(p_, W, H)
        cx, cy = W / 2, H * 0.32
        for k in range(26):
            a = 2 * math.pi * k / 26
            p_.fill(oval(cx + math.cos(a) * 17, cy + math.sin(a) * 17, 5, 4), '#5a7a3a')
        cols = ['#f2a5b5', '#f6d978', '#9fd3f0', '#b9e0a5', '#d9b3f0']
        for k in range(10):
            a = 2 * math.pi * k / 10 + 0.3
            p_.fill(oval(cx + math.cos(a) * 17, cy + math.sin(a) * 17, 2.8, 3.6), cols[k % 5]); p_.line(oval(cx + math.cos(a) * 17, cy + math.sin(a) * 17, 2.8, 3.6), 0.5)
        p_.fill(poly([(cx - 5, cy + 18), (cx + 5, cy + 18), (cx + 8, cy + 27), (cx, cy + 21), (cx - 8, cy + 27)]), '#f2d6e0')
    return art


def staircase(pen, v, part='flight', runner='#7a2a32', runner_b='#d8b860'):
    """The flight from the hall to the upstairs corridor along the right wall (x 0.35..1.3): 15 risers, a carpet runner
    with brass rods, the hall-side stringer and the closet under it ('flight'), or the balusters, handrail and newel post
    on the open side ('rail': draw it in front of anyone on the stairs when the camera sees that side)."""
    xa, xb = STAIR_X
    if part == 'flight':
        steps = []
        for k in range(ST_N):
            yk = ST_Y0 + k * ST_RUN
            steps.append((k, yk))
        steps.sort(key=lambda q: -v.d((xa + xb) / 2, q[1] + ST_RUN / 2))
        for (k, yk) in steps:
            Y0, Y1 = k * ST_RISE, (k + 1) * ST_RISE
            # riser (faces -y)
            Fr = Face((xa, Y1, yk), (1, 0, 0), (0, -1, 0), (xb - xa) * 100, ST_RISE * 100, (0, 0, -1), 'front')
            draw_face(pen, v, Fr, lambda p_, W, H: (p_.fill(rect(W * 0.16, 0, W * 0.68, H), runner), p_.fill(rect(W * 0.16, 0, 1.6, H), runner_b),
                                                    p_.fill(rect(W * 0.84 - 1.6, 0, 1.6, H), runner_b),
                                                    p_.texture(rect(W * 0.16, 0, W * 0.68, H), 'fabric', 0.5, 'overlay', 0.5)),
                      P_['trim'], ao={'bottom': 5}, lw=0.9)
            if k < ST_N - 1:
                Ft = Face((xa, Y1, yk + ST_RUN), (1, 0, 0), (0, 0, -1), (xb - xa) * 100, ST_RUN * 100, (0, 1, 0), 'top')

                def tread(p_, W, H):
                    p_.texture(rect(0, 0, W, H), 'wood', 0.5, 'overlay', 0.8, 90)
                    p_.fill(rect(W * 0.16, 0, W * 0.68, H), runner); p_.texture(rect(W * 0.16, 0, W * 0.68, H), 'fabric', 0.5, 'overlay', 0.5)
                    p_.fill(rect(W * 0.16, 0, 1.6, H), runner_b); p_.fill(rect(W * 0.84 - 1.6, 0, 1.6, H), runner_b)
                    p_.fill(rect(W * 0.16, H - 1.4, W * 0.68, 1.4), '#c8a24a')                      # brass stair rod
                    p_.fill(rect(0, H - 3, W, 3), '#000000', 40)
                draw_face(pen, v, Ft, tread, P_['floor0'], ao={'top': 6}, lw=0.8)
                # nosing lip
                nq = v.poly3([(xa, Y1, yk), (xb, Y1, yk), (xb, Y1 - 0.025, yk - 0.02), (xa, Y1 - 0.025, yk - 0.02)])
                pen.fill(nq, lit(P_['floor1'], (xa, Y1, yk), (0, 0, -1)))
        # the hall-side stringer + the closet wall under the flight (x = xa, facing -x)
        prof = [(ST_Y0, 0.0)]
        for k in range(ST_N - 1):
            yk = ST_Y0 + k * ST_RUN
            if (k + 1) * ST_RISE >= CEIL0: break
            prof += [(yk, (k + 1) * ST_RISE), (yk + ST_RUN, (k + 1) * ST_RISE)]
        prof += [(prof[-1][0], CEIL0), (ST_TOP, CEIL0), (ST_TOP, 0.0)]
        F = Face((xa, CEIL0, ST_TOP), (0, 0, -1), (0, -1, 0), (ST_TOP - ST_Y0) * 100, CEIL0 * 100, (-1, 0, 0), 'wall')
        shp = poly([((ST_TOP - y) * 100, (CEIL0 - Y) * 100) for (y, Y) in prof])

        def side(p_, W, H):
            pat(p_, W, H, 'roses', P_['hall_ink'], 120, 9, P_['hall_ink2']) if False else None
            p_.texture(rect(0, 0, W, H), 'plaster', 0.3, 'overlay', 0.5)
            pat(p_, W, H, 'ditsy', P_['hall_ink'], 150, 13, '#c8d0e0', 1.1)
            # white skirt board along the sawtooth
            sk = [((ST_TOP - y) * 100, (CEIL0 - Y) * 100) for (y, Y) in prof[1:-3]]
            if len(sk) > 1:
                p_.line(poly(sk, False), 16.0, P_['trim']); p_.line(poly([(x, y + 8) for (x, y) in sk], False), 0.8, '#000000', 90)
            # wainscot under the flight + the closet door
            p_.fill(rect(0, H - 92, W, 92), P_['wains']); p_.cv.save(); p_.cv.translate(0, H - 92); pat(p_, W, 92, 'beadboard', '#000000', 140); p_.cv.restore()
            dx0, dx1 = (ST_TOP - CLOSET[1]) * 100, (ST_TOP - CLOSET[0]) * 100
            dr = rect(dx0, H - CLOSET[2] * 100, dx1 - dx0, CLOSET[2] * 100)
            p_.fill(rect(dx0 - 6, H - CLOSET[2] * 100 - 6, dx1 - dx0 + 12, CLOSET[2] * 100 + 6), P_['trim'])
            door_art('four', 'right', bolt=False)(_Sub(p_, dx0, H - CLOSET[2] * 100), dx1 - dx0, CLOSET[2] * 100)
            p_.fill(rect(0, H - 13, W, 13), P_['trim'])
        draw_face(pen, v, F, side, P_['hall_paper'], shape=shp, ao={'bottom': 18})
        # the stairwell wall seen from the stairs (x = xa, facing +x): from the treads / the hall ceiling up to CEIL1
        prof2 = [(STAIRWELL[2], CEIL0), (ST_RAIL_END, CEIL0)]
        for k in range(ST_N - 1):
            yk = ST_Y0 + k * ST_RUN
            if yk + ST_RUN < ST_RAIL_END: continue
            prof2 += [(max(yk, ST_RAIL_END), (k + 1) * ST_RISE), (yk + ST_RUN, (k + 1) * ST_RISE)]
        prof2 += [(ST_TOP, UP_Y), (ST_TOP, CEIL1), (STAIRWELL[2], CEIL1)]
        F2 = Face((xa, CEIL1, STAIRWELL[2]), (0, 0, 1), (0, -1, 0), (ST_TOP - STAIRWELL[2]) * 100, (CEIL1 - 0.0) * 100, (1, 0, 0), 'wall')
        shp2 = poly([((y - STAIRWELL[2]) * 100, (CEIL1 - Y) * 100) for (y, Y) in prof2])
        draw_face(pen, v, F2, lambda p_, W, H: pat(p_, W, H, 'ditsy', P_['hall_ink'], 150, 14, '#c8d0e0', 1.1), P_['hall_paper'], shape=shp2,
                  ao={'left': 10, 'top': 12})
        # the bulkhead at the front of the stairwell (y 1.4, facing +y) and the stairwell ceiling
        Fb = Face((xa, CEIL1, STAIRWELL[2]), (1, 0, 0), (0, -1, 0), (xb - xa) * 100, (CEIL1 - CEIL0) * 100, (0, 0, 1), 'wall')
        draw_face(pen, v, Fb, lambda p_, W, H: pat(p_, W, H, 'ditsy', P_['hall_ink'], 150, 15, '#c8d0e0', 1.1), P_['hall_paper'], ao={'bottom': 10})
        ceil_rect(pen, v, xa, xb, STAIRWELL[2], ST_TOP, CEIL1)
    elif part == 'rail':
        xr = xa + 0.05
        def railY(y): return nosing_Y(y) + 0.9
        ys = []
        for k in range(ST_N - 1):
            yk = ST_Y0 + k * ST_RUN
            for f in (0.28, 0.72):
                y = yk + ST_RUN * f
                if y > ST_RAIL_END - 0.05: continue
                ys.append((y, (k + 1) * ST_RISE))
        ys.sort(key=lambda q: -v.d(xr, q[0]))
        for (y, Yt) in ys:
            if v.d(xr, y) < 0.15: continue
            a_, b_ = v.p(xr, Yt, y), v.p(xr, railY(y), y)
            w = max(1.6, 0.03 * v.s(xr, y))
            pen.seg(a_, b_, w + 2.2, LINE, 220); pen.seg(a_, b_, w, lit('#f2ede2', (xr, 1.5, y), (-1, 0, 0)))
            pen.seg((a_[0] + w * 0.25, a_[1]), (b_[0] + w * 0.25, b_[1]), w * 0.3, '#ffffff', 90)
        rl = [(xr, railY(y), y) for y in np.linspace(ST_Y0 - 0.12, ST_RAIL_END, 14) if v.d(xr, y) > 0.15]
        if len(rl) > 1:
            pts = [v.p(*q) for q in rl]
            w = max(3.0, 0.05 * v.s(xr, 1.8))
            pen.line(poly(pts, False), w + 3, LINE); pen.line(poly(pts, False), w, lit('#7a4a26', (xr, 1.8, 1.8), (0, 1, 0)))
            pen.line(poly([(x, y - w * 0.25) for (x, y) in pts], False), w * 0.25, '#c8946a', 150)
        if v.d(xr, ST_Y0 - 0.12) > 0.2:                                 # the newel post
            B = Box(xr, ST_Y0 - 0.12, 0.11, 0.11, 0.0, 1.12, 0)
            draw_box(pen, v, B, {'all': dict(fill='#f2ede2', art=lambda p_, W, H: (p_.fill(rect(0, H * 0.75, W, 3), '#000000', 50),
                                                                                    p_.fill(rect(0, H * 0.12, W, 2), '#000000', 50)))})
            cx_, cy_ = v.p(xr, 1.19, ST_Y0 - 0.12); s = v.s(xr, ST_Y0 - 0.12)
            cap = oval(cx_, cy_, 0.075 * s, 0.07 * s)
            pen.fill(cap, lit('#7a4a26', (xr, 1.2, 1.0), (0, 1, 0))); pen.line(cap, 1.2)


class _Sub:
    """A Pen proxy translated by (dx, dy) (to reuse an art fn inside a sub-rectangle of a face)."""

    def __init__(self, pen, dx, dy): self.pen, self.dx, self.dy = pen, dx, dy

    def __getattr__(self, k):
        pen, dx, dy = self.pen, self.dx, self.dy
        f = getattr(pen, k)
        if not callable(f): return f

        def g(*a, **kw):
            pen.cv.save(); pen.cv.translate(dx, dy)
            try: return f(*a, **kw)
            finally: pen.cv.restore()
        return g

    @property
    def cv(self): return self.pen.cv


class HallRoom(Room):
    name = 'hall'
    poly = [(HALL[0], HALL[2]), (HALL[1], HALL[2]), (HALL[1], HALL[3]), (HALL[0], HALL[3])]

    def lights(self, o):
        amb = o.get('amb_h', '#262c48')
        light = [Lamp(-0.5, CEIL0 - 0.12, 2.4, 3.8, LAMP_C, 1.15, (1.0, 1.0, 0.5))]
        console = [Lamp(-1.25, 1.12, 4.1, 2.2, LAMP_C, 0.8, (1.0, 0.6, 0.7))]
        porch = [Lamp(FD_CX, 1.0, 0.25, 1.6, '#ffcf8a', 0.18, only={'floor'})]
        up = [Lamp(0.8, UP_Y + 2.2, 5.2, 3.0, LAMP_C, 0.6)]
        var = [('hall', light, _kfn(o.get('hall', 1.0), 71)), ('console', console, _kfn(o.get('console', 0.0), 72)),
               ('porch', porch, _kfn(o.get('porch', 0.0), 73)), ('upstairs', up, _kfn(o.get('upstairs', 0.0), 74))]
        steady = [Lamp(kind='win', c=MOON_C, k=0.35, soft=10.0, panes=[[(FD_CX - 0.12, 1.62, -0.04), (FD_CX + 0.12, 1.62, -0.04), (FD_CX + 0.12, 1.42, -0.04), (FD_CX - 0.12, 1.42, -0.04)]],
                       d=_norm3((0.0, -0.4, 1.0)), only={'floor'})] if o.get('door', 0.0) else []
        if o.get('tod') == 'dawn':
            amb = '#56506a'
            steady = [Lamp(0.8, UP_Y + 1.6, 5.0, 4.5, DAWN_C, 0.9)]
        return amb, steady, var

    def shell(self, pen, v, o):
        x0, x1, y0, y1 = HALL
        floor_rect(pen, v, x0, x1, y0, y1, 0.0, P_['floor0'], 'boards', '#5a3a22', seed=21, art=lambda p_, W, H: _runner(p_, W, H, x0, y1, -1.0, 0.1, 0.25, 5.55))
        walls = [((1.3, 0.0), (-1.4, 0.0), [(1.3 - FDOOR[1], 0.0, 1.3 - FDOOR[0], FDOOR[2])]),
                 ((-1.4, 0.0), (-1.4, 5.8), [(LH_OPEN[0], 0.0, LH_OPEN[1], LH_OPEN[2])]),
                 ((-1.4, 5.8), (1.3, 5.8), [(HK_DOOR[0] + 1.4, 0.0, HK_DOOR[1] + 1.4, HK_DOOR[2])])]
        for (a, b, holes) in walls:
            wall(pen, v, a, b, 0.0, CEIL0, P_['hall_paper'], P_['hall_ink'], 'ditsy', holes, wains=0.92, seed=20 + len(holes), ink2='#c8d0e0', scale=1.1,
                 art=self.wall_art(a, b, o))
        # right wall: low under the corridor, tall in the stairwell, low at the front
        for (ya, yb, top) in ((5.8, ST_TOP, CEIL0), (ST_TOP, STAIRWELL[2], CEIL1), (STAIRWELL[2], 0.0, CEIL0)):
            wall(pen, v, (1.3, ya), (1.3, yb), 0.0, top, P_['hall_paper'], P_['hall_ink'], 'ditsy', [], wains=0.0, seed=27, ink2='#c8d0e0', scale=1.1,
                 art=self.photos_art(ya, yb, top) if top == CEIL1 else None, base_h=0.0, crown=0.0 if top == CEIL1 else 0.06)
        ceil_rect(pen, v, x0, STAIR_X[0], y0, y1, CEIL0)
        ceil_rect(pen, v, STAIR_X[0], x1, y0, STAIRWELL[2], CEIL0)
        ceil_rect(pen, v, STAIR_X[0], x1, ST_TOP, y1, CEIL0)
        staircase(pen, v, 'flight')
        # the ceiling fixture
        fx, fy = v.p(-0.5, CEIL0, 2.4)
        if v.d(-0.5, 2.4) > 0.3:
            s = v.s(-0.5, 2.4)
            bowl = ellipse3(v, -0.5, 2.4, 0.18, 0.18, CEIL0 - 0.08)
            pen.fill(bowl, lit('#e8e0d0', (-0.5, CEIL0 - 0.1, 2.4), (0, -1, 0))); pen.line(bowl, 1.0)
        # the front door (closed / ajar) drawn with the shell when it does not move
        ang = o.get('door', 0.0)
        if not callable(ang):
            fd = front_door(ang, o.get('flap', 0.0) if not callable(o.get('flap', 0.0)) else 0.0, o.get('bolt', 1.0), o.get('chain', True))
            fd.draw(pen, v, ang)

    def wall_art(self, a, b, o):
        if a == (-1.4, 0.0):                                  # left wall: coat hooks (Dad's jacket still hanging), the console mirror
            def art(p_, W, H):
                for k in range(4):
                    hx = 40 + k * 22
                    p_.fill(rrect(hx - 1.5, H - 172, 3, 9, 1.2), '#8a6a3a')
                _hframe(p_, W, H, 362, H - 205, 62, 74, 'mirror', frame='#8a6a3a')
                _frame_photo(p_, W, H, 470, H - 190, 34, 42, 'wedding')
                _frame_photo(p_, W, H, 512, H - 178, 26, 32, 'june')
            return art
        if a == (1.3, 0.0):                                   # front wall: the porch light switch by the door
            def art(p_, W, H):
                _light_switch(p_, (1.3 - 0.2) * 100, H - 120, o.get('porch_switch', 1.0) > 0.5, None)
                _frame_photo(p_, W, H, 255, H - 190, 30, 38, 'grandma')
            return art
        if a == (-1.4, 5.8):
            def art(p_, W, H):
                _frame_photo(p_, W, H, 160, H - 196, 44, 56, 'woods')
            return art
        return None

    def photos_art(self, ya, yb, top):
        def art(p_, W, H):
            for i in range(5):
                y = 1.6 + i * 0.6
                Yc = nosing_Y(y) + 1.55
                u = (ya - y) * 100
                _frame_photo(p_, W, H, u - 14, H - (Yc - 0.0) * 100, 26 + 6 * (i % 2), 32, ['laurie', 'wedding', 'june', 'grandma', 'woods'][i])
        return art

    def pieces(self, o):
        P = [Piece('console', (-1.25, 0.6, 4.1), lambda pen, v: _console(pen, v), block=[(-1.4, 3.65), (-1.05, 3.65), (-1.05, 4.55), (-1.4, 4.55)]),
             Piece('coats', (-1.33, 1.2, 0.95), lambda pen, v: _coats(pen, v)),
             Piece('stair_rail', (STAIR_X[0] + 0.05, 1.2, 1.8), lambda pen, v: staircase(pen, v, 'rail'))]
        if callable(o.get('door', 0.0)):
            pass
        return P

    def spots(self, v, o):
        S = {}
        S['door_inside'] = _mk_spot(v, 'door_inside', FD_CX, 0.42, 0.0, 'stand', 'at the front door, inside (hand on the knob)', face=(0, -1))
        S['peephole'] = _mk_spot(v, 'peephole', FD_CX, -0.025, PEEP_Y, 'point', 'the peephole (head_to target; stand at door_inside)')
        S['peephole_eye'] = _mk_spot(v, 'peephole_eye', FD_CX, 0.12, 0.0, 'stand', 'eye to the peephole: feet 0.12 m from the door', face=(0, -1))
        S['mail_slot'] = _mk_spot(v, 'mail_slot', FD_CX, -0.025, SLOT_Y, 'point', 'the brass mail slot (centre of the flap)')
        S['mail_slot_kneel'] = _mk_spot(v, 'mail_slot_kneel', FD_CX, 0.38, 0.0, 'kneel', 'kneeling at the mail slot (June): knees here, facing the door', face=(0, -1))
        S['knob'] = _mk_spot(v, 'knob', FDOOR[1] - 0.075, -0.0, KNOB_Y, 'point', 'the front door knob (inside)')
        S['deadbolt'] = _mk_spot(v, 'deadbolt', FDOOR[1] - 0.075, -0.0, KNOB_Y + 0.17, 'point', 'the deadbolt thumb-turn')
        S['chain'] = _mk_spot(v, 'chain', FDOOR[1] - 0.06, -0.0, 1.42, 'point', 'the door chain')
        S['porch_switch'] = _mk_spot(v, 'porch_switch', 0.2, 0.01, 1.2, 'point', 'the porch light switch by the front door')
        S['stairs_foot'] = _mk_spot(v, 'stairs_foot', 0.82, 0.55, 0.0, 'stand', 'at the foot of the stairs (facing up)', face=(0, 1))
        S['stairs_bottom_body'] = _mk_spot(v, 'stairs_bottom_body', 0.55, 0.45, 0.0, 'lie', 'the Bunnyman on his back at the foot of the stairs (head toward the door, body along x)')
        for k in (1, 2, 3, 5, 7, 9, 11, 13, 14):
            S['step%d' % k] = _mk_spot(v, 'step%d' % k, 0.82, ST_Y0 + (k - 1) * ST_RUN + 0.15, k * ST_RISE, 'stand',
                                       'standing on step %d (tread top Y %.2f); facing down the flight = face (0, -1)' % (k, k * ST_RISE))
        S['hall_mid'] = _mk_spot(v, 'hall_mid', -0.45, 2.3, 0.0, 'stand', 'the middle of the hall')
        S['hall_back'] = _mk_spot(v, 'hall_back', -0.45, 4.9, 0.0, 'stand', 'the back of the hall (by the kitchen door)')
        S['console_top'] = _mk_spot(v, 'console_top', -1.23, 4.1, 0.8, 'surface', 'the console table top (the bowl of plastic eggs)')
        S['living_open'] = _mk_spot(v, 'living_open', -1.3, 2.3, 0.0, 'stand', 'in the opening to the living room')
        return S


def _runner(p_, W, H, x0, y1, rx0, rx1, ry0, ry1, c='#7a2a32', b='#2a3a5a'):
    u0, v0 = floor_uv(x0, y1, rx0, ry1); u1, v1 = floor_uv(x0, y1, rx1, ry0)
    r = rect(u0, v0, u1 - u0, v1 - v0)
    p_.fill(r, c); p_.texture(r, 'fabric', 0.7, 'overlay', 0.8)
    p_.line(rect(u0 + 7, v0 + 7, u1 - u0 - 14, v1 - v0 - 14), 4.0, b); p_.line(rect(u0 + 13, v0 + 13, u1 - u0 - 26, v1 - v0 - 26), 1.2, '#d8b860')
    cx = (u0 + u1) / 2; y = v0 + 40
    while y < v1 - 30:
        dm = poly([(cx, y - 15), (cx + 17, y), (cx, y + 15), (cx - 17, y)])
        p_.fill(dm, b); p_.line(dm, 1.0, '#d8b860'); y += 62
    for xx in np.arange(u0 + 2, u1, 3.0):
        p_.seg((xx, v0), (xx, v0 - 4), 0.7, '#e8dcc0', 200); p_.seg((xx, v1), (xx, v1 + 4), 0.7, '#e8dcc0', 200)
    p_.line(r, 1.0, '#000000', 120)


def _console(pen, v):
    B = Box(-1.22, 4.1, 0.9, 0.34, 0.0, 0.8, 90)
    draw_parts(pen, v, table_parts(B, '#6a3e22', apron=0.1, inset=0.04))
    _egg_bowl(pen, v, -1.22, 0.8, 4.28)
    x, y = -1.27, 3.88; Y = 0.8
    lx, ly = v.p(x, Y, y); s = v.s(x, y)
    base = ellipse3(v, x, y, 0.07, 0.07, Y)
    pen.fill(base, lit('#c8b07a', (x, Y, y), None)); pen.line(base, 0.9)
    pen.seg((lx, ly), v.p(x, Y + 0.32, y), max(1.2, 0.014 * s), lit('#c8b07a', (x, Y + 0.2, y), None))
    _shade(pen, v, x, y, Y + 0.3, Y + 0.5, 0.14, 0.1, '#efe2c4', 0.0)


def _coats(pen, v):
    """Coats on the hooks by the front door: Dad's tan canvas work jacket (still there), Mom's rose cardigan, a scarf."""
    for (y, col_, kind, L) in ((0.4, '#b8945a', 'jacket', 0.8), (0.62, '#c98aa0', 'cardigan', 0.66), (0.84, '#3a5a7a', 'scarf', 0.85)):
        x = -1.37
        top = v.p(x, 1.72, y); s = v.s(x, y)
        if v.d(x, y) < 0.3: continue
        w = 0.24 if kind != 'scarf' else 0.08
        q = [(x, 1.72, y - w * 0.3), (x + 0.04, 1.6, y - w / 2), (x + 0.06, 1.72 - L, y - w / 2 - 0.04), (x + 0.06, 1.72 - L, y + w / 2 + 0.04),
             (x + 0.04, 1.6, y + w / 2), (x, 1.72, y + w * 0.3)]
        path = v.poly3(q)
        c = lit(col_, (x + 0.05, 1.3, y), (1, 0, 0))
        pen.fill(path, c); pen.line(path, 1.1)
        if kind == 'jacket':
            mid = v.poly3([(x + 0.06, 1.5, y), (x + 0.065, 1.72 - L, y)], closed=False)
            pen.line(mid, 0.8, '#3a2a14', 160)
            col2 = v.poly3([(x + 0.05, 1.68, y - 0.09), (x + 0.07, 1.55, y - 0.02), (x + 0.07, 1.55, y + 0.02), (x + 0.05, 1.68, y + 0.09)])
            pen.fill(col2, lit('#6a4a2a', (x, 1.6, y), (1, 0, 0)))


# ---------------------------------------------------------------------------------------------- the outside through the windows
def _outside_back(pen, v, tod='night'):
    """Behind the house: the yard to the treeline under the moon (what the kitchen window, the back door, June's window
    see)."""
    sky_dome(pen, v, 'dawn' if tod == 'dawn' else 'night')
    ground(pen, v, 10.0, 75.0, tod='dawn' if tod == 'dawn' else 'night', worn=[(-3.3, 12.1), (-5.5, 18.0), (-7.4, 25.6)])
    woods(pen, v, tod='dawn' if tod == 'dawn' else 'night', clearing=(-3.8, -1.4))
    yard_props(pen, v, tod)


def _outside_front(pen, v, tod='night'):
    """In front of the house: the porch roof edge and rail, the lawn, Orchard Road, a street lamp, the neighbours far off."""
    sky_dome(pen, v, 'dawn' if tod == 'dawn' else 'night', moon=False)
    ground(pen, v, -60.0, -0.1, tod='dawn' if tod == 'dawn' else 'night', c='#1e2e28')
    road_front(pen, v, tod)


# ---------------------------------------------------------------------------------------------- the yard and the road
def shed(pen, v, tod='night'):
    """The red barn-style shed at the back of the yard (peeling paint, a plank door, a small dusty window)."""
    B = SHED
    red = '#8a2e26' if tod != 'day87' else '#a83a2e'

    def plank(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'wood', 0.6, 'overlay', 1.0, 90)
        x = 0.0
        while x < W:
            p_.fill(rect(x, 0, 1.2, H), '#000000', 110); x += 18.0
        rng = np.random.default_rng(4)
        for i in range(int(W * H / 2500)):
            p_.fill(_blob(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(4, 14), rng.uniform(3, 9), 8, i, 0.5), '#c8b8a0', 90)
    def door_face(p_, W, H):
        plank(p_, W, H)
        dx0 = W * 0.36; dw = 92.0
        p_.fill(rect(dx0, H - 190, dw, 190), _darken(red, 0.15)); p_.line(rect(dx0, H - 190, dw, 190), 1.6, '#000000', 160)
        p_.line(poly([(dx0, H - 190), (dx0 + dw, H), (dx0, H), (dx0 + dw, H - 190)], False), 5.0, '#e8dcc8', 160)
        p_.fill(oval(dx0 + dw - 10, H - 95, 2.5), '#3a3a3a')
    def win_face(p_, W, H):
        plank(p_, W, H)
        p_.fill(rect(W * 0.35, H * 0.35, 52, 40), '#1a1e28'); p_.line(rect(W * 0.35, H * 0.35, 52, 40), 3.0, '#e8dcc8', 200)
        p_.seg((W * 0.35 + 26, H * 0.35), (W * 0.35 + 26, H * 0.35 + 40), 2.0, '#e8dcc8', 200)
    draw_box(pen, v, B, {'front': dict(fill=red, art=door_face), 'left': dict(fill=red, art=win_face), 'right': dict(fill=red, art=plank),
                         'back': dict(fill=red, art=plank), 'top': '#3a3a3e'})
    # gable roof (ridge along the shed's depth axis N)
    w2, d2 = B.w / 2 + 0.12, B.d / 2 + 0.15
    ridge = B.Y1 + 0.9
    roofc = '#3c3e44'
    for s_ in (-1, 1):
        q = [B.at(-w2 * s_, -d2, B.Y1 - 0.05), B.at(0, -d2, ridge), B.at(0, d2, ridge), B.at(-w2 * s_, d2, B.Y1 - 0.05)]
        nrm = _norm3((-s_ * B.U[0] * 0.9, 1.0, -s_ * B.U[1] * 0.9))
        if v.visible(q[0], nrm):
            path = v.poly3(q)
            pen.fill(path, lit(roofc, q[1], nrm)); pen.texture(path, 'grunge', 0.4, 'overlay', 0.8); pen.line(path, 1.2)
    for n_ in (-d2 + 0.15, d2 - 0.15):                                   # the gable triangles
        tri = [B.at(-B.w / 2, n_, B.Y1), B.at(0, n_, ridge - 0.05), B.at(B.w / 2, n_, B.Y1)]
        nn = (B.N[0] * (1 if n_ > 0 else -1), 0, B.N[1] * (1 if n_ > 0 else -1))
        if v.visible(tri[0], nn):
            path = v.poly3(tri)
            pen.fill(path, lit(red, tri[1], nn)); pen.line(path, 1.0)


def burn_barrel(pen, v, x=None, y=None, fire=0.0, t=0.0, egg=None, tod='night'):
    """The rusty 55-gallon burn barrel on two cinder blocks (holes punched round its base). fire 0..1 draws the flames
    (animated with t); egg = 0..1 melt progress of the plastic egg sitting in the fire (None: no egg)."""
    x = BARREL[0] if x is None else x; y = BARREL[1] if y is None else y
    D = v.d(x, y)
    if D < 0.3: return
    s = v.s(x, y)
    r = 0.29; H = 0.88; Yb = 0.18
    for dx in (-0.12, 0.12):                                            # cinder blocks
        B = Box(x + dx, y, 0.2, 0.4, 0.0, Yb, 0)
        draw_box(pen, v, B, {'all': '#7a7874', 'top': '#8a8884'})
    L_ = v.p(x - r, Yb, y); R_ = v.p(x + r, Yb, y)
    top = ellipse3(v, x, y, r, r, Yb + H)
    bot = ellipse3(v, x, y, r, r, Yb)
    tb, bb = _rb(top), _rb(bot)
    body = union(poly([(tb[0], (tb[1] + tb[3]) / 2), (tb[2], (tb[1] + tb[3]) / 2), (bb[2], (bb[1] + bb[3]) / 2), (bb[0], (bb[1] + bb[3]) / 2)]), bot)
    rust = lit('#7a4a2e', (x, 0.6, y), None, 1.1)
    pen.fill(body, rust); pen.texture(body, 'grunge', 0.7, 'overlay', 1.0)
    pen.linear(body, bb[0], 0, bb[2], 0, [(0, '#000000', 120), (0.35, '#000000', 0), (0.7, '#000000', 30), (1, '#000000', 140)])
    for Yr in (Yb + 0.25, Yb + 0.6):                                    # rolling hoops
        e = ellipse3(v, x, y, r * 1.01, r * 1.01, Yr)
        eb = _rb(e)
        pen.line(poly([(eb[0], (eb[1] + eb[3]) / 2)] + [v.p(x + r * 1.01 * math.cos(a), Yr, y + r * 1.01 * math.sin(a)) for a in np.linspace(math.pi, 2 * math.pi, 14)], False),
                 max(1.0, 0.012 * s), '#3a2014', 200)
    for k in range(7):                                                  # punched holes glowing when it burns
        a = math.pi + (k + 0.5) * math.pi / 7
        hx, hy = v.p(x + r * math.cos(a), Yb + 0.08, y + r * math.sin(a))
        pen.fill(oval(hx, hy, 0.022 * s, 0.016 * s), mix('#120806', '#ffb04a', fire * (0.6 + 0.4 * noise1(t * 6 + k, 3))))
    pen.line(body, 1.4)
    pen.fill(top, '#120a08'); pen.line(top, max(1.2, 0.015 * s), lit('#8a5a3a', (x, Yb + H, y), (0, 1, 0)))
    if fire > 0.01:
        _flames(pen, v, x, y, Yb + H, r, fire, t, egg)


def _flames(pen, v, x, y, Ytop, r, k, t, egg=None):
    """Flames licking out of the barrel (layered teardrops flickering with noise), sparks, a warm glow."""
    s = v.s(x, y)
    cx, cy = v.p(x, Ytop, y)
    pen.radial(None, cx, cy - 0.3 * s, 1.6 * s, [(0, '#ff9a3a', 90 * k), (1, '#ff9a3a', 0)], clip=False)
    if egg is not None:
        _melting_egg(pen, cx, cy - 0.02 * s, 0.07 * s, egg, t)
    for layer_, (col_, wk, hk) in enumerate((('#c83a14', 1.0, 1.0), ('#ff8a24', 0.75, 0.82), ('#ffd36a', 0.45, 0.6))):
        for i in range(5):
            ph = t * (2.2 + 0.4 * i) + i * 1.7
            fx = cx + (i - 2) * r * 0.32 * s + 0.04 * s * noise1(ph, i + layer_ * 7)
            hh = (0.28 + 0.16 * (0.5 + 0.5 * noise1(ph * 1.3, i + 3))) * s * hk * k
            ww = r * 0.36 * s * wk
            lean = 0.06 * s * noise1(ph * 0.8, i + 11)
            fl = smooth([(fx - ww, cy), (fx - ww * 0.6, cy - hh * 0.45), (fx + lean, cy - hh), (fx + ww * 0.6, cy - hh * 0.45), (fx + ww, cy)], True, 0.8)
            pen.fill(fl, col_, 235)
    for i in range(10):                                                 # sparks
        ph = (t * 0.7 + i * 0.137) % 1.0
        sx_ = cx + (i - 5) * 0.03 * s + 0.1 * s * noise1(t + i, 9)
        sy_ = cy - (0.3 + ph * 1.2) * s
        pen.fill(oval(sx_, sy_, max(0.8, 0.006 * s)), '#ffcf7a', 255 * (1 - ph) * k)


def _melting_egg(pen, x, y, r, melt, t):
    """The pink plastic egg sitting in the fire, sagging and blackening as it melts (melt 0..1)."""
    sag = clamp(melt)
    h = r * 1.3 * (1 - 0.65 * sag); w = r * (1 + 0.5 * sag)
    pts = [(x - w, y), (x - w * 0.9, y - h * 0.6), (x - w * 0.4 * (1 - sag * 0.3), y - h), (x + w * 0.3, y - h * (1 - 0.2 * sag)), (x + w * 0.95, y - h * 0.5),
           (x + w * (1 + 0.3 * sag), y + r * 0.1 * sag)]
    e = smooth(pts, True, 0.8)
    pen.fill(e, mix('#e9a8b6', '#2a1416', sag * 0.85)); pen.line(e, 1.0)
    if sag > 0.2:
        for k in range(3):
            dx = (k - 1) * w * 0.5
            pen.fill(smooth([(x + dx - w * 0.12, y), (x + dx, y + r * 0.6 * sag), (x + dx + w * 0.12, y)], True, 0.9), mix('#c8788a', '#1a0a0c', sag), 220)
    pen.fill(rect(x - w * 0.4, y - h * 0.45, w * 0.8, h * 0.18), '#7a4a58', 160 * (1 - sag))


def chopping_block(pen, v, x=None, y=None, hatchet=True):
    """The chopping block by the woodpile with the old hatchet stuck in it (the hatchet from 'our woodpile')."""
    x = CHOP[0] if x is None else x; y = CHOP[1] if y is None else y
    if v.d(x, y) < 0.3: return
    s = v.s(x, y)
    r = 0.24; H = 0.48
    top = ellipse3(v, x, y, r, r, H); bot = ellipse3(v, x, y, r, r, 0.0)
    tb, bb = _rb(top), _rb(bot)
    body = union(poly([(tb[0], (tb[1] + tb[3]) / 2), (tb[2], (tb[1] + tb[3]) / 2), (bb[2], (bb[1] + bb[3]) / 2), (bb[0], (bb[1] + bb[3]) / 2)]), bot)
    pen.fill(body, lit('#5a4632', (x, 0.3, y), None)); pen.texture(body, 'wood', 0.6, 'overlay', 1.0); pen.line(body, 1.2)
    pen.fill(top, lit('#b89a6a', (x, H, y), (0, 1, 0))); pen.line(top, 1.0)
    cx, cy = v.p(x, H, y)
    for rr in (0.3, 0.55, 0.8): pen.line(ellipse3(v, x, y, r * rr, r * rr, H), 0.7, '#6a5032', 150)
    if hatchet:
        hx, hy = v.p(x + 0.04, H + 0.02, y)
        head = poly([(hx - 0.07 * s, hy), (hx + 0.07 * s, hy), (hx + 0.09 * s, hy - 0.1 * s), (hx - 0.03 * s, hy - 0.11 * s)])
        pen.fill(head, lit('#5f6268', (x, H + 0.05, y), None)); pen.line(head, 1.0)
        pen.fill(oval(hx + 0.02 * s, hy - 0.06 * s, 0.025 * s), '#7b3a20', 160)
        ex, ey = hx - 0.3 * s, hy - 0.32 * s
        pen.seg((hx, hy - 0.08 * s), (ex, ey), max(2.0, 0.03 * s) + 2, LINE); pen.seg((hx, hy - 0.08 * s), (ex, ey), max(1.6, 0.03 * s), lit('#8a6440', (x, 0.8, y), None))
    # split logs around it
    for k, (dx, dy) in enumerate(((0.45, 0.2), (0.35, -0.3), (-0.4, 0.25))):
        lx, ly = v.p(x + dx, 0.07, y + dy)
        lg = oval(lx, ly, 0.16 * v.s(x + dx, y + dy), 0.06 * v.s(x + dx, y + dy))
        pen.fill(lg, lit('#7a5a3a', (x + dx, 0.1, y + dy), None)); pen.line(lg, 0.9)


def woodpile(pen, v, x0=-9.55, x1=-9.1, y0=24.0, y1=27.0, h=1.15):
    """Firewood stacked against the shed's side: a box of log ends (round ends drawn on the faces you can see)."""
    B = Box((x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0, 0.0, h, 90)

    def ends(p_, W, H):
        rng = np.random.default_rng(5)
        p_.fill(rect(0, 0, W, H), '#2a1e14')
        y = H - 7.0
        while y > 4:
            x = 6.0 + (4.0 if int(y) % 2 else 0)
            while x < W - 4:
                r = rng.uniform(4.5, 7.0)
                p_.fill(oval(x, y, r), '#a8885a'); p_.line(oval(x, y, r), 0.8, '#3a2a1a'); p_.line(oval(x, y, r * 0.5), 0.5, '#6a4a2a', 160)
                x += r * 2 + 0.5
            y -= 11.0
    draw_box(pen, v, B, {'front': dict(fill='#2a1e14', art=ends), 'back': dict(fill='#2a1e14', art=ends), 'left': dict(fill='#3a2a1c', art=ends),
                         'right': dict(fill='#3a2a1c', art=ends), 'top': dict(fill='#5a4430', art=lambda p_, W, H: p_.texture(rect(0, 0, W, H), 'wood', 0.6, 'overlay', 1.0))})


def swing_set(pen, v, x=None, y=None, tod='night', t=0.0, rust=1.0):
    """The old A-frame swing set (rusted now; new in 1987): two swings on chains, one hanging crooked."""
    x = SWING[0] if x is None else x; y = SWING[1] if y is None else y
    if v.d(x, y) < 0.5: return
    s = v.s(x, y)
    W2, H, sp = 1.6, 2.1, 0.75
    col_ = lit(mix('#4a7aa8', '#6a4a3a', 0.75 * rust), (x, 1.5, y), None)
    lw = max(1.4, 0.045 * s)
    for sx_ in (-W2, W2):
        apex = v.p(x + sx_, H, y)
        for sy_ in (-sp, sp):
            foot = v.p(x + sx_, 0.0, y + sy_)
            pen.seg(apex, foot, lw + 2, LINE); pen.seg(apex, foot, lw, col_)
    a_, b_ = v.p(x - W2, H, y), v.p(x + W2, H, y)
    pen.seg(a_, b_, lw + 2.5, LINE); pen.seg(a_, b_, lw * 1.1, col_)
    for i, (sx_, crooked) in enumerate(((-0.6, 0.0), (0.6, 1.0))):
        sway = 0.08 * math.sin(t * 0.9 + i) if tod != 'day87' else 0.0
        top1, top2 = v.p(x + sx_ - 0.2, H, y), v.p(x + sx_ + 0.2, H, y)
        seat_y = 0.45 + 0.12 * crooked * rust
        b1, b2 = v.p(x + sx_ - 0.2 + sway, seat_y + (0.12 * crooked * rust), y + sway), v.p(x + sx_ + 0.2 + sway, seat_y, y + sway)
        pen.seg(top1, b1, max(0.8, 0.008 * s), '#5a5a5a'); pen.seg(top2, b2, max(0.8, 0.008 * s), '#5a5a5a')
        pen.seg(b1, b2, max(2.0, 0.05 * s), LINE); pen.seg(b1, b2, max(1.5, 0.035 * s), lit('#2a2a2a' if rust else '#e8c84a', (x, 0.5, y), None))


def yard_props(pen, v, tod='night', t=0.0, fire=0.0, egg=None, porch_light=0.0):
    """Everything standing in the back yard, far -> near: the old split-rail fence at the treeline, the swing set, the
    shed with the woodpile, the chopping block with the hatchet, the burn barrel, the clothesline."""
    items = [('fence', (0.0, 37.5)), ('swing', SWING), ('shed', (SHED.cx, SHED.cy)), ('wood', (-9.3, 25.5)), ('chop', CHOP), ('barrel', BARREL),
             ('line', (3.0, 18.0))]
    items.sort(key=lambda q: -v.d(q[1][0], q[1][1]))
    for nm, (x, y) in items:
        if v.d(x, y) < 0.6 and nm != 'fence': continue
        if nm == 'fence': _fence(pen, v, tod)
        elif nm == 'swing': swing_set(pen, v, tod=tod, t=t, rust=0.0 if tod in ('day87', 'sunrise87') else 1.0)
        elif nm == 'shed': shed(pen, v, tod)
        elif nm == 'wood': woodpile(pen, v)
        elif nm == 'chop': chopping_block(pen, v)
        elif nm == 'barrel': burn_barrel(pen, v, fire=fire, t=t, egg=egg, tod=tod)
        elif nm == 'line': _clothesline(pen, v)


def _fence(pen, v, tod):
    """An old split-rail fence along the treeline, rails fallen in places (a gap where the path goes into the woods)."""
    xs = np.arange(-24.0, 24.0, 2.4)
    for i, x in enumerate(xs):
        if -4.0 < x < -1.0: continue                                       # the gap
        y = 37.5 + 0.3 * math.sin(i * 1.3)
        if v.d(x, y) < 1.0: continue
        a_, b_ = v.p(x, 0.0, y), v.p(x, 1.1, y)
        s = v.s(x, y)
        pen.seg(a_, b_, max(1.5, 0.09 * s) + 2, LINE); pen.seg(a_, b_, max(1.2, 0.09 * s), lit('#4a4038', (x, 0.6, y), None))
        if i + 1 < len(xs) and not (-4.0 < xs[i + 1] < -1.0) and i % 5 != 3:
            for Yr in (0.45, 0.9):
                y2 = 37.5 + 0.3 * math.sin((i + 1) * 1.3)
                p0, p1 = v.p(x, Yr, y), v.p(xs[i + 1], Yr - (0.3 if i % 7 == 2 else 0.0), y2)
                pen.seg(p0, p1, max(1.2, 0.06 * s) + 2, LINE); pen.seg(p0, p1, max(1.0, 0.06 * s), lit('#5a5046', (x, Yr, y), None))


def _clothesline(pen, v):
    """A T-post clothesline running from the house corner out into the yard; a forgotten peg bag."""
    p0 = (4.6, 2.0, 10.3); p1 = (5.5, 1.95, 22.0)
    if v.d(p1[0], p1[2]) > 0.6:
        a_, b_ = v.p(5.5, 0.0, 22.0), v.p(5.5, 2.05, 22.0)
        s = v.s(5.5, 22.0)
        pen.seg(a_, b_, max(1.5, 0.06 * s) + 2, LINE); pen.seg(a_, b_, max(1.2, 0.06 * s), lit('#6a6a64', (5.5, 1.0, 22.0), None))
        pen.seg(v.p(5.0, 2.05, 22.0), v.p(6.0, 2.05, 22.0), max(1.2, 0.05 * s) + 2, LINE)
    if v.d(p0[0], p0[2]) > 0.3 and v.d(p1[0], p1[2]) > 0.3:
        pts = [v.p(lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u) - 0.25 * math.sin(math.pi * u), lerp(p0[2], p1[2], u)) for u in np.linspace(0, 1, 12)]
        pen.line(poly(pts, False), 1.0, '#c8c8c0', 180)


def road_front(pen, v, tod='night', police=None, t=0.0):
    """Orchard Road in front of the house: asphalt, the curb, a street lamp, the mailbox, the DEAD END sign where the road
    stops at the trees, the neighbours' houses far down the road to the west (-x) with a few lit windows."""
    lamp_on = tod in ('night',)
    F = floor_face(-90.0, 30.0, -21.5, -14.0, 0.0)

    def asphalt(p_, W, H):
        p_.texture(rect(0, 0, W, H), 'asphalt', 0.6, 'overlay', 3.0)
        p_.fill(rect(0, H - 14, W, 14), '#5a5a58')
    draw_face(pen, v, F, asphalt, '#24262c', ao=False, line=False)
    # the neighbours far down the road (a row of houses facing the road on the other side, lit windows)
    for i, hx in enumerate((-60.0, -44.0, -30.0)):
        hy = -32.0
        if v.d(hx, hy) < 2: continue
        B = Box(hx, hy, 9.0, 8.0, 0.0, 5.6, 0)
        draw_box(pen, v, B, {'all': '#2a2e3a', 'front': dict(fill='#3a3e4c', art=lambda p_, W, H, i=i: _house_windows(p_, W, H, i))})
        ridge = [B.at(-4.8, 0.0, 5.6), B.at(0, 0.0, 8.4), B.at(4.8, 0.0, 5.6)]
        pen.fill(v.poly3(ridge), '#1a1c24')
    # street lamp at the corner of the lot
    lx, ly = -7.5, -14.6
    if v.d(lx, ly) > 1.0:
        a_, b_ = v.p(lx, 0.0, ly), v.p(lx, 4.6, ly)
        s = v.s(lx, ly)
        pen.seg(a_, b_, max(2.0, 0.1 * s) + 2, LINE); pen.seg(a_, b_, max(1.5, 0.1 * s), '#3a3e46')
        hd = v.p(lx + 0.7, 4.55, ly)
        pen.seg(b_, hd, max(1.5, 0.06 * s) + 2, LINE); pen.seg(b_, hd, max(1.2, 0.06 * s), '#3a3e46')
        if lamp_on:
            pen.glow(hd[0], hd[1] + 0.08 * s, 1.6 * s, '#ffcf7a', 80); pen.fill(oval(hd[0], hd[1] + 0.05 * s, 0.12 * s, 0.05 * s), '#fff2c8')
            px_, py_ = v.p(lx + 0.7, 0.0, ly)
            pen.radial(None, px_, py_, 4.0 * s, [(0, '#ffcf7a', 70), (1, '#ffcf7a', 0)], sy=0.3, clip=False)
    # the mailbox and the DEAD END sign
    mx, my = 3.2, -13.7
    if v.d(mx, my) > 0.8:
        s = v.s(mx, my)
        a_, b_ = v.p(mx, 0.0, my), v.p(mx, 1.05, my)
        pen.seg(a_, b_, max(1.5, 0.06 * s) + 2, LINE); pen.seg(a_, b_, max(1.2, 0.06 * s), '#5a4a3a')
        bx = Box(mx, my, 0.22, 0.5, 1.05, 1.28, 0)
        draw_box(pen, v, bx, {'all': '#2a2e34', 'top': '#3a3e46'})
    sx_, sy_ = 9.5, -14.2
    if v.d(sx_, sy_) > 1.0:
        s = v.s(sx_, sy_)
        a_, b_ = v.p(sx_, 0.0, sy_), v.p(sx_, 2.3, sy_)
        pen.seg(a_, b_, max(1.2, 0.05 * s) + 2, LINE); pen.seg(a_, b_, max(1.0, 0.05 * s), '#8a8a8a')
        F2 = Face((sx_ - 0.38, 2.6, sy_ - 0.02), (1, 0, 0), (0, -1, 0), 76, 60, (0, 0, -1), 'front')
        draw_face(pen, v, F2, lambda p_, W, H: (p_.fill(rect(0, 0, W, H), '#e8c42a'), p_.line(rect(3, 3, W - 6, H - 6), 2.0, '#1a1a1a'),
                                                btext(p_, 'DEAD', W / 2, H * 0.45, 'sans_b', 17, '#1a1a1a', 255, 'center'),
                                                btext(p_, 'END', W / 2, H * 0.82, 'sans_b', 17, '#1a1a1a', 255, 'center')), '#e8c42a', ao=False, lw=1.0)
    woods(pen, v, y_edge=-22.0, xr=(12.0, 70.0), depth=30.0, seed=17, tod=tod, mist=False) if v.yaw > 90 or v.yaw < -90 else None


def _house_windows(p_, W, H, seed):
    rng = np.random.default_rng(seed)
    for (x, y) in ((W * 0.2, H * 0.3), (W * 0.65, H * 0.3), (W * 0.2, H * 0.7), (W * 0.7, H * 0.7)):
        lit_ = rng.uniform() < 0.45
        p_.fill(rect(x, y, 110, 100), '#ffcf7a' if lit_ else '#141820')
        if lit_: p_.fill(rect(x, y, 110, 100), '#ff9a4a', 40)


# ====================================================================================================== extrusions
def _cross3(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def extrude(pen, v, O, U, V, pts, E, cap='#808080', side=None, art=None, art_back=None, line=True, lw=None, smooth_k=0.0, cap_back=None):
    """A shaped solid: the profile pts (cm, in the frame O + a U + b V, U/V unit 3D vectors, b down) extruded by E
    (metres, 3D). Visible side strips are vertex-lit flat quads (soft shading by their normal), the visible cap is a lit
    face with optional art (art_back for the far cap). Use for rolled arms, cushions, the wingback, the tub, lids."""
    n_front = _norm3(_scale3(E, -1)); n_back = _norm3(E)
    side = side or _darken(cap, 0.15)
    P0 = [_add3(_add3(O, U, a / 100.0), V, b / 100.0) for (a, b) in pts]
    P1 = [_add3(p_, E) for p_ in P0]
    n = len(pts)
    # orientation of the profile (to point the side normals outward)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    sgn = 1.0 if area > 0 else -1.0
    quads = []
    for i in range(n):
        a0, a1, b1, b0 = P0[i], P0[(i + 1) % n], P1[(i + 1) % n], P1[i]
        ed = _sub3(a1, a0)
        nrm = _norm3(_cross3(ed, E))
        # flip toward outside: test against the profile centroid
        cx_ = sum(q[0] for q in P0) / n, sum(q[1] for q in P0) / n, sum(q[2] for q in P0) / n
        mid = ((a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2, (a0[2] + a1[2]) / 2)
        if _dot3(nrm, _sub3(mid, cx_)) < 0: nrm = _scale3(nrm, -1)
        if not v.visible(mid, nrm): continue
        d = v.d((a0[0] + b1[0]) / 2, (a0[2] + b1[2]) / 2)
        quads.append((d, (a0, a1, b1, b0), nrm))
    quads.sort(key=lambda q: -q[0])
    for (_, q, nrm) in quads:
        path = v.poly3(list(q))
        if path.isEmpty(): continue
        c = lit(side, ((q[0][0] + q[2][0]) / 2, (q[0][1] + q[2][1]) / 2, (q[0][2] + q[2][2]) / 2), nrm, 1.0 + 0.12 * nrm[1])
        pen.fill(path, c)
        pen.line(path, 0.8, c, 255)                      # seal the hairline seams between strips
    W = max(a for a, b in pts) + 1; H = max(b for a, b in pts) + 1
    shp = poly(pts)
    for (Oc, nn, art_, cc) in ((O, n_front, art, cap), (_add3(O, E), n_back, art_back or art, cap_back or cap)):
        if not v.visible(Oc, nn): continue
        F = Face(Oc, U, V, W, H, nn, 'front')
        draw_face(pen, v, F, art_, cc, shape=shp, ao=False, line=False)
    if line:
        # silhouette: outline of the projected caps + the extreme side edges
        for Oc in (O, _add3(O, E)):
            pp = [v.p(*_add3(_add3(Oc, U, a / 100.0), V, b / 100.0)) for (a, b) in pts]
        pa = poly([v.p(*q) for q in _clip_near3(v, P0)]) if len(_clip_near3(v, P0)) >= 3 else None
        pb = poly([v.p(*q) for q in _clip_near3(v, P1)]) if len(_clip_near3(v, P1)) >= 3 else None
        if pa is not None and pb is not None:
            sil = union(pa, pb)
            for (_, q, nrm) in quads:
                pq = v.poly3(list(q))
                if not pq.isEmpty(): sil = union(sil, pq)
            c = (P0[0][0], P0[0][1], P0[0][2])
            w = lw if lw is not None else clamp(0.011 * v.S / max(v.near, v.d(c[0], c[2])), 0.7, 3.0)
            pen.line(sil, w, LINE, 210)


def rounded_rect_pts(w, h, r_top, r_bot=None, n=6, bulge=0.0):
    """A rounded rectangle profile (cm): w x h, top corners radius r_top, bottom r_bot; bulge puffs the top edge."""
    r_bot = r_top if r_bot is None else r_bot
    pts = []
    for (cx, cy, r, a0) in ((w - r_bot, h - r_bot, r_bot, 0), (r_bot, h - r_bot, r_bot, 90), (r_top, r_top, r_top, 180), (w - r_top, r_top, r_top, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        if a0 == 180 and bulge:
            for k in range(1, 6):
                u = k / 6
                pts.append((r_top + (w - 2 * r_top) * u, -bulge * math.sin(math.pi * u)))
    return pts


def box_extrude(pen, v, B, u0, u1, n0, n1, Y0, Y1, prof, cap, side=None, art=None, line=True, axis='n'):
    """Extrude a profile across a piece of box B: axis 'n' = the profile is the FRONT view (u across, Y up) extruded from
    the front (n1) to the back (n0); axis 'u' = the profile is the SIDE view (n across, Y up) extruded from u0 to u1.
    prof(W, H) -> pts in cm (y down from the top)."""
    U3 = (B.U[0], 0.0, B.U[1]); N3 = (B.N[0], 0.0, B.N[1]); dn = (0.0, -1.0, 0.0)
    if axis == 'n':
        W, H = (u1 - u0) * 100, (Y1 - Y0) * 100
        O = B.at(u0, n1, Y1)
        extrude(pen, v, O, U3, dn, prof(W, H), _scale3(N3, -(n1 - n0)), cap, side, art, line=line)
    else:
        W, H = (n1 - n0) * 100, (Y1 - Y0) * 100
        O = B.at(u0, n0, Y1)
        extrude(pen, v, O, N3, dn, prof(W, H), _scale3(U3, (u1 - u0)), cap, side, art, line=line)
