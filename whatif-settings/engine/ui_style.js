// Shared helpers for the UI, sets, captions and FX of "What If Real Life Had a SETTINGS MENU?".
// Pure functions that return SVG markup strings (1920x1080 design space). Deterministic: no Math.random, no Date.
// Colour maths in OKLCH (bible 3.1): grad() = 2-stop gradient (+L top / -L bottom), ink() = tinted outline,
// atmos() = depth haze. Kept self-contained so it does not depend on the character agent's style.js.

export const W = 1920, H = 1080;
export const FONT = { ui: 'Nunito', title: 'Lilita One' };

// ---------- number / string helpers ----------
export const f = (n) => Math.round(n * 10) / 10;
export const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const lerp = (a, b, t) => a + (b - a) * t;
/** progress of p inside [a,b], clamped to 0..1 */
export const seg = (p, a, b) => clamp((p - a) / (b - a));
export const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

export function hash(str) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
  return h.toString(36);
}
/** deterministic PRNG (mulberry32) */
export function rng(seed) {
  let a = (seed >>> 0) || 1;
  return () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ---------- easing ----------
export const ease = {
  outCubic: (t) => 1 - (1 - t) ** 3,
  inCubic: (t) => t ** 3,
  inOutCubic: (t) => (t < 0.5 ? 4 * t ** 3 : 1 - (-2 * t + 2) ** 3 / 2),
  inOutSine: (t) => -(Math.cos(Math.PI * t) - 1) / 2,
  outQuad: (t) => 1 - (1 - t) ** 2,
  outBack: (t, s = 1.9) => 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2,
  outElastic: (t) => (t === 0 || t === 1 ? t : 2 ** (-10 * t) * Math.sin((t * 10 - 0.75) * (2 * Math.PI / 3)) + 1),
};

/** Pop-in curve used by every UI element: p 0..1 over the entry (4-10 frames).
 *  scale 0.35 -> 1.12 (p .45) -> 0.97 (p .72) -> 1.0; opacity reaches 1 by p .3. */
export function popScale(p) {
  p = clamp(p);
  if (p <= 0) return 0.35;
  if (p < 0.45) return lerp(0.35, 1.12, ease.outCubic(p / 0.45));
  if (p < 0.72) return lerp(1.12, 0.97, ease.inOutSine((p - 0.45) / 0.27));
  return lerp(0.97, 1, ease.inOutSine((p - 0.72) / 0.28));
}
export const popOpacity = (p) => clamp(p / 0.3);

// ---------- colour maths (OKLab / OKLCH) ----------
function hexToRgb(h) {
  h = h.replace('#', '');
  if (h.length === 3) h = h.split('').map((c) => c + c).join('');
  const n = parseInt(h.slice(0, 6), 16);
  return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
}
const toLin = (c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const toSrgb = (c) => (c <= 0.0031308 ? 12.92 * c : 1.055 * Math.sign(c) * Math.abs(c) ** (1 / 2.4) - 0.055);
function rgbToOklab([r, g, b]) {
  r = toLin(r); g = toLin(g); b = toLin(b);
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  return [0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s, 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s, 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s];
}
function oklabToRgb([L, a, b]) {
  const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3;
  return [toSrgb(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s), toSrgb(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s), toSrgb(-0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)];
}
const inGamut = (rgb) => rgb.every((c) => c >= -0.0005 && c <= 1.0005);
const rgbHex = (rgb) => '#' + rgb.map((c) => Math.round(clamp(c) * 255).toString(16).padStart(2, '0')).join('').toUpperCase();

export function toOklch(hex) {
  const [L, a, b] = rgbToOklab(hexToRgb(hex));
  return [L, Math.hypot(a, b), ((Math.atan2(b, a) * 180) / Math.PI + 360) % 360];
}
/** OKLCH -> hex, reducing chroma until the colour is inside sRGB */
export function fromOklch(L, C, h) {
  L = clamp(L, 0, 1); C = Math.max(0, C);
  const hr = (h * Math.PI) / 180;
  let lo = 0, hi = C, rgb = oklabToRgb([L, C * Math.cos(hr), C * Math.sin(hr)]);
  if (inGamut(rgb)) return rgbHex(rgb);
  for (let i = 0; i < 18; i++) {
    const mid = (lo + hi) / 2;
    const r = oklabToRgb([L, mid * Math.cos(hr), mid * Math.sin(hr)]);
    if (inGamut(r)) { lo = mid; rgb = r; } else hi = mid;
  }
  return rgbHex(oklabToRgb([L, lo * Math.cos(hr), lo * Math.sin(hr)]));
}
/** shift lightness by dL (OKLCH L units), scale chroma, rotate hue */
export function shade(hex, dL = 0, cMul = 1, dH = 0) {
  const [L, C, h] = toOklch(hex);
  return fromOklch(L + dL, C * cMul, h + dH);
}
/** mix two colours in OKLab, t = 0 -> a, 1 -> b */
export function mix(a, b, t) {
  const A = rgbToOklab(hexToRgb(a)), B = rgbToOklab(hexToRgb(b));
  return rgbHex(oklabToRgb([lerp(A[0], B[0], t), lerp(A[1], B[1], t), lerp(A[2], B[2], t)]));
}
/** tinted outline colour for a fill: dark (L .30), chroma x.9, hue rotated ~12 deg toward purple (bible 3.1) */
export function ink(hex, L = 0.33, cm = 0.55) {
  let [, C, h] = toOklch(hex);
  if (C < 0.025) h = 285; // greys and whites get a cool grey-violet line
  const towards = 300; // purple
  let d = ((towards - h + 540) % 360) - 180;
  const dh = Math.sign(d) * Math.min(12, Math.abs(d));
  return fromOklch(L, Math.max(C * cm, 0.03), h + dh);
}
/** atmospheric depth: mix toward the sky colour and drop chroma */
export function atmos(hex, sky, t = 0.3) {
  const m = mix(hex, sky, t);
  return shade(m, 0, 1 - t * 0.8);
}
export const light = (hex, d = 0.06) => shade(hex, d);
export const dark = (hex, d = 0.07) => shade(hex, -d);

// ---------- defs: gradients and filters with content-hashed ids ----------
// Each builder adds its def to a Defs bag and returns 'url(#id)'. Ids are hashes of the content, so the same
// gradient used by two components resolves to identical markup (duplicate identical ids are harmless).
export class Defs {
  constructor() { this.m = new Map(); }
  add(prefix, body) {
    const id = prefix + hash(body);
    if (!this.m.has(id)) this.m.set(id, body.replace('__ID__', id));
    return id;
  }
  /** linear gradient; stops = [[offset, colour, opacity?], ...] or [c1, c2]; dir 'v' | 'h' | 'd' (TL->BR) | [x1,y1,x2,y2] */
  lin(stops, dir = 'v', units = 'objectBoundingBox') {
    const st = normStops(stops);
    const [x1, y1, x2, y2] = dir === 'v' ? [0, 0, 0, 1] : dir === 'h' ? [0, 0, 1, 0] : dir === 'd' ? [0, 0, 1, 1] : dir === 'u' ? [0, 1, 0, 0] : dir;
    const id = this.add('lg', `<linearGradient id="__ID__" gradientUnits="${units}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}">${st}</linearGradient>`);
    return `url(#${id})`;
  }
  /** radial gradient centred at (cx,cy) fractions (or user units when units='userSpaceOnUse') */
  rad(stops, cx = 0.5, cy = 0.5, r = 0.5, units = 'objectBoundingBox', fx, fy) {
    const st = normStops(stops);
    const fxy = fx !== undefined ? ` fx="${fx}" fy="${fy}"` : '';
    const id = this.add('rg', `<radialGradient id="__ID__" gradientUnits="${units}" cx="${cx}" cy="${cy}" r="${r}"${fxy}>${st}</radialGradient>`);
    return `url(#${id})`;
  }
  /** vertical 2-stop "plastic" gradient of a base fill (bible: top L+0.05, bottom L-0.07) */
  grad(fill, dir = 'v', up = 0.05, down = 0.07) { return this.lin([shade(fill, up), shade(fill, -down)], dir); }
  blur(sd, pad = 0.6) {
    const id = this.add('bl', `<filter id="__ID__" x="-${pad * 100}%" y="-${pad * 100}%" width="${100 + pad * 200}%" height="${100 + pad * 200}%" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="${sd}"/></filter>`);
    return `url(#${id})`;
  }
  /** soft UI drop shadow (UI only - the world never gets cast shadows) */
  shadow(dy = 10, sd = 14, op = 0.45, color = '#070A1A') {
    const id = this.add('sh', `<filter id="__ID__" x="-30%" y="-30%" width="160%" height="170%" color-interpolation-filters="sRGB"><feDropShadow dx="0" dy="${dy}" stdDeviation="${sd}" flood-color="${color}" flood-opacity="${op}"/></filter>`);
    return `url(#${id})`;
  }
  /** outer glow in a colour */
  glow(color, sd = 10, op = 0.9) {
    const id = this.add('gw', `<filter id="__ID__" x="-50%" y="-50%" width="200%" height="200%" color-interpolation-filters="sRGB"><feGaussianBlur in="SourceAlpha" stdDeviation="${sd}" result="b"/><feFlood flood-color="${color}" flood-opacity="${op}"/><feComposite in2="b" operator="in" result="g"/><feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge></filter>`);
    return `url(#${id})`;
  }
  clip(inner) { const id = this.add('cp', `<clipPath id="__ID__">${inner}</clipPath>`); return `url(#${id})`; }
  pattern(w, h, inner, extra = '') { const id = this.add('pt', `<pattern id="__ID__" width="${w}" height="${h}" patternUnits="userSpaceOnUse" ${extra}>${inner}</pattern>`); return `url(#${id})`; }
  raw(prefix, body) { return this.add(prefix, body); }
  toString() { return this.m.size ? `<defs>${[...this.m.values()].join('')}</defs>` : ''; }
}
function normStops(stops) {
  if (stops.length && typeof stops[0] === 'string') stops = stops.map((c, i) => [i / (stops.length - 1), c]);
  return stops.map(([o, c, a]) => `<stop offset="${o}" stop-color="${c}"${a !== undefined ? ` stop-opacity="${a}"` : ''}/>`).join('');
}

// ---------- svg primitives ----------
export function attrs(o) {
  return Object.entries(o).filter(([, v]) => v !== undefined && v !== null && v !== false)
    .map(([k, v]) => `${k.replace(/[A-Z]/g, (m) => '-' + m.toLowerCase())}="${typeof v === 'number' ? f(v) : v}"`).join(' ');
}
export const g = (inner, a = {}) => `<g ${attrs(a)}>${inner}</g>`;
export const rect = (x, y, w, h, a = {}) => `<rect ${attrs({ x, y, width: Math.max(0, w), height: Math.max(0, h), ...a })}/>`;
export const circle = (cx, cy, r, a = {}) => `<circle ${attrs({ cx, cy, r: Math.max(0, r), ...a })}/>`;
export const ellipse = (cx, cy, rx, ry, a = {}) => `<ellipse ${attrs({ cx, cy, rx: Math.max(0, rx), ry: Math.max(0, ry), ...a })}/>`;
export const line = (x1, y1, x2, y2, a = {}) => `<line ${attrs({ x1, y1, x2, y2, ...a })}/>`;
export const pts = (arr) => arr.map(([x, y]) => `${f(x)},${f(y)}`).join(' ');
export const poly = (p, a = {}) => `<polygon ${attrs({ points: pts(p), ...a })}/>`;
export const pline = (p, a = {}) => `<polyline ${attrs({ points: pts(p), fill: 'none', ...a })}/>`;
export const path = (d, a = {}) => `<path ${attrs({ d, ...a })}/>`;
export const text = (x, y, s, a = {}) => `<text ${attrs({ x, y, ...a })}>${s}</text>`;
export const tr = (x, y, s = 1, r = 0) => `translate(${f(x)} ${f(y)})${r ? ` rotate(${f(r)})` : ''}${s !== 1 ? ` scale(${Math.round(s * 1000) / 1000})` : ''}`;
/** stroke attribute bundle with round joins */
export const st = (color, w) => ({ stroke: color, strokeWidth: w, strokeLinejoin: 'round', strokeLinecap: 'round' });

/** rounded-rect path with per-corner radii [tl,tr,br,bl] */
export function rrPath(x, y, w, h, r) {
  const [a, b, c, d] = (Array.isArray(r) ? r : [r, r, r, r]).map((v) => Math.min(v, w / 2, h / 2));
  return `M${f(x + a)} ${f(y)}H${f(x + w - b)}Q${f(x + w)} ${f(y)} ${f(x + w)} ${f(y + b)}V${f(y + h - c)}Q${f(x + w)} ${f(y + h)} ${f(x + w - c)} ${f(y + h)}H${f(x + d)}Q${f(x)} ${f(y + h)} ${f(x)} ${f(y + h - d)}V${f(y + a)}Q${f(x)} ${f(y)} ${f(x + a)} ${f(y)}Z`;
}
/** star / starburst polygon points */
export function starPts(cx, cy, n, r1, r2, rot = -90, jitter = 0, seed = 1) {
  const R = rng(seed), out = [];
  for (let i = 0; i < n * 2; i++) {
    const a = ((rot + (i * 180) / n) * Math.PI) / 180;
    const r = (i % 2 ? r2 : r1) * (1 + (i % 2 ? 0 : (R() - 0.5) * jitter));
    out.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]);
  }
  return out;
}
/** gear outline path: n teeth, outer radius R, root radius r, teeth flat-topped and slightly rounded */
export function gearPath(cx, cy, R, r, n, rot = 0, toothFrac = 0.5) {
  let d = '';
  const step = (Math.PI * 2) / n;
  for (let i = 0; i < n; i++) {
    const a0 = (rot * Math.PI) / 180 + i * step;
    const tw = step * toothFrac, tt = tw * 0.72; // tooth base and top widths
    const pts4 = [
      [a0 - tw / 2, r], [a0 - tt / 2, R], [a0 + tt / 2, R], [a0 + tw / 2, r],
    ];
    pts4.forEach(([a, rad], k) => {
      const x = cx + Math.cos(a) * rad, y = cy + Math.sin(a) * rad;
      d += (i === 0 && k === 0 ? 'M' : 'L') + f(x) + ' ' + f(y);
    });
    // root arc to next tooth
    const an = a0 + step - tw / 2;
    d += `A${f(r)} ${f(r)} 0 0 1 ${f(cx + Math.cos(an) * r)} ${f(cy + Math.sin(an) * r)}`;
  }
  return d + 'Z';
}
export function arcPath(cx, cy, r, a0, a1) {
  // degrees, 0 = up, clockwise
  const p = (a) => [cx + Math.sin((a * Math.PI) / 180) * r, cy - Math.cos((a * Math.PI) / 180) * r];
  const [x0, y0] = p(a0), [x1, y1] = p(a1);
  const large = Math.abs(a1 - a0) > 180 ? 1 : 0;
  return `M${f(x0)} ${f(y0)}A${f(r)} ${f(r)} 0 ${large} 1 ${f(x1)} ${f(y1)}`;
}

/** Gloss strip: rounded white bar inset along the top edge of a part (bible: 30-45% white, 10-18% of width) */
export function glossTop(x, y, w, h, o = {}) {
  const inset = o.inset ?? Math.max(4, Math.min(w, h) * 0.1);
  const gh = o.h ?? Math.max(3, h * 0.12);
  return path(rrPath(x + inset * 1.4, y + inset, Math.max(0, w - inset * 2.8), gh, gh / 2), { fill: '#FFFFFF', opacity: o.op ?? 0.38 });
}

// ---------- pop-in + flash ring wrapper ----------
/** Wrap element markup so it pops in around (cx,cy) as p goes 0..1. bbox {x,y,w,h,r} draws a matching flash ring.
 *  ring:'rect'|'circle'|false. The flash ring expands ~70px and fades while the element overshoots. */
export function popIn(inner, cx, cy, p, o = {}) {
  if (p === undefined || p >= 1) return inner + (o.always || '');
  if (p <= 0) return '';
  const s = popScale(p), op = popOpacity(p);
  let ring = '';
  const rp = seg(p, 0.12, 1);
  if (o.ring !== false && rp > 0 && rp < 1) {
    const e = ease.outCubic(rp), grow = lerp(0, o.ringGrow ?? 70, e), sw = lerp(o.ringW ?? 12, 1, e), rop = (1 - rp) * 0.95;
    const col = o.ringColor ?? '#FFFFFF';
    if (o.ring === 'circle' || !o.bbox) {
      const r0 = o.r ?? 60;
      ring = circle(cx, cy, r0 + grow * 1.4, { fill: 'none', stroke: col, strokeWidth: sw, opacity: rop });
    } else {
      const b = o.bbox;
      ring = path(rrPath(b.x - grow, b.y - grow, b.w + grow * 2, b.h + grow * 2, (b.r ?? 20) + grow), { fill: 'none', stroke: col, strokeWidth: sw, opacity: rop });
    }
  }
  // white flash on the element itself early in the pop
  const fl = p < 0.5 ? (1 - seg(p, 0.15, 0.5)) * 0.55 : 0;
  const flash = fl > 0.01 && o.bbox ? path(rrPath(o.bbox.x, o.bbox.y, o.bbox.w, o.bbox.h, o.bbox.r ?? 20), { fill: '#FFFFFF', opacity: f(fl * 100) / 100 }) : '';
  return `<g opacity="${f(op * 100) / 100}"><g transform="translate(${f(cx)} ${f(cy)}) scale(${Math.round(s * 1000) / 1000}) translate(${f(-cx)} ${f(-cy)})">${inner}${flash}</g></g>${ring}`;
}

/** soft contact ellipse under feet / objects (multiply-like dark, no cast shadows) */
export function contact(cx, cy, rx, ry, op = 0.25, color = '#1A1430') {
  const d = new Defs();
  const fill = d.rad([[0, color, op], [0.6, color, op * 0.6], [1, color, 0]]);
  return d + ellipse(cx, cy, rx, ry, { fill });
}

// ---------- text measurement (measured advance widths, see ui_metrics.js) ----------
import { METRICS } from './ui_metrics.js';
/** approximate rendered width of a string: font 'n900' | 'n800' | 'n700' | 'lil'; letterSpacing in px */
export function textW(s, size, font = 'n900', letterSpacing = 0) {
  const m = METRICS[font] || METRICS.n900;
  let w = 0;
  for (const ch of String(s)) w += (m[ch] ?? m[ch.toLowerCase()] ?? 0.6) * size + letterSpacing;
  return w;
}
