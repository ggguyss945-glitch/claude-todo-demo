// Round-head cartoon people: big sphere head with a drawn face, a robe or tunic body, rubber-hose
// arms and legs (smooth curves, so there are no joints to break), blob hands, and outlines.
// Root sits at the feet, facing +z. Everything is rigid geometry except the hose limbs.
import * as THREE from 'three';
import { toon, outline, mk, gold } from './toon.js';
import { paintFace, headGeometry } from './faces.js';
import { canvas, toTex } from './tex.js';
import { clamp, lerp, hash, noise1 } from './util.js';
import * as HW from './headwear.js';

const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const INK = '#141010';
const inkMat = new THREE.MeshStandardMaterial({ color: INK, roughness: 0.7 });

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

// cloth pattern for robes and tunics: u wraps round (front at 0.5), v runs hem (0) to neck (1)
function robeTexture(o) {
  const [c, g] = canvas(512, 512);
  g.fillStyle = o.color; g.fillRect(0, 0, 512, 512);
  const r = (s) => hash(s, o.seed || 1);
  if (o.pattern === 'stripes') {
    g.fillStyle = o.stripe; for (let x = 0; x < 512; x += 32) g.fillRect(x, 0, 11, 512);
  } else if (o.pattern === 'mudcloth') {
    g.strokeStyle = o.stripe; g.fillStyle = o.stripe; g.lineWidth = 5;
    for (let y = 30; y < 512; y += 70) {
      for (let x = 0; x < 512; x += 32) {
        const k = (x / 32 + y / 70) % 3;
        if (k === 0) { g.beginPath(); g.moveTo(x + 4, y - 12); g.lineTo(x + 16, y + 12); g.lineTo(x + 28, y - 12); g.stroke(); }
        else if (k === 1) { g.beginPath(); g.arc(x + 16, y, 6, 0, Math.PI * 2); g.fill(); }
        else { g.fillRect(x + 6, y - 2, 20, 5); }
      }
      g.fillRect(0, y + 24, 512, 4);
    }
  } else if (o.pattern === 'checks') {
    g.fillStyle = o.stripe; for (let x = 0; x < 512; x += 40) for (let y = 0; y < 512; y += 40) if (((x + y) / 40) % 2 === 0) g.fillRect(x, y, 40, 40);
  } else if (o.pattern === 'patched') {
    for (let i = 0; i < 9; i++) {
      g.fillStyle = ['#8a6a48', '#6e5a40', '#9a7c58', '#5c4a36'][i % 4];
      const x = r(i) * 470, y = r(i + 20) * 470, w = 40 + r(i + 40) * 40, h = 40 + r(i + 60) * 40;
      g.fillRect(x, y, w, h); g.strokeStyle = '#2a1e14'; g.lineWidth = 3; g.setLineDash([7, 6]); g.strokeRect(x + 4, y + 4, w - 8, h - 8); g.setLineDash([]);
    }
  }
  // soft woven noise
  for (let i = 0; i < 700; i++) { g.fillStyle = `rgba(${r(i) > 0.5 ? '255,255,255' : '0,0,0'},0.018)`; g.fillRect(r(i + 3) * 512, r(i + 7) * 512, 6, 6); }
  if (o.trim) { // front opening band and hem band
    g.fillStyle = o.trim; g.fillRect(256 - 18, 0, 36, 512); g.fillRect(0, 0, 512, 34);
    if (o.trimDots) { g.fillStyle = o.trimDots; for (let y = 20; y < 512; y += 30) { g.beginPath(); g.arc(256, y, 6, 0, Math.PI * 2); g.fill(); } }
  }
  if (o.apron) { g.fillStyle = o.apron; g.fillRect(256 - 120, 0, 240, 360); g.fillStyle = 'rgba(0,0,0,0.06)'; g.fillRect(256 - 120, 340, 240, 20); }
  if (o.sashBand) { g.fillStyle = o.sashBand; g.fillRect(0, 300, 512, 40); }
  return toTex(c, { aniso: 4 });
}

const PROFILES = {
  robe: [[0.265, 0.0], [0.275, 0.05], [0.262, 0.25], [0.25, 0.5], [0.242, 0.75], [0.236, 0.95], [0.222, 1.08], [0.19, 1.17], [0.12, 1.23], [0.06, 1.26]],
  tunic: [[0.0, 0.5], [0.24, 0.5], [0.255, 0.56], [0.25, 0.75], [0.235, 0.95], [0.2, 1.1], [0.17, 1.18], [0.11, 1.24], [0.06, 1.26]],
};

export function makeToon(def) {
  const s = def.scale || 1, gth = def.girth || 1;
  const kind = def.body || 'robe';
  const ch = { def, s, kind, root: new THREE.Group(), name: def.name };
  ch.root.name = def.name;
  const body = new THREE.Group(); ch.root.add(body); ch.body = body;
  const prof = PROFILES[kind].map(([r, y]) => new THREE.Vector2(r * s * (y < 1.0 ? gth : lerp(gth, 1, (y - 1.0) / 0.26)), y * s));
  const lathe = new THREE.LatheGeometry(prof, 36);
  lathe.rotateY(Math.PI); // seam at the back
  const robeMat = toon('#ffffff', { map: robeTexture({ color: def.color, pattern: def.pattern, stripe: def.stripe, trim: def.trim, trimDots: def.trimDots, apron: def.apron, seed: def.seed }), lift: 0.08 });
  const torso = mk(lathe, robeMat, body, { outline: 7.5 });
  ch.torso = torso;
  // collar / necklace / sash
  if (def.necklace) {
    const nk = mk(new THREE.TorusGeometry(0.13 * s, 0.022 * s, 8, 28), gold({ glow: 0.25 }), body, { pos: [0, 1.2 * s, 0.035 * s], rot: [Math.PI / 2 + 0.35, 0, 0], outline: 2.4 });
    if (def.medallion) mk(new THREE.CylinderGeometry(0.05 * s, 0.05 * s, 0.015 * s, 20), gold(), body, { pos: [0, 1.08 * s, 0.205 * s], rot: [Math.PI / 2 - 0.25, 0, 0], outline: 2.4 });
  }
  if (def.sash) mk(new THREE.TorusGeometry(0.236 * s * gth, 0.032 * s, 8, 32), toon(def.sash, { lift: 0.06 }), body, { pos: [0, 0.82 * s, 0], rot: [Math.PI / 2, 0, 0], outline: 2.6 });
  // head on a neck pivot
  const neck = new THREE.Group(); neck.position.set(0, 1.24 * s, 0); body.add(neck); ch.neck = neck;
  const R = (def.head || 0.27) * s; ch.R = R;
  const headG = new THREE.Group(); headG.position.set(0, R * 0.82, 0); neck.add(headG); ch.head = headG;
  ch.faceDef = { id: def.name, skin: def.skin || '#f4ece0', hair: def.hairColor || INK, beard: def.beard, beardColor: def.beardColor, moustache: def.moustache,
    eyeY: def.eyeY, eyeSpread: def.eyeSpread, browW: def.browW, mouthW: def.mouthW, blush: def.blushBase };
  const face0 = paintFace(ch.faceDef, { expr: 'neutral' }, def.faceRes || 512);
  ch.faceMat = new THREE.MeshStandardMaterial({ map: face0.tex, roughness: 0.82, emissive: new THREE.Color(0xffffff), emissiveMap: face0.tex, emissiveIntensity: 0.06 });
  const headMesh = mk(headGeometry(R), ch.faceMat, headG, { outline: 9.0 });
  ch.headMesh = headMesh;
  if (def.hat) HW.build(def.hat, headG, R, def);
  if (def.beard3d) HW.longBeard(headG, R, def.beard3d);
  // limbs
  const armR = 0.019 * s, handR = 0.046 * s;
  ch.arms = {};
  for (const L of ['l', 'r']) {
    const sd = L === 'l' ? 1 : -1;
    const hose = new Hose(armR, inkMat, 14, 6);
    body.add(hose.mesh);
    const hand = mk(new THREE.SphereGeometry(handR, 16, 12), inkMat, ch.root, { outline: false });
    hand.castShadow = true;
    const sleeve = def.sleeve ? mk(new THREE.SphereGeometry(armR * 2.4, 12, 8), toon(def.sleeve), body, { outline: 2 }) : null;
    ch.arms[L] = { sd, hose, hand, sleeve, shoulder: V(sd * 0.19 * s * Math.min(gth, 1.15), 1.12 * s, 0.0), target: V(sd * 0.27 * s, 0.7 * s, 0.05 * s), bend: 1 };
  }
  ch.legs = {};
  for (const L of ['l', 'r']) {
    const sd = L === 'l' ? 1 : -1;
    const shoe = mk(new THREE.SphereGeometry(0.06 * s, 14, 10), def.shoes ? toon(def.shoes) : inkMat, ch.root, { scale: [0.95, 0.62, 1.55], outline: def.shoes ? 2.2 : false });
    let hose = null;
    if (kind === 'tunic') { hose = new Hose(0.022 * s, inkMat, 10, 6); ch.root.add(hose.mesh); }
    ch.legs[L] = { sd, shoe, hose, hip: V(sd * 0.085 * s, 0.56 * s, 0), foot: V(sd * 0.085 * s, 0.03 * s, kind === 'robe' ? 0.2 * s : 0.03 * s) };
  }
  // props held in hands are parented here by the shots
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
    const maxLen = 0.6 * s;
    if (d.length() > maxLen) tgt.copy(shRoot).add(d.setLength(maxLen));
    a.hand.position.copy(tgt);
    const tB = tgt.clone().applyMatrix4(ch.root.matrixWorld).applyMatrix4(inv);
    const mid = sh.clone().add(tB).multiplyScalar(0.5);
    const len = sh.distanceTo(tB);
    const slack = Math.max(0, 0.6 * s - len);
    const bend = (L === 'l' ? p.bendL : p.bendR) ?? 1;
    // elbows bow outwards and slightly back, more when the arm is folded
    const out = V(a.sd, -0.35, -0.45).normalize().multiplyScalar(slack * 0.7 * bend + 0.02 * s);
    a.hose.update(sh, mid.add(out), tB);
    if (a.sleeve) a.sleeve.position.copy(sh);
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
    if (lg.hose) {
      const hip = lg.hip.clone().applyMatrix4(ch.body.matrix);
      const top = f.clone().add(V(0, 0.04 * s, -0.02 * s));
      const mid = hip.clone().add(top).multiplyScalar(0.5).add(V(0, 0, 0.05 * s));
      lg.hose.update(hip, mid, top);
    }
  }
  const st = ch.state;
  const blink = st.blink || (!st.noBlink && isBlink(ch, t));
  const fv = paintFace(ch.faceDef, { expr: st.expr, look: st.look, talk: st.talk, blink, extra: st.extra }, ch.def.faceRes || 512);
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
