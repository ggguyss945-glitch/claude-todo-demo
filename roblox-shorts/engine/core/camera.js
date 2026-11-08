// Per-shot camera: keyframed position / target / FOV / roll, composable moves (push, pull, orbit, truck, crane,
// dolly, pan, tilt, follow), handheld noise, decaying shake (3D and pixel-exact 2D), and DOF focus tracking.
// All evaluation is a pure function of shot time t.
import * as THREE from 'three';
import { value, getEase, clamp, deg, Track } from './anim.js';
import { fbm1 } from './random.js';

const V = (v) => (v == null ? null : Array.isArray(v) && typeof v[0] === 'number' ? new THREE.Vector3(v[0], v[1], v[2]) : v);
// Normalise a position/target spec: [x,y,z] | Vector3 | keys [[t,[x,y,z]|Vector3,ease], ...] | Track | fn(t)
function vecSpec(s) {
  if (s == null) return null;
  if (typeof s === 'function' || s instanceof Track) return s;
  if (Array.isArray(s) && Array.isArray(s[0])) return s.map((k) => [k[0], V(k[1]), k[2]]);
  return V(s);
}
const worldPos = (o, out) => (o.isObject3D ? o.getWorldPosition(out) : out.copy(V(o)));

export class ShotCamera {
  constructor(width = 1080, height = 1920) {
    this.width = width; this.height = height;
    this.cam = new THREE.PerspectiveCamera(50, width / height, 0.05, 1000);
    this.reset();
    this._p = new THREE.Vector3(); this._tg = new THREE.Vector3(); this._tmp = new THREE.Vector3(); this._tmp2 = new THREE.Vector3();
  }
  // Called by the engine at every shot start.
  reset(duration = 1) {
    this.duration = duration;
    this.spec = { pos: new THREE.Vector3(0, 1.6, 6), target: new THREE.Vector3(0, 1.2, 0), fov: 50, roll: 0, near: 0.05, far: 1000, up: new THREE.Vector3(0, 1, 0) };
    this.moves = [];
    this.focusSpec = null; // object | point | number | fn
    this.focusDistance = 5;
    this.state = { pos: new THREE.Vector3(), target: new THREE.Vector3(), fov: 50, roll: 0, rot: new THREE.Euler(0, 0, 0, 'YXZ'), px: [0, 0], scale: 1 };
    this.cam.clearViewOffset(); this.cam.filmOffset = 0;
    return this;
  }
  // set({pos, target, fov, roll, near, far}). Each may be a constant, a keys array, a Track or a fn(t).
  // fov is VERTICAL degrees (three.js convention). Roblox default is 70.
  set(o = {}) {
    if (o.pos !== undefined) this.spec.pos = vecSpec(o.pos);
    if (o.target !== undefined) this.spec.target = vecSpec(o.target);
    if (o.fov !== undefined) this.spec.fov = o.fov;
    if (o.roll !== undefined) this.spec.roll = o.roll;
    if (o.near !== undefined) this.spec.near = o.near;
    if (o.far !== undefined) this.spec.far = o.far;
    return this;
  }
  // Convenience: place the camera at `distance` from target, at yaw/pitch degrees (yaw 0 = looking down -Z).
  frame({ target = [0, 1, 0], distance = 5, yaw = 0, pitch = 0, fov } = {}) {
    const tg = V(target).clone(); const y = deg(yaw), p = deg(pitch);
    const pos = tg.clone().add(new THREE.Vector3(Math.sin(y) * Math.cos(p), Math.sin(p), Math.cos(y) * Math.cos(p)).multiplyScalar(distance));
    return this.set({ pos, target: tg, ...(fov ? { fov } : {}) });
  }
  // DOF focus: Object3D (tracked every frame), [x,y,z], a distance in metres, or fn(t) -> any of these.
  focus(spec) { this.focusSpec = spec; return this; }
  add(move) { this.moves.push(move); return this; }

  // ---- moves (window defaults to the whole shot; t0/t1 in shot seconds; ease defaults to linear) ----
  // Push-in: image scale grows from 1 to 1+amount. mode 'zoom' (FOV, no parallax: the reference house style)
  // or 'dolly' (camera travels toward the target so the subject at target distance scales the same).
  push(amount = 0.19, { mode = 'zoom', t0 = 0, t1, ease } = {}) { return this.add({ type: 'push', amount, mode, t0, t1, ease }); }
  // Pull-back: scale from 1 down to 1/(1+amount).
  pull(amount = 0.19, opts = {}) { return this.add({ type: 'push', amount, inverse: true, mode: opts.mode || 'zoom', t0: opts.t0 || 0, t1: opts.t1, ease: opts.ease }); }
  orbit(degrees = 20, { axis = 'y', t0 = 0, t1, ease } = {}) { return this.add({ type: 'orbit', degrees, axis, t0, t1, ease }); }
  truck(dx = 1, { t0 = 0, t1, ease } = {}) { return this.add({ type: 'shift', local: [dx, 0, 0], t0, t1, ease }); }
  crane(dy = 1, { t0 = 0, t1, ease, keepTarget = false } = {}) { return this.add({ type: 'shift', local: [0, dy, 0], world: true, keepTarget, t0, t1, ease }); }
  dolly(dz = 1, { t0 = 0, t1, ease } = {}) { return this.add({ type: 'dolly', dz, t0, t1, ease }); }
  pan(degrees = 10, { t0 = 0, t1, ease } = {}) { return this.add({ type: 'aim', yaw: degrees, pitch: 0, t0, t1, ease }); }
  tilt(degrees = 10, { t0 = 0, t1, ease } = {}) { return this.add({ type: 'aim', yaw: 0, pitch: degrees, t0, t1, ease }); }
  rollBy(degrees = 10, { t0 = 0, t1, ease } = {}) { return this.add({ type: 'roll', degrees, t0, t1, ease }); }
  zoomFov(toFov, { t0 = 0, t1, ease } = {}) { return this.add({ type: 'fov', toFov, t0, t1, ease }); }
  // Target follows an object (plus offset); `lag` (0..1) blends between the keyed target and the object.
  follow(obj, { offset = [0, 0, 0], amount = 1, moveCamera = false } = {}) { return this.add({ type: 'follow', obj, offset: V(offset), amount, moveCamera }); }
  // Continuous handheld drift: rotation amplitude in degrees, position amplitude in metres, freq in Hz.
  handheld({ rot = 0.35, pos = 0.01, freq = 0.6, seed = 7 } = {}) { return this.add({ type: 'handheld', rot, pos, freq, seed }); }
  // Decaying shake starting at t0: rotational (deg) + positional (m) + optional 2D pixel jitter (px at 1080 wide).
  // decay = seconds to fall to ~5%. freq = jitter speed in Hz (the references: 10-20 Hz, decays in ~0.5 s).
  shake({ t0 = 0, dur = 0.6, rot = 1.2, pos = 0.02, px = 0, freq = 14, seed = 3, decay = 'exp' } = {}) { return this.add({ type: 'shake', t0, dur, rot, pos, px, freq, seed, decay }); }
  // Custom move: fn(state, t, cam) may modify state.pos/target/fov/roll/rot/px.
  custom(fn) { return this.add({ type: 'custom', fn }); }

  _u(m, t) { const t1 = m.t1 ?? this.duration; return getEase(m.ease)(clamp((t - m.t0) / Math.max(1e-6, t1 - m.t0))); }

  // Evaluate at shot time t and write the THREE camera. Idempotent; the engine calls it after update().
  apply(t) {
    const s = this.state, sp = this.spec, cam = this.cam;
    const p = value(sp.pos, t, s.pos); if (p !== s.pos) s.pos.copy(p);
    const tg = value(sp.target, t, s.target); if (tg !== s.target) s.target.copy(tg);
    s.fov = value(sp.fov, t); s.roll = value(sp.roll, t) || 0; s.rot.set(0, 0, 0); s.px[0] = 0; s.px[1] = 0; s.scale = 1;
    for (const m of this.moves) this._applyMove(m, t);
    if (s.scale !== 1) s.fov = (2 * Math.atan(Math.tan(deg(s.fov) / 2) / s.scale) * 180) / Math.PI;
    cam.position.copy(s.pos); cam.up.copy(sp.up); cam.lookAt(s.target);
    if (s.roll) cam.rotateZ(deg(s.roll));
    if (s.rot.x || s.rot.y || s.rot.z) { cam.rotateY(deg(s.rot.y)); cam.rotateX(deg(s.rot.x)); cam.rotateZ(deg(s.rot.z)); }
    cam.fov = s.fov; cam.near = value(sp.near, t); cam.far = value(sp.far, t); cam.aspect = this.width / this.height;
    if (s.px[0] || s.px[1]) { const k = this.width / 1080; cam.setViewOffset(this.width, this.height, -s.px[0] * k, -s.px[1] * k, this.width, this.height); }
    else cam.clearViewOffset();
    cam.updateProjectionMatrix(); cam.updateMatrixWorld(true);
    // focus distance = view-space depth of the focus point
    const f = typeof this.focusSpec === 'function' ? this.focusSpec(t) : this.focusSpec;
    if (f == null) this.focusDistance = s.pos.distanceTo(s.target);
    else if (typeof f === 'number') this.focusDistance = f;
    else { worldPos(f, this._tmp); this._tmp.applyMatrix4(cam.matrixWorldInverse); this.focusDistance = Math.max(0.01, -this._tmp.z); }
    return cam;
  }

  _applyMove(m, t) {
    const s = this.state;
    switch (m.type) {
      case 'push': {
        const u = this._u(m, t); const k = 1 + m.amount * u; const scale = m.inverse ? 1 / k : k;
        if (m.mode === 'zoom') s.scale *= scale;
        else { const d = this._tmp.subVectors(s.target, s.pos); const L = d.length(); s.pos.addScaledVector(d.normalize(), L - L / scale); }
        break;
      }
      case 'orbit': {
        const u = this._u(m, t); const a = deg(m.degrees) * u; const off = this._tmp.subVectors(s.pos, s.target);
        const ax = m.axis === 'x' ? new THREE.Vector3(1, 0, 0) : m.axis === 'z' ? new THREE.Vector3(0, 0, 1) : new THREE.Vector3(0, 1, 0);
        if (m.axis === 'pitch') { const right = this._tmp2.crossVectors(off, this.spec.up).normalize(); off.applyAxisAngle(right, a); }
        else off.applyAxisAngle(ax, a);
        s.pos.copy(s.target).add(off); break;
      }
      case 'shift': {
        const u = this._u(m, t); const fwd = this._tmp.subVectors(s.target, s.pos).normalize();
        const right = this._tmp2.crossVectors(fwd, this.spec.up).normalize(); const up = new THREE.Vector3().crossVectors(right, fwd);
        const d = new THREE.Vector3().addScaledVector(right, m.local[0] * u).addScaledVector(m.world ? this.spec.up : up, m.local[1] * u).addScaledVector(fwd, m.local[2] * u);
        s.pos.add(d); if (!m.keepTarget) s.target.add(d); break;
      }
      case 'dolly': { const u = this._u(m, t); const fwd = this._tmp.subVectors(s.target, s.pos).normalize(); s.pos.addScaledVector(fwd, m.dz * u); break; }
      case 'aim': {
        const u = this._u(m, t); const d = this._tmp.subVectors(s.target, s.pos);
        if (m.yaw) d.applyAxisAngle(this.spec.up, -deg(m.yaw) * u);
        if (m.pitch) { const right = this._tmp2.crossVectors(d, this.spec.up).normalize(); d.applyAxisAngle(right, deg(m.pitch) * u); }
        s.target.copy(s.pos).add(d); break;
      }
      case 'roll': s.roll += m.degrees * this._u(m, t); break;
      case 'fov': { const u = this._u(m, t); s.fov = s.fov + (m.toFov - s.fov) * u; break; }
      case 'follow': {
        worldPos(m.obj, this._tmp).add(m.offset);
        if (m.moveCamera) { const d = this._tmp2.subVectors(this._tmp, s.target).multiplyScalar(m.amount); s.pos.add(d); s.target.add(d); }
        else s.target.lerp(this._tmp, m.amount);
        break;
      }
      case 'handheld': {
        const f = m.freq, sd = m.seed;
        s.rot.x += fbm1(t * f, sd, 3) * m.rot; s.rot.y += fbm1(t * f + 31.7, sd + 1, 3) * m.rot; s.rot.z += fbm1(t * f * 0.7 + 7.1, sd + 2, 3) * m.rot * 0.5;
        s.pos.x += fbm1(t * f * 0.8 + 3.3, sd + 3, 2) * m.pos; s.pos.y += fbm1(t * f * 0.8 + 9.9, sd + 4, 2) * m.pos; break;
      }
      case 'shake': {
        const u = t - m.t0; if (u < 0 || u > m.dur * 1.5) break;
        const env = m.decay === 'linear' ? Math.max(0, 1 - u / m.dur) : Math.exp((-3 * u) / m.dur);
        const f = m.freq, sd = m.seed;
        const n = (o) => fbm1(u * f + o, sd + o, 2) * 1.6;
        s.rot.x += n(1) * m.rot * env; s.rot.y += n(2) * m.rot * env; s.rot.z += n(3) * m.rot * 0.6 * env;
        s.pos.x += n(4) * m.pos * env; s.pos.y += n(5) * m.pos * env;
        if (m.px) { s.px[0] += n(6) * m.px * env; s.px[1] += n(7) * m.px * env; }
        break;
      }
      case 'custom': m.fn(s, t, this); break;
    }
  }

  // Project a world point to pixel coords (x right, y down) using the current camera.
  toScreen(p, out = [0, 0]) { const v = this._tmp.copy(V(p)).project(this.cam); out[0] = (v.x * 0.5 + 0.5) * this.width; out[1] = (-v.y * 0.5 + 0.5) * this.height; out.z = v.z; return out; }
}

// The reference "house style" zoom-push FOV curve: linear image scale 1 -> 1+amount over the shot.
export const pushFov = (fov0, amount, u) => (2 * Math.atan(Math.tan(deg(fov0) / 2) / (1 + amount * u)) * 180) / Math.PI;
