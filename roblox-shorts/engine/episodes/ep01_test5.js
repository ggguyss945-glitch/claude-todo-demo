// EP01 "Never Move Grandpa" - 5-second look test (voice line 01):
//   "In this world, grandparents don't die. They turn into garden gnomes."
// Shot list, timings and every storyboard decision come from episodes/ep01/test5_timeline.json (board:
// episodes/ep01/test5_board.md). This module loads that JSON itself (top-level await), so it renders directly:
//   node tools/render.js engine/episodes/ep01_test5.js <out.mp4> quality=final workers=3
// Builders (one per timeline `shot` key): sky_to_street, porch_couple, grandma_cu, poof_swing, gnome_hero.
// Everything is a pure function of shot time t (seeded, no Math.random), built from engine/kit (sets + characters).
import * as THREE from 'three';
import * as sets from '../kit/sets.js';
import * as K from '../kit/chars.js';
import { makeRng, hash32 } from '../core/random.js';

const S = sets.STUD;                 // 1 stud = 0.32 m
const DEG = Math.PI / 180;
const TL = await (await fetch(new URL('../../episodes/ep01/test5_timeline.json', import.meta.url))).json();
const SHOT_START = Object.fromEntries(TL.shots.map((s) => [s.shot, s.start]));
const V3 = (a) => new THREE.Vector3(a[0], a[1], a[2]);
const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
const outQuart = (x) => 1 - Math.pow(1 - clamp01(x), 4);
// Event time inside a shot (seconds from the shot start), from the timeline's events[] (episode seconds).
const evT = (ctx, word) => { const e = (ctx.params.events || []).find((x) => x.word === word); return e ? e.frame / TL.fps - ctx.shot.f0 / TL.fps : null; };

// ------------------------------------------------------------------ small helpers
// Sprite with a constant on-screen size in OUTPUT pixels (same convention as kit/fx.js).
function pxSprite(mat, px = 40) {
  const s = new THREE.Sprite(mat); s.userData.px = px;
  s.onBeforeRender = function (r, sc, cam) { const k = (this.userData.px * 2) / (1920 * cam.projectionMatrix.elements[5]); this.scale.set(k, k, 1); this.updateMatrixWorld(); };
  return s;
}
// One big 4-point star glint (TF coin glint) on a precious prop: 0 -> peak px in 3 frames, gone by +16 frames.
function starGlint(ctx, { pos, t0, peak = 110, rot = 25, color = '#f4ecff' }) {
  const mat = new THREE.SpriteMaterial({ map: ctx.tex.sparkle({ points: 4, sharpness: 22, core: 0.6 }), color: new THREE.Color(color).multiplyScalar(2.4), blending: THREE.AdditiveBlending, depthWrite: false, depthTest: false, transparent: true, fog: false, sizeAttenuation: false });
  const s = pxSprite(mat, 0); s.position.copy(pos); s.renderOrder = 30; s.visible = false;
  const core = pxSprite(new THREE.SpriteMaterial({ map: ctx.tex.radialGlow({ falloff: 2.2 }), color: new THREE.Color('#fff4ff').multiplyScalar(1.6), blending: THREE.AdditiveBlending, depthWrite: false, depthTest: false, transparent: true, fog: false, sizeAttenuation: false }), 0);
  core.position.copy(pos); core.renderOrder = 29; core.visible = false;
  const g = new THREE.Group(); g.add(core, s);
  g.update = (t) => {
    const f = (t - t0) * 60; const on = f > -0.5 && f < 16.5; s.visible = core.visible = on; if (!on) return;
    const k = f < 3 ? (f + 1) / 4 : Math.pow(1 - (f - 3) / 13.5, 1.6);
    s.userData.px = peak * k; core.userData.px = peak * 0.42 * k; mat.rotation = rot * DEG * clamp01(f / 16); s.material.opacity = 1; core.material.opacity = 0.7 * k;
  };
  g.update(-1); return g;
}
// Cartoon "poof" cloud that hides a 1-frame transformation swap: soft white-lavender puffs (normal blending, drawn over
// everything) that are full on the swap frame, half a frame before, then swell and fade over `dur`.
function poofCloud(ctx, { pos, t0, dur = 0.3, count = 8, spread = [0.45, 0.6, 0.25], px = [230, 400], colors = ['#f6f0ff', '#efe4ff', '#fff2f6', '#ffffff'], seed = 'poof' }) {
  const g = new THREE.Group(); g.name = 'poofCloud'; const r = makeRng(hash32('ep01t5', seed)); const tex = ctx.tex.radialGlow({ falloff: 1.9 });
  for (let i = 0; i < count; i++) {
    const m = new THREE.SpriteMaterial({ map: tex, color: new THREE.Color(colors[i % colors.length]).multiplyScalar(1.15), transparent: true, depthWrite: false, depthTest: false, fog: false, sizeAttenuation: false });
    const s = pxSprite(m, 0); s.renderOrder = 25 + i; const o = new THREE.Vector3((r() - 0.5) * 2 * spread[0], (r() - 0.35) * 2 * spread[1], (r() - 0.5) * 2 * spread[2]);
    s.userData.d = { o, px: px[0] + (px[1] - px[0]) * r(), life: 0.75 + 0.5 * r(), drift: 0.35 + 0.4 * r() }; s.visible = false; g.add(s);
  }
  g.update = (t) => {
    for (const s of g.children) {
      const d = s.userData.d; const u = (t - t0) / (dur * d.life);
      if (u < -1.1 / (60 * dur * d.life) || u > 1) { s.visible = false; continue; } s.visible = true;
      const a = u < 0 ? 0.5 : Math.pow(1 - u, 2.2) * 0.98; const k = u < 0 ? 0.8 : 1 + 0.55 * (1 - Math.pow(1 - u, 2));
      s.position.set(pos[0] + d.o.x * (1 + d.drift * Math.max(0, u)), pos[1] + d.o.y * (1 + d.drift * Math.max(0, u)) + 0.08 * Math.max(0, u), pos[2] + d.o.z);
      s.userData.px = d.px * k; s.material.opacity = a;
    }
  };
  g.update(-10); return g;
}
// Put a stud-unit object into a metre-scaled wrapper.
function studWrap(obj) { const w = new THREE.Group(); w.scale.setScalar(S); w.add(obj); return w; }

// ------------------------------------------------------------------ the porch swing (new prop, studs)
// Slatted painted-wood bench (8.6 x 1.6 studs, seat top 1.5 above the deck, back 1.6 tall, armrests) hanging on four chains
// from two ceiling hooks. The bench is wider than the board's 5.5 studs because two seated R6 bodies (4 studs wide each,
// arms included) need 8.2. Origin = deck point under the bench centre; front = +Z (sitters face the street).
// Returns { root, pivot } where `pivot` (at the hooks' height H) is what sways; riders are added to `seat` (studs).
const SWING = { W: 8.6, D: 1.6, seatY: 1.5, back: 1.6, wood: '#e9e4da', chain: '#3a3a40' };
function buildSwing(ctx, H) {
  const tpl = ctx.cache('ep01t5:swing:' + H.toFixed(3), () => {
    const { W, D, seatY, back } = SWING; const wk = 'trim:' + SWING.wood, ck = 'metal:' + SWING.chain;
    const root = new THREE.Group(); root.name = 'porchSwing';
    const pivot = new THREE.Group(); pivot.name = 'swingPivot'; pivot.position.set(0, H, 0); root.add(pivot);
    const P = new sets.Parts(); P.push(new THREE.Matrix4().makeTranslation(0, -H, 0)); // build in deck coordinates, hang from the pivot
    // seat slats (front to back) + frame rails
    for (let i = 0; i < 6; i++) P.box(wk, W - 0.3, 0.13, 0.22, [0, seatY - 0.065, -0.6 + 0.04 + i * (D - 0.08) / 5.6 + 0.11], null, { bevel: 0.03 });
    for (const z of [-0.6, D - 0.6]) P.box(wk, W, 0.22, 0.2, [0, seatY - 0.2, z]);
    for (const x of [-W / 2 + 0.1, W / 2 - 0.1]) P.box(wk, 0.22, 0.22, D, [x, seatY - 0.2, D / 2 - 0.6]);
    // backrest: reclined 12 deg, five horizontal boards between two end posts
    P.push(new THREE.Matrix4().makeTranslation(0, seatY, -0.62).multiply(new THREE.Matrix4().makeRotationX(-12 * DEG)));
    for (const x of [-W / 2 + 0.1, W / 2 - 0.1]) P.box(wk, 0.24, back + 0.15, 0.2, [x, (back + 0.15) / 2, 0]);
    for (let i = 0; i < 5; i++) P.box(wk, W - 0.3, 0.2, 0.1, [0, 0.22 + i * (back - 0.25) / 4.2, 0], null, { bevel: 0.02 });
    P.box(wk, W + 0.1, 0.18, 0.28, [0, back + 0.18, 0], null, { bevel: 0.03 });
    P.pop();
    // armrests on turned posts
    for (const s of [-1, 1]) { const x = s * (W / 2 - 0.1); P.box(wk, 0.28, 0.14, D + 0.15, [x, seatY + 0.9, D / 2 - 0.6]); P.box(wk, 0.18, 0.9, 0.18, [x, seatY + 0.45, D - 0.7]); }
    // chains: two per side, front and back armrest corners up to one hook per side; drawn as short links
    for (const s of [-1, 1]) {
      const hook = [s * (W / 2 - 0.3), H - 0.15, 0.2];
      for (const z of [-0.55, D - 0.65]) {
        const a = new THREE.Vector3(s * (W / 2 - 0.1), seatY + 0.97, z), b = new THREE.Vector3(...hook); const n = Math.round(a.distanceTo(b) / 0.32);
        for (let k = 0; k < n; k++) { const p0 = a.clone().lerp(b, k / n), p1 = a.clone().lerp(b, (k + 0.85) / n); P.bar(ck, p0.toArray(), p1.toArray(), k % 2 ? 0.05 : 0.11, k % 2 ? 0.11 : 0.05); }
      }
    }
    P.pop();
    const mesh = P.build(sets.M, { name: 'swingMesh', cast: false, receive: true }); pivot.add(mesh);
    const seat = new THREE.Group(); seat.name = 'swingSeat'; seat.position.set(0, -H, 0); pivot.add(seat); // riders: deck coordinates
    // ceiling hooks (static)
    const HP = new sets.Parts(); for (const s of [-1, 1]) { HP.box(ck, 0.3, 0.3, 0.3, [s * (W / 2 - 0.3), H + 0.05, 0.2]); HP.cyl(ck, 0.05, 0.05, 0.3, 8, [s * (W / 2 - 0.3), H - 0.1, 0.2]); }
    root.add(HP.build(sets.M, { name: 'swingHooks' }));
    return studWrap(root);
  });
  const w = tpl.clone(true);
  return { root: w, pivot: w.getObjectByName('swingPivot'), seat: w.getObjectByName('swingSeat') };
}

// ------------------------------------------------------------------ the porch (s02-s04)
// The couple's bungalow: a deep full-width porch (11 studs, so the low s04 camera can stand inside the railing), both
// front windows lit, the swing to the right of the door in front of the right window, wall lanterns either side of the door.
const PORCH_HOUSE = { type: 'bungalow', wall: 'siding', wallColor: '#cdb79c', roofColor: '#3b3440', doorColor: '#6b1f1a', shutterColor: '#3b4347', porch: 'full', porchDepth: 11, offsetX: 0, lit: [1, 1, 0, 1], curtain: '#b84a5a', number: '14', planters: false, seed: 77 };
const SWING_X = 7.6, SWING_Z = 2.4, SEAT_X = 2.0; // studs from the door (x) and the front wall (z)
function swingSway(T) { return 2.5 * Math.sin(2 * Math.PI * 0.45 * T + 0.6); } // degrees, episode time (continuous over cuts)

function porchScene(ctx, { gnomes = false } = {}) {
  const set = sets.buildLot(ctx, { seed: 'ep01', hero: { house: PORCH_HOUSE } }); ctx.add(set);
  const L = set.userData.lots.find((l) => l.hero);
  const deckY = L.deckY; const wallZ = L.door[2] - 0.3 * S;
  const H = 8.8; // hook height above the deck (porch ceiling underside: beamY + 0.9 - F)
  const C = new THREE.Vector3(L.door[0] + SWING_X * S, deckY, wallZ + SWING_Z * S); // deck point under the bench centre (m)
  const sw = buildSwing(ctx, H); sw.root.position.copy(C); ctx.add(sw.root);
  ctx.add(sets.contactShadow(ctx, { pos: [C.x, deckY + 0.004, C.z + 0.25 * S], radius: 1.55, opacity: 0.32 }));
  // the couple (studs, children of the swinging seat): Grandma on the left of frame (-x), Grandpa on the right (+x)
  const gm = ctx.instance('ep01t5:grandma', () => K.makeCharacter('grandma', { units: 'stud', shadow: false }));
  const gp = ctx.instance('ep01t5:grandpa', () => K.makeCharacter('grandpa', { units: 'stud', shadow: false }));
  gm.position.set(-SEAT_X, 0, 0.05); gp.position.set(SEAT_X, 0, 0.05);
  K.setPose(gm, { ...K.POSES.sit, armLx: 6, armRx: 26, armLz: 0, armRz: 2, neckY: 7, neckZ: -3 });   // inner arm down: holding hands
  K.setPose(gp, { ...K.POSES.sit, armLx: 24, armRx: 6, armLz: 2, armRz: 0, neckY: -5, neckZ: 2 });
  sw.seat.add(gm, gp);
  const out = { set, L, deckY, wallZ, C, H, swing: sw, gm, gp };
  if (gnomes) { // the transformed couple standing on the seat (hidden until the snap)
    const ggm = K.makeGnome('grandma', { units: 'stud', lantern: false }); const ggp = K.makeGnome('grandpa', { units: 'stud', lantern: 0 });
    ggm.position.set(-SEAT_X, SWING.seatY, 0.25); ggp.position.set(SEAT_X, SWING.seatY, 0.25); ggm.rotation.y = 0.12; ggp.rotation.y = -0.08;
    ggm.visible = ggp.visible = false; sw.seat.add(ggm, ggp); out.ggm = ggm; out.ggp = ggp;
  }
  return out;
}
// World position of a point given in seat (stud) coordinates, at the swing's rest pose.
function seatPoint(P, x, y, z) { return P.C.clone().add(new THREE.Vector3(x * S, y * S, z * S)); }
function headWorld(avatar) { avatar.updateWorldMatrix(true, true); const h = avatar.getObjectByName('head'); return h.getWorldPosition(new THREE.Vector3()); }
function updateSwing(P, T, jolt = null) {
  let rx = swingSway(T), dy = 0;
  if (jolt) { const u = T - jolt.T0; if (u >= 0) { rx += jolt.amp * Math.exp(-2.2 * u) * Math.sin(2 * Math.PI * 1.1 * u); dy = -jolt.dip * (1 - springOne(u, 3, 0.35)); } }
  P.swing.pivot.rotation.x = rx * DEG; P.swing.pivot.position.y = P.H + dy;
}
function springOne(u, f, z) { if (u <= 0) return 0; const w = 2 * Math.PI * f, wd = w * Math.sqrt(1 - z * z); return 1 - Math.exp(-z * w * u) * (Math.cos(wd * u) + (z / Math.sqrt(1 - z * z)) * Math.sin(wd * u)); }

// ------------------------------------------------------------------ street gnomes (s01)
// Every lot on side A gets Grandpa-style family gnomes in its flowerbed and on its lawn, all facing their house (slot
// yaw), lanterns unlit (the lantern is a plot plant). Nearby lots get the 'mid' build, far ones 'low'.
const POINTED = [0, 1, 2, 3, 4, 5, 7]; // family variants with pointed hats (the fishing-hat one reads as a pot from behind)
function streetGnomes(ctx, set, heroId) {
  const r = makeRng(hash32('ep01t5', 'streetGnomes')); let k = 0;
  const hero = set.userData.lots.find((l) => l.id === heroId);
  for (const l of set.userData.lots) {
    if (l.side !== 'A') continue;
    const dist = Math.abs(l.index - hero.index); const lod = dist <= 2 ? 'mid' : 'low';
    for (const s of sets.slotsOf(set, { kind: 'gnome', lot: l.id })) {
      const n = s.name.split('.')[1];
      const take = n === 'bed0' || (n === 'bed1' && r() < 0.7) || (/lawn[0-3]/.test(n) && r() < 0.55);
      if (!take) continue;
      const g = l.id === heroId && n === 'bed0' ? K.makeGnome('grandpa', { lantern: 0, lod: 'mid' }) : K.makeFamilyGnome(POINTED[k++ % POINTED.length], { lod, lantern: 0 });
      sets.place(g, s); g.rotation.y += (r() - 0.5) * 0.12; ctx.add(g);
    }
  }
}

// ------------------------------------------------------------------ shot builders
const BUILDERS = {
  // s01 "In this world," - opener accent: crane + tilt down from the galaxy sky and the moon to the night street,
  // a gnome on every lawn facing its house; outQuart over 0-0.95 s (frame 0 at full speed), roll -9 -> 0, + push 10%.
  sky_to_street: {
    build(ctx) {
      const p = ctx.params, mv = p.camera.move, st = p.camera.start;
      const set = sets.buildStreet(ctx, { seed: 'ep01', lotsPerSide: 6, hero: { side: 'A', index: 3 } }); ctx.add(set);
      const heroId = set.userData.lots.find((l) => l.hero).id; streetGnomes(ctx, set, heroId);
      { const L = set.userData.lots.find((l) => l.hero); const o = L.origin; // two foreground gnomes near the fence: big backs in frame
        [[3.2, -3.4, 5], [-3.4, -6.4, 7], [-12, -4.8, 1]].forEach(([x, z, v]) => { const g = K.makeFamilyGnome(v, { lod: 'mid', lantern: 0 }); g.position.set(o[0] + x * S, 0, o[2] + z * S); g.rotation.y = Math.PI + (v - 5.5) * 0.15; ctx.add(g); }); }
      const v = set.userData.views.streetWide; const P1 = V3(v.pos), T1 = V3(v.target);
      const d = T1.clone().sub(P1); const dist = d.length(); const yaw = Math.atan2(d.x, -d.z); const pitch1 = Math.asin(d.y / dist);
      const hz = new THREE.Vector3(Math.sin(yaw), 0, -Math.cos(yaw));
      const P0 = P1.clone().addScaledVector(hz, -st.back_studs * S).add(new THREE.Vector3(0, st.up_studs * S, 0));
      const pitch0 = st.pitch_deg * DEG; const [r0, r1] = mv.roll_deg;
      const U = (t) => outQuart((t - mv.t0) / (mv.t1 - mv.t0));
      const posAt = (t, out = new THREE.Vector3()) => out.copy(P0).lerp(P1, U(t));
      const dirAt = (t) => { const pt = pitch0 + (pitch1 - pitch0) * U(t); return new THREE.Vector3(Math.sin(yaw) * Math.cos(pt), Math.sin(pt), -Math.cos(yaw) * Math.cos(pt)); };
      // light rig first, from the END framing (practicals = the lamps/windows nearest what the shot lands on)
      ctx.camera.set({ pos: v.pos, target: v.target, fov: v.fov });
      const yawDeg = yaw / DEG;
      ctx.shared.rig = sets.nightStreet(ctx, { set, moon: { az: yawDeg - 5, el: 41, size: 8, style: 'tf' }, skyOpts: { intensity: 1.5 } });
      ctx.camera.set({ pos: (t, o) => posAt(t, o || new THREE.Vector3()), target: (t, o) => (o || new THREE.Vector3()).copy(posAt(t)).addScaledVector(dirAt(t), dist), fov: v.fov, roll: (t) => r0 + (r1 - r0) * U(t) })
        .push(p.camera.push.Z);
      const c = [T1.x * 0.55 + P1.x * 0.45, 0.9, T1.z * 0.55 + P1.z * 0.45];
      ctx.shared.fx = sets.sparkles(ctx, { center: c, size: [9, 3.2, 6], count: p.fx.sparkles.count, px: p.fx.sparkles.px, seed: 's01' }); ctx.add(ctx.shared.fx);
    },
    update(ctx, t) { ctx.shared.fx.update(t); },
  },

  // s02 "grandparents" - MS two-shot of the old couple on the porch swing, eye level at the seated heads; push +19% + truck.
  porch_couple: {
    build(ctx) {
      const p = ctx.params; const P = porchScene(ctx); ctx.shared.P = P;
      K.setFace(P.gm, p.faces.grandma); K.setFace(P.gp, p.faces.grandpa);
      // 7.4 studs (board 9.5): in 9:16 the two-shot is width-limited, so we crop the outer arms (TF/PN MS framing) and
      // keep the faces big; eye level at the seated heads, faces in the upper 35-40%.
      const yaw = 28 * DEG, R = 7.4 * S;
      const tgt = P.C.clone().add(new THREE.Vector3(0, 3.85 * S, 0.3 * S));
      const pos = P.C.clone().add(new THREE.Vector3(Math.sin(yaw) * R, 4.65 * S, Math.cos(yaw) * R + 0.3 * S));
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: p.fov });
      ctx.shared.rig = sets.porchGlow(ctx, { set: P.set, subject: { pos: tgt.toArray(), cd: 1.6, color: '#ffe0c8' } });
      ctx.camera.push(p.camera.move.Z).truck(p.camera.drift.truck_studs * S);
      ctx.shared.fx = sets.sparkles(ctx, { center: [tgt.x, tgt.y + 0.1, tgt.z + 0.5], size: [2.6, 1.6, 1.2], count: p.fx.sparkles.count, px: p.fx.sparkles.px, seed: 's02' }); ctx.add(ctx.shared.fx);
    },
    update(ctx, t) { updateSwing(ctx.shared.P, ctx.T); ctx.shared.fx.update(t); },
  },

  // s03 "don't die." - reaction CU of Grandma, content (^^) from the cut; her glasses glint (4-point star) on "die".
  grandma_cu: {
    build(ctx) {
      const p = ctx.params; const P = porchScene(ctx); ctx.shared.P = P;
      K.setFace(P.gm, p.faces.grandma); K.setFace(P.gp, 'content');
      updateSwing(P, ctx.shot.start); const head = headWorld(P.gm);
      const yaw = 20 * DEG, R = 2.75 * S; // TF reaction CU: the head fills ~55% of the frame width (board: 3.2 studs)
      const tgt = head.clone().add(new THREE.Vector3(0, -0.42 * S, 0));
      const pos = head.clone().add(new THREE.Vector3(Math.sin(yaw) * R, 0.05 * S, Math.cos(yaw) * R));
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: p.fov });
      ctx.shared.rig = sets.porchGlow(ctx, { set: P.set, subject: { pos: head.toArray(), cd: 1.2, color: '#ffe0c8' } });
      ctx.camera.push(p.camera.move.Z).rollBy(p.camera.roll.deg[1] - p.camera.roll.deg[0]);
      // glint on her right lens rim (character's right = -x), frame 104 ("die")
      const gl = P.gm.getObjectByName('glasses'); P.gm.updateWorldMatrix(true, true);
      const lens = gl ? gl.localToWorld(new THREE.Vector3(-0.28, 0.15, 0.69)) : head.clone();
      ctx.shared.glintLocal = gl ? new THREE.Vector3(-0.28, 0.15, 0.69) : null;
      ctx.shared.glint = starGlint(ctx, { pos: lens, t0: evT(ctx, 'die') ?? 0.25, peak: 150, rot: 25 }); // 150 px sprite = a ~110 px visible star ctx.add(ctx.shared.glint);
      ctx.shared.fx = sets.sparkles(ctx, { center: [head.x + 0.1, head.y + 0.05, head.z + 0.25], size: [1.1, 1.0, 0.5], count: p.fx.sparkles.count, px: p.fx.sparkles.px, seed: 's03' }); ctx.add(ctx.shared.fx);
    },
    update(ctx, t) {
      const P = ctx.shared.P; updateSwing(P, ctx.T); ctx.shared.fx.update(t);
      if (ctx.shared.glintLocal) { const gl = P.gm.getObjectByName('glasses'); P.gm.updateWorldMatrix(true, true); const w = gl.localToWorld(ctx.shared.glintLocal.clone()); ctx.shared.glint.children.forEach((c) => c.position.copy(w)); }
      ctx.shared.glint.update(t);
    },
  },

  // s04 "They turn into garden" - low MS from the other front side; magic dust swirls, a sparkle burst on "turn" covers both
  // and they snap into two gnomes on the swing (1-frame swap under the burst core); the swing jolts.
  poof_swing: {
    build(ctx) {
      const p = ctx.params; const P = porchScene(ctx, { gnomes: true }); ctx.shared.P = P;
      K.setFace(P.gm, p.faces.grandma); K.setFace(P.gp, p.faces.grandpa);
      const yaw = -20 * DEG, R = 7.4 * S;
      const tgt = P.C.clone().add(new THREE.Vector3(0, 3.2 * S, 0.3 * S));
      const pos = P.C.clone().add(new THREE.Vector3(Math.sin(yaw) * R, 2.4 * S, Math.cos(yaw) * R + 0.3 * S));
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: p.fov });
      ctx.shared.rig = sets.porchGlow(ctx, { set: P.set, subject: { pos: tgt.toArray(), cd: 1.6, color: '#ffe0c8' } });
      ctx.camera.push(p.camera.move.Z);
      const tb = evT(ctx, 'turn') ?? 0.1333; ctx.shared.tb = tb; ctx.shared.Tb = ctx.shot.start + tb;
      const chest = (x) => seatPoint(P, x, 3.2, 0.9).toArray();
      const cols = ['#ffffff', '#e9dcff', '#ffe2c4', '#ffb0d8'];
      ctx.shared.bursts = [chest(-SEAT_X), chest(SEAT_X)].map((pos, i) => sets.burst(ctx, { pos, t0: tb, dur: 0.35, count: 30, puff: 12, corePx: 520, ringPx: [40, 620], colors: cols, spread: 0.75, puffColor: '#fff0f8', seed: 'poof' + i }));
      ctx.add(...ctx.shared.bursts);
      ctx.shared.poofs = [-SEAT_X, SEAT_X].map((x, i) => poofCloud(ctx, { pos: seatPoint(P, x, 3.0, 0.9).toArray(), t0: tb, seed: 'poof' + i, spread: [0.42, 0.62, 0.2] }));
      ctx.add(...ctx.shared.poofs);
      const mid = seatPoint(P, 0, 2.6, 0.4).toArray();
      ctx.shared.dust = sets.magicDust(ctx, { center: mid, radius: 1.35, height: 1.5, count: 44, rise: 0.25, swirl: 0.9, px: [10, 26], seed: 's04dust' }); ctx.add(ctx.shared.dust);
      ctx.shared.fx = sets.sparkles(ctx, { center: [mid[0], mid[1] + 0.2, mid[2] + 0.4], size: [2.8, 1.6, 1.2], count: 6, px: [40, 70], seed: 's04' }); ctx.add(ctx.shared.fx);
    },
    update(ctx, t) {
      const P = ctx.shared.P, tb = ctx.shared.tb; const after = t >= tb - 1e-6;
      updateSwing(P, ctx.T, { T0: ctx.shared.Tb, amp: 5, dip: 0.15 * 1 });
      P.gm.visible = P.gp.visible = !after; P.ggm.visible = P.ggp.visible = after;
      if (after) { K.gnomeIdle(P.ggm, t, { seed: 'gm' }); K.gnomeIdle(P.ggp, t, { seed: 'gp' }); }
      // dust: builds toward the burst, then settles at a lower level
      ctx.shared.dust.update(t); const k = t < tb ? 0.35 + 0.65 * clamp01(t / tb) : Math.max(0.25, 1 - 1.4 * (t - tb));
      ctx.shared.dust.children.forEach((s) => { s.material.opacity *= k; });
      ctx.shared.bursts.forEach((b) => b.update(t)); ctx.shared.poofs.forEach((b) => b.update(t)); ctx.shared.fx.update(t);
    },
  },

  // s05 "gnomes." - the hero creature: Grandpa as a glazed gnome in his flowerbed facing the house, from below, warm
  // window spill on his face, lantern UNLIT, no blink / head turn (plot devices). Push +28% + crane + roll; silent hold.
  gnome_hero: {
    build(ctx) {
      const p = ctx.params;
      const set = sets.buildLawnCloseup(ctx, { seed: 'ep01' }); ctx.add(set);
      const id = set.userData.lots.find((l) => l.hero).id; const sl = sets.slot(set, id + '.bed0');
      const g = K.makeGnome('grandpa', { lantern: p.lanternLit ? 1 : 0, lanternLight: p.lanternLit ? 0.9 : false }); sets.place(g, sl); ctx.add(g);
      ctx.add(sets.contactShadow(ctx, { pos: sl.pos, radius: 0.24, opacity: 0.45 }));
      // the rest of the family's lawn gnomes: they face the house too, so they stare at the lens
      let k = 0; for (const n of ['lawn0', 'lawn2', 'bedFront1']) { const s = sets.slot(set, id + '.' + n); if (!s) continue; const f = K.makeFamilyGnome(2 + k++, { lantern: 0 }); sets.place(f, s); ctx.add(f); }
      K.setGnomeGaze(g, 0, 10);
      g.updateWorldMatrix(true, true);
      const head = g.getObjectByName('gnomeHead').getWorldPosition(new THREE.Vector3());
      const eyes = g.getObjectByName('ballL').getWorldPosition(new THREE.Vector3()).add(g.getObjectByName('ballR').getWorldPosition(new THREE.Vector3())).multiplyScalar(0.5);
      const fwd = new THREE.Vector3(Math.sin(sl.yaw), 0, Math.cos(sl.yaw)); // the gnome faces the house
      const nose = eyes.clone().addScaledVector(fwd, 0.05 * S); nose.y -= 0.12 * S;
      const pos = nose.clone().addScaledVector(fwd, 1.22 * S); pos.y = 0.95 * S; // CU at the cut -> ECU after the +28% push
      const tgt = nose.clone(); tgt.y = 1.2 * S; // eyes in the upper 40% (bible §7.1), hat tip against the sky
      ctx.shared.cam = { pos, tgt };
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: p.fov });
      // TF moon just off the hat tip, the galaxy sky's nebula lifted so the sky behind the creature carries colour, not void
      const camYaw = Math.atan2(-fwd.x, fwd.z) / DEG; // az of the lens direction (az 0 = -Z, +90 = +X)
      ctx.shared.rig = sets.nightLawn(ctx, { set, subject: { pos: nose.toArray(), cd: 0.6, color: '#ffd9b0' }, window: { n: 1, cd: 2.2, color: '#ffd9a0', maxD: 10 },
        moon: { az: camYaw + 11, el: 27, size: 9, style: 'tf' }, skyOpts: { intensity: 2.4 }, postOpts: { exposure: 1.12 } });
      ctx.camera.push(p.camera.move.Z).crane(p.camera.drift.crane_studs * S).rollBy(p.camera.roll.deg[1] - p.camera.roll.deg[0]);
      // the bedroom-window spill as the face key: warm, from just above and behind the lens (the window is over the camera)
      ctx.add(ctx.lights.point({ color: '#ffc890', intensity: 0.9, pos: pos.clone().addScaledVector(fwd, 0.35).add(new THREE.Vector3(0, 0.55, 0)).toArray(), decay: 2 }));
      ctx.shared.g = g;
      const c = [nose.x - fwd.x * 0.1, nose.y + 0.05, nose.z - fwd.z * 0.1];
      ctx.shared.fx = sets.sparkles(ctx, { center: [c[0] - fwd.x * 0.5, c[1] + 0.1, c[2] - fwd.z * 0.5], size: [1.3, 0.9, 1.2], count: p.fx.sparkles.count, px: p.fx.sparkles.px, seed: 's05' }); ctx.add(ctx.shared.fx);
      ctx.shared.dust = sets.magicDust(ctx, { center: [head.x, sl.pos[1] + 0.25, head.z], radius: 0.35, height: 0.7, count: p.fx.magicDust.count, rise: 0.06, swirl: 0.35, px: [8, 18], seed: 's05dust' }); ctx.add(ctx.shared.dust);
    },
    update(ctx, t) {
      const g = ctx.shared.g; K.gnomeIdle(g, t, { seed: 'hero' });
      if (ctx.params.lanternLit) { const L = K.lanternLightUp(t, 3.75 - ctx.shot.start); K.setLantern(g, L.level * K.lanternFlicker(t), { halo: L.halo }); }
      ctx.shared.fx.update(t); ctx.shared.dust.update(t);
      const k = Math.max(0.3, 1 - t / 2.2); ctx.shared.dust.children.forEach((s) => { s.material.opacity *= k; });
    },
  },
};

export default {
  name: 'ep01_test5', fps: TL.fps, width: TL.width || 1080, height: TL.height || 1920, seed: 'ep01-test5', duration: TL.duration,
  quality: { shadows: 'off' },
  post: sets.postPreset('night'),
  shots: TL.shots.map((e) => ({ name: e.name, start: e.start, end: e.end, params: e.params, ...BUILDERS[e.shot] })),
};
export { BUILDERS as builders, TL as timeline };
