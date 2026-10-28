// Thumbnails v3: the niche's own clarity. Deadpan canon faces (small dot eyes), the scene tells the story:
// a horde you can read in a glance, one light colour, one idea per thumbnail, short text.
import { W, H, INK, PAL, finish, glow, hero, zombie, g, rect, circle, ellipse, line, poly, path, text, ink, rng } from '../../lib.js';
import { radioProp, mitt } from '../../ep/kit.js';
import { aisle } from '../../scenes.js';
import * as S from '../../ep/sets.js';
import { svgOf, headline, bloom, grade, RED, TAPE } from './pro.js';

const F = (n) => (+n).toFixed(1);
const lerp = (a, b, k) => a + (b - a) * k;
function mix(a, b, k) {
  const p = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const A = p(a), B = p(b);
  return '#' + A.map((v, i) => Math.round(lerp(v, B[i], k)).toString(16).padStart(2, '0')).join('');
}
const UNI = ['#8C8C86', '#2E3D55', '#C76A83', '#7C6A8E', '#8A7A4E', '#6FA3A6', '#A65F4A', '#596471', '#3B3F48'];

// a horde, back rows small and dark, front rows big; arms up, a rim of coloured light on one side of every head
function horde({ x0, x1, yb, yf, rows = 6, s0 = 0.42, s1 = 1.3, seed = 1, arms = 0.75, rim = RED, rimSide = -1, fog = '#0B0F1E', fogK = 0.65, density = 1.55 }) {
  const r = rng(seed); let out = '';
  for (let row = 0; row < rows; row++) {
    const t = row / (rows - 1), y = lerp(yb, yf, t * t * 0.5 + t * 0.5), sc = lerp(s0, s1, t * t), u = 60 * sc;
    const dim = fogK * (1 - t), lw = Math.max(2.5, 0.09 * u);
    const n = Math.max(3, Math.round((x1 - x0) / (u * density)));
    for (let i = 0; i < n; i++) {
      const x = x0 + ((i + 0.5 + (r() - 0.5) * 0.7) * (x1 - x0)) / n, yy = y + (r() - 0.5) * u * 0.6;
      const skin = mix('#8F9C86', fog, dim), body = mix(UNI[Math.floor(r() * UNI.length)], fog, dim), ink2 = { stroke: mix(INK, fog, dim * 0.4), strokeWidth: lw, strokeLinecap: 'round', strokeLinejoin: 'round' };
      const hx = x + (r() - 0.5) * 0.3 * u, hy = yy - 5.15 * u, tilt = (r() - 0.5) * 26;
      let z = rect(x - 0.62 * u, yy - 4.2 * u, 1.24 * u, 2.3 * u, { rx: 0.28 * u, fill: body, ...ink2 });
      if (r() < arms) for (const side of [-1, 1]) {
        const ax = x + side * (0.75 + r() * 0.45) * u, ay = yy - (6.3 + r() * 0.9) * u;
        z += path(`M${F(x + side * 0.5 * u)} ${F(yy - 3.9 * u)} Q${F(x + side * 0.95 * u)} ${F(yy - 5 * u)} ${F(ax)} ${F(ay)}`, { fill: 'none', ...ink2 }) + circle(ax, ay, 0.2 * u, { fill: skin, ...ink2 });
      }
      let hd = circle(hx, hy, u, { fill: skin, ...ink2 });
      const R = u * 0.86, a1 = rimSide < 0 ? 2.1 : -1.05, a2 = rimSide < 0 ? 4.2 : 1.05;
      hd += path(`M${F(hx + Math.cos(a1) * R)} ${F(hy + Math.sin(a1) * R)} A${F(R)} ${F(R)} 0 0 1 ${F(hx + Math.cos(a2) * R)} ${F(hy + Math.sin(a2) * R)}`, { fill: 'none', stroke: rim, strokeWidth: 0.16 * u, strokeLinecap: 'round', opacity: (0.35 + 0.6 * t).toFixed(2) });
      hd += ellipse(hx - 0.32 * u, hy + 0.02 * u, 0.2 * u, 0.23 * u, { fill: mix('#2B302A', fog, dim * 0.5) }) + ellipse(hx + 0.32 * u, hy + 0.05 * u, 0.19 * u, 0.21 * u, { fill: mix('#2B302A', fog, dim * 0.5) });
      hd += circle(hx - 0.29 * u, hy + 0.06 * u, 0.06 * u, { fill: '#E6EAD6' }) + circle(hx + 0.34 * u, hy + 0.09 * u, 0.055 * u, { fill: '#E6EAD6' }) + ellipse(hx + 0.03 * u, hy + 0.55 * u, 0.15 * u, 0.2 * u, { fill: '#241E1C' });
      out += g(z + g(hd, { transform: `rotate(${F(tilt)} ${F(hx)} ${F(hy + u)})` }));
    }
  }
  return g(out, { filter: 'url(#wobbleSoft)' });
}

// a shopping cart full of boxes, (x, y) = front wheel on the floor, facing left
function cart(x, y, k) {
  let s = '';
  s += path(`M${x} ${y - 70 * k} L${x + 20 * k} ${y - 230 * k} L${x + 300 * k} ${y - 230 * k} L${x + 280 * k} ${y - 70 * k} Z`, { fill: 'none', ...ink(6 * k) });
  for (let i = 1; i < 6; i++) s += line(x + (20 + i * 46) * k, y - 228 * k, x + (6 + i * 46) * k, y - 72 * k, { stroke: INK, strokeWidth: 3 * k });
  s += line(x + 10 * k, y - 150 * k, x + 290 * k, y - 150 * k, { stroke: INK, strokeWidth: 3 * k });
  s += line(x + 300 * k, y - 230 * k, x + 350 * k, y - 270 * k, ink(7 * k)) + line(x + 280 * k, y - 70 * k, x + 290 * k, y - 20 * k, ink(6 * k)) + line(x + 20 * k, y - 70 * k, x + 10 * k, y - 20 * k, ink(6 * k));
  s += circle(x + 20 * k, y - 12 * k, 13 * k, { fill: INK }) + circle(x + 270 * k, y - 12 * k, 13 * k, { fill: INK });
  const box = (bx, by, w, h, c) => rect(bx, by, w, h, { rx: 4 * k, fill: c, ...ink(4 * k) }) + line(bx, by + h * 0.3, bx + w, by + h * 0.3, { stroke: INK, strokeWidth: 2.5 * k });
  s += box(x + 40 * k, y - 330 * k, 120 * k, 100 * k, '#C9A06E') + box(x + 165 * k, y - 320 * k, 110 * k, 90 * k, '#BE9262') + box(x + 85 * k, y - 420 * k, 130 * k, 90 * k, '#D4AE7C');
  return g(s, { filter: 'url(#wobbleSoft)' });
}

// ---------- A: DAY 0 / DAY 7 ----------
function thumbA() {
  const T0 = [1010, 0], B0 = [930, 1080];
  let s = `<defs><clipPath id="p3a_l"><polygon points="0,0 ${T0} ${B0} 0,1080"/></clipPath><clipPath id="p3a_r"><polygon points="${T0} 1920,0 1920,1080 ${B0}"/></clipPath></defs>`;
  // DAY 0: bright, full shelves, you pushing a cart of stock down the aisle
  let L = g(aisle({ night: false, seed: 5 }).s, { transform: 'translate(-450 -40) scale(1.05)' });
  L += bloom(480, 260, 520, 240, '#FFF6DA', 0.35);
  L += cart(250, 1000, 1.0) + hero({ x: 690, y: 1000, s: 1.55, pose: 'push', expr: 'neutral', facing: -1, look: -0.2 });
  s += g(L, { clipPath: 'url(#p3a_l)' });
  // DAY 7: the same doors at night, a line of them on the glass, you at the edge with the radio
  let R = S.doorsOutside({ dawn: false });
  R += bloom(960, 640, 600, 320, '#8FB8FF', 0.35);
  R += horde({ x0: 560, x1: 1360, yb: 840, yf: 1080, rows: 4, s0: 0.75, s1: 1.25, seed: 11, arms: 0.55, rim: '#9FD0FF', rimSide: 1, fog: '#1A2540', fogK: 0.45, density: 1.45 });
  R += `<defs><filter id="p3a_dim"><feColorMatrix type="matrix" values="0.34 0 0 0 0 0 0.36 0 0 0 0 0 0.46 0 0.01 0 0 0 1 0"/></filter></defs>` + g(S.doorsInside(), { filter: 'url(#p3a_dim)' });
  R = g(R, { transform: 'translate(530 -60) scale(1.06)' });
  R += grade('#24345E', 0.35) + bloom(1900, 80, 260, 220, RED, 0.35);
  R += hero({ x: 1780, y: 1080, s: 1.85, pose: 'talkie', expr: 'worried', facing: 1, look: -0.6, extra: radioProp(1780 + 0.98 * 111 + 12, 1080 - 4.67 * 111 + 16, 0.5, { on: true, led: RED, rot: 8 }) });
  s += g(R, { clipPath: 'url(#p3a_r)' });
  s += line(...T0, ...B0, { stroke: INK, strokeWidth: 30 }) + line(...T0, ...B0, { stroke: '#FFFFFF', strokeWidth: 14 });
  s += headline(470, 200, 'DAY 0', { size: 200 }) + headline(1450, 200, 'DAY 7', { size: 200, fill: 'url(#pro_red)' });
  s += finish({ vignette: 0.35, grain: 0.04 });
  return { w: W, h: H, svg: svgOf(s, 5), css: 'saturate(1.12) contrast(1.06)' };
}

// ---------- B: POV, the radio in your hand, the horde, the man on the roof ----------
function thumbB() {
  let s = rect(0, 0, W, H, { fill: '#0A0D18' });
  // Freshway's dark front, sign off, roof edge against a pale moon
  s += circle(1520, 170, 150, { fill: '#E9DFC0' }) + bloom(1520, 170, 260, 220, '#E9DFC0', 0.35);
  s += g(rect(820, 330, 1180, 760, { fill: '#161B2A', ...ink(6) }) + rect(820, 305, 1180, 36, { fill: '#0C1020', ...ink(5) }) + rect(1000, 390, 820, 110, { rx: 10, fill: '#1C2E28', ...ink(5) })
    + text(1410, 472, 'FRESHWAY', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 78, fill: '#3E5E50', textAnchor: 'middle', letterSpacing: 10 }), { filter: 'url(#wobble)' });
  // Dale on the roof, black against the moon, his radio's red light
  const fx = 1520, fy = 307, k = 2.6, C = '#04050A';
  s += g(circle(fx, fy - 62 * k, 15 * k, { fill: C }) + rect(fx - 22 * k, fy - 67 * k, 44 * k, 9 * k, { rx: 3 * k, fill: C }) + rect(fx - 19 * k, fy - 48 * k, 38 * k, 48 * k, { rx: 9 * k, fill: C })
    + line(fx + 14 * k, fy - 40 * k, fx + 26 * k, fy - 66 * k, { stroke: C, strokeWidth: 8 * k, strokeLinecap: 'round' }) + rect(fx + 20 * k, fy - 86 * k, 12 * k, 24 * k, { rx: 3 * k, fill: C }));
  s += circle(fx + 26 * k, fy - 80 * k, 3.6 * k, { fill: RED }) + bloom(fx + 26 * k, fy - 80 * k, 50, 50, RED, 0.95, true);
  // the red emergency light over the side door, and the horde under it
  s += bloom(200, 700, 700, 520, RED, 0.45);
  s += horde({ x0: -120, x1: 1560, yb: 790, yf: 1210, rows: 6, s0: 0.38, s1: 1.45, seed: 21, arms: 0.85, rim: '#FF4A3A', rimSide: -1, fog: '#0A0D18', fogK: 0.7, density: 1.4 });
  s += grade('#3A1018', 0.18);
  // your hand and the walkie-talkie, bottom right, transmitting
  const hx = 1690, hy = 820;
  let pov = path(`M2000 1100 L1720 905 Q1650 860 1600 930 L1700 1100 Z`, { fill: PAL.jacket, ...ink(9) }) + path('M1745 925 L1640 1100', { stroke: PAL.jacketDark, strokeWidth: 8, fill: 'none' });
  pov += radioProp(hx, hy, 1.55, { on: true, led: RED, rot: -12 });
  for (let i = 0; i < 4; i++) pov += rect(hx - 112 + i * 4, hy - 10 + i * 46, 96, 40, { rx: 20, fill: PAL.skin, ...ink(6), transform: `rotate(-12 ${hx} ${hy})` });
  pov += path(`M${hx + 70} ${hy + 130} q40 -70 10 -150`, { fill: 'none', stroke: INK, strokeWidth: 44, strokeLinecap: 'round', transform: `rotate(-12 ${hx} ${hy})` }) + path(`M${hx + 70} ${hy + 130} q40 -70 10 -150`, { fill: 'none', stroke: PAL.skin, strokeWidth: 30, strokeLinecap: 'round', transform: `rotate(-12 ${hx} ${hy})` });
  s += g(pov, { filter: 'url(#wobbleSoft)' });
  const la = (-12 * Math.PI) / 180, llx = hx + (-30 * 1.55) * Math.cos(la) - (-140 * 1.55) * Math.sin(la), lly = hy + (-30 * 1.55) * Math.sin(la) + (-140 * 1.55) * Math.cos(la);
  s += bloom(llx, lly, 70, 70, RED, 0.95, true) + bloom(llx, lly, 200, 200, RED, 0.25);
  // text
  s += headline(70, 200, "HE'S", { size: 170, anchor: 'start' }) + headline(70, 370, 'LYING', { size: 190, anchor: 'start', fill: 'url(#pro_yel)' });
  s += g(rect(76, 410, 330, 96, { rx: 12, fill: '#D8261A', ...ink(8) }) + text(241, 482, 'DAY 7', { fontFamily: "'Lilita One'", fontSize: 72, fill: '#FFFFFF', textAnchor: 'middle', letterSpacing: 3 }), { filter: 'url(#pro_shadow)' });
  s += finish({ vignette: 0.6, grain: 0.05 });
  return { w: W, h: H, svg: svgOf(s, 6), css: 'saturate(1.12) contrast(1.08)' };
}

// ---------- C: the glass full of them, a minute to 7:00 ----------
function thumbC() {
  let sc = S.doorsOutside({ dawn: true }) + bloom(960, 420, 640, 300, '#FFC08A', 0.55);
  sc += horde({ x0: 520, x1: 1400, yb: 760, yf: 1180, rows: 6, s0: 0.5, s1: 1.4, seed: 7, arms: 0.95, rim: '#FFD2A0', rimSide: 1, fog: '#5A3A48', fogK: 0.55, density: 1.35 });
  sc += `<defs><filter id="p3c_dim"><feColorMatrix type="matrix" values="0.36 0 0 0 0 0 0.34 0 0 0 0 0 0.44 0 0.01 0 0 0 1 0"/></filter></defs>` + g(S.doorsInside(), { filter: 'url(#p3c_dim)' });
  let s = g(sc, { transform: 'translate(960 660) scale(1.3) translate(-960 -640)' });
  s += grade('#2A2F55', 0.22) + bloom(140, 900, 300, 260, RED, 0.22) + bloom(1780, 900, 300, 260, RED, 0.22);
  // the LED clock over the doors
  s += rect(0, 0, W, 210, { fill: '#1A1B26', opacity: 0.9 }) + g(rect(600, 18, 720, 250, { rx: 24, fill: '#120808', ...ink(9) }), { filter: 'url(#pro_shadow)' });
  s += ledDigits(678, 44, '6:59', 168) + text(960, 252, 'DOORS UNLOCK AT 7:00', { fontFamily: "'Lilita One'", fontSize: 36, fill: TAPE, textAnchor: 'middle', letterSpacing: 4 });
  s += bloom(960, 140, 380, 150, RED, 0.3);
  // you, inside, between us and the doors
  s += bloom(960, 1000, 380, 160, '#FFD7A8', 0.18);
  s += hero({ x: 960, y: 1080, s: 1.8, pose: 'scared', expr: 'worried', facing: 1, look: 0 });
  s += finish({ vignette: 0.5, grain: 0.04 });
  return { w: W, h: H, svg: svgOf(s, 7), css: 'saturate(1.12) contrast(1.06)' };
}
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

export const THUMBS3 = { thumbA, thumbB, thumbC };
