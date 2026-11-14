// Painted set textures with drawn lines, in the storybook style (lines are part of the paint).
import * as THREE from 'three';
import { canvas, toTex } from './tex.js';
import { hash } from './util.js';

const LINE = 'rgba(40,24,14,0.55)';
function speckle(g, w, h, n, a, seed) { for (let i = 0; i < n; i++) { g.fillStyle = hash(seed, i) > 0.5 ? `rgba(255,255,255,${a})` : `rgba(60,30,10,${a})`; g.fillRect(hash(seed, i + 0.1) * w, hash(seed, i + 0.2) * h, 2 + hash(seed, i + 0.3) * 5, 2 + hash(seed, i + 0.4) * 4); } }
function stain(g, w, h, n, seed, col = 'rgba(90,50,20,0.07)') {
  for (let i = 0; i < n; i++) {
    const x = hash(seed, i) * w, y = hash(seed, i + 0.5) * h, r = 20 + hash(seed, i + 0.7) * 70;
    const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, col); gr.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = gr; g.fillRect(x - r, y - r, 2 * r, 2 * r);
  }
}

// sandstone blocks with alternating ablaq stripes (Cairo's striped masonry)
export function ablaq(base = '#e6c89a', band = '#c0603a', rep = [1, 1], seed = 1, bands = true) {
  const [c, g] = canvas(512, 512);
  g.fillStyle = base; g.fillRect(0, 0, 512, 512);
  const rowH = 32;
  for (let r = 0; r < 512 / rowH; r++) {
    if (bands && r % 4 === 1) { g.fillStyle = band; g.fillRect(0, r * rowH, 512, rowH); }
    else if (hash(seed, r) < 0.35) { g.fillStyle = 'rgba(255,240,210,0.12)'; g.fillRect(0, r * rowH, 512, rowH); }
    g.strokeStyle = LINE; g.lineWidth = 2.2;
    g.beginPath(); g.moveTo(0, r * rowH + 0.5); g.lineTo(512, r * rowH + 0.5); g.stroke();
    const off = (r % 2) * 40;
    for (let x = off; x < 512 + 80; x += 80 + Math.floor(hash(seed, r, x) * 3) * 10) { g.beginPath(); g.moveTo(x, r * rowH); g.lineTo(x, (r + 1) * rowH); g.stroke(); }
  }
  stain(g, 512, 512, 14, seed);
  speckle(g, 512, 512, 900, 0.06, seed);
  return toTex(c, { repeat: rep, aniso: 8 });
}
export function plaster(base = '#efdcb8', rep = [1, 1], seed = 2) {
  const [c, g] = canvas(512, 512);
  g.fillStyle = base; g.fillRect(0, 0, 512, 512);
  stain(g, 512, 512, 22, seed, 'rgba(150,90,40,0.08)');
  // a few cracks
  g.strokeStyle = LINE; g.lineWidth = 2;
  for (let i = 0; i < 5; i++) {
    let x = hash(seed, i) * 512, y = hash(seed, i + 0.3) * 512; g.beginPath(); g.moveTo(x, y);
    for (let k = 0; k < 5; k++) { x += (hash(seed, i, k) - 0.5) * 40; y += 12 + hash(seed, k, i) * 16; g.lineTo(x, y); }
    g.stroke();
  }
  speckle(g, 512, 512, 700, 0.05, seed);
  return toTex(c, { repeat: rep, aniso: 8 });
}
export function flagstones(base = '#c9a87a', rep = [1, 1], seed = 3) {
  const [c, g] = canvas(1024, 1024);
  g.fillStyle = base; g.fillRect(0, 0, 1024, 1024);
  for (let y = 0; y < 1024; y += 96) {
    let x = -hash(seed, y) * 120;
    while (x < 1024) {
      const w = 90 + hash(seed, x, y) * 110;
      const sh = (hash(seed, x + 1, y) - 0.5) * 0.12;
      g.fillStyle = `rgba(${sh > 0 ? '255,240,220' : '80,50,20'},${Math.abs(sh)})`;
      g.fillRect(x + 4, y + 4, w - 8, 88);
      g.strokeStyle = LINE; g.lineWidth = 3; g.beginPath(); g.roundRect(x + 3, y + 3, w - 6, 90, 10); g.stroke();
      x += w;
    }
  }
  stain(g, 1024, 1024, 30, seed, 'rgba(110,70,30,0.09)');
  speckle(g, 1024, 1024, 2500, 0.06, seed);
  return toTex(c, { repeat: rep, aniso: 8 });
}
export function sand(base = '#e6b878', rep = [1, 1], seed = 4) {
  const [c, g] = canvas(512, 512);
  g.fillStyle = base; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 70; i++) {
    const y = hash(seed, i) * 512, a = 0.05 + hash(seed, i + 1) * 0.06;
    g.strokeStyle = `rgba(140,80,30,${a})`; g.lineWidth = 3 + hash(seed, i + 2) * 3;
    g.beginPath(); for (let x = 0; x <= 512; x += 16) { const yy = y + Math.sin(x / 40 + i) * 6; x ? g.lineTo(x, yy) : g.moveTo(x, yy); } g.stroke();
  }
  speckle(g, 512, 512, 1200, 0.05, seed);
  return toTex(c, { repeat: rep, aniso: 8 });
}
export function wood(base = '#9a6a3a', rep = [1, 1], seed = 5, planks = 6) {
  const [c, g] = canvas(256, 256);
  g.fillStyle = base; g.fillRect(0, 0, 256, 256);
  const h = 256 / planks;
  for (let i = 0; i < planks; i++) {
    g.fillStyle = `rgba(${hash(seed, i) > 0.5 ? '255,230,200' : '60,30,10'},${0.05 + hash(seed, i + 1) * 0.06})`; g.fillRect(0, i * h, 256, h);
    g.strokeStyle = 'rgba(80,40,15,0.18)'; g.lineWidth = 1.5;
    for (let k = 0; k < 3; k++) { const y = i * h + h * (0.25 + k * 0.25); g.beginPath(); g.moveTo(0, y); g.bezierCurveTo(80, y + 4, 170, y - 4, 256, y + 2); g.stroke(); }
    g.strokeStyle = LINE; g.lineWidth = 2.5; g.beginPath(); g.moveTo(0, i * h); g.lineTo(256, i * h); g.stroke();
  }
  return toTex(c, { repeat: rep, aniso: 8 });
}
export function stripes(a, b, n = 8, vertical = true, edge = null) {
  const [c, g] = canvas(256, 256);
  g.fillStyle = a; g.fillRect(0, 0, 256, 256);
  g.fillStyle = b;
  for (let i = 0; i < n; i++) vertical ? g.fillRect(i * 256 / n, 0, 256 / n / 2, 256) : g.fillRect(0, i * 256 / n, 256, 256 / n / 2);
  if (edge) { g.fillStyle = edge; vertical ? g.fillRect(0, 226, 256, 30) : g.fillRect(226, 0, 30, 256); }
  speckle(g, 256, 256, 300, 0.04, 9);
  return toTex(c, { aniso: 8 });
}
export function carpet(c1 = '#a8202a', c2 = '#f0c24a', c3 = '#1c2c6a', seed = 6) {
  const [c, g] = canvas(256, 384);
  g.fillStyle = c1; g.fillRect(0, 0, 256, 384);
  g.strokeStyle = c2; g.lineWidth = 10; g.strokeRect(14, 14, 228, 356);
  g.fillStyle = c3; g.fillRect(28, 28, 200, 328);
  g.fillStyle = c1; g.beginPath(); g.moveTo(128, 60); g.lineTo(200, 192); g.lineTo(128, 324); g.lineTo(56, 192); g.closePath(); g.fill();
  g.fillStyle = c2; g.beginPath(); g.moveTo(128, 120); g.lineTo(166, 192); g.lineTo(128, 264); g.lineTo(90, 192); g.closePath(); g.fill();
  for (let i = 0; i < 8; i++) { g.fillStyle = c2; g.beginPath(); g.arc(40 + (i % 2) * 176, 50 + Math.floor(i / 2) * 95, 8, 0, Math.PI * 2); g.fill(); }
  g.fillStyle = '#f2ead8'; for (let x = 0; x < 256; x += 10) { g.fillRect(x, 0, 4, 8); g.fillRect(x, 376, 4, 8); }
  return toTex(c, { aniso: 8 });
}
export function lattice(base = '#7a4a24', rep = [1, 1]) {
  const [c, g] = canvas(256, 256);
  g.fillStyle = '#2a160a'; g.fillRect(0, 0, 256, 256);
  g.fillStyle = base;
  for (let x = 0; x < 256; x += 32) for (let y = 0; y < 256; y += 32) { g.beginPath(); g.arc(x + 16, y + 16, 11, 0, Math.PI * 2); g.fill(); g.fillRect(x + 13, y, 6, 32); g.fillRect(x, y + 13, 32, 6); }
  g.strokeStyle = 'rgba(20,10,4,0.6)'; g.lineWidth = 2; for (let x = 0; x < 256; x += 32) for (let y = 0; y < 256; y += 32) { g.beginPath(); g.arc(x + 16, y + 16, 11, 0, Math.PI * 2); g.stroke(); }
  return toTex(c, { repeat: rep, aniso: 8 });
}
export function pyramidBlocks(base = '#d9a865', rep = [1, 1]) {
  const [c, g] = canvas(512, 512);
  g.fillStyle = base; g.fillRect(0, 0, 512, 512);
  for (let r = 0; r < 32; r++) {
    g.fillStyle = `rgba(${r % 2 ? '255,235,200' : '90,50,20'},0.07)`; g.fillRect(0, r * 16, 512, 16);
    g.strokeStyle = 'rgba(90,50,20,0.35)'; g.lineWidth = 1.5; g.beginPath(); g.moveTo(0, r * 16); g.lineTo(512, r * 16); g.stroke();
    for (let x = (r % 2) * 18; x < 512; x += 36) { g.beginPath(); g.moveTo(x, r * 16); g.lineTo(x, r * 16 + 16); g.stroke(); }
  }
  stain(g, 512, 512, 10, 7, 'rgba(120,70,20,0.1)');
  return toTex(c, { repeat: rep, aniso: 8 });
}
export function gradientTex(stops, w = 4, h = 256, vertical = true) {
  const [c, g] = canvas(vertical ? w : h, vertical ? h : w);
  const gr = vertical ? g.createLinearGradient(0, 0, 0, h) : g.createLinearGradient(0, 0, h, 0);
  for (const [t, col] of stops) gr.addColorStop(t, col);
  g.fillStyle = gr; g.fillRect(0, 0, c.width, c.height);
  return toTex(c, { mip: false });
}
export function tally(n, base = '#e8d2a8') {
  const [c, g] = canvas(512, 256);
  g.fillStyle = base; g.fillRect(0, 0, 512, 256);
  stain(g, 512, 256, 8, 11, 'rgba(110,70,30,0.12)');
  g.strokeStyle = '#3a2214'; g.lineWidth = 7; g.lineCap = 'round';
  for (let i = 0; i < n; i++) {
    const grp = Math.floor(i / 5), k = i % 5;
    const x0 = 30 + (grp % 4) * 120, y0 = 40 + Math.floor(grp / 4) * 110;
    if (k < 4) { g.beginPath(); g.moveTo(x0 + k * 18, y0); g.lineTo(x0 + k * 18 + 3, y0 + 70); g.stroke(); }
    else { g.beginPath(); g.moveTo(x0 - 8, y0 + 55); g.lineTo(x0 + 66, y0 + 12); g.stroke(); }
  }
  return toTex(c, { aniso: 8 });
}
