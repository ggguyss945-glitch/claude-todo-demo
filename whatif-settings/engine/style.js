// style.js — palette tokens, OKLCH colour math and the "toy plastic" finish helpers.
// Every helper returns SVG markup or a paint reference ("url(#id)"). Paint servers are collected in one
// deduplicating registry (ids derive from the parameters, so identical requests share one def); call
// resetDefs() before building a frame and put defsSvg() first in the <svg>.

export const W = 1920, H = 1080;

// ---------- palette ----------
export const PAL = {
  ink: '#1A1215',          // pupils, eye rings, brows, mouth lines only (never body outlines)
  white: '#FFFFFF',
  mouth: '#551124', tongue: '#FD6C89', teeth: '#FFFFFF',
  blush: '#FF8FA3', sweat: '#8FD8FF', tear: '#7CC8FF',
  star: '#FFD43B', heart: '#FF4D6D',
  skinCool: '#F4E7DB', skinWarm: '#F6DCC4', skinTan: '#E3B48C', skinBrown: '#B97A55',
  sky: '#BFD8F5',
  studioTop: '#EEF1FA', studioBot: '#D9DEEE', floor: '#E3E6F2',
  // cast
  samHoodie: '#FF7A3D', samHoodieDark: '#E4572A', samJeans: '#3A4A7A', samHair: '#8A4A2B', phones: '#FF8A1F',
  lilyOveralls: '#FF6FAE', lilyTee: '#FFD84A', lilyHair: '#7A3E2A',
  momCardigan: '#9B6CF0', momTop: '#7FE0C6', momHair: '#A5482C', momPants: '#3E4470',
  dadPolo: '#4A90E2', dadPants: '#CDB58A', dadHair: '#5B3A28', mug: '#FFFFFF',
  cat: '#9EA4B4', catSock: '#FFFFFF', catNose: '#FF9DB3',
  briggsVest: '#E0B03A', briggsShirt: '#DCEBFA', briggsTie: '#E2404A', briggsHair: '#B9BCC6', briggsPants: '#7C5E45',
  kevinTank: '#FFFFFF', kevinShorts: '#8E9C5A', kevinHair: '#E2B85A', blower: '#FF5A3C',
};

// ---------- seeded rng (mulberry32) ----------
export function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ---------- OKLCH ----------
const clamp01 = (v) => Math.min(1, Math.max(0, v));
const toLin = (c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const toGam = (c) => (c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055);

export function hexToRgb(hex) {
  let h = hex.replace('#', '');
  if (h.length === 3) h = h.split('').map((c) => c + c).join('');
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);
}
export function rgbToHex([r, g, b]) {
  return '#' + [r, g, b].map((v) => Math.round(clamp01(v) * 255).toString(16).padStart(2, '0')).join('').toUpperCase();
}
function rgbToLab([r, g, b]) {
  r = toLin(r); g = toLin(g); b = toLin(b);
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  return [0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
    1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
    0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s];
}
function labToRgbLinear([L, a, b]) {
  const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3;
  return [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
    -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
    -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s];
}
export function oklch(hex) {
  const [L, a, b] = rgbToLab(hexToRgb(hex));
  return { L, C: Math.hypot(a, b), h: ((Math.atan2(b, a) * 180) / Math.PI + 360) % 360 };
}
// back to hex, reducing chroma until the colour is inside sRGB (keeps lightness and hue)
export function fromOklch(L, C, h) {
  L = Math.min(1, Math.max(0, L));
  const hr = (h * Math.PI) / 180;
  const inGamut = (c) => labToRgbLinear([L, c * Math.cos(hr), c * Math.sin(hr)]).every((v) => v >= -1e-4 && v <= 1 + 1e-4);
  let c = C;
  if (!inGamut(c)) { let lo = 0, hi = c; for (let i = 0; i < 24; i++) { const mid = (lo + hi) / 2; if (inGamut(mid)) lo = mid; else hi = mid; } c = lo; }
  return rgbToHex(labToRgbLinear([L, c * Math.cos(hr), c * Math.sin(hr)]).map(toGam));
}
// shift a colour: dL in OKLCH lightness, cMul chroma multiplier, dh hue degrees
export function tone(hex, dL = 0, cMul = 1, dh = 0) {
  const { L, C, h } = oklch(hex);
  return fromOklch(L + dL, C * cMul, h + dh);
}
export function mix(a, b, t) {
  const A = rgbToLab(hexToRgb(a)), B = rgbToLab(hexToRgb(b));
  return rgbToHex(labToRgbLinear(A.map((v, i) => v + (B[i] - v) * t)).map(toGam));
}
const PURPLE_H = 305;
const towardPurple = (h, deg) => { const d = ((PURPLE_H - h + 540) % 360) - 180; return h + Math.sign(d) * Math.min(Math.abs(d), deg); };

// tinted outline: the dark shade of the fill, never black. L 0.28-0.32, chroma x0.9, hue 12 deg toward purple.
export function stroke(fill, dL = 0) {
  const { L, C, h } = oklch(fill);
  const c = Math.max(C * 0.9, 0.035);                         // greys and whites still get a tinted line
  const hh = C < 0.012 ? 300 : towardPurple(h, 12);            // only true neutrals borrow a cool violet line
  const LL = 0.30 + Math.max(0, L - 0.85) * 0.25 + dL;         // very light fills get a slightly lighter line
  return fromOklch(LL, Math.min(c, 0.13), hh);
}
export const lighter = (fill, d = 0.05) => tone(fill, d, 0.96);
export const darker = (fill, d = 0.07) => tone(fill, -d, 1.04);
// atmospheric perspective: mix toward the sky and drop chroma for back layers (depth 0..1)
export function atmos(fill, depth = 1, sky = PAL.sky) {
  const m = mix(fill, sky, 0.25 + 0.15 * depth);
  return tone(m, 0, 1 - 0.3 * depth);
}

// ---------- defs registry ----------
const REG = new Map();
let UID = 0;
export function resetDefs() { REG.clear(); UID = 0; }
export function defsSvg() { return `<defs>${[...REG.values()].join('')}</defs>`; }
export function uid(p = 'u') { UID += 1; return `${p}${UID}`; }
export function addDef(id, svg) { if (!REG.has(id)) REG.set(id, svg); return id; }
const hkey = (s) => { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(36); };
const r1 = (n) => Math.round(n * 10) / 10;

// 2-stop gradient: top/top-left L +0.05, bottom/bottom-right L -0.07 (about 12% luminance spread).
// dir: 'v' (sky, props), 'd' (character blocks, key light upper-left), 'h', or a number = light angle in degrees.
// box: [x0,y0,x1,y1] for a userSpaceOnUse gradient (so several shapes share one continuous ramp), else bbox units.
export function grad(fill, dir = 'd', { box = null, up = 0.05, down = 0.07 } = {}) {
  const a = tone(fill, up, 0.97), b = tone(fill, -down, 1.05);
  let v;
  if (dir === 'v') v = [0, 0, 0, 1];
  else if (dir === 'h') v = [0, 0, 1, 0];
  else if (dir === 'd') v = [0.1, 0, 0.9, 1];
  else { const t = (dir * Math.PI) / 180; v = [0.5 - 0.5 * Math.cos(t), 0.5 - 0.5 * Math.sin(t), 0.5 + 0.5 * Math.cos(t), 0.5 + 0.5 * Math.sin(t)]; }
  let coords, units;
  if (box) {
    const [x0, y0, x1, y1] = box, w = x1 - x0, h = y1 - y0;
    coords = [x0 + v[0] * w, y0 + v[1] * h, x0 + v[2] * w, y0 + v[3] * h].map(r1); units = 'userSpaceOnUse';
  } else { coords = v.map((n) => Math.round(n * 1000) / 1000); units = 'objectBoundingBox'; }
  const id = 'g' + hkey(`${fill}|${dir}|${coords}|${units}|${up}|${down}`);
  addDef(id, `<linearGradient id="${id}" gradientUnits="${units}" x1="${coords[0]}" y1="${coords[1]}" x2="${coords[2]}" y2="${coords[3]}"><stop offset="0" stop-color="${a}"/><stop offset="1" stop-color="${b}"/></linearGradient>`);
  return `url(#${id})`;
}
// 3-stop vertical ramp for skies and backdrops
export function ramp(stops, dir = 'v') {
  const id = 'r' + hkey(stops.join('|') + dir);
  const [x2, y2] = dir === 'v' ? [0, 1] : [1, 0];
  addDef(id, `<linearGradient id="${id}" x1="0" y1="0" x2="${x2}" y2="${y2}">${stops.map((c, i) => `<stop offset="${i / (stops.length - 1)}" stop-color="${c}"/>`).join('')}</linearGradient>`);
  return `url(#${id})`;
}
// face / round-part radial: centre (upper-left of middle) L +0.03, rim L -0.05
export function radial(fill, { cx = 0.4, cy = 0.36, r = 0.8, up = 0.03, down = 0.06 } = {}) {
  const id = 'f' + hkey(`${fill}|${cx}|${cy}|${r}|${up}|${down}`);
  addDef(id, `<radialGradient id="${id}" cx="${cx}" cy="${cy}" r="${r}" fx="${cx}" fy="${cy}"><stop offset="0" stop-color="${tone(fill, up, 0.95)}"/><stop offset="0.6" stop-color="${fill}"/><stop offset="1" stop-color="${tone(fill, -down, 1.06)}"/></radialGradient>`);
  return `url(#${id})`;
}
// cel shade band along the side away from the key light (right edge): transparent, then a hard step
export function shadeBand(fill, { at = 0.88, op = 0.55, dL = 0.075, dir = 'h' } = {}) {
  const c = tone(fill, -dL, 1.1);
  const id = 'b' + hkey(`${fill}|${at}|${op}|${dL}|${dir}`);
  const [x2, y2] = dir === 'h' ? [1, 0] : [0, 1];
  addDef(id, `<linearGradient id="${id}" x1="0" y1="0" x2="${x2}" y2="${y2}"><stop offset="0" stop-color="${c}" stop-opacity="0"/><stop offset="${at}" stop-color="${c}" stop-opacity="0"/><stop offset="${Math.min(1, at + 0.005)}" stop-color="${c}" stop-opacity="${op}"/><stop offset="1" stop-color="${c}" stop-opacity="${op}"/></linearGradient>`);
  return `url(#${id})`;
}
// soft contact shadow paint (radial, darkest in the middle)
function shadowPaint(color, op) {
  const id = 's' + hkey(color + op);
  addDef(id, `<radialGradient id="${id}"><stop offset="0" stop-color="${color}" stop-opacity="${op}"/><stop offset="0.55" stop-color="${color}" stop-opacity="${op * 0.75}"/><stop offset="1" stop-color="${color}" stop-opacity="0"/></radialGradient>`);
  return `url(#${id})`;
}
// contact shadow under feet / lifted objects: shrinks and fades with height h (px above ground)
export function contactShadow(cx, cy, rx, ry, { op = 0.28, h = 0, color = '#2A2346' } = {}) {
  const k = 1 / (1 + h / 120);
  return `<ellipse cx="${r1(cx)}" cy="${r1(cy)}" rx="${r1(rx * (0.6 + 0.4 * k))}" ry="${r1(ry * (0.6 + 0.4 * k))}" fill="${shadowPaint(color, Math.round(op * k * 100) / 100)}" style="mix-blend-mode:multiply"/>`;
}
// soft glow (screen) for light pools / studio key
export function glowPaint(color, op = 0.6) {
  const id = 'w' + hkey(color + op);
  addDef(id, `<radialGradient id="${id}"><stop offset="0" stop-color="${color}" stop-opacity="${op}"/><stop offset="1" stop-color="${color}" stop-opacity="0"/></radialGradient>`);
  return `url(#${id})`;
}

// ---------- SVG primitives ----------
export const f1 = r1;
export function attrs(o) {
  return Object.entries(o).filter(([, v]) => v !== undefined && v !== null && v !== false)
    .map(([k, v]) => `${k.replace(/[A-Z]/g, (m) => '-' + m.toLowerCase())}="${v}"`).join(' ');
}
export const g = (inner, a = {}) => `<g ${attrs(a)}>${inner}</g>`;
export const path = (d, a = {}) => `<path ${attrs({ d, ...a })}/>`;
export const rect = (x, y, w, h, a = {}) => `<rect ${attrs({ x: r1(x), y: r1(y), width: r1(w), height: r1(h), ...a })}/>`;
export const circle = (cx, cy, r, a = {}) => `<circle ${attrs({ cx: r1(cx), cy: r1(cy), r: r1(Math.max(0, r)), ...a })}/>`;
export const ellipse = (cx, cy, rx, ry, a = {}) => `<ellipse ${attrs({ cx: r1(cx), cy: r1(cy), rx: r1(Math.max(0, rx)), ry: r1(Math.max(0, ry)), ...a })}/>`;
export const text = (x, y, s, a = {}) => `<text ${attrs({ x: r1(x), y: r1(y), ...a })}>${s}</text>`;
export const line = (x1, y1, x2, y2, a = {}) => `<line ${attrs({ x1: r1(x1), y1: r1(y1), x2: r1(x2), y2: r1(y2), ...a })}/>`;
// outlined, gradient-filled part: fill can be a paint url; outline is stroke(base) unless given
export function solid(d, base, { sw = 3, dir = 'd', box = null, line: ln = null, paint = null, extra = {} } = {}) {
  return path(d, { fill: paint || grad(base, dir, { box }), stroke: ln || stroke(base), strokeWidth: r1(sw), strokeLinejoin: 'round', strokeLinecap: 'round', ...extra });
}
// union outline: draw every shape's stroke (2x width) underneath, then every fill on top, so shapes of one
// material read as a single silhouette with no inner seams. shapes: [{d, fill?}]
export function union(shapes, base, { sw = 3, dir = 'd', box = null, line: ln = null } = {}) {
  const lc = ln || stroke(base);
  const paint = grad(base, dir, { box });
  return shapes.map((s) => path(s.d, { fill: lc, stroke: lc, strokeWidth: r1(sw * 2), strokeLinejoin: 'round' })).join('')
    + shapes.map((s) => path(s.d, { fill: s.fill || paint })).join('');
}

// ---------- geometry ----------
const P = (x, y) => `${r1(x)} ${r1(y)}`;
export function rrect(x, y, w, h, r) {
  r = Math.min(r, w / 2, h / 2);
  return `M${P(x + r, y)}H${r1(x + w - r)}A${r1(r)} ${r1(r)} 0 0 1 ${P(x + w, y + r)}V${r1(y + h - r)}A${r1(r)} ${r1(r)} 0 0 1 ${P(x + w - r, y + h)}H${r1(x + r)}A${r1(r)} ${r1(r)} 0 0 1 ${P(x, y + h - r)}V${r1(y + r)}A${r1(r)} ${r1(r)} 0 0 1 ${P(x + r, y)}Z`;
}
// capsule between two points, width w (round ends)
export function capsule(x1, y1, x2, y2, w) {
  const dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy) || 0.001, nx = -dy / L, ny = dx / L, r = w / 2;
  return `M${P(x1 + nx * r, y1 + ny * r)}L${P(x2 + nx * r, y2 + ny * r)}A${r1(r)} ${r1(r)} 0 0 0 ${P(x2 - nx * r, y2 - ny * r)}L${P(x1 - nx * r, y1 - ny * r)}A${r1(r)} ${r1(r)} 0 0 0 ${P(x1 + nx * r, y1 + ny * r)}Z`;
}
// tapered capsule: radius r1 at p1, r2 at p2
export function taper(x1, y1, x2, y2, ra, rb) {
  const dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy) || 0.001, ux = dx / L, uy = dy / L, nx = -uy, ny = ux;
  const s = Math.min(0.99, Math.max(-0.99, (ra - rb) / L)), c = Math.sqrt(1 - s * s);
  const ax = nx * c + ux * s, ay = ny * c + uy * s, bx = -nx * c + ux * s, by = -ny * c + uy * s;
  const big1 = s > 0 ? 1 : 0, big2 = s > 0 ? 0 : 1;
  return `M${P(x1 + ax * ra, y1 + ay * ra)}L${P(x2 + ax * rb, y2 + ay * rb)}A${r1(rb)} ${r1(rb)} 0 ${big2} 0 ${P(x2 + bx * rb, y2 + by * rb)}L${P(x1 + bx * ra, y1 + by * ra)}A${r1(ra)} ${r1(ra)} 0 ${big1} 0 ${P(x1 + ax * ra, y1 + ay * ra)}Z`;
}
// rounded trapezoid: top edge width wt at y0, bottom width wb at y1, corner radii rt / rb
export function rtrap(cx, y0, y1, wt, wb, rt, rb) {
  const pts = [[cx - wt / 2, y0, rt], [cx + wt / 2, y0, rt], [cx + wb / 2, y1, rb], [cx - wb / 2, y1, rb]];
  return roundPoly(pts);
}
// polygon with per-corner radius [[x,y,r],...]
export function roundPoly(pts) {
  const n = pts.length; let d = '';
  for (let i = 0; i < n; i++) {
    const [x, y, r] = pts[i], [px, py] = pts[(i + n - 1) % n], [nx2, ny2] = pts[(i + 1) % n];
    const l1 = Math.hypot(px - x, py - y), l2 = Math.hypot(nx2 - x, ny2 - y);
    const rr = Math.min(r || 0, l1 / 2, l2 / 2);
    const ax = x + ((px - x) / l1) * rr, ay = y + ((py - y) / l1) * rr, bx = x + ((nx2 - x) / l2) * rr, by = y + ((ny2 - y) / l2) * rr;
    d += (i === 0 ? 'M' : 'L') + P(ax, ay) + `Q${P(x, y)} ${P(bx, by)}`;
  }
  return d + 'Z';
}
// smooth closed/open curve through points (Catmull-Rom -> cubic Bezier). sharp: set of indices kept as corners
export function spline(pts, { closed = false, sharp = new Set(), k = 1 / 6 } = {}) {
  const n = pts.length; if (n < 2) return '';
  const get = (i) => (closed ? pts[(i + n) % n] : pts[Math.max(0, Math.min(n - 1, i))]);
  let d = `M${P(...pts[0])}`;
  const segs = closed ? n : n - 1;
  for (let i = 0; i < segs; i++) {
    const p0 = get(i - 1), p1 = get(i), p2 = get(i + 1), p3 = get(i + 2);
    const s1 = sharp.has(i % n), s2 = sharp.has((i + 1) % n);
    const c1 = s1 ? p1 : [p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k];
    const c2 = s2 ? p2 : [p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k];
    d += `C${P(...c1)} ${P(...c2)} ${P(...p2)}`;
  }
  return d + (closed ? 'Z' : '');
}
export const polyline = (pts, close = true) => 'M' + pts.map((p) => P(p[0], p[1])).join('L') + (close ? 'Z' : '');

// ---------- gloss ----------
// gloss strips for a capsule p1->p2 of width w: a long strip and a thin companion on the lit side
// (the side whose normal faces the upper-left key light), white at 30-45%.
export function glossCapsule(x1, y1, x2, y2, w, { op = 0.38, from = 0.18, to = 0.82, thin = true } = {}) {
  const dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy) || 0.001, ux = dx / L, uy = dy / L;
  let nx = -uy, ny = ux; if (nx * -0.6 + ny * -0.8 < 0) { nx = -nx; ny = -ny; }
  const off = w * 0.24, sw = Math.max(1, w * 0.13);
  const a = [x1 + ux * L * from + nx * off, y1 + uy * L * from + ny * off], b = [x1 + ux * L * to + nx * off, y1 + uy * L * to + ny * off];
  let s = path(`M${P(...a)}L${P(...b)}`, { stroke: '#FFFFFF', strokeOpacity: op, strokeWidth: r1(sw), strokeLinecap: 'round', fill: 'none' });
  if (thin && L > w * 1.4) {
    const o2 = w * 0.06, sw2 = Math.max(0.6, w * 0.05);
    const c = [x1 + ux * L * (from + 0.08) + nx * o2, y1 + uy * L * (from + 0.08) + ny * o2], e = [x1 + ux * L * (to - 0.2) + nx * o2, y1 + uy * L * (to - 0.2) + ny * o2];
    s += path(`M${P(...c)}L${P(...e)}`, { stroke: '#FFFFFF', strokeOpacity: op * 0.7, strokeWidth: r1(sw2), strokeLinecap: 'round', fill: 'none' });
  }
  return s;
}
// gloss for a box-like part (torso, head): vertical strip inset 8-12% from the left edge and a short top strip
export function glossBox(x, y, w, h, { op = 0.34, left = true, top = true, sw = null } = {}) {
  const s = sw || Math.max(1.2, w * 0.06);
  let out = '';
  if (left) out += path(`M${P(x + w * 0.11, y + h * 0.2)}L${P(x + w * 0.11, y + h * 0.72)}`, { stroke: '#FFFFFF', strokeOpacity: op, strokeWidth: r1(s), strokeLinecap: 'round', fill: 'none' });
  if (top) out += path(`M${P(x + w * 0.22, y + h * 0.085)}L${P(x + w * 0.5, y + h * 0.085)}`, { stroke: '#FFFFFF', strokeOpacity: op * 0.9, strokeWidth: r1(s * 0.8), strokeLinecap: 'round', fill: 'none' });
  return out;
}
export const gloss = { capsule: glossCapsule, box: glossBox };

// ---------- type ----------
export const FONT_DISPLAY = "'Lilita One', 'Rubik', sans-serif";
export const FONT_UI = "'Rubik', sans-serif";
// outlined display label (paint-order keeps the outline outside the glyph)
export function label(x, y, s, { size = 40, fill = '#FFFFFF', line: ln = '#2A2346', sw = null, anchor = 'middle', font = FONT_DISPLAY, weight = 400, ls = 0.5 } = {}) {
  return text(x, y, s, { fontFamily: font, fontWeight: weight, fontSize: size, fill, stroke: ln, strokeWidth: r1(sw ?? size * 0.16), strokeLinejoin: 'round', paintOrder: 'stroke', textAnchor: anchor, letterSpacing: ls });
}
