// EP01 full episode, PART 2 (s25-s41, 26.55-46.30 s): the evening before the move, the empty spot, the run out barefoot,
// Grandpa at the gate facing the truck, "Come on, then", the pick-up across the line, the lawn moves, dozens of mounds,
// the reflector eyes, the snouts, the lantern lights, the moles stop at its edge, every lantern down the street lights
// up except next door.
// Shot list and every decision (camera numbers, cast and faces, light/grade, events with frames, SFX, assets) are in
// episodes/ep01/timeline.json (params of each shot) and episodes/ep01/board.md. Builders are pure functions of shot time
// t (engine/README.md determinism rules): no state between frames, no Math.random / Date; seeded RNGs only.
//
// Sets: our front garden is sets_ep01.heroLot (lot A1 at x = 0; gate (0, -6.4); door (0, 0.32, -13.22); Grandpa's
// bed0 under Theo's window at (-2.67, -12.67); the truck at the kerb with its open back 8 studs left of the gate; next door
// = lot A2 at +X). The two street wides (s35, s40) use sets_ep01.ep01Street (our lot = A3 at x = 5.76, next door A4).
// Continuity kept here (board.md section 5): SOLD sticker on from 27.51 s; the truck at the kerb, back open, dome light on;
// the gate open; the front door banged open in s28 and left open (warm hall light) from then on; Grandpa's bed is the
// empty soil ring from s27; Grandpa at the gate (s29-s30), in the hero's arms from the pick-up (s32) on; every lantern
// unlit until Grandpa's lights on "lit" (s38, 41.76 s); street + family lanterns light in the s40 cascade; next door's
// plastic lanterns never light; hero = heroBarefoot (mustard hoodie, bare feet).
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

const S = C.S, DEG = C.DEG, V3 = C.V3, clamp01 = C.clamp01, smooth = C.smooth, outExpo = C.outExpo, outQuad = C.outQuad;
const lerp = (a, b, k) => a + (b - a) * k;
const up = (p, dy = 0, dx = 0, dz = 0) => [p[0] + dx * S, p[1] + dy * S, p[2] + dz * S];
const SPK = (o = {}) => ({ ...C.SPARK, ...o });

// ------------------------------------------------------------------ staging constants (heroLot world metres)
const GP_GATE = [0.04, 0, -6.46];          // s29-s32: Grandpa's boots on the line in the open gate
const KNEEL_AT = [0, 0, -7.25];            // s31-s33: the hero kneels / stands on the path just inside the gate
const HOLD_AT = [0, 0, -8.6];              // s34-s41: the hero holding Grandpa on the path, 2.2 m inside the gate
const HOLD_OFF = [0, 0.1, 1.12];           // the held gnome in the hero's hips frame (studs): feet at 2.1 studs, the hands meet round his belly
const HUG = { armLx: 58, armRx: 58, armLz: -36, armRz: -36, neckX: -8 };   // both arms round the gnome's belly (hands meet in front)
const STREET_HERO = [5.76, 0, -8.6];       // ep01Street: the same spot on our lot A3
const CU_GRADE = { grade: { temperature: -6, tint: 6 } };   // close-ups keep warm skin / glaze inside the cool night (approved s05 numbers)
const GOLD = { color: '#ff9e1c', width: 0.012, outer: 2.0, peak: 0.75, hold: 0.42 };   // the s15 gold, kept saturated under the night grade

// ------------------------------------------------------------------ helpers
const evT = (ctx, k, fb) => C.evT(ctx, k, fb);
// The house-style push from params.camera.move (mode 'fov' = the engine's 'zoom': no parallax).
function basePush(ctx, o = {}) { const m = ctx.params.camera.move; ctx.camera.push(o.Z ?? m.Z ?? m.base_push ?? 0.19, { mode: m.mode === 'dolly' ? 'dolly' : 'zoom', t0: o.t0, t1: o.t1 }); }
function paramRoll(ctx) { const r = ctx.params.camera.roll; if (r) ctx.camera.rollBy(r.deg[1] - r.deg[0]); }
function sparks(ctx, center, size, count, seed, o = {}) { const f = sets.sparkles(ctx, SPK({ center, size, count, seed, ...o })); ctx.add(f); return f; }
function nightLot(ctx, o = {}) { const H = SE.heroLot(ctx, { tod: 'night', bed: 'empty', truck: 'open', gate: 1.5, sold: -1, ...o }); ctx.add(H); return H; }
// Night rig on a set (preset 'night' or 'nightHigh'), galaxy sky lifted for low cameras.
function nightRig(ctx, set, preset = 'nightHigh', o = {}) {
  const f = preset === 'night' ? sets.nightStreet : sets.nightLawn; const { low, ...rest } = o;
  return f(ctx, { set, skyPreset: low === false ? C.GALAXY : C.GALAXY_LOW, skyOpts: { intensity: 1.6 }, ...rest });
}
// Camera basis at t = 0 (after ctx.camera.set): position, forward, right.
function camBasis(ctx) { ctx.camera.apply(0); const cam = ctx.cam; const pos = cam.position.clone(); const fwd = new THREE.Vector3(0, 0, -1).applyQuaternion(cam.quaternion); const right = new THREE.Vector3(1, 0, 0).applyQuaternion(cam.quaternion); return { pos, fwd, right }; }
// Warm face key (bible: warm key on faces, cool set): a point light upper front-left of the subject as seen from the camera.
function warmKey(ctx, subject, { cd = 2.6, d = 0.8, color = '#ffc08a', side = 35, el = 35 } = {}) {
  const B = camBasis(ctx); const s = V3(subject); const back = B.fwd.clone().negate(); back.y = 0; back.normalize();
  const dir = back.clone().addScaledVector(B.right, -Math.tan(side * DEG)); dir.y = Math.tan(el * DEG); dir.normalize();
  return ctx.add(ctx.lights.point({ color, intensity: cd, pos: s.clone().addScaledVector(dir, d).toArray(), decay: 2 }));
}
// Cool moon rim from behind-right of the subject.
function coolRim(ctx, subject, { intensity = 0.8, color = '#8a90ff' } = {}) {
  const B = camBasis(ctx); const s = V3(subject); const p = s.clone().addScaledVector(B.fwd, 6).addScaledVector(B.right, 5).add(new THREE.Vector3(0, 4, 0));
  return ctx.add(ctx.lights.sun({ color, intensity, pos: p.toArray(), target: s.toArray(), shadow: false }));
}

// Our front door after s28: the leaf banged open (outward, hinge on the left) and the warm hall light in the doorway.
// The original door is part of the merged lot mesh, so a leaf copy covers it and the doorway glow sits just in front of it.
// k(t) = open amount 0..1 (overshoot ok). door = the lot's door point (world metres, deck height).
function frontDoor(ctx, door, { k = () => 1, light = 3.2 } = {}) {
  const W = 1.27, Hh = 2.39, z = door[2] - 0.045; const g = new THREE.Group(); g.name = 'p2FrontDoor';
  const glowMat = ctx.cache('p2:doorGlowMat', () => new THREE.MeshBasicMaterial({ color: new THREE.Color('#ffc890').multiplyScalar(1.35), fog: false }));
  const glow = new THREE.Mesh(new THREE.PlaneGeometry(W, Hh), glowMat); glow.position.set(door[0], door[1] + Hh / 2, z + 0.01); glow.renderOrder = 2; g.add(glow);
  const leafMat = ctx.cache('p2:doorLeafMat', () => new THREE.MeshStandardMaterial({ map: doorTex('#7a2a20'), roughness: 0.5 }));
  const edgeMat = ctx.cache('p2:doorEdgeMat', () => new THREE.MeshStandardMaterial({ color: '#5a1a14', roughness: 0.6 }));
  const hinge = new THREE.Group(); hinge.position.set(door[0] - W / 2, door[1], z + 0.03); g.add(hinge);
  const leaf = new THREE.Mesh(new THREE.BoxGeometry(W, Hh, 0.05), [edgeMat, edgeMat, edgeMat, edgeMat, leafMat, leafMat]); leaf.position.set(W / 2, Hh / 2, 0); hinge.add(leaf);
  const pl = ctx.add(ctx.lights.point({ color: '#ffc890', intensity: 0, pos: [door[0], door[1] + 1.7, door[2] + 0.55], decay: 2 }));
  const halo = C.pxSprite(C.addSpriteMat(ctx.tex.radialGlow({ falloff: 2.2 }), '#ffcf98', 0.8), 260); halo.position.set(door[0], door[1] + 1.4, z + 0.15); halo.renderOrder = 6; g.add(halo);
  g.update = (t) => { const a = k(t); hinge.rotation.y = -1.75 * a; const on = a > 0.02; glow.visible = on; pl.intensity = on ? light * Math.min(1, a * 1.5) : 0; pl.visible = on; halo.visible = on; halo.material.opacity = 0.35 * Math.min(1, a); };
  g.update(0); ctx.add(g); return g;
}
const LOT_DOOR = [0, 0.32, -13.216];
const streetDoor = (R) => { const l = R.userData.lots.find((x) => x.id === 'A3'); return [l.door[0], 0.32, l.door[2]]; };

// The hero (heroBarefoot) with Grandpa held in front of his belly, parented to the hips (so lean / lift carry him).
function heroWithGnome(ctx, { at = HOLD_AT, yaw = 0, face = 'shock', pose = HUG, gnome = {} } = {}) {
  const hero = K.makeCharacter('heroBarefoot', { face }); hero.position.set(at[0], at[1], at[2]); hero.rotation.y = yaw; K.setPose(hero, pose); ctx.add(hero);
  const g = K.makeGnome('grandpa', { units: 'stud', lantern: 0, wear: 0.12, ...gnome }); C.softenBeard(g);
  const hips = hero.getObjectByName('hips'); g.position.set(...HOLD_OFF); hips.add(g);
  hero.updateWorldMatrix(true, true); return { hero, g };
}
const worldOf = (o) => { o.updateWorldMatrix(true, false); return o.getWorldPosition(new THREE.Vector3()); };
const gnomeEyes = (g) => C.eyesOf(g);
// The lantern swinging on its ring (pendulum, decaying), u = seconds since the swing started.
function lanternSwing(g, u, { amp = 12, freq = 1.4, decay = 1.0, phase = Math.PI / 2 } = {}) {
  const L = g.getObjectByName('lantern'); if (!L) return; const a = amp * DEG * Math.exp(-decay * Math.max(0, u)) * Math.sin(2 * Math.PI * freq * u + phase);
  L.rotation.z = a; L.rotation.x = 0.3 * a;
}

// ==================================================================================================================
export const PART = 2;
export const builders = {

  // s25 "Then, the night before we moved," (26.55-27.80) - dusk WS from across the street: our house, the SOLD sticker
  // slaps across the COMES WITH ANCESTORS board on "moved", the truck at the kerb (back open, BALCONY GNOME box) in the left
  // third, Theo at the pickets hugging his whale, staring at Grandpa in his flowerbed. Dolly push 15 % + 0.4-stud truck.
  sold_truck_dusk: {
    quality: { shadows: 'pcfsoft' },
    build(ctx) {
      const p = ctx.params, c = p.camera; const tSold = evT(ctx, 'moved', 0.96);
      const H = SE.heroLot(ctx, { tod: 'dusk', bed: 'grandpa', truck: 'open', sold: tSold, gate: 0 }); ctx.add(H); const E = H.ep01, sp = E.spots; ctx.shared.H = H;
      // Theo on the sidewalk at the pickets left of the gate, body 3/4 to the street, head turned to Grandpa
      const theo = K.makeCharacter('theo', { face: 'wonder' }); K.addBadge6(theo); const wh = CR.stuffedWhale(); CR.holdWhale(theo, wh, 'hug');
      const TH = [-2.35, 0, -5.98]; theo.position.set(...TH); theo.rotation.y = Math.PI - 0.55; K.setPose(theo, { ...K.POSES.hug, neckY: 30, neckX: 2 }); ctx.add(theo);
      ctx.add(sets.contactShadow(ctx, { pos: [TH[0], 0.005, TH[2]], radius: 0.28, opacity: 0.35 }));
      const cp = new THREE.Vector3(3.0, 2.3, 5.6); const ang = 22 * DEG; const tg = cp.clone().add(new THREE.Vector3(-Math.sin(ang) * 14, -14 * Math.tan(3.5 * DEG), -Math.cos(ang) * 14));
      ctx.camera.set({ pos: cp.toArray(), target: tg.toArray(), fov: p.fov }); basePush(ctx); ctx.camera.truck(c.drift.truck_studs * S);
      ctx.shared.rig = SE.heroLight(ctx, H, {});
      const g = E.gnomes.grandpa; if (g) { K.setGnomeGaze(g, 0, 4); ctx.shared.g = g; }
      ctx.shared.fx = sparks(ctx, up(sp.board, 0.6, 1.0, 2.5), [5.0, 2.4, 3.0], 6, 's25', { px: [45, 75] });
    },
    update(ctx, t) { ctx.shared.H.ep01.update(t); ctx.shared.fx.update(t); if (ctx.shared.g) K.gnomeIdle(ctx.shared.g, t, { seed: 's25' }); },
  },

  // s26 "at nine," (27.80-28.25) - our hall at night: the wall clock (Roman numerals) ticks onto IX:00 on "nine"; below it
  // the rolled sleeping bag and three THEO boxes by the front door. Insert, push 25 %.
  hall_clock: {
    build(ctx) {
      const R = I.hall(ctx); ctx.add(R); ctx.shared.R = R; ctx.shared.tN = evT(ctx, 'nine', 0.133);
      const A = R.userData.anchors; const tg = [A.clock[0] * 0.55 + A.boxes[0] * 0.2 + A.sleepingBag[0] * 0.25, A.clock[1] * 0.58 + A.sleepingBag[1] * 0.42, A.clock[2]];
      const dist = 4.4; ctx.camera.set({ pos: [tg[0], tg[1] + dist * Math.tan(10 * DEG), tg[2] + dist], target: tg, fov: ctx.params.fov }); basePush(ctx);
      I.bedroomNight(ctx, { room: R, lamp: 3 }); ctx.add(ctx.lights.point({ color: '#ffe6c0', intensity: 3, pos: A.lamp, decay: 2 }));
      ctx.shared.fx = sparks(ctx, [A.clock[0], A.clock[1] - 0.9, A.clock[2] + 1.2], [2.0, 2.4, 1.2], 9, 's26', { px: [45, 80] });
    },
    update(ctx, t) { ctx.shared.R.ep01.tickToNine(t, ctx.shared.tN); ctx.shared.fx.update(t); },
  },

  // s27 "his spot was empty" (28.25-29.73) - looking down into the flowerbed from the lawn: the ring of flat pale soil with
  // two boot dents among the tulips, the lit sill of Theo's window across the top; held through the silence beat.
  empty_spot: {
    build(ctx) {
      const H = nightLot(ctx); const sp = H.ep01.spots;
      const c = ctx.params.camera; const B = V3(sp.bed0); const pos = B.clone().add(new THREE.Vector3(0, c.height_studs * S, c.dist_studs * S * 1.28));
      const tgt = pos.clone().add(new THREE.Vector3(0, -Math.tan(27 * DEG) * 2, -2)); ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: ctx.params.fov }); basePush(ctx);
      nightRig(ctx, H, 'nightHigh', { window: { n: 1, cd: 2.4, maxD: 10 } });
      warmKey(ctx, up(sp.bed0, 0.2), { cd: 1.2, d: 1.0, color: '#ffc896' });
      ctx.shared.fx = sparks(ctx, up(sp.bed0, 1.5, 0, 1.3), [1.6, 0.9, 1.0], 7, 's27', { px: [45, 80] });
    },
    update(ctx, t) { ctx.shared.fx.update(t); },
  },

  // s28 "So I ran out barefoot, after dark." (29.73-31.45) - ground level on the path: the front door bangs open on "ran"
  // (warm hall light), the hero sprints down the porch and across the wet lawn toward the lens (first bare foot lands on
  // "barefoot", then every 0.25 s), the camera tracks back 9.5 studs at boot level through the open gate.
  run_out_barefoot: {
    build(ctx) {
      const p = ctx.params; const H = nightLot(ctx); ctx.shared.H = H;
      const tBang = evT(ctx, 'ran', 0.383), tFoot = evT(ctx, 'barefoot', 0.75); const T = ctx.shot.duration;
      const door = frontDoor(ctx, LOT_DOOR, { k: (t) => (t < tBang ? 0 : springStep(t - tBang, 2.2, 0.38)) }); ctx.shared.door = door;
      const hero = K.makeCharacter('heroBarefoot', { face: 'shock' }); ctx.add(hero); ctx.shared.hero = hero;
      const z0 = -13.05, zFoot = -11.12, deck = 0.32; const v1 = (zFoot - z0) / Math.max(0.2, tFoot - tBang); const v2 = 4.7;
      const run = (t) => { const u = t - tBang; if (u < 0) return { z: z0, y: deck }; if (t < tFoot) { const z = z0 + v1 * u; const k = clamp01((z + 11.75) / (11.75 + zFoot)); return { z, y: deck * (1 - k * k) + 0.18 * Math.sin(Math.PI * k) }; } return { z: zFoot + v2 * (t - tFoot), y: 0 }; };
      ctx.shared.run = run; ctx.shared.tBang = tBang; ctx.shared.tFoot = tFoot;
      // boot-level tracking: back 9.5 studs over the shot (linear), a hair right of the path
      const zc0 = -7.45, zc1 = zc0 + p.camera.drift.dolly_back_studs * S; const h = p.camera.height_studs * S;
      const tgt = new THREE.Vector3();
      ctx.camera.set({ pos: (t, o) => (o || new THREE.Vector3()).set(0.2, h, lerp(zc0, zc1, t / T)),
        target: (t, o) => { const r = run(t); const k = smooth((t - tBang + 0.05) / 0.4); tgt.set(0, lerp(1.25, r.y + 0.86, k), lerp(-13.2, r.z, k)); return (o || new THREE.Vector3()).copy(tgt); }, fov: p.fov });
      ctx.camera.push(p.camera.move.Z, { mode: 'zoom' });
      nightRig(ctx, H, 'nightHigh', { lantern: { n: 1, cd: 2.5 } });
      const key = ctx.add(ctx.lights.point({ color: '#ffc08a', intensity: 2.2, pos: [0, 1.4, zc0], decay: 2 })); ctx.shared.key = key; ctx.shared.camZ = (t) => lerp(zc0, zc1, t / T);
      // wet-grass splashes on each footfall (every 0.25 s from "barefoot")
      ctx.shared.spl = []; for (let k = 0; k < 5; k++) { const tk = tFoot + 0.25 * k; if (tk > T) break; const r = run(tk); const b = sets.burst(ctx, { pos: [(k % 2 ? 0.13 : -0.13), 0.04, r.z + 0.05], t0: tk, dur: 0.3, count: 7, spread: 0.2, px: [10, 22], ring: false, core: false, colors: ['#e8f0ff', '#cfe0ff', '#ffffff'], brightness: 1.5, gravity: -0.35, seed: 's28spl' + k }); ctx.add(b); ctx.shared.spl.push(b); }
      ctx.shared.fx = sparks(ctx, [0.2, 0.35, -8.6], [2.2, 0.6, 3.0], 8, 's28', { px: [35, 65] });
    },
    update(ctx, t) {
      const s = ctx.shared; s.door.update(t); const r = s.run(t); const hero = s.hero; s.key.position.set(-0.45, 1.45, s.camZ(t) - 0.3);
      hero.visible = t >= s.tBang - 1 / 60; hero.position.set(0, r.y, r.z); hero.rotation.y = 0;
      K.setPose(hero, { ...K.runCycle(t, { period: 0.5, legs: 60, arms: 55, phase: 0.25 }), bodyX: 10, neckX: 4 });
      for (const b of s.spl) b.update(t); s.fx.update(t);
    },
  },

  // s29 "He was at the gate, facing the moving truck." (31.45-33.20) - THUMBNAIL: low OTS behind Grandpa, boots on the
  // shimmering property line in the open gate, staring up at the truck's open back (cargo dome light, BALCONY GNOME box).
  gate_truck_thumb: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); const E = H.ep01; frontDoor(ctx, LOT_DOOR);
      const tb = V3(E.spots.truckBack); const g = K.makeGnome('grandpa', { lantern: 0, wear: 0.12 }); C.softenBeard(g);
      g.position.set(...GP_GATE); g.rotation.y = Math.atan2(tb.x - GP_GATE[0], tb.z - GP_GATE[2]); ctx.add(g); ctx.shared.g = g;
      ctx.add(sets.contactShadow(ctx, { pos: [GP_GATE[0], 0.006, GP_GATE[2]], radius: 0.24, opacity: 0.4 }));
      K.setGnomeHead(g, 0, 6, 0); g.updateWorldMatrix(true, true); C.gazeAt(g, tb.clone().add(new THREE.Vector3(0, 0.3, 0)));
      const eyes = gnomeEyes(g); const fwd = new THREE.Vector3(Math.sin(g.rotation.y), 0, Math.cos(g.rotation.y));
      // OTS 150 deg round his front; 3 studs out (at the board's 1.8 his head and the truck back cannot share the 9:16 frame)
      const back = fwd.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), -c.yaw_deg * DEG);
      const pos = eyes.clone().addScaledVector(back, 3.0 * S); pos.y = c.height_studs * S;
      const tbc = tb.clone().add(new THREE.Vector3(0, 0.25, 0)); const head = eyes.clone().add(new THREE.Vector3(0, 0.06, 0));
      const az = (q) => Math.atan2(q.x - pos.x, q.z - pos.z), el = (q) => Math.atan2(q.y - pos.y, Math.hypot(q.x - pos.x, q.z - pos.z));
      let a0 = az(head), a1 = az(tbc); if (a1 - a0 > Math.PI) a1 -= 2 * Math.PI; if (a0 - a1 > Math.PI) a1 += 2 * Math.PI;
      const ya = a0 + 0.43 * (a1 - a0), pa = 0.5 * (el(head) + el(tbc)) + 2 * DEG;
      const look = pos.clone().add(new THREE.Vector3(Math.sin(ya) * Math.cos(pa), Math.sin(pa), Math.cos(ya) * Math.cos(pa)));
      ctx.camera.set({ pos: pos.toArray(), target: look.toArray(), fov: p.fov }); basePush(ctx); ctx.camera.crane(c.drift.crane_studs * S);
      nightRig(ctx, H, 'night', { lamp: { n: 3 }, postOpts: CU_GRADE });
      // warm house spill on his back + hat from behind the lens; the truck dome is his rim
      warmKey(ctx, eyes.toArray(), { cd: 1.6, d: 1.0, color: '#ffc896', side: 20, el: 40 });
      const PL = X.propertyLine(ctx, { a: [-0.66, -6.4], b: [0.66, -6.4], opacity: 0.028 }); ctx.add(PL.group); ctx.shared.PL = PL;
      ctx.shared.fx = sparks(ctx, eyes.clone().lerp(tb, 0.35).toArray(), [1.4, 1.0, 1.2], 8, 's29', { px: [45, 85] });
    },
    update(ctx, t) { K.gnomeIdle(ctx.shared.g, t, { seed: 's29' }); ctx.shared.PL.update(t); ctx.shared.fx.update(t); },
  },

  // s30 "He was trying to come with me." (33.20-34.35) - CU of his painted face, front and low, eyes up at the truck; on
  // "with" a dewdrop wells at his left eye (0.15 s) and runs down the cheek into the beard (0.45 s). Push 24 %, roll +1.
  gnome_tear: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); const E = H.ep01; frontDoor(ctx, LOT_DOOR);
      const tb = V3(E.spots.truckBack); const g = K.makeGnome('grandpa', { lantern: 0, wear: 0.12 }); C.softenBeard(g);
      g.position.set(...GP_GATE); g.rotation.y = Math.atan2(tb.x - GP_GATE[0], tb.z - GP_GATE[2]); ctx.add(g); ctx.shared.g = g;
      K.setGnomeGaze(g, 0, 15); g.updateWorldMatrix(true, true);
      const eyes = gnomeEyes(g); const fwd = new THREE.Vector3(Math.sin(g.rotation.y), 0, Math.cos(g.rotation.y));
      const dir = fwd.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), c.yaw_deg * DEG);
      const nose = eyes.clone().addScaledVector(fwd, 0.04); nose.y -= 0.03;
      const pos = nose.clone().addScaledVector(dir, c.dist_studs * S); pos.y = c.height_studs * S;
      const tgt = eyes.clone(); const hd = Math.hypot(tgt.x - pos.x, tgt.z - pos.z); tgt.y = pos.y + hd * Math.tan(c.pitch_deg * DEG) - 0.11;
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: p.fov }); basePush(ctx); paramRoll(ctx);
      nightRig(ctx, H, 'night', { lamp: { n: 2 }, skyOpts: { intensity: 1.8 }, postOpts: CU_GRADE });
      warmKey(ctx, nose.toArray(), { cd: 2.2, d: 0.75 }); coolRim(ctx, nose.toArray(), { intensity: 0.9 });
      const T = X.dewTear(ctx, g, { eye: 'L', t0: evT(ctx, 'with', 0.8), dur: 0.6, swell: 0.15, size: 0.34, opacity: 0.6 }); ctx.add(T.group); ctx.shared.T = T;
      ctx.shared.fx = sparks(ctx, nose.clone().lerp(pos, 0.45).toArray(), [0.9, 0.8, 0.3], 8, 's30', { drift: [0.02, 0.05] });
    },
    update(ctx, t) { K.gnomeIdle(ctx.shared.g, t, { seed: 's30', amp: 0.3 }); ctx.shared.T.update(t); ctx.shared.fx.update(t); },
  },

  // s31 "Come on, then." (34.35-34.93) - Grandpa's POV from the gate, gnome eye level: the hero kneeling on the path holds
  // out both arms toward the lens (70 deg), heartfelt, the open door's warm light behind him. Push 18 %.
  hero_arms_out: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); frontDoor(ctx, LOT_DOOR);
      const hero = K.makeCharacter('heroBarefoot', { face: p.cast[0].face || 'heartfelt' }); hero.position.set(...KNEEL_AT); hero.rotation.y = 0;
      K.setPose(hero, { ...K.POSES.kneel, bodyX: 22, armLx: 66, armRx: 66, armLz: -30, armRz: -30, neckX: -4 }); ctx.add(hero); ctx.shared.hero = hero;
      ctx.add(sets.contactShadow(ctx, { pos: [KNEEL_AT[0], 0.005, KNEEL_AT[2] + 0.1], radius: 0.5, opacity: 0.35 }));
      const pos = [KNEEL_AT[0], c.height_studs * S, KNEEL_AT[2] + c.dist_studs * S]; const hd = c.dist_studs * S;
      const tgt = [KNEEL_AT[0], pos[1] + hd * Math.tan(c.pitch_deg * DEG), KNEEL_AT[2]];
      ctx.camera.set({ pos, target: tgt, fov: p.fov }); basePush(ctx);
      nightRig(ctx, H, 'night', { lamp: { n: 2 }, postOpts: CU_GRADE });
      warmKey(ctx, [KNEEL_AT[0], 1.05, KNEEL_AT[2]], { cd: 5.0, d: 0.85 });
      ctx.shared.fx = sparks(ctx, [0, 0.8, KNEEL_AT[2] + 0.8], [1.6, 1.0, 0.9], 9, 's31');
    },
    update(ctx, t) { ctx.shared.fx.update(t); },
  },

  // s32 "I picked him up." (34.93-35.60) - MS from the sidewalk: the hero kneels behind Grandpa, reaches; on "picked" a gold
  // ripple runs along the property line and its flash hides the hand-off: Grandpa is in his arms (hug, 8 frames outQuad)
  // and he stands up; his arms and the gnome start to glow gold.
  pick_up: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); const E = H.ep01; frontDoor(ctx, LOT_DOOR);
      const tPick = evT(ctx, 'picked', 0.153); ctx.shared.tPick = tPick;
      const tb = V3(E.spots.truckBack); const g0 = K.makeGnome('grandpa', { lantern: 0, wear: 0.12 }); C.softenBeard(g0);
      g0.position.set(...GP_GATE); g0.rotation.y = Math.atan2(tb.x - GP_GATE[0], tb.z - GP_GATE[2]); ctx.add(g0); ctx.shared.g0 = g0; K.setGnomeGaze(g0, 0, 10);
      const sh0 = sets.contactShadow(ctx, { pos: [GP_GATE[0], 0.006, GP_GATE[2]], radius: 0.24, opacity: 0.4 }); ctx.add(sh0); ctx.shared.sh0 = sh0;
      const { hero, g } = heroWithGnome(ctx, { at: KNEEL_AT, face: p.cast[0].face || 'heartfelt', pose: HUG }); ctx.shared.hero = hero; ctx.shared.g = g;
      ctx.add(sets.contactShadow(ctx, { pos: [KNEEL_AT[0], 0.005, KNEEL_AT[2]], radius: 0.45, opacity: 0.35 }));
      const subj = new THREE.Vector3(0.0, 0.0, -6.95); const yaw = c.yaw_deg * 0.6 * DEG, R = c.dist_studs * S;
      const pos = new THREE.Vector3(subj.x + Math.sin(yaw) * R, c.height_studs * S, subj.z + Math.cos(yaw) * R);
      const tgt = subj.clone(); tgt.y = pos.y - R * Math.tan(-c.pitch_deg * DEG) - 0.35;
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: p.fov }); basePush(ctx);
      nightRig(ctx, H, 'night', { lamp: { n: 3 }, postOpts: CU_GRADE });
      warmKey(ctx, [0, 1.05, -7.1], { cd: 5.0, d: 1.0 });
      const PL = X.propertyLine(ctx, { a: [-0.66, -6.4], b: [0.66, -6.4] }); PL.part(tPick, [GP_GATE[0], 0.32, GP_GATE[2]]); ctx.add(PL.group); ctx.shared.PL = PL;
      const GO = X.goldOutline(ctx, [hero.getObjectByName('armL'), hero.getObjectByName('armR'), g], { t0: tPick, sparkles: 6, ...GOLD });  ctx.add(GO.group); ctx.shared.GO = GO;
      ctx.shared.fx = sparks(ctx, [0, 1.0, -6.6], [1.6, 1.2, 1.0], 8, 's32');
      const kneelReach = { ...K.POSES.kneel, bodyX: 24, armLx: 68, armRx: 68, armLz: -14, armRz: -14, neckX: -4 };
      ctx.shared.pose = (t) => { if (t < tPick) return kneelReach; const ua = outQuad((t - tPick) / (8 / 60)); const ub = outQuad((t - tPick - 0.04) / 0.26);
        const arms = K.mixPose(kneelReach, HUG, ua); const legs = K.mixPose(kneelReach, {}, ub); return { ...arms, legLx: legs.legLx || 0, legRx: legs.legRx || 0, lift: legs.lift || 0, bodyX: legs.bodyX || 0, neckX: lerp(-4, -8, ua) }; };
    },
    update(ctx, t) {
      const s = ctx.shared; const held = t >= s.tPick; s.g0.visible = s.sh0.visible = !held; s.g.visible = held;
      K.setPose(s.hero, s.pose(t)); if (held) lanternSwing(s.g, t - s.tPick, { amp: 14 }); K.gnomeIdle(s.g0, t, { seed: 's32' });
      s.PL.update(t); s.GO.update(t); s.fx.update(t);
    },
  },

  // s33 "Only family can." (35.60-36.70) - CU from slightly high: his arms round the gnome outlined in gold (the s15 callback),
  // the lantern swinging on its ring (+-12 deg at 1.4 Hz, decaying), still unlit. Push 20 %, roll -1.
  gold_arms: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); frontDoor(ctx, LOT_DOOR);
      const { hero, g } = heroWithGnome(ctx, { at: KNEEL_AT, face: 'heartfelt' }); ctx.shared.g = g;
      const subj = worldOf(g).add(new THREE.Vector3(0, 0.27, 0.0)); const yaw = c.yaw_deg * DEG, R = c.dist_studs * S * 1.35;
      const pos = new THREE.Vector3(subj.x + Math.sin(yaw) * R, subj.y + R * Math.tan(-c.pitch_deg * DEG), subj.z + Math.cos(yaw) * R);
      ctx.camera.set({ pos: pos.toArray(), target: subj.toArray(), fov: p.fov }); basePush(ctx); paramRoll(ctx);
      nightRig(ctx, H, 'night', { lamp: { n: 2 }, low: false, postOpts: CU_GRADE });
      warmKey(ctx, subj.toArray(), { cd: 3.2, d: 0.75 });
      const GO = X.goldOutline(ctx, [hero.getObjectByName('armL'), hero.getObjectByName('armR'), g], { t0: -0.06, sparkles: 8, ...GOLD }); ctx.add(GO.group); ctx.shared.GO = GO;
    },
    update(ctx, t) { lanternSwing(ctx.shared.g, t, { amp: 12, decay: 0.9 }); ctx.shared.GO.update(t); },
  },

  // s34 "Then the lawn moved." (36.70-37.63) - ground level across our lawn: the turf bulges like a duvet, a long wave of
  // mounds rolling toward the house past the hero (small at frame left, hugging Grandpa, frozen in shock); on "moved" the
  // bulges surge 0.8 stud and the camera shakes (+-8 px, spikes, decaying 0.5 s).
  lawn_moves: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); frontDoor(ctx, LOT_DOOR); const tM = evT(ctx, 'moved', 0.58); ctx.shared.tM = tM;
      heroWithGnome(ctx, { at: HOLD_AT, face: 'shock' });
      ctx.add(sets.contactShadow(ctx, { pos: [HOLD_AT[0], 0.005, HOLD_AT[2]], radius: 0.4, opacity: 0.35 }));
      // across the lawn from its right edge, looking along it (-X): house to the right, fence + street to the left, the hero
      // small at frame left; the wave front rolls left -> right toward the house (screen direction: house ahead / right)
      const h = 1.55 * S; const pos = [4.6, h, -6.8]; const ang = 57 * DEG; const L = 6;
      const tgt = [pos[0] - Math.sin(ang) * L, h + L * Math.tan(1.5 * DEG), pos[2] - Math.cos(ang) * L];
      ctx.camera.set({ pos, target: tgt, fov: p.fov }); basePush(ctx);
      ctx.camera.shake({ t0: tM, dur: 0.5, rot: 0.35, pos: 0.004, px: 8, freq: 16, seed: 34 }).shake({ t0: tM, dur: 0.12, rot: 0.2, px: 12, freq: 30, seed: 35 });
      nightRig(ctx, H, 'nightHigh', {});
      ctx.add(ctx.lights.point({ color: '#ffc896', intensity: 2.6, pos: [3.4, 1.1, -6.6], decay: 2 })); // the street lamp's spill over the fence onto the near humps
      const f = CR.moleField(ctx, { center: [0.3, -10.0], size: [34, 20], res: 128, seed: 's34', heads: false }); ctx.add(f.group);
      const lane = [[3.25, 1.0], [2.15, 1.1], [1.05, 0.95], [-1.0, 1.05], [-2.1, 1.0], [-3.2, 1.12], [-4.3, 0.95]];
      ctx.shared.h0 = []; ctx.shared.nWave = lane.length;
      lane.forEach(([x, sc], i) => { const st = [x, -6.9 - 0.12 * (i % 3)]; const en = [x * 0.95, -12.4]; const k = f.add({ at: st, scale: 1.8 * sc, height: 0.6 }); f.travel(k, [st, en], -1.0 - 0.05 * (i % 4), 3.1); ctx.shared.h0.push(0.58 + 0.08 * ((i * 5) % 3)); });
      // two broad duvet swells further back, under the beds side of the lawn
      for (const [x, z, sc] of [[-2.2, -11.2, 2.6], [2.6, -11.0, 2.4]]) { const k = f.add({ at: [x, z], scale: sc, height: 0.3 }); f.travel(k, [[x, z], [x * 0.95, -12.6]], -0.6, 1.4); ctx.shared.h0.push(0.26); }
      const sb = X.soilBurst(ctx, { bursts: lane.map(([x], i) => ({ pos: [x, 0.14, -8.55 - 0.1 * (i % 3)], t0: tM + 0.015 * i, count: 10, spread: 0.9, apex: 1.0, puffs: 1 })), seed: 's34soil' }); ctx.add(sb.group); ctx.shared.sb = sb;
      ctx.shared.fx = sparks(ctx, [2.6, 0.55, -9.6], [2.4, 0.8, 2.6], 7, 's34', { px: [40, 70] });
      ctx.shared.f = f; const mc = X.moundCrumbs(ctx, f, { pops: false, rate: 14 }); ctx.add(mc.group); ctx.shared.mc = mc;
    },
    update(ctx, t) {
      const s = ctx.shared; const surge = t < s.tM ? 0 : 0.8 * springStep(t - s.tM, 2.6, 0.45);
      s.f.moles.forEach((m, i) => { m.height = s.h0[i] + (i < s.nWave ? surge : surge * 0.5); });
      s.f.update(t); s.mc.update(t); s.sb.update(t); s.fx.update(t);
    },
  },

  // s35 "Dozens of mounds," (37.63-38.57) - crane up and back over the lawns of our street (x2.5 pull-back outExpo, half done
  // in 0.1 s, +18 studs up, + a linear 8 % push): dozens of mounds push up across our lawn and the neighbours', staggered in
  // waves from "mounds", crumbs popping off their tops; the hero tiny on our path.
  mounds_dozens: {
    build(ctx) {
      const p = ctx.params, c = p.camera, mv = c.move; const R = SE.ep01Street(ctx, { tod: 'night', lanterns: 0, truck: 'open', skip: ['A3.bed0'] }); ctx.add(R); ctx.shared.R = R;
      frontDoor(ctx, streetDoor(R)); heroWithGnome(ctx, { at: STREET_HERO, face: 'shock' });
      const tM = evT(ctx, 'mounds', 0.447);
      const hero = V3(STREET_HERO); const T0 = hero.clone().add(new THREE.Vector3(-0.5, 0.35, 0));
      const P0 = hero.clone().add(new THREE.Vector3(2.9, c.height_studs * S, 1.0));
      const P1 = T0.clone().add(P0.clone().sub(T0).multiplyScalar(mv.x)).add(new THREE.Vector3(0, mv.crane_up_studs * S, 0));
      const U = (t) => { const u = clamp01((t - mv.t0) / (mv.t1 - mv.t0)); return 0.8 * outExpo(u) + 0.2 * outQuad(u); };
      ctx.camera.set({ pos: (t, o) => (o || new THREE.Vector3()).copy(P0).lerp(P1, U(t)), target: (t, o) => (o || new THREE.Vector3()).copy(T0).add(new THREE.Vector3(-3.4 * U(t), 0, -0.5 * U(t))), fov: p.fov });
      ctx.camera.push(0.08, { mode: 'zoom' });
      nightRig(ctx, R, 'night', { low: false, lamp: { n: 4 } });
      // fields on the front lawns of A1..A4 (+ across the street B2, B3); waves of risers from "mounds"
      const r = makeRng(hash32('p2s35')); const fields = []; const lots = R.userData.lots.filter((l) => ['A1', 'A2', 'A3', 'A4', 'B2', 'B3'].includes(l.id));
      let wave = 0;
      for (const l of lots) {
        const sgn = l.side === 'A' ? 1 : -1; const cz = l.gate[2] - sgn * 3.3; const f = CR.moleField(ctx, { center: [l.gate[0], cz], size: [34, 19], res: 80, seed: 's35' + l.id, heads: false }); ctx.add(f.group);
        const n = l.id === 'A3' ? 8 : 9;
        for (let i = 0; i < n; i++) { let x = l.gate[0] + (r() - 0.5) * 10.0; const z = cz + (r() - 0.5) * 4.8; if (l.id === 'A3' && Math.abs(x - hero.x) < 1.2 && Math.abs(z - hero.z) < 1.2) x += 2.2;
          const k = f.add({ at: [x, z], scale: 1.15 + 0.5 * r(), height: 0.85 + 0.35 * r() });
          if (l.id === 'A3' && i < 2) { f.travel(k, [[x, z], [x * 0.98, z - 1.5 * sgn]], -1.5, 2.6); } // the s34 wave, already up
          else { f.rise(k, tM + 0.05 * (wave % 7) + 0.02 * r(), 0.42); wave++; }
        }
        fields.push(f);
      }
      ctx.shared.fields = fields; ctx.shared.mcs = fields.map((f) => { const m = X.moundCrumbs(ctx, f, { pops: true, popCount: 12, rate: 10 }); ctx.add(m.group); return m; });
      ctx.shared.fx = sparks(ctx, up(STREET_HERO, 3.0, -3, 2), [8, 3, 6], 9, 's35', { px: [40, 70] });
    },
    update(ctx, t) { const s = ctx.shared; s.fields.forEach((f, i) => { f.update(t); s.mcs[i].update(t); }); s.fx.update(t); },
  },

  // s36 "with eyes like bike reflectors." (38.57-39.95) - right in front of the lens a mound; on "eyes" two round amber
  // reflector eyes light up in the turf (3 frames); on "reflectors" a sweep of light flashes them (star glints, 0.25 s).
  // A street lamp behind the lens makes them retro-reflect. Strong push 28 %.
  reflector_eyes: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); frontDoor(ctx, LOT_DOOR);
      const M = [2.35, 0, -9.75]; const m = CR.makeMole({ preset: 'lawn', seed: 7, lod: 'hero' }); m.position.set(...M); m.rotation.y = -0.12; ctx.add(m); ctx.shared.m = m;
      const sn = m.getObjectByName('snout'); if (sn) sn.visible = false;            // the snout stays under the turf until s37
      const tE = evT(ctx, 'eyes', 0.15), tR = evT(ctx, 'reflectors', 0.823); ctx.shared.cue = { eyesOn: tE, flash: tR };
      CR.animateMole(m, 0, ctx.shared.cue); m.updateWorldMatrix(true, true);
      const eL = m.getObjectByName('eyeL').getWorldPosition(new THREE.Vector3()), eR = m.getObjectByName('eyeR').getWorldPosition(new THREE.Vector3()); const ec = eL.clone().add(eR).multiplyScalar(0.5);
      const dir = new THREE.Vector3(Math.sin(m.rotation.y), 0, Math.cos(m.rotation.y)).applyAxisAngle(new THREE.Vector3(0, 1, 0), c.yaw_deg * DEG);
      const pos = ec.clone().addScaledVector(dir, c.dist_studs * S); pos.y = c.height_studs * S; const hd = c.dist_studs * S;
      const tgt = ec.clone(); tgt.y = pos.y + hd * Math.tan(c.pitch_deg * DEG) - 0.035;
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: p.fov }); basePush(ctx);
      nightRig(ctx, H, 'nightHigh', {});
      // the street lamp behind the lens (warm) + a passing headlight sweep on "reflectors"
      ctx.add(ctx.lights.point({ color: '#ffc27a', intensity: 1.6, pos: pos.clone().addScaledVector(dir, 1.2).add(new THREE.Vector3(0.2, 0.6, 0)).toArray(), decay: 2 }));
      const sw = ctx.add(ctx.lights.point({ color: '#fff0d0', intensity: 0, pos: pos.toArray(), decay: 2 })); ctx.shared.sweep = { sw, tR, base: pos.clone().addScaledVector(dir, 0.9).add(new THREE.Vector3(0, 0.25, 0)), side: new THREE.Vector3(-dir.z, 0, dir.x) };
      coolRim(ctx, ec.toArray(), { intensity: 0.7 });
      ctx.shared.gl = [C.starGlint(ctx, { pos: eL.clone().addScaledVector(dir, 0.03), t0: tR, peak: 120, rot: 20, color: '#fff2d8' }), C.starGlint(ctx, { pos: eR.clone().addScaledVector(dir, 0.03), t0: tR + 0.05, peak: 105, rot: 35, color: '#fff2d8' })]; ctx.add(...ctx.shared.gl);
      ctx.shared.fx = sparks(ctx, ec.clone().lerp(pos, 0.4).add(new THREE.Vector3(0, 0.12, 0)).toArray(), [0.9, 0.5, 0.35], 6, 's36', { px: [40, 70] });
    },
    update(ctx, t) {
      const s = ctx.shared; CR.animateMole(s.m, t, { eyesOn: s.cue.eyesOn, flash: t < s.cue.flash + 0.245 ? s.cue.flash : null }); s.fx.update(t); s.gl.forEach((g) => g.update(t));
      const u = (t - s.sweep.tR) / 0.3; const k = u < 0 || u > 1 ? 0 : Math.sin(Math.PI * u); s.sweep.sw.intensity = 6 * k; s.sweep.sw.visible = k > 0;
      s.sweep.sw.position.copy(s.sweep.base).addScaledVector(s.sweep.side, lerp(-1.2, 1.2, clamp01(u)));
    },
  },

  // s37 "Moles, big ones." (39.95-40.97) - extreme low ECU: the turf splits and a pink star-shaped snout unfurls and sniffs
  // ("Moles,"), tentacles wriggling; on "big" a second snout x1.8 rises behind it and fills the frame as the camera punches
  // in x1.6 (inQuad, 0.45 s) over a 10 % base push, roll +10.
  snout_reveal: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); frontDoor(ctx, LOT_DOOR);
      const tMo = evT(ctx, 'moles', 0.017), tBig = evT(ctx, 'big', 0.503); ctx.shared.tBig = tBig;
      const M1 = [2.35, 0, -9.75]; const m1 = CR.makeMole({ preset: 'lawn', seed: 7, lod: 'hero' }); m1.position.set(...M1); m1.rotation.y = -0.12; ctx.add(m1);
      const M2 = [2.72, 0, -10.55]; const m2 = CR.makeMole({ preset: 'big', seed: 11, lod: 'hero' }); m2.position.set(...M2); m2.rotation.y = -0.3; ctx.add(m2);
      ctx.shared.m1 = m1; ctx.shared.m2 = m2;
      ctx.shared.c1 = { unfurl: tMo, sniff: [tMo + 0.3, tMo + 0.48] }; ctx.shared.c2 = { rise: tBig - 0.04, riseDur: 0.32, unfurl: tBig + 0.08, emerge: [[-1, -1], [tBig, 0.55]], eyesOn: tBig + 0.1 };
      CR.animateMole(m1, 0.6, ctx.shared.c1); m1.updateWorldMatrix(true, true);
      const sn1 = m1.getObjectByName('snout').getWorldPosition(new THREE.Vector3());
      const dir = new THREE.Vector3(Math.sin(m1.rotation.y), 0, Math.cos(m1.rotation.y)).applyAxisAngle(new THREE.Vector3(0, 1, 0), c.yaw_deg * DEG);
      const pos = sn1.clone().addScaledVector(dir, c.dist_studs * S); pos.y = c.height_studs * S;
      const look = sn1.clone().lerp(V3(M2), 0.35); const hd = Math.hypot(look.x - pos.x, look.z - pos.z); look.y = pos.y + hd * Math.tan(c.pitch_deg * DEG);
      ctx.camera.set({ pos: pos.toArray(), target: look.toArray(), fov: p.fov });
      basePush(ctx, { Z: c.move.base_push }); ctx.camera.push(c.move.x - 1, { mode: 'zoom', t0: tBig, t1: tBig + c.move.dur, ease: c.move.ease }); paramRoll(ctx);
      nightRig(ctx, H, 'nightHigh', {});
      ctx.add(ctx.lights.point({ color: '#ffc27a', intensity: 1.4, pos: pos.clone().addScaledVector(dir, 1.0).add(new THREE.Vector3(0.15, 0.55, 0)).toArray(), decay: 2 }));
      coolRim(ctx, sn1.toArray(), { intensity: 0.9 });
      const sb = X.soilBurst(ctx, { bursts: [{ pos: sn1.toArray(), t0: tMo, count: 14, spread: 0.7, apex: 0.5, puffs: 1 }, { pos: up(M2, 0.6), t0: tBig, count: 24, spread: 1.4, apex: 1.0, puffs: 2 }], seed: 's37soil' }); ctx.add(sb.group); ctx.shared.sb = sb;
    },
    update(ctx, t) { const s = ctx.shared; CR.animateMole(s.m1, t, s.c1); CR.animateMole(s.m2, t, s.c2); s.sb.update(t); },
  },

  // s38 "Grandpa's lantern lit," (40.97-41.95) - low CU on the gnome in the hero's arms, his lantern hand toward us; on
  // "lit" the lantern lights by itself (3 frames, overshoot 1.5, halo 0.2 s): a warm pool on his face and the mustard
  // hoodie, 12 gold motes rising; the grade warms over 8 frames to 60 % magic. Push 19 %.
  lantern_lights: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const H = nightLot(ctx); frontDoor(ctx, LOT_DOOR); const tLit = evT(ctx, 'lit', 0.793); ctx.shared.tLit = tLit;
      const { g } = heroWithGnome(ctx, { at: HOLD_AT, face: 'wonder' }); ctx.shared.g = g;
      const eyes = gnomeEyes(g); const lan = worldOf(g.getObjectByName('lantern'));
      const fwd = new THREE.Vector3(0, 0, 1); const dir = fwd.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), c.yaw_deg * DEG);
      const ctr = eyes.clone().lerp(lan, 0.35); const pos = ctr.clone().addScaledVector(dir, c.dist_studs * S); pos.y = c.height_studs * S;
      const hd = Math.hypot(ctr.x - pos.x, ctr.z - pos.z); const tgt = ctr.clone(); tgt.y = Math.max(ctr.y - 0.05, pos.y + hd * Math.tan(c.pitch_deg * DEG));
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: p.fov }); basePush(ctx);
      const rig = nightRig(ctx, H, 'nightHigh', { postOpts: CU_GRADE }); ctx.shared.rig = rig;
      warmKey(ctx, eyes.toArray(), { cd: 0.9, d: 0.7, color: '#ffc8a0' });
      const L = X.lanternLight(ctx, g, { t0: tLit, ring: 5, cd: 0.9, lightOffset: dir.clone().multiplyScalar(0.32).add(new THREE.Vector3(0, 0.06, 0)) }); ctx.add(L.group); ctx.shared.L = L;
      ctx.shared.gr = X.inShotGrade(ctx, 'current', 'magic', tLit, 8, 0.6, { rig, hemi: ['#ffcdb8', '#5a2030', 1.25] });
      ctx.shared.md = sets.magicDust(ctx, { center: lan.toArray(), radius: 0.3, height: 0.8, count: 12, rise: 0.35, px: [12, 26], seed: 's38dust' }); ctx.add(ctx.shared.md);
      ctx.shared.fx = sparks(ctx, ctr.clone().lerp(pos, 0.4).toArray(), [1.0, 0.8, 0.4], 7, 's38', { px: [45, 80] });
    },
    update(ctx, t) {
      const s = ctx.shared; lanternSwing(s.g, t + 1.6, { amp: 12, decay: 0.9 }); s.L.update(t); s.gr(t); s.md.update(t);
      const k = clamp01((t - s.tLit - 0.04) / 0.25); s.md.children.forEach((m) => { m.material.opacity *= k; m.visible = k > 0; }); s.fx.update(t);
    },
  },

  // s39 "and they stopped at its edge." (41.95-43.50) - top-down over the hero's bare feet: the gold circle of light on the
  // grass, mounds roll in from all sides and on "edge" their snouts snap back at the rim (0.15 s spring); held through the
  // pause. Push 15 %, roll +6.
  ring_edge: {
    build(ctx) {
      const p = ctx.params; const H = nightLot(ctx); frontDoor(ctx, LOT_DOOR); const tEdge = evT(ctx, 'edge', 0.795);
      const { g } = heroWithGnome(ctx, { at: HOLD_AT, face: 'shock', gnome: { lantern: 1 } }); ctx.shared.g = g;
      const hgt = 26 * S; // h 16 studs does not fit the 5-stud ring in a 9:16 frame at fov 50: raised to 26 (see NOTES)
      ctx.camera.set({ pos: [HOLD_AT[0], hgt, HOLD_AT[2] + 0.02], target: [HOLD_AT[0], 0, HOLD_AT[2]], fov: p.fov }); basePush(ctx); paramRoll(ctx);
      nightRig(ctx, H, 'nightHigh', { subject: { pos: [HOLD_AT[0], 1.0, HOLD_AT[2]], cd: 0.5 } });
      const L = X.lanternLight(ctx, g, { t0: -1, ring: 5, burst: false, cd: 1.6 }); ctx.add(L.group); ctx.shared.L = L;
      const f = CR.moleField(ctx, { center: [HOLD_AT[0], HOLD_AT[2] - 0.6], size: [34, 30], res: 112, seed: 's39', heads: 'snout' }); ctx.add(f.group);
      L.update(0); const cxz = L.ring.centerXZ(), rad = L.ring.radius;
      const angs = [-165, -132, -100, -68, -36, -4, 168, 200]; const r = makeRng(hash32('p2s39'));
      angs.forEach((a) => { const th = a * DEG; const d0 = 3.4 + 0.6 * r(); const st = [cxz[0] + Math.cos(th) * d0, cxz[1] + Math.sin(th) * d0]; const sc = 1.55 + 0.25 * r();
        const k = f.add({ at: st, scale: sc }); const path = [st, [cxz[0] + Math.cos(th) * 0.2, cxz[1] + Math.sin(th) * 0.2]]; const sp = 3.2 + 0.5 * r();
        f.travel(k, path, 0, sp); f.stopAt(k, cxz, rad); const sStop = f.moles[k].sStop ?? 0; f.travel(k, path, tEdge + (r() - 0.5) * 0.03 - sStop / sp, sp); f.eyes(k, -5, null); });
      ctx.shared.f = f; const mc = X.moundCrumbs(ctx, f, { pops: false }); ctx.add(mc.group); ctx.shared.mc = mc;
      ctx.shared.fx = sparks(ctx, [HOLD_AT[0], 1.2, HOLD_AT[2]], [3.2, 1.2, 4.6], 9, 's39', { px: [45, 80] });
    },
    update(ctx, t) { const s = ctx.shared; lanternSwing(s.g, t + 2.6, { amp: 12, decay: 0.9 }); s.L.update(t); s.f.update(t); s.mc.update(t); s.fx.update(t); },
  },

  // s40 "Down the street. Every lantern lit," (43.50-45.43) - high WS from above the porches looking along the front lawns:
  // dark gardens with mounds prowling (amber eyes); from "Every" the lanterns pop on garden by garden toward the camera
  // (the 4 nearest on the sound's tinks, the nearest on "lit"), each gnome's face lit from below as it stares at its house,
  // while the camera trucks fast along the kerb (30 studs in 0.95 s from 44.58 s). Our lot is already lit (Grandpa's ring
  // round the hero); next door's plastic gnomes stay dark.
  street_cascade: {
    build(ctx) {
      const p = ctx.params, c = p.camera; const R = SE.ep01Street(ctx, { tod: 'night', lanterns: 0, truck: 'open', skip: ['A3.bed0'] }); ctx.add(R); const E = R.ep01;
      frontDoor(ctx, streetDoor(R));
      const { g } = heroWithGnome(ctx, { at: STREET_HERO, face: 'wonder', gnome: { lantern: 1 } }); ctx.shared.g = g;
      const tEv = evT(ctx, 'every', 1.13), tLit = evT(ctx, 'lit', 1.72); const tTr = 44.58 - ctx.shot.start; const T = ctx.shot.duration;
      // high over our side's fence line from the far end of the street, looking back down it toward our lot: side A (ours) on the right,
      // next door (A4, dark) nearer than our lit lot, the parked truck beyond it (so it never hides our lot)
      // h 19 studs: at the board's 9 studs the picket fences hide every lawn gnome and its lantern from the road
      const dir = -1; const h = 19 * S; const P0 = new THREE.Vector3(30.0, h, -6.0); const yw = 16 * DEG; const fwd = new THREE.Vector3(dir * Math.cos(yw), 0, -Math.sin(yw));
      const L = 10; const look = P0.clone().addScaledVector(fwd, L); look.y = h - L * Math.tan(-c.pitch_deg * DEG);
      const vTr = (c.drift.truck_studs * S) / 0.95; const xAt = (t) => dir * (0.25 * t + (t > tTr ? vTr * (t - tTr) : 0));
      ctx.camera.set({ pos: (t, o) => (o || new THREE.Vector3()).copy(P0).add(new THREE.Vector3(xAt(t), 0, 0)), target: (t, o) => (o || new THREE.Vector3()).copy(look).add(new THREE.Vector3(xAt(t), 0, 0)), fov: p.fov });
      basePush(ctx);
      nightRig(ctx, R, 'night', { low: false, lamp: { n: 4 } });
      // Grandpa's lantern (our lot) already lit; the cascade lights every other non-plastic lantern
      const GL = X.lanternLight(ctx, g, { t0: -1, ring: 5, burst: false, cd: 1.6 }); ctx.add(GL.group); ctx.shared.GL = GL;
      const camEnd = P0.clone().add(new THREE.Vector3(xAt(T), 0, 0));
      const list = E.gnomes.filter((e) => !e.plastic && e.g.getObjectByName('lantern') && dir * (e.pos[0] - camEnd.x) > 1.4).map((e) => ({ ...e, d: V3(e.pos).distanceTo(camEnd) }));
      list.sort((a, b) => b.d - a.d); const n = list.length; const near = list.slice(-4); const far = list.slice(0, n - 4);
      const nearT = [tEv, tEv + 0.19, tEv + 0.38, tLit]; const r = makeRng(hash32('p2s40'));
      far.forEach((e, i) => { e.t0 = tEv + (0.45 * i) / Math.max(1, far.length - 1) + 0.02 * r(); }); near.forEach((e, i) => { e.t0 = nearT[i]; });
      ctx.shared.cas = list.map((e) => { const fx = X.lanternLight(ctx, e.g, { t0: e.t0, ring: 2, ringOpts: { boost: 1.5, rimBoost: 2.6, rimA: 0.5 }, burst: near.includes(e), burstOpts: { count: 8, ringPx: [16, 110], corePx: 90, px: [20, 40] }, haloPx: 54, cd: 1.6, light: near.includes(e), seed: 's40' + e.slot }); ctx.add(fx.group); return fx; });
      ctx.shared.cues = list.map((e) => +(ctx.shot.start + e.t0).toFixed(3)).sort((a, b) => a - b);
      // mounds prowling on the dark lawns (amber eyes), backing off as each lantern lights
      const lots = R.userData.lots.filter((l) => ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4'].includes(l.id)); const fields = [];
      for (const l of lots) {
        const sgn = l.side === 'A' ? 1 : -1; const cz = l.gate[2] - sgn * 3.3; const f = CR.moleField(ctx, { center: [l.gate[0], cz], size: [34, 19], res: 64, seed: 's40' + l.id, heads: 'eyes' }); ctx.add(f.group);
        const m = l.id === 'A4' ? 4 : 3;
        for (let i = 0; i < m; i++) { const x = l.gate[0] + (r() - 0.5) * 9.0, z = cz + (r() - 0.5) * 4.0; const k = f.add({ at: [x, z], scale: 0.85 + 0.25 * r() }); const a = r() * 6.28; f.travel(k, [[x, z], [x + Math.cos(a) * 1.6, z + Math.sin(a) * 0.9], [x + Math.cos(a + 1.5) * 2.4, z + Math.sin(a + 1.5) * 1.2]], -1 + r(), 2.2 + r()); f.eyes(k, -5, null); }
        if (l.id === 'A3') f.pushBack([STREET_HERO[0], STREET_HERO[2]], 0, 5 * S, -2, 0.5);
        for (const e of list.filter((x) => x.lot === l.id)) f.pushBack([e.pos[0], e.pos[2]], 0, 2.2 * S, e.t0, 0.45);
        fields.push(f);
      }
      ctx.shared.fields = fields;
      ctx.shared.fx = sparks(ctx, [16, 1.8, 0], [10, 2.5, 8], 9, 's40', { px: [40, 70] });
    },
    update(ctx, t) { const s = ctx.shared; lanternSwing(s.g, t + 4.2, { amp: 12, decay: 0.9 }); s.GL.update(t); for (const fx of s.cas) fx.update(t); for (const f of s.fields) f.update(t); s.fx.update(t); },
  },

  // s41 "except next door." (45.43-46.30) - next door's lawn, dark: the glossy plastic gnomes still facing the street with
  // their black plastic lanterns; on "door" a mound rolls under one and it tips into a hole (0 -> 70 deg, drops 1.5
  // studs). Night grade, temperature -24. Push 19 %.
  nextdoor_dark: {
    build(ctx) {
      const H = nightLot(ctx, { lanterns: 1 }); const E = H.ep01; frontDoor(ctx, LOT_DOOR); const tD = evT(ctx, 'door', 0.572); ctx.shared.tD = tD;
      const { g } = heroWithGnome(ctx, { at: HOLD_AT, face: 'wonder', gnome: { lantern: 1 } }); const GL = X.lanternLight(ctx, g, { t0: -1, ring: 5, burst: false, cd: 1.6 }); ctx.add(GL.group); ctx.shared.GL = GL;
      ctx.camera.set(E.views.nextDoorNight); basePush(ctx);
      nightRig(ctx, H, 'night', { low: false, lamp: { n: 3 }, postOpts: { grade: { temperature: -24 } } });
      const pg = E.nextDoor.gnomes[1]; ctx.shared.pg = pg; const P = pg.position.clone(); ctx.shared.P = P;
      const f = CR.moleField(ctx, { center: [P.x, P.z + 0.6], size: [20, 14], res: 96, seed: 's41', heads: 'eyes' }); ctx.add(f.group);
      const st = [P.x + 1.9, P.z + 0.9]; const path = [st, [P.x + 0.7, P.z + 0.35], [P.x, P.z]]; const k = f.add({ at: st, scale: 0.95 }); f.travel(k, path, 0, 3.2); f.eyes(k, -5, null);
      f.travel(k, path, tD - 0.02 - f.moles[k].len / 3.2, 3.2); f.sink(k, tD + 0.08, 0.45);
      ctx.shared.f = f;
      const hole = new THREE.Mesh(new THREE.CircleGeometry(0.3, 28), new THREE.MeshStandardMaterial({ color: '#0b0705', roughness: 1 })); hole.rotation.x = -Math.PI / 2; hole.position.set(P.x, 0.012, P.z); hole.visible = false; ctx.add(hole); ctx.shared.hole = hole;
      const sb = X.soilBurst(ctx, { pos: [P.x, 0.05, P.z], t0: tD, count: 22, spread: 1.0, apex: 0.9, puffs: 2 }); ctx.add(sb.group); ctx.shared.sb = sb;
      ctx.shared.fx = sparks(ctx, [P.x - 0.4, 1.0, P.z + 0.9], [2.2, 1.2, 1.4], 6, 's41', { px: [40, 70] });
    },
    update(ctx, t) {
      const s = ctx.shared; s.GL.update(t); s.f.update(t); s.sb.update(t); s.fx.update(t);
      const u = clamp01((t - s.tD) / 0.3); const e = Math.pow(u, 2.6); s.hole.visible = t >= s.tD;
      s.pg.position.set(s.P.x + 0.05 * e, s.P.y - 1.5 * S * e, s.P.z + 0.05 * e); s.pg.rotation.z = -70 * DEG * outQuad(u);
    },
  },
};
