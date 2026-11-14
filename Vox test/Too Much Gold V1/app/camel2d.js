// The camel as a flat drawing too: the 3D camel rig keeps animating (walk, neck, head, sitting),
// its meshes are hidden, and each frame its projected points are drawn on a camera-facing card
// with the same uneven ink lines as the people.
import * as THREE from 'three';
import { CH2D, CARDS, CHAR_LAYER } from './chars2d.js';

const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const INK = '#1b1215';
export const CAMELS = [];
const _inv = new THREE.Matrix4(), _m = new THREE.Matrix4();

export function toCard(cm) {
  cm.root.traverse((o) => { if (o.isMesh) o.visible = false; });
  const canvas = document.createElement('canvas'); canvas.width = canvas.height = 64;
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace; tex.generateMipmaps = false; tex.minFilter = THREE.LinearFilter;
  const card = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: tex, transparent: true, toneMapped: false, alphaTest: 0.03, fog: true }));
  card.layers.set(CHAR_LAYER); card.frustumCulled = false; card.matrixAutoUpdate = false; card.castShadow = true;
  card.customDepthMaterial = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: tex, alphaTest: 0.5 });
  card.userData.ndMat = new THREE.ShaderMaterial({
    uniforms: { map: { value: tex } },
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
    fragmentShader: 'uniform sampler2D map; varying vec2 vUv; void main(){ if (texture2D(map, vUv).a < 0.5) discard; gl_FragColor = vec4(0.5, 0.5, 1.0, 1.0); }',
  });
  cm.root.add(card);
  Object.assign(cm, { card, canvas, g: canvas.getContext('2d'), tex });
  CARDS.push(card); CAMELS.push(cm);
}

const shownInWorld = (o) => { for (let p = o; p; p = p.parent) if (!p.visible) return false; return true; };
export function drawCamels() { for (const cm of CAMELS) if (shownInWorld(cm.root)) drawCamel(cm); }

// convex hull (monotone chain) of 2D points
function hull(pts) {
  const p = pts.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cr = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lo = [], up = [];
  for (const q of p) { while (lo.length >= 2 && cr(lo[lo.length - 2], lo[lo.length - 1], q) <= 0) lo.pop(); lo.push(q); }
  for (let i = p.length - 1; i >= 0; i--) { const q = p[i]; while (up.length >= 2 && cr(up[up.length - 2], up[up.length - 1], q) <= 0) up.pop(); up.push(q); }
  up.pop(); lo.pop();
  return lo.concat(up);
}
// smooth a closed polygon (Chaikin) so hulls read as soft cartoon shapes
function soften(poly, n = 2) {
  let p = poly;
  for (let k = 0; k < n; k++) { const o = []; for (let i = 0; i < p.length; i++) { const a = p[i], b = p[(i + 1) % p.length]; o.push([a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25], [a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75]); } p = o; }
  return p;
}
const n1 = (x, s) => Math.sin(x * 1.7 + s) * 0.5 + Math.sin(x * 3.1 + s * 2.3) * 0.3 + Math.sin(x * 5.3 + s * 0.7) * 0.2;
function ink(g, pts, w, seed, closed = true) {
  g.strokeStyle = INK; g.lineCap = 'round'; g.lineJoin = 'round';
  const n = pts.length - (closed ? 0 : 1);
  for (let i = 0; i < n; i++) { const a = pts[i], b = pts[(i + 1) % pts.length]; g.lineWidth = Math.max(0.6, w * (0.86 + 0.24 * n1(i * 0.4, seed))); g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke(); }
}
const fillPoly = (g, p, col) => { g.beginPath(); g.moveTo(p[0][0], p[0][1]); for (const q of p) g.lineTo(q[0], q[1]); g.closePath(); g.fillStyle = col; g.fill(); };
function ellipsoidPts(obj, c, r, nu = 18, nv = 9) {
  const o = [];
  for (let i = 0; i < nu; i++) for (let j = 1; j < nv; j++) {
    const th = (i / nu) * Math.PI * 2, ph = (j / nv) * Math.PI;
    o.push(obj.localToWorld(V(c[0] + r[0] * Math.cos(th) * Math.sin(ph), c[1] + r[1] * Math.cos(ph), c[2] + r[2] * Math.sin(th) * Math.sin(ph))));
  }
  return o;
}

function drawCamel(cm) {
  const cam = CH2D.cam; if (!cam) return;
  const o = cm.o, seed = (cm.seed ??= Math.random() * 100);
  cm.root.updateMatrixWorld(true);
  cam.updateMatrixWorld(); _inv.copy(cam.matrixWorld).invert();
  const B = cm.body, H = cm.head;
  const C = B.localToWorld(V(0, 1.3, 0));
  const dC = -C.clone().applyMatrix4(_inv).z;
  if (dC < 0.2) { cm.card.visible = false; return; }
  cm.card.visible = true;
  const dCard = dC;
  const pr = (Pw) => { const c = Pw.clone().applyMatrix4(_inv); const z = Math.max(-c.z, 0.03); return [c.x * dCard / z, c.y * dCard / z, z]; };
  const camPos = V().setFromMatrixPosition(cam.matrixWorld);
  // ---- gather the shapes in plane coordinates
  const bodyP = [...ellipsoidPts(B, [0, 1.35, 0], [0.39, 0.36, 0.725]), ...ellipsoidPts(B, [0, 1.72, -0.05], [0.36, 0.306, 0.432])].map(pr);
  const blanketP = o.blanket === false ? [] : ellipsoidPts(B, [0, 1.38, 0], [0.45, 0.5, 0.63], 18, 5).filter((p, i) => true).map(pr).filter((q, i) => true);
  const headP = [...ellipsoidPts(H, [0, 0, 0], [0.17, 0.164, 0.2], 14, 7), ...ellipsoidPts(H, [0, -0.07, 0.24], [0.145, 0.122, 0.212], 14, 7)].map(pr);
  const sway = cm.pose.neck || 0;
  const neckBase = pr(B.localToWorld(V(0, 1.45, 0.62))), neckCtrl = pr(B.localToWorld(V(0, 2.0 + sway, 1.15)));
  const headC = pr(H.localToWorld(V(0, -0.02, 0.05)));
  const legs = cm.legs.map((L) => ({ hip: pr(cm.root.localToWorld(L.hipR.clone())), kn: pr(cm.root.localToWorld(L.kneeR.clone())), ft: pr(cm.root.localToWorld(L.footR.clone())) }));
  const tail = [pr(B.localToWorld(V(0, 1.3, -0.7))), pr(B.localToWorld(V(0, 1.1, -0.86))), pr(B.localToWorld(V(0.03 * Math.sin(cm._t * 3 || 0), 0.85, -0.82)))];
  const centre = pr(C);
  // bounds
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  const grow = (q, m = 0) => { x0 = Math.min(x0, q[0] - m); x1 = Math.max(x1, q[0] + m); y0 = Math.min(y0, q[1] - m); y1 = Math.max(y1, q[1] + m); };
  for (const q of [...bodyP, ...headP]) grow(q, 0.08);
  for (const L of legs) { grow(L.ft, 0.12); grow(L.kn, 0.1); }
  grow(neckCtrl, 0.2);
  const fov = (cam.fov || 40) * Math.PI / 180;
  { const hh = dCard * Math.tan(fov / 2) * 1.08, hw = hh * (cam.aspect || 0.5625);
    x0 = Math.max(x0, -hw); x1 = Math.min(x1, hw); y0 = Math.max(y0, -hh); y1 = Math.min(y1, hh);
    if (x1 <= x0 || y1 <= y0) { cm.card.visible = false; return; } }
  let k = CH2D.H / (2 * dCard * Math.tan(fov / 2));
  if (Math.max(x1 - x0, y1 - y0) * k > 1700) k = 1700 / Math.max(x1 - x0, y1 - y0);
  const cw = Math.max(16, Math.ceil((x1 - x0) * k)), ch = Math.max(16, Math.ceil((y1 - y0) * k));
  const cv = cm.canvas;
  if (cv.width !== cw || cv.height !== ch) { cv.width = cw; cv.height = ch; cm.tex.dispose(); cm.tex.image = cv; }
  const g = cm.g; g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, cw, ch);
  const X = (q) => [(q[0] - x0) * k, (y1 - q[1]) * k];
  const LW = Math.max(2.2 * CH2D.H / 2560, 0.016 * k);
  const fur = o.fur || '#d6a65e', furD = new THREE.Color(fur).offsetHSL(0, 0, -0.1).getStyle(), hoof = '#6a4a2a';
  const legW = 0.085 * k;
  const stroke = (pts, w, col, outline = true) => {
    const a = pts.map(X);
    const path = () => { g.beginPath(); g.moveTo(a[0][0], a[0][1]); g.quadraticCurveTo(a[1][0], a[1][1], a[2][0], a[2][1]); };
    g.lineCap = 'round'; g.lineJoin = 'round';
    if (outline) { path(); g.strokeStyle = INK; g.lineWidth = w + LW * 1.6; g.stroke(); }
    path(); g.strokeStyle = col; g.lineWidth = w; g.stroke();
  };
  // ---- far legs first (darker), then near legs, all under the body
  const order = legs.map((L, i) => ({ L, i, z: L.hip[2] })).sort((a, b) => b.z - a.z);
  for (const { L, i } of order) {
    const far = L.hip[2] > centre[2];
    stroke([L.hip, L.kn, L.ft], legW, far ? furD : fur);
    const [kx, ky] = X(L.kn); g.fillStyle = far ? furD : fur; g.beginPath(); g.arc(kx, ky, legW * 0.75, 0, Math.PI * 2); g.fill(); g.lineWidth = LW * 0.8; g.strokeStyle = INK; g.stroke();
    const [fx, fy] = X(L.ft); g.fillStyle = hoof; g.beginPath(); g.ellipse(fx, fy - legW * 0.1, legW * 0.85, legW * 0.42, 0, 0, Math.PI * 2); g.fill(); g.stroke();
  }
  // tail
  stroke(tail, 0.03 * k, furD);
  // is the head behind the body?
  const headBehind = headC[2] > centre[2] + 0.25;
  const drawNeckHead = () => {
    stroke([neckBase, neckCtrl, headC], 0.24 * k, fur);
    const hp = soften(hull(headP.map(X)), 2);
    fillPoly(g, hp, fur);
    g.save(); g.beginPath(); g.moveTo(hp[0][0], hp[0][1]); for (const q of hp) g.lineTo(q[0], q[1]); g.closePath(); g.clip();
    const sn = X(pr(H.localToWorld(V(0, -0.09, 0.36))));
    g.fillStyle = 'rgba(255,240,210,0.35)'; g.beginPath(); g.ellipse(sn[0], sn[1], 0.09 * k, 0.07 * k, 0, 0, Math.PI * 2); g.fill();
    g.restore();
    ink(g, hp, LW, seed + 3);
    // ears
    for (const sd of [-1, 1]) {
      const e0 = X(pr(H.localToWorld(V(sd * 0.11, 0.12, -0.04)))), e1 = X(pr(H.localToWorld(V(sd * 0.17, 0.2, -0.08))));
      g.fillStyle = fur; g.beginPath(); g.ellipse((e0[0] + e1[0]) / 2, (e0[1] + e1[1]) / 2, 0.035 * k, 0.06 * k, Math.atan2(e1[1] - e0[1], e1[0] - e0[0]) + Math.PI / 2, 0, Math.PI * 2); g.fill(); g.lineWidth = LW * 0.8; g.strokeStyle = INK; g.stroke();
    }
    // eyes: big, white, heavy-lidded
    const toCam = camPos.clone().sub(H.getWorldPosition(V())).normalize();
    for (const sd of [-1, 1]) {
      const local = V(sd * 0.12, 0.05, 0.1);
      const nW = local.clone().normalize().transformDirection(H.matrixWorld);
      if (nW.dot(toCam) < -0.15) continue;
      const [ex, ey] = X(pr(H.localToWorld(local)));
      const rx = 0.05 * k, ry = 0.065 * k;
      g.fillStyle = '#fbfbf6'; g.beginPath(); g.ellipse(ex, ey, rx, ry, 0, 0, Math.PI * 2); g.fill(); g.lineWidth = LW * 0.8; g.strokeStyle = INK; g.stroke();
      g.fillStyle = INK; g.beginPath(); g.ellipse(ex, ey + ry * 0.3, rx * 0.42, ry * 0.42, 0, 0, Math.PI * 2); g.fill();
      const lid = cm.pose.lid ?? 0.55, ly = ey - ry + 2 * ry * lid;
      g.save(); g.beginPath(); g.ellipse(ex, ey, rx + 1, ry + 1, 0, 0, Math.PI * 2); g.clip(); g.fillStyle = furD; g.fillRect(ex - rx - 2, ey - ry - 2, 2 * rx + 4, ly - (ey - ry) + 2); g.restore();
      g.lineWidth = LW * 1.1; g.beginPath(); g.moveTo(ex - rx * 1.1, ly); g.lineTo(ex + rx * 1.1, ly); g.stroke();
    }
    // nostrils and mouth
    for (const sd of [-1, 1]) { const [nx, ny] = X(pr(H.localToWorld(V(sd * 0.05, -0.04, 0.44)))); g.fillStyle = INK; g.beginPath(); g.ellipse(nx, ny, 0.012 * k, 0.018 * k, 0, 0, Math.PI * 2); g.fill(); }
    const m0 = X(pr(H.localToWorld(V(-0.08, -0.15, 0.36)))), m1 = X(pr(H.localToWorld(V(0.08, -0.15, 0.36)))), mc = X(pr(H.localToWorld(V(0, -0.17 + (cm.pose.chew ? Math.sin(cm._t * 11) * 0.012 : 0), 0.4))));
    g.lineWidth = LW * 0.8; g.strokeStyle = INK; g.beginPath(); g.moveTo(m0[0], m0[1]); g.quadraticCurveTo(mc[0], mc[1], m1[0], m1[1]); g.stroke();
    if (o.bridle) { const b0 = X(pr(H.localToWorld(V(-0.16, -0.02, 0.22)))), b1 = X(pr(H.localToWorld(V(0.16, -0.02, 0.22)))), bc = X(pr(H.localToWorld(V(0, -0.0, 0.33)))); g.lineWidth = 0.025 * k; g.strokeStyle = o.bridle; g.beginPath(); g.moveTo(b0[0], b0[1]); g.quadraticCurveTo(bc[0], bc[1], b1[0], b1[1]); g.stroke(); }
  };
  if (headBehind) drawNeckHead();
  // ---- body + hump
  const bp = soften(hull(bodyP.map(X)), 2);
  fillPoly(g, bp, fur);
  g.save(); g.beginPath(); g.moveTo(bp[0][0], bp[0][1]); for (const q of bp) g.lineTo(q[0], q[1]); g.closePath(); g.clip();
  const xs = bp.map((q) => q[0]), ys = bp.map((q) => q[1]);
  const bx0 = Math.min(...xs), bx1 = Math.max(...xs), by0 = Math.min(...ys), by1 = Math.max(...ys);
  const sh = g.createLinearGradient(0, by0, 0, by1); sh.addColorStop(0, 'rgba(255,255,255,0.18)'); sh.addColorStop(0.55, 'rgba(255,255,255,0)'); sh.addColorStop(1, 'rgba(60,20,0,0.25)');
  g.fillStyle = sh; g.fillRect(bx0, by0, bx1 - bx0, by1 - by0);
  // saddle blanket: a striped cap over the back
  if (o.blanket !== false) {
    const cap = soften(hull(ellipsoidPts(B, [0, 1.42, 0], [0.42, 0.42, 0.62], 18, 4).map(pr).map(X)), 1);
    g.save(); g.beginPath(); g.moveTo(cap[0][0], cap[0][1]); for (const q of cap) g.lineTo(q[0], q[1]); g.closePath(); g.clip();
    const cols = [o.cloth || '#b8262e', o.cloth2 || '#f2c24a', o.cloth3 || '#26307a', o.cloth2 || '#f2c24a'];
    const cy0 = Math.min(...cap.map((q) => q[1])), cy1 = Math.max(...cap.map((q) => q[1])), band = (cy1 - cy0) / 7;
    for (let i = 0; i < 8; i++) { g.fillStyle = cols[i % 4]; g.fillRect(bx0, cy0 + i * band, bx1 - bx0, band + 1); }
    g.restore();
    g.lineWidth = LW * 0.7; g.strokeStyle = INK; g.beginPath(); g.moveTo(cap[0][0], cap[0][1]); for (const q of cap) g.lineTo(q[0], q[1]); g.closePath(); g.stroke();
  }
  g.restore();
  ink(g, bp, LW * 1.05, seed + 1);
  // sacks of gold on both sides
  if (o.sacks) for (const sd of [-1, 1]) {
    const sc = pr(B.localToWorld(V(sd * 0.48, 1.18, 0.05)));
    if (sc[2] > centre[2] + 0.2) continue; // the far sack hides behind the body
    const [sx, sy] = X(sc), r = 0.19 * k;
    g.fillStyle = '#c8a46a'; g.beginPath(); g.ellipse(sx, sy, r * 0.85, r, 0, 0, Math.PI * 2); g.fill(); g.lineWidth = LW * 0.9; g.strokeStyle = INK; g.stroke();
    g.fillStyle = '#ffcf3a'; for (let i = 0; i < 4; i++) { g.beginPath(); g.ellipse(sx + (i - 1.5) * r * 0.35, sy - r * 0.85, r * 0.2, r * 0.09, 0, 0, Math.PI * 2); g.fill(); g.lineWidth = LW * 0.4; g.stroke(); }
    g.strokeStyle = '#7a5a30'; g.lineWidth = LW * 0.6; g.beginPath(); g.moveTo(sx - r * 0.6, sy - r * 0.55); g.quadraticCurveTo(sx, sy - r * 0.35, sx + r * 0.6, sy - r * 0.55); g.stroke();
  }
  // the royal seat
  if (o.seat) {
    const corners = []; for (const x of [-0.31, 0.31]) for (const y of [1.94, 2.06]) for (const z of [-0.36, 0.26]) corners.push(pr(B.localToWorld(V(x, y, z))));
    const sp = hull(corners.map(X));
    fillPoly(g, sp, '#8a1a2e'); ink(g, sp, LW * 0.8, seed + 5);
    const t0 = X(pr(B.localToWorld(V(-0.33, 1.94, 0.28)))), t1 = X(pr(B.localToWorld(V(0.33, 1.94, 0.28))));
    g.strokeStyle = '#f2b830'; g.lineWidth = 0.035 * k; g.beginPath(); g.moveTo(t0[0], t0[1]); g.lineTo(t1[0], t1[1]); g.stroke();
  }
  if (!headBehind) drawNeckHead();
  cm.tex.needsUpdate = true;
  // ---- place the card
  const camQ = new THREE.Quaternion().setFromRotationMatrix(cam.matrixWorld);
  const right = V(1, 0, 0).applyQuaternion(camQ), up = V(0, 1, 0).applyQuaternion(camQ), fwd = V(0, 0, -1).applyQuaternion(camQ);
  const pos = camPos.clone().addScaledVector(fwd, dCard).addScaledVector(right, (x0 + x1) / 2).addScaledVector(up, (y0 + y1) / 2);
  const Mw = new THREE.Matrix4().compose(pos, camQ, V(x1 - x0, y1 - y0, 1));
  cm.card.matrix.copy(_m.copy(cm.root.matrixWorld).invert()).multiply(Mw);
  cm.card.matrixWorldNeedsUpdate = true; cm.card.updateMatrixWorld(true);
  cm.card.material.color.copy(CH2D.tint);
}
