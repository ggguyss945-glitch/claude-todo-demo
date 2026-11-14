// Animation helpers shared by the shots. Everything is a pure function of time:
// a frame never depends on the frame before it (chunks render out of order).
import * as THREE from 'three';
import { armIK, handToObject, headLook, POSES, blendPose, walkPose, walkAlong, setGrip, STAND_Y, SIT_Y, SEAT_H } from './chars.js';
import { clamp, lerp, prog, easeInOut, smooth, noise1 } from './util.js';

export const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
export const clock = { t: 0 };
const _q = new THREE.Quaternion(), _m = new THREE.Matrix4();

// ---- grips: userData.hold is the object's pose in the wrist frame
const gripCache = new WeakMap();
export function gripOf(obj, key = 'hold') {
  let c = gripCache.get(obj);
  if (!c) { c = {}; gripCache.set(obj, c); }
  if (!c[key]) c[key] = obj.userData[key].clone().invert();
  return c[key];
}
// drive arm L so the hand holds `obj` where the object currently is
export function holdObj(ch, L, obj, w = 1, opts = {}) {
  if (w <= 0) return 0;
  const err = handToObject(ch, L, obj, gripOf(obj, opts.key || 'hold'), { w, pole: opts.pole });
  if (Math.abs(err) > 0.01 && w > 0.99 && globalThis.__ikWarn) globalThis.__ikWarn(ch.name || ch.root.name, L, err);
  return err;
}
// place obj so that it sits in the hand of ch (hand pose from current FK/IK)
export function attachToHand(obj, ch, L, key = 'hold') {
  const wr = ch.J[L + 'Wrist'];
  wr.updateWorldMatrix(true, false);
  _m.copy(wr.matrixWorld).multiply(obj.userData[key]);
  setWorldMatrix(obj, _m);
}
export function setWorldMatrix(obj, m) {
  const parent = obj.parent;
  if (parent) { parent.updateWorldMatrix(true, false); const inv = parent.matrixWorld.clone().invert(); m = inv.multiply(m); }
  m.decompose(obj.position, obj.quaternion, obj.scale);
  obj.updateMatrixWorld(true);
}

// ---- writing: hand orientation for a right hand writing on a horizontal sheet,
// expressed in the character's heading frame, then the tip lands on `tipW`
export function writingHandQuat(ch, L = 'r', tilt = 0) {
  const sd = L === 'r' ? 1 : -1; // r hand: thumb towards the body midline (+x local)
  const f = V3(0.12 * sd, -0.62 + tilt, 0.78).normalize(); // fingers forward and down
  let n = V3(0.55 * sd, -0.82, -0.1); // palm faces down and in
  n.sub(f.clone().multiplyScalar(n.dot(f))).normalize();
  const y = f.clone().negate(), z = n, x = new THREE.Vector3().crossVectors(y, z);
  const q = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, y, z));
  ch.root.getWorldQuaternion(_q);
  return _q.clone().multiply(q);
}
// tool (pencil/pen) whose tip should touch tipW: solve wrist, move the tool, run IK
export function writeWith(ch, L, tool, tipW, w = 1, tilt = 0, pole = null) {
  const hq = writingHandQuat(ch, L, tilt);
  const hold = tool.userData[L === 'l' && tool.userData.holdL ? 'holdL' : 'hold'];
  const tipInTool = tool.userData.tip;
  const tipInWrist = tipInTool.clone().applyMatrix4(hold);
  const wrist = tipW.clone().sub(tipInWrist.applyQuaternion(hq));
  const handM = new THREE.Matrix4().compose(wrist, hq, V3(1, 1, 1));
  setWorldMatrix(tool, handM.clone().multiply(hold));
  const err = armIK(ch, L, wrist, { hand: hq, w, pole });
  setGrip(ch, L, 0.55);
  return err;
}

// ---- placement
export function placeChar(ch, x, z, heading, pose = POSES.stand) {
  ch.root.visible = true;
  ch.root.position.set(x, 0, z);
  ch.root.rotation.set(0, heading, 0);
  ch.setPose(pose);
  ch.idle(clock.t);
  ch.root.updateMatrixWorld(true);
}
// sitting pose adjusted to a seat of height seatH (pose hipsY is for SEAT_H * scale)
export function seated(base, ch, seatH) {
  const s = ch.scale || 1;
  return { ...base, hipsY: (base.hipsY ?? SIT_Y) + (seatH - SEAT_H * s) / s };
}
// hand orientation: fingers along `fwd` (character-local), palm facing `palm` (character-local)
export function handQuat(ch, fwd, palm) {
  const f = V3(...fwd).normalize();
  const n = V3(...palm); n.sub(f.clone().multiplyScalar(n.dot(f))).normalize();
  const y = f.clone().negate(), z = n, x = new THREE.Vector3().crossVectors(y, z);
  const q = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, y, z));
  ch.root.getWorldQuaternion(_q);
  return _q.clone().multiply(q);
}
// put the palm centre at world point p with orientation q (wrist is 0.07 back along the fingers)
export function palmAt(ch, L, p, q, w = 1, pole = null, grip = 0.2) {
  const s = ch.scale || 1;
  const wrist = p.clone().sub(V3(0, -0.06 * s, 0.012 * s).applyQuaternion(q));
  const e = armIK(ch, L, wrist, { hand: q, w, pole });
  setGrip(ch, L, grip);
  return e;
}
// world point from a character-local offset
export function local(ch, x, y, z) { ch.root.updateMatrixWorld(true); return V3(x, y, z).applyMatrix4(ch.root.matrixWorld); }
// walking along a curve between ta and tb; outside that range they stand at the ends
export function walkChar(ch, curve, t, ta, tb, base = POSES.stand, phase0 = 0) {
  const s = ch.scale || 1;
  const wk = walkAlong(curve, t, ta, tb, s, easeInOut, phase0);
  ch.root.visible = true;
  ch.root.position.set(wk.pos.x, 0, wk.pos.z);
  ch.root.rotation.set(0, wk.heading, 0);
  const amp = clamp(wk.amp, 0, 1.15);
  ch.setPose(amp > 0.01 ? blendPose(base, walkPose(wk.phase, amp, base), clamp(amp * 4)) : base);
  ch.idle(clock.t);
  ch.root.updateMatrixWorld(true);
  return wk;
}
export function curve(pts) { return new THREE.CatmullRomCurve3(pts.map((p) => V3(p[0], 0, p[1])), false, 'centripetal', 0.5); }

// pose keyframes: [[t, pose], ...] eased
export function poseAt(t, ks) {
  if (t <= ks[0][0]) return ks[0][1];
  for (let i = 0; i < ks.length - 1; i++) if (t <= ks[i + 1][0]) return blendPose(ks[i][1], ks[i + 1][1], easeInOut(prog(t, ks[i][0], ks[i + 1][0])));
  return ks[ks.length - 1][1];
}

export function look(ch, p, w = 1, eyes = 0.6) { ch.root.updateMatrixWorld(true); headLook(ch, p, w, eyes); }

// ---- camera keyframes {t, p:[..], l:[..], fov}
export function camKeys(t, ks, ease = easeInOut) {
  if (t <= ks[0].t) return { ...ks[0] };
  for (let i = 0; i < ks.length - 1; i++) {
    const a = ks[i], b = ks[i + 1];
    if (t <= b.t) {
      const e = (b.ease || ease)(prog(t, a.t, b.t));
      return { p: a.p.map((v, j) => lerp(v, b.p[j], e)), l: a.l.map((v, j) => lerp(v, b.l[j], e)), fov: lerp(a.fov || 40, b.fov || 40, e), roll: lerp(a.roll || 0, b.roll || 0, e) };
    }
  }
  return { ...ks[ks.length - 1] };
}
// subtle handheld drift added to a camera
export function handheld(c, t, amp = 1, seed = 1) {
  const k = 0.006 * amp;
  c.p = [c.p[0] + noise1(t * 0.7, seed) * k, c.p[1] + noise1(t * 0.6, seed + 3) * k, c.p[2] + noise1(t * 0.5, seed + 7) * k];
  c.l = [c.l[0] + noise1(t * 0.55, seed + 11) * k * 1.5, c.l[1] + noise1(t * 0.5, seed + 13) * k * 1.5, c.l[2]];
  return c;
}
// camera orbiting a target: yaw from +z towards +x, pitch up (degrees)
export function orbitCam(target, yawDeg, pitchDeg, dist, fov = 40, extra = {}) {
  const y = yawDeg * Math.PI / 180, p = pitchDeg * Math.PI / 180;
  return { t: extra.t, p: [target[0] + Math.sin(y) * Math.cos(p) * dist, target[1] + Math.sin(p) * dist, target[2] + Math.cos(y) * Math.cos(p) * dist], l: [...target], fov, ...extra };
}
// arms folded across the chest (both hands tucked at the opposite elbow)
export function crossArms(ch, w = 1) {
  const s = ch.scale || 1;
  const hy = 0.0;
  palmAt(ch, 'l', local(ch, -0.1 * s, (ch.J.hips.position.y / s + 0.33) * s, 0.15 * s), handQuat(ch, [-1, 0.1, 0.15], [0, 0, -1]), w, local(ch, 0.6, 0.9, -0.1), 0.6);
  palmAt(ch, 'r', local(ch, 0.1 * s, (ch.J.hips.position.y / s + 0.3) * s, 0.19 * s), handQuat(ch, [1, 0.1, 0.15], [0, 0.2, -1]), w, local(ch, -0.6, 0.9, -0.1), 0.6);
}
export function handsBehind(ch, w = 1) {
  const s = ch.scale || 1;
  const y = ch.J.hips.position.y + 0.02 * s;
  palmAt(ch, 'l', local(ch, 0.03, y, -0.19 * s), handQuat(ch, [-1, -0.3, 0], [0, 0, -1]), w, local(ch, 0.6, 1.0, 0.1), 0.4);
  palmAt(ch, 'r', local(ch, -0.03, y + 0.02, -0.21 * s), handQuat(ch, [1, -0.3, 0], [0, 0, -1]), w, local(ch, -0.6, 1.0, 0.1), 0.4);
}
export { clamp, lerp, prog, easeInOut, smooth };
