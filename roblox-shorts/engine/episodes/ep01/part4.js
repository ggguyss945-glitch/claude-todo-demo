// EP01 full episode, PART 4 (s58-s76, 65.43-86.77 s): twist 2 and the choice: "And tomorrow night?", the head turn, the
// callback (s61-s63 are part1's fb_* builders), the flashbacks (sepia, B&W), the decades at the window, the slow blink,
// letting go.
// Shot list and every decision (camera numbers, cast and faces, light/grade, events with frames, SFX, assets) are in
// episodes/ep01/timeline.json (params of each shot) and episodes/ep01/board.md; new assets are specified in episodes/ep01/ASSETS.md.
// Builders are pure functions of shot time t (engine/README.md determinism rules): no state between frames, no
// Math.random / Date; seeded RNGs only.
//
// Sets: our front garden is sets_ep01.heroLot (lot A1: gate (0, -6.4); door (0, 0.32, -13.22); Grandpa's bed0 under Theo's
// window at (-2.67, 0.112, -12.67), window glass centre (-2.41, 1.63, -13.31); the room behind the window (interiors.js)
// has its own frame: origin on the floor at the inner wall face, centred on the window, +Z out through the glass).
// Continuity kept here (board.md section 5, part3 s56-s57): night; SOLD on the board; the gate open; the truck at the kerb,
// back open; the front door open (warm hall light); bed0 = the sunken hole with the $4.99 sticker; Grandpa in the hero's
// arms, lantern lit (level 1, flicker) with its 5-stud ring, the family lanterns lit (2-stud pools); the mounds waiting
// just outside the ring with their reflector eyes lit; Theo asleep in his room (star nightlight). hero = heroBarefoot.
// Staging of this part (kept identical across the shots that share it, so the cuts match):
//   s58-s60, s65  the hero on part3's s57 guard spot (bed0 + (0.25, 1.72) m), facing the house turned 40 deg to his right,
//                 Grandpa held against his chest FACING HIM (looking up at him); s59 grinds the head 150 deg away from him
//                 toward the window (head yaw +150), and it stays turned in s60 and s65.
//   s73-s76       the hero kneels in the bed right of the hole (bed0 + (0.78, -0.15) m), facing 60 deg toward the street,
//                 Grandpa in both hands facing him; s76 sets him down beside the hole (right edge), facing the window.
//   s64, s66-s68  flashbacks on heroLot eras '2010s' (room hero5), '1960s' (dad60s), '1990s' (cousin90s).
import * as THREE from 'three';
import * as sets from '../../kit/sets.js';
import * as K from '../../kit/chars.js';
import * as CR from '../../kit/creatures.js';
import * as SE from '../../kit/sets_ep01.js';
import * as I from '../../kit/interiors.js';
import * as X from '../../kit/fx_ep01.js';
import { doorTex } from '../../kit/kitlib.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { makeRng, hash32 } from '../../core/random.js';
import * as C from './common.js';

const S = C.S, DEG = C.DEG, V3 = C.V3, clamp01 = C.clamp01, smooth = C.smooth, outQuad = C.outQuad;
const lerp = (a, b, k) => a + (b - a) * k;
const YAX = new THREE.Vector3(0, 1, 0);
const up = (p, dy = 0, dx = 0, dz = 0) => [p[0] + dx * S, p[1] + dy * S, p[2] + dz * S];
const P3 = (p) => (p && p.isVector3 ? p.clone() : new THREE.Vector3(p[0], p[1], p[2]));
const SPK = (o = {}) => ({ ...C.SPARK, ...o });
const inOutSine = (x) => 0.5 - 0.5 * Math.cos(Math.PI * clamp01(x));
const outCubic = (x) => 1 - Math.pow(1 - clamp01(x), 3);
const dirOf = (a) => new THREE.Vector3(Math.sin(a), 0, Math.cos(a));   // rotation.y -> horizontal facing

// ------------------------------------------------------------------ staging constants (heroLot world metres)
const BED = [-2.669, 0.112, -12.672];       // bed0 (raised soil top 0.112): the hole since s51
const WIN = [-2.413, 1.632, -13.312];       // Theo's window, outer glass centre
const LOT_DOOR = [0, 0.32, -13.216];
const ROOM_FLOOR = 0.32;                    // the bungalow floor (= the porch deck)
const GUARD = [BED[0] + 0.25, 0, BED[2] + 1.72];   // part3 s57: where he stands guard
const GUARD_YAW = 220 * DEG;                // facing the house, turned 40 deg away from the path (the window at his front-right;
                                            // the porch column, 2.6 studs right of the window, stays out of the s60 whip)
const HOLD_OFF = [0, 0.1, 1.12];            // part2/3: the held gnome in the hero's hips frame (studs)
const HUG = { armLx: 78, armRx: 78, armLz: -44, armRz: -44, neckX: -8 };   // part2/3: both arms round the gnome
const KNEEL_AT = [BED[0] + 0.78, BED[1], BED[2] - 0.15];   // s73-s76: kneeling in the soil right of the hole
const KNEEL_YAW = -60 * DEG;                // facing 60 deg toward the street (3/4 to the kneelLow camera)
const KNEEL_HOLD = { ...K.POSES.kneel, bodyX: 14, armLx: 64, armRx: 64, armLz: -30, armRz: -30, neckX: -16 };
const KNEEL_OFF = [0, 0.62, 1.32];          // Grandpa in both hands, facing him (hips frame, studs)
const CU_GRADE = { grade: { temperature: -6, tint: 6 } };   // close-ups keep warm skin / glaze inside the cool night (approved s05)
const TOWARD_ONSET = 68.11;                 // word 267 "toward" (word_onsets.json): s60's whip

// ------------------------------------------------------------------ helpers (the part2/part3 conventions)
const evT = (ctx, k, fb) => C.evT(ctx, k, fb);
const tOnset = (ctx, sec) => (Math.round(sec * ctx.fps) - ctx.shot.f0) / ctx.fps;
function basePush(ctx, o = {}) { const m = ctx.params.camera.move; ctx.camera.push(o.Z ?? m.Z ?? m.base_push ?? 0.19, { mode: m.mode === 'dolly' ? 'dolly' : 'zoom', t0: o.t0, t1: o.t1 }); }
function paramRoll(ctx) { const r = ctx.params.camera.roll; if (r) ctx.camera.rollBy(r.deg[1] - r.deg[0]); }
function sparks(ctx, center, size, count, seed, o = {}) { count = Math.round(Math.max(10, count * 1.8)); const f = sets.sparkles(ctx, SPK({ center: P3(center).toArray(), size, count, seed, ...o })); ctx.add(f); return f; }
function nightLot(ctx, o = {}) { const H = SE.heroLot(ctx, { tod: 'night', bed: 'hole', truck: 'open', gate: 1.5, sold: -1, lanterns: 1, ...o }); ctx.add(H); return H; }
function nightRig(ctx, set, preset = 'nightHigh', o = {}) {
  const f = preset === 'night' ? sets.nightStreet : sets.nightLawn; const { low, lift = true, ...rest } = o;
  const L0 = sets.LIGHT[preset === 'night' ? 'night' : 'nightHigh']; if (lift) rest.hemiIntensity = (rest.hemiIntensity ?? L0.hemi[2]) * NIGHT_LIFT.hemi;
  const rig = f(ctx, { set, skyPreset: low === false ? C.GALAXY : C.GALAXY_LOW, skyOpts: { intensity: 1.6 }, ...rest });
  if (lift) { const P = ctx.post.params; ctx.post.set({ exposure: P.exposure * NIGHT_LIFT.exp, grade: { saturation: (P.grade.saturation ?? 1) * NIGHT_LIFT.sat } }); }
  return rig;
}
// Review fix: night exteriors were crushed and oversaturated against the approved s09 (QA gate mean 70-95, sat <= 0.6).
const NIGHT_LIFT = { hemi: 1.3, exp: 1.15, sat: 0.86 };
function camBasis(ctx) { ctx.camera.apply(0); const cam = ctx.cam; const pos = cam.position.clone(); const fwd = new THREE.Vector3(0, 0, -1).applyQuaternion(cam.quaternion); const right = new THREE.Vector3(1, 0, 0).applyQuaternion(cam.quaternion); const upv = new THREE.Vector3(0, 1, 0).applyQuaternion(cam.quaternion); return { pos, fwd, right, up: upv }; }
function warmKey(ctx, subject, { cd = 2.6, d = 0.8, color = '#ffc08a', side = 35, el = 35 } = {}) {
  const B = camBasis(ctx); const s = P3(subject); const back = B.fwd.clone().negate(); back.y = 0; back.normalize();
  const dir = back.clone().addScaledVector(B.right, -Math.tan(side * DEG)); dir.y = Math.tan(el * DEG); dir.normalize();
  return ctx.add(ctx.lights.point({ color, intensity: cd, pos: s.clone().addScaledVector(dir, d).toArray(), decay: 2 }));
}
function coolRim(ctx, subject, { intensity = 0.8, color = '#8a90ff' } = {}) {
  const B = camBasis(ctx); const s = P3(subject); const p = s.clone().addScaledVector(B.fwd, 6).addScaledVector(B.right, 5).add(new THREE.Vector3(0, 4, 0));
  return ctx.add(ctx.lights.sun({ color, intensity, pos: p.toArray(), target: s.toArray(), shadow: false }));
}
// Board camera (part3): subject (world m), yaw (deg about +Y from `ref`, the horizontal direction subject -> camera at
// yaw 0), dist / height in studs (height from `ground`), pitch in degrees (+ looks up); aimY (m) overrides the pitch.
function boardCam(ctx, subj, { ref = [0, 0, 1], yaw = 0, dist, h, pitch = 0, ground = 0, fov, aimY = null }) {
  const r0 = P3(ref); const d = new THREE.Vector3(r0.x, 0, r0.z).normalize().applyAxisAngle(YAX, yaw * DEG); const s = P3(subj);
  const pos = s.clone().addScaledVector(d, dist * S); pos.y = ground + h * S;
  const hd = Math.hypot(s.x - pos.x, s.z - pos.z); const tgt = s.clone(); tgt.y = aimY ?? pos.y + hd * Math.tan(pitch * DEG);
  ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov }); return { pos, tgt };
}
const worldOf = (o) => { o.updateWorldMatrix(true, false); return o.getWorldPosition(new THREE.Vector3()); };

// part2's front door: banged open in s28 and left open (warm hall light).
function frontDoor(ctx, door = LOT_DOOR, { light = 3.2 } = {}) {
  const W = 1.27, Hh = 2.39, z = door[2] - 0.045; const g = new THREE.Group(); g.name = 'p4FrontDoor';
  const glowMat = ctx.cache('p2:doorGlowMat', () => new THREE.MeshBasicMaterial({ color: new THREE.Color('#ffc890').multiplyScalar(1.35), fog: false }));
  const glow = new THREE.Mesh(new THREE.PlaneGeometry(W, Hh), glowMat); glow.position.set(door[0], door[1] + Hh / 2, z + 0.01); glow.renderOrder = 2; g.add(glow);
  const leafMat = ctx.cache('p2:doorLeafMat', () => new THREE.MeshStandardMaterial({ map: doorTex('#7a2a20'), roughness: 0.5 }));
  const edgeMat = ctx.cache('p2:doorEdgeMat', () => new THREE.MeshStandardMaterial({ color: '#5a1a14', roughness: 0.6 }));
  const hinge = new THREE.Group(); hinge.position.set(door[0] - W / 2, door[1], z + 0.03); hinge.rotation.y = -1.75; g.add(hinge);
  const leaf = new THREE.Mesh(new THREE.BoxGeometry(W, Hh, 0.05), [edgeMat, edgeMat, edgeMat, edgeMat, leafMat, leafMat]); leaf.position.set(W / 2, Hh / 2, 0); hinge.add(leaf);
  if (light) ctx.add(ctx.lights.point({ color: '#ffc890', intensity: light, pos: [door[0], door[1] + 1.7, door[2] + 0.55], decay: 2 }));
  const halo = C.pxSprite(C.addSpriteMat(ctx.tex.radialGlow({ falloff: 2.2 }), '#ffcf98', 0.8), 260); halo.position.set(door[0], door[1] + 1.4, z + 0.15); halo.renderOrder = 6; halo.material.opacity = 0.35; g.add(halo);
  ctx.add(g); return g;
}
// The lantern on its ring (pendulum, decaying), u = seconds since the swing started (part2).
function lanternSwing(g, u, { amp = 12, freq = 1.4, decay = 1.0, phase = Math.PI / 2 } = {}) {
  const L = g.getObjectByName('lantern'); if (!L) return; const a = amp * DEG * Math.exp(-decay * Math.max(0, u)) * Math.sin(2 * Math.PI * freq * u + phase);
  L.rotation.z = a; L.rotation.x = 0.3 * a;
}
// Grandpa's lantern, lit since s38 (level 1, flicker) with the 5-stud ring on the ground (following the lantern).
function grandpaLantern(ctx, g, o = {}) { const L = X.lanternLight(ctx, g, { t0: -1, ring: 5, burst: false, cd: 1.6, ...o }); ctx.add(L.group); return L; }
// The family gnomes' lanterns on our lawn, lit in the s40 cascade: 2-stud pools, no point lights (cheap).
function familyLanterns(ctx, H, { skip = [] } = {}) {
  const fam = H.ep01.gnomes.family || {}; const out = [];
  for (const [slot, g] of Object.entries(fam)) { if (skip.includes(slot) || !g.getObjectByName('lantern')) continue; const L = X.lanternLight(ctx, g, { t0: -1, ring: 2, ringOpts: { boost: 1.5, rimBoost: 2.6, rimA: 0.5 }, burst: false, light: false, haloPx: 48, seed: 'p3fam' + slot }); ctx.add(L.group); out.push(L); }
  return { update: (t) => { for (const L of out) L.update(t); } };
}
// Room frame of heroLot's bedroom (studs, origin on the floor at the inner wall face, centred on the window, +Z out):
// recovered from the sets owner's room_toWindow view, whose room-frame position is [3.2, 4.8, -10.8] (interiors.js).
function roomFrame(H) { const v = H.ep01.views.room_toWindow; const O = P3(v.pos).sub(new THREE.Vector3(3.2 * S, 4.8 * S, -10.8 * S)); return (x, y, z) => O.clone().add(new THREE.Vector3(x * S, y * S, z * S)); }
// A sleeping child on the room's bed (heroLot room anchors). 'side' = on the side facing the window (seen from outside,
// part3's Theo); 'up' = on the back with the face tilted `tilt` deg toward `toward` (seen from inside the room).
const SLEEP_POSE = { armLx: 78, armRx: 70, armLz: -16, armRz: -10, legLx: 42, legRx: 26, neckX: -6 };
const BACK_POSE = { armLx: 10, armRx: 10, armLz: 6, armRz: 6, legLx: 4, legRx: -4, neckX: 0 };
function sleeper(ctx, H, name, { sc = 0.75, lie = 'side', toward = null, tilt = 50, lift = 0.1, pose = null, whale = false, slide = 0, anchor = null } = {}) {
  const A = anchor || H.ep01.room.sleeper; const av = K.makeCharacter(name, { face: 'sleeping' });
  if (whale) CR.holdWhale(av, CR.stuffedWhale(), 'asleep');
  K.setPose(av, pose || (lie === 'side' ? SLEEP_POSE : BACK_POSE));
  const yAx = V3(A.head).sub(V3(A.body)).setY(0).normalize(); let zAx;
  if (lie === 'side') zAx = new THREE.Vector3(0, 0, 1);
  else { const tc = toward ? P3(toward).sub(V3(A.head)).setY(0).normalize() : new THREE.Vector3(0, 0, -1); tc.addScaledVector(yAx, -tc.dot(yAx)).normalize(); zAx = new THREE.Vector3(0, 1, 0).multiplyScalar(Math.cos(tilt * DEG)).addScaledVector(tc, Math.sin(tilt * DEG)).normalize(); }
  const xAx = new THREE.Vector3().crossVectors(yAx, zAx).normalize(); zAx = new THREE.Vector3().crossVectors(xAx, yAx).normalize();
  av.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(xAx, yAx, zAx));
  const top = (1 + A.top) * S;                          // mattress top (world m): room floor = 1 stud
  av.position.copy(V3(A.head)).addScaledVector(yAx, -(4.6 + slide) * S * sc);
  av.position.y = top + (lie === 'side' ? 1.0 : 0.5) * S * sc + lift * S;
  ctx.add(av); av.updateWorldMatrix(true, true); return av;
}
// part3's Theo asleep on the bare mattress, on his side facing the window, curled round the whale.
const MATTRESS_TOP = 0.66;
function theoAsleep(ctx, H, { blanket = false } = {}) {
  const A = H.ep01.room.sleeper; const theo = K.makeCharacter('theo', { face: 'sleeping' }); const sc = 0.85;
  const wh = CR.stuffedWhale(); CR.holdWhale(theo, wh, 'asleep'); K.setPose(theo, SLEEP_POSE);
  const yAx = V3(A.head).sub(V3(A.body)).setY(0).normalize(); const zAx = new THREE.Vector3(0, 0, 1); const xAx = new THREE.Vector3().crossVectors(yAx, zAx).normalize();
  theo.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(xAx, yAx, zAx));
  theo.position.copy(V3(A.head)).addScaledVector(yAx, -4.6 * S * sc); theo.position.y = MATTRESS_TOP + 1.0 * S * sc; theo.position.z -= 0.05;
  // s69-s76: he has pulled his blue blanket up to his chest (the bare pyjama boxes read as crates from the room's back)
  if (blanket) { const bl = new THREE.Mesh(ctx.cache('ep01p4:blanketGeo2', () => { const g = new RoundedBoxGeometry(2.7, 3.0, 1.9, 3, 0.55); g.userData.persistent = true; return g; }), I.XM('fab:#4f7ac8')); bl.position.set(-0.05, 1.1, 0.05); bl.name = 'p4Blanket'; theo.add(bl); }
  ctx.add(theo); theo.updateWorldMatrix(true, true); return { theo, whale: wh };
}
// The guard hold (s58-s60, s65): the hero on the s57 spot, Grandpa against his chest facing him (looking up at him).
function guardHold(ctx, { face = 'sad', headYaw = 0, headPitch = 18, pose = HUG } = {}) {
  const hero = K.makeCharacter('heroBarefoot', { face }); hero.position.set(...GUARD); hero.rotation.y = GUARD_YAW; K.setPose(hero, pose); ctx.add(hero);
  const g = K.makeGnome('grandpa', { units: 'stud', lantern: 1, wear: 0.12 }); C.softenBeard(g);
  hero.getObjectByName('hips').add(g); g.position.set(...HOLD_OFF); g.rotation.y = Math.PI;
  K.setGnomeHead(g, headYaw, headPitch, 0); hero.updateWorldMatrix(true, true);
  ctx.add(sets.contactShadow(ctx, { pos: [GUARD[0], 0.005, GUARD[2]], radius: 0.42, opacity: 0.35 }));
  return { hero, g, head: worldOf(hero.getObjectByName('head')), fwd: dirOf(GUARD_YAW) };
}
// The kneel hold (s73-s75): kneeling right of the hole, Grandpa in both hands facing him. The gnome stays upright
// whatever the lean (it counter-rotates the hips' bodyX).
function kneelHold(ctx, { face = 'heartfelt', pose = KNEEL_HOLD } = {}) {
  const hero = K.makeCharacter('heroBarefoot', { face }); hero.position.set(...KNEEL_AT); hero.rotation.y = KNEEL_YAW; ctx.add(hero);
  const g = K.makeGnome('grandpa', { units: 'stud', lantern: 1, wear: 0.12 }); C.softenBeard(g);
  hero.getObjectByName('hips').add(g); g.position.set(...KNEEL_OFF);
  const setHold = (P) => { K.setPose(hero, P); g.rotation.set(-(P.bodyX || 0) * DEG, Math.PI, 0); };
  setHold(pose); hero.updateWorldMatrix(true, true);
  ctx.add(sets.contactShadow(ctx, { pos: [KNEEL_AT[0], KNEEL_AT[1] + 0.005, KNEEL_AT[2]], radius: 0.5, opacity: 0.35 }));
  return { hero, g, setHold, fwd: dirOf(KNEEL_YAW) };
}
// The agent board by the path: seen from the house side its back face shows the FOR SALE text mirrored (props.js,
// sets README note); in the house-side close-ups (s58, s65, s71 through the glass) it is only background, so it is hidden.
function hideBoard(H) { const b = H.ep01.board; if (b) b.visible = false; }
// The sepia / B&W flashback night on the lot (part1's sepiaLight): the night-lawn preset, then the flashback grade.
function flashbackLight(ctx, H, grade = 'sepia', o = {}) {
  const { exposure, ...rest } = o;
  const rig = H.ep01.light(ctx, { skyPreset: C.GALAXY_LOW, skyOpts: { intensity: 1.4 }, window: { n: 2, cd: 2.4, color: '#ffd9a0', maxD: 14 }, ...rest });
  ctx.post.set(sets.postPreset(grade, { exposure: exposure ?? 1.12 })); return rig;
}
// Light decals (additive; X.boostBlend 'boost' mode: dst x (1 + src)) with the falloff in RGB, not alpha: a soft radial
// spot and a soft band (a bright stripe along u, soft across v and at both ends), black outside.
function boostTex(ctx, kind) {
  return ctx.cache('ep01p4:boostTex2:' + kind, () => {
    const W = 256, Hh = kind === 'band' ? 128 : 256; const c = document.createElement('canvas'); c.width = W; c.height = Hh; const g = c.getContext('2d');
    g.fillStyle = '#000'; g.fillRect(0, 0, W, Hh);
    if (kind === 'band') { const img = g.getImageData(0, 0, W, Hh); for (let y = 0; y < Hh; y++) for (let x = 0; x < W; x++) { const v = Math.abs(y / (Hh - 1) * 2 - 1), u = Math.abs(x / (W - 1) * 2 - 1); const sv = Math.min(1, Math.max(0, (1 - v) / 0.55)); const k = sv * sv * (3 - 2 * sv) * Math.pow(Math.max(0, 1 - Math.pow(u, 4)), 1.2); const i = (y * W + x) * 4; img.data[i] = img.data[i + 1] = img.data[i + 2] = Math.round(255 * k); img.data[i + 3] = 255; } g.putImageData(img, 0, 0); }
    else { const gr = g.createRadialGradient(W / 2, Hh / 2, 0, W / 2, Hh / 2, W / 2); gr.addColorStop(0, '#fff'); gr.addColorStop(0.35, '#9a9a9a'); gr.addColorStop(0.7, '#262626'); gr.addColorStop(1, '#000'); g.fillStyle = gr; g.fillRect(0, 0, W, Hh); }
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.NoColorSpace; t.userData.persistent = true; return t;
  });
}
function boostDecal(ctx, kind, color, k, w, h, { mode = 'add' } = {}) {
  // 'tint': a warm glaze (normal blending, the falloff as alphaMap, k = opacity): reads on bright skin, where an additive
  // stripe vanishes in the tone curve
  const m = mode === 'tint' ? new THREE.MeshBasicMaterial({ alphaMap: boostTex(ctx, kind), color: new THREE.Color(color), opacity: k, fog: false, transparent: true, depthWrite: false })
    : new THREE.MeshBasicMaterial({ map: boostTex(ctx, kind), color: new THREE.Color(color).multiplyScalar(k), fog: false, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending });
  if (mode === 'boost') X.boostBlend(m); const q = new THREE.Mesh(new THREE.PlaneGeometry(w, h), m); q.renderOrder = 8; return q;
}
// Solve one pose key (bisection) so a hand socket (or the midpoint of both) reaches the target height y (world m).
function solveArm(av, pose, key, y, { lo = -20, hi = 170, both = null, side = 'R' } = {}) {
  const hand = () => { K.setPose(av, pose); av.updateMatrixWorld(true); if (both) return worldOf(K.handSocket(av, 'L')).add(worldOf(K.handSocket(av, 'R'))).multiplyScalar(0.5); return worldOf(K.handSocket(av, side)); };
  for (let i = 0; i < 24; i++) { const m = (lo + hi) / 2; pose[key] = m; if (both) pose[both] = m; const h = hand(); if (h.y > y) hi = m; else lo = m; }
  pose[key] = (lo + hi) / 2; if (both) pose[both] = pose[key]; return hand();
}
// part1's lap loop (s22 / s63): an oval round the middle of the lawn with a dent toward the house under bed0's window.
function lapCurve(H) {
  const v = H.ep01.views.lapTop; const B = P3(H.ep01.spots.bed0); const ctr0 = P3(v.target); ctr0.y = 0; const ctr = ctr0.clone(); ctr.x = lerp(ctr0.x, B.x, 0.12);
  const rx = 5.9 * S, rz = 6.0 * S; const cz = ctr0.z + 0.4 * S; const pts = []; const N = 96;
  for (let i = 0; i < N; i++) {
    const a = (i / N) * Math.PI * 2; const x = ctr.x + Math.cos(a) * rx; let z = cz + Math.sin(a) * rz;
    const kx = B.x + 1.4 * S; const dk = Math.pow(Math.max(0, 1 - Math.abs(x - kx) / (1.3 * S)), 1.6) * (z < cz ? 1 : 0); z = lerp(z, Math.min(z, B.z + 2.2 * S), dk); pts.push(new THREE.Vector3(x, 0, z));
  }
  const curve = new THREE.CatmullRomCurve3(pts, true, 'catmullrom', 0.5);
  let kinkU = 0, bd = 1e9; for (let i = 0; i <= 400; i++) { const q = curve.getPointAt(i / 400); const d = q.distanceTo(new THREE.Vector3(B.x, 0, B.z)); if (d < bd) { bd = d; kinkU = i / 400; } }
  return { curve, ctr, cz, L: curve.getLength(), kinkU };
}
// part1's worn lap path texture (identical drawing, its own cache key).
function lapTexture(ctx, key, pts) {
  return ctx.cache('ep01p4:lapTex:' + key, () => {
    const N = 1024, c = document.createElement('canvas'); c.width = c.height = N; const g = c.getContext('2d'); g.clearRect(0, 0, N, N);
    g.lineCap = g.lineJoin = 'round';
    const path = () => { g.beginPath(); pts.forEach(([u, v], i) => (i ? g.lineTo(u * N, v * N) : g.moveTo(u * N, v * N))); g.closePath(); };
    g.strokeStyle = 'rgba(214,226,150,0.42)'; g.lineWidth = 46; path(); g.stroke();
    g.strokeStyle = 'rgba(240,248,190,0.30)'; g.lineWidth = 22; path(); g.stroke();
    const r = makeRng(hash32('ep01p1', 'lapStreaks')); g.strokeStyle = 'rgba(70,90,40,0.25)'; g.lineWidth = 2;
    for (let i = 0; i < pts.length; i++) { const [u0, v0] = pts[i], [u1, v1] = pts[(i + 1) % pts.length]; for (let k = 0; k < 3; k++) { const o = (r() - 0.5) * 30; g.beginPath(); g.moveTo(u0 * N + o, v0 * N + o * 0.3); g.lineTo(u1 * N + o, v1 * N + o * 0.3); g.stroke(); } }
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; t.userData.persistent = true; return t;
  });
}
// Grandpa (or young Grandpa) outside the window, his hand flat on the pane, the torch pointing down at the lawn (s66/s67).
function grandpaAtGlass(ctx, name, { face = 'heartfelt', back = 1.75, dx = 0.35 } = {}) {
  const gp = K.makeCharacter(name, { face }); const z0 = WIN[2] + back * S; gp.position.set(WIN[0] + dx * S, BED[1], z0); gp.rotation.y = Math.PI; ctx.add(gp);
  const pose = { bodyX: 10, armLx: 90, armLz: 6, armRx: 14, armRz: 4, neckX: 4 };
  // solve the left arm so the hand reaches the glass plane (z), at about face height
  let lo = 40, hi = 175; const hs = K.handSocket(gp, 'L');
  for (let i = 0; i < 22; i++) { const m = (lo + hi) / 2; pose.armLx = m; K.setPose(gp, pose); gp.updateMatrixWorld(true); const h = worldOf(hs); if (h.z < WIN[2] + 0.06) hi = m; else lo = m; }
  pose.armLx = Math.min(lo, 150); K.setPose(gp, pose); gp.updateMatrixWorld(true);
  const fl = CR.makeFlashlight({ on: 1, light: false }); CR.holdFlashlight(gp, fl, { axis: 'forward' }); gp.updateMatrixWorld(true);
  CR.aimFlashlight(fl, new THREE.Vector3(gp.position.x - 0.5, 0.0, gp.position.z + 0.9)); gp.updateMatrixWorld(true);
  return { gp, fl, pose };
}

// ==================================================================================================================
export const PART = 4;
export const builders = {

  // s58 "And tomorrow night?" (65.43-66.35) - CU on his face as it sinks in, worried (sad decal); the lantern between
  // them lights him from below; behind him, past the ring's edge, the mounds wait with their amber reflector eyes lit
  // (s57's mounds). h 4.6, d 2.4, yaw 10 (from his facing), pitch 0, push 25 %.
  tomorrow_night: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); frontDoor(ctx); theoAsleep(ctx, H);
      const { hero, g, head, fwd } = guardHold(ctx, { face: p.cast[0].face || 'sad', pose: { ...HUG, neckX: -12 } }); ctx.shared.g = g; ctx.shared.hero = hero;
      hideBoard(H);
      // the lens 0.6 stud above the board's 4.6 and 4 deg down: from eye level his shoulders hide every eye pair behind him
      // and his face framed left of centre (target 0.09 m right): his hair spikes fill the frame width when centred
      const bc = boardCam(ctx, head.clone().setY(0), { ref: fwd.toArray(), yaw: c.yaw_deg, dist: c.dist_studs, h: c.height_studs + 0.6, pitch: c.pitch_deg - 10, fov: p.fov }); // review: -6 deg more so his eyes clear the caption band
      { const B0 = camBasis(ctx); ctx.camera.set({ target: bc.tgt.clone().addScaledVector(B0.right, 0.09).toArray() }); } basePush(ctx);
      C.gazeAt(g, head);
      nightRig(ctx, H, 'nightHigh', { lamp: { n: 2 }, window: { n: 0 }, postOpts: CU_GRADE });
      coolRim(ctx, head.toArray(), { intensity: 0.9 });
      const B = camBasis(ctx); const lan = worldOf(g.getObjectByName('lantern')); const off = B.pos.clone().sub(lan).multiplyScalar(0.45).add(new THREE.Vector3(0, -0.05, 0));
      ctx.shared.GL = grandpaLantern(ctx, g, { cd: 0.55, lightOffset: off.toArray() }); ctx.shared.fam = familyLanterns(ctx, H);
      warmKey(ctx, head.toArray(), { cd: 0.5, d: 0.9, color: '#ffc8a0' });
      // the eye pairs, placed by casting rays through the open right third of the frame (NDC inside the end-of-push
      // frame) onto the lawn: 3-4.6 m behind him, well outside the 5-stud ring
      ctx.camera.apply(0); const ray = new THREE.Raycaster(); const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), -0.26); const spots = [];
      // two pairs flanking the lit family gnome in the visible strip of lawn right of his head (initial NDC; the 25 %
      // push keeps x <= 0.8 in frame), 4-5 m behind him
      for (const [nx, ny] of [[0.46, -0.31], [0.76, -0.27]]) { ray.setFromCamera(new THREE.Vector2(nx, ny), ctx.cam); const q = new THREE.Vector3(); if (ray.ray.intersectPlane(plane, q)) { const d = q.clone().sub(B.pos).setY(0); spots.push(B.pos.clone().add(d.setLength(Math.min(d.length(), 5.4))).setY(0)); } }
      const f = CR.moleField(ctx, { center: [lan.x + B.fwd.x * 3.2, lan.z + B.fwd.z * 3.2], size: [30, 26], res: 96, seed: 's58', heads: 'snout' }); ctx.add(f.group);
      spots.forEach((q, i) => { const k = f.add({ at: [q.x, q.z], scale: [1.2, 1.1, 1.25][i], face: [B.pos.x, B.pos.z] }); f.eyes(k, -5, null); f.travel(k, [[q.x, q.z], [q.x + 0.04 * Math.cos(i), q.z + 0.04 * Math.sin(i)]], 0, 0.12); });
      ctx.shared.f = f;
      // the reflector eyes as small screen-constant amber glows on the kit's eye positions (at 4-5 m the lit eye domes
      // are a few pixels: the glow is what reads in the dark, like the references' eyes in the night)
      const eyeMat = () => C.addSpriteMat(ctx.tex.radialGlow({ falloff: 2.0 }), '#ffae2a', 2.4, { depthTest: true });
      ctx.shared.eyeGlow = spots.map(() => [0, 1].map(() => { const sp = C.pxSprite(eyeMat(), 15); sp.renderOrder = 14; ctx.add(sp); return sp; }));
      ctx.shared.fx = sparks(ctx, head.clone().lerp(B.pos, 0.4), [0.9, 0.7, 0.4], 6, 's58', { px: [40, 70] });
    },
    update(ctx, t) {
      const s = ctx.shared; lanternSwing(s.g, t + 2.8, { amp: 8, decay: 0.8 }); K.gnomeIdle(s.g, t, { seed: 's58', amp: 0.2 }); s.GL.update(t); s.fam.update(t); s.f.update(t); s.fx.update(t);
      s.eyeGlow.forEach((pair, i) => { const e = X.fieldEyes(s.f, i); if (!e) return; pair.forEach((sp, j) => { if (e[j]) { sp.position.copy(e[j]); sp.material.opacity = 0.85 + 0.15 * Math.sin(2 * Math.PI * 0.7 * t + i * 2.1); } }); });
    },
  },

  // s59 "Grandpa turned his head," (66.35-67.38) - low CU on the gnome in his arms (we see the back of his head, the
  // hero's arms round him): from 66.55 his ceramic head grinds round 150 deg away from the hero toward the window, in
  // stepped 2.5 deg jerks every 3 frames, inOutSine, and stares past the lens. h 2.6, d 1.4, push 20 %.
  head_grind: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); theoAsleep(ctx, H);
      const { hero, g, head, fwd } = guardHold(ctx, { face: 'sad', pose: { ...HUG, neckX: -16 } }); ctx.shared.g = g; ctx.shared.hero = hero;
      C.gazeAt(g, head); const eyes = C.eyesOf(g);
      // yaw -35 from his facing: the side the head turns to, so the turned face ends staring just past the lens. Aimed at
      // the gnome's eyes (the board's pitch 10 from 2.6 studs would put his face at the top edge)
      boardCam(ctx, eyes.clone().setY(0), { ref: fwd.toArray(), yaw: c.yaw_deg, dist: c.dist_studs, h: c.height_studs, fov: p.fov, aimY: eyes.y - 0.07 }); basePush(ctx);
      nightRig(ctx, H, 'nightHigh', { lamp: { n: 2 }, window: { n: 0 }, postOpts: CU_GRADE });
      coolRim(ctx, eyes.toArray(), { intensity: 1.0 });
      const lan = worldOf(g.getObjectByName('lantern'));
      ctx.shared.GL = grandpaLantern(ctx, g, { cd: 1.0, lightOffset: head.clone().sub(lan).multiplyScalar(0.25).toArray() }); ctx.shared.fam = familyLanterns(ctx, H);
      warmKey(ctx, eyes.toArray(), { cd: 0.9, d: 0.6, color: '#ffc8a0' });
      const t0 = evT(ctx, 0, 0.2); const dur = Math.min(0.8, ctx.shot.duration - 0.1 - t0); Object.assign(ctx.shared, { t0, dur });
      const B = camBasis(ctx); ctx.shared.fx = sparks(ctx, eyes.clone().lerp(B.pos, 0.4), [0.7, 0.6, 0.35], 7, 's59', { px: [40, 72] });
    },
    update(ctx, t) {
      const s = ctx.shared; const yaw = K.gnomeHeadTurn(t, s.t0, s.dur, 0, 150, { jitter: 2.5, every: 3 }); const k = clamp01((t - s.t0) / s.dur);
      K.setGnomeHead(s.g, yaw, lerp(18, 12, k), 0); K.setGnomeGaze(s.g, 0, 4 * (1 - k));
      lanternSwing(s.g, t + 3.8, { amp: 8, decay: 0.8 }); s.GL.update(t); s.fam.update(t); s.fx.update(t);
    },
  },

  // s60 "away from me, toward my old window." (67.38-69.07) - low and close beside the gnome's turned head (it stares
  // toward the window): the hero's hurt face above it; on "toward" (68.11) a 55 deg whip pan (0.5 s, inOutSine, frames
  // sharp) runs past the hat to Theo's window: Theo asleep behind the lit glass. +12 % push throughout.
  away_to_window: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); const { theo } = theoAsleep(ctx, H);
      // near (left) arm lowered under the gnome's base: hugged, it crossed the lens as a giant sleeve
      const { hero, g, head } = guardHold(ctx, { face: p.cast[0].face || 'sad', headYaw: 150, headPitch: 12, pose: { ...HUG, armLx: 24, armLz: -6, neckX: -18, neckY: 22 } }); ctx.shared.g = g;
      const ge = C.eyesOf(g); const face = worldOf(hero.getObjectByName('head'));
      // the lens: low, beside the gnome at the hero's front-left (-86 deg, 0.95 m from him), so the hero's face and the
      // window are 55 deg apart as seen from it (geometry solved for the board's whip; yaw 160 / d 0.9 cannot frame both)
      const phi = -86 * DEG, R = 0.95; const cp = new THREE.Vector3(GUARD[0] + Math.sin(phi) * R, c.height_studs * S, GUARD[2] + Math.cos(phi) * R);
      const A0 = ge.clone().lerp(face, 0.85); const th = worldOf(theo.getObjectByName('head')); const A1 = th.clone().lerp(P3(WIN), 0.45); A1.x -= 0.3 * S;   // review: his hurt face framed, Theo clear of the muntins
      const ang = (v) => { const d = v.clone().sub(cp); return [Math.atan2(d.x, d.z), Math.atan2(d.y, Math.hypot(d.x, d.z))]; };
      const [y0, p0] = ang(A0), [y1, p1] = ang(A1); let dy = y1 - y0; while (dy > Math.PI) dy -= 2 * Math.PI; while (dy < -Math.PI) dy += 2 * Math.PI;
      const tw = tOnset(ctx, TOWARD_ONSET); const wd = c.move.dur ?? 0.5; const rise = 0.62;   // the lens rises 0.62 m in the whip (Theo, asleep on the floor mattress, clears the sill)
      // ... and swings 1.1 m right and 1 m toward the house during the whip: Theo sleeps at the room's left end, seen through the glass only from
      // right of the window centre (from the start position he is behind the frame's left edge)
      const cp1 = new THREE.Vector3(WIN[0] + 0.15, cp.y + rise, GUARD[2] - 0.95); /* in front of the gnome's head: the path passes 0.3 m clear of it */ const [y1b, p1b] = (() => { const d = A1.clone().sub(cp1); return [Math.atan2(d.x, d.z), Math.atan2(d.y, Math.hypot(d.x, d.z))]; })();
      let dyb = y1b - y0; while (dyb > Math.PI) dyb -= 2 * Math.PI; while (dyb < -Math.PI) dyb += 2 * Math.PI;
      Object.assign(ctx.shared, { tw, wd, dy: dyb, cp, A0, A1 }); void dy; void p1;
      const posAt = (t, o) => { const u = inOutSine((t - tw) / wd); return (o || new THREE.Vector3()).copy(cp).lerp(cp1, u); };
      ctx.camera.set({
        pos: posAt,
        target: (t, o) => { const u = inOutSine((t - tw) / wd); const yy = y0 + dyb * u, pp = lerp(p0, p1b, u); const q = (o || new THREE.Vector3()).set(Math.sin(yy) * Math.cos(pp), Math.sin(pp), Math.cos(yy) * Math.cos(pp)).multiplyScalar(2.0); return q.add(posAt(t)); },
        fov: p.fov });
      basePush(ctx, { Z: c.move.base_push ?? 0.12 });
      nightRig(ctx, H, 'nightHigh', { lamp: { n: 2 }, window: { n: 1, cd: 2.0, maxD: 10 }, postOpts: CU_GRADE });
      ctx.add(ctx.lights.sun({ color: '#8a90ff', intensity: 0.9, pos: face.clone().add(new THREE.Vector3(-4, 4, 3)).toArray(), target: face.toArray(), shadow: false }));
      const lan = worldOf(g.getObjectByName('lantern'));
      ctx.shared.GL = grandpaLantern(ctx, g, { cd: 1.0, lightOffset: head.clone().sub(lan).multiplyScalar(0.3).toArray() }); ctx.shared.fam = familyLanterns(ctx, H);
      ctx.add(ctx.lights.point({ color: '#ffc8a0', intensity: 0.7, pos: face.clone().lerp(cp, 0.5).add(new THREE.Vector3(0, 0.25, 0)).toArray(), decay: 2 }));
      ctx.shared.fx = sparks(ctx, cp.clone().lerp(face, 0.45), [0.8, 0.6, 0.6], 6, 's60', { px: [40, 70] });
      ctx.shared.fx2 = sparks(ctx, P3(WIN).add(new THREE.Vector3(0.4, -0.4, 0.9)), [1.6, 1.0, 0.8], 6, 's60w', { px: [40, 70] });
    },
    update(ctx, t) { const s = ctx.shared; K.gnomeIdle(s.g, t, { seed: 's60', amp: 0.2 }); lanternSwing(s.g, t + 4.8, { amp: 8, decay: 0.8 }); s.GL.update(t); s.fam.update(t); s.fx.update(t); s.fx2.update(t); },
  },

  // s64 "And one stop, always under my window." (70.90-72.83) - sepia, 2010s. From s63's top-down lap (the lapTop view,
  // ending framing of s63: zoom 1.15, roll 4) the camera cranes down 34 -> 4.6 studs and tilts -90 -> -4 deg in 1.4 s
  // (outCubic) into the kink: Grandpa walks the loop into it and stops on "stop" (8-frame walk -> stand), facing the
  // window, his torch beam resting on the lawn; inside, the hero aged 5 asleep. Then +10 % push.
  fb_one_stop: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = SE.heroLot(ctx, { tod: 'night', era: '2010s', keepOff: true }); ctx.add(H);
      const v = H.ep01.views.lapTop; const lc = lapCurve(H);
      const ext = 18 * S; const toUV = (q) => [(q.x - (lc.ctr.x - ext)) / (2 * ext), (q.z - (lc.cz - ext)) / (2 * ext)];
      const tex = lapTexture(ctx, 'v3', lc.curve.getSpacedPoints(160).map(toUV));
      const plane = new THREE.Mesh(new THREE.PlaneGeometry(2 * ext, 2 * ext), new THREE.MeshStandardMaterial({ map: tex, transparent: true, depthWrite: false, roughness: 0.6, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }));
      plane.rotation.x = -Math.PI / 2; plane.position.set(lc.ctr.x, 0.02, lc.cz); plane.renderOrder = 2; ctx.add(plane);
      // the hero aged 5 asleep on his small bed, on his side facing the window (seen from the lawn)
      sleeper(ctx, H, 'heroKid5', { sc: 0.75, lie: 'side', lift: 0.25 });
      // Grandpa: along the loop (clockwise from above, as in s63) into the kink; stops on "stop"
      const tS = evT(ctx, 'stop', 0.467); const vW = 3.4 * S;
      const gp = K.makeCharacter('grandpa', { face: p.cast[0].face || 'heartfelt' }); ctx.add(gp);
      const fl = CR.makeFlashlight({ on: 1, light: false }); CR.holdFlashlight(gp, fl, { axis: 'forward' });
      const kink = lc.curve.getPointAt(lc.kinkU); const faceYaw = Math.atan2(WIN[0] - kink.x, WIN[2] - kink.z);
      const Bm = X.flashlightBeam(ctx, { torch: fl, t0: -1, length: 6, angle: 18, cd: 3, opacity: 0.16, motes: 5 }); ctx.add(Bm.group);
      const sh = sets.contactShadow(ctx, { pos: [kink.x, 0.006, kink.z], radius: 0.4, opacity: 0.35 }); ctx.add(sh);
      // camera: s63's last framing (lapTop, zoomed 1.15, rolled 4 deg) -> behind Grandpa at 4.6 studs, pitch -4
      const P0 = P3(v.pos), T0 = P3(v.target); const fov0 = 2 * Math.atan(Math.tan((v.fov / 2) * DEG) / 1.15) / DEG;
      // end: MS behind him at 4.6 studs, 3.6 m back and 0.65 m left of the window, so he stands right of the glass and the
      // sleeping boy (head at the left end of the bed) reads past his shoulder
      const P1 = new THREE.Vector3(WIN[0] - 0.65, c.move.to_h * S, kink.z + 3.6); const T1 = new THREE.Vector3(WIN[0] + 0.05, 0, WIN[2]); T1.y = P1.y + Math.hypot(T1.x - P1.x, T1.z - P1.z) * Math.tan((c.move.to_pitch ?? -4) * DEG);
      const cd = c.move.dur ?? 1.4; const roll0 = 4;
      ctx.camera.set({
        pos: (t, o) => { const u = outCubic(t / cd); return (o || new THREE.Vector3()).copy(P0).lerp(P1, u).add(new THREE.Vector3(-4 * S * Math.sin(Math.PI * clamp01(u)), 0, 6 * S * Math.sin(Math.PI * clamp01(u)))); },   // review: the crane arcs 3 studs out over the lawn (it passed through the porch roof)
        // the target slides from the ground point under the lens to the window; a small -z lead keeps "up" = the house
        target: (t, o) => { const u = outCubic(t / (cd * 0.75)); const q = (o || new THREE.Vector3()).copy(T0).lerp(T1, u); return q; },   // the aim settles on the window a little before the lens lands (mid-crane it would sweep the porch column)
        fov: (t) => lerp(fov0, v.fov, outCubic(t / cd)), roll: (t) => roll0 * (1 - outCubic(t / cd)) });
      basePush(ctx, { Z: c.move.base_push ?? 0.1 });
      flashbackLight(ctx, H, 'sepia', { subject: { pos: [kink.x, 3.6 * S, kink.z], cd: 0.8, color: '#ffe6c8' }, exposure: 1.15 });
      // the room glow reads through the glass on the sleeping boy
      ctx.add(ctx.lights.point({ color: '#ffd9b0', intensity: 1.6, pos: up(WIN, -0.6, 0.6, -2.4), decay: 2 }));
      Object.assign(ctx.shared, { gp, fl, Bm, sh, lc, tS, vW, faceYaw });
    },
    update(ctx, t) {
      const s = ctx.shared; const { lc } = s;
      const d = Math.max(0, s.tS - t) * s.vW; const u = (lc.kinkU + d / lc.L) % 1; const q = lc.curve.getPointAt(u); const tan = lc.curve.getTangentAt(u).negate();
      const walkYaw = Math.atan2(tan.x, tan.z); const k = outQuad((t - s.tS) / (8 / 60));
      let dyaw = s.faceYaw - walkYaw; while (dyaw > Math.PI) dyaw -= 2 * Math.PI; while (dyaw < -Math.PI) dyaw += 2 * Math.PI;
      s.gp.position.set(q.x, 0, q.z); s.gp.rotation.y = walkYaw + dyaw * k; s.sh.position.set(q.x, 0.006, q.z);
      const amp = 1 - k; const wc = K.walkCycle(t, { period: 1.0, legs: 25 * amp, holdArms: true });
      K.setPose(s.gp, { ...wc, armLx: -(wc.legLx || 0) * 0.8, armRx: lerp(40, 22, k), armRz: 4, neckX: lerp(0, 8, k) });
      s.gp.updateMatrixWorld(true);
      const fw = dirOf(s.gp.rotation.y); const aim = s.gp.position.clone().addScaledVector(fw, lerp(1.4, 1.1, k) * S).add(new THREE.Vector3(fw.z, 0, -fw.x).multiplyScalar(0.45 * k * S));
      CR.aimFlashlight(s.fl, aim); CR.setFlashlight(s.fl, 1); s.gp.updateMatrixWorld(true); s.Bm.update(t);
    },
  },

  // s65 "Checking for moles?" (72.83-74.02) - back in the present: CU, his eyes fill (wetEyes decal), a choked half-laugh
  // (a small jolt on "moles"); Grandpa warm in his arms at frame bottom, his head still turned toward the window.
  // h 4.6, d 2.3, yaw -10, pitch -2, push 22 %, roll -1.
  hero_wet_eyes: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); frontDoor(ctx); theoAsleep(ctx, H);
      const { hero, g, head, fwd } = guardHold(ctx, { face: p.cast[0].face || 'wetEyes', headYaw: 150, headPitch: 10, pose: { ...HUG, neckX: -6 } }); ctx.shared.g = g; ctx.shared.hero = hero;
      hideBoard(H);
      boardCam(ctx, head.clone().setY(0), { ref: fwd.toArray(), yaw: c.yaw_deg, dist: c.dist_studs, h: c.height_studs, pitch: c.pitch_deg - 6, fov: p.fov }); basePush(ctx); paramRoll(ctx); // review: mouth out of the caption band
      nightRig(ctx, H, 'nightHigh', { lamp: { n: 2 }, window: { n: 0 }, postOpts: CU_GRADE });
      coolRim(ctx, head.toArray(), { intensity: 1.0 });
      const B = camBasis(ctx); const lan = worldOf(g.getObjectByName('lantern'));
      ctx.shared.GL = grandpaLantern(ctx, g, { cd: 0.6, lightOffset: B.pos.clone().sub(lan).multiplyScalar(0.45).toArray() }); ctx.shared.fam = familyLanterns(ctx, H);
      warmKey(ctx, head.toArray(), { cd: 0.6, d: 0.9, color: '#ffc8a0' });
      ctx.shared.f = { update() {} };
      ctx.shared.tL = evT(ctx, 'moles', tOnset(ctx, 73.245));
      ctx.shared.fx = sparks(ctx, head.clone().lerp(B.pos, 0.4).add(new THREE.Vector3(0, -0.15, 0)), [0.9, 0.8, 0.4], 7, 's65', { px: [40, 70] });
    },
    update(ctx, t) {
      const s = ctx.shared; const u = t - s.tL; const j = u < 0 ? 0 : Math.exp(-6 * u) * Math.sin(2 * Math.PI * 4.5 * u);   // the choked half-laugh: a little jolt
      K.setPose(s.hero, { ...HUG, neckX: -6 + 5 * j, bodyX: 2 * j, lift: 0.03 * Math.abs(j) });
      lanternSwing(s.g, t + 1.2, { amp: 6, decay: 0.8 }); K.gnomeIdle(s.g, t, { seed: 's65', amp: 0.2 }); s.GL.update(t); s.fam.update(t); s.f.update(t); s.fx.update(t);
    },
  },

  // s66 "He was checking on me." (74.02-74.90) - sepia, 2010s, from inside the room (mirror pair A): the hero aged 5 asleep
  // in his bed in the foreground; at the window Grandpa's kind face at the glass, his left hand flat on the pane, his
  // torch pointed down at the lawn (not into the room). h 3.0, d 6.0, yaw 0, pitch 0, push 19 %.
  fb_checking_me: { build(ctx) { mirrorPair(ctx, { era: '2010s', kid: 'heroKid5', gp: 'grandpa', grade: 'sepia' }); }, update(ctx, t) { mirrorPairUpdate(ctx, t); } },

  // s67 "Before me, he checked on Dad." (74.90-76.40) - B&W, the 1960s, the identical set-up (mirror pair B): young Grandpa
  // (dark hair and moustache) at the same window; asleep in the iron bed, the boy with Dad's sticking-out ears.
  bw_dad: { build(ctx) { mirrorPair(ctx, { era: '1960s', kid: 'dadKid', gp: 'grandpaYoung', grade: 'bw' }); }, update(ctx, t) { mirrorPairUpdate(ctx, t); } },

  // s68 "For 60 years," (76.40-77.37) / s69 "whoever was small in that room." (77.37-78.67) - the same window from
  // outside, the same set-up: the 1990s (sepia, yellow floral wallpaper, a girl with pigtails asleep on the top bunk, a
  // torch beam from frame left lying across the sill), then now (Theo asleep with his whale; the gold lantern light from
  // frame left on the glass instead of the torch). h 3.4, d 6.0, yaw 20, pitch 4, push 18 %.
  decades_window: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const now = p.phase === 'now' || !p.era;
      const H = now ? nightLot(ctx) : SE.heroLot(ctx, { tod: 'night', era: p.era || '1990s', keepOff: true }); if (!now) ctx.add(H);
      // the 1990s girl on the LOWER bunk: on the top one the window's horizontal muntin crosses her face from outside
      const R = roomFrame(H);
      if (now) theoAsleep(ctx, H, { blanket: true }); else sleeper(ctx, H, 'cousinKid', { sc: 0.75, lie: 'side', lift: 0.15, anchor: { head: R(-1.4, 2.1, -9.6).toArray(), body: R(1.2, 1.95, -9.6).toArray(), top: 1.65 } });
      // yaw 12 (board 20): the sleepers lie at the room's left end, so only a lens right of centre sees them through the
      // glass, but at 20 the porch column (2.6 studs right of the window) fills the right of the frame. h 4.0: the board's
      // 2.5 puts the lens under the line through the sill to Theo's floor mattress
      boardCam(ctx, [WIN[0], 0, WIN[2]], { ref: [0, 0, 1], yaw: Math.min(12, c.yaw_deg), dist: c.dist_studs + 0.6, h: 4.0, pitch: c.pitch_deg, fov: p.fov, aimY: WIN[1] - 0.12 }); basePush(ctx);
      const B = camBasis(ctx);
      // the light source just outside frame left (Grandpa's torch / the hero's lantern), 1.0 m up, 0.9 m out from the wall
      const halfW = Math.tan((p.fov / 2) * DEG) * 9 / 16; const src = B.pos.clone().addScaledVector(B.fwd, 1.6).addScaledVector(B.right, -1.6 * halfW * 1.25); src.y = now ? 0.95 : 1.15;
      const sill = new THREE.Vector3(WIN[0] + 0.15, WIN[1] - 0.72, WIN[2] + 0.12);
      if (now) {
        nightRig(ctx, H, 'nightHigh', { lamp: { n: 2 }, window: { n: 0 } });
        const L = ctx.add(ctx.lights.point({ color: '#ffb85c', intensity: 5.0, pos: src.toArray(), decay: 2 })); ctx.shared.L = L;
        // review: gold lantern light visibly on the glass (an additive warm glow on the lower-left panes) + a warm key on the sill
        { const gs = C.pxSprite(C.addSpriteMat(ctx.tex.radialGlow({ falloff: 1.5 }), '#ffa040', 2.2, { depthTest: false }), 420); gs.position.copy(P3(WIN).add(new THREE.Vector3(-0.3, -0.28, 0.1))); gs.renderOrder = 15; gs.material.opacity = 0.75; ctx.add(gs);
          ctx.add(ctx.lights.point({ color: '#ffb85c', intensity: 2.0, pos: sill.clone().add(new THREE.Vector3(-0.4, 0.5, 0.7)).toArray(), decay: 2 })); }
        const ring = X.lanternRing(ctx, { center: [src.x, 0, src.z], radius: 5, y: 0, seed: 's69ring' }); ctx.add(ring.group); ctx.shared.ring = ring;
        // the gold lantern light on the glass: a warm sheen over the lower-left panes (light-boost, so it tints the glass)
        const gq = boostDecal(ctx, 'spot', '#ffa040', 0.5, 1.2, 1.0, { mode: 'tint' }); gq.material.color.multiplyScalar(1.6); gq.position.copy(P3(WIN).add(new THREE.Vector3(-0.32, -0.3, 0.04))); ctx.add(gq);
        ctx.shared.fam = familyLanterns(ctx, H);
      } else {
        flashbackLight(ctx, H, 'sepia', { window: { n: 0 }, exposure: 1.15 });
        const dir = sill.clone().sub(src).normalize();
        const Bm = X.flashlightBeam(ctx, { origin: src, dir, length: src.distanceTo(sill) + 0.5, angle: 10, cd: 16, opacity: 0.5, motes: 8, ground: 0 }); ctx.add(Bm.group); ctx.shared.Bm = Bm;
        // the torch spot lying across the sill and the lower glass
        const sq = boostDecal(ctx, 'spot', '#fff2d8', 0.6, 1.0, 0.5, { mode: 'tint' }); sq.material.color.multiplyScalar(1.7); sq.position.copy(sill).add(new THREE.Vector3(0, 0.12, 0.05)); sq.rotation.z = 0.12; ctx.add(sq);
      }
      ctx.add(ctx.lights.point({ color: '#ffd9b0', intensity: 1.4, pos: up(WIN, -0.3, 0.4, -2.0), decay: 2 }));   // the room light on the sleeper
      ctx.shared.fx = sparks(ctx, P3(WIN).add(new THREE.Vector3(0.2, -0.5, 1.0)), [2.0, 1.4, 1.0], 7, 'p4decades' + (now ? 'n' : 'o'), { px: [40, 72] });
    },
    update(ctx, t) { const s = ctx.shared; if (s.ring) s.ring.update(t); if (s.L) s.L.intensity = 5.0 * K.lanternFlicker(t, 'p4s69'); if (s.Bm) s.Bm.update(t); if (s.fam) s.fam.update(t); s.fx.update(t); },
  },

  // s70 "That's why they face the house." (78.67-79.72) - the s09 framing again (part1 lawn_stare camera block: near slot
  // bedFront0, back 3.0, side -1.6, height 1.4, aim 3.0; pull 10 %): low behind our family gnomes staring at the house,
  // every lantern lit now, Theo's window lit with the small sleeping shape; in Grandpa's spot the hero stands holding him.
  lawn_stare_lit: {
    build(ctx) {
      const p = ctx.params; const c = { near_slot: 'bedFront0', back_studs: 3.0, side_studs: -1.6, height_studs: 1.4, look_ahead_studs: 0, look_side_studs: 0, aim_studs: 3.0, moon_az: -8, moon_el: 30, ...p.camera };
      const H = nightLot(ctx, { shiftBedFront0: false }); frontDoor(ctx); theoAsleep(ctx, H, { blanket: true }); const set = H; const id = 'A1';   // the s09 layout (bedFront0 unshifted)
      const sl = sets.slot(set, id + '.bed0'); const fwd = new THREE.Vector3(Math.sin(sl.yaw), 0, Math.cos(sl.yaw)); const side = new THREE.Vector3(-fwd.z, 0, fwd.x);
      const base = V3(sl.pos); const near = V3(sets.slot(set, id + '.' + c.near_slot).pos);
      const pos = near.clone().addScaledVector(fwd, -c.back_studs * S).addScaledVector(side, c.side_studs * S); pos.y = c.height_studs * S;
      const tgt = base.clone().addScaledVector(fwd, c.look_ahead_studs * S).addScaledVector(side, c.look_side_studs * S); tgt.y = c.aim_studs * S;
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: p.fov }); ctx.camera.pull(c.move.Z);
      const camYaw = Math.atan2(tgt.x - pos.x, -(tgt.z - pos.z)) / DEG;
      nightRig(ctx, H, 'nightHigh', { window: { n: 2, cd: 2.4, color: '#ffd9a0', maxD: 14 }, hemiIntensity: 1.05, moon: { az: camYaw + c.moon_az, el: c.moon_el, size: 9, style: 'tf' }, skyOpts: { intensity: 1.6 }, postOpts: { exposure: 1.1, grade: { temperature: -10, tint: 6 } } });
      // the hero in Grandpa's spot (beside the hole, a little right so the sleeping shape shows past his shoulder), back to us
      const HP = [base.x + 0.5 + 1.0 * S, BED[1], base.z - 0.08];   // review: 1 stud off the window axis so the lit window reads past him
      // Grandpa tucked under his left arm (the lens side), facing the house like every gnome, his lantern lit at the hip
      const hero = K.makeCharacter('heroBarefoot', { face: 'heartfelt' }); hero.position.set(...HP); hero.rotation.y = sl.yaw; K.setPose(hero, { armLx: 30, armLz: 4, armRx: 4, neckX: 12 }); ctx.add(hero);
      const g = K.makeGnome('grandpa', { units: 'stud', lantern: 1, wear: 0.12 }); C.softenBeard(g); hero.getObjectByName('hips').add(g); g.position.set(1.38, 0.62, 0.62); g.rotation.set(0.12, 0.25, -0.16); hero.updateWorldMatrix(true, true);
      ctx.add(sets.contactShadow(ctx, { pos: [HP[0], HP[1] + 0.005, HP[2]], radius: 0.42, opacity: 0.35 }));
      ctx.shared.GL = grandpaLantern(ctx, g, { cd: 2.0 }); ctx.shared.fam = familyLanterns(ctx, H); ctx.shared.g = g;
      warmKey(ctx, worldOf(hero.getObjectByName('head')).toArray(), { cd: 1.2, d: 0.9, color: '#ffb870', side: -40, el: 10 });   // his lantern lights him: no black silhouette
      ctx.shared.fx = sparks(ctx, pos.clone().lerp(base, 0.35).setY(0.7), [3.5, 1.4, 2.5], (p.fx && p.fx.sparkles && p.fx.sparkles.count) || 8, 's70');
      ctx.shared.famG = Object.values(H.ep01.gnomes.family || {});
    },
    update(ctx, t) { const s = ctx.shared; s.GL.update(t); s.fam.update(t); s.fx.update(t); s.famG.forEach((f, i) => K.gnomeIdle(f, t, { seed: 'fam' + i, amp: 0.4 })); lanternSwing(s.g, t + 6, { amp: 6, decay: 0.8 }); },
  },

  // s71 "I wasn't small anymore." (79.72-80.87) - from inside the room: the hero's face fills the window from outside,
  // big against the frame, lit gold from below by the lantern in his arms; Theo small and asleep at the bottom of frame.
  // h 2.2, d 4.0 (from the window), yaw 0, pitch 6, push 19 %. Bedroom grade.
  big_in_window: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); theoAsleep(ctx, H, { blanket: true }); const R = roomFrame(H); hideBoard(H);
      // the hero outside right at the glass, Grandpa tucked under his left arm (in front of him he would be inside the
      // wall): his head and shoulders fill the window opening, the lantern at his side lights his face gold from below
      const HP = [WIN[0] + 0.12, BED[1], WIN[2] + 0.7 * S];   // review: pressed to the glass
      const hero = K.makeCharacter('heroBarefoot', { face: p.cast[0].face || 'heartfelt' }); hero.position.set(...HP); hero.rotation.y = Math.PI; ctx.add(hero);
      K.setPose(hero, { armLx: 34, armLz: 4, armRx: 62, armRz: -8, neckX: -10, bodyX: 4 });
      const g = K.makeGnome('grandpa', { units: 'stud', lantern: 1, wear: 0.12 }); C.softenBeard(g); hero.getObjectByName('hips').add(g); g.position.set(1.38, 0.62, 0.62); g.rotation.set(0.12, 0.25, -0.16); hero.updateWorldMatrix(true, true);
      const face = worldOf(hero.getObjectByName('head')); ctx.shared.hero = hero; ctx.shared.g = g;
      // the lens from the back of the room over the mattress (TF 40.2 grammar: bed in the foreground, the figure in the
      // window): Theo small and asleep at the bottom, the window and the big boy filling it above. (The board's d 4.0
      // sits over Theo: from there he is either behind the lens or a giant foreground body.)
      const cp = R(-0.8, 4.6, -5.6); const tg = R(-0.6, 3.5, 0);   // review: nearer the glass, his face big in the pane (eyes ~y 0.35)
      ctx.camera.set({ pos: cp.toArray(), target: tg.toArray(), fov: p.fov }); basePush(ctx);
      const lan = worldOf(g.getObjectByName('lantern'));
      I.bedroomNight(ctx, { set: H, lamp: 3.0, nightlight: 2.2, moon: true, lanternOutside: { pos: lan.clone().add(new THREE.Vector3(0, 0.15, -0.25)).toArray(), cd: 1.8 } });
      ctx.shared.GL = grandpaLantern(ctx, g, { cd: 1.2, ring: 0, lightOffset: face.clone().sub(lan).multiplyScalar(0.4).add(new THREE.Vector3(0, 0, 0.15)).toArray() });
      ctx.add(ctx.lights.point({ color: '#ffc080', intensity: 0.8, pos: face.clone().add(new THREE.Vector3(0.15, -0.3, -0.45)).toArray(), decay: 2 }));
      ctx.shared.fx = sparks(ctx, cp.clone().lerp(face, 0.6), [1.6, 1.2, 1.4], 10, 's71', { px: [40, 72] });
    },
    update(ctx, t) { const s = ctx.shared; lanternSwing(s.g, t + 7, { amp: 6, decay: 0.8 }); s.GL.update(t); s.fx.update(t); },
  },

  // s72 "Theo was." (80.87-81.62) - high CU on Theo asleep, a band of gold lantern light falling across his cheek through
  // the glass. h 3.0, d 1.6, yaw 10, pitch -45, push 18 %. Bedroom grade.
  theo_lantern_cheek: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); const { theo } = theoAsleep(ctx, H, { blanket: true });
      const head = worldOf(theo.getObjectByName('head'));
      // d 2.4 (board 1.6): at 1.6 studs the sideways head overfills the frame and the band has nowhere to go
      boardCam(ctx, head.clone().setY(0), { ref: [0, 0, 1], yaw: c.yaw_deg, dist: c.dist_studs + 0.8, h: c.height_studs + 0.3, ground: ROOM_FLOOR, fov: p.fov, aimY: head.y - 0.02 }); basePush(ctx);
      // the room a notch darker than s71 (lamp 1.8, hemi 1.3, exposure 1.3): the warm band has to read against the face
      I.bedroomNight(ctx, { set: H, lamp: 1.8, nightlight: 1.4, hemiIntensity: 1.3, moon: true, lanternOutside: { cd: 1.2 }, postOpts: { exposure: 1.3, grade: { saturation: 0.92 } } });
      // the band of gold lantern light across his cheek: a narrow warm spot through the glass + a soft light-boost stripe
      // lying over the cheek and the pillow (facing the lens, diagonal), flickering with the lantern
      const src = new THREE.Vector3(WIN[0] + 0.35, 1.05, WIN[2] + 0.55); const sp = ctx.lights.spot({ color: '#ffb44a', intensity: 14, pos: src.toArray(), target: head.toArray(), angle: 4 * DEG, penumbra: 0.6, decay: 2 }); ctx.add(sp);
      const B = camBasis(ctx); const band = boostDecal(ctx, 'band', '#ff9a38', 0.62, 0.5, 0.085, { mode: 'tint' }); band.material.color.multiplyScalar(1.45);
      band.material.depthTest = false; band.renderOrder = 20;
      band.position.copy(head).add(new THREE.Vector3(0, 0.02, 0.1)).addScaledVector(B.fwd, -0.22).addScaledVector(B.up, -0.035); band.lookAt(B.pos); band.rotateZ(-28 * DEG); ctx.add(band);
      ctx.shared.fx = sparks(ctx, head.clone().lerp(B.pos, 0.4), [0.8, 0.5, 0.6], 9, 's72', { px: [40, 70] });
      Object.assign(ctx.shared, { sp, band, k0: 14 });
    },
    update(ctx, t) { const s = ctx.shared; const f = K.lanternFlicker(t, 'p4s72'); s.sp.intensity = s.k0 * f; s.band.material.opacity = 0.62 * (0.88 + 0.12 * f); s.fx.update(t); },
  },

  // s73 "I knelt in the flowerbed." (81.62-82.60) - MS from the lawn (kneelLow: h 2.2, d 7, yaw -30, pitch 4): he kneels in
  // the soil right of the hole the plastic gnome left ($4.99 sticker), Grandpa in both hands, the lit window above; the
  // kneel snaps in 10 frames on "knelt", then holds through the pause. Push 16 %.
  knelt_bed: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); frontDoor(ctx); theoAsleep(ctx, H, { blanket: true });
      const { hero, g, setHold } = kneelHold(ctx, { face: p.cast[0].face || 'heartfelt' }); ctx.shared.hero = hero; ctx.shared.g = g; ctx.shared.setHold = setHold;
      boardCam(ctx, [BED[0] + 0.25, 0, BED[2] + 0.2], { ref: [0, 0, 1], yaw: c.yaw_deg, dist: c.dist_studs, h: c.height_studs, pitch: c.pitch_deg, fov: p.fov, aimY: 1.02 }); basePush(ctx);
      nightRig(ctx, H, 'nightHigh', { lamp: { n: 2 }, window: { n: 1, cd: 2.4, maxD: 10 }, postOpts: CU_GRADE });
      ctx.shared.tK = evT(ctx, 'knelt', 1 / 60);
      const STAND = { ...HUG, neckX: -10 }; ctx.shared.STAND = STAND;
      ctx.shared.GL = grandpaLantern(ctx, g, { cd: 1.3, lightOffset: [0, 0.12, 0.0] }); ctx.shared.fam = familyLanterns(ctx, H);
      warmKey(ctx, up(KNEEL_AT, 3.0), { cd: 1.2, d: 1.0, color: '#ffc896' });
      ctx.shared.fx = sparks(ctx, up(KNEEL_AT, 2.4, -1.2, 2.0), [2.2, 1.4, 1.6], 7, 's73', { px: [40, 72] });
      ctx.shared.dust = sets.burst(ctx, { pos: up(KNEEL_AT, 0.15), t0: ctx.shared.tK + 9 / 60, dur: 0.3, count: 10, spread: 0.35, px: [8, 18], ring: false, core: false, colors: ['#8a5a3a', '#6a4028', '#a87048'], brightness: 1.0, gravity: -0.4, seed: 's73soil' }); ctx.add(ctx.shared.dust);
    },
    update(ctx, t) {
      const s = ctx.shared; const u = outQuad((t - s.tK) / (10 / 60)); const P = t < s.tK ? s.STAND : K.mixPose(s.STAND, KNEEL_HOLD, u);
      // standing: the hips frame is upright and the gnome sits higher; ease the gnome's offset with the pose
      s.setHold(P); s.g.position.set(0, lerp(HOLD_OFF[1], KNEEL_OFF[1], t < s.tK ? 0 : u), lerp(HOLD_OFF[2], KNEEL_OFF[2], t < s.tK ? 0 : u));
      s.hero.position.y = lerp(0, KNEEL_AT[1], t < s.tK ? 0 : u);
      lanternSwing(s.g, t - s.tK, { amp: 10, decay: 1.2 }); s.GL.update(t); s.fam.update(t); s.fx.update(t); s.dust.update(t);
    },
  },

  // s74 "I said goodnight," (82.60-83.40) - CU, eye level with the kneeling hero: he whispers goodnight to the gnome in his
  // hands, tender (heartfelt). h 3.4, d 2.0, yaw -10, pitch 0, push 20 %.
  hero_goodnight: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); theoAsleep(ctx, H, { blanket: true });
      const P74 = { ...KNEEL_HOLD, bodyX: 6, neckX: -17 }; ctx.shared.P74 = P74;
      const { hero, g, fwd } = kneelHold(ctx, { face: p.cast[0].face || 'heartfelt', pose: P74 }); ctx.shared.g = g; ctx.shared.hero = hero; ctx.shared.setHold = null;
      const head = worldOf(hero.getObjectByName('head')); C.gazeAt(g, head); K.setGnomeHead(g, 0, 16, 0);
      // eye level with the kneeling face (the board's h 3.4 is a standing-height number; kneeling, his eyes are lower)
      boardCam(ctx, head.clone().setY(0), { ref: fwd.toArray(), yaw: c.yaw_deg, dist: c.dist_studs, h: (head.y - BED[1]) / S + 0.15, ground: BED[1], pitch: c.pitch_deg - 10, fov: p.fov }); basePush(ctx); // review: eyes out of the caption band
      nightRig(ctx, H, 'nightHigh', { lamp: { n: 2 }, window: { n: 0 }, postOpts: CU_GRADE });
      coolRim(ctx, head.toArray(), { intensity: 1.0 });
      const B = camBasis(ctx); const lan = worldOf(g.getObjectByName('lantern'));
      ctx.shared.GL = grandpaLantern(ctx, g, { cd: 0.6, lightOffset: B.pos.clone().sub(lan).multiplyScalar(0.45).toArray() }); ctx.shared.fam = familyLanterns(ctx, H);
      warmKey(ctx, head.toArray(), { cd: 0.7, d: 0.9, color: '#ffc8a0' });
      ctx.shared.fx = sparks(ctx, head.clone().lerp(B.pos, 0.4).add(new THREE.Vector3(0, -0.12, 0)), [0.9, 0.7, 0.4], 7, 's74', { px: [40, 70] });
    },
    update(ctx, t) { const s = ctx.shared; K.setPose(s.hero, { ...s.P74, neckX: s.P74.neckX + 1.5 * Math.sin(2 * Math.PI * 0.4 * t) }); lanternSwing(s.g, t + 2, { amp: 6, decay: 0.8 }); K.gnomeIdle(s.g, t, { seed: 's74', amp: 0.2 }); s.GL.update(t); s.fam.update(t); s.fx.update(t); },
  },

  // s75 "and he blinked slowly, like he was sorry." (83.40-85.18) - close on the gnome in his hands, from the hero's chest
  // (gnome eye level): gaze up at the hero; on "blinked" the slow blink (4 frames closed, half-closed either side) with the
  // TIK glint; on "sorry" the lids settle to 0.3. Lantern under-light, cool rim, magic dust. h 2.5, d 1.3, push 28 %.
  slow_blink: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); theoAsleep(ctx, H, { blanket: true });
      const { hero, g, fwd } = kneelHold(ctx, { pose: { ...KNEEL_HOLD, neckX: -24 } }); ctx.shared.g = g;
      const head = worldOf(hero.getObjectByName('head')); K.setGnomeHead(g, 0, 14, 0); g.updateWorldMatrix(true, true);
      const eyes = C.eyesOf(g);
      // the lens between the hero's chest and the gnome: hide his torso, head and hood (the lens is inside them)
      for (const n of ['torso', 'head', 'neck']) { const o = hero.getObjectByName(n); if (o) o.visible = false; }
      hero.traverse((o) => { if (/hood/i.test(o.name)) o.visible = false; });
      boardCam(ctx, eyes.clone().setY(0), { ref: fwd.clone().negate().toArray(), yaw: c.yaw_deg, dist: c.dist_studs, h: c.height_studs, ground: BED[1], fov: p.fov, aimY: eyes.y - 0.015 }); basePush(ctx);
      // gaze at the hero = just above the lens (his face is right above it): at his real head the irises roll up under the lids
      { const B0 = camBasis(ctx); C.gazeAt(g, B0.pos.clone().add(new THREE.Vector3(0, 0.02, 0))); } void head;
      nightRig(ctx, H, 'nightHigh', { lamp: { n: 2 }, window: { n: 0 }, postOpts: CU_GRADE });
      coolRim(ctx, eyes.toArray(), { intensity: 1.0 });
      const lan = worldOf(g.getObjectByName('lantern'));
      ctx.shared.GL = grandpaLantern(ctx, g, { cd: 0.9, lightOffset: eyes.clone().sub(lan).multiplyScalar(0.2).add(new THREE.Vector3(0, -0.04, 0)).toArray() }); ctx.shared.fam = familyLanterns(ctx, H);
      warmKey(ctx, eyes.toArray(), { cd: 0.5, d: 0.6, color: '#ffc8a0' });
      const tb = evT(ctx, 'blinked', 0.283), ts = evT(ctx, 'sorry', 1.333); Object.assign(ctx.shared, { tb, ts });
      const T = X.blinkTik(ctx, g, { t0: tb, frames: 4, slow: true }); ctx.add(T.group); ctx.shared.T = T;
      ctx.shared.md = sets.magicDust(ctx, { center: lan.toArray(), radius: 0.2, height: 0.5, count: 12, rise: 0.3, px: [10, 22], seed: 's75dust' }); ctx.add(ctx.shared.md);
      const B = camBasis(ctx); ctx.shared.fx = sparks(ctx, eyes.clone().lerp(B.pos, 0.35), [0.6, 0.45, 0.3], 7, 's75', { px: [40, 72] });
    },
    update(ctx, t) {
      const s = ctx.shared; const b = K.gnomeBlink(t, [s.tb], { frames: 4, slow: true }); const settle = t < s.ts ? 0 : 0.22 * smooth((t - s.ts) / 0.22);   // board 0.3: on these lid shells 0.3 already hides the irises
      K.setGnomeLids(s.g, Math.max(b, settle)); s.T.update(t);
      lanternSwing(s.g, t + 2.8, { amp: 5, decay: 0.8 }); K.gnomeIdle(s.g, t, { seed: 's75', amp: 0.2 }); s.GL.update(t); s.fam.update(t); s.md.update(t); s.fx.update(t);
    },
  },

  // s76 "I set him down and I let go." (85.18-86.77) - insert on his hands, slightly high: they lower Grandpa into his ring
  // of soil beside the hole (touching on "him", 85.50), facing the window; on "go" (86.29) the hands open and lift away in
  // 8 frames: empty hands in lantern light. h 2.0, d 2.2, yaw -20, pitch -30, fov 55, push 20 %.
  set_down_let_go: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); theoAsleep(ctx, H, { blanket: true });
      const tT = evT(ctx, 'him', 0.317), tG = evT(ctx, 'go', 1.1); Object.assign(ctx.shared, { tT, tG });
      // he has turned to the house to set Grandpa down in front of him, on the right edge of the hole, facing the window
      const hero = K.makeCharacter('heroBarefoot', { face: 'heartfelt' }); hero.position.set(BED[0] + 0.38, BED[1], BED[2] + 0.85); hero.rotation.y = Math.PI; ctx.add(hero); ctx.shared.hero = hero;
      const g = K.makeGnome('grandpa', { lantern: 1, wear: 0.12 }); C.softenBeard(g); g.rotation.y = H.ep01.spots.bed0Yaw ?? Math.PI; ctx.add(g); ctx.shared.g = g;
      // poses: holding him up (start) -> placing (touch, on "him") -> hands open and lift away (8 frames on "go"). The
      // placing pose is solved so the hands' midpoint sits at his belly (0.85 stud) over the soil, and the hero slides so
      // that point is the landing spot.
      const GRIP = 0.85 * S; const D = new THREE.Vector3(BED[0] + 0.38, BED[1], BED[2] + 0.3);   // front-right edge of the hole (the sticker between them)
      const PL = { ...K.POSES.kneelPlace, armLz: -24, armRz: -24, neckX: -24 };   // hands on his sides
      const mid = solveArm(hero, PL, 'armLx', D.y + GRIP, { lo: 20, hi: 140, both: 'armRx' });
      hero.position.x += D.x - mid.x; hero.position.z += D.z - mid.z; hero.updateMatrixWorld(true);
      const P0 = { ...PL, bodyX: 30, armLx: PL.armLx - 18, armRx: PL.armRx - 18, neckX: -20 };
      const P2 = { ...PL, armLx: PL.armLx - 16, armRx: PL.armRx - 16, armLz: 8, armRz: 8, bodyX: 40, neckX: -20 };   // open and lift a little: the empty hands stay in frame
      Object.assign(ctx.shared, { PL, P0, P2, D, GRIP });
      ctx.add(sets.contactShadow(ctx, { pos: [hero.position.x, BED[1] + 0.005, hero.position.z], radius: 0.5, opacity: 0.35 }));
      const gs = sets.contactShadow(ctx, { pos: [D.x, BED[1] + 0.006, D.z], radius: 0.24, opacity: 0.45 }); ctx.add(gs); ctx.shared.gs = gs;
      // the lens on the window side, slightly high, 20 deg off the gnome's front on the hole's side (the tulips on the
      // other side hide his hands): his face as he settles back in, the hands on his sides, the hole and the $4.99 sticker,
      // the hero kneeling behind. In front of the sill, at the pane's height (1.05 m: Theo's window looking down), 2.0
      // studs out, so it looks down about 45 deg instead of 30; fov 62 (board 55) keeps both hands in the 9:16 width.
      boardCam(ctx, D, { ref: [0, 0, -1], yaw: Math.abs(c.yaw_deg), dist: 2.0, h: (1.05 - BED[1]) / S, ground: BED[1], fov: p.fov + 7, aimY: D.y + 0.28 }); basePush(ctx);
      nightRig(ctx, H, 'nightHigh', { lamp: { n: 2 }, window: { n: 1, cd: 1.6, maxD: 10 }, postOpts: CU_GRADE });
      ctx.shared.GL = grandpaLantern(ctx, g, { cd: 1.0 }); ctx.shared.fam = familyLanterns(ctx, H);
      // Theo's window spill from above-behind the lens (the gnome faces it) + a soft warm key on the hero's face
      ctx.add(ctx.lights.point({ color: '#ffd9a0', intensity: 1.6, pos: [D.x - 0.1, 1.5, WIN[2] + 0.25], decay: 2 }));
      warmKey(ctx, worldOf(hero.getObjectByName('head')).toArray(), { cd: 0.8, d: 0.8, color: '#ffc896' });
      ctx.shared.soil = sets.burst(ctx, { pos: [D.x, D.y + 0.03, D.z], t0: tT, dur: 0.28, count: 9, spread: 0.25, px: [8, 16], ring: false, core: false, colors: ['#8a5a3a', '#6a4028', '#a87048'], brightness: 1.0, gravity: -0.4, seed: 's76soil' }); ctx.add(ctx.shared.soil);
      ctx.shared.fx = sparks(ctx, up(D, 1.4, 0, 0.9), [1.0, 0.8, 0.8], 7, 's76', { px: [40, 70] });
    },
    update(ctx, t) {
      const s = ctx.shared; const hero = s.hero;
      let P; if (t < s.tT) P = K.mixPose(s.P0, s.PL, inOutSine(t / s.tT)); else if (t < s.tG) P = s.PL; else P = K.mixPose(s.PL, s.P2, outQuad((t - s.tG) / (8 / 60)));
      K.setPose(hero, P); hero.updateMatrixWorld(true);
      if (t < s.tT) { const m = worldOf(K.handSocket(hero, 'L')).add(worldOf(K.handSocket(hero, 'R'))).multiplyScalar(0.5); s.g.position.set(m.x, Math.max(s.D.y, m.y - s.GRIP), m.z); }
      else s.g.position.copy(s.D);
      s.gs.visible = t >= s.tT - 0.05; s.g.updateMatrixWorld(true);
      K.gnomeIdle(s.g, t, { seed: 's76', amp: 0.2 }); lanternSwing(s.g, t - s.tT, { amp: t < s.tT ? 0 : 7, decay: 1.6 });
      s.GL.update(t); s.fam.update(t); s.soil.update(t); s.fx.update(t);
    },
  },
};

// s66 / s67 mirror pair: the identical set-up inside the room, one era each.
function mirrorPair(ctx, { era, kid, gp, grade }) {
  const p = ctx.params, c = p.camera; const H = SE.heroLot(ctx, { tod: 'night', era, keepOff: false }); ctx.add(H); const R = roomFrame(H);
  // the lens: the sets owner's room_toWindow set-up (4.8 studs up, 10.8 back, from the bed's foot side): at the board's
  // h 3 / d 6 the lens sits over the bed and the sleeper's body fills the frame and hides the window
  const cp = R(0.8, 4.9, -10.8); const tg = R(-0.9, 3.8, 0);
  ctx.camera.set({ pos: cp.toArray(), target: tg.toArray(), fov: p.fov }); basePush(ctx);
  const av = sleeper(ctx, H, kid, { sc: 0.75, lie: 'up', toward: cp, tilt: 28, lift: -0.32, pose: { armLz: 8, armRz: 8, armLx: 4, armRx: 4 } });   // tucked in: the duvet covers the body, the head on the pillow
  const { gp: g, fl } = grandpaAtGlass(ctx, gp, { face: (p.cast[1] && p.cast[1].face) || 'heartfelt' });
  I.bedroomNight(ctx, { set: H, lamp: 3.2, nightlight: 0, moon: true, lanternOutside: false });
  ctx.post.set(sets.postPreset(grade, { exposure: 1.3 })); if (grade === 'sepia') ctx.post.set({ grade: { saturation: 0.32, temperature: 48 } });   // review: the lilac room read as the present (hue 254)
  const face = worldOf(g.getObjectByName('head'));
  ctx.add(ctx.lights.point({ color: '#ffe6c8', intensity: 1.4, pos: face.clone().add(new THREE.Vector3(0.15, 0.2, -0.75)).toArray(), decay: 2 }));   // the room light on his face at the glass
  const Bm = X.flashlightBeam(ctx, { torch: fl, t0: -1, length: 5, angle: 16, cd: 3, opacity: 0.18, motes: 5 }); ctx.add(Bm.group);
  ctx.shared.mp = { Bm, fl, av, g };
  ctx.shared.fx = sparks(ctx, cp.clone().lerp(face, 0.45), [1.6, 1.2, 1.4], 10, 'p4mirror' + era, { px: [40, 72] });
}
function mirrorPairUpdate(ctx, t) { const s = ctx.shared; CR.setFlashlight(s.mp.fl, 1); s.mp.Bm.update(t); s.fx.update(t); }
