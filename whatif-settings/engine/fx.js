// Motion FX for "What If Real Life Had a SETTINGS MENU?" (bible 3.4): starbursts, speed lines, sparkles, flash frames,
// glitch slices, confetti, shock rings, god rays. Pure functions -> SVG strings, deterministic (seeded, closed-form in t).
// Convention: p = 0..1 progress through the effect's own life; t = seconds (for looping motion).
import { W, H, Defs, f, clamp, lerp, seg, ease, rng, shade, ink, g, rect, circle, ellipse, line, poly, path, tr, st, starPts, gearPath } from './ui_style.js';

const ptsD = (arr) => arr.map((q, i) => (i ? 'L' : 'M') + f(q[0]) + ' ' + f(q[1])).join('') + 'Z';

/** comic starburst: irregular 10-16 points, dark rim, lighter middle, hot core. Pops 0 -> 1.18 -> 1 over p 0..0.45. */
export function starburst(o = {}, p = 1) {
  const { cx = 960, cy = 540, r = 320, points = 14, rot = 0, seed = 3, jitter = 0.32 } = o;
  const fill = o.fill || '#FF6A3D', rim = o.rim || ink(fill, 0.28), core = o.core || '#FFE36A';
  if (p <= 0) return '';
  const k = p < 0.45 ? lerp(0.2, 1.18, ease.outCubic(p / 0.45)) : lerp(1.18, 1, ease.inOutSine(seg(p, 0.45, 0.8)));
  const fade = o.fadeOut ? 1 - seg(p, 0.75, 1) : 1;
  const d = new Defs();
  const outer = starPts(0, 0, points, r, r * 0.52, rot - 90, jitter, seed);
  const mid = starPts(0, 0, points, r * 0.74, r * 0.42, rot - 90, jitter, seed);
  let s = path(ptsD(outer), { fill: d.lin([shade(fill, 0.06), shade(fill, -0.06)]), stroke: rim, strokeWidth: Math.max(4, r * 0.035), strokeLinejoin: 'round' });
  s += path(ptsD(mid), { fill: shade(fill, 0.1), opacity: 0.9 });
  if (core !== 'none') s += circle(0, 0, r * 0.34, { fill: d.rad([[0, '#FFFFFF'], [0.45, core], [1, core, 0]]) });
  return d + g(s, { transform: `translate(${f(cx)} ${f(cy)}) scale(${f(k * 1000) / 1000})`, opacity: f(fade * 100) / 100 });
}

/** speed lines. mode 'radial' (zoom burst from cx,cy) or 'dir' (parallel streaks along angle). t scrolls them. */
export function speedLines(o = {}) {
  const { cx = 960, cy = 540, mode = 'radial', count = 40, color = '#FFFFFF', seed = 9, t = 0, op = 0.85 } = o;
  const R = rng(seed);
  let s = '';
  if (mode === 'radial') {
    const r0 = o.r0 ?? 320, r1 = o.r1 ?? 1500;
    for (let i = 0; i < count; i++) {
      const a = (i / count) * Math.PI * 2 + (R() - 0.5) * 0.12, w = (o.width ?? 18) * (0.5 + R());
      const ph = (R() + t * 1.6) % 1, a0 = r0 + (r1 - r0) * ph * 0.5, len = (r1 - r0) * (0.25 + R() * 0.35);
      const x0 = cx + Math.cos(a) * a0, y0 = cy + Math.sin(a) * a0, x1 = cx + Math.cos(a) * (a0 + len), y1 = cy + Math.sin(a) * (a0 + len);
      const nx = -Math.sin(a) * w / 2, ny = Math.cos(a) * w / 2;
      s += poly([[x0, y0], [x1 + nx, y1 + ny], [x1 - nx, y1 - ny]], { fill: color, opacity: f(op * (0.5 + R() * 0.5) * 100) / 100 });
    }
  } else {
    const ang = ((o.angle ?? 0) * Math.PI) / 180, dx = Math.cos(ang), dy = Math.sin(ang);
    for (let i = 0; i < count; i++) {
      const off = (R() - 0.5) * 2400, len = 200 + R() * 500, w = (o.width ?? 10) * (0.5 + R());
      const along = ((R() * 3000 + t * (o.speed ?? 4000)) % 3000) - 1500;
      const mx = W / 2 + dx * along - dy * off, my = H / 2 + dy * along + dx * off;
      const x0 = mx - dx * len / 2, y0 = my - dy * len / 2, x1 = mx + dx * len / 2, y1 = my + dy * len / 2;
      s += path(`M${f(x0)} ${f(y0)}L${f(x1)} ${f(y1)}`, { fill: 'none', ...st(color, w), opacity: f(op * (0.4 + R() * 0.6) * 100) / 100 });
    }
  }
  return s;
}

/** one 4-point twinkle star */
export function sparkle(x, y, r, color = '#FFFFFF', op = 1, rot = 0) {
  const k = 0.17;
  const d = `M0 ${-r}Q${r * k} ${-r * k} ${r} 0Q${r * k} ${r * k} 0 ${r}Q${-r * k} ${r * k} ${-r} 0Q${-r * k} ${-r * k} 0 ${-r}Z`;
  return path(d.replace(/(-?\d+\.?\d*)/g, (m) => f(+m)), { fill: color, opacity: f(op * 100) / 100, transform: `translate(${f(x)} ${f(y)})${rot ? ` rotate(${f(rot)})` : ''}` });
}
/** a field of twinkles in a box; each one breathes on its own phase (t seconds) */
export function sparkles(o = {}) {
  const { x = 0, y = 0, w = W, h = H, count = 14, seed = 5, t = 0, colors = ['#FFFFFF', '#FFF4B0', '#BFE8FF'], size = 22 } = o;
  const R = rng(seed);
  let s = '';
  for (let i = 0; i < count; i++) {
    const px = x + R() * w, py = y + R() * h, ph = R() * Math.PI * 2, sp = 3 + R() * 4;
    const k = 0.35 + 0.65 * Math.max(0, Math.sin(t * sp + ph));
    s += sparkle(px, py, size * (0.5 + R() * 0.8) * k, colors[i % colors.length], 0.5 + 0.5 * k, t * 40 * (R() - 0.5));
  }
  return s;
}

/** flash frame. mode 'solid' (full colour) or 'screen'; p 0..1 over 4-6 frames: snap on, decay out */
export function flash(o = {}, p = 0) {
  const { color = '#FFFFFF', mode = 'screen', peak = mode === 'solid' ? 1 : 0.85 } = o;
  if (p <= 0 || p >= 1) return '';
  const a = p < 0.15 ? peak : peak * (1 - ease.outQuad(seg(p, 0.15, 1)));
  return rect(-200, -200, W + 400, H + 400, { fill: color, opacity: f(a * 100) / 100, style: mode === 'screen' ? 'mix-blend-mode:screen' : undefined });
}

/** expanding shock ring (impact kit): r 0 -> R over p */
export function shockRing(cx, cy, R, p, color = '#FFFFFF', w = 18) {
  if (p <= 0 || p >= 1) return '';
  const e = ease.outCubic(p);
  return circle(cx, cy, R * e, { fill: 'none', stroke: color, strokeWidth: f(w * (1 - e) + 1), opacity: f((1 - p) * 100) / 100 });
}

/** god rays: alternating wedges rotating slowly; screen blend */
export function godRays(o = {}) {
  const { cx = 960, cy = 540, count = 20, r = 1800, rot = 0, a = '#FFE36A', b = '#FFFFFF', op = 0.55 } = o;
  const d = new Defs();
  let s = '';
  for (let i = 0; i < count; i++) {
    const a0 = ((i / count) * 360 + rot) * Math.PI / 180, a1 = a0 + (Math.PI * 2) / count * 0.5;
    s += poly([[cx, cy], [cx + Math.cos(a0) * r, cy + Math.sin(a0) * r], [cx + Math.cos(a1) * r, cy + Math.sin(a1) * r]], { fill: i % 2 ? b : a, opacity: i % 2 ? 0.5 : 0.7 });
  }
  const mask = d.raw('mk', `<mask id="__ID__" maskUnits="userSpaceOnUse" x="-4000" y="-4000" width="8000" height="8000"><circle cx="${cx}" cy="${cy}" r="${r}" fill="url(#rfade${Math.round(cx)}_${Math.round(cy)})"/></mask>`);
  const fadeDef = `<radialGradient id="rfade${Math.round(cx)}_${Math.round(cy)}" gradientUnits="userSpaceOnUse" cx="${cx}" cy="${cy}" r="${r}"><stop offset="0" stop-color="#fff"/><stop offset="0.75" stop-color="#fff" stop-opacity="0.25"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>`;
  return `<defs>${fadeDef}</defs>` + d + g(s, { mask: `url(#${mask})`, opacity: op, style: 'mix-blend-mode:screen' });
}

/** confetti: closed-form ballistic pieces (rects, dots and tiny gears) from (cx,cy); t seconds since burst */
export function confetti(o = {}) {
  const { cx = 960, cy = 540, count = 70, seed = 12, t = 0.5, spread = 1100, up = 1500, gravity = 2200, colors = ['#FF7A3D', '#FFD43B', '#2FD27C', '#3CCBFF', '#A779FF', '#FF66B0'] } = o;
  if (t <= 0) return '';
  const R = rng(seed);
  let s = '';
  for (let i = 0; i < count; i++) {
    const vx = (R() - 0.5) * spread * 2, vy = -up * (0.5 + R() * 0.7), drag = 1 - Math.min(0.6, t * 0.35);
    const x = cx + vx * t * drag, y = cy + vy * t * drag + 0.5 * gravity * t * t * 0.55;
    const rot = (R() - 0.5) * 900 * t + R() * 360, flip = Math.cos(t * (8 + R() * 10) + R() * 6);
    const c = colors[i % colors.length], kind = i % 7, sz = (o.size ?? 22) * (0.7 + R() * 0.6);
    const fade = 1 - seg(t, 1.6, 2.4);
    if (fade <= 0) continue;
    let piece;
    if (kind === 6) piece = path(gearPath(0, 0, sz * 0.7, sz * 0.5, 6, 0, 0.5), { fill: c }) + circle(0, 0, sz * 0.2, { fill: shade(c, -0.15) });
    else if (kind === 5) piece = circle(0, 0, sz * 0.45, { fill: c });
    else piece = rect(-sz / 2, -sz * 0.3, sz, sz * 0.6, { fill: c, rx: 2 }) + rect(-sz / 2, -sz * 0.3, sz, sz * 0.18, { fill: '#FFFFFF', opacity: 0.4, rx: 2 });
    s += g(piece, { transform: `translate(${f(x)} ${f(y)}) rotate(${f(rot)}) scale(1 ${f(Math.max(0.15, Math.abs(flip)) * 100) / 100})`, opacity: f(fade * 100) / 100 });
  }
  return s;
}

/** glitch slices: wraps `inner` so horizontal bands of it are displaced, with RGB-split fringes and corrupt bars.
 *  amount = max band offset in px; seed picks bands; t re-rolls them every frame when animating. */
export function glitch(inner, o = {}) {
  const { seed = 4, bands = 7, amount = 90, rgb = 10, t = 0, bars = true } = o;
  const R = rng(seed + Math.floor(t * 30) * 7919);
  const d = new Defs();
  const src = d.raw('gs', `<g id="__ID__">${inner}</g>`);
  // Each band is a displaced plain <use> copy. The RGB fringe is faked with a tinted band and bright edge lines:
  // filtered / blend-moded <use> copies of a big scene are dropped unpredictably by Chromium (seen at 1x and 2x).
  let s = `<use href="#${src}"/>`;
  for (let i = 0; i < bands; i++) {
    const by = R() * H, bh = 14 + R() * 110, dx = (R() - 0.5) * 2 * amount, tint = R() < 0.5 ? '#FF2BD6' : '#33E8FF';
    const cp = d.clip(rect(-40, by, W + 80, bh));
    let band = `<use href="#${src}" transform="translate(${f(dx)} 0)"/>`;
    if (rgb) {
      band += rect(-40, by, W + 80, bh, { fill: tint, opacity: 0.13 });
      band += rect(-40, by, W + 80, Math.min(4, bh / 4), { fill: dx > 0 ? '#33E8FF' : '#FF2BD6', opacity: 0.8 });
      band += rect(-40, by + bh - Math.min(4, bh / 4), W + 80, Math.min(4, bh / 4), { fill: dx > 0 ? '#FF2BD6' : '#33E8FF', opacity: 0.8 });
    }
    s += g(band, { clipPath: cp });
    if (bars && R() < 0.45) s += rect(-50, by + bh * R(), W + 100, 3 + R() * 8, { fill: R() < 0.5 ? '#FF2BD6' : '#33E8FF', opacity: 0.5 });
  }
  return d + s;
}

/** soft vignette (night / sky-only / flashback shots only, per the bible) */
export function vignette(color = '#120C2E', strength = 0.45) {
  const d = new Defs();
  return d + rect(-100, -100, W + 200, H + 200, { fill: d.rad([[0.55, color, 0], [1, color, strength]], 0.5, 0.5, 0.75) });
}

// =====================================================================================================================
// hook additions (S00): ripple boom, sun flare, white blow-out, cracked glass, scroll streaks, box blur
// =====================================================================================================================
const TAU = Math.PI * 2;
const op2 = (v) => f(clamp(v) * 100) / 100;

/** ripple({cx, cy, R, rings, color, squash, fill}, p) - the I AGREE sub-boom wave: `rings` concentric bands leave
 *  (cx, cy) one after another (stagger .14 of p), each a thick soft band with a bright leading edge, out to radius R
 *  (default: past the frame corners); squash < 1 flattens them into floor-plane ellipses. p 0..1 over ~0.8 s. */
export function ripple(o = {}, p = 0) {
  const { cx = 960, cy = 540, rings = 3, color = '#7CF0B0', squash = 1, fill = true } = o;
  if (p <= 0 || p >= 1) return '';
  const R = o.R ?? Math.hypot(Math.max(cx, W - cx), Math.max(cy, H - cy)) * 1.15;
  let s = '';
  for (let j = 0; j < rings; j++) {
    const q = clamp((p - j * 0.14) / (1 - (rings - 1) * 0.14));
    if (q <= 0 || q >= 1) continue;
    const e = ease.outCubic(q), r = R * e, a = 1 - q;
    const bw = lerp(120, 26, e);
    if (fill && j === 0) s += ellipse(cx, cy, r, r * squash, { fill: color, opacity: op2(a * 0.12) });
    s += ellipse(cx, cy, Math.max(0, r - bw * 0.5), Math.max(0, (r - bw * 0.5) * squash), { fill: 'none', stroke: color, strokeWidth: f(bw), opacity: op2(a * 0.28) });
    s += ellipse(cx, cy, r, r * squash, { fill: 'none', stroke: '#FFFFFF', strokeWidth: f(lerp(14, 3, e)), opacity: op2(a * 0.9) });
  }
  return s;
}

/** sunFlare({cx, cy, r, k, t, rays, ghosts, color}) - the moon flaring into a sun: hot white core and yellow bloom
 *  (radial gradients, no filters), 8 thin rotating spikes, a horizontal anamorphic streak, lens ghosts along the line
 *  from the sun through the frame centre, plus godRays when rays:true. k 0..1 = intensity (scales everything). */
export function sunFlare(o = {}) {
  const { cx = 1500, cy = 260, r = 110, t = 0, color = '#FFE36A' } = o;
  const k = clamp(o.k ?? 1);
  if (k <= 0) return '';
  const d = new Defs();
  let s = '';
  if (o.rays) s += godRays({ cx, cy, rot: t * 20, op: 0.45 * k, count: 22, a: color, b: '#FFFFFF' });
  s += circle(cx, cy, r * (3.2 + 2.4 * k), { fill: d.rad([[0, '#FFFFFF', 0.95 * k], [0.18, color, 0.75 * k], [0.5, '#FFB21F', 0.25 * k], [1, '#FFB21F', 0]]) });
  for (let i = 0; i < 8; i++) {
    const a = (i / 8) * TAU + t * 0.25 + (i % 2) * 0.12, L = r * (i % 2 ? 3.2 : 5.2) * (0.6 + 0.4 * k), wd = r * (i % 2 ? 0.09 : 0.14);
    const ax = Math.cos(a), ay = Math.sin(a), nx = -ay, ny = ax;
    s += poly([[cx + nx * wd, cy + ny * wd], [cx + ax * L, cy + ay * L], [cx - nx * wd, cy - ny * wd]], { fill: '#FFFFFF', opacity: op2(0.75 * k) });
  }
  s += ellipse(cx, cy, r * 9 * k, r * 0.16, { fill: d.rad([[0, '#FFFFFF', 0.9 * k], [0.4, color, 0.45 * k], [1, color, 0]]) });
  s += circle(cx, cy, r, { fill: d.rad([[0, '#FFFFFF'], [0.7, '#FFFBE0'], [1, color]]) });
  if (o.ghosts !== false) {
    const vx = 960 - cx, vy = 540 - cy, ghosts = [[0.45, 0.35, '#B6FFB0'], [0.8, 0.18, '#FFB0E0'], [1.25, 0.55, '#B0E4FF'], [1.6, 0.25, '#FFE6A0']];
    for (const [u, rr, c] of ghosts) {
      const gx = cx + vx * u * 2, gy = cy + vy * u * 2, R6 = r * rr * 1.6;
      const hex = [...Array(6)].map((_, i) => [gx + Math.cos((i / 6) * TAU + 0.3) * R6, gy + Math.sin((i / 6) * TAU + 0.3) * R6]);
      s += poly(hex, { fill: c, opacity: op2(0.22 * k) }) + poly(hex, { fill: 'none', stroke: '#FFFFFF', strokeWidth: 3, opacity: op2(0.3 * k) });
    }
  }
  return d + s;
}

/** whiteout({cx, cy, color, tint}, k) - the room blows out white: k 0..0.5 grows a bloom from (cx, cy), 0.5..1 fills
 *  the frame; plain opacity (no blend modes), frame-sized. */
export function whiteout(o = {}, k = 0) {
  const { cx = 960, cy = 540, color = '#FFFFFF', tint = '#FFF4D6' } = o;
  k = clamp(k);
  if (k <= 0) return '';
  const d = new Defs(), c = clamp(k * 2), e = clamp(k * 2 - 1);
  const r = Math.hypot(Math.max(cx, W - cx), Math.max(cy, H - cy)) * (0.35 + 0.9 * c);
  return d + rect(-20, -20, W + 40, H + 40, { fill: d.rad([[0, color, c], [0.45, color, Math.max(e, c * 0.75)], [0.8, tint, Math.max(e, c * 0.35)], [1, tint, e]], cx, cy, r, 'userSpaceOnUse') });
}

/** crackedGlass({cx, cy, r, k, seed, box, color}) - a cracked-glass overlay: 10 jagged radial cracks from the impact
 *  point plus two rings of connecting shards, each a dark line with a white glint; k 0..1 grows them outward (rings
 *  after .35). box [x, y, w, h] clips it (e.g. a phone screen); no filters. */
export function crackedGlass(o = {}) {
  const { cx = 960, cy = 540, r = 900, seed = 3 } = o;
  const k = clamp(o.k ?? 1);
  if (k <= 0) return '';
  const d = new Defs(), R = rng(seed), n = 10;
  const rays = [];
  for (let i = 0; i < n; i++) {
    const a0 = (i / n) * TAU + (R() - 0.5) * 0.4, L = r * (0.55 + R() * 0.5), pts = [[cx, cy]];
    const segs = 6;
    for (let j = 1; j <= segs; j++) {
      const u = j / segs, a = a0 + (R() - 0.5) * 0.22;
      pts.push([cx + Math.cos(a) * L * u, cy + Math.sin(a) * L * u]);
    }
    rays.push({ pts, L });
  }
  const line2 = (P, kk, wd) => {
    if (kk <= 0) return '';
    let len = 0; for (let i = 1; i < P.length; i++) len += Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]);
    const dash = `${f(len * kk)} ${f(len + 10)}`, dd = P.map((q, i) => (i ? 'L' : 'M') + f(q[0]) + ' ' + f(q[1])).join('');
    return path(dd, { fill: 'none', stroke: '#0E1230', strokeWidth: wd * 2, strokeLinejoin: 'round', strokeLinecap: 'round', opacity: 0.4, strokeDasharray: dash }) +
      path(dd, { fill: 'none', stroke: o.color || '#FFFFFF', strokeWidth: wd, strokeLinejoin: 'round', strokeLinecap: 'round', opacity: 0.9, strokeDasharray: dash });
  };
  let s = '';
  const kr = seg(k, 0, 0.7);
  for (const ry of rays) s += line2(ry.pts, kr, 3.2);
  for (const [ring, w0] of [[2, 2.6], [4, 2.2]]) {
    const kk = seg(k, 0.35 + ring * 0.05, 0.85 + ring * 0.03);
    if (kk <= 0) continue;
    for (let i = 0; i < n; i++) {
      if (R() < 0.25) continue;
      const A = rays[i].pts[Math.min(ring, rays[i].pts.length - 1)], B = rays[(i + 1) % n].pts[Math.min(ring + (R() < 0.5 ? 1 : 0), rays[(i + 1) % n].pts.length - 1)];
      const M = [(A[0] + B[0]) / 2 + (R() - 0.5) * 30, (A[1] + B[1]) / 2 + (R() - 0.5) * 30];
      s += line2([A, M, B], kk, w0);
    }
  }
  // impact point: a white star of splinters and a few chips
  s += path(starPts(cx, cy, 7, r * 0.05, r * 0.015, 0, 0.5, seed).map((q, i) => (i ? 'L' : 'M') + f(q[0]) + ' ' + f(q[1])).join('') + 'Z', { fill: '#FFFFFF', opacity: op2(0.85 * seg(k, 0, 0.2)) });
  if (o.box) {
    const [bx, by, bw, bh] = o.box;
    return d + g(s, { clipPath: d.clip(rect(bx, by, bw, bh)) });
  }
  return d + s;
}

/** scrollStreaks({x, y, w, h, speed, seed, t, color, dir}) - motion streaks for a fast UI scroll: vertical (dir 'v',
 *  default) or horizontal light streaks inside the box, length and opacity from speed (px per frame, ~0 below 4). */
export function scrollStreaks(o = {}) {
  const { x = 0, y = 0, w = W, h = H, speed = 0, seed = 21, t = 0, color = '#FFFFFF', count = 14, dir = 'v' } = o;
  const k = clamp((Math.abs(speed) - 4) / 36);
  if (k <= 0) return '';
  const R = rng(seed + Math.floor(t * 30)), d = new Defs();
  let s = '';
  for (let i = 0; i < count; i++) {
    const L = (dir === 'v' ? h : w) * (0.15 + R() * 0.45) * (0.4 + 0.6 * k), wd = 3 + R() * 6;
    if (dir === 'v') s += rect(x + R() * w, y + R() * (h - L), wd, L, { fill: color, opacity: op2(k * (0.15 + R() * 0.35)), rx: wd / 2 });
    else s += rect(x + R() * (w - L), y + R() * h, L, wd, { fill: color, opacity: op2(k * (0.15 + R() * 0.35)), ry: wd / 2 });
  }
  return d + g(s, { clipPath: d.clip(rect(x, y, w, h)) });
}

/** boxBlur(svg, {x, y, w, h, sdx, sdy}) - a Gaussian (or directional) blur whose filter region is just the box, so its
 *  cost stays small; never wrap it in fx.glitch() or a <use> copy (Chromium caveat). */
export function boxBlur(svg, o = {}) {
  const { x = 0, y = 0, w = W, h = H, sdx = 0, sdy = 8 } = o;
  if (sdx < 0.3 && sdy < 0.3) return svg;
  const d = new Defs();
  const id = d.raw('bb', `<filter id="__ID__" filterUnits="userSpaceOnUse" x="${f(x)}" y="${f(y)}" width="${f(w)}" height="${f(h)}" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="${f(sdx)} ${f(sdy)}" edgeMode="duplicate"/></filter>`);
  return d + g(svg, { filter: `url(#${id})` });
}
