// EP01 full episode, PART 3 (s42-s57, 46.30-65.43 s): the reframe and the attempt: "Gnomes aren't decorations / They're the
// fence", Theo, the what-if, the truck clock, the plastic gnome, GULP, the mounds close in, the hero runs back and stands guard.
// Shot list and every decision (camera numbers, cast and faces, light/grade, events with frames, SFX, assets) are in
// episodes/ep01/timeline.json (params of each shot) and episodes/ep01/board.md; new assets are specified in episodes/ep01/ASSETS.md.
// Builders are pure functions of shot time t (engine/README.md determinism rules): no state between frames, no
// Math.random / Date; seeded RNGs only.
//
// Sets: our front garden is sets_ep01.heroLot (lot A1 at x = 0; gate (0, -6.4); door (0, 0.32, -13.22); Grandpa's bed0
// under Theo's window at (-2.67, 0.112, -12.67), window glass centre (-2.41, 1.63, -13.31); the brick edging along
// z -11.92; the truck at the kerb, its open back at x -2.56 facing +X, the ramp running down to x 0 along z -2.53).
// The two street views (s42, s43) use sets_ep01.ep01Street (our lot = A3 at x = 5.76, next door A4 with the plastics).
// Continuity kept here (board.md section 5, part2 NOTES): night; SOLD on the board; the gate open; the truck at the kerb,
// back open, cargo dome light on; the front door open with the warm hall light (since s28); Grandpa in the hero's arms
// with his lantern lit (level 1, flicker) and its 5-stud ring; the family / street lanterns lit since the s40 cascade
// (2-stud pools), next door's plastics dark; bed0 = the empty soil ring until the plastic gnome is planted (s50) and
// swallowed (s51), then the hole with the $4.99 sticker; Theo's window lit (star nightlight) except the s46 what-if;
// hero = heroBarefoot (mustard hoodie, bare feet), Theo = theo (star pyjamas, whale, "6" badge).
// Screen direction (board 5): s46 the step toward the truck goes left -> right; s56 the run back goes right -> left.
import * as THREE from 'three';
import * as sets from '../../kit/sets.js';
import * as K from '../../kit/chars.js';
import * as CR from '../../kit/creatures.js';
import * as SE from '../../kit/sets_ep01.js';
import * as I from '../../kit/interiors.js';
import * as X from '../../kit/fx_ep01.js';
import { doorTex } from '../../kit/kitlib.js';
import { springStep } from '../../core/anim.js';
import { makeRng, hash32 } from '../../core/random.js';
import * as C from './common.js';

const S = C.S, DEG = C.DEG, V3 = C.V3, clamp01 = C.clamp01, smooth = C.smooth, outQuad = C.outQuad;
const lerp = (a, b, k) => a + (b - a) * k;
const YAX = new THREE.Vector3(0, 1, 0);
const up = (p, dy = 0, dx = 0, dz = 0) => [p[0] + dx * S, p[1] + dy * S, p[2] + dz * S];
const P3 = (p) => (p && p.isVector3 ? p.clone() : new THREE.Vector3(p[0], p[1], p[2]));   // array or Vector3
const SPK = (o = {}) => ({ ...C.SPARK, ...o });

// ------------------------------------------------------------------ staging constants (heroLot world metres)
const BED = [-2.669, 0.112, -12.672];       // bed0 (raised soil top 0.112)
const WIN = [-2.413, 1.632, -13.312];       // Theo's window, outer glass centre
const LOT_DOOR = [0, 0.32, -13.216];
const ROOM_FLOOR = 0.32;                    // the bungalow floor (= the porch deck)
const HOLD_OFF = [0, 0.1, 1.12];            // part2: the hugged gnome in the hero's hips frame (studs)
const HUG = { armLx: 58, armRx: 58, armLz: -36, armRz: -36, neckX: -8 };   // part2: both arms round the gnome's belly
const CRADLE = { armLx: 52, armRx: 52, armLz: -40, armRz: -40, neckX: -30 }; // s47: forearms round his belly, tipped back
const TUCK_OFF = [1.38, 0.62, 0.62];        // Grandpa tucked under the hero's LEFT arm (hips frame, studs)
const TUCK_ARM = { armLx: 30, armLz: 4 };   // the left arm pressing him to the hip
const STREET_HERO = [5.76, 0, -8.6];        // part2: the hero on our path in ep01Street (lot A3)
const CU_GRADE = { grade: { temperature: -6, tint: 6 } };   // close-ups keep warm skin / glaze inside the cool night (approved s05)
const PLASTIC_SC = 0.85;                    // Mom's balcony gnome: a cheap, slightly smaller moulding (fits its box)
const plasticGnome = () => { const g = K.makePlasticGnome({ finish: 'glossy' }); g.scale.multiplyScalar(PLASTIC_SC); return g; };

// ------------------------------------------------------------------ helpers (the part2 conventions)
// Event time minus 0.1 ms: the engine's t for the event's own frame can land 1e-15 s under the exact quotient, which
// would push a `t >= t0` switch one frame late.
const evT = (ctx, k, fb) => { const v = C.evT(ctx, k, fb); return v == null ? v : v - 1e-4; };
// The house-style push from params.camera.move (mode 'fov' = the engine's 'zoom': no parallax).
function basePush(ctx, o = {}) { const m = ctx.params.camera.move; ctx.camera.push(o.Z ?? m.Z ?? 0.19, { mode: m.mode === 'dolly' ? 'dolly' : 'zoom', t0: o.t0, t1: o.t1 }); }
function paramRoll(ctx) { const r = ctx.params.camera.roll; if (r) ctx.camera.rollBy(r.deg[1] - r.deg[0]); }
function sparks(ctx, center, size, count, seed, o = {}) { const f = sets.sparkles(ctx, SPK({ center, size, count, seed, ...o })); ctx.add(f); return f; }
function nightLot(ctx, o = {}) { const H = SE.heroLot(ctx, { tod: 'night', bed: 'empty', truck: 'open', gate: 1.5, sold: -1, lanterns: 1, ...o }); ctx.add(H); return H; }
function nightRig(ctx, set, preset = 'nightHigh', o = {}) {
  const f = preset === 'night' ? sets.nightStreet : sets.nightLawn; const { low, ...rest } = o;
  return f(ctx, { set, skyPreset: low === false ? C.GALAXY : C.GALAXY_LOW, skyOpts: { intensity: 1.6 }, ...rest });
}
function camBasis(ctx) { ctx.camera.apply(0); const cam = ctx.cam; const pos = cam.position.clone(); const fwd = new THREE.Vector3(0, 0, -1).applyQuaternion(cam.quaternion); const right = new THREE.Vector3(1, 0, 0).applyQuaternion(cam.quaternion); return { pos, fwd, right }; }
// Warm face key from upper front-left of the subject as seen from the camera (bible: warm key on faces, cool set).
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
// dist / height in studs (height from `ground`), pitch in degrees (+ looks up). Returns { pos, tgt }.
function boardCam(ctx, subj, { ref = [0, 0, 1], yaw = 0, dist, h, pitch = 0, ground = 0, fov }) {
  const r0 = P3(ref); const d = new THREE.Vector3(r0.x, 0, r0.z).normalize().applyAxisAngle(YAX, yaw * DEG); const s = P3(subj);
  const pos = s.clone().addScaledVector(d, dist * S); pos.y = ground + h * S;
  const hd = Math.hypot(s.x - pos.x, s.z - pos.z); const tgt = s.clone(); tgt.y = pos.y + hd * Math.tan(pitch * DEG);
  ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov }); return { pos, tgt };
}
const worldOf = (o) => { o.updateWorldMatrix(true, false); return o.getWorldPosition(new THREE.Vector3()); };

// part2's front door: banged open in s28 and left open (warm hall light). The leaf copy covers the merged door.
function frontDoor(ctx, door = LOT_DOOR, { light = 3.2 } = {}) {
  const W = 1.27, Hh = 2.39, z = door[2] - 0.045; const g = new THREE.Group(); g.name = 'p3FrontDoor';
  const glowMat = ctx.cache('p2:doorGlowMat', () => new THREE.MeshBasicMaterial({ color: new THREE.Color('#ffc890').multiplyScalar(1.35), fog: false }));
  const glow = new THREE.Mesh(new THREE.PlaneGeometry(W, Hh), glowMat); glow.position.set(door[0], door[1] + Hh / 2, z + 0.01); glow.renderOrder = 2; g.add(glow);
  const leafMat = ctx.cache('p2:doorLeafMat', () => new THREE.MeshStandardMaterial({ map: doorTex('#7a2a20'), roughness: 0.5 }));
  const edgeMat = ctx.cache('p2:doorEdgeMat', () => new THREE.MeshStandardMaterial({ color: '#5a1a14', roughness: 0.6 }));
  const hinge = new THREE.Group(); hinge.position.set(door[0] - W / 2, door[1], z + 0.03); hinge.rotation.y = -1.75; g.add(hinge);
  const leaf = new THREE.Mesh(new THREE.BoxGeometry(W, Hh, 0.05), [edgeMat, edgeMat, edgeMat, edgeMat, leafMat, leafMat]); leaf.position.set(W / 2, Hh / 2, 0); hinge.add(leaf);
  ctx.add(ctx.lights.point({ color: '#ffc890', intensity: light, pos: [door[0], door[1] + 1.7, door[2] + 0.55], decay: 2 }));
  const halo = C.pxSprite(C.addSpriteMat(ctx.tex.radialGlow({ falloff: 2.2 }), '#ffcf98', 0.8), 260); halo.position.set(door[0], door[1] + 1.4, z + 0.15); halo.renderOrder = 6; halo.material.opacity = 0.35; g.add(halo);
  ctx.add(g); return g;
}
const streetDoor = (R) => { const l = R.userData.lots.find((x) => x.id === 'A3'); return [l.door[0], 0.32, l.door[2]]; };

// The hero (heroBarefoot) carrying Grandpa: 'hug' (in front of his belly, part2) or 'tuck' (under the left arm).
function heroWithGnome(ctx, { at = [0, 0, -8.6], yaw = 0, face = 'determined', mode = 'hug', pose = null, gnome = {} } = {}) {
  const hero = K.makeCharacter('heroBarefoot', { face }); hero.position.set(at[0], at[1], at[2]); hero.rotation.y = yaw;
  K.setPose(hero, pose || (mode === 'hug' ? HUG : TUCK_ARM)); ctx.add(hero);
  const g = K.makeGnome('grandpa', { units: 'stud', lantern: 1, wear: 0.12, ...gnome }); C.softenBeard(g);
  const hips = hero.getObjectByName('hips');
  if (mode === 'hug') g.position.set(...HOLD_OFF); else { g.position.set(...TUCK_OFF); g.rotation.set(0.12, 0.25, -0.16); }
  hips.add(g); hero.updateWorldMatrix(true, true); return { hero, g };
}
// The lantern on its ring (pendulum, decaying), u = seconds since the swing started (part2).
function lanternSwing(g, u, { amp = 12, freq = 1.4, decay = 1.0, phase = Math.PI / 2 } = {}) {
  const L = g.getObjectByName('lantern'); if (!L) return; const a = amp * DEG * Math.exp(-decay * Math.max(0, u)) * Math.sin(2 * Math.PI * freq * u + phase);
  L.rotation.z = a; L.rotation.x = 0.3 * a;
}
// Grandpa's lantern, lit since s38 (level 1, flicker) with the 5-stud ring on the grass (following the lantern).
function grandpaLantern(ctx, g, o = {}) { const L = X.lanternLight(ctx, g, { t0: -1, ring: 5, burst: false, cd: 1.6, ...o }); ctx.add(L.group); return L; }
// The family gnomes' lanterns on our lawn, lit in the s40 cascade: 2-stud pools, no point lights (cheap).
function familyLanterns(ctx, H, { skip = [] } = {}) {
  const fam = H.ep01.gnomes.family || {}; const out = [];
  for (const [slot, g] of Object.entries(fam)) { if (skip.includes(slot) || !g.getObjectByName('lantern')) continue; const L = X.lanternLight(ctx, g, { t0: -1, ring: 2, ringOpts: { boost: 1.5, rimBoost: 2.6, rimA: 0.5 }, burst: false, light: false, haloPx: 48, seed: 'p3fam' + slot }); ctx.add(L.group); out.push(L); }
  return { update: (t) => { for (const L of out) L.update(t); } };
}
// Theo asleep on the bare mattress, on his side facing the window (+Z), curled round the whale (bible: sleeping face):
// from outside his face reads through the glass, inside the window's warm light falls on it. Room anchors: sleeper.head / body.
const SLEEP_POSE = { armLx: 78, armRx: 70, armLz: -16, armRz: -10, legLx: 42, legRx: 26, neckX: -6 };
const MATTRESS_TOP = 0.66;
function theoAsleep(ctx, H, { badge = false } = {}) {
  const A = H.ep01.room.sleeper; const theo = K.makeCharacter('theo', { face: 'sleeping' }); const sc = 0.85;
  const wh = CR.stuffedWhale(); CR.holdWhale(theo, wh, 'asleep'); K.setPose(theo, SLEEP_POSE);
  const b = badge ? K.addBadge6(theo, { at: [0.62, 1.82], tilt: -14 }) : null;
  const yAx = V3(A.head).sub(V3(A.body)).setY(0).normalize(); const zAx = new THREE.Vector3(0, 0, 1); const xAx = new THREE.Vector3().crossVectors(yAx, zAx).normalize();
  theo.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(xAx, yAx, zAx));
  theo.position.copy(V3(A.head)).addScaledVector(yAx, -4.6 * S * sc).add(new THREE.Vector3(0.15, 0, 0)); theo.position.y = MATTRESS_TOP + 1.0 * S * sc; theo.position.z -= 0.05;
  ctx.add(theo); theo.updateWorldMatrix(true, true); return { theo, badge: b, whale: wh };
}
// A small cluster of tulips built as separate pivots so they can quiver (the set's tulips are merged).
function tulipCluster(ctx, spots, { seed = 'tul' } = {}) {
  const mats = ctx.cache('p3:tulipMats', () => ({ stem: new THREE.MeshStandardMaterial({ color: '#3f7a2e', roughness: 0.6 }), leaf: new THREE.MeshStandardMaterial({ color: '#356d2c', roughness: 0.55 }),
    cup: ['#e8385a', '#f2c230', '#ff6a8a', '#d8283a'].map((c) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.42, emissive: c, emissiveIntensity: 0.05 })) }));
  const cupG = ctx.cache('p3:tulipCup', () => { const g = new THREE.LatheGeometry([[0, 0], [0.13, 0.03], [0.19, 0.14], [0.18, 0.3], [0.11, 0.42], [0.06, 0.38]].map(([x, y]) => new THREE.Vector2(x, y)), 10); g.userData.persistent = true; return g; });
  const stemG = ctx.cache('p3:tulipStem', () => { const g = new THREE.CylinderGeometry(0.035, 0.045, 1, 6); g.translate(0, 0.5, 0); g.userData.persistent = true; return g; });
  const leafG = ctx.cache('p3:tulipLeaf', () => { const g = new THREE.SphereGeometry(1, 8, 6); g.userData.persistent = true; return g; });
  const r = makeRng(hash32('p3tulips', seed)); const out = [];
  for (const [x, y, z, ci, h] of spots) {
    const piv = new THREE.Group(); piv.position.set(x, y, z); const st = new THREE.Group(); st.scale.setScalar(S); piv.add(st);
    const hh = h ?? 1.05 + 0.15 * r(); const stem = new THREE.Mesh(stemG, mats.stem); stem.scale.set(1, hh, 1); st.add(stem);
    const cup = new THREE.Mesh(cupG, mats.cup[ci % 4]); cup.position.y = hh - 0.05; cup.rotation.y = r() * Math.PI; cup.scale.setScalar(1.08); st.add(cup);
    for (const s of [-1, 1]) { const lf = new THREE.Mesh(leafG, mats.leaf); lf.position.set(s * 0.1, 0.28, 0); lf.rotation.set(0, r() * Math.PI, s * 0.35); lf.scale.set(0.09, 0.34, 0.03); st.add(lf); }
    piv.userData.ph = r() * 6.28; piv.userData.f = 7 + 4 * r(); ctx.add(piv); out.push(piv);
  }
  return out;
}

// Mom's BALCONY GNOME box as a real open carton (the kit's box is a solid block, so nothing could come out of it): kraft
// walls and floor, two top flaps hinged on the +-Z edges (they open left / right in the s49 top-down frame) carrying the
// printed label, packing tape over the seam. Metres; origin at the floor centre. flaps[i].userData.sgn = opening sign.
function balconyCarton(ctx, { w = 0.7, d = 0.62, h = 0.6, th = 0.012 } = {}) {
  const mats = ctx.cache('p3:cartonMats', () => ({ out: new THREE.MeshStandardMaterial({ color: '#c99760', roughness: 0.82 }), inn: new THREE.MeshStandardMaterial({ color: '#8f6238', roughness: 0.9 }),
    tape: new THREE.MeshStandardMaterial({ color: '#d9b77e', roughness: 0.32 }),
    label: (() => { const c = document.createElement('canvas'); c.width = 512; c.height = 512; const g = c.getContext('2d');
      g.fillStyle = '#c99760'; g.fillRect(0, 0, 512, 512); for (let i = 0; i < 260; i++) { g.fillStyle = `rgba(90,60,30,${0.04 + 0.05 * ((i * 37) % 7) / 7})`; g.fillRect((i * 97) % 512, (i * 53) % 512, 3 + (i % 5), 1 + (i % 3)); }
      g.fillStyle = '#1e1a18'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.font = 'bold 84px "DejaVu Sans", sans-serif'; g.fillText('BALCONY', 256, 190); g.fillText('GNOME', 256, 290);
      g.strokeStyle = '#c8241c'; g.lineWidth = 8; g.strokeRect(150, 368, 212, 64); g.fillStyle = '#c8241c'; g.font = 'bold 40px "DejaVu Sans", sans-serif'; g.fillText('FRAGILE', 256, 402);
      const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.userData.persistent = true; return new THREE.MeshStandardMaterial({ map: t, roughness: 0.8 }); })() }));
  const g = new THREE.Group(); g.name = 'balconyCarton';
  const box = (sx, sy, sz, x, y, z, m) => { const b = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), m); b.position.set(x, y, z); g.add(b); return b; };
  box(d, th, w, 0, th / 2, 0, [mats.out, mats.out, mats.inn, mats.out, mats.out, mats.out]);
  for (const sz of [-1, 1]) box(d, h, th, 0, h / 2, sz * (w / 2 - th / 2), sz > 0 ? [mats.out, mats.out, mats.out, mats.out, mats.out, mats.inn] : [mats.out, mats.out, mats.out, mats.out, mats.inn, mats.out]);
  for (const sx of [-1, 1]) box(th, h, w - 2 * th, sx * (d / 2 - th / 2), h / 2, 0, sx > 0 ? [mats.out, mats.inn, mats.out, mats.out, mats.out, mats.out] : [mats.inn, mats.out, mats.out, mats.out, mats.out, mats.out]);
  const flaps = [];
  for (const sz of [1, -1]) {
    const hinge = new THREE.Group(); hinge.position.set(0, h, sz * w / 2); g.add(hinge); hinge.userData.sgn = sz;
    const fl = new THREE.Mesh(new THREE.BoxGeometry(d, th, w / 2), [mats.out, mats.out, mats.out, mats.inn, mats.out, mats.out]); fl.position.set(0, th / 2, -sz * w / 4); hinge.add(fl);
    // the printed label, half on each flap (image: text right = -Z, text up = -X)
    const pg = new THREE.PlaneGeometry(w / 2, d); const uv = pg.attributes.uv; const u0 = sz > 0 ? 0 : 0.5; for (let i = 0; i < uv.count; i++) uv.setX(i, u0 + uv.getX(i) * 0.5);
    const lab = new THREE.Mesh(pg, mats.label); lab.rotation.set(-Math.PI / 2, Math.PI / 2, 0, 'YXZ'); lab.position.set(0, th + 0.001, -sz * w / 4); hinge.add(lab);
    flaps.push(hinge);
  }
  const tape = box(d + 0.02, 0.004, 0.07, 0, h + th + 0.003, 0, mats.tape);
  return { group: g, flaps, tape, h };
}

// ==================================================================================================================
export const PART = 3;
export const builders = {

  // s42 "Gnomes aren't decorations." (46.30-47.62) - low CU on a neighbour's lit lawn gnome (family gnome 4, orange hat),
  // its face lit from below by its own lantern like the TF fairies, unblinking, staring at its house; behind it, out on
  // the lawn, a mound noses up to the edge of its pool, snout recoiling, and backs off. Push 22 %, roll +1.5.
  lit_gnome_cu: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const T = ctx.shot.duration;
      const R = SE.ep01Street(ctx, { tod: 'night', lanterns: 1, truck: 'open', skip: ['A3.bed0', 'A2.lawn3'] }); ctx.add(R);
      const P = [-4.64, 0, -8.352];                     // A2.lawn3 (the neighbour's lawn left of ours), facing its house (-Z)
      const g = K.makeFamilyGnome(4, { lantern: 1, lanternLight: 0.9 }); /* boarded 2.5 cd: at 0.2 m it washes the beard and coat out (QA v4/v5) */ g.position.set(...P); g.rotation.y = Math.PI + 0.12; ctx.add(g); ctx.shared.g = g;
      ctx.add(sets.contactShadow(ctx, { pos: [P[0], 0.005, P[2]], radius: 0.24, opacity: 0.4 }));
      K.setGnomeGaze(g, -4, 4); g.updateWorldMatrix(true, true); const eyes = C.eyesOf(g);
      const fwd = new THREE.Vector3(Math.sin(g.rotation.y), 0, Math.cos(g.rotation.y));
      boardCam(ctx, eyes, { ref: fwd.toArray(), yaw: c.yaw_deg, dist: c.dist_studs, h: 0.5, pitch: c.pitch_deg, fov: p.fov });
      basePush(ctx); paramRoll(ctx);
      nightRig(ctx, R, 'nightHigh', { lamp: { n: 3 }, postOpts: CU_GRADE });
      coolRim(ctx, eyes.toArray(), { intensity: 0.9 });
      ctx.add(ctx.lights.point({ color: '#ff9a40', intensity: 0.45, pos: eyes.clone().addScaledVector(fwd, 0.38).add(new THREE.Vector3(0, -0.24, 0)).toArray(), decay: 2 }));   // the lantern key from below (TF fairies)
      const L = X.lanternLight(ctx, g, { t0: -1, ring: 2, ringOpts: { boost: 1.6, rimBoost: 2.8 }, burst: false, haloPx: 70, seed: 's42' }); ctx.add(L.group); ctx.shared.L = L;
      // the mound: from the street side it noses to the rim of the 2-stud pool (snout recoils on the rim), then backs off
      const B = camBasis(ctx); const fh = B.fwd.clone().setY(0).normalize(); const rh = B.right.clone().setY(0).normalize();
      const st = V3(P).addScaledVector(fh, 1.85).addScaledVector(rh, 0.85); const en = V3(P).addScaledVector(fh, 0.2).addScaledVector(rh, 0.2);
      const f = CR.moleField(ctx, { center: [(P[0] + st.x) / 2, (P[2] + st.z) / 2], size: [16, 16], res: 96, seed: 's42', heads: 'snout' }); ctx.add(f.group);
      const k = f.add({ at: [st.x, st.z], scale: 1.0, face: [P[0], P[2]] }); f.travel(k, [[st.x, st.z], [en.x, en.z]], -0.55, 4.0); f.stopAt(k, [P[0], P[2]], 2 * S); f.eyes(k, -5, null);
      f.pushBack([P[0], P[2]], 0, 2 * S + 0.55, 0.78, 0.5); ctx.shared.f = f;
      const mc = X.moundCrumbs(ctx, f, { pops: false, rate: 10 }); ctx.add(mc.group); ctx.shared.mc = mc;
      const lan = worldOf(g.getObjectByName('lantern'));
      ctx.shared.md = sets.magicDust(ctx, { center: lan.toArray(), radius: 0.16, height: 0.45, count: 10, rise: 0.25, px: [10, 22], seed: 's42dust' }); ctx.add(ctx.shared.md);
      ctx.shared.fx = sparks(ctx, eyes.clone().add(new THREE.Vector3(0, 0.05, 0.25)).toArray(), [0.7, 0.5, 0.4], 6, 's42', { px: [40, 75] });
      void T;
    },
    update(ctx, t) { const s = ctx.shared; K.gnomeIdle(s.g, t, { seed: 's42', amp: 0.25 }); s.L.update(t); s.f.update(t); s.mc.update(t); s.md.update(t); s.fx.update(t); },
  },

  // s43 "They're the fence." (47.62-48.52) - EWS high over our street: an unbroken chain of 2-stud lantern pools runs along
  // the front lawns between the pavement and the houses, our lot's big ring round the hero; mounds with amber eyes prowl
  // outside the light; next door (A4) is the one dark gap. Held through the pause after "fence". Push 12 %, crane +4 studs.
  fence_aerial: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const R = SE.ep01Street(ctx, { tod: 'night', lanterns: 0, truck: 'open', skip: ['A3.bed0'] }); ctx.add(R); const E = R.ep01;
      frontDoor(ctx, streetDoor(R));
      const { g } = heroWithGnome(ctx, { at: STREET_HERO, face: 'determined' }); ctx.shared.g = g;
      // h 60 studs, pitch -35, fov 50, looking back down the street from beyond next door: the lawns of side A recede
      // from next door (bottom) past our lot to the far end (top)
      const h = c.height_studs * S; const head = 16 * DEG; const fwd = new THREE.Vector3(-Math.cos(head), 0, -Math.sin(head));
      const aim = new THREE.Vector3(8.5, 0, -9.0); const back = h / Math.tan(-c.pitch_deg * DEG);
      const pos = aim.clone().addScaledVector(fwd, -back); pos.y = h;
      ctx.camera.set({ pos: pos.toArray(), target: aim.toArray(), fov: p.fov }); basePush(ctx); ctx.camera.crane(c.drift.crane_studs * S);
      nightRig(ctx, R, 'night', { low: false, lamp: { n: 4 } });
      const GL = grandpaLantern(ctx, g); ctx.shared.GL = GL;
      const lit = E.gnomes.filter((e) => !e.plastic && e.g.getObjectByName('lantern'));
      lit.sort((a, b) => V3(a.pos).distanceTo(aim) - V3(b.pos).distanceTo(aim));
      ctx.shared.lan = lit.map((e, i) => { const L = X.lanternLight(ctx, e.g, { t0: -1, ring: 4.5, ringOpts: { boost: 1.8, rimBoost: 3.4, rimA: 0.7 }, burst: false, haloPx: 52, cd: 1.6, light: i < 3, seed: 's43' + e.slot }); ctx.add(L.group); return L; });
      // mounds prowling on every lawn, outside the pools; next door's lawn (the gap) has the most
      const r = makeRng(hash32('p3s43')); const fields = [];
      for (const l of R.userData.lots.filter((x) => x.side === 'A')) {
        const cz = l.gate[2] - 3.3; const f = CR.moleField(ctx, { center: [l.gate[0], cz], size: [34, 19], res: 64, seed: 's43' + l.id, heads: 'eyes' }); ctx.add(f.group);
        const pools = lit.filter((e) => e.lot === l.id).map((e) => e.pos); if (l.id === 'A3') pools.push(STREET_HERO);
        const n = l.id === 'A4' ? 5 : 3;
        for (let i = 0; i < n; i++) {
          let x = 0, z = 0; for (let tries = 0; tries < 12; tries++) { x = l.gate[0] + (r() - 0.5) * 9.5; z = cz + (r() - 0.5) * 4.6; if (pools.every((q) => Math.hypot(q[0] - x, q[2] - z) > (q === STREET_HERO ? 2.3 : 2.0))) break; }
          const k = f.add({ at: [x, z], scale: 1.05 + 0.3 * r() }); const a = r() * 6.28; const sp = 1.6 + 0.8 * r();
          f.travel(k, [[x, z], [x + Math.cos(a) * 0.9, z + Math.sin(a) * 0.5], [x + Math.cos(a + 1.3) * 1.5, z + Math.sin(a + 1.3) * 0.8]], -0.4 + 0.3 * r(), sp); f.eyes(k, -5, null);
          const q = pools.slice().sort((A, B) => Math.hypot(A[0] - x, A[2] - z) - Math.hypot(B[0] - x, B[2] - z))[0]; if (q) f.stopAt(k, [q[0], q[2]], q === STREET_HERO ? 5 * S : 4.5 * S);
        }
        fields.push(f);
      }
      ctx.shared.fields = fields;
      ctx.shared.fx = sparks(ctx, aim.clone().add(new THREE.Vector3(2, 3, 2)).toArray(), [10, 3, 8], 8, 's43', { px: [36, 64] });
    },
    update(ctx, t) { const s = ctx.shared; lanternSwing(s.g, t + 6, { amp: 12, decay: 0.9 }); s.GL.update(t); for (const L of s.lan) L.update(t); for (const f of s.fields) f.update(t); s.fx.update(t); },
  },

  // s44 "The new family's boy, Theo, six," (48.52-50.15) - the old room, half empty: Theo asleep on the bare mattress on the
  // floor, on his side hugging his whale, the yellow "6" badge on his pyjamas, boxes THEO, projected stars; the window
  // behind him warm with the lantern outside. The badge glints on "six" (star, 90 px). Character-intro push 30 % + roll 10.
  theo_intro: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); const { theo, badge } = theoAsleep(ctx, H, { badge: true }); ctx.shared.H = H;
      const face = worldOf(theo.getObjectByName('head')); const bp = worldOf(badge); const subj = face.clone().lerp(bp, 0.6);
      boardCam(ctx, subj, { ref: [0, 0, 1], yaw: c.yaw_deg, dist: c.dist_studs, h: c.height_studs, pitch: c.pitch_deg, ground: ROOM_FLOOR, fov: p.fov });
      basePush(ctx); paramRoll(ctx);
      I.bedroomNight(ctx, { set: H, lamp: 4, nightlight: 2.5, moon: true, lanternOutside: true }); ctx.post.params.exposure *= 0.86;
      warmKey(ctx, face.toArray(), { cd: 0.9, d: 0.7, color: '#ffc8a8' });
      const gl = C.starGlint(ctx, { pos: bp.clone().add(new THREE.Vector3(0, 0.01, 0.02)), t0: evT(ctx, 'six', 1.23), peak: 90, rot: 20, color: '#ffe9b0' }); ctx.add(gl); ctx.shared.gl = gl;
      ctx.shared.fx = sparks(ctx, face.clone().add(new THREE.Vector3(0.25, 0.3, 0.2)).toArray(), [1.2, 0.8, 0.5], 9, 's44', { px: [40, 80] });
    },
    update(ctx, t) { const s = ctx.shared; s.gl.update(t); s.fx.update(t); },
  },

  // s45 "was already asleep in my old room." (50.15-51.57) - outside: Theo's window, the room lit softly by the nightlight,
  // Theo asleep inside; the empty soil ring in the bed below in the lantern's warm pool; the hero at frame left holding the
  // lit gnome, looking in, sad. Dolly push 19 %.
  theo_window_out: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); frontDoor(ctx); theoAsleep(ctx, H);
      // yaw 20 / pitch 4 as boarded on the window base; lens 9 studs out at h 4.6 (from h 2.5 the sill hides Theo on his
      // mattress, and at 6 studs the hero is cut by the frame edge)
      const subj = [WIN[0] - 0.25, 0, BED[2]];
      const { pos } = boardCam(ctx, subj, { ref: [0, 0, 1], yaw: c.yaw_deg, dist: 8, h: 5.2, pitch: c.pitch_deg - 8, fov: p.fov }); basePush(ctx);
      const B = camBasis(ctx); const fh = B.fwd.clone().setY(0).normalize(); const rh = B.right.clone().setY(0).normalize();
      const hp = pos.clone().setY(0).addScaledVector(fh, 2.1).addScaledVector(rh, -0.36); const HP = hp.toArray();
      const { hero, g } = heroWithGnome(ctx, { at: HP, yaw: Math.atan2(WIN[0] - HP[0], WIN[2] - HP[2]) - 0.15, face: p.cast[0].face || 'sad', pose: { ...HUG, neckX: 10 } }); ctx.shared.g = g;
      ctx.add(sets.contactShadow(ctx, { pos: [HP[0], 0.005, HP[2]], radius: 0.42, opacity: 0.35 }));
      nightRig(ctx, H, 'nightHigh', { lamp: { n: 2 }, postOpts: CU_GRADE });
      warmKey(ctx, worldOf(hero.getObjectByName('head')).toArray(), { cd: 1.4, d: 0.9, color: '#ffc896' });
      ctx.shared.GL = grandpaLantern(ctx, g); ctx.shared.fam = familyLanterns(ctx, H);
      ctx.shared.fx = sparks(ctx, up(WIN, -1.6, 0, 2.2), [2.2, 1.4, 1.0], 8, 's45', { px: [40, 75] }); void hero;
    },
    update(ctx, t) { const s = ctx.shared; lanternSwing(s.g, t + 8, { amp: 10, decay: 0.9 }); s.GL.update(t); s.fam.update(t); s.fx.update(t); },
  },

  // s46 "Take Grandpa, and Theo's window goes dark." (51.57-53.68) - the what-if, profile WS: the hero takes one walk cycle
  // toward the truck (left -> right) and the circle of light slides with him off the flowerbed, which goes black; on
  // "Theo's" two mounds start gliding toward the bed; on "dark" the window snaps off (1 frame) and the mounds surge 0.5
  // stud. Push 12 % + truck 1.5 studs.
  take_window_dark: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); frontDoor(ctx); theoAsleep(ctx, H); ctx.shared.H = H;
      const tTheo = evT(ctx, "theo's", 0.698), tDark = evT(ctx, 'dark', 1.533); Object.assign(ctx.shared, { tTheo, tDark });
      const z0 = BED[2] + 0.72, tw0 = 0.18, tw1 = 0.18 + 0.73; const dz = (K.WALK_SPEED * S) * (tw1 - tw0) * 0.92;
      const zAt = (t) => z0 + dz * smooth((t - tw0) / (tw1 - tw0)) * 0.5 + dz * 0.5 * clamp01((t - tw0) / (tw1 - tw0)); ctx.shared.zAt = zAt; ctx.shared.tw = [tw0, tw1];
      const { hero, g } = heroWithGnome(ctx, { at: [BED[0] + 0.05, 0, z0], yaw: 0, face: p.cast[0].face || 'determined' }); ctx.shared.hero = hero; ctx.shared.g = g;
      const sh = sets.contactShadow(ctx, { pos: [BED[0], 0.005, z0], radius: 0.42, opacity: 0.35 }); ctx.add(sh); ctx.shared.sh = sh;
      // profile from the left (-X) side so the step toward the street reads left -> right (board 5); yaw -72 instead of
      // 90: at a pure profile the house front (and Theo's window) is edge-on and the "dark" beat cannot be seen
      const subj = [BED[0] - 0.15, 0, BED[2] + 0.75];
      boardCam(ctx, subj, { ref: [0, 0, 1], yaw: -62, dist: c.dist_studs, h: c.height_studs, pitch: c.pitch_deg, fov: p.fov });
      basePush(ctx); ctx.camera.truck(c.drift.truck_studs * S);
      nightRig(ctx, H, 'nightHigh', { lamp: { n: 2 }, window: { n: 0 } });
      // Theo's window spill on the bed / lawn (switched with the room)
      const spill = ctx.add(ctx.lights.point({ color: '#ffd9a0', intensity: 2.2, pos: up(WIN, -1.2, 0, 2.2), decay: 2 })); ctx.shared.spill = spill;
      ctx.shared.wd = X.windowDark(ctx, H, { t0: tDark });
      ctx.shared.GL = grandpaLantern(ctx, g); ctx.shared.fam = familyLanterns(ctx, H);
      // two mounds waiting outside the light on either side of the bed; from "Theo's" they glide to it, surge on "dark"
      const f = CR.moleField(ctx, { center: [BED[0], BED[2] + 1.2], size: [22, 16], res: 112, seed: 's46', heads: 'snout' }); ctx.add(f.group);
      const A0 = [BED[0] + 0.55, BED[2] + 2.75], B0 = [BED[0] + 1.85, BED[2] + 0.75];
      const a = f.add({ at: A0, scale: 1.35, face: [BED[0], BED[2]] }), b = f.add({ at: B0, scale: 1.25, face: [BED[0], BED[2]] });
      f.travel(a, [A0, [BED[0] + 0.25, BED[2] + 0.75]], tTheo, 2.0); f.travel(b, [B0, [BED[0] + 0.62, BED[2] + 0.3]], tTheo + 0.08, 1.8); f.eyes(a, -5, null); f.eyes(b, -5, null);
      ctx.shared.f = f; ctx.shared.h0 = [f.moles[a].height, f.moles[b].height];
      const mc = X.moundCrumbs(ctx, f, { pops: false, rate: 10 }); ctx.add(mc.group); ctx.shared.mc = mc;
      ctx.shared.fx = sparks(ctx, [BED[0], 0.9, BED[2] + 1.3], [1.6, 1.0, 2.6], 6, 's46', { px: [36, 64] });
    },
    update(ctx, t) {
      const s = ctx.shared; const hero = s.hero; const z = s.zAt(t); hero.position.z = z; s.sh.position.z = z;
      const [tw0, tw1] = s.tw; const u = (t - tw0) / (tw1 - tw0); const amp = Math.sin(Math.PI * clamp01(u));
      const wc = K.walkCycle(Math.max(0, t - tw0), { period: 0.73, legs: 34 * amp, arms: 0 }); K.setPose(hero, { ...HUG, legLx: wc.legLx || 0, legRx: wc.legRx || 0, bodyX: 4 * amp, lift: 0.08 * amp * Math.abs(Math.sin(2 * Math.PI * (t - tw0) / 0.73)) });
      lanternSwing(s.g, t - tw0, { amp: 9 * (u > 0 ? 1 : 0), decay: 1.4 }); s.GL.update(t); s.fam.update(t);
      s.wd.update(t); const on = t < s.tDark; s.spill.visible = on;
      const surge = t < s.tDark ? 0 : 0.5 * springStep(t - s.tDark, 3.0, 0.4); s.f.moles.forEach((m, i) => { m.height = s.h0[i] + surge; });
      s.f.update(t); s.mc.update(t); s.fx.update(t);
    },
  },

  // s47 "Leave him, and I never get another blink." (53.68-55.25) - the hero's POV looking down into his arms: Grandpa,
  // lantern lit, eyes wide open looking up at him, waiting. No blink. Push 20 %.
  gnome_waiting: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); frontDoor(ctx); theoAsleep(ctx, H);
      const HP = [BED[0] + 0.1, 0, BED[2] + 1.4];
      // cradled: held out a little in both arms and tipped back 35 deg so the painted face looks up at him (from his eye line
      // a gnome hugged upright shows only its hat)
      const { hero, g } = heroWithGnome(ctx, { at: HP, yaw: Math.PI, face: 'sad', pose: CRADLE }); ctx.shared.g = g; ctx.shared.hero = hero;
      g.position.set(0, 0.55, 1.3); g.rotation.set(35 * DEG, Math.PI, 0);
      for (const n of ['head']) { const o = hero.getObjectByName(n); if (o) o.visible = false; }
      hero.traverse((o) => { if (/hood/i.test(o.name)) o.visible = false; });
      // the lens at his chin (h 4.3 studs, in front of the hidden head), looking down 40 deg into his arms
      hero.updateWorldMatrix(true, true); const pos = hero.localToWorld(new THREE.Vector3(0, 4.3, 0.62)); pos.y = c.height_studs * S;
      const fwd = new THREE.Vector3(0, 0, -1); const tgt = pos.clone().addScaledVector(fwd, Math.cos(c.pitch_deg * DEG)); tgt.y += Math.sin(c.pitch_deg * DEG);
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: p.fov }); basePush(ctx);
      K.setGnomeHead(g, 0, 16, 0); g.updateWorldMatrix(true, true); C.gazeAt(g, pos); const ge = C.eyesOf(g); ctx.shared.camPos = pos;
      nightRig(ctx, H, 'nightHigh', { lamp: { n: 2 }, low: false, postOpts: CU_GRADE });
      const L = grandpaLantern(ctx, g, { cd: 1.0, lightOffset: [0, 0.1, 0.22] }); ctx.shared.L = L; ctx.shared.fam = familyLanterns(ctx, H);
      warmKey(ctx, ge.toArray(), { cd: 0.5, d: 0.6, color: '#ffc8a0' });
      const lan = worldOf(g.getObjectByName('lantern'));
      ctx.shared.md = sets.magicDust(ctx, { center: lan.toArray(), radius: 0.2, height: 0.5, count: 12, rise: 0.3, px: [10, 22], seed: 's47dust' }); ctx.add(ctx.shared.md);
      ctx.shared.fx = sparks(ctx, ge.clone().lerp(pos, 0.3).toArray(), [0.7, 0.3, 0.6], 7, 's47', { px: [40, 75] });
    },
    update(ctx, t) {
      const s = ctx.shared; lanternSwing(s.g, t + 3, { amp: 8, decay: 0.8 }); const L = s.g.getObjectByName('lantern'); if (L) L.rotation.x += 35 * DEG; // hangs plumb
      K.gnomeIdle(s.g, t, { seed: 's47', amp: 0.2 }); s.L.update(t); s.fam.update(t); s.md.update(t); s.fx.update(t);
    },
  },

  // s48 "And the truck left at dawn." (55.25-56.33) - insert in the truck cab: the red LED dashboard clock 11:52 (colon
  // blinking at 1 Hz on episode time), the yellow sticky note on the wheel LEAVE 6 AM; the street lamp through the
  // windscreen. Push 25 %.
  truck_clock: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const R = I.truckCab(ctx, { time: '11:52', note: 'LEAVE 6 AM' }); ctx.add(R); ctx.shared.R = R;
      const A = R.userData.anchors; const subj = V3(A.led).lerp(V3(A.note), 0.33); subj.y += 0.02;
      // fov 45, yaw -10, pitch -8 as boarded; the lens 1.9 m out (at the boarded 1.6 studs the 9:16 frame holds part of the LED alone)
      const d = new THREE.Vector3(0, 0, 1).applyAxisAngle(YAX, c.yaw_deg * DEG); const dist = 1.9;
      const pos = subj.clone().addScaledVector(d, dist); pos.y = subj.y + dist * Math.tan(-c.pitch_deg * DEG);
      ctx.camera.set({ pos: pos.toArray(), target: subj.toArray(), fov: p.fov }); basePush(ctx);
      I.cabNight(ctx, { cab: R });
    },
    update(ctx, t) { ctx.shared.R.ep01.update(t, ctx.T); },
  },

  // s49 "So I stood Mom's plastic gnome" (56.33-57.87) - top-down insert on the truck ramp: his hands rip the BALCONY GNOME
  // box open on "stood" (the tape tears, the flaps spring back) with Grandpa tucked under his left arm, lantern lit; on
  // "plastic" his hand lifts Mom's glossy plastic gnome out toward us (8-frame pose): red hat, $4.99 sticker, dead dot
  // eyes, smile. Push 22 %.
  balcony_box: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); frontDoor(ctx); const E = H.ep01;
      const tRip = evT(ctx, 'stood', 0.297), tLift = evT(ctx, 'plastic', 0.857); Object.assign(ctx.shared, { tRip, tLift });
      // the box: off the stack and down on the ramp (the ramp falls from x -2.56 (0.83 m) to x 0 along z -2.53, 18 deg)
      E.truck.ep01.balconyBox.visible = false; const slope = Math.atan2(0.832, 2.56);
      const bx = -1.05, bz = -2.528, by = 0.832 * (-bx / 2.56) + 0.012;
      const boxG = new THREE.Group(); boxG.position.set(bx, by, bz); boxG.rotation.z = -slope; ctx.add(boxG);
      const CB = balconyCarton(ctx); boxG.add(CB.group); ctx.shared.flaps = CB.flaps; ctx.shared.tape = CB.tape;
      // Mom's plastic gnome standing in the carton
      const pg = plasticGnome(); ctx.add(pg); ctx.shared.pg = pg;
      boxG.updateMatrixWorld(true); const inBox = new THREE.Vector3(0, 0.014, 0).applyMatrix4(boxG.matrixWorld);
      ctx.shared.inBox = inBox; ctx.shared.slope = slope;
      // the hero on the road beside the ramp (street side, +Z), facing it; Grandpa under the left arm
      const HP = [bx - 0.42, 0, bz + 0.74];
      const { hero, g } = heroWithGnome(ctx, { at: HP, yaw: Math.PI, face: 'determined', mode: 'tuck' }); ctx.shared.hero = hero; ctx.shared.g = g;
      const top = new THREE.Vector3(bx, by + CB.h, bz);
      ctx.camera.set({ pos: [top.x + 0.22 + 0.001, by + c.height_studs * S + 0.55, top.z + 0.08], target: [top.x + 0.22, top.y, top.z + 0.08], fov: p.fov }); basePush(ctx);
      nightRig(ctx, H, 'night', { lamp: { n: 2 }, low: false, postOpts: CU_GRADE });
      ctx.add(ctx.lights.point({ color: '#fff0d0', intensity: 2.2, pos: [bx - 0.9, by + 1.9, bz - 0.2], decay: 2 })); // the cargo dome's spill out of the open back
      ctx.shared.GL = grandpaLantern(ctx, g, { cd: 1.2, ring: 0 });
      const reach = { ...TUCK_ARM, bodyX: 14, armRx: 72, armRz: 4, neckX: -24 };     // fingers on the tape at the seam
      const rip = { ...reach, bodyX: 4, armRx: 50, armRz: 26 };                         // yank: back and out
      const dig = { ...reach, bodyX: 26, armRx: 62, armRz: 2 };                         // down into the carton
      const lift = { ...TUCK_ARM, bodyX: 12, armRx: 112, armRz: 2, neckX: -6 };          // up toward the lens over the carton
      ctx.shared.pose = (t) => K.poseAt(t, [[0, reach], [tRip - 0.06, rip], [tRip + 0.25, dig], [tLift, lift]], 0.1);
      ctx.shared.fx = sparks(ctx, top.clone().add(new THREE.Vector3(0, 0.3, 0)).toArray(), [0.8, 0.3, 0.9], 6, 's49', { px: [40, 70] });
      const pf = sets.burst(ctx, { pos: top.toArray(), t0: tRip, dur: 0.25, count: 10, spread: 0.3, px: [14, 30], ring: false, core: false, colors: ['#e8d8b8', '#d8c098', '#ffffff'], brightness: 1.2, gravity: -0.6, seed: 's49rip' }); ctx.add(pf); ctx.shared.pf = pf;
    },
    update(ctx, t) {
      const s = ctx.shared; K.setPose(s.hero, s.pose(t)); s.GL.update(t); s.pf.update(t); s.fx.update(t);
      // flaps: taped shut, snap open on the rip (spring), outward 125 deg
      const k = t < s.tRip ? 0 : springStep(t - s.tRip, 3.2, 0.42); for (const f of s.flaps) f.rotation.x = f.userData.sgn * 2.25 * k; s.tape.visible = t < s.tRip;
      // the plastic gnome: in the box until "plastic", then pulled up into the hand and tipped face-up to the lens
      const pg = s.pg; const u = clamp01((t - s.tLift) / (8 / 60)); const e = outQuad(u);
      s.hero.updateWorldMatrix(true, true); const hand = K.handSocket(s.hero, 'R'); const hp = worldOf(hand).add(new THREE.Vector3(0, -0.03, -0.05));
      // in the box, standing (hat up to the lens); lifted: the base in his hand, tipped onto its back so the face looks up at us
      pg.position.copy(s.inBox).lerp(hp, e); pg.rotation.set(-1.45 * e, Math.PI * 0.08 * (1 - e), -s.slope * (1 - e) + 0.12 * Math.sin(Math.PI * u), 'YXZ');
    },
  },

  // s50 "under Theo's window." (57.87-58.85) - MS from the lawn, kneeling height: under the lit window the hero kneels and
  // plants the plastic gnome in Grandpa's empty ring ("under": it thunks into the soil and wobbles), stands and backs off
  // with Grandpa under his arm; the warm ring slides off the bed. Push 18 %.
  plant_plastic: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); frontDoor(ctx); theoAsleep(ctx, H);
      const tU = evT(ctx, 'under', 0.02); ctx.shared.tU = tU;
      const pg = plasticGnome(); pg.position.set(BED[0], BED[1], BED[2]); pg.rotation.y = 0.15; ctx.add(pg); ctx.shared.pg = pg;
      const HP = [BED[0] + 0.8, 0, BED[2] + 0.32]; const yaw = Math.atan2(BED[0] - HP[0], BED[2] - HP[2]);
      const { hero, g } = heroWithGnome(ctx, { at: HP, yaw, face: p.cast[0].face || 'determined', mode: 'tuck' }); ctx.shared.hero = hero; ctx.shared.g = g; ctx.shared.HP = HP;
      const sh = sets.contactShadow(ctx, { pos: [HP[0], 0.005, HP[2]], radius: 0.45, opacity: 0.35 }); ctx.add(sh); ctx.shared.sh = sh;
      const back = new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw)).negate(); ctx.shared.back = back;
      const subj = [(BED[0] + HP[0]) / 2, 0, (BED[2] + HP[2]) / 2]; boardCam(ctx, subj, { ref: [0, 0, 1], yaw: c.yaw_deg, dist: c.dist_studs, h: c.height_studs, pitch: c.pitch_deg, fov: p.fov }); basePush(ctx);
      nightRig(ctx, H, 'nightHigh', { lamp: { n: 2 }, window: { n: 1, cd: 2.0, maxD: 10 }, postOpts: CU_GRADE });
      warmKey(ctx, [HP[0], 0.85, HP[2]], { cd: 2.4, d: 1.1 });
      ctx.shared.GL = grandpaLantern(ctx, g); ctx.shared.fam = familyLanterns(ctx, H);
      const kneel = { ...K.POSES.kneelPlace, ...TUCK_ARM, armRx: 66, armRz: -10, bodyX: 30 };
      const standP = { ...TUCK_ARM, armRx: 10, neckX: -12 };
      ctx.shared.pose = (t) => K.poseAt(t, [[0, kneel], [0.26, standP]], 0.2);
      ctx.shared.dAt = (t) => 0.95 * smooth((t - 0.42) / 0.5);
      const sb = X.soilBurst(ctx, { pos: [BED[0], BED[1] + 0.02, BED[2]], t0: tU, count: 12, spread: 0.45, apex: 0.25, puffs: 1 }); ctx.add(sb.group); ctx.shared.sb = sb;
      ctx.shared.fx = sparks(ctx, up(BED, 2.2, 0.4, 1.4), [1.8, 1.2, 1.2], 6, 's50', { px: [36, 64] });
    },
    update(ctx, t) {
      const s = ctx.shared; K.setPose(s.hero, s.pose(t));
      const d = s.dAt(t); s.hero.position.set(s.HP[0] + s.back.x * d, 0, s.HP[2] + s.back.z * d); s.sh.position.set(s.hero.position.x, 0.005, s.hero.position.z);
      const wk = clamp01((t - 0.42) / 0.5); if (wk > 0 && wk < 1) { const wc = K.walkCycle(t - 0.42, { period: 0.6, legs: -26 }); s.hero.getObjectByName('hipL').rotation.x = (wc.legLx || 0) * DEG * Math.sin(Math.PI * wk); s.hero.getObjectByName('hipR').rotation.x = (wc.legRx || 0) * DEG * Math.sin(Math.PI * wk); }
      // the thunk: drops 2 cm into the soil, then wobbles on a spring
      const u = t - s.tU; const drop = u < 0 ? 0.02 : 0.02 * (1 - outQuad(u / 0.05)); s.pg.position.y = BED[1] + drop;
      s.pg.rotation.z = u < 0 ? 0 : 10 * DEG * Math.exp(-u * 3.5) * Math.sin(u * 24); s.pg.rotation.x = u < 0 ? 0 : 4 * DEG * Math.exp(-u * 3.5) * Math.sin(u * 24 + 1.2);
      lanternSwing(s.g, t, { amp: 10, decay: 1.0 }); s.GL.update(t); s.fam.update(t); s.sb.update(t); s.fx.update(t);
    },
  },

  // s51 "Gulp. Gone." (58.85-59.70) - low CU on the plastic gnome in the dark bed (no lantern): a mound surges over it, the
  // turf closes round it like a mouth and it sinks in 6 frames, the seal burps crumbs (GULP, 6 px shake for 0.3 s);
  // "Gone.": the $4.99 sticker flutters down onto the bare soil (0.4 s). Push 20 %.
  gulp: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); frontDoor(ctx); theoAsleep(ctx, H);
      const tG = evT(ctx, 'gulp', 0.017), tGone = evT(ctx, 'gone', 0.483);
      const pg = plasticGnome(); pg.position.set(BED[0], BED[1], BED[2]); pg.rotation.y = 0.15; ctx.add(pg); ctx.shared.pg = pg;
      const subj = up(BED, 0, 0, 0); boardCam(ctx, up(BED, 0.7), { ref: [0, 0, 1], yaw: c.yaw_deg, dist: c.dist_studs, h: c.height_studs, pitch: c.pitch_deg, ground: 0, fov: p.fov }); basePush(ctx);
      ctx.camera.shake({ t0: tG, dur: 0.3, rot: 0.25, pos: 0.003, px: 6, freq: 16, seed: 51 });
      nightRig(ctx, H, 'nightHigh', { lamp: { n: 2 }, window: { n: 1, cd: 2.4, maxD: 10 } });
      coolRim(ctx, subj, { intensity: 0.8 });
      const f = CR.moleField(ctx, { center: [BED[0], BED[2]], size: [12, 8], res: 112, seed: 's51', heads: 'snout', y: BED[1] }); ctx.add(f.group);
      const st = [BED[0] + 1.05, BED[2] - 0.32]; const k = f.add({ at: st, scale: 1.1, face: [BED[0], BED[2]] }); f.travel(k, [st, [BED[0] + 0.05, BED[2] - 0.02]], tG - 0.42, (1.1 / S) / 0.42); f.eyes(k, -5, null);
      const Bc = camBasis(ctx); const toC = Bc.pos.clone().sub(V3(BED)).setY(0).normalize(); const land = V3(BED).addScaledVector(toC, 0.42).addScaledVector(Bc.right, 0.04); land.y = BED[1] + 0.006;
      const G = X.gulp(ctx, { field: f, index: k, target: pg, t0: tG, sticker: { t0: tGone, dur: 0.4, to: land }, seed: 's51' }); ctx.add(G.group); ctx.shared.G = G; ctx.shared.f = f;
      ctx.shared.fx = sparks(ctx, up(BED, 1.5, 0.3, 0.8), [1.0, 0.7, 0.5], 5, 's51', { px: [36, 60] });
    },
    update(ctx, t) { const s = ctx.shared; s.f.update(t); s.G.update(t); s.fx.update(t); },
  },

  // s52 "The mounds rolled closer" (59.70-60.72) - low behind the mounds as they roll across our lawn toward the house: the
  // dark flowerbed (the hole) and Theo's lit window ahead. On "rolled" they speed up to 3 studs/s. Dolly push 19 %.
  mounds_closer: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx, { bed: 'hole' }); frontDoor(ctx); theoAsleep(ctx, H);
      const tR = evT(ctx, 'rolled', 0.35);
      const subj = up(BED, 0, 0, 0); const { pos } = boardCam(ctx, subj, { ref: [0, 0, 1], yaw: c.yaw_deg, dist: c.dist_studs, h: c.height_studs, pitch: c.pitch_deg, fov: p.fov }); basePush(ctx);
      nightRig(ctx, H, 'nightHigh', { lamp: { n: 2 }, window: { n: 1, cd: 2.4, maxD: 10 } });
      ctx.shared.fam = familyLanterns(ctx, H); ctx.add(ctx.lights.point({ color: '#ffd2a0', intensity: 3.0, pos: up(WIN, -2.0, 0, 1.6), decay: 2 }));
      const f = CR.moleField(ctx, { center: [BED[0], (pos.z + BED[2]) / 2], size: [14, 16], res: 128, seed: 's52', heads: 'eyes' }); ctx.add(f.group);
      // the mounds wait (breathing) until "rolled", then roll at 3 studs/s toward the bed
      const lanes = [[-0.32, 1.45, 0.85], [0.42, 1.75, 0.95], [-0.7, 2.2, 1.0], [0.08, 2.6, 0.9], [0.68, 2.4, 0.85]]; ctx.shared.f = f;
      lanes.forEach(([dx, d0, sc], i) => { const st = [pos.x + dx, pos.z - d0]; const en = [BED[0] + dx * 0.4, BED[2] + 0.75]; const k = f.add({ at: st, scale: sc }); f.travel(k, [st, en], tR + 0.03 * i, 3); f.eyes(k, -5, null); });
      const mc = X.moundCrumbs(ctx, f, { pops: false, rate: 16 }); ctx.add(mc.group); ctx.shared.mc = mc;
      ctx.shared.fx = sparks(ctx, up(BED, 1.6, 0, 3.5), [2.2, 1.0, 2.0], 6, 's52', { px: [36, 64] });
    },
    update(ctx, t) {
      const s = ctx.shared; s.f.update(t); s.mc.update(t); s.fam.update(t); s.fx.update(t);
    },
  },

  // s53 "to the flowers," (60.72-61.38) - low CU in the flowerbed: two pink star snouts poke up among the tulips, sniffing the
  // stems; on "flowers" the tulips shake and the snouts wriggle. Push 22 %.
  mounds_flowers: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx, { bed: 'hole' }); frontDoor(ctx); theoAsleep(ctx, H);
      const tF = evT(ctx, 'flowers', 0.283); ctx.shared.tF = tF;
      const F0 = [BED[0] + 0.5, BED[1], -12.3]; // the bed's front tulip row right of Grandpa's spot (left of it the lens sits in the bush)
      const { pos } = boardCam(ctx, F0, { ref: [0, 0, 1], yaw: c.yaw_deg, dist: c.dist_studs, h: c.height_studs, pitch: c.pitch_deg, ground: BED[1] - 0.07, fov: p.fov }); basePush(ctx);
      nightRig(ctx, H, 'nightHigh', { lamp: { n: 1 }, window: { n: 1, cd: 2.6, maxD: 10 }, postOpts: CU_GRADE });
      const fwd = V3(F0).sub(pos).setY(0).normalize(); const side = new THREE.Vector3(-fwd.z, 0, fwd.x);
      const at = (a, b) => V3(F0).addScaledVector(side, a).addScaledVector(fwd, b);
      const m1 = CR.makeMole({ preset: 'small', seed: 21, lod: 'hero' }); m1.position.copy(at(-0.12, 0.3)); m1.position.y = BED[1] - 0.02; m1.rotation.y = Math.atan2(-fwd.x, -fwd.z) + 0.5; ctx.add(m1);
      const m2 = CR.makeMole({ preset: 'runt', seed: 23, lod: 'hero' }); m2.position.copy(at(0.2, 0.45)); m2.position.y = BED[1] - 0.02; m2.rotation.y = Math.atan2(-fwd.x, -fwd.z) - 0.4; ctx.add(m2);
      ctx.shared.m = [m1, m2]; ctx.shared.cue = [{ unfurl: -0.2, sniff: [0.0, tF + 0.35], eyesOn: -1, emerge: [[0, 0.3]] }, { unfurl: 0.02, sniff: [0.1, tF + 0.4], eyesOn: -1, emerge: [[0, 0.25]] }];
      const T = []; const add = (a, b, ci, h) => { const q = at(a, b); T.push([q.x, BED[1], q.z, ci, h]); };
      add(0.03, 0.12, 0, 1.15); add(0.12, 0.3, 1, 1.0); add(-0.24, 0.32, 3, 1.2); add(0.3, 0.18, 2, 1.1); add(-0.05, 0.5, 1, 1.25); add(-0.34, 0.1, 2, 0.95);
      ctx.shared.tul = tulipCluster(ctx, T, { seed: 's53' });
      coolRim(ctx, F0, { intensity: 0.8 });
      ctx.add(ctx.lights.point({ color: '#ffd9a0', intensity: 2.4, pos: up(WIN, -1.2, 0.8, 1.2), decay: 2 })); warmKey(ctx, up(F0, 0.6), { cd: 0.8, d: 0.6, color: '#ffc8a0' });
      ctx.shared.sb = X.soilBurst(ctx, { pos: at(-0.12, 0.3).setY(BED[1] + 0.03).toArray(), t0: -0.1, count: 10, spread: 0.4, apex: 0.3, puffs: 0 }); ctx.add(ctx.shared.sb.group);
    },
    update(ctx, t) {
      const s = ctx.shared; s.m.forEach((m, i) => CR.animateMole(m, t, s.cue[i]));
      const u = t - s.tF; for (const tp of s.tul) { const a = (u < 0 ? 0.012 : 0.09 * Math.exp(-u * 3.2)) * Math.sin(t * tp.userData.f + tp.userData.ph) + (u < 0 ? 0 : 0.03 * Math.sin(u * 31 + tp.userData.ph)); tp.rotation.set(a * 0.6, 0, a); }
      s.sb.update(t);
    },
  },

  // s54 "to the bricks," (61.38-61.92) - low CU on the dog-tooth brick edging under the window: a mound bumps along it,
  // the bricks lifting as it passes, and on "bricks" one tips out (10 deg). Push 20 %.
  mounds_bricks: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx, { bed: 'hole' }); frontDoor(ctx); theoAsleep(ctx, H); const E = H.ep01;
      const tB = evT(ctx, 'bricks', 0.25); ctx.shared.tB = tB;
      const B0 = [-2.413, 0.013, -11.92];
      const { pos } = boardCam(ctx, up(B0, 0.0), { ref: [0, 0, 1], yaw: c.yaw_deg, dist: c.dist_studs, h: c.height_studs, pitch: c.pitch_deg, fov: p.fov }); basePush(ctx);
      nightRig(ctx, H, 'nightHigh', { lamp: { n: 1 }, window: { n: 1, cd: 2.6, maxD: 10 }, postOpts: CU_GRADE });
      coolRim(ctx, B0, { intensity: 0.8 });
      const f = CR.moleField(ctx, { center: [B0[0], B0[2] + 0.3], size: [12, 8], res: 112, seed: 's54', heads: 'snout' }); ctx.add(f.group);
      const v = 3.0; const st = [B0[0] - 0.05 - v * S * tB, B0[2] - 0.3], en = [B0[0] + 1.2, B0[2] - 0.32]; const k = f.add({ at: st, scale: 0.8 });
      const bricks = E.bricks.map((b) => { const w = worldOf(b); return { b, w, y0: b.position.y, rx: b.rotation.x, rz: b.rotation.z }; });
      // the loose one: the brick nearest where the mound is on "bricks"
      f.travel(k, [st, en], 0, v); f.eyes(k, -5, null); const at = (t) => { const d = Math.min(1, Math.max(0, (v * S * t) / Math.hypot(en[0] - st[0], en[1] - st[1]))); return [lerp(st[0], en[0], d), lerp(st[1], en[1], d)]; };
      const mB = at(tB); let li = 0; bricks.forEach((q, i) => { if (Math.abs(q.w.x - mB[0]) < Math.abs(bricks[li].w.x - mB[0])) li = i; });
      Object.assign(ctx.shared, { f, bricks, li, at, v });
      const mc = X.moundCrumbs(ctx, f, { pops: false, rate: 18 }); ctx.add(mc.group); ctx.shared.mc = mc;
      ctx.shared.sb = X.soilBurst(ctx, { pos: [bricks[li].w.x, 0.08, bricks[li].w.z], t0: tB, count: 10, spread: 0.4, apex: 0.35, puffs: 1 }); ctx.add(ctx.shared.sb.group);
      void pos;
    },
    update(ctx, t) {
      const s = ctx.shared; s.f.update(t); s.mc.update(t); s.sb.update(t); const m = s.at(t);
      s.bricks.forEach((q, i) => { const d = q.w.x - m[0]; const bump = Math.exp(-(d * d) / (0.16 * 0.16)) * 0.035; const sc = 1 / S; // brick meshes live in the lot's stud space
        q.b.position.y = q.y0 + bump * sc; q.b.rotation.z = q.rz + (d > 0 ? -1 : 1) * 6 * DEG * (bump / 0.035);
        if (i === s.li) { const u = t - s.tB; const k = u < 0 ? 0 : springStep(u, 2.4, 0.5); q.b.rotation.x = q.rx + 10 * DEG * k; q.b.position.y = q.y0 + (bump + 0.012 * k) * sc; } });
    },
  },

  // s55 "to the glass." (61.92-62.57) - inside the room: Theo asleep in the foreground; behind him two amber reflector eyes
  // rise outside the window and on "glass" their breath fogs the pane (0.35 s). Push 25 %.
  eyes_fog_glass: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx, { bed: 'hole' }); const { theo } = theoAsleep(ctx, H); const E = H.ep01;
      const tG = evT(ctx, 'glass', 0.217); ctx.shared.tG = tG;
      // lens behind him toward his feet (straight behind, his shoulder and draped arm sit right in front of the pane) and
      // at h 4.0 studs (from h 2 his side silhouette hides the glass; level with the eyes); aimed at the pane with the boarded pitch
      const face = worldOf(theo.getObjectByName('head')); const subj = [WIN[0] + 0.32, 0, face.z];
      const { pos } = boardCam(ctx, subj, { ref: [0, 0, -1], yaw: c.yaw_deg, dist: c.dist_studs, h: 4.0, pitch: c.pitch_deg, ground: ROOM_FLOOR, fov: p.fov });
      { const hd = Math.hypot(WIN[0] - pos.x, WIN[2] - pos.z); ctx.camera.set({ pos: pos.toArray(), target: [WIN[0] - 0.06, pos.y + hd * Math.tan(c.pitch_deg * DEG), WIN[2]], fov: p.fov }); } basePush(ctx);
      I.bedroomNight(ctx, { set: H, lamp: 3.5, nightlight: 2.5, moon: true, lanternOutside: false });
      // the mole outside, up against the glass (big: its eyes reach the pane), rising into view
      const m = CR.makeMole({ preset: 'old', scale: 1.3, seed: 31, lod: 'hero' }); m.rotation.y = Math.PI; ctx.add(m); ctx.shared.m = m;
      for (const n of ['mound', 'moleShadow']) { const o = m.getObjectByName(n); if (o) o.visible = false; }
      const mx = WIN[0] - 0.05; let mz = WIN[2] + 0.6;
      CR.setMole(m, { emerge: 0.7, open: 1, eyes: 1, rise: 1, look: [0, -10] }); m.position.set(mx, 0.0, mz); m.updateWorldMatrix(true, true);
      // the snout disc stops 6 cm outside the outer glass (it poked through the pane and hid the fog)
      { const bb = new THREE.Box3().setFromObject(m.getObjectByName('snout')); mz += (WIN[2] + 0.06) - bb.min.z; m.position.z = mz; m.updateWorldMatrix(true, true); }
      const eL0 = worldOf(m.getObjectByName('eyeL')), eR0 = worldOf(m.getObjectByName('eyeR')); const eyeY = (eL0.y + eR0.y) / 2;
      const yUp = WIN[1] + 0.08 - eyeY; ctx.shared.yUp = yUp;
      const eL = eL0.clone().add(new THREE.Vector3(0, yUp, 0)), eR = eR0.clone().add(new THREE.Vector3(0, yUp, 0));
      const fog = X.glassFog(ctx, E.theo.glass, { t0: tG, center: [WIN[0] + 0.05, eL.y - 0.12, -13.504 + 0.008], r1: 1.1, grow: 0.35, opacity: 0.5, eyes: [eL, eR], eyeGlow: 1.0, toward: pos }); ctx.add(fog.group); ctx.shared.fog = fog;
      ctx.add(ctx.lights.point({ color: '#ffb347', intensity: 0.8, pos: [mx, WIN[1] - 0.1, WIN[2] + 0.25], decay: 2 }));
      ctx.shared.fx = sparks(ctx, face.clone().add(new THREE.Vector3(0.2, 0.5, 0.3)).toArray(), [1.2, 0.8, 0.6], 6, 's55', { px: [36, 64] });
    },
    update(ctx, t) {
      const s = ctx.shared; const m = s.m; const k = outQuad(clamp01((t + 0.22) / 0.3)); m.position.y = s.yUp * k - 0.25 * (1 - k);
      // the reflector eyes catch the room light (steady glint, a pulse with the breath on "glass"): the star snout hides the eye domes from the lens
      const fl = 0.45 + 0.55 * Math.exp(-Math.pow((t - s.tG - 0.06) / 0.09, 2));
      CR.setMole(m, { t, emerge: 0.7, open: 1, eyes: 1, flash: fl, rise: 1, look: [0, -10], sniff: t > s.tG - 0.05 && t < s.tG + 0.3 ? 1 : 0.3 }); s.fog.update(t); s.fx.update(t);
    },
  },

  // s56 "So I ran back, and they backed off." (62.57-64.10) - high WS: the hero runs back right -> left with the lit gnome and
  // plants his bare feet in the flowerbed on "back"; on "backed off" the circle of light pushes the mounds back like a tide
  // (3 studs in 0.5 s). Push 16 %, crane -0.5 studs.
  ran_back: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx, { bed: 'hole' }); frontDoor(ctx); theoAsleep(ctx, H);
      const tBack = evT(ctx, 'back', 0.533), tBk = evT(ctx, 'backed', 1.017); Object.assign(ctx.shared, { tBack, tBk });
      const P1 = new THREE.Vector3(BED[0] + 0.32, BED[1], BED[2] + 0.28); const dir = new THREE.Vector3(0.33, 0, 1.0).normalize();
      const v = K.RUN_SPEED * S * 0.85; const P0 = P1.clone().addScaledVector(dir, v * tBack); P0.y = 0;
      const posAt = (t) => { if (t >= tBack) return P1.clone(); const q = P0.clone().lerp(P1, t / tBack); const kk = clamp01((t / tBack - 0.82) / 0.18); q.y = BED[1] * kk; return q; };
      ctx.shared.posAt = posAt; const yaw = Math.atan2(-dir.x, -dir.z); ctx.shared.yaw = yaw;
      ctx.shared.yaw2 = yaw + Math.PI * 0.92;   // on the plant he spins round to face the lawn and the mounds (8-frame snap)
      const { hero, g } = heroWithGnome(ctx, { at: P0.toArray(), yaw, face: p.cast[0].face || 'angry' }); ctx.shared.hero = hero; ctx.shared.g = g;
      const sh = sets.contactShadow(ctx, { pos: [P0.x, 0.005, P0.z], radius: 0.42, opacity: 0.4 }); ctx.add(sh); ctx.shared.sh = sh;
      const subj = up(BED, 0, 0, 3); boardCam(ctx, subj, { ref: [0, 0, 1], yaw: c.yaw_deg, dist: c.dist_studs, h: c.height_studs, pitch: c.pitch_deg, fov: p.fov });
      basePush(ctx); ctx.camera.crane(c.drift.crane_studs * S);
      nightRig(ctx, H, 'nightHigh', { lamp: { n: 2 }, window: { n: 1, cd: 2.4, maxD: 10 }, subject: { pos: [P1.x, 1.0, P1.z], cd: 0.6 } });
      ctx.add(ctx.lights.point({ color: '#c8c0ff', intensity: 3.0, pos: [BED[0] - 0.6, 2.4, BED[2] + 2.6], decay: 2 }));   // cool moon fill on the mounds (they read black)
      const GL = grandpaLantern(ctx, g); ctx.shared.GL = GL; ctx.shared.fam = familyLanterns(ctx, H);
      // mounds crowding the bed and the wall under the window; the ring arrives with him (snouts recoil), then the tide
      const f = CR.moleField(ctx, { center: [BED[0], BED[2] + 1.0], size: [26, 20], res: 128, seed: 's56', heads: 'snout' }); ctx.add(f.group);
      // (no travel paths: a pushed mole with a path leaves its push trail as trench ridges)
      const r = makeRng(hash32('p3s56')); const spots = [[-1.3, 0.25], [-0.85, 1.0], [-0.1, 1.3], [0.7, 1.05], [1.25, 0.45], [-1.6, -0.3], [0.2, 0.68]];
      spots.forEach(([dx, dz], i) => { const at = [BED[0] + dx, BED[2] + dz]; const k = f.add({ at, scale: 1.3 + 0.3 * r(), face: [BED[0], BED[2]] }); f.eyes(k, -5, null); f.recoil(k, tBack + 0.02 * i); });
      f.pushBack([P1.x, P1.z], 0, 5 * S + 0.25, tBk, 0.5); ctx.shared.f = f;
      const mc = X.moundCrumbs(ctx, f, { pops: false, rate: 14 }); ctx.add(mc.group); ctx.shared.mc = mc;
      // wet-grass / soil splashes on the plant
      ctx.shared.spl = sets.burst(ctx, { pos: [P1.x, P1.y + 0.04, P1.z], t0: tBack, dur: 0.3, count: 10, spread: 0.35, px: [10, 22], ring: false, core: false, colors: ['#e8f0ff', '#cfe0ff', '#ffffff'], brightness: 1.4, gravity: -0.35, seed: 's56spl' }); ctx.add(ctx.shared.spl);
      ctx.shared.fx = sparks(ctx, [P1.x, 1.0, P1.z + 0.6], [2.6, 1.2, 2.6], 7, 's56', { px: [36, 64] });
    },
    update(ctx, t) {
      const s = ctx.shared; const hero = s.hero; const q = s.posAt(t); hero.position.copy(q); s.sh.position.set(q.x, Math.max(0.005, q.y + 0.005), q.z);
      if (t < s.tBack) { const rc = K.runCycle(t, { period: 0.5, legs: 55 }); K.setPose(hero, { ...HUG, legLx: rc.legLx || 0, legRx: rc.legRx || 0, bodyX: 12, lift: rc.lift || 0 }); hero.rotation.y = s.yaw; }
      else { const u = clamp01((t - s.tBack) / 0.12); const st = { ...HUG, neckX: -4, legLz: 6 * u, legRz: 6 * u, bodyX: 12 * (1 - u) - 4 * Math.sin(Math.PI * u) }; K.setPose(hero, st);
        hero.rotation.y = s.yaw + (s.yaw2 - s.yaw) * outQuad((t - s.tBack) / (8 / 60)); }
      lanternSwing(s.g, t - s.tBack, { amp: 12, decay: 1.1 }); s.GL.update(t); s.fam.update(t); s.f.update(t); s.mc.update(t); s.spl.update(t); s.fx.update(t);
    },
  },

  // s57 "Fine, I'd stand guard till dawn." (64.10-65.43) - MS from the window side: "Fine." Angry brows, he hugs the gnome
  // tighter (4 deg squeeze); behind him across the lawn the truck waits at the kerb, back open (dome light), mounds waiting
  // at the rim of the light. Push 19 %.
  stand_guard: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx, { bed: 'hole' }); frontDoor(ctx); const E = H.ep01; E.truck.ep01.balconyBox.visible = false;
      const HP = new THREE.Vector3(BED[0] + 0.25, 0, BED[2] + 1.72); const tb = V3(E.spots.truckBack);
      const axis = HP.clone().sub(tb).setY(0).normalize();                  // truck -> hero -> camera
      const { hero, g } = heroWithGnome(ctx, { at: HP.toArray(), face: p.cast[0].face || 'angry' }); ctx.shared.hero = hero; ctx.shared.g = g;
      hero.updateWorldMatrix(true, true); const head = worldOf(hero.getObjectByName('head'));
      const { pos } = boardCam(ctx, head.clone().setY(0), { ref: axis.toArray(), yaw: c.yaw_deg, dist: c.dist_studs, h: c.height_studs, pitch: c.pitch_deg, fov: p.fov });
      hero.rotation.y = Math.atan2(pos.x - HP.x, pos.z - HP.z) - 22 * DEG; hero.updateWorldMatrix(true, true);
      // re-aim at his face after the turn, keeping the boarded pitch, and nudge the frame so the truck back shows over his shoulder
      const head2 = worldOf(hero.getObjectByName('head')); const hd = Math.hypot(head2.x - pos.x, head2.z - pos.z); const tgt = head2.clone().lerp(tb, 0.06).add(new THREE.Vector3(-0.14, 0, 0)); tgt.y = pos.y + hd * Math.tan(c.pitch_deg * DEG) - 0.08;
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: p.fov }); basePush(ctx);
      nightRig(ctx, H, 'nightHigh', { lamp: { n: 3 }, window: { n: 0 }, postOpts: CU_GRADE });
      coolRim(ctx, head2.toArray(), { intensity: 1.0 });
      const GL = grandpaLantern(ctx, g, { cd: 1.0, lightOffset: [0, 0.1, 0.25] }); ctx.shared.GL = GL; ctx.shared.fam = familyLanterns(ctx, H);
      // mounds waiting just outside the ring, eyes lit (they carry into s58)
      const f = CR.moleField(ctx, { center: [HP.x, HP.z + 1.5], size: [26, 22], res: 112, seed: 's57', heads: 'snout' }); ctx.add(f.group);
      const L0 = worldOf(g.getObjectByName('lantern')); const R0 = 5 * S + 0.3;
      [[-0.55, 1.0], [0.15, 0.95], [0.75, 1.05], [-1.2, 1.1], [1.25, 1.2]].forEach(([a, sc], i) => { const th = Math.atan2(axis.x, axis.z) + Math.PI + a; const at = [L0.x + Math.sin(th) * R0, L0.z + Math.cos(th) * R0];
        const k = f.add({ at, scale: sc, face: [L0.x, L0.z] }); f.travel(k, [at, [at[0] + 0.05 * Math.cos(i), at[1] + 0.04 * Math.sin(i)]], 0, 0.15); f.eyes(k, -5, null); });
      ctx.shared.f = f; ctx.shared.tF = 0.12;
      ctx.shared.fx = sparks(ctx, head2.clone().lerp(pos, 0.4).toArray(), [1.0, 0.8, 0.5], 6, 's57', { px: [40, 70] });
    },
    update(ctx, t) {
      const s = ctx.shared; const u = t - s.tF; const sq = u < 0 ? 0 : 4 * springStep(u, 2.2, 0.55);
      K.setPose(s.hero, { ...HUG, armLz: HUG.armLz - sq, armRz: HUG.armRz - sq, armLx: HUG.armLx + sq * 0.5, armRx: HUG.armRx + sq * 0.5, neckX: -10, bodyX: 2 });
      lanternSwing(s.g, t + 1.5, { amp: 8, decay: 0.8 }); s.GL.update(t); s.fam.update(t); s.f.update(t); s.fx.update(t);
    },
  },
};
