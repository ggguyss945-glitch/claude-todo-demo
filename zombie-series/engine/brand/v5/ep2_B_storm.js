// LAST LIGHT ep. 2, A/B concept B "THE STORM" (Day 10): you walk straight through two hundred of them in the
// thunderstorm. Every one of them has its face turned up to the rain; nobody turns to you. One bolt floods the
// lot with cold white-violet light so every face reads. Storm teal/violet + white lightning, one red word.
import { W, H, INK, PAL, finish, g, rect, circle, ellipse, line, poly, path, ink, rng } from '../../lib.js';
import { svgOf, headline, grade } from '../v2/pro.js';

const F = (n) => (+n).toFixed(1);
const lerp = (a, b, k) => a + (b - a) * k;
function mix(a, b, k) {
  const p = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const A = p(a), B = p(b);
  return '#' + A.map((v, i) => Math.round(lerp(v, B[i], k)).toString(16).padStart(2, '0')).join('');
}

// soft light as a radial gradient: never clips to a filter region, at any render scale
let GID = 0;
function soft(cx, cy, rx, ry, color, op) {
  const id = `sb_g${GID++}`;
  return `<radialGradient id="${id}"><stop offset="0" stop-color="${color}" stop-opacity="${op}"/><stop offset="0.4" stop-color="${color}" stop-opacity="${(op * 0.55).toFixed(3)}"/><stop offset="1" stop-color="${color}" stop-opacity="0"/></radialGradient>`
    + ellipse(cx, cy, rx, ry, { fill: `url(#${id})`, style: 'mix-blend-mode:screen' });
}
// user-space filter regions, each only as big as its layer needs (big regions at 2x cost GPU memory)
const FR = (x, y, w, h) => `filterUnits="userSpaceOnUse" x="${x}" y="${y}" width="${w}" height="${h}"`;

// ---------- palette ----------
const SKINS = ['#9DB28E', '#A4B592', '#94AC8A', '#A9B48C', '#98B096'];
const SKIN = '#9DB28E', SKIN_UNDER = '#56685A', SOCKET = '#272C27', PUPIL = '#F1F4E2', MOUTH = '#221C1B';
const RIM = '#E4DCFF', HAZE = '#6688A8', BOLT = '#F4F1FF', BOLT_GLOW = '#A993FF';
const CLOTHES = ['#C76A83', '#6FA3A6', '#A65F4A', '#7C6A8E', '#2E3D55', '#8A7A4E', '#D9A441', '#596471', '#B5452F', '#4F7A52', '#E0894A', '#8C8C86'];
const HAIR = ['#3A2A22', '#5B4636', '#2B2B2E', '#7A6A55', '#8E8A80'];

// ---------- the sky: violet storm ceiling, teal toward the horizon, lit from inside by the bolt ----------
export function sky() {
  let s = `<defs>
    <linearGradient id="sb_sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#120C28"/><stop offset="0.42" stop-color="#2A2155"/><stop offset="0.72" stop-color="#3E4F86"/><stop offset="1" stop-color="#4F8C96"/></linearGradient>
    <radialGradient id="sb_flash" cx="0.84" cy="0.22" r="0.62"><stop offset="0" stop-color="#F1ECFF" stop-opacity="0.95"/><stop offset="0.28" stop-color="#B9A8FF" stop-opacity="0.55"/><stop offset="0.65" stop-color="#6B5FC8" stop-opacity="0.18"/><stop offset="1" stop-color="#2A2155" stop-opacity="0"/></radialGradient>
    <linearGradient id="sb_cloud" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1A1438"/><stop offset="1" stop-color="#3A3170"/></linearGradient>
    <filter id="sb_cblur" ${FR(-200, -200, 2320, 700)}><feGaussianBlur stdDeviation="6"/></filter>
    <filter id="sb_cblur2" ${FR(-200, 250, 2320, 250)}><feGaussianBlur stdDeviation="6"/></filter>
    <filter id="sb_cityblur" ${FR(-100, 360, 2120, 260)}><feGaussianBlur stdDeviation="6"/></filter>
    <filter id="sb_boltglow" ${FR(1250, -150, 800, 850)}><feGaussianBlur stdDeviation="22"/></filter>
    <filter id="sb_boltglowS" ${FR(1250, -150, 800, 850)}><feGaussianBlur stdDeviation="7"/></filter>
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
  s += g(cl2, { filter: 'url(#sb_cblur2)' });
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
export function lightning() {
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
  s += soft(1680, 260, 760, 620, '#C9BCFF', 0.6) + soft(1700, 520, 520, 160, '#EDE8FF', 0.7);
  s += path(d(main), { fill: 'none', stroke: BOLT_GLOW, strokeWidth: 120, strokeLinejoin: 'round', strokeLinecap: 'round', opacity: 0.8, filter: 'url(#sb_boltglow)' });
  s += g(branches.map((b) => path(d(b), { fill: 'none', stroke: BOLT_GLOW, strokeWidth: 40, strokeLinejoin: 'round', strokeLinecap: 'round' })).join('')
    + path(d(main), { fill: 'none', stroke: '#D4C8FF', strokeWidth: 44, strokeLinejoin: 'round', strokeLinecap: 'round' }), { filter: 'url(#sb_boltglowS)', opacity: 0.75 });
  for (const b of branches) s += path(d(b), { fill: 'none', stroke: '#D9CFFF', strokeWidth: 12, strokeLinejoin: 'round', strokeLinecap: 'round' }) + path(d(b), { fill: 'none', stroke: BOLT, strokeWidth: 5, strokeLinejoin: 'round', strokeLinecap: 'round' });
  s += path(d(main), { fill: 'none', stroke: '#E7E0FF', strokeWidth: 28, strokeLinejoin: 'round', strokeLinecap: 'round' });
  s += path(d(main), { fill: 'none', stroke: '#FFFFFF', strokeWidth: 14, strokeLinejoin: 'round', strokeLinecap: 'round' });
  return s;
}

// the far edge of the lot: the city through the rain, a teal haze, the flash where the bolt comes down
export function horizon() {
  let s = '';
  const r = rng(12);
  let city = '';
  for (let x = -40; x < W; x += 90) { const h = 30 + r() * 100, near = Math.max(0, 1 - Math.abs(x - 1700) / 650); city += rect(x, 540 - h, 86, h + 40, { fill: mix('#34416E', '#7A7CC0', near * 0.7) }); }
  s += g(city, { filter: 'url(#sb_cityblur)', opacity: 0.9 });
  s += `<linearGradient id="sb_lot" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4E7E96"/><stop offset="1" stop-color="#2E4E6A"/></linearGradient>`;
  s += rect(0, 520, W, 560, { fill: 'url(#sb_lot)' });
  // a curtain of rain haze where the lot meets the city, so the far edge has no hard line
  s += `<linearGradient id="sb_mist" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8C9AD0" stop-opacity="0"/><stop offset="0.5" stop-color="#8C9AD0" stop-opacity="0.55"/><stop offset="1" stop-color="#8C9AD0" stop-opacity="0"/></linearGradient>`;
  s += rect(0, 450, W, 150, { fill: 'url(#sb_mist)' });
  s += soft(1700, 540, 700, 110, '#E2DAFF', 0.6);
  return s;
}

// ---------- the dead, faces turned up to the rain ----------
// The head is tipped right back: the features crowd into the top of the face, the eyes are rolled up to the sky,
// we see up the nostrils and the whole dark underside of the jaw. detail 0 = distant, 1 = mid, 2 = close.
function upHead(hx, hy, u, { skin, under, socket, pupil, rim, rimOp, lw, detail, r, hair }) {
  let s = circle(hx, hy, u, { fill: skin });
  // the face plane, turned to the sky, catches the flash
  s += ellipse(hx, hy - 0.34 * u, 0.7 * u, 0.5 * u, { fill: '#F4F8E6', opacity: 0.16 });
  // only a band of hair shows over the crown
  if (hair) s += path(`M${F(hx - 0.8 * u)} ${F(hy - 0.6 * u)} A${F(u)} ${F(u)} 0 0 1 ${F(hx + 0.8 * u)} ${F(hy - 0.6 * u)} Q${F(hx)} ${F(hy - 0.95 * u)} ${F(hx - 0.8 * u)} ${F(hy - 0.6 * u)} Z`, { fill: hair });
  // the underside of the jaw, in shadow
  const a1 = 0.05, a2 = Math.PI - 0.05, p1 = [hx + Math.cos(a1) * u, hy + Math.sin(a1) * u], p2 = [hx + Math.cos(a2) * u, hy + Math.sin(a2) * u];
  s += path(`M${F(p1[0])} ${F(p1[1])} A${F(u)} ${F(u)} 0 0 1 ${F(p2[0])} ${F(p2[1])} Q${F(hx)} ${F(hy + 0.62 * u)} ${F(p1[0])} ${F(p1[1])} Z`, { fill: under });
  s += path(`M${F(p2[0] + 0.05 * u)} ${F(p2[1] + 0.01 * u)} Q${F(hx)} ${F(hy + 0.62 * u)} ${F(p1[0] - 0.05 * u)} ${F(p1[1] + 0.01 * u)}`, { fill: 'none', stroke: INK, strokeWidth: lw * (detail ? 0.7 : 0.55), strokeLinecap: 'round', opacity: 0.85 });
  // eyes high, flattened by the angle, the pupils rolled right up under the top lids
  const ey = hy - 0.56 * u, sz = 0.94 + r() * 0.12;
  s += ellipse(hx - 0.33 * u, ey + 0.02 * u, 0.19 * u * sz, 0.1 * u * sz, { fill: socket }) + ellipse(hx + 0.32 * u, ey, 0.18 * u * sz, 0.095 * u * sz, { fill: socket });
  s += circle(hx - 0.32 * u, ey - 0.045 * u, 0.04 * u, { fill: pupil }) + circle(hx + 0.33 * u, ey - 0.055 * u, 0.038 * u, { fill: pupil });
  // up the nose
  s += ellipse(hx - 0.07 * u, hy - 0.36 * u, 0.042 * u, 0.03 * u, { fill: socket }) + ellipse(hx + 0.07 * u, hy - 0.36 * u, 0.042 * u, 0.03 * u, { fill: socket });
  // the jaw hangs slack
  const m = (x, y) => `${F(hx + x * u)} ${F(hy + y * u)}`;
  s += path(`M${m(-0.08, -0.22)} Q${m(0.01, -0.25)} ${m(0.09, -0.21)} Q${m(0.1, -0.01)} ${m(0.01, 0.0)} Q${m(-0.1, -0.02)} ${m(-0.08, -0.22)} Z`, { fill: MOUTH });
  // the bolt's light along the wet right side of the skull
  s += path(`M${F(hx + Math.cos(-1.2) * 0.88 * u)} ${F(hy + Math.sin(-1.2) * 0.88 * u)} A${F(0.88 * u)} ${F(0.88 * u)} 0 0 1 ${F(hx + Math.cos(0.0) * 0.88 * u)} ${F(hy + Math.sin(0.0) * 0.88 * u)}`,
    { fill: 'none', stroke: rim, strokeWidth: 0.07 * u, strokeLinecap: 'round', opacity: rimOp * 0.65 });
  if (detail >= 2) {
    // drops bouncing off the crown and the face
    for (const [dx, dy, a] of [[-0.3, -1.06, -35], [0.34, -1.04, 30], [0.02, -1.13, 0]]) s += line(hx + dx * u, hy + dy * u, hx + dx * u + Math.sin(a * Math.PI / 180) * 0.11 * u, hy + dy * u - Math.cos(a * Math.PI / 180) * 0.11 * u, { stroke: '#E8F0FF', strokeWidth: 0.03 * u, strokeLinecap: 'round', opacity: 0.85 });
    for (const [dx, dy] of [[-0.55, -0.2], [0.5, -0.3], [0.2, -0.75]]) s += circle(hx + dx * u, hy + dy * u, 0.025 * u, { fill: '#EEF4FF', opacity: 0.8 });
  }
  s += circle(hx, hy, u, { fill: 'none', stroke: INK, strokeWidth: lw });
  return s;
}
function upZombie(x, yg, sc, { body, fogK = 0, detail = 1, r, tilt = 0, rimOp = 0.9, hair }) {
  const u = 60 * sc, lw = Math.max(2.2, 0.085 * u), fog = (c) => mix(c, HAZE, fogK);
  const ik = { stroke: mix(INK, HAZE, fogK * 0.35), strokeWidth: lw, strokeLinecap: 'round', strokeLinejoin: 'round' };
  const top = yg - 4.25 * u, bot = yg, hx = x + (r() - 0.5) * 0.2 * u, hy = yg - 5.15 * u;
  const cloth = fog(body);
  let s = '';
  // neck, longer than usual: the head is tipped right back
  s += rect(hx - 0.24 * u, hy + 0.5 * u, 0.48 * u, top - hy - 0.3 * u, { fill: fog(SKIN_UNDER), ...ik });
  s += path(`M${F(x - 0.6 * u)} ${F(bot)} L${F(x - 0.66 * u)} ${F(top + 0.3 * u)} Q${F(x - 0.66 * u)} ${F(top)} ${F(x - 0.34 * u)} ${F(top)} L${F(x + 0.34 * u)} ${F(top)} Q${F(x + 0.66 * u)} ${F(top)} ${F(x + 0.66 * u)} ${F(top + 0.3 * u)} L${F(x + 0.6 * u)} ${F(bot)} Z`, { fill: cloth, ...ik });
  if (detail >= 1) {
    // collar and the light along the wet shoulder
    s += path(`M${F(x - 0.3 * u)} ${F(top + 0.02 * u)} L${F(x)} ${F(top + 0.32 * u)} L${F(x + 0.3 * u)} ${F(top + 0.02 * u)}`, { fill: 'none', stroke: mix(cloth, '#000000', 0.35), strokeWidth: lw * 0.8, strokeLinejoin: 'round' });
    s += path(`M${F(x + 0.36 * u)} ${F(top + 0.04 * u)} Q${F(x + 0.62 * u)} ${F(top + 0.04 * u)} ${F(x + 0.62 * u)} ${F(top + 0.4 * u)}`, { fill: 'none', stroke: RIM, strokeWidth: 0.09 * u, strokeLinecap: 'round', opacity: 0.5 * rimOp });
    // arms hanging limp at the sides: they are not reaching for anything
    for (const side of [-1, 1]) {
      const sx = x + side * 0.58 * u, sy = top + 0.25 * u, ex = x + side * 0.74 * u, ey = top + 1.85 * u;
      s += path(`M${F(sx)} ${F(sy)} Q${F(x + side * 0.86 * u)} ${F(top + 1.0 * u)} ${F(ex)} ${F(ey)}`, { fill: 'none', ...ik }) + circle(ex, ey, 0.17 * u, { fill: fog(SKIN), ...ik });
    }
  }
  const sk = SKINS[Math.floor(r() * SKINS.length)];
  const hd = upHead(hx, hy, u, { skin: fog(sk), under: fog(SKIN_UNDER), socket: mix(SOCKET, HAZE, fogK * 0.5), pupil: PUPIL, rim: RIM, rimOp, lw, detail, r, hair: hair ? fog(hair) : null });
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

// ---------- you: walking through them, head a little down, finger at the lips, hammer up and ready ----------
function heroHead(cx, cy, u, { down = 0.08, rim, id = 'sbh' }) {
  let s = circle(cx, cy, u, { fill: PAL.skin });
  s += `<mask id="rim_${id}"><circle cx="${F(cx)}" cy="${F(cy)}" r="${F(u)}" fill="#fff"/><circle cx="${F(cx - rim.side * 0.17 * u)}" cy="${F(cy + 0.08 * u)}" r="${F(u)}" fill="#000"/></mask>`
    + circle(cx, cy, u, { fill: rim.color, opacity: rim.op, mask: `url(#rim_${id})` });
  // hair, rain-flattened: the canon cap with the fringe a little lower; the cowlick still stands
  const hx = cx - u, hy = cy, dy = down * 0.6 * u;
  s += path(`M${F(hx + 0.02 * u)} ${F(hy - 0.05 * u)} C${F(hx - 0.02 * u)} ${F(hy - 1.1 * u)} ${F(cx + 1.1 * u)} ${F(cy - 1.25 * u)} ${F(cx + 0.98 * u)} ${F(cy - 0.12 * u)} L${F(cx + 0.7 * u)} ${F(cy - 0.4 * u + dy)} L${F(cx + 0.48 * u)} ${F(cy - 0.27 * u + dy)} L${F(cx + 0.18 * u)} ${F(cy - 0.47 * u + dy)} L${F(cx - 0.12 * u)} ${F(cy - 0.33 * u + dy)} L${F(cx - 0.45 * u)} ${F(cy - 0.5 * u + dy)} L${F(cx - 0.72 * u)} ${F(cy - 0.3 * u + dy)} Z`, { fill: PAL.hair, ...ink(0.04 * u) });
  // wet sheen on the hair from the flash
  s += path(`M${F(cx + 0.2 * u)} ${F(cy - 0.86 * u)} Q${F(cx + 0.62 * u)} ${F(cy - 0.78 * u)} ${F(cx + 0.82 * u)} ${F(cy - 0.42 * u)}`, { fill: 'none', stroke: '#B9A8E8', strokeWidth: 0.07 * u, strokeLinecap: 'round', opacity: 0.75 });
  s += path(`M${F(cx - 0.62 * u)} ${F(cy - 0.62 * u)} Q${F(cx - 0.4 * u)} ${F(cy - 0.8 * u)} ${F(cx - 0.12 * u)} ${F(cy - 0.84 * u)}`, { fill: 'none', stroke: '#8E7FB8', strokeWidth: 0.05 * u, strokeLinecap: 'round', opacity: 0.6 });
  s += path(`M${F(cx + rim.side * 0.6 * u)} ${F(cy - 0.8 * u)} Q${F(cx + rim.side * 0.95 * u)} ${F(cy - 0.52 * u)} ${F(cx + rim.side * 0.98 * u)} ${F(cy - 0.14 * u)}`, { fill: 'none', stroke: rim.color, strokeWidth: 0.07 * u, strokeLinecap: 'round', opacity: 0.85 });
  const lick = `M${F(cx + 0.05 * u)} ${F(cy - 0.98 * u)} q${F(0.1 * u)} ${F(-0.35 * u)} ${F(0.38 * u)} ${F(-0.3 * u)}`;
  s += path(lick, { fill: 'none', stroke: INK, strokeWidth: 0.19 * u, strokeLinecap: 'round' }) + path(lick, { fill: 'none', stroke: PAL.hair, strokeWidth: 0.11 * u, strokeLinecap: 'round' });
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
  s += path(`M${F(mx - 0.16 * u)} ${F(my + 0.05 * u)} Q${F(mx)} ${F(my - 0.04 * u)} ${F(mx + 0.16 * u)} ${F(my + 0.05 * u)}`, { fill: 'none', ...ink(0.055 * u) });
  s += circle(cx, cy, u, { fill: 'none', ...ink(0.045 * u) });
  return s;
}
// claw hammer; (gx, gy) = the grip, `ang` (degrees) points from the grip up the handle; the claw is on local +y
function hammer(gx, gy, u, ang) {
  const P = (x, y) => `${F(x * u)} ${F(y * u)}`, o = ink(0.035 * u);
  let s = rect(-0.3 * u, -0.075 * u, 1.62 * u, 0.15 * u, { rx: 0.07 * u, fill: '#9A6440', ...o });
  s += line(0.25 * u, -0.025 * u, 1.2 * u, -0.025 * u, { stroke: '#C69062', strokeWidth: 0.03 * u, strokeLinecap: 'round' });
  s += rect(-0.36 * u, -0.09 * u, 0.5 * u, 0.18 * u, { rx: 0.08 * u, fill: '#25272B', ...o });                    // rubber grip
  // the claw, curving back toward the handle
  s += path(`M${P(1.5, 0.08)} Q${P(1.52, 0.42)} ${P(1.18, 0.6)} Q${P(1.3, 0.4)} ${P(1.28, 0.1)} Z`, { fill: '#7E8893', ...o });
  s += path(`M${P(1.42, 0.22)} Q${P(1.38, 0.4)} ${P(1.26, 0.5)}`, { fill: 'none', stroke: INK, strokeWidth: 0.02 * u, strokeLinecap: 'round' });
  // the block, the neck and the round striking face
  s += rect(1.26 * u, -0.2 * u, 0.26 * u, 0.32 * u, { rx: 0.04 * u, fill: '#8E98A3', ...o });
  s += rect(1.3 * u, -0.36 * u, 0.18 * u, 0.18 * u, { fill: '#8E98A3', ...o });
  s += rect(1.25 * u, -0.48 * u, 0.28 * u, 0.13 * u, { rx: 0.04 * u, fill: '#B4BEC8', ...o });
  s += line(1.31 * u, -0.17 * u, 1.31 * u, 0.06 * u, { stroke: '#FFFFFF', strokeWidth: 0.03 * u, strokeLinecap: 'round', opacity: 0.85 });   // lightning glint
  return g(s, { transform: `translate(${F(gx)} ${F(gy)}) rotate(${ang})` });
}
// a jacket sleeve along shoulder -> elbow -> wrist, ink-outlined, round at the joints
function sleeveArm(pts, u, w = 0.24 * u) {
  const dd = 'M' + pts.map(([px, py]) => `${F(px)} ${F(py)}`).join(' L');
  return path(dd, { fill: 'none', stroke: INK, strokeWidth: w + 0.09 * u, strokeLinejoin: 'round', strokeLinecap: 'round' })
    + path(dd, { fill: 'none', stroke: PAL.jacket, strokeWidth: w, strokeLinejoin: 'round', strokeLinecap: 'round' });
}
function you(x, y, sc) {
  const u = 60 * sc, shY = y - 4.05 * u, neckY = y - 4.25 * u, hipY = y - 2.2 * u, cx = x, cy = y - 5.25 * u, lw = Math.max(4, 0.1 * u);
  const tw = 0.62 * u, bw = 0.56 * u, top = shY - 0.15 * u, bot = hipY + 0.1 * u;
  let b = '';
  // jacket, its hood down behind the neck, the flash along its wet right edge
  b += path(`M${F(x - tw)} ${F(top + 0.2 * u)} Q${F(x - tw)} ${F(top)} ${F(x - tw + 0.25 * u)} ${F(top)} L${F(x + tw - 0.25 * u)} ${F(top)} Q${F(x + tw)} ${F(top)} ${F(x + tw)} ${F(top + 0.2 * u)} L${F(x + bw)} ${F(bot)} L${F(x - bw)} ${F(bot)} Z`, { fill: PAL.jacket, ...ink(0.045 * u) });
  b += path(`M${F(x + tw - 0.06 * u)} ${F(top + 0.16 * u)} L${F(x + bw - 0.04 * u)} ${F(bot)}`, { fill: 'none', stroke: '#C9B8FF', strokeWidth: 0.07 * u, opacity: 0.6, strokeLinecap: 'round' });
  b += line(x + 0.04 * u, top + 0.12 * u, x + 0.04 * u, bot - 0.05 * u, { stroke: PAL.jacketDark, strokeWidth: 0.04 * u });
  b += path(`M${F(x - 0.42 * u)} ${F(bot - 0.75 * u)} h${F(0.28 * u)}`, { stroke: PAL.jacketDark, strokeWidth: 0.035 * u, fill: 'none' }) + path(`M${F(x + 0.16 * u)} ${F(bot - 0.75 * u)} h${F(0.28 * u)}`, { stroke: PAL.jacketDark, strokeWidth: 0.035 * u, fill: 'none' });
  b += path(`M${F(x - 0.55 * u)} ${F(top + 0.05 * u)} Q${F(x)} ${F(top - 0.32 * u)} ${F(x + 0.55 * u)} ${F(top + 0.05 * u)} Q${F(x)} ${F(top + 0.3 * u)} ${F(x - 0.55 * u)} ${F(top + 0.05 * u)} Z`, { fill: PAL.jacketDark, ...ink(0.035 * u) });
  // headphones around the neck
  const hp = `M${F(x - 0.55 * u)} ${F(neckY - 0.05 * u)} Q${F(x)} ${F(neckY + 0.55 * u)} ${F(x + 0.55 * u)} ${F(neckY - 0.05 * u)}`;
  b += path(hp, { fill: 'none', stroke: INK, strokeWidth: 0.2 * u }) + path(hp, { fill: 'none', stroke: PAL.phones, strokeWidth: 0.11 * u });
  b += rect(x - 0.86 * u, neckY - 0.3 * u, 0.36 * u, 0.5 * u, { rx: 0.12 * u, fill: PAL.phones, ...ink(0.035 * u) }) + rect(x + 0.5 * u, neckY - 0.3 * u, 0.36 * u, 0.5 * u, { rx: 0.12 * u, fill: PAL.phones, ...ink(0.035 * u) });
  // the hammer arm (your right, our left): elbow down at the side, the hammer raised by the head
  const sL = [x - 0.52 * u, shY + 0.08 * u], eL = [x - 0.86 * u, shY + 0.78 * u], hL = [x - 1.0 * u, shY - 0.3 * u];
  b += sleeveArm([sL, eL, hL], u);
  const hm = hammer(hL[0], hL[1], u, -100);
  // the shush arm (your left, our right): elbow out, the fist up under the chin
  const fist = [cx + 0.15 * u, cy + 0.98 * u], sR = [x + 0.52 * u, shY + 0.08 * u], eR = [x + 0.86 * u, shY + 0.8 * u];
  b += sleeveArm([sR, eR, [fist[0] + 0.05 * u, fist[1] + 0.08 * u]], u);
  const hd = heroHead(cx, cy, u, { down: 0.08, rim: { color: '#CDBEFF', side: 1, op: 0.8 } });
  // the hand at the lips: a fist under the chin, one finger up across the mouth
  let fr = rect(cx + 0.0 * u, cy + 0.4 * u, 0.15 * u, 0.5 * u, { rx: 0.075 * u, fill: PAL.skin, ...ink(0.035 * u) });
  fr += circle(fist[0], fist[1], 0.2 * u, { fill: PAL.skin, ...ink(0.04 * u) });
  const gripHand = circle(hL[0], hL[1], 0.19 * u, { fill: PAL.skin, ...ink(0.04 * u) });
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
  GID = 0;
  const HX = 1240, HS = 3.0, HU = 60 * HS, HY = 615 + 5.25 * HU;
  let s = sky() + lightning() + horizon();
  // the lot, packed to the far edge: back rows small and hazy, nearer rows bigger and sharper
  const far = [];
  for (let i = 0; i < 6; i++) { const t = i / 5; far.push({ x0: -60, x1: W + 60, y: lerp(600, 820, t), s: lerp(0.25, 0.64, t), dens: 1.35, fog: lerp(0.55, 0.28, t), detail: t > 0.6 ? 1 : 0, rim: lerp(0.5, 0.8, t) }); }
  s += rows({ list: far, seed: 3 });
  s += rect(0, 0, W, H, { fill: '#6F64C8', opacity: 0.06, style: 'mix-blend-mode:screen' });
  // the rows around you: packed close on both sides, behind your shoulders
  const mid = [
    { x0: -80, x1: W + 80, y: 975, s: 0.92, dens: 1.3, fog: 0.18, detail: 1, rim: 0.85 },
    { x0: -80, x1: W + 80, y: 1150, s: 1.3, dens: 1.4, fog: 0.08, detail: 1, rim: 0.9 },
  ];
  s += rows({ list: mid, seed: 9, skip: (x) => Math.abs(x - HX) < 150 });
  s += rain({ n: 260, seed: 4, len: [50, 100], w: 2.6, op: 0.32 });
  const r = rng(51);
  // the two right beside you, a step behind
  s += g(upZombie(HX - 480, 1470, 2.15, { body: '#C76A83', fogK: 0, detail: 2, r, tilt: -7, hair: '#5B4636' })
    + upZombie(HX + 440, 1470, 2.15, { body: '#6FA3A6', fogK: 0, detail: 2, r, tilt: 8, rimOp: 1 }), { filter: 'url(#wobbleSoft)' });
  // light from the bolt washing the crowd from the upper right
  s += soft(1650, 560, 1000, 520, '#B6A6FF', 0.3);
  // you
  s += soft(HX + 40, 600, 420, 420, '#8E7FE0', 0.3);
  s += you(HX, HY, HS);
  // the nearest ones at the edges of frame, cropped and a shade darker, out of the flash
  s += `<defs><filter id="sb_near"><feColorMatrix type="matrix" values="0.8 0 0 0 0 0 0.8 0 0 0 0 0 0.86 0 0.01 0 0 0 1 0"/></filter></defs>`;
  s += g(g(upZombie(60, 1900, 3.1, { body: '#D9A441', fogK: 0, detail: 2, r, tilt: -10, hair: '#2B2B2E' })
    + upZombie(1890, 1960, 3.1, { body: '#B5452F', fogK: 0, detail: 2, r, tilt: 10, rimOp: 1, hair: '#7A6A55' }), { filter: 'url(#wobbleSoft)' }), { filter: 'url(#sb_near)' });
  // the downpour over everything, heavier and softer up close
  s += rain({ n: 110, seed: 8, len: [130, 230], w: 4.5, op: 0.3 });
  s += grade('#3B2F6E', 0.1);
  s += headline(64, 210, 'WAIT FOR', { size: 178, anchor: 'start' }) + headline(56, 438, 'THUNDER', { size: 250, anchor: 'start', fill: 'url(#pro_red)' });
  s += finish({ vignette: 0.5, grain: 0.05 });
  return { w: W, h: H, svg: svgOf(s, 10), css: 'saturate(1.14) contrast(1.06)' };
}

export default () => thumbStorm();
