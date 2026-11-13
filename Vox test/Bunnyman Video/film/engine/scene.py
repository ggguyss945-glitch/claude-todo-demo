"""engine.scene: layered 2.5D compositing with real parallax, depth of field, cached static layers and the frame pipeline.

Layer(depth, draw, name='', blur=None, alpha=1.0, cache=False, bounds=None, cache_res=1.0, dim=0.0, tint=None,
      ref_depth=None, screen=False, cache_t=0.0, blend=None)
  depth     float or f(t). 1.0 = the subject plane. Far backgrounds 3..50, door frames / foreground 0.4..0.8.
  draw      f(pen, t): draws in DESIGN coordinates exactly as the layer looks from the home camera (x=960, y=540, zoom=1)
            when it sits at ref_depth (default: its depth at t=0). Depth only changes how it reacts to the camera:
            a pan of dx moves it by dx/d, a dolly scales it like a real plane at distance d.
            Animate depth (e.g. 1.0 -> 0.35) to bring a subject toward the lens: it grows by ref_depth/depth about the
            optical axis, exactly like walking up to a doorbell camera (and the fisheye bulges it).
  blur      None = depth of field only; a number = extra blur sigma (design px) in quadrature; 0 = always sharp.
  alpha, dim (0..1 darken), tint ((hex, k): multiply toward a light colour): values or f(t).
  cache     True (or a string key shared by re-created layers): draw ONCE (at cache_t) into an image over `bounds`
            (design rect x0, y0, x1, y1; default the frame +-25%) and transform that image each frame. Static sets
            become cheap. Only non-empty tiles are drawn. cache_res > 1 keeps big push-ins crisp.
  screen    True: locked to the frame (ignores the camera) but still goes through the lens.
  .order    (attribute, optional) float or f(t): the depth used only to sort the draw order (a light on the floor drawn
            over the floor plate it sits on); projection and blur keep `depth`.
  blend     None (normal) | 'plus' | 'screen' | 'multiply': how the layer composites onto what is behind it. 'plus' is for
            light-contribution layers (sets: albedo x one lamp's light, alpha = the lamp's level): lights add up exactly.

render_frame(layers, cam_state, t, frame_i, focus=1.0, dof=0.0, lens=None, grade=None, post=None, hud=None, bg='#000000')
    -> uint8 RGB (CFG.rh, CFG.rw, 3)
  cam_state  camera.CamState (cam.at(t)), a Cam (evaluated at t) or None for home.
  focus      focus depth (number, or a layer name); dof = blur sigma (design px) for |1/d - 1/focus| = 1.
             Spec: background behind face close-ups sigma 4.5 design px (= 6 px at 2560): focus=1, bg at d=3, dof=6.75.
  lens       None | 'lens' | 'doorbell' | 'doorbell_ir' | 'peephole' | lens.Lens(...)
  grade      post.Grade or preset name (None: neutral; doorbell_night / ir_night for the doorbell);
  post       dict of per-frame effects (see engine.post)
  hud        f(cv, t): drawn last, crisp, in design coordinates (captions, header, rule cards, doorbell HUD ...)
Pipeline: layers -> source canvas (BGRA, skia) -> lens optics -> grade + bloom + police flash + vignette/lens mask
          -> doorbell sensor (noise, codec) -> post move (roll, post_push) and upscale -> blur/static/glitch/grain -> lens ring, HUD.

Scene(layers, cam, lens=None, grade=None, focus=1.0, dof=0.0, post=None, hud=None).frame(t, i): the same with cam a Cam and
    focus / dof / post / hud allowed to be functions of t.
project(x, y, depth, cs, lens, ref_depth) -> frame position (design px) of a layer point after camera + lens + post moves;
project_box((x, y, w, h), depth, cs, lens, ref_depth) -> its bounding box (pin doorbell motion boxes and tags to people).
STATS: accumulated seconds per pipeline stage (reset with STATS.clear()).
"""
import itertools, math, os, time
from collections import OrderedDict
import numpy as np
import cv2
import skia
from . import core
from .core import CFG, DW, DH, Pen, col, surface_for, image_from
from .camera import CamState, HOME
from .lens import get_lens
from . import post as P

STATS = {}
_LIN = skia.SamplingOptions(skia.FilterMode.kLinear)
C0X, C0Y = DW / 2, DH / 2
CELL = 96


def _tick(name, t0):
    t1 = time.perf_counter(); STATS[name] = STATS.get(name, 0.0) + (t1 - t0); return t1


_UID = itertools.count(1)


def _val(v, t):
    return v(t) if callable(v) else v


class Layer:
    def __init__(self, depth, draw, name='', blur=None, alpha=1.0, cache=False, bounds=None, cache_res=1.0, dim=0.0, tint=None,
                 ref_depth=None, screen=False, cache_t=0.0, blend=None):
        self.depth, self.draw, self.name, self.blur, self.alpha = depth, draw, name, blur, alpha
        self.blend = blend
        self.cache, self.cache_res, self.dim, self.tint, self.screen, self.cache_t = cache, cache_res, dim, tint, screen, cache_t
        self.bounds = bounds or (-DW * 0.25, -DH * 0.25, DW * 1.25, DH * 1.25)
        self.ref_depth = ref_depth if ref_depth is not None else float(_val(depth, 0.0))
        self._uid = next(_UID)

    def depth_at(self, t): return float(_val(self.depth, t))

    def __repr__(self): return 'Layer(%r, d=%s%s)' % (self.name, self.depth if not callable(self.depth) else 'f(t)', ', cached' if self.cache else '')


# ------------------------------------------------------------------ static layer cache (LRU by bytes)
class _Entry:
    __slots__ = ('arr', 'img', 'rects', 'density', 'bounds', 'nbytes')


_cache = OrderedDict()
_last_density = {}
_CACHE_LIMIT = int(os.environ.get('POV2_CACHE_MB', '700')) * 1024 * 1024
_cache_bytes = [0]


def clear_cache():
    _cache.clear(); _cache_bytes[0] = 0; _last_density.clear()


core.on_size_change(clear_cache)


def _occupied_rects(alpha, cell=CELL):
    """Merged rectangles (x0, y0, x1, y1) in pixels covering every cell with any non-zero alpha."""
    h, w = alpha.shape
    ny, nx = (h + cell - 1) // cell, (w + cell - 1) // cell
    pad = np.zeros((ny * cell, nx * cell), np.uint8); pad[:h, :w] = alpha
    occ = pad.reshape(ny, cell, nx, cell).max(axis=(1, 3)) > 0
    rects, prev = [], None
    for j in range(ny):
        runs, i = [], 0
        while i < nx:
            if occ[j, i]:
                k = i
                while k < nx and occ[j, k]: k += 1
                runs.append((i, k)); i = k
            else: i += 1
        if prev is not None and runs == prev[0]:
            for r in prev[1]: r[3] = min(h, (j + 1) * cell)
        else:
            cur = [[a * cell, j * cell, min(w, b * cell), min(h, (j + 1) * cell)] for a, b in runs]
            rects.extend(cur); prev = (runs, cur)
    return [tuple(r) for r in rects]


def _store(key, e):
    _cache[key] = e; _cache_bytes[0] += e.nbytes
    while _cache_bytes[0] > _CACHE_LIMIT and len(_cache) > 1:
        k, old = _cache.popitem(last=False); _cache_bytes[0] -= old.nbytes


def _density_bucket(d):
    """Round a density up to a 1.12^n grid so small camera changes reuse the cache."""
    n = math.ceil(math.log(max(1e-3, d)) / math.log(1.12) - 1e-6)
    return 1.12 ** n


def _base_key(layer):
    return layer.cache if isinstance(layer.cache, str) else ('uid', layer._uid)


def _gained(key, e, gains):
    """Variant of a cached entry with per-channel colour gains baked in (dim, tint, IR falloff): drawing with a skia
    colour filter would take the slow raster path, so gains are applied to the pixels once and cached."""
    if gains is None: return e
    gq = tuple(round(float(g) / 0.03) * 0.03 for g in gains)
    if all(abs(g - 1) < 1e-6 for g in gq): return e
    k2 = key + ('gain', gq)
    e2 = _cache.get(k2)
    if e2 is not None:
        _cache.move_to_end(k2); return e2
    arr = cv2.multiply(e.arr, (gq[2], gq[1], gq[0], 1.0))
    if max(gq) > 1.0:
        arr[..., :3] = np.minimum(arr[..., :3], arr[..., 3:4])
    e2 = _Entry(); e2.arr = np.ascontiguousarray(arr); e2.img = image_from(e2.arr); e2.rects = e.rects
    e2.density = e.density; e2.bounds = e.bounds; e2.nbytes = e2.arr.nbytes
    _store(k2, e2)
    return e2


def _pick_density(layer, need):
    """Reuse the layer's current cache while it is sharp enough (need <= d <= 1.6 need); else re-bake with headroom."""
    k = _base_key(layer)
    d = _last_density.get(k)
    if d is None or not (need <= d * 1.0001 and d <= need * 1.6):
        d = _density_bucket(need * 1.15)
        _last_density[k] = d
    return min(d, _density_cap(layer))


_MAX_SIDE, _MAX_PIXELS = 12000, 48e6


def _density_cap(layer):
    """Largest density whose cache fits skia and memory: extreme push-ins (a foreground at depth 0.6 under a big zoom
    once asked for a 49k x 16k surface) get an upscaled cache instead of a failed canvas."""
    x0, y0, x1, y1 = layer.bounds
    w, h = max(1.0, x1 - x0), max(1.0, y1 - y0)
    return min(_MAX_SIDE / w, _MAX_SIDE / h, math.sqrt(_MAX_PIXELS / (w * h)))


def _cached(layer, density, gains=None):
    key = (_base_key(layer), round(density, 4))
    e = _cache.get(key)
    if e is not None:
        _cache.move_to_end(key)
    else:
        x0, y0, x1, y1 = layer.bounds
        w, h = int(math.ceil((x1 - x0) * density)), int(math.ceil((y1 - y0) * density))
        arr = np.zeros((h, w, 4), np.uint8)
        s = surface_for(arr); cv = s.getCanvas()
        cv.scale(density, density); cv.translate(-x0, -y0)
        layer.draw(Pen(cv), layer.cache_t)
        del cv, s
        bounds = layer.bounds
        arr, crop = _crop_to_content(arr)                  # keep only the painted part: a piece of furniture caches as
        if crop is not None:                               # its own size, not a whole frame (no LRU thrash at 2560)
            cx0, cy0, cx1, cy1 = crop
            bounds = (x0 + cx0 / density, y0 + cy0 / density, x0 + cx1 / density, y0 + cy1 / density)
        e = _Entry(); e.arr = arr; e.img = image_from(arr); e.rects = _occupied_rects(arr[..., 3])
        e.density = density; e.bounds = bounds; e.nbytes = arr.nbytes
        _store(key, e)
    return _gained(key, e, gains)


def _crop_to_content(arr, pad=2):
    """(arr, (x0, y0, x1, y1) px) cropped to the non-transparent pixels (+pad) when that saves at least a fifth of the
    raster; (arr, None) otherwise. An empty raster becomes 1x1."""
    a = arr[..., 3]
    rows = np.flatnonzero(a.max(axis=1))
    if rows.size == 0:
        return np.zeros((1, 1, 4), np.uint8), (0, 0, 1, 1)
    cols = np.flatnonzero(a.max(axis=0))
    h, w = a.shape
    y0, y1 = max(0, rows[0] - pad), min(h, rows[-1] + 1 + pad)
    x0, x1 = max(0, cols[0] - pad), min(w, cols[-1] + 1 + pad)
    if (x1 - x0) * (y1 - y0) > 0.8 * w * h:
        return arr, None
    return np.ascontiguousarray(arr[y0:y1, x0:x1]), (x0, y0, x1, y1)


def _cached_blur(layer, density_full, sigma_design, gains=None):
    """Pre-blurred version of a cached layer: sigma in LAYER design px, stored at a low density."""
    sb = 1.1 ** round(math.log(max(0.3, sigma_design)) / math.log(1.1))
    db = min(density_full, _density_bucket(2.6 / sb))
    key = (_base_key(layer), 'blur', round(db, 4), round(sb, 3))
    e = _cache.get(key)
    if e is not None:
        _cache.move_to_end(key)
    else:
        src = _cached(layer, db)
        pad = int(math.ceil(sb * db * 3)) + 2
        arr = cv2.copyMakeBorder(src.arr, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(0, 0, 0, 0))
        arr = cv2.GaussianBlur(arr, (0, 0), sb * db)
        x0, y0, x1, y1 = src.bounds                        # (the source may be cropped to its content)
        e = _Entry(); e.arr = np.ascontiguousarray(arr); e.img = image_from(e.arr); e.rects = _occupied_rects(e.arr[..., 3])
        e.density = db; e.bounds = (x0 - pad / db, y0 - pad / db, x1 + pad / db, y1 + pad / db); e.nbytes = e.arr.nbytes
        _store(key, e)
    return _gained(key, e, gains)


def _blur_raster_too_big(layer, a, sig, sw, sh):
    """The pre-blurred cache holds the WHOLE layer at the needed density. Under a strong optical zoom (fz 2-3) that raster
    is many times the screen, and while the zoom moves its sigma/density bucket changes every few frames, so a huge
    Gaussian blur is rebuilt per frame (26 s/frame at 2560 on the dummy film's hall push). Past 2.5 screens, blur the
    layer in screen space instead (the dynamic path): the same sigma on screen, cost bounded by the screen size."""
    try:
        x0, y0, x1, y1 = layer.bounds
    except Exception:
        return False
    sb = 1.1 ** round(math.log(max(0.3, sig / max(1e-6, a))) / math.log(1.1))
    db = min(_density_bucket(a), _density_bucket(2.6 / sb))
    return (x1 - x0) * (y1 - y0) * db * db > 2.5 * sw * sh


SHARP_MAX_SCREENS = 12.0           # ~44 MP at 2560x1440 (a 170 MB RGBA raster, near _density_cap's 48 MP)
SHARP_REBAKE_S = 0.6               # a second big bake wanted this soon after the last one = the zoom is racing
_sharp_bake_t = {}


def _sharp_raster_too_big(layer, density, sw, sh):
    """The sharp cache, like the blurred one, holds the WHOLE layer (its bounds) at the needed density: under a strong
    optical zoom (fz 2-3) or for a near layer in a big close-up that is a raster of many screens."""
    try:
        x0, y0, x1, y1 = layer.bounds
    except Exception:
        return False
    return (x1 - x0) * (y1 - y0) * density * density > SHARP_MAX_SCREENS * sw * sh


def _sharp_dynamic(layer, density, sw, sh, t):
    """Guard for the sharp cached path (the `_blur_raster_too_big` idea, made for sharp layers): a raster past
    SHARP_MAX_SCREENS screens is still baked and reused while the camera is slow (one bake serves a whole slow push:
    re-drawing a forest of vector trees every frame is 10x slower than one big bake), but when the zoom races (a fresh
    big bake would be needed again within SHARP_REBAKE_S of film time) the layer is drawn straight into the frame instead
    of re-baking several screens of pixels per frame; it is baked again once the zoom settles.
    Measured at 2560 (Bunnyman film): a slow push on the woods (cold open, fz 2.45 + 3.5 %/s) stays on the cache, 0.16
    s/frame (drawing it on every frame was 1.79 s); a racing zoom (fz 1 -> 3 in 1.2 s on the same woods) costs about the
    same either way (one bake every ~1.4x of zoom thanks to _pick_density's headroom), so the threshold sits high, where
    the raster's memory and _density_cap's upscale (a soft cache) are the real cost."""
    key = (_base_key(layer), round(density, 4))
    if key in _cache or not _sharp_raster_too_big(layer, density, sw, sh):
        return False
    bk = _base_key(layer)
    if len(_sharp_bake_t) > 4096: _sharp_bake_t.clear()
    tb = _sharp_bake_t.get(bk)
    if tb is not None and abs(t - tb) < SHARP_REBAKE_S:
        return True
    _sharp_bake_t[bk] = t
    return False


def _draw_entry(cv, e, paint):
    """Draw a cached image (only its occupied tiles) in layer design coordinates."""
    x0, y0 = e.bounds[0], e.bounds[1]; d = e.density
    cv.save(); cv.translate(x0, y0); cv.scale(1.0 / d, 1.0 / d)
    for (a, b, c, dd) in e.rects:
        r = skia.Rect.MakeLTRB(a, b, c, dd)
        cv.drawImageRect(e.img, r, r, _LIN, paint, skia.Canvas.kFast_SrcRectConstraint)
    cv.restore()


# ------------------------------------------------------------------ surfaces
_surf = {}
core.on_size_change(_surf.clear)


def _surface(w, h, tag='main'):
    key = (tag, w, h)
    if key not in _surf:
        arr = np.zeros((h, w, 4), np.uint8); _surf[key] = (arr, surface_for(arr))
    return _surf[key]


def _color_filter(gr, gg, gb):
    return skia.ColorFilters.Matrix([gr, 0, 0, 0, 0, 0, gg, 0, 0, 0, 0, 0, gb, 0, 0, 0, 0, 0, 1, 0])


def _layer_paint(layer, t, ir_gain=None):
    """-> (alpha-only paint for images, colour-filter paint for dynamic saveLayer or None, gains (r, g, b) or None, alpha)."""
    a = float(_val(layer.alpha, t)); dim = float(_val(layer.dim, t) or 0.0); tint = _val(layer.tint, t)
    g = np.array([1.0, 1.0, 1.0]) * (1 - dim)
    if tint:
        c, k = tint; g = g * ((1 - k) + k * np.array(core.rgb(c)) / 255.0 * 1.6)
    if ir_gain is not None: g = g * ir_gain
    has_g = np.abs(g - 1).max() > 1e-3
    paint = skia.Paint(AntiAlias=False)
    if a < 0.999: paint.setAlphaf(max(0.0, a))
    layer_paint = None
    if has_g or a < 0.999:
        layer_paint = skia.Paint()
        if a < 0.999: layer_paint.setAlphaf(max(0.0, a))
        if has_g: layer_paint.setColorFilter(_color_filter(*g))
    return paint, layer_paint, (tuple(g) if has_g else None), a


# ------------------------------------------------------------------ compositing
_BLEND = {'plus': skia.BlendMode.kPlus, 'screen': skia.BlendMode.kScreen, 'multiply': skia.BlendMode.kModulate}


def composite(layers, cs, t, focus=1.0, dof=0.0, lens=None, bg='#000000'):
    """Render the layers into the lens' source canvas. Returns the BGRA array (owned by a cached surface)."""
    L = get_lens(lens)
    if L is not None:
        hx, hy, sd = L.geometry()
    else:
        hx, hy, sd = DW / 2, DH / 2, CFG.k
    sw, sh = int(round(2 * hx * sd)), int(round(2 * hy * sd))
    arr, surf = _surface(sw, sh)
    cv = surf.getCanvas()
    cv.clear(col(bg))
    cs = cs or HOME
    F = cs.fz
    delta = 1.0 - 1.0 / max(1e-3, cs.zoom)            # dolly distance in units of the depth-1 plane
    Cx, Cy = cs.x - C0X, cs.y - C0Y
    if isinstance(focus, str):
        fl = [l for l in layers if l.name == focus]; focus = fl[0].depth_at(t) if fl else 1.0
    fc = max(0.03, focus - delta)
    items = []
    for i, l in enumerate(layers):
        d = l.depth_at(t)
        o = getattr(l, 'order', None)                                   # optional draw-order depth (projection keeps d)
        items.append((-(float(_val(o, t)) if o is not None else d), i, l, d))
    items.sort(key=lambda x: (x[0], x[1]))
    pen = Pen(cv)
    for _, _, l, d in items:
        if l.screen:
            sL, ox, oy, dc = 1.0, 0.0, 0.0, max(0.03, d - delta)
            a = sd; tx = (hx - C0X) * sd; ty = (hy - C0Y) * sd
        else:
            dc = d - delta
            if dc <= 0.02 * l.ref_depth: continue                        # passed the camera
            sL = F * l.ref_depth / dc
            a = sL * sd
            tx = (hx - sL * C0X - F * Cx / dc) * sd
            ty = (hy - sL * C0Y - F * Cy / dc) * sd
        # blur in source px
        sig_d = dof * F * abs(1.0 / dc - 1.0 / fc) if dof else 0.0
        if l.blur == 0 or l.blur is False: sig_d = 0.0
        elif l.blur: sig_d = math.hypot(sig_d, float(_val(l.blur, t)))
        sig = sig_d * sd
        irg = L.ir_gain(d) if (L is not None and L.ir) else None
        paint, lpaint, gains, alpha = _layer_paint(l, t, irg)
        if alpha <= 0.001: continue
        bm = _BLEND.get(l.blend) if l.blend else None
        if bm is not None:
            paint.setBlendMode(bm)
            if lpaint is None and not l.cache: lpaint = skia.Paint()
            if lpaint is not None: lpaint.setBlendMode(bm)
        M = skia.Matrix(); M.setAll(a, 0, tx, 0, a, ty, 0, 0, 1)
        t0 = time.perf_counter()
        if sig < 0.6:
            cv.save(); cv.setMatrix(M)
            if l.cache:
                need = a * max(1.0, l.cache_res)                            # px per layer design px
                dens = _pick_density(l, need)
                if _sharp_dynamic(l, dens, sw, sh, t):                      # a huge raster under a racing zoom: draw it on the frame
                    cv.restore(); cv.save()
                    _draw_offscreen(cv, l, l.cache_t, M, sw, sh, gains, paint)
                    _tick('layers_sharp_dyn', t0)
                else:
                    e = _cached(l, dens, gains)
                    _draw_entry(cv, e, paint)
            elif lpaint is None:
                pen.lw = 4.0; l.draw(pen, t)
            else:
                cv.restore(); cv.save()
                _draw_offscreen(cv, l, t, M, sw, sh, gains, paint)
            cv.restore()
            _tick('layers_sharp', t0); _tick('L:' + (l.name or '?'), t0)
        elif l.cache and not _blur_raster_too_big(l, a, sig, sw, sh):
            e = _cached_blur(l, _density_bucket(a), sig / a, gains)
            cv.save(); cv.setMatrix(M); _draw_entry(cv, e, paint); cv.restore()
            _tick('layers_blur_cached', t0); _tick('L:' + (l.name or '?'), t0)
        else:
            ds = 2 if sig <= 8 else (4 if sig <= 16 else 8)
            bw, bh = (sw + ds - 1) // ds, (sh + ds - 1) // ds
            barr, bsurf = _surface(bw, bh, 'blur%d' % ds)
            bcv = bsurf.getCanvas(); bcv.clear(skia.ColorTRANSPARENT)
            Mb = skia.Matrix(); Mb.setAll(a / ds, 0, tx / ds, 0, a / ds, ty / ds, 0, 0, 1)
            bcv.save(); bcv.setMatrix(Mb); l.draw(Pen(bcv), t); bcv.restore()
            x, y, w, h = cv2.boundingRect(barr[..., 3])
            if w > 0 and h > 0:
                pad = int(math.ceil(sig / ds * 3)) + 1
                x0, y0 = max(0, x - pad), max(0, y - pad); x1, y1 = min(bw, x + w + pad), min(bh, y + h + pad)
                sub = cv2.GaussianBlur(barr[y0:y1, x0:x1], (0, 0), sig / ds)
                sub = np.ascontiguousarray(sub)
                if gains is not None:
                    sub = cv2.multiply(sub, (gains[2], gains[1], gains[0], 1.0))
                    if max(gains) > 1: sub[..., :3] = np.minimum(sub[..., :3], sub[..., 3:4])
                img = image_from(sub)
                cv.save(); cv.resetMatrix(); cv.translate(x0 * ds, y0 * ds); cv.scale(ds, ds)
                cv.drawImage(img, 0, 0, _LIN, paint)
                cv.restore()
                del img
            _tick('layers_blur_dyn', t0); _tick('L:' + (l.name or '?'), t0)
    return arr


def _draw_offscreen(cv, l, t, M, sw, sh, gains, paint):
    """Dynamic layer with alpha / dim / tint / IR gain: draw into a transparent full-size buffer, apply the gains to the
    occupied box only and blit it (a skia saveLayer with a colour filter takes the slow raster path)."""
    oarr, osurf = _surface(sw, sh, 'off')
    ocv = osurf.getCanvas(); ocv.clear(skia.ColorTRANSPARENT)
    ocv.save(); ocv.setMatrix(M); l.draw(Pen(ocv), t); ocv.restore()
    x, y, w, h = cv2.boundingRect(oarr[..., 3])
    if w <= 0 or h <= 0: return
    sub = oarr[y:y + h, x:x + w]
    if gains is not None:
        sub = cv2.multiply(sub, (gains[2], gains[1], gains[0], 1.0))
        if max(gains) > 1: sub[..., :3] = np.minimum(sub[..., :3], sub[..., 3:4])
    sub = np.ascontiguousarray(sub)
    img = image_from(sub)
    cv.save(); cv.resetMatrix()
    cv.drawImage(img, x, y, skia.SamplingOptions(), paint)
    cv.restore()


def _motion_blur(img, vx, vy, k_out):
    """Directional blur for whip pans. vx, vy design px/s of content; k_out = output px per design px of img."""
    fps = 60.0
    dx, dy = vx / fps * 0.5 * k_out, vy / fps * 0.5 * k_out             # 180 degree shutter
    L = math.hypot(dx, dy)
    if L < 6: return img
    h, w = img.shape[:2]; f = 4
    sm = cv2.resize(img, (w // f, h // f), interpolation=cv2.INTER_AREA)
    n = int(min(61, max(3, L / f))) | 1
    ker = np.zeros((n, n), np.float32); c = n // 2
    ux, uy = dx / L, dy / L
    cv2.line(ker, (int(round(c - ux * c)), int(round(c - uy * c))), (int(round(c + ux * c)), int(round(c + uy * c))), 1.0, 1)
    ker /= ker.sum()
    sm = cv2.filter2D(sm, -1, ker, borderType=cv2.BORDER_REFLECT)
    big = cv2.resize(sm, (w, h), interpolation=cv2.INTER_LINEAR)
    k = min(1.0, (L - 6) / 14.0)
    return cv2.addWeighted(img, 1 - k, big, k, 0)


def render_frame(layers, cam_state, t, frame_i, focus=1.0, dof=0.0, lens=None, grade=None, post=None, hud=None, bg='#000000'):
    t0 = time.perf_counter()
    L = get_lens(lens)
    if grade is None:
        grade = 'neutral' if L is None else ('ir_night' if L.ir else ('doorbell_night' if L.kind == 'doorbell' else 'neutral'))
    g = P.get_grade(grade)
    fx = post or {}
    cs = cam_state or HOME
    ts = t
    if L is not None and L.fps:                                          # doorbell stream frame rate
        ts = math.floor(t * L.fps + 1e-6) / L.fps
    if hasattr(cs, 'at'):                                                # a Cam was passed
        cs_pre, cs = cs.at(ts), cs.at(t)                                 # pre-lens moves step with the stream
    else:
        cs_pre = cs
    src = composite(layers, cs_pre, ts, focus, dof, L, bg)
    t0 = _tick('composite', t0)
    # ---- lens optics -> work image (BGR)
    if L is not None:
        work = L.optics(src)
    else:
        work = cv2.cvtColor(src, cv2.COLOR_BGRA2BGR)
    t0 = _tick('lens', t0)
    wh, ww = work.shape[:2]
    if abs(cs.vx) + abs(cs.vy) > 300:
        work = _motion_blur(work, cs.vx, cs.vy, ww / DW)
    if L is not None and L.ir:
        gch = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY); work = cv2.merge([gch, gch, gch])
    # ---- grade, bloom, flash, vignette (work res)
    bl = fx.get('bloom', g.p['bloom'])
    bright = P.bloom_src(work, g.p['bloom_thr']) if bl else None
    lm = L.mask() if L is not None else None
    work = P.apply_grade(work, g, fx, bright, lm, id(L) if L is not None else None, skip_vignette=(L is not None and L.own_vignette),
                         lens_add=L.ring_add() if L is not None else None)
    t0 = _tick('grade', t0)
    if L is not None:
        work = L.sensor(work, frame_i)
        t0 = _tick('sensor', t0)
    # ---- post move (roll, post push) + upscale to output
    RW, RH = CFG.rw, CFG.rh
    roll = cs.roll
    pz = cs.pz
    if roll:
        th = math.radians(abs(roll)); pz *= math.cos(th) + (RW / RH) * math.sin(th)
    post_mat = None
    if (ww, wh) != (RW, RH) or abs(pz - 1) > 1e-4 or roll or cs.px or cs.py:
        ko, kw = RW / DW, ww / DW
        th = math.radians(roll)
        c, s = math.cos(th), math.sin(th)
        # output px -> design: q = (u + .5)/ko; work design = c0 + P + R^-1 (q - c0)/pz; work px = wd*kw - .5
        A = np.array([[c, s], [-s, c]]) / pz / ko * kw
        off = np.array([C0X + cs.px, C0Y + cs.py]) * kw - 0.5 - A @ np.array([C0X * ko - 0.5, C0Y * ko - 0.5])
        Mi = np.hstack([A, off[:, None]]).astype(np.float32)
        if not roll and abs(pz - 1) < 1e-4 and not cs.px and not cs.py:
            out = cv2.resize(work, (RW, RH), interpolation=cv2.INTER_LINEAR)
        else:
            out = cv2.warpAffine(work, Mi, (RW, RH), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT101)
        post_mat = (pz, roll, cs.px, cs.py)
    else:
        out = work
    t0 = _tick('upscale', t0)
    out = P.finish(out, g, fx, frame_i)
    t0 = _tick('finish', t0)
    # ---- crisp overlays: lens ring + HUD
    need_overlay = hud is not None
    if need_overlay:
        o4 = cv2.cvtColor(out, cv2.COLOR_BGR2BGRA)
        s = surface_for(o4); cv = s.getCanvas()
        cv.scale(RW / DW, RW / DW)
        if hud is not None: hud(cv, t)
        del cv, s
        rgbimg = cv2.cvtColor(o4, cv2.COLOR_BGRA2RGB)
    else:
        rgbimg = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
    _tick('hud', t0)
    STATS['frames'] = STATS.get('frames', 0) + 1
    return rgbimg


def project(x, y, depth, cs=None, lens=None, ref_depth=None, screen=False):
    """Where design point (x, y) of a layer at `depth` (authored at ref_depth, default = depth) lands in the final frame,
    in design coordinates, after the camera, the lens distortion and post moves. Use it to pin HUD boxes / tags on
    subjects (e.g. doorbell motion box). x, y may be numpy arrays."""
    cs = cs or HOME
    L = get_lens(lens)
    x = np.asarray(x, np.float64); y = np.asarray(y, np.float64)
    d0 = depth if ref_depth is None else ref_depth
    delta = 1.0 - 1.0 / max(1e-3, cs.zoom); F = cs.fz
    if screen:
        qx, qy = x - C0X, y - C0Y
    else:
        dc = max(1e-3, depth - delta); sL = F * d0 / dc
        qx = sL * (x - C0X) - F * (cs.x - C0X) / dc
        qy = sL * (y - C0Y) - F * (cs.y - C0Y) / dc
    if L is not None: qx, qy = L.to_output(qx, qy)
    pz = cs.pz; roll = cs.roll
    if roll:
        th = math.radians(abs(roll)); pz *= math.cos(th) + (CFG.rw / CFG.rh) * math.sin(th)
    th = math.radians(roll); c, s = math.cos(th), math.sin(th)
    ux, uy = qx - cs.px, qy - cs.py
    return C0X + pz * (c * ux - s * uy), C0Y + pz * (s * ux + c * uy)


def project_box(box, depth, cs=None, lens=None, ref_depth=None, n=9):
    """Project a design box (x, y, w, h) on a layer; returns the bounding box (x, y, w, h) of its image in the frame."""
    x, y, w, h = box
    u = np.linspace(0, 1, n)
    px = np.concatenate([x + w * u, np.full(n, x + w), x + w * u, np.full(n, x)])
    py = np.concatenate([np.full(n, y), y + h * u, np.full(n, y + h), y + h * u])
    X, Y = project(px, py, depth, cs, lens, ref_depth)
    return float(X.min()), float(Y.min()), float(X.max() - X.min()), float(Y.max() - Y.min())


class Scene:
    """Convenience bundle: Scene(layers, cam, ...).frame(t, i). Any of focus/dof/post/hud/grade may be f(t)."""

    def __init__(self, layers, cam=None, lens=None, grade=None, focus=1.0, dof=0.0, post=None, hud=None, bg='#000000'):
        self.layers, self.cam, self.lens, self.grade = layers, cam, lens, grade
        self.focus, self.dof, self.post, self.hud, self.bg = focus, dof, post, hud, bg

    def frame(self, t, i):
        cs = self.cam.at(t) if self.cam is not None else HOME
        g = self.grade(t) if callable(self.grade) and not isinstance(self.grade, P.Grade) else self.grade
        return render_frame(self.layers, cs, t, i, _val(self.focus, t) if not isinstance(self.focus, str) else self.focus,
                            _val(self.dof, t), self.lens, g, _val(self.post, t), self.hud, self.bg)
