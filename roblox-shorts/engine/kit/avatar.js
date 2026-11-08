// R6 avatar builder (VISUAL_BIBLE §2.1-2.5, §3.1): six rigid parts, drum head with a decal face band, 2D clothing,
// chunky accessories, posable joints (neck, shoulders, hips + whole-body lean/turn/lift) and a pose library.
//
// Rig (studs, feet at y = 0, character faces +z; its LEFT is +x):
//   root (scaled 0.32 -> metres)
//    └ body      whole-body yaw/roll + lift (pose keys bodyY, bodyZ, lift)
//       ├ hips   pivot y = 2 (pose key bodyX = forward lean of the upper body, for kneel / bow)
//       │  ├ torso        2x2x1 at y 3
//       │  ├ neck         pivot y = 4: neckX (+ = look up), neckY (+ = turn to its left), neckZ (tilt)
//       │  │   └ head     drum at y 4.6 (+ face band, hair, glasses, hats)
//       │  ├ shoulderL/R  pivot (±1.5, 3.5): armLx (+ = raise forward), armLz (+ = raise outward), armLy (twist)
//       └ hipL/R         pivot (±0.5, 2): legLx (+ = swing forward), legLz (+ = outward)
// All pose angles are DEGREES. Missing keys = 0 (the rest pose = arms down, legs straight).
//
//   const a = makeAvatar({ skin, outfit, face, faceOverlays, hair, accessories, scale, units })
//   setFace(a, 'grin'); setPose(a, POSES.wave); setPose(a, poseAt(t, keys, blend)); walkCycle(t), runCycle(t), waveCycle(t)
import { THREE, STUD, DEG, cached, keyOf, mesh, group, makeRoot, shadowBlob, clamp, ownMat, claimMat } from './util.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { faceTexture, resolveFace } from './faces.js';
import { outfitMaterials, atlasUV, SKIN } from './clothing.js';
import { addAccessory } from './accessories.js';
import * as anim from '../core/anim.js';

// ---------------- geometry (cached, persistent) ----------------
export function headProfile(scaleR = 1) {
  const pts = [], r = 0.6, h = 0.6, f = 0.25, N = 10;
  pts.push(new THREE.Vector2(0, -h));
  for (let i = 0; i <= N; i++) { const a = -Math.PI / 2 + (i / N) * Math.PI / 2; pts.push(new THREE.Vector2((r - f + Math.cos(a) * f) * scaleR, -h + f + Math.sin(a) * f)); }
  for (let i = 1; i < 6; i++) pts.push(new THREE.Vector2(r * scaleR, -h + f + (i / 6) * (2 * (h - f))));
  for (let i = 0; i <= N; i++) { const a = (i / N) * Math.PI / 2; pts.push(new THREE.Vector2((r - f + Math.cos(a) * f) * scaleR, h - f + Math.sin(a) * f)); }
  pts.push(new THREE.Vector2(0, h));
  return pts;
}
export const headGeo = () => cached('r6head', () => { const g = new THREE.LatheGeometry(headProfile(), 48); g.computeVertexNormals(); return g; });
// Face band: a copy of the head lathe over the front 140 degrees, radius x1.004; UVs remapped so u spans the 140
// degrees (u = 0.5 at the front) and v = height (v = 1 at the head top), matching the 512 face frame.
export const FACE_ARC = 140;
export const faceBandGeo = () => cached('r6faceband', () => {
  const pts = headProfile(1.004).filter((p) => p.x > 0.05);
  const g = new THREE.LatheGeometry(pts, 40, -FACE_ARC / 2 * DEG, FACE_ARC * DEG), p = g.attributes.position, uv = g.attributes.uv;
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i), z = p.getZ(i); uv.setXY(i, (Math.atan2(x, z) / DEG + FACE_ARC / 2) / FACE_ARC, (y + 0.6) / 1.2); }
  g.computeVertexNormals(); return g;
});
const boxGeo = (w, h, d) => cached(keyOf('r6box', w, h, d), () => atlasUV(new RoundedBoxGeometry(w, h, d, 3, 0.06), w, h, d));

// ---------------- builder ----------------
// opts: skin, outfit {shirt, pants} (see clothing.js OUTFITS), face, faceOverlays, accessories [{ type, ... }],
//       scale (uniform; 1 = standard R6; bible: kids 1, Theo 0.85, 5-year-old 0.75), units 'm' | 'stud', shadow (blob), name
export function makeAvatar(o = {}) {
  const skin = o.skin || SKIN.salmon;
  const root = makeRoot(o.name || 'avatar', o.units); root.userData.kit = 'avatar';
  root.userData.faceOverlays = o.faceOverlays || {};
  root.userData.face = resolveFace(o.face || 'neutral');
  const S = o.scale ?? 1;
  const body = group('body', root); body.scale.setScalar(S);
  const mats = outfitMaterials({ skin, shirt: o.outfit?.shirt, pants: o.outfit?.pants });
  const skinMat = cached(keyOf('skinMat', skin), () => new THREE.MeshStandardMaterial({ color: skin, roughness: 0.52, metalness: 0 }));
  const hips = group('hips', body, [0, 2, 0]);
  mesh(boxGeo(2, 2, 1), mats.torso, { pos: [0, 1, 0], parent: hips, name: 'torso' });
  const neck = group('neck', hips, [0, 2, 0]);
  const head = group('head', neck, [0, 0.6, 0]);
  mesh(headGeo(), skinMat, { parent: head, name: 'headMesh' });
  const faceMat = new THREE.MeshStandardMaterial({ map: faceTexture(root.userData.face, root.userData.faceOverlays), transparent: true, roughness: 0.55, metalness: 0,
    polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2, depthWrite: false });
  claimMat(mesh(faceBandGeo(), faceMat, { parent: head, name: 'face', cast: false, order: 1 }));
  for (const s of [1, -1]) { // L = +x
    const nm = s > 0 ? 'L' : 'R';
    const sh = group('shoulder' + nm, hips, [s * 1.5, 1.5, 0]); sh.rotation.order = 'XZY';
    mesh(boxGeo(1, 2, 1), mats['arm' + nm], { pos: [0, -0.5, 0], parent: sh, name: 'arm' + nm });
    const hp = group('hip' + nm, body, [s * 0.5, 2, 0]); hp.rotation.order = 'XZY';
    mesh(boxGeo(1, 2, 1), mats['leg' + nm], { pos: [0, -1, 0], parent: hp, name: 'leg' + nm });
  }
  for (const a of o.accessories || []) addAccessory(head, a, { hips, root });
  if (o.shadow !== false) root.add(shadowBlob(2.6 * S, 1.6 * S, o.shadowOpacity ?? 0.34));
  return root;
}

// ---------------- rig access ----------------
const _rigs = new WeakMap();
export function rig(root) {
  let r = _rigs.get(root); if (r) return r;
  const f = (n) => root.getObjectByName(n);
  r = { root, body: f('body'), hips: f('hips'), torso: f('torso'), neck: f('neck'), head: f('head'), face: f('face'), shoulderL: f('shoulderL'), shoulderR: f('shoulderR'), hipL: f('hipL'), hipR: f('hipR') };
  _rigs.set(root, r); return r;
}

// Instant face swap (1 frame). The face material belongs to this avatar (created per build), so swapping it never
// touches another avatar, even ctx.instance() clones (a clone gets its own material on first swap).
export function setFace(root, name, overlays) {
  const R = rig(root); if (!R.face) return;
  const n = resolveFace(name), ov = overlays || root.userData.faceOverlays || {}, t = faceTexture(n, ov);
  if (R.face.material.map !== t) ownMat(R.face).map = t;
  root.userData.face = n;
}
// Faces on a timeline: keys [[t, 'neutral'], [1.2, 'shock']] -> face name at t (instant swaps).
export function faceAt(t, keys) { let f = keys[0][1]; for (const [k, v] of keys) if (t >= k - 1e-6) f = v; return f; }

// ---------------- poses ----------------
export const POSE_KEYS = ['armLx', 'armLy', 'armLz', 'armRx', 'armRy', 'armRz', 'legLx', 'legLz', 'legRx', 'legRz', 'neckX', 'neckY', 'neckZ', 'bodyX', 'bodyY', 'bodyZ', 'lift', 'breath'];
export function setPose(root, p = {}) {
  const R = rig(root), v = (k) => p[k] || 0;
  R.shoulderL.rotation.set(-v('armLx') * DEG, v('armLy') * DEG, v('armLz') * DEG);
  R.shoulderR.rotation.set(-v('armRx') * DEG, -v('armRy') * DEG, -v('armRz') * DEG);
  R.hipL.rotation.set(-v('legLx') * DEG, 0, v('legLz') * DEG);
  R.hipR.rotation.set(-v('legRx') * DEG, 0, -v('legRz') * DEG);
  R.neck.rotation.set(-v('neckX') * DEG, v('neckY') * DEG, v('neckZ') * DEG, 'YXZ');
  R.hips.rotation.set(v('bodyX') * DEG, 0, 0);
  R.body.rotation.set(0, v('bodyY') * DEG, v('bodyZ') * DEG);
  R.body.position.y = v('lift') * R.body.scale.y;
  const b = 1 + v('breath'); R.torso.scale.set(1, b, 1);
  return root;
}
// Bible pose library (joint-angle sets, degrees). Combine with mix() / poseAt().
export const POSES = {
  stand: {},
  idle: { armLz: 3, armRz: 3 },
  lookUp: { neckX: 24, armLz: 4, armRz: 4 },
  lookDown: { neckX: -22, bodyX: 6 },
  lookLeft: { neckY: 40 }, lookRight: { neckY: -40 },
  point: { armRx: 88, armRz: 6, neckY: -6 },
  pointUp: { armRx: 160, armRz: 12, neckX: 20 },
  reach: { armRx: 70, armLx: 62, neckX: -6, bodyX: 8 },
  hold: { armLx: 52, armRx: 52, armLz: -10, armRz: -10 },           // object held in front at chest height (both hands)
  holdLantern: { armRx: 32, armRz: 8 },                               // one hand: lantern hanging forward-right
  carry: { armLx: 82, armRx: 82, armLz: -14, armRz: -14, neckX: -6 },   // hug / carry (object parented to the torso)
  hug: { armLx: 86, armRx: 86, armLz: -24, armRz: -24 },
  kneel: { bodyX: 32, legLx: -90, legRx: -90, lift: -1.45, armLx: 40, armRx: 46, armLz: -6, armRz: -6, neckX: -14 },
  kneelPlace: { bodyX: 48, legLx: -90, legRx: -90, lift: -1.45, armLx: 70, armRx: 70, armLz: -12, armRz: -12, neckX: -18 },
  sit: { legLx: 90, legRx: 90, armLx: 20, armRx: 20 },               // seat top at y 1.5 (put the avatar on the seat)
  sitFloor: { legLx: 90, legRx: 90, lift: -1.5, armLx: 22, armRx: 22 },
  wave: { armRx: 0, armRz: 160, neckZ: -4 },                            // + waveCycle() rocks the arm ±15° at 2 Hz
  shocked: { armLx: 150, armRx: 150, armLz: -38, armRz: -38, neckX: 6 },  // hands to the sides of the head
  handsToHead: { armLx: 150, armRx: 150, armLz: -38, armRz: -38, neckX: 6 },
  sad: { neckX: -22, bodyX: 6, armLz: -4, armRz: -4, armLx: 8, armRx: 8 },
  shrug: { armLx: 20, armRx: 20, armLz: 34, armRz: 34, neckZ: 8 },
  cheer: { armLz: 150, armRz: 150, neckX: 14 },
  sleepwalk: { armLx: 90, armRx: 90, neckX: -25, legLx: 8, legRx: -8 },
  jump: { armLz: 172, armRz: 172, armLx: 8, armRx: 8, legLz: 4, legRz: 4 },
  run: { legLx: 55, legRx: -55, armLx: -50, armRx: 50, bodyX: 6 },
  panicRun: { legLx: 55, legRx: -55, armLx: 88, armRx: 88, bodyX: 8, neckX: 6 },
  walk: { legLx: 38, legRx: -38, armLx: -40, armRx: 40 },
  presentTall: { armLx: 10, armRx: 10, armLz: 70, armRz: 70, neckZ: 6 },  // "a fisherman's tall tale" hands wide
  handOnHeart: { armLx: 60, armLz: -55, armLy: 0, neckZ: 6 },
};
export const POSE_NAMES = Object.keys(POSES);
// Linear mix of two poses (u 0..1), or a weighted sum of several { pose: w }.
export function mixPose(a, b, u) { const o = {}; for (const k of POSE_KEYS) { const va = a[k] || 0, vb = b[k] || 0; if (va || vb) o[k] = va + (vb - va) * u; } return o; }
export function addPose(...ps) { const o = {}; for (const p of ps) for (const k in p) o[k] = (o[k] || 0) + p[k]; return o; }
// Pose-to-pose (bible §3.1): keys [[t, poseObjOrName], ...]; blend 0 = 1-frame snaps (use on cuts / under VFX),
// 0.1-0.25 s = a snappy in-between with `ease` (outBack / outQuad). Pure function of t.
export function poseAt(t, keys, blend = 0.15, ease = 'outQuad') {
  if (!keys._norm) { keys._norm = keys.map(([kt, p]) => [kt, fullPose(typeof p === 'string' ? POSES[p] : p)]); }
  return anim.poseSeq(t, keys._norm, blend, ease);
}
function fullPose(p) { const o = {}; for (const k of POSE_KEYS) o[k] = (p && p[k]) || 0; return o; }

// ---------------- cycles (pure functions of t) ----------------
// Walk: rigid swings, opposite phase, legs ±38°, arms ±40°, cycle 0.73 s, no bob. Travel 7 studs/s (feet do not slide).
export function walkCycle(t, { period = 0.73, legs = 38, arms = 40, phase = 0, holdArms = false } = {}) {
  const s = Math.sin(2 * Math.PI * (t / period + phase));
  const p = { legLx: legs * s, legRx: -legs * s };
  if (!holdArms) { p.armLx = -arms * s; p.armRx = arms * s; }
  return p;
}
export const WALK_SPEED = 7; // studs per second for the default walk
export function runCycle(t, { period = 0.5, legs = 58, arms = 52, panic = false, phase = 0 } = {}) {
  const s = Math.sin(2 * Math.PI * (t / period + phase));
  const p = { legLx: legs * s, legRx: -legs * s, bodyX: 6 };
  if (panic) { p.armLx = 88 + 6 * s; p.armRx = 88 - 6 * s; } else { p.armLx = -arms * s; p.armRx = arms * s; }
  return p;
}
export const RUN_SPEED = 13;
// Wave: arm up ~160°, rocking ±15° at 2 Hz.
export function waveCycle(t, { amp = 15, freq = 2, arm = 'R' } = {}) { const r = amp * Math.sin(2 * Math.PI * freq * t); return arm === 'R' ? { armRz: 160 + r, neckZ: -4 } : { armLz: 160 + r, neckZ: 4 }; }
// Hands-to-head snap (8 frames, ease-out) then a tiny rock.
export function handsToHeadAt(t, t0 = 0, from = {}) { const u = anim.seg(t, t0, t0 + 8 / 60, 'outCubic'); const p = mixPose(from, POSES.handsToHead, u); if (t > t0 + 8 / 60) { const r = 2 * Math.sin(2 * Math.PI * 1.6 * (t - t0)); p.neckZ = (p.neckZ || 0) + r; } return p; }
// Idle breath (CHOSEN, optional): torso scale-y 1.00-1.01 at 0.25 Hz.
export const breath = (t, phase = 0) => ({ breath: 0.005 + 0.005 * Math.sin(2 * Math.PI * (0.25 * t + phase)) });
// Whole-body turn helper: yaw (degrees) over [t0, t1] with inOutSine (bible: 180° in 14 frames).
export const turnAt = (t, t0, t1, from, to) => anim.tween(t, t0, t1, from, to, 'inOutSine');

// ---------------- props ----------------
// Attach a prop to a hand: returns the group positioned at the hand end (local studs, arm hanging = -y).
export function handSocket(root, side = 'R') { const R = rig(root); const sh = R['shoulder' + side]; let s = sh.getObjectByName('hand' + side); if (!s) { s = group('hand' + side, sh, [0, -1.95, 0]); } return s; }

export { SKIN };
