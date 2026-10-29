// LAST LIGHT ep. 2, A/B concept C "DON'T MOVE" (Day 10, top floor of Brookfield Mall):
// something cold touches the back of your neck. A girl, right behind you: "Don't. Move." It's a fire extinguisher.
// You, big, frozen, eyes turned toward her; Nora over your shoulder pressing the horn of a red extinguisher into
// your neck; behind you the glass railing and, below, the dry fountain with the dead standing around it.
// Cold storm daylight from the glass roof is the one light; teal is the dominant colour, the extinguisher the pop.
import { W, H, INK, PAL, finish, hero, zombie, body, g, rect, circle, ellipse, line, poly, path, text, ink, rng } from '../../lib.js';
import { svgOf, headline } from '../v2/pro.js';
import { NORA } from '../../ep/ep2/chars.js';

const F = (n) => (+n).toFixed(1);
const lerp = (a, b, k) => a + (b - a) * k;
function mix(a, b, k) {
  const p = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const A = p(a), B = p(b);
  return '#' + A.map((v, i) => Math.round(lerp(v, B[i], k)).toString(16).padStart(2, '0')).join('');
}
// soft light as a radial gradient (no filter region to clip at any render scale)
let GID = 0;
function soft(cx, cy, rx, ry, color, op, blend = 'screen') {
  const id = `cd_g${GID++}`;
  return `<radialGradient id="${id}"><stop offset="0" stop-color="${color}" stop-opacity="${op}"/><stop offset="0.45" stop-color="${color}" stop-opacity="${(op * 0.5).toFixed(3)}"/><stop offset="1" stop-color="${color}" stop-opacity="0"/></radialGradient>`
    + ellipse(cx, cy, rx, ry, { fill: `url(#${id})`, style: `mix-blend-mode:${blend}` });
}
const FR = 'filterUnits="userSpaceOnUse" x="-120" y="-120" width="2160" height="1320"';

// ---------- palette ----------
const LIGHT = '#CFF3EE', RIMC = '#B8F0EA';
const EXT = { red: '#E0261B', hi: '#FF6B55', lo: '#A3160F', metal: '#2A2C30', metalHi: '#5A5E66' };

// ---------- the mall: glass roof in the rain, the far balconies, the ground floor ----------
function roof() {
  let s = `<defs>
    <linearGradient id="cd_glass" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#10262E"/><stop offset="0.55" stop-color="#1E4A50"/><stop offset="0.78" stop-color="#4D8A88"/><stop offset="1" stop-color="#2C5E62"/></linearGradient>
    <filter id="cd_rb" ${FR}><feGaussianBlur stdDeviation="1.2"/></filter>
  </defs>`;
  s += rect(0, 0, W, 300, { fill: 'url(#cd_glass)' });
  // panes: mullions converge on a point far above the middle
  const vp = [1150, -1400];
  for (let x = -1400; x <= W + 1400; x += 230) s += line(x, 300, lerp(vp[0], x, 0.0) + (x - vp[0]) * 0.18, 0, { stroke: '#0A1A1F', strokeWidth: 14 });
  for (const y of [48, 120, 205]) s += line(0, y, W, y, { stroke: '#0A1A1F', strokeWidth: 10 });
  // rain on the glass: streaks running down, beads
  const r = rng(12); let rn = '';
  for (let i = 0; i < 230; i++) {
    const x = r() * W, y = r() * 300, l = 18 + r() * 46;
    rn += line(x, y, x - 6, y + l, { stroke: '#D8F4F2', strokeWidth: 2.4 + r() * 1.6, strokeLinecap: 'round', opacity: (0.18 + r() * 0.35).toFixed(2) });
  }
  for (let i = 0; i < 120; i++) rn += circle(r() * W, r() * 300, 2 + r() * 3.5, { fill: '#E6FAF8', opacity: (0.25 + r() * 0.4).toFixed(2) });
  s += g(rn, { filter: 'url(#cd_rb)' });
  // the steel beam the roof sits on
  s += rect(0, 296, W, 30, { fill: '#0C1C21' }) + line(0, 296, W, 296, { stroke: '#3E6A6C', strokeWidth: 4 });
  return s;
}
function farWall() {
  let s = rect(0, 320, W, 760, { fill: '#163036' });
  // one far tier of shops (the level below us, across the void), shutters down, sign bands in colour
  const shops = [['GAME ZONE', '#7C6A8E'], ['BOOK NOOK', '#B58759'], ['NAIL BAR', '#C76A83'], ['SPORTS HUB', '#6F8F4E'], ['TOY TOWN', '#D9A441']];
  shops.forEach(([name, col], i) => {
    const x = -60 + i * 420, w = 380, top = 352;
    s += rect(x, top, w, 190, { fill: '#0F2226', ...ink(4) }) + rect(x, top, w, 38, { fill: mix(col, '#163036', 0.35), ...ink(4) });
    s += text(x + w / 2, top + 28, name, { fontFamily: 'Rubik', fontWeight: 900, fontSize: 24, fill: '#E9EEE6', textAnchor: 'middle', letterSpacing: 4, opacity: 0.75 });
    for (let y = top + 50; y < top + 186; y += 15) s += line(x + 6, y, x + w - 6, y, { stroke: '#1C3439', strokeWidth: 5 });
  });
  // that tier's balcony: glass railing and slab
  s += rect(0, 500, W, 44, { fill: '#5E9A9A', opacity: 0.18 }) + line(0, 500, W, 500, { stroke: '#8FB8B4', strokeWidth: 7, opacity: 0.8 });
  s += rect(0, 544, W, 22, { fill: '#5C7472', ...ink(4) });
  // ground-floor shops far below, deep in the dark
  shops.forEach(([, col], i) => {
    const x = 150 + i * 420, w = 360, top = 610;
    s += rect(x, top, w, 220, { fill: '#0D1D21', ...ink(3) }) + rect(x, top, w, 30, { fill: mix(col, '#0D1D21', 0.55), ...ink(3) });
  });
  return s;
}
function groundFloor(fx, fy) {
  let s = `<defs><linearGradient id="cd_floor" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4E6A68"/><stop offset="1" stop-color="#6F8E88"/></linearGradient></defs>`;
  s += rect(0, 820, W, 260, { fill: 'url(#cd_floor)' }) + line(0, 820, W, 820, ink(4));
  for (let x = -600; x < W + 900; x += 170) s += line(x, 820, x + (x - fx) * 0.9, 1080, { stroke: '#44605E', strokeWidth: 3 });
  for (const y of [868, 935, 1020]) s += line(0, y, W, y, { stroke: '#44605E', strokeWidth: 3 });
  return s;
}
// the dry fountain: a wide stone basin, empty, the column in the middle
function fountain(cx, cy, k = 1) {
  let s = ellipse(cx, cy, 300 * k, 64 * k, { fill: '#A7A99C', ...ink(6) }) + ellipse(cx, cy - 6 * k, 262 * k, 46 * k, { fill: '#56605A', ...ink(4) });
  const r = rng(4); for (let i = 0; i < 14; i++) s += circle(cx + (r() - 0.5) * 380 * k, cy - 6 * k + (r() - 0.5) * 50 * k, 4.5 * k, { fill: '#C9A43A' });
  s += rect(cx - 30 * k, cy - 120 * k, 60 * k, 112 * k, { fill: '#B9BAAE', ...ink(5) }) + ellipse(cx, cy - 120 * k, 118 * k, 24 * k, { fill: '#B9BAAE', ...ink(5) }) + ellipse(cx, cy - 124 * k, 96 * k, 14 * k, { fill: '#6C756E' });
  s += rect(cx - 12 * k, cy - 184 * k, 24 * k, 62 * k, { fill: '#B9BAAE', ...ink(4) }) + ellipse(cx, cy - 186 * k, 50 * k, 12 * k, { fill: '#B9BAAE', ...ink(4) }) + circle(cx, cy - 204 * k, 12 * k, { fill: '#B9BAAE', ...ink(4) });
  return s;
}
// a shopping bag hanging from a zombie's hand
const bag = (hx, hy, u, col, side) => {
  const w = 0.62 * u, h = 0.72 * u, x = hx - w / 2 + side * 0.05 * u, y = hy + 0.1 * u;
  return path(`M${F(x + w * 0.25)} ${F(y)} q${F(w * 0.25)} ${F(-0.32 * u)} ${F(w * 0.5)} 0`, { fill: 'none', ...ink(Math.max(3, 0.06 * u)) }) + rect(x, y, w, h, { rx: 0.05 * u, fill: col, ...ink(Math.max(3, 0.06 * u)) })
    + line(x + w * 0.2, y + h * 0.3, x + w * 0.8, y + h * 0.3, { stroke: '#FFFFFF', strokeWidth: 0.05 * u, opacity: 0.6 });
};
// the dead around the fountain; [x, y, s, outfit, tilt, up, bagColour]
function theDead(list) {
  let s = '';
  for (const [x, y, sc, outfit, tilt, up, bc] of list.sort((a, b) => a[1] - b[1])) {
    const u = 60 * sc;
    const extra = bc ? bag(x + 0.8 * u, y - 2.25 * u, u, bc, 1) : '';
    s += zombie({ x, y, s: sc, outfit, tilt, look: 0.15 * Math.sin(x), up, filter: false, extra });
    // cold rim from the roof light, on the top-right of every head
    const hx = x + 0.1 * u, hy = y - 5.15 * u;
    s += path(`M${F(hx - 0.55 * u)} ${F(hy - 0.72 * u)} A${F(0.88 * u)} ${F(0.88 * u)} 0 0 1 ${F(hx + 0.85 * u)} ${F(hy - 0.1 * u)}`, { fill: 'none', stroke: RIMC, strokeWidth: 0.13 * u, strokeLinecap: 'round', opacity: 0.75, transform: `rotate(${F(tilt)} ${F(hx)} ${F(hy + u)})` });
  }
  return g(s, { filter: 'url(#wobbleSoft)' });
}
// our balcony's glass railing, right behind the two of them
function railing(y) {
  let s = rect(0, y, W, 92, { fill: '#7FC4C0', opacity: 0.16 });
  for (let x = 40; x < W; x += 240) s += line(x, y, x, y + 92, { stroke: '#9FC9C4', strokeWidth: 6, opacity: 0.55 });
  s += path(`M0 ${y + 30} L${W} ${y + 6}`, { stroke: '#FFFFFF', strokeWidth: 8, opacity: 0.12 });
  s += rect(0, y + 92, W, 26, { fill: '#7E9894', ...ink(5) }) + line(0, y + 118, W, y + 118, { stroke: '#0B1A1E', strokeWidth: 6 });
  s += line(0, y, W, y, { stroke: INK, strokeWidth: 22, strokeLinecap: 'round' }) + line(0, y - 2, W, y - 2, { stroke: '#C9DCD8', strokeWidth: 11 }) + line(0, y - 6, W, y - 6, { stroke: '#FFFFFF', strokeWidth: 3, opacity: 0.8 });
  return s;
}

// ---------- the hero's thumbnail head (pro.js head(), adapted: a frozen 'tense' face) ----------
function heroHead(cx, cy, u, { look = 0.6, rim, id = 'h' }) {
  let s = circle(cx, cy, u, { fill: PAL.skin });
  if (rim) s += `<mask id="rim_${id}"><circle cx="${F(cx)}" cy="${F(cy)}" r="${F(u)}" fill="#fff"/><circle cx="${F(cx - rim.side * 0.16 * u)}" cy="${F(cy + 0.06 * u)}" r="${F(u)}" fill="#000"/></mask>`
    + circle(cx, cy, u, { fill: rim.color, opacity: rim.op ?? 0.85, mask: `url(#rim_${id})` });
  s += path(`M${F(cx - u + 0.02 * u)} ${F(cy - 0.05 * u)} C${F(cx - u - 0.02 * u)} ${F(cy - 1.1 * u)} ${F(cx + 1.1 * u)} ${F(cy - 1.25 * u)} ${F(cx + 0.98 * u)} ${F(cy - 0.12 * u)} L${F(cx + 0.7 * u)} ${F(cy - 0.42 * u)} L${F(cx + 0.48 * u)} ${F(cy - 0.3 * u)} L${F(cx + 0.18 * u)} ${F(cy - 0.5 * u)} L${F(cx - 0.12 * u)} ${F(cy - 0.36 * u)} L${F(cx - 0.45 * u)} ${F(cy - 0.52 * u)} L${F(cx - 0.72 * u)} ${F(cy - 0.32 * u)} Z`, { fill: PAL.hair, ...ink(0.04 * u) });
  if (rim) s += path(`M${F(cx + rim.side * 0.62 * u)} ${F(cy - 0.78 * u)} Q${F(cx + rim.side * 0.95 * u)} ${F(cy - 0.5 * u)} ${F(cx + rim.side * 0.98 * u)} ${F(cy - 0.12 * u)}`, { fill: 'none', stroke: rim.color, strokeWidth: 0.06 * u, strokeLinecap: 'round', opacity: 0.7 });
  const lick = `M${F(cx + 0.05 * u)} ${F(cy - 0.98 * u)} q${F(0.1 * u)} ${F(-0.35 * u)} ${F(0.38 * u)} ${F(-0.3 * u)}`;
  s += path(lick, { fill: 'none', stroke: INK, strokeWidth: 0.19 * u, strokeLinecap: 'round' }) + path(lick, { fill: 'none', stroke: PAL.hair, strokeWidth: 0.11 * u, strokeLinecap: 'round' });
  // eyes turned hard to one side, heavy flat lids: frozen, listening
  const ex = cx + look * 0.26 * u, ey = cy + 0.04 * u, sp = 0.5 * u;
  for (const side of [-1, 1]) {
    const x0 = ex + side * sp / 2;
    s += ellipse(x0, ey, 0.13 * u, 0.19 * u, { fill: INK });
    s += circle(x0 + 0.05 * u, ey - 0.06 * u, 0.05 * u, { fill: '#FFFFFF' });
    const lid = ey - 0.19 * u + 0.3 * 0.38 * u, xo = x0 + side * 0.17 * u, xi = x0 - side * 0.17 * u;
    s += poly([[xo, ey - 0.26 * u], [xi, ey - 0.26 * u], [xi, lid + 0.01 * u], [xo, lid - 0.01 * u]], { fill: PAL.skin }) + line(xo, lid - 0.01 * u, xi, lid + 0.01 * u, ink(0.05 * u));
    const by = ey - 0.34 * u;
    s += line(x0 + side * 0.15 * u, by - 0.02 * u, x0 - side * 0.13 * u, by + 0.04 * u, ink(0.06 * u));
  }
  const mx = ex + look * 0.04 * u, my = cy + 0.5 * u;
  s += path(`M${F(mx - 0.12 * u)} ${F(my + 0.02 * u)} L${F(mx + 0.12 * u)} ${F(my + 0.02 * u)}`, { fill: 'none', ...ink(0.055 * u) });
  s += circle(cx, cy, u, { fill: 'none', ...ink(0.045 * u) });
  return s;
}
function heroActor({ x, y, s: sc, look, rim, id }) {
  const u = 60 * sc;
  const base = hero({ x, y, s: sc, pose: 'stand', expr: 'neutral', look, filter: false });
  return g(g(base + heroHead(x, y - 5.25 * u, u, { look, rim, id }), { filter: 'url(#wobbleSoft)' }), { filter: 'url(#pro_stk)' });
}

// ---------- Nora, thumbnail grade: same head build as pro.js actor(), her hair, freckles, serious ----------
function noraHead(cx, cy, u, { look = -0.35, rim, id = 'n' }) {
  let s = circle(cx, cy, u, { fill: NORA.skin });
  if (rim) s += `<mask id="rim_${id}"><circle cx="${F(cx)}" cy="${F(cy)}" r="${F(u)}" fill="#fff"/><circle cx="${F(cx - rim.side * 0.16 * u)}" cy="${F(cy + 0.06 * u)}" r="${F(u)}" fill="#000"/></mask>`
    + circle(cx, cy, u, { fill: rim.color, opacity: rim.op ?? 0.8, mask: `url(#rim_${id})` });
  // hair: centre part, side-swept bangs, a darker strand
  s += path(`M${F(cx - 1.0 * u)} ${F(cy + 0.15 * u)} C${F(cx - 1.08 * u)} ${F(cy - 1.15 * u)} ${F(cx + 1.08 * u)} ${F(cy - 1.2 * u)} ${F(cx + 1.0 * u)} ${F(cy + 0.15 * u)} L${F(cx + 0.82 * u)} ${F(cy - 0.2 * u)} C${F(cx + 0.55 * u)} ${F(cy - 0.45 * u)} ${F(cx + 0.2 * u)} ${F(cy - 0.62 * u)} ${F(cx + 0.02 * u)} ${F(cy - 0.78 * u)} C${F(cx - 0.25 * u)} ${F(cy - 0.5 * u)} ${F(cx - 0.6 * u)} ${F(cy - 0.42 * u)} ${F(cx - 0.84 * u)} ${F(cy - 0.18 * u)} Z`, { fill: NORA.hair, ...ink(0.04 * u) });
  s += path(`M${F(cx + 0.02 * u)} ${F(cy - 0.95 * u)} q${F(-0.05 * u)} ${F(0.1 * u)} 0 ${F(0.17 * u)}`, { fill: 'none', stroke: NORA.hairDark, strokeWidth: 0.04 * u, strokeLinecap: 'round' });
  s += path(`M${F(cx - 0.5 * u)} ${F(cy - 0.72 * u)} q${F(-0.25 * u)} ${F(0.2 * u)} ${F(-0.36 * u)} ${F(0.5 * u)} M${F(cx + 0.45 * u)} ${F(cy - 0.75 * u)} q${F(0.25 * u)} ${F(0.2 * u)} ${F(0.38 * u)} ${F(0.5 * u)}`, { fill: 'none', stroke: NORA.hairDark, strokeWidth: 0.035 * u, strokeLinecap: 'round', opacity: 0.8 });
  if (rim) s += path(`M${F(cx + rim.side * 0.6 * u)} ${F(cy - 0.82 * u)} Q${F(cx + rim.side * 0.98 * u)} ${F(cy - 0.5 * u)} ${F(cx + rim.side * 1.0 * u)} ${F(cy + 0.05 * u)}`, { fill: 'none', stroke: '#F2B79E', strokeWidth: 0.06 * u, strokeLinecap: 'round', opacity: 0.8 });
  // eyes: serious, lids slanting down to the nose, a lash flick at the outer corner
  const ex = cx + look * 0.26 * u, ey = cy + 0.06 * u, sp = 0.48 * u;
  for (const side of [-1, 1]) {
    const x0 = ex + side * sp / 2;
    s += ellipse(x0, ey, 0.12 * u, 0.18 * u, { fill: INK });
    s += circle(x0 + 0.045 * u, ey - 0.05 * u, 0.045 * u, { fill: '#FFFFFF' });
    const base = ey - 0.18 * u + 0.36 * 0.36 * u, tilt = 0.04 * u, yo = base - tilt, yi = base + tilt, xo = x0 + side * 0.16 * u, xi = x0 - side * 0.16 * u;
    s += poly([[xo, ey - 0.25 * u], [xi, ey - 0.25 * u], [xi, yi], [xo, yo]], { fill: NORA.skin }) + line(xo, yo, xi, yi, ink(0.045 * u));
    s += path(`M${F(xo - side * 0.02 * u)} ${F(yo + 0.005 * u)} l${F(side * 0.08 * u)} ${F(-0.06 * u)}`, { fill: 'none', ...ink(0.035 * u) });
    const by = ey - 0.33 * u;
    s += line(x0 + side * 0.15 * u, by - 0.02 * u, x0 - side * 0.12 * u, by + 0.07 * u, { stroke: NORA.hairDark, strokeWidth: 0.07 * u, strokeLinecap: 'round' });
  }
  for (const side of [-1, 1]) for (const [dx, dy] of [[0, 0], [0.1, 0.05], [-0.07, 0.08], [0.04, 0.12]]) s += circle(ex + side * (0.36 + dx) * u, ey + (0.22 + dy) * u, 0.028 * u, { fill: NORA.freckle });
  const mx = ex + look * 0.04 * u, my = cy + 0.52 * u;
  s += path(`M${F(mx - 0.11 * u)} ${F(my + 0.01 * u)} Q${F(mx)} ${F(my - 0.02 * u)} ${F(mx + 0.11 * u)} ${F(my + 0.02 * u)}`, { fill: 'none', ...ink(0.045 * u) });
  s += circle(cx, cy, u, { fill: 'none', ...ink(0.045 * u) });
  return s;
}

// ---------- the extinguisher ----------
// cylinder in local coordinates: base centre at the origin, axis up; returns markup and a point mapper
function extinguisherBody(ox, oy, k, ang) {
  const a = (ang * Math.PI) / 180, T = (px, py) => [ox + px * Math.cos(a) - py * Math.sin(a), oy + px * Math.sin(a) + py * Math.cos(a)];
  const lw = 5.5 * k;
  let s = `<defs><linearGradient id="cd_ext" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="${EXT.lo}"/><stop offset="0.22" stop-color="${EXT.hi}"/><stop offset="0.45" stop-color="${EXT.red}"/><stop offset="1" stop-color="${EXT.lo}"/></linearGradient></defs>`;
  let b = rect(-62 * k, -330 * k, 124 * k, 340 * k, { rx: 44 * k, fill: 'url(#cd_ext)', ...ink(lw) });
  b += rect(-40 * k, -316 * k, 14 * k, 250 * k, { rx: 7 * k, fill: '#FFFFFF', opacity: 0.35 });
  // label
  b += rect(-46 * k, -232 * k, 92 * k, 116 * k, { rx: 8 * k, fill: '#F6F1E4', ...ink(3.5 * k) }) + rect(-46 * k, -232 * k, 92 * k, 26 * k, { rx: 6 * k, fill: '#1E1A1A' });
  b += text(0, -213 * k, 'FIRE', { fontFamily: "'Lilita One'", fontSize: 20 * k, fill: '#F6F1E4', textAnchor: 'middle', letterSpacing: 2 * k });
  b += text(0, -160 * k, 'CO2', { fontFamily: "'Lilita One'", fontSize: 34 * k, fill: EXT.red, textAnchor: 'middle' });
  b += path(`M${-8 * k} ${-128 * k} q${-12 * k} ${-14 * k} 0 ${-30 * k} q${2 * k} ${12 * k} ${10 * k} ${14 * k} q${8 * k} ${10 * k} ${-10 * k} ${16 * k} Z`, { fill: '#F2A73B', opacity: 0 });
  // neck, valve head, carry handle and lever, gauge, pin
  b += rect(-20 * k, -362 * k, 40 * k, 36 * k, { fill: EXT.metalHi, ...ink(lw * 0.8) });
  b += rect(-38 * k, -396 * k, 76 * k, 38 * k, { rx: 8 * k, fill: EXT.metal, ...ink(lw * 0.8) }) + line(-30 * k, -388 * k, 26 * k, -388 * k, { stroke: '#8A9099', strokeWidth: 3 * k, strokeLinecap: 'round' });
  b += path(`M${-30 * k} ${-380 * k} L${-118 * k} ${-392 * k}`, { fill: 'none', stroke: INK, strokeWidth: 22 * k, strokeLinecap: 'round' }) + path(`M${-30 * k} ${-380 * k} L${-118 * k} ${-392 * k}`, { fill: 'none', stroke: EXT.metal, strokeWidth: 12 * k, strokeLinecap: 'round' });
  b += path(`M${-26 * k} ${-398 * k} L${-110 * k} ${-430 * k}`, { fill: 'none', stroke: INK, strokeWidth: 22 * k, strokeLinecap: 'round' }) + path(`M${-26 * k} ${-398 * k} L${-110 * k} ${-430 * k}`, { fill: 'none', stroke: EXT.metal, strokeWidth: 12 * k, strokeLinecap: 'round' });
  b += circle(44 * k, -372 * k, 18 * k, { fill: '#F6F1E4', ...ink(3.5 * k) }) + path(`M${32 * k} ${-372 * k} A${12 * k} ${12 * k} 0 0 1 ${50 * k} ${-382 * k}`, { fill: 'none', stroke: '#3DBE6A', strokeWidth: 4 * k }) + line(44 * k, -372 * k, 52 * k, -382 * k, { stroke: INK, strokeWidth: 3 * k, strokeLinecap: 'round' });
  b += circle(-46 * k, -366 * k, 11 * k, { fill: 'none', stroke: '#F2C230', strokeWidth: 4.5 * k });
  s += g(b, { transform: `translate(${F(ox)} ${F(oy)}) rotate(${F(ang)})` });
  return { s, T };
}
// the black horn on its hose: mouth centre (mx, my), pointing along angle `dir` (deg, direction the mouth faces)
function horn(mx, my, dir, len, mouth) {
  const a = (dir * Math.PI) / 180, d = [Math.cos(a), Math.sin(a)], n = [-d[1], d[0]];
  const bx = mx - d[0] * len, by = my - d[1] * len, nw = mouth * 0.24;
  const P = [[bx + n[0] * nw, by + n[1] * nw], [mx + n[0] * mouth / 2, my + n[1] * mouth / 2], [mx - n[0] * mouth / 2, my - n[1] * mouth / 2], [bx - n[0] * nw, by - n[1] * nw]];
  let s = poly(P, { fill: '#26282C', ...ink(6) });
  s += line(bx + n[0] * nw * 0.4, by + n[1] * nw * 0.4, mx + n[0] * mouth * 0.32, my + n[1] * mouth * 0.32, { stroke: '#6A707A', strokeWidth: 5, strokeLinecap: 'round', opacity: 0.9 });
  s += ellipse(mx, my, mouth * 0.16, mouth / 2, { fill: '#121315', ...ink(5), transform: `rotate(${F(dir)} ${F(mx)} ${F(my)})` });
  return { s, base: [bx, by] };
}
const hose = (x1, y1, cx, cy, x2, y2) => path(`M${F(x1)} ${F(y1)} Q${F(cx)} ${F(cy)} ${F(x2)} ${F(y2)}`, { fill: 'none', stroke: INK, strokeWidth: 30, strokeLinecap: 'round' })
  + path(`M${F(x1)} ${F(y1)} Q${F(cx)} ${F(cy)} ${F(x2)} ${F(y2)}`, { fill: 'none', stroke: '#2E3034', strokeWidth: 18, strokeLinecap: 'round' })
  + path(`M${F(x1)} ${F(y1)} Q${F(cx)} ${F(cy)} ${F(x2)} ${F(y2)}`, { fill: 'none', stroke: '#6A707A', strokeWidth: 4, strokeLinecap: 'round', opacity: 0.7, transform: 'translate(0 -5)' });

// Nora behind him: hair, hoodie, arms; the extinguisher in her arms, the horn to his neck
function noraWithExtinguisher({ x, y, s: sc, neck }) {
  const u = 60 * sc * 0.93, cx = x, cy = y - 5.25 * u;
  const shY = y - 4.05 * u, hipY = y - 2.2 * u, neckY = y - 4.25 * u, lw = Math.max(4, 0.1 * u);
  let s = '';
  // long hair behind the shoulders
  s += path(`M${F(cx - 1.02 * u)} ${F(cy - 0.1 * u)} C${F(cx - 1.28 * u)} ${F(cy + 0.9 * u)} ${F(cx - 1.08 * u)} ${F(cy + 1.8 * u)} ${F(cx - 0.6 * u)} ${F(cy + 2.0 * u)} L${F(cx + 0.6 * u)} ${F(cy + 2.0 * u)} C${F(cx + 1.08 * u)} ${F(cy + 1.8 * u)} ${F(cx + 1.28 * u)} ${F(cy + 0.9 * u)} ${F(cx + 1.02 * u)} ${F(cy - 0.1 * u)} Z`, { fill: NORA.hair, ...ink(0.04 * u) });
  // torso in the teal hoodie, pocket seam
  const tw = 0.62 * u, bw = 0.56 * u, top = shY - 0.15 * u, bot = hipY + 0.1 * u;
  s += path(`M${F(x - tw)} ${F(top + 0.2 * u)} Q${F(x - tw)} ${F(top)} ${F(x - tw + 0.25 * u)} ${F(top)} L${F(x + tw - 0.25 * u)} ${F(top)} Q${F(x + tw)} ${F(top)} ${F(x + tw)} ${F(top + 0.2 * u)} L${F(x + bw)} ${F(bot)} L${F(x - bw)} ${F(bot)} Z`, { fill: NORA.hoodie, ...ink(0.04 * u) });
  s += path(`M${F(x - 0.4 * u)} ${F(bot - 0.6 * u)} Q${F(x)} ${F(bot - 0.75 * u)} ${F(x + 0.4 * u)} ${F(bot - 0.6 * u)}`, { fill: 'none', stroke: NORA.hoodieDark, strokeWidth: 0.04 * u });
  // the hood bunched behind the neck, drawstrings
  s += path(`M${F(x - 0.62 * u)} ${F(neckY + 0.05 * u)} Q${F(x)} ${F(neckY - 0.35 * u)} ${F(x + 0.62 * u)} ${F(neckY + 0.05 * u)} Q${F(x)} ${F(neckY + 0.45 * u)} ${F(x - 0.62 * u)} ${F(neckY + 0.05 * u)} Z`, { fill: NORA.hoodieDark, ...ink(0.035 * u) });
  s += line(x - 0.16 * u, neckY + 0.2 * u, x - 0.2 * u, neckY + 0.8 * u, { stroke: '#E8E1D2', strokeWidth: 0.05 * u, strokeLinecap: 'round' }) + line(x + 0.16 * u, neckY + 0.2 * u, x + 0.22 * u, neckY + 0.74 * u, { stroke: '#E8E1D2', strokeWidth: 0.05 * u, strokeLinecap: 'round' });
  s += noraHead(cx, cy, u, { look: -0.45, rim: { color: '#DDF7F2', side: 1, op: 0.55 }, id: 'nora' });
  // the extinguisher, held upright against her chest, leaning toward him
  const E = extinguisherBody(x + 0.52 * u, y - 1.6 * u, 0.98 * (u / 140), -14);
  // horn: mouth hidden behind his neck, pointing left and a touch down
  const Hn = horn(neck[0], neck[1], 186, 0.95 * u, 0.5 * u);
  const valve = E.T(10 * (u / 140), -380 * (u / 140));
  // hose from the valve, looping up to the horn
  const hs = hose(valve[0], valve[1], valve[0] - 0.2 * u, valve[1] - 0.9 * u, Hn.base[0] + 0.02 * u, Hn.base[1]);
  // arms: her right hand on the horn, left hand holding the cylinder
  const shR = [x - 0.5 * u, shY + 0.05 * u], shL = [x + 0.5 * u, shY + 0.05 * u];
  const hR = [Hn.base[0] + 0.05 * u, Hn.base[1] + 0.02 * u], hL = E.T(70 * (u / 140), -150 * (u / 140));
  const armR = path(`M${F(shR[0])} ${F(shR[1])} Q${F(shR[0] - 0.1 * u)} ${F(shR[1] + 0.6 * u)} ${F(hR[0])} ${F(hR[1])}`, { fill: 'none', ...ink(lw) });
  const armL = path(`M${F(shL[0])} ${F(shL[1])} Q${F(shL[0] + 0.45 * u)} ${F(shL[1] + 0.6 * u)} ${F(hL[0])} ${F(hL[1])}`, { fill: 'none', ...ink(lw) });
  s += armL + E.s + hs + armR + Hn.s;
  s += circle(hR[0], hR[1], 0.17 * u, { fill: NORA.skin, ...ink(0.035 * u) }) + circle(hL[0], hL[1], 0.17 * u, { fill: NORA.skin, ...ink(0.035 * u) });
  return g(g(s, { filter: 'url(#wobbleSoft)' }), { filter: 'url(#pro_stk)' });
}

function thumb() {
  let s = `<defs><filter id="cd_bgb" ${FR}><feGaussianBlur stdDeviation="2.4"/></filter><filter id="cd_zb" ${FR}><feGaussianBlur stdDeviation="0.9"/></filter></defs>`;
  // background: roof, far balconies, ground floor, softened
  let bg = roof() + farWall() + groundFloor(1480, 975);
  s += g(bg, { filter: 'url(#cd_bgb)' });
  // the one light: cold storm daylight through the glass roof, falling on the fountain
  s += soft(1500, 150, 760, 300, LIGHT, 0.55);
  s += `<defs><linearGradient id="cd_shaft" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${LIGHT}" stop-opacity="0.28"/><stop offset="1" stop-color="${LIGHT}" stop-opacity="0.06"/></linearGradient><filter id="cd_shb" ${FR}><feGaussianBlur stdDeviation="30"/></filter></defs>`;
  s += poly([[1260, 300], [1760, 300], [1980, 1080], [1040, 1080]], { fill: 'url(#cd_shaft)', filter: 'url(#cd_shb)', style: 'mix-blend-mode:screen' });
  s += soft(1480, 960, 620, 200, LIGHT, 0.35);
  // the dry fountain and the dead around it
  const FX0 = 1480, FY0 = 975;
  s += g(fountain(FX0, FY0, 1.0), { filter: 'url(#wobbleSoft)' });
  const dead = [
    [1240, 915, 0.62, 'shopper', -8, 0.4, '#E9B93E'], [1390, 900, 0.58, 'guard', 6, 0.5], [1560, 898, 0.58, 'cashier', -6, 0.3], [1720, 912, 0.62, 'nurse', 8, 0.5],
    [1150, 1000, 0.74, 'jogger', 10, 0.5], [1820, 1000, 0.74, 'pretzel', -8, 0.6],
    [1300, 1100, 0.86, 'park', -6, 0.5, '#D65632'], [1500, 1110, 0.88, 'shopper', 8, 0.6, '#6FA3A6'], [1700, 1095, 0.86, 'suit', -10, 0.4],
    [1900, 1080, 0.82, 'janitor', 6, 0.5],
    // the ring continues to the left of the two of you
    [80, 1000, 0.76, 'nurse', 8, 0.5], [250, 930, 0.62, 'jogger', -6, 0.4], [160, 1110, 0.88, 'shopper', -8, 0.6, '#C76A83'], [360, 1060, 0.8, 'guard', 6, 0.5],
  ];
  s += theDead(dead);
  // our railing, right behind the two of you
  s += railing(640);
  // Nora over his shoulder, then the hero in front
  const sc = 2.9, hx = 600, u = 60 * sc, gy = 600 + 5.25 * u;
  const neck = [hx + 0.72 * u, gy - 4.36 * u];
  s += soft(820, 560, 520, 420, '#7FD6CC', 0.22);
  s += noraWithExtinguisher({ x: 950, y: 560 + 5.25 * 60 * 2.7 * 0.93, s: 2.7, neck });
  s += heroActor({ x: hx, y: gy, s: sc, look: 0.62, rim: { color: '#D6F7F1', side: 1, op: 0.7 }, id: 'cdh' });
  s += headline(60, 215, "DON'T MOVE", { size: 190, anchor: 'start', rich: `DON'T <tspan fill="url(#pro_red)">MOVE</tspan>` });
  s += finish({ vignette: 0.5, grain: 0.05 });
  return { w: W, h: H, svg: svgOf(s, 9), css: 'saturate(1.12) contrast(1.06)' };
}

export default () => thumb();
