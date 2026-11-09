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
//   SIT     the hero at dawn, sitting on the lawn by the porch's left corner, front-right of Grandpa
//   T_ASK   Theo on the lawn 2 m in front of Grandpa's bed (s83-s85 start), facing him; T_STEP after the nudge
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
const SIT = [-1.6, 0, -11.2];
const T_ASK = [-2.2, 0, -10.4];
const T_STEP = [-2.21, 0, -10.65];
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
// The light wave's walls fade out within [d0, d1] m of the lens (a copy of fx_ep01's wall shader with a distance term), so
// the wall can pass the lens at ground level without washing the whole frame.
function nearFade(group, d0 = 0.5, d1 = 1.4) {
  group.traverse((m) => {
    const mt = m.material; if (!m.isMesh || !mt || !mt.isShaderMaterial || !/vV = normalize\(cameraPosition/.test(mt.vertexShader)) return;
    mt.vertexShader = mt.vertexShader.replace('varying vec3 vN, vV;', 'varying vec3 vN, vV; varying float vD;').replace('vV = normalize(cameraPosition - w.xyz);', 'vV = normalize(cameraPosition - w.xyz); vD = length(cameraPosition - w.xyz);');
    mt.fragmentShader = mt.fragmentShader.replace('varying vec3 vN, vV;', `varying vec3 vN, vV; varying float vD;`).replace('gl_FragColor = vec4(uC * uA * a, 1.0);', `gl_FragColor = vec4(uC * uA * a * smoothstep(${d0.toFixed(3)}, ${d1.toFixed(3)}, vD), 1.0);`);
    mt.needsUpdate = true;
  });
}
// Lerp the hemisphere of a rig between two looks.
function hemiTo(rig, a, b, k) { if (!rig || !rig.hemi) return; rig.hemi.color.set(a[0]).lerp(new THREE.Color(b[0]), k); rig.hemi.groundColor.set(a[1]).lerp(new THREE.Color(b[1]), k); rig.hemi.intensity = lerp(a[2], b[2], k); }

// ------------------------------------------------------------------ dawn helpers
// Theo with the whale under his left arm; his right arm is free (point / wave). Pose keys merged over this base.
const THEO_BASE = { armLx: 14, armLz: -10, armRz: 4 };
// The dawn light on our lot (heroLight: sets.dawn, sun from the street side, exposure 1.7, soft shadows).
function dawnLight(ctx, H, o = {}) { return SE.heroLight(ctx, H, { sun: { az: 150, el: 10 }, ...o }); }
// Solve a pose key (bisection) so a hand socket reaches the target height y (world m); returns the hand position.
function solveArm(av, pose, key, y, { lo = -20, hi = 170, side = 'R' } = {}) {
  const hand = () => { K.setPose(av, pose); av.updateMatrixWorld(true); return worldOf(K.handSocket(av, side)); };
  for (let i = 0; i < 18; i++) { const m = (lo + hi) / 2; pose[key] = m; const h = hand(); if (h.y > y) hi = m; else lo = m; }
  pose[key] = (lo + hi) / 2; return hand();
}
// A mud smudge on the hero's cheek (s84): the decal face redrawn with a soft brown smear on his right cheek.
function mudCheekFace(ctx, face, overlays) {
  return ctx.cache('ep01p5:mudFace2:' + face, () => {
    const src = K.faceTexture(face, overlays).image; const c = document.createElement('canvas'); c.width = src.width; c.height = src.height; const g = c.getContext('2d');
    g.drawImage(src, 0, 0); const k = c.width / 512; const r = makeRng(hash32('mudCheek'));
    // "smiles with wet eyes": the wetEyes frown is replaced by a smile arc (same 9-px line)
    g.save(); g.globalCompositeOperation = 'destination-out'; g.fillRect(200 * k, 336 * k, 112 * k, 56 * k); g.restore();
    g.strokeStyle = '#141414'; g.lineWidth = 9 * k; g.lineCap = 'round'; g.beginPath(); g.arc(256 * k, 318 * k, 40 * k, 30 * DEG, 150 * DEG); g.stroke();
    for (let i = 0; i < 9; i++) { const x = (150 + r() * 46) * k, y = (300 + r() * 26) * k; const gr = g.createRadialGradient(x, y, 0, x, y, (12 + r() * 12) * k); gr.addColorStop(0, 'rgba(92,58,34,0.55)'); gr.addColorStop(1, 'rgba(92,58,34,0)'); g.fillStyle = gr; g.fillRect(x - 30 * k, y - 30 * k, 60 * k, 60 * k); }
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; t.userData.persistent = true; return t;
  });
}
function setFaceTex(av, tex) { const f = K.rig(av).face; if (!f) return; f.material = f.material.clone(); f.material.map = tex; }

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
      const F = X.fwoom(ctx, { gnome: g, t0: tF, t2: tFl, rig, peak: 4.5, cd: [1.6, 7, 2.4], burst: false, wave: { sparkles: 40, height: 1.2 }, seed: 's77' }); ctx.add(F.group); ctx.shared.F = F;
      // the burst ring + motes (fwoom's own burst has a 420 px core that whites out a close-up: bible P3 "no white flash frames")
      const lp = worldOf(g.getObjectByName('lanternGlass') || g.getObjectByName('lantern'));
      ctx.shared.b1 = sets.burst(ctx, { pos: lp.toArray(), t0: tF, dur: 0.4, count: 30, spread: 0.8, px: [34, 80], ringPx: [60, 900], ringColor: '#ffe6c0', colors: ['#ffffff', '#ffd27a', '#ff9ad5', '#fff2d8'], corePx: 220, brightness: 2.0, seed: 's77b1' }); ctx.add(ctx.shared.b1);
      ctx.shared.b2 = sets.burst(ctx, { pos: lp.toArray(), t0: tFl, dur: 0.35, count: 14, spread: 0.6, px: [28, 60], ringPx: [40, 520], ringColor: '#ffe6c0', colors: ['#ffd27a', '#ffe2a8', '#fff2d8'], corePx: 150, brightness: 1.8, seed: 's77b2' }); ctx.add(ctx.shared.b2);
      ctx.camera.shake({ t0: tF, dur: 0.4, rot: 0.35, pos: 0.004, px: 10, freq: 14, seed: 77 });
      ctx.shared.fam = familyLanterns(ctx, H);
      const B = camBasis(ctx); ctx.shared.fx = sparks(ctx, eyes.clone().lerp(B.pos, 0.4).add(new THREE.Vector3(0, 0.1, 0)), [0.9, 0.7, 0.5], 8, 's77', { px: [44, 80] });
    },
    update(ctx, t) { const s = ctx.shared; K.gnomeIdle(s.g, t, { seed: 's77', amp: 0.3 }); lanternSwing(s.g, t - s.tF, { amp: 6, decay: 1.4 }); s.F.update(t); s.b1.update(t); s.b2.update(t); s.fam.update(t); s.fx.update(t); },
  },

  // s78 "light rolled across the lawn," (88.58-89.75) - ground level on the lawn: the FWOOM wall of gold light rolls out
  // from Grandpa's bed (behind-left) and sweeps left -> right across the frame, lighting the blades, sparkles kicked up at
  // its front, and overtakes the lens on "across" (89.13, f5348). The camera trucks right with it (11 studs over the shot,
  // ~9 studs/s, its path at 55 deg to the wave's radius so the wave, at 8 studs/s, still overtakes it) + push 12 % (fov).
  // The wall fades within 1.4 m of the lens (no full-frame wash as it passes). Two mounds in its path sink as it reaches
  // them. (The wave keeps its 8 studs/s; its start is re-timed for this angle so the pass lands on the word.)
  light_rolls: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); hideBoard(H); frontDoor(ctx, { light: 1.6, glow: 1.0 }); theoAsleep(ctx, H);
      const g = grandpaAt(ctx, { lantern: 1 }); ctx.shared.g = g;
      const lan = worldOf(g.getObjectByName('lantern')); const Cn = new THREE.Vector3(lan.x, 0, lan.z);
      const v = 8 * S; const tA = evT(ctx, 'across', 0.55); const dur = ctx.shot.duration; const truck = (c.drift && c.drift.truck_studs ? c.drift.truck_studs : 11) * S;
      const u = new THREE.Vector3(0.55, 0, 0.835).normalize(); const camY = 1.4 * S; /* 1.4 studs (board 0.5): just over the blades, so the lit band on the grass reads */ const CA = Cn.clone().addScaledVector(u, 3.9); CA.y = camY;
      let right = u.clone().applyAxisAngle(YAX, -55 * DEG); let look = new THREE.Vector3(right.z, 0, -right.x);
      if (look.dot(Cn.clone().sub(CA)) < 0) { right = u.clone().applyAxisAngle(YAX, 55 * DEG); look = new THREE.Vector3(right.z, 0, -right.x); }
      const C0 = CA.clone().addScaledVector(right, -truck * tA / dur); const tW0 = tA - 3.9 / v;
      const tgt = C0.clone().addScaledVector(look, c.dist_studs * S); tgt.y = camY + c.dist_studs * S * Math.tan(-5 * DEG);
      ctx.camera.set({ pos: C0.toArray(), target: tgt.toArray(), fov: p.fov }).truck(truck); basePush(ctx);
      clearPlants(H, [[C0.x, C0.z, 0.25], [CA.x, CA.z, 0.25]]);
      ctx.shared.rig = sets.magicGlow(ctx, { set: H, skyPreset: C.GALAXY_LOW, skyOpts: { intensity: 1.6 }, hemiIntensity: 0.5, key: { intensity: 0.3 }, lamp: { n: 0 }, window: { n: 0 }, postOpts: { exposure: 0.95, glow: { amount: 0.06 } } });
      ctx.shared.GL = grandpaLantern(ctx, g, { cd: 1.6, levelFn: (t) => fwoomLevelEp(ctx, t) });
      const W = X.lightWave(ctx, { center: Cn, t0: tW0, speed: 8, height: 2.2, width: 1.8, intensity: 2.2, sparkles: 110, sector: 'camera', light: 4.0, seed: 's78w' }); ctx.add(W.group); ctx.shared.W = W; nearFade(W.group, 0.4, 1.2);
      const f = CR.moleField(ctx, { center: [CA.x, CA.z], size: [22, 22], res: 72, seed: 's78f', heads: 'snout' }); ctx.add(f.group);
      for (const [fw, lat, sc] of [[2.0, -0.2, 1.0], [3.2, 0.9, 1.1]]) { const q = CA.clone().addScaledVector(look, fw).addScaledVector(right, lat); const k = f.add({ at: [q.x, q.z], scale: sc, face: [Cn.x, Cn.z] }); f.eyes(k, -5, null); f.sink(k, tW0 + Math.hypot(q.x - Cn.x, q.z - Cn.z) / v, 0.5); }
      ctx.shared.f = f; ctx.shared.fam = familyLanterns(ctx, H);
    },
    update(ctx, t) { const s = ctx.shared; s.f.update(t); s.GL.update(t); s.W.update(t); s.fam.update(t); K.gnomeIdle(s.g, t, { seed: 's78', amp: 0.3 }); },
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
      const ctr = new THREE.Vector3(-4.35, 0, -11.05); const yw = (c.yaw_deg || 0) * DEG; const o = new THREE.Vector3(-0.01, 0, 0).applyAxisAngle(YAX, yw);
      ctx.camera.set({ pos: [ctr.x + o.x, c.height_studs * S, ctr.z + o.z], target: ctr.toArray(), fov: p.fov });
      basePush(ctx); ctx.camera.crane((c.drift && c.drift.crane_studs || 2) * S);
      const rig = sets.magicGlow(ctx, { set: H, skyPreset: C.GALAXY_LOW, hemiIntensity: 0.7, key: { intensity: 0.3 }, lamp: { n: 0 }, postOpts: { exposure: 1.0, glow: { amount: 0.08 } } }); ctx.shared.rig = rig;
      ctx.add(ctx.lights.sun({ color: '#ffc896', intensity: 2.6, pos: [GP[0] - 2, 2.2, GP[2] - 7], target: [ctr.x, 0, ctr.z], shadow: false }));
      ctx.shared.GL = grandpaLantern(ctx, g, { cd: 1.6, levelFn: (t) => fwoomLevelEp(ctx, t) });
      const v = 8 * S; const tM = evT(ctx, 'mound', 0.433); const r0 = 1.9; const tW0 = tM - r0 / v;
      const W = X.lightWave(ctx, { center: Cn, t0: tW0, speed: 8, height: 1.0, width: 1.4, intensity: 1.5, sparkles: 60, sector: [-10, 200], light: 0, seed: 's79w' }); ctx.add(W.group); ctx.shared.W = W;
      const f = CR.moleField(ctx, { center: [ctr.x + 0.6, ctr.z + 0.4], size: [18, 14], res: 112, seed: 's79f', heads: 'snout', height: [1.05, 1.25] }); ctx.add(f.group);
      [[1.9, 28, 1.0], [2.284, 62, 0.95], [2.668, 40, 1.05], [3.052, 74, 0.95], [3.436, 52, 1.0]].forEach(([r, a, sc]) => {
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
      const cam = new THREE.Vector3(-1.95, c.height_studs * S, -11.35); const dirL = new THREE.Vector3(-1, 0, 0.42).normalize();
      const look = cam.clone().addScaledVector(dirL, c.dist_studs * S); look.y = cam.y + c.dist_studs * S * Math.tan(c.pitch_deg * DEG);
      ctx.camera.set({ pos: cam.toArray(), target: look.toArray(), fov: p.fov }); basePush(ctx);
      const rig = sets.magicGlow(ctx, { set: H, skyPreset: C.GALAXY_LOW, skyOpts: { intensity: 1.6 }, hemiIntensity: 0.55, key: { intensity: 0.3 }, lamp: { n: 2 }, postOpts: { exposure: 0.95 } }); ctx.shared.rig = rig;
      ctx.shared.A = sets.postPreset('magic', { exposure: 0.95 }); ctx.shared.Bp = sets.postPreset('nightHigh', { exposure: 1.0 });
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
      hemiTo(s.rig, ['#ffcdb8', '#5a2030', 0.55], ['#8a90ff', '#241a3a', 0.95], k);
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
      const hp = [GP[0] + 0.72, 0, GP[2] + 1.28]; const hero = K.makeCharacter('heroBarefoot', { face: 'content' }); hero.position.set(...hp); hero.rotation.y = yawTo(hp, [GP[0], 0, GP[2] - 0.3]);
      K.setPose(hero, { ...K.POSES.sitFloor, armLx: 30, armRx: 30, armLz: -8, armRz: -8, neckX: 10 }); ctx.add(hero);
      ctx.add(sets.contactShadow(ctx, { pos: [hp[0], 0.005, hp[2]], radius: 0.45, opacity: 0.35 }));
      ctx.camera.set(H.ep01.views.quietWide); basePush(ctx, { mode: 'dolly' });
      nightRig(ctx, H, 'nightHigh', { window: { n: 2, cd: 2.4, color: '#ffd9a0', maxD: 14 }, hemiIntensity: 1.1, postOpts: { exposure: 1.1 } });
      ctx.shared.GL = grandpaLantern(ctx, g, { cd: 1.4 }); ctx.shared.fam = familyLanterns(ctx, H);
      ctx.shared.fx = sparks(ctx, up(GP, 3.5, 2, 6), [4.5, 2.2, 3.0], 9, 's81', { px: [44, 80] });
    },
    update(ctx, t) { const s = ctx.shared; s.GL.update(t); s.fam.update(t); s.fx.update(t); K.gnomeIdle(s.g, t, { seed: 's81', amp: 0.25 }); },
  },
  // s82 "At dawn, Theo came out in his socks." (94.07-95.87) - pink dawn over our house, low across the dewy lawn: the
  // front door (closed at first) opens on "came" (94.89, f5694) in 14 frames and Theo pads out onto the porch in striped
  // socks and pyjamas, the whale under his arm, small steps (walk 1.0 s), sleepy -> wonder; the hero sits muddy-kneed on
  // the lawn by Grandpa and the half-filled hole; lanterns 0.5, windows off. dawnLow view (h 0.8, d 12 from the steps,
  // yaw 15), aimed between the door and the bed so both read; push 15 % (dolly). Dew glints.
  dawn_theo_out: {
    quality: { shadows: 'pcfsoft' },
    build(ctx) {
      const p = ctx.params; const H = dawnLot(ctx); hideBoard(H);
      const g = grandpaAt(ctx, { lantern: 0.5 }); ctx.shared.g = g;
      const tC = evT(ctx, 'came', 0.833); ctx.shared.tC = tC;
      ctx.shared.door = frontDoor(ctx, { light: 1.0, glow: 0.75, open: (t) => 1.75 * outCubic((t - tC) / (14 / 60)) });
      const hero = K.makeCharacter('heroMuddy', { face: 'content' }); hero.position.set(...SIT); hero.rotation.y = yawTo(SIT, [0.2, 0, -12.4]);
      K.setPose(hero, { ...K.POSES.sitFloor, armLx: 34, armRx: 30, armLz: -6, armRz: -6, neckX: 6 }); ctx.add(hero);
      ctx.add(sets.contactShadow(ctx, { pos: [SIT[0], 0.005, SIT[2]], radius: 0.45, opacity: 0.35 }));
      const theo = theoWithWhale('theoSocks', { face: 'sleeping' }); theo.rotation.y = 0.12; ctx.add(theo); ctx.shared.theo = theo;
      const aimP = new THREE.Vector3(-1.1, 0, -12.4); const cam = aimP.clone().addScaledVector(dirOf(-10 * DEG), 15 * S); cam.y = 0.8 * S;   // low, 15 studs out (board: 12 from the steps, yaw 15): door, Grandpa and the hero all in frame
      ctx.camera.set({ pos: cam.toArray(), target: [aimP.x, 0.98, aimP.z], fov: p.fov }); basePush(ctx, { mode: 'dolly' });
      ctx.shared.rig = dawnLight(ctx, H);
      ctx.shared.dew = dew(ctx, [cam.x - 1.2, 0.18, cam.z - 1.6], [2.2, 0.25, 1.6], 6, 's82dew');
    },
    update(ctx, t) {
      const s = ctx.shared; s.door.update(t); const th = s.theo; const t0 = s.tC + 6 / 60; const u = Math.max(0, t - t0);
      th.visible = t >= t0; const z0 = LOT_DOOR[2] + 0.05; th.position.set(0.05, LOT_DOOR[1], z0 + Math.min(0.9, u * 0.62));
      const w = t >= t0 ? K.walkCycle(u, { period: 1.0, legs: 20, holdArms: true }) : {}; K.setPose(th, { ...THEO_BASE, ...w, neckX: -4 });
      K.setFace(th, t < s.tC + 0.55 ? 'sleeping' : 'wonder'); K.gnomeIdle(s.g, t, { seed: 's82', amp: 0.2 }); s.dew.update(t);
    },
  },

  // s83 "Is he nice?" (95.87-96.62) - MCU at Theo's eye height: on the lawn in front of the porch, whale under his arm, he
  // points at the gnome (off screen, screen-left of the lens), the arm rising in 0.45 s; sleepy and curious (wonder).
  // h 3.8, d 3.0, yaw -10, pitch 0, push 18 %.
  theo_asks: {
    quality: { shadows: 'pcfsoft' },
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = dawnLot(ctx); hideBoard(H); grandpaAt(ctx, { lantern: 0.5 });
      // the lens sits 40 deg to Theo's left of the gnome direction (board yaw -10) so the pointing arm reads across the frame
      const theo = theoWithWhale('theoSocks', { face: (p.cast[0] && p.cast[0].face) || 'wonder' }); theo.position.set(...T_ASK); const toG = yawTo(T_ASK, GP); theo.rotation.y = toG + 22 * DEG; ctx.add(theo); ctx.shared.theo = theo;
      ctx.add(sets.contactShadow(ctx, { pos: [T_ASK[0], 0.005, T_ASK[2]], radius: 0.36, opacity: 0.35 }));
      K.setPose(theo, THEO_BASE); theo.updateWorldMatrix(true, true); const head = worldOf(theo.getObjectByName('head'));
      boardCam(ctx, [head.x, 0, head.z], { ref: dirOf(toG).toArray(), yaw: 40, dist: c.dist_studs + 1.6, h: c.height_studs, pitch: c.pitch_deg, fov: p.fov, aimY: head.y - 0.2 }); basePush(ctx);
      ctx.shared.rig = dawnLight(ctx, H); warmKey(ctx, head.toArray(), { cd: 0.8, d: 1.0, color: '#ffd8c0' });
      ctx.shared.dew = dew(ctx, [head.x, head.y - 0.3, head.z].map((v, i) => v + [0.25, 0, 0.25][i]), [1.2, 0.8, 0.6], 4, 's83dew');
    },
    update(ctx, t) { const s = ctx.shared; const u = outQuad((t - 0.04) / 0.45); K.setPose(s.theo, { ...THEO_BASE, armRx: 72 * u, armRz: 4 + 44 * u, neckY: -18 * u, neckX: 2 }); s.dew.update(t); },
  },

  // s84 "The nicest." (96.62-97.22) - CU, eye level with the hero sitting on the lawn by Grandpa: he smiles with wet eyes
  // (wetEyes), a smudge of mud on his cheek; the low dawn sun rims him from behind-side. h 3.2, d 2.2, yaw 10, push 18 %.
  hero_nicest: {
    quality: { shadows: 'pcfsoft' },
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = dawnLot(ctx); hideBoard(H); grandpaAt(ctx, { lantern: 0.5 });
      const hero = K.makeCharacter('heroMuddy', { face: 'wetEyes' }); hero.position.set(...SIT); const toT = yawTo(SIT, T_ASK); hero.rotation.y = toT;
      K.setPose(hero, { ...K.POSES.sitFloor, armLx: 34, armRx: 30, armLz: -6, armRz: -6, neckX: 8 }); ctx.add(hero); ctx.shared.hero = hero;
      setFaceTex(hero, mudCheekFace(ctx, 'wetEyes', hero.userData.faceOverlays || { freckles: true }));
      hero.updateWorldMatrix(true, true); const head = worldOf(hero.getObjectByName('head'));
      boardCam(ctx, [head.x, 0, head.z], { ref: dirOf(toT).toArray(), yaw: c.yaw_deg, dist: c.dist_studs, h: c.height_studs, pitch: c.pitch_deg, fov: p.fov, aimY: head.y + 0.02 }); basePush(ctx);
      ctx.shared.rig = dawnLight(ctx, H); warmKey(ctx, head.toArray(), { cd: 0.9, d: 1.0, color: '#ffd8c0' });
    },
    update(ctx, t) { K.setPose(ctx.shared.hero, { ...K.POSES.sitFloor, armLx: 34, armRx: 30, armLz: -6, armRz: -6, neckX: 8, ...K.breath(t) }); },
  },

  // s85 "Say goodnight, and he'll blink." (97.22-98.58) - MS two-shot from the flowerbed side (where Grandpa stands, just
  // under the lens): the hero, kneeling beside Theo, sets a hand on his shoulder (16 frames) and nudges him a small step
  // toward the gnome. Faces heartfelt / wonder. h 3.5, d 8, yaw -20, pitch -2, push 19 %.
  nudge_theo: {
    quality: { shadows: 'pcfsoft' },
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = dawnLot(ctx); hideBoard(H); grandpaAt(ctx, { lantern: 0.5 });
      const f = P3(GP).sub(P3(T_ASK)).setY(0).normalize(); const toG = Math.atan2(f.x, f.z); const right = new THREE.Vector3(-f.z, 0, f.x);
      const theo = theoWithWhale('theoSocks', { face: 'wonder' }); theo.rotation.y = toG; ctx.add(theo);
      // the hero kneels at Theo's left; his right hand comes up onto Theo's left shoulder and nudges him on toward Grandpa
      const hp = P3(T_ASK).addScaledVector(right, -0.5).addScaledVector(f, -0.12); const hero = K.makeCharacter('heroMuddy', { face: 'heartfelt' }); hero.position.copy(hp); hero.rotation.y = toG + 12 * DEG; ctx.add(hero);
      ctx.add(sets.contactShadow(ctx, { pos: [hp.x, 0.005, hp.z], radius: 0.45, opacity: 0.35 }));
      Object.assign(ctx.shared, { theo, hero, hp, f, right });
      // the two-shot from where they are looking: the lens in the flowerbed by the window, Grandpa's hat low in the
      // foreground, the pair facing it (yaw 20 toward the bed's open side, away from the porch)
      const mid = P3(T_ASK).lerp(hp, 0.5);
      boardCam(ctx, [mid.x, 0, mid.z], { ref: f.toArray(), yaw: 20, dist: c.dist_studs, h: c.height_studs, pitch: c.pitch_deg, fov: p.fov }); basePush(ctx);
      const B = camBasis(ctx); clearPlants(H, [[B.pos.x, B.pos.z, 0.4]]);
      ctx.shared.rig = dawnLight(ctx, H); warmKey(ctx, [mid.x, 1.0, mid.z], { cd: 1.2, d: 1.2, color: '#ffd8c0' });
      ctx.shared.dew = dew(ctx, [mid.x, 0.5, mid.z - 0.6], [1.6, 0.8, 1.0], 5, 's85dew');
    },
    update(ctx, t) {
      const s = ctx.shared; const k = clamp01((t - 0.62) / 0.35); const ks = inOutSine(k);
      const tp = P3(T_ASK).lerp(P3(T_STEP), ks); s.theo.position.copy(tp);
      const step = k > 0 && k < 1 ? Math.sin(Math.PI * k) : 0; K.setPose(s.theo, { ...THEO_BASE, legLx: 18 * step, legRx: -10 * step, neckX: -6 });
      s.theo.updateMatrixWorld(true); const sh = worldOf(s.theo.getObjectByName('head')).add(new THREE.Vector3(0, -0.3, 0)).addScaledVector(s.right, -0.13).addScaledVector(s.f, -0.05);
      const ua = outCubic((t - 0.12) / (16 / 60)); const pose = { ...K.POSES.kneel, armLx: 34, armLz: -6, armRz: 18, bodyX: 20 + 8 * ks, neckX: -4, neckY: -14 };
      s.hero.position.copy(s.hp).addScaledVector(s.f, 0.14 * ks);
      const reach = { ...pose }; solveArm(s.hero, reach, 'armRx', sh.y, { lo: 0, hi: 150, side: 'R' }); K.setPose(s.hero, K.mixPose(pose, reach, ua));
      s.dew.update(t);
    },
  },

  // s86 "Theo tried it, and Grandpa blinked." (98.58-100.35) - low, from the flowerbed at Grandpa's front-left: his face
  // 3/4 big in the left foreground, eyes rolled toward Theo (screen-right), Theo behind at right waving shyly; on
  // "blinked" (99.89, f5993) the gnome blinks (2 frames) with the TIK glint. Lantern 0.5. h 1.1, d 1.6, pitch 6, push 20 %.
  theo_blink_twoshot: {
    quality: { shadows: 'pcfsoft' },
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = dawnLot(ctx); hideBoard(H);
      const g = grandpaAt(ctx, { lantern: 0.5 }); ctx.shared.g = g; const eyes = C.eyesOf(g);
      const theo = theoWithWhale('theoSocks', { face: (p.cast[1] && p.cast[1].face) || 'content' }); theo.position.set(...T_STEP); theo.rotation.y = yawTo(T_STEP, GP); ctx.add(theo); ctx.shared.theo = theo;
      ctx.add(sets.contactShadow(ctx, { pos: [T_STEP[0], 0.005, T_STEP[2]], radius: 0.36, opacity: 0.35 }));
      const toT = P3(T_STEP).sub(P3(GP)).setY(0).normalize(); const cdir = toT.clone().negate().applyAxisAngle(YAX, 24 * DEG);
      const cam = P3(eyes).addScaledVector(cdir, c.dist_studs * S); cam.y = BED[1] + c.height_studs * S;
      const th = worldOf(theo.getObjectByName('head')); const aim = P3(eyes).lerp(th, 0.62); const hd = Math.hypot(aim.x - cam.x, aim.z - cam.z); aim.y = cam.y + hd * Math.tan(c.pitch_deg * DEG) + 0.08;
      ctx.camera.set({ pos: cam.toArray(), target: aim.toArray(), fov: p.fov }); basePush(ctx);
      clearPlants(H, [[cam.x, cam.z, 0.32], [lerp(cam.x, eyes.x, 0.5), lerp(cam.z, eyes.z, 0.5), 0.2]]);
      K.setGnomeHead(g, 10, 4, 0); g.updateWorldMatrix(true, true);
      { const B = camBasis(ctx); C.gazeAt(g, B.pos.clone().addScaledVector(B.right, 0.55).add(new THREE.Vector3(0, 0.18, 0))); }   // eyes rolled to screen-right, toward Theo
      ctx.shared.rig = dawnLight(ctx, H); warmKey(ctx, eyes.toArray(), { cd: 0.7, d: 0.6, color: '#ffd8c0' });
      const tB = evT(ctx, 'blinked', 1.3); ctx.shared.tB = tB; const T = X.blinkTik(ctx, g, { t0: tB, frames: 2 }); ctx.add(T.group); ctx.shared.T = T;
    },
    update(ctx, t) {
      const s = ctx.shared; K.setGnomeLids(s.g, K.gnomeBlink(t, [s.tB], { frames: 2 })); s.T.update(t); K.gnomeIdle(s.g, t, { seed: 's86', amp: 0.2 });
      K.setPose(s.theo, { ...THEO_BASE, armRz: 112 + 9 * Math.sin(2 * Math.PI * 2 * t), armRx: 18, neckX: -4, neckZ: -3 });
    },
  },

  // s87 "At Theo." (100.35-100.82) - CU on Theo: his mouth becomes a delighted "o" (wonder), the whale under his arm, the
  // dawn street behind him. h 3.6, d 2.0, yaw -10, pitch 0, push 16 %. (ENGINE starts off screen.)
  theo_o: {
    quality: { shadows: 'pcfsoft' },
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = dawnLot(ctx); hideBoard(H); grandpaAt(ctx, { lantern: 0.5 });
      const theo = theoWithWhale('theoSocks', { face: (p.cast[0] && p.cast[0].face) || 'wonder' }); theo.position.set(...T_STEP); const toG = yawTo(T_STEP, GP); theo.rotation.y = toG; ctx.add(theo); ctx.shared.theo = theo;
      K.setPose(theo, { ...THEO_BASE, neckX: -6 }); theo.updateWorldMatrix(true, true); const head = worldOf(theo.getObjectByName('head'));
      boardCam(ctx, [head.x, 0, head.z], { ref: dirOf(toG).toArray(), yaw: c.yaw_deg, dist: c.dist_studs, h: c.height_studs, pitch: c.pitch_deg, fov: p.fov, aimY: head.y - 0.03 }); basePush(ctx);
      ctx.shared.rig = dawnLight(ctx, H); warmKey(ctx, head.toArray(), { cd: 0.8, d: 0.9, color: '#ffd8c0' });
    },
    update(ctx, t) { K.setPose(ctx.shared.theo, { ...THEO_BASE, neckX: -6 + 2 * outQuad(t / 0.2), ...K.breath(t) }); },
  },

  // s88 "From the truck, every gnome faced its house," (100.82-102.60) - POV from the open back of the leaving truck at
  // sunrise (sets_ep01 ep01Street + movingTruck 'leaving', the 'aisle' cargo framing the opening): the street recedes; on
  // every lawn a gnome faces its house, lanterns dimmed; Theo small on our lawn beside Grandpa. The truck pulls away from
  // the ENGINE start (100.37) at 4 studs/s^2 to 6 studs/s (~9 studs in the shot), + handheld 0.3 deg, + push 10 % (dolly).
  truck_pov: {
    quality: { shadows: 'pcfsoft' },
    build(ctx) {
      const p = ctx.params, c = p.camera;
      const T = SE.ep01Street(ctx, { tod: 'dawn', lanterns: 0.5, truck: 'leaving', truckOpts: { t0: epT(ctx, 100.37), accel: 4, vmax: 6, balconyBox: false, dome: false } }); ctx.add(T); ctx.shared.T = T;
      const gp = T.ep01.grandpa; const gpos = worldOf(gp);
      const theo = theoWithWhale('theo', { face: 'content' }); theo.position.set(gpos.x + 0.9, 0, gpos.z + 0.55); theo.rotation.y = 0.5; K.setPose(theo, { ...THEO_BASE, armRz: 130 }); ctx.add(theo); ctx.shared.theo = theo;
      // the lens rides in the cargo bay (povCamera) but keeps our lot in view as the street recedes (aim between the road
      // centre and Grandpa's bed, pitch -6), the box edges framing the opening
      const pov = T.ep01.truck.ep01.povCamera({ height: c.height_studs, back: 4.0, pitch: c.pitch_deg, fov: p.fov, yaw: 0 });
      const aimW = gpos.clone(); aimW.y = 0.9; const tmpV = new THREE.Vector3();
      ctx.camera.set({ pos: pov.pos, target: (t, o) => { const pp = pov.pos(t, tmpV); const tg = pov.target(t, o || new THREE.Vector3()); const a = aimW.clone().sub(pp).normalize().multiplyScalar(20).add(pp); return tg.lerp(a, 0.55); }, fov: pov.fov }).handheld({ rot: 0.3, pos: 0.004, freq: 1.1, seed: 88 }); basePush(ctx, { mode: 'dolly' });
      ctx.shared.rig = sets.dawn(ctx, { set: T, sun: { az: 92, el: 9 }, postOpts: { exposure: 1.6 } });
    },
    update(ctx, t) { const s = ctx.shared; s.T.ep01.update(t); K.setPose(s.theo, { ...THEO_BASE, armRz: 130 + 14 * Math.sin(2 * Math.PI * 1.8 * t), neckX: 4 }); },
  },

  // s89 "except one." (102.60-103.43) - tele from the truck (heroLot fromTruckTele, fov 25): Grandpa in his flowerbed with
  // his head turned round toward the truck, looking at us, Theo beside him; at 103.05 (f6183) the head grinds back toward
  // Theo's window (gnomeHeadTurn 0.8 s, stepped jitter), cut mid-turn and held through the pause. Truck vibration +-3 px,
  // push 15 % (fov). (Head yaw 160 -> 0, board 90 -> 0: the lens is behind him on the street, so 160 points his face at it.)
  grandpa_turned: {
    quality: { shadows: 'pcfsoft' },
    build(ctx) {
      const p = ctx.params; const H = dawnLot(ctx, { truck: false }); hideBoard(H);
      const g = grandpaAt(ctx, { lantern: 0.5 }); ctx.shared.g = g;
      // tele from the truck lane (12.8 m = 40 studs from him), over our picket fence
      const v0 = P3(H.ep01.views.fromTruckTele.pos); const gdir = v0.clone().sub(P3(GP)).setY(0).normalize(); const cam = P3(GP).addScaledVector(gdir, 40 * S).add(new THREE.Vector3(0.45, 0, 0)); cam.y = 8.5 * S; const v = { pos: cam.toArray() };   // 8.5 studs high (board 4): over the picket fence
      const theo = theoWithWhale('theoSocks', { face: (p.cast[1] && p.cast[1].face) || 'content' }); theo.position.set(...T_STEP); theo.rotation.y = yawTo(T_STEP, cam.toArray()) - 0.3; K.setPose(theo, { ...THEO_BASE, armRz: 125 }); ctx.add(theo); ctx.shared.theo = theo;
      const tgt = P3(GP).lerp(P3(T_STEP), 0.3); tgt.y = 0.7;
      ctx.camera.set({ pos: v.pos, target: tgt.toArray(), fov: p.fov }); basePush(ctx);
      ctx.shared.yawAt = Math.atan2(-gdir.x, -gdir.z) / DEG;   // head yaw that points his face at the lens (the gnome faces -Z)
      ctx.camera.custom((st, t) => { st.px[0] += 2.2 * Math.sin(t * 37.0) + 0.8 * Math.sin(t * 71.3 + 1.1); st.px[1] += 2.0 * Math.sin(t * 43.7 + 0.4) + 0.9 * Math.sin(t * 89.1); });
      ctx.shared.rig = dawnLight(ctx, H, { sun: { az: 150, el: 10 } });
      ctx.shared.tE = evT(ctx, 0, 0.45);
    },
    update(ctx, t) { const s = ctx.shared; K.setGnomeHead(s.g, K.gnomeHeadTurn(t, s.tE, 0.8, s.yawAt, 0), 2, 0); K.gnomeIdle(s.g, t, { seed: 's89', amp: 0.2 }); K.setPose(s.theo, { ...THEO_BASE, armRz: 125 + 12 * Math.sin(2 * Math.PI * 1.8 * t) }); },
  },
};
