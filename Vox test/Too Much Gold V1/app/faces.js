// Drawn cartoon faces painted onto the front of a sphere head (planar projection).
// Coordinates are in head radii: x right, y up, (0,0) = centre of the face.
import * as THREE from 'three';

const INK = '#141010';

// expression presets
export const EXPR = {
  neutral: { eyes: 'dot', brows: [0, 0], mouth: 'line' },
  calm: { eyes: 'dot', brows: [0.1, 0], mouth: 'smile' },
  happy: { eyes: 'open', brows: [0.4, -6], mouth: 'bigsmile' },
  joy: { eyes: 'happy', brows: [0.5, -10], mouth: 'bigsmile', blush: 1 },
  grin: { eyes: 'open', brows: [0.25, 8], mouth: 'grin' },
  proud: { eyes: 'half', brows: [0.15, -4], mouth: 'smirk' },
  smug: { eyes: 'half', brows: [0.0, 10], mouth: 'smirk' },
  greedy: { eyes: 'money', brows: [0.45, -10], mouth: 'grin', goldTooth: 1 },
  bored: { eyes: 'half', brows: [-0.1, 0], mouth: 'line' },
  unimpressed: { eyes: 'half', brows: [[-0.15, 0], [0.35, -6]], mouth: 'flat' },
  surprised: { eyes: 'open', brows: [0.7, -8], mouth: 'o' },
  shocked: { eyes: 'wide', brows: [0.9, -12], mouth: 'open', sweat: 1 },
  panic: { eyes: 'wide', brows: [0.8, -18], mouth: 'shout', sweat: 1 },
  worried: { eyes: 'open', brows: [0.45, -20], mouth: 'wavy', sweat: 1 },
  sheepish: { eyes: 'open', brows: [0.35, -18], mouth: 'grin', sweat: 1, blush: 0.6 },
  angry: { eyes: 'open', brows: [-0.2, 24], mouth: 'frown', vein: 1 },
  confused: { eyes: 'open', brows: [[0.5, -8], [-0.1, 12]], mouth: 'wavy' },
  laugh: { eyes: 'happy', brows: [0.4, -6], mouth: 'shout', blush: 0.4 },
  sleepy: { eyes: 'closed', brows: [0, 0], mouth: 'line' },
  dazzled: { eyes: 'money', brows: [0.6, -10], mouth: 'open' },
  shrug: { eyes: 'half', brows: [0.55, -14], mouth: 'smirk' },
};

const cache = new Map();
const MAX = 160;

function ell(g, x, y, rx, ry, rot = 0) { g.beginPath(); g.ellipse(x, y, Math.max(rx, 0.5), Math.max(ry, 0.5), rot, 0, Math.PI * 2); }

export function paintFace(def, state, res = 640) {
  const e = { ...EXPR[state.expr || 'neutral'] };
  const look = state.look || [0, 0];
  const talk = Math.round((state.talk || 0) * 4) / 4;
  const blink = !!state.blink;
  const key = [def.id, state.expr, look.map((v) => v.toFixed(2)).join(','), talk, blink ? 1 : 0, state.extra || ''].join('|');
  if (cache.has(key)) { const v = cache.get(key); cache.delete(key); cache.set(key, v); return v; }
  const c = document.createElement('canvas'); c.width = c.height = res;
  const g = c.getContext('2d');
  const S = res;
  const P = (x, y) => [S * (0.5 + x / 2), S * (0.5 - y / 2)];
  const u = S / 2; // one head radius in px
  g.fillStyle = def.skin; g.fillRect(0, 0, S, S);
  // soft cheek warmth, very subtle
  const cg = g.createRadialGradient(...P(0, -0.15), 0, ...P(0, -0.15), u * 0.9);
  cg.addColorStop(0, 'rgba(255,255,255,0.06)'); cg.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = cg; g.fillRect(0, 0, S, S);
  g.lineCap = 'round'; g.lineJoin = 'round';
  const lw = u * 0.045;
  const ey = 0.08 + (def.eyeY || 0), ex = 0.3 * (def.eyeSpread || 1);

  // drawn beard: a crescent along the jaw that leaves the mouth clear
  if (def.beard) {
    const full = def.beard === 'full';
    g.fillStyle = def.beardColor || def.hair || INK;
    const a0 = Math.PI + (full ? 0.12 : 0.62), a1 = 2 * Math.PI - (full ? 0.12 : 0.62);
    const myb = -0.34 + (def.mouthY || 0);
    g.beginPath();
    for (let i = 0; i <= 28; i++) {
      const a = a0 + (a1 - a0) * (i / 28);
      const rr = (full ? 0.88 : 0.76) + (i % 2 ? 0.03 : 0) * (i > 2 && i < 26 ? 1 : 0);
      const [x, y] = P(Math.cos(a) * rr * 0.9, -0.08 + Math.sin(a) * rr * 0.92);
      i ? g.lineTo(x, y) : g.moveTo(x, y);
    }
    const ex1 = Math.cos(a1) * (full ? 0.88 : 0.76) * 0.9, ey1 = -0.08 + Math.sin(a1) * (full ? 0.88 : 0.76) * 0.92;
    g.quadraticCurveTo(...P(ex1 * 0.75, myb + 0.02), ...P(0.26, myb - 0.08));
    g.quadraticCurveTo(...P(0, myb - 0.26), ...P(-0.26, myb - 0.08));
    g.quadraticCurveTo(...P(-ex1 * 0.75, myb + 0.02), ...P(-ex1, ey1));
    g.closePath(); g.fill();
    g.strokeStyle = INK; g.lineWidth = u * 0.012; g.stroke();
  }
  // ---- eyes
  for (const sd of [-1, 1]) {
    const [cx, cy] = P(sd * ex, ey);
    const lx = look[0] * u * 0.06, ly = -look[1] * u * 0.05;
    const type = blink ? 'closed' : e.eyes;
    g.strokeStyle = INK; g.fillStyle = INK; g.lineWidth = lw * 0.6;
    if (type === 'dot') {
      ell(g, cx + lx * 0.6, cy + ly * 0.6, u * 0.058, u * 0.078); g.fill();
    } else if (type === 'open' || type === 'wide' || type === 'money') {
      const rx = u * (type === 'wide' ? 0.17 : 0.135), ry = u * (type === 'wide' ? 0.2 : 0.16);
      g.fillStyle = '#fbfbf6'; ell(g, cx, cy, rx, ry); g.fill(); g.stroke();
      if (type === 'money') {
        const pr = u * 0.085;
        g.fillStyle = '#ffc21a'; ell(g, cx + lx, cy + ly, pr, pr); g.fill(); g.lineWidth = lw * 0.45; g.stroke();
        g.strokeStyle = '#b07800'; g.lineWidth = lw * 0.35; ell(g, cx + lx, cy + ly, pr * 0.62, pr * 0.62); g.stroke();
        g.fillStyle = 'rgba(255,255,255,0.95)'; ell(g, cx + lx - pr * 0.35, cy + ly - pr * 0.35, pr * 0.22, pr * 0.22); g.fill();
      } else {
        const pr = u * (type === 'wide' ? 0.05 : 0.068);
        g.fillStyle = INK; ell(g, cx + lx, cy + ly, pr, pr * 1.08); g.fill();
        g.fillStyle = 'rgba(255,255,255,0.95)'; ell(g, cx + lx - pr * 0.35, cy + ly - pr * 0.4, pr * 0.3, pr * 0.3); g.fill();
      }
    } else if (type === 'half') {
      const rx = u * 0.13, ry = u * 0.14;
      g.save(); g.beginPath(); g.rect(cx - rx * 1.5, cy - ry * 0.05, rx * 3, ry * 2); g.clip();
      g.fillStyle = '#fbfbf6'; ell(g, cx, cy, rx, ry); g.fill(); g.lineWidth = lw * 0.6; g.stroke();
      g.fillStyle = INK; ell(g, cx + lx, cy + ly + ry * 0.35, u * 0.06, u * 0.06); g.fill();
      g.restore();
      g.lineWidth = lw * 0.9; g.beginPath(); g.moveTo(cx - rx * 1.05, cy); g.lineTo(cx + rx * 1.05, cy); g.stroke();
    } else if (type === 'happy') {
      g.lineWidth = lw; g.beginPath(); g.arc(cx, cy + u * 0.05, u * 0.1, Math.PI * 1.1, Math.PI * 1.9); g.stroke();
    } else if (type === 'closed') {
      g.lineWidth = lw * 0.85; g.beginPath(); g.arc(cx, cy - u * 0.05, u * 0.1, Math.PI * 0.12, Math.PI * 0.88); g.stroke();
    }
  }
  // ---- brows
  const br = Array.isArray(e.brows[0]) ? e.brows : [e.brows, e.brows];
  for (const sd of [-1, 1]) {
    const [raise, ang] = sd < 0 ? br[0] : br[1];
    const by = ey + 0.27 + raise * 0.08 + (def.browY || 0);
    const a = (ang * Math.PI / 180) * sd;       // positive = inner end down (cross)
    const len = 0.13 * (def.browLen || 1);
    const [cx, cy] = P(sd * (ex + 0.02), by);
    const dx = Math.cos(a) * len * u, dy = Math.sin(a) * len * u;
    g.strokeStyle = INK; g.lineWidth = lw * (def.browW || 1.15);
    g.beginPath(); g.moveTo(cx - dx, cy - dy); g.quadraticCurveTo(cx, cy - u * 0.035, cx + dx, cy + dy); g.stroke();
  }
  // ---- moustache (drawn)
  const my = -0.34 + (def.mouthY || 0);
  // ---- mouth
  let m = e.mouth;
  if (talk > 0) m = talk >= 0.75 ? (m === 'grin' || m === 'bigsmile' ? 'bigsmile' : 'open') : talk >= 0.5 ? 'openSmall' : 'o';
  {
    const [cx, cy] = P(0, my);
    g.strokeStyle = INK; g.lineWidth = lw; g.fillStyle = '#3a0d0d';
    const W = u * 0.17 * (def.mouthW || 1);
    if (m === 'line' || m === 'flat') { g.beginPath(); g.moveTo(cx - W * (m === 'flat' ? 0.8 : 1), cy); g.lineTo(cx + W * (m === 'flat' ? 0.8 : 1), cy); g.stroke(); }
    else if (m === 'smile') { g.beginPath(); g.moveTo(cx - W, cy - u * 0.03); g.quadraticCurveTo(cx, cy + u * 0.12, cx + W, cy - u * 0.03); g.stroke(); }
    else if (m === 'frown') { g.beginPath(); g.moveTo(cx - W, cy + u * 0.05); g.quadraticCurveTo(cx, cy - u * 0.08, cx + W, cy + u * 0.05); g.stroke(); }
    else if (m === 'smirk') { g.beginPath(); g.moveTo(cx - W, cy + u * 0.01); g.quadraticCurveTo(cx + W * 0.2, cy + u * 0.05, cx + W * 1.05, cy - u * 0.07); g.stroke(); }
    else if (m === 'wavy') {
      g.lineWidth = lw * 0.85; g.beginPath();
      for (let i = 0; i <= 12; i++) { const x = cx - W + (2 * W * i) / 12, y = cy + Math.sin(i * 1.6) * u * 0.025; i ? g.lineTo(x, y) : g.moveTo(x, y); }
      g.stroke();
    } else if (m === 'o') { ell(g, cx, cy, u * 0.05, u * 0.06); g.fill(); g.stroke(); }
    else if (m === 'openSmall') { ell(g, cx, cy + u * 0.01, u * 0.085, u * 0.065); g.fill(); g.stroke(); }
    else if (m === 'open' || m === 'shout') {
      const rx = u * (m === 'shout' ? 0.16 : 0.11), ry = u * (m === 'shout' ? 0.14 : 0.12);
      ell(g, cx, cy + ry * 0.2, rx, ry); g.fill();
      g.save(); ell(g, cx, cy + ry * 0.2, rx, ry); g.clip();
      g.fillStyle = '#d65a62'; ell(g, cx, cy + ry * 1.0, rx * 0.7, ry * 0.5); g.fill();
      if (m === 'shout') { g.fillStyle = '#fbfbf6'; g.fillRect(cx - rx, cy - ry * 0.85, rx * 2, ry * 0.42); }
      g.restore(); ell(g, cx, cy + ry * 0.2, rx, ry); g.stroke();
    } else if (m === 'grin') {
      const rx = u * 0.2 * (def.mouthW || 1), ry = u * 0.085;
      g.fillStyle = '#fbfbf6';
      g.beginPath(); g.roundRect(cx - rx, cy - ry, rx * 2, ry * 2, ry * 0.9); g.fill();
      g.save(); g.beginPath(); g.roundRect(cx - rx, cy - ry, rx * 2, ry * 2, ry * 0.9); g.clip();
      if (e.goldTooth) { g.fillStyle = '#ffc21a'; g.fillRect(cx + rx * 0.2, cy - ry, rx * 0.36, ry); }
      g.lineWidth = lw * 0.45; g.beginPath(); g.moveTo(cx - rx, cy); g.lineTo(cx + rx, cy);
      for (let i = 1; i < 5; i++) { const x = cx - rx + (2 * rx * i) / 5; g.moveTo(x, cy - ry); g.lineTo(x, cy + ry); }
      g.stroke(); g.restore();
      g.lineWidth = lw * 0.8; g.beginPath(); g.roundRect(cx - rx, cy - ry, rx * 2, ry * 2, ry * 0.9); g.stroke();
    } else if (m === 'bigsmile') {
      const rx = u * 0.17, ry = u * 0.15;
      g.beginPath(); g.moveTo(cx - rx, cy - ry * 0.35); g.lineTo(cx + rx, cy - ry * 0.35);
      g.quadraticCurveTo(cx + rx, cy + ry * 1.1, cx, cy + ry * 1.1); g.quadraticCurveTo(cx - rx, cy + ry * 1.1, cx - rx, cy - ry * 0.35);
      g.closePath(); g.fill();
      g.save(); g.clip();
      g.fillStyle = '#fbfbf6'; g.fillRect(cx - rx, cy - ry * 0.4, rx * 2, ry * 0.42);
      g.fillStyle = '#d65a62'; ell(g, cx, cy + ry * 1.05, rx * 0.6, ry * 0.45); g.fill();
      g.restore();
      g.beginPath(); g.moveTo(cx - rx, cy - ry * 0.35); g.lineTo(cx + rx, cy - ry * 0.35);
      g.quadraticCurveTo(cx + rx, cy + ry * 1.1, cx, cy + ry * 1.1); g.quadraticCurveTo(cx - rx, cy + ry * 1.1, cx - rx, cy - ry * 0.35);
      g.closePath(); g.stroke();
    }
  }
  if (def.moustache) {
    const [cx, cy] = P(0, my + 0.1);
    g.fillStyle = def.hair || INK; g.strokeStyle = INK; g.lineWidth = lw * 0.4;
    for (const sd of [-1, 1]) {
      g.beginPath();
      g.moveTo(cx, cy - u * 0.02);
      if (def.moustache === 'curl') {
        g.bezierCurveTo(cx + sd * u * 0.12, cy - u * 0.08, cx + sd * u * 0.28, cy - u * 0.02, cx + sd * u * 0.3, cy - u * 0.12);
        g.bezierCurveTo(cx + sd * u * 0.33, cy + u * 0.06, cx + sd * u * 0.12, cy + u * 0.06, cx, cy + u * 0.03);
      } else {
        g.bezierCurveTo(cx + sd * u * 0.1, cy - u * 0.07, cx + sd * u * 0.22, cy - u * 0.03, cx + sd * u * 0.24, cy + u * 0.05);
        g.bezierCurveTo(cx + sd * u * 0.14, cy + u * 0.06, cx + sd * u * 0.06, cy + u * 0.03, cx, cy + u * 0.03);
      }
      g.fill(); g.stroke();
    }
  }
  // ---- extras
  if (e.blush || def.blush) {
    g.fillStyle = `rgba(232,96,110,${0.35 * (e.blush || def.blush)})`;
    for (const sd of [-1, 1]) { ell(g, ...P(sd * 0.45, -0.12), u * 0.11, u * 0.06); g.fill(); }
  }
  if (e.sweat) {
    const [cx, cy] = P(0.6, 0.42);
    g.fillStyle = '#8fd0ff'; g.strokeStyle = INK; g.lineWidth = lw * 0.45;
    g.beginPath(); g.moveTo(cx, cy - u * 0.14);
    g.quadraticCurveTo(cx + u * 0.09, cy, cx, cy + u * 0.06); g.quadraticCurveTo(cx - u * 0.09, cy, cx, cy - u * 0.14);
    g.fill(); g.stroke();
    g.fillStyle = 'rgba(255,255,255,0.9)'; ell(g, cx - u * 0.02, cy - u * 0.01, u * 0.015, u * 0.025); g.fill();
  }
  if (e.vein) {
    const [cx, cy] = P(0.45, 0.62);
    g.strokeStyle = '#d0242a'; g.lineWidth = lw * 0.8;
    for (const a of [0, Math.PI / 2, Math.PI, Math.PI * 1.5]) {
      g.beginPath(); g.arc(cx + Math.cos(a + 0.78) * u * 0.07, cy + Math.sin(a + 0.78) * u * 0.07, u * 0.045, a + 0.4, a + 2.3); g.stroke();
    }
  }
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  const v = { tex, canvas: c };
  cache.set(key, v);
  if (cache.size > MAX) { const k = cache.keys().next().value; cache.get(k).tex.dispose(); cache.delete(k); }
  return v;
}

// sphere with planar UVs on the front hemisphere (back maps to a plain skin corner)
export function headGeometry(r, seg = 40) {
  const g = new THREE.SphereGeometry(r, seg, Math.round(seg * 0.75));
  const pos = g.getAttribute('position'), uv = g.getAttribute('uv');
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i), y = pos.getY(i), z = pos.getZ(i);
    if (z > -0.05 * r) uv.setXY(i, 0.5 + x / (2 * r) * 0.98, 0.5 + y / (2 * r) * 0.98);
    else uv.setXY(i, 0.01, 0.99);
  }
  uv.needsUpdate = true;
  return g;
}
