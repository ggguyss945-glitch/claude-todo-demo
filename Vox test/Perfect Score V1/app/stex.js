// School / home textures, all painted on canvases (no image files).
import * as THREE from 'three';
import { canvas, toTex, noiseFill } from './tex.js';
import { rng } from './util.js';

const memo = new Map();
function once(key, fn) { if (!memo.has(key)) memo.set(key, fn()); return memo.get(key); }

// speckled vinyl floor tiles (classroom) with a slight sheen variation per tile
export function vinylTiles(base = '#c9bfa8', seed = 3, n = 4, repeat = [6, 6]) {
  return once('vinyl' + base + seed + repeat, () => {
    const S = 1024, T = S / n;
    const [c, g] = canvas(S, S);
    const r = rng(seed);
    for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
      const k = (r() - 0.5) * 14;
      g.fillStyle = shiftHex(base, k);
      g.fillRect(x * T, y * T, T, T);
    }
    for (let i = 0; i < 9000; i++) { // terrazzo-like flecks
      g.fillStyle = r() < 0.5 ? 'rgba(90,80,70,0.35)' : 'rgba(255,255,255,0.3)';
      const s = 1 + r() * 2.5;
      g.fillRect(r() * S, r() * S, s, s);
    }
    g.strokeStyle = 'rgba(60,50,40,0.35)'; g.lineWidth = 2;
    for (let i = 0; i <= n; i++) { g.beginPath(); g.moveTo(i * T, 0); g.lineTo(i * T, S); g.stroke(); g.beginPath(); g.moveTo(0, i * T); g.lineTo(S, i * T); g.stroke(); }
    noiseFill(g, S, S, 0, 8, seed + 1, 2);
    return toTex(c, { repeat });
  });
}

// glossy checkerboard corridor tiles
export function checkerTiles(a = '#d8d2c4', b = '#7a3a2a', repeat = [3, 16]) {
  return once('check' + a + b + repeat, () => {
    const S = 512, T = S / 4;
    const [c, g] = canvas(S, S);
    for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) {
      g.fillStyle = (x + y) % 2 ? a : b;
      g.fillRect(x * T, y * T, T, T);
    }
    noiseFill(g, S, S, 0, 10, 5, 1);
    g.strokeStyle = 'rgba(40,30,20,0.4)'; g.lineWidth = 2;
    for (let i = 0; i <= 4; i++) { g.beginPath(); g.moveTo(i * T, 0); g.lineTo(i * T, S); g.stroke(); g.beginPath(); g.moveTo(0, i * T); g.lineTo(S, i * T); g.stroke(); }
    return toTex(c, { repeat });
  });
}

// painted plaster wall with a darker wainscot band and a chair rail
export function schoolWall(top = '#e8dcc0', bottom = '#5f7f6a', railY = 0.34, repeat = [4, 1]) {
  return once('wall' + top + bottom + railY + repeat, () => {
    const W = 1024, H = 1024;
    const [c, g] = canvas(W, H);
    g.fillStyle = top; g.fillRect(0, 0, W, H);
    noiseFill(g, W, H, 0, 7, 21, 2);
    const ry = H * (1 - railY);
    g.fillStyle = bottom; g.fillRect(0, ry, W, H - ry);
    noiseFill(g, W, H, 0, 4, 22, 1);
    g.fillStyle = 'rgba(255,255,255,0.35)'; g.fillRect(0, ry - 14, W, 6);
    g.fillStyle = shiftHex(bottom, -30); g.fillRect(0, ry - 8, W, 12);
    g.fillStyle = 'rgba(0,0,0,0.25)'; g.fillRect(0, ry + 4, W, 4);
    g.fillStyle = '#3a2a20'; g.fillRect(0, H - 26, W, 26); // skirting
    const grd = g.createLinearGradient(0, 0, 0, H * 0.25);
    grd.addColorStop(0, 'rgba(0,0,0,0.12)'); grd.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = grd; g.fillRect(0, 0, W, H * 0.25);
    return toTex(c, { repeat });
  });
}

// vertical tongue-and-groove planks (the orange wood office of the reference)
export function plankWall(base = '#b86a2c', repeat = [3, 1]) {
  return once('plank' + base + repeat, () => {
    const W = 1024, H = 1024;
    const [c, g] = canvas(W, H);
    const r = rng(41);
    const pw = W / 8;
    for (let i = 0; i < 8; i++) {
      g.fillStyle = shiftHex(base, (r() - 0.5) * 26);
      g.fillRect(i * pw, 0, pw, H);
      for (let k = 0; k < 26; k++) {
        const x = i * pw + r() * pw;
        g.strokeStyle = `rgba(${r() < 0.6 ? '60,25,5' : '255,200,140'},${0.08 + r() * 0.14})`;
        g.lineWidth = 1 + r() * 3;
        g.beginPath(); g.moveTo(x, 0);
        for (let y = 0; y <= H; y += 32) g.lineTo(x + Math.sin(y * 0.006 + k + i) * 4, y);
        g.stroke();
      }
      if (r() < 0.5) { // knots
        g.fillStyle = 'rgba(70,30,8,0.4)';
        g.beginPath(); g.ellipse(i * pw + pw * (0.3 + r() * 0.4), r() * H, 6 + r() * 5, 14 + r() * 8, 0, 0, Math.PI * 2); g.fill();
      }
      g.fillStyle = 'rgba(30,10,0,0.75)'; g.fillRect(i * pw, 0, 4, H); // groove
      g.fillStyle = 'rgba(255,210,160,0.18)'; g.fillRect(i * pw + 4, 0, 3, H);
    }
    noiseFill(g, W, H, 0, 8, 42, 2);
    return toTex(c, { repeat });
  });
}

// damask wallpaper (the reference's living room)
export function damask(base = '#7a2a22', ink = '#4a1410', repeat = [5, 2.5]) {
  return once('damask' + base + ink + repeat, () => {
    const S = 512;
    const [c, g] = canvas(S, S);
    g.fillStyle = base; g.fillRect(0, 0, S, S);
    noiseFill(g, S, S, 0, 12, 61, 1);
    g.fillStyle = ink;
    const motif = (x, y, s) => {
      g.save(); g.translate(x, y); g.scale(s, s);
      g.beginPath();
      g.moveTo(0, -60); g.bezierCurveTo(30, -40, 36, -10, 14, 6); g.bezierCurveTo(40, 10, 44, 40, 18, 52);
      g.bezierCurveTo(10, 60, 4, 66, 0, 76); g.bezierCurveTo(-4, 66, -10, 60, -18, 52);
      g.bezierCurveTo(-44, 40, -40, 10, -14, 6); g.bezierCurveTo(-36, -10, -30, -40, 0, -60); g.fill();
      g.fillStyle = base;
      g.beginPath(); g.ellipse(0, 4, 8, 22, 0, 0, Math.PI * 2); g.fill();
      g.fillStyle = ink;
      for (const sd of [-1, 1]) { g.beginPath(); g.ellipse(sd * 30, -40, 6, 14, sd * 0.6, 0, Math.PI * 2); g.fill(); g.beginPath(); g.ellipse(sd * 34, 40, 5, 11, -sd * 0.5, 0, Math.PI * 2); g.fill(); }
      g.restore();
    };
    for (let y = 0; y < 2; y++) for (let x = 0; x < 2; x++) motif(128 + x * 256, 128 + y * 256, 1.25);
    for (let y = 0; y < 2; y++) for (let x = 0; x < 2; x++) motif(x * 256, 256 * y, 0.8);
    for (let y = 0; y < 2; y++) for (let x = 0; x < 2; x++) motif(256 + x * 256, 256 * y, 0.8);
    noiseFill(g, S, S, 0, 10, 62, 2);
    return toTex(c, { repeat });
  });
}

// persian-style rug
export function rugTexture(seed = 5) {
  return once('rug' + seed, () => {
    const W = 1024, H = 768;
    const [c, g] = canvas(W, H);
    g.fillStyle = '#9a2a1c'; g.fillRect(0, 0, W, H);
    const r = rng(seed);
    for (let i = 0; i < 8; i++) {
      g.strokeStyle = ['#e8c890', '#1c2a4a', '#f0e0c0', '#5a1a10'][i % 4];
      g.lineWidth = 10 + (i % 3) * 6;
      g.strokeRect(20 + i * 22, 20 + i * 22, W - 40 - i * 44, H - 40 - i * 44);
    }
    g.save(); g.translate(W / 2, H / 2);
    for (let k = 0; k < 4; k++) {
      g.rotate(Math.PI / 2);
      g.fillStyle = '#1c2a4a';
      g.beginPath(); g.ellipse(0, 0, 220, 130, 0, 0, Math.PI * 2); g.fill();
      g.fillStyle = '#e8c890';
      g.beginPath(); g.ellipse(0, 0, 150, 80, 0, 0, Math.PI * 2); g.fill();
      g.fillStyle = '#9a2a1c';
      g.beginPath(); g.ellipse(0, 0, 90, 45, 0, 0, Math.PI * 2); g.fill();
    }
    g.restore();
    for (let i = 0; i < 2600; i++) {
      g.fillStyle = ['rgba(240,220,180,0.5)', 'rgba(20,30,60,0.5)', 'rgba(60,10,5,0.4)'][Math.floor(r() * 3)];
      const x = r() * W, y = r() * H;
      g.fillRect(x, y, 4 + r() * 6, 3);
    }
    noiseFill(g, W, H, 0, 18, seed + 3, 2);
    return toTex(c);
  });
}

// low-pile office carpet
export function carpet(base = '#5a6250', seed = 9, repeat = [6, 6]) {
  return once('carpet' + base + seed + repeat, () => {
    const S = 512;
    const [c, g] = canvas(S, S);
    g.fillStyle = base; g.fillRect(0, 0, S, S);
    noiseFill(g, S, S, 0, 26, seed, 1);
    noiseFill(g, S, S, 0, 10, seed + 1, 4);
    return toTex(c, { repeat });
  });
}

// metal locker bank: doors with vents, handles and numbers
export function lockerTexture(base = '#2e6a8e', count = 6, start = 101) {
  return once('locker' + base + count + start, () => {
    const W = 192 * count, H = 1024;
    const [c, g] = canvas(W, H);
    for (let i = 0; i < count; i++) {
      const x = i * 192;
      const grd = g.createLinearGradient(x, 0, x + 192, 0);
      grd.addColorStop(0, shiftHex(base, -18)); grd.addColorStop(0.5, shiftHex(base, 10)); grd.addColorStop(1, shiftHex(base, -12));
      g.fillStyle = grd; g.fillRect(x, 0, 192, H);
      g.fillStyle = 'rgba(0,0,0,0.55)'; g.fillRect(x, 0, 5, H);
      g.fillStyle = 'rgba(255,255,255,0.18)'; g.fillRect(x + 5, 0, 3, H);
      for (const vy of [70, 900]) for (let k = 0; k < 5; k++) { g.fillStyle = 'rgba(0,0,0,0.6)'; g.fillRect(x + 50, vy + k * 16, 92, 7); }
      g.fillStyle = '#c8c8c8'; g.fillRect(x + 150, 470, 18, 80);
      g.fillStyle = 'rgba(0,0,0,0.5)'; g.fillRect(x + 154, 500, 10, 26);
      g.fillStyle = '#e8e8e0'; g.fillRect(x + 66, 230, 60, 30);
      g.fillStyle = '#222'; g.font = 'bold 24px "Liberation Sans"'; g.textAlign = 'center'; g.fillText(String(start + i), x + 96, 254);
    }
    noiseFill(g, W, H, 0, 8, 81, 2);
    return toTex(c);
  });
}

// whiteboard surface: callers draw text on the returned canvas
export function whiteboardCanvas(W = 1400, H = 600) {
  const [c, g] = canvas(W, H);
  const tex = toTex(c);
  return { c, g, tex, W, H };
}
export function clearBoard(g, W, H) {
  g.fillStyle = '#f4f6f4'; g.fillRect(0, 0, W, H);
  const grd = g.createLinearGradient(0, 0, W, H);
  grd.addColorStop(0, 'rgba(255,255,255,0.0)'); grd.addColorStop(0.45, 'rgba(255,255,255,0.0)');
  grd.addColorStop(0.5, 'rgba(200,210,220,0.18)'); grd.addColorStop(0.6, 'rgba(255,255,255,0.0)');
  g.fillStyle = grd; g.fillRect(0, 0, W, H);
  g.fillStyle = 'rgba(120,140,170,0.07)'; // ghost of old erased writing
  g.font = 'italic 60px "Liberation Sans"';
  g.fillText('x² + 3x = ...', 200, 420);
}

// posters: a handful of school wall posters
export function posterTexture(kind) {
  return once('poster' + kind, () => {
    const W = 512, H = 700;
    const [c, g] = canvas(W, H);
    if (kind === 'periodic') {
      g.fillStyle = '#f2efe6'; g.fillRect(0, 0, W, H);
      g.fillStyle = '#1c2a4a'; g.font = 'bold 40px "Liberation Sans"'; g.textAlign = 'center'; g.fillText('PERIODIC TABLE', W / 2, 60);
      const cols = ['#e86a5a', '#f0b84a', '#7ac86a', '#5aa8e8', '#b07ae0', '#e8e05a'];
      const r = rng(7);
      for (let y = 0; y < 9; y++) for (let x = 0; x < 12; x++) {
        if (y < 3 && x > 1 && x < 8) continue;
        g.fillStyle = cols[(x + y * 3) % cols.length]; g.fillRect(20 + x * 39, 100 + y * 58, 35, 52);
        g.fillStyle = 'rgba(0,0,0,0.6)'; g.font = 'bold 16px "Liberation Sans"';
        g.fillText(String.fromCharCode(65 + Math.floor(r() * 26)) + (r() < 0.5 ? String.fromCharCode(97 + Math.floor(r() * 26)) : ''), 37 + x * 39, 132 + y * 58);
      }
    } else if (kind === 'map') {
      g.fillStyle = '#7ab8e0'; g.fillRect(0, 0, W, H);
      g.fillStyle = '#8ac46a';
      const r = rng(17);
      for (let i = 0; i < 9; i++) { g.beginPath(); const cx = r() * W, cy = 120 + r() * (H - 200); for (let k = 0; k < 12; k++) { const a = k / 12 * Math.PI * 2; const rr = 40 + r() * 70; g.lineTo(cx + Math.cos(a) * rr * 1.3, cy + Math.sin(a) * rr); } g.fill(); }
      g.fillStyle = '#fff'; g.fillRect(0, 0, W, 70); g.fillStyle = '#1c2a4a'; g.font = 'bold 42px "Liberation Sans"'; g.textAlign = 'center'; g.fillText('THE WORLD', W / 2, 52);
    } else if (kind === 'quote') {
      g.fillStyle = '#1c3a5e'; g.fillRect(0, 0, W, H);
      g.fillStyle = '#f0c850'; g.font = 'bold 54px "Liberation Serif"'; g.textAlign = 'center';
      ['HARD', 'WORK', 'BEATS', 'TALENT'].forEach((w, i) => g.fillText(w, W / 2, 200 + i * 90));
      g.fillStyle = '#fff'; g.font = 'italic 28px "Liberation Serif"'; g.fillText('— every teacher ever', W / 2, 620);
    } else if (kind === 'math') {
      g.fillStyle = '#fdfbf2'; g.fillRect(0, 0, W, H);
      g.fillStyle = '#c0392b'; g.font = 'bold 44px "Liberation Sans"'; g.textAlign = 'center'; g.fillText('GEOMETRY', W / 2, 70);
      g.strokeStyle = '#1c2a4a'; g.lineWidth = 6;
      g.beginPath(); g.moveTo(100, 400); g.lineTo(400, 400); g.lineTo(100, 160); g.closePath(); g.stroke();
      g.beginPath(); g.arc(360, 560, 80, 0, Math.PI * 2); g.stroke();
      g.fillStyle = '#1c2a4a'; g.font = '34px "Liberation Serif"'; g.fillText('a² + b² = c²', W / 2, 470); g.fillText('A = πr²', 200, 570);
    } else if (kind === 'reading') {
      g.fillStyle = '#e8743a'; g.fillRect(0, 0, W, H);
      g.fillStyle = '#fff'; g.font = 'bold 64px "Liberation Sans"'; g.textAlign = 'center'; g.fillText('READ', W / 2, 130); g.fillText('MORE', W / 2, 210);
      for (let i = 0; i < 5; i++) { g.fillStyle = ['#1c3a5e', '#f0c850', '#2a8a5a', '#8a2a4a', '#fff'][i]; g.fillRect(90 + i * 68, 330 - i * 6, 56, 280 + i * 6); }
    }
    noiseFill(g, W, H, 0, 10, 99, 2);
    return toTex(c);
  });
}

// row of book spines for shelves
export function bookSpines(seed = 1) {
  return once('books' + seed, () => {
    const W = 1024, H = 256;
    const [c, g] = canvas(W, H);
    g.fillStyle = '#2a1a10'; g.fillRect(0, 0, W, H);
    const r = rng(seed);
    let x = 0;
    const cols = ['#7a1c24', '#1c3a5e', '#2a5a3a', '#c8a050', '#5a2a5a', '#d8d0c0', '#3a3a3a', '#a84a20', '#204a6a'];
    while (x < W) {
      const w = 18 + r() * 30, h = H * (0.7 + r() * 0.3);
      g.fillStyle = cols[Math.floor(r() * cols.length)];
      g.fillRect(x, H - h, w - 2, h);
      g.fillStyle = 'rgba(255,255,255,0.18)'; g.fillRect(x + 3, H - h + 20, w - 8, 5); g.fillRect(x + 3, H - 30, w - 8, 4);
      g.fillStyle = 'rgba(0,0,0,0.25)'; g.fillRect(x + w - 6, H - h, 4, h);
      x += w;
    }
    noiseFill(g, W, H, 0, 10, seed + 5, 1);
    return toTex(c);
  });
}

// bright outdoor view seen through windows (blown out, like the reference)
export function outsideView(kind = 'day') {
  return once('outside' + kind, () => {
    const W = 512, H = 512;
    const [c, g] = canvas(W, H);
    if (kind === 'night') {
      const grd = g.createLinearGradient(0, 0, 0, H);
      grd.addColorStop(0, '#0a1430'); grd.addColorStop(1, '#1a2a50');
      g.fillStyle = grd; g.fillRect(0, 0, W, H);
      const r = rng(5);
      for (let i = 0; i < 60; i++) { g.fillStyle = `rgba(255,255,240,${0.3 + r() * 0.6})`; g.fillRect(r() * W, r() * H * 0.6, 2, 2); }
      g.fillStyle = '#060a18';
      for (let i = 0; i < 8; i++) { const bw = 40 + r() * 60, bh = 80 + r() * 160, bx = r() * W; g.fillRect(bx, H - bh, bw, bh);
        for (let k = 0; k < 6; k++) { g.fillStyle = r() < 0.5 ? '#f0c060' : '#060a18'; g.fillRect(bx + 6 + (k % 3) * 12, H - bh + 14 + Math.floor(k / 3) * 22, 6, 9); }
        g.fillStyle = '#060a18'; }
      g.fillStyle = '#e8e8d8'; g.beginPath(); g.arc(W * 0.75, H * 0.2, 26, 0, Math.PI * 2); g.fill();
    } else {
      const grd = g.createLinearGradient(0, 0, 0, H);
      grd.addColorStop(0, '#d8ecff'); grd.addColorStop(0.6, '#f4fbff'); grd.addColorStop(1, '#e0f0d8');
      g.fillStyle = grd; g.fillRect(0, 0, W, H);
      const r = rng(8);
      for (let i = 0; i < 26; i++) { // soft tree canopies
        g.fillStyle = `rgba(${90 + r() * 40},${150 + r() * 40},${80 + r() * 30},0.5)`;
        g.beginPath(); g.arc(r() * W, H * (0.45 + r() * 0.3), 30 + r() * 60, 0, Math.PI * 2); g.fill();
      }
    }
    return toTex(c);
  });
}

// ceiling: acoustic tiles with a grid
export function ceilingTiles(repeat = [8, 8]) {
  return once('ceil' + repeat, () => {
    const S = 256;
    const [c, g] = canvas(S, S);
    g.fillStyle = '#ecebe6'; g.fillRect(0, 0, S, S);
    const r = rng(3);
    for (let i = 0; i < 900; i++) { g.fillStyle = 'rgba(80,80,80,0.25)'; g.fillRect(r() * S, r() * S, 1.5, 1.5); }
    g.fillStyle = '#c8c6c0'; g.fillRect(0, 0, S, 6); g.fillRect(0, 0, 6, S);
    return toTex(c, { repeat });
  });
}

export function shiftHex(h, k) {
  h = h.replace('#', '');
  const v = [0, 2, 4].map((i) => Math.max(0, Math.min(255, parseInt(h.slice(i, i + 2), 16) + k)));
  return '#' + v.map((x) => Math.round(x).toString(16).padStart(2, '0')).join('');
}

export function solidTex(col) {
  return once('solid' + col, () => { const [c, g] = canvas(4, 4); g.fillStyle = col; g.fillRect(0, 0, 4, 4); return toTex(c); });
}

export { THREE };
