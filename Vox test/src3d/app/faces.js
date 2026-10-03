// Procedural face painter (V3). Produces a photo-like face texture that is planar
// projected onto the front of the low-poly heads (the original maps photo faces
// onto blocky heads; here every face is painted from parameters, no images).
import { canvas, toTex, noiseFill } from './tex.js';
import { rng } from './util.js';

function hexRGB(h) {
  h = h.replace('#', '');
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
}
function rgba(h, a) { const [r, g, b] = hexRGB(h); return `rgba(${r},${g},${b},${a})`; }
function shade(h, k) {
  const [r, g, b] = hexRGB(h);
  const f = (v) => Math.max(0, Math.min(255, Math.round(k >= 0 ? v + (255 - v) * k : v * (1 + k))));
  return `rgb(${f(r)},${f(g)},${f(b)})`;
}
function shadeHex(h, k) {
  const [r, g, b] = hexRGB(h);
  const f = (v) => Math.max(0, Math.min(255, Math.round(k >= 0 ? v + (255 - v) * k : v * (1 + k))));
  return '#' + [r, g, b].map((v) => f(v).toString(16).padStart(2, '0')).join('');
}

export const DEFAULT_FACE = {
  skin: '#e2b08e', hair: '#3a2416', hairStyle: 'short', beard: 'none', beardColor: null,
  eye: '#4a6a8a', brow: 1.0, lip: '#b06a5a', female: false, age: 0.3, smile: 0.0, eyeOpen: 1.0,
  look: [0, 0], seed: 1, widthK: 1.0, browRaise: 0, makeup: 0,
};

const cache = new Map();

export function paintFace(params, size = 640) {
  const p = { ...DEFAULT_FACE, ...params };
  const key = JSON.stringify(p) + size;
  if (cache.has(key)) return cache.get(key);
  const W = size, H = Math.round(size * 1.25);
  const [c, g] = canvas(W, H);
  const r = rng(p.seed * 7919 + 13);
  const skin = p.skin;
  const dark = shadeHex(skin, -0.45), deep = shadeHex(skin, -0.7), light = shadeHex(skin, 0.25);
  // ---- base with low-frequency mottling (warm/cool variation like real skin)
  g.fillStyle = skin;
  g.fillRect(0, 0, W, H);
  for (let i = 0; i < 70; i++) {
    const x = r() * W, y = r() * H, rr = W * (0.05 + r() * 0.12);
    blob(g, x, y, rr, rr, rgba(r() < 0.5 ? '#b0503a' : '#f0d8c0', 0.05 + r() * 0.04));
  }
  // 3D form shading
  let grd = g.createRadialGradient(W * 0.5, H * 0.45, W * 0.1, W * 0.5, H * 0.5, W * 0.75);
  grd.addColorStop(0, rgba('#ffffff', 0.08));
  grd.addColorStop(0.5, rgba('#000000', 0.0));
  grd.addColorStop(1, rgba(deep, 0.6));
  g.fillStyle = grd;
  g.fillRect(0, 0, W, H);
  blob(g, W * 0.5, H * 0.23, W * 0.3, H * 0.11, rgba('#fff6ec', 0.18)); // forehead sheen
  blob(g, W * 0.27, H * 0.57, W * 0.11, H * 0.07, rgba('#fff0e2', 0.14)); // cheekbones
  blob(g, W * 0.73, H * 0.57, W * 0.11, H * 0.07, rgba('#fff0e2', 0.14));
  blob(g, W * 0.26, H * 0.64, W * 0.1, H * 0.06, rgba('#d0604a', 0.10 + (p.female ? 0.08 + p.makeup * 0.08 : 0))); // cheek warmth
  blob(g, W * 0.74, H * 0.64, W * 0.1, H * 0.06, rgba('#d0604a', 0.10 + (p.female ? 0.08 + p.makeup * 0.08 : 0)));
  blob(g, W * 0.5, H * 0.99, W * 0.55, H * 0.15, rgba(deep, 0.45)); // jaw
  blob(g, W * 0.05, H * 0.4, W * 0.13, H * 0.22, rgba(deep, 0.3)); // temples
  blob(g, W * 0.95, H * 0.4, W * 0.13, H * 0.22, rgba(deep, 0.3));
  blob(g, W * 0.12, H * 0.72, W * 0.1, H * 0.16, rgba(deep, 0.22)); // under cheekbone hollows
  blob(g, W * 0.88, H * 0.72, W * 0.1, H * 0.16, rgba(deep, 0.22));
  // age lines
  if (p.age > 0.45) {
    g.strokeStyle = rgba(dark, (p.age - 0.45) * 0.5);
    g.lineWidth = W * 0.004;
    for (let k = 0; k < 3; k++) {
      g.beginPath();
      g.moveTo(W * 0.3, H * (0.17 + k * 0.035));
      g.quadraticCurveTo(W * 0.5, H * (0.155 + k * 0.035), W * 0.7, H * (0.17 + k * 0.035));
      g.stroke();
    }
  }

  // ---- eyes
  const ey = H * 0.445;
  for (const side of [-1, 1]) {
    const ex = W * (0.5 + side * 0.19 * p.widthK);
    const ew = W * 0.108, eh = H * 0.029 * p.eyeOpen;
    blob(g, ex, ey - H * 0.022, ew * 1.15, H * 0.075, rgba(deep, 0.32 + p.age * 0.1)); // socket
    blob(g, ex + side * ew * 0.12, ey + H * 0.048, ew * 0.85, H * 0.03, rgba('#5a2a30', 0.16 + p.age * 0.14)); // under-eye
    blob(g, ex - side * ew * 0.75, ey, W * 0.03, H * 0.03, rgba('#5a2a24', 0.25)); // inner corner shadow
    if (p.eyeOpen > 0.2) {
      g.save();
      almond(g, ex, ey, ew, eh, side);
      g.clip();
      let eg = g.createLinearGradient(ex, ey - eh * 1.4, ex, ey + eh * 1.4);
      eg.addColorStop(0, '#a89a90'); eg.addColorStop(0.45, '#efe8e2'); eg.addColorStop(1, '#d6c8be');
      g.fillStyle = eg;
      g.fillRect(ex - ew, ey - eh * 1.6, ew * 2, eh * 3.2);
      blob(g, ex - side * ew * 0.75, ey, ew * 0.25, eh * 0.8, rgba('#d08080', 0.55)); // caruncle
      const ix = ex + p.look[0] * ew * 0.35, iy = ey + p.look[1] * eh * 0.3 - eh * 0.1;
      const ir = Math.max(eh * 1.08, W * 0.03);
      const ig = g.createRadialGradient(ix, iy, ir * 0.15, ix, iy, ir);
      ig.addColorStop(0, shade(p.eye, 0.45)); ig.addColorStop(0.55, p.eye); ig.addColorStop(0.88, shade(p.eye, -0.35)); ig.addColorStop(1, shade(p.eye, -0.85));
      g.fillStyle = ig;
      g.beginPath(); g.arc(ix, iy, ir, 0, Math.PI * 2); g.fill();
      g.strokeStyle = rgba(shadeHex(p.eye, 0.5), 0.35);
      g.lineWidth = W * 0.0018;
      for (let k = 0; k < 28; k++) { // iris fibres
        const a = (k / 28) * Math.PI * 2;
        g.beginPath(); g.moveTo(ix + Math.cos(a) * ir * 0.42, iy + Math.sin(a) * ir * 0.42); g.lineTo(ix + Math.cos(a) * ir * 0.9, iy + Math.sin(a) * ir * 0.9); g.stroke();
      }
      g.fillStyle = '#060404';
      g.beginPath(); g.arc(ix, iy, ir * 0.38, 0, Math.PI * 2); g.fill();
      g.fillStyle = 'rgba(255,255,255,0.95)';
      g.beginPath(); g.arc(ix - ir * 0.32, iy - ir * 0.34, ir * 0.16, 0, Math.PI * 2); g.fill();
      g.fillStyle = 'rgba(255,255,255,0.4)';
      g.beginPath(); g.arc(ix + ir * 0.35, iy + ir * 0.3, ir * 0.07, 0, Math.PI * 2); g.fill();
      g.fillStyle = 'rgba(40,20,10,0.42)'; // lid shadow on the eyeball
      g.fillRect(ex - ew, ey - eh * 1.6, ew * 2, eh * 0.95);
      g.restore();
    }
    // upper lid crease + lash line
    g.strokeStyle = rgba('#140804', 0.9);
    g.lineWidth = W * (p.female ? 0.013 : 0.0095);
    g.beginPath();
    g.moveTo(ex - ew, ey + eh * 0.1 * side);
    g.bezierCurveTo(ex - ew * 0.5, ey - eh * 2.0, ex + ew * 0.45, ey - eh * 2.0, ex + ew, ey - eh * 0.1 * side);
    g.stroke();
    if (p.female || p.makeup) {
      g.lineWidth = W * 0.004;
      for (let k = 0; k < 9; k++) {
        const u = 0.15 + k * 0.09;
        const lx = ex - ew + ew * 2 * u, ly = ey - eh * 1.45 * Math.sin(Math.PI * u);
        g.beginPath(); g.moveTo(lx, ly); g.lineTo(lx + side * W * 0.008 * (u - 0.3), ly - H * 0.012); g.stroke();
      }
    }
    g.strokeStyle = rgba(dark, 0.45);
    g.lineWidth = W * 0.005;
    g.beginPath();
    g.moveTo(ex - ew * 0.9, ey - eh * 1.3 - H * 0.008);
    g.quadraticCurveTo(ex, ey - eh * 3.1 - H * 0.012, ex + ew * 0.95, ey - eh * 1.0 - H * 0.006);
    g.stroke();
    g.strokeStyle = rgba(dark, 0.4);
    g.beginPath();
    g.moveTo(ex - ew * 0.85, ey + eh * 0.55);
    g.quadraticCurveTo(ex, ey + eh * 1.6, ex + ew * 0.9, ey + eh * 0.35);
    g.stroke();
    // brows: many short hair strokes along an arch
    const by = ey - H * (0.075 + p.browRaise * 0.022);
    const browCol = p.hairStyle === 'bald' ? (p.age > 0.6 ? '#9a9088' : shadeHex(skin, -0.62)) : shadeHex(p.hair, 0.05);
    for (let i = 0; i < 110 * p.brow; i++) {
      const u = r();
      const bx = ex + side * (u - 0.42) * ew * 2.15;
      const arch = Math.sin(Math.min(1, u * 1.15) * Math.PI) * H * 0.02;
      const yy = by - arch + (r() - 0.5) * H * 0.014 * (1 - Math.abs(u - 0.4));
      g.strokeStyle = rgba(browCol, 0.55 + r() * 0.4);
      g.lineWidth = W * (0.003 + r() * 0.004) * (p.female ? 0.75 : 1.15);
      g.beginPath();
      g.moveTo(bx, yy);
      g.lineTo(bx + side * W * (0.016 + r() * 0.01), yy - H * (0.004 + r() * 0.004));
      g.stroke();
    }
  }
  // ---- nose
  const ny = H * 0.6;
  blob(g, W * 0.5, H * 0.5, W * 0.035, H * 0.11, rgba('#fff8f0', 0.22)); // bridge
  blob(g, W * 0.435, H * 0.52, W * 0.035, H * 0.1, rgba(deep, 0.2));
  blob(g, W * 0.565, H * 0.52, W * 0.035, H * 0.1, rgba(deep, 0.2));
  blob(g, W * 0.5, ny + H * 0.035, W * 0.12, H * 0.032, rgba(deep, 0.45)); // under-nose
  blob(g, W * 0.5, ny - H * 0.008, W * 0.065, H * 0.032, rgba('#fff0e6', 0.26)); // tip highlight
  blob(g, W * 0.5, ny - H * 0.004, W * 0.07, H * 0.03, rgba('#c05040', 0.08));
  for (const sd of [-1, 1]) {
    g.fillStyle = rgba('#1e0a04', 0.75);
    g.beginPath(); g.ellipse(W * (0.5 + sd * 0.045), ny + H * 0.014, W * 0.019, H * 0.009, sd * -0.35, 0, Math.PI * 2); g.fill();
    g.strokeStyle = rgba(dark, 0.4);
    g.lineWidth = W * 0.006;
    g.beginPath(); g.arc(W * (0.5 + sd * 0.07), ny - H * 0.003, W * 0.03, sd < 0 ? Math.PI * 0.55 : -Math.PI * 0.45, sd < 0 ? Math.PI * 1.45 : Math.PI * 0.45); g.stroke();
  }
  // nasolabial folds
  g.strokeStyle = rgba(dark, 0.14 + p.age * 0.22 + Math.max(0, p.smile) * 0.12);
  g.lineWidth = W * 0.009;
  for (const sd of [-1, 1]) {
    g.beginPath(); g.moveTo(W * (0.5 + sd * 0.1), ny); g.quadraticCurveTo(W * (0.5 + sd * 0.17), H * 0.7, W * (0.5 + sd * 0.135), H * 0.77); g.stroke();
  }
  // ---- mouth
  const my = H * 0.715, mw = W * (p.female ? 0.125 : 0.138);
  const sm = p.smile * H * 0.014;
  blob(g, W * 0.5, my - H * 0.03, W * 0.03, H * 0.02, rgba(dark, 0.25)); // philtrum
  g.fillStyle = shade(p.lip, -0.2);
  g.beginPath();
  g.moveTo(W * 0.5 - mw, my - sm);
  g.quadraticCurveTo(W * 0.5 - mw * 0.45, my - H * 0.032, W * 0.5 - mw * 0.1, my - H * 0.024);
  g.quadraticCurveTo(W * 0.5, my - H * 0.017, W * 0.5 + mw * 0.1, my - H * 0.024);
  g.quadraticCurveTo(W * 0.5 + mw * 0.45, my - H * 0.032, W * 0.5 + mw, my - sm);
  g.quadraticCurveTo(W * 0.5, my + H * 0.003, W * 0.5 - mw, my - sm);
  g.fill();
  const lg = g.createLinearGradient(0, my, 0, my + H * 0.04);
  lg.addColorStop(0, shade(p.lip, -0.1)); lg.addColorStop(0.5, p.lip); lg.addColorStop(1, shade(p.lip, -0.25));
  g.fillStyle = lg;
  g.beginPath();
  g.moveTo(W * 0.5 - mw * 0.95, my - sm);
  g.quadraticCurveTo(W * 0.5, my + H * (p.female ? 0.042 : 0.034), W * 0.5 + mw * 0.95, my - sm);
  g.quadraticCurveTo(W * 0.5, my + H * 0.002, W * 0.5 - mw * 0.95, my - sm);
  g.fill();
  blob(g, W * 0.5, my + H * 0.017, mw * 0.42, H * 0.008, rgba('#ffffff', 0.22));
  g.strokeStyle = rgba('#240806', 0.8);
  g.lineWidth = W * 0.0075;
  g.beginPath();
  g.moveTo(W * 0.5 - mw * 1.02, my - sm * 1.1);
  g.quadraticCurveTo(W * 0.5, my + H * 0.007 - sm * 0.3, W * 0.5 + mw * 1.02, my - sm * 1.1);
  g.stroke();
  blob(g, W * 0.5 - mw * 1.05, my - sm, W * 0.02, H * 0.014, rgba(dark, 0.35)); // mouth corners
  blob(g, W * 0.5 + mw * 1.05, my - sm, W * 0.02, H * 0.014, rgba(dark, 0.35));
  blob(g, W * 0.5, my + H * 0.065, W * 0.11, H * 0.028, rgba(dark, 0.26)); // chin crease
  blob(g, W * 0.5, my + H * 0.12, W * 0.12, H * 0.04, rgba('#fff0e6', 0.12)); // chin
  // ---- male stubble shadow
  if (!p.female && p.beard !== 'full') {
    blob(g, W * 0.5, H * 0.86, W * 0.42, H * 0.17, rgba(shadeHex(p.beardColor || p.hair, -0.2), 0.12 + (p.beard === 'stubble' ? 0.2 : 0)));
  }
  // ---- beard
  const bc = p.beardColor || p.hair;
  if (p.beard !== 'none') {
    const dens = { stubble: 0.4, full: 1.0, goatee: 1.0, mustache: 0.95 }[p.beard];
    const n = Math.round(16000 * dens);
    for (let i = 0; i < n; i++) {
      const x = r(), y = r();
      const px = x * W, py = H * (0.6 + y * 0.42);
      const dx = (x - 0.5) / 0.5;
      let inside = false;
      const must = Math.abs(dx) < 0.33 && py > H * 0.648 && py < H * 0.69;
      const lips = Math.abs(dx) < 0.29 && py > H * 0.69 && py < H * 0.74;
      if (p.beard === 'full' || p.beard === 'stubble') inside = (must || (py > H * 0.69 && Math.abs(dx) < 0.98 - Math.max(0, (H * 0.74 - py) / H) * 6)) && !lips;
      else if (p.beard === 'goatee') inside = must || (Math.abs(dx) < 0.24 && py > H * 0.745) || (Math.abs(dx) > 0.26 && Math.abs(dx) < 0.36 && py > H * 0.66 && py < H * 0.78);
      else if (p.beard === 'mustache') inside = must;
      if (!inside) continue;
      g.strokeStyle = rgba(r() < 0.8 ? bc : shadeHex(bc, 0.35), 0.3 + r() * 0.55);
      g.lineWidth = W * (0.003 + r() * 0.003);
      g.beginPath(); g.moveTo(px, py); g.lineTo(px + (r() - 0.5) * W * 0.008, py + H * (0.008 + r() * 0.008)); g.stroke();
    }
  }
  // ---- hair line
  const hairTop = { bald: 0, short: 0.17, slick: 0.16, bun: 0.18, long: 0.19, curly: 0.21, buzz: 0.13 }[p.hairStyle];
  if (p.hairStyle === 'bald') {
    blob(g, W * 0.5, H * 0.07, W * 0.32, H * 0.09, rgba('#ffffff', 0.26));
    if (p.age > 0.5) {
      for (let i = 0; i < 2600; i++) {
        const x = r(); if (x > 0.14 && x < 0.86) continue;
        g.fillStyle = rgba('#c8c0b8', 0.5 * r());
        g.fillRect(x * W, H * (0.2 + r() * 0.25), 2, 4);
      }
    }
  } else {
    g.fillStyle = p.hair;
    g.beginPath();
    g.moveTo(0, 0);
    g.lineTo(W, 0);
    g.lineTo(W, H * (hairTop + 0.17));
    g.quadraticCurveTo(W * 0.93, H * hairTop * 0.95, W * 0.7, H * hairTop * 0.9);
    g.quadraticCurveTo(W * 0.5, H * (hairTop + 0.025), W * 0.3, H * hairTop * 0.9);
    g.quadraticCurveTo(W * 0.07, H * hairTop * 0.95, 0, H * (hairTop + 0.17));
    g.closePath();
    g.fill();
    for (let i = 0; i < 2600; i++) { // strands + soft hairline
      const x = r() * W, y = r() * H * (hairTop + 0.06);
      g.strokeStyle = rgba(r() < 0.55 ? '#000000' : '#ffffff', 0.06 + r() * 0.1);
      g.lineWidth = 1 + r() * 2;
      g.beginPath(); g.moveTo(x, y); g.lineTo(x + (r() - 0.5) * W * 0.05, y + H * 0.035); g.stroke();
    }
    blob(g, W * 0.5, H * (hairTop + 0.02), W * 0.35, H * 0.03, rgba(deep, 0.25));
    if (p.hairStyle === 'long' || p.female) {
      g.fillStyle = p.hair;
      g.fillRect(0, 0, W * 0.075, H * 0.82);
      g.fillRect(W * 0.925, 0, W * 0.075, H * 0.82);
    }
  }
  noiseFill(g, W, H, 0, 9, p.seed + 5, 2); // pores / photo grain
  noiseFill(g, W, H, 0, 5, p.seed + 6, 1);
  const res = { tex: toTex(c), canvas: c };
  cache.set(key, res);
  return res;
}

function blob(g, x, y, rx, ry, col) {
  const grd = g.createRadialGradient(x, y, 0, x, y, 1);
  grd.addColorStop(0, col);
  grd.addColorStop(1, col.replace(/[\d.]+\)$/, '0)'));
  g.save();
  g.translate(x, y);
  g.scale(Math.max(rx, 0.01), Math.max(ry, 0.01));
  g.fillStyle = grd;
  g.beginPath();
  g.arc(0, 0, 1, 0, Math.PI * 2);
  g.fill();
  g.restore();
}

function almond(g, ex, ey, ew, eh, side) {
  g.beginPath();
  g.moveTo(ex - ew, ey + eh * 0.15 * side);
  g.bezierCurveTo(ex - ew * 0.5, ey - eh * 2.0, ex + ew * 0.45, ey - eh * 2.0, ex + ew, ey - eh * 0.15 * side);
  g.bezierCurveTo(ex + ew * 0.5, ey + eh * 1.4, ex - ew * 0.5, ey + eh * 1.4, ex - ew, ey + eh * 0.15 * side);
  g.closePath();
}

export function headSideColor(p) {
  const q = { ...DEFAULT_FACE, ...p };
  return q.hairStyle === 'bald' ? q.skin : q.hair;
}
