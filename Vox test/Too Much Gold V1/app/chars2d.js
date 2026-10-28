// Hand-drawn 2D people living inside the 3D sets, the way the reference shorts do it: every
// character is a flat drawing (white wobbly ball head, tiny asymmetric face, bean body, stick
// limbs, thick uneven ink lines) painted each frame onto a card that faces the camera.
// A small invisible 3D rig (root, body, neck, head, hand targets, feet) drives the pose, so the
// shots move characters exactly as before; the drawing is made from the rig's projected points.
import * as THREE from 'three';
import { clamp, lerp, hash } from './util.js';

const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const INK = '#1b1215';
const HEAD = '#f8f5ef';
export const CHAR_LAYER = 3;
export const CARDS = [];
// set by the shot runner each frame: the camera, the output height, and a light tint for the drawings
export const CH2D = { cam: null, H: 2560, tint: new THREE.Color(1, 1, 1) };

// body silhouettes (radius, height) for s = 1
const PROFILES = {
  robe: { pts: [[0.205, 0.08], [0.215, 0.11], [0.2, 0.35], [0.182, 0.6], [0.168, 0.8], [0.176, 0.95], [0.172, 1.08], [0.155, 1.2], [0.11, 1.28], [0.045, 1.32]], belt: 0.8, hip: 0.16 },
  dress: { pts: [[0.235, 0.06], [0.24, 0.09], [0.215, 0.4], [0.188, 0.7], [0.165, 0.95], [0.15, 1.12], [0.125, 1.22], [0.08, 1.29], [0.03, 1.32]], belt: 0.8, hip: 0.14 },
  bean: { pts: [[0.1, 0.7], [0.165, 0.728], [0.198, 0.79], [0.208, 0.9], [0.203, 1.0], [0.19, 1.1], [0.165, 1.2], [0.12, 1.28], [0.05, 1.32]], belt: 0.86, hip: 0.76 },
};

// small expression vocabulary, drawn big and funny: dots pop into wide eyes, mouths change shape
export const EXPR = {
  neutral: { eyes: 'dot', brows: [0, 0], mouth: 'line' },
  calm: { eyes: 'closed', brows: [0.1, -4], mouth: 'smile' },
  happy: { eyes: 'dot', brows: [0.45, -8], mouth: 'smileOpen' },
  joy: { eyes: 'happy', brows: [0.55, -10], mouth: 'bigsmile', blush: 1 },
  grin: { eyes: 'happy', brows: [0.3, -6], mouth: 'teeth' },
  proud: { eyes: 'lid', brows: [0.2, 8], mouth: 'smirk' },
  smug: { eyes: 'lid', brows: [[0.05, 14], [0.45, 4]], mouth: 'smirk' },
  greedy: { eyes: 'money', brows: [0.5, -10], mouth: 'grinWide' },
  bored: { eyes: 'lid', brows: [-0.05, 0], mouth: 'line' },
  unimpressed: { eyes: 'lid', brows: [[-0.1, 6], [0.35, -4]], mouth: 'flat' },
  surprised: { eyes: 'open', brows: [0.9, -6], mouth: 'o' },
  shocked: { eyes: 'wide', brows: [1.1, -10], mouth: 'open', sweat: 1 },
  panic: { eyes: 'wide', brows: [1.0, -18], mouth: 'teeth', sweat: 1 },
  worried: { eyes: 'open', brows: [0.6, -22], mouth: 'wavy', sweat: 1 },
  sheepish: { eyes: 'happy', brows: [0.5, -20], mouth: 'teeth', sweat: 1, blush: 0.8 },
  angry: { eyes: 'dot', brows: [-0.25, 26], mouth: 'frown', vein: 1 },
  confused: { eyes: 'open', brows: [[0.7, -8], [-0.1, 14]], mouth: 'wavy' },
  laugh: { eyes: 'happy', brows: [0.5, -8], mouth: 'shout', blush: 0.5, tears: 1 },
  sleepy: { eyes: 'closed', brows: [0, 0], mouth: 'line' },
  dazzled: { eyes: 'money', brows: [0.8, -10], mouth: 'open' },
  shrug: { eyes: 'lid', brows: [0.7, -14], mouth: 'smirk' },
};

export function defaultPose() {
  return { lean: 0, side: 0, yaw: 0, bob: 0, squash: 1, headYaw: 0, headPitch: 0, headRoll: 0, hands: {}, feet: {}, walk: null, bendL: 1, bendR: 1 };
}
export function isBlink(ch, t) {
  const seed = hash(ch.name.length, ch.name.charCodeAt(0));
  const per = 2.8 + seed * 1.6;
  return ((t + seed * 7.3) % per) < 0.11;
}
const _m = new THREE.Matrix4();
export function at(ch, x, y, z) { ch.root.updateMatrixWorld(true); return V(x, y, z).applyMatrix4(ch.root.matrixWorld); }
export function toRoot(ch, wp) { ch.root.updateMatrixWorld(true); return wp.clone().applyMatrix4(_m.copy(ch.root.matrixWorld).invert()); }
export function lookAt(ch, wp, w = 1) {
  const hp = V(); ch.head.getWorldPosition(hp);
  const d = toRoot(ch, wp).sub(toRoot(ch, hp));
  const yaw = Math.atan2(d.x, d.z) - ch.pose.yaw;
  const pitch = -Math.atan2(d.y, Math.hypot(d.x, d.z));
  ch.pose.headYaw = clamp(yaw, -0.9, 0.9) * w * 0.75;
  ch.pose.headPitch = clamp(pitch, -0.5, 0.5) * w * 0.6;
  ch.state.look = [clamp(yaw * 1.2, -1, 1) * w, clamp(-pitch * 1.4, -1, 1) * w];
}

// ---------------------------------------------------------------- the character
export function makeToon(def) {
  const s = def.scale || 1, gth = def.girth || 1;
  const kind = def.body === 'tunic' ? 'bean' : (def.body || 'bean');
  const P = PROFILES[kind];
  const ch = { def, s, kind, P, gth, root: new THREE.Group(), name: def.name };
  ch.seed = (def.seed || 1) * 1.37 + def.name.length * 11.1 + def.name.charCodeAt(0) * 0.13;
  ch.root.name = def.name;
  const body = new THREE.Group(); ch.root.add(body); ch.body = body;
  const neck = new THREE.Group(); neck.position.set(0, 1.28 * s, 0); body.add(neck); ch.neck = neck;
  const R = (def.head || 0.285) * s; ch.R = R;
  const head = new THREE.Group(); head.position.set(0, R * 0.7, 0); neck.add(head); ch.head = head;
  ch.torso = new THREE.Group(); body.add(ch.torso);
  ch.arms = {}; ch.legs = {};
  for (const L of ['l', 'r']) {
    const sd = L === 'l' ? 1 : -1;
    const hand = new THREE.Object3D(); ch.root.add(hand);
    ch.arms[L] = { sd, hand, shoulder: V(sd * 0.15 * s * Math.min(gth, 1.2), 1.18 * s, 0.0), target: V(sd * 0.25 * s, 0.84 * s, 0.06 * s) };
    ch.legs[L] = { sd, hip: V(sd * 0.08 * s, P.hip * s, 0), foot: V(sd * 0.1 * s, 0.024 * s, 0.03 * s) };
  }
  // per-person hand-drawn quirks: head shape, eye sizes, mouth offset
  const r = (k) => hash(ch.seed, k);
  ch.look = {
    a2: 0.025 + r(1) * 0.035, p2: r(2) * 6.28, a3: 0.012 + r(3) * 0.02, p3: r(4) * 6.28, egg: (r(5) - 0.35) * 0.07,
    eyeL: 0.92 + r(6) * 0.16, eyeR: 0.92 + r(7) * 0.16, eyeTilt: (r(8) - 0.5) * 0.06, mouthX: (r(9) - 0.5) * 0.08, browTilt: (r(10) - 0.5) * 8,
    eyeY: (def.eyeY || 0) + (r(11) - 0.5) * 0.04, spread: (def.eyeSpread || 1) * (0.94 + r(12) * 0.12),
  };
  // the card that carries the drawing
  const canvas = document.createElement('canvas'); canvas.width = canvas.height = 64;
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace; tex.generateMipmaps = false; tex.minFilter = THREE.LinearFilter;
  const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, toneMapped: false, alphaTest: 0.03, fog: true, color: new THREE.Color(1, 1, 1) });
  const card = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), mat);
  card.layers.set(CHAR_LAYER);
  card.frustumCulled = false; card.matrixAutoUpdate = false; card.castShadow = true;
  card.customDepthMaterial = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: tex, alphaTest: 0.5 });
  card.userData.ndMat = new THREE.ShaderMaterial({
    uniforms: { map: { value: tex } },
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
    fragmentShader: 'uniform sampler2D map; varying vec2 vUv; void main(){ if (texture2D(map, vUv).a < 0.5) discard; gl_FragColor = vec4(0.5, 0.5, 1.0, 1.0); }',
  });
  ch.root.add(card);
  ch.card = card; ch.canvas = canvas; ch.g = canvas.getContext('2d'); ch.tex = tex;
  CARDS.push(card);
  ch.state = { expr: 'neutral', look: [0, 0], talk: 0, blink: false };
  ch.pose = defaultPose();
  ch.update = (t) => updateToon(ch, t);
  return ch;
}

// ---------------------------------------------------------------- per frame: pose the rig, project it, draw it
const _inv = new THREE.Matrix4(), _q = new THREE.Quaternion(), _sc = new THREE.Vector3(), _pos = new THREE.Vector3();
function updateToon(ch, t) {
  const cam = CH2D.cam; if (!cam) return;
  const p = ch.pose, s = ch.s;
  ch.body.rotation.set(p.lean, p.yaw, p.side);
  ch.body.position.y = p.bob;
  ch.body.scale.set(1 / Math.sqrt(p.squash), p.squash, 1 / Math.sqrt(p.squash));
  ch.neck.rotation.set(p.headPitch, p.headYaw, p.headRoll, 'YXZ');
  ch.root.updateMatrixWorld(true);
  const RW = ch.root.matrixWorld, BM = ch.body.matrix;
  // ---- rig points in world space
  const arms = {};
  for (const L of ['l', 'r']) {
    const a = ch.arms[L];
    const tgt = (p.hands[L] || a.target).clone();
    const sh = a.shoulder.clone().applyMatrix4(BM);
    const d = tgt.clone().sub(sh);
    const maxLen = 0.6 * s;
    if (d.length() > maxLen) tgt.copy(sh).add(d.setLength(maxLen));
    a.hand.position.copy(tgt);
    const len = sh.distanceTo(tgt), slack = Math.max(0, 0.6 * s - len);
    const bend = (L === 'l' ? p.bendL : p.bendR) ?? 1;
    const out = V(a.sd, -0.35, -0.3).normalize().multiplyScalar(slack * 0.75 * bend + 0.02 * s);
    const elbow = sh.clone().add(tgt).multiplyScalar(0.5).add(out);
    arms[L] = { sh: sh.applyMatrix4(RW), el: elbow.applyMatrix4(RW), hd: tgt.applyMatrix4(RW) };
  }
  const legs = {};
  const w = p.walk;
  for (const L of ['l', 'r']) {
    const lg = ch.legs[L];
    const f = (p.feet[L] || lg.foot).clone();
    if (w) { const ph = w.phase * Math.PI * 2 + (L === 'l' ? 0 : Math.PI); f.z += Math.sin(ph) * w.stride * 0.5; f.y += Math.max(0, Math.cos(ph)) * w.lift; }
    const hip = lg.hip.clone().applyMatrix4(BM);
    const rest = lg.hip.y - lg.foot.y, len = hip.distanceTo(f);
    const knee = hip.clone().add(f).multiplyScalar(0.5).add(V(0, 0, 0.02 * s + Math.max(0, rest - len) * 0.9));
    legs[L] = { hip: hip.applyMatrix4(RW), kn: knee.applyMatrix4(RW), ft: f.applyMatrix4(RW) };
  }
  const headW = V(); ch.head.getWorldPosition(headW);
  // ---- camera space and the card plane
  cam.updateMatrixWorld(); _inv.copy(cam.matrixWorld).invert();
  const C = ch.body.localToWorld(V(0, 0.95 * s, 0));
  const Cc = C.clone().applyMatrix4(_inv);
  const dC = -Cc.z;
  if (dC < 0.12) { ch.card.visible = false; return; }
  ch.card.visible = true;
  const dCard = dC + (p.push ?? 0.12 * s); // a little behind the body, so held props sit in front of the drawing
  const pr = (Pw) => { const c = Pw.clone().applyMatrix4(_inv); const z = Math.max(-c.z, 0.03); return [c.x * dCard / z, c.y * dCard / z, z]; };
  const scl = (z) => dCard / z;
  // ---- facing: angle between where the body/head point and the direction to the camera
  const camPos = V().setFromMatrixPosition(cam.matrixWorld);
  const facing = (obj) => {
    const f = V(0, 0, 1).transformDirection(obj.matrixWorld); const o = V(); obj.getWorldPosition(o);
    const c = camPos.clone().sub(o); f.y = 0; c.y = 0; f.normalize(); c.normalize();
    return Math.atan2(f.x * c.z - f.z * c.x, f.x * c.x + f.z * c.z);
  };
  const bodyYaw = facing(ch.body), headYaw = facing(ch.head);
  // ---- project everything
  const P = ch.P, gth = ch.gth;
  const prof = P.pts.map(([r0, y]) => {
    const c = pr(ch.body.localToWorld(V(0, y * s, 0)));
    const gscale = y < 1.05 ? gth : lerp(gth, 1, (y - 1.05) / 0.27);
    return { x: c[0], y: c[1], r: r0 * s * gscale * scl(c[2]) / Math.sqrt(p.squash), z: c[2], yy: y };
  });
  // silhouette normals in 2D (perpendicular to the projected body axis)
  for (let i = 0; i < prof.length; i++) {
    const a = prof[Math.max(0, i - 1)], b = prof[Math.min(prof.length - 1, i + 1)];
    let dx = b.x - a.x, dy = b.y - a.y; const l = Math.hypot(dx, dy) || 1; dx /= l; dy /= l;
    prof[i].nx = dy; prof[i].ny = -dx; // right-hand side of the axis
  }
  const hc = pr(headW), Rp = ch.R * scl(hc[2]);
  const headUp = V(0, 1, 0).transformDirection(ch.head.matrixWorld);
  const hu = pr(headW.clone().addScaledVector(headUp, ch.R));
  const roll = Math.atan2(hu[0] - hc[0], hu[1] - hc[1]);
  const A = {}, Lg = {};
  for (const L of ['l', 'r']) { A[L] = { sh: pr(arms[L].sh), el: pr(arms[L].el), hd: pr(arms[L].hd) }; Lg[L] = { hip: pr(legs[L].hip), kn: pr(legs[L].kn), ft: pr(legs[L].ft) }; }
  // ---- bounds of the drawing (plane metres)
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  const grow = (x, y, m = 0) => { x0 = Math.min(x0, x - m); x1 = Math.max(x1, x + m); y0 = Math.min(y0, y - m); y1 = Math.max(y1, y + m); };
  for (const q of prof) grow(q.x, q.y, q.r + 0.03);
  grow(hc[0], hc[1], Rp * 1.45); grow(hc[0], hc[1] + Rp * 1.0, Rp * 1.0);
  for (const L of ['l', 'r']) { grow(A[L].hd[0], A[L].hd[1], 0.08 * s); grow(A[L].el[0], A[L].el[1], 0.05 * s); grow(Lg[L].ft[0], Lg[L].ft[1], 0.09 * s); }
  if (ch.def.beard3d) grow(hc[0], hc[1] - Rp * 1.9, Rp * 0.7);
  // only what the camera can see needs pixels (a head right in front of the lens stays sharp)
  const fov = (cam.fov || 40) * Math.PI / 180;
  { const hh = dCard * Math.tan(fov / 2) * 1.08, hw = hh * (cam.aspect || 0.5625);
    x0 = Math.max(x0, -hw); x1 = Math.min(x1, hw); y0 = Math.max(y0, -hh); y1 = Math.min(y1, hh);
    if (x1 <= x0 || y1 <= y0) { ch.card.visible = false; return; } }
  let k = CH2D.H / (2 * dCard * Math.tan(fov / 2));
  const MAXPX = 1700;
  if (Math.max(x1 - x0, y1 - y0) * k > MAXPX) k = MAXPX / Math.max(x1 - x0, y1 - y0);
  const cw = Math.max(16, Math.ceil((x1 - x0) * k)), chh = Math.max(16, Math.ceil((y1 - y0) * k));
  const cv = ch.canvas;
  if (cv.width !== cw || cv.height !== chh) { cv.width = cw; cv.height = chh; ch.tex.dispose(); ch.tex.image = cv; }
  const g = ch.g;
  g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, cw, chh);
  const X = (x) => (x - x0) * k, Y = (y) => (y1 - y) * k;
  const D = { g, X, Y, k, s, ch, t, prof, hc, Rp, roll, headYaw, bodyYaw, A, Lg, scl, min: CH2D.H / 2560 };
  // riders are cut off at the seat
  if (p.clipY != null) { const cy = pr(V(C.x, p.clipY, C.z))[1]; g.save(); g.beginPath(); g.rect(0, 0, cw, Y(cy)); g.clip(); drawCharacter(D); g.restore(); }
  else drawCharacter(D);
  ch.tex.needsUpdate = true;
  // ---- place the card (world transform -> local to the root)
  const camQ = new THREE.Quaternion().setFromRotationMatrix(cam.matrixWorld);
  const cxp = (x0 + x1) / 2, cyp = (y0 + y1) / 2;
  const right = V(1, 0, 0).applyQuaternion(camQ), up = V(0, 1, 0).applyQuaternion(camQ), fwd = V(0, 0, -1).applyQuaternion(camQ);
  _pos.copy(camPos).addScaledVector(fwd, dCard).addScaledVector(right, cxp).addScaledVector(up, cyp);
  _sc.set(x1 - x0, y1 - y0, 1);
  const Mw = new THREE.Matrix4().compose(_pos, camQ, _sc);
  ch.card.matrix.copy(_m.copy(RW).invert()).multiply(Mw);
  ch.card.matrixWorldNeedsUpdate = true;
  ch.card.updateMatrixWorld(true);
  ch.card.material.color.copy(CH2D.tint);
}

// ---------------------------------------------------------------- drawing helpers
const shade = (hex, f) => { const c = new THREE.Color(hex); c.offsetHSL(0, 0, f); return '#' + c.getHexString(); };
const n1 = (x, s) => Math.sin(x * 1.7 + s) * 0.5 + Math.sin(x * 3.1 + s * 2.3) * 0.3 + Math.sin(x * 5.3 + s * 0.7) * 0.2;
// stroke a polyline with ink whose width swells and thins like a brush
function inkLine(g, pts, w, seed = 1, closed = false, col = INK) {
  g.strokeStyle = col; g.lineCap = 'round'; g.lineJoin = 'round';
  const n = pts.length - (closed ? 0 : 1);
  for (let i = 0; i < n; i++) {
    const a = pts[i], b = pts[(i + 1) % pts.length];
    g.lineWidth = Math.max(0.6, w * (0.86 + 0.24 * n1(i * 0.45, seed)));
    g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke();
  }
}
function pathOf(g, pts) { g.beginPath(); g.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) g.lineTo(pts[i][0], pts[i][1]); g.closePath(); }
// sample a quadratic curve (canvas px)
function quad(a, c, b, n = 12) { const o = []; for (let i = 0; i <= n; i++) { const t = i / n, u = 1 - t; o.push([u * u * a[0] + 2 * u * t * c[0] + t * t * b[0], u * u * a[1] + 2 * u * t * c[1] + t * t * b[1]]); } return o; }

function drawCharacter(D) {
  const { g, X, Y, k, ch, A, Lg, prof, bodyYaw, min } = D;
  const s = ch.s, def = ch.def;
  const LW = Math.max(2.2 * min, 0.0155 * k);           // main outline
  const limbW = Math.max(2.2 * min, 0.024 * s * k);     // arms and legs
  D.LW = LW;
  const front = Math.cos(bodyYaw);
  // which arm is behind the body?
  const behind = (L) => A[L].hd[2] > (prof[4].z + 0.03) && A[L].el[2] > prof[4].z - 0.05;
  // ---- legs (always behind the body)
  for (const L of ['l', 'r']) {
    const l = Lg[L];
    const pts = quad([X(l.hip[0]), Y(l.hip[1])], [X(l.kn[0]), Y(l.kn[1])], [X(l.ft[0]), Y(l.ft[1])], 10);
    inkLine(g, pts, limbW, ch.seed + (L === 'l' ? 3 : 7), false, '#1d1a22');
    // little feet pointing the way he faces
    const fx = X(l.ft[0]), fy = Y(l.ft[1]);
    const dir = Math.sin(bodyYaw) * 0.9;
    g.fillStyle = def.shoes || '#221c22';
    g.beginPath(); g.ellipse(fx - dir * 0.03 * s * k, fy - 0.004 * k, 0.045 * s * k * (0.6 + 0.4 * Math.abs(dir)), 0.024 * s * k, 0, 0, Math.PI * 2); g.fill();
    if (def.shoes) { g.lineWidth = LW * 0.5; g.strokeStyle = INK; g.stroke(); }
  }
  for (const L of ['l', 'r']) if (behind(L)) drawArm(D, L, limbW);
  drawBody(D);
  if (ch.state.bling || def.necklace) drawChains(D, !!ch.state.bling);
  drawHead(D);
  for (const L of ['l', 'r']) if (!behind(L)) drawArm(D, L, limbW);
}

function drawArm(D, L, w) {
  const { g, X, Y, A, ch, k } = D;
  const a = A[L];
  const pts = quad([X(a.sh[0]), Y(a.sh[1])], [X(a.el[0]), Y(a.el[1])], [X(a.hd[0]), Y(a.hd[1])], 12);
  inkLine(g, pts, w, ch.seed + (L === 'l' ? 11 : 13), false, '#1d1a22');
  // ball hand with a soft highlight
  const hx = X(a.hd[0]), hy = Y(a.hd[1]), r = Math.max(2.4 * D.min, 0.04 * ch.s * k);
  g.fillStyle = '#1d1a22'; g.beginPath(); g.arc(hx, hy, r, 0, Math.PI * 2); g.fill();
  g.fillStyle = 'rgba(255,255,255,0.22)'; g.beginPath(); g.ellipse(hx - r * 0.35, hy - r * 0.38, r * 0.32, r * 0.22, -0.6, 0, Math.PI * 2); g.fill();
}

function bodyOutline(D) {
  const { X, Y, prof } = D;
  const right = [], left = [];
  for (const q of prof) { right.push([X(q.x + q.nx * q.r), Y(q.y + q.ny * q.r)]); left.push([X(q.x - q.nx * q.r), Y(q.y - q.ny * q.r)]); }
  // round the bottom with a soft curve between the two lowest points
  const b0 = prof[0];
  const bottom = quad(left[0], [X(b0.x), Y(b0.y - Math.abs(b0.r) * (D.ch.kind === 'bean' ? 0.55 : 0.12))], right[0], 8);
  // round the top
  const tq = prof[prof.length - 1];
  const top = quad(right[right.length - 1], [X(tq.x - tq.ny * 0 + 0), Y(tq.y + tq.r * 1.4)], left[left.length - 1], 8);
  return [...bottom, ...right.slice(1), ...top.slice(1), ...left.slice(0, -1).reverse()];
}

function drawBody(D) {
  const { g, X, Y, k, ch, prof, bodyYaw, LW } = D;
  const def = ch.def;
  const pts = bodyOutline(D);
  const front = Math.cos(bodyYaw), side = Math.sin(bodyYaw);
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const bx0 = Math.min(...xs), bx1 = Math.max(...xs), by0 = Math.min(...ys), by1 = Math.max(...ys);
  g.save();
  pathOf(g, pts); g.fillStyle = def.color; g.fill();
  g.clip();
  // painted shading: light from the upper left, shadow on the right and at the hem
  const sh = g.createLinearGradient(bx0, 0, bx1, 0);
  sh.addColorStop(0, 'rgba(255,255,255,0.16)'); sh.addColorStop(0.45, 'rgba(255,255,255,0)'); sh.addColorStop(1, 'rgba(10,0,30,0.26)');
  g.fillStyle = sh; g.fillRect(bx0, by0, bx1 - bx0, by1 - by0);
  // where the front of the clothes is (moves as he turns)
  const at = (yy) => { // x of the front centre line at body height yy (metres), and the half width there
    let q = prof[0]; for (const p of prof) if (p.yy <= yy) q = p;
    return { x: X(q.x + q.nx * q.r * side), y: Y(q.y), r: q.r * k, q };
  };
  const vis = front > 0.15;
  const ink = 'rgba(27,18,21,0.9)';
  if (def.pattern === 'stripes' || def.pattern === 'pinstripe') {
    g.strokeStyle = def.stripe; g.lineWidth = (def.pattern === 'stripes' ? 0.022 : 0.009) * k;
    const step = (def.pattern === 'stripes' ? 0.07 : 0.045) * k, off = (side * 0.2 * k) % step;
    for (let x = bx0 - step + off; x < bx1 + step; x += step) { g.beginPath(); g.moveTo(x, by0); g.lineTo(x + (bx1 - bx0) * 0.02, by1); g.stroke(); }
  }
  if (def.pattern === 'patched') {
    for (let i = 0; i < 4; i++) {
      const px = lerp(bx0, bx1, 0.2 + hash(ch.seed, i) * 0.5), py = lerp(by0, by1, 0.3 + hash(ch.seed, i + 5) * 0.5), w = (0.06 + hash(i, 3) * 0.05) * k;
      g.fillStyle = ['#a08060', '#6e5a40', '#8a7050'][i % 3]; g.fillRect(px, py, w, w * 0.8);
      g.setLineDash([w * 0.12, w * 0.1]); g.strokeStyle = ink; g.lineWidth = LW * 0.35; g.strokeRect(px + w * 0.1, py + w * 0.1, w * 0.8, w * 0.6); g.setLineDash([]);
    }
  }
  if (vis && def.apron) {
    const a = at(1.2), b = at(ch.P.pts[0][1] + 0.12);
    const wA = 0.11 * k * ch.gth;
    g.fillStyle = def.apron; g.beginPath(); g.moveTo(a.x - wA * 0.8, a.y); g.lineTo(a.x + wA * 0.8, a.y); g.lineTo(b.x + wA * 1.2, b.y); g.quadraticCurveTo(b.x, b.y + wA * 0.25, b.x - wA * 1.2, b.y); g.closePath(); g.fill();
    g.strokeStyle = ink; g.lineWidth = LW * 0.45; g.stroke();
  }
  if (vis && def.trim) {
    const a = at(1.3), b = at(0.0);
    const wT = 0.04 * k;
    g.fillStyle = def.trim; g.beginPath(); g.moveTo(a.x - wT, a.y); g.lineTo(a.x + wT, a.y); g.lineTo(b.x + wT * 1.2, b.y + 40); g.lineTo(b.x - wT * 1.2, b.y + 40); g.closePath(); g.fill();
    g.strokeStyle = ink; g.lineWidth = LW * 0.35; g.stroke();
    if (def.trimDots) { g.fillStyle = def.trimDots; for (let yy = 1.15; yy > ch.P.pts[0][1] + 0.05; yy -= 0.13) { const c = at(yy); g.beginPath(); g.arc(c.x, c.y, 0.017 * k, 0, Math.PI * 2); g.fill(); } }
  }
  if (def.hem) { const b = at(ch.P.pts[0][1] + 0.08); g.fillStyle = def.hem; g.fillRect(bx0, b.y, bx1 - bx0, by1 - b.y); g.strokeStyle = ink; g.lineWidth = LW * 0.4; g.beginPath(); g.moveTo(bx0, b.y); g.lineTo(bx1, b.y); g.stroke(); }
  if (def.belt) {
    const c = at(ch.P.belt), hw = 0.03 * k;
    g.fillStyle = def.belt; g.beginPath(); g.moveTo(bx0, c.y - hw); g.quadraticCurveTo(c.x, c.y - hw + 0.02 * k, bx1, c.y - hw); g.lineTo(bx1, c.y + hw); g.quadraticCurveTo(c.x, c.y + hw + 0.02 * k, bx0, c.y + hw); g.closePath(); g.fill();
    g.strokeStyle = ink; g.lineWidth = LW * 0.4; g.stroke();
  }
  if (vis && def.collar) {
    const top = at(1.32), meet = at(1.1);
    const wc = 0.075 * k;
    g.fillStyle = def.collar; g.strokeStyle = ink; g.lineWidth = LW * 0.45;
    for (const sd of [-1, 1]) {
      g.beginPath(); g.moveTo(top.x + sd * wc * 1.25, top.y); g.lineTo(top.x + sd * wc * 0.35, top.y);
      g.lineTo(meet.x - sd * wc * 0.12, meet.y); g.lineTo(meet.x + sd * wc * 0.45, meet.y - 0.03 * k); g.closePath(); g.fill(); g.stroke();
    }
  }
  if (vis && def.buttons) { g.fillStyle = def.buttons; g.strokeStyle = ink; g.lineWidth = LW * 0.3; for (let i = 0; i < 4; i++) { const c = at(1.2 - i * 0.1); g.beginPath(); g.arc(c.x, c.y, 0.016 * k, 0, Math.PI * 2); g.fill(); g.stroke(); } }
  // a soft rim of light on the lit side
  g.strokeStyle = 'rgba(255,255,255,0.25)'; g.lineWidth = LW * 1.2; g.beginPath();
  const lp = pts.slice(Math.floor(pts.length * 0.62), Math.floor(pts.length * 0.9));
  if (lp.length) { g.moveTo(lp[0][0] + LW, lp[0][1]); for (const q of lp) g.lineTo(q[0] + LW, q[1]); g.stroke(); }
  g.restore();
  inkLine(g, [...pts, pts[0]], LW, ch.seed + 21);
}

function drawChains(D, rich) {
  const { g, X, Y, k, ch, prof, bodyYaw } = D;
  const side = Math.sin(bodyYaw);
  const q = prof[prof.length - 2], q2 = prof[prof.length - 4];
  const cx = X(q.x + q.nx * q.r * side * 0.6), cy = Y(q.y);
  const w = q.r * k * 0.95;
  g.lineCap = 'round';
  const loops = rich ? [[0.0, 0.08], [0.04, 0.16]] : [[0.0, 0.07]];
  for (const [dy, sag] of loops) {
    g.strokeStyle = '#8a5a10'; g.lineWidth = 0.03 * k; g.beginPath(); g.moveTo(cx - w, cy + dy * k); g.quadraticCurveTo(cx, cy + (dy + sag * 2) * k, cx + w, cy + dy * k); g.stroke();
    g.strokeStyle = '#ffd24a'; g.lineWidth = 0.018 * k; g.stroke();
  }
  const my = cy + (loops[loops.length - 1][0] + loops[loops.length - 1][1]) * k * 1.0 + 0.02 * k;
  g.fillStyle = '#f2b830'; g.beginPath(); g.arc(cx, my, 0.045 * k, 0, Math.PI * 2); g.fill();
  g.strokeStyle = INK; g.lineWidth = D.LW * 0.45; g.stroke();
  g.fillStyle = 'rgba(255,255,255,0.6)'; g.beginPath(); g.arc(cx - 0.014 * k, my - 0.014 * k, 0.012 * k, 0, Math.PI * 2); g.fill();
}

// head outline: a wobbly, slightly egg-shaped hand-drawn circle
function headPts(D, R) {
  const L = D.ch.look, out = [];
  for (let i = 0; i < 72; i++) {
    const th = (i / 72) * Math.PI * 2;
    const rr = R * (1 + L.a2 * Math.cos(2 * th + L.p2) + L.a3 * Math.cos(3 * th + L.p3) + L.egg * Math.sin(th));
    out.push([Math.cos(th) * rr, -Math.sin(th) * rr]);
  }
  return out;
}

function drawHead(D) {
  const { g, X, Y, ch, hc, Rp, k, roll, headYaw, LW } = D;
  const def = ch.def;
  const R = Rp * k;                           // head radius in canvas px
  const hx = X(hc[0]), hy = Y(hc[1]);
  const back = Math.cos(headYaw) < -0.25;
  const fx = Math.sin(headYaw) * 0.5;         // features slide toward where he looks (in R units)
  g.save(); g.translate(hx, hy); g.rotate(roll);
  const hp = headPts(D, R);
  const hat = def.hat || {};
  if (hat.type === 'hijab') drawHijab(g, R, hat, LW, ch, 'back');
  if (hat.type === 'crown') drawCrown(g, R, LW, fx, 'back');
  // skin
  g.save(); pathOf(g, hp); g.fillStyle = HEAD; g.fill(); g.clip();
  const gr = g.createRadialGradient(-R * 0.35, -R * 0.4, R * 0.1, 0, 0, R * 1.15);
  gr.addColorStop(0, 'rgba(255,255,255,0.35)'); gr.addColorStop(0.6, 'rgba(255,255,255,0)'); gr.addColorStop(1, 'rgba(70,80,140,0.2)');
  g.fillStyle = gr; g.fillRect(-R * 1.3, -R * 1.3, R * 2.6, R * 2.6);
  // glossy sheen across the forehead
  g.fillStyle = 'rgba(255,255,255,0.32)'; g.beginPath(); g.ellipse(-R * 0.18, -R * 0.62, R * 0.55, R * 0.12, -0.12, 0, Math.PI * 2); g.fill();
  if (!back) drawFace(D, g, R, fx, Math.sin(ch.pose.headPitch) * -0.25);
  g.restore();
  inkLine(g, [...hp, hp[0]], LW * 1.12, ch.seed + 31);
  if (hat.type) drawHat(g, R, hat, LW, ch, fx, back);
  if (def.beard3d) drawLongBeard(g, R, def.beard3d, LW, fx, back);
  // sweat drop sits outside the head outline
  const e = EXPR[ch.state.expr] || EXPR.neutral;
  if (e.sweat && !back) {
    const sx = R * (1.08 - fx * 0.2), sy = -R * 0.12;
    g.fillStyle = '#8fd4ff'; g.beginPath(); g.moveTo(sx, sy - R * 0.2); g.quadraticCurveTo(sx + R * 0.13, sy, sx, sy + R * 0.08); g.quadraticCurveTo(sx - R * 0.13, sy, sx, sy - R * 0.2); g.fill();
    g.strokeStyle = INK; g.lineWidth = LW * 0.45; g.stroke();
    g.fillStyle = 'rgba(255,255,255,0.9)'; g.beginPath(); g.ellipse(sx - R * 0.03, sy - R * 0.01, R * 0.02, R * 0.035, 0, 0, Math.PI * 2); g.fill();
  }
  g.restore();
}

// ---------------------------------------------------------------- faces
function drawFace(D, g, R, fx, fy) {
  const ch = D.ch, st = ch.state, L = ch.look, def = ch.def;
  const e = { ...(EXPR[st.expr] || EXPR.neutral) };
  const talk = Math.round((st.talk || 0) * 4) / 4;
  const blink = st.blink || (!st.noBlink && isBlink(ch, D.t));
  const lw = R * 0.07;
  const sq = 1 - Math.abs(fx) * 0.35;           // features bunch up as the head turns
  const ex = 0.33 * L.spread * sq, ey = 0.06 + L.eyeY + fy;
  const P = (x, y) => [R * (x + fx), -R * (y)];
  const look = st.look || [0, 0];
  g.lineCap = 'round'; g.lineJoin = 'round'; g.strokeStyle = INK; g.fillStyle = INK;
  const ell = (x, y, rx, ry, rot = 0) => { g.beginPath(); g.ellipse(x, y, Math.max(rx, 0.5), Math.max(ry, 0.5), rot, 0, Math.PI * 2); };
  // ---- beard and moustache under the features
  if (def.beard) {
    const full = def.beard === 'full';
    const w = (full ? 0.34 : 0.2) * sq, top = -0.64, h = full ? 0.28 : 0.2;
    g.fillStyle = def.beardColor || INK;
    const [ax, ay] = P(-w, top + 0.02), [bx, by] = P(w, top + 0.02), [cx, cy] = P(0, top + 0.07), [tx, ty] = P(0.02, top - h);
    g.beginPath(); g.moveTo(ax, ay); g.quadraticCurveTo(cx, cy, bx, by);
    g.bezierCurveTo(...P(w * 1.05, top - h * 0.55), ...P(w * 0.4, top - h * 0.98), tx, ty);
    g.bezierCurveTo(...P(-w * 0.45, top - h * 0.95), ...P(-w * 1.05, top - h * 0.5), ax, ay); g.fill();
    g.strokeStyle = 'rgba(255,255,255,0.18)'; g.lineWidth = lw * 0.35;
    for (let i = -2; i <= 2; i++) { g.beginPath(); g.moveTo(...P(i * w * 0.3, top - 0.05)); g.lineTo(...P(i * w * 0.24, top - h * 0.7)); g.stroke(); }
  }
  // ---- eyes
  const type = blink ? 'closed' : e.eyes;
  for (const sd of [-1, 1]) {
    const sz = sd < 0 ? L.eyeL : L.eyeR;
    const [cx, cy] = P(sd * ex, ey + sd * L.eyeTilt);
    const lx = look[0] * R * 0.06, ly = -look[1] * R * 0.05;
    g.strokeStyle = INK; g.fillStyle = INK;
    if (type === 'dot') { ell(cx + lx * 0.5, cy + ly * 0.5, R * 0.085 * sz, R * 0.115 * sz); g.fill(); }
    else if (type === 'lid') {
      const rx = R * 0.135 * sz, ry = R * 0.11 * sz;
      g.save(); g.beginPath(); g.rect(cx - rx * 2, cy - ry * 0.05, rx * 4, ry * 3); g.clip(); ell(cx + lx * 0.4, cy + ly * 0.3, rx, ry); g.fill(); g.restore();
      g.lineWidth = lw * 1.05; g.beginPath(); g.moveTo(cx - rx * 1.5, cy - ry * 0.05 + sd * R * 0.012); g.lineTo(cx + rx * 1.45, cy - ry * 0.05 - sd * R * 0.012); g.stroke();
    } else if (type === 'open' || type === 'wide' || type === 'money') {
      const rr = R * (type === 'wide' ? 0.25 : 0.205) * sz;
      g.fillStyle = '#fbfbf7'; ell(cx, cy, rr * 0.96, rr); g.fill(); g.lineWidth = lw * 0.95; g.stroke();
      if (type === 'money') {
        const pr = rr * 0.55; g.fillStyle = '#ffc21a'; ell(cx + lx, cy + ly, pr, pr); g.fill(); g.lineWidth = lw * 0.5; g.stroke();
        g.strokeStyle = '#a06c00'; g.lineWidth = lw * 0.4; ell(cx + lx, cy + ly, pr * 0.58, pr * 0.58); g.stroke();
      } else { const pr = rr * (type === 'wide' ? 0.24 : 0.3); g.fillStyle = INK; ell(cx + lx, cy + ly, pr, pr * 1.06); g.fill(); }
    } else if (type === 'happy') { g.lineWidth = lw * 1.1; g.beginPath(); g.arc(cx, cy + R * 0.09, R * 0.15 * sz, Math.PI * 1.12, Math.PI * 1.88); g.stroke(); }
    else if (type === 'closed') { g.lineWidth = lw; g.beginPath(); g.moveTo(cx - R * 0.12 * sz, cy + R * 0.01); g.quadraticCurveTo(cx, cy + R * 0.035, cx + R * 0.12 * sz, cy); g.stroke(); }
  }
  if (def.glasses) {
    g.strokeStyle = INK; g.lineWidth = lw * 0.6;
    for (const sd of [-1, 1]) { const [cx, cy] = P(sd * ex, ey); ell(cx, cy, R * 0.19, R * 0.18); g.stroke(); }
    g.beginPath(); g.moveTo(...P(-ex + 0.19, ey + 0.03)); g.quadraticCurveTo(...P(0, ey + 0.08), ...P(ex - 0.19, ey + 0.03)); g.stroke();
  }
  // ---- brows: short thick dashes
  const br = Array.isArray(e.brows[0]) ? e.brows : [e.brows, e.brows];
  for (const sd of [-1, 1]) {
    const [raise, ang] = sd < 0 ? br[0] : br[1];
    const by = ey + 0.3 + raise * 0.1;
    const a = ((ang + L.browTilt * sd) * Math.PI / 180) * sd;
    const len = 0.165 * sq;
    const [cx, cy] = P(sd * (ex + 0.02), by);
    const dx = Math.cos(a) * len * R, dy = Math.sin(a) * len * R;
    g.strokeStyle = INK; g.lineWidth = lw * 1.35 * (def.browW || 1);
    g.beginPath(); g.moveTo(cx - dx, cy - dy); g.quadraticCurveTo(cx, cy - R * 0.025, cx + dx, cy + dy); g.stroke();
  }
  // ---- mouth
  let m = e.mouth;
  if (talk > 0) m = talk >= 0.75 ? (m === 'teeth' || m === 'bigsmile' || m === 'grinWide' ? 'bigsmile' : 'open') : talk >= 0.5 ? 'openSmall' : 'o';
  const [mx, my] = P(L.mouthX, -0.3);
  const W = R * 0.19 * sq * (def.mouthW || 1);
  g.strokeStyle = INK; g.fillStyle = '#4a1418'; g.lineWidth = lw;
  if (m === 'line' || m === 'flat') { g.beginPath(); g.moveTo(mx - W * (m === 'flat' ? 0.75 : 0.9), my); g.quadraticCurveTo(mx, my + R * 0.012, mx + W * (m === 'flat' ? 0.75 : 0.9), my - R * 0.01); g.stroke(); }
  else if (m === 'smile') { g.beginPath(); g.moveTo(mx - W, my - R * 0.03); g.quadraticCurveTo(mx, my + R * 0.13, mx + W, my - R * 0.04); g.stroke(); }
  else if (m === 'frown') { g.beginPath(); g.moveTo(mx - W, my + R * 0.05); g.quadraticCurveTo(mx, my - R * 0.09, mx + W, my + R * 0.05); g.stroke(); }
  else if (m === 'smirk') { g.beginPath(); g.moveTo(mx - W * 0.9, my + R * 0.015); g.quadraticCurveTo(mx + W * 0.25, my + R * 0.07, mx + W * 1.0, my - R * 0.08); g.stroke(); }
  else if (m === 'wavy') { g.lineWidth = lw * 0.9; g.beginPath(); for (let i = 0; i <= 14; i++) { const x = mx - W + (2 * W * i) / 14, y = my + Math.sin(i * 1.5) * R * 0.03; i ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke(); }
  else if (m === 'o') { ell(mx, my, R * 0.06, R * 0.075); g.fill(); g.stroke(); }
  else if (m === 'openSmall') { ell(mx, my + R * 0.01, R * 0.1, R * 0.075); g.fill(); g.stroke(); }
  else if (m === 'open' || m === 'shout') {
    const rx = R * (m === 'shout' ? 0.2 : 0.12), ry = R * (m === 'shout' ? 0.17 : 0.13);
    g.beginPath(); g.moveTo(mx - rx, my - ry * 0.3); g.quadraticCurveTo(mx, my - ry * 0.55, mx + rx, my - ry * 0.3); g.quadraticCurveTo(mx + rx * 0.9, my + ry * 1.2, mx, my + ry * 1.15); g.quadraticCurveTo(mx - rx * 0.9, my + ry * 1.2, mx - rx, my - ry * 0.3); g.closePath();
    g.fill(); g.save(); g.clip(); g.fillStyle = '#e0606a'; ell(mx, my + ry * 1.05, rx * 0.7, ry * 0.5); g.fill();
    if (m === 'shout') { g.fillStyle = '#fbfbf7'; g.fillRect(mx - rx, my - ry * 0.6, rx * 2, ry * 0.45); }
    g.restore(); g.stroke();
  } else if (m === 'teeth' || m === 'grinWide') {
    const rx = R * (m === 'grinWide' ? 0.26 : 0.17) * sq, ry = R * (m === 'grinWide' ? 0.1 : 0.12);
    g.fillStyle = '#fbfbf7'; g.beginPath(); g.roundRect(mx - rx, my - ry, rx * 2, ry * 2, ry * 0.7); g.fill();
    g.save(); g.clip(); g.lineWidth = lw * 0.55; g.beginPath(); g.moveTo(mx - rx, my); g.lineTo(mx + rx, my);
    const n = m === 'grinWide' ? 6 : 4; for (let i = 1; i < n; i++) { const x = mx - rx + (2 * rx * i) / n; g.moveTo(x, my - ry); g.lineTo(x, my + ry); } g.stroke();
    if (m === 'grinWide') { g.fillStyle = '#ffc21a'; g.fillRect(mx + rx * 0.34, my - ry, rx * 0.32, ry); }
    g.restore(); g.lineWidth = lw * 0.95; g.beginPath(); g.roundRect(mx - rx, my - ry, rx * 2, ry * 2, ry * 0.7); g.stroke();
  } else if (m === 'smileOpen' || m === 'bigsmile') {
    const rx = R * (m === 'bigsmile' ? 0.2 : 0.15), ry = R * (m === 'bigsmile' ? 0.17 : 0.12);
    g.beginPath(); g.moveTo(mx - rx, my - ry * 0.3); g.quadraticCurveTo(mx, my - ry * 0.15, mx + rx, my - ry * 0.35); g.quadraticCurveTo(mx + rx * 0.7, my + ry * 1.1, mx - R * 0.01, my + ry); g.quadraticCurveTo(mx - rx * 0.8, my + ry * 0.95, mx - rx, my - ry * 0.3); g.closePath();
    g.fill(); g.save(); g.clip(); g.fillStyle = '#fbfbf7'; g.fillRect(mx - rx, my - ry * 0.5, rx * 2, ry * 0.42); g.fillStyle = '#e0606a'; ell(mx, my + ry * 0.95, rx * 0.6, ry * 0.42); g.fill(); g.restore(); g.stroke();
  }
  if (def.moustache) {
    const [cx, cy] = P(L.mouthX * 0.6, -0.19);
    g.fillStyle = def.hairColor || INK;
    for (const sd of [-1, 1]) {
      g.beginPath(); g.moveTo(cx, cy - R * 0.03);
      if (def.moustache === 'curl') {
        g.bezierCurveTo(cx + sd * R * 0.12, cy - R * 0.09, cx + sd * R * 0.28, cy - R * 0.02, cx + sd * R * 0.31, cy - R * 0.12);
        g.bezierCurveTo(cx + sd * R * 0.35, cy + R * 0.07, cx + sd * R * 0.12, cy + R * 0.07, cx, cy + R * 0.035);
      } else {
        g.bezierCurveTo(cx + sd * R * 0.1, cy - R * 0.08, cx + sd * R * 0.23, cy - R * 0.04, cx + sd * R * 0.25, cy + R * 0.06);
        g.bezierCurveTo(cx + sd * R * 0.15, cy + R * 0.07, cx + sd * R * 0.06, cy + R * 0.035, cx, cy + R * 0.035);
      }
      g.fill();
    }
    g.strokeStyle = 'rgba(255,255,255,0.2)'; g.lineWidth = lw * 0.3;
    for (let i = -3; i <= 3; i++) { if (!i) continue; g.beginPath(); g.moveTo(cx + i * R * 0.05, cy - R * 0.04); g.lineTo(cx + i * R * 0.06, cy + R * 0.03); g.stroke(); }
  }
  if (e.blush || def.blushBase) {
    g.fillStyle = `rgba(236,104,118,${0.4 * (e.blush || def.blushBase)})`;
    for (const sd of [-1, 1]) { const [cx, cy] = P(sd * (ex + 0.14), ey - 0.2); ell(cx, cy, R * 0.12, R * 0.065); g.fill(); }
  }
  if (e.tears) {
    g.fillStyle = 'rgba(140,210,255,0.95)';
    for (const sd of [-1, 1]) { const [cx, cy] = P(sd * (ex + 0.12), ey - 0.1); g.beginPath(); g.ellipse(cx, cy, R * 0.035, R * 0.06, 0, 0, Math.PI * 2); g.fill(); }
  }
  if (e.vein) {
    const [cx, cy] = P(0.45, 0.6); g.strokeStyle = '#d0242a'; g.lineWidth = lw * 0.8;
    for (const a of [0, 1.57, 3.14, 4.71]) { g.beginPath(); g.arc(cx + Math.cos(a + 0.78) * R * 0.07, cy + Math.sin(a + 0.78) * R * 0.07, R * 0.045, a + 0.4, a + 2.3); g.stroke(); }
  }
}

// ---------------------------------------------------------------- hats, drawn flat
function outlineFill(g, LW, col, seed, build) { g.beginPath(); build(); g.fillStyle = col; g.fill(); g.strokeStyle = INK; g.lineWidth = LW; g.stroke(); }
function drawHat(g, R, h, LW, ch, fx, back) {
  const t = h.type;
  if (t === 'turban' || t === 'wrap') {
    const big = h.size || 1, top = t === 'wrap' ? 0.85 : 1.18 * big, wid = (t === 'wrap' ? 1.02 : 1.06) * big;
    const base = 0.32;
    const shape = () => {
      g.moveTo(-R * wid, -R * base); g.bezierCurveTo(-R * wid * 1.05, -R * (base + 0.45), -R * wid * 0.85, -R * top, 0, -R * top);
      g.bezierCurveTo(R * wid * 0.85, -R * top, R * wid * 1.05, -R * (base + 0.45), R * wid, -R * base);
      g.quadraticCurveTo(0, -R * (base - 0.16), -R * wid, -R * base); g.closePath();
    };
    g.save(); g.beginPath(); shape(); g.fillStyle = h.color; g.fill(); g.clip();
    // wrapped cloth folds
    g.strokeStyle = h.stripe || shade(h.color, -0.16); g.lineWidth = R * 0.07;
    for (let i = 0; i < 4; i++) { const y = -R * (base + 0.12 + i * 0.2 * big); g.beginPath(); g.moveTo(-R * 1.2, y + R * 0.18); g.quadraticCurveTo(fx * R, y - R * 0.12, R * 1.2, y - R * 0.05 * (i % 2 ? -1 : 1)); g.stroke(); }
    g.strokeStyle = 'rgba(0,0,0,0.18)'; g.lineWidth = R * 0.035;
    for (let i = 0; i < 3; i++) { const y = -R * (base + 0.22 + i * 0.22 * big); g.beginPath(); g.moveTo(-R * 1.1, y); g.quadraticCurveTo(0, y - R * 0.2, R * 1.1, y + R * 0.06); g.stroke(); }
    g.fillStyle = 'rgba(255,255,255,0.22)'; g.beginPath(); g.ellipse(-R * 0.35, -R * (top - 0.18), R * 0.35, R * 0.1, -0.2, 0, Math.PI * 2); g.fill();
    g.restore();
    g.beginPath(); shape(); g.strokeStyle = INK; g.lineWidth = LW; g.stroke();
    if (h.jewel && !back) {
      const jx = fx * R * 1.2, jy = -R * (base + 0.22);
      g.fillStyle = '#f2b830'; g.beginPath(); g.arc(jx, jy, R * 0.15, 0, Math.PI * 2); g.fill(); g.lineWidth = LW * 0.5; g.stroke();
      g.fillStyle = h.jewel; g.beginPath(); g.arc(jx, jy, R * 0.09, 0, Math.PI * 2); g.fill();
      g.fillStyle = 'rgba(255,255,255,0.8)'; g.beginPath(); g.arc(jx - R * 0.03, jy - R * 0.03, R * 0.025, 0, Math.PI * 2); g.fill();
    }
    if (t === 'wrap') { g.fillStyle = h.color; g.beginPath(); g.ellipse(R * (0.8 - fx * 0.5), -R * 0.6, R * 0.16, R * 0.12, 0.4, 0, Math.PI * 2); g.fill(); g.lineWidth = LW * 0.7; g.stroke(); }
  } else if (t === 'kufi') {
    const shape = () => { g.moveTo(-R * 0.95, -R * 0.42); g.bezierCurveTo(-R * 0.95, -R * 1.12, R * 0.95, -R * 1.12, R * 0.95, -R * 0.42); g.quadraticCurveTo(0, -R * 0.32, -R * 0.95, -R * 0.42); g.closePath(); };
    g.save(); g.beginPath(); shape(); g.fillStyle = h.color; g.fill(); g.clip();
    g.strokeStyle = h.stripe || shade(h.color, -0.2); g.lineWidth = R * 0.06; g.beginPath(); g.moveTo(-R, -R * 0.5); g.quadraticCurveTo(0, -R * 0.4, R, -R * 0.5); g.stroke();
    for (let i = -3; i <= 3; i++) { g.beginPath(); g.moveTo(i * R * 0.25 + fx * R * 0.3, -R * 0.55); g.lineTo(i * R * 0.18 + fx * R * 0.3, -R * 0.95); g.lineWidth = R * 0.025; g.stroke(); }
    g.restore(); g.beginPath(); shape(); g.strokeStyle = INK; g.lineWidth = LW; g.stroke();
  } else if (t === 'crown') {
    drawCrown(g, R, LW, fx, 'front');
  } else if (t === 'hijab') {
    drawHijab(g, R, h, LW, ch, 'front');
  } else if (t === 'baker') {
    const shape = () => {
      g.moveTo(-R * 0.78, -R * 0.45); g.lineTo(-R * 0.82, -R * 0.95);
      g.arc(-R * 0.5, -R * 1.18, R * 0.42, Math.PI * 0.85, Math.PI * 1.75); g.arc(0, -R * 1.42, R * 0.48, Math.PI * 1.15, Math.PI * 1.85); g.arc(R * 0.5, -R * 1.18, R * 0.42, Math.PI * 1.25, Math.PI * 2.15);
      g.lineTo(R * 0.78, -R * 0.45); g.quadraticCurveTo(0, -R * 0.36, -R * 0.78, -R * 0.45); g.closePath();
    };
    g.save(); g.beginPath(); shape(); g.fillStyle = '#fdfbf6'; g.fill(); g.clip();
    g.strokeStyle = 'rgba(80,90,140,0.25)'; g.lineWidth = R * 0.05; g.beginPath(); g.moveTo(-R, -R * 0.95); g.quadraticCurveTo(0, -R * 0.88, R, -R * 0.95); g.stroke();
    for (const x of [-0.3, 0.25]) { g.beginPath(); g.moveTo(R * x, -R * 1.05); g.quadraticCurveTo(R * (x + 0.05), -R * 1.35, R * (x - 0.02), -R * 1.6); g.stroke(); }
    g.restore(); g.beginPath(); shape(); g.strokeStyle = INK; g.lineWidth = LW; g.stroke();
  } else if (t === 'helmet') {
    const shape = () => { g.moveTo(-R * 1.0, -R * 0.35); g.bezierCurveTo(-R * 1.0, -R * 1.25, R * 1.0, -R * 1.25, R * 1.0, -R * 0.35); g.quadraticCurveTo(0, -R * 0.25, -R * 1.0, -R * 0.35); g.closePath(); };
    outlineFill(g, LW, '#b8bcc8', 1, shape);
    g.fillStyle = '#b8bcc8'; g.beginPath(); g.moveTo(-R * 0.12, -R * 1.0); g.lineTo(0, -R * 1.55); g.lineTo(R * 0.12, -R * 1.0); g.closePath(); g.fill(); g.lineWidth = LW * 0.7; g.stroke();
    outlineFill(g, LW * 0.7, h.wrap || '#f2efe6', 2, () => { g.moveTo(-R * 1.02, -R * 0.4); g.quadraticCurveTo(0, -R * 0.28, R * 1.02, -R * 0.4); g.lineTo(R * 1.0, -R * 0.56); g.quadraticCurveTo(0, -R * 0.45, -R * 1.0, -R * 0.56); g.closePath(); });
    g.fillStyle = 'rgba(255,255,255,0.45)'; g.beginPath(); g.ellipse(-R * 0.4, -R * 0.85, R * 0.25, R * 0.08, -0.5, 0, Math.PI * 2); g.fill();
  } else if (t === 'hair') {
    const col = h.color || '#1e140c';
    const shape = () => {
      g.moveTo(-R * 1.02, -R * 0.05); g.bezierCurveTo(-R * 1.1, -R * 1.2, R * 1.1, -R * 1.2, R * 1.03, -R * 0.1);
      g.quadraticCurveTo(R * 0.7, -R * 0.55, R * (0.15 + fx * 0.3), -R * 0.62); g.quadraticCurveTo(-R * 0.5, -R * 0.45, -R * 0.85, -R * 0.2); g.closePath();
    };
    g.save(); g.beginPath(); shape(); g.fillStyle = col; g.fill(); g.clip();
    g.strokeStyle = shade(col, 0.15); g.lineWidth = R * 0.035;
    for (let i = -4; i <= 4; i++) { g.beginPath(); g.moveTo(R * (i * 0.2), -R * 1.05); g.quadraticCurveTo(R * (i * 0.22 + 0.1), -R * 0.8, R * (i * 0.2 + 0.15), -R * 0.5); g.stroke(); }
    g.restore(); g.beginPath(); shape(); g.strokeStyle = INK; g.lineWidth = LW; g.stroke();
  }
}

function drawCrown(g, R, LW, fx, layer) {
  if (layer === 'back') { // velvet cap rising above the band
    g.beginPath(); g.moveTo(-R * 0.82, -R * 0.75); g.bezierCurveTo(-R * 0.85, -R * 1.45, R * 0.85, -R * 1.45, R * 0.82, -R * 0.75); g.closePath();
    g.fillStyle = '#b8203a'; g.fill(); g.strokeStyle = INK; g.lineWidth = LW; g.stroke();
    g.fillStyle = 'rgba(255,255,255,0.18)'; g.beginPath(); g.ellipse(-R * 0.3, -R * 1.12, R * 0.25, R * 0.08, -0.3, 0, Math.PI * 2); g.fill();
    return;
  }
  const gold = '#f2b830', goldD = '#b07a14';
  // points with ball tips
  for (let i = -2; i <= 2; i++) {
    const x = (i * 0.38 + fx * 0.25) * R, bx = x, by = -R * 0.82;
    g.beginPath(); g.moveTo(bx - R * 0.15, by); g.lineTo(bx, by - R * 0.42); g.lineTo(bx + R * 0.15, by); g.closePath(); g.fillStyle = gold; g.fill(); g.strokeStyle = INK; g.lineWidth = LW * 0.75; g.stroke();
    g.beginPath(); g.arc(bx, by - R * 0.48, R * 0.075, 0, Math.PI * 2); g.fill(); g.stroke();
  }
  // the band
  const band = () => { g.moveTo(-R * 0.95, -R * 0.42); g.quadraticCurveTo(0, -R * 0.3, R * 0.95, -R * 0.42); g.lineTo(R * 0.92, -R * 0.86); g.quadraticCurveTo(0, -R * 0.76, -R * 0.92, -R * 0.86); g.closePath(); };
  g.save(); g.beginPath(); band(); g.fillStyle = gold; g.fill(); g.clip();
  g.fillStyle = goldD; g.fillRect(-R, -R * 0.5, R * 2, R * 0.08);
  g.fillStyle = 'rgba(255,255,255,0.35)'; g.fillRect(-R, -R * 0.82, R * 2, R * 0.05);
  g.restore(); g.beginPath(); band(); g.strokeStyle = INK; g.lineWidth = LW; g.stroke();
  for (let i = -2; i <= 2; i++) {
    const x = (i * 0.38 + fx * 0.3) * R, y = -R * 0.62;
    g.fillStyle = i % 2 ? '#1c9a52' : '#d4182a'; g.beginPath(); g.arc(x, y, R * 0.075, 0, Math.PI * 2); g.fill(); g.lineWidth = LW * 0.45; g.stroke();
    g.fillStyle = 'rgba(255,255,255,0.7)'; g.beginPath(); g.arc(x - R * 0.02, y - R * 0.025, R * 0.02, 0, Math.PI * 2); g.fill();
  }
}

function drawHijab(g, R, h, LW, ch, layer) {
  const col = h.color;
  if (layer === 'back') { // the drape behind the head and over the shoulders
    g.beginPath(); g.moveTo(-R * 1.12, -R * 0.1); g.bezierCurveTo(-R * 1.25, -R * 1.35, R * 1.25, -R * 1.35, R * 1.12, -R * 0.1);
    g.quadraticCurveTo(R * 1.25, R * 0.8, R * 0.95, R * 1.25); g.lineTo(-R * 0.95, R * 1.25); g.quadraticCurveTo(-R * 1.25, R * 0.8, -R * 1.12, -R * 0.1); g.closePath();
    g.fillStyle = col; g.fill(); g.strokeStyle = INK; g.lineWidth = LW; g.stroke();
    return;
  }
  // the front frame around the face (a ring with a face-shaped hole)
  g.save();
  g.beginPath(); g.ellipse(0, -R * 0.05, R * 1.13, R * 1.15, 0, 0, Math.PI * 2); g.ellipse(0, R * 0.03, R * 0.8, R * 0.84, 0, 0, Math.PI * 2, true);
  g.fillStyle = col; g.fill('evenodd');
  g.strokeStyle = INK; g.lineWidth = LW; g.beginPath(); g.ellipse(0, R * 0.03, R * 0.8, R * 0.84, 0, Math.PI * 1.05, Math.PI * 1.95); g.stroke();
  g.strokeStyle = shade(col, -0.15); g.lineWidth = R * 0.04; g.beginPath(); g.arc(0, -R * 0.1, R * 0.97, Math.PI * 1.15, Math.PI * 1.85); g.stroke();
  g.restore();
}

function drawLongBeard(g, R, col, LW, fx, back) {
  if (back) return;
  const x = fx * R;
  g.beginPath(); g.moveTo(x - R * 0.62, -R * 0.1); g.bezierCurveTo(x - R * 0.75, R * 0.9, x - R * 0.3, R * 1.6, x + R * 0.05, R * 1.85);
  g.bezierCurveTo(x + R * 0.3, R * 1.55, x + R * 0.75, R * 0.9, x + R * 0.62, -R * 0.1);
  g.quadraticCurveTo(x + R * 0.3, R * 0.25, x, R * 0.22); g.quadraticCurveTo(x - R * 0.3, R * 0.25, x - R * 0.62, -R * 0.1); g.closePath();
  g.fillStyle = col; g.fill(); g.strokeStyle = INK; g.lineWidth = LW; g.stroke();
  g.strokeStyle = 'rgba(120,120,150,0.35)'; g.lineWidth = R * 0.03;
  for (let i = -2; i <= 2; i++) { g.beginPath(); g.moveTo(x + i * R * 0.18, R * 0.35); g.quadraticCurveTo(x + i * R * 0.14, R * 0.9, x + i * R * 0.06, R * 1.4); g.stroke(); }
  // moustache over it
  g.fillStyle = col; g.beginPath(); g.ellipse(x - R * 0.14, R * 0.18, R * 0.18, R * 0.07, 0.2, 0, Math.PI * 2); g.ellipse(x + R * 0.14, R * 0.18, R * 0.18, R * 0.07, -0.2, 0, Math.PI * 2); g.fill(); g.lineWidth = LW * 0.5; g.strokeStyle = INK; g.stroke();
}
