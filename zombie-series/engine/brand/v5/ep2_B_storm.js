// LAST LIGHT ep. 2, A/B concept B "THE STORM" (Day 10): you walk straight through two hundred of them in the
// thunderstorm. Every one of them has its face turned up to the rain; nobody turns to you. One bolt floods the
// lot with cold white-violet light so every face reads. Storm teal/violet + white lightning, one red word.
import { W, H, INK, PAL, finish, g, rect, circle, ellipse, line, poly, path, ink, rng } from '../../lib.js';
import { svgOf, headline, bloom, grade } from '../v2/pro.js';

const F = (n) => (+n).toFixed(1);
const lerp = (a, b, k) => a + (b - a) * k;
function mix(a, b, k) {
  const p = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const A = p(a), B = p(b);
  return '#' + A.map((v, i) => Math.round(lerp(v, B[i], k)).toString(16).padStart(2, '0')).join('');
}

// ---------- palette ----------
const SKIN = '#9DB28E', SKIN_UNDER = '#61735F', SOCKET = '#272C27', PUPIL = '#F1F4E2', MOUTH = '#221C1B';
const RIM = '#E4DCFF', HAZE = '#6C6AA8', BOLT = '#F4F1FF', BOLT_GLOW = '#A993FF';
const CLOTHES = ['#C76A83', '#6FA3A6', '#A65F4A', '#7C6A8E', '#2E3D55', '#8A7A4E', '#D9A441', '#596471', '#B5452F', '#4F7A52', '#E0894A', '#8C8C86'];
const HAIR = ['#3A2A22', '#5B4636', '#2B2B2E', '#7A6A55', '#8E8A80'];

// ---------- the sky: violet storm ceiling, teal toward the horizon, lit from inside by the bolt ----------
function sky() {
  let s = `<defs>
    <linearGradient id="sb_sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#120C28"/><stop offset="0.42" stop-color="#2A2155"/><stop offset="0.72" stop-color="#3E4F86"/><stop offset="1" stop-color="#4F8C96"/></linearGradient>
    <radialGradient id="sb_flash" cx="0.84" cy="0.22" r="0.62"><stop offset="0" stop-color="#F1ECFF" stop-opacity="0.95"/><stop offset="0.28" stop-color="#B9A8FF" stop-opacity="0.55"/><stop offset="0.65" stop-color="#6B5FC8" stop-opacity="0.18"/><stop offset="1" stop-color="#2A2155" stop-opacity="0"/></radialGradient>
    <linearGradient id="sb_cloud" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1A1438"/><stop offset="1" stop-color="#3A3170"/></linearGradient>
    <filter id="sb_cblur" x="-20%" y="-40%" width="140%" height="180%"><feGaussianBlur stdDeviation="6"/></filter>
    <filter id="sb_boltglow" x="-50%" y="-20%" width="200%" height="140%"><feGaussianBlur stdDeviation="22"/></filter>
    <filter id="sb_boltglowS" x="-50%" y="-20%" width="200%" height="140%"><feGaussianBlur stdDeviation="7"/></filter>
    <filter id="sb_rainblur" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="1.6"/></filter>
  </defs>`;
  s += rect(0, 0, W, H, { fill: 'url(#sb_sky)' });
  s += rect(0, 0, W, 700, { fill: 'url(#sb_flash)', style: 'mix-blend-mode:screen' });
  // the cloud ceiling: heavy lumps, darker over the headline, their bellies lit near the bolt
  const r = rng(41);
  let cl = '';
  for (let i = 0; i < 30; i++) {
    const x = -150 + r() * (W + 300), y = -40 + r() * 230, rx = 170 + r() * 210, ry = 70 + r() * 70;
    const near = Math.max(0, 1 - Math.hypot(x - 1640, (y - 160) * 1.6) / 900);
    cl += ellipse(x, y, rx, ry, { fill: mix('#1B1540', '#8E7FE0', near * 0.85), opacity: 0.95 });
    cl += ellipse(x + 10, y + ry * 0.55, rx * 0.82, ry * 0.32, { fill: mix('#2C2560', '#D8CEFF', near * 0.9), opacity: 0.55 + near * 0.35 });
  }
  s += g(cl, { filter: 'url(#sb_cblur)' });
  // a second, lower band of cloud over the horizon, thinner
  const r2 = rng(5);
  let cl2 = '';
  for (let i = 0; i < 14; i++) {
    const x = r2() * W, y = 320 + r2() * 90, rx = 220 + r2() * 200, ry = 26 + r2() * 22;
    const near = Math.max(0, 1 - Math.abs(x - 1650) / 700);
    cl2 += ellipse(x, y, rx, ry, { fill: mix('#3A3A78', '#B7AAF5', near * 0.6), opacity: 0.55 });
  }
  s += g(cl2, { filter: 'url(#sb_cblur)' });
  return s;
}

// a jagged bolt with branches; (x0,y0) up in the clouds, (x1,y1) where it hits behind the crowd
function boltPath(x0, y0, x1, y1, segs, amp, r) {
  const pts = [[x0, y0]];
  for (let i = 1; i < segs; i++) {
    const k = i / segs, j = (r() - 0.5) * 2 * amp * (1 - 0.35 * k);
    pts.push([lerp(x0, x1, k) + j, lerp(y0, y1, k) + (r() - 0.5) * 18]);
  }
  pts.push([x1, y1]);
  return pts;
}
const d = (pts) => 'M' + pts.map(([x, y]) => `${F(x)} ${F(y)}`).join(' L');
function lightning() {
  const r = rng(77);
  const main = boltPath(1600, -30, 1700, 560, 11, 70, r);
  const branches = [];
  // forks off the main channel, thinner, reaching sideways and down
  for (const [i, dx, dy, n] of [[2, -260, 150, 5], [4, 230, 170, 5], [6, -200, 190, 5], [7, 170, 120, 4], [3, 120, -10, 3], [8, -120, 110, 3]]) {
    const [bx, by] = main[i];
    branches.push(boltPath(bx, by, bx + dx, by + dy, n, 30, r));
  }
  let s = '';
  // the air around it glows
  s += bloom(1680, 260, 420, 420, '#C9BCFF', 0.55) + bloom(1700, 520, 360, 120, '#E8E2FF', 0.6);
  s += path(d(main), { fill: 'none', stroke: BOLT_GLOW, strokeWidth: 90, strokeLinejoin: 'round', strokeLinecap: 'round', opacity: 0.75, filter: 'url(#sb_boltglow)' });
  for (const b of branches) s += path(d(b), { fill: 'none', stroke: BOLT_GLOW, strokeWidth: 34, strokeLinejoin: 'round', strokeLinecap: 'round', opacity: 0.6, filter: 'url(#sb_boltglowS)' });
  for (const b of branches) s += path(d(b), { fill: 'none', stroke: '#D9CFFF', strokeWidth: 9, strokeLinejoin: 'round', strokeLinecap: 'round' }) + path(d(b), { fill: 'none', stroke: BOLT, strokeWidth: 4, strokeLinejoin: 'round', strokeLinecap: 'round' });
  s += path(d(main), { fill: 'none', stroke: '#D4C8FF', strokeWidth: 30, strokeLinejoin: 'round', strokeLinecap: 'round', filter: 'url(#sb_boltglowS)' });
  s += path(d(main), { fill: 'none', stroke: '#E7E0FF', strokeWidth: 20, strokeLinejoin: 'round', strokeLinecap: 'round' });
  s += path(d(main), { fill: 'none', stroke: '#FFFFFF', strokeWidth: 9, strokeLinejoin: 'round', strokeLinecap: 'round' });
  return s;
}

// the far edge of the lot: the city and two dark lamp posts against the haze, the lot itself
function horizon() {
  let s = '';
  const r = rng(12);
  for (let x = -40; x < W; x += 90) { const h = 40 + r() * 120; s += rect(x, 520 - h, 86, h + 40, { fill: mix('#2E3466', '#5B5E9C', Math.max(0, 1 - Math.abs(x - 1680) / 600) * 0.7), ...ink(3) }); }
  s += rect(0, 500, W, 200, { fill: '#2F3D66' });
  s += bloom(1700, 520, 520, 70, '#D9D0FF', 0.5);
  return g(s, { filter: 'url(#wobble)' });
}

// ---------- the dead, faces turned up to the rain ----------
// (x, yg) ground point like lib's zombie(); detail 0 = distant blob, 1 = arms and chin, 2 = close-up with rain on the face
function upHead(hx, hy, u, { skin, under, socket, pupil, rim, rimOp, lw, detail, r, hair }) {
  let s = circle(hx, hy, u, { fill: skin });
  if (hair) s += path(`M${F(hx - 0.94 * u)} ${F(hy - 0.34 * u)} A${F(u)} ${F(u)} 0 0 1 ${F(hx + 0.94 * u)} ${F(hy - 0.34 * u)} Q${F(hx)} ${F(hy - 0.86 * u)} ${F(hx - 0.94 * u)} ${F(hy - 0.34 * u)} Z`, { fill: hair });
  // the underside of the jaw: the head is tipped back, so we see under the chin
  const a1 = 0.42, a2 = Math.PI - 0.42, p1 = [hx + Math.cos(a1) * u, hy + Math.sin(a1) * u], p2 = [hx + Math.cos(a2) * u, hy + Math.sin(a2) * u];
  s += path(`M${F(p1[0])} ${F(p1[1])} A${F(u)} ${F(u)} 0 0 1 ${F(p2[0])} ${F(p2[1])} Q${F(hx)} ${F(hy + 0.98 * u)} ${F(p1[0])} ${F(p1[1])} Z`, { fill: under });
  if (detail >= 1) s += path(`M${F(p2[0] + 0.06 * u)} ${F(p2[1] + 0.02 * u)} Q${F(hx)} ${F(hy + 0.98 * u)} ${F(p1[0] - 0.06 * u)} ${F(p1[1] + 0.02 * u)}`, { fill: 'none', stroke: INK, strokeWidth: lw * 0.6, strokeLinecap: 'round', opacity: 0.7 });
  // eyes high on the face, pupils rolled up to the sky
  const ey = hy - 0.4 * u, sz = 0.92 + r() * 0.16;
  s += ellipse(hx - 0.34 * u, ey + 0.02 * u, 0.21 * u * sz, 0.17 * u * sz, { fill: socket }) + ellipse(hx + 0.33 * u, ey, 0.2 * u * sz, 0.165 * u * sz, { fill: socket });
  s += circle(hx - 0.33 * u, ey - 0.05 * u, 0.065 * u, { fill: pupil }) + circle(hx + 0.34 * u, ey - 0.07 * u, 0.06 * u, { fill: pupil });
  if (detail >= 1) s += circle(hx - 0.06 * u, hy - 0.1 * u, 0.035 * u, { fill: socket }) + circle(hx + 0.06 * u, hy - 0.1 * u, 0.035 * u, { fill: socket });   // nostrils, seen from below
  // slack open mouth catching the rain
  s += ellipse(hx + 0.02 * u, hy + 0.16 * u, 0.13 * u, 0.15 * u, { fill: MOUTH });
  if (detail >= 1) s += rect(hx - 0.07 * u, hy + 0.03 * u, 0.15 * u, 0.05 * u, { rx: 0.02 * u, fill: '#E9E4D3' });
  // the bolt's light on the up-turned face and the wet top of the head
  s += path(`M${F(hx + Math.cos(-1.9) * 0.86 * u)} ${F(hy + Math.sin(-1.9) * 0.86 * u)} A${F(0.86 * u)} ${F(0.86 * u)} 0 0 1 ${F(hx + Math.cos(0.25) * 0.86 * u)} ${F(hy + Math.sin(0.25) * 0.86 * u)}`,
    { fill: 'none', stroke: rim, strokeWidth: 0.14 * u, strokeLinecap: 'round', opacity: rimOp });
  if (detail >= 2) {
    s += ellipse(hx + 0.5 * u, hy - 0.62 * u, 0.12 * u, 0.06 * u, { fill: '#FFFFFF', opacity: 0.7, transform: `rotate(40 ${F(hx + 0.5 * u)} ${F(hy - 0.62 * u)})` });
    // rain running off the cheeks
    s += path(`M${F(hx - 0.62 * u)} ${F(hy - 0.12 * u)} q${F(-0.04 * u)} ${F(0.22 * u)} ${F(0.02 * u)} ${F(0.42 * u)}`, { fill: 'none', stroke: '#DCEBFF', strokeWidth: 0.05 * u, strokeLinecap: 'round', opacity: 0.8 })
      + path(`M${F(hx + 0.6 * u)} ${F(hy - 0.08 * u)} q${F(0.03 * u)} ${F(0.2 * u)} ${F(-0.02 * u)} ${F(0.36 * u)}`, { fill: 'none', stroke: '#DCEBFF', strokeWidth: 0.045 * u, strokeLinecap: 'round', opacity: 0.7 });
    // drops bouncing off the crown
    for (const [dx, dy, a] of [[-0.25, -1.08, -40], [0.32, -1.05, 30], [0.02, -1.14, 0]]) s += line(hx + dx * u, hy + dy * u, hx + dx * u + Math.sin(a * Math.PI / 180) * 0.12 * u, hy + dy * u - Math.cos(a * Math.PI / 180) * 0.12 * u, { stroke: '#E8F0FF', strokeWidth: 0.035 * u, strokeLinecap: 'round', opacity: 0.85 });
  }
  s += circle(hx, hy, u, { fill: 'none', stroke: INK, strokeWidth: lw });
  return s;
}
function upZombie(x, yg, sc, { body, fogK = 0, detail = 1, r, tilt = 0, rimOp = 0.9, hair }) {
  const u = 60 * sc, lw = Math.max(2.2, 0.085 * u), fog = (c) => mix(c, HAZE, fogK);
  const ik = { stroke: mix(INK, HAZE, fogK * 0.35), strokeWidth: lw, strokeLinecap: 'round', strokeLinejoin: 'round' };
  const top = yg - 4.25 * u, bot = yg - 1.5 * u, hx = x + (r() - 0.5) * 0.2 * u, hy = yg - 5.15 * u;
  const cloth = fog(body);
  let s = '';
  // neck, longer than usual: the head is tipped right back
  s += rect(hx - 0.24 * u, hy + 0.5 * u, 0.48 * u, top - hy - 0.3 * u, { fill: fog(SKIN_UNDER), ...ik });
  s += path(`M${F(x - 0.6 * u)} ${F(bot)} L${F(x - 0.66 * u)} ${F(top + 0.3 * u)} Q${F(x - 0.66 * u)} ${F(top)} ${F(x - 0.34 * u)} ${F(top)} L${F(x + 0.34 * u)} ${F(top)} Q${F(x + 0.66 * u)} ${F(top)} ${F(x + 0.66 * u)} ${F(top + 0.3 * u)} L${F(x + 0.6 * u)} ${F(bot)} Z`, { fill: cloth, ...ik });
  if (detail >= 1) {
    // collar, a tear, the light along the wet shoulder
    s += path(`M${F(x - 0.3 * u)} ${F(top + 0.02 * u)} L${F(x)} ${F(top + 0.32 * u)} L${F(x + 0.3 * u)} ${F(top + 0.02 * u)}`, { fill: 'none', stroke: mix(cloth, '#000000', 0.35), strokeWidth: lw * 0.8, strokeLinejoin: 'round' });
    s += path(`M${F(x + 0.2 * u)} ${F(top + 1.6 * u)} l${F(0.08 * u)} ${F(-0.22 * u)} l${F(0.08 * u)} ${F(0.22 * u)}`, { fill: mix(cloth, '#000000', 0.3), stroke: INK, strokeWidth: lw * 0.5 });
    s += path(`M${F(x + 0.36 * u)} ${F(top + 0.04 * u)} Q${F(x + 0.62 * u)} ${F(top + 0.04 * u)} ${F(x + 0.62 * u)} ${F(top + 0.4 * u)}`, { fill: 'none', stroke: RIM, strokeWidth: 0.09 * u, strokeLinecap: 'round', opacity: 0.55 * rimOp });
    // arms hanging limp at the sides: they are not reaching for anything
    for (const side of [-1, 1]) {
      const sx = x + side * 0.58 * u, sy = top + 0.25 * u, ex = x + side * 0.74 * u, ey = top + 1.85 * u;
      s += path(`M${F(sx)} ${F(sy)} Q${F(x + side * 0.86 * u)} ${F(top + 1.0 * u)} ${F(ex)} ${F(ey)}`, { fill: 'none', ...ik }) + circle(ex, ey, 0.17 * u, { fill: fog(SKIN), ...ik });
    }
  }
  const hd = upHead(hx, hy, u, { skin: fog(SKIN), under: fog(SKIN_UNDER), socket: mix(SOCKET, HAZE, fogK * 0.5), pupil: PUPIL, rim: RIM, rimOp, lw, detail, r, hair: hair ? fog(hair) : null });
  s += g(hd, { transform: `rotate(${F(tilt)} ${F(hx)} ${F(hy + u)})` });
  return s;
}
// rows of them from the far edge of the lot forward; `skip(x, y)` keeps a corridor clear
function rows({ list, seed, skip = () => false }) {
  const r = rng(seed);
  let out = '';
  for (const R of list) {
    const u = 60 * R.s, n = Math.round((R.x1 - R.x0) / (u * R.dens));
    for (let i = 0; i < n; i++) {
      const x = R.x0 + ((i + 0.5 + (r() - 0.5) * 0.6) * (R.x1 - R.x0)) / n, yg = R.y + (r() - 0.5) * u * 0.5;
      const body = CLOTHES[Math.floor(r() * CLOTHES.length)], tilt = (r() - 0.5) * 22, hair = r() < 0.45 ? HAIR[Math.floor(r() * HAIR.length)] : null;
      const sc = R.s * (0.92 + r() * 0.16);
      if (skip(x, yg, sc)) continue;
      // nearer the bolt (right), a little brighter rim
      out += upZombie(x, yg, sc, { body, fogK: R.fog, detail: R.detail, r, tilt, rimOp: R.rim * (0.75 + 0.25 * (x / W)), hair });
    }
  }
  return g(out, { filter: 'url(#wobbleSoft)' });
}

// ---------- you: walking through them, head a little down, finger at the lips, hammer ready ----------
function heroHead(cx, cy, u, { down = 0.08, rim, id = 'sbh' }) {
  let s = circle(cx, cy, u, { fill: PAL.skin });
  s += `<mask id="rim_${id}"><circle cx="${F(cx)}" cy="${F(cy)}" r="${F(u)}" fill="#fff"/><circle cx="${F(cx - rim.side * 0.17 * u)}" cy="${F(cy + 0.08 * u)}" r="${F(u)}" fill="#000"/></mask>`
    + circle(cx, cy, u, { fill: rim.color, opacity: rim.op, mask: `url(#rim_${id})` });
  // hair, rain-flattened: the canon cap with a heavier fringe; the cowlick still stands
  const hx = cx - u, hy = cy, dy = down * 0.6 * u;
  s += path(`M${F(hx + 0.02 * u)} ${F(hy - 0.05 * u)} C${F(hx - 0.02 * u)} ${F(hy - 1.1 * u)} ${F(cx + 1.1 * u)} ${F(cy - 1.25 * u)} ${F(cx + 0.98 * u)} ${F(cy - 0.12 * u)} L${F(cx + 0.7 * u)} ${F(cy - 0.4 * u + dy)} L${F(cx + 0.48 * u)} ${F(cy - 0.27 * u + dy)} L${F(cx + 0.18 * u)} ${F(cy - 0.47 * u + dy)} L${F(cx - 0.12 * u)} ${F(cy - 0.33 * u + dy)} L${F(cx - 0.45 * u)} ${F(cy - 0.5 * u + dy)} L${F(cx - 0.72 * u)} ${F(cy - 0.3 * u + dy)} Z`, { fill: PAL.hair, ...ink(0.04 * u) });
  s += path(`M${F(cx + rim.side * 0.6 * u)} ${F(cy - 0.8 * u)} Q${F(cx + rim.side * 0.95 * u)} ${F(cy - 0.52 * u)} ${F(cx + rim.side * 0.98 * u)} ${F(cy - 0.14 * u)}`, { fill: 'none', stroke: rim.color, strokeWidth: 0.07 * u, strokeLinecap: 'round', opacity: 0.85 });
  const lick = `M${F(cx + 0.05 * u)} ${F(cy - 0.98 * u)} q${F(0.1 * u)} ${F(-0.35 * u)} ${F(0.38 * u)} ${F(-0.3 * u)}`;
  s += path(lick, { fill: 'none', stroke: INK, strokeWidth: 0.19 * u, strokeLinecap: 'round' }) + path(lick, { fill: 'none', stroke: PAL.hair, strokeWidth: 0.11 * u, strokeLinecap: 'round' });
  // wet: drops on the hair, one on the temple
  for (const [dx, dy, k] of [[-0.55, -0.62, 1], [0.3, -0.78, 0.8], [0.72, -0.45, 0.9]]) s += ellipse(cx + dx * u, cy + dy * u, 0.04 * u * k, 0.06 * u * k, { fill: '#CFE4FF', opacity: 0.9 });
  s += path(`M${F(cx - 0.8 * u)} ${F(cy - 0.08 * u)} q${F(0.05 * u)} ${F(0.09 * u)} 0 ${F(0.13 * u)} q${F(-0.05 * u)} ${F(-0.04 * u)} 0 ${F(-0.13 * u)}`, { fill: '#BFE0F5', ...ink(0.018 * u) });
  // serious eyes under heavy lids, looking straight out at you; brows down to the nose
  const ex = cx, ey = cy + 0.04 * u + down * u, sp = 0.5 * u;
  for (const side of [-1, 1]) {
    const x0 = ex + side * sp / 2;
    s += ellipse(x0, ey, 0.13 * u, 0.19 * u, { fill: INK });
    s += circle(x0 + 0.045 * u, ey - 0.075 * u, 0.048 * u, { fill: '#FFFFFF' }) + circle(x0 - 0.04 * u, ey + 0.07 * u, 0.022 * u, { fill: '#FFFFFF' });
    const base = ey - 0.19 * u + 0.36 * 0.38 * u, tilt = 0.05 * u;
    const yo = base - tilt, yi = base + tilt, xo = x0 + side * 0.17 * u, xi = x0 - side * 0.17 * u;
    s += poly([[xo, ey - 0.26 * u], [xi, ey - 0.26 * u], [xi, yi], [xo, yo]], { fill: PAL.skin }) + line(xo, yo, xi, yi, ink(0.05 * u));
    s += circle(x0 + 0.04 * u, (yo + yi) / 2 + 0.07 * u, 0.03 * u, { fill: '#FFFFFF' });
    const by = ey - 0.3 * u;
    s += line(x0 + side * 0.16 * u, by - 0.01 * u, x0 - side * 0.13 * u, by + 0.11 * u, ink(0.065 * u));
  }
  const mx = ex, my = cy + 0.5 * u + down * u;
  s += path(`M${F(mx - 0.15 * u)} ${F(my + 0.05 * u)} Q${F(mx)} ${F(my - 0.04 * u)} ${F(mx + 0.15 * u)} ${F(my + 0.05 * u)}`, { fill: 'none', ...ink(0.055 * u) });
  s += circle(cx, cy, u, { fill: 'none', ...ink(0.045 * u) });
  return s;
}
function hammer(hx, hy, u, ang) {
  // claw hammer, (hx, hy) = the grip, pointing along `ang` (degrees) from the grip to the head
  const k = u / 100;
  let s = rect(-8 * k, -14 * k, 150 * k, 28 * k, { rx: 12 * k, fill: '#9A6440', ...ink(4 * k + 1) });
  s += line(20 * k, -6 * k, 120 * k, -6 * k, { stroke: '#C08A5C', strokeWidth: 5 * k, strokeLinecap: 'round' });
  s += rect(-30 * k, -16 * k, 46 * k, 32 * k, { rx: 10 * k, fill: '#2A2C30', ...ink(3.5 * k + 1) });   // rubber grip
  const hd = `M${136 * k} ${-62 * k} L${172 * k} ${-62 * k} L${172 * k} ${36 * k} Q${200 * k} ${50 * k} ${214 * k} ${86 * k} Q${180 * k} ${78 * k} ${160 * k} ${58 * k} L${136 * k} ${58 * k} Z`;
  s += path(hd, { fill: '#8E98A3', ...ink(4 * k + 1) });
  s += rect(128 * k, -84 * k, 52 * k, 30 * k, { rx: 6 * k, fill: '#AEB8C2', ...ink(4 * k + 1) });   // striking face
  s += line(178 * k, -76 * k, 178 * k, -60 * k, { stroke: '#FFFFFF', strokeWidth: 5 * k, strokeLinecap: 'round', opacity: 0.9 });   // lightning glint
  return g(s, { transform: `translate(${F(hx)} ${F(hy)}) rotate(${ang})` });
}
function you(x, y, sc) {
  const u = 60 * sc, shY = y - 4.05 * u, neckY = y - 4.25 * u, hipY = y - 2.2 * u, cx = x, cy = y - 5.25 * u, lw = Math.max(4, 0.1 * u);
  const tw = 0.62 * u, bw = 0.56 * u, top = shY - 0.15 * u, bot = hipY + 0.1 * u;
  let b = '';
  // jacket, its hood down behind the neck
  b += path(`M${F(x - tw)} ${F(top + 0.2 * u)} Q${F(x - tw)} ${F(top)} ${F(x - tw + 0.25 * u)} ${F(top)} L${F(x + tw - 0.25 * u)} ${F(top)} Q${F(x + tw)} ${F(top)} ${F(x + tw)} ${F(top + 0.2 * u)} L${F(x + bw)} ${F(bot)} L${F(x - bw)} ${F(bot)} Z`, { fill: PAL.jacket, ...ink(0.045 * u) });
  b += path(`M${F(x + tw - 0.06 * u)} ${F(top + 0.16 * u)} L${F(x + bw - 0.04 * u)} ${F(bot)}`, { fill: 'none', stroke: '#C9B8FF', strokeWidth: 0.07 * u, opacity: 0.6, strokeLinecap: 'round' });   // the flash along the wet jacket
  b += line(x + 0.04 * u, top + 0.12 * u, x + 0.04 * u, bot - 0.05 * u, { stroke: PAL.jacketDark, strokeWidth: 0.04 * u });
  b += path(`M${F(x - 0.42 * u)} ${F(bot - 0.75 * u)} h${F(0.28 * u)}`, { stroke: PAL.jacketDark, strokeWidth: 0.035 * u, fill: 'none' }) + path(`M${F(x + 0.16 * u)} ${F(bot - 0.75 * u)} h${F(0.28 * u)}`, { stroke: PAL.jacketDark, strokeWidth: 0.035 * u, fill: 'none' });
  b += path(`M${F(x - 0.55 * u)} ${F(top + 0.05 * u)} Q${F(x)} ${F(top - 0.32 * u)} ${F(x + 0.55 * u)} ${F(top + 0.05 * u)} Q${F(x)} ${F(top + 0.3 * u)} ${F(x - 0.55 * u)} ${F(top + 0.05 * u)} Z`, { fill: PAL.jacketDark, ...ink(0.035 * u) });
  // headphones around the neck
  const hp = `M${F(x - 0.55 * u)} ${F(neckY - 0.05 * u)} Q${F(x)} ${F(neckY + 0.55 * u)} ${F(x + 0.55 * u)} ${F(neckY - 0.05 * u)}`;
  b += path(hp, { fill: 'none', stroke: INK, strokeWidth: 0.2 * u }) + path(hp, { fill: 'none', stroke: PAL.phones, strokeWidth: 0.11 * u });
  b += rect(x - 0.86 * u, neckY - 0.3 * u, 0.36 * u, 0.5 * u, { rx: 0.12 * u, fill: PAL.phones, ...ink(0.035 * u) }) + rect(x + 0.5 * u, neckY - 0.3 * u, 0.36 * u, 0.5 * u, { rx: 0.12 * u, fill: PAL.phones, ...ink(0.035 * u) });
  // the hammer arm (your right, our left): elbow out, the grip at the chest, the head up by the shoulder
  const grip = [x - 0.18 * u, shY + 0.95 * u];
  b += path(`M${F(x - 0.5 * u)} ${F(shY + 0.05 * u)} Q${F(x - 0.95 * u)} ${F(shY + 1.05 * u)} ${F(grip[0])} ${F(grip[1])}`, { fill: 'none', ...ink(lw) });
  const hm = hammer(grip[0], grip[1], u * 0.95, -128);
  // the shush arm (your left, our right): up to the lips
  const fist = [cx + 0.12 * u, cy + 1.02 * u];
  b += path(`M${F(x + 0.5 * u)} ${F(shY + 0.05 * u)} Q${F(x + 1.05 * u)} ${F(shY + 0.75 * u)} ${F(fist[0] + 0.08 * u)} ${F(fist[1] + 0.06 * u)}`, { fill: 'none', ...ink(lw) });
  const hd = heroHead(cx, cy, u, { down: 0.08, rim: { color: '#CDBEFF', side: 1, op: 0.8 } });
  // the hand at the lips: a fist under the chin, one finger up across the mouth
  let fr = circle(fist[0], fist[1], 0.17 * u, { fill: PAL.skin, ...ink(0.04 * u) });
  fr += rect(cx + 0.03 * u, cy + 0.36 * u, 0.13 * u, 0.62 * u, { rx: 0.065 * u, fill: PAL.skin, ...ink(0.035 * u) });
  fr += line(cx + 0.06 * u, cy + 0.44 * u, cx + 0.13 * u, cy + 0.44 * u, { stroke: '#D9CFC0', strokeWidth: 0.02 * u, strokeLinecap: 'round' });   // the nail
  const gripHand = circle(grip[0], grip[1], 0.17 * u, { fill: PAL.skin, ...ink(0.04 * u) });
  return g(g(b + hm + gripHand + hd + fr, { filter: 'url(#wobbleSoft)' }), { filter: 'url(#pro_stk)' });
}

// ---------- rain ----------
function rain({ n, seed, len = [60, 120], w = 3, op = 0.4, col = '#D5E4F5', slant = 0.34, y0 = -60, y1 = H + 60, blur }) {
  const r = rng(seed); let s = '';
  for (let i = 0; i < n; i++) {
    const x = -200 + r() * (W + 400), y = y0 + r() * (y1 - y0), L = lerp(len[0], len[1], r());
    s += line(x, y, x - slant * L, y + L, { stroke: col, strokeWidth: w * (0.8 + r() * 0.4), strokeLinecap: 'round', opacity: (op * (0.6 + r() * 0.4)).toFixed(2) });
  }
  return blur ? g(s, { filter: `url(#${blur})` }) : s;
}

function thumbStorm() {
  const HX = 1185, HY = 1455, HS = 2.7, HU = 60 * HS;
  let s = sky() + lightning() + horizon();
  // the lot, packed to the far edge: back rows small and hazy, nearer rows bigger and sharper
  const far = [];
  for (let i = 0; i < 6; i++) { const t = i / 5; far.push({ x0: -60, x1: W + 60, y: lerp(640, 820, t), s: lerp(0.27, 0.62, t), dens: 1.35, fog: lerp(0.55, 0.3, t), detail: t > 0.6 ? 1 : 0, rim: lerp(0.5, 0.8, t) }); }
  s += rows({ list: far, seed: 3 });
  s += rect(0, 0, W, H, { fill: '#6F64C8', opacity: 0.07, style: 'mix-blend-mode:screen' });
  // the rows around you: packed close on both sides, behind your shoulders
  const mid = [
    { x0: -80, x1: W + 80, y: 960, s: 0.9, dens: 1.5, fog: 0.2, detail: 1, rim: 0.85 },
    { x0: -80, x1: W + 80, y: 1110, s: 1.25, dens: 1.6, fog: 0.1, detail: 1, rim: 0.9 },
  ];
  s += rows({ list: mid, seed: 9, skip: (x) => Math.abs(x - HX) < 120 });
  s += rain({ n: 260, seed: 4, len: [50, 100], w: 2.6, op: 0.32 });
  const r = rng(51);
  // the two right beside you, a step behind
  s += g(upZombie(HX - 430, 1380, 2.05, { body: '#C76A83', fogK: 0, detail: 2, r, tilt: -6, hair: '#5B4636' })
    + upZombie(HX + 445, 1395, 2.1, { body: '#6FA3A6', fogK: 0, detail: 2, r, tilt: 7, rimOp: 1 }), { filter: 'url(#wobbleSoft)' });
  // light from the bolt washing the crowd from the upper right
  s += bloom(1650, 520, 700, 330, '#B6A6FF', 0.28);
  // you
  s += bloom(HX, 640, 320, 300, '#8E7FE0', 0.25);
  s += you(HX, HY, HS);
  // the nearest ones, at the edges of frame, cropped: faces up, mouths open to the rain
  s += g(upZombie(110, 1700, 3.0, { body: '#D9A441', fogK: 0, detail: 2, r, tilt: -10, hair: '#2B2B2E' })
    + upZombie(560, 1790, 2.65, { body: '#2E3D55', fogK: 0, detail: 2, r, tilt: 8 })
    + upZombie(1790, 1720, 3.0, { body: '#B5452F', fogK: 0, detail: 2, r, tilt: 9, rimOp: 1, hair: '#7A6A55' }), { filter: 'url(#wobbleSoft)' });
  // the downpour over everything, heavier and softer up close
  s += rain({ n: 120, seed: 8, len: [120, 220], w: 4.5, op: 0.4, blur: 'sb_rainblur' });
  s += grade('#3B2F6E', 0.12);
  s += headline(64, 210, 'WAIT FOR', { size: 178, anchor: 'start' }) + headline(56, 438, 'THUNDER', { size: 250, anchor: 'start', fill: 'url(#pro_red)' });
  s += finish({ vignette: 0.5, grain: 0.05 });
  return { w: W, h: H, svg: svgOf(s, 10), css: 'saturate(1.14) contrast(1.06)' };
}

export default () => thumbStorm();
