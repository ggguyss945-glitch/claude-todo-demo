// Static environments for episode 2: the staff restroom, the stockroom doors, Brookfield Mall inside and out,
// the Bright Tech store. Plain markup with the line wobble baked in; shots wrap them in set(key, ...).
import { W, H, INK, PAL, g, rect, circle, ellipse, line, poly, path, text, ink, rng } from '../../lib.js';
import { label } from '../kit.js';

const wob = (s) => g(s, { filter: 'url(#wobble)' });
const tiles = (x0, y0, x1, y1, step, fill, grout) => {
  let s = rect(x0, y0, x1 - x0, y1 - y0, { fill });
  for (let x = x0; x <= x1; x += step) s += line(x, y0, x, y1, { stroke: grout, strokeWidth: 2.5 });
  for (let y = y0; y <= y1; y += step) s += line(x0, y, x1, y, { stroke: grout, strokeWidth: 2.5 });
  return s;
};
const pipe = (d, w = 26, fill = '#9AA3A8') => path(d, { fill: 'none', stroke: INK, strokeWidth: w + 10, strokeLinecap: 'round', strokeLinejoin: 'round' })
  + path(d, { fill: 'none', stroke: fill, strokeWidth: w, strokeLinecap: 'round', strokeLinejoin: 'round' })
  + path(d, { fill: 'none', stroke: '#FFFFFF', strokeWidth: w * 0.18, strokeLinecap: 'round', strokeLinejoin: 'round', opacity: 0.35, transform: `translate(0 ${-w * 0.22})` });

// ---------- staff restroom ----------
export function restroom() {
  let s = rect(0, 0, W, H, { fill: '#E2DED0' });
  s += tiles(0, 300, W, 800, 64, '#CFD8CF', '#B3BFB4') + rect(0, 290, W, 16, { fill: '#9DAE9F', ...ink(4) });
  s += rect(0, 800, W, 280, { fill: '#9EA69F' });
  for (let i = 0; i < 16; i++) s += line(i * 140 - 300, H, i * 120 - 40, 800, { stroke: '#8C948D', strokeWidth: 3 });
  for (const y of [860, 940, 1030]) s += line(0, y, W, y, { stroke: '#8C948D', strokeWidth: 3 });
  s += line(0, 800, W, 800, ink(5));
  // pipes along the top of the wall, dropping to the sink and into the stall
  s += pipe('M-20 130 H1560 V300') + pipe('M520 130 V420', 18) + pipe('M1240 130 V260', 18, '#B5703F');
  for (const x of [260, 760, 1100, 1420]) s += rect(x - 14, 110, 28, 40, { fill: '#6E767B', ...ink(3) });
  // mirror, sink, towels
  s += rect(330, 260, 380, 290, { rx: 10, fill: '#9FB8C4', ...ink(6) }) + path('M380 520 L520 300 M440 530 L600 290', { stroke: '#D9E8EE', strokeWidth: 10, opacity: 0.6 });
  s += path('M300 560 H740 L715 640 H325 Z', { fill: '#F4F2EC', ...ink(6) }) + ellipse(520, 585, 150, 22, { fill: '#D9DCD6', ...ink(4) });
  s += rect(470, 640, 100, 160, { fill: '#E6E3DA', ...ink(5) });
  s += path('M500 560 V520 H560 V532', { fill: 'none', stroke: INK, strokeWidth: 16, strokeLinecap: 'round' }) + path('M500 560 V520 H560 V532', { fill: 'none', stroke: '#C9CDD0', strokeWidth: 9, strokeLinecap: 'round' });
  s += rect(790, 300, 150, 190, { rx: 12, fill: '#F2F0EA', ...ink(5) }) + rect(830, 470, 70, 26, { fill: '#E8E1D2', ...ink(3) });
  s += rect(800, 560, 170, 90, { rx: 8, fill: '#FBF6EA', ...ink(4) }) + label(885, 598, 'EMPLOYEES', 15, INK) + label(885, 622, 'MUST WASH', 15, INK) + label(885, 640, 'HANDS', 13, PAL.red);
  // stall
  s += rect(1080, 200, 560, 640, { fill: '#7E9AA8', ...ink(6) }) + rect(1120, 240, 480, 600, { fill: '#8FAAB7', ...ink(5) });
  s += rect(1540, 480, 30, 60, { rx: 6, fill: '#C9CDD0', ...ink(3) }) + rect(1546, 492, 18, 14, { fill: '#3DBE6A' });
  // utility closet
  s += rect(1700, 230, 220, 570, { fill: '#B58759', ...ink(6) }) + rect(1730, 260, 160, 60, { rx: 6, fill: '#FBF6EA', ...ink(4) }) + label(1810, 300, 'UTILITY', 22, INK);
  s += circle(1730, 540, 14, { fill: '#C9C3B5', ...ink(4) });
  // a ceiling light panel
  s += rect(760, 20, 400, 60, { rx: 8, fill: '#F6F1DE', ...ink(4) });
  return wob(s);
}
export function faucetClose() {
  let s = tiles(0, 0, W, 760, 150, '#CFD8CF', '#B3BFB4');
  s += path('M-40 700 H1960 V1100 H-40 Z', { fill: '#F4F2EC', ...ink(7) }) + ellipse(960, 820, 760, 150, { fill: '#D9DCD6', ...ink(6) }) + ellipse(960, 830, 120, 40, { fill: '#8E9499', ...ink(5) }) + ellipse(960, 830, 60, 18, { fill: '#2B2F33' });
  // faucet: a gooseneck from the left, cross handle
  s += rect(560, 560, 130, 160, { rx: 20, fill: '#C9CDD0', ...ink(7) }) + path('M625 570 V420 Q625 330 760 330 H860 Q930 330 930 400 V470', { fill: 'none', stroke: INK, strokeWidth: 74, strokeLinecap: 'round' })
    + path('M625 570 V420 Q625 330 760 330 H860 Q930 330 930 400 V470', { fill: 'none', stroke: '#C9CDD0', strokeWidth: 58, strokeLinecap: 'round' })
    + path('M640 560 V430 Q640 350 760 350', { fill: 'none', stroke: '#F2F4F5', strokeWidth: 12, strokeLinecap: 'round', opacity: 0.8 });
  s += rect(900, 460, 60, 40, { rx: 8, fill: '#9AA3A8', ...ink(5) });
  s += rect(400, 600, 120, 36, { rx: 14, fill: '#C9CDD0', ...ink(5) }) + rect(440, 560, 40, 110, { rx: 14, fill: '#C9CDD0', ...ink(5) }) + circle(460, 618, 16, { fill: PAL.blue, ...ink(3) });
  return wob(s);
}
export function heaterCloset() {
  let s = rect(0, 0, W, H, { fill: '#8E8676' }) + rect(0, 0, W, H, { fill: '#A39A88', opacity: 0.6 });
  for (let x = 0; x < W; x += 210) s += line(x, 0, x, 900, { stroke: '#857D6E', strokeWidth: 3 });
  s += rect(0, 900, W, 180, { fill: '#6E685E' }) + line(0, 900, W, 900, ink(5));
  // pipes into the top of the tank: cold (blue band) and hot (red band)
  s += pipe('M860 -20 V210', 30, '#B5703F') + pipe('M1060 -20 V210', 30, '#B5703F');
  s += rect(842, 120, 36, 22, { fill: PAL.blue, ...ink(3) }) + rect(1042, 120, 36, 22, { fill: PAL.red, ...ink(3) });
  // the tank
  s += rect(760, 200, 400, 700, { rx: 40, fill: '#E9E5DA', ...ink(7) }) + ellipse(960, 210, 200, 40, { fill: '#F3F0E8', ...ink(6) });
  s += rect(790, 240, 40, 640, { fill: '#FFFFFF', opacity: 0.45 }) + rect(1090, 240, 40, 640, { fill: '#C9C3B5', opacity: 0.5 });
  s += rect(840, 360, 240, 190, { rx: 10, fill: '#FBF6EA', ...ink(4) }) + rect(840, 360, 240, 46, { rx: 10, fill: PAL.blue, ...ink(4) });
  s += label(960, 393, 'AQUA-TEMP', 26, '#FFFFFF') + label(960, 470, '20 GAL', 54, INK) + label(960, 520, '75.7 L · GAS', 18, '#6B5F55');
  // relief valve with its pipe down the side, drain valve at the bottom
  s += rect(1160, 330, 50, 40, { rx: 6, fill: '#C9A43A', ...ink(4) }) + pipe('M1200 370 V860', 14, '#B5703F');
  s += rect(930, 830, 60, 40, { rx: 6, fill: '#C9A43A', ...ink(4) }) + circle(960, 850, 14, { fill: PAL.red, ...ink(3) });
  s += rect(860, 900, 200, 30, { fill: '#5E584E', ...ink(4) });
  return wob(s);
}
export function drainClose() {
  let s = rect(0, 0, W, H, { fill: '#6E685E' });
  s += path('M-40 -40 H1960 V640 Q960 760 -40 640 Z', { fill: '#E9E5DA', ...ink(8) }) + path('M-40 560 Q960 690 1960 560', { fill: 'none', stroke: '#C9C3B5', strokeWidth: 14 });
  s += rect(860, 520, 200, 120, { rx: 14, fill: '#C9A43A', ...ink(7) }) + rect(910, 630, 100, 90, { rx: 10, fill: '#B8932E', ...ink(6) });
  // bucket under the valve
  s += path('M700 820 L760 1100 H1160 L1220 820 Z', { fill: '#E07A3A', ...ink(7) }) + ellipse(960, 820, 262, 46, { fill: '#B5652F', ...ink(6) }) + path('M720 860 Q960 900 1200 860', { fill: 'none', stroke: '#C76A3A', strokeWidth: 8 });
  return wob(s);
}
export function toiletClose() {
  let s = tiles(0, 0, W, 900, 160, '#CFD8CF', '#B3BFB4') + rect(0, 900, W, 180, { fill: '#9EA69F' }) + line(0, 900, W, 900, ink(5));
  s += pipe('M1500 -20 V420 H1300', 20);
  s += rect(660, 260, 600, 330, { rx: 26, fill: '#F4F2EC', ...ink(7) }) + rect(700, 300, 60, 34, { rx: 8, fill: '#C9CDD0', ...ink(4) });
  s += path('M760 590 H1160 Q1180 760 1060 820 L1020 1000 H900 L860 820 Q740 760 760 590 Z', { fill: '#F4F2EC', ...ink(7) }) + ellipse(960, 640, 230, 50, { fill: '#E6E3DA', ...ink(5) });
  return wob(s);
}
export function pipesWall() {
  let s = rect(0, 0, W, H, { fill: '#B8B3A5' });
  for (let y = 0; y < H; y += 54) for (let x = (y / 54) % 2 ? -60 : 0; x < W; x += 120) s += rect(x, y, 120, 54, { fill: 'none', stroke: '#9E998C', strokeWidth: 3 });
  s += pipe('M-40 300 H1960', 54) + pipe('M-40 520 H1300 Q1360 520 1360 580 V1120', 44, '#B5703F') + pipe('M-40 760 H1960', 34);
  for (const x of [240, 760, 1280, 1720]) for (const y of [300, 760]) s += rect(x - 22, y - 42, 44, 84, { rx: 6, fill: '#6E767B', ...ink(4) });
  return wob(s);
}

// ---------- the stockroom doors from the sales floor ----------
export function stockDoors() {
  const r = rng(52);
  let s = rect(0, 0, W, H, { fill: '#C8C2AE' }) + rect(0, 860, W, 220, { fill: '#D9CDB2' }) + line(0, 860, W, 860, ink(5));
  for (let x = -100; x < W + 200; x += 160) s += line(x, 860, x - 240, H, { stroke: '#BDB096', strokeWidth: 3 });
  s += line(0, 960, W, 960, { stroke: '#BDB096', strokeWidth: 3 });
  // shelf ends either side
  for (const x0 of [0, 1500]) {
    s += rect(x0, 160, 420, 700, { fill: '#B7AF9B', ...ink(5) });
    for (const y of [330, 510, 690, 860]) {
      let x = x0 + 16;
      while (x < x0 + 400) { const w = 50 + r() * 40, h = 70 + r() * 60; s += rect(x, y - h, Math.min(w, x0 + 404 - x), h, { fill: ['#C44A3A', '#E9B93E', '#3E6E9A', '#6F8F4E', '#E07A3A', '#F3EEDF'][Math.floor(r() * 6)], ...ink(2.5) }); x += w + 4; }
      s += rect(x0, y, 420, 18, { fill: '#8E877A', ...ink(3) });
    }
  }
  // the door frame and two swing doors with round windows
  s += rect(560, 170, 800, 700, { fill: '#6E747A', ...ink(7) });
  for (const [dx, side] of [[600, -1], [962, 1]]) {
    s += rect(dx, 210, 358, 650, { rx: 6, fill: '#7E9AA8', ...ink(6) });
    s += rect(dx, 700, 358, 160, { fill: '#9AA3A8', ...ink(5) });
    s += circle(dx + 179, 380, 78, { fill: '#2B323A', ...ink(7) }) + circle(dx + 179, 380, 62, { fill: '#3A4552', ...ink(3) });
    s += rect(dx + (side < 0 ? 290 : 28), 520, 40, 120, { rx: 10, fill: '#C9CDD0', ...ink(4) });
  }
  s += rect(700, 70, 520, 90, { rx: 10, fill: '#FBF6EA', ...ink(5) }) + label(960, 116, 'STOCKROOM', 44, INK, 'middle', 8) + label(960, 148, 'EMPLOYEES ONLY', 18, PAL.red, 'middle', 6);
  return wob(s);
}

// ---------- Brookfield Mall: the atrium across four floors ----------
const SHOPS = [
  ['BRIGHT TECH', '#3E6E9A', true], ['SPORTS HUB', '#6F8F4E', false], ['PHOTO PLUS', '#8E5B4A', false], ['GAME ZONE', '#7C6A8E', false],
  ['CINEMA 6', '#A0453A', false], ['STYLE CO', '#C76A83', false], ['BOOK NOOK', '#B58759', false], ['TOY TOWN', '#E9B93E', false],
  ['KIDS WORLD', '#6FA3A6', false], ['NAIL BAR', '#C76A83', false], ['SHOE ZONE', '#3B3F48', false], ['CAFE 22', '#7A5C40', false],
  ['PRETZEL PALACE', '#C4473A', false], ['FOOD COURT', '#E07A3A', false], ['GIFTS', '#7C6A8E', false], ['PHARMACY', '#3E6E5A', false],
];
export function atrium() {
  let s = rect(0, 0, W, H, { fill: '#55606E' });
  // glass roof: a band of panes across the top
  s += rect(0, 0, W, 150, { fill: '#2E3A4E', ...ink(6) });
  for (let x = 0; x <= W; x += 120) s += line(x, 0, x + (x - W / 2) * 0.08, 150, { stroke: '#1E2433', strokeWidth: 8 });
  s += line(0, 75, W, 75, { stroke: '#1E2433', strokeWidth: 6 });
  // four floors of shops; each tier: storefronts, then the balcony slab with a glass railing in front
  const tiers = [[160, 300], [330, 470], [500, 640], [670, 860]];
  tiers.forEach(([y0, y1], fl) => {
    s += rect(0, y0, W, y1 - y0, { fill: '#7E8794' });
    for (let i = 0; i < 4; i++) {
      const [name, col] = SHOPS[fl * 4 + i], x = 60 + i * 470, w = 420, top = y0 + 14, h = y1 - y0 - 30;
      s += rect(x, top, w, h, { fill: '#2A303A', ...ink(4) }) + rect(x, top, w, 36, { fill: col, ...ink(4) });
      s += text(x + w / 2, top + 26, name, { fontFamily: 'Rubik', fontWeight: 900, fontSize: 22, fill: '#F7F2E6', textAnchor: 'middle', letterSpacing: 3 });
      if ((fl + i) % 3 !== 1) for (let y = top + 44; y < top + h; y += 14) s += line(x + 6, y, x + w - 6, y, { stroke: '#4A525E', strokeWidth: 4 });   // shutter down
      else s += rect(x + 20, top + 50, w - 40, h - 60, { fill: '#3A4250', opacity: 0.9 });
    }
    if (fl < 3) {
      s += rect(0, y1 - 16, W, 26, { fill: '#C9C3B5', ...ink(4) });
      s += rect(0, y1 - 64, W, 48, { fill: '#9FB8C4', opacity: 0.22 }) + line(0, y1 - 64, W, y1 - 64, { stroke: '#C9CDD0', strokeWidth: 8 });
      for (let x = 0; x < W; x += 160) s += line(x, y1 - 64, x, y1 - 16, { stroke: '#8E9499', strokeWidth: 4 });
    }
  });
  // the stopped escalator up the left side
  s += poly([[120, 860], [520, 640], [600, 640], [220, 860]], { fill: '#8E9499', ...ink(5) }) + path('M120 860 L520 640', { stroke: INK, strokeWidth: 12 }) + path('M220 860 L600 640', { stroke: INK, strokeWidth: 12 });
  for (let k = 0.08; k < 1; k += 0.08) s += line(120 + 400 * k, 860 - 220 * k, 220 + 380 * k, 860 - 220 * k, { stroke: '#6E767B', strokeWidth: 4 });
  // ground floor: tiles and the dry fountain
  s += rect(0, 860, W, 220, { fill: '#B8AE9A' }) + line(0, 860, W, 860, ink(5));
  for (let x = -200; x < W + 400; x += 180) s += line(x, 860, x + (x - W / 2) * 0.5, H, { stroke: '#A69C88', strokeWidth: 3 });
  s += ellipse(960, 975, 430, 92, { fill: '#9C968A', ...ink(7) }) + ellipse(960, 962, 380, 72, { fill: '#6E685E', ...ink(5) });
  s += rect(930, 860, 60, 110, { fill: '#C9C3B5', ...ink(5) }) + ellipse(960, 860, 120, 26, { fill: '#C9C3B5', ...ink(5) }) + rect(948, 800, 24, 60, { fill: '#C9C3B5', ...ink(4) }) + ellipse(960, 800, 60, 14, { fill: '#C9C3B5', ...ink(4) });
  const r = rng(4); for (let i = 0; i < 14; i++) s += circle(720 + r() * 480, 950 + r() * 40, 5, { fill: '#C9A43A' });
  return wob(s);
}
// looking straight down the atrium from the level-4 railing
export function atriumDown() {
  let s = rect(0, 0, W, H, { fill: '#3A4250' });
  // three lower balconies stepping in toward the ground floor
  const rings_ = [[0.0, '#6E767B'], [0.22, '#5E6670'], [0.42, '#4E5662'], [0.6, '#B8AE9A']];
  rings_.forEach(([k, col], i) => {
    const x0 = 60 + k * 700, y0 = 40 + k * 380, x1 = W - x0, y1 = H - 60 - k * 300;
    s += rect(x0, y0, x1 - x0, y1 - y0, { fill: col, ...ink(5) });
    if (i < 3) for (let x = x0 + 60; x < x1 - 40; x += 160) s += rect(x, y0 + 10, 110, 40 - i * 8, { fill: SHOPS[(i * 3 + Math.floor(x / 160)) % 16][1], ...ink(3) });
  });
  s += ellipse(960, 690, 190, 70, { fill: '#9C968A', ...ink(5) }) + ellipse(960, 684, 160, 54, { fill: '#6E685E', ...ink(4) }) + circle(960, 676, 22, { fill: '#C9C3B5', ...ink(4) });
  // the railing we stand at, in the foreground
  s += rect(0, 930, W, 150, { fill: '#C9C3B5', ...ink(6) }) + rect(0, 900, W, 40, { fill: '#9FB8C4', opacity: 0.25 }) + line(0, 900, W, 900, { stroke: INK, strokeWidth: 16 }) + line(0, 900, W, 900, { stroke: '#C9CDD0', strokeWidth: 8 });
  return wob(s);
}
export function skylight() {
  let s = rect(0, 0, W, H, { fill: '#1E2638' });
  // panes converging to a vanishing point high in the middle
  const vp = [960, -600];
  for (let x = -1200; x <= W + 1200; x += 240) s += line(x, H + 100, vp[0] + (x - vp[0]) * 0.18, 0, { stroke: '#0E1320', strokeWidth: 18 });
  for (const y of [980, 760, 580, 430, 300, 190, 95]) s += line(0, y, W, y, { stroke: '#0E1320', strokeWidth: 14 - (980 - y) / 90 });
  // the top balcony edge peeking in at the bottom corners
  s += poly([[0, H], [0, 860], [380, 1080]], { fill: '#6E767B', ...ink(6) }) + poly([[W, H], [W, 860], [W - 380, 1080]], { fill: '#6E767B', ...ink(6) });
  return wob(s);
}
// the escalator from the side: ground floor bottom left to level two top right
export function escalatorSide() {
  let s = rect(0, 0, W, H, { fill: '#4E5662' });
  s += rect(0, 0, W, 300, { fill: '#5E6670' }) + rect(1200, 120, 720, 180, { fill: '#2A303A', ...ink(5) }) + rect(1200, 120, 720, 40, { fill: '#7C6A8E', ...ink(4) }) + label(1560, 150, 'GAME ZONE', 26, '#F7F2E6', 'middle', 4);
  s += rect(1100, 300, 820, 34, { fill: '#C9C3B5', ...ink(5) });
  s += rect(0, 900, W, 180, { fill: '#B8AE9A' }) + line(0, 900, W, 900, ink(5));
  // truss
  s += poly([[160, 900], [380, 900], [1260, 334], [1100, 334]], { fill: '#8E9499', ...ink(7) });
  for (let k = 0.05; k < 1; k += 0.045) { const x = lerp(270, 1180, k), y = lerp(900, 334, k); s += path(`M${x - 34} ${y} h34 v-26`, { fill: 'none', stroke: '#6E767B', strokeWidth: 5 }); }
  // handrail and the glass side panel
  s += poly([[140, 820], [360, 820], [1240, 254], [1090, 254]], { fill: '#9FB8C4', opacity: 0.25 });
  s += path('M100 830 Q120 780 170 780 L1100 250 Q1160 220 1260 240', { fill: 'none', stroke: INK, strokeWidth: 30, strokeLinecap: 'round' }) + path('M100 830 Q120 780 170 780 L1100 250 Q1160 220 1260 240', { fill: 'none', stroke: '#2B2F33', strokeWidth: 18, strokeLinecap: 'round' });
  return wob(s);
}
function lerp(a, b, k) { return a + (b - a) * k; }
// looking up a stopped escalator (POV)
export function escalatorPov() {
  let s = rect(0, 0, W, H, { fill: '#3A4250' });
  const vp = [960, 120];
  const P = (x, y, k) => [vp[0] + (x - vp[0]) * (1 - k), vp[1] + (y - vp[1]) * (1 - k)];
  // steps: horizontal bands that get thinner toward the top
  for (let i = 0; i < 26; i++) {
    const k0 = 1 - Math.pow(0.9, i), k1 = 1 - Math.pow(0.9, i + 1);
    const a = P(560, 1080, k0), b = P(1360, 1080, k0), c = P(1360, 1080, k1), d = P(560, 1080, k1);
    const m = [(a[0] + d[0]) / 2, (a[1] + d[1]) / 2], n = [(b[0] + c[0]) / 2, (b[1] + c[1]) / 2];
    s += poly([a, b, n, m], { fill: '#6E767B', stroke: INK, strokeWidth: 3 }) + poly([m, n, c, d], { fill: '#9AA3A8', stroke: INK, strokeWidth: 3 });
    s += line(a[0], a[1], b[0], b[1], { stroke: '#E9B93E', strokeWidth: Math.max(2, 10 * (1 - k0)) });
  }
  // side panels and handrails
  s += poly([[0, 1080], [560, 1080], [vp[0] - 40, vp[1]], [0, 0]], { fill: '#8E9499', ...ink(6) }) + poly([[W, 1080], [1360, 1080], [vp[0] + 40, vp[1]], [W, 0]], { fill: '#8E9499', ...ink(6) });
  s += line(300, 1080, 930, 130, { stroke: INK, strokeWidth: 40, strokeLinecap: 'round' }) + line(1620, 1080, 990, 130, { stroke: INK, strokeWidth: 40, strokeLinecap: 'round' });
  s += line(300, 1080, 930, 130, { stroke: '#2B2F33', strokeWidth: 26, strokeLinecap: 'round' }) + line(1620, 1080, 990, 130, { stroke: '#2B2F33', strokeWidth: 26, strokeLinecap: 'round' });
  s += rect(700, 0, 520, 110, { fill: '#2A303A', ...ink(4) }) + rect(700, 0, 520, 34, { fill: '#3E6E9A', ...ink(4) });
  return wob(s);
}

// ---------- Bright Tech, level 4 ----------
export function brightFront() {
  let s = rect(0, 0, W, H, { fill: '#4E5662' });
  s += rect(160, 120, 1600, 700, { fill: '#2A303A', ...ink(7) });
  // sign
  s += rect(160, 120, 1600, 130, { fill: '#3E6E9A', ...ink(6) }) + circle(560, 185, 44, { fill: '#E9B93E', ...ink(5) });
  for (let a = 0; a < 8; a++) { const t = a * Math.PI / 4; s += line(560 + Math.cos(t) * 56, 185 + Math.sin(t) * 56, 560 + Math.cos(t) * 74, 185 + Math.sin(t) * 74, { stroke: '#E9B93E', strokeWidth: 8, strokeLinecap: 'round' }); }
  s += text(1010, 218, 'BRIGHT TECH', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 92, fill: '#F7F2E6', textAnchor: 'middle', letterSpacing: 8 });
  // glass front: two big panes and the open door between them
  s += rect(200, 280, 600, 520, { fill: '#3A4552', ...ink(5) }) + rect(1120, 280, 600, 520, { fill: '#3A4552', ...ink(5) }) + rect(820, 280, 280, 520, { fill: '#1E232B', ...ink(5) });
  for (const x of [200, 1120]) s += path(`M${x + 60} 760 L${x + 260} 320 M${x + 160} 780 L${x + 400} 300`, { stroke: '#9FB8C4', strokeWidth: 10, opacity: 0.25 });
  // window display: a stand of phones on the left, the lantern stand on the right
  s += rect(260, 640, 480, 160, { fill: '#5E6670', ...ink(4) });
  for (let i = 0; i < 5; i++) s += rect(290 + i * 88, 560, 56, 90, { rx: 8, fill: '#1E1F22', ...ink(3) });
  s += rect(1180, 680, 480, 120, { fill: '#5E6670', ...ink(4) }) + rect(1240, 600, 140, 30, { fill: '#FBF6EA', ...ink(3) }) + label(1310, 622, 'SOLAR · USB', 14, INK);
  // balcony railing in front
  s += rect(0, 880, W, 200, { fill: '#C9C3B5', ...ink(5) }) + rect(0, 830, W, 60, { fill: '#9FB8C4', opacity: 0.22 }) + line(0, 830, W, 830, { stroke: INK, strokeWidth: 16 }) + line(0, 830, W, 830, { stroke: '#C9CDD0', strokeWidth: 8 });
  for (let x = 0; x < W; x += 200) s += line(x, 830, x, 880, { stroke: '#8E9499', strokeWidth: 5 });
  return wob(s);
}
export function brightInside() {
  let s = rect(0, 0, W, H, { fill: '#5E6670' });
  s += rect(0, 0, W, 90, { fill: '#4A525E' }) + line(0, 90, W, 90, ink(4));
  for (const x of [300, 960, 1620]) s += rect(x - 150, 20, 300, 40, { rx: 6, fill: '#8E9499', ...ink(3) });
  // the TV wall
  s += rect(80, 160, 1760, 420, { fill: '#4A525E', ...ink(5) });
  for (let row = 0; row < 2; row++) for (let i = 0; i < 6; i++) s += rect(120 + i * 285, 190 + row * 195, 255, 165, { rx: 6, fill: '#161A20', ...ink(4) });
  s += label(960, 150, 'TV · AUDIO · DRONES · PHONES', 26, '#E8E1D2', 'middle', 6);
  // floor and two display tables
  s += rect(0, 600, W, 480, { fill: '#B3A88E' }) + line(0, 600, W, 600, ink(5));
  for (let x = -300; x < W + 300; x += 200) s += line(x, 600, x + (x - W / 2) * 0.7, H, { stroke: '#A3987E', strokeWidth: 3 });
  for (const [x, y, w] of [[260, 700, 520], [1160, 720, 560]]) {
    s += rect(x, y, w, 60, { fill: '#E9E5DC', ...ink(5) }) + rect(x + 30, y + 60, 40, 220, { fill: '#8E9499', ...ink(4) }) + rect(x + w - 70, y + 60, 40, 220, { fill: '#8E9499', ...ink(4) });
    for (let i = 0; i < Math.floor(w / 110); i++) s += rect(x + 30 + i * 110, y - 26, 70, 30, { rx: 6, fill: '#1E1F22', ...ink(3) });
  }
  return wob(s);
}
export function brightCamp() {
  let s = rect(0, 0, W, H, { fill: '#4A525E' });
  // the shop window: night outside, the solar panel taped to the glass
  s += rect(120, 80, 1100, 700, { fill: '#1E2638', ...ink(6) });
  for (let i = 0; i < 40; i++) s += circle(160 + ((i * 337) % 1020), 120 + ((i * 211) % 300), 2, { fill: '#F3EBDD', opacity: 0.5 });
  s += rect(140, 520, 1060, 240, { fill: '#2C303A' }) + rect(640, 560, 360, 160, { fill: '#5A5E68', ...ink(4) }) + label(820, 620, 'FRESHWAY', 26, '#8E9499', 'middle', 4);
  s += g(rect(-210, -130, 420, 260, { fill: '#2E4A6E', ...ink(6) }) + Array.from({ length: 8 }, (_, i) => rect(-200 + (i % 4) * 102, -120 + Math.floor(i / 4) * 122, 96, 116, { fill: '#3E6E9A', stroke: '#9FB8C4', strokeWidth: 2 })).join('')
    + g(rect(-60, -18, 120, 36, { fill: '#C9C3B5', opacity: 0.9 }), { transform: 'translate(-200 -120) rotate(-35)' }) + g(rect(-60, -18, 120, 36, { fill: '#C9C3B5', opacity: 0.9 }), { transform: 'translate(200 -120) rotate(35)' })
    + g(rect(-60, -18, 120, 36, { fill: '#C9C3B5', opacity: 0.9 }), { transform: 'translate(-200 120) rotate(35)' }) + g(rect(-60, -18, 120, 36, { fill: '#C9C3B5', opacity: 0.9 }), { transform: 'translate(200 120) rotate(-35)' }), { transform: 'translate(560 300) rotate(-3)' });
  s += line(560, 430, 700, 880, { stroke: INK, strokeWidth: 6 });
  // floor, sleeping bag, two backpacks, a power bank on charge
  s += rect(0, 780, W, 300, { fill: '#B3A88E' }) + line(0, 780, W, 780, ink(5));
  s += path('M260 980 Q240 900 330 880 L1020 860 Q1110 860 1100 940 Q1100 1010 1010 1010 L340 1030 Q270 1030 260 980 Z', { fill: '#7C4A8E', ...ink(6) }) + path('M840 866 Q800 940 860 1010', { fill: 'none', stroke: '#5E3470', strokeWidth: 8 });
  s += ellipse(420, 935, 110, 46, { fill: '#B98FCB', ...ink(5) });
  s += rect(1300, 720, 220, 260, { rx: 40, fill: '#3E6E5A', ...ink(6) }) + rect(1330, 820, 160, 100, { rx: 20, fill: '#2F5546', ...ink(4) });
  s += rect(1560, 800, 170, 190, { rx: 34, fill: '#E07A3A', ...ink(6) }) + rect(1585, 870, 120, 70, { rx: 16, fill: '#C4602A', ...ink(4) }) + circle(1645, 840, 16, { fill: '#E9B93E', ...ink(3) });
  s += rect(1250, 1000, 90, 50, { rx: 8, fill: '#1E1F22', ...ink(4) }) + circle(1325, 1012, 5, { fill: '#7FD36B' }) + path('M1250 1025 Q1100 1060 980 1040', { fill: 'none', stroke: INK, strokeWidth: 5 });
  return wob(s);
}

// ---------- Brookfield Mall side door, outside in the rain ----------
export function mallSideDoor() {
  let s = rect(0, 0, W, H, { fill: '#2A3040' });
  s += rect(0, 0, W, 860, { fill: '#5A5E68' });
  for (let y = 0; y < 860; y += 60) s += line(0, y, W, y, { stroke: '#4E525C', strokeWidth: 3 });
  s += rect(380, 120, 1160, 70, { fill: '#3A4256', ...ink(5) }) + label(960, 168, 'BROOKFIELD MALL · EAST ENTRANCE', 34, '#9A8E80', 'middle', 6);
  // the two chained doors on the left, a tall glass panel on the right
  s += rect(420, 230, 640, 630, { fill: '#6E747A', ...ink(7) });
  for (const x of [440, 750]) s += rect(x, 250, 290, 610, { fill: '#2E3646', ...ink(5) }) + rect(x + 20, 520, 250, 30, { rx: 12, fill: '#C9CDD0', ...ink(4) });
  s += rect(1100, 230, 400, 630, { fill: '#6E747A', ...ink(7) }) + rect(1120, 250, 360, 610, { fill: '#2E3646', ...ink(5) });
  for (const x of [470, 780, 1150]) s += path(`M${x} 820 L${x + 130} 300`, { stroke: '#9FB8C4', strokeWidth: 8, opacity: 0.25 });
  s += rect(0, 860, W, 220, { fill: '#30343E' }) + line(0, 860, W, 860, ink(5));
  return wob(s);
}
