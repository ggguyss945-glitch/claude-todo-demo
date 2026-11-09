// EP01 full episode, PART 5 (s77-s97, 86.77-113.30 s): FWOOM to the end: the flare, the light rolling, the mounds sinking,
// the eyes winking out, the quiet wide, dawn with Theo, the truck leaving, the photos, the narrator at 71, the loop shot.
// Shot list and every decision (camera numbers, cast and faces, light/grade, events with frames, SFX, assets) are in
// episodes/ep01/timeline.json (params of each shot) and episodes/ep01/board.md; new assets are specified in episodes/ep01/ASSETS.md.
// Builders are pure functions of shot time t (engine/README.md determinism rules): no state between frames, no
// Math.random / Date; seeded RNGs only (ctx.rng / makeRng(hash32(...))); render-to-texture photos are cached per worker.
//
// Sets: our front garden is sets_ep01.heroLot (lot A1: gate (0, -6.4); door (0, 0.32, -13.22); porch deck x -1.76..1.76,
// z -13.31..-11.39 at 0.32 m; steps to z -11.02; Grandpa's bed0 slot (-2.67, 0.112, -12.67) under Theo's window, window
// glass centre (-2.41, 1.63, -13.31)); the epilogue is sets_ep01.backGarden (bench, garden table, striped deck chair,
// the granddaughter's lit window).
// Continuity kept here (board.md section 5, part4 s73-s76):
//   night (s77-s81)  Grandpa stands where s76 set him down: on the right edge of the hole (bed0 + (0.38, 0, 0.3) m), facing
//                    the window; the hole with the $4.99 sticker beside him; his lantern lit (FWOOM curve in s77-s80, level 1
//                    steady in s81); the family lanterns lit (2-stud pools); SOLD board, gate open, truck at the kerb with
//                    its back open, the front door open (warm hall light), Theo asleep in his lit room (blanket, whale);
//                    the hero (heroBarefoot) kneeling right behind Grandpa in s77, sitting back on his heels in s81.
//   dawn (s82-s89)   lanterns 0.5, windows off, the hero muddy (heroMuddy) sitting on the lawn by the bed, Theo in striped
//                    socks with the whale; s88/s89 from the leaving truck.
//   epilogue         the back garden at dusk (s90-s96), night for the loop shot (s97); the narrator at 71 = heroOld.
// Staging (metres, world), shared by the shots that cut together:
//   GP      Grandpa (s76's set-down spot), facing the window (rotation.y = PI)
//   SIT     the hero at dawn, sitting on the lawn in front of the bricks, right of Grandpa
//   T_ASK   Theo on the lawn in front of the porch's left corner (s83-s85 start), facing Grandpa; T_STEP after the nudge
import * as THREE from 'three';
import * as sets from '../../kit/sets.js';
import * as K from '../../kit/chars.js';
import * as CR from '../../kit/creatures.js';
import * as SE from '../../kit/sets_ep01.js';
import * as X from '../../kit/fx_ep01.js';
import { doorTex } from '../../kit/kitlib.js';
import { makeRng, hash32 } from '../../core/random.js';
import * as C from './common.js';

const S = C.S, DEG = C.DEG, clamp01 = C.clamp01, smooth = C.smooth, outQuad = C.outQuad, outExpo = C.outExpo;
const lerp = (a, b, k) => a + (b - a) * k;
const YAX = new THREE.Vector3(0, 1, 0);
const P3 = (p) => (p && p.isVector3 ? p.clone() : new THREE.Vector3(p[0], p[1] ?? 0, p[2]));
const up = (p, dy = 0, dx = 0, dz = 0) => { const v = P3(p); return [v.x + dx * S, v.y + dy * S, v.z + dz * S]; };
const inOutSine = (x) => 0.5 - 0.5 * Math.cos(Math.PI * clamp01(x));
const outCubic = (x) => 1 - Math.pow(1 - clamp01(x), 3);
const dirOf = (a) => new THREE.Vector3(Math.sin(a), 0, Math.cos(a));   // rotation.y -> horizontal facing (+z of the object)
const yawTo = (from, to) => Math.atan2(to[0] - from[0], to[2] - from[2]);
const worldOf = (o) => { o.updateWorldMatrix(true, false); return o.getWorldPosition(new THREE.Vector3()); };

// ------------------------------------------------------------------ staging
const BED = [-2.669, 0.112, -12.672];
const WIN = [-2.413, 1.632, -13.312];
const LOT_DOOR = [0, 0.32, -13.216];
const GP = [BED[0] + 0.38, BED[1], BED[2] + 0.3];
const GP_YAW = Math.PI;
const SIT = [-1.86, 0, -11.52];
const T_ASK = [-0.98, 0, -10.62];
const T_STEP = [-1.16, 0, -10.86];
const CU_GRADE = { grade: { temperature: -6, tint: 6 } };   // night close-ups keep warm skin / glaze (approved s05, part4)
const FWOOM_T0 = 86.86, FLARED_T = 87.92;                   // episode seconds (s77 events): the curve carries on in s78-s81
const DEW = ['#ffe2c4', '#fff4e0'];

// ------------------------------------------------------------------ helpers (the part2-part4 conventions)
const evT = (ctx, k, fb) => C.evT(ctx, k, fb);
const epT = (ctx, sec) => (Math.round(sec * ctx.fps) - ctx.shot.f0) / ctx.fps;        // episode seconds -> shot seconds (frame-snapped)
function basePush(ctx, o = {}) { const m = ctx.params.camera.move; ctx.camera.push(o.Z ?? m.Z ?? m.base_push ?? 0.19, { mode: (o.mode ?? m.mode) === 'dolly' ? 'dolly' : 'zoom', t0: o.t0, t1: o.t1 }); }
function paramRoll(ctx) { const r = ctx.params.camera.roll; if (r) ctx.camera.rollBy(r.deg[1] - r.deg[0]); }
function sparks(ctx, center, size, count, seed, o = {}) { const f = sets.sparkles(ctx, { ...C.SPARK, center: P3(center).toArray(), size, count, seed, ...o }); ctx.add(f); return f; }
function dew(ctx, center, size, count, seed) { return sparks(ctx, center, size, count, seed, { colors: DEW, px: [30, 50], drift: [0.01, 0.03], brightness: 1.5, underlay: 0 }); }
function nightLot(ctx, o = {}) { const H = SE.heroLot(ctx, { tod: 'night', bed: 'hole', truck: 'open', gate: 1.5, sold: -1, lanterns: 1, ...o }); ctx.add(H); return H; }
function dawnLot(ctx, o = {}) { const H = SE.heroLot(ctx, { tod: 'dawn', bed: 'hole', truck: 'open', truckOpts: { dome: false }, gate: 1.5, sold: -1, lanterns: 0.5, ...o }); ctx.add(H); return H; }
function nightRig(ctx, set, preset = 'nightHigh', o = {}) {
  const f = preset === 'night' ? sets.nightStreet : sets.nightLawn; const { low, ...rest } = o;
  return f(ctx, { set, skyPreset: low === false ? C.GALAXY : C.GALAXY_LOW, skyOpts: { intensity: 1.6 }, ...rest });
}
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
// Board camera: subject (world m), yaw (deg about +Y from `ref`, the horizontal direction subject -> camera at yaw 0),
// dist / height in studs (height from `ground`), pitch in degrees (+ looks up); aimY (m) overrides the pitch.
function boardCam(ctx, subj, { ref = [0, 0, 1], yaw = 0, dist, h, pitch = 0, ground = 0, fov, aimY = null }) {
  const r0 = P3(ref); const d = new THREE.Vector3(r0.x, 0, r0.z).normalize().applyAxisAngle(YAX, yaw * DEG); const s = P3(subj);
  const pos = s.clone().addScaledVector(d, dist * S); pos.y = ground + h * S;
  const hd = Math.hypot(s.x - pos.x, s.z - pos.z); const tgt = s.clone(); tgt.y = aimY ?? pos.y + hd * Math.tan(pitch * DEG);
  ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov }); return { pos, tgt };
}
// The front door (part2/part4): a hinged leaf in front of the set's door and a warm glow plane in the doorway.
// open: number (rad, 0 closed .. 1.75 open) or fn(t). glow: hall light multiplier.
function frontDoor(ctx, { door = LOT_DOOR, light = 3.2, open = 1.75, glow = 1.35 } = {}) {
  const W = 1.27, Hh = 2.39, z = door[2] - 0.045; const g = new THREE.Group(); g.name = 'p5FrontDoor';
  const glowMat = new THREE.MeshBasicMaterial({ color: new THREE.Color('#ffc890').multiplyScalar(glow), fog: false });
  const gl = new THREE.Mesh(new THREE.PlaneGeometry(W, Hh), glowMat); gl.position.set(door[0], door[1] + Hh / 2, z + 0.01); gl.renderOrder = 2; g.add(gl);
  const leafMat = ctx.cache('p2:doorLeafMat', () => new THREE.MeshStandardMaterial({ map: doorTex('#7a2a20'), roughness: 0.5 }));
  const edgeMat = ctx.cache('p2:doorEdgeMat', () => new THREE.MeshStandardMaterial({ color: '#5a1a14', roughness: 0.6 }));
  const hinge = new THREE.Group(); hinge.position.set(door[0] - W / 2, door[1], z + 0.03); g.add(hinge);
  const leaf = new THREE.Mesh(new THREE.BoxGeometry(W, Hh, 0.05), [edgeMat, edgeMat, edgeMat, edgeMat, leafMat, leafMat]); leaf.position.set(W / 2, Hh / 2, 0); hinge.add(leaf);
  let pl = null; if (light) pl = ctx.add(ctx.lights.point({ color: '#ffc890', intensity: light, pos: [door[0], door[1] + 1.7, door[2] + 0.55], decay: 2 }));
  const set = (t) => { const a = typeof open === 'function' ? open(t) : open; hinge.rotation.y = -a; gl.visible = a > 0.02; if (pl) pl.intensity = light * clamp01(a / 0.6); };
  set(0); ctx.add(g); return { group: g, update: set };
}
// The lantern on its ring (pendulum, decaying), u = seconds since the swing started (part2/part4).
function lanternSwing(g, u, { amp = 12, freq = 1.4, decay = 1.0, phase = Math.PI / 2 } = {}) {
  const L = g.getObjectByName('lantern'); if (!L) return; const a = amp * DEG * Math.exp(-decay * Math.max(0, u)) * Math.sin(2 * Math.PI * freq * u + phase);
  L.rotation.z = a; L.rotation.x = 0.3 * a;
}
// Grandpa where s76 set him down (beside the hole, facing the window).
function grandpaAt(ctx, { lantern = 1, extra = {}, shadow = true } = {}) {
  const g = K.makeGnome('grandpa', { lantern, wear: 0.12, ...extra }); C.softenBeard(g); g.position.set(...GP); g.rotation.y = GP_YAW; ctx.add(g);
  if (shadow) ctx.add(sets.contactShadow(ctx, { pos: [GP[0], GP[1] + 0.006, GP[2]], radius: 0.24, opacity: 0.45 }));
  g.updateWorldMatrix(true, true); return g;
}
// Grandpa's lantern, lit since s38 (level 1, flicker) with the 5-stud ring; levelFn for the FWOOM tail.
function grandpaLantern(ctx, g, o = {}) { const L = X.lanternLight(ctx, g, { t0: -1, ring: 5, burst: false, cd: 1.6, ...o }); ctx.add(L.group); return L; }
// The family gnomes' lanterns on our lawn (lit in the s40 cascade): 2-stud pools, no point lights (part4).
function familyLanterns(ctx, H, { skip = [], level = 1 } = {}) {
  const fam = H.ep01.gnomes.family || {}; const out = [];
  for (const [slot, g] of Object.entries(fam)) { if (skip.includes(slot) || !g.getObjectByName('lantern')) continue; const L = X.lanternLight(ctx, g, { t0: -1, level, ring: 2, ringOpts: { boost: 1.5, rimBoost: 2.6, rimA: 0.5 }, burst: false, light: false, haloPx: 48, seed: 'p3fam' + slot }); ctx.add(L.group); out.push(L); }
  return { update: (t) => { for (const L of out) L.update(t); } };
}
// part3/part4's Theo asleep on the bare mattress, on his side facing the window, curled round the whale, blanket up.
const SLEEP_POSE = { armLx: 78, armRx: 70, armLz: -16, armRz: -10, legLx: 42, legRx: 26, neckX: -6 };
const MATTRESS_TOP = 0.66;
function theoAsleep(ctx, H) {
  const A = H.ep01.room.sleeper; const theo = K.makeCharacter('theo', { face: 'sleeping' }); const sc = 0.85;
  const wh = CR.stuffedWhale(); CR.holdWhale(theo, wh, 'asleep'); K.setPose(theo, SLEEP_POSE);
  const yAx = P3(A.head).sub(P3(A.body)).setY(0).normalize(); const zAx = new THREE.Vector3(0, 0, 1); const xAx = new THREE.Vector3().crossVectors(yAx, zAx).normalize();
  theo.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(xAx, yAx, zAx));
  theo.position.copy(P3(A.head)).addScaledVector(yAx, -4.6 * S * sc); theo.position.y = MATTRESS_TOP + 1.0 * S * sc; theo.position.z -= 0.05;
  const bl = new THREE.Mesh(ctx.cache('ep01p5:blanketGeo', () => { const g = new THREE.BoxGeometry(2.7, 3.0, 1.9); g.userData.persistent = true; return g; }), new THREE.MeshStandardMaterial({ color: '#4f7ac8', roughness: 0.9 })); bl.position.set(-0.05, 1.1, 0.05); theo.add(bl);
  ctx.add(theo); theo.updateWorldMatrix(true, true); return theo;
}
// The hero kneeling behind Grandpa after letting go (s76's last pose: hands lifted away).
const LET_GO = { ...K.POSES.kneelPlace, bodyX: 26, armLx: 34, armRx: 34, armLz: 16, armRz: 16, neckX: -14 };
// FWOOM lantern curve in episode time (s77's events), for the shots after it.
const fwoomLevelEp = (ctx, t, o = {}) => X.fwoomLevel(t, epT(ctx, FWOOM_T0), { base: 1, peak: 6, end: 1.5, t2: epT(ctx, FLARED_T), peak2: 3, ...o });
// Theo with the whale under his arm (dawn).
function theoWithWhale(name = 'theo', o = {}) { const th = K.makeCharacter(name, o); const wh = CR.stuffedWhale(); CR.holdWhale(th, wh, 'underArm'); return th; }
// Remove the flowerbed's tulips / stems / daisies (merged per colour in the set) within horizontal circles [[x, z, r], ...]
// (world m) round a low lens, so a camera in the bed sees past them. Geometry is copied (the set template is shared).
function clearPlants(root, circles, { names = /^(tulip:|stem)/ } = {}) {
  root.updateMatrixWorld(true); const v = new THREE.Vector3();
  root.traverse((m) => {
    if (!m.isMesh || !names.test(m.name)) return; const g0 = m.geometry; const g = g0.index ? g0.toNonIndexed() : g0; const pa = g.attributes.position; const n = pa.count / 3; const keep = [];
    for (let i = 0; i < n; i++) { let cx = 0, cz = 0; for (let k = 0; k < 3; k++) { v.fromBufferAttribute(pa, i * 3 + k).applyMatrix4(m.matrixWorld); cx += v.x / 3; cz += v.z / 3; } if (!circles.some(([x, z, r]) => Math.hypot(cx - x, cz - z) < r)) keep.push(i); }
    if (keep.length === n) { if (g !== g0) g.dispose(); return; }
    const ng = new THREE.BufferGeometry();
    for (const [name, at] of Object.entries(g.attributes)) { const sz = at.itemSize, src = at.array; const arr = new src.constructor(keep.length * 3 * sz); keep.forEach((tri, j) => arr.set(src.subarray(tri * 3 * sz, tri * 3 * sz + 3 * sz), j * 3 * sz)); ng.setAttribute(name, new THREE.BufferAttribute(arr, sz, at.normalized)); }
    if (g !== g0) g.dispose(); m.geometry = ng;
  });
}
// The agent board by the path: its back face shows the text mirrored (props.js); hidden in shots that see it from the house side (as part4).
function hideBoard(H) { const b = H.ep01.board; if (b) b.visible = false; }
// Lerp the hemisphere of a rig between two looks.
function hemiTo(rig, a, b, k) { if (!rig || !rig.hemi) return; rig.hemi.color.set(a[0]).lerp(new THREE.Color(b[0]), k); rig.hemi.groundColor.set(a[1]).lerp(new THREE.Color(b[1]), k); rig.hemi.intensity = lerp(a[2], b[2], k); }

// ==================================================================================================================
export const PART = 5;
export const builders = {
  // s77 "FWOOM. His lantern flared," (86.77-88.58) - low on the gnome in his bed, from the window side (the lawn and the
  // street behind him): on FWOOM (86.86, f5212) the lantern flares white-gold (fx_ep01.fwoom: glass x2.4 -> x14, light
  // 1.6 -> 9 -> 2.4 cd, burst ring + streaks + gold/pink motes, grade nightHigh -> magic in 8 frames, the light wave rolls
  // out across the lawn) with a +-10 px shake for 0.4 s; on "flared" (87.92) the second, smaller pulse. The hero kneels
  // behind him, hands just lifted away (s76), lit gold. h 0.6, d 2.2, yaw -15 (lantern side), pitch 14, push 24 %.
  fwoom_flare: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); frontDoor(ctx); theoAsleep(ctx, H);
      const g = grandpaAt(ctx, { lantern: 1 }); ctx.shared.g = g;
      const hero = K.makeCharacter('heroBarefoot', { face: 'wonder' }); hero.position.set(GP[0] + 0.42, BED[1], GP[2] + 0.95); hero.rotation.y = Math.PI - 0.35; K.setPose(hero, { ...LET_GO, bodyX: 12, neckX: 4 }); ctx.add(hero);
      ctx.add(sets.contactShadow(ctx, { pos: [hero.position.x, BED[1] + 0.005, hero.position.z], radius: 0.5, opacity: 0.35 }));
      const eyes = C.eyesOf(g); const fwd = dirOf(GP_YAW); const lan = worldOf(g.getObjectByName('lantern'));
      const gl = new THREE.Vector3(-fwd.z, 0, fwd.x); const lanSide = Math.sign(lan.clone().sub(eyes).dot(gl)) || 1;
      const nose = eyes.clone().addScaledVector(fwd, 0.05 * S); nose.y -= 0.12 * S;
      const dir = fwd.clone().applyAxisAngle(YAX, -lanSide * c.yaw_deg * DEG);
      const pos = nose.clone().addScaledVector(dir, c.dist_studs * S); pos.y = c.height_studs * S;
      const tgt = eyes.clone().lerp(lan, 0.3); const hd = Math.hypot(tgt.x - pos.x, tgt.z - pos.z); tgt.y = pos.y + hd * Math.tan(c.pitch_deg * DEG);
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: p.fov }); basePush(ctx);
      clearPlants(H, [[pos.x, pos.z, 0.3], [lerp(pos.x, nose.x, 0.5), lerp(pos.z, nose.z, 0.5), 0.22]]);
      const rig = nightRig(ctx, H, 'nightHigh', { lamp: { n: 2 }, window: { n: 1, cd: 1.6, maxD: 10 }, postOpts: CU_GRADE });
      coolRim(ctx, eyes.toArray(), { intensity: 0.9 });
      warmKey(ctx, nose.toArray(), { cd: 0.9, d: 0.7, color: '#ffc8a0' });   // Theo's window spill from above-behind the lens
      const tF = evT(ctx, 0, 0.1), tFl = evT(ctx, 'flared', 1.15); Object.assign(ctx.shared, { tF, tFl });
      const F = X.fwoom(ctx, { gnome: g, t0: tF, t2: tFl, rig, cd: [1.6, 9, 2.4], wave: { sparkles: 40, height: 1.2 }, seed: 's77' }); ctx.add(F.group); ctx.shared.F = F;
      ctx.camera.shake({ t0: tF, dur: 0.4, rot: 0.35, pos: 0.004, px: 10, freq: 14, seed: 77 });
      ctx.shared.fam = familyLanterns(ctx, H);
      const B = camBasis(ctx); ctx.shared.fx = sparks(ctx, eyes.clone().lerp(B.pos, 0.4).add(new THREE.Vector3(0, 0.1, 0)), [0.9, 0.7, 0.5], 8, 's77', { px: [44, 80] });
    },
    update(ctx, t) { const s = ctx.shared; K.gnomeIdle(s.g, t, { seed: 's77', amp: 0.3 }); lanternSwing(s.g, t - s.tF, { amp: 6, decay: 1.4 }); s.F.update(t); s.fam.update(t); s.fx.update(t); },
  },

  // s78 "light rolled across the lawn," (88.58-89.75) - ground level across the lawn, looking at the house: the FWOOM wall
  // of gold light (from Grandpa's bed, 8 studs/s, 1.2 studs high here) sweeps left -> right, lighting the blades, sparkles
  // kicked up at its front, and crosses the frame centre on "across" (89.13, f5348) while the camera trucks with it
  // (11 studs over the shot, ~9 studs/s) + push 12 % (fov). The camera line is at 46 deg to the wave's radius, so the front
  // runs along it at ~11.5 studs/s: a little faster than the truck. Two mounds in the midground sink as it reaches them.
  light_rolls: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); frontDoor(ctx); theoAsleep(ctx, H);
      const g = grandpaAt(ctx, { lantern: 1 }); ctx.shared.g = g;
      const lan = worldOf(g.getObjectByName('lantern')); const Cn = new THREE.Vector3(lan.x, 0, lan.z);
      const v = 8 * S; const tW0 = epT(ctx, FWOOM_T0) + 0.05; const R = (t) => (t - tW0) * v;
      const tA = evT(ctx, 'across', 0.55); const dur = ctx.shot.duration; const truck = (c.drift && c.drift.truck_studs ? c.drift.truck_studs : 11) * S; const vc = truck / dur;
      const ZC = -7.32, Zw = ZC - 3 * S;        // camera line, and the line 3 studs in front of it where the wall crosses the centre
      const xw = (t) => Cn.x + Math.sqrt(Math.max(0, R(t) * R(t) - (Zw - Cn.z) * (Zw - Cn.z)));
      const x0 = xw(tA) - vc * tA; const camY = c.height_studs * S;
      const pos = [x0, camY, ZC]; const tgt = [x0, camY + 6 * S * Math.tan(c.pitch_deg * DEG), ZC - 6 * S];
      ctx.camera.set({ pos, target: tgt, fov: p.fov }).truck(truck); basePush(ctx);
      ctx.shared.rig = sets.magicGlow(ctx, { set: H, skyPreset: C.GALAXY_LOW, skyOpts: { intensity: 1.6 }, hemiIntensity: 0.62, key: { intensity: 0.45 }, lamp: { n: 0 }, postOpts: { exposure: 0.95, glow: { amount: 0.08 } } });
      ctx.shared.GL = grandpaLantern(ctx, g, { cd: 1.6, levelFn: (t) => fwoomLevelEp(ctx, t) });
      const W = X.lightWave(ctx, { center: Cn, t0: tW0, speed: 8, height: 1.6, width: 1.6, intensity: 1.7, sparkles: 80, sector: [0, 120], light: 4.0, seed: 's78w' }); ctx.add(W.group); ctx.shared.W = W;
      // two mounds in the midground (outside the lantern ring) that deflate as the front passes them
      const f = CR.moleField(ctx, { center: [x0 + 1.6, -9.7], size: [26, 14], res: 72, seed: 's78f', heads: 'snout' }); ctx.add(f.group);
      for (const [mx, mz, sc] of [[x0 + 0.5, -9.35, 0.9], [x0 + 2.4, -10.25, 1.0]]) { const k = f.add({ at: [mx, mz], scale: sc, face: [Cn.x, Cn.z] }); f.eyes(k, -5, null); const d = Math.hypot(mx - Cn.x, mz - Cn.z); f.sink(k, tW0 + d / v, 0.5); }
      ctx.shared.f = f; ctx.shared.fam = familyLanterns(ctx, H);
      ctx.shared.md = sets.magicDust(ctx, { center: [x0 + 1.5, 0.25, ZC - 1.4], radius: 1.4, height: 0.6, count: 16, rise: 0.15, px: [10, 22], seed: 's78dust' }); ctx.add(ctx.shared.md);
    },
    update(ctx, t) { const s = ctx.shared; s.f.update(t); s.GL.update(t); s.W.update(t); s.fam.update(t); s.md.update(t); K.gnomeIdle(s.g, t, { seed: 's78', amp: 0.3 }); },
  },

  // s79 "and every mound sank," (89.75-91.02) - top-down over the lawn beside Grandpa's bed (frame turned so the house is
  // at screen-left and the porch at the top: the ring rolls left -> right, the board's screen direction for s78-s79):
  // Grandpa small at the left edge in his lantern ring, five mounds on the dark lawn; the gold ring rolls out from him and
  // each mound deflates as it passes, the first on "mound" (90.18, f5411), then one every 0.15 s; the turf settles flat
  // behind it and the reflector eyes wink out. h 14 studs, pitch -90, fov 60, push 12 % + crane 2 studs. A low warm key
  // from the house side gives the mounds their relief. (The ring is re-timed for this angle so the passes land on the word.)
  mounds_sink: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); frontDoor(ctx);
      const g = grandpaAt(ctx, { lantern: 1 }); ctx.shared.g = g;
      const lan = worldOf(g.getObjectByName('lantern')); const Cn = new THREE.Vector3(lan.x, 0, lan.z);
      const ctr = new THREE.Vector3(-2.55, 0, -10.95); const yw = (c.yaw_deg || 0) * DEG; const o = new THREE.Vector3(-0.01, 0, 0).applyAxisAngle(YAX, yw);
      ctx.camera.set({ pos: [ctr.x + o.x, c.height_studs * S, ctr.z + o.z], target: ctr.toArray(), fov: p.fov });
      basePush(ctx); ctx.camera.crane((c.drift && c.drift.crane_studs || 2) * S);
      const rig = sets.magicGlow(ctx, { set: H, skyPreset: C.GALAXY_LOW, hemiIntensity: 0.7, key: { intensity: 0.3 }, lamp: { n: 0 }, postOpts: { exposure: 1.0, glow: { amount: 0.08 } } }); ctx.shared.rig = rig;
      ctx.add(ctx.lights.sun({ color: '#ffc896', intensity: 1.6, pos: [GP[0] - 3, 3.2, GP[2] - 7], target: [ctr.x, 0, ctr.z], shadow: false }));
      ctx.shared.GL = grandpaLantern(ctx, g, { cd: 1.6, levelFn: (t) => fwoomLevelEp(ctx, t) });
      const v = 8 * S; const tM = evT(ctx, 'mound', 0.433); const r0 = 1.9; const tW0 = tM - r0 / v;
      const W = X.lightWave(ctx, { center: Cn, t0: tW0, speed: 8, height: 1.0, width: 1.4, intensity: 1.5, sparkles: 60, sector: [-10, 200], light: 0, seed: 's79w' }); ctx.add(W.group); ctx.shared.W = W;
      const f = CR.moleField(ctx, { center: [ctr.x - 0.6, ctr.z + 0.4], size: [16, 14], res: 112, seed: 's79f', heads: 'snout', height: [0.8, 1.0] }); ctx.add(f.group);
      [[1.9, 10, 1.0], [2.284, 48, 0.95], [2.668, 22, 1.05], [3.052, 56, 0.95], [3.436, 34, 1.0]].forEach(([r, a, sc]) => {
        const x = Cn.x - Math.sin(a * DEG) * r, z = Cn.z + Math.cos(a * DEG) * r; const k = f.add({ at: [x, z], scale: sc, face: [Cn.x, Cn.z] }); f.eyes(k, -5, null); f.sink(k, tW0 + r / v, 0.45);
      });
      ctx.shared.f = f; ctx.shared.fam = familyLanterns(ctx, H, { level: 0.6 });
      ctx.shared.fx = sparks(ctx, [ctr.x - 0.5, 0.6, ctr.z + 0.3], [3.6, 0.6, 2.2], 8, 's79', { px: [40, 70] });
    },
    update(ctx, t) { const s = ctx.shared; s.f.update(t); s.GL.update(t); s.W.update(t); s.fam.update(t); s.fx.update(t); },
  },

  // s80 "eyes winking out pair by pair." (91.02-92.50) - low across the dark lawn beyond the light, toward next door's
  // fence and the dark street corner: five amber reflector-eye pairs blink out one pair at a time on "winking" / "out" /
  // "pair" / "by" / "pair" (f5477, 5500, 5511, 5525, 5534), each with the blip glint, and the mound sinks away behind it.
  // The magic grade decays toward night (magic 1 -> 0.4 over the shot). h 1.0, d 8, yaw 0, pitch 2, fov 60, push 19 %.
  eyes_wink_out: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); hideBoard(H);
      const cam = new THREE.Vector3(-1.95, c.height_studs * S, -11.35); const dirL = new THREE.Vector3(-0.42, 0, 1).normalize();
      const look = cam.clone().addScaledVector(dirL, c.dist_studs * S); look.y = cam.y + c.dist_studs * S * Math.tan(c.pitch_deg * DEG);
      ctx.camera.set({ pos: cam.toArray(), target: look.toArray(), fov: p.fov }); basePush(ctx);
      const rig = sets.magicGlow(ctx, { set: H, skyPreset: C.GALAXY_LOW, skyOpts: { intensity: 1.6 }, hemiIntensity: 0.75, key: { intensity: 0.35 }, lamp: { n: 2 }, postOpts: { exposure: 1.0 } }); ctx.shared.rig = rig;
      ctx.shared.A = sets.postPreset('magic', { exposure: 1.0 }); ctx.shared.Bp = sets.postPreset('nightHigh', { exposure: 1.0 });
      ctx.shared.gb = C.gradeBlend(ctx.shared.A.grade, ctx.shared.Bp.grade);
      const side = new THREE.Vector3(dirL.z, 0, -dirL.x);   // screen-left
      const at = (fwd, lat) => cam.clone().addScaledVector(dirL, fwd).addScaledVector(side, lat);
      const f = CR.moleField(ctx, { center: [at(3.0, 0).x, at(3.0, 0).z], size: [20, 20], res: 72, seed: 's80f', heads: 'eyes' }); ctx.add(f.group);
      const pts = [[3.9, 0.55, 1.05], [2.3, -0.42, 0.95], [4.6, -0.5, 1.1], [3.0, 0.05, 1.0], [1.65, 0.36, 0.9]];
      const tOff = [0, 1, 2, 3, 4].map((i) => evT(ctx, i, 0.3 + 0.25 * i));
      pts.forEach(([fw, lat, sc], i) => { const q = at(fw, lat); const k = f.add({ at: [q.x, q.z], scale: sc, face: [cam.x, cam.z] }); f.eyes(k, -5, tOff[i]); f.sink(k, tOff[i] + 0.05, 0.55); });
      f.update(0); const items = []; pts.forEach((_, i) => { const e = X.fieldEyes(f, i); if (e) items.push({ L: e[0], R: e[1], t: tOff[i] }); });
      const Wk = X.winkOut(ctx, items, { px: 56 }); ctx.add(Wk.group); Object.assign(ctx.shared, { f, Wk });
      ctx.shared.fx = sparks(ctx, at(1.2, 0).setY(0.5), [1.4, 0.5, 1.0], 5, 's80', { px: [36, 64] });
    },
    update(ctx, t) {
      const s = ctx.shared; s.f.update(t); s.Wk.update(t); s.fx.update(t);
      const k = 0.6 * clamp01(t / ctx.shot.duration); const pp = ctx.post.params; s.gb(pp.grade, k); pp.exposure = lerp(s.A.exposure, s.Bp.exposure, k);
      pp.bloom.strength = lerp(s.A.bloom.strength, s.Bp.bloom.strength, k); pp.bloom.threshold = lerp(s.A.bloom.threshold, s.Bp.bloom.threshold, k); if (pp.glow) pp.glow.amount = lerp(0.12, 0, k);
      hemiTo(s.rig, ['#ffcdb8', '#5a2030', 0.75], ['#8a90ff', '#241a3a', 1.0], k);
    },
  },

  // s81 "Then he stood still, facing Theo's window." (92.50-94.07) - the quiet wide (heroLot quietWide view): a small
  // gnome in his flowerbed under the lit window, lantern low and steady (level 1, 5-stud ring), Theo asleep inside, the
  // hero small on the lawn sitting back on his heels to the right of him (so the gnome stays clear); the family lanterns,
  // the open door. h 7, d 24, yaw -10, pitch -10, fov 60, push 12 % (dolly).
  quiet_wide: {
    build(ctx) {
      const p = ctx.params; const H = nightLot(ctx); frontDoor(ctx); theoAsleep(ctx, H);
      const g = grandpaAt(ctx, { lantern: 1 }); ctx.shared.g = g;
      const hp = [GP[0] + 0.95, 0, GP[2] + 1.05]; const hero = K.makeCharacter('heroBarefoot', { face: 'content' }); hero.position.set(...hp); hero.rotation.y = yawTo(hp, [GP[0], 0, GP[2] - 0.3]);
      K.setPose(hero, { ...K.POSES.sitFloor, armLx: 30, armRx: 30, armLz: -8, armRz: -8, neckX: 10 }); ctx.add(hero);
      ctx.add(sets.contactShadow(ctx, { pos: [hp[0], 0.005, hp[2]], radius: 0.45, opacity: 0.35 }));
      ctx.camera.set(H.ep01.views.quietWide); basePush(ctx, { mode: 'dolly' });
      nightRig(ctx, H, 'nightHigh', { window: { n: 2, cd: 2.4, color: '#ffd9a0', maxD: 14 }, hemiIntensity: 1.1, postOpts: { exposure: 1.1 } });
      ctx.shared.GL = grandpaLantern(ctx, g, { cd: 1.4 }); ctx.shared.fam = familyLanterns(ctx, H);
      ctx.shared.fx = sparks(ctx, up(GP, 3.5, 2, 6), [4.5, 2.2, 3.0], 9, 's81', { px: [44, 80] });
    },
    update(ctx, t) { const s = ctx.shared; s.GL.update(t); s.fam.update(t); s.fx.update(t); K.gnomeIdle(s.g, t, { seed: 's81', amp: 0.25 }); },
  },
};
