// face.js — the face kit. Any eyes x brows x mouth, plus add-ons, drawn in head-local units:
// the head spans x -50..50, y -47..47 with its centre at 0,0. face() returns two layers:
//   .face — features painted on the skin (drawn under the hair fringe and accessories)
//   .fx   — add-ons that float over everything (sweat, ?, Z's, hearts, dizzy stars, bump)
// Line weights are fixed in head units, so they scale with the head (eye ring ~1.7x the body outline).
import { PAL, g, path, circle, ellipse, text, grad, stroke, tone, uid, addDef, fxDef, f1, spline, FONT_DISPLAY } from './style.js';

const INK = PAL.ink;
const RING = 4.1;      // eye ring width
const LINE = 3.4;      // mouth outline / lid line
const BROW = 5.6;      // brow thickness

// ---------- yaw mapping ----------
// Features live on the front of the head. For yaw psi (deg, + = turning to screen right) a feature at
// front x maps to screen x = 50 sin(phi), phi = asin(x/50)*(1-0.45|sin psi|) + 0.62 psi, squeezed by cos(phi).
export function mapFeature(x, yaw = 0) {
  const p = (yaw * Math.PI) / 180, s = Math.abs(Math.sin(p));
  const phi = Math.asin(Math.max(-1, Math.min(1, x / 50))) * (1 - 0.45 * s) + 0.62 * p;
  return { x: 50 * Math.sin(phi), k: Math.cos(phi), phi };
}

// ---------- small shape helpers ----------
const ln = (d, w = LINE, c = INK, extra = {}) => path(d, { fill: 'none', stroke: c, strokeWidth: w, strokeLinecap: 'round', strokeLinejoin: 'round', ...extra });
function clipDef(d) { const id = uid('c'); addDef(id, `<clipPath id="${id}"><path d="${d}"/></clipPath>`); return `url(#${id})`; }
function circlePath(cx, cy, r) { return `M${f1(cx - r)} ${f1(cy)}a${f1(r)} ${f1(r)} 0 1 0 ${f1(2 * r)} 0a${f1(r)} ${f1(r)} 0 1 0 ${f1(-2 * r)} 0Z`; }
function ellipsePath(cx, cy, rx, ry) { return `M${f1(cx - rx)} ${f1(cy)}a${f1(rx)} ${f1(ry)} 0 1 0 ${f1(2 * rx)} 0a${f1(rx)} ${f1(ry)} 0 1 0 ${f1(-2 * rx)} 0Z`; }
// clip a polygon by the half-plane a*x + b*y <= c (Sutherland-Hodgman)
function clipPoly(poly, a, b, c) {
  const out = [], inside = (p) => a * p[0] + b * p[1] <= c + 1e-9;
  for (let i = 0; i < poly.length; i++) {
    const P = poly[i], Q = poly[(i + 1) % poly.length], ip = inside(P), iq = inside(Q);
    if (ip) out.push(P);
    if (ip !== iq) { const t = (c - a * P[0] - b * P[1]) / (a * (Q[0] - P[0]) + b * (Q[1] - P[1])); out.push([P[0] + t * (Q[0] - P[0]), P[1] + t * (Q[1] - P[1])]); }
  }
  return out;
}
// chord of circle (0,0,r) along the line through (0, y0) at angle th: returns [p1, p2] or null
function chord(r, y0, th) {
  const c = Math.cos(th), s = Math.sin(th), B = y0 * s, C = y0 * y0 - r * r, D = B * B - C;
  if (D <= 0) return null;
  const t1 = -B - Math.sqrt(D), t2 = -B + Math.sqrt(D);
  return [[t1 * c, y0 + t1 * s], [t2 * c, y0 + t2 * s]];
}
export function starPath(R, inner = 0.48, n = 5, rot = -90) {
  const pts = [];
  for (let i = 0; i < n * 2; i++) { const a = ((rot + (i * 180) / n) * Math.PI) / 180, rr = i % 2 ? R * inner : R; pts.push([Math.cos(a) * rr, Math.sin(a) * rr]); }
  return pts;
}
function roundedStar(R, inner = 0.5) {
  const p = starPath(R, inner), n = p.length; let d = '';
  for (let i = 0; i < n; i++) {
    const a = p[i], b = p[(i + 1) % n], m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
    d += (i === 0 ? `M${f1(m[0])} ${f1(m[1])}` : '') ;
    const nb = p[(i + 2) % n], m2 = [(b[0] + nb[0]) / 2, (b[1] + nb[1]) / 2];
    d += `Q${f1(b[0])} ${f1(b[1])} ${f1(m2[0])} ${f1(m2[1])}`;
  }
  return d + 'Z';
}
export function heartPath(s = 1) {
  return `M0 ${f1(8 * s)}C${f1(-3 * s)} ${f1(5.5 * s)} ${f1(-11 * s)} ${f1(0 * s)} ${f1(-11 * s)} ${f1(-5.5 * s)}C${f1(-11 * s)} ${f1(-10.5 * s)} ${f1(-5 * s)} ${f1(-12 * s)} 0 ${f1(-6.5 * s)}C${f1(5 * s)} ${f1(-12 * s)} ${f1(11 * s)} ${f1(-10.5 * s)} ${f1(11 * s)} ${f1(-5.5 * s)}C${f1(11 * s)} 0 ${f1(3 * s)} ${f1(5.5 * s)} 0 ${f1(8 * s)}Z`;
}
export function dropPath(s = 1) {
  return `M0 ${f1(-10 * s)}C${f1(2.5 * s)} ${f1(-5 * s)} ${f1(6.5 * s)} ${f1(-1 * s)} ${f1(6.5 * s)} ${f1(3.2 * s)}A${f1(6.5 * s)} ${f1(6.5 * s)} 0 0 1 ${f1(-6.5 * s)} ${f1(3.2 * s)}C${f1(-6.5 * s)} ${f1(-1 * s)} ${f1(-2.5 * s)} ${f1(-5 * s)} 0 ${f1(-10 * s)}Z`;
}
const twinkle = (x, y, r, c = '#FFFFFF', o = 1) => path(`M${f1(x)} ${f1(y - r)}Q${f1(x + r * 0.16)} ${f1(y - r * 0.16)} ${f1(x + r)} ${f1(y)}Q${f1(x + r * 0.16)} ${f1(y + r * 0.16)} ${f1(x)} ${f1(y + r)}Q${f1(x - r * 0.16)} ${f1(y + r * 0.16)} ${f1(x - r)} ${f1(y)}Q${f1(x - r * 0.16)} ${f1(y - r * 0.16)} ${f1(x)} ${f1(y - r)}Z`, { fill: c, opacity: o });

// ---------- eyes ----------
// side: -1 screen-left eye, +1 screen-right. p: { look:[dx,dy], pupil (fraction of r), lid, tilt, lower, lowerTilt }
// lid / lower are chord heights in units of r (-1 top .. 1 bottom); tilt > 0 drops the inner corner (angry),
// tilt < 0 lifts it (sad).
function lidded(r, side, p, inner) {
  const box = r * 2.2;
  let poly = [[-box, -box], [box, -box], [box, box], [-box, box]];
  const lines = [];
  if (p.lid != null) {
    const th = (-side * (p.tilt || 0) * Math.PI) / 180, y0 = p.lid * r;
    // keep points below the line y = y0 + tan(th) x  ->  tan(th) x - y <= -y0
    poly = clipPoly(poly, Math.tan(th), -1, -y0);
    const c = chord(r, y0, th); if (c) lines.push(c);
  }
  if (p.lower != null) {
    const th = (side * (p.lowerTilt || 0) * Math.PI) / 180, y0 = p.lower * r;
    poly = clipPoly(poly, -Math.tan(th), 1, y0);
    const c = chord(r, y0, th); if (c) lines.push(c);
  }
  const clipped = p.lid != null || p.lower != null;
  const body = clipped ? g(inner, { clipPath: clipDef('M' + poly.map((q) => `${f1(q[0])} ${f1(q[1])}`).join('L') + 'Z') }) : inner;
  const lidLines = lines.map(([a, b]) => {
    const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1, e = RING * 0.25;
    return ln(`M${f1(a[0] - (dx / L) * e)} ${f1(a[1] - (dy / L) * e)}L${f1(b[0] + (dx / L) * e)} ${f1(b[1] + (dy / L) * e)}`, RING);
  }).join('');
  return body + lidLines;
}
function pupilDot(x, y, pr, { hl = true } = {}) {
  let s = circle(x, y, pr, { fill: INK });
  if (hl) s += circle(x + pr * 0.36, y - pr * 0.38, pr * 0.34, { fill: '#FFFFFF' }) + circle(x - pr * 0.34, y + pr * 0.4, pr * 0.14, { fill: '#FFFFFF', opacity: 0.85 });
  return s;
}
const EYES = {
  // ring + dot pupil (the default "alert" eye)
  ring(r, side, p) {
    const pr = r * (p.pupil ?? 0.44), [lx, ly] = p.look || [0, 0];
    const lim = r - pr - 1.2, m = Math.hypot(lx, ly), k = m > lim ? lim / m : 1;
    const inner = circle(0, 0, r, { fill: '#FFFFFF' })
      + g(pupilDot(lx * k, ly * k, pr), { clipPath: clipDef(circlePath(0, 0, r - 0.5)) })
      + circle(0, 0, r, { fill: 'none', stroke: INK, strokeWidth: RING });
    return lidded(r, side, p, inner);
  },
  // black bean with catchlight (the default "calm" eye)
  bean(r, side, p) {
    const [lx, ly] = p.look || [0, 0], rx = r * 0.56, ry = r * 0.8;
    const inner = ellipse(lx * 0.35, ly * 0.35, rx, ry, { fill: INK })
      + circle(lx * 0.35 + rx * 0.32, ly * 0.35 - ry * 0.38, rx * 0.36, { fill: '#FFFFFF' })
      + circle(lx * 0.35 - rx * 0.3, ly * 0.35 + ry * 0.34, rx * 0.15, { fill: '#FFFFFF', opacity: 0.8 });
    const q = { ...p }; if (q.lid != null) q.lid = q.lid * 0.8;
    return lidded(r * 0.82, side, q, inner);
  },
  // half-lid: heavy flat upper lid, pupils sitting low
  half(r, side, p) {
    const look = p.look || [0, 2.5];
    return EYES.ring(r, side, { pupil: 0.46, ...p, look: [look[0], Math.max(look[1], 1.5)], lid: p.lid ?? -0.08, tilt: p.tilt ?? 0 });
  },
  // closed happy arcs ^^
  happy(r) { return ln(`M${f1(-r * 0.78)} ${f1(r * 0.32)}Q0 ${f1(-r * 0.95)} ${f1(r * 0.78)} ${f1(r * 0.32)}`, RING * 1.15); },
  // closed calm/sleep arcs (smile-shaped)
  closed(r) { return ln(`M${f1(-r * 0.74)} ${f1(-r * 0.1)}Q0 ${f1(r * 0.72)} ${f1(r * 0.74)} ${f1(-r * 0.1)}`, RING * 1.1); },
  // squeezed shut > <
  strain(r, side) {
    const s = -side; // left eye points toward the centre: ">"
    return ln(`M${f1(-s * r * 0.62)} ${f1(-r * 0.56)}L${f1(s * r * 0.5)} 0L${f1(-s * r * 0.62)} ${f1(r * 0.56)}`, RING * 1.15);
  },
  star(r) {
    const R = r * 1.12, c = PAL.star;
    return path(roundedStar(R, 0.52), { fill: grad(c, 'd', { up: 0.06, down: 0.1 }), stroke: stroke(c), strokeWidth: RING * 0.8, strokeLinejoin: 'round' })
      + circle(-R * 0.22, -R * 0.22, R * 0.15, { fill: '#FFFFFF' }) + circle(R * 0.12, R * 0.12, R * 0.07, { fill: '#FFFFFF', opacity: 0.8 });
  },
  heart(r) {
    const c = PAL.heart, s = r / 10.5;
    return path(heartPath(s * 1.02), { fill: grad(c, 'd', { up: 0.07, down: 0.08 }), stroke: stroke(c), strokeWidth: RING * 0.8, strokeLinejoin: 'round', transform: `translate(0 ${f1(r * 0.12)})` })
      + ellipse(-5 * s, -5 * s, 2.6 * s, 1.8 * s, { fill: '#FFFFFF', opacity: 0.9, transform: `rotate(-30 ${f1(-5 * s)} ${f1(-5 * s)})` });
  },
  // tiny pupils in big whites (shock)
  pin(r, side, p) { return EYES.ring(r * 1.08, side, { ...p, pupil: 0.17, look: p.look || [0, 0] }); },
  // big glossy pupils with a pooled tear line
  teary(r, side, p) {
    const pr = r * 0.6, [lx, ly] = p.look || [0, 0.5];
    const pool = `M${f1(-r)} ${f1(r * 0.34)}Q${f1(-r * 0.5)} ${f1(r * 0.2)} 0 ${f1(r * 0.36)}Q${f1(r * 0.5)} ${f1(r * 0.52)} ${f1(r)} ${f1(r * 0.34)}L${f1(r)} ${f1(r)}L${f1(-r)} ${f1(r)}Z`;
    const inner = circle(0, 0, r, { fill: '#FFFFFF' })
      + g(circle(lx, ly, pr, { fill: INK }) + circle(lx + pr * 0.32, ly - pr * 0.36, pr * 0.36, { fill: '#FFFFFF' }) + circle(lx - pr * 0.36, ly + pr * 0.22, pr * 0.2, { fill: '#FFFFFF' }) + circle(lx + pr * 0.44, ly + pr * 0.3, pr * 0.1, { fill: '#FFFFFF' })
        + path(pool, { fill: PAL.tear, opacity: 0.75 }), { clipPath: clipDef(circlePath(0, 0, r - 0.5)) })
      + circle(0, 0, r, { fill: 'none', stroke: INK, strokeWidth: RING });
    return lidded(r, side, p, inner);
  },
  // narrowed (suspicious / disgusted)
  squint(r, side, p) { return EYES.ring(r, side, { pupil: 0.5, look: [0, 0.5], lid: -0.22, tilt: 10, lower: 0.42, lowerTilt: -6, ...p }); },
  // angry: lids slant down to the nose
  angry(r, side, p) { return EYES.ring(r, side, { pupil: 0.4, lid: -0.32, tilt: 24, ...p }); },
  spiral(r) {
    const pts = []; for (let i = 0; i <= 64; i++) { const t = i / 64, a = t * Math.PI * 5.2, rr = r * 0.82 * t; pts.push([Math.cos(a) * rr, Math.sin(a) * rr]); }
    return circle(0, 0, r, { fill: '#FFFFFF', stroke: INK, strokeWidth: RING }) + ln('M' + pts.map((q) => `${f1(q[0])} ${f1(q[1])}`).join('L'), RING * 0.6);
  },
  dot(r) { return circle(0, 0, r * 0.3, { fill: INK }); },
  none() { return ''; },
};

// ---------- brows ----------
// [innerDy, outerDy, arch] relative to brow line; inner = end nearest the nose
const BROWS = {
  neutral: [0, 1.5, -1.6], worry: [-6.5, 2.5, -0.6], angry: [6.5, -3.5, 0.6], flat: [2.5, 2.5, 0], raised: [-6, -4, -3.2],
  sad: [-4, 4, 0.4], soft: [-3, 1.5, -1.2], none: null,
};
export function browSpec(type, side) {
  if (Array.isArray(type)) return type;
  if (type === 'skeptic') return side < 0 ? [-7.5, -5, -3.5] : [3, 2, 0];
  if (type === 'skepticR') return side > 0 ? [-7.5, -5, -3.5] : [3, 2, 0];
  return BROWS[type] || null;
}
function brow(type, side, { x, y, len = 16, k = 1, w = BROW, color = INK }) {
  const spec = browSpec(type, side);
  if (!spec) return '';
  const [di, dout, arch] = spec, inX = x - side * len * 0.5 * k, outX = x + side * len * 0.5 * k;
  const mx = (inX + outX) / 2, my = y + (di + dout) / 2 + arch * 1.4;
  return ln(`M${f1(inX)} ${f1(y + di)}Q${f1(mx)} ${f1(my)} ${f1(outX)} ${f1(y + dout)}`, type === 'angry' ? w * 1.1 : w, color);
}

// ---------- mouths ----------
// each returns markup centred on 0,0; opts: { gap (gap tooth), m (scale) }
function filledMouth(d, extras, { tongue = null, teeth = null, gap = false, lower = null } = {}) {
  const clip = clipDef(d);
  let inner = path(d, { fill: PAL.mouth });
  if (tongue) inner += ellipse(tongue[0], tongue[1], tongue[2], tongue[3], { fill: PAL.tongue });
  if (teeth) {
    inner += path(`M-40 -40H40V${f1(teeth)}H-40Z`, { fill: PAL.teeth });
    if (gap) inner += path(`M-1.6 ${f1(teeth - 7)}h3.2v7h-3.2Z`, { fill: PAL.mouth });
  }
  if (lower != null) inner += path(`M-40 ${f1(lower)}H40V40H-40Z`, { fill: PAL.teeth });
  return g(inner + (extras || ''), { clipPath: clip }) + path(d, { fill: 'none', stroke: INK, strokeWidth: LINE, strokeLinejoin: 'round' });
}
const MOUTHS = {
  smile: () => ln('M-10 -2.5Q0 7.5 10 -2.5'),
  bigSmile: () => ln('M-14 -4Q0 10.5 14 -4') + ln('M-15.5 -6.5Q-14.5 -4.5 -13 -3.5', LINE * 0.8) + ln('M15.5 -6.5Q14.5 -4.5 13 -3.5', LINE * 0.8),
  frown: () => ln('M-9 4Q0 -4.5 9 4'),
  flat: () => ln('M-8 0L8 0'),
  meh: () => ln('M-4 1L9 -1.5'),
  set: () => ln('M-11 0L11 0') + ln('M-11 0L-12.5 2.5', LINE * 0.9) + ln('M11 0L12.5 2.5', LINE * 0.9),
  smirk: () => ln('M-10 1.5Q1 4.5 10.5 -4.5') + ln('M10.5 -4.5Q12.6 -4 13 -1.6', LINE * 0.8),
  wavy: () => ln('M-14 1Q-10.5 -3.5 -7 1T0 1T7 1T14 1'),
  cat: () => ln('M-10 -1.5Q-5 6 0 -0.5Q5 6 10 -1.5'),
  smallO: () => filledMouth(ellipsePath(0, 0, 4.6, 5.6), '', {}),
  o: () => filledMouth(ellipsePath(0, 1, 7.5, 9.5), '', { tongue: [0, 8.5, 5.5, 3.6] }),
  dOpen: ({ gap }) => filledMouth('M-13 -5Q0 -7 13 -5C13 6 7 13.5 0 13.5C-7 13.5 -13 6 -13 -5Z', '', { tongue: [1, 12.5, 7.5, 5], teeth: -1.6, gap }),
  laugh: ({ gap }) => filledMouth('M-17 -6.5Q0 -1 17 -6.5C17 9 9 20 0 20C-9 20 -17 9 -17 -6.5Z', '', { tongue: [1, 18.5, 10, 6.5], teeth: -0.5, gap }),
  grin: ({ gap }) => filledMouth('M-17 -6Q0 -1.5 17 -6Q13 12 0 12Q-13 12 -17 -6Z', ln('M-15 1.5Q0 6.5 15 1.5', 1.6) + (gap ? '' : ln('M0 -3.4L0 3.6', 1.4)) + ln('M-8 -3L-8.5 3.4', 1.4) + ln('M8 -3L8.5 3.4', 1.4), { teeth: 30, gap }),
  scream: () => filledMouth('M0 -15C9 -15 13.5 -7 13.5 3C13.5 14 8 21 0 21C-8 21 -13.5 14 -13.5 3C-13.5 -7 -9 -15 0 -15Z', '', { tongue: [0, 18, 9, 6], teeth: -11.5 }),
  wavyOpen: () => filledMouth('M-14 -3Q-10.5 -7 -7 -3T0 -3T7 -3T14 -3L14 4Q10.5 8 7 4T0 4T-7 4T-14 4Z', ln('M-14 0.5Q-10.5 -3.5 -7 0.5T0 0.5T7 0.5T14 0.5', 1.3, '#C9B9C2'), { teeth: 30 }),
  gritted: () => filledMouth('M-14 -7H14Q19 -7 19 0Q19 7 14 7H-14Q-19 7 -19 0Q-19 -7 -14 -7Z', ln('M-19 0H19', 1.6) + ln('M-9 -7V7', 1.6) + ln('M0 -7V7', 1.6) + ln('M9 -7V7', 1.6), { teeth: 30 }),
  grimace: () => filledMouth('M-15 -5Q0 -7.5 15 -5Q17 -4 16.5 -1.5Q15.5 5 9 5.5Q0 6.5 -9 5.5Q-15.5 5 -16.5 -1.5Q-17 -4 -15 -5Z', ln('M-16 0.3Q0 -1.5 16 0.3', 1.5) + ln('M-6 -6V6', 1.4) + ln('M6 -6V6', 1.4), { teeth: 30 }),
  yawn: () => filledMouth('M0 -12C7.5 -12 10 -5 10 2.5C10 11 6 16 0 16C-6 16 -10 11 -10 2.5C-10 -5 -7.5 -12 0 -12Z', '', { tongue: [0, 14, 7.5, 5], teeth: -9.8 }),
  tongueOut: () => {
    const t = PAL.tongue;
    return path('M-5 1.5Q-5.5 11 0 11.5Q5.5 11 5 1.5Z', { fill: grad(t, 'd'), stroke: stroke(t), strokeWidth: LINE * 0.8, strokeLinejoin: 'round' }) + ln('M0 3.5L0 7.5', 1.4, stroke(t)) + ln('M-11 -2Q0 6 11 -2');
  },
  blech: () => {
    const t = PAL.tongue;
    return filledMouth('M-12 -4Q-2 -6 12 -3Q11 5 0 5.5Q-11 5 -12 -4Z', '', { teeth: -2.8 })
      + path('M-3 2Q-4.5 13 2 13.5Q8 13 6 2Z', { fill: grad(t, 'd'), stroke: stroke(t), strokeWidth: LINE * 0.8, strokeLinejoin: 'round' }) + ln('M1.7 4.5L2 8.5', 1.4, stroke(t));
  },
  ugh: () => filledMouth('M-13 -1Q-6 -6.5 1 -4.5Q8 -3 13.5 -7.5Q13 3.5 5 5Q-4 6.5 -13 -1Z', ln('M-11 -0.6Q0 -2.5 12 -4', 1.4), { teeth: 30 }),
  cry: () => filledMouth('M-14.5 3Q0 -9 14.5 3Q14 15 0 15Q-14 15 -14.5 3Z', '', { tongue: [0, 14, 8.5, 5], teeth: -3.6 }),
  evil: () => {
    const d = 'M-18 -6Q0 1 18 -6Q12 13 0 13Q-12 13 -18 -6Z';
    const teeth = 'M-16 -5.5L-12 1L-8 -2.6L-4 3L0 -2.2L4 3L8 -2.6L12 1L16 -5.5L16 -20L-16 -20Z';
    return filledMouth(d, path(teeth, { fill: PAL.teeth }), {});
  },
  // ---- dog muzzle mouths (TINY) ----
  dogW: () => ln('M-11 -2Q-5.5 5.5 0 -1Q5.5 5.5 11 -2'),
  dogPant: ({ gap }) => filledMouth('M-14 -4Q-7 -1 0 -4Q7 -1 14 -4C14 7 8 14 0 14C-8 14 -14 7 -14 -4Z', '', { tongue: [0, 12, 9, 6], gap }),
  // ---- visemes ----
  none: () => '',
  v_closed: () => ln('M-8.5 0Q0 2 8.5 0'),
  v_small: () => filledMouth('M-7.5 0Q-7.5 -4.2 0 -4.2Q7.5 -4.2 7.5 0Q7.5 4.6 0 4.6Q-7.5 4.6 -7.5 0Z', '', { tongue: [0, 4.4, 4.2, 2.2], teeth: -2.6 }),
  v_E: ({ gap }) => filledMouth('M-12.5 -4.5Q0 -6 12.5 -4.5Q14 0.5 11 3.5Q0 5.5 -11 3.5Q-14 0.5 -12.5 -4.5Z', '', { teeth: -1.4, lower: 2.4, gap }),
  v_A: ({ gap }) => filledMouth('M-11.5 -6Q0 -7.5 11.5 -6Q12 8 0 13.5Q-12 8 -11.5 -6Z', '', { tongue: [0, 11.5, 7, 4.6], teeth: -3, gap }),
  v_O: () => filledMouth(ellipsePath(0, 1.5, 7, 8.8), '', { tongue: [0, 8.5, 4.6, 3] }),
};
export const VISEMES = ['v_closed', 'v_small', 'v_E', 'v_A', 'v_O'];
export const MOUTH_TYPES = Object.keys(MOUTHS);
export const EYE_TYPES = Object.keys(EYES);
export const BROW_TYPES = [...Object.keys(BROWS), 'skeptic', 'skepticR'];

// ---------- expression presets ----------
// eyes, brows, mouth, optional per-eye overrides (eyeL / eyeR), lid params, look, add-ons, mouth scale (m)
export const PRESETS = {
  neutral: { eyes: 'bean', brows: 'neutral', mouth: 'smile' },
  happy: { eyes: 'happy', brows: 'raised', mouth: 'dOpen', add: { blush: 1 } },
  starstruck: { eyes: 'star', brows: 'raised', mouth: 'laugh', m: 0.9, add: { sparkle: 1, blush: 1 } },
  shocked: { eyes: 'ring', brows: 'raised', mouth: 'o', look: [0, 0], pupil: 0.4, add: { shock: 1 } },
  deadpan: { eyes: 'half', brows: 'flat', mouth: 'flat', look: [0, 2] },
  smug: { eyes: 'half', lid: 0.02, tilt: -6, lower: 0.62, brows: 'skeptic', mouth: 'smirk', look: [3, 2] },
  scared: { eyes: 'ring', pupil: 0.32, brows: 'worry', mouth: 'smallO', look: [0, -1.5], add: { sweat: 1 } },
  panic: { eyes: 'pin', brows: 'worry', mouth: 'wavyOpen', m: 1.05, add: { sweat: 2, shock: 1 } },
  angry: { eyes: 'angry', brows: 'angry', mouth: 'gritted', add: { vein: 1 } },
  guilty: { eyes: 'ring', pupil: 0.42, look: [-5.5, 2], brows: 'worry', mouth: 'grimace', add: { sweat: 1 } },
  sleepy: { eyes: 'half', lid: 0.3, look: [0, 3], brows: 'soft', mouth: 'smallO', add: { zzz: 1 } },
  confused: { eyes: 'ring', eyeL: { scale: 0.84, look: [2, -1] }, eyeR: { scale: 1.12, look: [-1, -1] }, brows: 'skeptic', mouth: 'wavy', m: 0.7, add: { q: 1 } },
  scream: { eyes: 'strain', brows: 'worry', mouth: 'scream', m: 1.12, add: { shock: 1 } },
  laugh: { eyes: 'happy', brows: 'raised', mouth: 'laugh', add: { joy: 1, blush: 1 } },
  cry: { eyes: 'teary', brows: 'sad', mouth: 'cry', add: { tears: 1 } },
  sly: { eyes: 'half', lid: -0.1, tilt: 14, look: [5, 2], brows: 'angry', browScale: 0.6, mouth: 'smirk' },
  determined: { eyes: 'angry', lid: -0.42, tilt: 14, pupil: 0.46, brows: 'angry', mouth: 'grin' },
  disgusted: { eyes: 'squint', brows: 'skeptic', mouth: 'ugh', mouthDX: 2, add: { gloom: 1 } },
  dizzy: { eyes: 'spiral', brows: 'none', mouth: 'wavy', m: 0.8, add: { dizzy: 1 } },
  love: { eyes: 'heart', brows: 'raised', mouth: 'dOpen', m: 0.85, add: { hearts: 1, blush: 1 } },
  relieved: { eyes: 'closed', brows: 'soft', mouth: 'bigSmile', add: { sweat: 1, blush: 0.6 } },
  nervous: { eyes: 'bean', look: [4, -2], brows: 'worry', mouth: 'wavy', m: 0.75, add: { sweat: 2 } },
  bored: { eyes: 'half', lid: 0.14, look: [4.5, -1], brows: 'flat', mouth: 'meh' },
  evil: { eyes: 'angry', lid: -0.12, tilt: 30, pupil: 0.3, brows: 'angry', mouth: 'evil', add: { gloom: 1 } },
  // extras for scenes
  excited: { eyes: 'ring', pupil: 0.48, brows: 'raised', mouth: 'dOpen', add: { blush: 0.6 } },
  wink: { eyes: 'ring', eyeR: { type: 'happy' }, brows: 'raised', mouth: 'tongueOut', add: { sparkle: 1 } },
  sad: { eyes: 'bean', look: [0, 3], brows: 'sad', mouth: 'frown' },
  skeptic: { eyes: 'ring', eyeL: { lid: -0.15 }, look: [2, 0], brows: 'skeptic', mouth: 'flat' },
  surprised: { eyes: 'ring', brows: 'raised', mouth: 'smallO' },
  yawn: { eyes: 'closed', brows: 'soft', mouth: 'yawn' },
  blep: { eyes: 'happy', brows: 'neutral', mouth: 'tongueOut' },
  talk: { eyes: 'bean', brows: 'neutral', mouth: 'v_A' },
  // hook extras
  squint: { eyes: 'squint', lid: -0.3, tilt: 6, lower: 0.38, pupil: 0.52, look: [0, 3], brows: 'angry', browScale: 0.55, mouth: 'set', m: 0.8 },
  ish: { eyes: 'half', lid: 0.05, tilt: -8, look: [-5, 2.5], brows: 'worry', mouth: 'grimace', m: 0.62, add: { sweat: 1 } },
  forcedGrin: { eyes: 'ring', pupil: 0.36, look: [0, 0], brows: 'worry', mouth: 'grin', m: 0.92, add: { sweat: 1 } },
  shout: { eyes: 'strain', brows: 'angry', mouth: 'scream', m: 1.05, add: { shock: 1 } },
  blank: { eyes: 'none', brows: 'none', mouth: 'none' },
};
export const SHEET_ORDER = ['neutral', 'happy', 'starstruck', 'shocked', 'deadpan', 'smug', 'scared', 'panic', 'angry', 'guilty', 'sleepy', 'confused',
  'scream', 'laugh', 'cry', 'sly', 'determined', 'disgusted', 'dizzy', 'love', 'relieved', 'nervous', 'bored', 'evil'];

export const isViseme = (m) => typeof m === 'string' && m.startsWith('v_');
// A face spec is a preset name or {preset?, eyes?, brows?, mouth?, ...overrides, add?}. A viseme mouth on top of an
// expression keeps the expression's eyes / brows / add-ons but drops its mouth scale and offsets (m, mouthDX, mouthDY,
// mouthTilt) unless the spec sets them itself, so every viseme has one size per character.
export function resolve(spec) {
  if (!spec) return { ...PRESETS.neutral };
  if (typeof spec === 'string') return { ...(PRESETS[spec] || PRESETS.neutral) };
  const base = spec.preset ? PRESETS[spec.preset] || {} : {};
  const out = { ...base, ...spec, add: { ...(base.add || {}), ...(spec.add || {}) } };
  if (isViseme(spec.mouth) && !isViseme(base.mouth)) for (const k of ['m', 'mouthDX', 'mouthDY', 'mouthTilt']) if (spec[k] === undefined) delete out[k];
  return out;
}
// ---------- face morph ----------
// {preset: 'starstruck', to: 'scared', k} draws a clean shrink-swap-grow between two faces (no double features):
// k 0..0.5 the first face's eyes and mouth shrink, k 0.5..1 the second face's pop open (outBack); brows and look
// glide; add-ons switch at 0.5. k is clamped, so a shot can drive it straight from a time segment.
const outBack = (x) => { const c = 1.9; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2; };
export function morph(spec) {
  const k = Math.max(0, Math.min(1, +spec.k || 0));
  const { to, k: _k, ...rest } = spec; void _k;
  const A = resolve(rest), B = resolve(to);
  const second = k >= 0.5;
  const u = second ? (k - 0.5) / 0.5 : k / 0.5;
  const out = { ...(second ? B : A) };
  if (isViseme(rest.mouth)) { out.mouth = rest.mouth; out.m = rest.m; delete out.mouthDX; delete out.mouthDY; delete out.mouthTilt; }   // lip-sync wins over both faces
  out.featK = second ? 0.3 + 0.7 * outBack(u) : 1 - 0.7 * u * u;
  out.browMix = { a: A.brows, b: B.brows, k: k < 0.15 ? 0 : k > 0.85 ? 1 : (k - 0.15) / 0.7, sa: A.browScale ?? 1, sb: B.browScale ?? 1 };
  const la = A.look || [0, 0], lb = B.look || [0, 0];
  out.look = [la[0] + (lb[0] - la[0]) * k, la[1] + (lb[1] - la[1]) * k];
  return out;
}

// ---------- add-ons ----------
function sweatDrop(x, y, s = 1, rot = 12) {
  const c = PAL.sweat;
  return g(path(dropPath(s), { fill: grad(c, 'd', { up: 0.05, down: 0.1 }), stroke: stroke(c), strokeWidth: f1(2.2 * s), strokeLinejoin: 'round' })
    + ellipse(-2 * s, 1.5 * s, 1.5 * s, 2.6 * s, { fill: '#FFFFFF', opacity: 0.85 }), { transform: `translate(${f1(x)} ${f1(y)}) rotate(${rot})` });
}
function qMark(x, y, size, rot = 10) {
  return g(text(0, 0, '?', { fontFamily: FONT_DISPLAY, fontSize: size, fill: '#FFFFFF', stroke: '#2A2346', strokeWidth: f1(size * 0.14), strokeLinejoin: 'round', paintOrder: 'stroke', textAnchor: 'middle' }), { transform: `translate(${f1(x)} ${f1(y)}) rotate(${rot})` });
}
function zMark(x, y, size) {
  return text(x, y, 'Z', { fontFamily: FONT_DISPLAY, fontSize: size, fill: '#C9D6FF', stroke: '#3B3A7A', strokeWidth: f1(size * 0.13), strokeLinejoin: 'round', paintOrder: 'stroke', textAnchor: 'middle' });
}
function smallStar(x, y, R, rot = 0) {
  const c = PAL.star;
  return path(roundedStar(R, 0.5), { fill: grad(c, 'd'), stroke: stroke(c), strokeWidth: f1(R * 0.22), strokeLinejoin: 'round', transform: `translate(${f1(x)} ${f1(y)}) rotate(${rot})` });
}
function smallHeart(x, y, s, rot = 0) {
  const c = PAL.heart;
  return g(path(heartPath(s), { fill: grad(c, 'd'), stroke: stroke(c), strokeWidth: f1(2.4 * s), strokeLinejoin: 'round' }) + ellipse(-4.6 * s, -5 * s, 2.2 * s, 1.5 * s, { fill: '#FFFFFF', opacity: 0.85, transform: `rotate(-30 ${f1(-4.6 * s)} ${f1(-5 * s)})` }), { transform: `translate(${f1(x)} ${f1(y)}) rotate(${rot})` });
}

// hanging tongue (k = length 0..1.5) under any mouth: from the lower lip, a soft U with a centre crease
function tongue(k, mouth) {
  const t = PAL.tongue, y0 = mouth === 'dogPant' ? 9 : mouth === 'dogW' || mouth === 'cat' ? 1 : mouth === 'smile' ? 2.5 : 4;
  const L = 6 + 12 * k, w = 6.4;
  const d = `M${f1(-w)} ${f1(y0)}L${f1(-w)} ${f1(y0 + L - w)}A${f1(w)} ${f1(w)} 0 0 0 ${f1(w)} ${f1(y0 + L - w)}L${f1(w)} ${f1(y0)}Z`;
  return path(d, { fill: grad(t, 'd'), stroke: stroke(t), strokeWidth: LINE * 0.8, strokeLinejoin: 'round' })
    + ln(`M0 ${f1(y0 + 1.5)}L0 ${f1(y0 + L * 0.62)}`, 1.5, stroke(t)) + path(`M${f1(-w * 0.45)} ${f1(y0 + 3)}L${f1(-w * 0.45)} ${f1(y0 + L * 0.5)}`, { stroke: '#FFFFFF', strokeOpacity: 0.45, strokeWidth: 1.6, strokeLinecap: 'round', fill: 'none' });
}
// the mannequin's blank face: no features, just two soft eye sockets and a nose ridge moulded in the plastic
export function blankFace(opts = {}) {
  const yaw = opts.yaw || 0, eyeX = opts.eyeX ?? 19, eyeY = opts.eyeY ?? 5, skin = opts.skin || PAL.skinCool;
  const side = Math.abs(yaw) > 75, back = Math.abs(yaw) > 120;
  if (back) return '';
  const dk = tone(skin, -0.07, 1.1);
  let s = '';
  for (const sd of [-1, 1]) {
    const m = mapFeature(sd * eyeX, yaw); if (m.k < 0.25 || (side && sd * yaw > 0)) continue;
    s += ellipse(m.x, eyeY + 1, 10.5 * m.k, 6.5, { fill: dk, opacity: 0.35 }) + ellipse(m.x - 2 * m.k, eyeY - 2.5, 6 * m.k, 2, { fill: '#FFFFFF', opacity: 0.35 });
  }
  const n = mapFeature(0, yaw), ny = ((opts.mouthY ?? 28) + eyeY) / 2 + 2;
  s += path(`M${f1(n.x - 1.5)} ${f1(eyeY + 5)}Q${f1(n.x + 3.5 * Math.max(0.4, n.k) + yaw * 0.03)} ${f1(ny)} ${f1(n.x - 2)} ${f1(ny + 3)}`, { fill: 'none', stroke: dk, strokeOpacity: 0.55, strokeWidth: 2.4, strokeLinecap: 'round' });
  s += path(`M${f1(n.x - 6 * n.k)} ${f1((opts.mouthY ?? 28) + 1)}Q${f1(n.x)} ${f1((opts.mouthY ?? 28) + 2.5)} ${f1(n.x + 6 * n.k)} ${f1((opts.mouthY ?? 28) + 1)}`, { fill: 'none', stroke: dk, strokeOpacity: 0.3, strokeWidth: 2.2, strokeLinecap: 'round' });
  return s;
}

// ---------- the face ----------
// opts: { yaw, skin, eyeX, eyeY, eyeR, browY, browLen, mouthY, mouthScale, gap, freckles, top (head top y for add-ons),
//         look (override), browColor, cat }
export function face(spec, opts = {}) {
  const e = spec && typeof spec === 'object' && spec.to ? morph(spec) : resolve(spec);
  const featK = e.featK ?? 1;
  const yaw = opts.yaw || 0;
  const eyeX = opts.eyeX ?? 19, eyeY = opts.eyeY ?? 5, eyeR = (opts.eyeR ?? 12.4), browY = opts.browY ?? eyeY - 19.5;
  const mouthY = opts.mouthY ?? 28, mScale = (opts.mouthScale ?? 1) * (e.m ?? 1);
  const look = opts.look || e.look || [0, 0];
  const yawLook = Math.sin((yaw * Math.PI) / 180) * 3.5;
  const side = Math.abs(yaw) > 75;              // profile: hide the far eye / brow
  const back = Math.abs(yaw) > 120;
  const top = opts.top ?? -60;
  let out = '', fx = '';
  if (back) return { face: '', fx: addons(e, { ...opts, top, eyeX, eyeY, yaw, mouthY, back: true }).fx };

  // gloom: cool shade washing down from the hairline (disgust / dread), under the features
  if (e.add?.gloom && opts.headBox) {
    const hb = opts.headBox;
    const gid = fxDef('gloomshade', `<linearGradient id="gloomshade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4B3FA8" stop-opacity="0.5"/><stop offset="0.5" stop-color="#4B3FA8" stop-opacity="0.12"/><stop offset="0.62" stop-color="#4B3FA8" stop-opacity="0"/></linearGradient>`);
    out += path(`M-50 ${f1(hb.top + hb.r)}A${hb.r} ${hb.r} 0 0 1 ${f1(-50 + hb.r)} ${f1(hb.top)}H${f1(50 - hb.r)}A${hb.r} ${hb.r} 0 0 1 50 ${f1(hb.top + hb.r)}V${f1(hb.bot - hb.r)}A${hb.r} ${hb.r} 0 0 1 ${f1(50 - hb.r)} ${f1(hb.bot)}H${f1(-50 + hb.r)}A${hb.r} ${hb.r} 0 0 1 -50 ${f1(hb.bot - hb.r)}Z`, { fill: `url(#${gid})` });
    for (const x of [-30, -20, 20, 30]) out += path(`M${x} ${f1(eyeY - 2)}L${x} ${f1(eyeY + 6)}`, { stroke: '#4B3FA8', strokeWidth: 2.4, strokeLinecap: 'round', opacity: 0.0 });
  }
  // blush & freckles first (under features)
  const cheekY = eyeY + 13;
  for (const s of [-1, 1]) {
    const m = mapFeature(s * (eyeX + 12), yaw); if (m.k < 0.25 || (side && s * yaw > 0)) continue;
    if (e.add?.blush) out += ellipse(m.x, cheekY, 7.2 * m.k, 4, { fill: PAL.blush, opacity: 0.5 * Math.min(1, e.add.blush) });
    if (opts.freckles) {
      for (const [dx, dy, r] of [[-3.2, -0.8, 1.15], [0.6, 1.4, 1.05], [3.6, -0.6, 1.1], [1.2, -3, 0.9]]) out += circle(m.x + dx * m.k * -s, cheekY + dy - 1, r, { fill: tone(opts.skin || PAL.skinCool, -0.2, 2.2, -8), opacity: 0.75 });
    }
  }
  // eyes + brows
  for (const s of [-1, 1]) {
    const per = s < 0 ? e.eyeL : e.eyeR;
    const type = per?.type || e.eyes;
    const m = mapFeature(s * eyeX, yaw);
    if (m.k < 0.2 || (side && s * yaw > 0)) continue;
    const sc = per?.scale ?? 1, r = eyeR * sc * featK;
    const p = { look: [look[0] + yawLook, look[1]], pupil: e.pupil, lid: e.lid, tilt: e.tilt, lower: e.lower, lowerTilt: e.lowerTilt, ...(per || {}) };
    if (per?.look) p.look = [per.look[0] + yawLook, per.look[1]];
    let body = (EYES[type] || EYES.bean)(r, s, p);
    if (opts.lashes && ['ring', 'bean', 'half', 'angry', 'pin', 'teary', 'squint'].includes(type)) {
      // two flicks at the outer upper corner (sit on the lid line when lidded)
      const rr = type === 'bean' ? r * 0.82 : type === 'pin' ? r * 1.08 : r;
      const lidY = p.lid != null ? p.lid * rr : -Math.sqrt(0.5) * rr;
      const ax = s * Math.sqrt(Math.max(0, rr * rr - lidY * lidY)), ay = lidY;
      body += ln(`M${f1(ax)} ${f1(ay)}L${f1(ax + s * 5.5)} ${f1(ay - 4.5)}`, 3) + ln(`M${f1(ax - s * 3)} ${f1(ay - 2.2)}L${f1(ax + s * 1)} ${f1(ay - 7.5)}`, 3);
    }
    out += g(body, { transform: `translate(${f1(m.x)} ${f1(eyeY)}) scale(${f1(Math.max(0.3, m.k) * 100) / 100} 1)` });
    let bType = e.browOverride || e.brows;
    let bs = e.browScale ?? 1;
    if (e.browMix) {
      const M = e.browMix, a = browSpec(M.a, s), b = browSpec(M.b, s);
      if (a && b) { bType = a.map((v, i) => v + (b[i] - v) * M.k); bs = M.sa + (M.sb - M.sa) * M.k; } else bType = M.k < 0.5 ? M.a : M.b;
    }
    if (bType && bType !== 'none') {
      const bm = mapFeature(s * (eyeX + 1), yaw);
      const by = browY - (sc - 1) * eyeR * 0.9;
      let bb = brow(bType, s, { x: 0, y: by, len: (opts.browLen ?? 16), k: 1, w: (opts.browW ?? BROW), color: opts.browColor || INK });
      if (bs !== 1) bb = g(bb, { transform: `translate(0 ${f1(by)}) scale(1 ${bs}) translate(0 ${f1(-by)})` });
      out += g(bb, { transform: `translate(${f1(bm.x)} 0) scale(${f1(Math.max(0.3, bm.k) * 100) / 100} 1)` });
    }
  }
  // cat muzzle: nose sits between eyes and mouth
  if (opts.cat) {
    const m = mapFeature(0, yaw);
    const ny = mouthY - 8.5;
    out += g(path('M-4.6 -2.4Q0 -3.6 4.6 -2.4Q3.4 1.6 0 2.6Q-3.4 1.6 -4.6 -2.4Z', { fill: PAL.catNose, stroke: stroke(PAL.catNose), strokeWidth: 1.8, strokeLinejoin: 'round' }), { transform: `translate(${f1(m.x)} ${f1(ny)}) scale(${f1(Math.max(0.35, m.k))} 1)` });
  }
  // mouth (opts.mouthShift moves it sideways, e.g. onto a dog's muzzle in profile); optional hanging tongue
  {
    const m = mapFeature(0, yaw);
    const fn = MOUTHS[e.mouth] || MOUTHS.smile;
    const tilt = e.mouthTilt || 0;
    const ms = mScale * (e.featK ? 0.5 + 0.5 * featK : 1);
    let mo = fn({ gap: opts.gap });
    const tg = opts.tongue ?? e.tongue ?? 0;
    if (tg > 0 && e.mouth !== 'none') mo += tongue(tg, e.mouth);
    // visemes keep a readable width in profile (expression mouths keep their original squeeze)
    const vis = isViseme(e.mouth) && Math.abs(yaw) > 50;
    const kx = vis ? Math.max(0.7, m.k) : Math.max(0.4, m.k), dx = vis ? -Math.sign(yaw) * (0.7 - Math.min(0.7, m.k)) * 9 : 0;
    out += g(mo, { transform: `translate(${f1(m.x + dx + (e.mouthDX || 0) + (opts.mouthShift || 0))} ${f1(mouthY + (e.mouthDY || 0))}) rotate(${tilt}) scale(${f1(ms * kx * 100) / 100} ${f1(ms * 100) / 100})` });
  }
  const a = addons(e, { ...opts, top, eyeX, eyeY, eyeR, yaw, mouthY });
  return { face: out + a.face, fx: a.fx };
}

function addons(e, o) {
  const A = e.add || {};
  let face = '', fx = '';
  const yaw = o.yaw || 0, dir = Math.sin((yaw * Math.PI) / 180);
  const top = o.top;
  if (A.tears && !o.back) {
    for (const s of [-1, 1]) {
      const m = mapFeature(s * o.eyeX, yaw); if (m.k < 0.3) continue;
      const x = m.x, y0 = o.eyeY + o.eyeR * 0.55;
      const d = `M${f1(x - 3.4)} ${f1(y0)}Q${f1(x - 5)} ${f1(y0 + 18)} ${f1(x - 3.6)} ${f1(y0 + 36)}L${f1(x + 3.6)} ${f1(y0 + 36)}Q${f1(x + 5)} ${f1(y0 + 18)} ${f1(x + 3.4)} ${f1(y0)}Z`;
      face += path(d, { fill: PAL.tear, opacity: 0.85, stroke: stroke(PAL.tear), strokeWidth: 1.6, strokeOpacity: 0.6 }) + path(`M${f1(x - 1.4)} ${f1(y0 + 5)}L${f1(x - 1.6)} ${f1(y0 + 28)}`, { stroke: '#FFFFFF', strokeWidth: 1.5, strokeLinecap: 'round', opacity: 0.8, fill: 'none' });
    }
    fx += sweatDrop(-o.eyeX - 22, o.eyeY + 2, 0.55, -50) + sweatDrop(o.eyeX + 22, o.eyeY + 2, 0.55, 50);
  }
  if (A.joy && !o.back) fx += sweatDrop(-o.eyeX - 17, o.eyeY - 2, 0.5, -60) + sweatDrop(o.eyeX + 17, o.eyeY - 2, 0.5, 60);
  if (A.sweat) {
    // sweatSize: overall scale (pop it 0 -> 1.2 -> 1 over 6 frames); sweatK 0..1: the drop slides 20 units down the
    // temple and grows x1.4 (bible 3.2), so a line can 'grow' the drop by animating sweatK
    const sk = Math.max(0, Math.min(1.5, A.sweatK ?? 0)), sz = (A.sweatSize ?? 1) * (1 + 0.4 * sk);
    const sx = o.back ? -36 : 38 + dir * 4, sy = -22 + 20 * sk;
    if (sz > 0.01) fx += sweatDrop(sx + 2 * sk, sy, 0.95 * sz, 14 - 6 * sk);
    if (A.sweat > 1 && sz > 0.01) fx += sweatDrop(-sx - 2, -14 + 14 * sk, 0.7 * sz, -14);
  }
  if (A.vein) {
    const x = 33, y = -24, c = '#FF3B5C', sc = stroke(c);
    const v = (r) => path(`M${f1(-7)} ${f1(-2.2)}Q-2.2 -2.2 -2.2 -7`, { fill: 'none', stroke: sc, strokeWidth: 5.2, strokeLinecap: 'round', transform: `rotate(${r})` }) + path(`M${f1(-7)} ${f1(-2.2)}Q-2.2 -2.2 -2.2 -7`, { fill: 'none', stroke: c, strokeWidth: 2.8, strokeLinecap: 'round', transform: `rotate(${r})` });
    fx += g(v(0) + v(90) + v(180) + v(270), { transform: `translate(${x} ${y})` });
  }
  if (A.shock) {
    // emphasis ticks fanning out from the upper corners of the head
    let s = '';
    for (const sd of [-1, 1]) for (const [ang, l] of [[-62, 11], [-34, 13], [-6, 10]]) {
      const t = (ang * Math.PI) / 180, ux = sd * Math.cos(t), uy = Math.sin(t), x0 = sd * 46, y0 = top + 30;
      s += path(`M${f1(x0 + ux * 16)} ${f1(y0 + uy * 16)}L${f1(x0 + ux * (16 + l))} ${f1(y0 + uy * (16 + l))}`, { stroke: '#2A2346', strokeWidth: 3.6, strokeLinecap: 'round', fill: 'none' });
    }
    fx += s;
  }
  if (A.q) { fx += qMark(54, top + 30, 34, 12); if (A.q > 1) fx += qMark(70, top + 40, 24, 22); }
  if (A.zzz) fx += zMark(46, top + 38, 17) + zMark(58, top + 25, 22) + zMark(71, top + 10, 26);
  if (A.hearts) fx += smallHeart(54, top + 22, 0.75, 14) + smallHeart(-56, top + 30, 0.55, -16) + smallHeart(66, top + 46, 0.45, 24);
  if (A.sparkle) fx += twinkle(-60, top + 34, 8) + twinkle(60, top + 24, 10) + twinkle(68, top + 46, 5) + twinkle(-50, top + 16, 4.5);
  if (A.dizzy) {
    const cy = top + 16;
    fx += ellipse(0, cy, 40, 9, { fill: 'none', stroke: '#FFE27A', strokeWidth: 2.2, opacity: 0.8 });
    for (const [a, r] of [[200, 7], [290, 6], [20, 7.5], [110, 5.5]]) { const t = (a * Math.PI) / 180; fx += smallStar(Math.cos(t) * 40, cy + Math.sin(t) * 9, r, a / 3); }
  }
  if (A.bump) {
    const c = o.skin || PAL.skinCool;
    fx += path('M-12 0Q-12 -14 0 -14Q12 -14 12 0Z', { fill: grad(c, 'd'), stroke: stroke(c), strokeWidth: 3, strokeLinejoin: 'round', transform: `translate(8 ${f1(top + 8)})` })
      + smallStar(-14, top - 6, 6, 10) + smallStar(30, top - 10, 5, -10);
  }
  return { face, fx };
}

// convenience: a free-floating face (for icons / tests)
export function faceIcon(spec, { size = 100, skin = PAL.skinCool } = {}) {
  const f = face(spec, { skin });
  return g(f.face + f.fx, { transform: `scale(${size / 100})` });
}
