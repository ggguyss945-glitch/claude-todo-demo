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
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
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
function clearPlants(root, circles, { names = /^(tulip:|stem)/, drop = null } = {}) {
  root.updateMatrixWorld(true); const v = new THREE.Vector3(); const out = drop || ((cx, cy, cz) => circles.some(([x, z, r]) => Math.hypot(cx - x, cz - z) < r));
  root.traverse((m) => {
    if (!m.isMesh || !names.test(m.name)) return; const g0 = m.geometry; const g = g0.index ? g0.toNonIndexed() : g0; const pa = g.attributes.position; const n = pa.count / 3; const keep = [];
    for (let i = 0; i < n; i++) { let cx = 0, cy = 0, cz = 0; for (let k = 0; k < 3; k++) { v.fromBufferAttribute(pa, i * 3 + k).applyMatrix4(m.matrixWorld); cx += v.x / 3; cy += v.y / 3; cz += v.z / 3; } if (!out(cx, cy, cz)) keep.push(i); }
    if (keep.length === n) { if (g !== g0) g.dispose(); return; }
    const ng = new THREE.BufferGeometry();
    for (const [name, at] of Object.entries(g.attributes)) { const sz = at.itemSize, src = at.array; const arr = new src.constructor(keep.length * 3 * sz); keep.forEach((tri, j) => arr.set(src.subarray(tri * 3 * sz, tri * 3 * sz + 3 * sz), j * 3 * sz)); ng.setAttribute(name, new THREE.BufferAttribute(arr, sz, at.normalized)); }
    if (g !== g0) g.dispose(); m.geometry = ng;
  });
}
// The agent board by the path: its back face shows the text mirrored (props.js); hidden in shots that see it from the house side (as part4).
function hideBoard(H) { const b = H.ep01.board; if (b) b.visible = false; }
// ... or keep it and blank its back face (box material 5 = -Z, the house side): a sign's back is plain, and hiding the
// panel leaves its post and arm standing bare (they are merged into the lot).
// ... or take the whole board out of a shot that never needs it: the panel hidden and its post + arm triangles stripped
// from the merged lot mesh (geometry copied, as clearPlants).
function removeBoard(H) {
  const b = H.ep01.board; if (!b) return; b.visible = false; const c = worldOf(b); const ax = new THREE.Vector3(1, 0, 0).applyQuaternion(b.getWorldQuaternion(new THREE.Quaternion())); ax.y = 0; ax.normalize();
  // the post stands 2.2 studs left of the panel centre and the arm runs to 2.7 studs right of it: strip along -2.65..2.85
  clearPlants(H, [], { names: /^(trim|black)/, drop: (x, y, z) => { const dx = x - c.x, dz = z - c.z; const along = dx * ax.x + dz * ax.z, across = -dx * ax.z + dz * ax.x; return y < 7.3 * S && Math.abs(across) < 0.4 * S && Math.abs(along - 0.1 * S) < 2.75 * S; } });
}
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

// ------------------------------------------------------------------ epilogue helpers (photos, phone, bench)
// The yearly photo, staged on our lot in spring daylight `year` years after the move (the sets owner's photoTexture
// recipe: heroLot day + year, Grandpa mossy by the year and looking back over his shoulder at the camera), with this
// shot's choices: Theo at 6 + year on the lawn beside him or grey at the window, Theo's granddaughter waving in the
// window, a thumbs-up, the mid-blink lids, and the view ('photo' = the yearly framing, 'close' = Grandpa close, 'bed' =
// the flowerbed). stagePhoto puts it in a scene (live, s93); photoTex renders it once per worker to a canvas texture.
function stagePhoto(ctx, year, o = {}) {
  const H = SE.heroLot(ctx, { tod: 'day', year, era: 'now', board: false, keepOff: false, truck: false, bed: 'grandpa', nextDoor: false, theoRoom: { era: 'later', lit: false }, roomGlow: false, gnomes: ['lawn0', 'lawn1', 'bedFront1'], grandpa: { age: o.age ?? Math.min(0.9, 0.05 + 0.85 * year / 60) } });
  sets.setWindows(H, 'off'); H.ep01.theo.setGlass('photo');
  const g = H.ep01.gnomes.grandpa; K.setGnomeHead(g, o.headYaw ?? 150, 4, 0); K.setGnomeGaze(g, 0, 2); if (o.blink) K.setGnomeLids(g, o.blink);
  const sp = H.ep01.spots; const bp = P3(sp.bed0); const w = P3(sp.theoWindow); const age = 6 + year; const people = [];
  const th = K.theoAt(age, { face: o.face || 'grin' });
  if (o.theo === 'window') { th.position.set(w.x + 0.12, 0.32, w.z - 1.15 * S); th.rotation.y = 0; K.setPose(th, { armRz: 18, armLz: 10, neckX: -6 }); }
  else { th.position.set(bp.x - 2.7 * S, 0, bp.z + 2.7 * S); th.rotation.y = 0.18; K.setPose(th, o.thumbs ? { armRx: 128, armRz: 12, armLz: 6, neckY: 6 } : age < 13 ? { armRz: 150, neckZ: -4 } : { armRz: 25, armRx: -20, neckY: 8 }); }
  people.push(th);
  if (o.girl) { const girl = K.makeCharacter('theoGranddaughter', { face: 'openSmile' }); girl.position.set(w.x - 0.18, 0.32, w.z - 1.1 * S); girl.rotation.y = 0; K.setPose(girl, { ...K.POSES.wave, armRz: 158 }); people.push(girl); }
  const B = bp; const views = { photo: { pos: up(B, 4.2, -1.7, 12.5), target: up(B, 3.2, -1.4, 0), fov: 45 }, close: { pos: up(B, 2.0, 0.6, 5.2), target: up(B, 1.0, 0.1, 0), fov: 40 }, bed: { pos: up(B, 4.2, -2.6, 7.6), target: up(B, 0.7, -0.6, 0), fov: 45 } };
  return { H, g, people, view: views[o.view || 'photo'] };
}
function photoLights(scene, bp, win) {
  scene.add(new THREE.HemisphereLight('#bcd4ff', '#5a4a30', 1.15)); const sun = new THREE.DirectionalLight('#fff3e0', 2.6); sun.position.set(bp.x - 14, 18, bp.z + 22); sun.target.position.copy(bp); scene.add(sun, sun.target);
  const fill = new THREE.PointLight('#fff0e0', 2.5, 0, 2); fill.position.set(bp.x + 1.2, 1.6, bp.z + 2.6); scene.add(fill);
  const bounce = new THREE.PointLight('#fff4e8', 3.0, 0, 2); bounce.position.copy(win).add(new THREE.Vector3(0.3, 0.4, -1.4)); scene.add(bounce);
}
const PHOTO_FS = `uniform sampler2D tDiffuse; uniform float exposure, warm, lift, sat; varying vec2 vUv;
  vec3 aces(vec3 x){ const float a=2.51, b=0.03, c=2.43, d=0.59, e=0.14; return clamp((x*(a*x+b))/(x*(c*x+d)+e), 0.0, 1.0); }
  void main(){ vec3 c = texture2D(tDiffuse, vUv).rgb * exposure; c = aces(c); float l = dot(c, vec3(0.2126, 0.7152, 0.0722)); c = mix(vec3(l), c, sat); c += vec3(warm, warm * 0.4, -warm * 0.6);
    c = lift * vec3(1.0, 0.92, 0.82) + c * (1.0 - lift); vec2 q = vUv - 0.5; c *= 1.0 - 0.22 * dot(q, q) * 2.0; c = pow(clamp(c, 0.0, 1.0), vec3(1.0 / 2.2)); gl_FragColor = vec4(c, 1.0); }`;
function photoTex(ctx, year, o = {}) {
  return ctx.cache('ep01p5:photo:' + year + ':' + JSON.stringify(o), () => {
    const size = o.size || 512; const R = ctx.renderer; const scene = new THREE.Scene();
    const st = stagePhoto(ctx, year, o); scene.add(st.H); st.people.forEach((x) => scene.add(x));
    const sky = sets.sky(ctx, { preset: 'day' }); scene.add(sky); photoLights(scene, P3(st.H.ep01.spots.bed0), P3(st.H.ep01.spots.theoWindow));
    const v = st.view; const cam = new THREE.PerspectiveCamera(v.fov, 1, 0.05, 900); cam.position.copy(P3(v.pos)); cam.lookAt(P3(v.target)); cam.updateMatrixWorld(true);
    const rt = new THREE.WebGLRenderTarget(size, size, { type: THREE.HalfFloatType, samples: 4 }); const rt2 = new THREE.WebGLRenderTarget(size, size, { type: THREE.UnsignedByteType });
    const prev = R.getRenderTarget(); const prevAuto = R.autoClear; const prevCol = R.getClearColor(new THREE.Color()); const prevA = R.getClearAlpha(); const prevSM = R.shadowMap.enabled;
    R.shadowMap.enabled = false; R.autoClear = true; R.setClearColor('#000000', 1); R.setRenderTarget(rt); R.clear(); R.render(scene, cam);
    const q = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.ShaderMaterial({ uniforms: { tDiffuse: { value: rt.texture }, exposure: { value: 1.05 }, warm: { value: 0.05 }, lift: { value: 0.06 }, sat: { value: 0.9 } }, vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }', fragmentShader: PHOTO_FS, depthTest: false, depthWrite: false }));
    q.frustumCulled = false; const qs = new THREE.Scene(); qs.add(q); R.setRenderTarget(rt2); R.render(qs, new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1));
    const px = new Uint8Array(size * size * 4); R.readRenderTargetPixels(rt2, 0, 0, size, size, px);
    R.setRenderTarget(prev); R.autoClear = prevAuto; R.setClearColor(prevCol, prevA); R.shadowMap.enabled = prevSM; rt.dispose(); rt2.dispose(); q.geometry.dispose(); q.material.dispose();
    const c = document.createElement('canvas'); c.width = c.height = size; const g2 = c.getContext('2d'); const id = g2.createImageData(size, size);
    for (let y = 0; y < size; y++) id.data.set(px.subarray((size - 1 - y) * size * 4, (size - y) * size * 4), y * size * 4);
    g2.putImageData(id, 0, 0); const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8; tex.userData.persistent = true;
    return { texture: tex, canvas: c, year };
  });
}
// The phone (1 x 2 studs, black rounded body) with a live screen: draw(g, t, W, H) repaints a 360 x 720 canvas each frame.
function livePhone(ctx, draw) {
  const body = ctx.cache('ep01p5:phoneBody', () => { const P = new sets.Parts(); P.add('black:#141418', new RoundedBoxGeometry(1.0, 2.0, 0.1, 4, 0.12)); P.box('metal:#3a3a44', 0.3, 0.06, 0.02, [0.2, 0.86, -0.06]); return sets.persistTree(P.build(sets.M, { name: 'phoneBody' })); });
  const W = 360, Hh = 720; const c = document.createElement('canvas'); c.width = W; c.height = Hh; const g = c.getContext('2d');
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8; tex.minFilter = THREE.LinearFilter; tex.generateMipmaps = false;
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(0.92, 1.84), new THREE.MeshBasicMaterial({ map: tex, color: new THREE.Color(1.15, 1.15, 1.15), fog: false })); screen.position.z = 0.053;
  const inner = new THREE.Group(); inner.add(body.clone(), screen); inner.scale.setScalar(S); const root = new THREE.Group(); root.name = 'p5Phone'; root.add(inner);
  root.update = (t) => { draw(g, t, W, Hh); tex.needsUpdate = true; }; return root;
}
function phoneChrome(g, W, title = 'Theo', sub = 'just now') {
  g.fillStyle = '#0c0c10'; g.fillRect(0, 0, W, 720); g.textBaseline = 'middle';
  g.fillStyle = '#f4f2f8'; g.font = 'bold 22px "DejaVu Sans", sans-serif'; g.textAlign = 'left'; g.fillText('9:41', 20, 26); g.textAlign = 'right'; g.fillText('100%', W - 20, 26);
  g.fillStyle = '#d9a52c'; g.beginPath(); g.arc(44, 84, 22, 0, Math.PI * 2); g.fill(); g.fillStyle = '#0c0c10'; g.font = 'bold 24px "DejaVu Sans", sans-serif'; g.textAlign = 'center'; g.fillText(title[0], 44, 85);
  g.fillStyle = '#f4f2f8'; g.textAlign = 'left'; g.font = 'bold 26px "DejaVu Sans", sans-serif'; g.fillText(title, 78, 76); g.fillStyle = '#9a98a8'; g.font = '19px "DejaVu Sans", sans-serif'; g.fillText(sub, 78, 102);
  g.fillStyle = '#3a3846'; g.fillRect(W / 2 - 60, 700, 120, 5);
}
// The narrator at 71 on the garden bench (backGarden benchSeatL, facing the house); `hold`: the phone held up in his
// right hand at chest height, screen to his eyes (returns the phone's world pose helpers).
const OLD_SIT = { ...K.POSES.sit, armLx: 34, armLz: -10, armRx: 34, armRz: -10, neckX: -4 };
function oldOnBench(ctx, G, { face = 'content', name = 'heroOld', pose = OLD_SIT, extra = {} } = {}) {
  const A = G.userData.anchors; const old = K.makeCharacter(name, { face, ...extra }); old.position.set(A.benchSeatL[0], A.benchSeatL[1] - 1.5 * S, A.benchSeatL[2]); old.rotation.y = Math.PI;
  if (name === 'heroOldShort') old.position.y += K.seatOffset(old, 1.5);
  K.setPose(old, pose); ctx.add(old); old.updateWorldMatrix(true, true); return old;
}
const HOLD_POSE = { ...K.POSES.sit, armRx: 58, armRz: -16, armLx: 30, armLz: -8, neckX: -16 };
function holdPhone(old, phone, { lift = 0.05, out = 0.07, pose = HOLD_POSE } = {}) {
  K.setPose(old, pose); old.updateMatrixWorld(true); const hand = worldOf(K.handSocket(old, 'R')); const eyes = worldOf(old.getObjectByName('head')).add(new THREE.Vector3(0, 0.03, 0));
  const toE = eyes.clone().sub(hand).normalize(); phone.position.copy(hand).add(new THREE.Vector3(0, lift, 0)).addScaledVector(toE, out); phone.lookAt(eyes); phone.updateMatrixWorld(true);
  return { hand, eyes, center: phone.position.clone() };
}
// The Polaroid date in the s90 pile: Theo's age on each (7, 10, 16, 25, 40) = years 1, 4, 10, 19, 34 after the move.
const PILE_YEARS = [1, 4, 10, 19, 34];

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

  // s78 "light rolled across the lawn," (88.58-89.75) - ground level on the lawn, 1.9 m out from Grandpa's bed, looking
  // out across the dark lawn (family gnomes, three snout mounds) to the front fence and the houses across the way: the
  // FWOOM wall of gold light comes from behind-left (the bed), sweeps in from the left past the lens on "across" (89.13,
  // f5348) and rolls on away over the lawn toward the fence, lighting the blades with sparkles kicked up at its front; the
  // mounds in its path sink as it reaches them. The lens looks 58 deg off the wave's radius so the front crosses the frame
  // left -> right (board screen direction), trucks right with it 5 studs (board 11: at that speed it outruns the wave)
  // + push 12 % (fov). The wall fades within 2.4 m of the lens (no full-frame wash as it passes). The agent board (in the
  // line of sight, seen from behind) is taken out of this shot. (The wave keeps its 8 studs/s; its start is re-timed so
  // the pass lands on the word.)
  light_rolls: {
    build(ctx) {
      const p = ctx.params; const H = nightLot(ctx); removeBoard(H); frontDoor(ctx, { light: 1.6, glow: 1.0 }); theoAsleep(ctx, H);
      const g = grandpaAt(ctx, { lantern: 1 }); ctx.shared.g = g;
      const lan = worldOf(g.getObjectByName('lantern')); const Cn = new THREE.Vector3(lan.x, 0, lan.z);
      const v = 8 * S; const tA = evT(ctx, 'across', 0.55); const dur = ctx.shot.duration; const truck = 5 * S; const r0 = 1.9;
      const u = new THREE.Vector3(-0.45, 0, 0.89).normalize(); const camY = 1.4 * S; /* 1.4 studs (board 0.5): just over the blades, so the lit band on the grass reads */
      let look = u.clone().applyAxisAngle(YAX, 58 * DEG); let right = new THREE.Vector3(-look.z, 0, look.x);
      if (right.dot(u) < 0) { look = u.clone().applyAxisAngle(YAX, -58 * DEG); right = new THREE.Vector3(-look.z, 0, look.x); }   // the source must sit behind-LEFT: the front then sweeps left -> right
      const CA = Cn.clone().addScaledVector(u, r0); CA.y = camY; const C0 = CA.clone().addScaledVector(right, -truck * tA / dur);
      const rA = Math.hypot(CA.x - Cn.x, CA.z - Cn.z); const tW0 = tA - rA / v;
      const tgt = C0.clone().addScaledVector(look, 6 * S); tgt.y = camY + 6 * S * Math.tan(-3 * DEG);
      ctx.camera.set({ pos: C0.toArray(), target: tgt.toArray(), fov: p.fov }).truck(truck); basePush(ctx);
      clearPlants(H, [[C0.x, C0.z, 0.3], [CA.x, CA.z, 0.3], [C0.x + right.x * truck, C0.z + right.z * truck, 0.3]]);
      ctx.shared.rig = sets.magicGlow(ctx, { set: H, skyPreset: C.GALAXY_LOW, skyOpts: { intensity: 1.6 }, hemiIntensity: 0.5, key: { intensity: 0.3 }, lamp: { n: 2 }, window: { n: 0 }, postOpts: { exposure: 0.95, glow: { amount: 0.06 } } });
      ctx.shared.GL = grandpaLantern(ctx, g, { cd: 1.6, levelFn: (t) => fwoomLevelEp(ctx, t) });
      const ang = (w) => Math.atan2(w.z, w.x) / DEG; const aU = ang(u), aL = ang(look); const lo = Math.min(aU, aL) - 30, hi = Math.max(aU, aL) + 30;
      const W = X.lightWave(ctx, { center: Cn, t0: tW0, speed: 8, height: 2.0, width: 1.8, intensity: 1.7, sparkles: 120, sector: [lo, hi], light: 2.2, seed: 's78w' }); ctx.add(W.group); ctx.shared.W = W; nearFade(W.group, 0.7, 2.4);   // softer near the lens: no cream wash after the pass
      const f = CR.moleField(ctx, { center: [CA.x + look.x * 3, CA.z + look.z * 3], size: [22, 22], res: 72, seed: 's78f', heads: 'snout' }); ctx.add(f.group);
      for (const [fw, lat, sc] of [[2.2, -0.35, 1.0], [3.4, 0.45, 1.1], [4.6, -0.2, 1.0]]) { const q = CA.clone().addScaledVector(look, fw).addScaledVector(right, lat); const k = f.add({ at: [q.x, q.z], scale: sc, face: [Cn.x, Cn.z] }); f.eyes(k, -5, null); f.sink(k, tW0 + Math.hypot(q.x - Cn.x, q.z - Cn.z) / v, 0.5); }
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
      ctx.shared.fx = sparks(ctx, up(GP, 4.6, -1.6, 2.2), [3.6, 2.4, 2.2], 8, 's81', { px: [40, 72] });   // over the bed and the window, clear of the hero's head
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
      const p = ctx.params; const H = dawnLot(ctx); hideBoard(H); const f0 = H.ep01.gnomes.family.lawn0; if (f0) f0.visible = false;   // it stands between the lens and the door here
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
      // the pair is backlit by the low sun (the lens looks toward the street): a face key on the kneeling hero keeps his
      // skin the warm salmon of s84 (without it his face goes brown against Theo's)
      { K.setPose(hero, { ...K.POSES.kneel, bodyX: 20 }); hero.updateWorldMatrix(true, true); const hh = worldOf(hero.getObjectByName('head')); const kl = warmKey(ctx, hh.toArray(), { cd: 1.0, d: 0.75, color: '#ffd2b0', side: 20, el: 25 });
        ctx.shared.heroKey = { light: kl, off: kl.position.clone().sub(hh) }; }   // follows his head as he leans in (update)
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
      if (s.heroKey && s.heroKey.light && s.heroKey.light.position) { s.hero.updateMatrixWorld(true); s.heroKey.light.position.copy(worldOf(s.hero.getObjectByName('head'))).add(s.heroKey.off); }
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
      // orbit 34 deg off his facing axis (was 24): Theo then stands clear of the hat, so his waving arm reads
      const toT = P3(T_STEP).sub(P3(GP)).setY(0).normalize(); const cdir = toT.clone().negate().applyAxisAngle(YAX, 34 * DEG);
      const cam = P3(eyes).addScaledVector(cdir, c.dist_studs * S); cam.y = BED[1] + c.height_studs * S;
      const th = worldOf(theo.getObjectByName('head')); const aim = P3(eyes).lerp(th, 0.56); const hd = Math.hypot(aim.x - cam.x, aim.z - cam.z); aim.y = cam.y + hd * Math.tan(c.pitch_deg * DEG) + 0.08;
      ctx.camera.set({ pos: cam.toArray(), target: aim.toArray(), fov: p.fov }); basePush(ctx);
      clearPlants(H, [[cam.x, cam.z, 0.32], [lerp(cam.x, eyes.x, 0.5), lerp(cam.z, eyes.z, 0.5), 0.2]]);
      K.setGnomeHead(g, 10, 4, 0); g.updateWorldMatrix(true, true);
      { const B = camBasis(ctx); C.gazeAt(g, B.pos.clone().addScaledVector(B.right, 0.55).add(new THREE.Vector3(0, 0.18, 0))); }   // eyes rolled to screen-right, toward Theo
      ctx.shared.rig = dawnLight(ctx, H); warmKey(ctx, eyes.toArray(), { cd: 0.7, d: 0.6, color: '#ffd8c0' });
      warmKey(ctx, th.toArray(), { cd: 1.1, d: 0.9, color: '#ffd2b0', side: 25, el: 25 });   // Theo is backlit by the low sun: keep his skin s83/s87's salmon
      const tB = evT(ctx, 'blinked', 1.3); ctx.shared.tB = tB; const T = X.blinkTik(ctx, g, { t0: tB, frames: 2 }); ctx.add(T.group); ctx.shared.T = T;
    },
    update(ctx, t) {
      const s = ctx.shared; K.setGnomeLids(s.g, K.gnomeBlink(t, [s.tB], { frames: 2 })); s.T.update(t); K.gnomeIdle(s.g, t, { seed: 's86', amp: 0.2 });
      K.setPose(s.theo, { ...THEO_BASE, armRz: 128 + 11 * Math.sin(2 * Math.PI * 2 * t), armRx: 14, neckX: -4, neckZ: -3 });
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
      // our street at sunrise, the truck pulling away from our kerb (ENGINE 100.37: 4 studs/s^2 to 6 studs/s). Our lawn
      // carries its six family gnomes of every heroLot shot (s06 layout, bedFront0 shifted to the path) instead of the
      // street's two, all facing the house; next door's plastic gnomes (they face the street) are left out of this shot so
      // every gnome in it faces its house.
      const T = SE.ep01Street(ctx, { tod: 'dawn', lanterns: 0.5, truck: 'leaving', skip: ['A4.bed0', 'A4.lawn0', 'A4.lawn3', 'A3.lawn2', 'A3.lawn3'], truckOpts: { t0: epT(ctx, 100.37), accel: 4, vmax: 6, balconyBox: false, dome: false } }); ctx.add(T); ctx.shared.T = T;
      const POINTED = [0, 1, 2, 3, 4, 5, 7];
      ['bedFront0', 'lawn0', 'lawn1', 'lawn2', 'lawn3', 'bedFront1'].forEach((n, k) => {
        const s0 = sets.slot(T.ep01.set, 'A3.' + n); if (!s0) return; const s = { ...s0, pos: s0.pos.slice() }; if (n === 'bedFront0') s.pos[0] += 1.5 * S;
        const f = K.makeFamilyGnome(POINTED[(2 + k) % POINTED.length], { lantern: 0.5, lod: 'mid' }); sets.place(f, s); ctx.add(f); ctx.add(sets.contactShadow(ctx, { pos: s.pos, radius: 0.26, opacity: 0.4 }));
      });
      const gp = T.ep01.grandpa; const gpos = worldOf(gp);
      const theo = theoWithWhale('theo', { face: 'content' }); theo.position.set(gpos.x - 0.85, 0, gpos.z + 0.6); theo.rotation.y = 0.6; K.setPose(theo, { ...THEO_BASE, armRz: 130 }); ctx.add(theo); ctx.shared.theo = theo;   // at Grandpa's street-side left: both read from the truck
      // the lens stands in the cargo bay near the open back on the road side (povCamera), looking back out of the opening
      // toward our lawn (yaw 60): the house-side door rail frames the left, the roof edge the top, the bay floor the bottom;
      // as the truck pulls away our lawn recedes with every gnome's back to us (each faces its house), Theo small beside
      // Grandpa. h 9.5 studs (board 6: from 6 the picket fence hides the lawn gnomes), fov 60 (board 70: gnomes too small).
      const pov = T.ep01.truck.ep01.povCamera({ height: 9.5, back: 2.0, side: 3.2, pitch: -14, fov: 60, yaw: 60 });
      ctx.camera.set({ pos: pov.pos, target: pov.target, fov: pov.fov }).handheld({ rot: 0.3, pos: 0.004, freq: 1.1, seed: 88 }); basePush(ctx, { mode: 'dolly' });
      // Grandpa alone has his head turned round after the truck (s89 opens on that look): tiny here, the reveal is s89's
      { const cm = pov.pos(ctx.shot.duration * 0.7, new THREE.Vector3()); const d = cm.sub(gpos).setY(0).normalize(); const ry = gp.rotation.y;
        const lx = d.x * Math.cos(ry) - d.z * Math.sin(ry), lz = d.x * Math.sin(ry) + d.z * Math.cos(ry); K.setGnomeHead(gp, Math.atan2(lx, lz) / DEG, 2, 0); }
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
      const theo = theoWithWhale('theoSocks', { face: (p.cast[1] && p.cast[1].face) || 'content' }); const tp = [GP[0] - 0.75, 0, GP[2] + 0.62]; theo.position.set(...tp); theo.rotation.y = yawTo(tp, cam.toArray()) - 0.3; K.setPose(theo, { ...THEO_BASE, armRz: 125 }); ctx.add(theo); ctx.shared.theo = theo;   // beside him (he has stepped round to wave the truck off)
      const tgt = P3(GP).lerp(P3(tp), 0.4); tgt.y = 0.74;
      ctx.camera.set({ pos: v.pos, target: tgt.toArray(), fov: 11 }); basePush(ctx);   // fov 11 (board 25): a tele CU on Grandpa, Theo at the left edge beside him
      ctx.shared.yawAt = Math.atan2(-gdir.x, -gdir.z) / DEG;   // head yaw that points his face at the lens (the gnome faces -Z)
      ctx.camera.custom((st, t) => { st.px[0] += 2.2 * Math.sin(t * 37.0) + 0.8 * Math.sin(t * 71.3 + 1.1); st.px[1] += 2.0 * Math.sin(t * 43.7 + 0.4) + 0.9 * Math.sin(t * 89.1); });
      ctx.shared.rig = dawnLight(ctx, H, { sun: { az: 150, el: 10 } });
      { K.setPose(theo, { ...THEO_BASE, armRz: 125 }); theo.updateWorldMatrix(true, true); const th = worldOf(theo.getObjectByName('head')); warmKey(ctx, th.toArray(), { cd: 1.4, d: 1.1, color: '#ffd2b0', side: 20, el: 25 }); }
      warmKey(ctx, C.eyesOf(g).toArray(), { cd: 0.7, d: 0.7, color: '#ffd2b0', side: 15, el: 30 });   // his turned face, lit for the look at the lens
      ctx.shared.tE = evT(ctx, 0, 0.45);
    },
    update(ctx, t) { const s = ctx.shared; K.setGnomeHead(s.g, K.gnomeHeadTurn(t, s.tE, 0.8, s.yawAt, 0), 2, 0); K.gnomeIdle(s.g, t, { seed: 's89', amp: 0.2 }); K.setPose(s.theo, { ...THEO_BASE, armRz: 125 + 12 * Math.sin(2 * Math.PI * 1.8 * t) }); },
  },
  // s90 "Every spring for 60 years," (103.43-104.98) - top-down on the teak garden table at dusk (backGarden tableTop):
  // the first spring's Polaroid lies on the table; the next ones drop one by one onto the pile on "spring" / "sixty" /
  // "years" / 104.75 (f6230, 6254, 6268, 6285), each the same gnome under the same window with Theo beside him, older in
  // each (ages 7 -> 10, 16, 25, 40). Mug and reading glasses beside the pile. Push 22 % (fov) + roll -2 deg. The photos are
  // rendered once per worker from the 3D set in spring daylight (fx_photo_look on the prints only).
  polaroid_stack: {
    quality: { shadows: 'pcfsoft' },
    build(ctx) {
      const p = ctx.params; const G = SE.backGarden(ctx, { tod: 'dusk' }); ctx.add(G); const A = G.userData.anchors;
      const t0s = [-1, ...[0, 1, 2, 3].map((i) => evT(ctx, i, 0.4 + 0.3 * i) - 0.26)];   // land on the event frames (0.28 s fall)
      const cards = PILE_YEARS.map((y) => X.polaroid(ctx, { photo: photoTex(ctx, y), date: X.photoDate(y), seed: y, curl: 0.1 }));
      const D = X.polaroidDrop(ctx, cards, { at: A.pile, t0s, dur: 0.28, height: 0.45, seed: 's90' }); ctx.add(D); ctx.shared.D = D;
      const v = G.userData.views.tableTop; ctx.camera.set({ pos: up(A.pile, 11.5, -0.3, 0.01), target: up(A.pile, 0, -0.3), fov: p.fov }); basePush(ctx); paramRoll(ctx); void v;
      ctx.shared.rig = G.ep01.light(ctx);
      ctx.shared.fx = sparks(ctx, up(A.pile, 2.0), [1.6, 0.6, 1.4], 4, 's90', { colors: ['#ffe2c4', '#fff0dc'], px: [36, 60] });
    },
    update(ctx, t) { ctx.shared.D.update(t); ctx.shared.fx.update(t); },
  },

  // s91 "Theo's sent me a photo." (104.98-106.23) - ECU of the phone screen -> pull back x2.5 (outExpo, 0.9 s) + a linear
  // 6 % push after: the phone is in an old, freckled hand with a mustard cardigan cuff (the narrator at 71, first old
  // image), over his right shoulder on the garden bench at dusk. On "sent" (105.35, f6321) the ping banner drops in and
  // Theo's new photo slides up: the gnome mossy and faded under the window, Theo at 66 with a thumbs-up, his granddaughter
  // waving from the window.
  phone_reveal: {
    quality: { shadows: 'pcfsoft' },
    build(ctx) {
      const p = ctx.params; const G = SE.backGarden(ctx, { tod: 'dusk' }); ctx.add(G);
      const old = oldOnBench(ctx, G, { face: 'content', pose: HOLD_POSE });
      const newP = photoTex(ctx, 60, { blink: 0.55, girl: true, thumbs: true }).canvas, oldP = photoTex(ctx, 59, {}).canvas;
      const tS = evT(ctx, 'sent', 0.367); ctx.shared.tS = tS;
      const ph = livePhone(ctx, (g, t, W) => {
        phoneChrome(g, W, 'Theo', t < tS ? 'last spring' : 'just now'); const u = outCubic((t - tS) / 0.3); const y1 = lerp(720, 150, u), y0 = 150 - 560 * u;
        g.drawImage(oldP, 12, y0, W - 24, W - 24); g.fillStyle = '#c8c6d4'; g.font = '20px "DejaVu Sans", sans-serif'; g.textAlign = 'left'; g.fillText('Grandpa, year 59', 18, y0 + W + 4);
        if (t >= tS) { g.drawImage(newP, 12, y1, W - 24, W - 24); g.fillStyle = '#f4f2f8'; g.font = 'bold 22px "DejaVu Sans", sans-serif'; g.fillText('60 springs! ♥', 18, y1 + W + 4);
          const b = outCubic((t - tS) / 0.15); g.fillStyle = 'rgba(58,56,70,0.95)'; g.fillRect(14, -70 + 128 * b, W - 28, 58); g.fillStyle = '#f4f2f8'; g.font = 'bold 20px "DejaVu Sans", sans-serif'; g.fillText('Theo sent a photo', 30, -41 + 128 * b); }
      });
      ctx.add(ph); const hp = holdPhone(old, ph); ctx.shared.ph = ph;
      // over his right shoulder (his right = +X here, the bench faces -Z): the lens looks past his ear at the screen
      const toE = hp.eyes.clone().sub(hp.center); toE.y = 0; toE.normalize(); const cdir = toE.applyAxisAngle(YAX, 38 * DEG); if (cdir.x > 0) cdir.applyAxisAngle(YAX, -76 * DEG);   // past his left cheek (the phone arm is his right), 38 deg off the screen axis
      const cam = hp.center.clone().addScaledVector(cdir, 0.85).add(new THREE.Vector3(0, 0.15, 0));
      ctx.camera.set({ pos: cam.toArray(), target: hp.center.toArray(), fov: p.fov });
      ctx.camera.custom((st, t) => { st.scale *= t < 0.9 ? lerp(2.5, 1, outExpo(t / 0.9)) : 1 + 0.06 * clamp01((t - 0.9) / (ctx.shot.duration - 0.9)); });
      ctx.shared.rig = G.ep01.light(ctx); warmKey(ctx, hp.hand.toArray(), { cd: 0.6, d: 0.6, color: '#ffd0a0' });
    },
    update(ctx, t) { ctx.shared.ph.update(t); },
  },

  // s92 "Grandpa, same flowerbed, same window," (106.23-108.27) - over his shoulder, top-down onto the phone: his thumb
  // swipes on "same" (106.75, f6405) and "same" (107.65, f6459), each new photo sliding in from the right in 8 frames:
  // "Grandpa" (close, mossy), "same flowerbed" (another year's tulips), "same window" (another year's curtains, Theo grey
  // at the window). h 4.6, d 1.4, yaw 200, pitch -35, fov 45, push 19 %.
  phone_swipes: {
    quality: { shadows: 'pcfsoft' },
    build(ctx) {
      const p = ctx.params, c = p.camera; const G = SE.backGarden(ctx, { tod: 'dusk' }); ctx.add(G);
      const old = oldOnBench(ctx, G, { face: 'content', pose: HOLD_POSE });
      const pics = [photoTex(ctx, 52, { view: 'close' }).canvas, photoTex(ctx, 33, { view: 'bed', theo: 'window' }).canvas, photoTex(ctx, 45, { theo: 'window' }).canvas];
      const caps = ['Grandpa', 'spring 33', 'spring 45'];
      const ts = [evT(ctx, 0, 0.517), evT(ctx, 1, 1.417)]; ctx.shared.ts = ts;
      const ph = livePhone(ctx, (g, t, W) => {
        phoneChrome(g, W, 'Theo', 'Photos'); let k = 0; for (const t0 of ts) { const u = (t - t0) * 60 / 8; k += u >= 1 ? 1 : u > 0 ? outCubic(u) : 0; }
        pics.forEach((pc, i) => { const x = 12 + (i - k) * W; if (x > W || x < -W) return; g.drawImage(pc, x, 150, W - 24, W - 24); g.fillStyle = '#c8c6d4'; g.font = '20px "DejaVu Sans", sans-serif'; g.textAlign = 'left'; g.fillText(caps[i], x + 6, 150 + W + 4); });
        for (let i = 0; i < 3; i++) { g.fillStyle = Math.round(k) === i ? '#f4f2f8' : '#5a5868'; g.beginPath(); g.arc(W / 2 - 24 + 24 * i, 640, 6, 0, Math.PI * 2); g.fill(); }
      });
      // the hand holds the phone from below (phone raised 0.23 m over the hand, tilted to his eyes), so from over his left
      // shoulder the forearm block stays under the screen instead of crossing it (it hid half the photos)
      const LOW = { ...HOLD_POSE, armRx: 40, armRz: -18, neckX: -24 }; K.setPose(old, LOW);
      ctx.add(ph); const hp = holdPhone(old, ph, { pose: LOW, lift: 0.23, out: 0.13 }); ctx.shared.ph = ph; ctx.shared.old = old;
      const back = new THREE.Vector3(0, 0, 1).applyAxisAngle(YAX, (c.yaw_deg - 180) * DEG); const cdir = back.clone().multiplyScalar(Math.cos(-c.pitch_deg * DEG)); cdir.y = Math.sin(-c.pitch_deg * DEG); cdir.normalize();
      // over his left shoulder (the phone is in his right hand: from the right the arm hides it), looking down past his cheek
      const toE = hp.eyes.clone().sub(hp.center); toE.y = 0; toE.normalize(); const sd = toE.clone().applyAxisAngle(YAX, 56 * DEG); if (sd.x > 0) sd.applyAxisAngle(YAX, -112 * DEG);
      const cam = hp.center.clone().addScaledVector(sd, 0.92).add(new THREE.Vector3(0, 0.55, 0)); void cdir;
      ctx.camera.set({ pos: cam.toArray(), target: hp.center.toArray(), fov: p.fov }); basePush(ctx);
      ctx.shared.rig = G.ep01.light(ctx); warmKey(ctx, hp.hand.toArray(), { cd: 0.6, d: 0.6, color: '#ffd0a0' });
      ctx.shared.p0 = ph.position.clone();
    },
    update(ctx, t) { const s = ctx.shared; s.ph.update(t); let d = 0; for (const t0 of s.ts) { const u = (t - t0) * 60 / 8; if (u > -1 && u < 2) d += 0.006 * Math.sin(Math.PI * clamp01((u + 1) / 3)); } s.ph.position.copy(s.p0).add(new THREE.Vector3(0, -d, 0)); },
  },

  // s93 "always mid-blink." (108.27-109.15) - the newest photo fills the frame: the spring lot 60 years on, rendered live
  // in full resolution with the print look (day grade, lifted warm blacks): Grandpa mossy and faded, caught mid-blink (lids
  // 0.55), looking back at the lens; Theo at 66 (bald, grey beard) giving a thumbs-up beside him; Theo's granddaughter in
  // whale pyjamas waving from the window above. A white print border pushes out of frame with the 25 % push. Frozen (a photo).
  photo_midblink: {
    quality: { shadows: 'pcfsoft' },
    build(ctx) {
      const p = ctx.params; const st = stagePhoto(ctx, 60, { blink: 0.55, girl: true, thumbs: true }); ctx.add(st.H); st.people.forEach((x) => ctx.add(x));
      const bp = P3(st.H.ep01.spots.bed0); const pos = new THREE.Vector3(bp.x - 0.45, 0.95, bp.z + 3.7), tgt = new THREE.Vector3(bp.x - 0.42, 1.12, bp.z); ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: p.fov }); basePush(ctx);
      SE.heroLight(ctx, st.H, { tod: 'day', postOpts: { exposure: 1.1, grade: { temperature: 8, saturation: 0.9, outBlack: '#2a2018', outWhite: '#f4ecdc' } } });
      // the print border (camera-locked card at t = 0; the fov push carries it out of frame like a push into the print)
      const B = camBasis(ctx); const d = 0.6, hh = 2 * d * Math.tan((p.fov / 2) * DEG), ww = hh * 9 / 16;
      const cv = document.createElement('canvas'); cv.width = 540; cv.height = 960; const g = cv.getContext('2d'); g.fillStyle = '#f4f0e6'; g.fillRect(0, 0, 540, 960); g.clearRect(16, 16, 508, 860);
      g.fillStyle = '#22307a'; g.globalAlpha = 0.85; g.font = 'italic 600 40px "DejaVu Serif", serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(X.photoDate(60), 270, 918);
      const bt = new THREE.CanvasTexture(cv); bt.colorSpace = THREE.SRGBColorSpace;
      const card = new THREE.Mesh(new THREE.PlaneGeometry(ww, hh), new THREE.MeshBasicMaterial({ map: bt, transparent: true, depthTest: false, depthWrite: false, fog: false }));
      card.position.copy(B.pos).addScaledVector(B.fwd, d); card.quaternion.copy(ctx.cam.quaternion); card.renderOrder = 60; ctx.add(card);
    },
    update() {},
  },

  // s94 "I'm 71," (109.15-109.97) - CU of the narrator at 71 on the garden bench (grey hair and moustache, mustard
  // cardigan, olive fishing hat, freckles), the phone lowered in his hand, content; warm side sun. Base push 10 % +
  // punch-in x1.5 in 0.5 s from "seventy" (109.38) + roll 10 deg over the shot. h 3.5 (his seated eye line), d 2.6, yaw -15.
  old_reveal: {
    quality: { shadows: 'pcfsoft' },
    build(ctx) {
      const p = ctx.params, c = p.camera; const G = SE.backGarden(ctx, { tod: 'dusk' }); ctx.add(G);
      const old = oldOnBench(ctx, G, { face: (p.cast[0] && p.cast[0].face) || 'content', pose: { ...OLD_SIT, armRx: 40, neckX: 2 } });
      const head = worldOf(old.getObjectByName('head'));
      boardCam(ctx, [head.x, 0, head.z], { ref: [0, 0, -1], yaw: c.yaw_deg, dist: c.dist_studs, h: head.y / S, pitch: 0, fov: p.fov, aimY: head.y + 0.03 });
      const m = c.move; ctx.camera.push(m.base_push ?? 0.1); const tP = epT(ctx, 109.383);
      ctx.camera.custom((st, t) => { st.scale *= 1 + ((m.x ?? 1.5) - 1) * clamp01((t - tP) / (m.dur ?? 0.5)); }); paramRoll(ctx);
      ctx.shared.rig = G.ep01.light(ctx); warmKey(ctx, head.toArray(), { cd: 0.9, d: 1.0, color: '#ffc896' });
      ctx.shared.old = old;
    },
    update(ctx, t) { K.setPose(ctx.shared.old, { ...OLD_SIT, armRx: 40, neckX: 2, ...K.breath(t) }); },
  },

  // s95 "and my granddaughter says I'm getting" (109.97-111.30) / s96 "shorter." (111.30-111.78) - the s06 composition at
  // dusk (backGarden benchMS = the s06 numbers: h 3.6, d 7.5, yaw -15, pitch -4, push 18 %): the narrator on the bench,
  // content; his granddaughter beside him, hands on hips (arms 30 out), frowning at him (sideGlance). s96 is the jump cut:
  // he is smaller (heroOldShort x0.85, sleeves over his hands), feet dangling, face wonder.
  bench_granddaughter: {
    quality: { shadows: 'pcfsoft' },
    build(ctx) {
      const p = ctx.params; const short = p.phase === 'short'; const G = SE.backGarden(ctx, { tod: 'dusk' }); ctx.add(G); const A = G.userData.anchors;
      const face = (p.cast[0] && p.cast[0].face) || (short ? 'wonder' : 'content');
      const old = oldOnBench(ctx, G, short ? { face, name: 'heroOldShort', pose: { ...K.CAST_POSES.sitDangle, neckX: 6, neckY: -14 } } : { face, pose: { ...OLD_SIT, neckY: -12 } });
      const gd = K.makeCharacter('granddaughter', { face: 'sideGlance' }); const gp = [A.benchSeatL[0] - 0.64, 0, A.benchSeatL[2] - 0.32]; gd.position.set(...gp); const vb = G.userData.views.benchMS; gd.rotation.y = lerp(yawTo(gp, A.benchSeatL), yawTo(gp, vb.pos), 0.45);
      K.setPose(gd, { armLz: 30, armRz: 30, armLx: -10, armRx: -10, neckY: 10 }); ctx.add(gd); ctx.add(sets.contactShadow(ctx, { pos: [gp[0], 0.005, gp[2]], radius: 0.36, opacity: 0.35 }));
      const ph = livePhone(ctx, (g, t, W) => { phoneChrome(g, W, 'Theo', 'just now'); }); ph.position.set(A.benchSeatL[0] - 0.42, A.benchSeatL[1] + 0.02, A.benchSeatL[2] + 0.05); ph.rotation.set(-Math.PI / 2, 0, 0.4); ph.update(0); ctx.add(ph);
      { const vb = G.userData.views.benchMS; const tg = P3(vb.target).add(new THREE.Vector3(-0.22, 0, 0)); ctx.camera.set({ ...vb, target: tg.toArray() }); } basePush(ctx);   // aim 0.22 m toward her: both in frame
      ctx.shared.rig = G.ep01.light(ctx); const head = worldOf(old.getObjectByName('head')); warmKey(ctx, head.toArray(), { cd: 1.2, d: 1.4, color: '#ffc896' });
      Object.assign(ctx.shared, { old, short, face });
    },
    update(ctx, t) { const s = ctx.shared; if (!s.short) K.setPose(s.old, { ...OLD_SIT, neckY: -12, ...K.breath(t) }); },
  },

  // s97 "I've already picked my window." (111.78-113.30) - the loop shot. Reverse angle from the granddaughter's lit window
  // at night: he lowers himself into the striped deck chair facing it (12 frames), facing the lens, the TF moon behind his
  // hat (az -16, el 32 of the view); a long linear dolly push (x1.8 at the target, 2.24 -> 0.96 m from his face) ends on an
  // ECU of his face at frame 0's gnome-face position and size (eyes centre at 54 % / 56.5 % of the frame, head ~60 % of
  // the width) with frame 0's -15 deg roll; on "window" (112.69, f6761) the dandelion clock beside the chair releases its
  // seeds, which drift up across him. Warm window spill 2.8 cd from behind the lens, galaxy sky, night grade (frame 0).
  final_window: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const G = SE.backGarden(ctx, { tod: 'night' }); ctx.add(G); const A = G.userData.anchors;
      const old = K.makeCharacter('heroOld', { face: (p.cast[0] && p.cast[0].face) || 'content' }); old.rotation.y = Math.PI; ctx.add(old); ctx.shared.old = old;
      const SITP = { ...K.POSES.sit, bodyX: -14, armLx: 26, armRx: 26, armLz: -8, armRz: -8, neckX: 6 }; ctx.shared.SITP = SITP;
      const seatPos = new THREE.Vector3(A.chairSeat[0], A.chairSeat[1] - 1.75 * S, A.chairSeat[2]); const standPos = seatPos.clone().add(new THREE.Vector3(0, 1.75 * S - 0.02, -0.28)); standPos.y = 0;
      Object.assign(ctx.shared, { seatPos, standPos, tS0: 0.05 });
      old.position.copy(seatPos); K.setPose(old, SITP); old.updateMatrixWorld(true); const face = worldOf(old.getObjectByName('head')).add(new THREE.Vector3(0, 0.02, 0));
      // start: 7 studs out at h 3.4, looking at him (pitch ~ +2); end: 0.96 m from the face, framed and rolled like frame 0
      const camY = c.height_studs * S; const P0 = new THREE.Vector3(face.x, camY, face.z - c.dist_studs * S); const T0 = face.clone();
      const P1 = new THREE.Vector3(face.x + 0.01, face.y + 0.02, face.z - 1.02); const dir = face.clone().sub(P1).normalize(); const rt = new THREE.Vector3().crossVectors(dir, YAX).normalize(); const upv = new THREE.Vector3().crossVectors(rt, dir);
      const r = -15 * DEG; const ox = 0.031 * 2 * 1.02 * Math.tan(31 * DEG) * 9 / 16 * 2, oy = -0.058 * 2 * 1.02 * Math.tan(31 * DEG) * 2;   // face offset in the frame (m at the face)
      const vx = ox * Math.cos(r) - oy * Math.sin(r), vy = ox * Math.sin(r) + oy * Math.cos(r);
      const T1 = face.clone().addScaledVector(rt, -vx).addScaledVector(upv, -vy);
      const L = (a, b, k) => a.clone().lerp(b, k); const dur = ctx.shot.duration;
      ctx.camera.set({ pos: (t, o) => (o || new THREE.Vector3()).copy(L(P0, P1, clamp01(t / dur))), target: (t, o) => (o || new THREE.Vector3()).copy(L(T0, T1, clamp01(t / dur))), fov: p.fov, roll: (t) => -15 * clamp01(t / dur) });
      const camYaw = Math.atan2(T0.x - P0.x, -(T0.z - P0.z)) / DEG;
      ctx.shared.rig = G.ep01.light(ctx, { tod: 'night', windowCd: 2.8, moon: { az: camYaw - 16, el: 32, size: 8, style: 'tf' }, preset: { skyPreset: C.GALAXY, skyOpts: { intensity: 1.5 }, postOpts: sets.postPreset('night', {}) } });
      // the frame-0 face key: warm spill from behind the lens, upper left of the end framing (s01: 2.8 cd at the lens)
      ctx.add(ctx.lights.point({ color: '#ffc08a', intensity: 2.8, pos: P1.clone().addScaledVector(rt, -0.25).add(new THREE.Vector3(0, 0.3, 0)).addScaledVector(dir, 0.15).toArray(), decay: 2 }));
      coolRim(ctx, face.toArray(), { intensity: 0.7 });
      // the dandelion clock: its seed head goes on "window", the seeds puff and drift up across him
      const tW = evT(ctx, 'window', 0.9); ctx.shared.tW = tW; const rel = G.ep01.release; const seedsMesh = []; if (rel) rel.traverse((m) => { if (m.isMesh && /tulip:#f6f2ea|plastic:#efeae0/.test(m.name)) seedsMesh.push(m); }); ctx.shared.seedsMesh = seedsMesh;
      const relTop = P3(A.release); ctx.shared.puff = sets.burst(ctx, { pos: relTop.toArray(), t0: tW, dur: 0.5, count: 0, puff: 14, puffColor: '#f4f0ea', spread: 0.35, ring: false, core: false, gravity: 0.15, seed: 's97puff' }); ctx.add(ctx.shared.puff);
      const r2 = makeRng(hash32('s97seeds')); const seedMat = C.addSpriteMat(ctx.tex.sparkle({ points: 6, sharpness: 10, core: 0.7 }), '#fff6ee', 1.6); const seeds = [];
      for (let i = 0; i < 14; i++) { const sp = C.pxSprite(seedMat.clone(), 0); sp.renderOrder = 20; sp.userData.d = { v: new THREE.Vector3((face.x - relTop.x) * (0.25 + 0.5 * r2()) + (r2() - 0.5) * 0.3, 0.25 + 0.35 * r2(), (face.z - relTop.z) * 0.3 * r2() - 0.15 * r2()), ph: r2() * 6, px: 14 + 12 * r2() }; ctx.add(sp); seeds.push(sp); }
      Object.assign(ctx.shared, { seeds, relTop });
      ctx.shared.fx = sparks(ctx, face.clone().add(new THREE.Vector3(0, 0.15, -0.6)), [1.4, 1.0, 1.0], 9, 's97', { px: [40, 76] });
    },
    update(ctx, t) {
      const s = ctx.shared; const u = outQuad((t - s.tS0) / (12 / 60)); const old = s.old;
      old.position.copy(s.standPos).lerp(s.seatPos, u); K.setPose(old, K.mixPose({ neckX: 4, armLx: 10, armRx: 10 }, s.SITP, u));
      for (const m of s.seedsMesh) m.visible = t < s.tW;
      for (const sp of s.seeds) { const d = sp.userData.d; const a = t - s.tW; sp.visible = a > 0; if (!sp.visible) continue; const k = 1 - Math.exp(-a * 2.2);
        sp.position.copy(s.relTop).addScaledVector(d.v, k * 1.6).add(new THREE.Vector3(0.03 * Math.sin(t * 3 + d.ph), 0.1 * a, 0)); sp.userData.px = d.px * (0.8 + 0.2 * Math.sin(t * 5 + d.ph)); sp.material.opacity = Math.min(1, a * 6) * 0.9; }
      s.puff.update(t); s.fx.update(t);
    },
  },
};
