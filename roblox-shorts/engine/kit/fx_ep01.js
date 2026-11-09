// EP01 effects kit (ASSETS.md "EFFECTS"; VISUAL_BIBLE 3.2, 5, 6.3). Units: world METRES (1 stud = 0.32 m); sizes named
// in the specs as studs are taken in STUDS (radius: 5 = 5 studs). Sprite sizes `px` are output pixels of the 1080x1920
// frame (screen-constant, they follow the zoom push). Every effect is a pure function of shot time t: build it in
// build(ctx), add `fx.group` (or the returned object) to the scene, and call `fx.update(t)` in update(ctx, t) AFTER the
// objects it follows (gnome, torch, mole field) have been posed for that t. Camera-dependent placement happens in
// onBeforeRender (the engine applies the camera after update()). Nothing accumulates between frames.
//
//   import * as X from '../../kit/fx_ep01.js';
//   const L = X.lanternLight(ctx, gnome, { t0: evT(ctx, 'lit'), ring: 5 }); ctx.add(L.group);   update: L.update(t)
//   const W = X.lightWave(ctx, { center, t0 }); ctx.add(W.group);                              update: W.update(t)
//
// API with examples: engine/kit/README_EP01.md, section "Effects (EP01 full episode) - kit/fx_ep01.js".
import * as THREE from 'three';
import * as sets from './sets.js';
import * as K from './chars.js';
import * as C from './creatures.js';
import { makeRng, hash32 } from '../core/random.js';
import { ringTex } from './kitlib.js';

const S = sets.STUD, PI = Math.PI, DEG = PI / 180;
export const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
const smooth = (x) => { const u = clamp01(x); return u * u * (3 - 2 * u); };
const outExpo = (x) => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * clamp01(x)));
const outQuad = (x) => 1 - (1 - clamp01(x)) * (1 - clamp01(x));
const inQuad = (x) => clamp01(x) * clamp01(x);
const outCubic = (x) => 1 - Math.pow(1 - clamp01(x), 3);
const inOutSine = (x) => 0.5 - 0.5 * Math.cos(PI * clamp01(x));
const outBack = (x) => { const c1 = 1.70158, c3 = c1 + 1, u = clamp01(x) - 1; return 1 + c3 * u * u * u + c1 * u * u; };
const hdr = (hex, k = 1) => new THREE.Color(hex).multiplyScalar(k);
const lerp = (a, b, k) => a + (b - a) * k;
// [x, z] (ground point), [x, y, z] or a Vector3 -> Vector3 (metres)
export const P3 = (p, y = 0) => (p && p.isVector3 ? p.clone() : p.length === 2 ? new THREE.Vector3(p[0], y, p[1]) : new THREE.Vector3(p[0], p[1], p[2]));
const worldOf = (o, out = new THREE.Vector3()) => { o.updateWorldMatrix(true, false); return o.getWorldPosition(out); };
const persist = (t) => { t.userData.persistent = true; return t; };
const cache = (ctx, key, fn) => ctx.cache('fxep01:' + key, fn);
function canvasTex(c, { srgb = true, repeat = false } = {}) {
  const t = new THREE.CanvasTexture(c); if (srgb) t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  if (repeat) t.wrapS = t.wrapT = THREE.RepeatWrapping; return persist(t);
}
function dataTex(W, H, fn, { repeat = false } = {}) {
  const d = new Uint8Array(W * H * 4);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) { const v = fn(x, y); const i = (y * W + x) * 4; d[i] = v[0]; d[i + 1] = v[1]; d[i + 2] = v[2]; d[i + 3] = v[3]; }
  const t = new THREE.DataTexture(d, W, H); t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearMipmapLinearFilter; t.generateMipmaps = true;
  if (repeat) t.wrapS = t.wrapT = THREE.RepeatWrapping; t.needsUpdate = true; return persist(t);
}

// "Light boost" blending: dst * (1 + src). Ground light that lights the grass texture (warm light on blue-teal grass
// stays gold and keeps the blades) instead of an additive wash that turns grey under the cool night grade.
export function boostBlend(mat) { mat.blending = THREE.CustomBlending; mat.blendEquation = THREE.AddEquation; mat.blendSrc = THREE.DstColorFactor; mat.blendDst = THREE.OneFactor; mat.transparent = true; mat.depthWrite = false; return mat; }

// ============================================================================================ sprites (approved look)
// Constant-pixel sprite (copy of the approved test's pxSprite): userData.px = output pixels (1920-high frame).
export function pxSprite(mat, px = 40, aspect = 1) {
  const s = new THREE.Sprite(mat); s.userData.px = px; s.userData.aspect = aspect;
  s.onBeforeRender = function (r, sc, cam) { const k = (this.userData.px * 2) / (1920 * cam.projectionMatrix.elements[5]); this.scale.set(k, k * this.userData.aspect, 1); this.updateMatrixWorld(); };
  return s;
}
export const addSpriteMat = (map, color, k = 1, o = {}) => new THREE.SpriteMaterial({ map, color: hdr(color, k), blending: THREE.AdditiveBlending, depthWrite: false, depthTest: false, transparent: true, fog: false, sizeAttenuation: false, ...o });
export const SPARK = { sharpness: 7, core: 0.75, underlay: 0.55, underlayOpacity: 0.5, brightness: 2.0, px: [55, 95] }; // the approved TF glint
const GOLD = ['#ffd27a', '#fff2d8', '#ffe2a8', '#ffc070'];
const sparkTex = (ctx, points = 6) => ctx.tex.sparkle({ points, sharpness: SPARK.sharpness, core: SPARK.core });

// One big 4-point star glint (promoted from part1 / common.js; identical look): 3-frame rise, 13.5-frame fall.
export function starGlint(ctx, { pos, t0, peak = 110, rot = 25, color = '#f4ecff', depthTest = false }) {
  const mat = addSpriteMat(ctx.tex.sparkle({ points: 4, sharpness: 22, core: 0.6 }), color, 2.4, { depthTest });
  const s = pxSprite(mat, 0); s.position.copy(P3(pos)); s.renderOrder = 30; s.visible = false;
  const core = pxSprite(addSpriteMat(ctx.tex.radialGlow({ falloff: 2.2 }), '#fff4ff', 1.6, { depthTest }), 0);
  core.position.copy(s.position); core.renderOrder = 29; core.visible = false;
  const g = new THREE.Group(); g.name = 'starGlint'; g.add(core, s);
  g.update = (t) => {
    const f = (t - t0) * 60; const on = f > -0.5 && f < 16.5; s.visible = core.visible = on; if (!on) return;
    const k = f < 3 ? (f + 1) / 4 : Math.pow(1 - (f - 3) / 13.5, 1.6);
    s.userData.px = peak * k; core.userData.px = peak * 0.42 * k; mat.rotation = rot * DEG * clamp01(f / 16); s.material.opacity = 1; core.material.opacity = 0.7 * k;
  };
  g.setPos = (p) => { s.position.copy(p); core.position.copy(p); };
  g.update(-1); return g;
}

// TF burst streaks (promoted from part1): additive rays shooting out of `pos` in the camera plane over `life` s. The
// camera basis is read at render time (onBeforeRender), so update(t) needs no camera.
function streakTex(ctx) {
  return ctx.cache('ep01t5:streakTex', () => {
    const W = 128, H = 32, d = new Uint8Array(W * H * 4);
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const u = x / (W - 1), v = (y - (H - 1) / 2) / ((H - 1) / 2); const taper = Math.pow(Math.sin(Math.PI * u), 0.6) * (0.35 + 0.65 * u);
      const a = Math.exp(-v * v * 9 / Math.max(0.15, taper)) * taper; const i = (y * W + x) * 4; d[i] = d[i + 1] = d[i + 2] = 255; d[i + 3] = Math.round(clamp01(a) * 255);
    }
    const t = new THREE.DataTexture(d, W, H); t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearMipmapLinearFilter; t.generateMipmaps = true; t.needsUpdate = true; t.userData.persistent = true; return t;
  });
}
export function streaks(ctx, { pos, t0, count = 14, px = [120, 260], life = 0.25, colors = ['#ffffff', '#ff7aa0', '#ffffff', '#ffd0e0'], seed = 'streaks', reach = 0.55 }) {
  const g = new THREE.Group(); g.name = 'streaks'; const r = makeRng(hash32('ep01t5', seed)); const tex = streakTex(ctx); const P0 = P3(pos);
  const right = new THREE.Vector3(), up = new THREE.Vector3();
  for (let i = 0; i < count; i++) {
    const s = pxSprite(addSpriteMat(tex, colors[i % colors.length], 2.2), 0, 0.2); s.renderOrder = 42; s.frustumCulled = false;
    s.userData.d = { a: (i / count) * Math.PI * 2 + (r() - 0.5) * 0.35, px: px[0] + (px[1] - px[0]) * r(), reach: reach * (0.6 + 0.6 * r()), life: life * (0.8 + 0.4 * r()) }; s.userData.k = 0; s.visible = false;
    const base = s.onBeforeRender;
    s.onBeforeRender = function (rr, sc, cam) {
      right.setFromMatrixColumn(cam.matrixWorld, 0).normalize(); up.setFromMatrixColumn(cam.matrixWorld, 1).normalize(); const d = this.userData.d;
      this.position.copy(P0).addScaledVector(right, Math.cos(d.a) * d.reach * (0.25 + 0.75 * this.userData.k)).addScaledVector(up, Math.sin(d.a) * d.reach * (0.25 + 0.75 * this.userData.k));
      base.call(this, rr, sc, cam);
    };
    g.add(s);
  }
  g.update = (t) => {
    for (const s of g.children) {
      const d = s.userData.d; const u = (t - t0) / d.life; if (u < 0 || u > 1) { s.visible = false; continue; } s.visible = true;
      const k = outExpo(u); s.userData.k = k; s.material.rotation = d.a; s.userData.px = d.px * (0.5 + 0.7 * k) * (1 - 0.4 * u); s.material.opacity = Math.pow(1 - u, 1.3);
    }
  };
  g.update(-1); return g;
}

// Cartoon puff cloud (promoted from part1: the s04 transformation poof).
function puffTex(ctx) {
  return ctx.cache('ep01t5:puffTex', () => {
    const N = 128, d = new Uint8Array(N * N * 4), c = (N - 1) / 2;
    for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) { const r = Math.hypot(x - c, y - c) / c; const a = r >= 1 ? 0 : r < 0.6 ? 1 : 1 - smooth((r - 0.6) / 0.4); const sh = 1 - 0.1 * clamp01((y - c) / c + 0.3 * (x - c) / c); const i = (y * N + x) * 4; d[i] = d[i + 1] = d[i + 2] = Math.round(255 * clamp01(sh)); d[i + 3] = Math.round(a * 255); }
    const t = new THREE.DataTexture(d, N, N); t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearMipmapLinearFilter; t.generateMipmaps = true; t.needsUpdate = true; t.userData.persistent = true; return t;
  });
}
export function poofCloud(ctx, { pos, t0, dur = 0.18, count = 6, spread = [0.42, 0.9, 0.2], px = [520, 700], colors = ['#fbf6ff', '#f3eaff', '#fff4f8', '#ffffff'], seed = 'poof' }) {
  const g = new THREE.Group(); g.name = 'poofCloud'; const r = makeRng(hash32('ep01t5', seed)); const tex = puffTex(ctx);
  for (let i = 0; i < count; i++) {
    const m = new THREE.SpriteMaterial({ map: tex, color: new THREE.Color(colors[i % colors.length]).multiplyScalar(1.05), transparent: true, depthWrite: false, depthTest: false, fog: false, sizeAttenuation: false });
    const s = pxSprite(m, 0); s.renderOrder = 25 + i; const o = new THREE.Vector3((r() - 0.5) * 2 * spread[0], (r() - 0.5) * 2 * spread[1] * 0.5, (r() - 0.5) * 2 * spread[2]);
    s.userData.d = { o, px: px[0] + (px[1] - px[0]) * r(), life: 0.8 + 0.4 * r(), drift: 0.3 + 0.4 * r() }; s.visible = false; g.add(s);
  }
  g.update = (t) => {
    const f = (t - t0) * 60;
    for (const s of g.children) {
      const d = s.userData.d; const v = (f - 1.5) / (60 * dur * d.life);
      if (f < -1.5 || v > 1) { s.visible = false; continue; } s.visible = true;
      const a = f < -0.5 ? 0.5 : f <= 1.5 ? 0.97 : 0.97 * Math.pow(1 - v, 2.5);
      const k = f < -0.5 ? 0.85 : 1 + 0.5 * outQuad(Math.max(0, v)); const dr = 1 + d.drift * Math.max(0, v);
      s.position.set(pos[0] + d.o.x * dr, pos[1] + d.o.y * dr + 0.06 * Math.max(0, v), pos[2] + d.o.z);
      s.userData.px = d.px * k; s.material.opacity = a;
    }
  };
  g.update(-10); return g;
}

// ============================================================================================ in-shot grade switch
// gradeBlend (approved test) and inShotGrade(ctx, from, to, t0, frames = 8, amount = 1, { rig, hemi }): blends grade,
// exposure, bloom and glow from `from` ('current' = ctx.post.params at build time, or a postPreset name) to the `to`
// preset over `frames` frames from t0 (bible P3: 6-10 frames on the beat word). Call it in build() AFTER the post is set;
// it enables glow at amount 0 when the target uses it (no recompile mid-shot). Returns update(t). `hemi`: [sky, ground,
// intensity] blends rig.hemi (P3 magic: ['#ffcdb8', '#5a2030', 1.4]).
const hexArr = (h) => { const c = new THREE.Color(); c.setStyle(h, THREE.NoColorSpace); return [c.r, c.g, c.b]; };
const toArr = (v, dflt) => (Array.isArray(v) ? v.slice(0, 3) : hexArr(v || dflt));
const GRADE_NUM = ['temperature', 'tint', 'contrast', 'pivot', 'saturation', 'shadowsAmount', 'highlightsAmount', 'balance'];
const GRADE_COL = ['shadows', 'highlights', 'outBlack', 'outWhite'];
export function gradeBlend(A, B) {
  const a = {}, b = {}; const d0 = (k) => (k === 'contrast' || k === 'saturation' ? 1 : k === 'pivot' ? 0.45 : 0);
  for (const k of GRADE_NUM) { a[k] = A[k] ?? d0(k); b[k] = B[k] ?? d0(k); }
  for (const k of GRADE_COL) { const dc = k === 'outWhite' ? '#ffffff' : '#000000'; a[k] = toArr(A[k], dc); b[k] = toArr(B[k], dc); }
  return (G, k) => { for (const n of GRADE_NUM) G[n] = a[n] + (b[n] - a[n]) * k; for (const n of GRADE_COL) G[n] = a[n].map((x, i) => x + (b[n][i] - x) * k); };
}
export function inShotGrade(ctx, from = 'current', to = 'magic', t0 = 0, frames = 8, amount = 1, { rig = null, hemi = null } = {}) {
  const A = from === 'current' ? JSON.parse(JSON.stringify(ctx.post.params)) : sets.postPreset(from); const B = typeof to === 'string' ? sets.postPreset(to) : to;
  const gb = gradeBlend(A.grade || {}, B.grade || {}); const useGlow = B.glow && B.glow.enabled;
  if (useGlow && !(ctx.post.params.glow && ctx.post.params.glow.enabled)) ctx.post.set({ glow: { enabled: true, amount: 0, radius: B.glow.radius, mode: B.glow.mode, tint: B.glow.tint } });
  const H0 = rig && rig.hemi ? [rig.hemi.color.clone(), rig.hemi.groundColor.clone(), rig.hemi.intensity] : null;
  const H1 = hemi ? [new THREE.Color(hemi[0]), new THREE.Color(hemi[1]), hemi[2]] : null;
  const bl = (o, k) => (o && o.bloom ? o.bloom[k] : undefined);
  return (t) => {
    const u = smooth(((t - t0) * 60) / frames) * amount; const pp = ctx.post.params;
    gb(pp.grade, u); pp.exposure = lerp(A.exposure ?? 1, B.exposure ?? 1, u);
    for (const k of ['strength', 'threshold', 'radius']) if (bl(A, k) != null && bl(B, k) != null) pp.bloom[k] = lerp(bl(A, k), bl(B, k), u);
    if (useGlow) pp.glow.amount = lerp(A.glow && A.glow.enabled ? A.glow.amount : 0, B.glow.amount, u);
    if (H0 && H1) { rig.hemi.color.copy(H0[0]).lerp(H1[0], u); rig.hemi.groundColor.copy(H0[1]).lerp(H1[1], u); rig.hemi.intensity = lerp(H0[2], H1[2], u); }
  };
}

// ============================================================================================ LANTERN RING (fx_lantern_ring)
// lanternRing(ctx, { center | follow, radius: 5 (studs), rim: 0.25, falloff: 0.6, inner: '#ff8a2a', boost: 1.7,
// rimColor: '#ffb04a', rimBoost: 3.0, rimA: 0.55, innerA: 0.06, level: 1, glints: 0, y }) -> Mesh (+ .group).
// The ground light of a lit lantern: a flat warm interior, a bright crisp rim 0.25 stud wide (the line the moles stop at)
// and a soft 0.6-stud falloff outside. Two passes on one disc: a light boost (dst x (1 + warm x level), so the lawn
// texture is lit gold, not washed) and a thin additive glow on the rim (+ a trace inside).
// `follow`: an Object3D (lantern / gnome / hero) or fn(t) -> Object3D: the centre is its ground point every update.
// ring.edgeOf(pos) -> [x, z] rim point toward pos; ring.centerXZ(); ring.radius (metres) -> moleField.stopAt(i,
// ring.centerXZ(), ring.radius); ring.setLevel(k); ring.update(t); ring.contains(pos).
const RING_VS = `varying vec2 vP; void main(){ vP = position.xy; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;
const RING_FS = `uniform float uR, uRim, uFall, uLevel, uTime, uBoost, uRimB, uInnerA, uRimA, uSeed, uMode, uPoolA, uPoolR; uniform vec3 uInner, uRimC, uPool; varying vec2 vP;
void main(){
  float d = length(vP); float ang = atan(vP.y, vP.x);
  float R = uR * (1.0 + 0.006 * sin(ang * 7.0 + uTime * 1.3 + uSeed) + 0.004 * sin(ang * 19.0 - uTime * 2.1));
  float inner = (1.0 - smoothstep(R - uRim * 1.2, R - uRim * 0.35, d)) * (0.5 + 0.5 * (1.0 - smoothstep(0.0, R, d)));
  float rx = (d - (R - uRim * 0.5)) / (uRim * 0.5);
  float rim = exp(-rx * rx * 1.8) * (0.86 + 0.14 * sin(ang * 13.0 - uTime * 1.8 + uSeed * 3.0));
  float o = d > R - uRim * 0.5 ? 0.55 * pow(1.0 - clamp((d - (R - uRim * 0.5)) / uFall, 0.0, 1.0), 2.2) : 0.0;
  float pool = pow(clamp(1.0 - d / uPoolR, 0.0, 1.0), 1.7);
  vec3 c = uMode < 0.5 ? uInner * (uBoost * (inner + o)) + uRimC * (uRimB * rim) : uInner * (uInnerA * (inner + o)) + uRimC * (uRimA * rim) + uPool * (uPoolA * pool);
  gl_FragColor = vec4(c * uLevel, 1.0);
}`;
// EP01 review fix: the multiplicative boost turned the grass to pale straw. The boost / rim numbers callers pass are scaled
// down (RING_K) and an additive warm pool (pool colour, poolA, 1.25 R, centre-weighted) carries the light instead.
const RING_K = { boost: 0.42, rimBoost: 0.55, rimA: 0.5 };
export function lanternRing(ctx, { center = [0, 0, 0], follow = null, radius = 5, rim = 0.25, falloff = 1.6, inner = '#ff9a40', boost = 1.7, rimColor = '#ffb04a', rimBoost = 3.0, rimA = 0.55, innerA = 0.1, pool = '#ff8a30', poolA = 0.17, poolR = 1.25, level = 1, intensity = 1, glints = 0, y = null, seed = 'ring' } = {}) {
  boost *= RING_K.boost; rimBoost *= RING_K.rimBoost; rimA *= RING_K.rimA;
  const R = radius * S, W = rim * S, F = falloff * S, PR = R * poolR, half = Math.max(R + F + W, PR);
  const mk = (mode) => { const u = { uR: { value: R }, uRim: { value: W }, uFall: { value: F }, uLevel: { value: level }, uTime: { value: 0 }, uBoost: { value: boost * intensity }, uRimB: { value: rimBoost * intensity }, uInnerA: { value: innerA * intensity }, uRimA: { value: rimA * intensity }, uSeed: { value: (hash32(seed) % 1000) / 100 }, uMode: { value: mode }, uInner: { value: new THREE.Color(inner) }, uRimC: { value: new THREE.Color(rimColor) }, uPool: { value: new THREE.Color(pool) }, uPoolA: { value: poolA * intensity }, uPoolR: { value: PR } };
    const m = new THREE.ShaderMaterial({ uniforms: u, vertexShader: RING_VS, fragmentShader: RING_FS, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 }); if (mode === 0) boostBlend(m); return m; };
  const geo = new THREE.PlaneGeometry(half * 2, half * 2); const mB = mk(0), mA = mk(1);
  const m = new THREE.Mesh(geo, mB); m.rotation.x = -PI / 2; m.renderOrder = 3; m.name = 'lanternRing';
  const add = new THREE.Mesh(geo, mA); add.rotation.x = -PI / 2; add.renderOrder = 4; add.name = 'lanternRingGlow';
  const grp = new THREE.Group(); grp.name = 'lanternRingFx'; grp.add(m, add);
  const c0 = follow ? new THREE.Vector3() : P3(center); const gy = y ?? c0.y;
  m.radius = R; m.center = new THREE.Vector3(c0.x, gy, c0.z); m.group = grp; m.level = level;
  const r = makeRng(hash32('ringGlints', seed)); const gl = [];
  for (let i = 0; i < glints; i++) { const s = pxSprite(addSpriteMat(sparkTex(ctx, 6), GOLD[i % GOLD.length], 1.8, { depthTest: true }), 30); s.renderOrder = 7; s.userData.d = { a: r() * PI * 2, w: (r() - 0.5) * 0.25, h: 0.04 + 0.25 * r(), per: 0.7 + 0.6 * r(), ph: r(), px: 34 + 26 * r() }; grp.add(s); gl.push(s); }
  m.setLevel = (k) => { m.level = k; mB.uniforms.uLevel.value = k; mA.uniforms.uLevel.value = k; m.visible = add.visible = k > 0.001; };
  m.centerXZ = () => [m.center.x, m.center.z];
  m.edgeVec = (pos) => { const p = P3(pos); const d = new THREE.Vector3(p.x - m.center.x, 0, p.z - m.center.z); if (d.lengthSq() < 1e-8) d.set(1, 0, 0); return m.center.clone().addScaledVector(d.normalize(), R); };
  m.edgeOf = (pos) => { const e = m.edgeVec(pos); return [e.x, e.z]; };
  m.contains = (pos) => { const p = P3(pos); return Math.hypot(p.x - m.center.x, p.z - m.center.z) < R; };
  const fp = new THREE.Vector3();
  m.update = (t) => {
    if (follow) { worldOf(typeof follow === 'function' ? follow(t) : follow, fp); m.center.set(fp.x, gy, fp.z); }
    m.position.set(m.center.x, m.center.y + 0.018, m.center.z); add.position.copy(m.position); mB.uniforms.uTime.value = mA.uniforms.uTime.value = t;
    for (const s of gl) { const d = s.userData.d; const a = d.a + d.w * t; const tw = 0.5 + 0.5 * Math.sin((t / d.per + d.ph) * PI * 2); s.position.set(m.center.x + Math.cos(a) * R * 0.985, m.center.y + d.h * S + 0.04 * Math.sin(t * 0.8 + d.ph * 6), m.center.z + Math.sin(a) * R * 0.985); s.userData.px = d.px * (0.6 + 0.6 * tw); s.material.opacity = (0.35 + 0.65 * tw) * clamp01(m.level); s.visible = m.level > 0.02; }
  };
  grp.update = m.update; m.update(0); return m;
}

// ============================================================================================ LANTERN LIGHT-UP
// lanternLight(ctx, gnome, { t0, level: 1, cd: 3.2, ring: 5 | 0, ringOpts, burst: true, haloPx: 64, flicker: true,
// levelFn: (t) => level }) -> { group, update(t), ring, light, level(t), cues }.
// Glass glows (K.setLantern: emissive 0 -> x6 in 3 frames, 6-frame overshoot to 1.5, flame on), the kit halo fades in
// over 0.2 s, plus a screen-constant warm halo (15-30 px core), a warm point light at the glass (#ffb85c, `cd` x level,
// no shadow: it under-lights the face like the TF fairies), a light ring/pool on the ground following the lantern, and
// a small gold burst on the light-up frame. levelFn overrides the light-up curve (FWOOM).
export function lanternLight(ctx, gnome, { t0 = 0, level = 1, cd = 1.6, ring = 5, ringOpts = {}, burst = true, burstOpts = {}, haloPx = 64, haloColor = '#ff9a40', glassK = 2.4, flicker = true, levelFn = null, light = true, lightOffset = null, seed = 'lantern' } = {}) {
  haloPx = Math.max(64, haloPx * 1.25); // review: every lit lantern gets a 60-90 px halo
  const grp = new THREE.Group(); grp.name = 'lanternLightFx';
  const L = gnome.getObjectByName('lantern'); if (!L) throw new Error('lanternLight: gnome has no lantern');
  let pl = L.getObjectByName('lanternLight'); const own = !pl && light;
  if (own) { pl = new THREE.PointLight('#ffb85c', 0, 0, 2); pl.name = 'fxLanternLight'; pl.position.set(0, -0.165, 0); if (lightOffset) { grp.add(pl); pl.userData.off = P3(lightOffset); } else L.add(pl); }
  const glassPos = () => { const g = L.getObjectByName('lanternGlass') || L; return worldOf(g, new THREE.Vector3()); };
  const halo = pxSprite(addSpriteMat(ctx.tex.radialGlow({ falloff: 2.6 }), haloColor, 1.3, { depthTest: true }), haloPx); halo.renderOrder = 12; grp.add(halo);
  const core = pxSprite(addSpriteMat(ctx.tex.radialGlow({ falloff: 3.2 }), '#fff0c8', 1.6, { depthTest: true }), haloPx * 0.32); core.renderOrder = 13; grp.add(core);
  const rg = ring ? lanternRing(ctx, { follow: () => L, radius: ring, y: 0, seed: seed + 'ring', ...ringOpts }) : null; if (rg) grp.add(rg.group);
  const kitPool = gnome.getObjectByName('lanternPool'); if (kitPool && rg) kitPool.visible = false; // the ring replaces the kit's additive pool
  const b = burst ? sets.burst(ctx, { pos: glassPos().toArray(), t0, dur: 0.32, count: 12, spread: 0.35, px: [26, 54], ringPx: [30, 300], ringColor: '#ffe6b8', colors: ['#fff6e0', '#ffd27a', '#ffe2a8'], corePx: 150, brightness: 2.0, gravity: -0.1, seed: seed + 'burst', ...burstOpts }) : null;
  if (b) grp.add(b);
  const levelAt = (t) => { if (levelFn) return { level: levelFn(t), halo: 1 }; const r = K.lanternLightUp(t, t0); return { level: r.level * level, halo: r.halo }; };
  const p = new THREE.Vector3();
  const update = (t) => {
    const { level: lv, halo: h } = levelAt(t); const fl = flicker ? K.lanternFlicker(t, seed) : 1;
    K.setLantern(gnome, lv, { halo: h, flicker: fl, light: !own });
    const kh = L.getObjectByName('lanternHalo'); if (kh) { kh.scale.setScalar(0.9 * (1 + 0.1 * Math.min(3, Math.max(0, lv - 1)))); kh.material.opacity = 0.5 * Math.min(lv, 1.4) * h; }
    const gm = L.getObjectByName('lanternGlass'); if (gm && gm.material) { gm.material.emissiveIntensity = glassK * lv * fl; gm.material.emissive.set('#ff9a2a'); }
    const fm = L.getObjectByName('lanternFlame'); if (fm && fm.material && lv > 0) fm.material.color.set('#fff0c8').multiplyScalar(2.2 * Math.min(lv, 3));
    if (own && pl) { pl.intensity = cd * (2 * Math.min(lv, 1) + Math.max(0, lv - 1)) * fl; pl.visible = lv > 0.001; if (pl.userData.off) pl.position.copy(glassPos()).add(pl.userData.off); }
    else if (pl) pl.userData.cd = pl.userData.cd ?? cd;
    worldOf(L.getObjectByName('lanternGlass') || L, p); halo.position.copy(p); core.position.copy(p);
    const k = Math.min(lv, 3) * h; halo.visible = core.visible = k > 0.002;
    halo.material.opacity = 0.72 * Math.min(1, k) * fl; halo.userData.px = haloPx * (0.85 + 0.15 * Math.min(2, lv)); core.material.opacity = 0.8 * Math.min(1, k); core.userData.px = haloPx * 0.32 * (0.9 + 0.1 * Math.min(3, lv));
    if (rg) { rg.setLevel(Math.min(1.6, lv) * h * (0.94 + 0.06 * fl)); rg.update(t); }
    if (b) b.update(t);
  };
  update(0);
  return { group: grp, update, ring: rg, light: pl, level: (t) => levelAt(t).level, cues: [{ t: t0, kind: 'lantern_on' }] };
}

// ============================================================================================ LANTERN CASCADE (fx_lantern_cascade)
// lanternCascade(ctx, gnomes, { t0, order: 'toward camera' | 'away' | 'given', gap: [0.15, 0.3], skip: [lot ids / slot
// names], preLit: [...], ring: 2, lights: 4, cd: 1.6, burst: true, seed }) -> { group, items, cues, update(t) }.
// gnomes: Object3D[] or ep01Street's root.ep01.gnomes ({ g, lot, slot, plastic }); plastic gnomes are skipped. Each lantern
// lights with K.lanternLightUp at its own seeded time (bible: light-state events cascade 0.15-0.45 s apart), gets a 2-stud
// ring, and the `lights` nearest the camera get a real point light. cues = [{ t, lot, slot }] (a 'tink' each, for the mix).
export function lanternCascade(ctx, gnomes, { t0 = 0, order = 'toward camera', gap = [0.15, 0.3], skip = [], preLit = [], ring = 2, ringOpts = {}, lights = 4, cd = 1.6, burst = true, from = null, seed = 'cascade' } = {}) {
  const grp = new THREE.Group(); grp.name = 'lanternCascade'; const r = makeRng(hash32('cascade', seed));
  const cam = from ? P3(from) : sets.camBasis(ctx).pos;
  let list = gnomes.map((e) => (e && e.isObject3D ? { g: e } : { ...e, g: e.g || e.gnome })).filter((e) => e.g && !e.plastic && e.g.getObjectByName('lantern'))
    .filter((e) => !skip.some((s) => s === e.lot || s === e.slot || s === e.g.name));
  list.forEach((e) => { e.d = worldOf(e.g).distanceTo(cam); e.pre = preLit.some((s) => s === e.lot || s === e.slot); });
  if (order === 'toward camera') list.sort((a, b) => b.d - a.d); else if (order === 'away') list.sort((a, b) => a.d - b.d);
  let t = t0; const lit = list.filter((e) => !e.pre);
  lit.forEach((e, i) => { if (i > 0) t += gap[0] + (gap[1] - gap[0]) * r(); e.t0 = t; });
  list.filter((e) => e.pre).forEach((e) => { e.t0 = -10; });
  const near = list.slice().sort((a, b) => a.d - b.d).slice(0, lights);
  for (const e of list) {
    e.fx = lanternLight(ctx, e.g, { t0: e.t0, ring, ringOpts: { boost: 1.5, rimBoost: 2.6, rimA: 0.5, ...ringOpts }, burst: burst && !e.pre, burstOpts: { count: 8, ringPx: [16, 110], corePx: 90, px: [20, 40] }, haloPx: 54, cd, light: near.includes(e), seed: seed + (e.slot || e.g.uuid) });
    grp.add(e.fx.group);
  }
  return { group: grp, items: list, cues: lit.map((e) => ({ t: e.t0, lot: e.lot, slot: e.slot, kind: 'tink' })), update: (tt) => { for (const e of list) e.fx.update(tt); } };
}

// ============================================================================================ FLASHLIGHT BEAM (fx_beam)
// flashlightBeam(ctx, { torch | origin + dir, length: 9 (studs), angle: 14 (deg, full cone), t0 (on, 1 frame), t1 (off),
// cd: 4, color: '#fff1d0', opacity: 0.18, ground: 0, spot: true, light: true, motes: 6 }) -> { group, update(t), on(t0) }.
// torch = creatures.makeFlashlight() (reads its lens each frame: the beam follows the hand). An additive cone (bright along
// the axis, soft at the silhouette, fading to the tip), a ground spot (elongated light pool where the axis hits y = ground)
// and an unshadowed SpotLight; a few dust motes hang in the beam.
const BEAM_VS = `varying float vU; varying vec3 vN, vV; void main(){ vU = position.z; vec4 mv = modelViewMatrix * vec4(position, 1.0); vV = -mv.xyz; vN = normalMatrix * normal; gl_Position = projectionMatrix * mv; }`;
const BEAM_FS = `uniform vec3 uC; uniform float uA; varying float vU; varying vec3 vN, vV;
void main(){ float along = pow(clamp(1.0 - vU, 0.0, 1.0), 1.4) * smoothstep(0.0, 0.14, vU); float e = abs(dot(normalize(vN), normalize(vV))); float soft = pow(e, 2.0);
  gl_FragColor = vec4(uC * uA * along * soft, 1.0); }`;
export function flashlightBeam(ctx, { torch = null, origin = null, dir = null, length = 9, angle = 14, t0 = -1e9, t1 = 1e9, cd = 4, color = '#fff1d0', opacity = 0.18, ground = 0, spot = true, light = true, motes = 6, seed = 'beam' } = {}) {
  const grp = new THREE.Group(); grp.name = 'flashlightBeam'; const Lm = length * S, half = (angle / 2) * DEG, rEnd = Math.tan(half) * Lm;
  const geo = new THREE.ConeGeometry(1, 1, 40, 8, true); geo.translate(0, -0.5, 0); geo.rotateX(-PI / 2); // apex at 0, axis +z, base at z = 1
  const u = { uC: { value: hdr(color, 1) }, uA: { value: opacity * 2.4 } };
  const cone = new THREE.Mesh(geo, new THREE.ShaderMaterial({ uniforms: u, vertexShader: BEAM_VS, fragmentShader: BEAM_FS, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide }));
  cone.scale.set(rEnd, rEnd, Lm); cone.renderOrder = 8; cone.frustumCulled = false; grp.add(cone);
  const poolMat = new THREE.MeshBasicMaterial({ map: ctx.tex.radialGlow({ falloff: 1.5 }), color: hdr(color, 1), transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 });
  const pool = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), poolMat); pool.renderOrder = 3; grp.add(pool);
  let sl = null; if (light) { sl = new THREE.SpotLight(color, 0, 0, half * 1.5, 0.65, 2); sl.name = 'beamLight'; grp.add(sl, sl.target); }
  const lensGlow = pxSprite(addSpriteMat(ctx.tex.radialGlow({ falloff: 2.4 }), '#fff6e4', 1.5, { depthTest: true }), 70); lensGlow.renderOrder = 9; grp.add(lensGlow);
  const r = makeRng(hash32('beamMotes', seed)); const mts = [];
  for (let i = 0; i < motes; i++) { const s = pxSprite(addSpriteMat(ctx.tex.radialGlow({ falloff: 1.8 }), '#fff4e0', 1.4, { depthTest: true }), 8); s.userData.d = { u: 0.15 + 0.7 * r(), a: r() * PI * 2, rr: Math.sqrt(r()) * 0.7, w: 0.2 + 0.4 * r(), ph: r() * 6, px: 6 + 8 * r() }; s.renderOrder = 9; grp.add(s); mts.push(s); }
  const O = new THREE.Vector3(), D = new THREE.Vector3(0, 0, 1), Z = new THREE.Vector3(0, 0, 1), side = new THREE.Vector3(), upv = new THREE.Vector3();
  let tOn = t0;
  const ray = () => {
    if (torch) { const lens = torch.getObjectByName('torchLens') || torch; lens.updateWorldMatrix(true, false); lens.getWorldPosition(O); D.set(0, 0, 1).transformDirection(lens.matrixWorld).normalize(); }
    else { O.copy(typeof origin === 'function' ? origin() : P3(origin)); D.copy(typeof dir === 'function' ? dir() : P3(dir)).normalize(); }
  };
  const update = (t) => {
    const on = t >= tOn && t < t1; grp.visible = on; if (sl) sl.visible = on; if (!on) return;
    ray(); cone.position.copy(O); cone.quaternion.setFromUnitVectors(Z, D);
    lensGlow.position.copy(O); lensGlow.material.opacity = 0.75;
    if (sl) { sl.intensity = cd; sl.position.copy(O); sl.target.position.copy(O).addScaledVector(D, 4); sl.target.updateMatrixWorld(); }
    // ground spot
    pool.visible = false;
    if (spot && D.y < -0.03) {
      const dist = (ground - O.y) / D.y; if (dist > 0 && dist < Lm * 1.25) {
        const hit = O.clone().addScaledVector(D, dist); const rr = Math.tan(half) * dist * 1.15; const el = Math.max(0.18, -D.y);
        pool.visible = true; pool.position.set(hit.x, ground + 0.015, hit.z); pool.rotation.set(-PI / 2, 0, Math.atan2(D.x, D.z) + PI);
        pool.scale.set(rr, Math.min(rr / el, rr * 4), 1); poolMat.opacity = 0.6 * (1 - 0.5 * clamp01(dist / Lm));
      }
    }
    side.crossVectors(D, Math.abs(D.y) > 0.95 ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 1, 0)).normalize(); upv.crossVectors(side, D).normalize();
    for (const s of mts) { const d = s.userData.d; const uu = d.u + 0.04 * Math.sin(t * d.w + d.ph); const rad = Math.tan(half) * Lm * uu * d.rr; const a = d.a + 0.3 * Math.sin(t * d.w * 0.7 + d.ph);
      s.position.copy(O).addScaledVector(D, Lm * uu).addScaledVector(side, Math.cos(a) * rad).addScaledVector(upv, Math.sin(a) * rad + 0.01 * Math.sin(t * 1.3 + d.ph)); s.material.opacity = 0.45 * (1 - uu) * (0.6 + 0.4 * Math.sin(t * 3 + d.ph)); s.userData.px = d.px; }
  };
  update(0);
  return { group: grp, update, cone, pool, light: sl, on: (t) => { tOn = t; } };
}

// ============================================================================================ CURTAIN CASCADE (fx_curtains)
// curtainCascade(ctx, set, { t0, gap: 0.12, n: 6, color: '#7a2a3a', frames: 4, from: camera pos, lots: null, inView: true })
// -> { group, update(t), cues }. Per lit front window in the camera view at t = 0 (nearest first; build after the camera) two backlit fabric panels slide shut from the
// window sides in 4 frames (outQuad) and the window glow sprite drops to x0.6. set = a sets.buildStreet / heroLot /
// ep01Street root (uses userData.windows / lots).
function curtainTex(ctx, color) {
  return cache(ctx, 'curtain:' + color, () => {
    const c = document.createElement('canvas'); c.width = 128; c.height = 64; const g = c.getContext('2d'); const base = new THREE.Color(color);
    void base; g.fillStyle = color; g.fillRect(0, 0, 128, 64);
    for (let x = 0; x < 128; x++) { const f = Math.pow(0.5 + 0.5 * Math.sin((x / 128) * PI * 2 * 4.5), 0.8) + 0.08 * Math.sin(x * 1.7); g.fillStyle = f > 0.5 ? `rgba(255,220,200,${0.22 * (f - 0.5)})` : `rgba(0,0,0,${0.5 * (0.5 - f)})`; g.fillRect(x, 0, 1, 64); }
    g.fillStyle = 'rgba(0,0,0,0.25)'; g.fillRect(0, 0, 128, 3); return canvasTex(c);
  });
}
export function curtainCascade(ctx, set, { t0 = 0, gap = 0.12, n = 6, color = '#7a2a3a', frames = 4, from = null, lots = null, inView = true, glow = 0.6, emissive = 1.1, seed = 'curtains' } = {}) {
  const grp = new THREE.Group(); grp.name = 'curtainCascade'; const r = makeRng(hash32('curtains', seed)); const U = set.userData;
  set.updateMatrixWorld(true); const sc = set.scale.x || 1; const camP = from ? P3(from) : sets.camBasis(ctx).pos; const cam = ctx.cam; cam.updateMatrixWorld(true); cam.updateProjectionMatrix();
  const inV = (v) => { if (!inView || from) return true; const q = v.clone().project(cam); return q.z < 1 && Math.abs(q.x) < 0.92 && Math.abs(q.y) < 0.92; };
  const toW = (p) => new THREE.Vector3(p[0], p[1], p[2]).divideScalar(sc).applyMatrix4(set.matrixWorld);
  const lotYaw = Object.fromEntries(U.lots.map((l) => [l.id, l.yaw]));
  const wins = U.windows.filter((w) => w.lit && w.face === 'front' && (!lots || lots.includes(w.lot))).map((w) => ({ ...w, W: toW(w.pos) })).filter((w) => inV(w.W)).sort((a, b) => a.W.distanceTo(camP) - b.W.distanceTo(camP)).slice(0, n);
  const glows = []; set.traverse((o) => { if (o.name === 'winGlow' && o.isSprite) glows.push(o); });
  const tex = curtainTex(ctx, color); const mat = new THREE.MeshStandardMaterial({ map: tex, color: '#ffffff', emissive: hdr(color, 1), emissiveMap: tex, emissiveIntensity: emissive, roughness: 0.9, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1 });
  const geoL = new THREE.PlaneGeometry(1, 1); geoL.translate(0.5, 0, 0); const geoR = new THREE.PlaneGeometry(1, 1); geoR.translate(-0.5, 0, 0);
  const items = wins.map((w, i) => {
    const yaw = lotYaw[w.lot] ?? 0; const nrm = new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw)).transformDirection(set.matrixWorld); const ang = Math.atan2(nrm.x, nrm.z);
    const g = new THREE.Group(); g.position.copy(w.W).addScaledVector(nrm, -0.035 * S); g.rotation.y = ang; grp.add(g); // just in front of the glass, behind the muntin bars
    const ww = 4 * S, wh = 5 * S; const pL = new THREE.Mesh(geoL, mat), pR = new THREE.Mesh(geoR, mat); pL.position.x = -ww / 2; pR.position.x = ww / 2; pL.scale.y = pR.scale.y = wh * 1.0; g.add(pL, pR);
    const wg = glows.filter((s) => { const p = worldOf(s, new THREE.Vector3()); return Math.hypot(p.x - w.W.x, p.z - w.W.z) < 1.0 && Math.abs(p.y - w.W.y) < 1.2; }).map((s) => { s.material = s.material.clone(); return { s, op: s.material.opacity }; });
    return { g, pL, pR, ww, t: t0 + i * gap + (i ? (r() - 0.5) * 0.03 : 0), wg };
  });
  const update = (t) => {
    for (const it of items) {
      const u = ((t - it.t) * 60 + 1) / frames; const k = u <= 0 ? 0 : outQuad(u); it.g.visible = k > 0;
      const w = (it.ww / 2 + 0.03 * S) * (0.12 + 0.88 * k); it.pL.scale.x = it.pR.scale.x = w;
      for (const e of it.wg) e.s.material.opacity = e.op * (1 - (1 - glow) * k);
    }
  };
  update(0); return { group: grp, update, cues: items.map((it) => ({ t: it.t, kind: 'curtain' })), windows: items.length };
}

// ============================================================================================ GLASS FOG (fx_glass_fog)
// glassFog(ctx, pane, { t0, center, r1: 0.9 (studs), grow: 0.35, opacity: 0.7, color: '#dfe4ff', glow: '#ffb347',
// eyes: [Vector3, Vector3] (world: the amber eyes behind the glass), eyeGlow: 0.8, toward: viewer point, brightness: 1 })
// -> Mesh with update(t). A soft noisy breath disc on the pane that blooms over `grow` s, then breathes (+-6 %, 0.4 Hz)
// and slowly clears; warm where the eyes shine through. pane: the glass Mesh (PlaneGeometry, faces +Z) or { pos, normal }.
function noiseTex(ctx, N = 64, seed = 7) {
  return cache(ctx, 'noise:' + N + ':' + seed, () => {
    const r = makeRng(hash32('fxnoise', seed)); const G = (n) => { const a = new Float32Array(n * n); for (let i = 0; i < a.length; i++) a[i] = r(); return a; };
    const oct = [[4, 0.5], [8, 0.3], [16, 0.2]].map(([n, w]) => ({ n, w, g: G(n) }));
    const val = (x, y) => { let s = 0; for (const o of oct) { const fx = (x / N) * o.n, fy = (y / N) * o.n; const x0 = Math.floor(fx), y0 = Math.floor(fy), tx = smooth(fx - x0), ty = smooth(fy - y0); const g = (i, j) => o.g[((j % o.n) + o.n) % o.n * o.n + (((i % o.n) + o.n) % o.n)]; s += o.w * lerp(lerp(g(x0, y0), g(x0 + 1, y0), tx), lerp(g(x0, y0 + 1), g(x0 + 1, y0 + 1), tx), ty); } return s; };
    return dataTex(N, N, (x, y) => { const v = Math.round(255 * clamp01(val(x, y))); return [v, v, v, 255]; }, { repeat: true });
  });
}
const FOG_FS = `uniform float uR, uOp, uEyeK; uniform vec3 uCol, uWarm; uniform vec2 uE0, uE1; uniform sampler2D uNoise; varying vec2 vP;
void main(){ if (uR <= 0.0001) discard; float n = texture2D(uNoise, vP * 2.2 + 0.37).r; float n2 = texture2D(uNoise, vP * 7.0 + 0.11).r;
  float d = length(vP * vec2(1.0, 1.15)) + (n - 0.5) * 0.45 * uR;
  float a = uOp * (1.0 - smoothstep(uR * 0.35, uR, d)) * (0.72 + 0.28 * n2);
  float w = uEyeK * (exp(-dot(vP - uE0, vP - uE0) / (uR * uR * 0.18)) + exp(-dot(vP - uE1, vP - uE1) / (uR * uR * 0.18)));
  gl_FragColor = vec4(mix(uCol, uWarm, clamp(w, 0.0, 0.85)), a); }`;
export function glassFog(ctx, pane, { t0 = 0, center = null, r1 = 0.9, grow = 0.35, opacity = 0.7, color = '#dfe4ff', glow = '#ffb347', eyes = [], eyeGlow = 0.8, toward = null, brightness = 1.0, clear = 2.5, seed = 'fog' } = {}) {
  let pos, nrm;
  if (pane && pane.isObject3D) { pane.updateWorldMatrix(true, false); pos = center ? P3(center) : pane.getWorldPosition(new THREE.Vector3()); nrm = new THREE.Vector3(0, 0, 1).transformDirection(pane.matrixWorld); }
  else { pos = P3(center || pane.pos); nrm = P3(pane.normal).normalize(); }
  const view = toward ? P3(toward) : sets.camBasis(ctx).pos; if (view.clone().sub(pos).dot(nrm) < 0) nrm.negate();
  const R1 = r1 * S; const u = { uR: { value: 0 }, uOp: { value: opacity }, uEyeK: { value: eyes.length ? eyeGlow : 0 }, uCol: { value: hdr(color, brightness) }, uWarm: { value: hdr(glow, brightness * 2.2) }, uE0: { value: new THREE.Vector2(9, 9) }, uE1: { value: new THREE.Vector2(9, 9) }, uNoise: { value: noiseTex(ctx, 64, hash32(seed) % 50) } };
  const m = new THREE.Mesh(new THREE.PlaneGeometry(R1 * 2.6, R1 * 2.6), new THREE.ShaderMaterial({ uniforms: u, vertexShader: RING_VS, fragmentShader: FOG_FS, transparent: true, depthWrite: false }));
  m.position.copy(pos).addScaledVector(nrm, 0.004); m.lookAt(m.position.clone().add(nrm)); m.renderOrder = 6; m.name = 'glassFog'; m.updateMatrixWorld(true);
  const inv = new THREE.Matrix4().copy(m.matrixWorld).invert();
  eyes.slice(0, 2).forEach((e, i) => { const l = P3(e).applyMatrix4(inv); (i ? u.uE1 : u.uE0).value.set(l.x, l.y); });
  m.update = (t) => { const a = (t - t0) / grow; if (a <= 0) { u.uR.value = 0; return; } const br = 1 + 0.06 * Math.sin((t - t0) * 2 * PI * 0.4) * smooth(a - 1);
    u.uR.value = R1 * outCubic(a) * br; u.uOp.value = opacity * (1 - 0.6 * smooth((t - t0 - grow) / clear)); };
  m.group = m; m.update(0); return m;
}

// ============================================================================================ GOLD OUTLINE (fx_gold_outline)
// goldOutline(ctx, objs, { t0, color: '#ffb43a' (saturated: the night grade whitens #ffd27a), width: 0.02 (m), peak: 0.9, hold: 0.5, rise: 0.12, settle: 0.6,
// t1: fade-out time, opacity: fn(t) override, sparkles: 8, filter: (mesh) => bool }) -> { group, update(t) }.
// "Only family": an inverted hull (BackSide, additive) pushed out along smoothed normals in view space, two layers (a
// crisp rim and a soft 2.4x halo), on every mesh under objs (hands/arms, the gnome); opacity 0 -> peak -> hold. Plus gold
// TF sparkles around the outlined bounds.
const HULL_VS = `attribute vec3 oNormal; uniform float uW; void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.0); vec3 n = normalize(normalMatrix * oNormal); mv.xyz += n * uW; gl_Position = projectionMatrix * mv; }`;
const HULL_FS = `uniform vec3 uC; uniform float uA; void main(){ gl_FragColor = vec4(uC * uA, 1.0); }`;
const _oN = new WeakMap();
function smoothNormalsGeo(geo) {
  if (_oN.has(geo)) return _oN.get(geo);
  const pos = geo.attributes.position, nor = geo.attributes.normal; const n = pos.count; const acc = new Map(); const key = (i) => `${Math.round(pos.getX(i) * 2000)},${Math.round(pos.getY(i) * 2000)},${Math.round(pos.getZ(i) * 2000)}`;
  for (let i = 0; i < n; i++) { const k = key(i); const a = acc.get(k) || [0, 0, 0]; a[0] += nor.getX(i); a[1] += nor.getY(i); a[2] += nor.getZ(i); acc.set(k, a); }
  const on = new Float32Array(n * 3); for (let i = 0; i < n; i++) { const a = acc.get(key(i)); const l = Math.hypot(a[0], a[1], a[2]) || 1; on[i * 3] = a[0] / l; on[i * 3 + 1] = a[1] / l; on[i * 3 + 2] = a[2] / l; }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', pos.clone()); g.setAttribute('oNormal', new THREE.BufferAttribute(on, 3)); if (geo.index) g.setIndex(geo.index.clone());
  g.userData.persistent = !!geo.userData.persistent; _oN.set(geo, g); return g;
}
export function goldOutline(ctx, objs, { t0 = 0, color = '#ffb43a', width = 0.02, outer = 2.4, peak = 0.9, hold = 0.5, rise = 0.12, settle = 0.6, t1 = null, fade = 0.25, opacity = null, sparkles = 8, filter = null, seed = 'gold' } = {}) {
  const grp = new THREE.Group(); grp.name = 'goldOutline'; const list = [].concat(objs);
  const mk = (w, a) => new THREE.ShaderMaterial({ uniforms: { uW: { value: w }, uC: { value: hdr(color, 1.6) }, uA: { value: a } }, vertexShader: HULL_VS, fragmentShader: HULL_FS, side: THREE.BackSide, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending });
  const inner = mk(width, 0), halo = mk(width * outer, 0); const hulls = []; const box = new THREE.Box3();
  for (const o of list) o.traverse((m) => {
    if (!m.isMesh || m.isSkinnedMesh || m.isInstancedMesh || !m.geometry || !m.geometry.attributes.normal || m.userData.fxHull) return;
    if (m.material && (m.material.blending === THREE.AdditiveBlending || (m.material.transparent && m.material.opacity < 0.5))) return;
    if (filter && !filter(m)) return;
    hulls.push(m);
  });
  for (const m of hulls) { const g = smoothNormalsGeo(m.geometry); for (const mat of [halo, inner]) { const h = new THREE.Mesh(g, mat); h.userData.fxHull = true; h.renderOrder = mat === inner ? 7 : 6; h.castShadow = h.receiveShadow = false; h.frustumCulled = false; m.add(h); } m.updateWorldMatrix(true, false); box.expandByObject(m); }
  let sp = null; if (sparkles > 0 && !box.isEmpty()) { const c = box.getCenter(new THREE.Vector3()), sz = box.getSize(new THREE.Vector3()); sp = sets.sparkles(ctx, { ...SPARK, px: [40, 75], center: c.toArray(), size: [sz.x + 0.3, sz.y + 0.25, sz.z + 0.3], count: sparkles, colors: GOLD, drift: [0.03, 0.07], seed: 'gold' + seed }); grp.add(sp); }
  const aAt = (t) => { if (opacity != null) return typeof opacity === 'function' ? opacity(t) : opacity; if (t < t0) return 0; let a = t < t0 + rise ? peak * outQuad((t - t0) / rise) : lerp(peak, hold, inOutSine((t - t0 - rise) / settle)); if (t1 != null) a *= 1 - smooth((t - t1) / fade); return a; };
  const update = (t) => { const a = aAt(t); inner.uniforms.uA.value = a; halo.uniforms.uA.value = a * 0.32; for (const m of hulls) for (const h of m.children) if (h.userData.fxHull) h.visible = a > 0.003; if (sp) { sp.update(t); sp.visible = a > 0.01; sp.children.forEach((s) => { s.material.opacity *= clamp01(a / Math.max(0.01, hold)); }); } };
  update(0); return { group: grp, update, meshes: hulls.length };
}

// ============================================================================================ PROPERTY LINE (fx_property_line)
// propertyLine(ctx, { a, b (ground points [x, z] or [x, y, z]), height: 2.6 (studs), opacity: 0.06 }) -> { group,
// update(t), bonk(t0, at), part(t0, at) }. A vertical additive curtain along the lot boundary: faint lavender-gold vertical
// streaks drifting up 0.3 studs/s, fading out at the top, and a gold line on the ground.
// bonk(t0, at): 3 concentric ripple rings spread from the contact point over 0.45 s (radius 0 -> 2 studs, opacity
// 0.6 -> 0) + a flash at the contact + a 12-sparkle burst (shake the camera yourself: ctx.camera.shake({ t0, dur: 0.3, px: 4 })).
// part(t0, at): the family carry-out: the curtain parts round `at` in a gold flash with 10 gold sparkles and a gold pulse
// running along the line both ways (s32's "gold ripple along it"), no ripple rings.
const PL_FS = `uniform float uT, uOp, uLen, uH; uniform vec4 uB0, uB1, uP; uniform vec3 uA, uBc, uGold; varying vec2 vP;
float h1(float x){ return fract(sin(x * 127.1 + 3.7) * 43758.5453); }
void main(){
  float x = vP.x, y = vP.y; float v = y / uH; float id = floor(x / 0.05); float fx = fract(x / 0.05);
  float line = exp(-pow((fx - 0.5) / 0.11, 2.0)) * (0.35 + 0.65 * h1(id));
  float dash = 0.5 + 0.5 * sin(y * 24.0 - uT * 2.3 + h1(id + 7.0) * 6.283); dash = 0.35 + 0.65 * dash * dash;
  float ends = smoothstep(0.0, 0.25, min(x + uLen * 0.5, uLen * 0.5 - x)); float vert = (1.0 - smoothstep(0.3, 1.0, v)) * smoothstep(0.0, 0.03, v) * (0.65 + 0.35 * (1.0 - v));
  vec3 col = mix(uA, uBc, step(0.62, h1(id + 3.0)));
  float a = uOp * (line * dash + 0.28) * vert * ends;
  // part: the curtain opens round the carry point, gold flash + a gold pulse along the line
  float pu = (uT - uP.x) / 0.55; float open = 0.0; vec3 add = vec3(0.0);
  if (uP.w > 0.5 && pu > -0.05 && pu < 1.0) { float dx = x - uP.y; open = exp(-pow(dx / 0.32, 2.0)) * smoothstep(-0.05, 0.12, pu) * (1.0 - smoothstep(0.55, 1.0, pu));
    float fl = exp(-pow(dx / 0.55, 2.0)) * exp(-pow((y - uP.z) / 0.5, 2.0)) * (pu < 0.12 ? pu / 0.12 : pow(1.0 - (pu - 0.12) / 0.88, 2.0));
    float run = exp(-pow((abs(dx) - pu * 2.2) / 0.12, 2.0)) * (1.0 - pu) * (1.0 - smoothstep(0.25, 0.6, v));
    add += uGold * (0.9 * fl + 0.75 * run) * vert; }
  a *= 1.0 - 0.92 * open;
  // bonk ripples
  for (int k = 0; k < 2; k++) { vec4 B = k == 0 ? uB0 : uB1; float bu = (uT - B.x) / 0.45; if (B.w < 0.5 || bu < 0.0 || bu > 1.0) continue;
    float d = length(vec2(x - B.y, y - B.z)); float rings = 0.0;
    for (int j = 0; j < 3; j++) { float rr = (bu - float(j) * 0.16) * 0.64; if (rr <= 0.0) continue; rings += exp(-pow((d - rr) / 0.022, 2.0)) * (1.0 - float(j) * 0.22); }
    float fall = pow(1.0 - bu, 1.5); add += mix(uBc, vec3(1.0, 0.97, 1.0), 0.5) * (1.1 * rings * fall + 0.45 * exp(-d * d / 0.02) * pow(1.0 - bu, 3.0)) * (1.0 - smoothstep(0.6, 1.0, v)); }
  gl_FragColor = vec4(col * a + add, 1.0);
}`;
const PLG_FS = `uniform float uA; uniform vec3 uGold; varying vec2 vP; uniform float uW; void main(){ float e = 1.0 - smoothstep(0.0, uW, abs(vP.y)); gl_FragColor = vec4(uGold * uA * e * e, 1.0); }`;
export function propertyLine(ctx, { a, b, height = 2.6, ground = null, opacity = 0.06, colorA = '#c9b8ff', colorB = '#ffd9a0', gold = '#ffd27a', lineWidth = 0.12, lineA = 0.35, seed = 'pline' } = {}) {
  const A = P3(a), B = P3(b); const gy = ground ?? A.y; A.y = B.y = gy; const len = A.distanceTo(B), H = height * S; const mid = A.clone().add(B).multiplyScalar(0.5); const ang = Math.atan2(B.x - A.x, B.z - A.z);
  const grp = new THREE.Group(); grp.name = 'propertyLine'; grp.position.copy(mid); grp.rotation.y = ang - PI / 2; // local +x runs A -> B
  const u = { uT: { value: 0 }, uOp: { value: opacity * 4.5 }, uLen: { value: len }, uH: { value: H }, uB0: { value: new THREE.Vector4() }, uB1: { value: new THREE.Vector4() }, uP: { value: new THREE.Vector4() }, uA: { value: hdr(colorA, 1) }, uBc: { value: hdr(colorB, 1) }, uGold: { value: hdr(gold, 1.6) } };
  const geo = new THREE.PlaneGeometry(len, H); geo.translate(0, H / 2, 0);
  const wall = new THREE.Mesh(geo, new THREE.ShaderMaterial({ uniforms: u, vertexShader: RING_VS, fragmentShader: PL_FS, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide })); wall.renderOrder = 8; grp.add(wall);
  const gu = { uA: { value: lineA }, uGold: { value: hdr(gold, 1.4) }, uW: { value: lineWidth * S } };
  const gl = new THREE.Mesh(new THREE.PlaneGeometry(len, lineWidth * S * 2), new THREE.ShaderMaterial({ uniforms: gu, vertexShader: RING_VS, fragmentShader: PLG_FS, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 }));
  gl.rotation.x = -PI / 2; gl.position.y = 0.012; gl.renderOrder = 3; grp.add(gl);
  const bonks = [], parts = [], fx = []; const fxGroup = new THREE.Group(); fxGroup.name = 'propertyLineBursts'; grp.updateMatrixWorld(true); const inv = () => new THREE.Matrix4().copy(grp.matrixWorld).invert();
  const local = (at) => P3(at).applyMatrix4(inv());
  const api = {
    group: grp, wall, length: len,
    bonk(t0, at) { const l = local(at); bonks.push([t0, l.x, Math.max(0.05, l.y), 1]); const w = P3(at); fx.push(sets.burst(ctx, { pos: w.toArray(), t0, dur: 0.35, count: 12, spread: 0.45, px: [28, 60], ringPx: [30, 320], ringColor: '#efe6ff', colors: ['#ffffff', '#e9dcff', '#ffe2c4'], corePx: 170, brightness: 2.0, seed: seed + 'bonk' + bonks.length })); fxGroup.add(fx[fx.length - 1]); return api; },
    part(t0, at) { const l = local(at); parts.push([t0, l.x, Math.max(0.1, l.y), 1]); const w = P3(at); fx.push(sets.burst(ctx, { pos: w.toArray(), t0, dur: 0.4, count: 10, spread: 0.5, px: [30, 64], ring: false, colors: GOLD, corePx: 240, brightness: 2.2, gravity: 0.1, seed: seed + 'part' + parts.length })); fxGroup.add(fx[fx.length - 1]); return api; },
    update(t) {
      u.uT.value = t; const pick = (arr) => { let best = null; for (const e of arr) if (t >= e[0] - 0.05 && (!best || e[0] > best[0])) best = e; return best; };
      const bs = bonks.filter((e) => t >= e[0] - 0.02 && t <= e[0] + 0.5).slice(-2); u.uB0.value.set(...(bs[0] || [0, 0, 0, 0])); u.uB1.value.set(...(bs[1] || [0, 0, 0, 0]));
      const p = pick(parts); u.uP.value.set(...(p || [0, 0, 0, 0]));
      let lf = 0; for (const e of [...bonks, ...parts]) { const q = (t - e[0]) / 0.5; if (q >= 0 && q <= 1) lf = Math.max(lf, Math.pow(1 - q, 2)); } gu.uA.value = lineA * (1 + 2.5 * lf);
      for (const f of fx) f.update(t);
    },
  };
  const outer = new THREE.Group(); outer.name = 'propertyLineFx'; outer.add(grp, fxGroup); api.group = outer;
  api.update(0); return api;
}

// ============================================================================================ SOIL (fx_soil)
// soilBurst(ctx, { pos, t0, count: 24, spread: 0.9 (studs), apex: 0.6 (studs), dur: 0.4, size: [0.022, 0.05] (studs, radius),
// y0 (start height, m), puffs: 3, puffColor: '#9a8066', puffOpacity: 0.55, rest: 1.0, ground } | { bursts: [{ pos, t0,
// count, spread, apex, y0, puffs }], ...shared }) -> { group, update(t) }. Instanced brown lumps thrown up on parabolas
// (land in ~dur s, tumble, rest, shrink away after `rest` s) + soft dust puffs. Mound tops, the GULP seal, the lawn moving.
const CRUMB_COLS = ['#6b4a2f', '#7a5638', '#5e3d26', '#8a6844', '#4a3020', '#6e4e34'];
function crumbMat() { return new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 0.95, metalness: 0 }); }
function dustTex(ctx) {
  return cache(ctx, 'dustTex', () => { const N = 96, c = (N - 1) / 2; const r = makeRng(hash32('dust'));
    const lobes = Array.from({ length: 7 }, () => [(r() - 0.5) * 0.7, (r() - 0.5) * 0.7, 0.35 + 0.3 * r()]);
    return dataTex(N, N, (x, y) => { const u = (x - c) / c, v = (y - c) / c; let a = 0; for (const [lx, ly, lr] of lobes) a = Math.max(a, 1 - Math.hypot(u - lx, v - ly) / lr); a = smooth(a * 1.6) * (1 - smooth((Math.hypot(u, v) - 0.7) / 0.3)); return [255, 255, 255, Math.round(255 * clamp01(a))]; }); });
}
export function soilBurst(ctx, o = {}) {
  const sh = { count: 24, spread: 0.9, apex: 0.6, dur: 0.4, size: [0.022, 0.05], y0: null, puffs: 3, puffColor: '#9a8066', puffOpacity: 0.55, puffSize: [0.8, 1.8], rest: 1.0, ground: null, grass: 0.12, seed: 'soil', ...o };
  const list = (o.bursts || [o]).map((b, i) => ({ ...sh, ...b, i }));
  const grp = new THREE.Group(); grp.name = 'soilBurst'; const total = list.reduce((s, b) => s + b.count, 0);
  const im = new THREE.InstancedMesh(cache(ctx, 'crumbGeo', () => { const g = new THREE.IcosahedronGeometry(1, 0); g.userData.persistent = true; return g; }), crumbMat(), Math.max(1, total)); im.frustumCulled = false; im.castShadow = false; im.receiveShadow = false; grp.add(im);
  const crumbs = []; const col = new THREE.Color();
  for (const b of list) {
    const r = makeRng(hash32('soil', b.seed, b.i, b.t0)); const P = P3(b.pos); const gy = b.ground ?? P.y; const y0 = b.y0 ?? P.y;
    for (let k = 0; k < b.count; k++) {
      const th = r() * PI * 2, hs = b.spread * S * (0.35 + 0.65 * r()); const T = b.dur * (0.75 + 0.5 * r()); const ap = b.apex * S * (0.45 + 0.55 * r());
      const g = (8 * ap) / (T * T), vy = (4 * ap) / T; const tl = (vy + Math.sqrt(vy * vy + 2 * g * Math.max(0, y0 - gy))) / g;
      const off = new THREE.Vector3(Math.cos(th), 0, Math.sin(th)).multiplyScalar(b.spread * S * 0.18 * r());
      crumbs.push({ t0: b.t0 + 0.03 * r(), p0: P.clone().add(off).setY(y0), vx: (Math.cos(th) * hs) / tl, vz: (Math.sin(th) * hs) / tl, vy, g, tl, gy, size: (b.size[0] + (b.size[1] - b.size[0]) * r()) * S, rot: [r() * 6, r() * 6, r() * 6], w: [(r() - 0.5) * 20, (r() - 0.5) * 20, (r() - 0.5) * 20], rest: b.rest * (0.8 + 0.4 * r()), sq: 0.6 + 0.4 * r() });
      col.set(r() < b.grass ? '#4f7a3a' : CRUMB_COLS[Math.floor(r() * CRUMB_COLS.length)]); im.setColorAt(crumbs.length - 1, col);
    }
  }
  if (im.instanceColor) im.instanceColor.needsUpdate = true;
  const puffs = []; const dt = dustTex(ctx);
  for (const b of list) { const r = makeRng(hash32('puff', b.seed, b.i, b.t0)); const P = P3(b.pos); for (let k = 0; k < b.puffs; k++) {
    const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: dt, color: new THREE.Color(b.puffColor), transparent: true, depthWrite: false, opacity: 0, fog: true })); s.renderOrder = 9;
    const a = r() * PI * 2; s.userData.d = { t0: b.t0 + 0.02 + 0.06 * r(), p: P.clone().add(new THREE.Vector3(Math.cos(a), 0, Math.sin(a)).multiplyScalar(b.spread * S * 0.3 * r())).setY((b.y0 ?? P.y) + 0.1 * S), dir: new THREE.Vector3(Math.cos(a), 0, Math.sin(a)), s0: b.puffSize[0] * S * (0.8 + 0.4 * r()), s1: b.puffSize[1] * S * (0.8 + 0.4 * r()), life: 0.6 + 0.3 * r(), op: b.puffOpacity, rot: r() * 6 };
    s.material.rotation = s.userData.d.rot; grp.add(s); puffs.push(s); } }
  const M4 = new THREE.Matrix4(), Q = new THREE.Quaternion(), E = new THREE.Euler(), Pp = new THREE.Vector3(), Sc = new THREE.Vector3();
  const update = (t) => {
    crumbs.forEach((c, i) => {
      const a = t - c.t0; let s = c.size; if (a < 0) s = 0; else if (a > c.tl + c.rest) s *= 1 - clamp01((a - c.tl - c.rest) / 0.25);
      const fl = Math.min(a, c.tl); Pp.set(c.p0.x + c.vx * Math.max(0, fl), Math.max(c.gy + c.size * 0.5, c.p0.y + c.vy * Math.max(0, fl) - 0.5 * c.g * Math.max(0, fl) ** 2), c.p0.z + c.vz * Math.max(0, fl));
      const rt = Math.max(0, fl); E.set(c.rot[0] + c.w[0] * rt, c.rot[1] + c.w[1] * rt, c.rot[2] + c.w[2] * rt); Q.setFromEuler(E); Sc.set(s, s * c.sq, s); M4.compose(Pp, Q, Sc); im.setMatrixAt(i, M4);
    });
    im.instanceMatrix.needsUpdate = true;
    for (const s of puffs) { const d = s.userData.d; const u = (t - d.t0) / d.life; s.visible = u > 0 && u < 1; if (!s.visible) continue; const k = outQuad(u); s.position.copy(d.p).addScaledVector(d.dir, 0.25 * S * k).add(new THREE.Vector3(0, 0.35 * S * k, 0)); const sz = lerp(d.s0, d.s1, k); s.scale.set(sz, sz * 0.8, 1); s.material.opacity = d.op * Math.min(1, u / 0.08) * Math.pow(1 - u, 1.4); }
  };
  update(-1); return { group: grp, update, count: crumbs.length };
}

// moundCrumbs(ctx, field, { moles: 'all' | [i], rate: 16 (crumbs/s while travelling), life: 0.5, pops: true, popCount: 10,
// size }) -> { group, update(t) }: soil crumbs flicked off the fronts of travelling mounds (creatures.moleField) and a
// pop of crumbs when a mound rises. Reads the field's mole plans (travel / rise); call after field.update(t).
function fieldPoint(field, x, z, y = 0) { field.group.updateWorldMatrix(true, false); return field.group.localToWorld(new THREE.Vector3(x * S, y * S, z * S)); }
// The mole's planned ground position at time t (travel only; ignores push-backs): { x, z, hx, hz (field studs), moving }
export function moleAt(field, i, t) {
  const m = field.moles[i]; let x = m.at[0], z = m.at[1], hx = m.h0[0], hz = m.h0[1], moving = false;
  if (m.path) { const end = m.sStop != null ? m.sStop : m.len; const s = Math.max(0, Math.min(end, m.speed * (t - m.t0))); moving = t > m.t0 && s < end; const u = clamp01(s / m.len); const q = m.path.getPointAt(u), tg = m.path.getTangentAt(Math.min(0.999, Math.max(0.001, u))); x = q.x; z = q.z; const l = Math.hypot(tg.x, tg.z) || 1; hx = tg.x / l; hz = tg.z / l; }
  return { x, z, hx, hz, moving };
}
export const moleWorld = (field, i, t, y = 0) => { const s = moleAt(field, i, t); return fieldPoint(field, s.x, s.z, y); };
export function moundCrumbs(ctx, field, { moles = 'all', rate = 16, life = 0.5, apex = 0.5, size = [0.03, 0.06], pops = true, popCount = 10, seed = 'mc' } = {}) {
  const idx = moles === 'all' ? field.moles.map((m, i) => i) : moles; const grp = new THREE.Group(); grp.name = 'moundCrumbs';
  const trav = idx.filter((i) => field.moles[i].path); const per = Math.ceil(rate * life) + 2; const N = Math.max(1, trav.length * per);
  const im = new THREE.InstancedMesh(cache(ctx, 'crumbGeo', () => { const g = new THREE.IcosahedronGeometry(1, 0); g.userData.persistent = true; return g; }), crumbMat(), N); im.frustumCulled = false; grp.add(im);
  const col = new THREE.Color(); for (let k = 0; k < N; k++) { col.set(CRUMB_COLS[hash32(seed, k) % CRUMB_COLS.length]); im.setColorAt(k, col); } if (im.instanceColor) im.instanceColor.needsUpdate = true;
  let pop = null;
  if (pops) { const bursts = idx.filter((i) => field.moles[i].rise).map((i) => { const m = field.moles[i]; const s = moleAt(field, i, m.rise[0]); return { pos: fieldPoint(field, s.x, s.z), y0: m.height * m.scale * S * 0.7, t0: m.rise[0] + m.rise[1] * 0.35, count: popCount, spread: 0.9 * m.scale, apex: 0.55 * m.scale, puffs: 1, puffOpacity: 0.35 }; });
    if (bursts.length) { pop = soilBurst(ctx, { bursts, seed: seed + 'pop', rest: 1.6 }); grp.add(pop.group); } }
  const M4 = new THREE.Matrix4(), Q = new THREE.Quaternion(), E = new THREE.Euler(), Pp = new THREE.Vector3(), Sc = new THREE.Vector3();
  const update = (t) => {
    let slot = 0;
    trav.forEach((i, j) => {
      const m = field.moles[i]; const end = m.t0 + (m.sStop != null ? m.sStop : m.len) / m.speed;
      const k0 = Math.max(0, Math.ceil((t - life - m.t0) * rate)), k1 = Math.floor((Math.min(t, end) - m.t0) * rate);
      for (let n = 0; n < per; n++) {
        const k = k0 + n; const base = j * per + (((k % per) + per) % per); const tau = m.t0 + k / rate; const a = t - tau;
        if (k > k1 || a < 0 || a > life) { M4.makeScale(0, 0, 0); im.setMatrixAt(base, M4); continue; }
        const s = moleAt(field, i, tau); const h = hash32(seed, i, k); const r1 = (h % 1000) / 1000, r2 = ((h >>> 10) % 1000) / 1000, r3 = ((h >>> 20) % 1000) / 1000;
        const sc = m.scale; const side = r1 < 0.5 ? -1 : 1; const fx = s.x + s.hx * 0.55 * sc, fz = s.z + s.hz * 0.55 * sc;
        const P0 = fieldPoint(field, fx, fz, m.height * sc * 0.45); const lat = new THREE.Vector3(-s.hz, 0, s.hx).transformDirection(field.group.matrixWorld);
        const fwd = new THREE.Vector3(s.hx, 0, s.hz).transformDirection(field.group.matrixWorld);
        const T = life * (0.7 + 0.3 * r2), ap = apex * S * sc * (0.5 + 0.5 * r3), g = (8 * ap) / (T * T), vy = (4 * ap) / T; const tt = Math.min(a, T);
        Pp.copy(P0).addScaledVector(lat, side * (0.25 + 0.5 * r2) * S * sc * (tt / T) * 1.6).addScaledVector(fwd, (0.1 + 0.3 * r1) * S * sc * (tt / T)); Pp.y = Math.max(0.01, P0.y + vy * tt - 0.5 * g * tt * tt);
        const sz = (size[0] + (size[1] - size[0]) * r3) * S * sc * (a > life - 0.1 ? (life - a) / 0.1 : 1); E.set(r1 * 6 + a * 9, r2 * 6 + a * 7, r3 * 6); Q.setFromEuler(E); Sc.set(sz, sz * 0.75, sz); M4.compose(Pp, Q, Sc); im.setMatrixAt(base, M4); slot++;
      }
    });
    im.instanceMatrix.needsUpdate = true; if (pop) pop.update(t);
  };
  update(0); return { group: grp, update };
}

// ============================================================================================ PRICE STICKER FLUTTER (fx_sticker)
// flutter(ctx, { text: '$4.99', tex, from, to, t0, dur: 0.4, size: 0.5 (studs, width), swing: 35 (deg), turns: 1.5,
// yaw }) -> Mesh with update(t). A paper quad falls from `from` to `to` swinging side to side (+-swing, decaying) and lands
// flat on the soil (stays there). Hidden before t0.
export function stickerTex(ctx, text = '$4.99') {
  return cache(ctx, 'sticker:' + text, () => { const c = document.createElement('canvas'); c.width = 256; c.height = 128; const g = c.getContext('2d');
    g.fillStyle = '#fbfaf6'; g.fillRect(0, 0, 256, 128); g.strokeStyle = '#e0261e'; g.lineWidth = 10; g.strokeRect(8, 8, 240, 112);
    g.fillStyle = '#e0261e'; g.font = 'bold 66px "DejaVu Sans", sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(text, 128, 70); g.fillStyle = '#9a9aa2'; g.font = 'bold 18px "DejaVu Sans", sans-serif'; g.fillText('SALE  •  GARDEN', 128, 24);
    g.fillStyle = 'rgba(80,60,40,0.18)'; g.beginPath(); g.moveTo(0, 128); g.lineTo(60, 128); g.lineTo(0, 90); g.fill(); return canvasTex(c); });
}
export function flutter(ctx, { text = '$4.99', tex = null, from, to, t0 = 0, dur = 0.4, size = 0.5, swing = 35, turns = 1.5, yaw = null, seed = 'flutter' } = {}) {
  const w = size * S, h = w * 0.5; const r = makeRng(hash32('flutter', seed)); const A = P3(from), B = P3(to); const yawF = yaw ?? (r() - 0.5) * 1.6;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshStandardMaterial({ map: tex || stickerTex(ctx, text), roughness: 0.75, side: THREE.FrontSide, polygonOffset: true, polygonOffsetFactor: -2 })); m.name = 'priceStickerFlutter'; m.renderOrder = 4;
  const back = new THREE.Mesh(m.geometry, new THREE.MeshStandardMaterial({ color: '#f4f0ea', roughness: 0.8, side: THREE.FrontSide, polygonOffset: true, polygonOffsetFactor: -2 })); back.rotation.y = PI; back.renderOrder = 4; m.add(back);
  const side = new THREE.Vector3(Math.cos(yawF), 0, -Math.sin(yawF)); const amp = 0.55 * w;
  m.update = (t) => {
    const u = (t - t0) / dur; m.visible = u >= 0; if (!m.visible) return; const k = clamp01(u); const ph = k * turns * 2 * PI;
    m.position.copy(A).lerp(B, 0.45 * k + 0.55 * k * k).addScaledVector(side, Math.sin(ph) * amp * (1 - k)); m.position.y = Math.max(B.y + 0.003, m.position.y);
    m.rotation.set(-PI / 2 + (1 - smooth(k)) * 0.75 * Math.cos(ph * 0.5), yawF, swing * DEG * Math.sin(ph + PI / 2) * (1 - k), 'YXZ');
  };
  m.group = m; m.update(-1); return m;
}

// ============================================================================================ GULP (soil side of moleField.swallow)
// gulp(ctx, { field, index, target, at, t0, depth: 2.2, radius: 0.85, swallow: true, wobble: 8, sticker: { t0, to } | null })
// -> { group, update(t), cues, field }. The ground opens (dark throat inside the turf lips), the target (plastic gnome) is
// pulled down with a jerky wobble, crumbs fly as the lips rise, a dirt puff + crumb burp on the seal (t0 + 0.24) and a
// small second burp; optional price-sticker flutter. With field + index it calls field.swallow(index, target, t0) (pass
// swallow: false if the shot already did); without a field it builds its own small mole field (a mound surges in from
// the side) and updates it. Call field.update(t) BEFORE gulp.update(t) when you own the field.
export function gulp(ctx, { field = null, index = null, target = null, at = null, t0 = 0, depth = 2.2, radius = 0.85, swallow = true, wobble = 8, sticker = null, from = null, seed = 'gulp' } = {}) {
  const grp = new THREE.Group(); grp.name = 'gulpFx'; const P = at ? P3(at) : worldOf(target, new THREE.Vector3()); // ground = the target's base (raised bed soil)
  let F = field, own = false, idx = index;
  if (!F) { own = true; F = C.moleField(ctx, { center: [P.x, P.z], size: [12, 12], res: 64, heads: false, seed }); const fr = from ? P3(from) : P.clone().add(new THREE.Vector3(-1.6, 0, 0.4)); idx = F.add({ at: [fr.x, fr.z] }); F.travel(idx, [[fr.x, fr.z], [P.x, P.z]], t0 - 0.55, 3.6); grp.add(F.group); }
  if (swallow) F.swallow(idx, target || [P.x, P.z], t0, { depth, radius });
  const R = radius * S;
  const throat = new THREE.Mesh(new THREE.CircleGeometry(1, 40), new THREE.MeshBasicMaterial({ map: ctx.tex.radialGlow({ falloff: 0.7 }), color: '#100804', transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -6, polygonOffsetUnits: -6 }));
  throat.rotation.x = -PI / 2; throat.position.set(P.x, P.y + 0.01, P.z); throat.renderOrder = 2; grp.add(throat);
  const soil = soilBurst(ctx, { seed: seed + 'soil', bursts: [
    { pos: P, t0: t0 + 0.02, count: 16, spread: radius * 1.7, apex: 0.55, y0: P.y + 0.15 * S, puffs: 1, puffOpacity: 0.3 },
    { pos: P, t0: t0 + 0.24, count: 22, spread: 1.1, apex: 0.75, y0: P.y + 0.3 * S, puffs: 4, puffOpacity: 0.55 },
    { pos: P, t0: t0 + 0.42, count: 8, spread: 0.6, apex: 0.35, y0: P.y + 0.15 * S, puffs: 1, puffOpacity: 0.3 } ], rest: 2.5 });
  grp.add(soil.group);
  const toCam = sticker && !sticker.to ? (() => { const c = sets.camBasis(ctx).pos; const d = new THREE.Vector3(c.x - P.x, 0, c.z - P.z).normalize(); return P.clone().addScaledVector(d, 1.15 * S).add(new THREE.Vector3(-d.z * 0.35 * S, 0.006, d.x * 0.35 * S)); })() : null;
  const st = sticker ? flutter(ctx, { text: sticker.text || '$4.99', from: sticker.from || P.clone().add(new THREE.Vector3(0, 1.1 * S, 0)), to: sticker.to || toCam, t0: sticker.t0 ?? t0 + 0.47, dur: sticker.dur ?? 0.4, seed: seed + 'st' }) : null;
  if (st) grp.add(st);
  const rz0 = target && target.isObject3D ? target.rotation.z : 0, rx0 = target && target.isObject3D ? target.rotation.x : 0;
  const update = (t) => {
    if (own) F.update(t);
    const u = t - t0; let k = 0;
    if (u >= -0.02 && u < 0.12) k = outQuad((u + 0.02) / 0.14); else if (u >= 0.12 && u < 0.26) k = 1 - inQuad((u - 0.12) / 0.14);
    throat.visible = k > 0.01; throat.scale.setScalar(R * 0.95 * k);
    if (target && target.isObject3D) { const a = clamp01((u - 0.02) / 0.22); const wb = u > 0 && u < 0.26 ? wobble * DEG * Math.sin(u * 55) * (1 - a) : 0; target.rotation.z = rz0 + wb; target.rotation.x = rx0 + (u > 0 && u < 0.26 ? 0.5 * wb : 0); }
    soil.update(t); if (st) st.update(t);
  };
  update(-1);
  return { group: grp, update, field: F, index: idx, sticker: st, cues: [{ t: t0, kind: 'gulp' }, { t: t0 + 0.24, kind: 'seal' }, { t: t0 + 0.42, kind: 'burp' }].concat(st ? [{ t: (sticker.t0 ?? t0 + 0.47) + (sticker.dur ?? 0.4), kind: 'sticker_land' }] : []) };
}

// ============================================================================================ DEW TEAR (fx_tear)
// dewTear(ctx, gnome, { eye: 'L' | 'R', t0, dur: 0.6, swell: 0.15, size: 0.26 (x eye radius), opacity: 0.42 }) -> { group, update(t) }.
// A glossy water drop wells at the lower lid for `swell` s, then slides down the cheek into the beard, leaving a wet
// trail; a catchlight sprite keeps it readable at night. The path is ray-cast onto the face once (head-local, so it
// follows head turns). Material: MeshPhysical, transmission-free (roughness 0.05, clearcoat 1).
export function dewTear(ctx, gnome, { eye = 'L', t0 = 0, dur = 1.0, swell = 0.15, size = 0.5, opacity = 0.9, seed = 'tear' } = {}) {
  size = Math.max(size, 0.5); opacity = Math.max(opacity, 0.9); dur = Math.max(dur, 1.0); // review: the tear must read over the white beard
  const head = gnome.getObjectByName('gnomeHead') || gnome; const ball = gnome.getObjectByName('ball' + eye); if (!ball) throw new Error('dewTear: no eye ' + eye);
  gnome.updateWorldMatrix(true, true);
  const hs = head.getWorldScale(new THREE.Vector3()).x; const bw = ball.getWorldPosition(new THREE.Vector3()); const e = head.worldToLocal(bw.clone());
  ball.geometry.computeBoundingSphere(); const er = (ball.geometry.boundingSphere.radius * ball.getWorldScale(new THREE.Vector3()).x) / hs; // eye radius, head-local
  const sgn = eye === 'L' ? 1 : -1;
  const meshes = []; head.traverse((o) => { if (o.isMesh && !/^ball|lash|eyeGlint|eyeHalo/i.test(o.name) && !(o.material && o.material.transparent && o.material.opacity < 0.9)) meshes.push(o); });
  const rc = new THREE.Raycaster(); const fwdW = new THREE.Vector3(0, 0, 1).transformDirection(head.matrixWorld).normalize();
  const offs = [[0.05, -1.08], [0.18, -1.45], [0.3, -1.95], [0.42, -2.55], [0.5, -3.2], [0.55, -3.9]];
  const pts = offs.map(([dx, dy]) => {
    const l = new THREE.Vector3(e.x + sgn * dx * er, e.y + dy * er, e.z + 4 * er); const o = head.localToWorld(l.clone()); rc.set(o, fwdW.clone().negate()); const hit = rc.intersectObjects(meshes, false)[0];
    if (!hit) return new THREE.Vector3(e.x + sgn * dx * er, e.y + dy * er, e.z + er * 0.6);
    const n = hit.face ? hit.face.normal.clone().transformDirection(hit.object.matrixWorld) : fwdW.clone(); const p = hit.point.clone().addScaledVector(n, er * size * 0.55); return head.worldToLocal(p);
  });
  const curve = new THREE.CatmullRomCurve3(pts, false, 'centripetal');
  const rD = er * size; const mat = new THREE.MeshPhysicalMaterial({ color: '#8fd0ff', roughness: 0.05, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.03, transparent: true, opacity, emissive: '#2a6aa8', emissiveIntensity: 0.8, depthWrite: false });
  const drop = new THREE.Mesh(new THREE.SphereGeometry(rD, 20, 14), mat); drop.renderOrder = 9; drop.name = 'dewTear'; head.add(drop);
  const TS = 48, RS = 6; const trailGeo = new THREE.TubeGeometry(curve, TS, rD * 0.32, RS, false); const trail = new THREE.Mesh(trailGeo, new THREE.MeshPhysicalMaterial({ color: '#9ad4ff', roughness: 0.04, clearcoat: 1, transparent: true, opacity: 0.75, emissive: '#3a78b8', emissiveIntensity: 0.8, depthWrite: false })); trail.renderOrder = 8; head.add(trail);
  const glint = pxSprite(addSpriteMat(ctx.tex.sparkle({ points: 4, sharpness: 22, core: 0.7 }), '#ffffff', 1.8, { depthTest: false }), 10); glint.renderOrder = 31; const sheen = pxSprite(addSpriteMat(ctx.tex.radialGlow({ falloff: 2.0 }), '#dcecff', 0.9, { depthTest: true }), 26); sheen.renderOrder = 30; const grp = new THREE.Group(); grp.add(sheen, glint); grp.name = 'dewTearFx';
  const tmp = new THREE.Vector3();
  const update = (t) => {
    head.updateWorldMatrix(true, false); const a = t - t0; const on = a >= 0 && a < dur + 0.12; drop.visible = glint.visible = sheen.visible = on; trail.visible = a > swell;
    if (!on) { trail.geometry.setDrawRange(0, a >= dur ? Infinity : 0); return; }
    let u = 0, sc = 1;
    if (a < swell) { sc = outBack(a / swell) * (0.55 + 0.45 * (a / swell)); }
    else { const v = clamp01((a - swell) / (dur - swell)); u = 0.55 * v * v + 0.45 * v; if (a > dur) sc = 1 - clamp01((a - dur) / 0.12); }
    const p = curve.getPointAt(Math.min(0.999, u)); const tg = curve.getTangentAt(Math.min(0.999, Math.max(0.001, u)));
    drop.position.copy(p); drop.quaternion.setFromUnitVectors(new THREE.Vector3(0, -1, 0), tg.clone().normalize()); const el = a < swell ? 1 + 0.15 * (a / swell) : 1.25; drop.scale.set(sc, sc * el, sc);
    trail.geometry.setDrawRange(0, Math.floor(u * TS) * RS * 6);
    head.localToWorld(tmp.copy(p).add(new THREE.Vector3(-0.3 * rD, 0.35 * rD, 0.5 * rD))); glint.position.copy(tmp); glint.userData.px = 32 + 10 * sc; glint.material.opacity = 0.95 * sc; glint.material.rotation = 0.4; head.localToWorld(tmp.copy(p)); sheen.position.copy(tmp); sheen.userData.px = 34 * sc + 10; sheen.material.opacity = 0.5 * sc;
  };
  update(-1); return { group: grp, update, drop, trail };
}

// ============================================================================================ WINDOW STATE (fx_window_dark)
// windowState(win, level): win = a heroLot root (Theo's window: room glow, nightlight, glass haze, lamp shade) or its
// ep01.theo object; level 0 = dark, 1 = lit. windowDark(ctx, win, { t0, t1: null (restore), from: 1, to: 0 }) ->
// { update(t), cues }: the 1-frame light-state switch on the event frame.
export function windowState(win, level) {
  const th = win && win.ep01 ? win.ep01.theo : win && win.setLevel ? win : null;
  if (th) { th.setLevel(level); return; }
  if (win && win.isMesh && win.material) { if (!win.userData.fxMat) { win.userData.fxMat = win.material.clone(); win.userData.fxE = win.material.emissiveIntensity ?? 1; win.material = win.userData.fxMat; } if ('emissiveIntensity' in win.material) win.material.emissiveIntensity = win.userData.fxE * level; }
}
export function windowDark(ctx, win, { t0 = 0, t1 = null, from = 1, to = 0 } = {}) {
  const update = (t) => windowState(win, t >= t0 && (t1 == null || t < t1) ? to : from);
  update(0); return { update, group: new THREE.Group(), cues: [{ t: t0, kind: 'light_off' }].concat(t1 != null ? [{ t: t1, kind: 'light_on' }] : []) };
}

// ============================================================================================ LIGHT WAVE + FWOOM (fx_fwoom)
// lightWave(ctx, { center, t0, speed: 8 (studs/s), height: 1.0 (studs), width: 1.4 (studs), maxR: 40 (studs), core:
// '#ffc56a', trail: '#ff8ac8', intensity: 1, sparkles: 60, sector: [deg0, deg1] | 'camera' (sparkles only where seen),
// light: 2.5 cd | 0 (a point light riding the front toward the camera: lights every blade it passes), ground }) ->
// { group, update(t), radiusAt(t) (metres) }. A thick additive ring wall rolling outward over the grass (gold core at
// the front, pink trailing edge), a band of light on the grass under it (light boost: the blades are lit, not washed) with
// a crisp additive line at the front, sparkles kicked up at the front.
const WAVE_VS = `varying vec2 vUv; varying vec3 vW; void main(){ vUv = uv; vec4 w = modelMatrix * vec4(position, 1.0); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`;
const WALL_VS = `varying vec2 vUv; varying vec3 vN, vV; void main(){ vUv = uv; vec4 w = modelMatrix * vec4(position, 1.0); vN = normalize(mat3(modelMatrix) * normal); vV = normalize(cameraPosition - w.xyz); gl_Position = projectionMatrix * viewMatrix * w; }`;
const WAVE_FS = `uniform vec3 uC; uniform float uA, uT; varying vec2 vUv; varying vec3 vN, vV; void main(){ float v = vUv.y; float face = smoothstep(0.04, 0.55, abs(dot(normalize(vN), normalize(vV)))); // fade at the silhouette: no hard edge where the wall grazes the lens
  float a = pow(1.0 - v, 1.7) * smoothstep(0.0, 0.04, v) * face * (0.8 + 0.2 * sin(vUv.x * 6.2832 * 40.0 + uT * 3.0) * sin(vUv.x * 6.2832 * 11.0 - uT * 1.7)); gl_FragColor = vec4(uC * uA * a, 1.0); }`;
const BAND_FS = `uniform vec3 uC, uP, uCen; uniform float uR, uW, uA, uMode; varying vec2 vUv; varying vec3 vW; void main(){ float d = length(vW.xz - uCen.xz); float b = uR - d; if (b < -0.12 || b > uW * 3.5) discard;
  float body = smoothstep(-0.08, 0.02, b) * exp(-max(b, 0.0) / (uW * 0.9)); float line = exp(-pow((b - 0.02) / 0.04, 2.0)); vec3 c = mix(uC, uP, smoothstep(0.0, uW * 1.6, b));
  gl_FragColor = vec4(uMode < 0.5 ? c * body * uA : uC * line * uA, 1.0); }`;
export function lightWave(ctx, { center, t0 = 0, speed = 8, height = 1.0, width = 1.4, maxR = 40, core = '#ffc56a', trail = '#ff8ac8', intensity = 1, sparkles = 60, sector = 'camera', light = 2.5, ground = null, seed = 'wave' } = {}) {
  const Cn = P3(center); const gy = ground ?? Cn.y; Cn.y = gy; const v = speed * S, H = height * S, Wd = width * S, RM = maxR * S;
  const grp = new THREE.Group(); grp.name = 'lightWave';
  const wallGeo = new THREE.CylinderGeometry(1, 1, 1, 160, 1, true); wallGeo.translate(0, 0.5, 0);
  const mkWall = (col, a) => new THREE.Mesh(wallGeo, new THREE.ShaderMaterial({ uniforms: { uC: { value: hdr(col, 1.4) }, uA: { value: a }, uT: { value: 0 } }, vertexShader: WALL_VS, fragmentShader: WAVE_FS, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide }));
  const wFront = mkWall(core, 0.9 * intensity), wBack = mkWall(trail, 0.3 * intensity); [wFront, wBack].forEach((w) => { w.renderOrder = 9; w.frustumCulled = false; grp.add(w); });
  const bandMat = (mode, a) => { const m = new THREE.ShaderMaterial({ uniforms: { uC: { value: new THREE.Color(core) }, uP: { value: new THREE.Color(trail) }, uCen: { value: Cn.clone() }, uR: { value: 0 }, uW: { value: Wd }, uA: { value: a }, uMode: { value: mode } }, vertexShader: WAVE_VS, fragmentShader: BAND_FS, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 }); if (mode === 0) boostBlend(m); return m; };
  const bandGeo = new THREE.PlaneGeometry(1, 1); const bands = [[bandMat(0, 1.6 * intensity), 1.6], [bandMat(1, 1.6 * intensity), 1.6]].map(([m, a]) => { const b = new THREE.Mesh(bandGeo, m); b.rotation.x = -PI / 2; b.renderOrder = 4; b.frustumCulled = false; b.userData.a = a; grp.add(b); return b; });
  const B = sets.camBasis(ctx); const camAng = Math.atan2(B.pos.z - Cn.z, B.pos.x - Cn.x);
  const [a0, a1] = sector === 'camera' ? [camAng - 75 * DEG, camAng + 75 * DEG] : sector ? [sector[0] * DEG, sector[1] * DEG] : [0, 2 * PI];
  const r = makeRng(hash32('wave', seed)); const sps = [];
  for (let i = 0; i < sparkles; i++) { const s = pxSprite(addSpriteMat(sparkTex(ctx, r() < 0.5 ? 6 : 8), ['#ffd27a', '#fff2d8', '#ff9ad5', '#ffe2a8'][i % 4], 2.0, { depthTest: true }), 0); s.renderOrder = 10; s.userData.d = { a: a0 + (a1 - a0) * r(), r: RM * Math.sqrt(0.02 + 0.98 * r()) * 0.95, life: 0.55 + 0.35 * r(), h: (0.4 + 0.9 * r()) * H, px: 36 + 44 * r(), per: 0.35 + 0.3 * r(), ph: r(), out: 0.15 + 0.25 * r() }; grp.add(s); sps.push(s); }
  let pl = null; if (light) { pl = new THREE.PointLight(core, 0, 0, 2); grp.add(pl); }
  const radiusAt = (t) => Math.max(0, (t - t0) * v);
  const update = (t) => {
    const R = radiusAt(t); const on = t >= t0 && R < RM; grp.visible = on; if (!on) return;
    const fade = (1 - smooth((R - RM * 0.75) / (RM * 0.25))) * smooth((t - t0) / 0.06);
    wFront.position.copy(Cn); wFront.scale.set(Math.max(0.01, R), H, Math.max(0.01, R)); wFront.material.uniforms.uA.value = 0.9 * intensity * fade; wFront.material.uniforms.uT.value = t;
    const Rb = Math.max(0.01, R - Wd * 0.6); wBack.position.copy(Cn); wBack.scale.set(Rb, H * 0.7, Rb); wBack.material.uniforms.uA.value = 0.3 * intensity * fade; wBack.material.uniforms.uT.value = t;
    for (const b of bands) { b.position.set(Cn.x, gy + 0.016, Cn.z); b.scale.set(2 * (R + 0.2), 2 * (R + 0.2), 1); b.material.uniforms.uR.value = R; b.material.uniforms.uA.value = b.userData.a * intensity * fade; }
    for (const s of sps) { const d = s.userData.d; const age = t - (t0 + d.r / v); s.visible = age > 0 && age < d.life; if (!s.visible) continue; const k = age / d.life; const rr = d.r + d.out * S * k; s.position.set(Cn.x + Math.cos(d.a) * rr, gy + 0.05 + d.h * outQuad(k), Cn.z + Math.sin(d.a) * rr); const tw = 0.5 + 0.5 * Math.sin((t / d.per + d.ph) * 2 * PI); s.userData.px = d.px * (0.7 + 0.5 * tw) * (1 - 0.4 * k); s.material.opacity = (k < 0.1 ? k / 0.1 : 1 - (k - 0.1) / 0.9) * (0.6 + 0.4 * tw) * fade; }
    if (pl) { pl.intensity = light * fade; pl.position.set(Cn.x + Math.cos(camAng) * R, gy + 0.6 * H, Cn.z + Math.sin(camAng) * R); }
  };
  update(-1); return { group: grp, update, radiusAt, center: Cn, speed: v };
}
// FWOOM lantern curve (bible P3): level `base` -> `peak` in 0.15 s, back down to `end` by 1.5 s (shape 'flash': a fast
// exponential fall, 0.32 s; 'sine': the bible's inOutSine, which kept the frame white for 0.6 s); an optional second,
// smaller pulse at t2 (s77 "flared"). Returns the lantern level (K.setLantern units: 1 = lit, 4-6 = FWOOM).
export function fwoomLevel(t, t0, { base = 1, peak = 6, end = 1.5, t2 = null, peak2 = 3, shape = 'flash' } = {}) {
  const u = t - t0; let k; if (u < 0) k = base; else if (u < 0.15) k = base + (peak - base) * (u / 0.15);
  else { const v = (u - 0.15) / 1.5; k = end + (peak - end) * (shape === 'sine' ? 1 - inOutSine(v) : Math.exp(-(u - 0.15) / 0.32) * (1 - smooth(v))); }
  if (t2 != null && t >= t2) { const w = t - t2; const p = w < 0.08 ? w / 0.08 : Math.pow(Math.max(0, 1 - (w - 0.08) / 0.6), 1.5); k = Math.max(k, k + (peak2 - k) * p); }
  return k;
}
// fwoom(ctx, { gnome, t0, t2: second pulse, center: ground point (default: the lantern), field, moles: 'all' | [i],
// speed: 8, stagger: 0.04, sinkDur: 0.5, burst/streaks/dust: true, grade: 'magic' | false, frames: 8, rig, hemi, wave: {...},
// peak: 6, cd: [2.2, 11, 3], ring: 5 }) -> { group, update(t), cues, wave, lantern }.
// The lantern flares white-gold (glass x2.4 -> x14; the light follows the bible's 8 -> 50 -> 10 curve shape, scaled to
// 2.2 -> 11 -> 3 cd: the bible values blew a 1 m close-up to p50 217; pass cd for wide shots), a burst ring + streaks + gold/pink motes fly
// out, the grade swings to magic in 8 frames, a lightWave rolls out from the bed and every mole of `field` sinks as the
// front reaches it (field.sink: deflate 0.5 s, eyes wink out 2 frames 0.12 s later). cues: one 'blip' per mole.
export function fwoom(ctx, { gnome, t0 = 0, t2 = null, center = null, field = null, moles = 'all', speed = 8, stagger = 0.04, sinkDur = 0.5, burst = true, streaks: doStreaks = true, dust = true, grade = 'magic', frames = 8, rig = null, hemi = ['#ffcdb8', '#5a2030', 1.4], wave = {}, peak = 6, cd = [2.2, 11, 3], ring = 5, seed = 'fwoom' } = {}) {
  const grp = new THREE.Group(); grp.name = 'fwoom'; const L = gnome.getObjectByName('lantern'); const lp = worldOf(L.getObjectByName('lanternGlass') || L, new THREE.Vector3());
  const Cn = center ? P3(center) : new THREE.Vector3(lp.x, 0, lp.z);
  const lvl = (t) => fwoomLevel(t, t0, { base: 1, peak, end: 1.5, t2, peak2: Math.max(2, peak * 0.5) });
  const lan = lanternLight(ctx, gnome, { t0: -10, ring, ringOpts: {}, burst: false, haloPx: 80, cd: cd[0], levelFn: lvl, seed: seed + 'lan' }); grp.add(lan.group);
  // light curve in cd: base -> peak -> end, shaped like the lantern level
  const cdAt = (t) => { const k = (lvl(t) - 1) / (peak - 1); const u = t - t0; return u < 0.15 ? cd[0] + (cd[1] - cd[0]) * clamp01(k) : cd[2] + (cd[1] - cd[2]) * clamp01((lvl(t) - 1.5) / (peak - 1.5)); };
  const parts = [];
  if (burst) parts.push(sets.burst(ctx, { pos: lp.toArray(), t0, dur: 0.4, count: 34, spread: 0.9, px: [34, 80], ringPx: [60, 980], ringColor: '#ffe6c0', colors: ['#ffffff', '#ffd27a', '#ff9ad5', '#fff2d8'], corePx: 420, brightness: 2.4, seed: seed + 'b' }));
  if (burst && t2 != null) parts.push(sets.burst(ctx, { pos: lp.toArray(), t0: t2, dur: 0.35, count: 14, spread: 0.6, px: [28, 60], ringPx: [40, 560], ringColor: '#ffe6c0', colors: GOLD, corePx: 240, brightness: 2.0, seed: seed + 'b2' }));
  if (doStreaks) parts.push(streaks(ctx, { pos: lp.toArray(), t0, count: 16, px: [140, 300], life: 0.3, colors: ['#ffffff', '#ffd27a', '#ff9ad5', '#fff2d8'], reach: 0.7, seed: seed + 's' }));
  let md = null; if (dust) { md = sets.magicDust(ctx, { center: [lp.x, lp.y - 0.1, lp.z], radius: 0.9, height: 1.4, count: 34, rise: 0.4, swirl: 0.8, px: [14, 30], colors: ['#ffd27a', '#ffc070', '#ff9ad5', '#fff2d8'], seed: seed + 'dust' }); parts.push(md); }
  parts.forEach((p) => grp.add(p));
  const W = lightWave(ctx, { center: Cn, t0: t0 + 0.05, speed, seed: seed + 'w', ...wave }); grp.add(W.group);
  const cues = [{ t: t0, kind: 'fwoom' }]; if (t2 != null) cues.push({ t: t2, kind: 'flare2' });
  if (field) { const idx = moles === 'all' ? field.moles.map((m, i) => i) : moles; idx.forEach((i, j) => { const p = moleWorld(field, i, t0); const d = Math.hypot(p.x - Cn.x, p.z - Cn.z); const ts = t0 + 0.05 + d / W.speed + stagger * (j % 3); field.sink(i, ts, sinkDur); cues.push({ t: ts + 0.12, kind: 'blip', mole: i }); }); }
  const gr = grade ? inShotGrade(ctx, 'current', grade, t0, frames, 1, { rig, hemi: rig ? hemi : null }) : null;
  const pl = L.getObjectByName('fxLanternLight') || L.getObjectByName('lanternLight');
  const update = (t) => { lan.update(t); if (pl) { pl.intensity = t < t0 ? cd[0] : cdAt(t); pl.visible = true; } for (const p of parts) p.update(t); if (md) { const k = smooth((t - t0 - 0.03) / 0.2); md.children.forEach((s) => { s.material.opacity *= k; s.visible = k > 0; }); } W.update(t); if (gr) gr(t); };
  update(-1); return { group: grp, update, cues, wave: W, lantern: lan, level: lvl };
}

// Eye pairs winking out (s80): winkOut(ctx, [{ L, R, t }] | field moles, { px: 46, color: '#ffc070' }) -> { group, update }.
// A small amber star pops on each eye for 3 frames as the pair goes dark (the "blip"); pair the call with the creatures'
// eyesOff / field.eyes(i, tOn, tOff) at the same t. fieldEyes(field, i) -> [L, R] world positions of a field head's eyes.
export function fieldEyes(field, i) { const h = field.moles[i].head; if (!h) return null; h.updateWorldMatrix(true, true); const g = (n) => { const o = h.getObjectByName(n); return o ? o.getWorldPosition(new THREE.Vector3()) : null; }; return [g('eyeL'), g('eyeR')]; }
export function winkOut(ctx, items, { px = 46, color = '#ffc070', seed = 'wink' } = {}) {
  const grp = new THREE.Group(); grp.name = 'winkOut'; const gl = [];
  items.forEach((it, i) => { for (const p of [it.L, it.R, it.pos].filter(Boolean)) { const g = starGlint(ctx, { pos: P3(p), t0: it.t, peak: px, rot: 20 + 15 * (i % 3), color, depthTest: false }); grp.add(g); gl.push(g); } });
  return { group: grp, update: (t) => gl.forEach((g) => g.update(t)) };
}

// ============================================================================================ DAWN LIGHT SWEEP
// dawnSweep(ctx, { from: [x, z], to: [x, z], t0, dur: 1.4, width: 5 (studs), color: '#ffa860', intensity: 1.6, after: 0.35,
// shade: 0.3, sun: rig.key | null, ramp: [0.45, 1], hemi: rig.hemi | null, glints: 10 }) -> { group, update(t), k(t) }.
// The low sun clearing the roofs: a band of warm light sweeps over the ground from `from` to `to` (light boost: the lit
// texture warms; the ground ahead of the band stays in the blue shade, x0.7; behind it a gentle warm lift), the dew glints
// wake as it passes, and with `sun` (the rig's DirectionalLight) its intensity ramps ramp[0] -> ramp[1] with the band (the
// grass blades, props and characters brighten with it; `hemi` ramps the same way). k(t) = progress 0..1.
// Why not a moving shadow edge: the street set's lawn takes no sun shadows (checked: even a test cube casts none on it).
const SWEEP_FS = `uniform vec3 uC; uniform vec2 uA0, uDir; uniform float uS, uW, uI, uAfter, uLen, uShade; varying vec2 vUv; varying vec3 vW; // light boost: dst * (1 + c)
void main(){ float p = dot(vW.xz - uA0, uDir); float n = sin(vW.x * 3.1 + vW.z * 1.7) * 0.5 + sin(vW.x * 0.9 - vW.z * 2.3) * 0.5; float b = exp(-pow((p - uS + n * 0.08 * uW) / uW, 2.0));
  float behind = uAfter * smoothstep(uS + uW * 0.5, uS - uW, p); float ahead = smoothstep(uS - uW * 0.5, uS + uW, p); float ends = smoothstep(-uW, 0.0, p) * (1.0 - smoothstep(uLen, uLen + uW * 2.0, p));
  vec3 c = uC * uI * (b + behind) * ends - vec3(uShade) * ahead * ends; gl_FragColor = vec4(max(c, vec3(-0.9)), 1.0); }`; // negative = shade (half-float target)
export function dawnSweep(ctx, { from, to, t0 = 0, dur = 1.4, width = 5, color = '#ffa860', intensity = 1.6, after = 0.35, shade = 0.3, sun = null, ramp = [0.45, 1], hemi = null, ground = 0, span = 30, glints = 10, seed = 'sweep' } = {}) {
  const A = P3(from), B = P3(to); const dir = new THREE.Vector2(B.x - A.x, B.z - A.z); const len = dir.length(); dir.normalize(); const W = width * S;
  const grp = new THREE.Group(); grp.name = 'dawnSweep'; const k = (t) => clamp01((t - t0) / dur);
  const u = { uC: { value: new THREE.Color(color) }, uA0: { value: new THREE.Vector2(A.x, A.z) }, uDir: { value: dir }, uS: { value: -W }, uW: { value: W }, uI: { value: intensity }, uAfter: { value: after }, uLen: { value: len }, uShade: { value: shade } };
  const sz = len + 2 * W + span * S; const plane = new THREE.Mesh(new THREE.PlaneGeometry(sz, sz), boostBlend(new THREE.ShaderMaterial({ uniforms: u, vertexShader: WAVE_VS, fragmentShader: SWEEP_FS, polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 })));
  plane.rotation.x = -PI / 2; plane.position.set((A.x + B.x) / 2, ground + 0.014, (A.z + B.z) / 2); plane.renderOrder = 3; grp.add(plane);
  const sun0 = sun ? sun.intensity : 0, hemi0 = hemi ? hemi.intensity : 0;
  const r = makeRng(hash32('sweep', seed)); const gl = []; const side = new THREE.Vector2(-dir.y, dir.x);
  for (let i = 0; i < glints; i++) { const p = r(); const q = (r() - 0.5) * span * S * 0.6; const sp = pxSprite(addSpriteMat(sparkTex(ctx, 6), r() < 0.5 ? '#ffe2c4' : '#fff4e0', 1.8, { depthTest: true }), 0); sp.position.set(A.x + dir.x * len * p + side.x * q, ground + (0.05 + 0.15 * r()) * S, A.z + dir.y * len * p + side.y * q); sp.userData.d = { p, px: 30 + 20 * r(), per: 0.6 + 0.6 * r(), ph: r() }; sp.renderOrder = 7; grp.add(sp); gl.push(sp); }
  const update = (t) => { const kk = inOutSine(k(t)); u.uS.value = -W + (len + 2 * W) * kk;
    if (sun) sun.intensity = sun0 * lerp(ramp[0], ramp[1], kk); if (hemi) hemi.intensity = hemi0 * lerp(0.75, 1, kk);
    for (const sp of gl) { const d = sp.userData.d; const age = t - (t0 + dur * d.p); const tw = 0.5 + 0.5 * Math.sin((t / d.per + d.ph) * 2 * PI); sp.visible = age > 0; if (!sp.visible) continue; sp.userData.px = d.px * (age < 0.3 ? 1.4 - age : 0.6 + 0.5 * tw); sp.material.opacity = age < 0.3 ? 1 : 0.35 + 0.5 * tw; } };
  update(-1); return { group: grp, update, k };
}

// ============================================================================================ BLINK "TIK" GLINT
// blinkTik(ctx, gnome, { t0 (blink start, same as K.gnomeBlink), frames: 2, slow: false, eyes: 'both' | 'L' | 'R',
// px: 58, color: '#fff6ea' }) -> { group, update(t), tReopen }. The accent for the [TIK] cue: as the lids reopen a small
// soft 4-point glint pops on each eye's catchlight (2-frame rise, 10-frame fall; the second eye one frame later).
export function blinkTik(ctx, gnome, { t0 = 0, frames = 2, slow = false, eyes = 'both', px = 58, color = '#fff6ea', seed = 'tik' } = {}) {
  const tR = t0 + (frames + (slow ? 1 : 0)) / 60; const names = eyes === 'both' ? ['L', 'R'] : [eyes]; const grp = new THREE.Group(); grp.name = 'blinkTik'; const gl = [];
  names.forEach((nm, i) => {
    const ball = gnome.getObjectByName('ball' + nm); if (!ball) return; ball.geometry.computeBoundingSphere(); const s = pxSprite(addSpriteMat(ctx.tex.sparkle({ points: 4, sharpness: 12, core: 0.75 }), color, 2.2, { depthTest: false }), 0); s.renderOrder = 32; s.frustumCulled = false;
    const c = pxSprite(addSpriteMat(ctx.tex.radialGlow({ falloff: 2.2 }), color, 1.2, { depthTest: false }), 0); c.renderOrder = 31; c.frustumCulled = false;
    const tt = tR + i / 60; const ew = new THREE.Vector3(), tc = new THREE.Vector3(), rt = new THREE.Vector3(), upv = new THREE.Vector3();
    const place = function (r, sc, cam) { ball.updateWorldMatrix(true, false); ball.getWorldPosition(ew); const er = ball.geometry.boundingSphere.radius * ball.getWorldScale(tc).x; tc.setFromMatrixPosition(cam.matrixWorld).sub(ew).normalize(); rt.setFromMatrixColumn(cam.matrixWorld, 0).normalize(); upv.setFromMatrixColumn(cam.matrixWorld, 1).normalize(); this.position.copy(ew).addScaledVector(tc, er * 1.1).addScaledVector(upv, er * 0.5).addScaledVector(rt, -er * 0.32); };
    for (const sp of [s, c]) { const base = sp.onBeforeRender; sp.onBeforeRender = function (r, sc, cam) { place.call(this, r, sc, cam); base.call(this, r, sc, cam); }; grp.add(sp); }
    gl.push({ s, c, tt });
  });
  const update = (t) => { for (const g of gl) { const f = (t - g.tt) * 60; const on = f > -0.5 && f < 12; g.s.visible = g.c.visible = on; if (!on) continue; const k = f < 2 ? (f + 1) / 3 : Math.pow(1 - (f - 2) / 10, 1.5); g.s.userData.px = px * k; g.c.userData.px = px * 0.55 * k; g.s.material.opacity = 1; g.c.material.opacity = 0.75 * k; g.s.material.rotation = 0.35 + 0.25 * clamp01(f / 12); } };
  update(-1); return { group: grp, update, tReopen: tR, cues: [{ t: tR, kind: slow ? 'tik_slow' : 'tik' }] };
}

// ============================================================================================ PHOTO LOOK + POLAROIDS (fx_photo_look)
// photoLook(ctx, src, { lift: '#2a2420', warm: 8, sat: 0.85, vignette: 0.28, grain: 1, key }) -> { canvas, texture }.
// The print look for photo textures only (never the episode frame): lifted warm blacks, a warm cast (+8 on R, +3 G, -5 B,
// display units), saturation x0.85, a soft vignette inside the print, a 1-px paper grain. src: canvas | { canvas } |
// texture with a canvas image. Cached per worker per source canvas.
const _looked = new WeakMap();
export function photoLook(ctx, src, { lift = '#2a2420', warm = 8, sat = 0.85, vignette = 0.28, grain = 1, seed = 3 } = {}) {
  const c0 = src && src.isTexture ? src.image : src && src.canvas ? src.canvas : src; const key = JSON.stringify([lift, warm, sat, vignette, grain, seed]);
  let per = _looked.get(c0); if (!per) { per = {}; _looked.set(c0, per); } if (per[key]) return per[key];
  const W = c0.width, H = c0.height; const c = document.createElement('canvas'); c.width = W; c.height = H; const g = c.getContext('2d'); g.drawImage(c0, 0, 0);
  const id = g.getImageData(0, 0, W, H); const d = id.data; const L = new THREE.Color(lift).convertLinearToSRGB(); const lr = L.r * 255, lg = L.g * 255, lb = L.b * 255; const r = makeRng(hash32('grain', seed));
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const i = (y * W + x) * 4; let R = d[i], G = d[i + 1], B = d[i + 2]; const l = 0.2126 * R + 0.7152 * G + 0.0722 * B;
    R = l + (R - l) * sat + warm; G = l + (G - l) * sat + warm * 0.4; B = l + (B - l) * sat - warm * 0.6;
    R = lr + (R * (255 - lr)) / 255; G = lg + (G * (255 - lg)) / 255; B = lb + (B * (255 - lb)) / 255;
    const q = Math.hypot((x / W - 0.5) * 2, (y / H - 0.5) * 2); const v = 1 - vignette * smooth((q - 0.55) / 0.85); const n = (r() - 0.5) * 2 * grain * 4;
    d[i] = Math.max(0, Math.min(255, R * v + n)); d[i + 1] = Math.max(0, Math.min(255, G * v + n)); d[i + 2] = Math.max(0, Math.min(255, B * v + n));
  }
  g.putImageData(id, 0, 0); const out = { canvas: c, texture: canvasTex(c) }; per[key] = out; return out;
}
const ORD = (n) => n + (n % 100 >= 11 && n % 100 <= 13 ? 'th' : ['th', 'st', 'nd', 'rd'][n % 10] || 'th');
export const photoDate = (year) => `${ORD(year)} spring`;
// polaroid(ctx, { photo: canvas | texture | { canvas }, date: '1st spring', w: 3.5, h: 4.2 (studs), curl: 0.12 (studs),
// look: {...photoLook}, ink: '#22307a', paper: '#f4f0e6', back: '#2c2a30', seed }) -> Group (metres, front +Z, origin at
// the card centre; userData.texture). The Polaroid insert: white paper frame (thick bottom margin) with a paper grain and
// a faint edge yellowing, the photo with the print look, the date hand-written in blue ballpoint (per-letter jitter), and
// a slight curl (the card bows and one corner lifts). Use polaroidDrop / polaroidSlide to animate it in.
function polaroidCanvas(ctx, photo, { date, ink, paper, look, seed }) {
  const W = 700, H = 840, M = 34, PH = W - 2 * M; const c = document.createElement('canvas'); c.width = W; c.height = H; const g = c.getContext('2d'); const r = makeRng(hash32('pol', seed, date));
  g.fillStyle = paper; g.fillRect(0, 0, W, H);
  for (let k = 0; k < 1400; k++) { g.fillStyle = `rgba(${r() < 0.5 ? '90,70,40' : '255,255,255'},${0.02 + 0.03 * r()})`; g.fillRect(r() * W, r() * H, 1 + r() * 2, 1 + r() * 2); }
  const eg = g.createLinearGradient(0, 0, W, H); eg.addColorStop(0, 'rgba(180,150,90,0.10)'); eg.addColorStop(0.5, 'rgba(180,150,90,0)'); eg.addColorStop(1, 'rgba(160,130,80,0.12)'); g.fillStyle = eg; g.fillRect(0, 0, W, H);
  if (photo) { const src = photo.isTexture ? photo.image : photo.canvas || photo; const lk = photoLook(ctx, src, look); g.drawImage(lk.canvas, M, M, PH, PH); }
  else { g.fillStyle = '#2a2420'; g.fillRect(M, M, PH, PH); }
  g.strokeStyle = 'rgba(40,30,20,0.25)'; g.lineWidth = 2; g.strokeRect(M, M, PH, PH); g.fillStyle = 'rgba(0,0,0,0.06)'; g.fillRect(M, M + PH, PH, 4);
  if (date) { g.save(); g.translate(W * 0.5, M + PH + (H - M - PH) * 0.52); g.rotate(-0.035 + (r() - 0.5) * 0.03); g.font = `italic 600 56px "DejaVu Serif", "Liberation Serif", serif`; g.textBaseline = 'middle';
    const chars = [...date]; const ws = chars.map((ch) => g.measureText(ch).width * 0.92); const tot = ws.reduce((a, b) => a + b, 0); let x = -tot / 2;
    chars.forEach((ch, i) => { g.save(); g.translate(x + ws[i] / 2, (r() - 0.5) * 4 + Math.sin(i * 0.9) * 1.5); g.rotate((r() - 0.5) * 0.08); g.fillStyle = ink; g.globalAlpha = 0.86; g.textAlign = 'center'; g.fillText(ch, 0, 0); g.globalAlpha = 0.3; g.fillText(ch, 0.8, 0.5); g.restore(); x += ws[i]; });
    g.restore(); }
  return c;
}
export function polaroid(ctx, { photo = null, date = '', w = 3.5, h = 4.2, curl = 0.12, look = {}, ink = '#22307a', paper = '#f4f0e6', back = '#2c2a30', roughness = 0.42, seed = 1 } = {}) {
  const c = polaroidCanvas(ctx, photo, { date, ink, paper, look, seed }); const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  const Wm = w * S, Hm = h * S; const geo = new THREE.PlaneGeometry(Wm, Hm, 14, 16); const pa = geo.attributes.position;
  for (let i = 0; i < pa.count; i++) { const xn = pa.getX(i) / (Wm / 2), yn = pa.getY(i) / (Hm / 2); const corner = smooth((xn * 0.55 + yn * 0.45 - 0.35) / 0.65); pa.setZ(i, curl * S * (0.3 * xn * xn + 0.15 * yn * yn + 0.75 * corner * corner)); }
  geo.computeVertexNormals();
  const front = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ map: tex, roughness, metalness: 0 })); front.name = 'polaroidFront';
  const bk = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: back, roughness: 0.7, side: THREE.BackSide })); bk.name = 'polaroidBack';
  const grp = new THREE.Group(); grp.name = 'polaroid'; grp.add(front, bk); grp.userData.texture = tex; grp.userData.size = [Wm, Hm]; return grp;
}
// polaroidDrop(ctx, cards, { at: [x, y, z] (table top), t0s: [...], dur: 0.28, height: 0.5, spread: [0.3, 0.24], shadows: true })
// -> Group with update(t): each card falls face-up from `height` m with a spin (outQuad), lands at a seeded angle on the
// pile (each 4 mm above the last) with a 2-frame settle; a soft contact shadow grows under it as it lands.
export function polaroidDrop(ctx, cards, { at = [0, 0, 0], t0s = null, dur = 0.28, height = 0.5, spread = [0.3, 0.24], shadows = true, seed = 'drop' } = {}) {
  const grp = new THREE.Group(); grp.name = 'polaroidDrop'; grp.position.copy(P3(at)); const r = makeRng(hash32('pdrop', seed));
  const items = cards.map((c, i) => { const land = { x: (r() - 0.5) * spread[0], z: (r() - 0.5) * spread[1], a: (r() - 0.5) * 1.1, y: 0.004 + i * 0.004 }; grp.add(c);
    let sh = null; if (shadows) { const [w, h] = c.userData.size || [1, 1.2]; sh = new THREE.Mesh(new THREE.PlaneGeometry(w * 1.12, h * 1.1), new THREE.MeshBasicMaterial({ map: ctx.tex.radialGlow({ falloff: 0.9 }), color: '#0a0610', transparent: true, opacity: 0, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2 })); sh.rotation.x = -PI / 2; grp.add(sh); }
    return { c, land, t0: t0s ? t0s[i] : -1, sh }; });
  grp.update = (t) => { for (const it of items) { const L = it.land; const u = it.t0 < 0 ? 1 : (t - it.t0) / dur; it.c.visible = u >= 0; if (it.sh) it.sh.visible = u >= 0; if (u < 0) continue; const k = outQuad(u); const st = u > 1 ? Math.exp(-(t - it.t0 - dur) * 30) * Math.sin((t - it.t0 - dur) * 60) * 0.01 : 0;
    it.c.position.set(L.x * k + (1 - k) * 0.06, L.y + 0.002 + (1 - k) * height + Math.abs(st) * 0.2, L.z * k); it.c.rotation.set(-PI / 2 + (1 - k) * 0.45 + st, 0, L.a + (1 - k) * 1.3, 'XYZ');
    if (it.sh) { it.sh.position.set(L.x * k, L.y - 0.001, L.z * k); it.sh.rotation.z = L.a; it.sh.material.opacity = 0.45 * k * k; } } };
  grp.update(1e9); return grp;
}
// polaroidSlide(card, { t0, dur: 0.3, from: [dx, dy, dz] (m, offset from its rest pose), spin: 6 (deg) }) -> update(t): the
// full-frame insert (s93): the card slides into its rest pose (outBack) with a small rotation settle. Pose the card first.
export function polaroidSlide(card, { t0 = 0, dur = 0.3, from = [0, -0.6, 0], spin = 6 } = {}) {
  const p0 = card.position.clone(), r0 = card.rotation.clone(); const off = P3(from);
  return (t) => { const u = (t - t0) / dur; const k = u < 0 ? 0 : outBack(u); card.visible = u >= 0; card.position.copy(p0).addScaledVector(off, 1 - k); card.rotation.set(r0.x, r0.y, r0.z + spin * DEG * (1 - k)); };
}

// List of what this kit makes (README / QA bookkeeping).
export const FX_EP01 = ['lanternRing', 'lanternLight', 'lanternCascade', 'flashlightBeam', 'curtainCascade', 'glassFog', 'goldOutline', 'propertyLine', 'soilBurst', 'moundCrumbs', 'flutter', 'gulp', 'dewTear', 'windowState', 'windowDark', 'lightWave', 'fwoom', 'fwoomLevel', 'winkOut', 'dawnSweep', 'blinkTik', 'photoLook', 'polaroid', 'polaroidDrop', 'polaroidSlide', 'inShotGrade', 'gradeBlend', 'starGlint', 'streaks', 'poofCloud'];
