import { W, H, INK, PAL, defs, finish, grade, glow, hero, zombie, crowd, caption, soundCaption, hud, watermark,
  g, rect, circle, ellipse, line, poly, path, text, ink, filled, persp, rng } from './lib.js';

const svg = (inner, seed) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}">${defs(seed)}${inner}</svg>`;
const label = (x, y, s, size = 26, fill = INK, anchor = 'middle') => text(x, y, s, { fontFamily: 'Rubik', fontWeight: 800, fontSize: size, letterSpacing: 2, fill, textAnchor: anchor });

// ---------- character sheet ----------
function sheet() {
  let s = rect(0, 0, W, H, { fill: PAL.paper });
  s += rect(0, 0, W, H, { fill: 'url(#graph)', opacity: 0.5 });
  s += label(60, 70, 'HERO · "YOU"', 30, INK, 'start');
  s += text(60, 104, 'olive jacket · orange headphones around the neck · messy dark hair', { fontFamily: 'Rubik', fontWeight: 500, fontSize: 20, fill: '#6B5F55' });
  const poses = [['stand', 'neutral', 'NEUTRAL'], ['stand', 'worried', 'WORRIED'], ['scared', 'scared', 'SCARED'], ['flashlight', 'determined', 'FLASHLIGHT'], ['shush', 'whisper', 'SHUSH'], ['walk', 'determined', 'SNEAK'], ['crouch', 'worried', 'CROUCH']];
  poses.forEach(([p, e, l], i) => {
    const x = 150 + i * 190;
    s += hero({ x, y: 520, s: 0.62, pose: p, expr: e, hold: p === 'flashlight' ? 'flashlight' : undefined, facing: 1 });
    s += label(x, 565, l, 18, '#6B5F55');
  });
  s += line(60, 610, W - 60, 610, { stroke: '#B9AE97', strokeWidth: 2, strokeDasharray: '8 8' });
  s += label(60, 660, 'THE DEAD · they keep the uniform of their old job', 26, INK, 'start');
  const zs = [['cashier', 'CASHIER'], ['guard', 'SECURITY'], ['janitor', 'JANITOR'], ['jogger', 'JOGGER'], ['suit', 'MANAGER'], ['shopper', 'SHOPPER']];
  zs.forEach(([o, l], i) => {
    const x = 150 + i * 200;
    s += zombie({ x, y: 1000, s: 0.6, outfit: o, tilt: i % 2 ? 8 : -10, look: i % 2 ? 0.4 : -0.3, pose: i === 3 ? 'reach' : 'stand' });
    s += label(x, 1045, l, 18, '#6B5F55');
  });
  // props
  s += label(1450, 160, 'PROPS', 26, INK, 'start');
  const px = 1460;
  s += g(rect(px, 200, 70, 120, { rx: 10, fill: '#BFDDEB', ...ink(5) }) + rect(px + 20, 182, 30, 22, { rx: 4, fill: '#3E6E9A', ...ink(4) }) + rect(px, 250, 70, 24, { fill: '#3E6E9A', opacity: 0.4 }), { filter: 'url(#wobbleSoft)' });
  s += label(px + 35, 350, 'WATER', 16, '#6B5F55');
  s += g(rect(px + 130, 230, 70, 90, { rx: 8, fill: PAL.red, ...ink(5) }) + rect(px + 130, 255, 70, 34, { fill: '#F3EEDF', ...ink(3) }) + text(px + 165, 279, 'BEANS', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 15, textAnchor: 'middle', fill: INK }), { filter: 'url(#wobbleSoft)' });
  s += label(px + 165, 350, 'FOOD', 16, '#6B5F55');
  s += g(rect(px + 260, 205, 50, 115, { rx: 10, fill: '#333', ...ink(5) }) + rect(px + 268, 222, 34, 34, { rx: 4, fill: '#7FB069', ...ink(3) }) + line(px + 300, 205, px + 300, 165, ink(6)) + circle(px + 285, 285, 10, { fill: PAL.red, ...ink(3) }), { filter: 'url(#wobbleSoft)' });
  s += label(px + 285, 350, 'RADIO', 16, '#6B5F55');
  s += g(rect(px + 20, 400, 150, 34, { rx: 12, fill: '#2C2C2C', ...ink(5) }) + rect(px + 160, 394, 34, 46, { rx: 6, fill: '#C9A43A', ...ink(4) }), { filter: 'url(#wobbleSoft)' });
  s += label(px + 100, 470, 'FLASHLIGHT', 16, '#6B5F55');
  s += g(circle(px + 300, 418, 34, { fill: '#F2F0EA', ...ink(5) }) + line(px + 300, 418, px + 300, 396, ink(4)) + line(px + 300, 418, px + 316, 426, ink(4)) + rect(px + 275, 372, 18, 14, { fill: PAL.red, ...ink(3) }) + rect(px + 308, 372, 18, 14, { fill: PAL.red, ...ink(3) }), { filter: 'url(#wobbleSoft)' });
  s += label(px + 300, 470, 'ALARM CLOCK', 16, '#6B5F55');
  s += label(1450, 560, 'PALETTE', 26, INK, 'start');
  [PAL.jacket, PAL.phones, PAL.skin, PAL.hair, PAL.zSkin, PAL.red, PAL.cream, PAL.card].forEach((c, i) => {
    s += rect(1460 + (i % 4) * 100, 590 + Math.floor(i / 4) * 100, 80, 80, { rx: 8, fill: c, ...ink(4) });
  });
  s += finish({ vignette: 0.35, grain: 0.06 });
  return svg(s, 3);
}

export const SCENES = { sheet };

// ---------- supermarket aisle (one-point perspective) ----------
const PROD = ['#C2674A', '#D4AE52', '#5A7396', '#7A8F5C', '#B57A88', '#C98A55', '#7F6F9C', '#4F7F7C', '#A8594A', '#C9B67F'];
function aisle({ night = false, seed = 5 } = {}) {
  const VP = [960, 440], FAR = 0.16, p = persp(VP, FAR), r = rng(seed);
  const zOf = (Zd) => (1 - 1 / (1 + Zd)) / (1 - FAR); // world depth ratio -> param z
  const Lx = 250, Rx = 1670, FY = 1040, TOP = 120, CEIL = -260, Z0 = -0.6;
  let s = rect(0, 0, W, H / 2, { fill: '#E4DFD0' }) + rect(0, H / 2 - 60, W, H / 2 + 60, { fill: '#D9CDB2' });
  // ceiling light strips
  for (let Zd = 0.9; Zd < 5.2; Zd += 0.55) {
    const z1 = zOf(Zd), z2 = zOf(Zd + 0.28);
    s += poly([p(880, CEIL, z1), p(1040, CEIL, z1), p(1040, CEIL, z2), p(880, CEIL, z2)], { fill: night ? '#8C8E86' : '#FBF8EC', stroke: INK, strokeWidth: 3 });
  }
  // floor tiles
  for (let x = Lx; x <= Rx; x += 142) s += line(...p(x, FY, Z0), ...p(x, FY, 1), { stroke: '#BDB096', strokeWidth: 2 });
  for (let Zd = -0.33; Zd < 5.25; Zd += 0.22) s += line(...p(Lx, FY, zOf(Zd)), ...p(Rx, FY, zOf(Zd)), { stroke: '#BDB096', strokeWidth: 2 });
  // back wall with coolers
  const b1 = p(Lx, TOP - 200, 1), b2 = p(Rx, FY, 1);
  s += rect(b1[0], b1[1], b2[0] - b1[0], b2[1] - b1[1], { fill: '#C8C2AE', stroke: INK, strokeWidth: 3 });
  for (let i = 0; i < 4; i++) {
    const cw = (b2[0] - b1[0] - 30) / 4;
    s += rect(b1[0] + 15 + i * cw, b1[1] + 70, cw - 8, b2[1] - b1[1] - 80, { fill: night ? '#6E8FA3' : '#CFE3EA', stroke: INK, strokeWidth: 3 });
  }
  s += rect(b1[0] + 40, b1[1] + 18, b2[0] - b1[0] - 80, 34, { fill: PAL.blue, stroke: INK, strokeWidth: 3 });
  s += text((b1[0] + b2[0]) / 2, b1[1] + 43, 'DAIRY · CHILLED', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 20, fill: '#FFF', textAnchor: 'middle', letterSpacing: 2 });
  // shelf faces
  const side = (X) => {
    let o = poly([p(X, TOP, Z0), p(X, TOP, 1), p(X, FY, 1), p(X, FY, Z0)], { fill: '#B7AF9B', stroke: INK, strokeWidth: 5 });
    const boards = [300, 520, 740, 960];
    for (const L of boards) {
      let Zd = -0.34;
      while (Zd < 5.2) {
        const len = 0.04 + r() * 0.06, h = r() < 0.55 ? 60 + r() * 35 : 105 + r() * 50;
        const z1 = zOf(Zd), z2 = zOf(Zd + len);
        const c = PROD[Math.floor(r() * PROD.length)];
        o += poly([p(X, L, z1), p(X, L - h, z1), p(X, L - h, z2), p(X, L, z2)], { fill: c, stroke: INK, strokeWidth: 2.5 });
        if (r() < 0.7) o += poly([p(X, L - h * 0.62, z1), p(X, L - h * 0.38, z1), p(X, L - h * 0.38, z2), p(X, L - h * 0.62, z2)], { fill: '#F3EEDF', opacity: 0.85 });
        Zd += len + 0.004;
      }
      o += poly([p(X, L, Z0), p(X, L + 22, Z0), p(X, L + 22, 1), p(X, L, 1)], { fill: '#8E877A', stroke: INK, strokeWidth: 3 });
      for (let Zd2 = 0; Zd2 < 5; Zd2 += 0.6) { const q = p(X, L + 4, zOf(Zd2)), sc = 1 - (1 - FAR) * zOf(Zd2); o += rect(q[0] - 16 * sc, q[1], 32 * sc, 14 * sc, { fill: '#FFF8E0', stroke: INK, strokeWidth: 1.5 }); }
    }
    return o;
  };
  s += side(Lx) + side(Rx);
  // hanging aisle sign
  const sg = p(960, -40, zOf(0.9)), sc = 1 - (1 - FAR) * zOf(0.9);
  s += line(sg[0] - 120 * sc, 0, sg[0] - 120 * sc, sg[1] - 50 * sc, { stroke: INK, strokeWidth: 3 }) + line(sg[0] + 120 * sc, 0, sg[0] + 120 * sc, sg[1] - 50 * sc, { stroke: INK, strokeWidth: 3 });
  s += rect(sg[0] - 190 * sc, sg[1] - 50 * sc, 380 * sc, 120 * sc, { rx: 8, fill: PAL.yellow, stroke: INK, strokeWidth: 4 });
  s += text(sg[0], sg[1] + 10 * sc, 'AISLE 7', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 52 * sc, fill: INK, textAnchor: 'middle' });
  s += text(sg[0], sg[1] + 50 * sc, 'CANNED · SOUP · BEANS', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 20 * sc, fill: INK, textAnchor: 'middle', letterSpacing: 2 });
  return { s: g(s, { filter: 'url(#wobble)' }), p, zOf, FY };
}
const at = (A, x, Zd) => { const z = A.zOf(Zd); const q = A.p(x, A.FY, z); return { x: q[0], y: q[1], k: 1 - (1 - 0.16) * z }; };

function supermarket_day() {
  const A = aisle({ seed: 5 });
  let s = A.s;
  const z1 = at(A, 1180, 3.2), z2 = at(A, 760, 4.2);
  s += zombie({ x: z1.x, y: z1.y, s: 1.4 * z1.k, outfit: 'cashier', tilt: 10, look: -0.4 });
  s += zombie({ x: z2.x, y: z2.y, s: 1.4 * z2.k, outfit: 'shopper', tilt: -8, look: 0.3 });
  const h = at(A, 760, 0.12);
  s += hero({ x: h.x, y: h.y, s: 1.45 * h.k, pose: 'stand', expr: 'worried', facing: 1, look: 0.35 });
  // shopping basket on floor
  const bk = at(A, 1080, 0.35);
  s += g(path(`M${bk.x - 70 * bk.k} ${bk.y - 70 * bk.k} h${140 * bk.k} l${-18 * bk.k} ${70 * bk.k} h${-104 * bk.k} z`, { fill: PAL.red, ...ink(5) }) + path(`M${bk.x - 50 * bk.k} ${bk.y - 70 * bk.k} q${50 * bk.k} ${-70 * bk.k} ${100 * bk.k} 0`, { fill: 'none', ...ink(6) }), { filter: 'url(#wobbleSoft)' });
  s += hud({ theme: 'price', day: 3, time: '8:02 AM', noise: 1 });
  s += caption('regulars');
  s += watermark() + finish();
  return svg(s, 5);
}

function supermarket_night() {
  const A = aisle({ night: true, seed: 5 });
  let s = A.s;
  const zs = [[1250, 2.6, 'cashier', 12], [1060, 3.4, 'suit', -6], [760, 3.9, 'shopper', 8], [1400, 4.6, 'guard', -10]];
  for (const [x, Zd, o, t] of zs) { const q = at(A, x, Zd); s += zombie({ x: q.x, y: q.y, s: 1.4 * q.k, outfit: o, tilt: t, look: -0.5 }); }
  const h = at(A, 640, 0.05);
  const hu = 60 * 1.45 * h.k, hx1 = h.x + 1.45 * hu, hy1 = h.y - 3.45 * hu, T1 = [990, 500];
  s += hero({ x: h.x, y: h.y, s: 1.45 * h.k, pose: 'flashlight', expr: 'scared', hold: 'flashlight', aim: Math.atan2(T1[1] - hy1, T1[0] - hx1) * 180 / Math.PI, facing: 1, look: 0.5 });
  s += rect(0, 0, W, H, { fill: '#1F2940', opacity: 0.86, style: 'mix-blend-mode:multiply' });
  s += ellipse(h.x + 60, h.y - 300, 260, 340, { fill: '#FFF2C4', opacity: 0.16, filter: 'url(#soft)', style: 'mix-blend-mode:screen' });
  // emergency exit glow at the back
  s += glow(960, 395, 90, '#7CFF9A', 0.5) + rect(925, 380, 70, 26, { fill: '#3DBE6A', stroke: INK, strokeWidth: 2 }) + text(960, 400, 'EXIT', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 18, fill: '#EFFFF2', textAnchor: 'middle' });
  // flashlight beam from hero toward the far end
  const u = 60 * 1.45 * h.k, hx0 = h.x + 1.45 * u, hy0 = h.y - 3.45 * u, T = [990, 500];
  const a = Math.atan2(T[1] - hy0, T[0] - hx0), aim = a * 180 / Math.PI, tip = [hx0 + Math.cos(a) * 0.7 * u, hy0 + Math.sin(a) * 0.7 * u];
  const dist = Math.hypot(T[0] - tip[0], T[1] - tip[1]) * 1.25;
  const far = (d) => [tip[0] + Math.cos(a + d) * dist, tip[1] + Math.sin(a + d) * dist];
  s += poly([tip, far(-0.2), far(0.2)], { fill: 'url(#beam)', style: 'mix-blend-mode:screen', opacity: 0.95 });
  s += ellipse(T[0] + 10, T[1] + 20, 170, 140, { fill: '#FFF2C4', opacity: 0.6, filter: 'url(#soft)', style: 'mix-blend-mode:screen' });
  s += ellipse(T[0] + 10, T[1] + 20, 90, 80, { fill: '#FFF2C4', opacity: 0.35, filter: 'url(#softS)', style: 'mix-blend-mode:screen' });
  s += hud({ theme: 'price', day: 10, time: '4:51 AM', noise: 4 });
  s += caption('breathe');
  s += watermark() + finish({ vignette: 1, grain: 0.13 });
  return svg(s, 6);
}

// ---------- shopping mall atrium (camera on level 2, looking across and down) ----------
function mall() {
  const r = rng(11);
  let s = rect(0, 0, W, H, { fill: '#D8D2C2' });
  s += rect(0, 0, W, 130, { fill: '#DCE8EC', ...ink(5) });
  for (let x = -40; x < W; x += 150) s += line(x, 0, x + 50, 130, { stroke: INK, strokeWidth: 4 });
  s += line(0, 65, W, 65, { stroke: INK, strokeWidth: 4 });
  // banner
  s += line(1290, 130, 1290, 200, ink(3)) + line(1530, 130, 1530, 200, ink(3));
  s += rect(1260, 196, 300, 92, { fill: PAL.red, ...ink(5) }) + text(1410, 240, 'GRAND SALE', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 30, fill: '#FFF', textAnchor: 'middle' }) + text(1410, 274, 'UP TO -50%', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 20, fill: '#FFE9C8', textAnchor: 'middle', letterSpacing: 2 });
  // opposite level 2 storefronts
  const stores2 = [['TOY TOWN', '#D4AE52'], ['PHONE+', '#5A7396'], ['BOOKS', '#7A8F5C'], ['SHOES', '#B57A88'], ['CINEMA', '#A8594A'], ['TEA', '#7F6F9C']];
  stores2.forEach(([n, c], i) => {
    const x = 20 + i * 315;
    s += rect(x, 150, 300, 190, { fill: '#EFE9DA', ...ink(5) }) + rect(x, 150, 300, 42, { fill: c, ...ink(5) });
    s += text(x + 150, 181, n, { fontFamily: 'Rubik', fontWeight: 900, fontSize: 24, fill: '#FFF', textAnchor: 'middle', letterSpacing: 2 });
    s += rect(x + 20, 208, 260, 132, { fill: n === 'CINEMA' ? '#2B2F3A' : '#BFD3D8', ...ink(4) });
  });
  s += rect(0, 340, W, 18, { fill: '#B7AF9B', ...ink(4) });
  for (let x = 0; x < W; x += 110) s += rect(x + 5, 300, 100, 40, { fill: '#BFD3D8', opacity: 0.5, ...ink(3) });
  s += rect(0, 296, W, 8, { fill: '#6F695F' });
  s += rect(0, 358, W, 40, { fill: '#8E877A', ...ink(4) });
  // level 1 storefronts with shutters
  ['FRESHWAY', 'BURGER', 'PHARMACY', 'GIFTS', 'SPORTS', 'BANK'].forEach((n, i) => {
    const x = 20 + i * 315;
    s += rect(x, 398, 300, 170, { fill: '#E6DFCE', ...ink(5) }) + rect(x, 398, 300, 36, { fill: '#7C766B', ...ink(4) });
    s += text(x + 150, 424, n, { fontFamily: 'Rubik', fontWeight: 800, fontSize: 20, fill: '#F5EFE0', textAnchor: 'middle', letterSpacing: 2 });
    const down = 40 + r() * 90;
    s += rect(x + 15, 434, 270, down, { fill: '#A9A396', ...ink(3) });
    for (let yy = 444; yy < 434 + down; yy += 11) s += line(x + 15, yy, x + 285, yy, { stroke: '#7F7A70', strokeWidth: 2 });
    s += rect(x + 15, 434 + down, 270, 134 - down, { fill: '#38404A', ...ink(3) });
  });
  // ground floor seen from above
  s += rect(0, 568, W, 512, { fill: '#D6CDB8' });
  for (let x = -600; x < W + 600; x += 130) s += line(x, 568, x + (x - 960) * 0.25, 900, { stroke: '#BDB096', strokeWidth: 2 });
  for (const y of [600, 640, 690, 750, 820]) s += line(0, y, W, y, { stroke: '#BDB096', strokeWidth: 2 });
  s += ellipse(1020, 700, 230, 60, { fill: '#B8B1A0', ...ink(5) }) + ellipse(1020, 690, 195, 44, { fill: '#9AA6A8', ...ink(4) });
  s += rect(1006, 600, 28, 92, { fill: '#B8B1A0', ...ink(4) }) + ellipse(1020, 600, 60, 15, { fill: '#B8B1A0', ...ink(4) });
  s += crowd({ x0: 620, x1: 1480, y: 790, rows: 4, n: 20, s: 0.27, seed: 4, spread: 30 });
  s += crowd({ x0: 120, x1: 520, y: 840, rows: 2, n: 6, s: 0.3, seed: 12, spread: 30 });
  // escalator: ground floor (left) up to the opposite level 2 walkway
  s += poly([[200, 880], [340, 880], [760, 352], [650, 352]], { fill: '#8F8A80', ...ink(5) });
  for (let i = 1; i < 16; i++) { const t = i / 16; s += line(200 + t * 450, 880 - t * 528, 340 + t * 420, 880 - t * 528, { stroke: '#6F6A60', strokeWidth: 3 }); }
  s += path('M170 870 L632 340', { stroke: INK, strokeWidth: 12, fill: 'none' }) + path('M366 872 L786 344', { stroke: INK, strokeWidth: 12, fill: 'none' });
  // haze pushes the lower floors back
  s += rect(0, 398, W, 500, { fill: '#F4F0E6', opacity: 0.18 });
  s = g(s, { filter: 'url(#wobble)' });
  // foreground: our level, hero behind the glass railing
  let fg = rect(0, 880, W, 200, { fill: '#C9C1AE', ...ink(5) });
  fg += g(path('M220 1080 l40 -120 h150 l40 120 z', { fill: PAL.red, ...ink(5) }) + path('M270 960 q65 -70 130 0', { fill: 'none', ...ink(6) }), {});
  fg += hero({ x: 1600, y: 1205, s: 1.4, pose: 'shush', expr: 'whisper', facing: -1, look: -0.45 });
  for (let x = 0; x < W; x += 260) fg += rect(x + 8, 880, 244, 200, { fill: '#CFE0E4', opacity: 0.38, ...ink(4) });
  fg += rect(0, 866, W, 26, { fill: '#9E978A', ...ink(6) });
  s += g(fg, { filter: 'url(#wobble)' });
  s += hud({ theme: 'mall', day: 4, time: '1:30 PM', noise: 2 });
  s += caption('quiet', { y: 1000 });
  s += watermark() + finish();
  return svg(s, 11);
}

// ---------- park at dusk ----------
function park() {
  const r = rng(21);
  let s = `<linearGradient id="dusk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6E6A8E"/><stop offset="0.55" stop-color="#C98FA0"/><stop offset="1" stop-color="#F3B58A"/></linearGradient>`;
  s += rect(0, 0, W, 640, { fill: 'url(#dusk)' });
  s += circle(1500, 560, 60, { fill: '#FFD9A0' });
  for (let x = 0; x < W; x += 95) { const h = 60 + r() * 150; s += rect(x, 610 - h, 82, h + 40, { fill: '#8C7F9A', opacity: 0.55 }); }
  for (let x = -40; x < W + 60; x += 66) s += circle(x, 625 - r() * 30, 55 + r() * 30, { fill: '#5C5A70', opacity: 0.9 });
  s += rect(0, 630, W, 450, { fill: '#7D8B55' });
  s += path('M900 1080 C960 920 1180 800 1290 640 L1340 640 C1270 800 1120 930 1190 1080 Z', { fill: '#D8C9A6', ...ink(4) });
  for (let x = 0; x < W; x += 46) s += rect(x, 662, 9, 62, { fill: '#5C4430', opacity: 0.75 });
  s += line(0, 676, W, 676, { stroke: '#5C4430', strokeWidth: 6, opacity: 0.75 });
  for (const [x, y, k] of [[1680, 820, 0.75], [1230, 690, 0.42], [120, 760, 0.6]]) s += line(x, y, x, y - 320 * k, { stroke: INK, strokeWidth: 10 * k }) + rect(x - 22 * k, y - 340 * k, 44 * k, 30 * k, { fill: '#FFE7A8', ...ink(4) });
  // bench + bin
  s += rect(1380, 840, 200, 18, { fill: PAL.wood, ...ink(4) }) + rect(1380, 800, 200, 16, { fill: PAL.wood, ...ink(4) }) + line(1395, 858, 1395, 900, ink(6)) + line(1565, 858, 1565, 900, ink(6));
  // playground tower
  const tx = 600, deck = 560, roofB = 250;
  for (const px of [tx - 190, tx + 170]) s += rect(px, roofB, 22, 980 - roofB, { fill: PAL.wood, ...ink(5) });
  s += poly([[tx - 230, roofB], [tx, roofB - 150], [tx + 230, roofB]], { fill: '#C2674A', ...ink(6) });
  s += rect(tx - 210, deck, 420, 32, { fill: '#C99A62', ...ink(6) });
  for (let i = 0; i < 4; i++) s += line(tx - 190, deck - 40 - i * 40, tx + 190, deck - 40 - i * 40, { stroke: INK, strokeWidth: 5, opacity: 0.85 });
  for (let i = 0; i < 7; i++) s += line(tx - 300, 960 - i * 58, tx - 205, 960 - i * 58, { stroke: INK, strokeWidth: 6 });
  s += line(tx - 300, 980, tx - 300, deck, ink(6)) + line(tx - 205, 980, tx - 205, deck, ink(6));
  s += path(`M${tx + 190} ${deck} C${tx + 360} ${deck + 40} ${tx + 380} ${deck + 300} ${tx + 560} ${deck + 360} L${tx + 560} ${deck + 400} C${tx + 360} ${deck + 340} ${tx + 330} ${deck + 90} ${tx + 190} ${deck + 40} Z`, { fill: '#D4AE52', ...ink(6) });
  s = g(s, { filter: 'url(#wobble)' });
  s += hero({ x: tx + 20, y: deck + 2, s: 0.78, pose: 'scared', expr: 'scared', facing: -1, look: 0.35 });
  // the dead below, reaching up
  const zs = [[tx - 120, 1000, 'jogger', 10, 0.82], [tx + 210, 1010, 'park', -12, 0.86], [tx - 420, 980, 'suit', 6, 0.78], [tx + 520, 1040, 'shopper', -6, 0.9], [1250, 735, 'jogger', 10, 0.42], [1450, 720, 'park', -8, 0.38], [980, 760, 'suit', 6, 0.45]];
  for (const [x, y, o, t, k] of zs) s += zombie({ x, y, s: k, outfit: o, tilt: t, pose: 'reach', look: -0.3 });
  s += ellipse(960, 760, 1300, 70, { fill: '#F4E9E4', opacity: 0.28, filter: 'url(#soft)', style: 'mix-blend-mode:screen' });
  s += grade('dusk');
  s += glow(120, 560, 110, '#FFE7A8', 0.7) + glow(1680, 570, 90, '#FFE7A8', 0.6) + glow(1500, 560, 240, '#FFD9A0', 0.35);
  s += hud({ theme: 'park', day: 2, time: '7:48 PM', noise: 3 });
  s += caption('ladder');
  s += watermark() + finish();
  return svg(s, 21);
}

Object.assign(SCENES, { supermarket_day, supermarket_night, mall, park });

// ---------- supermarket exterior at night: the regulars at the shutter ----------
function exterior_night() {
  const r = rng(31);
  let s = rect(0, 0, W, 560, { fill: '#2E3A55' });
  for (let i = 0; i < 70; i++) s += circle(r() * W, r() * 300, 1 + r() * 2, { fill: '#F3EBDD', opacity: 0.5 + r() * 0.5 });
  s += circle(1620, 150, 52, { fill: '#F1E9D2' }) + circle(1600, 140, 52, { fill: '#2E3A55', opacity: 0.25 });
  for (let x = 0; x < W; x += 110) { const h = 120 + r() * 200; s += rect(x, 560 - h, 100, h, { fill: '#1E2638', ...ink(3) }); for (let k = 0; k < 6; k++) if (r() < 0.12) s += rect(x + 12 + (k % 3) * 28, 560 - h + 20 + Math.floor(k / 3) * 34, 16, 20, { fill: '#F6D98B', opacity: 0.8 }); }
  // building
  s += rect(160, 260, 1600, 470, { fill: '#C9BFA7', ...ink(6) });
  s += rect(160, 260, 1600, 110, { fill: '#3E6E5A', ...ink(6) });
  s += text(960, 340, 'FRESHWAY', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 84, fill: '#F5EFE0', textAnchor: 'middle', letterSpacing: 8 });
  s += rect(1430, 290, 270, 54, { rx: 8, fill: '#B5452F', ...ink(4) }) + text(1565, 327, 'OPEN 24 HOURS', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 24, fill: '#FFF', textAnchor: 'middle', letterSpacing: 1 });
  // shutter (bowed) across the glass front
  s += rect(260, 400, 1400, 330, { fill: '#9C988C', ...ink(6) });
  for (let y = 412; y < 730; y += 16) s += path(`M260 ${y} Q960 ${y + 16 * (1 - Math.abs(y - 560) / 170)} 1660 ${y}`, { fill: 'none', stroke: '#6E6A60', strokeWidth: 3 });
  s += path('M900 730 l20 -40 l26 20 l18 -36 l30 56', { fill: '#2A2522', ...ink(3) });
  // parking lot
  s += rect(0, 730, W, 350, { fill: '#4A4E58' });
  for (let x = -200; x < W + 200; x += 260) s += line(x, 1080, x + 120, 760, { stroke: '#E9E2C8', strokeWidth: 6, opacity: 0.5 });
  // shopping cart corral + Dana-like car
  s += rect(1600, 840, 260, 120, { rx: 30, fill: '#7A3B33', ...ink(6) }) + rect(1640, 800, 170, 60, { rx: 20, fill: '#9FB3C2', ...ink(5) });
  s += circle(1650, 965, 30, { fill: INK }) + circle(1810, 965, 30, { fill: INK });
  s = g(s, { filter: 'url(#wobble)' });
  // the crowd leaning on the shutter
  s += crowd({ x0: 280, x1: 1640, y: 760, rows: 3, n: 24, s: 0.48, seed: 7, spread: 26, arms: false });
  s += crowd({ x0: 120, x1: 1500, y: 900, rows: 2, n: 14, s: 0.62, seed: 8, spread: 24 });
  s += grade('night');
  // sodium lamp pools
  s += line(80, 1080, 80, 520, { stroke: INK, strokeWidth: 14 }) + rect(60, 506, 90, 22, { fill: '#FFB866', ...ink(4) });
  s += glow(105, 535, 55, '#FFB866', 0.75) + ellipse(240, 1010, 300, 80, { fill: '#FFB866', opacity: 0.22, filter: 'url(#soft)', style: 'mix-blend-mode:screen' });
  s += glow(1565, 316, 60, '#FF6A4A', 0.45);
  // roof edge: tiny hero silhouette with a light
  s += hero({ x: 1240, y: 262, s: 0.42, pose: 'flashlight', expr: 'worried', hold: 'flashlight', aim: 40, facing: 1 });
  s += glow(1275, 220, 40, '#FFF2C4', 0.7);
  s += hud({ theme: 'price', day: 3, time: '11:58 PM', noise: 0, place: 'FRESHWAY · ROOF' });
  s += caption('saturday');
  s += watermark() + finish({ vignette: 1 });
  return svg(s, 31);
}

// ---------- POV: first person, letterboxed, no narrator ----------
function pov_stockroom() {
  let s = rect(0, 0, W, H, { fill: '#2A2C33' });
  // stockroom racks in near-darkness
  const rack = (x, w) => { let o = rect(x, 120, w, 900, { fill: '#3A3D46', ...ink(5) }); for (const y of [300, 520, 740]) { o += rect(x, y, w, 18, { fill: '#55525A', ...ink(4) }); for (let i = 0; i < 5; i++) o += rect(x + 20 + i * (w - 40) / 5, y - 120, (w - 60) / 5, 120, { fill: '#6B5E4C', ...ink(3) }); } return o; };
  s += rack(-60, 600) + rack(1380, 640);
  s += rect(560, 120, 820, 900, { fill: '#1E2027' });
  // the dead between racks, half lit
  s += zombie({ x: 1010, y: 1180, s: 1.75, outfit: 'cashier', tilt: 12, look: -0.5 });
  s += zombie({ x: 700, y: 900, s: 0.7, outfit: 'guard', tilt: -6, look: 0.2 });
  s = g(s, { filter: 'url(#wobble)' });
  s += rect(0, 0, W, H, { fill: '#1D2433', opacity: 0.8, style: 'mix-blend-mode:multiply' });
  // flashlight cone from the lens toward the face
  const L = [1240, 830];
  s += poly([L, [760, 420], [1240, 400]], { fill: '#FFF2C4', opacity: 0.14, style: 'mix-blend-mode:screen' });
  s += ellipse(1030, 650, 260, 240, { fill: '#FFF2C4', opacity: 0.5, filter: 'url(#soft)', style: 'mix-blend-mode:screen' });
  s += ellipse(1030, 650, 170, 160, { fill: '#FFF2C4', opacity: 0.3, filter: 'url(#softS)', style: 'mix-blend-mode:screen' });
  // our hands: left hand braced on the rack edge, right hand with the flashlight pointing into the room
  const sleeve = (d) => path(d, { fill: PAL.jacket, ...ink(7) });
  const mitt = (cx, cy, rot, k = 1) => g(path(`M${-60 * k} ${-30 * k} C${-60 * k} ${-90 * k} ${50 * k} ${-95 * k} ${60 * k} ${-35 * k} L${62 * k} ${35 * k} C${50 * k} ${80 * k} ${-55 * k} ${80 * k} ${-60 * k} ${30 * k} Z`, { fill: PAL.skin, ...ink(7) })
    + path(`M${-60 * k} ${-5 * k} C${-110 * k} ${-20 * k} ${-115 * k} ${-75 * k} ${-75 * k} ${-70 * k}`, { fill: PAL.skin, ...ink(7) }), { transform: `translate(${cx} ${cy}) rotate(${rot})` });
  let hands = '';
  hands += sleeve('M1700 1080 L1330 900 L1440 800 L1880 1080 Z');
  hands += path('M1420 930 L1240 830 L1262 800 L1450 890 Z', { fill: '#2C2C2C', ...ink(6) });
  hands += ellipse(1250, 815, 26, 36, { fill: '#C9A43A', ...ink(6), transform: 'rotate(-30 1250 815)' }) + ellipse(1246, 812, 14, 22, { fill: '#FFF6D8', transform: 'rotate(-30 1246 812)' });
  hands += mitt(1410, 900, -20, 1.05);
  s += g(hands, { filter: 'url(#wobbleSoft)' });
  // radial darkness around the beam
  s += `<radialGradient id="povDark" cx="0.53" cy="0.52" r="0.6"><stop offset="0.35" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.8"/></radialGradient>`;
  s += rect(0, 0, W, H, { fill: 'url(#povDark)' });
  // letterbox = POV mode
  s += rect(0, 0, W, 130, { fill: '#000' }) + rect(0, H - 130, W, 130, { fill: '#000' });
  s += soundCaption('slow breathing, very close', { y: H - 70 });
  s += text(60, 82, 'POV', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 30, fill: '#E8E1D2', letterSpacing: 6, opacity: 0.85 }) + circle(150, 72, 10, { fill: '#D65632' });
  s += finish({ vignette: 0.6, grain: 0.16 });
  return svg(s, 41);
}

// ---------- motion graphics cards ----------
const cream = () => rect(0, 0, W, H, { fill: PAL.cream });
const icon = {
  water: (x, y, k = 1) => g(rect(x - 45 * k, y - 70 * k, 90 * k, 150 * k, { rx: 14 * k, fill: '#BFDDEB', ...ink(6) }) + rect(x - 18 * k, y - 95 * k, 36 * k, 28 * k, { rx: 5, fill: '#3E6E9A', ...ink(5) }) + rect(x - 45 * k, y - 5 * k, 90 * k, 30 * k, { fill: '#3E6E9A', opacity: 0.45 }), { filter: 'url(#wobbleSoft)' }),
  can: (x, y, k = 1, fill = PAL.red) => g(rect(x - 40 * k, y - 55 * k, 80 * k, 110 * k, { rx: 10 * k, fill, ...ink(6) }) + rect(x - 40 * k, y - 22 * k, 80 * k, 40 * k, { fill: '#F3EEDF', ...ink(3) }), { filter: 'url(#wobbleSoft)' }),
  clock: (x, y, k = 1) => g(circle(x, y, 60 * k, { fill: '#F2F0EA', ...ink(6) }) + line(x, y, x, y - 36 * k, ink(6)) + line(x, y, x + 26 * k, y + 12 * k, ink(6)) + rect(x - 52 * k, y - 78 * k, 30 * k, 22 * k, { fill: PAL.red, ...ink(4) }) + rect(x + 22 * k, y - 78 * k, 30 * k, 22 * k, { fill: PAL.red, ...ink(4) }), { filter: 'url(#wobbleSoft)' }),
  ear: (x, y, k = 1) => g(path(`M${x - 30 * k} ${y + 60 * k} C${x - 80 * k} ${y - 20 * k} ${x - 40 * k} ${y - 90 * k} ${x + 10 * k} ${y - 90 * k} C${x + 70 * k} ${y - 90 * k} ${x + 70 * k} ${y - 10 * k} ${x + 20 * k} ${y + 20 * k} C${x} ${y + 40 * k} ${x + 10 * k} ${y + 70 * k} ${x - 30 * k} ${y + 60 * k} Z`, { fill: PAL.skin, ...ink(6) }) + path(`M${x - 10 * k} ${y - 40 * k} q${30 * k} ${-20 * k} ${40 * k} ${10 * k}`, { fill: 'none', ...ink(5) }) + path(`M${x + 90 * k} ${y - 60 * k} q${30 * k} ${40 * k} 0 ${80 * k} M${x + 120 * k} ${y - 80 * k} q${45 * k} ${60 * k} 0 ${120 * k}`, { fill: 'none', stroke: PAL.red, strokeWidth: 7, strokeLinecap: 'round' }), { filter: 'url(#wobbleSoft)' }),
};
const smallCaps = (x, y, s, size = 26, fill = '#6B5F55') => text(x, y, s, { fontFamily: 'Rubik', fontWeight: 800, fontSize: size, letterSpacing: 6, fill, textAnchor: 'middle' });
const big = (x, y, s, size = 150, fill = INK) => text(x, y, s, { fontFamily: 'Rubik', fontWeight: 900, fontSize: size, fill, textAnchor: 'middle' });

function card_episode() {
  let s = rect(0, 0, W, H, { fill: PAL.card });
  s += smallCaps(W / 2, 330, 'LAST LIGHT  ·  SEASON 1: FRESHWAY', 30, '#B9AE97');
  s += big(W / 2, 520, 'EPISODE 1', 70, PAL.tag);
  s += big(W / 2, 680, 'THE NIGHT SHIFT', 150, '#F3EBDD');
  s += line(W / 2 - 300, 740, W / 2 + 300, 740, { stroke: '#4A403A', strokeWidth: 3 });
  s += smallCaps(W / 2, 800, 'DAY 0 — DAY 7', 28, '#B9AE97');
  s += finish({ vignette: 0.9, grain: 0.14 });
  return svg(s, 51);
}
function card_day() {
  let s = rect(0, 0, W, H, { fill: PAL.card });
  s += big(W / 2, 560, 'DAY 3', 190, '#F3EBDD');
  s += smallCaps(W / 2, 650, 'THE REGULARS', 34, PAL.tag);
  s += finish({ vignette: 0.9, grain: 0.14 });
  return svg(s, 52);
}
function card_problem() {
  let s = cream();
  s += icon.water(W / 2, 330, 1.2);
  s += smallCaps(W / 2, 560, 'PROBLEM 2', 34);
  s += big(W / 2, 720, 'WATER', 190);
  s += finish({ vignette: 0.5, grain: 0.1 });
  return svg(s, 53);
}
function card_rule() {
  let s = rect(0, 0, W, H, { fill: PAL.card });
  s += g(rect(W / 2 - 150, 290, 300, 76, { fill: PAL.tag }) + text(W / 2, 346, 'RULE 1', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 52, fill: PAL.card, textAnchor: 'middle', letterSpacing: 4 }), { transform: `rotate(-3 ${W / 2} 330)` });
  s += big(W / 2, 560, 'THEY HEAR.', 130, '#F3EBDD');
  s += big(W / 2, 720, "THEY DON'T SEE.", 130, '#F3EBDD');
  s += icon.ear(W / 2 - 40, 880, 0.8);
  s += finish({ vignette: 0.9, grain: 0.14 });
  return svg(s, 54);
}
function card_fact() {
  let s = cream();
  s += smallCaps(W / 2, 250, 'A CLOSED FREEZER STAYS COLD FOR ABOUT', 30);
  s += big(W / 2, 560, '48', 360);
  s += smallCaps(W / 2, 650, 'HOURS', 50, INK);
  // timeline bar
  s += rect(560, 760, 800, 34, { rx: 17, fill: '#FBF6EA', ...ink(5) }) + rect(560, 760, 520, 34, { rx: 17, fill: '#7FB3D5', ...ink(5) });
  s += text(560, 840, '0 h', { fontFamily: 'Rubik', fontWeight: 700, fontSize: 24, fill: '#6B5F55' }) + text(1360, 840, '72 h', { fontFamily: 'Rubik', fontWeight: 700, fontSize: 24, fill: '#6B5F55', textAnchor: 'end' });
  s += text(W / 2, 940, 'Source: USDA Food Safety', { fontFamily: 'Rubik', fontWeight: 500, fontSize: 20, fill: '#8E8576', textAnchor: 'middle' });
  s += finish({ vignette: 0.5, grain: 0.1 });
  return svg(s, 55);
}
function card_inventory() {
  let s = cream();
  s += smallCaps(W / 2, 150, 'SUPPLIES  ·  DAY 5', 40, INK);
  s += text(420, 300, 'Water', { fontFamily: 'Rubik', fontWeight: 700, fontSize: 34, fill: '#6B5F55' }) + text(1500, 300, '38 gal', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 56, fill: INK, textAnchor: 'end' });
  for (let i = 0; i < 10; i++) s += g(icon.water(450 + i * 105, 420, 0.55), { opacity: i < 7 ? 1 : 0.25 });
  s += text(420, 620, 'Food', { fontFamily: 'Rubik', fontWeight: 700, fontSize: 34, fill: '#6B5F55' }) + text(1500, 620, '9,000 cans', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 56, fill: INK, textAnchor: 'end' });
  for (let i = 0; i < 10; i++) s += icon.can(450 + i * 105, 720, 0.6, [PAL.red, PAL.yellow, PAL.green][i % 3]);
  s += text(420, 900, 'Batteries', { fontFamily: 'Rubik', fontWeight: 700, fontSize: 34, fill: '#6B5F55' }) + text(1500, 900, '3 days', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 56, fill: PAL.red, textAnchor: 'end' });
  s += text(W / 2, 1010, 'Food is not the problem. Light is.', { fontFamily: 'Rubik', fontWeight: 500, fontStyle: 'italic', fontSize: 30, fill: '#6B5F55', textAnchor: 'middle' });
  s += finish({ vignette: 0.5, grain: 0.1 });
  return svg(s, 56);
}
function card_map() {
  let s = rect(0, 0, W, H, { fill: '#EDE3CC' }) + rect(0, 0, W, H, { fill: 'url(#graph)' });
  s += smallCaps(260, 90, 'FRESHWAY · FLOOR PLAN', 28, INK);
  const X = 260, Y = 150, w = 1400, h = 800;
  let m = rect(X, Y, w, h, { fill: '#F7EFDC', ...ink(7) });
  for (let i = 0; i < 8; i++) m += rect(X + 140 + i * 150, Y + 170, 60, 460, { fill: '#D9CDB2', ...ink(4) }) + text(X + 170 + i * 150, Y + 160, String(i + 1), { fontFamily: 'Rubik', fontWeight: 800, fontSize: 22, fill: '#6B5F55', textAnchor: 'middle' });
  m += rect(X, Y + 690, w, 110, { fill: '#CFE3EA', ...ink(5) }) + text(X + w / 2, Y + 755, 'GLASS FRONT · SHUTTER', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 24, fill: '#3E6E9A', textAnchor: 'middle', letterSpacing: 3 });
  m += rect(X + 30, Y + 30, 360, 100, { fill: '#C8D8DE', ...ink(4) }) + text(X + 210, Y + 90, 'WALK-IN FREEZER', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 20, fill: '#3E6E9A', textAnchor: 'middle' });
  m += rect(X + w - 260, Y + 30, 230, 100, { fill: '#E3D6C1', ...ink(4) }) + text(X + w - 145, Y + 90, 'OFFICE', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 20, fill: '#6B5F55', textAnchor: 'middle' });
  m += rect(X + w - 30, Y + 220, 30, 90, { fill: '#3DBE6A', ...ink(4) }) + text(X + w + 20, Y + 270, 'FIRE EXIT', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 18, fill: '#2E7D4F' });
  // zombies outside
  const r = rng(61);
  for (let i = 0; i < 70; i++) m += circle(X + 30 + r() * (w - 60), Y + h + 30 + r() * 80, 9, { fill: PAL.zSkin, ...ink(3) });
  // sound rings from alarm clock thrown behind the store
  m += circle(X + w + 120, Y + 120, 20, { fill: PAL.red, ...ink(4) });
  for (const rr of [60, 110, 160]) m += circle(X + w + 120, Y + 120, rr, { fill: 'none', stroke: PAL.red, strokeWidth: 5, strokeDasharray: '14 10', opacity: 0.8 });
  // route
  m += path(`M${X + 520} ${Y + 600} L${X + 520} ${Y + 150} L${X + w - 300} ${Y + 150}`, { fill: 'none', stroke: INK, strokeWidth: 6, strokeDasharray: '4 16', strokeLinecap: 'round' });
  // YOU
  m += circle(X + 520, Y + 600, 26, { fill: PAL.red, ...ink(5) }) + rect(X + 548, Y + 558, 110, 46, { rx: 8, fill: PAL.red, ...ink(4) }) + text(X + 603, Y + 590, 'YOU', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 26, fill: '#FFF', textAnchor: 'middle' });
  s += g(m, { filter: 'url(#wobbleSoft)' });
  s += caption('clock', { y: 1050, size: 80 });
  s += finish({ vignette: 0.45, grain: 0.1 });
  return svg(s, 61);
}

// ---------- close-up reaction: hands under the bent shutter ----------
function closeup_shutter() {
  let s = rect(0, 0, W, H, { fill: '#9C988C' });
  for (let y = 0; y < 760; y += 30) s += path(`M0 ${y} Q960 ${y + 26 * Math.sin(y / 120)} ${W} ${y}`, { fill: 'none', stroke: '#6E6A60', strokeWidth: 5 });
  s += path('M0 760 Q960 700 1920 770 L1920 800 Q960 740 0 790 Z', { fill: '#5E5A52', ...ink(6) });
  s += rect(0, 790, W, 290, { fill: '#CFC2A6' });
  for (let x = -100; x < W + 100; x += 160) s += line(x, 790, x + (x - 960) * 0.5, 1080, { stroke: '#BDB096', strokeWidth: 3 });
  // grey hands sliding under the gap
  const hand = (x, rot, k) => g(path(`M0 0 L${-20 * k} ${80 * k} M0 0 c${-40 * k} ${20 * k} ${-50 * k} ${70 * k} ${-30 * k} ${110 * k} c${20 * k} ${30 * k} ${70 * k} ${30 * k} ${90 * k} ${-5 * k} c${20 * k} ${-40 * k} ${10 * k} ${-90 * k} ${-60 * k} ${-105 * k}`, { fill: PAL.zSkin, ...ink(7) })
    + path(`M${-30 * k} ${110 * k} l${-14 * k} ${46 * k} M${0} ${118 * k} l${-4 * k} ${52 * k} M${30 * k} ${112 * k} l${8 * k} ${48 * k} M${55 * k} ${95 * k} l${22 * k} ${40 * k}`, { fill: 'none', stroke: PAL.zSkin, strokeWidth: 26 * k, strokeLinecap: 'round' })
    + path(`M${-30 * k} ${110 * k} l${-14 * k} ${46 * k} M${0} ${118 * k} l${-4 * k} ${52 * k} M${30 * k} ${112 * k} l${8 * k} ${48 * k} M${55 * k} ${95 * k} l${22 * k} ${40 * k}`, { fill: 'none', stroke: INK, strokeWidth: 4, strokeLinecap: 'round', opacity: 0.6 }),
    { transform: `translate(${x} 770) rotate(${rot})` });
  s += hand(300, -10, 0.9) + hand(620, 8, 1) + hand(1500, -6, 0.85) + hand(1760, 12, 0.95);
  s = g(s, { filter: 'url(#wobble)' });
  // hero in the foreground, close
  s += hero({ x: 1420, y: 1560, s: 2.5, pose: 'scared', expr: 'scared', facing: -1, look: -0.6 });
  s += grade('dusk');
  s += hud({ theme: 'price', day: 38, time: '9:14 AM', noise: 1 });
  s += caption('cuff');
  s += watermark() + finish({ vignette: 1 });
  return svg(s, 71);
}

Object.assign(SCENES, { closeup_shutter, exterior_night, pov_stockroom, card_episode, card_day, card_problem, card_rule, card_fact, card_inventory, card_map });

export { svg, aisle, at, icon, smallCaps, big, cream, PROD };
