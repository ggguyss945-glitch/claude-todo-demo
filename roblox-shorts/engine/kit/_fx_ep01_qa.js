// QA stills for the EP01 effects kit (fx_ep01.js), each effect in its board shot's set, light and grade.
//   node tools/render.js engine/kit/_fx_ep01_qa.js <outdir> times=... workers=2 quality=final
// One 2 s shot per effect: shot i covers [2i, 2i+2). SHOTS below lists them (index: name - board shots).
import * as THREE from 'three';
import * as sets from './sets.js';
import * as K from './chars.js';
import * as C from './creatures.js';
import * as SE from './sets_ep01.js';
import * as I from './interiors.js';
import * as X from './fx_ep01.js';

const S = sets.STUD, DEG = Math.PI / 180;
const V = (a) => new THREE.Vector3(a[0], a[1], a[2]);
const SPARK = X.SPARK;
const GALAXY_LOW = { ...sets.SKIES.galaxy, stops: [[-1, '#000000'], [-0.02, '#1c1650'], [0.12, '#140f3e'], [0.35, '#0b0828'], [0.65, '#06041a'], [1, '#030210']], nebula: 0.6, seed: 21 };
const up = (p, dy, dx = 0, dz = 0) => [p[0] + dx * S, p[1] + dy * S, p[2] + dz * S];
function orbit(subject, { dist, height, yaw = 0, fov = 70, aim = null }) { const c = V(subject); const a = yaw * DEG; return { pos: [c.x + Math.sin(a) * dist * S, height * S, c.z + Math.cos(a) * dist * S], target: aim || subject, fov }; }
function hero(ctx, o = {}) { const H = SE.heroLot(ctx, { tod: 'night', ...o }); ctx.add(H); return H; }
function spark(ctx, center, size, count, seed) { const s = sets.sparkles(ctx, { ...SPARK, center, size, count, seed }); ctx.add(s); return s; }
const fwdOf = (yaw) => new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw));
// the approved s05 camera: from below at 3/4 on the gnome's lantern side (part1 gnome_hero)
function s05cam(g, { dist = 1.25, height = 0.55, yaw = -20, pitch = 26, aimLantern = 0.3, fov = 70 } = {}) {
  g.updateWorldMatrix(true, true); const eyes = g.getObjectByName('ballL').getWorldPosition(new THREE.Vector3()).add(g.getObjectByName('ballR').getWorldPosition(new THREE.Vector3())).multiplyScalar(0.5);
  const fwd = fwdOf(g.rotation.y); const lan = g.getObjectByName('lantern').getWorldPosition(new THREE.Vector3()); const gl = new THREE.Vector3(-fwd.z, 0, fwd.x); const side = Math.sign(lan.clone().sub(eyes).dot(gl)) || 1;
  const nose = eyes.clone().addScaledVector(fwd, 0.05 * S); nose.y -= 0.12 * S; const dir = fwd.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), side * yaw * DEG);
  const pos = nose.clone().addScaledVector(dir, dist * S); pos.y = height * S; const tgt = eyes.clone().lerp(lan, aimLantern); const hd = Math.hypot(tgt.x - pos.x, tgt.z - pos.z); tgt.y = pos.y + hd * Math.tan(pitch * DEG);
  return { pos: pos.toArray(), target: tgt.toArray(), fov };
}

const SHOTS = [
  // 0: s38 lantern light-up: the gnome in the hero's arms, lantern toward us; it lights at 0.4 s (3 frames + overshoot)
  ['lantern_lightup', {
    build(ctx) {
      const H = hero(ctx, { bed: 'empty' }); const sp = H.ep01.spots; const c = V(sp.lawnMid || up(sp.bed0, 0, 0, 8)); c.y = 0;
      const av = K.makeCharacter('heroBarefoot'); av.position.copy(c); av.rotation.y = 0; K.setPose(av, K.POSES.carry); ctx.add(av);
      const g = K.makeGnome('grandpa', { lantern: 0, wear: 0.12 }); g.position.copy(c).add(new THREE.Vector3(0, 2.6 * S, 1.3 * S)); ctx.add(g); ctx.shared.g = g;
      g.updateWorldMatrix(true, true); const lan = g.getObjectByName('lantern').getWorldPosition(new THREE.Vector3()); const side = Math.sign(lan.x - g.position.x) || 1;
      const ctr = g.position.clone().add(new THREE.Vector3(0, 1.0 * S, 0)); const d = new THREE.Vector3(Math.sin(side * 22 * DEG), 0, Math.cos(side * 22 * DEG));
      ctx.camera.set({ pos: ctr.clone().addScaledVector(d, 2.7 * S).setY(2.5 * S).toArray(), target: ctr.clone().lerp(lan, 0.3).add(new THREE.Vector3(0, 0.2 * S, 0)).toArray(), fov: 70 }).push(0.19);
      ctx.shared.rig = H.ep01.light(ctx, { skyPreset: GALAXY_LOW, subject: { pos: ctr.toArray(), cd: 0.5 } });
      const L = X.lanternLight(ctx, g, { t0: 0.4, ring: 5, cd: 0.9, lightOffset: d.clone().multiplyScalar(0.35).add(new THREE.Vector3(0, 0.08, 0)) }); ctx.add(L.group); ctx.shared.L = L;
      ctx.shared.gr = X.inShotGrade(ctx, 'current', 'magic', 0.4, 8, 0.6);
      ctx.shared.md = sets.magicDust(ctx, { center: lan.toArray(), radius: 0.35, height: 0.8, count: 12, rise: 0.35, px: [12, 24], seed: 'qa0d' }); ctx.add(ctx.shared.md);
      ctx.shared.sp = spark(ctx, ctr.clone().add(new THREE.Vector3(0, 0.2, 0.3)).toArray(), [1.4, 1.0, 0.8], 6, 'qa0');
    },
    update(ctx, t) { const s = ctx.shared; K.gnomeIdle(s.g, t); s.L.update(t); s.gr(t); s.md.update(t); const k = Math.max(0, Math.min(1, (t - 0.45) / 0.3)); s.md.children.forEach((m) => { m.material.opacity *= k; m.visible = k > 0; }); s.sp.update(t); },
  }],
  // 1: s39 top-down: the hero holds the lit gnome on the lawn; mounds roll in and stop at the ring's rim
  ['ring_topdown', {
    build(ctx) {
      const H = hero(ctx, { bed: 'empty' }); const sp = H.ep01.spots; const c = V(sp.lawnMid || up(sp.bed0, 0, 0, 8)); c.y = 0;
      const av = K.makeCharacter('heroBarefoot'); av.position.copy(c); av.rotation.y = Math.PI; K.setPose(av, K.POSES.carry); ctx.add(av);
      const g = K.makeGnome('grandpa', { lantern: 1, wear: 0.12 }); g.position.copy(c).add(new THREE.Vector3(0, 1.75 * S, -1.05 * S)); g.rotation.y = Math.PI; ctx.add(g); ctx.shared.g = g;
      ctx.camera.set({ pos: [c.x, 22 * S, c.z + 0.02], target: [c.x, 0, c.z], fov: 60 }).push(0.2);
      H.ep01.light(ctx, { skyPreset: GALAXY_LOW, subject: { pos: [c.x, 1.0, c.z], cd: 0.5 } });
      const L = X.lanternLight(ctx, g, { t0: -1, ring: 5, burst: false, cd: 3.2 }); ctx.add(L.group); ctx.shared.L = L;
      const f = C.moleField(ctx, { center: [c.x, c.z], size: [30, 30], res: 112, seed: 'qa1', heads: 'snout' }); ctx.add(f.group);
      for (let i = 0; i < 7; i++) { const a = (i / 7) * Math.PI * 2 + 0.3; const st = [c.x + Math.cos(a) * 12 * S, c.z + Math.sin(a) * 12 * S]; const k = f.add({ at: st, scale: 0.8 + 0.06 * (i % 3) }); f.travel(k, [st, [c.x, c.z]], -2.4 + 0.12 * i, 3.4); f.stopAt(k, L.ring.centerXZ(), L.ring.radius); }
      ctx.shared.f = f; ctx.shared.mc = X.moundCrumbs(ctx, f, { pops: false }); ctx.add(ctx.shared.mc.group);
    },
    update(ctx, t) { const s = ctx.shared; s.L.update(t); s.f.update(t); s.mc.update(t); },
  }],
  // 2: s40 street cascade: lanterns pop on garden by garden toward the camera; our lot (A3) already lit, next door dark
  ['street_cascade', {
    build(ctx) {
      const R = SE.ep01Street(ctx, { tod: 'night', lanterns: 0 }); ctx.add(R); const E = R.ep01;
      const hg = R.userData.lots.find((l) => l.id === 'A3').gate; // from the porches of A1-A2 back along the lawns: the gnomes face us
      ctx.camera.set({ pos: up(hg, 5.5, -40, -15), target: up(hg, 1.0, 10, 2), fov: 60 }).push(0.12);
      sets.nightStreet(ctx, { set: R, skyPreset: { ...sets.SKIES.galaxy, nebula: 0.45 } });
      const cas = X.lanternCascade(ctx, E.gnomes, { t0: 0.2, preLit: ['A3'], skip: ['A4'], lights: 4 }); ctx.add(cas.group); ctx.shared.cas = cas;
      ctx.shared.sp = spark(ctx, up(E.views.alongLawns.target, 1.0), [6, 2, 4], 8, 'qa2');
    },
    update(ctx, t) { ctx.shared.cas.update(t); ctx.shared.sp.update(t); },
  }],
  // 3: s51 GULP: a mound surges over the plastic gnome, the turf closes like a mouth, soil burps, the $4.99 sticker flutters
  ['gulp', {
    build(ctx) {
      const H = hero(ctx, { bed: 'plastic' }); const pg = H.ep01.gnomes.plastic; const B = H.ep01.spots.bed0; ctx.shared.H = H;
      ctx.camera.set(H.ep01.views.bedLow).push(0.2);
      H.ep01.light(ctx, { skyPreset: GALAXY_LOW, subject: { pos: up(B, 0.8), cd: 0.9 } });
      const f = C.moleField(ctx, { center: [B[0], B[2]], size: [16, 16], res: 96, seed: 'qa3', heads: false }); ctx.add(f.group);
      const st = V(B).add(new THREE.Vector3(-4.5 * S, 0, 2.0 * S)); const k = f.add({ at: [st.x, st.z] }); f.travel(k, [[st.x, st.z], [B[0], B[2]]], -0.9, 3.6);
      const G = X.gulp(ctx, { field: f, index: k, target: pg, t0: 0.6, sticker: {} }); ctx.add(G.group); ctx.shared.f = f; ctx.shared.G = G;
    },
    update(ctx, t) { ctx.shared.f.update(t); ctx.shared.G.update(t); },
  }],
  // 4: s34/s35 the lawn moves: mounds rise (crumbs pop off the tops) and roll toward the house flicking soil
  ['mounds_roll', {
    build(ctx) {
      const H = hero(ctx, { bed: 'grandpa' }); const B = H.ep01.spots.bed0;
      ctx.camera.set(orbit(B, { dist: 12, height: 2.4, yaw: 10, fov: 70, aim: up(B, 0.2, 0, 4) })).push(0.18);
      H.ep01.light(ctx, { skyPreset: GALAXY_LOW });
      const c = V(B).add(new THREE.Vector3(0, 0, 7 * S)); const f = C.moleField(ctx, { center: [c.x, c.z], size: [30, 22], res: 128, seed: 'qa4', heads: 'snout' }); ctx.add(f.group);
      const starts = [[-7, 8], [-2, 9], [3, 8.5], [8, 7], [-10, 4], [6, 3]];
      starts.forEach(([dx, dz], i) => { const st = [B[0] + dx * S, B[2] + dz * S]; const en = [B[0] + dx * 0.4 * S, B[2] + 3.0 * S]; const k = f.add({ at: st, scale: 0.85 + 0.1 * (i % 2) }); f.rise(k, 0.15 + 0.09 * i, 0.5); f.travel(k, [st, en], 0.55 + 0.07 * i, 3.0); });
      ctx.shared.f = f; const mc = X.moundCrumbs(ctx, f, {}); ctx.add(mc.group); ctx.shared.mc = mc;
    },
    update(ctx, t) { ctx.shared.f.update(t); ctx.shared.mc.update(t); },
  }],
  // 5: s77 FWOOM: low on the gnome in his bed: the lantern flares, burst + streaks + motes, grade to magic in 8 frames
  ['fwoom_flare', {
    build(ctx) {
      const H = hero(ctx, { bed: 'grandpa', lantern: 1 }); const g = H.ep01.gnomes.grandpa; const B = H.ep01.spots.bed0; ctx.shared.g = g;
      ctx.camera.set(s05cam(g, { dist: 2.2, height: 0.6, yaw: -24, pitch: 18 })).push(0.2);
      const rig = H.ep01.light(ctx, { skyPreset: GALAXY_LOW, subject: { pos: up(B, 1.3), cd: 0.5 } });
      const F = X.fwoom(ctx, { gnome: g, t0: 0.4, t2: 1.3, rig }); ctx.add(F.group); ctx.shared.F = F;
      ctx.shared.sp = spark(ctx, up(B, 1.8, 0.3, 1.2), [2.0, 1.4, 1.2], 8, 'qa5');
    },
    update(ctx, t) { K.gnomeIdle(ctx.shared.g, t); ctx.shared.F.update(t); ctx.shared.sp.update(t); },
  }],
  // 6: s78 the light rolls across the lawn: ground level, the wave comes from the bed toward the lens
  ['light_rolls', {
    build(ctx) {
      const H = hero(ctx, { bed: 'grandpa', lantern: 1 }); const g = H.ep01.gnomes.grandpa; const B = H.ep01.spots.bed0;
      ctx.camera.set({ pos: up(B, 0.55, -7, 8), target: up(B, 0.6, 7, 6.5), fov: 70 }).push(0.12); // across the lawn: the wave sweeps left -> right
      const rig = sets.magicGlow(ctx, { set: H, skyPreset: GALAXY_LOW }); void rig;
      const L = X.lanternLight(ctx, g, { t0: -1, level: 1.6, ring: 5, burst: false }); ctx.add(L.group); ctx.shared.L = L;
      const W = X.lightWave(ctx, { center: [B[0], B[2]], t0: 0.2 }); ctx.add(W.group); ctx.shared.W = W;
      ctx.shared.md = sets.magicDust(ctx, { center: up(B, 1.0), radius: 0.8, height: 1.2, count: 24, seed: 'qa6' }); ctx.add(ctx.shared.md);
    },
    update(ctx, t) { ctx.shared.L.update(t); ctx.shared.W.update(t); ctx.shared.md.update(t); },
  }],
  // 7: s79 every mound sank: top-down over the lawn, the ring passes and the mounds deflate in turn
  ['mounds_sink', {
    build(ctx) {
      const H = hero(ctx, { bed: 'grandpa', lantern: 1 }); const g = H.ep01.gnomes.grandpa; const B = H.ep01.spots.bed0;
      const c = V(B).add(new THREE.Vector3(0, 0, 6 * S));
      ctx.camera.set({ pos: [c.x, 19 * S, c.z + 0.02], target: [c.x, 0, c.z], fov: 60 }).push(0.15);
      const rig = H.ep01.light(ctx, { skyPreset: GALAXY_LOW });
      const f = C.moleField(ctx, { center: [c.x, c.z], size: [34, 26], res: 128, seed: 'qa7', heads: 'snout' }); ctx.add(f.group);
      for (let i = 0; i < 11; i++) { const a = -0.1 + (i / 11) * Math.PI * 1.05; const rr = 6 + 4 * ((i * 7) % 5) / 5; const k = f.add({ at: [B[0] + Math.cos(a) * rr * S, B[2] + Math.sin(a) * rr * S], scale: 0.8, face: [B[0], B[2]] }); f.eyes(k, -1, null); }
      const F = X.fwoom(ctx, { gnome: g, t0: 0.3, field: f, rig }); ctx.add(F.group); ctx.shared.F = F; ctx.shared.f = f;
    },
    update(ctx, t) { ctx.shared.f.update(t); ctx.shared.F.update(t); },
  }],
  // 8: s80 eyes winking out pair by pair: low across the dark lawn, five amber pairs, a blip glint as each goes
  ['eyes_wink', {
    build(ctx) {
      const H = hero(ctx, { bed: 'grandpa', lantern: 1 }); const B = H.ep01.spots.bed0;
      const cam = V(B).add(new THREE.Vector3(-2 * S, 1.0 * S, 4 * S)); const look = V(B).add(new THREE.Vector3(2.5 * S, 0.2 * S, 11 * S));
      ctx.camera.set({ pos: cam.toArray(), target: look.toArray(), fov: 70 }).push(0.2);
      H.ep01.light(ctx, { skyPreset: GALAXY_LOW });
      const f = C.moleField(ctx, { center: [look.x, look.z], size: [26, 22], res: 64, seed: 'qa8', heads: 'eyes' }); ctx.add(f.group);
      const pts = [[-3, -2.5], [0.5, -0.5], [3.2, -2], [-1.5, 2.5], [3.5, 2.5]]; const tOff = [0.27, 0.65, 0.83, 1.06, 1.21]; const items = [];
      pts.forEach(([dx, dz], i) => { const k = f.add({ at: [look.x + dx * S, look.z + dz * S], scale: 0.7, face: cam.toArray().filter((_, j) => j !== 1) }); f.eyes(k, -1, tOff[i]); });
      f.update(0); pts.forEach((_, i) => { const e = X.fieldEyes(f, i); if (e) items.push({ L: e[0], R: e[1], t: tOff[i] }); });
      const W = X.winkOut(ctx, items, {}); ctx.add(W.group); ctx.shared.f = f; ctx.shared.W = W;
      const L = X.lanternLight(ctx, H.ep01.gnomes.grandpa, { t0: -1, ring: 5, burst: false }); ctx.add(L.group); ctx.shared.L = L;
    },
    update(ctx, t) { ctx.shared.f.update(t); ctx.shared.W.update(t); ctx.shared.L.update(t); },
  }],
  // 9: s82 dawn: a band of low warm sun sweeps over the lawn to the house; dew glints wake as it passes
  ['dawn_sweep', {
    build(ctx) {
      const H = hero(ctx, { tod: 'dawn', bed: 'grandpa', lantern: 0.5 }); const sp = H.ep01.spots; ctx.shared.H = H;
      ctx.camera.set({ pos: up(sp.steps, 15, -3, 13), target: up(sp.steps, 0, -2, 4), fov: 70 }).push(0.15); // high: clear of the signs
      const rig = H.ep01.light(ctx);
      const D = X.dawnSweep(ctx, { from: [sp.gate[0] + 4 * S, sp.gate[2] + 2 * S], to: [sp.steps[0], sp.steps[2]], t0: 0.2, dur: 1.4, sun: rig.key, hemi: rig.hemi }); ctx.add(D.group); ctx.shared.D = D;
    },
    update(ctx, t) { ctx.shared.H.ep01.update(t); ctx.shared.D.update(t); },
  }],
  // 10: s18 the blink "tik": close on Grandpa from below; blink at 0.5 (2 frames), the glint as the lids reopen
  ['blink_tik', {
    build(ctx) {
      const H = hero(ctx, { bed: 'grandpa', lantern: 0 }); const g = H.ep01.gnomes.grandpa; const B = H.ep01.spots.bed0; ctx.shared.g = g;
      ctx.camera.set(s05cam(g, { dist: 1.5, height: 0.8, yaw: -18, pitch: 16, aimLantern: 0 })).push(0.2);
      H.ep01.light(ctx, { skyPreset: GALAXY_LOW, subject: { pos: up(B, 1.7), cd: 0.7, color: '#ffd9b0' } });
      K.setGnomeGaze(g, 0, 20); const T = X.blinkTik(ctx, g, { t0: 0.5 }); ctx.add(T.group); ctx.shared.T = T;
      ctx.shared.sp = spark(ctx, up(B, 2.0, 0.2, 1.0), [1.4, 1.0, 0.8], 6, 'qa10');
    },
    update(ctx, t) { const g = ctx.shared.g; K.gnomeIdle(g, t); K.setGnomeLids(g, K.gnomeBlink(t, [0.5])); ctx.shared.T.update(t); ctx.shared.sp.update(t); },
  }],
  // 11: s30 the dewdrop tear: close on his painted face, front and low; wells at 0.3, runs into the beard
  ['tear', {
    build(ctx) {
      const H = hero(ctx, { bed: 'grandpa', lantern: 0 }); const g = H.ep01.gnomes.grandpa; const sl = H.ep01.spots; ctx.shared.g = g;
      g.updateWorldMatrix(true, true); const e = g.getObjectByName('ballL').getWorldPosition(new THREE.Vector3()).add(g.getObjectByName('ballR').getWorldPosition(new THREE.Vector3())).multiplyScalar(0.5);
      const f = fwdOf(g.rotation.y); const cam = e.clone().addScaledVector(f, 1.45 * S).add(new THREE.Vector3(0, -0.28 * S, 0)).addScaledVector(new THREE.Vector3(f.z, 0, -f.x), 0.25 * S);
      ctx.camera.set({ pos: cam.toArray(), target: e.clone().add(new THREE.Vector3(0, -0.12 * S, 0)).toArray(), fov: 60 }).push(0.18);
      H.ep01.light(ctx, { skyPreset: GALAXY_LOW, subject: { pos: e.toArray(), cd: 0.6, color: '#ffd9b0' } }); void sl;
      K.setGnomeGaze(g, 0, 6); const T = X.dewTear(ctx, g, { eye: 'L', t0: 0.3 }); ctx.add(T.group); ctx.shared.T = T;
    },
    update(ctx, t) { K.gnomeIdle(ctx.shared.g, t, { amp: 0.2 }); ctx.shared.T.update(t); },
  }],
  // 12: s14 the gate bonk: a family gnome toddles to the open gate and bonks the shimmer curtain at 0.8 s
  ['gate_bonk', {
    build(ctx) {
      const H = hero(ctx, { bed: 'grandpa', gate: 1.4 }); const sp = H.ep01.spots; const G0 = V(sp.gate); G0.y = 0;
      const g = K.makeFamilyGnome(0, { lantern: 0 }); ctx.add(g); ctx.shared.g = g; ctx.shared.G0 = G0;
      const a = [G0.x - 3.2 * S, G0.z], b = [G0.x + 3.2 * S, G0.z];
      ctx.camera.set({ pos: [G0.x + 0.9 * S, 1.3 * S, G0.z + 5.2 * S], target: [G0.x, 0.85 * S, G0.z - 2.0 * S], fov: 70 }).push(0.2);
      H.ep01.light(ctx, { skyPreset: GALAXY_LOW, subject: { pos: [G0.x, 0.6, G0.z - 0.3], cd: 0.9 } });
      const PL = X.propertyLine(ctx, { a, b }); PL.bonk(0.8, [G0.x, 1.1 * S, G0.z]); ctx.add(PL.group); ctx.shared.PL = PL;
      ctx.camera.shake({ t0: 0.8, dur: 0.3, px: 4, rot: 0.3, freq: 14 });
      ctx.shared.sp = spark(ctx, [G0.x, 1.4 * S, G0.z + 1.0 * S], [2.0, 1.0, 1.0], 6, 'qa12');
    },
    update(ctx, t) { const s = ctx.shared; const g = s.g; const u = Math.min(t, 0.8); const back = t > 0.8 ? 0.35 * S * Math.exp(-(t - 0.8) * 6) * Math.sin((t - 0.8) * 18) : 0;
      const h = K.gnomeHop(u, 0); g.position.set(s.G0.x, h.y * S * 1.0, s.G0.z - (2.4 - 3.0 * (u / 0.8)) * S * 0.75 - 0.32 * S - Math.abs(back)); g.rotation.set(0, 0, (t < 0.8 ? h.roll : 6 * Math.sin((t - 0.8) * 22) * Math.exp(-(t - 0.8) * 5)) * DEG);
      s.PL.update(t); s.sp.update(t); },
  }],
  // 13: s32/s33 the family carry: the hero lifts Grandpa over the line - gold ripple along it, his arms outlined in gold
  ['gold_carry', {
    build(ctx) {
      const H = hero(ctx, { bed: 'empty' }); const sp = H.ep01.spots; const G0 = V(sp.lawnMid || up(sp.bed0, 0, 0, 8)); G0.y = 0; G0.z += 1.2 * S;
      const av = K.makeCharacter('heroBarefoot'); av.position.set(G0.x - 0.4 * S, 0, G0.z - 0.6 * S); av.rotation.y = 0; K.setPose(av, K.POSES.carry); ctx.add(av);
      const g = K.makeGnome('grandpa', { lantern: 0, wear: 0.12 }); g.position.set(av.position.x, 2.05 * S, av.position.z + 1.05 * S); ctx.add(g); ctx.shared.g = g;
      ctx.camera.set({ pos: [G0.x + 2.6 * S, 3.0 * S, G0.z + 5.6 * S], target: [G0.x - 0.4 * S, 2.8 * S, G0.z - 0.3 * S], fov: 70 }).push(0.2); // 3/4 front, mid-lawn (the gate itself is the shot's job)
      H.ep01.light(ctx, { skyPreset: GALAXY_LOW, subject: { pos: [av.position.x, 1.0, av.position.z + 0.3], cd: 1.0 } });
      const PL = X.propertyLine(ctx, { a: [G0.x - 3.2 * S, G0.z], b: [G0.x + 3.2 * S, G0.z] }); PL.part(0.5, [g.position.x, 1.6 * S, G0.z]); ctx.add(PL.group); ctx.shared.PL = PL;
      const GO = X.goldOutline(ctx, [av.getObjectByName('armL'), av.getObjectByName('armR'), g], { t0: 0.5 }); ctx.add(GO.group); ctx.shared.GO = GO;
    },
    update(ctx, t) { ctx.shared.PL.update(t); ctx.shared.GO.update(t); },
  }],
  // 14: s19/s20 sepia flashback: human Grandpa on the dark lawn, flashlight clicks on at 0.4 s, beam across the wet grass
  ['flashlight', {
    build(ctx) {
      const H = hero(ctx, { bed: 'none', era: 'now' }); const sp = H.ep01.spots; const c = V(up(sp.bed0, 0, -5, 9)); c.y = 0;
      const av = K.makeCharacter('grandpaFlashback'); av.position.copy(c); av.rotation.y = -Math.PI / 2 + 0.25; K.setPose(av, { ...K.POSES.stand, armRx: 38, armRz: 4 }); ctx.add(av);
      const fl = C.makeFlashlight({ light: false }); C.holdFlashlight(av, fl, { axis: 'forward' }); ctx.shared.fl = fl;
      av.updateWorldMatrix(true, true); C.aimFlashlight(fl, c.clone().add(new THREE.Vector3(-3.0, 0, 0.4)));
      ctx.camera.set({ pos: [c.x - 0.5 * S, 3.6 * S, c.z + 10.5 * S], target: [c.x - 2.4 * S, 1.8 * S, c.z], fov: 70 }).push(0.18);
      H.ep01.light(ctx, { skyPreset: GALAXY_LOW, subject: { pos: [c.x, 1.4, c.z], cd: 0.8 } }); ctx.post.set(sets.postPreset('sepia', { exposure: 1.05 }));
      const Bm = X.flashlightBeam(ctx, { torch: fl, t0: 0.4 }); ctx.add(Bm.group); ctx.shared.Bm = Bm;
    },
    update(ctx, t) { C.setFlashlight(ctx.shared.fl, t >= 0.4 ? 1 : 0); ctx.shared.Bm.update(t); },
  }],
  // 15: s11 dusk street: on "dark" curtains snap shut window by window, nearest first (0.12 s apart)
  ['curtains', {
    build(ctx) {
      const R = SE.ep01Street(ctx, { tod: 'dusk' }); ctx.add(R); const hero_ = R.userData.lots.find((l) => l.id === 'A3');
      ctx.camera.set({ pos: up(hero_.gate, 6.0, 26, 22), target: up(hero_.gate, 5.0, -10, -16), fov: 60 }).push(0.15);
      sets.dusk(ctx, { set: R, postOpts: { exposure: 1.5 } });
      const Cc = X.curtainCascade(ctx, R, { t0: 0.5, n: 6 }); ctx.add(Cc.group); ctx.shared.Cc = Cc;
    },
    update(ctx, t) { ctx.shared.Cc.update(t); },
  }],
  // 16: s55 from inside the room: amber eyes outside the glass, their breath fogs the pane on "glass" (0.5 s)
  ['glass_fog', {
    build(ctx) {
      const H = hero(ctx, { bed: 'grandpa', theoRoom: { era: 'theo', lit: true } }); const E = H.ep01; ctx.shared.H = H;
      const v = E.views.room_fromBed || E.views.room_toWindow; ctx.camera.set(v).push(0.18);
      I.bedroomNight(ctx, { set: H, lamp: 2.5 });
      const glass = E.theo.glass; glass.updateWorldMatrix(true, false); const gc = glass.getWorldPosition(new THREE.Vector3()); const n = new THREE.Vector3(0, 0, 1).transformDirection(glass.matrixWorld);
      const m = C.makeMole({ seed: 7, scale: 0.9 }); m.position.copy(gc).addScaledVector(n, 1.1 * S); m.position.y = gc.y - 1.45 * S; m.rotation.y = Math.atan2(-n.x, -n.z); ctx.add(m); C.setMole(m, { t: 0, rise: 1, open: 1, emerge: 0.5, eyes: 1 }); ctx.shared.m = m;
      m.updateWorldMatrix(true, true); const eyes = ['eyeL', 'eyeR'].map((k) => m.getObjectByName(k)).filter(Boolean).map((o) => o.getWorldPosition(new THREE.Vector3()));
      const ctr = eyes.length ? eyes[0].clone().add(eyes[1]).multiplyScalar(0.5) : gc.clone(); const onGlass = ctr.clone().sub(gc); onGlass.addScaledVector(n, -onGlass.dot(n)); const fc = gc.clone().add(onGlass).add(new THREE.Vector3(0, -0.25 * S, 0));
      const Fg = X.glassFog(ctx, glass, { t0: 0.5, center: fc, eyes }); ctx.add(Fg); ctx.shared.Fg = Fg;
    },
    update(ctx, t) { C.setMole(ctx.shared.m, { t, rise: 1, open: 1, emerge: 0.5, eyes: 1, breathe: 1 }); ctx.shared.Fg.update(t); },
  }],
  // 17: s46 Theo's window goes dark on "dark" (0.8 s): the 1-frame light-state switch
  ['window_dark', {
    build(ctx) {
      const H = hero(ctx, { bed: 'empty' }); ctx.camera.set(H.ep01.views.theoWindowOut).push(0.18);
      H.ep01.light(ctx, { skyPreset: GALAXY_LOW }); const Wd = X.windowDark(ctx, H, { t0: 0.8 }); ctx.shared.Wd = Wd;
    },
    update(ctx, t) { ctx.shared.Wd.update(t); },
  }],
  // 18: s93 the newest photo fills the frame: Polaroid (white frame, curl, date ink), Grandpa mid-blink, Theo at 66
  ['polaroid_insert', {
    build(ctx) {
      const ph = SE.photoTexture(ctx, 60, { blink: 0.55, girl: true }); const card = X.polaroid(ctx, { photo: ph, date: X.photoDate(60), seed: 60 });
      const table = new THREE.Mesh(new THREE.PlaneGeometry(4, 4), new THREE.MeshStandardMaterial({ ...ctx.tex.woodPlanks({ color: '#9a6232', planks: 7, seed: 4, repeat: [2, 2] }).mat, roughness: 0.5 })); table.rotation.x = -Math.PI / 2; ctx.add(table);
      card.rotation.set(-Math.PI / 2, 0, 0.06); card.position.set(0, 0.004, 0); ctx.add(card); ctx.shared.slide = X.polaroidSlide(card, { t0: 0.1, dur: 0.3, from: [0, 0, 0.5], spin: 5 });
      ctx.camera.set({ pos: [0.05, 2.1, 0.5], target: [0, 0, 0.02], fov: 50 }).push(0.2);
      ctx.add(ctx.lights.hemi('#ffe8d0', '#5a4030', 1.2)); ctx.add(ctx.lights.sun({ color: '#fff3e0', intensity: 2.2, pos: [-2, 4, 2], target: [0, 0, 0], shadow: false }));
      ctx.post.set(sets.postPreset('day', { exposure: 1.0 }));
    },
    update(ctx, t) { ctx.shared.slide(t); },
  }],
  // 19: s90 top-down on the garden table at dusk: Polaroids drop one by one onto a pile (years 1, 5, 10, 16)
  ['polaroid_stack', {
    build(ctx) {
      const years = [1, 5, 10, 16]; const cards = years.map((y) => X.polaroid(ctx, { photo: SE.photoTexture(ctx, y), date: X.photoDate(y), seed: y, curl: 0.1 }));
      const table = new THREE.Mesh(new THREE.PlaneGeometry(5, 5), new THREE.MeshStandardMaterial({ ...ctx.tex.woodPlanks({ color: '#9a6232', planks: 9, seed: 5, repeat: [2, 2] }).mat, roughness: 0.5 })); table.rotation.x = -Math.PI / 2; ctx.add(table);
      const D = X.polaroidDrop(ctx, cards, { at: [0, 0.0, 0], t0s: [0.3, 0.62, 0.86, 1.14] }); ctx.add(D); ctx.shared.D = D;
      ctx.camera.set({ pos: [0, 12.5 * S, 0.01], target: [0, 0, 0], fov: 45 }).push(0.22);
      ctx.add(ctx.lights.hemi('#a08ad0', '#5a3424', 1.5)); ctx.add(ctx.lights.sun({ color: '#ff9a50', intensity: 2.4, pos: [-4, 2.0, 1.5], target: [0, 0, 0], shadow: false }));
      ctx.post.set(sets.postPreset('dusk', { exposure: 1.35 }));
    },
    update(ctx, t) { ctx.shared.D.update(t); },
  }],
];

export default {
  name: 'fx_ep01_qa', fps: 60, width: 1080, height: 1920, seed: 'ep01-fx', duration: SHOTS.length * 2,
  quality: { shadows: 'off' }, post: sets.postPreset('nightHigh'),
  shots: SHOTS.map(([name, b], i) => ({ name, start: 2 * i, end: 2 * i + 2, build: b.build, update: b.update || (() => {}), quality: b.quality })),
};
