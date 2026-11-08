// EP01 "Never Move Grandpa" - 5-second look test (voice line 01):
//   "In this world, grandparents don't die. They turn into garden gnomes."
// Shot list, timings and storyboard decisions come from episodes/ep01/test5_timeline.json (board:
// episodes/ep01/test5_board.md, review fixes: episodes/ep01/test5_review.md). This module loads that JSON itself (top-level
// await), so it renders directly:
//   node tools/render.js engine/episodes/ep01_test5.js <out.mp4> quality=final workers=3
// or through the timeline (episodes/ep01/test5.js re-exports the builder map):
//   node tools/render.js episodes/ep01/test5_timeline.json <out.mp4> quality=final workers=3
// Builders (one per timeline `shot` key): sky_to_street, porch_couple, grandma_cu, poof_swing, gnome_hero, lawn_stare.
// Everything is a pure function of shot time t (seeded, no Math.random), built from engine/kit (sets + characters).
import * as THREE from 'three';
import * as sets from '../kit/sets.js';
import * as K from '../kit/chars.js';
import { makeRng, hash32 } from '../core/random.js';
import { springStep } from '../core/anim.js';

const S = sets.STUD;                 // 1 stud = 0.32 m
const DEG = Math.PI / 180;
const TL = await (await fetch(new URL('../../episodes/ep01/test5_timeline.json', import.meta.url))).json();
const V3 = (a) => new THREE.Vector3(a[0], a[1], a[2]);
const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
const smooth = (x) => { const u = clamp01(x); return u * u * (3 - 2 * u); };
const outExpo = (x) => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * clamp01(x)));
const outQuad = (x) => 1 - (1 - clamp01(x)) * (1 - clamp01(x));
// Event time inside a shot (seconds from the shot start), from the timeline's events[] (episode seconds).
const evT = (ctx, word) => { const e = (ctx.params.events || []).find((x) => x.word === word); return e ? e.frame / TL.fps - ctx.shot.f0 / TL.fps : null; };
// TF sparkle look (bible rule 9): soft fat 6-8-point snowflakes with a glow core and a soft underlay, 55-95 px.
const SPARK = { sharpness: 7, core: 0.75, underlay: 0.55, underlayOpacity: 0.5, brightness: 2.0, px: [55, 95] };
const GALAXY = { ...sets.SKIES.galaxy, nebula: 0.45 }; // magenta/purple wisps survive the night grade
// Low-angle lawn shots look INTO the sky: lift it to TF's deep blue-violet night (not a black void) so the frame is not
// half crushed black; the nebula band sits where these cameras look (20-60 deg up).
const GALAXY_LOW = { ...sets.SKIES.galaxy, stops: [[-1, '#000000'], [-0.02, '#1c1650'], [0.12, '#140f3e'], [0.35, '#0b0828'], [0.65, '#06041a'], [1, '#030210']], nebula: 0.6, seed: 21 };

// ------------------------------------------------------------------ small helpers
// Sprite with a constant on-screen size in OUTPUT pixels (same convention as kit/fx.js); aspect < 1 makes a streak.
function pxSprite(mat, px = 40, aspect = 1) {
  const s = new THREE.Sprite(mat); s.userData.px = px; s.userData.aspect = aspect;
  s.onBeforeRender = function (r, sc, cam) { const k = (this.userData.px * 2) / (1920 * cam.projectionMatrix.elements[5]); this.scale.set(k, k * this.userData.aspect, 1); this.updateMatrixWorld(); };
  return s;
}
const addSpriteMat = (map, color, k = 1, o = {}) => new THREE.SpriteMaterial({ map, color: new THREE.Color(color).multiplyScalar(k), blending: THREE.AdditiveBlending, depthWrite: false, depthTest: false, transparent: true, fog: false, sizeAttenuation: false, ...o });
// One big 4-point star glint (TF coin glint) on a precious prop: 0 -> peak px in 3 frames, gone by +16 frames.
function starGlint(ctx, { pos, t0, peak = 110, rot = 25, color = '#f4ecff' }) {
  const mat = addSpriteMat(ctx.tex.sparkle({ points: 4, sharpness: 22, core: 0.6 }), color, 2.4);
  const s = pxSprite(mat, 0); s.position.copy(pos); s.renderOrder = 30; s.visible = false;
  const core = pxSprite(addSpriteMat(ctx.tex.radialGlow({ falloff: 2.2 }), '#fff4ff', 1.6), 0);
  core.position.copy(pos); core.renderOrder = 29; core.visible = false;
  const g = new THREE.Group(); g.add(core, s);
  g.update = (t) => {
    const f = (t - t0) * 60; const on = f > -0.5 && f < 16.5; s.visible = core.visible = on; if (!on) return;
    const k = f < 3 ? (f + 1) / 4 : Math.pow(1 - (f - 3) / 13.5, 1.6);
    s.userData.px = peak * k; core.userData.px = peak * 0.42 * k; mat.rotation = rot * DEG * clamp01(f / 16); s.material.opacity = 1; core.material.opacity = 0.7 * k;
  };
  g.update(-1); return g;
}
// Cartoon "poof" that hides the human -> gnome swap: soft white puffs (normal blending, drawn over the bodies) that are
// half on the frame before the snap, OPAQUE on the snap frame and the next (the swap happens under them), then swell and
// clear in `dur` seconds (so the frame is back to its own exposure ~0.2 s after the snap: a local puff, not a wash).
function puffTex(ctx) { // cartoon cloud puff: opaque core to 60% of the radius, soft edge
  return ctx.cache('ep01t5:puffTex', () => {
    const N = 128, d = new Uint8Array(N * N * 4), c = (N - 1) / 2;
    for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) { const r = Math.hypot(x - c, y - c) / c; const a = r >= 1 ? 0 : r < 0.6 ? 1 : 1 - smooth((r - 0.6) / 0.4); const sh = 1 - 0.1 * clamp01((y - c) / c + 0.3 * (x - c) / c); const i = (y * N + x) * 4; d[i] = d[i + 1] = d[i + 2] = Math.round(255 * clamp01(sh)); d[i + 3] = Math.round(a * 255); }
    const t = new THREE.DataTexture(d, N, N); t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearMipmapLinearFilter; t.generateMipmaps = true; t.needsUpdate = true; t.userData.persistent = true; return t;
  });
}
function poofCloud(ctx, { pos, t0, dur = 0.18, count = 6, spread = [0.42, 0.9, 0.2], px = [520, 700], colors = ['#fbf6ff', '#f3eaff', '#fff4f8', '#ffffff'], seed = 'poof' }) {
  const g = new THREE.Group(); g.name = 'poofCloud'; const r = makeRng(hash32('ep01t5', seed)); const tex = puffTex(ctx);
  for (let i = 0; i < count; i++) {
    const m = new THREE.SpriteMaterial({ map: tex, color: new THREE.Color(colors[i % colors.length]).multiplyScalar(1.05), transparent: true, depthWrite: false, depthTest: false, fog: false, sizeAttenuation: false });
    const s = pxSprite(m, 0); s.renderOrder = 25 + i; const o = new THREE.Vector3((r() - 0.5) * 2 * spread[0], (r() - 0.5) * 2 * spread[1] * 0.5, (r() - 0.5) * 2 * spread[2]);
    s.userData.d = { o, px: px[0] + (px[1] - px[0]) * r(), life: 0.8 + 0.4 * r(), drift: 0.3 + 0.4 * r() }; s.visible = false; g.add(s);
  }
  g.update = (t) => {
    const f = (t - t0) * 60; // frames from the snap
    for (const s of g.children) {
      const d = s.userData.d; const v = (f - 1.5) / (60 * dur * d.life); // fade phase after the 2 opaque frames
      if (f < -1.5 || v > 1) { s.visible = false; continue; } s.visible = true;
      const a = f < -0.5 ? 0.5 : f <= 1.5 ? 0.97 : 0.97 * Math.pow(1 - v, 2.5);
      const k = f < -0.5 ? 0.85 : 1 + 0.5 * outQuad(Math.max(0, v)); const dr = 1 + d.drift * Math.max(0, v);
      s.position.set(pos[0] + d.o.x * dr, pos[1] + d.o.y * dr + 0.06 * Math.max(0, v), pos[2] + d.o.z);
      s.userData.px = d.px * k; s.material.opacity = a;
    }
  };
  g.update(-10); return g;
}
// TF-style burst streaks: additive white/pink rays shooting out of the burst centre in the camera plane (0.25 s).
function streakTex(ctx) {
  return ctx.cache('ep01t5:streakTex', () => {
    const W = 128, H = 32, d = new Uint8Array(W * H * 4);
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const u = x / (W - 1), v = (y - (H - 1) / 2) / ((H - 1) / 2); const taper = Math.pow(Math.sin(Math.PI * u), 0.6) * (0.35 + 0.65 * u);
      const a = Math.exp(-v * v * 9 / Math.max(0.15, taper)) * taper; const i = (y * W + x) * 4; d[i] = d[i + 1] = d[i + 2] = 255; d[i + 3] = Math.round(clamp01(a) * 255);
    }
    const t = new THREE.DataTexture(d, W, H); t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearMipmapLinearFilter; t.generateMipmaps = true; t.needsUpdate = true; t.userData.persistent = true; return t;
  });
}
function streaks(ctx, { pos, t0, count = 14, px = [120, 260], life = 0.25, colors = ['#ffffff', '#ff7aa0', '#ffffff', '#ffd0e0'], seed = 'streaks', reach = 0.55 }) {
  const g = new THREE.Group(); g.name = 'streaks'; const r = makeRng(hash32('ep01t5', seed)); const tex = streakTex(ctx); const P0 = V3(pos);
  for (let i = 0; i < count; i++) {
    const s = pxSprite(addSpriteMat(tex, colors[i % colors.length], 2.2), 0, 0.2); s.renderOrder = 42;
    s.userData.d = { a: (i / count) * Math.PI * 2 + (r() - 0.5) * 0.35, px: px[0] + (px[1] - px[0]) * r(), reach: reach * (0.6 + 0.6 * r()), life: life * (0.8 + 0.4 * r()) }; s.visible = false; g.add(s);
  }
  g.update = (t, cam) => {
    const right = new THREE.Vector3(), up = new THREE.Vector3(); cam.updateMatrixWorld(true); right.setFromMatrixColumn(cam.matrixWorld, 0); up.setFromMatrixColumn(cam.matrixWorld, 1);
    for (const s of g.children) {
      const d = s.userData.d; const u = (t - t0) / d.life; if (u < 0 || u > 1) { s.visible = false; continue; } s.visible = true;
      const k = outExpo(u); const dir = right.clone().multiplyScalar(Math.cos(d.a)).addScaledVector(up, Math.sin(d.a));
      s.position.copy(P0).addScaledVector(dir, d.reach * (0.25 + 0.75 * k)); s.material.rotation = d.a;
      s.userData.px = d.px * (0.5 + 0.7 * k) * (1 - 0.4 * u); s.material.opacity = Math.pow(1 - u, 1.3);
    }
  };
  return g;
}
// Put a stud-unit object into a metre-scaled wrapper.
function studWrap(obj) { const w = new THREE.Group(); w.scale.setScalar(S); w.add(obj); return w; }
// Gnome eyes look at a world point (gnome local frame faces +Z).
function gazeAt(g, worldPt, extraPitch = 0) {
  g.updateWorldMatrix(true, true);
  const e = g.getObjectByName('ballL').getWorldPosition(new THREE.Vector3()).add(g.getObjectByName('ballR').getWorldPosition(new THREE.Vector3())).multiplyScalar(0.5);
  const a = g.worldToLocal(e.clone()), b = g.worldToLocal(worldPt.clone()); const d = b.sub(a);
  K.setGnomeGaze(g, Math.atan2(d.x, d.z) / DEG, Math.atan2(d.y, Math.hypot(d.x, d.z)) / DEG + extraPitch);
}
function eyesOf(g) { g.updateWorldMatrix(true, true); return g.getObjectByName('ballL').getWorldPosition(new THREE.Vector3()).add(g.getObjectByName('ballR').getWorldPosition(new THREE.Vector3())).multiplyScalar(0.5); }
// Hero-gnome surface at ECU: few chips (wear 0.12) and a softer beard bump (bump 1.4 -> 0.8) so the beard reads as glaze.
function softenBeard(g) { g.traverse((o) => { if (o.isMesh && o.material && o.material.bumpMap && Math.abs(o.material.bumpScale - 1.4) < 1e-6) { o.material = o.material.clone(); o.material.bumpScale = 0.8; } }); }
// Grandma's glasses: no lens glass (it tinted her ^^ eye lines navy) and no temple arms (they read as a mole in 3/4).
function cleanGlasses(av) { const gl = av.getObjectByName('glasses'); if (!gl) return; gl.children.forEach((m) => { if (!m.isMesh) return; const p = m.geometry.type; if (p === 'CircleGeometry' || p === 'BoxGeometry') m.visible = false; }); }

// ------------------------------------------------------------------ the porch swing (new prop, studs)
// Slatted painted-wood bench (8.6 x 1.6 studs, seat top 1.5 above the deck, back 1.6 tall, armrests) hanging on brass
// chains from two ceiling hooks. Wider than the board's 5.5 studs because two seated R6 bodies (4 studs wide each) need 8.2.
// Origin = deck point under the bench centre; front = +Z (sitters face the street).
const SWING = { W: 8.6, D: 1.6, seatY: 1.5, back: 1.6, wood: '#e9e4da', chain: '#8a6a3a' };
function buildSwing(ctx, H) {
  const tpl = ctx.cache('ep01t5:swing2:' + H.toFixed(3), () => {
    const { W, D, seatY, back } = SWING; const wk = 'trim:' + SWING.wood, ck = 'brass:' + SWING.chain;
    const root = new THREE.Group(); root.name = 'porchSwing';
    const pivot = new THREE.Group(); pivot.name = 'swingPivot'; pivot.position.set(0, H, 0); root.add(pivot);
    const P = new sets.Parts(); P.push(new THREE.Matrix4().makeTranslation(0, -H, 0)); // build in deck coordinates, hang from the pivot
    for (let i = 0; i < 6; i++) P.box(wk, W - 0.3, 0.13, 0.22, [0, seatY - 0.065, -0.6 + 0.04 + i * (D - 0.08) / 5.6 + 0.11], null, { bevel: 0.03 });
    for (const z of [-0.6, D - 0.6]) P.box(wk, W, 0.22, 0.2, [0, seatY - 0.2, z]);
    for (const x of [-W / 2 + 0.1, W / 2 - 0.1]) P.box(wk, 0.22, 0.22, D, [x, seatY - 0.2, D / 2 - 0.6]);
    P.push(new THREE.Matrix4().makeTranslation(0, seatY, -0.62).multiply(new THREE.Matrix4().makeRotationX(-12 * DEG)));
    for (const x of [-W / 2 + 0.1, W / 2 - 0.1]) P.box(wk, 0.24, back + 0.15, 0.2, [x, (back + 0.15) / 2, 0]);
    for (let i = 0; i < 5; i++) P.box(wk, W - 0.3, 0.2, 0.1, [0, 0.22 + i * (back - 0.25) / 4.2, 0], null, { bevel: 0.02 });
    P.box(wk, W + 0.1, 0.18, 0.28, [0, back + 0.18, 0], null, { bevel: 0.03 });
    P.pop();
    for (const s of [-1, 1]) { const x = s * (W / 2 - 0.1); P.box(wk, 0.28, 0.14, D + 0.15, [x, seatY + 0.9, D / 2 - 0.6]); P.box(wk, 0.18, 0.9, 0.18, [x, seatY + 0.45, D - 0.7]); }
    for (const s of [-1, 1]) {
      const hook = [s * (W / 2 - 0.3), H - 0.15, 0.2];
      for (const z of [-0.55, D - 0.65]) {
        const a = new THREE.Vector3(s * (W / 2 - 0.1), seatY + 0.97, z), b = new THREE.Vector3(...hook); const n = Math.round(a.distanceTo(b) / 0.32);
        for (let k = 0; k < n; k++) { const p0 = a.clone().lerp(b, k / n), p1 = a.clone().lerp(b, (k + 0.85) / n); P.bar(ck, p0.toArray(), p1.toArray(), k % 2 ? 0.06 : 0.12, k % 2 ? 0.12 : 0.06); }
      }
    }
    P.pop();
    const mesh = P.build(sets.M, { name: 'swingMesh', cast: false, receive: true }); pivot.add(mesh);
    const seat = new THREE.Group(); seat.name = 'swingSeat'; seat.position.set(0, -H, 0); pivot.add(seat);
    const HP = new sets.Parts(); for (const s of [-1, 1]) { HP.box(ck, 0.3, 0.3, 0.3, [s * (W / 2 - 0.3), H + 0.05, 0.2]); HP.cyl(ck, 0.05, 0.05, 0.3, 8, [s * (W / 2 - 0.3), H - 0.1, 0.2]); }
    root.add(HP.build(sets.M, { name: 'swingHooks' }));
    return studWrap(root);
  });
  const w = tpl.clone(true);
  return { root: w, pivot: w.getObjectByName('swingPivot'), seat: w.getObjectByName('swingSeat') };
}
// White spindle railing (PN porch rail, 3.1 studs tall), along +X centred on the origin, studs.
function spindleRail(ctx, len) {
  return ctx.cache('ep01t5:rail:' + len, () => {
    const P = new sets.Parts(); const k = 'trim:#f1eee8';
    P.box(k, len, 0.34, 0.42, [0, 3.1, 0], null, { bevel: 0.05 }); P.box(k, len, 0.26, 0.3, [0, 0.45, 0]);
    const n = Math.floor(len / 0.62); for (let i = 1; i < n; i++) P.box(k, 0.2, 2.5, 0.2, [-len / 2 + (i * len) / n, 1.8, 0]);
    for (const x of [-len / 2, len / 2]) { P.box(k, 0.62, 3.7, 0.62, [x, 1.85, 0]); P.box(k, 0.8, 0.2, 0.8, [x, 3.8, 0]); }
    return studWrap(P.build(sets.M, { name: 'spindleRail', receive: true }));
  }).clone(true);
}
// Porch dressing (bible 5-15 props): a side table with a teacup and a knitting basket, a geranium pot, studs.
function porchDressing(ctx) {
  return ctx.cache('ep01t5:dressing', () => {
    const P = new sets.Parts(); const w = 'wood:#7a4a28';
    P.box(w, 1.5, 0.16, 1.5, [0, 2.1, 0], null, { bevel: 0.04 }); for (const [x, z] of [[-0.6, -0.6], [0.6, -0.6], [-0.6, 0.6], [0.6, 0.6]]) P.box(w, 0.16, 2.05, 0.16, [x, 1.02, z]);
    P.box(w, 1.3, 0.1, 1.3, [0, 0.6, 0]);
    P.cyl('plastic:#f4f0ea', 0.36, 0.36, 0.05, 20, [0.1, 2.21, 0.1]); P.cyl('plastic:#f4f0ea', 0.22, 0.16, 0.32, 18, [0.1, 2.4, 0.1]); P.cyl('plastic:#c86f93', 0.225, 0.225, 0.05, 18, [0.1, 2.5, 0.1]);
    P.cyl('wood:#a0703a', 0.55, 0.45, 0.55, 16, [0, 0.9, 0]); for (const [x, z, c] of [[-0.15, 0.1, '#c84a6a'], [0.18, -0.05, '#7d9be8'], [0.02, -0.2, '#f2cf6a']]) P.add('plastic:' + c, new THREE.SphereGeometry(0.22, 12, 8), [x, 1.2, z]);
    P.bar('metal:#c9c4cc', [-0.1, 1.15, 0.1], [0.3, 1.75, -0.2], 0.04, 0.04); P.bar('metal:#c9c4cc', [0.1, 1.15, 0.15], [-0.3, 1.7, -0.1], 0.04, 0.04);
    const g = new THREE.Group(); g.add(P.build(sets.M, { name: 'sideTable', receive: true }));
    const pot = sets.props.prop('potPlant', { seed: 9, blossom: '#e0485a' }); pot.position.set(-11.2, 0, -0.2); g.add(pot);
    return studWrap(g);
  }).clone(true);
}

// ------------------------------------------------------------------ the porch (s02-s04)
// The couple's bungalow: a deep full-width porch (11 studs, so the low s04 camera fits inside the railing), both front
// windows lit (amber, dimmer than the subject), dark wine curtains, wall lanterns either side of the door (lit, haloed),
// the swing to the right of the door in front of the right window.
const PORCH_HOUSE = { type: 'bungalow', wall: 'siding', wallColor: '#cdb79c', roofColor: '#3b3440', doorColor: '#6b1f1a', shutterColor: '#3b4347', porch: 'full', porchDepth: 11, offsetX: 0, lit: [1, 1, 0, 1], curtain: '#7a2a3a', winIntensity: 1.4, number: '14', planters: false, seed: 77 };
const SWING_X = 7.6, SWING_Z = 2.4, SEAT_X = 2.0, TURN_IN = 0.15; // studs from the door (x) and the front wall (z); riders turn in 8.6 deg
// Porch grade: warm skin, cool night around it (review: R-B >= +35 on skin, maroon corners, white capped at #e9d4ee).
const PORCH_POST = { exposure: 1.1, grade: { temperature: -3, tint: 4, saturation: 1.0, contrast: 1.04, shadows: '#3e1420', shadowsAmount: 0.3, highlights: '#f0d2e0', highlightsAmount: 0.2, outBlack: '#060104', outWhite: '#e9d4ee' } };
// Face key warm from upper front-left, cool hemisphere/key as fill only.
const PORCH_LIGHT = (subjectPos, cd = 3.0) => ({ subject: { pos: subjectPos, cd, color: '#ffc49a' }, hemiIntensity: 0.95, key: { color: '#9aa0ff', intensity: 0.7 }, lantern: { cd: 3, n: 2, maxD: 14 }, postOpts: PORCH_POST, skyPreset: GALAXY });
function swingSway(T) { return 2.5 * Math.sin(2 * Math.PI * 0.45 * T + 0.6); } // degrees, episode time (continuous over cuts)

function porchScene(ctx, { gnomes = false } = {}) {
  const set = sets.buildLot(ctx, { seed: 'ep01', hero: { house: PORCH_HOUSE } }); ctx.add(set);
  const L = set.userData.lots.find((l) => l.hero);
  const deckY = L.deckY; const wallZ = L.door[2] - 0.3 * S;
  const H = 8.8; // hook height above the deck (porch ceiling underside)
  const C = new THREE.Vector3(L.door[0] + SWING_X * S, deckY, wallZ + SWING_Z * S); // deck point under the bench centre (m)
  const lotG = set.getObjectByName('lot_' + L.id); const deckKey = 'porch:#a8743a';
  if (lotG) { const dm = ctx.cache('ep01t5:deckMat', () => { const m = new THREE.MeshStandardMaterial({ ...ctx.tex.woodPlanks({ color: '#9a6638', planks: 8, joints: 1, gap: 0.004, gapColor: '#4a2c16', variation: 0.12, grain: 0.8, gloss: 0.55, seed: 4 }).mat, roughness: 0.38 }); m.name = 'ep01t5:deck'; return m; });
    lotG.traverse((o) => { if (o.isMesh && o.name === deckKey) o.material = dm; }); }
  const sw = buildSwing(ctx, H); sw.root.position.copy(C); ctx.add(sw.root);
  ctx.add(sets.contactShadow(ctx, { pos: [C.x, deckY + 0.004, C.z + 0.25 * S], radius: 1.55, opacity: 0.32 }));
  const dr = porchDressing(ctx); dr.position.set(C.x + 6.0 * S, deckY, C.z + 0.2 * S); ctx.add(dr);
  // the couple (studs, children of the swinging seat): Grandma on the left of frame (-x), Grandpa on the right (+x)
  const gm = ctx.instance('ep01t5:grandma', () => K.makeCharacter('grandma', { units: 'stud', shadow: false }));
  const gp = ctx.instance('ep01t5:grandpa', () => K.makeCharacter('grandpa', { units: 'stud', shadow: false }));
  cleanGlasses(gm);
  gm.position.set(-SEAT_X, 0, 0.05); gp.position.set(SEAT_X, 0, 0.05); gm.rotation.y = TURN_IN; gp.rotation.y = -TURN_IN;
  K.setPose(gm, { ...K.POSES.sit, armLx: 6, armRx: 26, armLz: 0, armRz: 6, neckY: 6, neckZ: -3 });   // inner arms down and in: holding hands
  K.setPose(gp, { ...K.POSES.sit, armLx: 24, armRx: 6, armLz: -6, armRz: 0, neckY: -4, neckZ: 2 });
  sw.seat.add(gm, gp);
  const out = { set, L, deckY, wallZ, C, H, swing: sw, gm, gp };
  if (gnomes) { // the transformed couple standing together on the seat, x1.35, turned toward each other (hidden until the snap)
    const ggm = K.makeGnome('grandma', { units: 'stud', lantern: false, wear: 0.12 }); const ggp = K.makeGnome('grandpa', { units: 'stud', lantern: 0, wear: 0.12 });
    softenBeard(ggp);
    ggm.position.set(-1.05, SWING.seatY, 0.1); ggp.position.set(1.05, SWING.seatY, 0.1); ggm.rotation.y = 0.26; ggp.rotation.y = -0.26;
    ggm.scale.setScalar(1.35); ggp.scale.setScalar(1.35);
    ggm.visible = ggp.visible = false; sw.seat.add(ggm, ggp); out.ggm = ggm; out.ggp = ggp;
  }
  return out;
}
function seatPoint(P, x, y, z) { return P.C.clone().add(new THREE.Vector3(x * S, y * S, z * S)); }
function headWorld(avatar) { avatar.updateWorldMatrix(true, true); const h = avatar.getObjectByName('head'); return h.getWorldPosition(new THREE.Vector3()); }
function updateSwing(P, T, { jolt = null, amp = 1 } = {}) {
  let rx = swingSway(T) * amp, dy = 0;
  if (jolt) { const u = T - jolt.T0; if (u >= 0) { rx += jolt.amp * Math.exp(-2.2 * u) * Math.sin(2 * Math.PI * 1.1 * u); dy = -jolt.dip * (1 - springStep(u, 3, 0.35)); } }
  P.swing.pivot.rotation.x = rx * DEG; P.swing.pivot.position.y = P.H + dy;
}

// ------------------------------------------------------------------ street gnomes (s01)
// One or two family gnomes per lawn on side A, centred in front of each house (the bed under the front window + one on
// the lawn), all facing their house (slot yaw), lanterns unlit (a plot plant). Side B (across the street) gets the bed
// gnome only. Near lots get the 'mid' build, far ones 'low'.
const POINTED = [0, 1, 2, 3, 4, 5, 7]; // family variants with pointed hats (the fishing-hat one reads as a pot from behind)
function streetGnomes(ctx, set, heroId, skip = []) {
  const r = makeRng(hash32('ep01t5', 'streetGnomes2')); let k = 0;
  const hero = set.userData.lots.find((l) => l.id === heroId);
  for (const l of set.userData.lots) {
    const dist = Math.abs(l.index - hero.index); const lod = l.side === 'A' && dist <= 1 ? 'mid' : 'low';
    const names = l.side === 'A' ? (l.id === heroId ? ['bed0', 'lawn2', 'lawn3'] : ['bed0', 'lawn0', 'lawn3']) : ['bed0', 'lawn2'];
    for (const n of names) {
      const s = sets.slot(set, l.id + '.' + n); if (!s || skip.includes(s.name)) continue;
      const g = l.id === heroId && n === 'bed0' ? K.makeGnome('grandpa', { lantern: 0, lod: 'mid' }) : K.makeFamilyGnome(POINTED[k++ % POINTED.length], { lod, lantern: 0 });
      sets.place(g, s); g.rotation.y += (r() - 0.5) * 0.1; ctx.add(g);
    }
  }
}

// ------------------------------------------------------------------ magic grade blend (s04, on "turn")
const hexArr = (h) => { const c = new THREE.Color(); c.setStyle(h, THREE.NoColorSpace); return [c.r, c.g, c.b]; };
const lerpArr = (a, b, k) => a.map((x, i) => x + (b[i] - x) * k);
const GRADE_NUM = ['temperature', 'tint', 'contrast', 'pivot', 'saturation', 'shadowsAmount', 'highlightsAmount', 'balance'];
const GRADE_COL = ['shadows', 'highlights', 'outBlack', 'outWhite'];
function gradeBlend(A, B) {
  const a = {}, b = {};
  for (const k of GRADE_NUM) { a[k] = A[k] ?? (k === 'contrast' || k === 'saturation' ? 1 : k === 'pivot' ? 0.45 : 0); b[k] = B[k] ?? (k === 'contrast' || k === 'saturation' ? 1 : k === 'pivot' ? 0.45 : 0); }
  for (const k of GRADE_COL) { a[k] = hexArr(A[k] || (k === 'outWhite' ? '#ffffff' : '#000000')); b[k] = hexArr(B[k] || (k === 'outWhite' ? '#ffffff' : '#000000')); }
  return (G, k) => { for (const n of GRADE_NUM) G[n] = a[n] + (b[n] - a[n]) * k; for (const n of GRADE_COL) G[n] = lerpArr(a[n], b[n], k); };
}

// ------------------------------------------------------------------ shot builders
const BUILDERS = {
  // s01 "In this world," - TF opener: frame 0 is a bright ECU of a neighbour's gnome seen from its house side (face to the
  // lens, moon behind its hat), then a snap pull-back (outExpo, half done in 0.1 s) + crane up + roll -15 -> 0 that lands on
  // a high 3/4 view from the porches: every gnome on every lawn faces the camera (= its house), the street, lit lamps and
  // the houses across. A linear 10% push is layered on top so the shot never settles before the cut.
  sky_to_street: {
    build(ctx) {
      const p = ctx.params; const mv = p.camera.move;
      const set = sets.buildStreet(ctx, { seed: 'ep01', lotsPerSide: 6, hero: { side: 'A', index: 3 } }); ctx.add(set);
      const hero = set.userData.lots.find((l) => l.hero); const heroId = hero.id;
      const gs = { ...sets.slot(set, heroId + '.' + p.camera.start.gnome_slot) };
      streetGnomes(ctx, set, heroId, [gs.name]);
      const G = K.makeFamilyGnome(p.camera.start.gnome_variant, { lod: 'hero', lantern: 0, wear: 0.12 }); sets.place(G, gs);
      if (p.camera.start.at) { G.position.set(hero.gate[0] + p.camera.start.at[0] * S, 0, hero.origin[2] + p.camera.start.at[1] * S); gs.pos = G.position.toArray(); }
      ctx.add(G);
      (p.set.row || []).forEach(([x, z, v], i) => { const f = K.makeFamilyGnome(v, { lod: 'mid', lantern: 0 }); f.position.set(hero.gate[0] + x * S, 0, hero.origin[2] + z * S); f.rotation.y = gs.yaw + (i % 2 ? 0.05 : -0.04); ctx.add(f); ctx.add(sets.contactShadow(ctx, { pos: [f.position.x, 0, f.position.z], radius: 0.24, opacity: 0.35 })); });
      ctx.add(sets.contactShadow(ctx, { pos: gs.pos, radius: 0.24, opacity: 0.4 }));
      const eyes = eyesOf(G); const fwd = new THREE.Vector3(Math.sin(gs.yaw), 0, Math.cos(gs.yaw)); // the gnome faces its house
      const side = new THREE.Vector3(-fwd.z, 0, fwd.x); // gnome's left in world (screen-right from the lens)
      // start: ECU of the face, slightly below the eyes looking up a touch (hat + moon in frame)
      const st = p.camera.start;
      const P0 = eyes.clone().addScaledVector(fwd, st.dist_studs * S).addScaledVector(side, st.side_studs * S); P0.y = eyes.y + st.up_studs * S;
      const T0 = eyes.clone().add(new THREE.Vector3(0, st.aim_up_studs * S, 0));
      // end: high 3/4 from the porches back toward the street, the start gnome low-centre in frame
      const en = p.camera.end; const back = fwd.clone(); // toward the house
      const out = fwd.clone().negate(); // toward the street
      const P1 = V3(hero.door).addScaledVector(out, en.out_studs * S).addScaledVector(side, en.side_studs * S); P1.y = hero.deckY + en.up_studs * S;
      const T1 = V3(hero.gate).addScaledVector(out, en.look_out_studs * S).addScaledVector(side, en.look_side_studs * S); T1.y = en.look_y_studs * S;
      const U = (t) => 0.8 * outExpo((t - mv.t0) / (mv.t1 - mv.t0)) + 0.2 * outQuad((t - mv.t0) / (mv.t1 - mv.t0));
      const [r0, r1] = mv.roll_deg;
      // light rig from the END framing (key from behind-left-above the porch camera lights every gnome face)
      ctx.camera.set({ pos: P1.toArray(), target: T1.toArray(), fov: p.fov });
      const camAz = Math.atan2(-fwd.x, fwd.z) / DEG + 180; // az of the start view direction (toward the street)
      ctx.shared.rig = sets.nightStreet(ctx, { set, moon: { az: camAz + st.moon_az, el: st.moon_el, size: 8, style: 'tf' }, skyPreset: GALAXY, skyOpts: { intensity: 1.5 }, lamp: { n: 4 } });
      const tmpA = new THREE.Vector3();
      ctx.camera.set({ pos: (t, o) => (o || new THREE.Vector3()).copy(P0).lerp(P1, U(t)), target: (t, o) => (o || new THREE.Vector3()).copy(T0).lerp(T1, U(t)), fov: (t) => st.fov + (p.fov - st.fov) * U(t), roll: (t) => r0 + (r1 - r0) * U(t) })
        .push(p.camera.push.Z);
      // the face key at frame 0: warm spill from the house behind the lens (upper left), and a cool rim from the street
      tmpA.copy(P0).addScaledVector(side, -0.25).add(new THREE.Vector3(0, 0.3, 0)).addScaledVector(fwd, 0.15);
      ctx.add(ctx.lights.point({ color: '#ffc08a', intensity: 2.8, pos: tmpA.toArray(), decay: 2 }));
      const c = eyes.clone().addScaledVector(fwd, 0.6).add(new THREE.Vector3(0, 0.1, 0));
      ctx.shared.fx = sets.sparkles(ctx, { ...SPARK, center: c.toArray(), size: [2.2, 1.4, 1.6], count: 6, seed: 's01a' }); ctx.add(ctx.shared.fx);
      const c2 = V3(gs.pos).addScaledVector(back, -3 * S).add(new THREE.Vector3(0, 1.4, 0));
      ctx.shared.fx2 = sets.sparkles(ctx, { ...SPARK, center: c2.toArray(), size: [7, 2.6, 6], count: p.fx.sparkles.count, seed: 's01b' }); ctx.add(ctx.shared.fx2);
      ctx.shared.G = G; K.setGnomeGaze(G, 0, -4);
    },
    update(ctx, t) { ctx.shared.fx.update(t); ctx.shared.fx2.update(t); K.gnomeIdle(ctx.shared.G, t, { seed: 'opener' }); },
  },

  // s02 "grandparents" - MS two-shot from the front-left over a white spindle railing (PN porch framing: the rail hides the
  // seated legs), both heads inside the frame through the push, the couple turned toward each other holding hands; the
  // porch's open end shows the night yard and a neighbour's lit windows at frame right.
  porch_couple: {
    build(ctx) {
      const p = ctx.params; const P = porchScene(ctx); ctx.shared.P = P; const c = p.camera;
      K.setFace(P.gm, p.faces.grandma); K.setFace(P.gp, p.faces.grandpa);
      updateSwing(P, ctx.shot.start); const mid = headWorld(P.gm).add(headWorld(P.gp)).multiplyScalar(0.5);
      const yaw = c.yaw_deg * DEG, R = c.dist_studs * S;
      const tgt = mid.clone().add(new THREE.Vector3(c.aim_x_studs * S, c.aim_dy_studs * S, 0));
      const pos = new THREE.Vector3(mid.x + Math.sin(yaw) * R, P.deckY + c.height_studs * S, mid.z + Math.cos(yaw) * R);
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: p.fov });
      ctx.shared.rig = sets.porchGlow(ctx, { set: P.set, ...PORCH_LIGHT(mid.toArray(), 3.0) });
      ctx.camera.push(c.move.Z).truck(c.drift.truck_studs * S);
      // the railing between the lens and the swing, square to the view so it spans the bottom of the frame
      const rail = spindleRail(ctx, 16); const toCam = new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw));
      rail.position.set(mid.x, P.deckY, mid.z).addScaledVector(toCam, c.rail_studs * S); rail.rotation.y = yaw; rail.scale.y *= c.rail_scale_y ?? 1; ctx.add(rail);
      ctx.shared.fx = sets.sparkles(ctx, { ...SPARK, center: [tgt.x, tgt.y + 0.15, tgt.z + 0.6], size: [2.8, 1.6, 1.2], count: p.fx.sparkles.count, seed: 's02' }); ctx.add(ctx.shared.fx);
    },
    update(ctx, t) { updateSwing(ctx.shared.P, ctx.T); ctx.shared.fx.update(t); },
  },

  // s03 "don't die." - reaction CU of Grandma, content (^^) from the cut; her glasses glint (4-point star) on "die".
  // The swing is held still in this shot so the push reads (the sway carried her head out of the push).
  grandma_cu: {
    build(ctx) {
      const p = ctx.params; const P = porchScene(ctx); ctx.shared.P = P; const c = p.camera;
      K.setFace(P.gm, p.faces.grandma); K.setFace(P.gp, 'content');
      updateSwing(P, ctx.shot.start, { amp: 0 }); const head = headWorld(P.gm);
      const yaw = TURN_IN + c.yaw_deg * DEG, R = c.dist_studs * S;
      const tgt = head.clone().add(new THREE.Vector3(c.aim_x_studs * S, c.aim_dy_studs * S, 0));
      const pos = head.clone().add(new THREE.Vector3(Math.sin(yaw) * R, 0.05 * S, Math.cos(yaw) * R));
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: p.fov });
      ctx.shared.rig = sets.porchGlow(ctx, { set: P.set, ...PORCH_LIGHT(head.toArray(), 2.4) });
      ctx.camera.push(c.move.Z).rollBy(c.roll.deg[1] - c.roll.deg[0]);
      const gl = P.gm.getObjectByName('glasses'); P.gm.updateWorldMatrix(true, true);
      const local = new THREE.Vector3(-0.28, 0.15, 0.69); const lens = gl ? gl.localToWorld(local.clone()) : head.clone();
      ctx.shared.glint = starGlint(ctx, { pos: lens, t0: evT(ctx, 'die') ?? 0.25, peak: 150, rot: 25 }); ctx.add(ctx.shared.glint);
      ctx.shared.fx = sets.sparkles(ctx, { ...SPARK, center: [head.x + 0.12, head.y + 0.05, head.z + 0.3], size: [1.2, 1.1, 0.5], count: p.fx.sparkles.count, seed: 's03' }); ctx.add(ctx.shared.fx);
    },
    update(ctx, t) { updateSwing(ctx.shared.P, ctx.T, { amp: 0 }); ctx.shared.fx.update(t); ctx.shared.glint.update(t); },
  },

  // s04 "They turn into garden" - centred low MS of the couple; magic dust builds, on "turn" a TF burst (streaks, fat
  // sparkles, ring, core) over a short opaque poof hides the swap (humans out on f134, gnomes in on f135), and the grade
  // swings to the warm magic look in 8 frames. The two gnomes stand together on the seat, x1.35, turned to each other.
  poof_swing: {
    build(ctx) {
      const p = ctx.params; const P = porchScene(ctx, { gnomes: true }); ctx.shared.P = P; const c = p.camera;
      K.setFace(P.gm, p.faces.grandma); K.setFace(P.gp, p.faces.grandpa);
      const yaw = c.yaw_deg * DEG, R = c.dist_studs * S;
      const tgt = P.C.clone().add(new THREE.Vector3(0, c.aim_studs * S, 0.3 * S));
      const pos = P.C.clone().add(new THREE.Vector3(Math.sin(yaw) * R, c.height_studs * S, Math.cos(yaw) * R + 0.3 * S));
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: p.fov });
      ctx.shared.rig = sets.porchGlow(ctx, { set: P.set, ...PORCH_LIGHT(tgt.toArray(), 3.0) });
      const tb = evT(ctx, 'turn') ?? 0.1333;
      ctx.camera.push(c.move.Z).push(c.punch.Z, { t0: tb, t1: tb + c.punch.dur, ease: c.punch.ease }); // punch-in on the reveal, under the poof
      ctx.shared.tb = tb; ctx.shared.Tb = ctx.shot.start + tb;
      gazeAt(P.ggm, pos); gazeAt(P.ggp, pos);
      // burst per grandparent (chest), drawn over the poof; streaks; the poof itself (opaque on the swap frames)
      const chest = (x) => seatPoint(P, x, 3.3, 1.1).toArray(); const cols = ['#ffffff', '#e9dcff', '#ffe2c4', '#ffb0d8'];
      ctx.shared.bursts = [chest(-SEAT_X), chest(SEAT_X)].map((q, i) => { const b = sets.burst(ctx, { pos: q, t0: tb, dur: 0.38, count: 36, px: [50, 90], puff: 0, corePx: 420, ringPx: [60, 640], colors: cols, spread: 0.8, brightness: 2.4, seed: 'poof' + i });
        b.traverse((o) => { if (o.isSprite) { o.renderOrder = 40; o.material.depthTest = false; } }); return b; });
      ctx.add(...ctx.shared.bursts);
      ctx.shared.streaks = [chest(-SEAT_X), chest(SEAT_X)].map((q, i) => streaks(ctx, { pos: q, t0: tb, count: 14, seed: 'st' + i }));
      ctx.add(...ctx.shared.streaks);
      ctx.shared.poofs = [-1, 1].map((sx, i) => poofCloud(ctx, { pos: seatPoint(P, sx * c.poof_x_studs, 2.9, 0.9).toArray(), t0: tb, seed: 'poof' + i, count: 5, px: [220, 320], spread: [0.16, 0.55, 0.1], dur: 0.14 }));
      ctx.add(...ctx.shared.poofs);
      const mid = seatPoint(P, 0, 2.8, 0.5).toArray();
      ctx.shared.dust = sets.magicDust(ctx, { center: mid, radius: 1.35, height: 1.5, count: 44, rise: 0.25, swirl: 0.9, px: [10, 26], seed: 's04dust' }); ctx.add(ctx.shared.dust);
      ctx.shared.motes = sets.magicDust(ctx, { center: seatPoint(P, 0, 3.0, 0.6).toArray(), radius: 1.1, height: 1.6, count: 26, rise: 0.35, swirl: 0.7, px: [14, 30], colors: ['#ffd27a', '#ffc070', '#ff9ad5', '#fff2d8'], seed: 's04motes' }); ctx.add(ctx.shared.motes);
      ctx.shared.fx = sets.sparkles(ctx, { ...SPARK, center: [mid[0], mid[1] + 0.25, mid[2] + 0.45], size: [2.4, 1.6, 1.0], count: p.fx.sparkles.count, seed: 's04' }); ctx.add(ctx.shared.fx);
      // warm magic look (bible P3 / 6.3 'magic glow moment'), blended in over 8 frames from the snap
      const A = JSON.parse(JSON.stringify(ctx.post.params)); const B = sets.postPreset('magic');
      ctx.shared.mg = { A, B, grade: gradeBlend(A.grade, B.grade), hemi0: [ctx.shared.rig.hemi.color.clone(), ctx.shared.rig.hemi.groundColor.clone(), ctx.shared.rig.hemi.intensity],
        hemi1: [new THREE.Color('#ffcdb8'), new THREE.Color('#5a2030'), 1.4], subj0: ctx.shared.rig.subject.intensity };
      ctx.post.set({ glow: { enabled: true, amount: 0, radius: B.glow.radius, mode: B.glow.mode, tint: B.glow.tint } });
    },
    update(ctx, t) {
      const P = ctx.shared.P, tb = ctx.shared.tb; const f = (t - tb) * 60; const humans = f < -0.5, gn = f >= -0.5; // humans to f133, gnomes from f134 (under the flash)
      // 1-frame white-pink flash on "turn" (screen blend) that hides the swap, gone in 5 frames (no lingering wash)
      const fi = Math.round(f); ctx.post.params.flash.color = '#fff2f8'; ctx.post.params.flash.amount = fi >= 0 && fi < 5 ? [0.85, 0.55, 0.3, 0.14, 0.05][fi] : 0;
      updateSwing(P, ctx.T, { jolt: { T0: ctx.shared.Tb + 1 / 60, amp: 5, dip: 0.15 } });
      P.gm.visible = P.gp.visible = humans; P.ggm.visible = P.ggp.visible = gn;
      if (gn) { K.gnomeIdle(P.ggm, t, { seed: 'gm' }); K.gnomeIdle(P.ggp, t, { seed: 'gp' }); }
      ctx.shared.dust.update(t); const k = t < tb ? 0.35 + 0.65 * clamp01(t / tb) : Math.max(0.2, 1 - 1.6 * (t - tb));
      ctx.shared.dust.children.forEach((s) => { s.material.opacity *= k; });
      ctx.shared.motes.update(t); const km = smooth((t - tb - 0.05) / 0.2); ctx.shared.motes.children.forEach((s) => { s.material.opacity *= km; s.visible = km > 0; });
      ctx.shared.bursts.forEach((b) => b.update(t)); ctx.shared.poofs.forEach((b) => b.update(t)); ctx.shared.fx.update(t);
      ctx.camera.apply(t); ctx.shared.streaks.forEach((s) => s.update(t, ctx.cam)); // streak directions need this frame's camera
      // magic grade blend
      const M = ctx.shared.mg; const u = smooth(f / 8); const pp = ctx.post.params;
      M.grade(pp.grade, u); pp.exposure = M.A.exposure + (M.B.exposure - M.A.exposure) * u;
      pp.bloom.strength = M.A.bloom.strength + (M.B.bloom.strength - M.A.bloom.strength) * u; pp.bloom.threshold = M.A.bloom.threshold + (M.B.bloom.threshold - M.A.bloom.threshold) * u; pp.bloom.radius = M.A.bloom.radius + (M.B.bloom.radius - M.A.bloom.radius) * u;
      pp.glow.amount = M.B.glow.amount * u;
      const h = ctx.shared.rig.hemi; h.color.copy(M.hemi0[0]).lerp(M.hemi1[0], u); h.groundColor.copy(M.hemi0[1]).lerp(M.hemi1[1], u); h.intensity = M.hemi0[2] + (M.hemi1[2] - M.hemi0[2]) * u;
    },
  },

  // s05 "gnomes." - the hero creature: Grandpa as a glazed gnome in his flowerbed, from below and at 3/4 on his lantern
  // side, warm window-spill key on his face, cool moon rim from behind-right, TF moon off the hat tip. Lantern UNLIT, no
  // blink / head turn (plot devices). Push + roll (character intro).
  gnome_hero: {
    build(ctx) {
      const p = ctx.params; const c = p.camera;
      const set = sets.buildLawnCloseup(ctx, { seed: 'ep01' }); ctx.add(set);
      const id = set.userData.lots.find((l) => l.hero).id; const sl = sets.slot(set, id + '.bed0');
      const g = K.makeGnome('grandpa', { lantern: 0, wear: 0.12 }); softenBeard(g); sets.place(g, sl); ctx.add(g);
      ctx.add(sets.contactShadow(ctx, { pos: sl.pos, radius: 0.24, opacity: 0.45 }));
      let k = 0; for (const n of ['lawn0', 'lawn2', 'bedFront1']) { const s = sets.slot(set, id + '.' + n); if (!s) continue; const f = K.makeFamilyGnome(2 + k++, { lantern: 0 }); sets.place(f, s); ctx.add(f); }
      g.updateWorldMatrix(true, true);
      const eyes = eyesOf(g); const fwd = new THREE.Vector3(Math.sin(sl.yaw), 0, Math.cos(sl.yaw)); // the gnome faces the house
      const lan = g.getObjectByName('lantern').getWorldPosition(new THREE.Vector3());
      const gl = new THREE.Vector3(-fwd.z, 0, fwd.x); const lanSide = Math.sign(lan.clone().sub(eyes).dot(gl)) || 1; // +1: lantern on the gnome's left
      const nose = eyes.clone().addScaledVector(fwd, 0.05 * S); nose.y -= 0.12 * S;
      const yaw = lanSide * c.yaw_deg * DEG; const dir = fwd.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), yaw);
      const pos = nose.clone().addScaledVector(dir, c.dist_studs * S); pos.y = c.height_studs * S;
      const tgt = eyes.clone().lerp(lan, c.aim_lantern); const hd = Math.hypot(tgt.x - pos.x, tgt.z - pos.z); tgt.y = pos.y + hd * Math.tan(c.pitch_deg * DEG); // look up pitch_deg
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: p.fov });
      const camYaw = Math.atan2(tgt.x - pos.x, -(tgt.z - pos.z)) / DEG;
      ctx.shared.rig = sets.nightLawn(ctx, { set, subject: { pos: nose.toArray(), cd: 0.6, color: '#ffd9b0' }, window: { n: 1, cd: 2.2, color: '#ffd9a0', maxD: 10 }, hemiIntensity: 1.0, key: { intensity: 0.45 },
        moon: { az: camYaw + c.moon_az, el: c.moon_el, size: 9, style: 'tf' }, skyPreset: GALAXY_LOW, skyOpts: { intensity: 2.2 }, postOpts: { exposure: 1.12, grade: { temperature: -4, tint: 6 } } });
      ctx.camera.push(c.move.Z).crane(c.drift.crane_studs * S).rollBy(c.roll.deg[1] - c.roll.deg[0]);
      // warm key: the bedroom-window spill, upper camera-left (az -35, el 35), 0.8 m from the nose
      const camF = tgt.clone().sub(pos).normalize(); const camR = new THREE.Vector3().crossVectors(camF, new THREE.Vector3(0, 1, 0)).normalize();
      const kd = camF.clone().multiplyScalar(-1).applyAxisAngle(new THREE.Vector3(0, 1, 0), -35 * DEG * 0).addScaledVector(camR, -Math.tan(35 * DEG)).normalize(); kd.y = Math.tan(35 * DEG); kd.normalize();
      ctx.add(ctx.lights.point({ color: '#ffc08a', intensity: 3.4, pos: nose.clone().addScaledVector(kd, 0.8).toArray(), decay: 2 }));
      // cool rim from behind-right (the moon side)
      const rimFrom = nose.clone().addScaledVector(fwd, -6).addScaledVector(camR, 5).add(new THREE.Vector3(0, 4, 0));
      ctx.add(ctx.lights.sun({ color: '#8a90ff', intensity: 0.8, pos: rimFrom.toArray(), target: nose.toArray(), shadow: false }));
      K.setGnomeGaze(g, 0, 10);
      ctx.shared.g = g;
      const sc = nose.clone().lerp(pos, 0.45);
      ctx.shared.fx = sets.sparkles(ctx, { ...SPARK, center: sc.toArray(), size: [0.9, 0.9, 0.35], count: p.fx.sparkles.count, drift: [0.02, 0.05], seed: 's05' }); ctx.add(ctx.shared.fx);
      ctx.shared.dust = sets.magicDust(ctx, { center: [eyes.x, sl.pos[1] + 0.25, eyes.z], radius: 0.35, height: 0.7, count: p.fx.magicDust.count, rise: 0.06, swirl: 0.35, px: [10, 20], seed: 's05dust' }); ctx.add(ctx.shared.dust);
    },
    update(ctx, t) {
      K.gnomeIdle(ctx.shared.g, t, { seed: 'hero' });
      ctx.shared.fx.update(t); ctx.shared.dust.update(t);
      const k = Math.max(0.3, 1 - t / 1.6); ctx.shared.dust.children.forEach((s) => { s.material.opacity *= k; });
    },
  },

  // s06 (silent tail, 3.77-5.00 s) - low wide behind the lawn gnomes: the whole family, Grandpa in his bed under the lit
  // window, all staring at the house; TF moon over the roof; a slow pull-back. Ends the test on the story's creepy image
  // (and loops to frame 0, a gnome's face).
  lawn_stare: {
    build(ctx) {
      const p = ctx.params; const c = p.camera;
      const set = sets.buildLawnCloseup(ctx, { seed: 'ep01' }); ctx.add(set);
      const id = set.userData.lots.find((l) => l.hero).id; const sl = sets.slot(set, id + '.bed0');
      const g = K.makeGnome('grandpa', { lantern: 0, wear: 0.12 }); sets.place(g, sl); ctx.add(g);
      ctx.add(sets.contactShadow(ctx, { pos: sl.pos, radius: 0.24, opacity: 0.45 }));
      const fam = []; let k = 0;
      for (const n of c.gnomes) { const s = sets.slot(set, id + '.' + n); if (!s) continue; const f = K.makeFamilyGnome(POINTED[(2 + k++) % POINTED.length], { lantern: 0, lod: 'mid' }); sets.place(f, s); ctx.add(f); fam.push(f); ctx.add(sets.contactShadow(ctx, { pos: s.pos, radius: 0.26, opacity: 0.4 })); }
      const fwd = new THREE.Vector3(Math.sin(sl.yaw), 0, Math.cos(sl.yaw)); const side = new THREE.Vector3(-fwd.z, 0, fwd.x);
      const base = V3(sl.pos); const near = V3(sets.slot(set, id + '.' + c.near_slot).pos);
      const pos = near.clone().addScaledVector(fwd, -c.back_studs * S).addScaledVector(side, c.side_studs * S); pos.y = c.height_studs * S;
      const tgt = base.clone().addScaledVector(fwd, c.look_ahead_studs * S).addScaledVector(side, c.look_side_studs * S); tgt.y = c.aim_studs * S;
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: p.fov });
      const camYaw = Math.atan2(tgt.x - pos.x, -(tgt.z - pos.z)) / DEG;
      ctx.shared.rig = sets.nightLawn(ctx, { set, window: { n: 2, cd: 2.4, color: '#ffd9a0', maxD: 14 }, hemiIntensity: 1.05,
        moon: { az: camYaw + c.moon_az, el: c.moon_el, size: 9, style: 'tf' }, skyPreset: GALAXY_LOW, skyOpts: { intensity: 1.6 }, postOpts: { exposure: 1.1, grade: { temperature: -10, tint: 6 } } });
      ctx.camera.pull(c.move.Z);
      ctx.shared.fx = sets.sparkles(ctx, { ...SPARK, center: pos.clone().lerp(base, 0.35).setY(0.7).toArray(), size: [3.5, 1.4, 2.5], count: p.fx.sparkles.count, seed: 's06' }); ctx.add(ctx.shared.fx);
      ctx.shared.fam = fam;
    },
    update(ctx, t) { ctx.shared.fx.update(t); ctx.shared.fam.forEach((f, i) => K.gnomeIdle(f, t, { seed: 'fam' + i, amp: 0.4 })); },
  },
};

export default {
  name: 'ep01_test5', fps: TL.fps, width: TL.width || 1080, height: TL.height || 1920, seed: 'ep01-test5', duration: TL.duration,
  quality: { shadows: 'off' },
  post: sets.postPreset('night'),
  shots: TL.shots.map((e) => ({ name: e.name, start: e.start, end: e.end, params: e.params, ...BUILDERS[e.shot] })),
};
export { BUILDERS as builders, TL as timeline };
