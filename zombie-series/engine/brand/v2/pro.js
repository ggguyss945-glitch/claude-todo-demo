// Thumbnail-grade art for LAST LIGHT ep. 1: the same cast and sets as the episode, staged for a feed.
// Characters get thumbnail acting (bigger eyes, brows, open mouths), a white sticker outline and rim light;
// backgrounds are blurred and graded so the face always wins.
import { W, H, INK, PAL, defs, finish, glow, hero, zombie, crowd, g, rect, circle, ellipse, line, poly, path, text, ink, rng } from '../../lib.js';
import { screenGlow, radioProp, mitt } from '../../ep/kit.js';
import { aisle } from '../../scenes.js';
import * as S from '../../ep/sets.js';

const F = (n) => (+n).toFixed(1);
const FONT = "'Lilita One', Rubik, sans-serif";
export const RED = '#FF3B2F', TAPE = '#F2C230';

// shared filters and gradients; generous regions so blurs never clip square
export const FX = `<defs>
  <filter id="pro_stk" x="-15%" y="-15%" width="130%" height="130%"><feMorphology in="SourceAlpha" operator="dilate" radius="9" result="d"/><feFlood flood-color="#FFFFFF"/><feComposite in2="d" operator="in" result="o"/><feMerge><feMergeNode in="o"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="pro_b1" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="1.3"/></filter>
  <filter id="pro_b2" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="2.2"/></filter>
  <filter id="pro_b4" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="4"/></filter>
  <filter id="pro_glow" x="-150%" y="-150%" width="400%" height="400%"><feGaussianBlur stdDeviation="28"/></filter>
  <filter id="pro_glowS" x="-150%" y="-150%" width="400%" height="400%"><feGaussianBlur stdDeviation="10"/></filter>
  <filter id="pro_shadow" x="-10%" y="-20%" width="130%" height="160%"><feGaussianBlur in="SourceAlpha" stdDeviation="6"/><feOffset dy="12" result="b"/><feFlood flood-color="#000" flood-opacity="0.6"/><feComposite in2="b" operator="in" result="s"/><feMerge><feMergeNode in="s"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <linearGradient id="pro_white" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#E4E1DA"/></linearGradient>
  <linearGradient id="pro_red" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FF6A45"/><stop offset="1" stop-color="#E0221A"/></linearGradient>
  <linearGradient id="pro_yel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFE45C"/><stop offset="1" stop-color="#F5A623"/></linearGradient>
</defs>`;
export const svgOf = (s, seed = 5) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}">${defs(seed, seed)}${FX}${s}</svg>`;
// soft light that never shows a square edge
export const bloom = (cx, cy, rx, ry, color, op, small = false) => ellipse(cx, cy, rx, ry, { fill: color, opacity: op, filter: `url(#${small ? 'pro_glowS' : 'pro_glow'})`, style: 'mix-blend-mode:screen' });
export const grade = (color, op) => rect(-20, -20, W + 40, H + 40, { fill: color, opacity: op, style: 'mix-blend-mode:multiply' });

// headline: gradient fill, thick ink outline, soft drop shadow; `rich` may hold <tspan>s
export function headline(x, y, str, { size = 200, fill = 'url(#pro_white)', sw = 24, anchor = 'middle', rot = 0, ls = 2, rich } = {}) {
  const t = { fontFamily: FONT, fontSize: size, textAnchor: anchor, letterSpacing: ls, strokeLinejoin: 'round' };
  return g(text(x, y, rich || str, { ...t, fill, stroke: INK, strokeWidth: sw, paintOrder: 'stroke' }), { transform: rot ? `rotate(${rot} ${x} ${y})` : undefined, filter: 'url(#pro_shadow)' });
}

// ---------- the hero, acting for the thumbnail ----------
function head(cx, cy, u, { face = 'happy', look = 0, tired = false, bandage = false, scratch = false, lick: showLick = true, rim, id = 'h' }) {
  let s = circle(cx, cy, u, { fill: PAL.skin });
  if (rim) s += `<mask id="rim_${id}"><circle cx="${F(cx)}" cy="${F(cy)}" r="${F(u)}" fill="#fff"/><circle cx="${F(cx - rim.side * 0.16 * u)}" cy="${F(cy + 0.06 * u)}" r="${F(u)}" fill="#000"/></mask>`
    + circle(cx, cy, u, { fill: rim.color, opacity: rim.op ?? 0.85, mask: `url(#rim_${id})` });
  const hx = cx - u, hy = cy;
  s += path(`M${F(hx + 0.02 * u)} ${F(hy - 0.05 * u)} C${F(hx - 0.02 * u)} ${F(hy - 1.1 * u)} ${F(cx + 1.1 * u)} ${F(cy - 1.25 * u)} ${F(cx + 0.98 * u)} ${F(cy - 0.12 * u)} L${F(cx + 0.7 * u)} ${F(cy - 0.42 * u)} L${F(cx + 0.48 * u)} ${F(cy - 0.3 * u)} L${F(cx + 0.18 * u)} ${F(cy - 0.5 * u)} L${F(cx - 0.12 * u)} ${F(cy - 0.36 * u)} L${F(cx - 0.45 * u)} ${F(cy - 0.52 * u)} L${F(cx - 0.72 * u)} ${F(cy - 0.32 * u)} Z`, { fill: PAL.hair, ...ink(0.04 * u) });
  if (rim) s += path(`M${F(cx + rim.side * 0.62 * u)} ${F(cy - 0.78 * u)} Q${F(cx + rim.side * 0.95 * u)} ${F(cy - 0.5 * u)} ${F(cx + rim.side * 0.98 * u)} ${F(cy - 0.12 * u)}`, { fill: 'none', stroke: rim.color, strokeWidth: 0.06 * u, strokeLinecap: 'round', opacity: 0.7 });
  const lick = `M${F(cx + 0.05 * u)} ${F(cy - 0.98 * u)} q${F(0.1 * u)} ${F(-0.35 * u)} ${F(0.38 * u)} ${F(-0.3 * u)}`;
  if (showLick) s += path(lick, { fill: 'none', stroke: INK, strokeWidth: 0.19 * u, strokeLinecap: 'round' }) + path(lick, { fill: 'none', stroke: PAL.hair, strokeWidth: 0.11 * u, strokeLinecap: 'round' });
  if (bandage) s += g(rect(-0.34 * u, -0.1 * u, 0.68 * u, 0.2 * u, { rx: 0.05 * u, fill: '#F4EEDF', ...ink(0.025 * u) }) + line(-0.06 * u, -0.06 * u, -0.06 * u, 0.06 * u, { stroke: '#C9BFA6', strokeWidth: 0.02 * u }) + line(0.06 * u, -0.06 * u, 0.06 * u, 0.06 * u, { stroke: '#C9BFA6', strokeWidth: 0.02 * u }),
    { transform: `translate(${F(cx - 0.42 * u)} ${F(cy - 0.46 * u)}) rotate(-24)` });
  const ex = cx + look * 0.26 * u, ey = cy + 0.04 * u, sp = 0.5 * u;
  const big = face === 'terrified' ? 1.12 : 1;
  for (const side of [-1, 1]) {
    const x0 = ex + side * sp / 2;
    if (tired) s += path(`M${F(x0 - 0.14 * u)} ${F(ey + 0.24 * u)} q${F(0.14 * u)} ${F(0.1 * u)} ${F(0.28 * u)} 0`, { fill: 'none', stroke: '#8E7FA6', strokeWidth: 0.045 * u, strokeLinecap: 'round' });
    s += ellipse(x0, ey, 0.13 * u * big, 0.19 * u * big, { fill: INK });
    s += circle(x0 + 0.045 * u, ey - 0.075 * u, 0.048 * u, { fill: '#FFFFFF' }) + circle(x0 - 0.04 * u, ey + 0.07 * u, 0.022 * u, { fill: '#FFFFFF' });
    if (face === 'bored' || face === 'serious') {
      // heavy upper lid: flat and half shut when bored, slanted down to the nose when serious
      const base = ey - 0.19 * u + (face === 'bored' ? 0.5 : 0.36) * 0.38 * u, tilt = face === 'serious' ? 0.05 * u : 0;
      const yo = base - tilt, yi = base + tilt, xo = x0 + side * 0.17 * u, xi = x0 - side * 0.17 * u;
      s += poly([[xo, ey - 0.26 * u], [xi, ey - 0.26 * u], [xi, yi], [xo, yo]], { fill: PAL.skin }) + line(xo, yo, xi, yi, ink(0.05 * u));
      s += circle(x0 + 0.04 * u, (yo + yi) / 2 + 0.07 * u, 0.03 * u, { fill: '#FFFFFF' });
    }
    const by = ey - 0.3 * u;
    if (face === 'bored') s += line(x0 - 0.13 * u, by + 0.07 * u, x0 + 0.13 * u, by + 0.07 * u, ink(0.045 * u));
    if (face === 'calm') s += path(`M${F(x0 - 0.11 * u)} ${F(by + 0.02 * u)} Q${F(x0)} ${F(by - 0.05 * u)} ${F(x0 + 0.11 * u)} ${F(by + 0.02 * u)}`, { fill: 'none', ...ink(0.035 * u) });
    if (face === 'serious') s += line(x0 + side * 0.16 * u, by - 0.01 * u, x0 - side * 0.13 * u, by + 0.11 * u, ink(0.065 * u));
    if (face === 'terrified') s += path(`M${F(x0 + side * 0.15 * u)} ${F(by + 0.06 * u)} L${F(x0 - side * 0.13 * u)} ${F(by - 0.07 * u)}`, { fill: 'none', ...ink(0.06 * u) });
  }
  const mx = ex + look * 0.05 * u, my = cy + 0.5 * u;
  if (face === 'happy') {
    s += path(`M${F(mx - 0.21 * u)} ${F(my - 0.05 * u)} Q${F(mx)} ${F(my + 0.3 * u)} ${F(mx + 0.21 * u)} ${F(my - 0.05 * u)} Z`, { fill: '#3A1F1F', ...ink(0.04 * u) })
      + path(`M${F(mx - 0.1 * u)} ${F(my + 0.12 * u)} Q${F(mx)} ${F(my + 0.03 * u)} ${F(mx + 0.11 * u)} ${F(my + 0.12 * u)} Q${F(mx)} ${F(my + 0.2 * u)} ${F(mx - 0.1 * u)} ${F(my + 0.12 * u)} Z`, { fill: '#E07A7A' });
    s += ellipse(cx - 0.55 * u, cy + 0.3 * u, 0.13 * u, 0.065 * u, { fill: '#F2A3A3', opacity: 0.6 }) + ellipse(cx + 0.55 * u, cy + 0.3 * u, 0.13 * u, 0.065 * u, { fill: '#F2A3A3', opacity: 0.6 });
  } else if (face === 'calm') {
    s += path(`M${F(mx - 0.12 * u)} ${F(my - 0.01 * u)} Q${F(mx)} ${F(my + 0.08 * u)} ${F(mx + 0.12 * u)} ${F(my - 0.01 * u)}`, { fill: 'none', ...ink(0.045 * u) });
  } else if (face === 'bored') {
    s += path(`M${F(mx - 0.13 * u)} ${F(my + 0.03 * u)} Q${F(mx)} ${F(my + 0.01 * u)} ${F(mx + 0.13 * u)} ${F(my - 0.02 * u)}`, { fill: 'none', ...ink(0.045 * u) });
  } else if (face === 'serious') {
    s += path(`M${F(mx - 0.15 * u)} ${F(my + 0.05 * u)} Q${F(mx)} ${F(my - 0.04 * u)} ${F(mx + 0.15 * u)} ${F(my + 0.05 * u)}`, { fill: 'none', ...ink(0.055 * u) });
  } else {
    s += ellipse(mx, my + 0.06 * u, 0.15 * u, 0.21 * u, { fill: '#3A1F1F', ...ink(0.04 * u) });
    s += rect(mx - 0.1 * u, my - 0.13 * u, 0.2 * u, 0.06 * u, { rx: 0.02 * u, fill: '#FBF8EE' }) + ellipse(mx, my + 0.19 * u, 0.09 * u, 0.05 * u, { fill: '#E07A7A' });
    s += path(`M${F(cx + 0.78 * u)} ${F(cy - 0.5 * u)} q${F(0.09 * u)} ${F(0.2 * u)} 0 ${F(0.29 * u)} q${F(-0.09 * u)} ${F(-0.09 * u)} 0 ${F(-0.29 * u)}`, { fill: '#9ED8F5', ...ink(0.025 * u) })
      + path(`M${F(cx - 0.86 * u)} ${F(cy - 0.12 * u)} q${F(0.06 * u)} ${F(0.14 * u)} 0 ${F(0.2 * u)} q${F(-0.06 * u)} ${F(-0.06 * u)} 0 ${F(-0.2 * u)}`, { fill: '#9ED8F5', ...ink(0.02 * u) });
  }
  if (scratch) for (const [dx, dy] of [[0.42, 0.18], [0.5, 0.26]]) s += line(cx + dx * u, cy + dy * u, cx + (dx + 0.2) * u, cy + (dy - 0.1) * u, { stroke: '#B5452F', strokeWidth: 0.035 * u, strokeLinecap: 'round' });
  if (tired) for (const [dx, dy, r] of [[0.48, 0.62, 0.07], [-0.6, 0.45, 0.05], [0.25, 0.75, 0.04]]) s += circle(cx + dx * u, cy + dy * u, r * u, { fill: '#7B6E5E', opacity: 0.35 });
  s += circle(cx, cy, u, { fill: 'none', ...ink(0.045 * u) });
  return s;
}
// the hero with a thumbnail face; `front` is drawn over the head (props held up at the cheek)
export function actor({ x, y, s: sc, pose = 'stand', face = 'happy', look = 0, tired = false, bandage = false, scratch = false, lick = true, rim, extra = '', front = '', id = 'a', sticker = true }) {
  const u = 60 * sc;
  let body = hero({ x, y, s: sc, pose, expr: face === 'happy' ? 'smile' : 'scared', look, extra, filter: false });
  if (!lick) {   // under a helmet: mask out the base figure's cowlick
    const cy = y - 5.25 * u;
    body = `<mask id="nolick_${id}" maskUnits="userSpaceOnUse" x="${F(x - 4 * u)}" y="${F(y - 9 * u)}" width="${F(8 * u)}" height="${F(10 * u)}"><rect x="${F(x - 4 * u)}" y="${F(y - 9 * u)}" width="${F(8 * u)}" height="${F(10 * u)}" fill="#fff"/><ellipse cx="${F(x + 0.25 * u)}" cy="${F(cy - 1.2 * u)}" rx="${F(0.42 * u)}" ry="${F(0.26 * u)}" fill="#000"/></mask>` + g(body, { mask: `url(#nolick_${id})` });
  }
  const hd = head(x, y - 5.25 * u, u, { face, look, tired, bandage, scratch, lick, rim, id });
  return g(g(body + hd + front, { filter: 'url(#wobbleSoft)' }), { filter: sticker ? 'url(#pro_stk)' : undefined });
}
// walkie-talkie up at the cheek, red light on; returns [markup, led x, led y]
export function talkie(x, y, sc, rot = 8) {
  const u = 60 * sc, hx = x + 0.98 * u, hy = y - 4.67 * u, k = 0.3 * sc, rx = hx + 0.12 * u, ry = hy + 0.14 * u;
  const a = (rot * Math.PI) / 180, lx = rx + (-30 * k) * Math.cos(a) - (-140 * k) * Math.sin(a), ly = ry + (-30 * k) * Math.sin(a) + (-140 * k) * Math.cos(a);
  return [radioProp(rx, ry, k, { on: true, led: RED, rot }) + circle(hx, hy, 0.16 * u, { fill: PAL.skin, ...ink(0.05 * u) }), lx, ly];
}

// ---------- the crowd at Freshway's glass, several rows deep (doors-set coordinates) ----------
export function glassCrowd(seed = 3, { front = 1.35, palms = true } = {}) {
  let s = crowd({ x0: 540, x1: 1380, y: 760, rows: 3, n: 16, s: 0.72, seed, spread: 30, arms: true });
  const fits = ['cashier', 'jogger', 'shopper', 'park', 'nurse', 'janitor', 'guard', 'suit', 'shopper', 'cashier'];
  for (let i = 0; i < 9; i++) s += zombie({ x: 585 + i * 94, y: 955 + 18 * Math.sin(i * 2.7), s: 1.02, outfit: fits[(i + 3) % fits.length], tilt: i % 2 ? 10 : -10, look: 0.1 * Math.sin(i), filter: false });
  for (let i = 0; i < 7; i++) s += zombie({ x: 600 + i * 122, y: 1150 + 22 * Math.sin(i * 3.3), s: front, outfit: fits[i], tilt: i % 2 ? -8 : 8, look: 0.05 * Math.sin(i * 2), pose: 'reach', filter: false });
  if (palms) for (const [px, py, r] of [[640, 640, 100], [790, 600, 80], [1110, 610, 96], [1280, 650, 84], [930, 700, 92]]) s += mitt(px, py, r, 0.62, '#A8B79B');
  return g(s, { filter: 'url(#wobbleSoft)' });
}
const doorsFrame = (dim = 0.55) => `<defs><filter id="pro_dim${Math.round(dim * 100)}"><feColorMatrix type="matrix" values="${dim} 0 0 0 0 0 ${dim} 0 0 0 0 0 ${dim + 0.08} 0 0.01 0 0 0 1 0"/></filter></defs>` + g(S.doorsInside(), { filter: `url(#pro_dim${Math.round(dim * 100)})` });

// ---------- A: DAY 0 / DAY 7, mirror framing ----------
function thumbA() {
  const SEAM = [[1000, 0], [920, 1080]];
  let s = `<defs><clipPath id="pa_l"><polygon points="0,0 ${SEAM[0].join(',')} ${SEAM[1].join(',')} 0,1080"/></clipPath><clipPath id="pa_r"><polygon points="${SEAM[0].join(',')} 1920,0 1920,1080 ${SEAM[1].join(',')}"/></clipPath>
    <linearGradient id="pa_warm" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFE7A6" stop-opacity="0.55"/><stop offset="1" stop-color="#FFB36B" stop-opacity="0.1"/></linearGradient></defs>`;
  const sc = 2.75, gy = 1430;
  // Day 0: the bright store, a happy kid on the night shift
  let L = g(aisle({ night: false, seed: 5 }).s, { transform: 'translate(-460 -20) scale(1.04)', filter: 'url(#pro_b2)' });
  L += rect(0, 0, 1000, 1080, { fill: 'url(#pa_warm)', opacity: 0.6, style: 'mix-blend-mode:multiply' }) + bloom(470, 330, 420, 260, '#FFF6DA', 0.4);
  const u = 60 * sc;
  const box = g(rect(-0.82 * u, 0, 1.64 * u, 0.92 * u, { rx: 0.08 * u, fill: '#C9A06E', ...ink(0.05 * u) }) + line(-0.82 * u, 0.2 * u, 0.82 * u, 0.2 * u, ink(0.035 * u))
    + rect(-0.56 * u, 0.34 * u, 1.12 * u, 0.38 * u, { rx: 0.05 * u, fill: '#F6F1E4', ...ink(0.03 * u) }) + text(0, 0.6 * u, 'FRESHWAY', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 0.16 * u, fill: '#2F6B52', textAnchor: 'middle', letterSpacing: 2 }),
    { transform: `translate(470 ${F(gy - 3.62 * u)})` });
  const _badge = g(rect(-0.34 * u, -0.12 * u, 0.68 * u, 0.24 * u, { rx: 0.05 * u, fill: '#F6F1E4', ...ink(0.025 * u) }) + text(0, 0.06 * u, 'NIGHT SHIFT', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 0.1 * u, fill: '#B5452F', textAnchor: 'middle', letterSpacing: 1 }), { transform: `translate(${F(470 - 0.3 * u)} ${F(gy - 3.85 * u)}) rotate(-4)` });
  L += actor({ x: 470, y: gy, s: sc, pose: 'carry', face: 'happy', look: 0.12, extra: box, id: 'a0', rim: { color: '#FFF3C8', side: -1, op: 0.6 } });
  s += g(L, { clipPath: 'url(#pa_l)' });
  // Day 7: the same doors at night, two hundred of them on the glass, red emergency light
  let R = g(S.doorsOutside({ dawn: false }) + glassCrowd(4) + doorsFrame(0.5), { transform: 'translate(500 -30) scale(1.03)', filter: 'url(#pro_b1)' });
  R += grade('#3A6A9A', 0.3) + bloom(1460, 600, 520, 320, '#6FB4FF', 0.22) + bloom(1890, 90, 300, 240, RED, 0.4) + bloom(990, 1060, 260, 160, RED, 0.22);
  const [tk, lx, ly] = talkie(1440, gy, sc);
  R += actor({ x: 1440, y: gy, s: sc, pose: 'talkie', face: 'terrified', look: -0.28, tired: true, bandage: true, id: 'a7', rim: { color: '#7FC4FF', side: -1, op: 0.75 }, front: tk });
  R += bloom(lx, ly, 70, 70, RED, 0.95, true) + bloom(lx + 40, ly + 60, 220, 200, RED, 0.28);
  s += g(R, { clipPath: 'url(#pa_r)' });
  s += line(...SEAM[0], ...SEAM[1], { stroke: INK, strokeWidth: 42 }) + line(...SEAM[0], ...SEAM[1], { stroke: '#FFFFFF', strokeWidth: 22 });
  s += headline(470, 210, 'DAY 0', { size: 210 }) + headline(1450, 210, 'DAY 7', { size: 210, fill: 'url(#pro_red)' });
  s += finish({ vignette: 0.35, grain: 0.05 });
  return { w: W, h: H, svg: svgOf(s, 5), css: 'saturate(1.12) contrast(1.06)' };
}

// ---------- A4: the same split; a bored night-shift worker on day 0, a survivor with a crowbar on day 7 ----------
export function apron(x, y, u) {
  let s = poly([[x - 0.43 * u, y - 3.98 * u], [x + 0.43 * u, y - 3.98 * u], [x + 0.55 * u, y - 2.05 * u], [x - 0.55 * u, y - 2.05 * u]], { fill: '#2F6B52', ...ink(0.04 * u) });
  s += line(x - 0.3 * u, y - 3.98 * u, x - 0.22 * u, y - 4.3 * u, ink(0.04 * u)) + line(x + 0.3 * u, y - 3.98 * u, x + 0.22 * u, y - 4.3 * u, ink(0.04 * u));
  s += text(x, y - 3.42 * u, 'FRESHWAY', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 0.15 * u, fill: '#F3EAD2', textAnchor: 'middle', letterSpacing: 1 });
  s += rect(x - 0.28 * u, y - 3.0 * u, 0.56 * u, 0.34 * u, { rx: 0.04 * u, fill: '#265A45', ...ink(0.03 * u) }) + line(x, y - 3.0 * u, x, y - 2.66 * u, ink(0.02 * u));
  s += g(rect(-0.2 * u, -0.08 * u, 0.4 * u, 0.16 * u, { rx: 0.03 * u, fill: '#F6F1E4', ...ink(0.02 * u) }) + text(0, 0.05 * u, 'STAFF', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 0.1 * u, fill: '#B5452F', textAnchor: 'middle' }), { transform: `translate(${F(x - 0.16 * u)} ${F(y - 3.72 * u)}) rotate(-5)` });
  return s;
}
function coffeeArm(x, y, u) {
  // the 'radio' pose's right forearm, redrawn over the apron, holding a paper cup at the chest
  const shY = y - 4.05 * u, sx = x + 0.5 * u, sy = shY + 0.05 * u, ax = x + 0.42 * u, hy = shY + 0.2 * u;
  const mx = (sx + ax) / 2 + 0.15 * u, my = (sy + hy) / 2 + 0.1 * u, lw = Math.max(4, 0.1 * u);
  let s = path(`M${F(sx)} ${F(sy)} Q${F(mx)} ${F(my)} ${F(ax)} ${F(hy)}`, { fill: 'none', ...ink(lw) });
  s += poly([[ax - 0.15 * u, hy - 0.5 * u], [ax + 0.15 * u, hy - 0.5 * u], [ax + 0.12 * u, hy + 0.02 * u], [ax - 0.12 * u, hy + 0.02 * u]], { fill: '#F4EFE4', ...ink(0.035 * u) });
  s += rect(ax - 0.17 * u, hy - 0.58 * u, 0.34 * u, 0.09 * u, { rx: 0.03 * u, fill: '#FFFFFF', ...ink(0.03 * u) }) + poly([[ax - 0.145 * u, hy - 0.36 * u], [ax + 0.145 * u, hy - 0.36 * u], [ax + 0.135 * u, hy - 0.2 * u], [ax - 0.135 * u, hy - 0.2 * u]], { fill: '#A8683A', ...ink(0.025 * u) });
  s += path(`M${F(ax - 0.04 * u)} ${F(hy - 0.64 * u)} q${F(0.05 * u)} ${F(-0.08 * u)} 0 ${F(-0.16 * u)} M${F(ax + 0.06 * u)} ${F(hy - 0.66 * u)} q${F(0.05 * u)} ${F(-0.08 * u)} 0 ${F(-0.16 * u)}`, { fill: 'none', stroke: '#FFFFFF', strokeWidth: 0.03 * u, strokeLinecap: 'round', opacity: 0.8 });
  s += circle(ax, hy, 0.15 * u, { fill: PAL.skin, ...ink(4) });
  return s;
}
export function survivalGear(x, y, u) {
  // backpack straps, a chest strap, a rip and dirt on the jacket
  let s = '';
  for (const side of [-1, 1]) s += poly([[x + side * 0.42 * u, y - 4.12 * u], [x + side * 0.24 * u, y - 4.12 * u], [x + side * 0.28 * u, y - 2.2 * u], [x + side * 0.46 * u, y - 2.2 * u]], { fill: '#4A3424', ...ink(0.035 * u) });
  s += rect(x - 0.44 * u, y - 3.62 * u, 0.88 * u, 0.12 * u, { fill: '#3A2A1E', ...ink(0.03 * u) }) + rect(x - 0.09 * u, y - 3.66 * u, 0.18 * u, 0.2 * u, { rx: 0.03 * u, fill: '#9C9890', ...ink(0.03 * u) });
  s += path(`M${F(x + 0.05 * u)} ${F(y - 2.9 * u)} l${F(0.08 * u)} ${F(0.12 * u)} l${F(0.07 * u)} ${F(-0.1 * u)} l${F(0.08 * u)} ${F(0.14 * u)} l${F(0.06 * u)} ${F(-0.08 * u)} l${F(-0.02 * u)} ${F(0.2 * u)} l${F(-0.3 * u)} 0 Z`, { fill: '#2C3020', ...ink(0.02 * u) });
  for (const [dx, dy, r] of [[-0.12, 2.6, 0.12], [0.2, 3.3, 0.09], [-0.32, 3.0, 0.07]]) s += ellipse(x + dx * u, y - dy * u, r * u, r * 0.7 * u, { fill: '#2B2A22', opacity: 0.3 });
  return s;
}
export function crowbar(x, y, u) {
  // held at the cheek, resting on the shoulder, the hook sticking up behind the head
  const B = [x + 1.3 * u, y - 4.12 * u], T = [x - 0.55 * u, y - 7.0 * u], w = 0.15 * u;
  const hook = `M${F(T[0])} ${F(T[1])} q${F(-0.34 * u)} ${F(-0.16 * u)} ${F(-0.4 * u)} ${F(0.26 * u)}`;
  const tip = `M${F(B[0])} ${F(B[1])} l${F(0.16 * u)} ${F(0.08 * u)}`;
  let s = '';
  for (const [c, ww] of [[INK, w + 0.07 * u], ['#B8261C', w]]) {
    s += line(B[0], B[1], T[0], T[1], { stroke: c, strokeWidth: ww, strokeLinecap: 'round' }) + path(hook, { fill: 'none', stroke: c, strokeWidth: ww, strokeLinecap: 'round' }) + path(tip, { fill: 'none', stroke: c, strokeWidth: ww, strokeLinecap: 'round' });
  }
  s += line(B[0] - 0.1 * u, B[1] - 0.16 * u, T[0] + 0.25 * u, T[1] + 0.38 * u, { stroke: '#FF8A70', strokeWidth: 0.03 * u, strokeLinecap: 'round', opacity: 0.7 });
  return s;
}
// a stack of stock in the worker's arms: two cartons with made-up brands on them, hands under the bottom one
export function stock(x, y, u) {
  const box = (bx, by, w, h, fill) => rect(bx, by, w, h, { rx: 0.04 * u, fill, ...ink(0.04 * u) }) + line(bx, by + 0.16 * u, bx + w, by + 0.16 * u, { stroke: '#8E6A40', strokeWidth: 0.025 * u });
  let s = '';
  // bottom carton: CRUNCHY O's cereal
  const b0 = [x - 0.88 * u, y - 3.42 * u, 1.76 * u, 0.92 * u];
  s += box(...b0, '#C9A06E');
  s += rect(x - 0.72 * u, y - 3.14 * u, 0.98 * u, 0.5 * u, { rx: 0.06 * u, fill: '#D8261A', ...ink(0.03 * u) }) + circle(x - 0.6 * u, y - 2.89 * u, 0.16 * u, { fill: '#F2C230', ...ink(0.025 * u) })
    + text(x - 0.6 * u, y - 2.84 * u, 'O', { fontFamily: "'Lilita One'", fontSize: 0.17 * u, fill: '#D8261A', textAnchor: 'middle' })
    + text(x - 0.13 * u, y - 2.93 * u, 'CRUNCHY', { fontFamily: "'Lilita One'", fontSize: 0.16 * u, fill: '#FFFFFF', textAnchor: 'middle' }) + text(x - 0.13 * u, y - 2.74 * u, "O's", { fontFamily: "'Lilita One'", fontSize: 0.16 * u, fill: '#F2C230', textAnchor: 'middle' });
  s += text(x + 0.55 * u, y - 2.95 * u, '12 x 500g', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 0.1 * u, fill: '#5A4026', textAnchor: 'middle' });
  s += path(`M${F(x + 0.45 * u)} ${F(y - 2.68 * u)} l0 ${F(-0.16 * u)} M${F(x + 0.39 * u)} ${F(y - 2.78 * u)} l${F(0.06 * u)} ${F(-0.06 * u)} l${F(0.06 * u)} ${F(0.06 * u)} M${F(x + 0.65 * u)} ${F(y - 2.68 * u)} l0 ${F(-0.16 * u)} M${F(x + 0.59 * u)} ${F(y - 2.78 * u)} l${F(0.06 * u)} ${F(-0.06 * u)} l${F(0.06 * u)} ${F(0.06 * u)}`, { fill: 'none', stroke: '#5A4026', strokeWidth: 0.025 * u, strokeLinecap: 'round' });
  // top carton: AQUA PURE water, a little off-centre
  const t0 = [x - 0.62 * u, y - 4.12 * u, 1.36 * u, 0.7 * u];
  s += box(...t0, '#D4AE7C');
  s += rect(x - 0.5 * u, y - 3.9 * u, 0.86 * u, 0.36 * u, { rx: 0.05 * u, fill: '#2F7FC1', ...ink(0.03 * u) }) + path(`M${F(x - 0.38 * u)} ${F(y - 3.62 * u)} q${F(0.06 * u)} ${F(-0.16 * u)} ${F(0.12 * u)} 0 q${F(-0.06 * u)} ${F(0.06 * u)} ${F(-0.12 * u)} 0 Z`, { fill: '#BFE8FF' })
    + text(x - 0.0 * u, y - 3.67 * u, 'AQUA PURE', { fontFamily: "'Lilita One'", fontSize: 0.14 * u, fill: '#FFFFFF', textAnchor: 'middle' });
  s += rect(x + 0.42 * u, y - 3.92 * u, 0.26 * u, 0.4 * u, { rx: 0.03 * u, fill: '#F6F1E4', ...ink(0.02 * u) }) + text(x + 0.55 * u, y - 3.74 * u, '24', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 0.1 * u, fill: INK, textAnchor: 'middle' }) + text(x + 0.55 * u, y - 3.6 * u, 'PCS', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 0.06 * u, fill: INK, textAnchor: 'middle' });
  // a FRESHWAY stock sticker on the bottom carton
  s += g(rect(-0.2 * u, -0.07 * u, 0.4 * u, 0.14 * u, { rx: 0.03 * u, fill: '#2F6B52', ...ink(0.02 * u) }) + text(0, 0.04 * u, 'FRESHWAY', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 0.07 * u, fill: '#F3EAD2', textAnchor: 'middle' }), { transform: `translate(${F(x + 0.52 * u)} ${F(y - 3.28 * u)}) rotate(-4)` });
  return s;
}
export const stockHands = (x, y, u) => circle(x - 0.86 * u, y - 2.62 * u, 0.15 * u, { fill: PAL.skin, ...ink(4) }) + circle(x + 0.86 * u, y - 2.62 * u, 0.15 * u, { fill: PAL.skin, ...ink(4) });

function thumbA4() {
  const SEAM = [[1000, 0], [920, 1080]];
  let s = `<defs><clipPath id="p4_l"><polygon points="0,0 ${SEAM[0].join(',')} ${SEAM[1].join(',')} 0,1080"/></clipPath><clipPath id="p4_r"><polygon points="${SEAM[0].join(',')} 1920,0 1920,1080 ${SEAM[1].join(',')}"/></clipPath>
    <linearGradient id="p4_warm" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFE7A6" stop-opacity="0.55"/><stop offset="1" stop-color="#FFB36B" stop-opacity="0.1"/></linearGradient></defs>`;
  const sc = 2.75, gy = 1430, u = 60 * sc;
  // Day 0: the bright store; an ordinary night-shift worker in the Freshway apron carrying stock, looking at us
  let L = g(aisle({ night: false, seed: 5 }).s, { transform: 'translate(-460 -20) scale(1.04)', filter: 'url(#pro_b2)' });
  L += rect(0, 0, 1000, 1080, { fill: 'url(#p4_warm)', opacity: 0.6, style: 'mix-blend-mode:multiply' }) + bloom(470, 330, 420, 260, '#FFF6DA', 0.4);
  L += actor({ x: 470, y: gy, s: sc, pose: 'carry', face: 'calm', look: 0, extra: apron(470, gy, u) + stock(470, gy, u), front: stockHands(470, gy, u), id: 'p40', rim: { color: '#FFF3C8', side: -1, op: 0.6 } });
  s += g(L, { clipPath: 'url(#p4_l)' });
  // Day 7: the same doors at night, the glass full of them; a survivor now, crowbar on the shoulder
  let R = g(S.doorsOutside({ dawn: false }) + glassCrowd(4) + doorsFrame(0.5), { transform: 'translate(500 -30) scale(1.03)', filter: 'url(#pro_b1)' });
  R += grade('#3A6A9A', 0.3) + bloom(1460, 600, 520, 320, '#6FB4FF', 0.22) + bloom(1890, 90, 300, 240, RED, 0.4) + bloom(990, 1060, 260, 160, RED, 0.22);
  const x7 = 1440, hx = x7 + 0.98 * u, hy = gy - 4.67 * u;
  const chestRadio = radioProp(x7 - 0.33 * u, gy - 3.05 * u, 0.42, { on: true, led: RED, rot: -6 });
  R += actor({ x: x7, y: gy, s: sc, pose: 'talkie', face: 'serious', look: -0.22, tired: true, bandage: true, scratch: true, id: 'p47',
    rim: { color: '#7FC4FF', side: -1, op: 0.75 }, extra: survivalGear(x7, gy, u) + chestRadio + crowbar(x7, gy, u), front: circle(hx, hy, 0.17 * u, { fill: PAL.skin, ...ink(0.05 * u) }) });
  R += bloom(x7 - 0.33 * u - 30 * 0.42, gy - 3.05 * u - 140 * 0.42, 50, 50, RED, 0.9, true);
  s += g(R, { clipPath: 'url(#p4_r)' });
  s += line(...SEAM[0], ...SEAM[1], { stroke: INK, strokeWidth: 42 }) + line(...SEAM[0], ...SEAM[1], { stroke: '#FFFFFF', strokeWidth: 22 });
  s += headline(470, 210, 'DAY 0', { size: 210 }) + headline(1450, 210, 'DAY 7', { size: 210, fill: 'url(#pro_red)' });
  s += finish({ vignette: 0.35, grain: 0.05 });
  return { w: W, h: H, svg: svgOf(s, 5), css: 'saturate(1.12) contrast(1.06)' };
}

// ---------- B: the voice on the radio, and the man on the roof against the moon ----------
function thumbB() {
  let s = `<defs><linearGradient id="pb_sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0A1230"/><stop offset="0.6" stop-color="#1B2E5C"/><stop offset="1" stop-color="#2C4A7A"/></linearGradient></defs>`;
  s += rect(0, 0, W, H, { fill: 'url(#pb_sky)' });
  const r = rng(8); for (let i = 0; i < 110; i++) s += circle(r() * W, r() * 600, 0.8 + r() * 2, { fill: '#FFFFFF', opacity: (0.3 + r() * 0.6).toFixed(2) });
  // the moon, huge, right behind him
  const mx = 1450, my = 330;
  s += bloom(mx, my, 330, 330, '#F6E7B8', 0.55) + circle(mx, my, 230, { fill: '#F4E9C8', ...ink(6) }) + circle(mx - 70, my - 60, 34, { fill: '#E4D6AE' }) + circle(mx + 80, my + 40, 22, { fill: '#E4D6AE' }) + circle(mx + 20, my + 120, 16, { fill: '#E4D6AE' });
  // Freshway's roof line, the lot below, the dead out there
  s += g(rect(860, 540, 1100, 560, { fill: '#141B2E', ...ink(6) }) + rect(860, 520, 1100, 34, { fill: '#0C1120', ...ink(5) }) + rect(1040, 600, 760, 110, { rx: 10, fill: '#1F3A30', ...ink(5) })
    + text(1420, 682, 'FRESHWAY', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 78, fill: '#5E8E78', textAnchor: 'middle', letterSpacing: 10 }), { filter: 'url(#wobble)' });
  s += rect(0, 900, W, 180, { fill: '#121826' }) + line(0, 900, W, 900, ink(5));
  for (let i = 0; i < 9; i++) { const x = 1000 + i * 105 + 20 * Math.sin(i * 3), y = 1010 + 20 * Math.sin(i * 1.7), k = 0.8 + 0.15 * Math.sin(i); s += g(circle(x, y - 95 * k, 34 * k, { fill: '#0B0F1A' }) + rect(x - 26 * k, y - 62 * k, 52 * k, 70 * k, { rx: 12 * k, fill: '#0B0F1A' })) + circle(x - 11 * k, y - 98 * k, 4 * k, { fill: '#D9F2A8' }) + circle(x + 11 * k, y - 96 * k, 4 * k, { fill: '#D9F2A8' }); }
  // Dale on the roof edge, a black cut-out against the moon: cap, radio up, red light, two pale eyes
  const fx = mx, fy = 522, k = 3.6, C = '#05070D';
  let fig = circle(fx, fy - 62 * k, 15 * k, { fill: C }) + rect(fx - 22 * k, fy - 67 * k, 44 * k, 9 * k, { rx: 3 * k, fill: C }) + rect(fx - 19 * k, fy - 48 * k, 38 * k, 48 * k, { rx: 9 * k, fill: C });
  fig += line(fx + 14 * k, fy - 40 * k, fx + 26 * k, fy - 66 * k, { stroke: C, strokeWidth: 8 * k, strokeLinecap: 'round' }) + rect(fx + 20 * k, fy - 86 * k, 12 * k, 24 * k, { rx: 3 * k, fill: C }) + line(fx + 28 * k, fy - 86 * k, fx + 28 * k, fy - 106 * k, { stroke: C, strokeWidth: 3 * k, strokeLinecap: 'round' });
  s += fig + circle(fx - 5 * k, fy - 61 * k, 2.2 * k, { fill: '#F2F0E0' }) + circle(fx + 6 * k, fy - 61 * k, 2.2 * k, { fill: '#F2F0E0' });
  s += circle(fx + 26 * k, fy - 80 * k, 3.4 * k, { fill: RED }) + bloom(fx + 26 * k, fy - 80 * k, 60, 60, RED, 0.95, true) + bloom(fx + 26 * k, fy - 80 * k, 120, 120, RED, 0.14);
  // red arrow from the headline to him
  s += g(path('M1060 250 Q1150 200 1225 255', { fill: 'none', stroke: INK, strokeWidth: 34, strokeLinecap: 'round' }) + path('M1060 250 Q1150 200 1225 255', { fill: 'none', stroke: RED, strokeWidth: 18, strokeLinecap: 'round' })
    + poly([[1250, 275], [1190, 285], [1225, 230]], { fill: RED, ...ink(8) }), { filter: 'url(#wobbleSoft)' });
  // you, radio at your cheek, frozen; red light on one side of the face, moonlight on the other
  const sc = 2.7, gx = 560, gy = 1440;
  s += bloom(gx, 640, 420, 480, '#4A78C8', 0.35);
  const [tk, lx, ly] = talkie(gx, gy, sc);
  s += actor({ x: gx, y: gy, s: sc, pose: 'talkie', face: 'terrified', look: 0.55, id: 'b', rim: { color: '#FF6A5A', side: 1, op: 0.8 }, front: tk });
  s += bloom(lx, ly, 70, 70, RED, 0.95, true) + bloom(lx + 30, ly + 40, 240, 220, RED, 0.3);
  s += headline(60, 200, "DON'T ANSWER", { size: 165, anchor: 'start', rich: `DON'T <tspan fill="url(#pro_red)">ANSWER</tspan>` });
  s += finish({ vignette: 0.55, grain: 0.05 });
  return { w: W, h: H, svg: svgOf(s, 6), css: 'saturate(1.12) contrast(1.06)' };
}

// ---------- C: a minute to 7:00, the glass full of them ----------
function thumbC() {
  let s = g(S.doorsOutside({ dawn: true }) + glassCrowd(7, { front: 1.45 }) + doorsFrame(0.42), { transform: 'translate(960 640) scale(1.32) translate(-960 -640)', filter: 'url(#pro_b1)' });
  s += grade('#283A6E', 0.42) + bloom(960, 760, 560, 260, '#FF9A6A', 0.16);
  // the store's LED clock
  s += rect(0, -10, W, 70, { fill: '#2A2F45' }) + g(rect(560, -30, 800, 350, { rx: 28, fill: '#120808', ...ink(10) }) + rect(584, 44, 752, 252, { rx: 18, fill: '#1E0C0C' }), { filter: 'url(#pro_shadow)' });
  s += ledDigits(660, 58, '6:59', 196) + text(960, 300, 'DOORS UNLOCK AT 7:00', { fontFamily: FONT, fontSize: 42, fill: TAPE, textAnchor: 'middle', letterSpacing: 4 });
  s += bloom(960, 170, 420, 170, RED, 0.3);
  // you, backing away from the glass
  const sc = 2.7, gx = 1440, gy = 1450;
  s += bloom(gx, 700, 340, 380, '#FFD7A8', 0.18);
  s += actor({ x: gx, y: gy, s: sc, pose: 'scared', face: 'terrified', look: -0.45, id: 'c', rim: { color: '#FFD9A8', side: -1, op: 0.7 } });
  // 1 vs 200 sticker
  s += g(circle(300, 860, 175, { fill: 'url(#pro_yel)', ...ink(14) }) + circle(300, 860, 150, { fill: 'none', stroke: '#FFF4B0', strokeWidth: 6, opacity: 0.8 }), { filter: 'url(#pro_shadow)', transform: 'rotate(-8 300 860)' });
  s += headline(300, 830, '1 vs', { size: 92, sw: 16, rot: -8, rich: `1 <tspan fill="url(#pro_red)">vs</tspan>` }) + headline(300, 935, '200', { size: 120, sw: 18, rot: -8 });
  s += finish({ vignette: 0.45, grain: 0.05 });
  return { w: W, h: H, svg: svgOf(s, 7), css: 'saturate(1.15) contrast(1.06)' };
}
// seven-segment digits like the store's clock
const SEG = { 0: 'abcdef', 1: 'bc', 2: 'abged', 3: 'abgcd', 4: 'fgbc', 5: 'afgcd', 6: 'afgedc', 7: 'abc', 8: 'abcdefg', 9: 'abcdfg' };
function ledDigits(x, y, str, h, on = '#FF3B2F', off = '#3A1010') {
  const w = h * 0.56, t = h * 0.14, hh = h / 2;
  const seg = { a: [t * 0.6, 0, w - t * 1.2, t], g: [t * 0.6, hh - t / 2, w - t * 1.2, t], d: [t * 0.6, h - t, w - t * 1.2, t], f: [0, t * 0.6, t, hh - t * 0.9], b: [w - t, t * 0.6, t, hh - t * 0.9], e: [0, hh + t * 0.3, t, hh - t * 0.9], c: [w - t, hh + t * 0.3, t, hh - t * 0.9] };
  let s = '', cx = x;
  for (const ch of str) {
    if (ch === ':') { s += circle(cx + t * 0.9, y + h * 0.3, t * 0.62, { fill: on }) + circle(cx + t * 0.9, y + h * 0.72, t * 0.62, { fill: on }); cx += t * 2.6; continue; }
    for (const k of 'abcdefg') { const [sx, sy, sw, sh] = seg[k]; s += rect(cx + sx, y + sy, sw, sh, { rx: t / 2, fill: (SEG[ch] || '').includes(k) ? on : off }); }
    cx += w + t * 1.4;
  }
  return g(g(s, { filter: 'url(#pro_glowS)', opacity: 0.9 }) + s, { transform: `skewX(-7) translate(${(y + h) * 0.12} 0)` });
}

export const THUMBS = { thumbA, thumbA4, thumbB, thumbC };
