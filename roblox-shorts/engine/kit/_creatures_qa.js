// QA stills for the EP01 creatures + new cast (creatures.js, cast.js additions), in the episode's own sets and light.
//   node tools/render.js engine/kit/_creatures_qa.js <outdir> times=... workers=2 quality=final
// One 2 s shot per sheet: shot i covers [2i, 2i+2). SHOTS below lists them (names are printed in the render log).
import * as THREE from 'three';
import * as sets from './sets.js';
import * as K from './chars.js';
import * as C from './creatures.js';

const S = sets.STUD, DEG = Math.PI / 180;
const V = (a) => new THREE.Vector3(...a);
const SPARK = { sharpness: 7, core: 0.75, underlay: 0.55, underlayOpacity: 0.5, brightness: 2.0, px: [55, 95] };
const GALAXY_LOW = { ...sets.SKIES.galaxy, stops: [[-1, '#000000'], [-0.02, '#1c1650'], [0.12, '#140f3e'], [0.35, '#0b0828'], [0.65, '#06041a'], [1, '#030210']], nebula: 0.6, seed: 21 };

function lawn(ctx) { const set = sets.buildLawnCloseup(ctx, { seed: 'ep01' }); ctx.add(set); const id = set.userData.lots.find((l) => l.hero).id; return { set, id, slot: (n) => sets.slot(set, id + '.' + n) }; }
// camera from a subject point: dist / height in studs, yaw (deg, 0 = in front along the subject's facing dir), pitch (deg up)
function camAt(ctx, subj, facingYaw, { dist, height, yaw = 0, pitch = 0, fov = 60, aim = null }) {
  const a = facingYaw + yaw * DEG; const dir = new THREE.Vector3(Math.sin(a), 0, Math.cos(a));
  const pos = V(subj).addScaledVector(dir, dist * S); pos.y = height * S;
  const tgt = aim ? V(aim) : V(subj); const hd = Math.hypot(tgt.x - pos.x, tgt.z - pos.z); if (!aim) tgt.y = pos.y + hd * Math.tan(pitch * DEG);
  ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov }); return { pos, tgt, camYaw: Math.atan2(tgt.x - pos.x, -(tgt.z - pos.z)) / DEG };
}
function studio(ctx, { grade = 'day', exposure = 1.0, top = '#a39fc2', bottom = '#4e4a66' } = {}) {
  const c = document.createElement('canvas'); c.width = 8; c.height = 256; const g = c.getContext('2d'); const gr = g.createLinearGradient(0, 0, 0, 256); gr.addColorStop(0, top); gr.addColorStop(1, bottom); g.fillStyle = gr; g.fillRect(0, 0, 8, 256);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; const m = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshBasicMaterial({ map: t })); m.position.set(0, 0, -6); ctx.add(m);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshStandardMaterial({ color: '#6a6680', roughness: 0.9 })); fl.rotation.x = -Math.PI / 2; ctx.add(fl);
  ctx.add(ctx.lights.hemi('#ece8ff', '#5a4a52', 1.15)); ctx.add(ctx.lights.sun({ color: '#fff4ea', intensity: 1.45, pos: [-6, 9, 10], target: [0, 1, 0], shadow: false }));
  ctx.post.set(sets.postPreset(grade, { exposure }));
}
function label(text, pos, h = 0.1) {
  const c = document.createElement('canvas'); c.width = 512; c.height = 96; const g = c.getContext('2d'); g.font = 'bold 50px sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.lineWidth = 9; g.strokeStyle = '#000'; g.strokeText(text, 256, 50); g.fillStyle = '#fff'; g.fillText(text, 256, 50);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, transparent: true, depthWrite: false, toneMapped: false })); s.scale.set((h * 512) / 96, h, 1); s.position.copy(V(pos)); s.renderOrder = 40; return s;
}
// two rows of three (portrait frame): row 0 raised 1.75 m behind, row 1 on the floor
const rows = (ctx, R) => R.forEach((row, ri) => row.forEach(([obj, name], i) => { const x = (i - 1) * 0.8, y = ri === 0 ? 1.75 : 0, z = ri === 0 ? -0.6 : 0; obj.position.set(x, y, z); ctx.add(obj); ctx.add(label(name, [x, y - 0.1, z + 0.4], 0.075)); }));
const lineup = (ctx, list, { y = 0, spacing = 2.4 * S, z = 0 } = {}) => list.forEach(([obj, name], i) => { if (!obj) return; const x = (i - (list.length - 1) / 2) * spacing; obj.position.set(x, y, z); ctx.add(obj); if (name) ctx.add(label(name, [x, -0.12, z + 0.4], 0.09)); });

const SHOTS = [
  // 0: s36 look - a mound right in front of the lens, reflector eyes lighting (0.3) and flashing (1.0)
  ['mole_cu_night', {
    build(ctx) {
      const L = lawn(ctx); const sl = L.slot('lawn1'); const yaw = sl.yaw + Math.PI; // face the street (the camera)
      const m = C.makeMole({ seed: 3 }); m.position.set(...sl.pos); m.rotation.y = yaw; ctx.add(m); ctx.shared.m = m;
      const head = V(sl.pos).add(new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw)).multiplyScalar(0.9 * S)); head.y = 0.45 * S;
      const c = camAt(ctx, head.toArray(), yaw, { dist: 2.6, height: 0.55, pitch: 2, fov: 55 });
      ctx.shared.rig = sets.nightLawn(ctx, { set: L.set, subject: { pos: head.toArray(), cd: 0.5, color: '#d8d4ff' }, window: { n: 1, cd: 2.2, color: '#ffd9a0', maxD: 10 }, hemiIntensity: 1.0, key: { intensity: 0.45 }, moon: { az: c.camYaw - 22, el: 30, size: 9, style: 'tf' }, skyPreset: GALAXY_LOW, skyOpts: { intensity: 2.0 }, postOpts: { exposure: 1.12, grade: { temperature: -4, tint: 6 } } });
      ctx.add(ctx.lights.point({ color: '#ffc27a', intensity: 1.2, pos: c.pos.clone().add(new THREE.Vector3(0, 0.25, 0)).toArray(), decay: 2 })); // the street lamp behind the lens
      ctx.camera.push(0.28);
      ctx.shared.fx = sets.sparkles(ctx, { ...SPARK, center: head.clone().lerp(c.pos, 0.4).toArray(), size: [0.9, 0.7, 0.4], count: 6, seed: 'qa0' }); ctx.add(ctx.shared.fx);
    },
    update(ctx, t) { C.animateMole(ctx.shared.m, t, { eyesOn: 0.3, flash: 1.0 }); ctx.shared.fx.update(t); },
  }],
  // 1: s37 look - small snout unfurls in front, a BIG one (x1.8) peeks behind with its claws on the turf; extreme low
  ['mole_big_peek', {
    build(ctx) {
      const L = lawn(ctx); const sl = L.slot('lawn1'); const yaw = sl.yaw + Math.PI; const fwd = new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw)), side = new THREE.Vector3(fwd.z, 0, -fwd.x);
      const a = C.makeMole({ seed: 5 }); a.position.copy(V(sl.pos).addScaledVector(fwd, 0.6 * S).addScaledVector(side, -0.8 * S)); a.rotation.y = yaw + 0.25; ctx.add(a);
      const b = C.makeMole({ preset: 'big', seed: 9 }); b.position.copy(V(sl.pos).addScaledVector(fwd, -2.6 * S).addScaledVector(side, 0.9 * S)); b.rotation.y = yaw - 0.12; ctx.add(b);
      ctx.shared.a = a; ctx.shared.b = b;
      const head = V(sl.pos).addScaledVector(fwd, 0.4 * S); head.y = 0.8 * S;
      const c = camAt(ctx, head.toArray(), yaw, { dist: 3.4, height: 0.35, pitch: 16, fov: 70 });
      ctx.shared.rig = sets.nightLawn(ctx, { set: L.set, subject: { pos: head.toArray(), cd: 0.8 }, window: { n: 1, cd: 2.2 }, hemiIntensity: 1.0, key: { intensity: 0.5 }, moon: { az: c.camYaw + 18, el: 34, size: 9, style: 'tf' }, skyPreset: GALAXY_LOW, skyOpts: { intensity: 2.2 }, postOpts: { exposure: 1.12, grade: { temperature: -4, tint: 6 } } });
      const camR = new THREE.Vector3().crossVectors(c.tgt.clone().sub(c.pos).normalize(), new THREE.Vector3(0, 1, 0)).normalize();
      ctx.add(ctx.lights.sun({ color: '#8a90ff', intensity: 0.9, pos: head.clone().addScaledVector(fwd, -6).addScaledVector(camR, 5).add(new THREE.Vector3(0, 4, 0)).toArray(), target: head.toArray(), shadow: false }));
      ctx.camera.push(0.1).rollBy(6);
    },
    update(ctx, t) { C.animateMole(ctx.shared.a, t, { unfurl: 0.15, eyesOn: 0, sniff: [0.6, 1.6] }); C.animateMole(ctx.shared.b, t, { unfurl: 0.5, eyesOn: 0.4, emerge: [[0, 0], [0.4, 0.55]], look: [0, 8] }); },
  }],
  // 2: pose sheet in context - buried (0) / peek (0.5) / out (1); 3/4 front, night lawn
  ['mole_poses', {
    build(ctx) {
      const L = lawn(ctx); const sl = L.slot('lawnMid'); const yaw = sl.yaw; const fwd = new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw)), side = new THREE.Vector3(fwd.z, 0, -fwd.x);
      ctx.shared.ms = [0, 0.5, 1].map((e, i) => { const m = C.makeMole({ seed: 11 + i }); m.position.copy(V(sl.pos).addScaledVector(side, (i - 1) * 0.9 * S).addScaledVector(fwd, -(i - 1) * 4.2 * S)); m.rotation.y = yaw - 0.4 + i * 0.25; ctx.add(m); return [m, e]; });
      const c = camAt(ctx, V(sl.pos).toArray(), yaw, { dist: 9.5, height: 3.4, fov: 50, aim: V(sl.pos).addScaledVector(fwd, -1.0 * S).add(new THREE.Vector3(0, 0.5 * S, 0)).toArray() });
      ctx.shared.rig = sets.nightLawn(ctx, { set: L.set, subject: { pos: V(sl.pos).add(new THREE.Vector3(0, 0.5 * S, 0)).toArray(), cd: 1.2 }, window: { n: 1, cd: 2.2 }, hemiIntensity: 1.1, moon: { az: c.camYaw - 20, el: 30, size: 7, style: 'tf' }, skyPreset: GALAXY_LOW, postOpts: { exposure: 1.12 } });
      ctx.camera.push(0.12);
    },
    update(ctx, t) { for (const [m, e] of ctx.shared.ms) C.animateMole(m, t, { emerge: [[0, e]], eyesOn: 0, look: [0, 4] }); },
  }],
  // 3: s39 look - top-down: the lantern ring round the hero; mounds roll in and stop at its edge, trails behind them
  ['field_topdown', {
    build(ctx) {
      const L = lawn(ctx); const c0 = L.slot('lawnMid'); const cen = [c0.pos[0], c0.pos[2]]; const R = 2.6 * S;
      const f = C.moleField(ctx, { center: cen, size: [30, 30], res: 128, seed: 'qa3', heads: 'snout' }); ctx.add(f.group); ctx.shared.f = f;
      for (let i = 0; i < 7; i++) { const a = [0.15, 0.55, -0.4, Math.PI - 0.1, Math.PI + 0.45, Math.PI - 0.6, 1.4][i] + 0.0, r0 = (9 + (i % 3) * 1.5) * S; const st = [cen[0] + Math.sin(a) * r0, cen[1] + Math.cos(a) * r0]; const k = f.add({ at: st, scale: 0.8 + (i % 3) * 0.12 }); f.travel(k, [st, [cen[0] + Math.sin(a + 0.25) * 5 * S, cen[1] + Math.cos(a + 0.25) * 5 * S], cen], 0.05 * i, 3.2); f.stopAt(k, cen, R); f.eyes(k, 0); }
      const hero = K.makeCharacter('heroBarefoot', { face: 'shock' }); K.setPose(hero, K.POSES.hug); hero.position.set(cen[0], 0, cen[1]); hero.rotation.y = c0.yaw; ctx.add(hero);
      const g = K.makeGnome('grandpa', { lantern: 1, lanternLight: 3 }); const t = K.rig(hero).torso; g.scale.setScalar(1); g.position.set(0, -0.5, 0.9); g.rotation.y = 0; t.add(g);
      ctx.add(sets.lightPool(ctx, { pos: [cen[0], 0.02, cen[1]], radius: R, color: '#ffb870', opacity: 0.55, falloff: 1.2 }));
      ctx.camera.set({ pos: [cen[0], 18 * S, cen[1] + 0.001], target: [cen[0], 0, cen[1]], fov: 50 });
      ctx.shared.rig = sets.nightLawn(ctx, { set: L.set, hemiIntensity: 1.1, window: { n: 1 }, postOpts: { exposure: 1.1 } });
      ctx.add(ctx.lights.point({ color: '#ffb85c', intensity: 3, pos: [cen[0], 1.2 * S * 3, cen[1]], decay: 2 }));
      ctx.camera.push(0.15).rollBy(6);
    },
    update(ctx, t) { ctx.shared.f.update(t); },
  }],
  // 4: s34 / s52 look - ground level across the lawn: bulges rolling toward the house, ridges behind them
  ['field_ground', {
    build(ctx) {
      const L = lawn(ctx); const b = L.slot('bed0'); const lotYaw = b.yaw + Math.PI; const fwd = new THREE.Vector3(Math.sin(lotYaw), 0, Math.cos(lotYaw)), side = new THREE.Vector3(fwd.z, 0, -fwd.x);
      const cen = V(b.pos).addScaledVector(fwd, 10 * S); const f = C.moleField(ctx, { center: [cen.x, cen.z], size: [34, 22], yaw: b.yaw, res: 128, seed: 'qa4', heads: 'snout' }); ctx.add(f.group); ctx.shared.f = f;
      for (let i = 0; i < 5; i++) { const st = V(b.pos).addScaledVector(fwd, 17 * S).addScaledVector(side, (i - 2) * 3.4 * S); const en = V(b.pos).addScaledVector(fwd, 2.5 * S).addScaledVector(side, (i - 2) * 1.2 * S); const k = f.add({ at: [st.x, st.z], scale: 0.85 + 0.1 * (i % 2) }); f.travel(k, [[st.x, st.z], [en.x, en.z]], -2 + i * 0.25, 3.5); f.eyes(k, 0); }
      const pos = V(b.pos).addScaledVector(fwd, 19 * S).addScaledVector(side, 2 * S); pos.y = 2.2 * S; const tgt = V(b.pos).addScaledVector(fwd, 7 * S).add(new THREE.Vector3(0, 0.4 * S, 0));
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: 70 });
      ctx.shared.rig = sets.nightLawn(ctx, { set: L.set, window: { n: 2, cd: 2.4, maxD: 14 }, hemiIntensity: 1.05, skyPreset: GALAXY_LOW, skyOpts: { intensity: 1.6 }, postOpts: { exposure: 1.1, grade: { temperature: -10, tint: 6 } } });
      ctx.camera.push(0.19, { mode: 'dolly' });
    },
    update(ctx, t) { ctx.shared.f.update(t); },
  }],
  // 5: s80 look - five amber eye pairs low across the dark lawn, winking out pair by pair from 0.8 s
  ['eyes_pairs', {
    build(ctx) {
      const L = lawn(ctx); const b = L.slot('lawnMid'); const yaw = b.yaw; const fwd = new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw)), side = new THREE.Vector3(fwd.z, 0, -fwd.x);
      const cen = V(b.pos).addScaledVector(fwd, 4 * S); const f = C.moleField(ctx, { center: [cen.x, cen.z], size: [40, 26], yaw: yaw, res: 96, seed: 'qa5', heads: 'eyes' }); ctx.add(f.group); ctx.shared.f = f;
      const off = [0.8, 1.0, 1.15, 1.35, 1.5];
      for (let i = 0; i < 5; i++) { const p = V(b.pos).addScaledVector(fwd, (5 + ((i * 2) % 5) * 1.6) * S).addScaledVector(side, (i - 2) * 2.0 * S); const k = f.add({ at: [p.x, p.z], scale: 0.9, head: 'eyes', face: [b.pos[0] - fwd.x * 4 * S, b.pos[2] - fwd.z * 4 * S] }); f.eyes(k, 0, off[i]); }
      const pos = V(b.pos).addScaledVector(fwd, -4 * S); pos.y = 1.0 * S; const tgt = V(b.pos).addScaledVector(fwd, 9 * S); tgt.y = 0.45 * S;
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: 60 });
      ctx.shared.rig = sets.nightLawn(ctx, { set: L.set, hemiIntensity: 0.8, window: { n: 1, cd: 1.6 }, skyPreset: GALAXY_LOW, postOpts: { exposure: 1.0 } });
      ctx.add(ctx.lights.point({ color: '#ffd9a0', intensity: 1.5, pos: pos.clone().add(new THREE.Vector3(0, 0.6, 0)).toArray(), decay: 2 }));
      ctx.camera.push(0.19);
    },
    update(ctx, t) { ctx.shared.f.update(t); },
  }],
  // 6: snout ECU - the star nose detail (22 rays, Eimer's-organ bumps, wet nostril pad), sniffing
  ['snout_ecu', {
    build(ctx) {
      const L = lawn(ctx); const sl = L.slot('lawn1'); const yaw = sl.yaw + Math.PI; const m = C.makeMole({ seed: 7 }); m.position.set(...sl.pos); m.rotation.y = yaw; ctx.add(m); ctx.shared.m = m;
      const fwd = new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw)); const nose = V(sl.pos).addScaledVector(fwd, 1.42 * S); nose.y = 0.2 * S;
      const c = camAt(ctx, nose.toArray(), yaw, { dist: 1.25, height: 0.42, yaw: 24, pitch: -2, fov: 50, aim: nose.clone().add(new THREE.Vector3(0, 0.12 * S, 0)).toArray() });
      ctx.shared.rig = sets.nightLawn(ctx, { set: L.set, subject: { pos: nose.toArray(), cd: 0.7, color: '#ffd9b0' }, window: { n: 1, cd: 2.2 }, hemiIntensity: 1.0, key: { intensity: 0.5 }, moon: { az: c.camYaw - 25, el: 26, size: 9, style: 'tf' }, skyPreset: GALAXY_LOW, skyOpts: { intensity: 2.2 }, postOpts: { exposure: 1.12, grade: { temperature: -4, tint: 6 } } });
      ctx.add(ctx.lights.sun({ color: '#8a90ff', intensity: 0.9, pos: nose.clone().addScaledVector(fwd, -5).add(new THREE.Vector3(2, 4, 0)).toArray(), target: nose.toArray(), shadow: false }));
      ctx.camera.push(0.2);
    },
    update(ctx, t) { C.animateMole(ctx.shared.m, t, { sniff: [0.2, 1.8], eyesOn: 0 }); },
  }],
  // 7: s12 look - next door's lawn by day: REX lying, chewing a plastic gnome's hat; sit / stand variants behind
  ['dog_day', {
    build(ctx) {
      const L = lawn(ctx); const sl = L.slot('lawnMid'); const yaw = sl.yaw; const fwd = new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw)), side = new THREE.Vector3(fwd.z, 0, -fwd.x);
      const base = V(sl.pos).addScaledVector(fwd, 3 * S);
      const pg = K.makePlasticGnome({ finish: 'glossy' }); pg.position.copy(base.clone().addScaledVector(side, -0.6 * S).addScaledVector(fwd, 1.6 * S)); pg.rotation.y = yaw + Math.PI; ctx.add(pg);
      const d = C.makeDog(); d.position.copy(base.clone().addScaledVector(side, 0.9 * S)); d.rotation.y = yaw - 1.0; ctx.add(d);
      const d2 = C.makeDog(); d2.position.copy(base.clone().addScaledVector(side, 2.4 * S).addScaledVector(fwd, -3.6 * S)); d2.rotation.y = yaw - 0.4; ctx.add(d2);
      const d3 = C.makeDog(); d3.position.copy(base.clone().addScaledVector(side, -2.2 * S).addScaledVector(fwd, -4.0 * S)); d3.rotation.y = yaw + 0.7; ctx.add(d3);
      ctx.shared.dogs = [[d, 'chew'], [d2, 'sit'], [d3, 'stand']];
      const pos = base.clone().addScaledVector(fwd, 7.5 * S); pos.y = 3.4 * S; const tgt = base.clone().addScaledVector(fwd, -1.6 * S); tgt.y = 0.9 * S;
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: 62 });
      ctx.shared.rig = sets.day(ctx, { set: L.set }); ctx.camera.push(0.19);
    },
    quality: { shadows: 'pcfsoft' },
    update(ctx, t) { for (const [d, p] of ctx.shared.dogs) C.dogAt(d, t, { pose: p }); },
  }],
  // 8: Theo + whale + badge (bedroom grade): hug + badge / socks with the whale under his arm / the whale itself
  ['theo_whale_badge', {
    build(ctx) {
      studio(ctx, { grade: 'bedroom', exposure: 1.05, top: '#6a4a8a', bottom: '#2a1a3a' });
      ctx.add(ctx.lights.point({ color: '#ffb870', intensity: 2.5, pos: [0.6, 1.2, 1.2], decay: 2 }));
      const a = K.makeCharacter('theoBadge', { face: 'wonder' }); K.setPose(a, K.POSES.hug); C.holdWhale(a, C.stuffedWhale(), 'hug'); a.position.set(-0.45, 0, 0); a.rotation.y = 0.35; ctx.add(a);
      const c = K.makeCharacter('theoSocks', { face: 'sleeping' }); C.holdWhale(c, C.stuffedWhale(), 'underArm'); K.setPose(c, { armLx: 10, armLz: -8, ...K.walkCycle(0.2, { period: 1.0, legs: 22, holdArms: true }) }); c.position.set(0.5, 0, -0.3); c.rotation.y = -0.3; ctx.add(c);
      const w1 = C.stuffedWhale(); w1.position.set(-0.32, 0.05, 1.0); w1.rotation.set(0, 0.75, 0); w1.scale.multiplyScalar(1.5); ctx.add(w1);
      const w2 = C.stuffedWhale(); w2.position.set(0.4, 0.05, 0.95); w2.rotation.set(0, -1.75, 0); w2.scale.multiplyScalar(1.5); ctx.add(w2);
      ctx.add(label('hug + badge6', [-0.45, -0.1, 0.5], 0.08)); ctx.add(label('socks + underArm', [0.5, -0.1, 0.5], 0.08));
      ctx.camera.set({ pos: [0, 1.0, 4.3], target: [0, 0.85, 0], fov: 34 });
    },
  }],
  // 9: new cast lineup A (studio, neutral day grade)
  ['cast_a', {
    build(ctx) {
      studio(ctx, { grade: 'day' });
      rows(ctx, [[[K.makeCharacter('grandma'), 'grandma'], [K.makeCharacter('grandmaShort', { face: 'wonder' }), 'grandmaShort'], [K.makeCharacter('grandkid'), 'grandkid']], [[K.makeCharacter('heroOld'), 'heroOld'], [K.makeCharacter('heroOldShort', { face: 'wonder' }), 'heroOldShort'], [K.makeCharacter('heroKid5'), 'heroKid5']]]);
      ctx.camera.set({ pos: [0, 1.62, 8.4], target: [0, 1.62, 0], fov: 30 });
    },
  }],
  // 10: lineup B
  ['cast_b', {
    build(ctx) {
      studio(ctx, { grade: 'day' });
      rows(ctx, [[[K.makeCharacter('grandpaYoung'), 'grandpaYoung'], [K.makeCharacter('dadKid'), 'dadKid'], [K.makeCharacter('cousinKid'), 'cousinKid']], [[K.makeCharacter('granddaughter'), 'granddaughter'], [K.makeCharacter('theoGranddaughter'), 'theoGrandd.'], [K.makeCharacter('heroMuddy'), 'heroMuddy']]]);
      ctx.camera.set({ pos: [0, 1.62, 8.4], target: [0, 1.62, 0], fov: 30 });
    },
  }],
  // 11: lineup C: the new family's parents, Mom / Dad night variants, Theo socks / badge
  ['cast_c', {
    build(ctx) {
      studio(ctx, { grade: 'day' });
      rows(ctx, [[[K.makeCharacter('theoMom'), 'theoMom'], [K.makeCharacter('theoDad'), 'theoDad'], [K.makeCharacter('momNight'), 'momNight']], [[K.makeCharacter('dadNight'), 'dadNight'], [K.makeCharacter('theoSocks'), 'theoSocks'], [K.makeCharacter('theoBadge'), 'theoBadge']]]);
      ctx.camera.set({ pos: [0, 1.62, 8.4], target: [0, 1.62, 0], fov: 30 });
    },
  }],
  // 12: Theo through the years (photo series)
  ['theo_ages', {
    build(ctx) {
      studio(ctx, { grade: 'day' });
      rows(ctx, [[[K.theoAt(7), 'Theo 7'], [K.theoAt(10), 'Theo 10'], [K.theoAt(16), 'Theo 16']], [[K.theoAt(25), 'Theo 25'], [K.theoAt(40), 'Theo 40'], [K.theoAt(66), 'Theo 66']]]);
      ctx.camera.set({ pos: [0, 1.62, 8.4], target: [0, 1.62, 0], fov: 30 });
    },
  }],
  // 13: s23 look (sepia) - Grandpa, torch under the chin, wink; s19 look beside: walking, beam forward
  ['grandpa_torch', {
    build(ctx) {
      const L = lawn(ctx); const sl = L.slot('lawn1'); const yaw = sl.yaw + Math.PI;
      const g = K.makeCharacter('grandpa', { face: 'wink' }); g.position.set(...sl.pos); g.rotation.y = yaw; ctx.add(g);
      K.setPose(g, { armRx: 100, armRz: -38, neckX: -4 }); const fl = C.makeFlashlight({ on: 1, cd: 2.5 }); C.holdFlashlight(g, fl, { axis: 'forward' }); g.updateMatrixWorld(true); C.aimFlashlight(fl, g.getObjectByName('head').localToWorld(new THREE.Vector3(0, -0.2, 0.55)));
      ctx.shared.fl = fl; ctx.shared.g = g;
      const fwd = new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw)); const face = V(sl.pos); face.y = 4.6 * S;
      ctx.add(ctx.lights.point({ color: '#fff1d0', intensity: 2.5, pos: face.clone().addScaledVector(fwd, 0.6 * S).add(new THREE.Vector3(0, -0.9 * S, 0)).toArray(), decay: 2 }));
      camAt(ctx, face.toArray(), yaw, { dist: 2.8, height: 3.9, pitch: 8, fov: 70, aim: face.clone().add(new THREE.Vector3(0, -0.2 * S, 0)).toArray() });
      ctx.shared.rig = sets.nightLawn(ctx, { set: L.set, hemiIntensity: 1.0, window: { n: 1 }, skyPreset: GALAXY_LOW, post: false });
      ctx.post.set(sets.postPreset('sepia'));
      ctx.camera.push(0.22).rollBy(-1);
    },
    update(ctx, t) { C.setFlashlight(ctx.shared.fl, 1, { cd: 2.5 }); },
  }],
  ['grandpa_walk_beam', {
    build(ctx) {
      const L = lawn(ctx); const sl = L.slot('lawn1'); const yaw = sl.yaw + Math.PI / 2;
      const g = K.makeCharacter('grandpa', { face: 'content' }); g.position.set(...sl.pos); g.rotation.y = yaw; ctx.add(g); ctx.shared.g = g;
      const fl = C.makeFlashlight({ on: 1, cd: 8 }); C.holdFlashlight(g, fl); ctx.shared.fl = fl;
      const fwd = new THREE.Vector3(Math.sin(sl.yaw + Math.PI), 0, Math.cos(sl.yaw + Math.PI)); const mid = V(sl.pos); mid.y = 2.6 * S;
      ctx.camera.set({ pos: mid.clone().addScaledVector(fwd, 9 * S).add(new THREE.Vector3(0, 1.8 * S, 0)).toArray(), target: mid.toArray(), fov: 70 });
      ctx.shared.rig = sets.nightLawn(ctx, { set: L.set, hemiIntensity: 1.0, window: { n: 2 }, skyPreset: GALAXY_LOW, post: false });
      ctx.post.set(sets.postPreset('sepia')); ctx.camera.push(0.12);
    },
    update(ctx, t) { K.setPose(ctx.shared.g, { ...K.walkCycle(t, { period: 1.0, legs: 25, holdArms: true }), armRx: 62, armLx: 0 }); C.setFlashlight(ctx.shared.fl, 1); },
  }],
  // 15: s82 look - pink dawn: the hero muddy-kneed by Grandpa in his bed; Theo pads out in striped socks with the whale
  ['dawn_muddy', {
    build(ctx) {
      const L = lawn(ctx); const b = L.slot('bed0'); const yaw = b.yaw; const fwd = new THREE.Vector3(Math.sin(yaw + Math.PI), 0, Math.cos(yaw + Math.PI)), side = new THREE.Vector3(fwd.z, 0, -fwd.x);
      const g = K.makeGnome('grandpa', { lantern: 0.5 }); sets.place(g, b); ctx.add(g); K.setLantern(g, 0.5);
      const h = K.makeCharacter('heroMuddy', { face: 'content' }); K.setPose(h, { ...K.POSES.sitFloor, armLx: 10, armRx: 30 }); h.position.copy(V(b.pos).addScaledVector(fwd, 2.6 * S).addScaledVector(side, 1.4 * S)); h.position.y = 0; h.rotation.y = yaw + Math.PI - 1.3; ctx.add(h);
      const th = K.makeCharacter('theoSocks', { face: 'wonder' }); C.holdWhale(th, C.stuffedWhale(), 'underArm'); K.setPose(th, { armLx: 10, armLz: -8, ...K.walkCycle(0.3, { period: 1.0, legs: 22, holdArms: true }) }); th.position.copy(V(b.pos).addScaledVector(fwd, 4.6 * S).addScaledVector(side, -1.8 * S)); th.position.y = 0; th.rotation.y = yaw + Math.PI + 0.5; ctx.add(th);
      const tgt = V(b.pos).addScaledVector(fwd, 3.2 * S); tgt.y = 1.5 * S; const pos = tgt.clone().addScaledVector(fwd, 8.5 * S).addScaledVector(side, 5.5 * S); pos.y = 2.2 * S;
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: 55 });
      ctx.shared.rig = sets.dawn(ctx, { set: L.set }); ctx.camera.push(0.15, { mode: 'dolly' });
    },
    quality: { shadows: 'pcfsoft' },
  }],
  // 16: s07 / s96 look - the jump-cut shrink, seated: Grandma vs Grandma short (sleeves over the hands, feet dangling)
  ['short_sit', {
    build(ctx) {
      studio(ctx, { grade: 'day', top: '#d8c0a8', bottom: '#6a4a3a' });
      const seatM = new THREE.MeshStandardMaterial({ color: '#c86f93', roughness: 0.7 }), rugM = new THREE.MeshStandardMaterial({ color: '#e8d2b8', roughness: 0.95 });
      const mk = (name, x, y, face) => { const a = K.makeCharacter(name, { face }); K.setPose(a, name.endsWith('Short') ? K.CAST_POSES.sitDangle : K.POSES.sit); a.position.set(x, y + K.seatOffset(a, 1.5), 0); ctx.add(a); const s = new THREE.Mesh(new THREE.BoxGeometry(2.6 * S, 1.5 * S, 1.6 * S), seatM); s.position.set(x, y + 0.75 * S, -0.62 * S); ctx.add(s); const r = new THREE.Mesh(new THREE.BoxGeometry(2.4 * S, 0.06, 2.4 * S), rugM); r.position.set(x, y + 0.03, 0.3); ctx.add(r); ctx.add(label(name, [x, y - 0.08, 0.7], 0.07)); return a; };
      mk('grandma', -0.48, 1.55, 'content'); mk('grandmaShort', 0.48, 1.55, 'wonder'); mk('heroOld', -0.48, 0, 'content'); mk('heroOldShort', 0.48, 0, 'wonder');
      ctx.camera.set({ pos: [4.4, 1.6, 4.2], target: [0, 1.25, 0.1], fov: 34 });
    },
  }],
  // 17: mole rise frame (crumbs popping off the crest) + a sinking one behind
  ['mole_rise', {
    build(ctx) {
      const L = lawn(ctx); const sl = L.slot('lawn1'); const yaw = sl.yaw + Math.PI; const fwd = new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw)), side = new THREE.Vector3(fwd.z, 0, -fwd.x);
      const a = C.makeMole({ seed: 21 }); a.position.copy(V(sl.pos).addScaledVector(side, 0.4 * S)); a.rotation.y = yaw - 0.2; ctx.add(a);
      const b = C.makeMole({ seed: 22, preset: 'small' }); b.position.copy(V(sl.pos).addScaledVector(side, 3.5 * S).addScaledVector(fwd, -2 * S)); b.rotation.y = yaw + 0.4; ctx.add(b);
      ctx.shared.a = a; ctx.shared.b = b;
      const c = camAt(ctx, V(sl.pos).toArray(), yaw, { dist: 5.5, height: 1.5, fov: 55, aim: V(sl.pos).addScaledVector(side, 1.0 * S).addScaledVector(fwd, -0.4 * S).add(new THREE.Vector3(0, 0.4 * S, 0)).toArray() });
      ctx.shared.rig = sets.nightLawn(ctx, { set: L.set, subject: { pos: V(sl.pos).add(new THREE.Vector3(0, 0.5 * S, 0)).toArray(), cd: 1.0 }, window: { n: 1 }, hemiIntensity: 1.05, moon: { az: c.camYaw - 20, el: 30, size: 7, style: 'tf' }, skyPreset: GALAXY_LOW, postOpts: { exposure: 1.12 } });
      ctx.camera.push(0.15);
    },
    update(ctx, t) { C.animateMole(ctx.shared.a, t, { rise: 0.3, unfurl: 0.6, eyesOn: 0.7 }); C.animateMole(ctx.shared.b, t, { sink: 0.6 }); },
  }],
  // 18: GULP - the turf closes round a plastic gnome like a mouth (moleField.swallow at 0.5 s)
  ['gulp', {
    build(ctx) {
      const L = lawn(ctx); const b = L.slot('lawn1'); const yaw = b.yaw + Math.PI; const fwd = new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw));
      const pg = K.makePlasticGnome({ finish: 'glossy' }); pg.position.set(...b.pos); pg.rotation.y = yaw; ctx.add(pg);
      const f = C.moleField(ctx, { center: [b.pos[0], b.pos[2]], size: [16, 16], res: 96, seed: 'qa18', heads: false }); ctx.add(f.group);
      const st = V(b.pos).addScaledVector(fwd, -5 * S); const k = f.add({ at: [st.x, st.z] }); f.travel(k, [[st.x, st.z], [b.pos[0], b.pos[2]]], -1, 3.6); f.swallow(k, pg, 0.5); ctx.shared.f = f;
      const c = camAt(ctx, V(b.pos).toArray(), yaw, { dist: 4.2, height: 0.9, fov: 70, aim: V(b.pos).add(new THREE.Vector3(0, 0.6 * S, 0)).toArray() });
      ctx.shared.rig = sets.nightLawn(ctx, { set: L.set, subject: { pos: V(b.pos).add(new THREE.Vector3(0, 0.6 * S, 0)).toArray(), cd: 0.9 }, window: { n: 1 }, hemiIntensity: 1.05, moon: { az: c.camYaw - 20, el: 30, size: 7, style: 'tf' }, skyPreset: GALAXY_LOW, postOpts: { exposure: 1.12 } });
      ctx.camera.push(0.2);
    },
    update(ctx, t) { ctx.shared.f.update(t); },
  }],
];

export default {
  name: 'creatures_qa', fps: 60, width: 1080, height: 1920, seed: 'ep01-creatures', duration: SHOTS.length * 2,
  quality: { shadows: 'off' }, post: sets.postPreset('nightHigh'),
  shots: SHOTS.map(([name, b], i) => ({ name, start: 2 * i, end: 2 * i + 2, build: b.build, update: b.update || (() => {}), quality: b.quality })),
};
