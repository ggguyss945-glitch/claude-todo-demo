// camera.js — per-shot camera for engine v3 (bible 1.8, 3.3).
//
//   const cam = camera(t, opts)            (inside a shot: ctx.cam(opts), which fills t, dur, fps and a seed)
//
// World camera (world px, 1920x1080 design space; the screen centre shows world point (960 + x, 540 + y)):
//   keys    [[t, {x, y, z, r}, ease?], ...]  keyframes (fields carry forward; zoom is interpolated in log space).
//           Snap zoom: a key 6-8 frames after the previous one with ease 'outExpo'. Whip inside a shot: an x key
//           0.15-0.25 s after the previous one with 'inOutCubic' (motion blur switches on by itself).
//   push    extra slow push over the whole shot, e.g. 0.04 = +4% (inOutSine). Default 0.03 when no keys are given.
//   drift   slow seeded drift amplitude in px (default 10; 0 = locked)
//   dolly   0..1: far layers zoom less than near ones (0 = lens zoom, every depth zooms the same)
// Screen-space accents (applied after the world camera, so UI under cam.screen() can opt in):
//   punch   [{t, k = 1.12, at: [sx, sy], in = 2 frames, settle = 0.25 s, keep = 0.03}]  punch-in on a stressed word:
//           scale k about a screen point in 1-4 frames (outBack), settling back to 1 + keep over `settle`
//   shake   [{t, amp = 22, decay = 0.08, freq = 28, rot = 0}]  trauma shake (A e^(-t/decay) noise)
//   blur    'auto' (default): directional motion blur on fast moves (> 30 px/frame); false: crisp
//
// Output:
//   cam.layer(svg, depth = 1)        wraps world content in the camera transform for that parallax depth
//   cam.compose(layers)              [{svg, depth}] -> string, each layer at its depth (sets: sky .08, far .3, mid .75, near 1)
//   cam.set(set, {insert, only, skip, bake, live})  draw a sets.js set {layers}; insert: [{after: 'mid', svg, depth = 1}]
//                                    puts actors between layers; bake: 'kitchen' bakes every static layer (except `live`
//                                    names, default ['light', 'grade']: screen-blended layers must stay vector) to a bitmap of what this shot sees, at the shot's max zoom (render.js bake=1)
//   cam.screen(svg, {shake: true})   screen-locked layer (UI, stickers); shakes with the camera only if asked
//   cam.toScreen([x, y], depth = 1)  world -> screen point;  cam.toWorld([sx, sy], depth = 1) the inverse
//   cam.state                        {x, y, z, r, k, sx, sy, sr, vx, vy, speed (screen px/frame at depth 1)}
//   cam.maxZoom(depth = 1)           largest on-screen scale over the shot (for bake resolution)
//   cam.visible(depth = 1)           world rect [x0, y0, x1, y1] covering everything visible over the shot
import { FPS, clamp, lerp, track, isKeys, ease, noise1d, shake as shakeFn, hash } from './motion.js';

export const W = 1920, H = 1080, CX = W / 2, CY = H / 2;
const r6 = (n) => Math.round(n * 1e6) / 1e6, r3 = (n) => Math.round(n * 1000) / 1000;

// ---------- 2D affine matrices [a, b, c, d, e, f] (x' = a x + c y + e, y' = b x + d y + f) ----------
export const M = {
  id: () => [1, 0, 0, 1, 0, 0],
  mul: (A, B) => [A[0] * B[0] + A[2] * B[1], A[1] * B[0] + A[3] * B[1], A[0] * B[2] + A[2] * B[3], A[1] * B[2] + A[3] * B[3], A[0] * B[4] + A[2] * B[5] + A[4], A[1] * B[4] + A[3] * B[5] + A[5]],
  tr: (x, y) => [1, 0, 0, 1, x, y],
  sc: (sx, sy = sx) => [sx, 0, 0, sy, 0, 0],
  rot: (deg) => { const a = (deg * Math.PI) / 180, c = Math.cos(a), s = Math.sin(a); return [c, s, -s, c, 0, 0]; },
  about: (m, x, y) => M.mul(M.tr(x, y), M.mul(m, M.tr(-x, -y))),
  apply: (m, [x, y]) => [m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]],
  inv: (m) => { const det = m[0] * m[3] - m[1] * m[2] || 1e-9; return [m[3] / det, -m[1] / det, -m[2] / det, m[0] / det, (m[2] * m[5] - m[3] * m[4]) / det, (m[1] * m[4] - m[0] * m[5]) / det]; },
  str: (m) => `matrix(${r6(m[0])} ${r6(m[1])} ${r6(m[2])} ${r6(m[3])} ${r3(m[4])} ${r3(m[5])})`,
  isId: (m) => Math.abs(m[0] - 1) < 1e-7 && Math.abs(m[3] - 1) < 1e-7 && Math.abs(m[1]) < 1e-7 && Math.abs(m[2]) < 1e-7 && Math.abs(m[4]) < 1e-4 && Math.abs(m[5]) < 1e-4,
};

// ---------- punch-ins ----------
function punchK(t, list, fps) {
  let k = 1, ax = CX, ay = CY, wsum = 0;
  for (const p of list || []) {
    const t0 = p.t ?? 0, dt = t - t0; if (dt < 0) continue;
    const kk = p.k ?? 1.12, rise = (p.in ?? 2) / fps, settle = p.settle ?? 0.25, keep = p.keep ?? 0.03;
    const end = 1 + (kk - 1) * (p.hold ? 1 : clamp(keep / Math.max(1e-6, kk - 1)));
    let v;
    if (dt < rise) v = lerp(1, kk, ease.outBack(dt / rise));
    else if (p.hold) v = kk;
    else v = lerp(kk, end, ease.inOutSine(clamp((dt - rise) / settle)));
    if (p.until !== undefined && t > p.until) v = lerp(v, 1, ease.inOutSine(clamp((t - p.until) / (p.out ?? 0.2))));
    k *= v;
    const w = Math.abs(v - 1);
    if (p.at && w > 0) { ax = (ax * wsum + p.at[0] * w) / (wsum + w); ay = (ay * wsum + p.at[1] * w) / (wsum + w); wsum += w; }
  }
  return { k, ax, ay };
}

/** build the camera at local time t. o: see header; plus dur, fps, seed (ctx.cam fills them). */
export function camera(t, o = {}) {
  const fps = o.fps ?? FPS, dur = o.dur ?? 2, seed = o.seed ?? 1;
  const kt = isKeys(o.keys) ? {
    x: track(o.keys.map(([tt, v, e]) => [tt, v.x ?? null, e]).filter((k) => k[1] !== null), { default: 0 }),
    y: track(o.keys.map(([tt, v, e]) => [tt, v.y ?? null, e]).filter((k) => k[1] !== null), { default: 0 }),
    z: track(o.keys.map(([tt, v, e]) => [tt, v.z ?? null, e]).filter((k) => k[1] !== null), { log: true, default: 1 }),
    r: track(o.keys.map(([tt, v, e]) => [tt, v.r ?? null, e]).filter((k) => k[1] !== null), { default: 0 }),
  } : null;
  const push = o.push ?? (kt ? 0 : 0.03);
  const driftA = typeof o.drift === 'object' ? o.drift.amp ?? 10 : o.drift ?? 10;
  const driftF = typeof o.drift === 'object' ? o.drift.freq ?? 0.07 : 0.07;
  const base = (tt) => {
    let x = kt ? kt.x(tt) ?? 0 : o.x ?? 0, y = kt ? kt.y(tt) ?? 0 : o.y ?? 0, z = kt ? kt.z(tt) ?? 1 : o.z ?? 1, r = kt ? kt.r(tt) ?? 0 : o.r ?? 0;
    if (push) z *= 1 + push * ease.inOutSine(clamp(tt / Math.max(0.01, dur)));
    if (driftA) { x += driftA * noise1d(tt * driftF + 0.37, seed + 11); y += driftA * 0.6 * noise1d(tt * driftF + 0.71, seed + 12); }
    return { x, y, z, r };
  };
  const scr = (tt) => {
    const p = punchK(tt, o.punch, fps), s = shakeFn(tt, o.shake || [], seed + 31);
    return { k: p.k, ax: p.ax, ay: p.ay, sx: s.x, sy: s.y, sr: s.r };
  };
  const dolly = o.dolly ?? 0;
  const worldM = (b, d) => {
    const zd = dolly ? 1 + (b.z - 1) * lerp(1, d, dolly) : b.z;
    // screen = C + R(r) * zd * (P - (C + o*d))
    return M.mul(M.tr(CX, CY), M.mul(M.rot(b.r), M.mul(M.sc(zd), M.tr(-(CX + b.x * d), -(CY + b.y * d)))));
  };
  const screenM = (s, withShake = true) => {
    let m = M.about(M.sc(s.k), s.ax, s.ay);
    if (withShake && (s.sx || s.sy || s.sr)) m = M.mul(M.about(M.rot(s.sr), CX, CY), M.mul(M.tr(s.sx, s.sy), m));
    return m;
  };
  const full = (tt, d = 1) => M.mul(screenM(scr(tt)), worldM(base(tt), d));
  const b = base(t), s = scr(t);
  // screen velocity of the frame centre at depth 1 (px per frame), from a centred difference
  const p0 = M.apply(M.inv(full(t, 1)), [CX, CY]);
  const pa = M.apply(full(t - 0.5 / fps, 1), p0), pb = M.apply(full(t + 0.5 / fps, 1), p0);
  const vx = pb[0] - pa[0], vy = pb[1] - pa[1];
  const speed = Math.hypot(vx, vy);
  const blurOn = o.blur !== false && speed > (o.blurMin ?? 30);
  const cam = {
    t, opts: o, state: { ...b, ...s, vx, vy, speed },
    matrix: (d = 1) => M.mul(screenM(s), worldM(b, d)),
    layer(svg, depth = 1) { return `<g transform="${M.str(cam.matrix(depth))}">${svg}</g>`; },
    compose(layers) {
      return layers.filter(Boolean).map((l) => (l.screen ? cam.screen(l.svg, l) : cam.layer(l.svg, l.depth ?? 1))).join('');
    },
    set(set, so = {}) {
      const ins = so.insert ? (Array.isArray(so.insert) ? so.insert : [so.insert]) : [];
      const out = [];
      const defsL = set.layers.find((l) => l.name === 'defs');
      for (const l of set.layers) {
        if (so.only && !so.only.includes(l.name) && l.name !== 'defs') continue;
        if (so.skip && so.skip.includes(l.name)) continue;
        if (l.name === 'defs') out.push({ svg: l.svg, depth: 0, screen: true, shake: false });
        else out.push({ svg: so.bake && !(so.live || ['light', 'grade']).includes(l.name) ? cam.bakeLayer(so.bake, l, defsL) : l.svg, depth: l.depth });
        for (const i of ins) if (i.after === l.name) out.push({ svg: i.svg, depth: i.depth ?? 1, screen: i.screen });
      }
      for (const i of ins) if (!i.after || i.after === 'top') out.push({ svg: i.svg, depth: i.depth ?? 1, screen: i.screen });
      return cam.blur(cam.compose(out));
    },
    /** one set layer as a baked bitmap covering what this shot can see of it (needs ctx.cam, which passes bakeFn).
     *  key: a name for the set + its options; a function (layer) -> svg is also accepted for custom bakers. */
    bakeLayer(key, l, defsL) {
      if (typeof key === 'function') return key(l);
      if (!o.bakeFn) return l.svg;
      const [vx0, vy0, vx1, vy1] = cam.visible(l.depth);
      const B = o.bakeBounds || [-480, -240, 2400, 1320];
      const x0 = Math.floor(Math.max(B[0], vx0)), y0 = Math.floor(Math.max(B[1], vy0)), x1 = Math.ceil(Math.min(B[2], vx1)), y1 = Math.ceil(Math.min(B[3], vy1));
      if (x1 <= x0 || y1 <= y0) return l.svg;
      const box = { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
      const res = Math.max(1, Math.ceil(cam.maxZoom(l.depth) * 20) / 20);
      return o.bakeFn(`${key}/${l.name}/${x0},${y0},${box.w},${box.h}`, () => (defsL ? defsL.svg : '') + l.svg, box, res);
    },
    world(svg) { return cam.layer(svg, 1); },
    screen(svg, so = {}) {
      if (!so.shake) return svg;
      const m = screenM({ k: 1, ax: CX, ay: CY, sx: s.sx, sy: s.sy, sr: s.sr });
      return M.isId(m) ? svg : `<g transform="${M.str(m)}">${svg}</g>`;
    },
    toScreen(P, depth = 1) { return M.apply(cam.matrix(depth), P); },
    toWorld(P, depth = 1) { return M.apply(M.inv(cam.matrix(depth)), P); },
    /** directional motion blur for fast camera moves; wrap the composed world (never inside a <use>) */
    blur(svg) {
      if (!blurOn) return svg;
      return motionBlur(svg, vx, vy, { k: o.blurK ?? 0.45, max: o.blurMax ?? 90, id: `cb${seed % 9973}` });
    },
    maxZoom(depth = 1, n = 24) {
      let m = 0;
      for (let i = 0; i <= n; i++) {
        const tt = (dur * i) / n, A = full(tt, depth); m = Math.max(m, Math.hypot(A[0], A[1]));
      }
      return m;
    },
    visible(depth = 1, n = 24, pad = 40) {
      let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
      for (let i = 0; i <= n; i++) {
        const tt = (dur * i) / n, inv = M.inv(full(tt, depth));
        for (const P of [[-pad, -pad], [W + pad, -pad], [-pad, H + pad], [W + pad, H + pad]]) {
          const q = M.apply(inv, P); x0 = Math.min(x0, q[0]); y0 = Math.min(y0, q[1]); x1 = Math.max(x1, q[0]); y1 = Math.max(y1, q[1]);
        }
      }
      return [x0, y0, x1, y1];
    },
  };
  return cam;
}

/** directional blur of a frame-sized layer: feGaussianBlur along the motion (screen px per frame vx, vy).
 *  The filter region is the screen rectangle in user space, so cost stays frame-sized. */
export function motionBlur(svg, vx, vy, o = {}) {
  const sp = Math.hypot(vx, vy);
  if (sp < 1) return svg;
  const k = o.k ?? 0.45, sd = Math.min(o.max ?? 90, sp * k);
  const ang = (Math.atan2(vy, vx) * 180) / Math.PI;
  const id = `${o.id || 'mb'}_${Math.round(sd)}_${Math.round(ang)}`;
  // blur along x in a rotated frame: rotate content to the motion axis, blur horizontally, rotate back
  const axisAligned = Math.abs(vy) < Math.abs(vx) * 0.08 || Math.abs(vx) < Math.abs(vy) * 0.08;
  if (axisAligned) {
    const horiz = Math.abs(vx) >= Math.abs(vy);
    const f = `<filter id="${id}" filterUnits="userSpaceOnUse" x="-200" y="-200" width="${W + 400}" height="${H + 400}" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="${horiz ? r3(sd) : 0} ${horiz ? 0 : r3(sd)}" edgeMode="duplicate"/></filter>`;
    return `<defs>${f}</defs><g filter="url(#${id})">${svg}</g>`;
  }
  const f = `<filter id="${id}" filterUnits="userSpaceOnUse" x="-600" y="-600" width="${W + 1200}" height="${H + 1200}" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="${r3(sd)} 0" edgeMode="duplicate"/></filter>`;
  return `<defs>${f}</defs><g transform="rotate(${r3(ang)} ${CX} ${CY})"><g filter="url(#${id})"><g transform="rotate(${r3(-ang)} ${CX} ${CY})">${svg}</g></g></g>`;
}

/** helper: camera offset {x, y} so world point P sits at screen point S at zoom z (for framing a face) */
export function frameOn(P, z = 1, S = [CX, CY]) {
  return { x: P[0] - CX - (S[0] - CX) / z, y: P[1] - CY - (S[1] - CY) / z, z };
}
export { hash };
