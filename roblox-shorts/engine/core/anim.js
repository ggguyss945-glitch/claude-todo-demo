// Animation toolkit: easing, keyframe tracks, analytic springs, seeded noise wobble, holds/steps.
// Everything here is a pure function of time t (seconds from the shot start). No hidden state that depends on
// which frames were rendered before, so interleaved workers and stills mode give identical results.
import * as THREE from 'three';
import { noise1, fbm1, hash32 } from './random.js';

export const clamp = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
export const lerp = (a, b, t) => a + (b - a) * t;
export const invLerp = (a, b, x) => (b === a ? 0 : (x - a) / (b - a));
export const remap = (x, a0, a1, b0, b1, doClamp = true) => { let u = invLerp(a0, a1, x); if (doClamp) u = clamp(u); return lerp(b0, b1, u); };
export const smoothstep = (a, b, x) => { const u = clamp(invLerp(a, b, x)); return u * u * (3 - 2 * u); };
export const deg = (d) => (d * Math.PI) / 180;
export const fract = (x) => x - Math.floor(x);

// ---------------- easing ----------------
const PI = Math.PI;
const c1 = 1.70158, c2 = c1 * 1.525, c3 = c1 + 1, c4 = (2 * PI) / 3, c5 = (2 * PI) / 4.5;
function bounceOut(x) { const n = 7.5625, d = 2.75; if (x < 1 / d) return n * x * x; if (x < 2 / d) return n * (x -= 1.5 / d) * x + 0.75; if (x < 2.5 / d) return n * (x -= 2.25 / d) * x + 0.9375; return n * (x -= 2.625 / d) * x + 0.984375; }
export const ease = {
  linear: (x) => x,
  step: (x) => (x < 1 ? 0 : 1), // hold the previous value until the key, then snap
  hold: (x) => (x < 1 ? 0 : 1),
  stepStart: (x) => (x > 0 ? 1 : 0), // snap immediately at the previous key
  smooth: (x) => x * x * (3 - 2 * x),
  smoother: (x) => x * x * x * (x * (x * 6 - 15) + 10),
  inQuad: (x) => x * x, outQuad: (x) => 1 - (1 - x) * (1 - x), inOutQuad: (x) => (x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2),
  inCubic: (x) => x * x * x, outCubic: (x) => 1 - Math.pow(1 - x, 3), inOutCubic: (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
  inQuart: (x) => x ** 4, outQuart: (x) => 1 - Math.pow(1 - x, 4), inOutQuart: (x) => (x < 0.5 ? 8 * x ** 4 : 1 - Math.pow(-2 * x + 2, 4) / 2),
  inQuint: (x) => x ** 5, outQuint: (x) => 1 - Math.pow(1 - x, 5), inOutQuint: (x) => (x < 0.5 ? 16 * x ** 5 : 1 - Math.pow(-2 * x + 2, 5) / 2),
  inSine: (x) => 1 - Math.cos((x * PI) / 2), outSine: (x) => Math.sin((x * PI) / 2), inOutSine: (x) => -(Math.cos(PI * x) - 1) / 2,
  inExpo: (x) => (x === 0 ? 0 : Math.pow(2, 10 * x - 10)), outExpo: (x) => (x === 1 ? 1 : 1 - Math.pow(2, -10 * x)),
  inOutExpo: (x) => (x === 0 ? 0 : x === 1 ? 1 : x < 0.5 ? Math.pow(2, 20 * x - 10) / 2 : (2 - Math.pow(2, -20 * x + 10)) / 2),
  inCirc: (x) => 1 - Math.sqrt(1 - x * x), outCirc: (x) => Math.sqrt(1 - Math.pow(x - 1, 2)),
  inOutCirc: (x) => (x < 0.5 ? (1 - Math.sqrt(1 - Math.pow(2 * x, 2))) / 2 : (Math.sqrt(1 - Math.pow(-2 * x + 2, 2)) + 1) / 2),
  inBack: (x) => c3 * x * x * x - c1 * x * x, outBack: (x) => 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2),
  inOutBack: (x) => (x < 0.5 ? (Math.pow(2 * x, 2) * ((c2 + 1) * 2 * x - c2)) / 2 : (Math.pow(2 * x - 2, 2) * ((c2 + 1) * (x * 2 - 2) + c2) + 2) / 2),
  inElastic: (x) => (x === 0 ? 0 : x === 1 ? 1 : -Math.pow(2, 10 * x - 10) * Math.sin((x * 10 - 10.75) * c4)),
  outElastic: (x) => (x === 0 ? 0 : x === 1 ? 1 : Math.pow(2, -10 * x) * Math.sin((x * 10 - 0.75) * c4) + 1),
  inOutElastic: (x) => (x === 0 ? 0 : x === 1 ? 1 : x < 0.5 ? -(Math.pow(2, 20 * x - 10) * Math.sin((20 * x - 11.125) * c5)) / 2 : (Math.pow(2, -20 * x + 10) * Math.sin((20 * x - 11.125) * c5)) / 2 + 1),
  inBounce: (x) => 1 - bounceOut(1 - x), outBounce: bounceOut, inOutBounce: (x) => (x < 0.5 ? (1 - bounceOut(1 - 2 * x)) / 2 : (1 + bounceOut(2 * x - 1)) / 2),
};
// CSS-style cubic-bezier(x1,y1,x2,y2) easing.
export function cubicBezier(x1, y1, x2, y2) {
  const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx, cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
  const sx = (t) => ((ax * t + bx) * t + cx) * t, sy = (t) => ((ay * t + by) * t + cy) * t, dx = (t) => (3 * ax * t + 2 * bx) * t + cx;
  return (x) => {
    if (x <= 0) return 0; if (x >= 1) return 1;
    let t = x; for (let i = 0; i < 8; i++) { const e = sx(t) - x; const d = dx(t); if (Math.abs(e) < 1e-6 || Math.abs(d) < 1e-6) break; t -= e / d; }
    t = clamp(t); return sy(t);
  };
}
// Resolve an easing spec: name | function | [x1,y1,x2,y2] | undefined (linear).
export function getEase(e) {
  if (!e) return ease.linear;
  if (typeof e === 'function') return e;
  if (Array.isArray(e)) return cubicBezier(...e);
  const f = ease[e]; if (!f) throw new Error('unknown easing ' + e); return f;
}
// Eased progress 0..1 of t inside [t0,t1].
export const seg = (t, t0, t1, e) => getEase(e)(clamp(invLerp(t0, t1, t)));
// Shorthand: tween a number from a to b over [t0,t1].
export const tween = (t, t0, t1, a, b, e) => lerp(a, b, seg(t, t0, t1, e));
// Envelope: 0 -> 1 over attack, hold, 1 -> 0 over release (all seconds), starting at t0.
export function pulse(t, t0, attack = 0.1, hold = 0, release = 0.3, e = 'smooth') {
  const u = t - t0; if (u <= 0) return 0;
  if (u < attack) return getEase(e)(u / attack);
  if (u < attack + hold) return 1;
  if (u < attack + hold + release) return 1 - getEase(e)((u - attack - hold) / release);
  return 0;
}
export const loop = (t, period) => fract(t / period);
export const pingpong = (t, period) => { const u = fract(t / (2 * period)) * 2; return u < 1 ? u : 2 - u; };
// Quantize time to a step (e.g. 1/12 s for "on twos" stop-motion feel).
export const quantize = (t, step) => Math.floor(t / step + 1e-9) * step;

// ---------------- value kinds ----------------
const _c1 = new THREE.Color(), _c2 = new THREE.Color();
function kindOf(v) {
  if (typeof v === 'number') return 'num';
  if (typeof v === 'boolean') return 'bool';
  if (typeof v === 'string') return 'color';
  if (Array.isArray(v)) return 'arr';
  if (v.isColor) return 'color';
  if (v.isQuaternion) return 'quat';
  if (v.isEuler) return 'euler';
  if (v.isVector2 || v.isVector3 || v.isVector4) return 'vec';
  if (typeof v === 'object') return 'obj';
  throw new Error('unsupported key value');
}
function prep(v, kind) {
  if (kind === 'color') return typeof v === 'string' || typeof v === 'number' ? new THREE.Color(v) : v.clone();
  if (kind === 'euler') return new THREE.Quaternion().setFromEuler(v);
  return v;
}
function mixVal(kind, a, b, u, out) {
  switch (kind) {
    case 'num': return a + (b - a) * u;
    case 'bool': return u < 1 ? a : b;
    case 'arr': { const o = out || new Array(a.length); for (let i = 0; i < a.length; i++) o[i] = a[i] + (b[i] - a[i]) * u; return o; }
    case 'vec': return (out || a.clone()).copy(a).lerp(b, u);
    case 'color': return (out || new THREE.Color()).copy(a).lerp(b, u);
    case 'quat': case 'euler': return (out || new THREE.Quaternion()).copy(a).slerp(b, u);
    case 'obj': { const o = out || {}; for (const k in a) { const x = a[k], y = b[k] ?? x; o[k] = typeof x === 'number' ? x + (y - x) * u : u < 1 ? x : y; } return o; }
  }
}
function copyVal(kind, a, out) {
  switch (kind) {
    case 'num': case 'bool': return a;
    case 'arr': return out ? (a.forEach((x, i) => (out[i] = x)), out) : a.slice();
    case 'obj': return out ? Object.assign(out, a) : { ...a };
    default: return out ? out.copy(a) : a.clone();
  }
}
// Catmull-Rom (centripetal-ish uniform) for num/arr/vec.
function cr(p0, p1, p2, p3, u) { const u2 = u * u, u3 = u2 * u; return 0.5 * (2 * p1 + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u3); }

// ---------------- keyframe track ----------------
// keys: [[t, value, ease?], ...] or [{t, v, ease}]. The ease of a key shapes the segment ARRIVING at that key
// ("go to value by time t with ease"). Use 'step'/'hold' to snap at that key (Roblox pose-to-pose pops).
// opts.interp: 'linear' (default, eased per key) | 'catmull' (smooth path through all keys; num/arr/vec only).
// Values: number, boolean, [numbers], Vector2/3/4, Color or '#hex', Quaternion (slerp), Euler (slerp via quaternion),
// plain object of numbers (poses: {armL: .3, armR: -1}).
export class Track {
  constructor(keys, opts = {}) {
    this.keys = keys.map((k) => (Array.isArray(k) ? { t: k[0], v: k[1], ease: k[2] } : { t: k.t, v: k.v ?? k.value, ease: k.ease }));
    this.keys.sort((a, b) => a.t - b.t);
    this.kind = kindOf(this.keys[0].v);
    this._order = this.kind === 'euler' ? this.keys[0].v.order : 'XYZ';
    for (const k of this.keys) { k.v = prep(k.v, this.kind); k.e = getEase(k.ease); }
    this.interp = opts.interp || 'linear';
    this.out = this.kind === 'euler' ? new THREE.Euler() : null;
    this._q = this.kind === 'euler' ? new THREE.Quaternion() : null;
  }
  get start() { return this.keys[0].t; }
  get end() { return this.keys[this.keys.length - 1].t; }
  // at(t, out?) -> value. `out` (Vector3, Color, Quaternion, array, object) is filled and returned when given.
  at(t, out) {
    if (this.kind === 'euler') { const q = this._at(t, this._q); return (out || this.out).setFromQuaternion(q, this._order); }
    return this._at(t, out);
  }
  _at(t, out) {
    const K = this.keys, n = K.length, kind = this.kind === 'euler' ? 'quat' : this.kind;
    if (t <= K[0].t) return copyVal(kind, K[0].v, out);
    if (t >= K[n - 1].t) return copyVal(kind, K[n - 1].v, out);
    let i = 1; while (i < n - 1 && t >= K[i].t) i++;
    const a = K[i - 1], b = K[i]; const u = b.e(clamp((t - a.t) / Math.max(1e-9, b.t - a.t)));
    if (this.interp === 'catmull' && (kind === 'num' || kind === 'arr' || kind === 'vec')) {
      const p0 = K[Math.max(0, i - 2)].v, p3 = K[Math.min(n - 1, i + 1)].v;
      if (kind === 'num') return cr(p0, a.v, b.v, p3, u);
      if (kind === 'arr') { const o = out || new Array(a.v.length); for (let j = 0; j < a.v.length; j++) o[j] = cr(p0[j], a.v[j], b.v[j], p3[j], u); return o; }
      const o = out || a.v.clone(); o.x = cr(p0.x, a.v.x, b.v.x, p3.x, u); o.y = cr(p0.y, a.v.y, b.v.y, p3.y, u);
      if ('z' in o) o.z = cr(p0.z, a.v.z, b.v.z, p3.z, u); if ('w' in o) o.w = cr(p0.w, a.v.w, b.v.w, p3.w, u); return o;
    }
    return mixVal(kind, a.v, b.v, u, out);
  }
}
export const track = (keys, opts) => new Track(keys, opts);
// All keys snap (holds). Same as track with ease 'step' on every key.
export const steps = (keys) => new Track(keys.map((k) => (Array.isArray(k) ? [k[0], k[1], 'step'] : { ...k, ease: 'step' })));

// Evaluate "anything animatable": constant, Track, function(t), or a keys array.
export function value(spec, t, out) {
  if (spec == null) return spec;
  if (spec instanceof Track) return spec.at(t, out);
  if (typeof spec === 'function') return spec(t, out);
  if (Array.isArray(spec) && spec.length && Array.isArray(spec[0])) { if (!spec._track) spec._track = new Track(spec); return spec._track.at(t, out); }
  return spec;
}

// Pose-to-pose with optional short blend (seconds). poses: [[t, {joint: angle, ...}], ...].
// blend = 0 gives Roblox-style single-frame snaps; 0.08-0.15 gives a quick snappy in-between.
export function poseSeq(t, poses, blend = 0, e = 'outCubic', out) {
  if (!poses._k || poses._b !== blend) {
    const keys = [];
    poses.forEach(([pt, pose], i) => {
      if (i === 0 || blend <= 0) keys.push([pt, pose, i === 0 ? undefined : 'step']);
      else { keys.push([pt, poses[i - 1][1], 'step']); keys.push([pt + blend, pose, e]); }
    });
    // collapse duplicate-time keys so blend windows are well formed
    poses._k = new Track(keys); poses._b = blend;
  }
  return poses._k.at(t, out);
}

// ---------------- springs ----------------
// Normalised step response of a damped harmonic oscillator: 0 at u=0, -> 1. freq in Hz, zeta = damping ratio
// (0.3 bouncy, 0.6 snappy, 1 critical, >1 sluggish).
export function springStep(u, freq = 2, zeta = 0.5) {
  if (u <= 0) return 0;
  const w = 2 * Math.PI * freq;
  if (zeta < 1) { const wd = w * Math.sqrt(1 - zeta * zeta); return 1 - Math.exp(-zeta * w * u) * (Math.cos(wd * u) + (zeta / Math.sqrt(1 - zeta * zeta)) * Math.sin(wd * u)); }
  if (zeta === 1) return 1 - Math.exp(-w * u) * (1 + w * u);
  const r = Math.sqrt(zeta * zeta - 1), s1 = -w * (zeta - r), s2 = -w * (zeta + r);
  return 1 + (s2 * Math.exp(s1 * u) - s1 * Math.exp(s2 * u)) / (s1 - s2);
}
// Spring from `from` to `to` starting at t0 (numbers).
export const spring = (t, t0, from, to, freq = 2, zeta = 0.5) => from + (to - from) * springStep(t - t0, freq, zeta);
// A spring that chases a piecewise-constant target given as keys [[t, value], ...]. Exact (superposition of step
// responses), stateless. Works for numbers, arrays and Vector3s. Great for overshooting "pops" and settles.
export function springKeys(t, keys, freq = 2, zeta = 0.5, out) {
  const k0 = keys[0][1];
  if (typeof k0 === 'number') { let v = k0; for (let i = 1; i < keys.length; i++) v += (keys[i][1] - keys[i - 1][1]) * springStep(t - keys[i][0], freq, zeta); return v; }
  if (Array.isArray(k0)) { const o = out || k0.slice(); for (let j = 0; j < k0.length; j++) { let v = k0[j]; for (let i = 1; i < keys.length; i++) v += (keys[i][1][j] - keys[i - 1][1][j]) * springStep(t - keys[i][0], freq, zeta); o[j] = v; } return o; }
  const o = out || k0.clone(); o.copy(k0);
  for (let i = 1; i < keys.length; i++) { const s = springStep(t - keys[i][0], freq, zeta); o.x += (keys[i][1].x - keys[i - 1][1].x) * s; o.y += (keys[i][1].y - keys[i - 1][1].y) * s; if ('z' in o) o.z += (keys[i][1].z - keys[i - 1][1].z) * s; }
  return o;
}
// Spring that follows an arbitrary function target(t) -> number. Integrated deterministically from t=0 at fixed
// dt (semi-implicit Euler), so the result only depends on t. Cost O(t/dt); fine for shots of a few seconds.
export function springFollow(t, target, freq = 2, zeta = 0.5, dt = 1 / 240) {
  const w = 2 * Math.PI * freq; let x = target(0), v = 0; const n = Math.floor(t / dt);
  for (let i = 0; i < n; i++) { const a = w * w * (target(i * dt) - x) - 2 * zeta * w * v; v += a * dt; x += v * dt; }
  const r = t - n * dt; if (r > 0) { const a = w * w * (target(n * dt) - x) - 2 * zeta * w * v; v += a * r; x += v * r; }
  return x;
}
// Damped sine "jiggle" after an impact at t0: amp * e^(-decay*u) * sin(2*pi*freq*u).
export const jiggle = (t, t0, amp = 1, freq = 4, decay = 6) => { const u = t - t0; return u <= 0 ? 0 : amp * Math.exp(-decay * u) * Math.sin(2 * Math.PI * freq * u); };

// ---------------- seeded noise for motion ----------------
// seed may be a number or a string label.
const sd = (s) => (typeof s === 'number' ? s : hash32(s) & 0xffff);
// Smooth random wobble in [-amp, amp] at about `freq` Hz.
export const wobble = (t, seed = 0, freq = 1, amp = 1, oct = 2) => fbm1(t * freq, sd(seed), oct) * amp;
export function wobble3(t, seed = 0, freq = 1, amp = 1, out = new THREE.Vector3(), oct = 2) {
  const s = sd(seed); return out.set(fbm1(t * freq, s, oct) * amp, fbm1(t * freq + 17.3, s + 101, oct) * amp, fbm1(t * freq + 41.7, s + 211, oct) * amp);
}
export const bob = (t, freq = 1, amp = 1, phase = 0) => Math.sin(2 * Math.PI * (freq * t + phase)) * amp;
// Blink helper: returns 0..1 eyelid closure. Blinks at seeded times every ~interval s, each `dur` long.
export function blink(t, seed = 0, interval = 3.2, dur = 0.14) {
  const s = sd(seed); const k = Math.floor(t / interval);
  for (let i = k - 1; i <= k; i++) {
    const tb = i * interval + interval * (0.2 + 0.6 * ((noise1(i * 7.13 + 0.5, s) + 1) / 2));
    const u = (t - tb) / dur; if (u >= 0 && u <= 1) return Math.sin(u * Math.PI);
  }
  return 0;
}

// ---------------- simple helpers for objects ----------------
// Apply a {pos, rot, scale} pose to an Object3D, each entry being anything `value()` accepts.
export function applyTransform(obj, t, { pos, rot, scale, quat } = {}) {
  if (pos) { const p = value(pos, t); if (Array.isArray(p)) obj.position.set(p[0], p[1], p[2]); else obj.position.copy(p); }
  if (rot) { const r = value(rot, t); if (Array.isArray(r)) obj.rotation.set(r[0], r[1], r[2]); else obj.rotation.copy(r); }
  if (quat) obj.quaternion.copy(value(quat, t));
  if (scale != null) { const s = value(scale, t); if (typeof s === 'number') obj.scale.setScalar(s); else if (Array.isArray(s)) obj.scale.set(s[0], s[1], s[2]); else obj.scale.copy(s); }
}
