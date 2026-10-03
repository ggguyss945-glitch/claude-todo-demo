// Low-poly character rig with painted clothing and faces.
import * as THREE from 'three';
import { canvas, toTex, noiseFill } from './tex.js';
import { paintFace, DEFAULT_FACE } from './faces.js';
import { lerp } from './util.js';

const matCache = new Map();
export function mat(color, opts = {}) {
  const key = color + JSON.stringify(opts);
  if (matCache.has(key)) return matCache.get(key);
  const m = new THREE.MeshStandardMaterial({ color, roughness: opts.rough ?? 0.75, metalness: opts.metal ?? 0.0,
    flatShading: opts.flat ?? true, ...(opts.extra || {}) });
  matCache.set(key, m);
  return m;
}

// flat-shaded cylinder with the front (+z) at u = 0.5
export function cyl(rt, rb, h, seg = 8, sz = 1.0, open = false) {
  const g = new THREE.CylinderGeometry(rt, rb, h, seg, 1, open, Math.PI, Math.PI * 2);
  g.scale(1, 1, sz);
  return g.toNonIndexed();
}

export function box(w, h, d) {
  return new THREE.BoxGeometry(w, h, d);
}

// --------------------------------------------------------------- outfits ---
function paintTorso(o) {
  const S = 512;
  const [c, g] = canvas(S, S);
  const F = S / 2; // front centre x
  const base = o.top;
  g.fillStyle = base;
  g.fillRect(0, 0, S, S);
  noiseFill(g, S, S, 0, 10, o.seed || 3, 2);
  // soft fold shading
  for (let i = 0; i < 6; i++) {
    const x = (i / 6) * S + 30;
    const grd = g.createLinearGradient(x - 30, 0, x + 30, 0);
    grd.addColorStop(0, 'rgba(0,0,0,0)'); grd.addColorStop(0.5, 'rgba(0,0,0,0.10)'); grd.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = grd;
    g.fillRect(x - 30, S * 0.3, 60, S * 0.7);
  }
  const vDepth = o.vDepth ?? 0.45;
  const vHalf = o.vHalf ?? 46;
  const drawV = (col) => {
    g.fillStyle = col;
    g.beginPath();
    g.moveTo(F - vHalf, 0);
    g.lineTo(F + vHalf, 0);
    g.lineTo(F, S * vDepth);
    g.closePath();
    g.fill();
  };
  if (o.kind === 'shirt') {
    // open collar with dark tee, button placket
    drawV(o.under || '#151515');
    g.strokeStyle = 'rgba(0,0,0,0.35)';
    g.lineWidth = 4;
    g.beginPath(); g.moveTo(F + 4, S * vDepth); g.lineTo(F + 4, S); g.stroke();
    g.fillStyle = '#e8e8f0';
    for (let y = S * (vDepth + 0.08); y < S; y += S * 0.13) { g.beginPath(); g.arc(F - 6, y, 5, 0, Math.PI * 2); g.fill(); }
    // collar flaps
    g.fillStyle = shadeHex(base, 0.12);
    g.beginPath(); g.moveTo(F - vHalf - 20, 0); g.lineTo(F - vHalf + 8, 0); g.lineTo(F - 12, S * 0.2); g.lineTo(F - vHalf - 30, S * 0.1); g.fill();
    g.beginPath(); g.moveTo(F + vHalf + 20, 0); g.lineTo(F + vHalf - 8, 0); g.lineTo(F + 12, S * 0.2); g.lineTo(F + vHalf + 30, S * 0.1); g.fill();
    // breast pocket
    g.strokeStyle = 'rgba(0,0,0,0.25)'; g.lineWidth = 3;
    g.strokeRect(F + 40, S * 0.3, 52, 56);
    // pin stripes
    g.strokeStyle = 'rgba(255,255,255,0.06)'; g.lineWidth = 2;
    for (let x = 0; x < S; x += 9) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, S); g.stroke(); }
  } else if (o.kind === 'vest') {
    // dealer: red vest all round, white shirt showing through a deep V at the front
    g.fillStyle = base;
    g.fillRect(0, 0, S, S);
    noiseFill(g, S, S, 0, 8, 7, 2);
    g.fillStyle = o.shirt || '#f2f0ea';
    g.beginPath(); g.moveTo(F - 78, 0); g.lineTo(F + 78, 0); g.lineTo(F, S * 0.62); g.closePath(); g.fill();
    g.strokeStyle = 'rgba(0,0,0,0.3)'; g.lineWidth = 5;
    g.beginPath(); g.moveTo(F - 80, 0); g.lineTo(F, S * 0.63); g.lineTo(F + 80, 0); g.stroke();
    g.fillStyle = 'rgba(0,0,0,0.25)'; // pocket welts
    g.fillRect(F - 120, S * 0.62, 60, 6); g.fillRect(F + 60, S * 0.62, 60, 6);
    g.strokeStyle = 'rgba(0,0,0,0.35)'; g.lineWidth = 4;
    g.beginPath(); g.moveTo(F, S * 0.62); g.lineTo(F, S); g.stroke();
    g.fillStyle = '#2a0806';
    for (let y = S * 0.68; y < S; y += S * 0.1) { g.beginPath(); g.arc(F - 10, y, 7, 0, Math.PI * 2); g.fill(); }
    g.fillStyle = 'rgba(255,255,255,0.10)';
    g.fillRect(F - 110, S * 0.3, 60, S * 0.7);
  } else if (o.kind === 'suit' || o.kind === 'tux') {
    drawV(o.shirt || '#f4f4f2');
    if (o.tie === 'stripe') {
      g.save();
      g.beginPath(); g.moveTo(F - 14, S * 0.06); g.lineTo(F + 14, S * 0.06); g.lineTo(F + 22, S * vDepth); g.lineTo(F, S * (vDepth + 0.05)); g.lineTo(F - 22, S * vDepth); g.closePath(); g.clip();
      g.fillStyle = '#16161c'; g.fillRect(F - 30, 0, 60, S);
      g.strokeStyle = '#f0f0f0'; g.lineWidth = 5;
      for (let y = -40; y < S; y += 22) { g.beginPath(); g.moveTo(F - 30, y); g.lineTo(F + 30, y + 30); g.stroke(); }
      g.strokeStyle = '#b0202a'; g.lineWidth = 3;
      for (let y = -29; y < S; y += 22) { g.beginPath(); g.moveTo(F - 30, y); g.lineTo(F + 30, y + 30); g.stroke(); }
      g.restore();
    } else if (o.tie === 'plain') {
      g.fillStyle = o.tieColor || '#1c2a6a';
      g.beginPath(); g.moveTo(F - 13, S * 0.06); g.lineTo(F + 13, S * 0.06); g.lineTo(F + 20, S * vDepth); g.lineTo(F, S * (vDepth + 0.05)); g.lineTo(F - 20, S * vDepth); g.closePath(); g.fill();
    }
    // lapels
    g.strokeStyle = 'rgba(255,255,255,0.12)'; g.lineWidth = 6;
    g.beginPath(); g.moveTo(F - vHalf - 18, 0); g.lineTo(F - 6, S * (vDepth + 0.02)); g.stroke();
    g.beginPath(); g.moveTo(F + vHalf + 18, 0); g.lineTo(F + 6, S * (vDepth + 0.02)); g.stroke();
    g.strokeStyle = 'rgba(0,0,0,0.45)'; g.lineWidth = 3;
    g.beginPath(); g.moveTo(F, S * vDepth); g.lineTo(F, S); g.stroke();
    g.fillStyle = o.buttons || '#d8d0b8';
    for (let k = 0; k < 2; k++) { g.beginPath(); g.arc(F - 8, S * (vDepth + 0.14 + k * 0.17), 7, 0, Math.PI * 2); g.fill(); }
    if (o.badge) {
      const bx = F + 92, by = S * 0.3;
      g.fillStyle = '#e8e8e0'; g.fillRect(bx - 4, by - 4, 52, 70);
      g.fillStyle = '#3a6ad0'; g.fillRect(bx, by, 44, 62);
      g.fillStyle = '#d8b040'; g.beginPath(); g.ellipse(bx + 22, by + 30, 12, 18, 0, 0, Math.PI * 2); g.fill();
      g.fillStyle = '#ffffff'; g.fillRect(bx + 4, by + 52, 36, 5);
    }
    if (o.pocketSquare) { g.fillStyle = '#ffffff'; g.fillRect(F + 80, S * 0.3, 40, 10); }
  } else if (o.kind === 'dress') {
    if (o.neck !== false) {
      g.fillStyle = o.skin;
      g.beginPath(); g.moveTo(F - 70, 0); g.lineTo(F + 70, 0); g.lineTo(F, S * 0.35); g.closePath(); g.fill();
    }
    g.fillStyle = 'rgba(255,255,255,0.08)';
    g.fillRect(F - 80, S * 0.25, 40, S);
  } else if (o.kind === 'tank') {
    g.fillStyle = o.skin;
    g.fillRect(0, 0, S, S * 0.2);
    g.fillRect(F - 230, 0, 70, S * 0.4);
    g.fillRect(F + 160, 0, 70, S * 0.4);
    g.beginPath(); g.moveTo(F - 70, 0); g.lineTo(F + 70, 0); g.lineTo(F, S * 0.3); g.closePath(); g.fill();
    // gold chain with $ pendant
    g.strokeStyle = '#e8c860'; g.lineWidth = 7;
    g.beginPath(); g.moveTo(F - 75, 0); g.quadraticCurveTo(F, S * 0.5, F + 75, 0); g.stroke();
    g.fillStyle = '#f0d070'; g.font = 'bold 70px "Liberation Sans"'; g.textAlign = 'center'; g.fillText('$', F, S * 0.36 + 50);
  } else if (o.kind === 'zigzag') {
    g.strokeStyle = '#f2f2f2'; g.lineWidth = 9;
    for (let y = 30; y < S; y += 46) {
      g.beginPath();
      for (let x = 0; x <= S; x += 28) g.lineTo(x, y + ((x / 28) % 2 ? 14 : -14));
      g.stroke();
    }
    g.fillStyle = o.skin;
    g.beginPath(); g.moveTo(F - 60, 0); g.lineTo(F + 60, 0); g.lineTo(F, S * 0.18); g.closePath(); g.fill();
  } else if (o.kind === 'hoodie' || o.kind === 'tee') {
    g.fillStyle = 'rgba(0,0,0,0.25)';
    g.beginPath(); g.ellipse(F, 0, 60, 34, 0, 0, Math.PI); g.fill();
    if (o.print) { g.fillStyle = o.print; g.fillRect(F - 50, S * 0.4, 100, 70); }
  } else if (o.kind === 'jacket') {
    drawV(o.shirt || '#d8d0c0');
    g.strokeStyle = 'rgba(0,0,0,0.4)'; g.lineWidth = 3;
    g.beginPath(); g.moveTo(F, S * vDepth); g.lineTo(F, S); g.stroke();
  }
  return toTex(c);
}

function shadeHex(h, k) {
  h = h.replace('#', '');
  const v = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
  const f = (x) => Math.max(0, Math.min(255, Math.round(k >= 0 ? x + (255 - x) * k : x * (1 + k))));
  return '#' + v.map((x) => f(x).toString(16).padStart(2, '0')).join('');
}

// ------------------------------------------------------------------- head ---
function headGeometry(w = 0.2, h = 0.25, d = 0.23) {
  // octagonal prism, slightly narrower at the jaw, flat face towards +z
  const g = new THREE.CylinderGeometry(0.5, 0.42, 1, 8, 2, false, Math.PI / 8, Math.PI * 2);
  const pos = g.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    let x = pos.getX(i), y = pos.getY(i), z = pos.getZ(i);
    // pull the crown in a little and taper the jaw
    const k = y > 0.4 ? 0.82 : y < -0.4 ? 0.9 : 1.0;
    pos.setXYZ(i, x * w * k, y * h, z * d * k);
  }
  const ng = g.toNonIndexed();
  ng.computeVertexNormals();
  // planar UVs from the front + material groups by facing
  const p = ng.attributes.position;
  const uv = new Float32Array(p.count * 2);
  ng.clearGroups();
  const tri = p.count / 3;
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3(), n = new THREE.Vector3();
  let groupStart = 0, curMat = -1;
  const mats = [];
  for (let t = 0; t < tri; t++) {
    a.fromBufferAttribute(p, t * 3); b.fromBufferAttribute(p, t * 3 + 1); c.fromBufferAttribute(p, t * 3 + 2);
    n.subVectors(c, b).cross(new THREE.Vector3().subVectors(a, b)).normalize();
    const m = n.z > 0.3 ? 0 : (n.z > -0.2 && n.y < 0.6 ? 1 : 2); // 0 face, 1 side (skin), 2 back/top (hair)
    mats.push(m);
    for (let k = 0; k < 3; k++) {
      const x = p.getX(t * 3 + k), y = p.getY(t * 3 + k);
      uv[(t * 3 + k) * 2] = 0.5 + x / (w * 1.08);
      uv[(t * 3 + k) * 2 + 1] = 0.5 + y / h;
    }
  }
  ng.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  // reorder triangles by material so groups are contiguous
  const order = [...Array(tri).keys()].sort((x, y) => mats[x] - mats[y]);
  const np = new Float32Array(p.count * 3), nuv = new Float32Array(p.count * 2);
  order.forEach((ti, j) => {
    for (let k = 0; k < 3; k++) {
      for (let q = 0; q < 3; q++) np[(j * 3 + k) * 3 + q] = p.array[(ti * 3 + k) * 3 + q];
      for (let q = 0; q < 2; q++) nuv[(j * 3 + k) * 2 + q] = uv[(ti * 3 + k) * 2 + q];
    }
  });
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.BufferAttribute(np, 3));
  out.setAttribute('uv', new THREE.BufferAttribute(nuv, 2));
  out.computeVertexNormals();
  const sorted = order.map((i) => mats[i]);
  for (let m = 0; m < 3; m++) {
    const first = sorted.indexOf(m), last = sorted.lastIndexOf(m);
    if (first >= 0) out.addGroup(first * 3, (last - first + 1) * 3, m);
  }
  return out;
}

let _blobMat = null;
function blobMat() {
  if (_blobMat) return _blobMat;
  const [c, g] = canvas(128, 128);
  const grd = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  grd.addColorStop(0, 'rgba(0,0,0,0.75)'); grd.addColorStop(0.5, 'rgba(0,0,0,0.35)'); grd.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = grd; g.fillRect(0, 0, 128, 128);
  _blobMat = new THREE.MeshBasicMaterial({ map: toTex(c, { srgb: false }), transparent: true, depthWrite: false, opacity: 0.55 });
  return _blobMat;
}

function hairTexture(col, seed = 1) {
  const [c, g] = canvas(256, 256);
  g.fillStyle = col;
  g.fillRect(0, 0, 256, 256);
  let r = seed * 9301 + 49297;
  const rnd = () => { r = (r * 9301 + 49297) % 233280; return r / 233280; };
  for (let i = 0; i < 1400; i++) {
    const x = rnd() * 256, y = rnd() * 256;
    g.strokeStyle = rnd() < 0.55 ? 'rgba(0,0,0,0.22)' : 'rgba(255,255,255,0.12)';
    g.lineWidth = 1 + rnd() * 1.5;
    g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x + 6, y + 10, x + (rnd() - 0.5) * 10, y + 22); g.stroke();
  }
  return toTex(c);
}

function sideTexture(skin, hair, hairLine) {
  const [c, g] = canvas(64, 256);
  g.fillStyle = skin;
  g.fillRect(0, 0, 64, 256);
  if (hair) {
    g.fillStyle = hair;
    g.fillRect(0, 0, 64, 256 * hairLine);
  }
  noiseFill(g, 64, 256, 0, 10, 4, 1);
  return toTex(c);
}

// ------------------------------------------------------------- character ---
export const OUTFITS = {
  player: { kind: 'shirt', top: '#6f6fd6', sleeve: '#6f6fd6', pants: '#2c3e66', shoes: '#2a1a10', under: '#121212' },
  dealer: { kind: 'vest', top: '#d82418', sleeve: '#f2f0ea', pants: '#151515', shoes: '#0c0c0c', bowtie: '#e01a10' },
  guard: { kind: 'suit', top: '#141a2c', sleeve: '#141a2c', pants: '#10131c', shoes: '#0a0a0a', tie: 'stripe', badge: true },
  pit: { kind: 'tux', top: '#0e0e10', sleeve: '#0e0e10', pants: '#0e0e10', shoes: '#050505', bowtie: '#0a0a0a' },
  manager: { kind: 'suit', top: '#16161c', sleeve: '#16161c', pants: '#16161c', shoes: '#0a0a0a', tie: 'plain', tieColor: '#1c2a6a' },
  operator: { kind: 'suit', top: '#1c1c22', sleeve: '#1c1c22', pants: '#1a1a20', shoes: '#0a0a0a', tie: 'none' },
};

export function makeCharacter(o) {
  const out = { ...o };
  const skin = o.face?.skin || DEFAULT_FACE.skin;
  const outfit = { ...(OUTFITS[o.outfit] || {}), ...(o.clothes || {}), skin };
  const s = o.scale || 1;
  const bw = o.build || 1; // width factor
  const root = new THREE.Group();
  root.name = o.name || 'char';
  const J = {};
  const add = (parent, name, x, y, z) => { const gg = new THREE.Group(); gg.position.set(x, y, z); parent.add(gg); J[name] = gg; return gg; };
  const torsoTex = paintTorso({ ...outfit, seed: o.seed || 3 });
  const torsoMat = new THREE.MeshStandardMaterial({ map: torsoTex, roughness: 0.8, flatShading: true });
  const sleeveMat = mat(outfit.sleeve || outfit.top, { rough: 0.8 });
  const pantsMat = mat(outfit.pants || '#222', { rough: 0.85 });
  const shoeMat = mat(outfit.shoes || '#111', { rough: 0.4 });
  const skinMat = mat(skin, { rough: 0.7 });
  const handMat = mat(o.handColor || skin, { rough: 0.7 });

  const hips = add(root, 'hips', 0, 0.95 * s, 0);
  // pelvis
  const pelvis = new THREE.Mesh(cyl(0.165 * bw * s, 0.17 * bw * s, 0.2 * s, 8, 0.62), o.dress ? mat(o.dress, { rough: 0.8 }) : pantsMat);
  pelvis.position.y = -0.08 * s;
  hips.add(pelvis);
  const spine = add(hips, 'spine', 0, 0.0, 0);
  const torso = new THREE.Mesh(cyl(0.215 * bw * s, 0.165 * bw * s, 0.52 * s, 8, 0.6), torsoMat);
  torso.position.y = 0.26 * s;
  spine.add(torso);
  if (o.female) {
    const bust = new THREE.Mesh(cyl(0.15 * s, 0.16 * s, 0.12 * s, 8, 0.6), torsoMat);
    bust.position.set(0, 0.32 * s, 0.045 * s);
    spine.add(bust);
  }
  const neck = add(spine, 'neck', 0, 0.52 * s, 0);
  const neckMesh = new THREE.Mesh(cyl(0.05 * s, 0.058 * s, 0.11 * s, 6, 1), skinMat);
  neckMesh.position.y = 0.05 * s;
  neck.add(neckMesh);
  if (outfit.kind === 'suit' || outfit.kind === 'tux' || outfit.kind === 'vest' || outfit.kind === 'shirt') {
    const collar = new THREE.Mesh(cyl(0.064 * s, 0.07 * s, 0.05 * s, 8, 1, true), mat(outfit.kind === 'shirt' ? outfit.top : '#f4f4f2', { rough: 0.8, extra: { side: THREE.DoubleSide } }));
    collar.position.y = 0.025 * s;
    neck.add(collar);
  }
  const head = add(neck, 'head', 0, 0.12 * s, 0);
  const faceP = { ...DEFAULT_FACE, ...(o.face || {}) };
  const { tex: faceTex, canvas: faceCanvas } = paintFace(faceP);
  out.faceCanvas = faceCanvas;
  const hw = 0.228 * s * (o.headW || 1), hh = 0.27 * s * (o.headH || 1), hd = 0.245 * s;
  const hairCol = faceP.hairStyle === 'bald' ? null : faceP.hair;
  const headMats = [
    new THREE.MeshStandardMaterial({ map: faceTex, roughness: 0.65, flatShading: true }),
    new THREE.MeshStandardMaterial({ map: sideTexture(skin, hairCol, 0.3), roughness: 0.7, flatShading: true }),
    new THREE.MeshStandardMaterial({ map: sideTexture(hairCol ? shadeHex(skin, -0.1) : skin, hairCol, faceP.hairStyle === 'long' ? 1.0 : 0.62), roughness: 0.7, flatShading: true }),
  ];
  const headMesh = new THREE.Mesh(headGeometry(hw, hh, hd), headMats);
  headMesh.position.y = hh / 2;
  head.add(headMesh);
  out.headMesh = headMesh;
  for (const side of [-1, 1]) {
    const ear = new THREE.Mesh(box(0.022 * s, 0.062 * s, 0.046 * s), skinMat);
    ear.position.set(side * hw * 0.51, hh * 0.47, -0.012 * s);
    ear.rotation.y = side * 0.25;
    head.add(ear);
    const lobe = new THREE.Mesh(box(0.016 * s, 0.024 * s, 0.022 * s), skinMat);
    lobe.position.set(side * hw * 0.5, hh * 0.38, -0.0 * s);
    head.add(lobe);
  }
  // hair volume: a slightly oversized cap that follows the head silhouette
  if (faceP.hairStyle !== 'bald') {
    const hairMat = new THREE.MeshStandardMaterial({ map: hairTexture(faceP.hair, faceP.seed), roughness: 0.75, flatShading: true });
    const style = faceP.hairStyle;
    const capH = { buzz: 0.16, short: 0.3, slick: 0.24, bun: 0.28, long: 0.34, curly: 0.38 }[style] || 0.28;
    const g = new THREE.CylinderGeometry(0.5 * 0.86, 0.5, 1, 8, 1, false, Math.PI / 8, Math.PI * 2);
    g.scale(hw * 1.07, hh * capH, hd * 1.08);
    const cap = new THREE.Mesh(g, hairMat);
    cap.position.set(0, hh * (1.0 - capH / 2) + 0.004 * s, -0.004 * s);
    head.add(cap);
    // fringe edge sits just above the brow line at the front
    const fr = new THREE.Mesh(box(hw * 0.86, hh * 0.05, hd * 0.12), hairMat);
    fr.position.set(0, hh * (0.86 - (style === 'buzz' ? 0.0 : 0.02)), hd * 0.47);
    if (style !== 'slick') head.add(fr);
    if (style === 'long' || faceP.female) {
      const back = new THREE.Mesh(box(hw * 1.06, hh * 0.95, hd * 0.25), hairMat);
      back.position.set(0, hh * 0.45, -hd * 0.45);
      head.add(back);
      for (const sd of [-1, 1]) {
        const side = new THREE.Mesh(box(hw * 0.12, hh * 0.75, hd * 0.75), hairMat);
        side.position.set(sd * hw * 0.53, hh * 0.52, -hd * 0.08);
        head.add(side);
      }
    } else {
      const nape = new THREE.Mesh(box(hw * 0.96, hh * 0.42, hd * 0.12), hairMat);
      nape.position.set(0, hh * 0.62, -hd * 0.48);
      head.add(nape);
    }
  }
  // blink: second face texture with closed lids
  out.faceOpen = faceTex;
  out.faceClosed = paintFace({ ...faceP, eyeOpen: 0.08 }).tex;
  out.blinkSeed = (o.seed || 1) * 1.37;
  if (faceP.hairStyle === 'bun') {
    const bun = new THREE.Mesh(new THREE.SphereGeometry(0.06 * s, 6, 5), mat(faceP.hair));
    bun.position.set(0, hh * 0.95, -0.07 * s);
    head.add(bun);
  }
  if (faceP.hairStyle === 'curly') {
    for (let i = 0; i < 9; i++) {
      const puff = new THREE.Mesh(new THREE.IcosahedronGeometry(0.055 * s, 0), mat(faceP.hair, { rough: 0.9 }));
      const a = (i / 9) * Math.PI * 2;
      puff.position.set(Math.cos(a) * 0.08 * s, hh * 0.92 + Math.sin(i * 1.7) * 0.02 * s, Math.sin(a) * 0.08 * s - 0.01 * s);
      head.add(puff);
    }
  }
  if (o.hat === 'top') {
    const hat = new THREE.Group();
    const brim = new THREE.Mesh(cyl(0.16 * s, 0.16 * s, 0.015 * s, 12, 1), mat('#1a1410', { rough: 0.6 }));
    const crown = new THREE.Mesh(cyl(0.105 * s, 0.11 * s, 0.2 * s, 12, 1), mat('#1a1410', { rough: 0.6 }));
    crown.position.y = 0.1 * s;
    const band = new THREE.Mesh(cyl(0.112 * s, 0.112 * s, 0.03 * s, 12, 1), mat('#4a3020', { rough: 0.6 }));
    band.position.y = 0.025 * s;
    hat.add(brim, crown, band);
    hat.position.y = hh * 0.92;
    head.add(hat);
  }
  if (o.glasses) {
    const gl = makeGlasses(o.glasses, s * (o.headW || 1));
    gl.position.set(0, hh * 0.56, hd * 0.5 + 0.004 * s);
    head.add(gl);
    out.glasses = gl;
  }
  if (outfit.bowtie) {
    const bow = new THREE.Group();
    for (const side of [-1, 1]) {
      const wing = new THREE.Mesh(new THREE.ConeGeometry(0.032 * s, 0.06 * s, 4), mat(outfit.bowtie, { rough: 0.5 }));
      wing.rotation.z = side * Math.PI / 2;
      wing.position.x = side * 0.03 * s;
      bow.add(wing);
    }
    const knot = new THREE.Mesh(box(0.022 * s, 0.026 * s, 0.02 * s), mat(outfit.bowtie, { rough: 0.5 }));
    bow.add(knot);
    bow.position.set(0, 0.49 * s, 0.135 * s * bw);
    spine.add(bow);
  }
  // arms
  for (const [side, L] of [[1, 'l'], [-1, 'r']]) {
    const sh = add(spine, L + 'Shoulder', side * 0.215 * bw * s, 0.47 * s, 0);
    const upper = new THREE.Mesh(cyl(0.062 * s, 0.054 * s, 0.31 * s, 7, 1), sleeveMat);
    upper.position.y = -0.155 * s;
    sh.add(upper);
    const shoulderCap = new THREE.Mesh(new THREE.IcosahedronGeometry(0.068 * s, 0), sleeveMat);
    sh.add(shoulderCap);
    const el = add(sh, L + 'Elbow', 0, -0.31 * s, 0);
    const fore = new THREE.Mesh(cyl(0.052 * s, 0.044 * s, 0.27 * s, 7, 1), o.bareArms ? skinMat : sleeveMat);
    fore.position.y = -0.135 * s;
    el.add(fore);
    const wr = add(el, L + 'Wrist', 0, -0.27 * s, 0);
    buildHand(wr, side, s, handMat, J, L);
    if (o.cuffs) {
      const cuff = new THREE.Mesh(cyl(0.046 * s, 0.046 * s, 0.03 * s, 7, 1), mat('#f4f4f2'));
      cuff.position.y = -0.005 * s;
      wr.add(cuff);
    }
  }
  // legs
  for (const [side, L] of [[1, 'l'], [-1, 'r']]) {
    const hp = add(hips, L + 'Hip', side * 0.09 * bw * s, -0.08 * s, 0);
    const thigh = new THREE.Mesh(cyl(0.085 * s, 0.065 * s, 0.44 * s, 7, 1), o.dress && o.skirtLong ? mat(o.dress) : (o.dress ? skinMat : pantsMat));
    thigh.position.y = -0.22 * s;
    hp.add(thigh);
    const kn = add(hp, L + 'Knee', 0, -0.44 * s, 0);
    const shin = new THREE.Mesh(cyl(0.062 * s, 0.05 * s, 0.43 * s, 7, 1), o.dress && !o.skirtLong ? skinMat : pantsMat);
    shin.position.y = -0.215 * s;
    kn.add(shin);
    const an = add(kn, L + 'Ankle', 0, -0.43 * s, 0);
    const foot = new THREE.Mesh(box(0.09 * s, 0.07 * s, 0.24 * s), shoeMat);
    foot.position.set(0, -0.03 * s, 0.06 * s);
    an.add(foot);
  }
  if (o.dress) {
    const skirt = new THREE.Mesh(cyl(0.18 * s, o.skirtLong ? 0.3 * s : 0.24 * s, (o.skirtLong ? 0.75 : 0.38) * s, 9, 0.75, true),
      mat(o.dress, { rough: 0.8, extra: { side: THREE.DoubleSide } }));
    skirt.position.y = -(o.skirtLong ? 0.36 : 0.18) * s - 0.04 * s;
    hips.add(skirt);
  }
  // shoes: sole + heel; belt on trousers
  for (const L of ['l', 'r']) {
    const an = J[L + 'Ankle'];
    const sole = new THREE.Mesh(box(0.098 * s, 0.018 * s, 0.25 * s), mat('#0a0806', { rough: 0.6 }));
    sole.position.set(0, -0.07 * s, 0.062 * s);
    an.add(sole);
    const toe = new THREE.Mesh(box(0.085 * s, 0.05 * s, 0.05 * s), shoeMat);
    toe.position.set(0, -0.045 * s, 0.17 * s);
    an.add(toe);
  }
  if (!o.dress) {
    const belt = new THREE.Mesh(cyl(0.172 * bw * s, 0.172 * bw * s, 0.035 * s, 8, 0.63), mat('#16100c', { rough: 0.45 }));
    belt.position.y = 0.0;
    hips.add(belt);
    const buckle = new THREE.Mesh(box(0.035 * s, 0.026 * s, 0.01 * s), new THREE.MeshStandardMaterial({ color: '#c8a858', metalness: 0.9, roughness: 0.3 }));
    buckle.position.set(0, 0, 0.172 * bw * s * 0.63 + 0.003 * s);
    hips.add(buckle);
  }
  // jacket lapels and buttons as real geometry (catch the light)
  if (outfit.kind === 'suit' || outfit.kind === 'tux' || outfit.kind === 'jacket') {
    const lapMat = mat(outfit.top, { rough: 0.55 });
    for (const sd of [-1, 1]) {
      const lap = new THREE.Mesh(box(0.05 * s, 0.24 * s, 0.012 * s), lapMat);
      lap.position.set(sd * 0.06 * s * bw, 0.4 * s, 0.128 * s * bw);
      lap.rotation.set(-0.1, sd * 0.25, sd * 0.38);
      spine.add(lap);
    }
    const btnMat = new THREE.MeshStandardMaterial({ color: outfit.buttons || '#d8d0b8', metalness: 0.5, roughness: 0.35 });
    for (let k = 0; k < 2; k++) {
      const b = new THREE.Mesh(cyl(0.009 * s, 0.009 * s, 0.006 * s, 8), btnMat);
      b.rotation.x = Math.PI / 2;
      b.position.set(-0.004 * s, (0.17 - k * 0.085) * s, 0.112 * s * bw);
      spine.add(b);
    }
  }
  root.traverse((m) => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } });
  // soft contact shadow on the floor (ambient occlusion stand-in)
  const blob = new THREE.Mesh(new THREE.PlaneGeometry(0.9 * s, 0.9 * s), blobMat());
  blob.rotation.x = -Math.PI / 2;
  blob.position.y = 0.006;
  blob.renderOrder = 1;
  root.add(blob);
  out.root = root;
  // idle: breathing, blinking, tiny weight shifts (added on top of the pose)
  out.idle = (t) => {
    const ph = out.blinkSeed;
    const br = Math.sin(t * 1.7 + ph * 5);
    J.spine.rotation.x += br * 0.012;
    J.neck.rotation.x -= br * 0.008;
    J.neck.rotation.y += Math.sin(t * 0.37 + ph) * 0.025;
    J.lShoulder.rotation.z += br * 0.01;
    J.rShoulder.rotation.z -= br * 0.01;
    const cyc = (t + ph * 3.1) % 3.7;
    const closed = cyc < 0.11;
    const m = headMesh.material[0];
    const want = closed ? out.faceClosed : out.faceOpen;
    if (m.map !== want) { m.map = want; m.needsUpdate = true; }
  };
  out.J = J;
  out.setPose = (pose) => applyPose(out, pose);
  out.setPose(POSES.stand);
  return out;
}

// Blocky hand: palm, four two-segment fingers and a thumb; curl via pose.lGrip/rGrip.
function buildHand(wr, side, s, m, J, L) {
  const palm = new THREE.Mesh(box(0.078 * s, 0.075 * s, 0.032 * s), m);
  palm.position.y = -0.04 * s;
  wr.add(palm);
  const fingers = [];
  for (let i = 0; i < 4; i++) {
    const fx = (i - 1.5) * 0.019 * s * -side;
    const len = [0.036, 0.042, 0.04, 0.032][i] * s;
    const k1 = new THREE.Group();
    k1.position.set(fx, -0.078 * s, 0);
    wr.add(k1);
    const p1 = new THREE.Mesh(box(0.017 * s, len, 0.022 * s), m);
    p1.position.y = -len / 2;
    k1.add(p1);
    const k2 = new THREE.Group();
    k2.position.y = -len;
    k1.add(k2);
    const p2 = new THREE.Mesh(box(0.016 * s, len * 0.8, 0.02 * s), m);
    p2.position.y = -len * 0.4;
    k2.add(p2);
    fingers.push([k1, k2]);
  }
  const t1 = new THREE.Group();
  t1.position.set(side * 0.038 * s, -0.022 * s, 0.012 * s);
  t1.rotation.z = side * 0.55;
  wr.add(t1);
  const tm = new THREE.Mesh(box(0.02 * s, 0.05 * s, 0.022 * s), m);
  tm.position.y = -0.025 * s;
  t1.add(tm);
  J[L + 'Fingers'] = { fingers, thumb: t1, side };
}

function curlHand(h, grip, spread = 0) {
  if (!h) return;
  h.fingers.forEach(([k1, k2], i) => {
    k1.rotation.set(-grip * 1.35, 0, (i - 1.5) * spread * 0.08);
    k2.rotation.set(-grip * 1.5, 0, 0);
  });
  h.thumb.rotation.set(-grip * 0.6, 0, h.side * (0.55 - grip * 0.3));
}

export function makeGlasses(kind, s = 1) {
  const g = new THREE.Group();
  if (kind === 'pink') {
    const frame = mat('#e0329a', { rough: 0.35, extra: { emissive: new THREE.Color('#40081c') } });
    const lens = new THREE.MeshStandardMaterial({ color: '#e8eef0', roughness: 0.15, transparent: true, opacity: 0.55 });
    for (const side of [-1, 1]) {
      const x = side * 0.052 * s;
      const fw = 0.085 * s, fh = 0.062 * s, t = 0.012 * s;
      const parts = [[fw, t, 0, fh / 2], [fw, t, 0, -fh / 2], [t, fh, -fw / 2, 0], [t, fh, fw / 2, 0]];
      for (const [w, h, ox, oy] of parts) {
        const m = new THREE.Mesh(box(w, h, 0.012 * s), frame);
        m.position.set(x + ox, oy, 0);
        g.add(m);
      }
      const l = new THREE.Mesh(box(fw - t, fh - t, 0.004 * s), lens);
      l.position.set(x, 0, -0.002 * s);
      g.add(l);
      const arm = new THREE.Mesh(box(0.01 * s, 0.012 * s, 0.2 * s), frame);
      arm.position.set(side * 0.1 * s, fh * 0.35, -0.1 * s);
      g.add(arm);
    }
    const bridge = new THREE.Mesh(box(0.025 * s, 0.01 * s, 0.01 * s), frame);
    bridge.position.y = 0.012 * s;
    g.add(bridge);
  } else if (kind === 'sun') {
    const m = new THREE.MeshStandardMaterial({ color: '#050505', roughness: 0.08, metalness: 0.6 });
    for (const side of [-1, 1]) {
      const l = new THREE.Mesh(box(0.082 * s, 0.045 * s, 0.012 * s), m);
      l.position.set(side * 0.05 * s, 0, 0);
      l.rotation.z = side * -0.08;
      g.add(l);
      const arm = new THREE.Mesh(box(0.008 * s, 0.01 * s, 0.18 * s), m);
      arm.position.set(side * 0.098 * s, 0.01 * s, -0.09 * s);
      g.add(arm);
    }
    const bridge = new THREE.Mesh(box(0.03 * s, 0.01 * s, 0.01 * s), m);
    bridge.position.y = 0.012 * s;
    g.add(bridge);
  } else if (kind === 'reading') {
    const m = new THREE.MeshStandardMaterial({ color: '#3a2a18', roughness: 0.4, metalness: 0.3 });
    for (const side of [-1, 1]) {
      const ring = new THREE.Mesh(new THREE.TorusGeometry(0.026 * s, 0.003 * s, 4, 12), m);
      ring.scale.set(1.35, 0.8, 1);
      ring.position.set(side * 0.048 * s, 0, 0);
      g.add(ring);
    }
  }
  return g;
}

// ------------------------------------------------------------------ poses ---
// joint -> [x,y,z] euler (radians). Arms hang down by default; -x swings forward.
export const POSES = {
  stand: { lShoulder: [0, 0, 0.08], rShoulder: [0, 0, -0.08], lElbow: [-0.15, 0, 0], rElbow: [-0.15, 0, 0] },
  sit: {
    hipsY: 0.52, lHip: [-1.5, 0, 0.05], rHip: [-1.5, 0, -0.05], lKnee: [1.45, 0, 0], rKnee: [1.45, 0, 0],
    lShoulder: [-0.5, 0, 0.1], rShoulder: [-0.5, 0, -0.1], lElbow: [-1.0, 0, 0], rElbow: [-1.0, 0, 0],
  },
  sitTable: {
    hipsY: 0.52, spine: [0.18, 0, 0], neck: [-0.1, 0, 0], lHip: [-1.5, 0, 0.05], rHip: [-1.5, 0, -0.05], lKnee: [1.45, 0, 0], rKnee: [1.45, 0, 0],
    lShoulder: [-0.75, 0, 0.2], rShoulder: [-0.75, 0, -0.2], lElbow: [-0.95, 0, 0.0], rElbow: [-0.95, 0, 0.0], lWrist: [0.2, 0, 0], rWrist: [0.2, 0, 0],
  },
  dealer: {
    spine: [0.12, 0, 0], neck: [-0.08, 0, 0], lShoulder: [-0.35, 0, 0.25], rShoulder: [-0.35, 0, -0.25],
    lElbow: [-1.05, 0, 0], rElbow: [-1.05, 0, 0], lWrist: [0.3, 0, 0], rWrist: [0.3, 0, 0],
  },
  handsBack: { lShoulder: [0.25, 0, 0.12], rShoulder: [0.25, 0, -0.12], lElbow: [-0.5, 0, 0.6], rElbow: [-0.5, 0, -0.6] },
  armsCrossed: { lShoulder: [-0.4, 0, 0.18], rShoulder: [-0.4, 0, -0.18], lElbow: [-1.7, 0.9, 0], rElbow: [-1.7, -0.9, 0] },
  walkie: { lShoulder: [0, 0, 0.1], lElbow: [-0.15, 0, 0], rShoulder: [-0.6, 0, -0.55], rElbow: [-2.3, 0, 0.3], rWrist: [0, 0, 0] },
  phone: { lShoulder: [-0.9, 0, 0.6], lElbow: [-2.3, 0, -0.2], rShoulder: [-1.0, 0, -0.55], rElbow: [-2.2, 0, 0.35] },
  handOnHip: { lShoulder: [0.1, 0, 0.45], lElbow: [-0.3, 0, 1.2], rShoulder: [0, 0, -0.1], rElbow: [-0.2, 0, 0] },
  leanIn: {
    hipsY: 0.95, spine: [0.55, 0, 0], neck: [-0.4, 0, 0], lShoulder: [-1.2, 0, 0.15], rShoulder: [-1.2, 0, -0.15],
    lElbow: [-0.3, 0, 0], rElbow: [-0.3, 0, 0],
  },
  typing: {
    hipsY: 0.52, spine: [0.1, 0, 0], lHip: [-1.5, 0, 0.05], rHip: [-1.5, 0, -0.05], lKnee: [1.45, 0, 0], rKnee: [1.45, 0, 0],
    lShoulder: [-0.7, 0, 0.15], rShoulder: [-0.7, 0, -0.15], lElbow: [-0.9, 0, 0], rElbow: [-0.9, 0, 0],
  },
};

export function blendPose(a, b, t) {
  const out = {};
  const keysAll = new Set([...Object.keys(a), ...Object.keys(b)]);
  for (const k of keysAll) {
    const dflt = k === 'hipsY' ? 0.95 : k.endsWith('Grip') ? 0.25 : k.endsWith('Spread') ? 0 : [0, 0, 0];
    const va = a[k] ?? dflt;
    const vb = b[k] ?? dflt;
    out[k] = Array.isArray(va) ? va.map((v, i) => lerp(v, vb[i], t)) : lerp(va, vb, t);
  }
  return out;
}

function applyPose(ch, pose) {
  const J = ch.J;
  for (const k in J) if (k !== 'hips' && J[k].rotation) J[k].rotation.set(0, 0, 0);
  curlHand(J.lFingers, pose.lGrip ?? 0.25, pose.lSpread ?? 0);
  curlHand(J.rFingers, pose.rGrip ?? 0.25, pose.rSpread ?? 0);
  J.hips.rotation.set(0, 0, 0);
  const s = ch.scale || 1;
  J.hips.position.y = (pose.hipsY ?? 0.95) * s;
  for (const k in pose) {
    if (k === 'hipsY' || k.endsWith('Grip') || k.endsWith('Spread')) continue;
    if (k === 'hipsRot') { J.hips.rotation.set(...pose[k]); continue; }
    if (J[k]) J[k].rotation.set(...pose[k]);
  }
}

// walking cycle (phase in cycles)
export function walkPose(phase, base = POSES.stand) {
  const a = Math.sin(phase * Math.PI * 2);
  const b = Math.sin(phase * Math.PI * 2 + Math.PI);
  return {
    ...base,
    lHip: [a * 0.45, 0, 0.03], rHip: [b * 0.45, 0, -0.03],
    lKnee: [Math.max(0, -a) * 0.8 + 0.1, 0, 0], rKnee: [Math.max(0, -b) * 0.8 + 0.1, 0, 0],
    lShoulder: [b * 0.35, 0, 0.08], rShoulder: [a * 0.35, 0, -0.08],
    lElbow: [-0.3, 0, 0], rElbow: [-0.3, 0, 0],
    hipsY: 0.95 + Math.abs(Math.cos(phase * Math.PI * 2)) * 0.02,
  };
}
