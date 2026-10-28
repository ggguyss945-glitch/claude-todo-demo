// Channel art for UNDEAD ORBIT: three A/B thumbnails for LAST LIGHT episode 1, the channel logo and the banner.
// Everything is drawn with the series' own characters and sets, so the art matches the episode frame for frame.
import { W, H, INK, PAL, defs, finish, glow, hero, zombie, crowd, g, rect, circle, ellipse, line, poly, path, text, ink, rng } from '../lib.js';
import { nightTint, screenGlow, darkness, radioProp, mitt } from '../ep/kit.js';
import { aisle } from '../scenes.js';
import * as S from '../ep/sets.js';

const svg = (w, h, inner, seed = 5) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}">${defs(seed, seed)}${inner}</svg>`;
const FONT = "'Lilita One', Rubik, sans-serif";
const RED = '#E8392B', LIME = '#C5DB9C', TAPE = '#F2C230';

// ---------- type ----------
// thumbnail headline: drop shadow, thick ink outline, flat fill; `rich` may carry coloured <tspan>s
function headline(x, y, plain, { size = 200, fill = '#FFFFFF', sw = 22, anchor = 'middle', rot = 0, shadow = 12, ls = 3, rich } = {}) {
  const base = { fontFamily: FONT, fontSize: size, textAnchor: anchor, letterSpacing: ls, strokeLinejoin: 'round' };
  const t = rot ? `rotate(${rot} ${x} ${y})` : undefined;
  return g(text(x + shadow * 0.5, y + shadow, plain, { ...base, fill: '#000', opacity: 0.5, stroke: '#000', strokeWidth: sw })
    + text(x, y, rich || plain, { ...base, fill, stroke: INK, strokeWidth: sw, paintOrder: 'stroke' }), { transform: t });
}

// seven-segment digits, the store's own LED clock look
const SEG = { 0: 'abcdef', 1: 'bc', 2: 'abged', 3: 'abgcd', 4: 'fgbc', 5: 'afgcd', 6: 'afgedc', 7: 'abc', 8: 'abcdefg', 9: 'abcdfg' };
function led(x, y, str, h, on = '#FF3B2F', off = '#3A1010') {
  const w = h * 0.56, t = h * 0.14, hh = h / 2;
  const seg = {
    a: [t * 0.6, 0, w - t * 1.2, t], g: [t * 0.6, hh - t / 2, w - t * 1.2, t], d: [t * 0.6, h - t, w - t * 1.2, t],
    f: [0, t * 0.6, t, hh - t * 0.9], b: [w - t, t * 0.6, t, hh - t * 0.9], e: [0, hh + t * 0.3, t, hh - t * 0.9], c: [w - t, hh + t * 0.3, t, hh - t * 0.9],
  };
  let s = '', cx = x;
  for (const ch of str) {
    if (ch === ':') { s += circle(cx + t * 0.9, y + h * 0.3, t * 0.62, { fill: on }) + circle(cx + t * 0.9, y + h * 0.72, t * 0.62, { fill: on }); cx += t * 2.6; continue; }
    const lit = SEG[ch] || '';
    for (const k of 'abcdefg') { const [sx, sy, sw, sh] = seg[k]; s += rect(cx + sx, y + sy, sw, sh, { rx: t / 2, fill: lit.includes(k) ? on : off }); }
    cx += w + t * 1.4;
  }
  return g(g(s, { filter: 'url(#softS)', opacity: 0.85 }) + s, { transform: `skewX(-7) translate(${(y + h) * 0.12} 0)` });
}

// ---------- space ----------
const sparkle = (x, y, r, fill = '#FFFFFF', op = 0.9) =>
  path(`M${x} ${y - r} Q${x} ${y} ${x + r} ${y} Q${x} ${y} ${x} ${y + r} Q${x} ${y} ${x - r} ${y} Q${x} ${y} ${x} ${y - r} Z`, { fill, opacity: op });
function stars(w, h, n, seed, { y0 = 0, y1 = h, x0 = 0, x1 = w, big = 0.05 } = {}) {
  const r = rng(seed); let s = '';
  for (let i = 0; i < n; i++) {
    const x = x0 + r() * (x1 - x0), y = y0 + r() * (y1 - y0), k = r();
    const rad = k < 0.85 ? 0.8 + r() * 1.5 : 1.8 + r() * 2.2, c = k < 0.92 ? '#FFFFFF' : r() < 0.5 ? '#FFE7A8' : '#BFE3FF';
    s += circle(x, y, rad, { fill: c, opacity: (0.3 + r() * 0.7).toFixed(2) });
    if (k > 1 - big) s += sparkle(x, y, 7 + r() * 13, c, 0.85);
  }
  return s;
}
// smooth random blob, for continents and nebulae
function blob(x, y, rad, seed, n = 9, j = 0.4) {
  const r = rng(seed), p = [];
  for (let i = 0; i < n; i++) { const a = (i / n) * Math.PI * 2, rr = rad * (1 - j / 2 + r() * j); p.push([x + Math.cos(a) * rr, y + Math.sin(a) * rr * (0.75 + r() * 0.3)]); }
  const mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
  let m = mid(p[n - 1], p[0]), d = `M${m[0].toFixed(1)} ${m[1].toFixed(1)}`;
  for (let i = 0; i < n; i++) { const q = p[i], m2 = mid(p[i], p[(i + 1) % n]); d += ` Q${q[0].toFixed(1)} ${q[1].toFixed(1)} ${m2[0].toFixed(1)} ${m2[1].toFixed(1)}`; }
  return d + ' Z';
}
function spaceBg(w, h, seed, id) {
  let s = `<defs><linearGradient id="sp_${id}" x1="0" y1="0" x2="0.35" y2="1"><stop offset="0" stop-color="#070918"/><stop offset="0.5" stop-color="#16123A"/><stop offset="1" stop-color="#08091A"/></linearGradient>
    <filter id="neb_${id}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="${Math.round(w / 28)}"/></filter></defs>`;
  s += rect(0, 0, w, h, { fill: `url(#sp_${id})` });
  const r = rng(seed + 7), cols = ['#6B3FA0', '#2A7F95', '#B0448A', '#3B4FB0'];
  let neb = '';
  for (let i = 0; i < 9; i++) neb += path(blob(r() * w, r() * h, (0.12 + r() * 0.16) * w, seed + i, 8, 0.6), { fill: cols[i % cols.length], opacity: (0.16 + r() * 0.18).toFixed(2) });
  s += g(neb, { filter: `url(#neb_${id})` });
  return s + stars(w, h, Math.round((w * h) / 5200), seed);
}

// ---------- the mascot: a zombie planet held together by caution tape ----------
export function mascot(cx, cy, r, id = 'm', { look = 0 } = {}) {
  const rx = r * 1.5, ry = r * 0.36, rot = -12, ringY = cy + r * 0.2, tw = r * 0.2, lw = Math.max(4, r * 0.05);
  let s = `<defs>
    <pattern id="tape_${id}" width="${tw * 1.5}" height="${tw * 1.5}" patternUnits="userSpaceOnUse" patternTransform="rotate(40)">
      <rect width="${tw * 1.5}" height="${tw * 1.5}" fill="${TAPE}"/><rect width="${tw * 0.7}" height="${tw * 1.5}" fill="#1E1A1A"/></pattern>
    <clipPath id="pc_${id}"><circle cx="${cx}" cy="${cy}" r="${r}"/></clipPath>
    <clipPath id="fr_${id}"><rect x="${cx - r * 3}" y="${ringY}" width="${r * 6}" height="${r * 3}" transform="rotate(${rot} ${cx} ${ringY})"/></clipPath>
    <radialGradient id="psh_${id}" cx="36%" cy="30%" r="78%"><stop offset="0.5" stop-color="#0B1030" stop-opacity="0"/><stop offset="1" stop-color="#0B1030" stop-opacity="0.6"/></radialGradient>
    <radialGradient id="atm_${id}" cx="50%" cy="50%" r="50%"><stop offset="0.82" stop-color="#B8E07A" stop-opacity="0"/><stop offset="0.9" stop-color="#B8E07A" stop-opacity="0.35"/><stop offset="1" stop-color="#B8E07A" stop-opacity="0"/></radialGradient>
  </defs>`;
  const ring = g(ellipse(cx, ringY, rx, ry, { fill: 'none', stroke: INK, strokeWidth: tw + lw * 2 }) + ellipse(cx, ringY, rx, ry, { fill: 'none', stroke: `url(#tape_${id})`, strokeWidth: tw }),
    { transform: `rotate(${rot} ${cx} ${ringY})` });
  s += circle(cx, cy, r * 1.22, { fill: `url(#atm_${id})` });
  s += ring;   // back half, the planet covers it
  // planet body, continents, craters, terminator shade
  let body = circle(cx, cy, r, { fill: '#9DB384' });
  body += path(blob(cx - r * 0.55, cy - r * 0.55, r * 0.42, 11), { fill: '#86A070' }) + path(blob(cx + r * 0.7, cy - r * 0.15, r * 0.36, 23), { fill: '#86A070' })
    + path(blob(cx - r * 0.2, cy + r * 0.78, r * 0.5, 37), { fill: '#86A070' }) + path(blob(cx + r * 0.25, cy - r * 0.92, r * 0.3, 41), { fill: '#86A070' });
  body += ellipse(cx + r * 0.62, cy + r * 0.38, r * 0.13, r * 0.1, { fill: '#7C946A', ...ink(lw * 0.5) }) + ellipse(cx - r * 0.72, cy + r * 0.2, r * 0.09, r * 0.07, { fill: '#7C946A', ...ink(lw * 0.45) });
  body += circle(cx, cy, r, { fill: `url(#psh_${id})` }) + ellipse(cx - r * 0.38, cy - r * 0.5, r * 0.28, r * 0.16, { fill: '#FFFFFF', opacity: 0.18, transform: `rotate(-30 ${cx - r * 0.38} ${cy - r * 0.5})` });
  s += g(body, { clipPath: `url(#pc_${id})` });
  // face: the dead's hollow eyes, slack jaw, a stitched scar
  const ex = cx + look * r * 0.12, ey = cy - r * 0.26;
  s += ellipse(ex - r * 0.33, ey, r * 0.2, r * 0.23, { fill: '#2E332D' }) + ellipse(ex + r * 0.31, ey + r * 0.03, r * 0.185, r * 0.21, { fill: '#2E332D' });
  s += circle(ex - r * 0.29 + look * r * 0.05, ey + r * 0.05, r * 0.065, { fill: '#E8EAD8' }) + circle(ex + r * 0.34 + look * r * 0.05, ey + r * 0.08, r * 0.06, { fill: '#E8EAD8' });
  s += ellipse(ex + r * 0.02, cy + r * 0.12, r * 0.13, r * 0.15, { fill: '#2A1F1F' }) + rect(ex - r * 0.045, cy - r * 0.03, r * 0.09, r * 0.06, { fill: '#EFE9D6' });
  const sx0 = cx - r * 0.66, sy0 = cy - r * 0.62;
  s += path(`M${sx0} ${sy0} Q${cx - r * 0.45} ${cy - r * 0.78} ${cx - r * 0.22} ${cy - r * 0.74}`, { fill: 'none', stroke: '#5E7150', strokeWidth: lw * 0.9, strokeLinecap: 'round' });
  for (let i = 0; i < 4; i++) { const k = 0.15 + i * 0.22, px = sx0 + (cx - r * 0.22 - sx0) * k, py = sy0 + (cy - r * 0.74 - sy0) * k - r * 0.08 * Math.sin(k * Math.PI); s += line(px - r * 0.03, py - r * 0.06, px + r * 0.03, py + r * 0.06, { stroke: '#5E7150', strokeWidth: lw * 0.7, strokeLinecap: 'round' }); }
  s += circle(cx, cy, r, { fill: 'none', ...ink(lw) });
  s += g(ring, { clipPath: `url(#fr_${id})` });   // front half of the tape crosses in front
  return g(s, { filter: 'url(#wobbleSoft)' });
}

// ---------- thumbnail pieces ----------
// a crowd pressed against the store's glass front (doors set coordinates), several rows deep
function pressedCrowd(seed = 2, palms = true) {
  let s = crowd({ x0: 560, x1: 1360, y: 820, rows: 3, n: 15, s: 0.7, seed, spread: 34, arms: true });
  const outfits = ['cashier', 'jogger', 'shopper', 'park', 'nurse', 'janitor', 'guard', 'suit', 'shopper'];
  for (let i = 0; i < 9; i++) s += zombie({ x: 600 + i * 90 + 10 * Math.sin(i * 7), y: 1010 + 30 * Math.sin(i * 3.1), s: 1.18, outfit: outfits[i], tilt: (i % 2 ? 9 : -9), look: 0.06 * Math.sin(i), pose: 'reach', filter: false });
  if (palms) for (let i = 0; i < 13; i++) s += mitt(590 + i * 62, 560 + 46 * Math.sin(i * 2.3), 90 + 22 * Math.sin(i), 0.6, PAL.zSkin);
  return s;
}
// you, the walkie-talkie up at your cheek, its red light on
function talkieHero(x, y, sc, { expr = 'scared', look = 0, lit } = {}) {
  const u = 60 * sc, hx = x + 0.98 * u, hy = y - 4.67 * u, k = 0.27 * sc, rx = hx + 0.1 * u, ry = hy + 0.16 * u, rot = 8;
  const a = (rot * Math.PI) / 180, lx = rx + (-30 * k) * Math.cos(a) - (-140 * k) * Math.sin(a), ly = ry + (-30 * k) * Math.sin(a) + (-140 * k) * Math.cos(a);
  const extra = radioProp(rx, ry, k, { on: true, led: PAL.red, rot }) + circle(hx, hy, 0.15 * u, { fill: PAL.skin, ...ink(5) });
  const h = hero({ x, y, s: sc, pose: 'talkie', expr, look, extra });
  return (lit ? g(h, { filter: `url(#${lit})` }) : h) + glow(lx, ly, 26 * k * 2.2, PAL.red, 0.9);
}
const coolLit = (id, m = '0.8 0 0 0 0.02 0 0.84 0 0 0.03 0 0 1 0 0.06 0 0 0 1 0') => `<defs><filter id="${id}" x="-10%" y="-10%" width="120%" height="120%"><feColorMatrix type="matrix" values="${m}"/></filter></defs>`;

// A: the niche's own format, DAY 0 calm against DAY 7 dread, split by a slanted white seam
function thumbA() {
  const L = [[0, 0], [1010, 0], [905, 1080], [0, 1080]], R = [[1010, 0], [1920, 0], [1920, 1080], [905, 1080]];
  let s = `<defs><clipPath id="cl"><polygon points="${L.map((p) => p.join(',')).join(' ')}"/></clipPath><clipPath id="cr"><polygon points="${R.map((p) => p.join(',')).join(' ')}"/></clipPath></defs>`;
  // left: the bright store at the start of the night shift
  let left = g(aisle({ night: false, seed: 5 }).s, { transform: 'translate(-480 0)' });
  left += screenGlow(480, 300, 600, 320, '#FFF4D8', 0.35);
  const u = 60 * 3.1;
  const box = g(rect(-1.15 * u, 0, 2.3 * u, 1.35 * u, { rx: 10, fill: '#C49A6C', ...ink(8) }) + line(-1.15 * u, 0.28 * u, 1.15 * u, 0.28 * u, ink(5))
    + rect(-0.78 * u, 0.48 * u, 1.56 * u, 0.5 * u, { rx: 8, fill: '#F3EEDF', ...ink(5) }) + text(0, 0.84 * u, 'FRESHWAY', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 0.22 * u, fill: '#3E6E5A', textAnchor: 'middle', letterSpacing: 3 }),
    { transform: `translate(470 ${1530 - 3.95 * u})` });
  left += hero({ x: 470, y: 1530, s: 3.1, pose: 'carry', expr: 'smile', look: 0.15, extra: box });
  s += g(left, { clipPath: 'url(#cl)' });
  // right: a week later, the same doors with two hundred of them outside
  let right = g(S.doorsOutside({ dawn: false }) + pressedCrowd(4, false) + S.doorsInside(), { transform: 'translate(500 0)' });
  right += nightTint(0.5, '#22305A') + screenGlow(1460, 600, 560, 380, '#7F9BD8', 0.28) + screenGlow(1780, 160, 360, 260, RED, 0.22);
  right += coolLit('lit') + talkieHero(1430, 1530, 3.1, { expr: 'scared', look: -0.3, lit: 'lit' });
  s += g(right, { clipPath: 'url(#cr)' });
  // seam
  s += line(1010, -20, 905, 1100, { stroke: INK, strokeWidth: 40 }) + line(1010, -20, 905, 1100, { stroke: '#FFFFFF', strokeWidth: 22 });
  s += headline(470, 215, 'DAY 0', { size: 205 }) + headline(1440, 215, 'DAY 7', { size: 205, fill: RED });
  s += finish({ vignette: 0.45, grain: 0.06 });
  return { w: W, h: H, svg: svg(W, H, s, 5), css: 'saturate(1.15) contrast(1.05)' };
}

// B: the voice on the radio, and the man on the roof behind you
function thumbB() {
  let s = S.sky('night') + g(S.cityBand('night'), { transform: 'translate(0 260)', opacity: 0.9 });
  // Freshway's front, the roof edge, the lot
  s += g(rect(860, 470, 1140, 700, { fill: '#4C505A', ...ink(7) }) + rect(860, 445, 1140, 40, { fill: '#2A2D34', ...ink(6) })
    + rect(1010, 540, 820, 120, { rx: 10, fill: '#2F4A40', ...ink(6) }) + text(1420, 628, 'FRESHWAY', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 84, fill: '#7FA08E', textAnchor: 'middle', letterSpacing: 10 })
    + rect(1000, 720, 340, 360, { fill: '#2A3440', ...ink(6) }) + rect(1380, 720, 340, 360, { fill: '#2A3440', ...ink(6) }), { filter: 'url(#wobble)' });
  s += rect(0, 860, W, 220, { fill: '#2B2E36' }) + line(0, 860, W, 860, ink(5));
  for (let x = -100; x < W; x += 230) s += line(x, 1080, x + 120, 880, { stroke: '#E9E2C8', strokeWidth: 6, opacity: 0.35 });
  s += crowd({ x0: 1060, x1: 1900, y: 1000, rows: 2, n: 10, s: 0.55, seed: 9, spread: 30 });
  s += nightTint(0.42, '#22305A');
  // the figure on the roof edge: cap, radio held up, two pale eyes
  const fx = 1505, fy = 447, k = 3.1, C = '#07080D';
  s += screenGlow(fx, fy - 140, 260, 220, '#8FA6C8', 0.45);
  let fig = circle(fx, fy - 62 * k, 15 * k, { fill: C }) + rect(fx - 21 * k, fy - 66 * k, 42 * k, 9 * k, { rx: 3, fill: C }) + rect(fx - 19 * k, fy - 48 * k, 38 * k, 48 * k, { rx: 9 * k, fill: C });
  fig += line(fx + 14 * k, fy - 40 * k, fx + 26 * k, fy - 64 * k, { stroke: C, strokeWidth: 8 * k, strokeLinecap: 'round' }) + rect(fx + 20 * k, fy - 84 * k, 12 * k, 24 * k, { rx: 3, fill: C }) + line(fx + 28 * k, fy - 84 * k, fx + 28 * k, fy - 104 * k, { stroke: C, strokeWidth: 3 * k });
  fig += circle(fx - 5 * k, fy - 61 * k, 2.4 * k, { fill: '#F2F0E0' }) + circle(fx + 6 * k, fy - 61 * k, 2.4 * k, { fill: '#F2F0E0' });
  s += fig + glow(fx - 5 * k, fy - 61 * k, 12 * k, '#F2F0E0', 0.35) + circle(fx + 26 * k, fy - 79 * k, 3.4 * k, { fill: RED }) + glow(fx + 26 * k, fy - 79 * k, 22 * k, RED, 0.95);
  // hand-drawn red ring around him
  s += g(ellipse(fx + 10, fy - 150, 175, 215, { fill: 'none', stroke: INK, strokeWidth: 30 }) + ellipse(fx + 10, fy - 150, 175, 215, { fill: 'none', stroke: RED, strokeWidth: 16 }), { transform: `rotate(8 ${fx} ${fy - 150})`, filter: 'url(#wobble)' });
  // you, radio to your ear, looking back
  s += screenGlow(760, 560, 420, 520, '#6A86C8', 0.25);
  s += coolLit('litB', '0.86 0 0 0 0.02 0 0.88 0 0 0.03 0 0 1 0 0.07 0 0 0 1 0') + talkieHero(560, 1590, 3.35, { expr: 'scared', look: 0.75, lit: 'litB' });
  s += headline(60, 190, "DON'T ANSWER", { size: 172, anchor: 'start', rich: `DON'T <tspan fill="${RED}">ANSWER</tspan>` });
  s += finish({ vignette: 0.7, grain: 0.07 });
  return { w: W, h: H, svg: svg(W, H, s, 6), css: 'saturate(1.15) contrast(1.06)' };
}

// C: the doors unlock themselves at 7:00 and the whole lot is waiting
function thumbC() {
  let s = S.doorsOutside({ dawn: true }) + pressedCrowd(7, false);
  s += screenGlow(960, 380, 520, 260, '#FFD2A8', 0.35);
  s += coolLit('dim', '0.5 0 0 0 0 0 0.48 0 0 0 0 0 0.62 0 0.02 0 0 0 1 0') + g(S.doorsInside(), { filter: 'url(#dim)' });
  s += rect(560, 250, 800, 740, { fill: '#BFD6E0', opacity: 0.08 });
  s += path('M600 300 l120 -40 M620 360 l160 -60 M1010 300 l120 -40', { stroke: '#FFFFFF', strokeWidth: 8, opacity: 0.3 });
  s += darkness(0.5, 0.45, 0.7, 0.62, 'vc') + screenGlow(120, 120, 380, 300, RED, 0.16) + screenGlow(1800, 120, 380, 300, RED, 0.16);
  // the store's LED clock over the doors, a minute to opening
  s += g(rect(590, 22, 740, 300, { rx: 26, fill: '#140A0B', ...ink(9) }) + rect(612, 44, 696, 256, { rx: 16, fill: '#1E0C0D' }), { filter: 'url(#wobbleSoft)' });
  s += led(660, 62, '6:59', 190);
  s += text(960, 300, 'DOORS UNLOCK AT 7:00', { fontFamily: FONT, fontSize: 40, fill: TAPE, textAnchor: 'middle', letterSpacing: 4 });
  s += screenGlow(960, 170, 420, 160, '#FF3B2F', 0.25);
  s += g(rect(860, 360, 200, 70, { rx: 12, fill: '#2B1D21', ...ink(5) }) + text(960, 409, 'LOCKED', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 34, fill: '#FF6A5A', textAnchor: 'middle', letterSpacing: 3 }), { filter: 'url(#wobbleSoft)' });
  // you, inside, turning to us
  s += coolLit('litC', '0.95 0 0 0 0.03 0 0.9 0 0 0.02 0 0 0.95 0 0.05 0 0 0 1 0');
  s += g(hero({ x: 1560, y: 1600, s: 3.25, pose: 'scared', expr: 'scared', look: -0.3 }), { filter: 'url(#litC)' });
  s += headline(330, 1010, '1 vs 200', { size: 140, rot: -6, rich: `1 <tspan fill="${RED}">vs</tspan> 200` });
  s += finish({ vignette: 0.5, grain: 0.07 });
  return { w: W, h: H, svg: svg(W, H, s, 7), css: 'saturate(1.2) contrast(1.06)' };
}

// ---------- channel logo: 800x800, reads inside YouTube's circle crop down to 98 px ----------
function logo() {
  const N = 800;
  let s = spaceBg(N, N, 21, 'lg');
  s += sparkle(150, 190, 22, '#FFFFFF', 0.9) + sparkle(655, 150, 15, '#FFE7A8', 0.9) + sparkle(640, 640, 12, '#BFE3FF', 0.8);
  s += mascot(400, 410, 222, 'lg');
  return { w: N, h: N, svg: svg(N, N, s, 9) };
}

// ---------- banner: 2048x1152; name and mascot inside the 1235x338 strip every device shows ----------
const BW = 2048, BH = 1152, SAFE = { x: (BW - 1235) / 2, y: (BH - 338) / 2, w: 1235, h: 338 };
// the dead planet's horizon: a very wide ellipse, so the cast stands almost level across the banner
const HZ = { cx: 1024, cy: 3910, rx: 6000, ry: 3000 };
const horizon = (x) => HZ.cy - HZ.ry * Math.sqrt(1 - ((x - HZ.cx) / HZ.rx) ** 2);
function bannerCast() {
  // the episode's cast lined up like a class photo: heads in the visible strip, feet on the planet
  let s = '';
  const tag = (x, y, k, t) => g(rect(x - 64 * k, y, 128 * k, 34 * k, { rx: 6 * k, fill: '#F7F2E6', ...ink(3) }) + text(x, y + 24 * k, t, { fontFamily: 'Rubik', fontWeight: 900, fontSize: 18 * k, fill: INK, textAnchor: 'middle', letterSpacing: 1 }));
  const at = (x, lift = 0) => horizon(x) + 6 - lift;
  const L = [['nurse', 80, 1.0, 30, 9], ['jogger', 185, 1.06, 6, -8], ['cashier', 292, 1.1, 22, 7], ['guard', 398, 1.12, 0, -9]];
  for (const [o, x, k, lift, t] of L) s += zombie({ x, y: at(x, lift), s: k, outfit: o, tilt: t, look: 0.35, pose: o === 'jogger' ? 'reach' : 'stand' });
  s += zombie({ x: 508, y: at(508, -8), s: 1.18, outfit: 'suit', tilt: -6, look: 0.45, extra: tag(508 + 0.35 * 70, at(508, -8) - 3.6 * 70, 0.9, 'GARY') });
  const R = [['shopper', 1668, 1.12, 0, 8], ['park', 1772, 1.06, 18, -7], ['janitor', 1872, 1.0, 34, 9]];
  for (const [o, x, k, lift, t] of R) s += zombie({ x, y: at(x, lift), s: k, outfit: o, tilt: t, look: -0.35 });
  // Dale: the guard's own outline in shadow against a cold backlight, radio up, two pale eyes, a question mark
  const dx = 1950, dy = at(1950, 10), dk = 1.08, du = 60 * dk, fc = -1;
  s += screenGlow(dx, dy - 4.6 * du, 2.4 * du, 3.4 * du, '#7F9BD8', 0.5);
  s += `<defs><filter id="shade" x="-20%" y="-20%" width="140%" height="140%"><feColorMatrix type="matrix" values="0 0 0 0 0.03 0 0 0 0 0.035 0 0 0 0 0.06 0 0 0 1 0"/></filter></defs>`;
  const hx = dx + 0.98 * du * fc, hy = dy - 4.67 * du, rx = hx - 0.1 * du, ry = hy + 0.16 * du;
  s += g(zombie({ x: dx, y: dy, s: dk, outfit: 'guard', pose: 'talkie', facing: fc, tilt: 4, look: 0.3, filter: false,
    extra: radioProp(rx, ry, 0.29, { on: false, rot: -8 }) }), { filter: 'url(#shade)' });
  const ex = dx - 0.1 * du + 0.09 * du, ey = dy - 5.15 * du;
  s += circle(ex - 0.24 * du, ey + 0.05 * du, 0.08 * du, { fill: '#F2F0E0' }) + circle(ex + 0.24 * du, ey + 0.03 * du, 0.08 * du, { fill: '#F2F0E0' }) + glow(ex, ey, 0.6 * du, '#F2F0E0', 0.25);
  const a = (-8 * Math.PI) / 180, lx = rx + (-30 * 0.29) * Math.cos(a) - (-140 * 0.29) * Math.sin(a), ly = ry + (-30 * 0.29) * Math.sin(a) + (-140 * 0.29) * Math.cos(a);
  s += circle(lx, ly, 8, { fill: RED }) + glow(lx, ly, 34, RED, 0.9);
  s += headline(dx + 52, ey - 1.15 * du, '?', { size: 96, fill: TAPE, sw: 12, shadow: 6, rot: 10 });
  // you, right next to the name, walkie-talkie up
  s += talkieHero(1555, at(1555, -4), 1.08, { expr: 'worried', look: -0.35 });
  return s;
}
function banner() {
  let s = spaceBg(BW, BH, 33, 'bn');
  // TV-only sky: a far ringed planet, a moon, brighter stars
  s += g(circle(250, 190, 70, { fill: '#C07A5A', ...ink(5) }) + ellipse(250, 190, 120, 24, { fill: 'none', stroke: '#E8C9A0', strokeWidth: 8, transform: 'rotate(-18 250 190)' }) + circle(228, 170, 18, { fill: '#A8644A', opacity: 0.8 }), { opacity: 0.85 });
  s += circle(1820, 170, 46, { fill: '#E9E2CE', ...ink(4) }) + circle(1806, 160, 10, { fill: '#CFC6AE' }) + circle(1838, 186, 7, { fill: '#CFC6AE' });
  s += sparkle(620, 120, 26) + sparkle(1460, 250, 20, '#FFE7A8') + sparkle(1100, 90, 16, '#BFE3FF');
  // the dead planet underfoot, with Freshway on the horizon and one window still lit
  s += `<defs><radialGradient id="hz" cx="50%" cy="0%" r="55%"><stop offset="0" stop-color="#B8E07A" stop-opacity="0.5"/><stop offset="1" stop-color="#B8E07A" stop-opacity="0"/></radialGradient>
    <clipPath id="hzc"><ellipse cx="${HZ.cx}" cy="${HZ.cy}" rx="${HZ.rx}" ry="${HZ.ry}"/></clipPath></defs>`;
  s += ellipse(HZ.cx, HZ.cy - 40, HZ.rx + 120, HZ.ry + 120, { fill: 'url(#hz)', opacity: 0.6 });
  let ground = ellipse(HZ.cx, HZ.cy, HZ.rx, HZ.ry, { fill: '#6F855E' });
  for (const [x, y, r, sd] of [[300, 1040, 170, 5], [1500, 1080, 240, 8], [900, 1120, 150, 12], [1900, 1010, 120, 15]]) ground += path(blob(x, y, r, sd, 9, 0.5), { fill: '#5E744F' });
  for (const [x, y, r] of [[640, 1000, 26], [1210, 1060, 34], [1760, 1100, 22]]) ground += ellipse(x, y, r, r * 0.42, { fill: '#566B48', ...ink(4) });
  s += g(g(ground, { clipPath: 'url(#hzc)' }) + ellipse(HZ.cx, HZ.cy, HZ.rx, HZ.ry, { fill: 'none', ...ink(8) }), { filter: 'url(#wobble)' });
  const fy = horizon(1024) + 4;
  s += g(rect(944, fy - 64, 160, 64, { fill: '#4C505A', ...ink(4) }) + rect(944, fy - 74, 160, 14, { fill: '#2A2D34', ...ink(3) }) + rect(968, fy - 56, 112, 18, { rx: 3, fill: '#2F4A40', ...ink(2) })
    + text(1024, fy - 42, 'FRESHWAY', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 12, fill: '#9CC2AE', textAnchor: 'middle', letterSpacing: 2 })
    + rect(1050, fy - 30, 22, 18, { fill: '#FFD98A', ...ink(2) }), { filter: 'url(#wobbleSoft)' }) + glow(1061, fy - 21, 26, '#FFD98A', 0.8);
  s += bannerCast();
  // centre lockup: mascot + UNDEAD / ORBIT + tagline, all inside the safe strip
  const cy = SAFE.y + SAFE.h / 2;
  s += screenGlow(1024, cy, 640, 200, '#2A2060', 0.55);
  s += mascot(790, cy - 8, 116, 'bn', { look: 0.2 });
  s += headline(1000, cy - 12, 'UNDEAD', { size: 124, anchor: 'start', fill: LIME, sw: 16, shadow: 8, ls: 6 });
  s += headline(1000, cy + 106, 'ORBIT', { size: 124, anchor: 'start', fill: TAPE, sw: 16, shadow: 8, ls: 6 });
  s += text(1024, SAFE.y + SAFE.h - 14, 'ZOMBIE SURVIVAL STORIES · ANIMATED', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 26, fill: '#E9E4F5', textAnchor: 'middle', letterSpacing: 6, opacity: 0.9 });
  return { w: BW, h: BH, svg: svg(BW, BH, s, 11) };
}

export const ITEMS = { thumbA, thumbB, thumbC, logo, banner };
