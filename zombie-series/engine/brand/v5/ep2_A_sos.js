// LAST LIGHT ep. 2 · A/B concept A "S.O.S." — Day 9, night. From Freshway's roof you watch one top-floor window of
// Brookfield Mall blink three short, three long, three short. Two hundred of the dead stand in the lot between.
// One idea: the warm light across the dark. Deep blue night, one warm light, the headline in that light's colour.
import { W, H, INK, PAL, finish, g, rect, circle, ellipse, line, poly, path, text, ink, rng } from '../../lib.js';
import { svgOf, headline, bloom, actor } from '../v2/pro.js';

const F = (n) => (+n).toFixed(1);
const WARM = '#FFD46A';

// ---------- the horde (pro3's horde(), with a palette and skin of our own: brighter clothes for the front rows) ----------
const lerp = (a, b, k) => a + (b - a) * k;
function mix(a, b, k) {
  const p = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const A = p(a), B = p(b);
  return '#' + A.map((v, i) => Math.round(lerp(v, B[i], k)).toString(16).padStart(2, '0')).join('');
}
const CLOTHES = ['#4FA3A8', '#D0668A', '#8A6FB0', '#C9A24A', '#C2603F', '#4F78B8', '#8C8C86', '#6E9A5A', '#B8453A', '#6FA3A6', '#7C6A8E'];
function horde({ x0, x1, yb, yf, rows = 6, s0 = 0.42, s1 = 1.3, seed = 1, arms = 0.75, rim = '#CFE0FF', rimSide = -1, fog = '#0B0F1E', fogK = 0.65, density = 1.55, skin = '#93A487', clothes = CLOTHES }) {
  const r = rng(seed); let out = '';
  for (let row = 0; row < rows; row++) {
    const t = rows > 1 ? row / (rows - 1) : 1, y = lerp(yb, yf, t * t * 0.5 + t * 0.5), sc = lerp(s0, s1, t * t), u = 60 * sc;
    const dim = fogK * (1 - t), lw = Math.max(2.5, 0.09 * u);
    const n = Math.max(3, Math.round((x1 - x0) / (u * density)));
    for (let i = 0; i < n; i++) {
      const x = x0 + ((i + 0.5 + (r() - 0.5) * 0.7) * (x1 - x0)) / n, yy = y + (r() - 0.5) * u * 0.6;
      const sk = mix(skin, fog, dim), body = mix(clothes[Math.floor(r() * clothes.length)], fog, dim), ink2 = { stroke: mix(INK, fog, dim * 0.4), strokeWidth: lw, strokeLinecap: 'round', strokeLinejoin: 'round' };
      const hx = x + (r() - 0.5) * 0.3 * u, hy = yy - 5.15 * u, tilt = (r() - 0.5) * 26;
      let z = rect(x - 0.62 * u, yy - 4.2 * u, 1.24 * u, 2.3 * u, { rx: 0.28 * u, fill: body, ...ink2 });
      if (r() < arms) for (const side of [-1, 1]) {
        const ax = x + side * (0.75 + r() * 0.45) * u, ay = yy - (6.3 + r() * 0.9) * u;
        z += path(`M${F(x + side * 0.5 * u)} ${F(yy - 3.9 * u)} Q${F(x + side * 0.95 * u)} ${F(yy - 5 * u)} ${F(ax)} ${F(ay)}`, { fill: 'none', ...ink2 }) + circle(ax, ay, 0.2 * u, { fill: sk, ...ink2 });
      }
      let hd = circle(hx, hy, u, { fill: sk, ...ink2 });
      const R = u * 0.86, a1 = rimSide < 0 ? 2.1 : -1.05, a2 = rimSide < 0 ? 4.2 : 1.05;
      hd += path(`M${F(hx + Math.cos(a1) * R)} ${F(hy + Math.sin(a1) * R)} A${F(R)} ${F(R)} 0 0 1 ${F(hx + Math.cos(a2) * R)} ${F(hy + Math.sin(a2) * R)}`, { fill: 'none', stroke: rim, strokeWidth: 0.16 * u, strokeLinecap: 'round', opacity: (0.35 + 0.6 * t).toFixed(2) });
      hd += ellipse(hx - 0.32 * u, hy + 0.02 * u, 0.2 * u, 0.23 * u, { fill: mix('#2B302A', fog, dim * 0.5) }) + ellipse(hx + 0.32 * u, hy + 0.05 * u, 0.19 * u, 0.21 * u, { fill: mix('#2B302A', fog, dim * 0.5) });
      hd += circle(hx - 0.29 * u, hy + 0.06 * u, 0.06 * u, { fill: '#E6EAD6' }) + circle(hx + 0.34 * u, hy + 0.09 * u, 0.055 * u, { fill: '#E6EAD6' }) + ellipse(hx + 0.03 * u, hy + 0.55 * u, 0.15 * u, 0.2 * u, { fill: '#241E1C' });
      out += g(z + g(hd, { transform: `rotate(${F(tilt)} ${F(hx)} ${F(hy + u)})` }));
    }
  }
  return g(out, { filter: 'url(#wobbleSoft)' });
}

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
const MALL = { x0: 880, x1: 2000, roof: 180, ground: 660 };
const COLS = [], CW = 240, GAP = 36;
for (let x = MALL.x0 + 40; x < MALL.x1; x += CW + GAP) COLS.push(x);
const FLOORS = [[268, 176], [464, 80], [562, 56], [636, 24]];
const WIN = { x: COLS[2], y: FLOORS[0][0], w: CW, h: FLOORS[0][1] };   // the lit window, top floor (Bright Tech)
function mall() {
  const { x0, x1, roof, ground } = MALL;
  let s = '';
  // the glass skylight vault over the atrium, catching a little moonlight
  const vx = x0 + 400, vr = 280, vh = 150, vy = roof - 10;
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
  s += text(x0 + 360, roof + 64, 'BROOKFIELD MALL', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 48, fill: '#34445F', textAnchor: 'middle', letterSpacing: 10 });
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
  let s = `<defs><radialGradient id="sosA_win" cx="0.7" cy="0.3" r="0.85"><stop offset="0" stop-color="#FFFDF2"/><stop offset="0.4" stop-color="#FFEBA8"/><stop offset="1" stop-color="#FFB040"/></radialGradient></defs>`;
  // soft god rays fanning out of the window, fading with distance
  s += `<defs><radialGradient id="sosA_rayg" gradientUnits="userSpaceOnUse" cx="${cx}" cy="${cy}" r="820"><stop offset="0" stop-color="#FFE2A0" stop-opacity="0.34"/><stop offset="0.35" stop-color="#FFD890" stop-opacity="0.12"/><stop offset="1" stop-color="#FFD890" stop-opacity="0"/></radialGradient></defs>`;
  let rays = '';
  for (const [a, sp] of [[-196, 7], [-178, 4], [-160, 6], [-138, 3], [-40, 4], [-16, 5], [168, 5], [14, 3]]) {
    const a0 = ((a - sp / 2) * Math.PI) / 180, a1 = ((a + sp / 2) * Math.PI) / 180, len = 820;
    rays += poly([[cx, cy], [cx + Math.cos(a0) * len, cy + Math.sin(a0) * len], [cx + Math.cos(a1) * len, cy + Math.sin(a1) * len]], { fill: 'url(#sosA_rayg)' });
  }
  s += g(rays, { filter: 'url(#pro_glowS)', style: 'mix-blend-mode:screen' });
  s += bloom(cx, cy, 260, 190, '#FFA62E', 0.24) + bloom(cx, cy, 150, 110, WARM, 0.6);
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
  s += line(x + w * 0.86, y, x + w * 0.86, y + h, { stroke: INK, strokeWidth: 5 });
  s += bloom(lx, ly, 56, 56, '#FFFFFF', 0.85, true) + bloom(lx, ly, 22, 22, '#FFFFFF', 1, true);
  s += g(path(`M${F(lx)} ${F(ly - 110)} L${F(lx + 7)} ${F(ly)} L${F(lx)} ${F(ly + 110)} L${F(lx - 7)} ${F(ly)} Z M${F(lx - 150)} ${F(ly)} L${F(lx)} ${F(ly - 7)} L${F(lx + 150)} ${F(ly)} L${F(lx)} ${F(ly + 7)} Z`, { fill: '#FFFBEA' }), { opacity: 0.9, style: 'mix-blend-mode:screen' });
  return s;
}

// ---------- the signal: · · · — — — · · · flying out of the window toward you ----------
function morse(pts) {
  let glow = '', marks = '';
  pts.forEach(([x, y, a, d, len]) => {
    const r = d / 2, tr = `translate(${F(x)} ${F(y)}) rotate(${F(a)})`;
    const shape = (o) => (len > d ? rect(-len / 2, -r, len, d, { rx: r, ...o }) : circle(0, 0, r, o));
    glow += g(shape({ fill: WARM }), { transform: tr });
    marks += g(shape({ fill: 'url(#sosA_mk)', ...ink(Math.max(6, 0.17 * d)) }), { transform: tr });
  });
  return `<defs><linearGradient id="sosA_mk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFBEA"/><stop offset="1" stop-color="#FFC94A"/></linearGradient></defs>`
    + g(glow, { filter: 'url(#pro_glow)', opacity: 0.8, style: 'mix-blend-mode:screen' }) + g(marks, { filter: 'url(#pro_shadow)' });
}
// the nine marks laid along a quadratic curve by arc length, in Morse proportions (dash = 2.1 dots,
// gaps 0.42 inside a letter, 1.05 between letters), every mark and gap growing as the signal comes closer
function morsePath(P0, P1, P2, k0 = 0.75, k1 = 1.2) {
  const q = (t) => [(1 - t) ** 2 * P0[0] + 2 * (1 - t) * t * P1[0] + t * t * P2[0], (1 - t) ** 2 * P0[1] + 2 * (1 - t) * t * P1[1] + t * t * P2[1]];
  const N = 400, acc = [0], P = [q(0)];
  for (let i = 1; i <= N; i++) { P.push(q(i / N)); acc.push(acc[i - 1] + Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1])); }
  const total = acc[N];
  const at = (sArc) => { let i = acc.findIndex((v) => v >= sArc); if (i <= 0) i = 1; const k = (sArc - acc[i - 1]) / (acc[i] - acc[i - 1] || 1); return [i - 1 + k, P[i - 1][0] + (P[i][0] - P[i - 1][0]) * k, P[i - 1][1] + (P[i][1] - P[i - 1][1]) * k]; };
  const kind = ['d', 'd', 'd', 'D', 'D', 'D', 'd', 'd', 'd'];
  const walk = (sig) => {
    let c = 0; const out = [];
    kind.forEach((m, i) => {
      const d = sig * (k0 + (k1 - k0) * Math.min(1, c / total)), len = m === 'D' ? 2.1 * d : d;
      out.push([c + len / 2, d, len]); c += len;
      if (i < 8) c += (i === 2 || i === 5 ? 1.05 : 0.42) * d;
    });
    return [out, c];
  };
  let sig = 50, res;
  for (let it = 0; it < 8; it++) { res = walk(sig); sig *= total / res[1]; }
  return res[0].map(([c, d, len]) => {
    const [ti, x, y] = at(c), [, x1, y1] = at(Math.max(0, c - 4)), [, x2, y2] = at(Math.min(total, c + 4));
    let a = (Math.atan2(y2 - y1, x2 - x1) * 180) / Math.PI; if (a > 90) a -= 180; if (a < -90) a += 180;
    return [x, y, a, d, len];
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
  s += bloom(WIN.x + WIN.w / 2, 650, 520, 110, '#FFB050', 0.16);   // the window's light just reaching the far rows
  // front rows: big, in colour, faces you can read
  s += horde({ x0: -60, x1: 2000, yb: 1010, yf: 1225, rows: 2, s0: 1.0, s1: 1.32, seed: 41, arms: 0.35, rim: '#CFE0FF', rimSide: -1, fog: '#16203A', fogK: 0.18, density: 1.38 });
  // you, on Freshway's roof: binoculars down on the ledge, looking across at the window
  const sc = 2.8, gx = 450, gy = 1455, u = 60 * sc, top = 984;
  const cy = gy - 5.25 * u, by = top - 0.33 * u, hy = gy - 4.05 * u + 0.85 * u;   // binoculars on the ledge; hands where the 'carry' pose puts them
  s += bloom(gx, 600, 400, 440, '#3E64B0', 0.35);
  const hands = circle(gx - 0.45 * u, hy, 0.15 * u, { fill: PAL.skin, ...ink(4) }) + circle(gx + 0.5 * u, hy, 0.15 * u, { fill: PAL.skin, ...ink(4) });
  s += actor({ x: gx, y: gy, s: sc, pose: 'carry', face: 'serious', look: 0.55, scratch: true, lick: false, id: 'sosA', rim: { color: '#FFC070', side: 1, op: 0.7 },
    extra: binoculars(gx, by, u) + hands, front: cowlick(gx, cy, u) });
  s += parapet(top);
  // the signal, from the window across the lot to you
  s += morse(morsePath([WIN.x - 32, WIN.y + 98], [1080, 470], [712, 520], 0.72, 1.2));
  s += headline(56, 300, 'S.O.S.', { size: 310, anchor: 'start', fill: 'url(#pro_yel)', sw: 30, ls: 6 });
  s += finish({ vignette: 0.5, grain: 0.05 });
  return { w: W, h: H, svg: svgOf(s, 9), css: 'saturate(1.12) contrast(1.06)' };
}

export default () => thumb();
