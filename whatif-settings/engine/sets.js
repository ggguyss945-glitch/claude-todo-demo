// Backgrounds for "What If Real Life Had a SETTINGS MENU?" in the clean toy-plastic style (bible 1.6, 3.1):
// 2-stop gradients on every surface, gloss strips on lit edges (key light upper left), tinted outlines that thin with depth
// (near props ~3px, mid buildings ~2px, far layers none), no cast shadows (soft contact ellipses only), motivated light pools,
// atmospheric haze on far layers, one hue family per scene. Every set returns
//   { w, h, layers: [{ name, depth, svg }], svg }   (svg = layers composed for cam {x,y})
// and draws x from -480 to 2400 so the camera can pan +-400 px. Depth factors: sky 0.08, far 0.3, mid 0.75, near 1.0.
import {
  W, H, FONT, Defs, f, clamp, lerp, rng, shade, mix, ink, atmos, g, rect, circle, ellipse, line, poly, path, text, tr, st,
  rrPath, gearPath, starPts, glossTop, contact, textW, esc,
} from './ui_style.js';

export const X0 = -480, X1 = 2400, SW = X1 - X0;
const SWM = 2.2; // mid-layer outline width (buildings)
const SWN = 3.2; // near-layer outline width (props)

// ---------- composition ----------
export function compose(layers, cam = {}) {
  const cx = cam.x || 0, cy = cam.y || 0;
  return layers.map((l) => `<g data-layer="${l.name}" transform="translate(${f(-cx * l.depth)} ${f(-cy * l.depth)})">${l.svg}</g>`).join('');
}
export const wrap = (inner, w = W, h = H) => `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${inner}</svg>`;
/** layers[0] is always the shared <defs> (depth 0) so any subset of layers can be recomposed */
function finish(d, layers, o = {}) {
  const all = [{ name: 'defs', depth: 0, svg: String(d) }, ...layers];
  return { w: W, h: H, layers: all, svg: compose(all, o.cam) };
}

// ---------- generic plastic shapes ----------
/** rounded box with vertical 2-stop gradient, gloss strip and tinted outline */
export function pbox(d, x, y, w, h, fill, o = {}) {
  const r = o.r ?? Math.min(w, h) * 0.08, sw = o.sw ?? SWM;
  let s = path(rrPath(x, y, w, h, r), { fill: d.grad(fill, o.dir || 'v', o.up ?? 0.05, o.down ?? 0.06), stroke: o.stroke ?? (sw ? ink(fill) : 'none'), strokeWidth: sw, strokeLinejoin: 'round' });
  if (o.gloss !== false) s += glossTop(x, y, w, h, { op: o.glossOp ?? 0.32, h: o.glossH, inset: o.glossInset });
  return s;
}
/** union of circles with one outline around the whole blob (clouds, canopies, bushes). lobes [[cx,cy,r],...] */
export function blob(d, lobes, fill, o = {}) {
  const sw = o.sw ?? 0, minY = Math.min(...lobes.map(([, y, r]) => y - r)), maxY = Math.max(...lobes.map(([, y, r]) => y + r));
  const flatY = o.flat; // flat bottom at y
  const grad = o.gradFill || d.lin([[0, shade(fill, o.up ?? 0.06)], [1, shade(fill, -(o.down ?? 0.07))]], [0, minY, 0, flatY ?? maxY], 'userSpaceOnUse');
  const shapes = (extra, fl) => lobes.map(([cx, cy, r]) => circle(cx, cy, r + extra, { fill: fl })).join('') +
    (flatY !== undefined ? rect(Math.min(...lobes.map(([x, , r]) => x - r * 0.75)) - extra, Math.max(...lobes.map(([, y]) => y)) - extra, Math.max(...lobes.map(([x, , r]) => x + r * 0.75)) - Math.min(...lobes.map(([x, , r]) => x - r * 0.75)) + extra * 2, flatY - Math.max(...lobes.map(([, y]) => y)) + extra * 2, { fill: fl, rx: extra }) : '');
  let s = '';
  const clipId = flatY !== undefined ? d.clip(rect(-5000, -5000, 15000, flatY + 5000 + sw)) : null;
  if (sw) s += shapes(sw / 2, o.stroke || ink(fill));
  s += shapes(0, grad);
  // highlight lobes (upper-left light) and gloss
  if (o.hi !== false) {
    const hi = o.hiColor || shade(fill, 0.07);
    s += lobes.filter((_, i) => i % 1 === 0).map(([cx, cy, r]) => circle(cx - r * 0.18, cy - r * 0.2, r * 0.62, { fill: hi, opacity: o.hiOp ?? 0.55 })).join('');
  }
  if (o.shadeBottom) s += lobes.map(([cx, cy, r]) => ellipse(cx + r * 0.05, cy + r * 0.55, r * 0.8, r * 0.35, { fill: shade(fill, -0.09), opacity: 0.5 })).join('');
  if (o.gloss !== false && o.glossArc !== false) {
    const [gx, gy, gr] = lobes.reduce((a, b) => (b[1] - b[2] < a[1] - a[2] ? b : a));
    s += path(`M${f(gx - gr * 0.62)} ${f(gy - gr * 0.25)}A${f(gr * 0.7)} ${f(gr * 0.7)} 0 0 1 ${f(gx - gr * 0.05)} ${f(gy - gr * 0.66)}`, { fill: 'none', ...st('#FFFFFF', Math.max(3, gr * 0.12)), opacity: o.glossOp ?? 0.4 });
  }
  return clipId ? g(s, { clipPath: clipId }) : s;
}
/** puffy toy cloud: no outline, white face with soft blue underside (bible: no line on clouds) */
export function cloud(d, cx, cy, s = 1, seed = 1, o = {}) {
  const R = rng(seed), n = 4 + Math.floor(R() * 2), lobes = [];
  const w = 300 * s;
  for (let i = 0; i < n; i++) {
    const t = i / (n - 1), r = (52 + Math.sin(t * Math.PI) * 46 + R() * 14) * s;
    lobes.push([cx - w / 2 + t * w, cy - Math.sin(t * Math.PI) * 34 * s - r * 0.35, r]);
  }
  const base = o.base || '#FFFFFF', under = o.under || '#C7DDF8';
  const flat = cy + 30 * s;
  let out = blob(d, lobes.map(([x, y, r]) => [x, y + 8 * s, r]), under, { flat: flat + 6 * s, hi: false, gloss: false, up: 0, down: 0.02 });
  out += blob(d, lobes, base, { flat, hi: false, gloss: false, up: 0, down: 0.03, gradFill: d.lin([[0, '#FFFFFF'], [0.7, mix(base, under, 0.15)], [1, mix(base, under, 0.55)]], [0, cy - 120 * s, 0, flat], 'userSpaceOnUse') });
  out += lobes.slice(0, 3).map(([x, y, r]) => ellipse(x - r * 0.15, y - r * 0.35, r * 0.4, r * 0.18, { fill: '#FFFFFF', opacity: 0.9 })).join('');
  return g(out, { opacity: o.op ?? 1 });
}
/** sun with soft halo (screen-blended pool of light) */
export function sun(d, cx, cy, r = 70, o = {}) {
  let s = circle(cx, cy, r * 3.2, { fill: d.rad([[0, o.halo || '#FFF6C8', 0.75], [0.35, o.halo || '#FFF6C8', 0.25], [1, o.halo || '#FFF6C8', 0]]), style: 'mix-blend-mode:screen' });
  for (let i = 0; i < 12; i++) {
    const a = (i * 30 + (o.rot || 0)) * Math.PI / 180;
    s += line(cx + Math.cos(a) * r * 1.35, cy + Math.sin(a) * r * 1.35, cx + Math.cos(a) * r * 1.65, cy + Math.sin(a) * r * 1.65, { ...st('#FFF4C0', r * 0.12), opacity: 0.6 });
  }
  s += circle(cx, cy, r, { fill: d.lin(o.fill || ['#FFF8D6', '#FFE36A', '#FFC93A']) });
  s += circle(cx - r * 0.25, cy - r * 0.25, r * 0.45, { fill: '#FFFFFF', opacity: 0.45 });
  return s;
}
/** round toy tree: trunk + 3-4 lobe canopy with one outline */
export function tree(d, x, base, s = 1, o = {}) {
  const leaf = o.leaf || '#4BC240', trunk = o.trunk || '#9A6238', sw = o.sw ?? SWM;
  const R = rng(o.seed || 3);
  let out = '';
  const tw = 34 * s, th = 150 * s;
  out += pbox(d, x - tw / 2, base - th, tw, th, trunk, { r: tw * 0.35, sw, glossOp: 0.25 });
  const cy = base - th - 70 * s;
  const lobes = [[x - 62 * s, cy + 22 * s, 68 * s], [x + 58 * s, cy + 26 * s, 66 * s], [x, cy - 30 * s, 86 * s], [x + (R() - 0.5) * 30 * s, cy + 40 * s, 70 * s]];
  out += blob(d, lobes, leaf, { sw, hiOp: 0.5 });
  // leaf sparkle bumps
  for (let i = 0; i < 5; i++) out += ellipse(x + (R() - 0.5) * 150 * s, cy + (R() - 0.6) * 100 * s, 12 * s, 7 * s, { fill: shade(leaf, 0.12), opacity: 0.7 });
  return out;
}
export function bush(d, x, base, w, h, color = '#3FAF4A', o = {}) {
  const n = Math.max(2, Math.round(w / (h * 0.9))), lobes = [];
  for (let i = 0; i < n; i++) lobes.push([x + (i + 0.5) * (w / n), base - h * 0.5 - (i % 2) * h * 0.08, h * 0.58]);
  return blob(d, lobes, color, { sw: o.sw ?? SWM, flat: base, hiOp: 0.45 });
}
/** window with white frame, sky-reflecting glass and a glint */
export function win(d, x, y, w, h, o = {}) {
  const frame = o.frame || '#FFFFFF', sw = o.sw ?? SWM, glass = o.glass || ['#D4F0FF', '#8CCBF5', '#6FB6EE'];
  let s = path(rrPath(x - 7, y - 7, w + 14, h + 14, o.r ?? 8), { fill: d.grad(frame, 'v', 0.02, 0.06), stroke: ink(o.wall || '#B8C4D8'), strokeWidth: sw });
  s += path(rrPath(x, y, w, h, (o.r ?? 8) - 3), { fill: d.lin(glass) });
  if (o.lit) s += path(rrPath(x, y, w, h, (o.r ?? 8) - 3), { fill: d.lin(['#FFE9A8', '#FFC35A']), opacity: o.lit });
  s += poly([[x + w * 0.12, y + h], [x + w * 0.5, y], [x + w * 0.68, y], [x + w * 0.3, y + h]], { fill: '#FFFFFF', opacity: o.lit ? 0.2 : 0.45 });
  if (o.cross !== false) { s += rect(x + w / 2 - 3.5, y, 7, h, { fill: frame }); s += rect(x, y + h / 2 - 3.5, w, 7, { fill: frame }); }
  if (o.curtain) {
    const c = o.curtain;
    s += path(`M${f(x)} ${f(y)}H${f(x + w * 0.24)}Q${f(x + w * 0.16)} ${f(y + h * 0.5)} ${f(x + w * 0.08)} ${f(y + h)}H${f(x)}Z`, { fill: d.grad(c), stroke: ink(c), strokeWidth: 1.5 });
    s += path(`M${f(x + w)} ${f(y)}H${f(x + w * 0.76)}Q${f(x + w * 0.84)} ${f(y + h * 0.5)} ${f(x + w * 0.92)} ${f(y + h)}H${f(x + w)}Z`, { fill: d.grad(c), stroke: ink(c), strokeWidth: 1.5 });
  }
  if (o.sill !== false) s += pbox(d, x - 14, y + h + 5, w + 28, 14, frame, { r: 5, sw, glossOp: 0.5, stroke: ink(o.wall || '#B8C4D8') });
  return s;
}
/** front-on gable house. o: { x, base, w, h, body, roof, door, trim, wins:[...], chimney, attic, flatRoof } */
export function house(d, o) {
  const { x, base, w, h, body, roof, door = '#2FA3A0', trim = '#FFFFFF', sw = SWM } = o;
  const by = base - h, ov = 26, rh = o.roofH ?? w * 0.36;
  let s = '';
  if (o.chimney) {
    const cx = x + w * (o.chimney === 'left' ? 0.24 : 0.72);
    s += pbox(d, cx - 26, by - rh * 0.8, 52, rh * 0.8, o.chimneyColor || '#C9725A', { r: 4, sw });
    s += pbox(d, cx - 34, by - rh * 0.8 - 14, 68, 18, shade(o.chimneyColor || '#C9725A', -0.04), { r: 5, sw });
  }
  // body
  s += path(rrPath(x, by, w, h, 6), { fill: d.lin([shade(body, 0.04), shade(body, -0.06)]), stroke: ink(body), strokeWidth: sw });
  s += rect(x + w - w * 0.07, by + 2, w * 0.07 - 2, h - 4, { fill: shade(body, -0.06), opacity: 0.6 }); // subtle shading strip on the far edge
  s += rect(x + 3, by + 2, w * 0.05, h - 4, { fill: '#FFFFFF', opacity: 0.18 }); // lit edge
  // siding lines
  for (let yy = by + 26; yy < base - 8; yy += 26) s += rect(x + 3, yy, w - 6, 2, { fill: shade(body, -0.05), opacity: 0.5 });
  // foundation strip
  s += pbox(d, x - 6, base - 18, w + 12, 18, o.base || '#B9B3C9', { r: 4, sw, gloss: false });
  if (o.flatRoof) {
    s += pbox(d, x - ov, by - 34, w + ov * 2, 38, roof, { r: 8, sw, glossOp: 0.4 });
  } else {
    // gable roof with thick fascia
    const L = [x - ov, by + 4], T = [x + w / 2, by - rh], Rr = [x + w + ov, by + 4];
    const rp = `M${f(L[0])} ${f(L[1])}L${f(T[0])} ${f(T[1])}L${f(Rr[0])} ${f(Rr[1])}Z`;
    s += path(rp, { fill: d.lin([shade(roof, 0.06), shade(roof, -0.07)]), stroke: ink(roof), strokeWidth: sw, strokeLinejoin: 'round' });
    // shingle rows (clipped)
    const cl = d.clip(path(rp));
    let rows = '';
    for (let yy = T[1] + 34; yy < by; yy += 30) rows += rect(x - ov, yy, w + ov * 2, 3, { fill: shade(roof, -0.08), opacity: 0.55 });
    s += g(rows, { clipPath: cl });
    // fascia band along the slopes + gloss on the lit (left) slope
    s += path(`M${f(L[0] - 4)} ${f(L[1] + 2)}L${f(T[0])} ${f(T[1] - 6)}L${f(Rr[0] + 4)} ${f(Rr[1] + 2)}`, { fill: 'none', ...st(shade(roof, -0.12), 14) });
    s += path(`M${f(L[0] - 4)} ${f(L[1] + 2)}L${f(T[0])} ${f(T[1] - 6)}L${f(Rr[0] + 4)} ${f(Rr[1] + 2)}`, { fill: 'none', ...st(ink(roof), sw), strokeWidth: 14 + sw * 2, opacity: 0 });
    s += path(`M${f(lerp(L[0], T[0], 0.12))} ${f(lerp(L[1], T[1], 0.12) - 6)}L${f(lerp(L[0], T[0], 0.86))} ${f(lerp(L[1], T[1], 0.86) - 6)}`, { fill: 'none', ...st('#FFFFFF', 5), opacity: 0.4 });
    if (o.attic) s += win(d, x + w / 2 - 26, by - rh * 0.55, 52, 52, { r: 26, cross: true, sill: false, wall: roof, sw });
  }
  // windows + door
  (o.wins || []).forEach((wn) => { s += win(d, x + wn[0], by + wn[1], wn[2], wn[3], { curtain: wn[4], wall: body, sw, lit: o.lit }); });
  if (o.doorAt !== undefined) {
    const dw = 78, dh = 140, dx = x + o.doorAt - dw / 2, dy = base - 18 - dh;
    s += pbox(d, dx - 16, base - 24, dw + 32, 12, '#D8D2E2', { r: 4, sw, gloss: false });
    s += path(rrPath(dx - 7, dy - 7, dw + 14, dh + 10, [40, 40, 4, 4]), { fill: trim, stroke: ink(body), strokeWidth: sw });
    s += path(rrPath(dx, dy, dw, dh, [36, 36, 3, 3]), { fill: d.lin([shade(door, 0.05), shade(door, -0.07)]), stroke: ink(door), strokeWidth: sw });
    s += path(rrPath(dx + 14, dy + 16, dw - 28, 34, [16, 16, 4, 4]), { fill: d.lin(['#D4F0FF', '#8CCBF5']), stroke: ink(door), strokeWidth: 1.5 });
    s += path(rrPath(dx + 12, dy + 64, dw - 24, dh - 80, 6), { fill: 'none', stroke: shade(door, -0.08), strokeWidth: 3 });
    s += circle(dx + dw - 16, dy + dh * 0.58, 6, { fill: d.lin(['#FFE48A', '#E0A520']), stroke: '#8A5A10', strokeWidth: 1.5 });
    s += rect(dx + 6, dy + 8, 5, dh - 20, { fill: '#FFFFFF', opacity: 0.25, rx: 2.5 });
  }
  if (o.garage) {
    const [gx, gw, gh] = o.garage, gy = base - 18 - gh;
    s += path(rrPath(x + gx - 8, gy - 8, gw + 16, gh + 8, 6), { fill: trim, stroke: ink(body), strokeWidth: sw });
    s += path(rrPath(x + gx, gy, gw, gh, 4), { fill: d.lin(['#F4F6FA', '#CBD3E2']), stroke: ink('#CBD3E2'), strokeWidth: sw });
    for (let i = 1; i < 4; i++) s += rect(x + gx + 4, gy + (gh / 4) * i - 2, gw - 8, 4, { fill: '#AAB4C8' });
    s += rect(x + gx + gw / 2 - 22, gy + gh * 0.62, 44, 7, { rx: 3.5, fill: '#7A86A0' });
  }
  return s;
}
export function fence(d, x0, x1, base, h = 64, color = '#FFFFFF', o = {}) {
  const sw = o.sw ?? SWM, pw = 22, gap = 12;
  let s = pbox(d, x0, base - h * 0.72, x1 - x0, 12, shade(color, -0.04), { r: 4, sw, gloss: false });
  s += pbox(d, x0, base - h * 0.32, x1 - x0, 12, shade(color, -0.04), { r: 4, sw, gloss: false });
  for (let xx = x0 + 4; xx < x1 - pw; xx += pw + gap) {
    s += path(`M${f(xx)} ${f(base)}V${f(base - h + 10)}L${f(xx + pw / 2)} ${f(base - h)}L${f(xx + pw)} ${f(base - h + 10)}V${f(base)}Z`, { fill: d.grad(color, 'v', 0.0, 0.08), stroke: ink(color), strokeWidth: sw, strokeLinejoin: 'round' });
    s += rect(xx + 4, base - h + 14, 4, h - 22, { fill: '#FFFFFF', opacity: 0.6, rx: 2 });
  }
  return s;
}
/** 4-point twinkle */
export function twinkle(x, y, r, color = '#FFFFFF', op = 1) {
  return path(`M${f(x)} ${f(y - r)}Q${f(x + r * 0.16)} ${f(y - r * 0.16)} ${f(x + r)} ${f(y)}Q${f(x + r * 0.16)} ${f(y + r * 0.16)} ${f(x)} ${f(y + r)}Q${f(x - r * 0.16)} ${f(y + r * 0.16)} ${f(x - r)} ${f(y)}Q${f(x - r * 0.16)} ${f(y - r * 0.16)} ${f(x)} ${f(y - r)}Z`, { fill: color, opacity: op });
}
function mailbox(d, x, base, color = '#3D7FEA', label, o = {}) {
  const sw = o.sw ?? SWN;
  let s = contact(x, base + 2, 46, 9, 0.25);
  s += pbox(d, x - 8, base - 120, 16, 120, '#8A6A4A', { r: 4, sw });
  s += path(`M${f(x - 46)} ${f(base - 116)}V${f(base - 160)}A46 34 0 0 1 ${f(x + 46)} ${f(base - 160)}V${f(base - 116)}Z`, { fill: d.grad(color), stroke: ink(color), strokeWidth: sw, strokeLinejoin: 'round' });
  s += path(`M${f(x - 34)} ${f(base - 170)}A36 24 0 0 1 ${f(x + 10)} ${f(base - 188)}`, { fill: 'none', ...st('#FFFFFF', 5), opacity: 0.45 });
  s += pbox(d, x + 40, base - 178, 10, 44, '#FF4A3D', { r: 3, sw: 2 });
  s += pbox(d, x + 26, base - 184, 32, 16, '#FF4A3D', { r: 4, sw: 2 });
  if (label) s += text(x, base - 128, esc(label), { fontFamily: FONT.ui, fontWeight: 900, fontSize: 18, fill: '#FFFFFF', textAnchor: 'middle', letterSpacing: 1 });
  return s;
}
function hydrant(d, x, base, sw = SWN) {
  const c = '#F2443A';
  let s = contact(x, base + 2, 40, 8, 0.25);
  s += pbox(d, x - 24, base - 96, 48, 96, c, { r: 10, sw });
  s += pbox(d, x - 32, base - 104, 64, 16, shade(c, -0.03), { r: 6, sw });
  s += path(`M${f(x - 24)} ${f(base - 104)}A24 22 0 0 1 ${f(x + 24)} ${f(base - 104)}Z`, { fill: d.grad(c), stroke: ink(c), strokeWidth: sw });
  s += pbox(d, x - 42, base - 74, 18, 22, shade(c, -0.03), { r: 5, sw });
  s += pbox(d, x + 24, base - 74, 18, 22, shade(c, -0.03), { r: 5, sw });
  s += circle(x, base - 58, 10, { fill: shade(c, -0.08), stroke: ink(c), strokeWidth: 2 });
  return s;
}
function lamp(d, x, base, sw = SWN, o = {}) {
  const c = o.color || '#3E4A70';
  let s = contact(x, base + 2, 34, 7, 0.25);
  s += pbox(d, x - 9, base - 460, 18, 460, c, { r: 6, sw });
  s += pbox(d, x - 22, base - 30, 44, 30, c, { r: 6, sw });
  s += path(`M${f(x)} ${f(base - 456)}Q${f(x)} ${f(base - 500)} ${f(x + 60)} ${f(base - 500)}`, { fill: 'none', ...st(ink(c), 18) });
  s += path(`M${f(x)} ${f(base - 456)}Q${f(x)} ${f(base - 500)} ${f(x + 60)} ${f(base - 500)}`, { fill: 'none', ...st(c, 12) });
  s += path(`M${f(x + 36)} ${f(base - 500)}H${f(x + 96)}L${f(x + 86)} ${f(base - 474)}H${f(x + 46)}Z`, { fill: d.grad(c), stroke: ink(c), strokeWidth: sw, strokeLinejoin: 'round' });
  s += ellipse(x + 66, base - 472, 18, 6, { fill: o.on ? '#FFF2B0' : '#E8EEF8', stroke: ink(c), strokeWidth: 2 });
  if (o.on) s += circle(x + 66, base - 460, 90, { fill: d.rad([[0, '#FFE9A0', 0.6], [1, '#FFE9A0', 0]]), style: 'mix-blend-mode:screen' });
  return s;
}
function bin(d, x, base, color, sw = SWN) {
  let s = contact(x, base + 2, 44, 8, 0.25);
  s += path(`M${f(x - 36)} ${f(base - 120)}H${f(x + 36)}L${f(x + 30)} ${f(base)}H${f(x - 30)}Z`, { fill: d.grad(color), stroke: ink(color), strokeWidth: sw, strokeLinejoin: 'round' });
  s += pbox(d, x - 42, base - 134, 84, 18, shade(color, -0.03), { r: 6, sw });
  s += rect(x - 26, base - 108, 6, 92, { fill: '#FFFFFF', opacity: 0.3, rx: 3 });
  s += circle(x + 22, base - 6, 9, { fill: '#2A2E40', stroke: '#111', strokeWidth: 1 });
  return s;
}
function gnome(d, x, base, sw = SWM) {
  let s = contact(x, base + 2, 26, 6, 0.25);
  s += path(`M${f(x - 22)} ${f(base)}Q${f(x - 24)} ${f(base - 40)} ${f(x)} ${f(base - 44)}Q${f(x + 24)} ${f(base - 40)} ${f(x + 22)} ${f(base)}Z`, { fill: d.grad('#3D7FEA'), stroke: ink('#3D7FEA'), strokeWidth: sw });
  s += path(`M${f(x - 18)} ${f(base - 36)}Q${f(x)} ${f(base - 6)} ${f(x + 18)} ${f(base - 36)}Q${f(x)} ${f(base - 30)} ${f(x - 18)} ${f(base - 36)}Z`, { fill: '#FFFFFF', stroke: ink('#FFFFFF'), strokeWidth: 1.5 });
  s += circle(x, base - 48, 12, { fill: '#F6D3BE', stroke: ink('#F6D3BE'), strokeWidth: sw });
  s += path(`M${f(x - 16)} ${f(base - 52)}L${f(x + 4)} ${f(base - 104)}L${f(x + 16)} ${f(base - 52)}Z`, { fill: d.grad('#F2443A'), stroke: ink('#F2443A'), strokeWidth: sw, strokeLinejoin: 'round' });
  s += circle(x + 1, base - 46, 4, { fill: '#F08F8F' });
  return s;
}
function sign(d, x, base, lines, o = {}) {
  const sw = o.sw ?? SWM, w = o.w || 170, h = o.h || 80, c = o.color || '#FFFFFF';
  let s = pbox(d, x - 6, base - 130, 12, 130, '#9A6238', { r: 4, sw });
  s += pbox(d, x - w / 2, base - 130 - h + 20, w, h, c, { r: 10, sw, stroke: ink(o.ink || '#8090B0') });
  lines.forEach((ln, i) => { s += text(x, base - 130 - h + 20 + 32 + i * 26, esc(ln), { fontFamily: FONT.ui, fontWeight: 900, fontSize: 21, fill: o.textColor || '#E5303D', textAnchor: 'middle' }); });
  return s;
}
/** gear wallpaper motif (our brand motif instead of studs): small gears at +3% L */
function gearPattern(d, color, size = 90, op = 1) {
  const c = shade(color, 0.03), c2 = shade(color, -0.025);
  return d.pattern(size, size, path(gearPath(size * 0.25, size * 0.25, size * 0.14, size * 0.1, 8, 0, 0.5), { fill: c, opacity: op }) + circle(size * 0.75, size * 0.75, size * 0.045, { fill: c2, opacity: op }));
}

// ======================================================================================
// STREET (sunny day)
// ======================================================================================
export function street(o = {}) {
  const d = new Defs();
  const base = 704, lawnY = 698, walkY = 806, curbY = 864, roadY = 880;
  const sky = o.sky || ['#1E7BF6', '#3A97FA', '#8DCDFC'];
  // --- sky (depth 0.08)
  let skyL = rect(X0, -200, SW, 940, { fill: d.lin([[0, sky[0]], [0.55, sky[1]], [1, sky[2]]], [0, -200, 0, 740], 'userSpaceOnUse') });
  skyL += sun(d, 300, 150, 66);
  skyL += cloud(d, -120, 170, 0.8, 11) + cloud(d, 720, 120, 1.0, 12) + cloud(d, 1330, 250, 0.7, 13) + cloud(d, 1820, 110, 0.95, 14) + cloud(d, 2280, 230, 0.75, 15) + cloud(d, 470, 330, 0.55, 16, { op: 0.9 });
  // --- far (depth 0.3): hazy hills, far rooftops, water tower; no outlines
  const hz = sky[2];
  let far = '';
  far += path(`M${X0} 600 Q 0 520 420 585 T 1240 570 T 2000 560 T ${X1} 590 V 760 H ${X0} Z`, { fill: d.lin([atmos('#5CC48A', hz, 0.55), atmos('#4FB47E', hz, 0.42)], 'v') });
  const R = rng(7);
  for (let i = 0; i < 26; i++) {
    const hx = X0 + 40 + i * 112 + R() * 30, hw = 70 + R() * 40, hh = 40 + R() * 26, hy = 640 + R() * 16;
    const col = atmos(['#F3B4A0', '#B9A7EE', '#9CC8F7', '#F8E19A', '#A9E3C8'][i % 5], hz, 0.5);
    far += rect(hx, hy - hh, hw, hh + 60, { fill: col });
    far += poly([[hx - 8, hy - hh + 1], [hx + hw / 2, hy - hh - hw * 0.32], [hx + hw + 8, hy - hh + 1]], { fill: atmos(['#E76A5E', '#6E58C8', '#4A78D8', '#3FA27E'][i % 4], hz, 0.5) });
    if (i % 2) far += circle(hx + hw + 18, hy - 10, 26 + R() * 10, { fill: atmos('#3FAF4A', hz, 0.48) });
  }
  // water tower with the town name
  const wt = atmos('#9DB4DA', hz, 0.35);
  far += rect(1500, 470, 8, 150, { fill: atmos('#7B8FB8', hz, 0.4) }) + rect(1600, 470, 8, 150, { fill: atmos('#7B8FB8', hz, 0.4) }) + rect(1550, 480, 8, 140, { fill: atmos('#7B8FB8', hz, 0.4) });
  far += path('M1480 470 Q1480 400 1554 395 Q1628 400 1628 470 Z', { fill: wt }) + rect(1474, 462, 160, 16, { rx: 8, fill: atmos('#7B8FB8', hz, 0.38) });
  far += path('M1500 382 L1554 350 L1608 382 Z', { fill: atmos('#6F86B4', hz, 0.38) });
  far += text(1554, 446, 'PINEWOOD', { fontFamily: FONT.title, fontSize: 22, fill: atmos('#FFFFFF', hz, 0.15), textAnchor: 'middle', letterSpacing: 1 });
  far += path(`M${X0} 672 Q 300 640 700 668 T 1500 660 T ${X1} 664 V 760 H ${X0} Z`, { fill: atmos('#57C25A', hz, 0.3) });
  // --- mid (depth 0.75): lawns, houses, trees, fences
  let mid = '';
  mid += rect(X0, lawnY, SW, walkY - lawnY + 10, { fill: d.lin(['#63D255', '#4CBF45']) });
  mid += rect(X0, lawnY, SW, 5, { fill: '#8BE07A', opacity: 0.8 });
  // lawn texture: soft darker tufts
  const RL = rng(21);
  for (let i = 0; i < 60; i++) { const tx = X0 + RL() * SW, ty = lawnY + 20 + RL() * 80; if (tx > 1050 && tx < 1700) continue; mid += path(`M${f(tx)} ${f(ty)}l6 -12l6 12l6 -9l5 9`, { fill: 'none', ...st('#42AE3E', 3), opacity: 0.6 }); }
  // houses, back to front
  mid += house(d, { x: -440, base, w: 330, h: 250, body: '#CDB8F4', roof: '#7558D4', door: '#FF8A5C', wins: [[40, 70, 90, 80], [200, 70, 90, 80]], chimney: true });
  mid += tree(d, -60, base + 6, 1.05, { seed: 4 });
  // Sam's house (the family): butter yellow, coral roof, teal door
  mid += house(d, { x: 60, base, w: 410, h: 280, body: '#FFE08F', roof: '#F0645A', door: '#2FA3A0', chimney: 'left', attic: true, doorAt: 300,
    wins: [[40, 70, 110, 96, '#FF9FB2'], [40, 186, 110, 0], [176, 70, 76, 96, '#8AD0FF']] });
  mid += fence(d, 40, 500, walkY - 6, 66, '#FFFFFF');
  mid += gnome(d, 150, walkY - 14);
  mid += tree(d, 560, base + 6, 1.1, { seed: 5, leaf: '#47BE3E' });
  mid += house(d, { x: 640, base, w: 340, h: 250, body: '#9FD0FF', roof: '#3C62C8', door: '#FFC23D', chimney: true, doorAt: 250, wins: [[34, 64, 110, 90, '#FFFFFF']] });
  mid += bush(d, 640, walkY - 4, 150, 64, '#3FAF4A') + bush(d, 860, walkY - 4, 120, 56, '#47B84C');
  // Kevin's modern house + the perfect lawn
  const kx = 1120, kw = 500;
  const stripeW = 46;
  let stripes = '';
  for (let i = -6; i < 24; i++) stripes += poly([[kx - 60 + i * stripeW * 2, walkY + 8], [kx - 60 + i * stripeW * 2 + stripeW, walkY + 8], [kx - 60 + i * stripeW * 2 + stripeW + 70, lawnY], [kx - 60 + i * stripeW * 2 + 70, lawnY]], { fill: '#7CE85F' });
  const lawnClip = d.clip(rect(kx - 70, lawnY, kw + 150, walkY - lawnY + 8));
  mid += rect(kx - 70, lawnY, kw + 150, walkY - lawnY + 8, { fill: d.lin(['#5EE04E', '#45D23E']) });
  mid += g(stripes, { clipPath: lawnClip, opacity: 0.6 });
  mid += rect(kx - 70, walkY - 2, kw + 150, 8, { fill: '#E9EEF5', stroke: ink('#E9EEF5'), strokeWidth: 1.5 }); // crisp edging
  mid += house(d, { x: kx, base, w: kw, h: 300, body: '#F3F6FA', roof: '#3A4766', door: '#3A4766', flatRoof: true, trim: '#FFFFFF', base: '#9AA6BE', doorAt: 400,
    wins: [[40, 60, 200, 110], [270, 60, 80, 110]], garage: [36, 190, 92] });
  // perfect cube hedges (Kevin trims them with a ruler)
  for (let i = 0; i < 4; i++) mid += pbox(d, kx + 20 + i * 118, base - 2 - 58 + 40, 92, 58, '#2FAE55', { r: 10, sw: SWM, glossOp: 0.35 });
  mid += sign(d, kx + 430, walkY - 18, ['KEEP OFF', 'THE GRASS'], { w: 150, h: 76 });
  // twinkles over the perfect lawn
  [[kx + 60, 760, 14], [kx + 250, 740, 10], [kx + 380, 782, 12], [kx + 520, 748, 9], [kx + 150, 790, 8]].forEach(([tx, ty, r]) => { mid += twinkle(tx, ty, r, '#FFFFFF', 0.95); });
  mid += tree(d, 1730, base + 6, 1.0, { seed: 9, leaf: '#4BC240' });
  mid += house(d, { x: 1830, base, w: 380, h: 270, body: '#FFC4A6', roof: '#8C5BE0', door: '#3D7FEA', chimney: true, attic: true, doorAt: 80, wins: [[160, 70, 90, 90, '#FFE08A'], [270, 70, 90, 90, '#FFE08A']] });
  mid += bush(d, 1990, walkY - 4, 200, 60, '#3FAF4A');
  mid += house(d, { x: 2270, base, w: 300, h: 240, body: '#A9E8CF', roof: '#2E9C7A', wins: [[40, 60, 90, 80]] });
  // --- near (depth 1.0): sidewalk, curb, road, street props
  let near = '';
  near += rect(X0, walkY, SW, curbY - walkY, { fill: d.lin(['#E6EBF2', '#CFD6E2']) });
  for (let xx = X0; xx < X1; xx += 150) near += rect(xx, walkY + 4, 3, curbY - walkY - 6, { fill: '#B7C0D0' });
  near += rect(X0, walkY, SW, 4, { fill: '#FFFFFF', opacity: 0.8 });
  near += rect(X0, curbY, SW, roadY - curbY, { fill: d.lin(['#C3CBD9', '#A7B1C4']) });
  near += rect(X0, curbY, SW, 4, { fill: '#F2F5FA' });
  near += rect(X0, roadY, SW, H - roadY + 40, { fill: d.lin([[0, '#4E5468'], [0.1, '#585E74'], [1, '#474C5F']], [0, roadY, 0, H + 40], 'userSpaceOnUse') });
  near += rect(X0, roadY, SW, 8, { fill: '#363A4A', opacity: 0.7 });
  for (let xx = X0 + 30; xx < X1; xx += 240) near += path(rrPath(xx, 990, 130, 16, 8), { fill: '#FFD23F' }) + rect(xx + 10, 992, 110, 4, { rx: 2, fill: '#FFF1A8', opacity: 0.8 });
  near += ellipse(330, 1046, 90, 18, { fill: '#3E4354' }) + ellipse(330, 1043, 76, 13, { fill: 'none', stroke: '#5E6478', strokeWidth: 3 });
  near += mailbox(d, 470, walkY + 30, '#3D7FEA', 'SAM') + mailbox(d, 1660, walkY + 30, '#2B3550', 'KEVIN');
  near += lamp(d, 880, walkY + 34);
  near += bin(d, -200, walkY + 40, '#2FAE55') + bin(d, -110, walkY + 40, '#3D7FEA');
  near += hydrant(d, 2120, walkY + 36);
  return finish(d, [
    { name: 'sky', depth: 0.08, svg: skyL },
    { name: 'far', depth: 0.3, svg: far },
    { name: 'mid', depth: 0.75, svg: mid },
    { name: 'near', depth: 1.0, svg: near },
  ], o);
}

// ======================================================================================
// BEDROOM at 2:13 AM (moonlight + phone glow)
// ======================================================================================
export function bedroom(o = {}) {
  const d = new Defs();
  const floorY = 800, wainY = 600;
  const wall = '#4C3E84', wallLo = '#3E3373';
  // --- far: the window view (night sky, moon, stars, sleeping houses)
  const wx = 1250, wy = 110, ww = 470, wh = 420;
  let far = '';
  far += rect(wx, wy, ww, wh, { fill: d.lin(['#141B4A', '#24306E', '#3A4690']) });
  const RS = rng(31);
  for (let i = 0; i < 26; i++) far += twinkle(wx + RS() * ww, wy + RS() * wh * 0.7, 3 + RS() * 6, '#FFFFFF', 0.5 + RS() * 0.5);
  far += circle(wx + 330, wy + 110, 130, { fill: d.rad([[0, '#BFD0FF', 0.55], [1, '#BFD0FF', 0]]) });
  far += path(`M${wx + 360} ${wy + 50}A62 62 0 1 0 ${wx + 392} ${wy + 150}A50 50 0 1 1 ${wx + 360} ${wy + 50}Z`, { fill: d.lin(['#FFFBE6', '#FFE9A6']) });
  far += path(`M${wx} ${wy + 330} Q ${wx + 120} ${wy + 290} ${wx + 240} ${wy + 320} T ${wx + ww} ${wy + 300} V ${wy + wh} H ${wx} Z`, { fill: '#2A2F6A' });
  for (let i = 0; i < 4; i++) {
    const hx = wx + 30 + i * 118, hy = wy + 345 + (i % 2) * 10;
    far += rect(hx, hy, 80, 70, { fill: '#30387A' }) + poly([[hx - 8, hy], [hx + 40, hy - 30], [hx + 88, hy]], { fill: '#262C64' });
    far += rect(hx + 28, hy + 22, 22, 20, { fill: i === 2 ? '#FFD36A' : '#3E4890', rx: 3 });
  }
  // --- mid: the room shell and furniture
  let mid = '';
  mid += rect(X0, -40, SW, wainY + 40, { fill: d.lin([shade(wall, 0.02), wallLo]) });
  mid += rect(X0, -40, SW, wainY + 40, { fill: gearPattern(d, wall, 110) });
  mid += rect(X0, wainY, SW, floorY - wainY, { fill: d.lin(['#38488E', '#2E3C7C']) });
  for (let xx = X0; xx < X1; xx += 70) mid += rect(xx, wainY + 16, 4, floorY - wainY - 30, { fill: '#2A3670', opacity: 0.8 });
  mid += pbox(d, X0, wainY - 10, SW, 22, '#5A6BB4', { r: 4, sw: 0, glossOp: 0.3 });
  mid += rect(X0, floorY - 24, SW, 24, { fill: '#5A6BB4' }) + rect(X0, floorY - 24, SW, 4, { fill: '#8A9AD8', opacity: 0.5 });
  // floor planks
  mid += rect(X0, floorY, SW, H - floorY + 40, { fill: d.lin(['#3A3468', '#2A2652']) });
  for (let yy = floorY + 40, k = 0; yy < H + 40; yy += 46 + k * 8, k++) {
    mid += rect(X0, yy, SW, 3, { fill: '#221E44', opacity: 0.7 });
    for (let xx = X0 + (k % 2) * 120; xx < X1; xx += 240) mid += rect(xx, yy - 46 - k * 6, 3, 46 + k * 6, { fill: '#221E44', opacity: 0.45 });
  }
  // window frame + curtains + sill
  mid += path(rrPath(wx - 22, wy - 22, ww + 44, wh + 44, 14), { fill: 'none', stroke: d.lin(['#8D9BE0', '#6070C0']), strokeWidth: 28 });
  mid += path(rrPath(wx - 36, wy - 36, ww + 72, wh + 72, 18), { fill: 'none', stroke: ink('#6070C0'), strokeWidth: 3 });
  mid += path(rrPath(wx - 8, wy - 8, ww + 16, wh + 16, 8), { fill: 'none', stroke: ink('#6070C0'), strokeWidth: 3 });
  mid += rect(wx + ww / 2 - 7, wy, 14, wh, { fill: '#7383CF' }) + rect(wx, wy + wh * 0.45, ww, 14, { fill: '#7383CF' });
  mid += poly([[wx + 40, wy + wh], [wx + 170, wy], [wx + 220, wy], [wx + 90, wy + wh]], { fill: '#FFFFFF', opacity: 0.06 });
  mid += pbox(d, wx - 60, wy + wh + 18, ww + 120, 28, '#8D9BE0', { r: 8, sw: SWM, glossOp: 0.4 });
  const cur = '#7A3E9E';
  for (const [cxp, flip] of [[wx - 70, 1], [wx + ww + 70, -1]]) {
    const cw = 120 * flip;
    mid += path(`M${f(cxp - cw * 0.55)} ${wy - 50}H${f(cxp + cw * 0.5)}Q${f(cxp + cw * 0.2)} ${wy + 220} ${f(cxp + cw * 0.62)} ${wy + wh + 70}H${f(cxp - cw * 0.55)}Z`, { fill: d.lin([shade(cur, 0.04), shade(cur, -0.08)], 'h'), stroke: ink(cur), strokeWidth: SWM, strokeLinejoin: 'round' });
    for (let k = 1; k < 4; k++) mid += path(`M${f(cxp - cw * 0.55 + cw * 0.27 * k)} ${wy - 40}Q${f(cxp - cw * 0.55 + cw * 0.27 * k - cw * 0.06)} ${wy + 200} ${f(cxp - cw * 0.55 + cw * 0.3 * k)} ${wy + wh + 60}`, { fill: 'none', ...st(shade(cur, -0.08), 4), opacity: 0.6 });
  }
  mid += pbox(d, wx - 170, wy - 62, ww + 340, 18, '#9A7AC8', { r: 9, sw: SWM });
  // string lights across the top (warm motivated glows)
  let lights = path(`M${X0} 40 Q 300 120 700 60 T 1250 70`, { fill: 'none', ...st('#2A2450', 3) });
  const lp = [[-300, 64], [-120, 92], [60, 104], [240, 102], [420, 88], [600, 70], [780, 62], [960, 72], [1140, 74]];
  lp.forEach(([lx, ly], i) => {
    const c = ['#FFD36A', '#FF8FB0', '#7FE0FF', '#B7FF8A'][i % 4];
    lights += circle(lx, ly + 16, 44, { fill: d.rad([[0, c, 0.55], [1, c, 0]]), style: 'mix-blend-mode:screen' });
    lights += rect(lx - 5, ly, 10, 10, { fill: '#2A2450', rx: 2 }) + ellipse(lx, ly + 18, 9, 13, { fill: d.lin(['#FFFFFF', c]), stroke: ink(c), strokeWidth: 1.5 });
  });
  mid += lights;
  // poster: our own rocket poster
  const px = 80, py = 150;
  mid += pbox(d, px, py, 230, 300, '#F2F4FF', { r: 10, sw: SWM, gloss: false, stroke: ink('#8A90C8') });
  mid += rect(px + 14, py + 14, 202, 272, { fill: d.lin(['#2C3B8E', '#5A3FA8']), rx: 6 });
  for (let i = 0; i < 9; i++) mid += twinkle(px + 30 + ((i * 53) % 180), py + 40 + ((i * 89) % 200), 5, '#FFFFFF', 0.8);
  mid += path(`M${px + 115} ${py + 60}C${px + 140} ${py + 90} ${px + 145} ${py + 150} ${px + 135} ${py + 200}H${px + 95}C${px + 85} ${py + 150} ${px + 90} ${py + 90} ${px + 115} ${py + 60}Z`, { fill: d.lin(['#FFFFFF', '#D6DCF2']), stroke: '#2A2450', strokeWidth: 2.5 });
  mid += circle(px + 115, py + 120, 14, { fill: '#7FD0FF', stroke: '#2A2450', strokeWidth: 2.5 });
  mid += path(`M${px + 95} ${py + 170}L${px + 72} ${py + 214}H${px + 98}Z M${px + 135} ${py + 170}L${px + 158} ${py + 214}H${px + 132}Z`, { fill: '#FF7A3D', stroke: '#2A2450', strokeWidth: 2.5, strokeLinejoin: 'round' });
  mid += path(`M${px + 102} ${py + 204}Q${px + 115} ${py + 260} ${px + 128} ${py + 204}Z`, { fill: '#FFC23D' });
  mid += text(px + 115, py + 268, 'GO FURTHER', { fontFamily: FONT.title, fontSize: 24, fill: '#FFD36A', textAnchor: 'middle' });
  // shelf with trophies and a gear-logo game box
  mid += pbox(d, 380, 250, 300, 20, '#9A6CC8', { r: 6, sw: SWM });
  mid += pbox(d, 400, 196, 40, 54, '#FFC23D', { r: 8, sw: SWM }) + pbox(d, 408, 176, 24, 24, '#FFC23D', { r: 12, sw: SWM });
  mid += pbox(d, 460, 170, 70, 80, '#FF7A3D', { r: 8, sw: SWM });
  mid += path(gearPath(495, 208, 22, 16, 8, 0, 0.5), { fill: '#FFFFFF' }) + circle(495, 208, 7, { fill: '#FF7A3D' });
  mid += pbox(d, 550, 206, 26, 44, '#3D7FEA', { r: 5, sw: SWM }) + pbox(d, 580, 200, 26, 50, '#25BE66', { r: 5, sw: SWM }) + pbox(d, 610, 210, 26, 40, '#FF5596', { r: 5, sw: SWM });
  // bed (headboard against the wall), blanket with a gear pattern
  const bx = 470, bw = 720, bTop = 470;
  mid += path(rrPath(bx, bTop, bw, 300, [60, 60, 6, 6]), { fill: d.lin(['#6A55B0', '#4E3E92']), stroke: ink('#4E3E92'), strokeWidth: SWM });
  mid += path(rrPath(bx + 30, bTop + 30, bw - 60, 200, [40, 40, 6, 6]), { fill: d.lin(['#5C4AA2', '#4A3A8A']), stroke: ink('#4E3E92'), strokeWidth: 2 });
  mid += path(`M${bx + 70} ${bTop + 18}Q${bx + bw / 2} ${bTop - 16} ${bx + bw - 70} ${bTop + 18}`, { fill: 'none', ...st('#FFFFFF', 6), opacity: 0.25 });
  mid += pbox(d, bx - 16, bTop + 40, 34, 400, '#5B4AA0', { r: 14, sw: SWM }) + pbox(d, bx + bw - 18, bTop + 40, 34, 400, '#5B4AA0', { r: 14, sw: SWM });
  mid += circle(bx + 1, bTop + 36, 24, { fill: d.grad('#7A66C4'), stroke: ink('#5B4AA0'), strokeWidth: SWM }) + circle(bx + bw - 1, bTop + 36, 24, { fill: d.grad('#7A66C4'), stroke: ink('#5B4AA0'), strokeWidth: SWM });
  // pillows
  mid += path(rrPath(bx + 70, bTop + 150, 260, 110, 50), { fill: d.lin(['#E8ECFF', '#B9C2EC']), stroke: ink('#B9C2EC'), strokeWidth: SWM });
  mid += path(rrPath(bx + 390, bTop + 150, 260, 110, 50), { fill: d.lin(['#E8ECFF', '#B9C2EC']), stroke: ink('#B9C2EC'), strokeWidth: SWM });
  // mattress + blanket
  mid += pbox(d, bx + 12, bTop + 250, bw - 24, 60, '#DCE2FA', { r: 18, sw: SWM, glossOp: 0.3 });
  const bl = '#2F4FB8';
  const blanket = `M${bx - 4} ${bTop + 300}Q${bx + bw / 2} ${bTop + 272} ${bx + bw + 4} ${bTop + 300}L${bx + bw + 30} ${floorY + 90}Q${bx + bw / 2} ${floorY + 110} ${bx - 30} ${floorY + 90}Z`;
  mid += path(blanket, { fill: d.lin([shade(bl, 0.05), shade(bl, -0.06)]), stroke: ink(bl), strokeWidth: SWM, strokeLinejoin: 'round' });
  mid += g(rect(bx - 40, bTop + 260, bw + 80, 400, { fill: d.pattern(120, 100, path(gearPath(30, 30, 16, 11, 8, 0, 0.5), { fill: '#5A7AE0', opacity: 0.55 }) + circle(30, 30, 5, { fill: bl }) + twinkle(90, 76, 8, '#7F9CF0', 0.55)) }), { clipPath: d.clip(path(blanket)) });
  mid += path(`M${bx + 10} ${bTop + 300}Q${bx + bw / 2} ${bTop + 274} ${bx + bw - 10} ${bTop + 300}`, { fill: 'none', ...st('#FFFFFF', 8), opacity: 0.3 });
  mid += path(`M${bx + 20} ${bTop + 330}Q${bx + bw / 2} ${bTop + 306} ${bx + bw - 20} ${bTop + 330}`, { fill: 'none', ...st('#8FA8FF', 22), opacity: 0.5 });
  // nightstand + alarm clock 2:13 (red glow)
  const nx = 220, ny = 640;
  mid += pbox(d, nx, ny, 210, 200, '#6A58B4', { r: 12, sw: SWM });
  mid += pbox(d, nx + 16, ny + 30, 178, 66, '#7A68C4', { r: 10, sw: 2 }) + pbox(d, nx + 16, ny + 110, 178, 66, '#7A68C4', { r: 10, sw: 2 });
  mid += circle(nx + 105, ny + 63, 9, { fill: '#C8B8F0', stroke: ink('#7A68C4'), strokeWidth: 2 }) + circle(nx + 105, ny + 143, 9, { fill: '#C8B8F0', stroke: ink('#7A68C4'), strokeWidth: 2 });
  mid += circle(nx + 105, ny - 40, 120, { fill: d.rad([[0, '#FF3B5C', 0.45], [1, '#FF3B5C', 0]]), style: 'mix-blend-mode:screen' });
  mid += pbox(d, nx + 34, ny - 86, 142, 86, '#3A2E6A', { r: 18, sw: SWN });
  mid += rect(nx + 50, ny - 72, 110, 54, { rx: 10, fill: '#160C24' });
  mid += text(nx + 105, ny - 31, '2:13', { fontFamily: FONT.title, fontSize: 44, fill: '#FF4A5E', textAnchor: 'middle', filter: d.glow('#FF2A4A', 5, 0.9), letterSpacing: 2 });
  mid += circle(nx + 160, ny - 92, 9, { fill: '#5A4A90', stroke: ink('#3A2E6A'), strokeWidth: 2 }) + circle(nx + 50, ny - 92, 9, { fill: '#5A4A90', stroke: ink('#3A2E6A'), strokeWidth: 2 });
  // headphones stand? -> a glass of water + headphones charging
  mid += pbox(d, nx + 6, ny - 52, 22, 52, '#9FD8FF', { r: 4, sw: 2, glossOp: 0.6 });
  // desk on the far right corner with a sleeping monitor (standby LED)
  mid += pbox(d, 1800, 560, 520, 26, '#7A62C0', { r: 8, sw: SWM }) + pbox(d, 1830, 586, 26, 260, '#6A58B4', { r: 8, sw: SWM });
  mid += pbox(d, 1880, 360, 300, 190, '#2A2450', { r: 14, sw: SWN }) + rect(1896, 376, 268, 158, { rx: 8, fill: d.lin(['#1C1838', '#2A2552']) });
  mid += pbox(d, 2010, 548, 40, 14, '#2A2450', { r: 4, sw: 2 }) + circle(2160, 520, 4, { fill: '#7FE0FF', filter: d.glow('#7FE0FF', 3, 1) });
  // round rug (moonlit) on the floor
  mid += ellipse(1460, 960, 330, 74, { fill: d.lin(['#8A6CD8', '#6A4EB8']), stroke: ink('#6A4EB8'), strokeWidth: SWM });
  mid += ellipse(1460, 960, 250, 52, { fill: 'none', stroke: '#B79CFF', strokeWidth: 6, opacity: 0.7 });
  // --- light pools (screen): moonlight shaft from the window onto the rug, phone glow on the bed
  let light = '';
  light += poly([[wx + 10, wy + wh], [wx + ww - 10, wy + wh], [1840, 1080], [1100, 1080]], { fill: d.lin([[0, '#BFD2FF', 0.3], [1, '#BFD2FF', 0.04]]), style: 'mix-blend-mode:screen' });
  light += ellipse(1460, 960, 300, 62, { fill: d.rad([[0, '#D8E4FF', 0.45], [1, '#D8E4FF', 0]]), style: 'mix-blend-mode:screen' });
  const pgx = o.phone?.x ?? 830, pgy = o.phone?.y ?? 660;
  light += circle(pgx, pgy, 360, { fill: d.rad([[0, '#BFF2FF', 0.62], [0.25, '#8FD8FF', 0.32], [1, '#6FB8FF', 0]]), style: 'mix-blend-mode:screen' });
  // --- near: framing props on the floor (laundry, a ball, comics), darker as they are out of the light
  let near = '';
  near += path(`M-120 ${H + 20}Q-60 960 60 990Q150 940 240 1000Q300 1030 330 ${H + 20}Z`, { fill: d.lin(['#5A4FA0', '#3E3680']), stroke: ink('#3E3680'), strokeWidth: SWN, strokeLinejoin: 'round' });
  near += path('M20 1030Q90 990 170 1018', { fill: 'none', ...st('#7A6FC8', 6), opacity: 0.7 });
  near += path(`M120 ${H + 20}Q150 1000 220 1006Q262 1012 270 ${H + 20}Z`, { fill: d.grad('#FF7A3D'), stroke: ink('#FF7A3D'), strokeWidth: SWN }); // an orange hoodie sleeve in the laundry
  near += circle(1880, 1010, 64, { fill: d.lin(['#F4F6FF', '#C8CEE8']), stroke: ink('#C8CEE8'), strokeWidth: SWN });
  near += path('M1880 948L1856 982L1880 1008L1906 982Z M1820 1000L1846 990 M1940 1000L1914 990', { fill: '#3A3F6A', stroke: '#3A3F6A', strokeWidth: 3, strokeLinejoin: 'round' });
  near += pbox(d, 2040, 1000, 220, 40, '#E5303D', { r: 6, sw: SWN }) + pbox(d, 2060, 966, 200, 36, '#25AEF2', { r: 6, sw: SWN });
  // night grade: a soft vignette (bible: vignette only on night POV/sky shots)
  const vig = rect(X0, -60, SW, H + 120, { fill: d.rad([[0.55, '#120C2E', 0], [1, '#120C2E', 0.5]], 0.5, 0.5, 0.75) });
  return finish(d, [
    { name: 'far', depth: 0.3, svg: far },
    { name: 'mid', depth: 0.75, svg: mid },
    { name: 'light', depth: 0.75, svg: light },
    { name: 'near', depth: 1.0, svg: near },
    { name: 'grade', depth: 0, svg: vig },
  ], o);
}

// ======================================================================================
// KITCHEN in the morning
// ======================================================================================
export function kitchen(o = {}) {
  const d = new Defs();
  const counterY = 640, floorY = 820;
  const wall = '#FFEFD2';
  // --- far: window view (morning sky, sun low, garden)
  const wx = 560, wy = 110, ww = 520, wh = 330;
  let far = '';
  far += rect(wx, wy, ww, wh, { fill: d.lin(['#8FD0FF', '#C8E8FF', '#FFE6B0']) });
  far += sun(d, wx + 150, wy + 210, 46, { halo: '#FFF0C0' });
  far += cloud(d, wx + 380, wy + 80, 0.45, 41);
  far += path(`M${wx} ${wy + 260} Q ${wx + 160} ${wy + 230} ${wx + 300} ${wy + 255} T ${wx + ww} ${wy + 250} V ${wy + wh} H ${wx} Z`, { fill: atmos('#5CC48A', '#C8E8FF', 0.3) });
  far += circle(wx + 420, wy + 240, 46, { fill: atmos('#3FAF4A', '#C8E8FF', 0.25) }) + rect(wx + 414, wy + 270, 12, 60, { fill: atmos('#9A6238', '#C8E8FF', 0.3) });
  far += fence(d, wx, wx + ww, wy + wh, 44, atmos('#FFFFFF', '#C8E8FF', 0.1), { sw: 1.2 });
  // --- mid: walls, tiles, cabinets, counters, fridge, appliances
  let mid = '';
  mid += rect(X0, -40, SW, counterY + 40, { fill: d.lin([shade(wall, 0.01), shade(wall, -0.035)]) });
  // backsplash tiles between the counter and the upper cabinets (mint)
  const tileTop = 380;
  mid += rect(X0, tileTop, SW, counterY - tileTop, { fill: d.lin(['#CFF3E8', '#B8EADB']) });
  mid += rect(X0, tileTop, SW, counterY - tileTop, { fill: d.pattern(64, 52, rect(0, 0, 64, 52, { fill: 'none', stroke: '#9FDCCB', strokeWidth: 3 }) + rect(5, 5, 22, 6, { rx: 3, fill: '#FFFFFF', opacity: 0.55 })) });
  // window frame & sill (cut into the tiles)
  mid += path(rrPath(wx - 18, wy - 18, ww + 36, wh + 36, 14), { fill: 'none', stroke: d.lin(['#FFFFFF', '#E6E9F2']), strokeWidth: 24 });
  mid += path(rrPath(wx - 30, wy - 30, ww + 60, wh + 60, 18), { fill: 'none', stroke: ink('#E6E9F2'), strokeWidth: SWM });
  mid += path(rrPath(wx - 6, wy - 6, ww + 12, wh + 12, 8), { fill: 'none', stroke: ink('#E6E9F2'), strokeWidth: SWM });
  mid += rect(wx + ww / 2 - 6, wy, 12, wh, { fill: '#F4F6FA' });
  mid += poly([[wx + 60, wy + wh], [wx + 190, wy], [wx + 240, wy], [wx + 110, wy + wh]], { fill: '#FFFFFF', opacity: 0.3 });
  // café curtain valance (yellow gingham)
  const val = '#FFC23D';
  mid += path(`M${wx - 40} ${wy - 40}H${wx + ww + 40}V${wy + 20}Q${wx + ww * 0.875 + 20} ${wy + 54} ${wx + ww * 0.75} ${wy + 20}Q${wx + ww * 0.625} ${wy + 54} ${wx + ww * 0.5} ${wy + 20}Q${wx + ww * 0.375} ${wy + 54} ${wx + ww * 0.25} ${wy + 20}Q${wx + ww * 0.125 - 20} ${wy + 54} ${wx - 40} ${wy + 20}Z`, { fill: d.grad(val), stroke: ink(val), strokeWidth: SWM, strokeLinejoin: 'round' });
  mid += path(`M${wx - 30} ${wy - 26}H${wx + ww + 30}`, { fill: 'none', ...st('#FFFFFF', 6), opacity: 0.45 });
  // plant on the sill
  mid += pbox(d, wx + 420, wy + wh - 60, 70, 60, '#F0645A', { r: 10, sw: SWM });
  mid += blob(d, [[wx + 440, wy + wh - 84, 26], [wx + 470, wy + wh - 92, 28], [wx + 455, wy + wh - 116, 24]], '#3FAF4A', { sw: SWM });
  // upper cabinets (teal) left and right of the window
  const cab = '#5BC8B0';
  const upper = (x, w) => {
    let s = pbox(d, x, 60, w, 250, cab, { r: 12, sw: SWM });
    const n = Math.max(1, Math.round(w / 200)), dw = (w - 24 - (n - 1) * 12) / n;
    for (let i = 0; i < n; i++) {
      s += path(rrPath(x + 12 + i * (dw + 12), 76, dw, 218, 10), { fill: d.lin([shade(cab, 0.06), shade(cab, -0.03)]), stroke: shade(cab, -0.1), strokeWidth: 3 });
      s += pbox(d, x + 12 + i * (dw + 12) + (i % 2 ? 14 : dw - 22), 230, 10, 44, '#FFC23D', { r: 5, sw: 2 });
    }
    return s + pbox(d, x - 12, 300, w + 24, 18, shade(cab, -0.05), { r: 6, sw: SWM, gloss: false });
  };
  mid += upper(-460, 420) + upper(0, 460) + upper(1150, 300);
  // wall clock 7:30
  mid += circle(1630, 190, 78, { fill: d.lin(['#FFFFFF', '#E8ECF4']), stroke: ink('#FF7A3D'), strokeWidth: 3 });
  mid += circle(1630, 190, 78, { fill: 'none', stroke: '#FF7A3D', strokeWidth: 12 });
  for (let i = 0; i < 12; i++) { const a = i * Math.PI / 6; mid += circle(1630 + Math.sin(a) * 58, 190 - Math.cos(a) * 58, i % 3 ? 3 : 5, { fill: '#3A4470' }); }
  mid += line(1630, 190, 1630, 240, st('#3A4470', 7)) + line(1630, 190, 1650, 160, st('#3A4470', 9)) + circle(1630, 190, 7, { fill: '#FF7A3D' });
  // lower cabinets + counter
  mid += rect(X0, counterY, SW, floorY - counterY, { fill: d.lin([shade(cab, 0.02), shade(cab, -0.07)]) });
  for (let xx = X0 + 10; xx < X1; xx += 190) {
    mid += path(rrPath(xx, counterY + 48, 170, floorY - counterY - 70, 10), { fill: d.lin([shade(cab, 0.06), shade(cab, -0.04)]), stroke: shade(cab, -0.12), strokeWidth: 3 });
    mid += pbox(d, xx + 60, counterY + 66, 50, 10, '#FFC23D', { r: 5, sw: 2 });
  }
  mid += rect(X0, floorY - 22, SW, 22, { fill: shade(cab, -0.14) });
  const top = '#E2A766';
  mid += pbox(d, X0, counterY - 6, SW, 40, top, { r: 6, sw: SWM, glossOp: 0.45 });
  // sink under the window
  mid += path(rrPath(wx + 90, counterY - 6, 340, 20, 6), { fill: d.lin(['#C9D2E2', '#9AA6BE']), stroke: ink('#9AA6BE'), strokeWidth: 2 });
  mid += path(`M${wx + 250} ${counterY - 6}V${counterY - 90}Q${wx + 250} ${counterY - 120} ${wx + 290} ${counterY - 120}H${wx + 300}V${counterY - 100}`, { fill: 'none', ...st(ink('#C9D2E2'), 22) });
  mid += path(`M${wx + 250} ${counterY - 6}V${counterY - 90}Q${wx + 250} ${counterY - 120} ${wx + 290} ${counterY - 120}H${wx + 300}V${counterY - 100}`, { fill: 'none', ...st('#D9E0EC', 15) });
  mid += path(`M${wx + 246} ${counterY - 20}V${counterY - 88}`, { fill: 'none', ...st('#FFFFFF', 4), opacity: 0.7 });
  // toaster + coffee maker (left counter), fruit bowl (right of sink)
  mid += contact(150, counterY - 4, 90, 8, 0.2);
  mid += pbox(d, 70, counterY - 120, 170, 116, '#E8EDF5', { r: 30, sw: SWM, stroke: ink('#B8C2D6') });
  mid += rect(100, counterY - 126, 40, 12, { rx: 6, fill: '#3A4470' }) + rect(166, counterY - 126, 40, 12, { rx: 6, fill: '#3A4470' });
  mid += pbox(d, 200, counterY - 70, 14, 34, '#3A4470', { r: 5, sw: 1.5 });
  mid += path(`M92 ${counterY - 44}H222`, { ...st('#FFFFFF', 5), opacity: 0.6 });
  mid += contact(380, counterY - 4, 70, 7, 0.2);
  mid += pbox(d, 320, counterY - 200, 130, 196, '#3A4470', { r: 16, sw: SWN });
  mid += pbox(d, 340, counterY - 90, 90, 78, '#B8E4FF', { r: 12, sw: 2, glossOp: 0.6 });
  mid += rect(344, counterY - 52, 82, 36, { rx: 8, fill: '#7A4A2A', opacity: 0.85 });
  mid += circle(385, counterY - 160, 12, { fill: '#2FD27C', filter: d.glow('#2FD27C', 3, 0.8) });
  for (let i = 0; i < 3; i++) mid += path(`M${370 + i * 16} ${counterY - 214}q-12 -20 0 -40q12 -20 0 -40`, { fill: 'none', ...st('#FFFFFF', 5), opacity: 0.5 });
  mid += contact(wx + ww + 120, counterY - 4, 90, 8, 0.2);
  mid += path(`M${wx + ww + 40} ${counterY - 50}H${wx + ww + 200}Q${wx + ww + 190} ${counterY - 4} ${wx + ww + 120} ${counterY - 4}Q${wx + ww + 50} ${counterY - 4} ${wx + ww + 40} ${counterY - 50}Z`, { fill: d.grad('#FF7A3D'), stroke: ink('#FF7A3D'), strokeWidth: SWM });
  mid += circle(wx + ww + 90, counterY - 66, 28, { fill: d.grad('#F2443A'), stroke: ink('#F2443A'), strokeWidth: SWM }) + circle(wx + ww + 140, counterY - 70, 30, { fill: d.grad('#FFC23D'), stroke: ink('#FFC23D'), strokeWidth: SWM });
  mid += path(`M${wx + ww + 60} ${counterY - 80}Q${wx + ww + 120} ${counterY - 140} ${wx + ww + 180} ${counterY - 70}`, { fill: 'none', ...st(ink('#FFE066'), 22) }) + path(`M${wx + ww + 60} ${counterY - 80}Q${wx + ww + 120} ${counterY - 140} ${wx + ww + 180} ${counterY - 70}`, { fill: 'none', ...st('#FFE066', 16) });
  // fridge on the right with magnets, a drawing and Mom's label-maker labels
  const fx = 1500, fy = 250, fw = 300, fh = floorY - fy;
  mid += pbox(d, fx, fy, fw, fh, '#F4F7FC', { r: 30, sw: SWM, stroke: ink('#C9D2E2') });
  mid += rect(fx + 4, fy + 200, fw - 8, 5, { fill: '#C9D2E2' });
  mid += pbox(d, fx + fw - 40, fy + 60, 16, 110, '#C9D2E2', { r: 8, sw: 2 }) + pbox(d, fx + fw - 40, fy + 240, 16, 150, '#C9D2E2', { r: 8, sw: 2 });
  mid += rect(fx + 10, fy + 20, 14, fh - 40, { fill: '#FFFFFF', opacity: 0.8, rx: 7 });
  mid += g(pbox(d, -70, -55, 140, 110, '#FFFFFF', { r: 6, sw: 2, gloss: false, stroke: '#B8C2D6' }) + circle(-20, -8, 20, { fill: '#FFC23D' }) + path('M-50 40L-10 0L20 30L40 10L60 40Z', { fill: '#3FAF4A' }) + rect(10, -30, 40, 20, { fill: '#FF5596', rx: 4 }), { transform: `translate(${fx + 120} ${fy + 320}) rotate(-4)` });
  mid += circle(fx + 120, fy + 262, 10, { fill: '#E5303D', stroke: ink('#E5303D'), strokeWidth: 2 });
  for (const [lx, ly, t] of [[fx + 60, fy + 110, 'FRIDGE'], [fx + 70, fy + 460, 'COLD STUFF']]) {
    const lw = textW(t, 20) + 22;
    mid += rect(lx, ly, lw, 30, { rx: 4, fill: '#1E2140' }) + text(lx + lw / 2, ly + 22, esc(t), { fontFamily: FONT.ui, fontWeight: 900, fontSize: 20, fill: '#FFFFFF', textAnchor: 'middle', letterSpacing: 1 });
  }
  mid += circle(fx + 230, fy + 120, 14, { fill: '#25AEF2', stroke: ink('#25AEF2'), strokeWidth: 2 }) + circle(fx + 200, fy + 150, 12, { fill: '#25BE66', stroke: ink('#25BE66'), strokeWidth: 2 });
  // a label on the toaster too
  mid += rect(110, counterY - 96, 90, 24, { rx: 4, fill: '#1E2140' }) + text(155, counterY - 78, 'TOASTER', { fontFamily: FONT.ui, fontWeight: 900, fontSize: 16, fill: '#FFFFFF', textAnchor: 'middle', letterSpacing: 1 });
  // pendant lamp
  mid += line(1300, -40, 1300, 120, st('#3A4470', 4));
  mid += path('M1240 170Q1240 110 1300 110Q1360 110 1360 170Z', { fill: d.grad('#FF7A3D'), stroke: ink('#FF7A3D'), strokeWidth: SWM });
  mid += ellipse(1300, 172, 38, 8, { fill: '#FFF3C8' });
  // floor: checker tiles with fake perspective (rows grow toward the camera)
  mid += rect(X0, floorY, SW, H - floorY + 40, { fill: '#F3E6CF' });
  let yy = floorY, rh = 44, k = 0;
  while (yy < H + 40) {
    for (let xx = X0 - (k % 2) * 60; xx < X1; xx += 240) mid += rect(xx, yy, 120, rh, { fill: '#9ED9C8' });
    yy += rh; rh *= 1.25; k++;
  }
  mid += rect(X0, floorY, SW, H - floorY + 40, { fill: d.lin([[0, '#5A4A30', 0.18], [0.3, '#5A4A30', 0], [1, '#5A4A30', 0]]) });
  // --- light: sun rays through the window (screen)
  let light = '';
  light += poly([[wx + 40, wy + 40], [wx + 300, wy + 40], [wx + 900, H + 40], [wx + 120, H + 40]], { fill: d.lin([[0, '#FFF0B0', 0.4], [1, '#FFF0B0', 0.0]]), style: 'mix-blend-mode:screen' });
  light += poly([[wx + 330, wy + 40], [wx + 440, wy + 40], [wx + 1180, H + 40], [wx + 920, H + 40]], { fill: d.lin([[0, '#FFF0B0', 0.3], [1, '#FFF0B0', 0.0]]), style: 'mix-blend-mode:screen' });
  light += circle(wx + 160, wy + 220, 260, { fill: d.rad([[0, '#FFE9A0', 0.35], [1, '#FFE9A0', 0]]), style: 'mix-blend-mode:screen' });
  // --- near: breakfast table with a gingham cloth (characters sit behind it)
  let near = '';
  const ty = o.tableY ?? 900;
  const cloth = '#F25A5A';
  near += pbox(d, 260, ty + 120, 34, 200, '#B97A48', { r: 10, sw: SWN }) + pbox(d, 1626, ty + 120, 34, 200, '#B97A48', { r: 10, sw: SWN });
  const tablePath = `M200 ${ty}H1720Q1760 ${ty} 1760 ${ty + 40}L1770 ${ty + 160}Q1700 ${ty + 190} 1640 ${ty + 160}Q1560 ${ty + 190} 1480 ${ty + 160}Q1400 ${ty + 190} 1320 ${ty + 160}Q1240 ${ty + 190} 1160 ${ty + 160}Q1080 ${ty + 190} 1000 ${ty + 160}Q920 ${ty + 190} 840 ${ty + 160}Q760 ${ty + 190} 680 ${ty + 160}Q600 ${ty + 190} 520 ${ty + 160}Q440 ${ty + 190} 360 ${ty + 160}Q280 ${ty + 190} 200 ${ty + 160}L160 ${ty + 160}L150 ${ty + 40}Q150 ${ty} 200 ${ty}Z`;
  near += path(tablePath, { fill: d.lin(['#FFFFFF', '#F2E8EE']), stroke: ink(cloth), strokeWidth: SWN, strokeLinejoin: 'round' });
  near += g(rect(140, ty - 10, 1660, 220, { fill: d.pattern(80, 80, rect(0, 0, 40, 80, { fill: cloth, opacity: 0.45 }) + rect(0, 0, 80, 40, { fill: cloth, opacity: 0.45 })) }), { clipPath: d.clip(path(tablePath)) });
  near += path(`M200 ${ty + 6}H1720`, { ...st('#FFFFFF', 6), opacity: 0.6 });
  // breakfast props on the table
  near += contact(520, ty + 26, 90, 10, 0.25) + contact(1180, ty + 30, 70, 9, 0.25) + contact(1460, ty + 26, 60, 9, 0.25);
  near += pbox(d, 440, ty - 200, 160, 220, '#FFC23D', { r: 12, sw: SWN });
  near += circle(520, ty - 110, 52, { fill: d.grad('#FF7A3D'), stroke: ink('#FF7A3D'), strokeWidth: 3 }) + circle(520, ty - 110, 20, { fill: '#FFC23D' });
  near += text(520, ty - 160, 'GEAR-OS', { fontFamily: FONT.title, fontSize: 28, fill: '#E5303D', textAnchor: 'middle', stroke: '#FFFFFF', strokeWidth: 5, paintOrder: 'stroke' });
  near += text(520, ty - 30, 'CEREAL', { fontFamily: FONT.ui, fontWeight: 900, fontSize: 20, fill: '#8A4A06', textAnchor: 'middle', letterSpacing: 2 });
  // bowl
  near += path(`M1100 ${ty - 40}H1260Q1255 ${ty + 26} 1180 ${ty + 26}Q1105 ${ty + 26} 1100 ${ty - 40}Z`, { fill: d.grad('#3D7FEA'), stroke: ink('#3D7FEA'), strokeWidth: SWN });
  near += ellipse(1180, ty - 40, 80, 14, { fill: '#FFF8E8', stroke: ink('#3D7FEA'), strokeWidth: SWN });
  for (let i = 0; i < 6; i++) near += circle(1130 + i * 20, ty - 44 + (i % 2) * 5, 8, { fill: '#FFB43D', stroke: '#B0701A', strokeWidth: 1.5 });
  // Dad's mug
  near += pbox(d, 1410, ty - 100, 100, 120, '#FFFFFF', { r: 14, sw: SWN, stroke: ink('#C9D2E2') });
  near += path(`M1510 ${ty - 76}Q1560 ${ty - 76} 1560 ${ty - 40}Q1560 ${ty - 6} 1510 ${ty - 10}`, { fill: 'none', ...st(ink('#C9D2E2'), 20) }) + path(`M1510 ${ty - 76}Q1560 ${ty - 76} 1560 ${ty - 40}Q1560 ${ty - 6} 1510 ${ty - 10}`, { fill: 'none', ...st('#FFFFFF', 13) });
  near += text(1460, ty - 62, "WORLD'S", { fontFamily: FONT.ui, fontWeight: 900, fontSize: 15, fill: '#4A90E2', textAnchor: 'middle' });
  near += text(1460, ty - 40, 'OKAYEST', { fontFamily: FONT.title, fontSize: 21, fill: '#E5303D', textAnchor: 'middle' });
  near += text(1460, ty - 20, 'DAD', { fontFamily: FONT.ui, fontWeight: 900, fontSize: 16, fill: '#4A90E2', textAnchor: 'middle' });
  // orange juice
  near += pbox(d, 820, ty - 140, 74, 160, '#DFF2FF', { r: 10, sw: SWN, glossOp: 0.7, stroke: ink('#9FC8E8') });
  near += rect(826, ty - 100, 62, 114, { rx: 6, fill: d.lin(['#FFC23D', '#FF9A1F']) });
  return finish(d, [
    { name: 'far', depth: 0.3, svg: far },
    { name: 'mid', depth: 0.75, svg: mid },
    { name: 'light', depth: 0.75, svg: light },
    { name: 'near', depth: 1.0, svg: near },
  ], o);
}

// ======================================================================================
// CLASSROOM
// ======================================================================================
export function classroom(o = {}) {
  const d = new Defs();
  const wainY = 620, floorY = 790;
  const wall = '#FCEBBF';
  // --- far: the view through the windows (schoolyard trees)
  let far = '';
  const wins = [[1380, 140, 230, 360], [1660, 140, 230, 360]];
  for (const [x, y, w, h] of wins) {
    far += rect(x, y, w, h, { fill: d.lin(['#4AA3FA', '#9FD6FD']) });
    far += cloud(d, x + 120, y + 90, 0.35, 51 + x);
    far += path(`M${x} ${y + h - 90} Q ${x + w / 2} ${y + h - 120} ${x + w} ${y + h - 95} V ${y + h} H ${x} Z`, { fill: atmos('#57C25A', '#9FD6FD', 0.25) });
    far += circle(x + w * 0.3, y + h - 110, 50, { fill: atmos('#3FAF4A', '#9FD6FD', 0.2) }) + rect(x + w * 0.3 - 6, y + h - 70, 12, 60, { fill: atmos('#9A6238', '#9FD6FD', 0.3) });
  }
  // --- mid
  let mid = '';
  mid += rect(X0, -40, SW, wainY + 40, { fill: d.lin([shade(wall, 0.01), shade(wall, -0.04)]) });
  mid += rect(X0, -40, SW, wainY + 40, { fill: d.pattern(96, 96, rect(0, 0, 48, 96, { fill: shade(wall, -0.012) })) });
  mid += rect(X0, wainY, SW, floorY - wainY, { fill: d.lin(['#7FC7BE', '#5FB1A8']) });
  for (let xx = X0; xx < X1; xx += 90) mid += rect(xx, wainY + 20, 4, floorY - wainY - 36, { fill: '#4E9C94', opacity: 0.6 });
  mid += pbox(d, X0, wainY - 12, SW, 24, '#C98B57', { r: 5, sw: SWM });
  mid += rect(X0, floorY - 20, SW, 20, { fill: '#C98B57' });
  // alphabet banner
  const letters = 'ABCDEFGHIJKLM';
  for (let i = 0; i < letters.length; i++) {
    const lx = 330 + i * 70, col = ['#F0474E', '#FFAE1F', '#25BE66', '#25AEF2', '#8A5CF2', '#FF5596'][i % 6];
    mid += path(rrPath(lx, 40, 58, 64, 10), { fill: d.lin(['#FFFFFF', '#EEF0F8']), stroke: ink('#C9D2E2'), strokeWidth: 2 });
    mid += text(lx + 29, 88, letters[i] + letters[i].toLowerCase(), { fontFamily: FONT.title, fontSize: 30, fill: col, textAnchor: 'middle' });
  }
  // chalkboard with chalk writing
  const cbx = 300, cby = 150, cbw = 940, cbh = 400;
  mid += pbox(d, cbx - 26, cby - 26, cbw + 52, cbh + 52, '#C98B57', { r: 16, sw: SWM });
  mid += rect(cbx, cby, cbw, cbh, { rx: 8, fill: d.lin(['#2F7A5E', '#245F4A']) });
  mid += rect(cbx, cby, cbw, cbh, { rx: 8, fill: d.rad([[0, '#FFFFFF', 0.06], [1, '#FFFFFF', 0]], 0.3, 0.3, 0.7) });
  const chalk = { fontFamily: FONT.title, fill: '#F3F6EE', opacity: 0.92 };
  mid += text(cbx + 50, cby + 84, 'Today: The Water Cycle', { ...chalk, fontSize: 52 });
  mid += path(`M${cbx + 50} ${cby + 104}H${cbx + 610}`, { fill: 'none', ...st('#F3F6EE', 5), opacity: 0.7 });
  // chalk diagram: cloud, rain, sun, arrows
  mid += path(`M${cbx + 120} ${cby + 290}q-40 0 -40 -36q0 -36 44 -36q10 -40 56 -40q46 0 56 40q44 0 44 36q0 36 -40 36z`, { fill: 'none', ...st('#F3F6EE', 5), opacity: 0.9 });
  for (let i = 0; i < 4; i++) mid += line(cbx + 120 + i * 30, cby + 310, cbx + 110 + i * 30, cby + 350, { ...st('#9FD8FF', 5), opacity: 0.9 });
  mid += circle(cbx + 470, cby + 250, 40, { fill: 'none', ...st('#FFE08A', 5) });
  for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; mid += line(cbx + 470 + Math.cos(a) * 54, cby + 250 + Math.sin(a) * 54, cbx + 470 + Math.cos(a) * 70, cby + 250 + Math.sin(a) * 70, { ...st('#FFE08A', 5) }); }
  mid += path(`M${cbx + 410} ${cby + 300}Q${cbx + 330} ${cby + 360} ${cbx + 260} ${cby + 300}`, { fill: 'none', ...st('#F3F6EE', 5), opacity: 0.8 }) + path(`M${cbx + 272} ${cby + 286}L${cbx + 258} ${cby + 300}L${cbx + 278} ${cby + 308}`, { fill: 'none', ...st('#F3F6EE', 5), opacity: 0.8 });
  mid += text(cbx + 620, cby + 220, '1. Evaporation', { ...chalk, fontSize: 34 }) + text(cbx + 620, cby + 270, '2. Condensation', { ...chalk, fontSize: 34 }) + text(cbx + 620, cby + 320, '3. Precipitation', { ...chalk, fontSize: 34 });
  mid += text(cbx + 620, cby + 370, '4. ...', { ...chalk, fontSize: 34, opacity: 0.6 });
  mid += pbox(d, cbx - 10, cby + cbh + 16, cbw + 20, 18, '#B8784A', { r: 5, sw: SWM });
  mid += rect(cbx + 80, cby + cbh + 8, 50, 12, { rx: 6, fill: '#FFFFFF' }) + rect(cbx + 150, cby + cbh + 8, 36, 12, { rx: 6, fill: '#FFC0D0' }) + pbox(d, cbx + 820, cby + cbh + 2, 90, 22, '#5C6B9E', { r: 6, sw: 2 });
  // clock 9:05
  mid += circle(1300, 100, 56, { fill: d.lin(['#FFFFFF', '#E8ECF4']), stroke: '#3A4470', strokeWidth: 9 });
  mid += line(1300, 100, 1300, 62, st('#3A4470', 6)) + line(1300, 100, 1328, 112, st('#3A4470', 7)) + circle(1300, 100, 5, { fill: '#F0474E' });
  // window frames on the right + light
  for (const [x, y, w, h] of wins) {
    mid += path(rrPath(x - 16, y - 16, w + 32, h + 32, 10), { fill: 'none', stroke: d.lin(['#FFFFFF', '#E6E9F2']), strokeWidth: 22 });
    mid += path(rrPath(x - 27, y - 27, w + 54, h + 54, 14), { fill: 'none', stroke: ink('#E6E9F2'), strokeWidth: SWM });
    mid += rect(x, y + h * 0.5 - 5, w, 10, { fill: '#F4F6FA' });
    mid += poly([[x + 30, y + h], [x + 110, y], [x + 140, y], [x + 60, y + h]], { fill: '#FFFFFF', opacity: 0.3 });
    mid += pbox(d, x - 36, y + h + 14, w + 72, 22, '#FFFFFF', { r: 6, sw: SWM, stroke: ink('#E6E9F2') });
  }
  // bulletin board on the left
  mid += pbox(d, -360, 170, 560, 330, '#D69A62', { r: 12, sw: SWM });
  mid += rect(-344, 186, 528, 298, { rx: 6, fill: d.lin(['#E9B98A', '#DFAA78']) });
  const papers = [[-320, 210, 130, 160, '#FFFFFF', -4], [-170, 200, 140, 120, '#FFF3A8', 3], [-10, 220, 150, 170, '#FFFFFF', -2], [-160, 340, 120, 120, '#BFE6FF', 4], [-320, 390, 120, 80, '#FFD0E0', -3]];
  papers.forEach(([x, y, w, h, c, r], i) => {
    mid += g(pbox(d, 0, 0, w, h, c, { r: 4, sw: 1.5, gloss: false, stroke: '#B8A080' }) + rect(14, 20, w - 28, 8, { rx: 4, fill: '#B8C2D6' }) + rect(14, 36, w - 50, 8, { rx: 4, fill: '#B8C2D6' }) + circle(w / 2, 8, 8, { fill: ['#F0474E', '#25AEF2', '#25BE66', '#FFAE1F', '#8A5CF2'][i], stroke: '#00000033', strokeWidth: 1 }), { transform: `translate(${x} ${y}) rotate(${r})` });
  });
  mid += g(path(starPts(0, 0, 5, 38, 16).map((p, i) => (i ? 'L' : 'M') + f(p[0]) + ' ' + f(p[1])).join('') + 'Z', { fill: d.grad('#FFC23D'), stroke: ink('#FFC23D'), strokeWidth: 2.5, strokeLinejoin: 'round' }), { transform: 'translate(110 420) rotate(8)' });
  // teacher's desk (mid layer, front-left) with apple, globe, books
  const dx = 120, dy = 640;
  mid += contact(dx + 300, floorY + 4, 330, 14, 0.22);
  mid += pbox(d, dx, dy, 600, 34, '#B97A48', { r: 8, sw: SWM, glossOp: 0.45 });
  mid += pbox(d, dx + 20, dy + 34, 560, floorY - dy - 34, '#A86C3E', { r: 6, sw: SWM, gloss: false });
  mid += path(rrPath(dx + 60, dy + 60, 200, 60, 8), { fill: 'none', stroke: shade('#A86C3E', -0.08), strokeWidth: 4 }) + pbox(d, dx + 140, dy + 84, 40, 10, '#FFC23D', { r: 5, sw: 1.5 });
  mid += circle(dx + 120, dy - 34, 32, { fill: d.grad('#F2443A'), stroke: ink('#F2443A'), strokeWidth: SWM }) + path(`M${dx + 120} ${dy - 66}q4 -14 14 -18`, { fill: 'none', ...st('#7A4A2A', 5) }) + path(`M${dx + 128} ${dy - 74}q16 -14 30 -2q-16 12 -30 2z`, { fill: '#3FAF4A' });
  mid += ellipse(dx + 108, dy - 48, 9, 5, { fill: '#FFFFFF', opacity: 0.6 });
  mid += pbox(d, dx + 400, dy - 30, 150, 30, '#3D7FEA', { r: 5, sw: SWM }) + pbox(d, dx + 410, dy - 58, 130, 28, '#25BE66', { r: 5, sw: SWM }) + pbox(d, dx + 396, dy - 84, 140, 26, '#F0474E', { r: 5, sw: SWM });
  mid += pbox(d, dx + 280, dy - 20, 60, 20, '#5C6B9E', { r: 6, sw: SWM }) + line(dx + 310, dy - 20, dx + 310, dy - 60, st('#5C6B9E', 6));
  mid += circle(dx + 310, dy - 110, 52, { fill: d.lin(['#5AC8FF', '#2E8CF0']), stroke: ink('#2E8CF0'), strokeWidth: SWM });
  mid += path(`M${dx + 284} ${dy - 140}q20 -8 30 10q-8 22 -30 18q-12 -14 0 -28z M${dx + 322} ${dy - 96}q18 -10 26 6q-6 20 -26 14z`, { fill: '#3FBF5A' });
  mid += path(`M${dx + 258} ${dy - 110}A52 52 0 0 0 ${dx + 362} ${dy - 110}`, { fill: 'none', stroke: '#B8784A', strokeWidth: 6 });
  // bookshelf against the right wall
  mid += pbox(d, 2040, 360, 340, 430, '#B97A48', { r: 10, sw: SWM });
  for (let sy = 0; sy < 3; sy++) {
    mid += rect(2058, 380 + sy * 135, 304, 116, { fill: '#8A5A34', rx: 4 });
    for (let b = 0; b < 8; b++) mid += pbox(d, 2064 + b * 37, 400 + sy * 135 + (b % 3) * 8, 30, 96 - (b % 3) * 8, ['#F0474E', '#25AEF2', '#FFAE1F', '#25BE66', '#8A5CF2', '#FF5596'][(b + sy) % 6], { r: 4, sw: 1.8, glossOp: 0.3 });
  }
  // floor: warm linoleum squares
  mid += rect(X0, floorY, SW, H - floorY + 40, { fill: d.lin(['#E7D3B0', '#D8C097']) });
  {
    let yy = floorY, rh = 50, k = 0;
    while (yy < H + 40) {
      mid += rect(X0, yy, SW, 3, { fill: '#C4A97E', opacity: 0.8 });
      for (let xx = X0 + (k % 2) * 80; xx < X1; xx += 160) mid += rect(xx, yy, 3, rh, { fill: '#C4A97E', opacity: 0.6 });
      yy += rh; rh *= 1.22; k++;
    }
  }
  // --- light: daylight through the windows (screen)
  let light = '';
  for (const [x, y, w, h] of wins) light += poly([[x, y], [x + w, y], [x + w - 520, H + 40], [x - 760, H + 40]], { fill: d.lin([[0, '#FFF6D0', 0.28], [1, '#FFF6D0', 0]]), style: 'mix-blend-mode:screen' });
  // --- near: student desks in the foreground (characters sit at them)
  let near = '';
  const desk = (x, y, w) => {
    let s = pbox(d, x + 30, y + 40, 24, 260, '#8A96B8', { r: 8, sw: SWN }) + pbox(d, x + w - 54, y + 40, 24, 260, '#8A96B8', { r: 8, sw: SWN });
    s += pbox(d, x, y, w, 46, '#E2A766', { r: 10, sw: SWN, glossOp: 0.45 });
    s += pbox(d, x + 20, y + 46, w - 40, 60, '#9AA6C8', { r: 6, sw: SWN, gloss: false });
    return s;
  };
  near += desk(-200, 930, 560) + desk(1560, 930, 560);
  near += pbox(d, 40, 896, 150, 34, '#25AEF2', { r: 5, sw: SWN }) + pbox(d, 1700, 900, 120, 30, '#FF5596', { r: 5, sw: SWN });
  near += g(pbox(d, -18, -6, 160, 12, '#FFC23D', { r: 6, sw: 2 }) + poly([[142, -6], [168, 0], [142, 6]], { fill: '#F6D3BE', stroke: ink('#F6D3BE'), strokeWidth: 2 }), { transform: 'translate(1860 920) rotate(-8)' });
  return finish(d, [
    { name: 'far', depth: 0.3, svg: far },
    { name: 'mid', depth: 0.75, svg: mid },
    { name: 'light', depth: 0.75, svg: light },
    { name: 'near', depth: 1.0, svg: near },
  ], o);
}

// ======================================================================================
// STREET — DAY 7 "FACTORY RESET" chaos variant
// ======================================================================================
const MISSING = (d, size = 40) => d.pattern(size * 2, size * 2, rect(0, 0, size * 2, size * 2, { fill: '#121018' }) + rect(0, 0, size, size, { fill: '#FF2BD6' }) + rect(size, size, size, size, { fill: '#FF2BD6' }));
export function streetReset(o = {}) {
  const base = street({ ...o, cam: undefined, sky: ['#3A0614', '#7E0F22', '#C8202E'] });
  const d = new Defs();
  const pct = o.pct ?? 87;
  // replace the sky: a giant loading bar IS the sky
  let sky = rect(X0, -200, SW, 940, { fill: d.lin([[0, '#26040E'], [0.5, '#5A0A1A'], [1, '#A8182A']], [0, -200, 0, 740], 'userSpaceOnUse') });
  const barX = -60, barY = 120, barW = 2040, barH = 300, fillW = barW * pct / 100;
  sky += path(rrPath(barX - 16, barY - 16, barW + 32, barH + 32, 70), { fill: '#12020A', stroke: '#FF6A6A', strokeWidth: 6, opacity: 0.95 });
  sky += path(rrPath(barX, barY, barW, barH, 56), { fill: MISSING(d, 50), opacity: 0.55 });
  const stripes = d.pattern(120, 120, rect(0, 0, 120, 120, { fill: 'none' }) + path('M-30 120L60 0H120L30 120Z', { fill: '#FFFFFF', opacity: 0.16 }) + path('M90 120L180 0H240L150 120Z', { fill: '#FFFFFF', opacity: 0.16 }), `patternTransform="translate(${f(((o.t || 0) * 160) % 120)} 0)"`);
  // the filled part shows the remains of the old blue sky, de-rezzing into blocks at the leading edge
  const fillClip = d.clip(path(rrPath(barX, barY, fillW, barH, 56)));
  sky += g(rect(barX, barY, fillW, barH, { fill: d.lin(['#FF8A3D', '#FF3B3B', '#C8102E'], 'v') }) + rect(barX, barY, fillW, barH, { fill: stripes }) + rect(barX, barY + 18, fillW, 26, { fill: '#FFFFFF', opacity: 0.3 }), { clipPath: fillClip });
  const R = rng(77);
  for (let i = 0; i < 26; i++) {
    const bx = barX + fillW - 10 + R() * 240, by = barY + R() * barH, bs = 20 + R() * 40;
    sky += rect(bx, by, bs, bs, { fill: R() < 0.5 ? '#FF3B3B' : '#FF2BD6', opacity: 0.4 + R() * 0.5, stroke: '#12020A', strokeWidth: 2 });
  }
  sky += circle(barX + fillW, barY + barH / 2, 200, { fill: d.rad([[0, '#FFB070', 0.6], [1, '#FFB070', 0]]), style: 'mix-blend-mode:screen' });
  sky += text(960, barY + barH / 2 + 46, `FACTORY RESET  ${pct}%`, { fontFamily: FONT.title, fontSize: 132, fill: '#FFFFFF', textAnchor: 'middle', stroke: '#3A0410', strokeWidth: 16, paintOrder: 'stroke', strokeLinejoin: 'round', letterSpacing: 4 });
  sky += text(960, barY + barH + 80, 'Do not turn off reality', { fontFamily: FONT.ui, fontWeight: 900, fontSize: 44, fill: '#FFB0B0', textAnchor: 'middle', letterSpacing: 2 });
  // far layer: re-tint toward the red sky, and lift blocks off the hills
  let far = `<g style="filter:hue-rotate(-150deg) saturate(1.3) brightness(0.85)">${base.layers[2].svg}</g>`;
  for (let i = 0; i < 30; i++) { const bx = X0 + R() * SW, by = 380 + R() * 260, bs = 10 + R() * 26; far += rect(bx, by, bs, bs, { fill: R() < 0.3 ? '#FF2BD6' : '#C84860', opacity: 0.8 }); }
  // mid layer: houses with missing-texture patches, one house in wireframe, Kevin's lawn half-reset
  let mid = base.layers[3].svg;
  const patches = [[120, 470, 180, 140], [700, 520, 150, 110], [1180, 440, 210, 150], [1880, 520, 170, 130], [1300, 720, 330, 80], [-300, 560, 140, 120], [560, 380, 120, 120]];
  patches.forEach(([x, y, w, h], i) => {
    const jag = [];
    const RR = rng(100 + i);
    for (let k = 0; k <= 8; k++) jag.push([x + (w * k) / 8, y + (RR() - 0.5) * 30]);
    for (let k = 8; k >= 0; k--) jag.push([x + (w * k) / 8, y + h + (RR() - 0.5) * 30]);
    mid += poly(jag, { fill: MISSING(d, 22), stroke: '#FF2BD6', strokeWidth: 3 });
  });
  // a wireframe ghost of the house that already reset
  mid += g(rect(640, 454, 340, 250, { fill: '#1A0510', opacity: 0.9 }) + rect(640, 454, 340, 250, { fill: 'none', stroke: '#FF6A9A', strokeWidth: 3, strokeDasharray: '14 8' }) +
    poly([[614, 458], [810, 330], [1006, 458]], { fill: 'none', stroke: '#FF6A9A', strokeWidth: 3, strokeDasharray: '14 8' }) + line(640, 454, 980, 704, { stroke: '#FF6A9A', strokeWidth: 2, opacity: 0.5 }) + line(980, 454, 640, 704, { stroke: '#FF6A9A', strokeWidth: 2, opacity: 0.5 }) +
    text(810, 600, 'LOADING…', { fontFamily: FONT.ui, fontWeight: 900, fontSize: 30, fill: '#FF9AC0', textAnchor: 'middle', letterSpacing: 3 }));
  // floating de-rezzed cubes rising from the street
  for (let i = 0; i < 40; i++) {
    const bx = X0 + 200 + R() * (SW - 400), by = 360 + R() * 440, bs = 14 + R() * 34, c = ['#FF3B3B', '#FF2BD6', '#FFB070', '#8A5CF2'][i % 4];
    mid += g(rect(-bs / 2, -bs / 2, bs, bs, { fill: d.grad(c), stroke: ink(c), strokeWidth: 2, rx: 3 }) + rect(-bs / 2 + 3, -bs / 2 + 3, bs - 6, bs * 0.16, { fill: '#FFFFFF', opacity: 0.45, rx: 2 }), { transform: `translate(${f(bx)} ${f(by)}) rotate(${f(R() * 90)})` });
  }
  let near = base.layers[4].svg;
  // cracks of void in the road
  near += path('M300 930L380 960L350 1000L460 1040L430 1090H260L300 1030L240 990Z', { fill: MISSING(d, 18), stroke: '#FF2BD6', strokeWidth: 3 });
  near += path('M1500 900L1620 930L1580 980L1700 1000L1660 1090H1480L1530 1010L1460 960Z', { fill: MISSING(d, 18), stroke: '#FF2BD6', strokeWidth: 3 });
  // red alert grade: multiply wash + rotating alarm beams + vignette
  let grade = rect(X0, -60, SW, H + 120, { fill: '#FF2A3A', opacity: 0.22, style: 'mix-blend-mode:multiply' });
  const beam = (cx, cy, ang, col) => g(poly([[0, 0], [1400, -160], [1400, 160]], { fill: d.lin([[0, col, 0.4], [1, col, 0]], 'h') }), { transform: `translate(${cx} ${cy}) rotate(${ang})`, style: 'mix-blend-mode:screen' });
  grade += beam(-40, 40, 28 + (o.t || 0) * 90, '#FF5A5A') + beam(1960, 40, 152 - (o.t || 0) * 90, '#FF5A5A');
  grade += rect(X0, -60, SW, H + 120, { fill: d.rad([[0.5, '#2A0008', 0], [1, '#2A0008', 0.65]], 0.5, 0.5, 0.75) });
  const layers = [
    base.layers[0],
    { name: 'defs2', depth: 0, svg: String(d) },
    { name: 'sky', depth: 0.08, svg: sky },
    { name: 'far', depth: 0.3, svg: far },
    { name: 'mid', depth: 0.75, svg: mid },
    { name: 'near', depth: 1.0, svg: near },
    { name: 'grade', depth: 0, svg: grade },
  ];
  return { w: W, h: H, layers, svg: compose(layers, o.cam), glitch: true };
}

export const SETS = { street, bedroom, kitchen, classroom, streetReset };
