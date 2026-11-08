// QA board for the suburb night kit: one shot per set, rendered as stills (1 s each).
//   node tools/render.js engine/kit/_sets_qa.js <outdir> times=0.5,1.5,2.5,3.5,4.5,6.5,7.45,8.5,9.5 quality=final
// (street, lawn, porch, closeup, porchOut, [5.5 plan: debug top-down of every slot], dusk, magic, dawn, props board)
// Stand-in characters come from the look-dev kit (lookdev/js/chars.js): gnomes normalised to 2.0 studs (VISUAL_BIBLE
// §2.6), an R6 kid at 5.2 studs. Every street gnome stands on a lawn slot facing its house (back to the street).
import * as THREE from 'three';
import * as kit from './sets.js';
import { makeGnome, makeKid } from '../../lookdev/js/chars.js';

const S = kit.STUD;
const VARIANTS = [
  { hat: '#c4212b', coat: '#2f58c4' }, { hat: '#2f6a3a', coat: '#c4212b' }, { hat: '#3a58b8', coat: '#d9a52c' }, { hat: '#c4212b', coat: '#3f7a3a' },
  { hat: '#7a3aa0', coat: '#c86a2a' }, { hat: '#d9a52c', coat: '#7a2a2a' }, { hat: '#c4212b', coat: '#5a5a62', glasses: true },
];
function gnome(ctx, v = 0, o = {}) {
  const t = ctx.cache('qa:gnome:' + v + JSON.stringify(o), () => {
    const g = makeGnome({ ...VARIANTS[v % VARIANTS.length], lantern: { lit: false, power: 1, lights: false }, seed: v + 1, lod: o.lod ?? 0.5, ...o });
    const k = (2.0 / (g.userData.height || 2.95)) * S; const w = new THREE.Group(); g.scale.setScalar(k); w.add(g); return w;
  });
  return t.clone(true);
}
function grandpa(ctx) { return gnome(ctx, 0, { hat: '#6b6b2e', coat: '#c4212b', lod: 1 }); }
function placeGnome(ctx, set, slot, v) {
  const g = slot.name.endsWith('grandpa') ? grandpa(ctx) : gnome(ctx, v); kit.place(g, slot); ctx.add(g);
  ctx.add(kit.contactShadow(ctx, { pos: slot.pos, radius: 0.24, opacity: 0.4 })); return g;
}

// Every lot gets its bed gnome(s) and 2-3 lawn gnomes (deterministic), all facing their house.
function streetGnomes(ctx, set, { all = [], skip = [] } = {}) {
  const r = ctx.rngFor('qaGnomes'); let k = 0;
  for (const l of set.userData.lots) {
    if (skip.includes(l.id)) continue;
    const slots = kit.slotsOf(set, { kind: 'gnome', lot: l.id });
    const pick = all.includes(l.id) ? slots.filter((s) => /bed0|bed1|lawn/.test(s.name)) : slots.filter((s) => /bed0|lawn/.test(s.name)).filter((s, i) => i === 0 || r() < 0.6);
    for (const s of pick) placeGnome(ctx, set, s, k++);
  }
}

const shot = (name, start, build, update) => ({ name, start, end: start + 1, build, update });
export default {
  name: 'sets_qa', fps: 60, width: 1080, height: 1920, seed: 'kit-qa',
  quality: { shadows: 'off' },
  shots: [
    // 1. Wide street at night, gnomes on every lawn facing their houses (backs to the street).
    shot('street', 0, (ctx) => {
      const set = kit.buildStreet(ctx, { seed: 'ep01', lotsPerSide: 6, hero: { side: 'A', index: 2 } }); ctx.add(set);
      streetGnomes(ctx, set, { all: ['A2', 'A1', 'A0'] });
      const v = set.userData.views.streetWide; ctx.camera.set(v).push(0.19);
      ctx.shared.rig = kit.nightStreet(ctx, { set });
      ctx.shared.fx = kit.sparkles(ctx, { center: v.target.map((x, i) => (i === 1 ? 2.5 : x)), size: [14, 5, 10], count: 8, px: [40, 70] }); ctx.add(ctx.shared.fx);
    }, (ctx, t) => ctx.shared.fx.update(t)),
    // 2. A single lawn (hero lot) at eye level from the sidewalk.
    shot('lawn', 1, (ctx) => {
      const set = kit.buildLot(ctx, { seed: 'ep01', hero: { house: { type: 'bungalow', wall: 'siding', wallColor: '#9fae8c', porch: 'center', roof: 'side', lit: [1, 0, 1, 1] } } }); ctx.add(set);
      const id = set.userData.lots.find((l) => l.hero).id; let k = 0;
      for (const s of kit.slotsOf(set, { kind: 'gnome', lot: id }).filter((s) => /bed0|bed1|lawn0|lawn1|lawn2/.test(s.name))) placeGnome(ctx, set, s, k++);
      const v = set.userData.views.lawn; ctx.camera.set(v).push(0.19);
      ctx.shared.rig = kit.nightStreet(ctx, { set, highKey: true });
      ctx.shared.fx = kit.sparkles(ctx, { center: v.target, size: [8, 4, 6], count: 10 }); ctx.add(ctx.shared.fx);
    }, (ctx, t) => ctx.shared.fx.update(t)),
    // 3. Porch: the kid at the door (character slot), lanterns, lit windows, railing, steps.
    shot('porch', 2, (ctx) => {
      const set = kit.buildLot(ctx, { seed: 'ep01', hero: { house: { type: 'twoStorey', wall: 'siding', wallColor: '#d9cfb5', porch: 'full', lit: [1, 1, 1, 0, 1, 0, 0, 0] } } }); ctx.add(set);
      const id = set.userData.lots.find((l) => l.hero).id;
      const kid = ctx.cache('qa:kid', () => { const k = makeKid({ face: 'wonder' }); const w = new THREE.Group(); k.scale.setScalar(S); w.add(k); return w; }).clone(true);
      const sl = kit.slot(set, id + '.porchDoor'); kit.place(kid, { ...sl, pos: [sl.pos[0] - 0.5, sl.pos[1], sl.pos[2]], yaw: sl.yaw + 0.7 }); ctx.add(kid);
      const v = set.userData.views.porch; ctx.camera.set(v).push(0.19);
      ctx.shared.rig = kit.porchGlow(ctx, { set });
      ctx.shared.fx = kit.sparkles(ctx, { center: v.target, size: [4, 3, 3], count: 9 }); ctx.add(ctx.shared.fx);
    }, (ctx, t) => ctx.shared.fx.update(t)),
    // 4. Lawn close-up: grandpa in his flowerbed under the lit bedroom window, grass blades, stones, porch steps.
    shot('closeup', 3, (ctx) => {
      const set = kit.buildLawnCloseup(ctx, { seed: 'ep01' }); ctx.add(set);
      const id = set.userData.lots.find((l) => l.hero).id;
      const g = grandpa(ctx); const s = kit.slot(set, id + '.bed0'); kit.place(g, s); ctx.add(g);
      ctx.add(kit.contactShadow(ctx, { pos: s.pos, radius: 0.24, opacity: 0.45 }));
      for (const n of ['lawn0', 'lawn2']) placeGnome(ctx, set, kit.slot(set, id + '.' + n), 3);
      const v = set.userData.views.gnomeCU; ctx.camera.set(v).push(0.19);
      ctx.shared.rig = kit.nightLawn(ctx, { set, subject: { pos: [s.pos[0], s.pos[1] + 0.3, s.pos[2]] } });
      ctx.shared.fx = kit.sparkles(ctx, { center: [s.pos[0], 0.9, s.pos[2] + 0.6], size: [2.5, 1.4, 1.6], count: 9 }); ctx.add(ctx.shared.fx);
    }, (ctx, t) => ctx.shared.fx.update(t)),
    // 5. Reverse: from the porch out to the street, every gnome facing the camera (they face their houses).
    shot('porchOut', 4, (ctx) => {
      const set = kit.buildLawnCloseup(ctx, { seed: 'ep01' }); ctx.add(set);
      streetGnomes(ctx, set, { all: ['A1'] });
      const v = set.userData.views.porchOut; ctx.camera.set(v).push(0.19);
      ctx.shared.rig = kit.porchGlow(ctx, { set });
      ctx.shared.fx = kit.sparkles(ctx, { center: v.target, size: [8, 3, 8], count: 8 }); ctx.add(ctx.shared.fx);
    }, (ctx, t) => ctx.shared.fx.update(t)),
    // 6. Plan (debug): top-down over the hero lot with a gnome on EVERY gnome slot and a kid on every character slot.
    shot('plan', 5, (ctx) => {
      const set = kit.buildLawnCloseup(ctx, { seed: 'ep01' }); ctx.add(set); const id = set.userData.lots.find((l) => l.hero).id; let k = 0;
      for (const s of kit.slotsOf(set, { lot: id })) { if (s.kind === 'gnome') placeGnome(ctx, set, s, k++); else { const m = new THREE.Mesh(new THREE.ConeGeometry(0.25, 0.8, 4), new THREE.MeshBasicMaterial({ color: '#ff3030' })); m.rotation.x = Math.PI / 2; const g = new THREE.Group(); m.position.z = 0.3; g.add(m); kit.place(g, s); g.position.y += 0.4; ctx.add(g); } }
      const L = kit.lot(set, id); ctx.camera.set({ pos: [L.origin[0], 26, L.origin[2] - 3.8], target: [L.origin[0], 0, L.origin[2] - 3.79 + 0.001], fov: 40 });
      kit.nightStreet(ctx, { set, highKey: true }); ctx.shared.fx = { update() {} };
    }, () => {}),
    // 7. Dusk garden (EP01 frame 1 / epilogue): deck chair facing the lit window, a dandelion clock, low warm sun.
    { name: 'dusk', start: 6, end: 7, quality: { shadows: 'pcfsoft' }, build(ctx) {
      const set = kit.buildLawnCloseup(ctx, { seed: 'ep01' }); ctx.add(set); const id = set.userData.lots.find((l) => l.hero).id;
      const sl = kit.slot(set, id + '.bedFront0'); const chair = kit.props.prop('deckChair'); const cw = new THREE.Group(); chair.scale.setScalar(S); cw.add(chair);
      kit.place(cw, { pos: [sl.pos[0] + 0.25, 0, sl.pos[2] + 1.3], yaw: sl.yaw }); chair.traverse((o) => { if (o.isMesh) o.castShadow = true; }); ctx.add(cw);
      const dd = kit.props.prop('dandelion', { height: 1.3 }); const dw = new THREE.Group(); dd.scale.setScalar(S); dw.add(dd); kit.place(dw, { pos: [sl.pos[0] + 1.3, 0, sl.pos[2] + 1.6], yaw: 0 }); ctx.add(dw);
      const C = [sl.pos[0] + 0.25, 0, sl.pos[2] + 1.3];
      ctx.camera.set({ pos: [C[0] + 1.1, 1.05, C[2] + 2.1], target: [C[0] - 0.25, 1.05, C[2] - 1.6], fov: 60 }).push(0.19);
      kit.dusk(ctx, { set }); ctx.shared.fx = kit.sparkles(ctx, { center: [sl.pos[0] + 0.8, 1.0, sl.pos[2] + 1.5], size: [2, 1, 1.5], count: 5, colors: ['#ffe2c4'] }); ctx.add(ctx.shared.fx);
    }, update: (ctx, t) => ctx.shared.fx.update(t) },
    // 8. Magic glow (P3): a lit lantern gnome, gold/pink dust, a 0.35 s VFX burst caught mid-flight.
    { name: 'magic', start: 7, end: 8, build(ctx) {
      const set = kit.buildLawnCloseup(ctx, { seed: 'ep01' }); ctx.add(set); const id = set.userData.lots.find((l) => l.hero).id;
      const s = kit.slot(set, id + '.lawn2'); const g = ctx.cache('qa:litGnome', () => { const gg = makeGnome({ hat: '#6b6b2e', coat: '#c4212b', lantern: { lit: true, power: 1.4, lights: false }, lod: 1 }); const w = new THREE.Group(); gg.scale.setScalar((2.0 / gg.userData.height) * S); w.add(gg); return w; }).clone(true);
      kit.place(g, s); ctx.add(g); g.updateMatrixWorld(true);
      const lp = new THREE.Vector3(); (g.getObjectByName('lantern') || g).getWorldPosition(lp); lp.y += 0.05;
      ctx.camera.set({ pos: [s.pos[0] + 0.5, 0.55, s.pos[2] - 1.7], target: [s.pos[0], 0.42, s.pos[2]], fov: 62 }).push(0.19);
      kit.magicGlow(ctx, { set, source: lp.toArray() });
      const dust = kit.magicDust(ctx, { center: lp.toArray(), radius: 0.35, height: 0.6, count: 26 }); const b = kit.burst(ctx, { pos: lp.toArray(), t0: 0.3, spread: 0.45 });
      ctx.add(kit.lightPool(ctx, { pos: [lp.x, 0, lp.z], radius: 0.7, color: '#ffb85c', opacity: 0.45 }));
      ctx.shared.fx = { update: (t) => { dust.update(t); b.update(t); } }; ctx.add(dust, b);
    }, update: (ctx, t) => ctx.shared.fx.update(t) },
    // 9. Pink dawn (P4): the street, lamps and windows off, long soft shadows.
    { name: 'dawn', start: 8, end: 9, quality: { shadows: 'pcfsoft' }, build(ctx) {
      const set = kit.buildStreet(ctx, { seed: 'ep01', lotsPerSide: 6, hero: { side: 'A', index: 2 } }); ctx.add(set); streetGnomes(ctx, set, { all: ['A2', 'A1', 'A0'] });
      const v = set.userData.views.streetWide; ctx.camera.set(v).push(0.19);
      kit.dawn(ctx, { set, target: [v.target[0] + 3, 0, v.target[2]] }); ctx.shared.fx = { update() {} };
    }, update: () => {} },
    // 10. Props board (debug): moving truck (open back, ramp, labelled boxes), sign, agent board, kennel, car, hydrant.
    { name: 'props', start: 9, end: 10, build(ctx) {
      const set = kit.buildLot(ctx, { seed: 'ep01' }); ctx.add(set); const L = kit.lot(set, set.userData.lots.find((l) => l.hero).id);
      const at = (name, o, x, z, yaw = 0) => { const p = kit.props.prop(name, o); p.scale.setScalar(S); const w = new THREE.Group(); w.add(p); w.position.set(L.origin[0] + x, 0, z); w.rotation.y = yaw; ctx.add(w); return w; };
      at('movingTruck', {}, 6.5, -1.7, Math.PI / 2);
      at('postSign', { lines: ['KEEP OFF', 'THE LAWN', 'AFTER DARK'], header: 'NOTICE' }, -2.6, L.origin[2] - 1.2, 0.3);
      at('agentBoard', { lines: ['COMES WITH', 'ANCESTORS'], header: 'FOR SALE' }, -0.6, L.origin[2] - 1.0, 0);
      at('kennel', {}, -3.2, L.origin[2] - 4.5, 0.5); at('hydrant', {}, -4.2, L.origin[2] + 1.6); at('car', {}, -9, 1.6, Math.PI / 2);
      ctx.camera.set({ pos: [L.origin[0] - 3.2, 2.4, 3.4], target: [L.origin[0] + 1.2, 1.0, -3.6], fov: 70 });
      kit.nightStreet(ctx, { set }); ctx.shared.fx = { update() {} };
    }, update: () => {} },
  ],
};
