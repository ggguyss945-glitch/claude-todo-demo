// Procedural face painter. Produces a "photo-like" face texture that is planar
// projected onto the front of the low-poly heads (the original video maps photo
// faces onto blocky heads; here every face is painted from parameters).
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

export const DEFAULT_FACE = {
  skin: '#e2b08e', hair: '#3a2416', hairStyle: 'short', beard: 'none', beardColor: null,
  eye: '#4a6a8a', brow: 1.0, lip: '#b06a5a', female: false, age: 0.3, smile: 0.0, eyeOpen: 1.0,
  look: [0, 0], seed: 1, widthK: 1.0, browRaise: 0, makeup: 0,
};

export function paintFace(params, size = 512) {
  const p = { ...DEFAULT_FACE, ...params };
  const W = size, H = Math.round(size * 1.25);
  const [c, g] = canvas(W, H);
  const r = rng(p.seed * 7919 + 13);
  const skin = p.skin;
  // base
  g.fillStyle = skin;
  g.fillRect(0, 0, W, H);
  // broad 3D shading: darker towards the sides and bottom
  let grd = g.createRadialGradient(W * 0.5, H * 0.42, W * 0.12, W * 0.5, H * 0.5, W * 0.72);
  grd.addColorStop(0, rgba('#ffffff', 0.10));
  grd.addColorStop(0.55, rgba('#000000', 0.0));
  grd.addColorStop(1, rgba('#2a1206', 0.55));
  g.fillStyle = grd;
  g.fillRect(0, 0, W, H);
  // forehead + cheekbone highlights
  blob(g, W * 0.5, H * 0.24, W * 0.26, H * 0.1, rgba('#fff4e8', 0.16));
  blob(g, W * 0.28, H * 0.56, W * 0.1, H * 0.07, rgba('#fff0e0', 0.12));
  blob(g, W * 0.72, H * 0.56, W * 0.1, H * 0.07, rgba('#fff0e0', 0.12));
  // jaw shadow
  blob(g, W * 0.5, H * 0.98, W * 0.5, H * 0.14, rgba('#1a0a04', 0.35));
  // temples
  blob(g, W * 0.06, H * 0.38, W * 0.12, H * 0.2, rgba('#2a1206', 0.25));
  blob(g, W * 0.94, H * 0.38, W * 0.12, H * 0.2, rgba('#2a1206', 0.25));
  if (p.female) {
    blob(g, W * 0.27, H * 0.62, W * 0.08, H * 0.04, rgba('#e06060', 0.12 + p.makeup * 0.1));
    blob(g, W * 0.73, H * 0.62, W * 0.08, H * 0.04, rgba('#e06060', 0.12 + p.makeup * 0.1));
  }

  // ---- eyes
  const ey = H * (0.445 - p.browRaise * 0.0);
  for (const side of [-1, 1]) {
    const ex = W * (0.5 + side * 0.2 * p.widthK);
    const ew = W * 0.15, eh = H * 0.04 * p.eyeOpen;
    // socket shadow
    blob(g, ex, ey - eh * 0.6, ew * 1.05, eh * 2.6, rgba('#3a1a0a', 0.28 + p.age * 0.1));
    blob(g, ex + side * ew * 0.1, ey + eh * 1.5, ew * 0.8, eh * 0.9, rgba('#3a1a20', 0.16 + p.age * 0.12));
    // almond
    g.save();
    almond(g, ex, ey, ew, eh, side);
    g.clip();
    let eg = g.createLinearGradient(ex, ey - eh, ex, ey + eh);
    eg.addColorStop(0, '#b9aca2'); eg.addColorStop(0.45, '#ede6df'); eg.addColorStop(1, '#d8cbc2');
    g.fillStyle = eg;
    g.fillRect(ex - ew, ey - eh * 1.5, ew * 2, eh * 3);
    const ix = ex + p.look[0] * ew * 0.35, iy = ey + p.look[1] * eh * 0.3;
    const ir = Math.max(eh * 0.95, W * 0.036);
    const ig = g.createRadialGradient(ix, iy, ir * 0.2, ix, iy, ir);
    ig.addColorStop(0, shade(p.eye, 0.35)); ig.addColorStop(0.7, p.eye); ig.addColorStop(1, shade(p.eye, -0.6));
    g.fillStyle = ig;
    g.beginPath(); g.arc(ix, iy, ir, 0, Math.PI * 2); g.fill();
    g.fillStyle = '#080604';
    g.beginPath(); g.arc(ix, iy, ir * 0.42, 0, Math.PI * 2); g.fill();
    g.fillStyle = 'rgba(255,255,255,0.9)';
    g.beginPath(); g.arc(ix - ir * 0.3, iy - ir * 0.35, ir * 0.16, 0, Math.PI * 2); g.fill();
    // upper lid shadow inside the eye
    g.fillStyle = 'rgba(40,20,10,0.35)';
    g.fillRect(ex - ew, ey - eh * 1.4, ew * 2, eh * 0.7);
    g.restore();
    // lid lines
    g.strokeStyle = rgba('#1c0c06', 0.85);
    g.lineWidth = W * (p.female ? 0.014 : 0.011);
    g.beginPath();
    g.moveTo(ex - ew, ey + side * 0);
    g.quadraticCurveTo(ex, ey - eh * 2.1, ex + ew, ey);
    g.stroke();
    g.strokeStyle = rgba('#3a1a0a', 0.35);
    g.lineWidth = W * 0.005;
    g.beginPath();
    g.moveTo(ex - ew * 0.9, ey - eh * 1.2);
    g.quadraticCurveTo(ex, ey - eh * 3.0, ex + ew * 0.95, ey - eh * 0.9);
    g.stroke();
    g.beginPath();
    g.moveTo(ex - ew * 0.85, ey + eh * 0.5);
    g.quadraticCurveTo(ex, ey + eh * 1.5, ex + ew * 0.9, ey + eh * 0.3);
    g.stroke();
    // brows
    const by = ey - H * (0.07 + p.browRaise * 0.02);
    g.strokeStyle = rgba(p.hairStyle === 'bald' && p.age > 0.6 ? '#9a9088' : (p.hairStyle === 'bald' ? '#5a4030' : p.hair), 0.95);
    for (let i = 0; i < 60 * p.brow; i++) {
      const u = r();
      const bx = ex + side * (u - 0.45) * ew * 2.1;
      const yy = by - Math.sin(u * Math.PI) * H * 0.018 + (r() - 0.5) * H * 0.012;
      g.lineWidth = W * (0.005 + r() * 0.005) * (p.female ? 0.8 : 1.3);
      g.beginPath();
      g.moveTo(bx, yy);
      g.lineTo(bx + side * W * 0.02, yy - H * 0.006);
      g.stroke();
    }
  }
  // ---- nose
  const ny = H * 0.6;
  blob(g, W * 0.5, H * 0.5, W * 0.035, H * 0.1, rgba('#fff6ee', 0.18)); // bridge highlight
  blob(g, W * 0.44, H * 0.52, W * 0.03, H * 0.1, rgba('#3a1a0a', 0.18));
  blob(g, W * 0.56, H * 0.52, W * 0.03, H * 0.1, rgba('#3a1a0a', 0.18));
  blob(g, W * 0.5, ny + H * 0.03, W * 0.11, H * 0.03, rgba('#3a1a0a', 0.35)); // under-nose shadow
  blob(g, W * 0.5, ny - H * 0.01, W * 0.06, H * 0.03, rgba('#fff0e6', 0.2)); // tip
  g.fillStyle = rgba('#2a0e06', 0.7);
  g.beginPath(); g.ellipse(W * 0.455, ny + H * 0.012, W * 0.018, H * 0.009, 0.3, 0, Math.PI * 2); g.fill();
  g.beginPath(); g.ellipse(W * 0.545, ny + H * 0.012, W * 0.018, H * 0.009, -0.3, 0, Math.PI * 2); g.fill();
  g.strokeStyle = rgba('#3a1a0a', 0.3);
  g.lineWidth = W * 0.006;
  g.beginPath(); g.arc(W * 0.43, ny - H * 0.005, W * 0.03, Math.PI * 0.6, Math.PI * 1.4); g.stroke();
  g.beginPath(); g.arc(W * 0.57, ny - H * 0.005, W * 0.03, -Math.PI * 0.4, Math.PI * 0.4); g.stroke();
  // nasolabial folds
  g.strokeStyle = rgba('#3a1a0a', 0.12 + p.age * 0.2);
  g.lineWidth = W * 0.008;
  g.beginPath(); g.moveTo(W * 0.4, ny); g.quadraticCurveTo(W * 0.34, H * 0.7, W * 0.37, H * 0.76); g.stroke();
  g.beginPath(); g.moveTo(W * 0.6, ny); g.quadraticCurveTo(W * 0.66, H * 0.7, W * 0.63, H * 0.76); g.stroke();
  // ---- mouth
  const my = H * 0.715, mw = W * (p.female ? 0.13 : 0.14);
  const sm = p.smile * H * 0.012;
  g.fillStyle = shade(p.lip, -0.15);
  g.beginPath();
  g.moveTo(W * 0.5 - mw, my - sm);
  g.quadraticCurveTo(W * 0.5 - mw * 0.4, my - H * 0.03, W * 0.5, my - H * 0.018);
  g.quadraticCurveTo(W * 0.5 + mw * 0.4, my - H * 0.03, W * 0.5 + mw, my - sm);
  g.quadraticCurveTo(W * 0.5, my + H * 0.004, W * 0.5 - mw, my - sm);
  g.fill();
  g.fillStyle = p.lip;
  g.beginPath();
  g.moveTo(W * 0.5 - mw * 0.95, my - sm);
  g.quadraticCurveTo(W * 0.5, my + H * (p.female ? 0.04 : 0.032), W * 0.5 + mw * 0.95, my - sm);
  g.quadraticCurveTo(W * 0.5, my + H * 0.002, W * 0.5 - mw * 0.95, my - sm);
  g.fill();
  blob(g, W * 0.5, my + H * 0.016, mw * 0.4, H * 0.008, rgba('#ffffff', 0.18));
  g.strokeStyle = rgba('#2a0a06', 0.75);
  g.lineWidth = W * 0.007;
  g.beginPath();
  g.moveTo(W * 0.5 - mw, my - sm);
  g.quadraticCurveTo(W * 0.5, my + H * 0.006 - sm * 0.3, W * 0.5 + mw, my - sm);
  g.stroke();
  blob(g, W * 0.5, my + H * 0.06, W * 0.1, H * 0.025, rgba('#3a1a0a', 0.22)); // under lip
  // ---- beard
  const bc = p.beardColor || p.hair;
  if (p.beard !== 'none') {
    const dens = { stubble: 0.35, full: 1.0, goatee: 0.9, mustache: 0.9 }[p.beard];
    const n = Math.round(9000 * dens);
    for (let i = 0; i < n; i++) {
      const x = r(), y = r();
      const px = x * W, py = H * (0.6 + y * 0.42);
      let inside = false;
      const dx = (x - 0.5) / 0.5;
      if (p.beard === 'full' || p.beard === 'stubble') {
        inside = py > H * (0.63 + 0.12 * (1 - Math.abs(dx)) * 0) && Math.abs(dx) < 0.98 - (py < H * 0.68 ? 0.4 : 0);
        if (py < H * 0.69 && Math.abs(dx) < 0.32) inside = py > H * 0.645; // mustache band
        if (py > H * 0.69 && py < H * 0.735 && Math.abs(dx) < 0.3) inside = false; // lips
      } else if (p.beard === 'goatee') {
        inside = (Math.abs(dx) < 0.32 && py > H * 0.645 && py < H * 0.69) || (Math.abs(dx) < 0.22 && py > H * 0.75);
      } else if (p.beard === 'mustache') {
        inside = Math.abs(dx) < 0.34 && py > H * 0.645 && py < H * 0.69;
      }
      if (!inside) continue;
      g.fillStyle = rgba(bc, 0.35 + r() * 0.5);
      g.fillRect(px, py, W * 0.006, H * 0.012);
    }
  }
  // ---- hair
  const hairTop = { bald: 0, short: 0.17, slick: 0.16, bun: 0.18, long: 0.19, curly: 0.2, buzz: 0.13 }[p.hairStyle];
  if (p.hairStyle === 'bald') {
    blob(g, W * 0.5, H * 0.08, W * 0.3, H * 0.08, rgba('#ffffff', 0.22));
    if (p.age > 0.5) {
      g.fillStyle = rgba('#c0b8b0', 0.5);
      for (let i = 0; i < 1600; i++) { const x = r(); if (x > 0.15 && x < 0.85) continue; g.fillRect(x * W, H * (0.2 + r() * 0.2), 2, 3); }
    }
  } else {
    g.fillStyle = p.hair;
    g.beginPath();
    g.moveTo(0, 0);
    g.lineTo(W, 0);
    g.lineTo(W, H * (hairTop + 0.16));
    g.quadraticCurveTo(W * 0.92, H * hairTop * 0.95, W * 0.7, H * hairTop * 0.9);
    g.quadraticCurveTo(W * 0.5, H * (hairTop + 0.02), W * 0.3, H * hairTop * 0.9);
    g.quadraticCurveTo(W * 0.08, H * hairTop * 0.95, 0, H * (hairTop + 0.16));
    g.closePath();
    g.fill();
    for (let i = 0; i < 900; i++) {
      const x = r() * W, y = r() * H * (hairTop + 0.05);
      g.strokeStyle = rgba(r() < 0.5 ? '#000000' : '#ffffff', 0.08 + r() * 0.08);
      g.lineWidth = 1 + r() * 2;
      g.beginPath(); g.moveTo(x, y); g.lineTo(x + (r() - 0.5) * W * 0.06, y + H * 0.03); g.stroke();
    }
    if (p.hairStyle === 'long' || p.female) {
      g.fillStyle = p.hair;
      g.fillRect(0, 0, W * 0.07, H * 0.8);
      g.fillRect(W * 0.93, 0, W * 0.07, H * 0.8);
    }
  }
  // skin pores / photo grain
  noiseFill(g, W, H, 0, 10, p.seed + 5, 2);
  const t = toTex(c);
  return { tex: t, canvas: c };
}

function blob(g, x, y, rx, ry, col) {
  const grd = g.createRadialGradient(x, y, 0, x, y, 1);
  grd.addColorStop(0, col);
  grd.addColorStop(1, col.replace(/[\d.]+\)$/, '0)'));
  g.save();
  g.translate(x, y);
  g.scale(rx, ry);
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

// Flat colour for the parts of the head that are not the face projection.
export function headSideColor(p) {
  const q = { ...DEFAULT_FACE, ...p };
  return q.hairStyle === 'bald' ? q.skin : q.hair;
}
