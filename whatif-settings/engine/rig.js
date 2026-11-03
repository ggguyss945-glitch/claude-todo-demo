// rig.js — generic toy-figure construction shared by the cast.
// A figure is built in body units (1 unit = 1 px at s = 1) with the origin at the ground point between the
// feet; the head is built in head-local units (head width = 100) so the face kit and hair scale with it.
// Parts are rigid: rounded-trapezoid torso, capsule arms with an optional elbow, mitten hands, capsule legs,
// shoe caps. Facing is a yaw angle; every front feature is re-mapped around the head/torso, so one
// construction gives front, three-quarter, side and back views.
import { PAL, g, path, circle, ellipse, rect, grad, radial, shadeBand, stroke, tone, union, solid, rrect, rtrap, capsule, taper,
  glossCapsule, glossBox, contactShadow, f1, spline, polyline, uid, addDef } from './style.js';
import { face as drawFace, mapFeature, blankFace } from './face.js';

const D2R = Math.PI / 180;
export const FACINGS = {
  front: 0, 'three-quarter-right': 32, 'tq-right': 32, right: 32, 'three-quarter-left': -32, 'tq-left': -32, left: -32,
  side: 90, 'side-right': 90, 'side-left': -90, back: 180, 'tq-back-right': 148, 'tq-back-left': -148,
};
export const yawOf = (f) => (typeof f === 'number' ? f : FACINGS[f] ?? 0);

// ---------- head geometry (head-local units) ----------
// rounded rectangle half-width at height y; box {a, top, bot, rt, rb}
export function halfWidth(y, B) {
  const { a, top, bot, rt, rb } = B;
  if (y < top || y > bot) return 0;
  if (y < top + rt) { const d = top + rt - y; return a - rt + Math.sqrt(Math.max(0, rt * rt - d * d)); }
  if (y > bot - rb) { const d = y - (bot - rb); return a - rb + Math.sqrt(Math.max(0, rb * rb - d * d)); }
  return a;
}
// outline points of the box from the right side at yR, over the top, down the left side to yL
function topOutline(B, yR, yL) {
  const pts = [], { a, top, rt } = B, n = 14;
  const side = (y0, y1, sgn) => { const steps = Math.max(2, Math.ceil(Math.abs(y1 - y0) / 6)); for (let i = 0; i <= steps; i++) { const y = y0 + ((y1 - y0) * i) / steps; pts.push([sgn * halfWidth(y, B), y]); } };
  if (yR > top + rt) side(yR, top + rt, 1);
  for (let i = 0; i <= n; i++) { const t = (-90 * i) / n * D2R; const x = a - rt + rt * Math.cos(t), y = top + rt + rt * Math.sin(t); if (y <= yR) pts.push([x, y]); }
  for (let i = 0; i <= n; i++) { const t = (-90 - (90 * i) / n) * D2R; const x = -(a - rt) + rt * Math.cos(t), y = top + rt + rt * Math.sin(t); if (y <= yL) pts.push([x, y]); }
  if (yL > top + rt) side(top + rt, yL, -1);
  return pts;
}
// u (around-the-head coordinate: 0 front centre, +-1 sides, +-2 back) -> screen angle for yaw
const wrapU = (u) => ((((u + 2) % 4) + 4) % 4) - 2;
// hairline y(u): tips [[u, y, depth, skew]] — scallops between tips (sharp V at each tip)
export function hairline(tips, u) {
  u = wrapU(u);
  for (let i = 0; i < tips.length - 1; i++) {
    const [u0, y0, d0 = 0, sk = 1] = tips[i], [u1, y1] = tips[i + 1];
    if (u >= u0 && u <= u1) { const t = (u - u0) / (u1 - u0 || 1); return y0 + (y1 - y0) * t - d0 * Math.sin(Math.PI * t ** sk); }
  }
  return tips[tips.length - 1][1];
}
// The helmet: region above the hairline, bounded by the head box grown by t (and crown extra on top).
// Returns the path in head-local units for this yaw.
export function helmetPath(spec, head, yaw) {
  const t = spec.t ?? 4, crown = spec.crown ?? 4;
  const B = { a: 50 + t, top: head.top - t - crown, bot: head.bot + t, rt: head.r + t + crown * 0.6, rb: head.r + t };
  const angles = new Set();
  for (let i = 0; i <= 120; i++) angles.add(-90 + (180 * i) / 120);
  for (const tp of spec.tips) for (const k of [-4, 0, 4]) { const a = (tp[0] + k) * 90 + yaw; if (a > -90 && a < 90) angles.add(a); }
  const al = [...angles].sort((p, q) => p - q);
  const bottom = al.map((a) => { const u = (a - yaw) / 90, y = Math.min(hairline(spec.tips, u), B.bot - 1); return [halfWidth(y, B) * Math.sin(a * D2R), y]; });
  const yL = bottom[0][1], yR = bottom[bottom.length - 1][1];
  const pts = bottom.concat(topOutline(B, yR, yL));
  return { d: polyline(pts), B };
}
// a band of hair between two hairlines (bald tops, comb-overs): top(u) and bottom(u), present where mask(u)
export function bandPaths(spec, head, yaw) {
  const t = spec.t ?? 4;
  const B = { a: 50 + t, top: head.top - t, bot: head.bot + t, rt: head.r + t, rb: head.r + t };
  const out = [];
  let run = [];
  const flush = () => {
    if (run.length > 1) {
      const top = run.map(([a, u]) => { const y = hairline(spec.top, u); return [halfWidth(y, B) * Math.sin(a * D2R), y]; });
      const bot = run.map(([a, u]) => { const y = hairline(spec.bottom, u); return [halfWidth(y, B) * Math.sin(a * D2R), y]; }).reverse();
      out.push(polyline(top.concat(bot)));
    }
    run = [];
  };
  for (let i = 0; i <= 140; i++) {
    const a = -90 + (180 * i) / 140, u = wrapU((a - yaw) / 90);
    if (spec.mask(u)) run.push([a, u]); else flush();
  }
  flush();
  return out;
}
// wavy highlight strands across the hair (light) or a shadow line above the fringe (dark)
export function strands(list, head, yaw, color, spec) {
  const t = spec.t ?? 4, crown = spec.crown ?? 4;
  const B = { a: 50 + t, top: head.top - t - crown, bot: head.bot + t, rt: head.r + t + crown * 0.6, rb: head.r + t };
  let out = '';
  for (const s of list) {
    const segs = []; let cur = [];
    for (let i = 0; i <= 48; i++) {
      const u = s.u0 + ((s.u1 - s.u0) * i) / 48, a = u * 90 + yaw;
      const yb = s.follow ? hairline(spec.tips, u) - s.follow : s.y;
      const y = yb + (s.amp ?? 2) * Math.sin((s.waves ?? 3) * Math.PI * (u - s.u0) / Math.max(0.01, s.u1 - s.u0) * 2);
      const hw = halfWidth(y, B) - (s.inset ?? 8);
      if (a > -78 && a < 78 && hw > 0) cur.push([hw * Math.sin(a * D2R), y]); else if (cur.length) { segs.push(cur); cur = []; }
    }
    if (cur.length) segs.push(cur);
    for (const sg of segs) if (sg.length > 2) out += path(spline(sg), { fill: 'none', stroke: s.dark ? tone(color, -0.09, 1.1) : tone(color, 0.095, 0.88), strokeWidth: s.w ?? 4.2, strokeLinecap: 'round', opacity: s.op ?? 0.95 });
  }
  return out;
}
// position on a cylinder around the head for an attachment at u (ponytail, pigtails, ears)
export function wrapPoint(u, y, yaw, R = 50, out = 0) {
  const a = (u * 90 + yaw) * D2R;
  return { x: (R + out) * Math.sin(a), z: Math.cos(a), a };
}

// ---------- limbs ----------
const dirDown = (deg, sgn) => [-sgn * Math.sin(deg * D2R), Math.cos(deg * D2R)];
// mitten hand at wrist w, pointing along dir, thumb on the inner side. kind: open | fist | point | thumbs | grip | flat
export function mitten(wx, wy, dir, size, inner, kind, skin, sw) {
  const [dx, dy] = dir, nx = -dy, ny = dx;           // n: perpendicular
  const P = (a, b) => [wx + dx * a + nx * b * inner, wy + dy * a + ny * b * inner];
  const shapes = [];
  const r = size;
  if (kind === 'fist' || kind === 'grip' || kind === 'point' || kind === 'thumbs') {
    const c = P(r * 0.75, 0);
    shapes.push({ d: `M${f1(c[0] - r * 0.92)} ${f1(c[1])}a${f1(r * 0.92)} ${f1(r * 0.92)} 0 1 0 ${f1(r * 1.84)} 0a${f1(r * 0.92)} ${f1(r * 0.92)} 0 1 0 ${f1(-r * 1.84)} 0Z` });
    if (kind === 'point') { const a = P(r * 0.9, r * 0.3), b = P(r * 2.2, r * 0.5); shapes.push({ d: capsule(a[0], a[1], b[0], b[1], r * 0.62) }); }
    if (kind === 'thumbs') { const a = P(r * 0.5, r * 0.55), b = P(r * 0.1, r * 1.55); shapes.push({ d: capsule(a[0], a[1], b[0], b[1], r * 0.6) }); }
  } else {
    // palm: an ellipse a little longer than wide, along the forearm; thumb nub on the inner side
    const c = P(r * 1.0, 0), pts = [];
    for (let i = 0; i < 16; i++) { const t = (i / 16) * Math.PI * 2, al = Math.cos(t) * r * 1.04, pe = Math.sin(t) * r * 0.9; pts.push([c[0] + dx * al + nx * pe, c[1] + dy * al + ny * pe]); }
    shapes.push({ d: spline(pts, { closed: true }) });
    if (kind !== 'flat') { const a = P(r * 0.5, r * 0.7), b = P(r * 0.9, r * 1.22); shapes.push({ d: capsule(a[0], a[1], b[0], b[1], r * 0.56) }); }
  }
  const xs = shapes.length ? [wx - r * 3, wy - r * 3, wx + r * 3, wy + r * 3] : null;
  return union(shapes, skin, { sw, box: xs });
}
// soft fabric stripes along a capsule segment (pyjamas): lines parallel to the axis, inside the capsule body
export function segStripes(x1, y1, x2, y2, w, st, { from = 0, to = 1 } = {}) {
  if (!st) return '';
  const dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy) || 0.001, ux = dx / L, uy = dy / L, nx = -uy, ny = ux;
  const r = w / 2, n = st.n ?? 3, lw = w * (st.w ?? 0.15);
  let out = '';
  for (let i = 0; i < n; i++) {
    const o = (n === 1 ? 0 : -0.62 + (1.24 * i) / (n - 1)) * (r - lw * 0.6);
    const inset = Math.sqrt(Math.max(0, r * r - o * o)) * 0.55 + lw * 0.5;
    const a0 = Math.max(L * from, inset * (from <= 0 ? 1 : 0)), a1 = Math.min(L * to, L - inset * (to >= 1 ? 1 : 0));
    if (a1 <= a0) continue;
    out += path(`M${f1(x1 + ux * a0 + nx * o)} ${f1(y1 + uy * a0 + ny * o)}L${f1(x1 + ux * a1 + nx * o)} ${f1(y1 + uy * a1 + ny * o)}`, { stroke: st.color, strokeOpacity: st.op ?? 0.8, strokeWidth: f1(lw), strokeLinecap: 'round', fill: 'none' });
  }
  return out;
}
// arm chain. returns { svg, hand: [x,y], dir }
export function arm(o) {
  const { sx, sy, a, fore = 0, sgn, d, sleeve, skin, sw, handKind = 'open', sleeveLen = 1, cuff = null, sleeveW = 1.1, stripes = null } = o;
  const u = dirDown(a, sgn), e = [sx + u[0] * d.up, sy + u[1] * d.up];
  const v = dirDown(a + fore, sgn), w = [e[0] + v[0] * d.fore, e[1] + v[1] * d.fore];
  const pad = d.w * 1.2, box = [Math.min(sx, e[0], w[0]) - pad, Math.min(sy, e[1], w[1]) - pad, Math.max(sx, e[0], w[0]) + pad, Math.max(sy, e[1], w[1]) + pad];
  let svg = '';
  const segs = [{ d: capsule(sx, sy, e[0], e[1], d.w) }, { d: capsule(e[0], e[1], w[0], w[1], d.w * 0.96) }];
  const hand = () => mitten(w[0] - v[0] * d.w * 0.15, w[1] - v[1] * d.w * 0.15, v, d.hand, -sgn, handKind, skin, sw);
  if (sleeve && sleeveLen >= 1) {
    svg += union(segs, sleeve, { sw, box });
    if (stripes) svg += segStripes(sx, sy, e[0], e[1], d.w, stripes, { from: 0.12 }) + segStripes(e[0], e[1], w[0], w[1], d.w * 0.96, stripes, { to: 0.86 });
    svg += glossCapsule(sx, sy, e[0], e[1], d.w, { op: 0.34 }) + glossCapsule(e[0], e[1], w[0], w[1], d.w, { op: 0.3, thin: false });
    if (cuff) { const c0 = [w[0] - v[0] * d.w * 0.42, w[1] - v[1] * d.w * 0.42]; svg += path(capsule(c0[0], c0[1], w[0] - v[0] * 0.5, w[1] - v[1] * 0.5, d.w * 1.04), { fill: grad(cuff, 'd'), stroke: stroke(cuff), strokeWidth: f1(sw) }); }
    svg += hand();
  } else {
    svg += union(segs, skin, { sw, box });
    svg += glossCapsule(e[0], e[1], w[0], w[1], d.w, { op: 0.26, thin: false });
    if (sleeve) {
      const L = d.up * sleeveLen, se = [sx + u[0] * L, sy + u[1] * L];
      svg += path(taper(sx - u[0] * 4, sy - u[1] * 4, se[0], se[1], d.w * sleeveW * 0.5, d.w * sleeveW * 0.56), { fill: grad(sleeve, 'd', { box }), stroke: stroke(sleeve), strokeWidth: f1(sw), strokeLinejoin: 'round' });
      svg += glossCapsule(sx, sy, se[0], se[1], d.w * sleeveW, { op: 0.34, from: 0.1, to: 0.7, thin: false });
    } else svg += glossCapsule(sx, sy, e[0], e[1], d.w, { op: 0.26, thin: false });
    svg += hand();
  }
  return { svg, hand: [w[0] + v[0] * d.hand * 0.75, w[1] + v[1] * d.hand * 0.75], wrist: w, elbow: e, dir: v, handSvg: '' };
}
// leg with pants (full or shorts) and a shoe cap
export function leg(o) {
  const { hx, hy, a, sgn, d, pants, pantLen = 1, skin, sw, shoe, yaw = 0, sock = null, knee = 0, stripes = null, hem = null } = o;
  const u = dirDown(a, sgn);
  const L = d.len, ax = hx + u[0] * L, ay = hy + u[1] * L;
  const box = [Math.min(hx, ax) - d.w, hy - 4, Math.max(hx, ax) + d.w, ay + 4];
  let svg = '';
  if (pantLen >= 1) {
    svg += union([{ d: capsule(hx, hy, ax, ay, d.w) }], pants, { sw, box });
    if (stripes) svg += segStripes(hx, hy, ax, ay, d.w, stripes, { from: 0.05 });
    if (hem) { const h0 = [hx + u[0] * (L - d.w * 0.62), hy + u[1] * (L - d.w * 0.62)]; svg += path(capsule(h0[0], h0[1], ax, ay - 1, d.w * 1.02), { fill: grad(hem, 'd'), stroke: stroke(hem), strokeWidth: f1(sw * 0.9) }); }
  } else {
    svg += union([{ d: capsule(hx, hy, ax, ay, d.w * 0.86) }], skin, { sw, box });
    if (sock) { const s0 = [hx + u[0] * L * 0.8, hy + u[1] * L * 0.8]; svg += path(capsule(s0[0], s0[1], ax, ay, d.w * 0.9), { fill: grad(sock, 'd'), stroke: stroke(sock), strokeWidth: f1(sw) }); }
    const pe = [hx + u[0] * L * pantLen, hy + u[1] * L * pantLen];
    svg += path(taper(hx, hy - 6, pe[0], pe[1], d.w * 0.56, d.w * 0.62), { fill: grad(pants, 'd', { box }), stroke: stroke(pants), strokeWidth: f1(sw), strokeLinejoin: 'round' });
  }
  svg += glossCapsule(hx, hy, ax, ay, d.w * (pantLen >= 1 ? 1 : 0.86), { op: 0.22, thin: false, from: 0.12, to: 0.7 });
  svg += shoeCap(ax, ay, shoe, d, sw, yaw, u);
  void knee;
  return { svg, ankle: [ax, ay] };
}
// shoe cap: a domed toe seen from the front; stretches toward the facing side in profile
export function shoeCap(ax, ay, shoe, d, sw, yaw, u = [0, 1]) {
  const s = Math.sin(yaw * D2R), c = Math.abs(Math.cos(yaw * D2R));
  const w = shoe.w * (0.92 + 0.5 * Math.abs(s)), h = shoe.h, off = s * shoe.w * 0.32;
  const bx = ax + off + u[0] * 4, by = ay + h * 0.62;
  const x0 = bx - w / 2, x1 = bx + w / 2, yb = by, yt = by - h;
  const toe = s > 0.2 ? 1 : s < -0.2 ? -1 : 0;
  const tl = toe === -1 ? 0.62 : 0.5, tr = toe === 1 ? 0.62 : 0.5;
  const dd = `M${f1(x0)} ${f1(yb - 3)}Q${f1(x0)} ${f1(yt + h * tl * 0.3)} ${f1(x0 + w * 0.2)} ${f1(yt + h * 0.12)}Q${f1(bx)} ${f1(yt - h * 0.1)} ${f1(x1 - w * 0.2)} ${f1(yt + h * 0.12)}Q${f1(x1)} ${f1(yt + h * tr * 0.3)} ${f1(x1)} ${f1(yb - 3)}Q${f1(x1)} ${f1(yb)} ${f1(x1 - 4)} ${f1(yb)}L${f1(x0 + 4)} ${f1(yb)}Q${f1(x0)} ${f1(yb)} ${f1(x0)} ${f1(yb - 3)}Z`;
  let svg = path(dd, { fill: grad(shoe.color, 'd'), stroke: stroke(shoe.color), strokeWidth: f1(sw), strokeLinejoin: 'round' });
  if (shoe.sole) svg += path(`M${f1(x0 + 1)} ${f1(yb - h * 0.3)}L${f1(x1 - 1)} ${f1(yb - h * 0.3)}L${f1(x1 - 1)} ${f1(yb - 3)}Q${f1(x1 - 1)} ${f1(yb - 1)} ${f1(x1 - 4)} ${f1(yb - 1)}L${f1(x0 + 4)} ${f1(yb - 1)}Q${f1(x0 + 1)} ${f1(yb - 1)} ${f1(x0 + 1)} ${f1(yb - 3)}Z`, { fill: grad(shoe.sole, 'v'), stroke: stroke(shoe.color), strokeWidth: f1(sw * 0.7), strokeLinejoin: 'round' });
  if (shoe.accent) svg += path(`M${f1(bx - w * 0.28 + off * 0.3)} ${f1(yt + h * 0.42)}Q${f1(bx + off * 0.3)} ${f1(yt + h * 0.3)} ${f1(bx + w * 0.28 + off * 0.3)} ${f1(yt + h * 0.42)}`, { fill: 'none', stroke: shoe.accent, strokeWidth: f1(sw * 1.1), strokeLinecap: 'round' });
  svg += path(`M${f1(x0 + w * 0.22)} ${f1(yt + h * 0.32)}Q${f1(bx - w * 0.05)} ${f1(yt + h * 0.12)} ${f1(bx + w * 0.12)} ${f1(yt + h * 0.16)}`, { fill: 'none', stroke: '#FFFFFF', strokeOpacity: 0.55, strokeWidth: f1(sw * 0.9), strokeLinecap: 'round' });
  void c;
  return svg;
}

// ---------- head ----------
// merge toon-level add-ons ({sweat, tears, blush, q, zzz, stars|dizzy, bump, hearts, ...}) into a face spec
export function withAdd(faceSpec, add) {
  if (!add || !Object.keys(add).length) return faceSpec;
  const a = { ...add }; if (a.stars) { a.dizzy = a.stars; delete a.stars; }
  if (!faceSpec || typeof faceSpec === 'string') return { preset: faceSpec || 'neutral', add: a };
  return { ...faceSpec, add: { ...(faceSpec.add || {}), ...a } };
}
// draws head shape + face + hair in head-local units; returns markup placed by the caller
export function headMarkup(spec, o) {
  const { yaw, faceSpec, look, sw, pose, add, blank = 0 } = o;
  const hd = spec.dims.head;
  const hh = (100 * hd.h) / hd.w, head = { top: -hh / 2, bot: hh / 2, r: hd.r * 100, a: 50 };
  const skin = spec.skin;
  const lsw = (sw * 100) / hd.w;                     // outline width in head units
  const ctx = { yaw, head, sw: lsw, pose: pose || {}, spec, back: Math.abs(yaw) > 120, side: Math.abs(yaw) > 75 };
  let back = '', front = '', over = '';
  if (spec.hair?.behind) back += spec.hair.behind(ctx);
  const hp = rrect(-50, head.top, 100, hh, head.r);
  let skull = path(hp, { fill: radial(skin, { cx: 0.36, cy: 0.34, r: 0.85 }), stroke: stroke(skin), strokeWidth: f1(lsw), strokeLinejoin: 'round' });
  skull += path(hp, { fill: shadeBand(skin, { at: ctx.back ? 0.86 : 0.875, op: 0.6, dL: 0.075 }) });
  skull += path(`M-41 ${f1(head.top + hh * 0.42)}L-41 ${f1(head.top + hh * 0.8)}`, { stroke: '#FFFFFF', strokeOpacity: 0.55, strokeWidth: 4.2, strokeLinecap: 'round', fill: 'none' });
  if (spec.ears === false) { /* no ears */ } else if (typeof spec.ears === 'function') skull = spec.ears(ctx) + skull;
  else {
    // small ears on the cylinder at u = +-1: behind the skull (peeking out) or on it when that side faces us
    const ey = (spec.faceOpts?.eyeY ?? 6) + 5;
    let behind = '', onTop = '';
    for (const sd of [-1, 1]) {
      const a = (sd * 90 + yaw) * D2R, z = Math.cos(a), x = 50 * Math.sin(a);
      if (z < -0.35) continue;
      if (z <= 0.2) {
        const ox = x + Math.sign(x || sd) * 3;
        behind += path(`M${f1(ox - 7.5)} ${f1(ey)}a7.5 10.5 0 1 0 15 0a7.5 10.5 0 1 0 -15 0Z`, { fill: grad(skin, 'd'), stroke: stroke(skin), strokeWidth: f1(lsw), strokeLinejoin: 'round' })
          + path(`M${f1(ox + Math.sign(x || sd) * 1.5)} ${f1(ey - 5)}Q${f1(ox + Math.sign(x || sd) * 4)} ${f1(ey)} ${f1(ox + Math.sign(x || sd) * 1)} ${f1(ey + 5)}`, { fill: 'none', stroke: stroke(skin), strokeWidth: 2, strokeLinecap: 'round', opacity: 0.55 });
      } else {
        const k = Math.max(0.45, z);
        onTop += g(path('M-6.5 -9.5Q4.5 -11.5 6.5 -2Q7.5 8 -1 10.5Q-5 11.5 -6.5 8Z', { fill: grad(skin, 'd'), stroke: stroke(skin), strokeWidth: f1(lsw), strokeLinejoin: 'round' })
          + path('M-2.5 -5Q3 -5.5 3 0Q2.5 4.5 -1 5.5', { fill: 'none', stroke: stroke(skin), strokeWidth: 2, strokeLinecap: 'round', opacity: 0.55 }),
        { transform: `translate(${f1(x)} ${f1(ey)}) scale(${f1(-sd * k)} 1)` });
      }
    }
    skull = behind + skull + onTop;
  }
  const fopts = { yaw, skin, look, top: head.top - (spec.hair?.height ?? 10), headBox: head, ...(spec.faceOpts || {}) };
  const f = drawFace(withAdd(faceSpec, add), fopts);
  if (spec.hair?.front) front += spec.hair.front(ctx);
  if (spec.headwear) over += spec.headwear(ctx, f);
  const preface = spec.faceUnder ? spec.faceUnder(ctx) : '';
  // mannequin blend: the features fade out (gone by blank 0.75) while the moulded blank face fades in
  let feat = preface + f.face;
  if (blank > 0) {
    const fo = 1 - Math.min(1, Math.max(0, (blank - 0.25) / 0.5)), bo = Math.min(1, Math.max(0, (blank - 0.35) / 0.5));
    feat = (fo > 0.001 ? (fo < 0.999 ? g(feat, { opacity: f1(fo * 100) / 100 }) : feat) : '') + (bo > 0.001 ? g(blankFace(fopts), bo < 0.999 ? { opacity: f1(bo * 100) / 100 } : {}) : '');
  }
  // the floating add-ons (sweat, ?, sparkles) fade with the features: a mannequin does not sweat
  const fxOut = blank > 0 ? (blank >= 0.75 ? '' : g(f.fx, { opacity: f1((1 - Math.max(0, (blank - 0.25) / 0.5)) * 100) / 100 })) : f.fx;
  return { svg: back + skull + feat + (spec.faceOver ? spec.faceOver(ctx, faceSpec) : '') + front + over, fx: fxOut, add };
}

// ---------- the figure ----------
// spec: per-character construction (see cast.js). o: { x, y, s, facing, pose, face, look, add, props }
export function buildFigure(spec, o = {}) {
  const yaw = yawOf(o.facing ?? 'front');
  const pose = { armL: 8, armR: 8, foreL: 0, foreR: 0, legL: 3, legR: 3, head: 0, lean: 0, bob: 0, ...(spec.pose || {}), ...(o.pose || {}) };
  const d = spec.dims, s = o.s ?? 1;
  const sw = d.head.h * (spec.lineK ?? 0.028);
  const sn = Math.sin(yaw * D2R), cs = Math.cos(yaw * D2R), aS = Math.abs(sn), aC = Math.abs(cs);
  const back = aC > 0.5 && cs < 0, sideOn = aS > 0.94;
  const kW = aC + 0.72 * aS;                                   // torso projected width factor
  const ankleY = -d.shoe.h * 0.62;
  const hipY = ankleY - d.leg.len;
  const torsoBot = hipY + (d.torso.hipOverlap ?? 14);
  const torsoTop = torsoBot - d.torso.h;
  const shrug = Math.max(0, Math.min(1.3, pose.shrug || 0));          // 0..1: shoulders up, head sinks into them
  const shoulderY = torsoTop + (d.torso.shoulder ?? 20) - 9 * shrug;
  const neckY = torsoTop + (d.torso.neck ?? 6);
  const headCY = neckY - d.head.h / 2 + (d.head.sink ?? 0) + 6 * shrug;
  const wt = d.torso.wt * kW, wb = d.torso.wb * kW;
  const tm = (x) => { const m = mapFeature((x / (d.torso.wt / 2)) * 50, yaw); return { x: (m.x / 50) * (wt / 2), k: m.k }; };
  const ctx = { yaw, sn, cs, back, sideOn, sw, d, pose, torsoTop, torsoBot, shoulderY, neckY, hipY, wt, wb, tm, spec, kW, add: o.add || {}, props: { ...(spec.props || {}), ...(o.props || {}) } };

  // shoulders & hips placed on the rotating body
  const shX = d.torso.wt / 2 + d.arm.w * (d.arm.out ?? 0.02), hipX = d.leg.hip;
  const armL = { x: -shX * cs, z: shX * sn, sgn: 1, a: pose.armL, fore: pose.foreL, hand: pose.handL || spec.hands?.L || 'open', id: 'L' };
  const armR = { x: shX * cs, z: -shX * sn, sgn: -1, a: pose.armR, fore: pose.foreR, hand: pose.handR || spec.hands?.R || 'open', id: 'R' };
  const legLp = { x: -hipX * cs, z: hipX * sn, sgn: 1, a: pose.legL, id: 'L' };
  const legRp = { x: hipX * cs, z: -hipX * sn, sgn: -1, a: pose.legR, id: 'R' };
  // in the back view the screen sides swap, so mirror the angle sign to keep "outward" outward
  for (const p of [armL, armR, legLp, legRp]) if (back) p.sgn = -p.sgn;

  const props = { ...(spec.props || {}), ...(o.props || {}) };
  const drawArm = (A) => {
    const r = arm({ sx: A.x, sy: shoulderY, a: A.a, fore: A.fore, sgn: A.sgn, d: d.arm, sleeve: spec.top.sleeve ? (spec.top.sleeveColor || spec.top.color) : null, skin: spec.skin, sw, handKind: props[A.id] ? (spec.propGrip?.[props[A.id]] || 'grip') : A.hand, sleeveLen: spec.top.sleeveLen ?? 1, cuff: spec.top.cuff, sleeveW: spec.top.sleeveW, stripes: spec.top.stripes });
    let pre = '', post = '';
    if (props[A.id] && spec.drawProp) { const pr = spec.drawProp(props[A.id], { hand: r.hand, wrist: r.wrist, dir: r.dir, side: A.id, sw, ctx }); pre = pr.behind || ''; post = pr.front || ''; }
    return pre + r.svg + post;
  };
  const drawLeg = (Lg) => leg({ hx: Lg.x, hy: hipY, a: Lg.a, sgn: Lg.sgn, d: d.leg, pants: spec.pants.color, pantLen: spec.pants.len ?? 1, skin: spec.skin, sw, shoe: { ...d.shoe, ...spec.shoes }, yaw, sock: spec.pants.sock, stripes: spec.pants.stripes, hem: spec.pants.hem }).svg;

  // ---- assemble (painter's order) ----
  let lower = '', upper = '', far = '', near = '';
  const legs = [legLp, legRp].sort((p, q) => p.z - q.z);
  const withLegs = o.legs !== false;                          // legs: false -> waist up (in bed, behind a counter)
  if (withLegs) for (const Lg of legs) lower += drawLeg(Lg);
  // pelvis bridges the legs so pants read as one garment
  if (withLegs) {
    const pw = (hipX * 2 * aC + d.leg.w * 0.5 * aS) + d.leg.w, ph = d.torso.pelvis ?? 24;
    const px = -pw / 2, py = torsoBot - ph * 0.55;
    const pc = spec.pants.hip || spec.pants.color;
    lower += path(rrect(px, py, pw, ph, Math.min(12, ph / 2)), { fill: grad(pc, 'd'), stroke: stroke(pc), strokeWidth: f1(sw), strokeLinejoin: 'round' });
    if (spec.decor?.belt) lower += spec.decor.belt(ctx, { px, py, pw, ph });
  }
  const arms = [armL, armR];
  const farArms = sideOn || aS > 0.3 ? arms.filter((A) => A.z < 0) : [];
  const nearArms = arms.filter((A) => !farArms.includes(A));
  for (const A of farArms) far += drawArm(A);

  // torso
  const tp = rtrap(0, torsoTop, torsoBot, wt, wb, d.torso.rt * Math.min(1, kW + 0.15), d.torso.rb);
  let torso = '';
  if (spec.decor?.behindTorso) torso += spec.decor.behindTorso(ctx);
  torso += path(tp, { fill: grad(spec.top.color, 'd'), stroke: stroke(spec.top.color), strokeWidth: f1(sw), strokeLinejoin: 'round' });
  if (spec.top.stripes) torso += torsoStripes(tp, spec.top.stripes, { torsoTop, torsoBot, wt, wb, tm, d });
  if (spec.decor?.torso) torso += spec.decor.torso(ctx);
  torso += path(tp, { fill: shadeBand(spec.top.color, { at: 0.88, op: 0.45, dL: 0.06 }) });
  torso += glossBox(-wt / 2, torsoTop, wt, d.torso.h, { op: 0.3, sw: sw * 1.3 });
  let neck = spec.decor?.neck ? spec.decor.neck(ctx) : '';

  // head
  const hs = d.head.w / 100;
  const hm = headMarkup(spec, { yaw, faceSpec: o.face, look: o.look, sw, pose, add: o.add, blank: o.blank || 0 });
  const headG = g(hm.svg, { transform: `translate(0 ${f1(headCY)}) scale(${f1(hs * 1000) / 1000})` });
  const fxG = g(hm.fx, { transform: `translate(0 ${f1(headCY)}) scale(${f1(hs * 1000) / 1000})` });
  const headPivot = `rotate(${f1(pose.head)} 0 ${f1(neckY)})`;
  let neckFront = spec.decor?.neckFront ? spec.decor.neckFront(ctx) : '';
  for (const A of nearArms) near += drawArm(A);
  const extra = spec.decor?.over ? spec.decor.over(ctx) : '';

  upper = far + torso + neck + g(headG, { transform: headPivot }) + neckFront + near + extra + g(fxG, { transform: headPivot });
  const upperG = g(upper, { transform: `translate(0 ${f1(pose.bob)}) rotate(${f1(pose.lean)} 0 ${f1(hipY)})` });
  const shadowW = (hipX + d.shoe.w * 0.55) * (aC + 0.6 * aS) * 1.25 + 10;
  const shadow = o.shadow === false || !withLegs ? '' : contactShadow(0, 2, shadowW, 9 + d.shoe.w * 0.08, { op: 0.3 });
  const body = shadow + lower + upperG;
  const tx = `translate(${f1(o.x ?? 0)} ${f1(o.y ?? 0)}) scale(${f1(s * 1000) / 1000})`;
  return g(body, { transform: tx });
}

// vertical fabric stripes wrapped round the torso (they follow the yaw like the other front details), clipped to it
function torsoStripes(tp, st, { torsoTop, torsoBot, wt, wb, tm, d }) {
  const id = uid('ts');
  addDef(id, `<clipPath id="${id}"><path d="${tp}"/></clipPath>`);
  const gap = st.gap ?? 17, lw = st.wT ?? 5.2, hw = d.torso.wb / 2;
  let out = '';
  for (let x = -Math.floor(hw / gap) * gap; x <= hw; x += gap) {
    const a = tm(x * (d.torso.wt / d.torso.wb)), b = tm(x);
    if (a.k < 0.12 && b.k < 0.12) continue;
    out += path(`M${f1(a.x)} ${f1(torsoTop - 2)}L${f1(b.x)} ${f1(torsoBot + 2)}`, { stroke: st.color, strokeOpacity: st.op ?? 0.8, strokeWidth: f1(lw * Math.max(0.35, (a.k + b.k) / 2)), fill: 'none' });
  }
  void wt; void wb;
  return g(out, { clipPath: `url(#${id})` });
}
// height of a figure in body units (ground to top of hair), for layout
export function figureHeight(spec) {
  const d = spec.dims; const ankleY = -d.shoe.h * 0.62, hipY = ankleY - d.leg.len, torsoBot = hipY + (d.torso.hipOverlap ?? 14), torsoTop = torsoBot - d.torso.h;
  const neckY = torsoTop + (d.torso.neck ?? 6);
  return -(neckY - d.head.h + (d.head.sink ?? 0)) + (spec.hair?.height ?? 8) * (d.head.w / 100);
}
export function hipYOf(spec) { const d = spec.dims; return -d.shoe.h * 0.62 - d.leg.len; }
export function headCenterY(spec) {
  const d = spec.dims; const ankleY = -d.shoe.h * 0.62, hipY = ankleY - d.leg.len, torsoBot = hipY + (d.torso.hipOverlap ?? 14), torsoTop = torsoBot - d.torso.h;
  return torsoTop + (d.torso.neck ?? 6) - d.head.h / 2 + (d.head.sink ?? 0);
}
export { mapFeature };
