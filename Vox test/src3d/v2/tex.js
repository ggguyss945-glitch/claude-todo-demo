// Procedural canvas textures (no image files are loaded anywhere).
import * as THREE from 'three';
import { rng } from './util.js';

export function canvas(w, h) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  return [c, c.getContext('2d')];
}

export function toTex(c, { repeat = null, srgb = true, aniso = 8, mip = true } = {}) {
  const t = new THREE.CanvasTexture(c);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = aniso;
  if (repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(repeat[0], repeat[1]); }
  if (!mip) { t.generateMipmaps = false; t.minFilter = THREE.LinearFilter; }
  return t;
}

export function noiseFill(g, w, h, base, amp, seed = 1, cell = 1) {
  const r = rng(seed);
  const img = g.getImageData(0, 0, w, h);
  const d = img.data;
  for (let y = 0; y < h; y += cell) {
    for (let x = 0; x < w; x += cell) {
      const n = (r() - 0.5) * amp;
      for (let yy = 0; yy < cell && y + yy < h; yy++) for (let xx = 0; xx < cell && x + xx < w; xx++) {
        const i = ((y + yy) * w + x + xx) * 4;
        d[i] = Math.max(0, Math.min(255, d[i] + n));
        d[i + 1] = Math.max(0, Math.min(255, d[i + 1] + n));
        d[i + 2] = Math.max(0, Math.min(255, d[i + 2] + n));
      }
    }
  }
  g.putImageData(img, 0, 0);
}

// ---------------------------------------------------------------- table ---
export const WHEEL_ORDER = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16,
  33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26];
export const REDS = new Set([1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]);
export const RED = '#d8231b', BLACK = '#141414', FELT = '#14a02c';

// Felt + betting layout. Canvas maps x∈[-W/2,W/2] -> u, z∈[-L/2,L/2] -> v (top = dealer end).
export function layoutTexture(T, opts = {}) {
  const PX = 760; // px per metre
  const w = Math.round(T.W * PX), h = Math.round(T.L * PX);
  const [c, g] = canvas(w, h);
  g.fillStyle = opts.felt || FELT;
  g.fillRect(0, 0, w, h);
  noiseFill(g, w, h, 0, 10, 3, 2);
  const X = (x) => (x + T.W / 2) * PX, Z = (z) => (z + T.L / 2) * PX;
  g.strokeStyle = '#f4f4ee';
  g.lineWidth = 0.012 * PX;
  g.lineJoin = 'miter';
  const { cols, rows, x0, z0, cw, ch } = T.grid;
  // zero box
  g.beginPath();
  g.moveTo(X(x0), Z(z0));
  g.lineTo(X(x0 + cw * 0.5), Z(z0 - ch * 1.1));
  g.lineTo(X(x0 + cw * 2.5), Z(z0 - ch * 1.1));
  g.lineTo(X(x0 + cw * 3), Z(z0));
  g.stroke();
  drawOval(g, X(x0 + cw * 1.5), Z(z0 - ch * 0.55), cw * 0.32 * PX, ch * 0.34 * PX, '#18b83a');
  numText(g, '0', X(x0 + cw * 1.5), Z(z0 - ch * 0.55), ch * 0.42 * PX, 0);
  for (let r = 0; r < rows; r++) {
    for (let k = 0; k < cols; k++) {
      const n = r * 3 + k + 1;
      const cx = x0 + cw * (k + 0.5), cz = z0 + ch * (r + 0.5);
      g.strokeRect(X(x0 + cw * k), Z(z0 + ch * r), cw * PX, ch * PX);
      drawOval(g, X(cx), Z(cz), cw * 0.36 * PX, ch * 0.36 * PX, REDS.has(n) ? RED : BLACK);
      numText(g, String(n), X(cx), Z(cz), ch * 0.44 * PX, 0);
    }
  }
  // column bets ("2 to 1") row at the player end
  for (let k = 0; k < 3; k++) g.strokeRect(X(x0 + cw * k), Z(z0 + ch * rows), cw * PX, ch * 0.8 * PX);
  // outside border line
  g.lineWidth = 0.014 * PX;
  g.strokeRect(X(x0), Z(z0 - ch * 1.1), cw * 3 * PX, ch * (rows + 1.9) * PX);
  // the three colour circles (RED / BLACK / GREEN bets)
  for (const s of T.spots) {
    g.beginPath();
    g.arc(X(s.x), Z(s.z), s.r * PX, 0, Math.PI * 2);
    g.fillStyle = s.color;
    g.fill();
    g.lineWidth = 0.018 * PX;
    g.strokeStyle = '#f7f7f0';
    g.stroke();
  }
  const t = toTex(c, { aniso: 16 });
  return t;
}

function drawOval(g, x, y, rx, ry, col) {
  g.beginPath();
  g.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2);
  g.fillStyle = col;
  g.fill();
}

function numText(g, s, x, y, size, rot) {
  g.save();
  g.translate(x, y);
  g.rotate(rot);
  // numbers face the player (player sits at +z = bottom of canvas), so text is drawn upright w.r.t. canvas
  g.font = `bold ${size}px "Liberation Sans", Arial, sans-serif`;
  g.fillStyle = '#ffffff';
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.fillText(s, 0, size * 0.04);
  g.restore();
}

export function wheelRingTexture() {
  // polar strip rendered directly as a disc texture
  const S = 1024;
  const [c, g] = canvas(S, S);
  const cx = S / 2, cy = S / 2;
  const n = 37, da = (Math.PI * 2) / n;
  const rOut = S * 0.5, rNum = S * 0.36, rIn = S * 0.27;
  g.fillStyle = '#6b3b1c';
  g.fillRect(0, 0, S, S);
  for (let i = 0; i < n; i++) {
    const num = WHEEL_ORDER[i];
    const a0 = -Math.PI / 2 + i * da - da / 2;
    g.beginPath();
    g.arc(cx, cy, rOut, a0, a0 + da);
    g.arc(cx, cy, rIn, a0 + da, a0, true);
    g.closePath();
    g.fillStyle = num === 0 ? '#1fb53a' : REDS.has(num) ? '#e0221a' : '#151515';
    g.fill();
  }
  // separators and rings
  g.strokeStyle = '#d9c9a0';
  g.lineWidth = 3;
  for (let i = 0; i < n; i++) {
    const a = -Math.PI / 2 + i * da - da / 2;
    g.beginPath();
    g.moveTo(cx + rIn * Math.cos(a), cy + rIn * Math.sin(a));
    g.lineTo(cx + rOut * Math.cos(a), cy + rOut * Math.sin(a));
    g.stroke();
  }
  for (const r of [rIn, rNum - S * 0.055, rOut - 2]) {
    g.beginPath(); g.arc(cx, cy, r, 0, Math.PI * 2); g.stroke();
  }
  g.font = `bold ${S * 0.048}px "Liberation Sans", Arial`;
  g.fillStyle = '#ffffff';
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  for (let i = 0; i < n; i++) {
    const a = -Math.PI / 2 + i * da;
    g.save();
    g.translate(cx + (rNum + S * 0.06) * Math.cos(a), cy + (rNum + S * 0.06) * Math.sin(a));
    g.rotate(a + Math.PI / 2);
    g.fillText(String(WHEEL_ORDER[i]), 0, 0);
    g.restore();
  }
  return toTex(c, { aniso: 16 });
}

// ---------------------------------------------------------------- chips ---
const chipCache = new Map();
export function chipTextures(color, label) {
  const key = color + label;
  if (chipCache.has(key)) return chipCache.get(key);
  // side: one chip tall band with white edge-spot rectangles
  const [cs, gs] = canvas(512, 32);
  gs.fillStyle = color;
  gs.fillRect(0, 0, 512, 32);
  gs.fillStyle = '#f2f2f2';
  for (let i = 0; i < 8; i++) {
    const x = i * 64 + 16;
    gs.fillRect(x, 0, 14, 16);
    gs.fillRect(x + 14, 16, 14, 16);
  }
  gs.fillStyle = 'rgba(0,0,0,0.25)';
  gs.fillRect(0, 30, 512, 2);
  const side = toTex(cs);
  side.wrapS = side.wrapT = THREE.RepeatWrapping;
  // top face
  const S = 256;
  const [ct, gt] = canvas(S, S);
  gt.fillStyle = color;
  gt.fillRect(0, 0, S, S);
  gt.fillStyle = '#f2f2f2';
  for (let i = 0; i < 8; i++) {
    gt.save();
    gt.translate(S / 2, S / 2);
    gt.rotate((i / 8) * Math.PI * 2);
    gt.fillRect(-14, -S / 2, 28, 34);
    gt.restore();
  }
  gt.setLineDash([10, 8]);
  gt.strokeStyle = '#f2f2f2';
  gt.lineWidth = 5;
  gt.beginPath(); gt.arc(S / 2, S / 2, S * 0.33, 0, Math.PI * 2); gt.stroke();
  gt.setLineDash([]);
  gt.font = `bold ${S * 0.26}px "Liberation Sans", Arial`;
  gt.textAlign = 'center';
  gt.textBaseline = 'middle';
  gt.fillStyle = '#ffffff';
  gt.fillText(label, S / 2 + 4, S / 2 + 4);
  gt.font = `bold ${S * 0.1}px "Liberation Sans", Arial`;
  const top = toTex(ct);
  const res = { side, top };
  chipCache.set(key, res);
  return res;
}

// ---------------------------------------------------------- environment ---
export function carpetTexture(seed = 5) {
  const S = 1024;
  const [c, g] = canvas(S, S);
  g.fillStyle = '#4a2018';
  g.fillRect(0, 0, S, S);
  noiseFill(g, S, S, 0, 16, seed, 2);
  // chevron / art-deco line pattern like the original carpet
  g.strokeStyle = 'rgba(25,8,6,0.75)';
  g.lineWidth = 6;
  const step = 128;
  for (let y = 0; y < S; y += step) {
    for (let x = 0; x < S; x += step) {
      for (let k = 0; k < 3; k++) {
        const o = 18 + k * 18;
        g.beginPath();
        g.moveTo(x + o, y + step - 10);
        g.lineTo(x + o, y + o);
        g.lineTo(x + step - 10, y + o);
        g.stroke();
      }
    }
  }
  g.strokeStyle = 'rgba(120,60,40,0.25)';
  g.lineWidth = 2;
  for (let y = 0; y < S; y += step) for (let x = 0; x < S; x += step) {
    g.strokeRect(x + 4, y + 4, step - 8, step - 8);
  }
  return toTex(c, { repeat: [10, 10] });
}

export function wallTexture(base = '#0c1a42', seed = 9) {
  const S = 512;
  const [c, g] = canvas(S, S);
  g.fillStyle = base;
  g.fillRect(0, 0, S, S);
  noiseFill(g, S, S, 0, 10, seed, 1);
  // vertical damask-ish pattern
  g.strokeStyle = 'rgba(70,110,200,0.22)';
  g.lineWidth = 3;
  for (let x = 0; x < S; x += 64) {
    for (let y = 0; y < S; y += 96) {
      g.beginPath();
      g.moveTo(x + 32, y);
      g.bezierCurveTo(x + 58, y + 24, x + 58, y + 72, x + 32, y + 96);
      g.bezierCurveTo(x + 6, y + 72, x + 6, y + 24, x + 32, y);
      g.stroke();
      g.beginPath();
      g.arc(x + 32, y + 48, 6, 0, Math.PI * 2);
      g.stroke();
    }
  }
  g.fillStyle = 'rgba(0,0,0,0.25)';
  for (let x = 0; x < S; x += 64) g.fillRect(x, 0, 2, S);
  return toTex(c, { repeat: [8, 3] });
}

export function woodTexture(base = '#8a5a30', seed = 2, grain = 0.35, w = 512, h = 512) {
  const [c, g] = canvas(w, h);
  g.fillStyle = base;
  g.fillRect(0, 0, w, h);
  const r = rng(seed);
  for (let i = 0; i < 160; i++) {
    const y = r() * h;
    g.strokeStyle = `rgba(${r() < 0.5 ? '40,20,8' : '255,220,170'},${grain * r() * 0.5})`;
    g.lineWidth = 1 + r() * 3;
    g.beginPath();
    g.moveTo(0, y);
    for (let x = 0; x <= w; x += 32) g.lineTo(x, y + Math.sin(x * 0.01 + i) * 6 * r());
    g.stroke();
  }
  noiseFill(g, w, h, 0, 8, seed + 1, 1);
  return toTex(c);
}

export function wickerTexture() {
  const S = 256;
  const [c, g] = canvas(S, S);
  g.fillStyle = '#5a3a1e';
  g.fillRect(0, 0, S, S);
  for (let y = 0; y < S; y += 16) for (let x = 0; x < S; x += 16) {
    const on = ((x + y) / 16) % 2 === 0;
    g.fillStyle = on ? '#c8a473' : '#9b7546';
    if (on) g.fillRect(x + 1, y + 3, 14, 10); else g.fillRect(x + 3, y + 1, 10, 14);
  }
  noiseFill(g, S, S, 0, 20, 4, 1);
  return toTex(c, { repeat: [3, 3] });
}

export function leatherTexture(base = '#b8562a') {
  const S = 256;
  const [c, g] = canvas(S, S);
  g.fillStyle = base;
  g.fillRect(0, 0, S, S);
  noiseFill(g, S, S, 0, 14, 11, 1);
  return toTex(c, { repeat: [6, 1] });
}

// ------------------------------------------------------------- display board ---
export function makeBoard() {
  const [c, g] = canvas(512, 1024);
  const tex = toTex(c);
  const [ce, ge] = canvas(512, 1024);
  const emi = toTex(ce);
  let last = '';
  function draw(state, spin) {
    const key = state + (state === 'rolling' ? Math.round(spin * 40) : '');
    if (key === last) return;
    last = key;
    g.fillStyle = '#1a5c32';
    g.fillRect(0, 0, 512, 1024);
    noiseFill(g, 512, 1024, 0, 6, 21, 2);
    ge.fillStyle = '#000';
    ge.fillRect(0, 0, 512, 1024);
    const title = { black: 'BLACK!', red: 'RED!', green: 'GREEN!', rolling: 'Rolling...' }[state];
    for (const gg of [g, ge]) {
      gg.fillStyle = gg === g ? '#f4f4ec' : '#bdbdb5';
      gg.textAlign = 'center';
      gg.textBaseline = 'alphabetic';
      gg.font = state === 'rolling' ? 'italic bold 92px "Liberation Serif", serif' : 'bold 104px "Liberation Serif", serif';
      gg.fillText(title, 256, 210);
    }
    const cx = 256, cy = 470, R = 175;
    if (state === 'rolling') {
      // stylised spinning wheel: 8 alternating wedges
      g.save();
      g.translate(cx, cy);
      g.rotate(spin);
      const cols = ['#e0453a', '#1a1414', '#e0453a', '#1a1414', '#58a83a', '#1a1414', '#e0453a', '#1a1414'];
      for (let i = 0; i < 8; i++) {
        g.beginPath();
        g.moveTo(0, 0);
        g.arc(0, 0, R, (i * Math.PI) / 4, ((i + 1) * Math.PI) / 4);
        g.closePath();
        g.fillStyle = cols[i];
        g.fill();
        g.strokeStyle = '#e8d2a0';
        g.lineWidth = 4;
        g.stroke();
      }
      g.beginPath(); g.arc(0, 0, R * 0.38, 0, Math.PI * 2); g.fillStyle = '#3a2416'; g.fill();
      g.strokeStyle = '#e8d2a0'; g.lineWidth = 6; g.stroke();
      g.beginPath(); g.moveTo(-R * 0.38, 0); g.lineTo(R * 0.38, 0); g.moveTo(0, -R * 0.38); g.lineTo(0, R * 0.38); g.stroke();
      g.restore();
      for (const gg of [g, ge]) {
        gg.beginPath(); gg.arc(cx, cy, R, 0, Math.PI * 2);
        gg.strokeStyle = gg === g ? '#f0e6c8' : '#9a9070'; gg.lineWidth = 7; gg.stroke();
      }
    } else {
      const base = { black: ['#3a3a3a', '#0a0a0a'], red: ['#ff5040', '#c01208'], green: ['#90f070', '#2fa020'] }[state];
      g.beginPath(); g.arc(cx, cy, R + 7, 0, Math.PI * 2); g.fillStyle = '#0c0c0c'; g.fill();
      const grd = g.createRadialGradient(cx - R * 0.35, cy - R * 0.4, R * 0.05, cx, cy, R);
      grd.addColorStop(0, base[0]); grd.addColorStop(1, base[1]);
      g.beginPath(); g.arc(cx, cy, R, 0, Math.PI * 2); g.fillStyle = grd; g.fill();
      if (state !== 'black') {
        ge.beginPath(); ge.arc(cx, cy, R, 0, Math.PI * 2);
        ge.fillStyle = state === 'red' ? '#601008' : '#205a10'; ge.fill();
      }
    }
    tex.needsUpdate = true;
    emi.needsUpdate = true;
  }
  return { tex, emi, draw };
}

// prediction ring fill (dotted chip-like disc)
export function ringFillTexture(color) {
  const S = 128;
  const [c, g] = canvas(S, S);
  g.fillStyle = color;
  g.fillRect(0, 0, S, S);
  g.fillStyle = 'rgba(255,255,255,0.75)';
  for (let y = 4; y < S; y += 12) for (let x = ((y / 12) % 2) * 6 + 4; x < S; x += 12) g.fillRect(x, y, 5, 5);
  return toTex(c);
}

export function halftoneTexture(c1 = '#1b74d8', c2 = '#8fd4ff', dot = '#e8f6ff') {
  const S = 512;
  const [c, g] = canvas(S, S);
  const grd = g.createLinearGradient(0, 0, 0, S);
  grd.addColorStop(0, c1); grd.addColorStop(1, c2);
  g.fillStyle = grd;
  g.fillRect(0, 0, S, S);
  g.fillStyle = dot;
  for (let y = 0; y < S; y += 14) for (let x = (y / 14) % 2 ? 7 : 0; x < S; x += 14) {
    const r = 2 + 3.5 * (y / S);
    g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); g.fill();
  }
  return toTex(c);
}

export function diamondPlateTexture() {
  const S = 256;
  const [c, g] = canvas(S, S);
  g.fillStyle = '#a8a294';
  g.fillRect(0, 0, S, S);
  noiseFill(g, S, S, 0, 18, 31, 1);
  g.lineCap = 'round';
  for (let y = 0; y < S; y += 32) for (let x = 0; x < S; x += 32) {
    const o = (y / 32) % 2 ? 16 : 0;
    g.strokeStyle = 'rgba(255,255,240,0.6)';
    g.lineWidth = 5;
    g.beginPath();
    if (((x + y) / 32) % 2) { g.moveTo(x + o + 6, y + 6); g.lineTo(x + o + 22, y + 22); }
    else { g.moveTo(x + o + 22, y + 6); g.lineTo(x + o + 6, y + 22); }
    g.stroke();
    g.strokeStyle = 'rgba(60,55,45,0.55)';
    g.lineWidth = 2;
    g.stroke();
  }
  return toTex(c, { repeat: [3, 3] });
}

export function slotScreenTexture(seed = 1) {
  const [c, g] = canvas(256, 384);
  const r = rng(seed);
  const grd = g.createLinearGradient(0, 0, 0, 384);
  grd.addColorStop(0, '#1a3a9a'); grd.addColorStop(1, '#0a1840');
  g.fillStyle = grd;
  g.fillRect(0, 0, 256, 384);
  g.fillStyle = '#ffd040';
  g.font = 'bold 34px "Liberation Sans"';
  g.textAlign = 'center';
  g.fillText(['JACKPOT', 'LUCKY 7', 'FORTUNE', 'DIAMOND'][seed % 4], 128, 52);
  for (let k = 0; k < 3; k++) for (let j = 0; j < 3; j++) {
    g.fillStyle = '#f4f4f4';
    g.fillRect(24 + k * 72, 90 + j * 70, 64, 62);
    const sym = ['7', '♦', '♣', 'BAR', '★'][Math.floor(r() * 5)];
    g.fillStyle = ['#e02020', '#2050e0', '#20a040', '#e0a000'][Math.floor(r() * 4)];
    g.font = `bold ${sym === 'BAR' ? 22 : 44}px "Liberation Sans"`;
    g.fillText(sym, 56 + k * 72, 138 + j * 70);
  }
  g.fillStyle = '#ff40c0';
  g.fillRect(20, 310, 216, 40);
  g.fillStyle = '#fff';
  g.font = 'bold 26px "Liberation Sans"';
  g.fillText('SPIN', 128, 340);
  return toTex(c);
}

export function woodPanelTexture() {
  const [c, g] = canvas(1024, 1024);
  g.fillStyle = '#6a3414';
  g.fillRect(0, 0, 1024, 1024);
  const r = rng(77);
  for (let i = 0; i < 300; i++) {
    const x = r() * 1024;
    g.strokeStyle = `rgba(${r() < 0.5 ? '30,10,0' : '200,120,60'},${0.12 * r()})`;
    g.lineWidth = 1 + r() * 4;
    g.beginPath();
    g.moveTo(x, 0);
    for (let y = 0; y <= 1024; y += 32) g.lineTo(x + Math.sin(y * 0.008 + i) * 10, y);
    g.stroke();
  }
  // raised panels
  for (let px = 0; px < 2; px++) for (let py = 0; py < 2; py++) {
    const x = 40 + px * 512, y = 40 + py * 512;
    g.strokeStyle = 'rgba(20,6,0,0.6)'; g.lineWidth = 10; g.strokeRect(x, y, 432, 432);
    g.strokeStyle = 'rgba(255,170,100,0.18)'; g.lineWidth = 4; g.strokeRect(x + 8, y + 8, 416, 416);
  }
  noiseFill(g, 1024, 1024, 0, 8, 78, 2);
  return toTex(c, { repeat: [3, 1.5] });
}
