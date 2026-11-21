// Cartoon people in the hand-drawn web-short style: a big white ball head with a tiny drawn face,
// a bean-shaped body or a long robe, stick-thin black arms and legs, ball hands, thick outlines.
// Root sits at the feet, facing +z. Everything is rigid geometry except the hose limbs.
import * as THREE from 'three';
import { toon, outline, mk, gold, hullMaterial, OUTLINE } from './toon.js';
import { paintFace, headGeometry } from './faces.js';
import { canvas, toTex } from './tex.js';
import { clamp, lerp, hash, noise1 } from './util.js';
import * as HW from './headwear.js';

const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const INK = '#141010';
const HEAD = '#f7f3ec';
const inkMat = new THREE.MeshStandardMaterial({ color: '#1c1a20', roughness: 0.6 });
const handMat = new THREE.MeshStandardMaterial({ color: '#1c1a20', roughness: 0.35 });
// 'flat 3D': heads and bodies are squashed front-to-back like thick cut-outs
const FLAT_HEAD = 0.6, FLAT_BODY = 0.72;

// a quadratic-bezier tube whose vertices are rewritten in place each frame
export class Hose {
  constructor(radius, mat, segs = 16, radial = 7, taper = 0) {
    this.r = radius; this.segs = segs; this.radial = radial; this.taper = taper;
    const n = (segs + 1) * (radial + 1);
    const geo = new THREE.BufferGeometry();
    this.pos = new Float32Array(n * 3); this.nrm = new Float32Array(n * 3);
    geo.setAttribute('position', new THREE.BufferAttribute(this.pos, 3));
    geo.setAttribute('normal', new THREE.BufferAttribute(this.nrm, 3));
    const idx = [];
    for (let i = 0; i < segs; i++) for (let j = 0; j < radial; j++) {
      const a = i * (radial + 1) + j, b = a + radial + 1;
      idx.push(a, b, a + 1, b, b + 1, a + 1);
    }
    geo.setIndex(idx);
    this.mesh = new THREE.Mesh(geo, mat);
    this.mesh.castShadow = true; this.mesh.frustumCulled = false;
  }
  update(p0, p1, p2) {
    const { segs, radial } = this;
    let prevN = null;
    const P = V(), T = V(), N = V(), B = V(), tmp = V();
    for (let i = 0; i <= segs; i++) {
      const t = i / segs, it = 1 - t;
      P.set(0, 0, 0).addScaledVector(p0, it * it).addScaledVector(p1, 2 * it * t).addScaledVector(p2, t * t);
      T.set(0, 0, 0).addScaledVector(tmp.copy(p1).sub(p0), 2 * it).addScaledVector(V().copy(p2).sub(p1), 2 * t);
      if (T.lengthSq() < 1e-10) T.set(0, -1, 0);
      T.normalize();
      if (!prevN) { N.set(0, 0, 1); if (Math.abs(N.dot(T)) > 0.9) N.set(1, 0, 0); N.sub(tmp.copy(T).multiplyScalar(N.dot(T))).normalize(); }
      else { N.copy(prevN).sub(tmp.copy(T).multiplyScalar(prevN.dot(T))).normalize(); }
      prevN = N.clone();
      B.crossVectors(T, N);
      const r = this.r * (1 - this.taper * t);
      for (let j = 0; j <= radial; j++) {
        const a = (j / radial) * Math.PI * 2;
        const nx = N.x * Math.cos(a) + B.x * Math.sin(a), ny = N.y * Math.cos(a) + B.y * Math.sin(a), nz = N.z * Math.cos(a) + B.z * Math.sin(a);
        const k = (i * (radial + 1) + j) * 3;
        this.pos[k] = P.x + nx * r; this.pos[k + 1] = P.y + ny * r; this.pos[k + 2] = P.z + nz * r;
        this.nrm[k] = nx; this.nrm[k + 1] = ny; this.nrm[k + 2] = nz;
      }
    }
    this.mesh.geometry.attributes.position.needsUpdate = true;
    this.mesh.geometry.attributes.normal.needsUpdate = true;
  }
}

// Clothes are flat colour with a few drawn details (collar, belt, trim, buttons, apron), like a
// hand-drawn cartoon. u wraps round the body (front at 0.5), v runs from the hem (0) to the top (1).
function clothTexture(o, H) {
  const [c, g] = canvas(1024, 1024);
  const S = 1024;
  const X = (u) => u * S, Y = (v) => (1 - v) * S;
  const vAt = (y) => (y - H.y0) / (H.y1 - H.y0);
  g.fillStyle = o.color; g.fillRect(0, 0, S, S);
  const ink = 'rgba(20,14,10,0.85)';
  if (o.pattern === 'stripes') { g.fillStyle = o.stripe; for (let x = 0; x < S; x += 64) g.fillRect(x + 20, 0, 18, S); }
  if (o.pattern === 'pinstripe') { g.fillStyle = o.stripe; for (let x = 0; x < S; x += 40) g.fillRect(x, 0, 7, S); }
  if (o.pattern === 'patched') {
    const r = (k) => hash(k, o.seed || 1);
    for (let i = 0; i < 6; i++) {
      const x = 200 + r(i) * 600, y = 200 + r(i + 9) * 600, w = 90 + r(i + 3) * 60, h = 80 + r(i + 5) * 60;
      g.fillStyle = ['#8a6a48', '#6e5a40', '#a08060'][i % 3]; g.fillRect(x, y, w, h);
      g.strokeStyle = ink; g.lineWidth = 4; g.setLineDash([12, 9]); g.strokeRect(x + 7, y + 7, w - 14, h - 14); g.setLineDash([]);
    }
  }
  if (o.apron) {
    const top = vAt(H.y1 - 0.04);
    g.fillStyle = o.apron; g.beginPath(); g.roundRect(X(0.36), Y(top), X(0.28), Y(vAt(H.y0 + 0.08)) - Y(top), 30); g.fill();
    g.strokeStyle = ink; g.lineWidth = 6; g.stroke();
    g.beginPath(); g.roundRect(X(0.44), Y(vAt(H.belt - 0.04)), X(0.12), 90, 10); g.stroke();
  }
  if (o.trim) { // a front band from hem to collar, with buttons or jewels
    g.fillStyle = o.trim; g.fillRect(X(0.5) - 34, 0, 68, S);
    g.strokeStyle = ink; g.lineWidth = 5; g.beginPath(); g.moveTo(X(0.5) - 34, 0); g.lineTo(X(0.5) - 34, S); g.moveTo(X(0.5) + 34, 0); g.lineTo(X(0.5) + 34, S); g.stroke();
    if (o.trimDots) { g.fillStyle = o.trimDots; for (let y = 60; y < S; y += 74) { g.beginPath(); g.arc(X(0.5), y, 13, 0, Math.PI * 2); g.fill(); } }
  }
  if (o.hem) { g.fillStyle = o.hem; g.fillRect(0, Y(vAt(H.y0 + 0.07)), S, S); g.strokeStyle = ink; g.lineWidth = 6; g.beginPath(); g.moveTo(0, Y(vAt(H.y0 + 0.07))); g.lineTo(S, Y(vAt(H.y0 + 0.07))); g.stroke(); }
  if (o.belt) {
    const a = Y(vAt(H.belt + 0.035)), b = Y(vAt(H.belt - 0.035));
    g.fillStyle = o.belt; g.fillRect(0, a, S, b - a);
    g.strokeStyle = ink; g.lineWidth = 6; g.beginPath(); g.moveTo(0, a); g.lineTo(S, a); g.moveTo(0, b); g.lineTo(S, b); g.stroke();
  }
  if (o.collar) { // crossed lapels meeting on the chest (an X / V collar)
    const top = Y(1), meet = Y(vAt(H.y1 - 0.24));
    g.fillStyle = o.collar; g.strokeStyle = ink; g.lineWidth = 6;
    for (const sd of [-1, 1]) {
      g.beginPath(); g.moveTo(X(0.5 + sd * 0.11), top); g.lineTo(X(0.5 + sd * 0.05), top); g.lineTo(X(0.5 - sd * 0.012), meet); g.lineTo(X(0.5 + sd * 0.035), meet + 30); g.closePath(); g.fill(); g.stroke();
    }
  }
  if (o.buttons) { g.fillStyle = o.buttons; g.strokeStyle = ink; g.lineWidth = 4; for (let i = 0; i < 4; i++) { const y = Y(vAt(H.y1 - 0.12 - i * 0.11)); g.beginPath(); g.arc(X(0.5), y, 15, 0, Math.PI * 2); g.fill(); g.stroke(); } }
  if (o.sashBand) { const y = Y(vAt(H.belt)); g.fillStyle = o.sashBand; g.save(); g.translate(X(0.5), y); g.rotate(-0.5); g.fillRect(-300, -30, 600, 60); g.restore(); }
  return toTex(c, { aniso: 8 });
}

// body profiles (radius, height) for s = 1; the head sits on top with no neck
const PROFILES = {
  // long robe to the ankles, like a kaftan or galabeya; the belt sits at 0.78
  // (the king): a rounded bean of a chest over a skirt that flares to the ankles
  robe: { pts: [[0, 0.08], [0.205, 0.08], [0.215, 0.11], [0.2, 0.35], [0.182, 0.6], [0.168, 0.8], [0.176, 0.95], [0.172, 1.08], [0.155, 1.2], [0.11, 1.28], [0.045, 1.32], [0, 1.325]], belt: 0.8, hip: 0.16 },
  // long dress, narrow at the shoulders and wide at the hem
  dress: { pts: [[0, 0.06], [0.235, 0.06], [0.24, 0.09], [0.215, 0.4], [0.188, 0.7], [0.165, 0.95], [0.15, 1.12], [0.125, 1.22], [0.08, 1.29], [0.03, 1.32], [0, 1.325]], belt: 0.8, hip: 0.14 },
  // the classic: a bean-shaped body, widest low down, on long stick legs
  bean: { pts: [[0, 0.7], [0.1, 0.7], [0.165, 0.728], [0.198, 0.79], [0.208, 0.9], [0.203, 1.0], [0.19, 1.1], [0.165, 1.2], [0.12, 1.28], [0.05, 1.32], [0, 1.325]], belt: 0.86, hip: 0.76 },
};

export function makeToon(def) {
  const s = def.scale || 1, gth = def.girth || 1;
  const kind = def.body === 'tunic' ? 'bean' : (def.body || 'bean');
  const P = PROFILES[kind];
  const ch = { def, s, kind, root: new THREE.Group(), name: def.name };
  ch.root.name = def.name;
  const body = new THREE.Group(); ch.root.add(body); ch.body = body;
  const y0 = P.pts[0][1], y1 = P.pts[P.pts.length - 1][1];
  const prof = P.pts.map(([r, y]) => new THREE.Vector2(r * s * (y < 1.05 ? gth : lerp(gth, 1, (y - 1.05) / 0.27)), y * s));
  const lathe = new THREE.LatheGeometry(prof, 48);
  lathe.rotateY(Math.PI); // seam at the back
  // v by height, so the drawn details land where they belong
  const pos = lathe.getAttribute('position'), uv = lathe.getAttribute('uv');
  for (let i = 0; i < pos.count; i++) uv.setY(i, (pos.getY(i) / s - y0) / (y1 - y0));
  const tex = clothTexture({ color: def.color, pattern: def.pattern, stripe: def.stripe, trim: def.trim, trimDots: def.trimDots, apron: def.apron, seed: def.seed,
    belt: def.belt, collar: def.collar, buttons: def.buttons, hem: def.hem, sashBand: def.sashBand }, { y0, y1, belt: P.belt });
  const robeMat = toon('#ffffff', { map: tex, lift: 0.22, rough: 0.85 });
  const torso = mk(lathe, robeMat, body, { outline: 10 });
  torso.scale.z = FLAT_BODY;
  ch.torso = torso;
  if (def.necklace) {
    mk(new THREE.TorusGeometry(0.11 * s, 0.018 * s, 8, 28), gold({ glow: 0.35 }), torso, { pos: [0, 1.22 * s, 0.035 * s], rot: [Math.PI / 2 + 0.5, 0, 0], outline: 3 });
    if (def.medallion) mk(new THREE.CylinderGeometry(0.045 * s, 0.045 * s, 0.014 * s, 20), gold({ glow: 0.4 }), torso, { pos: [0, 1.11 * s, 0.155 * s], rot: [Math.PI / 2 - 0.3, 0, 0], outline: 3 });
  }
  // head: a big round ball resting on the body
  const neck = new THREE.Group(); neck.position.set(0, 1.28 * s, 0); body.add(neck); ch.neck = neck;
  const R = (def.head || 0.285) * s; ch.R = R;
  const headG = new THREE.Group(); headG.position.set(0, R * 0.7, 0); headG.scale.z = FLAT_HEAD; neck.add(headG); ch.head = headG;
  ch.faceDef = { id: def.name, skin: def.skin || HEAD, hair: def.hairColor || INK, beard: def.beard, beardColor: def.beardColor, moustache: def.moustache,
    eyeY: def.eyeY, eyeSpread: def.eyeSpread, browW: def.browW, mouthW: def.mouthW, blush: def.blushBase, glasses: def.glasses };
  const face0 = paintFace(ch.faceDef, { expr: 'neutral' }, def.faceRes || 768);
  // glossy: the sky and sun leave a soft sheen across the forehead
  ch.faceMat = new THREE.MeshStandardMaterial({ map: face0.tex, roughness: 0.42, envMapIntensity: 0.55, emissive: new THREE.Color(0xffffff), emissiveMap: face0.tex, emissiveIntensity: 0.32 });
  const headMesh = mk(headGeometry(R, 48, (def.seed || 1) + def.name.length * 7.3), ch.faceMat, headG, { outline: 13 });
  ch.headMesh = headMesh;
  if (def.hat) HW.build(def.hat, headG, R, def);
  if (def.beard3d) HW.longBeard(headG, R, def.beard3d);
  // stick arms with ball hands
  const armR = 0.0118 * s, handR = 0.04 * s;
  ch.arms = {};
  for (const L of ['l', 'r']) {
    const sd = L === 'l' ? 1 : -1;
    const hose = new Hose(armR, inkMat, 14, 6);
    body.add(hose.mesh);
    const hand = mk(new THREE.SphereGeometry(handR, 16, 12), handMat, ch.root, { outline: false });
    ch.arms[L] = { sd, hose, hand, shoulder: V(sd * 0.15 * s * Math.min(gth, 1.2), 1.18 * s, 0.0), target: V(sd * 0.25 * s, 0.84 * s, 0.06 * s), bend: 1 };
  }
  // stick legs with small black feet (only the ankles show under a long robe)
  ch.legs = {};
  for (const L of ['l', 'r']) {
    const sd = L === 'l' ? 1 : -1;
    const shoe = mk(new THREE.SphereGeometry(0.04 * s, 14, 10), def.shoes ? toon(def.shoes, { lift: 0.1 }) : handMat, ch.root, { scale: [0.95, 0.6, 1.65], outline: def.shoes ? 2.5 : false });
    const hose = new Hose(0.0125 * s, inkMat, 10, 6); ch.root.add(hose.mesh);
    ch.legs[L] = { sd, shoe, hose, hip: V(sd * 0.08 * s, P.hip * s, 0), foot: V(sd * 0.1 * s, 0.024 * s, 0.03 * s) };
  }
  // hand-drawn outlines on everything the character wears
  ch.root.traverse((o) => { if (o.userData.isHull) o.material = hullMaterial(o.material.userData.width ?? o.material.uniforms.uWidth.value, OUTLINE, true); });
  ch.state = { expr: 'neutral', look: [0, 0], talk: 0, blink: false };
  ch.pose = defaultPose();
  ch.update = (t) => updateToon(ch, t);
  return ch;
}

export function defaultPose() {
  return { lean: 0, side: 0, yaw: 0, bob: 0, squash: 1, headYaw: 0, headPitch: 0, headRoll: 0, hands: {}, feet: {}, walk: null, bendL: 1, bendR: 1 };
}

const _m = new THREE.Matrix4();
export function updateToon(ch, t) {
  const p = ch.pose, s = ch.s;
  ch.body.rotation.set(p.lean, p.yaw, p.side);
  ch.body.position.y = p.bob;
  ch.body.scale.set(1 / Math.sqrt(p.squash), p.squash, 1 / Math.sqrt(p.squash));
  ch.neck.rotation.set(p.headPitch, p.headYaw, p.headRoll, 'YXZ');
  ch.root.updateMatrixWorld(true);
  const inv = _m.copy(ch.body.matrixWorld).invert();
  // arms: hand targets are in root space; the hose is built in body space
  for (const L of ['l', 'r']) {
    const a = ch.arms[L];
    const tgt = (p.hands[L] || a.target).clone();
    const sh = a.shoulder.clone();
    const shRoot = sh.clone().applyMatrix4(ch.body.matrix);
    const d = tgt.clone().sub(shRoot);
    const maxLen = 0.58 * s;
    if (d.length() > maxLen) tgt.copy(shRoot).add(d.setLength(maxLen));
    a.hand.position.copy(tgt);
    const tB = tgt.clone().applyMatrix4(ch.root.matrixWorld).applyMatrix4(inv);
    const mid = sh.clone().add(tB).multiplyScalar(0.5);
    const len = sh.distanceTo(tB);
    const slack = Math.max(0, 0.58 * s - len);
    const bend = (L === 'l' ? p.bendL : p.bendR) ?? 1;
    // elbows bow outwards and slightly back, more when the arm is folded
    const out = V(a.sd, -0.35, -0.45).normalize().multiplyScalar(slack * 0.7 * bend + 0.02 * s);
    a.hose.update(sh, mid.add(out), tB);
  }
  // legs / feet
  const w = p.walk; // {phase, stride, lift}
  for (const L of ['l', 'r']) {
    const lg = ch.legs[L];
    const f = (p.feet[L] || lg.foot).clone();
    if (w) {
      const ph = w.phase * Math.PI * 2 + (L === 'l' ? 0 : Math.PI);
      f.z += Math.sin(ph) * w.stride * 0.5;
      f.y += Math.max(0, Math.cos(ph)) * w.lift;
    }
    lg.shoe.position.copy(f);
    lg.shoe.rotation.set(w ? -Math.max(0, Math.cos(w.phase * Math.PI * 2 + (L === 'l' ? 0 : Math.PI))) * 0.3 : 0, 0, 0);
    {
      const hip = lg.hip.clone().applyMatrix4(ch.body.matrix);
      const top = f.clone().add(V(0, 0.01 * s, -0.025 * s));
      // knees bow a little forward when the leg is shorter than its rest length
      const len = hip.distanceTo(top), rest = (lg.hip.y - lg.foot.y);
      const mid = hip.clone().add(top).multiplyScalar(0.5).add(V(0, 0, 0.02 * s + Math.max(0, rest - len) * 0.8));
      lg.hose.update(hip, mid, top);
    }
  }
  const st = ch.state;
  const blink = st.blink || (!st.noBlink && isBlink(ch, t));
  const fv = paintFace(ch.faceDef, { expr: st.expr, look: st.look, talk: st.talk, blink, extra: st.extra }, ch.def.faceRes || 768);
  if (ch.faceMat.map !== fv.tex) { ch.faceMat.map = fv.tex; ch.faceMat.emissiveMap = fv.tex; ch.faceMat.needsUpdate = true; }
}

export function isBlink(ch, t) {
  const seed = hash(ch.name.length, ch.name.charCodeAt(0));
  const per = 2.8 + seed * 1.6;
  return ((t + seed * 7.3) % per) < 0.11;
}

// world-space point of a character-local offset
export function at(ch, x, y, z) { ch.root.updateMatrixWorld(true); return V(x, y, z).applyMatrix4(ch.root.matrixWorld); }
// convert a world point into root space (for hand targets)
export function toRoot(ch, wp) { ch.root.updateMatrixWorld(true); return wp.clone().applyMatrix4(_m.copy(ch.root.matrixWorld).invert()); }
// head look toward a world point (yaw/pitch into the pose), eyes follow
export function lookAt(ch, wp, w = 1) {
  const hp = V(); ch.head.getWorldPosition(hp);
  const d = toRoot(ch, wp).sub(toRoot(ch, hp));
  const yaw = Math.atan2(d.x, d.z) - ch.pose.yaw;
  const pitch = -Math.atan2(d.y, Math.hypot(d.x, d.z));
  ch.pose.headYaw = clamp(yaw, -0.9, 0.9) * w * 0.75;
  ch.pose.headPitch = clamp(pitch, -0.5, 0.5) * w * 0.6;
  ch.state.look = [clamp(yaw * 1.2, -1, 1) * w, clamp(-pitch * 1.4, -1, 1) * w];
}
