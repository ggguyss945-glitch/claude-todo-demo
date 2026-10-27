// Static environments for episode shots. Every function returns plain markup with the line wobble baked in;
// shots wrap them in set(key, ...) so each variant is rasterized once.
import { W, H, INK, PAL, glow, g, rect, circle, ellipse, line, poly, path, text, ink, rng, crowd } from '../lib.js';
import { label } from './kit.js';

const wob = (s) => g(s, { filter: 'url(#wobble)' });
const box = (x, y, w, h, fill, l = '', k = 1) => rect(x, y, w, h, { fill, ...ink(4) }) + (l ? text(x + w / 2, y + h * 0.6, l, { fontFamily: 'Rubik', fontWeight: 800, fontSize: Math.min(22, h * 0.32) * k, fill: '#5A4630', textAnchor: 'middle' }) : '')
  + line(x + 4, y + h * 0.22, x + w - 4, y + h * 0.22, { stroke: '#8E6A45', strokeWidth: 2 });

// ---------- stockroom with the walk-in freezer ----------
export function stockroom({ open = false } = {}) {
  const r = rng(91);
  let s = rect(0, 0, W, H, { fill: '#B8B3A5' });
  for (let y = 0; y < 760; y += 54) for (let x = (y / 54) % 2 ? -60 : 0; x < W; x += 120) s += rect(x, y, 120, 54, { fill: 'none', stroke: '#9E998C', strokeWidth: 3 });
  s += rect(0, 760, W, 320, { fill: '#9C978A' }) + line(0, 760, W, 760, ink(5));
  for (let i = 0; i < 9; i++) s += ellipse(200 + r() * 1500, 820 + r() * 220, 60 + r() * 90, 14 + r() * 14, { fill: '#8C877B', opacity: 0.6 });
  // tall shelving units on the left
  const unit = (x0, w) => {
    let o = '';
    for (const ux of [x0, x0 + w]) o += rect(ux - 12, 120, 24, 660, { fill: '#C76A3A', ...ink(4) });
    for (const y of [250, 420, 590, 760]) o += rect(x0 - 12, y - 18, w + 24, 18, { fill: '#3E6E9A', ...ink(4) });
    const items = ['PEAS', 'SOUP', 'TOWELS', 'BEANS', 'RICE', 'CORN'];
    for (const [i, y] of [250, 420, 590, 760].entries()) {
      let x = x0 + 14;
      while (x < x0 + w - 90) { const bw = 90 + r() * 70, bh = 80 + r() * 60; if (y === 250 && r() < 0.3) { x += bw; continue; } o += box(x, y - 18 - bh, Math.min(bw, x0 + w - 14 - x), bh, ['#B58759', '#C49A6C', '#A87B4F'][Math.floor(r() * 3)], items[Math.floor(r() * 6)]); x += bw + 6; }
    }
    return o;
  };
  s += unit(60, 460) + unit(600, 420);
  s += label(310, 300, '', 20);
  // walk-in freezer front
  s += rect(1110, 150, 790, 620, { fill: '#C9CDD0', ...ink(6) });
  for (let x = 1130; x < 1890; x += 70) s += line(x, 160, x, 760, { stroke: '#B2B7BB', strokeWidth: 3 });
  s += rect(1110, 150, 790, 46, { fill: '#AEB4B9', ...ink(5) }) + label(1505, 183, 'WALK-IN FREEZER  ·  KEEP CLOSED', 22, '#3E4A55');
  const dx = 1300, dy = 230, dw = 380, dh = 535;
  if (open) {
    s += rect(dx, dy, dw, dh, { fill: '#5E7F99', ...ink(6) });
    for (const y of [330, 450, 570]) s += rect(dx + 20, y, dw - 40, 12, { fill: '#9DB6C8', ...ink(3) }) + rect(dx + 40, y - 60, 90, 60, { fill: '#D9E6EE', ...ink(3) }) + rect(dx + 160, y - 48, 120, 48, { fill: '#C1D3DF', ...ink(3) });
    for (let i = 0; i < 9; i++) s += rect(dx + 8 + i * 41, dy + 4, 30, 260, { fill: '#DCEAF2', opacity: 0.35, stroke: '#9DB6C8', strokeWidth: 2 });
    // door swung open toward the camera
    s += poly([[dx + dw, dy - 6], [dx + dw + 250, dy - 40], [dx + dw + 250, dy + dh + 60], [dx + dw, dy + dh + 4]], { fill: '#D5D9DC', ...ink(6) });
    s += rect(dx + dw + 190, dy + 220, 24, 120, { rx: 10, fill: '#8E9499', ...ink(4) });
  } else {
    s += rect(dx, dy, dw, dh, { fill: '#D5D9DC', ...ink(6) });
    s += rect(dx + 120, dy + 70, 140, 110, { rx: 8, fill: '#9CB4C4', ...ink(5) }) + path(`M${dx + 135} ${dy + 160} q40 -40 70 -10 t40 -30`, { fill: 'none', stroke: '#E9F2F6', strokeWidth: 6, opacity: 0.8 });
    s += rect(dx + 300, dy + 210, 34, 150, { rx: 12, fill: '#8E9499', ...ink(5) });
  }
  s += rect(1730, 300, 120, 70, { rx: 8, fill: '#2B2F33', ...ink(4) }) + text(1790, 347, '-18°C', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 30, fill: '#8FE3FF', textAnchor: 'middle' });
  s += rect(1240, 765, 520, 14, { fill: '#7C8388', ...ink(3) });
  // emergency light over the door
  s += rect(860, 40, 150, 44, { rx: 8, fill: '#E9E2CF', ...ink(4) }) + circle(900, 62, 12, { fill: '#F6EBC0', ...ink(3) }) + circle(970, 62, 12, { fill: '#F6EBC0', ...ink(3) });
  return wob(s);
}

// ---------- the manager's office ----------
export function office() {
  const r = rng(17);
  let s = rect(0, 0, W, H, { fill: '#D6CBB4' });
  s += rect(0, 0, W, 70, { fill: '#C9BEA6' }) + line(0, 70, W, 70, ink(4));
  for (let x = 0; x < W; x += 160) s += rect(x, 0, 158, 68, { fill: 'none', stroke: '#B8AD95', strokeWidth: 2 });
  s += rect(0, 820, W, 260, { fill: '#6F757C' }) + line(0, 820, W, 820, ink(5));
  for (let i = 0; i < 30; i++) s += rect(r() * W, 840 + r() * 230, 40, 3, { fill: '#5E646B' });
  // door frame on the left, open, dark store beyond
  s += rect(70, 180, 270, 640, { fill: '#2E3646', ...ink(6) }) + rect(55, 165, 300, 18, { fill: '#9C8467', ...ink(4) });
  s += rect(90, 560, 50, 260, { fill: '#3A4252' }) + rect(250, 600, 70, 220, { fill: '#384050' });
  // wall clock
  s += circle(760, 290, 96, { fill: '#F4F0E6', ...ink(7) }) + circle(760, 290, 8, { fill: INK });
  for (let i = 0; i < 12; i++) { const a = i * Math.PI / 6; s += line(760 + Math.cos(a) * 78, 290 + Math.sin(a) * 78, 760 + Math.cos(a) * 88, 290 + Math.sin(a) * 88, ink(4)); }
  // corkboard with the staff schedule
  s += rect(420, 200, 220, 170, { fill: '#B98B5E', ...ink(5) });
  for (let i = 0; i < 6; i++) s += rect(436 + (i % 3) * 66, 214 + Math.floor(i / 3) * 76, 56, 64, { fill: ['#FBF6EA', '#F6E9A8', '#F2D2C8'][i % 3], ...ink(2), transform: `rotate(${(r() - 0.5) * 8} ${466 + (i % 3) * 66} ${246 + Math.floor(i / 3) * 76})` });
  s += label(530, 395, 'NIGHT SHIFT', 16, '#6B5F55');
  // framed certificate
  s += rect(940, 210, 170, 130, { fill: '#F7F1E1', ...ink(5) }) + rect(952, 222, 146, 106, { fill: 'none', stroke: '#C9A43A', strokeWidth: 4 }) + label(1025, 262, 'MANAGER', 16, INK) + label(1025, 288, 'OF THE MONTH', 13, INK) + label(1025, 316, 'G. PRUITT', 14, PAL.red);
  // CCTV stack
  s += rect(1180, 150, 330, 300, { fill: '#3A3D42', ...ink(6) });
  for (let i = 0; i < 6; i++) {
    const mx = 1195 + (i % 3) * 105, my = 165 + Math.floor(i / 3) * 140;
    s += rect(mx, my, 95, 125, { fill: '#5E7564', ...ink(3) }) + rect(mx + 6, my + 6, 83, 80, { fill: '#7E9A86' });
    for (let k = 0; k < 4; k++) s += circle(mx + 18 + k * 18 + r() * 6, my + 60 + r() * 14, 6, { fill: '#3E5446' });
    s += label(mx + 46, my + 112, `CAM ${i + 1}`, 12, '#C9D8CC');
  }
  // the control panel
  s += rect(1580, 300, 240, 330, { rx: 10, fill: '#9AA0A6', ...ink(6) }) + rect(1580, 300, 240, 50, { rx: 10, fill: '#7C8288', ...ink(5) });
  s += label(1700, 334, 'STORE SCHEDULE', 18, '#F2F2EE');
  s += label(1622, 400, 'DOORS', 14, '#2B2F33', 'start') + label(1622, 460, 'LIGHTS', 14, '#2B2F33', 'start');
  s += rect(1730, 380, 60, 30, { rx: 6, fill: '#E9E5DC', ...ink(3) }) + rect(1730, 440, 60, 30, { rx: 6, fill: '#E9E5DC', ...ink(3) });
  s += label(1700, 610, 'OPEN · · · · CLOSED', 13, '#2B2F33');
  // music box next to it, with its own timer
  s += rect(1600, 690, 200, 100, { rx: 8, fill: '#5A5F66', ...ink(5) }) + label(1700, 724, 'MUSIC · AUTO', 15, '#E9E5DC') + rect(1640, 740, 120, 32, { rx: 4, fill: '#202326', ...ink(3) }) + text(1700, 765, '7:00', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 22, fill: '#9CFF8A', textAnchor: 'middle' });
  s += path('M1800 760 C1860 760 1870 820 1880 1080', { fill: 'none', stroke: '#1E1A1A', strokeWidth: 12 });
  // ceiling speaker
  s += circle(980, 70, 54, { fill: '#EDEAE2', ...ink(5) }); for (let i = 0; i < 4; i++) s += circle(980, 70, 12 + i * 10, { fill: 'none', stroke: '#B8B3A8', strokeWidth: 3 });
  // desk
  s += rect(430, 640, 760, 70, { fill: '#9B6E45', ...ink(6) }) + rect(450, 710, 30, 150, { fill: '#7F5634', ...ink(5) }) + rect(1140, 710, 30, 150, { fill: '#7F5634', ...ink(5) });
  s += rect(500, 520, 200, 125, { rx: 6, fill: '#2E3135', ...ink(5) }) + rect(512, 532, 176, 96, { fill: '#41505A' }) + rect(580, 640, 40, 10, { fill: '#2E3135' });
  s += rect(760, 600, 160, 40, { fill: '#F7F2E6', ...ink(3), transform: 'rotate(-4 840 620)' }) + rect(940, 590, 64, 50, { rx: 8, fill: '#F7F2E6', ...ink(4) }) + label(972, 622, '#1', 16, PAL.red);
  return wob(s);
}
// manager's office door seen from the back corridor
export function officeDoor({ dawn = false } = {}) {
  let s = rect(0, 0, W, H, { fill: dawn ? '#B7B4A8' : '#9C998F' }) + rect(0, 860, W, 220, { fill: dawn ? '#A8A091' : '#8B8476' }) + line(0, 860, W, 860, ink(5));
  for (let x = 0; x < W; x += 240) s += line(x, 0, x, 860, { stroke: '#8F8C83', strokeWidth: 2 });
  s += rect(680, 150, 560, 710, { fill: '#8A6A4A', ...ink(7) }) + rect(660, 130, 600, 24, { fill: '#6E5238', ...ink(5) });
  s += rect(770, 230, 380, 300, { rx: 6, fill: '#D9DCD6', ...ink(6) });
  s += rect(840, 580, 240, 60, { rx: 6, fill: '#E9DDBF', ...ink(4) }) + label(960, 610, 'MANAGER', 22, INK) + label(960, 632, 'G. PRUITT', 15, '#6B5F55');
  s += rect(1130, 650, 70, 26, { rx: 10, fill: '#C9A43A', ...ink(4) }) + circle(1150, 700, 9, { fill: INK });
  s += rect(1380, 380, 250, 120, { fill: '#F2EEE2', ...ink(4) }) + label(1505, 430, 'STAFF ONLY', 24, PAL.red) + label(1505, 470, 'BEYOND THIS POINT', 14, '#6B5F55');
  return wob(s);
}

// ---------- front entrance from inside: glass doors, crowd beyond ----------
export function doorsOutside({ dawn = true } = {}) {
  let s = rect(0, 0, W, H, { fill: dawn ? '#E3C9B4' : '#9FB3C2' }) + rect(0, 0, W, 300, { fill: dawn ? '#D6A9A0' : '#8AA3B6', opacity: 0.6 });
  s += rect(0, 560, W, 520, { fill: '#6E7178' });
  for (let x = -200; x < W + 200; x += 260) s += line(x, 1080, x + 160, 620, { stroke: '#E9E2C8', strokeWidth: 6, opacity: 0.45 });
  s += rect(200, 440, 260, 120, { rx: 30, fill: '#8E5B4A', ...ink(5) }) + rect(1500, 450, 300, 110, { rx: 30, fill: '#5C6E86', ...ink(5) });
  return wob(s);
}
export function doorsInside() {
  let s = '';
  s += path(`M0 0 H${W} V1080 H0 Z M560 230 H1360 V990 H560 Z`, { fill: '#D8D2C4', fillRule: 'evenodd', ...ink(6) });
  s += rect(0, 990, W, 90, { fill: '#D9CDB2' }) + line(0, 990, W, 990, ink(5));
  for (let x = 0; x < W; x += 160) s += line(x, 990, x + (x - 960) * 0.4, 1080, { stroke: '#BDB096', strokeWidth: 3 });
  s += rect(540, 210, 840, 40, { fill: '#8E9499', ...ink(5) }) + rect(540, 210, 30, 790, { fill: '#8E9499', ...ink(5) }) + rect(1350, 210, 30, 790, { fill: '#8E9499', ...ink(5) }) + rect(948, 250, 24, 740, { fill: '#8E9499', ...ink(4) });
  s += rect(560, 250, 388, 740, { fill: '#BFD6E0', opacity: 0.18 }) + rect(972, 250, 388, 740, { fill: '#BFD6E0', opacity: 0.18 });
  s += path('M600 300 l120 -40 M620 360 l160 -60', { stroke: '#FFFFFF', strokeWidth: 8, opacity: 0.35 }) + path('M1010 300 l120 -40', { stroke: '#FFFFFF', strokeWidth: 8, opacity: 0.35 });
  s += rect(700, 620, 160, 56, { rx: 8, fill: '#3E6E5A', opacity: 0.9, ...ink(3) }) + label(780, 657, 'ENTER', 22, '#F5EFE0') + rect(1060, 620, 160, 56, { rx: 8, fill: '#3E6E5A', opacity: 0.9, ...ink(3) }) + label(1140, 657, 'ENTER', 22, '#F5EFE0');
  s += rect(860, 120, 200, 70, { rx: 10, fill: '#3E6E5A', ...ink(5) }) + label(960, 165, 'FRESHWAY', 28, '#F5EFE0', 'middle', 4);
  // checkout lanes in the foreground
  for (const [x, n] of [[40, 3], [1600, 4]]) {
    s += rect(x, 640, 280, 360, { fill: '#B9B2A1', ...ink(6) }) + rect(x, 610, 280, 40, { fill: '#5E6B3A', ...ink(5) });
    s += line(x + 240, 610, x + 240, 420, ink(6)) + rect(x + 205, 360, 70, 70, { rx: 10, fill: '#F2EEE2', ...ink(4) }) + label(x + 240, 410, String(n), 40, INK);
  }
  return wob(s);
}

// ---------- security desk with the radio charging dock ----------
export function securityDesk() {
  let s = rect(0, 0, W, H, { fill: '#CFC7B4' }) + rect(0, 0, W, 90, { fill: '#BDB49F' });
  s += rect(560, 120, 800, 120, { rx: 8, fill: '#2E3D55', ...ink(6) }) + label(960, 200, 'SECURITY', 66, '#F2EEE2', 'middle', 10);
  s += rect(1500, 300, 260, 340, { fill: '#F2EEE2', ...ink(5) }) + label(1630, 350, 'SHIFT LOG', 22, INK);
  for (let i = 0; i < 7; i++) s += line(1530, 390 + i * 32, 1730 - (i % 3) * 40, 390 + i * 32, { stroke: '#8E8576', strokeWidth: 3 });
  s += rect(0, 640, W, 440, { fill: '#7A5C40', ...ink(6) }) + rect(0, 620, W, 40, { fill: '#9B7A57', ...ink(5) });
  s += rect(260, 380, 360, 250, { rx: 8, fill: '#2E3135', ...ink(6) }) + rect(276, 396, 328, 190, { fill: '#5E7564' }) + rect(410, 630, 60, 20, { fill: '#2E3135' });
  s += rect(1180, 560, 120, 70, { rx: 6, fill: '#F2EEE2', ...ink(4) });
  return wob(s);
}
export function dockBase(x, y, k = 1) {
  let s = rect(x - 170 * k, y, 340 * k, 70 * k, { rx: 12 * k, fill: '#232527', ...ink(5) });
  for (const [i, dx] of [[1, -85], [2, 85]]) {
    s += rect(x + (dx - 60) * k, y - 30 * k, 120 * k, 40 * k, { rx: 8 * k, fill: '#141516', ...ink(4) });
    s += text(x + dx * k, y + 50 * k, `SLOT ${i}`, { fontFamily: 'Rubik', fontWeight: 800, fontSize: 18 * k, fill: '#9C9890', textAnchor: 'middle', letterSpacing: 2 });
  }
  return s;
}

// ---------- fire exit at the back corridor ----------
export function fireExit({ stage = 'bare', open = 0 } = {}) {
  const r = rng(5);
  let s = rect(0, 0, W, H, { fill: '#BDB7A6' });
  for (let y = 0; y < 820; y += 60) for (let x = (y / 60) % 2 ? -70 : 0; x < W; x += 140) s += rect(x, y, 140, 60, { fill: 'none', stroke: '#A8A291', strokeWidth: 3 });
  s += rect(0, 820, W, 260, { fill: '#8F8A7E' }) + line(0, 820, W, 820, ink(5));
  s += rect(690, 170, 540, 650, { fill: '#55575A', ...ink(6) });
  // the door (slightly ajar when pushed from outside)
  const door = rect(710, 190, 500, 630, { fill: '#8E3B2F', ...ink(6) }) + rect(760, 470, 400, 40, { rx: 14, fill: '#C9C3B5', ...ink(5) }) + rect(860, 240, 200, 150, { fill: '#7E8B90', ...ink(4) })
    + path('M860 280 L1060 280 M860 330 L1060 330 M900 240 L900 390 M960 240 L960 390 M1020 240 L1020 390', { stroke: '#5E6A70', strokeWidth: 3 });
  s += open ? g(door, { transform: `translate(${710} 0) scale(${(1 - open * 0.05).toFixed(3)} 1) translate(-710 0)` }) + rect(1210 - open * 25, 190, open * 25, 630, { fill: '#0E0F12' }) : door;
  // maglock bar on the frame
  s += rect(860, 150, 200, 34, { rx: 4, fill: '#C9CDD0', ...ink(4) });
  s += rect(760, 60, 400, 70, { rx: 8, fill: '#B5452F', ...ink(5) }) + label(960, 92, 'EMERGENCY EXIT ONLY', 24, '#FFF') + label(960, 118, 'ALARM WILL SOUND', 16, '#F6D9CF');
  if (stage !== 'bare') {
    // water pallets on the sides
    for (const px of [480, 1250]) {
      s += rect(px, 700, 220, 30, { fill: '#9B7A57', ...ink(4) });
      for (let row = 0; row < 4; row++) for (let i = 0; i < 4; i++) s += rect(px + 8 + i * 52, 650 - row * 70, 46, 66, { rx: 10, fill: '#BFDDEB', ...ink(3) }) + rect(px + 20 + i * 52, 636 - row * 70, 22, 16, { fill: '#3E6E9A', ...ink(2) });
      s += rect(px, 350, 220, 352, { fill: '#E9F4F8', opacity: 0.25, stroke: '#9DB6C8', strokeWidth: 3 });
    }
    // dog food bags stacked against the door
    for (let row = 0; row < 5; row++) for (let i = 0; i < 4 - (row > 2 ? 1 : 0); i++) {
      const bx = 720 + i * 125 + (row % 2) * 60 + (r() - 0.5) * 10, by = 760 - row * 95;
      s += g(rect(-70, -45, 140, 90, { rx: 26, fill: '#B88A4E', ...ink(5) }) + rect(-46, -20, 92, 40, { rx: 6, fill: '#E9C77A', ...ink(3) }) + text(0, 8, 'WOOF', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 22, fill: '#7A4A22', textAnchor: 'middle' }),
        { transform: `translate(${bx} ${by}) rotate(${(r() - 0.5) * 10})` });
    }
    if (stage === 'done') {
      // patio chairs on top
      for (const [cx, rot] of [[820, -12], [1010, 8], [1180, -4]]) s += g(path('M-60 0 h120 l10 -90 h-140 z', { fill: '#F2F0EA', ...ink(5) }) + line(-50, 0, -60, 80, ink(7)) + line(50, 0, 60, 80, ink(7)) + rect(-60, -160, 120, 70, { rx: 10, fill: '#F2F0EA', ...ink(5) }),
        { transform: `translate(${cx} 300) rotate(${rot})` });
      s += rect(1300, 820, 240, 60, { rx: 6, fill: '#E9C77A', ...ink(4) }) + label(1420, 860, '50% OFF', 24, PAL.red);
    }
  }
  return wob(s);
}

// ---------- roof of the store, mall across the street ----------
export function sky(time) {
  const st = { sunset: ['#F4B16E', '#C96D6A', '#5D4470'], night: ['#28324A', '#1E2639', '#141A28'], day: ['#BFD9E6', '#A9C7D9', '#8FB3CA'] }[time];
  let s = `<linearGradient id="sky_${time}" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="${st[0]}"/><stop offset="0.5" stop-color="${st[1]}"/><stop offset="1" stop-color="${st[2]}"/></linearGradient>`;
  s += rect(0, 0, W, H, { fill: `url(#sky_${time})` });
  if (time === 'night') { const r = rng(3); for (let i = 0; i < 90; i++) s += circle(r() * W, r() * 420, 1 + r() * 2, { fill: '#F3EBDD', opacity: 0.4 + r() * 0.6 }); s += circle(1680, 130, 50, { fill: '#F1E9D2' }) + circle(1660, 120, 50, { fill: '#28324A', opacity: 0.3 }); }
  if (time === 'sunset') s += circle(420, 500, 120, { fill: '#FFD79A', opacity: 0.9 });
  return s;
}
export function mallFacade({ time = 'sunset', x = 1080, y = 120, k = 1, lit = true } = {}) {
  let s = rect(x, y, 760 * k, 420 * k, { fill: time === 'night' ? '#3A4256' : '#B9AE9C', ...ink(6) });
  s += rect(x, y, 760 * k, 70 * k, { fill: time === 'night' ? '#2E3446' : '#8C7F6C', ...ink(5) });
  s += text(x + 380 * k, y + 50 * k, 'BROOKFIELD MALL', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 40 * k, fill: time === 'night' ? '#7A6E64' : '#B5452F', textAnchor: 'middle', letterSpacing: 4 });
  for (let fl = 0; fl < 4; fl++) for (let i = 0; i < 9; i++) {
    const wx = x + 30 * k + i * 80 * k, wy = y + 95 * k + fl * 78 * k, isLit = lit && fl === 0 && i === 6;
    s += rect(wx, wy, 56 * k, 50 * k, { fill: isLit ? '#FFD98A' : (time === 'night' ? '#1E2433' : '#5E6B78'), ...ink(3) });
  }
  return s;
}
export function cityBand(time) {
  const r = rng(12); let s = '';
  for (let x = -40; x < W; x += 95) { const h = 90 + r() * 220; s += rect(x, 560 - h, 90, h, { fill: time === 'night' ? '#1B2131' : time === 'sunset' ? '#6E4E6A' : '#8EA2B4', ...ink(3) }); }
  return s;
}
export function roofSet({ time = 'sunset', hvacDoor = 'ajar' } = {}) {
  let s = sky(time) + cityBand(time) + mallFacade({ time, x: 1060, y: 200, k: 0.95 });
  // the parking lot far below, seen past the parapet
  s += rect(0, 560, W, 160, { fill: time === 'night' ? '#2E323C' : '#5E616A' });
  for (let x = -100; x < W; x += 120) s += line(x, 720, x + 60, 570, { stroke: '#E9E2C8', strokeWidth: 3, opacity: 0.35 });
  s += crowd({ x0: 40, x1: 1880, y: 700, rows: 3, n: 46, s: 0.16, seed: 21, spread: 32 });
  // roof deck
  s += poly([[0, 720], [W, 720], [W, H], [0, H]], { fill: time === 'night' ? '#4B4A4E' : '#8F8A80', ...ink(5) });
  const r = rng(33); for (let i = 0; i < 220; i++) s += circle(r() * W, 735 + r() * 345, 2 + r() * 2.5, { fill: time === 'night' ? '#3A393D' : '#7E796F' });
  s += rect(0, 700, W, 30, { fill: time === 'night' ? '#5A5960' : '#A39E93', ...ink(5) });
  // HVAC units and the mechanical room
  for (const [hx, hy] of [[120, 760], [1520, 770]]) { s += rect(hx, hy, 260, 150, { rx: 8, fill: '#B7BBBE', ...ink(5) }) + circle(hx + 80, hy + 75, 50, { fill: '#8E9499', ...ink(4) }) + circle(hx + 190, hy + 75, 40, { fill: '#8E9499', ...ink(4) }); }
  s += rect(1180, 560, 280, 200, { fill: '#A8A296', ...ink(6) }) + poly([[1170, 565], [1470, 565], [1450, 530], [1190, 530]], { fill: '#8C867A', ...ink(5) });
  s += rect(1250, 620, 110, 140, { fill: hvacDoor === 'ajar' ? '#2E2A2A' : '#7E786C', ...ink(5) });
  if (hvacDoor === 'ajar') s += poly([[1250, 620], [1220, 610], [1220, 772], [1250, 760]], { fill: '#7E786C', ...ink(4) });
  s += label(1320, 600, 'MECH', 18, '#4A463E');
  // roof hatch
  s += poly([[700, 900], [940, 900], [980, 1000], [660, 1000]], { fill: '#3A3836', ...ink(5) }) + poly([[700, 900], [940, 900], [930, 780], [710, 780]], { fill: '#9C968A', ...ink(5) });
  return wob(s);
}

// ---------- parking lot seen from above (the roof) ----------
export function lotSet({ time = 'night' } = {}) {
  let s = sky(time) + cityBand(time) + mallFacade({ time, x: 1180, y: 60, k: 0.85 });
  s += rect(0, 420, W, 660, { fill: time === 'night' ? '#30343E' : time === 'sunset' ? '#6A6066' : '#666A72' });
  for (let row = 0; row < 4; row++) for (let x = -100; x < W + 100; x += 150) {
    const y0 = 470 + row * 160; s += line(x + row * 30, y0, x + row * 30 + 40, y0 + 120, { stroke: '#E9E2C8', strokeWidth: 4, opacity: 0.35 });
  }
  const r = rng(9);
  for (let i = 0; i < 9; i++) { const cx = 120 + r() * 1650, cy = 480 + r() * 520, c = ['#8E5B4A', '#5C6E86', '#7A7A6E', '#A0453A'][i % 4]; s += rect(cx, cy, 150, 70, { rx: 24, fill: c, ...ink(5) }) + rect(cx + 30, cy - 26, 90, 36, { rx: 12, fill: '#9FB3C2', ...ink(4) }); }
  for (const lx of [300, 980, 1660]) s += line(lx, 1000, lx, 470, ink(9)) + rect(lx - 50, 460, 100, 18, { fill: '#C9C3B5', ...ink(4) });
  // the store's front edge at the bottom
  s += rect(0, 1010, W, 70, { fill: '#5A5960', ...ink(5) });
  return wob(s);
}

// ---------- camping aisle where you sleep ----------
export function campAisle({ time = 'night' } = {}) {
  const r = rng(41);
  let s = rect(0, 0, W, H, { fill: '#C9C2AE' }) + rect(0, 860, W, 220, { fill: '#B3A88E' }) + line(0, 860, W, 860, ink(5));
  for (const y of [260, 470, 680]) {
    s += rect(0, y, W, 20, { fill: '#8E877A', ...ink(4) });
    let x = 20; while (x < W - 100) { const w = 110 + r() * 80, h = 110 + r() * 60, c = ['#3E6E5A', '#C76A3A', '#3E6E9A', '#D4AE52', '#7A5C40'][Math.floor(r() * 5)]; s += rect(x, y - h, w, h, { fill: c, ...ink(3) }) + rect(x + 10, y - h * 0.7, w - 20, h * 0.3, { fill: '#F3EEDF', opacity: 0.8 }); x += w + 8; }
  }
  s += rect(1360, 40, 440, 110, { rx: 10, fill: PAL.yellow, ...ink(5) }) + label(1580, 100, 'AISLE 9', 40, INK) + label(1580, 136, 'CAMPING & OUTDOORS', 20, INK);
  // tent, chair, sleeping bag
  s += path('M560 860 L860 520 L1160 860 Z', { fill: '#E07A3A', ...ink(7) }) + path('M860 520 L860 860', ink(5)) + path('M760 860 Q860 700 960 860 Z', { fill: '#2B2622', ...ink(5) });
  s += line(860, 520, 860, 470, ink(6)) + path('M860 470 l60 18 l-60 18', { fill: PAL.red, ...ink(3) });
  s += rect(260, 830, 280, 50, { rx: 24, fill: '#3E6E9A', ...ink(5) });
  for (const [cx, n] of [[1290, 3], [1350, 2]]) for (let i = 0; i < n; i++) s += rect(cx + i * 10, 800 - i * 50, 50, 48, { rx: 6, fill: '#E9B93E', ...ink(3) }) + rect(cx + i * 10, 816 - i * 50, 50, 16, { fill: '#F3EEDF' });
  return wob(s);
}

// ---------- outside walls ----------
export function staffWall({ time = 'night' } = {}) {
  let s = rect(0, 0, W, H, { fill: '#1F2638' }) + rect(0, 120, W, 760, { fill: '#8C8578', ...ink(6) });
  for (let y = 140; y < 880; y += 50) for (let x = (y / 50) % 2 ? -60 : 0; x < W; x += 120) s += rect(x, y, 120, 50, { fill: 'none', stroke: '#777064', strokeWidth: 3 });
  s += rect(0, 880, W, 200, { fill: '#3A3D44' });
  s += rect(760, 380, 380, 500, { fill: '#6E747A', ...ink(7) }) + rect(780, 400, 340, 480, { fill: '#7E858C', ...ink(5) });
  s += rect(840, 450, 220, 70, { rx: 6, fill: '#E9E5DC', ...ink(4) }) + label(950, 497, 'STAFF ONLY', 30, PAL.red);
  s += rect(1060, 640, 40, 80, { rx: 6, fill: '#C9C3B5', ...ink(4) }) + circle(1080, 668, 10, { fill: INK });
  s += rect(910, 300, 100, 40, { rx: 6, fill: '#C9C3B5', ...ink(4) });
  s += rect(1300, 300, 400, 160, { fill: '#2E3A4E', ...ink(5) }) + rect(200, 300, 400, 160, { fill: '#2E3A4E', ...ink(5) });
  return wob(s);
}
export function dockExterior() {
  let s = sky('day') + rect(0, 140, W, 600, { fill: '#B7AE9C', ...ink(6) }) + rect(0, 120, W, 40, { fill: '#8C8578', ...ink(5) });
  s += rect(260, 300, 520, 440, { fill: '#9AA0A6', ...ink(6) });
  for (let y = 320; y < 740; y += 26) s += line(260, y, 780, y, { stroke: '#7C8288', strokeWidth: 3 });
  s += label(520, 280, 'RECEIVING', 30, '#4A463E', 'middle', 6);
  s += rect(1100, 360, 230, 380, { fill: '#8E3B2F', ...ink(6) }) + rect(1100, 330, 230, 30, { fill: '#C9CDD0', ...ink(4) }) + label(1215, 320, 'FIRE EXIT', 22, '#4A463E');
  s += rect(0, 740, W, 120, { fill: '#9C968A', ...ink(5) }) + rect(0, 860, W, 220, { fill: '#5E616A' });
  s += rect(1480, 600, 300, 160, { rx: 10, fill: '#3E6E5A', ...ink(6) }) + rect(1470, 590, 320, 30, { fill: '#2F5546', ...ink(4) });
  return wob(s);
}
export function skyline() {
  let s = sky('day') + cityBand('day');
  s += rect(0, 560, W, 520, { fill: '#8FA07A' });
  s += path('M1220 560 L1260 330 L1420 330 L1460 560 Z', { fill: '#C9C3B5', ...ink(6) }) + path('M1480 560 L1500 260 L1540 260 L1560 560 Z', { fill: '#A8A296', ...ink(5) }) + path('M1580 560 L1595 300 L1625 300 L1640 560 Z', { fill: '#A8A296', ...ink(5) });
  s += rect(1180, 470, 520, 90, { fill: '#9C968A', ...ink(5) });
  for (const tx of [180, 560, 940]) s += path(`M${tx} 900 L${tx + 50} 520 L${tx + 100} 900 M${tx + 15} 640 h70 M${tx + 25} 580 h50`, { fill: 'none', ...ink(6) });
  s += path('M180 600 Q370 650 560 600 Q750 650 940 600 Q1080 640 1220 600', { fill: 'none', stroke: INK, strokeWidth: 3 });
  return wob(s);
}
