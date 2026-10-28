// Helpers for writing shots: cameras with a soft handheld drift, placing and moving characters,
// hands and held props, talking, cheering, riding a camel.
import * as THREE from 'three';
import { clamp, lerp, prog, smooth, easeInOut, easeOut, noise1, hash } from './util.js';
import { toRoot, lookAt } from './chars2d.js';

export const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
export { clamp, lerp, prog, smooth, easeInOut, easeOut, hash };

// camera keys: [[t, [px,py,pz], [lx,ly,lz], fov, ease?]]
// o: { ap, focus (point [x,y,z]), drift (m), seed, roll }
export function cam(keys, o = {}) {
  return (t) => {
    let a = keys[0], b = keys[0], k = 0;
    if (t >= keys[keys.length - 1][0]) { a = b = keys[keys.length - 1]; }
    else for (let i = 0; i < keys.length - 1; i++) if (t <= keys[i + 1][0]) { a = keys[i]; b = keys[i + 1]; k = (b[4] || easeInOut)(prog(t, a[0], b[0])); break; }
    const p = a[1].map((v, i) => lerp(v, b[1][i], k));
    const l = a[2].map((v, i) => lerp(v, b[2][i], k));
    const fov = lerp(a[3] || 40, b[3] || 40, k);
    const d = o.drift ?? 0.012, s = o.seed ?? 1;
    // slow, organic drift like a hand-held camera on a slider
    p[0] += noise1(t * 0.7, s) * d; p[1] += noise1(t * 0.6, s + 3) * d * 0.7; p[2] += noise1(t * 0.5, s + 5) * d;
    l[0] += noise1(t * 0.9, s + 7) * d * 0.8; l[1] += noise1(t * 0.8, s + 9) * d * 0.6;
    const f = o.focus ? Math.hypot(o.focus[0] - p[0], o.focus[1] - p[1], o.focus[2] - p[2]) : null;
    return { p, l, fov, ap: o.ap ?? 8, focus: typeof o.focusFn === 'function' ? o.focusFn(t, p) : f, roll: o.roll ? o.roll(t) : 0 };
  };
}

export function put(ch, p, yaw = 0, expr = 'neutral') {
  ch.root.visible = true;
  ch.root.position.copy(p);
  ch.root.rotation.set(0, yaw, 0);
  ch.state.expr = expr;
  ch.root.updateMatrixWorld(true);
  return ch;
}
export const yawTo = (from, to) => Math.atan2(to.x - from.x, to.z - from.z);
export function faceTo(ch, p) { ch.root.rotation.y = yawTo(ch.root.position, p); ch.root.updateMatrixWorld(true); }
export function exprAt(t, list) { let e = list[0][1]; for (const [tt, x] of list) if (t >= tt) e = x; return e; }

// hand target: world point -> root space; local: character-local point (scaled)
export function handW(ch, L, wp) { ch.pose.hands[L] = toRoot(ch, wp); }
export function handL(ch, L, x, y, z) { ch.pose.hands[L] = V(x, y, z).multiplyScalar(ch.s); }
export function handWorld(ch, L) { const p = V(); ch.arms[L].hand.getWorldPosition(p); return p; }
export function local(ch, x, y, z) { ch.root.updateMatrixWorld(true); return V(x * ch.s, y * ch.s, z * ch.s).applyMatrix4(ch.root.matrixWorld); }

// gentle idle life: breathing bob, a little sway and head drift, never frozen
export function idle(ch, t, amt = 1) {
  const s = hash(ch.name.length, ch.name.charCodeAt(1) || 3) * 10;
  ch.pose.bob += Math.sin(t * 2.1 + s) * 0.006 * amt * ch.s;
  ch.pose.side += Math.sin(t * 0.9 + s) * 0.012 * amt;
  ch.pose.headRoll += Math.sin(t * 0.7 + s * 2) * 0.03 * amt;
  ch.pose.headYaw += Math.sin(t * 0.5 + s) * 0.04 * amt;
}
export function look(ch, wp, w = 1) { lookAt(ch, wp, w); }

// walk a robed or legged character from a to b between t0 and t1 (eased), facing the way they go
export function walk(ch, a, b, t0, t1, t, o = {}) {
  const k = (o.ease || ((x) => x))(prog(t, t0, t1));
  const p = a.clone().lerp(b, k);
  ch.root.visible = true;
  ch.root.position.copy(p);
  ch.root.rotation.set(0, o.yaw ?? yawTo(a, b), 0);
  const moving = t > t0 && t < t1;
  const dist = a.distanceTo(b) * k;
  const stride = (o.stride || 0.42) * ch.s;
  const phase = dist / stride / 2;
  if (moving || o.always) {
    ch.pose.walk = { phase, stride: stride * 0.55, lift: 0.05 * ch.s };
    ch.pose.bob += Math.abs(Math.sin(phase * Math.PI * 2)) * 0.03 * ch.s;
    ch.pose.side += Math.sin(phase * Math.PI * 2) * 0.035;
    // arms swing opposite to the feet
    const sw = Math.sin(phase * Math.PI * 2) * 0.16 * ch.s;
    if (!o.keepHands) { handL(ch, 'l', 0.27, 0.7, 0.05 + sw); handL(ch, 'r', -0.27, 0.7, 0.05 - sw); }
  }
  ch.root.updateMatrixWorld(true);
  return p;
}
// cheering: both arms up, waving
export function cheer(ch, t, amt = 1) {
  const s = hash(ch.name.length, 7) * 6;
  const w = Math.sin(t * 7 + s) * 0.08;
  handL(ch, 'l', 0.33 + w, lerp(0.75, 1.72, amt), 0.12);
  handL(ch, 'r', -0.33 + w, lerp(0.75, 1.72 - Math.abs(w), amt), 0.12);
  ch.pose.bob += Math.abs(Math.sin(t * 7 + s)) * 0.035 * amt * ch.s;
}
// a hop for the kids
export function hop(ch, t, f = 2.4, h = 0.22, phase = 0) {
  const x = (t * f + phase) % 1;
  const y = Math.max(0, Math.sin(x * Math.PI)) * h * ch.s;
  ch.root.position.y += y;
  ch.pose.squash = y < 0.02 ? 0.92 + y * 2 : 1.04;
}
// shrug: shoulders up (squash), palms out
export function shrug(ch, k) {
  ch.pose.squash *= 1 + 0.06 * k;
  ch.pose.headRoll += 0.16 * k;
  handL(ch, 'l', lerp(0.27, 0.48, k), lerp(0.7, 1.08, k), lerp(0.05, 0.28, k));
  handL(ch, 'r', lerp(-0.27, -0.48, k), lerp(0.7, 1.08, k), lerp(0.05, 0.28, k));
}
// mouth flaps from the voice track
export function talk(ch, W, who, t) {
  const list = (W.mouth || {})[who] || [];
  for (const m of list) {
    if (t >= m.t0 && t <= m.t1) {
      const i = Math.floor((t - m.t0) * m.fps);
      ch.state.talk = m.v[Math.min(m.v.length - 1, Math.max(0, i))] || 0;
      // the head bobs a little on stressed syllables
      ch.pose.headPitch += -ch.state.talk * 0.05;
      return;
    }
  }
}
// sit a character on a camel's seat (robe hidden in the hump); returns the rider root position
export function ride(ch, camel, yawOff = 0) {
  camel.root.updateMatrixWorld(true);
  const p = V(0, 1.42 + camel.body.position.y, -0.05).applyMatrix4(camel.root.matrixWorld);
  ch.root.visible = true;
  ch.root.position.copy(p);
  ch.root.rotation.set(0, camel.root.rotation.y + yawOff, 0);
  ch.pose.lean += camel.body.rotation.x;
  ch.root.updateMatrixWorld(true);
  return p;
}
// place a prop so a point on it sits at a character's hand
export function handPt(ch, L) {
  ch.root.updateMatrixWorld(true);
  const tgt = ch.pose.hands[L] || ch.arms[L].target;
  return tgt.clone().applyMatrix4(ch.root.matrixWorld);
}
export function holdProp(prop, ch, L, off = V(), rot = null) {
  const p = handPt(ch, L);
  prop.visible = true;
  prop.position.copy(p).add(off);
  if (rot) prop.rotation.set(...rot);
  prop.updateMatrixWorld(true);
}
// caravan helper: a camel walking along +x or -x at speed v
export function camelWalk(cm, p, yaw, t, v, phase0 = 0) {
  cm.root.visible = true;
  cm.root.position.copy(p);
  cm.root.rotation.set(0, yaw, 0);
  cm.pose.walk = { phase: (t * v) / 2.4 + phase0, stride: 0.95 };
  cm.update(t);
  cm.root.updateMatrixWorld(true);
}
