// Lighting + post presets for the suburb kit (VISUAL_BIBLE §5 lighting presets, §6 post stack). METRES, physically
// based units (point lights in candela). Each preset function sets the whole look for a shot: sky (optional), hemisphere
// ambient, one soft key from the camera's upper front-left, practical lights near the camera (street lamps, porch
// lanterns, window spill), fog, and the post/grade preset. Call it in build() AFTER ctx.camera.set(...).
//
//   const rig = nightStreet(ctx, { set });          // P1 night street / lawn
//   const rig = nightStreet(ctx, { set, highKey: true });   // EP01 lifted lawn close shots (hemi 1.3)
//   const rig = porchGlow(ctx, { set });            // P1 + warm porch lantern / window spill emphasis
//   const rig = magicGlow(ctx, { set, source: [x, y, z] }); rig.update(t) for the FWOOM curve
//   const rig = dawn(ctx, { set });                 // P4 pink dawn (lamps and windows off, soft sun shadows)
//   rig = { lights: [...], key, hemi, update(t) }
// The grade is calibrated with lookdev/tools/stats.py against the §5 target rows (see README_SETS.md, QA numbers).
import * as THREE from 'three';
import { sky as makeSky } from './sky.js';
import { M } from './kitlib.js';

// ------------------------------------------------------------------ grade presets (display-space colours)
// Start values from VISUAL_BIBLE §6.2; `night`, `porch` and `nightHigh` calibrated on the kit's stills (QA in README_SETS).
export const GRADE = {
  night: { temperature: -18, tint: 8, contrast: 1.08, pivot: 0.4, saturation: 0.9, shadows: '#1a1446', shadowsAmount: 0.2, highlights: '#c8c4ff', highlightsAmount: 0.25, balance: 0, outBlack: '#000000', outWhite: '#c4c3fc' },
  bedroom: { temperature: -6, tint: 14, contrast: 0.95, saturation: 1.08, shadows: '#5a1e3a', shadowsAmount: 0.35, highlights: '#e0c8f8', highlightsAmount: 0.2, outBlack: '#140507', outWhite: '#e7d4fc' },
  warmGlow: { temperature: 14, tint: 6, contrast: 0.95, saturation: 0.92, shadows: '#6c2a3d', shadowsAmount: 0.35, highlights: '#ffdcc4', highlightsAmount: 0.25, outBlack: '#1e070b', outWhite: '#fde3c7' },
  dawn: { temperature: 10, tint: 6, saturation: 1.05, shadows: '#5b2a3a', shadowsAmount: 0.25, highlights: '#ffe6cc', highlightsAmount: 0.2, outBlack: '#120604', outWhite: '#fcf4d9' },
  day: { temperature: 2, saturation: 1.05, outBlack: '#0a0604', outWhite: '#f6f2e6' },
  dusk: { temperature: 16, tint: 4, saturation: 1.02, shadows: '#2a0d18', shadowsAmount: 0.3, highlights: '#ffd2a0', highlightsAmount: 0.25, outBlack: '#0c0304', outWhite: '#f2d4b0' },
  sepia: { temperature: 30, contrast: 0.95, saturation: 0.6, highlights: '#ffd9a8', highlightsAmount: 0.2, outBlack: '#1a0e08', outWhite: '#e3cdb8' },
  bw: { contrast: 1.08, saturation: 0, outBlack: '#0e0c0a', outWhite: '#e8e2d8' },
};
GRADE.porch = { ...GRADE.night };      // tuned below in QA (warm practicals must survive the cool grade)
GRADE.nightHigh = { ...GRADE.night };  // EP01 lifted lawn shots

// Episode base (§6.1): clean image, low bloom, every other effect off.
export const BASE_POST = {
  toneMapping: 'aces', exposure: 1.0, aa: 'msaa', msaaSamples: 4, dither: true,
  bloom: { enabled: true, strength: 0.12, radius: 0.35, threshold: 1.2, knee: 0.5, start: 'quarter', tint: '#ffffff' },
  glow: { enabled: false }, dof: { enabled: false }, vignette: { enabled: false }, chroma: { enabled: false },
  lens: { enabled: false }, grain: { enabled: false }, godrays: { enabled: false }, blur: { enabled: false },
  grade: { enabled: true, ...GRADE.night },
};
// Per scene type (§6.3).
const SCENE_POST = {
  night: { exposure: 1.25, bloom: { strength: 0.12, threshold: 1.2, radius: 0.35 }, grade: 'night' },
  nightHigh: { exposure: 1.0, bloom: { strength: 0.12, threshold: 1.2, radius: 0.35 }, grade: 'nightHigh' },
  porch: { exposure: 1.12, bloom: { strength: 0.13, threshold: 1.15, radius: 0.35 }, grade: 'porch' },
  bedroom: { exposure: 1.05, bloom: { strength: 0.15, threshold: 1.1, radius: 0.35 }, grade: 'bedroom' },
  magic: { exposure: 1.15, bloom: { strength: 0.4, threshold: 0.9, radius: 0.5 }, glow: { enabled: true, amount: 0.12, radius: 0.8, mode: 'screen', tint: '#ffd8c8' }, grade: 'warmGlow' },
  dawn: { exposure: 1.4, bloom: { strength: 0.12, threshold: 1.2, radius: 0.35 }, grade: 'dawn' },
  day: { exposure: 1.0, bloom: { strength: 0.1, threshold: 1.3, radius: 0.3 }, grade: 'day' },
  dusk: { exposure: 1.4, bloom: { strength: 0.15, threshold: 1.1, radius: 0.4 }, grade: 'dusk' },
  sepia: { exposure: 1.0, bloom: { strength: 0.1, threshold: 1.2, radius: 0.35 }, grade: 'sepia' },
  bw: { exposure: 1.0, bloom: { strength: 0.1, threshold: 1.2, radius: 0.35 }, grade: 'bw' },
};
const clone = (o) => JSON.parse(JSON.stringify(o));
function merge(a, b) { for (const k in b) { if (b[k] && typeof b[k] === 'object' && !Array.isArray(b[k]) && a[k] && typeof a[k] === 'object') merge(a[k], b[k]); else a[k] = b[k]; } return a; }
// postPreset('night', { exposure: 1.1 }) -> a complete post params object (base + scene row + overrides).
export function postPreset(name = 'night', extra = {}) {
  const s = SCENE_POST[name]; if (!s) throw new Error('unknown post preset ' + name);
  const p = clone(BASE_POST); const { grade, ...rest } = clone(s); merge(p, rest); p.grade = { enabled: true, ...clone(GRADE[grade]) };
  return merge(p, clone(extra));
}
export const POST_NAMES = Object.keys(SCENE_POST);

// ------------------------------------------------------------------ light presets (numbers from §5.1)
export const LIGHT = {
  night: { hemi: ['#8a90ff', '#241a3a', 1.4], key: { color: '#b4b8ff', intensity: 1.8, el: 48, side: 0.55 }, lamp: { color: '#ffc27a', cd: 5, n: 3 }, lantern: { color: '#ffb766', cd: 3, n: 1 }, window: { color: '#ffd9a0', cd: 1.5, n: 1 }, fog: { color: '#06051a', density: 0.012 }, sky: 'galaxy', post: 'night' },
  nightHigh: { hemi: ['#8a90ff', '#241a3a', 1.25], key: { color: '#b4b8ff', intensity: 1.4, el: 48, side: 0.55 }, lamp: { color: '#ffc27a', cd: 5, n: 3 }, lantern: { color: '#ffb766', cd: 3, n: 1 }, window: { color: '#ffd9a0', cd: 2, n: 1 }, fog: { color: '#06051a', density: 0.012 }, sky: 'galaxy', post: 'nightHigh' },
  porch: { hemi: ['#8a90ff', '#241a3a', 1.25], key: { color: '#b4b8ff', intensity: 1.5, el: 45, side: 0.55 }, lamp: { color: '#ffc27a', cd: 5, n: 3 }, lantern: { color: '#ffb766', cd: 4, n: 2 }, window: { color: '#ffd9a0', cd: 2.2, n: 2 }, fog: { color: '#06051a', density: 0.012 }, sky: 'galaxy', post: 'porch' },
  magic: { hemi: ['#ffcdb8', '#5a2030', 1.4], key: { color: '#ffe2c8', intensity: 1.2, el: 40, side: 0.5 }, lamp: { color: '#ffc27a', cd: 5, n: 2 }, lantern: { color: '#ffb766', cd: 3, n: 1 }, window: { color: '#ffd9a0', cd: 1.5, n: 0 }, source: { color: '#ffb85c', cd: 8 }, fog: { color: '#1a0a14', density: 0.01 }, sky: 'galaxy', post: 'magic' },
  dawn: { hemi: ['#c4c8ff', '#6a4a3a', 1.0], sun: { color: '#ffcf9e', intensity: 2.6, el: 10, az: 125 }, lamp: { n: 0 }, lantern: { n: 0 }, window: { n: 0 }, fog: { color: '#e8c4c0', density: 0.006 }, sky: 'dawn', post: 'dawn', lampsOff: true, windowsOff: true },
  dusk: { hemi: ['#a08ad0', '#5a3424', 1.7], sun: { color: '#ff9a50', intensity: 2.6, el: 6, az: 78 }, lamp: { n: 0 }, lantern: { color: '#ffb766', cd: 2, n: 1 }, window: { color: '#ffd9a0', cd: 1.5, n: 1 }, fog: { color: '#c08a6a', density: 0.006 }, sky: 'dusk', post: 'dusk', lampsDim: true },
  day: { hemi: ['#bcd4ff', '#5a4a30', 1.0], sun: { color: '#fff3e0', intensity: 2.5, el: 45, az: -40 }, lamp: { n: 0 }, lantern: { n: 0 }, window: { n: 0 }, fog: { color: '#c8d0e0', density: 0.006 }, sky: 'day', post: 'day', lampsOff: true, windowsOff: true },
};

// ------------------------------------------------------------------ helpers
// Camera at t = 0 (call after ctx.camera.set): position, forward, right, up, a target point.
export function camBasis(ctx) {
  ctx.camera.apply(0); const cam = ctx.cam; cam.updateMatrixWorld(true);
  const pos = cam.getWorldPosition(new THREE.Vector3()); const fwd = cam.getWorldDirection(new THREE.Vector3());
  const right = new THREE.Vector3().crossVectors(fwd, new THREE.Vector3(0, 1, 0)).normalize(); const up = new THREE.Vector3().crossVectors(right, fwd).normalize();
  return { pos, fwd, right, up, target: pos.clone().addScaledVector(fwd, 6) };
}
// Directional key from the camera's upper front-left (the light sits behind-left-above the camera, lighting faces).
export function keyLight(ctx, { color = '#b4b8ff', intensity = 1.4, el = 48, side = 0.55, shadow = false, target = null, size = 8, mapSize = 2048, radius = 6, basis = null } = {}) {
  const B = basis || camBasis(ctx); const T = target ? new THREE.Vector3(...target) : B.target;
  const flat = B.fwd.clone(); flat.y = 0; flat.normalize(); const r = B.right.clone(); r.y = 0; r.normalize();
  const d = flat.multiplyScalar(-1).addScaledVector(r, -side).normalize(); d.y = Math.tan((el * Math.PI) / 180); d.normalize();
  const pos = T.clone().addScaledVector(d, 25);
  return ctx.lights.sun({ color, intensity, pos: pos.toArray(), target: T.toArray(), shadow, size, mapSize, radius, far: 80, bias: -0.0004, normalBias: 0.03 });
}
// Sun at an absolute azimuth/elevation (degrees; az 0 = from -Z, +90 = from +X), for dawn/dusk/day.
export function sunLight(ctx, { color, intensity, el = 10, az = 120, shadow = true, target = [0, 0, 0], size = 14, mapSize = 2048, radius = 3 } = {}) {
  const a = (az * Math.PI) / 180, e = (el * Math.PI) / 180; const T = new THREE.Vector3(...target);
  const pos = T.clone().add(new THREE.Vector3(Math.sin(a) * Math.cos(e), Math.sin(e), -Math.cos(a) * Math.cos(e)).multiplyScalar(40));
  return ctx.lights.sun({ color, intensity, pos: pos.toArray(), target: T.toArray(), shadow, size, mapSize, radius, far: 120, bias: -0.0005, normalBias: 0.04 });
}
// Set-root metres -> world (the set may have been moved/rotated by the shot).
function toWorld(set, p) { if (!set) return new THREE.Vector3(...p); set.updateMatrixWorld(true); return new THREE.Vector3(...p).divideScalar(set.scale.x || 1).applyMatrix4(set.matrixWorld); }
const nearest = (list, from, n, maxD = 1e9) => list.map((x) => ({ x, d: x.w.distanceTo(from) })).filter((e) => e.d < maxD).sort((a, b) => a.d - b.d).slice(0, n).map((e) => e.x);

// Practical point lights near the camera: street lamps (4-6 nearest), porch lanterns, lit-window spill (§5.1 P1).
export function practicals(ctx, set, { lamp = {}, lantern = {}, window: win = {}, from = null } = {}) {
  const out = []; if (!set || !set.userData) return out; const B = from ? { pos: new THREE.Vector3(...from) } : camBasis(ctx); const U = set.userData;
  const focus = B.target ? B.pos.clone().lerp(B.target, 0.6) : B.pos; // weight toward what the camera looks at
  if (lamp.n) for (const l of nearest(U.lamps.map((l) => ({ ...l, w: toWorld(set, l.head) })), focus, lamp.n)) { const p = l.w.clone(); p.y -= 0.1; out.push(ctx.add(ctx.lights.point({ color: lamp.color, intensity: lamp.cd, pos: p.toArray(), decay: 2 }))); }
  if (lantern.n) for (const l of nearest(U.lanterns.map((l) => ({ ...l, w: toWorld(set, l.pos) })), focus, lantern.n, lantern.maxD ?? 12)) out.push(ctx.add(ctx.lights.point({ color: lantern.color, intensity: lantern.cd, pos: l.w.toArray(), decay: 2 })));
  if (win.n) {
    const lots = Object.fromEntries(U.lots.map((l) => [l.id, l])); const lit = U.windows.filter((w) => w.lit && w.face === 'front');
    for (const w of nearest(lit.map((w) => ({ ...w, w: toWorld(set, w.pos) })), focus, win.n, win.maxD ?? 10)) {
      const yaw = lots[w.lot].yaw; const n = new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw)); const p = w.w.clone().addScaledVector(n, 0.7); p.y -= 0.25;
      out.push(ctx.add(ctx.lights.point({ color: win.color, intensity: win.cd, pos: p.toArray(), decay: 2 })));
    }
  }
  return out;
}
// Light states on a (cloned) set: street lamps and lit windows on/off/dim. Swaps shared materials (never mutates them).
export function setLamps(set, state = 'on') {
  set.traverse((o) => {
    if (o.name === 'lampGlass') o.material = M(state === 'on' ? 'emissive:#ffd9a0:4' : state === 'dim' ? 'emissive:#ffd9a0:1.2' : 'black:#2a2a2e');
    if (o.name === 'lampHalo' || o.name === 'lampPool') o.visible = state === 'on';
  });
}
export function setWindows(set, state = 'on') {
  set.traverse((o) => { if (o.isMesh && o.name.startsWith('win:')) { if (!o.userData.litMat) o.userData.litMat = o.material.name; o.material = state === 'on' ? M(o.userData.litMat) : M('glassDark'); } if (o.name === 'winGlow') o.visible = state === 'on'; });
}

// ------------------------------------------------------------------ preset runner
function run(ctx, name, o = {}) {
  const L = { ...LIGHT[name], ...(o.light || {}) }; const set = o.set || null; const B = camBasis(ctx); const rig = { lights: [], name, update: () => {} };
  if (o.sky !== false && L.sky) { rig.sky = makeSky(ctx, { preset: o.skyPreset || L.sky, ...(o.skyOpts || {}), moon: o.moon ?? (name.startsWith('night') || name === 'porch' ? { az: -38, el: 34, size: 6, style: 'tf' } : null), sun: o.sunDisc ?? (L.sun ? { az: L.sun.az, el: Math.max(2, L.sun.el - 1), color: '#fff0d8', size: 3.5 } : null) }); ctx.add(rig.sky); }
  const h = o.hemi || L.hemi; rig.hemi = ctx.add(ctx.lights.hemi(h[0], h[1], o.hemiIntensity ?? h[2]));
  if (L.key) rig.key = ctx.add(keyLight(ctx, { ...L.key, ...(o.key || {}), basis: B, target: o.target }));
  if (L.sun) rig.key = ctx.add(sunLight(ctx, { ...L.sun, ...(o.sun || {}), target: o.target || B.target.toArray(), shadow: o.shadows ?? true }));
  if (set) rig.lights.push(...practicals(ctx, set, { lamp: { ...L.lamp, ...(o.lamp || {}) }, lantern: { ...L.lantern, ...(o.lantern || {}) }, window: { ...L.window, ...(o.window || {}) } }));
  if (set && L.lampsOff) setLamps(set, 'off'); else if (set && L.lampsDim) setLamps(set, 'dim');
  if (set && L.windowsOff) setWindows(set, 'off');
  if (o.subject) { // "the subject is the brightest thing in a night frame": a soft lift from upper front-left of the camera
    const s = new THREE.Vector3(...o.subject.pos); const p = s.clone().addScaledVector(B.right, -0.6).addScaledVector(B.fwd, -0.9).add(new THREE.Vector3(0, 0.9, 0));
    rig.subject = ctx.add(ctx.lights.point({ color: o.subject.color || '#d8d4ff', intensity: o.subject.cd ?? 1.2, pos: p.toArray(), decay: 2 }));
  }
  if (o.fog !== false && L.fog) ctx.setFog({ ...L.fog, ...(o.fogOpts || {}) });
  if (o.post !== false) ctx.post.set(postPreset(L.post, o.postOpts || {}));
  return rig;
}
// P1 NIGHT STREET / NIGHT LAWN. highKey: EP01 lifted lawn shots (hemi 1.3, nightHigh grade).
export const nightStreet = (ctx, o = {}) => run(ctx, o.highKey ? 'nightHigh' : 'night', o);
export const nightLawn = (ctx, o = {}) => run(ctx, 'nightHigh', o);
// Porch glow: P1 with the porch lanterns and the nearest lit windows as warm practicals (porch / doorstep shots).
export const porchGlow = (ctx, o = {}) => run(ctx, 'porch', o);
// P3 MAGIC GLOW: warm grade, a strong lantern source (o.source = [x,y,z]); rig.fwoom(t0) returns an update(t) that runs
// the FWOOM curve (8 -> 50 cd in 0.15 s, back to 10 over 1.5 s inOutSine) and drives emissive materials passed in o.emissives.
export function magicGlow(ctx, o = {}) {
  const rig = run(ctx, 'magic', o); const L = LIGHT.magic;
  if (o.source) { rig.source = ctx.add(ctx.lights.point({ color: L.source.color, intensity: o.sourceCd ?? L.source.cd, pos: o.source, decay: 2 })); }
  rig.fwoom = (t0 = 0, { base = 8, peak = 50, end = 10, emissives = [], eBase = 4, ePeak = 25 } = {}) => (t) => {
    const u = t - t0; let k;
    if (u < 0) k = 0; else if (u < 0.15) k = u / 0.15; else { const v = Math.min(1, (u - 0.15) / 1.5); const e = 0.5 - 0.5 * Math.cos(Math.PI * v); k = 1 - e * (1 - (end - base) / (peak - base)); }
    if (rig.source) rig.source.intensity = base + (peak - base) * k; for (const m of emissives) m.emissiveIntensity = eBase + (ePeak - eBase) * k;
  };
  return rig;
}
// P4 DAWN: dawn sky + low sun from behind-side (soft long shadows), lamps and windows off.
export const dawn = (ctx, o = {}) => run(ctx, 'dawn', o);
// Additional EP01 presets.
export const dusk = (ctx, o = {}) => run(ctx, 'dusk', o);
export const day = (ctx, o = {}) => run(ctx, 'day', o);
export const PRESETS = { nightStreet, nightLawn, porchGlow, magicGlow, dawn, dusk, day };
