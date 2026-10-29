// Episode 2 thumbnail C: the niche's DAY X | DAY Y split. Day 8 in the bright store, Day 14 in the dark mall with
// Nora and the dead behind; PART 2 stamp across the seam. Every episode gets one thumbnail in this format.
import { W, H, INK, PAL, finish, g, rect, circle, ellipse, line, poly, path, text, ink, rng } from '../../lib.js';
import { svgOf, headline, bloom, grade, actor, RED, apron, stock, stockHands, survivalGear, crowbar } from '../v2/pro.js';
import { horde } from '../v2/pro3.js';
import { radioProp } from '../../ep/kit.js';
import { aisle } from '../../scenes.js';
import * as S2 from '../../ep/ep2/sets2.js';
import { NORA } from '../../ep/ep2/chars.js';

const F = (n) => (+n).toFixed(1);
const lerp = (a, b, k) => a + (b - a) * k;
function mix(a, b, k) {
  const p = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const A = p(a), B = p(b);
  return '#' + A.map((v, i) => Math.round(lerp(v, B[i], k)).toString(16).padStart(2, '0')).join('');
}
// soft light as a radial gradient (no filter region to clip at any render scale)
const EXT = { red: '#E3281C', hi: '#FF7058', lo: '#A3160F', metal: '#2A2C30', metalHi: '#5A5E66' };

function noraHead(cx, cy, u, { look = -0.4, rim, id = 'n' }) {
  let s = circle(cx, cy, u, { fill: NORA.skin });
  if (rim) s += `<mask id="rim_${id}"><circle cx="${F(cx)}" cy="${F(cy)}" r="${F(u)}" fill="#fff"/><circle cx="${F(cx - rim.side * 0.16 * u)}" cy="${F(cy + 0.06 * u)}" r="${F(u)}" fill="#000"/></mask>`
    + circle(cx, cy, u, { fill: rim.color, opacity: rim.op ?? 0.8, mask: `url(#rim_${id})` });
  // hair: a full cap over the crown, centre part, side-swept bangs, darker strands
  s += path(`M${F(cx - 1.04 * u)} ${F(cy + 0.2 * u)} C${F(cx - 1.12 * u)} ${F(cy - 1.46 * u)} ${F(cx + 1.12 * u)} ${F(cy - 1.46 * u)} ${F(cx + 1.04 * u)} ${F(cy + 0.2 * u)} L${F(cx + 0.84 * u)} ${F(cy - 0.18 * u)} C${F(cx + 0.58 * u)} ${F(cy - 0.45 * u)} ${F(cx + 0.22 * u)} ${F(cy - 0.6 * u)} ${F(cx + 0.03 * u)} ${F(cy - 0.8 * u)} C${F(cx - 0.24 * u)} ${F(cy - 0.5 * u)} ${F(cx - 0.6 * u)} ${F(cy - 0.42 * u)} ${F(cx - 0.86 * u)} ${F(cy - 0.16 * u)} Z`, { fill: NORA.hair, ...ink(0.042 * u) });
  s += path(`M${F(cx + 0.03 * u)} ${F(cy - 1.04 * u)} q${F(-0.05 * u)} ${F(0.12 * u)} 0 ${F(0.22 * u)}`, { fill: 'none', stroke: NORA.hairDark, strokeWidth: 0.045 * u, strokeLinecap: 'round' });
  s += path(`M${F(cx - 0.42 * u)} ${F(cy - 0.86 * u)} q${F(-0.3 * u)} ${F(0.22 * u)} ${F(-0.44 * u)} ${F(0.6 * u)} M${F(cx + 0.44 * u)} ${F(cy - 0.88 * u)} q${F(0.3 * u)} ${F(0.22 * u)} ${F(0.44 * u)} ${F(0.62 * u)}`, { fill: 'none', stroke: NORA.hairDark, strokeWidth: 0.035 * u, strokeLinecap: 'round', opacity: 0.75 });
  if (rim) s += path(`M${F(cx + rim.side * 0.5 * u)} ${F(cy - 0.98 * u)} Q${F(cx + rim.side * 1.02 * u)} ${F(cy - 0.68 * u)} ${F(cx + rim.side * 1.0 * u)} ${F(cy + 0.08 * u)}`, { fill: 'none', stroke: '#F6C2A6', strokeWidth: 0.06 * u, strokeLinecap: 'round', opacity: 0.85 });
  // eyes: serious and steady, lids a little heavy, a lash flick at the outer corner
  const ex = cx + look * 0.26 * u, ey = cy + 0.07 * u, sp = 0.48 * u;
  for (const side of [-1, 1]) {
    const x0 = ex + side * sp / 2;
    s += ellipse(x0, ey, 0.12 * u, 0.18 * u, { fill: INK });
    s += circle(x0 + 0.045 * u, ey - 0.05 * u, 0.045 * u, { fill: '#FFFFFF' });
    const base = ey - 0.18 * u + 0.3 * 0.36 * u, tilt = 0.02 * u, yo = base - tilt, yi = base + tilt, xo = x0 + side * 0.16 * u, xi = x0 - side * 0.16 * u;
    s += poly([[xo, ey - 0.25 * u], [xi, ey - 0.25 * u], [xi, yi], [xo, yo]], { fill: NORA.skin }) + line(xo, yo, xi, yi, ink(0.045 * u));
    s += path(`M${F(xo - side * 0.02 * u)} ${F(yo + 0.005 * u)} l${F(side * 0.08 * u)} ${F(-0.06 * u)}`, { fill: 'none', ...ink(0.035 * u) });
    const by = ey - 0.33 * u;
    s += line(x0 + side * 0.14 * u, by - 0.01 * u, x0 - side * 0.12 * u, by + 0.04 * u, { stroke: NORA.hairDark, strokeWidth: 0.07 * u, strokeLinecap: 'round' });
  }
  for (const side of [-1, 1]) for (const [dx, dy] of [[0, 0], [0.1, 0.05], [-0.07, 0.08], [0.04, 0.12]]) s += circle(ex + side * (0.36 + dx) * u, ey + (0.22 + dy) * u, 0.028 * u, { fill: NORA.freckle });
  const mx = ex + look * 0.04 * u, my = cy + 0.53 * u;
  s += path(`M${F(mx - 0.1 * u)} ${F(my + 0.01 * u)} L${F(mx + 0.1 * u)} ${F(my + 0.01 * u)}`, { fill: 'none', ...ink(0.045 * u) });
  s += circle(cx, cy, u, { fill: 'none', ...ink(0.045 * u) });
  return s;
}

// ---------- the extinguisher ----------
// hanging from its carry handle: (hx, hy) = the hand on the handle; k = scale; returns markup and the hose outlet
function extinguisher(hx, hy, k, ang = 0) {
  const lw = 5.5 * k;
  let s = `<defs><linearGradient id="cd_ext" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="${EXT.lo}"/><stop offset="0.24" stop-color="${EXT.hi}"/><stop offset="0.5" stop-color="${EXT.red}"/><stop offset="1" stop-color="${EXT.lo}"/></linearGradient></defs>`;
  // local: origin at the carry handle grip, cylinder below
  let b = '';
  b += rect(-66 * k, 70 * k, 132 * k, 380 * k, { rx: 48 * k, fill: 'url(#cd_ext)', ...ink(lw) });
  b += rect(-42 * k, 92 * k, 15 * k, 280 * k, { rx: 7 * k, fill: '#FFFFFF', opacity: 0.38 });
  b += rect(-48 * k, 168 * k, 96 * k, 120 * k, { rx: 8 * k, fill: '#F6F1E4', ...ink(3.5 * k) }) + rect(-48 * k, 168 * k, 96 * k, 28 * k, { rx: 6 * k, fill: '#1E1A1A' });
  b += text(0, 189 * k, 'FIRE', { fontFamily: "'Lilita One'", fontSize: 21 * k, fill: '#F6F1E4', textAnchor: 'middle', letterSpacing: 2 * k });
  b += text(0, 248 * k, 'CO2', { fontFamily: "'Lilita One'", fontSize: 36 * k, fill: EXT.red, textAnchor: 'middle' });
  b += line(-34 * k, 268 * k, 34 * k, 268 * k, { stroke: '#1E1A1A', strokeWidth: 5 * k, strokeLinecap: 'round' });
  // neck and valve head
  b += rect(-20 * k, 42 * k, 40 * k, 34 * k, { fill: EXT.metalHi, ...ink(lw * 0.8) });
  b += rect(-40 * k, 8 * k, 80 * k, 40 * k, { rx: 9 * k, fill: EXT.metal, ...ink(lw * 0.8) }) + line(-32 * k, 16 * k, 28 * k, 16 * k, { stroke: '#8A9099', strokeWidth: 3 * k, strokeLinecap: 'round' });
  // carry handle (in the hand) and the squeeze lever over it
  const bar = (d) => path(d, { fill: 'none', stroke: INK, strokeWidth: 24 * k, strokeLinecap: 'round' }) + path(d, { fill: 'none', stroke: EXT.metal, strokeWidth: 13 * k, strokeLinecap: 'round' });
  b += bar(`M${-30 * k} ${16 * k} L${-110 * k} ${6 * k}`) + bar(`M${-26 * k} ${2 * k} L${-104 * k} ${-26 * k}`);
  // gauge and safety pin
  b += circle(46 * k, 26 * k, 19 * k, { fill: '#F6F1E4', ...ink(3.5 * k) }) + path(`M${33 * k} ${26 * k} A${13 * k} ${13 * k} 0 0 1 ${52 * k} ${15 * k}`, { fill: 'none', stroke: '#3DBE6A', strokeWidth: 4.5 * k }) + line(46 * k, 26 * k, 54 * k, 15 * k, { stroke: INK, strokeWidth: 3 * k, strokeLinecap: 'round' });
  b += circle(-52 * k, 36 * k, 12 * k, { fill: 'none', stroke: '#F2C230', strokeWidth: 5 * k });
  s += g(b, { transform: `translate(${F(hx + 70 * k)} ${F(hy)}) rotate(${F(ang)})` });
  const a = (ang * Math.PI) / 180, out = [hx + 70 * k + (-8 * k) * Math.cos(a) - (6 * k) * Math.sin(a), hy + (-8 * k) * Math.sin(a) + (6 * k) * Math.cos(a)];
  return { s, out };
}
// the black horn: mouth centre (mx, my), facing along `dir` degrees
// Nora behind him: hair, hoodie, arms; her right hand presses the horn into his neck, her left holds the cylinder
function noraBack({ x, y, u }) {
  const cx = x, cy = y - 5.25 * u, shY = y - 4.05 * u, hipY = y - 2.2 * u, neckY = y - 4.25 * u;
  let s = '';
  s += path(`M${F(cx - 1.04 * u)} ${F(cy - 0.1 * u)} C${F(cx - 1.32 * u)} ${F(cy + 0.9 * u)} ${F(cx - 1.12 * u)} ${F(cy + 1.85 * u)} ${F(cx - 0.62 * u)} ${F(cy + 2.05 * u)} L${F(cx + 0.62 * u)} ${F(cy + 2.05 * u)} C${F(cx + 1.12 * u)} ${F(cy + 1.85 * u)} ${F(cx + 1.32 * u)} ${F(cy + 0.9 * u)} ${F(cx + 1.04 * u)} ${F(cy - 0.1 * u)} Z`, { fill: NORA.hair, ...ink(0.042 * u) });
  const tw = 0.64 * u, bw = 0.58 * u, top = shY - 0.15 * u, bot = hipY + 0.1 * u;
  s += path(`M${F(x - tw)} ${F(top + 0.2 * u)} Q${F(x - tw)} ${F(top)} ${F(x - tw + 0.25 * u)} ${F(top)} L${F(x + tw - 0.25 * u)} ${F(top)} Q${F(x + tw)} ${F(top)} ${F(x + tw)} ${F(top + 0.2 * u)} L${F(x + bw)} ${F(bot)} L${F(x - bw)} ${F(bot)} Z`, { fill: NORA.hoodie, ...ink(0.042 * u) });
  s += path(`M${F(x - 0.4 * u)} ${F(bot - 0.6 * u)} Q${F(x)} ${F(bot - 0.75 * u)} ${F(x + 0.4 * u)} ${F(bot - 0.6 * u)}`, { fill: 'none', stroke: NORA.hoodieDark, strokeWidth: 0.04 * u });
  s += path(`M${F(x - 0.62 * u)} ${F(neckY + 0.05 * u)} Q${F(x)} ${F(neckY - 0.35 * u)} ${F(x + 0.62 * u)} ${F(neckY + 0.05 * u)} Q${F(x)} ${F(neckY + 0.45 * u)} ${F(x - 0.62 * u)} ${F(neckY + 0.05 * u)} Z`, { fill: NORA.hoodieDark, ...ink(0.035 * u) });
  s += line(x - 0.16 * u, neckY + 0.2 * u, x - 0.2 * u, neckY + 0.8 * u, { stroke: '#E8E1D2', strokeWidth: 0.05 * u, strokeLinecap: 'round' }) + line(x + 0.16 * u, neckY + 0.2 * u, x + 0.22 * u, neckY + 0.74 * u, { stroke: '#E8E1D2', strokeWidth: 0.05 * u, strokeLinecap: 'round' });
  s += noraHead(cx, cy, u, { look: -0.5, rim: { color: '#DDF7F2', side: 1, op: 0.5 }, id: 'nora' });
  return { s, shR: [x - 0.52 * u, shY + 0.05 * u], shL: [x + 0.52 * u, shY + 0.05 * u] };
}

function thumb() {
  const SEAM = [[1000, 0], [920, 1080]];
  let s = `<defs><clipPath id="c8_l"><polygon points="0,0 ${SEAM[0].join(',')} ${SEAM[1].join(',')} 0,1080"/></clipPath><clipPath id="c8_r"><polygon points="${SEAM[0].join(',')} 1920,0 1920,1080 ${SEAM[1].join(',')}"/></clipPath>
    <linearGradient id="c8_warm" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFE7A6" stop-opacity="0.55"/><stop offset="1" stop-color="#FFB36B" stop-opacity="0.1"/></linearGradient>
    <filter id="c8_night"><feColorMatrix type="matrix" values="0.42 0 0 0 0 0 0.5 0 0 0.01 0 0 0.62 0 0.03 0 0 0 1 0"/></filter></defs>`;
  const sc = 2.75, gy = 1430, u = 60 * sc;
  // DAY 8: the bright store; you carrying the water, calm
  let L = g(aisle({ night: false, seed: 5 }).s, { transform: 'translate(-460 -20) scale(1.04)', filter: 'url(#pro_b2)' });
  L += rect(0, 0, 1000, 1080, { fill: 'url(#c8_warm)', opacity: 0.6, style: 'mix-blend-mode:multiply' }) + bloom(470, 330, 420, 260, '#FFF6DA', 0.4);
  L += actor({ x: 470, y: gy, s: sc, pose: 'carry', face: 'calm', look: 0, extra: apron(470, gy, u) + stock(470, gy, u), front: stockHands(470, gy, u), id: 'c80', rim: { color: '#FFF3C8', side: -1, op: 0.6 } });
  s += g(L, { clipPath: 'url(#c8_l)' });
  // DAY 14: Brookfield Mall at night, the dead filling the atrium behind you and Nora
  let R = g(S2.atrium(), { transform: 'translate(560 -40) scale(1.0)', filter: 'url(#c8_night)' });
  R = g(R, { filter: 'url(#pro_b2)' });
  R += grade('#24406A', 0.35) + bloom(1500, 120, 520, 200, '#BFEFEA', 0.35) + bloom(1890, 90, 300, 240, RED, 0.4);
  R += horde({ x0: 900, x1: 2000, yb: 860, yf: 1200, rows: 4, s0: 0.62, s1: 1.08, seed: 14, arms: 0.12, rim: '#BFEFEA', rimSide: 1, fog: '#1A2B40', fogK: 0.4, density: 1.35 });
  // Nora, a step behind your right shoulder, the extinguisher hanging from her hand
  const nu = 150, nx = 1700, ny = 640 + 5.25 * nu;
  const N = noraBack({ x: nx, y: ny, u: nu });
  // she carries it at her side, elbow bent, so the whole red cylinder sits in frame
  const k = 0.68, hand = [nx + 0.74 * nu, ny - 4.0 * nu], E = extinguisher(hand[0] - 40 * k, hand[1], k, 0);
  const lw = Math.max(4, 0.1 * nu);
  let nora = N.s;
  nora += path(`M${F(N.shL[0])} ${F(N.shL[1])} Q${F(N.shL[0] + 0.5 * nu)} ${F(N.shL[1] + 1.25 * nu)} ${F(hand[0] - 40 * k)} ${F(hand[1] + 10 * k)}`, { fill: 'none', ...ink(lw) });
  nora += E.s + circle(hand[0] - 40 * k, hand[1] + 10 * k, 0.17 * nu, { fill: NORA.skin, ...ink(0.035 * nu) });
  const hR = [nx - 0.78 * nu, ny - 2.45 * nu];
  nora += path(`M${F(N.shR[0])} ${F(N.shR[1])} Q${F(N.shR[0] - 0.25 * nu)} ${F(N.shR[1] + 0.8 * nu)} ${F(hR[0])} ${F(hR[1])}`, { fill: 'none', ...ink(lw) }) + circle(hR[0], hR[1], 0.17 * nu, { fill: NORA.skin, ...ink(0.035 * nu) });
  R += bloom(1700, 640, 300, 360, '#7FD6CC', 0.18);
  R += g(g(nora, { filter: 'url(#wobbleSoft)' }), { filter: 'url(#pro_stk)' });
  // you: a week of it on your face, the radio on your chest, the crowbar on your shoulder
  const x7 = 1380, hx = x7 + 0.98 * u, hy = gy - 4.67 * u;
  const chestRadio = radioProp(x7 - 0.33 * u, gy - 3.05 * u, 0.42, { on: true, led: RED, rot: -6 });
  R += actor({ x: x7, y: gy, s: sc, pose: 'talkie', face: 'serious', look: -0.22, tired: true, bandage: true, scratch: true, id: 'c814',
    rim: { color: '#9FE3DA', side: -1, op: 0.75 }, extra: survivalGear(x7, gy, u) + chestRadio + crowbar(x7, gy, u), front: circle(hx, hy, 0.17 * u, { fill: PAL.skin, ...ink(0.05 * u) }) });
  R += bloom(x7 - 0.33 * u - 30 * 0.42, gy - 3.05 * u - 140 * 0.42, 50, 50, RED, 0.9, true);
  s += g(R, { clipPath: 'url(#c8_r)' });
  s += line(...SEAM[0], ...SEAM[1], { stroke: INK, strokeWidth: 42 }) + line(...SEAM[0], ...SEAM[1], { stroke: '#FFFFFF', strokeWidth: 22 });
  s += headline(470, 210, 'DAY 8', { size: 210 }) + headline(1450, 210, 'DAY 14', { size: 210, fill: 'url(#pro_red)' });
  // PART 2 stamp across the seam
  s += g(rect(-250, -78, 500, 156, { rx: 14, fill: '#F6F1E4', stroke: '#D8261A', strokeWidth: 16 }) + rect(-226, -54, 452, 108, { rx: 8, fill: 'none', stroke: '#D8261A', strokeWidth: 5 })
    + text(0, 40, 'PART 2', { fontFamily: "'Lilita One'", fontSize: 112, fill: '#D8261A', textAnchor: 'middle', letterSpacing: 6 }), { transform: 'translate(700 948) rotate(-6)', filter: 'url(#pro_shadow)' });
  s += finish({ vignette: 0.35, grain: 0.05 });
  return { w: W, h: H, svg: svgOf(s, 5), css: 'saturate(1.12) contrast(1.06)' };
}

export default () => thumb();
