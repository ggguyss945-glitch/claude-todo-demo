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
    const c = colors[i % colors.length], kind = i % 7, sz = 12 + R() * 14;
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
