// LAST LIGHT ep. 2 · A/B concept A "S.O.S." — Day 9, night. From Freshway's roof you watch one top-floor window of
// Brookfield Mall blink three short, three long, three short. Two hundred of the dead stand in the lot between.
// One idea: the warm light across the dark. Deep blue night, one warm light, the headline in that light's colour.
import { W, H, INK, PAL, finish, g, rect, circle, ellipse, line, poly, path, text, ink, rng } from '../../lib.js';
import { svgOf, headline, bloom, actor } from '../v2/pro.js';
import { horde } from '../v2/pro3.js';

const F = (n) => (+n).toFixed(1);
const WARM = '#FFD46A';

// ---------- the sky: deep blue, a cool moon glow off-frame top left, a few stars ----------
function sky() {
  let s = `<defs><linearGradient id="sosA_sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#070D24"/><stop offset="0.55" stop-color="#132658"/><stop offset="1" stop-color="#2A4C86"/></linearGradient></defs>`;
  s += rect(0, 0, W, H, { fill: 'url(#sosA_sky)' });
  const r = rng(19);
  for (let i = 0; i < 120; i++) s += circle(r() * W, r() * 620, 0.8 + r() * 2.1, { fill: '#FFFFFF', opacity: (0.25 + r() * 0.6).toFixed(2) });
  s += bloom(120, -40, 700, 420, '#6E96E6', 0.28);
  return s;
}

// ---------- Brookfield Mall: a dark block across the lot, glass skylight on top, one window lit ----------
const MALL = { x0: 780, x1: 2000, roof: 180, ground: 660 };
const COLS = [], CW = 200, GAP = 34;
for (let x = MALL.x0 + 40; x < MALL.x1; x += CW + GAP) COLS.push(x);
const FLOORS = [[272, 150], [442, 84], [544, 62], [624, 36]];
const WIN = { x: COLS[3], y: FLOORS[0][0], w: CW, h: FLOORS[0][1] };   // the lit window, top floor (Bright Tech)
function mall() {
  const { x0, x1, roof, ground } = MALL;
  let s = '';
  // the glass skylight vault over the atrium, catching a little moonlight
  const vx = 1190, vr = 280, vh = 150, vy = roof - 10;
  const dome = `M${vx - vr} ${vy} A${vr} ${vh} 0 0 1 ${vx + vr} ${vy} Z`;
  s += `<defs><clipPath id="sosA_dome"><path d="${dome}"/></clipPath></defs>` + path(dome, { fill: '#1C2B4C' });
  let ribs = '';
  for (let i = -3; i <= 3; i++) ribs += path(`M${vx + i * 70} ${vy} Q${vx + i * 52} ${vy - vh * 0.8} ${vx + i * 20} ${vy - vh}`, { fill: 'none', stroke: '#0C1326', strokeWidth: 6 });
  for (const k of [0.4, 0.75]) ribs += line(vx - vr, vy - vh * k, vx + vr, vy - vh * k, { stroke: '#0C1326', strokeWidth: 6 });
  s += g(ribs, { clipPath: 'url(#sosA_dome)' }) + path(dome, { fill: 'none', ...ink(6) });
  s += path(`M${vx - vr + 34} ${vy - 52} A${vr - 30} ${vh - 22} 0 0 1 ${vx - 60} ${vy - vh + 10}`, { fill: 'none', stroke: '#86A8E6', strokeWidth: 8, strokeLinecap: 'round', opacity: 0.6 });
  // the block
  s += rect(x0, roof, x1 - x0, ground - roof, { fill: '#121A30', ...ink(7) });
  s += rect(x0 - 10, roof - 16, x1 - x0 + 20, 30, { fill: '#0D1426', ...ink(6) });
  s += line(x0 + 6, roof + 18, x0 + 6, ground, { stroke: '#4A6AA8', strokeWidth: 6, opacity: 0.5 });   // moonlit corner
  // sign band, unlit
  s += rect(x0, roof + 14, x1 - x0, 64, { fill: '#0F1729', ...ink(5) });
  s += text(1150, roof + 64, 'BROOKFIELD MALL', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 48, fill: '#34445F', textAnchor: 'middle', letterSpacing: 10 });
  // four floors of dark glass
  FLOORS.forEach(([y, h], fl) => {
    s += line(x0, y - 10, x1, y - 10, { stroke: '#0A1020', strokeWidth: 6 });
    for (const x of COLS) {
      if (fl === 0 && x === WIN.x) continue;
      s += rect(x, y, CW, h, { fill: '#182540', ...ink(4) });
      s += line(x + CW * 0.2, y + h - 6, x + CW * 0.45, y + 6, { stroke: '#3B5A92', strokeWidth: 5, opacity: 0.35 });
    }
  });
  return s;
}
// the lit window: hot glass, a girl's shape holding the lantern up, a glint
function litWindow() {
  const { x, y, w, h } = WIN, cx = x + w / 2, cy = y + h / 2;
  let s = `<defs><radialGradient id="sosA_win" cx="0.7" cy="0.3" r="0.85"><stop offset="0" stop-color="#FFFDF2"/><stop offset="0.4" stop-color="#FFEBA8"/><stop offset="1" stop-color="#FFB040"/></radialGradient>
    <linearGradient id="sosA_ray" x1="1" y1="0" x2="0" y2="0"><stop offset="0" stop-color="#FFE7A0" stop-opacity="0.55"/><stop offset="1" stop-color="#FFE7A0" stop-opacity="0"/></linearGradient></defs>`;
  // soft god rays fanning out of the window, fading with distance
  s += `<defs><radialGradient id="sosA_rayg" gradientUnits="userSpaceOnUse" cx="${cx}" cy="${cy}" r="820"><stop offset="0" stop-color="#FFE2A0" stop-opacity="0.34"/><stop offset="0.35" stop-color="#FFD890" stop-opacity="0.12"/><stop offset="1" stop-color="#FFD890" stop-opacity="0"/></radialGradient></defs>`;
  let rays = '';
  for (const [a, sp] of [[-196, 7], [-178, 4], [-160, 6], [-138, 3], [-40, 4], [-16, 5], [168, 5], [14, 3]]) {
    const a0 = ((a - sp / 2) * Math.PI) / 180, a1 = ((a + sp / 2) * Math.PI) / 180, len = 820;
    rays += poly([[cx, cy], [cx + Math.cos(a0) * len, cy + Math.sin(a0) * len], [cx + Math.cos(a1) * len, cy + Math.sin(a1) * len]], { fill: 'url(#sosA_rayg)' });
  }
  s += g(rays, { filter: 'url(#pro_glowS)', style: 'mix-blend-mode:screen' });
  s += bloom(cx, cy, 280, 200, '#FFA62E', 0.32) + bloom(cx, cy, 150, 110, WARM, 0.6);
  s += rect(x, y, w, h, { fill: 'url(#sosA_win)', ...ink(5) });
  // the person in the window, a dark shape against the glow, arm up with the lantern
  const k = h / 112, px = x + 0.34 * w, py = y + h, C = '#2A1A14';
  s += path(`M${F(px - 46 * k)} ${py} Q${F(px - 44 * k)} ${F(py - 50 * k)} ${F(px)} ${F(py - 54 * k)} Q${F(px + 44 * k)} ${F(py - 50 * k)} ${F(px + 46 * k)} ${py} Z`, { fill: C });
  s += circle(px, py - 78 * k, 24 * k, { fill: C }) + path(`M${F(px - 20 * k)} ${F(py - 90 * k)} Q${F(px - 36 * k)} ${F(py - 58 * k)} ${F(px - 30 * k)} ${F(py - 38 * k)}`, { fill: 'none', stroke: C, strokeWidth: 12 * k, strokeLinecap: 'round' });
  // the arm straight up, the lantern hanging from the hand by its bail
  const hx = x + 0.7 * w, hy = y + 0.1 * h, lx = hx, ly = y + 0.36 * h;
  s += path(`M${F(px + 30 * k)} ${F(py - 42 * k)} Q${F(hx - 8 * k)} ${F(py - 62 * k)} ${F(hx)} ${F(hy + 6 * k)}`, { fill: 'none', stroke: C, strokeWidth: 15 * k, strokeLinecap: 'round' });
  s += path(`M${F(lx - 11 * k)} ${F(ly - 16 * k)} Q${F(lx)} ${F(hy - 6 * k)} ${F(lx + 11 * k)} ${F(ly - 16 * k)}`, { fill: 'none', stroke: C, strokeWidth: 4 * k });
  s += rect(lx - 15 * k, ly - 18 * k, 30 * k, 38 * k, { rx: 7 * k, fill: '#FFFFFF', stroke: C, strokeWidth: 4 * k }) + rect(lx - 17 * k, ly - 22 * k, 34 * k, 7 * k, { rx: 3 * k, fill: C });
  s += line(x + w * 0.86, y, x + w * 0.86, y + h, { stroke: INK, strokeWidth: 5 }) + line(x, y + h * 0.62, x + w * 0.34 - 50 * k, y + h * 0.62, { stroke: INK, strokeWidth: 4, opacity: 0.0 });
  s += bloom(lx, ly, 56, 56, '#FFFFFF', 0.85, true) + bloom(lx, ly, 22, 22, '#FFFFFF', 1, true);
  s += g(path(`M${F(lx)} ${F(ly - 110)} L${F(lx + 7)} ${F(ly)} L${F(lx)} ${F(ly + 110)} L${F(lx - 7)} ${F(ly)} Z M${F(lx - 150)} ${F(ly)} L${F(lx)} ${F(ly - 7)} L${F(lx + 150)} ${F(ly)} L${F(lx)} ${F(ly + 7)} Z`, { fill: '#FFFBEA' }), { opacity: 0.9, style: 'mix-blend-mode:screen' });
  return s;
}

// ---------- the signal: · · · — — — · · · flying out of the window toward you ----------
function morse(pts) {
  let glow = '', marks = '';
  pts.forEach(([x, y, a, k], i) => {
    const dash = i >= 3 && i <= 5, r = 25 * k, len = 96 * k, tr = `translate(${F(x)} ${F(y)}) rotate(${F(a)})`;
    const shape = (o) => (dash ? rect(-len / 2, -r, len, 2 * r, { rx: r, ...o }) : circle(0, 0, r, o));
    glow += g(shape({ fill: WARM }), { transform: tr });
    marks += g(shape({ fill: 'url(#sosA_mk)', ...ink(Math.max(6, 9 * k)) }), { transform: tr });
  });
  return `<defs><linearGradient id="sosA_mk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFBEA"/><stop offset="1" stop-color="#FFC94A"/></linearGradient></defs>`
    + g(glow, { filter: 'url(#pro_glow)', opacity: 0.8, style: 'mix-blend-mode:screen' }) + g(marks, { filter: 'url(#pro_shadow)' });
}
// the nine marks along a quadratic curve, Morse spacing, growing as they come closer
function morsePath(P0, P1, P2, k0 = 0.7, k1 = 1.25) {
  const q = (t) => [(1 - t) ** 2 * P0[0] + 2 * (1 - t) * t * P1[0] + t * t * P2[0], (1 - t) ** 2 * P0[1] + 2 * (1 - t) * t * P1[1] + t * t * P2[1]];
  const L = [1, 1, 1, 2.6, 2.6, 2.6, 1, 1, 1];
  const pos = []; let c = 0;
  L.forEach((l, i) => { if (i) c += i === 3 || i === 6 ? 1.7 : 0.8; pos.push(c + l / 2); c += l; });
  return pos.map((p) => {
    const t = p / c, [x, y] = q(t), [x2, y2] = q(Math.min(1, t + 0.01)), [x1, y1] = q(Math.max(0, t - 0.01));
    let a = (Math.atan2(y2 - y1, x2 - x1) * 180) / Math.PI; if (a > 90) a -= 180; if (a < -90) a += 180;
    return [x, y, a, k0 + (k1 - k0) * t];
  });
}

// ---------- props ----------
function binoculars(x, y, u) {
  // resting on the ledge in both hands, lenses toward us
  let s = rect(x - 0.52 * u, y - 0.22 * u, 1.04 * u, 0.3 * u, { rx: 0.1 * u, fill: '#2A2C30', ...ink(0.045 * u) });
  for (const side of [-1, 1]) {
    const bx = x + side * 0.3 * u;
    s += circle(bx, y + 0.06 * u, 0.27 * u, { fill: '#33363C', ...ink(0.05 * u) }) + circle(bx, y + 0.06 * u, 0.18 * u, { fill: '#121418', ...ink(0.03 * u) });
    s += path(`M${F(bx - 0.1 * u)} ${F(y - 0.02 * u)} A${F(0.13 * u)} ${F(0.13 * u)} 0 0 1 ${F(bx + 0.06 * u)} ${F(y - 0.06 * u)}`, { fill: 'none', stroke: '#8FB4FF', strokeWidth: 0.04 * u, strokeLinecap: 'round' });
  }
  s += rect(x - 0.08 * u, y - 0.3 * u, 0.16 * u, 0.2 * u, { rx: 0.04 * u, fill: '#1E2024', ...ink(0.03 * u) });
  return s;
}
// a short, sharp cowlick (the canon one, drawn tighter so it reads as hair at thumbnail size, not a sprout)
function cowlick(cx, cy, u) {
  const d = `M${F(cx - 0.02 * u)} ${F(cy - 0.96 * u)} q${F(0.02 * u)} ${F(-0.24 * u)} ${F(0.3 * u)} ${F(-0.26 * u)}`;
  return path(d, { fill: 'none', stroke: INK, strokeWidth: 0.2 * u, strokeLinecap: 'round' }) + path(d, { fill: 'none', stroke: PAL.hair, strokeWidth: 0.11 * u, strokeLinecap: 'round' });
}

// ---------- Freshway's roof parapet across the foreground: you on this side, the dead beyond ----------
function parapet(top) {
  let s = rect(-30, top + 26, W + 60, H - top, { fill: '#1A2236', ...ink(7) });
  s += rect(-30, top, W + 60, 40, { rx: 8, fill: '#46557A', ...ink(7) });
  s += line(0, top + 11, W, top + 11, { stroke: '#9DB6EA', strokeWidth: 6, strokeLinecap: 'round', opacity: 0.5 });
  for (let x = 150; x < W; x += 300) s += line(x, top + 42, x, H, { stroke: '#10172A', strokeWidth: 5 });
  return g(s, { filter: 'url(#wobbleSoft)' });
}

function thumb() {
  let s = sky();
  s += bloom(WIN.x + WIN.w / 2, WIN.y + 60, 700, 460, '#FF9A3A', 0.07);
  s += mall() + litWindow();
  // the lot and the dead filling it, moonlit from the left, faces you can read
  s += rect(0, MALL.ground, W, H - MALL.ground, { fill: '#1A2236' }) + line(0, MALL.ground, W, MALL.ground, ink(5));
  s += bloom(1150, 880, 900, 260, '#7FA0E0', 0.26);
  // back rows: small, fogged, a touch soft so the front rows and the window win
  s += g(horde({ x0: -60, x1: 2000, yb: 690, yf: 880, rows: 4, s0: 0.32, s1: 0.72, seed: 43, arms: 0.5, rim: '#B8CCF5', rimSide: -1, fog: '#16203A', fogK: 0.62, density: 1.4 }), { filter: 'url(#pro_b1)' });
  // front rows: big, in colour, faces you can read
  s += horde({ x0: -60, x1: 2000, yb: 1010, yf: 1225, rows: 2, s0: 1.0, s1: 1.32, seed: 41, arms: 0.7, rim: '#CFE0FF', rimSide: -1, fog: '#16203A', fogK: 0.18, density: 1.38 });
  // you, on Freshway's roof: binoculars down on the ledge, looking across at the window
  const sc = 2.8, gx = 450, gy = 1455, u = 60 * sc, top = 984;
  const cy = gy - 5.25 * u, by = top - 0.3 * u;
  s += bloom(gx, 600, 400, 440, '#3E64B0', 0.35);
  const hands = circle(gx - 0.5 * u, by + 0.06 * u, 0.15 * u, { fill: PAL.skin, ...ink(4) }) + circle(gx + 0.5 * u, by + 0.06 * u, 0.15 * u, { fill: PAL.skin, ...ink(4) });
  s += actor({ x: gx, y: gy, s: sc, pose: 'carry', face: 'serious', look: 0.55, scratch: true, lick: false, id: 'sosA', rim: { color: '#FFC070', side: 1, op: 0.7 },
    extra: binoculars(gx, by, u) + hands, front: cowlick(gx, cy, u) });
  s += parapet(top);
  // the signal, from the window across the lot to you
  s += morse(morsePath([WIN.x - 34, WIN.y + 92], [1200, 450], [790, 505]));
  s += headline(56, 300, 'S.O.S.', { size: 310, anchor: 'start', fill: 'url(#pro_yel)', sw: 30, ls: 6 });
  s += finish({ vignette: 0.5, grain: 0.05 });
  return { w: W, h: H, svg: svgOf(s, 9), css: 'saturate(1.12) contrast(1.06)' };
}

export default () => thumb();
